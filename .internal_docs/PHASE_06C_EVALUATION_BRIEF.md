# Phase 06C Evaluation Brief

## Purpose

This brief is for an evaluation-focused worker running in parallel with the Phase 06C implementation worker.

The job here is not to redesign retrieval. The job is to create lightweight, reproducible evidence that can tell the project whether metadata-aware query targeting and coverage-preserving retrieval actually improve the demo-blocking comparison failure.

## Core Rule

Treat metadata-aware query targeting as the leading next experiment based on current evidence, not as a proven root cause.

## Read First

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `README.md`
- `PHASE_06B_RERANKING_RESULTS_HANDOFF.md`
- `PHASE_06C_QUERY_TARGETING_KICKOFF.md`

## Your Ownership

You own:

- evaluation commands
- retrieval-result snapshots
- before/after comparisons
- evidence notes and recommendations

You do not own:

- broad retrieval implementation
- design pivots without evidence
- global docs cleanup unless explicitly requested after results stabilize

## Evaluation Goal

Produce a small, defensible evidence slice that can answer:

- does the new retrieval path improve named-company coverage for comparison-style questions
- does it reduce irrelevant-company contamination in final top-k
- is the project closer to final demo lock, or still blocked on retrieval quality

## Required Outputs

### 1. Representative question slice

Use a small set of representative questions emphasizing:

- explicit multi-company comparisons
- named-company risk questions
- cases where missing one named company invalidates the answer

At minimum include:

- `What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?`

### 2. Exact command capture

For every run you report, record the exact command.

Also capture the runtime settings used, including:

- retrieval mode
- `top-k`
- rerank candidate pool
- reranker on or off
- any metadata filters
- whether the run was retrieval-only or full answer generation

### 3. Result snapshots

For each reported run, summarize:

- which named companies appeared in final top-k
- whether unrelated companies entered final top-k
- whether citation coverage appears complete enough for the named entities
- whether the result is strong enough for demo use

### 4. Recommendation

Leave a concise recommendation stating one of:

- the new path materially improves the demo blocker and the project should move toward final evaluation
- the new path helps but is still not enough for demo lock
- the new path does not materially improve the main failure and another bounded retrieval step is needed

## Non-Goals

Do not:

- claim a root cause that the data does not prove
- expand into a large benchmark harness
- reopen backend reliability without a demonstrated regression
- spend time on docs polish instead of evidence capture

## Suggested Comparison Matrix

Compare, when available:

- current `hybrid + BGE rerank`
- metadata-filtered hybrid + BGE rerank
- coverage-preserving hybrid + BGE rerank

If only some variants exist by the time you run evaluation, state that explicitly rather than inferring missing results.

## Good End Artifact

A good output from this brief is a short handoff or note that includes:

- exact commands run
- concise retrieval outcomes
- whether all named entities were preserved in final top-k
- whether irrelevant-company contamination remained
- whether the repo is ready for the next demo-lock phase
