from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace

from .config import get_settings
from .storage import build_dense_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or refresh the dense retrieval table from the lexical chunk table."
    )
    parser.add_argument(
        "--embedding-model",
        default=None,
        help="Override the dense embedding model for this build, for example `Snowflake/snowflake-arctic-embed-xs`.",
    )
    parser.add_argument(
        "--dense-table-name",
        default=None,
        help="Override the dense LanceDB table name so alternate embedding builds can coexist.",
    )
    parser.add_argument(
        "--metadata-artifact-name",
        default=None,
        help="Override the metadata artifact filename so alternate embedding builds can coexist.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    if args.embedding_model or args.dense_table_name or args.metadata_artifact_name:
        settings = replace(
            settings,
            dense_embedding_model=args.embedding_model or settings.dense_embedding_model,
            dense_lancedb_table_name=args.dense_table_name or settings.dense_lancedb_table_name,
            dense_index_artifact_name=args.metadata_artifact_name or settings.dense_index_artifact_name,
        )
    try:
        payload = build_dense_index(settings)
    except (FileNotFoundError, ValueError) as exc:
        message = (
            "Dense index build requires the lexical chunk table to exist first. "
            "Run `uv run eliza-rag-load-chunks` before `uv run eliza-rag-build-dense-index`."
        )
        print(message, file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(payload, indent=2))
