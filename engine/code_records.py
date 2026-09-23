"""Stage 0 + Stage 1: relevance filtering and raw-evidence extraction, one row per record.

Every coded field is derived from a specific verbatim sentence (kept in the `*_text` columns) so any claim can be
traced back to the raw record. Unknown sentences raise, so coverage is 100% by construction.
"""
import re
import pandas as pd

from . import lexicon as L

from . import config

# memory dimensions -> forgotten-information families used in reporting
FORGOTTEN_FAMILY = {
    "date": "time precision", "exact_day": "time precision", "month": "time precision",
    "object_name": "name", "place_name": "name",
    "searchable_keyword": "search keyword", "album": "album / organisation",
    "original_retrieval_path": "how it was originally found", "exact_wording": "exact wording",
}


PHRASE = {
    "story": "the story around it", "visual_appearance": "how it looked", "object": "the object", "people": "who was there",
    "situation": "the situation", "place": "the place in general", "recognition_ability": "that they would recognise it on sight",
    "color": "colours", "setting": "the setting", "approximate_time": "roughly when it was taken", "activity": "what was happening",
    "existence": "that the photo exists",
    "date": "the date", "exact_day": "the exact day", "month": "the month", "object_name": "what the object is called",
    "place_name": "the place name", "searchable_keyword": "a useful search keyword", "album": "which album it is in",
    "original_retrieval_path": "how they originally found it", "exact_wording": "the exact words",
}


def scenario(obj: str, remembered: list[str], forgotten: list[str]) -> str:
    """Neutral, non-interpretive Stage-1B description built only from coded fields."""
    s = f"User is attempting to retrieve {obj.rstrip('.')}"
    if remembered: s += "; states they remember " + ", ".join(PHRASE[x] for x in remembered)
    s += "; states they do not remember " + ", ".join(PHRASE[x] for x in forgotten) if forgotten else "; names no specific information they lack"
    return s + "."


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def code_relevant(sents: list[str]) -> dict:
    """Retrieval-shaped record: optional opener, object, memory, behavior, optional closer (verified, not assumed)."""
    idx = 0
    opener = None
    if idx < len(sents) and sents[idx] in L.OPENERS:
        opener = sents[idx]
        idx += 1
        
    if idx >= len(sents) or sents[idx] not in L.OBJECTS:
        raise KeyError(f"object not in lexicon: {sents[idx] if idx < len(sents) else 'EOF'}")
    obj = sents[idx]
    idx += 1
    
    if idx >= len(sents) or sents[idx] not in L.MEMORY:
        raise KeyError(f"memory sentence not in lexicon: {sents[idx] if idx < len(sents) else 'EOF'}")
    mem = sents[idx]
    idx += 1
    
    if idx >= len(sents) or sents[idx] not in L.BEHAVIOR:
        raise KeyError(f"behavior sentence not in lexicon: {sents[idx] if idx < len(sents) else 'EOF'}")
    beh = sents[idx]
    idx += 1
    
    closer = None
    if idx < len(sents):
        closer = sents[idx]
        if closer not in L.CLOSERS and closer not in L.MEMORY:
            raise KeyError(f"closer not in lexicon: {closer}")
            
    m, b = L.MEMORY[mem], L.BEHAVIOR[beh]
    c = L.CLOSERS.get(closer) if closer else None
    stages = {"RECALL"} | set(b["stages"]) | (set(c["stages"]) if c else set())
    if m["express_barrier"]:
        stages.add("EXPRESS")
    if m["code"] == "M05_recognize_cannot_narrow":
        stages.add("RECOGNIZE")
    signals = list(b["signals"]) + (c["signals"] if c else [])
    return dict(
        opener_text=opener, opener_code=L.OPENERS.get(opener, ""),
        object_text=obj.rstrip("."), object_class=L.OBJECTS[obj],
        object_class_basis="judgement" if obj in L.OBJECT_JUDGEMENT else "stated",
        object_class_alt=L.OBJECT_JUDGEMENT[obj][0] if obj in L.OBJECT_JUDGEMENT else "",
        memory_text=mem, memory_code=m["code"],
        remembered="|".join(m["remembered"]), forgotten="|".join(m["forgotten"]),
        forgotten_family="|".join(sorted({FORGOTTEN_FAMILY[f] for f in m["forgotten"]})),
        express_barrier=m["express_barrier"],
        scenario=scenario(obj, m["remembered"], m["forgotten"]),
        behavior_text=beh, behavior_code=b["code"], retrieval_state=b["state"],
        outcome=b["outcome"] or "unknown", outcome_stated=b["outcome"] is not None,
        closer_text=closer or "", closer_code=c.get("code", "") if c else "", closer_flag=c["flag"] if c else "",
        journey_stages="|".join(s for s in ["RECALL", "EXPRESS", "MATCH", "RECOGNIZE", "RECOVER"] if s in stages),
        severity_signals="|".join(dict.fromkeys(signals)),
        n_severity_signals=len(set(signals)),
    )


def build() -> pd.DataFrame:
    raw = pd.read_csv(config.INPUT)
    rows = []
    from .rule_coder import RuleCoder
    coder = RuleCoder()
    for r in raw.itertuples(index=False):
        c = coder.code(r.text)
        base = dict(record_id=r.record_id, source=r.source, 
                    date_posted=getattr(r, 'date_posted', ''), 
                    author_id=getattr(r, 'author_id', ''),
                    raw_text=r.text)
        if not c:
            rows.append({**base, "relevance": "insufficient_evidence"})
            continue
        if c.relevance != "retrieval_related":
            # get the off topic from the first sentence
            sents = split_sentences(r.text)
            topic = L.OFFTOPIC.get(sents[0], "unknown") if sents else "unknown"
            rows.append({**base, "relevance": c.relevance, "offtopic_topic": topic})
        else:
            stages = {"RECALL"}
            if c.express_barrier: stages.add("EXPRESS")
            if c.retrieval_state == "candidate_inspection":
                stages.add("RECOGNIZE")
                stages.add("MATCH")
            if c.outcome in ["abandoned", "external_workaround", "failed"] or c.retrieval_state in ["exit_path", "recovery_dependent"]:
                stages.add("RECOVER")
            if any(s in c.severity_signals for s in ["reformulation", "browsing", "strategy_switch"]):
                stages.add("RECOVER")
                stages.add("EXPRESS")
                
            object_text = next((q.text for q in c.quotes if q.field == "object"), "").rstrip(".")
            out_dict = dict(
                opener_text="", opener_code="",
                object_text=object_text,
                object_class=c.object_class,
                object_class_basis="judgement" if (object_text + ".") in L.OBJECT_JUDGEMENT else "stated",
                object_class_alt=L.OBJECT_JUDGEMENT[object_text + "."][0] if (object_text + ".") in L.OBJECT_JUDGEMENT else "",
                memory_text="", memory_code="",
                remembered="|".join(c.remembered), forgotten="|".join(c.forgotten),
                forgotten_family="|".join(sorted({FORGOTTEN_FAMILY[f] for f in c.forgotten})) if c.forgotten else "",
                express_barrier=c.express_barrier,
                scenario=scenario(c.object_class, c.remembered, c.forgotten),
                behavior_text="", behavior_code="", retrieval_state=c.retrieval_state,
                outcome=c.outcome, outcome_stated=c.outcome != "unknown",
                closer_text="", closer_code="", closer_flag="",
                journey_stages="|".join(s for s in ["RECALL", "EXPRESS", "MATCH", "RECOGNIZE", "RECOVER"] if s in stages),
                severity_signals="|".join(c.severity_signals),
                n_severity_signals=len(c.severity_signals),
            )
            rows.append({**base, "relevance": "retrieval_related", **out_dict})
    df = pd.DataFrame(rows)

    # duplicates: exact text; near-duplicates = identical object+memory+behavior+closer (opener is only framing)
    df["exact_duplicate_of"] = ""
    first = {}
    for i, t in df["raw_text"].items():
        if t in first: df.at[i, "exact_duplicate_of"] = df.at[first[t], "record_id"]
        else: first[t] = i
    rel = df["relevance"] == "retrieval_related"
    sig = df.loc[rel, ["object_class", "remembered", "forgotten", "retrieval_state", "outcome", "severity_signals"]].astype(str).agg("|".join, axis=1)
    df["core_signature"] = ""
    df.loc[rel, "core_signature"] = sig
    df["near_duplicate_group_size"] = 0
    df.loc[rel, "near_duplicate_group_size"] = sig.map(sig.value_counts())
    df["low_information"] = df["raw_text"].map(lambda t: len(split_sentences(t)) <= 1)
    return df


if __name__ == "__main__":
    config.configure()
    d = build()
    d.to_csv(config.OUTPUT / "coded_records.csv", index=False, encoding="utf-8")
    print(d["relevance"].value_counts().to_string())
