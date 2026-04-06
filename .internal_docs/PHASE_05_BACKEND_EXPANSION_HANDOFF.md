# Phase 05 Backend Expansion Completed Handoff

## Status

The Phase 05 backend expansion is now implemented.

The answer path supports all four intended backend modes:

1. hosted OpenAI
2. hosted OpenRouter
3. user-provided OpenAI-compatible backend
4. repo-supported local fallback via Ollama

The same `uv run eliza-rag-answer ...` command now works across those modes through explicit configuration rather than code edits.

## What Changed

Primary implementation files:

- `src/eliza_rag/config.py`
- `src/eliza_rag/answer_generation.py`
- `src/eliza_rag/local_runtime.py`
- `src/eliza_rag/local_runtime_cli.py`
- `pyproject.toml`
- `tests/test_answer_generation.py`
- `tests/test_local_runtime.py`
- `tests/test_retrieval.py`

Primary documentation files:

- `README.md`
- `.env.example`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `QUALITY_NOTES.md`
- `IMPLEMENTATION_KANBAN.md`
- `PHASE_05_CLEANUP_HANDOFF.md`
- `PHASE_05_HANDOFF.md`

## Delivered Behavior

### 1. OpenRouter is now first-class

The backend resolver now supports:

- `ELIZA_RAG_LLM_PROVIDER=openai`
- `ELIZA_RAG_LLM_PROVIDER=openrouter`
- `ELIZA_RAG_LLM_PROVIDER=openai_compatible`
- `ELIZA_RAG_LLM_PROVIDER=local_ollama`

OpenRouter now has:

- an explicit provider branch rather than an undocumented generic-compatible path
- a documented default base URL of `https://openrouter.ai/api/v1`
- normal hosted-provider API key enforcement
- documented model naming expectations such as `openai/gpt-5-mini`

### 2. Repo-supported local runtime choice was made

Chosen runtime:

- `ollama`

Why this path was chosen:

- it is simpler to explain than bundling a Python inference stack
- it is less intrusive than introducing local model build tooling into the repo
- it already exposes a practical local serving workflow
- it keeps the answer pipeline on the same OpenAI-compatible `/v1/responses` shape

Default local model:

- `qwen2.5:3b-instruct`

This is a lightweight fallback choice for reviewer portability, not a claim that it is the best-quality local model.

### 3. Managed local startup behavior exists

Repo-supported commands:

```bash
uv run eliza-rag-local-llm status
uv run eliza-rag-local-llm start
uv run eliza-rag-local-llm prepare
```

Behavior:

- `status` reports runtime presence, server state, and model availability
- `start` starts the local Ollama server if possible
- `prepare` starts the server if needed and pulls the configured model
- this workflow assumes Ollama is already installed and may require downloading model weights

When `ELIZA_RAG_LLM_PROVIDER=local_ollama`, the normal answer path:

- checks runtime readiness before issuing the final answer call
- attempts local server startup when the runtime is installed but not yet running
- fails clearly when Ollama is not installed
- fails clearly when the configured local model has not been prepared

### 4. Backend resolution is unified

The answer command remains:

```bash
uv run eliza-rag-answer "..."
```

Backend switching is now controlled entirely through environment variables, primarily:

- `ELIZA_RAG_LLM_PROVIDER`
- `ELIZA_RAG_LLM_BASE_URL`
- `ELIZA_RAG_LLM_API_KEY`
- `ELIZA_RAG_LLM_MODEL`

Primary active config for the normal `local_ollama` answer path uses:

- `ELIZA_RAG_LLM_PROVIDER`
- `ELIZA_RAG_LLM_BASE_URL`
- `ELIZA_RAG_LLM_API_KEY`
- `ELIZA_RAG_LLM_MODEL`

Standalone runtime-helper settings remain available through:

- `ELIZA_RAG_LOCAL_LLM_RUNTIME`
- `ELIZA_RAG_LOCAL_LLM_RUNTIME_COMMAND`
- `ELIZA_RAG_LOCAL_LLM_BASE_URL`
- `ELIZA_RAG_LOCAL_LLM_MODEL`
- `ELIZA_RAG_LOCAL_LLM_START_TIMEOUT_SECONDS`

Compatibility note:

- `ELIZA_RAG_LOCAL_LLM_BASE_URL` and `ELIZA_RAG_LOCAL_LLM_MODEL` are still recognized when `ELIZA_RAG_LLM_PROVIDER=local_ollama`, but the repo docs now standardize on `ELIZA_RAG_LLM_*` for the active answer path

### 5. Failure semantics are more operational

The answer path now distinguishes between:

- unsupported provider selection
- missing hosted credentials
- unreachable hosted or compatible endpoint
- incompatible backend response shape
- missing local runtime binary
- local runtime startup failure
- missing local model artifact

The answer contract remains strict:

- malformed model JSON still fails fast
- missing inline citations in the top-level `answer` still fail fast

## Verification

Executed:

- `uv run pytest`
- `uv run ruff check src/eliza_rag tests`
- `uv run eliza-rag-local-llm status`

Observed:

- full test suite passed
- lint passed
- the local runtime CLI entry point executed successfully
- in this workspace, `eliza-rag-local-llm status` reported `runtime_available=false`

## What Was Not Live-Verified

The following were not live-verified in this workspace:

- a real hosted OpenAI answer call
- a real hosted OpenRouter answer call
- a real user-provided OpenAI-compatible answer call
- a real local Ollama answer call

The committed verification is deterministic test coverage plus a CLI smoke check, not a live provider round-trip.

## Phase 06 Starting Point

Phase 06 can now assume:

- answer backend support is explicit and documented
- OpenRouter is first-class
- the repo documents and supports a concrete local fallback path via Ollama, but does not provision the Ollama runtime itself
- the answer path still preserves the citation-enforced single-call contract

The next work should move to retrieval quality and evaluation rather than backend expansion.
