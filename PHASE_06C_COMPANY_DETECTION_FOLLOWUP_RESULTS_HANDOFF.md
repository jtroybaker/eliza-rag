# Phase 06C Company Detection Follow-Up Results Handoff

## Summary

This follow-up stayed tightly scoped to deterministic company detection for metadata-backed aliases.

The key change was stronger alias normalization in query analysis:

- normalize company names with stable ordered tokenization
- strip trailing corporate suffixes such as `Inc`, `Corporation`, and `Co`
- generate inspectable prefix aliases for safe short forms such as `JPMorgan` from `JPMorgan Chase & Co`
- allow space/punctuation-insensitive matching for multi-token aliases without introducing fuzzy matching
- avoid generic single-word aliases that would overmatch prompts such as `bank`

## Prompt Variants Now Recognized

The real-corpus `analyze_query(...)` run now recognizes:

- `JPMorgan`
- `JPMorgan Chase`
- `Bank of America`
- the original Apple and Tesla prompt forms used in Phase 06C

## Exact Commands Used

Verification:

```bash
uv run ruff check src/eliza_rag/retrieval.py tests/test_retrieval.py
uv run python -m pytest tests/test_retrieval.py
```

Query-analysis inspection:

```bash
uv run python -c "from eliza_rag.config import get_settings; from eliza_rag.retrieval import analyze_query; queries=['What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?','Compare the main risk factors facing Apple and Tesla.','What are the primary risk factors facing JPMorgan and Bank of America, and how do they compare?']; settings=get_settings(); import json; print(json.dumps({q: analyze_query(q, settings=settings).to_dict() for q in queries}, indent=2))"
```

Comparison matrix re-run:

```bash
uv run python -c "from eliza_rag.config import get_settings; from eliza_rag.retrieval import retrieve; import json; settings=get_settings(); queries=[('apple_tesla_jpm','What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?', ['AAPL','TSLA','JPM']), ('apple_tesla','Compare the main risk factors facing Apple and Tesla.', ['AAPL','TSLA']), ('jpm_bac','What are the primary risk factors facing JPMorgan and Bank of America, and how do they compare?', ['JPM','BAC'])]; modes=['hybrid','targeted_hybrid']; out=[]; \
for slug,q,expected in queries: \
    for mode in modes: \
        results=retrieve(settings,q,mode=mode,top_k=8,enable_rerank=True,reranker='bge-reranker-v2-m3',rerank_candidate_pool=12); \
        tickers=[r.ticker for r in results]; \
        out.append({'query_id':slug,'mode':mode,'expected':expected,'top_tickers':tickers,'unique_tickers':sorted(set(tickers)),'covered_expected':sorted(set(expected) & set(tickers)),'missing_expected':sorted(set(expected)-set(tickers)),'unexpected_tickers':sorted(set(tickers)-set(expected)),'top_chunks':[{'rank':r.rank,'ticker':r.ticker,'chunk_id':r.chunk_id,'source_mode':r.source_retrieval_mode,'retrieval_mode':r.retrieval_mode} for r in results]}); \
print(json.dumps(out, indent=2))"
```

## Result Snapshot

### 1. Apple, Tesla, and JPMorgan

`hybrid + BGE rerank`:

- final top-k tickers: `JPM, JPM, TSLA, TSLA, TSLA, TSLA, JPM, MS`
- named-company coverage: `JPM` and `TSLA`
- missing named company: `AAPL`
- unrelated-company contamination: `MS`

`targeted_hybrid + BGE rerank`:

- final top-k tickers: `JPM, JPM, JPM, AAPL, TSLA, TSLA, TSLA, AAPL`
- named-company coverage: complete for `AAPL`, `TSLA`, and `JPM`
- unrelated-company contamination: none

### 2. Apple and Tesla

`hybrid + BGE rerank`:

- final top-k tickers: `TSLA, TSLA, MS, AXP, TSLA, MSFT, GE, GE`
- missing named company: `AAPL`

`targeted_hybrid + BGE rerank`:

- final top-k tickers: `AAPL, AAPL, AAPL, TSLA, TSLA, AAPL, AAPL, AAPL`
- named-company coverage: complete
- unrelated-company contamination: none

### 3. JPMorgan and Bank of America

`hybrid + BGE rerank`:

- final top-k tickers: `JPM, JPM, JPM, BAC, JPM, JPM, GS, MS`
- named-company coverage: complete
- unrelated-company contamination: `GS`, `MS`

`targeted_hybrid + BGE rerank`:

- final top-k tickers: `BAC, BAC, JPM, JPM, BAC, JPM, JPM, MS`
- named-company coverage: complete
- unrelated-company contamination: reduced to `MS`

## Recommendation

The main Apple/Tesla/JPMorgan blocker is now acceptable for final evaluation.

Recommended path:

- use `targeted_hybrid` with `bge-reranker-v2-m3` for named-company comparison prompts
- move to lightweight final evaluation and demo-lock preparation rather than another bounded retrieval-quality phase

## Remaining Uncertainty

- the detector is still deterministic and metadata-driven, so future misses are still possible for company aliases that are not represented clearly enough in corpus metadata
- the comparison slice improved materially, but broader alias generalization still needs to be treated as a heuristic capability rather than a guarantee
