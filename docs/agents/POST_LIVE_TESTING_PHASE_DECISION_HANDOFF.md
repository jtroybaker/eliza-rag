# Next Session Handoff

## Purpose

Live testing has been completed, and the answer-path bugs found during that testing were fixed.

This handoff is for the next agent after:

- live execution testing
- local Ollama answer-path stabilization
- the fixes captured in `docs/agents/ANSWER_PIPELINE_FIXES.md`

That agent should:

- read the repo state from disk
- absorb the verified live-testing outcomes
- treat the answer pipeline as stabilized unless current repo state shows otherwise
- choose the next bounded phase based on remaining quality and demo-readiness gaps
- update the standard project docs so the repo remains the source of truth

## Start Here

Read these files first:

- `agents.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `docs/agents/IMPLEMENTATION_KANBAN.md`
- `README.md`
- `docs/agents/ANSWER_PIPELINE_FIXES.md`
- `PHASE_05_SESSION_HANDOFF.md`
- `PHASE_05_HANDOFF.md`
- `PHASE_05_CLEANUP_HANDOFF.md`
- `PHASE_05_BACKEND_EXPANSION_HANDOFF.md`
- `PHASE_05_LOCAL_FALLBACK_FOLLOWUP_HANDOFF.md`
- `docs/agents/INDEX_PORTABILITY_HANDOFF.md`
- `LIVE_DEMO_EXECUTION_STEPS.md`

Treat `docs/agents/ANSWER_PIPELINE_FIXES.md` as the authoritative summary of what broke during testing and what was fixed.

If the user provides any final live-test notes beyond that file, use them as the highest-priority new input.

## What Has Already Been Resolved

The following live-testing issues were addressed:

- prompt-template formatting crash from literal JSON braces
- Ollama-compatible response-shape mismatch
- brittle parsing of non-strict JSON from local models
- citation-formatting variance in top-level answers
- hallucinated or unknown citation ids from local models
- redundant default CLI output
- documentation gaps around heuristic query analysis

The answer pipeline now has a repo-supported local Ollama path that uses the native Ollama generate endpoint and more tolerant parsing around local-model output variance.

Do not reopen those fixes unless:

- the current repo state no longer contains them
- new regression evidence appears
- a follow-on design change requires revisiting them

## Current Decision Frame

The main question is no longer "what failed during live testing?"

The main question is:

- is the system now strong enough to lock the demo path, or
- is answer quality still weak enough to justify a bounded retrieval-improvement phase first?

Use that framing unless current repo state shows the live path is still broken.

## How To Choose The Next Phase

Use this order:

1. verify the tested live demo path still works in the current repo state
2. verify whether fresh-clone reviewer flow is dependable, if that was part of testing
3. decide whether the primary remaining risk is answer quality or final demo polish
4. only reopen backend reliability if a real regression is demonstrated

### If the current live path regressed

Examples:

- Ollama path no longer returns parseable grounded output
- hosted backend path now fails
- a fix described in `docs/agents/ANSWER_PIPELINE_FIXES.md` is missing or broken again

Then the next phase should be:

- backend reliability regression cleanup

This is expected to be an exception case, not the default next step.

### If live execution works, but answers are still not good enough

Examples:

- correct companies found, but supporting excerpts are still weak
- comparison questions are still thin or incomplete
- citations are grounded, but the final answer is not persuasive enough for a demo

Then the next phase should be:

- retrieval quality improvement

Most likely first candidate:

- reranking

### If live execution works and answers are acceptable for the intended demo

Then the next phase should be:

- lightweight evaluation and final demo lock

That should include:

- a small representative question set
- documented backend and retrieval mode recommendations
- finalizing the default demo mode
- README and CLI polish only where it improves reviewer clarity

## Selected Next Phase

The project has now chosen:

- Phase 06B: Retrieval Quality

Chosen first candidate within that phase:

- reranking

This means the remaining work should be framed around retrieval-quality improvement before final demo lock.

Phase 06C should now be treated as the follow-on phase after reranking results are in, unless a backend regression appears.

## Recommended Next-Phase Shapes

Pick one of these, not all at once.

### Phase 06A: Backend Reliability Regression Cleanup

Use only if current repo behavior contradicts the fixes already recorded.

Target outcomes:

- restore the broken live path
- add or tighten regression coverage for the failure
- update docs if verified backend behavior changed again

### Phase 06B: Retrieval Quality

Use if live execution is now dependable but answer quality is still the main weakness.

Target outcomes:

- add reranking
- compare lexical vs hybrid vs reranked candidate
- choose the strongest practical demo path

### Phase 06C: Lightweight Evaluation And Demo Lock

Use if the core path is working and reasonably strong already.

Target outcomes:

- create a small representative evaluation set
- document what was tested and what passed
- choose and freeze the final demo configuration
- capture final quality notes and remaining caveats

## Standard Documentation Duties

The next agent should preserve the repo-doc workflow used so far.

Always update:

- `docs/agents/IMPLEMENTATION_KANBAN.md`
  - to reflect the selected next phase or state change

Update when needed:

- `DECISIONS.md`
  - if the default backend, CLI behavior, or demo mode is formally locked
- `LIMITATIONS.md`
  - if evaluation confirms remaining answer-quality caveats
- `README.md`
  - if verified reviewer flow or recommended demo commands changed

Also produce:

- a new bounded phase kickoff file if a new phase starts
- a new handoff file at the end of that work

Do not let important findings live only in chat.

## What The Next Agent Should Avoid

Do not:

- reclassify already-fixed answer-path issues as open problems without new evidence
- reopen the entire architecture without a concrete test-driven reason
- jump into broad optimization without first checking whether the current demo path is already good enough
- claim final demo quality that was not actually demonstrated
- let docs drift away from verified behavior

## Deliverable For The Next Session

The next agent should leave behind:

- a clear statement of which backend and retrieval mode are now recommended
- a clear statement of whether the repo passed a fresh-clone reviewer-flow test
- a clear statement of whether answer quality justified Phase 06B or Phase 06C
- updated project docs
- a bounded kickoff or handoff for the next phase
- no ambiguity about whether the main remaining risk is:
  - retrieval quality
  - reviewer-flow portability
  - final demo polish
  - a demonstrated backend regression
