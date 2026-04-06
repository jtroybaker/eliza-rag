# Phase 07C Kickoff: Provider Experiment Prep

## Purpose

This worker owns the first bounded provider-experiment prep after interface extraction completes.

The goal is to make one alternate embedding provider and one alternate reranker ready to compare against the current baseline, without changing the default path prematurely.

Phase 07B handoff reference: `PHASE_07B_INTERFACE_EXTRACTION_HANDOFF.md`

## Own

- provider selection surface for alternate embedders and rerankers
- one alternate embedding implementation behind the embedder interface
- one alternate reranker implementation behind the reranker interface
- documentation for how to run the baseline vs candidate comparisons

## Do Not Own

- changing the default provider recommendation without eval results
- broad query-routing redesign
- a multi-provider matrix that changes several major components at once

## Recommended Candidates

Start with:

- embedding baseline: current Snowflake path
- embedding candidate: `BAAI/bge-m3`
- reranker baseline: current `bge-reranker-v2-m3`
- reranker candidate: one alternate reranker behind the same interface

Use the current golden evaluation set to compare providers one component at a time.

## Required Outputs

### 1. Provider Selection Surface

Expose enough configuration to choose:

- baseline embedder
- alternate embedder
- baseline reranker
- alternate reranker

Requirements:

- keep defaults unchanged
- keep selection explicit and inspectable

### 2. Alternate Provider Adapters

Implement provider-specific adapters behind the extracted interfaces.

Requirements:

- no hidden default flips
- no behavior changes to the current baseline path when alternate providers are not selected

### 3. Comparison Commands

Document exact commands for:

- current baseline run
- alternate embedding run
- alternate reranker run

## Validation

At minimum, leave behind:

- exact commands used
- any model-download or artifact-build prerequisites
- a concise note on whether the candidate is merely wired in or actually evaluated

## Definition Of Done

This worker is done when:

- the repo can select alternate embedding and reranking providers explicitly
- baseline behavior remains unchanged by default
- the comparison path is documented clearly enough for later evaluation
