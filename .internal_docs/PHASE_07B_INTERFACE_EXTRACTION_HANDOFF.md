# Phase 07B Handoff: Interface Extraction Without Behavior Change

## Outcome

Phase 07B is implemented.

This pass extracted explicit internal provider seams for:

- embedder
- reranker
- query analyzer
- retriever
- answer backend

The refactor kept the existing CLI and default behavior stable while moving current implementations behind small internal contracts.

## What Changed

### Shared contracts

- added `src/eliza_rag/interfaces.py`
- defined internal protocols for `Embedder`, `Reranker`, `QueryAnalyzer`, `Retriever`, and `AnswerBackend`

### Default adapter migration

- `src/eliza_rag/embeddings.py`
  - moved embedding behavior behind resolver-selected adapters
  - preserved the existing hashed baseline and sentence-transformer-backed behavior
- `src/eliza_rag/retrieval.py`
  - moved deterministic query analysis behind `build_query_analyzer(...)`
  - moved retrieval mode dispatch behind `build_retriever(...)`
  - moved reranker dispatch behind `build_reranker(...)`
- `src/eliza_rag/answer_generation.py`
  - typed backend clients against the shared `AnswerBackend` contract
  - left prompt assembly and answer parsing in the core orchestration path

## Old-To-New Mapping

- `build_dense_vectors(...)` and `encode_text(...)` -> `Embedder` adapters selected by `resolve_embedder(...)`
- inline query-analysis logic in `analyze_query(...)` -> `DeterministicQueryAnalyzer`
- inline retrieval mode branching in `retrieve(...)` -> retriever adapters selected by `build_retriever(...)`
- inline reranker branching in `rerank_results(...)` -> reranker adapters selected by `build_reranker(...)`
- answer backend client typing in `answer_generation.py` -> shared `AnswerBackend` protocol in `interfaces.py`

## Validation

Commands run:

- `uv run pytest tests/test_embeddings.py -q`
- `uv run pytest tests/test_retrieval.py -q`
- `uv run pytest tests/test_answer_generation.py -q`

Observed results:

- `tests/test_embeddings.py`: `7 passed`
- `tests/test_retrieval.py`: `23 passed`
- `tests/test_answer_generation.py`: `23 passed`

## Deferred

- provider-specific configuration objects still live inside the current modules rather than separate provider packages
- `storage.py` still uses the existing embedding entrypoints instead of a deeper dependency-injected assembly layer
- CLI wiring intentionally stayed unchanged in this pass; the seams are internal

## Recommended Next Step

Proceed with bounded Phase 07C provider experiments behind the new interfaces:

- compare one alternate embedder against the current baseline
- compare one alternate reranker against the current baseline
- keep deterministic query analysis and the current answer orchestration as defaults unless the eval runner shows they are the main bottlenecks
