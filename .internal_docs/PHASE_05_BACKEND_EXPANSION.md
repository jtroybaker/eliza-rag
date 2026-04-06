# Phase 05 Backend Expansion Handoff

## Purpose

This file extends the cleanup work captured in `PHASE_05_CLEANUP.md` and `PHASE_05_CLEANUP_HANDOFF.md`.

The cleanup pass improved contract enforcement and made backend configuration explicit, but the actual demo requirement is now broader:

- the answer path must support OpenRouter as a first-class provider
- the repo must be able to provide its own lightweight local model path on demand when no language-model service is already running

This is not just documentation cleanup. It is a bounded implementation slice that should be completed before Phase 06 work on reranking or evaluation.

## New Required Capabilities

The repository should support all of the following answer-generation modes:

1. hosted OpenAI
2. hosted OpenRouter
3. user-provided OpenAI-compatible server
4. repo-supported local lightweight model fallback via Ollama

The main reviewer/demo requirement is:

- if no external LLM service is already running, the repo must still offer a path to bring up a lightweight local model on demand and use it from the same answer pipeline

## Why The Current State Is Still Incomplete

The current answer backend cleanup improved two things:

- stricter citation enforcement in the top-level `answer`
- explicit provider/base URL configuration for OpenAI-compatible Responses API servers

However, the current implementation still falls short of the actual demo need:

- OpenRouter is not yet a first-class supported provider
- local compatibility is only protocol-level support, not repo-supported runtime support via Ollama
- the repo does not currently launch or provision its own lightweight local model path

That means the repo still assumes a live external service already exists, which is not safe enough for the intended demo environment.

## Required Implementation Work

### 1. Add OpenRouter as a first-class provider

Expected outcome:

- explicit provider support for `openrouter`
- documented default base URL for OpenRouter
- correct authentication behavior
- documented model naming expectations for OpenRouter
- test coverage for provider selection and request construction

Minimum standard:

- OpenRouter should not be treated as an undocumented special case of `openai_compatible`
- the repo docs should tell a user exactly how to configure and use it

### 2. Choose a repo-supported lightweight local runtime

This is the main design decision still missing.

The next agent must choose one practical path for a lightweight local model that the repo can bring up on demand.

The chosen path must be documented in `DECISIONS.md`.

The decision should explicitly address:

- runtime choice
- why it is the most practical option for this repo
- installation or build implications
- expected hardware constraints
- how the repo will detect readiness
- how the answer CLI will route to it

Possible patterns:

- use an existing local server runtime such as `ollama` if the repo will manage startup and model pull behavior
- use a local OpenAI-compatible server such as a `llama.cpp` server path
- use a Python-managed local inference runtime if that is feasible within the repo and timebox

Do not leave this vague. Pick one.

### 3. Implement managed local startup behavior

Expected outcome:

- one clear repo-supported command to prepare or start the local backend
- health-check behavior before answer generation depends on it
- clear handling when the local model artifact is missing
- clear behavior when the runtime is not installed or not buildable on the current machine

The repo does not necessarily need to hide all setup cost, but it must provide a reviewer-usable path that is owned by the repo rather than assumed to exist externally.

### 4. Unify backend resolution in the answer path

Expected outcome:

- the same `eliza-rag-answer` command should work across:
  - hosted OpenAI
  - hosted OpenRouter
  - user-provided compatible backend
  - repo-supported local backend via Ollama

The backend switch must be driven by explicit configuration or documented CLI behavior, not by code edits.

### 5. Add backend readiness and failure semantics

Expected outcome:

- failures distinguish between:
  - missing hosted credentials
  - unsupported provider selection
  - unreachable hosted endpoint
  - missing local runtime
  - missing local model artifact
  - incompatible response shape from a backend

The current answer path is strict by design. Keep it strict, but make the error surfaces operationally useful.

### 6. Add verification coverage

Expected outcome:

- unit tests remain deterministic and mocked where appropriate
- provider-selection coverage includes OpenRouter
- local-managed startup logic has test coverage where feasible
- live/manual smoke steps are documented for:
  - OpenAI
  - OpenRouter
  - repo-supported local mode via Ollama

Do not claim live verification unless it was actually run.

## Documentation Work Required

After implementation, update:

- `README.md`
- `.env.example`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `QUALITY_NOTES.md`
- `PHASE_05_CLEANUP_HANDOFF.md` if you want the updated backend state reflected there

The README should explicitly document three answer-backend setup paths:

1. OpenAI hosted
2. OpenRouter hosted
3. repo-supported local lightweight model via Ollama

It should also document:

- exact environment variables
- any required prep/start command for local mode
- expected limitations of the local mode
- what was live-verified vs what is only interface-level support

## Acceptance Standard Before Phase 06

Do not start Phase 06 until the repo can honestly claim:

- the answer path supports OpenAI
- the answer path supports OpenRouter
- the repo can provide its own lightweight local model path on demand when no LLM service is already running
- the main answer text remains citation-enforced
- backend behavior and limitations are documented accurately

## Suggested Execution Order

1. inspect the current backend client abstraction and config surface
2. add OpenRouter as a first-class provider
3. choose and document the managed local runtime
4. implement prepare/start/check behavior for local mode
5. wire local mode into backend selection
6. add tests for provider selection and local-start logic
7. run or document smoke paths for OpenAI, OpenRouter, and local-managed mode
8. update docs and handoff notes

## Non-Goals

This pass should not expand into:

- reranking
- retrieval redesign
- broader eval framework work
- prompt experimentation unrelated to backend support

This is specifically about making the answer backend reviewer-safe and demo-safe.
