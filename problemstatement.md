# Problem Statement — Google Photos Retrieval

> **PROVISIONAL PROBLEM HYPOTHESIS — REQUIRES PRIMARY RESEARCH**
> Built from a **real** corpus (`Book19.xlsx` / `Book19.csv`). Counts below are "X of Y records in that file". No interviews, usability tests or surveys have been run. The cause is deliberately left open, and no solution is proposed.

Label key: `[RAW]` verbatim record · `[OBS]` observed behaviour in the corpus (a count) · `[INTERP]` interpretation · `[OPP-HYP]` opportunity hypothesis · `[PROB-HYP]` problem hypothesis · `[VALIDATED]` validated problem (**none yet**) · `[ASSUME]` assumption · `[UNKNOWN]` not knowable from this data.

---

## 1. Product outcome (why we care)

Increase the percentage of users who **successfully retrieve a photo they remember but cannot precisely describe** when they start searching.

This is the outcome the problem must connect to. It is not the problem itself.

## 2. Provisional problem statement

> **Google Photos users** trying to **find a specific photo they believe they have**, in **a large personal library**, when they **remember its context but not a precise identifier** (date, name, keyword or album), struggle to **reach it without repeated attempts, manual inspection of candidates, or leaving the product**, because **[cause to be validated — see §5]**, resulting in **extra effort, uncertainty about whether the right photo was found, and in some cases giving up**.

The bracketed cause is empty on purpose. The statement uses none of the following: AI, semantic search, chatbot, assistant, metadata, embeddings, feature names, implementation details. The evidence does not establish any of them as necessary.

## 3. How each element is supported today

| Element | Wording in the statement | Supporting evidence `[OBS]` | Strength |
|---|---|---|---|
| **User** | Users retrieving a specific photo they believe exists | 800 of 800 relevant records describe an attempt to find a particular photo. "Knows it exists" is explicit in 0 of the 404 target records (0.0%) and implied by the attempt in the rest `[ASSUME]` | Medium |
| **Context** | Large personal library | "Thousands of images" is stated in only 0 of 800 records `[ASSUME]` for the rest | Low |
| **Imprecise memory** | Context remembered, no precise identifier | 594 of 800 name specific missing information (time precision 199, a name 149, a keyword 64, album 63, how it was originally found 63, exact wording 56); 206 more describe memory the user cannot readily use as an identifier `[INTERP]` | Medium (corpus is selected for this; no precise-identifier retrievals exist to compare) |
| **Struggle** | Repeated attempts, manual inspection, leaving the product | Recovery behaviours in 284 of 800; candidate inspection or uncertain candidate sets in 120. Across the corpus: strategy switching 166, browsing 234, reformulation 99, other app/device 130 | Medium |
| **Consequence** | Effort, uncertainty, giving up | Failed 140, gave up and asked someone 115, other app/device 86, similar-but-not-exact 120, found only after several attempts 114 | Low–Medium (only 800 of 800 records state any outcome) |
| **Cause** | *[open]* | Not established | None |

## 4. Target segment the statement points at

**TARGET SEGMENT HYPOTHESIS — TO BE VALIDATED.** Effortful-path retrievers: users who attempted to retrieve a specific photo they expected to exist, lacked a precise identifier, and either changed strategy or made several attempts (284 records), or manually inspected a candidate set (120 records). Together this is 404 of 800 records (50.5%).

Effort is definitional within this group, so it says who to study, not how bad the problem is `[UNKNOWN]`.

## 4A. Where the problem sits: decomposition of successful retrieval

Successful retrieval needs six things to hold in order: usable partial memory (D1), expression (D2), the product bringing the photo into the candidates (D3), the user recognising it (D4), refinement when the first try fails (D5), and the photo being in the library (D6). A retrieval fails at the first node that does not hold. Four nodes are the case's own questions.

| Node | Case question | What the corpus says `[OBS]` |
|---|---|---|
| D2 Express | Is the user context-to-query translation what they remember? | 322 of 800 records state difficulty; strongest explicit signal |
| D3 Understand & match | Does Google Photos fail to understand the clues? | **0 of 800 records say so.** 0 show indirect signs only (too many results, could not find, near miss). Unanswerable here, not answered no |
| D4 Evaluate | Are relevant results difficult to evaluate? | 0 with breakdown or effort evidence; 0 also say they would recognise the photo on sight |
| D5 Refine | Does the user struggle to refine? | 0 with effort or unresolved endings; only 114 state a success |
| D1 Remember, D6 Available | Boundary conditions | D1 is the precondition (594 name missing information); D6 has 0 explicit statements and 0 indirect signs |

`[OPP-HYP]` The evidence supports investigating D2, D4 and D5. It cannot rank them, and it cannot say whether D3 is a problem at all. The research therefore classifies every unsuccessful task by its first failing node, so the ranking comes from observed failures.

## 5. Candidate causes (competing, to be tested — none is a root cause)

| # | Candidate cause `[PROB-HYP]` | Competing explanation | What would falsify it |
|---|---|---|---|
| H1 | Users remember more than their first query carries (expression gap) | Memory is genuinely thin, so it is a remember problem | Prompted remember adds nothing usable; first queries already contain all they can remember |
| H2 | The right photo is among the candidates but users cannot confirm it (recognition gap) | The target was never surfaced (matching gap) | Target mostly absent from inspected sets; or participants confirm it instantly once shown |
| H3 | Users narrow by date because it is available, not because it is their best clue (coarse time scoping) | Time really is the most reliable clue and libraries are simply large | Participants prefer date even when stronger clues are supplied and windows stay small |
| H4 | After a failed attempt, users get no signal about why, so they cycle wording, albums and scrolling (unguided recovery) | Strategy changes follow personal habit, or recovery is efficient and only unlucky users post | Strategy changes track stable habits regardless of results |
| H5 | For some users the photo is not in the searchable library (deleted, other account, received elsewhere) | The photo is present and unreachable; "asked someone" reflects convenience | In most failed cases the photo is present in the library |

Node D3 (the product failing to understand the clues) has no row above because the corpus gives no explicit evidence for or against it. It is tested directly by the failing-node classification in the task tests, not assumed either way.

Also to test: H6 (object type changes the problem) and H7 (the corpus overstates difficulty because it contains only complaint posts). See `output/discovery_report.md` §9.

One data finding constrains H1: records with an explicit expression barrier reach the exit-path state at 39.4% versus 42.6% overall, so within this file the barrier is not linked to worse outcomes `[OBS]`.

## 6. Scope

| In scope | Out of scope for this problem |
|---|---|
| Finding an existing photo, video or screenshot from an imprecise memory | Restoring deleted photos (3 records; restore flow, no search-behaviour evidence) |
| Recovery after a first attempt does not resolve | Sharing, storage, backup, editing, printing, battery, settings (37 off-topic records) |
| Recognising the intended photo among candidates | Photo capture and organisation habits, except as they affect retrieval |

## 7. What would count as success (definitions to be fixed with production data)

- **Outcome metric:** share of retrieval attempts that start from imprecise memory and end in a confirmed successful retrieval. Baseline: **TBD, requires Google production data.**
- **Operational terms still to define:** what counts as "starting from imprecise memory" in logs; what counts as "confirmed"; what counts as an effortful attempt (for example ≥2 queries, or a long browse before success).
- **Guardrails to watch, not optimise blindly:** time to retrieval, abandonment, retrievals that end in another app.

## 8. Gate from provisional to validated

The statement becomes a validated problem definition only when all of these hold:

1. Interviews (planned n = 16) give a specific recent incident for at least 80% of participants, and every hypothesis H1–H7 has a documented verdict.
2. Task-based tests (planned n = 12) confirm the same behaviours by observation, not only by report, and every unsuccessful task is classified by its first failing node (D1–D6).
3. At least one cause explains the pattern while its rival does not, supported by two or more methods.
4. A survey (≥ 400) estimates prevalence of the scenario. Production sizing stays TBD until Google data is available.
5. The cause slot in §2 is filled with evidence-backed wording containing no solution language.

## 9. Assumptions and unknowns

- `[ASSUME]` The four retrieval states in the corpus are snapshots of one journey, so recovery-dependent and candidate-inspection behaviour are pooled.
- `[ASSUME]` "Knows the photo exists" holds for every record because the user is searching for it.
- `[UNKNOWN]` How common any of this is, how users with precise identifiers behave, whether "other app/device" users eventually found the photo, and whether the target was ever in the candidate set.

## 10. What comes next, and what does not

Next: run the primary research in `implementationplan.md` Phase 3, then revisit this file.

Not yet: how-might-we questions, ideation, solutions, MVP, testing. Those follow only after §8 is satisfied.
