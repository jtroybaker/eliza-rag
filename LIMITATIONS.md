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
