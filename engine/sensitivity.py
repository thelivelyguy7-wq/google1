"""Phase 2: does a different reasonable analyst reach the same conclusions?

Two outputs:
  sensitivity.md  the target segment and the opportunity ranking recomputed under alternative definitions
  decision_log.md every coding choice that moves a headline number, with its reason and its size

Both are counts over the synthetic corpus. A conclusion that survives every variant is still only a conclusion
about this file.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .analyze import _in, predicates

# frequency label thresholds used by the report (percent of relevant records)
THRESHOLDS = {"as published (30 / 15)": (30, 15), "stricter (40 / 25)": (40, 25), "looser (25 / 10)": (25, 10)}


def _label(pct: float, hi: float, mid: float) -> str:
    return "High" if pct >= hi else ("Medium" if pct >= mid else "Low")


def target_variants(r: pd.DataFrame) -> list[dict]:
    """The target segment (SEG-T) under five alternative definitions."""
    P = predicates(r)
    seg2 = P["segments"]["SEG-2 Recovery-dependent retrievers"]
    seg3 = P["segments"]["SEG-3 Candidate-inspection-dependent retrievers"]
    base = seg2 | seg3
    similar = _in(r["behavior_code"], "B14")
    rows = [
        ("As published: recovery-dependent or candidate-inspection", base, len(r)),
        ("(a) Recovery-dependent only", seg2, len(r)),
        ("(b) Candidate-inspection only", seg3, len(r)),
        ("(c) Exact duplicates removed", base & (r["exact_duplicate_of"] == ""), int((r["exact_duplicate_of"] == "").sum())),
        ("(d) Near-duplicates removed", base & ~r.duplicated("core_signature"), int((~r.duplicated("core_signature")).sum())),
        ("(e) Similar-but-not-exact counted as an exit, not effort", base & ~similar, len(r) - int(similar.sum())),
    ]
    out = []
    for name, mask, denom in rows:
        n = int(mask.sum())
        out.append(dict(variant=name, n=n, denom=denom, pct=round(100 * n / denom, 1), largest=bool(n > denom - n)))
    return out


def ranking_variants(r: pd.DataFrame) -> dict:
    """Opportunity frequency labels under three threshold settings, plus the rank order."""
    P = predicates(r)
    freqs = {k.split()[0]: round(100 * v.mean(), 1) for k, v in P["opps"].items()}
    table = {name: {k: _label(v, hi, mid) for k, v in freqs.items()} for name, (hi, mid) in THRESHOLDS.items()}
    return dict(freqs=freqs, labels=table, order=sorted(freqs, key=lambda k: -freqs[k]), E=len(r))


def write_sensitivity(precomputed=None) -> str:
    from .analyze import compute
    m, df, r = precomputed or compute()
    tv, rv = target_variants(r), ranking_variants(r)
    pub = tv[0]
    holds = [v for v in tv[1:] if v["largest"]]
    unstable = [k for k in rv["order"] if len({rv["labels"][s][k] for s in rv["labels"]}) > 1]
    o = ["# Sensitivity analysis", "",
         "Does the target segment, and the opportunity ranking, survive a different reasonable analyst? "
         "Synthetic corpus only: a variant that agrees still agrees about this file, not about users.", "",
         "## 1. Target segment under alternative definitions", "",
         "| Variant | Records | Of | Share | Still the largest group? |", "|---|---|---|---|---|"]
    for v in tv:
        o.append(f"| {v['variant']} | {v['n']} | {v['denom']} | {v['pct']}% | {'yes' if v['largest'] else 'no'} |")
    o += ["", f"**Reading.** The published definition covers {pub['n']} of {pub['denom']} records ({pub['pct']}%); "
              f"{len(holds)} of {len(tv) - 1} variants still leave it the majority group. Splitting it (a, b) leaves "
              "neither half a majority, which is why the two states are pooled. Duplicate removal barely moves it. "
              "Treating similar-but-not-exact as an exit shrinks it without changing which group is largest.", ""]
    o += ["## 2. Opportunity frequency labels under different thresholds", "",
          "| Opportunity | Share of relevant records | " + " | ".join(rv["labels"]) + " |",
          "|---|---|" + "---|" * len(rv["labels"])]
    for k in rv["order"]:
        o.append(f"| {k} | {rv['freqs'][k]}% | " + " | ".join(rv["labels"][s][k] for s in rv["labels"]) + " |")
    o += ["", "**Reading.** Rank order by frequency is fixed: " + " > ".join(rv["order"]) + ". The High/Medium/Low "
              f"labels are threshold-dependent for {', '.join(unstable) if unstable else 'no area'}"
              f"{'' if not unstable else ', so those labels should never be quoted without the threshold'}. "
              "Frequency is one of seven prioritisation inputs, so a label change does not by itself move the selected "
              "opportunity: O5 leads on frequency under every threshold.", ""]
    o += ["## 3. What this does not test", "",
          "- Whether the lexicon codes each sentence correctly. That needs a second human coder (Phase 2.4).",
          "- Whether the corpus resembles real behaviour. It cannot: the text is template-composed.",
          "- Whether the ranking is right, only whether it is stable under these variants.", ""]
    text = "\n".join(o)
    (config.OUTPUT / "sensitivity.md").write_text(text, encoding="utf-8")
    return text


def _entries(m, r) -> list[tuple]:
    beh, clo = r["behavior_code"], r["closer_code"]
    D, T = m["decomposition"], m["target"]

    def n(mask): return int(mask.sum())

    b08, b14 = n(_in(beh, "B08")), n(_in(beh, "B14"))
    return [
        ("Off-topic records excluded from every denominator", f"{m['stage0']['irrelevant']} records",
         "The `SIM-N…` records describe sharing, storage, battery and editing, with no retrieval angle.",
         "Including them would dilute every share by about 4.4 points and mix two populations."),
        ("Deleted-photo restore treated as possibly relevant, not relevant", f"{m['stage0']['possibly']} records",
         "The intent is to get a photo back, but it is a restore flow carrying no memory or search evidence.",
         "Moving it into the relevant set adds 3 records and no coded behaviour."),
        ("B08 switched to another device or app counted as an exit path", f"{b08} records",
         "The record ends outside Google Photos and never states whether the photo was found.",
         f"Counting it as recovery would move {b08} records from SEG-1 into SEG-2 and raise the target segment to {T['n'] + b08}."),
        ("B14 similar-but-not-exact counted as candidate inspection", f"{b14} records",
         "The user was inspecting candidates and states an uncertain outcome, not a terminal one.",
         f"Counting it as an exit cuts the target segment to {T['n'] - b14}: variant (e) in `sensitivity.md`."),
        ("Unstated outcome coded unknown, never inferred", f"{m['outcome_all']['unknown']} records",
         "The brief forbids inferring outcomes, and most records simply do not say how the search ended.",
         "Any inference would manufacture a success or failure rate this corpus cannot support."),
        ("Opener sentences excluded from behaviour evidence",
         f"{m['stage0']['opener_mix']['affect_frustration'] + m['stage0']['opener_mix']['request_to_vendor']} records with an affect or vendor-request opener",
         "The search is frustrating is sentiment; please make this easier is a solution request. Neither is behaviour.",
         "Using them would make sentiment a discovery method, which the brief rules out."),
        ("D3 left at zero rather than inferred from too many results", f"{D['D3']['indirect']} records carry indirect signs",
         "A broad result set does not state that the product misunderstood the input.",
         "Inferring it would invent a matching problem no record states, and pre-empt the task-test attribution."),
        ("Object classes flagged where the text does not settle them",
         f"{m['object_judgement']['judgement_records']} records across {len(m['object_judgement']['judgement_objects'])} objects",
         "The old meme I saved and our Diwali family photo fit more than one class; a yellow truck fits none.",
         "No finding depends on object class: object is statistically independent of memory and behaviour."),
        ("C04 easier with an exact date or name counted as an expression barrier", f"{n(_in(clo, 'C04'))} records",
         "It is a statement about the input step, contrasting imprecise memory with precise identifiers.",
         f"Dropping it reduces opportunity O1 from {m['opps']['O1 Memory expression']['n']} to {n(r['express_barrier'])} records."),
        ("SEG-2 and SEG-3 pooled into one target segment", f"{T['n']} records",
         "The states are snapshots of one journey; each record shows only the step its sentence names.",
         "Keeping them apart leaves neither a majority: variants (a) and (b) in `sensitivity.md`."),
    ]


def write_decision_log(precomputed=None) -> str:
    from .analyze import compute
    m, df, r = precomputed or compute()
    o = ["# Decision log", "",
         "Coding choices that move a headline number, with the size of the move, so a reader can price the judgement "
         "rather than take it on trust. Synthetic corpus only.", "",
         "| Decision | Records affected | Why | What a different choice would do |", "|---|---|---|---|"]
    for row in _entries(m, r):
        o.append("| " + " | ".join(row) + " |")
    o += ["", "Choices deliberately **not** made: no outcome inferred from sentiment; no population percentage derived "
              "from any count; no opportunity turned into a feature; no numeric priority score.", ""]
    text = "\n".join(o)
    (config.OUTPUT / "decision_log.md").write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    config.configure()
    write_sensitivity()
    write_decision_log()
    print("wrote sensitivity.md and decision_log.md")
