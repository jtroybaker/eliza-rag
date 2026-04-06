from __future__ import annotations

import json
from pathlib import Path


def discover_eval_artifacts(eval_dir: Path, explicit_paths: list[Path] | None = None) -> list[Path]:
    if explicit_paths:
        return sorted(path.resolve() for path in explicit_paths)
    return sorted(
        path.resolve()
        for path in eval_dir.glob("*.json")
        if path.name.endswith("_answer.json")
        and not path.name.endswith("_judged.json")
    )


def load_eval_artifact(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise ValueError(f"{path} is not a saved eval artifact.")
    return payload


def build_eval_report(paths: list[Path]) -> dict[str, object]:
    runs = [summarize_eval_artifact(path, load_eval_artifact(path)) for path in paths]
    query_rows = _build_query_rows(runs)
    return {
        "run_count": len(runs),
        "runs": runs,
        "query_rows": query_rows,
        "failure_clusters": [
            row
            for row in query_rows
            if any(cell["outcome"] not in {"pass", "not_scored"} for cell in row["runs"])
        ],
    }


def summarize_eval_artifact(path: Path, payload: dict[str, object]) -> dict[str, object]:
    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    reranking = config.get("reranking") if isinstance(config, dict) else {}
    build_manifest = (
        payload.get("build_manifest") if isinstance(payload.get("build_manifest"), dict) else {}
    )
    dense_index = (
        build_manifest.get("dense_index")
        if isinstance(build_manifest, dict) and isinstance(build_manifest.get("dense_index"), dict)
        else {}
    )
    entries = payload.get("entries") if isinstance(payload.get("entries"), list) else []
    answer_judging = config.get("answer_judging") if isinstance(config, dict) else {}
    summarized_entries = [summarize_eval_entry(entry) for entry in entries if isinstance(entry, dict)]
    embedder = _resolve_embedder(path, dense_index)
    reranker = (
        reranking.get("reranker")
        if isinstance(reranking, dict) and reranking.get("enabled")
        else "disabled"
    )
    return {
        "path": str(path),
        "label": path.stem,
        "display_label": _build_run_display_label(
            path.stem,
            embedder=embedder,
            reranker=reranker,
            include_answer=bool(config.get("include_answer")),
        ),
        "plot_label": _build_run_plot_label(
            embedder=embedder,
            reranker=reranker,
            include_answer=bool(config.get("include_answer")),
        ),
        "eval_version": payload.get("eval_version"),
        "retrieval_mode": config.get("retrieval_mode"),
        "include_answer": bool(config.get("include_answer")),
        "embedder": embedder,
        "reranker": reranker,
        "answer_judging_method": (
            answer_judging.get("method")
            if isinstance(answer_judging, dict)
            else None
        ),
        "summary": _summarize_entry_outcomes(summarized_entries),
        "entries": summarized_entries,
    }


def summarize_eval_entry(entry: dict[str, object]) -> dict[str, object]:
    scoring = entry.get("scoring") if isinstance(entry.get("scoring"), dict) else {}
    answer_quality = (
        scoring.get("answer_quality")
        if isinstance(scoring.get("answer_quality"), dict)
        else {}
    )
    groundedness = (
        answer_quality.get("groundedness")
        if isinstance(answer_quality, dict) and isinstance(answer_quality.get("groundedness"), dict)
        else {}
    )
    comparison_completeness = (
        answer_quality.get("comparison_completeness")
        if isinstance(answer_quality, dict)
        and isinstance(answer_quality.get("comparison_completeness"), dict)
        else {}
    )
    return {
        "query_id": entry.get("query_id"),
        "outcome": str(scoring.get("outcome", "not_scored")),
        "answer_overall": _resolve_answer_overall(scoring),
        "answer_overall_score": _resolve_answer_overall_score(scoring),
        "groundedness": groundedness.get("status", "not_evaluated"),
        "comparison_completeness": comparison_completeness.get("status", "not_evaluated"),
    }


def render_markdown_report(report: dict[str, object]) -> str:
    lines = [
        "# Eval Artifact Report",
        "",
        f"Artifacts compared: {report['run_count']}",
        "",
        "## Run Summary",
        "",
        "| Run | Embedder | Reranker | Mode | Include Answer | Answer Judging | Pass | Partial | Fail |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for run in report["runs"]:
        summary = run["summary"]
        lines.append(
            "| {label} | {embedder} | {reranker} | {retrieval_mode} | {include_answer} | {answer_judging_method} | {pass_count} | {partial_count} | {fail_count} |".format(
                label=run["display_label"],
                embedder=run["embedder"],
                retrieval_mode=run["retrieval_mode"],
                reranker=run["reranker"],
                include_answer="yes" if run["include_answer"] else "no",
                answer_judging_method=run["answer_judging_method"] or "n/a",
                pass_count=summary["pass"],
                partial_count=summary["partial_pass"],
                fail_count=summary["fail"],
            )
        )

    lines.extend(
        [
            "",
            "## Query Matrix",
            "",
            "| Query | Run | Outcome | Answer Overall | Answer Score | Groundedness | Comparison Completeness |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["query_rows"]:
        for cell in row["runs"]:
            lines.append(
                "| {query_id} | {run_label} | {outcome} | {answer_overall} | {answer_overall_score} | {groundedness} | {comparison_completeness} |".format(
                    query_id=row["query_id"],
                    run_label=cell["label"],
                    outcome=cell["outcome"],
                    answer_overall=cell["answer_overall"],
                    answer_overall_score=cell["answer_overall_score"],
                    groundedness=cell["groundedness"],
                    comparison_completeness=cell["comparison_completeness"],
                )
            )

    failures = report["failure_clusters"]
    if failures:
        lines.extend(["", "## Failure Clusters", ""])
        for row in failures:
            failing_runs = ", ".join(
                f"{cell['label']} ({cell['outcome']})"
                for cell in row["runs"]
                if cell["outcome"] not in {"pass", "not_scored"}
            )
            lines.append(f"- `{row['query_id']}`: {failing_runs}")

    return "\n".join(lines) + "\n"


def _build_query_rows(runs: list[dict[str, object]]) -> list[dict[str, object]]:
    query_ids = sorted(
        {
            str(entry["query_id"])
            for run in runs
            for entry in run["entries"]
            if entry.get("query_id") is not None
        }
    )
    rows: list[dict[str, object]] = []
    for query_id in query_ids:
        cells: list[dict[str, object]] = []
        for run in runs:
            match = next((entry for entry in run["entries"] if entry["query_id"] == query_id), None)
            if match is None:
                continue
            cells.append(
                {
                    "label": run["display_label"],
                    "plot_label": run.get("plot_label", run["display_label"]),
                    "outcome": match["outcome"],
                    "answer_overall": match["answer_overall"],
                    "answer_overall_score": match["answer_overall_score"],
                    "groundedness": match["groundedness"],
                    "comparison_completeness": match["comparison_completeness"],
                }
            )
        rows.append({"query_id": query_id, "runs": cells})
    return rows


def _resolve_answer_overall_score(scoring: dict[str, object]) -> str:
    answer_quality = scoring.get("answer_quality")
    if isinstance(answer_quality, dict):
        overall_score = answer_quality.get("overall_score")
        if isinstance(overall_score, (int, float)):
            return f"{overall_score:.2f}"
    return "n/a"


def _resolve_answer_overall(scoring: dict[str, object]) -> str:
    answer_quality = scoring.get("answer_quality")
    if isinstance(answer_quality, dict):
        overall = answer_quality.get("overall")
        if isinstance(overall, str):
            return overall

    citation_quality = scoring.get("citation_quality")
    answer_usefulness = scoring.get("answer_usefulness")
    citation_status = (
        citation_quality.get("status")
        if isinstance(citation_quality, dict)
        else "not_evaluated"
    )
    usefulness_status = (
        answer_usefulness.get("status")
        if isinstance(answer_usefulness, dict)
        else "not_evaluated"
    )
    statuses = {citation_status, usefulness_status}
    if statuses.issubset({"not_evaluated", "not_applicable"}):
        return "not_evaluated"
    if "error" in statuses or "fail" in statuses:
        return "fail"
    if "partial_pass" in statuses:
        return "partial_pass"
    return "pass"


def _summarize_entry_outcomes(entries: list[dict[str, object]]) -> dict[str, int]:
    summary = {"pass": 0, "partial_pass": 0, "fail": 0}
    for entry in entries:
        outcome = entry["outcome"]
        if outcome in summary:
            summary[outcome] += 1
    return summary


def _resolve_embedder(path: Path, dense_index: dict[str, object]) -> str:
    embedding_model = dense_index.get("embedding_model") if isinstance(dense_index, dict) else None
    if embedding_model == "Snowflake/snowflake-arctic-embed-xs":
        return "snowflake-arctic-embed-xs"
    if embedding_model == "hashed_v1":
        return "hashed_v1"
    if isinstance(embedding_model, str) and embedding_model:
        return embedding_model
    if "hashed_v1" in path.stem:
        return "hashed_v1"
    if "snowflake" in path.stem:
        return "snowflake-arctic-embed-xs"
    return "unknown"


def _build_run_display_label(
    stem: str,
    *,
    embedder: str,
    reranker: str,
    include_answer: bool,
) -> str:
    if stem == "baseline_targeted_hybrid_retrieval":
        return "legacy baseline retrieval-only"
    return f"{embedder} + {reranker}"


def _build_run_plot_label(
    *,
    embedder: str,
    reranker: str,
    include_answer: bool,
) -> str:
    embedder_label = {
        "snowflake-arctic-embed-xs": "sf",
        "hashed_v1": "hash",
    }.get(embedder, embedder)
    reranker_label = {
        "bge-reranker-v2-m3": "m3",
        "bge-reranker-base": "base",
        "heuristic": "heur",
        "disabled": "off",
    }.get(reranker, reranker)
    return f"{embedder_label}+{reranker_label}"
