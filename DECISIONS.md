# Decision Record

## Purpose

This file captures the main technology and design choices for the SEC filings RAG demo, along with the reasoning behind each choice. The goal is to make the system easy to review, easy to run locally, and strong on retrieval accuracy within the assessment timebox.

## Decision: Use LanceDB As The Retrieval Engine

Decision:

- Use `LanceDB` as the primary local retrieval engine for chunk storage, vector search, full-text search, hybrid search, metadata filtering, and reranking integration.

Justification:

- We want to test `dense`, `BM25` or FTS, and `hybrid` retrieval without writing a large amount of infrastructure glue code.
- This is a demo, so low operational overhead matters more than maximum scale.
- `LanceDB` keeps the system local and lightweight while supporting the retrieval APIs we want for eval experiments.
- It reduces implementation time spent on infra and increases time available for chunking, reranking, prompt quality, and evaluation.

## Decision: Use `uv` As The Default Local Runner And Environment Manager

Decision:

- Use `uv` as the default local project workflow for environment creation, dependency sync, and command execution.

Justification:

- It keeps the repo portable and easy to execute on a fresh machine.
- It avoids introducing extra packaging or task-runner layers for a small local demo.
- It provides a clear path for both synced execution (`uv sync`, `uv run ...`) and lightweight script execution (`uv run --no-sync ...`) during early phases.

Why not `SQLite` as the main retrieval engine:

- `SQLite` is still a fine source-of-truth option, but on its own it does not give us an equally convenient vector plus FTS plus hybrid retrieval layer.
- Using `SQLite` would likely push us into extra custom integration work that does not improve answer quality.

Why not other alternatives first:

- `Qdrant` is a strong alternative, but we would still expect slightly more explicit retrieval plumbing for this demo.
- `Weaviate` is capable, but it adds more operational surface area than we want for a short assessment.
- `Milvus Lite` is less attractive here because our eval design explicitly wants a strong lexical plus hybrid comparison path.

## Decision: One Normalized Filing Record, Many Chunk Records

Decision:

- Maintain a normalized logical schema with one filing-level record per source filing and many chunk-level records derived from that filing.

Justification:

- It gives us a stable `filing_id` for provenance, evaluation, and citations.
- It keeps document-level metadata consistent even if chunking strategies change.
- It makes re-indexing and chunk regeneration straightforward.

## Decision: Duplicate Filterable Metadata Onto Each Chunk

Decision:

- Duplicate lightweight, filterable filing metadata onto each chunk row.

Examples:

- `filing_id`
- `ticker`
- `company_name`
- `form_type`
- `filing_date`
- `fiscal_period`
- `section`
- `chunk_index`

Justification:

- Retrieval runs at chunk granularity, not filing granularity.
- Direct chunk-level filtering is simpler and faster than relying on a retrieval-time join.
- Metadata duplication is cheap for this corpus size.
- This design works cleanly with vector, FTS, and hybrid retrieval.

## Decision: Use Chunking Strategy As An Explicit Eval Dimension

Decision:

- Treat chunking as a first-class experimental axis in evaluation.

Default choice:

- paragraph-aware chunking with header carry-forward

Additional approach:

- use `chonkie` as the experimentation driver for quickly comparing chunking strategies under a common interface

Justification:

- Chunking quality directly affects retrieval accuracy and answer grounding.
- SEC filings are long, structured, and section-heavy, so chunking tradeoffs matter materially.
- `chonkie` is useful here as a harness for comparing chunking strategies, not as a single strategy itself.

## Decision: Evaluate Dense, FTS, And Hybrid Retrieval Separately

Decision:

- Include retrieval mode as its own experimental dimension:
  - dense only
  - FTS or BM25 only
  - hybrid

Justification:

- SEC questions often require both semantic matching and exact terminology matching.
- We want the eval to determine whether hybrid retrieval materially improves results rather than assuming it does.
- Treating retrieval mode as a separate axis supports a more disciplined experiment matrix.

## Decision: Use HNSW For Approximate Nearest Neighbor Search

Decision:

- Use an HNSW-based ANN strategy for dense retrieval.

Current Phase 04 implementation detail:

- the LanceDB dense index is currently created as `IVF_HNSW_PQ`

Justification:

- It is a standard, defensible default for small-to-medium local retrieval systems.
- It offers strong recall with low implementation friction.
- More complex ANN schemes are unlikely to improve the demo meaningfully.

Interpretation:

- the architectural intent remains "use a practical HNSW-family ANN path"
- the current implementation should not be described as plain HNSW without noting the `IVF_HNSW_PQ` index type

## Decision: Keep Phase 04 Dense Embeddings Fully Local And Reproducible

Decision:

- Use a deterministic local hashed embedding workflow for the first dense retrieval implementation.
- Store dense vectors in a dedicated `filing_chunks_dense` LanceDB table built from the lexical chunk table.

Justification:

- The repository did not yet carry a local neural embedding dependency or model artifact.
- A deterministic hashed embedding path satisfies the Phase 04 requirement for explicit, reproducible embedding generation without introducing hidden network downloads.
- A dedicated dense table keeps lexical retrieval stable and makes dense-index refresh an explicit command rather than an implicit side effect during query execution.

Tradeoff:

- Retrieval quality is expected to be weaker than a stronger sentence embedding model.
- The follow-on evaluation phases should treat the embedding model as an upgrade point rather than the final dense strategy.

Superseded by later project state:

- this is no longer the default dense retrieval strategy
- `hashed_v1` is retained only as a baseline fallback for comparison and evaluation

## Decision: Use `Snowflake/snowflake-arctic-embed-xs` As The Default Dense Embedding Model

Decision:

- use the Hugging Face repo `Snowflake/snowflake-arctic-embed-xs` as the default dense embedding model

Justification:

- the hashed baseline was useful for a deterministic local starting point, but it was not strong enough for the repo's quality goals
- a real embedding model was needed before judging whether dense and hybrid retrieval quality could support the demo
- this model can still be run locally after dependency install and model download without changing the one-final-call answer contract

Operational note:

- first build now has a real model-download cost
- `hashed_v1` remains available as a deliberate baseline rather than the default path
- the committed local dense artifact snapshot can still lag behind that default, so artifact-driven reporting must distinguish saved on-disk state from config intent

## Decision: Use Reranking In The Strong Candidate Pipeline

Decision:

- Include reranking in the strongest candidate pipeline, especially for multi-company and time-comparison questions.

Preferred approach:

- cross-encoder reranking over the top retrieved candidates

Justification:

- Initial retrieval often finds the right documents but not the best excerpt ordering.
- Reranking is one of the highest-leverage quality improvements for grounded RAG answers.
- It is easier to justify in a demo than more exotic indexing complexity.

Current project state:

- Phase 06B established reranking as a necessary but insufficient retrieval-quality upgrade.
- The project has now moved to Phase 06C, which focuses on metadata-aware query targeting and coverage-preserving retrieval before final demo lock.

## Decision: Use `BAAI/bge-reranker-v2-m3` As The Default Reranker

Decision:

- use `BAAI/bge-reranker-v2-m3` as the default reranker
- retain the deterministic heuristic reranker only as a fallback and evaluation baseline

Justification:

- the heuristic reranker was intentionally lightweight and not strong enough to answer the real quality question
- a proper cross-encoder reranker is a more defensible default for comparison-style retrieval
- this gives the project a real reranking baseline before making larger architectural changes

Observed outcome:

- live testing showed that Snowflake dense embeddings plus BGE reranking still did not solve the main multi-company retrieval failure
- the remaining gap appears to be candidate coverage and query understanding, not merely reranker strength

Follow-on implication:

- metadata-aware query parsing and coverage-preserving candidate selection were the correct next bounded step after Phase 06B
- the follow-up deterministic alias pass strengthened company detection for metadata-backed forms such as `JPMorgan`, `JPMorgan Chase`, and `Bank of America`
- the re-run comparison slice now shows full named-company coverage on the Apple/Tesla/JPMorgan blocker under `targeted_hybrid + BGE rerank`
- the project should now move to lightweight final evaluation and demo-lock preparation rather than another bounded retrieval-quality phase

## Decision: Expose Provider Experiment Selection Explicitly Without Flipping Defaults

Decision:

- expose named embedder and reranker selections explicitly at the CLI and adapter level
- keep the current baseline defaults unchanged until the committed eval path shows that a candidate is better

Current named selections:

- embedder baseline: `snowflake-arctic-embed-xs`
- embedder candidate: `bge-m3`
- reranker baseline: `bge-reranker-v2-m3`
- reranker candidate: `bge-reranker-base`

Justification:

- Phase 07 is now far enough along that provider experiments are useful, but only if they remain one-at-a-time and inspectable
- explicit names are easier to reason about than relying only on raw Hugging Face repo ids buried in config
- side-by-side dense artifact naming reduces the risk of quietly overwriting the current baseline index
- changing defaults before running the bounded eval slice would make the repo harder to defend and harder to debug

Interpretation:

- Phase 07C is prep work for provider comparison, not a recommendation change
- alternate providers should be assessed against the committed golden eval baseline before any default path is reconsidered

## Decision: Keep Query Rewriting Lightweight

Decision:

- Start with deterministic query expansion rather than an always-on LLM rewrite stage.

Examples:

- map company names to tickers
- detect time constraints such as "last two years"
- detect intent terms such as `risk`, `revenue`, `growth outlook`, and `regulatory`

Justification:

- It keeps the system easier to reason about and easier to demo.
- It avoids introducing another opaque failure point early.
- It respects the spirit of the one-final-call answer constraint while still improving retrieval quality.

## Decision: Use One Final LLM Call For Answer Generation

Decision:

- The user-facing answer is generated in exactly one final LLM API call, with retrieved context injected into the prompt.

Justification:

- This is a hard requirement from the assessment.
- It keeps the answer path simple and reviewable.
- It makes the retrieval and prompt design more important, which is the core of the exercise.

Implementation note:

- the final answer contract now requires inline citation ids in the top-level `answer` field, not only in structured findings

## Decision: Treat Answer Backends As An Explicit Interface

Decision:

- Represent answer generation as an explicit backend client with configurable provider, base URL, API key, and model.

## Decision: Commit A Small Golden Eval Set Before Provider Extraction

Decision:

- commit a small golden eval set into the repo at `eval/golden_queries.json`
- save a baseline run artifact in-repo so later refactors can be judged against a known retrieval snapshot

Justification:

- Phase 07 work is primarily regression-risk management, not raw feature expansion
- provider extraction without a frozen baseline would make failures harder to attribute
- the committed eval set is small enough to inspect manually and broad enough to cover the repo’s main question types

Current scope:

- named-company comparisons
- single-company risk-factor lookup
- time-bounded growth or revenue lookup
- broader sector or regulatory prompt

## Decision: Emit A Build Manifest From The Actual Saved Retrieval Contract

Decision:

- emit `artifacts/build_manifest.json` as a machine-readable artifact
- prefer the saved dense metadata contract when reporting embedding model and dimension, rather than assuming current config values are authoritative

Justification:

- release and eval artifacts should describe the index that actually exists on disk
- the saved dense index may lag or differ from the current default embedding settings
- using the saved contract avoids silent drift between documentation, runtime defaults, and baseline evaluation

Implementation consequence:

- the build manifest now records chunking, lexical and dense table names, dense-index model and dimension, reranker defaults, and relevant artifact paths
- `eliza-rag-build-dense-index` refreshes the build manifest as part of the normal artifact build flow

## Decision: Dense Query Encoding Must Follow Saved Dense Metadata

Decision:

- dense retrieval query encoding must follow `artifacts/dense_index_metadata.json`, not only `Settings.dense_embedding_model`

Justification:

- the eval harness exposed a real mismatch where the workspace had a `hashed_v1` dense index on disk while current settings still pointed at a different default model
- query-time embedder selection based only on config can make an otherwise valid local dense index unusable
- the index contract is defined by the saved artifact, so query encoding must respect that contract

Implication:

- future modularization should preserve artifact-driven provider resolution where a saved index or build artifact is the real source of truth

## Decision: Keep Phase 09 Answer Judging Structured, Saved, And Heuristic-Only

Decision:

- keep retrieval-level scoring and answer-level scoring separate in the eval artifact shape
- save answer-level judgments directly into the eval artifact beside the raw answer text and citations
- keep the first Phase 09 judging method `heuristic_only` rather than adding a second judge-model dependency immediately
- build the reporting layer as a read-only view over saved `eval/*.json` artifacts

Justification:

- the repo needed stronger answer-quality evidence, but not a broad new online dependency surface
- a saved structured heuristic layer is easier to inspect than hidden transient judge output
- the raw artifact should remain the source of truth, with any report or visualization treated as a convenience layer

Current implementation:

- rubric saved at `eval/answer_judging_rubric.md`
- answer-level dimensions:
  - groundedness
  - citation quality
  - usefulness
  - comparison completeness
  - uncertainty handling
- generated report path: `uv run eliza-rag-eval-report`

## Decision: Add Judge-Assisted Eval As A Separate Artifact Pass

Decision:

- add an LLM judge path that runs over saved answer-included eval artifacts and writes a separate judged artifact
- default the hosted judge configuration to OpenRouter with `qwen/qwen3.6-plus:free`
- preserve the original answer artifact unchanged and treat the judge result as an additional scored layer

Justification:

- the heuristic answer judge is useful for bounded checks, but it is not strong enough for the user's current evaluation bar
- applying the judge to saved artifacts preserves raw evidence, exact prompts, and provenance
- keeping the judged artifact separate prevents the repo from silently replacing raw measured output with derived interpretation

Supported modes:

- hosted OpenAI Responses API
- hosted OpenRouter
- OpenAI-compatible Responses API servers exposed by a local or self-managed backend
- repo-supported local fallback via Ollama

Justification:

- the previous hardcoded OpenAI URL overstated backend flexibility
- OpenRouter is a meaningful hosted provider option for demo portability and model access
- local-compatible operation should be intentional and reviewable rather than implied by swapping only the model name
- the repo needs one owned fallback path for environments where no external LLM service is already running
- explicit configuration keeps the single-call answer path intact while making the supported contract honest

Current contract:

- request body: `{"model": ..., "input": ...}`
- endpoint shape: `/v1/responses`
- response field used by the repo: `output_text`

Hosted-provider requirement:

- `ELIZA_RAG_LLM_API_KEY` is required for `openai` and `openrouter`
- API keys are optional for `openai_compatible` and `local_ollama` because those backends may ignore authorization entirely

## Decision: Use Ollama As The Repo-Supported Local LLM Runtime

Decision:

- Use `ollama` as the repo-supported lightweight local runtime for the fallback answer backend.

Justification:

- it is simpler to explain and operate in a reviewer demo than bundling a Python inference stack or building `llama.cpp` inside the repo
- it provides a practical local model pull and serve workflow with low repo code volume
- it exposes an OpenAI-compatible `/v1` surface that fits the existing single-call answer backend shape
- the repo can own startup, readiness checks, and model-presence checks without pretending to bundle model weights itself

Config decision:

- `ELIZA_RAG_LLM_*` is the primary config surface for the active `local_ollama` answer path
- `ELIZA_RAG_LOCAL_LLM_BASE_URL` and `ELIZA_RAG_LOCAL_LLM_MODEL` remain compatibility aliases when `ELIZA_RAG_LLM_PROVIDER=local_ollama`, and they still apply directly to the standalone runtime helper
- this keeps the normal answer flow aligned with the same provider-selection interface used for hosted backends while avoiding a misleading split config story

Implementation implications:

- `uv run eliza-rag-local-llm prepare` is the repo-supported prepare path
- `uv run eliza-rag-local-llm start` starts the runtime without pulling a model
- `uv run eliza-rag-local-llm status` reports whether the runtime is installed, running, and model-ready
- `ELIZA_RAG_LLM_PROVIDER=local_ollama` routes the normal `eliza-rag-answer` command through the same answer pipeline while auto-checking local runtime readiness
- local fallback is not zero-download: users may need to install Ollama first and then download model weights during `prepare`

Hardware and portability note:

- the default local model is `qwen2.5:3b-instruct`, chosen as a practical lightweight baseline rather than a final quality target
- real performance depends on the local machine; the repo only guarantees explicit checks and failure messages, not acceptable latency on every system

Why not bundle another local runtime first:

- a Python-managed inference runtime would add heavier dependency and packaging complexity to a repo that is otherwise `uv`-first and lightweight
- a `llama.cpp` path would still require binary acquisition or local compilation work that is harder to make reviewer-safe within this timebox

## Decision: Optimize For Accuracy And Explainability Over Scale

Decision:

- Make choices that are easy to explain and reproduce locally, provided they do not hurt answer quality.

Justification:

- This is a take-home demo, not a production-scale platform build.
- Reviewers will care more about correctness, design judgment, and evaluation discipline than about distributed systems complexity.
- Every infrastructure choice should justify itself by improving speed of implementation, retrieval quality, or demo clarity.

## Decision: Optimize For Fast Local Demo Portability

Decision:

- The implementation should support a simple reviewer flow: clone the repo, restore one prebuilt LanceDB archive, and run a demo question with minimal setup friction.

Justification:

- This is the most likely usage pattern during review.
- `LanceDB` is being chosen partly because it supports this local-first workflow well.
- A portable demo reduces setup risk and makes the system easier to evaluate live.
- A release archive is simpler and less failure-prone under demo pressure than requiring every reviewer to rebuild local retrieval artifacts from scratch.

Implications:

- keep all retrieval infrastructure local
- use predictable on-disk artifact paths
- make the GitHub Release archive the primary supported reviewer path
- restore `data/lancedb/` plus `artifacts/dense_index_metadata.json` from a published ZIP before retrieval and answer commands
- keep the local build path available for maintainers when the retrieval artifacts need to be regenerated
- keep lexical retrieval usable with only the lexical chunk table present
- keep dense and hybrid retrieval behind explicit readiness checks with actionable failure guidance
- pin dependencies and document setup tightly

## Decision: Ship Prebuilt Retrieval Artifacts As A Release Archive

Decision:

- Treat this repo as a prepackaged demo bundle for reviewers, using a GitHub Release ZIP for the prebuilt retrieval artifacts while keeping the build path available for maintainers.

Justification:

- The current retrieval system still builds portable local LanceDB state deterministically from repo inputs.
- Under demo pressure, the release archive is a safer reviewer path than asking every machine to rebuild lexical and dense artifacts locally.
- The build and compaction steps are still valuable, but they now serve the publisher workflow rather than the primary reviewer workflow.

Reviewer contract:

- `uv sync`
- set `ELIZA_RAG_LANCEDB_ARCHIVE_URL`
- run `uv run eliza-rag-storage fetch-archive`
- then run `eliza-rag-search` or `eliza-rag-answer`

Rebuild triggers:

- rerun `uv run eliza-rag-load-chunks` whenever chunk materialization inputs or logic change
- rerun `uv run eliza-rag-build-dense-index` after every lexical chunk-table refresh so `filing_chunks_dense` stays aligned with `filing_chunks`
- rerun compaction and regenerate `artifacts/lancedb-demo.zip` before publishing a new demo release

## Decision: Stabilize With A Golden Eval Set Before Broad Modularization

Decision:

- freeze a small golden evaluation set and a build manifest before extracting broad provider interfaces or swapping major retrieval models

Justification:

- the current repo now has a credible demo path, so the dominant risk has shifted from missing capability to regression during refactor
- modularizing retrieval and answer components without a stable measurement harness would make future failures harder to localize
- a small eval set is enough to preserve signal on named-company coverage, contamination, comparison quality, and citation plausibility

Required artifacts:

- a golden query set with expected entity coverage and contamination rules
- a build manifest that records chunking, embedding, reranker, and artifact identity together
- saved structured outputs for baseline and candidate runs

## Decision: Treat Retrieval Components As Explicit Provider Interfaces

Decision:

- extract explicit internal interfaces for:
  - embedder
  - reranker
  - query analyzer
  - retriever
  - answer backend

Justification:

- the repo is now far enough along that provider swaps should happen behind stable seams rather than by editing orchestration code directly
- this keeps the CLI surface stable while making model experiments safer and easier to compare
- it aligns with the repo's need to test alternate embedding and reranking models without reopening the full architecture each time

Implementation constraint:

- first extract the current implementation behind interfaces without changing default behavior
- only then add alternate providers

## Decision: Prefer One-At-A-Time Provider Experiments

Decision:

- evaluate alternate embedding and reranking models one component at a time rather than combining multiple major provider swaps in the same experiment

Justification:

- single-variable experiments are easier to interpret
- the current repo already has evidence that query analysis, retrieval coverage, dense embeddings, and reranking all interact
- changing too many dimensions at once would make future decisions less defensible

Recommended order:

1. embeddings
2. rerankers
3. query-analysis or routing changes only if evaluation still points there

## Decision: Keep Deterministic Query Analysis As The Default Until Proven Insufficient

Decision:

- keep deterministic query analysis and routing as the default control-plane behavior during the next modularization phase

Justification:

- the current deterministic logic is inspectable, cheap, and aligned with the one-final-call answer contract
- routing is a control-plane problem, and a learned or generative router would add opaque failure modes before the repo has enough evaluation structure to justify them
- the strongest immediate upgrade opportunities remain embedding and reranking quality behind stable interfaces

## Decision: Keep Default CLI Answer Output Minimal

Decision:

- Make the default `eliza-rag-answer` terminal output user-oriented and compact:
  - show the synthesized answer
  - show citations
- Keep the richer structured fields available through `--json`.
- Keep a human-readable expanded terminal view behind `--verbose`.

Justification:

- In the terminal, `summary`, `answer`, and `findings` are often redundant and make the result harder to scan.
- The structured schema is still useful for debugging, downstream tooling, and future UI work.
- Separating default presentation from the underlying response schema lets the repo preserve machine-readable richness without forcing that complexity into the primary CLI UX.

Implications:

- the answer-generation response model still carries `summary`, `answer`, `findings`, `uncertainty`, and citations
- default CLI output optimizes for a user asking a question, not for inspecting the full internal answer contract
- `--verbose` is the opt-in path for reviewers who want prompt metadata, findings, and uncertainty in the terminal
