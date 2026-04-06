# Phase 07 Session Handoff

## Helper Style

The prior session operated as a technical lead and review-oriented session manager.

What that means in practice:

- used repo docs as the source of truth instead of relying on chat memory
- broke Phase 07 into bounded worker tracks with explicit kickoff files
- reviewed worker output for congruence, not just implementation optimism
- used cleanup work to close CLI, artifact, and documentation mismatches before moving on
- preserved a clear distinction between what is wired, what is validated, and what is still only planned

This should remain the operating style for the next session manager.

## Current Repo State

Phase 07 is effectively complete for its intended scope:

- the golden eval and build-manifest layer exists
- internal provider seams exist
- alternate embedder and reranker selections are wired
- cleanup closed the main congruence gaps between code, docs, and handoff claims

Current source-of-truth docs:

- `agents.md`
- `README.md`
- `HIGH_LEVEL_PLAN.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`

Current Phase 07 docs:

- `PHASE_07_STABILIZATION_AND_MODULARIZATION_KICKOFF.md`
- `PHASE_07A_GOLDEN_EVAL_AND_MANIFEST_KICKOFF.md`
- `PHASE_07A_GOLDEN_EVAL_AND_MANIFEST_HANDOFF.md`
- `PHASE_07B_INTERFACE_EXTRACTION_KICKOFF.md`
- `PHASE_07B_INTERFACE_EXTRACTION_HANDOFF.md`
- `PHASE_07C_PROVIDER_EXPERIMENT_PREP_KICKOFF.md`
- `PHASE_07C_PROVIDER_EXPERIMENT_PREP_HANDOFF.md`
- `PHASE_07_CLEANUP_KICKOFF.md`
- `PHASE_07_CLEANUP_HANDOFF.md`

## What Is Actually Done

Completed and in repo:

- committed golden eval set at `eval/golden_queries.json`
- eval CLI at `uv run eliza-rag-eval`
- build manifest at `artifacts/build_manifest.json`
- saved baseline eval output at `eval/baseline_targeted_hybrid_retrieval.json`
- explicit internal interfaces for:
  - `Embedder`
  - `Reranker`
  - `QueryAnalyzer`
  - `Retriever`
  - `AnswerBackend`
- named embedder selections:
  - `snowflake-arctic-embed-xs`
  - `bge-m3`
  - `hashed_v1`
- named reranker selections:
  - `bge-reranker-v2-m3`
  - `bge-reranker-base`
  - `heuristic`
- eval, retrieval, and answer CLIs now expose the same reranker selection surface
- answer backend typing now uses the shared interface cleanly

## Important Current Truths

These are the details the next manager should keep straight:

- the recommended retrieval path for named-company comparison prompts is still `targeted_hybrid + bge-reranker-v2-m3`
- the code/config default dense path is Snowflake
- the committed local dense artifact snapshot still reports `hashed_v1`
- the current baseline eval artifact therefore reflects the committed local artifact contract, not a Snowflake rebuild
- Phase 07 wired provider comparisons; it did not yet prove that the alternate providers are better
- eval scoring is still shallow:
  - ticker coverage and comparison placeholders exist
  - broader contamination, citation quality, and answer-usefulness scoring still need work

## Recommended Immediate Next Step

Run bounded provider experiments against the committed golden eval set before changing any defaults.

Use a one-variable-at-a-time comparison order:

1. baseline embedder + baseline reranker
2. alternate embedder + baseline reranker
3. baseline embedder + alternate reranker

Only after those runs:

- decide whether the committed local dense artifact snapshot should be rebuilt with Snowflake
- decide whether any provider recommendation should change

This next bounded step should be treated as Phase 08 rather than as more open-ended Phase 07 follow-on work:

- provider evaluation should now produce saved evidence, not just wiring
- eval scoring should be hardened enough to support later default-change decisions

## Session Manager Priorities

1. Keep the experiment scope narrow.
2. Preserve the current demo recommendation until eval artifacts justify a change.
3. Make workers save exact commands and outputs for every provider comparison run.
4. Keep artifact-state truth explicit:
   - config default
   - committed local artifact baseline
   - experiment artifact outputs
5. Do not let handoff docs claim quality wins that were only wiring wins.

## Risks To Watch

- Confusing code defaults with committed artifact state.
- Treating a provider as "better" because it is wired, not because the eval shows it.
- Over-reading ticker coverage alone as proof of better end-to-end answer quality.
- Letting experiment outputs drift without updating the build manifest or saved eval artifacts.
- Reopening broad modularization work before the current provider comparisons are finished.

## Recommended Read Order For Next Manager

1. `agents.md`
2. `IMPLEMENTATION_KANBAN.md`
3. `README.md`
4. `DECISIONS.md`
5. `LIMITATIONS.md`
6. `PHASE_07A_GOLDEN_EVAL_AND_MANIFEST_HANDOFF.md`
7. `PHASE_07B_INTERFACE_EXTRACTION_HANDOFF.md`
8. `PHASE_07C_PROVIDER_EXPERIMENT_PREP_HANDOFF.md`
9. `PHASE_07_CLEANUP_HANDOFF.md`

## Working Norms To Preserve

- keep work bounded and evidence-driven
- use the golden eval set and saved artifacts as the regression contract
- update `IMPLEMENTATION_KANBAN.md` when state changes
- update `DECISIONS.md` only when a real decision changes
- update `LIMITATIONS.md` when experiments expose new caveats
- prefer exact commands and saved artifacts over narrative-only progress reports
