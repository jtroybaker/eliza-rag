from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _env_path(name: str, default: Path) -> Path:
    return Path(os.getenv(name, default)).expanduser().resolve()


@dataclass(frozen=True, slots=True)
class Settings:
    repo_root: Path
    data_dir: Path
    artifacts_dir: Path
    prompts_dir: Path
    quality_notes_path: Path
    prompt_iteration_log_path: Path
    corpus_dir: Path
    corpus_zip_path: Path
    lancedb_dir: Path
    lancedb_table_name: str
    dense_lancedb_table_name: str
    dense_index_artifact_name: str
    lancedb_remote_repo_id: str | None
    lancedb_remote_repo_type: str
    lancedb_remote_revision: str | None
    lancedb_remote_token: str | None
    lancedb_remote_auto_download: bool
    lancedb_archive_url: str | None
    lancedb_archive_auto_download: bool
    chunk_size_tokens: int
    chunk_overlap_tokens: int
    retrieval_top_k: int
    answer_top_k: int
    enable_rerank: bool
    reranker_type: str
    rerank_candidate_pool: int
    dense_embedding_model: str
    dense_embedding_dim: int
    dense_index_metric: str
    llm_provider: str
    llm_base_url: str
    llm_api_key: str | None
    llm_model: str
    local_llm_runtime: str
    local_llm_runtime_command: str
    local_llm_base_url: str
    local_llm_model: str
    local_llm_start_timeout_seconds: int

    @property
    def manifest_path(self) -> Path:
        return self.corpus_dir / "manifest.json"

    @property
    def chunk_artifact_path(self) -> Path:
        return self.artifacts_dir / "chunk_records.jsonl"

    @property
    def dense_index_artifact_path(self) -> Path:
        return self.artifacts_dir / self.dense_index_artifact_name

    @property
    def final_prompt_template_path(self) -> Path:
        return self.prompts_dir / "final_answer_prompt.txt"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    repo_root = _repo_root()
    data_dir = _env_path("ELIZA_RAG_DATA_DIR", repo_root / "data")
    artifacts_dir = _env_path("ELIZA_RAG_ARTIFACTS_DIR", repo_root / "artifacts")
    prompts_dir = repo_root / "prompts"
    corpus_dir = _env_path("ELIZA_RAG_CORPUS_DIR", repo_root / "edgar_corpus")
    corpus_zip_path = _env_path("ELIZA_RAG_CORPUS_ZIP", repo_root / "edgar_corpus.zip")
    lancedb_dir = _env_path("ELIZA_RAG_LANCEDB_DIR", data_dir / "lancedb")
    llm_provider = os.getenv("ELIZA_RAG_LLM_PROVIDER", "openai").strip().lower()
    enable_rerank = os.getenv("ELIZA_RAG_ENABLE_RERANK", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    default_base_urls = {
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "openai_compatible": "http://127.0.0.1:11434/v1",
        "local_ollama": "http://127.0.0.1:11434/v1",
    }
    default_models = {
        "openai": "gpt-5-mini",
        "openrouter": "openai/gpt-5-mini",
        "openai_compatible": os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        "local_ollama": "qwen2.5:3b-instruct",
    }
    local_base_url_alias = os.getenv("ELIZA_RAG_LOCAL_LLM_BASE_URL")
    local_model_alias = os.getenv("ELIZA_RAG_LOCAL_LLM_MODEL")
    llm_base_url = (
        os.getenv("ELIZA_RAG_LLM_BASE_URL")
        or (
            local_base_url_alias
            if llm_provider == "local_ollama" and local_base_url_alias
            else default_base_urls.get(llm_provider, "")
        )
    )
    llm_model = (
        os.getenv("ELIZA_RAG_LLM_MODEL")
        or (
            local_model_alias
            if llm_provider == "local_ollama" and local_model_alias
            else default_models.get(llm_provider, os.getenv("OPENAI_MODEL", "gpt-5-mini"))
        )
    )

    return Settings(
        repo_root=repo_root,
        data_dir=data_dir,
        artifacts_dir=artifacts_dir,
        prompts_dir=prompts_dir,
        quality_notes_path=repo_root / "QUALITY_NOTES.md",
        prompt_iteration_log_path=repo_root / "PROMPT_ITERATION_LOG.md",
        corpus_dir=corpus_dir,
        corpus_zip_path=corpus_zip_path,
        lancedb_dir=lancedb_dir,
        lancedb_table_name=os.getenv("ELIZA_RAG_LANCEDB_TABLE", "filing_chunks"),
        dense_lancedb_table_name=os.getenv("ELIZA_RAG_DENSE_LANCEDB_TABLE", "filing_chunks_dense"),
        dense_index_artifact_name=os.getenv(
            "ELIZA_RAG_DENSE_INDEX_ARTIFACT_NAME",
            "dense_index_metadata.json",
        ),
        lancedb_remote_repo_id=os.getenv("ELIZA_RAG_LANCEDB_REMOTE_REPO_ID"),
        lancedb_remote_repo_type=os.getenv("ELIZA_RAG_LANCEDB_REMOTE_REPO_TYPE", "dataset"),
        lancedb_remote_revision=os.getenv("ELIZA_RAG_LANCEDB_REMOTE_REVISION"),
        lancedb_remote_token=os.getenv("ELIZA_RAG_LANCEDB_REMOTE_TOKEN"),
        lancedb_remote_auto_download=os.getenv(
            "ELIZA_RAG_LANCEDB_REMOTE_AUTO_DOWNLOAD",
            "true",
        ).strip().lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        },
        lancedb_archive_url=os.getenv("ELIZA_RAG_LANCEDB_ARCHIVE_URL"),
        lancedb_archive_auto_download=os.getenv(
            "ELIZA_RAG_LANCEDB_ARCHIVE_AUTO_DOWNLOAD",
            "true",
        ).strip().lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        },
        chunk_size_tokens=int(os.getenv("ELIZA_RAG_CHUNK_SIZE_TOKENS", "800")),
        chunk_overlap_tokens=int(os.getenv("ELIZA_RAG_CHUNK_OVERLAP_TOKENS", "100")),
        retrieval_top_k=int(os.getenv("ELIZA_RAG_RETRIEVAL_TOP_K", "8")),
        answer_top_k=int(os.getenv("ELIZA_RAG_ANSWER_TOP_K", "6")),
        enable_rerank=enable_rerank,
        reranker_type=os.getenv("ELIZA_RAG_RERANKER", "bge-reranker-v2-m3").strip().lower(),
        rerank_candidate_pool=int(os.getenv("ELIZA_RAG_RERANK_CANDIDATE_POOL", "12")),
        dense_embedding_model=os.getenv(
            "ELIZA_RAG_DENSE_EMBEDDING_MODEL",
            "Snowflake/snowflake-arctic-embed-xs",
        ),
        dense_embedding_dim=int(os.getenv("ELIZA_RAG_DENSE_EMBEDDING_DIM", "256")),
        dense_index_metric=os.getenv("ELIZA_RAG_DENSE_INDEX_METRIC", "cosine"),
        llm_provider=llm_provider,
        llm_base_url=llm_base_url,
        llm_api_key=os.getenv("ELIZA_RAG_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        llm_model=llm_model,
        local_llm_runtime=os.getenv("ELIZA_RAG_LOCAL_LLM_RUNTIME", "ollama").strip().lower(),
        local_llm_runtime_command=os.getenv("ELIZA_RAG_LOCAL_LLM_RUNTIME_COMMAND", "ollama"),
        local_llm_base_url=local_base_url_alias or "http://127.0.0.1:11434/v1",
        local_llm_model=local_model_alias or "qwen2.5:3b-instruct",
        local_llm_start_timeout_seconds=int(
            os.getenv("ELIZA_RAG_LOCAL_LLM_START_TIMEOUT_SECONDS", "45")
        ),
    )
