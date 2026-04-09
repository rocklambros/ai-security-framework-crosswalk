"""Tests for paper table generator."""
import json
from pathlib import Path
from classifier.sacred.paper_tables import generate_tables


def _sacred_results():
    return {
        "sacred_run": True,
        "n_pairs": 400,
        "tier_accuracy": 0.81,
        "macro_f1": 0.79,
        "bootstrap_ci_95": {"point": 0.81, "lower": 0.77, "upper": 0.85},
        "per_class": {
            "unrelated": {"accuracy": 0.75, "count": 50},
            "partial": {"accuracy": 0.60, "count": 50},
            "related": {"accuracy": 0.90, "count": 200},
            "equivalent": {"accuracy": 0.70, "count": 100},
        },
        "conformal": {"avg_set_size": 1.5, "marginal_coverage": 0.92},
        "router": {"n_abstained": 40, "n_passed": 360, "precision_on_passed": 0.85},
    }


def _ablation_results():
    return {
        "full": {"description": "Full", "n_features": 38, "tier_accuracy": 0.81, "macro_f1": 0.79, "per_class": {}},
        "no_gat": {"description": "No GAT", "n_features": 3, "tier_accuracy": 0.78, "macro_f1": 0.76, "per_class": {}},
        "lexical_only": {"description": "BM25 only", "n_features": 1, "tier_accuracy": 0.62, "macro_f1": 0.58, "per_class": {}},
    }


def test_generate_tables(tmp_path):
    sacred_path = tmp_path / "sacred.json"
    sacred_path.write_text(json.dumps(_sacred_results()))
    ablations_path = tmp_path / "ablations.json"
    ablations_path.write_text(json.dumps(_ablation_results()))
    out_dir = tmp_path / "paper" / "tables"

    paths = generate_tables(sacred_path, ablations_path, out_dir)
    assert (out_dir / "table1.md").exists()
    assert (out_dir / "table1.tex").exists()
    assert (out_dir / "table3.md").exists()
    assert (out_dir / "table3.tex").exists()

    t1 = (out_dir / "table1.md").read_text()
    assert "0.81" in t1
    assert "400" in t1

    t3 = (out_dir / "table3.md").read_text()
    assert "full" in t3
    assert "no_gat" in t3


def test_generate_tables_missing_files(tmp_path):
    paths = generate_tables(
        tmp_path / "no_sacred.json",
        tmp_path / "no_ablations.json",
        tmp_path / "out",
    )
    assert paths == {}
