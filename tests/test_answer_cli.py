from __future__ import annotations

import json
from pathlib import Path

import pytest

from eliza_rag.answer_cli import main
from eliza_rag.models import AnswerCitation, AnswerFinding, AnswerResponse, RetrievalResult


def _response() -> AnswerResponse:
    retrieval_result = RetrievalResult(
        chunk_id="aapl-001",
        filing_id="aapl-10k-2025",
        ticker="AAPL",
        form_type="10-K",
        filing_date="2025-01-31",
        section="Risk Factors",
        section_path="Part I > Item 1A",
        text="Apple notes supply-chain concentration and competition risks.",
        raw_score=2.0,
        retrieval_mode="lexical",
        rank=1,
        company_name="Apple Inc.",
        fiscal_period="FY2024",
        source_path="edgar_corpus/aapl.txt",
        chunk_index=12,
    )
    citation = AnswerCitation(
        citation_id="C1",
        chunk_id="aapl-001",
        filing_id="aapl-10k-2025",
        ticker="AAPL",
        company_name="Apple Inc.",
        form_type="10-K",
        filing_date="2025-01-31",
        section="Risk Factors",
        source_path="edgar_corpus/aapl.txt",
    )
    return AnswerResponse(
        question="What risk factors does Apple describe?",
        answer="Apple cites concentration risk [C1].",
        summary="Apple cites risk exposure.",
        findings=[AnswerFinding(statement="Apple cites concentration risk.", citations=["C1"])],
        uncertainty="The excerpt is limited.",
        citations=[citation],
        retrieval_mode="lexical",
        prompt_path=str(Path("prompts/final_answer_prompt.txt")),
        prompt_preview="preview",
        prompt_characters=123,
        retrieval_results=[retrieval_result],
        raw_model_response='{"summary":"x"}',
        model="qwen2.5:3b-instruct",
    )


def test_answer_cli_default_output_is_simplified(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "eliza_rag.answer_cli.get_settings",
        lambda: object(),
    )
    monkeypatch.setattr(
        "eliza_rag.answer_cli.generate_answer",
        lambda *args, **kwargs: _response(),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["eliza-rag-answer", "What risk factors does Apple describe?"],
    )

    main()

    captured = capsys.readouterr()
    assert "Answer:" in captured.out
    assert "Citations:" in captured.out
    assert "Summary:" not in captured.out
    assert "Findings:" not in captured.out
    assert "Model:" not in captured.out


def test_answer_cli_verbose_output_includes_extra_sections(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "eliza_rag.answer_cli.get_settings",
        lambda: object(),
    )
    monkeypatch.setattr(
        "eliza_rag.answer_cli.generate_answer",
        lambda *args, **kwargs: _response(),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["eliza-rag-answer", "What risk factors does Apple describe?", "--verbose"],
    )

    main()

    captured = capsys.readouterr()
    assert "Answer:" in captured.out
    assert "Summary:" in captured.out
    assert "Findings:" in captured.out
    assert "Model:" in captured.out


def test_answer_cli_json_output_is_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    response = _response()
    monkeypatch.setattr(
        "eliza_rag.answer_cli.get_settings",
        lambda: object(),
    )
    monkeypatch.setattr(
        "eliza_rag.answer_cli.generate_answer",
        lambda *args, **kwargs: response,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["eliza-rag-answer", "What risk factors does Apple describe?", "--json"],
    )

    main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["summary"] == response.summary
    assert payload["answer"] == response.answer


def test_answer_cli_defaults_to_recommended_demo_path(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def _fake_generate_answer(*args, **kwargs):
        observed.update(kwargs)
        return _response()

    monkeypatch.setattr("eliza_rag.answer_cli.get_settings", lambda: object())
    monkeypatch.setattr("eliza_rag.answer_cli.generate_answer", _fake_generate_answer)
    monkeypatch.setattr(
        "sys.argv",
        ["eliza-rag-answer", "What risk factors does Apple describe?"],
    )

    main()

    assert observed["mode"] == "targeted_hybrid"
    assert observed["enable_rerank"] is True


def test_answer_cli_forwards_rerank_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def _fake_generate_answer(*args, **kwargs):
        observed.update(kwargs)
        return _response()

    monkeypatch.setattr("eliza_rag.answer_cli.get_settings", lambda: object())
    monkeypatch.setattr("eliza_rag.answer_cli.generate_answer", _fake_generate_answer)
    monkeypatch.setattr(
        "sys.argv",
        [
            "eliza-rag-answer",
            "What risk factors does Apple describe?",
            "--rerank",
            "--reranker",
            "heuristic",
            "--rerank-candidate-pool",
            "9",
        ],
    )

    main()

    assert observed["enable_rerank"] is True
    assert observed["reranker"] == "heuristic"
    assert observed["rerank_candidate_pool"] == 9


def test_answer_cli_can_disable_reranking(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def _fake_generate_answer(*args, **kwargs):
        observed.update(kwargs)
        return _response()

    monkeypatch.setattr("eliza_rag.answer_cli.get_settings", lambda: object())
    monkeypatch.setattr("eliza_rag.answer_cli.generate_answer", _fake_generate_answer)
    monkeypatch.setattr(
        "sys.argv",
        ["eliza-rag-answer", "What risk factors does Apple describe?", "--no-rerank"],
    )

    main()

    assert observed["enable_rerank"] is False
