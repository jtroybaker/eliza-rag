# Phase 07A Handoff: Golden Eval Set And Build Manifest

## What Landed

- committed golden evaluation set at `eval/golden_queries.json`
- new eval runner CLI at `uv run eliza-rag-eval`
- generated build manifest at `artifacts/build_manifest.json`
- saved baseline retrieval-only eval output at `eval/baseline_targeted_hybrid_retrieval.json`
- eval usage note and exact commands at `eval/README.md`

## Implementation Summary

The Phase 07A implementation added a bounded evaluation and artifact-traceability layer without changing the public search or answer workflows.

Main additions:

- `src/eliza_rag/evals.py`
  - loads the committed golden eval set
  - emits the machine-readable build manifest
  - runs the bounded eval harness and saves structured output
- `src/eliza_rag/eval_cli.py`
  - exposes `eliza-rag-eval`
- `src/eliza_rag/config.py`
  - adds stable paths for eval and manifest artifacts
- `src/eliza_rag/dense_index_cli.py`
  - now refreshes the build manifest when the dense index is rebuilt

## Important Fix Discovered During Implementation

The first real baseline run exposed a retrieval bug:

- dense query encoding was following current settings instead of the saved dense-index metadata artifact

That mismatch breaks retrieval when the on-disk dense index contract differs from the current default embedding settings.

The fix landed in `src/eliza_rag/retrieval.py`:

- dense query encoding now follows `artifacts/dense_index_metadata.json`
- the emitted build manifest also reflects the saved dense index contract rather than only current config defaults

## Baseline Result Snapshot

Saved run:

- `uv run eliza-rag-eval --mode targeted_hybrid --rerank --reranker heuristic --output eval/baseline_targeted_hybrid_retrieval.json`

Observed results:

- Apple/Tesla/JPMorgan comparison: expected ticker coverage passed
- Apple/Tesla comparison: expected ticker coverage passed
- JPMorgan/Bank of America comparison: expected ticker coverage passed
- NVIDIA revenue-growth query: expected ticker coverage passed
- Apple single-company risk query: expected ticker coverage passed, but contamination remains visible
- sector/regulatory bank query: expected ticker coverage failed in the saved baseline

Interpretation:

- the new harness is doing the intended job of freezing both strong and weak baseline behavior before broader modularization
- the main remaining Phase 07A quality signal is not harness shape, but retrieval quality on broader sector prompts and contamination on some single-company prompts

## Validation Completed

- `uv run --extra dev pytest -q tests/test_evals.py tests/test_eval_cli.py tests/test_retrieval.py tests/test_retrieval_cli.py tests/test_answer_cli.py tests/test_storage.py tests/test_config.py`
- result: `37 passed`
- `uv run python -m compileall src/eliza_rag`

## Remaining Follow-On Work

- add richer pass/fail scoring beyond ticker-coverage placeholders
- decide whether later interface extraction should preserve the current `targeted_hybrid` baseline as the default eval mode
- use the committed baseline artifact to judge retrieval regressions during provider-interface extraction and later reranker or embedding experiments
