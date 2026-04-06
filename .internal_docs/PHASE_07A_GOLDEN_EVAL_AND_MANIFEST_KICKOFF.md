# Phase 07A Kickoff: Golden Eval Set And Build Manifest

## Purpose

This worker owns the baseline-preservation layer for Phase 07.

The goal is to make future modularization and provider swaps measurable rather than anecdotal.

## Own

- committed golden evaluation artifact
- build manifest format and generation
- evaluation-runner output format
- tests or checks for the new artifact shapes where appropriate

## Do Not Own

- major retrieval refactors
- provider-interface extraction outside what is strictly needed for the eval runner
- alternate embedding or reranker implementations

## Required Outputs

### 1. Golden Evaluation Artifact

Create a file in the repo that captures a small set of representative prompts.

Minimum coverage:

- Apple/Tesla/JPMorgan comparison
- Apple/Tesla comparison
- JPMorgan/Bank of America comparison
- at least one single-company risk-factor query
- at least one time-bounded growth or revenue query
- at least one broader sector or regulatory query

Each record should include:

- query id
- prompt text
- expected tickers
- whether comparison behavior is required
- optional contamination or filtering notes

### 2. Build Manifest

Create a machine-readable artifact that records:

- chunking configuration
- lexical and dense table names
- embedding model name and dimension
- reranker name
- relevant artifact file names

### 3. Eval Runner Contract

Define or implement a bounded runner that saves:

- config used
- retrieved tickers
- retrieved chunk ids
- answer output when applicable
- pass/fail fields or placeholders for later scoring

## Validation

At minimum, leave behind:

- exact command(s) used to run the eval harness
- one saved baseline output
- a short note on what still requires later scoring logic

## Definition Of Done

This worker is done when:

- the golden evaluation artifact exists in the repo
- the build manifest shape is defined and emitted
- a baseline eval run can be saved and inspected
