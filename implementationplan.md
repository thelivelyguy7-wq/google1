# Phase-Wise Implementation Plan

> AI-Powered Discovery Engine: Google Photos, retrieving photos users remember but cannot precisely describe
> Derived from [problemstatement.md](problemstatement.md) and [architecture.md](architecture.md)

---

## Executive Summary

The Discovery Engine is a **research instrument**, not a product solution. It turns user conversations into traceable, comparable, behavioural evidence, and stops at research hypotheses and an interview brief.

This plan breaks the build into **13 phases**. Phases 0–8 deliver the engine: data layer, analysis, validation, synthesis, exploration and API. Phase 9 adds test data and evaluation. Phase 10 hardens the build with tests and docs. Phase 11 switches the engine to the project's raw dataset, `google_photos_discovery_annotated`. Phase 12 delivers the discovery workspace UI.

| Phase | Focus | Outcome | Status |
|-------|-------|---------|--------|
| **0** | Foundation | Package skeleton, taxonomy, data contracts, SQLite store, config | ✅ Done |
| **1** | Ingestion | Multi-format loading, cleaning, PII scrub, dedupe, chunking | ✅ Done |
| **2** | Analysis layer | Claude analyzer (relevance → extraction) + offline heuristic analyzer | ✅ Done (Claude untested live) |
| **3** | Evidence validation | Verbatim-quote validation, evidence IDs, PM overrides | ✅ Done |
| **4** | Quantitative synthesis | Rates with explicit denominators, distributions, cross-tabs, journey | ✅ Done |
| **5** | Segments & opportunities | Segment and opportunity comparison, contradictions, evidence strength | ✅ Done |
| **6** | Hypotheses & handoff | Hypotheses, JTBD, leading opportunity, discovery report, research brief | ✅ Done |
| **7** | Exploration interface | Source-diverse evidence search, PM question answering | ✅ Done |
| **8** | API & dashboard | FastAPI + first single-page dashboard (now at `/classic`) | ✅ Done |
| **9** | Test data & evaluation | Seeded generator (840 rows), answer key, accuracy scoring | ✅ Done (superseded for data by Phase 11) |
| **10** | Tests & docs | pytest suite (14 tests), README, problem statement, architecture, edge cases, evals | ✅ Done |
| **11** | Raw dataset `google_photos_discovery_annotated` | xlsx → CSV, database rebuilt from it alone, reports regenerated, annotation cross-check | ✅ Done (evaluation tasks open) |
| **12** | Discovery workspace (UI/UX) | 11 views, evidence inspector, ask palette, review queue, light/dark, responsive | ✅ Done (browser tests to commit) |

**LLM:** Claude Opus 5 (`claude-opus-5`) via the Anthropic Python SDK, with structured outputs, adaptive thinking and server-side refusal fallback (`fallbacks: "default"`). Without credentials, the engine runs end to end on the heuristic analyzer, and every output records which analyzer produced it.

---

## Prerequisites

- Python 3.10+ (built and tested on 3.14)
- Packages from `requirements.txt`: `anthropic`, `pydantic`, `pandas`, `openpyxl`, `scikit-learn`, `numpy`, `fastapi`, `uvicorn`, `pytest`
- Optional from Phase 2 onward: Claude credentials (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, or an `ant auth login` profile)
- The raw dataset `google_photos_discovery_annotated.xlsx` at the project root (Phase 11)
- For browser tests (Phase 12): Playwright with Microsoft Edge or Chromium

---

## Non-Negotiable Principles (apply to every phase)

1. **Raw evidence ≠ AI interpretation.** `records` and `chunks` are never modified by analysis.
2. **No fabrication.** Every signal carries a verbatim quote; quotes that can't be found in the source are flagged and excluded from counts.
3. **Honest numbers.** Every percentage carries its numerator, denominator and scope. Small samples are labelled DIRECTIONAL.
4. **Epistemic labels stay separate.** Observation, Insight, Interpretation, Hypothesis and Opportunity are never merged.
5. **Problem spaces, not features.** Opportunity areas never name a solution.
6. **Accurate provenance.** Every dataset's origin is recorded and shown truthfully in files, database rows, reports and the dashboard.
7. **Sentiment is supplementary only.**
8. **No PII.** Author identifiers are salted hashes; emails and phone numbers are scrubbed on ingest.

---

## Phase 0: Foundation

**Goal:** Build the package skeleton, controlled vocabularies, data contracts, storage and settings that every later phase depends on.

**Maps to problem statement:**
- §4 Framework: keep Observation / Insight / Interpretation / Hypothesis / Opportunity separate
- §8 Evidence sources and ingestion: store raw evidence separately from AI interpretation
- §10 Classification schemes (extensible)
- §11 Retrieval failure taxonomy A–G

### Tasks

#### 0.1 Taxonomy

| # | Task | File(s) |
|---|------|---------|
| 0.1.1 | Journey stages: recall → express → match → recognize → recover (revised in Phase 13.6; was remember → express → understand → retrieve → evaluate → refine → confirm) | `discovery_engine/taxonomy.py` |
| 0.1.2 | Retrieval scenarios, memory signals, forgotten-information labels | `discovery_engine/taxonomy.py` |
| 0.1.3 | Behaviours, workarounds, success statuses, query orientations | `discovery_engine/taxonomy.py` |
| 0.1.4 | Failure taxonomy A–G with definitions, plus `none_observed` / `unclear` | `discovery_engine/taxonomy.py` |
| 0.1.5 | Seed opportunity areas, written as problem spaces (8 areas) | `discovery_engine/taxonomy.py` |

#### 0.2 Data contracts

| # | Task | File(s) |
|---|------|---------|
| 0.2.1 | `RawRecord`: source, platform, URL, title, text, thread, replies, engagement, dates, author hash, dataset, provenance flag | `discovery_engine/models.py` |
| 0.2.2 | `Signal` (label, value, verbatim quote, precision), `QueryAttempt`, `JourneyStep` | `discovery_engine/models.py` |
| 0.2.3 | `ChunkAnalysis`: the single output schema every analyzer must produce | `discovery_engine/models.py` |
| 0.2.4 | `RelevanceResult` for the relevance gate | `discovery_engine/models.py` |

#### 0.3 Store

| # | Task | File(s) |
|---|------|---------|
| 0.3.1 | SQLite schema: `records`, `chunks`, `analyses` (versioned), `signals`, `overrides`, `syntheses` | `discovery_engine/store.py` |
| 0.3.2 | Write helpers: insert record/chunk, save analysis + signals in one transaction, add override, save synthesis | `discovery_engine/store.py` |
| 0.3.3 | Read views `current_analyses()` / `current_signals()` that apply overrides at read time | `discovery_engine/store.py` |

#### 0.4 Configuration

| # | Task | File(s) |
|---|------|---------|
| 0.4.1 | Settings with env overrides: `DE_DB_PATH`, `DE_MODEL`, `DE_EFFORT`, `DE_SYNTHESIS_EFFORT`, `DE_CONCURRENCY`, `DE_CHUNK_CHARS`, `DE_AUTHOR_SALT`, `DE_MIN_SAMPLE` | `discovery_engine/config.py` |
| 0.4.2 | `requirements.txt`, `.gitignore` (database, caches, `.env`) | project root |

### Deliverables

- [x] `discovery_engine` package imports cleanly
- [x] Taxonomy covers every label set in problem statement §10–§11
- [x] Store creates all six tables on first use
- [x] Overrides apply on read without editing stored payloads

### Acceptance Criteria

- `python -c "import discovery_engine"` succeeds.
- A fresh `Store(path)` creates the schema.
- Stored AI payloads are unchanged after an override is added.

### Estimated effort

**0.5–1 day**

---

## Phase 1: Ingestion

**Goal:** Turn source files into clean, deduplicated, chunked raw evidence, without losing or inventing anything.

**Maps to problem statement:**
- §8 Sources and formats: CSV, XLSX, JSON, JSONL, text
- §9 Pipeline: COLLECT → CLEAN → DEDUPLICATE → CHUNK
- §18 Privacy: no PII, no identifying individuals

### Tasks

#### 1.1 Loading

| # | Task | File(s) |
|---|------|---------|
| 1.1.1 | Loaders for CSV, XLSX, JSON (list or `{records: []}`), JSONL, TXT (blank-line blocks) | `discovery_engine/ingest.py` |
| 1.1.2 | `FIELD_ALIASES`: map common export columns (`body`, `selftext`, `review`, `id`, `permalink`, `created_utc`, `video_title`, …) onto record fields | `discovery_engine/ingest.py` |

#### 1.2 Cleaning and privacy

| # | Task | File(s) |
|---|------|---------|
| 1.2.1 | Unescape HTML, strip tags, collapse whitespace | `discovery_engine/ingest.py` |
| 1.2.2 | Replace emails and phone-like numbers with placeholders | `discovery_engine/ingest.py` |
| 1.2.3 | Replace author names with a salted SHA-256 hash | `discovery_engine/ingest.py` |
| 1.2.4 | Skip texts shorter than 15 characters | `discovery_engine/ingest.py` |

#### 1.3 Deduplication

| # | Task | File(s) |
|---|------|---------|
| 1.3.1 | Exact duplicates: hash of normalised title + text | `discovery_engine/ingest.py` |
| 1.3.2 | Near duplicates: Jaccard similarity of 5-word shingles ≥ 0.9 | `discovery_engine/ingest.py` |
| 1.3.3 | Keep duplicates as raw evidence with `duplicate_of` set; exclude them from chunks and counts | `discovery_engine/ingest.py` |
| 1.3.4 | Idempotency: `record_id = source:source_id`, so re-ingesting adds nothing | `discovery_engine/ingest.py` |

#### 1.4 Chunking

| # | Task | File(s) |
|---|------|---------|
| 1.4.1 | Sentence-boundary chunking up to `DE_CHUNK_CHARS` (3,500) | `discovery_engine/ingest.py` |

### Deliverables

- [x] `ingest_file()` returns stats: rows, inserted, skipped, already present, exact and near duplicates
- [x] PII scrubbed before storage
- [x] Duplicates marked, not deleted
- [x] CLI: `python -m discovery_engine ingest PATH [--source] [--dataset] [--synthetic]`

### Acceptance Criteria

- Ingesting the same file twice inserts nothing the second time.
- Emails and phone numbers never reach the database.
- Missing fields stay empty; no URLs, titles or dates are invented.

### Estimated effort

**0.5–1 day**

---

## Phase 2: Analysis Layer

**Goal:** Turn each chunk into a structured `ChunkAnalysis`: relevance, scenario, memory, forgotten information, search behaviour, failure, workarounds and segment signals.

**Maps to problem statement:**
- §6 Product-outcome decomposition (journey stages)
- §10 Classification schemes
- §17 AI analysis layer: 12 distinct modules, not one summarisation step

### Tasks

#### 2.1 Claude analyzer

| # | Task | File(s) |
|---|------|---------|
| 2.1.1 | Relevance classifier call (`effort: low`, schema `RelevanceResult`) | `discovery_engine/analyze/llm.py` |
| 2.1.2 | Evidence extractor call (`effort: DE_EFFORT`, schema `ChunkAnalysis`) with `client.beta.messages.parse` | `discovery_engine/analyze/llm.py` |
| 2.1.3 | System prompt: evidence rules, perspective separation, no assumed causality, no solutions, label vocabularies, `proposed:` labels | `discovery_engine/analyze/llm.py` |
| 2.1.4 | Wrap source text in `<source>` and declare it untrusted (prompt-injection safety) | `discovery_engine/analyze/llm.py` |
| 2.1.5 | Adaptive thinking, prompt caching, server-side refusal fallback; check `stop_reason` before reading output | `discovery_engine/analyze/llm.py` |
| 2.1.6 | `complete_json()` helper for later synthesis calls (streaming) | `discovery_engine/analyze/llm.py` |

#### 2.2 Heuristic analyzer

| # | Task | File(s) |
|---|------|---------|
| 2.2.1 | Sentence-level regex and lexicon patterns for every `ChunkAnalysis` section | `discovery_engine/analyze/heuristic.py` |
| 2.2.2 | Quote = the exact sentence that matched (always verbatim) | `discovery_engine/analyze/heuristic.py` |
| 2.2.3 | Guards: exclude query and need sentences from memory; check negated statuses first; cap confidence at 0.5 | `discovery_engine/analyze/heuristic.py` |
| 2.2.4 | Rule-based opportunity mapping from failure stage, clues and workarounds | `discovery_engine/analyze/heuristic.py` |

#### 2.3 Runner

| # | Task | File(s) |
|---|------|---------|
| 2.3.1 | Analyzer selection: `auto` (Claude if credentials found) / `claude` / `heuristic` | `discovery_engine/analyze/runner.py` |
| 2.3.2 | Resume: skip chunks already analysed by the same analyzer unless `--reanalyze` | `discovery_engine/analyze/runner.py` |
| 2.3.3 | Thread pool for Claude (`DE_CONCURRENCY`); database writes on the main thread | `discovery_engine/analyze/runner.py` |
| 2.3.4 | Error policy: stop on authentication errors; record refusals and API errors as skipped and continue | `discovery_engine/analyze/runner.py` |

### Deliverables

- [x] Both analyzers produce the same `ChunkAnalysis` schema
- [x] `ChunkAnalysis` compiles to a valid structured-output schema (checked offline)
- [x] Analyzer, model and prompt version stored with every analysis
- [x] CLI: `python -m discovery_engine analyze [--analyzer] [--reanalyze] [--limit] [--dataset]`
- [ ] Claude analyzer run against the live API (needs credentials; see Phase 11 open tasks)

### Acceptance Criteria

- Off-topic text is classified not relevant.
- Every heuristic quote validates as verbatim.
- An interrupted run resumes without re-analysing finished chunks.

### Estimated effort

**2–3 days**

---

## Phase 3: Evidence Validation

**Goal:** Make every AI claim checkable: normalise labels, give each claim an evidence ID, verify each quote against the source, and let a PM correct results.

**Maps to problem statement:**
- §9 Evidence preservation: evidence ID, excerpt, classification, confidence
- §17 Module 11: Evidence Validator
- §18 No fabrication; human in the loop; auditability

### Tasks

#### 3.1 Validator

| # | Task | File(s) |
|---|------|---------|
| 3.1.1 | Quote validation: normalise quote marks, whitespace and case; allow in-order `...` elision; minimum length 3 | `discovery_engine/validate.py` |
| 3.1.2 | Validate against exactly the text the analyzer saw (`title + chunk`) | `discovery_engine/analyze/runner.py` |
| 3.1.3 | Label normalisation (`place` → `remembered_place`); unknown labels → `proposed:<label>` | `discovery_engine/validate.py` |
| 3.1.4 | Flatten all claims into `signals` (12 kinds) with deterministic evidence IDs | `discovery_engine/validate.py` |
| 3.1.5 | Keep invalid quotes with `quote_valid = 0`; exclude them from every count | `discovery_engine/validate.py`, `store.py` |

#### 3.2 Overrides

| # | Task | File(s) |
|---|------|---------|
| 3.2.1 | Analysis overrides: `relevant`, `retrieval_scenario`, `failure_stage`, `success_status`, `perspective`, `describes_retrieval_attempt`, `opportunity_areas` | `discovery_engine/store.py` |
| 3.2.2 | Signal override: `rejected` | `discovery_engine/store.py` |
| 3.2.3 | Store old value, new value, note and timestamp for audit | `discovery_engine/store.py` |

### Deliverables

- [x] `validate_analysis()` returns normalised payload, signals and `{quotes_total, quotes_invalid}`
- [x] Evidence IDs (`EV-xxxxxxxxxx`) on every signal
- [x] Re-analysis versions results (`is_current`) instead of overwriting them

### Acceptance Criteria

- A fabricated quote is flagged invalid and excluded from counts.
- Feature-like "opportunities" become `proposed:*`.
- After an override, reads reflect the correction and the stored payload is unchanged.

### Estimated effort

**1 day**

---

## Phase 4: Quantitative Synthesis

**Goal:** Answer the core discovery questions with honest, traceable numbers.

**Maps to problem statement:**
- §7 Primary discovery questions 1–45
- §12 Quantitative analysis: numerator, denominator, scope; directional samples
- §14 Customer journey mapping

### Tasks

#### 4.1 Corpus and rate helper

| # | Task | File(s) |
|---|------|---------|
| 4.1.1 | `Corpus(store, include_synthetic, sources, dataset)` with populations `analyses`, `relevant`, `attempts` | `discovery_engine/quant.py` |
| 4.1.2 | `rate()` helper: numerator, denominator, pct, definition, scope, directional flag (`< DE_MIN_SAMPLE`) | `discovery_engine/quant.py` |
| 4.1.3 | Count distinct records, not signals | `discovery_engine/quant.py` |
| 4.1.4 | `diverse_examples()`: evidence picked round-robin across sources | `discovery_engine/quant.py` |

#### 4.2 Distributions

| # | Task | File(s) |
|---|------|---------|
| 4.2.1 | `overview()`: funnel, outcomes, perspectives, quote validation, proposed labels | `discovery_engine/quant.py` |
| 4.2.2 | `scenarios()`: attempts, outcomes, failure stages, top remembered/forgotten/workarounds per scenario | `discovery_engine/quant.py` |
| 4.2.3 | `memory()`: remembered clues, exact vs approximate | `discovery_engine/quant.py` |
| 4.2.4 | `forgotten()`: gaps; unsuccessful rate with vs without each; text-stated blocking | `discovery_engine/quant.py` |
| 4.2.5 | `search_formulation()`: query types, orientation, outcome by type, length, repeated attempts, strategies | `discovery_engine/quant.py` |
| 4.2.6 | `failures()`, `workarounds()`, `journey()` | `discovery_engine/quant.py` |
| 4.2.7 | Cross-tabs: scenario × failure, scenario × forgotten | `discovery_engine/quant.py` |

### Deliverables

- [x] Every rate in the system is produced by `rate()`
- [x] Scope records sources, date range, provenance count and analyzer mix
- [x] Forgotten information reported as association, not cause

### Acceptance Criteria

- A zero denominator gives `pct = None`, never a made-up number.
- Denominators below 30 are marked directional (†).

### Estimated effort

**1–1.5 days**

---

## Phase 5: Segments, Opportunities, Contradictions

**Goal:** Compare who is affected and which problem spaces have the strongest evidence, with no hidden score, while actively looking for evidence against each conclusion.

**Maps to problem statement:**
- §11 Root-cause discipline: symptom → behaviour → barrier → root cause
- §13 Segmentation and target segment dimensions
- §15 Opportunities, comparison fields, evidence strength, contradictory evidence

### Tasks

#### 5.1 Shared profile and segments

| # | Task | File(s) |
|---|------|---------|
| 5.1.1 | `profile()`: volume, sources, vague-memory cases, severity, dominant failure stage, top labels, provenance share | `discovery_engine/synthesis.py` |
| 5.1.2 | Scenario segments (6), usage segments (7), behavioural segments (3) | `discovery_engine/synthesis.py` |
| 5.1.3 | Distinctiveness (total-variation distance from all attempts); research feasibility left to PM judgement | `discovery_engine/synthesis.py` |

#### 5.2 Opportunities

| # | Task | File(s) |
|---|------|---------|
| 5.2.1 | Group relevant records by `opportunity_areas` | `discovery_engine/synthesis.py` |
| 5.2.2 | Severity, strategic relevance, unresolved questions, record IDs | `discovery_engine/synthesis.py` |
| 5.2.3 | Insights (OBSERVATION / INSIGHT), each citing only the signal kinds it is about | `discovery_engine/synthesis.py` |
| 5.2.4 | Root-cause chain with epistemic levels and evidence | `discovery_engine/synthesis.py` |

#### 5.3 Contradictions and evidence strength

| # | Task | File(s) |
|---|------|---------|
| 5.3.1 | Six contradiction types: counter-evidence, vague-memory success, alternative explanation, source concentration, scenario concentration, known workaround | `discovery_engine/synthesis.py` |
| 5.3.2 | `COUNTER_CONTRADICTS` mapping: which counter labels refute which opportunities | `discovery_engine/synthesis.py` |
| 5.3.3 | Weight counter-evidence by the opportunity's concentration in each record's scenario | `discovery_engine/synthesis.py` |
| 5.3.4 | Strength rules HIGH / MEDIUM / LOW / DIRECTIONAL (records, sources, first-person share, contradiction ratio); return PASS/FAIL per check | `discovery_engine/evidence.py` |

### Deliverables

- [x] Segment and opportunity comparisons with every dimension exposed
- [x] Contradictions reported per opportunity
- [x] Strength checks and caveats returned with every level

### Acceptance Criteria

- No composite score anywhere; the PM can sort by any dimension.
- Counter-evidence that supports an opportunity (e.g. data gaps for `index_coverage_gaps`) doesn't count against it.
- Opportunity record counts equal the length of their record-ID lists.

### Estimated effort

**1.5–2 days**

---

## Phase 6: Hypotheses and Research Handoff

**Goal:** Turn the strongest evidence into testable hypotheses, JTBD candidates, a proposed leading opportunity, an interview brief and the discovery report, without writing any findings.

**Maps to problem statement:**
- §14 JTBD (WHEN / BUT / PLEASE HELP ME / SO)
- §16 Hypotheses and primary-research handoff; non-leading interview questions
- §19 Final discovery output (14 sections)

### Tasks

#### 6.1 Hypotheses and JTBD

| # | Task | File(s) |
|---|------|---------|
| 6.1.1 | Per-opportunity scaffolds: belief, expected observations, falsification signals | `discovery_engine/hypotheses.py` |
| 6.1.2 | BECAUSE lines built only from computed rates | `discovery_engine/hypotheses.py` |
| 6.1.3 | JTBD candidates labelled INTERPRETATION, with stated-goal evidence | `discovery_engine/hypotheses.py` |
| 6.1.4 | Optional Claude wording pass (`--refine-hypotheses`) with citation checking | `discovery_engine/hypotheses.py` |

#### 6.2 Leading opportunity and interview guidance

| # | Task | File(s) |
|---|------|---------|
| 6.2.1 | Stated selection rule: strength tier → vague-memory share → unsuccessful share → sources; return as a proposal | `discovery_engine/hypotheses.py` |
| 6.2.2 | Core behavioural questions plus opportunity-specific ones | `discovery_engine/hypotheses.py` |
| 6.2.3 | `non_leading()` filter: reject "would you use/like", AI, assistant, chatbot, feature, conversational | `discovery_engine/hypotheses.py` |

#### 6.3 Bundle and reports

| # | Task | File(s) |
|---|------|---------|
| 6.3.1 | `build_bundle()`: all Phase 4–6 outputs, saved to `syntheses` | `discovery_engine/report.py` |
| 6.3.2 | Research brief: target segment, hypotheses, contradictions, unknowns, objectives, screener, questions, falsification signals; findings "Not yet collected" | `discovery_engine/report.py` |
| 6.3.3 | `render_report()`: 14-section discovery report with provenance banner | `discovery_engine/report.py` |
| 6.3.4 | CLI: `python -m discovery_engine synthesize` → `reports/discovery_report.md`, `reports/research_brief.md` | `discovery_engine/__main__.py` |

### Deliverables

- [x] Hypotheses in WE BELIEVE / BECAUSE / WE EXPECT TO OBSERVE / WE NEED TO VALIDATE form
- [x] Leading-opportunity proposal with its full ranking table
- [x] Research brief for 5–6 interviews
- [x] Discovery report covering all 14 sections

### Acceptance Criteria

- No leading or solution-naming interview questions survive the filter.
- The research brief contains no findings.
- Every BECAUSE line traces to a computed rate.

### Estimated effort

**1–1.5 days**

---

## Phase 7: Exploration Interface

**Goal:** Let the PM search evidence and ask discovery questions, with answers built only from stored evidence and drawn from diverse sources.

**Maps to problem statement:**
- §17 Exploration interface: the 11 example PM questions
- §17 RAG / vector search: semantic + behavioural relevance, source diversity, structured filters

### Tasks

#### 7.1 Evidence index

| # | Task | File(s) |
|---|------|---------|
| 7.1.1 | TF-IDF index (1–2 grams, sublinear) over current, non-duplicate chunks | `discovery_engine/search.py` |
| 7.1.2 | `Filters`: sources, scenarios, failure stages, status, perspective, remembered (all), forgotten (all), workarounds/behaviours/opportunities (any), attempts only, provenance, date range | `discovery_engine/search.py` |
| 7.1.3 | MMR re-ranking with source (0.15) and thread (0.20) diversity penalties | `discovery_engine/search.py` |

#### 7.2 Question interface

| # | Task | File(s) |
|---|------|---------|
| 7.2.1 | `Plan` schema with 11 intents and filters | `discovery_engine/ask.py` |
| 7.2.2 | Rule-based question parser (offline) | `discovery_engine/ask.py` |
| 7.2.3 | Claude plan parser when credentials exist, falling back to rules on error | `discovery_engine/ask.py` |
| 7.2.4 | Deterministic answer assembly: tables, comparisons, contradictions, hypotheses or evidence | `discovery_engine/ask.py` |
| 7.2.5 | CLI: `python -m discovery_engine ask "question"` | `discovery_engine/__main__.py` |

### Deliverables

- [x] Diversified evidence search with structured filters
- [x] All 11 example questions from the problem statement answered with evidence

### Acceptance Criteria

- The LLM only produces the plan; every number and quote comes from stored evidence.
- Top results span multiple sources where matches exist.
- Label filters are strictly honoured.

### Estimated effort

**1–1.5 days**

---

## Phase 8: API and Dashboard

**Goal:** Give the PM a local, inspectable interface: overview through drill-down, raw evidence next to AI interpretation, and the ability to challenge the AI.

**Maps to problem statement:**
- §17 Discovery dashboard sections
- §18 Human in the loop; auditability (opportunity → insight → pattern → evidence)

### Tasks

#### 8.1 API

| # | Task | File(s) |
|---|------|---------|
| 8.1.1 | `GET /api/bundle`, `POST /api/rebuild` | `discovery_engine/server.py` |
| 8.1.2 | `GET /api/record/{id}`: raw evidence, AI interpretation, signals, overrides, analysis history | `discovery_engine/server.py` |
| 8.1.3 | `POST /api/search`, `POST /api/ask` | `discovery_engine/server.py` |
| 8.1.4 | `POST /api/override` with an editable-field whitelist (400 otherwise) | `discovery_engine/server.py` |
| 8.1.5 | `GET /api/report.md`, `GET /api/brief.md` | `discovery_engine/server.py` |
| 8.1.6 | CLI: `python -m discovery_engine serve [--port]` | `discovery_engine/__main__.py` |

#### 8.2 Dashboard

| # | Task | File(s) |
|---|------|---------|
| 8.2.1 | Tabs: Overview, Scenarios, Remembered, Forgotten, Search formulation, Failures & journey, Workarounds, Segments, Opportunities, Hypotheses & brief, Explore & ask | `discovery_engine/web/index.html` |
| 8.2.2 | Sortable comparison tables for scenarios, segments and opportunities | `discovery_engine/web/index.html` |
| 8.2.3 | Heatmaps: scenario × forgotten, scenario × failure | `discovery_engine/web/index.html` |
| 8.2.4 | Opportunity drill-down: insights → patterns → evidence chain → challenging evidence → unresolved questions → strength checks | `discovery_engine/web/index.html` |
| 8.2.5 | Record modal: raw vs AI side by side; *challenge* a field, *reject* a signal | `discovery_engine/web/index.html` |
| 8.2.6 | Light and dark themes, hover tooltips with numerator/denominator/sources, URL-hash tabs, provenance banner | `discovery_engine/web/index.html` |

### Deliverables

- [x] Every endpoint responds in the smoke test
- [x] Dashboard renders all tabs (checked via headless screenshots)
- [x] Corrections stored and applied after Rebuild

### Acceptance Criteria

- An invalid override field returns HTTP 400.
- Every number in the UI shows its denominator on hover.
- Any opportunity can be traced to a source record in at most four clicks.

### Estimated effort

**2 days**

---

## Phase 9: Test Data and Evaluation

> **Status:** superseded for data by Phase 11. The generator and evaluator remain in the codebase for tests. `data/synthetic/` is no longer ingested.

**Goal:** Provide a seeded, labelled development dataset with a separate answer key, to exercise the pipeline and score analyzer accuracy.

**Maps to problem statement:**
- §8 Sources: 120 rows each for Play Store, App Store, Reddit, Google Photos Community, social media, YouTube, forums
- §18 No fabrication: generated data must be labelled as such

### Tasks

#### 9.1 Generator

| # | Task | File(s) |
|---|------|---------|
| 9.1.1 | Content pools: ~70 memory episodes across 17 scenarios, plus noise, advice, opinion, success and misattribution pools | `discovery_engine/synthetic/episodes.py` |
| 9.1.2 | Per-source mix of row kinds (each sums to 120) | `discovery_engine/synthetic/generate.py` |
| 9.1.3 | Platform renderers for the 7 sources | `discovery_engine/synthetic/generate.py` |
| 9.1.4 | Output: per-source JSONL, combined JSONL/CSV, flat inspection CSV, `ground_truth.jsonl`, README | `data/synthetic/` |
| 9.1.5 | CLI: `generate-synthetic [--per-source] [--seed]`, `demo` | `discovery_engine/__main__.py` |

#### 9.2 Evaluation

| # | Task | File(s) |
|---|------|---------|
| 9.2.1 | Relevance and attempt precision/recall/F1 | `discovery_engine/evaluate.py` |
| 9.2.2 | Exact-match accuracy: scenario, status, failure stage | `discovery_engine/evaluate.py` |
| 9.2.3 | Multi-label P/R/F1: remembered, forgotten, workarounds, segments, query types; failure-stage confusion matrix | `discovery_engine/evaluate.py` |

### Deliverables

- [x] 840 rows, 120 per source, reproducible from the seed
- [x] Answer key kept separate from analyzer input
- [x] Evaluation run; heuristic bugs found and fixed (outcome accuracy 0.68 → 1.00; attempt detection 0.85 → 0.97)

### Acceptance Criteria

- Analyzers never see the answer key.
- Scores are reported with a caveat that template text inflates accuracy.

### Estimated effort

**1.5 days**

---

## Phase 10: Tests and Docs

**Goal:** Lock in the guardrails with automated tests, and document how to run, extend and trust the engine.

**Maps to problem statement:**
- §20 Success criteria
- §18 Guardrails

### Tasks

#### 10.1 Tests

| # | Task | File(s) |
|---|------|---------|
| 10.1.1 | Quote validation (verbatim, whitespace-tolerant, elision) | `tests/test_engine.py` |
| 10.1.2 | Unknown labels → `proposed:*`; fabricated quotes excluded | `tests/test_engine.py` |
| 10.1.3 | Rate helper denominators and directional flag | `tests/test_engine.py` |
| 10.1.4 | PII scrub, chunking, dedupe, idempotent ingest | `tests/test_engine.py` |
| 10.1.5 | Generator counts and labels; heuristic quotes verbatim; noise not relevant | `tests/test_engine.py` |
| 10.1.6 | Leading interview questions filtered | `tests/test_engine.py` |
| 10.1.7 | End-to-end pipeline: strength levels, record counts, banners, brief has no findings | `tests/test_engine.py` |
| 10.1.8 | Search diversity and label filters; overrides apply on read | `tests/test_engine.py` |

#### 10.2 Documentation

| # | Task | File(s) |
|---|------|---------|
| 10.2.1 | Setup, commands, evidence flow, analyzers, privacy | `README.md` |
| 10.2.2 | Problem definition and scope decisions | `problemstatement.md` |
| 10.2.3 | Phase-by-phase architecture | `architecture.md` |
| 10.2.4 | This plan | `implementationplan.md` |

### Deliverables

- [x] `python -m pytest -q tests` → 13 passed
- [x] Tests use temporary databases and never touch `data/discovery.db`
- [x] All four documents current

### Acceptance Criteria

- The full test suite passes after any change to Phases 1–8.
- The docs describe the code as built.

### Estimated effort

**1 day**

---

## Phase 11: Raw Dataset `google_photos_discovery_annotated`

**Goal:** Make `google_photos_discovery_annotated.xlsx` the engine's single source of data, ignore all earlier datasets, rebuild every output from it, and keep its annotations independent so they can check the engine.

**Maps to problem statement:**
- §22 Project scope decisions: single source of data, role of the annotations
- §22.1–§22.5 Dataset profile, annotation columns, cross-check, missing fields, provenance note

**Input:** `google_photos_discovery_annotated.xlsx`, sheet `Sheet1`.
- 840 rows × 8 columns: `source`, `id`, `text`, `retrieval_intent`, `retrieval_scenario`, `retrieval_object`, `memory_clues`, `forgotten_information`.
- 120 rows per source, unique IDs, no missing values, no date column.
- Text 48–886 characters; 72 exact duplicate texts.

### Tasks

#### 11.1 Profiling and provenance

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 11.1.1 | Locate the file; the Downloads copy and project-folder copy were confirmed identical, and the project-folder copy is used | `google_photos_discovery_annotated.xlsx` | ✅ |
| 11.1.2 | Profile sheets, columns, types, nulls, per-source counts, ID uniqueness, duplicates, text length | xlsx | ✅ |
| 11.1.3 | Profile annotation columns: value counts, single vs `;`-separated multi-value | xlsx | ✅ |
| 11.1.4 | Provenance check against earlier generator output: 840 of 840 texts identical; recorded in problem statement §22.5 as the audit trail | — | ✅ |

#### 11.2 Conversion and rebuild

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 11.2.1 | Convert to CSV (UTF-8); verify every cell (840 × 8) against the xlsx | `google_photos_discovery_annotated.csv` | ✅ |
| 11.2.2 | Stop the workspace server (it holds the database open) and delete the old database | `data/discovery.db` | ✅ |
| 11.2.3 | Ingest `source`, `id`, `text` with `--dataset google_photos_discovery_annotated`, **no provenance flag**, so outputs stay neutral; annotation columns not ingested | `ingest.py` (unchanged) | ✅ |
| 11.2.4 | Analyze (heuristic), synthesize, regenerate report and brief | `reports/` | ✅ |
| 11.2.5 | Restart the workspace and confirm it serves the new bundle | `server.py` | ✅ |

#### 11.3 Annotation cross-check

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 11.3.1 | Join annotations to engine labels by `record_id`; compare relevance (725/745 agree, 97.3%) | ad-hoc script | ✅ |
| 11.3.2 | Review the 20 relevance disagreements record by record | Review queue | ⏳ Open |
| 11.3.3 | Draft a mapping from annotation categories to engine labels (scenario, object, memory clues, forgotten information); get PM sign-off | `evals.md` §3 | ⏳ Open |
| 11.3.4 | Turn the mapped annotations into an answer key and run `evaluate` | `data/eval/`, `evaluate.py` | ⏳ Open |
| 11.3.5 | Add a committed script for the cross-check so it can be re-run after re-analysis | `discovery_engine/` | ⏳ Open |

#### 11.4 Documentation

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 11.4.1 | README quick start uses the new dataset | `README.md` | ✅ |
| 11.4.2 | Problem statement §22 rewritten for the new dataset | `problemstatement.md` | ✅ |
| 11.4.3 | Architecture Phase 11 rewritten | `architecture.md` | ✅ |
| 11.4.4 | Rebuild `edgecases.md` (section 10 raw-dataset cases) and `evals.md` (annotations as reference labels, draft mapping, first measurements) | `edgecases.md`, `evals.md` | ✅ |

#### 11.5 Follow-ups

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 11.5.1 | Re-analyse with Claude once credentials exist (`analyze --analyzer claude --reanalyze`) and compare against the annotations | CLI | ⏳ Open |

### Commands

```bash
# from the project root; stop the server and delete data/discovery.db first for a clean rebuild
python -m discovery_engine ingest google_photos_discovery_annotated.csv --dataset google_photos_discovery_annotated
python -m discovery_engine analyze
python -m discovery_engine synthesize
python -m discovery_engine serve --port 8931
```

### Current run (heuristic analyzer)

| Metric | Value |
|---|---|
| Records in database | 840 (dataset `google_photos_discovery_annotated` only) |
| Duplicates marked | 95 (77 exact, 18 near) |
| Unique records analysed | 745 |
| Relevant to retrieval | 577 / 745 |
| First-person retrieval attempts | 552 |
| Quotes extracted / failed verbatim check | 11,119 / 0 |
| Relevance agreement with annotations | 725 / 745 (97.3%) |
| Strongest opportunity | `index_coverage_gaps` (HIGH); the other seven are MEDIUM |
| Proposed lead / runner-up | `approximate_time_anchoring` / `candidate_recognition` |

### Deliverables

- [x] `google_photos_discovery_annotated.csv`, identical to the xlsx in every cell
- [x] Database containing only `google_photos_discovery_annotated`
- [x] Reports, brief and workspace rebuilt from this dataset alone
- [x] Relevance cross-check against annotations
- [ ] Reviewed annotation → engine label mapping
- [ ] Extraction scored against mapped annotations
- [ ] Claude analysis run

### Acceptance Criteria

- Database contains exactly one dataset, `google_photos_discovery_annotated`, with 840 records.
- Annotation columns are never used as analyzer input.
- Duplicates are marked, not deleted; 745 unique records analysed.
- 0 invalid quotes across all extracted evidence.
- Outputs name the dataset and make no claim about its origin; the pre-ingest check is recorded in problem statement §22.5.

### Dataset limitations carried into outputs

| Missing field | Consequence |
|---|---|
| Date | No date range, time filters or trends |
| Title, platform detail, thread context, replies | Less context per record; more duplicates; source-level comparison only |
| Source URL | Evidence traced by `record_id`, not by link |
| Engagement | Severity can't be weighted by upvotes, likes or ratings |

### Estimated effort

**0.5 day** (done), plus **1.5–2 days** for the open cross-check and evaluation tasks

---

## Phase 12: Discovery Workspace (UI/UX)

**Goal:** Replace the single-page dashboard with a workspace that follows the discovery chain. It should let a PM trace any number to its quotes, question the AI in place, and leave with a research plan.

**Maps to problem statement:**
- §17 Discovery dashboard and exploration interface
- §18 Human in the loop; auditability
- §20 Success criteria 1–12 (each answerable from a view)

### Tasks

#### 12.1 Shell and design system

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 12.1.1 | App shell: grouped sidebar (Understand / Decide / Hand off / Investigate), top bar with breadcrumbs, ask trigger, provenance pill, Rebuild, theme toggle | `web/index.html` | ✅ |
| 12.1.2 | Design tokens for light and dark themes; dataviz reference palette; sequential ramp; components | `web/styles.css` | ✅ |
| 12.1.3 | Hash router with deep links for every view and opportunity | `web/app.js` | ✅ |
| 12.1.4 | Serve static assets; keep the old dashboard at `/classic` | `server.py` | ✅ |

#### 12.2 Views

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 12.2.1 | Overview: KPI tiles, evidence funnel, proposed lead with margin and close-call flag, six discovery-question cards, journey strip, outcomes, sources | `web/app.js` | ✅ |
| 12.2.2 | Retrieval journey: stage cards, breakdowns with definitions, workarounds, scenario × breakdown heatmap | `web/app.js` | ✅ |
| 12.2.3 | Memory gap: remembered vs forgotten, dumbbell association chart, exact/approximate, scenario × forgotten heatmap | `web/app.js` | ✅ |
| 12.2.4 | Search behaviour: query types, orientation, outcome by query type, strategies, verbatim queries | `web/app.js` | ✅ |
| 12.2.5 | Scenarios and Segments: sortable comparison tables; segment profile drawer (selection criteria added in Phase 13.2) | `web/app.js` | ✅ |
| 12.2.6 | Opportunities: numbered map with ranked legend, comparison table; detail page with evidence chain, insights, strength checks, contradictions, unknowns | `web/app.js` | ✅ |
| 12.2.7 | Research plan: target segment, screener, hypothesis cards, JTBD, copyable interview guide, checklists, downloads (Method and Problem definition tabs added in Phase 13) | `web/app.js` | ✅ |
| 12.2.8 | Ask & explore: question box, suggestions, answers showing how the question was read, faceted evidence search | `web/app.js` | ✅ |
| 12.2.9 | Review queue: needs review, proposed labels, quote failures, correction log | `web/app.js`, `server.py` (`/api/review`) | ✅ |

#### 12.3 Evidence interaction

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 12.3.1 | Drill-down from every bar, cell, stage, row and bubble to matching records | `web/app.js` | ✅ |
| 12.3.2 | Evidence inspector drawer: raw text with quotes highlighted by signal kind, AI interpretation, signals, history; stacked back navigation | `web/app.js` | ✅ |
| 12.3.3 | Challenge a field / reject a signal with a required reason; toast with Rebuild | `web/app.js`, `server.py` (`/api/meta`) | ✅ |
| 12.3.4 | Ask palette (Ctrl+K, `/`) for questions and navigation | `web/app.js` | ✅ |
| 12.3.5 | Readable narrative text: rewrite backend labels and dict strings for display only | `web/app.js` | ✅ |

#### 12.4 Quality

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 12.4.1 | Browser tests: every view × light/dark, key interactions, mobile overflow, console and page errors | `tools/ui_check.py` | ✅ 55/55 |
| 12.4.2 | Screenshot review; fix bar fills, hidden-form boxes, duplicate check markers, raw labels, map label collisions, focus artefact | `web/styles.css`, `web/app.js` | ✅ |
| 12.4.3 | Fix research brief missing hypotheses for lead/runner-up; regression test | `report.py`, `tests/test_engine.py` | ✅ |
| 12.4.4 | Commit the browser test script to the repo | `tools/ui_check.py` | ✅ (Phase 13.5.1) |
| 12.4.5 | Neutral provenance presentation: `DE_PROVENANCE` / `--provenance` (auto \| neutral); dataset ingested without a flag, so the workspace pill and reports name the dataset only | `config.py`, `report.py`, `web/app.js` | ✅ |

### Deliverables

- [x] Workspace at `/` with 11 views, drawer, palette and review queue
- [x] Light and dark themes; responsive to 390 px; keyboard accessible
- [x] Every number traceable to quotes in at most two clicks
- [x] `/api/meta` and `/api/review` endpoints
- [x] Browser tests committed (`tools/ui_check.py`); CI wiring still open

### Acceptance Criteria

- No console or page errors on any view in either theme.
- Every rate shows its percentage and numerator/denominator, with the denominator definition on hover.
- A PM can challenge any analysis field or reject any signal from the inspector, with a reason stored in the audit log.
- No horizontal page scroll at 390 px width.

### Estimated effort

**2.5–3 days**

---

## Phase 13: Metric Decomposition, Methodology and Problem Definition

**Goal:** Take the evidence the last three steps of the case study: break the business metric into product outcomes (Part 2), state the research method and why it beats the alternatives (Part 3), and draft the problem definition with its evolution chain (Part 4). Problem spaces only - no feature ever leaves this phase.

**Maps to problem statement:**
- §16 Opportunity areas as problem spaces; §18 guardrails and epistemic labels
- §19 Research handoff; §20 Success criteria 5, 6, 8, 9, 12
- Case study Parts 2, 3 and 4

### Tasks

#### 13.1 Part 2 - break down the business metric

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 13.1.1 | Map failure codes to journey stages; keep data/index separate as "not a user stage" | `decomposition.py` | ✅ |
| 13.1.2 | Phrase the product outcome each stage would move, as an outcome and never a feature | `decomposition.py` | ✅ |
| 13.1.3 | Measure baseline, breaks-here, still-unresolved and max headroom per stage; rank by recoverable share | `decomposition.py` | ✅ |
| 13.1.4 | Label headroom `INTERPRETATION` and carry its assumption wherever it is shown | `decomposition.py`, `web/app.js`, `report.py` | ✅ |
| 13.1.5 | Attach the opportunity areas that sit under each stage, with counts | `decomposition.py` | ✅ |
| 13.1.6 | Decomposition card leads the Opportunities page; rows drill to the attempts behind each stage | `web/app.js` | ✅ |
| 13.1.7 | Report §2 becomes the measured decomposition table | `report.py` | ✅ |

#### 13.2 Choosing the target segment

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 13.2.1 | State the comparison criteria on the Segments page, including that size alone is not a reason | `web/app.js` | ✅ |
| 13.2.2 | `study` / `target_segment` override target; **Select** in the table and the segment drawer | `server.py`, `web/app.js` | ✅ |
| 13.2.3 | Read the chosen segment on rebuild; mark it "Chosen by you" in the plan | `store.py`, `report.py`, `web/app.js` | ✅ |
| 13.2.4 | Fall back to the coverage-based recruitment mix when nothing is chosen | `report.py` | ✅ |

#### 13.3 Part 3 - methodology

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 13.3.1 | Method, reasoning, participants, five-step session plan | `problem.py` | ✅ |
| 13.3.2 | Four alternatives considered, each with why it was not chosen | `problem.py` | ✅ |
| 13.3.3 | What to capture per episode, coded in the engine's taxonomy so results compare | `problem.py` | ✅ |
| 13.3.4 | Analysis plan, ethics and privacy, validity threats with mitigations | `problem.py` | ✅ |
| 13.3.5 | Method tab in the workspace; methodology section in the handed-off brief | `web/app.js`, `report.py` | ✅ |

#### 13.4 Part 4 - problem definition

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 13.4.1 | Nine fields, each with an epistemic level, evidence and a settling question where relevant | `problem.py` | ✅ |
| 13.4.2 | Root cause as `HYPOTHESIS` with its chain, never stated as a finding | `problem.py` | ✅ |
| 13.4.3 | "What this problem is not": explicitly rules out "users find it difficult to search for old photos" | `problem.py` | ✅ |
| 13.4.4 | Business rationale tied to the measured headroom, with the questions public posts cannot answer | `problem.py` | ✅ |
| 13.4.5 | Five-step evolution chain: business metric -> product outcomes -> AI-powered discovery -> observed user behaviour -> problem definition | `problem.py`, `web/app.js` | ✅ |
| 13.4.6 | Problem definition tab; report §15 | `web/app.js`, `report.py` | ✅ |

#### 13.7 Research fit per segment, and the methodology behind it

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 13.7.1 | Measure content sensitivity per segment; flag when it is definitional | `research.py` | ✅ |
| 13.7.2 | Measure segment overlap (containment), so a choice is not made between near-identical groups | `research.py`, `synthesis.py` (`record_ids`) | ✅ |
| 13.7.3 | Derive recruitability and observability from the segment's definition, with the rule exposed | `research.py` | ✅ |
| 13.7.4 | Generate a segment-specific screener: incident qualifier, must-be-yes, capture, insider exclusion, consent where sensitive | `research.py` | ✅ |
| 13.7.5 | Derive what changes in the session (time balance, screen-share policy) | `research.py` | ✅ |
| 13.7.6 | Replace the retrospective-only method with the hybrid study, and record the old plan as a rejected alternative | `problem.py` | ✅ |
| 13.7.7 | State what each part of the session buys; add the clue delta and resolution coding to instrumentation and analysis | `problem.py` | ✅ |
| 13.7.8 | Brief takes the chosen segment's screener and session adaptation | `report.py` | ✅ |
| 13.7.9 | Research fit column on the Segments table, full section in the drawer, adaptation card on the Method tab (with an explicit "no segment chosen" state) | `web/app.js` | ✅ |
| 13.7.10 | 12 mission checks and 5 browser checks for the above | `tools/` | ✅ 69/69, 60/60 |

#### 13.6 Five-stage retrieval journey

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 13.6.1 | Replace the seven-step journey with Recall → Express → Match → Recognize → Recover | `taxonomy.py`, `models.py` | ✅ |
| 13.6.2 | Re-map failure codes: B and C both land on Match; D on Recognize; E on Recover; F stays outside the journey | `decomposition.py`, `analyze/heuristic.py` | ✅ |
| 13.6.3 | Keep the merged stage auditable: `STAGE_COMPONENTS` reports B and C counts on the Match row | `decomposition.py`, `web/app.js` | ✅ |
| 13.6.4 | State each stage as a user capability (`STAGE_CONDITION`), shown as a chain strip, row tooltips and a numbered list in report §2 | `decomposition.py`, `web/app.js`, `report.py` | ✅ |
| 13.6.5 | Show every journey stage, including ones with no measured breakdowns (closes EC-DEC-03) | `web/app.js`, `report.py` | ✅ |
| 13.6.6 | Re-analyse the corpus so stored journey signals use the new vocabulary | `data/discovery.db` | ✅ 745 chunks, 0 invalid quotes |
| 13.6.7 | Four mission checks for the model (order, conditions, data outside the journey, components reconcile) | `tools/mission_check.py` | ✅ |

#### 13.5 Quality

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 13.5.1 | Commit the mission and browser check scripts to the repo | `tools/mission_check.py`, `tools/ui_check.py` | ✅ |
| 13.5.2 | 18 new mission checks for Parts 2-4 (share reconciliation, levels, banned framing, chain), plus the §18 solution-language check extended to stage outcomes and problem fields | `tools/mission_check.py` | ✅ |
| 13.5.3 | 15 new browser checks (decomposition rows and drill, segment criteria and selection, three research tabs) | `tools/ui_check.py` | ✅ |
| 13.5.4 | Screenshot review; fix doubled DRAFT banner, clipped Select column, thin scenario statement | `web/app.js`, `web/styles.css`, `problem.py` | ✅ |

### Deliverables

- [x] `bundle.decomposition`, `bundle.target_segment`, `bundle.problem_definition`, `research_brief.methodology`
- [x] Opportunities page led by the metric decomposition; Segments page with criteria and selection; Research plan with three tabs
- [x] Report §2 and §15; methodology in the brief
- [x] `tools/mission_check.py` and `tools/ui_check.py` in the repo

### Acceptance Criteria

- Stage shares plus "no breakdown" and "unclear" reconcile against the attempt denominator.
- Headroom is never presented as a forecast, in any surface.
- Every problem-definition field carries an epistemic level, and the root cause is a hypothesis with the question that settles it.
- The problem is not framed as "users find it difficult to search for old photos"; that framing appears only where it is ruled out.
- The evolution chain runs from the business metric to the problem definition in five traceable steps.

### Estimated effort

**1.5-2 days**

---

## Phase 14: Behavioural Segmentation

**Goal:** Scrap the old Segments page. One primary segmentation by retrieval behaviour (Direct, Contextual, Candidate-Heavy, Recovery), with memory state, retrieval complexity and outcome/effort as secondary lenses across it.

**Maps to problem statement:** §20 criterion 8 (which segments are most affected); case study Part 2 (where the opportunity is) and Part 3 (who to interview).

### Tasks

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 14.1 | Behaviour flags per attempt from extracted signals, with the triggering signals kept for audit | `behavior_segments.py` | ✅ |
| 14.2 | Primary placement by precedence; test "most effortful wins", reject it on the evidence (Recovery 72.5%, Candidate-heavy 8), adopt Candidate-heavy > Recovery > Direct > Contextual | `behavior_segments.py` | ✅ |
| 14.3 | Read samples from every segment; fix the Direct flag firing on descriptive searches that worked | `behavior_segments.py` | ✅ |
| 14.4 | Unclassified remainder with reasons (outside the library / no signal) | `behavior_segments.py` | ✅ |
| 14.5 | Fix the analyzer: success stated from the system's side; negated "never found it" outcomes | `analyze/heuristic.py` | ✅ re-analysed 745 chunks, 0 invalid quotes |
| 14.6 | Secondary lenses: memory state, retrieval complexity, outcome/effort, overall and within each segment | `behavior_segments.py`, `synthesis.py` | ✅ |
| 14.7 | Remove two lens artefacts: typed clues count as memory held; find rates exclude unstated outcomes; show "photo not there" per category | `behavior_segments.py`, `synthesis.py` | ✅ |
| 14.8 | Research fit for the four segments: role, recruiting, observability, sensitivity, co-occurrence, screener, session shape | `research.py` | ✅ |
| 14.9 | Recruitment mix from the behavioural segments; stale target choice set aside with a warning (closes EC-DEC-07) | `report.py` | ✅ |
| 14.10 | Record-set drill-down for segments and lens cells | `search.py`, `web/app.js` | ✅ |
| 14.11 | New Segments page and drawer; lens heat tables on the sequential ramp per the dataviz method | `web/app.js`, `web/styles.css` | ✅ |
| 14.12 | Report §10 rewritten with the lenses | `report.py` | ✅ |
| 14.13 | Replace the orphaned two-axis "modes" checks (their code no longer exists) with 16 segmentation checks and 12 browser checks | `tools/` | ✅ 85/85, 69/69 |
| 14.14 | Audit Recovery against its definition: require a failed first attempt; fix the "next week" return-later false positive; add a check that recomputes the rule | `behavior_segments.py`, `analyze/heuristic.py`, `tools/mission_check.py` | ✅ 326 → 285 (59.1% → 51.6%), 86/86 |
| 14.15 | Revise to the NextLeap binary model: primary segmentation becomes Direct vs Contextual only (exhaustive, no precedence rule, no unclassified remainder); Candidate-heavy and Recovery move from primary segments into a new Retrieval State secondary lens (`direct_low_effort`, `candidate_heavy`, `recovery_dependent`, `unresolved`, `unavailable`) | `behavior_segments.py`, `synthesis.py` | ✅ |
| 14.16 | Redefine retrieval complexity to combine clue count with clue precision (low/medium/high), so it separates "Rahul, Goa" from "that café, blue chairs, sometime" the way count alone cannot | `behavior_segments.py` | ✅ |
| 14.17 | Add `IMPACT_MAP` (WHY/WHO/HOW/WHAT) and `TARGET_SEGMENT_HYPOTHESIS`; surface both in report §10 and the Segments page | `behavior_segments.py`, `report.py`, `web/app.js` | ✅ |
| 14.18 | Split research fit into per-primary-segment (`research_fit`) and per-retrieval-state (`research_fit_by_state`), reusing the Candidate-heavy/Recovery interview guidance at the state level | `research.py`, `report.py` | ✅ |
| 14.19 | Update `mission_check.py`'s segmentation and Part 3 checks for the binary model; found and fixed a scope mismatch (`Corpus(s, True)` hardcoded instead of matching the loaded bundle's own `include_synthetic`) that was inflating the Recovery-dependent count | `tools/mission_check.py` | ✅ 84/91 (7 remaining failures are pre-existing gaps unrelated to this revision - see Verification note under Phase 14 in `architecture.md`) |

### Acceptance Criteria

- Every attempt sits in exactly one of the two primary segments (Direct or Contextual); the two always sum to 100% of attempts.
- Every attempt has exactly one Retrieval State (direct/low-effort, candidate-heavy, recovery-dependent, unresolved or unavailable), assigned by a stated precedence rule.
- Each secondary lens (memory state, retrieval complexity, retrieval state) places every attempt once, overall and within each segment.
- Find rates by lens never count posts with no stated outcome as failures.
- Every number on the page drills into exactly the attempts behind it.
- Impact mapping (WHY/WHO/HOW/WHAT) and the target-segment hypothesis are present in both the report and the Segments page, and WHAT names candidate directions without choosing one.

### Estimated effort

**1.5-2 days**

---

## Summary Timeline

| Phase | Effort | Cumulative | Status |
|---|---|---|---|
| 0 Foundation | 0.5–1 d | 1 d | ✅ |
| 1 Ingestion | 0.5–1 d | 2 d | ✅ |
| 2 Analysis layer | 2–3 d | 5 d | ✅ (Claude run open) |
| 3 Evidence validation | 1 d | 6 d | ✅ |
| 4 Quantitative synthesis | 1–1.5 d | 7.5 d | ✅ |
| 5 Segments & opportunities | 1.5–2 d | 9.5 d | ✅ |
| 6 Hypotheses & handoff | 1–1.5 d | 11 d | ✅ |
| 7 Exploration | 1–1.5 d | 12.5 d | ✅ |
| 8 API & dashboard | 2 d | 14.5 d | ✅ |
| 9 Test data & evaluation | 1.5 d | 16 d | ✅ (superseded for data) |
| 10 Tests & docs | 1 d | 17 d | ✅ |
| 11 Raw dataset | 0.5 d (+1.5–2 d open evaluation work) | 17.5 d | ✅ (5 open items) |
| 12 Discovery workspace | 2.5–3 d | 20.5 d | ✅ (1 open item: CI wiring) |
| 13 Decomposition, methodology, problem definition | 2.5–3 d | 23.5 d | ✅ |
| 14 Behavioural segmentation | 1.5–2 d | 25.5 d | ✅ |

---

## Known Limitation to State in Every Output

Outputs must describe the raw dataset `google_photos_discovery_annotated` accurately, including its provenance note (problem statement §22.5). Patterns found in it are research hypotheses: they show where to look in the 5–6 interviews, and are validated only through that primary research.
