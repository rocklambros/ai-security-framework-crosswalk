# classifier/lambda/train_all.py
"""Lambda training orchestrator — 9-phase pipeline for crosswalk-v2.

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

def phase3_finetune_sweeps(sweep_count: int = 50) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print(f"PHASE 3: Cross-encoder fine-tuning ({sweep_count} trials/model)")
    print("=" * 60)

    import importlib
    import wandb
    from classifier.ensemble.cross_encoder import CrossEncoderClassifier
    from classifier.ensemble.corn_loss import corn_loss, corn_label_from_logits
    _wc = importlib.import_module("classifier.lambda.wandb_config")
    CE_SWEEP_CONFIG = _wc.CE_SWEEP_CONFIG
    CROSS_ENCODER_MODELS = _wc.CROSS_ENCODER_MODELS
    WANDB_ENTITY = _wc.WANDB_ENTITY
    WANDB_PROJECT = _wc.WANDB_PROJECT

    sweep_ids = []
    for model_cfg in CROSS_ENCODER_MODELS:
        name = model_cfg["name"]
        model_id = model_cfg["model_id"]
        output_dir = Path(f"runs/ce_v2/{name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if a pretrained SimCSE checkpoint exists
        simcse_dir = Path(f"runs/ce_v2/contrastive/{name}")
        init_from = str(simcse_dir) if (simcse_dir / "config.json").exists() else model_id

        print(f"  [phase3] creating WANDB sweep for {name}")
        sweep_cfg = {**CE_SWEEP_CONFIG, "name": f"ce-sweep-{name}"}
        sweep_id = wandb.sweep(sweep_cfg, project=WANDB_PROJECT, entity=WANDB_ENTITY)

        def train_fn(model_name=name, model_path=init_from, out=str(output_dir)):
            """WANDB agent function — one trial."""
            import torch
            import numpy as np
            from sklearn.metrics import f1_score, accuracy_score

            # Clear GPU memory from previous trial
            torch.cuda.empty_cache()

            run = wandb.init()
            config = dict(run.config)

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            use_amp = device.type == "cuda"
            scaler = torch.amp.GradScaler("cuda") if use_amp else None

            loss_type = config.get("loss_type", "kl")
            sigma = config.get("sigma", 0.75)

            # Build cross-encoder with appropriate head
            model = CrossEncoderClassifier(
                model_name=model_path,
                n_classes=4,
                max_length=256,
                dropout=config.get("dropout", 0.1),
                head_type=loss_type,
            )
            model = model.to(device)

            # Load training data
            train_data = []
            with open("data/splits/expert_train.jsonl") as f:
                for line in f:
                    train_data.append(json.loads(line))

            val_data = []
            with open("data/splits/expert_val.jsonl") as f:
                for line in f:
                    val_data.append(json.loads(line))

            lr = config.get("learning_rate", 2e-5)
            bs = config.get("batch_size", 32)
            epochs = config.get("epochs", 5)
            warmup_ratio = config.get("warmup_ratio", 0.1)
            wd = config.get("weight_decay", 0.01)

            # Clamp batch size for GPU memory safety
            bs = min(bs, 32)

            optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
            n_steps = (len(train_data) // bs) * epochs
            warmup_steps = int(n_steps * warmup_ratio)
            scheduler = torch.optim.lr_scheduler.LinearLR(
                optimizer, start_factor=0.1, total_iters=warmup_steps
            )

            best_f1 = 0.0
            patience_counter = 0

            for epoch in range(epochs):
                model.train()
                np.random.shuffle(train_data)
                epoch_loss = 0.0
                n_batches = 0

                for i in range(0, len(train_data), bs):
                    batch = train_data[i:i+bs]
                    texts_a = [r["source_text"] for r in batch]
                    texts_b = [r["target_text"] for r in batch]
                    labels = torch.tensor([r["tier_label"] for r in batch], device=device)

                    encoding = model.tokenize_batch(texts_a, texts_b)
                    encoding = {k: v.to(device) for k, v in encoding.items()}

                    with torch.amp.autocast("cuda", enabled=use_amp):
                        logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
                        if loss_type == "kl":
                            from classifier.ensemble.kl_ordinal_loss import kl_ordinal_loss
                            loss = kl_ordinal_loss(logits, labels, n_classes=4, sigma=sigma)
                        else:
                            loss = corn_loss(logits, labels, n_classes=4)

                    optimizer.zero_grad()
                    if scaler:
                        scaler.scale(loss).backward()
                        scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        optimizer.step()
                    scheduler.step()

                    epoch_loss += loss.item()
                    n_batches += 1

                avg_loss = epoch_loss / max(n_batches, 1)

                # Validation
                model.eval()
                val_preds = []
                val_labels = []
                with torch.no_grad():
                    for i in range(0, len(val_data), bs):
                        batch = val_data[i:i+bs]
                        texts_a = [r["source_text"] for r in batch]
                        texts_b = [r["target_text"] for r in batch]
                        labels_batch = [r["tier_label"] for r in batch]

                        encoding = model.tokenize_batch(texts_a, texts_b)
                        encoding = {k: v.to(device) for k, v in encoding.items()}

                        with torch.amp.autocast("cuda", enabled=use_amp):
                            logits, _ = model.forward(encoding["input_ids"], encoding["attention_mask"])
                        if loss_type == "kl":
                            preds = logits.argmax(dim=1).cpu().tolist()
                        else:
                            preds = corn_label_from_logits(logits, n_classes=4).cpu().tolist()
                        val_preds.extend(preds)
                        val_labels.extend(labels_batch)

                val_f1 = f1_score(val_labels, val_preds, average="macro")
                val_acc = accuracy_score(val_labels, val_preds)

                wandb.log({
                    "epoch": epoch,
                    "train_loss": avg_loss,
                    "val_macro_f1": val_f1,
                    "val_tier_accuracy": val_acc,
                    "learning_rate": optimizer.param_groups[0]["lr"],
                    "loss_type": loss_type,
                    "sigma": sigma if loss_type == "kl" else 0.0,
                })

                if val_f1 > best_f1:
                    best_f1 = val_f1
                    patience_counter = 0
                    model.save(Path(out) / "best")
                    wandb.log({"best_epoch": epoch, "best_val_macro_f1": best_f1})
                else:
                    patience_counter += 1
                    if patience_counter >= 3:
                        print(f"    Early stopping at epoch {epoch}")
                        break

            # Clean up GPU memory
            del model, optimizer
            if scaler:
                del scaler
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
    for split in ["human_test_frozen.jsonl", "human_cal.jsonl"]:
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
    print("PHASE 8: Mondrian conformal calibration")
    print("=" * 60)

    import numpy as np
    from classifier.ensemble.feature_pipeline import FeaturePipeline
    from classifier.ensemble.stacker import LGBMStacker
    from classifier.ensemble.label_shift import adjust_label_shift, estimate_prior
    from classifier.data.tier_mapper import map_expert_tier

    ce_data = dict(np.load("data/processed/ce_features_v2.npz"))
    pipe = FeaturePipeline.load(Path("runs/stacker_v2/feature_pipeline"))

    # Find the latest stacker run
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

    # Load calibration data with proper labels
    cal_data = []
    cal_labels = []
    with open("data/splits/human_cal.jsonl") as f:
        for line in f:
            row = json.loads(line)
            cal_data.append(row)
            cal_labels.append(int(map_expert_tier(row["expert_tier"])))
    y_cal = np.array(cal_labels)

    # Get calibration features (cal is after train+val in ce_features)
    n_train_val = 0
    for split in ["expert_train.jsonl", "expert_val.jsonl"]:
        with open(f"data/splits/{split}") as f:
            n_train_val += sum(1 for _ in f)

    X_all = pipe.transform(ce_data)
    X_cal = X_all[n_train_val:n_train_val+len(cal_data)]

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

    # Mondrian conformal: per-class nonconformity scores
    alpha = 0.10
    n_classes = 4
    q_hat = {}
    coverage = {}

    for c in range(n_classes):
        mask = y_cal == c
        if mask.sum() == 0:
            q_hat[str(c)] = 1.0
            coverage[str(c)] = 1.0
            continue
        scores = 1.0 - proba_adjusted[mask, c]
        n_c = mask.sum()
        q_level = min(np.ceil((n_c + 1) * (1 - alpha)) / n_c, 1.0)
        q_hat[str(c)] = float(np.quantile(scores, q_level))
        coverage[str(c)] = float((scores <= q_hat[str(c)]).mean())

    conformal = {
        "alpha": alpha,
        "n_cal": len(cal_data),
        "marginal_coverage": 1 - alpha,
        "method": "mondrian",
        "q_hat": q_hat,
        "coverage": coverage,
        "label_shift_applied": True,
        "source_prior": source_prior.tolist(),
        "target_prior": target_prior.tolist(),
    }

    out = Path("runs/stacker_v2/conformal.json")
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
    from sklearn.metrics import f1_score, accuracy_score, confusion_matrix
    from classifier.ensemble.feature_pipeline import FeaturePipeline
    from classifier.ensemble.stacker import LGBMStacker
    from classifier.ensemble.label_shift import adjust_label_shift, estimate_prior
    from classifier.data.tier_mapper import map_expert_tier, TierLabel

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

    # Load model and features
    ce_data = dict(np.load("data/processed/ce_features_v2.npz"))
    pipe = FeaturePipeline.load(Path("runs/stacker_v2/feature_pipeline"))
    X_all = pipe.transform(ce_data)

    # Test features are after train+val+cal
    n_before_test = 0
    for split in ["expert_train.jsonl", "expert_val.jsonl", "human_cal.jsonl"]:
        with open(f"data/splits/{split}") as f:
            n_before_test += sum(1 for _ in f)
    X_test = X_all[n_before_test:n_before_test+len(test_data)]

    # Load stacker
    registry = Path("runs/registry.jsonl")
    last_run = None
    with registry.open() as f:
        for line in f:
            last_run = json.loads(line)
    stacker = LGBMStacker.load(Path(last_run["model_path"]))

    # Predict with label shift correction
    proba_raw = stacker.predict_proba(X_test)

    train_labels = []
    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            train_labels.append(json.loads(line)["tier_label"])
    source_prior = estimate_prior(np.array(train_labels), n_classes=4)

    cal_labels = []
    with open("data/splits/human_cal.jsonl") as f:
        for line in f:
            cal_labels.append(int(map_expert_tier(json.loads(line)["expert_tier"])))
    target_prior = estimate_prior(np.array(cal_labels), n_classes=4)

    proba_adj = adjust_label_shift(proba_raw, source_prior, target_prior)
    y_pred = proba_adj.argmax(axis=1)

    # Metrics
    tier_acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
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

    # Conformal prediction sets
    conformal_data = json.loads(Path("runs/stacker_v2/conformal.json").read_text())
    q_hat = conformal_data.get("q_hat", {})
    set_sizes = []
    covered = 0
    for i in range(len(y_test)):
        pred_set = []
        for c in range(4):
            score = 1.0 - proba_adj[i, c]
            if score <= float(q_hat.get(str(c), 1.0)):
                pred_set.append(c)
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
        "n_pairs": len(test_data),
        "confusion_matrix": cm_dict,
        "per_class": per_class,
        "bootstrap_ci_95": {
            "lower": boot_accs[int(0.025 * n_boot)],
            "point": tier_acc,
            "upper": boot_accs[int(0.975 * n_boot)],
        },
        "conformal": {
            "marginal_coverage": covered / len(y_test),
            "avg_set_size": float(np.mean(set_sizes)),
        },
        "label_shift_applied": True,
        "sacred_run": True,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
    }

    print(f"  [phase9] tier_accuracy={tier_acc:.4f}")
    print(f"  [phase9] macro_f1={macro_f1:.4f}")
    print(f"  [phase9] bootstrap 95% CI: [{sacred_result['bootstrap_ci_95']['lower']:.4f}, {sacred_result['bootstrap_ci_95']['upper']:.4f}]")
    print(f"  [phase9] conformal coverage={sacred_result['conformal']['marginal_coverage']:.4f}, avg_set_size={sacred_result['conformal']['avg_set_size']:.2f}")

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
        description="Lambda training orchestrator — crosswalk-v2 (9-phase pipeline)",
    )
    parser.add_argument(
        "--phase", type=int, default=None,
        choices=list(PHASES.keys()), metavar="N",
        help="Run a single phase (1-9). Omit to run all.",
    )
    parser.add_argument(
        "--sweep-count", type=int, default=50, dest="sweep_count",
        help="WANDB sweep trials per model for phase 3 (default: 50).",
    )
    return parser


def run_phase(phase_num: int, sweep_count: int) -> dict[str, Any]:
    fn = PHASES[phase_num]
    if phase_num == 3:
        return fn(sweep_count=sweep_count)
    return fn()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print("\n" + "#" * 60)
    print("  crosswalk-v2  |  Lambda training orchestrator")
    print("#" * 60)

    if args.phase is not None:
        name = PHASE_NAMES[args.phase]
        print(f"\nRunning phase {args.phase}: {name}")
        result = run_phase(args.phase, args.sweep_count)
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
