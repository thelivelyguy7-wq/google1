# Primary Research Brief (5–6 interviews)

Generated 2026-09-18T21:21:28+00:00. **PLAN ONLY. No interview findings exist yet. Do not fill this section with assumed results.**

Dataset: `google_photos_discovery_contextual_resegmented`.

## Target segment
Contextual Retrieval. Together these cover 156 of 156 records (100.0%) behind the two tested opportunities. Suggested mix of 6 interviews: 6 × Contextual Retrieval (156 records).

## Retrieval scenarios
document, travel, family

## Opportunity areas under test
- **Anchoring a rough sense of time** (`approximate_time_anchoring`): Help users locate photos when they only remember time approximately or relative to another event.
- **Recognising the right photo** (`candidate_recognition`): Help users recognise the intended photo among many visually similar candidates.

## Hypotheses
- WE BELIEVE users know roughly when a memory happened, relative to a life event or season, but not the date needed to navigate to it.
- WE BELIEVE the intended photo is often reachable, but users cannot pick it out among many near-identical candidates, especially when retrieving food/restaurant, travel memories.

## Evidence behind each hypothesis
- *Anchoring a rough sense of time*: 85/85 supporting records describe both remembered and forgotten information. No single dominant breakdown stage; the most common, data missing or unsearchable (F), covers 28%. Unsuccessful outcomes in 66/85; abandonment signals in 19/85. Top forgotten: exact date, exact location, exact object name. Top workarounds: date browsing, manual scrolling, abandonment.
  - `EV-4950c5088e` (app_store): “Timing wise it was a few years back.”
  - `EV-ef7a18108e` (app_store): “It was in 2018 or 2019, can't pin it down.”
- *Recognising the right photo*: 78/80 supporting records describe both remembered and forgotten information. Most breakdowns (100%) are at one stage: can't pick out the right photo (D). Unsuccessful outcomes in 71/80; abandonment signals in 22/80. Top forgotten: exact date, exact location, exact text. Top workarounds: manual scrolling, abandonment, date browsing.
  - `EV-0ad93230f7` (app_store): “There are so many almost identical shots from that day that I can't tell which one it is.”
  - `EV-a7b99fe932` (forums): “I have hundreds of similar shots and can't tell which one it was.”

## Contradictory evidence
- explicit counter evidence (89): Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity (labels: failure not search related, vague search succeeded). Scenario-weighted count: 44.2 (weight = the opportunity's record count in that scenario / its largest scenario count).
- vague memory success (44): Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.
- alternative explanation (24): Some supporting records attribute the failure to missing or unindexed data rather than to the user's memory or the query.
- known workaround exists (1): Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.

## Unknowns
- Does the forgotten information actually cause the failure, or only co-occur with it?
- How often does this happen per user per month (frequency cannot be measured from public posts)?
- What did the user try that is not written in the post?

## Interview objectives
- Reconstruct 1-2 recent, real retrieval episodes per participant, step by step.
- Identify what was remembered and what was missing at the start of each episode.
- Locate the stage where the episode broke down (recall / express / match / recognize / recover, or the data layer).
- Observe workarounds and the point of abandonment.
- Test each hypothesis against its falsification signals.

## Screener
- In the last 3 months, have you tried to find a specific old photo, video, screenshot or document on your phone that you could not find right away? (must be yes)
- What was it? (capture the scenario; recruit toward the target scenarios)
- Roughly how many photos are in your library? (capture only, do not exclude)
- Have you worked in photography, search or machine learning? (exclude: they narrate the system, not the memory)

## Interview questions (behavioural, non-leading)
1. Tell me about the last time you tried to find an old photo that you remembered but couldn't immediately locate.
2. What did you remember about the photo at that moment?
3. What didn't you remember about it?
4. What did you do first? Walk me through it on your phone if you can.
5. What did you search for first? What happened?
6. What did you try when that didn't work?
7. How did you know whether a result was the photo you wanted?
8. How did it end? How long did it take, roughly?
9. Why did you need that photo at that moment?
10. Has something similar happened before? What did you do that time?
11. How did you work out when the photo was taken?
12. Where in your library did you start looking, and why there?
13. When you reached photos from the right time or place, what did you do next?
14. What made two similar photos hard to tell apart?

## Behaviours to observe
- time described relative to other events ('before covid', 'when he was one')
- jumping to a guessed year and scrolling month by month
- several date guesses before landing in the right period
- users reaching the right day or event quickly and then spending most of their time comparing thumbnails
- opening many full-size photos to check details
- settling for a 'close enough' photo

## Signals to validate
- 85/85 supporting records describe both remembered and forgotten information.
- No single dominant breakdown stage; the most common, data missing or unsearchable (F), covers 28%.
- Unsuccessful outcomes in 66/85; abandonment signals in 19/85.
- Top forgotten: exact date, exact location, exact object name. Top workarounds: date browsing, manual scrolling, abandonment.
- 78/80 supporting records describe both remembered and forgotten information.
- Most breakdowns (100%) are at one stage: can't pick out the right photo (D).
- Unsuccessful outcomes in 71/80; abandonment signals in 22/80.
- Top forgotten: exact date, exact location, exact text. Top workarounds: manual scrolling, abandonment, date browsing.

## Signals that would falsify the hypotheses
- users recall the year accurately
- date navigation is quick once any anchor is known
- users rarely see the right event in results
- users recognise the photo instantly once it appears

## Method notes
- Elicit the memory before the device is in hand. The gap between what they remember and what they type is the finding.
- Let them attempt it unaided first. Help only in the final assisted-resolution step, never before.
- Avoid naming any solution. Do not ask whether they would use a feature.
- Record the exact queries typed, and note what they remembered but did not type.
- End every episode knowing whether the item existed and was indexed. Without that, a failure cannot be attributed.

## Methodology
**Hybrid retrieval-episode study on the participant's own library: memory elicitation first, then an unaided live attempt, then a walkthrough of a past failure, then assisted resolution**

*Capture what the person remembers before they touch the app, watch them search with exactly that, then find out whether the photo was ever findable.*

**Why this method**
- The corpus is already retrospective self-report. More interviews of the same kind would add volume, not a new kind of evidence. The session has to produce something public posts cannot: observed behaviour, and ground truth.
- The problem is a gap between the memory a person holds and the query the system needs. That gap is only measurable if the memory is captured *before* the search, so the elicitation comes first and is never skipped.
- Asking someone to recall how they tried to recall is doubly unreliable. A live attempt removes one layer of recall bias; the walkthrough is kept for episodes that cannot be reproduced, not as the main instrument.
- 22.3% of attempts in the corpus break down because the item or its metadata is missing. Nothing in an interview separates 'could not find it' from 'it was never there' unless the session ends by finding the item together.
- Discovery, not validation: no prototype exists yet, so nothing is shown to react to.

**What each part of the session buys**
- *Memory elicitation before search* — For each target, the participant fills a spoken memory card: time, people, place, objects, text, appearance, occasion, and how sure they are of each. No device in hand yet. **Buys:** The held memory, independent of the query. The difference between this card and what they later type is the express-stage gap, which the engine can never see in a public post.
- *Seeded, unaided live attempt* — The participant nominates 2-3 photos at recruitment that they know exist but could not find. They attempt one now, unaided, thinking aloud. Success is their own recognition, not a known file. **Buys:** Observed express, match, recognize and recover behaviour, in their real library, at real scale.
- *Retrospective walkthrough* — One past episode reconstructed step by step: what they needed and why, what they searched, what came back, what they tried next, how it ended. **Buys:** Episodes that cannot be reproduced to order, above all the ones they abandoned.
- *Assisted resolution, last* — The moderator helps find the item, by any means, and records whether it existed, whether it was indexed, and what finally worked. **Buys:** Ground truth per episode: user-stage failure or data/index limitation. Kept last so nothing teaches the participant mid-session.

**Participants**
5-6 participants from the target segment, recruited against that segment's screener, mixed across the retrieval scenarios that carry the evidence. Purposive, not representative: this study establishes mechanism, and the corpus rates stay the estimate of prevalence.

**Session plan**
1. 5 min: consent, what will and will not be recorded, how the session works (no right answers, no product shown).
2. 10 min: library context - size, age, devices, sharing, and how they usually find things.
3. 10 min: memory elicitation for the nominated targets, device face-down. What do they remember, and how sure are they of each clue?
4. 15 min: unaided live attempt on their own library, thinking aloud. The moderator does not help, name features or suggest terms.
5. 12 min: walkthrough of one past episode that cannot be reproduced, especially one they gave up on.
6. 5 min: assisted resolution - find it together, and record whether it was there, indexed, and what worked.
7. 3 min: close - anything they expected to be asked, and what they would have done next if the session had not happened.

**Capture in every episode**
- The memory card per target: each clue, and the participant's own confidence in it, before any searching.
- Every query verbatim, in order, with its timestamp, and whether it was typed, spoken or browsed.
- The clue delta: which remembered clues reached the query, which were dropped, and which were reworded.
- The stage where each episode broke down, in the engine's own model (recall, express, match, recognize, recover, or the data layer).
- Recognition behaviour: how far they scrolled, how long they looked, whether they passed over the target and came back.
- Workarounds in order, and the exact point at which they stopped.
- Resolution: found or not, by what means, and whether the item turned out to be missing, unindexed or simply unreachable by search.

**Analysis plan**
- Code each episode into the journey stages and the memory/forgotten label sets, using the engine's taxonomy so interviews and corpus can be compared directly.
- Tabulate the clue delta across participants: held vs expressed vs what the system needed. This is the primary analysis, not a side observation.
- Classify every episode's resolution as user-stage failure or data/index limitation before interpreting anything else.
- Two people code the first two transcripts independently and reconcile before the rest.
- Compare each hypothesis against its falsification signals before looking for support.
- Log every disconfirming episode explicitly; a single well-evidenced counter-case is enough to reopen the leading opportunity.
- Stop-rule check: if the last two sessions produce no new stage, clue or workaround, treat coverage as sufficient for this decision.

**Alternatives considered**
- Retrospective interview only (no live task): This was the earlier plan. It repeats the evidence type the corpus already has, and asks people to recall a memory failure from memory. Kept as one part of the session, not the whole.
- Lab task with a researcher-supplied library: Perfectly controlled and entirely beside the point: the participant's own memory of their own photos is the thing under study, and it cannot be transplanted.
- Survey at scale: Self-reported frequency would not show where the attempt breaks down, and the engine already gives breadth.
- Diary study over 2-4 weeks: Best for frequency, which public posts cannot answer, but too slow for this decision. Worth running after the problem is defined.
- Usability test of a concept: Premature: it tests a solution before the problem is defined, and invites solution bias.
- Log analysis of search sessions: Would answer frequency and drop-off precisely, but requires product telemetry this study has no access to.

**Ethics and privacy**
- Screen share is opt-in, per episode, and off by default for segments whose material is sensitive. The participant always drives their own device.
- Do not capture, store or ask for photo content. Record queries, outcomes and behaviour, never images.
- Nominated targets are described by the participant in their own words at recruitment; they are never asked to send a photo.
- No names, faces or locations in notes; refer to participants by code.
- Say plainly that this is research, that no product is being sold, and that they can stop or skip any episode at any time.

**Threats to validity**
- Recall bias: participants narrate a tidier attempt than happened. Mitigation: the live attempt is the primary instrument, and the walkthrough asks for the last time, not the typical time.
- Seeding artificiality: a nominated target is not a spontaneous need, so urgency and give-up behaviour may differ. Mitigation: pair every seeded attempt with one unseeded past episode, and compare.
- Moderator contamination: helping, or naming a stage or feature, teaches the participant mid-session. Mitigation: assisted resolution is last, and the guide is solution-free and filtered for leading questions.
- Selection bias: the screener recruits people who remember failing, over-representing failure. Mitigation: also ask for the most recent successful retrieval in each session.
- Corpus bias carried into recruitment: the engine's evidence is public complaint-shaped text. Mitigation: recruit across scenarios, not only the ones with the most posts.
- Small n: 5-6 sessions establish mechanism, not rates. Mitigation: never report interview percentages; carry prevalence questions to telemetry or a diary study.

## Findings
_Not yet collected._
