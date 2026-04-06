# Phase 09 Instructions: Gemini Judge Rerun Without Regenerating Answers

## Purpose

These instructions rerun the judged overlay artifacts with:

- provider: `openrouter`
- model: `google/gemini-2.5-flash-lite`

This pass does **not** regenerate answers.

It only re-judges the existing saved raw answer artifacts and refreshes the judged-only report outputs.

## Important Working Rule

Do not run `uv run eliza-rag-eval --include-answer` during this pass.

That would regenerate answers and would change the raw evidence layer.

For this rerun, the raw `*_answer.json` artifacts remain the evidence source and only the `*_answer_judged.json` overlays are rewritten.

## Inputs

Existing raw answer artifacts:

- `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`
- `eval/provider_hashed_v1_bge_v2_m3_answer.json`
- `eval/provider_hashed_v1_bge_reranker_base_answer.json`
- `eval/provider_snowflake_bge_reranker_base_answer.json`

## Environment

Set the judge override explicitly:

```bash
export OPENROUTER_API_KEY=your_key_here
export ELIZA_RAG_JUDGE_PROVIDER=openrouter
export ELIZA_RAG_JUDGE_MODEL=google/gemini-2.5-flash-lite
```

## Step 1: Rerun Judged Overlays Only

```bash
uv run eliza-rag-eval-judge \
  eval/provider_baseline_snowflake_bge_v2_m3_answer.json \
  --output eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json

uv run eliza-rag-eval-judge \
  eval/provider_hashed_v1_bge_v2_m3_answer.json \
  --output eval/provider_hashed_v1_bge_v2_m3_answer_judged.json

uv run eliza-rag-eval-judge \
  eval/provider_hashed_v1_bge_reranker_base_answer.json \
  --output eval/provider_hashed_v1_bge_reranker_base_answer_judged.json

uv run eliza-rag-eval-judge \
  eval/provider_snowflake_bge_reranker_base_answer.json \
  --output eval/provider_snowflake_bge_reranker_base_answer_judged.json
```

## Step 2: Refresh Judged-Only Report Outputs

```bash
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

## Expected Result

After this pass:

- the raw answer artifacts remain unchanged
- the judged overlay artifacts reflect `google/gemini-2.5-flash-lite`
- `eval/provider_eval_report_judged.md` reflects the Gemini judged-only view
- `eval/provider_eval_visualization_judged.png` reflects the Gemini judged-only view

## Interpretation Rule

If Gemini is more lenient or harsher than the previous judge, that does **not** mean the answers changed.

It only means the overlay interpretation changed.

The raw `*_answer.json` artifacts remain the primary evidence source.
