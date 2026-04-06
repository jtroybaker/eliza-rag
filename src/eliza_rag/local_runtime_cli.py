from __future__ import annotations

import argparse
import json
import sys

from .config import get_settings
from .local_runtime import LocalRuntimeError, build_local_runtime_manager
from .retrieval import warm_retrieval_models


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, start, and inspect the repo-supported Ollama local runtime."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser(
        "prepare",
        help="Start the local runtime if needed and pull the configured model.",
    )
    prepare_parser.add_argument(
        "--skip-pull",
        action="store_true",
        help="Only start the local runtime and skip model pull.",
    )
    prepare_parser.add_argument(
        "--skip-retrieval-warmup",
        action="store_true",
        help="Skip preloading retrieval-time embedding and reranker models.",
    )

    subparsers.add_parser(
        "start",
        help="Start the local runtime if it is not already running.",
    )
    subparsers.add_parser(
        "status",
        help="Report whether the runtime is installed, running, and model-ready.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()
    manager = build_local_runtime_manager(settings)

    try:
        if args.command == "prepare":
            status = manager.prepare(pull=not args.skip_pull)
            retrieval_warmup = None
            if not args.skip_retrieval_warmup:
                try:
                    retrieval_warmup = warm_retrieval_models(settings)
                except RuntimeError as exc:
                    raise LocalRuntimeError(f"Failed to warm retrieval models: {exc}") from exc
        elif args.command == "start":
            status = manager.start()
            retrieval_warmup = None
        else:
            status = manager.status()
            retrieval_warmup = None
    except LocalRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc

    payload = {
        "runtime": status.runtime,
        "command": status.command,
        "base_url": status.base_url,
        "model": status.model,
        "runtime_available": status.runtime_available,
        "server_running": status.server_running,
        "model_available": status.model_available,
    }
    if args.command == "prepare":
        payload["retrieval_warmup"] = retrieval_warmup
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
