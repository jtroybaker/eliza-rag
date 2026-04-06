# Limitations And Caveats

## Purpose

This file tracks known weaknesses, caveats, and data-quality limitations in the project so they are visible during implementation, evaluation, and the final readout.

These items are not necessarily blockers. In many cases they are exactly the kinds of constraints the retrieval and evaluation framework should expose and handle.

## Dataset Limitations

### Flattened Filing Text

The corpus is provided as plain text and appears to be heavily flattened relative to the original SEC filing structure.

Implications:

- original layout and formatting cues are partially lost
- headings may not always appear as clean standalone blocks
- tables, bullets, and section boundaries may be degraded
- inline references can resemble true section headers

Impact on system behavior:

- section detection is heuristic rather than authoritative
- chunking may create imperfect boundaries
- section metadata should be treated as approximate
- lexical and late-interaction retrieval may prove especially valuable on this kind of text

### Imperfect Section Reconstruction

The system currently infers structure from lossy text patterns such as `PART`, `Item`, and related headings.

Implications:

- some inferred section breaks may be false positives
- some true section boundaries may be missed
- chunk labels may not perfectly match the source filing's intended structure

Mitigation:

- treat section metadata as a retrieval aid, not as ground truth
- let the evaluation framework determine whether section-aware chunking helps or hurts
- preserve alternative chunking strategies in the experiment matrix

### Corpus Date Range Mismatch

The assessment brief describes a 2023-2025 corpus, but the provided archive appears to span a broader range.

Observed in earlier inspection:

- filings range from `2015-02-27` to `2026-02-19`

Implications:

- the implementation should trust the provided data, not only the brief summary
- time-aware retrieval and evaluation should use actual filing metadata
- demo explanations should acknowledge the mismatch if relevant

## System Limitations

### Baseline Chunking Is Heuristic

The current chunker is a practical baseline, not a final claim of optimal segmentation.

Implications:

- chunking quality must be validated through evaluation
- different chunking strategies may outperform the baseline on flattened filings
- `chonkie` remains important as the experiment driver for chunking comparisons

### Section Metadata May Be Approximate

Because the source text is imperfect, section and section-path labels should be treated as useful metadata rather than exact document truth.

Implications:

- section-based filtering may help, but should not be over-trusted
- retrieval quality should be judged by answer grounding, not only by matching inferred section labels

### Local Demo Prioritizes Simplicity Over Production Robustness

This repository is being built as a portable assessment demo, not as a production retrieval platform.

Implications:

- local reproducibility and clarity are prioritized
- some engineering shortcuts may be acceptable if they do not hurt answer quality
- final evaluation should still punish weak retrieval or poor grounding

### Final Answer Path Uses A Strict Single-Call Contract

The Phase 05 answer command intentionally performs exactly one final answer-generation API call and does not retry or repair malformed model output.

Implications:

- the prompt is strict so the returned payload is easier to parse and inspect
- if the model returns invalid JSON, the CLI fails fast instead of issuing a second call
- this preserves compliance with the assignment's one-final-call requirement, but it is less forgiving than a production workflow

### OpenAI-Compatible Backends Still Depend On A Narrow Responses Contract

The repository now supports hosted OpenAI, hosted OpenRouter, user-provided OpenAI-compatible backends, and a repo-supported local fallback via Ollama, but the HTTP client still expects a narrow Responses-style contract.

Implications:

- `ELIZA_RAG_LLM_PROVIDER=openai_compatible` assumes a server that exposes a `/v1/responses`-style endpoint
- the current client sends `model` and `input` and expects an `output_text` field in the response
- some self-hosted or proxy backends may claim OpenAI compatibility while still failing this narrower contract
- OpenRouter support is first-class, but model naming is provider-specific and typically requires names such as `openai/gpt-5-mini`

### Repo-Supported Local Ollama Mode Still Depends On Machine State

The repository can now help operate a lightweight local Ollama path, but it does not bundle Ollama itself or any model artifacts.

Implications:

- the local fallback still requires the `ollama` runtime to be installed on the machine
- first use may also require downloading the Ollama runtime through Ollama's own installation flow before the repo can interact with it
- first-time `prepare` runs may incur significant model-download cost
- local inference quality and latency depend heavily on available CPU, RAM, and optional GPU support
- `eliza-rag-answer` can start the local runtime on demand in `local_ollama` mode, but it fails fast if the configured model was not prepared yet

### Citation Quality Depends On Retrieval Quality

The citation scheme is traceable, but it only cites the retrieved chunks placed into the final prompt.

Implications:

- citations remain inspectable and map back to chunk metadata
- the parser now rejects answers that omit inline citation ids in the top-level `answer`
- poor retrieval ordering can still lead to incomplete comparative answers
- reranking plus coverage-preserving retrieval is now the active mitigation path for stronger answer quality on multi-entity questions during Phase 06C

### Dense Retrieval Is Stronger Than Before, But Still Not Sufficient Alone

The default dense retrieval path now uses `Snowflake/snowflake-arctic-embed-xs`, and the default reranker now uses `BAAI/bge-reranker-v2-m3`.

Implications:

- the dense and rerank stages are no longer limited to the original hashed and heuristic baselines
- first-time local setup now carries real model-download and build-time cost
- stronger semantic scoring improved the technical credibility of the stack, but did not by itself resolve the main multi-company comparison failure

### Multi-Company Coverage Still Depends On Heuristic Retrieval And Deterministic Entity Detection

Phase 06B and Phase 06C runs showed that named-company comparison queries can still lose required entities in the final top-k even after upgrading both the dense model and the reranker and then adding coverage-preserving retrieval.

Observed behavior:

- a query naming Apple, Tesla, and JPMorgan still produced top-k contexts dominated by Tesla and JPMorgan
- after switching to the stronger BGE reranker, the candidate set still omitted Apple and even admitted an unrelated Bank of America chunk in one run
- after the company-detection follow-up, deterministic alias normalization now recognizes prompt forms such as `JPMorgan`, `JPMorgan Chase`, and `Bank of America`
- with that stronger detection in place, `targeted_hybrid + BGE rerank` restored full named-company coverage on the Apple/Tesla/JPMorgan comparison slice
- in narrower Apple/Tesla comparisons, `targeted_hybrid` substantially reduced unrelated-company contamination when detection succeeded

Implications:

- stronger reranking alone does not guarantee entity coverage
- coverage-preserving retrieval only helps when deterministic company detection succeeds
- the main known multi-company blocker has been narrowed enough to justify final evaluation, but the behavior is still heuristic rather than guaranteed for every unseen company-name variant
- future regressions are still possible for aliases that are not represented clearly enough in corpus metadata

### Release Archive Freshness Is A Publisher Responsibility

The primary demo distribution path now restores a prebuilt LanceDB archive from a GitHub Release instead of rebuilding retrieval state on every reviewer machine.

Implications:

- the archive must be regenerated after any corpus, chunking, lexical-index, or dense-index refresh
- a stale release ZIP can drift from the current code and quietly produce confusing demo behavior if it is not republished
- this tradeoff is acceptable for the current live-demo goal because it reduces reviewer setup risk, but it is still a manual publisher responsibility rather than a self-validating artifact pipeline

### The New Golden Eval Baseline Already Exposes Contamination And Sector-Coverage Gaps

Phase 07A added a committed golden eval set and a saved baseline run artifact. That baseline already shows meaningful retrieval-quality gaps rather than just harness shape.

Observed in `eval/baseline_targeted_hybrid_retrieval.json`:

- the Apple single-company annual-risk prompt still pulls unrelated issuers into the top-k
- the broader bank regulatory or capital prompt does not fully recover the expected `JPM` and `BAC` coverage in the saved baseline

Implications:

- freezing the eval set does not mean retrieval quality is frozen at an acceptable endpoint
- broader sector prompts remain weaker than named-company comparison prompts
- later scoring should explicitly penalize contamination and not only missing expected tickers

### Retrieval-Level And Answer-Level Scoring Are Now Separated, But The Answer Judge Is Still Heuristic

The eval runner no longer stops at retrieval-only scoring, but the current answer judge is still a bounded heuristic layer rather than a human review process or judge-model ensemble.

Current state:

- expected ticker coverage is recorded
- comparison behavior is recorded
- contamination observations are now turned into stable saved fields
- explicit `pass`, `partial_pass`, and `fail` outcomes are now assigned for retrieval-only runs
- the answer-included baseline artifact now also records:
  - groundedness
  - citation quality
  - usefulness
  - comparison completeness
  - uncertainty handling
- the current answer-judging method is `heuristic_only`

Implications:

- the provider artifacts are now stronger retrieval-quality evidence than the old placeholder contract
- the saved answer-included baseline is stronger end-to-end evidence than the retrieval-only runs, but it is still not the same thing as human judgment
- future provider experiments should avoid claiming answer wins from heuristic judge output alone without preserving the raw answer artifact

### OpenRouter Judge Runs Depend On External Credentials And Provider Behavior

The repo now supports a judge-assisted eval pass using OpenRouter, with `qwen/qwen3.6-plus:free` as the default configured judge model.

Implications:

- a real judge run requires `OPENROUTER_API_KEY` or `ELIZA_RAG_JUDGE_API_KEY`
- the judge path still depends on the narrow Responses-style contract already used elsewhere in the repo
- free hosted models can change behavior or availability independently of the saved raw eval artifacts
- judge-assisted outputs should therefore be treated as an overlay on saved answer artifacts, not as a replacement for them

### Local Answer Artifacts Can Still Fail Because The Single-Call Answer Contract Is Strict

The saved Phase 09 answer-included baseline run shows that the answer layer can still fail even when retrieval looks reasonable.

Observed in `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`:

- the sector-style bank regulatory prompt still fails retrieval-level expectations
- the local Ollama answer for that case also failed the strict parsing contract with `Model response must include a non-empty \`answer\``

Implications:

- answer-included evals can expose answer-format failures in addition to retrieval-quality failures
- the single-call answer contract remains intentionally strict and does not retry malformed outputs
- answer-level reporting should therefore be interpreted alongside the raw `answer_error` and saved artifact contents, not only the summary counts

### Provider Wiring Is Not The Same Thing As Provider Evaluation

Phase 07C exposed alternate provider selections explicitly, and Phase 08 converted part of that surface into actual saved evidence.

Current state:

- saved provider-comparison artifacts now exist for:
  - Snowflake embedder + `bge-reranker-v2-m3`
  - `hashed_v1` embedder + `bge-reranker-v2-m3`
  - Snowflake embedder + `bge-reranker-base`
- alternate embedder `bge-m3` is still selectable beside baseline `snowflake-arctic-embed-xs`
- alternate reranker `bge-reranker-base` is selectable beside baseline `bge-reranker-v2-m3`
- the `bge-m3` embedder was not retained in the saved Phase 08 evidence set because the local rebuild cost was too high for this bounded run
- README commands now describe how to run baseline versus candidate comparisons one component at a time

Implications:

- no default recommendation should change just because a candidate is wired in
- the repo now has meaningful saved provider evidence, but only for the runs that completed locally
- side-by-side dense builds need separate table names and metadata artifact names or the baseline contract can be overwritten

### Hugging Face Model Downloads Still Add Operational Friction

The provider experiment surface depends on local model downloads for the non-hashed embedder and the transformer rerankers.

Implications:

- first use of `bge-m3`, `bge-reranker-v2-m3`, or `bge-reranker-base` can fail or stall in environments without network access or sufficient local cache
- provider experiments are therefore easier to wire than to reproduce deterministically on a fresh machine
- this does not block the baseline demo path, but it does matter for later comparison reproducibility

### Release Archives Should Remain The Reviewer-Facing Artifact Source

The repo now carries both saved eval evidence and a reviewer-facing release-archive story. Those need to stay distinct.

Implications:

- saved `eval/*.json` artifacts are useful evidence and should remain small enough to review and visualize
- local experiment tables and temporary inspection outputs should not become part of the normal reviewer story
- GitHub Release archives should remain the sanctioned large retrieval artifact source for reviewers
- stale local dense tables, temp LanceDB inspection directories, or abandoned provider rebuilds should not be treated as demo truth unless they are republished deliberately

### Generated Reports Are Views, Not New Evidence Sources

The repo now includes a generated report artifact at `eval/provider_eval_report.md`.

Implications:

- the report is useful for spotting failure clusters quickly
- the report is derived from saved `eval/*.json` files and can only be as good as those inputs
- recommendation changes should still cite the underlying JSON artifacts, not only the generated report

### Modularization Without A Frozen Eval Set Would Be High Risk

The repo is now far enough along that broad modularization work can regress a demo path that currently functions.

Implications:

- extracting provider interfaces before freezing a small golden evaluation set would make regressions harder to detect
- changing multiple components at once would blur whether failures come from architecture changes, provider swaps, or both
- the next phase should add a golden set and build manifest before treating provider modularity as the main workstream

### Query Routing Is Still Better Framed As A Control-Plane Problem Than A Model-Swap Problem

The current repo uses deterministic query analysis to infer years, companies, and comparison intent. That logic is heuristic, but it is also inspectable.

Implications:

- a learned or generative routing model would add opaque failure modes before the repo has enough evaluation structure to justify it
- routing changes should be treated as a later experiment, not the first modularization target
- embeddings and rerankers remain the safer first provider-swap surfaces

## Evaluation Implications

These limitations are part of the experiment, not just background noise.

The evaluation framework should be expected to:

- reveal whether chunking helps or hurts on flattened filing text
- reveal whether lexical, dense, hybrid, or reranked retrieval performs best under noisy structure
- penalize strategies that rely too heavily on incorrect structural assumptions
- reward systems that remain accurate and grounded despite imperfect inputs

## Late Interaction Note

Late-interaction retrieval should be treated as a retrieval-stage candidate, not as answer-generation behavior.

Interpretation of the one-call requirement:

- the final user-facing answer must come from one LLM API call
- retrieval, indexing, reranking, and late-interaction retrieval can happen before that final answer call

Implication:

- a ColBERT-style or other late-interaction retrieval stage does not inherently violate the one-call requirement, as long as it is part of retrieval and not a multi-call answer synthesis loop

This should still be validated against the project wording and judged pragmatically against timebox and implementation overhead.

## Final Readout Requirement

These limitations should be reflected in the final readout.

At minimum, the final summary should acknowledge:

- the corpus is imperfect and structurally lossy
- section-aware chunking is heuristic
- retrieval and evaluation choices were designed to mitigate noisy inputs
- the chosen pipeline was selected empirically under those constraints
