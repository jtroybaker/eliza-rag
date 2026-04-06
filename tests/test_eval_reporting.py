from __future__ import annotations

import json
from pathlib import Path

from eliza_rag.eval_reporting import (
    build_eval_report,
    discover_eval_artifacts,
    render_markdown_report,
)


def _write_eval_artifact(
    path: Path,
    *,
    include_answer: bool,
    outcome: str,
    answer_overall: str,
    groundedness: str,
    embedder: str = "Snowflake/snowflake-arctic-embed-xs",
    reranker: str = "bge-reranker-v2-m3",
) -> None:
    path.write_text(
        json.dumps(
            {
                "eval_version": 3,
                "config": {
                    "retrieval_mode": "targeted_hybrid",
                    "include_answer": include_answer,
                    "reranking": {"enabled": True, "reranker": reranker},
                    "answer_judging": {"method": "heuristic_only"},
                },
                "build_manifest": {
                    "dense_index": {
                        "embedding_model": embedder,
                    }
                },
                "entries": [
                    {
                        "query_id": "q1",
                        "scoring": {
                            "outcome": outcome,
                            "answer_quality": {
                                "overall": answer_overall,
                                "groundedness": {"status": groundedness},
                                "comparison_completeness": {"status": "pass"},
                            },
                        },
                    }
                ],
                "summary": {
                    "pass": 1 if outcome == "pass" else 0,
                    "partial_pass": 1 if outcome == "partial_pass" else 0,
                    "fail": 1 if outcome == "fail" else 0,
                },
            }
        ),
        encoding="utf-8",
    )


def test_discover_eval_artifacts_skips_golden_set(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    (eval_dir / "golden_queries.json").write_text("{}", encoding="utf-8")
    (eval_dir / "baseline_targeted_hybrid_retrieval.json").write_text('{"entries":[]}', encoding="utf-8")
    (eval_dir / "run_a.json").write_text('{"entries":[]}', encoding="utf-8")
    (eval_dir / "run_answer.json").write_text('{"entries":[]}', encoding="utf-8")
    (eval_dir / "run_a_judged.json").write_text('{"entries":[]}', encoding="utf-8")

    paths = discover_eval_artifacts(eval_dir)

    assert [path.name for path in paths] == ["run_answer.json"]


def test_discover_eval_artifacts_keeps_explicit_judged_paths(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    judged = eval_dir / "run_a_judged.json"
    judged.write_text('{"entries":[]}', encoding="utf-8")

    paths = discover_eval_artifacts(eval_dir, [judged])

    assert [path.name for path in paths] == ["run_a_judged.json"]


def test_build_eval_report_summarizes_runs(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    run_a = eval_dir / "run_a.json"
    run_b = eval_dir / "run_b.json"
    _write_eval_artifact(
        run_a,
        include_answer=False,
        outcome="pass",
        answer_overall="not_evaluated",
        groundedness="not_evaluated",
    )
    _write_eval_artifact(
        run_b,
        include_answer=True,
        outcome="partial_pass",
        answer_overall="partial_pass",
        groundedness="pass",
    )

    report = build_eval_report([run_a, run_b])

    assert report["run_count"] == 2
    assert report["runs"][1]["include_answer"] is True
    assert report["runs"][0]["embedder"] == "snowflake-arctic-embed-xs"
    assert report["runs"][1]["display_label"] == "snowflake-arctic-embed-xs + bge-reranker-v2-m3"
    assert report["runs"][1]["plot_label"] == "sf+m3"
    assert report["query_rows"][0]["runs"][1]["answer_overall"] == "partial_pass"
    assert report["query_rows"][0]["runs"][1]["answer_overall_score"] == "n/a"
    assert report["failure_clusters"][0]["query_id"] == "q1"


def test_render_markdown_report_includes_query_matrix(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    run_a = eval_dir / "run_a.json"
    _write_eval_artifact(
        run_a,
        include_answer=True,
        outcome="pass",
        answer_overall="pass",
        groundedness="pass",
    )

    report = build_eval_report([run_a])
    rendered = render_markdown_report(report)

    assert "# Eval Artifact Report" in rendered
    assert "| Run | Embedder | Reranker | Mode | Include Answer | Answer Judging | Pass | Partial | Fail |" in rendered
    assert "| Query | Run | Outcome | Answer Overall | Answer Score | Groundedness | Comparison Completeness |" in rendered
    assert "| q1 | snowflake-arctic-embed-xs + bge-reranker-v2-m3 | pass | pass | n/a | pass | pass |" in rendered
