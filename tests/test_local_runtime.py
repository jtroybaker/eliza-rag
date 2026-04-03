from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from eliza_rag.local_runtime import LocalRuntimeError, build_local_runtime_manager
from eliza_rag.config import Settings


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    values: dict[str, object] = {
        "repo_root": tmp_path,
        "data_dir": tmp_path / "data",
        "artifacts_dir": tmp_path / "artifacts",
        "prompts_dir": prompts_dir,
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
        "dense_embedding_model": "hashed_v1",
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


def test_local_runtime_status_reports_missing_binary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    manager = build_local_runtime_manager(settings)

    monkeypatch.setattr("eliza_rag.local_runtime.shutil.which", lambda _: None)

    status = manager.status()

    assert status.runtime_available is False
    assert status.server_running is False
    assert status.model_available is False


def test_local_runtime_ensure_ready_errors_when_model_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    manager = build_local_runtime_manager(settings)

    monkeypatch.setattr("eliza_rag.local_runtime.shutil.which", lambda _: "/usr/bin/ollama")
    monkeypatch.setattr(manager, "_is_server_running", lambda: True)
    monkeypatch.setattr(manager, "_list_models", lambda: {"llama3.2:latest"})

    with pytest.raises(LocalRuntimeError, match="Run `uv run eliza-rag-local-llm prepare`"):
        manager.ensure_ready()


def test_local_runtime_prepare_starts_server_and_pulls_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    manager = build_local_runtime_manager(settings)
    server_checks = iter([False, True, True])
    models = {"qwen2.5:3b-instruct"}
    pull_calls: list[tuple[str, ...]] = []

    class _FakeProcess:
        def poll(self) -> None:
            return None

    monkeypatch.setattr("eliza_rag.local_runtime.shutil.which", lambda _: "/usr/bin/ollama")
    monkeypatch.setattr(manager, "_is_server_running", lambda: next(server_checks))
    monkeypatch.setattr(manager, "_list_models", lambda: models)
    monkeypatch.setattr(
        "eliza_rag.local_runtime.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    def _fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        pull_calls.append(tuple(args))
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("eliza_rag.local_runtime.subprocess.run", _fake_run)
    monkeypatch.setattr("eliza_rag.local_runtime.time.sleep", lambda _: None)

    status = manager.prepare()

    assert status.server_running is True
    assert status.model_available is True
    assert pull_calls == []


def test_local_runtime_prepare_surfaces_pull_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    manager = build_local_runtime_manager(settings)

    monkeypatch.setattr("eliza_rag.local_runtime.shutil.which", lambda _: "/usr/bin/ollama")
    monkeypatch.setattr(manager, "_is_server_running", lambda: True)
    monkeypatch.setattr(manager, "_list_models", lambda: set())

    monkeypatch.setattr(
        "eliza_rag.local_runtime.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="",
            stderr="pull failed",
        ),
    )

    with pytest.raises(LocalRuntimeError, match="Failed to pull local Ollama model"):
        manager.prepare()
