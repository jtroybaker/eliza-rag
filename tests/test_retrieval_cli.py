from __future__ import annotations

import json

import pytest

from eliza_rag.retrieval_cli import main


def test_retrieval_cli_forwards_rerank_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    def _fake_retrieve(*args, **kwargs):
        observed.update(kwargs)
        return []

    monkeypatch.setattr("eliza_rag.retrieval_cli.get_settings", lambda: type("S", (), {"retrieval_top_k": 8})())
    monkeypatch.setattr("eliza_rag.retrieval_cli.index_status", lambda _settings: {})
    monkeypatch.setattr(
        "eliza_rag.retrieval_cli.analyze_query",
        lambda query, filters=None, settings=None: type(
            "Q", (), {"to_dict": lambda self: {"raw_query": query}}
        )(),
    )
    monkeypatch.setattr("eliza_rag.retrieval_cli.retrieve", _fake_retrieve)
    monkeypatch.setattr(
        "sys.argv",
        [
            "eliza-rag-search",
            "Apple risk factors",
            "--rerank",
            "--reranker",
            "heuristic",
            "--rerank-candidate-pool",
            "10",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert observed["enable_rerank"] is True
    assert observed["reranker"] == "heuristic"
    assert observed["rerank_candidate_pool"] == 10
    assert payload["reranking"] == {
        "enabled": True,
        "reranker": "heuristic",
        "candidate_pool": 10,
    }
