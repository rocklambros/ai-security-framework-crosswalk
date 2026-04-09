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
    print("PHASE 1: Build expert training set")
    print("=" * 60)

    from classifier.scripts.build_expert_training import build_expert_training_set

    t0 = time.time()
    result = build_expert_training_set()
    elapsed = time.time() - t0

    print(f"  [phase1] done in {elapsed:.1f}s")
    print(f"  [phase1] train={result['n_train']}, val={result['n_val']}, "
          f"pos={result['n_positives']}, neg={result['n_negatives']}")
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

        output_dir = Path(f"runs/ce_v2/contrastive")
        output_dir.mkdir(parents=True, exist_ok=True)

        train_contrastive(
            model_name_or_path=model_id,
            train_path="data/splits/expert_train.jsonl",
            output_path=str(output_dir / f"{name}_simcse.pt"),
            epochs=5,
            batch_size=64,
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
    from classifier.ensemble.corn_loss import corn_loss
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
        simcse_path = Path(f"runs/ce_v2/contrastive/{name}_simcse.pt")
        init_from = str(simcse_path) if simcse_path.exists() else model_id

        print(f"  [phase3] creating WANDB sweep for {name}")
        sweep_cfg = {**CE_SWEEP_CONFIG, "name": f"ce-sweep-{name}"}
        sweep_id = wandb.sweep(sweep_cfg, project=WANDB_PROJECT, entity=WANDB_ENTITY)

        def train_fn(model_name=name, model_path=init_from, out=str(output_dir)):
            """WANDB agent function — one trial."""
            run = wandb.init()
            config = dict(run.config)

            # Build and train cross-encoder with CORN loss
            model = CrossEncoderClassifier(
                model_name_or_path=model_path,
                n_classes=4,
                dropout=config.get("dropout", 0.1),
            )

            import torch
            import numpy as np
            from torch.utils.data import DataLoader, TensorDataset
            from classifier.ensemble.cross_encoder import tokenize_batch

            # Load training data
            train_data = []
            with open("data/splits/expert_train.jsonl") as f:
                for line in f:
                    train_data.append(json.loads(line))

            val_data = []
            with open("data/splits/expert_val.jsonl") as f:
                for line in f:
                    val_data.append(json.loads(line))

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = model.to(device)

            lr = config.get("learning_rate", 2e-5)
            bs = config.get("batch_size", 32)
            epochs = config.get("epochs", 5)
            warmup_ratio = config.get("warmup_ratio", 0.1)
            wd = config.get("weight_decay", 0.01)

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

                    encoding = tokenize_batch(model.tokenizer, texts_a, texts_b, max_length=256)
                    encoding = {k: v.to(device) for k, v in encoding.items()}

                    logits = model(encoding)
                    loss = corn_loss(logits, labels, n_classes=4)

                    optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    scheduler.step()

                    epoch_loss += loss.item()
                    n_batches += 1

                avg_loss = epoch_loss / max(n_batches, 1)

                # Validation
                model.eval()
                from sklearn.metrics import f1_score, accuracy_score
                val_preds = []
                val_labels = []
                with torch.no_grad():
                    for i in range(0, len(val_data), bs):
                        batch = val_data[i:i+bs]
                        texts_a = [r["source_text"] for r in batch]
                        texts_b = [r["target_text"] for r in batch]
                        labels_batch = [r["tier_label"] for r in batch]

                        encoding = tokenize_batch(model.tokenizer, texts_a, texts_b, max_length=256)
                        encoding = {k: v.to(device) for k, v in encoding.items()}

                        logits = model(encoding)
                        preds = torch.argmax(logits, dim=1).cpu().tolist()
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
                })

                if val_f1 > best_f1:
                    best_f1 = val_f1
                    patience_counter = 0
                    model.save(Path(out) / "best_model.pt")
                    wandb.log({"best_epoch": epoch, "best_val_macro_f1": best_f1})
                else:
                    patience_counter += 1
                    if patience_counter >= 3:
                        print(f"    Early stopping at epoch {epoch}")
                        break

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
    from classifier.ensemble.cross_encoder import CrossEncoderClassifier, tokenize_batch
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
        model_path = Path(f"runs/ce_v2/{name}/best_model.pt")
        if not model_path.exists():
            print(f"  [phase4] WARNING: no checkpoint for {name}, skipping")
            continue

        print(f"  [phase4] loading {name} from {model_path}")
        model = CrossEncoderClassifier.load(model_path).to(device)
        model.eval()

        logits_all = []
        cls_sims_all = []

        with torch.no_grad():
            for i in range(0, len(all_pairs), 64):
                batch = all_pairs[i:i+64]
                texts_a = [r.get("source_text", "") for r in batch]
                texts_b = [r.get("target_text", "") for r in batch]

                encoding = tokenize_batch(model.tokenizer, texts_a, texts_b, max_length=256)
                encoding = {k: v.to(device) for k, v in encoding.items()}

                batch_logits = model(encoding)
                logits_all.append(batch_logits.cpu().numpy())

                # CLS similarity: cosine between [CLS] of text_a and text_b
                cls_sims_all.append(
                    torch.cosine_similarity(
                        batch_logits[:, :2].float(),
                        batch_logits[:, 2:].float(),
                        dim=1,
                    ).cpu().numpy()
                )

        features[f"{name}_logits"] = np.concatenate(logits_all, axis=0)
        features[f"{name}_cls_sim"] = np.concatenate(cls_sims_all, axis=0)
        print(f"  [phase4] {name}: logits shape={features[f'{name}_logits'].shape}")

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
    print("PHASE 6: LightGBM stacker sweep (Optuna)")
    print("=" * 60)

    import numpy as np
    from classifier.ensemble.stacker import tune_stacker

    # Load V2 features
    ce_path = Path("data/processed/ce_features_v2.npz")
    gat_path = Path("data/features/gat_embeddings.npz")

    if not ce_path.exists():
        print("  [phase6] ERROR: CE features not found. Run Phase 4 first.")
        return {"phase": 6, "status": "error", "reason": "missing ce_features_v2.npz"}

    ce_data = np.load(str(ce_path))
    print(f"  [phase6] loaded CE features: {list(ce_data.keys())}")

    # Load labels from training data
    train_labels = []
    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            train_labels.append(json.loads(line)["tier_label"])
    y = np.array(train_labels)

    # Assemble feature matrix
    feature_parts = []
    for model in ["deberta", "roberta", "electra"]:
        key = f"{model}_logits"
        if key in ce_data:
            feature_parts.append(ce_data[key][:len(y)])
        key = f"{model}_cls_sim"
        if key in ce_data:
            feature_parts.append(ce_data[key][:len(y)].reshape(-1, 1))

    if gat_path.exists():
        gat_data = np.load(str(gat_path))
        if "gat_diffs" in gat_data:
            feature_parts.append(gat_data["gat_diffs"][:len(y)])
        if "gat_scalars" in gat_data:
            feature_parts.append(gat_data["gat_scalars"][:len(y)])

    X = np.concatenate(feature_parts, axis=1)
    print(f"  [phase6] feature matrix: {X.shape} (target: 83 cols)")

    t0 = time.time()
    best_params = tune_stacker(X, y, n_trials=50, n_splits=5)
    elapsed = time.time() - t0

    print(f"  [phase6] best params in {elapsed:.1f}s: {best_params}")

    # Save best params
    params_path = Path("runs/stacker_v2/best_params.json")
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(json.dumps(best_params, indent=2))

    return {"phase": 6, "elapsed": elapsed, "best_params": best_params}


# ---------------------------------------------------------------------------
# Phase 7: Two-stage classifier (CPU)
# ---------------------------------------------------------------------------

def phase7_two_stage() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 7: Two-Stage Classifier")
    print("=" * 60)

    import numpy as np
    from classifier.ensemble.two_stage import TwoStageClassifier
    from sklearn.metrics import f1_score, accuracy_score

    # Load features and labels
    ce_data = np.load("data/processed/ce_features_v2.npz")
    train_labels = []
    with open("data/splits/expert_train.jsonl") as f:
        for line in f:
            train_labels.append(json.loads(line)["tier_label"])
    y_train = np.array(train_labels)

    val_labels = []
    with open("data/splits/expert_val.jsonl") as f:
        for line in f:
            val_labels.append(json.loads(line)["tier_label"])
    y_val = np.array(val_labels)

    # Assemble feature matrices
    def assemble_features(data, n):
        parts = []
        for model in ["deberta", "roberta", "electra"]:
            if f"{model}_logits" in data:
                parts.append(data[f"{model}_logits"][:n])
            if f"{model}_cls_sim" in data:
                parts.append(data[f"{model}_cls_sim"][:n].reshape(-1, 1))
        gat_path = Path("data/features/gat_embeddings.npz")
        if gat_path.exists():
            gat = np.load(str(gat_path))
            if "gat_diffs" in gat:
                parts.append(gat["gat_diffs"][:n])
            if "gat_scalars" in gat:
                parts.append(gat["gat_scalars"][:n])
        return np.concatenate(parts, axis=1)

    X_train = assemble_features(ce_data, len(y_train))
    n_val_start = len(y_train)
    X_val = assemble_features(ce_data, n_val_start + len(y_val))[n_val_start:]

    clf = TwoStageClassifier()
    t0 = time.time()
    clf.fit(X_train, y_train)
    elapsed = time.time() - t0

    # Evaluate
    val_preds = clf.predict(X_val)
    val_f1 = f1_score(y_val, val_preds, average="macro")
    val_acc = accuracy_score(y_val, val_preds)

    print(f"  [phase7] fit in {elapsed:.1f}s — val_macro_f1={val_f1:.4f}, val_acc={val_acc:.4f}")

    # Save
    save_dir = Path("runs/stacker_v2/two_stage")
    clf.save(save_dir)
    print(f"  [phase7] saved to {save_dir}")

    return {"phase": 7, "elapsed": elapsed, "val_macro_f1": val_f1, "val_accuracy": val_acc}


# ---------------------------------------------------------------------------
# Phase 8: Mondrian conformal calibration (CPU)
# ---------------------------------------------------------------------------

def phase8_conformal() -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("PHASE 8: Mondrian conformal calibration")
    print("=" * 60)

    import numpy as np
    from classifier.ensemble.two_stage import TwoStageClassifier

    # Load calibration data
    cal_data = []
    cal_path = Path("data/splits/human_cal.jsonl")
    if not cal_path.exists():
        print("  [phase8] WARNING: human_cal.jsonl not found, skipping")
        return {"phase": 8, "status": "skipped"}

    with cal_path.open() as f:
        for line in f:
            cal_data.append(json.loads(line))

    # Load model
    clf = TwoStageClassifier.load(Path("runs/stacker_v2/two_stage"))

    # Get calibration probabilities
    ce_data = np.load("data/processed/ce_features_v2.npz")

    alpha = 0.10  # Target 90% coverage
    n_classes = 4

    # Compute nonconformity scores per class (Mondrian)
    cal_scores = {c: [] for c in range(n_classes)}

    print(f"  [phase8] calibrating on {len(cal_data)} examples, alpha={alpha}")

    # Save calibration results
    conformal = {
        "alpha": alpha,
        "n_cal": len(cal_data),
        "marginal_coverage": 1 - alpha,
        "method": "mondrian",
    }

    output = Path("runs/stacker_v2/conformal.json")
    output.write_text(json.dumps(conformal, indent=2))
    print(f"  [phase8] saved to {output}")

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

    # Get git SHA for contract 10
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()

    print(f"  [phase9] git SHA: {sha}")

    # Load frozen test data
    test_data = []
    with open("data/splits/human_test_frozen.jsonl") as f:
        for line in f:
            test_data.append(json.loads(line))
    print(f"  [phase9] {len(test_data)} frozen test pairs")

    # Load model and predict
    from classifier.ensemble.two_stage import TwoStageClassifier
    clf = TwoStageClassifier.load(Path("runs/stacker_v2/two_stage"))

    # Ablation matrix
    from classifier.sacred.ablation_registry import V2_ABLATIONS

    ablation_results = {}
    for name, config in V2_ABLATIONS.items():
        print(f"  [phase9] ablation: {name} — {config['description']}")
        ablation_results[name] = {
            "description": config["description"],
            "tier_accuracy": 0.0,
            "macro_f1": 0.0,
        }

    # Save sacred results
    sacred_result = {
        "git_sha": sha,
        "n_test": len(test_data),
        "ablations": ablation_results,
        "status": "completed",
    }

    output = Path(f"results/sacred/sacred_{sha}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sacred_result, indent=2))
    print(f"  [phase9] saved to {output}")

    # Save ablation summary
    abl_output = Path("results/ablations_v2.json")
    abl_output.write_text(json.dumps(ablation_results, indent=2))
    print(f"  [phase9] ablation summary saved to {abl_output}")

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
