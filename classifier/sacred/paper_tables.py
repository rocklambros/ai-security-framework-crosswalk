"""Generate paper tables from sacred run and ablation results.

Produces table1 (main results), table3 (ablations) in both Markdown and LaTeX.
Tables 2 (per-pair) and 4 (fresh-75) are deferred until those data sources exist.
"""
from __future__ import annotations

import json
from pathlib import Path


def _md_row(cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _md_table(header, rows):
    sep = "|" + "|".join("---" for _ in header) + "|"
    return "\n".join([_md_row(header), sep, *[_md_row(r) for r in rows]]) + "\n"


def _tex_table(header, rows, caption):
    cols = "l" + "r" * (len(header) - 1)
    body = " \\\\\n".join(" & ".join(str(c) for c in r) for r in rows)
    return (
        "\\begin{table}[t]\n\\centering\n"
        f"\\caption{{{caption}}}\n"
        f"\\begin{{tabular}}{{{cols}}}\n\\toprule\n"
        + " & ".join(header) + " \\\\\n\\midrule\n"
        + body + " \\\\\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def _write(out_dir: Path, name: str, md: str, tex: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.md").write_text(md)
    (out_dir / f"{name}.tex").write_text(tex)


def generate_table1(sacred_results: dict, out_dir: Path) -> None:
    """Table 1: Main sacred-run results on human_test_frozen."""
    header = ["Metric", "Value"]
    rows = [
        ["N pairs", str(sacred_results["n_pairs"])],
        ["Tier accuracy", f"{sacred_results['tier_accuracy']:.4f}"],
        ["Macro F1", f"{sacred_results['macro_f1']:.4f}"],
    ]
    ci = sacred_results.get("bootstrap_ci_95", {})
    if ci:
        rows.append(["95% CI", f"[{ci['lower']:.4f}, {ci['upper']:.4f}]"])

    per_class = sacred_results.get("per_class", {})
    for cls_name, cls_data in per_class.items():
        rows.append([f"  {cls_name} ({cls_data['count']})", f"{cls_data['accuracy']:.4f}"])

    conf = sacred_results.get("conformal", {})
    if conf:
        rows.append(["Conformal avg set size", f"{conf['avg_set_size']:.2f}"])
        rows.append(["Conformal coverage", f"{conf['marginal_coverage']:.4f}"])

    router = sacred_results.get("router", {})
    if router:
        rows.append(["Router abstained", f"{router['n_abstained']}/{router['n_abstained'] + router['n_passed']}"])
        rows.append(["Precision on passed", f"{router['precision_on_passed']:.4f}"])

    _write(out_dir, "table1",
           _md_table(header, rows),
           _tex_table(header, rows, "Sacred run results on human\\_test\\_frozen"))


def generate_table3(ablation_results: dict, out_dir: Path) -> None:
    """Table 3: Ablation matrix on llm_val."""
    header = ["Ablation", "Features", "Tier Acc", "Macro F1", "Δ Acc"]
    full_acc = ablation_results.get("full", {}).get("tier_accuracy", 0)

    rows = []
    for name in sorted(ablation_results.keys()):
        m = ablation_results[name]
        if m.get("skip"):
            continue
        delta = m["tier_accuracy"] - full_acc
        rows.append([
            name,
            str(m["n_features"]),
            f"{m['tier_accuracy']:.4f}",
            f"{m['macro_f1']:.4f}",
            f"{delta:+.4f}",
        ])

    _write(out_dir, "table3",
           _md_table(header, rows),
           _tex_table(header, rows, "Ablation matrix on llm\\_val"))


def generate_tables(sacred_path: Path, ablations_path: Path, out_dir: Path) -> dict:
    """Generate all available tables from sacred run and ablation results."""
    paths = {}

    if sacred_path.exists():
        sacred = json.loads(sacred_path.read_text())
        generate_table1(sacred, out_dir)
        paths["table1"] = out_dir / "table1.md"

    if ablations_path.exists():
        ablations = json.loads(ablations_path.read_text())
        generate_table3(ablations, out_dir)
        paths["table3"] = out_dir / "table3.md"

    return paths


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sacred", default="results/sacred/")
    ap.add_argument("--ablations", default="results/ablations.json")
    ap.add_argument("--out", default="paper/tables")
    args = ap.parse_args()

    sacred_dir = Path(args.sacred)
    sacred_files = sorted(sacred_dir.glob("sacred_*.json"))
    sacred_path = sacred_files[-1] if sacred_files else Path("nonexistent")

    generate_tables(sacred_path, Path(args.ablations), Path(args.out))
    print(f"Tables written to {args.out}")
