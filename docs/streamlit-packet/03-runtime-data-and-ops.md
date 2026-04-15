# Streamlit Runtime, State, And Editing Notes

This file focuses on practical Streamlit behavior you will run into while editing this app.

## How To Run The Page

Install dependencies:

```bash
uv sync
```

Start the page:

```bash
uv run streamlit run streamlit_app.py
```

The repo-root launcher is the file Streamlit should target.

## What Happens When You Save A File

In normal Streamlit development:

- you edit the Python file
- Streamlit detects the change
- the app reruns
- the browser updates

That makes it very fast to iterate on layout and widget changes.

## The Main State Contract

The app depends on these `st.session_state` keys:

- `run_payload`
- `run_error`
- `run_logs`
- `setup_payload`
- `setup_error`
- `runtime_payload`
- `runtime_error`

If you change the render flow, update the state contract carefully.

Typical mistakes:

- writing a new key in one place and forgetting to initialize it
- changing the payload shape without updating the result renderer
- storing an object that `st.json(...)` cannot display cleanly

## What Should Go In Session State

Good candidates:

- the latest result payload
- the latest error string
- progress messages
- compact JSON-friendly metadata

Bad candidates:

- transient local formatting variables
- objects that only matter within one helper call
- values that can be recomputed cheaply on every rerun

Rule of thumb:

If the right panel needs to remember it after the click is over, store it.

## What Should Stay Local

These should usually remain local variables:

- current widget return values
- small layout helpers
- temporary strings used to build headers
- per-run placeholder objects from `st.empty()`

Local variables are fine when they only need to exist during the current script run.

## `st.empty()` Versus `st.session_state`

These serve different purposes.

Use `st.empty()` when:

- you want to replace a visible block during the current run
- you are streaming or updating progress text

Use `st.session_state` when:

- you need the next rerun to remember something
- another part of the page should read the stored value later

This app uses both patterns.

## Buttons Versus Forms

Use a button when:

- one click should trigger one action immediately

Use a form when:

- several inputs should be gathered together
- the expensive work should happen only when the user explicitly submits

This app uses plain buttons for setup/runtime actions and a form for the query path. That split is a good Streamlit pattern.

## Why The Renderers Read From State

The results panel does not try to share local variables with the click handlers.

That is intentional.

Benefits:

- render code stays simple
- action handlers stay simple
- reruns are easier to reason about
- state bugs are easier to debug

If you find yourself trying to thread local variables across unrelated helpers, you are probably fighting the Streamlit model.

## Working With Custom HTML

This app uses a lot of `st.markdown(..., unsafe_allow_html=True)`.

Practical rules:

- escape dynamic text with `html.escape(...)`
- keep repeated HTML in helper functions
- avoid mixing too much business logic into the HTML string building
- remember that Streamlit markdown is still the injection point for the HTML

If you skip escaping, user input or model output can break the markup or render unsafe HTML.

## Working With Custom CSS

The theme is injected directly in `_apply_chromatic_editorial_theme()`.

Benefits:

- one file controls the visual system
- no separate frontend toolchain
- easy to iterate during Streamlit development

Tradeoffs:

- the CSS can get long
- class names are informal, not componentized
- some selectors target Streamlit internals and may need updates when Streamlit changes

When editing the CSS, prefer changing variables or helper classes before adding more one-off rules.

## Common Streamlit Debugging Questions

### "Why did my variable reset?"

Because the script reran and the value was only local.

Fix:

- store it in `st.session_state` if it must survive reruns

### "Why did my button logic only fire once?"

Because `st.button(...)` is event-like, not stateful.

Fix:

- persist any lasting effect in session state

### "Why is my expensive code running too often?"

Because it is outside the button/form submit branch, or tied to a widget that reruns the page.

Fix:

- move the expensive work into a form submit or explicit button branch

### "Why did the result panel stop rendering?"

Common causes:

- a session-state key is missing
- the stored payload shape changed
- the renderer expects a field that no longer exists

Fix:

- inspect the payload with `st.json(...)`
- check `_init_state()`
- check the rendering helpers that read the payload

## Safe Editing Strategy

When changing this Streamlit file:

1. read `main()`
2. find the state keys involved
3. find which handler writes them
4. find which renderer reads them
5. make sure the payload shape still matches

That approach catches most bugs faster than reading the whole file linearly.

## What To Verify After Streamlit-Focused Changes

If you change layout, state, or widgets, verify:

1. the app still imports
2. the page loads
3. the left and right columns render
4. setup buttons still update visible state
5. form submission still updates the results panel
6. expanders open with the expected content
7. error messages still appear after failures

## The Best Operational Summary

For Streamlit work, the app is easiest to maintain if you think in three layers:

- widget event handlers write state
- render helpers read state
- styling helpers control presentation
