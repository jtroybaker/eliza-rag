# Phase 03 Kickoff

## Phase Goal

Implement the first retrieval-capable query path over the existing LanceDB chunk store.

This phase should turn the current chunked corpus into something that can accept a user-style question, retrieve relevant chunks, and return normalized retrieval results suitable for later prompt assembly, reranking, and evaluation.

## Current State

The repository is ready to proceed.

Completed in prior phases:

- project scaffold and dependency baseline
- corpus extraction and inspection
- filing-level normalization
- deterministic chunk materialization
- local LanceDB chunk-table loading

Current chunk/LanceDB baseline:

- corpus filings processed: `246`
- chunk rows materialized: `20,062`
- local LanceDB table exists at `data/lancedb`
- table name: `filing_chunks`

## Important Context

Before making changes, read:

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `PHASE_02_HANDOFF.md`
- relevant retrieval sections of `HIGH_LEVEL_PLAN.md`

Use repo files as the source of truth.

## Phase 03 Position

We are in a workable implementation state.

Known caveat:

- section-aware chunking is heuristic because the source corpus is flattened and structurally lossy

Interpretation:

- this is a dataset limitation, not a blocker
- do not spend this phase trying to “fix” the corpus
- retrieval and evaluation should be built to work despite imperfect structure

## Scope For Phase 03

Keep this phase focused on:

1. first retrieval mode implementation
2. retrieval result normalization
3. metadata-aware filtering hooks
4. smoke tests for retrieval behavior

This phase should produce a usable retrieval layer, not a full answer-generation system.

## Recommended Retrieval Order

Implement in this order:

1. lexical or FTS retrieval over the existing LanceDB table
2. normalized retrieval result objects
3. metadata-aware filtering
4. optionally dense retrieval scaffolding if it fits cleanly after the above

Reason:

- lexical retrieval is likely the fastest way to exercise the end-to-end retrieval path on SEC filings
- it gives immediate signal on company names, terms, and exact-topic matches
- it keeps Phase 03 bounded while preserving the ability to compare dense, lexical, and hybrid later

If LanceDB’s practical surface makes dense retrieval easier to stand up first, that is acceptable, but do not let the phase sprawl.

## Required Outputs

### 1. First retrieval mode

Implement one real retrieval path over `filing_chunks`.

Requirements:

- accept a natural-language query
- retrieve top-k chunk candidates
- preserve chunk metadata in results
- keep implementation local and reproducible

Preferred first mode:

- lexical or FTS retrieval

### 2. Retrieval result normalization

Define a common retrieval result format so later dense, hybrid, and reranked paths can plug into the same downstream interface.

Include at minimum:

- `chunk_id`
- `filing_id`
- `ticker`
- `form_type`
- `filing_date`
- `section`
- `section_path`
- `text`
- raw score
- retrieval mode
- rank

### 3. Metadata-aware filtering hooks

Add the ability to support direct filters later, even if the first pass is simple.

Examples:

- ticker filter
- form type filter
- date constraints

This can begin as a structured filter object or thin query-preparation layer.

### 4. Retrieval smoke tests

Add lightweight verification that retrieval works and returns plausible results.

This does not need to be a full eval harness yet.

Useful examples:

- company-specific query
- risk-factor query
- revenue or outlook query

## Nice-To-Have, But Not Required

- deterministic query analysis for company and date extraction
- a sample retrieval CLI command
- dense retrieval scaffolding if it fits naturally
- early support for comparing two retrieval modes behind a common interface

## Explicit Non-Goals

Do not spend this phase on:

- full answer prompt assembly
- final one-call answer generation
- reranking unless it is trivial to stub
- full evaluation harness
- `chonkie` integration
- UI work

## Suggested Execution Order

1. inspect the current LanceDB table and schema
2. implement a retrieval module with a normalized result shape
3. add a CLI or script for running retrieval queries
4. add filter support to the retrieval path
5. run a few smoke-test queries and capture outputs
6. update docs and handoff notes

## Documentation Updates Required

At the end of Phase 03:

- update `IMPLEMENTATION_KANBAN.md`
- write `PHASE_03_HANDOFF.md`
- update `README.md` with new runnable retrieval commands
- update `LIMITATIONS.md` if new caveats appear
- update `DECISIONS.md` only if a material design choice changes

## Definition Of Done

Phase 03 is done when:

- the repo has at least one working retrieval mode over LanceDB
- retrieval results are normalized into a reusable format
- the retrieval path preserves metadata needed downstream
- simple retrieval smoke tests succeed

## Phase 04 Preview

The next phase should likely focus on:

- a second retrieval mode
- query expansion
- hybrid retrieval
- early evaluation scaffolding
