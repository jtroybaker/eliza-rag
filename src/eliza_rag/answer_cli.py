from __future__ import annotations

import argparse
import json
import sys

from .answer_generation import AnswerGenerationError, generate_answer
from .config import get_settings
from .models import RetrievalFilters
from .retrieval import DenseIndexNotReadyError, LexicalIndexNotReadyError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the end-to-end SEC filings RAG demo with one final LLM API call."
    )
    parser.add_argument("question", help="Natural-language business question to answer.")
    parser.add_argument(
        "--mode",
        choices=("lexical", "dense", "hybrid", "targeted_hybrid"),
        default="hybrid",
        help="Retrieval mode to use before the final answer call.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Maximum number of retrieved chunks to inject into the final prompt.",
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
        help="Wrap the lexical query as a phrase query when full-text search is used.",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Apply the configured reranker over the retrieved candidate pool before the final answer call.",
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full answer payload as JSON instead of a terminal summary.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include summary, findings, and metadata in the terminal output.",
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
    enable_rerank = (
        args.rerank
        or args.reranker is not None
        or args.rerank_candidate_pool is not None
        or getattr(settings, "enable_rerank", False)
    )

    try:
        response = generate_answer(
            settings,
            args.question,
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
    except AnswerGenerationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc

    if args.json:
        print(json.dumps(response.to_dict(), indent=2))
        return

    print("Answer:")
    print(response.answer)
    print()
    print("Citations:")
    for citation in response.citations:
        company = citation.company_name or citation.ticker
        section = citation.section or "unknown"
        print(
            f"- {citation.citation_id}: {company} {citation.form_type} {citation.filing_date} "
            f"{section} ({citation.chunk_id})"
        )
    if not args.verbose:
        return

    print()
    print(f"Question: {response.question}")
    print(f"Model: {response.model}")
    print(f"Retrieval mode: {response.retrieval_mode}")
    print()
    print("Summary:")
    print(response.summary)
    print()
    print("Findings:")
    for finding in response.findings:
        print(f"- {finding.statement} [{' '.join(finding.citations)}]")
    print()
    print("Uncertainty:")
    print(response.uncertainty)


if __name__ == "__main__":
    main()
