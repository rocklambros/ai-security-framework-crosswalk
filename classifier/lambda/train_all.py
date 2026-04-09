"""Lambda H100 training orchestrator — 9-phase pipeline for crosswalk-v2."""
from __future__ import annotations

import argparse
import sys
import time
from typing import Any


# ---------------------------------------------------------------------------
# Phase 1: Build expert training set
# ---------------------------------------------------------------------------

def phase1_build_data() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 1: Build expert training set")
    print("=" * 60)

    from classifier.labeling.build_training_set import build_expert_training_set  # type: ignore

    t0 = time.time()
    result = build_expert_training_set()
    elapsed = time.time() - t0

    print(f"  [phase1] done in {elapsed:.1f}s — {result}")
    return {"phase": 1, "elapsed": elapsed, "result": result}


# ---------------------------------------------------------------------------
# Phase 2: Contrastive pre-training (3 models)
# ---------------------------------------------------------------------------

def phase2_contrastive() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 2: Contrastive pre-training")
    print("=" * 60)

    from classifier.sacred.contrastive import train_contrastive  # type: ignore
    from classifier.lambda_.wandb_config import CROSS_ENCODER_MODELS  # type: ignore

    results = []
    for model_cfg in CROSS_ENCODER_MODELS:
        print(f"  [phase2] contrastive training: {model_cfg['name']} ({model_cfg['model_id']})")
        t0 = time.time()
        res = train_contrastive(model_id=model_cfg["model_id"], group=model_cfg["group"])
        elapsed = time.time() - t0
        print(f"  [phase2] {model_cfg['name']} done in {elapsed:.1f}s")
        results.append({"model": model_cfg["name"], "elapsed": elapsed, "result": res})

    return {"phase": 2, "models": results}


# ---------------------------------------------------------------------------
# Phase 3: Cross-encoder fine-tuning sweeps (WANDB)
# ---------------------------------------------------------------------------

def phase3_finetune_sweeps(sweep_count: int = 30) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print(f"PHASE 3: Cross-encoder fine-tuning sweeps (count={sweep_count})")
    print("=" * 60)

    import wandb  # type: ignore
    from classifier.lambda_.wandb_config import (  # type: ignore
        CE_SWEEP_CONFIG,
        CROSS_ENCODER_MODELS,
        WANDB_ENTITY,
        WANDB_PROJECT,
    )
    from classifier.sacred.finetune import run_ce_finetune  # type: ignore

    sweep_ids = []
    for model_cfg in CROSS_ENCODER_MODELS:
        print(f"  [phase3] creating sweep for {model_cfg['name']}")
        sweep_cfg = dict(CE_SWEEP_CONFIG)
        sweep_cfg["name"] = f"ce-sweep-{model_cfg['name']}"
        sweep_id = wandb.sweep(
            sweep_cfg,
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
        )
        print(f"  [phase3] sweep_id={sweep_id} — launching {sweep_count} agents")
        wandb.agent(
            sweep_id,
            function=lambda: run_ce_finetune(model_id=model_cfg["model_id"]),
            count=sweep_count,
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
        )
        sweep_ids.append({"model": model_cfg["name"], "sweep_id": sweep_id})

    return {"phase": 3, "sweeps": sweep_ids}


# ---------------------------------------------------------------------------
# Phase 4: Extract CLS embeddings from trained CEs
# ---------------------------------------------------------------------------

def phase4_extract_features() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 4: Extract CLS embeddings from trained cross-encoders")
    print("=" * 60)

    from classifier.sacred.feature_extraction import extract_cls_embeddings  # type: ignore
    from classifier.lambda_.wandb_config import CROSS_ENCODER_MODELS  # type: ignore

    artifacts = []
    for model_cfg in CROSS_ENCODER_MODELS:
        print(f"  [phase4] extracting CLS embeddings: {model_cfg['name']}")
        t0 = time.time()
        artifact_path = extract_cls_embeddings(
            model_name=model_cfg["name"],
            model_id=model_cfg["model_id"],
        )
        elapsed = time.time() - t0
        print(f"  [phase4] {model_cfg['name']} saved to {artifact_path} ({elapsed:.1f}s)")
        artifacts.append({"model": model_cfg["name"], "path": artifact_path, "elapsed": elapsed})

    return {"phase": 4, "artifacts": artifacts}


# ---------------------------------------------------------------------------
# Phase 5: GATv2 retrain (Lambda GPU required)
# ---------------------------------------------------------------------------

def phase5_gat_retrain() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 5: GATv2 retrain (placeholder — Lambda A100/H100 required)")
    print("=" * 60)

    # NOTE: Full GATv2 retrain requires Lambda GPU with sufficient VRAM.
    # This phase is a placeholder; actual training is triggered via the
    # Lambda cloud job scheduler once the GAT retrain unblock is resolved
    # (see project_plan5_lambda_block.md).

    print("  [phase5] WARNING: GAT retrain blocked pending Lambda A100 availability")
    print("  [phase5] Skipping GATv2 retrain — using cached GAT embeddings if available")

    try:
        from classifier.baselines.gat import load_cached_gat_embeddings  # type: ignore

        embeddings = load_cached_gat_embeddings()
        print(f"  [phase5] loaded cached GAT embeddings: shape={embeddings.shape}")
        return {"phase": 5, "status": "cached", "shape": list(embeddings.shape)}
    except Exception as exc:
        print(f"  [phase5] no cached embeddings available: {exc}")
        return {"phase": 5, "status": "skipped", "reason": str(exc)}


# ---------------------------------------------------------------------------
# Phase 6: Stacker sweep (Optuna + WANDB)
# ---------------------------------------------------------------------------

def phase6_stacker_sweep() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 6: Stacker sweep (Optuna + WANDB)")
    print("=" * 60)

    import optuna  # type: ignore
    import wandb  # type: ignore
    from classifier.lambda_.wandb_config import (  # type: ignore
        STACKER_SWEEP_CONFIG,
        WANDB_ENTITY,
        WANDB_PROJECT,
    )
    from classifier.sacred.stacker import objective_stacker  # type: ignore

    print("  [phase6] initialising Optuna study (direction=maximize, metric=oof_macro_f1)")
    study = optuna.create_study(
        direction="maximize",
        study_name="stacker-sweep",
        sampler=optuna.samplers.TPESampler(seed=42),
    )

    sweep_id = wandb.sweep(
        STACKER_SWEEP_CONFIG,
        project=WANDB_PROJECT,
        entity=WANDB_ENTITY,
    )
    print(f"  [phase6] WANDB sweep_id={sweep_id}")

    n_trials = 100
    print(f"  [phase6] running {n_trials} Optuna trials")
    study.optimize(objective_stacker, n_trials=n_trials, show_progress_bar=True)

    best = study.best_params
    print(f"  [phase6] best oof_macro_f1={study.best_value:.4f} params={best}")
    return {"phase": 6, "best_value": study.best_value, "best_params": best, "sweep_id": sweep_id}


# ---------------------------------------------------------------------------
# Phase 7: Fit TwoStageClassifier
# ---------------------------------------------------------------------------

def phase7_two_stage() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 7: Fit TwoStageClassifier")
    print("=" * 60)

    from classifier.sacred.two_stage import TwoStageClassifier, fit_two_stage  # type: ignore

    print("  [phase7] fitting TwoStageClassifier with best stacker params from phase 6")
    t0 = time.time()
    model, metrics = fit_two_stage()
    elapsed = time.time() - t0

    print(f"  [phase7] done in {elapsed:.1f}s — metrics={metrics}")
    return {"phase": 7, "elapsed": elapsed, "metrics": metrics}


# ---------------------------------------------------------------------------
# Phase 8: Mondrian conformal calibration
# ---------------------------------------------------------------------------

def phase8_conformal() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 8: Mondrian conformal calibration")
    print("=" * 60)

    from classifier.sacred.conformal import run_mondrian_calibration  # type: ignore

    print("  [phase8] running Mondrian conformal calibration on calibration split")
    t0 = time.time()
    cal_result = run_mondrian_calibration()
    elapsed = time.time() - t0

    coverage = cal_result.get("coverage", None)
    efficiency = cal_result.get("efficiency", None)
    print(f"  [phase8] done in {elapsed:.1f}s — coverage={coverage}, efficiency={efficiency}")
    return {"phase": 8, "elapsed": elapsed, "calibration": cal_result}


# ---------------------------------------------------------------------------
# Phase 9: Final evaluation on frozen test set
# ---------------------------------------------------------------------------

def phase9_sacred_run() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 9: Final evaluation on frozen test set (sacred run)")
    print("=" * 60)

    from classifier.sacred.evaluate import run_sacred_evaluation  # type: ignore

    print("  [phase9] running final evaluation on frozen holdout — NO TUNING AFTER THIS")
    t0 = time.time()
    eval_result = run_sacred_evaluation()
    elapsed = time.time() - t0

    macro_f1 = eval_result.get("macro_f1", None)
    mrr = eval_result.get("mrr", None)
    tier_acc = eval_result.get("tier_acc", None)
    print(f"  [phase9] FINAL RESULTS — macro_f1={macro_f1}, mrr={mrr}, tier_acc={tier_acc}")
    print(f"  [phase9] sacred run completed in {elapsed:.1f}s")
    return {"phase": 9, "elapsed": elapsed, "eval": eval_result}


# ---------------------------------------------------------------------------
# Phase registry
# ---------------------------------------------------------------------------

PHASES: dict[int, Any] = {
    1: phase1_build_data,
    2: phase2_contrastive,
    3: phase3_finetune_sweeps,
    4: phase4_extract_features,
    5: phase5_gat_retrain,
    6: phase6_stacker_sweep,
    7: phase7_two_stage,
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
    7: "two_stage",
    8: "conformal",
    9: "sacred_run",
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="train_all",
        description="Lambda H100 training orchestrator — crosswalk-v2 (9-phase pipeline)",
    )
    parser.add_argument(
        "--phase",
        type=int,
        default=None,
        choices=list(PHASES.keys()),
        metavar="N",
        help="Run a single phase (1-9). Omit to run all phases sequentially.",
    )
    parser.add_argument(
        "--sweep-count",
        type=int,
        default=30,
        dest="sweep_count",
        help="Number of WANDB sweep agents for phase 3 (default: 30).",
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
    print("  crosswalk-v2  |  Lambda H100 training orchestrator")
    print("#" * 60)

    if args.phase is not None:
        name = PHASE_NAMES[args.phase]
        print(f"\nRunning single phase: {args.phase} ({name})")
        result = run_phase(args.phase, args.sweep_count)
        print(f"\nPhase {args.phase} result: {result}")
        return

    # Run all phases sequentially
    print("\nRunning all 9 phases sequentially")
    pipeline_start = time.time()
    results: list[dict[str, Any]] = []

    for phase_num in sorted(PHASES.keys()):
        try:
            result = run_phase(phase_num, args.sweep_count)
            results.append(result)
        except Exception as exc:
            print(f"\n[ERROR] Phase {phase_num} ({PHASE_NAMES[phase_num]}) failed: {exc}", file=sys.stderr)
            raise

    total_elapsed = time.time() - pipeline_start
    print("\n" + "#" * 60)
    print(f"  All 9 phases complete in {total_elapsed:.1f}s")
    print("#" * 60)


if __name__ == "__main__":
    main()
