# Phase 08 Kickoff: Evidence-Driven Provider Evaluation And Scoring Hardening

## Purpose

Phase 08 is the next bounded engineering phase for the project.

Phase 07 established the infrastructure needed to make later quality decisions safely:

- a committed golden eval set
- a saved baseline eval artifact
- a build manifest
- explicit provider seams
- explicit alternate embedder and reranker selections

What Phase 07 did not do is prove that any alternate provider should replace the current recommendation.

Phase 08 should convert that prepared experiment surface into decision-quality evidence without reopening broad architecture work.

## Why Phase 08 Was Chosen

The main repo risk is no longer missing retrieval plumbing.

The main repo risks are now:

- changing defaults without saved evidence
- confusing wiring wins with quality wins
- over-reading ticker coverage without judging contamination, citations, or answer usefulness
- letting artifact-state truth drift away from the documented baseline

The next bounded step should therefore be narrow provider evaluation plus stronger scoring.

## Read First

Before changing code, read:

- `agents.md`
- `README.md`
- `IMPLEMENTATION_KANBAN.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `PHASE_07_SESSION_HANDOFF.md`
- `PHASE_07A_GOLDEN_EVAL_AND_MANIFEST_HANDOFF.md`
- `PHASE_07C_PROVIDER_EXPERIMENT_PREP_HANDOFF.md`
- `PHASE_07_CLEANUP_HANDOFF.md`
- `eval/README.md`

Use the repo docs and saved artifacts as the source of truth instead of chat memory.

## Phase Goal

Run bounded one-variable-at-a-time provider comparisons against the committed golden eval set, then strengthen the eval scoring so later default changes can be justified.

## Target Outcomes

- save a baseline provider run artifact that reflects the current recommended path
- save an alternate-embedder-only comparison artifact
- save an alternate-reranker-only comparison artifact
- document the exact commands and manifest linkage for every saved run
- extend scoring beyond ticker-coverage placeholders
- decide whether the committed local dense artifact baseline should remain `hashed_v1` or be refreshed to Snowflake after the evidence is in

## Scope For Phase 08

Keep this phase tightly scoped to:

1. provider comparison evidence
2. scoring hardening
3. artifact and documentation congruence driven by those results

Do not broaden into:

- another modularization phase
- a broad query-routing redesign
- multiple provider swaps in a single comparison run
- answer-pipeline rewrites that make provider results harder to interpret

## Required Outputs

### 1. Saved Comparison Artifacts

Run and save at least these bounded comparisons:

1. baseline embedder + baseline reranker
2. alternate embedder + baseline reranker
3. baseline embedder + alternate reranker

For each run, save:

- exact command used
- output artifact path
- manifest linkage
- a short interpretation grounded in the saved artifact

### 2. Stronger Scoring

Extend the eval contract so it can judge more than ticker coverage.

Minimum scoring additions:

- contamination observations
- citation-quality observations when answers are included
- answer-usefulness observations when answers are included
- clearer pass/fail or partial-pass semantics

The scoring layer does not need to become a large benchmark framework. It only needs to become strong enough to support bounded provider decisions.

### 3. Dense Artifact Baseline Decision

After the comparison artifacts exist:

- decide whether the committed local dense artifact snapshot should remain the current `hashed_v1` baseline
- or decide whether the repo should refresh the saved local baseline to Snowflake

Do not make that change before the comparison evidence exists.

## Suggested Execution Order

1. confirm the current baseline command and artifact naming
2. run and save the baseline provider comparison artifact
3. run and save the alternate-embedder comparison artifact
4. run and save the alternate-reranker comparison artifact
5. strengthen scoring using the saved artifacts as the target contract
6. update repo docs to reflect the evidence, not just the wiring surface

## Documentation Updates Required

At the end of Phase 08:

- update `IMPLEMENTATION_KANBAN.md`
- update `README.md`
- update `LIMITATIONS.md` if new caveats appear
- update `DECISIONS.md` only if a real default or recommendation changes
- write a Phase 08 handoff that distinguishes:
  - what was measured
  - what changed
  - what still remains provisional

## Definition Of Done

Phase 08 is done when:

- the repo has saved one-variable-at-a-time provider comparison artifacts
- the eval runner has stronger scoring than today’s placeholder contract
- docs clearly distinguish baseline evidence from unproven provider options
- any recommendation or default change is backed by saved eval output rather than by wiring alone
