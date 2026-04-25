"""Build Section 13 (Conclusion) + Appendices A and B."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# ========================================
# SECTION 13: Conclusion
# ========================================

nb["cells"].append(make_md("""## 13 · Conclusion

This project traced a complete arc from a baseline classifier that could not identify equivalent controls to an ensemble that broke through on the hardest class.

The v7c pipeline scored 81.0% exact accuracy and 0.512 macro F1 on a frozen 179-pair holdout. Those headline numbers masked a structural failure: Equivalent-class F1 was 0.000. The classifier never predicted that two controls from different frameworks meant the same thing.

OpenCRE provided the external ground truth the training set lacked. Its 13,519 pairs with hop-distance labels mapped naturally onto our four ordinal tiers. Disagreement mining (v8) added 673 pairs where v7c disagreed with OpenCRE labels. Direct augmentation (v8b) added 2,046 pairs and caused DeBERTa-large to collapse to single-class prediction while the LightGBM stacker overfit to train accuracy of 1.000 against validation accuracy of 0.528.

v_final responded to each failure with a specific architectural change. Mapping-level deduplication removed 56% of text-pair contamination from the validation split. Ordinal losses (KL-divergence, CORN, focal) replaced standard cross-entropy. Softmax averaging across three models replaced the learnable stacker. The result: macro F1 rose to 0.558 (+4.6 pp), Equivalent F1 reached 0.400 (from 0.000), conformal coverage exceeded 90% on all four classes, and the ensemble scored all 4,001 edges in the crosswalk graph.

The trained ensemble is available at [huggingface.co/rockCO78/ai-security-crosswalk-vfinal](https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal) for anyone to use or extend."""))

nb["cells"].append(make_md("""> **Plain English:** I started with a model that scored 81% overall but 0% on the class that matters most. After discovering OpenCRE, I tried two ways to use its data---one worked partially, one caused the model to collapse. The third attempt stripped the architecture down to a simple average of three models with ordinal-aware losses and got Equivalent right for the first time. The model, the code, and the data are all public."""))

nb["cells"].append(make_md("""---

**Project 2 transition.** The Dash application (Project 2) surfaces these 4,001 scored edges interactively, with click-through from high-level framework heatmaps down to individual control pairs and their predicted tiers."""))

# ========================================
# APPENDIX A: Pipeline History
# ========================================

# Copy old cells 103-113 (Appendix A) — 11 cells
appendix_a_cells = copy_old_cells(old, list(range(103, 114)))

# Update the section header to say "Appendix A" consistently
first_src = "".join(appendix_a_cells[0]["source"])
if "## Appendix A" not in first_src:
    first_src = first_src.replace("## A", "## Appendix A")
appendix_a_cells[0]["source"] = [l + "\n" for l in first_src.split("\n")[:-1]] + [first_src.split("\n")[-1]]

nb["cells"].extend(appendix_a_cells)

# ========================================
# APPENDIX B: Style Guide
# ========================================

# Copy old cell 5 (style guide) as Appendix B
style_cell = copy_old_cells(old, [5])[0]
style_src = "".join(style_cell["source"])
# Replace header
style_src = style_src.replace("## Style guide", "## Appendix B: Style guide")
style_cell["source"] = [l + "\n" for l in style_src.split("\n")[:-1]] + [style_src.split("\n")[-1]]
nb["cells"].append(style_cell)

save_notebook(nb)
