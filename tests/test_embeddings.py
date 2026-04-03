from __future__ import annotations

from pathlib import Path

import pytest

from eliza_rag.config import Settings
from eliza_rag.embeddings import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EXTERNAL_EMBEDDING_MODEL,
    DenseIndexMetadata,
    build_dense_vectors,
    encode_text,
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
        "dense_lancedb_table_name": "filing_chunks_dense_arctic",
        "dense_index_artifact_name": "dense_index_metadata.arctic.json",
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
        "dense_embedding_model": DEFAULT_EXTERNAL_EMBEDDING_MODEL,
        "dense_embedding_dim": 256,
        "dense_index_metric": "cosine",
        "llm_provider": "local_ollama",
        "llm_base_url": "http://127.0.0.1:11434/v1",
        "llm_api_key": None,
        "llm_model": "qwen2.5:3b-instruct",
        "local_llm_runtime": "ollama",
        "local_llm_runtime_command": "ollama",
        "local_llm_base_url": "http://127.0.0.1:11434/v1",
        "local_llm_model": "qwen2.5:3b-instruct",
        "local_llm_start_timeout_seconds": 1,
    }
    values.update(overrides)
    return Settings(**values)


def test_build_dense_vectors_supports_hashed_baseline(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path,
        dense_embedding_model=DEFAULT_EMBEDDING_MODEL,
        dense_embedding_dim=64,
    )

    metadata, vectors = build_dense_vectors(settings, ["apple risk", "tesla risk"])

    assert metadata.model == DEFAULT_EMBEDDING_MODEL
    assert metadata.dimension == 64
    assert len(vectors) == 2
    assert all(len(vector) == 64 for vector in vectors)


def test_build_dense_vectors_uses_sentence_transformer_embeddings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)

    monkeypatch.setattr(
        "eliza_rag.embeddings._encode_texts_with_sentence_transformer",
        lambda texts, model: [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
    )

    metadata, vectors = build_dense_vectors(settings, ["apple risk", "tesla risk"])

    assert metadata.model == DEFAULT_EXTERNAL_EMBEDDING_MODEL
    assert metadata.dimension == 3
    assert metadata.document_frequency_by_bucket == []
    assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_encode_text_uses_sentence_transformer_for_query_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = DenseIndexMetadata(
        model=DEFAULT_EXTERNAL_EMBEDDING_MODEL,
        dimension=3,
        document_count=2,
        document_frequency_by_bucket=[],
    )

    monkeypatch.setattr(
        "eliza_rag.embeddings._encode_texts_with_sentence_transformer",
        lambda texts, model: [[0.7, 0.8, 0.9]],
    )

    vector = encode_text("apple risk", metadata)

    assert vector == [0.7, 0.8, 0.9]
