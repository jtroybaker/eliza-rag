# Phase 06C Follow-Up Kickoff: Stronger Deterministic Company Detection

## Purpose

This kickoff defines the next bounded follow-up inside Phase 06C.

Phase 06C established that coverage-preserving retrieval is directionally correct: `targeted_hybrid` improves top-k purity and restores missing company coverage when deterministic entity detection succeeds. The remaining blocker is narrower and more specific: deterministic company detection is still incomplete for important prompt forms, especially financial-company names such as JPMorgan-style queries.

This follow-up should stay tightly scoped to improving deterministic company and ticker detection, then re-running the same comparison slice already used in Phase 06C.

## Why This Follow-Up Was Chosen

Current repo evidence now shows:

- stronger dense embeddings plus stronger reranking were not enough on their own
- `targeted_hybrid` materially improves retrieval quality when named-company detection succeeds
- the main Apple/Tesla/JPMorgan blocker is still not solved because `JPM` was not detected in the tested prompt
- a JPMorgan/Bank of America comparison also fell back to baseline behavior because neither company was detected in the query-analysis run

The next bounded step should therefore focus on:

- stronger deterministic company alias coverage
- stronger normalization for common company-name prompt variants
- re-validation of the same comparison-style queries after that improvement

This should not become a broad redesign of retrieval or a new model-selection phase.

## Read First

Before changing code, read:

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `README.md`
- `PHASE_06C_QUERY_TARGETING_KICKOFF.md`
- `PHASE_06C_QUERY_TARGETING_IMPLEMENTATION_HANDOFF.md`
- `PHASE_06C_EVALUATION_RESULTS_HANDOFF.md`

Use repo files as the source of truth rather than prior chat context.

## Follow-Up Goal

Improve deterministic company detection enough that coverage-preserving retrieval can be judged fairly on the main multi-company comparison blocker.

## Required Outcomes

- strengthen deterministic detection of company names and aliases already represented in repo metadata
- improve matching for prompt variants such as:
  - `JPMorgan`
  - `JPMorgan Chase`
  - `Bank of America`
  - other common company-name forms that currently fail despite the ticker existing in corpus metadata
- keep detection logic deterministic and inspectable
- re-run the established Phase 06C comparison matrix after the detection changes
- leave behind exact commands and a concise result handoff

## Scope

Keep this follow-up tightly scoped to:

1. deterministic alias and normalization improvements
2. query-analysis behavior for company and ticker detection
3. tests for the new detection coverage
4. re-running the existing retrieval comparison slice

Do not broaden into:

- LLM-based query rewriting
- another reranker swap
- another embedding-model swap
- final demo lock before the comparison blocker is re-tested

## Required Outputs

### 1. Stronger deterministic company detection

Improve the current company detection path using repo-available metadata and simple deterministic matching rules.

Good targets include:

- alias normalization for punctuation, casing, and common suffix differences
- matching company-name variants that omit legal suffixes
- explicit support for common short forms that appear in natural questions

Requirements:

- no LLM planner or rewrite stage
- no opaque fuzzy-matching layer that is hard to explain
- prefer auditable matching behavior over aggressive recall with unclear errors

### 2. Focused test coverage

Add or update tests that show the detector now handles the previously failing prompt shapes.

At minimum, cover:

- Apple, Tesla, and JPMorgan comparison
- JPMorgan and Bank of America comparison
- one negative or ambiguity-sensitive case to avoid overmatching

### 3. Re-run the comparison matrix

Re-run the same comparison slice used in the current Phase 06C evaluation:

- Apple/Tesla/JPMorgan
- Apple/Tesla
- JPMorgan/Bank of America

Use the same core retrieval settings where possible so the result is comparable.

### 4. End-of-follow-up handoff

Produce a concise handoff that states:

- what detection logic changed
- which prompt variants are now recognized
- exact commands used for validation
- whether the main Apple/Tesla/JPMorgan blocker is now acceptable for final evaluation
- what still remains uncertain if the blocker is not fully solved

## Suggested Execution Order

1. inspect the current alias and detection logic
2. identify why `JPMorgan` and `Bank of America` prompt forms are missed
3. implement the smallest deterministic fix that covers the observed gap
4. add targeted tests
5. re-run the existing comparison matrix
6. document whether the blocker is resolved enough to move toward demo lock

## Recommended Commands

Start from:

```bash
uv sync --extra dev
```

Useful verification commands:

```bash
uv run ruff check src tests
uv run python -m pytest tests/test_retrieval.py
uv run eliza-rag-search "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?" --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
uv run eliza-rag-search "What are the primary risk factors facing JPMorgan and Bank of America, and how do they compare?" --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
```

If you use direct `python -c` inspection for query-analysis payloads, include those exact commands in the handoff.

## Documentation Expectations

Always update:

- `IMPLEMENTATION_KANBAN.md` if the follow-up materially changes the current phase state

Update when warranted:

- `README.md` if the recommended retrieval mode changes
- `LIMITATIONS.md` if the main comparison blocker is narrowed further or resolved
- `DECISIONS.md` only if the recommended retrieval path or demo recommendation changes

## Definition Of Done

This follow-up is done when:

- deterministic company detection covers the previously failing financial-company prompt variants
- the Phase 06C comparison matrix has been re-run with exact commands recorded
- the project can clearly say whether `targeted_hybrid` is now good enough to justify final evaluation and demo-lock work

## Decision After This Follow-Up

If the Apple/Tesla/JPMorgan blocker is resolved well enough:

- move to lightweight final evaluation and demo-lock preparation

If it is still not resolved:

- choose one more bounded retrieval-quality step based on the new evidence rather than assumption
