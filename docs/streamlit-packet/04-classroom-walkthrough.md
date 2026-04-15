# Classroom Walkthrough

This file is a teaching script for explaining the Streamlit code, not the product behavior behind it.

## Five-Minute Version

### 1. Explain The Execution Model

Say:

"This page is a Streamlit script, so every interaction reruns the file from top to bottom. The app only feels stateful because important values are saved in `st.session_state`."

### 2. Explain The Entry Point

Say:

"`streamlit run streamlit_app.py` starts a tiny launcher file, which calls `main()` in `src/eliza_rag/streamlit_app.py`."

### 3. Explain The Layout

Say:

"`main()` builds a two-column layout. The left column contains controls and the right column displays the latest stored result."

### 4. Explain Actions

Say:

"Buttons handle immediate actions. The text query uses a form so typing does not trigger expensive work on every keystroke."

### 5. Explain Persistence

Say:

"After an action runs, the code stores a payload or error in `st.session_state`, calls `st.rerun()`, and the results panel redraws from the stored data."

## Ten-Minute Engineering Version

Walk through the code in this order:

1. `streamlit_app.py`
2. `src/eliza_rag/streamlit_app.py:main()`
3. `_init_state()`
4. `_render_setup_panel()`
5. `_render_query_controls()`
6. `_render_query_form()`
7. `_render_results_panel()`
8. `_apply_chromatic_editorial_theme()`

## Questions A New Streamlit Reader Should Be Able To Answer

After reading this packet, they should be able to answer:

1. Why is there both a root `streamlit_app.py` and a packaged Streamlit module?
2. Why does the script need `st.session_state`?
3. What is the difference between a button event and a form submit in Streamlit?
4. Why does the app call `st.rerun()` after storing results?
5. Why does the results panel read from session state instead of local variables?
6. What is `st.empty()` doing in the form handler?
7. Why does the app use `unsafe_allow_html=True`, and why is `html.escape(...)` important?

## What To Point At In The UI

When giving a walkthrough, explicitly point out:

- the two-column layout
- the setup buttons
- the grouped query form
- the advanced-options expander
- the right-side metadata expander
- the result expanders

Each one maps directly to a standard Streamlit pattern.

## Good Explanations To Avoid

Do not say:

- "Streamlit keeps a live object tree on the server"
- "Buttons remember their on/off state"
- "The page only rerenders the widget that changed"

Say instead:

- Streamlit reruns the script
- buttons are event-like
- lasting state must be stored explicitly

## If You Need A One-Minute Summary

Use this:

"This codebase uses Streamlit in a standard but well-structured way: a small launcher starts the packaged app, `main()` rebuilds the page on each rerun, user actions store payloads in `st.session_state`, and the results panel renders from that stored state. Layout comes from columns, forms, and expanders, while custom styling is handled with HTML and injected CSS."
