# Phase 06C Kickoff: Metadata-Aware Query Targeting And Coverage-Preserving Retrieval

## Purpose

Phase 06C is the next bounded retrieval-quality phase for the project.

Phase 06B established that stronger dense embeddings plus a stronger reranker were not enough to make the main multi-company comparison failure acceptable for demo lock. The next step is to improve how the candidate set is constructed before reranking, especially for questions that explicitly name multiple companies.

This phase should stay tightly scoped to deterministic query targeting and coverage-preserving retrieval behavior.

## Why Phase 06C Was Chosen

The current repo state already supports:

- lexical retrieval
- dense retrieval
- hybrid retrieval
- configurable reranking in retrieval and answer flows
- a stronger default dense model using `Snowflake/snowflake-arctic-embed-xs`
- a stronger default reranker using `BAAI/bge-reranker-v2-m3`

Phase 06B verified an important negative result:

- stronger embeddings alone did not make the main comparison question acceptable
- stronger reranking alone still did not guarantee candidate coverage across all named companies

Current interpretation:

- metadata-aware query targeting is the leading next experiment
- it is not yet a proven root cause

This phase should test whether retrieval quality improves when candidate coverage is made more deliberate before final reranking.

## Read First

Before changing code, read:

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `README.md`
- `ANSWER_PIPELINE_FIXES.md`
- `POST_LIVE_TESTING_PHASE_DECISION_HANDOFF.md`
- `PHASE_06B_RERANKING_KICKOFF.md`
- `PHASE_06B_RERANKING_RESULTS_HANDOFF.md`

Use repo files as the source of truth rather than prior chat context.

## Phase Goal

Improve candidate coverage for explicitly named companies and comparison-style questions before reranking, while keeping the one-final-call answer-generation contract unchanged.

## Target Outcomes

- detect named companies and tickers deterministically from the query
- detect when a question is explicitly multi-company or comparative
- add an optional retrieval path that preserves candidate coverage across named companies before final reranking
- compare current `hybrid + BGE rerank` against metadata-targeted alternatives
- document whether coverage-preserving retrieval materially improves grounded answer usefulness

## Scope For Phase 06C

Keep this phase tightly scoped to:

1. deterministic company and ticker detection
2. comparison-style intent detection
3. filtered or coverage-preserving candidate collection
4. reranking after coverage has been established
5. lightweight evidence on whether this improves the demo-blocking failure

Do not broaden into large eval infrastructure, broad architecture redesign, or final demo lock during this phase.

## Required Outputs

### 1. Deterministic query targeting

Implement a bounded query-targeting layer that can infer:

- named companies
- explicit tickers
- whether the query is multi-company
- whether the query is comparative enough to require coverage across named entities

Requirements:

- keep the logic deterministic and inspectable
- prefer repo-available metadata and simple rules over opaque heuristics
- do not add an LLM rewrite stage

### 2. Coverage-preserving retrieval behavior

Add a retrieval option that improves candidate coverage before reranking.

Acceptable approaches may include:

- metadata-filtered hybrid retrieval when entities are confidently detected
- candidate-pool allocation that preserves one-or-more candidates per named company
- fallback to the current baseline when no clear entity set is detected

Requirements:

- reranking remains downstream of candidate collection
- the final answer contract remains exactly one final LLM call
- the new behavior must be optional and inspectable rather than silently replacing all retrieval paths

### 3. CLI and configuration surface

Expose the new behavior cleanly enough that it can be tested and demonstrated.

Requirements:

- clear retrieval option naming
- clear defaults
- no ambiguous hidden mode switching

### 4. Focused validation

Run representative comparison-style questions and inspect whether:

- all named companies appear in the candidate set
- final top-k coverage improves
- irrelevant companies are reduced
- answer grounding becomes more defensible

### 5. End-of-phase documentation

Record what was implemented, what improved, and what remains uncertain.

The end result should make it easy to answer:

- did coverage-preserving retrieval help enough to justify the next demo-eval phase
- or is another bounded retrieval experiment still required

## Explicit Non-Goals

Do not spend this phase on:

- another reranker swap as the primary move
- another embedding-model swap as the primary move
- LLM-based query rewriting
- reopening backend reliability without a demonstrated regression
- final demo lock before retrieval quality is shown to be acceptable

## Suggested Execution Order

1. inspect the current retrieval flow and query-analysis hooks
2. define the deterministic company/ticker detection rules
3. decide the first coverage-preserving retrieval shape
4. expose the new behavior in retrieval and answer flows
5. add tests for parsing and retrieval behavior
6. run comparison-style validation queries
7. document what improved and what is still unproven

## Recommended Commands

Start from:

```bash
uv sync --extra dev
```

Useful verification commands:

```bash
uv run ruff check src tests
uv run python -m pytest tests/test_retrieval.py tests/test_answer_cli.py
uv run eliza-rag-search "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?" --mode hybrid --top-k 8
uv run eliza-rag-answer "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?" --mode hybrid
```

If new retrieval options are added, document the exact commands used to exercise them.

## Documentation Updates Required

At the end of Phase 06C:

- update `IMPLEMENTATION_KANBAN.md`
- write a results handoff for this phase
- update `DECISIONS.md` if the recommended retrieval path changes
- update `LIMITATIONS.md` if comparison-style caveats remain
- update `README.md` if reviewer-facing commands or recommended retrieval options change

## Definition Of Done

Phase 06C is done when:

- the repo has a deterministic query-targeting path for named-company questions
- the repo has an optional metadata-targeted or coverage-preserving retrieval path before reranking
- representative comparison-style runs were tested with exact commands recorded
- the project can clearly state whether this solved enough of the retrieval gap to move toward final evaluation and demo lock

## Worker Variants

### Worker A: Implementation Owner

Own:

- retrieval implementation
- query parsing
- CLI/config surface
- tests for changed code

Do:

- make the feature real and runnable
- keep documentation edits minimal and limited to surface-area changes you introduce
- leave a concise implementation handoff with exact commands

Do not:

- claim root-cause certainty from limited runs
- spend time on broad evaluation writeups beyond what is needed to validate your changes

### Worker B: Evaluation Owner

Own:

- reproducible comparison runs
- exact command capture
- result snapshots
- evidence writeup

Do:

- measure current baseline and new path if available
- emphasize whether named-entity coverage improved in final top-k
- state clearly what remains uncertain

Do not:

- make broad code changes unless narrowly needed for instrumentation
- present the query-targeting hypothesis as proven fact

## Phase 07 Preview

If Phase 06C succeeds, the next phase should likely focus on:

- lightweight evaluation and final demo lock
- choosing and documenting the recommended retrieval mode
- freezing the reviewer-facing demo path

If Phase 06C does not succeed, the next phase should remain another bounded retrieval-improvement step chosen from observed evidence rather than assumption.
