# SEC Filings RAG Demo Plan

## Goal

Build a working demo that answers a business question over SEC filings using:

- offline indexing and retrieval preparation
- one final LLM API call per user question
- grounded answers with citations to retrieved filing excerpts

This plan is optimized for the assessment timebox: quick to implement, easy to explain live, and accurate enough to defend.

## Current Repo State

The repo is no longer at the early scaffold stage described in the original execution plan.

Current implemented state:

- local corpus normalization and chunk materialization are working
- lexical, dense, hybrid, and `targeted_hybrid` retrieval paths exist
- reranking is implemented and exposed explicitly
- one alternate embedder and one alternate reranker are now wired behind explicit provider-selection surfaces
- the one-final-call answer path is implemented
- the primary reviewer flow now restores a prebuilt GitHub Release archive instead of requiring a local retrieval rebuild
- the top-level docs now separate reviewer usage, architecture explanation, and deeper eval detail

Current interpretation:

- the main demo path is credible enough to stabilize
- the repo has completed the bounded answer-eval and visualization work from Phase 09
- the next priority after that work is documentation and presentation quality rather than new core capability
- Phase 07 completed the provider-boundary extraction work
- Phase 08 completed the provider-evidence and retrieval-scoring layer
- Phase 09 completed bounded answer-level evaluation and artifact-driven inspection
- Phase 10 is the final bounded demo-lock and reviewer-packaging phase

## Next Recommended Execution Path

The next bounded phase should now be treated as Phase 10:

1. simplify the top-level README around the reviewer journey
2. separate the compact architecture story into its own document
3. tighten the evaluation narrative around the saved judged visualization
4. keep raw artifacts, judged overlays, and read-only reports clearly separated
5. leave maintainer detail and phase history in supporting docs rather than the entry path

This is the recommended order because:

- the main uncertainty is now presentation quality, not missing retrieval capability
- the repo already has a credible saved evidence stack
- reviewer friction is now more likely to come from diffuse documentation than from missing core mechanics

Current status:

- the eval baseline and build-manifest foundation are in place
- Phase 07B completed the explicit interface extraction for embedders, rerankers, query analyzers, retrievers, and answer backends
- Phase 07 is complete in intended scope
- Phase 08 produced bounded saved provider evidence and stronger retrieval-level scoring
- Phase 09 produced bounded answer-level evaluation, judged overlays, and artifact-driven reporting
- Phase 10 should now be treated as the final demo-lock and reviewer-packaging pass

## What We Know From The Workspace

- The workspace currently contains only the prompt, the assessment PDF, and `edgar_corpus.zip`.
- The corpus archive appears to contain plain-text 10-K and 10-Q filings across many large US companies.
- The archive contents do not fully match the brief wording. The brief says 2023-2025, but filenames in the archive appear to include earlier and later dates as well.

## Working Assumptions

1. We will treat the zip file contents as source of truth, not the brief summary.
2. We will preserve document metadata from filenames and `manifest.json` if present.
3. The answer step must be one LLM API call, but retrieval can be multi-stage and fully offline.
4. Accuracy matters more than latency for the assessment, as long as the demo remains responsive.
5. We should prefer a design that can be explained clearly in 5-10 minutes.

## Success Criteria

- Correctly identifies relevant companies, dates, and topics from the user question.
- Retrieves the most relevant filing passages, not just the correct documents.
- Produces a structured answer that compares companies or time periods when asked.
- Grounds claims in retrieved evidence and avoids unsupported synthesis.
- Keeps the final answer inside one LLM call.

## Recommended System Design

### 1. Ingestion And Metadata Normalization

- Unzip corpus locally.
- Parse `manifest.json` if present.
- Extract metadata from filenames:
  - `ticker`
  - `form_type`
  - filing date
  - fiscal period token if available
- Store one normalized record per filing.
- Create chunk records that each retain:
  - `filing_id`
  - duplicated filterable metadata such as `ticker`, `form_type`, `filing_date`, and fiscal period
  - chunk-local metadata such as section name and chunk index when available

Reason:
Metadata filtering will materially improve retrieval for questions that mention company names, industries, or time periods.
Duplicating lightweight filing metadata onto each chunk is the right tradeoff here because vector and BM25 retrieval typically operate at chunk granularity, and this avoids a retrieval-time join.

### 2. Filing Chunking

Recommended default:

- paragraph-aware chunking
- target chunk size: 700-1,000 tokens
- overlap: 80-120 tokens
- keep section headers attached to following body text

Why:

- SEC filings are long and section-structured.
- Business questions often require paragraph-level reasoning, not sentence-only lookup.
- Too-small chunks lose context around risks, outlook, and year-over-year changes.

Variants to evaluate:

- `C1`: fixed-size chunking, 800 tokens, 100 overlap
- `C2`: paragraph-aware chunking with header carry-forward
- `C3`: section-first chunking for known sections such as Risk Factors and MD&A
- `C4`: use `chonkie` as the chunking driver to compare multiple chunking strategies quickly under one interface
  - token-based or fixed-size chunking
  - recursive or paragraph-aware chunking
  - sentence-based chunking
  - semantic or structure-aware chunking if integration remains lightweight

Expected winner:

- `C2` is the best default balance.
- `C3` may help targeted questions but is more engineering work and less robust across unknown prompts.
- `C4` is worth using as the experimentation harness if setup overhead stays low, because it reduces the cost of comparing chunking strategies rather than representing one single strategy.

### 3. Indexing Strategy

Maintain:

- a filing-level normalized record store as the source of truth
- a chunk-level retrieval store with duplicated filterable metadata

Recommended engine:

- use `LanceDB` as the local retrieval engine for chunk storage, vector search, full-text search, hybrid search, metadata filtering, and reranking integration

Why:

- we want to compare dense, lexical, and hybrid retrieval modes without spending assessment time writing retrieval infrastructure
- this is a lightweight local demo, so operational simplicity matters
- `LanceDB` gives us the retrieval APIs needed for the eval matrix with minimal glue code

Build retrieval candidates along a separate retrieval-mode dimension:

- dense vector retrieval for semantic matching
- sparse BM25 retrieval for exact phrase, entity, and terminology matching
- hybrid retrieval that combines both

Recommended retrieval stack:

- run retrieval over chunks, not full filings
- support direct chunk-level filtering by duplicated metadata
- test dense-only, BM25-only, and hybrid retrieval
- use reciprocal rank fusion or weighted merge for hybrid candidates
- optionally rerank top candidates

Why:

- SEC questions mix semantic needs with exact terminology, company names, regulations, and financial phrases.
- Hybrid retrieval is more robust than dense-only for this domain.

Fallback if needed:

- if `LanceDB` integration becomes unexpectedly costly, fall back to a simpler source-of-truth plus separate retrieval components design
- this should be treated as a contingency, not the primary recommendation

### 4. ANN Choice

Recommended:

- HNSW-based ANN for the dense index

Why:

- fast, standard, strong recall, easy to justify
- ideal for a small-to-medium local corpus

Not recommended for v1:

- IVF/PQ or heavier compression schemes

Reason:

- unnecessary complexity for this dataset size
- likely hurts recall more than it helps operationally in an assessment demo

### 5. Query Understanding And Rewriting

Recommended lightweight approach:

- no mandatory LLM rewrite step in v1
- deterministic query expansion before retrieval:
  - detect company names and map to tickers
  - detect time language such as "last two years"
  - detect intent classes such as `risk`, `revenue`, `growth outlook`, `regulatory`
  - expand with synonyms when useful

Why:

- keeps the answer path compliant with the one-call constraint
- avoids hidden failure points
- gives a clean live explanation

Variants to evaluate:

- `Q1`: raw user query only
- `Q2`: deterministic metadata-aware rewrite
- `Q3`: one-shot LLM rewrite for retrieval only

Expected winner:

- `Q2` for production of the assessment submission
- `Q3` can be tested offline, but likely adds complexity without enough upside for the timebox

### 6. Reranking

Recommended:

- rerank top 20-40 retrieved chunks down to top 6-10 chunks using a cross-encoder or strong reranker

Why:

- many questions ask for cross-company comparison or temporal change
- initial retrieval may surface correct documents but poor excerpt ordering
- reranking usually gives a bigger answer-quality gain than more exotic indexing changes

Variants to evaluate:

- `R0`: no reranker
- `R1`: cross-encoder reranker on top fused results
- `R2`: ColBERT-style late interaction if feasible

Expected winner:

- `R1` is the likely best accuracy-to-effort choice

### 7. Late Interaction / ColBERT-Zero

Interest area:

- LightOn's open-source ColBERT-zero style late-interaction retrieval is worth evaluating because filings contain long passages where token-level matching can outperform standard dense embeddings.

Assessment:

- Include as an experimental candidate, not the default implementation path.
- It is promising for retrieval accuracy, especially on nuanced comparison questions.
- Risk is setup and tuning overhead within a 4-hour assessment.

Recommendation:

- Build the baseline system first with hybrid retrieval + reranking.
- If time remains, test a ColBERT-style candidate against the same evaluation set.
- Only adopt it if it clearly improves grounded answer quality, not just retrieval scores.

## Candidate Pipeline Segments To Evaluate

We should treat the system as interchangeable stages and test a small set of realistic combinations.

Primary experimental dimensions:

- chunking strategy
- retrieval mode: dense, BM25, hybrid
- query rewrite strategy
- reranking strategy

This can be treated as a small multi-armed bandit style search over pipeline segments, with answer quality as the reward signal and retrieval metrics as supporting signals.
If `chonkie` is used, it should be treated as the driver for chunking experiments within the chunking-strategy dimension, not as a separate arm by itself.

### Baseline

`P0 = C1 + dense only + no rewrite + no reranker`

Purpose:

- establish a minimum working path quickly

### Strong Practical Candidate

`P1 = C2 + hybrid retrieval + deterministic rewrite + cross-encoder reranker`

Purpose:

- likely best submission candidate

### High-Recall Candidate

`P2 = C2 + BM25 or hybrid retrieval + deterministic rewrite + larger candidate pool + reranker`

Purpose:

- improve cross-company and cross-period questions

### Experimental Late-Interaction Candidate

`P3 = C2 + BM25 or hybrid prefilter + ColBERT-style late interaction`

Purpose:

- test whether late interaction materially improves excerpt selection

### Chunking Experiment Candidate

`P4 = C4 + best retrieval mode from eval + deterministic rewrite + reranker`

Purpose:

- use `chonkie` to compare several chunking strategies quickly and determine whether any outperform the default paragraph-aware baseline enough to justify adoption

## Evaluation Plan

The evaluation should pick the best pipeline by answer accuracy, not by retrieval score alone.

### 1. Build A Small Gold Evaluation Set

Create 12-20 representative questions covering:

- single-company trend questions
- cross-company comparison questions
- regulatory risk questions
- risk factor questions
- revenue / growth outlook questions
- time-bounded questions such as "last two years"

For each question, record:

- expected companies
- expected filing date range
- expected themes
- one or more relevant filing passages

### 2. Retrieval Evaluation

Measure:

- Recall@k on gold passages or gold documents
- MRR or nDCG on relevant chunks
- metadata hit rate:
  - correct companies
  - correct periods
- performance by retrieval mode:
  - dense only
  - BM25 only
  - hybrid

Purpose:

- eliminate obviously weak retrieval designs before full answer evaluation

### 3. End-To-End Answer Evaluation

For each candidate pipeline, run the final one-call prompt and score:

- groundedness:
  - are claims supported by retrieved text
- completeness:
  - does it cover all requested companies or periods
- factual consistency:
  - does it avoid contradicting the filings
- comparative usefulness:
  - does it actually compare, not just summarize separately
- citation quality:
  - are evidence snippets traceable to specific filings

Recommended judging method:

- use a strong LLM as an offline evaluator with a rubric
- manually inspect failures for the top 2-3 pipelines

This aligns with the prompt note that using a strong model with one-shot demonstrations is acceptable for verification.

### 3A. Stability Harness Before Broader Modularity

Before broadening the architecture further, add a narrow stability harness that records:

- query text
- expected company coverage
- unacceptable contamination
- retrieval mode and reranker configuration
- final answer output
- citation ids and cited chunks

Purpose:

- make modular refactors measurable rather than anecdotal
- prevent accidental regressions while extracting provider interfaces
- create a stable baseline before testing alternate embedding and reranking models

### 4. Decision Rule

Choose the final pipeline by:

1. strongest end-to-end answer quality on the gold set
2. strongest groundedness and citation behavior
3. simplest architecture that achieves the above

This prevents over-selecting a fancy retriever that is harder to explain but not meaningfully better in the demo.

## Prompt Strategy For The Final One-Call Answer

The final prompt should:

- restate the user question
- include a compact instructions block
- include retrieved context chunks with metadata
- require structured output
- require evidence-based reasoning only from provided context
- require explicit uncertainty when evidence is missing

Recommended answer format:

- short executive summary
- per-company or per-period findings
- comparison section
- evidence citations
- limitations / ambiguities if needed

## Deliverable Plan

### Phase 1: Fast Skeleton

- unpack and inspect corpus
- write ingestion script
- implement baseline chunking
- build dense retrieval baseline
- create one-call answer prompt

### Phase 2: Accuracy Upgrades

- add BM25
- add hybrid fusion
- add deterministic query expansion
- add reranker

### Phase 3: Evaluation And Selection

- create eval set
- score candidate pipelines
- compare answer outputs
- choose final system

### Phase 4: Submission Artifacts

- README with exact setup and run instructions
- prompt iteration log
- final prompt template
- example request
- evaluation notes
- demo walkthrough notes

### Phase 5: Stabilization And Modularization Prep

- golden evaluation set and eval runner
- build manifest tied to release artifacts
- explicit provider interfaces for:
  - embedder
  - reranker
  - query analyzer
  - retriever
  - answer backend
- no-behavior-change extraction of current implementations behind those interfaces

### Phase 6: Bounded Provider Experiments

- compare the current Snowflake embedding baseline against one stronger candidate
- compare the current BGE reranker against one alternate reranker
- keep deterministic query analysis as the default unless evaluation proves otherwise

## Proposed Final Recommendation

Unless experiments show otherwise, the default submission should be:

- paragraph-aware chunking with header carry-forward
- hybrid retrieval: dense + BM25
- HNSW ANN for dense search
- deterministic metadata-aware query expansion
- cross-encoder reranking
- one final answer-generation LLM call with strict grounding instructions

This is the highest-confidence path for the assessment because it is:

- accurate
- explainable
- implementable inside the timebox
- easy to defend against alternatives

## Risks And Mitigations

- Risk: archive contents span more than the brief date range
  - Mitigation: expose filing date metadata and support time filtering explicitly
- Risk: long filings produce noisy retrieval
  - Mitigation: chunk carefully and rerank aggressively
- Risk: comparison questions need evidence from multiple companies
  - Mitigation: diversify retrieval across entities and cap per-document dominance
- Risk: modularization could silently regress a demo path that currently works
  - Mitigation: freeze a golden evaluation set and build manifest before provider swaps
- Risk: introducing a learned router too early adds opaque failures
  - Mitigation: keep deterministic query analysis as the default until evaluation shows it is the dominant bottleneck
- Risk: answer call exceeds context budget
  - Mitigation: limit to top reranked chunks and compress metadata formatting
- Risk: late-interaction experiments consume too much time
  - Mitigation: treat ColBERT-style retrieval as optional after baseline quality is proven

## Immediate Next Steps

1. Unpack the corpus and inspect `manifest.json`.
2. Implement ingestion and metadata normalization.
3. Build `P0` and `P1` first.
4. Create the evaluation question set before spending time on exotic retrieval variants.
5. Only test ColBERT-style late interaction if `P1` still misses key cases.
