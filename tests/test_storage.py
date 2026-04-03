from __future__ import annotations

from pathlib import Path

from eliza_rag.config import Settings
from eliza_rag.models import ChunkRecord
from eliza_rag.storage import (
    create_lancedb_archive,
    ensure_dense_metadata_artifact,
    fetch_lancedb_archive,
    load_chunk_records,
    prepare_lancedb_artifacts,
)


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "repo_root": tmp_path,
        "data_dir": tmp_path / "data",
        "artifacts_dir": tmp_path / "artifacts",
        "prompts_dir": tmp_path / "prompts",
        "quality_notes_path": tmp_path / "QUALITY_NOTES.md",
        "prompt_iteration_log_path": tmp_path / "PROMPT_ITERATION_LOG.md",
        "corpus_dir": tmp_path / "edgar_corpus",
        "corpus_zip_path": tmp_path / "edgar_corpus.zip",
        "lancedb_dir": tmp_path / "data" / "lancedb",
        "lancedb_table_name": "filing_chunks",
        "dense_lancedb_table_name": "filing_chunks_dense",
        "dense_index_artifact_name": "dense_index_metadata.json",
        "lancedb_remote_repo_id": None,
        "lancedb_remote_repo_type": "dataset",
        "lancedb_remote_revision": None,
        "lancedb_remote_token": None,
        "lancedb_remote_auto_download": True,
        "lancedb_archive_url": None,
        "lancedb_archive_auto_download": True,
        "chunk_size_tokens": 800,
        "chunk_overlap_tokens": 100,
        "retrieval_top_k": 8,
        "answer_top_k": 6,
        "enable_rerank": False,
        "reranker_type": "heuristic",
        "rerank_candidate_pool": 12,
        "dense_embedding_model": "Snowflake/snowflake-arctic-embed-xs",
        "dense_embedding_dim": 256,
        "dense_index_metric": "cosine",
        "llm_provider": "openai",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_api_key": None,
        "llm_model": "gpt-5-mini",
        "local_llm_runtime": "ollama",
        "local_llm_runtime_command": "ollama",
        "local_llm_base_url": "http://127.0.0.1:11434/v1",
        "local_llm_model": "qwen2.5:3b-instruct",
        "local_llm_start_timeout_seconds": 1,
    }
    values.update(overrides)
    return Settings(**values)


def test_ensure_dense_metadata_artifact_reconstructs_external_embedding_metadata(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    load_chunk_records(
        settings,
        [
            ChunkRecord(
                chunk_id="AAPL::chunk-0001",
                filing_id="AAPL_10K_2024",
                ticker="AAPL",
                company_name="Apple Inc.",
                form_type="10-K",
                filing_date="2024-11-01",
                fiscal_period="2024Q4",
                source_path="edgar_corpus/AAPL_10K_2024_full.txt",
                section="Risk Factors",
                section_path="Item 1A",
                chunk_index=0,
                text="Apple faces supply chain, regulatory, and competitive risks.",
            )
        ],
    )

    import lancedb

    database = lancedb.connect(settings.lancedb_dir)
    database.create_table(
        settings.dense_lancedb_table_name,
        data=[
            {
                "chunk_id": "AAPL::chunk-0001",
                "filing_id": "AAPL_10K_2024",
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "form_type": "10-K",
                "filing_date": "2024-11-01",
                "fiscal_period": "2024Q4",
                "source_path": "edgar_corpus/AAPL_10K_2024_full.txt",
                "section": "Risk Factors",
                "section_path": "Item 1A",
                "chunk_index": 0,
                "text": "Apple faces supply chain, regulatory, and competitive risks.",
                "vector": [0.1, 0.2, 0.3],
            }
        ],
        mode="overwrite",
    )

    payload = ensure_dense_metadata_artifact(settings)

    assert payload == {
        "metadata_path": str(settings.dense_index_artifact_path),
        "created": True,
        "model": "Snowflake/snowflake-arctic-embed-xs",
        "dimension": 3,
        "document_count": 1,
    }
    assert settings.dense_index_artifact_path.exists()


def test_prepare_lancedb_artifacts_fetches_hosted_snapshot_when_local_tables_are_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = _settings(
        tmp_path,
        lancedb_remote_repo_id="example/eliza-rag-demo",
        lancedb_remote_auto_download=True,
    )

    monkeypatch.setattr(
        "eliza_rag.storage.fetch_hosted_lancedb",
        lambda current_settings: {
            "repo_id": current_settings.lancedb_remote_repo_id,
            "database_path": str(current_settings.lancedb_dir),
        },
    )

    payload = prepare_lancedb_artifacts(settings, require_dense=False)

    assert payload == {
        "action": "downloaded_hosted_lancedb",
        "repo_id": "example/eliza-rag-demo",
        "database_path": str(settings.lancedb_dir),
    }


def test_create_and_fetch_lancedb_archive_round_trip(tmp_path: Path) -> None:
    settings = _settings(tmp_path, dense_embedding_model="hashed_v1")
    load_chunk_records(
        settings,
        [
            ChunkRecord(
                chunk_id="AAPL::chunk-0001",
                filing_id="AAPL_10K_2024",
                ticker="AAPL",
                company_name="Apple Inc.",
                form_type="10-K",
                filing_date="2024-11-01",
                fiscal_period="2024Q4",
                source_path="edgar_corpus/AAPL_10K_2024_full.txt",
                section="Risk Factors",
                section_path="Item 1A",
                chunk_index=0,
                text="Apple faces supply chain, regulatory, and competitive risks.",
            )
        ],
    )
    settings.dense_index_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    settings.dense_index_artifact_path.write_text(
        '{"model":"hashed_v1","dimension":256,"document_count":1,"document_frequency_by_bucket":[0]}',
        encoding="utf-8",
    )

    archive_payload = create_lancedb_archive(settings)

    assert Path(archive_payload["archive_path"]).exists()

    for path in (settings.lancedb_dir, settings.dense_index_artifact_path):
        if path.is_dir():
            import shutil

            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    fetch_payload = fetch_lancedb_archive(settings, archive_path=Path(archive_payload["archive_path"]))

    assert settings.lancedb_dir.exists()
    assert settings.dense_index_artifact_path.exists()
    assert fetch_payload["database_path"] == str(settings.lancedb_dir)
