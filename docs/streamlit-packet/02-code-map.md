# Streamlit Code Map

This file maps the code by Streamlit responsibility rather than by product behavior.

## `streamlit_app.py`

Purpose:

- acts as the Streamlit CLI entrypoint

What to notice:

- it is intentionally tiny
- it imports `main` from the package
- it keeps `streamlit run streamlit_app.py` simple

Why this pattern is useful:

- the actual app can live in `src/`
- import paths stay normal
- the launcher stays easy to inspect

## `src/eliza_rag/streamlit_app.py`

This is the real Streamlit page.

Think of it in five parts.

### 1. Top-Level App Composition

Key function:

- `main()`

Streamlit responsibilities:

- configure the page with `st.set_page_config(...)`
- apply the CSS theme
- initialize `st.session_state`
- create the two-column layout
- call the render helpers in page order

This is the "page assembly" layer.

### 2. State Initialization

Key function:

- `_init_state()`

Streamlit responsibility:

- declare the session keys the page expects to exist

Why it matters:

- later render functions can safely read session state without repeated guard code
- it makes the rerun model much easier to reason about

### 3. Input And Control Rendering

Key functions:

- `_render_setup_panel()`
- `_render_query_controls()`
- `_render_query_form()`

Streamlit responsibilities:

- draw buttons, radios, toggles, selectboxes, and text areas
- decide which controls live in columns
- group the expensive inputs inside a form
- respond to button clicks and form submit events

What to notice:

- buttons are handled inline with `if st.button(...):`
- form submission is handled with `st.form_submit_button(...)`
- advanced options are tucked into `st.expander(...)`

This is the main "interaction" layer.

### 4. Result Rendering

Key functions:

- `_render_results_panel()`
- `_render_answer_payload()`
- `_render_search_payload()`
- `_render_result_expanders()`
- `_render_citation_expander()`

Streamlit responsibilities:

- show empty-state UI before the first run
- show errors after failed actions
- render structured metadata with `st.json(...)`
- render long result details inside expanders
- display stored outputs from `st.session_state`

What to notice:

- this part of the file is mostly read-only
- it does not trigger actions
- it turns stored Python data into visible UI

This is the "view" layer.

### 5. HTML And Styling Helpers

Key functions:

- `_metric_card(...)`
- `_citation_card(...)`
- `_paragraphs(...)`
- `_status_banner(...)`
- `_apply_chromatic_editorial_theme()`

Streamlit responsibilities:

- package repeated HTML snippets
- safely escape text placed into HTML
- inject CSS with `st.markdown(...)`

What to notice:

- these helpers exist because the app goes beyond Streamlit's default widget styling
- the CSS is inline, so there is no separate frontend build system

This is the "presentation polish" layer.

## Streamlit Features Used In This Repo

If you are learning Streamlit, these are the concrete APIs to study in this file:

- `st.set_page_config`
- `st.columns`
- `st.markdown`
- `st.radio`
- `st.selectbox`
- `st.toggle`
- `st.text_area`
- `st.form`
- `st.form_submit_button`
- `st.button`
- `st.expander`
- `st.empty`
- `st.spinner`
- `st.error`
- `st.success`
- `st.warning`
- `st.caption`
- `st.write`
- `st.json`
- `st.rerun`
- `st.session_state`

## Boundaries To Keep In Mind

When reading the code, separate these two kinds of functions:

Streamlit-facing functions:

- create layout
- read widget values
- manage session state
- display output

Non-Streamlit backend functions:

- return status data
- perform long-running work
- build domain-specific payloads

The app is easier to understand if you keep those boundaries clean in your head.

## Best Reading Path For A New Streamlit Reader

1. `streamlit_app.py`
2. `src/eliza_rag/streamlit_app.py:main()`
3. `_init_state()`
4. `_render_query_form()`
5. `_render_results_panel()`
6. `_apply_chromatic_editorial_theme()`

That path teaches the launcher, rerun model, state model, and rendering model with the least distraction.
