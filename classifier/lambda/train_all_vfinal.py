"""v_final 7-phase training orchestrator.

Simplified from v8b's 10 phases:
- REMOVED: SimCSE (caused collapse), GATv2 (negligible impact), OpenCRE extraction (wrong domain)
- ADDED: focal loss, CORN loss, OverfittingGuard, bi-encoder (BGE)

Usage:
    python -m classifier.lambda.train_all_vfinal --phase 0
    python -m classifier.lambda.train_all_vfinal --all
    python -m classifier.lambda.train_all_vfinal --phase 2 --model-index 0  # Single model on GPU
"""
from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path


def _wc():
    """Lazy loader for wandb_config (avoids 'lambda' keyword in dotted import)."""
    return importlib.import_module("classifier.lambda.wandb_config")


def phase0_rebuild_splits():
    """Rebuild expert_train/val with mapping-level dedup."""
    from classifier.scripts.build_expert_training import build_expert_training_set
    print("Phase 0: Rebuilding clean splits (mapping-level dedup)")
    stats = build_expert_training_set(leakage_mode="node")
    print(json.dumps(stats, indent=2))

    train_path = Path("data/splits/expert_train.jsonl")
    val_path = Path("data/splits/expert_val.jsonl")
    train_pairs = set()
    with train_path.open() as f:
        for line in f:
            r = json.loads(line)
            train_pairs.add((r["source_text"], r["target_text"]))
    overlap = 0
    with val_path.open() as f:
        for line in f:
            r = json.loads(line)
            if (r["source_text"], r["target_text"]) in train_pairs:
                overlap += 1
    assert overlap == 0, f"CONTAMINATION: {overlap} overlapping text pairs"
    print(f"  Contamination check: PASSED (0 overlapping pairs)")
    return stats


def phase1_zero_shot_baseline():
    """Zero-shot BGE cosine similarity baseline (free, no training)."""
    import numpy as np
    from transformers import AutoModel, AutoTokenizer
    import torch

    print("Phase 1: Zero-shot BGE cosine baseline")
    model_name = "BAAI/bge-large-en-v1.5"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    test_path = Path("data/splits/human_test_frozen.jsonl")
    pairs = [json.loads(line) for line in test_path.open()]

    TIER_MAP = {"Direct": 3, "Related": 2, "Tangential": 1, "None": 0}
    labels = [TIER_MAP[p["expert_tier"]] for p in pairs]

    def encode(texts):
        enc = tokenizer(texts, max_length=256, truncation=True, padding=True, return_tensors="pt")
        with torch.no_grad():
            out = model(**enc)
        mask = enc["attention_mask"].unsqueeze(-1).float()
        return ((out.last_hidden_state * mask).sum(1) / mask.sum(1)).numpy()

    emb_a = encode([p["source_text"] for p in pairs])
    emb_b = encode([p["target_text"] for p in pairs])

    cosines = np.array([
        np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
        for a, b in zip(emb_a, emb_b)
    ])

    thresholds = [0.3, 0.5, 0.7]
    preds = np.digitize(cosines, thresholds)

    from sklearn.metrics import accuracy_score, f1_score
    acc = accuracy_score(labels, preds)
    macro_f1 = f1_score(labels, preds, average="macro")

    results = {"zero_shot_bge_accuracy": acc, "zero_shot_bge_macro_f1": macro_f1}
    out_path = Path("runs/vfinal/zero_shot_baseline.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"  Accuracy: {acc:.3f}, Macro F1: {macro_f1:.3f}")
    return results


def phase2_sweep(model_index: int, sweep_count: int = 25):
    """Run W&B Bayesian sweep for one model."""
    import wandb
    from classifier.ensemble.cross_encoder_trainer import train_cross_encoder

    wc = _wc()
    models = wc.VFINAL_MODELS
    m = models[model_index]
    name, model_id, group = m["name"], m["model_id"], m["group"]

    print(f"Phase 2: Sweep for {name} ({model_id}), {sweep_count} trials")

    def train_fn():
        run = wandb.init(project=wc.WANDB_PROJECT_VFINAL, entity=wc.WANDB_ENTITY, group=group)
        config = dict(wandb.config)
        wandb.config.update({"ce_model_name": name})

        metrics = train_cross_encoder(
            model_name=model_id,
            train_path="data/splits/expert_train.jsonl",
            val_path="data/splits/expert_val.jsonl",
            output_dir=f"runs/vfinal/ce/{name}/{run.id}",
            contrastive_init=None,
            **{k: v for k, v in config.items()},
        )

        monitoring = wc.VFINAL_MONITORING
        val_f1 = metrics.get("val_macro_f1", 0)
        train_acc = metrics.get("train_acc", 0)
        val_acc = metrics.get("val_acc", 0)

        if val_f1 < monitoring["collapse_guard"]["threshold"]:
            wandb.alert(title="Class Collapse", text=monitoring["collapse_guard"]["alert"])

        gap = train_acc - val_acc
        if gap > monitoring["overfitting_guard"]["threshold"]:
            wandb.alert(title="Overfitting", text=monitoring["overfitting_guard"]["alert"])

        if val_acc >= monitoring["leakage_guard"]["threshold"]:
            wandb.alert(title="Possible Leakage", text=monitoring["leakage_guard"]["alert"])

        wandb.log({"combined_f1": metrics.get("combined_f1", 0)})
        run.finish()

    sweep_id = wandb.sweep(
        sweep=wc.VFINAL_CE_SWEEP_CONFIG,
        project=wc.WANDB_PROJECT_VFINAL,
        entity=wc.WANDB_ENTITY,
    )
    wandb.agent(sweep_id, function=train_fn, count=sweep_count,
                project=wc.WANDB_PROJECT_VFINAL, entity=wc.WANDB_ENTITY)


def phase3_extract_embeddings(model_index: int | None = None):
    """Extract CLS embeddings and logits from best sweep checkpoint."""
    from classifier.ensemble.cross_encoder import CrossEncoderClassifier
    from classifier.ensemble.bi_encoder import BiEncoderClassifier
    import wandb
    import numpy as np
    import torch

    wc = _wc()
    models = wc.VFINAL_MODELS
    indices = [model_index] if model_index is not None else range(len(models))

    for idx in indices:
        m = models[idx]
        name = m["name"]
        print(f"Phase 3: Extracting embeddings for {name}")

        best_dir = Path(f"runs/vfinal/ce/{name}/best")
        if not best_dir.exists():
            api = wandb.Api()
            runs = api.runs(
                f"{wc.WANDB_ENTITY}/{wc.WANDB_PROJECT_VFINAL}",
                filters={"config.ce_model_name": name, "state": "finished"},
            )
            best_run = max(runs, key=lambda r: r.summary.get("combined_f1", 0))
            print(f"  Best run: {best_run.id} (cf1={best_run.summary.get('combined_f1', 0):.3f})")
            best_dir = Path(f"runs/vfinal/ce/{name}/{best_run.id}/best")

        if not best_dir.exists():
            print(f"  WARNING: No checkpoint found for {name}, skipping")
            continue

        is_bi = m.get("type") == "bi_encoder"
        if is_bi:
            model = BiEncoderClassifier.load(best_dir)
        else:
            model = CrossEncoderClassifier.load(best_dir)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device).eval()

        for split_name, split_path in [
            ("train", "data/splits/expert_train.jsonl"),
            ("val", "data/splits/expert_val.jsonl"),
            ("test", "data/splits/human_test_frozen.jsonl"),
            ("cal", "data/splits/human_cal.jsonl"),
        ]:
            rows = [json.loads(l) for l in Path(split_path).open()]
            texts_a = [r["source_text"] for r in rows]
            texts_b = [r["target_text"] for r in rows]

            all_logits = []
            all_cls = []
            with torch.no_grad():
                for i in range(0, len(texts_a), 32):
                    batch_a = texts_a[i:i+32]
                    batch_b = texts_b[i:i+32]
                    tokens = model.tokenize_batch(batch_a, batch_b)
                    tokens = {k: v.to(device) for k, v in tokens.items()}

                    if is_bi:
                        logits, cls_emb = model.forward(
                            tokens["input_ids_a"], tokens["attention_mask_a"],
                            tokens["input_ids_b"], tokens["attention_mask_b"],
                        )
                    else:
                        logits, cls_emb = model.forward(
                            tokens["input_ids"], tokens["attention_mask"]
                        )
                    all_logits.append(logits.cpu().numpy())
                    all_cls.append(cls_emb.cpu().numpy())

            out_path = Path(f"data/features/vfinal_{name}_{split_name}.npz")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez(out_path,
                     logits=np.concatenate(all_logits),
                     cls_emb=np.concatenate(all_cls))
            print(f"  {split_name}: {len(rows)} pairs → {out_path}")


def phase4_stacker_sweep():
    """5-fold CV stacker sweep with Optuna."""
    import logging
    import warnings
    import numpy as np
    from classifier.ensemble.stacker import (
        LGBMStacker,
        tune_stacker,
        train_and_evaluate,
        FEATURE_COLS_VFINAL,
        VFINAL_CE_MODEL_NAMES,
        VFINAL_CE_CLS_SIM_COLS,
    )

    print("Phase 4: Stacker sweep (5-fold CV, 10 Optuna trials)")

    # ------------------------------------------------------------------
    # 1. Load feature npz files
    # ------------------------------------------------------------------
    print("  Loading feature npz files...")
    feat_dir = Path("data/features")
    npz: dict[str, dict[str, np.ndarray]] = {}
    for model in VFINAL_CE_MODEL_NAMES:
        npz[model] = {}
        for split in ("train", "val"):
            path = feat_dir / f"vfinal_{model}_{split}.npz"
            data = np.load(str(path))
            npz[model][split] = {"logits": data["logits"], "cls_emb": data["cls_emb"]}
            n = data["logits"].shape[0]
            print(f"    {model}/{split}: {n} rows, logits={data['logits'].shape}, cls={data['cls_emb'].shape}")

    # ------------------------------------------------------------------
    # 2. Cosine similarity helper
    # ------------------------------------------------------------------
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        norm_a = np.linalg.norm(a, axis=1, keepdims=True)
        norm_b = np.linalg.norm(b, axis=1, keepdims=True)
        norm_a = np.where(norm_a == 0, 1, norm_a)
        norm_b = np.where(norm_b == 0, 1, norm_b)
        return (a * b).sum(axis=1) / (norm_a.squeeze() * norm_b.squeeze())

    # Pairwise combos: (roberta, deberta_base), (roberta, bge), (deberta_base, bge)
    # mapped to VFINAL_CE_CLS_SIM_COLS: ["roberta_cls_sim", "deberta_base_cls_sim", "bge_cls_sim"]
    _cls_pairs = [
        ("roberta", "deberta_base"),
        ("roberta", "bge"),
        ("deberta_base", "bge"),
    ]

    # ------------------------------------------------------------------
    # 3. Load baseline features from JSONL
    # ------------------------------------------------------------------
    print("  Loading baseline features from JSONL splits...")

    def _load_baseline(jsonl_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns (labels, bm25, bridge) arrays."""
        labels, bm25_vals, bridge_vals = [], [], []
        with jsonl_path.open() as fh:
            for line in fh:
                row = json.loads(line)
                labels.append(int(row["tier_label"]))
                bm25_vals.append(float(row.get("score_bm25", 0.0)))
                bridge_vals.append(float(row.get("score_bridge", 0.0)))
        return (
            np.array(labels, dtype=np.int32),
            np.array(bm25_vals, dtype=np.float32),
            np.array(bridge_vals, dtype=np.float32),
        )

    y_train, bm25_train, bridge_train = _load_baseline(Path("data/splits/expert_train.jsonl"))
    y_val, bm25_val, bridge_val = _load_baseline(Path("data/splits/expert_val.jsonl"))
    print(f"    train labels: {len(y_train)}, val labels: {len(y_val)}")

    # ------------------------------------------------------------------
    # 4. Assemble 17-feature matrices
    # ------------------------------------------------------------------
    print("  Assembling 17-feature matrices...")

    def _build_X(split: str, bm25: np.ndarray, bridge: np.ndarray) -> np.ndarray:
        cols = []
        # 12 logit features (3 models × 4 logits)
        for model in VFINAL_CE_MODEL_NAMES:
            cols.append(npz[model][split]["logits"])   # (n, 4)
        # 3 pairwise CLS sim features
        for m_a, m_b in _cls_pairs:
            sim = _cosine_sim(
                npz[m_a][split]["cls_emb"],
                npz[m_b][split]["cls_emb"],
            ).reshape(-1, 1)               # (n, 1)
            cols.append(sim)
        # 2 baseline features
        cols.append(bm25.reshape(-1, 1))
        cols.append(bridge.reshape(-1, 1))
        X = np.hstack(cols)
        assert X.shape[1] == len(FEATURE_COLS_VFINAL), (
            f"Expected {len(FEATURE_COLS_VFINAL)} features, got {X.shape[1]}"
        )
        return X

    X_train = _build_X("train", bm25_train, bridge_train)
    X_val = _build_X("val", bm25_val, bridge_val)
    print(f"    X_train: {X_train.shape}, X_val: {X_val.shape}")

    # ------------------------------------------------------------------
    # 5. Optuna sweep — 10 trials, 5-fold CV on train set
    # ------------------------------------------------------------------
    print("  Running Optuna sweep (10 trials, 5-fold CV)...")
    best_params = tune_stacker(X_train, y_train, n_trials=10, n_splits=5)
    print(f"  Best params: {best_params}")

    # Save best params
    params_dir = Path("runs/vfinal/stacker")
    params_dir.mkdir(parents=True, exist_ok=True)
    params_path = params_dir / "best_params.json"
    params_path.write_text(json.dumps(best_params, indent=2))
    print(f"  Saved best params → {params_path}")

    # Log to wandb if active
    try:
        import wandb
        if wandb.run is not None:
            wandb.log({"stacker/best_params": best_params})
    except ImportError:
        pass

    # ------------------------------------------------------------------
    # 6. Train final stacker on full train set
    # ------------------------------------------------------------------
    print("  Training final stacker on full train set...")
    run_dir = params_dir / "final_run"
    metrics = train_and_evaluate(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        params=best_params,
        run_dir=run_dir,
    )
    stacker: LGBMStacker = metrics.pop("stacker")
    print(f"  val_acc={metrics['val_acc']:.4f}, val_logloss={metrics['val_logloss']:.4f}")

    # ------------------------------------------------------------------
    # 7. Compute macro F1 on val and compare vs best single-model CE
    # ------------------------------------------------------------------
    from sklearn.metrics import f1_score as _f1_score

    # Reload stacker predictions for macro F1
    stacker_preds = stacker.predict(X_val)
    stacker_macro_f1 = float(_f1_score(y_val, stacker_preds, average="macro"))
    print(f"  Stacker val macro_f1={stacker_macro_f1:.4f}")

    # Best single-CE macro F1: find best logit-only model on val
    best_ce_f1 = 0.0
    for model in VFINAL_CE_MODEL_NAMES:
        ce_preds = np.argmax(npz[model]["val"]["logits"], axis=1)
        ce_f1 = float(_f1_score(y_val, ce_preds, average="macro"))
        print(f"    {model} single-model macro_f1={ce_f1:.4f}")
        if ce_f1 > best_ce_f1:
            best_ce_f1 = ce_f1

    improvement_pp = (stacker_macro_f1 - best_ce_f1) * 100
    if improvement_pp < 2.0:
        warnings.warn(
            f"Stacker macro_f1 ({stacker_macro_f1:.4f}) does NOT beat best single CE "
            f"({best_ce_f1:.4f}) by >=2pp; delta={improvement_pp:.2f}pp",
            stacklevel=2,
        )
        logging.getLogger(__name__).warning(
            "Stacker improvement %.2fpp < 2pp threshold (stacker=%.4f, best_ce=%.4f)",
            improvement_pp, stacker_macro_f1, best_ce_f1,
        )
    else:
        print(f"  Stacker beats best CE by {improvement_pp:.2f}pp ✓")

    metrics["val_macro_f1"] = stacker_macro_f1
    metrics["best_ce_macro_f1"] = best_ce_f1
    metrics["improvement_pp"] = improvement_pp

    # Log to wandb if active
    try:
        import wandb
        if wandb.run is not None:
            wandb.log({
                "stacker/val_macro_f1": stacker_macro_f1,
                "stacker/best_ce_macro_f1": best_ce_f1,
                "stacker/improvement_pp": improvement_pp,
            })
    except ImportError:
        pass

    # ------------------------------------------------------------------
    # 8. Save final stacker model
    # ------------------------------------------------------------------
    model_save_path = params_dir / "stacker_final.txt"
    stacker.save(model_save_path)
    print(f"  Saved final stacker model → {model_save_path}")

    print("Phase 4 complete.")
    return metrics


def phase5_conformal():
    """Conformal calibration on human_cal."""
    print("Phase 5: Conformal calibration")
    raise NotImplementedError("Wire up in Task 12")


def phase6_sacred_eval():
    """Sacred evaluation on frozen test."""
    print("Phase 6: Sacred evaluation")
    raise NotImplementedError("Wire up in Task 13")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="v_final training pipeline")
    parser.add_argument("--phase", type=int, help="Run a single phase (0-6)")
    parser.add_argument("--model-index", type=int, help="Model index for phase 2/3")
    parser.add_argument("--sweep-count", type=int, default=25)
    parser.add_argument("--all", action="store_true", help="Run all local phases")
    args = parser.parse_args()

    if args.phase is not None:
        dispatch = {
            0: lambda: phase0_rebuild_splits(),
            1: lambda: phase1_zero_shot_baseline(),
            2: lambda: phase2_sweep(args.model_index or 0, args.sweep_count),
            3: lambda: phase3_extract_embeddings(args.model_index),
            4: lambda: phase4_stacker_sweep(),
            5: lambda: phase5_conformal(),
            6: lambda: phase6_sacred_eval(),
        }
        dispatch[args.phase]()
    elif args.all:
        phase0_rebuild_splits()
        phase1_zero_shot_baseline()
        for i in range(3):
            phase2_sweep(i, args.sweep_count)
            phase3_extract_embeddings(i)
        phase4_stacker_sweep()
        phase5_conformal()
        phase6_sacred_eval()


if __name__ == "__main__":
    main()
