from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .answer_generation import AnswerGenerationError, generate_answer
from .config import Settings
from .embeddings import DenseIndexMetadata, load_dense_index_metadata
from .eval_judging import (
    build_answer_judging_metadata,
    build_eval_judge_runtime,
    build_not_evaluated_answer_quality,
    judge_answer_quality,
    resolve_eval_outcome,
    summarize_eval_outcomes,
)
from .models import RetrievalFilters
from .retrieval import analyze_query, retrieve


@dataclass(frozen=True, slots=True)
class GoldenEvalCase:
    query_id: str
    prompt: str
    expected_tickers: list[str]
    requires_comparison: bool
    contamination_notes: str | None = None
    filters: RetrievalFilters | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "prompt": self.prompt,
            "expected_tickers": list(self.expected_tickers),
            "requires_comparison": self.requires_comparison,
            "contamination_notes": self.contamination_notes,
            "filters": self.filters.to_dict() if self.filters else None,
        }


def load_golden_eval_cases(path: Path) -> list[GoldenEvalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        GoldenEvalCase(
            query_id=str(item["query_id"]),
            prompt=str(item["prompt"]),
            expected_tickers=[str(ticker) for ticker in item["expected_tickers"]],
            requires_comparison=bool(item["requires_comparison"]),
            contamination_notes=(
                str(item["contamination_notes"])
                if item.get("contamination_notes") is not None
                else None
            ),
            filters=_filters_from_payload(item.get("filters")),
        )
        for item in payload["cases"]
    ]


def emit_build_manifest(settings: Settings, *, output_path: Path | None = None) -> dict[str, object]:
    dense_metadata = _load_optional_dense_metadata(settings)
    embedding_model = dense_metadata.model if dense_metadata is not None else settings.dense_embedding_model
    embedding_dimension = (
        dense_metadata.dimension if dense_metadata is not None else settings.dense_embedding_dim
    )
    payload = {
        "manifest_version": 1,
        "chunking": {
            "chunk_size_tokens": settings.chunk_size_tokens,
            "chunk_overlap_tokens": settings.chunk_overlap_tokens,
        },
        "tables": {
            "lexical": settings.lancedb_table_name,
            "dense": settings.dense_lancedb_table_name,
        },
        "dense_index": {
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dimension,
            "metric": settings.dense_index_metric,
        },
        "reranker": {
            "default": settings.reranker_type,
            "candidate_pool": settings.rerank_candidate_pool,
            "enabled_by_default": settings.enable_rerank,
        },
        "artifacts": {
            "corpus_manifest": str(_relative_to_repo(settings, settings.manifest_path)),
            "chunk_records": str(_relative_to_repo(settings, settings.chunk_artifact_path)),
            "dense_index_metadata": str(
                _relative_to_repo(settings, settings.dense_index_artifact_path)
            ),
            "golden_eval_set": str(_relative_to_repo(settings, settings.golden_eval_artifact_path)),
            "final_prompt_template": str(
                _relative_to_repo(settings, settings.final_prompt_template_path)
            ),
        },
    }
    destination = output_path or settings.build_manifest_output_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def run_golden_eval(
    settings: Settings,
    *,
    golden_eval_path: Path | None = None,
    output_path: Path | None = None,
    manifest_output_path: Path | None = None,
    mode: str = "targeted_hybrid",
    top_k: int | None = None,
    phrase_query: bool = False,
    include_answer: bool = False,
    enable_rerank: bool | None = None,
    reranker: str | None = None,
    rerank_candidate_pool: int | None = None,
    invocation_command: str | None = None,
) -> dict[str, object]:
    cases_path = golden_eval_path or settings.golden_eval_artifact_path
    cases = load_golden_eval_cases(cases_path)
    manifest_path = manifest_output_path or settings.build_manifest_output_path
    manifest_payload = emit_build_manifest(settings, output_path=manifest_path)
    eval_payload = {
        "eval_version": 3,
        "golden_eval_set": str(_relative_to_repo(settings, cases_path)),
        "build_manifest_path": str(_relative_to_repo(settings, manifest_path)),
        "run_metadata": {
            "command": invocation_command,
            "output_path": (
                str(_relative_to_repo(settings, output_path)) if output_path is not None else None
            ),
            "manifest_output_path": str(_relative_to_repo(settings, manifest_path)),
        },
        "config": {
            "retrieval_mode": mode,
            "top_k": top_k or settings.retrieval_top_k,
            "phrase_query": phrase_query,
            "include_answer": include_answer,
            "reranking": {
                "enabled": (
                    enable_rerank
                    if enable_rerank is not None
                    else bool(settings.enable_rerank or reranker or rerank_candidate_pool)
                ),
                "reranker": reranker or settings.reranker_type,
                "candidate_pool": rerank_candidate_pool or settings.rerank_candidate_pool,
            },
            "answer_judging": build_answer_judging_metadata(settings),
        },
        "scoring_status": {
            "implemented": True,
            "note": (
                "Pass, partial_pass, and fail are assigned from explicit retrieval outcomes plus "
                "OpenRouter-backed quantitative answer judging when answers are included."
            ),
        },
        "entries": [],
        "build_manifest": manifest_payload,
    }
    judge_client = None
    judge_prompt_template = None
    if include_answer:
        judge_client, judge_prompt_template = build_eval_judge_runtime(settings)

    for case in cases:
        structured_query = analyze_query(case.prompt, filters=case.filters, settings=settings)
        results = retrieve(
            settings,
            case.prompt,
            mode=mode,
            top_k=top_k,
            filters=case.filters,
            phrase_query=phrase_query,
            enable_rerank=enable_rerank,
            reranker=reranker,
            rerank_candidate_pool=rerank_candidate_pool,
        )
        retrieved_tickers = _unique_preserve_order(result.ticker for result in results)
        entry: dict[str, object] = {
            **case.to_dict(),
            "structured_query": structured_query.to_dict(),
            "retrieved_tickers": retrieved_tickers,
            "retrieved_chunk_ids": [result.chunk_id for result in results],
            "retrieval_result_count": len(results),
            "answer_output": None,
            "answer_summary": None,
            "answer_findings": None,
            "answer_citations": None,
            "answer_uncertainty": None,
            "answer_model": None,
            "answer_error": None,
            "scoring": {},
        }

        answer_response: AnswerResponse | None = None
        if include_answer:
            try:
                answer_response = generate_answer(
                    settings,
                    case.prompt,
                    mode=mode,
                    top_k=top_k,
                    filters=case.filters,
                    phrase_query=phrase_query,
                    enable_rerank=enable_rerank,
                    reranker=reranker,
                    rerank_candidate_pool=rerank_candidate_pool,
                )
            except AnswerGenerationError as exc:
                entry["answer_error"] = str(exc)
            else:
                entry["answer_output"] = answer_response.answer
                entry["answer_summary"] = answer_response.summary
                entry["answer_findings"] = [finding.to_dict() for finding in answer_response.findings]
                entry["answer_citations"] = [citation.to_dict() for citation in answer_response.citations]
                entry["answer_uncertainty"] = answer_response.uncertainty
                entry["answer_model"] = answer_response.model

        entry["scoring"] = _score_eval_entry(
            settings,
            case,
            entry=entry,
            retrieved_tickers=retrieved_tickers,
            judge_client=judge_client,
            judge_prompt_template=judge_prompt_template,
        )

        eval_payload["entries"].append(entry)

    eval_payload["summary"] = summarize_eval_outcomes(eval_payload["entries"])

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(eval_payload, indent=2), encoding="utf-8")

    return eval_payload


def _filters_from_payload(payload: object) -> RetrievalFilters | None:
    if not isinstance(payload, dict):
        return None
    return RetrievalFilters(
        tickers=[str(value) for value in payload["tickers"]] if payload.get("tickers") else None,
        form_types=(
            [str(value) for value in payload["form_types"]]
            if payload.get("form_types")
            else None
        ),
        filing_date_from=(
            str(payload["filing_date_from"]) if payload.get("filing_date_from") else None
        ),
        filing_date_to=str(payload["filing_date_to"]) if payload.get("filing_date_to") else None,
    )


def _relative_to_repo(settings: Settings, path: Path) -> Path:
    try:
        return path.relative_to(settings.repo_root)
    except ValueError:
        return path


def _load_optional_dense_metadata(settings: Settings) -> DenseIndexMetadata | None:
    if not settings.dense_index_artifact_path.exists():
        return None
    return load_dense_index_metadata(settings)


def _unique_preserve_order(values: list[str] | tuple[str, ...] | object) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = str(value)
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _score_eval_entry(
    settings: Settings,
    case: GoldenEvalCase,
    *,
    entry: dict[str, object],
    retrieved_tickers: list[str],
    judge_client: object | None,
    judge_prompt_template: str | None,
) -> dict[str, object]:
    expected_ticker_set = set(case.expected_tickers)
    retrieved_ticker_set = set(retrieved_tickers)
    expected_ticker_coverage = all(ticker in retrieved_ticker_set for ticker in case.expected_tickers)
    comparison_behavior_observed = (
        len(retrieved_ticker_set.intersection(expected_ticker_set)) >= 2
        if case.requires_comparison
        else None
    )
    contamination_tickers = [
        ticker for ticker in _unique_preserve_order(retrieved_tickers) if ticker not in expected_ticker_set
    ]
    contamination_observed = bool(contamination_tickers)
    contamination_severity = _score_contamination_severity(
        expected_ticker_count=len(case.expected_tickers),
        contamination_tickers=contamination_tickers,
    )
    retrieval_scoring = {
        "expected_ticker_coverage": expected_ticker_coverage,
        "comparison_behavior_required": case.requires_comparison,
        "comparison_behavior_observed": comparison_behavior_observed,
        "contamination_observed": contamination_observed,
        "contamination_tickers": contamination_tickers,
        "contamination_severity": contamination_severity,
    }
    answer_quality = (
        judge_answer_quality(
            settings,
            entry=entry,
            client=judge_client,
            prompt_template=judge_prompt_template,
        )
        if isinstance(entry.get("answer_output"), str) or entry.get("answer_error") is not None
        else build_not_evaluated_answer_quality(settings)
    )
    citation_quality = answer_quality["citation_quality"]
    answer_usefulness = answer_quality["usefulness"]
    outcome = resolve_eval_outcome(
        expected_ticker_coverage=expected_ticker_coverage,
        requires_comparison=case.requires_comparison,
        comparison_behavior_observed=comparison_behavior_observed,
        contamination_severity=contamination_severity,
        citation_quality_status=str(citation_quality["status"]),
        answer_usefulness_status=str(answer_usefulness["status"]),
    )
    notes = _build_score_notes(
        contamination_tickers=contamination_tickers,
        answer_error=entry.get("answer_error"),
        citation_quality_status=str(citation_quality["status"]),
        answer_usefulness_status=str(answer_usefulness["status"]),
    )
    return {
        "retrieval": retrieval_scoring,
        "answer_quality": answer_quality,
        "expected_ticker_coverage": expected_ticker_coverage,
        "comparison_behavior_required": case.requires_comparison,
        "comparison_behavior_observed": comparison_behavior_observed,
        "contamination_observed": contamination_observed,
        "contamination_tickers": contamination_tickers,
        "contamination_severity": contamination_severity,
        "citation_quality": citation_quality,
        "answer_usefulness": answer_usefulness,
        "outcome": outcome,
        "pass": outcome == "pass",
        "notes": notes or None,
    }


def _score_contamination_severity(
    *,
    expected_ticker_count: int,
    contamination_tickers: list[str],
) -> str:
    contamination_count = len(contamination_tickers)
    if contamination_count == 0:
        return "none"
    if expected_ticker_count <= 1 or contamination_count >= expected_ticker_count:
        return "high"
    return "moderate"


def _build_score_notes(
    *,
    contamination_tickers: list[str],
    answer_error: object,
    citation_quality_status: str,
    answer_usefulness_status: str,
) -> list[str]:
    notes: list[str] = []
    if contamination_tickers:
        notes.append(f"Unexpected retrieved tickers: {', '.join(contamination_tickers)}.")
    if answer_error:
        notes.append(f"Answer generation error: {answer_error}")
    if citation_quality_status == "not_evaluated":
        notes.append("Citation quality was not evaluated because answers were not included.")
    if answer_usefulness_status == "not_evaluated":
        notes.append("Answer usefulness was not evaluated because answers were not included.")
    return notes
