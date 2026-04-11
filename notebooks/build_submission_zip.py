# notebooks/build_submission_zip.py
"""Build the COMP 4433 Project 1 submission zip."""
import shutil
from pathlib import Path

def build_zip():
    staging = Path("/tmp/project1_submission")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    # Copy notebook
    shutil.copy("notebooks/project1_crosswalk_eda.ipynb", staging / "project1_crosswalk_eda.ipynb")

    # Copy data/processed files the notebook loads via jload() and cload()
    data_dir = staging / "data" / "processed"
    data_dir.mkdir(parents=True)
    for name in [
        "nodes.json", "edges.json", "graph_stats.json",
        "training_data.csv", "nist_validation_data.csv",
        "bridge_comparison.csv", "weight_comparison.json",
        "learned_weights.json", "finetune_benchmark.json",
        "node2vec_projection.csv", "v1_vs_v2_comparison.json",
    ]:
        src = Path("data/processed") / name
        if src.exists():
            shutil.copy(src, data_dir / name)

    # Copy v6 results
    v6_dir = data_dir / "v6_results"
    v6_dir.mkdir(parents=True)
    for name in ["v6_all_results.json", "v6_pair_predictions.jsonl"]:
        src = Path("data/processed/v6_results") / name
        if src.exists():
            shutil.copy(src, v6_dir / name)

    # Copy Opus scores (needed for Figure 7.4)
    v5_dir = data_dir / "v5_features"
    v5_dir.mkdir(parents=True)
    opus = Path("data/processed/v5_features/opus_scores_human_test_frozen.jsonl")
    if opus.exists():
        shutil.copy(opus, v5_dir / opus.name)

    # Copy results (sacred)
    results_dir = staging / "results"
    results_sacred = results_dir / "sacred"
    results_sacred.mkdir(parents=True)
    for f in Path("results/sacred").glob("sacred_*.json"):
        shutil.copy(f, results_sacred / f.name)

    # Create zip
    output = Path("notebooks/project1_lambros")
    shutil.make_archive(str(output), "zip", str(staging))
    print(f"Created {output}.zip ({(output.with_suffix('.zip')).stat().st_size / 1024:.0f} KB)")

if __name__ == "__main__":
    build_zip()
