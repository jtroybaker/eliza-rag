from __future__ import annotations

import json
from pathlib import Path

import pytest

from eliza_rag.config import Settings
from eliza_rag.eval_judging import judge_eval_artifact


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


def test_judge_eval_artifact_updates_answer_quality(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.prompts_dir.mkdir(parents=True, exist_ok=True)
    settings.eval_judge_prompt_template_path.write_text("prompt {answer_output}", encoding="utf-8")
    input_path = tmp_path / "eval.json"
    input_path.write_text(
        json.dumps(
            {
                "eval_version": 3,
                "config": {"answer_judging": {"method": "heuristic_only"}},
                "entries": [
                    {
                        "query_id": "q1",
                        "prompt": "Compare Apple and Tesla risk factors",
                        "expected_tickers": ["AAPL", "TSLA"],
                        "requires_comparison": True,
                        "contamination_notes": None,
                        "retrieved_tickers": ["AAPL", "TSLA"],
                        "answer_output": "Apple [C1]. Tesla [C2].",
                        "answer_summary": "summary",
                        "answer_findings": [],
                        "answer_citations": [],
                        "answer_uncertainty": "Limited.",
                        "answer_error": None,
                        "scoring": {
                            "retrieval": {
                                "expected_ticker_coverage": True,
                                "comparison_behavior_required": True,
                                "comparison_behavior_observed": True,
                                "contamination_severity": "none",
                            },
                            "outcome": "pass",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    class _FakeClient:
        def generate(self, prompt: str) -> str:
            assert "Apple [C1]. Tesla [C2]." in prompt
            return json.dumps(
                {
                    "groundedness": {"score": 5, "rationale": "Grounded."},
                    "citation_quality": {"score": 4, "rationale": "Citations cover both."},
                    "usefulness": {"score": 3, "rationale": "Good but brief."},
                    "comparison_completeness": {"score": 4, "rationale": "Covers both."},
                    "uncertainty_handling": {"score": 5, "rationale": "States limits."},
                    "summary": "Useful but brief.",
                }
            )

    monkeypatch.setattr("eliza_rag.eval_judging.build_eval_judge_client", lambda settings: _FakeClient())

    output_path = tmp_path / "eval_judged.json"
    payload = judge_eval_artifact(settings, input_path=input_path, output_path=output_path)

    assert payload["config"]["answer_judging"]["method"] == "llm_judge_openrouter_quantitative"
    scoring = payload["entries"][0]["scoring"]
    assert scoring["answer_quality"]["overall"] == "pass"
    assert scoring["answer_quality"]["overall_score"] == 4.1
    assert scoring["answer_quality"]["groundedness"]["score"] == 5
    assert scoring["citation_quality"]["status"] == "pass"
    assert scoring["answer_usefulness"]["status"] == "partial_pass"
    assert scoring["outcome"] == "partial_pass"
    assert output_path.exists()


def test_judge_eval_artifact_accepts_prose_before_final_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    settings.prompts_dir.mkdir(parents=True, exist_ok=True)
    settings.eval_judge_prompt_template_path.write_text("prompt {answer_output}", encoding="utf-8")
    input_path = tmp_path / "eval.json"
    input_path.write_text(
        json.dumps(
            {
                "eval_version": 3,
                "config": {"answer_judging": {"method": "heuristic_only"}},
                "entries": [
                    {
                        "query_id": "q1",
                        "prompt": "Apple risk factors",
                        "expected_tickers": ["AAPL"],
                        "requires_comparison": False,
                        "contamination_notes": None,
                        "retrieved_tickers": ["AAPL"],
                        "answer_output": "Apple [C1].",
                        "answer_summary": "summary",
                        "answer_findings": [],
                        "answer_citations": [],
                        "answer_uncertainty": "Limited.",
                        "answer_error": None,
                        "scoring": {
                            "retrieval": {
                                "expected_ticker_coverage": True,
                                "comparison_behavior_required": False,
                                "comparison_behavior_observed": None,
                                "contamination_severity": "none",
                            },
                            "outcome": "pass",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    class _FakeClient:
        def generate(self, prompt: str) -> str:
            return """Analysis first.

```json
{
  "groundedness": {"score": 4, "rationale": "Grounded."},
  "citation_quality": {"score": 4, "rationale": "Cited."},
  "usefulness": {"score": 3, "rationale": "Useful enough."},
  "comparison_completeness": {"score": null, "rationale": "Not a comparison prompt."},
  "uncertainty_handling": {"score": 4, "rationale": "Handles limits."},
  "summary": "Solid single-company answer."
}
```"""

    monkeypatch.setattr("eliza_rag.eval_judging.build_eval_judge_client", lambda settings: _FakeClient())

    payload = judge_eval_artifact(settings, input_path=input_path, output_path=tmp_path / "out.json")

    assert payload["entries"][0]["scoring"]["answer_quality"]["overall"] == "partial_pass"
    assert payload["entries"][0]["scoring"]["answer_quality"]["comparison_completeness"]["status"] == "not_applicable"
