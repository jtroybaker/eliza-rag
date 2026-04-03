# Final Evaluation And Demo-Lock Preparation

## Purpose

Use this file to run the final lightweight evaluation and reviewer-flow simulation from a fresh clone.

The goal is to answer four questions:

1. can a reviewer clone the repo and get to a working demo path without hidden local state
2. does the recommended retrieval mode now behave well enough on the key comparison prompts
3. which backend should be treated as the preferred demo backend
4. is the repo ready for final demo lock, or does it still need one more fix

## Before You Start

Important:

- a normal `git clone` only includes committed state
- if your current working tree has uncommitted changes that you want included in the simulation, commit them first on a temporary branch before cloning
- do not manually copy built artifacts into the fresh clone unless the repo is explicitly supposed to ship them

Recommended prep in the current repo:

```bash
git status
git add -A
git commit -m "snapshot for final evaluation"
```

If you do not want to commit yet, stop here and decide how you want to snapshot the exact state you intend to test.

## 1. Create A Fresh Clone

From outside the repo:

```bash
cd /tmp
rm -rf eliza-rag-final-eval
git clone /home/jtb/repos/eliza-rag eliza-rag-final-eval
cd eliza-rag-final-eval
git rev-parse HEAD
```

Write down:

- clone path
- commit hash tested
- date/time of the run

## 2. Record The Environment

Before installing anything, capture:

```bash
python3 --version
uv --version
uname -a
```

If using a hosted backend, also note:

- backend provider
- model name

If using local Ollama, also note:

- whether Ollama was already installed
- model selected
- whether the model had to be downloaded during the run

## 3. Run The Reviewer Setup Exactly From The Clone

Core retrieval build:

```bash
uv sync
uv run eliza-rag-load-chunks
uv run eliza-rag-build-dense-index
```

Record:

- whether each command succeeded on the first try
- runtime duration if any step felt unusually slow
- whether README instructions were sufficient without guessing

## 4. Choose One Demo Backend

Pick one primary backend for the final evaluation pass.

### Option A: Local Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
export ELIZA_RAG_LLM_PROVIDER=local_ollama
export ELIZA_RAG_LLM_MODEL=qwen2.5:3b-instruct
uv run eliza-rag-local-llm prepare
uv run eliza-rag-local-llm status
```

Use this if you want the most reviewer-portable local story.

### Option B: OpenAI

```bash
export ELIZA_RAG_LLM_PROVIDER=openai
export ELIZA_RAG_LLM_API_KEY=your_key_here
```

Use this if you want the cleanest high-quality final answer check.

### Option C: OpenRouter

```bash
export ELIZA_RAG_LLM_PROVIDER=openrouter
export ELIZA_RAG_LLM_API_KEY=your_openrouter_key_here
export ELIZA_RAG_LLM_MODEL=openai/gpt-5-mini
```

Use this if OpenRouter is your intended hosted fallback.

## 5. Confirm The Retrieval Recommendation Before Running Answers

The current recommended retrieval path for named-company comparisons is:

- `--mode targeted_hybrid`
- `--rerank`
- reranker `bge-reranker-v2-m3`

Run these retrieval-only checks first:

```bash
uv run eliza-rag-search "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?" --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
uv run eliza-rag-search "Compare the main risk factors facing Apple and Tesla." --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
uv run eliza-rag-search "What are the primary risk factors facing JPMorgan and Bank of America, and how do they compare?" --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
```

For each run, record:

- whether all named companies appear in final top-k
- whether unrelated-company contamination is still visible
- whether the result looks good enough to support the final answer step

## 6. Run A Narrow Answer Smoke Test

Start with one simpler question:

```bash
uv run eliza-rag-answer "What risk factors does Apple describe?" --ticker AAPL --mode lexical --top-k 4
```

Check:

- command succeeds
- answer contains inline citations like `[C1]`
- citation block matches those ids
- answer is coherent and grounded

## 7. Run The Final Evaluation Question Set

Run at least these four questions.

### A. Main named-company comparison

```bash
uv run eliza-rag-answer "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?" --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
```

### B. Narrower named-company comparison

```bash
uv run eliza-rag-answer "Compare the main risk factors facing Apple and Tesla." --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
```

### C. Financial-company comparison

```bash
uv run eliza-rag-answer "What are the primary risk factors facing JPMorgan and Bank of America, and how do they compare?" --mode targeted_hybrid --top-k 8 --rerank --reranker bge-reranker-v2-m3 --rerank-candidate-pool 12
```

### D. One non-comparison sanity check

Use one of these:

```bash
uv run eliza-rag-answer "How has NVIDIA's revenue and growth outlook changed over the last two years?" --mode hybrid --top-k 6 --rerank
```

or

```bash
uv run eliza-rag-answer "What regulatory risks do the major pharmaceutical companies face, and how are they addressing them?" --mode hybrid --top-k 6 --rerank
```

## 8. Score Each Run

For each answer, record:

- backend used
- command used
- success or failure
- whether the answer covered all requested companies or entities
- whether the comparison was explicit rather than just a list
- whether the citations looked plausible
- whether uncertainty was stated clearly where evidence was weak
- whether you would be comfortable showing that output in a live demo

Simple scoring suggestion:

- `pass`: demo-acceptable as is
- `borderline`: usable but visibly weak
- `fail`: not suitable for demo

## 9. Watch For These Failure Patterns

Note them explicitly if they appear:

- setup step required undocumented guesswork
- fresh clone depended on hidden machine state beyond documented prerequisites
- local Ollama failed to prepare or start
- dense or lexical artifacts were unexpectedly missing after the documented build
- `targeted_hybrid` retrieval looked good but answer generation still dropped a named company
- answer cited chunks but did not really compare the companies
- non-comparison questions regressed under the current defaults

## 10. Make The Demo-Lock Decision

Use this rule:

- lock the demo path only if the fresh-clone setup was straightforward and the main evaluation questions are at least mostly `pass` with no major blocker
- if the clone flow works but one question is still merely `borderline`, decide whether that question should be removed from the live demo set or whether one more bounded fix is justified
- do not lock the demo path if the fresh-clone flow is confusing or if the main Apple/Tesla/JPMorgan comparison is still weak in answer mode

## 11. Preserve Notes For The Repo

At minimum, write down:

- clone commit tested
- backend used
- exact commands run
- which retrieval mode should be the recommended demo default
- whether the repo passed a fresh-clone reviewer-flow test
- which questions were `pass`, `borderline`, or `fail`
- whether the project is ready for final demo lock
- any README or CLI confusion you had during the run

## Likely Outcomes

If the run is strong:

- update the repo docs to lock the recommended demo path
- create a final evaluation or demo-lock handoff

If the run is mixed:

- keep the notes precise
- decide whether the weakness is acceptable demo risk or one final bounded fix

If the fresh-clone flow itself is weak:

- fix reviewer ergonomics before claiming final demo readiness
