from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import get_settings
from .eval_reporting import build_eval_report, discover_eval_artifacts, render_markdown_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a read-only report from saved eval JSON artifacts."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional explicit eval artifact paths. Defaults to all eval/*.json artifacts except the golden set.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write the rendered report to this path instead of only printing it.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format for the report.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    explicit_paths = [Path(path).resolve() for path in args.paths]
    artifact_paths = discover_eval_artifacts(settings.eval_dir, explicit_paths or None)
    report = build_eval_report(artifact_paths)
    rendered = (
        json.dumps(report, indent=2)
        if args.format == "json"
        else render_markdown_report(report)
    )

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

    print(rendered)


if __name__ == "__main__":
    main()
