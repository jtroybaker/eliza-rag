# eliza-rag

Portable SEC filings RAG demo: restore a prebuilt local index, ask a question, inspect grounded citations, and discuss the saved evaluation artifacts.

The main demo contract is:

1. clone the repo
2. restore the published LanceDB archive
3. choose a local or hosted LLM
4. run one answer command

## Reviewer Quickstart

Install dependencies:

```bash
uv sync
```

Restore the prebuilt retrieval state from a GitHub Release archive:

```bash
export ELIZA_RAG_LANCEDB_ARCHIVE_URL=https://github.com/YOUR_ORG/YOUR_REPO/releases/download/v1.0.0/lancedb-demo.zip
uv run eliza-rag-storage fetch-archive
```

### Local LLM Path

Install Ollama if needed:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then prepare the local fallback and ask a question:

```bash
export ELIZA_RAG_LLM_PROVIDER=local_ollama
export ELIZA_RAG_LLM_MODEL=qwen2.5:3b-instruct
uv run eliza-rag-local-llm prepare
uv run eliza-rag-answer "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
```

`uv run eliza-rag-local-llm prepare` now warms the local Ollama model and the retrieval-time models used by the recommended demo path, so the first real question is less likely to stall on downloads.

### Hosted LLM Path

If you already have an API key, you can skip Ollama:

```bash
export ELIZA_RAG_LLM_PROVIDER=openai
export ELIZA_RAG_LLM_API_KEY=your_key_here
uv run eliza-rag-answer "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
```

Useful follow-up commands:

```bash
uv run eliza-rag-search "Compare the main risk factors facing Apple and Tesla" --mode targeted_hybrid --top-k 5 --rerank
uv run eliza-rag-answer "How has NVIDIA's revenue and growth outlook changed over the last two years?" --json
```

## What The Project Does

This repo answers business questions over SEC filings with a local retrieval stack and one final answer-generation call.

The current default demo path is:

- deterministic query analysis to detect companies and simple time cues
- targeted hybrid retrieval over a local LanceDB index
- explicit reranking with `bge-reranker-v2-m3`
- one final grounded answer with inline chunk citations

The recommended retrieval mode for named-company comparison prompts is `targeted_hybrid` with reranking enabled, and `eliza-rag-answer` now defaults to that reviewer-facing path.

## Pipeline At A Glance

- Query understanding: lightweight deterministic parsing extracts company aliases, ticker hints, and simple date bounds.
- Embeddings and retrieval: chunk embeddings and lexical search live in local LanceDB tables so the demo can run from a restored archive instead of a fresh rebuild.
- Reranking: top candidates are reranked before the final context pack is built.
- Answer generation: a single LLM call produces the user-facing answer and inline citations.
- Evaluation: the repo keeps saved retrieval, answer, and judged-overlay artifacts so the demo story stays tied to inspectable files rather than transient runs.

For the compact walkthrough version, see `ARCHITECTURE.md`.

## Evaluation Story

The primary discussion artifact is:

- `eval/provider_eval_visualization_judged.png`

Use it as a presentation aid, not as the evidence source.

The intended interpretation is:

- the repo freezes a small evaluation slice in `eval/golden_queries.json`
- retrieval and reranking components vary in bounded ways across saved runs
- raw `*_answer.json` artifacts remain the main answer-behavior evidence
- `*_answer_judged.json` overlays add an interpretation layer on top of those saved answers
- the judged visualization makes tradeoffs easier to discuss live, but it should not be treated as stronger evidence than the raw saved artifacts underneath it

Current judged summary from `eval/provider_eval_report_judged.md`:

- Snowflake + `bge-reranker-v2-m3`: `4 pass / 1 partial_pass / 1 fail`
- `hashed_v1` + `bge-reranker-v2-m3`: `1 pass / 5 partial_pass / 0 fail`
- `hashed_v1` + `bge-reranker-base`: `2 pass / 2 partial_pass / 2 fail`
- Snowflake + `bge-reranker-base`: `2 pass / 3 partial_pass / 1 fail`

The most useful live-demo takeaway is not that one judged score is definitive. It is that the repo preserves raw answers, judged overlays, and read-only reports separately so retrieval and answer tradeoffs can be inspected instead of hand-waved.

## Maintainer Notes

The reviewer path is restore-first. Maintainers can still rebuild or republish artifacts when needed:

```bash
uv run eliza-rag-load-chunks
uv run eliza-rag-build-dense-index
uv run eliza-rag-storage compact --optimize --cleanup-older-than-hours 0 --delete-unverified
uv run eliza-rag-storage package-archive
```

## Further Reading

- `ARCHITECTURE.md`: compact pipeline walkthrough for live explanation
- `eval/README.md`: saved eval artifacts, exact eval commands, and reporting outputs
- `LIMITATIONS.md`: known caveats and interpretation constraints
