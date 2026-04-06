from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlparse
from urllib.request import urlretrieve
import zipfile

import pyarrow as pa
import lancedb

from .config import Settings
from .embeddings import (
    DenseIndexMetadata,
    build_dense_vectors,
    resolve_embedder_alias,
    resolve_embedder_model,
    write_dense_index_metadata,
)
from .models import ChunkRecord


def chunk_table_schema() -> pa.Schema:
    return pa.schema(
        [
            ("chunk_id", pa.string()),
            ("filing_id", pa.string()),
            ("ticker", pa.string()),
            ("company_name", pa.string()),
            ("form_type", pa.string()),
            ("filing_date", pa.string()),
            ("fiscal_period", pa.string()),
            ("source_path", pa.string()),
            ("section", pa.string()),
            ("section_path", pa.string()),
            ("chunk_index", pa.int32()),
            ("text", pa.string()),
        ]
    )


def chunk_rows(chunks: list[ChunkRecord]) -> list[dict[str, object]]:
    return [chunk.to_dict() for chunk in chunks]


def load_chunk_records(settings: Settings, chunks: list[ChunkRecord]) -> dict[str, object]:
    settings.lancedb_dir.mkdir(parents=True, exist_ok=True)
    database = lancedb.connect(settings.lancedb_dir)
    table = database.create_table(
        settings.lancedb_table_name,
        data=chunk_rows(chunks),
        schema=chunk_table_schema(),
        mode="overwrite",
    )
    return {
        "database_path": str(settings.lancedb_dir),
        "table_name": settings.lancedb_table_name,
        "row_count": table.count_rows(),
        "schema": table.schema.names,
    }


def dense_chunk_table_schema(*, dimension: int) -> pa.Schema:
    return pa.schema(
        [
            ("chunk_id", pa.string()),
            ("filing_id", pa.string()),
            ("ticker", pa.string()),
            ("company_name", pa.string()),
            ("form_type", pa.string()),
            ("filing_date", pa.string()),
            ("fiscal_period", pa.string()),
            ("source_path", pa.string()),
            ("section", pa.string()),
            ("section_path", pa.string()),
            ("chunk_index", pa.int32()),
            ("text", pa.string()),
            ("vector", pa.list_(pa.float32(), dimension)),
        ]
    )


def build_dense_index(settings: Settings) -> dict[str, object]:
    database = lancedb.connect(settings.lancedb_dir)
    chunk_table = database.open_table(settings.lancedb_table_name)
    chunk_rows = chunk_table.to_arrow().to_pylist()
    texts = [str(row["text"]) for row in chunk_rows]
    metadata, vectors = build_dense_vectors(settings, texts)
    dense_rows = [
        {
            **row,
            "vector": vector,
        }
        for row, vector in zip(chunk_rows, vectors, strict=True)
    ]

    dense_table = database.create_table(
        settings.dense_lancedb_table_name,
        data=dense_rows,
        schema=dense_chunk_table_schema(dimension=metadata.dimension),
        mode="overwrite",
    )
    dense_table.create_index(
        metric=settings.dense_index_metric,
        vector_column_name="vector",
        replace=True,
        index_type="IVF_HNSW_PQ",
        name="vector_idx",
    )
    metadata_path = write_dense_index_metadata(settings.dense_index_artifact_path, metadata)
    return {
        "database_path": str(settings.lancedb_dir),
        "source_table_name": settings.lancedb_table_name,
        "table_name": settings.dense_lancedb_table_name,
        "row_count": dense_table.count_rows(),
        "schema": dense_table.schema.names,
        "embedder": resolve_embedder_alias(settings.dense_embedding_model),
        "embedding_model": resolve_embedder_model(settings.dense_embedding_model),
        "embedding_dimension": metadata.dimension,
        "index_metric": settings.dense_index_metric,
        "metadata_path": str(metadata_path),
    }


def compact_lancedb_tables(
    settings: Settings,
    *,
    table_names: list[str] | None = None,
    cleanup_older_than: timedelta | None = None,
    optimize: bool = False,
    delete_unverified: bool = False,
) -> dict[str, object]:
    database = lancedb.connect(settings.lancedb_dir)
    selected_table_names = table_names or [
        settings.lancedb_table_name,
        settings.dense_lancedb_table_name,
    ]
    tables: list[dict[str, object]] = []

    for table_name in selected_table_names:
        try:
            table = database.open_table(table_name)
        except (FileNotFoundError, ValueError):
            tables.append(
                {
                    "table_name": table_name,
                    "table_exists": False,
                }
            )
            continue

        before_version = table.version
        before_count = table.count_rows()
        compaction = table.compact_files()
        cleanup = table.cleanup_old_versions(
            older_than=cleanup_older_than,
            delete_unverified=delete_unverified,
        )
        if optimize:
            table.optimize(
                cleanup_older_than=cleanup_older_than,
                delete_unverified=delete_unverified,
            )

        tables.append(
            {
                "table_name": table_name,
                "table_exists": True,
                "row_count": before_count,
                "version_before": before_version,
                "version_after": table.version,
                "fragments_removed": getattr(compaction, "fragments_removed", None),
                "files_removed": getattr(cleanup, "bytes_removed", None),
                "old_versions_removed": getattr(cleanup, "old_versions", None),
                "optimize_requested": optimize,
                "delete_unverified": delete_unverified,
            }
        )

    return {
        "database_path": str(settings.lancedb_dir),
        "tables": tables,
    }


def fetch_hosted_lancedb(
    settings: Settings,
    *,
    force_download: bool = False,
    local_files_only: bool = False,
) -> dict[str, object]:
    if not settings.lancedb_remote_repo_id:
        raise ValueError(
            "Hosted LanceDB download is not configured. Set `ELIZA_RAG_LANCEDB_REMOTE_REPO_ID` first."
        )

    from huggingface_hub import snapshot_download

    settings.lancedb_dir.mkdir(parents=True, exist_ok=True)
    local_path = Path(
        snapshot_download(
            repo_id=settings.lancedb_remote_repo_id,
            repo_type=settings.lancedb_remote_repo_type,
            revision=settings.lancedb_remote_revision,
            local_dir=settings.lancedb_dir,
            token=settings.lancedb_remote_token,
            force_download=force_download,
            local_files_only=local_files_only,
        )
    )
    metadata_payload = ensure_dense_metadata_artifact(settings)
    return {
        "repo_id": settings.lancedb_remote_repo_id,
        "repo_type": settings.lancedb_remote_repo_type,
        "revision": settings.lancedb_remote_revision,
        "local_path": str(local_path),
        "database_path": str(settings.lancedb_dir),
        "dense_metadata": metadata_payload,
    }


def prepare_lancedb_artifacts(settings: Settings, *, require_dense: bool = False) -> dict[str, object] | None:
    lexical_ready = _table_exists(settings.lancedb_dir, settings.lancedb_table_name)
    dense_ready = _table_exists(settings.lancedb_dir, settings.dense_lancedb_table_name)
    metadata_ready = settings.dense_index_artifact_path.exists()

    if lexical_ready and (not require_dense or (dense_ready and metadata_ready)):
        return None

    if lexical_ready and require_dense and dense_ready:
        metadata_payload = ensure_dense_metadata_artifact(settings)
        if settings.dense_index_artifact_path.exists():
            return {
                "action": "reconstructed_dense_metadata",
                "dense_metadata": metadata_payload,
            }

    if settings.lancedb_archive_url and settings.lancedb_archive_auto_download:
        payload = fetch_lancedb_archive(settings)
        payload["action"] = "downloaded_lancedb_archive"
        return payload

    if not settings.lancedb_remote_repo_id or not settings.lancedb_remote_auto_download:
        return None

    payload = fetch_hosted_lancedb(settings)
    payload["action"] = "downloaded_hosted_lancedb"
    return payload


def ensure_dense_metadata_artifact(settings: Settings) -> dict[str, object] | None:
    if settings.dense_index_artifact_path.exists():
        return {
            "metadata_path": str(settings.dense_index_artifact_path),
            "created": False,
        }

    resolved_embedding_model = resolve_embedder_model(settings.dense_embedding_model)
    if resolved_embedding_model == "hashed_v1":
        return None

    if not _table_exists(settings.lancedb_dir, settings.dense_lancedb_table_name):
        return None

    database = lancedb.connect(settings.lancedb_dir)
    table = database.open_table(settings.dense_lancedb_table_name)
    vector_type = table.schema.field("vector").type
    dimension = getattr(vector_type, "list_size", None)
    if dimension is None:
        raise ValueError("Dense vector column is not a fixed-size list; cannot infer embedding dimension.")

    metadata = DenseIndexMetadata(
        model=resolved_embedding_model,
        dimension=int(dimension),
        document_count=table.count_rows(),
        document_frequency_by_bucket=[],
    )
    metadata_path = write_dense_index_metadata(settings.dense_index_artifact_path, metadata)
    return {
        "metadata_path": str(metadata_path),
        "created": True,
        "model": metadata.model,
        "dimension": metadata.dimension,
        "document_count": metadata.document_count,
    }


def create_lancedb_archive(settings: Settings, *, output_path: Path | None = None) -> dict[str, object]:
    if not settings.lancedb_dir.exists():
        raise FileNotFoundError(
            f"LanceDB directory `{settings.lancedb_dir}` does not exist. Build retrieval artifacts first."
        )
    if not settings.dense_index_artifact_path.exists():
        raise FileNotFoundError(
            f"Dense metadata artifact `{settings.dense_index_artifact_path}` is missing."
        )

    archive_path = output_path or (settings.artifacts_dir / "lancedb-demo.zip")
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(settings.lancedb_dir.rglob("*")):
            if path.is_dir():
                continue
            archive.write(path, arcname=path.relative_to(settings.repo_root))
        archive.write(
            settings.dense_index_artifact_path,
            arcname=settings.dense_index_artifact_path.relative_to(settings.repo_root),
        )

    return {
        "archive_path": str(archive_path),
        "database_path": str(settings.lancedb_dir),
        "metadata_path": str(settings.dense_index_artifact_path),
        "archive_size_bytes": archive_path.stat().st_size,
    }


def fetch_lancedb_archive(
    settings: Settings,
    *,
    archive_url: str | None = None,
    archive_path: Path | None = None,
) -> dict[str, object]:
    source = archive_url or settings.lancedb_archive_url
    downloaded_temp_archive = False
    if archive_path is None and not source:
        raise ValueError(
            "LanceDB archive download is not configured. Set `ELIZA_RAG_LANCEDB_ARCHIVE_URL` first."
        )

    if archive_path is None:
        parsed = urlparse(str(source))
        if parsed.scheme in {"", "file"}:
            archive_path = Path(parsed.path if parsed.scheme == "file" else str(source)).expanduser().resolve()
        else:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
                temp_archive = Path(handle.name)
            urlretrieve(str(source), temp_archive)
            archive_path = temp_archive
            downloaded_temp_archive = True

    settings.lancedb_dir.parent.mkdir(parents=True, exist_ok=True)
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    _clear_existing_lancedb_artifacts(settings)

    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(settings.repo_root)

    metadata_payload = ensure_dense_metadata_artifact(settings)
    if downloaded_temp_archive:
        archive_path.unlink(missing_ok=True)
    return {
        "archive_source": str(source or archive_path),
        "archive_path": str(archive_path),
        "database_path": str(settings.lancedb_dir),
        "metadata_path": str(settings.dense_index_artifact_path),
        "dense_metadata": metadata_payload,
    }


def _table_exists(database_path: Path, table_name: str) -> bool:
    try:
        database = lancedb.connect(database_path)
        database.open_table(table_name)
    except FileNotFoundError:
        return False
    except ValueError:
        return False
    return True


def _clear_existing_lancedb_artifacts(settings: Settings) -> None:
    if settings.lancedb_dir.exists():
        shutil.rmtree(settings.lancedb_dir)
    if settings.dense_index_artifact_path.exists():
        settings.dense_index_artifact_path.unlink()
