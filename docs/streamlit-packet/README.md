# Streamlit Educational Packet

This packet explains how the Streamlit app works from the ground up, using the current code in this repository rather than a generic Streamlit example.

Read it in this order:

1. `01-ground-up.md`: core concepts, app lifecycle, and end-to-end request flow
2. `02-code-map.md`: file-by-file tour of the implementation
3. `03-runtime-data-and-ops.md`: configuration, artifacts, local runtime, and failure modes
4. `04-classroom-walkthrough.md`: a teaching script for demos, onboarding, or handoff

## What The App Is

The app is a thin Streamlit frontend over the repo's existing RAG pipeline:

- setup and restore the local LanceDB retrieval artifacts
- check or prepare the local Ollama runtime
- choose a hosted or local answer provider
- run retrieval-only search or the full grounded answer flow
- inspect citations, chunk text, metadata, and pipeline status

## Primary Entry Points

- `streamlit_app.py`: root launcher used by `streamlit run`
- `src/eliza_rag/streamlit_app.py`: the actual app implementation

## One-Sentence Mental Model

The page itself does very little "AI" work. It mostly collects user choices, calls the repo's retrieval and answer functions, and renders their outputs in a reviewer-friendly format.
