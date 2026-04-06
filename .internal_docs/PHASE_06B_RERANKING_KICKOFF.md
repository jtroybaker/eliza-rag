# Phase 06B Kickoff: Retrieval Quality With Reranking

## Purpose

Phase 06B is now the active path for the project.

The live answer path has already been tested and stabilized. The next bounded goal is to improve retrieval quality, especially for multi-company and comparison-style questions, by adding reranking ahead of the final answer call.

## Why Phase 06B Was Chosen

The current repo state already supports:

- lexical retrieval
- dense retrieval
- hybrid retrieval
- a single-call grounded answer pipeline
- a repo-supported local Ollama path

The remaining concern is answer usefulness, not basic answer-path execution.

In particular:

- correct companies can be found without the strongest excerpt ordering
- comparative questions are more sensitive to candidate ranking quality
- the current dense path is intentionally baseline-grade
- reranking is already the preferred next quality upgrade in `DECISIONS.md`

## Phase Goal

Improve retrieval quality with a bounded reranking stage and choose whether reranked retrieval should become the recommended demo path.

## Target Outcomes

- implement reranking over top retrieved candidates
- make reranking configurable rather than implicit
- compare baseline hybrid retrieval against reranked retrieval on representative questions
- document whether reranking materially improves grounded answer usefulness
- keep the one-final-call answer contract unchanged

## Expected Work

1. Add a reranking stage after initial retrieval candidate collection.
2. Decide the first owned reranker implementation and configuration surface.
3. Expose reranking in CLI and evaluation paths.
4. Test multi-company, comparison, and risk-focused questions where ranking quality matters most.
5. Update docs to state whether reranking is optional, recommended, or default.

## Non-Goals

Do not:

- reopen backend reliability work unless a regression is demonstrated
- broaden into full final-demo lock before reranking results are known
- add LLM-based query rewriting
- violate the one-final-call answer-generation requirement

## Required Documentation Updates During This Phase

Always update:

- `IMPLEMENTATION_KANBAN.md`

Update when warranted:

- `DECISIONS.md`
- `LIMITATIONS.md`
- `README.md`

Produce at phase end:

- a handoff summarizing reranking results
- a clear recommendation on whether to proceed to final evaluation/demo lock
