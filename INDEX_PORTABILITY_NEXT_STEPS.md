# Index Portability Implementation Next Steps

## Purpose

This file captures the implementation work still needed around indexing portability and reviewer setup.

The repo already builds the searchable state locally in LanceDB. The remaining work is to tighten the downstream user experience and make the indexing/distribution story explicit in code and docs.

## Current Technical State

The current searchable system is built locally in two steps:

1. `uv run eliza-rag-load-chunks`
   - writes the lexical chunk table to `data/lancedb/filing_chunks.lance`
2. `uv run eliza-rag-build-dense-index`
   - writes the dense table to `data/lancedb/filing_chunks_dense.lance`

At query time:

- lexical retrieval reads from `filing_chunks`
- dense retrieval reads from `filing_chunks_dense`
- hybrid retrieval reads from both

This means the repo currently supports a portable local-build flow, not a zero-build prepackaged search bundle.

## Implementation Work Remaining

### 1. Make the portability mode explicit

The project should explicitly choose and document one of these supported modes:

- local-build reviewer flow
- prebuilt-artifact reviewer flow

Implementation tasks:

- update `DECISIONS.md` with the chosen distribution mode
- update `README.md` so the reviewer flow matches that choice exactly
- ensure `IMPLEMENTATION_KANBAN.md` reflects the chosen portability path

### 2. If local build remains the supported path, tighten the setup flow

Implementation tasks:

- make the README reviewer path explicit about when `eliza-rag-load-chunks` is required
- make the README reviewer path explicit about when `eliza-rag-build-dense-index` is required
- ensure CLI failure messages clearly tell the user which build step is missing
- verify the answer demo path is understandable for:
  - lexical-only mode
  - hybrid mode with dense prerequisites

Desired outcome:

- a downstream user can follow the README and know exactly which build commands are required before retrieval and answer generation

### 3. If prebuilt artifacts are desired, add a concrete packaging path

Implementation tasks:

- decide where the built LanceDB artifacts should live:
  - committed in repo
  - release bundle
  - downloadable artifact
- define the artifact set that must stay aligned:
  - `data/lancedb/filing_chunks.lance`
  - `data/lancedb/filing_chunks_dense.lance`
  - any supporting artifact metadata needed for validation
- document how a user rebuilds the artifacts if they are missing or stale
- add a validation check so the repo can detect whether shipped artifacts are present and usable

Desired outcome:

- a downstream user can run the demo without rebuilding search artifacts, or gets a precise fallback instruction if rebuild is necessary

### 4. Add artifact/readiness validation

Regardless of portability mode, the repo should validate the search state more explicitly.

Implementation tasks:

- add a small readiness check for:
  - lexical LanceDB table presence
  - dense LanceDB table presence when `dense` or `hybrid` mode is requested
- ensure the answer path and retrieval CLI both surface missing-artifact guidance clearly
- consider adding one dedicated command such as an environment or demo readiness check if it helps reviewer ergonomics

Desired outcome:

- users should not have to guess whether indexing is complete

### 5. Document rebuild triggers

Implementation tasks:

- document exactly when a rebuild is required
- at minimum call out:
  - rerun `eliza-rag-load-chunks` if chunk materialization changes
  - rerun `eliza-rag-build-dense-index` after any lexical chunk table refresh
- make sure the docs use the same wording everywhere

Desired outcome:

- the repo avoids stale-index confusion during iteration and review

### 6. Add one explicit reviewer-facing setup path

Implementation tasks:

- make one path in the README authoritative
- keep it short and executable
- avoid making the reviewer infer which index build commands are optional

Desired outcome:

- the user sees one recommended path first
- advanced alternatives can remain in later sections

## Recommended Implementation Order

1. decide whether the supported portability mode is local-build or prebuilt-artifact
2. update `DECISIONS.md` and `README.md` to match that choice
3. tighten missing-artifact and rebuild guidance in CLI output and docs
4. add or improve artifact readiness validation
5. only then consider prebuilt artifact packaging if the project wants true zero-build reviewer setup

## Bottom Line

The core indexing pipeline already works.

The remaining work is not about inventing a new retrieval system. It is about making the indexing experience reviewer-safe and operationally explicit:

- what gets built
- where it lives
- when it must be rebuilt
- whether the downstream user is expected to build it or receive it prebuilt
