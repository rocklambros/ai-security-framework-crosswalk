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

    # Copy data files the notebook needs
    data_dir = staging / "data" / "upstream"
    data_dir.mkdir(parents=True)
    shutil.copy("data/upstream/mappings_v1.jsonl", data_dir / "mappings_v1.jsonl")

    # Copy results (sacred + ablations)
    results_dir = staging / "results"
    results_sacred = results_dir / "sacred"
    results_sacred.mkdir(parents=True)

    for f in Path("results/sacred").glob("sacred_*.json"):
        shutil.copy(f, results_sacred / f.name)

    ablation = Path("results/ablations_v2.json")
    if ablation.exists():
        shutil.copy(ablation, results_dir / "ablations_v2.json")

    # Create zip
    output = Path("notebooks/project1_lambros")
    shutil.make_archive(str(output), "zip", str(staging))
    print(f"Created {output}.zip ({(output.with_suffix('.zip')).stat().st_size / 1024:.0f} KB)")

if __name__ == "__main__":
    build_zip()
