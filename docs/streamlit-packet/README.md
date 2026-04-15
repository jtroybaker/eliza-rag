# Streamlit Technical Packet

This packet explains the Streamlit code in this repository as a Streamlit program first.

It intentionally does not try to teach:

- the app's RAG design
- the retrieval pipeline
- answer-generation behavior
- provider-specific backend details

Those systems are treated here as imported Python functions. The goal is to help a new engineer understand how the page behaves at the Streamlit layer: reruns, state, layout, forms, buttons, rendering, and custom styling.

Read it in this order:

1. `01-ground-up.md`: the Streamlit execution model used by this app
2. `02-code-map.md`: where each Streamlit concern lives in the code
3. `03-runtime-data-and-ops.md`: practical Streamlit debugging, state, and editing notes
4. `04-classroom-walkthrough.md`: a teaching script focused on Streamlit mechanics

## Primary Files

- `streamlit_app.py`: the repo-root launcher used by `streamlit run streamlit_app.py`
- `src/eliza_rag/streamlit_app.py`: the actual Streamlit implementation

## One-Sentence Mental Model

This app is a single Streamlit script that reruns from top to bottom on each interaction, using `st.session_state` to preserve the data the results panel needs.
