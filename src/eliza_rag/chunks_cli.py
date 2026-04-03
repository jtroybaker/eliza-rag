from __future__ import annotations

import argparse
import json

from .chunking import materialize_chunk_records, write_chunk_artifact
from .config import get_settings
from .corpus import inspect_corpus
from .storage import load_chunk_records


def _add_common_args(parser: argparse.ArgumentParser, *, allow_artifact: bool = True) -> None:
    parser.add_argument("--limit", type=int, default=None, help="Limit filings processed for a smaller smoke test.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=3,
        help="Number of sample chunks to include in the JSON summary output.",
    )
    if allow_artifact:
        parser.add_argument(
            "--write-artifact",
            action="store_true",
            help="Write chunk rows to artifacts/chunk_records.jsonl.",
        )


def build_materialize_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize deterministic chunk rows from normalized filings.")
    _add_common_args(parser)
    return parser


def build_load_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize chunk rows and load them into a local LanceDB table.")
    _add_common_args(parser, allow_artifact=True)
    return parser


def _build_summary(chunks: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "chunk_id": chunk["chunk_id"],
            "filing_id": chunk["filing_id"],
            "section": chunk["section"],
            "chunk_index": chunk["chunk_index"],
            "text_preview": str(chunk["text"])[:200],
        }
        for chunk in chunks
    ]


def materialize_main() -> None:
    args = build_materialize_parser().parse_args()
    settings = get_settings()
    inspection, filings = inspect_corpus(settings)

    if args.limit is not None:
        filings = filings[: args.limit]

    chunks = materialize_chunk_records(filings, settings)
    payload: dict[str, object] = {
        "normalized_filing_count": len(filings),
        "chunk_count": len(chunks),
        "chunk_size_tokens": settings.chunk_size_tokens,
        "chunk_overlap_tokens": settings.chunk_overlap_tokens,
        "corpus_discovered_file_count": inspection.discovered_file_count,
        "sample_chunks": _build_summary([chunk.to_dict() for chunk in chunks[: args.sample_size]]),
    }

    if args.write_artifact:
        payload["artifact_path"] = str(write_chunk_artifact(settings, chunks))

    print(json.dumps(payload, indent=2))


def load_main() -> None:
    args = build_load_parser().parse_args()
    settings = get_settings()
    inspection, filings = inspect_corpus(settings)

    if args.limit is not None:
        filings = filings[: args.limit]

    chunks = materialize_chunk_records(filings, settings)
    payload: dict[str, object] = {
        "normalized_filing_count": len(filings),
        "chunk_count": len(chunks),
        "chunk_size_tokens": settings.chunk_size_tokens,
        "chunk_overlap_tokens": settings.chunk_overlap_tokens,
        "corpus_discovered_file_count": inspection.discovered_file_count,
        "sample_chunks": _build_summary([chunk.to_dict() for chunk in chunks[: args.sample_size]]),
    }

    if args.write_artifact:
        payload["artifact_path"] = str(write_chunk_artifact(settings, chunks))

    payload["lancedb"] = load_chunk_records(settings, chunks)
    print(json.dumps(payload, indent=2))
