# Phase 09 Kickoff: Answer-Level Evaluation And Artifact-Driven Visualization

## Purpose

Phase 09 is the next bounded engineering phase for the project.

Phase 08 converted the eval runner from placeholder scoring into a stronger retrieval-quality contract and produced saved provider comparison artifacts.

What the repo still does not have is a credible answer-quality layer that can support stronger claims about:

- groundedness
- citation quality
- comparison completeness
- practical usefulness

The repo also does not yet have a compact visualization layer that makes the saved evidence easier to inspect without turning local experiment state into the new source of truth.

Phase 09 should close those two gaps without reopening broad retrieval or provider work.

## Why Phase 09 Was Chosen

The next meaningful uncertainty is no longer "can we save retrieval evidence?"

The next uncertainties are:

- whether answer generation remains strong when retrieval looks good
- whether answer quality can be judged consistently enough to support later recommendation changes
- whether later review can happen from saved eval artifacts instead of ad hoc local inspection

This phase should therefore focus on answer-level judging plus artifact-driven visualization.

## Read First

Before changing code, read:

- `agents.md`
- `README.md`
- `IMPLEMENTATION_KANBAN.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `PHASE_08_PROVIDER_EVALUATION_AND_SCORING_HANDOFF.md`
- `eval/README.md`
- the saved provider artifacts in `eval/`

Use the saved eval artifacts as the evidence base rather than chat memory or local transient tables.

## Phase Goal

Add a bounded answer-level evaluation path and a small visualization layer that both operate on saved eval artifacts.

## Target Outcomes

- save answer-included eval artifacts for the current recommended provider path
- add a bounded answer-quality judging layer with explicit structured outputs
- keep retrieval-level and answer-level scoring clearly separated in the artifact format
- generate a simple visualization or summary view directly from saved `eval/*.json` files
- keep the visualization layer read-only with respect to retrieval state

## Scope For Phase 09

Keep this phase tightly scoped to:

1. answer-included eval runs
2. structured answer-level judging
3. artifact-driven visualization or reporting

Do not broaden into:

- new provider swaps
- a broad UI or dashboard rewrite
- replacing the saved JSON artifacts with a database-backed analytics layer
- changing the current reviewer-facing release artifact story
- using visualizations as a substitute for saved raw evidence

## Required Outputs

### 1. Answer-Included Eval Artifacts

Run and save at least one answer-included eval artifact for the current recommended path:

- `targeted_hybrid`
- Snowflake dense artifact
- `bge-reranker-v2-m3`

If cost remains bounded, optionally save one comparison answer-included artifact for a weaker or alternate path.

For each saved answer-included run, preserve:

- exact command used
- output artifact path
- manifest linkage
- whether answer judging was heuristic-only or judge-assisted

### 2. Structured Answer-Level Judging

Add a bounded judging layer that records answer-level outcomes explicitly.

Preferred judged dimensions:

- groundedness
- citation quality
- usefulness
- comparison completeness when relevant
- uncertainty handling when relevant

Requirements:

- keep the output structured and machine-readable
- preserve the underlying answer text and citations in the eval artifact
- make it obvious when a field is judged versus not evaluated
- avoid collapsing retrieval quality and answer quality into one opaque number

If a judge model is used:

- keep the rubric narrow and stable
- save the rubric or prompt used
- treat judge results as a scored layer over saved artifacts, not as hidden transient state

### 3. Artifact-Driven Visualization

Add a small visualization or reporting path built directly from saved `eval/*.json` artifacts.

Acceptable forms:

- a CLI summary report
- a small static HTML view
- a notebook-free generated artifact committed to the repo

Requirements:

- the visualization must read saved eval artifacts rather than query LanceDB directly
- the visualization must keep retrieval-level and answer-level outcomes distinguishable
- the visualization should make it easy to compare provider runs and spot failure clusters

Good initial views:

- per-run summary counts
- per-query outcome matrix
- contamination hotspots
- answer-quality status by query
- side-by-side baseline versus candidate comparisons

## Suggested Execution Order

1. confirm the current recommended baseline provider path and artifact names
2. save one answer-included eval artifact for that path
3. add structured answer-level judging fields and tests
4. save or backfill judged output for the answer-included artifact
5. build a simple visualization or summary layer over the saved `eval/*.json` files
6. update docs so the visualization is clearly described as a view over saved artifacts, not as the evidence source itself

## Decision Rules To Preserve

- do not treat retrieval-only wins as answer-quality wins
- do not treat visualization output as stronger evidence than the underlying saved JSON
- do not recommend a provider change based only on judge output without preserving the raw run artifact
- do not refresh the reviewer-facing release artifact baseline in this phase unless that work is explicitly taken on and documented

## Documentation Updates Required

At the end of Phase 09:

- update `IMPLEMENTATION_KANBAN.md`
- update `README.md`
- update `LIMITATIONS.md` with any judge-model or visualization caveats
- update `DECISIONS.md` only if a real evaluation-policy or recommendation decision changes
- write a Phase 09 handoff that separates:
  - what was measured directly
  - what was judge-scored
  - what was visualized
  - what remains provisional

## Definition Of Done

Phase 09 is done when:

- the repo has at least one saved answer-included eval artifact for the current recommended path
- answer-level scoring is structured enough to support bounded quality discussions
- a simple visualization or reporting layer reads directly from saved eval artifacts
- the docs keep raw evidence, judged interpretation, and visualization output clearly separated
