# Phase 08 Handoff: Provider Evaluation Evidence And Scoring Hardening

## Outcome

Phase 08 is partially complete.

This pass did complete the two most important bounded goals:

- convert the eval runner from placeholder scoring into a saved retrieval-quality contract
- save one-variable-at-a-time provider comparison artifacts that are strong enough to support the next discussion cleanly

This pass did not complete every possible provider experiment. In particular, the `bge-m3` embedder was left wired but was not retained in the saved evidence set because the local rebuild cost was too high for this bounded slice.

## What Landed

- stronger eval scoring in `src/eliza_rag/evals.py`
  - explicit `pass`, `partial_pass`, and `fail`
  - contamination observations recorded directly in saved artifacts
  - conditional citation-quality and answer-usefulness scoring fields for answer-included runs
  - per-run summary counts
- manifest linkage fix in the eval CLI flow
  - `--manifest-output` now propagates into the saved eval payload instead of silently pointing back to the default manifest path
- batched external embedding generation in `src/eliza_rag/embeddings.py`
  - added to make non-hashed rebuilds more tractable locally
- saved Phase 08 provider comparison artifacts:
  - `eval/provider_baseline_snowflake_bge_v2_m3.json`
  - `eval/provider_hashed_v1_bge_v2_m3.json`
  - `eval/provider_snowflake_bge_reranker_base.json`
- per-run manifest artifacts:
  - `artifacts/build_manifest.provider_baseline_snowflake_bge_v2_m3.json`
  - `artifacts/build_manifest.provider_hashed_v1_bge_v2_m3.json`
  - `artifacts/build_manifest.provider_snowflake_bge_reranker_base.json`

## What Was Measured

Saved baseline provider run:

```bash
ELIZA_RAG_DENSE_LANCEDB_TABLE=filing_chunks_dense_snowflake_eval \
ELIZA_RAG_DENSE_INDEX_ARTIFACT_NAME=dense_index_metadata.snowflake_eval.json \
uv run eliza-rag-eval \
  --mode targeted_hybrid \
  --rerank \
  --reranker bge-reranker-v2-m3 \
  --manifest-output artifacts/build_manifest.provider_baseline_snowflake_bge_v2_m3.json \
  --output eval/provider_baseline_snowflake_bge_v2_m3.json
```

Saved alternate-embedder comparison actually used in this phase:

```bash
ELIZA_RAG_DENSE_LANCEDB_TABLE=filing_chunks_dense \
ELIZA_RAG_DENSE_INDEX_ARTIFACT_NAME=dense_index_metadata.json \
uv run eliza-rag-eval \
  --mode targeted_hybrid \
  --rerank \
  --reranker bge-reranker-v2-m3 \
  --manifest-output artifacts/build_manifest.provider_hashed_v1_bge_v2_m3.json \
  --output eval/provider_hashed_v1_bge_v2_m3.json
```

Saved alternate-reranker comparison:

```bash
ELIZA_RAG_DENSE_LANCEDB_TABLE=filing_chunks_dense_snowflake_eval \
ELIZA_RAG_DENSE_INDEX_ARTIFACT_NAME=dense_index_metadata.snowflake_eval.json \
uv run eliza-rag-eval \
  --mode targeted_hybrid \
  --rerank \
  --reranker bge-reranker-base \
  --manifest-output artifacts/build_manifest.provider_snowflake_bge_reranker_base.json \
  --output eval/provider_snowflake_bge_reranker_base.json
```

Snowflake dense build used for the saved baseline and alternate-reranker runs:

```bash
uv run eliza-rag-build-dense-index \
  --embedder snowflake-arctic-embed-xs \
  --dense-table-name filing_chunks_dense_snowflake_eval \
  --metadata-artifact-name dense_index_metadata.snowflake_eval.json
```

## What Changed In The Scoring Contract

Old state:

- expected ticker coverage existed
- comparison placeholder fields existed
- `pass` was unset
- contamination, citation quality, and answer usefulness were not turned into stable saved judgments

Current state:

- retrieval-only runs now receive stable `pass`, `partial_pass`, or `fail`
- contamination is explicitly recorded in:
  - `contamination_observed`
  - `contamination_tickers`
  - `contamination_severity`
- answer-level scoring fields now exist:
  - `citation_quality`
  - `answer_usefulness`
- those answer-level fields remain `not_evaluated` in the saved provider artifacts from this phase because the bounded provider slice was run without `--include-answer`

Interpretation:

- the repo now has a retrieval-quality eval contract that is materially stronger than the old placeholder contract
- the repo still does not have a full answer-quality gate

## Saved Evidence Summary

### Snowflake embedder + `bge-reranker-v2-m3`

Artifact:

- `eval/provider_baseline_snowflake_bge_v2_m3.json`

Observed summary:

- `4 pass`
- `1 partial_pass`
- `1 fail`

Interpretation:

- this is the strongest saved provider artifact in the current Phase 08 slice
- the main remaining weaknesses are still Apple single-company contamination and the broader bank-sector prompt

### `hashed_v1` embedder + `bge-reranker-v2-m3`

Artifact:

- `eval/provider_hashed_v1_bge_v2_m3.json`

Observed summary:

- `3 pass`
- `3 partial_pass`
- `0 fail`

Interpretation:

- `hashed_v1` avoided the outright fail on the broad bank-sector prompt
- it did so with materially more contamination on multiple prompts
- the overall profile is weaker and less clean than Snowflake on this bounded slice

### Snowflake embedder + `bge-reranker-base`

Artifact:

- `eval/provider_snowflake_bge_reranker_base.json`

Observed summary:

- `4 pass`
- `1 partial_pass`
- `1 fail`

Interpretation:

- this did not show a meaningful win over `bge-reranker-v2-m3` on the committed golden slice
- the saved evidence does not justify changing the current reranker recommendation

## What Was Attempted But Not Kept

The repo still wires `bge-m3` as an alternate embedder.

What happened in this phase:

- a `bge-m3` dense rebuild was attempted
- the local rebuild cost was too high for this bounded slice
- the run was abandoned before completion
- no `bge-m3` dense table or metadata artifact remains in the repo state

Interpretation:

- `bge-m3` remains a possible later experiment surface
- it is not part of the saved Phase 08 evidence set and should not be cited as measured evidence

## Artifact Hygiene Notes

This repo now has three different artifact categories that should stay distinct:

1. committed small evidence artifacts
   - `eval/*.json`
   - selected manifest JSON files when useful for provenance
2. reviewer-facing release artifacts
   - GitHub Release ZIP archives containing the sanctioned retrieval state
3. disposable local experiment state
   - local LanceDB tables
   - temporary inspection directories
   - abandoned rebuild outputs

Working rule:

- GitHub Release archives should remain the reviewer-facing source of large retrieval state
- local experiment tables should not become the default reviewer truth just because they exist on disk
- saved `eval/*.json` artifacts are the correct source for later visualizations or judge-driven dashboards

## Dense Artifact Baseline Decision

Current decision after this pass:

- do not refresh the committed local dense artifact baseline yet
- keep the committed local artifact snapshot at `hashed_v1` for now

Reason:

- Snowflake evidence is stronger than `hashed_v1` on the bounded slice
- but the reviewer-facing release artifact path has not yet been republished around a Snowflake-based baseline
- changing the committed local baseline without updating the release artifact story would blur the repo’s source-of-truth story again

## Recommended Next Work

1. keep the saved provider artifacts as the retrieval-quality baseline for later comparison
2. add answer-included runs or a judge-based scoring layer before making stronger answer-quality claims
3. if using a judge model, keep it bounded and structured
   - groundedness
   - citation quality
   - usefulness
   - comparison completeness
   - contamination penalty
   - final grade
4. if a visualization is added, build it directly from the saved `eval/*.json` artifacts
5. if a later publish step moves the release archive to Snowflake, update the release artifact and docs together rather than only the local metadata snapshot

## Validation Completed

Commands run successfully during this pass:

```bash
uv run pytest -q tests/test_embeddings.py tests/test_evals.py tests/test_eval_cli.py
uv run python -m compileall src/eliza_rag
```

Observed result:

- focused test slice passed
- compileall passed

## Most Important Truths For The Next Session Manager

- the repo now has saved provider evidence, not just provider wiring
- the saved evidence currently favors Snowflake over `hashed_v1`
- the saved evidence does not currently justify switching from `bge-reranker-v2-m3` to `bge-reranker-base`
- the eval scoring contract is now strong enough to support bounded retrieval-quality decisions
- the eval scoring contract is not yet a complete answer-quality gate
- the next meaningful step is likely judge-based answer evaluation or a small visualization layer over the saved artifacts, not another open-ended provider-rebuild session
