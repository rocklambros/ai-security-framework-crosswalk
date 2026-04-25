"""Build Section 6: Uncertainty, Ordinal Regression, and the Pivot."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# --- Section header ---
nb["cells"].append(make_md("""## 6 · Uncertainty quantification and ordinal structure

Two problems with the v7c baseline go beyond the Equivalent blind spot. First, the classifier produces a point prediction with no uncertainty estimate. A compliance workflow needs to know when the model is guessing. Second, the four tiers are ordered---an Unrelated-to-Equivalent error is worse than a Related-to-Equivalent error---but the logistic regression treats all misclassifications equally."""))

# --- Analytical approaches narrative (from cell 90) ---
nb["cells"].append(make_md("""### Three directions worth investigating

Three changes would most likely improve the classifier:

1. **More Equivalent training data.** The expert training set contains only a handful of Equivalent pairs. Any external source of high-similarity control pairs could help.
2. **Ordinal regression instead of flat 4-class classification.** The logistic regression ignores the ordering of tiers. An ordinal loss that penalizes distant errors more heavily than adjacent ones could improve calibration.
3. **Conformal prediction for uncertainty.** Wrapping point predictions in prediction sets would give downstream consumers a calibrated measure of confidence.

The ordinal regression demonstrator below addresses direction 2. The OpenCRE discovery in the next section addresses direction 1. v_final combines both."""))

# --- Ordinal regression demonstrator ---
nb["cells"].append(make_md("""### Ordinal regression demonstrator

The four tiers (Unrelated < Partial < Related < Equivalent) form a natural ladder. An ordinal model estimates cumulative thresholds: P(tier >= k) for each cutpoint. This proof-of-concept uses `statsmodels.OrderedModel` on the calibration split to show what ordinal structure looks like in practice."""))

nb["cells"].append(make_md("""> **Plain English:** Instead of treating the four tiers as disconnected buckets, this model says "tier 0 is most likely, and as the feature score increases, the probability mass slides rightward toward tier 3." The S-curves below visualize that slide."""))

# Copy the statsmodels code cells (old cells 99, 100)
nb["cells"].extend(copy_old_cells(old, [99, 100]))

nb["cells"].append(make_md("""The ordinal fit converges and the cumulative-probability plot shows a clean monotone sweep from mostly-Unrelated on the left to mostly-Equivalent on the right. This confirms that the ordinal structure in the data is real and exploitable. The v_final pipeline will use three ordinal loss functions that build on this principle.

> **Plain English:** The proof-of-concept works. When trained to respect the tier ordering, the model produces probability curves that slide smoothly from "definitely unrelated" to "probably equivalent" as the input feature increases. This motivated the ordinal losses used in the final pipeline."""))

# Renumber figures: old Figure 9.2 -> Figure 6.1
for cell in nb["cells"][-6:]:
    src = "".join(cell["source"])
    src = src.replace("Figure 9.2", "Figure 6.1")
    src = src.replace("fig9_2", "fig6_1")
    cell["source"] = [l + "\n" for l in src.split("\n")[:-1]] + [src.split("\n")[-1]]

save_notebook(nb)
