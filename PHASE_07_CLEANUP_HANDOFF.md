# Phase 07 Cleanup Handoff: Congruence, Artifact Consistency, And Interface Hygiene

## Outcome

Phase 07 cleanup is implemented.

This pass closed the remaining congruence gaps between:

- public CLI surfaces
- saved evaluation and manifest artifacts
- current repo documentation
- interface claims in the Phase 07 handoff docs

## What Landed

- `eliza-rag-eval` now accepts the alternate reranker selection `bge-reranker-base`
- eval CLI coverage now includes the alternate reranker selection surface
- `answer_generation.py` now relies on the shared `AnswerBackend` protocol without a duplicate local backend protocol beside it
- repo docs now distinguish the code/config default dense path from the currently committed local dense artifact snapshot
- Phase 07 handoff docs now reflect the cleaned-up interface and CLI story

## Implementation Summary

### Eval CLI congruence

- `src/eliza_rag/eval_cli.py`
  - expanded `--reranker` choices to:
    - `bge-reranker-v2-m3`
    - `bge-reranker-base`
    - `heuristic`
- `tests/test_eval_cli.py`
  - added coverage proving the eval CLI accepts and forwards `bge-reranker-base`

Interpretation:

- the eval, retrieval, and answer CLIs now expose the same reranker selection surface for the current Phase 07 provider-prep story

### Answer backend interface hygiene

- `src/eliza_rag/answer_generation.py`
  - removed the duplicate local backend protocol
  - kept backend clients typed against the shared `AnswerBackend` contract from `interfaces.py`
- `tests/test_answer_generation.py`
  - now references the shared interface in the test fake client as well

Interpretation:

- the code now matches the Phase 07B claim that answer backends use the shared interface contract

### Dense artifact and documentation consistency

No dense artifact rebuild was performed in this cleanup pass.

Instead, the docs now state the actual current repo state explicitly:

- the code/config default dense path is `snowflake-arctic-embed-xs`
- the committed local artifact snapshot in `artifacts/dense_index_metadata.json` still describes `hashed_v1`
- the saved baseline eval artifact should therefore be read as a baseline against the current committed local artifact contract, not as proof that the local dense artifact has already been rebuilt with Snowflake

Files updated for that distinction:

- `README.md`
- `DECISIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `eval/README.md`
- `PHASE_07C_PROVIDER_EXPERIMENT_PREP_HANDOFF.md`

## Validation

Commands run:

```bash
uv run pytest -q tests/test_eval_cli.py tests/test_evals.py tests/test_retrieval.py tests/test_retrieval_cli.py tests/test_answer_generation.py tests/test_answer_cli.py
uv run eliza-rag-eval --help
```

Observed results:

- pytest slice: `56 passed in 64.01s`
- eval CLI help now includes:
  - `--reranker {bge-reranker-v2-m3,bge-reranker-base,heuristic}`

## Remaining Work

- run the bounded provider comparison slice against the committed golden eval set
- decide whether to rebuild and commit a Snowflake-based local dense artifact snapshot or continue treating the committed `hashed_v1` snapshot as the saved local baseline
- extend eval scoring beyond the current coverage-oriented placeholders
