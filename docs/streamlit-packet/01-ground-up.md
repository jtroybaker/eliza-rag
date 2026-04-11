# Ground-Up Explanation

## Start With The Right Mental Model

This app is not a standalone product with its own custom backend server. It is a Streamlit interface wrapped around plain Python functions already present in the repo.

That distinction matters:

- Streamlit handles page rendering, widgets, and session state
- repo modules handle retrieval, answer generation, storage, and local runtime management
- the app stitches those layers together into one workflow

## The Smallest Useful Architecture

There are five layers:

1. `streamlit run streamlit_app.py` starts the UI
2. `streamlit_app.py` imports and calls `eliza_rag.streamlit_app.main()`
3. the Streamlit module builds the page, tracks state, and reacts to button/form submits
4. backend modules perform retrieval, answer generation, archive restore, and runtime preparation
5. Streamlit renders the returned payloads as cards, expanders, evidence blocks, and metadata panes

## End-To-End Flow

```mermaid
flowchart TD
    A[User opens Streamlit page] --> B[main()]
    B --> C[set_page_config + inject CSS theme]
    C --> D[initialize session_state keys]
    D --> E[load Settings from env and repo paths]
    E --> F[build provider options]
    F --> G[render Setup panel]
    F --> H[render Ask controls]
    H --> I[submit form]
    I --> J[analyze query]
    J --> K{Run mode}
    K -->|Search| L[retrieve evidence]
    K -->|Answer| M[retrieve evidence]
    M --> N[build grounded prompt]
    N --> O[call LLM backend]
    O --> P[validate JSON + citations]
    L --> Q[store payload in session_state]
    P --> Q
    Q --> R[st.rerun()]
    R --> S[render results panel]
```

## What Happens On Page Load

When the app starts, `main()` does the following in order:

1. sets Streamlit page metadata such as title, icon, layout, and sidebar state
2. injects a custom editorial CSS theme
3. initializes `st.session_state` keys used across reruns
4. loads repo settings via `get_settings()`
5. builds provider choices from environment variables
6. renders the top banner, left-side controls, and right-side results panel

This is standard Streamlit behavior: every interaction reruns the script from top to bottom, and persistent data is carried through `st.session_state`.

## Why Session State Matters Here

Without session state, every button click would wipe the last run result. This app stores the important outputs in:

- `run_payload`: last search or answer result
- `run_error`: last user-visible run error
- `run_logs`: pipeline progress messages shown in the UI
- `setup_payload`: archive restore result
- `setup_error`: archive restore error
- `runtime_payload`: local runtime status or prepare result
- `runtime_error`: local runtime error

That is the core reason the app feels like a stateful workflow instead of a stateless script dump.

## The Left Column: Setup And Ask

The left column has three jobs.

### 1. Setup

The setup panel checks whether retrieval artifacts exist locally. It uses `index_status(settings)` to determine whether the lexical and dense LanceDB tables are present.

The "Restore Archive" button calls `fetch_lancedb_archive(settings)`.

What that means in practice:

- if the repo already has the local archive and tables, the environment is ready
- if not, the app can restore them from a configured archive source

### 2. Local Runtime

The runtime panel exists for the local Ollama path.

It uses `build_local_runtime_manager(settings)` and then:

- `status()` to inspect whether Ollama exists, is running, and has the model
- `prepare(pull=True)` to start the server and pull the model if needed
- `warm_retrieval_models(settings)` to preload retrieval-time models

This keeps the "first real query" from paying all setup costs at once.

### 3. Ask

The query controls define how the pipeline should run:

- provider: local Ollama, hosted OpenAI, hosted OpenRouter, or a configured compatible API
- retrieval mode: `targeted_hybrid`, `hybrid`, `dense`, or `lexical`
- reranking: on or off
- reranker choice: `bge-reranker-v2-m3`, `bge-reranker-base`, or `heuristic`
- show summary: whether to display the model-generated executive summary
- run mode: `Answer` or `Search`

The form does not do any work until the submit button is pressed.

## What Happens When The User Clicks Submit

The form handler `_render_query_form(...)` is the operational center of the page.

It does this:

1. validates that the text box is not empty
2. creates a `logs` list and status placeholder
3. defines a `_progress()` callback so backend work can surface progress messages in the UI
4. creates empty `RetrievalFilters()`
5. runs deterministic query analysis with `analyze_query(...)`
6. branches into either search-only retrieval or full answer generation
7. writes the resulting payload into session state
8. triggers `st.rerun()` so the right column redraws from stored state

The split between search and answer is important:

- `Search` returns ranked chunks only
- `Answer` returns a grounded synthesis plus citations and the underlying retrieval results

## Search Mode

Search mode calls `retrieve(...)`.

Inside that path:

1. the query analyzer creates a `StructuredQuery`
2. filters are merged with detected tickers or dates
3. a retriever is selected based on mode
4. lexical, dense, or hybrid candidates are fetched from LanceDB
5. optional reranking reorders the candidate set
6. normalized `RetrievalResult` objects are returned

The page then stores those results and renders them as expanders with chunk text and metadata.

## Answer Mode

Answer mode calls `generate_answer(...)`.

That function does more work:

1. runs retrieval using the selected retrieval mode
2. ensures at least one retrieval result exists
3. builds a prompt package using the final prompt template and retrieved chunk texts
4. chooses an answer backend client based on provider settings
5. sends one final generation request
6. parses the model output as strict JSON
7. validates findings, summary, uncertainty, and inline citation ids
8. returns an `AnswerResponse`

This is deliberately single-call answer generation. The repo is not using an agent loop for the final answer step.

## How The Prompt Is Built

The answer prompt comes from `prompts/final_answer_prompt.txt`.

The code turns retrieval results into labeled context blocks:

- each chunk is assigned a citation id like `C1`, `C2`, `C3`
- chunk metadata is included in the context header
- the chunk text is appended below that header
- the question and concatenated context are injected into the template

That design gives the model a strict vocabulary for evidence references and makes post-validation possible.

## How Citations Stay Grounded

The answer parser does not trust the model blindly.

It validates that:

- the response is a JSON object
- `summary`, `answer`, and `uncertainty` exist with the expected types
- `findings` is a list of objects with statements and citations
- the `answer` contains valid inline citations such as `[C1]`

If the model cites unknown ids, the parser strips those. If the answer has no valid inline citations but the findings do, the parser appends the known finding citations. If nothing valid remains, it raises an error.

That is one of the stronger parts of the implementation: the app enforces basic grounding rules after generation instead of only hoping the prompt worked.

## Retrieval Modes In Plain English

### `lexical`

Uses full-text search over chunk text. Good for exact language matches.

### `dense`

Uses vector similarity over chunk embeddings. Good for semantic similarity.

### `hybrid`

Runs lexical and dense retrieval separately, then fuses ranks.

### `targeted_hybrid`

Uses hybrid retrieval, but if the query names multiple companies and appears comparative, it allocates retrieval coverage across those target tickers before falling back to general hybrid results.

This mode is why the repo is better suited for prompts like:

"Compare the main risk factors facing Apple and Tesla."

It reduces the chance that one company dominates all top results.

## Why The UI Uses `st.rerun()`

After setup, runtime, search, or answer actions, the app stores payloads in session state and forces a rerun.

That pattern gives two benefits:

- widget callbacks stay simple
- rendering logic remains clean because the results panel reads from state instead of from in-flight local variables

In other words, the action handlers mutate state, and the results panel is a pure-ish view over that state.

## The Right Column: Inspect

The results panel shows three kinds of information:

1. current status or errors
2. run metadata such as provider, model, retrieval mode, structured query, and progress logs
3. either a grounded answer view or a retrieval-results view

For answers, the panel renders:

- answer prose
- optional summary
- findings list
- uncertainty note
- evidence expanders for each citation

For retrieval-only searches, it renders chunk expanders directly.

## Failure Modes

The app is designed to surface operational failures clearly:

- missing archive or missing tables
- dense index not ready
- lexical index not ready
- local Ollama not installed
- local Ollama server not running
- local Ollama model not pulled
- hosted provider key missing
- backend endpoint unreachable
- model response not valid JSON
- answer response missing valid citations

Most of these become `st.error(...)` messages through the stored `*_error` state fields.

## Why This App Is Reasonable Engineering

The implementation is intentionally modest:

- one thin frontend file
- separate backend modules for retrieval, storage, and answer generation
- explicit data models
- strict answer parsing
- portable restore-first local retrieval

That makes it teachable. A reader can start at the Streamlit page, follow the function calls downward, and understand the full system without needing hidden services or complex orchestration.
