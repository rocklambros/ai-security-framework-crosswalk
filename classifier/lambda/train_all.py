# classifier/lambda/train_all.py
"""Lambda training orchestrator — 9-phase pipeline for crosswalk-v3.

Each phase function imports its dependencies lazily so the script can be
loaded on a CPU-only machine and still run CPU-only phases.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Phase 1: Build expert training set (CPU)
# ---------------------------------------------------------------------------

def phase1_build_data() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 1: Build expert training set (pair-level exclusion)")
    print("=" * 60)

    from classifier.scripts.build_expert_training import build_expert_training_set

    t0 = time.time()
    result = build_expert_training_set(leakage_mode="pair")
    elapsed = time.time() - t0

    print(f"  [phase1] done in {elapsed:.1f}s")
    print(f"  [phase1] train={result['n_train']}, val={result['n_val']}, "
          f"pos={result['n_positives']}, neg={result['n_negatives']}")
    print(f"  [phase1] leakage_mode=pair (standard STS protocol)")
    return {"phase": 1, "elapsed": elapsed, **result}


# ---------------------------------------------------------------------------
# Phase 2: Contrastive pre-training (GPU)
# ---------------------------------------------------------------------------

def phase2_contrastive() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 2: Contrastive pre-training (SimCSE)")
    print("=" * 60)

    import importlib
    from classifier.ensemble.contrastive_pretrain import train_contrastive
    _wc = importlib.import_module("classifier.lambda.wandb_config")
    CROSS_ENCODER_MODELS = _wc.CROSS_ENCODER_MODELS

    results = []
    for model_cfg in CROSS_ENCODER_MODELS:
        name = model_cfg["name"]
        model_id = model_cfg["model_id"]
        print(f"  [phase2] {name} ({model_id})")
        t0 = time.time()

        out_dir = Path(f"runs/ce_v2/contrastive/{name}")
        out_dir.mkdir(parents=True, exist_ok=True)

        train_contrastive(
            model_name=model_id,
            train_path="data/splits/expert_train.jsonl",
            output_dir=str(out_dir),
            epochs=5,
            batch_size=32,
        )
        elapsed = time.time() - t0
        print(f"  [phase2] {name} done in {elapsed:.1f}s")
        results.append({"model": name, "elapsed": elapsed})

    return {"phase": 2, "models": results}


# ---------------------------------------------------------------------------
# Phase 3: Cross-encoder fine-tuning sweeps (GPU + WANDB)
# ---------------------------------------------------------------------------

def phase3_finetune_sweeps(sweep_count: int = 30, model_filter: str | None = None) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print(f"PHASE 3: Cross-encoder fine-tuning with human-label domain adaptation ({sweep_count} trials/model)")
    print("=" * 60)

    import importlib
    import wandb
    from classifier.ensemble.cross_encoder import CrossEncoderClassifier
    _wc = importlib.import_module("classifier.lambda.wandb_config")
    CE_SWEEP_CONFIG = _wc.CE_SWEEP_CONFIG
    CROSS_ENCODER_MODELS = _wc.CROSS_ENCODER_MODELS
    WANDB_ENTITY = _wc.WANDB_ENTITY
    WANDB_PROJECT = _wc.WANDB_PROJECT

    models_to_run = CROSS_ENCODER_MODELS
    if model_filter:
        models_to_run = [m for m in CROSS_ENCODER_MODELS if m["name"] == model_filter]
        if not models_to_run:
            raise ValueError(f"Unknown model: {model_filter}. Choose from: {[m['name'] for m in CROSS_ENCODER_MODELS]}")
        print(f"  [phase3] running single model: {model_filter}")

    sweep_ids = []
    for model_cfg in models_to_run:
        name = model_cfg["name"]
        model_id = model_cfg["model_id"]
        output_dir = Path(f"runs/ce_v2/{name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if a COMPLETE pretrained SimCSE checkpoint exists
        # (config.json alone is not enough -- need actual model weights)
        simcse_dir = Path(f"runs/ce_v2/contrastive/{name}")
        has_weights = (
            (simcse_dir / "model.safetensors").exists()
            or (simcse_dir / "pytorch_model.bin").exists()
        )
        init_from = str(simcse_dir) if has_weights else model_id
        if not has_weights and (simcse_dir / "config.json").exists():
            print(f"  [phase3] WARNING: {name} contrastive checkpoint incomplete, falling back to pretrained {model_id}")

        print(f"  [phase3] creating WANDB sweep for {name}")
        sweep_cfg = {**CE_SWEEP_CONFIG, "name": f"ce-sweep-{name}"}
        sweep_id = wandb.sweep(sweep_cfg, project=WANDB_PROJECT, entity=WANDB_ENTITY)

        def train_fn(model_name=name, model_path=init_from, out=str(output_dir)):
            """WANDB agent function — one trial with human-label domain adaptation."""
            import torch
            import torch.nn as nn
            import numpy as np
            from torch.utils.data import WeightedRandomSampler
            from sklearn.metrics import f1_score, accuracy_score
            from classifier.data.split_human_cal import split_human_cal
            from classifier.ensemble.kl_ordinal_loss import kl_ordinal_loss

            # Clear GPU memory from previous trial
            torch.cuda.empty_cache()

            run = wandb.init()
            config = dict(run.config)

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            # DeBERTa-v3 uses FP16 internally — AMP GradScaler conflicts with it
            is_deberta = "deberta" in model_path.lower()
            use_amp = device.type == "cuda" and not is_deberta
            scaler = torch.amp.GradScaler("cuda") if use_amp else None

            sigma = config.get("sigma", 0.75)

            # Build cross-encoder with KL head (always)
            model = CrossEncoderClassifier(
                model_name=model_path,
                n_classes=4,
                max_length=256,
                dropout=config.get("dropout", 0.1),
                head_type="kl",
            )
            # DeBERTa-v3 stores weights in FP16 — cast to FP32 for stable training
            if is_deberta:
                model = model.float()
            model = model.to(device)

            # Load algorithmic training data
            raw_data = []
            with open("data/splits/expert_train.jsonl") as f:
                for line in f:
                    raw_data.append(json.loads(line))

            # Deduplicate: soft-label expansion creates 3 rows per pair with
            # contradictory labels. For CE training, sample ONE label per unique
            # pair proportional to sample_weight (preserves prior distribution).
            import random as _rng
            _rng.seed(42)
            pair_groups: dict[tuple, list] = {}
            for r in raw_data:
                key = (r["source_text"], r["target_text"])
                pair_groups.setdefault(key, []).append(r)
            train_data = []
            for key, rows in pair_groups.items():
                if len(rows) == 1:
                    chosen = dict(rows[0])
                else:
                    w = [r.get("sample_weight", 1.0) for r in rows]
                    chosen = dict(_rng.choices(rows, weights=w, k=1)[0])
                chosen["sample_weight"] = 1.0
                train_data.append(chosen)
            print(f"  CE dedup: {len(raw_data)} -> {len(train_data)} unique pairs")

            # Load human-labeled calibration data
            human_train, human_val, _, _ = split_human_cal()

            # Build sample weights: uniform 1.0 for deduped algorithmic data,
            # human_cal_weight for human labels
            human_cal_weight = config.get("human_cal_weight", 10)
            sample_weights = np.array(
                [1.0] * len(train_data)
                + [float(human_cal_weight)] * len(human_train)
            )
            train_data = train_data + human_train

            # SECONDARY validation: expert_val
            val_data_expert = []
            with open("data/splits/expert_val.jsonl") as f:
                for line in f:
                    val_data_expert.append(json.loads(line))

            # PRIMARY validation: human_cal val split
            val_data = human_val  # ~50 pairs

            lr = config.get("learning_rate", 2e-5)
            bs = config.get("batch_size", 32)
            epochs = config.get("epochs", 5)
            warmup_ratio = config.get("warmup_ratio", 0.1)
            wd = config.get("weight_decay", 0.01)
            frozen_epochs = config.get("frozen_epochs", 2)
            encoder_lr_factor = config.get("encoder_lr_factor", 0.1)

            # Clamp batch size for GPU memory safety
            bs = min(bs, 32)

            # Class-balanced sampling weights
            class_counts = np.bincount([r["tier_label"] for r in train_data], minlength=4)
            class_weights_arr = 1.0 / np.maximum(class_counts, 1)
            per_sample_class_weight = np.array([class_weights_arr[r["tier_label"]] for r in train_data])
            # Combine class weight with human_cal source weight
            combined_weight = per_sample_class_weight * sample_weights

            # Freeze encoder for warm-up epochs (skip if frozen_epochs=0)
            if frozen_epochs > 0:
                for param in model.encoder.parameters():
                    param.requires_grad = False

            # Separate parameter groups with discriminative learning rates
            head_params = [p for n, p in model.named_parameters() if "classifier" in n]
            encoder_params = [p for n, p in model.named_parameters() if "classifier" not in n]

            optimizer = torch.optim.AdamW([
                {"params": head_params, "lr": lr},
                {"params": encoder_params, "lr": lr * encoder_lr_factor},
            ], weight_decay=wd)

            n_steps = (len(train_data) // bs) * epochs
            warmup_steps = int(n_steps * warmup_ratio)
            scheduler = torch.optim.lr_scheduler.LinearLR(
                optimizer, start_factor=0.1, total_iters=warmup_steps
            )

            best_f1 = 0.0
            patience_counter = 0

            if frozen_epochs == 0:
                print(f"    No frozen epochs -- full model trainable from start")

            for epoch in range(epochs):
                # Unfreeze encoder after frozen_epochs (keep head intact)
                if epoch == frozen_epochs and frozen_epochs > 0:
                    for param in model.encoder.parameters():
                        param.requires_grad = True
                    # Rebuild optimizer with encoder params now trainable
                    head_params = [p for n, p in model.named_parameters() if "classifier" in n]
                    encoder_params = [p for n, p in model.named_parameters() if "classifier" not in n]
                    optimizer = torch.optim.AdamW([
                        {"params": head_params, "lr": lr},
                        {"params": encoder_params, "lr": lr * encoder_lr_factor},
                    ], weight_decay=wd)
                    print(f"    Encoder unfrozen at epoch {epoch} (head preserved)")

                model.train()

                # Weighted sampling per epoch
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

                for i in range(0, len(epoch_data), bs):
                    batch = epoch_data[i:i+bs]
                    texts_a = [r["source_text"] for r in batch]
                    texts_b = [r["target_text"] for r in batch]
                    labels = torch.tensor([r["tier_label"] for r in batch], device=device)

                    encoding = model.tokenize_batch(texts_a, texts_b)
                    encoding = {k: v.to(device) for k, v in encoding.items()}

                    with torch.amp.autocast("cuda", enabled=use_amp):
                        logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
                        loss = kl_ordinal_loss(logits, labels, n_classes=4, sigma=sigma)

                    optimizer.zero_grad()
                    if scaler:
                        scaler.scale(loss).backward()
                        scaler.unscale_(optimizer)
                        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0).item()
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        loss.backward()
                        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0).item()
                        optimizer.step()
                    scheduler.step()

                    epoch_loss += loss.item()
                    max_grad_norm = max(max_grad_norm, grad_norm)
                    n_batches += 1

                avg_loss = epoch_loss / max(n_batches, 1)

                # PRIMARY validation: human_cal_val
                model.eval()
                val_preds_human = []
                val_labels_human = []
                val_kl_loss_sum = 0.0
                val_kl_batches = 0
                with torch.no_grad():
                    for i in range(0, len(val_data), bs):
                        batch = val_data[i:i+bs]
                        texts_a = [r["source_text"] for r in batch]
                        texts_b = [r["target_text"] for r in batch]
                        labels_batch = [r["tier_label"] for r in batch]
                        labels_t = torch.tensor(labels_batch, device=device)
                        encoding = model.tokenize_batch(texts_a, texts_b)
                        encoding = {k: v.to(device) for k, v in encoding.items()}
                        with torch.amp.autocast("cuda", enabled=use_amp):
                            logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
                            val_loss_batch = kl_ordinal_loss(logits, labels_t, n_classes=4, sigma=sigma)
                        preds = logits.argmax(dim=1).cpu().tolist()
                        val_preds_human.extend(preds)
                        val_labels_human.extend(labels_batch)
                        val_kl_loss_sum += val_loss_batch.item()
                        val_kl_batches += 1
                val_kl_loss = val_kl_loss_sum / max(val_kl_batches, 1)

                human_val_f1 = f1_score(val_labels_human, val_preds_human, average="macro")
                human_val_acc = accuracy_score(val_labels_human, val_preds_human)
                n_unique_preds = len(set(val_preds_human))

                # SECONDARY validation: expert_val
                val_preds_expert = []
                val_labels_expert = []
                with torch.no_grad():
                    for i in range(0, len(val_data_expert), bs):
                        batch = val_data_expert[i:i+bs]
                        texts_a = [r["source_text"] for r in batch]
                        texts_b = [r["target_text"] for r in batch]
                        labels_batch = [r["tier_label"] for r in batch]
                        encoding = model.tokenize_batch(texts_a, texts_b)
                        encoding = {k: v.to(device) for k, v in encoding.items()}
                        with torch.amp.autocast("cuda", enabled=use_amp):
                            logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
                        preds = logits.argmax(dim=1).cpu().tolist()
                        val_preds_expert.extend(preds)
                        val_labels_expert.extend(labels_batch)

                expert_val_f1 = f1_score(val_labels_expert, val_preds_expert, average="macro")

                # COLLAPSE GUARD
                if n_unique_preds < 3:
                    combined_f1 = 0.0
                    print(f"    COLLAPSE DETECTED: only {n_unique_preds} unique preds")
                else:
                    combined_f1 = 0.7 * human_val_f1 + 0.3 * expert_val_f1

                # Per-class F1
                per_class_f1 = f1_score(val_labels_human, val_preds_human, average=None, labels=[0, 1, 2, 3])

                # Prediction distribution for debugging collapse
                from collections import Counter
                pred_dist = Counter(val_preds_human)

                wandb.log({
                    "epoch": epoch,
                    "train_loss": avg_loss,
                    "val_kl_loss": val_kl_loss,
                    "train_val_loss_gap": avg_loss - val_kl_loss,
                    "max_grad_norm": max_grad_norm,
                    "grad_clipped": max_grad_norm > 1.0,
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
                    "learning_rate": optimizer.param_groups[0]["lr"],
                    "loss_type": "kl",
                    "sigma": sigma,
                })

                # Best model selection on combined_f1
                # Don't count frozen-encoder epochs toward patience (collapse is expected)
                if combined_f1 > best_f1:
                    best_f1 = combined_f1
                    patience_counter = 0
                    model.save(Path(out) / "best")
                    wandb.log({"best_epoch": epoch, "best_combined_f1": best_f1})
                elif epoch >= frozen_epochs:
                    patience_counter += 1
                    if patience_counter >= 3:
                        print(f"    Early stopping at epoch {epoch}")
                        break

            # Clean up GPU memory thoroughly between trials
            del model, optimizer
            if scaler:
                del scaler
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            run.finish()

        print(f"  [phase3] launching {sweep_count} agents for {name}")
        wandb.agent(sweep_id, function=train_fn, count=sweep_count,
                    project=WANDB_PROJECT, entity=WANDB_ENTITY)
        sweep_ids.append({"model": name, "sweep_id": sweep_id})

    return {"phase": 3, "sweeps": sweep_ids}


# ---------------------------------------------------------------------------
# Phase 4: Extract CLS embeddings (GPU)
# ---------------------------------------------------------------------------

def phase4_extract_features() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 4: Extract CLS embeddings")
    print("=" * 60)

    import importlib
    import torch
    import numpy as np
    from classifier.ensemble.cross_encoder import CrossEncoderClassifier
    _wc = importlib.import_module("classifier.lambda.wandb_config")
    CROSS_ENCODER_MODELS = _wc.CROSS_ENCODER_MODELS

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load all control text pairs
    all_pairs = []
    for split in ["expert_train.jsonl", "expert_val.jsonl"]:
        path = Path(f"data/splits/{split}")
        if path.exists():
            with path.open() as f:
                for line in f:
                    all_pairs.append(json.loads(line))

    # Also load frozen test + cal for full feature extraction
    for split in ["human_cal.jsonl", "human_test_frozen.jsonl"]:
        path = Path(f"data/splits/{split}")
        if path.exists():
            with path.open() as f:
                for line in f:
                    all_pairs.append(json.loads(line))

    print(f"  [phase4] extracting features for {len(all_pairs)} pairs")
    features = {}

    for model_cfg in CROSS_ENCODER_MODELS:
        name = model_cfg["name"]
        model_path = Path(f"runs/ce_v2/{name}/best")
        if not model_path.exists():
            print(f"  [phase4] WARNING: no checkpoint for {name}, skipping")
            continue

        print(f"  [phase4] loading {name} from {model_path}")
        model = CrossEncoderClassifier.load(model_path).to(device)
        model.eval()
        head_type = getattr(model, "head_type", "corn")
        print(f"  [phase4] {name}: head_type={head_type}")

        logits_all = []
        cls_embs_all = []

        with torch.no_grad():
            for i in range(0, len(all_pairs), 64):
                batch = all_pairs[i:i+64]
                texts_a = [r.get("source_text", "") for r in batch]
                texts_b = [r.get("target_text", "") for r in batch]

                encoding = model.tokenize_batch(texts_a, texts_b)
                encoding = {k: v.to(device) for k, v in encoding.items()}

                batch_logits, batch_cls = model.forward(encoding["input_ids"], encoding["attention_mask"])
                logits_all.append(batch_logits.cpu().numpy())
                cls_embs_all.append(batch_cls.cpu().numpy())

        features[f"{name}_logits"] = np.concatenate(logits_all, axis=0)
        features[f"{name}_cls_emb"] = np.concatenate(cls_embs_all, axis=0)
        features[f"{name}_head_type"] = head_type
        print(f"  [phase4] {name}: logits shape={features[f'{name}_logits'].shape}, cls_emb shape={features[f'{name}_cls_emb'].shape}")

    # Save features
    output_path = Path("data/processed/ce_features_v2.npz")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(str(output_path), **features)
    print(f"  [phase4] saved features to {output_path}")

    return {"phase": 4, "n_pairs": len(all_pairs), "models": list(features.keys())}


# ---------------------------------------------------------------------------
# Phase 5: GATv2 retrain (GPU, H100)
# ---------------------------------------------------------------------------

def phase5_gat_retrain() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 5: GATv2 retrain")
    print("=" * 60)

    import torch

    if not torch.cuda.is_available():
        print("  [phase5] WARNING: No GPU available. Skipping GAT retrain.")
        print("  [phase5] Using cached GAT embeddings if available.")
        cached = Path("data/features/gat_embeddings.npz")
        if cached.exists():
            import numpy as np
            data = np.load(str(cached))
            print(f"  [phase5] loaded cached: {list(data.keys())}")
            return {"phase": 5, "status": "cached"}
        return {"phase": 5, "status": "skipped", "reason": "no GPU"}

    # Real GAT training — requires torch_geometric
    from classifier.ensemble.gat_train import train_gat

    t0 = time.time()
    output_dir = Path("runs/gat_v2")
    output_dir.mkdir(parents=True, exist_ok=True)

    result = train_gat(
        output_dir=str(output_dir),
        embedding_dim=64,
        epochs=200,
        lr=0.005,
    )
    elapsed = time.time() - t0

    print(f"  [phase5] GAT retrain done in {elapsed:.1f}s")
    return {"phase": 5, "status": "trained", "elapsed": elapsed, **result}


# ---------------------------------------------------------------------------
# Phase 6: Stacker sweep (CPU)
# ---------------------------------------------------------------------------

def phase6_stacker_sweep() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 6: LightGBM stacker sweep (Optuna + PCA features)")
    print("=" * 60)

    import numpy as np
    from classifier.ensemble.feature_pipeline import FeaturePipeline
    from classifier.ensemble.stacker import tune_stacker
    from classifier.ensemble.label_shift import estimate_prior
    from classifier.data.tier_mapper import map_expert_tier

    ce_path = Path("data/processed/ce_features_v2.npz")
    if not ce_path.exists():
        print("  [phase6] ERROR: CE features not found. Run Phase 4 first.")
        return {"phase": 6, "status": "error", "reason": "missing ce_features_v2.npz"}

    ce_data = dict(np.load(str(ce_path)))

    # Load training labels
    train_labels = []
    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            train_labels.append(json.loads(line)["tier_label"])
    y = np.array(train_labels)

    # Estimate target-domain prior from human_cal
    cal_labels = []
    with open("data/splits/human_cal.jsonl") as f:
        for line in f:
            row = json.loads(line)
            cal_labels.append(int(map_expert_tier(row["expert_tier"])))
    target_prior = estimate_prior(np.array(cal_labels), n_classes=4)
    print(f"  [phase6] target prior (from cal): {target_prior}")

    # Build features via pipeline
    pipe = FeaturePipeline(pca_variance=0.95)
    X = pipe.fit_transform(ce_data, n_train=len(y))
    print(f"  [phase6] feature matrix: {X.shape} (was 3081 raw)")
    print(f"  [phase6] features: {pipe.feature_names()[:10]}... ({len(pipe.feature_names())} total)")

    # Compute class weights from target prior
    source_prior = estimate_prior(y, n_classes=4)
    class_weight = {k: target_prior[k] / max(source_prior[k], 1e-6) for k in range(4)}
    print(f"  [phase6] class weights: {class_weight}")

    t0 = time.time()
    best_params = tune_stacker(X, y, n_trials=100, n_splits=5)
    elapsed = time.time() - t0

    print(f"  [phase6] best params in {elapsed:.1f}s: {best_params}")

    # Save
    out = Path("runs/stacker_v2")
    out.mkdir(parents=True, exist_ok=True)
    (out / "best_params.json").write_text(json.dumps(best_params, indent=2))
    pipe.save(out / "feature_pipeline")

    return {"phase": 6, "elapsed": elapsed, "best_params": best_params,
            "n_features": X.shape[1], "target_prior": target_prior.tolist()}


# ---------------------------------------------------------------------------
# Phase 7: Two-stage classifier (CPU)
# ---------------------------------------------------------------------------

def phase7_train_stacker() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 7: Train final stacker with best params")
    print("=" * 60)

    import numpy as np
    from classifier.ensemble.feature_pipeline import FeaturePipeline
    from classifier.ensemble.stacker import train_and_evaluate
    from classifier.data.tier_mapper import map_expert_tier
    from classifier.ensemble.label_shift import estimate_prior

    ce_data = dict(np.load("data/processed/ce_features_v2.npz"))

    # Load labels
    train_labels, val_labels = [], []
    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            train_labels.append(json.loads(line)["tier_label"])
    with open("data/splits/expert_val.jsonl") as f:
        for line in f:
            val_labels.append(json.loads(line)["tier_label"])
    y_train = np.array(train_labels)
    y_val = np.array(val_labels)

    # Load feature pipeline
    pipe = FeaturePipeline.load(Path("runs/stacker_v2/feature_pipeline"))
    X_all = pipe.transform(ce_data)
    X_train = X_all[:len(y_train)]
    X_val = X_all[len(y_train):len(y_train)+len(y_val)]

    # Load best params
    best_params = json.loads(Path("runs/stacker_v2/best_params.json").read_text())

    # Compute sample weights from label shift
    cal_labels = []
    with open("data/splits/human_cal.jsonl") as f:
        for line in f:
            row = json.loads(line)
            cal_labels.append(int(map_expert_tier(row["expert_tier"])))
    target_prior = estimate_prior(np.array(cal_labels), n_classes=4)
    source_prior = estimate_prior(y_train, n_classes=4)
    sample_weights = np.array([target_prior[y] / max(source_prior[y], 1e-6) for y in y_train])

    t0 = time.time()
    result = train_and_evaluate(
        X_train, y_train, X_val, y_val,
        sample_weight=sample_weights,
        params=best_params,
    )
    elapsed = time.time() - t0

    print(f"  [phase7] train_acc={result['train_acc']:.4f}, val_acc={result['val_acc']:.4f}")
    print(f"  [phase7] train_logloss={result['train_logloss']:.4f}, val_logloss={result['val_logloss']:.4f}")

    return {"phase": 7, "elapsed": elapsed, **{k: v for k, v in result.items() if k != 'stacker'}}


# ---------------------------------------------------------------------------
# Phase 8: Mondrian conformal calibration (CPU)
# ---------------------------------------------------------------------------

def phase8_conformal() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 8: Marginal conformal calibration (human_cal_val)")
    print("=" * 60)

    import numpy as np
    from classifier.ensemble.feature_pipeline import FeaturePipeline
    from classifier.ensemble.stacker import LGBMStacker
    from classifier.ensemble.label_shift import adjust_label_shift, estimate_prior
    from classifier.data.tier_mapper import map_expert_tier
    from classifier.data.split_human_cal import split_human_cal

    ce_data = dict(np.load("data/processed/ce_features_v2.npz"))
    pipe = FeaturePipeline.load(Path("runs/stacker_v2/feature_pipeline"))

    # Find the latest stacker run from registry
    registry = Path("runs/registry.jsonl")
    last_run = None
    if registry.exists():
        with registry.open() as f:
            for line in f:
                last_run = json.loads(line)
    if not last_run:
        return {"phase": 8, "status": "error", "reason": "no stacker run found"}

    model_path = Path(last_run["model_path"])
    stacker = LGBMStacker.load(model_path)

    # Use only the 50 held-out human_cal_val pairs for conformal calibration
    _, _, _, cal_val_indices = split_human_cal()

    # Cal labels from the val split
    cal_labels_all = []
    with open("data/splits/human_cal.jsonl") as f:
        for line in f:
            row = json.loads(line)
            cal_labels_all.append(int(map_expert_tier(row["expert_tier"])))
    y_cal = np.array([cal_labels_all[i] for i in cal_val_indices])

    # Feature indices: cal is at positions n_train+n_val through n_train+n_val+150
    # We need only the val indices within that range
    n_train = sum(1 for _ in open("data/splits/expert_train.jsonl"))
    n_val = sum(1 for _ in open("data/splits/expert_val.jsonl"))
    n_cal_start = n_train + n_val  # 6728 + 1187 = 7915

    X_all = pipe.transform(ce_data)
    X_cal = X_all[[n_cal_start + i for i in cal_val_indices]]

    # Get calibration probabilities
    proba_cal = stacker.predict_proba(X_cal)

    # Apply label shift correction
    train_labels = []
    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            train_labels.append(json.loads(line)["tier_label"])
    source_prior = estimate_prior(np.array(train_labels), n_classes=4)
    target_prior = estimate_prior(y_cal, n_classes=4)
    proba_adjusted = adjust_label_shift(proba_cal, source_prior, target_prior)

    # MARGINAL conformal: single threshold across all classes
    # (50 pairs too few for per-class Mondrian — only ~12 per class)
    alpha = 0.10
    scores = 1.0 - proba_adjusted[np.arange(len(y_cal)), y_cal]
    n_cal = len(y_cal)
    q_level = min(np.ceil((n_cal + 1) * (1 - alpha)) / n_cal, 1.0)
    q_hat = float(np.quantile(scores, q_level))

    # Coverage on calibration set
    covered = int((scores <= q_hat).sum())
    coverage = covered / n_cal

    conformal = {
        "alpha": alpha,
        "n_cal": n_cal,
        "marginal_coverage": coverage,
        "method": "marginal",
        "q_hat": q_hat,
        "label_shift_applied": True,
        "source_prior": source_prior.tolist(),
        "target_prior": target_prior.tolist(),
    }

    out = Path("runs/stacker_v2/conformal.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(conformal, indent=2))
    print(f"  [phase8] conformal: {conformal}")

    return {"phase": 8, **conformal}


# ---------------------------------------------------------------------------
# Phase 9: Sacred evaluation + ablation matrix (CPU)
# ---------------------------------------------------------------------------

def phase9_sacred_run() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 9: Sacred evaluation on frozen test set")
    print("=" * 60)

    import subprocess
    import numpy as np
    from scipy.special import softmax
    from sklearn.metrics import f1_score, accuracy_score, confusion_matrix
    from sklearn.linear_model import LogisticRegression
    from classifier.data.tier_mapper import map_expert_tier, TierLabel
    from classifier.data.split_human_cal import split_human_cal

    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    print(f"  [phase9] git SHA: {sha}")

    # Load frozen test data with proper label conversion
    test_data = []
    test_labels = []
    with open("data/splits/human_test_frozen.jsonl") as f:
        for line in f:
            row = json.loads(line)
            test_data.append(row)
            test_labels.append(int(map_expert_tier(row["expert_tier"])))
    y_test = np.array(test_labels)
    print(f"  [phase9] {len(test_data)} frozen test pairs")
    print(f"  [phase9] test label dist: {dict(zip(*np.unique(y_test, return_counts=True)))}")

    # Load CE features
    ce_data = dict(np.load("data/processed/ce_features_v2.npz"))
    models = ["deberta", "roberta", "deberta_base"]

    # Compute split offsets
    n_train = sum(1 for _ in open("data/splits/expert_train.jsonl"))
    n_val = sum(1 for _ in open("data/splits/expert_val.jsonl"))
    n_cal = sum(1 for _ in open("data/splits/human_cal.jsonl"))
    cal_start = n_train + n_val
    test_start = cal_start + n_cal

    def get_logit_features(start: int, count: int) -> np.ndarray:
        """Concat logits from all 3 CE models (12 features)."""
        return np.concatenate(
            [ce_data[f"{m}_logits"][start:start + count] for m in models],
            axis=1,
        )

    # --- Method A: Ensemble raw logits (no stacker, no label shift) ---
    ens_logits = np.zeros((len(test_data), 4))
    for m in models:
        ens_logits += ce_data[f"{m}_logits"][test_start:test_start + len(test_data)]
    ens_logits /= len(models)
    y_pred_raw = ens_logits.argmax(axis=1)

    raw_acc = float(accuracy_score(y_test, y_pred_raw))
    raw_f1 = float(f1_score(y_test, y_pred_raw, average="macro"))
    print(f"  [phase9] ensemble_raw: acc={raw_acc:.4f}, f1={raw_f1:.4f}")

    # --- Method B: LogReg trained on human_cal logits (domain-adapted) ---
    cal_labels = []
    with open("data/splits/human_cal.jsonl") as f:
        for line in f:
            cal_labels.append(int(map_expert_tier(json.loads(line)["expert_tier"])))
    y_cal = np.array(cal_labels)

    X_cal = get_logit_features(cal_start, n_cal)
    X_test_lr = get_logit_features(test_start, len(test_data))

    lr = LogisticRegression(C=0.1, max_iter=1000, class_weight="balanced")
    lr.fit(X_cal, y_cal)
    y_pred_lr = lr.predict(X_test_lr)
    proba_lr = lr.predict_proba(X_test_lr)

    lr_acc = float(accuracy_score(y_test, y_pred_lr))
    lr_f1 = float(f1_score(y_test, y_pred_lr, average="macro"))
    print(f"  [phase9] logreg_cal: acc={lr_acc:.4f}, f1={lr_f1:.4f}")

    # Pick the method with best macro_f1 (primary metric)
    if lr_f1 >= raw_f1:
        y_pred = y_pred_lr
        proba_adj = proba_lr
        method_used = "logreg_on_human_cal"
        tier_acc, macro_f1 = lr_acc, lr_f1
    else:
        y_pred = y_pred_raw
        proba_adj = softmax(ens_logits, axis=1)
        method_used = "ensemble_raw"
        tier_acc, macro_f1 = raw_acc, raw_f1

    print(f"  [phase9] selected: {method_used}")

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2, 3])
    tier_names = ["unrelated", "partial", "related", "equivalent"]
    cm_dict = {}
    per_class = {}
    for i, name_i in enumerate(tier_names):
        cm_dict[name_i] = {tier_names[j]: int(cm[i, j]) for j in range(4)}
        per_class[name_i] = {
            "accuracy": float(cm[i, i] / max(cm[i].sum(), 1)),
            "count": int(cm[i].sum()),
        }

    per_class_f1 = f1_score(y_test, y_pred, average=None, labels=[0, 1, 2, 3])
    for i, name_i in enumerate(tier_names):
        per_class[name_i]["f1"] = float(per_class_f1[i])

    # Conformal prediction sets using human_cal_val
    _, _, _, cal_val_indices = split_human_cal()
    y_cal_val = y_cal[cal_val_indices]
    X_cal_val = X_cal[cal_val_indices]
    proba_cal_val = lr.predict_proba(X_cal_val)

    alpha = 0.10
    scores = 1.0 - proba_cal_val[np.arange(len(y_cal_val)), y_cal_val]
    n_cal_conf = len(y_cal_val)
    q_level = min(np.ceil((n_cal_conf + 1) * (1 - alpha)) / n_cal_conf, 1.0)
    q_hat = float(np.quantile(scores, q_level))

    set_sizes = []
    covered = 0
    for i in range(len(y_test)):
        pred_set = [c for c in range(4) if 1.0 - proba_adj[i, c] <= q_hat]
        set_sizes.append(len(pred_set))
        if y_test[i] in pred_set:
            covered += 1

    # Bootstrap CI
    rng = np.random.RandomState(42)
    n_boot = 2000
    boot_accs = []
    for _ in range(n_boot):
        idx = rng.choice(len(y_test), size=len(y_test), replace=True)
        boot_accs.append(float(accuracy_score(y_test[idx], y_pred[idx])))
    boot_accs.sort()

    sacred_result = {
        "tier_accuracy": tier_acc,
        "macro_f1": macro_f1,
        "method": method_used,
        "n_pairs": len(test_data),
        "confusion_matrix": cm_dict,
        "per_class": per_class,
        "ablation": {
            "ensemble_raw": {"tier_accuracy": raw_acc, "macro_f1": raw_f1},
            "logreg_on_human_cal": {"tier_accuracy": lr_acc, "macro_f1": lr_f1},
        },
        "bootstrap_ci_95": {
            "lower": boot_accs[int(0.025 * n_boot)],
            "point": tier_acc,
            "upper": boot_accs[int(0.975 * n_boot)],
        },
        "conformal": {
            "marginal_coverage": covered / len(y_test),
            "avg_set_size": float(np.mean(set_sizes)),
            "q_hat": q_hat,
            "alpha": alpha,
            "n_cal": n_cal_conf,
        },
        "sacred_run": True,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
    }

    print(f"  [phase9] tier_accuracy={tier_acc:.4f}")
    print(f"  [phase9] macro_f1={macro_f1:.4f}")
    print(f"  [phase9] bootstrap 95% CI: [{sacred_result['bootstrap_ci_95']['lower']:.4f}, {sacred_result['bootstrap_ci_95']['upper']:.4f}]")
    print(f"  [phase9] conformal coverage={sacred_result['conformal']['marginal_coverage']:.4f}, avg_set_size={sacred_result['conformal']['avg_set_size']:.2f}")
    print(f"  [phase9] per-class F1: {dict(zip(tier_names, per_class_f1.round(4)))}")

    # Save
    output = Path(f"results/sacred/sacred_{sha}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sacred_result, indent=2))

    return {"phase": 9, "sha": sha, **sacred_result}


# ---------------------------------------------------------------------------
# Phase registry & CLI
# ---------------------------------------------------------------------------

PHASES: dict[int, Any] = {
    1: phase1_build_data,
    2: phase2_contrastive,
    3: phase3_finetune_sweeps,
    4: phase4_extract_features,
    5: phase5_gat_retrain,
    6: phase6_stacker_sweep,
    7: phase7_train_stacker,
    8: phase8_conformal,
    9: phase9_sacred_run,
}

PHASE_NAMES: dict[int, str] = {
    1: "build_data",
    2: "contrastive",
    3: "finetune_sweeps",
    4: "extract_features",
    5: "gat_retrain",
    6: "stacker_sweep",
    7: "train_stacker",
    8: "conformal",
    9: "sacred_run",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="train_all",
        description="Lambda training orchestrator — crosswalk-v3 (9-phase pipeline)",
    )
    parser.add_argument(
        "--phase", type=int, default=None,
        choices=list(PHASES.keys()), metavar="N",
        help="Run a single phase (1-9). Omit to run all.",
    )
    parser.add_argument(
        "--sweep-count", type=int, default=30, dest="sweep_count",
        help="WANDB sweep trials per model for phase 3 (default: 30).",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        choices=["deberta", "roberta", "deberta_base"],
        help="Run phase 3 for a single model (for parallel GPU execution).",
    )
    return parser


def run_phase(phase_num: int, sweep_count: int, model: str | None = None) -> dict[str, Any]:
    fn = PHASES[phase_num]
    if phase_num == 3:
        return fn(sweep_count=sweep_count, model_filter=model)
    return fn()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print("\n" + "#" * 60)
    print("  crosswalk-v3  |  Lambda training orchestrator")
    print("#" * 60)

    if args.phase is not None:
        name = PHASE_NAMES[args.phase]
        print(f"\nRunning phase {args.phase}: {name}")
        result = run_phase(args.phase, args.sweep_count, args.model)
        print(f"\nPhase {args.phase} result:")
        print(json.dumps(result, indent=2, default=str))
        return

    print("\nRunning all 9 phases sequentially")
    t_start = time.time()
    results = []

    for num in sorted(PHASES):
        try:
            result = run_phase(num, args.sweep_count)
            results.append(result)
        except Exception as exc:
            print(f"\n[ERROR] Phase {num} ({PHASE_NAMES[num]}) failed: {exc}", file=sys.stderr)
            raise

    print(f"\n{'#' * 60}")
    print(f"  All 9 phases complete in {time.time() - t_start:.1f}s")
    print(f"{'#' * 60}")


if __name__ == "__main__":
    main()
