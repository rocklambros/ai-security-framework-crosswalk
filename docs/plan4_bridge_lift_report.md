# Plan 4 — Bridge / Graph Enrichment Report

Date:          2026-04-09T11:59Z
Git SHA:       d1dab15
Upstream pin:  1e286efa6dd78b6e044ea16dc3f64d854f9cd069

## Graph delta

- upstream_crossref edges injected: **0**
- firewalled (frozen-tuple overlap): **230**
- skipped (missing node / DSGAI not in graph): **133**
- total edges before: 5813
- total edges after:  5813

**Why zero injected?** All 363 upstream crossrefs link between OWASP
source lists (LLM Top 10, Agentic Top 10, DSGAI). The frozen-tuple
firewall (`data/splits/frozen_tuples.json`) contains all 10 `owasp_llm`
and all 10 `owasp_agentic` node IDs as frozen target tuples. Every
crossref edge targeting these nodes is correctly blocked to prevent
information leakage into the frozen test set. The remaining 133 crossrefs
target `owasp_dsgai` nodes which are not yet in the graph (DSGAI nodes
require framework expansion — Plan 4 Task Extension).

This is the correct behavior of the honesty firewall. The crossref edges
*cannot* be injected without violating the frozen test partition.

## Bridge benchmark (non-frozen cal, n=150)

| metric   | baseline | enriched | delta |
|----------|--------:|---------:|------:|
| MRR      |  0.1816 |   0.1816 |  0.00 |
| Hit@1    |  0.0600 |   0.0600 |  0.00 |
| Hit@5    |  0.2800 |   0.2800 |  0.00 |
| Hit@20   |  0.6133 |   0.6133 |  0.00 |

Delta is zero because zero upstream_crossref edges were injected.

## Node2Vec benchmark (non-frozen cal, n=150)

| metric   | baseline | enriched | delta |
|----------|--------:|---------:|------:|
| MRR      |  0.1711 |   0.1711 |  0.00 |
| Hit@1    |  0.0467 |   0.0467 |  0.00 |
| Hit@5    |  0.2733 |   0.2733 |  0.00 |
| Hit@20   |  0.6200 |   0.6200 |  0.00 |

Same reasoning. Node2Vec MRR (0.171) slightly trails bridge MRR (0.182),
consistent with the Session 6 finding that node2vec is a marginal
supplementary signal.

## Crossref benchmark (firewalled crossref edges, n=77)

| metric | value  |
|--------|-------:|
| n      |     77 |
| MRR    | 0.3283 |
| Hit@1  | 0.1299 |
| Hit@5  | 0.5974 |
| Hit@20 | 1.0000 |
| skipped| 153    |

77 of 230 firewalled crossrefs had both endpoints in the graph. The
bridge can recover the correct cross-source-list target in its top 5
for 60% of pairs and always within top 20 (the target sets are small:
10 LLM or 10 Agentic nodes). MRR 0.328 shows the bridge has meaningful
structural signal for cross-source-list relationships even without
crossref edges in the graph.

153 skipped: 133 target `owasp_dsgai` (not in graph), 20 other mismatches.

## Interpretation

- The frozen-tuple firewall correctly prevented all crossref edge
  injection. This is a **valid null result** — the graph enrichment
  mechanism works, but the crossref data entirely overlaps the frozen
  test endpoints.
- The crossref benchmark (MRR 0.328) is the first quantitative measure
  of cross-source-list mapping quality. It establishes a baseline for
  the Plan 5 classifier to beat.
- Framework expansion (adding DSGAI and the 18 other target frameworks)
  would unlock crossref edges for non-frozen framework pairs, enabling
  actual graph enrichment. This is documented in Plan 4 Task Extension.
- `human_test_frozen` was not read by any script in this plan.

## Artifacts

- `results/plan4_bridge_lift.json` — 1 row
- `results/plan4_node2vec_lift.json` — 1 row
- `results/plan4_crossref_benchmark.json` — 1 row
- `mapping_engine/engine/upstream_prior_edges.py` — loader with frozen-tuple firewall
- `mapping_engine/tests/test_upstream_prior_edges.py` — 5 tests
- `mapping_engine/scripts/benchmark_bridge_lift.py`
- `mapping_engine/scripts/benchmark_node2vec_lift.py`
- `mapping_engine/scripts/benchmark_crossref.py`
- `mapping_engine/tests/test_benchmark_crossref.py` — 4 tests
