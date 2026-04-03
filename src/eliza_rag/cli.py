from __future__ import annotations

import argparse
import json

from .config import get_settings
from .corpus import inspect_corpus, write_inspection_artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the SEC filings corpus.")
    parser.add_argument(
        "--write-artifact",
        action="store_true",
        help="Write the corpus inspection report to artifacts/corpus_inspection.json.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    inspection, filings = inspect_corpus(settings)

    payload = inspection.to_dict()
    payload["normalized_filing_count"] = len(filings)

    if args.write_artifact:
        artifact_path = write_inspection_artifact(settings, inspection)
        payload["artifact_path"] = str(artifact_path)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
