# Implementation Kanban

## Status Key

- `todo`
- `in_progress`
- `blocked`
- `done`

## Current Build Goal

Deliver a working SEC filings RAG demo with:

- local corpus ingestion
- chunk-level metadata duplication
- LanceDB-backed retrieval
- evaluation across chunking and retrieval strategies
- one final LLM call for answer generation
- a fast local reviewer flow: install, build, demo

Current portability path:

- explicit local-build reviewer flow
- lexical retrieval requires the `filing_chunks` table built by `uv run eliza-rag-load-chunks`
- dense and hybrid retrieval additionally require `filing_chunks_dense` plus `artifacts/dense_index_metadata.json` built by `uv run eliza-rag-build-dense-index`

## Active Phase

### `in_progress` Phase 06C: Metadata-Aware Query Targeting And Coverage-Preserving Retrieval

Goal:

- improve answer usefulness by preserving named-entity coverage before final reranking on multi-company and comparison-style questions

Why now:

- live testing has already been completed
- answer-path bugs were fixed during post-test stabilization
- Phase 06B confirmed that stronger dense embeddings plus stronger reranking were still not enough to solve the main comparison-style retrieval failure
- the main remaining risk is retrieval quality on comparison-style and multi-company questions where entity coverage collapses

Phase 06C deliverables:

- add deterministic company and ticker targeting for structured query analysis
- add an optional coverage-preserving retrieval path before reranking
- compare baseline `hybrid + BGE rerank` against `targeted_hybrid + BGE rerank`
- decide whether the new path is strong enough to justify final demo evaluation or whether another bounded retrieval step is needed

Current implementation state:

- explicit reranking is wired into retrieval and answer flows, with `BAAI/bge-reranker-v2-m3` as the default reranker
- the default dense embedding model is `Snowflake/snowflake-arctic-embed-xs`
- an explicit `targeted_hybrid` retrieval mode now exists for coverage-preserving retrieval before reranking
- Phase 06C evaluation shows `targeted_hybrid` materially improves top-k purity when entity detection succeeds
- the follow-up company-detection pass now adds stronger deterministic alias normalization for metadata-backed company names, including prompt forms such as `JPMorgan`, `JPMorgan Chase`, and `Bank of America`
- the re-run comparison matrix now shows full named-company coverage for the main Apple/Tesla/JPMorgan blocker under `targeted_hybrid + BGE rerank`
- current recommendation is to move to lightweight final evaluation and demo-lock preparation, using `targeted_hybrid` as the preferred retrieval mode for named-company comparison prompts

## Track 1: Project Setup

### `done` Create initial project structure

Expected output:

- `src/`
- `data/`
- `scripts/`
- `eval/`
- `artifacts/`

### `done` Create environment and dependency manifest

Expected output:

- Python version pinned
- package manager choice documented as `uv`
- dependencies for LanceDB, embeddings, reranking, eval, and CLI execution

### `done` Create `.env.example` and config module

Expected output:

- API key placeholders
- model configuration fields
- retrieval and chunking defaults

## Track 2: Corpus Ingestion

### `done` Unpack and inspect corpus

Expected output:

- extracted corpus directory
- manifest inspection notes
- filename pattern validation

### `done` Implement filing metadata normalization

Expected output:

- parser for filename metadata
- optional manifest merge logic
- stable `filing_id` generation

### `done` Implement filing-level normalized record creation

Expected output:

- one normalized record per filing
- source path and raw text retained

Implementation notes:

- corpus inspection command verified against 246 local filings
- `manifest.json` aligns with discovered files
- current stable `filing_id` uses the filename stem

## Track 3: Chunking

### `done` Define chunk record schema

Expected output:

- chunk schema with:
  - `chunk_id`
  - `filing_id`
  - duplicated filing metadata for filtering
  - optional section metadata
  - `chunk_index`
  - chunk text

### `done` Implement baseline paragraph-aware chunker

Expected output:

- header carry-forward
- configurable size and overlap
- section detection where feasible

Current state:

- baseline chunker normalizes noisy filing text after the metadata header
- chunking is paragraph-aware with sentence fallback for oversized blocks
- chunk rows preserve deterministic ordering, overlap, and section metadata

### `todo` Integrate `chonkie` as chunking experiment driver

Expected output:

- common interface for multiple chunking strategies
- ability to generate chunk sets for comparison

### `done` Materialize chunk records with duplicated metadata

Expected output:

- chunk rows with:
  - `chunk_id`
  - `filing_id`
  - `ticker`
  - `company_name`
  - `form_type`
  - `filing_date`
  - `fiscal_period`
  - `section`
  - `chunk_index`
  - chunk text

Current state:

- chunk IDs remain deterministic via `filing_id::chunk-XXXX`
- materialization duplicates filing metadata onto each chunk row
- optional JSONL artifact path exists for local inspection before indexing

## Track 4: Retrieval

### `done` Create LanceDB schema and table initialization

Expected output:

- chunk table design
- metadata fields indexed or queryable
- ingestion path into LanceDB

Current state:

- local LanceDB database path defaults to `data/lancedb`
- chunk rows are loaded into the `filing_chunks` table with overwrite semantics
- CLI smoke path reports persisted row counts after loading

### `done` Implement dense retrieval

Expected output:

- embedding generation
- vector search over chunk rows
- metadata-aware filtering

Current state:

- dense retrieval is implemented over the `filing_chunks_dense` LanceDB table
- the repo provides an explicit `eliza-rag-build-dense-index` command to build or refresh dense vectors
- dense retrieval reuses the same normalized result contract and filter shape as lexical retrieval

### `done` Implement lexical retrieval

Expected output:

- LanceDB full-text or BM25-style query path
- metadata-aware filtering

Current state:

- lexical retrieval is implemented with LanceDB FTS over the chunk `text` column
- retrieval setup lazily creates the required FTS and scalar indices on the local table
- CLI query path supports ticker, form type, and filing-date filters

### `done` Implement hybrid retrieval

Expected output:

- fused retrieval path
- mode switch for `dense`, `lexical`, `hybrid`

Current state:

- hybrid retrieval combines lexical and dense candidates with reciprocal rank fusion
- CLI mode selection now supports `lexical`, `dense`, and `hybrid`

### `done` Implement retrieval result normalization

Expected output:

- common ranked result format across retrieval modes
- chunk IDs, scores, metadata, and text payloads preserved

Current state:

- normalized retrieval results include chunk and filing IDs, metadata, text, raw score, retrieval mode, and rank
- result objects are shared by the retrieval module and CLI JSON output

### `done` Add retrieval smoke tests

Expected output:

- lightweight checks for company-specific, risk, and revenue-style queries

Current state:

- pytest smoke tests cover result normalization, filter SQL generation, and filtered lexical retrieval behavior
- local CLI smoke query is verified against the existing `filing_chunks` table

### `in_progress` Add configurable reranking stage

Expected output:

- bounded reranking over the initial retrieval candidate pool
- explicit CLI and config controls for reranking
- result metadata that preserves the source retrieval mode after reranking

Current state:

- reranking can be enabled per command with `--rerank`
- the repo now supports both a fallback `heuristic` reranker and a model-backed `bge-reranker-v2-m3` reranker
- live runs with Snowflake dense embeddings plus BGE reranking still failed the main multi-company comparison query because the final top-k lost Apple coverage
- reranking alone should not be treated as sufficient mitigation for multi-company questions

### `todo` Add metadata-aware query parsing and coverage-preserving retrieval

Expected output:

- infer likely company/ticker constraints from the user query
- apply metadata-aware filters or candidate balancing before final reranking
- preserve named-entity coverage in multi-company comparison questions

Why this is next:

- live Phase 06B runs showed that stronger embeddings plus a stronger reranker still allowed the candidate set to collapse onto the wrong companies
- the remaining quality gap is now better framed as query understanding and candidate coverage, not just semantic scoring strength

### `done` Make index portability mode explicit and reviewer-safe

Expected output:

- one documented portability mode for reviewers
- explicit rebuild triggers for lexical and dense artifacts
- clear CLI failure guidance when retrieval artifacts are missing

Current state:

- the repo now declares the local-build reviewer flow as the supported portability mode
- lexical retrieval fails with a direct `uv run eliza-rag-load-chunks` instruction when the chunk table is missing
- dense and hybrid retrieval fail with a direct `uv run eliza-rag-build-dense-index` instruction when dense artifacts are missing
- retrieval JSON status now reports lexical table presence plus dense table and metadata presence

## Track 5: Query Handling

### `done` Implement deterministic query analysis

Expected output:

- company and ticker detection
- time-range detection
- intent detection for risks, outlook, revenue, regulation, and comparison

Current state:

- a shared structured query object now carries raw query text, lexical text, dense text, expansion terms, and optional derived date bounds
- the current hook performs lightweight year extraction and dense-query expansion scaffolding without rewriting the lexical path aggressively

### `done` Implement metadata-aware query expansion

Expected output:

- structured retrieval inputs
- optional expanded lexical query
- optional retrieval filters

Current state:

- retrieval now runs through a shared query-analysis hook before dispatching by mode

## Track 6: Answer Generation

### `done` Enforce citation-grounded answer contract

Expected output:

- top-level `answer` must include inline citation ids
- unknown citation ids fail fast
- malformed answer payloads fail clearly

Current state:

- parser now enforces inline citation ids such as `[C1]` in the main answer text
- citations referenced by both `answer` and `findings` must exist in the prompt context
- malformed JSON and empty `findings` are covered by deterministic unit tests

### `done` Support explicit answer backend configuration

Expected output:

- provider selection for hosted and local-compatible backends
- configurable base URL, API key, and model
- docs that state the supported protocol honestly

Current state:

- answer generation now uses explicit `ELIZA_RAG_LLM_PROVIDER`, `ELIZA_RAG_LLM_BASE_URL`, `ELIZA_RAG_LLM_API_KEY`, and `ELIZA_RAG_LLM_MODEL` settings
- supported modes are hosted OpenAI, hosted OpenRouter, user-provided OpenAI-compatible `/v1/responses` servers, and a repo-supported local fallback via Ollama
- repo-supported local startup is exposed through `eliza-rag-local-llm prepare|start|status`
- the `local_ollama` answer path now auto-checks runtime readiness and fails clearly on missing runtime or missing model state
- offline tests cover provider selection, provider error surfacing, and local runtime management behavior
- expansion terms are currently modest and deterministic so later phases can extend them without redesigning the retrieval interface

## Track 6: Reranking

### `in_progress` Add reranking stage

Expected output:

- rerank top retrieved chunks
- configurable reranker on or off

Current state:

- Phase 06B is the active project path
- reranking is the chosen next retrieval-quality improvement
- implementation remains to be completed

### `in_progress` Support reranking in eval matrix

Expected output:

- `none` vs `cross_encoder` or equivalent

Current state:

- Phase 06B requires direct comparison between current baseline retrieval and reranked retrieval
- the evaluation matrix should stay bounded around the reranking decision rather than expanding broadly

## Track 7: Answer Generation

### `done` Create final answer prompt template

Expected output:

- structured instructions
- grounded answer constraints
- citation format
- uncertainty behavior

Current state:

- the final prompt template is saved in `prompts/final_answer_prompt.txt`
- the template requires strict JSON output, explicit uncertainty language, and chunk citation ids
- prompt iteration notes are captured in `PROMPT_ITERATION_LOG.md`

### `done` Implement single-call answer pipeline

Expected output:

- retrieve context
- format prompt
- execute one final LLM call
- return structured answer plus citations

Current state:

- `eliza-rag-answer` now owns prompt assembly and final answer generation
- the answer path retrieves chunks first, injects them into the saved prompt template, and makes one final OpenAI Responses API call
- answer payloads include summary, full answer text, supported findings, uncertainty, and traceable chunk citations

## Track 8: Evaluation

### `todo` Create gold evaluation question set

Expected output:

- 12 to 20 representative questions
- expected entities, periods, and themes

### `todo` Define experiment matrix

Expected output:

- chunking strategy arms
- retrieval mode arms
- query rewrite arms
- reranking arms

### `todo` Implement retrieval evaluation

Expected output:

- Recall@k
- MRR or nDCG
- metadata hit rate

### `todo` Implement end-to-end answer evaluation

Expected output:

- groundedness scoring
- completeness scoring
- comparative usefulness scoring
- citation quality scoring

### `todo` Select final pipeline from eval results

Expected output:

- chosen default config
- short justification for why it won

## Track 9: Demo UX

### `done` Build simple input interface

Expected output:

- CLI or minimal app entrypoint
- question input
- answer output

Current state:

- the reviewer-facing CLI is `uv run eliza-rag-answer "..."` with optional `--json` output
- retrieval-only CLI paths remain available for inspection and debugging

### `done` Add example request ready to execute

Expected output:

- one reproducible example command

Current state:

- `README.md` now includes end-to-end example commands for both terminal and JSON output modes

## Track 10: Documentation

### `done` Write README

Expected output:

- setup
- indexing
- running a query
- running eval
- clear reviewer flow for quick local demo execution

Current state:

- `README.md` now documents the end-to-end answer command, API-key requirement, and reviewer demo flow

### `done` Create prompt iteration log

Expected output:

- prompt revisions
- why each change was made

Current state:

- `PROMPT_ITERATION_LOG.md` records the first prompt version and the rationale for strict JSON plus citation rules

### `todo` Summarize evaluation findings

Expected output:

- final notes for submission
- explicit caveats and limitations summary aligned with `LIMITATIONS.md`

## Suggested Execution Order

1. Project setup
2. Corpus ingestion
3. Baseline chunking
4. LanceDB ingestion and dense retrieval
5. Lexical and hybrid retrieval
6. Prompt template and one-call answer path
7. Eval set and experiment matrix
8. Reranking
9. Documentation and final packaging

## Immediate Next Tasks

### `in_progress` Implement reranking over top retrieval candidates

Why first:

- it is the selected Phase 06B workstream and the highest-leverage retrieval-quality upgrade already identified by the project docs

### `todo` Expose reranking configuration in retrieval and answer commands

### `todo` Compare baseline hybrid retrieval against reranked retrieval on representative questions

### `todo` Decide whether reranked retrieval becomes the recommended demo path

### `todo` Write a Phase 06B handoff with results and recommendation
