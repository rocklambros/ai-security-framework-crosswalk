# Mapping Engine: ML Improvement Plan

Last updated: April 7, 2026

## Results Summary (Session 11)

| item | value |
|---|---|
| Best weight method | **Hand-tuned kept** (logistic/LightGBM evaluated, rejected on FP tradeoff) |
| NIST validation: hand-tuned | see Figure 5.3 of Project 1 notebook |
| NIST validation: logistic | equal or marginally better recall, worse precision |
| Frozen pair tier_acc (SME) | csa_aicm 0.22, mitre_atlas 0.20, nist_rmf 0.30 |
| Total mappings (4 pairs) | 109 (AIUC→ASI) + 3 other pair outputs in `mapping_engine/output/results/` |
| v1 vs v2 preservation | 57/119 (47.9%) — flagged regression, lost set is next AL queue |
| Reranker | rejected (ms-marco + bge-v2-m3 both non-inferior at best) |
| Node2Vec | committed opt-in, production weight 0.0 |
| Fine-tune | base model kept |
| LambdaMART | rejected (overfit gate) |
| Highest-impact change | graph bridge (NetworkX 2-hop weighted Jaccard) — unblocked non-AIUC pairs |

## Phase status (Session 11)

- **Phase 1.1 — Embedding upgrade**: COMPLETE. sentence-transformers with per-pair Z-norm. Fine-tune benchmark evaluated; base model retained.
- **Phase 1.2 — Learned weights**: COMPLETE. Logistic + LightGBM trained and compared against hand-tuned. Production keeps hand-tuned weights. Coefficients preserved for the notebook ROC curves.
- **Phase 1.3 — Graph bridge**: COMPLETE. 2-hop weighted Jaccard via NetworkX. Highest-impact change in the program.
- **Phase 2.1 — Cross-encoder reranker**: COMPLETE, rejected. Both ms-marco-MiniLM-L-6-v2 and BAAI/bge-reranker-v2-m3 failed non-inferiority on the 550 SME pool.
- **Phase 2.2 — Active learning**: COMPLETE (rounds 1–2). 550 SME labels across 4 pair sheets, frozen in `test_s9_s8_parity.py`.
- **Phase 3.1 — Contrastive fine-tuning**: COMPLETE, rejected.
- **Phase 3.2 — Node2Vec**: COMPLETE, committed opt-in at weight 0.0.
- **Phase 4 — Negative signals**: DEFERRED. The v1-vs-v2 lost set (62 pairs) is the natural positive queue for the next labeling round; negative signal work moves after that.

---


## Approved Library Stack

Core (COMP 4433 approved): numpy, pandas, matplotlib, seaborn, statsmodels, sklearn

Extended (requires instructor approval, ask Ben Wednesday 3 PM):
- networkx: graph data structure, neighborhood computation, centrality metrics
- sentence-transformers: embedding models for semantic signal
- lightgbm: learned signal weights, gradient-boosted tier prediction

All ML/graph computation happens in preprocessing scripts or `mapping_engine/`. The Project 1 notebook loads pre-computed results and visualizes with matplotlib/seaborn only.

## Baseline: Current Pipeline (v1)

Four signals, hand-tuned weights, validated on 10 anchor pairs.

```
content   = 0.467 * reference_bridge + 0.333 * semantic + 0.200 * keyword
composite = min(content * (1 + 0.5 * function_match), 1.0)
```

Known problems:
- Embedding model (all-MiniLM-L6-v2, 22M params) lacks domain vocabulary
- Weights are hand-tuned, no evidence they're optimal
- Reference bridge is pair-specific (OWASP LLM Top 10 Jaccard)
- No negative signal (no way to detect false positives)
- No active learning loop for anchor selection
- 14.3% generalization gap on NIST validation set

## Prioritized Improvements

Ranked by ROI (impact per engineering hour). Each improvement includes what it replaces, how it integrates, and what to visualize in the Project 1 notebook.

### Phase 1: Drop-in upgrades (8 hours total)

#### 1.1 Upgrade Embedding Model

Time: 2 hours
Replaces: all-MiniLM-L6-v2 (22M params, 384 dims)
New: BAAI/bge-large-en-v1.5 (335M params, 1024 dims) or intfloat/e5-large-v2

Why: The current model has no understanding of compliance/governance vocabulary. "Vendor due diligence" and "supply chain risk" are distant in its embedding space. A larger model trained on more diverse corpora captures these relationships without manual synonym groups.

Integration:
- Drop-in replacement in `mapping_engine/engine/semantic.py`
- Same Z-score normalization pipeline applies
- Compare old vs new cosine similarity distributions to validate improvement

Notebook visualization:
- Side-by-side histograms: raw cosine similarity distribution for MiniLM vs bge-large
- Scatter plot: MiniLM score vs bge-large score per pair, colored by expert tier
- Expected result: wider score spread (less high-baseline compression) with the larger model

Success metric: Semantic signal alone correctly separates Direct from Related pairs with >0.15 score gap (currently ~0.08).

#### 1.2 Learn Signal Weights via Logistic Regression

Time: 4 hours
Replaces: hand-tuned weights (0.467, 0.333, 0.200)
New: sklearn LogisticRegression or LightGBM trained on labeled pairs

Training data:
- Positives: 119 AIUC expert mappings (from AIUC_2_OWASP repo test_data.json)
- Negatives: sampled from all 510 AIUC*OWASP pairs minus the 119 positives (391 negatives)
- Validation: 66 NIST mappings (held out entirely)

Features per (source, target) pair:
- bridge_score (float, 0-1)
- semantic_score (float, 0-1, after Z-norm)
- keyword_score (float, 0-1)
- function_match (binary, 0 or 1)
- entry_type_match (categorical: control-risk, control-control, technique-risk)
- domain_distance (float: cosine distance between domain-level embeddings)

Models to compare:
1. Logistic regression (interpretable, produces feature importance coefficients)
2. LightGBM (captures non-linear interactions between signals)
3. Ordinal regression via statsmodels (predicts tier directly: Direct > Related > None)

Notebook visualization:
- Feature importance bar chart: learned weights vs hand-tuned weights
- ROC curve for each model
- Calibration plot (predicted probability vs actual mapping rate)
- Confusion matrix on NIST validation set: hand-tuned vs learned weights

Success metric: Reduce the 14.3% generalization gap on NIST validation to <8%.

#### 1.3 2-Hop Weighted Jaccard for Graph Bridge

Time: 2 hours
Replaces: OWASP LLM Top 10 Jaccard (pair-specific)
New: graph-neighborhood Jaccard on the crosswalk graph (pair-agnostic)

How it works:
```python
import networkx as nx

def graph_bridge_score(G, node_a, node_b, confidence_weights, max_hops=2):
    """Weighted Jaccard on k-hop neighborhoods."""
    def weighted_neighbors(node, hops):
        neighbors = {}
        for neighbor in nx.single_source_shortest_path_length(G, node, cutoff=hops):
            if neighbor == node:
                continue
            # Weight by edge confidence and hop distance
            path_len = nx.shortest_path_length(G, node, neighbor)
            decay = 1.0 / path_len  # 1-hop=1.0, 2-hop=0.5
            edge_data = G.get_edge_data(node, neighbor) or G.get_edge_data(neighbor, node)
            conf = confidence_weights.get(edge_data.get('confidence', 'unvalidated'), 0.2) if edge_data else 0.2
            neighbors[neighbor] = decay * conf
        return neighbors
    
    n_a = weighted_neighbors(node_a, max_hops)
    n_b = weighted_neighbors(node_b, max_hops)
    shared = set(n_a.keys()) & set(n_b.keys())
    if not shared:
        return 0.0
    intersection = sum(min(n_a[n], n_b[n]) for n in shared)
    union = sum(max(n_a.get(n, 0), n_b.get(n, 0)) for n in set(n_a) | set(n_b))
    return intersection / union if union > 0 else 0.0
```

Confidence weights: authoritative=1.0, expert=0.8, inferred=0.4, unvalidated=0.2

Notebook visualization:
- Heatmap: framework-pair bridge score density (10x10 frameworks)
- Comparison scatter: old LLM-Top-10 Jaccard vs new graph-bridge for AIUC-OWASP pairs
- Network diagram (matplotlib, not interactive): subgraph around a high-bridge pair showing the shared neighborhood

Success metric: Non-zero bridge scores for >60% of framework pairs (currently 0% for pairs without LLM Top 10 citations).

### Phase 2: Precision improvements (7 hours total)

#### 2.1 Cross-Encoder Reranking

Time: 4 hours
New signal, not a replacement. Applied as a second-stage filter.

How it works:
- After the composite pipeline produces scored pairs, take the top 50 candidate pairs per source node
- Re-score each with a cross-encoder (cross-encoder/ms-marco-MiniLM-L-6-v2)
- The cross-encoder sees both texts simultaneously and models fine-grained token interactions
- Use the cross-encoder score as a reranking signal, not a replacement for the composite

Integration:
- New module: `mapping_engine/engine/reranker.py`
- Called after `composer.py`, before tier assignment
- Composite score is blended with cross-encoder: `final = 0.7 * composite + 0.3 * cross_encoder`
- The 0.7/0.3 blend is itself learnable via the logistic regression from 1.2

Notebook visualization:
- Before/after scatter: composite score vs reranked score, colored by tier change
- Bar chart: number of tier promotions and demotions after reranking
- Box plot: cross-encoder score distribution by expert-labeled tier

Success metric: Reranking changes <15% of tier assignments (stability) but improves precision on the NIST validation set by 5+ percentage points.

#### 2.2 Uncertainty-Based Active Learning

Time: 3 hours for the selection logic. Ongoing human time for labeling.

How it works:
- After running the pipeline on a new framework pair, identify the 20 pairs closest to each threshold boundary (composite score in [threshold - 0.05, threshold + 0.05])
- Rank by uncertainty: pairs where signals disagree (one high, one low) are more informative than pairs where all signals agree
- Present to expert for labeling: "Is this Direct, Related, or None?"
- Feed labels back into training set for 1.2

Uncertainty metric:
```python
def signal_disagreement(bridge, semantic, keyword):
    scores = [bridge, semantic, keyword]
    return max(scores) - min(scores)  # High disagreement = high uncertainty
```

Notebook visualization:
- Scatter plot: composite score vs signal disagreement, with threshold boundaries marked
- Highlight the 20 most-uncertain pairs as labeled points
- Before/after accuracy comparison: random anchor selection vs uncertainty-sampled anchors

Success metric: 10 uncertainty-sampled labels improve validation accuracy more than 20 random labels.

### Phase 3: Advanced (hold for Project 2 or post-course)

#### 3.1 Contrastive Fine-Tuning of Embedding Model

Time: 6 hours
Prerequisite: items 1.1 and 1.2 completed

How it works:
- Use 185 labeled pairs as positive examples
- Generate hard negatives: for each positive (A, B), find the nearest non-mapped node to A and pair it with B
- Fine-tune bge-large-en-v1.5 with MultipleNegativesRankingLoss (sentence-transformers library)
- 185 positives is thin. Augment with paraphrases (back-translation or synonym substitution on the text)

Risk: Overfitting on 185 examples. Mitigate with early stopping on the NIST validation set and learning rate warmup.

Notebook visualization:
- t-SNE of embedding space: before and after fine-tuning, colored by framework
- Retrieval precision at k=5: base model vs fine-tuned

#### 3.2 Node2Vec Graph Embeddings

Time: 8 hours
Prerequisite: graph has >500 edges from multiple pipeline runs

How it works:
- Train Node2Vec on the crosswalk graph (networkx + node2vec library)
- p=1, q=1 (balanced BFS/DFS) for initial run. Tune later.
- Use resulting node embeddings as a 4th content signal (or replace graph bridge)
- Cosine similarity between Node2Vec embeddings captures multi-hop structural similarity

Risk: Graph is too small for Node2Vec to learn meaningful structure. Only viable after running the pipeline on 5+ framework pairs to densify the graph.

Notebook visualization:
- 2D projection (UMAP or t-SNE) of Node2Vec embeddings, colored by framework
- Cluster analysis: do frameworks form coherent clusters? Do cross-framework edges connect cluster boundaries?

#### 3.3 GNN Link Prediction

Time: 12+ hours
Nuclear option. Hold for post-course research.

Train a Graph Attention Network for link prediction: given two nodes, predict whether an edge should exist and its confidence tier. Requires PyTorch Geometric. Only viable with a dense graph (1000+ edges).

### Phase 4: Negative signals and error correction (4 hours)

#### 4.1 Contrastive Feature Detection

Time: 2 hours

How it works:
- For each (source, target) pair with high semantic similarity, check for distinctive keywords that appear in opposite contexts across the corpus
- Example: "physical access" vs "API access" both contain "access" but the distinctive qualifier changes meaning entirely
- Implement as a penalty multiplier: `final = composite * (1 - 0.3 * contrastive_penalty)`

Integration: New module `mapping_engine/engine/contrastive.py`, called between composer and tier assignment.

Notebook visualization:
- Scatter: semantic score vs contrastive penalty, with false positives highlighted
- Top 10 false positives caught by contrastive detection

#### 4.2 Taxonomy Distance Regularization

Time: 2 hours

How it works:
- Use node metadata (entry_type, domain) to compute structural distance
- Same-domain pairs get a small boost (1.05x)
- Cross-domain pairs with high semantic similarity get flagged for review
- Pairs where entry_type semantics conflict (e.g., tactic mapped to commitment) get penalized

Notebook visualization:
- Heatmap: mapping density by source_domain x target_domain
- Box plot: composite score distribution for same-domain vs cross-domain pairs

## Project 1 Notebook Structure

The notebook tells the story of building and validating a mapping engine. Each section maps to a Project 1 requirement.

### Section 1: The Dataset (exploratory overview)
- Node count by framework (bar chart, seaborn)
- Entry type distribution (stacked bar)
- Edge count and confidence distribution (histogram)
- Framework connectivity heatmap (matplotlib, differential axes with gridspec) [REQ: multi-plot figure]

### Section 2: Signal Analysis (the engine's inputs)
- Semantic similarity distribution: MiniLM vs bge-large (side-by-side violin) [REQ: 3+ plot types]
- TF-IDF keyword overlap heatmap across frameworks
- Graph bridge score density by framework pair
- On-plot annotation: call out the high-baseline compression problem on the semantic histogram [REQ: annotation]

### Section 3: Learned vs Hand-Tuned Weights (the methodology improvement)
- Feature importance comparison (grouped bar chart)
- ROC curves overlaid (matplotlib)
- Confusion matrices side-by-side
- Discussion of which signals the model upweighted/downweighted and why [REQ: trends, observations]

### Section 4: Coverage and Gaps (what the graph reveals)
- Framework pair coverage completeness heatmap
- Unmapped node analysis by framework and entry_type
- Cluster analysis of Node2Vec embeddings (if Phase 3 complete) or bridge neighborhoods
- Annotated outliers [REQ: anomalies]

### Section 5: Analytical Approaches (next steps)
- Discussion of cross-encoder reranking, active learning, contrastive fine-tuning [REQ: analytical approaches]
- What would change with a denser graph
- Transition to Project 2 (Dash app for interactive exploration)

## Execution Order

1. Verify graph build output (nodes.json, edges.json exist and validate)
2. Implement Phase 1.3 (graph bridge) since it unblocks pair-agnostic mapping
3. Implement Phase 1.1 (embedding upgrade) in semantic.py
4. Run AIUC-1 to OWASP Agentic with new bridge + new embeddings, compare to v1 baseline
5. Implement Phase 1.2 (learned weights) using v1 labeled data
6. Run CSA AICM to OWASP Agentic as first new pair (stress test at 243 controls)
7. Implement Phase 2.1 (cross-encoder reranking) on top of Phase 1 results
8. Build Project 1 notebook, visualizing each phase's impact
9. Phase 2.2 (active learning) and Phase 4 (negative signals) as time permits
10. Phases 3.1-3.3 deferred to Project 2 or post-course

## Dependencies

```
# requirements.txt for mapping_engine/
numpy>=2.4.0
pandas>=2.3.3
matplotlib>=3.10.0
seaborn>=0.13.2
statsmodels>=0.14.6
scikit-learn>=1.8.0
networkx>=3.4
sentence-transformers>=3.4
lightgbm>=4.6
jsonschema>=4.23
pyyaml>=6.0
pydantic>=2.10
```
