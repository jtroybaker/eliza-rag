# Phase 06C Evaluation Results Handoff

## Purpose

This note captures a small, reproducible evaluation slice for Phase 06C.

The goal was to test whether the new metadata-aware, coverage-preserving retrieval path materially improves named-company coverage for comparison-style questions, especially the main Apple/Tesla/JPMorgan demo blocker.

## Scope And Runtime Settings

All reported runs were retrieval-only.

Shared settings across the comparison runs:

- `top-k=8`
- reranking enabled
- reranker: `bge-reranker-v2-m3`
- rerank candidate pool: `12`
- metadata filters: none
- phrase query: off

Important current repo-state note:

- current repo behavior was re-verified directly with `uv run eliza-rag-search --help` and `uv run eliza-rag-answer --help`
- both public CLIs now expose `--mode targeted_hybrid`
- the targeted retrieval evidence in this handoff was gathered against an earlier partial repo state, when I exercised the same mode through the direct `retrieve(..., mode='targeted_hybrid')` entrypoint

## Exact Commands

Query-analysis inspection:

```bash
uv run python -c "from eliza_rag.config import get_settings; from eliza_rag.retrieval import analyze_query; queries=['What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?','Compare the main risk factors facing Apple and Tesla.','What are the primary risk factors facing JPMorgan and Bank of America, and how do they compare?']; settings=get_settings(); import json; print(json.dumps({q: analyze_query(q, settings=settings).to_dict() for q in queries}, indent=2))"
```

Baseline CLI run for the main blocker:

```bash
uv run eliza-rag-search "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?" --mode hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
```

Equivalent current CLI command for the targeted main-blocker run:

```bash
uv run eliza-rag-search "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?" --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
```

Original targeted command used when the evidence below was captured:

```bash
uv run python -c "from eliza_rag.config import get_settings; from eliza_rag.retrieval import retrieve; import json; q='What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?'; settings=get_settings(); results=retrieve(settings, q, mode='targeted_hybrid', top_k=8, enable_rerank=True, reranker='bge-reranker-v2-m3', rerank_candidate_pool=12); print(json.dumps({'query': q, 'retrieval_mode': 'targeted_hybrid', 'top_k': 8, 'reranking': {'enabled': True, 'reranker': 'bge-reranker-v2-m3', 'candidate_pool': 12}, 'result_count': len(results), 'results': [r.to_dict() for r in results]}, indent=2))"
```

Compact comparison matrix:

```bash
uv run python -c "from eliza_rag.config import get_settings; from eliza_rag.retrieval import retrieve; import json; settings=get_settings(); queries=[('apple_tesla_jpm','What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?', ['AAPL','TSLA','JPM']), ('apple_tesla','Compare the main risk factors facing Apple and Tesla.', ['AAPL','TSLA']), ('jpm_bac','What are the primary risk factors facing JPMorgan and Bank of America, and how do they compare?', ['JPM','BAC'])]; modes=['hybrid','targeted_hybrid']; out=[]; \
for slug,q,expected in queries: \
    for mode in modes: \
        results=retrieve(settings,q,mode=mode,top_k=8,enable_rerank=True,reranker='bge-reranker-v2-m3',rerank_candidate_pool=12); \
        tickers=[r.ticker for r in results]; \
        out.append({'query_id':slug,'mode':mode,'expected':expected,'top_tickers':tickers,'unique_tickers':sorted(set(tickers)),'covered_expected':sorted(set(expected) & set(tickers)),'missing_expected':sorted(set(expected)-set(tickers)),'unexpected_tickers':sorted(set(tickers)-set(expected)),'top_chunks':[{'rank':r.rank,'ticker':r.ticker,'chunk_id':r.chunk_id,'source_mode':r.source_retrieval_mode,'retrieval_mode':r.retrieval_mode} for r in results]}); \
print(json.dumps(out, indent=2))"
```

## Observed Query-Targeting Behavior

The direct `analyze_query(..., settings=get_settings())` run showed:

- Apple/Tesla/JPMorgan: detected `AAPL` and `TSLA`, but not `JPM`
- Apple/Tesla: detected `AAPL` and `TSLA`
- JPMorgan/Bank of America: detected neither company

Interpretation:

- the new targeting path is real
- but company detection is still incomplete for financial-company names used in the tested prompts
- this directly limits how much `targeted_hybrid` can help on the main blocker

## Result Snapshots

### 1. Main blocker: Apple, Tesla, and JPMorgan

Baseline `hybrid + BGE rerank`:

- final top-k tickers: `JPM, JPM, TSLA, BAC, TSLA, AMZN, JPM, AXP`
- named-company coverage: `JPM` and `TSLA` only
- missing named company: `AAPL`
- unrelated-company contamination: `BAC`, `AMZN`, `AXP`
- demo-readiness: not acceptable

Targeted `targeted_hybrid + BGE rerank`:

- final top-k tickers: `TSLA, AAPL, AAPL, AAPL, TSLA, TSLA, AAPL, TSLA`
- named-company coverage: `AAPL` and `TSLA` only
- missing named company: `JPM`
- unrelated-company contamination: none in final top-k
- demo-readiness: still not acceptable, because one required named company is still absent

Interpretation:

- the new path materially improves contamination and restores Apple coverage
- it does not solve the full comparison failure because JPMorgan is not detected and therefore not preserved

### 2. Two-company comparison: Apple and Tesla

Baseline `hybrid + BGE rerank`:

- final top-k tickers: `AAPL, TSLA, TSLA, BAC, TSLA, MSFT, GE, MS`
- named-company coverage: complete for `AAPL` and `TSLA`
- unrelated-company contamination: `BAC`, `MSFT`, `GE`, `MS`
- demo-readiness: borderline for retrieval-only inspection, but still noisy

Targeted `targeted_hybrid + BGE rerank`:

- final top-k tickers: `AAPL, AAPL, AAPL, AAPL, TSLA, TSLA, AAPL, TSLA`
- named-company coverage: complete for `AAPL` and `TSLA`
- unrelated-company contamination: none in final top-k
- demo-readiness: much stronger than baseline for this narrower case

Interpretation:

- when company detection succeeds, the targeted path clearly improves final top-k purity

### 3. Financial comparison: JPMorgan and Bank of America

Baseline `hybrid + BGE rerank`:

- final top-k tickers: `JPM, JPM, JPM, BAC, JPM, JPM, BAC, RTX`
- named-company coverage: complete for `JPM` and `BAC`
- unrelated-company contamination: `RTX`

Targeted `targeted_hybrid + BGE rerank`:

- final top-k tickers: `JPM, JPM, JPM, BAC, JPM, JPM, BAC, RTX`
- named-company coverage: complete for `JPM` and `BAC`
- unrelated-company contamination: `RTX`

Interpretation:

- no meaningful change was observed
- consistent with the query-analysis run, this appears to be a fallback-to-baseline case because the detector did not identify either company name

## Recommendation

Recommendation:

- the new path helps but is still not enough for demo lock

Reason:

- on the required Apple/Tesla/JPMorgan comparison, `targeted_hybrid` removes unrelated-company contamination and restores Apple, but it still fails to preserve all named companies in final top-k
- the remaining gap is now narrower and more specific: company detection and targeting coverage are still incomplete for some important names, especially the JPMorgan-style financial-company prompts tested here

## Bottom Line

Phase 06C appears directionally correct.

Evidence from this slice suggests:

- coverage-preserving retrieval is a real improvement when entity detection succeeds
- the repo is not yet ready to move to final demo evaluation for the main three-company blocker
- the next bounded retrieval step should stay focused on improving deterministic company detection and then re-running this same comparison matrix
