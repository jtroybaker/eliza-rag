# Phase 02 Kickoff

## Phase Goal

Build the first retrieval-ready data layer for the SEC filings RAG demo.

This phase should convert normalized filing records into chunk records and persist those chunk records into a local LanceDB table so later phases can add retrieval, reranking, and answer generation without revisiting ingestion fundamentals.

## Phase 01 Assessment

Phase 01 was successful and created a clean base to build on.

Completed and verified:

- Python project scaffold exists
- `uv`-first setup is in place
- `.env.example` and config module exist
- corpus extraction and inspection path exists
- `manifest.json` handling exists
- filing-level normalization exists
- chunk schema exists
- inspection artifact was generated successfully

Important verified corpus facts from Phase 01:

- filings discovered: `246`
- manifest count: `246`
- filename parse failures: `0`
- date range: `2015-02-27` to `2026-02-19`
- form counts:
  - `10-K`: `89`
  - `10-Q`: `157`

Conclusion:

- the repo is ready for chunk generation and LanceDB ingestion
- no redesign is needed before proceeding

## Read First

Before changing code, read:

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `PHASE_01_HANDOFF.md`
- the chunking and retrieval sections of `HIGH_LEVEL_PLAN.md`

Use the repo files as the source of truth rather than prior chat context.

## Scope For Phase 02

Keep this phase tightly scoped to:

1. baseline chunking
2. chunk materialization
3. LanceDB table initialization and loading

Do not expand into full retrieval evaluation, answer generation, or prompt tuning yet.

## Required Outputs

### 1. Baseline paragraph-aware chunking

Implement a baseline chunker that is good enough for the first retrieval experiments.

Requirements:

- paragraph-aware chunking
- configurable target chunk size
- configurable overlap
- preserve useful local context
- attempt section-aware behavior where it is easy and reliable
- produce stable chunk ordering within each filing

Recommended default:

- target size roughly in the range already described in `HIGH_LEVEL_PLAN.md`
- header carry-forward when feasible

This should be the default baseline, not the final chunking system.

### 2. Chunk materialization

Materialize chunk rows from normalized filings using the existing chunk schema.

Each chunk should include:

- `chunk_id`
- `filing_id`
- duplicated filterable metadata:
  - `ticker`
  - `company_name`
  - `form_type`
  - `filing_date`
  - `fiscal_period`
- chunk-local metadata:
  - `section`
  - `chunk_index`
- chunk text

Expectations:

- chunk IDs should be deterministic
- metadata duplication should be explicit and consistent
- output should be easy to inspect before loading into LanceDB

### 3. LanceDB table setup

Create the first local LanceDB integration around chunk records.

Requirements:

- define a table schema aligned with chunk materialization
- support writing chunk rows into a local database path
- keep artifact and database paths predictable
- preserve enough structure to support later filtering and hybrid retrieval work

This phase does not need to implement full query APIs yet unless the setup naturally includes a minimal smoke test.

## Nice-To-Have, But Not Required

- minimal section detection heuristics
- a small local inspection command for chunk output
- a LanceDB smoke test that confirms rows load correctly
- a first pass at storing fields needed later for lexical and hybrid retrieval

## Explicit Non-Goals

Do not spend this phase on:

- embedding generation
- dense retrieval implementation
- lexical or hybrid retrieval implementation
- reranking
- full eval harness
- answer prompt design
- UI work

Those belong to later phases.

## Suggested Execution Order

1. inspect the existing filing and chunk models
2. implement baseline chunking logic
3. materialize chunk records from a small sample and inspect them
4. scale chunk materialization to the full corpus
5. add LanceDB initialization and ingestion
6. run a smoke test that confirms chunk rows are persisted locally
7. update the kanban and handoff notes

## Recommended Commands

Start from:

```bash
uv sync
```

Useful verification commands:

```bash
uv run --no-sync python -m compileall src scripts
uv run eliza-rag-inspect-corpus --write-artifact
```

If new CLI entry points are added in this phase, document them in `README.md`.

## Documentation Updates Required

At the end of Phase 02:

- update `IMPLEMENTATION_KANBAN.md`
- write a `PHASE_02_HANDOFF.md`
- update `README.md` if new runnable commands exist
- update `DECISIONS.md` only if a real design choice changes

## Definition Of Done

Phase 02 is done when:

- normalized filings can be turned into deterministic chunk records
- chunk rows carry duplicated filterable metadata
- chunk rows can be written into a local LanceDB table
- the repo is ready for Phase 03 to implement the first retrieval path

## Phase 03 Preview

The next phase should likely focus on:

- first retrieval mode implementation
- retrieval result normalization
- metadata-aware filtering
- initial retrieval smoke tests
