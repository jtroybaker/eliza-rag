# Phase 09 Part 02 Handoff: Answer-Included Comparison Follow-Up

## Outcome

This session part should be treated as the next bounded implementation slice after the Phase 09 congruence cleanup.

The goal is to extend the saved evidence base from:

- one answer-included baseline artifact

to:

- one answer-included baseline artifact
- one answer-included alternate-embedder artifact
- one answer-included alternate-reranker artifact

Optionally, this part may also add separate judged overlays for the newly saved answer artifacts.

## Why This Part Exists

Phase 08 already saved the bounded retrieval-only provider comparison set:

- `eval/provider_baseline_snowflake_bge_v2_m3.json`
- `eval/provider_hashed_v1_bge_v2_m3.json`
- `eval/provider_snowflake_bge_reranker_base.json`

Phase 09 added only one raw answer-included artifact:

- `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`

That means the repo can now discuss answer behavior on the current recommended path, but it still cannot compare answer behavior across the already-defined provider axes with the same clarity as the retrieval-only evidence layer.

This part should close that gap without reopening broader provider exploration.

## Source Of Truth For This Part

Read these first:

1. `agents.md`
2. `IMPLEMENTATION_KANBAN.md`
3. `README.md`
4. `eval/README.md`
5. `PHASE_08_PROVIDER_EVALUATION_AND_SCORING_HANDOFF.md`
6. `PHASE_09_SESSION_HANDOFF.md`
7. `PHASE_09_ANSWER_EVAL_AND_VISUALIZATION_HANDOFF.md`

Then work from the existing saved artifact set in `eval/`.

## Required Outcome

At the end of this part, the repo should have answer-included coverage for the same bounded comparison axes already used in the saved Phase 08 retrieval evidence:

1. baseline:
   - Snowflake + `bge-reranker-v2-m3`
2. alternate embedder:
   - `hashed_v1` + `bge-reranker-v2-m3`
3. alternate reranker:
   - Snowflake + `bge-reranker-base`

Minimum required new raw artifacts:

- `eval/provider_hashed_v1_bge_v2_m3_answer.json`
- `eval/provider_snowflake_bge_reranker_base_answer.json`

Minimum required new manifest artifacts:

- `artifacts/build_manifest.provider_hashed_v1_bge_v2_m3_answer.json`
- `artifacts/build_manifest.provider_snowflake_bge_reranker_base_answer.json`

Optional judged overlays:

- `eval/provider_hashed_v1_bge_v2_m3_answer_judged.json`
- `eval/provider_snowflake_bge_reranker_base_answer_judged.json`

## Scope

Keep this part tightly scoped to:

1. answer-included eval runs for the two existing alternate comparison axes
2. optional judged overlays for those new answer artifacts
3. regeneration of read-only report and plot outputs after the artifact set expands
4. bounded doc updates that record the newly saved artifacts and commands

Do not broaden into:

- a new `bge-m3` experiment
- release archive refresh work
- a new judge rubric or broad prompt redesign
- a new analytics backend
- Phase 10 planning beyond a brief note of what remains next

## Concrete Tasks

### 1. Save The Alternate-Embedder Answer-Included Artifact

Use the current committed local dense artifact contract for the `hashed_v1` comparison path.

Suggested command:

```bash
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
```

Expected interpretation:

- this is the answer-included counterpart to `eval/provider_hashed_v1_bge_v2_m3.json`
- it should be treated as the alternate-embedder answer run, not as a new baseline recommendation

### 2. Save The Alternate-Reranker Answer-Included Artifact

Use the saved Snowflake eval dense table and metadata artifact, matching the original Phase 08 alternate-reranker comparison axis.

Suggested command:

```bash
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

Expected interpretation:

- this is the answer-included counterpart to `eval/provider_snowflake_bge_reranker_base.json`
- it should test answer behavior under the already-bounded reranker comparison axis, not reopen reranker selection generally

### 3. Optionally Generate Separate Judged Overlays

If runtime cost is acceptable and the raw answer artifacts were saved successfully, generate separate judged overlays for the new answer artifacts.

Suggested commands:

```bash
uv run eliza-rag-eval-judge \
  eval/provider_hashed_v1_bge_v2_m3_answer.json \
  --output eval/provider_hashed_v1_bge_v2_m3_answer_judged.json

uv run eliza-rag-eval-judge \
  eval/provider_snowflake_bge_reranker_base_answer.json \
  --output eval/provider_snowflake_bge_reranker_base_answer_judged.json
```

Working rule:

- raw answer-included artifacts remain the evidence source
- judged artifacts remain overlays for interpretation
- do not overwrite the raw answer artifacts

### 4. Regenerate Read-Only Outputs From The Expanded Artifact Set

After the raw answer artifacts are saved, regenerate:

```bash
uv run eliza-rag-eval-report --output eval/provider_eval_report.md
uv run eliza-rag-eval-plot --output eval/provider_eval_visualization.png
```

If the judged overlays are also generated, confirm that report and plot outputs remain interpretable and do not blur raw and judged artifacts into one ambiguous run story.

### 5. Update Docs With Exact Saved Outputs

At minimum, update:

- `IMPLEMENTATION_KANBAN.md`
- `README.md`
- `eval/README.md`

Update `LIMITATIONS.md` only if the expanded answer runs expose a new caveat that is not already documented.

## Acceptance Criteria

This part is done when:

- the repo has answer-included raw artifacts for:
  - baseline Snowflake + `bge-reranker-v2-m3`
  - alternate `hashed_v1` + `bge-reranker-v2-m3`
  - alternate Snowflake + `bge-reranker-base`
- each new raw artifact has its own manifest linkage
- any judged overlays are saved as separate `_judged.json` outputs
- regenerated report and plot outputs still operate only on saved eval JSON artifacts
- the docs record exact filenames and commands for the new saved artifacts

## Validation

Suggested validation slice:

```bash
uv run pytest -q tests/test_evals.py tests/test_eval_cli.py tests/test_eval_reporting.py tests/test_eval_report_cli.py tests/test_eval_judging.py
uv run python -m compileall src/eliza_rag
uv run eliza-rag-eval-report --output /tmp/provider_eval_report_check.md
uv run eliza-rag-eval-plot --output /tmp/provider_eval_visualization_check.png
```

If judged overlays are produced, also validate that `uv run eliza-rag-eval-judge --help` still matches the documented workflow.

## Risks To Watch

- treating judged overlays as stronger evidence than the corresponding raw answer artifacts
- over-claiming provider differences from a very small answer-included sample
- accidentally mixing the Snowflake eval dense table with the default committed `hashed_v1` artifact contract
- making the regenerated report harder to read if raw and judged answer artifacts appear as near-duplicate runs
- letting this bounded follow-up turn into a broader provider-expansion session

## Recommended Next Step After This Part

After this follow-up lands, the repo should be in a much better position to decide whether any additional Phase 09 cleanup is needed around report labeling and judged-overlay presentation, or whether it is ready for a Phase 10 kickoff focused on the next real uncertainty rather than missing answer-comparison evidence.
