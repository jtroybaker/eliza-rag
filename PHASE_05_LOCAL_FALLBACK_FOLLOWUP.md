# Remaining Backend Cleanup

## Goal

Tighten the local fallback story so the repo honestly supports a user-guided local Ollama path, without claiming zero-setup or bundled runtime installation.

## What To Change

### 1. Narrow the wording

Update wording everywhere from "repo-managed local fallback" to "repo-supported local fallback via Ollama" unless the repo actually installs Ollama itself.

Current reality:

- the repo can start, check, and prepare Ollama once it is installed
- the repo does not provision the Ollama runtime from scratch

That is still useful, but it is not the same as shipping the runtime.

### 2. Fix the local config surface

Right now the docs mention:

- `ELIZA_RAG_LOCAL_LLM_BASE_URL`
- `ELIZA_RAG_LOCAL_LLM_MODEL`

But in `local_ollama` mode the runtime manager currently uses:

- `settings.llm_base_url`
- `settings.llm_model`

Pick one approach and make it consistent.

Preferred:

- make `ELIZA_RAG_LOCAL_LLM_*` actually drive the local runtime path consistently

Acceptable:

- remove or de-emphasize those vars from docs and standardize on `ELIZA_RAG_LLM_*` for active local mode

Do not leave a misleading dual config surface in place.

### 3. Add a first-class Ollama install + prepare section to the README

This section should explicitly cover:

- local mode requires Ollama to be installed
- example install command(s) or an official install link
- `uv run eliza-rag-local-llm prepare`
- default model: `qwen2.5:3b-instruct`
- how to override the model
- how to run `eliza-rag-answer` with `ELIZA_RAG_LLM_PROVIDER=local_ollama`
- expected failure cases if Ollama is missing or the model is not prepared

### 4. Make the download assumption explicit

State clearly that local fallback may require downloading:

- the Ollama runtime
- model weights

This is acceptable and expected. The repo should not imply that local fallback is zero-download.

### 5. Update repo docs to match the corrected claim

At minimum update:

- `README.md`
- `QUALITY_NOTES.md`
- `LIMITATIONS.md`
- `DECISIONS.md`
- `PHASE_05_BACKEND_EXPANSION_HANDOFF.md`

## Acceptance Standard

This follow-up is done when the repo can honestly say:

- OpenAI is supported
- OpenRouter is supported
- OpenAI-compatible backends are supported
- local fallback is supported via an Ollama-based workflow that the repo documents and helps operate
- the repo does not falsely claim bundled runtime provisioning
- the local config and env var story is internally consistent

## Nice To Have

- add one manual smoke-test note for the Ollama path in docs
- add a short troubleshooting section for:
  - `ollama` not on PATH
  - server not starting
  - model not pulled yet
