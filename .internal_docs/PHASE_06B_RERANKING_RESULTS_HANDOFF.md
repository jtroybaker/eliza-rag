# Phase 06B Reranking Results Handoff

## Purpose

This handoff captures what was actually implemented and observed during Phase 06B so the next session can choose the right follow-on step from repo state rather than chat memory.

## What Changed In This Phase

The repo now includes:

- explicit reranking controls in `eliza-rag-search` and `eliza-rag-answer`
- a configurable rerank candidate pool
- preserved source retrieval mode metadata after reranking
- a fallback deterministic `heuristic` reranker
- a model-backed default reranker using `BAAI/bge-reranker-v2-m3`
- a default dense embedding model using the Hugging Face repo `Snowflake/snowflake-arctic-embed-xs`
- retained support for the older `hashed_v1` dense embedding path as a baseline fallback

## Verification Completed

Verified during this phase:

- `uv run ruff check src tests`
- `uv run python -m pytest tests/test_embeddings.py tests/test_retrieval.py tests/test_answer_generation.py tests/test_local_runtime.py`
- `uv run python -m pytest tests/test_retrieval.py tests/test_answer_cli.py tests/test_retrieval_cli.py`

The focused reranker tests passed after the BGE reranker became the default reranker.

## Live Retrieval Outcomes

Primary live question used during this phase:

- `What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?`

### Before the model upgrades

With the older hashed dense path and heuristic reranking:

- top results were dominated by Tesla and JPMorgan
- Apple did not appear in the final top-k
- the answer model still mentioned Apple despite no Apple citation in the retrieved context

Interpretation:

- the pipeline executed successfully
- answer quality was not good enough because retrieval coverage was incomplete

### After upgrading the dense model

The active dense metadata now shows:

- model: `Snowflake/snowflake-arctic-embed-xs`
- dimension: `384`

However, live retrieval quality on the comparison question still did not become acceptable by embeddings alone.

### After upgrading the reranker

The repo was updated to use:

- reranker: `BAAI/bge-reranker-v2-m3`

Live retrieval after the BGE reranker change still showed:

- Apple missing from the final top-k
- final reranked context still dominated by JPMorgan and Tesla
- one live run admitted an unrelated Bank of America chunk into the top-k

Interpretation:

- the remaining problem is not simply "we only had a weak reranker"
- the current evidence suggests the remaining gap may involve candidate coverage and query understanding
- other causes are not yet ruled out, including hybrid fusion behavior, retrieval parameter choices, and chunk-selection dynamics

## Main Conclusion

Phase 06B achieved the implementation goal of adding real reranking and stronger dense retrieval, but it did not achieve the product goal of making multi-company comparison retrieval strong enough for demo lock.

Reranking should not be treated as the final fix.

## Recommended Next Step

The next bounded retrieval-quality step should be:

- metadata-aware query parsing or self-query-style constraint inference

This should be treated as the leading next experiment, not a proven root-cause fix.

The likely goal is to infer:

- named companies or tickers from the query
- whether the question is explicitly comparative
- whether the retrieval stage should preserve one-or-more candidates per named company before final reranking

Recommended retrieval direction:

- use parsed company/ticker constraints to drive filtered or coverage-preserving hybrid retrieval
- rerank only after candidate coverage is preserved

Observed facts that support this direction:

- stronger dense embeddings alone did not make the comparison question acceptable
- a stronger reranker alone still left Apple out of the final top-k in live testing
- one live run still admitted an unrelated Bank of America chunk into the top-k

What is not yet proven:

- that query understanding is the only remaining issue
- that chunking, fusion strategy, or retrieval parameter tuning would not materially help

This is a better next move than:

- swapping to yet another reranker first
- assuming stronger embeddings alone will fix multi-company coverage
- locking the final demo path now

## Recommendation On Demo Progression

Recommendation:

- do not proceed directly to final evaluation or demo lock yet

Reason:

- the main comparison-style retrieval failure is still live even after stronger dense and rerank components were introduced

## What The Next Agent Should Read

Start with:

- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `README.md`
- `PHASE_06B_RERANKING_KICKOFF.md`
- this file

## Suggested Next-Phase Framing

Suggested next phase:

- metadata-aware query parsing and filtered hybrid retrieval

Suggested first experiment:

- detect named companies or tickers in the query
- ensure the candidate pool keeps coverage across those named entities
- compare:
  - current hybrid plus BGE rerank
  - metadata-filtered hybrid plus BGE rerank
  - coverage-preserving hybrid plus BGE rerank
