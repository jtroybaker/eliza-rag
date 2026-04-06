# Phase 09 Handoff: GPT-5.4 Judge Rerun And Raw-Artifact Refresh

## Outcome

This follow-up session did two distinct things:

1. refreshed the main raw answer-only comparison set so all raw `*_answer.json` artifacts now use the same inline judge contract
2. reran the separate judged overlays with GPT-5.4 over the saved answers only

That means the repo now has:

- a method-consistent raw answer-only comparison view
- a separate GPT-5.4 judged-only overlay view

## Why This Matters

Before this pass, the main raw answer-only comparison had drifted into a mixed state:

- older raw answer artifacts still reflected the earlier scoring contract
- the newer `hashed_v1 + bge-reranker-base` raw artifact already reflected the newer inline judge path

That made the main visualization hard to trust as a like-for-like comparison.

This session repaired that by rerunning the three older raw answer artifacts under the current inline answer judging path.

Separately, the user wanted to test whether a different judge would soften the judged overlay results. GPT-5.4 was tried as a drop-in replacement judge over the already-saved answers.

## Source Of Truth

Read these first:

1. `agents.md`
2. `README.md`
3. `IMPLEMENTATION_KANBAN.md`
4. `eval/README.md`
5. `PHASE_09_PART_02_ANSWER_COMPARISON_FOLLOWUP_HANDOFF.md`

Then inspect the saved artifacts in `eval/`.

## What Changed

### 1. Raw Answer-Only Comparison Set Was Refreshed

These raw answer artifacts were rerun under the same inline contract:

- `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`
- `eval/provider_hashed_v1_bge_v2_m3_answer.json`
- `eval/provider_snowflake_bge_reranker_base_answer.json`

The previously added fourth condition remained in place:

- `eval/provider_hashed_v1_bge_reranker_base_answer.json`

All four raw answer artifacts now report:

- `answer_judging.method = llm_judge_openrouter_quantitative`
- provider `openrouter`
- model `z-ai/glm-5`

### 2. GPT-5.4 Judged Overlays Were Regenerated

These overlays were rerun against the saved answer artifacts only:

- `eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json`
- `eval/provider_hashed_v1_bge_v2_m3_answer_judged.json`
- `eval/provider_hashed_v1_bge_reranker_base_answer_judged.json`
- `eval/provider_snowflake_bge_reranker_base_answer_judged.json`

Judge config used for this pass:

- provider: `openrouter`
- model: `openai/gpt-5.4`

Important working rule:

- no answers were regenerated for the GPT-5.4 overlay pass
- only the separate judged overlays were rewritten
- raw answer artifacts remained the evidence source for the main answer-only view

### 3. Read-Only Outputs Were Refreshed

Main raw answer-only outputs:

- `eval/provider_eval_report.md`
- `eval/provider_eval_visualization.png`

GPT-5.4 judged-only outputs:

- `eval/provider_eval_report_judged.md`
- `eval/provider_eval_visualization_judged.png`

## Current Raw Answer-Only State

The main answer-only comparison now covers four conditions:

1. `snowflake-arctic-embed-xs + bge-reranker-v2-m3`
2. `hashed_v1 + bge-reranker-v2-m3`
3. `snowflake-arctic-embed-xs + bge-reranker-base`
4. `hashed_v1 + bge-reranker-base`

Current raw answer-only summary from `eval/provider_eval_report.md`:

- Snowflake + `bge-reranker-v2-m3`: `0 pass / 1 partial_pass / 5 fail`
- `hashed_v1` + `bge-reranker-base`: `2 pass / 2 partial_pass / 2 fail`
- `hashed_v1` + `bge-reranker-v2-m3`: `0 pass / 3 partial_pass / 3 fail`
- Snowflake + `bge-reranker-base`: `0 pass / 1 partial_pass / 5 fail`

Interpretation:

- the main raw answer-only view is now internally method-consistent again
- `hashed_v1 + bge-reranker-base` is currently the least bad raw answer-only condition
- this does not, by itself, prove it should become a recommendation

## Current GPT-5.4 Judged-Only State

Current judged-only summary from `eval/provider_eval_report_judged.md`:

- Snowflake + `bge-reranker-v2-m3`: `0 pass / 0 partial_pass / 6 fail`
- `hashed_v1` + `bge-reranker-base`: `0 pass / 1 partial_pass / 5 fail`
- `hashed_v1` + `bge-reranker-v2-m3`: `0 pass / 0 partial_pass / 6 fail`
- Snowflake + `bge-reranker-base`: `0 pass / 0 partial_pass / 6 fail`

Interpretation:

- GPT-5.4 judged the saved answers even more harshly than the prior GLM overlay pass
- only one partial pass remained under GPT-5.4:
  - `hashed_v1 + bge-reranker-base` on the `compare_jpm_bac_risk_factors` case

## Exact Commands Used

### Refresh Raw Answer Artifacts Under Current Inline Contract

```bash
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
```

### Rerun GPT-5.4 Judged Overlays Over Saved Answers

```bash
ELIZA_RAG_JUDGE_PROVIDER=openrouter \
ELIZA_RAG_JUDGE_MODEL=openai/gpt-5.4 \
uv run eliza-rag-eval-judge \
  eval/provider_baseline_snowflake_bge_v2_m3_answer.json \
  --output eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json

ELIZA_RAG_JUDGE_PROVIDER=openrouter \
ELIZA_RAG_JUDGE_MODEL=openai/gpt-5.4 \
uv run eliza-rag-eval-judge \
  eval/provider_hashed_v1_bge_v2_m3_answer.json \
  --output eval/provider_hashed_v1_bge_v2_m3_answer_judged.json

ELIZA_RAG_JUDGE_PROVIDER=openrouter \
ELIZA_RAG_JUDGE_MODEL=openai/gpt-5.4 \
uv run eliza-rag-eval-judge \
  eval/provider_hashed_v1_bge_reranker_base_answer.json \
  --output eval/provider_hashed_v1_bge_reranker_base_answer_judged.json

ELIZA_RAG_JUDGE_PROVIDER=openrouter \
ELIZA_RAG_JUDGE_MODEL=openai/gpt-5.4 \
uv run eliza-rag-eval-judge \
  eval/provider_snowflake_bge_reranker_base_answer.json \
  --output eval/provider_snowflake_bge_reranker_base_answer_judged.json
```

### Refresh Read-Only Outputs

```bash
uv run eliza-rag-eval-report --output eval/provider_eval_report.md
uv run eliza-rag-eval-plot --output eval/provider_eval_visualization.png

uv run eliza-rag-eval-report \
  eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json \
  eval/provider_hashed_v1_bge_v2_m3_answer_judged.json \
  eval/provider_hashed_v1_bge_reranker_base_answer_judged.json \
  eval/provider_snowflake_bge_reranker_base_answer_judged.json \
  --output eval/provider_eval_report_judged.md

uv run eliza-rag-eval-plot \
  eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json \
  eval/provider_hashed_v1_bge_v2_m3_answer_judged.json \
  eval/provider_hashed_v1_bge_reranker_base_answer_judged.json \
  eval/provider_snowflake_bge_reranker_base_answer_judged.json \
  --output eval/provider_eval_visualization_judged.png
```

## Important Caveats

1. The user explicitly does not believe the answers deserve scores this low.
2. GPT-5.4 did not soften the judged-only results; it made them harsher overall.
3. The raw answer-only view and the judged-only view answer different questions:
   - raw answer-only view = current inline evidence path
   - judged-only view = overlay interpretation over saved answers with a chosen external judge model
4. The next useful step is probably not another visualization refresh.

The more useful next step is to separate failures into:

- retrieval miss
- answer construction/parsing miss
- judge/rubric harshness or mismatch

## Recommended Next Step

Run a per-query failure review over the four raw answer artifacts and the four GPT-5.4 judged overlays.

The goal should be to determine whether the current low scores are primarily caused by:

1. retrieval coverage failures
2. answer synthesis failures
3. parser / answer-shape failures
4. overly strict or misaligned judging behavior

Do not change the recommendation solely from the current judged summary counts without that failure decomposition.
