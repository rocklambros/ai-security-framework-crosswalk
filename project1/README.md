# Project 1: AI Security Framework Crosswalk -- Exploratory Visual Analysis

A scientific notebook that performs an exploratory visual analysis of the AI Security Framework Crosswalk dataset using matplotlib and seaborn. Built as the first deliverable for COMP 4433 Data Visualization (University of Denver, Spring 2026).

## What this notebook does

The notebook walks a reader through a knowledge graph that links nine AI security frameworks into a single crosswalk containing **983 nodes and 4,001 graph edges**, augmented by upstream mappings, cross-references, and expert anchor pairs that bring the unified edge count to over 5,000. It is written for a technical audience that has not seen any of the underlying code. Every figure has narrative text before it explaining what to look for and text after it interpreting what the figure shows. A "Plain English" callout after each figure summarizes the takeaway for non-specialist readers.

The notebook also presents the results of the **v7c classifier**, a two-stage ensemble pipeline that predicts relationship tiers (Unrelated, Partial, Related, Equivalent) for any pair of nodes from different frameworks:

- **Stage 1:** Graph Attention Network (GAT) embeddings + 3 cross-encoder models (DeBERTa-v3-large, RoBERTa-large, DeBERTa-v3-base) + 3 baseline features (BGE cosine, BM25, bridge) = 50 features per pair
- **Stage 2:** Regularized logistic regression (C=0.01) with conformal prediction wrapping
- **Results:** 81.0% exact-tier accuracy, 94.4% adjacent accuracy, 91.6% conformal coverage on a 179-pair expert-labeled holdout test set

## Contents

- `COMP_4433_RockLambros_project1_crosswalk_eda.ipynb` -- The main analysis notebook (114 cells, 30 code cells, 24 figures)
- `project1_lambros.zip` -- Packaged submission (self-contained, includes all data)
- `data/` -- Self-contained data files for reproducibility
- `runs/v7c_sacred/` -- v7c evaluation results used by the notebook
- `mapping_engine/config/pairs/` -- Expert anchor pair configurations

## Running

The notebook is self-contained with all data files in `data/` and `runs/`. It loads pre-computed artifacts and does no ML or GPU work at render time.

```bash
cd project1
pip install numpy pandas matplotlib seaborn statsmodels scikit-learn pyyaml
jupyter lab COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
```

To execute the full notebook programmatically (verifies all 30 code cells run without error):

```bash
jupyter nbconvert --to notebook --execute COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
```

## Notebook sections and figures

The notebook is organized into ten sections with 24 figures:

### Section 3: Schema and Data Profile
- **Figure 3.0** -- Schema table profile showing node and edge field definitions
- **Figure 3.1** -- Lineage cards tracing each framework from source document to graph node
- **Figure 3.2** -- Node count distribution across frameworks
- **Figure 3.3** -- Edge confidence level distribution

### Section 4: The Dataset -- Framework Landscape
- **Figure 4.1** -- Three-panel gridspec: cross-framework edge count heatmap (center), nodes per framework bar (bottom left), confidence histogram (bottom right). The headline figure showing AIUC-1 as the hub.
- **Figure 4.1b** -- Transitive reachability heatmap. Same layout as 4.1 but counting unique node pairs reachable via direct edges or 2-hop transitive paths through bridge frameworks. Fills in the zeros from 4.1 (e.g., ATLAS to CSA AICM shows 629 reachable pairs despite zero direct edges).
- **Figure 4.2** -- Grouped bar chart of entry-type composition by framework (row-normalized)

### Section 5: v7c Feature Analysis
- **Figure 5.1** -- Small multiples of six legacy features broken out by expert tier (violin plots)
- **Figure 5.2** -- GAT cosine vs. Node2Vec cosine scatter colored by tier
- **Figure 5.3** -- v7c 50-feature importance (logistic regression absolute coefficients)

### Section 6: Feature Ablation
- **Figure 6.1** -- Leave-one-out ablation bar chart showing each feature family's contribution
- **Figure 6.2** -- Stacker accuracy by number of features (learning curve)

### Section 7: Coverage, Gaps, and Graph Structure
- **Figure 7.1** -- Cross-framework coverage completeness heatmap (direction-agnostic, direct edges)
- **Figure 7.1b** -- Transitive coverage completeness. Side-by-side comparison of direct-only vs. transitive coverage. Mean coverage rises from 21.5% to 47.2% when bridge paths are included.
- **Figure 7.2** -- Orphan nodes by framework
- **Figure 7.3** -- Node2Vec UMAP projection colored by framework

### Section 8: Model Evaluation
- **Figure 8.1** -- Confusion matrix and per-class accuracy (two-panel layout)
- **Figure 8.2** -- Side-by-side confusion matrices: GAT-only vs. full ensemble
- **Figure 8.3** -- Calibration reliability diagram

### Section 9: Conformal Prediction
- **Figure 9.1** -- Conformal prediction set sizes by tier (five-panel layout)
- **Figure 9.2** -- Fitted cumulative probabilities for hypothetical pairs

### Appendix A: Lineage and Diagnostics
- **Figure A.0** -- Lineage cards for all frameworks
- **Figure A.1** -- Per-framework edge density diagnostic
- **Figure A.2** -- Technique presence matrix heatmap

## Visualization design

Every chart follows principles from four assigned readings on data visualization:

- **Cleveland & McGill (1984)** -- Position along a common scale (rank 1) preferred over area or color saturation
- **Borner et al. (2019)** -- Categorical data encoded with distinct hues; ordinal data with luminance ramps
- **Borland & Taylor (2007)** -- Single-hue luminance ramps for sequential data; no rainbow colormaps
- **Graze & Schwabish (2024)** -- Named palettes, colorblind-safe, consistent across all figures

The ordinal tier palette uses a single-hue blue-teal luminance ramp (lighter = weaker relationship, darker = stronger). All heatmaps use the `crest` sequential colormap with cell-value annotations for direct labeling.

## See also

- [Root README](../README.md) -- Full project context
- [Project 2 README](../project2/README.md) -- Interactive Dash application
- [Visualization Design Rationale](../project2/VISUALIZATION_DESIGN.md) -- Plotly chart design decisions for the Dash app
