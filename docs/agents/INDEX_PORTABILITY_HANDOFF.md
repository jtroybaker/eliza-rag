# Index Portability Handoff

## Purpose

This handoff records the concrete follow-up work completed from `docs/agents/INDEX_PORTABILITY_NEXT_STEPS.md`.

The repo now treats index portability as an explicit local-build reviewer flow rather than an implied or partially documented behavior.

## Portability Decision

Supported mode:

- local-build reviewer flow

Not implemented as the primary path:

- prebuilt zero-build search artifact distribution

Reasoning:

- the repo already had a deterministic local artifact build path
- reviewer ergonomics were better served by making the required build steps explicit
- prebuilt artifact packaging would add separate artifact-versioning and validation work that is not necessary for the current demo scope

## What Changed

### Code

Files updated:

- `src/eliza_rag/retrieval.py`
- `src/eliza_rag/retrieval_cli.py`
- `src/eliza_rag/answer_cli.py`
- `src/eliza_rag/answer_generation.py`
- `tests/test_retrieval.py`

Behavior changes:

- lexical retrieval now checks that the lexical LanceDB table exists before searching
- lexical failure guidance now tells the user to run `uv run eliza-rag-load-chunks`
- dense retrieval still checks that dense artifacts exist, but now does so after confirming the lexical table exists
- dense failure guidance tells the user to run `uv run eliza-rag-build-dense-index` after loading or refreshing chunks
- retrieval JSON status now reports:
  - lexical table presence
  - dense table presence
  - dense metadata artifact presence

### Docs

Files updated:

- `README.md`
- `DECISIONS.md`
- `docs/agents/IMPLEMENTATION_KANBAN.md`

Documentation changes:

- the local-build reviewer flow is now called out as the supported portability mode
- the README now has one authoritative reviewer setup path
- the README now states when `eliza-rag-load-chunks` is required
- the README now states when `eliza-rag-build-dense-index` is required
- rebuild triggers are documented explicitly and consistently

## Reviewer Setup Contract

Baseline:

```bash
uv sync
uv run eliza-rag-load-chunks
```

Required for dense, hybrid, or the default answer path:

```bash
uv run eliza-rag-build-dense-index
```

Then run either:

```bash
uv run eliza-rag-search "risk factors" --mode lexical
```

or:

```bash
uv run eliza-rag-answer "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
```

Important note:

- `eliza-rag-answer` defaults to `hybrid` retrieval, so it requires the dense build step unless the caller overrides `--mode lexical`

## Rebuild Rules

- rerun `uv run eliza-rag-load-chunks` whenever chunk materialization inputs or logic change
- rerun `uv run eliza-rag-build-dense-index` after every chunk-table refresh so `filing_chunks_dense` stays aligned with `filing_chunks`

## Validation Added

Lexical readiness:

- the system now fails clearly if `filing_chunks` is missing

Dense readiness:

- the system now fails clearly if either `filing_chunks_dense` or `artifacts/dense_index_metadata.json` is missing

Status reporting:

- `eliza-rag-search` includes `index_status` in its JSON payload so users can see whether lexical and dense artifacts are present

## Verification Status

Completed:

- `uv run python -m compileall src`
- targeted retrieval readiness tests for:
  - missing lexical table guidance
  - missing dense artifact guidance
  - readiness status payload shape

Observed result:

- targeted readiness tests passed: `3 passed, 6 deselected`

Environment note:

- a full `tests/test_retrieval.py` run printed progress but did not exit cleanly in this environment, so this handoff only claims the targeted readiness checks plus compile verification

Workspace note:

- a live readiness check in this workspace reported:
  - lexical table present
  - dense table present
  - dense metadata artifact present

## Remaining Optional Work

Not required for the current chosen portability mode, but still possible later:

- add a dedicated `eliza-rag-check-readiness` command if a single pre-demo validation command would help reviewers
- implement prebuilt artifact packaging if the project later wants a true zero-build review flow
- add artifact freshness validation beyond presence checks if stale-index detection becomes important
