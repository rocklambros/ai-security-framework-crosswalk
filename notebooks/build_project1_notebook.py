"""Build notebooks/project1_crosswalk_eda.ipynb from scratch via nbformat.

Run from repo root: `python notebooks/build_project1_notebook.py`
The script is idempotent — re-running overwrites the .ipynb.
"""
from __future__ import annotations
from pathlib import Path
import nbformat as nbf

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "notebooks" / "project1_crosswalk_eda.ipynb"

nb = nbf.v4.new_notebook()
cells = []


def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text: str) -> None:
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


# ============================================================
# Section 1 — Title and Abstract
# ============================================================
md(r"""
# AI Security Framework Crosswalk: Exploratory Visual Analysis

**Author:** Rock Lambros &nbsp;·&nbsp; University of Denver &nbsp;·&nbsp; COMP 4433 Project 1

## Abstract

This notebook explores a knowledge graph that links nine AI-security frameworks
(AIUC-1, CSA AICM, CoSAI Risk Map, EU GPAI Code of Practice, MITRE ATLAS,
NIST AI RMF, OWASP Agentic AI, OWASP AI Exchange, and OWASP LLM Top 10) into a
single 983-node, 5,813-edge crosswalk. A composite mapping engine fuses four
similarity signals (a parent-aware *bridge* score, dense semantic similarity,
TF-IDF keyword overlap, and a binary function-match flag), and the analysis
here interrogates how those signals behave, where they agree and disagree, how
the learned weights compare to the hand-tuned baseline, and where the graph
still has structural gaps.

The audience is a scientific reader who cares less about the prettiness of any
one chart and more about whether the choices the mapping engine is making are
defensible. Every figure is paired with a narrative that interprets the visual
in those terms.
""")


# ============================================================
# Section 2 — Setup and data loading
# ============================================================
md("## 2 · Setup and Data Loading")
md(
    "Load all pre-computed artifacts produced by the mapping pipeline. No model "
    "training happens in this notebook — every numeric input is a CSV or JSON "
    "that already lives in `data/processed/`."
)

code(r"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import networkx as nx

# resolve repo root whether the notebook is opened from repo root or notebooks/
HERE = Path.cwd()
REPO = HERE if (HERE / "data" / "processed").exists() else HERE.parent
DATA = REPO / "data" / "processed"
assert DATA.exists(), f"data/processed not found from {HERE}"

sns.set_theme(style="whitegrid", context="paper", font_scale=1.15)
plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "axes.titleweight": "bold",
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "legend.frameon": False,
})

def jload(name):
    return json.loads((DATA / name).read_text())

def cload(name):
    return pd.read_csv(DATA / name)

nodes = jload("nodes.json")
edges = jload("edges.json")
graph_stats = jload("graph_stats.json")
training = cload("training_data.csv")
nist_val = cload("nist_validation_data.csv")
bridge_cmp = cload("bridge_comparison.csv")
weight_cmp = jload("weight_comparison.json")
learned_w = jload("learned_weights.json")
finetune = jload("finetune_benchmark.json")
n2v_proj = cload("node2vec_projection.csv")

nodes_df = pd.DataFrame(nodes)
edges_df = pd.DataFrame(edges)

print(f"nodes: {len(nodes_df):,}   edges: {len(edges_df):,}")
print(f"frameworks: {nodes_df['framework'].nunique()}")
print(f"orphan nodes (graph_stats): {graph_stats['orphan_count']}")
print(f"training rows: {len(training):,}   nist validation rows: {len(nist_val):,}")
""")

md(
    "Build a NetworkX graph for any structural metrics that need it later "
    "(degree, components, etc.)."
)

code(r"""
G = nx.DiGraph()
for n in nodes:
    G.add_node(n["node_id"], **{k: n.get(k) for k in ("framework", "entry_type", "name")})
for e in edges:
    G.add_edge(e["source_node_id"], e["target_node_id"], rationale=e.get("rationale_code"))
print(f"NetworkX graph: |V|={G.number_of_nodes()}  |E|={G.number_of_edges()}")
print(f"weakly connected components: {nx.number_weakly_connected_components(G)}")
""")


# ============================================================
# Section 3 — The dataset
# ============================================================
md("## 3 · The Dataset: Framework Landscape")
md(
    "The crosswalk is heavily asymmetric: a few large frameworks (AIUC-1, "
    "CSA AICM, MITRE ATLAS) dominate the node count, and most cross-framework "
    "edges fan out from AIUC-1. Figure 3.1 below makes that asymmetry visible "
    "in a single composed figure with differentially sized panels."
)

code(r"""
FRAMEWORKS = sorted(nodes_df["framework"].unique())
PRETTY = {
    "aiuc_1": "AIUC-1",
    "csa_aicm": "CSA AICM",
    "cosai_rm": "CoSAI RM",
    "eu_gpai_cop": "EU GPAI CoP",
    "mitre_atlas": "MITRE ATLAS",
    "nist_rmf": "NIST AI RMF",
    "owasp_agentic": "OWASP Agentic",
    "owasp_ai_exchange": "OWASP AI Exch.",
    "owasp_llm": "OWASP LLM",
}
labels = [PRETTY[f] for f in FRAMEWORKS]

# cross-framework edge counts (exclude intra-framework hierarchical edges)
cross = edges_df[edges_df["source_framework"] != edges_df["target_framework"]]
edge_mat = (
    cross.groupby(["source_framework", "target_framework"])
    .size()
    .unstack(fill_value=0)
    .reindex(index=FRAMEWORKS, columns=FRAMEWORKS, fill_value=0)
)

# node counts per framework, sorted descending
node_counts = (
    nodes_df.groupby("framework").size().reindex(FRAMEWORKS).sort_values(ascending=True)
)
node_counts.index = [PRETTY[f] for f in node_counts.index]

# confidence-level edge counts
conf_counts = edges_df["confidence"].fillna("unknown").value_counts()
conf_order = ["authoritative", "expert", "suggestive", "unvalidated", "unknown"]
conf_counts = conf_counts.reindex([c for c in conf_order if c in conf_counts.index])
""")

code(r"""
fig = plt.figure(figsize=(13, 9))
gs = gridspec.GridSpec(
    2, 2,
    width_ratios=[2.2, 1.0],
    height_ratios=[1.6, 1.0],
    hspace=0.45, wspace=0.35,
)

# --- top-left (large): cross-framework edge heatmap
ax_h = fig.add_subplot(gs[0, :])
sns.heatmap(
    edge_mat.values,
    ax=ax_h,
    annot=True, fmt="d",
    cmap="rocket_r",
    xticklabels=labels, yticklabels=labels,
    cbar_kws={"label": "cross-framework edges"},
)
ax_h.set_title("Figure 3.1 · Cross-framework edge counts (source → target)")
ax_h.set_xlabel("target framework")
ax_h.set_ylabel("source framework")
plt.setp(ax_h.get_xticklabels(), rotation=30, ha="right")

# annotate the AIUC-1 hub row
aiuc_row = FRAMEWORKS.index("aiuc_1")
ax_h.annotate(
    "AIUC-1 is the hub:\nmost outbound edges originate here",
    xy=(len(FRAMEWORKS) - 0.5, aiuc_row + 0.5),
    xytext=(len(FRAMEWORKS) + 0.6, aiuc_row + 1.4),
    fontsize=9, ha="left", va="center",
    arrowprops=dict(arrowstyle="->", color="black", lw=1.0),
    annotation_clip=False,
)

# --- bottom-left: node counts per framework
ax_n = fig.add_subplot(gs[1, 0])
sns.barplot(
    x=node_counts.values, y=node_counts.index,
    ax=ax_n, palette="crest",
)
ax_n.set_title("Nodes per framework")
ax_n.set_xlabel("node count")
ax_n.set_ylabel("")
for i, v in enumerate(node_counts.values):
    ax_n.text(v + 4, i, str(int(v)), va="center", fontsize=8)

# --- bottom-right: edges by confidence
ax_c = fig.add_subplot(gs[1, 1])
sns.barplot(
    x=conf_counts.index, y=conf_counts.values,
    ax=ax_c, palette="flare",
)
ax_c.set_title("Edges by confidence level")
ax_c.set_xlabel("")
ax_c.set_ylabel("edge count")
plt.setp(ax_c.get_xticklabels(), rotation=25, ha="right")
for i, v in enumerate(conf_counts.values):
    ax_c.text(i, v + 30, str(int(v)), ha="center", fontsize=8)

fig.suptitle("The crosswalk landscape: hub-and-spoke by design", y=1.00, fontsize=14, weight="bold")
plt.show()
""")

md(
    "**Reading the figure.** The heatmap is the dominant panel because the "
    "single most important fact about this graph is the asymmetry it shows: "
    "AIUC-1 originates roughly an order of magnitude more cross-framework "
    "edges than any other framework. CSA AICM is the second hub, but it "
    "primarily fans out to its own controls and to OWASP AI Exchange. The "
    "node-count bar chart underneath confirms this is partly an artifact of "
    "raw size — AIUC-1 and CSA AICM are the two largest frameworks — but "
    "the bridge signal is also genuinely picking up the structural role "
    "AIUC-1 plays as a comprehensive control catalogue. The confidence "
    "histogram on the right is the sanity check: most edges are *suggestive* "
    "(machine-proposed via category co-occurrence), with a much smaller "
    "core of *authoritative* and *expert*-validated edges. That ratio is "
    "exactly what should drive a reader's prior on any single mapping."
)

code(r"""
# Figure 3.2 — entry-type composition per framework (stacked bars)
type_mat = (
    nodes_df.groupby(["framework", "entry_type"]).size().unstack(fill_value=0)
    .reindex(FRAMEWORKS)
)
type_mat = type_mat.div(type_mat.sum(axis=1), axis=0)  # row-normalize
type_mat = type_mat.loc[:, type_mat.sum().sort_values(ascending=False).index]

fig, ax = plt.subplots(figsize=(11, 5))
bottom = np.zeros(len(type_mat))
palette = sns.color_palette("Set2", n_colors=len(type_mat.columns))
for i, col in enumerate(type_mat.columns):
    ax.bar(
        [PRETTY[f] for f in type_mat.index],
        type_mat[col].values,
        bottom=bottom, label=col, color=palette[i],
    )
    bottom += type_mat[col].values
ax.set_title("Figure 3.2 · Entry-type composition by framework (row-normalized)")
ax.set_ylabel("share of nodes")
ax.set_ylim(0, 1)
plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", title="entry type")
plt.tight_layout()
plt.show()
""")

md(
    "**What this tells us.** Frameworks differ not just in size but in *kind*. "
    "AIUC-1 and CSA AICM are mostly controls and activities. MITRE ATLAS is "
    "dominated by techniques and mitigations. NIST AI RMF is almost entirely "
    "subcategories. OWASP Agentic and OWASP LLM are short risk catalogues. "
    "The bridge signal exploits this: when the source is a *control* and the "
    "target is a *risk*, the function-match feature is asymmetric in a way "
    "that the keyword and semantic features alone cannot capture."
)


# ============================================================
# Section 4 — Signal analysis
# ============================================================
md("## 4 · Signal Analysis: How the Mapping Engine Sees Similarity")
md(
    "The composite score is a weighted sum of four primary signals. This "
    "section interrogates each signal's distribution and how the signals "
    "covary, because the value of a fused score depends on whether its "
    "components disagree often enough to be informative."
)

code(r"""
# Figure 4.1 — semantic score distribution: mapped vs unmapped pairs.
# (semantic_benchmark.json was not produced by the current pipeline run; we
# substitute the equivalent comparison using the semantic_score column from
# training_data.csv, which contains both labeled-positive and labeled-negative
# pairs scored by the same encoder.)
sem = training[["semantic_score", "is_mapped"]].copy()
sem["label"] = sem["is_mapped"].map({0: "unmapped", 1: "mapped"})

fig, ax = plt.subplots(figsize=(8, 5))
sns.violinplot(
    data=sem, x="label", y="semantic_score",
    ax=ax, inner="quartile", cut=0, palette=["#9aa6b2", "#1f77b4"],
)
sns.stripplot(
    data=sem, x="label", y="semantic_score",
    ax=ax, color="black", alpha=0.25, size=2.5, jitter=0.2,
)
ax.set_title("Figure 4.1 · Semantic similarity by mapping label")
ax.set_xlabel("")
ax.set_ylabel("cosine similarity")
mapped_mean = sem.loc[sem.label == "mapped", "semantic_score"].mean()
unmapped_mean = sem.loc[sem.label == "unmapped", "semantic_score"].mean()
ax.text(
    0.5, 0.95,
    f"Δ means = {mapped_mean - unmapped_mean:+.3f}",
    transform=ax.transAxes, ha="center", va="top", fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray"),
)
plt.tight_layout()
plt.show()
""")

md(
    "**The high-baseline problem.** Both distributions sit well above 0.4. "
    "Even pairs that experts marked as *unmapped* still have cosine "
    "similarity around 0.5, because every text in this corpus is written in "
    "the same AI-security register. The mean separation between mapped and "
    "unmapped is small (typically a few hundredths), which is exactly why a "
    "single semantic score is not sufficient and the bridge signal has to "
    "carry structural weight."
)

code(r"""
# Figure 4.2 — high-baseline annotation, overlaid histogram.
fig, ax = plt.subplots(figsize=(9, 5))
sns.histplot(
    data=sem, x="semantic_score", hue="label",
    bins=30, stat="density", common_norm=False,
    ax=ax, palette=["#9aa6b2", "#1f77b4"], alpha=0.55, edgecolor="white",
)
ax.set_title("Figure 4.2 · Semantic similarity histogram (the compression zone)")
ax.set_xlabel("cosine similarity")
ax.set_ylabel("density")

# annotate the compression zone
ax.axvspan(0.4, 0.7, color="#f6c177", alpha=0.18, zorder=0)
ax.annotate(
    "All AI-security texts cluster here.\nThe signal is in the tail.",
    xy=(0.55, ax.get_ylim()[1] * 0.55),
    xytext=(0.78, ax.get_ylim()[1] * 0.85),
    fontsize=10, ha="left", va="center",
    arrowprops=dict(arrowstyle="->", lw=1.1, color="black"),
)
plt.tight_layout()
plt.show()
""")

md(
    "**Implication.** The interesting region for thresholding lies above 0.7, "
    "not at the conventional 0.5 cosine cutoff. The mapping engine's "
    "calibrated thresholds (Direct ≥ 0.45, Related ≥ 0.25 on the *composite*, "
    "not the raw semantic score) only make sense once you understand that the "
    "composite has been deliberately spread out by the bridge and function "
    "components."
)

code(r"""
# Figure 4.3 — bridge v1 vs v2 scatter, colored by expected tier.
fig, ax = plt.subplots(figsize=(8, 6))
tier_palette = {"Direct": "#2a9d8f", "Related": "#e9c46a", "None": "#9aa6b2"}
for tier, sub in bridge_cmp.groupby("expected_tier"):
    ax.scatter(
        sub["v1_jaccard"], sub["v2_bridge"],
        s=130, edgecolor="black", linewidth=0.6,
        color=tier_palette.get(tier, "#9aa6b2"),
        label=tier, zorder=3,
    )
ax.axhline(0, color="gray", lw=0.5)
ax.axvline(0, color="gray", lw=0.5)
ax.set_xlabel("v1 Jaccard bridge (raw token overlap)")
ax.set_ylabel("v2 parent-aware bridge")
ax.set_title("Figure 4.3 · Bridge v1 vs v2 on expert anchors")
# annotate v1 == 0 cases
ax.annotate(
    "v2 finds signal where v1\nreturns exactly zero",
    xy=(0.005, 0.16), xytext=(0.04, 0.18),
    fontsize=9,
    arrowprops=dict(arrowstyle="->", lw=1.0, color="black"),
)
ax.legend(title="expert tier")
plt.tight_layout()
plt.show()
""")

md(
    "**Why v2 was worth the rebuild.** Every anchor pair in the comparison "
    "set has a v1 Jaccard score of essentially zero — these were exactly the "
    "cases v1 missed. The v2 bridge, which inherits parent context and uses "
    "TF-IDF weighting, recovers a positive score for all of them. That's not "
    "a free lunch (v2 also fires more false positives, which is why it has "
    "to be fused with semantic and function-match signals), but it explains "
    "the qualitative jump in coverage between sessions."
)

code(r"""
# Figure 4.4 — signal correlation matrix.
sig_cols = ["bridge_score", "semantic_score", "keyword_score", "function_match", "node2vec_score"]
corr = training[sig_cols].corr(method="pearson")
fig, ax = plt.subplots(figsize=(6.5, 5.5))
sns.heatmap(
    corr, ax=ax, annot=True, fmt=".2f",
    cmap="vlag", vmin=-1, vmax=1, center=0,
    square=True, cbar_kws={"label": "Pearson r"},
)
ax.set_title("Figure 4.4 · Signal correlation matrix")
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
plt.tight_layout()
plt.show()
""")

md(
    "**Why fusion works.** The off-diagonal correlations are mostly low. "
    "Bridge and keyword overlap a little (both reward shared vocabulary), "
    "and bridge correlates positively with node2vec (both reward graph "
    "neighbors). But semantic similarity is largely uncorrelated with bridge, "
    "and function-match is almost orthogonal to everything. That is the "
    "necessary precondition for an ensemble: each signal carries information "
    "the others don't."
)


# ============================================================
# Section 5 — Learned vs hand-tuned weights
# ============================================================
md("## 5 · Learned vs Hand-Tuned: Evidence-Based Weight Selection")
md(
    "Three learners (logistic regression, LightGBM, an ordinal model) were "
    "fit to the labeled training data and compared against the hand-tuned "
    "weights (`bridge=0.467, semantic=0.333, keyword=0.2`). The questions "
    "this section asks: do the learners agree about which signals matter? "
    "And does that agreement justify replacing the hand-tuned weights?"
)

code(r"""
# Figure 5.1 — feature importance grouped bars.
import math

features = ["bridge_score", "semantic_score", "keyword_score", "function_match", "node2vec_score"]
hand_w = {"bridge_score": 0.467, "semantic_score": 0.333, "keyword_score": 0.2,
          "function_match": 0.0, "node2vec_score": 0.0}
log_c = learned_w["logistic_coefficients"]
lgbm_i = learned_w["lightgbm_feature_importance"]

def normalize(d):
    s = sum(abs(d.get(f, 0.0)) for f in features)
    return {f: (abs(d.get(f, 0.0)) / s if s else 0.0) for f in features}

hand_n = normalize(hand_w)
log_n = normalize(log_c)
lgbm_n = normalize(lgbm_i)

x = np.arange(len(features))
w = 0.27
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(x - w, [hand_n[f] for f in features], w, label="hand-tuned", color="#9aa6b2")
ax.bar(x,     [log_n[f]  for f in features], w, label="logistic (|coef|)", color="#1f77b4")
ax.bar(x + w, [lgbm_n[f] for f in features], w, label="LightGBM (importance)", color="#e76f51")
ax.set_xticks(x)
ax.set_xticklabels([f.replace("_score", "").replace("_", " ") for f in features], rotation=20)
ax.set_ylabel("normalized weight / importance")
ax.set_title("Figure 5.1 · Hand-tuned vs learned signal importance")
ax.legend()
plt.tight_layout()
plt.show()
""")

md(
    "**Reading.** All three models agree that *bridge* is the heaviest single "
    "signal. The hand-tuned weights deliberately set node2vec to zero — the "
    "learners disagree, with LightGBM in particular putting more than a third "
    "of its importance on node2vec. That is exactly the kind of disagreement "
    "that has to be reconciled with held-out evaluation rather than waved "
    "away by the model with the highest training accuracy. Per Cleveland & "
    "McGill, this comparison uses position on a common scale — the "
    "perceptual channel humans read most accurately — so visual ranking of "
    "feature importance is reliable."
)

code(r"""
# Figure 5.2 — ROC curves on the NIST validation set, computed from the
# stored composite-style scores using the learned coefficients.
from sklearn.metrics import roc_curve, auc as sk_auc

X_val = nist_val[features].values
y_val = nist_val["is_mapped"].values

def hand_score(row):
    return (
        hand_w["bridge_score"] * row["bridge_score"]
        + hand_w["semantic_score"] * row["semantic_score"]
        + hand_w["keyword_score"] * row["keyword_score"]
    )

hand_scores = nist_val.apply(hand_score, axis=1).values

intercept = log_c.get("intercept", 0.0)
log_z = (
    intercept
    + log_c["bridge_score"]   * nist_val["bridge_score"]
    + log_c["semantic_score"] * nist_val["semantic_score"]
    + log_c["keyword_score"]  * nist_val["keyword_score"]
    + log_c["function_match"] * nist_val["function_match"]
    + log_c["node2vec_score"] * nist_val["node2vec_score"]
)
log_scores = 1.0 / (1.0 + np.exp(-log_z.values))

# LightGBM importance is not a callable model here; use a proxy linear blend
# weighted by normalized LightGBM importance just to draw a comparable curve.
lgbm_scores = sum(lgbm_n[f] * nist_val[f].values for f in features)

curves = {
    "Hand-tuned":          (hand_scores, "#9aa6b2"),
    "Logistic":            (log_scores,  "#1f77b4"),
    "LightGBM (proxy)":    (lgbm_scores, "#e76f51"),
}

fig, ax = plt.subplots(figsize=(7, 6))
for name, (s, color) in curves.items():
    fpr, tpr, _ = roc_curve(y_val, s)
    a = sk_auc(fpr, tpr)
    ax.plot(fpr, tpr, color=color, lw=2, label=f"{name}  (AUC={a:.3f})")
ax.plot([0, 1], [0, 1], color="gray", lw=0.8, ls="--")
ax.set_xlabel("false positive rate")
ax.set_ylabel("true positive rate")
ax.set_title("Figure 5.2 · ROC curves on NIST AI RMF validation set")
ax.legend(loc="lower right")
plt.tight_layout()
plt.show()
""")

md(
    "**Held-out reality check.** Training-set numbers are misleading because "
    "the labeled training pool is small and the signals are highly correlated "
    "with the labels by construction. The honest comparison is the held-out "
    "NIST validation set: there, the gap between hand-tuned and learned "
    "models compresses dramatically, which is why `weight_comparison.json` "
    "still pins `best_model = \"Hand-tuned\"` — a learned model is only "
    "worth adopting if it generalizes."
)

code(r"""
# Figure 5.3 — confusion matrices side by side at threshold 0.5.
from sklearn.metrics import confusion_matrix

threshold = 0.5
hand_pred = (hand_scores >= 0.4).astype(int)  # hand-tuned uses a lower cutoff
log_pred = (log_scores >= threshold).astype(int)

cm_hand = confusion_matrix(y_val, hand_pred)
cm_log = confusion_matrix(y_val, log_pred)

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
for ax, cm, title in zip(axes, (cm_hand, cm_log), ("Hand-tuned (cutoff 0.40)", "Logistic (cutoff 0.50)")):
    sns.heatmap(
        cm, ax=ax, annot=True, fmt="d", cmap="Blues",
        xticklabels=["pred unmapped", "pred mapped"],
        yticklabels=["true unmapped", "true mapped"],
        cbar=False,
    )
    ax.set_title(title)
fig.suptitle("Figure 5.3 · NIST validation confusion matrices", weight="bold", y=1.02)
plt.tight_layout()
plt.show()
""")

md(
    "**What changed and what didn't.** Both models are dominated by the true-"
    "negative quadrant (the validation set is mostly unmapped pairs, as it "
    "should be — real-world mapping is sparse). The logistic model recovers "
    "a few more true positives but at the cost of more false positives, "
    "which is the standard precision-recall tradeoff. The decision to keep "
    "the hand-tuned weights for production is a deliberate choice in favor "
    "of precision: reviewers' time is the binding constraint, so a higher "
    "false-positive rate is more expensive than a few missed mappings."
)


# ============================================================
# Section 6 — Coverage, gaps, graph structure
# ============================================================
md("## 6 · Coverage, Gaps, and Graph Structure")
md(
    "Even a well-tuned mapping engine has structural gaps. This section makes "
    "those gaps visible: which framework pairs are fully explored, where the "
    "orphan nodes live, and what the embedding space looks like."
)

code(r"""
# Figure 6.1 — coverage completeness heatmap.
src_counts = nodes_df.groupby("framework").size().reindex(FRAMEWORKS)
covered = (
    cross.groupby(["source_framework", "target_framework"])["source_node_id"]
    .nunique()
    .unstack(fill_value=0)
    .reindex(index=FRAMEWORKS, columns=FRAMEWORKS, fill_value=0)
)
coverage_pct = (covered.div(src_counts, axis=0) * 100.0).astype(float)
cov_arr = coverage_pct.to_numpy().copy()
np.fill_diagonal(cov_arr, np.nan)

fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(
    cov_arr, ax=ax,
    annot=True, fmt=".0f",
    cmap="viridis", vmin=0, vmax=100,
    xticklabels=labels, yticklabels=labels,
    cbar_kws={"label": "% of source nodes with ≥1 mapping"},
    mask=np.isnan(cov_arr),
)
ax.set_title("Figure 6.1 · Cross-framework coverage completeness")
ax.set_xlabel("target framework")
ax.set_ylabel("source framework")
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
plt.tight_layout()
plt.show()
""")

md(
    "**Where the holes are.** Coverage is bimodal: AIUC-1 → everything-else "
    "is densely populated (the active labeling sessions concentrated here), "
    "while NIST RMF, OWASP Agentic, and OWASP LLM all have *zero* outbound "
    "coverage because they're treated as targets only in the current "
    "pipeline. That asymmetry is by design but it limits the kinds of "
    "queries the graph can answer (you cannot start at a NIST subcategory "
    "and walk outward without inverting edges first)."
)

code(r"""
# Figure 6.2 — orphan nodes per framework.
in_deg = dict(G.in_degree())
out_deg = dict(G.out_degree())
orphans = nodes_df.assign(
    in_deg=nodes_df["node_id"].map(in_deg),
    out_deg=nodes_df["node_id"].map(out_deg),
)
orphan_per_fw = (
    orphans[(orphans["in_deg"] == 0) & (orphans["out_deg"] == 0)]
    .groupby("framework").size().reindex(FRAMEWORKS, fill_value=0)
    .sort_values(ascending=True)
)

fig, ax = plt.subplots(figsize=(9, 4.5))
colors = ["#e76f51" if PRETTY[f] in ("NIST AI RMF", "OWASP AI Exch.") else "#1f77b4"
          for f in orphan_per_fw.index]
ax.barh([PRETTY[f] for f in orphan_per_fw.index], orphan_per_fw.values, color=colors)
ax.set_title("Figure 6.2 · Orphan nodes by framework (zero in-degree and zero out-degree)")
ax.set_xlabel("orphan count")
for i, v in enumerate(orphan_per_fw.values):
    ax.text(v + 0.2, i, str(int(v)), va="center", fontsize=9)

# annotate the largest orphan group
top = orphan_per_fw.idxmax()
top_idx = list(orphan_per_fw.index).index(top)
ax.annotate(
    "highest orphan count —\nunmapped territory",
    xy=(orphan_per_fw[top], top_idx),
    xytext=(orphan_per_fw[top] + 4, top_idx - 1.5),
    fontsize=9,
    arrowprops=dict(arrowstyle="->", lw=1.0),
)
plt.tight_layout()
plt.show()
""")

md(
    "**Orphan diagnostic.** Orphan nodes are not bugs per se — some entries "
    "(parent domains, structural placeholders) genuinely have no neighbors. "
    "But persistent orphans in NIST AI RMF and OWASP AI Exchange flag the "
    "frameworks where the next round of labeling has the highest marginal "
    "value."
)

code(r"""
# Figure 6.3 — Node2Vec 2D projection scatter.
fig, ax = plt.subplots(figsize=(10, 7))
for fw in FRAMEWORKS:
    sub = n2v_proj[n2v_proj["framework"] == fw]
    ax.scatter(sub["x"], sub["y"], s=14, alpha=0.55, label=PRETTY[fw])
ax.set_title("Figure 6.3 · Node2Vec embedding projected to 2D (UMAP)")
ax.set_xlabel("UMAP-1"); ax.set_ylabel("UMAP-2")
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), markerscale=2, fontsize=9)
plt.tight_layout()
plt.show()
""")

md(
    "**Embedding interpretation.** Frameworks form mostly coherent clusters "
    "in the Node2Vec space — the random-walk training on the existing edge "
    "set learned the obvious lesson that nodes inside the same framework "
    "co-occur most often. The interesting points are the *bridges*: nodes "
    "that drift toward another framework's cluster. Those are precisely the "
    "candidates the bridge signal upweights, and they explain why Node2Vec "
    "showed up in the LightGBM importance even though the production "
    "composite zeroes it out."
)


# ============================================================
# Section 7 — Analytical approaches and next steps
# ============================================================
md("## 7 · Analytical Approaches and Next Steps")
md(r"""
This EDA was deliberately *descriptive* — it characterizes the dataset and the
mapping engine's signals without making causal claims. The next phases of the
project layer on top of it as follows.

**Cross-encoder reranking (diagnostic).** Sessions 9 and 9B evaluated
`ms-marco-MiniLM-L-6-v2` and `BAAI/bge-reranker-v2-m3` on the 550 SME-labeled
candidates. Both rerankers were *rejected* for global adoption because they
under-perform on the uncertainty-sampled labeling pool (the active learner
deliberately chose the cases where the composite was least confident, which is
exactly where rerankers struggle). A per-pair toggle remains an option; the
honest finding is that the production composite still wins on this evaluation
set.

**Active learning (descriptive → explanatory).** Uncertainty sampling — pick
the candidate where the composite is closest to a tier boundary — is what
generated the labeling sheets visualized above. It is a *descriptive* technique
in the sense that it takes the model as given and asks where to label next; it
becomes *explanatory* once the new labels are folded back into the training
pool and the weights are refit.

**Contrastive fine-tuning (explanatory).** The `finetune_benchmark.json`
results show the ceiling: a fine-tuned `bge-large-en-v1.5` improves
`precision_at_5` from 0.81 → 1.00 on the AIUC anchor set. That ceiling is
expensive to reach (it requires curated triples and GPU time), but it is the
most likely path to compressing the high-baseline problem identified in
Figure 4.2.

**LambdaMART / GNN link prediction (the nuclear option).** Phase E of Session
9B fit XGBoost `rank:pairwise` on the unified 550 labels with group-K-fold by
pair. The held-out gain was real (+0.078 NDCG@5) but the train/holdout gap
was 0.31 — far above the 0.10 overfit threshold — so the booster was rejected
per the s10/s11/s13 honest-rejection ledger. A graph neural network for link
prediction would inherit the same overfitting risk on this label volume; it
is queued for after a non-uncertainty-biased eval set exists.

**Transition to Project 2.** The Dash app for Project 2 will turn the
visualizations above into interactive views: the heatmap becomes a clickable
matrix, the embedding scatter becomes a brushable scatter linked to the
underlying node text, and the confusion matrices become a per-pair drill-down.
This notebook is deliberately static and matplotlib-only so that the analytical
case for each visualization is settled *before* interactivity gets layered on
top.

**Naming the methods (course vocabulary).**

| Approach | Type | Purpose |
| --- | --- | --- |
| Heatmaps, bar charts, histograms (this notebook) | Descriptive | Characterize the dataset |
| Mapped-vs-unmapped distribution comparison (Fig 4.1, 4.2) | Diagnostic | Detect the high-baseline problem |
| Hand-tuned vs learned weights (Sec 5) | Explanatory | Test which signals carry causal weight |
| Coverage and orphan diagnostics (Sec 6) | Diagnostic | Identify where the next labeling round should go |
| Reranker / LambdaMART experiments (Sessions 9, 9B) | Confirmatory | Decide whether to adopt new components |
""")


# ============================================================
# write notebook
# ============================================================
nb["cells"] = cells
nb.metadata["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.metadata["language_info"] = {"name": "python"}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT)
print(f"wrote {OUT.relative_to(REPO)} ({len(cells)} cells)")
