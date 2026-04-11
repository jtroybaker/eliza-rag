# Runtime, Data, And Operations

## What Must Exist For The App To Work

The app needs four categories of things:

1. Python dependencies
2. SEC filing corpus and retrieval artifacts
3. an answer backend
4. optional local runtime support if using Ollama

## Dependencies

The project depends on:

- `streamlit` for the UI
- `lancedb` for local retrieval tables
- `sentence-transformers` and related model tooling for embeddings and reranking
- `python-dotenv` for local env loading

Install with:

```bash
uv sync
```

Run the app with:

```bash
uv run streamlit run streamlit_app.py
```

## Configuration Model

The app uses `get_settings()` as its single settings source.

Settings come from:

1. `.env`
2. `.env.local`
3. the current shell environment

Common variables include:

- `ELIZA_RAG_LANCEDB_ARCHIVE_URL`
- `ELIZA_RAG_LLM_PROVIDER`
- `ELIZA_RAG_LLM_MODEL`
- `ELIZA_RAG_OPENAI_API_KEY`
- `ELIZA_RAG_OPENROUTER_API_KEY`
- `ELIZA_RAG_LOCAL_LLM_BASE_URL`
- `ELIZA_RAG_LOCAL_LLM_MODEL`

## Retrieval Artifacts

The UI assumes retrieval is local.

That means the app expects:

- a lexical LanceDB table
- a dense LanceDB table
- dense index metadata

The setup panel checks readiness with `index_status(settings)`.

If those artifacts are missing, the intended recovery path is:

1. configure `ELIZA_RAG_LANCEDB_ARCHIVE_URL`
2. click `Restore Archive`

Under the hood, the app calls `fetch_lancedb_archive(settings)`, which:

- resolves a local or remote archive path
- clears any existing local LanceDB artifacts
- extracts the archive into the repo
- reconstructs dense metadata if needed

## Provider Selection Logic

The app does not hardcode one provider. It computes available options based on environment state.

The provider radio can expose:

- `Local Ollama`
- `Hosted OpenAI`
- `Hosted OpenRouter`
- `Configured Compatible API`

The options appear only when the required env state is available. For example:

- hosted OpenAI is added if an OpenAI key exists
- hosted OpenRouter is added if an OpenRouter key exists
- a compatible API option is added when base settings already point to an OpenAI-compatible endpoint

## Local Ollama Path

When the provider is local, answer generation uses the native Ollama generate API instead of the OpenAI-compatible `/responses` API.

The runtime manager is responsible for:

- validating that the `ollama` command exists
- checking `http://127.0.0.1:11434`
- starting `ollama serve` if needed
- pulling the configured model if missing

The UI offers two separate actions for good reason:

- `Check Runtime`: inspect state without changing anything
- `Prepare Runtime`: make the local path actually usable

## Hosted Provider Path

When using hosted providers:

- the app creates an `OpenAICompatibleResponsesClient`
- the final answer call is sent to `base_url + /responses`
- the API key is attached as a bearer token when required

This is intentionally minimal. The repo does not depend on a large SDK to do one request.

## Why The App Uses One Final Answer Call

The design keeps answer generation bounded:

- retrieval happens first
- the prompt is assembled once
- the model is called once
- the output is validated once

Operationally, that means:

- simpler debugging
- easier demo explanation
- fewer hidden states
- easier saved-artifact inspection

## Common Operational Failures

### Archive problems

Symptoms:

- setup card says archive missing
- answer or search calls fail due to missing lexical or dense tables

Likely fixes:

- configure `ELIZA_RAG_LANCEDB_ARCHIVE_URL`
- restore the archive again

### Ollama problems

Symptoms:

- runtime says not ready
- answer call fails for local provider

Likely fixes:

- install Ollama
- run `Prepare Runtime`
- verify the expected model name

### Hosted key problems

Symptoms:

- provider option is missing
- answer generation raises missing API key errors

Likely fixes:

- add the provider-specific key to `.env.local`
- restart the app if needed

### Model output problems

Symptoms:

- answer call completes but the parser rejects the response

Likely causes:

- model returned non-JSON output
- model omitted required fields
- model failed to include valid citations

Why this is acceptable:

- parser failure is better than silently showing an ungrounded answer

## What To Validate After Changes

If you modify the app or backend, validate these paths:

1. app imports cleanly
2. setup status renders
3. provider options appear as expected
4. search mode returns chunks
5. answer mode returns grounded answers with citations
6. local runtime buttons behave sensibly when Ollama is absent and when it is present
7. errors render cleanly in the right panel

## Operational Summary

The Streamlit app is operationally simple because it pushes complexity into reusable modules and keeps the UI layer as an orchestrator.

That makes the main operating model easy to remember:

- restore data
- choose backend
- run query
- inspect evidence
