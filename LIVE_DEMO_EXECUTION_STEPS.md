# Live Demo Execution Steps

## Purpose

Use this file when you want the shortest practical path to test the repo end to end.

The goal is to:

- build the local retrieval state
- run one hosted or local answer backend
- try the likely demo questions
- record what worked and what did not

## 1. Build The Local Retrieval State

Run these first:

```bash
uv sync
uv run eliza-rag-load-chunks
uv run eliza-rag-build-dense-index
```

These commands prepare:

- the lexical LanceDB table
- the dense LanceDB table
- the default hybrid answer path

## Fresh Clone Simulation

If you want to simulate the real reviewer flow, do this from a fresh clone instead of the current working directory.

From the current repo root:

```bash
git init
git add .
git commit -m "snapshot for reviewer-flow test"
cd ..
git clone /home/jtb/repos/eliza-rag eliza-rag-fresh
cd eliza-rag-fresh
```

Then follow the rest of this file from the fresh clone.

Important notes:

- only do this if you are comfortable snapshotting the current workspace state into a local git repo
- the goal is to catch hidden dependencies on untracked local state
- if you want the simulation to reflect the intended reviewer flow, do not manually copy built artifacts into the fresh clone unless the repo is supposed to ship them
- note every place where the README was unclear or where you had to guess

## 2. Pick One Answer Backend

Choose one of the following.

### Option A: OpenAI

```bash
export ELIZA_RAG_LLM_PROVIDER=openai
export ELIZA_RAG_LLM_API_KEY=your_key_here
```

### Option B: OpenRouter

```bash
export ELIZA_RAG_LLM_PROVIDER=openrouter
export ELIZA_RAG_LLM_API_KEY=your_openrouter_key_here
export ELIZA_RAG_LLM_MODEL=openai/gpt-5-mini
```

### Option C: Local Ollama

Install Ollama if needed:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then prepare the local fallback:

```bash
export ELIZA_RAG_LLM_PROVIDER=local_ollama
export ELIZA_RAG_LLM_MODEL=qwen2.5:3b-instruct
uv run eliza-rag-local-llm prepare
uv run eliza-rag-local-llm status
uv run eliza-rag-load-chunks
uv run eliza-rag-build-dense-index
```

## 3. Run One Narrow Smoke Test

Start with this:

```bash
uv run eliza-rag-answer "What risk factors does Apple describe?" --ticker AAPL --mode lexical --top-k 4
```

Check:

- the command succeeds
- the answer includes inline citations like `[C1]`
- the CLI prints a citation block that matches those ids

## 4. Run The Three Likely Demo Questions

Use the current best default:

```bash
uv run eliza-rag-answer "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?" --mode hybrid --top-k 6
uv run eliza-rag-answer "How has NVIDIA's revenue and growth outlook changed over the last two years?" --mode hybrid --top-k 6
uv run eliza-rag-answer "What regulatory risks do the major pharmaceutical companies face, and how are they addressing them?" --mode hybrid --top-k 6
```

## 5. Record The Results

For each run, write down:

- backend used
- question used
- whether the command succeeded
- whether the answer was coherent
- whether the citations looked plausible
- whether the answer covered the requested companies or time periods
- whether uncertainty was stated clearly when coverage was weak

## 6. Watch For These Failure Patterns

If you see these, note them explicitly:

- backend or credential failure
- local Ollama startup failure
- dense-index missing error
- answer is structurally valid but weak or incomplete
- comparison question does not really compare
- right companies found but weak evidence ordering

## 7. Save Your Notes For The Next Session

At minimum, preserve:

- which backend worked best
- which questions looked strong
- which questions looked weak
- whether `hybrid` looked better than `lexical`
- whether reranking now appears necessary
