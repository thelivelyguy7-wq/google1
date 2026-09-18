# Discovery Report: Retrieving Vaguely Remembered Photos

Generated 2026-09-18T21:21:28+00:00.

> **Dataset:** `google_photos_discovery_contextual_resegmented` · 840 records, 745 unique.

> **Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000) (`python -m discovery_engine serve`)

† = denominator below the minimum sample; treat as directional. Every rate is numerator/denominator of distinct records.


## 1. Business Metric
Increase the percentage of users who successfully retrieve a photo they remember but cannot precisely describe when they start searching.

## 2. Product Outcome Decomposition
Baseline: **180/552 (32.6%) attempts end in a confirmed find**; 324/552 (58.7%) do not.

Five things have to go right for a vaguely remembered photo to be found:

1. **Recall** — The user remembers enough contextual information to identify the intended photo.
2. **Express** — The user converts what they remember into a search attempt.
3. **Match** — Photos surfaces candidates that correspond to the user's remembered clues.
4. **Recognize** — The user can identify the intended photo among the candidates.
5. **Recover** — After a failed attempt, the user can refine or change the search and continue.

Plus one condition outside the user's journey: The item, and the information needed to find it, exist in the library and are indexed.

| Stage | Product outcome to influence | Breaks here | Still unresolved | Max headroom (pts) | Opportunity areas |
|---|---|---|---|---|---|
| Recall | Users start with something the system can act on | 0/552 (0.0%) | 0/552 (0.0%) | +0.0 | — |
| Express | Remembered context becomes a usable query | 89/552 (16.1%) | 71/552 (12.9%) | +12.9 | Turning context into search terms (89), Recovering after a failed search (33), Combining several weak clues (24) |
| Match | Remembered clues bring back the intended photo | 95/552 (17.2%) | 74/552 (13.4%) | +13.4 | Combining several weak clues (44), Recovering after a failed search (41), Trusting "no results" (24) |
| Recognize | Users recognise the intended photo among candidates | 80/552 (14.5%) | 71/552 (12.9%) | +12.9 | Recognising the right photo (80), Recovering after a failed search (58), Combining several weak clues (40) |
| Recover | A failed first attempt has a useful next step | 52/552 (9.4%) | 35/552 (6.3%) | +6.3 | Recovering after a failed search (52), Combining several weak clues (20), Anchoring a rough sense of time (15) |
| Data & index (outside the journey) | Needed items and their context are retrievable at all | 123/552 (22.3%) | 73/552 (13.2%) | +13.2 | Missing or unsearchable data (120), Recovering after a failed search (41), Anchoring a rough sense of time (24) |

*INTERPRETATION. Headroom is the share of all attempts that broke down at this stage and did not succeed: the most the success rate could rise if that stage never failed. It assumes nothing else changes and that each attempt has a single decisive breakdown, so treat it as an upper bound for prioritisation, not a forecast.*

Ranked by recoverable share: match, data, express, recognize, recover. 113/552 (20.5%) of attempts describe no breakdown; 0/552 (0.0%) are unclear.

## 3. Discovery Scope
- Scope: 745 unique records from 7 sources
- Sources: {'google_play': 116, 'app_store': 111, 'reddit': 110, 'google_photos_community': 116, 'social_media': 96, 'youtube': 90, 'forums': 106}
- Analyzers: {'heuristic': 745}
- Duplicates excluded: 95
- Relevant to retrieval: 577/745 (77.4%); first-person retrieval attempts among relevant: 552/577 (95.7%)
- Quote validation: 0 of 10679 extracted quotes could not be found in the source and were excluded.
- Method: staged extraction (relevance, then structured signals with verbatim quotes), deterministic validation, record-level counting, rule-based evidence strength, counter-evidence search.

## 4. User Retrieval Scenarios
| Scenario | Attempts | Sources | Unsuccessful | Top failure stage | Top forgotten |
|---|---|---|---|---|---|
| travel | 50/552 (9.1%) | 7 | 29 | can't pick out the right photo (D) | exact date, exact location |
| document | 48/552 (8.7%) | 7 | 32 | can't express the memory (A) | exact date, exact text |
| screenshot | 45/552 (8.2%) | 7 | 19 | data missing or unsearchable (F) | exact text, exact location |
| food/restaurant | 44/552 (8.0%) | 7 | 33 | search misreads the clue (B) | exact location, exact object name |
| event | 44/552 (8.0%) | 7 | 22 | can't pick out the right photo (D) | exact date, event name |
| video | 42/552 (7.6%) | 7 | 24 | data missing or unsearchable (F) | exact date, metadata |
| family | 38/552 (6.9%) | 7 | 22 | data missing or unsearchable (F) | exact date, metadata |
| receipt | 35/552 (6.3%) | 7 | 23 | data missing or unsearchable (F) | exact text, exact date |
| wedding | 33/552 (6.0%) | 7 | 18 | can't pick out the right photo (D) | exact date, album |
| medical/health image | 24/552 (4.3%) | 7 | 16 | can't express the memory (A) | exact location, exact object name |
| object | 22/552 (4.0%) | 7 | 14 | can't express the memory (A) | exact location, exact date |
| work | 21/552 (3.8%) | 6 | 14 | data missing or unsearchable (F) | exact date, exact location |
| personal | 20/552 (3.6%) | 7 | 10 | can't pick out the right photo (D) | exact date, exact location |
| school/college | 20/552 (3.6%) | 7 | 16 | data missing or unsearchable (F) | exact date, event name |
| location | 19/552 (3.4%) | 7 | 8 | can't pick out the right photo (D) | exact location, exact text |
| purchase-related image | 19/552 (3.4%) | 7 | 13 | data missing or unsearchable (F) | exact location, exact object name |
| other | 16/552 (2.9%) | 6 | 3 | data missing or unsearchable (F) | exact location, person name |
| friend | 12/552 (2.2%) | 6 | 8 | can't express the memory (A) | person name, exact date |

## 5. Memory Patterns (what people remember)
| Remembered | Attempts | Sources | Precision (exact/approx) |
|---|---|---|---|
| person | 227/552 (41.1%) | 7 | 221/6 |
| time approximation | 196/552 (35.5%) | 7 | 86/110 |
| object | 175/552 (31.7%) | 7 | 173/3 |
| visual appearance | 159/552 (28.8%) | 7 | 158/3 |
| place | 154/552 (27.9%) | 7 | 138/16 |
| event | 107/552 (19.4%) | 7 | 108/0 |
| context | 79/552 (14.3%) | 7 | 72/7 |
| trip | 38/552 (6.9%) | 7 | 38/0 |
| occasion | 38/552 (6.9%) | 7 | 36/2 |
| text | 35/552 (6.3%) | 6 | 35/0 |
| activity | 27/552 (4.9%) | 7 | 23/4 |
| relationship | 6/552 (1.1%) | 4 | 6/0 |
| emotion | 5/552 (0.9%) | 2 | 5/0 |

- **person** examples:
  - `EV-aca63835e5` (app_store): “It had my husband and his cousins in it.”
  - `EV-8a1b651591` (forums): “In the end I texted my friend to send it again.”
  - `EV-55f4065651` (google_photos_community): “Does anyone know how to find the photo of my son's vaccination card?”

- **time approximation** examples:
  - `EV-b1b31793b3` (app_store): “It was when we bought it, 2 years ago maybe.”
  - `EV-e07931f4b2` (forums): “Timing wise it was 2021 or 2022, not sure.”
  - `EV-d0b1998a7e` (google_photos_community): “Timing wise it was one of the new years, 2019 or 2020.”

- **object** examples:
  - `EV-1b91da102f` (app_store): “Does anyone know how to find the photo of the warranty card for the washing machine?”
  - `EV-72dc2c6381` (forums): “Does anyone know how to find the photo of my first tattoo right after I got it?”
  - `EV-e1157daa62` (google_photos_community): “Does anyone know how to find the photo of my son's vaccination card?”

## 6. Forgotten Information
| Forgotten | Attempts | Unsuccessful when forgotten | Unsuccessful when not | Text links gap to failure |
|---|---|---|---|---|
| exact date | 253/552 (45.8%) | 176/253 (69.6%) | 148/299 (49.5%) | 0/253 (0.0%) |
| exact location | 126/552 (22.8%) | 93/126 (73.8%) | 231/426 (54.2%) | 0/126 (0.0%) |
| exact text | 91/552 (16.5%) | 66/91 (72.5%) | 258/461 (56.0%) | 0/91 (0.0%) |
| exact object name | 82/552 (14.9%) | 63/82 (76.8%) | 261/470 (55.5%) | 0/82 (0.0%) |
| exact keyword | 18/552 (3.3%) | 12/18 (66.7%) † | 312/534 (58.4%) | 0/18 (0.0%) † |
| event name | 16/552 (2.9%) | 11/16 (68.8%) † | 313/536 (58.4%) | 0/16 (0.0%) † |
| album | 15/552 (2.7%) | 9/15 (60.0%) † | 315/537 (58.7%) | 0/15 (0.0%) † |
| metadata | 15/552 (2.7%) | 12/15 (80.0%) † | 312/537 (58.1%) | 0/15 (0.0%) † |
| person name | 11/552 (2.0%) | 9/11 (81.8%) † | 315/541 (58.2%) | 0/11 (0.0%) † |

*These are associations, not causes. 'Text links gap to failure' counts only records where the author connects the two.*

## 7. Search Formulation
- Attempts quoting at least one query: 493/552 (89.3%); median query length: 2 words
- Attempts with 2+ queries: 194/552 (35.1%)
- Query types: keyword 390/764 (51.0%), natural language 247/764 (32.3%), metadata 115/764 (15.1%), date 12/764 (1.6%)
- Query orientation: image contents 364/764 (47.6%), what they saw 142/764 (18.6%), where 139/764 (18.2%), approximate when 127/764 (16.6%), who 103/764 (13.5%)
- Outcome by query type: natural language: not found 102, wrong results 60, found 45, too many results 40; keyword: not found 190, wrong results 79, too many results 61, found 60; metadata: not found 50, wrong results 28, too many results 26, found 11; date: too many results 5, not found 5, wrong results 2
- Example queries:
  - `EV-ca8e947600` (app_store): “Searched for "hammock between coconut trees near beach homestay"”
  - `EV-fcdbcaa907` (forums): “typed "beach 2021"”
  - `EV-3d520de4ef` (google_photos_community): “Searched for "31 december"”
  - `EV-bb51693d40` (google_play): “Tried "whatsapp"”
  - `EV-88a42747b4` (reddit): “Searched for "girl in sunflower costume on stage"”
  - `EV-8a914409c3` (social_media): “Searched for "video of band with violin red lights pub"”

## 8. Failure Patterns
| Stage | Attempts | Sources | Meaning |
|---|---|---|---|
| data missing or unsearchable (F) | 123/552 (22.3%) | 7 | Relevant information is unavailable, missing, inaccessible or insufficiently represented. |
| no breakdown described | 113/552 (20.5%) | 7 | No failure is described. |
| can't express the memory (A) | 89/552 (16.1%) | 7 | User remembers something but struggles to translate it into searchable information. |
| can't pick out the right photo (D) | 80/552 (14.5%) | 7 | The relevant photo may be present but the user struggles to recognise or distinguish it. |
| stuck after the first miss (E) | 52/552 (9.4%) | 7 | First attempt fails and the user does not know how to continue effectively. |
| photo never surfaces (C) | 51/552 (9.2%) | 7 | The relevant photo does not appear or is insufficiently surfaced. |
| search misreads the clue (B) | 44/552 (8.0%) | 7 | User provides a meaningful clue but the system appears not to interpret it correctly. |

- **data missing or unsearchable (F)**:
  - `EV-148eb52b3e` (app_store): “The text on the bill isn't searchable as far as I can tell.”
  - `EV-a35c4f9e02` (forums): “For context, location was probably off on my phone.”

- **can't express the memory (A)**:
  - `EV-c4a228c828` (app_store): “How do you even search for something like that?”
  - `EV-9207b05f38` (forums): “I just didn't know how to describe it in a way search would get.”

- **can't pick out the right photo (D)**:
  - `EV-0ad93230f7` (app_store): “There are so many almost identical shots from that day that I can't tell which one it is.”
  - `EV-a7b99fe932` (forums): “I have hundreds of similar shots and can't tell which one it was.”


**Journey (difficulty by stage):** recall 0/552 (0.0%) → express 89/552 (16.1%) → match 405/552 (73.4%) → recognize 80/552 (14.5%) → recover 52/552 (9.4%)

## 9. Workarounds
| Workaround | Attempts | Sources |
|---|---|---|
| manual scrolling | 162/552 (29.3%) | 7 |
| abandonment | 85/552 (15.4%) | 7 |
| date browsing | 85/552 (15.4%) | 7 |
| ask another person | 53/552 (9.6%) | 7 |
| other application | 49/552 (8.9%) | 7 |
| repeated search | 45/552 (8.2%) | 5 |
| synonym search | 43/552 (7.8%) | 7 |
| people browsing | 33/552 (6.0%) | 6 |
| location browsing | 23/552 (4.2%) | 6 |
| filters | 15/552 (2.7%) | 5 |
| external search | 14/552 (2.5%) | 7 |
| album browsing | 11/552 (2.0%) | 5 |
| return later | 9/552 (1.6%) | 5 |

## 10. Retrieval Segments (by user behaviour)
**Primary segmentation is binary.** Person, place, event, object and visual detail are memory clues used to characterize attempts, not separate segments; candidate-heavy and recovery-dependent outcomes are retrieval states within these segments (below), not segments of their own.

1. **Direct Retrieval** — User expresses a strong identifier; the query is precise, ambiguity is low, and the photo is found with little effort.
2. **Contextual Retrieval** — User remembers the surrounding context rather than a precise identifier; the query is built from several weaker clues that the system has to connect.

| Segment | Share of attempts | Sources | Found | Unsuccessful | Abandon | Dominant breakdown | Strength |
|---|---|---|---|---|---|---|---|
| Direct Retrieval | 26/552 (4.7%) | 7 | 26/26 (100.0%) † | 0/26 (0.0%) † | 0/26 (0.0%) † | — | LOW |
| Contextual Retrieval | 526/552 (95.3%) | 7 | 154/526 (29.3%) | 324/526 (61.6%) | 85/526 (16.2%) | data missing or unsearchable (F) | HIGH |

**How attempts are placed.** An attempt is Direct only if it meets the Direct rule in full; every other attempt is Contextual.

*Public posts are written mostly when something goes wrong, so effortless retrievals are under-represented here and hard ones over-represented. Direct Retrieval is the success path the metric is aiming for; treat its small share as a property of the corpus, not of users. Recruit one Direct participant deliberately as a contrast.*

### Impact mapping
**WHY** Increase successful retrieval of remembered-but-imprecisely-described photos.

**WHO** Users engaging in Contextual Retrieval, especially those in a candidate-heavy or recovery-dependent state.

**HOW** The user needs to connect multiple contextual memories into a successful retrieval path without repeated search failure or manual candidate inspection.

**WHAT** Solution space - not yet chosen. Only to be entered after HOW is validated by primary research. Candidate directions to evaluate later, none selected: contextual query expansion, multi-clue retrieval, conversational refinement, memory-based search assistance, temporal/contextual narrowing, candidate explanation.

**Target segment hypothesis (to validate, not a conclusion):** Contextual Retrieval users whose incomplete memories lead to candidate-heavy or recovery-dependent retrieval.

### Retrieval states
How attempts within the segments above actually played out. Not exclusive user groups: every attempt gets exactly one state, by the precedence rule below (data/index limitation, then a crowded result set, then a changed route after a failed first try, then a clean find, else unresolved).

| State | Definition | Share of attempts | Sources | Mostly in | Strength |
|---|---|---|---|---|---|
| Direct / low-effort | Finds the relevant photo without a crowded result set, a changed route, or a breakdown. | 104/552 (18.8%) | 7 | Contextual (78), Direct (26) | MEDIUM |
| Candidate-heavy | The system returns multiple plausible candidates and the user struggles to narrow or recognise the intended one. | 82/552 (14.9%) | 7 | Contextual (82) | HIGH |
| Recovery-dependent | The first attempt fails and the user changes strategy - reformulates, browses, filters, asks someone, or tries elsewhere - to continue. | 285/552 (51.6%) | 7 | Contextual (285) | HIGH |
| Unresolved | The user cannot confidently find the photo, and no data/index limitation or changed route explains why. | 40/552 (7.2%) | 7 | Contextual (40) | MEDIUM |
| Unavailable | The photo is not actually in the searchable library (never backed up, on another device or account, not indexed). | 41/552 (7.4%) | 7 | Contextual (41) | LOW |

### Secondary segmentation
The Direct/Contextual split is the primary cut; each lens below cuts across it.

#### Memory state
*What does the person still hold about the photo?* From the remembered and forgotten signals, plus what the person typed: a precisely stated person, place, text or object counts as an identifier; a forgotten date, location, text, name, album or metadata counts as a lost identifier; what a query describes (who, where, roughly when, what it looked like) counts as context held.

| Category | Share of attempts | Found (of attempts stating an outcome) | Photo not there to find |
|---|---|---|---|
| Identifier held | 52/552 (9.4%) | 7/17 (41.2%) † | 27/52 (51.9%) |
| Partial identifier | 356/552 (64.5%) | 97/356 (27.2%) | 76/356 (21.3%) |
| Context only | 134/552 (24.3%) | 72/127 (56.7%) | 15/134 (11.2%) |
| Nothing specific stated | 10/552 (1.8%) | 4/4 (100.0%) † | 5/10 (50.0%) † |

Within each segment: Direct Retrieval: Identifier held 19.2%, Context only 65.4%, Nothing specific stated 15.4%; Contextual Retrieval: Identifier held 8.9%, Partial identifier 67.7%, Context only 22.2%, Nothing specific stated 1.1%.

#### Retrieval complexity
*How many clues does the system have to combine, and how ambiguous are they?* Distinct kinds of clue in the attempt, remembered or typed (person, place, event, object, appearance, rough time, text...), combined with whether any of them is a precise anchor. More kinds with no anchor means more, weaker constraints to intersect; keyword search matches words, not combinations.

| Category | Share of attempts | Found (of attempts stating an outcome) | Photo not there to find |
|---|---|---|---|
| Low complexity | 118/552 (21.4%) | 29/88 (33.0%) | 34/118 (28.8%) |
| Medium complexity | 379/552 (68.7%) | 129/368 (35.1%) | 78/379 (20.6%) |
| High complexity | 45/552 (8.2%) | 18/44 (40.9%) | 6/45 (13.3%) |
| No clue stated | 10/552 (1.8%) | 4/4 (100.0%) † | 5/10 (50.0%) † |

Within each segment: Direct Retrieval: Low complexity 19.2%, Medium complexity 65.4%, No clue stated 15.4%; Contextual Retrieval: Low complexity 21.5%, Medium complexity 68.8%, High complexity 8.6%, No clue stated 1.1%.

#### Retrieval state
*How did the attempt actually play out?* Assigned by precedence from the extracted signals, most specific cause first: a data/index limitation is Unavailable; otherwise a crowded or hard-to-distinguish result set is Candidate-heavy; otherwise a changed route after a failed first attempt is Recovery-dependent; a clean find is Direct/low-effort; anything else that neither resolves nor names a cause is Unresolved.

| Category | Share of attempts |
|---|---|
| Direct / low-effort | 104/552 (18.8%) |
| Candidate-heavy | 82/552 (14.9%) |
| Recovery-dependent | 285/552 (51.6%) |
| Unresolved | 40/552 (7.2%) |
| Unavailable | 41/552 (7.4%) |

Within each segment: Direct Retrieval: Direct / low-effort 100.0%; Contextual Retrieval: Direct / low-effort 14.8%, Candidate-heavy 15.6%, Recovery-dependent 54.2%, Unresolved 7.6%, Unavailable 7.8%.

*Read the find rates as composition, not cause: posts that failed are longer and list more of what the person remembers, so part of any gradient is how people write. The interview memory card measures it properly.*

## 11. Opportunity Areas

### Missing or unsearchable data (HIGH)
`index_coverage_gaps` · Address content that is not retrievable because the needed information is missing, unindexed or inaccessible.


- **OBSERVATION**: 120 records from 7 sources map to this area.

- **OBSERVATION**: Unsuccessful outcome in 71/120 supporting records; abandonment signals in 20/120.

- **INSIGHT**: Most-remembered clues: person (59), time approximation (48), object (45); most-forgotten: exact date (42), exact location (21), exact text (20).

- **INSIGHT**: Scenarios affected: video (18), document (14), screenshot (12), receipt (11).

- **Evidence chain:** *symptom* (OBSERVATION): Outcomes among supporting records: not found 33, not stated 30, found 19, abandoned 17, partly found 12, uncertain 9. → *behavior* (OBSERVATION): Most frequent workarounds: manual scrolling, abandonment, synonym search. → *barrier* (INSIGHT): Most breakdowns (100%) are at one stage: data missing or unsearchable (F), i.e. relevant information is unavailable, missing, inaccessible or insufficiently represented. → *potential root cause* (HYPOTHESIS): Users retain person, time approximation, object but lack exact date, exact location, exact text; the retrieval path appears to break at the 'data missing or unsearchable (F)' stage. Validate in interviews before treating this as the cause.

- Evidence:
  - `EV-148eb52b3e` (app_store): “The text on the bill isn't searchable as far as I can tell.”
  - `EV-a35c4f9e02` (forums): “For context, location was probably off on my phone.”
  - `EV-96ac9ae829` (google_photos_community): “I think it's in a shared album someone else made, not my library.”

- **Challenging evidence:**
  - vague memory success (49 records): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
  - known workaround exists (2 records): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

- **Unresolved:** Does the forgotten information actually cause the failure, or only co-occur with it? / How often does this happen per user per month (frequency cannot be measured from public posts)? / What did the user try that is not written in the post?

### Recovering after a failed search (MEDIUM)
`recovery_after_failed_search` · Help users know what to try next after an unsuccessful retrieval attempt, instead of falling back to exhaustive scrolling.


- **OBSERVATION**: 225 records from 7 sources map to this area.

- **OBSERVATION**: Unsuccessful outcome in 184/225 supporting records; abandonment signals in 85/225.

- **INSIGHT**: Most-remembered clues: time approximation (95), person (94), object (88); most-forgotten: exact date (130), exact location (58), exact text (49).

- **INSIGHT**: Scenarios affected: travel (22), event (22), document (21), receipt (18).

- **Evidence chain:** *symptom* (OBSERVATION): Outcomes among supporting records: abandoned 77, not found 65, found 41, uncertain 26, partly found 16. → *behavior* (OBSERVATION): Most frequent workarounds: manual scrolling, abandonment, date browsing. → *barrier* (INSIGHT): No single dominant breakdown stage: the most common, can't pick out the right photo (D), covers only 26% of breakdowns. → *potential root cause* (HYPOTHESIS): Users retain time approximation, person, object but lack exact date, exact location, exact text; the retrieval path appears to break at several stages. Validate in interviews before treating this as the cause.

- Evidence:
  - `EV-148eb52b3e` (app_store): “The text on the bill isn't searchable as far as I can tell.”
  - `EV-a7b99fe932` (forums): “I have hundreds of similar shots and can't tell which one it was.”
  - `EV-250e5cac75` (google_photos_community): “How do you even search for something like that?”

- **Challenging evidence:**
  - explicit counter evidence (108 records): Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity (labels: failure not search related, vague search succeeded). Scenario-weighted count: 65.3 (weight = the opportunity's record count in that scenario / its largest scenario count).
  - vague memory success (50 records): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
  - alternative explanation (41 records): Some supporting records attribute the failure to missing or unindexed data rather than to the user's memory or the query.
  - known workaround exists (2 records): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

- **Unresolved:** Does the forgotten information actually cause the failure, or only co-occur with it? / How often does this happen per user per month (frequency cannot be measured from public posts)? / What did the user try that is not written in the post?

### Combining several weak clues (MEDIUM)
`multi_clue_combination` · Help users narrow retrieval by combining several weak, partial clues that individually return too much or nothing.


- **OBSERVATION**: 131 records from 7 sources map to this area.

- **OBSERVATION**: Unsuccessful outcome in 103/131 supporting records; abandonment signals in 25/131.

- **INSIGHT**: Most-remembered clues: person (57), visual appearance (51), time approximation (50); most-forgotten: exact date (83), exact location (43), exact object name (29).

- **INSIGHT**: Scenarios affected: food/restaurant (22), event (15), object (12), wedding (9).

- **Evidence chain:** *symptom* (OBSERVATION): Outcomes among supporting records: not found 48, found 28, abandoned 21, uncertain 21, partly found 13. → *behavior* (OBSERVATION): Most frequent workarounds: manual scrolling, date browsing, abandonment. → *barrier* (INSIGHT): No single dominant breakdown stage: the most common, search misreads the clue (B), covers only 34% of breakdowns. → *potential root cause* (HYPOTHESIS): Users retain person, visual appearance, time approximation but lack exact date, exact location, exact object name; the retrieval path appears to break at several stages. Validate in interviews before treating this as the cause.

- Evidence:
  - `EV-0ad93230f7` (app_store): “There are so many almost identical shots from that day that I can't tell which one it is.”
  - `EV-a7b99fe932` (forums): “I have hundreds of similar shots and can't tell which one it was.”
  - `EV-49f1afb5d3` (google_photos_community): “All the results look the same as tiny thumbnails.”

- **Challenging evidence:**
  - explicit counter evidence (108 records): Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity (labels: failure not search related, vague search succeeded). Scenario-weighted count: 36.6 (weight = the opportunity's record count in that scenario / its largest scenario count).
  - vague memory success (50 records): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
  - alternative explanation (3 records): Some supporting records attribute the failure to missing or unindexed data rather than to the user's memory or the query.
  - known workaround exists (2 records): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

- **Unresolved:** Does the forgotten information actually cause the failure, or only co-occur with it? / How often does this happen per user per month (frequency cannot be measured from public posts)? / What did the user try that is not written in the post?

### Turning context into search terms (MEDIUM)
`context_to_query_translation` · Help users retrieve memories using contextual clues (events, relationships, experiences) they remember but cannot translate into searchable terms.


- **OBSERVATION**: 93 records from 7 sources map to this area.

- **OBSERVATION**: Unsuccessful outcome in 73/93 supporting records; abandonment signals in 17/93.

- **INSIGHT**: Most-remembered clues: time approximation (42), object (42), visual appearance (37); most-forgotten: exact date (47), exact text (21), exact location (18).

- **INSIGHT**: Scenarios affected: document (17), screenshot (9), object (8), medical/health image (8).

- **Evidence chain:** *symptom* (OBSERVATION): Outcomes among supporting records: not found 34, found 20, abandoned 16, uncertain 15, partly found 8. → *behavior* (OBSERVATION): Most frequent workarounds: manual scrolling, other application, abandonment. → *barrier* (INSIGHT): Most breakdowns (96%) are at one stage: can't express the memory (A), i.e. user remembers something but struggles to translate it into searchable information. → *potential root cause* (HYPOTHESIS): Users retain time approximation, object, visual appearance but lack exact date, exact text, exact location; the retrieval path appears to break at the 'can't express the memory (A)' stage. Validate in interviews before treating this as the cause.

- Evidence:
  - `EV-c4a228c828` (app_store): “How do you even search for something like that?”
  - `EV-9207b05f38` (forums): “I just didn't know how to describe it in a way search would get.”
  - `EV-250e5cac75` (google_photos_community): “How do you even search for something like that?”

- **Challenging evidence:**
  - explicit counter evidence (104 records): Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity (labels: failure not search related, vague search succeeded). Scenario-weighted count: 35.1 (weight = the opportunity's record count in that scenario / its largest scenario count).
  - vague memory success (48 records): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
  - alternative explanation (2 records): Some supporting records attribute the failure to missing or unindexed data rather than to the user's memory or the query.
  - known workaround exists (2 records): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

- **Unresolved:** Does the forgotten information actually cause the failure, or only co-occur with it? / How often does this happen per user per month (frequency cannot be measured from public posts)? / What did the user try that is not written in the post?

### Anchoring a rough sense of time (MEDIUM)
`approximate_time_anchoring` · Help users locate photos when they only remember time approximately or relative to another event.


- **OBSERVATION**: 85 records from 7 sources map to this area.

- **OBSERVATION**: Unsuccessful outcome in 66/85 supporting records; abandonment signals in 19/85.

- **INSIGHT**: Most-remembered clues: time approximation (85), person (37), visual appearance (31); most-forgotten: exact date (85), exact location (16), exact object name (8).

- **INSIGHT**: Scenarios affected: document (13), travel (11), family (10), video (8).

- **Evidence chain:** *symptom* (OBSERVATION): Outcomes among supporting records: not found 26, found 19, abandoned 17, uncertain 16, partly found 7. → *behavior* (OBSERVATION): Most frequent workarounds: date browsing, manual scrolling, abandonment. → *barrier* (INSIGHT): No single dominant breakdown stage: the most common, data missing or unsearchable (F), covers only 28% of breakdowns. → *potential root cause* (HYPOTHESIS): Users retain time approximation, person, visual appearance but lack exact date, exact location, exact object name; the retrieval path appears to break at several stages. Validate in interviews before treating this as the cause.

- Evidence:
  - `EV-109234f082` (app_store): “There are so many almost identical shots from that day that I can't tell which one it is.”
  - `EV-a35c4f9e02` (forums): “For context, location was probably off on my phone.”
  - `EV-49f1afb5d3` (google_photos_community): “All the results look the same as tiny thumbnails.”

- **Challenging evidence:**
  - explicit counter evidence (89 records): Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity (labels: failure not search related, vague search succeeded). Scenario-weighted count: 44.2 (weight = the opportunity's record count in that scenario / its largest scenario count).
  - vague memory success (44 records): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
  - alternative explanation (24 records): Some supporting records attribute the failure to missing or unindexed data rather than to the user's memory or the query.
  - known workaround exists (1 records): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

- **Unresolved:** Does the forgotten information actually cause the failure, or only co-occur with it? / How often does this happen per user per month (frequency cannot be measured from public posts)? / What did the user try that is not written in the post?

### Recognising the right photo (MEDIUM)
`candidate_recognition` · Help users recognise the intended photo among many visually similar candidates.


- **OBSERVATION**: 80 records from 7 sources map to this area.

- **OBSERVATION**: Unsuccessful outcome in 71/80 supporting records; abandonment signals in 22/80.

- **INSIGHT**: Most-remembered clues: person (43), visual appearance (32), place (25); most-forgotten: exact date (46), exact location (25), exact text (13).

- **INSIGHT**: Scenarios affected: food/restaurant (14), travel (12), wedding (10), event (9).

- **Evidence chain:** *symptom* (OBSERVATION): Outcomes among supporting records: not found 33, abandoned 21, uncertain 9, found 9, partly found 8. → *behavior* (OBSERVATION): Most frequent workarounds: manual scrolling, abandonment, date browsing. → *barrier* (INSIGHT): Most breakdowns (100%) are at one stage: can't pick out the right photo (D), i.e. the relevant photo may be present but the user struggles to recognise or distinguish it. → *potential root cause* (HYPOTHESIS): Users retain person, visual appearance, place but lack exact date, exact location, exact text; the retrieval path appears to break at the 'can't pick out the right photo (D)' stage. Validate in interviews before treating this as the cause.

- Evidence:
  - `EV-0ad93230f7` (app_store): “There are so many almost identical shots from that day that I can't tell which one it is.”
  - `EV-a7b99fe932` (forums): “I have hundreds of similar shots and can't tell which one it was.”
  - `EV-49f1afb5d3` (google_photos_community): “All the results look the same as tiny thumbnails.”

- **Challenging evidence:**
  - explicit counter evidence (79 records): Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity (labels: failure not search related, vague search succeeded). Scenario-weighted count: 38.6 (weight = the opportunity's record count in that scenario / its largest scenario count).
  - vague memory success (40 records): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
  - known workaround exists (2 records): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

- **Unresolved:** Does the forgotten information actually cause the failure, or only co-occur with it? / How often does this happen per user per month (frequency cannot be measured from public posts)? / What did the user try that is not written in the post?

### Recalling what the text said (MEDIUM)
`text_in_image_recall` · Help users retrieve documents, receipts and screenshots when they remember what the content was about but not its exact words.


- **OBSERVATION**: 55 records from 7 sources map to this area.

- **OBSERVATION**: Unsuccessful outcome in 48/55 supporting records; abandonment signals in 9/55.

- **INSIGHT**: Most-remembered clues: object (33), time approximation (24), visual appearance (23); most-forgotten: exact text (46), exact location (14), exact object name (14).

- **INSIGHT**: Scenarios affected: screenshot (20), receipt (13), document (13), medical/health image (9).

- **Evidence chain:** *symptom* (OBSERVATION): Outcomes among supporting records: not found 28, abandoned 9, found 7, uncertain 6, partly found 5. → *behavior* (OBSERVATION): Most frequent workarounds: other application, manual scrolling, repeated search. → *barrier* (INSIGHT): No single dominant breakdown stage: the most common, data missing or unsearchable (F), covers only 36% of breakdowns. → *potential root cause* (HYPOTHESIS): Users retain object, time approximation, visual appearance but lack exact text, exact location, exact object name; the retrieval path appears to break at several stages. Validate in interviews before treating this as the cause.

- Evidence:
  - `EV-148eb52b3e` (app_store): “The text on the bill isn't searchable as far as I can tell.”
  - `EV-83125bf4a4` (forums): “I just didn't know how to describe it in a way search would get.”
  - `EV-2cc48c3e17` (google_photos_community): “Text inside screenshots doesn't seem to be searchable.”

- **Challenging evidence:**
  - explicit counter evidence (29 records): Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity (labels: failure not search related, vague search succeeded). Scenario-weighted count: 20.8 (weight = the opportunity's record count in that scenario / its largest scenario count).
  - vague memory success (13 records): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
  - alternative explanation (20 records): Some supporting records attribute the failure to missing or unindexed data rather than to the user's memory or the query.
  - known workaround exists (1 records): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

- **Unresolved:** Does the forgotten information actually cause the failure, or only co-occur with it? / How often does this happen per user per month (frequency cannot be measured from public posts)? / What did the user try that is not written in the post?

### Trusting "no results" (MEDIUM)
`trust_in_search_completeness` · Help users judge whether a photo is absent from results versus absent from the library.


- **OBSERVATION**: 24 records from 7 sources map to this area.

- **OBSERVATION**: Unsuccessful outcome in 24/24 supporting records; abandonment signals in 10/24.

- **INSIGHT**: Most-remembered clues: person (11), object (10), place (8); most-forgotten: exact date (13), exact location (6), exact text (6).

- **INSIGHT**: Scenarios affected: document (5), screenshot (4), object (3), event (3).

- **Evidence chain:** *symptom* (OBSERVATION): Outcomes among supporting records: not found 14, abandoned 10. → *behavior* (OBSERVATION): Most frequent workarounds: abandonment, manual scrolling, other application. → *barrier* (INSIGHT): Most breakdowns (100%) are at one stage: photo never surfaces (C), i.e. the relevant photo does not appear or is insufficiently surfaced. → *potential root cause* (HYPOTHESIS): Users retain person, object, place but lack exact date, exact location, exact text; the retrieval path appears to break at the 'photo never surfaces (C)' stage. Validate in interviews before treating this as the cause.

- Evidence:
  - `EV-f1f4df3aaa` (app_store): “I typed "agreement" in search and got no results.”
  - `EV-05fd7991f1` (forums): “I typed "girl laughing covered in yellow with marigolds" in search and nothing came up.”
  - `EV-89c15fc252` (google_photos_community): “I searched "wedding" and nothing came up.”

- **Challenging evidence:**
  - explicit counter evidence (28 records): Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity (labels: vague search succeeded). Scenario-weighted count: 11.8 (weight = the opportunity's record count in that scenario / its largest scenario count).
  - vague memory success (36 records): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
  - known workaround exists (1 records): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

- **Unresolved:** Does the forgotten information actually cause the failure, or only co-occur with it? / How often does this happen per user per month (frequency cannot be measured from public posts)? / What did the user try that is not written in the post?

## 12. Opportunity Comparison
| Opportunity | Records | Signals | Sources | Vague-memory cases | Unsuccessful | Abandon | Refuting records | Vague-memory successes | Strength |
|---|---|---|---|---|---|---|---|---|---|
| Missing or unsearchable data | 120 | 2080 | 7 | 84/120 (70.0%) | 71/120 (59.2%) | 20/120 (16.7%) | 0 | 49 | HIGH |
| Recovering after a failed search | 225 | 5310 | 7 | 214/225 (95.1%) | 184/225 (81.8%) | 85/225 (37.8%) | 108 | 50 | MEDIUM |
| Combining several weak clues | 131 | 3188 | 7 | 125/131 (95.4%) | 103/131 (78.6%) | 25/131 (19.1%) | 108 | 50 | MEDIUM |
| Turning context into search terms | 93 | 1944 | 7 | 87/93 (93.5%) | 73/93 (78.5%) | 17/93 (18.3%) | 104 | 48 | MEDIUM |
| Anchoring a rough sense of time | 85 | 2042 | 7 | 85/85 (100.0%) | 66/85 (77.6%) | 19/85 (22.4%) | 89 | 44 | MEDIUM |
| Recognising the right photo | 80 | 1930 | 7 | 78/80 (97.5%) | 71/80 (88.8%) | 22/80 (27.5%) | 79 | 40 | MEDIUM |
| Recalling what the text said | 55 | 1141 | 7 | 52/55 (94.5%) | 48/55 (87.3%) | 9/55 (16.4%) | 29 | 13 | MEDIUM |
| Trusting "no results" | 24 | 543 | 7 | 23/24 (95.8%) † | 24/24 (100.0%) † | 10/24 (41.7%) † | 28 | 36 | MEDIUM |

Evidence-strength rules: HIGH: {'min_records': 30, 'min_sources': 4, 'min_behavioral_share': 0.6, 'max_contradiction_ratio': 0.2}; MEDIUM: {'min_records': 12, 'min_sources': 3, 'min_behavioral_share': 0.4, 'max_contradiction_ratio': 0.35}; LOW: {'min_records': 5, 'min_sources': 2, 'min_behavioral_share': 0.0, 'max_contradiction_ratio': 1.0}

## 13. Leading Opportunity (proposal for PM review)
**Anchoring a rough sense of time**, runner-up **Recognising the right photo**.

Selection rule: 1) keep opportunities at the best available evidence level (MEDIUM or better when any exist); 2) order by share of vague-memory cases (the business metric's population); 3) then by share of unsuccessful outcomes; 4) then by number of independent sources. This is a proposal for the PM to accept or override, not a decision.

| Opportunity | Strength | Vague-memory % | Unsuccessful % | Sources | Records |
|---|---|---|---|---|---|
| Anchoring a rough sense of time | MEDIUM | 100.0 | 77.6 | 7 | 85 |
| Recognising the right photo | MEDIUM | 97.5 | 88.8 | 7 | 80 |
| Trusting "no results" | MEDIUM | 95.8 | 100.0 | 7 | 24 |
| Combining several weak clues | MEDIUM | 95.4 | 78.6 | 7 | 131 |
| Recovering after a failed search | MEDIUM | 95.1 | 81.8 | 7 | 225 |
| Recalling what the text said | MEDIUM | 94.5 | 87.3 | 7 | 55 |
| Turning context into search terms | MEDIUM | 93.5 | 78.5 | 7 | 93 |
| Missing or unsearchable data | HIGH | 70.0 | 59.2 | 7 | 120 |

## 14. Research Hypotheses

### Anchoring a rough sense of time (evidence: MEDIUM)
**WE BELIEVE users know roughly when a memory happened, relative to a life event or season, but not the date needed to navigate to it.**

**BECAUSE**
- 85/85 supporting records describe both remembered and forgotten information.
- No single dominant breakdown stage; the most common, data missing or unsearchable (F), covers 28%.
- Unsuccessful outcomes in 66/85; abandonment signals in 19/85.
- Top forgotten: exact date, exact location, exact object name. Top workarounds: date browsing, manual scrolling, abandonment.

**WE EXPECT TO OBSERVE**
- time described relative to other events ('before covid', 'when he was one')
- jumping to a guessed year and scrolling month by month
- several date guesses before landing in the right period

**WE NEED TO VALIDATE**
- Whether this happens outside public complaint posts, in document, travel retrieval, for the participants recruited.
- Whether the breakdown is at the stage the evidence suggests or earlier in the journey.

**WOULD FALSIFY**
- users recall the year accurately
- date navigation is quick once any anchor is known

Evidence:
  - `EV-4950c5088e` (app_store): “Timing wise it was a few years back.”
  - `EV-ef7a18108e` (app_store): “It was in 2018 or 2019, can't pin it down.”
  - `EV-347cf7d093` (app_store): “I jumped to roughly that year with the scrollbar and went month by month.”

### Recognising the right photo (evidence: MEDIUM)
**WE BELIEVE the intended photo is often reachable, but users cannot pick it out among many near-identical candidates, especially when retrieving food/restaurant, travel memories.**

**BECAUSE**
- 78/80 supporting records describe both remembered and forgotten information.
- Most breakdowns (100%) are at one stage: can't pick out the right photo (D).
- Unsuccessful outcomes in 71/80; abandonment signals in 22/80.
- Top forgotten: exact date, exact location, exact text. Top workarounds: manual scrolling, abandonment, date browsing.

**WE EXPECT TO OBSERVE**
- users reaching the right day or event quickly and then spending most of their time comparing thumbnails
- opening many full-size photos to check details
- settling for a 'close enough' photo

**WE NEED TO VALIDATE**
- Whether this happens outside public complaint posts, in food/restaurant, travel retrieval, for the participants recruited.
- Whether the breakdown is at the stage the evidence suggests or earlier in the journey.

**WOULD FALSIFY**
- users rarely see the right event in results
- users recognise the photo instantly once it appears

Evidence:
  - `EV-0ad93230f7` (app_store): “There are so many almost identical shots from that day that I can't tell which one it is.”
  - `EV-a7b99fe932` (forums): “I have hundreds of similar shots and can't tell which one it was.”
  - `EV-49f1afb5d3` (google_photos_community): “All the results look the same as tiny thumbnails.”

### Missing or unsearchable data (evidence: HIGH)
**WE BELIEVE a share of failures happen because the needed item or its information is missing, unindexed or outside the searched library, not because of memory or query.**

**BECAUSE**
- 84/120 supporting records describe both remembered and forgotten information.
- Most breakdowns (100%) are at one stage: data missing or unsearchable (F).
- Unsuccessful outcomes in 71/120; abandonment signals in 20/120.
- Top forgotten: exact date, exact location, exact text. Top workarounds: manual scrolling, abandonment, synonym search.

**WE EXPECT TO OBSERVE**
- items from old phones, shared/partner libraries, chats or screen recordings
- users unsure whether the photo still exists
- failures even when users use the right clue

**WE NEED TO VALIDATE**
- Whether this happens outside public complaint posts, in video, document retrieval, for the participants recruited.
- Whether the breakdown is at the stage the evidence suggests or earlier in the journey.

**WOULD FALSIFY**
- the item turns out to be present and findable with a different query
- missing-data cases are rare in recent libraries

Evidence:
  - `EV-148eb52b3e` (app_store): “The text on the bill isn't searchable as far as I can tell.”
  - `EV-a35c4f9e02` (forums): “For context, location was probably off on my phone.”
  - `EV-1c1f891466` (app_store): “The location data was probably off.”

### Recovering after a failed search (evidence: MEDIUM)
**WE BELIEVE after the first failed search, users lack a sense of what to try next and fall back to exhaustive scrolling or giving up.**

**BECAUSE**
- 214/225 supporting records describe both remembered and forgotten information.
- No single dominant breakdown stage; the most common, can't pick out the right photo (D), covers 26%.
- Unsuccessful outcomes in 184/225; abandonment signals in 85/225.
- Top forgotten: exact date, exact location, exact text. Top workarounds: manual scrolling, abandonment, date browsing.

**WE EXPECT TO OBSERVE**
- one or two reformulations, then abandonment of search as a strategy
- long manual scrolling sessions
- returning to the task later or asking someone else

**WE NEED TO VALIDATE**
- Whether this happens outside public complaint posts, in travel, event retrieval, for the participants recruited.
- Whether the breakdown is at the stage the evidence suggests or earlier in the journey.

**WOULD FALSIFY**
- users systematically try other strategies (people, places, dates) after a failure
- abandonment is caused by lack of time, not lack of next steps

Evidence:
  - `EV-c57f323d5a` (app_store): “I didn't know what else to try.”
  - `EV-081d3df466` (forums): “I didn't know what else to try.”
  - `EV-aabab236ac` (app_store): “I scrolled for like 40 minutes.”

### Combining several weak clues (evidence: MEDIUM)
**WE BELIEVE users hold several weak clues (person, visual appearance, time approximation) that each return too much or the wrong thing, and they cannot combine them into one retrieval.**

**BECAUSE**
- 125/131 supporting records describe both remembered and forgotten information.
- No single dominant breakdown stage; the most common, search misreads the clue (B), covers 34%.
- Unsuccessful outcomes in 103/131; abandonment signals in 25/131.
- Top forgotten: exact date, exact location, exact object name. Top workarounds: manual scrolling, date browsing, abandonment.

**WE EXPECT TO OBSERVE**
- long descriptive queries that return results matching only one clue
- users dropping clues to 'simplify' the search
- frustration that results ignore part of the description

**WE NEED TO VALIDATE**
- Whether this happens outside public complaint posts, in food/restaurant, event retrieval, for the participants recruited.
- Whether the breakdown is at the stage the evidence suggests or earlier in the journey.

**WOULD FALSIFY**
- single-clue queries succeed as often as multi-clue ones
- users do not naturally hold more than one clue

Evidence:
  - `EV-a6ef59612b` (app_store): “It doesn't understand what I'm describing at all.”
  - `EV-9f3f101c9d` (forums): “It doesn't understand what I'm describing at all.”
  - `EV-ca8e947600` (app_store): “Searched for "hammock between coconut trees near beach homestay"”

### Turning context into search terms (evidence: MEDIUM)
**WE BELIEVE users in document, screenshot remember a memory through time approximation, object, visual appearance but cannot turn it into terms the search accepts.**

**BECAUSE**
- 87/93 supporting records describe both remembered and forgotten information.
- Most breakdowns (96%) are at one stage: can't express the memory (A).
- Unsuccessful outcomes in 73/93; abandonment signals in 17/93.
- Top forgotten: exact date, exact text, exact location. Top workarounds: manual scrolling, other application, abandonment.

**WE EXPECT TO OBSERVE**
- describing the memory as an event or experience before naming any object
- a first query that is a noun guess, not the remembered context
- switching to scrolling once the guessed words fail

**WE NEED TO VALIDATE**
- Whether this happens outside public complaint posts, in document, screenshot retrieval, for the participants recruited.
- Whether the breakdown is at the stage the evidence suggests or earlier in the journey.

**WOULD FALSIFY**
- users say they knew the right word and search still failed
- the first query already used the remembered context and succeeded

Evidence:
  - `EV-c4a228c828` (app_store): “How do you even search for something like that?”
  - `EV-07b96b7773` (google_photos_community): “I don't know what word the app would use for it.”
  - `EV-f4e20ba5d0` (app_store): “We were at the furniture shop when I took it.”

### Recalling what the text said (evidence: MEDIUM)
**WE BELIEVE users retrieving screenshot, receipt remember what the content was about (object, time approximation, visual appearance) but not the exact words, numbers or names printed on it.**

**BECAUSE**
- 52/55 supporting records describe both remembered and forgotten information.
- No single dominant breakdown stage; the most common, data missing or unsearchable (F), covers 36%.
- Unsuccessful outcomes in 48/55; abandonment signals in 9/55.
- Top forgotten: exact text, exact location, exact object name. Top workarounds: other application, manual scrolling, repeated search.

**WE EXPECT TO OBSERVE**
- searches for the document type ('bill', 'report') rather than its contents
- urgency tied to an external deadline
- workarounds in other apps (email, chat) where the item was shared

**WE NEED TO VALIDATE**
- Whether this happens outside public complaint posts, in screenshot, receipt retrieval, for the participants recruited.
- Whether the breakdown is at the stage the evidence suggests or earlier in the journey.

**WOULD FALSIFY**
- users remember exact words and search still misses them (points to index coverage instead)
- users rarely photograph documents they later need

Evidence:
  - `EV-d67481bd27` (app_store): “I don't remember the exact words on it.”
  - `EV-91d4d1405d` (forums): “I don't remember the exact words on it.”
  - `EV-55143c65ec` (app_store): “It had the PNR number on it.”

### Trusting "no results" (evidence: MEDIUM)
**WE BELIEVE when search returns nothing, users cannot tell whether the photo is absent from the library or only from the results.**

**BECAUSE**
- 23/24 supporting records describe both remembered and forgotten information.
- Most breakdowns (100%) are at one stage: photo never surfaces (C).
- Unsuccessful outcomes in 24/24; abandonment signals in 10/24.
- Top forgotten: exact date, exact location, exact text. Top workarounds: abandonment, manual scrolling, other application.

**WE EXPECT TO OBSERVE**
- repeated identical searches
- users checking other devices or backups
- users concluding the photo was lost when it exists

**WE NEED TO VALIDATE**
- Whether this happens outside public complaint posts, in document, screenshot retrieval, for the participants recruited.
- Whether the breakdown is at the stage the evidence suggests or earlier in the journey.

**WOULD FALSIFY**
- users trust 'no results' and move on quickly
- the photo is genuinely absent in most cases

Evidence:
  - `EV-f1f4df3aaa` (app_store): “I typed "agreement" in search and got no results.”
  - `EV-05fd7991f1` (forums): “I typed "girl laughing covered in yellow with marigolds" in search and nothing came up.”
  - `EV-89c15fc252` (google_photos_community): “I searched "wedding" and nothing came up.”

## 15. Problem Definition (draft)
> DRAFT — built from discovery evidence only. Interviews (Part 3) confirm, refine or kill each field.

### Target user segment (INTERPRETATION)

Contextual Retrieval

*Together these cover 156 of 156 records (100.0%) behind the two tested opportunities. Suggested mix of 6 interviews: 6 × Contextual Retrieval (156 records).*

**To settle in interviews:** Do participants recruited this way actually recognise the episode we think they have?

### Retrieval scenario (OBSERVATION)

Retrieving document, travel, family items from a personal library, months or years later, while still remembering time approximation, person, visual appearance and no longer holding exact date, exact location.

  - `EV-4950c5088e` (app_store): “Timing wise it was a few years back.”
  - `EV-5fb5b26049` (forums): “Does anyone know how to find that picture from the trip where we stayed near the beach?”

### Product outcome to influence (INTERPRETATION)

Needed items and their context are retrievable at all — Fewer attempts fail because the item or the information needed to find it is missing or unindexed.

### Root cause of retrieval failure (HYPOTHESIS)

Users retain time approximation, person, visual appearance but lack exact date, exact location, exact object name; the retrieval path appears to break at several stages. Validate in interviews before treating this as the cause.

**To settle in interviews:** Is this the cause, or does the attempt already fail earlier, before the query is typed?

  - `EV-4950c5088e` (app_store): “Timing wise it was a few years back.”
  - `EV-5fb5b26049` (forums): “Does anyone know how to find that picture from the trip where we stayed near the beach?”

### Existing user workarounds (OBSERVATION)

date browsing, manual scrolling, abandonment, other application

  - `EV-02768ec646` (app_store): “I jumped to roughly that year with the scrollbar and went month by month.”
  - `EV-00853dd800` (forums): “I jumped to roughly that year with the scrollbar and went month by month.”

### Why solving it creates user value (INTERPRETATION)

Attempts are prompted by a concrete need with a deadline attached (a claim, a booking, a gift, a request from someone else), so failure costs the user the task, not just the photo. Abandonment appears in 19/85 supporting records.

**To settle in interviews:** What did the user do instead when they gave up, and what did that cost them?

  - `app_store:app-0025` (app_store): “I need it because I was telling someone about the trip and wanted to show them.”
  - `forums:for-0001` (forums): “I need it now because I want to book the same homestay.”

### Why it makes business sense (INTERPRETATION)

The business metric is successful retrieval of vaguely remembered photos. Today 180/552 attempts in the corpus end in a confirmed find (32.6%), and 324 end unresolved. The stage with the largest recoverable share is match (up to 13.4 points). A library that cannot return its own contents weakens the reason to keep adding to it.

**Open, not answerable from public posts:**
- How often does this happen per user per month? Public posts cannot answer this; product telemetry or a diary study can.
- Does retrieval failure change backup, storage-tier or app-open behaviour? That needs company data this study has no access to.

### What this problem is not (INTERPRETATION)

Not 'users find it difficult to search for old photos'. The evidence is narrower: users arrive with real clues (time approximation, person, visual appearance) and still fail, because exact date, exact location, exact object name is missing and the retrieval path needs it.

### Competing explanation to rule out (HYPOTHESIS)

Runner-up: Recognising the right photo. Help users recognise the intended photo among many visually similar candidates.

### How the thinking evolved
1. **Business metric** (GIVEN): Increase the share of users who successfully retrieve a photo they remember but cannot precisely describe.
2. **Product outcomes** (INTERPRETATION): Decomposed into the five things that must go right: recall → express → match → recognize → recover, plus whether the item is retrievable at all.
3. **AI-powered discovery** (OBSERVATION): 840 records analysed; 577 about retrieval; 552 first-person attempts, each signal carrying a verbatim quote.
4. **Observed user behaviour** (OBSERVATION): Most-remembered clues: person, time approximation, object; most-forgotten: exact date, exact location, exact text; breakdowns concentrate at match, data, express.
5. **Problem definition** (DRAFT): Stated above, pending the 5–6 interviews. Each field carries either evidence or an open question, never an assumed finding.

## JTBD candidates (INTERPRETATION)

- *Anchoring a rough sense of time*: WHEN I need a document, travel item I remember through time approximation, person, visual appearance, BUT I cannot recall exact date, exact location, exact object name, PLEASE HELP ME get from the clues I do have to the specific item, SO I can act on the need that prompted the search (see goal evidence). (stated goals in 59/85 records)
  - `app_store:app-0025` (app_store): “I need it because I was telling someone about the trip and wanted to show them.”
  - `forums:for-0001` (forums): “I need it now because I want to book the same homestay.”

- *Recognising the right photo*: WHEN I need a food/restaurant, travel item I remember through person, visual appearance, place, BUT I cannot recall exact date, exact location, exact text, PLEASE HELP ME get from the clues I do have to the specific item, SO I can act on the need that prompted the search (see goal evidence). (stated goals in 43/80 records)
  - `app_store:app-0012` (app_store): “I need it because I want to use it as a wallpaper again.”
  - `forums:for-0002` (forums): “I need it because the artist asked for a before picture.”

- *Missing or unsearchable data*: WHEN I need a video, document item I remember through person, time approximation, object, BUT I cannot recall exact date, exact location, exact text, PLEASE HELP ME get from the clues I do have to the specific item, SO I can act on the need that prompted the search (see goal evidence). (stated goals in 52/120 records)
  - `app_store:app-0014` (app_store): “I need it now because there's a sale now.”
  - `forums:for-0001` (forums): “I need it now because I want to book the same homestay.”
