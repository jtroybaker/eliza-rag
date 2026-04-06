from __future__ import annotations

import json
from pathlib import Path

from .answer_generation import AnswerGenerationError, OpenAICompatibleResponsesClient
from .config import Settings

JUDGE_METHOD = "llm_judge_openrouter_quantitative"
JUDGE_RUBRIC_VERSION = "phase_10_llm_judge_v2"
JUDGE_RUBRIC_PATH = "eval/answer_judging_rubric.md"
JUDGE_SCORE_MIN = 0
JUDGE_SCORE_MAX = 5
JUDGE_DIMENSIONS = (
    "groundedness",
    "citation_quality",
    "usefulness",
    "comparison_completeness",
    "uncertainty_handling",
)
JUDGE_DIMENSION_WEIGHTS = {
    "groundedness": 0.30,
    "citation_quality": 0.25,
    "usefulness": 0.25,
    "comparison_completeness": 0.15,
    "uncertainty_handling": 0.05,
}


class EvalJudgeError(RuntimeError):
    """Raised when judge evaluation cannot complete or parse."""


def judge_eval_artifact(
    settings: Settings,
    *,
    input_path: Path,
    output_path: Path | None = None,
    invocation_command: str | None = None,
) -> dict[str, object]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise EvalJudgeError(f"{input_path} is not a saved eval artifact.")

    active_output_path = output_path or _default_output_path(input_path)
    client, prompt_template = build_eval_judge_runtime(settings)
    config = payload.get("config")
    if not isinstance(config, dict):
        config = {}
        payload["config"] = config

    config["answer_judging"] = build_answer_judging_metadata(settings)
    payload["eval_version"] = 4
    payload["judge_run_metadata"] = {
        "input_path": str(_relative_to_repo(settings, input_path)),
        "output_path": str(_relative_to_repo(settings, active_output_path)),
        "command": invocation_command,
    }

    entries = payload["entries"]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        scoring = entry.get("scoring")
        if not isinstance(scoring, dict):
            continue
        judged_answer_quality = judge_answer_quality(
            settings,
            entry=entry,
            client=client,
            prompt_template=prompt_template,
        )
        scoring["answer_quality"] = judged_answer_quality
        scoring["citation_quality"] = judged_answer_quality["citation_quality"]
        scoring["answer_usefulness"] = judged_answer_quality["usefulness"]
        retrieval = scoring.get("retrieval") if isinstance(scoring.get("retrieval"), dict) else {}
        scoring["outcome"] = resolve_eval_outcome(
            expected_ticker_coverage=bool(retrieval.get("expected_ticker_coverage")),
            requires_comparison=bool(retrieval.get("comparison_behavior_required")),
            comparison_behavior_observed=(
                bool(retrieval.get("comparison_behavior_observed"))
                if retrieval.get("comparison_behavior_observed") is not None
                else None
            ),
            contamination_severity=str(retrieval.get("contamination_severity", "none")),
            citation_quality_status=str(judged_answer_quality["citation_quality"]["status"]),
            answer_usefulness_status=str(judged_answer_quality["usefulness"]["status"]),
        )
        scoring["pass"] = scoring["outcome"] == "pass"

    payload["summary"] = summarize_eval_outcomes(entries)
    active_output_path.parent.mkdir(parents=True, exist_ok=True)
    active_output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_eval_judge_runtime(settings: Settings) -> tuple[OpenAICompatibleResponsesClient, str]:
    return build_eval_judge_client(settings), settings.eval_judge_prompt_template_path.read_text(
        encoding="utf-8"
    )


def build_answer_judging_metadata(settings: Settings) -> dict[str, object]:
    return {
        "method": JUDGE_METHOD,
        "judge_assisted": True,
        "provider": settings.judge_provider,
        "model": settings.judge_model,
        "rubric_version": JUDGE_RUBRIC_VERSION,
        "rubric_path": JUDGE_RUBRIC_PATH,
        "prompt_path": str(_relative_to_repo(settings, settings.eval_judge_prompt_template_path)),
        "score_range": {"min": JUDGE_SCORE_MIN, "max": JUDGE_SCORE_MAX},
        "aggregation": {
            "type": "weighted_average",
            "weights": JUDGE_DIMENSION_WEIGHTS,
        },
    }


def build_eval_judge_client(settings: Settings) -> OpenAICompatibleResponsesClient:
    if settings.judge_provider != "openrouter":
        raise EvalJudgeError("Only OpenRouter-backed judge evaluation is currently supported.")
    if not settings.judge_api_key:
        raise EvalJudgeError(
            "ELIZA_RAG_JUDGE_API_KEY or OPENROUTER_API_KEY is required for OpenRouter judge evaluation."
        )
    return OpenAICompatibleResponsesClient(
        api_key=settings.judge_api_key,
        model=settings.judge_model,
        base_url=settings.judge_base_url,
        provider_label="OpenRouter judge backend",
    )


def judge_answer_quality(
    settings: Settings,
    *,
    entry: dict[str, object],
    client: OpenAICompatibleResponsesClient | None = None,
    prompt_template: str | None = None,
) -> dict[str, object]:
    answer_error = entry.get("answer_error")
    answer_output = entry.get("answer_output")
    if answer_error:
        return build_errored_answer_quality(settings, str(answer_error))
    if not isinstance(answer_output, str) or not answer_output.strip():
        return build_not_evaluated_answer_quality(settings)

    active_client = client or build_eval_judge_client(settings)
    active_prompt_template = prompt_template or settings.eval_judge_prompt_template_path.read_text(
        encoding="utf-8"
    )

    prompt = _render_judge_prompt(active_prompt_template, entry)
    try:
        raw_response = active_client.generate(prompt)
    except AnswerGenerationError as exc:
        raise EvalJudgeError(str(exc)) from exc

    parsed = _parse_judge_response(raw_response)
    scorecard = _build_scorecard(parsed)
    overall_score = _aggregate_dimension_scores(scorecard)
    overall_status = _status_for_score(overall_score)
    return {
        "evaluated": True,
        "methodology": build_answer_judging_metadata(settings),
        "groundedness": scorecard["groundedness"],
        "citation_quality": scorecard["citation_quality"],
        "usefulness": scorecard["usefulness"],
        "comparison_completeness": scorecard["comparison_completeness"],
        "uncertainty_handling": scorecard["uncertainty_handling"],
        "overall": overall_status,
        "overall_score": overall_score,
        "overall_score_max": JUDGE_SCORE_MAX,
        "aggregation": {
            "type": "weighted_average",
            "weights_used": {
                name: JUDGE_DIMENSION_WEIGHTS[name]
                for name in JUDGE_DIMENSIONS
                if scorecard[name]["score"] is not None
            },
        },
        "notes": [parsed["summary"]],
        "judge_result": {
            "summary": parsed["summary"],
            "raw_response": raw_response,
        },
    }


def _render_judge_prompt(template: str, entry: dict[str, object]) -> str:
    scoring = entry.get("scoring") if isinstance(entry.get("scoring"), dict) else {}
    retrieval = scoring.get("retrieval") if isinstance(scoring.get("retrieval"), dict) else {}
    return template.format(
        query_id=json.dumps(entry.get("query_id")),
        prompt=json.dumps(entry.get("prompt")),
        expected_tickers=json.dumps(entry.get("expected_tickers", []), indent=2),
        requires_comparison=json.dumps(entry.get("requires_comparison")),
        contamination_notes=json.dumps(entry.get("contamination_notes")),
        retrieved_tickers=json.dumps(entry.get("retrieved_tickers", []), indent=2),
        retrieval_scoring=json.dumps(retrieval, indent=2),
        answer_output=json.dumps(entry.get("answer_output")),
        answer_summary=json.dumps(entry.get("answer_summary")),
        answer_findings=json.dumps(entry.get("answer_findings", []), indent=2),
        answer_citations=json.dumps(entry.get("answer_citations", []), indent=2),
        answer_uncertainty=json.dumps(entry.get("answer_uncertainty")),
    )


def _parse_judge_response(raw_response: str) -> dict[str, object]:
    candidate = raw_response.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    try:
        payload = _extract_judge_payload(candidate)
    except json.JSONDecodeError as exc:
        raise EvalJudgeError("Judge model returned invalid JSON.") from exc

    for name in JUDGE_DIMENSIONS:
        field = payload.get(name)
        if not isinstance(field, dict):
            raise EvalJudgeError(f"Judge response missing `{name}`.")
        score = field.get("score")
        rationale = field.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise EvalJudgeError(f"Judge response missing rationale for `{name}`.")
        if score is not None:
            if not isinstance(score, int):
                raise EvalJudgeError(f"Judge response had non-integer score for `{name}`.")
            if score < JUDGE_SCORE_MIN or score > JUDGE_SCORE_MAX:
                raise EvalJudgeError(
                    f"Judge response had out-of-range score for `{name}`: {score}"
                )
    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise EvalJudgeError("Judge response missing `summary`.")

    return {
        "groundedness": payload["groundedness"],
        "citation_quality": payload["citation_quality"],
        "usefulness": payload["usefulness"],
        "comparison_completeness": payload["comparison_completeness"],
        "uncertainty_handling": payload["uncertainty_handling"],
        "summary": summary.strip(),
    }


def _normalize_dimension(payload: dict[str, object]) -> dict[str, object]:
    raw_score = payload.get("score")
    score = int(raw_score) if isinstance(raw_score, int) else None
    return {
        "score": score,
        "score_max": JUDGE_SCORE_MAX,
        "status": _status_for_score(score),
        "notes": str(payload["rationale"]).strip(),
    }


def _build_scorecard(parsed: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        name: _normalize_dimension(parsed[name])
        for name in JUDGE_DIMENSIONS
    }


def _aggregate_dimension_scores(scorecard: dict[str, dict[str, object]]) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for name in JUDGE_DIMENSIONS:
        score = scorecard[name]["score"]
        if score is None:
            continue
        weight = JUDGE_DIMENSION_WEIGHTS[name]
        weighted_sum += float(score) * weight
        total_weight += weight
    if total_weight == 0.0:
        return 0.0
    return round(weighted_sum / total_weight, 2)


def _status_for_score(score: int | float | None) -> str:
    if score is None:
        return "not_applicable"
    if score >= 4.0:
        return "pass"
    if score >= 2.5:
        return "partial_pass"
    return "fail"


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return text
    return text[start:]


def _extract_judge_payload(text: str) -> dict[str, object]:
    decoder = json.JSONDecoder()
    candidate_positions = [index for index, char in enumerate(text) if char == "{"]
    for start in candidate_positions:
        try:
            payload, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and all(name in payload for name in JUDGE_DIMENSIONS):
            return payload
    payload, _ = decoder.raw_decode(_extract_json_object(text))
    if not isinstance(payload, dict):
        raise EvalJudgeError("Judge model returned a non-object JSON payload.")
    return payload


def build_errored_answer_quality(settings: Settings, answer_error: str) -> dict[str, object]:
    error_dimension = {
        "score": 0,
        "score_max": JUDGE_SCORE_MAX,
        "status": "error",
        "notes": answer_error,
    }
    return {
        "evaluated": True,
        "methodology": build_answer_judging_metadata(settings),
        "groundedness": error_dimension,
        "citation_quality": {
            "score": 0,
            "score_max": JUDGE_SCORE_MAX,
            "status": "error",
            "observed_citation_ids": [],
            "observed_tickers": [],
            "notes": answer_error,
        },
        "usefulness": error_dimension,
        "comparison_completeness": {
            "score": None,
            "score_max": JUDGE_SCORE_MAX,
            "status": "not_applicable",
            "notes": "Answer generation failed.",
        },
        "uncertainty_handling": error_dimension,
        "overall": "fail",
        "overall_score": 0.0,
        "overall_score_max": JUDGE_SCORE_MAX,
        "aggregation": {
            "type": "weighted_average",
            "weights_used": {
                "groundedness": JUDGE_DIMENSION_WEIGHTS["groundedness"],
                "citation_quality": JUDGE_DIMENSION_WEIGHTS["citation_quality"],
                "usefulness": JUDGE_DIMENSION_WEIGHTS["usefulness"],
                "uncertainty_handling": JUDGE_DIMENSION_WEIGHTS["uncertainty_handling"],
            },
        },
        "notes": [answer_error],
        "judge_result": None,
    }


def build_not_evaluated_answer_quality(settings: Settings) -> dict[str, object]:
    note = "Answer generation was not included for this eval run."
    return {
        "evaluated": False,
        "methodology": build_answer_judging_metadata(settings),
        "groundedness": {
            "score": None,
            "score_max": JUDGE_SCORE_MAX,
            "status": "not_evaluated",
            "notes": note,
        },
        "citation_quality": {
            "score": None,
            "score_max": JUDGE_SCORE_MAX,
            "status": "not_evaluated",
            "observed_citation_ids": [],
            "observed_tickers": [],
            "notes": note,
        },
        "usefulness": {
            "score": None,
            "score_max": JUDGE_SCORE_MAX,
            "status": "not_evaluated",
            "notes": note,
        },
        "comparison_completeness": {
            "score": None,
            "score_max": JUDGE_SCORE_MAX,
            "status": "not_evaluated",
            "notes": note,
        },
        "uncertainty_handling": {
            "score": None,
            "score_max": JUDGE_SCORE_MAX,
            "status": "not_evaluated",
            "notes": note,
        },
        "overall": "not_evaluated",
        "overall_score": None,
        "overall_score_max": JUDGE_SCORE_MAX,
        "aggregation": {"type": "weighted_average", "weights_used": {}},
        "notes": [note],
        "judge_result": None,
    }


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_judged.json")


def _relative_to_repo(settings: Settings, path: Path) -> Path:
    try:
        return path.relative_to(settings.repo_root)
    except ValueError:
        return path


def resolve_eval_outcome(
    *,
    expected_ticker_coverage: bool,
    requires_comparison: bool,
    comparison_behavior_observed: bool | None,
    contamination_severity: str,
    citation_quality_status: str,
    answer_usefulness_status: str,
) -> str:
    if not expected_ticker_coverage:
        return "fail"
    if requires_comparison and not comparison_behavior_observed:
        return "fail"
    if citation_quality_status in {"fail", "error"} or answer_usefulness_status in {"fail", "error"}:
        return "fail"
    if contamination_severity != "none":
        return "partial_pass"
    if citation_quality_status == "partial_pass" or answer_usefulness_status == "partial_pass":
        return "partial_pass"
    return "pass"


def summarize_eval_outcomes(entries: list[dict[str, object]]) -> dict[str, int]:
    summary = {"pass": 0, "partial_pass": 0, "fail": 0}
    for entry in entries:
        scoring = entry.get("scoring")
        if not isinstance(scoring, dict):
            continue
        outcome = scoring.get("outcome")
        if outcome in summary:
            summary[str(outcome)] += 1
    return summary
