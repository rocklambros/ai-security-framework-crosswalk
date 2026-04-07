"""Build notebooks/project1_crosswalk_eda.ipynb from scratch via nbformat.

Run from repo root: `python notebooks/build_project1_notebook.py`
The script is idempotent. Re-running overwrites the .ipynb.
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
# Section 1
# ============================================================
md(r"""
# AI Security Framework Crosswalk: Exploratory Visual Analysis

**Author:** Rock Lambros, University of Denver, COMP 4433 Project 1

## Abstract

This notebook explores a knowledge graph that links nine AI security frameworks
into a single crosswalk containing 983 nodes and 5,813 edges. The frameworks
are AIUC-1, CSA AICM, CoSAI Risk Map, EU GPAI Code of Practice, MITRE ATLAS,
NIST AI RMF, OWASP Agentic AI, OWASP AI Exchange, and OWASP LLM Top 10. The
mapping engine that produced this graph fuses four similarity signals: a
parent aware bridge score derived from shared category ancestors, a dense
semantic similarity computed by a pretrained sentence transformer, a TF IDF
keyword overlap, and a binary function match flag that asks whether two nodes
describe the same kind of object such as a control, a risk, a technique, or a
mitigation. The analysis below examines how those signals behave on real data,
where they agree and where they pull in opposite directions, how a learned
weighting compares to the hand tuned baseline that production currently uses,
and which framework pairs still have structural gaps that the next round of
labeling effort should target.

The intended reader is a scientific audience that wants to know whether the
choices the mapping engine is making are defensible. Every figure is paired
with a narrative that walks through what the visualization shows and why it
is informative for that question. No model training happens in the notebook
itself. All learned coefficients, embeddings, and benchmark numbers are read
from pre-computed CSV and JSON artifacts produced by the mapping pipeline.
""")


# ============================================================
# Section 2
# ============================================================
md("## 2 · Setup and Data Loading")
md(
    "All artifacts referenced below live in `data/processed/`. The mapping "
    "pipeline writes them as part of its normal run, and the notebook only "
    "reads them. The intent is to keep this notebook reproducible from any "
    "machine that has the repo cloned, without requiring access to a GPU or "
    "the embedding models."
)

code(r"""
# Standard scientific Python plus NetworkX. We import everything up front so
# that any environment problems surface immediately rather than three cells
# into the analysis.
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import networkx as nx

# Resolve the repo root in a way that works whether the notebook is launched
# from the repo root, from notebooks/, or from notebooks/project1_submission/.
# We walk upward looking for the data/processed directory rather than relying
# on a hard coded relative path, because graders will run this from a fresh
# unzipped submission folder.
HERE = Path.cwd()
candidate = HERE
for _ in range(4):
    if (candidate / "data" / "processed").exists():
        break
    candidate = candidate.parent
REPO = candidate
DATA = REPO / "data" / "processed"
assert DATA.exists(), f"could not locate data/processed starting from {HERE}"

# Seaborn theme. We pick the paper context because the deliverable is a static
# scientific document rather than a slideshow, and we set a slightly larger
# font_scale than the default so that axis labels remain readable when the
# notebook is rendered to PDF or HTML.
sns.set_theme(style="whitegrid", context="paper", font_scale=1.15)
plt.rcParams.update({
    "figure.dpi": 110,           # screen rendering
    "savefig.dpi": 300,          # print quality on export
    "axes.titleweight": "bold",  # titles need to anchor each panel
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "legend.frameon": False,     # frames around legends add visual noise
})

def jload(name):
    return json.loads((DATA / name).read_text())

def cload(name):
    return pd.read_csv(DATA / name)

# Load every artifact the notebook will reference. Loading them all in one
# place makes it obvious which files the notebook depends on, and lets the
# notebook fail fast if any of them are missing.
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
v1v2 = jload("v1_vs_v2_comparison.json")  # diff of expert v1 crosswalk vs pipeline v2

# Convert the JSON node and edge tables into pandas frames so we can use
# groupby-style operations later. Keeping both the raw list of dicts and the
# DataFrame view is convenient because some operations (like NetworkX graph
# construction) want the dict form, while aggregation wants the frame form.
nodes_df = pd.DataFrame(nodes)
edges_df = pd.DataFrame(edges)

# Print a small sanity summary so the reader can verify they loaded the same
# version of the data the analysis below assumes.
print(f"nodes: {len(nodes_df):,}   edges: {len(edges_df):,}")
print(f"frameworks: {nodes_df['framework'].nunique()}")
print(f"orphan nodes (graph_stats): {graph_stats['orphan_count']}")
print(f"training rows: {len(training):,}   nist validation rows: {len(nist_val):,}")
""")

md(
    "We also build a NetworkX directed graph from the same nodes and edges. "
    "We will use this later to compute degree distributions and to identify "
    "orphan nodes for the gap analysis in section 6. NetworkX gives us those "
    "structural metrics with one or two lines of code each, which is much "
    "cleaner than recomputing them from the raw edge list every time."
)

code(r"""
# Build a directed graph keyed on node_id. We use a DiGraph because the
# rationale codes (PARENT, MITIGATES, DETECTS, etc.) are directional. Treating
# the edges as undirected would conflate "control mitigates risk" with "risk
# mitigated by control" and would make in-degree and out-degree meaningless.
G = nx.DiGraph()
for n in nodes:
    # Only attach the fields we actually use downstream. Storing the full node
    # description on every NetworkX node would balloon memory unnecessarily.
    G.add_node(n["node_id"], **{k: n.get(k) for k in ("framework", "entry_type", "name")})
for e in edges:
    G.add_edge(e["source_node_id"], e["target_node_id"], rationale=e.get("rationale_code"))

print(f"NetworkX graph: |V|={G.number_of_nodes()}  |E|={G.number_of_edges()}")
print(f"weakly connected components: {nx.number_weakly_connected_components(G)}")
""")


# ============================================================
# Section 3
# ============================================================
md("## 3 · The Dataset: Framework Landscape")
md(
    "The crosswalk is structurally lopsided in a way that affects every "
    "downstream analysis. AIUC-1 and CSA AICM together account for roughly "
    "half of all nodes, and AIUC-1 originates the overwhelming majority of "
    "cross framework edges. Part of the explanation is that AIUC-1 was "
    "designed as a comprehensive control catalogue, so it naturally has many "
    "anchors that other frameworks can attach to. Part of the explanation is "
    "that the active labeling sessions concentrated their effort on AIUC-1 "
    "first because it offered the highest expected coverage per hour of SME "
    "review. Either way, any reader who treats the graph as if all frameworks "
    "contribute equally will be misled, and the figure below is designed to "
    "make the asymmetry impossible to miss in a single glance."
)

code(r"""
# Canonical framework order and pretty labels. Sorting alphabetically by the
# internal slug keeps the heatmap reproducible across runs, while the PRETTY
# dict gives us human readable axis labels.
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

# Restrict to genuinely cross framework edges. Intra framework edges (parent
# child links inside AIUC-1, for example) would dominate the heatmap and hide
# the cross framework structure that this section is trying to surface.
cross = edges_df[edges_df["source_framework"] != edges_df["target_framework"]]

# Aggregate cross framework edge counts into a 9x9 matrix. We reindex so that
# any framework with zero outbound edges still appears as a row, which is
# important because some frameworks (NIST RMF, OWASP Agentic, OWASP LLM) act
# only as targets and we want the empty rows to be visible.
edge_mat = (
    cross.groupby(["source_framework", "target_framework"])
    .size()
    .unstack(fill_value=0)
    .reindex(index=FRAMEWORKS, columns=FRAMEWORKS, fill_value=0)
)

# Node count per framework, sorted ascending so the bar chart reads top down.
node_counts = (
    nodes_df.groupby("framework").size().reindex(FRAMEWORKS).sort_values(ascending=True)
)
node_counts.index = [PRETTY[f] for f in node_counts.index]

# Confidence histogram. We force the conventional ordering rather than letting
# value_counts pick its own, so the visual ordering matches the editorial
# ranking from authoritative down to unvalidated.
conf_counts = edges_df["confidence"].fillna("unknown").value_counts()
conf_order = ["authoritative", "expert", "suggestive", "unvalidated", "unknown"]
conf_counts = conf_counts.reindex([c for c in conf_order if c in conf_counts.index])
""")

code(r"""
# Figure 3.1. Composed three panel layout. The reason for using gridspec
# rather than subplots is that the heatmap carries the central message and
# deserves the largest share of the canvas, while the two bar charts are
# supporting evidence and can be smaller. Equal sized subplots would force
# the heatmap into a square that is too small to read its 81 cells, while a
# differential gridspec lets us give the heatmap the room it needs.
fig = plt.figure(figsize=(13, 9))
gs = gridspec.GridSpec(
    2, 2,
    width_ratios=[2.2, 1.0],   # left column wider so the heatmap is not squished
    height_ratios=[1.6, 1.0],  # top row taller for the same reason
    hspace=0.45, wspace=0.35,
)

# Top row spans both columns. This is the differential sizing the assignment
# requirements ask for: the heatmap occupies a panel that is roughly four
# times the area of either bar chart underneath it.
ax_h = fig.add_subplot(gs[0, :])
sns.heatmap(
    edge_mat.values,
    ax=ax_h,
    annot=True, fmt="d",
    cmap="crest",  # sequential, perceptually uniform, accessible
    xticklabels=labels, yticklabels=labels,
    cbar_kws={"label": "cross-framework edges"},
)
ax_h.set_title("Figure 3.1 · Cross-framework edge counts (source → target)")
ax_h.set_xlabel("target framework")
ax_h.set_ylabel("source framework")
plt.setp(ax_h.get_xticklabels(), rotation=30, ha="right")

# Annotation that points at the AIUC-1 row. We add this because the row is
# the single most important visual feature of the chart and an arrow draws
# the eye to it before the reader has parsed the cell values.
aiuc_row = FRAMEWORKS.index("aiuc_1")
ax_h.annotate(
    "AIUC-1 is the hub:\nmost outbound edges originate here",
    xy=(len(FRAMEWORKS) - 0.5, aiuc_row + 0.5),
    xytext=(len(FRAMEWORKS) + 0.6, aiuc_row + 1.4),
    fontsize=9, ha="left", va="center",
    arrowprops=dict(arrowstyle="->", color="black", lw=1.0),
    annotation_clip=False,
)

# Bottom left: nodes per framework, horizontal bar so labels read left to
# right and the eye can compare lengths along a common baseline.
ax_n = fig.add_subplot(gs[1, 0])
sns.barplot(
    x=node_counts.values, y=node_counts.index,
    ax=ax_n, hue=node_counts.index, palette="crest", legend=False,
)
ax_n.set_title("Nodes per framework")
ax_n.set_xlabel("node count")
ax_n.set_ylabel("")
# Inline value labels save the reader from squinting at the axis ticks.
for i, v in enumerate(node_counts.values):
    ax_n.text(v + 4, i, str(int(v)), va="center", fontsize=8)

# Bottom right: confidence histogram. Vertical orientation here because there
# are only five categories and the labels are short, so vertical bars do not
# clip and the bottom right panel reads as a complement to the bottom left.
ax_c = fig.add_subplot(gs[1, 1])
sns.barplot(
    x=conf_counts.index, y=conf_counts.values,
    ax=ax_c, hue=conf_counts.index, palette="Set2", legend=False,
)
ax_c.set_title("Edges by confidence level")
ax_c.set_xlabel("")
ax_c.set_ylabel("edge count")
plt.setp(ax_c.get_xticklabels(), rotation=30, ha="right")
for i, v in enumerate(conf_counts.values):
    ax_c.text(i, v + 30, str(int(v)), ha="center", fontsize=8)

fig.suptitle("The crosswalk landscape: hub-and-spoke by design", y=1.00, fontsize=14, weight="bold")
plt.show()
""")

md(
    "The heatmap on top earns the largest share of the figure because it "
    "carries the central fact about this graph. Reading down the AIUC-1 row "
    "shows that nearly every other framework receives substantial inbound "
    "mapping from AIUC-1, while the corresponding column under AIUC-1 is "
    "almost empty, meaning very few frameworks have been mapped outward into "
    "AIUC-1 yet. CSA AICM is the secondary hub, and most of its outbound "
    "edges run to OWASP AI Exchange and to itself. Several rows are entirely "
    "empty, which corresponds to frameworks that have not yet been used as a "
    "mapping source in the current pipeline. The bar chart of node counts "
    "underneath confirms that the heatmap is not purely an artifact of "
    "corpus size, since CSA AICM is actually the largest framework by node "
    "count yet still produces fewer outbound edges than AIUC-1. The "
    "confidence histogram on the right gives the appropriate skepticism "
    "prior. The majority of edges sit at the suggestive confidence level, "
    "which means they were proposed by the mapping engine via category co "
    "occurrence and have not been reviewed by an expert. A much smaller core "
    "of edges carry authoritative or expert confidence. A reader looking at "
    "any single mapping in this graph should check its confidence level "
    "before treating it as evidence."
)

code(r"""
# Figure 3.2. Stacked bar chart of entry type composition. We row normalize
# so the bars all reach 1.0 and the comparison is about proportions rather
# than absolute counts. Absolute counts are already covered by figure 3.1.
type_mat = (
    nodes_df.groupby(["framework", "entry_type"]).size().unstack(fill_value=0)
    .reindex(FRAMEWORKS)
)
type_mat = type_mat.div(type_mat.sum(axis=1), axis=0)
# Order columns by total prevalence so the most common entry types appear at
# the bottom of every stack. This makes the colored bands easier to track
# across frameworks because the eye is anchored on the same baseline color.
type_mat = type_mat.loc[:, type_mat.sum().sort_values(ascending=False).index]

fig, ax = plt.subplots(figsize=(11, 5))
bottom = np.zeros(len(type_mat))
# Set2 is a categorical palette with good contrast at 7-8 categories, which
# is roughly the number of distinct entry_type values across all frameworks.
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
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", title="entry type")
plt.tight_layout()
plt.show()
""")

md(
    "Frameworks differ from one another in the kind of entries they contain, "
    "not only in how many entries they have. AIUC-1 and CSA AICM are "
    "dominated by controls and the activity steps that implement those "
    "controls. MITRE ATLAS is mostly attack techniques and mitigations. NIST "
    "AI RMF decomposes into functions, categories, and subcategories. OWASP "
    "Agentic and OWASP LLM are short risk catalogues with around ten entries "
    "each. This composition matters for the mapping engine because the "
    "function match feature asks whether the two nodes are the same kind of "
    "object, and that question is asymmetric. A control does not map to "
    "another control in any interesting way. A control maps to a risk it is "
    "meant to mitigate, or to a technique it is designed to detect. The "
    "bridge signal exploits exactly this asymmetry, which is why it carries "
    "more weight in the production composite than the simpler keyword "
    "overlap signal does."
)


# ============================================================
# Section 4
# ============================================================
md("## 4 · Signal Analysis: How the Mapping Engine Sees Similarity")
md(
    "The composite score that the mapping engine emits is a weighted sum of "
    "four primary signals plus an optional Node2Vec contribution. Whether "
    "that fused score is trustworthy depends on two conditions. Each signal "
    "has to be informative on its own at least somewhere in the data, and "
    "the signals have to disagree often enough that combining them adds "
    "information instead of just averaging redundant evidence. The figures in "
    "this section examine both conditions in turn."
)

code(r"""
# Figure 4.0. Marginal distributions of the four primary signals over the
# full labeled training pool. Before we start splitting by category or
# looking at correlations, we want to know what each feature looks like on
# its own. A 2x2 small multiples grid of histograms is the right format
# because it keeps the x axis scale consistent per feature while letting
# the reader eyeball all four shapes at once.
sig_cols_4 = ["bridge_score", "semantic_score", "keyword_score", "function_match"]
pretty_sig = {
    "bridge_score":   "bridge",
    "semantic_score": "semantic",
    "keyword_score":  "keyword",
    "function_match": "function match",
}
fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), sharey=False)
# crest is our single sequential palette for the whole notebook. We pull
# four well-separated samples from it so each panel has its own color
# without introducing a second palette family.
crest_colors = sns.color_palette("crest", n_colors=4)
for ax, col, color in zip(axes.flat, sig_cols_4, crest_colors):
    sns.histplot(
        data=training, x=col, ax=ax,
        bins=30, color=color, edgecolor="white", alpha=0.85,
    )
    ax.set_title(pretty_sig[col])
    ax.set_xlabel("")
    ax.set_ylabel("count")
    # Annotate the median as a thin vertical reference so the reader can
    # see central tendency without needing a second chart.
    med = training[col].median()
    ax.axvline(med, color="black", lw=0.8, ls="--")
    ax.text(
        med, ax.get_ylim()[1] * 0.92, f"  median={med:.2f}",
        fontsize=8, va="top",
    )
fig.suptitle("Figure 4.0 · Marginal distributions of the four primary signals", y=1.02, fontsize=13, weight="bold")
plt.tight_layout()
plt.show()
""")

md(
    "Before comparing signals against each other or splitting them by "
    "category, a good exploratory pass looks at each feature on its own. "
    "The four marginals tell four different stories and explain why the "
    "production composite blends rather than picks. Bridge is heavily "
    "right skewed because most candidate pairs share no graph neighbors "
    "and therefore get a near zero bridge score, with a long tail of pairs "
    "that genuinely do share structural context. Semantic is roughly "
    "unimodal and centered near the middle of the cosine range, which is "
    "a familiar shape for sentence embedding cosines on within domain text "
    "and is exactly the compression that makes a standalone semantic cutoff "
    "impossible. Keyword is more uniform than either of the other two "
    "content signals because TF IDF overlap varies smoothly with shared "
    "vocabulary density. Function match is effectively binary, which it "
    "should be given that it encodes a discrete taxonomy alignment check. "
    "The production composite needs all four because no single one of "
    "these shapes on its own is concentrated enough around the positives "
    "to act as a decision rule."
)

code(r"""
# Figure 4.1. Violin plot of semantic similarity for mapped versus unmapped
# pairs from training_data.csv. The training pool already contains both
# labeled positives (is_mapped == 1) and labeled negatives (is_mapped == 0)
# scored by the production sentence transformer, so we can show the
# distributional comparison directly without needing a separate benchmark.
sem = training[["semantic_score", "is_mapped"]].copy()
sem["label"] = sem["is_mapped"].map({0: "unmapped", 1: "mapped"})

fig, ax = plt.subplots(figsize=(8, 5))
# inner='quartile' adds the three internal quartile lines so the reader can
# see median and IQR without needing a separate box plot. cut=0 prevents the
# kernel density tails from extending past the actual data range, which
# would be misleading because cosine similarity is bounded.
sns.violinplot(
    data=sem, x="label", y="semantic_score", hue="label",
    ax=ax, inner="quartile", cut=0,
    palette=["#9aa6b2", "#1f77b4"], legend=False,
)
# Overlay the actual data points at low alpha. Violin plots can hide multi
# modality if the kernel bandwidth is wide, and the strip plot underneath
# acts as a sanity check that the density estimate matches reality.
sns.stripplot(
    data=sem, x="label", y="semantic_score",
    ax=ax, color="black", alpha=0.25, size=2.5, jitter=0.2,
)
ax.set_title("Figure 4.1 · Semantic similarity by mapping label")
ax.set_xlabel("")
ax.set_ylabel("cosine similarity")

# Print the mean separation directly on the chart. A small numerical anchor
# next to a distributional plot is more honest than asking the reader to
# eyeball the difference between two violins.
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
    "The two distributions of cosine similarity overlap heavily. Pairs that "
    "experts marked as unmapped still sit at a mean cosine of roughly 0.5, "
    "because every text in the corpus is written in the same AI security "
    "register and uses many of the same words. The mean separation between "
    "mapped and unmapped is only a few hundredths of a unit, and the "
    "distributions touch each other through most of their range. A decision "
    "rule built on raw semantic similarity alone would either have to set "
    "its threshold very high, losing recall in the process, or accept a "
    "large number of false positives. This is the empirical reason that the "
    "production composite includes the bridge and function match signals "
    "alongside the semantic axis. Cosine similarity on its own does not "
    "separate the classes well enough to be used as a standalone decision "
    "rule on this corpus."
)

code(r"""
# Figure 4.2. The same data viewed as overlaid density histograms, with an
# explicit annotation of the compression zone. Histograms and violins answer
# slightly different questions: a violin gives quick comparative shape, while
# a histogram gives a quantitative read on density at a given x value.
fig, ax = plt.subplots(figsize=(9, 5))
sns.histplot(
    data=sem, x="semantic_score", hue="label",
    bins=30, stat="density", common_norm=False,
    ax=ax, palette=["#9aa6b2", "#1f77b4"], alpha=0.55, edgecolor="white",
)
ax.set_title("Figure 4.2 · Semantic similarity histogram (the compression zone)")
ax.set_xlabel("cosine similarity")
ax.set_ylabel("density")

# Highlight the 0.4 to 0.7 band where the two classes are essentially
# indistinguishable. axvspan draws a tinted rectangle behind the histogram
# bars without obscuring them, which is the right effect for a contextual
# annotation: the reader should still be able to see the underlying data.
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
    "The same data viewed as overlaid densities reinforces the point. Both "
    "distributions pile up between 0.4 and 0.7, which is the compression "
    "zone the annotation marks. There is real signal in the high tail above "
    "0.7 where mapped pairs become dominant, but most of the labeled data "
    "lives in the compressed middle where the encoder cannot tell the "
    "classes apart. The calibrated production thresholds (Direct above 0.45 "
    "and Related above 0.25) are intentionally set on the composite score "
    "rather than on this raw cosine, because the composite has been spread "
    "out by the bridge and function match contributions and so admits a "
    "sensible cutoff that the raw cosine does not."
)

code(r"""
# Figure 4.3. Bridge v1 versus v2 scatter colored by expected tier. The
# bridge_comparison.csv file contains a small set of expert anchor pairs
# that were specifically chosen to expose the v1 -> v2 improvement. Plotting
# v1 on x and v2 on y lets us see the per pair lift directly: anything above
# the y == x diagonal represents an improvement.
fig, ax = plt.subplots(figsize=(8, 6))
tier_palette = {"Direct": "#2a9d8f", "Related": "#e9c46a", "None": "#9aa6b2"}
for tier, sub in bridge_cmp.groupby("expected_tier"):
    ax.scatter(
        sub["v1_jaccard"], sub["v2_bridge"],
        s=130, edgecolor="black", linewidth=0.6,
        color=tier_palette.get(tier, "#9aa6b2"),
        label=tier, zorder=3,
    )
# Reference axes through zero so the reader can see at a glance which points
# had a v1 score of essentially zero (almost all of them).
ax.axhline(0, color="gray", lw=0.5)
ax.axvline(0, color="gray", lw=0.5)
ax.set_xlabel("v1 Jaccard bridge (raw token overlap)")
ax.set_ylabel("v2 parent-aware bridge")
ax.set_title("Figure 4.3 · Bridge v1 vs v2 on expert anchors")
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
    "The bridge signal received a substantive rebuild in earlier work, and "
    "this scatter shows why that effort was justified. Every anchor pair in "
    "the comparison set has a v1 Jaccard score of essentially zero, which is "
    "to say that v1 returned no useful overlap for any of the cases on the "
    "chart. The v2 implementation, which inherits parent context so a child "
    "activity inherits some of its parent control's tokens and uses TF IDF "
    "weighting so common AI security boilerplate gets discounted, recovers a "
    "positive score for every one of those anchors. The cost is that v2 also "
    "fires more aggressively on negatives, which is the reason it has to be "
    "combined with the semantic and function match signals rather than used "
    "as a standalone score."
)

code(r"""
# Figure 4.4. Pearson correlation matrix across the four primary signals
# plus Node2Vec. We use Pearson rather than Spearman because the signals
# are continuous and roughly linear in their effect on the composite, and
# Pearson is the more conventional choice for feature interaction reporting
# in regression style models.
sig_cols = ["bridge_score", "semantic_score", "keyword_score", "function_match", "node2vec_score"]
corr = training[sig_cols].corr(method="pearson")

fig, ax = plt.subplots(figsize=(6.5, 5.5))
# A custom diverging palette centered at zero is appropriate for a
# correlation matrix because positive and negative correlations carry
# different meanings and should be visually distinct.
div_cmap = sns.diverging_palette(220, 20, as_cmap=True)
sns.heatmap(
    corr, ax=ax, annot=True, fmt=".2f",
    cmap=div_cmap, vmin=-1, vmax=1, center=0,
    square=True, cbar_kws={"label": "Pearson r"},
)
ax.set_title("Figure 4.4 · Signal correlation matrix")
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
plt.tight_layout()
plt.show()
""")

md(
    "The off diagonal correlations are mostly low, which is the precondition "
    "that makes a fused score worth computing in the first place. Bridge and "
    "keyword have the largest pairwise correlation, around what you would "
    "expect given that both reward shared vocabulary, but the magnitude is "
    "still modest. The single largest off diagonal entry is bridge against "
    "Node2Vec at r = 0.75, which is high and expected because both signals "
    "are structural readings of the same graph neighborhood. After that "
    "the correlations drop sharply: bridge against function match sits at "
    "r = 0.42, bridge against keyword at r = 0.34, Node2Vec against "
    "function match at r = 0.34, Node2Vec against keyword at r = 0.27. "
    "Everything touching the semantic axis is low: semantic against bridge "
    "is r = 0.11, against keyword is r = 0.13, against Node2Vec is "
    "r = 0.22, and against function match is r = 0.00 to two decimal "
    "places. The practical reading is that the semantic signal is the most "
    "informationally independent feature in the stack and function match "
    "is close behind. A feature that lives in its own direction in feature "
    "space contributes disproportionately to the effective rank of the "
    "combined signal, which is why the production composite keeps semantic "
    "at a non trivial weight even though its marginal shape (figure 4.0) "
    "is heavily compressed."
)

code(r"""
# Figure 4.5. Composite score broken down by target OWASP ASI risk. The
# training pool contains the Cartesian product of AIUC-1 source controls
# against the 10 agentic risks, so target_node_id is a ten level
# categorical we can use to ask whether a continuous variable (composite)
# shifts across levels of a categorical variable. That is guide question
# three from the assignment.
comp_df = training.copy()
# Reproduce the production composite inline from the four stored signal
# columns so the reader can see the formula next to the figure.
comp_df["composite"] = (
    0.467 * comp_df["bridge_score"]
    + 0.333 * comp_df["semantic_score"]
    + 0.200 * comp_df["keyword_score"]
) * (1 + 0.5 * comp_df["function_match"])
comp_df["target_id"] = comp_df["target_node_id"].str.split(":").str[-1]

# Order risks by descending median composite so the x axis implicitly
# ranks the targets from strongest to weakest candidate pool.
order = (
    comp_df.groupby("target_id")["composite"]
    .median().sort_values(ascending=False).index.tolist()
)

fig, ax = plt.subplots(figsize=(11, 5))
sns.boxplot(
    data=comp_df, x="target_id", y="composite", order=order,
    hue="target_id", palette="crest", legend=False,
    showfliers=True, linewidth=1.0, ax=ax,
)
ax.axhline(0.45, color="#e76f51", ls="--", lw=1.0)
ax.text(
    len(order) - 0.5, 0.455, "Direct cutoff (0.45)",
    fontsize=8.5, color="#e76f51", ha="right", va="bottom",
)
ax.set_title("Figure 4.5 · Composite score by target OWASP ASI risk (AIUC-1 → Agentic)")
ax.set_xlabel("target risk (ordered by median composite)")
ax.set_ylabel("composite score")
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
plt.tight_layout()
plt.show()
""")

md(
    "Composite score varies substantially across the ten agentic risks, "
    "which is the kind of finding that directly informs where a review "
    "round should focus. The risks at the left of the chart have "
    "consistently stronger candidate pools, meaning AIUC-1 contains many "
    "controls that score highly against them. The risks at the right have "
    "softer pools, meaning either the controls are genuinely less "
    "applicable or the signals are not surfacing them. The dashed line at "
    "0.45 marks the production Direct tier threshold and gives the reader "
    "a fixed reference for comparing distributions against the decision "
    "rule. The descriptive finding worth emphasizing is that no single "
    "risk is saturated: every distribution has an upper tail crossing the "
    "threshold, which means every agentic risk has at least a few strong "
    "candidate mappings. The differences across the ten risks are the "
    "cleanest example in the notebook of a continuous variable whose "
    "shape shifts meaningfully across levels of a categorical feature."
)


# ============================================================
# Section 5
# ============================================================
md("## 5 · Feature Relevance: How Different Weighting Strategies See the Signals")
md(
    "This section is a descriptive look at how four different weighting "
    "strategies distribute importance across the five signal features. It is "
    "not a model selection exercise. The fitted coefficients for each "
    "strategy are loaded from artifacts the pipeline produced in earlier "
    "preprocessing runs and are shown here purely as a way of asking which "
    "features different estimators decide are important. Whether any of "
    "these strategies should be deployed in production is a decision that "
    "lives outside this notebook and is answered in the improvement plan "
    "document. The reader should take this section as feature exploration, "
    "not as a model comparison."
)

code(r'''
# Figure 5.1. Grouped bar chart showing how four different weighting
# strategies distribute normalized importance across the five signal
# features. This is a descriptive look at four snapshots of the same
# question (which features matter?) taken through four different
# estimators, not a model comparison on a held-out set.
features = ["bridge_score", "semantic_score", "keyword_score", "function_match", "node2vec_score"]

# The hand tuned weights are kept in the source code of the mapper rather
# than in a JSON file. We hard code them here for the comparison so the
# notebook does not need to import the production package.
hand_w = {"bridge_score": 0.467, "semantic_score": 0.333, "keyword_score": 0.2,
          "function_match": 0.0, "node2vec_score": 0.0}
log_c = learned_w["logistic_coefficients"]
lgbm_i = learned_w["lightgbm_feature_importance"]
ord_c = learned_w["ordinal_coefficients"]

def normalize(d):
    # Sum of absolute values to 1 so four estimators living on wildly
    # different scales (logistic coefficients sum to about 15, LightGBM
    # importances into the thousands, ordinal coefficients into the hundreds)
    # can be compared on a single vertical axis.
    s = sum(abs(d.get(f, 0.0)) for f in features)
    return {f: (abs(d.get(f, 0.0)) / s if s else 0.0) for f in features}

hand_n = normalize(hand_w)
log_n = normalize(log_c)
lgbm_n = normalize(lgbm_i)
ord_n = normalize(ord_c)

x = np.arange(len(features))
w = 0.20   # bar width for four groups per tick
fig, ax = plt.subplots(figsize=(11, 5))
ax.bar(x - 1.5*w, [hand_n[f] for f in features], w, label="hand-tuned",         color="#9aa6b2")
ax.bar(x - 0.5*w, [log_n[f]  for f in features], w, label="logistic (|coef|)",  color="#1f77b4")
ax.bar(x + 0.5*w, [ord_n[f]  for f in features], w, label="ordinal (|coef|)",   color="#2a9d8f")
ax.bar(x + 1.5*w, [lgbm_n[f] for f in features], w, label="LightGBM importance", color="#e76f51")
ax.set_xticks(x)
ax.set_xticklabels([f.replace("_score", "").replace("_", " ") for f in features], rotation=30)
ax.set_ylabel("normalized |weight| (sum to 1)")
ax.set_title("Figure 5.1 · Four weighting strategies compared across five signal features")
ax.legend(frameon=False, loc="upper right")
# On-plot annotation for the feature with the widest spread across estimators.
# node2vec is the obvious story: hand-tuned gives it zero, LightGBM gives it
# the largest single share. Pointing this out with an arrow anchors the
# reader on the most discussion-worthy feature on the chart.
ax.annotate(
    "Widest disagreement:\nhand-tuned = 0,\nLightGBM ≈ maximum",
    xy=(4 + 1.5*w, lgbm_n["node2vec_score"]),
    xytext=(2.6, lgbm_n["node2vec_score"] + 0.08),
    fontsize=9, ha="left",
    arrowprops=dict(arrowstyle="->", lw=1.0, color="black"),
)
plt.tight_layout()
plt.show()
''')

md(
    "The four weighting strategies agree on one thing and disagree sharply "
    "on another. All four place substantial mass on the bridge signal, "
    "which is the strongest descriptive evidence in this figure that bridge "
    "is the single most informative feature across quite different "
    "estimator families. The disagreement is on Node2Vec. The hand tuned "
    "configuration zeroes it out, the LightGBM tree places the largest "
    "single share of its importance there, and the two linear estimators "
    "sit somewhere in between. This is exactly the kind of split that a "
    "purely descriptive look at the features is good at surfacing. The "
    "reason different estimators reach different conclusions about Node2Vec "
    "is a question for modeling work that lives outside this notebook. "
    "What the figure does tell the reader is that Node2Vec is the feature "
    "whose relevance is most estimator-dependent, and therefore the one to "
    "watch in any future modeling round. The bar chart format uses position "
    "on a common scale, which is the perceptual channel Cleveland and "
    "McGill identified as the most accurate available for quantitative "
    "comparison, so visual ranking across the four strategies is reliable "
    "to within a few percent."
)


# ============================================================
# Section 6
# ============================================================
md("## 6 · Coverage, Gaps, and Graph Structure")
md(
    "Even a well tuned mapping engine has structural gaps. This section "
    "makes those gaps visible so that future labeling effort can be targeted "
    "where it has the highest marginal value, instead of being spent "
    "uniformly across pairs that are already saturated."
)

code(r"""
# Figure 6.1. Coverage completeness heatmap. For each (source, target)
# framework pair, compute the share of source nodes that have at least one
# outbound edge into the target framework. A cell at 100% means every node
# in the source framework has been mapped to something in the target, which
# is the upper bound of coverage. White cells (NaN) are the diagonal, which
# we mask because intra framework coverage is not meaningful for this view.
src_counts = nodes_df.groupby("framework").size().reindex(FRAMEWORKS)
covered = (
    cross.groupby(["source_framework", "target_framework"])["source_node_id"]
    .nunique()
    .unstack(fill_value=0)
    .reindex(index=FRAMEWORKS, columns=FRAMEWORKS, fill_value=0)
)
# Cast to float so we can write NaN into the diagonal. Without the cast we
# would get a TypeError because the underlying array is integer.
coverage_pct = (covered.div(src_counts, axis=0) * 100.0).astype(float)
cov_arr = coverage_pct.to_numpy().copy()  # copy because the .values view is read-only
np.fill_diagonal(cov_arr, np.nan)

fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(
    cov_arr, ax=ax,
    annot=True, fmt=".0f",
    cmap="crest", vmin=0, vmax=100,
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
    "Coverage is bimodal in a way the heatmap makes obvious. The AIUC-1 row "
    "is mostly above 50 percent, because the active labeling sessions "
    "concentrated their effort on this framework and the production mapping "
    "engine fans out densely from it. CSA AICM and MITRE ATLAS sit somewhere "
    "in the middle, with partial coverage of OWASP AI Exchange and a few "
    "other targets. NIST AI RMF, OWASP Agentic, and OWASP LLM are entirely "
    "empty as source rows because the current pipeline treats them as "
    "targets only. That choice reflects the editorial role of those "
    "frameworks: they describe risks and outcomes rather than controls, so "
    "the natural mapping direction is from a control catalogue into them "
    "rather than the other way around. The consequence for downstream use "
    "is that a reader who wants to start at a NIST subcategory and walk "
    "outward to the controls that satisfy it has to invert the edge "
    "direction first, which the graph schema supports but the current data "
    "model does not pre-compute."
)

code(r"""
# Figure 6.2. Orphan nodes by framework. An orphan is a node with zero
# in-degree and zero out-degree in the directed graph, meaning it has no
# neighbors at all. We compute degrees from the NetworkX object built in
# section 2 rather than from the raw edges DataFrame, because NetworkX
# handles the edge direction bookkeeping correctly.
in_deg = dict(G.in_degree())
out_deg = dict(G.out_degree())

# Annotate every node with its in-degree and out-degree, then filter to the
# nodes that have neither. Group by framework so we can see which framework
# is contributing the most isolated nodes.
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
# Highlight the two frameworks where orphan counts are operationally
# meaningful (NIST RMF and OWASP AI Exchange) by giving them a contrasting
# color. The other frameworks share a single neutral color so the eye is
# drawn to the highlighted bars first.
colors = ["#e76f51" if PRETTY[f] in ("NIST AI RMF", "OWASP AI Exch.") else "#1f77b4"
          for f in orphan_per_fw.index]
ax.barh([PRETTY[f] for f in orphan_per_fw.index], orphan_per_fw.values, color=colors)
ax.set_title("Figure 6.2 · Orphan nodes by framework (zero in-degree and zero out-degree)")
ax.set_xlabel("orphan count")
for i, v in enumerate(orphan_per_fw.values):
    ax.text(v + 0.2, i, str(int(v)), va="center", fontsize=9)

# Annotate the bar with the largest count so the visual hierarchy points the
# reader at the most actionable finding first.
top = orphan_per_fw.idxmax()
top_idx = list(orphan_per_fw.index).index(top)
ax.annotate(
    "highest orphan count\n(unmapped territory)",
    xy=(orphan_per_fw[top], top_idx),
    xytext=(orphan_per_fw[top] + 4, max(top_idx - 1.5, 0)),
    fontsize=9,
    arrowprops=dict(arrowstyle="->", lw=1.0),
)
plt.tight_layout()
plt.show()
""")

md(
    "Orphan nodes are not always bugs. Some entries are structural "
    "placeholders or top level domain headers that legitimately have no "
    "neighbors. The interesting cases are persistent orphans inside "
    "frameworks that should have many connections, because those flag "
    "concrete labeling work. NIST AI RMF and OWASP AI Exchange both carry "
    "meaningful orphan counts, and those are the frameworks where the next "
    "round of human review will produce the largest gain in graph density. "
    "The bar chart format makes it easy to compare counts across frameworks "
    "at a glance, which is what a labeling planner actually needs in order "
    "to allocate review hours."
)

code(r"""
# Figure 6.3. Two dimensional projection of the Node2Vec embedding. The
# pipeline already ran UMAP on the 64 dimensional Node2Vec vectors and saved
# the (x, y) coordinates per node, so we just plot them here colored by
# framework. We deliberately use a low alpha so dense clusters do not turn
# into solid blobs and the reader can still see structure inside them.
fig, ax = plt.subplots(figsize=(10, 7))
for fw in FRAMEWORKS:
    sub = n2v_proj[n2v_proj["framework"] == fw]
    ax.scatter(sub["x"], sub["y"], s=14, alpha=0.55, label=PRETTY[fw])
ax.set_title("Figure 6.3 · Node2Vec embedding projected to 2D (UMAP)")
ax.set_xlabel("UMAP-1"); ax.set_ylabel("UMAP-2")
# Place the legend outside the plot area so it does not occlude any clusters.
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), markerscale=2, fontsize=9)
plt.tight_layout()
plt.show()
""")

md(
    "The Node2Vec embedding clusters mostly by framework, which is the "
    "expected result given that random walks on this graph are dominated by "
    "intra framework hierarchical edges. The structurally interesting points "
    "are the ones that drift toward another framework's cluster, because "
    "they correspond to nodes whose graph neighborhood overlaps meaningfully "
    "with content from a different source. Those are exactly the candidates "
    "that the bridge signal upweights, and they are the reason LightGBM "
    "ended up putting substantial importance on Node2Vec even though the "
    "production composite zeros it out. A future revision of the composite "
    "could reintroduce Node2Vec at a small weight specifically to surface "
    "these cross cluster bridge candidates, but that change should wait "
    "until a held out evaluation set exists which is not biased by the "
    "active learner's own selection of uncertainty cases."
)


# ============================================================
# Section 6.5 · v1 expert crosswalk vs v2 pipeline output
# ============================================================
md("### 6.4 · Expert crosswalk (v1) vs pipeline output (v2)")
md(
    "The AIUC-1 to OWASP ASI mapping is the only pair in this study where we "
    "have a hand-crafted expert crosswalk to compare against. The upstream "
    "AIUC-2 repository ships a set of 119 expert-authored pairs (Primary and "
    "Secondary relationships across the 10 ASI risks). The current pipeline "
    "produces 109 pairs for the same source and target. The two sets overlap "
    "but do not match, and the shape of the disagreement is informative about "
    "where the composite signal is strong and where it still needs help."
)

code(r"""
# Figure 6.4. Three panel diff of the v1 expert crosswalk against the v2
# pipeline output for AIUC-1 to OWASP ASI. We deliberately use gridspec with
# differentially sized axes so that the most important panel (the set sizes
# on the left) gets the widest frame and the supporting panels sit to the
# right as secondary reference material.
c = v1v2["counts"]
v1_only = c["lost_from_v1"]
both = c["preserved"]
v2_only = c["new_in_v2"]

fig = plt.figure(figsize=(13, 5), constrained_layout=True)
gs = gridspec.GridSpec(
    nrows=1, ncols=3, figure=fig,
    width_ratios=[1.5, 1.1, 1.4],   # left panel wider because it is the headline
)
axA = fig.add_subplot(gs[0, 0])
axB = fig.add_subplot(gs[0, 1])
axC = fig.add_subplot(gs[0, 2])

# Panel A: v1 only / preserved / v2 only set sizes. A stacked bar makes the
# overlap visually obvious without needing a Venn diagram, which matplotlib
# does not render cleanly without extra packages.
cats = ["v1 only\n(lost)", "preserved\n(in both)", "v2 only\n(new)"]
vals = [v1_only, both, v2_only]
colors = ["#e76f51", "#2a9d8f", "#457b9d"]
bars = axA.bar(cats, vals, color=colors, edgecolor="black", linewidth=0.6)
axA.set_title("Figure 6.4A · AIUC-1 to OWASP ASI pair-level diff")
axA.set_ylabel("number of (control, risk) pairs")
for b, v in zip(bars, vals):
    axA.text(
        b.get_x() + b.get_width() / 2, b.get_height() + 1,
        str(v), ha="center", va="bottom", fontsize=10,
    )
# On-plot annotation calling out the preservation rate, which is the single
# most important number in this whole section.
pct = c["preserved_pct"] * 100
axA.annotate(
    f"{pct:.1f}% of the 119 v1\nexpert pairs survive in v2",
    xy=(1, both), xytext=(1.4, both + 18),
    fontsize=9.5, ha="left",
    arrowprops=dict(arrowstyle="->", lw=1.0, color="#333"),
)
axA.set_ylim(0, max(vals) * 1.35)

# Panel B: tier distribution side by side. v1 only has Direct/Related because
# its labels are Primary/Secondary. v2 exposes the same two tiers in the
# production output. A grouped bar is the right chart for a 2x2 comparison.
td = v1v2["tier_distribution"]
tiers = ["Direct", "Related"]
v1_vals = [td["v1"].get(t, 0) for t in tiers]
v2_vals = [td["v2"].get(t, 0) for t in tiers]
x = np.arange(len(tiers))
width = 0.35
axB.bar(x - width/2, v1_vals, width, label="v1 (expert)", color="#f4a261", edgecolor="black", linewidth=0.5)
axB.bar(x + width/2, v2_vals, width, label="v2 (pipeline)", color="#264653", edgecolor="black", linewidth=0.5)
axB.set_xticks(x); axB.set_xticklabels(tiers)
axB.set_ylabel("pair count")
axB.set_title("Figure 6.4B · Tier distribution")
axB.legend(fontsize=9, loc="upper right")
for xi, vv in zip(x - width/2, v1_vals):
    axB.text(xi, vv + 1, str(vv), ha="center", fontsize=9)
for xi, vv in zip(x + width/2, v2_vals):
    axB.text(xi, vv + 1, str(vv), ha="center", fontsize=9)

# Panel C: composite score distribution for the 52 new-in-v2 pairs. This tells
# us whether the new candidates are confident discoveries or marginal ones
# living near the decision threshold. A KDE on top of a histogram (seaborn
# histplot with kde=True) gives both the raw shape and a smoothed summary.
new_scores = [p["v2_score"] for p in v1v2["new_pairs"]]
sns.histplot(new_scores, bins=14, kde=True, ax=axC, color="#457b9d", edgecolor="white")
axC.axvline(0.45, color="#e76f51", linestyle="--", linewidth=1.2)
axC.text(0.46, axC.get_ylim()[1] * 0.9, "Direct cutoff\n(0.45)", fontsize=8.5, color="#e76f51")
axC.set_title("Figure 6.4C · Score distribution of new-in-v2 pairs")
axC.set_xlabel("v2 composite score")
axC.set_ylabel("count")

plt.show()
""")

md(
    "The diff panel on the left describes where the two snapshots overlap. "
    "About forty eight percent of the 119 v1 expert pairs are also produced "
    "by v2, meaning sixty two pairs that a human expert flagged as primary or "
    "secondary mappings did not clear the production composite threshold on "
    "this run, and the pipeline separately surfaced fifty two new pairs that "
    "the expert set did not contain. The "
    "middle panel shows the tier distribution stays in roughly the same shape: "
    "v1 leans heavily toward Primary (Direct in our vocabulary) and v2 leans "
    "even harder that way, because the composite tends to resolve ambiguous "
    "cases into the top tier rather than the middle one. The right panel is "
    "the most diagnostic. Almost every new pair in v2 sits above the 0.45 "
    "Direct threshold, which means these are confident discoveries rather "
    "than marginal hits the threshold accidentally promoted. That in turn "
    "suggests the v1 expert set was not exhaustive, and part of the "
    "disagreement is the pipeline correctly finding mappings the human "
    "expert overlooked. The other part, of course, is the sixty two lost "
    "pairs where the human saw a relationship the composite does not score "
    "highly enough, and those are the queue for the next round of active "
    "learning. This is a descriptive comparison of two snapshots of the same "
    "mapping problem, not a judgment on which one is correct."
)


# ============================================================
# Section 7
# ============================================================
md("## 7 · Analytical Approaches and Next Steps")
md(r"""
This notebook is deliberately descriptive. It characterizes the dataset and the
signals the mapping engine uses without making causal claims about which
framework is the best or which mapping is the most important. The next phases
of the project layer on top of it as follows.

### Cross encoder reranking

Sessions 9 and 9B evaluated two cross encoder rerankers (`ms-marco-MiniLM-L-6-v2`
and `BAAI/bge-reranker-v2-m3`) on a pool of 550 SME labeled candidates. Both
rerankers were rejected for global adoption because they underperform on the
uncertainty sampled labeling pool. The active learner deliberately chose the
cases where the composite was least confident, which is exactly the kind of
input where rerankers struggle, so a per pair toggle remains an option but the
production composite is unchanged. This was a diagnostic exercise: the
rerankers were tested against the hypothesis that more sophisticated semantic
models would beat the existing ensemble, and the answer on this evaluation
pool was no.

### Active learning

Uncertainty sampling, which picks the candidate where the composite score is
closest to a tier boundary, is the technique that generated the labeling
sheets feeding into the comparisons in this notebook. As a method it is
descriptive in the sense that it takes the model as given and asks where to
label next. It becomes explanatory once the new labels are folded back into
the training pool and the weights are refit, because the comparison between
the old and new fits is a controlled experiment in which the only thing that
changed was the data.

### Contrastive fine tuning

The `finetune_benchmark.json` results show the realistic ceiling for the
semantic signal alone. A `bge-large-en-v1.5` encoder fine tuned on curated
triples from the labeled data improves precision at 5 from 0.81 to 1.00 on
the AIUC anchor set. That ceiling is expensive to reach because it requires
curated triples and GPU time, but it is the most likely path to compressing
the high baseline problem that figure 4.2 visualizes. The honest finding is
that better semantic signal would help, and the production system is
currently leaving that improvement on the table.

### LambdaMART and graph neural networks

Phase E of session 9B fit an XGBoost `rank:pairwise` model on the 550 unified
labels with group K fold cross validation by pair. The held out gain on
NDCG at 5 was a real positive number (around +0.078), but the train versus
held out gap was 0.31, far above the 0.10 overfit threshold the team set in
advance. The booster was rejected per the same honest rejection ledger as the
rerankers. A graph neural network for link prediction would inherit the same
overfitting risk on this label volume and is queued for after a non
uncertainty biased evaluation set exists.

### Transition to project 2

The dashboard for project 2 will turn the visualizations above into
interactive views. The cross framework heatmap becomes a clickable matrix in
which selecting a cell drills into the underlying mappings. The embedding
scatter becomes a brushable scatter linked to the underlying node text. The
confusion matrices become a per pair drill down. The reason this notebook is
static and matplotlib only is that the analytical case for each visualization
should be settled first, since interactivity can hide a weak underlying chart
behind motion and selection.

### Naming the methods using course vocabulary

| Approach | Type | Purpose |
| --- | --- | --- |
| Heatmaps, bar charts, histograms in this notebook | Descriptive | Characterize the dataset |
| Mapped versus unmapped distribution comparison (Figs 4.1, 4.2) | Diagnostic | Detect the high baseline problem |
| Hand tuned versus learned weight comparison (Sec 5) | Explanatory | Test which signals carry independent information |
| Coverage and orphan diagnostics (Sec 6) | Diagnostic | Identify where the next labeling round should go |
| Reranker and LambdaMART experiments (Sessions 9, 9B) | Confirmatory | Decide whether to adopt new components |
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
