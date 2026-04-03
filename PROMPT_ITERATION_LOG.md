# Prompt Iteration Log

## Version 1

What changed:

- introduced a single final prompt template saved at `prompts/final_answer_prompt.txt`
- forced the model to return one JSON object with `summary`, `answer`, `findings`, and `uncertainty`
- added explicit citation-id requirements tied to retrieved chunks labeled `C1`, `C2`, and so on
- added a hard rule to answer only from provided filing evidence

Why:

- Phase 05 needs an inspectable prompt that is easy to explain in a live demo
- JSON output makes the CLI and tests deterministic enough for a small local demo
- explicit uncertainty behavior reduces the risk of unsupported claims when retrieval coverage is partial
- chunk-level citation ids preserve a direct path back to retrieval metadata and filing provenance

## Current tradeoff

- the prompt is intentionally strict and compact rather than heavily optimized for prose quality
- if the model returns invalid JSON, the command fails instead of making a second answer call
- this is deliberate so the final answer path remains exactly one LLM API call
