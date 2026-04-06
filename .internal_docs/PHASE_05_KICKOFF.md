# Phase 05 Kickoff

## Phase Goal

Turn the current retrieval system into a minimally complete end-to-end RAG demo that satisfies the core assignment requirement: answer a business question about SEC filings using retrieved context in exactly one final LLM API call.

This phase should move the repository from "working retrieval modes" to "runnable question-to-answer demo" without overbuilding a full production system.

## Phase 04 Assessment

Phase 04 was successful and completed its intended scope.

Completed and verified:

- dense retrieval is implemented over a dedicated LanceDB table
- retrieval now supports `lexical`, `dense`, and `hybrid` behind a shared interface
- structured query-analysis hooks exist for later expansion work
- retrieval tests passed on `2026-04-02`
- dense and hybrid retrieval now fail with explicit prerequisite guidance when the dense index is missing

Important current system facts:

- lexical retrieval remains the most trustworthy baseline
- dense retrieval currently uses a deterministic hashed embedding workflow
- hybrid retrieval is available and likely the most defensible multi-mode retrieval starting point
- there is still no final answer pipeline, prompt template, or one-command demo flow

Conclusion:

- the retrieval foundation is sufficient to start answer generation
- the main remaining work is assembling a reviewer-usable end-to-end demo path

## Read First

Before changing code, read:

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `PHASE_04_HANDOFF.md`
- the answer-generation, query-handling, reranking, and evaluation sections of `HIGH_LEVEL_PLAN.md`
- the assignment summary in `prompt.txt`

Use the repo files as the source of truth rather than prior chat context.

## Scope For Phase 05

Keep this phase tightly scoped to:

1. final prompt template
2. single-call answer generation pipeline
3. runnable end-to-end demo command
4. minimal citation and grounding behavior
5. example request and prompt-iteration documentation
6. lightweight quality notes tied to the assignment examples

Do not expand into a large eval framework, UI buildout, or broad retrieval redesign unless a blocker appears.

## Required Outputs

### 1. Final prompt template

Create the first real answer-generation prompt template for the demo.

Requirements:

- inject retrieved context into one final LLM request
- instruct the model to answer only from provided filing evidence
- require explicit uncertainty behavior when evidence is insufficient
- require citation references back to retrieved chunks or filings
- support comparison-style business questions

Expectation:

- keep the prompt inspectable and easy to explain live
- log prompt iterations rather than leaving prompt changes implicit

### 2. Single-call answer pipeline

Implement an end-to-end pipeline that:

- accepts a natural-language business question
- runs retrieval beforehand
- formats the retrieved context for prompting
- executes exactly one final LLM API call
- returns a structured grounded answer

Requirements:

- no multi-step answer synthesis loop
- retrieval remains external to the final answer call
- one clear code path should own prompt assembly and answer generation

### 3. Runnable demo command

Add a reviewer-usable command path for the full question-to-answer flow.

Requirements:

- one documented command that can be run after setup
- obvious environment requirements for API access
- output that is readable in a terminal session

Good target:

- one CLI command for retrieval-only remains available
- one separate CLI command for final answer generation becomes the primary demo path

### 4. Citation and grounding behavior

Implement a minimal but defensible citation scheme.

Requirements:

- each answer should cite the supporting retrieved evidence
- citations should map back to preserved retrieval metadata
- the answer should distinguish supported findings from uncertainty or absence of evidence

This does not need to become a polished rendering system yet.

### 5. Prompt iteration log and example request

Add the deliverables the assignment explicitly asks for.

Requirements:

- a prompt iteration log with what changed and why
- a final prompt template saved in-repo
- at least one example request ready to execute end to end

### 6. Lightweight quality notes

Document how quality was checked for the current submission candidate.

This can be lightweight, but it should cover:

- what business-question examples were tried
- what retrieval mode was used
- where the current pipeline is weak
- why the chosen demo path is still defensible

## Nice-To-Have, But Not Required

- a small reranking stage if it clearly improves answer quality without sprawl
- deterministic company-name-to-ticker normalization if sample questions need it
- answer output in a machine-readable envelope alongside plain text
- a tiny canned evaluation note comparing `lexical` vs `hybrid` for the demo questions

## Explicit Non-Goals

Do not spend this phase on:

- a full web UI
- a large benchmark harness
- exhaustive prompt experimentation
- advanced agentic query rewriting
- replacing the dense embedding baseline unless it is absolutely necessary for demo viability

Those belong to later optimization phases.

## Suggested Execution Order

1. inspect the current retrieval CLI and models
2. decide the default retrieval mode for the end-to-end demo
3. implement prompt-template storage and prompt assembly
4. add the single-call answer generation module
5. add a CLI command for question-to-answer execution
6. run a few assignment-style questions and inspect grounding quality
7. record prompt iterations and example requests
8. update README and handoff docs

## Recommended Commands

Start from:

```bash
uv sync --extra dev
```

Useful verification commands:

```bash
uv run python -m compileall src scripts tests
uv run --extra dev pytest tests/test_retrieval.py
uv run eliza-rag-search "What are the primary risk factors facing Apple and Tesla?" --mode hybrid --top-k 6
```

If a new answer-generation CLI entry point is added in this phase, document it prominently in `README.md`.

## Documentation Updates Required

At the end of Phase 05:

- update `IMPLEMENTATION_KANBAN.md`
- write a `PHASE_05_HANDOFF.md`
- update `README.md` with the end-to-end demo command
- add the final prompt template to the repo
- add a prompt-iteration log to the repo
- update `LIMITATIONS.md` if answer-generation caveats appear
- update `DECISIONS.md` only if a real design choice changes

## Definition Of Done

Phase 05 is done when:

- the repo can accept a natural-language business question and return an answer via one final LLM API call
- the answer path uses retrieved SEC filing context and provides citations
- the demo command is documented and runnable by a reviewer with setup completed
- the repo includes a final prompt template, prompt-iteration log, and example request
- lightweight quality notes exist for the chosen demo path

## Phase 06 Preview

The next phase should likely focus on:

- reranking if it materially improves answer quality
- stronger deterministic query analysis for company and time constraints
- lightweight evaluation comparisons across retrieval modes
- final submission polish and reviewer ergonomics
