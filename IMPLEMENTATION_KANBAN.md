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
- a fast reviewer flow: install, restore, demo

Current portability path:

- primary reviewer path uses a GitHub Release archive containing `data/lancedb/` plus `artifacts/dense_index_metadata.json`
- maintainers can still regenerate lexical and dense retrieval artifacts locally with `uv run eliza-rag-load-chunks` and `uv run eliza-rag-build-dense-index`
- `uv run eliza-rag-storage package-archive` is the publisher step that turns the current retrieval state into the demo artifact

## Active Phase

### `done` Phase 10: Final Demo Lock, Narrative Cleanup, And Reviewer Packaging

Goal:

- turn the existing implementation and saved artifact set into a cleaner reviewer-facing demo package

Why now:

- the repo already has the core retrieval, answer, and eval layers needed for a credible demo
- the main remaining gap is presentation clarity rather than missing capability
- reviewer and maintainer documentation had drifted together too heavily in the top-level README

Phase 10 deliverables:

- rewrite `README.md` around the clone-to-demo reviewer journey
- add `ARCHITECTURE.md` as a compact live-walkthrough document
- tighten the evaluation story around `eval/provider_eval_visualization_judged.png`
- separate reviewer-facing entry docs from deeper eval detail and historical phase records
- preserve the distinction between raw artifacts, judged overlays, and read-only reports

Current implementation state:

- the top-level README is now reviewer-first and shorter
- the prior top-level README was preserved under `.internal_docs/README_DEPRECATED.md`
- `ARCHITECTURE.md` now explains the pipeline in plain language
- the judged visualization is now framed as a discussion aid layered over saved raw evidence
- supporting docs now separate:
  - reviewer usage
  - compact architecture explanation
  - eval detail
  - historical handoff records
- the repo should now be treated as presentation-ready unless a later pass finds concrete reviewer-friction issues

### `done` Phase 06C: Metadata-Aware Query Targeting And Coverage-Preserving Retrieval

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
- the release-archive demo flow is now implemented so reviewers can restore prebuilt retrieval artifacts instead of rebuilding LanceDB state locally during the demo setup

### `done` Phase 07: Stabilization, Evaluation Harness, And Modular Provider Boundaries

Goal:

- freeze the current demo path before broad modularization
- make release artifacts more traceable
- extract clean interfaces so alternate embedding and reranking models can be tested without destabilizing the CLI flow

Why now:

- the repo already has a credible reviewer and demo path
- the main risk has shifted from missing features to regressions during refactor
- provider experimentation is now more valuable than another broad architecture phase, but only if it happens behind measurable interfaces

Phase 07 deliverables:

- create a small golden evaluation set with expected company coverage and contamination rules
- emit a build manifest that records chunking, embedding, reranker, and artifact identity together
- add an evaluation runner that saves structured outputs for baseline and candidate runs
- extract explicit interfaces for embedders, rerankers, query analyzers, retrievers, and answer backends
- keep deterministic query analysis as the default while provider experiments focus first on embeddings and rerankers

Current implementation state:

- `targeted_hybrid + BGE rerank` is the current recommended retrieval path for named-company comparison prompts
- the release-archive reviewer flow is implemented and should remain the primary demo contract during this phase
- the code/config default dense embedder is Snowflake, but the currently committed local dense artifact snapshot still reports `hashed_v1`
- Phase 07 cleanup is complete:
  - `eliza-rag-eval` now accepts `bge-reranker-base`
  - the eval CLI surface now matches the retrieval and answer CLIs for reranker selection
  - answer backend typing now uses the shared `AnswerBackend` contract cleanly
  - the docs now distinguish the default Snowflake path from the current committed `hashed_v1` local artifact snapshot
  - implementation handoff is captured in `.internal_docs/PHASE_07_CLEANUP_HANDOFF.md`
- Phase 07A is complete:
  - committed golden eval set at `eval/golden_queries.json`
  - bounded eval runner available as `uv run eliza-rag-eval`
  - build manifest emitted to `artifacts/build_manifest.json`
  - baseline retrieval-only eval saved at `eval/baseline_targeted_hybrid_retrieval.json`
  - dense query encoding now follows saved dense-index metadata rather than current config defaults
- Phase 07C is complete:
  - named embedder selections now expose default `snowflake-arctic-embed-xs`, retained fallback `hashed_v1`, and alternate `bge-m3`
  - named reranker selections now expose baseline `bge-reranker-v2-m3` and alternate `bge-reranker-base`
  - `uv run eliza-rag-build-dense-index --embedder ...` now supports explicit side-by-side alternate dense builds
  - README comparison commands now document baseline versus alternate provider runs without changing defaults
- the next coding pass should run bounded provider comparisons against the committed golden eval set before any default recommendation changes

### `done` Phase 08: Evidence-Driven Provider Evaluation And Scoring Hardening

Goal:

- turn the prepared Phase 07 experiment surface into decision-quality evidence
- harden eval scoring so future default changes are justified by saved artifacts rather than wiring claims

Why now:

- Phase 07 completed the infrastructure needed for bounded provider comparisons
- the repo still lacks saved evidence that the alternate embedder or alternate reranker is better than baseline
- current eval scoring is still too shallow to support a strong default-change decision

Phase 08 deliverables:

- save a baseline provider-comparison eval artifact using the current recommended path
- save an alternate-embedder-only eval artifact
- save an alternate-reranker-only eval artifact
- record exact commands and manifest linkage for each saved run
- extend scoring beyond ticker coverage and comparison placeholders
- decide, after those runs, whether the committed local dense artifact baseline should remain `hashed_v1` or be refreshed to Snowflake

Current implementation state:

- saved provider-comparison artifacts now exist for the bounded runs that actually completed locally:
  - Snowflake embedder + `bge-reranker-v2-m3` at `eval/provider_baseline_snowflake_bge_v2_m3.json`
  - `hashed_v1` embedder + `bge-reranker-v2-m3` at `eval/provider_hashed_v1_bge_v2_m3.json`
  - Snowflake embedder + `bge-reranker-base` at `eval/provider_snowflake_bge_reranker_base.json`
- per-run manifest linkage now exists for those saved artifacts under `artifacts/build_manifest.provider_*.json`
- eval scoring is no longer placeholder-level:
  - the runner now saves explicit `pass`, `partial_pass`, and `fail` outcomes
  - contamination observations are recorded directly in the eval artifact
  - citation-quality and answer-usefulness scoring are present as conditional answer-level fields and remain `not_evaluated` when answers are not included
- current evidence on the golden slice favors Snowflake over the committed local `hashed_v1` baseline:
  - Snowflake + `bge-reranker-v2-m3`: `4 pass / 1 partial_pass / 1 fail`
  - `hashed_v1` + `bge-reranker-v2-m3`: `3 pass / 3 partial_pass / 0 fail`
  - interpretation: `hashed_v1` avoids the outright fail on the broad bank-sector prompt, but does so with materially more contamination
- current evidence does not show a meaningful reranker win for `bge-reranker-base` over `bge-reranker-v2-m3` on this bounded slice:
  - Snowflake + `bge-reranker-base`: `4 pass / 1 partial_pass / 1 fail`
- the attempted `bge-m3` embedder comparison was abandoned for this phase because the local rebuild cost was too high relative to the bounded evidence goal
- the current recommendation for named-company comparison prompts remains `targeted_hybrid + bge-reranker-v2-m3`
- the committed local dense artifact baseline should remain `hashed_v1` for now:
  - Snowflake evidence is better, but the repo has not yet refreshed the reviewer-facing release artifact contract to a published Snowflake archive
- reviewer-facing artifact hygiene needs to stay explicit:
  - GitHub Release archives remain the intended large retrieval artifact source for reviewers
  - local experiment tables and per-run manifests should remain separate from the release-path baseline

### `done` Phase 09: Answer-Level Evaluation And Artifact-Driven Visualization

Goal:

- add bounded answer-level evaluation on top of the saved Phase 08 retrieval evidence layer
- add a small visualization or reporting path that reads directly from saved eval artifacts

Why now:

- Phase 08 established stronger retrieval-quality evidence and saved provider artifacts
- the main remaining uncertainty is answer quality, not whether provider evidence can be saved
- later review and recommendation changes will be easier if the repo can inspect saved artifacts visually without depending on local transient state

Phase 09 deliverables:

- save at least one answer-included eval artifact for the current recommended provider path
- add bounded structured answer-level judging
- keep retrieval-level and answer-level scoring distinct in the saved artifact shape
- add a small visualization or reporting path driven directly from saved `eval/*.json` artifacts

Current implementation state:

- the answer-included baseline artifact now exists at `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`
- the answer-included baseline manifest now exists at `artifacts/build_manifest.provider_baseline_snowflake_bge_v2_m3_answer.json`
- additional answer-included comparison artifacts now exist at:
  - `eval/provider_hashed_v1_bge_v2_m3_answer.json`
  - `eval/provider_hashed_v1_bge_reranker_base_answer.json`
  - `eval/provider_snowflake_bge_reranker_base_answer.json`
- the answer-judging layer is now quantitative and OpenRouter-backed:
  - method: `llm_judge_openrouter_quantitative`
  - rubric saved at `eval/answer_judging_rubric.md`
  - default model in the current environment: `z-ai/glm-5`
  - dimensions:
    - groundedness
    - citation quality
    - usefulness
    - comparison completeness
    - uncertainty handling
  - each dimension receives a `0-5` score
  - overall answer score is a weighted aggregate over the atomic dimensions
- judged overlays now exist at:
  - `eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json`
  - `eval/provider_hashed_v1_bge_v2_m3_answer_judged.json`
  - `eval/provider_hashed_v1_bge_reranker_base_answer_judged.json`
  - `eval/provider_snowflake_bge_reranker_base_answer_judged.json`
- the current judged answer summaries are:
  - baseline Snowflake + `bge-reranker-v2-m3`: `1 pass / 2 partial_pass / 3 fail`
  - `hashed_v1` + `bge-reranker-base`: `0 pass / 4 partial_pass / 2 fail`
  - `hashed_v1` + `bge-reranker-v2-m3`: `0 pass / 2 partial_pass / 4 fail`
  - Snowflake + `bge-reranker-base`: `0 pass / 2 partial_pass / 4 fail`
- the expanded raw answer-only matrix currently shows:
  - baseline Snowflake + `bge-reranker-v2-m3`: `3 pass / 2 partial_pass / 1 fail`
  - `hashed_v1` + `bge-reranker-base`: `2 pass / 2 partial_pass / 2 fail`
  - `hashed_v1` + `bge-reranker-v2-m3`: `3 pass / 3 partial_pass / 0 fail`
  - Snowflake + `bge-reranker-base`: `3 pass / 2 partial_pass / 1 fail`
- the repo now has a read-only report path:
  - CLI: `uv run eliza-rag-eval-report`
  - generated artifact: `eval/provider_eval_report.md`
- judged-only report artifact: `eval/provider_eval_report_judged.md`
- the repo still builds on the saved retrieval-quality artifact set from Phase 08:
  - `eval/provider_baseline_snowflake_bge_v2_m3.json`
  - `eval/provider_hashed_v1_bge_v2_m3.json`
  - `eval/provider_snowflake_bge_reranker_base.json`
- visualization work should remain artifact-driven:
  - read saved eval JSON
  - do not query live LanceDB state directly
  - do not replace the raw evidence artifacts with a secondary analytics truth

### `done` Phase 07A: Golden Eval Set And Build Manifest

Goal:

- freeze a small regression baseline before broader modularization
- make release and retrieval artifacts more traceable

Completed deliverables:

- committed golden evaluation set with required comparison, single-company, time-bounded, and sector-style prompts
- machine-readable build manifest covering chunking, table names, dense-index contract, reranker settings, and artifact paths
- bounded eval runner that saves config, retrieved tickers, retrieved chunk ids, optional answer fields, and scoring placeholders
- saved baseline output for the current local retrieval state
- tests for the new eval and manifest shapes

Important implementation note:

- the first real eval run exposed a bug where dense query encoding followed current settings instead of the saved dense metadata artifact
- that mismatch is now fixed and should be treated as part of the Phase 07A stabilization work, not as separate later cleanup

### `done` Phase 07C: Provider Experiment Prep

Goal:

- make one alternate embedder and one alternate reranker selectable behind the extracted provider seams
- document exact comparison commands without flipping the default recommendation

Completed deliverables:

- explicit named embedder aliases for the baseline Snowflake path and alternate `bge-m3` path
- explicit alternate reranker adapter `bge-reranker-base` beside the baseline `bge-reranker-v2-m3`
- dense-index build CLI support for explicit embedder selection plus alternate artifact naming
- focused provider-selection tests and README command documentation

Important implementation note:

- this phase wires the comparison surface only
- it does not yet claim that the alternate embedder or reranker outperforms the current baseline

### `done` Phase 07 Cleanup: Congruence, Artifact Consistency, And Interface Hygiene

Goal:

- remove the remaining mismatches between CLI claims, saved artifacts, interface documentation, and current code state

Completed deliverables:

- eval CLI reranker surface expanded to include `bge-reranker-base`
- eval CLI test coverage added for the alternate reranker selection
- duplicate local answer-backend protocol removed in favor of the shared `AnswerBackend` contract
- docs updated to distinguish the Snowflake code/config default from the currently committed local `hashed_v1` dense artifact snapshot
- cleanup handoff recorded in `.internal_docs/PHASE_07_CLEANUP_HANDOFF.md`

Important implementation note:

- this cleanup pass did not rebuild dense artifacts
- it resolved the artifact mismatch by making the saved local artifact state explicit in the docs and handoff records

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

- the repo now declares the GitHub Release archive restore flow as the supported reviewer mode
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

### `done` Add reranking stage

Expected output:

- rerank top retrieved chunks
- configurable reranker on or off

Current state:

- reranking is implemented in retrieval and answer flows
- `--rerank` exposes reranking explicitly at the CLI layer
- the repo supports both `heuristic` and `bge-reranker-v2-m3`, with BGE as the recommended path

### `todo` Support reranking in eval matrix

Expected output:

- `none` vs `cross_encoder` or equivalent

Current state:

- the next evaluation harness should preserve direct comparison between reranked and non-reranked runs
- reranking should now be treated as one controlled axis within the broader golden-set regression harness

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

### `in_progress` Create gold evaluation question set

Expected output:

- 12 to 20 representative questions
- expected entities, periods, and themes

Current state:

- the repo now has several known-critical demo questions that should seed the golden set
- the next step is to formalize them into a committed evaluation artifact with explicit pass/fail expectations

### `in_progress` Define experiment matrix

Expected output:

- chunking strategy arms
- retrieval mode arms
- query rewrite arms
- reranking arms

Current state:

- the immediate matrix should stay intentionally narrow
- first compare the current default path against no-behavior-change modularization baselines and one-at-a-time provider swaps

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
4. Retrieval and answer path implementation
5. Release-archive reviewer flow
6. Golden eval set and build manifest
7. No-behavior-change interface extraction
8. One-at-a-time provider experiments

## Track 11: Modularization

### `todo` Add build manifest for retrieval artifacts

Expected output:

- artifact metadata that records chunking settings, embedding model, reranker, and source artifact names together
- a portable record that can be shipped with release archives and used in evaluation reports

### `done` Extract embedder interface

Expected output:

- stable internal contract for embedding providers
- current Snowflake implementation retained as the default adapter
- room for one alternate embedding provider without CLI churn

Status:

- added `src/eliza_rag/interfaces.py` with a shared `Embedder` contract
- moved current embedding behavior behind resolver-selected adapters in `src/eliza_rag/embeddings.py`
- kept existing dense-index build and query behavior stable

### `done` Extract reranker interface

Expected output:

- stable internal contract for reranking providers
- current heuristic and BGE rerankers moved behind the same interface

Status:

- added reranker adapters and `build_reranker(...)` dispatch in `src/eliza_rag/retrieval.py`
- preserved the existing heuristic and transformer reranker behavior behind one internal seam

### `done` Extract query analyzer and retriever interfaces

Expected output:

- deterministic query analysis preserved as the default implementation
- retrieval orchestration separated from provider-specific retrieval logic

Status:

- moved deterministic query analysis behind `build_query_analyzer(...)`
- moved retrieval mode dispatch behind `build_retriever(...)`
- preserved the current CLI retrieval behavior and default retrieval path

### `done` Extract answer backend interface cleanly from answer orchestration

Expected output:

- prompt assembly and citation enforcement remain in the core pipeline
- backend transport details move behind explicit backend clients

Status:

- answer backends now implement the shared `AnswerBackend` protocol
- prompt assembly, response parsing, and citation enforcement remain in core orchestration

## Immediate Next Tasks

### `in_progress` Run bounded provider experiments behind the extracted interfaces

Why first:

- the repo now has a frozen eval baseline and explicit provider seams, so one-at-a-time provider comparison is the next highest-signal step

### `todo` Compare the baseline Snowflake embedder against `bge-m3`

### `todo` Compare the baseline `bge-reranker-v2-m3` reranker against `bge-reranker-base`

### `todo` Extend eval scoring beyond the current coverage placeholders once the first provider comparisons are recorded
### `todo` Compare baseline hybrid retrieval against reranked retrieval on representative questions

### `todo` Decide whether reranked retrieval becomes the recommended demo path

### `todo` Write a Phase 06B handoff with results and recommendation
