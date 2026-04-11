from __future__ import annotations

from pathlib import Path
from urllib import error

import pytest

from eliza_rag.answer_generation import (
    AnswerGenerationError,
    LocalOllamaGenerateClient,
    OpenAICompatibleResponsesClient,
    build_answer_backend_client,
    build_prompt_package,
    generate_answer,
    parse_model_response,
    resolve_provider_config,
)
from eliza_rag.config import Settings
from eliza_rag.interfaces import AnswerBackend
from eliza_rag.local_runtime import LocalRuntimeError
from eliza_rag.models import RetrievalResult


class FakeClient(AnswerBackend):
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self._model_name = "fake-model"
        self.prompt: str | None = None

    @property
    def model(self) -> str:
        return self._model_name

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return self._response_text


class _FakeHTTPResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload.encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "final_answer_prompt.txt").write_text(
        "Question:\n{question}\n\nContext:\n{context}\n",
        encoding="utf-8",
    )
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
        "llm_provider": "openai",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_api_key": "test-key",
        "llm_model": "gpt-5-mini",
        "local_llm_runtime": "ollama",
        "local_llm_runtime_command": "ollama",
        "local_llm_base_url": "http://127.0.0.1:11434/v1",
        "local_llm_model": "qwen2.5:3b-instruct",
        "local_llm_start_timeout_seconds": 1,
    }
    values.update(overrides)
    return Settings(**values)


def _retrieval_results() -> list[RetrievalResult]:
    return [
        RetrievalResult(
            chunk_id="aapl-001",
            filing_id="aapl-10k-2025",
            ticker="AAPL",
            form_type="10-K",
            filing_date="2025-01-31",
            section="Risk Factors",
            section_path="Part I > Item 1A",
            text="Apple notes supply-chain concentration and competition risks.",
            raw_score=2.0,
            retrieval_mode="hybrid_rrf",
            rank=1,
            company_name="Apple Inc.",
            fiscal_period="FY2024",
            source_path="edgar_corpus/aapl.txt",
            chunk_index=12,
        ),
        RetrievalResult(
            chunk_id="tsla-001",
            filing_id="tsla-10k-2025",
            ticker="TSLA",
            form_type="10-K",
            filing_date="2025-02-01",
            section="Risk Factors",
            section_path="Part I > Item 1A",
            text="Tesla highlights manufacturing scale-up and regulatory risks.",
            raw_score=1.5,
            retrieval_mode="hybrid_rrf",
            rank=2,
            company_name="Tesla, Inc.",
            fiscal_period="FY2024",
            source_path="edgar_corpus/tsla.txt",
            chunk_index=9,
        ),
    ]


def test_build_prompt_package_includes_citation_headers(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    prompt_package = build_prompt_package(
        settings,
        "What are the risk factors facing Apple and Tesla?",
        _retrieval_results(),
    )

    assert prompt_package.prompt_path == settings.final_prompt_template_path
    assert "[C1]" in prompt_package.prompt
    assert "chunk_id=aapl-001" in prompt_package.prompt
    assert "Apple notes supply-chain concentration" in prompt_package.prompt
    assert [citation.citation_id for citation in prompt_package.citations] == ["C1", "C2"]


def test_build_prompt_package_supports_literal_json_braces_in_template(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.final_prompt_template_path.write_text(
        """
Return exactly one JSON object with this shape:
{
  "summary": "test",
  "answer": "test",
  "findings": [{"statement": "x", "citations": ["C1"]}],
  "uncertainty": "test"
}

Question:
{question}

Context:
{context}
""".strip(),
        encoding="utf-8",
    )

    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    assert '"summary": "test"' in prompt_package.prompt
    assert "Question:\nquestion" in prompt_package.prompt
    assert "[C1]" in prompt_package.prompt


def test_parse_model_response_requires_inline_answer_citations(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    parsed = parse_model_response(
        """
        {
          "summary": "test",
          "answer": "Apple and Tesla both report operational risks.",
          "findings": [{"statement": "x", "citations": ["C1"]}],
          "uncertainty": "none"
        }
        """,
        prompt_package.citations,
    )

    assert parsed["answer"] == "Apple and Tesla both report operational risks. [C1]"


def test_parse_model_response_rejects_unknown_answer_citations(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    parsed = parse_model_response(
        """
        {
          "summary": "test",
          "answer": "Apple faces concentration risk [C9].",
          "findings": [{"statement": "x", "citations": ["C1"]}],
          "uncertainty": "none"
        }
        """,
        prompt_package.citations,
    )

    assert parsed["answer"] == "Apple faces concentration risk. [C1]"


def test_parse_model_response_accepts_parenthetical_answer_citations(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    parsed = parse_model_response(
        """
        {
          "summary": "test",
          "answer": "Apple faces concentration risk (C1, C2).",
          "findings": [{"statement": "x", "citations": ["C1"]}],
          "uncertainty": "none"
        }
        """,
        prompt_package.citations,
    )

    assert parsed["answer"] == "Apple faces concentration risk [C1] [C2]."


def test_parse_model_response_normalizes_bracketed_answer_citation_groups(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    parsed = parse_model_response(
        """
        {
          "summary": "test",
          "answer": "Apple faces concentration risk [C1, C2].",
          "findings": [{"statement": "x", "citations": ["C1"]}],
          "uncertainty": "none"
        }
        """,
        prompt_package.citations,
    )

    assert parsed["answer"] == "Apple faces concentration risk [C1] [C2]."


def test_parse_model_response_validates_finding_citation_ids(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    with pytest.raises(AnswerGenerationError, match="at least one finding with known citation ids"):
        parse_model_response(
            """
            {
              "summary": "test",
              "answer": "Apple faces concentration risk [C1].",
              "findings": [{"statement": "x", "citations": ["C9"]}],
              "uncertainty": "none"
            }
            """,
            prompt_package.citations,
        )


def test_parse_model_response_rejects_malformed_json(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    with pytest.raises(AnswerGenerationError, match="not valid JSON"):
        parse_model_response("{", prompt_package.citations)


def test_parse_model_response_accepts_fenced_json(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    parsed = parse_model_response(
        """
        ```json
        {
          "summary": "test",
          "answer": "Apple faces concentration risk [C1].",
          "findings": [{"statement": "x", "citations": ["C1"]}],
          "uncertainty": "none"
        }
        ```
        """,
        prompt_package.citations,
    )

    assert parsed["summary"] == "test"


def test_parse_model_response_accepts_prose_wrapped_json(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    parsed = parse_model_response(
        """
        Here is the requested JSON:
        {
          "summary": "test",
          "answer": "Apple faces concentration risk [C1].",
          "findings": [{"statement": "x", "citations": ["C1"]}],
          "uncertainty": "none"
        }
        """,
        prompt_package.citations,
    )

    assert parsed["summary"] == "test"


def test_parse_model_response_allows_empty_findings(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    parsed = parse_model_response(
        """
        {
          "summary": "test",
          "answer": "Apple faces concentration risk [C1].",
          "findings": [],
          "uncertainty": "none"
        }
        """,
        prompt_package.citations,
    )

    assert parsed["findings"] == []


def test_parse_model_response_allows_missing_findings(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    parsed = parse_model_response(
        """
        {
          "summary": "test",
          "answer": "Apple faces concentration risk [C1].",
          "uncertainty": "none"
        }
        """,
        prompt_package.citations,
    )

    assert parsed["findings"] == []


def test_parse_model_response_requires_findings_list_when_present(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    prompt_package = build_prompt_package(settings, "question", _retrieval_results())

    with pytest.raises(AnswerGenerationError, match="`findings` must be a list"):
        parse_model_response(
            """
            {
              "summary": "test",
              "answer": "Apple faces concentration risk [C1].",
              "findings": "not-a-list",
              "uncertainty": "none"
            }
            """,
            prompt_package.citations,
        )


def test_build_answer_backend_client_supports_openai_compatible_mode(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path,
        llm_provider="openai_compatible",
        llm_base_url="http://localhost:11434/v1/",
        llm_model="local-model",
        llm_api_key="dummy",
    )

    client = build_answer_backend_client(settings)

    assert isinstance(client, OpenAICompatibleResponsesClient)
    assert client.model == "local-model"
    assert client._base_url == "http://localhost:11434/v1"


def test_resolve_provider_config_supports_openrouter(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path,
        llm_provider="openrouter",
        llm_base_url="https://openrouter.ai/api/v1",
        llm_model="openai/gpt-5-mini",
    )

    provider_config = resolve_provider_config(settings)

    assert provider_config.provider == "openrouter"
    assert provider_config.requires_api_key is True
    assert provider_config.base_url == "https://openrouter.ai/api/v1"


def test_build_answer_backend_client_rejects_unknown_provider(tmp_path: Path) -> None:
    settings = _settings(tmp_path, llm_provider="anthropic")

    with pytest.raises(AnswerGenerationError, match="Unsupported LLM provider"):
        build_answer_backend_client(settings)


def test_build_answer_backend_client_requires_api_key(tmp_path: Path) -> None:
    settings = _settings(tmp_path, llm_api_key=None)

    with pytest.raises(AnswerGenerationError, match="hosted provider `openai`"):
        build_answer_backend_client(settings)


def test_openai_compatible_client_surfaces_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenAICompatibleResponsesClient(
        api_key="dummy",
        model="local-model",
        base_url="http://localhost:11434/v1",
        provider_label="Configured OpenAI-compatible backend",
    )

    def _raise_url_error(*args: object, **kwargs: object) -> object:
        raise error.URLError("connection refused")

    monkeypatch.setattr("eliza_rag.answer_generation.request.urlopen", _raise_url_error)

    with pytest.raises(AnswerGenerationError, match="endpoint is unreachable: connection refused"):
        client.generate("prompt")


def test_openai_compatible_client_accepts_output_text_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = OpenAICompatibleResponsesClient(
        api_key="dummy",
        model="local-model",
        base_url="http://localhost:11434/v1",
        provider_label="Configured OpenAI-compatible backend",
    )

    monkeypatch.setattr(
        "eliza_rag.answer_generation.request.urlopen",
        lambda *args, **kwargs: _FakeHTTPResponse('{"output_text":"{\\"summary\\":\\"x\\"}"}'),
    )

    assert client.generate("prompt") == '{"summary":"x"}'


def test_openai_compatible_client_accepts_ollama_content_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = OpenAICompatibleResponsesClient(
        api_key="dummy",
        model="local-model",
        base_url="http://localhost:11434/v1",
        provider_label="Repo-managed local Ollama backend",
    )

    monkeypatch.setattr(
        "eliza_rag.answer_generation.request.urlopen",
        lambda *args, **kwargs: _FakeHTTPResponse(
            '{"output":[{"type":"message","content":[{"type":"output_text","text":"{\\"summary\\":\\"x\\"}"}]}]}'
        ),
    )

    assert client.generate("prompt") == '{"summary":"x"}'


def test_local_ollama_generate_client_accepts_response_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = LocalOllamaGenerateClient(
        model="qwen2.5:3b-instruct",
        base_url="http://localhost:11434/v1",
    )

    monkeypatch.setattr(
        "eliza_rag.answer_generation.request.urlopen",
        lambda *args, **kwargs: _FakeHTTPResponse('{"response":"{\\"summary\\":\\"x\\"}"}'),
    )

    assert client.generate("prompt") == '{"summary":"x"}'


def test_build_answer_backend_client_requires_local_model_when_using_ollama(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(
        tmp_path,
        llm_provider="local_ollama",
        llm_api_key=None,
        llm_model="qwen2.5:3b-instruct",
    )

    class _FakeManager:
        def ensure_ready(self) -> None:
            raise LocalRuntimeError("Local Ollama model `qwen2.5:3b-instruct` is not available.")

    monkeypatch.setattr(
        "eliza_rag.answer_generation.build_local_runtime_manager",
        lambda _settings: _FakeManager(),
    )

    with pytest.raises(AnswerGenerationError, match="Local Ollama model `qwen2.5:3b-instruct` is not available"):
        build_answer_backend_client(settings)


def test_build_answer_backend_client_uses_native_ollama_client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(
        tmp_path,
        llm_provider="local_ollama",
        llm_api_key=None,
        llm_model="qwen2.5:3b-instruct",
        llm_base_url="http://localhost:11434/v1",
    )

    class _FakeManager:
        def ensure_ready(self) -> None:
            return None

    monkeypatch.setattr(
        "eliza_rag.answer_generation.build_local_runtime_manager",
        lambda _settings: _FakeManager(),
    )

    client = build_answer_backend_client(settings)

    assert isinstance(client, LocalOllamaGenerateClient)
    assert client.model == "qwen2.5:3b-instruct"


def test_generate_answer_fails_when_retrieval_returns_no_results(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    fake_client = FakeClient("{}")

    monkeypatch.setattr("eliza_rag.answer_generation.retrieve", lambda *args, **kwargs: [])

    with pytest.raises(AnswerGenerationError, match="No retrieval results were returned"):
        generate_answer(
            settings,
            "What are the risk factors facing Apple and Tesla?",
            client=fake_client,
        )


def test_generate_answer_uses_single_retrieval_to_prompt_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    fake_client = FakeClient(
        """
        {
          "summary": "Apple and Tesla both report risk exposure.",
          "answer": "Apple emphasizes supply-chain and competition risks [C1], while Tesla emphasizes manufacturing and regulatory risks [C2].",
          "findings": [
            {"statement": "Apple cites supply-chain concentration and competition risks.", "citations": ["C1"]},
            {"statement": "Tesla cites manufacturing scale-up and regulatory risks.", "citations": ["C2"]}
          ],
          "uncertainty": "The retrieved evidence does not quantify which risk is most material across all filings."
        }
        """
    )

    monkeypatch.setattr(
        "eliza_rag.answer_generation.retrieve",
        lambda *args, **kwargs: _retrieval_results(),
    )

    response = generate_answer(
        settings,
        "What are the risk factors facing Apple and Tesla?",
        client=fake_client,
    )

    assert response.model == "fake-model"
    assert response.retrieval_mode == "hybrid"
    assert response.summary.startswith("Apple and Tesla")
    assert len(response.findings) == 2
    assert response.citations[0].chunk_id == "aapl-001"
    assert "What are the risk factors facing Apple and Tesla?" in str(fake_client.prompt)
