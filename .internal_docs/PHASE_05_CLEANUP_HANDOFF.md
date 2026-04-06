# Phase 05 Cleanup Handoff

## Purpose

This document closes out the work requested in `PHASE_05_CLEANUP.md` and records the repo state that Phase 06 should inherit.

The cleanup pass started as contract and documentation work, but the repo state now also includes the bounded backend expansion needed before Phase 06. The answer-generation path now has explicit provider support plus a repo-supported local fallback path via Ollama.

## Cleanup Scope Completed

The following cleanup goals are now complete:

- top-level `answer` citation enforcement is implemented
- answer backend configuration is explicit instead of hardcoded to one hosted endpoint
- OpenRouter is now a first-class hosted provider
- OpenAI-compatible local/server mode remains a first-class interface
- repo-supported local Ollama support is implemented for the fallback answer path
- deterministic offline tests cover the main answer-contract and backend-selection gaps
- repo docs and handoff notes were corrected to match actual behavior

## Code Changes

Primary files changed:

- `src/eliza_rag/answer_generation.py`
- `src/eliza_rag/config.py`
- `src/eliza_rag/local_runtime.py`
- `src/eliza_rag/local_runtime_cli.py`
- `tests/test_answer_generation.py`
- `tests/test_local_runtime.py`
- `tests/test_retrieval.py`
- `.env.example`
- `README.md`
- `QUALITY_NOTES.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `DECISIONS.md`
- `PHASE_05_HANDOFF.md`

### 1. Answer citation contract tightened

`src/eliza_rag/answer_generation.py` now enforces that:

- the top-level `answer` is present and non-empty
- the top-level `answer` includes inline citation ids such as `[C1]`
- citation ids referenced in `answer` must exist in the prompt context
- unknown citation ids fail fast
- malformed JSON still fails fast
- empty `findings` still fail fast

This closes the prior gap where `findings` citations were validated but the main `answer` text was not.

### 2. Backend abstraction introduced

The final answer call is now routed through an explicit backend client abstraction.

Current supported providers:

- `openai`
- `openrouter`
- `openai_compatible`
- `local_ollama`

All four still route through an OpenAI-compatible Responses API contract, but provider semantics, defaults, and failure messages are now explicit.

### 3. LLM config made explicit

`src/eliza_rag/config.py` now exposes:

- `ELIZA_RAG_LLM_PROVIDER`
- `ELIZA_RAG_LLM_BASE_URL`
- `ELIZA_RAG_LLM_API_KEY`
- `ELIZA_RAG_LLM_MODEL`

Compatibility fallback remains in place for:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`

That fallback exists only to avoid breaking older local setups. The repo documentation now points users to the `ELIZA_RAG_LLM_*` variables as the supported interface.

### 4. Repo-managed local support added

The supported local/server contract is now documented as:

- an OpenAI-compatible HTTP server
- endpoint shape: `/v1/responses`
- request fields used by the repo: `model`, `input`
- response field used by the repo: `output_text`

Repo-managed local path:

- `uv run eliza-rag-local-llm prepare` starts Ollama if needed and pulls the configured model
- `uv run eliza-rag-local-llm start` starts Ollama without pulling
- `uv run eliza-rag-local-llm status` reports installed/runtime/model-ready state
- `ELIZA_RAG_LLM_PROVIDER=local_ollama` uses the same `eliza-rag-answer` command and auto-checks local readiness

## Test Coverage Added

`tests/test_answer_generation.py` now covers:

- `answer` with no inline citations
- `answer` with unknown citation ids
- unknown citation ids in `findings`
- malformed JSON
- empty `findings`
- backend config selection for `openai_compatible`
- backend config selection for `openrouter`
- rejection of unsupported providers
- missing API key error surface
- provider/network error surface
- local-provider missing-model error surface
- no retrieval results
- happy-path end-to-end answer assembly with a fake client

`tests/test_local_runtime.py` now covers:

- missing local runtime binary
- missing local model artifact
- local startup behavior
- local model-pull failure handling

`tests/test_retrieval.py` was updated only as needed for the expanded `Settings` shape.

## Verification Run

Executed successfully:

- `uv run pytest tests/test_answer_generation.py tests/test_local_runtime.py`
- `uv run eliza-rag-local-llm status`

Observed result:

- answer-generation and local-runtime tests passed
- local runtime CLI executed and reported `runtime_available=false` in this workspace

## What Was Not Verified Live

The following were not live-verified in this cleanup pass:

- a real hosted OpenAI answer call
- a real hosted OpenRouter answer call
- a real local Ollama answer call
- a real user-provided OpenAI-compatible server answer call

This distinction matters. The committed tests are deterministic, mocked unit tests. They verify parsing, configuration, and failure handling, but they do not prove that a specific hosted or local backend is reachable from a given machine.

## Documentation State After Cleanup

The repo docs now state these points explicitly:

- the main `answer` text is citation-disciplined
- the answer path uses exactly one final LLM call after retrieval
- supported backend modes are hosted OpenAI, hosted OpenRouter, user-provided OpenAI-compatible servers, and a repo-supported local fallback via Ollama
- local Ollama mode is repo-supported for startup/readiness but still depends on an installed runtime and model artifact
- unit tests are offline and mocked rather than live backend verification

## Phase 06 Starting Point

Phase 06 should assume the following baseline is now true:

- retrieval stack exists and remains unchanged in this cleanup pass
- answer generation is structurally stricter than before
- backend support is explicit and documented
- the repo no longer needs to imply vague local model support
- the next useful work is quality improvement, not cleanup of the Phase 05 contract

## Recommended Next Steps

The most defensible Phase 06 starting sequence is:

1. run one live smoke test against hosted OpenAI
2. run one live smoke test against a user-provided OpenAI-compatible local/server backend
3. improve retrieval result ordering, most likely with reranking
4. add lightweight comparative evaluation around answer quality and grounding
5. polish CLI failure messaging only after the live smoke paths are confirmed

## Non-Goals Still Unchanged

This cleanup pass did not attempt:

- reranking
- retrieval redesign
- eval framework buildout
- prompt experimentation beyond enforcing the existing contract

## Bottom Line

Phase 05 is now in a materially cleaner state than before:

- the answer contract is stricter
- backend claims are more honest
- local-compatible support is explicit instead of implied
- tests cover the main contract regressions
- documentation matches the implementation closely enough for Phase 06 to proceed without cleanup debt first
