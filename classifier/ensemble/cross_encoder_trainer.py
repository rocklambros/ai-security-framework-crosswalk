"""Cross-encoder training function for W&B sweep integration.

Extracted from the v7 inline training loop in train_all.py Phase 3.
Supports both v7 (expert_train.jsonl) and v8/v9 (v8b_train.jsonl) data.
v9 additions: CollapseGuard, LLRD optimizer, mid-epoch validation.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score
from torch.utils.data import WeightedRandomSampler

import wandb


_COLLAPSE_MIN_CLASS_PCT = 0.02
_COLLAPSE_MIN_CF1 = 0.10
_COLLAPSE_PATIENCE = 2
_COLLAPSE_MAX_RECOVERIES = 3
_MID_EPOCH_VAL_INTERVAL = 200


def _build_llrd_optimizer(
    model: nn.Module,
    head_lr: float,
    decay_factor: float = 0.85,
    weight_decay: float = 0.01,
) -> torch.optim.AdamW:
    """Layer-wise learning rate decay for transformer encoders."""
    no_decay = {"bias", "LayerNorm.weight", "layernorm.weight"}
    param_groups = []

    head_params_d = []
    head_params_nd = []
    encoder_layer_params: dict[int, tuple[list, list]] = {}
    embed_params_d = []
    embed_params_nd = []

    encoder = getattr(model, "encoder", model)
    n_layers = getattr(getattr(encoder, "config", None), "num_hidden_layers", 12)

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        is_nodecay = any(nd in name for nd in no_decay)
        if "classifier" in name or "head" in name:
            (head_params_nd if is_nodecay else head_params_d).append(param)
        elif "embedding" in name.lower():
            (embed_params_nd if is_nodecay else embed_params_d).append(param)
        else:
            layer_idx = None
            for li in range(n_layers):
                if f"layer.{li}." in name or f"layers.{li}." in name:
                    layer_idx = li
                    break
            if layer_idx is not None:
                if layer_idx not in encoder_layer_params:
                    encoder_layer_params[layer_idx] = ([], [])
                d_list, nd_list = encoder_layer_params[layer_idx]
                (nd_list if is_nodecay else d_list).append(param)
            else:
                (embed_params_nd if is_nodecay else embed_params_d).append(param)

    if head_params_d:
        param_groups.append({"params": head_params_d, "lr": head_lr, "weight_decay": weight_decay})
    if head_params_nd:
        param_groups.append({"params": head_params_nd, "lr": head_lr, "weight_decay": 0.0})

    for layer_idx in sorted(encoder_layer_params.keys(), reverse=True):
        layer_lr = head_lr * (decay_factor ** (n_layers - layer_idx))
        d_list, nd_list = encoder_layer_params[layer_idx]
        if d_list:
            param_groups.append({"params": d_list, "lr": layer_lr, "weight_decay": weight_decay})
        if nd_list:
            param_groups.append({"params": nd_list, "lr": layer_lr, "weight_decay": 0.0})

    embed_lr = head_lr * (decay_factor ** n_layers)
    if embed_params_d:
        param_groups.append({"params": embed_params_d, "lr": embed_lr, "weight_decay": weight_decay})
    if embed_params_nd:
        param_groups.append({"params": embed_params_nd, "lr": embed_lr, "weight_decay": 0.0})

    total_params = sum(p.numel() for g in param_groups for p in g["params"])
    print(f"    LLRD optimizer: {len(param_groups)} groups, {n_layers} layers, "
          f"decay={decay_factor}, head_lr={head_lr:.2e}, embed_lr={embed_lr:.2e}, "
          f"{total_params:,} params")
    return torch.optim.AdamW(param_groups, weight_decay=weight_decay)


def _quick_val_predictions(
    model: nn.Module,
    val_subset: list[dict],
    device: torch.device,
    bs: int,
    use_amp: bool,
    amp_dtype: torch.dtype,
) -> Counter:
    """Fast validation pass returning prediction distribution."""
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, len(val_subset), bs):
            batch = val_subset[i : i + bs]
            texts_a = [r["source_text"] for r in batch]
            texts_b = [r["target_text"] for r in batch]
            encoding = model.tokenize_batch(texts_a, texts_b)
            encoding = {k: v.to(device) for k, v in encoding.items()}
            with torch.amp.autocast("cuda", enabled=use_amp, dtype=amp_dtype):
                logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
            preds.extend(logits.argmax(dim=1).cpu().tolist())
    model.train()
    return Counter(preds)


def _is_collapsed(pred_dist: Counter, n_classes: int = 4) -> bool:
    """True if any class has <2% of predictions or <3 unique classes predicted."""
    total = sum(pred_dist.values())
    if total == 0:
        return True
    if len(pred_dist) < 3:
        return True
    for cls in range(n_classes):
        if pred_dist.get(cls, 0) / total < _COLLAPSE_MIN_CLASS_PCT:
            return True
    return False


def train_cross_encoder(
    model_name: str,
    train_path: str,
    val_path: str,
    output_dir: str,
    contrastive_init: str | None = None,
    learning_rate: float = 2e-5,
    batch_size: int = 8,
    epochs: int = 15,
    warmup_ratio: float = 0.1,
    weight_decay: float = 0.01,
    dropout: float = 0.1,
    loss_type: str = "kl",
    sigma: float = 0.40,
    human_cal_weight: int = 5,
    encoder_lr_factor: float = 0.1,
    use_llrd: bool = False,
    llrd_decay: float = 0.85,
    **_extra,
) -> Dict[str, Any]:
    """Train a cross-encoder classifier, logging metrics to the active W&B run.

    Returns dict with val_macro_f1, train_acc, val_acc for monitoring guards.
    """
    from classifier.ensemble.cross_encoder import CrossEncoderClassifier
    from classifier.ensemble.kl_ordinal_loss import kl_ordinal_loss, ordinal_soft_targets
    from classifier.data.split_human_cal import split_human_cal

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bs = min(batch_size, 32)

    init_from = model_name
    if contrastive_init:
        cdir = Path(contrastive_init)
        has_weights = (
            (cdir / "model.safetensors").exists()
            or (cdir / "pytorch_model.bin").exists()
        )
        if has_weights:
            init_from = str(cdir)
        elif (cdir / "config.json").exists():
            print(f"    WARNING: contrastive checkpoint incomplete, using pretrained {model_name}")

    is_deberta = "deberta" in init_from.lower()
    use_amp = device.type == "cuda"
    amp_dtype = torch.bfloat16 if is_deberta else torch.float16

    model = CrossEncoderClassifier(
        model_name=init_from,
        n_classes=4,
        max_length=256,
        dropout=dropout,
        head_type="kl",
    )
    model = model.to(device)

    scaler = torch.amp.GradScaler("cuda") if (use_amp and not is_deberta) else None

    raw_data = []
    with open(train_path) as f:
        for line in f:
            raw_data.append(json.loads(line))

    pair_groups: dict[tuple, list] = {}
    for r in raw_data:
        key = (r["source_text"], r["target_text"])
        pair_groups.setdefault(key, []).append(r)

    train_data = []
    for key, rows in pair_groups.items():
        if len(rows) == 1:
            chosen = dict(rows[0])
        else:
            soft_target = [0.0] * 4
            total_w = 0.0
            for r in rows:
                w = r.get("sample_weight", 1.0)
                soft_target[r["tier_label"]] += w
                total_w += w
            if total_w > 0:
                soft_target = [s / total_w for s in soft_target]
            chosen = dict(rows[0])
            chosen["soft_target"] = soft_target
            chosen["tier_label"] = max(range(4), key=lambda i: soft_target[i])
            chosen["sample_weight"] = total_w / len(rows)
        train_data.append(chosen)

    n_soft = sum(1 for r in train_data if "soft_target" in r)
    print(f"  CE dedup: {len(raw_data)} -> {len(train_data)} unique pairs ({n_soft} with soft targets)")

    human_train, human_val, _, _ = split_human_cal()

    sample_weights = np.array(
        [1.0] * len(train_data) + [float(human_cal_weight)] * len(human_train)
    )
    train_data = train_data + human_train

    val_data_expert = []
    with open(val_path) as f:
        for line in f:
            val_data_expert.append(json.loads(line))
    val_data = human_val

    class_counts = np.bincount([r["tier_label"] for r in train_data], minlength=4)
    class_weights_arr = 1.0 / np.maximum(class_counts, 1)
    per_sample_class_weight = np.array([class_weights_arr[r["tier_label"]] for r in train_data])
    combined_weight = per_sample_class_weight * sample_weights

    if use_llrd:
        optimizer = _build_llrd_optimizer(model, head_lr=learning_rate,
                                         decay_factor=llrd_decay, weight_decay=weight_decay)
    else:
        head_params = [p for n, p in model.named_parameters() if "classifier" in n]
        encoder_params = [p for n, p in model.named_parameters() if "classifier" not in n]
        optimizer = torch.optim.AdamW([
            {"params": head_params, "lr": learning_rate},
            {"params": encoder_params, "lr": learning_rate * encoder_lr_factor},
        ], weight_decay=weight_decay)

    n_steps = (len(train_data) // bs) * epochs
    warmup_steps = int(n_steps * warmup_ratio)
    scheduler = torch.optim.lr_scheduler.LinearLR(
        optimizer, start_factor=0.1, total_iters=warmup_steps
    )

    best_f1 = 0.0
    best_checkpoint_path = Path(output_dir) / "best"
    patience_counter = 0
    collapse_consecutive = 0
    collapse_recoveries = 0
    final_metrics: Dict[str, Any] = {}

    val_quick_subset = val_data_expert[:min(200, len(val_data_expert))]

    for epoch in range(epochs):
        model.train()
        sampler = WeightedRandomSampler(
            weights=torch.DoubleTensor(combined_weight),
            num_samples=len(train_data),
            replacement=True,
        )
        epoch_indices = list(sampler)
        epoch_data = [train_data[i] for i in epoch_indices]

        epoch_loss = 0.0
        n_batches = 0
        max_grad_norm = 0.0
        nan_skips = 0
        correct = 0
        total = 0
        step_in_epoch = 0

        for i in range(0, len(epoch_data), bs):
            batch = epoch_data[i : i + bs]
            texts_a = [r["source_text"] for r in batch]
            texts_b = [r["target_text"] for r in batch]
            labels = torch.tensor([r["tier_label"] for r in batch], device=device)

            batch_soft = None
            if any("soft_target" in r for r in batch):
                batch_soft = []
                for r in batch:
                    if "soft_target" in r:
                        batch_soft.append(r["soft_target"])
                    else:
                        st = ordinal_soft_targets(
                            torch.tensor([r["tier_label"]]), n_classes=4, sigma=sigma
                        )
                        batch_soft.append(st.squeeze(0).tolist())
                batch_soft = torch.tensor(batch_soft, device=device, dtype=torch.float32)

            encoding = model.tokenize_batch(texts_a, texts_b)
            encoding = {k: v.to(device) for k, v in encoding.items()}

            with torch.amp.autocast("cuda", enabled=use_amp, dtype=amp_dtype):
                logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
                loss = kl_ordinal_loss(logits, labels, n_classes=4, sigma=sigma,
                                       soft_targets=batch_soft)

            if not torch.isfinite(loss):
                nan_skips += 1
                optimizer.zero_grad()
                continue

            optimizer.zero_grad()
            if scaler:
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0).item()
                if not (grad_norm < float("inf")):
                    scaler.update()
                    nan_skips += 1
                    continue
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0).item()
                if not (grad_norm < float("inf")):
                    nan_skips += 1
                    continue
                optimizer.step()
            scheduler.step()

            preds = logits.detach().argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            epoch_loss += loss.item()
            max_grad_norm = max(max_grad_norm, grad_norm)
            n_batches += 1
            step_in_epoch += 1

            # --- Mid-epoch collapse check ---
            if step_in_epoch % _MID_EPOCH_VAL_INTERVAL == 0 and step_in_epoch > 0:
                quick_dist = _quick_val_predictions(
                    model, val_quick_subset, device, bs, use_amp, amp_dtype,
                )
                if _is_collapsed(quick_dist):
                    print(f"    MID-EPOCH COLLAPSE at epoch {epoch} step {step_in_epoch}: {dict(quick_dist)}")
                    wandb.log({"mid_epoch_collapse": 1, "collapse_step": step_in_epoch})
                    if best_checkpoint_path.exists() and collapse_recoveries < _COLLAPSE_MAX_RECOVERIES:
                        collapse_recoveries += 1
                        print(f"    RECOVERY #{collapse_recoveries}: reloading best checkpoint, halving LR")
                        model = type(model).load(best_checkpoint_path).to(device)
                        for pg in optimizer.param_groups:
                            pg["lr"] *= 0.5
                        wandb.log({"collapse_recovery": collapse_recoveries})
                    elif collapse_recoveries >= _COLLAPSE_MAX_RECOVERIES:
                        print(f"    KILL: {_COLLAPSE_MAX_RECOVERIES} recoveries exhausted")
                        wandb.alert(title="Collapse Kill",
                                    text=f"Run killed after {collapse_recoveries} recovery attempts")
                        break

        avg_loss = epoch_loss / max(n_batches, 1)
        train_acc = correct / max(total, 1)

        # --- Full epoch validation ---
        model.eval()
        val_preds_human, val_labels_human = [], []
        val_kl_loss_sum, val_kl_batches = 0.0, 0
        with torch.no_grad():
            for i in range(0, len(val_data), bs):
                batch = val_data[i : i + bs]
                texts_a = [r["source_text"] for r in batch]
                texts_b = [r["target_text"] for r in batch]
                labels_batch = [r["tier_label"] for r in batch]
                labels_t = torch.tensor(labels_batch, device=device)
                encoding = model.tokenize_batch(texts_a, texts_b)
                encoding = {k: v.to(device) for k, v in encoding.items()}
                with torch.amp.autocast("cuda", enabled=use_amp, dtype=amp_dtype):
                    logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
                    val_loss_batch = kl_ordinal_loss(logits, labels_t, n_classes=4, sigma=sigma)
                val_preds_human.extend(logits.argmax(dim=1).cpu().tolist())
                val_labels_human.extend(labels_batch)
                val_kl_loss_sum += val_loss_batch.item()
                val_kl_batches += 1

        val_kl_loss = val_kl_loss_sum / max(val_kl_batches, 1)
        human_val_f1 = f1_score(val_labels_human, val_preds_human, average="macro")
        human_val_acc = accuracy_score(val_labels_human, val_preds_human)
        n_unique_preds = len(set(val_preds_human))

        val_preds_expert, val_labels_expert = [], []
        with torch.no_grad():
            for i in range(0, len(val_data_expert), bs):
                batch = val_data_expert[i : i + bs]
                texts_a = [r["source_text"] for r in batch]
                texts_b = [r["target_text"] for r in batch]
                labels_batch = [r["tier_label"] for r in batch]
                encoding = model.tokenize_batch(texts_a, texts_b)
                encoding = {k: v.to(device) for k, v in encoding.items()}
                with torch.amp.autocast("cuda", enabled=use_amp, dtype=amp_dtype):
                    logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
                val_preds_expert.extend(logits.argmax(dim=1).cpu().tolist())
                val_labels_expert.extend(labels_batch)

        expert_val_f1 = f1_score(val_labels_expert, val_preds_expert, average="macro")

        # --- Collapse detection (stricter than v8b) ---
        pred_dist = Counter(val_preds_human)
        epoch_collapsed = _is_collapsed(pred_dist)

        if epoch_collapsed:
            combined_f1 = 0.0
            collapse_consecutive += 1
            print(f"    COLLAPSE at epoch {epoch}: {dict(pred_dist)} (consecutive={collapse_consecutive})")
        else:
            combined_f1 = 0.5 * human_val_f1 + 0.5 * expert_val_f1
            collapse_consecutive = 0

        per_class_f1 = f1_score(val_labels_human, val_preds_human, average=None, labels=[0, 1, 2, 3])

        wandb.log({
            "epoch": epoch,
            "train_loss": avg_loss,
            "train_acc": train_acc,
            "val_kl_loss": val_kl_loss,
            "train_val_loss_gap": avg_loss - val_kl_loss,
            "max_grad_norm": max_grad_norm,
            "human_val_macro_f1": human_val_f1,
            "human_val_tier_accuracy": human_val_acc,
            "expert_val_macro_f1": expert_val_f1,
            "combined_f1": combined_f1,
            "n_unique_preds": n_unique_preds,
            "pred_class_0_pct": pred_dist.get(0, 0) / max(len(val_preds_human), 1),
            "pred_class_1_pct": pred_dist.get(1, 0) / max(len(val_preds_human), 1),
            "pred_class_2_pct": pred_dist.get(2, 0) / max(len(val_preds_human), 1),
            "pred_class_3_pct": pred_dist.get(3, 0) / max(len(val_preds_human), 1),
            "f1_class_0": per_class_f1[0] if len(per_class_f1) > 0 else 0.0,
            "f1_class_1": per_class_f1[1] if len(per_class_f1) > 1 else 0.0,
            "f1_class_2": per_class_f1[2] if len(per_class_f1) > 2 else 0.0,
            "f1_class_3": per_class_f1[3] if len(per_class_f1) > 3 else 0.0,
            "nan_skips": nan_skips,
            "collapse_recoveries": collapse_recoveries,
        })

        # --- Epoch-level collapse recovery ---
        if collapse_consecutive >= _COLLAPSE_PATIENCE:
            if collapse_recoveries >= _COLLAPSE_MAX_RECOVERIES:
                print(f"    KILL: {collapse_consecutive} consecutive collapsed epochs, "
                      f"{collapse_recoveries} recoveries exhausted")
                wandb.alert(title="Collapse Kill",
                            text=f"Run killed: {collapse_consecutive} collapsed epochs, "
                                 f"{collapse_recoveries} recoveries failed")
                break
            collapse_recoveries += 1
            collapse_consecutive = 0
            print(f"    EPOCH RECOVERY #{collapse_recoveries}: reloading best, halving LR")
            if best_checkpoint_path.exists():
                model = type(model).load(best_checkpoint_path).to(device)
            for pg in optimizer.param_groups:
                pg["lr"] *= 0.5
            wandb.log({"collapse_recovery": collapse_recoveries})
            continue

        if combined_f1 > best_f1:
            best_f1 = combined_f1
            patience_counter = 0
            model.save(best_checkpoint_path)
            wandb.log({"best_epoch": epoch, "best_combined_f1": best_f1})
        elif combined_f1 > 0:
            patience_counter += 1
            if patience_counter >= 3:
                print(f"    Early stopping at epoch {epoch}")
                break

        final_metrics = {
            "val_macro_f1": human_val_f1,
            "train_acc": train_acc,
            "val_acc": human_val_acc,
            "expert_val_f1": expert_val_f1,
            "combined_f1": combined_f1,
            "best_combined_f1": best_f1,
            "collapse_recoveries": collapse_recoveries,
        }

    import gc
    del model, optimizer
    if scaler:
        del scaler
    gc.collect()
    torch.cuda.empty_cache()

    return final_metrics
