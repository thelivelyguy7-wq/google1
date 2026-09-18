# Problem Statement: AI-Powered Discovery Engine

> Product Management case study, Google Photos (Core Experience)
> Related documents: [implementationplan.md](implementationplan.md) · [README.md](README.md)

---

## 1. Project Context

Over years of use, Google Photos users build up thousands of photos, videos, screenshots, documents, receipts, notes and other visual memories.

Conventional search works when users know exactly what they want. Retrieval gets much harder when **memory is incomplete**. Users say things like:

- "That small café we went to during our Goa trip."
- "The picture of the medicine I took when I was sick last year."
- "That photo from my friend's wedding where we were standing outside."
- "The screenshot of the product I wanted to buy."
- "The document I photographed a few years ago."
- "That picture from the trip where we stayed near the beach."
- "The photo of the bill I took sometime last summer."
- "The screenshot where I had the information about that course."
- "The picture of the food we ordered at that restaurant."
- "That photo where I was wearing the blue shirt."

The user knows the visual memory exists. They may not remember the exact date, exact location, filename, album, exact words in the image, the person's name, the exact event, the right search terms, or any metadata attached to the photo.

### Strategic objective

> **Increase the percentage of users who successfully retrieve a photo they remember but cannot precisely describe when they start searching.**

This is **not** a generic search-improvement project. It focuses on the retrieval problem that occurs when **user memory is incomplete** while **the retrieval system requires, or works better with, precise search signals**. The Discovery Engine investigates this problem at scale *before* any product solution is proposed.

---

## 2. Core Discovery Question

> **How do people retrieve old visual memories when they remember the experience, context, content, or appearance of a photo but cannot precisely describe the photo?**

The engine investigates the gap between **how people remember a photo** and **how a photo retrieval system expects users to describe or locate it**.

This gap must not be assumed to be the root cause. The engine must establish whether the gap exists, what forms it takes, who experiences it, how often it happens, and where in the retrieval journey things break down.

---

## 3. Product Role of the Discovery Engine

The Discovery Engine is a **research and discovery instrument**, not the final product solution. It supports this reasoning chain:

```
BUSINESS OUTCOME → PRODUCT OUTCOMES → SYSTEM / RETRIEVAL JOURNEY → USER EVIDENCE
→ BEHAVIORAL PATTERNS → RETRIEVAL BARRIERS → OPPORTUNITY AREAS → TARGET SEGMENTS
→ RESEARCH HYPOTHESES → PRIMARY RESEARCH → PROBLEM DEFINITION
```

It must **not** jump from user comments to a feature proposal, chatbot, conversational search, semantic search, AI assistant, new filter, interface redesign, or product recommendation. Solutions come later in the discovery process. The engine's job is to discover evidence and give it structure.

---

## 4. Framework (NextLeap PM)

```
BUSINESS OUTCOME → PRODUCT OUTCOME → IMPACT / BEHAVIORAL DECOMPOSITION → DISCOVERY
→ SEGMENTATION → JTBD → CUSTOMER JOURNEY → USER RESEARCH → PROBLEM DEFINITION
→ HYPOTHESIS → IDEATION → SOLUTION → MVP → TEST → METRICS → RISKS
```

The engine works mainly in **Discovery**. It supports quantitative discovery, qualitative discovery, behavioural analysis, segmentation, retrieval-journey mapping, opportunity identification and comparison, and hypothesis generation.

It must keep these categories distinct and never merge them: **Observation · Insight · Interpretation · Hypothesis · Opportunity · Solution**.

---

## 5. Business Outcome

> **Increase successful retrieval of vaguely remembered photos.**

A *successful retrieval* means a user who starts with a remembered but imprecisely described visual memory ends up identifying the intended photo.

The objective must not be redefined as improving generic search, raising search usage or the number of searches, increasing AI usage, engagement or time spent, or driving feature adoption. Some of these may later become supporting metrics. None of them is the business outcome.

---

## 6. Product-Outcome Decomposition (working model)

```
REMEMBER → EXPRESS → UNDERSTAND → RETRIEVE → EVALUATE → REFINE → CONFIRM
```

This is a working model, and the engine must be able to discover that the real journey differs from it.

| Stage | What to investigate |
|---|---|
| **Remember** | What the user remembers (person, place, event, occasion, object, activity, approximate period, visual appearance, text, emotion, relationship, trip, food, clothing, document type, health, purchase, social or work context) and what they don't (exact date, location, name, wording, album, filename, person identity, event name, object name). |
| **Express** | How memory becomes a retrieval attempt: exact terms, natural-language phrases, keywords, approximate dates, locations, people, categories, objects, visual traits, combinations of clues, repeated attempts, alternative wording. Do users describe naturally, guess system-friendly keywords, try several queries, search by metadata, browse, filter, or switch strategy? |
| **Understand** | Whether the system appears to understand the clues: semantic or vocabulary mismatch, ambiguous intent, missing context, several possible interpretations, failure to connect clues or the relationships between them. *Not every failed search is an AI-understanding problem.* |
| **Retrieve** | Whether relevant content surfaces: no results, partially relevant, ranked too low, too many, duplicates, incorrect, missing candidates, inability to connect several weak clues. |
| **Evaluate** | Whether users can pick the right photo from the candidates: results inspected, visual similarity, available context, recognition difficulty, scrolling burden, ambiguity, confidence. *A photo can be retrieved and still be hard to identify.* |
| **Refine** | What happens after failure: modify, add or remove context, try synonyms, change strategy, browse dates, locations, albums or people, scroll manually, abandon, return later. Do users know what to try next? |
| **Confirm** | Found · not found · partially found · uncertain · abandoned. |

---

## 7. Primary Discovery Questions

**Memory**
1. What kinds of old photos do users struggle to retrieve?
2. What kinds of videos do users struggle to retrieve?
3. What kinds of screenshots do users struggle to retrieve?
4. What kinds of documents do users struggle to retrieve?
5. What kinds of memories are easiest to describe?
6. What kinds of memories are hardest to describe?
7. What contextual information survives in memory?
8. What metadata is commonly forgotten?
9. What visual details are remembered?
10. What non-visual contextual details are remembered?

**Search expression**
11. How do users formulate searches when memory is incomplete?
12. Do users use natural language?
13. Do users use keywords?
14. Do users guess metadata?
15–20. Do users search by location, date, person, object, event, or visual characteristics?
21. Do users combine multiple weak clues?
22. Do users repeatedly reformulate their queries?

**Forgotten information**
23. What information do users commonly forget?
24. Does the forgotten information prevent retrieval?
25. Which missing metadata fields cause the greatest retrieval difficulty?
26. Do users remember approximate information rather than exact information?
27. Do users remember relationships rather than attributes?
28. Do users remember context rather than metadata?

**Failure**
29. Where does retrieval fail?
30. Does the user fail to express the memory?
31. Does the system fail to interpret the clues?
32. Does the system fail to retrieve relevant candidates?
33. Are relevant candidates present but difficult to recognise?
34. Does the user fail to refine an unsuccessful search?
35. Does the user abandon retrieval?

**Workarounds**
36. What do users do when search fails?
37–41. Do they browse manually, use dates, use locations, inspect albums, or try different keywords?
42–44. Do they search externally, ask another person, or use another application?
45. Do they simply give up?

---

## 8. Evidence Sources and Ingestion

**Sources:** Google Play and Apple App Store reviews, Reddit, Google Photos Community and Help/Support discussions, public forums, social media, YouTube comments, public blog comments, product-review discussions, photography communities, Android/iOS communities, and other public user-generated discussions.

Use only publicly accessible information that is appropriate to analyse. Do not require private data, identify individuals, or expose personal information.

**Formats:** CSV, XLSX, JSON, JSONL, text, scraped structured records, API output (where legally and technically appropriate), and manually supplied datasets.

**Record fields:** source, source URL/ID, timestamp, author identifier (only if necessary and non-sensitive), title, text, thread context, parent comment, replies, engagement, platform, retrieval date.

**Raw evidence must be stored separately from AI interpretation.**

---

## 9. Evidence Preservation and Pipeline

For each extracted signal, store: source, URL, platform, date, original text or excerpt, evidence ID, evidence type, classification, confidence, behavioural signal, interpretation, and associated opportunity area.

The pipeline:

```
COLLECT → CLEAN → DEDUPLICATE → CHUNK → RETRIEVE RELEVANT CONVERSATIONS
→ CLASSIFY RETRIEVAL CONTEXT → EXTRACT MEMORY SIGNALS → EXTRACT FORGOTTEN INFORMATION
→ IDENTIFY SEARCH FORMULATION → IDENTIFY RETRIEVAL BARRIER → IDENTIFY USER BEHAVIOR
→ IDENTIFY WORKAROUND → QUANTIFY SIGNALS → COMPARE THEMES → SEGMENT USERS / SCENARIOS
→ MAP TO RETRIEVAL JOURNEY → IDENTIFY OPPORTUNITY AREAS → PRIORITIZE / COMPARE
→ GENERATE RESEARCH HYPOTHESES
```

---

## 10. Classification Schemes (extensible)

All label sets can be extended. When evidence shows a recurring pattern, new labels may be created; nothing is forced into an existing category.

- **Behaviour:** retrieval_attempt, successful / failed / abandoned retrieval, repeated_search, query_refinement, manual_browsing, date / location / person / album-based search, keyword_search, natural_language_search, visual_description, contextual_description, metadata_guessing, external_workaround.
- **Memory signals:** remembered person, place, event, occasion, object, activity, trip, time approximation, visual appearance, text, relationship, context, emotion, sequence, social context. Also capture specificity, stated confidence, number and type of clues, and whether each is exact or approximate.
- **Forgotten information:** exact date, exact location, person name, event name, filename, album, exact keyword, exact text, exact object name, metadata. *Forgetting something does not automatically cause failure; whether it creates a barrier must be established from the evidence.*
- **Retrieval scenarios:** travel, food/restaurant, family, friend, event, wedding, work, document, receipt, medical/health, screenshot, purchase-related, location, object, social, school/college, personal, other.
- **Search formulation:** original query, type, length, specificity, the clues it contains (contextual, metadata, visual, temporal, geographic, person, object, event), reformulations, number of attempts, reason for reformulating. Critically: is the query built around *what happened, where, who, what they saw, why the photo was taken, approximately when, what the image contained, or what it was needed for*?

---

## 11. Retrieval Failure Taxonomy

| Code | Failure | Definition |
|---|---|---|
| A | Memory expression | The user remembers something but struggles to turn it into searchable information. |
| B | System understanding | The user gives a meaningful clue, but the system appears to misinterpret it. |
| C | Retrieval | The relevant photo does not appear, or is not surfaced prominently enough. |
| D | Result evaluation | The photo may be present, but the user struggles to recognise or distinguish it. |
| E | Refinement | The first attempt fails and the user doesn't know how to continue effectively. |
| F | Data / index limitation | The needed information is unavailable, missing, inaccessible or poorly represented. |
| G | Other | A recurring failure mode that fits none of the above. |

**Root-cause discipline:** keep *symptom* ("I couldn't find the photo"), *behaviour* (searched several times), *barrier* (couldn't form a more useful query) and *root cause* (remembered the context but lacked the metadata or vocabulary the retrieval path needs) separate. The root cause must come from evidence, not assumption.

---

## 12. Analysis Requirements

**Qualitative:** what users are trying to accomplish, remember, forget, try, find frustrating and expect; what they do after failure and which workarounds they develop; what information matters to users versus to the system; and where those two don't match. **Behavioural evidence takes priority over emotional language.**

**Quantitative:** counts and percentages for retrieval-related conversations, incomplete memory, date and location uncertainty, contextual descriptions, failed and repeated searches, manual browsing, abandonment, and breakdowns by scenario, failure category, workaround and opportunity area.

**Every percentage must state its numerator, denominator, dataset scope, source population and time period.** Small samples are reported as counts and labelled directional. Denominators are never invented.

**Synthesis principle:** quantitative data shows where to look; qualitative data helps explain why. Combined findings are labelled Observation, Insight or Hypothesis according to the strength of evidence.

---

## 13. Segmentation and Target Segment

Don't assume all users share the same problem. Segment mainly by **behaviour** (heavy library users, frequent searchers, frequent failures, manual browsers, repeat attempts, document/travel/screenshot retrievers) and by **technology or usage** (mobile, desktop, cross-device, retrieval mechanism). Use demographic or geographic dimensions only when they are relevant, ethical and supported by evidence.

Compare segments on: frequency, severity, clarity of the unmet need, behavioural evidence, opportunity size, relevance to the strategic metric, evidence strength, distinctiveness, feasibility of primary research, and potential for product intervention. **Don't choose a segment just because it has the most mentions**; show the selection logic.

---

## 14. JTBD and Customer Journey

**JTBD** (NextLeap structure, derived only from evidence):

> **WHEN I** … **BUT** … **PLEASE HELP ME** … **SO I** …

**Journey map** from actual behaviour: remember, identify clues, start retrieval, formulate search, system returns results, evaluate, decide whether to refine, change strategy, find or abandon. For each step capture: user goal, action, remembered and missing information, system response, expectation, difficulty, workaround, failure point, and emotional signal.

---

## 15. Opportunities, Evidence Strength and Contradictions

**Opportunity areas are problem spaces, not features.**

| ✗ Not an opportunity | ✓ Opportunity area |
|---|---|
| "Build an AI chatbot." "Add conversational search." "Add a memory assistant." | "Help users retrieve memories using contextual clues they remember but cannot translate into precise search metadata." (still to be validated against evidence) |

Structure: **User behaviour → Retrieval barrier → Unmet need → Opportunity area.**

**Opportunity comparison fields:** name, supporting evidence count, unique source count, source diversity, affected scenarios and segments, severity, workaround and abandonment signals, strategic relevance, evidence confidence, unresolved questions. If a scoring framework is used, expose its dimensions and assumptions. No arbitrary AI score.

**Evidence strength:** HIGH / MEDIUM / LOW / DIRECTIONAL, based on the number of observations, source diversity, consistency, behavioural specificity, contradictory evidence and quality of context. A frequently repeated opinion is not automatically strong behavioural evidence.

**Contradictory evidence:** for each major insight, actively ask: what contradicts this? Do some users experience the opposite? Is it limited to one scenario or platform? Is another factor the cause? Could the behaviour have another explanation? The engine must not optimise for confirming the PM's initial hypothesis.

---

## 16. Research Hypotheses and Primary Research Handoff

**Hypothesis format:**

> **WE BELIEVE** … **BECAUSE** … **WE EXPECT TO OBSERVE** … **WE NEED TO VALIDATE** …

**Research brief for 5–6 interviews** must include: target segment, retrieval scenario, top opportunity areas, key hypotheses, supporting and contradictory evidence, unknowns, interview objectives, behavioural interview questions, behaviours to observe, signals to validate, and signals that would falsify each hypothesis. **No fabricated interview results.**

**Interview questions focus on past behaviour.**

| ✓ Preferred | ✗ Avoid (leading) |
|---|---|
| "Tell me about the last time you tried to find an old photo that you remembered but couldn't immediately locate." | "Would you use an AI assistant for this?" |
| "What did you remember about the photo?" | "Would conversational search solve this problem?" |
| "What did you search first?" / "What did you try when that didn't work?" | "Would you like Google Photos to understand your memories?" |
| "How did you know whether a result was the photo you wanted?" | |

---

## 17. System Requirements

**Output schema per conversation** (structured, traceable, auditable): source, source_url, platform, date, retrieval_scenario, retrieval_object, retrieval_attempt, success_status, remembered_information[], forgotten_information[], search_formulation, search_strategy[], query_refinement[], failure_stage, failure_reason, user_behavior[], workarounds[], user_goal, jtbd_signal, segment_signal, opportunity_area, evidence_strength, evidence_excerpt, research_hypothesis, confidence.

**Dashboard:** overview (records, retrieval-related, success / failure / abandonment signals); retrieval scenarios; memory signals; forgotten information; failure points; workarounds; opportunity areas with evidence volume, source diversity, affected scenarios and segments, severity, confidence and unresolved questions.

**Exploration interface.** The PM can ask, with supporting evidence in every answer:
- "Show me conversations where users remembered the place but not the date."
- "Find examples of people trying to retrieve a photo using an event description."
- "What information do users remember most frequently / commonly forget?"
- "Show me retrieval attempts that ended in abandonment."
- "Compare travel-photo retrieval problems with document retrieval problems."
- "What workarounds do users use after search failure?"
- "Which retrieval failure points appear most frequently?"
- "Which opportunity areas have evidence across multiple sources?"
- "Show evidence that contradicts the leading opportunity."
- "Generate interview hypotheses for this opportunity."

**RAG / vector search** (if used): prioritise semantic relevance, behavioural relevance, retrieval scenario, source diversity, then temporal relevance. Avoid returning near-identical comments from one source or thread. Combine semantic retrieval with structured filters (source, platform, date, scenario, failure stage, behaviour, segment, evidence strength).

**AI analysis layer**, as distinct modules rather than one summarisation step:
1. Relevance Classifier
2. Retrieval Scenario Classifier
3. Memory Signal Extractor
4. Forgotten Information Extractor
5. Search Behavior Analyzer
6. Failure-Point Classifier
7. Workaround Extractor
8. Segment Analyzer
9. Theme / Pattern Detector
10. Opportunity Synthesizer
11. Evidence Validator
12. Research Hypothesis Generator

---

## 18. Guardrails

| Guardrail | Requirement |
|---|---|
| **Sentiment is not the method** | Negative sentiment ≠ product opportunity. A frustrated user who found the photo may matter less than a neutral account of repeated failure. |
| **Don't overfit to one source** | Report source distribution and source-specific vs cross-source patterns. Independent cross-source repetition is stronger evidence. |
| **No fabrication** | Never invent comments, survey responses, interview findings, percentages, source counts, URLs or behaviour, or present an AI inference as a user statement. **Synthetic data must always be labelled SYNTHETIC / SIMULATED.** |
| **Privacy and ethics** | Public, appropriate data only. No identifying individuals, unnecessary sensitive inference, private conversations, unnecessary PII, or personal profiles. This is product discovery, not surveillance. |
| **Human in the loop** | The PM can inspect raw evidence, extracted signals, classifications, confidence, sources and synthesis, and can challenge any AI conclusion. |
| **Auditability** | Every insight answers "where did this come from?" by tracing opportunity → insight → behavioural pattern → source evidence. |

---

## 19. Final Discovery Output

The discovery report contains:
1. Business metric
2. Product-outcome decomposition
3. Discovery scope (sources, dataset size, period, method)
4. Retrieval scenarios
5. Memory patterns
6. Forgotten information
7. Search formulation
8. Failure patterns
9. Workarounds
10. Segments
11. Opportunity areas
12. Opportunity comparison
13. Leading opportunity (with evidence and caveats)
14. Research hypotheses for 5–6 interviews

---

## 20. Success Criteria

The engine succeeds if a PM can answer these questions:
1. What are users trying to retrieve?
2. What do they remember?
3. What do they forget?
4. How do they attempt retrieval?
5. Where does retrieval fail?
6. Why does it fail?
7. What workarounds do they use?
8. Which segments and scenarios are most affected?
9. Which opportunities have the strongest evidence?
10. What evidence supports each opportunity?
11. What evidence challenges each opportunity?
12. What should primary research validate?

It is **not** successful merely because it produces summaries, classifies sentiment, renders attractive dashboards, uses an LLM or RAG, or generates many themes.

> **Its value: turning large-scale user conversations into traceable, comparable, behavioural product-discovery insights.**

---

## 21. Guiding Principle and End State

Don't ask *"What AI feature should we build?"* Ask, in order:
1. **What is actually happening** when users try to retrieve a visual memory they cannot precisely describe?
2. **What behaviour, barrier or system breakdown** explains the failure?
3. **Which opportunity** has the strongest and most relevant evidence?
4. **What do we still need to learn** from users?

Only after primary research does the PM move to Problem Definition, then Hypothesis, Ideation, Solution and an AI-native MVP.

**End state:** a defensible evidence chain:

```
BUSINESS OUTCOME → SUCCESSFUL RETRIEVAL → PRODUCT OUTCOMES → RETRIEVAL BEHAVIORS
→ PUBLIC USER EVIDENCE → MEMORY PATTERNS → SEARCH BEHAVIOR → FAILURE POINTS
→ WORKAROUNDS → SEGMENTS → OPPORTUNITY AREAS → RESEARCH HYPOTHESES
→ PRIMARY RESEARCH → PROBLEM DEFINITION
```

The target is not *"Users struggle to find old photos,"* but:

> *"**These users**, in **this retrieval scenario**, remember **these contextual or visual clues**, lack **this precise information**, attempt retrieval **in these ways**, hit **this failure point**, use **these workarounds**, and therefore experience **this unmet need**."*

---

## 22. Project Scope Decisions

| Decision | Detail |
|---|---|
| **Single source of data** | The engine analyses only the raw dataset **`google_photos_discovery_annotated.xlsx`**, converted row for row to `google_photos_discovery_annotated.csv`. All earlier datasets (`dataset_flat`, `data/synthetic/`) are ignored and no longer ingested. |
| **Coverage** | 840 conversations: **120 each** from Google Play reviews, App Store reviews, Reddit, Google Photos Community/support, social media, YouTube comments, and forums/other public discussions. |
| **What the engine analyses** | `source`, `id` and `text`. The analyzers derive their own labels (relevance, scenario, memory, forgotten information, search behaviour, failure stage, workarounds) from the text, with verbatim quotes. |
| **Role of the annotations** | The dataset's five annotation columns are kept with the raw evidence but are **not analyzer input**, so they stay independent. They are used to cross-check the engine's output (§22.3) and, once mapped to the engine's labels, as candidate gold labels for evaluation. |
| **Beyond summaries and sentiment** | The workflow must identify, compare and trace retrieval problems and opportunity areas using evidence, not just summarise conversations or score sentiment. |
| **Standard for conclusions** | Patterns from this dataset produce research hypotheses and an interview plan (§16). They are validated only through primary research. |

### 22.1 Raw dataset: `google_photos_discovery_annotated`

| Property | Value |
|---|---|
| Files | `google_photos_discovery_annotated.xlsx` (sheet `Sheet1`) and `google_photos_discovery_annotated.csv` (UTF-8, identical to the xlsx in every cell) |
| Rows × columns | 840 × 8 |
| Columns | `source` · `id` · `text` · `retrieval_intent` · `retrieval_scenario` · `retrieval_object` · `memory_clues` · `forgotten_information` |
| Rows per source | google_play 120 · app_store 120 · reddit 120 · google_photos_community 120 · social_media 120 · youtube 120 · forums 120 |
| IDs | Unique; prefixes `gplay`, `app`, `red`, `goo`, `soc`, `you`, `for` |
| Text length | 48–886 characters (median 323) |
| Missing values | None ("Not stated" is used where an annotation doesn't apply) |
| Dates | No date column |
| Duplicate texts in file | 72 exact repeats |

### 22.2 Annotation columns

| Column | Values (rows) | Multi-value? |
|---|---|---|
| `retrieval_intent` | Retrieval-related (602) · Not retrieval-related (238) | No |
| `retrieval_scenario` | General photo/media retrieval (209) · Not stated (194) · Event memory (133) · Person-related memory (130) · Document / screenshot retrieval (103) · Trip / experience memory (71) | No |
| `retrieval_object` | Photo/image (473) · Not stated (184) · Video (74) · Screenshot (74) · Document (35) | No |
| `memory_clues` | Not stated (382) · person/relationship (234) · time/date reference (206) · document/screenshot context (112) · place/trip/experience context (71) | Yes, `;`-separated (counts are mentions) |
| `forgotten_information` | Not stated (554) · exact wording/name (228) · date/time (209) · location (88) · specific retrieval detail (4) | Yes, `;`-separated (counts are mentions) |

These categories are broader than the engine's taxonomy (§10). For example, "person/relationship" covers the engine's `remembered_person` and `remembered_relationship`. Comparing them beyond relevance needs an explicit, reviewed label mapping.

### 22.3 Annotations vs. engine output

Checked on the 745 unique records with the heuristic analyzer (2026-09-17):

| | Engine: relevant | Engine: not relevant |
|---|---|---|
| **Annotation: retrieval-related** | 567 | 10 |
| **Annotation: not retrieval-related** | 10 | 158 |

Agreement on relevance: **725 / 745 (97.3%)**. Disagreements are reviewed record by record, not resolved automatically in either direction.

### 22.4 Missing fields and what they mean for discovery

| Missing field | Consequence |
|---|---|
| Date | No date range in scope, no time-based filtering or trend analysis. |
| Title | Post titles can't serve as evidence; short posts collide more often as duplicates. |
| Platform detail (subreddit, forum, social network) | Source-level comparison only. |
| Source URL | Evidence is traced by `record_id` (`source:id`), not by link. No URLs are invented. |
| Thread context / replies | No thread-level diversity or reply analysis. |
| Engagement (ratings, likes, upvotes) | Severity can't be weighted by engagement. |
| Author | No author signal, and no PII to protect. |

### 22.5 Provenance note

The dataset is ingested **neutrally**: no provenance flag is set, so no output claims the text was either collected from users or generated. Reports, the brief and the workspace name the dataset and nothing more.

For the record, a check on 2026-09-17 found the `text` of all 840 rows identical to conversations produced by this project's generator (`discovery_engine/synthetic/`). This note is the audit trail for that check. Because the origin is not asserted either way in outputs, conclusions drawn from this dataset stay what §16 requires of them: research hypotheses to test in interviews, not validated findings about users.
