# Phase 07C Handoff: Provider Experiment Prep

## What Landed

- explicit named embedder selections for the current baseline and first alternate candidate
- explicit named reranker selections for the current baseline and first alternate candidate
- dense-index build CLI support for side-by-side alternate embedder builds
- README commands for baseline versus candidate provider comparisons
- focused tests covering the new selection surface and alternate reranker path

## Implementation Summary

The Phase 07C implementation stayed bounded to provider-experiment preparation rather than changing the default retrieval path.

Main additions:

- `src/eliza_rag/embeddings.py`
  - added named embedder aliases:
    - `snowflake-arctic-embed-xs`
    - `bge-m3`
    - existing `hashed_v1`
  - resolved embedder selection through the extracted embedder interface rather than relying only on raw model strings
- `src/eliza_rag/dense_index_cli.py`
  - added `--embedder` so baseline and alternate dense builds are explicit and inspectable
- `src/eliza_rag/storage.py`
  - dense-index build output now records both the named embedder alias and the resolved embedding model id
- `src/eliza_rag/retrieval.py`
  - added alternate reranker adapter `bge-reranker-base`
  - kept `bge-reranker-v2-m3` as the default reranker path
  - generalized transformer-reranker loading so both rerankers stay behind the same interface
- `src/eliza_rag/retrieval_cli.py`
  - exposed the alternate reranker in CLI selection
- `src/eliza_rag/answer_cli.py`
  - exposed the alternate reranker in the end-to-end answer CLI as well

## Default Behavior Check

This phase intentionally did not flip defaults.

Current defaults remain:

- dense embedder default: `Snowflake/snowflake-arctic-embed-xs`
- reranker default: `bge-reranker-v2-m3`
- retrieval recommendation for named-company comparison prompts: `targeted_hybrid`

Current saved local artifact note:

- the committed `artifacts/dense_index_metadata.json` snapshot still describes a `hashed_v1` dense index
- that artifact state should not be read as a recommendation change; it means the local saved baseline artifact has not yet been refreshed to the Snowflake default

Interpretation:

- the repo can now wire alternate embedding and reranking providers explicitly
- the repo has not yet produced evidence that the alternate providers are better than the baseline

## Exact Commands Used

Focused verification:

```bash
uv run pytest -q tests/test_embeddings.py::test_resolve_embedder_model_supports_named_provider_aliases tests/test_embeddings.py::test_resolve_embedder_alias_prefers_named_provider_aliases tests/test_retrieval.py::test_retrieve_can_use_alternate_transformer_reranker tests/test_retrieval_cli.py::test_retrieval_cli_forwards_rerank_arguments tests/test_answer_cli.py::test_answer_cli_forwards_rerank_arguments tests/test_config.py
```

Documented baseline dense build:

```bash
uv run eliza-rag-build-dense-index \
  --embedder snowflake-arctic-embed-xs \
  --dense-table-name filing_chunks_dense \
  --metadata-artifact-name dense_index_metadata.json
```

Documented alternate embedding build:

```bash
uv run eliza-rag-build-dense-index \
  --embedder bge-m3 \
  --dense-table-name filing_chunks_dense_bge_m3 \
  --metadata-artifact-name dense_index_metadata.bge_m3.json
```

Documented baseline reranker run:

```bash
uv run eliza-rag-search "Compare the main risk factors facing Apple and Tesla" \
  --mode targeted_hybrid \
  --top-k 5 \
  --rerank \
  --reranker bge-reranker-v2-m3
```

Documented alternate reranker run:

```bash
uv run eliza-rag-search "Compare the main risk factors facing Apple and Tesla" \
  --mode targeted_hybrid \
  --top-k 5 \
  --rerank \
  --reranker bge-reranker-base
```

## Validation Completed

- focused provider-selection test slice passed:
  - `8 passed in 0.76s`

What this validation proves:

- embedder aliases resolve correctly
- alternate reranker selection is wired correctly
- retrieval, answer, and eval CLIs accept the expanded reranker selection surface

What it does not prove:

- that `bge-m3` is a better embedder than the Snowflake baseline
- that `bge-reranker-base` is a better reranker than `bge-reranker-v2-m3`
- that the alternate dense build has already been executed against the current local artifact set

## Prerequisites And Operational Notes

- `uv sync` must be run before using the Hugging Face-backed embedding and reranker adapters
- first use of `bge-m3`, `bge-reranker-v2-m3`, or `bge-reranker-base` will trigger model downloads from Hugging Face
- alternate dense builds should use a separate dense table name and metadata artifact name so baseline artifacts remain intact

## Recommended Next Work

- run the committed golden eval slice one component at a time against:
  - baseline embedder plus baseline reranker
  - alternate embedder plus baseline reranker
  - baseline embedder plus alternate reranker
- save those eval outputs as explicit experiment artifacts before considering any default recommendation change
