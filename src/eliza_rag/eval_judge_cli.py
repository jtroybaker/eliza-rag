from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

from .config import get_settings
from .eval_judging import judge_eval_artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply an OpenRouter-backed LLM judge to a saved answer-included eval artifact."
    )
    parser.add_argument("input", help="Path to the saved eval artifact to judge.")
    parser.add_argument(
        "--output",
        default=None,
        help="Write the judged artifact to this path. Defaults to <input>_judged.json.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    payload = judge_eval_artifact(
        settings,
        input_path=Path(args.input).resolve(),
        output_path=Path(args.output).resolve() if args.output else None,
        invocation_command=shlex.join(["uv", "run", "eliza-rag-eval-judge", *sys.argv[1:]]),
    )
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
