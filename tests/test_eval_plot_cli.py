from __future__ import annotations

import pytest

from eliza_rag.eval_plot_cli import main


def test_eval_plot_cli_forwards_output_and_paths(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    monkeypatch.setattr(
        "eliza_rag.eval_plot_cli.get_settings",
        lambda: type("Settings", (), {"eval_dir": "/tmp/eval"})(),
    )

    def _fake_generate(eval_dir, *, output_path, explicit_paths=None):
        observed["eval_dir"] = eval_dir
        observed["output_path"] = output_path
        observed["explicit_paths"] = explicit_paths

    monkeypatch.setattr("eliza_rag.eval_plot_cli.generate_eval_plot", _fake_generate)
    monkeypatch.setattr(
        "sys.argv",
        ["eliza-rag-eval-plot", "eval/a.json", "--output", "eval/out.png"],
    )

    main()

    assert str(observed["output_path"]).endswith("eval/out.png")
    assert len(observed["explicit_paths"]) == 1
    assert str(observed["explicit_paths"][0]).endswith("eval/a.json")
    assert str(capsys.readouterr().out).strip().endswith("eval/out.png")
