# Google Photos Retrieval — Product Discovery Report

> **REPRESENTATIVE DATASET.** All counts are *X of Y records in a real corpus* (`google_photos_raw_dataset.csv`). They are not Google Photos user research, not population statistics, not Google internal data. They show directional patterns and hypotheses only.
>
> **PROPOSED RESEARCH PLAN — NOT RESEARCH FINDINGS.** No interviews, tests or surveys have been run; nothing in §9–§12 is a participant result.

Label key: `[RAW]` verbatim record · `[OBS]` observed behaviour in the corpus (a count) · `[INTERP]` interpretation · `[OPP-HYP]` opportunity hypothesis · `[PROB-HYP]` problem hypothesis · `[VALIDATED]` validated problem (**none yet**) · `[ASSUME]` assumption · `[UNKNOWN]` not knowable from this data

Record IDs trace every conclusion; the full list behind each named group is in `output/evidence_index.csv`. Method, the discovery chain, structure tests and the file map are in `output/discovery_appendix.md`.

## 1. Dataset Quality & Relevance

| Classification | Records | Basis |
|---|---|---|
| **Retrieval-related** | **800** of 840 | Contains a retrieval object, a memory statement and a behaviour/outcome statement about finding an existing photo (IDs `REC-0001…`) |
| Possibly retrieval-related | 3 | 'I accidentally deleted a photo and need to restore it': intent is to get a photo back, but it is a restore flow with no memory or search-behaviour evidence. Excluded from all denominators |
| Not retrieval-related | 37 | Single-sentence `REC-N…` records on sharing, settings, storage, battery, backup, editing, printing, collage, face-grouping defect |
| Insufficient evidence | 0 | None: every non-relevant record is unambiguous |
| Ambiguous retrieval intent | 0 | None by the rules above; the 3 'possibly' records are the nearest case |

All 800 relevant records are retained, including those where the user eventually found the photo. `[OBS]` These counts describe this file only.

**Duplicates / low information**
- Exact-duplicate text: 28 records overall (3 among relevant, 25 among the off-topic set, which reuses only 15 sentences). Retained; the target segment changes 404 → 351 after near-duplicate removal.
- Near-duplicates (same object + memory + behaviour + closer, different opener): 222 records in repeated groups (123 extra copies).
- Extremely low-information: 40 records (single sentence), all off-topic. Among relevant records, 800 have no closing sentence but still carry object, memory and behaviour.

**Important data-quality limitations**
1. **Template-composed text.** The 840 records use only 90 distinct sentences in a fixed order (opener → object → memory → one behaviour/outcome → optional closer). Frequencies reflect how the file was generated, not how often anything happens.
2. **No cross-field structure beyond chance.** Object×memory, memory×behaviour, object×state and source×state associations are all statistically indistinguishable from independence (Cramér's V ≤ nan, smallest p = 0.647; table in the appendix). So "screenshot searchers behave differently" or "Reddit users fail more" cannot be claimed from this data. This also confirms that source/platform is not a usable segmentation axis, and it means the case's question 'what kinds of old photos do users struggle to retrieve?' has no data-supported answer beyond the object mix.
3. **Semantic mismatches.** 0 of 215 document/screenshot/object records pair the item with people/place/album memory. Object-specific memory conclusions are unsafe.
4. **Outcome is sparse and partly circular.** Only 800 of 800 relevant records state an outcome; 0 are unknown. Outcome sits in the same sentence that defines the retrieval state, so 'outcome by segment' restates the definition; it is not independent evidence.
5. **Complaint-selected corpus.** Every relevant record is a help-seeking or complaint post. There are 0 records of quick, uneventful retrieval, so success/failure *rates* and any baseline are unobservable `[UNKNOWN]`.
6. **Framing sentences are not behaviour.** Openers such as 'The search is frustrating' (0) and 'Google Photos, please make this easier' (0) were kept as text but not used as evidence (no sentiment analysis; no solution inferred from the vendor request).
7. **Metadata not used analytically.** `engagement`, `author_id` (840 records share an author id with another) and `date_posted` ( to ) were not used.
8. **Object classes are partly my grouping.** 308 of 800 records name an object whose class is a judgement call (11 of 30 distinct objects; e.g. 'the old meme I saved', 'our Diwali family photo'). Each carries an alternative class in `coded_records.csv` (`object_class_alt`), and 'a yellow truck' is left as *Unspecified*. No finding in this report depends on the class, because object is independent of memory and behaviour.

## 2. Retrieval Need Landscape

Needs come from what records say users remember, lack and do, never from source. They overlap. Shares are of 800 relevant records. Behaviour lists mirror the corpus overall because behaviour is independent of memory pattern here (§1).

| Need | User goal | Memory pattern | Behaviour (most common stated) | Outcome (stated) | Evidence |
|---|---|---|---|---|---|
| **N1 Retrieve a photo when the date is only approximately known** | Find a specific photo when only an approximate date is known | People/situation without the date; roughly when but not the day; year but not the month |  | no outcome stated; 0 unknown | 0 of 800 (0.0%); [RAW]  (all 0: `evidence_index.csv` → `need:N1`) |
| **N2 Retrieve a photo remembered by appearance/gist but lacking a name, keyword or wording** | Find a photo remembered by look or gist | Object look/colour/setting without a name or keyword; visual detail hard to describe; activity without exact words |  | no outcome stated; 0 unknown | 0 of 800 (0.0%); [RAW]  (all 0: `evidence_index.csv` → `need:N2`) |
| **N3 Retrieve a photo remembered by story, people and activity but lacking an organising handle (album)** | Find a photo remembered as a story | Story more vivid than metadata; who was there and what they were doing, but not the album |  | no outcome stated; 0 unknown | 0 of 800 (0.0%); [RAW]  (all 0: `evidence_index.csv` → `need:N3`) |
| **N4 Retrieve a place-based memory without the place name** | Find a place-based memory | Place remembered generally, not its name |  | no outcome stated; 0 unknown | 0 of 800 (0.0%); [RAW]  (all 0: `evidence_index.csv` → `need:N4`) |
| **N5 Re-find a photo known to exist after losing the original path to it** | Re-find a photo known to exist | Knows it exists, cannot recall how it was originally found |  | no outcome stated; 0 unknown | 0 of 800 (0.0%); [RAW]  (all 0: `evidence_index.csv` → `need:N5`) |
| **N6 Recognise/verify the right photo among plausible candidates** | Confirm the intended photo among plausible candidates | Sees many plausible results / a similar photo and cannot tell which is right |  | 120 similar-but-uncertain; 0 unknown | 120 of 800 (15.0%); [RAW] REC-0001, REC-0004 (all 120: `evidence_index.csv` → `need:N6`) |
| **N7 Reach a photo the user says they would recognise but cannot narrow towards** | Reach a photo they say they would recognise | 'Can recognise it if I see it' but does not know how to narrow |  | no outcome stated; 0 unknown | 0 of 800 (0.0%); [RAW]  (all 0: `evidence_index.csv` → `need:N7`) |
| **N8 Recover after a first attempt did not resolve** | Recover after the first attempt does not resolve | Any; defined by behaviour (reformulation, switching, giving up, other app) |  | 114 found-with-effort, 140 failed, 115 abandoned, 86 other-app/device workaround; 0 unknown | 625 of 800 (78.1%); [RAW] REC-0002, REC-0003 (all 625: `evidence_index.csv` → `need:N8`) |
| **N9 Retrieve an information-bearing image (document, screenshot, prescription)** | Retrieve an information-bearing image | Object is a document, screenshot or prescription/medical image (memory text is generic; see limitation 3) |  | 38 found-with-effort, 37 similar-but-uncertain, 49 failed, 36 abandoned, 28 other-app/device workaround; 0 unknown | 257 of 800 (32.1%); [RAW] REC-0002, REC-0004 (all 257: `evidence_index.csv` → `need:N9`) |

**Need detail: retrieval context and journey stages involved** (Stage 3 fields)

| Need | Retrieval context `[OBS]` | Journey stages involved (records touching each) | Memory characteristics |
|---|---|---|---|
| N1 | objects: ; library size stated in 0 of 0 | Recall 0, Express 0, Match 0, Recognize 0, Recover 0 | remembers: ; lacks:  |
| N2 | objects: ; library size stated in 0 of 0 | Recall 0, Express 0, Match 0, Recognize 0, Recover 0 | remembers: ; lacks:  |
| N3 | objects: ; library size stated in 0 of 0 | Recall 0, Express 0, Match 0, Recognize 0, Recover 0 | remembers: ; lacks:  |
| N4 | objects: ; library size stated in 0 of 0 | Recall 0, Express 0, Match 0, Recognize 0, Recover 0 | remembers: ; lacks:  |
| N5 | objects: ; library size stated in 0 of 0 | Recall 0, Express 0, Match 0, Recognize 0, Recover 0 | remembers: ; lacks:  |
| N6 | objects: family person 27, document screenshot 22, event social 20; library size stated in 0 of 120 | Recall 120, Express 66, Match 120, Recognize 120, Recover 36 | remembers: people 33, approximate time 26, visual appearance 18; lacks: time precision 37, don't explicitly state 28, name 24 |
| N7 | objects: ; library size stated in 0 of 0 | Recall 0, Express 0, Match 0, Recognize 0, Recover 0 | remembers: ; lacks:  |
| N8 | objects: family person 145, document screenshot 128, event social 102; library size stated in 0 of 625 | Recall 625, Express 484, Match 0, Recognize 0, Recover 625 | remembers: people 151, visual appearance 110, activity 99; lacks: don't explicitly state 169, time precision 146, name 113 |
| N9 | objects: document screenshot 161, medical 96; library size stated in 0 of 257 | Recall 257, Express 186, Match 37, Recognize 37, Recover 214 | remembers: people 68, visual appearance 51, activity 44; lacks: don't explicitly state 66, name 54, time precision 51 |

`[INTERP]` The needs fall into three families: **(a) memory-to-query gaps** (N1–N5, N7: the user holds context but lacks a usable identifier), **(b) verification** (N6) and **(c) recovery** (N8). Every relevant record states an imprecise or hard-to-use memory (594 name specific missing information; the other 206 describe memory the user cannot readily use as an identifier, which is an interpretation). No record describes retrieval by a precise identifier, so a Direct-vs-Contextual split has nothing to split here; the only Direct-side signal is the contrast sentence 'It feels much easier when I know an exact date or person's name' (0 records).

**Answers to the case's sample questions** (with what the data can and cannot support)

| Case question | Answer from this corpus | Limit |
|---|---|---|
| What kinds of old photos do users struggle to retrieve? | `[OBS]` Objects span Family / person memory 183, Document / screenshot / saved image 161, Event / social occasion 134, Medical-related image 121, Trip / place memory 121, Physical object / product 54. | No class struggles more than chance (object is independent of behaviour and outcome), so no ranking of kinds is supportable |
| What do people actually remember? | `[OBS]` people 200, visual appearance 134, approximate time 126, activity 119, story 82, object 78, situation 73, place 71 (records naming each). | Memory statements are template sentences; richness of real memory is `[UNKNOWN]` |
| What have they forgotten? | `[OBS]` don't explicitly state 206, time precision 199, name 149, search keyword 64, album / organisation 63, how it was originally found 63, exact wording 56. Time precision is the largest named family. | 'Don't explicitly state' = memory stated without a named gap |
| How do users formulate searches when memory is incomplete? | `[OBS]` See the behaviour table below: first-attempt input strategies 0, date-based narrowing 0, reformulation 0, strategy switching 0. | One behaviour sentence per record; sequences within a record are not observable |

**How users searched (Stage 1E: one stated behaviour per record)** `[OBS]`

| Behaviour group | Records | Members | Example records |
|---|---|---|---|
| First-attempt input strategies | 0 of 800 (0.0%) | person place search 0; text in image search 0; object keyword 0 |  |
| Date-based narrowing | 0 of 800 (0.0%) | date search too many 0; date range compare 0 |  |
| Reformulation (different or several related words) | 0 of 800 (0.0%) | different wording 0; several related words 0 |  |
| Switching strategy (terms/albums, person then browse, keywords then scroll) | 0 of 800 (0.0%) | switch terms albums 0; person then browse 0; keywords then scroll 0 |  |
| Manual inspection and browsing | 0 of 800 (0.0%) | open results one by one 0; timeline manual 0; large thumbnail set 0 |  |
| Outcome stated in the same sentence (similar-not-exact, several attempts) | 0 of 800 (0.0%) | similar not exact 0; found after several attempts 0 |  |
| Exit (could not find, gave up and asked someone, other app/device) | 0 of 800 (0.0%) | other device or app 0; gave up asked someone 0; could not find 0 |  |

**Stated outcomes across all relevant records (every category in the brief; unstated is never inferred)** `[OBS]`

| Outcome | Records |
|---|---|
| Found quickly | 55 of 800 (6.9%) |
| Found with effort | 114 of 800 (14.2%) |
| Found after reformulation | 41 of 800 (5.1%) |
| Found after browsing | 129 of 800 (16.1%) |
| Similar result but uncertain | 120 of 800 (15.0%) |
| Failed | 140 of 800 (17.5%) |
| Abandoned | 115 of 800 (14.4%) |
| External workaround | 86 of 800 (10.8%) |
| Outcome Not Stated | 0 of 800 (0.0%) |

**Retrieval objects** (context, not segments): Family / person memory 183; Document / screenshot / saved image 161; Event / social occasion 134; Medical-related image 121; Trip / place memory 121; Physical object / product 54; Unspecified (described by appearance only) 26 (of 800).

## 3. Behavioral Segments

Segments are observable *retrieval states* stated in each record's single behaviour/outcome sentence, so SEG-1…4 are mutually exclusive and sum to 800. All share one precondition: a specific photo the user expects to exist, with imprecise memory of it. They correspond to the retrieval-state lens (unresolved / recovery-dependent / candidate-heavy); no 'direct / low-effort' state exists in this corpus.

| Segment | Objective definition | Records | Typical behaviour | Failure / effort | Outcome (stated) |
|---|---|---|---|---|---|
| **SEG-1 Exit-path retrievers** | Record states the user could not find the photo, gave up and asked someone else, or switched to another device/app (B12, B10, B08). | 341 of 800 (42.6%); [RAW] REC-0002, REC-0003 (all 341: `evidence_index.csv` → `seg:SEG-1`) |  | 341 with ≥1 severity signal; 251 with ≥2 | 140 failed, 115 abandoned, 86 other-app/device workaround; 0 unknown |
| **SEG-2 Recovery-dependent retrievers** | Record states the user reformulated, switched strategy, fell back to browsing after a search, or needed several attempts (B05, B07, B09, B15, B17, B18). | 284 of 800 (35.5%); [RAW] REC-0005, REC-0006 (all 284: `evidence_index.csv` → `seg:SEG-2`) |  | 284 with ≥1 severity signal; 192 with ≥2 | 114 found-with-effort; 0 unknown |
| **SEG-3 Candidate-inspection-dependent retrievers** | Record states manual candidate inspection or an unmanageable/uncertain candidate set: date search with too many results, opening results one by one, manual timeline, very large thumbnail set, date-range comparison, similar-but-not-exact (B03, B04, B11, B13, B14, B16). | 120 of 800 (15.0%); [RAW] REC-0001, REC-0004 (all 120: `evidence_index.csv` → `seg:SEG-3`) |  | 120 with ≥1 severity signal; 64 with ≥2 | 120 similar-but-uncertain; 0 unknown |
| **SEG-4 First-attempt-stage retrievers** | Record states one initial search (person+place, text-in-image, object keyword) with no reformulation, browsing or outcome (B01, B02, B06). | 55 of 800 (6.9%); [RAW] REC-0025, REC-0029 (all 55: `evidence_index.csv` → `seg:SEG-4`) |  | 3 with ≥1 severity signal; 3 with ≥2 | no outcome stated; 0 unknown |
| **SEG-T Effortful-path retrievers (SEG-2 or SEG-3)** | Union of SEG-2 and SEG-3: attempted to retrieve a specific photo they expected to exist, lacked a precise identifier, and either changed strategy/repeated attempts or manually inspected a candidate set. | 404 of 800 (50.5%); [RAW] REC-0001, REC-0004 (all 404: `evidence_index.csv` → `seg:SEG-T`) |  | 404 with ≥1 severity signal; 256 with ≥2 | 114 found-with-effort, 120 similar-but-uncertain; 0 unknown |

**Segment profile: what they remember, forget, do, and how it ended** (Stage 4) `[OBS]`

| Segment | Remember | Forget | Do | Found quickly | Found with effort | Uncertain | Failed | Abandoned | Other-app workaround | Outcome Not Stated |
|---|---|---|---|---|---|---|---|---|---|---|
| SEG-1 | people 83, approximate time 58, visual appearance 56 | time precision 93, don't explicitly state 85, name 63 |  | 0 | 0 | 0 | 140 | 115 | 86 | 0 |
| SEG-2 | people 68, visual appearance 54, activity 47 | don't explicitly state 84, time precision 53, name 50 |  | 0 | 114 | 0 | 0 | 0 | 0 | 0 |
| SEG-3 | people 33, approximate time 26, visual appearance 18 | time precision 37, don't explicitly state 28, name 24 |  | 0 | 0 | 120 | 0 | 0 | 0 | 0 |
| SEG-4 | people 16, approximate time 10, activity 9 | time precision 16, name 12, don't explicitly state 9 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| SEG-T | people 101, visual appearance 72, activity 58 | don't explicitly state 112, time precision 90, name 74 |  | 0 | 114 | 120 | 0 | 0 | 0 | 0 |

**Severity signals by segment** (records carrying each signal) `[OBS]`

| Segment | browsing | uncertainty | strategy switch | large candidate set | repeated attempts | failure | external workaround | abandonment | reformulation | candidate inspection |
|---|---|---|---|---|---|---|---|---|---|---|
| SEG-1 | 56 | 27 | 99 | 52 | 13 | 140 | 130 | 115 | 34 | 27 |
| SEG-2 | 158 | 27 | 50 | 72 | 128 | 0 | 0 | 0 | 57 | 44 |
| SEG-3 | 20 | 120 | 17 | 22 | 5 | 0 | 0 | 0 | 8 | 15 |
| SEG-4 | 0 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| SEG-T | 178 | 147 | 67 | 94 | 133 | 0 | 0 | 0 | 65 | 59 |

Severity-signal vocabulary (from the brief, coded from behaviour/closer sentences): reformulation, browsing, large candidate set, uncertainty, repeated attempts, strategy switching, external workaround, abandonment, failure. Across all relevant records: browsing 234, uncertainty 177, strategy switch 166, large candidate set 149, repeated attempts 146, failure 140, external workaround 130, abandonment 115, reformulation 99, candidate inspection 86; 748 of 800 carry ≥1 signal and 510 carry ≥2.

`[INTERP]` Retrieval state is defined by the sentence that carries the signals, so 'all members show a signal' inside SEG-1/2/3 is **definitional, not a finding**. The informative contrasts: (a) SEG-4 has almost none (3 of 55, all from the closing 'cannot tell which is right' sentence); (b) memory barriers are spread evenly: explicit express-barrier statements occur in 127/341 of SEG-1, 138/284 of SEG-2, 41/120 of SEG-3 and 16/55 of SEG-4 (40.2% overall), so no segment is distinguished by memory type in this file.

## 4. Retrieval Journey Mapping

Working model, not a proven funnel: Recall → Express → Match → Recognize → Recover. Each record maps to the stages its sentences evidence.

| Stage | Records touching stage | Records with explicit breakdown evidence | What counts as breakdown evidence |
|---|---|---|---|
| **Recall** | 800 of 800 | 594 of 800 (74.2%) | memory sentence names information the user lacks (M02-M04, M06-M10, M12) |
| **Express** | 566 of 800 | 322 of 800 (40.2%) | memory cannot be turned into keyword/name/wording/description/narrowing (M02,M05,M06,M11,M12) or user contrasts with precise identifiers (C04) |
| **Match** | 120 of 800 | 0 of 800 (0.0%) | date search returned too many results (B03) or many plausible results (C08); product output is otherwise rarely described |
| **Recognize** | 120 of 800 | 0 of 800 (0.0%) | one-by-one opening, timeline/thumbnail scan, date-range comparison, similar-not-exact, cannot tell which is right (B04,B11,B13,B14,B16,C08) |
| **Recover** | 661 of 800 | 0 of 800 (0.0%) | reformulation, switching, browsing fallback, several attempts, other app, gave up, failed (B05,B07-B10,B12,B15,B17,B18) |

Most common stage paths (of 7 observed): `RECALL > EXPRESS > RECOVER` 484; `RECALL > RECOVER` 141; `RECALL > MATCH > RECOGNIZE` 54; `RECALL` 39; `RECALL > EXPRESS > MATCH > RECOGNIZE > RECOVER` 36; `RECALL > EXPRESS > MATCH > RECOGNIZE` 30; `RECALL > EXPRESS` 16.

**The five stage questions answered from the data** (Stage 2) `[OBS]`

| Stage | Question | Answer | Unknown |
|---|---|---|---|
| Recall | What does the user remember? | people 200, visual appearance 134, approximate time 126, activity 119, story 82 | Whether real memory is richer than these statements |
| Express | How does the user convert that memory into a search or action? | First-attempt inputs 0; date-based 0; reformulation 0; person then browse 0; keywords then scroll 0; explicit barrier 322 | Order and content of real queries |
| Match | Does the product appear to surface plausible candidates? | Candidates surfaced in 0 records (incl. 'too many results' 0); **0 records say the product misread the clues** | Whether the target was among the candidates |
| Recognize | Can the user identify the intended photo among candidates? | Would recognise on sight 0; cannot tell / near miss 0; heavy inspection or browsing 0 | When recognition holds and when it fails |
| Recover | What does the user do after the first attempt does not work? | Reformulate / switch / browse 0; success after several attempts 0; exits 0 | What prompted each change; whether other-app users succeeded |

### 4.1 Decomposition of successful retrieval

`[INTERP]` **Successful retrieval of a vaguely remembered photo = the user has usable partial memory (D1) AND turns it into an input (D2) AND the product brings the intended photo into the candidates (D3) AND the user recognises it (D4) AND, if the first try fails, the user can refine until it works or stop knowingly (D5) AND the photo is in the searchable library (D6).** A retrieval fails at the first node that does not hold. The nodes map onto the case's four questions plus two boundary nodes. Built in `engine/decomposition.py`.

| Node | Case question | User behaviour | Product outcome | Maps to opportunity |
|---|---|---|---|---|
| **D1 Recall** | What information do people actually remember, and what have they forgotten? | Holds partial context (people, place, story, look, roughly when) but lacks a precise identifier | n/a: this is the precondition the case starts from (photo exists, memory is incomplete) | O6 Retrieval-path memory |
| **D2 Express** | Is the user unable to express what they remember? | Turns memory into a query, filter or navigation step | The input the product receives carries the clues the user actually holds | O1 Memory expression (with O2 Approximate-time narrowing and O8 Information discovery) |
| **D3 Understand & match** | Does Google Photos fail to understand the clues they provide? | Submits clues and inspects what comes back | The intended photo appears among the candidates returned | O4 Contextual matching |
| **D4 Evaluate** | Are potentially relevant results difficult to evaluate? | Scans candidates and decides which one is the photo | The user confirms the right photo, quickly and with confidence | O3 Candidate recognition / verification |
| **D5 Refine** | Does the user struggle to refine an unsuccessful search? | Reformulates, switches strategy, browses, asks someone, or stops | A failed first attempt still ends in success, or in an informed stop | O5 Retrieval recovery |
| **D6 Available** | Is the photo in the searchable library at all? | Asks another person, switches app or device, or gives up | Retrieval is possible: the photo exists in the library the user is searching | O7 Corpus / access boundary |

**Evidence per node** `[OBS]` (records; a record can appear under several polarities). *Breakdown* = record states a difficulty here; *indirect* = consistent with failure here but not attributable; *effort* = extra work here; *intact* = capability retained or step worked; *no evidence* = the record says nothing about this node.

| Node | Breakdown (explicit) | Indirect | Effort | Intact | Attempt only | No evidence at node | Reading `[INTERP]` |
|---|---|---|---|---|---|---|---|
| **D1 Recall** | 0 | 0 | 0 | 0 | 0 | 800 of 800 | Precondition, not a failure: 594 records name missing information; no record says the user remembers too little to search. |
| **D2 Express** | 322 | 0 | 0 | 0 | 0 | 478 of 800 | Strongest explicit difficulty: 322 records state memory is hard to express. |
| **D3 Understand & match** | 0 | 0 | 0 | 0 | 0 | 800 of 800 | **0 records say the product misread the clues.** Only indirect signs (0); 0 records show candidates were surfaced. Cannot be attributed from this corpus. |
| **D4 Evaluate** | 0 | 0 | 0 | 0 | 0 | 800 of 800 | 0 cannot confirm or found a near miss; 0 did heavy inspection; 0 say they would recognise it. Recognition holds in some records and fails in others. |
| **D5 Refine** | 0 | 0 | 0 | 0 | 0 | 800 of 800 | 0 reformulate/switch/browse; 0 end unresolved or leave; only 0 state success. |
| **D6 Available** | 0 | 0 | 0 | 0 | 0 | 800 of 800 | 0 records say the photo is missing. 0 leave the product, so absence is a hypothesis only. |

**Where the decomposition points** `[OPP-HYP]`

- Users report difficulty **expressing** (D2, 322), **evaluating** (D4, 0 records with breakdown or effort evidence) and **refining** (D5, 0 records). These are where the evidence supports investigating.
- The case asks whether Google Photos **fails to understand the clues** (D3). **0 of 800 records say so.** The corpus cannot answer this question, which is not the same as the answer being no. It is the highest-value unknown and it must not be assumed away or assumed true.
- **Where the greatest opportunity lies cannot be settled from this corpus,** because failures are not attributed to nodes. The task-based tests must do that attribution (§10.3), so the ranking can come from observed failures instead of statements.

**First-failing-node rule for classifying every non-successful attempt in the task tests** `[ASSUME]` (proposed):

1. **D6 Available**: The target photo is not in the participant's searchable library.
2. **D1 Recall**: The participant cannot form any query and cannot describe any detail even when prompted neutrally.
3. **D2 Express**: The participant can later describe details that never reached a query (recall present, expression absent).
4. **D3 Understand & match**: The target never appears in any result set the participant saw.
5. **D4 Evaluate**: The target appears in results the participant saw, but was not selected or was rejected.
6. **D5 Refine**: Target found only after reformulation or a change of strategy (effortful success), or the participant stops after several tries with the underlying node recorded from the rules above.

**Product outcomes to measure per node** (candidate measures; TBD, requires Google production data or primary research. These are candidate measures, not results.)

| Node | Candidate measure |
|---|---|
| D1 Recall | Share of retrieval attempts that start with contextual clues but no precise identifier (date, name, album, exact keyword) |
| D2 Express | Clues the user can state when prompted versus clues present in the first query (research); first-query length and clue types (production) |
| D3 Understand & match | Target-in-candidate-set rate for tasks with a known target (research); selected photo appearing on the first results page (production) |
| D4 Evaluate | Candidates inspected before confirmation, time to confirm, wrong-photo confirmations, stated confidence (research); open-and-return counts (production) |
| D5 Refine | Success rate after reformulation, queries before success, abandonment after N unsuccessful queries (production); what prompted each change (research) |
| D6 Available | Share of unsuccessful retrievals where the photo is absent from the library (needs a library audit in research) |

**Major breakdowns** `[OBS]`
- **Recall → Express:** 594 records name information the user lacks (time precision 199, a name 149, a keyword 64, album 63, how it was originally found 63, exact wording 56). 322 records state the memory cannot easily be converted into a query, e.g. . [RAW] REC-0006, REC-0008, REC-0009 (all 322: `evidence_index.csv` → `node:D2:breakdown`)
- **Match:** the corpus rarely says what the product returned; only 0 records do. `[UNKNOWN]` whether matching, expression or recognition is the weak link. [RAW]  (all 0: `evidence_index.csv` → `opp:O4`)
- **Recognize:** 0 records say the user *would recognise* the photo on sight (e.g. ), while 0 say plausible results left them unable to tell which is right and 0 report a similar-but-not-exact find. Recognition holds in some records and fails in others; the file cannot say when. [RAW]  (all 0: `evidence_index.csv` → `node:D4:breakdown`)
- **Recover:** 0 records (0.0%) show reformulation, switching, browsing fallback, other-app use, giving up or failure. Only 114 state a success. [RAW]  (all 0: `evidence_index.csv` → `opp:O5`)

**Repeated behaviours:** reformulation (99), browsing (234), strategy switching (166). **Success pattern:** only 'found after several attempts' (114); success comes with effort. **Failure/exit patterns:** could not find (140), gave up and asked someone (115), moved to another app/device (86). **Uncertainty:** whether other-app/device users found the photo, and whether 'similar but not exact' users later succeeded, is not stated.

## 5. Opportunity Areas

Opportunities are *where* retrieval could improve; they are not features and not problems. Counts are non-exclusive; together the 8 cover 322 of 800. Each maps to a decomposition node (§4.1). All are `[OPP-HYP]`.

### O1 Memory expression
- **User behaviour:** User holds context but says it cannot be turned into a keyword, name, wording, description or narrowing step; contrasts this with ease when an exact date/name is known.
- **Journey stage:** Express (from Recall) · **Decomposition node:** D2
- **Frequency** `[OBS]`: 322 of 800 relevant records (40.2%); [RAW] REC-0006, REC-0008, REC-0009 (all 322: `evidence_index.csv` → `opp:O1`)
- **Severity:** Signals come from the behaviour sentences of these records (reformulation, browsing, uncertainty), not from the barrier statement itself.
- **Outcome:** 56 found-with-effort, 41 similar-but-uncertain, 53 failed, 39 abandoned, 35 other-app/device workaround; 0 unknown
- **Evidence example:** 
- **User consequence** `[INTERP]`: Extra attempts or manual scanning; some stop.  **Product consequence** `[INTERP]`: A photo that exists and is recognisable may never be reached from the first query.
- **Unknowns** `[UNKNOWN]`: Whether users hold richer memory than they express, or the memory is thin; whether failure is at input or at interpretation.

### O2 Approximate-time narrowing
- **User behaviour:** Only an approximate time is known (day/month unknown); users search by date and get too many results, or compare a date range by hand.
- **Journey stage:** Express → Match · **Decomposition node:** D2/D3
- **Frequency** `[OBS]`: 0 of 800 relevant records (0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O2`)
- **Severity:** Date search 'too many results' (0), manual date-range comparison (0).
- **Outcome:** no outcome stated; 0 unknown
- **Evidence example:** 
- **User consequence** `[INTERP]`: Long scanning of broad time windows.  **Product consequence** `[INTERP]`: Time is the clue users have, but as a search scope it may be too coarse.
- **Unknowns** `[UNKNOWN]`: Whether time is the strongest memory or simply the most available tool.

### O3 Candidate recognition / verification
- **User behaviour:** Candidates are surfaced or browsed but the user cannot confirm which is right, or finds only a similar photo.
- **Journey stage:** Recognize · **Decomposition node:** D4
- **Frequency** `[OBS]`: 0 of 800 relevant records (0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O3`)
- **Severity:** 'Cannot tell which is right' (0), similar-not-exact (0), one-by-one opening (0), very large thumbnail set (0).
- **Outcome:** no outcome stated; 0 unknown
- **Evidence example:** 
- **User consequence** `[INTERP]`: Uncertainty about having found the right photo; time spent comparing.  **Product consequence** `[INTERP]`: A successful retrieval may sit in the candidate set unconfirmed.
- **Unknowns** `[UNKNOWN]`: Whether the target was in the candidate set; what cues users use to verify.

### O4 Contextual matching (candidate-set precision)
- **User behaviour:** Users report result sets that are too large or plausible-but-undifferentiated after a query.
- **Journey stage:** Match · **Decomposition node:** D3
- **Frequency** `[OBS]`: 0 of 800 relevant records (0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O4`)
- **Severity:** Only two explicit statements describe product output; the stage is thinly observed.
- **Outcome:** no outcome stated; 0 unknown
- **Evidence example:** 
- **User consequence** `[INTERP]`: Sifting through results.  **Product consequence** `[INTERP]`: Matching quality cannot be judged from this corpus.
- **Unknowns** `[UNKNOWN]`: Almost everything: the corpus does not describe what was returned, and 0 records say the product misread the clues.

### O5 Retrieval recovery
- **User behaviour:** After the first attempt does not resolve, users reformulate, switch between terms/albums, fall back to browsing, use another app/device, ask another person, or stop.
- **Journey stage:** Recover · **Decomposition node:** D5
- **Frequency** `[OBS]`: 0 of 800 relevant records (0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O5`)
- **Severity:** Reformulation 99, strategy switch 166, browsing 234, external workaround 130, abandonment 115, failure 140.
- **Outcome:** no outcome stated; 0 unknown
- **Evidence example:** 
- **User consequence** `[INTERP]`: Repeated effort; for 341 records the search ends in failure, giving up or another app.  **Product consequence** `[INTERP]`: Successful retrieval is delayed or lost; only 114 records state a (effortful) success.
- **Unknowns** `[UNKNOWN]`: What triggers a change of strategy, what makes users continue or stop, and whether other-app users found the photo.

### O6 Retrieval-path memory (album / how it was found)
- **User behaviour:** Users know a photo exists but not its album, or how they originally reached it.
- **Journey stage:** Recall → Express · **Decomposition node:** D1
- **Frequency** `[OBS]`: 0 of 800 relevant records (0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O6`)
- **Severity:** Mostly memory statements; behaviour is generic.
- **Outcome:** no outcome stated; 0 unknown
- **Evidence example:** 
- **User consequence** `[INTERP]`: No remembered route back to the photo.  **Product consequence** `[INTERP]`: Navigation-based retrieval is unavailable when the path is forgotten.
- **Unknowns** `[UNKNOWN]`: How users normally re-find photos; whether organisation habits matter.

### O7 Corpus / access boundary (indirect evidence)
- **User behaviour:** Users ask someone else to send the photo or switch to another device/app.
- **Journey stage:** Recover (boundary of the searchable library) · **Decomposition node:** D6
- **Frequency** `[OBS]`: 0 of 800 relevant records (0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O7`)
- **Severity:** Abandonment 115; other-app/device 86.
- **Outcome:** no outcome stated; 0 unknown
- **Evidence example:** 
- **User consequence** `[INTERP]`: Leaves the product to complete the task.  **Product consequence** `[INTERP]`: Retrieval success is not captured in Photos when the photo lives elsewhere or the user gives up.
- **Unknowns** `[UNKNOWN]`: Whether the photo was in the user's Google Photos library at all (deleted, other account, other app).

### O8 Information discovery (knowing what can narrow a search)
- **User behaviour:** Users say they can recognise the photo but do not know how to narrow the results: the gap is knowing what clues or controls the search can act on, not remembering.
- **Journey stage:** Express · **Decomposition node:** D2
- **Frequency** `[OBS]`: 0 of 800 relevant records (0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O8`)
- **Severity:** One explicit sentence ('I don't know how to narrow the results'); every record with it is also an expression-barrier record (O8 is a subset of O1).
- **Outcome:** no outcome stated; 0 unknown
- **Evidence example:** 
- **User consequence** `[INTERP]`: Trial-and-error with wording, filters and browsing.  **Product consequence** `[INTERP]`: A capability the product has may go unused because users cannot tell it exists or applies.
- **Unknowns** `[UNKNOWN]`: Whether users lack knowledge of narrowing options or the options do not fit what they remember. The corpus has no statement about what users know the product can do.

`[OBS]` Express-barrier records reach the exit-path state no more often than the corpus overall: 127 of 322 O1 records (39.4%) versus 341 of 800 overall (42.6%). Within this file, O1 rests on what users say, not on a measurable link to worse outcomes. [RAW] REC-0012, REC-0022, REC-0048 (all 127: `evidence_index.csv` → `claim:K11`)

## 6. Opportunity Prioritization

Reasoning: Frequency × Severity × Outcome, then strategic relevance to the goal ('successfully retrieve a photo remembered but not precisely described'), evidence strength, researchability. No numeric scores. Labels are used only with the stated evidence. Frequency convention (analytic, not statistical): High ≥ 30% of relevant records, Medium 15–29%, Low < 15%. Potential solvability is `[UNKNOWN]` for every area and is not scored.

| Opportunity | Frequency | Severity | Outcome | Strategic relevance | Evidence strength | Researchability | Why investigate? |
|---|---|---|---|---|---|---|---|
| **O5 Retrieval recovery** | Low (0, 0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O5`) | High: 0 records with ≥2 signals; failure, abandonment, other-app use all sit here | Only area containing every terminal outcome (341 failed/abandoned/other-app) plus all 114 effortful successes | High: success is decided after the first attempt | High: explicit behaviour statements; but a symptom locus (causes lie upstream) | High: participants can recount a recent attempt | Where retrieval is won or lost; lets research trace back to Express and forward to Recognize |
| **O1 Memory expression** | High (322, 40.2%); [RAW] REC-0006, REC-0008 (all 322: `evidence_index.csv` → `opp:O1`) | Medium: signals come from behaviour sentences, not the barrier itself | Not distinguishable from base rate (39.4% vs 42.6% exit) | High: the goal is defined by imprecise memory | Medium: explicit but self-report only | High: memory-reconstruction interviews | Leading upstream hypothesis; must be tested against rivals, not assumed |
| **O3 Candidate recognition / verification** | Low (0, 0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O3`) | High: uncertainty 177, large candidate sets 149 | 120 similar-but-uncertain, 0 abandoned/failed | High: a found-but-unconfirmed photo is not a success | Medium–High: explicit and repeated, silent on whether the target was present | High: observable in task tests | Distinguishes 'not surfaced' from 'surfaced but not recognised' |
| **O2 Approximate-time narrowing** | Low (0, 0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O2`) | Medium: 'too many results' 0; manual comparison 0 | Mixed; no distinctive outcome | Medium–High | Medium: time memory explicit (0) but tool-availability confound | High | Largest single forgotten-information family (199 records) |
| **O6 Retrieval-path memory (album / how it was found)** | Low (0, 0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O6`) | Low–Medium | Mixed | Medium | Low–Medium: memory statements only | Medium | Test inside interviews; not a lead |
| **O4 Contextual matching (candidate-set precision)** | Low (0, 0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O4`) | Medium | Thin | Medium (unknown: 0 records say the product misread the clues) | Low: output rarely described | Medium | Corpus cannot size it; the task tests must (D3 attribution) |
| **O7 Corpus / access boundary (indirect evidence)** | Low (0, 0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O7`) | High per record (all terminal) but indirect | Terminal: 115 abandoned + 86 other-app | Medium: if the photo is outside the library, search cannot succeed | Low: indirect inference | Medium: needs a library audit, not just interviews | Cheap to rule in/out during interviews (was the photo in the library?) |
| **O8 Information discovery (knowing what can narrow a search)** | Low (0, 0.0%); [RAW]  (all 0: `evidence_index.csv` → `opp:O8`) | Low–Medium: one explicit statement; overlaps O1 | Mixed; no distinctive outcome | Medium: separates 'cannot express' from 'does not know what can be expressed' | Low: single sentence, subset of O1 | High: interviews and tasks can ask what participants believed they could do | Distinguishes a knowledge gap from a memory gap inside O1 (D2) |

**Selected for primary research** `[OPP-HYP]`: **O5 Retrieval recovery**, examined together with O3 and O1, and with O4 tested directly, as competing explanations of *why the first attempt does not resolve* (expression D2, matching D3, recognition D4). Rationale: it is the largest area with explicit behaviour evidence, contains every terminal outcome, is tied to the strategic goal, and is highly researchable. O1 alone would over-weight self-report that shows no outcome difference; O3 alone omits the exits; O4 cannot be ranked from this corpus but must not be ranked last by default. No solution is chosen.

Records behind the selection `[OBS]`: O5 [RAW]  (all 0: `evidence_index.csv` → `opp:O5`); O3 [RAW]  (all 0: `evidence_index.csv` → `opp:O3`); O1 [RAW] REC-0006, REC-0008 (all 322: `evidence_index.csv` → `opp:O1`); O4 [RAW]  (all 0: `evidence_index.csv` → `opp:O4`).

## 7. Target Segment Hypothesis

**TARGET SEGMENT HYPOTHESIS — TO BE VALIDATED** `[OPP-HYP]`

> We should investigate **users who attempted to retrieve a specific photo they expected to exist, lacked a precise identifier for it, and either changed strategy / made several attempts or manually inspected a candidate set (SEG-T)** because they are the largest behaviourally defined group in the corpus (404 of 800, 50.5%), every member states effortful behaviour (definitional, see assumptions), none is described as retrieving quickly, and, if the four states are snapshots of one journey `[INTERP]`, the group sits upstream of the exit-path state (341 records) where retrieval visibly fails.

| Element | Detail |
|---|---|
| Objective definition | Records whose behaviour sentence is one of B03, B04, B05, B07, B09, B11, B13, B14, B15, B16, B17, B18 (recovery-dependent 284 + candidate-inspection 120). Shared precondition: imprecise memory of a specific photo. |
| Dataset size | 404 of 800 (50.5%); 351 after removing near-duplicates |
| Stated outcomes | 114 found-with-effort, 120 similar-but-uncertain; 0 unknown |
| Evidence | Express-barrier statements 179; 'would recognise on sight' 0; 'cannot tell which is right' 0; explicit 'knows the photo exists' 0 (0.0%). [RAW] REC-0001, REC-0004, REC-0005, REC-0006, REC-0007 (all 404: `evidence_index.csv` → `seg:SEG-T`) |
| Why investigate | Frequency (largest); effort (strategy switching, browsing, large candidate sets, repeated attempts); outcome uncertainty (0 unknown, 120 uncertain); strategic relevance (retrieval is not clean for these users); researchability (recent attempts are recallable and observable) |
| Why not SEG-1 alone | Defined by outcome, so the corpus says nothing about what preceded it. Recruit SEG-1-like participants (failed/abandoned recently) as an adjacent probe. |
| Why not SEG-4 | 55 records, essentially no severity evidence. |

**Assumptions** `[ASSUME]`: (1) the states are sequential snapshots of one journey, so the boundary between SEG-2 and SEG-3 is porous, hence the union; (2) 'expected to exist' is implied for all records by the attempt, and explicit in only 0 of 404; (3) effort is definitional within SEG-T, so it says *who to study*, not *how bad it is* `[UNKNOWN]`.

## 8. Impact-Sizing Framework

`Incremental successful retrievals = E × t × f × r × l`

| Step | Symbol | Observed dataset value `[OBS]` | Assumption `[ASSUME]` | Production value |
|---|---|---|---|---|
| Eligible retrieval attempts | E | 800 relevant records (posts, not attempts); [RAW] REC-0001, REC-0002 (all 800: `evidence_index.csv` → `claim:K01`) | Unit = one retrieval attempt sequence started from imprecise memory | **TBD: requires Google production data** |
| % in target behaviour | t | 404 of 800 (50.5%); [RAW] REC-0001, REC-0004 (all 404: `evidence_index.csv` → `seg:SEG-T`) | Not transferable to production | **TBD: requires Google production data** |
| % with failure/effort | f | Effort signal 404 of 404 (100% by definition); stated non-clean outcome 120 (similar-but-uncertain); downstream exit-path 341 (of which 255 failed/abandoned); [RAW] REC-0002, REC-0003 (all 341: `evidence_index.csv` → `seg:SEG-1`) | 'Effort' needs an operational log definition (e.g. ≥2 queries or a long browse before success) | **TBD: requires Google production data** |
| % potentially recoverable | r | None; the corpus cannot estimate | Recoverable = photo is in the library and the user can recognise it; proxy to test: 'would recognise on sight' 0 of 404; [RAW]  (all 0: `evidence_index.csv` → `claim:K08`) | **TBD: primary research + production data** |
| Expected improvement | l | None | Only estimable after a solution exists; out of scope until the problem is defined | **TBD** |
| Incremental successful retrievals | — | — | — | **TBD** |

Arithmetic illustration on counts only (not a forecast): the explicit non-success set is 120 similar-but-uncertain + 255 failed/abandoned = 375 records; each 10 points of recovery on that set corresponds to ~38 records. Outcome is unknown for 0 of 404 target records, so the true base could be much larger or smaller.

## 9. Research Hypotheses

Each is a `[PROB-HYP]` to test, not a root cause. Every one has a competing explanation, separate evidence for/against/unknown, and a falsification test. Node = decomposition node (§4.1).

### H1 — Memory richer than expressed
- **Node:** D2
- **Observation** `[OBS]`: 322 records say memory is hard to turn into a query; behaviour shows reformulation (99) and switching (166). [RAW] REC-0006, REC-0008, REC-0009 (all 322: `evidence_index.csv` → `hyp:H1`)
- **Interpretation** `[INTERP]`: Many users say what they remember cannot be typed as a search, yet still try several searches.
- **Hypothesis** `[PROB-HYP]`: Users may hold more contextual detail than their first query carries.
- **Competing explanation:** Memory is genuinely thin or generic, so it is a recall problem, not an expression problem.
- **Validate / falsify:** Prompted recall adds nothing usable, or first queries already contain everything they can recall (falsified). Neutral cues surface details the first query omitted (supported).
- **Evidence for:** 322 explicit barrier statements.
- **Evidence against:** No outcome difference for O1 (39.4% vs 42.6%).
- **Unknown** `[UNKNOWN]`: What participants can recall on demand.
- **Qualitative (WHY/HOW):** Interviews: memory reconstruction and details that never reached the first query.
- **Quantitative (WHERE/HOW MUCH):** Survey: how often users recall clues they did not type.

### H2 — Candidate present but not recognisable
- **Node:** D4
- **Observation** `[OBS]`: 'Cannot tell which is right' 0; similar-not-exact 0; one-by-one opening 0. [RAW]  (all 0: `evidence_index.csv` → `hyp:H2`)
- **Interpretation** `[INTERP]`: Users report both plausible candidates they cannot separate and being able to recognise the photo on sight.
- **Hypothesis** `[PROB-HYP]`: Users see the right photo among candidates but lack cues to confirm it (near-duplicates, burst shots, generic scenes).
- **Competing explanation:** The target was never among the candidates (matching gap), or users hold a wrong mental image of the photo.
- **Validate / falsify:** Log whether the target appeared in inspected sets. Falsified if it is mostly absent, or if participants confirm it instantly once shown.
- **Evidence for:** Explicit uncertainty statements.
- **Evidence against:** 0 records claim they would recognise it on sight.
- **Unknown** `[UNKNOWN]`: Whether the target was present.
- **Qualitative (WHY/HOW):** Task tests and interviews: how the target was recognised or missed.
- **Quantitative (WHERE/HOW MUCH):** Survey: how often users report seeing but doubting the right photo.

### H3 — Time is used as a scope because it is available, not because it is the best memory
- **Node:** D2/D3
- **Observation** `[OBS]`: Approximate time in 0 records; date search 'too many results' 0; date-range comparison 0. [RAW]  (all 0: `evidence_index.csv` → `hyp:H3`)
- **Interpretation** `[INTERP]`: Most users lacking the exact date still lean on date narrowing, and it often returns broad sets.
- **Hypothesis** `[PROB-HYP]`: Users default to date narrowing because it is the tool they know, producing broad windows.
- **Competing explanation:** Time is the most reliable clue and windows are large because libraries are large.
- **Validate / falsify:** Ask what was remembered first and why date was chosen; give richer clues in tasks. Falsified if participants prefer date even with stronger clues and windows stay small.
- **Evidence for:** Date is the largest forgotten-information family.
- **Evidence against:** None in the corpus.
- **Unknown** `[UNKNOWN]`: Clue ranking within individuals.
- **Qualitative (WHY/HOW):** Interviews: why date was chosen; tasks that supply richer clues.
- **Quantitative (WHERE/HOW MUCH):** Survey and production: share of attempts starting from date narrowing, and window size.

### H4 — Recovery is unguided
- **Node:** D5
- **Observation** `[OBS]`: 0 records show recovery behaviours; the corpus never states why users changed strategy. [RAW]  (all 0: `evidence_index.csv` → `hyp:H4`)
- **Interpretation** `[INTERP]`: Users change strategy often, but the file never says what prompted the change.
- **Hypothesis** `[PROB-HYP]`: After a failed attempt users get no signal about why it failed, so they cycle wording, albums and scrolling.
- **Competing explanation:** Cycling is habit or a preference for browsing, independent of any signal; or recovery is efficient and only unlucky users post.
- **Validate / falsify:** Interview 'what did you try next and why'; tasks recording whether strategy changes followed results. Falsified if changes track stable personal habits regardless of results.
- **Evidence for:** Reformulation and switching signals.
- **Evidence against:** Only 114 records state a success after effort.
- **Unknown** `[UNKNOWN]`: Decision triggers.
- **Qualitative (WHY/HOW):** Interviews: what prompted each strategy change.
- **Quantitative (WHERE/HOW MUCH):** Production: queries before success and abandonment after N tries.

### H5 — Photo not in the searchable library
- **Node:** D6
- **Observation** `[OBS]`: Asked someone else 115; other device/app 86; deleted-photo restore records (3, outside the denominator). [RAW]  (all 0: `evidence_index.csv` → `hyp:H5`)
- **Interpretation** `[INTERP]`: Some users end the search by leaving the product; the file does not say whether the photo was ever findable.
- **Hypothesis** `[PROB-HYP]`: For some users the photo lives elsewhere (received via message, other account, deleted), so search cannot succeed.
- **Competing explanation:** The photo is in the library and unreachable; 'ask someone' reflects convenience.
- **Validate / falsify:** Screener + library audit: was the photo present? Falsified if it is present in most failed cases.
- **Evidence for:** Indirect only.
- **Evidence against:** No record states absence.
- **Unknown** `[UNKNOWN]`: Presence in the library.
- **Qualitative (WHY/HOW):** Screener and library audit: was the photo present.
- **Quantitative (WHERE/HOW MUCH):** Survey and production: share of failed retrievals where the photo was absent.

### H6 — Object type changes the retrieval problem
- **Node:** all
- **Observation** `[OBS]`: Objects span trip/family/event items (438) and document/medical items (282). [RAW] REC-0002, REC-0004, REC-0008 (all 282: `evidence_index.csv` → `hyp:H6`)
- **Interpretation** `[INTERP]`: Objects vary widely, but the file gives no basis for saying object type changes how people search.
- **Hypothesis** `[PROB-HYP]`: Utility images (documents, prescriptions) are searched by content/text, memorial photos by story and people.
- **Competing explanation:** Behaviour is object-independent; differences are individual.
- **Validate / falsify:** Compare tasks across object types. Falsified if strategies and success do not differ by type.
- **Evidence for:** Plausible on its face.
- **Evidence against:** Object is independent of memory and behaviour here (V=nan, p=1.0); some pairings are incoherent.
- **Unknown** `[UNKNOWN]`: Everything.
- **Qualitative (WHY/HOW):** Task comparison across object types.
- **Quantitative (WHERE/HOW MUCH):** Survey: scenario incidence by object type.

### H7 — The corpus overstates difficulty (selection effect)
- **Node:** all
- **Observation** `[OBS]`: All relevant records are complaint/help posts; no uneventful retrievals exist. [RAW] REC-0001, REC-0002, REC-0003 (all 800: `evidence_index.csv` → `hyp:H7`)
- **Interpretation** `[INTERP]`: The file contains only posts about difficulty, so it cannot show how common difficulty is.
- **Hypothesis** `[PROB-HYP]`: Most real retrievals from imprecise memory succeed quickly; the corpus captures only the tail.
- **Competing explanation:** Difficulty is common and under-reported.
- **Validate / falsify:** Survey with neutral recall of recent attempts. Supported if most succeed in one attempt; weakened if effortful or unsuccessful retrieval is common.
- **Evidence for:** Sampling logic.
- **Evidence against:** None.
- **Unknown** `[UNKNOWN]`: Prevalence.
- **Qualitative (WHY/HOW):** Interviews: what participants recall as ordinary retrievals.
- **Quantitative (WHERE/HOW MUCH):** Survey: share of recent attempts that succeeded on the first try.

`[VALIDATED]` None of H1–H7 is validated. Verdicts stay *untested* until primary research supplies evidence.

## 10. Primary Research Plan

**PROPOSED RESEARCH PLAN — NOT RESEARCH FINDINGS.** Sequence: interviews → task-based tests → survey. Nothing here tests a solution. Dataset findings (§1–§8) and future primary findings are kept in separate columns of every synthesis table (§11).

**Rule:** quantitative evidence answers WHERE and HOW MUCH; qualitative research answers WHY and HOW. Each method below is used only for what it can answer.

| Method | Answers | Cannot answer | Used for |
|---|---|---|---|
| Corpus (today) | WHERE, directionally | WHY, HOW, HOW MUCH | Choosing what to investigate; no more |
| Interviews | WHY, HOW | HOW MUCH | H1–H5, H7; memory reconstruction; what prompted each change |
| Task-based tests | HOW (observed), WHERE (first failing node, small n) | HOW MUCH at population scale | H2–H6; D3 attribution |
| Survey | WHERE, HOW MUCH (self-reported) | WHY | Prevalence of the scenarios found qualitatively; H7 |
| Production data | HOW MUCH | WHY | Impact sizing (all TBD) |

### 10.1 Interview plan
- **Purpose:** learn how people remember and describe photos they later struggle to find, and what happens next (WHY/HOW).
- **Method:** 30-minute behavioural interviews, remote, recall-a-recent-incident format (no hypotheticals).
- **Sample:** 16 participants: 6 effortful-path (recent multi-attempt or heavy-browsing retrieval), 4 recent failure/abandonment, 2 who found a contextual-memory photo quickly (contrast, since the corpus has no success baseline), 4 heavy-library users regardless of outcome. Quotas across age, device and library size.
- **Strata trace to the corpus** `[OBS]`: effortful-path [RAW] REC-0001, REC-0004 (all 404: `evidence_index.csv` → `seg:SEG-T`); failure/abandonment [RAW] REC-0002, REC-0003 (all 341: `evidence_index.csv` → `seg:SEG-1`).

### 10.2 Interview guide (30 min)

**Warm-up (0–4 min)**
- Roughly how many photos and videos do you keep in your library, and what kinds?
- When did you last look for an older photo? What do you usually look for?
- *Interviewer note:* Library size and habits; do not mention search features.

**Recent retrieval incident (4–9)**
- Tell me about the last time you went looking for a photo you knew you had. What set it off?
- Where were you, on what device, and why did it matter then?
- *Interviewer note:* Anchor on one real event; skip if none in the last month.

**Memory reconstruction (9–14)**
- Before you started, what did you remember about the photo? What came to mind first?
- What did you not remember that you expected to?
- How sure were you that the photo existed?
- *Interviewer note:* Probe: people, place, story, look, roughly when, text. Do not list dimensions first. Note details the participant adds later that never reached a query (D2 evidence).

**Search behaviour (14–18)**
- What was the very first thing you did? Why that?
- Walk me through what you typed or tapped, in order.
- *Interviewer note:* No suggestion of methods.

**Failure / recovery (18–22)**
- What happened after that?
- At what point did you become unsure it would work? What did you do next, and why?
- What made you keep going, or stop?
- *Interviewer note:* Probe reformulation, browsing, other apps, asking people.

**Recognition (22–25)**
- How did you decide a photo was the one?
- Did you ever look at a photo and doubt it? What made you doubt?
- *Interviewer note:* Include 'similar but not exact' cases. Ask whether the right photo appeared earlier without being noticed (D3 vs D4).

**Workarounds (25–27)**
- Did you use anything outside Google Photos? Was the photo in your library?
- *Interviewer note:* Tests H5.

**Reflection (27–30)**
- Looking back, what made that difficult, or easy?
- Anything about that search you'd want us to understand?
- *Interviewer note:* Solution preferences are not asked. If time remains and the participant raises ideas, note them without probing.

Avoid: 'Would an assistant/AI help?', 'Do you wish you could describe it in your own words?', any mention of features, or questions that assume difficulty.

### 10.3 Task-based usability plan
- **Setup:** a prepared test library (comparable across participants) plus one self-chosen older photo per participant that they have not opened in over a year (non-sensitive; medical items use seeded stand-ins). ~45-minute sessions, think-aloud, 5-minute task cap `[ASSUME]`. Participants are not told how to search.
- **Sample:** 12 participants (5–8 typically surface most severe usability problems; benchmark times would need ≥ 20 `[ASSUME]`).
- **Recorded for every task (the six primary measures):** retrieval success, time to successful retrieval, attempts/reformulations, candidate photos inspected, abandonment, confidence (1–5).
- **Failure attribution:** every unsuccessful task is classified by the first failing node using the rule in §4.1, so the greatest opportunity comes from observed failures, not statements.
- **Also logged for every task (Stage 10B):** first action; first query; every reformulation; filters used; browsing behaviour (scrolling, timeline or thumbnail scanning); number of candidates inspected; time to success; confidence; abandonment; workaround use (another app, or asking someone).

| Task | User scenario | Information provided | Information withheld | Expected behaviour to observe |
|---|---|---|---|---|
| T1 Trip/place | Find the photo of the small café you visited on a trip | People with you, the general place, roughly the season | Exact place name, exact date | First action and query; place vs person vs date; whether the café ever appears in results |
| T2 Event/people | Find the photo from a family celebration | Who was there, what was happening, approximate year | Album, month, event name | Person-then-browse patterns; date-range use; comparison of near-identical candidates |
| T3 Document/screenshot | Find the screenshot of a booking or receipt | Gist of what it said, roughly when | File name, exact wording, date | Text-in-image attempts; browsing; workaround use |
| T4 Episode/story | Find the photo you took during a time you were unwell (seeded stand-in) | The story and setting | Any searchable keyword, date | Reformulation; strategy switching; what prompts a change |
| T5 Visual object | Find the photo of a specific object (e.g. a yellow toy truck) among similar items | How it looked | Its name, date | Verification among near-identical candidates; wrong-photo confirmations |

| Task | Primary measure (headline) | Also recorded | Qualitative observations |
|---|---|---|---|
| T1 Trip/place | Retrieval success within 5 min | The other five measures | Which clue the participant led with and why; whether the target appeared but was skipped (D3 vs D4) |
| T2 Event/people | Time to successful retrieval | The other five measures | Cues used to tell near-identical candidates apart; where doubt appeared |
| T3 Document/screenshot | Retrieval success within 5 min | The other five measures | Whether text or gist drove the query; reaction when a text search fails |
| T4 Episode/story | Attempts / reformulations | The other five measures | What the participant said they remembered but never typed (D2); trigger for each strategy change |
| T5 Visual object | Candidate photos inspected before confirming | The other five measures | Verbal doubt statements; how a 'similar but not exact' photo was rejected or accepted |

### 10.4 Exploratory survey plan (after interviews and tests)
- **Purpose:** estimate prevalence, frequency, importance and failure/effort of retrieval scenarios *identified qualitatively* (WHERE/HOW MUCH). Reported separately from sample findings.
- **Content:** last retrieval attempt in the past 30 days; what was remembered/unknown (checklist derived from interviews); what was tried and in what order; outcome and time/attempt bands; confidence; other-app use; importance of the photo. No solution questions.
- **Sample:** ≥ 400 for ±5 points at 95% confidence on a proportion (worst case p=0.5), ≥ 100 per compared subgroup `[ASSUME]`. Active Google Photos users with quotas on library size, device and age.
- **Limits:** self-report and recall bias; survey rates are not production rates.

### 10.5 Recruitment criteria
- Uses Google Photos as a primary photo store for ≥ 2 years; library of several thousand items `[ASSUME threshold]`.
- Has searched for an older photo in the past 30 days where they remembered the photo but not a precise identifier.
- Mix of outcomes (effortful success, failure/abandonment, quick success), object types, devices and ages.
- Exclude: Google/competitor employees, UX/research professionals, anyone in a photo-search study in the last 6 months.

### 10.6 Sample-size rationale
- **Interviews (16):** thematic saturation has been reported around 12 interviews in fairly homogeneous samples (Guest, Bunce & Johnson, 2006); this segment is heterogeneous and needs contrast groups. Stop early if the last 3 add no new themes; extend if a hypothesis stays contested.
- **Usability tests (12):** enough to see recurring strategies and severe breakdowns per task; not enough to benchmark time-to-success (≥ 20 needed `[ASSUME]`).
- **Survey (≥ 400; ≥ 100 per subgroup):** ±5 points at 95% confidence for a proportion in the worst case; sized only after qualitative work fixes the categories.

### 10.7 Success measures for the research
- ≥ 80% of interviewees give a specific recent incident with recall of what they remembered and tried.
- Each of H1–H7 ends with a documented verdict (supported / weakened / falsified) with at least one competing explanation tested.
- Task tests: complete logging of the six primary measures for every task, plus a failing-node classification for every unsuccessful attempt.
- Findings triangulated across ≥ 2 methods before any root cause is called validated.

## 11. Research Synthesis Framework

**PROPOSED RESEARCH PLAN — NOT RESEARCH FINDINGS.** No participant data exists yet; the primary-findings column is empty on purpose.

| Layer | Question | Corpus input (today) | Primary-research input (future) | Rule to advance | Guard rail |
|---|---|---|---|---|---|
| Observation | What did people say or do? | `[OBS]` coded records | Transcripts, task logs (six measures + failing node) | Verbatim or logged, tagged with record or participant ID | No interpretation here |
| Pattern | What recurs? | Counts (X of 800) | Seen in ≥ 3 participants, in both stated and observed behaviour where possible | Two sources agree | Report 'n of N participants', never percentages of users |
| Interpretation | What might it mean? | `[INTERP]` | Written as ≥ 2 rival interpretations | Rival explains the same pattern | Keep separate from observation |
| Root-cause hypothesis | Why does the first attempt not resolve? | H1–H7 as `[PROB-HYP]` | Each marked supported / weakened / falsified | Rivals tested | No cause on one method |
| Validation | Is it real and how common? | None | Survey prevalence + task-test replication + production checks | Cause explains the pattern, rivals do not | Production sizing stays TBD until Google data exists |
| Problem | Can we state it? | Provisional only | Validated causes | §12 template only when validation is met | No solution language |

## 12. Problem Definition

**PROVISIONAL PROBLEM HYPOTHESIS — REQUIRES PRIMARY RESEARCH** `[PROB-HYP]`

> Google Photos users trying to **find a specific photo they know they have** in **a large personal library**, when they remember its context but **not a precise identifier** (date, name, keyword or album), struggle to **reach it without repeated attempts, manual inspection, or leaving the product** because **[cause to be validated: candidates H1 expression gap · H2 recognition gap · H3 coarse time scoping · H4 unguided recovery · H5 photo outside the library; H3-related matching (D3) untested]**, resulting in **extra effort, uncertainty about whether the right photo was found, and in some cases giving up**.

The cause slot is intentionally empty. User, context, struggle and consequence are supported directionally by the corpus; the cause is `[UNKNOWN]` until primary research. 'Large library' is stated in only 0 records and 'knows it exists' is explicit in 0 of 404 target records, so both are `[ASSUME]`. `[VALIDATED]` No validated problem exists. The statement contains no solution, feature or technology terms.

Evidence behind each element `[OBS]`: imprecise memory [RAW] REC-0001, REC-0002 (all 594: `evidence_index.csv` → `claim:K02`); struggle [RAW]  (all 0: `evidence_index.csv` → `opp:O5`); manual inspection [RAW] REC-0001, REC-0004 (all 120: `evidence_index.csv` → `seg:SEG-3`); consequence [RAW] REC-0002, REC-0003 (all 341: `evidence_index.csv` → `seg:SEG-1`), [RAW]  (all 0: `evidence_index.csv` → `claim:K07`).

## 13. Evidence / Interpretation / Hypothesis / Unknown Matrix

Evidence cells are `[OBS]` counts with `[RAW]` record IDs; the full list behind each claim ID is in `evidence_index.csv` under `claim:Kxx`. Hypothesis cells carry their type: `[OPP-HYP]` or `[PROB-HYP]`.

| Claim | Evidence | Interpretation | Hypothesis | Unknown |
|---|---|---|---|---|
| K01 Relevant records are 800 of 840 | 37 off-topic + 3 possible; [RAW] REC-0001, REC-0002 (all 800: `evidence_index.csv` → `claim:K01`) | The file mixes on- and off-topic posts | — | Real-world share of retrieval talk |
| K02 Every relevant record describes imprecise memory | 594 of 800 name lacked information; [RAW] REC-0001, REC-0002 (all 594: `evidence_index.csv` → `claim:K02`) | The corpus is selected for contextual memory | — | How users with precise identifiers behave (no such records) |
| K03 Time precision is the most common lacked information | 199 records; [RAW]  (all 0: `evidence_index.csv` → `claim:K03`) | Users know roughly when, not exactly | `[PROB-HYP]` H3 | Whether time is the strongest clue |
| K04 Users say memory is hard to convert into a query | 322 of 800; [RAW] REC-0006, REC-0008 (all 322: `evidence_index.csv` → `claim:K04`) | A gap between remembering and expressing | `[PROB-HYP]` H1 | Whether memory is rich or thin |
| K05 Effort is widespread | 748 of 800 carry ≥1 severity signal; [RAW] REC-0001, REC-0002 (all 748: `evidence_index.csv` → `claim:K05`) | Retrieval often costs more than one step | `[PROB-HYP]` H4, H7 | Prevalence; corpus is complaint-only |
| K06 Recovery behaviours are common | 0 of 800; [RAW]  (all 0: `evidence_index.csv` → `claim:K06`) | First attempts often do not resolve | `[PROB-HYP]` H4 | Why users change strategy |
| K07 Some users cannot confirm candidates | C08 0; similar-not-exact 0; [RAW]  (all 0: `evidence_index.csv` → `claim:K07`) | Recognition can fail | `[PROB-HYP]` H2 | Whether the target was present |
| K08 Some users say they would recognise on sight | 0 of 800; [RAW]  (all 0: `evidence_index.csv` → `claim:K08`) | Recognition may be intact when access is the barrier | `[PROB-HYP]` H2 rival | What cues suffice |
| K09 Exit paths exist | 341: failed 140, gave up 115, other app 86; [RAW] REC-0002, REC-0003 (all 341: `evidence_index.csv` → `claim:K09`) | Some retrievals end outside success | `[PROB-HYP]` H5 | Whether the photo was in the library; whether other-app users succeeded |
| K10 Success is rarely stated | 114 found-with-effort; 0 found-quickly; [RAW]  (all 0: `evidence_index.csv` → `claim:K10`) | Complaint bias hides easy successes | `[PROB-HYP]` H7 | Success rate |
| K11 Express-barrier records do not fail more often | 39.4% vs 42.6%; [RAW] REC-0012, REC-0022 (all 127: `evidence_index.csv` → `claim:K11`) | No measurable link inside this file | `[PROB-HYP]` H1 (weakened as a sole explanation) | Whether a real link exists |
| K12 SEG-T is the target segment hypothesis | 404 of 800; [RAW] REC-0001, REC-0004 (all 404: `evidence_index.csv` → `claim:K12`) | Largest behavioural group with explicit effort | `[OPP-HYP]` TARGET SEGMENT HYPOTHESIS — TO BE VALIDATED | Size and outcomes in production |
| K13 Time-based narrowing is common | 0 of 800; [RAW]  (all 0: `evidence_index.csv` → `claim:K13`) | Users lean on date when it is all they have | `[PROB-HYP]` H3 | Clue ranking within individuals |
| K14 Most outcomes are unstated | 0 of 800; [RAW]  (all 0: `evidence_index.csv` → `claim:K14`) | Failure and success rates cannot be computed | — | Real outcome distribution |
| K15 No record says the product misread the clues | 0 of 800; node D3 breakdown = 0 | The 'does Google Photos understand?' question is unanswerable here, not answered no | `[PROB-HYP]` D3 gap untested | Whether the target was ever among the results |
| K16 Retrieval recovery is the opportunity to research | O5 0 of 800; [RAW]  (all 0: `evidence_index.csv` → `opp:O5`) | Where success is decided | `[OPP-HYP]` investigate O5 with O3, O1 and O4 as rivals | Root cause |
| K17 Memory, behaviour, object and source are independent | Cramér's V ≤ nan; p ≥ 0.647 (appendix) | Template composition, not user behaviour | — | Any true structure; source is not a usable axis |
| K18 No solution has been chosen; no problem is validated | — | The problem is not yet defined | `[VALIDATED]` none | All of §9–§12 pending primary research |
