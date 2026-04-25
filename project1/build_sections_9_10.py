"""Build Sections 9-10: v8b Collapse Crisis + v_final Architecture.

Section 9 is the "anomalies" discussion COMP 4433 requires.
Section 10 presents the architectural response.
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

nb = load_notebook()
old = load_old_notebook()

# ========================================
# SECTION 9: v8b Collapse Crisis
# ========================================

nb["cells"].append(make_md("""## 9 · The v8b collapse crisis

v8b took a broader approach than v8's targeted disagreement mining. Instead of selecting only disagreements, v8b added 2,046 OpenCRE pairs directly to training with per-class caps: 997 Unrelated, 690 Partial, 683 Equivalent, and 673 Related. This brought the total training set to 14,222 pairs.

The results were a disaster on two fronts."""))

# --- v8b data assembly stats ---
nb["cells"].append(make_code("""# 9.1 — v8b data assembly and collapse diagnostics
v8b_assembly = json.loads(
    (REPO_ROOT / "runs" / "v8b_diagnosis" / "v8b_data_assembly.json").read_text()
)
print("v8b Data Assembly")
print(f"  Expert train:         {v8b_assembly['expert_train_original']:,}")
print(f"  OpenCRE added:        {v8b_assembly['v8_rows_added']:,}")
print(f"  Skipped by cap:       {v8b_assembly['skipped_by_cap']:,}")
print(f"  v8b train total:      {v8b_assembly['v8_train_total']:,}")
print(f"  Class caps:           {v8b_assembly['class_caps']}")
print(f"\\nLabel distribution:")
for tier, count in sorted(v8b_assembly["label_distribution"].items()):
    print(f"    {tier}: {count:,}")"""))

nb["cells"].append(make_md("""### Failure 1: DeBERTa-large model collapse

DeBERTa-v3-large collapsed during training. By epoch 4, every sweep configuration produced 100% single-class predictions---the model predicted the same tier for every pair regardless of input. The collapse guard triggered but the model never recovered."""))

# --- NEW code cell: Figure 9.1 v8b collapse diagnostics from WandB ---
nb["cells"].append(make_code("""# Figure 9.1 — v8b model collapse diagnostics from WandB runs.
# Bar chart showing the fraction of runs that collapsed to
# single-class prediction (n_unique_preds == 1).
# Position on common scale for comparison (Cleveland & McGill 1984).

wandb_v8b = json.loads(
    (REPO_ROOT / "runs" / "v8b_diagnosis" / "wandb_runs.json").read_text()
)

# Count collapsed vs non-collapsed runs
total_runs = len(wandb_v8b)
collapsed = sum(1 for r in wandb_v8b if r.get("n_unique_preds") == 1)
partial_collapse = sum(1 for r in wandb_v8b
                       if r.get("n_unique_preds") is not None
                       and 1 < r["n_unique_preds"] < 4)
healthy = sum(1 for r in wandb_v8b if r.get("n_unique_preds") == 4)

categories = ["Collapsed\\n(1 class)", "Partial collapse\\n(2-3 classes)", "Healthy\\n(4 classes)"]
counts = [collapsed, partial_collapse, healthy]
colors = ["#e74c3c", "#f39c12", "#2ecc71"]

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(categories, counts, color=colors, edgecolor="white", linewidth=0.8)

for bar, count in zip(bars, counts):
    pct = count / total_runs * 100 if total_runs > 0 else 0
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{count} ({pct:.0f}%)", ha="center", va="bottom", fontsize=10, fontweight="bold")

# Annotation (Graze & Schwabish 2024: on-plot annotation)
ax.annotate(
    f"{collapsed} of {total_runs} runs predicted\\na single class for every pair",
    xy=(0, collapsed), xytext=(1.2, collapsed * 0.8),
    fontsize=9, color="black",
    arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
)

ax.set_ylabel("Number of WandB runs")
ax.set_title(f"v8b sweep: {collapsed}/{total_runs} runs collapsed to single-class prediction", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig9_1_v8b_collapse.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""Model collapse is a known failure mode in fine-tuning. When the loss landscape has sharp minima near trivial solutions (predicting a single class), gradient updates can push the model into a region where it never escapes. The noisy OpenCRE labels in v8b made this worse: the model learned that predicting Unrelated (the majority class) was a safe default."""))

nb["cells"].append(make_md("""### Failure 2: stacker overfitting

Even for the runs that did not collapse, the LightGBM stacker (which combined the three models' outputs into a final prediction) overfit catastrophically."""))

# --- Copy old cell 127: stacker overfitting diagnostic (rename figure) ---
nb["cells"].extend(copy_old_cells(old, [127]))

nb["cells"].append(make_md("""Training accuracy of 1.000 against validation accuracy of 0.528 is a 47-point gap. The stacker memorized the training data rather than learning generalizable patterns. With 17 input features (softmax logits from 3 models) and a small validation set, the LightGBM had enough capacity to memorize every training example.

> **Plain English:** The combiner---a machine learning model that was supposed to blend the three models' predictions---instead just memorized the training answers. It scored perfectly on the practice test and failed the real one. This is the classic overfitting problem, and it pointed to a clear fix: remove the learnable combiner entirely."""))

# --- NEW code cell: Figure 9.3 WandB loss curves (collapse vs success) ---
nb["cells"].append(make_code("""# Figure 9.3 — Training loss curves: collapsed vs. successful v8b runs.
# Line chart with two groups. Uses luminance contrast to distinguish
# collapse (red, thick) from success (blue, thin) (Borland & Taylor 2007).

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Select a few representative runs
collapsed_runs = [r for r in wandb_v8b
                  if r.get("n_unique_preds") == 1
                  and len(r.get("history", [])) > 3][:5]
healthy_runs = [r for r in wandb_v8b
                if r.get("n_unique_preds") == 4
                and len(r.get("history", [])) > 3][:5]

# Panel A: Training loss
ax = axes[0]
for r in collapsed_runs:
    epochs = [h.get("epoch") for h in r["history"] if h.get("train_loss") is not None]
    losses = [h["train_loss"] for h in r["history"] if h.get("train_loss") is not None]
    if epochs and losses:
        ax.plot(epochs, losses, color="#e74c3c", alpha=0.5, linewidth=2, label="_nolegend_")

for r in healthy_runs:
    epochs = [h.get("epoch") for h in r["history"] if h.get("train_loss") is not None]
    losses = [h["train_loss"] for h in r["history"] if h.get("train_loss") is not None]
    if epochs and losses:
        ax.plot(epochs, losses, color="#2e86c1", alpha=0.5, linewidth=1.5, label="_nolegend_")

ax.plot([], [], color="#e74c3c", linewidth=2, label="Collapsed")
ax.plot([], [], color="#2e86c1", linewidth=1.5, label="Healthy")
ax.legend(frameon=False, fontsize=9)
ax.set_xlabel("Epoch")
ax.set_ylabel("Training loss")
ax.set_title("Collapsed runs show flat loss after early epochs", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)

# Panel B: Combined F1
ax = axes[1]
for r in collapsed_runs:
    epochs = [h.get("epoch") for h in r["history"] if h.get("combined_f1") is not None]
    f1s = [h["combined_f1"] for h in r["history"] if h.get("combined_f1") is not None]
    if epochs and f1s:
        ax.plot(epochs, f1s, color="#e74c3c", alpha=0.5, linewidth=2)

for r in healthy_runs:
    epochs = [h.get("epoch") for h in r["history"] if h.get("combined_f1") is not None]
    f1s = [h["combined_f1"] for h in r["history"] if h.get("combined_f1") is not None]
    if epochs and f1s:
        ax.plot(epochs, f1s, color="#2e86c1", alpha=0.5, linewidth=1.5)

ax.set_xlabel("Epoch")
ax.set_ylabel("Combined F1")
ax.set_title("Collapsed runs never develop class diversity", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout()
plt.savefig(REPO_ROOT / "report" / "figures" / "fig9_3_wandb_loss_curves.png", dpi=150, bbox_inches="tight")
plt.show()"""))

nb["cells"].append(make_md("""The loss curves tell the story visually. Collapsed runs (red) plateau early: the model stops learning after the first few epochs because it has converged on the trivial solution of predicting a single class. Healthy runs (blue) show continued improvement, with combined F1 rising through training.

> **Plain English:** When a model collapses, its training loss curve goes flat. It has found a shortcut (always guess "unrelated") and stopped learning. The healthy runs keep improving because they are still finding structure in the data."""))

nb["cells"].append(make_md("""### What went wrong and what it taught us

Two root causes drove v8b's failures:

1. **Noisy labels at scale.** Adding 2,046 OpenCRE pairs with proxy labels overwhelmed the signal from 5,920 expert labels. The model learned to fit noise rather than structure.
2. **Learnable second stage.** The LightGBM stacker had enough capacity to memorize the noisy training distribution. A simpler combination method---one with no learnable parameters---could not overfit by construction.

These two observations directly motivated every design decision in v_final."""))

# ========================================
# SECTION 10: v_final Architecture
# ========================================

nb["cells"].append(make_md("""## 10 · v_final: clean architecture, proper validation

Three changes define v_final, each a direct response to a v8b failure mode."""))

# --- Copy old cells 131-132 (architecture diagram + dedup figure) ---
nb["cells"].extend(copy_old_cells(old, [131, 132]))

nb["cells"].append(make_md("""### Change 1: mapping-level deduplication

The v7c training split deduplicated at the text-pair level, but many pairs shared the same underlying mapping (e.g., the same two controls rephrased slightly differently). After deduplication at the mapping level, 56% of text-pair contamination was removed from the validation split. The validation metrics now reflect true generalization, not memorized near-duplicates."""))

nb["cells"].append(make_md("""### Change 2: ordinal loss functions

Standard cross-entropy treats each tier as equally wrong. An Unrelated-to-Equivalent misclassification costs the same as Unrelated-to-Partial. Three ordinal losses replace cross-entropy:

- **KL-divergence with ordinal smoothing.** Constructs soft label distributions centered on the true tier, decaying with ordinal distance.
- **CORN ordinal regression.** Learns cumulative thresholds P(tier >= k) as independent binary problems, then reconstructs the tier distribution.
- **Focal loss with class reweighting.** Down-weights easy examples (mostly Unrelated) and up-weights hard examples (Equivalent).

Each of the 3 models was trained with each of the 3 losses (9 runs total). The best checkpoint per model was selected by combined F1 on the clean validation split."""))

nb["cells"].append(make_md("""### Change 3: softmax averaging replaces stacking

After the stacker memorized v8b's training distribution, the fix was simple: remove the learnable second stage entirely. The ensemble prediction is the arithmetic mean of the three models' softmax probability vectors. This approach has zero learnable parameters in the combination step, so it cannot overfit by construction."""))

# --- Copy old cell 133: why softmax averaging beats learned stacking ---
nb["cells"].extend(copy_old_cells(old, [133]))

# --- Training infrastructure ---
nb["cells"].append(make_md("""### Training infrastructure

Nine model variants (3 encoders times 3 loss functions) were trained on three NVIDIA H100 80GB GPUs via RunPod. Two engineering challenges required workarounds:

- **BF16 GradScaler incompatibility.** H100 GPUs run BF16 natively, but PyTorch's GradScaler performs inf-checking that fails under BF16 (which has no distinct inf representation). Fix: disable GradScaler, run BF16 training directly with `torch.amp.autocast`.
- **CLS dimension mismatch.** BGE-large-v1.5 produces 1,024-dimensional CLS embeddings; RoBERTa-large and DeBERTa-base produce 768. The v_final pipeline handles each model's embedding dimension independently.

> **Plain English:** Three models, each trained three different ways, on fast GPUs. The final ensemble picks the best version of each model and averages their predictions. No learning in the averaging step means no overfitting in the averaging step."""))

# Renumber figures in copied cells
fig_map = {
    "Figure 11.3": "Figure 9.2",
    "Figure 12.1": "Figure 10.1",
    "Figure 12.2": "Figure 10.2",
    "fig11_3": "fig9_2",
    "fig12_1": "fig10_1",
    "fig12_2": "fig10_2",
}

section_start_idx = None
for i, c in enumerate(nb["cells"]):
    src = "".join(c["source"])
    if "## 9" in src and "collapse" in src.lower():
        section_start_idx = i
        break

if section_start_idx:
    for cell in nb["cells"][section_start_idx:]:
        src = "".join(cell["source"])
        for old_ref, new_ref in fig_map.items():
            src = src.replace(old_ref, new_ref)
        cell["source"] = [l + "\n" for l in src.split("\n")[:-1]] + [src.split("\n")[-1]]

save_notebook(nb)
