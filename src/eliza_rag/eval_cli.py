from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

from .config import get_settings
from .evals import emit_build_manifest, run_golden_eval


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit a build manifest and run the committed golden evaluation set."
    )
    parser.add_argument(
        "--golden-eval-path",
        default=None,
        help="Override the golden eval set path. Defaults to eval/golden_queries.json.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write the eval results JSON to this path.",
    )
    parser.add_argument(
        "--manifest-output",
        default=None,
        help="Write the build manifest JSON to this path.",
    )
    parser.add_argument(
        "--mode",
        choices=("lexical", "dense", "hybrid", "targeted_hybrid"),
        default="targeted_hybrid",
        help="Retrieval mode to use for the golden eval run.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Maximum number of chunks to return per query.",
    )
    parser.add_argument(
        "--phrase-query",
        action="store_true",
        help="Enable phrase query mode for lexical retrieval when applicable.",
    )
    parser.add_argument(
        "--include-answer",
        action="store_true",
        help="Attempt the final answer-generation call for each eval case.",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Apply the configured reranker during eval.",
    )
    parser.add_argument(
        "--reranker",
        choices=("bge-reranker-v2-m3", "bge-reranker-base", "heuristic"),
        default=None,
        help="Override the reranker implementation.",
    )
    parser.add_argument(
        "--rerank-candidate-pool",
        type=int,
        default=None,
        help="Number of candidates to collect before reranking.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    manifest_output = Path(args.manifest_output).resolve() if args.manifest_output else None
    eval_output = Path(args.output).resolve() if args.output else None
    golden_eval_path = Path(args.golden_eval_path).resolve() if args.golden_eval_path else None

    emit_build_manifest(settings, output_path=manifest_output)
    payload = run_golden_eval(
        settings,
        golden_eval_path=golden_eval_path,
        output_path=eval_output,
        manifest_output_path=manifest_output,
        mode=args.mode,
        top_k=args.top_k,
        phrase_query=args.phrase_query,
        include_answer=args.include_answer,
        enable_rerank=args.rerank or None,
        reranker=args.reranker,
        rerank_candidate_pool=args.rerank_candidate_pool,
        invocation_command=shlex.join(["uv", "run", "eliza-rag-eval", *sys.argv[1:]]),
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
