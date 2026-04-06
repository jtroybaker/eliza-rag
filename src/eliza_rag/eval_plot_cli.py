from __future__ import annotations

import argparse
from pathlib import Path

from .config import get_settings
from .eval_visualization import generate_eval_plot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a seaborn-based plot from saved eval JSON artifacts."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional explicit eval artifact paths. Defaults to all eval/*.json artifacts except the golden set.",
    )
    parser.add_argument(
        "--output",
        default="eval/provider_eval_visualization.png",
        help="PNG output path for the generated plot.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    explicit_paths = [Path(path).resolve() for path in args.paths]
    output_path = Path(args.output).resolve()
    generate_eval_plot(
        settings.eval_dir,
        output_path=output_path,
        explicit_paths=explicit_paths or None,
    )
    print(output_path)


if __name__ == "__main__":
    main()
