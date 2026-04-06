from __future__ import annotations

import json

import pytest

from eliza_rag.eval_cli import main


def test_eval_cli_forwards_eval_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    monkeypatch.setattr("eliza_rag.eval_cli.get_settings", lambda: object())
    monkeypatch.setattr("eliza_rag.eval_cli.emit_build_manifest", lambda *args, **kwargs: {})

    def _fake_run_golden_eval(*args, **kwargs):
        observed.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr("eliza_rag.eval_cli.run_golden_eval", _fake_run_golden_eval)
    monkeypatch.setattr(
        "sys.argv",
        [
            "eliza-rag-eval",
            "--mode",
            "targeted_hybrid",
            "--rerank",
            "--reranker",
            "heuristic",
            "--rerank-candidate-pool",
            "10",
            "--output",
            "eval/out.json",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {"ok": True}
    assert observed["mode"] == "targeted_hybrid"
    assert observed["enable_rerank"] is True
    assert observed["reranker"] == "heuristic"
    assert observed["rerank_candidate_pool"] == 10
    assert observed["manifest_output_path"] is None
    assert observed["invocation_command"] == (
        "uv run eliza-rag-eval --mode targeted_hybrid --rerank --reranker heuristic "
        "--rerank-candidate-pool 10 --output eval/out.json"
    )


def test_eval_cli_accepts_alternate_reranker(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    monkeypatch.setattr("eliza_rag.eval_cli.get_settings", lambda: object())
    monkeypatch.setattr("eliza_rag.eval_cli.emit_build_manifest", lambda *args, **kwargs: {})

    def _fake_run_golden_eval(*args, **kwargs):
        observed.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr("eliza_rag.eval_cli.run_golden_eval", _fake_run_golden_eval)
    monkeypatch.setattr(
        "sys.argv",
        [
            "eliza-rag-eval",
            "--rerank",
            "--reranker",
            "bge-reranker-base",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {"ok": True}
    assert observed["enable_rerank"] is True
    assert observed["reranker"] == "bge-reranker-base"


def test_eval_cli_forwards_manifest_output_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    monkeypatch.setattr("eliza_rag.eval_cli.get_settings", lambda: object())
    monkeypatch.setattr("eliza_rag.eval_cli.emit_build_manifest", lambda *args, **kwargs: {})

    def _fake_run_golden_eval(*args, **kwargs):
        observed.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr("eliza_rag.eval_cli.run_golden_eval", _fake_run_golden_eval)
    monkeypatch.setattr(
        "sys.argv",
        [
            "eliza-rag-eval",
            "--manifest-output",
            "artifacts/provider_manifest.json",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {"ok": True}
    assert str(observed["manifest_output_path"]).endswith("artifacts/provider_manifest.json")
