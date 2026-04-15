# Ground-Up Streamlit Explanation

## Start With The Right Mental Model

The Streamlit execution model used in this app:

- Streamlit runs the script from top to bottom
- a user interaction causes another full rerun
- widget values are reconstructed on that rerun
- persistent values must live in `st.session_state`

If that model is clear, the rest of this file makes sense.

## What Actually Runs

The launch path is:

1. `streamlit run streamlit_app.py`
2. the repo-root `streamlit_app.py` imports `main`
3. `src/eliza_rag/streamlit_app.py:main()` builds the page

That root file is only a launcher. The real page code lives in the package module.

## The Core Streamlit Lifecycle In This App

```mermaid
flowchart TD
    A[Browser loads page] --> B[Streamlit runs main()]
    B --> C[set page config]
    C --> D[inject CSS]
    D --> E[initialize session_state keys]
    E --> F[render widgets and panels]
    F --> G{User interacts?}
    G -->|No| H[Page stays visible]
    G -->|Yes| I[Streamlit reruns script]
    I --> C
```

That loop is the whole app model.

## Why `main()` Looks Declarative

`main()` reads like layout code because it mostly is layout code:

- set page metadata
- apply theme
- initialize state
- compute options for widgets
- render left column
- render right column

This is normal Streamlit style. Instead of a permanent server-side UI tree, you rebuild the page description on every rerun.

## Why Session State Exists

Without `st.session_state`, the page would forget the previous result on every click.

This app stores these values:

- `run_payload`
- `run_error`
- `run_logs`
- `setup_payload`
- `setup_error`
- `runtime_payload`
- `runtime_error`

These keys matter because the right column is rendered from stored state, not from local variables created during a single button click.

## The Most Important Pattern In The File

The dominant pattern is:

1. a button or form submit triggers work
2. the handler stores a result or error in `st.session_state`
3. the code calls `st.rerun()`
4. the page redraws from the saved state

That is how the app creates the feeling of a persistent interface even though the script reruns each time.

## Columns

The page uses:

```python
left_col, right_col = st.columns([1.05, 0.95], gap="large")
```

That does two things:

- creates two layout containers
- lets the code render different UI sections inside each container with `with left_col:` and `with right_col:`

This is one of the most common Streamlit layout patterns.

## Buttons

In Streamlit, `st.button(...)` returns `True` only on the rerun caused by that click.

That means code like this:

```python
if st.button("Restore Archive"):
    ...
```

does not mean "this button is currently on." It means "the user clicked this button for this rerun."

That is why the app immediately stores results in session state. The `True` value from the button is temporary.

## Forms

The query area uses `st.form(...)`.

That matters because widgets inside a form behave differently from standalone widgets:

- editing the text area does not immediately trigger the expensive pipeline
- the form waits for `st.form_submit_button(...)`
- only the submit action should run the expensive code path

This is the correct Streamlit pattern when multiple widget inputs should be gathered and applied together.

## Radio Buttons, Selectboxes, And Toggles

The app uses a few common Streamlit input widgets:

- `st.radio(...)`
- `st.selectbox(...)`
- `st.toggle(...)`
- `st.text_area(...)`

These return plain Python values on each rerun. The code does not need to manually fetch them from the DOM. Streamlit reconstructs them for you.

Example:

- `st.radio(...)` returns the selected label
- `st.selectbox(...)` returns the selected option
- `st.toggle(...)` returns `True` or `False`

## Expanders

The app uses `st.expander(...)` for two jobs:

- hide advanced controls until the user wants them
- hide large result details until the user opens them

This is a strong Streamlit pattern because pages can get long quickly. Expanders keep the default view readable.

## Placeholders

The form handler creates:

```python
status_placeholder = st.empty()
```

`st.empty()` gives you a spot in the page that can be replaced later in the same run.

The app uses it so the progress callback can keep updating the visible status banner while work is running.

That is different from session state:

- `st.empty()` is for replacing a piece of UI during a run
- `st.session_state` is for surviving future reruns

## Spinners

The app wraps long-running work with:

```python
with st.spinner("Running the RAG flow..."):
    ...
```

From a Streamlit perspective, the important point is simple:

- the spinner gives immediate user feedback during blocking Python work
- it does not make the work asynchronous

The code is still synchronous Python running in the request.

## Rendering JSON

The results panel uses `st.json(...)` for metadata payloads.

That is useful because:

- it gives a readable structured view with almost no code
- it avoids hand-formatting nested dicts
- it works well for session-state-backed payloads

This is a common Streamlit convenience for debug panels and developer-facing metadata.

## Rendering Raw HTML

The app often uses:

```python
st.markdown(..., unsafe_allow_html=True)
```

That tells Streamlit to render HTML inside the markdown block.

The app uses this for:

- branded headers
- custom cards
- status banners
- citation card structure
- inline CSS theme injection

This is powerful, but it comes with a rule: if user- or model-generated text is inserted into HTML, it must be escaped. That is why the code uses `html.escape(...)`.

## Why `_paragraphs(...)` Exists

Streamlit can render plain markdown directly, but this app wants answer text inside custom card HTML.

So `_paragraphs(...)` converts plain text into escaped `<p>...</p>` blocks. That is a Streamlit/UI concern, not business logic.

## Why `_metric_card(...)` And `_status_banner(...)` Exist

These helpers return HTML strings for repeated UI structures.

They exist because:

- repeated `st.markdown("""...""")` blocks get noisy
- repeated card markup is easier to maintain in one place
- Streamlit has no built-in reusable HTML component abstraction for small cases like this

## Why There Is So Much `st.rerun()`

New Streamlit readers often ask whether `st.rerun()` is redundant because Streamlit reruns anyway.

In this app, the explicit `st.rerun()` calls are useful because:

- the handler mutates session state after the click
- the code wants a fresh render pass driven by the new stored payload
- it keeps the action code and display code cleanly separated

The pattern is:

- do work
- save state
- rerun
- render from state

## A Useful Way To Read This File

Read `src/eliza_rag/streamlit_app.py` in this order:

1. `main()`
2. `_init_state()`
3. `_render_setup_panel()`
4. `_render_query_controls()`
5. `_render_query_form()`
6. `_render_results_panel()`
7. the small HTML/render helpers
8. `_apply_chromatic_editorial_theme()`

That order mirrors how the page feels to the user and how Streamlit rebuilds the interface.

## What To Ignore On First Read

If your goal is to learn Streamlit from this file, treat these imported functions as black boxes:

- `get_settings()`
- `index_status(...)`
- `retrieve(...)`
- `generate_answer(...)`
- `fetch_lancedb_archive(...)`
- `build_local_runtime_manager(...)`

The Streamlit lesson is not what they do internally. The Streamlit lesson is how the page calls them and then renders the returned data.

## The Best Short Summary

This app is a standard Streamlit script with three important techniques:

- use columns, forms, expanders, and placeholders to structure the page
- use `st.session_state` to preserve results across reruns
- use `st.markdown(..., unsafe_allow_html=True)` plus CSS to go beyond default Streamlit styling
