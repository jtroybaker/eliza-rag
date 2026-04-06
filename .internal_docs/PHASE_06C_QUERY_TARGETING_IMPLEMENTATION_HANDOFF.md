# Phase 06C Implementation Handoff

## Implemented

- added an explicit `targeted_hybrid` retrieval mode
- added deterministic company and ticker detection to structured query analysis
- added comparison-intent and coverage-required flags to the structured query payload
- added a coverage-preserving hybrid retrieval path that allocates candidates across named tickers before final reranking
- exposed the new mode in the public `eliza-rag-search` and `eliza-rag-answer` parsers
- added focused tests for company detection, comparison intent, and coverage-preserving retrieval ordering

## Files Touched

- `src/eliza_rag/models.py`
- `src/eliza_rag/retrieval.py`
- `src/eliza_rag/retrieval_cli.py`
- `src/eliza_rag/answer_cli.py`
- `tests/test_retrieval.py`

## Verification

Passed:

```bash
uv run ruff check src/eliza_rag/retrieval.py src/eliza_rag/retrieval_cli.py src/eliza_rag/answer_cli.py src/eliza_rag/models.py tests/test_retrieval.py
uv run python -m pytest tests/test_retrieval.py -k 'analyze_query_detects_companies_and_comparison_intent or detect_comparison_intent_is_false_for_single_company_lookup or targeted_hybrid_preserves_candidate_coverage'
uv run python -m pytest tests/test_answer_cli.py -k forwards_rerank_arguments
uv run eliza-rag-search --help
uv run eliza-rag-answer --help
uv run eliza-rag-search "Compare the main risk factors facing Apple and Tesla" --mode targeted_hybrid --top-k 4
```

Attempted but did not complete in this environment:

```bash
uv run python -m pytest tests/test_retrieval.py tests/test_answer_cli.py tests/test_answer_generation.py
```

Not end-to-end verified in this environment:

```bash
uv run eliza-rag-answer "Compare the main risk factors facing Apple and Tesla" --mode targeted_hybrid
```

## Notes For Integration

- `targeted_hybrid` is optional and does not replace the existing `hybrid` default
- query targeting uses repo corpus metadata via deterministic alias matching, not an LLM rewrite stage
- when multiple target tickers are detected, candidate collection runs per-ticker hybrid retrieval, then interleaves results before any reranker is applied
- when coverage is not clearly required, `targeted_hybrid` falls back to the normal hybrid path and only changes the surfaced retrieval mode label
- public CLI exposure was verified for both commands via `--help`
- end-to-end retrieval execution was verified for `eliza-rag-search`
- end-to-end answer execution with `eliza-rag-answer --mode targeted_hybrid` was not verified here
