# Evals: AI-Powered Discovery Engine

> Covers how we measure whether the engine's evidence, numbers and conclusions can be trusted, what has been measured on the raw dataset `google_photos_discovery_annotated`, and what still needs to run.
> Related: [edgecases.md](edgecases.md) · [architecture.md](architecture.md) · [implementationplan.md](implementationplan.md) · [problemstatement.md](problemstatement.md) §22

---

## 1. Why Evals Matter Here

The engine's output decides which problem goes into user interviews. A wrong label changes a count, a count changes an evidence-strength level, and a strength level can change the leading opportunity. So the evals check more than extraction accuracy. They check whether the **conclusions** hold up.

| Question | Eval families |
|---|---|
| Does the engine extract the right facts from each conversation? | E1 Ingestion, E2 Extraction quality |
| Is every claim grounded in what the text actually says? | E3 Grounding, E4 Guardrails |
| Are the conclusions stable, or artefacts of thresholds and noise? | E5 Synthesis robustness, E6 Contradiction recall |
| Can a PM find and question the evidence? | E7 Search, E8 Ask, E9 Discovery workspace |
| Is the Claude analyzer affordable and reliable at scale? | E10 Claude operations |

### Status legend

| Status | Meaning |
|---|---|
| ✅ Automated | Runs in `pytest` or a CLI command today |
| 🟢 Scripted | Runs from a committed script in `tools/` (`mission_check.py`, `ui_check.py`); not yet in CI |
| 🟡 Measured once | Run with recorded results; not yet automated |
| ⬜ Proposed | Designed here; not yet built or run |

---

## 2. Eval Datasets

| Dataset | Contents | Used for | Status |
|---|---|---|---|
| **Raw dataset annotations** | `google_photos_discovery_annotated`: 5 annotation columns on 840 rows (745 unique after dedupe) | Reference labels for relevance, scenario, object, memory clues, forgotten information (§3–§4) | 🟡 Measured once with a **draft** mapping |
| **Raw dataset hand-label sample** | 100 unique records, labelled for fields the annotations don't cover: attempt, outcome, failure stage, workarounds, query type | E2.6–E2.10 | ⬜ |
| **Annotation reliability sample** | The same 100 records, re-annotated independently on the 5 annotation columns | Measures how trustworthy the annotations are (E2.11) | ⬜ |
| **Unit fixtures** | Hand-written snippets in `tests/test_engine.py` (fabricated quotes, PII strings, duplicates, noise) | E1, E3, E4 unit checks | ✅ |
| **Legacy answer key** | Generator ground truth from the legacy synthetic set | Regression baseline for the heuristic analyzer only (§4.3) | 🟡 Legacy |
| **Edge-case probes** | Probes in [edgecases.md](edgecases.md) | Regression checks | 🟡 Run 2026-09-17 |
| **Planted-evidence set** | Copy of the raw dataset plus hand-written counter-evidence records tagged `eval_planted` | E6 contradiction recall | ⬜ |
| **Ask question set** | 11 example questions from the problem statement + 3 paraphrases each (44), with expected plans | E8 | 🟡 11 originals smoke-tested |

**Rules**
- Annotations and hand labels are **never analyzer input**. They are joined to engine output by `record_id = source:id` after analysis.
- Eval-only records (planted records, re-annotations) go into a separate database via `--db`, never `data/discovery.db`.
- Only canonical (non-duplicate) records are scored. Duplicate texts always carry identical annotations (EC-RAW-04), so no annotation information is lost.

---

## 3. Using the Annotations as Reference Labels

### 3.1 Coverage

| Engine output | Annotation column | Covered? |
|---|---|---|
| `relevant` | `retrieval_intent` | ✅ Direct |
| `retrieval_scenario` (19 labels) | `retrieval_scenario` (5 categories + Not stated) | ⚠️ Coarse: needs many-to-one mapping |
| `retrieval_object` | `retrieval_object` | ✅ Near-direct |
| `remembered` signals (15 labels) | `memory_clues` (4 categories, multi-value) | ⚠️ Coarse |
| `forgotten` signals (10 labels) | `forgotten_information` (4 categories, multi-value) | ⚠️ Coarse |
| `describes_retrieval_attempt`, `success_status`, `failure_stage`, workarounds, queries, segments | — | ❌ Needs the hand-label sample |

### 3.2 Scoring rules

1. **Gate on intent.** Compare scenario, object, memory clues and forgotten information only where **both** the annotation and the engine say retrieval-related. 56 "Not retrieval-related" rows still have an object filled in (EC-RAW-06), so ungated comparison would penalise noise.
2. **"Not stated" means empty.** It is never scored as a label.
3. **Multi-value fields** are split on `;` (the only separator used) and scored as multi-label sets: micro precision, recall and F1, plus per category.
4. **Engine labels are mapped up** to annotation categories. The comparison always happens at the annotation's coarser granularity.
5. **Report per source** as well as overall, so a weak platform isn't hidden by the average.

### 3.3 Draft label mapping (needs PM sign-off)

> This mapping is a **draft** written to get a first measurement. Scores in §4 change if it changes. Review it before treating any number as a target.

| Annotation category | Engine labels mapped to it |
|---|---|
| **Scenario:** Event memory | `event_memory`, `wedding_memory`, `school_or_college_memory` |
| **Scenario:** Person-related memory | `family_memory`, `friend_memory`, `personal_memory`, `social_memory` |
| **Scenario:** Document / screenshot retrieval | `document`, `receipt`, `screenshot`, `medical_or_health_image`, `purchase_related_image` |
| **Scenario:** Trip / experience memory | `travel_memory`, `food_restaurant_memory`, `location_memory` |
| **Scenario:** General photo/media retrieval | `object_memory`, `work_memory`, `video`, `other` |
| **Object:** Photo/image · Video · Screenshot · Document · Not stated | `photo` (and `multiple`) · `video` · `screenshot` · `document_or_receipt` · `unknown` |
| **Memory:** person/relationship | `remembered_person`, `remembered_relationship`, `remembered_social_context` |
| **Memory:** time/date reference | `remembered_time_approximation` |
| **Memory:** place/trip/experience context | `remembered_place`, `remembered_trip`, `remembered_event`, `remembered_occasion`, `remembered_activity` |
| **Memory:** document/screenshot context | `remembered_text`, `remembered_context` |
| **Forgotten:** date/time | `exact_date_unknown` |
| **Forgotten:** location | `exact_location_unknown` |
| **Forgotten:** exact wording/name | `exact_text_unknown`, `person_name_unknown`, `event_name_unknown`, `exact_object_name_unknown`, `exact_keyword_unknown` |
| **Forgotten:** specific retrieval detail | `album_unknown`, `filename_unknown`, `metadata_unknown` |

**Questions for sign-off**
1. Should `school_or_college_memory` count as Event or Person-related?
2. Should `food_restaurant_memory` count as Trip / experience?
3. Is `remembered_context` really "document/screenshot context"?
4. Should `remembered_object` map anywhere? It's currently unmapped, so it can't count as a hit.

---

## 4. Current Results

### 4.1 Raw dataset vs. annotations (heuristic analyzer, draft mapping)

**Run:** 2026-09-17 · 745 unique records · heuristic analyzer · draft mapping in §3.3.

**Relevance** (all 745 records)

| Metric | Result |
|---|---|
| Agreement | 725 / 745 (97.3%) |
| Precision / Recall / F1 (annotation as reference) | 0.983 / 0.983 / 0.983 |
| Disagreements | 10 engine-relevant-only, 10 annotation-relevant-only |

| Source | Agreement |
|---|---|
| google_photos_community | 115/116 |
| youtube | 89/90 |
| reddit | 108/110 |
| app_store | 108/111 |
| forums | 103/106 |
| google_play | 112/116 |
| social_media | 90/96 (weakest) |

**Detailed fields** (567 records where both say retrieval-related)

| Field | Metric | Result |
|---|---|---|
| Scenario (5 categories) | Accuracy | **266/567 (46.9%)** |
| Object | Accuracy | 439/567 (77.4%) |
| Memory clues | Micro P / R / F1 | 0.473 / 0.673 / **0.555** |
| Forgotten information | Micro P / R / F1 | 0.554 / 0.649 / **0.597** |

| Category | P / R / F1 |
|---|---|
| Memory: time/date reference | 0.749 / 0.753 / 0.751 |
| Memory: person/relationship | 0.647 / 0.759 / 0.699 |
| Memory: document/screenshot context | 0.349 / 0.343 / 0.346 |
| Memory: place/trip/experience context | 0.182 / 0.725 / **0.292** |
| Forgotten: date/time | 0.591 / 0.741 / 0.658 |
| Forgotten: exact wording/name | 0.635 / 0.562 / 0.596 |
| Forgotten: location | 0.452 / 0.648 / 0.533 |
| Forgotten: specific retrieval detail | 0.133 / 1.000 / 0.235 (only 4 annotated) |

**Largest confusions**

| Field | Annotation says | Engine (mapped) says | Records |
|---|---|---|---|
| Scenario | General photo/media retrieval | Document / screenshot retrieval | 57 |
| Scenario | General photo/media retrieval | Trip / experience memory | 33 |
| Scenario | Event memory | General photo/media retrieval | 23 |
| Scenario | Person-related memory | General photo/media retrieval | 21 |
| Object | Photo/image | Document | 55 |
| Object | Photo/image | Not stated | 26 |
| Memory | (not annotated) | place/trip/experience context | 224 false positives |

**What this does and doesn't tell us**
- **Relevance is trustworthy** for this dataset under both labellings, so the funnel counts (577 relevant, 552 attempts) rest on solid ground.
- **Detailed fields are not yet trustworthy.** The low agreement has three possible causes, which this measurement can't separate:
  1. The draft mapping is wrong for some categories.
  2. The annotation categories are applied differently from the engine's definitions (e.g. "General photo/media retrieval" is a broad catch-all).
  3. The heuristic analyzer over-extracts; place/trip context precision is 0.18.
- **Scenario-level conclusions are affected.** Segment and opportunity breakdowns by scenario (e.g. "Document, receipt & health-record retrievers" as target segment) inherit this uncertainty. Treat them as directional until E2.2–E2.5 pass.
- **Next step:** review 20 records from each of the four largest confusions to attribute the cause. Then fix the mapping, the analyzer or the annotations accordingly (roadmap §9).

### 4.2 Grounding and pipeline integrity (raw dataset)

| Check | Result |
|---|---|
| CSV conversion fidelity (840 × 8 cells vs xlsx) | Identical |
| Direct xlsx ingest vs CSV ingest | Identical records, IDs and duplicate flags |
| Quotes failing the verbatim check | 0 / 11,119 |
| Duplicate-text groups with conflicting annotations | 0 / 31 |
| Unit and end-to-end tests | 15 / 15 pass |
| Workspace browser checks | 40 / 40 pass, no console or page errors |

### 4.3 Legacy regression baseline

Kept only to catch regressions in the heuristic analyzer. It was measured on the legacy generated set with its generator answer key, which shares vocabulary with the heuristic's patterns, so it **overstates** accuracy.

| Field | Score |
|---|---|
| Relevance F1 | 0.946 |
| Attempt F1 | 0.982 |
| Scenario accuracy (fine-grained) | 0.887 |
| Outcome accuracy | 1.000 |
| Failure-stage accuracy | 0.965 |
| Remembered F1 / Forgotten F1 | 0.697 / 0.902 |

The gap between this baseline and §4.1 (e.g. forgotten F1 0.90 vs 0.60) is itself a finding. Accuracy measured against the generator's own answer key doesn't carry over to independent labels.

---

## 5. Eval Catalogue

### E1. Ingestion correctness

| ID | Check | Metric | Target | Status |
|---|---|---|---|---|
| E1.1 | Re-ingesting the same file adds nothing | Inserted rows on second run | 0 | ✅ `test_ingest_dedupes_and_is_idempotent` |
| E1.2 | Exact duplicates detected | Recall on planted duplicates | 100% | ✅ same test |
| E1.3 | PII scrubbing | Recall on emails/phones; false scrubs on non-PII numbers | 100% recall; 0 false scrubs | ✅ recall · ⬜ false scrubs (fails today, EC-ING-10) |
| E1.4 | Conversion fidelity for the raw dataset | Identical cells, xlsx vs CSV | 840 × 8 identical | 🟡 Pass |
| E1.5 | Source representation after dedupe | Unique share per source vs raw share | Within ±5 points | 🟡 **Fails**: youtube 90/120, social_media 96/120 (EC-RAW-03) |
| E1.6 | Ignored columns reported | Ingest stats list unmapped columns | All 5 annotation columns listed | ⬜ (EC-RAW-01) |

### E2. Extraction quality

| ID | Field | Reference | Metric | Proposed target | Status |
|---|---|---|---|---|---|
| E2.1 | Relevance | Annotations | F1 | ≥ 0.90 | 🟡 **0.983** |
| E2.2 | Scenario (coarse) | Annotations | Accuracy | ≥ 0.75 | 🟡 **0.469** fails |
| E2.3 | Retrieval object | Annotations | Accuracy | ≥ 0.85 | 🟡 **0.774** fails |
| E2.4 | Memory clues (coarse) | Annotations | Micro F1 | ≥ 0.70 | 🟡 **0.555** fails |
| E2.5 | Forgotten information (coarse) | Annotations | Micro F1 | ≥ 0.70 | 🟡 **0.597** fails |
| E2.6 | Retrieval attempt vs advice/opinion | Hand-label sample | F1 | ≥ 0.85 | ⬜ |
| E2.7 | Outcome | Hand-label sample | Accuracy | ≥ 0.85 | ⬜ |
| E2.8 | Failure stage | Hand-label sample | Macro-F1 across A–F + confusion matrix | ≥ 0.70 | ⬜ |
| E2.9 | Workarounds | Hand-label sample | Micro F1 | ≥ 0.75 | ⬜ |
| E2.10 | Query type | Hand-label sample | Micro F1 | ≥ 0.70 | ⬜ |
| E2.11 | Annotation reliability | Re-annotated sample | Cohen's κ per annotation column | ≥ 0.6 before using a column as reference | ⬜ |
| E2.12 | Heuristic vs Claude agreement | Both analyses | Cohen's κ per field on 745 records; each also scored vs annotations | Report only | ⬜ needs Claude run |

Targets are **proposed** starting points. Revise E2.2–E2.5 after the mapping is signed off and E2.11 shows how consistently the annotations themselves can be applied.

### E3. Grounding

| ID | Check | Metric | Target | Status |
|---|---|---|---|---|
| E3.1 | Quotes exist in source | Invalid-quote rate | Heuristic 0%; Claude ≤ 2% | ✅ computed every run · 🟡 0 / 11,119 on raw dataset |
| E3.2 | Quote supports its label | Support precision on 100 human-reviewed signals, stratified by kind | ≥ 0.90 | ⬜ Priority: the place/trip precision of 0.18 (§4.1) suggests many unsupported labels |
| E3.3 | Trivially short quotes | Share of valid quotes under 3 words | ≤ 1% | ⬜ (EC-VAL-04) |
| E3.4 | Invented labels | Share of `proposed:*` labels a PM accepts | Report only | ⬜ |

### E4. Guardrails (problem statement §18)

| ID | Guardrail | Check | Target | Status |
|---|---|---|---|---|
| E4.1 | No fabricated quotes | Fabricated quote excluded from counts | Pass | ✅ `test_fabricated_quotes_are_flagged_and_excluded` |
| E4.2 | Honest numbers | Every rate has a denominator; zero denominator gives no percentage | Pass | ✅ `test_rate_always_carries_denominator_and_directional_flag` |
| E4.3 | Report numbers traceable | Every `n/d (x%)` in `discovery_report.md` matched to the saved bundle | 100% | ⬜ |
| E4.4 | No solution language in opportunities | Scan names, descriptions and `proposed:*` areas for solution terms | 0 hits | ⬜ |
| E4.5 | Non-leading interview questions | Leading-question filter on the brief | 0 leading questions | ✅ `test_interview_questions_filter_leading` |
| E4.6 | Brief contains no findings, and tests the lead | "Not yet collected"; hypotheses exist for the lead | Pass | ✅ `test_end_to_end_pipeline` |
| E4.7 | No unsupported provenance claim | With nothing flagged, outputs name the dataset only (0 claim strings); with records flagged, disclosure appears | Pass | ✅ `test_end_to_end_pipeline` (flagged path) · 🟡 label scan on current outputs |
| E4.8 | Epistemic labels | Every insight, chain step and JTBD carries its level | 100% | ⬜ (true by construction; add an assertion) |
| E4.9 | Prompt injection (Claude) | 20 records with embedded instructions: labels unchanged vs clean copies | 0 changed | ⬜ needs Claude run |
| E4.10 | Annotations never reach analyzers | No annotation text in chunks or prompts | Pass | 🟡 checked (annotation columns have no ingest alias); ⬜ add test |

### E5. Synthesis robustness

This matters for the raw dataset: seven of eight opportunities have vague-memory shares of 93–100% (EC-S-04), and scenario labels agree with annotations only 46.9% of the time (§4.1).

| ID | Check | Method | Metric | Target | Status |
|---|---|---|---|---|---|
| E5.1 | Bootstrap stability | Resample unique records 200×; rebuild | % runs with same lead; rank correlation | Lead unchanged ≥ 80% | ⬜ |
| E5.2 | Threshold sensitivity | Vary each strength threshold ±20% | Opportunities whose level changes | Report | ⬜ |
| E5.3 | Leave-one-source-out | Drop each source; rebuild | Lead changes? | Unchanged in ≥ 6 of 7 | ⬜ |
| E5.4 | Scenario-label sensitivity | Rebuild segments using the annotations' scenarios (mapped down to segment groups) instead of the engine's | Target segment changes? | Report | ⬜ |
| E5.5 | Analyzer sensitivity | Bundles from heuristic vs Claude | Lead/runner-up match; strength-level agreement | Report | ⬜ needs Claude run |
| E5.6 | Override sensitivity | Apply 20 realistic PM corrections; rebuild | Lead changes? | Report | ⬜ (EC-OV-03 blocks re-analysis cases) |
| E5.7 | Margin reporting | Lead vs runner-up gap in the report | Shown | 🟡 in workspace · ⬜ in Markdown report |

### E6. Contradiction recall

| ID | Check | Method | Metric | Target | Status |
|---|---|---|---|---|---|
| E6.1 | Counter-evidence found | 10 planted counter-evidence records per opportunity (separate DB) | Share appearing in that opportunity's contradictions | ≥ 90% | ⬜ |
| E6.2 | Supporting evidence not miscounted | Plant "partner's library" cases | Counted against `index_coverage_gaps` | 0 | ⬜ |
| E6.3 | Concentration flags | Opportunity built from one source | `source_concentration` raised | Pass | ⬜ |

### E7. Search

| ID | Check | Metric | Target | Status |
|---|---|---|---|---|
| E7.1 | Filters are exact | Precision of label filters | 100% | ✅ `test_search_diversifies_sources` |
| E7.2 | Source diversity | Distinct sources in top 7 when ≥ 4 match | ≥ 4 | ✅ same test · 🟡 raw dataset drill-downs return up to 7 sources |
| E7.3 | Relevance ranking | nDCG@10 on 20 PM queries with graded judgements | ≥ 0.70 | ⬜ |
| E7.4 | Diversity cost | nDCG@10 with MMR vs relevance-only | Drop ≤ 0.05 | ⬜ |

### E8. Ask interface

| ID | Check | Metric | Target | Status |
|---|---|---|---|---|
| E8.1 | Spec questions answered | 11 example questions return a plan and evidence-backed answer | 11 / 11 | 🟡 11 / 11 |
| E8.2 | Plan accuracy on paraphrases | Correct intent + filters on 44 questions (rules vs Claude) | ≥ 90% intent, ≥ 80% filters | ⬜ |
| E8.3 | Grounded answers | Numbers and quotes exist in the database | 100% | ✅ by construction |
| E8.4 | Off-topic questions | "No matching intent" for unrelated questions | 100% | ⬜ fails today (EC-ASK-01) |

### E9. Discovery workspace

| ID | Check | Target | Status |
|---|---|---|---|
| E9.1 | All 11 views render in light and dark mode; no console or page errors | Pass | 🟢 69/69 browser checks (`tools/ui_check.py`) |
| E9.2 | Key interactions: drill-down, inspector, challenge form, back/escape, palette, suggestions, facet search, sorting, drawers, map navigation, review tabs, decomposition drill, segment selection, research tabs | Pass | 🟢 included in the 55 checks |
| E9.3 | No horizontal page overflow at 390 px; mobile menu opens | Pass | 🟢 overview, opportunities, opportunity detail, research, segments, explore |
| E9.4 | Every number shows its denominator on hover | 100% of rate displays | 🟡 by construction (`rateTip`); ⬜ automated check |
| E9.5 | Any number traceable to quotes in ≤ 2 clicks | Pass | 🟡 manual |
| E9.6 | Annotation labels visible beside AI labels in the inspector | Pass | ⬜ not built (EC-UI-07) |
| E9.7 | Browser tests committed and run in CI | Pass | 🟡 committed as `tools/ui_check.py`; CI wiring open |
| E9.8 | Wide tables never clip a column at 1440 px | 0 px overflow | 🟢 checked on Segments (found and fixed a 23 px clip) |

### E11. Case study Parts 2-4 (decomposition, methodology, problem definition)

Run by `tools/mission_check.py` against the built bundle, report and brief. 69/69 pass on the current build.

| ID | Check | Target | Status |
|---|---|---|---|
| E11.0 | The journey is Recall → Express → Match → Recognize → Recover, in order, each stating a user capability | Pass | 🟢 |
| E11.0b | Data and index is reported outside the user's journey | Pass | 🟢 22.3% of attempts |
| E11.0c | The merged Match stage reconciles with its two failure codes | B + C = Match | 🟢 44 + 51 = 95 |
| E11.1 | Stage shares plus "no breakdown" and "unclear" reconcile against the attempt denominator | Exact (±1 for rounding) | 🟢 439 + 113 + 0 = 552 |
| E11.2 | No stage reports more breakdowns than there are attempts, or more unresolved than breakdowns | Pass | 🟢 |
| E11.3 | Per-stage headroom does not double-count attempts | Sum ≤ the unresolved share | 🟢 sums to 58.7 pts, exactly the unresolved share |
| E11.4 | Headroom is labelled an upper bound wherever it appears | Pass | 🟢 `INTERPRETATION` + assumption text in bundle, workspace and report |
| E11.5 | Every stage names the opportunity areas beneath it | 100% of non-zero stages | 🟢 |
| E11.6 | Stages are ranked by recoverable share, not volume | Pass | 🟢 largest = Match, +13.4 pts, then data & index +13.2 |
| E11.7 | The method is named, justified, and weighed against rejected alternatives | ≥ 3 alternatives, each with a reason | 🟢 6 alternatives, including the retrospective-only plan it replaced |
| E11.7a | The session design states what each part of it buys | ≥ 4 elements | 🟢 |
| E11.7b | The method produces what the corpus cannot: observation and ground truth | Pass | 🟢 |
| E11.7c | Every segment carries a research fit | 16/16 | 🟢 |
| E11.7d | Every segment's screener has a must-be-yes qualifier and asks for a recent incident | 100% | 🟢 |
| E11.7e | Every screener excludes domain insiders | 100% | 🟢 |
| E11.7f | High-sensitivity segments run without a screen share | 100% | 🟢 |
| E11.7g | Sensitivity is measured against the segment's own denominator, and flagged when definitional | Pass | 🟢 |
| E11.7h | Segment overlap is measured and bounded | 0 ≤ share ≤ 1 | 🟢 |
| E11.7i | Segments defined by stopping are not studied with a live task | Pass | 🟢 Abandoners = recall only |
| E11.7j | The brief's screener is the chosen segment's screener | Pass when a segment is chosen | 🟢 |
| E11.8 | Sample size in the methodology matches the brief | 5-6 | 🟢 |
| E11.9 | Sessions are coded in the engine's taxonomy so interviews and corpus compare | Pass | 🟢 |
| E11.10 | Validity threats each carry a mitigation | 100% | 🟢 4 threats |
| E11.11 | The methodology reaches the brief that is handed off | Pass | 🟢 |
| E11.12 | Every problem-definition field is present and carries an epistemic level | 7/7 core fields | 🟢 |
| E11.13 | Root cause is a `HYPOTHESIS` with the question that settles it | Pass | 🟢 |
| E11.14 | The banned framing appears only where it is ruled out | Pass | 🟢 |
| E11.15 | The scenario states what the user still remembers and what they have lost | Pass | 🟢 (this check failed on the first run and the scenario text was rewritten) |
| E11.16 | The business rationale ties to measured headroom and lists what public posts cannot answer | Pass | 🟢 +13.2 pts, 2 open questions |
| E11.17 | A competing explanation is named to rule out | Pass | 🟢 runner-up opportunity |
| E11.18 | The evolution chain runs business metric -> problem definition in five steps | Pass | 🟢 |
| E11.19 | The problem definition is marked DRAFT and reaches report §15 | Pass | 🟢 |
| E11.20 | No solution language in stage outcomes or problem-definition fields | Pass | 🟢 |
| E11.21 | Decomposition and problem definition move when the PM corrects the underlying evidence | ±1 per correction | ⬜ not automated (shares the corrected corpus by construction) |
| E11.22 | A stale target segment (no longer in the segment list) is detected | Warn in the plan | ⬜ not built (EC-DEC-07) |

---

### E12. Behavioural segmentation

Run by `tools/mission_check.py` (84/91 on the current single-source dataset; see below) and `tools/ui_check.py` (requires `playwright`, not installed, not run).

Revised to the NextLeap binary model: Direct vs Contextual is the only primary segmentation; Candidate-heavy and Recovery-dependent moved into a Retrieval State secondary lens. See [[segmentation_framework_nextleap]].

| ID | Check | Target | Status |
|---|---|---|---|
| E12.1 | The two primary segments exist, and are exhaustive | Pass | 🟢 Direct 26 (4.7%), Contextual 526 (95.3%) |
| E12.2 | Every attempt placed exactly once | Segments sum to attempts | 🟢 552 = 552 |
| E12.2a | Every Recovery-dependent attempt shows its first attempt failed, recomputed from stored analyses | 100% | 🟢 285/285 |
| E12.3 | Retrieval states sum to every attempt | Exact | 🟢 104+82+285+40+41 = 552 |
| E12.4 | Every segment has a definition, a placement rule and verbatim, de-duplicated quotes | 100% | 🟢 |
| E12.5 | Each lens places every attempt once, overall and within each segment | Exact | 🟢 3 lenses |
| E12.6 | Lens find rates exclude posts with no stated outcome | Pass | 🟢 |
| E12.7 | Retrieval complexity carries information | Not flat across low/medium/high | 🟢 33.0% / 35.1% / 40.9% found (increasing, not the originally-assumed decreasing gradient - real finding, not a bug: see caveat on writing length below) |
| E12.8 | A stale target choice is set aside | Pass | 🟢 |
| E12.9 | Every segment number and lens cell drills into exactly its attempts | Pass | 🟢 e.g. 82 of 82 |
| E12.10 | Segment tables fit at 1440 and 390 px | 0 px overflow | ⬜ not verified this pass (`ui_check.py` did not run) |
| E12.11 | Placement agrees with a human reading of the text | Sample agreement ≥ 85% | ⬜ read samples during design; a scored hand-labelled sample is still to do |
| E12.12 | Impact mapping (WHY/WHO/HOW/WHAT) and the target-segment hypothesis are present | Pass | 🟢 |

**Known gaps found while re-running mission_check.py for this revision** (pre-date the segmentation work, not caused by it):
- `Store.reference_labels()` does not exist, and no `{DATASET}.csv` reference file exists at the project root, so the §22 "engine vs. the dataset's own labels" comparison (5-6 checks) cannot run. `Book16.csv` has the right shape for this but was never wired up, and its 42 rows of spliced-in labeller commentary would need stripping before ingest first.
- The DB holds two datasets (`google_photos_discovery_contextual_resegmented` and a superseded `simulated_v2`) because a safety guardrail correctly blocked deleting the stale rows; the server and CLI now default to excluding it, but the "only the current dataset is in the database" check still fails against the raw DB state.

### E10. Claude operations

> Every run in this family spends money. Get approval first, and start with a 50-chunk pilot.

| ID | Check | Metric | Target | Status |
|---|---|---|---|---|
| E10.1 | Cost per chunk | Tokens per chunk; $ per 1,000 chunks at effort low/medium/high | Lowest effort that meets E2 targets | ⬜ |
| E10.2 | Relevance-gate saving | Share of chunks stopped at relevance | Report (≈ 23% not relevant in raw dataset under both labellings) | ⬜ |
| E10.3 | Prompt caching | `cache_read_input_tokens > 0` from the second request | Pass | ⬜ (system prompt may be below the cacheable minimum) |
| E10.4 | Reliability | Refusal, truncation and API-error skip rate | ≤ 1% | ⬜ |
| E10.5 | Latency | p50 / p95 seconds per chunk at concurrency 4 | Report | ⬜ |
| E10.6 | Quality uplift | E2.2–E2.5 on Claude vs heuristic, same mapping | Report | ⬜ |
| E10.7 | Full-corpus estimate | Projected cost and time for 745 chunks | Approved before full run | ⬜ |

---

## 6. How to Run

| What | Command | Output |
|---|---|---|
| Unit and end-to-end tests | `python -m pytest -q tests` | 15 tests |
| Invalid-quote rate (E3.1) | `python -m discovery_engine analyze --analyzer heuristic` | `quotes_total`, `quotes_invalid` |
| Annotation cross-check (E2.1–E2.5) | ⬜ To be committed as `python -m discovery_engine evaluate-annotations --file google_photos_discovery_annotated.csv --mapping <mapping.json>`. The §4.1 numbers came from an ad-hoc script using the §3.3 mapping | Relevance, scenario, object, multi-label scores; per-source breakdown; confusions |
| Hand-label scoring (E2.6–E2.10) | `python -m discovery_engine evaluate --truth data/eval/raw_handlabels.jsonl` | Precision/recall/F1, accuracy, confusion matrix (`evaluate` skips records not in the file) |
| Workspace checks (E9) | `python tools/ui_check.py` against a running `serve --port 8931` (Edge; set `UI_CHECK_OUT` to keep the screenshots) | 69 checks, console and page errors, screenshots |
| Mission and case-study checks (E4, E11, E12) | `python tools/mission_check.py` after `synthesize` | 86 checks across §20 success criteria, §18 guardrails, §22 dataset rules and case study Parts 2-4 |
| Claude pilot (E10) | `python -m discovery_engine --db data/claude_pilot.db analyze --analyzer claude --limit 50` | Pilot analyses + token usage (after approval) |

Use `--db` to keep eval databases away from `data/discovery.db`, which holds only the raw dataset.

---

## 7. When to Run

| Trigger | Run |
|---|---|
| Any code change | `pytest` (E1.1–E1.2, E3.1, E4.1–E4.2, E4.5–E4.7, E7.1–E7.2) |
| Change to `analyze/`, `validate.py` or the taxonomy | E2.1–E2.5 annotation cross-check, E3.1, then E5.1 |
| Label mapping changed | E2.2–E2.5, E5.4 |
| Change to `synthesis.py`, `evidence.py`, `hypotheses.py` or `report.py` | E4.6, E5.1–E5.3, E6 |
| Change to `web/` or `server.py` | E9.1–E9.3, E9.8 |
| Change to `decomposition.py`, `problem.py`, `research.py` or the leading-opportunity rule | E11 (`tools/mission_check.py`) |
| Before sharing a discovery report | E3.2 spot-check, E4.3 number trace, E5.1 stability, E5.4 scenario sensitivity |
| Before switching extraction to Claude | E10 pilot, E2.12, E4.9, E10.6 |
| Dataset file changes | E1.4–E1.6, edge-case section 10 probes, E2.1–E2.5 |

---

## 8. Reporting Template

Record every eval run in `reports/evals/<date>-<name>.md`:

```markdown
# Eval run: <name>
Date: <YYYY-MM-DD> · Dataset: google_photos_discovery_annotated · Analyzer: <heuristic | claude + model + effort>
Database: <path> · Mapping version: <file/hash> · Reference: <annotations | hand labels, n, κ>

## Results
| ID | Metric | Target | Result | Pass? |

## Per-source breakdown
| Source | Relevance agreement | Scenario accuracy | Memory F1 | Forgotten F1 |

## Largest confusions (with 3 example record_ids each)
| Field | Reference | Engine | Records | Likely cause (mapping / annotation / analyzer) |

## Effect on conclusions
- Leading opportunity changed? <yes/no> · Target segment changed? <yes/no> · Strength levels changed: <list>

## Decision
<ship / fix and re-run / adjust mapping or target, with reason>
```

---

## 9. Roadmap

| Order | Work | Unblocks | Effort |
|---|---|---|---|
| 1 | Review and sign off the draft label mapping (§3.3 questions) | Trustworthy E2.2–E2.5 targets | 0.25 d |
| 2 | Commit `evaluate-annotations` with a versioned mapping file | Repeatable cross-checks after every change | 0.5 d |
| 3 | Review 20 records from each of the four largest confusions; attribute each to mapping, annotation or analyzer | Knowing what to fix | 0.5 d |
| 4 | Re-annotate 100 records independently (E2.11) and hand-label them for attempt, outcome, failure stage, workarounds, query type (E2.6–E2.10) | Annotation reliability; coverage of fields the dataset doesn't annotate | 1.5 d |
| 5 | E3.2 support spot-check (100 signals), starting with place/trip context | Grounding beyond quote existence | 0.5 d |
| 6 | E5.1–E5.4 robustness script; add the margin to the Markdown report | Trust in the lead and target segment | 1 d |
| 7 | Store annotations in their own table and show them in the inspector and review queue (EC-UI-07, EC-RAW-08) | Reviewing disagreements in place | 1 d |
| 8 | Claude pilot with approval: E10, E2.12, E4.9 | Decision on moving extraction to Claude | 0.5 d + API cost |
| 9 | Commit browser tests (E9.7), E4.3 number tracing, E4.10 annotation-leak test | Regression safety | 0.75 d |
