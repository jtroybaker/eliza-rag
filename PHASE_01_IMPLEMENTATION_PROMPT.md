# Phase 01 Implementation Prompt

You are starting implementation for the SEC filings RAG demo in this repository.

## Read First

Before making changes, read only these files:

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- the relevant sections of `HIGH_LEVEL_PLAN.md`

Do not assume prior chat context is available. The repository files are the source of truth.

## Objective For This Phase

Begin implementation with the smallest useful vertical slice that unlocks the rest of the project.

Focus on:

1. project scaffold
2. dependency baseline
3. corpus extraction and inspection
4. normalized filing schema
5. chunk schema design

Do not try to build the entire system in one pass.

## Requirements Already Decided

- Use `LanceDB` as the main local retrieval engine.
- Keep one normalized filing record per filing.
- Create many chunk records per filing.
- Duplicate lightweight filterable metadata onto each chunk.
- Use `chonkie` as the driver for chunking experiments later.
- The final answer path must use one LLM API call, but that is not the focus of this phase.

## Phase 01 Deliverables

Implement the following:

### 1. Project structure

Create a practical repo scaffold such as:

- `src/`
- `src/eliza_rag/`
- `scripts/`
- `data/`
- `eval/`
- `artifacts/`

Adjust naming if needed, but keep it simple.

### 2. Environment baseline

Add the minimum dependency and configuration setup needed to continue implementation.

This should include:

- Python project manifest
- core dependencies
- `.env.example` if API-bound config is expected later
- a config module or equivalent for local paths and defaults

Prefer a lightweight setup that reviewers can run easily.

### 3. Corpus extraction and inspection

Implement a script or command path that:

- extracts `edgar_corpus.zip`
- inspects whether `manifest.json` exists
- records basic corpus facts needed for implementation

Do not over-engineer this. The purpose is to unblock ingestion.

### 4. Filing metadata normalization

Implement normalized filing parsing that produces one stable filing-level record per source file.

At minimum support:

- `filing_id`
- `ticker`
- `form_type`
- `filing_date`
- `fiscal_period` if available
- `source_path`
- raw text

If `manifest.json` adds useful metadata, merge it carefully.

### 5. Chunk schema definition

Define the chunk record shape even if full chunking is not yet implemented.

It should support:

- `chunk_id`
- `filing_id`
- duplicated metadata fields for filtering
- section metadata where available
- `chunk_index`
- chunk text

## Constraints

- Keep the implementation local and lightweight.
- Avoid unnecessary infrastructure.
- Do not start dense, lexical, or hybrid retrieval yet unless it is trivial to scaffold.
- Do not build the eval harness yet beyond any small schema or folder setup.
- Keep code clear and inspectable.

## Expected Output At End Of Phase

By the end of this phase, the repository should have:

- runnable project scaffolding
- dependency baseline
- extracted corpus or a repeatable extraction script
- normalized filing parsing implemented
- chunk record schema defined
- kanban updated to reflect completed and in-progress work

## Documentation Updates Required

When finished:

- update `IMPLEMENTATION_KANBAN.md`
- update `DECISIONS.md` only if a new decision is made
- update `README` only if setup instructions become clear enough to record now

## Execution Guidance

- Work in small, coherent steps.
- Prefer completing a clean ingestion foundation over touching many unfinished subsystems.
- If a tradeoff is needed, choose the simpler implementation and document it briefly.
- Preserve stable IDs and metadata integrity from the start.

## Definition Of Done

This phase is done when the repo is ready for the next phase to implement:

- baseline chunking
- LanceDB table setup
- first retrieval path
