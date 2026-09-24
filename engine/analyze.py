"""Stages 2-8: journey mapping, needs, segments, opportunities, target, impact sizing.

All counts are over dataset records ("X of Y relevant records"), never population rates.
Needs / segments / opportunities are non-exclusive predicates over coded fields, except `retrieval_state`, which is
mutually exclusive by construction (one behavior sentence per record).
"""
import json
import math

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from . import config
from .code_records import FORGOTTEN_FAMILY, build
from . import decomposition as DC
from . import lexicon as L

STAGES = ["REMEMBER", "EXPRESS", "MATCH", "RECOGNIZE", "RECOVER"]

# Every count dict below is filled out over its full vocabulary, so a corpus that happens not to contain a code still
# yields a zero rather than a missing key. The report and the web app index these dicts by code.
SIGNAL_VOCAB = ["strategy_switch", "browsing", "large_candidate_set", "uncertainty", "external_workaround",
                "candidate_inspection", "reformulation", "repeated_attempts", "abandonment", "failure"]
BEHAVIOR_LABELS = {v["code"].split("_", 1)[0]: v["code"].split("_", 1)[1].replace("_", " ") for v in L.BEHAVIOR.values()}


def _fill(counts: dict, vocab) -> dict:
    """Observed counts first (descending), then every unobserved vocabulary entry at zero."""
    out = {k: int(v) for k, v in counts.items()}
    for k in vocab:
        out.setdefault(k, 0)
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def _in(series, *codes):
    return series.str.startswith(tuple(codes))


def predicates(r: pd.DataFrame) -> dict:
    """name -> boolean mask over relevant records. Code prefixes (M03, B05 ...) refer to lexicon codes."""
    mem, beh, clo = r["memory_code"], r["behavior_code"], r["closer_code"]
    info_items = {"the photo of a prescription", "the medicine box I photographed", "the picture I sent to my doctor"}
    needs = {
        "N1 Retrieve a photo when the date is only approximately known": _in(mem, "M03", "M07", "M10"),
        "N2 Retrieve a photo remembered by appearance/gist but lacking a name, keyword or wording": _in(mem, "M02", "M06", "M11", "M12"),
        "N3 Retrieve a photo remembered by story, people and activity but lacking an organising handle (album)": _in(mem, "M01", "M08"),
        "N4 Retrieve a place-based memory without the place name": _in(mem, "M04"),
        "N5 Re-find a photo known to exist after losing the original path to it": _in(mem, "M09"),
        "N6 Recognise/verify the right photo among plausible candidates": (r["retrieval_state"] == "candidate_inspection") | _in(clo, "C08"),
        "N7 Reach a photo the user says they would recognise but cannot narrow towards": _in(mem, "M05") | _in(clo, "C01"),
        "N8 Recover after a first attempt did not resolve": r["retrieval_state"].isin(["recovery_dependent", "exit_path"]),
        "N9 Retrieve an information-bearing image (document, screenshot, prescription)":
            (r["object_class"] == "document_screenshot") | r["object_text"].isin(info_items),
    }
    segments = {
        "SEG-1 Exit-path retrievers": r["retrieval_state"] == "exit_path",
        "SEG-2 Recovery-dependent retrievers": r["retrieval_state"] == "recovery_dependent",
        "SEG-3 Candidate-inspection-dependent retrievers": r["retrieval_state"] == "candidate_inspection",
        "SEG-4 First-attempt-stage retrievers": r["retrieval_state"] == "first_attempt",
    }
    segments["SEG-T Effortful-path retrievers (SEG-2 or SEG-3)"] = segments["SEG-2 Recovery-dependent retrievers"] | segments["SEG-3 Candidate-inspection-dependent retrievers"]
    opps = {
        "O1 Memory expression": r["express_barrier"] | _in(clo, "C04"),
        "O2 Approximate-time narrowing": _in(mem, "M03", "M07", "M10") | _in(beh, "B03", "B16"),
        "O3 Candidate recognition / verification": _in(beh, "B04", "B11", "B13", "B14", "B16") | _in(clo, "C08"),
        "O4 Contextual matching (candidate-set precision)": _in(beh, "B03") | _in(clo, "C08"),
        "O5 Retrieval recovery": _in(beh, "B05", "B07", "B08", "B09", "B10", "B12", "B15", "B17", "B18"),
        "O6 Retrieval-path memory (album / how it was found)": _in(mem, "M08", "M09"),
        "O7 Corpus / access boundary (indirect evidence)": _in(beh, "B08", "B10"),
        "O8 Information discovery (knowing what can narrow a search)": _in(mem, "M05"),
    }
    return dict(needs=needs, segments=segments, opps=opps)


def cramers_v(a, b):
    ct = pd.crosstab(a, b)
    chi2, p, dof, _ = chi2_contingency(ct)
    n = ct.values.sum()
    v = math.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    return dict(chi2=round(chi2, 1), dof=int(dof), p=round(float(p), 3), cramers_v=round(v, 3))


def summarize(mask, r, ids=3):
    sub = r[mask]
    return dict(n=int(mask.sum()), of=len(r), pct=round(100 * mask.mean(), 1),
                example_ids=sub["record_id"].sort_values().head(ids).tolist())


def profile(mask, r):
    sub = r[mask]
    n = len(sub)
    out = {k: int((sub["outcome"] == k).sum()) for k in
           ["found_with_effort", "similar_uncertain", "failed", "abandoned", "external_workaround", "unknown"]}
    return dict(
        n=n, outcomes=out,
        express_barrier=int(sub["express_barrier"].sum()),
        recognition_retained=int((_in(sub["memory_code"], "M05") | _in(sub["closer_code"], "C01")).sum()),
        cannot_confirm=int(_in(sub["closer_code"], "C08").sum()),
        knows_exists=int((_in(sub["closer_code"], "C06") | _in(sub["memory_code"], "M09")).sum()),
        with_severity_signal=int((sub["n_severity_signals"] >= 1).sum()),
        with_2plus_signals=int((sub["n_severity_signals"] >= 2).sum()),
        top_behaviors=[(k.split("_", 1)[1].replace("_", " ") if "_" in k else k, int(v)) for k, v in sub["behavior_code"].value_counts().head(3).items() if k],
        signal_counts=sub["severity_signals"].str.split("|").explode().replace("", np.nan).dropna().value_counts().to_dict(),
        stage_counts={st: int(sub["journey_stages"].str.contains(st).sum()) for st in STAGES},
        remembered_mix=sub["remembered"].replace("", "don't explicitly state").str.split("|").explode().value_counts().to_dict(),
        large_library_stated=int(_in(sub["closer_code"], "C02").sum()),
        found_quickly=0,
        object_mix=sub["object_class"].value_counts().to_dict(),
        forgotten_mix=sub["forgotten_family"].replace("", "don't explicitly state").str.split("|").explode().value_counts().to_dict(),
    )



BEHAVIOR_GROUPS = {
    "First-attempt input strategies": ["B01", "B02", "B06"],
    "Date-based narrowing": ["B03", "B16"],
    "Reformulation (different or several related words)": ["B05", "B17"],
    "Switching strategy (terms/albums, person then browse, keywords then scroll)": ["B07", "B09", "B18"],
    "Manual inspection and browsing": ["B04", "B11", "B13"],
    "Outcome stated in the same sentence (similar-not-exact, several attempts)": ["B14", "B15"],
    "Exit (could not find, gave up and asked someone, other app/device)": ["B08", "B10", "B12"],
}


def extras(r: pd.DataFrame, P: dict, m: dict) -> dict:
    """Behaviour/outcome distributions, decomposition, stage questions and the full evidence index."""
    E = len(r)
    out = {}
    beh = r["behavior_code"]

    # ---- how users searched when memory was incomplete (Stage 1E / brief question 4)
    groups = {}
    for name, codes in BEHAVIOR_GROUPS.items():
        mask = _in(beh, *codes)
        groups[name] = dict(n=int(mask.sum()), of=E, pct=round(100 * mask.mean(), 1),
                            members={c: int(_in(beh, c).sum()) for c in codes},
                            example_ids=r.loc[mask, "record_id"].sort_values().head(3).tolist())
    out["behavior_groups"] = groups
    out["behavior_labels"] = BEHAVIOR_LABELS

    # ---- overall outcome distribution, every category in the brief shown (zeros included)
    cats = ["found_quickly", "found_with_effort", "found_after_reformulation", "found_after_browsing",
            "similar_uncertain", "failed", "abandoned", "external_workaround", "unknown"]
    out["outcome_all"] = {c: int((r["outcome"] == c).sum()) for c in cats}

    # ---- object-class judgement calls (brief: do not force a category)
    out["object_judgement"] = dict(
        judgement_records=int((r["object_class_basis"] == "judgement").sum()),
        stated_records=int((r["object_class_basis"] == "stated").sum()),
        judgement_objects=sorted(r.loc[r["object_class_basis"] == "judgement", "object_text"].unique().tolist()),
        n_objects=int(r["object_text"].nunique()),
    )

    # ---- decomposition
    out["decomposition"] = DC.summarize(r)

    # ---- Stage 2: the five stage questions answered from the data
    def n(mask): return int(mask.sum())
    out["stage_questions"] = {
        "REMEMBER": dict(question="What does the user remember?",
                       top_remembered=list(m["stage1"]["remembered"].items())[:5],
                       top_lacking=list(m["stage1"]["forgotten_family"].items())[:5]),
        "EXPRESS": dict(question="How does the user convert that memory into a search or action?",
                        first_attempt=n(_in(beh, "B01", "B02", "B06")), date=n(_in(beh, "B03", "B16")),
                        reformulation=n(_in(beh, "B05", "B17")), person_then_browse=n(_in(beh, "B09")),
                        keywords_then_scroll=n(_in(beh, "B18")),
                        barrier=n(P["opps"]["O1 Memory expression"])),
        "MATCH": dict(question="Does the product appear to surface plausible candidates?",
                      candidates_surfaced=out["decomposition"]["D3"]["intact"],
                      too_many_results=n(_in(beh, "B03")),
                      product_misread_stated=out["decomposition"]["D3"]["breakdown"]),
        "RECOGNIZE": dict(question="Can the user identify the intended photo among candidates?",
                          can_on_sight=out["decomposition"]["D4"]["intact"],
                          cannot_tell=out["decomposition"]["D4"]["breakdown"],
                          heavy_inspection=out["decomposition"]["D4"]["effort"]),
        "RECOVER": dict(question="What does the user do after the first attempt does not work?",
                        effort=out["decomposition"]["D5"]["effort"], success_after_effort=out["decomposition"]["D5"]["intact"],
                        exits=out["decomposition"]["D5"]["breakdown"]),
    }

    # ---- evidence index: every named group -> every record id behind it (rule 15)
    idx = {}
    for k, v in P["needs"].items(): idx[f"need:{k.split()[0]}"] = v
    for k, v in P["segments"].items(): idx[f"seg:{k.split()[0]}"] = v
    for k, v in P["opps"].items(): idx[f"opp:{k.split()[0]}"] = v
    for node, pol in DC.node_masks(r).items():
        for pk, v in pol.items(): idx[f"node:{node}:{pk}"] = v
    exit_mask = P["segments"]["SEG-1 Exit-path retrievers"]
    claims = {
        "K01": pd.Series(True, index=r.index),
        "K02": r["forgotten"] != "",
        "K03": _in(r["memory_code"], "M03", "M07", "M10"),
        "K04": r["express_barrier"],
        "K05": r["n_severity_signals"] >= 1,
        "K06": P["opps"]["O5 Retrieval recovery"],
        "K07": _in(beh, "B14") | _in(r["closer_code"], "C08"),
        "K08": _in(r["memory_code"], "M05") | _in(r["closer_code"], "C01"),
        "K09": exit_mask,
        "K10": _in(beh, "B15"),
        "K11": P["opps"]["O1 Memory expression"] & exit_mask,
        "K12": P["segments"]["SEG-T Effortful-path retrievers (SEG-2 or SEG-3)"],
        "K13": _in(beh, "B03", "B16") | _in(r["memory_code"], "M07", "M10"),
        "K14": r["outcome"] == "unknown",
    }
    for k, v in claims.items(): idx[f"claim:{k}"] = v
    hyp = {
        "H1": r["express_barrier"],
        "H2": _in(beh, "B04", "B14") | _in(r["closer_code"], "C08"),
        "H3": _in(beh, "B03", "B16") | _in(r["memory_code"], "M07", "M10"),
        "H4": P["opps"]["O5 Retrieval recovery"],
        "H5": _in(beh, "B08", "B10"),
        "H6": r["object_class"].isin(["document_screenshot", "medical"]),
        "H7": pd.Series(True, index=r.index),
    }
    for k, v in hyp.items(): idx[f"hyp:{k}"] = v
    out["evidence_index"] = {k: r.loc[v, "record_id"].sort_values().tolist() for k, v in idx.items()}
    out["evidence_index_n"] = {k: len(v) for k, v in out["evidence_index"].items()}
    return out


def compute() -> dict:
    df = build()
    r = df[df["relevance"] == "retrieval_related"].copy().reset_index(drop=True)
    P = predicates(r)
    m = {}

    # ---- Stage 0
    dup_all = int((df["exact_duplicate_of"] != "").sum())
    dup_rel = int((r["exact_duplicate_of"] != "").sum())
    m["stage0"] = dict(
        total=len(df), relevant=len(r), possibly=int((df.relevance == "possibly_relevant").sum()),
        irrelevant=int((df.relevance == "not_retrieval_related").sum()), insufficient=0, ambiguous=0,
        exact_dup_all=dup_all, exact_dup_relevant=dup_rel,
        near_dup_records=int((r["near_duplicate_group_size"] > 1).sum()),
        near_dup_extra=int(sum(g - 1 for g in r.groupby("core_signature").size() if g > 1)),
        low_info=int(df["low_information"].sum()),
        offtopic_topics=df.loc[df.relevance != "retrieval_related", "offtopic_topic"].value_counts().to_dict(),
        n_unique_sentences=90,
        opener_mix=_fill(r["opener_code"].value_counts().to_dict(), set(L.OPENERS.values())),
        repeated_authors=int(df["author_id"].duplicated(keep=False).sum()),
        source_mix=r["source"].value_counts().to_dict(),
        date_min=df.date_posted.min(), date_max=df.date_posted.max(),
    )

    # ---- Stage 1 distributions
    rem = r["remembered"].str.split("|").explode().value_counts()
    fgt = r["forgotten"].replace("", "none_named").str.split("|").explode().value_counts()
    m["stage1"] = dict(
        object_class=_fill(r["object_class"].value_counts().to_dict(), L.OBJECT_CLASS_LABEL),
        remembered=rem.to_dict(), forgotten=fgt.to_dict(),
        forgotten_family=_fill(r["forgotten_family"].replace("", "don't explicitly state").str.split("|").explode().value_counts().to_dict(),
                              set(FORGOTTEN_FAMILY.values()) | {"don't explicitly state"}),
        memory_code=_fill(r["memory_code"].value_counts().to_dict(), [v["code"] for v in L.MEMORY.values()]),
        behavior_code=_fill(r["behavior_code"].value_counts().to_dict(), [v["code"] for v in L.BEHAVIOR.values()]),
        closer_code=_fill(r.loc[r.closer_code != "", "closer_code"].value_counts().to_dict(), [v["code"] for v in L.CLOSERS.values()]),
        no_closer=int((r.closer_code == "").sum()),
        retrieval_state=r["retrieval_state"].value_counts().to_dict(),
        outcome=r["outcome"].value_counts().to_dict(),
        state_x_outcome=pd.crosstab(r["retrieval_state"], r["outcome"]).to_dict("index"),
        signals=_fill(r["severity_signals"].str.split("|").explode().replace("", np.nan).dropna().value_counts().to_dict(), SIGNAL_VOCAB),
        n_with_signal=int((r["n_severity_signals"] >= 1).sum()),
        n_with_2plus=int((r["n_severity_signals"] >= 2).sum()),
        express_barrier=int(r["express_barrier"].sum()),
        outcome_stated=int(r["outcome_stated"].sum()),
    )

    # ---- Stage 2 journey
    touched = {s: int(r["journey_stages"].str.contains(s).sum()) for s in STAGES}
    b = r["behavior_code"]; c = r["closer_code"]; mm = r["memory_code"]
    breakdown = {
        "REMEMBER": dict(n=int((r["forgotten"] != "").sum()), basis="memory sentence names information the user lacks (M02-M04, M06-M10, M12)"),
        "EXPRESS": dict(n=int(P["opps"]["O1 Memory expression"].sum()), basis="memory cannot be turned into keyword/name/wording/description/narrowing (M02,M05,M06,M11,M12) or user contrasts with precise identifiers (C04)"),
        "MATCH": dict(n=int(P["opps"]["O4 Contextual matching (candidate-set precision)"].sum()), basis="date search returned too many results (B03) or many plausible results (C08); product output is otherwise rarely described"),
        "RECOGNIZE": dict(n=int(P["opps"]["O3 Candidate recognition / verification"].sum()), basis="one-by-one opening, timeline/thumbnail scan, date-range comparison, similar-not-exact, cannot tell which is right (B04,B11,B13,B14,B16,C08)"),
        "RECOVER": dict(n=int(P["opps"]["O5 Retrieval recovery"].sum()), basis="reformulation, switching, browsing fallback, several attempts, other app, gave up, failed (B05,B07-B10,B12,B15,B17,B18)"),
    }
    paths = r["journey_stages"].str.replace("|", " > ", regex=False).value_counts().head(8).to_dict()
    m["journey"] = dict(touched=touched, breakdown=breakdown, top_paths=paths,
                        n_paths=int(r["journey_stages"].nunique()))

    # ---- Stages 3-5: needs, segments, opportunities
    m["needs"] = {k: {**summarize(v, r), "profile": profile(v, r)} for k, v in P["needs"].items()}
    m["segments"] = {k: {**summarize(v, r), "profile": profile(v, r)} for k, v in P["segments"].items()}
    m["opps"] = {k: {**summarize(v, r), "profile": profile(v, r)} for k, v in P["opps"].items()}
    seg_names = list(P["segments"])[:4]
    m["segment_overlap_with_express"] = {k: int((P["segments"][k] & r["express_barrier"]).sum()) for k in seg_names}
    m["opp_overlap"] = {a: {b_: int((P["opps"][a] & P["opps"][b_]).sum()) for b_ in P["opps"]} for a in P["opps"]}
    m["opp_union_all"] = int(pd.concat(list(P["opps"].values()), axis=1).any(axis=1).sum())

    # ---- Target segment
    T = P["segments"]["SEG-T Effortful-path retrievers (SEG-2 or SEG-3)"]
    t = r[T]
    m["target"] = dict(
        n=int(T.sum()), of=len(r), pct=round(100 * T.mean(), 1),
        profile=profile(T, r),
        knows_exists_pct=round(100 * profile(T, r)["knows_exists"] / int(T.sum()), 1),
        by_state=t["retrieval_state"].value_counts().to_dict(),
        by_behavior=t["behavior_code"].value_counts().sort_index().to_dict(),
        adjacent_exit=int(P["segments"]["SEG-1 Exit-path retrievers"].sum()),
        unresolved_or_exit_downstream=int(P["segments"]["SEG-1 Exit-path retrievers"].sum()),
        example_ids=t["record_id"].sort_values().head(5).tolist(),
        after_exact_dup_removal=int(T[r["exact_duplicate_of"] == ""].sum()),
        after_near_dup_removal=int(T[~r.duplicated("core_signature")].sum()),
    )

    # ---- Impact sizing (dataset arithmetic only)
    E = len(r); n_t = int(T.sum())
    uncertain_in_t = int((t["outcome"] == "similar_uncertain").sum())
    effort_in_t = int((t["n_severity_signals"] >= 1).sum())
    m["impact"] = dict(eligible=E, target=n_t, target_pct=round(100 * n_t / E, 1),
                       target_with_effort_signal=effort_in_t,
                       target_uncertain_stated=uncertain_in_t,
                       target_found_with_effort_stated=int((t["outcome"] == "found_with_effort").sum()),
                       target_outcome_unknown=int((t["outcome"] == "unknown").sum()),
                       exits_adjacent=int(P["segments"]["SEG-1 Exit-path retrievers"].sum()),
                       exits_failed_or_abandoned=int(r["outcome"].isin(["failed", "abandoned"]).sum()))

    # ---- Structure / independence checks (are cross-tabs meaningful, or generator artifacts?)
    m["independence"] = {
        "object_class x memory_code": cramers_v(r["object_class"], r["memory_code"]),
        "object_class x retrieval_state": cramers_v(r["object_class"], r["retrieval_state"]),
        "memory_code x retrieval_state": cramers_v(r["memory_code"], r["retrieval_state"]),
        "memory_code x behavior_code": cramers_v(r["memory_code"], r["behavior_code"]),
        "source x retrieval_state": cramers_v(r["source"], r["retrieval_state"]),
        "source x memory_code": cramers_v(r["source"], r["memory_code"]),
        "source x object_class": cramers_v(r["source"], r["object_class"]),
    }
    doc_or_obj = r["object_class"].isin(["document_screenshot", "physical_object"])
    social_mem = _in(r["memory_code"], "M03", "M04", "M08")
    m["incoherent_pairs"] = dict(
        n=int((doc_or_obj & social_mem).sum()), of_doc_object=int(doc_or_obj.sum()),
        example=r.loc[doc_or_obj & social_mem, ["record_id", "object_text", "memory_text"]].head(3).to_dict("records"))

    # ---- traceability samples
    def quote(mask, k=2):
        return r.loc[mask, ["record_id", "raw_text"]].sort_values("record_id").head(k).to_dict("records")
    m["quotes"] = dict(
        express=quote(_in(mm, "M11")), exit_=quote(_in(b, "B10")), recovery=quote(_in(b, "B15")),
        uncertain=quote(_in(c, "C08") & _in(b, "B14")), inspection=quote(_in(b, "B13")),
        time=quote(_in(mm, "M10") & _in(b, "B16")), abandon=quote(_in(b, "B12")),
        recog=quote(_in(mm, "M05")), path=quote(_in(mm, "M09")),
    )
    m.update(extras(r, P, m))
    return m, df, r


if __name__ == "__main__":
    metrics, df, r = compute()
    config.configure()
    (config.OUTPUT / "metrics.json").write_text(json.dumps(metrics, indent=2, default=int), encoding="utf-8")
    print(json.dumps({k: metrics[k] for k in ["stage0", "impact", "independence", "incoherent_pairs"]}, indent=1, default=int)[:4000])
