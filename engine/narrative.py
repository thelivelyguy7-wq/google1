"""Narrative content shared by the Markdown report and the web app.

Static prose lives here as data. Anything that depends on a count is a function taking the computed metrics, so a
number is never pasted into text: it is always read from `metrics.json` at render time.
"""

# ----------------------------------------------------------------- static prose
NEEDS = {
    "N1": ("Find a specific photo when only an approximate date is known", "People/situation without the date; roughly when but not the day; year but not the month"),
    "N2": ("Find a photo remembered by look or gist", "Object look/colour/setting without a name or keyword; visual detail hard to describe; activity without exact words"),
    "N3": ("Find a photo remembered as a story", "Story more vivid than metadata; who was there and what they were doing, but not the album"),
    "N4": ("Find a place-based memory", "Place remembered generally, not its name"),
    "N5": ("Re-find a photo known to exist", "Knows it exists, cannot remember how it was originally found"),
    "N6": ("Confirm the intended photo among plausible candidates", "Sees many plausible results / a similar photo and cannot tell which is right"),
    "N7": ("Reach a photo they say they would recognise", "'Can recognise it if I see it' but does not know how to narrow"),
    "N8": ("Recover after the first attempt does not resolve", "Any; defined by behaviour (reformulation, switching, giving up, other app)"),
    "N9": ("Retrieve an information-bearing image", "Object is a document, screenshot or prescription/medical image (memory text is generic; see limitation 3)"),
}

SEGMENT_DEFS = {
    "SEG-1": "Record states the user could not find the photo, gave up and asked someone else, or switched to another device/app (B12, B10, B08).",
    "SEG-2": "Record states the user reformulated, switched strategy, fell back to browsing after a search, or needed several attempts (B05, B07, B09, B15, B17, B18).",
    "SEG-3": "Record states manual candidate inspection or an unmanageable/uncertain candidate set: date search with too many results, opening results one by one, manual timeline, very large thumbnail set, date-range comparison, similar-but-not-exact (B03, B04, B11, B13, B14, B16).",
    "SEG-4": "Record states one initial search (person+place, text-in-image, object keyword) with no reformulation, browsing or outcome (B01, B02, B06).",
    "SEG-T": "Union of SEG-2 and SEG-3: attempted to retrieve a specific photo they expected to exist, lacked a precise identifier, and either changed strategy/repeated attempts or manually inspected a candidate set.",
}

MODES = {
    "H1": ("Interviews: memory reconstruction and details that never reached the first query.", "Survey: how often users remember clues they did not type."),
    "H2": ("Task tests and interviews: how the target was recognised or missed.", "Survey: how often users report seeing but doubting the right photo."),
    "H3": ("Interviews: why date was chosen; tasks that supply richer clues.", "Survey and production: share of attempts starting from date narrowing, and window size."),
    "H4": ("Interviews: what prompted each strategy change.", "Production: queries before success and abandonment after N tries."),
    "H5": ("Screener and library audit: was the photo present.", "Survey and production: share of failed retrievals where the photo was absent."),
    "H6": ("Task comparison across object types.", "Survey: scenario incidence by object type."),
    "H7": ("Interviews: what participants remember as ordinary retrievals.", "Survey: share of recent attempts that succeeded on the first try."),
}

INTERVIEW_GUIDE = [
    ("Warm-up (0–4 min)", ["Roughly how many photos and videos do you keep in your library, and what kinds?", "When did you last look for an older photo? What do you usually look for?"], "Library size and habits; do not mention search features."),
    ("Recent retrieval incident (4–9)", ["Tell me about the last time you went looking for a photo you knew you had. What set it off?", "Where were you, on what device, and why did it matter then?"], "Anchor on one real event; skip if none in the last month."),
    ("Memory reconstruction (9–14)", ["Before you started, what did you remember about the photo? What came to mind first?", "What did you not remember that you expected to?", "How sure were you that the photo existed?"], "Probe: people, place, story, look, roughly when, text. Do not list dimensions first. Note details the participant adds later that never reached a query (D2 evidence)."),
    ("Search behaviour (14–18)", ["What was the very first thing you did? Why that?", "Walk me through what you typed or tapped, in order."], "No suggestion of methods."),
    ("Failure / recovery (18–22)", ["What happened after that?", "At what point did you become unsure it would work? What did you do next, and why?", "What made you keep going, or stop?"], "Probe reformulation, browsing, other apps, asking people."),
    ("Recognition (22–25)", ["How did you decide a photo was the one?", "Did you ever look at a photo and doubt it? What made you doubt?"], "Include 'similar but not exact' cases. Ask whether the right photo appeared earlier without being noticed (D3 vs D4)."),
    ("Workarounds (25–27)", ["Did you use anything outside Google Photos? Was the photo in your library?"], "Tests H5."),
    ("Reflection (27–30)", ["Looking back, what made that difficult, or easy?", "Anything about that search you'd want us to understand?"], "Solution preferences are not asked. If time remains and the participant raises ideas, note them without probing."),
]

TASKS = [
    ("T1 Trip/place", "Find the photo of the small café you visited on a trip", "People with you, the general place, roughly the season", "Exact place name, exact date", "First action and query; place vs person vs date; whether the café ever appears in results"),
    ("T2 Event/people", "Find the photo from a family celebration", "Who was there, what was happening, approximate year", "Album, month, event name", "Person-then-browse patterns; date-range use; comparison of near-identical candidates"),
    ("T3 Document/screenshot", "Find the screenshot of a booking or receipt", "Gist of what it said, roughly when", "File name, exact wording, date", "Text-in-image attempts; browsing; workaround use"),
    ("T4 Episode/story", "Find the photo you took during a time you were unwell (seeded stand-in)", "The story and setting", "Any searchable keyword, date", "Reformulation; strategy switching; what prompts a change"),
    ("T5 Visual object", "Find the photo of a specific object (e.g. a yellow toy truck) among similar items", "How it looked", "Its name, date", "Verification among near-identical candidates; wrong-photo confirmations"),
]

TASK_QUALITATIVE = {
    "T1": "Which clue the participant led with and why; whether the target appeared but was skipped (D3 vs D4)",
    "T2": "Cues used to tell near-identical candidates apart; where doubt appeared",
    "T3": "Whether text or gist drove the query; reaction when a text search fails",
    "T4": "What the participant said they remembered but never typed (D2); trigger for each strategy change",
    "T5": "Verbal doubt statements; how a 'similar but not exact' photo was rejected or accepted",
}

TASK_PRIMARY = {"T1": "Retrieval success within 5 min", "T2": "Time to successful retrieval",
                "T3": "Retrieval success within 5 min", "T4": "Attempts / reformulations",
                "T5": "Candidate photos inspected before confirming"}


# ----------------------------------------------------------------- count-dependent prose
def opportunities(ctx) -> dict:
    """Opportunity cards. `ctx` supplies the metrics and the evidence-quote helper."""
    s1, ev, S1 = ctx["s1"], ctx["ev"], ctx["S1"]
    opp_txt = {
        "O1": dict(node="D2", beh="User holds context but says it cannot be turned into a keyword, name, wording, description or narrowing step; contrasts this with ease when an exact date/name is known.", st="Express (from Remember)",
                   sev="Signals come from the behaviour sentences of these records (reformulation, browsing, uncertainty), not from the barrier statement itself.", quote=ev("memory_code", "M06", 1),
                   uc="Extra attempts or manual scanning; some stop.", pc="A photo that exists and is recognisable may never be reached from the first query.",
                   unk="Whether users hold richer memory than they express, or the memory is thin; whether failure is at input or at interpretation."),
        "O2": dict(node="D2/D3", beh="Only an approximate time is known (day/month unknown); users search by date and get too many results, or compare a date range by hand.", st="Express → Match",
                   sev="Date search 'too many results' (%d), manual date-range comparison (%d)." % (s1["behavior_code"]["B03_date_search_too_many"], s1["behavior_code"]["B16_date_range_compare"]), quote=ev("behavior_code", "B03", 1),
                   uc="Long scanning of broad time windows.", pc="Time is the clue users have, but as a search scope it may be too coarse.",
                   unk="Whether time is the strongest memory or simply the most available tool."),
        "O3": dict(node="D4", beh="Candidates are surfaced or browsed but the user cannot confirm which is right, or finds only a similar photo.", st="Recognize",
                   sev="'Cannot tell which is right' (%d), similar-not-exact (%d), one-by-one opening (%d), very large thumbnail set (%d)." % (s1["closer_code"]["C08_plausible_cannot_tell"], s1["behavior_code"]["B14_similar_not_exact"], s1["behavior_code"]["B04_open_results_one_by_one"], s1["behavior_code"]["B13_large_thumbnail_set"]), quote=ev("behavior_code", "B14", 1),
                   uc="Uncertainty about having found the right photo; time spent comparing.", pc="A successful retrieval may sit in the candidate set unconfirmed.",
                   unk="Whether the target was in the candidate set; what cues users use to verify."),
        "O4": dict(node="D3", beh="Users report result sets that are too large or plausible-but-undifferentiated after a query.", st="Match",
                   sev="Only two explicit statements describe product output; the stage is thinly observed.", quote=ev("behavior_code", "B03", 1),
                   uc="Sifting through results.", pc="Matching quality cannot be judged from this corpus.", unk="Almost everything: the corpus does not describe what was returned, and 0 records say the product misread the clues."),
        "O5": dict(node="D5", beh="After the first attempt does not resolve, users reformulate, switch between terms/albums, fall back to browsing, use another app/device, ask another person, or stop.", st="Recover",
                   sev="Reformulation %d, strategy switch %d, browsing %d, external workaround %d, abandonment %d, failure %d." % tuple(s1["signals"][k] for k in ["reformulation", "strategy_switch", "browsing", "external_workaround", "abandonment", "failure"]), quote=ev("behavior_code", "B15", 1),
                   uc="Repeated effort; for %d records the search ends in failure, giving up or another app." % S1["n"], pc="Successful retrieval is delayed or lost; only %d records state a (effortful) success." % s1["outcome"]["found_with_effort"],
                   unk="What triggers a change of strategy, what makes users continue or stop, and whether other-app users found the photo."),
        "O6": dict(node="D1", beh="Users know a photo exists but not its album, or how they originally reached it.", st="Remember → Express",
                   sev="Mostly memory statements; behaviour is generic.", quote=ev("memory_code", "M09", 1),
                   uc="No remembered route back to the photo.", pc="Navigation-based retrieval is unavailable when the path is forgotten.", unk="How users normally re-find photos; whether organisation habits matter."),
        "O7": dict(node="D6", beh="Users ask someone else to send the photo or switch to another device/app.", st="Recover (boundary of the searchable library)",
                   sev="Abandonment %d; other-app/device %d." % (s1["signals"]["abandonment"], s1["outcome"]["external_workaround"]), quote=ev("behavior_code", "B10", 1),
                   uc="Leaves the product to complete the task.", pc="Retrieval success is not captured in Photos when the photo lives elsewhere or the user gives up.",
                   unk="Whether the photo was in the user's Google Photos library at all (deleted, other account, other app)."),
        "O8": dict(node="D2", beh="Users say they can recognise the photo but do not know how to narrow the results: the gap is knowing what clues or controls the search can act on, not remembering.", st="Express",
                   sev="One explicit sentence ('I don't know how to narrow the results'); every record with it is also an expression-barrier record (O8 is a subset of O1).", quote=ev("memory_code", "M05", 1),
                   uc="Trial-and-error with wording, filters and browsing.", pc="A capability the product has may go unused because users cannot tell it exists or applies.",
                   unk="Whether users lack knowledge of narrowing options or the options do not fit what they remember. The corpus has no statement about what users know the product can do."),
    }
    return opp_txt


def hypotheses(ctx) -> list:
    """H1-H7 as (name, node, evidence key, observation, interpretation, hypothesis, rival, test, for, against, unknown)."""
    s1, J, ind, pct = ctx["s1"], ctx["J"], ctx["ind"], ctx["pct"]
    O1, E, recog, exit_o1, exit_all = ctx["O1"], ctx["E"], ctx["recog"], ctx["exit_o1"], ctx["exit_all"]
    hyps = [
        ("H1 — Memory richer than expressed", "D2", "hyp:H1",
         f"{s1['express_barrier']} records say memory is hard to turn into a query; behaviour shows reformulation ({s1['signals']['reformulation']}) and switching ({s1['signals']['strategy_switch']}).",
         "Many users say what they remember cannot be typed as a search, yet still try several searches.",
         "Users may hold more contextual detail than their first query carries.",
         "Memory is genuinely thin or generic, so it is a remember problem, not an expression problem.",
         "Prompted remember adds nothing usable, or first queries already contain everything they can remember (falsified). Neutral cues surface details the first query omitted (supported).",
         f"{s1['express_barrier']} explicit barrier statements.", f"No outcome difference for O1 ({pct(exit_o1, O1['n'])} vs {pct(exit_all, E)}).", "What participants can remember on demand."),
        ("H2 — Candidate present but not recognisable", "D4", "hyp:H2",
         f"'Cannot tell which is right' {s1['closer_code']['C08_plausible_cannot_tell']}; similar-not-exact {s1['behavior_code']['B14_similar_not_exact']}; one-by-one opening {s1['behavior_code']['B04_open_results_one_by_one']}.",
         "Users report both plausible candidates they cannot separate and being able to recognise the photo on sight.",
         "Users see the right photo among candidates but lack cues to confirm it (near-duplicates, burst shots, generic scenes).",
         "The target was never among the candidates (matching gap), or users hold a wrong mental image of the photo.",
         "Log whether the target appeared in inspected sets. Falsified if it is mostly absent, or if participants confirm it instantly once shown.",
         "Explicit uncertainty statements.", f"{recog} records claim they would recognise it on sight.", "Whether the target was present."),
        ("H3 — Time is used as a scope because it is available, not because it is the best memory", "D2/D3", "hyp:H3",
         f"Approximate time in {s1['memory_code']['M07_approx_time_not_day'] + s1['memory_code']['M10_year_not_month']} records; date search 'too many results' {s1['behavior_code']['B03_date_search_too_many']}; date-range comparison {s1['behavior_code']['B16_date_range_compare']}.",
         "Most users lacking the exact date still lean on date narrowing, and it often returns broad sets.",
         "Users default to date narrowing because it is the tool they know, producing broad windows.",
         "Time is the most reliable clue and windows are large because libraries are large.",
         "Ask what was remembered first and why date was chosen; give richer clues in tasks. Falsified if participants prefer date even with stronger clues and windows stay small.",
         "Date is the largest forgotten-information family.", "None in the corpus.", "Clue ranking within individuals."),
        ("H4 — Recovery is unguided", "D5", "hyp:H4",
         f"{J['breakdown']['RECOVER']['n']} records show recovery behaviours; the corpus never states why users changed strategy.",
         "Users change strategy often, but the file never says what prompted the change.",
         "After a failed attempt users get no signal about why it failed, so they cycle wording, albums and scrolling.",
         "Cycling is habit or a preference for browsing, independent of any signal; or recovery is efficient and only unlucky users post.",
         "Interview 'what did you try next and why'; tasks recording whether strategy changes followed results. Falsified if changes track stable personal habits regardless of results.",
         "Reformulation and switching signals.", f"Only {s1['outcome']['found_with_effort']} records state a success after effort.", "Decision triggers."),
        ("H5 — Photo not in the searchable library", "D6", "hyp:H5",
         f"Asked someone else {s1['outcome']['abandoned']}; other device/app {s1['outcome']['external_workaround']}; deleted-photo restore records (3, outside the denominator).",
         "Some users end the search by leaving the product; the file does not say whether the photo was ever findable.",
         "For some users the photo lives elsewhere (received via message, other account, deleted), so search cannot succeed.",
         "The photo is in the library and unreachable; 'ask someone' reflects convenience.",
         "Screener + library audit: was the photo present? Falsified if it is present in most failed cases.",
         "Indirect only.", "No record states absence.", "Presence in the library."),
        ("H6 — Object type changes the retrieval problem", "all", "hyp:H6",
         f"Objects span trip/family/event items ({s1['object_class']['family_person'] + s1['object_class']['event_social'] + s1['object_class']['travel_place']}) and document/medical items ({s1['object_class']['document_screenshot'] + s1['object_class']['medical']}).",
         "Objects vary widely, but the file gives no basis for saying object type changes how people search.",
         "Utility images (documents, prescriptions) are searched by content/text, memorial photos by story and people.",
         "Behaviour is object-independent; differences are individual.",
         "Compare tasks across object types. Falsified if strategies and success do not differ by type.",
         "Plausible on its face.", f"Object is independent of memory and behaviour here (V={ind['object_class x memory_code']['cramers_v']}, p={ind['object_class x memory_code']['p']}); some pairings are incoherent.", "Everything."),
        ("H7 — The corpus overstates difficulty (selection effect)", "all", "hyp:H7",
         "All relevant records are complaint/help posts; no uneventful retrievals exist.",
         "The file contains only posts about difficulty, so it cannot show how common difficulty is.",
         "Most real retrievals from imprecise memory succeed quickly; the corpus captures only the tail.",
         "Difficulty is common and under-reported.",
         "Survey with neutral remember of recent attempts. Supported if most succeed in one attempt; weakened if effortful or unsuccessful retrieval is common.",
         "Sampling logic.", "None.", "Prevalence."),
    ]
    return hyps
