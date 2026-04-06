# Phase 03 Handoff

## Status

Phase 03 is complete for the intended scope:

- first retrieval mode implemented over the local LanceDB chunk table
- retrieval results normalized into a reusable ranked result shape
- metadata-aware filtering hooks added for lexical retrieval
- smoke tests and runnable query commands added

Phase 03 definition of done is satisfied:

- the repo has one working retrieval mode over `filing_chunks`
- retrieval results preserve downstream metadata needs
- simple retrieval smoke tests succeed

## What Was Implemented

Key files:

- `src/eliza_rag/models.py`
- `src/eliza_rag/retrieval.py`
- `src/eliza_rag/retrieval_cli.py`
- `tests/test_retrieval.py`
- `scripts/search_chunks.py`
- `pyproject.toml`
- `README.md`
- `IMPLEMENTATION_KANBAN.md`

## Spec Coverage

### 1. First retrieval mode

Implemented a lexical retrieval path over the existing `filing_chunks` LanceDB table.

Delivered behavior:

- accepts a natural-language query
- runs LanceDB FTS over chunk text
- preserves chunk metadata in ranked results
- keeps the retrieval path local and reproducible

Operational notes:

- retrieval setup lazily creates the `text` FTS index if needed
- scalar indices are also created for `ticker`, `form_type`, and `filing_date`
- phrase-query mode upgrades the text index to store positions when needed

### 2. Retrieval result normalization

Implemented a common result object in `src/eliza_rag/models.py`.

Each normalized result includes:

- `chunk_id`
- `filing_id`
- `ticker`
- `form_type`
- `filing_date`
- `section`
- `section_path`
- `text`
- `raw_score`
- `retrieval_mode`
- `rank`

Additional preserved fields:

- `company_name`
- `fiscal_period`
- `source_path`
- `chunk_index`

### 3. Metadata-aware filtering hooks

Implemented a structured filter object for lexical retrieval.

Currently supported filters:

- ticker
- form type
- filing-date lower bound
- filing-date upper bound

The retrieval module converts these into a LanceDB prefilter expression so later dense or hybrid modes can reuse the same high-level filter shape.

### 4. Retrieval smoke tests

Added smoke coverage in `tests/test_retrieval.py`.

Covered behaviors:

- filter SQL generation
- normalized lexical retrieval results with ranks and scores
- combined ticker, form type, and filing-date filtering

## New Command Paths

Primary CLI path:

```bash
uv run eliza-rag-search "risk factors" --ticker AAPL --top-k 3 --phrase-query
```

Script wrapper path:

```bash
uv run --no-sync python scripts/search_chunks.py "revenue growth" --ticker GOOG --form-type 10-K --filing-date-from 2025-01-01 --filing-date-to 2025-12-31
```

## Verification

Verification completed on April 2, 2026 with:

```bash
uv run python -m compileall src scripts tests
uv run --extra dev pytest tests/test_retrieval.py
uv run eliza-rag-search "risk factors" --ticker AAPL --top-k 3 --phrase-query
```

Observed results:

- compile check succeeded
- retrieval smoke tests passed: `3 passed`
- CLI retrieval returned `3` ranked Apple chunks for the phrase query `risk factors`
- first result was `AAPL_10K_2022Q3_2022-10-28_full::chunk-0007`
- local index status after retrieval included `text_idx`, `ticker_idx`, `form_type_idx`, and `filing_date_idx`

## Known Limitations

- retrieval is lexical-only for now; dense and hybrid modes remain future work
- section metadata is still heuristic because the source corpus is flattened
- phrase-query support may rebuild the FTS index once when position data is first required

## Documentation Updated

Updated repo docs required by the kickoff:

- `README.md` updated with runnable retrieval commands
- `IMPLEMENTATION_KANBAN.md` updated to mark lexical retrieval, normalization, and smoke tests as done
- `PHASE_03_HANDOFF.md` written as the phase record

`DECISIONS.md` was not changed because Phase 03 followed the existing retrieval direction rather than introducing a new architectural choice.

## Explicit Non-Goals Preserved

The following were intentionally not implemented in Phase 03:

- dense retrieval
- hybrid retrieval
- deterministic query analysis
- query expansion
- reranking
- answer generation
- full evaluation harness
- UI work

## Recommended Phase 04 Start

Next work should focus on:

- adding a second retrieval mode, likely dense retrieval
- introducing shared query-analysis and expansion hooks
- implementing hybrid retrieval behind the same normalized result interface
- starting early retrieval evaluation beyond smoke tests
