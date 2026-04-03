# Phase 04 Handoff

## Status

Phase 04 is complete for the intended scope:

- dense retrieval is implemented and queryable over a dedicated LanceDB table
- retrieval now supports `lexical`, `dense`, and `hybrid` behind one shared interface
- dense and hybrid CLI paths are available and documented
- lightweight structured query-analysis hooks exist for later expansion work
- multi-mode retrieval tests pass locally
- dense and hybrid retrieval now fail with an explicit prerequisite message when the dense index has not been built

## What Was Implemented

Key files:

- `src/eliza_rag/embeddings.py`
- `src/eliza_rag/retrieval.py`
- `src/eliza_rag/storage.py`
- `src/eliza_rag/retrieval_cli.py`
- `src/eliza_rag/dense_index_cli.py`
- `tests/test_retrieval.py`
- `README.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`

## Spec Coverage

### 1. Dense retrieval

Implemented a real dense retrieval path over the chunk corpus.

Delivered behavior:

- builds deterministic local embeddings for every chunk row
- writes vectors into the `filing_chunks_dense` LanceDB table
- persists dense-index metadata to `artifacts/dense_index_metadata.json`
- supports metadata-aware filtered vector search with normalized ranked results

Operational note:

- dense indexing is explicit via `uv run eliza-rag-build-dense-index`
- dense and hybrid retrieval require both the lexical chunk table and a built dense index; rerun `uv run eliza-rag-build-dense-index` after refreshing `filing_chunks`
- the current embedding model is a reproducible hashed baseline rather than a neural encoder

### 2. Shared retrieval interface

Implemented a common retrieval entry point for:

- `lexical`
- `dense`
- `hybrid`

Shared behavior:

- one normalized `RetrievalResult` shape
- one `RetrievalFilters` shape
- one CLI mode switch

### 3. Hybrid retrieval

Implemented a first hybrid retrieval path with reciprocal rank fusion.

Delivered behavior:

- retrieves lexical and dense candidates independently
- fuses candidates with a simple RRF score
- returns normalized results labeled as `hybrid_rrf`

### 4. Query-analysis and expansion hooks

Implemented lightweight shared query handling:

- `StructuredQuery` carries raw query text plus retrieval-mode-specific text fields
- lightweight year extraction can produce filing-date bounds when explicit filter args are absent
- dense-query expansion hooks exist for deterministic synonym growth in later phases

### 5. Retrieval comparison coverage

Expanded retrieval coverage to verify:

- dense retrieval returns normalized results
- dense retrieval preserves metadata filters
- lexical, dense, and hybrid paths can be compared through one interface
- hybrid fused ranks are stable and ordered

## New Command Paths

Build or refresh the dense index:

```bash
uv run eliza-rag-build-dense-index
```

Run dense retrieval:

```bash
uv run eliza-rag-search "risk factors" --ticker AAPL --top-k 3 --mode dense
```

Run hybrid retrieval:

```bash
uv run eliza-rag-search "revenue growth" --ticker GOOG --top-k 3 --mode hybrid
```

## Verification

Verification completed on April 2, 2026 with:

```bash
uv run python -m compileall src scripts tests
uv run --extra dev pytest tests/test_retrieval.py
uv run eliza-rag-build-dense-index
uv run eliza-rag-search "risk factors" --ticker AAPL --top-k 3 --mode dense
uv run eliza-rag-search "revenue growth" --ticker GOOG --top-k 3 --mode hybrid
```

Observed results:

- compile check succeeded
- retrieval test suite passed: `6 passed`
- dense-index build wrote `20062` rows into `filing_chunks_dense`
- dense CLI retrieval returned `3` filtered Apple chunks
- hybrid CLI retrieval returned `3` filtered Alphabet chunks with fused ranks

## Known Limitations

- the dense embedding model is a deterministic hashed baseline, not a stronger semantic encoder
- dense-only result quality is therefore weaker than the likely best eventual retrieval stack
- dense and hybrid retrieval are not self-initializing; they depend on the existing lexical chunk table plus the explicit dense-index build step
- hybrid retrieval is implemented, but later phases should evaluate stronger dense models and reranking before treating it as the final answer pipeline

## Decision Record Note

- `DECISIONS.md` was updated for the dedicated dense table and hashed baseline embedding workflow.
- The current LanceDB vector index implementation uses `IVF_HNSW_PQ` even though the older ANN decision text was written as plain `HNSW`; this is now called out explicitly so future phases do not assume those are identical.

## Recommended Phase 05 Start

Next work should focus on:

- upgrading deterministic query analysis beyond year extraction
- improving hybrid quality with better dense embeddings and reranking
- starting answer-pipeline assembly around the retrieved context
