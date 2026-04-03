# Agent Instructions

## Purpose

This file gives future agents a compact operating guide for working in this repository without carrying a large conversational context forward.

The repo should be treated as the source of truth. Prefer reading these files first instead of relying on prior chat history:

- `HIGH_LEVEL_PLAN.md`
- `DECISIONS.md`
- `IMPLEMENTATION_KANBAN.md`
- `LIMITATIONS.md`

## Current Project Goal

Build a working demo that answers business questions over SEC filings using retrieval-augmented generation with:

- offline ingestion and indexing
- one final LLM API call for answer generation
- strong grounding and citation behavior
- evaluation across chunking, retrieval, and reranking options

## Core Decisions Already Made

- Use `LanceDB` as the main local retrieval engine.
- Keep one normalized filing record per filing.
- Create many chunk records per filing.
- Duplicate lightweight filterable metadata onto each chunk.
- Treat chunking as an explicit eval dimension.
- Treat retrieval mode as an explicit eval dimension:
  - dense
  - lexical or FTS
  - hybrid
- Use `chonkie` as the chunking experiment driver, not as a single chunking strategy.
- Prefer lightweight deterministic query expansion before trying more complex rewrite flows.
- The final user-facing answer must come from one LLM API call.

## How To Work

1. Start by reading the current state from:
   - `DECISIONS.md`
   - `LIMITATIONS.md`
   - `IMPLEMENTATION_KANBAN.md`
   - only the relevant sections of `HIGH_LEVEL_PLAN.md`
2. Pick one bounded task or one closely related task group.
3. Implement that task fully.
4. Update `IMPLEMENTATION_KANBAN.md` to reflect the new state.
5. If the task changes architecture or major tooling, update `DECISIONS.md`.
6. If the task changes execution order or experiment framing, update `HIGH_LEVEL_PLAN.md` only if needed.
7. If the task reveals new caveats, dataset weaknesses, or evaluation risks, update `LIMITATIONS.md`.

## Phase Doc Alignment

Phase kickoff and handoff documents must follow the execution path laid out in `HIGH_LEVEL_PLAN.md`.

This means:

- each new phase should map clearly onto the next logical segment of the high-level plan
- phase docs should state how the phase advances the intended pipeline or experiment path
- if a phase intentionally deviates from the high-level plan, the deviation must be called out explicitly and justified
- `HIGH_LEVEL_PLAN.md` should be updated when the intended execution path materially changes, rather than letting phase docs drift silently

Treat `HIGH_LEVEL_PLAN.md` as the roadmap and phase docs as bounded execution slices of that roadmap.

## Token Discipline

To preserve context length:

- do not reload the entire repo unless necessary
- do not restate long prior reasoning in chat
- use the markdown files in this repo as persistent memory
- prefer small, focused work sessions
- after finishing a task, write the result into repo docs rather than relying on chat memory

Preferred workflow:

- one agent or session handles one implementation slice
- each slice should be small enough to verify and document cleanly
- future sessions should resume from repo state, not from conversational recap

## Recommended Task Splitting

Good task boundaries:

- project scaffold and dependency setup
- corpus extraction and manifest inspection
- filing metadata normalization
- chunk schema and chunk materialization
- LanceDB table setup
- dense retrieval path
- lexical retrieval path
- hybrid retrieval path
- query analysis and deterministic expansion
- reranking integration
- answer prompt and single-call generation
- eval dataset creation
- eval harness implementation
- README and submission artifacts

Avoid combining too many of these into one session unless they are tightly coupled.

## Implementation Expectations

- Keep the system local and easy to run.
- Optimize for correctness, explainability, and demo readiness over scale.
- Avoid adding infrastructure unless it directly reduces implementation effort or improves evaluation quality.
- Prefer simple, inspectable data flows and stable IDs.
- Keep chunk-level metadata rich enough for direct filtering and citation tracing.

## Evaluation Expectations

The eval should compare pipeline segments, not just produce one happy-path demo.

At minimum, preserve the ability to compare:

- chunking strategies
- retrieval modes
- reranking on vs off
- query expansion variants

Primary selection criterion:

- end-to-end answer quality

Supporting criteria:

- retrieval metrics
- groundedness
- completeness
- citation quality
- implementation simplicity

## Documentation Expectations

When making meaningful progress:

- update `IMPLEMENTATION_KANBAN.md`
- update `DECISIONS.md` if a decision was made
- add short comments or docstrings only where they reduce future confusion

Do not let important decisions live only in chat.

## If Unsure

- prefer the simpler implementation
- preserve the current architecture unless there is a clear reason to change it
- document the tradeoff briefly in `DECISIONS.md`
- document newly discovered caveats in `LIMITATIONS.md` when relevant
- keep moving with a bounded task rather than reopening the whole design
