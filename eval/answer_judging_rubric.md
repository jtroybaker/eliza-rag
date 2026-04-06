# Answer Judging Rubric

This rubric defines the bounded answer-level scoring layer for Phase 09.

Method:

- `heuristic_only`
- no external judge model
- saved answer text and citations remain the evidence source

Judge-assisted method now also supported:

- `llm_judge_openrouter`
- default hosted judge model: `qwen/qwen3.6-plus:free`
- runs over saved answer-included eval artifacts and writes a separate judged artifact

Rubric version:

- `phase_09_answer_eval_v1`

Dimensions:

- `groundedness`
  - `pass`: answer text preserves inspectable inline citations and the cited evidence covers the expected tickers
  - `partial_pass`: citations exist but expected ticker coverage is incomplete
  - `fail`: inline grounding is missing or unusable
- `citation_quality`
  - `pass`: cited evidence covers all expected tickers
  - `partial_pass`: some citation coverage exists but is incomplete
  - `fail`: no usable inline citation trail exists
- `usefulness`
  - `pass`: answer includes a summary, findings, and usable grounded coverage
  - `partial_pass`: answer is usable but comparison coverage is incomplete
  - `fail`: answer is empty or materially incomplete
- `comparison_completeness`
  - `not_applicable`: non-comparison query
  - `pass`: answer covers all expected comparison entities
  - `partial_pass`: answer covers multiple entities but not all expected ones
  - `fail`: answer collapses the comparison materially
- `uncertainty_handling`
  - `pass`: uncertainty field is present and inspectable
  - `partial_pass`: uncertainty field is present but thin
  - `fail`: uncertainty field is absent

Interpretation:

- retrieval-level scoring and answer-level scoring are intentionally separate
- the saved JSON artifact remains the source of truth
- this rubric is a bounded heuristic layer, not a claim of human-equivalent judgment
