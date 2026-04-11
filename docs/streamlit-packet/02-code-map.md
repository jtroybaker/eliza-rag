# Code Map

This section maps each important file to its role in the Streamlit app.

## Entry Points

### `streamlit_app.py`

Purpose:

- root launcher used by `streamlit run streamlit_app.py`

What it does:

- imports `main` from `eliza_rag.streamlit_app`
- calls `main()` under `if __name__ == "__main__":`

Why it exists:

- keeps the Streamlit CLI entrypoint simple while letting the real app live inside the package

## Frontend Module

### `src/eliza_rag/streamlit_app.py`

Purpose:

- builds the full Streamlit experience

Key functions:

- `main()`: page setup, theme injection, layout, and top-level composition
- `_init_state()`: initializes session keys
- `_available_provider_settings()`: computes provider options from env vars and base settings
- `_render_setup_panel()`: archive restore and local runtime controls
- `_render_query_controls()`: provider, retrieval mode, reranking, and advanced options
- `_render_query_form()`: handles the actual submit event and backend calls
- `_render_results_panel()`: selects between empty state, error, answer, or search rendering
- `_render_answer_payload()`: renders answer, findings, uncertainty, and citations
- `_render_search_payload()`: renders retrieval-only results
- `_render_citation_expander()`: shows chunk text plus metadata for one citation
- `_apply_chromatic_editorial_theme()`: injects the custom visual style

Important design choice:

- the file does not implement retrieval or generation algorithms itself
- it orchestrates imported backend functions and formats their outputs for humans

## Configuration

### `src/eliza_rag/config.py`

Purpose:

- centralizes settings, repo paths, defaults, and environment variables

Why the app depends on it:

- the Streamlit page needs a single source of truth for:
  - data directories
  - LanceDB table names
  - archive URLs
  - LLM provider and model settings
  - local Ollama runtime settings

Important behavior:

- `get_settings()` merges `.env`, `.env.local`, and process environment variables
- the result is cached with `@lru_cache(maxsize=1)`

Practical implication:

- the app reads configuration once per process and then reuses it across reruns

## Retrieval Layer

### `src/eliza_rag/retrieval.py`

Purpose:

- query analysis, artifact readiness checks, retrieval execution, hybrid fusion, and reranking

Key concepts:

- `StructuredQuery`: normalized query plus detected companies and date hints
- retriever adapters: lexical, dense, hybrid, targeted hybrid
- reranker adapters: heuristic, `bge-reranker-v2-m3`, `bge-reranker-base`

Important functions:

- `analyze_query(...)`
- `index_status(...)`
- `retrieve(...)`
- `retrieve_lexical(...)`
- `retrieve_dense(...)`
- `retrieve_hybrid(...)`
- `retrieve_targeted_hybrid(...)`
- `rerank_results(...)`
- `warm_retrieval_models(...)`

Why `targeted_hybrid` matters:

- it actively spreads retrieval across multiple detected target tickers when the query looks comparative

## Answer Layer

### `src/eliza_rag/answer_generation.py`

Purpose:

- converts retrieved chunks into a grounded prompt, calls a backend, and validates the model output

Important classes:

- `OpenAICompatibleResponsesClient`
- `LocalOllamaGenerateClient`
- `PromptPackage`
- `ProviderConfig`

Important functions:

- `resolve_provider_config(...)`
- `build_answer_backend_client(...)`
- `generate_answer(...)`
- `build_prompt_package(...)`
- `parse_model_response(...)`

Why it matters:

- this file is where a search result becomes a final answer
- it also enforces the contract that answers must be valid JSON with citations

## Local Runtime Layer

### `src/eliza_rag/local_runtime.py`

Purpose:

- manage the repo-supported local Ollama workflow

Important behavior:

- checks whether Ollama exists on `PATH`
- checks whether the Ollama server is reachable
- checks whether the configured model is already available
- can start the server and pull the model

Why the Streamlit page uses it:

- the page has buttons for "Check Runtime" and "Prepare Runtime"
- those buttons are thin wrappers around this module

## Storage And Archive Restore

### `src/eliza_rag/storage.py`

Purpose:

- LanceDB table creation, dense index building, archive packaging, and archive restore

Important functions for the app:

- `fetch_lancedb_archive(...)`
- `prepare_lancedb_artifacts(...)`
- `create_lancedb_archive(...)`

Why it matters:

- the Streamlit setup panel depends on this module to make the demo portable
- reviewers do not need to rebuild indexes from scratch if the archive is published

## Data Models

### `src/eliza_rag/models.py`

Purpose:

- typed payloads for retrieval, answers, citations, and corpus inspection

Why it matters:

- these dataclasses define the shapes passed between backend code and the UI
- they reduce ad hoc dict handling until the final rendering layer

## Prompt File

### `prompts/final_answer_prompt.txt`

Purpose:

- defines the final answer-generation contract

Why it matters:

- the app's answer path depends on the model returning exactly one JSON object
- grounding requirements are specified here, not only in code comments

## Streamlit Config

### `.streamlit/config.toml`

Purpose:

- sets Streamlit theme defaults

Why it matters:

- even though the app injects custom CSS, this file still establishes the base color scheme for Streamlit-native components

## Recommended Reading Path For New Engineers

1. `src/eliza_rag/streamlit_app.py`
2. `src/eliza_rag/config.py`
3. `src/eliza_rag/retrieval.py`
4. `src/eliza_rag/answer_generation.py`
5. `src/eliza_rag/local_runtime.py`
6. `src/eliza_rag/storage.py`
7. `src/eliza_rag/models.py`
8. `prompts/final_answer_prompt.txt`

That order follows the same direction as a user request moving through the system.
