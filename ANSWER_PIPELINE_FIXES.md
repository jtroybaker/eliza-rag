# Answer Pipeline Fixes

This note captures the fixes applied during iterative live testing of `eliza-rag-answer`, especially against the local Ollama path.

## 1. Prompt Template Formatting Crash

Observed failure:

- `KeyError: '\n  "summary"'`

Cause:

- the final prompt template included a literal JSON example
- Python `str.format()` treated those braces as template fields instead of plain text

Fix:

- replaced generic `template.format(...)` with explicit replacement of only `{question}` and `{context}`
- added a regression test using a brace-heavy prompt template

Effect:

- prompt construction no longer crashes when the template includes literal JSON

## 2. Ollama-Compatible Response Shape Mismatch

Observed failure:

- `Repo-managed local Ollama backend returned an incompatible response shape: missing output_text`

Cause:

- the original backend client assumed OpenAI-style `/v1/responses` payloads with `output_text`
- Ollama compatibility can return content in other shapes

Initial fix:

- added fallback parsing for compatible response payloads such as `output[].content[].text` and `message.content`

Follow-on fix:

- moved `local_ollama` to Ollama's native `/api/generate` endpoint with `format: "json"`

Effect:

- the repo-supported local path now asks Ollama for explicit JSON instead of relying on prompt obedience alone

## 3. Non-Strict JSON Returned By Local Models

Observed failure:

- `Model response was not valid JSON. The final prompt expects a strict JSON object.`

Cause:

- local models sometimes wrapped the JSON in prose or code fences

Fix:

- made response parsing accept:
  - strict JSON
  - fenced ```json blocks
  - prose-wrapped output containing a leading JSON object

Effect:

- the parser became tolerant of common local-model formatting noise while still requiring a JSON object

## 4. Citation Formatting Variance In The Top-Level Answer

Observed failures:

- `Model response answer must include inline citation ids such as [C1].`

Cause:

- local model answers sometimes used:
  - `(C1, C2)`
  - `[C1, C2]`
  - no inline answer citations at all, even when findings had valid citations

Fixes:

- normalized parenthetical citation groups into `[C1] [C2]`
- normalized bracketed grouped citations into `[C1] [C2]`
- if the answer text had no valid inline citations but findings did, appended known finding citations to the answer

Effect:

- valid grounded answers are no longer rejected just because the local model used slightly different citation formatting

## 5. Unknown Citation Ids From The Local Model

Observed failure:

- `Model response referenced unknown citation ids: C5`

Cause:

- the local model occasionally hallucinated citation ids outside the retrieved set

Fix:

- for findings, kept only citation ids that exist in the retrieved citation set
- for the top-level answer, stripped unknown inline citations
- failed only if no grounded finding remained after filtering

Effect:

- the answer path now tolerates local-model citation overreach without accepting fully ungrounded output

## 6. CLI Output Was Too Redundant

Observed issue:

- the terminal output showed `summary`, `answer`, and `findings` together by default
- for human users, those sections were often overlapping and noisy

Fix:

- simplified the default CLI output to:
  - `Answer`
  - `Citations`
- added `--verbose` to expose the richer terminal view
- kept `--json` unchanged for machine-readable structured output
- documented the decision in `DECISIONS.md`

Effect:

- default terminal UX is now simpler, while structured detail remains available when needed

## 7. Documentation Clarification On Query Analysis

Observed concern:

- the repo has lightweight query analysis, but it is heuristic rather than model-based

Fix:

- documented in `README.md` and `QUALITY_NOTES.md` that:
  - query analysis is deterministic
  - year/date inference can be fallible
  - lexical mode still mostly uses the raw question text for FTS

Effect:

- reviewers get a more accurate picture of what the retrieval layer actually does

## Result

The answer pipeline now:

- builds prompts safely with literal JSON templates
- supports hosted backends plus a stable repo-supported local Ollama path
- tolerates common local-model JSON and citation-formatting variance
- keeps grounding requirements while being less brittle
- presents a simpler default CLI UX
