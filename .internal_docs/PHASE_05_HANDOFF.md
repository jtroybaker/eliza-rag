# Phase 05 Handoff

## Status

Phase 05 answer generation is now cleaned up and tightened for handoff:

- a final prompt template now exists in-repo
- the repo now has a single-call answer-generation pipeline
- a reviewer-usable `eliza-rag-answer` CLI command is available
- answers carry chunk-level citation ids that map back to retrieval metadata
- the top-level `answer` now fails fast if it omits valid inline citation ids
- answer backend configuration is now explicit for hosted OpenAI and OpenAI-compatible servers
- prompt iteration and lightweight quality notes are now documented

## What Was Implemented

Key files:

- `src/eliza_rag/answer_generation.py`
- `src/eliza_rag/answer_cli.py`
- `src/eliza_rag/config.py`
- `src/eliza_rag/models.py`
- `tests/test_answer_generation.py`
- `prompts/final_answer_prompt.txt`
- `PROMPT_ITERATION_LOG.md`
- `QUALITY_NOTES.md`
- `README.md`

## Delivered Behavior

- the end-to-end pipeline accepts a natural-language question
- retrieval runs first using the existing retrieval module
- retrieved chunks are formatted into a saved final prompt template
- exactly one final hosted or OpenAI-compatible Responses API call generates the user-facing answer
- the command returns a structured answer with summary, findings, uncertainty, and citation metadata

## Demo Commands

Primary answer-generation path:

```bash
uv run eliza-rag-answer "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
```

Machine-readable output:

```bash
uv run eliza-rag-answer "How has NVIDIA's revenue and growth outlook changed over the last two years?" --json
```

## Known Limitations

- the final answer path now depends on `ELIZA_RAG_LLM_PROVIDER`, `ELIZA_RAG_LLM_BASE_URL`, `ELIZA_RAG_LLM_API_KEY`, and `ELIZA_RAG_LLM_MODEL`
- local-compatible mode assumes an OpenAI-style `/v1/responses` server that returns `output_text`
- the CLI intentionally does not retry invalid model output because the assignment requires one final answer-generation call
- hybrid retrieval is the best current default because dense embeddings are still baseline-only and no reranker is active yet

## Recommended Phase 06 Start

Next work should focus on:

- reranking the hybrid candidate pool before prompt assembly
- lightweight evaluation comparisons across `lexical` and `hybrid` on assignment-style questions
- live smoke verification against one hosted backend and one user-provided OpenAI-compatible local/server backend
- final reviewer polish around prompt visibility and failure messages
