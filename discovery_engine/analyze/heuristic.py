"""Heuristic (rule/lexicon) analyzer.

Purpose: run the full pipeline offline, and give a transparent baseline against
which Claude output can be compared. It is deliberately conservative: every
signal quotes the sentence that triggered it, confidence stays <= 0.5, and it
never guesses a JTBD beyond stitching quoted fragments.

It is NOT a substitute for the Claude analyzer on real-world text.
"""
from __future__ import annotations

import re

from ..analyze.llm import empty_payload

PROMPT_VERSION = "heuristic-v1"

I = re.IGNORECASE


def _sentences(text: str) -> list[str]:
    return [m.group(0).strip() for m in re.finditer(r"[^.!?\n]+[.!?]*", text) if len(m.group(0).strip()) > 2]


def _find(patterns: list[tuple[str, str]], sentences: list[str], multi: bool = True) -> list[tuple[str, str]]:
    """Return (label, sentence) for each pattern that matches; one hit per label."""
    hits, seen = [], set()
    for label, pat in patterns:
        rx = re.compile(pat, I)
        for s in sentences:
            if rx.search(s) and label not in seen:
                hits.append((label, s))
                seen.add(label)
                break
        if hits and not multi:
            break
    return hits


NEG = r"(no idea|can'?t (remember|recall|pin)|cannot (remember|recall)|don'?t (remember|know|recall)|not sure|never (saved|knew|put)|no clue|forgot|could'?ve been|don'?t have)"

PLACE_WORDS = r"(beach|hotel|venue|house|place|shop|mall|park|nursery|stadium|resort|warehouse|club|pub|homestay|temple|station|terrace|backyard|apartment|living room|meeting room|parking|rooftop|town|backwaters|lake|goa|kerala|tokyo|delhi|bangalore|portugal|lisbon|switzerland|mysore|himachal|meghalaya|downtown|street|hill)"
PERSON_WORDS = r"\b(my|our|a|the) (college |school |best |old )?(friends?|sister|brother|mom|dad|mother|father|wife|husband|partner|son|daughter|cousins?|grandmother|grandma|grandparents|nephew|aunt|uncle|landlord|team|classmates?|neighbours|colleagues?|parents|family|gang|guy|groom|bride)\b"
COLOR = r"\b(blue|red|green|yellow|pink|purple|orange|grey|gray|white|black|silver|brass|mustard|maroon|gold|golden|neon)\b"

MEMORY_PATTERNS = [
    ("remembered_trip", r"\b(trip|vacation|holiday|honeymoon|trek|backpacking|road trip)\b"),
    ("remembered_event", r"\b(wedding|party|concert|fest|procession|function|haldi|sangeet|reception|offsite|farewell|awards?|gig|match|visarjan|play)\b"),
    ("remembered_occasion", r"\b(birthday|anniversary|diwali|eid|new year)\b"),
    ("remembered_person", PERSON_WORDS),
    ("remembered_place", rf"\b(somewhere|near|at|in|on|outside) (the |a |my |our |some |an )?[\w' -]{{0,30}}{PLACE_WORDS}\b"),
    ("remembered_time_approximation", r"\b(maybe|around|sometime|probably|or so|a few (years|months|weeks)|couple of (years|months)|years? ago|months? ago|weeks? ago|last (year|month|summer|spring|quarter)|before covid|when (he|she|i|we) (was|were)|one (summer|winter|of the)|20\d\d or 20\d\d)\b"),
    ("remembered_visual_appearance", rf"{COLOR}|\b(wearing|in the background|in the corner|costume|lights|thumb covering|handwriting|confetti)\b"),
    ("remembered_text", r"\b(it said|mentioned|something about|the (policy |serial |passport |pnr )?(number|name|total|prices?|fees|deadline|values|grades|amount|dates))\b"),
    ("remembered_object", r"\b(medicine|tablets|pipe|plant|shelf|lamp|shoes|fabric|passport|card|report|prescription|bill|receipt|letter|tattoo|dent|whiteboard|agreement|marksheet|estimate|notes|menu|label)\b"),
    ("remembered_context", r"\b(i took it (when|to|for|so|after|right)|i took (a photo|it) (to|so|when|before)|we were|as proof|someone (posted|shared|sent)|came through|screenshotted|i screen-recorded|photographed)\b"),
    ("remembered_activity", r"\b(eating|singing|dancing|learning to|riding|hiking|playing)\b"),
    ("remembered_emotion", r"\b(means a lot|funniest|so happy|happy day|best picture)\b"),
    ("remembered_relationship", r"\b(the one (my|that)|sent (me|us)|forwarded|my (wife|husband) took|a scan my)\b"),
]

FORGOTTEN_PATTERNS = [
    ("exact_date_unknown", rf"{NEG}[^.]*\b(date|year|month|when|day)\b|\bnot sure (which|what) year\b|\bcan'?t pin it down\b"),
    ("exact_location_unknown", rf"{NEG}[^.]*\b(where|place|town|location|restaurant name|called)\b"),
    ("person_name_unknown", rf"{NEG}[^.]*\b(his|her|their|the guy'?s|the person'?s) name\b"),
    ("event_name_unknown", rf"{NEG}[^.]*\b(event|occasion|what (the )?(event|function) was)\b"),
    ("exact_text_unknown", rf"{NEG}[^.]*\b(exact (words|wording|text)|what it said|wording)\b"),
    ("exact_object_name_unknown", rf"{NEG}[^.]*\b(what (it|the thing|that|they) (is|are) called|name of (the|that) (thing|plant|medicine|drops)|what .* called)\b"),
    ("album_unknown", rf"{NEG}[^.]*\balbum\b"),
    ("exact_keyword_unknown", rf"{NEG}[^.]*\b(what word|what to (call|type|search)|which word|search term)\b"),
    ("filename_unknown", r"\b(filename|file name|IMG_?\d*)\b"),
    ("metadata_unknown", r"\blocation (data )?was (probably )?off\b|\bno (dates|metadata)\b"),
]

QUERY_RX = re.compile(r"(searched(?: for)?|search(?:ing)? for|tried(?: searching)?|typed|searching)\s+[\"“]([^\"”]{2,80})[\"”]", I)

OUTCOME_PATTERNS = [
    ("not_found", r"\b(nothing (came up|showed)|no results|0 results|zero results)\b"),
    ("wrong_results", r"\b(random|nothing to do with|irrelevant|wrong (photos|results|ones)|completely different)\b"),
    ("too_many_results", r"\b(too many|hundreds|thousands|\d,?\d{3} (photos|pictures|results))\b"),
    # Negation guard: "never found it" is not a found outcome.
    ("found", r"\b(there it was|popped up|showed up|(?<!never )found it|got it on the first try|(it|search) found (the|my|a|our))\b"),
]

STRATEGY_PATTERNS = [
    ("date_based_search", r"\b(by (year|date|month)|jumped to|date jump|month by month)\b"),
    ("location_based_search", r"\b(map view|places|by location|the map)\b"),
    ("person_based_search", r"\b(face group|faces|people tab|person'?s face)\b"),
    ("album_based_search", r"\balbums?\b(?![^.]*\b(never|not sure|don'?t)\b)"),
    ("manual_browsing", r"\bscroll(ed|ing)?\b"),
    ("repeated_search", r"\b(kept (retyping|searching|trying)|different searches|a few more (words|searches)|searched again|every (word|combination))\b"),
    ("query_refinement", r"\b(synonyms?|another word|different words|added the|removed the|more specific)\b"),
    ("metadata_guessing", r"\b(guess(ed|ing)? the (year|date|place)|plus the year)\b"),
]

WORKAROUND_PATTERNS = [
    ("manual_scrolling", r"\bscroll(ed|ing)? (back|through|for)|\bscrolled\b"),
    ("date_browsing", r"\b(jumped to|month by month|scrollbar|date jump)\b"),
    ("location_browsing", r"\b(map view|places view|the map)\b"),
    ("album_browsing", r"\b(checked|went through|looked through) (all )?(my |the )?albums\b"),
    ("people_browsing", r"\b(face group|went through the faces|people section)\b"),
    ("ask_another_person", r"\b(texted|asked|messaged) (my|a|the) \w+|\bsend it again\b|\bstill had it\b"),
    ("other_application", r"\b(whatsapp chats?|gmail|my email|instagram saved|telegram|drive folder)\b(?=[^.]*\b(instead|found|searched|checked|looked)\b)|\b(searched|checked|looked in) (my )?(whatsapp|gmail|email|telegram)\b"),
    ("external_search", r"\b(googled|youtube tutorial|reddit for tips|looked up how)\b"),
    ("synonym_search", r"\bsynonyms?\b"),
    ("repeated_search", r"\b(kept (retyping|searching|trying)|different searches)\b"),
    ("filters", r"\b(screenshots? (filter|category)|documents? (filter|category)|filter)\b"),
    # A bare "next week" is usually a deadline ("their anniversary next week"), not coming back later.
    ("return_later", r"\b(tried again (the next|later|a week)|came back to it|for the day)\b"),
    ("abandonment", r"\b(gave up|give up|giving up|stopped looking)\b"),
]

FAILURE_PATTERNS = [
    ("F_data_index_limitation", r"\b(not searchable|isn'?t searchable|(doesn'?t|don'?t) seem to be (searchable|indexed)|not indexed|location (data )?was (probably )?off|partner'?s library|shared album|never (got )?backed up|old phone|no dates|doesn'?t (read|pick up) (the )?text|screen recording|isn'?t indexed)\b"),
    ("E_refinement", r"\b(no idea what else|ran out of ideas|didn'?t know what (else|to try)|what else to try|out of ideas)\b"),
    ("D_result_evaluation", r"\b(identical|look(s)? the same|all look|can'?t tell which|tiny thumbnails|near(ly)? duplicates?|similar shots|which one it was)\b"),
    ("B_system_understanding", r"\b(doesn'?t understand|took [^.]* literally|ignores?|ignored|matches? one word|only matched|half of what i type)\b"),
    ("A_memory_expression", r"\b(didn'?t know how to describe|can'?t put it into|how do you even search|don'?t know what to (type|search|call)|no idea what to (search|type|call)|put it into (search )?words)\b"),
    ("C_retrieval", r"\b(never shows|doesn'?t show up|not showing|won'?t show|nothing came up|no results|0 results|search never)\b"),
]

# Order matters: negated forms must be tested before "found", and an explicit
# later success ("finally found it") outranks an earlier "gave up for the day".
STATUS_PATTERNS = [
    ("partially_found", r"\b(similar one but not|not the exact|close but not)\b"),
    ("uncertain", r"\b(might be it|not sure (it'?s|if it'?s) the same|could be the one)\b"),
    ("not_found", r"\b(still (haven'?t|can'?t|couldn'?t) find|never found|haven'?t found|still missing)\b"),
    # "it found the photo ... in seconds": success stated from the system's side.
    ("found", r"\b(finally found|(?<!never )found it|got it eventually|got it on the first|there it was|popped up|found (the|one|a) [^.]* by|(it|search) found (the|my|a|our))\b"),
    ("abandoned", r"\b(gave up|give up|stopped looking)\b"),
]

SEGMENT_PATTERNS = [
    ("large_library", r"\b\d{1,3}(,\d{3}|k\+?)\s*(\+ )?(photos|pictures)|\b\d{1,2} years of photos\b|\b\d{2},\d{3} (photos|pictures)"),
    ("long_tenure", r"\b(since it launched|since 20\d\d|years ago)\b(?=[^.]*\b(using|backing|moved|used)\b)|\b(been backing up everything|used google photos since|moved all my old)\b"),
    ("android_device", r"\b(pixel|samsung|android)\b"),
    ("ios_device", r"\b(iphone|ios|ipad)\b"),
    ("desktop_web", r"\b(web version|photos\.google\.com|laptop|my pc)\b"),
    ("frequent_searcher", r"\b(search [^.]*(every day|daily|a lot))\b"),
    ("screenshot_heavy", r"\b(ridiculous number of screenshots|half my library is screenshots)\b"),
    ("shared_library", r"\b(partner library|shared albums?)\b"),
]

COUNTER_PATTERNS = [
    ("vague_search_succeeded", r"\b(search is amazing|impressed|on the first try|in seconds|took two minutes)\b"),
    ("failure_not_search_related", r"\b(had deleted it|never got backed up|not the app'?s fault|in my partner'?s library, not mine)\b"),
    ("prefers_browsing_over_search", r"\b(stopped using search|just scroll|more predictable)\b"),
]

SCENARIO_LEXICON = {
    "screenshot": r"\bscreenshot|screen ?shot|screenshotted\b",
    "video": r"\bvideo|gig|screen-recorded|recording\b",
    "receipt": r"\b(bill|receipt|warranty|estimate|invoice)\b",
    "document": r"\b(passport|agreement|insurance papers?|vaccination card|marksheet|certificate|document)\b",
    "medical_or_health_image": r"\b(medicine|tablets|rash|blood test|prescription|doctor|dermatologist|eye drops)\b",
    "wedding_memory": r"\b(wedding|haldi|sangeet|reception|bride|groom)\b",
    "travel_memory": r"\b(trip|vacation|holiday|honeymoon|backpacking|hotel|houseboat|train window|waterfall)\b",
    "food_restaurant_memory": r"\b(restaurant|caf[eé]|dessert|ramen|menu|biryani|wine|street food|chaat)\b",
    "event_memory": r"\b(concert|awards?|procession|annual day|fireworks|new year party|visarjan)\b",
    "work_memory": r"\b(whiteboard|client|offsite|site inspection|manager|portfolio)\b",
    "school_or_college_memory": r"\b(college fest|classmates?|farewell|exams?|school)\b",
    "family_memory": r"\b(son|daughter|dad|mom|grandparents|family|nephew|aunt)\b",
    "friend_memory": r"\b(friends|gang|best friend|trek)\b",
    "purchase_related_image": r"\b(buy|sale|order|product|lamp|shoes|sofa)\b",
    "location_memory": r"\b(parking|homestay|temple|where i parked)\b",
    "object_memory": r"\b(plant|shelf|dent)\b",
    "personal_memory": r"\b(shirt|tattoo|letter to myself|profile photo)\b",
}

OBJECT_BY_SCENARIO = {"screenshot": "screenshot", "purchase_related_image": "screenshot", "video": "video",
                      "document": "document_or_receipt", "receipt": "document_or_receipt"}

CONTEXTUAL = {"remembered_event", "remembered_trip", "remembered_context", "remembered_relationship",
              "remembered_occasion", "remembered_activity", "remembered_social_context"}


def _sig(label: str, sentence: str, precision: str = "not_applicable", value: str | None = None) -> dict:
    return {"label": label, "value": value or label.replace("_", " "), "quote": sentence, "precision": precision}


class HeuristicAnalyzer:
    name = "heuristic"
    prompt_version = PROMPT_VERSION
    model = None

    def analyze(self, chunk_text: str, meta: dict) -> tuple[dict, None]:
        title = meta.get("title") or ""
        text = f"{title}. {chunk_text}" if title else chunk_text
        sents = _sentences(text)
        low = text.lower()

        about_photos = re.search(r"\b(photos?|pics?|pictures?|screenshots?|videos?|images?|library|shots?|selfie|candid|scan)\b", low)
        about_finding = re.search(r"\b(find|found|search|searched|searching|looking for|look for|locate|scroll|retrieve|can'?t find|dig up|track down|showed up|results?)\b", low)
        if not (about_photos and about_finding):
            return empty_payload(False, "heuristic: no photo-retrieval vocabulary", 0.4), None

        p = empty_payload(True, "heuristic: mentions finding/searching photos", 0.4)

        first_person_attempt = re.search(
            r"\b(i|we) (searched|tried|typed|scrolled|was looking|am looking|have been looking|'ve been looking|spent|looked|went through|ended up|kept|jumped)\b"
            r"|\b(can'?t|couldn'?t) find\b|\bsearched\b|\bi'?m trying to find\b|(^|[.!?]\s+)(tried|spent|found (the|it|one)|got it|thought search|was sure i'?d)\b"
            r"|\bdoes anyone know how to find\b|\blooking for (a|the|that|my)\b", low)
        if re.match(r"\s*(tip:|try |search by|use the|check whether|name the|ask whoever|you can|if it was)", low):
            p["perspective"] = "advice_or_answer"
        elif first_person_attempt:
            p["perspective"] = "first_person_experience"
        elif re.search(r"\b(should|i wish|would help|nobody does|i'?ve stopped|it'?s frustrating|is fine if)\b", low):
            p["perspective"] = "opinion_or_feature_request"
        p["describes_retrieval_attempt"] = p["perspective"] == "first_person_experience"

        scores = {k: len(re.findall(v, low)) for k, v in SCENARIO_LEXICON.items()}
        best = max(scores, key=scores.get)
        p["retrieval_scenario"] = best if scores[best] else "other"
        p["retrieval_object"] = OBJECT_BY_SCENARIO.get(best, "photo") if scores[best] else "unknown"

        for label, pat in STATUS_PATTERNS:
            if re.search(pat, low):
                p["success_status"] = label
                break

        remembered = []
        # Queries are EXPRESS evidence and need statements are goals; neither is a memory report.
        memory_sents = [s for s in sents if not QUERY_RX.search(s)
                        and not re.search(r"\b(i need it|i want|asked (me )?for|needs it|wants (it|the))\b", s, I)]
        for label, s in _find(MEMORY_PATTERNS, memory_sents):
            if re.search(NEG, s, I) and label in ("remembered_place", "remembered_text"):
                continue  # "can't remember the place" is not remembering the place
            precision = "approximate" if re.search(r"\b(maybe|around|sometime|probably|i think|not sure|or so|somewhere|some)\b", s, I) else "exact"
            remembered.append(_sig(label, s, precision))
        p["remembered_information"] = remembered

        p["forgotten_information"] = [_sig(label, s) for label, s in _find(FORGOTTEN_PATTERNS, sents)]

        queries = []
        for s in sents:
            for m in QUERY_RX.finditer(s):
                q = m.group(2).strip()
                words = q.split()
                if re.search(r"\b(19|20)\d\d\b|\b(january|february|march|april|may|june|july|august|september|october|november|december|summer|winter)\b", q, I):
                    qtype = "date" if len(words) == 1 else "metadata"
                elif len(words) >= 4:
                    qtype = "natural_language"
                else:
                    qtype = "keyword"
                orient = []
                if re.search(r"\b(19|20)\d\d|summer|winter|december|october|march|july|june|september|april\b", q, I):
                    orient.append("approximate_when")
                if re.search(PLACE_WORDS, q, I):
                    orient.append("where")
                if re.search(r"\b(me|friends?|dad|mom|grandma|girl|boy|baby|couple|team|students|people|family|guy|lady)\b", q, I):
                    orient.append("who")
                if re.search(COLOR, q, I):
                    orient.append("what_they_saw")
                if not orient:
                    orient.append("image_contents")
                outcome = "unclear"
                for label, pat in OUTCOME_PATTERNS:
                    if re.search(pat, s, I):
                        outcome = label
                        break
                queries.append({"query_text": q, "quote": m.group(0), "query_type": qtype, "orientation": orient,
                                "outcome": outcome})
        p["queries"] = queries
        p["attempt_count"] = len(queries) or None

        strategies = [_sig(label, s) for label, s in _find(STRATEGY_PATTERNS, sents)]
        types = {q["query_type"] for q in queries}
        if "keyword" in types:
            strategies.append(_sig("keyword_search", next(q["quote"] for q in queries if q["query_type"] == "keyword")))
        if "natural_language" in types:
            strategies.append(_sig("natural_language_search", next(q["quote"] for q in queries if q["query_type"] == "natural_language")))
        if types & {"date", "metadata"}:
            strategies.append(_sig("metadata_guessing", next(q["quote"] for q in queries if q["query_type"] in ("date", "metadata"))))
        if len(queries) >= 2 and not any(s["label"] == "repeated_search" for s in strategies):
            strategies.append(_sig("repeated_search", queries[1]["quote"]))
        p["search_strategies"] = strategies
        p["query_refinements"] = [s for s in strategies if s["label"] in ("query_refinement", "repeated_search")]

        workarounds = [_sig(label, s) for label, s in _find(WORKAROUND_PATTERNS, sents)]
        p["workarounds"] = workarounds

        stage_hit = _find(FAILURE_PATTERNS, sents, multi=False)
        if stage_hit:
            p["failure_stage"], p["failure_quote"] = stage_hit[0]
            p["failure_reason"] = f"heuristic cue for {stage_hit[0][0]}"
        elif p["success_status"] in ("not_found", "abandoned"):
            p["failure_stage"], p["failure_reason"] = "unclear", "failure stated but no stage cue"

        behaviors = []
        if p["describes_retrieval_attempt"]:
            behaviors.append(_sig("retrieval_attempt", first_person_sentence(sents)))
        status_behavior = {"found": "successful_retrieval", "not_found": "failed_retrieval", "abandoned": "abandoned_retrieval"}
        if p["success_status"] in status_behavior:
            s = next((x for x in sents if re.search(dict(STATUS_PATTERNS)[p["success_status"]], x, I)), None)
            if s:
                behaviors.append(_sig(status_behavior[p["success_status"]], s))
        behaviors += [s for s in strategies if s["label"] not in {b["label"] for b in behaviors}]
        if any(r["label"] in CONTEXTUAL for r in remembered) and p["describes_retrieval_attempt"]:
            r = next(r for r in remembered if r["label"] in CONTEXTUAL)
            behaviors.append(_sig("contextual_description", r["quote"]))
        if any(r["label"] == "remembered_visual_appearance" for r in remembered) and p["describes_retrieval_attempt"]:
            behaviors.append(_sig("visual_description", next(r["quote"] for r in remembered if r["label"] == "remembered_visual_appearance")))
        if any(w["label"] in ("ask_another_person", "other_application", "external_search") for w in workarounds):
            behaviors.append(_sig("external_workaround", next(w["quote"] for w in workarounds if w["label"] in ("ask_another_person", "other_application", "external_search"))))
        p["user_behaviors"] = behaviors

        p["segment_signals"] = [_sig(label, s) for label, s in _find(SEGMENT_PATTERNS, sents)]
        p["counter_evidence"] = [_sig(label, s) for label, s in _find(COUNTER_PATTERNS, sents)]
        p["expectations"] = [_sig("stated_expectation", s) for s in sents
                             if re.search(r"\b(should|i expected|i thought it would|i wish)\b", s, I)][:2]

        goal = next((s for s in sents if re.search(r"\b(i need|i want|asked (me )?for|wants|needs it|deadline|for my|for our)\b", s, I)), "")
        p["user_goal"] = goal

        journey = []
        if remembered:
            journey.append({"stage": "recall", "observation": "user describes what they remember", "difficulty": False, "quote": remembered[0]["quote"]})
        if queries:
            journey.append({"stage": "express", "observation": f"user tried {len(queries)} quoted search(es)", "difficulty": False, "quote": queries[0]["quote"]})
            bad = next((q for q in queries if q["outcome"] in ("not_found", "wrong_results", "too_many_results")), None)
            if bad:
                journey.append({"stage": "match", "observation": f"search outcome: {bad['outcome']}", "difficulty": True, "quote": bad["quote"]})
        # Two codes land on "match": the query was read differently than meant, or the item never surfaced.
        # F (data or index limitation) is deliberately absent: it is not a stage of the user's journey,
        # and the decomposition reports it on its own row.
        stage_to_journey = {"A_memory_expression": "express", "B_system_understanding": "match", "C_retrieval": "match",
                            "D_result_evaluation": "recognize", "E_refinement": "recover"}
        if p["failure_stage"] in stage_to_journey and p["failure_quote"]:
            journey.append({"stage": stage_to_journey[p["failure_stage"]], "observation": p["failure_reason"], "difficulty": True, "quote": p["failure_quote"]})
        if workarounds:
            journey.append({"stage": "recover", "observation": f"workaround: {workarounds[0]['label']}", "difficulty": False, "quote": workarounds[0]["quote"]})
        if behaviors and p["success_status"] in status_behavior and len(behaviors) > 1 and p["failure_stage"] == "D_result_evaluation":
            journey.append({"stage": "recognize", "observation": f"outcome: {p['success_status']}", "difficulty": p["success_status"] != "found", "quote": behaviors[1]["quote"]})
        p["journey"] = journey

        p["forgotten_info_blocks_retrieval"] = "unclear" if p["forgotten_information"] else "not_applicable"
        p["opportunity_areas"] = map_opportunities(p)
        if remembered and p["forgotten_information"] and goal:
            p["jtbd_signal"] = (f"WHEN I remember \"{remembered[0]['quote']}\" BUT \"{p['forgotten_information'][0]['quote']}\" "
                                f"PLEASE HELP ME retrieve it SO \"{goal}\"")
        p["interpretation"] = "Heuristic extraction: lexical cues only; verify against the source before relying on it."
        p["supplementary_sentiment"] = "negative" if re.search(r"\b(frustrat|annoy|useless|hate|ridiculous|terrible)\w*", low) else "neutral"
        p["confidence"] = 0.5 if p["describes_retrieval_attempt"] else 0.35
        return p, None


def first_person_sentence(sents: list[str]) -> str:
    return next((s for s in sents if re.search(r"\b(i|we)\b", s, I)), sents[0])


def map_opportunities(p: dict) -> list[str]:
    stage = p["failure_stage"]
    labels_r = {r["label"] for r in p["remembered_information"]}
    labels_f = {f["label"] for f in p["forgotten_information"]}
    work = {w["label"] for w in p["workarounds"]}
    outcomes = {q["outcome"] for q in p["queries"]}
    failed = stage not in ("none_observed",) or p["success_status"] in ("not_found", "abandoned", "partially_found", "uncertain")
    if not failed:
        return []
    opps = []
    if stage == "A_memory_expression" or (labels_r & CONTEXTUAL and "exact_keyword_unknown" in labels_f):
        opps.append("context_to_query_translation")
    if stage == "B_system_understanding" or ("natural_language" in {q["query_type"] for q in p["queries"]} and outcomes & {"wrong_results", "too_many_results"}):
        opps.append("multi_clue_combination")
    if stage == "D_result_evaluation":
        opps.append("candidate_recognition")
    if stage == "E_refinement" or (work & {"manual_scrolling", "abandonment"} and p["queries"]):
        opps.append("recovery_after_failed_search")
    if "remembered_time_approximation" in labels_r and "exact_date_unknown" in labels_f and (work & {"date_browsing", "manual_scrolling"} or stage != "none_observed"):
        opps.append("approximate_time_anchoring")
    if p["retrieval_scenario"] in ("document", "receipt", "screenshot", "medical_or_health_image") and (labels_f & {"exact_text_unknown", "exact_object_name_unknown"}):
        opps.append("text_in_image_recall")
    if stage == "F_data_index_limitation":
        opps.append("index_coverage_gaps")
    if stage == "C_retrieval" and p["success_status"] in ("not_found", "abandoned"):
        opps.append("trust_in_search_completeness")
    return opps[:3]
