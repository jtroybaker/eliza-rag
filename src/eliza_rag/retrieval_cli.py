from __future__ import annotations

import argparse
import json
import sys

from .config import get_settings
from .models import RetrievalFilters
from .retrieval import (
    DenseIndexNotReadyError,
    LexicalIndexNotReadyError,
    analyze_query,
    index_status,
    retrieve,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run retrieval over the local LanceDB chunk tables.")
    parser.add_argument("query", help="Natural-language retrieval query.")
    parser.add_argument(
        "--mode",
        choices=("lexical", "dense", "hybrid", "targeted_hybrid"),
        default="lexical",
        help="Retrieval mode to execute.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Maximum number of ranked chunk results to return.",
    )
    parser.add_argument(
        "--ticker",
        action="append",
        dest="tickers",
        default=None,
        help="Restrict retrieval to a ticker. Repeat for multiple tickers.",
    )
    parser.add_argument(
        "--form-type",
        action="append",
        dest="form_types",
        default=None,
        help="Restrict retrieval to a filing form type such as 10-K or 10-Q.",
    )
    parser.add_argument(
        "--filing-date-from",
        default=None,
        help="Lower ISO date bound for filing_date, for example 2024-01-01.",
    )
    parser.add_argument(
        "--filing-date-to",
        default=None,
        help="Upper ISO date bound for filing_date, for example 2025-12-31.",
    )
    parser.add_argument(
        "--phrase-query",
        action="store_true",
        help="Wrap the query as a phrase query when using full-text search.",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Apply the configured reranker over the retrieved candidate pool before returning results.",
    )
    parser.add_argument(
        "--reranker",
        choices=("bge-reranker-v2-m3", "heuristic"),
        default=None,
        help="Override the reranker implementation.",
    )
    parser.add_argument(
        "--rerank-candidate-pool",
        type=int,
        default=None,
        help="Number of initial candidates to collect before reranking.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()
    filters = RetrievalFilters(
        tickers=args.tickers,
        form_types=args.form_types,
        filing_date_from=args.filing_date_from,
        filing_date_to=args.filing_date_to,
    )
    structured_query = analyze_query(args.query, filters=filters, settings=settings)
    enable_rerank = (
        args.rerank
        or args.reranker is not None
        or args.rerank_candidate_pool is not None
        or getattr(settings, "enable_rerank", False)
    )
    try:
        results = retrieve(
            settings,
            args.query,
            mode=args.mode,
            top_k=args.top_k,
            filters=filters,
            phrase_query=args.phrase_query,
            enable_rerank=enable_rerank,
            reranker=args.reranker,
            rerank_candidate_pool=args.rerank_candidate_pool,
        )
    except (DenseIndexNotReadyError, LexicalIndexNotReadyError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
    payload = {
        "query": args.query,
        "retrieval_mode": args.mode,
        "top_k": args.top_k or settings.retrieval_top_k,
        "filters": filters.to_dict(),
        "reranking": {
            "enabled": enable_rerank,
            "reranker": args.reranker,
            "candidate_pool": args.rerank_candidate_pool,
        },
        "structured_query": structured_query.to_dict(),
        "index_status": index_status(settings),
        "result_count": len(results),
        "results": [result.to_dict() for result in results],
    }
    print(json.dumps(payload, indent=2))
