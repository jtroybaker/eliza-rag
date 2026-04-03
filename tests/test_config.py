from __future__ import annotations

from eliza_rag.config import get_settings


def test_local_ollama_uses_local_aliases_when_primary_llm_vars_are_unset(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ELIZA_RAG_LLM_PROVIDER", "local_ollama")
    monkeypatch.delenv("ELIZA_RAG_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ELIZA_RAG_LLM_MODEL", raising=False)
    monkeypatch.setenv("ELIZA_RAG_LOCAL_LLM_BASE_URL", "http://127.0.0.1:22434/v1")
    monkeypatch.setenv("ELIZA_RAG_LOCAL_LLM_MODEL", "llama3.2:3b")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.llm_base_url == "http://127.0.0.1:22434/v1"
    assert settings.llm_model == "llama3.2:3b"

    get_settings.cache_clear()


def test_local_ollama_prefers_primary_llm_vars_over_local_aliases(monkeypatch) -> None:
    monkeypatch.setenv("ELIZA_RAG_LLM_PROVIDER", "local_ollama")
    monkeypatch.setenv("ELIZA_RAG_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("ELIZA_RAG_LLM_MODEL", "qwen2.5:3b-instruct")
    monkeypatch.setenv("ELIZA_RAG_LOCAL_LLM_BASE_URL", "http://127.0.0.1:22434/v1")
    monkeypatch.setenv("ELIZA_RAG_LOCAL_LLM_MODEL", "llama3.2:3b")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.llm_base_url == "http://127.0.0.1:11434/v1"
    assert settings.llm_model == "qwen2.5:3b-instruct"
    assert settings.local_llm_base_url == "http://127.0.0.1:22434/v1"
    assert settings.local_llm_model == "llama3.2:3b"

    get_settings.cache_clear()


def test_lancedb_remote_settings_are_loaded_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("ELIZA_RAG_LANCEDB_REMOTE_REPO_ID", "example/eliza-rag-demo")
    monkeypatch.setenv("ELIZA_RAG_LANCEDB_REMOTE_REPO_TYPE", "dataset")
    monkeypatch.setenv("ELIZA_RAG_LANCEDB_REMOTE_REVISION", "main")
    monkeypatch.setenv("ELIZA_RAG_LANCEDB_REMOTE_TOKEN", "hf_test")
    monkeypatch.setenv("ELIZA_RAG_LANCEDB_REMOTE_AUTO_DOWNLOAD", "false")
    monkeypatch.setenv("ELIZA_RAG_LANCEDB_ARCHIVE_URL", "https://example.com/lancedb-demo.zip")
    monkeypatch.setenv("ELIZA_RAG_LANCEDB_ARCHIVE_AUTO_DOWNLOAD", "false")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.lancedb_remote_repo_id == "example/eliza-rag-demo"
    assert settings.lancedb_remote_repo_type == "dataset"
    assert settings.lancedb_remote_revision == "main"
    assert settings.lancedb_remote_token == "hf_test"
    assert settings.lancedb_remote_auto_download is False
    assert settings.lancedb_archive_url == "https://example.com/lancedb-demo.zip"
    assert settings.lancedb_archive_auto_download is False

    get_settings.cache_clear()
