"""v8 training orchestrator — 10-phase pipeline with OpenCRE integration.

Phase 0: OpenCRE data extraction + v7c diagnosis (CPU)
Phase 1: v8 training data assembly (CPU, uses v7c for inference)
Phase 2: Contrastive pre-training (GPU)
Phase 3: Cross-encoder fine-tuning sweeps (GPU + W&B)
Phase 4: Extract CLS embeddings (GPU)
Phase 5: GATv2 retrain (GPU)
Phase 6: Stacker sweep with gap penalty feature (CPU)
Phase 7: Final stacker training (CPU)
Phase 8: Conformal calibration (CPU)
Phase 9: Sacred evaluation on frozen test (CPU)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


def phase0_opencre_extraction() -> dict[str, Any]:
    """Extract OpenCRE pairs and diagnose v7c."""
    print("\n" + "=" * 60)
    print("PHASE 0: OpenCRE data extraction + v7c diagnosis")
    print("=" * 60)

    t0 = time.time()

    from classifier.data.opencre_loader import run_extraction
    pairs_path = run_extraction(use_cache=True)

    try:
        from classifier.scripts.diagnose_v7c import main as diagnose
        diagnose()
        diagnosis = {"status": "complete"}
    except Exception as e:
        print(f"  v7c diagnosis skipped: {e}")
        diagnosis = {"skipped": str(e)}

    elapsed = time.time() - t0
    print(f"  [phase0] done in {elapsed:.1f}s")
    return {"phase": 0, "elapsed": elapsed, "diagnosis": diagnosis}


def phase1_assemble_v8_data() -> dict[str, Any]:
    """Assemble v8 training data via disagreement mining."""
    print("\n" + "=" * 60)
    print("PHASE 1: v8 training data assembly (disagreement mining)")
    print("=" * 60)

    t0 = time.time()
    from classifier.scripts.build_v8_training import assemble_v8_training
    report = assemble_v8_training()
    elapsed = time.time() - t0
    print(f"  [phase1] done in {elapsed:.1f}s")
    return {"phase": 1, "elapsed": elapsed, **report}


def phase2_contrastive() -> dict[str, Any]:
    """Contrastive pre-training on v8 data."""
    print("\n" + "=" * 60)
    print("PHASE 2: Contrastive pre-training (SimCSE)")
    print("=" * 60)

    import importlib
    from classifier.ensemble.contrastive_pretrain import train_contrastive
    _wc = importlib.import_module("classifier.lambda.wandb_config")
    CROSS_ENCODER_MODELS = _wc.CROSS_ENCODER_MODELS

    t0 = time.time()
    results = []
    for model_cfg in CROSS_ENCODER_MODELS:
        name = model_cfg["name"]
        model_id = model_cfg["model_id"]
        print(f"  [phase2] {name} ({model_id})")
        out_dir = Path(f"runs/v8/contrastive/{name}")
        out_dir.mkdir(parents=True, exist_ok=True)
        train_contrastive(
            model_name=model_id,
            train_path="data/splits/v8_train.jsonl",
            output_dir=str(out_dir),
            epochs=5,
            batch_size=32,
        )
        results.append({"model": name})

    elapsed = time.time() - t0
    print(f"  [phase2] done in {elapsed:.1f}s")
    return {"phase": 2, "elapsed": elapsed, "models": results}


def phase3_cross_encoder_sweeps(sweep_count: int = 50) -> dict[str, Any]:
    """Cross-encoder fine-tuning sweeps with v8 augmented data."""
    print("\n" + "=" * 60)
    print(f"PHASE 3: Cross-encoder sweeps ({sweep_count} trials/model)")
    print("=" * 60)

    import importlib
    import wandb
    _wc = importlib.import_module("classifier.lambda.wandb_config")

    t0 = time.time()
    results = []

    for model_cfg in _wc.CROSS_ENCODER_MODELS:
        name = model_cfg["name"]
        model_id = model_cfg["model_id"]
        print(f"\n  [phase3] Sweeping {name}...")

        sweep_id = wandb.sweep(
            _wc.V8_CE_SWEEP_CONFIG,
            project=_wc.WANDB_PROJECT_V8,
            entity=_wc.WANDB_ENTITY,
        )

        def train_fn():
            run = wandb.init()
            config = wandb.config

            from classifier.ensemble.cross_encoder_trainer import train_cross_encoder
            metrics = train_cross_encoder(
                model_name=model_id,
                train_path="data/splits/v8_train.jsonl",
                val_path="data/splits/expert_val.jsonl",
                output_dir=f"runs/v8/ce/{name}/{run.id}",
                contrastive_init=f"runs/v8/contrastive/{name}",
                **{k: v for k, v in config.items() if k != "opencre_weight"},
            )

            monitoring = _wc.V8_MONITORING
            val_f1 = metrics.get("val_macro_f1", 0)
            train_acc = metrics.get("train_acc", 0)
            val_acc = metrics.get("val_acc", 0)

            if val_f1 < monitoring["collapse_guard"]["threshold"]:
                wandb.alert(
                    title="Class Collapse Detected",
                    text=monitoring["collapse_guard"]["alert"],
                )

            gap = train_acc - val_acc
            if gap > monitoring["overfitting_guard"]["threshold"]:
                wandb.alert(
                    title="Overfitting Detected",
                    text=monitoring["overfitting_guard"]["alert"],
                )

            if val_acc >= monitoring["leakage_guard"]["threshold"]:
                wandb.alert(
                    title="Possible Leakage",
                    text=monitoring["leakage_guard"]["alert"],
                )

            wandb.log({"combined_f1": val_f1})
            run.finish()

        wandb.agent(sweep_id, function=train_fn, count=sweep_count)
        results.append({"model": name, "sweep_id": sweep_id})

    elapsed = time.time() - t0
    print(f"  [phase3] done in {elapsed:.1f}s")
    return {"phase": 3, "elapsed": elapsed, "results": results}


def phase4_extract_embeddings() -> dict[str, Any]:
    """Extract CLS embeddings from best cross-encoder checkpoints."""
    print("\n" + "=" * 60)
    print("PHASE 4: Extract CLS embeddings")
    print("=" * 60)

    t0 = time.time()
    import importlib
    _wc = importlib.import_module("classifier.lambda.wandb_config")

    from classifier.features.cls_extractor import extract_cls_features

    for model_cfg in _wc.CROSS_ENCODER_MODELS:
        name = model_cfg["name"]
        best_dir = Path(f"runs/v8/ce/{name}/best")
        if not best_dir.exists():
            import wandb
            api = wandb.Api()
            runs = api.runs(f"{_wc.WANDB_ENTITY or ''}/{_wc.WANDB_PROJECT_V8}",
                           filters={"config.model_name": name})
            best_run = max(runs, key=lambda r: r.summary.get("combined_f1", 0), default=None)
            if best_run:
                best_dir = Path(f"runs/v8/ce/{name}/{best_run.id}")

        if best_dir.exists():
            print(f"  [phase4] Extracting {name} from {best_dir}")
            extract_cls_features(
                model_dir=str(best_dir),
                output_path=f"data/processed/ce_features_v8_{name}.npz",
            )

    elapsed = time.time() - t0
    print(f"  [phase4] done in {elapsed:.1f}s")
    return {"phase": 4, "elapsed": elapsed}


def phase5_gat_retrain() -> dict[str, Any]:
    """Retrain GATv2 with v8 graph data."""
    print("\n" + "=" * 60)
    print("PHASE 5: GATv2 retrain")
    print("=" * 60)

    t0 = time.time()
    from classifier.features.gat_trainer import train_gat
    metrics = train_gat(
        output_dir="runs/v8/gat",
        embeddings_output="data/features/gat_embeddings_v8.npz",
    )
    elapsed = time.time() - t0
    print(f"  [phase5] done in {elapsed:.1f}s")
    return {"phase": 5, "elapsed": elapsed, **metrics}


def phase6_stacker_sweep() -> dict[str, Any]:
    """Stacker hyperparameter sweep with gap penalty feature."""
    print("\n" + "=" * 60)
    print("PHASE 6: Stacker sweep (with gap penalty)")
    print("=" * 60)

    import importlib
    import wandb
    _wc = importlib.import_module("classifier.lambda.wandb_config")

    from classifier.ensemble.stacker import LGBMStacker, FEATURE_COLS_V3
    from classifier.features.gap_penalty import compute_gap_penalties

    t0 = time.time()

    import numpy as np
    from classifier.scripts.build_v8_training import load_jsonl

    train_data = load_jsonl(Path("data/splits/v8_train.jsonl"))
    gap_penalties = compute_gap_penalties(train_data)

    ce_features = np.load("data/processed/ce_features_v8_deberta.npz")["features"]
    gat_features = np.load("data/features/gat_embeddings_v8.npz")["pair_features"]
    import pandas as pd
    baseline_df = pd.read_parquet("data/features/baseline_features.parquet")

    X = np.column_stack([
        ce_features,
        gat_features,
        baseline_df[["score_bm25", "score_bridge"]].values,
        gap_penalties.reshape(-1, 1),
    ])

    y = np.array([r.get("tier_label", 0) for r in train_data])
    weights = np.array([r.get("sample_weight", 1.0) for r in train_data])

    wandb.init(project=_wc.WANDB_PROJECT_V8, name="v8-stacker-sweep", job_type="sweep")

    from classifier.ensemble.stacker import tune_stacker
    best_params = tune_stacker(X, y, sample_weight=weights, n_trials=30)
    wandb.log({"best_params": best_params})
    wandb.finish()

    params_path = Path("runs/v8/stacker/best_params.json")
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(json.dumps(best_params, indent=2))

    elapsed = time.time() - t0
    print(f"  [phase6] done in {elapsed:.1f}s")
    return {"phase": 6, "elapsed": elapsed, "best_params": best_params}


def phase7_final_stacker() -> dict[str, Any]:
    """Train final v8 stacker with best hyperparameters."""
    print("\n" + "=" * 60)
    print("PHASE 7: Final stacker training")
    print("=" * 60)

    t0 = time.time()
    params_path = Path("runs/v8/stacker/best_params.json")
    params = json.loads(params_path.read_text()) if params_path.exists() else {}

    import numpy as np
    from classifier.ensemble.stacker import LGBMStacker

    stacker = LGBMStacker(params=params, version="v3")

    X_train = np.load("runs/v8/stacker/X_train.npy")
    y_train = np.load("runs/v8/stacker/y_train.npy")
    w_train = np.load("runs/v8/stacker/w_train.npy")

    stacker.fit(X_train, y_train, sample_weight=w_train)

    out_dir = Path("runs/v8/stacker/final")
    out_dir.mkdir(parents=True, exist_ok=True)
    stacker.save(out_dir / "model.txt")

    X_val = np.load("runs/v8/stacker/X_val.npy")
    y_val = np.load("runs/v8/stacker/y_val.npy")
    y_pred_val = stacker.predict(X_val)

    from sklearn.metrics import accuracy_score, f1_score
    val_acc = float(accuracy_score(y_val, y_pred_val))
    val_f1 = float(f1_score(y_val, y_pred_val, average="macro", zero_division=0))
    train_pred = stacker.predict(X_train)
    train_acc = float(accuracy_score(y_train, train_pred))

    elapsed = time.time() - t0
    print(f"  [phase7] done in {elapsed:.1f}s")
    print(f"  [phase7] train_acc={train_acc:.4f}, val_acc={val_acc:.4f}, val_f1={val_f1:.4f}")
    return {"phase": 7, "elapsed": elapsed, "train_acc": train_acc, "val_acc": val_acc, "val_f1": val_f1}


def phase8_conformal() -> dict[str, Any]:
    """Marginal conformal calibration."""
    print("\n" + "=" * 60)
    print("PHASE 8: Conformal calibration")
    print("=" * 60)

    t0 = time.time()
    from classifier.calibration.conformal import calibrate_conformal

    pre_reg = json.loads(Path("classifier/sacred/pre_registered.json").read_text())
    alpha = pre_reg["conformal"]["alpha"]

    result = calibrate_conformal(
        model_dir="runs/v8/stacker/final",
        cal_path="data/splits/human_cal.jsonl",
        alpha=alpha,
        output_dir="runs/v8/conformal",
    )

    elapsed = time.time() - t0
    print(f"  [phase8] done in {elapsed:.1f}s")
    return {"phase": 8, "elapsed": elapsed, **result}


def phase9_sacred_eval() -> dict[str, Any]:
    """Sacred evaluation on frozen test."""
    print("\n" + "=" * 60)
    print("PHASE 9: Sacred evaluation (frozen test)")
    print("=" * 60)

    t0 = time.time()
    from classifier.sacred.v8_sacred_run import run_v8_sacred

    result = run_v8_sacred()

    elapsed = time.time() - t0
    print(f"  [phase9] done in {elapsed:.1f}s")
    return {"phase": 9, "elapsed": elapsed, **result}


PHASE_MAP = {
    0: phase0_opencre_extraction,
    1: phase1_assemble_v8_data,
    2: phase2_contrastive,
    3: phase3_cross_encoder_sweeps,
    4: phase4_extract_embeddings,
    5: phase5_gat_retrain,
    6: phase6_stacker_sweep,
    7: phase7_final_stacker,
    8: phase8_conformal,
    9: phase9_sacred_eval,
}


def main():
    parser = argparse.ArgumentParser(description="v8 training orchestrator")
    parser.add_argument("--phase", type=int, help="Run specific phase (0-9)")
    parser.add_argument("--sweep-count", type=int, default=50, help="CE sweep trials per model")
    parser.add_argument("--all", action="store_true", help="Run all phases")
    args = parser.parse_args()

    if args.phase is not None:
        fn = PHASE_MAP.get(args.phase)
        if fn is None:
            print(f"Unknown phase {args.phase}. Valid: {list(PHASE_MAP.keys())}")
            sys.exit(1)
        if args.phase == 3:
            result = fn(sweep_count=args.sweep_count)
        else:
            result = fn()
        print(json.dumps(result, indent=2, default=str))
    elif args.all:
        results = []
        for phase_num in sorted(PHASE_MAP.keys()):
            fn = PHASE_MAP[phase_num]
            if phase_num == 3:
                result = fn(sweep_count=args.sweep_count)
            else:
                result = fn()
            results.append(result)
        Path("runs/v8/pipeline_results.json").parent.mkdir(parents=True, exist_ok=True)
        Path("runs/v8/pipeline_results.json").write_text(json.dumps(results, indent=2, default=str))
        print("\n" + "=" * 60)
        print("  v8 PIPELINE COMPLETE")
        print("=" * 60)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
