# Classroom Walkthrough

This file is written as a teaching script for onboarding, interviews, demos, or handoff.

## Five-Minute Version

### 1. Explain The Page

Say:

"This is a Streamlit wrapper over a local SEC filings RAG pipeline. The page itself does not contain the retrieval or answer logic. It exposes that logic through setup buttons, query controls, and an evidence viewer."

### 2. Explain The Two Halves

Say:

"The left side is for preparing and running the pipeline. The right side is for inspecting what happened."

### 3. Explain Setup

Say:

"The app first checks whether the local LanceDB retrieval artifacts exist. If not, it can restore them from a published archive. It can also check or prepare a local Ollama runtime for the local answer path."

### 4. Explain Query Execution

Say:

"When I submit a question, the app analyzes the query, runs retrieval using the chosen mode, and either stops at evidence search or performs one final answer-generation call."

### 5. Explain Grounding

Say:

"The answer path labels retrieved chunks as citations like C1 and C2, includes them in the prompt, and then validates that the model's answer cites those ids correctly."

## Ten-Minute Engineering Version

Walk through the code in this order:

1. `streamlit_app.py`
2. `src/eliza_rag/streamlit_app.py`
3. `src/eliza_rag/config.py`
4. `src/eliza_rag/retrieval.py`
5. `src/eliza_rag/answer_generation.py`
6. `src/eliza_rag/local_runtime.py`
7. `src/eliza_rag/storage.py`

## Questions A New Engineer Should Be Able To Answer

After reading this packet, they should be able to answer:

1. Why is there both a root `streamlit_app.py` and a packaged Streamlit module?
2. What is stored in `st.session_state`, and why?
3. What is the difference between `Search` and `Answer` mode?
4. How does `targeted_hybrid` differ from regular `hybrid` retrieval?
5. How are answer citations created and validated?
6. What does `Prepare Runtime` actually do?
7. What is the intended recovery path if the local retrieval tables are missing?

## Demo Prompts

Use prompts that exercise the app's strengths:

- "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
- "How has NVIDIA's revenue and growth outlook changed over the last two years?"
- "Compare the main risk factors facing Apple and Tesla."

These prompts work because they stress company detection, comparison intent, and evidence inspection.

## What To Point At In The UI

When giving a walkthrough, explicitly point out:

- provider radio
- retrieval mode selector
- reranking toggle
- run mode switch between `Answer` and `Search`
- run metadata expander
- citation expanders with chunk text and metadata

## Good Explanations To Avoid

Do not say:

- "Streamlit is the backend"
- "The model searches the filings directly"
- "The answer is trusted because the prompt says to be grounded"

Say instead:

- Streamlit is the presentation and interaction layer
- retrieval is performed locally against LanceDB
- the answer is checked after generation for JSON structure and citation validity

## If You Need A One-Minute Summary

Use this:

"The Streamlit app is a thin UI over a local SEC-filings RAG pipeline. It restores local retrieval artifacts, optionally prepares a local Ollama runtime, lets the user choose retrieval and answer settings, and then renders either ranked evidence or a citation-grounded final answer. The important engineering choice is that the app itself stays thin while the backend modules keep retrieval, generation, storage, and runtime management separate."
