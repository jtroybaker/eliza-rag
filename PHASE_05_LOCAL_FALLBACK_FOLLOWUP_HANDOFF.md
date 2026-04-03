# Phase 05 Local Fallback Follow-Up Handoff

## Purpose

This document closes out the work requested in `PHASE_05_LOCAL_FALLBACK_FOLLOWUP.md`.

The goal of this follow-up was to make the local fallback story honest and internally consistent:

- local fallback is supported via an Ollama-based workflow
- the repo can help start, check, and prepare that workflow
- the repo does not install or bundle the Ollama runtime itself
- the active config story for `local_ollama` is no longer split across misleading parallel env var surfaces

## Scope Completed

The requested follow-up items are now addressed:

- wording was narrowed from "repo-managed local fallback" to "repo-supported local fallback via Ollama"
- the active `local_ollama` config path was standardized on `ELIZA_RAG_LLM_*`
- `ELIZA_RAG_LOCAL_LLM_BASE_URL` and `ELIZA_RAG_LOCAL_LLM_MODEL` remain recognized as compatibility aliases when the provider is `local_ollama`
- the README now includes a first-class Ollama install and prepare section
- the docs now state explicitly that local fallback may require downloading both Ollama and model weights
- the minimum requested docs were updated to match the corrected claim

## Code Changes

Primary implementation files changed:

- `src/eliza_rag/config.py`
- `src/eliza_rag/local_runtime.py`
- `src/eliza_rag/local_runtime_cli.py`
- `tests/test_config.py`
- `.env.example`

### 1. Local config behavior is now consistent

`src/eliza_rag/config.py` now resolves `local_ollama` settings in this order:

- prefer `ELIZA_RAG_LLM_BASE_URL` and `ELIZA_RAG_LLM_MODEL`
- if those are unset and the provider is `local_ollama`, fall back to `ELIZA_RAG_LOCAL_LLM_BASE_URL` and `ELIZA_RAG_LOCAL_LLM_MODEL`
- otherwise use the normal provider defaults

This preserves compatibility without keeping two equally-promoted config paths in the docs.

### 2. Local runtime wording was corrected

`src/eliza_rag/local_runtime.py` and `src/eliza_rag/local_runtime_cli.py` now describe the local path as a repo-supported Ollama workflow rather than a repo-managed runtime.

That wording is important because the repo can operate Ollama after installation, but it does not provision Ollama from scratch.

## Documentation Changes

Primary documentation files changed:

- `README.md`
- `QUALITY_NOTES.md`
- `LIMITATIONS.md`
- `DECISIONS.md`
- `PHASE_05_BACKEND_EXPANSION_HANDOFF.md`
- `PHASE_05_CLEANUP_HANDOFF.md`
- `IMPLEMENTATION_KANBAN.md`
- `PHASE_05_BACKEND_EXPANSION.md`
- `.env.example`

### README updates

`README.md` now includes:

- explicit local setup wording: local mode requires Ollama to already be installed
- an example Ollama install command and official download link
- `uv run eliza-rag-local-llm prepare`
- the default model: `qwen2.5:3b-instruct`
- the preferred local config surface using `ELIZA_RAG_LLM_PROVIDER`, `ELIZA_RAG_LLM_BASE_URL`, and `ELIZA_RAG_LLM_MODEL`
- expected failure cases for missing `ollama`, startup failure, and missing model pull
- a manual smoke-test note using `uv run eliza-rag-local-llm status`
- a short troubleshooting section
- explicit wording that local fallback is not zero-download

### Other doc updates

The follow-up docs now consistently say:

- OpenAI is supported
- OpenRouter is supported
- OpenAI-compatible backends are supported
- local fallback is supported via an Ollama workflow the repo documents and helps operate
- the repo does not falsely claim bundled runtime provisioning

## Tests Added

`tests/test_config.py` was added to cover:

- `local_ollama` using `ELIZA_RAG_LOCAL_LLM_BASE_URL` and `ELIZA_RAG_LOCAL_LLM_MODEL` when the primary `ELIZA_RAG_LLM_*` values are unset
- `local_ollama` preferring the primary `ELIZA_RAG_LLM_*` values when both surfaces are present

Existing local runtime tests remained in:

- `tests/test_local_runtime.py`

## Verification Run

Executed successfully:

- `uv run pytest tests/test_config.py tests/test_local_runtime.py`

Observed:

- all focused config and local runtime tests passed

Additional verification:

- a repo-wide search was used to remove remaining outdated "repo-managed" wording outside the task file itself

## What Was Not Verified Live

This follow-up did not live-verify:

- an actual Ollama installation flow on this machine
- a real `uv run eliza-rag-local-llm prepare` against a live Ollama runtime
- a real local `eliza-rag-answer` round-trip with `ELIZA_RAG_LLM_PROVIDER=local_ollama`

That is intentional. This pass was focused on configuration consistency and documentation accuracy, not on adding new live integration claims.

## Final Repo Claim After This Follow-Up

The repo can now honestly claim:

- OpenAI is supported
- OpenRouter is supported
- OpenAI-compatible backends are supported
- local fallback is supported via a repo-documented Ollama workflow
- the repo can start, check, and prepare Ollama once it is installed
- the repo does not install or bundle Ollama itself
- local fallback may require runtime and model downloads
- the active local config story is internally consistent

## Recommended Next Step

If a later pass wants stronger operational confidence, the next most useful verification step is one real local smoke test on a machine with Ollama installed:

1. install Ollama
2. run `uv run eliza-rag-local-llm prepare`
3. run `uv run eliza-rag-local-llm status`
4. run one `ELIZA_RAG_LLM_PROVIDER=local_ollama uv run eliza-rag-answer "..."`

Until that happens, the repo should continue to describe the local path as documented and test-covered, not as live-verified in this workspace.
