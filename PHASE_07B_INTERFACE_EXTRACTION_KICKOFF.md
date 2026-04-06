# Phase 07B Kickoff: Interface Extraction Without Behavior Change

Implementation handoff: `PHASE_07B_INTERFACE_EXTRACTION_HANDOFF.md`

## Purpose

This worker owns the no-behavior-change modularization pass for Phase 07.

The goal is to extract clean internal seams so provider swaps can happen safely later.

## Own

- explicit internal interfaces for:
  - embedder
  - reranker
  - query analyzer
  - retriever
  - answer backend
- moving current implementations behind those interfaces
- keeping existing CLI behavior stable

## Do Not Own

- broad evaluation design
- changing the recommended retrieval mode
- introducing learned routing
- landing multiple new provider implementations as part of the same refactor

## Required Outputs

### 1. Interface Definitions

Define internal contracts that are small, explicit, and easy to test.

Priority order:

1. embedder
2. reranker
3. query analyzer
4. retriever
5. answer backend

### 2. Default Adapter Migration

Move the current implementations behind those interfaces first.

Requirements:

- preserve current config semantics
- preserve current CLI semantics
- preserve current default retrieval and answer behavior

### 3. Contract Tests

Add or update tests so they validate interface-level behavior rather than only current concrete modules.

## Validation

At minimum, leave behind:

- exact test commands run
- a short mapping of old modules to new interface-backed modules
- a note describing any intentionally deferred extraction work

## Definition Of Done

This worker is done when:

- the main provider seams are explicit in the codebase
- current defaults still behave the same way
- tests cover the extracted contracts well enough to support later provider swaps

## Implementation Notes

### Interface-backed modules

- embedder: `src/eliza_rag/embeddings.py` now resolves document and query embedding through `resolve_embedder(...)` and the `Embedder` contract in `src/eliza_rag/interfaces.py`
- reranker: `src/eliza_rag/retrieval.py` now resolves rerankers through `build_reranker(...)` and the `Reranker` contract in `src/eliza_rag/interfaces.py`
- query analyzer: `src/eliza_rag/retrieval.py` now routes `analyze_query(...)` through `build_query_analyzer(...)` and the `QueryAnalyzer` contract in `src/eliza_rag/interfaces.py`
- retriever: `src/eliza_rag/retrieval.py` now routes mode selection through `build_retriever(...)` and the `Retriever` contract in `src/eliza_rag/interfaces.py`
- answer backend: `src/eliza_rag/answer_generation.py` now types backend clients against the shared `AnswerBackend` contract in `src/eliza_rag/interfaces.py`

### Old-to-new mapping

- `build_dense_vectors(...)` and `encode_text(...)` -> `Embedder` adapters selected by `resolve_embedder(...)`
- inline query-analysis logic in `analyze_query(...)` -> `DeterministicQueryAnalyzer`
- inline retrieval mode branching in `retrieve(...)` -> retriever adapters selected by `build_retriever(...)`
- inline reranker branching in `rerank_results(...)` -> reranker adapters selected by `build_reranker(...)`
- answer backend client ABC in `answer_generation.py` -> shared `AnswerBackend` protocol in `interfaces.py`

### Validation

- `uv run pytest tests/test_embeddings.py -q`
- `uv run pytest tests/test_retrieval.py -q`
- `uv run pytest tests/test_answer_generation.py -q`

### Deferred

- provider-specific configuration objects are still kept inside the current modules rather than moved into separate provider packages
- retrieval artifact building in `storage.py` still calls the existing embedding entrypoints instead of a deeper dependency-injected assembly layer
- CLI wiring is intentionally unchanged; this pass only extracted internal seams behind the existing defaults
