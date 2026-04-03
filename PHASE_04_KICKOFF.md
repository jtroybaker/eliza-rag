# Phase 04 Kickoff

## Phase Goal

Extend the retrieval layer beyond the current lexical baseline by adding a second retrieval mode and the minimum shared abstractions needed for retrieval comparison.

This phase should move the repository from "one working retrieval path" to "multiple retrieval-capable paths behind a common interface" so later phases can add reranking, answer generation, and evaluation without redesigning retrieval again.

## Phase 03 Assessment

Phase 03 was successful and completed its intended scope.

Completed and verified:

- lexical retrieval is implemented over the local `filing_chunks` LanceDB table
- retrieval results are normalized into a reusable ranked result shape
- metadata-aware filtering hooks exist for retrieval
- CLI and script query paths exist
- retrieval smoke tests passed on `2026-04-02`

Important current retrieval facts:

- local database path: `data/lancedb`
- table name: `filing_chunks`
- current retrieval mode available: `lexical`
- normalized result shape already preserves downstream metadata needs

Conclusion:

- the retrieval foundation is in place
- no retrieval redesign is needed before adding dense and hybrid behavior

## Read First

Before changing code, read:

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `PHASE_03_HANDOFF.md`
- the retrieval, query-handling, and reranking sections of `HIGH_LEVEL_PLAN.md`

Use the repo files as the source of truth rather than prior chat context.

## Scope For Phase 04

Keep this phase tightly scoped to:

1. dense retrieval implementation
2. shared retrieval-mode interface improvements
3. early hybrid retrieval support if it fits cleanly
4. lightweight query-analysis and expansion hooks for later phases
5. early retrieval comparison coverage beyond simple smoke tests

Do not expand into full answer generation, final prompt design, or broad evaluation framework work yet.

## Required Outputs

### 1. Dense retrieval

Implement a real dense retrieval path over `filing_chunks`.

Requirements:

- generate embeddings for chunk rows using a local reproducible workflow
- persist embeddings in a way LanceDB can query directly
- support top-k vector retrieval over chunk rows
- preserve the same normalized result contract already used by lexical retrieval
- support the existing metadata filter object

Recommended behavior:

- keep embedding generation explicit rather than hidden inside query flow
- expose a clear command path for building or refreshing embeddings
- use the same table when practical, unless a separate vector-oriented table is materially cleaner

### 2. Shared retrieval interface

Strengthen the retrieval module so multiple retrieval modes can coexist without special-case downstream handling.

Requirements:

- support at least `lexical` and `dense`
- keep one common ranked result format
- keep one common filter shape
- support an explicit retrieval mode switch in code and CLI paths

Expectation:

- later hybrid and reranked retrieval should be able to plug into this interface with minimal refactor

### 3. Hybrid retrieval scaffolding or implementation

If it fits cleanly after dense retrieval, add a first hybrid retrieval path.

Acceptable first version:

- retrieve candidates from lexical and dense modes
- combine them with a simple, explainable fusion strategy such as reciprocal rank fusion
- return normalized ranked results with the retrieval mode labeled clearly

If hybrid retrieval does not fit cleanly in the phase without compromising dense retrieval quality, leave it as explicit scaffolding and document the remaining work.

### 4. Query-analysis and expansion hooks

Add minimal shared hooks for later query handling without overbuilding.

Good candidates:

- a structured query object
- optional ticker or company normalization hook
- optional time-range extraction hook
- optional lexical expansion field separate from the raw query

This does not need to become a full retrieval rewrite system yet.

### 5. Retrieval comparison coverage

Add lightweight test or command coverage that exercises the multi-mode retrieval layer.

Coverage should aim to verify:

- dense retrieval returns normalized ranked results
- metadata filtering still works under dense retrieval
- lexical and dense results can be compared under the same interface
- hybrid retrieval, if implemented, produces stable fused ranks

This is still not the full eval harness.

## Nice-To-Have, But Not Required

- cached embedding artifacts to reduce repeated indexing cost
- support for choosing the embedding model in config
- small retrieval comparison CLI output for `lexical` vs `dense` vs `hybrid`
- early query-analysis tests for ticker and date extraction

## Explicit Non-Goals

Do not spend this phase on:

- final one-call answer generation
- full prompt assembly
- full reranking implementation
- complete eval dataset creation
- `chonkie` integration
- UI work

Those belong to later phases.

## Suggested Execution Order

1. inspect the current retrieval module and CLI surface
2. choose and wire the dense embedding model and storage approach
3. implement chunk embedding generation and LanceDB vector indexing
4. add dense retrieval behind the existing normalized result interface
5. add CLI mode selection and verification commands
6. add lightweight query-analysis or expansion hooks if they fit naturally
7. implement or scaffold hybrid retrieval
8. run multi-mode retrieval checks and update docs

## Recommended Commands

Start from:

```bash
uv sync --extra dev
```

Useful verification commands:

```bash
uv run python -m compileall src scripts tests
uv run --extra dev pytest tests/test_retrieval.py
uv run eliza-rag-search "risk factors" --ticker AAPL --top-k 3 --mode lexical
```

If new embedding or dense-index commands are added in this phase, document them in `README.md`.

## Documentation Updates Required

At the end of Phase 04:

- update `IMPLEMENTATION_KANBAN.md`
- write a `PHASE_04_HANDOFF.md`
- update `README.md` with new dense or hybrid retrieval commands
- update `LIMITATIONS.md` if embedding-model or index caveats appear
- update `DECISIONS.md` only if a real design choice changes

## Definition Of Done

Phase 04 is done when:

- the repo has a working dense retrieval mode over the chunk corpus
- retrieval mode selection supports at least `lexical` and `dense`
- normalized results remain consistent across retrieval modes
- metadata-aware filtering still works for the new retrieval path
- lightweight verification exists for multi-mode retrieval behavior

## Phase 05 Preview

The next phase should likely focus on:

- stronger hybrid retrieval if still incomplete
- deterministic query analysis and metadata-aware expansion
- reranking integration
- early answer-pipeline assembly around retrieved context
