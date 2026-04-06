from __future__ import annotations

import json

import pytest

from eliza_rag.eval_judge_cli import main


def test_eval_judge_cli_forwards_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    monkeypatch.setattr("eliza_rag.eval_judge_cli.get_settings", lambda: object())

    def _fake_judge(*args, **kwargs):
        observed.update(kwargs)
        return {"summary": {"pass": 1, "partial_pass": 0, "fail": 0}}

    monkeypatch.setattr("eliza_rag.eval_judge_cli.judge_eval_artifact", _fake_judge)
    monkeypatch.setattr(
        "sys.argv",
        [
            "eliza-rag-eval-judge",
            "eval/input.json",
            "--output",
            "eval/output.json",
        ],
    )

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {"pass": 1, "partial_pass": 0, "fail": 0}
    assert str(observed["input_path"]).endswith("eval/input.json")
    assert str(observed["output_path"]).endswith("eval/output.json")
