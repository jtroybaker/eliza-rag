# Phase 07 Cleanup Kickoff: Congruence, Artifact Consistency, And Interface Hygiene

## Purpose

This cleanup pass is for finishing the remaining Phase 07 congruence work after the main worker tracks landed.

The goal is not to broaden the architecture further. The goal is to make the Phase 07 outputs internally consistent across:

- public CLI surfaces
- saved evaluation artifacts
- current repo documentation
- interface claims in the handoff docs

## Why This Cleanup Exists

The Phase 07 work is directionally correct and largely complete, but review found three cleanup items that should be resolved before treating the phase as fully coherent:

1. the eval CLI does not yet expose the alternate reranker that Phase 07C says is ready for comparison
2. the saved dense metadata and build manifest still describe a `hashed_v1` dense index, which conflicts with repo-level documentation that describes the Snowflake path as the default dense workflow
3. answer-backend extraction claims are slightly ahead of the code because a local backend protocol still exists beside the shared interface

This cleanup worker should resolve those mismatches without reopening broad refactor work.

## Read First

Before changing code, read:

- `agents.md`
- `README.md`
- `DECISIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `PHASE_07A_GOLDEN_EVAL_AND_MANIFEST_HANDOFF.md`
- `PHASE_07B_INTERFACE_EXTRACTION_HANDOFF.md`
- `PHASE_07C_PROVIDER_EXPERIMENT_PREP_HANDOFF.md`

Inspect these implementation files specifically:

- `src/eliza_rag/eval_cli.py`
- `src/eliza_rag/evals.py`
- `src/eliza_rag/retrieval.py`
- `src/eliza_rag/answer_generation.py`
- `artifacts/build_manifest.json`
- `artifacts/dense_index_metadata.json`
- `eval/baseline_targeted_hybrid_retrieval.json`

## Scope

Keep this cleanup tightly scoped to:

1. public-surface congruence
2. artifact-state consistency
3. interface-hygiene cleanup
4. documentation and handoff corrections required by those changes

Do not broaden into:

- new provider experiments
- new retrieval modes
- new answer backends
- broader architecture movement beyond what is needed to remove the inconsistency

## Required Cleanup Items

### 1. Eval CLI Must Support The Alternate Reranker If The Repo Claims It Does

Problem:

- `eliza-rag-eval` currently accepts `bge-reranker-v2-m3` and `heuristic`, but not `bge-reranker-base`
- Phase 07C documentation says alternate reranker comparison is now wired and ready for bounded evaluation

Required work:

- extend `eliza-rag-eval` so its reranker selection surface matches the retrieval and answer CLIs
- add or update tests for the eval CLI reranker option
- update any docs or examples that describe the eval path

Definition of done:

- `uv run eliza-rag-eval --rerank --reranker bge-reranker-base ...` is valid
- targeted tests cover the new selection surface

### 2. Dense Artifact State Must Match The Repo Story

Problem:

- the repo docs and decisions describe Snowflake as the default dense path
- the currently saved dense metadata and build manifest still identify the baseline as `hashed_v1`

Required work:

- determine whether the intended local baseline artifact should still be `hashed_v1` or should now be rebuilt with Snowflake
- make the following agree:
  - `artifacts/dense_index_metadata.json`
  - `artifacts/build_manifest.json`
  - `eval/baseline_targeted_hybrid_retrieval.json`
  - repo docs and decision records
- if rebuild is not feasible in this cleanup pass, document clearly that config defaults and current local artifacts differ

Preferred resolution:

- if practical, rebuild the baseline dense artifacts so the saved artifact state matches the stated default path
- if not practical, tighten the docs so they distinguish:
  - code/config default
  - currently saved local artifact baseline

Definition of done:

- artifact files and documentation no longer contradict each other about the current dense baseline

### 3. Answer Backend Interface Story Must Be Clean

Problem:

- the Phase 07B handoff says answer backends were moved to the shared interface
- the code still keeps a local backend protocol beside the shared interface import

Required work:

- either remove the duplicate local protocol and use the shared `AnswerBackend` interface consistently
- or narrow the docs and handoff language so they state the extraction is partial

Preferred resolution:

- remove the duplicate local protocol unless doing so causes avoidable churn

Definition of done:

- the code and docs tell one consistent story about the answer-backend contract

## Required Documentation Updates

Update as needed:

- `README.md`
- `DECISIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `PHASE_07B_INTERFACE_EXTRACTION_HANDOFF.md`
- `PHASE_07C_PROVIDER_EXPERIMENT_PREP_HANDOFF.md`

If the dense artifact baseline remains intentionally hashed after cleanup, that must be stated explicitly in the relevant docs instead of leaving readers to infer the wrong thing.

## Validation

At minimum, run and record exact commands for:

```bash
uv run pytest -q tests/test_eval_cli.py tests/test_evals.py tests/test_retrieval.py tests/test_retrieval_cli.py tests/test_answer_generation.py tests/test_answer_cli.py
uv run eliza-rag-eval --help
```

If artifact files are regenerated, record the exact commands used to regenerate them.

## Definition Of Done

This cleanup pass is done when:

- the eval CLI surface matches the provider-prep claims
- dense artifact files, baseline eval output, and repo docs agree on the current dense baseline
- the answer-backend interface story is clean in both code and handoff docs
- the resulting Phase 07 state can be reviewed without obvious congruence gaps
