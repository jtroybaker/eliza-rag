from __future__ import annotations

import json

import pytest

from eliza_rag.local_runtime_cli import main


class _FakeManager:
    def prepare(self, *, pull: bool = True):
        assert pull is True
        return type(
            "Status",
            (),
            {
                "runtime": "ollama",
                "command": "ollama",
                "base_url": "http://127.0.0.1:11434/v1",
                "model": "qwen2.5:3b-instruct",
                "runtime_available": True,
                "server_running": True,
                "model_available": True,
            },
        )()


def test_local_runtime_cli_prepare_warms_retrieval_models(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("eliza_rag.local_runtime_cli.get_settings", lambda: object())
    monkeypatch.setattr("eliza_rag.local_runtime_cli.build_local_runtime_manager", lambda _: _FakeManager())
    monkeypatch.setattr(
        "eliza_rag.local_runtime_cli.warm_retrieval_models",
        lambda _settings: {
            "dense_query_model": "Snowflake/snowflake-arctic-embed-xs",
            "reranker": "bge-reranker-v2-m3",
        },
    )
    monkeypatch.setattr("sys.argv", ["eliza-rag-local-llm", "prepare"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["retrieval_warmup"] == {
        "dense_query_model": "Snowflake/snowflake-arctic-embed-xs",
        "reranker": "bge-reranker-v2-m3",
    }


def test_local_runtime_cli_prepare_can_skip_retrieval_warmup(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("eliza_rag.local_runtime_cli.get_settings", lambda: object())
    monkeypatch.setattr("eliza_rag.local_runtime_cli.build_local_runtime_manager", lambda _: _FakeManager())
    monkeypatch.setattr(
        "eliza_rag.local_runtime_cli.warm_retrieval_models",
        lambda _settings: pytest.fail("warm_retrieval_models should not be called"),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["eliza-rag-local-llm", "prepare", "--skip-retrieval-warmup"],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["retrieval_warmup"] is None
