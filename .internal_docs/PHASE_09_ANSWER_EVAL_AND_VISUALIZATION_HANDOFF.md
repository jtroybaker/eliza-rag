# Phase 09 Handoff: Answer-Level Evaluation And Artifact-Driven Visualization

## Outcome

Phase 09 is complete in bounded form.

This pass added:

- a real raw answer-included eval artifact for the current recommended provider path
- a structured built-in answer-level judging layer on that raw artifact
- a separate judge-assisted overlay path that writes a new artifact
- read-only markdown reporting over saved eval artifacts
- read-only plot generation over saved eval artifacts

Comparison scope preserved from the saved evidence layer:

- embedder comparison in saved artifacts:
  - `snowflake-arctic-embed-xs` vs `hashed_v1`
  - fixed reranker: `bge-reranker-v2-m3`
- reranker comparison in saved artifacts:
  - `bge-reranker-v2-m3` vs `bge-reranker-base`
  - fixed embedder: `snowflake-arctic-embed-xs`
- no saved `bge-m3` embedder result exists in the committed evidence set

## What Was Measured Directly

Saved raw answer-included baseline run:

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
```

Saved raw evidence artifacts:

- `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`
- `artifacts/build_manifest.provider_baseline_snowflake_bge_v2_m3_answer.json`

Run metadata preserved in the raw artifact:

- exact command used
- output artifact path
- manifest output path

Observed summary in the raw artifact:

- `3 pass`
- `2 partial_pass`
- `1 fail`

The raw answer artifact remains the evidence source for the measured run.

## What Was Heuristic-Scored In The Raw Artifact

The raw answer-included eval artifact now separates retrieval scoring from answer scoring.

The built-in answer scoring inside that raw artifact is currently:

- `heuristic_only`
- rubric saved at `eval/answer_judging_rubric.md`
- explicit answer-quality dimensions:
  - groundedness
  - citation quality
  - usefulness
  - comparison completeness
  - uncertainty handling

Important observed behavior from the raw artifact:

- the Apple/Tesla/JPMorgan comparison remained a retrieval pass but downgraded to answer `partial_pass` because the cited answer coverage dropped one expected ticker
- the single-company Apple prompt stayed retrieval `partial_pass`, but the answer-level layer still judged the answer itself usable and grounded
- the broader bank-sector prompt remained the main failure cluster and also produced an answer-format error under the strict single-call contract

## What Was Judge-Assisted Later

The repo also supports a separate judge-assisted pass over saved answer artifacts.

Judge-assisted command surface:

```bash
uv run eliza-rag-eval-judge \
  eval/provider_baseline_snowflake_bge_v2_m3_answer.json \
  --output eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json
```

Saved judged overlay artifact:

- `eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json`

Important artifact-story rule:

- the judge-assisted pass writes a new artifact
- it does not mutate the raw answer-included evidence artifact
- the judged artifact should be treated as an overlay for interpretation, not as the source of truth

## What Was Visualized

The repo now has both read-only visualization paths over saved eval artifacts.

Markdown report path:

```bash
uv run eliza-rag-eval-report --output eval/provider_eval_report.md
```

Generated artifact:

- `eval/provider_eval_report.md`

Plot path:

```bash
uv run eliza-rag-eval-plot --output eval/provider_eval_visualization.png
```

Default output path:

- `eval/provider_eval_visualization.png`

The plot CLI is available and can generate that artifact from saved eval JSON when needed.

Both paths read saved `eval/*.json` artifacts only. They are views over the evidence base, not replacements for it.

## What Remains Provisional

- the built-in answer judging in the raw artifact is still `heuristic_only` and should not be treated as equivalent to human review
- the judge-assisted overlay is also an interpretation layer, not a replacement for the raw artifact
- only one answer-included provider artifact was saved in this bounded phase
- the repo still does not justify a provider recommendation change from answer judging alone
- the reviewer-facing release artifact baseline still remains separate from local experiment manifests and eval outputs

## Validation Target For This Handoff

The relevant exposed scripts to keep in sync with these docs are:

- `uv run eliza-rag-eval`
- `uv run eliza-rag-eval-report`
- `uv run eliza-rag-eval-plot`
- `uv run eliza-rag-eval-judge`

Suggested bounded validation slice:

```bash
uv run pytest -q tests/test_eval_reporting.py tests/test_eval_report_cli.py tests/test_eval_judging.py
uv run eliza-rag-eval-report --output /tmp/provider_eval_report_check.md
uv run eliza-rag-eval-plot --output /tmp/provider_eval_visualization_check.png
```

## Most Important Truths For The Next Session

- the repo now has one real raw answer-included artifact on the current recommended Snowflake + `bge-reranker-v2-m3` path
- retrieval wins and answer wins are now distinguishable in the saved artifact format
- the current built-in answer-judging method in that raw artifact is intentionally `heuristic_only`
- the repo also supports a separate judge-assisted overlay artifact path
- the generated report and plot are useful, but the raw JSON artifacts remain the evidence source
