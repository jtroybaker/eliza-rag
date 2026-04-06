# Phase 07 Kickoff: Stabilization, Evaluation Harness, And Modular Provider Boundaries

## Purpose

Phase 07 is the next bounded engineering phase for the project.

The repo now has a credible demo path:

- a reviewer-safe release-archive restore flow
- `targeted_hybrid` retrieval for named-company comparison prompts
- explicit reranking support
- a single-call grounded answer path

The next risk is not missing baseline capability. The next risk is regressing a working demo while making the codebase more modular and more open to provider swaps.

This phase should therefore stabilize first, then modularize behind measurable interfaces.

## Why Phase 07 Was Chosen

Phase 06C narrowed the main multi-company retrieval blocker enough to move out of bounded retrieval triage.

Current interpretation:

- the current path is strong enough to preserve as a baseline
- the repo now needs a small golden evaluation set and artifact traceability
- provider swaps should happen behind explicit interfaces rather than through more orchestration churn

## Read First

Before changing code, read:

- `agents.md`
- `README.md`
- `DECISIONS.md`
- `LIMITATIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `HIGH_LEVEL_PLAN.md`
- `PHASE_06C_COMPANY_DETECTION_FOLLOWUP_RESULTS_HANDOFF.md`

Use repo files as the source of truth rather than prior chat context.

## Phase Goal

Freeze the current demo path with a small evaluation harness and a build manifest, then extract clean provider boundaries so alternate embedding and reranking models can be tested safely.

## Target Outcomes

- create a committed golden evaluation set with explicit coverage and contamination expectations
- emit a build manifest that ties chunking, embedding, reranker, and artifact state together
- add an evaluation runner that saves structured outputs for baseline and candidate runs
- extract explicit interfaces for:
  - embedder
  - reranker
  - query analyzer
  - retriever
  - answer backend
- keep deterministic query analysis as the default while testing alternate providers one component at a time

## Scope For Phase 07

Keep this phase tightly scoped to:

1. baseline preservation
2. artifact traceability
3. interface extraction
4. bounded provider experimentation prep

Do not broaden into:

- a large UI rewrite
- a generalized agentic planner
- a broad learned-routing phase
- multiple simultaneous provider swaps without baseline comparisons

## Required Outputs

### 1. Golden Evaluation Set

Create a small committed evaluation artifact with:

- representative single-company questions
- representative comparison questions
- known alias-sensitive questions
- one or two ambiguous questions that should surface uncertainty

Each record should include at least:

- query text
- expected companies or tickers
- whether comparison behavior is required
- unacceptable contamination rules where clear

### 2. Build Manifest

Create a manifest artifact that records:

- chunking settings
- lexical and dense artifact names
- embedding model identity
- reranker identity
- table names
- creation timestamp or version marker

The manifest should travel with release-oriented retrieval artifacts.

### 3. Evaluation Runner

Add a bounded evaluation path that records:

- query
- config used
- retrieved entities
- final answer output when applicable
- citations and chunk ids

This does not need to be a large benchmark system. It only needs to be strong enough to catch regressions during modularization.

### 4. Interface Extraction

Extract explicit internal interfaces for:

- embedder
- reranker
- query analyzer
- retriever
- answer backend

Requirements:

- keep current CLI behavior stable
- keep the current implementations as defaults first
- do not combine interface extraction with multiple provider swaps in the same change set

Status:

- implemented in Phase 07B
- handoff summary: `PHASE_07B_INTERFACE_EXTRACTION_HANDOFF.md`

### 5. Provider Experiment Prep

Prepare the repo for bounded experiments on:

- one alternate embedding provider
- one alternate reranker

Keep deterministic query analysis as the default unless the evaluation harness later proves it is the leading bottleneck.

## Suggested Execution Order

1. commit the golden eval artifact shape
2. add build manifest generation
3. add eval-runner output shape
4. extract the embedder interface
5. extract the reranker interface
6. extract the remaining interfaces without changing CLI behavior

Current progress:

- steps 1 through 6 are complete across Phase 07A and Phase 07B
- the next phase should focus on bounded provider experiments rather than more interface churn
7. add one alternate embedding provider
8. add one alternate reranker

## Documentation Updates Required

At the end of Phase 07:

- update `IMPLEMENTATION_KANBAN.md`
- update `DECISIONS.md` if interface or provider decisions change
- update `LIMITATIONS.md` if modularization reveals new risks
- update `README.md` if evaluation or provider configuration becomes reviewer-visible
- write a results handoff summarizing what was extracted and what was only prepared

## Definition Of Done

Phase 07 is done when:

- the repo has a committed golden evaluation artifact
- the repo emits a build manifest for retrieval artifacts
- the repo can run a bounded saved evaluation over the current baseline
- the main provider seams are explicit and current behavior is preserved
- at least one alternate provider path is ready to evaluate without destabilizing the baseline
