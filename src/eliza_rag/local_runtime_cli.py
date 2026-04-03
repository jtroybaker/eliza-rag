from __future__ import annotations

import argparse
import json
import sys

from .config import get_settings
from .local_runtime import LocalRuntimeError, build_local_runtime_manager


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
        elif args.command == "start":
            status = manager.start()
        else:
            status = manager.status()
    except LocalRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc

    print(
        json.dumps(
            {
                "runtime": status.runtime,
                "command": status.command,
                "base_url": status.base_url,
                "model": status.model,
                "runtime_available": status.runtime_available,
                "server_running": status.server_running,
                "model_available": status.model_available,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
