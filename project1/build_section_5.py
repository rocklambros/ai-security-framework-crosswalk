"""Build Section 5: The v7c baseline and its failure.

Appends ~15 cells to the notebook. Section 5 frames v7c as "the baseline that
failed" — its EQUIVALENT F1=0.000 blind spot motivates everything that follows.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_notebook import (
    make_md,
    make_code,
    load_notebook,
    save_notebook,
    load_old_notebook,
    copy_old_cells,
)


def fig_rename(src: str) -> str:
    """Apply all figure number renames for Section 5."""
    replacements = [
        # Longer strings first to avoid partial matches
        ("Figure 6.1", "Figure 5.2"),
        ("fig6_1",     "fig5_2"),
        ("Figure 6.2", "Figure 5.3"),
        ("fig6_2",     "fig5_3"),
        ("Figure 8.1", "Figure 5.4"),
        ("fig8_1",     "fig5_4"),
        ("Figure 8.3", "Figure 5.5"),
        ("fig8_3",     "fig5_5"),
    ]
    for old, new in replacements:
        src = src.replace(old, new)
    return src


def fix_repo(src: str) -> str:
    """Ensure savefig uses REPO_ROOT, not bare REPO."""
    return src.replace('REPO / "report"', 'REPO_ROOT / "report"')


def add_savefig(src: str, figname: str) -> str:
    """Insert a plt.savefig call before plt.show() if not already present."""
    if "savefig" in src:
        return src
    savefig_line = (
        f'plt.savefig(REPO_ROOT / "report" / "figures" / "{figname}.png",'
        f' dpi=150, bbox_inches="tight")'
    )
    return src.replace("plt.show()", savefig_line + "\nplt.show()")


def copy_and_patch(old_nb, idx: int, figname: str = None) -> dict:
    """Copy one old cell, apply fig renames, fix REPO, and optionally add savefig."""
    cells = copy_old_cells(old_nb, [idx])
    cell = cells[0]
    src_lines = cell["source"]
    src = "".join(src_lines)
    src = fig_rename(src)
    src = fix_repo(src)
    if figname:
        src = add_savefig(src, figname)
    # Re-encode as notebook source lines
    lines = src.split("\n")
    cell["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
    return cell


def build():
    nb = load_notebook()
    old_nb = load_old_notebook()
    new_cells = []

    # ── Cell 1: Section header ──────────────────────────────────────────────
    new_cells.append(make_md(
        "## 5 · The v7c baseline and its failure\n"
        "\n"
        "Before introducing data augmentation or a new architecture, I need to "
        "establish what the original v7c pipeline actually does — and where it "
        "breaks down.\n"
        "\n"
        "v7c is a two-stage classifier. Stage one encodes each control as a "
        "node embedding using a graph attention network (GAT) trained on the "
        "crosswalk graph; stage two feeds 50 hand-engineered features into a "
        "logistic regression with L2 regularization (C=0.01). The 50 features "
        "come from three families: 35 GAT geometry features (cosine similarity, "
        "L2 distance, dot product, and 32 element-wise embedding diffs), "
        "3 baseline text-and-graph features (BGE cosine, BM25, two-hop bridge "
        "score), and 12 cross-encoder soft probabilities from DeBERTa-v3-large, "
        "RoBERTa-large, and DeBERTa-v3-base.\n"
        "\n"
        "On the frozen test set of 179 pairs the pipeline reaches **81.0% "
        "exact-match accuracy** and **0.512 macro F1**. Those numbers look "
        "reasonable until you look at the per-class breakdown: the Equivalent "
        "class achieves **F1 = 0.000**. The classifier never predicts Equivalent "
        "— not once across 179 test pairs. The 81% headline hides a total blind "
        "spot on the class that matters most for framework alignment."
    ))

    # ── Cell 2: Feature family definitions (old cell 36) ───────────────────
    new_cells.append(copy_and_patch(old_nb, 36))

    # ── Cell 3: Feature violins Figure 5.1 (old cell 37) ───────────────────
    # Cell 37 already references "Figure 5.1" — no rename needed, just add savefig
    cell37 = copy_and_patch(old_nb, 37, figname="fig5_1_feature_violins")
    new_cells.append(cell37)

    # ── Cell 4: Feature violin interpretation ──────────────────────────────
    new_cells.append(make_md(
        "Figure 5.1 uses the v6 legacy feature set (LLM votes, Opus scores, "
        "structural cosines) rather than the v7c cross-encoder features, "
        "because v7c replaced LLM and Opus with CE soft probabilities. "
        "Even on the legacy features the pattern is clear: `llm_final_score` "
        "separates Equivalent from the other tiers, but the Equivalent violin "
        "is narrow — only 7 test pairs. That small sample is the first sign of "
        "trouble. The GAT cosine panel shows partial overlap across all four "
        "tiers, which means geometry alone cannot resolve close cases."
    ))

    # ── Cell 5: Feature importance narrative (old cell 47) ─────────────────
    new_cells.append(copy_and_patch(old_nb, 47))

    # ── Cell 6: Feature importance chart Figure 5.2 (old cell 48) ──────────
    # Rename Figure 6.1 → Figure 5.2, fig6_1 → fig5_2
    new_cells.append(copy_and_patch(old_nb, 48, figname="fig5_2_feature_importance"))

    # ── Cell 7: Feature importance interpretation ───────────────────────────
    new_cells.append(make_md(
        "The CE features dominate: the top-ranked feature is a DeBERTa-v3-large "
        "soft probability, and CE features collectively account for most of the "
        "cumulative importance. The 80% threshold (dashed orange line) is reached "
        "in roughly the top 10 features. That concentration tells me the 35 GAT "
        "geometry features are largely redundant — the cross-encoders have already "
        "compressed the semantic signal. This will matter when I redesign the "
        "architecture in Section 9."
    ))

    # ── Cell 8: Method comparison Figure 5.3 (old cell 51) ─────────────────
    # Rename Figure 6.2 → Figure 5.3, fig6_2 → fig5_3
    new_cells.append(copy_and_patch(old_nb, 51, figname="fig5_3_method_comparison"))

    # ── Cell 9: Method comparison interpretation ────────────────────────────
    new_cells.append(make_md(
        "Figure 5.3 shows that Method B (full 50-feature pipeline) outperforms "
        "the ablations, but the gap between B and C (CE-only) is small — about "
        "two percentage points. Method A (GAT-only) drops sharply. This confirms "
        "the importance ranking: CE features carry the load, GAT features add a "
        "small margin, and the three baseline features contribute noise as much "
        "as signal."
    ))

    # ── Cell 10: Frozen test results header ─────────────────────────────────
    new_cells.append(make_md(
        "### Frozen test results\n"
        "\n"
        "The numbers below come from the single locked evaluation run. "
        "I set aside the test split before any hyperparameter search and "
        "never touched it again until the final sacred evaluation. "
        "Everything that follows in the notebook is measured against this "
        "same frozen set."
    ))

    # ── Cell 11: Sacred summary print (old cell 71) ─────────────────────────
    new_cells.append(copy_and_patch(old_nb, 71))

    # ── Cell 12: Confusion matrix Figure 5.4 (old cell 72) ─────────────────
    # Rename Figure 8.1 → Figure 5.4, fig8_1 → fig5_4
    new_cells.append(copy_and_patch(old_nb, 72, figname="fig5_4_confusion_matrix"))

    # ── Cell 13: Confusion matrix interpretation ────────────────────────────
    new_cells.append(make_md(
        "The Equivalent row in Figure 5.4A is all zeros. All 7 Equivalent test "
        "pairs are misclassified — 6 as Related, 1 as Partial. The per-class "
        "accuracy panel (5.4B) makes this explicit: Equivalent accuracy is 0%, "
        "F1 = 0.00. The dominant off-diagonal error visible in the heatmap "
        "annotation is the one the model gets most wrong, but the Equivalent "
        "failure is categorically different — it is not a boundary confusion, "
        "it is an invisible class."
    ))

    # ── Cell 14: Headline accuracy Figure 5.5 (old cell 83) ─────────────────
    # Rename Figure 8.3 → Figure 5.5, fig8_3 → fig5_5
    new_cells.append(copy_and_patch(old_nb, 83, figname="fig5_5_headline_accuracy"))

    # ── Cell 15: The pivot ───────────────────────────────────────────────────
    new_cells.append(make_md(
        "### The pivot\n"
        "\n"
        "The 81% headline accuracy in Figure 5.5 looks competitive against the "
        "majority-class baseline, but it is built almost entirely on 172 "
        "non-Equivalent pairs. The 7 Equivalent pairs in the test set are "
        "invisible to the model — it has never seen enough of them to learn "
        "what they look like.\n"
        "\n"
        "This is data starvation, not model weakness. The training set contains "
        "fewer than 30 Equivalent pairs across all splits. No amount of "
        "regularization tuning or feature engineering will fix a class with "
        "that few examples. I need more labeled Equivalent pairs.\n"
        "\n"
        "This sent me looking for external sources of high-similarity control "
        "pairs. Where could I find more labeled data for the Equivalent class?"
    ))

    # Append all new cells to notebook
    nb["cells"].extend(new_cells)
    save_notebook(nb)
    print(f"Section 5 added: {len(new_cells)} new cells")


if __name__ == "__main__":
    build()
