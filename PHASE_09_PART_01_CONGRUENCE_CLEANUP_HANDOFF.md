# Phase 09 Part 01 Handoff: Congruence Cleanup For Eval, Judge, And Visualization State

## Outcome

This session part should be treated as a bounded congruence-cleanup pass inside Phase 09.

The goal is not to reopen provider evaluation or start a new phase.

The goal is to make the session-manager and Phase 09 handoff docs accurately match the repo's current evaluation, judging, and visualization surfaces.

## Why This Part Exists

The repo state has moved slightly ahead of the current handoff text.

What is already true in the workspace:

- bounded Phase 09 answer-level evaluation is implemented
- the answer-included baseline artifact exists
- the heuristic answer-judging layer exists
- a separate judge-assisted artifact path exists
- a markdown report path exists
- a plot-based visualization path exists

What is currently inconsistent:

- `PHASE_09_ANSWER_EVAL_AND_VISUALIZATION_HANDOFF.md` still describes answer scoring as only `heuristic_only` and "not judge-assisted"
- that same handoff only mentions the markdown report path, not the plot CLI
- `PHASE_09_SESSION_HANDOFF.md` still frames Phase 09 as upcoming kickoff work rather than a completed bounded pass with follow-up cleanup and comparison work remaining

## Source Of Truth For This Part

Read these first:

1. `agents.md`
2. `IMPLEMENTATION_KANBAN.md`
3. `README.md`
4. `eval/README.md`
5. `PHASE_09_SESSION_HANDOFF.md`
6. `PHASE_09_ANSWER_EVAL_AND_VISUALIZATION_HANDOFF.md`

Then confirm against the actual repo surfaces:

- `pyproject.toml`
- `src/eliza_rag/eval_report_cli.py`
- `src/eliza_rag/eval_plot_cli.py`
- `src/eliza_rag/eval_visualization.py`
- `src/eliza_rag/eval_judging.py`
- `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`
- `eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json`

## Required Outcome

At the end of this part, the docs should make the following current state explicit:

- the raw answer-included baseline artifact exists
- the raw answer artifact remains the evidence source
- the current built-in answer judging layer is still `heuristic_only`
- the repo also supports a separate judge-assisted pass that writes a new artifact rather than mutating the raw one
- the repo has both:
  - a read-only markdown report path
  - a plot-based visualization path
- Phase 09 is complete in bounded form, but follow-up comparison and congruence work still remains

## Scope

Keep this part tightly scoped to:

1. doc congruence
2. handoff accuracy
3. artifact-story clarity

Do not broaden into:

- new provider comparisons
- new judge prompt or rubric design
- release artifact refresh work
- Phase 10 planning beyond a brief note of what remains next

## Concrete Tasks

### 1. Update The Phase 09 Session-Manager Handoff

Revise `PHASE_09_SESSION_HANDOFF.md` so it no longer presents Phase 09 as only a kickoff target.

It should reflect that Phase 09 has already landed in bounded form and that the next immediate work is cleanup plus expanded answer-included comparison coverage.

Preserve these management norms:

- raw eval artifacts are the evidence base
- judged artifacts are an overlay, not the source of truth
- visualization output must remain read-only
- reviewer-facing release artifacts are still separate from local eval outputs

### 2. Update The Phase 09 Answer-Eval Handoff

Revise `PHASE_09_ANSWER_EVAL_AND_VISUALIZATION_HANDOFF.md` so it accurately distinguishes:

- what was measured directly
- what was heuristic-scored
- what was judge-assisted later as a separate artifact
- what was visualized

Minimum corrections:

- do not imply the repo lacks judge-assisted support
- mention the separate judged artifact path
- mention the plot CLI if it remains in repo
- keep the distinction between raw answer artifacts and judged overlays explicit

### 3. Verify Repo Surface Claims

Before closing the part, verify that the docs match the exposed user-facing CLIs:

- `uv run eliza-rag-eval`
- `uv run eliza-rag-eval-report`
- `uv run eliza-rag-eval-plot`
- `uv run eliza-rag-eval-judge`

## Acceptance Criteria

This part is done when:

- `PHASE_09_SESSION_HANDOFF.md` reflects the current bounded-complete Phase 09 state
- `PHASE_09_ANSWER_EVAL_AND_VISUALIZATION_HANDOFF.md` no longer understates the judge and visualization surfaces
- the docs consistently say that raw saved JSON remains the evidence source
- no code-path claims in the updated docs contradict the current CLI or artifact layout

## Suggested Validation

Run a minimal congruence validation slice:

```bash
uv run pytest -q tests/test_eval_reporting.py tests/test_eval_report_cli.py tests/test_eval_judging.py
uv run eliza-rag-eval-report --output /tmp/provider_eval_report_check.md
uv run eliza-rag-eval-plot --output /tmp/provider_eval_visualization_check.png
```

If helpful, also confirm the exposed scripts from `pyproject.toml`.

## Important Notes For The Next Session

- there is already a real judged artifact in repo:
  - `eval/provider_baseline_snowflake_bge_v2_m3_answer_judged.json`
- there is already a real raw answer-included artifact in repo:
  - `eval/provider_baseline_snowflake_bge_v2_m3_answer.json`
- the next substantial engineering slice after this cleanup should be answer-included comparison coverage for the alternate bounded provider paths, not another docs-only pass

## Recommended Next Step After This Part

After the congruence cleanup lands, move to the bounded Phase 09 follow-up:

1. save answer-included alternate artifacts for the existing comparison axes
2. optionally produce separate judged overlays for those new artifacts
3. regenerate read-only report and visualization outputs from the expanded artifact set
