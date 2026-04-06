# Eval Artifacts

## Reviewer Discussion Path

If you only need the final demo discussion surface, start here:

- raw answer artifacts: `eval/*_answer.json`
- judged overlays: `eval/*_answer_judged.json`
- judged report: `eval/provider_eval_report_judged.md`
- judged visualization: `eval/provider_eval_visualization_judged.png`

Important interpretation rule:

- raw saved artifacts are the evidence base
- judged overlays are an interpretation layer over those artifacts
- reports and visualizations are read-only views, not replacement truth

The judged visualization is the easiest live discussion artifact, but it should not be presented as stronger evidence than the raw saved answer artifacts underneath it.

Golden eval set:

- `eval/golden_queries.json`

Build manifest output:

- `artifacts/build_manifest.json`

Baseline retrieval-only eval output:

- `eval/baseline_targeted_hybrid_retrieval.json`
- this saved baseline reflects the current committed local dense artifact contract, which still points at `hashed_v1`

Phase 08 provider comparison outputs:

- `eval/provider_baseline_snowflake_bge_v2_m3.json`
- `eval/provider_hashed_v1_bge_v2_m3.json`
- `eval/provider_snowflake_bge_reranker_base.json`

Comparison axes:

- embedder comparison actually saved:
  - `provider_baseline_snowflake_bge_v2_m3.json` = `snowflake-arctic-embed-xs` + `bge-reranker-v2-m3`
  - `provider_hashed_v1_bge_v2_m3.json` = `hashed_v1` + `bge-reranker-v2-m3`
- reranker comparison actually saved:
  - `provider_baseline_snowflake_bge_v2_m3.json` = `snowflake-arctic-embed-xs` + `bge-reranker-v2-m3`
  - `provider_snowflake_bge_reranker_base.json` = `snowflake-arctic-embed-xs` + `bge-reranker-base`
- not represented in saved evidence:
  - `bge-m3` embedder

Phase 09 answer-included output:

- `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`
- `eval/provider_hashed_v1_bge_v2_m3_answer.json`
- `eval/provider_hashed_v1_bge_reranker_base_answer.json`
- `eval/provider_snowflake_bge_reranker_base_answer.json`
- saved with local Ollama answer generation on the Snowflake + `bge-reranker-v2-m3` baseline retrieval path

Phase 09 answer-judging rubric:

- `eval/answer_judging_rubric.md`

Judge architecture:

- judge CLI: `uv run eliza-rag-eval-judge`
- default judge provider: `openrouter`
- default judge model in the current environment: `z-ai/glm-5`
- the judge runs over saved answer-included eval artifacts and writes a new judged artifact
- each judged artifact now records:
  - per-dimension `0-5` scores
  - weighted aggregate `overall_score`
  - derived categorical status from the quantitative scorecard

Phase 09 generated report:

- `eval/provider_eval_report.md`
- `eval/provider_eval_report_judged.md`
- `eval/provider_eval_visualization.png`
- `eval/provider_eval_visualization_judged.png`

Phase 08 comparison manifest outputs:

- `artifacts/build_manifest.provider_baseline_snowflake_bge_v2_m3.json`
- `artifacts/build_manifest.provider_hashed_v1_bge_v2_m3.json`
- `artifacts/build_manifest.provider_snowflake_bge_reranker_base.json`

Phase 09 answer-included manifest output:

- `artifacts/build_manifest.provider_baseline_snowflake_bge_v2_m3_answer.json`
- `artifacts/build_manifest.provider_hashed_v1_bge_v2_m3_answer.json`
- `artifacts/build_manifest.provider_hashed_v1_bge_reranker_base_answer.json`
- `artifacts/build_manifest.provider_snowflake_bge_reranker_base_answer.json`

Exact commands:

```bash
uv run eliza-rag-build-dense-index
uv run eliza-rag-eval --mode targeted_hybrid --rerank --reranker heuristic --output eval/baseline_targeted_hybrid_retrieval.json
ELIZA_RAG_LLM_PROVIDER=local_ollama \
ELIZA_RAG_DENSE_LANCEDB_TABLE=filing_chunks_dense_snowflake_eval \
ELIZA_RAG_DENSE_INDEX_ARTIFACT_NAME=dense_index_metadata.snowflake_eval.json \
uv run eliza-rag-eval \
  --mode targeted_hybrid \
  --rerank \
  --reranker bge-reranker-v2-m3 \
  --include-answer \
  --manifest-output artifacts/build_manifest.provider_baseline_snowflake_bge_v2_m3_answer.json \
  --output eval/provider_baseline_snowflake_bge_v2_m3_answer.json
ELIZA_RAG_LLM_PROVIDER=local_ollama \
ELIZA_RAG_DENSE_LANCEDB_TABLE=filing_chunks_dense \
ELIZA_RAG_DENSE_INDEX_ARTIFACT_NAME=dense_index_metadata.json \
uv run eliza-rag-eval \
  --mode targeted_hybrid \
  --rerank \
  --reranker bge-reranker-base \
  --include-answer \
  --manifest-output artifacts/build_manifest.provider_hashed_v1_bge_reranker_base_answer.json \
  --output eval/provider_hashed_v1_bge_reranker_base_answer.json
ELIZA_RAG_LLM_PROVIDER=local_ollama \
ELIZA_RAG_DENSE_LANCEDB_TABLE=filing_chunks_dense \
ELIZA_RAG_DENSE_INDEX_ARTIFACT_NAME=dense_index_metadata.json \
uv run eliza-rag-eval \
  --mode targeted_hybrid \
  --rerank \
  --reranker bge-reranker-v2-m3 \
  --include-answer \
  --manifest-output artifacts/build_manifest.provider_hashed_v1_bge_v2_m3_answer.json \
  --output eval/provider_hashed_v1_bge_v2_m3_answer.json
ELIZA_RAG_LLM_PROVIDER=local_ollama \
ELIZA_RAG_DENSE_LANCEDB_TABLE=filing_chunks_dense_snowflake_eval \
ELIZA_RAG_DENSE_INDEX_ARTIFACT_NAME=dense_index_metadata.snowflake_eval.json \
uv run eliza-rag-eval \
  --mode targeted_hybrid \
  --rerank \
  --reranker bge-reranker-base \
  --include-answer \
  --manifest-output artifacts/build_manifest.provider_snowflake_bge_reranker_base_answer.json \
  --output eval/provider_snowflake_bge_reranker_base_answer.json
uv run eliza-rag-eval-report --output eval/provider_eval_report.md
OPENROUTER_API_KEY=your_key_here \
ELIZA_RAG_JUDGE_PROVIDER=openrouter \
ELIZA_RAG_JUDGE_MODEL=z-ai/glm-5 \
uv run eliza-rag-eval-judge \
  eval/provider_baseline_snowflake_bge_v2_m3_answer.json \
  --output eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json
OPENROUTER_API_KEY=your_key_here \
ELIZA_RAG_JUDGE_PROVIDER=openrouter \
ELIZA_RAG_JUDGE_MODEL=z-ai/glm-5 \
uv run eliza-rag-eval-judge \
  eval/provider_hashed_v1_bge_v2_m3_answer.json \
  --output eval/provider_hashed_v1_bge_v2_m3_answer_judged.json
OPENROUTER_API_KEY=your_key_here \
ELIZA_RAG_JUDGE_PROVIDER=openrouter \
ELIZA_RAG_JUDGE_MODEL=z-ai/glm-5 \
uv run eliza-rag-eval-judge \
  eval/provider_hashed_v1_bge_reranker_base_answer.json \
  --output eval/provider_hashed_v1_bge_reranker_base_answer_judged.json
OPENROUTER_API_KEY=your_key_here \
ELIZA_RAG_JUDGE_PROVIDER=openrouter \
ELIZA_RAG_JUDGE_MODEL=z-ai/glm-5 \
uv run eliza-rag-eval-judge \
  eval/provider_snowflake_bge_reranker_base_answer.json \
  --output eval/provider_snowflake_bge_reranker_base_answer_judged.json
uv run eliza-rag-eval-report \
  eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json \
  eval/provider_hashed_v1_bge_reranker_base_answer_judged.json \
  eval/provider_hashed_v1_bge_v2_m3_answer_judged.json \
  eval/provider_snowflake_bge_reranker_base_answer_judged.json \
  --output eval/provider_eval_report_judged.md
```

Scoring status:

- the current runner now saves explicit `pass`, `partial_pass`, and `fail` outcomes
- contamination observations are part of the saved scoring payload
- retrieval-level and answer-level scoring are now separated explicitly in the artifact shape
- answer-level judging now records:
  - groundedness
  - citation quality
  - usefulness
  - comparison completeness
  - uncertainty handling
- the current judged answer-level method is `llm_judge_openrouter_quantitative`
- the judged answer overlays currently report:
  - baseline Snowflake + `bge-reranker-v2-m3`: `1 pass / 2 partial_pass / 3 fail`
  - `hashed_v1` + `bge-reranker-base`: `0 pass / 4 partial_pass / 2 fail`
  - `hashed_v1` + `bge-reranker-v2-m3`: `0 pass / 2 partial_pass / 4 fail`
  - Snowflake + `bge-reranker-base`: `0 pass / 2 partial_pass / 4 fail`
- the main answer-only raw comparison now also includes the combined-condition expansion:
  - `hashed_v1` + `bge-reranker-base`: `2 pass / 2 partial_pass / 2 fail`

Judge status:

- the repo now also supports a judge-assisted artifact pass over saved answers
- judge-assisted runs should be saved as separate artifacts rather than mutating the original answer-included evidence file

Reporting status:

- `uv run eliza-rag-eval-report` reads saved `eval/*.json` artifacts only
- default artifact discovery skips `*_judged.json` overlays so raw and judged evidence stay separate unless you pass explicit paths
- the generated report is a read-only view and is not a replacement for the saved raw evidence
