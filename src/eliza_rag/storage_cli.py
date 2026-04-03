from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta

from .config import get_settings
from .storage import create_lancedb_archive, compact_lancedb_tables, fetch_hosted_lancedb, fetch_lancedb_archive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain or fetch LanceDB artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compact_parser = subparsers.add_parser(
        "compact",
        help="Compact LanceDB tables and clean up old versions.",
    )
    compact_parser.add_argument(
        "--table-name",
        action="append",
        dest="table_names",
        default=None,
        help="Specific table name to compact. Repeat to compact multiple tables.",
    )
    compact_parser.add_argument(
        "--cleanup-older-than-hours",
        type=int,
        default=None,
        help="Only delete versions older than this many hours. Defaults to LanceDB's full cleanup behavior.",
    )
    compact_parser.add_argument(
        "--optimize",
        action="store_true",
        help="Run LanceDB optimize after compaction and cleanup.",
    )
    compact_parser.add_argument(
        "--delete-unverified",
        action="store_true",
        help="Also delete recent unverified files. Use this right after a local rebuild when no other process is using the database.",
    )

    fetch_parser = subparsers.add_parser(
        "fetch-hosted",
        help="Download a hosted LanceDB snapshot into the configured local database path.",
    )
    fetch_parser.add_argument(
        "--force-download",
        action="store_true",
        help="Redownload files even when Hugging Face already has them cached locally.",
    )
    fetch_parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Use only already-cached files and fail instead of reaching the network.",
    )

    archive_parser = subparsers.add_parser(
        "package-archive",
        help="Create a ZIP archive containing the local LanceDB directory plus dense metadata.",
    )
    archive_parser.add_argument(
        "--output-path",
        default=None,
        help="Override the output ZIP path. Defaults to artifacts/lancedb-demo.zip.",
    )

    archive_fetch_parser = subparsers.add_parser(
        "fetch-archive",
        help="Download or restore a ZIP archive containing `data/lancedb` and dense metadata.",
    )
    archive_fetch_parser.add_argument(
        "--archive-url",
        default=None,
        help="HTTP(S) URL or local path to a ZIP archive. Defaults to ELIZA_RAG_LANCEDB_ARCHIVE_URL.",
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()

    if args.command == "compact":
        cleanup_older_than = (
            timedelta(hours=args.cleanup_older_than_hours)
            if args.cleanup_older_than_hours is not None
            else None
        )
        try:
            payload = compact_lancedb_tables(
                settings,
                table_names=args.table_names,
                cleanup_older_than=cleanup_older_than,
                optimize=args.optimize,
                delete_unverified=args.delete_unverified,
            )
        except ImportError as exc:
            if "pylance" not in str(exc).lower() and "lance" not in str(exc).lower():
                raise
            print(
                "LanceDB compaction requires the optional `pylance` package. "
                "Run `uv sync` after pulling the updated project dependencies, "
                "or install it directly with `uv add pylance`, then rerun "
                "`uv run eliza-rag-storage compact --optimize`.",
                file=sys.stderr,
            )
            raise SystemExit(2) from exc
    elif args.command == "fetch-hosted":
        payload = fetch_hosted_lancedb(
            settings,
            force_download=args.force_download,
            local_files_only=args.local_files_only,
        )
    elif args.command == "package-archive":
        payload = create_lancedb_archive(
            settings,
            output_path=None if args.output_path is None else settings.repo_root / args.output_path,
        )
    else:
        payload = fetch_lancedb_archive(
            settings,
            archive_url=args.archive_url,
        )

    print(json.dumps(payload, indent=2))
