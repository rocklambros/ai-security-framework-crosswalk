# Plan 3 Handoff Summary

## Scorers

| Scorer | Version | Scored/Total | Null Rate |
|---|---|---|---|
| bm25 | 1.0.0 | 1472/1894 | 22.3% |
| bge_cosine | 2.0.0 | 1894/1894 | 0.0% |

BM25 null rate is due to nodes with empty text (no description or name in nodes.json).

## Pool Matrix

- 26 framework pairs (`classifier.data.candidates.FRAMEWORK_PAIRS`)
- Pool: `data/candidates/pool_v1.jsonl` (Plan 1-B)
- llm_val: `data/labels/llm_sme/v1/labels.jsonl` (1894 silver labels, Plan 2)

## Retrieval-Floor Parity

- `coverage_at_20 = 0.6500` (unchanged vs Plan 1-B baseline)
- `coverage_at_k_used(100) = 0.8825` (unchanged)
- Lifting the 0.6500 ceiling is Phase 2/3 reranker work, NOT Plan 3

## Outputs for downstream plans

- `data/features/baseline_features.parquet` (Plan 5 stacker input)
- `data/baselines/latest/results_llm_val.json` (eval results)
- `data/baselines/bge_cosine_embeddings.parquet` (768-dim BAAI/bge-base-en-v1.5)

## Not implemented (deferred)

- v2 composite scorer (requires mapping_engine integration)
- BGE reranker scorer (requires FlagEmbedding, large GPU memory)
- Opus 4.6 zero-shot ceiling (requires Opus API access; only Haiku available)
- Per-pair coverage CLI (depends on full scorer set)

These can be added incrementally by registering new scorers against the Protocol.
