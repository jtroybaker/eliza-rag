# Quality Notes

## Demo Path

- default end-to-end demo path uses `hybrid` retrieval with `ELIZA_RAG_ANSWER_TOP_K=6`
- lexical retrieval remains available as the fallback baseline if the dense index is unavailable

## Example Questions Tried

- `What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?`
- `How has NVIDIA's revenue and growth outlook changed over the last two years?`
- `What regulatory risks do the major pharmaceutical companies face, and how are they addressing them?`

## What Was Checked

- retrieval output includes chunk metadata needed for traceable citations
- final prompt injects retrieved filing context and requires evidence-bound JSON output
- parser now enforces inline citation ids in the top-level `answer`, not only in `findings`
- the answer pipeline performs retrieval before one final answer-generation API call
- backend selection is explicit via `ELIZA_RAG_LLM_PROVIDER`, `ELIZA_RAG_LLM_BASE_URL`, `ELIZA_RAG_LLM_API_KEY`, and `ELIZA_RAG_LLM_MODEL`
- provider resolution now includes `openrouter` and `local_ollama`
- the repo-supported Ollama workflow covers installed/runtime/model-ready checks through `eliza-rag-local-llm`
- terminal output remains readable while full JSON output is available with `--json`

## Current Weaknesses

- dense retrieval still depends on a deterministic hashed embedding baseline, so hybrid is more defensible than dense-only
- no reranker is active yet, so some comparison questions may surface the right filings with suboptimal chunk ordering
- query analysis is deterministic and heuristic rather than model-based, so inferred year bounds or expansion terms can be fallible on ambiguous questions
- answer quality is sensitive to the top retrieved chunks because the final prompt intentionally avoids multi-step repair loops
- live backend verification is still environment-dependent; the committed test suite is deterministic and mocked rather than a live OpenAI, OpenRouter, or full local-answer round-trip
- local Ollama mode is operationally safer than before, but it still depends on an existing Ollama install and any required model downloads

## Why The Current Demo Path Is Defensible

- it satisfies the assignment constraint of exactly one final LLM API call
- it preserves transparent grounding through enforced inline citation ids, structured findings citations, and retrieval metadata
- it keeps the reviewer flow simple: build indices, pick a backend, run one command, inspect citations
