from __future__ import annotations

import json
from pathlib import Path

import pytest

from eliza_rag.answer_generation import AnswerResponse
from eliza_rag.config import Settings
from eliza_rag.evals import emit_build_manifest, load_golden_eval_cases, run_golden_eval
from eliza_rag.models import (
    AnswerCitation,
    AnswerFinding,
    RetrievalFilters,
    RetrievalResult,
    StructuredQuery,
)


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "repo_root": tmp_path,
        "data_dir": tmp_path / "data",
        "artifacts_dir": tmp_path / "artifacts",
        "prompts_dir": tmp_path / "prompts",
        "quality_notes_path": tmp_path / "QUALITY_NOTES.md",
        "prompt_iteration_log_path": tmp_path / "PROMPT_ITERATION_LOG.md",
        "corpus_dir": tmp_path / "edgar_corpus",
        "corpus_zip_path": tmp_path / "edgar_corpus.zip",
        "lancedb_dir": tmp_path / "data" / "lancedb",
        "lancedb_table_name": "filing_chunks",
        "dense_lancedb_table_name": "filing_chunks_dense",
        "dense_index_artifact_name": "dense_index_metadata.json",
        "lancedb_remote_repo_id": None,
        "lancedb_remote_repo_type": "dataset",
        "lancedb_remote_revision": None,
        "lancedb_remote_token": None,
        "lancedb_remote_auto_download": True,
        "lancedb_archive_url": None,
        "lancedb_archive_auto_download": True,
        "chunk_size_tokens": 800,
        "chunk_overlap_tokens": 100,
        "retrieval_top_k": 8,
        "answer_top_k": 6,
        "enable_rerank": False,
        "reranker_type": "heuristic",
        "rerank_candidate_pool": 12,
        "dense_embedding_model": "Snowflake/snowflake-arctic-embed-xs",
        "dense_embedding_dim": 256,
        "dense_index_metric": "cosine",
        "llm_provider": "openai",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_api_key": None,
        "llm_model": "gpt-5-mini",
        "judge_provider": "openrouter",
        "judge_base_url": "https://openrouter.ai/api/v1",
        "judge_api_key": "test-key",
        "judge_model": "qwen/qwen3.6-plus:free",
        "local_llm_runtime": "ollama",
        "local_llm_runtime_command": "ollama",
        "local_llm_base_url": "http://127.0.0.1:11434/v1",
        "local_llm_model": "qwen2.5:3b-instruct",
        "local_llm_start_timeout_seconds": 1,
    }
    values.update(overrides)
    return Settings(**values)


def test_load_golden_eval_cases_reads_filters(tmp_path: Path) -> None:
    path = tmp_path / "golden_queries.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": [
                    {
                        "query_id": "q1",
                        "prompt": "Apple risk factors",
                        "expected_tickers": ["AAPL"],
                        "requires_comparison": False,
                        "filters": {
                            "tickers": ["AAPL"],
                            "form_types": ["10-K"],
                            "filing_date_from": "2024-01-01",
                            "filing_date_to": "2025-12-31",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    cases = load_golden_eval_cases(path)

    assert len(cases) == 1
    assert cases[0].filters == RetrievalFilters(
        tickers=["AAPL"],
        form_types=["10-K"],
        filing_date_from="2024-01-01",
        filing_date_to="2025-12-31",
    )


def test_emit_build_manifest_uses_dense_metadata_dimension(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.prompts_dir.mkdir(parents=True, exist_ok=True)
    settings.corpus_dir.mkdir(parents=True, exist_ok=True)
    settings.final_prompt_template_path.write_text("prompt", encoding="utf-8")
    settings.manifest_path.write_text("{}", encoding="utf-8")
    settings.dense_index_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    settings.dense_index_artifact_path.write_text(
        json.dumps(
            {
                "model": "Snowflake/snowflake-arctic-embed-xs",
                "dimension": 384,
                "document_count": 10,
                "document_frequency_by_bucket": [],
            }
        ),
        encoding="utf-8",
    )

    payload = emit_build_manifest(settings)

    assert payload["dense_index"]["embedding_dimension"] == 384
    assert settings.build_manifest_output_path.exists()


def test_run_golden_eval_writes_expected_shape(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.prompts_dir.mkdir(parents=True, exist_ok=True)
    settings.corpus_dir.mkdir(parents=True, exist_ok=True)
    settings.eval_dir.mkdir(parents=True, exist_ok=True)
    settings.final_prompt_template_path.write_text("prompt", encoding="utf-8")
    settings.manifest_path.write_text("{}", encoding="utf-8")
    settings.golden_eval_artifact_path.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": [
                    {
                        "query_id": "q1",
                        "prompt": "Compare Apple and Tesla risk factors",
                        "expected_tickers": ["AAPL", "TSLA"],
                        "requires_comparison": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "eliza_rag.evals.analyze_query",
        lambda prompt, filters=None, settings=None: StructuredQuery(
            raw_query=prompt,
            retrieval_text=prompt,
            lexical_query=prompt,
            dense_query=prompt,
            expansion_terms=[],
            detected_tickers=["AAPL", "TSLA"],
            detected_company_names=["Apple", "Tesla"],
            target_tickers=["AAPL", "TSLA"],
            is_multi_company=True,
            is_comparison_query=True,
            requires_entity_coverage=True,
        ),
    )
    monkeypatch.setattr(
        "eliza_rag.evals.retrieve",
        lambda *args, **kwargs: [
            RetrievalResult(
                chunk_id="AAPL::1",
                filing_id="AAPL_10K_2025",
                ticker="AAPL",
                form_type="10-K",
                filing_date="2025-01-31",
                section="Risk Factors",
                section_path="Item 1A",
                text="Apple text",
                raw_score=1.0,
                retrieval_mode="lexical",
                rank=1,
            ),
            RetrievalResult(
                chunk_id="TSLA::2",
                filing_id="TSLA_10K_2025",
                ticker="TSLA",
                form_type="10-K",
                filing_date="2025-01-30",
                section="Risk Factors",
                section_path="Item 1A",
                text="Tesla text",
                raw_score=0.9,
                retrieval_mode="lexical",
                rank=2,
            ),
        ],
    )

    output_path = settings.eval_dir / "baseline.json"
    payload = run_golden_eval(settings, output_path=output_path, enable_rerank=True)

    assert payload["config"]["reranking"]["enabled"] is True
    assert payload["config"]["answer_judging"]["method"] == "llm_judge_openrouter_quantitative"
    assert payload["scoring_status"]["implemented"] is True
    assert payload["entries"][0]["retrieved_tickers"] == ["AAPL", "TSLA"]
    assert payload["entries"][0]["scoring"]["retrieval"]["expected_ticker_coverage"] is True
    assert payload["entries"][0]["scoring"]["expected_ticker_coverage"] is True
    assert payload["entries"][0]["scoring"]["comparison_behavior_observed"] is True
    assert payload["entries"][0]["scoring"]["answer_quality"]["overall"] == "not_evaluated"
    assert payload["entries"][0]["scoring"]["answer_quality"]["overall_score"] is None
    assert payload["entries"][0]["scoring"]["outcome"] == "pass"
    assert payload["summary"] == {"pass": 1, "partial_pass": 0, "fail": 0}
    assert output_path.exists()


def test_run_golden_eval_marks_contaminated_single_company_result_as_partial_pass(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    settings.prompts_dir.mkdir(parents=True, exist_ok=True)
    settings.corpus_dir.mkdir(parents=True, exist_ok=True)
    settings.eval_dir.mkdir(parents=True, exist_ok=True)
    settings.final_prompt_template_path.write_text("prompt", encoding="utf-8")
    settings.manifest_path.write_text("{}", encoding="utf-8")
    settings.golden_eval_artifact_path.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": [
                    {
                        "query_id": "q1",
                        "prompt": "Apple risk factors",
                        "expected_tickers": ["AAPL"],
                        "requires_comparison": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "eliza_rag.evals.analyze_query",
        lambda prompt, filters=None, settings=None: StructuredQuery(
            raw_query=prompt,
            retrieval_text=prompt,
            lexical_query=prompt,
            dense_query=prompt,
            expansion_terms=[],
            detected_tickers=["AAPL"],
            detected_company_names=["Apple"],
            target_tickers=["AAPL"],
        ),
    )
    monkeypatch.setattr(
        "eliza_rag.evals.retrieve",
        lambda *args, **kwargs: [
            RetrievalResult(
                chunk_id="AAPL::1",
                filing_id="AAPL_10K_2025",
                ticker="AAPL",
                form_type="10-K",
                filing_date="2025-01-31",
                section="Risk Factors",
                section_path="Item 1A",
                text="Apple text",
                raw_score=1.0,
                retrieval_mode="lexical",
                rank=1,
            ),
            RetrievalResult(
                chunk_id="MSFT::2",
                filing_id="MSFT_10K_2025",
                ticker="MSFT",
                form_type="10-K",
                filing_date="2025-01-31",
                section="Risk Factors",
                section_path="Item 1A",
                text="Microsoft text",
                raw_score=0.8,
                retrieval_mode="lexical",
                rank=2,
            ),
        ],
    )

    payload = run_golden_eval(settings)

    scoring = payload["entries"][0]["scoring"]
    assert scoring["expected_ticker_coverage"] is True
    assert scoring["contamination_observed"] is True
    assert scoring["contamination_tickers"] == ["MSFT"]
    assert scoring["contamination_severity"] == "high"
    assert scoring["retrieval"]["contamination_severity"] == "high"
    assert scoring["outcome"] == "partial_pass"
    assert scoring["pass"] is False


def test_run_golden_eval_scores_answer_observations_when_answers_are_included(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    settings.prompts_dir.mkdir(parents=True, exist_ok=True)
    settings.corpus_dir.mkdir(parents=True, exist_ok=True)
    settings.eval_dir.mkdir(parents=True, exist_ok=True)
    settings.final_prompt_template_path.write_text("prompt", encoding="utf-8")
    settings.manifest_path.write_text("{}", encoding="utf-8")
    settings.golden_eval_artifact_path.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": [
                    {
                        "query_id": "q1",
                        "prompt": "Compare Apple and Tesla risk factors",
                        "expected_tickers": ["AAPL", "TSLA"],
                        "requires_comparison": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "eliza_rag.evals.analyze_query",
        lambda prompt, filters=None, settings=None: StructuredQuery(
            raw_query=prompt,
            retrieval_text=prompt,
            lexical_query=prompt,
            dense_query=prompt,
            expansion_terms=[],
            detected_tickers=["AAPL", "TSLA"],
            detected_company_names=["Apple", "Tesla"],
            target_tickers=["AAPL", "TSLA"],
            is_multi_company=True,
            is_comparison_query=True,
            requires_entity_coverage=True,
        ),
    )
    monkeypatch.setattr(
        "eliza_rag.evals.retrieve",
        lambda *args, **kwargs: [
            RetrievalResult(
                chunk_id="AAPL::1",
                filing_id="AAPL_10K_2025",
                ticker="AAPL",
                form_type="10-K",
                filing_date="2025-01-31",
                section="Risk Factors",
                section_path="Item 1A",
                text="Apple text",
                raw_score=1.0,
                retrieval_mode="lexical",
                rank=1,
            ),
            RetrievalResult(
                chunk_id="TSLA::2",
                filing_id="TSLA_10K_2025",
                ticker="TSLA",
                form_type="10-K",
                filing_date="2025-01-30",
                section="Risk Factors",
                section_path="Item 1A",
                text="Tesla text",
                raw_score=0.9,
                retrieval_mode="lexical",
                rank=2,
            ),
        ],
    )
    monkeypatch.setattr(
        "eliza_rag.evals.generate_answer",
        lambda *args, **kwargs: AnswerResponse(
            question="Compare Apple and Tesla risk factors",
            answer="Apple highlights supply-chain risk [C1]. Tesla highlights manufacturing risk [C2].",
            summary="Apple and Tesla emphasize different operational risks.",
            findings=[
                AnswerFinding(statement="Apple cites supply-chain concentration.", citations=["C1"]),
                AnswerFinding(statement="Tesla cites manufacturing scale-up risk.", citations=["C2"]),
            ],
            uncertainty="Limited to retrieved excerpts.",
            citations=[
                AnswerCitation(
                    citation_id="C1",
                    chunk_id="AAPL::1",
                    filing_id="AAPL_10K_2025",
                    ticker="AAPL",
                    company_name="Apple Inc",
                    form_type="10-K",
                    filing_date="2025-01-31",
                    section="Risk Factors",
                    source_path="apple.txt",
                ),
                AnswerCitation(
                    citation_id="C2",
                    chunk_id="TSLA::2",
                    filing_id="TSLA_10K_2025",
                    ticker="TSLA",
                    company_name="Tesla Inc",
                    form_type="10-K",
                    filing_date="2025-01-30",
                    section="Risk Factors",
                    source_path="tesla.txt",
                ),
            ],
            retrieval_mode="targeted_hybrid",
            prompt_path="prompt.txt",
            prompt_preview="prompt",
            prompt_characters=100,
            retrieval_results=[],
            raw_model_response="{}",
            model="gpt-5-mini",
        ),
    )
    monkeypatch.setattr(
        "eliza_rag.evals.build_eval_judge_runtime",
        lambda settings: (object(), "judge prompt"),
    )
    monkeypatch.setattr(
        "eliza_rag.evals.judge_answer_quality",
        lambda settings, *, entry, client=None, prompt_template=None: {
            "evaluated": True,
            "methodology": {
                "method": "llm_judge_openrouter_quantitative",
                "judge_assisted": True,
            },
            "groundedness": {"score": 5, "score_max": 5, "status": "pass", "notes": "Grounded."},
            "citation_quality": {"score": 4, "score_max": 5, "status": "pass", "notes": "Cites both."},
            "usefulness": {"score": 4, "score_max": 5, "status": "pass", "notes": "Useful."},
            "comparison_completeness": {
                "score": 4,
                "score_max": 5,
                "status": "pass",
                "notes": "Covers both.",
            },
            "uncertainty_handling": {
                "score": 3,
                "score_max": 5,
                "status": "partial_pass",
                "notes": "Some limits stated.",
            },
            "overall": "pass",
            "overall_score": 4.2,
            "overall_score_max": 5,
            "aggregation": {"type": "weighted_average", "weights_used": {"groundedness": 0.3}},
            "notes": ["Strong answer."],
            "judge_result": {"summary": "Strong answer.", "raw_response": "{}"},
        },
    )

    payload = run_golden_eval(settings, include_answer=True)

    entry = payload["entries"][0]
    scoring = entry["scoring"]
    assert entry["answer_summary"] == "Apple and Tesla emphasize different operational risks."
    assert scoring["answer_quality"]["groundedness"]["status"] == "pass"
    assert scoring["answer_quality"]["groundedness"]["score"] == 5
    assert scoring["citation_quality"]["status"] == "pass"
    assert scoring["answer_usefulness"]["status"] == "pass"
    assert scoring["answer_quality"]["comparison_completeness"]["status"] == "pass"
    assert scoring["answer_quality"]["uncertainty_handling"]["status"] == "partial_pass"
    assert scoring["answer_quality"]["overall_score"] == 4.2
    assert scoring["answer_quality"]["overall"] == "pass"
    assert scoring["outcome"] == "pass"
