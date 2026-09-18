"""SYNTHETIC / SIMULATED dataset generator.

Produces `per_source` rows for each of 7 source types, rendered in that
platform's style from the content pools in `episodes.py`. Every row is marked
`is_synthetic: true` and uses a `synthetic://` URL (never a real-looking link).

A separate ground-truth file records what the generator *intended* each row to
contain. Analyzers never see it; `evaluate.py` uses it to score extraction.

IMPORTANT: patterns in this data are designed by the generator's weights.
Findings from it validate the pipeline, not user behaviour.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from .episodes import ADVICE, MISATTRIBUTION, NOISE, OPINION, SCENARIOS, SEGMENT_PHRASES, SUCCESS

SOURCES = ["google_play", "app_store", "reddit", "google_photos_community", "social_media", "youtube", "forums"]

MIX = {  # kind -> rows per 120, per source (each sums to 120)
    "google_play": {"attempt": 60, "success": 10, "misattribution": 6, "opinion": 14, "advice": 0, "noise": 30},
    "app_store": {"attempt": 62, "success": 10, "misattribution": 6, "opinion": 14, "advice": 0, "noise": 28},
    "reddit": {"attempt": 80, "success": 8, "misattribution": 8, "opinion": 6, "advice": 10, "noise": 8},
    "google_photos_community": {"attempt": 84, "success": 4, "misattribution": 12, "opinion": 4, "advice": 10, "noise": 6},
    "social_media": {"attempt": 55, "success": 14, "misattribution": 5, "opinion": 20, "advice": 6, "noise": 20},
    "youtube": {"attempt": 45, "success": 12, "misattribution": 5, "opinion": 18, "advice": 25, "noise": 15},
    "forums": {"attempt": 76, "success": 8, "misattribution": 8, "opinion": 8, "advice": 12, "noise": 8},
}

LENGTH = {"google_play": "short", "app_store": "medium", "reddit": "long", "google_photos_community": "long",
          "social_media": "short", "youtube": "short", "forums": "long"}

CLUE_TYPES = ["place", "trip", "event", "occasion", "person", "object", "visual", "time", "text", "context",
              "activity", "relationship", "emotion"]
CLUE_LABEL = {"place": "remembered_place", "trip": "remembered_trip", "event": "remembered_event",
              "occasion": "remembered_occasion", "person": "remembered_person", "object": "remembered_object",
              "visual": "remembered_visual_appearance", "time": "remembered_time_approximation", "text": "remembered_text",
              "context": "remembered_context", "activity": "remembered_activity", "relationship": "remembered_relationship",
              "emotion": "remembered_emotion"}

REM_T = {
    "place": ["It was taken {v}.", "I know it was {v}.", "We were {v} when I took it."],
    "trip": ["It's from {v}.", "This was during {v}."],
    "event": ["It was at {v}.", "It's from {v}."],
    "occasion": ["It was for {v}.", "It was taken on {v}."],
    "person": ["I remember {v} being in it.", "It had {v} in it."],
    "object": ["It's a picture of {v}.", "The photo shows {v}."],
    "visual": ["I remember {v}.", "I can picture {v}.", "All I remember visually is {v}."],
    "time": ["It was {v}.", "Timing wise it was {v}."],
    "text": ["It had {v} on it.", "I remember it showed {v}."],
    "context": ["I remember {v}.", "For context, {v}."],
    "activity": ["It was while {v}."],
    "relationship": ["It's {v}.", "It was {v}."],
    "emotion": ["{V}.", "Honestly {v}."],
}

FORGET_T = {
    "exact_date_unknown": ["I have no idea what year it was.", "I can't remember the date at all.", "I don't remember when exactly.", "Not sure which month or year, honestly."],
    "exact_location_unknown": ["I don't remember the name of the place.", "I can't recall where exactly it was.", "No clue what the place was called."],
    "person_name_unknown": ["I never knew his name.", "I don't remember the person's name."],
    "event_name_unknown": ["I don't even remember what the event was called.", "I can't recall the name of the event."],
    "exact_text_unknown": ["I don't remember the exact words on it.", "I can't recall what it said exactly."],
    "exact_object_name_unknown": ["I don't know what it's called.", "No idea what the thing is actually called."],
    "album_unknown": ["I'm not sure if I ever put it in an album.", "I don't remember which album it went into."],
    "exact_keyword_unknown": ["I don't know what word the app would use for it.", "No idea what to search for really."],
    "metadata_unknown": ["The location data was probably off.", "The photo probably has no proper date on it."],
}

QUERY_T = ['I searched "{q}"', 'Tried "{q}"', 'I typed "{q}" in search', 'Searched for "{q}"']
QUERY_OUT = {
    "not_found": [" and nothing came up.", " and got no results."],
    "wrong_results": [" but it just showed random photos.", " and got a bunch of pictures that had nothing to do with it."],
    "too_many_results": [" and it gave me hundreds of photos.", " and got thousands of results to scroll through."],
    "found": [" and there it was.", " and it popped up near the top."],
}
STAGE_QUERY_OUTCOME = {"A_memory_expression": ["wrong_results", "not_found"], "B_system_understanding": ["wrong_results"],
                       "C_retrieval": ["not_found"], "D_result_evaluation": ["too_many_results"], "E_refinement": ["not_found", "wrong_results"],
                       "F_data_index_limitation": ["not_found"], "none_observed": ["found"]}

FAIL_T = {
    "A_memory_expression": ["I just didn't know how to describe it in a way search would get.", "I know exactly what it looks like but can't put it into search words.",
                            "How do you even search for something like that?"],
    "B_system_understanding": ["It seems like search ignores half of what I type and only matches one word.", 'It took "{kw}" literally and ignored everything else.',
                               "It doesn't understand what I'm describing at all."],
    "C_retrieval": ["The photo is definitely in my library but search never shows it.", "It just doesn't show up in search even though I know it's there."],
    "D_result_evaluation": ["There are so many almost identical shots from that day that I can't tell which one it is.", "All the results look the same as tiny thumbnails.",
                            "I have hundreds of similar shots and can't tell which one it was."],
    "E_refinement": ["After that I had no idea what else to try.", "I ran out of ideas pretty quickly.", "I didn't know what else to try."],
}
FAIL_F_BY_SCENARIO = {
    "document": "The text in the photo doesn't seem to be searchable.", "receipt": "The text on the bill isn't searchable as far as I can tell.",
    "screenshot": "Text inside screenshots doesn't seem to be searchable.", "purchase_related_image": "Text inside screenshots doesn't seem to be searchable.",
    "medical_or_health_image": "The writing on it isn't searchable, it seems.", "location_memory": "The location data was probably off so there's nothing to go on.",
    "video": "Screen recordings don't seem to be indexed at all.", "wedding_memory": "I think it's in a shared album someone else made, not my library.",
    "work_memory": "I think it's on my old phone and never got backed up.",
}
FAIL_F_DEFAULT = ["It came from my old phone and I'm not sure it ever got backed up.", "I think it's in my partner's library, not mine."]

WORK_T = {
    "manual_scrolling": ["Ended up scrolling back through years of photos.", "I scrolled for like 40 minutes."],
    "date_browsing": ["I jumped to roughly that year with the scrollbar and went month by month."],
    "location_browsing": ["I went through the map view hoping to spot it."],
    "album_browsing": ["I checked all my albums one by one."],
    "people_browsing": ["I went through the face group for that person too."],
    "ask_another_person": ["In the end I texted my friend to send it again.", "I asked my sister if she still had it."],
    "other_application": ["Eventually I searched my WhatsApp chats instead.", "I checked my Gmail in case I had sent it to someone."],
    "external_search": ["I even googled how to search Google Photos better."],
    "synonym_search": ['Tried synonyms like "{syn}" too.'],
    "repeated_search": ["I kept retyping different searches."],
    "filters": ["I tried the screenshots category filter as well."],
    "return_later": ["Gave up for the day and tried again the next week."],
    "abandonment": ["Eventually I just gave up.", "I gave up on finding it."],
}
WORK_WEIGHTS_DEFAULT = {"manual_scrolling": 5, "date_browsing": 3, "repeated_search": 3, "synonym_search": 2, "album_browsing": 1,
                        "ask_another_person": 2, "location_browsing": 1, "external_search": 1, "return_later": 1, "people_browsing": 1}
WORK_WEIGHTS_BY_SCENARIO = {
    "document": {"other_application": 5, "manual_scrolling": 3, "repeated_search": 2, "synonym_search": 2},
    "receipt": {"other_application": 5, "manual_scrolling": 3, "repeated_search": 2},
    "screenshot": {"filters": 4, "manual_scrolling": 4, "other_application": 2, "repeated_search": 2},
    "purchase_related_image": {"filters": 3, "manual_scrolling": 3, "external_search": 2, "synonym_search": 2},
    "medical_or_health_image": {"manual_scrolling": 3, "other_application": 3, "synonym_search": 3},
    "travel_memory": {"date_browsing": 5, "location_browsing": 4, "manual_scrolling": 3, "ask_another_person": 2},
    "wedding_memory": {"ask_another_person": 5, "manual_scrolling": 3, "album_browsing": 3},
    "friend_memory": {"ask_another_person": 5, "people_browsing": 3, "date_browsing": 2},
    "family_memory": {"people_browsing": 4, "date_browsing": 4, "manual_scrolling": 3},
    "event_memory": {"date_browsing": 4, "manual_scrolling": 4, "people_browsing": 2},
}

OUTCOME_T = {
    "found": ["Finally found it after {dur}.", "Got it eventually, after {dur}."],
    "not_found": ["Still haven't found it.", "Never found it."],
    "abandoned": [],
    "partially_found": ["I found a similar one but not the exact photo I wanted."],
    "uncertain": ["Found one that might be it, but I'm not sure it's the same one."],
}
DURATIONS = ["about an hour", "two evenings", "half an hour of scrolling", "way too long", "three days"]

OPEN_T = ["I'm trying to find {item}.", "Looking for {item}.", "Does anyone know how to find {item}?", "I've been looking for {item} for days."]
NEED_T = ["I need it because {need}.", "I need it now because {need}."]

PLAY_LEAD = ["Search is useless for old photos.", "Great backup app but search needs work.", "Search is hit or miss.", "", "", "Frustrating search."]
APP_TITLES = ["Search can't find old photos", "Love it but search is frustrating", "Where did my photo go?", "Good backup, weak search",
              "Can't find anything older than a year", "Search needs to be smarter", "Almost perfect"]
SUBREDDITS = ["reddit/r/googlephotos", "reddit/r/GooglePixel", "reddit/r/iphone", "reddit/r/datahoarder", "reddit/r/android"]
REDDIT_TITLES = ["Can't find {item}. Any tips?", "How do you find a photo when you only half remember it?", "Search can't find {item}",
                 "Lost {item} somewhere in 40k photos", "Is there a better way to search for stuff like this?"]
COMMUNITY_TITLES = ["How can I find {item} when I don't remember the date?", "Search not finding a photo I know exists",
                    "Unable to locate {item}", "Help finding an old photo in my library"]
YOUTUBE_VIDEOS = ["10 Google Photos search tricks you didn't know", "Google Photos hidden features (2025)", "How to find old photos fast on Android",
                  "Google Photos vs iCloud Photos: which is better?", "Organise 50,000 photos in one afternoon"]
YOUTUBE_LEADS = ["Tried the tips from this video but ", "Great video. Still, ", "", "", "This didn't help me: "]
SOCIAL_PLATFORMS = ["x", "threads", "facebook", "instagram_comments"]
FORUMS = ["xda_forums", "android_central_forums", "macrumors_forums", "toms_guide_forum"]
FORUM_TITLES = ["Finding a specific old photo in Google Photos", "Google Photos search is failing me", "Tips for locating {item}?", "Search vs scrolling for old memories"]
CLOSERS = ["Any tips?", "Is there a better way to search for stuff like this?", "Am I doing something wrong?", "How do you all deal with this?", ""]
NOISE_OPENERS = ["", "Update: ", "Honestly, ", "Two things. ", "Minor gripe: "]
ADVICE_OPENERS = ["", "What worked for me: ", "Pro tip: ", "From experience, ", "Something that helps: "]


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _weighted(rng: random.Random, weights: dict):
    keys = list(weights)
    return rng.choices(keys, weights=[weights[k] for k in keys])[0]


class Generator:
    def __init__(self, seed: int = 7):
        self.rng = random.Random(seed)
        self.start = datetime(2023, 1, 1)
        self.span_days = (datetime(2026, 8, 31) - self.start).days

    def _date(self) -> str:
        return (self.start + timedelta(days=self.rng.randrange(self.span_days), seconds=self.rng.randrange(86400))).isoformat()

    def _episode(self):
        scen = _weighted(self.rng, {k: v["weight"] for k, v in SCENARIOS.items()})
        return scen, self.rng.choice(SCENARIOS[scen]["episodes"])

    # -- attempt narrative ------------------------------------------------------
    def attempt(self, length: str) -> tuple[list[str], dict]:
        rng = self.rng
        scen, ep = self._episode()
        spec = SCENARIOS[scen]
        n_rem, n_forget, n_q, n_work = {"short": (1, 1, 1, 1), "medium": (2, 1, 2, 1), "long": (3, 2, 3, 2)}[length]
        available = [t for t in CLUE_TYPES if t in ep]
        rem_types = rng.sample(available, min(len(available), rng.randint(max(1, n_rem - 1), n_rem + (length == "long"))))
        forget = rng.sample(ep["forget"], min(len(ep["forget"]), rng.randint(1, n_forget)))
        outcome = _weighted(rng, spec["outcomes"])
        stage = _weighted(rng, spec["failures"])
        if outcome == "found" and rng.random() < 0.45:
            stage = "none_observed"

        sents: list[str] = []
        seg = None
        if length != "short" and rng.random() < 0.45:
            seg = rng.choice(list(SEGMENT_PHRASES))
            if scen == "screenshot" and rng.random() < 0.5:
                seg = "screenshot_heavy"
            sents.append(_cap(rng.choice(SEGMENT_PHRASES[seg])) + ".")
        sents.append(rng.choice(OPEN_T).format(item=ep["item"]))
        if rng.random() < (0.4 if length == "short" else 0.75):
            sents.append(rng.choice(NEED_T).format(need=ep["need"]))
        for t in rem_types:
            tpl = rng.choice(REM_T[t])
            sents.append(tpl.format(v=ep[t], V=_cap(ep[t])))
        for f in forget:
            sents.append(rng.choice(FORGET_T[f]))

        q_kinds = rng.sample(["kw", "nl", "meta"], min(3, rng.randint(1, n_q)))
        queries = []
        for i, qk in enumerate(q_kinds):
            last = i == len(q_kinds) - 1
            if stage == "none_observed" and last:
                qo = "found"
            else:
                qo = rng.choice(STAGE_QUERY_OUTCOME.get(stage, ["not_found"]))
            qtype = {"kw": "keyword", "nl": "natural_language", "meta": "metadata"}[qk]
            sents.append(rng.choice(QUERY_T).format(q=ep[qk]) + rng.choice(QUERY_OUT[qo]))
            queries.append({"type": qtype, "text": ep[qk], "outcome": qo})

        if stage == "F_data_index_limitation":
            sents.append(FAIL_F_BY_SCENARIO.get(scen) or rng.choice(FAIL_F_DEFAULT))
        elif stage != "none_observed":
            sents.append(rng.choice(FAIL_T[stage]).format(kw=ep["kw"]))

        weights = dict(WORK_WEIGHTS_BY_SCENARIO.get(scen, WORK_WEIGHTS_DEFAULT))
        works = []
        for _ in range(rng.randint(0 if length == "short" else 1, n_work)):
            w = _weighted(rng, weights)
            weights.pop(w, None)
            works.append(w)
            if not weights:
                break
        if outcome == "abandoned":
            works.append("abandonment")
        for w in works:
            sents.append(rng.choice(WORK_T[w]).format(syn=ep["syn"]))
        if OUTCOME_T[outcome]:
            sents.append(rng.choice(OUTCOME_T[outcome]).format(dur=rng.choice(DURATIONS)))

        truth = {
            "kind": "attempt", "relevant": True, "attempt": True, "scenario": scen, "episode_item": ep["item"],
            "remembered": sorted({CLUE_LABEL[t] for t in rem_types}), "forgotten": sorted(set(forget)),
            "queries": queries, "failure_stage": stage, "workarounds": sorted(set(works)), "outcome": outcome,
            "segments": [seg] if seg else [], "counter": [],
        }
        return sents, truth

    def success(self) -> tuple[list[str], dict]:
        scen, ep = self._episode()
        visual = ep.get("visual", ep["kw"])
        text = self.rng.choice(SUCCESS).format(item=ep["item"], nl=ep["nl"], kw=ep["kw"], visual_any=visual)
        return [text], {"kind": "success", "relevant": True, "attempt": True, "scenario": scen, "remembered": [], "forgotten": [],
                        "queries": [], "failure_stage": "none_observed", "workarounds": [], "outcome": "found", "segments": [],
                        "counter": ["vague_search_succeeded"]}

    def misattribution(self) -> tuple[list[str], dict]:
        scen, ep = self._episode()
        text = self.rng.choice(MISATTRIBUTION).format(item=ep["item"])
        return [text], {"kind": "misattribution", "relevant": True, "attempt": True, "scenario": scen, "remembered": [], "forgotten": [],
                        "queries": [], "failure_stage": "F_data_index_limitation", "workarounds": [], "outcome": "not_found",
                        "segments": [], "counter": ["failure_not_search_related"]}

    def opinion(self) -> tuple[list[str], dict]:
        _, ep = self._episode()
        text = self.rng.choice(OPINION).format(nl=ep["nl"])
        return [text], {"kind": "opinion", "relevant": True, "attempt": False, "scenario": None, "remembered": [], "forgotten": [],
                        "queries": [], "failure_stage": None, "workarounds": [], "outcome": None, "segments": [], "counter": []}

    def advice(self) -> tuple[list[str], dict]:
        text = self.rng.choice(ADVICE_OPENERS) + self.rng.choice(ADVICE)
        return [text], {"kind": "advice", "relevant": True, "attempt": False, "scenario": None, "remembered": [], "forgotten": [],
                        "queries": [], "failure_stage": None, "workarounds": [], "outcome": None, "segments": [], "counter": []}

    def noise(self) -> tuple[list[str], dict]:
        parts = self.rng.sample(NOISE, self.rng.choice([1, 2]))
        return [self.rng.choice(NOISE_OPENERS) + parts[0]] + parts[1:], {"kind": "noise", "relevant": False, "attempt": False}

    # -- platform rendering ---------------------------------------------------------
    def render(self, source: str, idx: int, kind: str) -> tuple[dict, dict]:
        rng = self.rng
        length = LENGTH[source]
        sents, truth = getattr(self, kind)(length) if kind == "attempt" else getattr(self, kind)()
        item = truth.get("episode_item") or "an old photo"
        body = " ".join(s for s in sents if s)
        row = {"source": source, "source_id": f"syn-{source[:3]}-{idx:04d}", "created_at": self._date(),
               "author": f"synthetic_user_{rng.randrange(100000)}", "is_synthetic": True,
               "source_url": f"synthetic://{source}/syn-{source[:3]}-{idx:04d}", "title": None, "thread_context": None,
               "replies": [], "engagement": {}}
        failed = truth.get("outcome") not in (None, "found")
        if source == "google_play":
            lead = rng.choice(PLAY_LEAD) if kind in ("attempt", "opinion") else ""
            body = f"{lead} {body}".strip()
            row.update(platform="android", engagement={"rating": rng.randint(1, 3) if failed or kind == "opinion" else rng.randint(3, 5),
                                                      "thumbs_up": rng.randrange(0, 300), "app_version": f"7.{rng.randint(1, 30)}.0"})
        elif source == "app_store":
            row.update(platform="ios", title=rng.choice(APP_TITLES),
                       engagement={"rating": rng.randint(1, 3) if failed or kind == "opinion" else rng.randint(3, 5)})
        elif source == "reddit":
            closer = rng.choice(CLOSERS) if kind == "attempt" else ""
            body = f"{body} {closer}".strip()
            row.update(platform=rng.choice(SUBREDDITS),
                       title=rng.choice(REDDIT_TITLES).format(item=item) if kind != "noise" else rng.choice(["Rant", "Anyone else?", "Quick question"]),
                       replies=rng.sample(ADVICE, rng.randint(0, 3)), engagement={"score": rng.randrange(1, 900), "num_comments": rng.randrange(0, 120)})
        elif source == "google_photos_community":
            device = rng.choice(["", " Device: Pixel 8, Android 15.", " Device: iPhone 14, iOS 18.", " Using photos.google.com on Windows."])
            row.update(platform="google_photos_help_community",
                       title=rng.choice(COMMUNITY_TITLES).format(item=item) if kind != "noise" else "General question",
                       text_suffix=device, thread_context="Google Photos Help Community > Search & browse",
                       replies=[f"Product Expert: {a}" for a in rng.sample(ADVICE, rng.randint(1, 2))],
                       engagement={"same_question": rng.randrange(0, 80), "recommended_answer": rng.random() < 0.3})
            body = body + device
            row.pop("text_suffix")
        elif source == "social_media":
            tag = rng.choice(["", " #GooglePhotos", " @googlephotos", " #help", ""])
            body = body + tag
            row.update(platform=rng.choice(SOCIAL_PLATFORMS), engagement={"likes": rng.randrange(0, 2000), "reposts": rng.randrange(0, 200)})
        elif source == "youtube":
            lead = rng.choice(YOUTUBE_LEADS) if kind == "attempt" else ""
            if lead:
                body = lead + body[:1].lower() + body[1:]
            row.update(platform="youtube_comments", thread_context=rng.choice(YOUTUBE_VIDEOS), engagement={"likes": rng.randrange(0, 1500)})
        elif source == "forums":
            closer = rng.choice(CLOSERS) if kind == "attempt" else ""
            body = f"{body} {closer}".strip()
            row.update(platform=rng.choice(FORUMS), title=rng.choice(FORUM_TITLES).format(item=item),
                       thread_context="Apps & software", engagement={"views": rng.randrange(50, 20000), "replies": rng.randrange(0, 40)})
        if source in ("social_media", "google_play", "youtube") and rng.random() < 0.2:
            body = body.lower()
        row["text"] = body
        row["record_id"] = f"{source}:{row['source_id']}"
        truth.pop("episode_item", None)
        return row, {"record_id": row["record_id"], "source": source, **truth}

    def generate(self, per_source: int = 120) -> tuple[list[dict], list[dict]]:
        rows, truths = [], []
        for source in SOURCES:
            mix = MIX[source]
            scale = per_source / 120
            kinds = [k for k, n in mix.items() for _ in range(round(n * scale))]
            kinds = (kinds + ["attempt"] * per_source)[:per_source]
            self.rng.shuffle(kinds)
            for i, kind in enumerate(kinds):
                row, truth = self.render(source, i, kind)
                rows.append(row)
                truths.append(truth)
        return rows, truths


README = """# SYNTHETIC / SIMULATED DATA

Every row in this folder was generated by `discovery_engine/synthetic/generate.py`.
No row is a real user statement, and every `source_url` uses the `synthetic://` scheme.

- `<source>.jsonl`: 120 rows per source type (Play Store, App Store, Reddit, Google Photos
  Community, social media, YouTube comments, forums). Every row has `is_synthetic: true`.
- `synthetic_all.jsonl` / `synthetic_all.csv`: all sources combined (the format the engine ingests).
- `synthetic_dataset_flat.csv`: one flat row per record for inspecting in a spreadsheet or
  Parquet Visualizer. Engagement is split into `engagement_*` columns, replies are joined with ` || `,
  and the intended labels are added as `truth_*` columns. Do not ingest this file: the `truth_*`
  columns would leak the answer key.
- `ground_truth.jsonl`: what the generator intended each row to contain. It is NOT for
  analysis; `evaluate` uses it to score analyzer accuracy.

The frequencies and scenario-to-failure links in this data come from the generator's
weights in `episodes.py`. Use this data to test the pipeline, never as evidence about users.
"""


def write_flat_csv(out_dir: str | Path) -> Path:
    """One flat row per record for spreadsheet / Parquet Visualizer inspection.

    Nested fields are flattened (engagement_* columns, replies joined with ' || ').
    Ground-truth columns are prefixed `truth_`; they describe generator intent and
    must never be fed to an analyzer.
    """
    import pandas as pd
    out = Path(out_dir)
    rows = [json.loads(l) for l in (out / "synthetic_all.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    truth = {t["record_id"]: t for t in map(json.loads, (out / "ground_truth.jsonl").read_text(encoding="utf-8").splitlines())}
    flat = []
    for r in rows:
        t = truth.get(r["record_id"], {})
        row = {
            "record_id": r["record_id"], "source": r["source"], "platform": r["platform"], "source_id": r["source_id"],
            "created_at": r["created_at"], "is_synthetic": r["is_synthetic"], "source_url": r["source_url"],
            "title": r.get("title") or "", "text": r["text"], "text_chars": len(r["text"]),
            "thread_context": r.get("thread_context") or "",
            "reply_count": len(r.get("replies") or []), "replies": " || ".join(r.get("replies") or []),
        }
        for k in ("rating", "thumbs_up", "app_version", "score", "num_comments", "same_question", "recommended_answer",
                  "likes", "reposts", "views", "replies"):
            v = (r.get("engagement") or {}).get(k)
            row[f"engagement_{k}"] = "" if v is None else v
        row.update({
            "truth_kind": t.get("kind", ""), "truth_relevant": t.get("relevant", ""), "truth_attempt": t.get("attempt", ""),
            "truth_scenario": t.get("scenario") or "", "truth_outcome": t.get("outcome") or "",
            "truth_failure_stage": t.get("failure_stage") or "",
            "truth_remembered": "; ".join(t.get("remembered", [])), "truth_forgotten": "; ".join(t.get("forgotten", [])),
            "truth_query_types": "; ".join(q["type"] for q in t.get("queries", [])),
            "truth_queries": "; ".join(q["text"] for q in t.get("queries", [])),
            "truth_query_outcomes": "; ".join(q["outcome"] for q in t.get("queries", [])),
            "truth_workarounds": "; ".join(t.get("workarounds", [])), "truth_segments": "; ".join(t.get("segments", [])),
            "truth_counter_evidence": "; ".join(t.get("counter", [])),
        })
        flat.append(row)
    path = out / "synthetic_dataset_flat.csv"
    pd.DataFrame(flat).to_csv(path, index=False, encoding="utf-8")
    return path


def write_dataset(out_dir: str | Path, per_source: int = 120, seed: int = 7) -> dict:
    import pandas as pd
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows, truths = Generator(seed).generate(per_source)
    for source in SOURCES:
        with open(out / f"{source}.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                if r["source"] == source:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / "synthetic_all.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    df = pd.DataFrame(rows)
    df["replies"] = df["replies"].map(json.dumps)
    df["engagement"] = df["engagement"].map(json.dumps)
    df.to_csv(out / "synthetic_all.csv", index=False)
    with open(out / "ground_truth.jsonl", "w", encoding="utf-8") as fh:
        for t in truths:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")
    (out / "README.md").write_text(README, encoding="utf-8")
    write_flat_csv(out)
    from collections import Counter
    return {"rows": len(rows), "by_source": dict(Counter(r["source"] for r in rows)),
            "by_kind": dict(Counter(t["kind"] for t in truths)), "out_dir": str(out)}
