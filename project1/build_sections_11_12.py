"""Build Sections 11-12: v_final Results + Deployment + HuggingFace."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# ========================================
# SECTION 11: v_final Results
# ========================================

nb["cells"].append(make_md("""## 11 · v_final results: the complete picture

This section evaluates v_final on the same 179-pair frozen test set used for v7c. Every metric below uses identical data and methodology so the comparison is direct."""))

# --- Copy old cells 137-143 (results loading, confusion matrix, per-class F1,
#     model progression, bootstrap CI, conformal) ---
nb["cells"].extend(copy_old_cells(old, [137, 138, 139, 140, 141, 142, 143]))

# --- Interpretation narrative ---
nb["cells"].append(make_md("""### Results interpretation

Macro F1 rises from 0.512 to 0.558 (+4.6 percentage points), driven almost entirely by the Equivalent class: F1 goes from 0.000 to 0.400. The classifier now correctly identifies 4 of the 7 Equivalent test pairs.

The improvement comes with a trade-off. Related-class F1 drops from 0.556 to 0.378. The confusion matrix shows why: 6 of 24 Related test pairs are now predicted Equivalent. The ordinal losses shifted the decision boundary upward, catching more Equivalents but relabeling some Related pairs in the process. On a 4-class ordinal scale with 24 Related test examples, this is an expected side effect.

Exact accuracy dips slightly (81.0% to 79.9%) because the model now occasionally predicts Equivalent when it previously would have predicted Unrelated. Macro F1 is the better metric here because it weighs each class equally rather than letting the Unrelated majority dominate.

The bootstrap confidence intervals (10,000 resamples, 95% CI) show macro F1 between 0.436 and 0.661, with the v7c point estimate of 0.512 inside this range. On 179 test pairs, we cannot claim statistical significance at the 0.05 level. The improvement is directionally consistent but a larger test set would be needed for definitive separation.

Conformal prediction coverage exceeds 90% on all four classes, meeting the calibration target. The median prediction set contains 1 tier (a crisp prediction)."""))

nb["cells"].append(make_md("""> **Plain English:** The retrained model gets the hardest class (Equivalent) right for the first time---4 out of 7 test pairs. The price is that it sometimes confuses Related pairs for Equivalent, which makes sense because those two tiers are adjacent on the scale. The confidence intervals are wide because the test set is small, so I cannot definitively say this version is better by traditional statistics. But the qualitative change---from 0% to 57% recall on the class that matters most---is the real result."""))

# --- NEW code cell: Figure 11.6 Adjacent-error direction bar chart ---
nb["cells"].append(make_code("""# Figure 11.6 — Adjacent-error direction analysis.
# Of all misclassifications, how many are off by 1 tier vs 2+ tiers,
# and which direction? Bar chart (Cleveland & McGill 1984).
vfinal = json.loads((REPO_ROOT / "runs" / "vfinal" / "sacred" / "results.json").read_text())
cm = vfinal["confusion_matrix"]  # 4x4 nested list

adjacent_up = 0    # predicted tier is 1 above true tier
adjacent_down = 0  # predicted tier is 1 below true tier
distant = 0        # predicted tier is 2+ away from true tier
correct = 0

for true_idx in range(4):
    for pred_idx in range(4):
        count = cm[true_idx][pred_idx]
        if true_idx == pred_idx:
            correct += count
        elif abs(true_idx - pred_idx) == 1:
            if pred_idx > true_idx:
                adjacent_up += count
            else:
                adjacent_down += count
        else:
            distant += count

categories = ["Correct", "Adjacent up\\n(+1 tier)", "Adjacent down\\n(-1 tier)", "Distant\\n(2+ tiers)"]
counts = [correct, adjacent_up, adjacent_down, distant]
colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"]

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(categories, counts, color=colors, edgecolor="white", linewidth=0.8)

for bar, count in zip(bars, counts):
    total = sum(counts)
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
            f"{count} ({count/total*100:.0f}%)", ha="center", va="bottom", fontsize=9)

# Annotation
ax.annotate(
    f"{(correct + adjacent_up + adjacent_down)/(correct + adjacent_up + adjacent_down + distant)*100:.0f}%"
    " of predictions are\\ncorrect or off by 1 tier",
    xy=(0.5, correct * 0.6), xytext=(2.3, correct * 0.7),
    fontsize=9, color="black",
    arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
)

ax.set_ylabel("Number of test pairs")
ax.set_title("Most errors are adjacent: the ordinal losses keep predictions close", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig11_6_adjacent_errors.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""The ordinal losses work as designed. When the model is wrong, it is usually wrong by one tier rather than two or three. This is exactly the behavior ordinal losses incentivize: distant misclassifications are penalized more heavily than adjacent ones."""))

# ========================================
# SECTION 12: Deployment + Impact + HuggingFace
# ========================================

nb["cells"].append(make_md("""## 12 · Full-graph deployment and model availability

With a trained classifier in hand, I scored every edge in the crosswalk graph. The v_final ensemble assigned ordinal tiers to all 4,001 cross-framework edges."""))

# --- Copy old cells 147-148 (full graph predictions + coverage gain) ---
nb["cells"].extend(copy_old_cells(old, [147, 148]))

nb["cells"].append(make_md("""The classifier identifies 416 edges at Partial or above, including 59 predicted Equivalent. These are concrete candidates for compliance crosswalk mappings that organizations can review and validate.

> **Plain English:** The model scored every connection in the crosswalk and flagged 416 as potentially meaningful (not just noise). Of those, 59 pairs are predicted to be equivalent---the same control expressed in different standards. A compliance team can start with those 59 and expand outward."""))

# --- HuggingFace narrative cells ---
nb["cells"].append(make_md("""### Model availability

The trained v_final ensemble is available at [huggingface.co/rockCO78/ai-security-crosswalk-vfinal](https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal). The repository contains:

- **Three encoder checkpoints:** RoBERTa-large (1.4 GB), DeBERTa-v3-base (704 MB), BGE-large-v1.5 (1.3 GB), each with its classification head
- **Inference script:** `scripts/predict_edges.py` loads all three models, runs a forward pass on each, averages the softmax vectors, and writes predictions
- **AIBOM-compliant model card:** Full documentation of architecture, training data, metrics, limitations, environmental impact, and usage instructions

To run inference on a new pair of controls, clone the repository, load the three encoders and their heads, tokenize the pair as `[CLS] source_text [SEP] target_text [SEP]`, compute the softmax average, and take the argmax."""))

nb["cells"].append(make_md("""### Extending the crosswalk to new frameworks

To add a 10th framework to the crosswalk:

1. **Prepare node data.** Add the new framework's controls to `data/processed/nodes.json` with fields: `node_id`, `framework`, `name`, `description`, `entry_type`.
2. **Generate candidate pairs.** Create cross-framework pairs between the new framework and each existing framework.
3. **Score with the ensemble.** Run `scripts/predict_edges.py` on the candidate pairs to get ordinal tier predictions.
4. **Review high-confidence predictions.** Have domain experts validate a sample of the Equivalent and Related predictions.
5. **Fine-tune (optional).** If expert labels are available for the new framework, fine-tune the ensemble using the same ordinal loss functions on the expanded training set."""))

# Renumber figures in copied cells
fig_map = {
    "Figure 13.1": "Figure 11.1",
    "Figure 13.2": "Figure 11.2",
    "Figure 13.3": "Figure 11.3",
    "Figure 13.4": "Figure 11.4",
    "Figure 13.5": "Figure 11.5",
    "Figure 14.1": "Figure 12.1",
    "Figure 14.2": "Figure 12.2",
    "fig13_1": "fig11_1",
    "fig13_2": "fig11_2",
    "fig13_3": "fig11_3",
    "fig13_4": "fig11_4",
    "fig13_5": "fig11_5",
    "fig14_1": "fig12_1",
    "fig14_2": "fig12_2",
}

section_start_idx = None
for i, c in enumerate(nb["cells"]):
    src = "".join(c["source"])
    if "## 11" in src and "v_final" in src.lower():
        section_start_idx = i
        break

if section_start_idx:
    for cell in nb["cells"][section_start_idx:]:
        src = "".join(cell["source"])
        for old_ref, new_ref in fig_map.items():
            src = src.replace(old_ref, new_ref)
        cell["source"] = [l + "\n" for l in src.split("\n")[:-1]] + [src.split("\n")[-1]]

save_notebook(nb)
