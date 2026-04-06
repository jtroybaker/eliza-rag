from __future__ import annotations

import json

import pytest

from eliza_rag.eval_report_cli import main


def test_eval_report_cli_renders_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "eliza_rag.eval_report_cli.get_settings",
        lambda: type("Settings", (), {"eval_dir": "/tmp/eval"})(),
    )
    monkeypatch.setattr(
        "eliza_rag.eval_report_cli.discover_eval_artifacts",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        "eliza_rag.eval_report_cli.build_eval_report",
        lambda *args, **kwargs: {"run_count": 0, "runs": [], "query_rows": [], "failure_clusters": []},
    )
    monkeypatch.setattr(
        "sys.argv",
        ["eliza-rag-eval-report", "--format", "json"],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["run_count"] == 0
