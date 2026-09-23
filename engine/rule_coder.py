import re
from typing import Optional
from .coders import Coder, Coding, Quote, Relevance, ObjectClass, Remembered, Forgotten, State, Outcome, Signal
from . import lexicon as L

NEW_SENTENCES = {
    "After that I gave up.": dict(outcome="abandoned", state="exit_path", signals=["abandonment"]),
    "I only found near-duplicates, never the exact photo.": dict(outcome="similar_uncertain", state="candidate_inspection", signals=["uncertainty"]),
    "In the end I never found it.": dict(outcome="failed", state="exit_path", signals=["failure"]),
    "A different search term finally worked.": dict(outcome="found_after_reformulation", state="recovery_dependent", signals=["reformulation"]),
    "I picked one that looked close, but I am still not sure it was the right one.": dict(outcome="similar_uncertain", state="candidate_inspection", signals=["uncertainty"]),
    "Rephrasing the search is what finally brought it up.": dict(outcome="found_after_reformulation", state="recovery_dependent", signals=["reformulation"]),
    "Browsing around that period is how I found it.": dict(outcome="found_after_browsing", state="recovery_dependent", signals=["browsing"]),
    "I stopped searching because it was taking too long.": dict(outcome="abandoned", state="exit_path", signals=["abandonment"]),
    "It came up in the first few results.": dict(outcome="found_quickly", state="first_attempt", signals=[]),
    "I ended up finding it in an old WhatsApp chat instead.": dict(outcome="external_workaround", state="exit_path", signals=["external_workaround"]),
    "Nothing I tried brought it up.": dict(outcome="failed", state="exit_path", signals=["failure"]),
    "It took a long time, but I found it.": dict(outcome="found_with_effort", state="recovery_dependent", signals=["repeated_attempts"]),
    "I got there eventually, after a lot of effort.": dict(outcome="found_with_effort", state="recovery_dependent", signals=["repeated_attempts"]),
    "I finally spotted it while scrolling.": dict(outcome="found_after_browsing", state="recovery_dependent", signals=["browsing"]),
    "In the end a friend sent it to me again.": dict(outcome="external_workaround", state="exit_path", signals=["external_workaround"]),
    "I found it within a minute.": dict(outcome="found_quickly", state="first_attempt", signals=[])
}

class RuleCoder:
    name = "rule"

    def code(self, text: str) -> Optional[Coding]:
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
        if not parts: return None

        # Check offtopic
        if len(parts) == 1 and parts[0] in L.OFFTOPIC:
            topic = L.OFFTOPIC[parts[0]]
            return Coding(relevance="possibly_relevant" if topic in L.POSSIBLY_RELEVANT_TOPICS else "not_retrieval_related")

        c = Coding(relevance="retrieval_related")
        
        for p in parts:
            if p in L.OBJECTS:
                c.object_class = L.OBJECTS[p]
                c.quotes.append(Quote(field="object", text=p))
            elif p in L.MEMORY:
                m = L.MEMORY[p]
                c.remembered.extend(m["remembered"])
                c.forgotten.extend(m["forgotten"])
                if m["express_barrier"]: c.express_barrier = True
                c.quotes.append(Quote(field="remembered", text=p))
                if m["forgotten"]:
                    c.quotes.append(Quote(field="forgotten", text=p))
            elif p in L.BEHAVIOR:
                b = L.BEHAVIOR[p]
                if b["state"] and b["state"] != "unknown": c.retrieval_state = b["state"]
                if b["outcome"] and b["outcome"] != "unknown": c.outcome = b["outcome"]
                c.severity_signals.extend(b["signals"])
                c.quotes.append(Quote(field="behavior", text=p))
                if b["outcome"]:
                    c.quotes.append(Quote(field="outcome", text=p))
            elif p in NEW_SENTENCES:
                n = NEW_SENTENCES[p]
                if n["state"]: c.retrieval_state = n["state"]
                if n["outcome"]: c.outcome = n["outcome"]
                c.severity_signals.extend(n["signals"])
                c.quotes.append(Quote(field="behavior", text=p))
                c.quotes.append(Quote(field="outcome", text=p))
            elif p in L.CLOSERS:
                cl = L.CLOSERS[p]
                c.severity_signals.extend(cl["signals"])
            elif p in L.OPENERS:
                pass

        if not c.quotes:
            return None

        # Deduplicate list fields
        c.remembered = list(dict.fromkeys(c.remembered))
        c.forgotten = list(dict.fromkeys(c.forgotten))
        c.severity_signals = list(dict.fromkeys(c.severity_signals))
        return c
