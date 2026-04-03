# Cleanup Handoff Before Phase 06

## Why This Exists

Phase 05 delivered a real answer path, but the repo is not yet tight enough to treat that path as fully trustworthy or fully documented. Before Phase 06, the next agent should harden the answer-generation contract, make backend support honest and configurable, and update docs to match reality.

## Current State

What exists now:

- retrieval stack is in place: lexical, dense, hybrid
- final prompt template exists
- `eliza-rag-answer` exists
- answer path performs retrieval first and then one final model call
- prompt iteration log and quality notes exist
- tests exist for prompt assembly / parsing happy path

What is not tight enough yet:

- top-level `answer` citations are not enforced
- live answer backend is hardcoded to OpenAI Responses API
- local models are not first-class
- docs over-imply grounding guarantees and backend flexibility
- tests do not cover the most important contract gaps

## Review Findings To Carry Forward

### 1. Grounding contract gap

The prompt requires inline citation ids in the top-level `answer`, but the parser only validates citations in `findings`.

Relevant files:

- `src/eliza_rag/answer_generation.py`
- `prompts/final_answer_prompt.txt`

Impact:

- the CLI can print a narrative answer that appears grounded without actually enforcing citations in the main answer text
- this weakens the core Phase 05 claim about citation-grounded answers

### 2. Backend is OpenAI-only, not provider-abstracted

The answer client posts directly to `https://api.openai.com/v1/responses`.

Relevant files:

- `src/eliza_rag/answer_generation.py`
- `src/eliza_rag/config.py`
- `.env.example`

Impact:

- this is not "OpenAI-compatible local models supported"
- it is one hardcoded hosted provider path
- users can change model name via env, but not provider or endpoint

### 3. Local lightweight models are not first-class

There is no config for:

- provider selection
- base URL override
- local backend docs
- local backend smoke path

Impact:

- the repo cannot honestly claim local model support yet
- if lightweight local models are required for reviewer or developer workflows, that support needs to be implemented explicitly

### 4. Tests are offline and mocked, not live answer-call verification

You do not need an OpenAI key for current tests because `tests/test_answer_generation.py` uses a fake client and patched retrieval.

Relevant file:

- `tests/test_answer_generation.py`

Impact:

- this is fine for unit coverage
- but the repo should not imply that live end-to-end answer generation has been verified unless it actually has been

## Required Pre-Phase-06 Work

### 1. Fix the answer citation contract

Implement validation so that:

- the top-level `answer` must include citation ids if the prompt requires them
- citation ids in `answer` must be known ids from the prompt context
- missing or unknown citations fail fast

Minimum target:

- enforce the same grounding discipline on `answer` that currently exists for `findings`

### 2. Expand test coverage

Add tests for:

- `answer` with no citations
- `answer` with unknown citation ids
- malformed JSON
- empty `findings`
- no retrieval results
- provider error surfaces
- backend config selection behavior

Keep these deterministic and offline where possible.

### 3. Introduce backend abstraction

Refactor final answer generation so the repo supports at least:

- hosted OpenAI mode
- configurable OpenAI-compatible local/server mode

Minimum design expectation:

- separate "answer backend client" from "OpenAI hosted implementation"
- do not leave provider selection implicit in hardcoded URL logic

### 4. Make local models a first-class supported path

Add explicit config for something like:

- `ELIZA_RAG_LLM_PROVIDER`
- `ELIZA_RAG_LLM_BASE_URL`
- `ELIZA_RAG_LLM_MODEL`
- `ELIZA_RAG_LLM_API_KEY`

OpenAI can remain the default if desired, but local-compatible execution must be intentional and documented.

### 5. Define the supported local contract honestly

Do not document "local models supported" in a vague way.

Document exactly what is supported, for example:

- OpenAI-compatible HTTP server
- expected request shape
- expected response field(s)
- whether a dummy API key is acceptable
- any limitations vs hosted OpenAI

### 6. Verify both supported modes

At minimum verify:

- hosted OpenAI path
- local-compatible path

If a local model runtime is not bundled in-repo, still make the interface first-class and provide a documented smoke command for users who run their own compatible local server.

### 7. Correct and update documentation

After code changes, update:

- `README.md`
- `.env.example`
- `QUALITY_NOTES.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `DECISIONS.md` if backend architecture changes
- `PHASE_05_HANDOFF.md` if you want the handoff corrected rather than just superseded

## Suggested Execution Order

1. inspect current `answer_generation.py`, `config.py`, and `test_answer_generation.py`
2. fix parser enforcement for top-level `answer` citations
3. add failing tests for citation/JSON/provider edge cases
4. refactor backend client to support configurable provider/base URL
5. add env/config plumbing for local-compatible mode
6. document exact supported backend modes
7. run tests and smoke checks
8. update project docs and handoff notes

## Non-Goals For This Cleanup Pass

Do not expand into:

- reranking work
- eval framework buildout
- retrieval redesign
- broad prompt experimentation

This pass is about tightening the existing Phase 05 answer path and making the docs true.

## Practical Standard

The repo should be left in a state where these statements are actually true:

- the main answer text is citation-disciplined, not just the structured findings
- backend support is accurately described
- local-compatible operation is either truly supported and documented, or clearly not claimed
- reviewers and future agents can tell exactly how live answer generation works
- Phase 06 starts from a stable, honest baseline instead of a soft contract

## One Useful Clarification

Current tests passing without an OpenAI key is expected. They are mocked unit tests, not live backend verification. That is not itself a problem, but the repo should be explicit about that distinction.
