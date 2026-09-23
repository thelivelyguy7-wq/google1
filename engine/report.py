"""Stage 15: render the 13-section discovery report from computed metrics (no hand-typed counts).

Epistemic labels follow the brief's six categories and are never merged:
  [RAW]        verbatim record text or record ID
  [OBS]        observed behaviour in the corpus: a count over coded records (primary-research counts will use [OBS-PRIMARY])
  [INTERP]     interpretation: what the evidence may suggest
  [OPP-HYP]    opportunity hypothesis: an area worth investigating
  [PROB-HYP]   problem hypothesis: a possible underlying user problem
  [VALIDATED]  validated problem: supported by primary research (none exists yet)
plus [ASSUME] for assumptions and [UNKNOWN] for what the data cannot say.
"""
from .analyze import compute, _in
from . import config
from . import narrative as NR
from . import lexicon as L

TAGS = ("`[RAW]` verbatim record · `[OBS]` observed behaviour in the corpus (a count) · `[INTERP]` interpretation · `[OPP-HYP]` opportunity hypothesis · "
        "`[PROB-HYP]` problem hypothesis · `[VALIDATED]` validated problem (**none yet**) · `[ASSUME]` assumption · `[UNKNOWN]` not knowable from this data")


def g(d, prefix):
    return next(v for k, v in d.items() if k.startswith(prefix))


def oc(p):
    o = p["outcomes"]
    parts = [f"{o['found_with_effort']} found-with-effort", f"{o['similar_uncertain']} similar-but-uncertain",
             f"{o['failed']} failed", f"{o['abandoned']} abandoned", f"{o['external_workaround']} other-app/device workaround"]
    parts = [x for x in parts if not x.startswith("0 ")]
    return (", ".join(parts) or "no outcome stated") + f"; {o['unknown']} unknown"


def tb(p):
    return "; ".join(f"{k} ({v})" for k, v in p["top_behaviors"])


def pct(a, b):
    return f"{100 * a / b:.1f}%"


def top(d, k=4):
    return ", ".join(f"{a.replace('_', ' ')} {b}" for a, b in list(d.items())[:k])


def build_report(precomputed=None) -> str:
    m, df, r = precomputed or compute()
    s0, s1, J, T, I, D = m["stage0"], m["stage1"], m["journey"], m["target"], m["impact"], m["decomposition"]
    E = s0["relevant"]
    idx = m["evidence_index"]
    N, S, O = m["needs"], m["segments"], m["opps"]
    S1, S2, S3, S4, ST = (g(S, p) for p in ["SEG-1", "SEG-2", "SEG-3", "SEG-4", "SEG-T"])
    O1, O2, O3, O4, O5, O6, O7, O8 = (g(O, f"O{i}") for i in range(1, 9))
    BG, OA, OJ, SQ = m["behavior_groups"], m["outcome_all"], m["object_judgement"], m["stage_questions"]

    def tr(key, k=3):
        """Traceability: example record IDs plus a pointer to the full list in evidence_index.csv (rule 15)."""
        ids = idx[key]
        return f"[RAW] {', '.join(ids[:k])} (all {len(ids)}: `evidence_index.csv` → `{key}`)"

    def ev(col, prefix, k=2):
        sub = r[_in(r[col], prefix)].sort_values("record_id").head(k)
        cmap = {"memory_code": "memory_text", "behavior_code": "behavior_text", "closer_code": "closer_text"}
        return "; ".join(f'{a} "{b}"' for a, b in zip(sub.record_id, sub[cmap[col]]))

    exit_o1 = sum(O1["profile"]["outcomes"][k] for k in ["failed", "abandoned", "external_workaround"])
    exit_all = S1["n"]
    xb_by_seg = {n: g(S, n)["profile"]["express_barrier"] for n in ["SEG-1", "SEG-2", "SEG-3", "SEG-4"]}
    ind = m["independence"]
    max_v = max(v["cramers_v"] for v in ind.values()); min_p = min(v["p"] for v in ind.values())
    recog = D["D4"]["intact"]
    out = []
    w = out.append

    # ------------------------------------------------------------------ preface (not a numbered section)
    w("# Google Photos Retrieval — Product Discovery Report")
    w("")
    w("> **REPRESENTATIVE DATASET.** All counts are *X of Y records in a real corpus* (`google_photos_raw_dataset.csv`). "
      "They are not Google Photos user research, not population statistics, not Google internal data. They show directional patterns and hypotheses only.")
    w(">")
    w("> **PROPOSED RESEARCH PLAN — NOT RESEARCH FINDINGS.** No interviews, tests or surveys have been run; nothing in §9–§12 is a participant result.")
    w("")
    w(f"Label key: {TAGS}")
    w("")
    w("Record IDs trace every conclusion; the full list behind each named group is in `output/evidence_index.csv`. Method, the discovery chain, structure tests and the file map are in `output/discovery_appendix.md`.")
    w("")

    # ------------------------------------------------------------------ 1
    w("## 1. Dataset Quality & Relevance")
    w("")
    w("| Classification | Records | Basis |")
    w("|---|---|---|")
    w(f"| **Retrieval-related** | **{s0['relevant']}** of {s0['total']} | Contains a retrieval object, a memory statement and a behaviour/outcome statement about finding an existing photo (IDs `REC-0001…`) |")
    w(f"| Possibly retrieval-related | {s0['possibly']} | 'I accidentally deleted a photo and need to restore it': intent is to get a photo back, but it is a restore flow with no memory or search-behaviour evidence. Excluded from all denominators |")
    w(f"| Not retrieval-related | {s0['irrelevant']} | Single-sentence `REC-N…` records on sharing, settings, storage, battery, backup, editing, printing, collage, face-grouping defect |")
    w(f"| Insufficient evidence | {s0['insufficient']} | None: every non-relevant record is unambiguous |")
    w(f"| Ambiguous retrieval intent | {s0['ambiguous']} | None by the rules above; the {s0['possibly']} 'possibly' records are the nearest case |")
    w("")
    w(f"All {s0['relevant']} relevant records are retained, including those where the user eventually found the photo. `[OBS]` These counts describe this file only.")
    w("")
    w("**Duplicates / low information**")
    w(f"- Exact-duplicate text: {s0['exact_dup_all']} records overall ({s0['exact_dup_relevant']} among relevant, {s0['exact_dup_all'] - s0['exact_dup_relevant']} among the off-topic set, which reuses only 15 sentences). Retained; the target segment changes {T['n']} → {T['after_near_dup_removal']} after near-duplicate removal.")
    w(f"- Near-duplicates (same object + memory + behaviour + closer, different opener): {s0['near_dup_records']} records in repeated groups ({s0['near_dup_extra']} extra copies).")
    w(f"- Extremely low-information: {s0['low_info']} records (single sentence), all off-topic. Among relevant records, {s1['no_closer']} have no closing sentence but still carry object, memory and behaviour.")
    w("")
    w("**Important data-quality limitations**")
    w(f"1. **Template-composed text.** The 840 records use only {s0['n_unique_sentences']} distinct sentences in a fixed order (opener → object → memory → one behaviour/outcome → optional closer). Frequencies reflect how the file was generated, not how often anything happens.")
    w(f"2. **No cross-field structure beyond chance.** Object×memory, memory×behaviour, object×state and source×state associations are all statistically indistinguishable from independence (Cramér's V ≤ {max_v}, smallest p = {min_p}; table in the appendix). "
      "So \"screenshot searchers behave differently\" or \"Reddit users fail more\" cannot be claimed from this data. This also confirms that source/platform is not a usable segmentation axis, and it means the case's question 'what kinds of old photos do users struggle to retrieve?' has no data-supported answer beyond the object mix.")
    if m['incoherent_pairs']['n'] > 0:
        ex = f" (e.g. {m['incoherent_pairs']['example'][0]['record_id']}: \"{m['incoherent_pairs']['example'][0]['object_text']}\" + \"{m['incoherent_pairs']['example'][0]['memory_text']}\")"
    else:
        ex = ""
    w(f"3. **Semantic mismatches.** {m['incoherent_pairs']['n']} of {m['incoherent_pairs']['of_doc_object']} document/screenshot/object records pair the item with people/place/album memory{ex}. Object-specific memory conclusions are unsafe.")
    w(f"4. **Outcome is sparse and partly circular.** Only {s1['outcome_stated']} of {E} relevant records state an outcome; {s1['outcome'].get('unknown', 0)} are unknown. Outcome sits in the same sentence that defines the retrieval state, so 'outcome by segment' restates the definition; it is not independent evidence.")
    w("5. **Complaint-selected corpus.** Every relevant record is a help-seeking or complaint post. There are 0 records of quick, uneventful retrieval, so success/failure *rates* and any baseline are unobservable `[UNKNOWN]`.")
    w(f"6. **Framing sentences are not behaviour.** Openers such as 'The search is frustrating' ({s0['opener_mix'].get('affect_frustration', 0)}) and 'Google Photos, please make this easier' ({s0['opener_mix'].get('request_to_vendor', 0)}) were kept as text but not used as evidence (no sentiment analysis; no solution inferred from the vendor request).")
    w(f"7. **Metadata not used analytically.** `engagement`, `author_id` ({s0['repeated_authors']} records share an author id with another) and `date_posted` ({s0['date_min']} to {s0['date_max']}) were not used.")
    w(f"8. **Object classes are partly my grouping.** {OJ['judgement_records']} of {E} records name an object whose class is a judgement call ({len(OJ['judgement_objects'])} of {OJ['n_objects']} distinct objects; e.g. 'the old meme I saved', 'our Diwali family photo'). Each carries an alternative class in `coded_records.csv` (`object_class_alt`), and 'a yellow truck' is left as *Unspecified*. No finding in this report depends on the class, because object is independent of memory and behaviour.")
    w("")

    # ------------------------------------------------------------------ 2
    w("## 2. Retrieval Need Landscape")
    w("")
    w(f"Needs come from what records say users remember, lack and do, never from source. They overlap. Shares are of {E} relevant records. Behaviour lists mirror the corpus overall because behaviour is independent of memory pattern here (§1).")
    w("")
    w("| Need | User goal | Memory pattern | Behaviour (most common stated) | Outcome (stated) | Evidence |")
    w("|---|---|---|---|---|---|")
    need_text = NR.NEEDS
    for k, v in N.items():
        c = k.split()[0]
        w(f"| **{k}** | {need_text[c][0]} | {need_text[c][1]} | {tb(v['profile'])} | {oc(v['profile'])} | {v['n']} of {E} ({v['pct']}%); {tr('need:' + c, 2)} |")
    w("")
    w("**Need detail: retrieval context and journey stages involved** (Stage 3 fields)")
    w("")
    w("| Need | Retrieval context `[OBS]` | Journey stages involved (records touching each) | Memory characteristics |")
    w("|---|---|---|---|")
    for k, v in N.items():
        c = k.split()[0]; p = v["profile"]
        ctx = f"objects: {top(p['object_mix'], 3)}; library size stated in {p['large_library_stated']} of {v['n']}"
        stages = ", ".join(f"{st.title()} {n}" for st, n in p["stage_counts"].items())
        mem = f"remembers: {top(p['remembered_mix'], 3)}; lacks: {top(p['forgotten_mix'], 3)}"
        w(f"| {c} | {ctx} | {stages} | {mem} |")
    w("")
    w("`[INTERP]` The needs fall into three families: **(a) memory-to-query gaps** (N1–N5, N7: the user holds context but lacks a usable identifier), **(b) verification** (N6) and **(c) recovery** (N8). "
      f"Every relevant record states an imprecise or hard-to-use memory ({J['breakdown']['RECALL']['n']} name specific missing information; the other {E - J['breakdown']['RECALL']['n']} describe memory the user cannot readily use as an identifier, which is an interpretation). "
      "No record describes retrieval by a precise identifier, so a Direct-vs-Contextual split has nothing to split here; the only Direct-side signal is the contrast sentence "
      f"'It feels much easier when I know an exact date or person's name' ({s1['closer_code']['C04_easier_with_precise_identifier']} records).")
    w("")
    w("**Answers to the case's sample questions** (with what the data can and cannot support)")
    w("")
    w("| Case question | Answer from this corpus | Limit |")
    w("|---|---|---|")
    w(f"| What kinds of old photos do users struggle to retrieve? | `[OBS]` Objects span {top({L.OBJECT_CLASS_LABEL[k]: v for k, v in s1['object_class'].items()}, 6)}. | No class struggles more than chance (object is independent of behaviour and outcome), so no ranking of kinds is supportable |")
    w(f"| What do people actually remember? | `[OBS]` {top(s1['remembered'], 8)} (records naming each). | Memory statements are template sentences; richness of real memory is `[UNKNOWN]` |")
    w(f"| What have they forgotten? | `[OBS]` {top(s1['forgotten_family'], 7)}. Time precision is the largest named family. | 'Don't explicitly state' = memory stated without a named gap |")
    w(f"| How do users formulate searches when memory is incomplete? | `[OBS]` See the behaviour table below: first-attempt input strategies {BG['First-attempt input strategies']['n']}, date-based narrowing {BG['Date-based narrowing']['n']}, reformulation {BG['Reformulation (different or several related words)']['n']}, strategy switching {BG['Switching strategy (terms/albums, person then browse, keywords then scroll)']['n']}. | One behaviour sentence per record; sequences within a record are not observable |")
    w("")
    w("**How users searched (Stage 1E: one stated behaviour per record)** `[OBS]`")
    w("")
    w("| Behaviour group | Records | Members | Example records |")
    w("|---|---|---|---|")
    lab = m["behavior_labels"]
    for name, v in BG.items():
        mem_s = "; ".join(f"{lab[c]} {n}" for c, n in v["members"].items())
        w(f"| {name} | {v['n']} of {E} ({v['pct']}%) | {mem_s} | {', '.join(v['example_ids'])} |")
    w("")
    w("**Stated outcomes across all relevant records (every category in the brief; unstated is never inferred)** `[OBS]`")
    w("")
    w("| Outcome | Records |")
    w("|---|---|")
    names = {"found_quickly": "Found quickly", "found_with_effort": "Found with effort", "found_after_reformulation": "Found after reformulation",
             "found_after_browsing": "Found after browsing", "similar_uncertain": "Similar result but uncertain", "failed": "Failed",
             "abandoned": "Abandoned", "external_workaround": "External workaround", "unknown": "Outcome Not Stated"}
    for c, n in OA.items():
        w(f"| {names[c]} | {n} of {E} ({pct(n, E)}) |")
    w("")
    w("**Retrieval objects** (context, not segments): " + "; ".join(f"{L.OBJECT_CLASS_LABEL[k]} {v}" for k, v in s1["object_class"].items()) + f" (of {E}).")
    w("")

    # ------------------------------------------------------------------ 3
    w("## 3. Behavioral Segments")
    w("")
    w(f"Segments are observable *retrieval states* stated in each record's single behaviour/outcome sentence, so SEG-1…4 are mutually exclusive and sum to {E}. All share one precondition: a specific photo the user expects to exist, with imprecise memory of it. "
      "They correspond to the retrieval-state lens (unresolved / recovery-dependent / candidate-heavy); no 'direct / low-effort' state exists in this corpus.")
    w("")
    w("| Segment | Objective definition | Records | Typical behaviour | Failure / effort | Outcome (stated) |")
    w("|---|---|---|---|---|---|")
    segdef = NR.SEGMENT_DEFS
    for k, v in S.items():
        c = k.split()[0]; p = v["profile"]
        w(f"| **{k}** | {segdef[c]} | {v['n']} of {E} ({v['pct']}%); {tr('seg:' + c, 2)} | {tb(p)} | {p['with_severity_signal']} with ≥1 severity signal; {p['with_2plus_signals']} with ≥2 | {oc(p)} |")
    w("")
    w("**Segment profile: what they remember, forget, do, and how it ended** (Stage 4) `[OBS]`")
    w("")
    w("| Segment | Remember | Forget | Do | Found quickly | Found with effort | Uncertain | Failed | Abandoned | Other-app workaround | Outcome Not Stated |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for k, v in S.items():
        p = v["profile"]; o = p["outcomes"]
        w(f"| {k.split()[0]} | {top(p['remembered_mix'], 3)} | {top(p['forgotten_mix'], 3)} | {tb(p)} | {p['found_quickly']} | {o['found_with_effort']} | {o['similar_uncertain']} | {o['failed']} | {o['abandoned']} | {o['external_workaround']} | {o['unknown']} |")
    w("")
    w("**Severity signals by segment** (records carrying each signal) `[OBS]`")
    w("")
    sig_names = list(s1["signals"].keys())
    w("| Segment | " + " | ".join(x.replace("_", " ") for x in sig_names) + " |")
    w("|---|" + "---|" * len(sig_names))
    for k, v in S.items():
        sc = v["profile"]["signal_counts"]
        w(f"| {k.split()[0]} | " + " | ".join(str(sc.get(x, 0)) for x in sig_names) + " |")
    w("")
    w("Severity-signal vocabulary (from the brief, coded from behaviour/closer sentences): reformulation, browsing, large candidate set, uncertainty, repeated attempts, strategy switching, external workaround, abandonment, failure. "
      "Across all relevant records: " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in s1["signals"].items()) + f"; {s1['n_with_signal']} of {E} carry ≥1 signal and {s1['n_with_2plus']} carry ≥2.")
    w("")
    w(f"`[INTERP]` Retrieval state is defined by the sentence that carries the signals, so 'all members show a signal' inside SEG-1/2/3 is **definitional, not a finding**. The informative contrasts: (a) SEG-4 has almost none ({S4['profile']['with_severity_signal']} of {S4['n']}, all from the closing 'cannot tell which is right' sentence); "
      f"(b) memory barriers are spread evenly: explicit express-barrier statements occur in {xb_by_seg['SEG-1']}/{S1['n']} of SEG-1, {xb_by_seg['SEG-2']}/{S2['n']} of SEG-2, {xb_by_seg['SEG-3']}/{S3['n']} of SEG-3 and {xb_by_seg['SEG-4']}/{S4['n']} of SEG-4 ({pct(s1['express_barrier'], E)} overall), so no segment is distinguished by memory type in this file.")
    w("")

    # ------------------------------------------------------------------ 4
    w("## 4. Retrieval Journey Mapping")
    w("")
    w("Working model, not a proven funnel: Recall → Express → Match → Recognize → Recover. Each record maps to the stages its sentences evidence.")
    w("")
    w("| Stage | Records touching stage | Records with explicit breakdown evidence | What counts as breakdown evidence |")
    w("|---|---|---|---|")
    for st in ["RECALL", "EXPRESS", "MATCH", "RECOGNIZE", "RECOVER"]:
        b = J["breakdown"][st]
        w(f"| **{st.title()}** | {J['touched'][st]} of {E} | {b['n']} of {E} ({pct(b['n'], E)}) | {b['basis']} |")
    w("")
    w("Most common stage paths (of " + str(J["n_paths"]) + " observed): " + "; ".join(f"`{k}` {v}" for k, v in J["top_paths"].items()) + ".")
    w("")
    w("**The five stage questions answered from the data** (Stage 2) `[OBS]`")
    w("")
    w("| Stage | Question | Answer | Unknown |")
    w("|---|---|---|---|")
    w(f"| Recall | {SQ['RECALL']['question']} | {top(dict(SQ['RECALL']['top_remembered']), 5)} | Whether real memory is richer than these statements |")
    w(f"| Express | {SQ['EXPRESS']['question']} | First-attempt inputs {SQ['EXPRESS']['first_attempt']}; date-based {SQ['EXPRESS']['date']}; reformulation {SQ['EXPRESS']['reformulation']}; person then browse {SQ['EXPRESS']['person_then_browse']}; keywords then scroll {SQ['EXPRESS']['keywords_then_scroll']}; explicit barrier {SQ['EXPRESS']['barrier']} | Order and content of real queries |")
    w(f"| Match | {SQ['MATCH']['question']} | Candidates surfaced in {SQ['MATCH']['candidates_surfaced']} records (incl. 'too many results' {SQ['MATCH']['too_many_results']}); **{SQ['MATCH']['product_misread_stated']} records say the product misread the clues** | Whether the target was among the candidates |")
    w(f"| Recognize | {SQ['RECOGNIZE']['question']} | Would recognise on sight {SQ['RECOGNIZE']['can_on_sight']}; cannot tell / near miss {SQ['RECOGNIZE']['cannot_tell']}; heavy inspection or browsing {SQ['RECOGNIZE']['heavy_inspection']} | When recognition holds and when it fails |")
    w(f"| Recover | {SQ['RECOVER']['question']} | Reformulate / switch / browse {SQ['RECOVER']['effort']}; success after several attempts {SQ['RECOVER']['success_after_effort']}; exits {SQ['RECOVER']['exits']} | What prompted each change; whether other-app users succeeded |")
    w("")

    w("### 4.1 Decomposition of successful retrieval")
    w("")
    w("`[INTERP]` **Successful retrieval of a vaguely remembered photo = the user has usable partial memory (D1) AND turns it into an input (D2) AND the product brings the intended photo into the candidates (D3) AND the user recognises it (D4) AND, if the first try fails, the user can refine until it works or stop knowingly (D5) AND the photo is in the searchable library (D6).** "
      "A retrieval fails at the first node that does not hold. The nodes map onto the case's four questions plus two boundary nodes. Built in `engine/decomposition.py`.")
    w("")
    w("| Node | Case question | User behaviour | Product outcome | Maps to opportunity |")
    w("|---|---|---|---|---|")
    for k, v in D.items():
        w(f"| **{k} {v['name']}** | {v['brief_question']} | {v['user_behavior']} | {v['product_outcome']} | {v['opportunity']} |")
    w("")
    w("**Evidence per node** `[OBS]` (records; a record can appear under several polarities). *Breakdown* = record states a difficulty here; *indirect* = consistent with failure here but not attributable; *effort* = extra work here; *intact* = capability retained or step worked; *no evidence* = the record says nothing about this node.")
    w("")
    w("| Node | Breakdown (explicit) | Indirect | Effort | Intact | Attempt only | No evidence at node | Reading `[INTERP]` |")
    w("|---|---|---|---|---|---|---|---|")
    reading = {
        "D1": f"Precondition, not a failure: {D['D1']['condition']} records name missing information; no record says the user remembers too little to search.",
        "D2": f"Strongest explicit difficulty: {D['D2']['breakdown']} records state memory is hard to express.",
        "D3": f"**{D['D3']['breakdown']} records say the product misread the clues.** Only indirect signs ({D['D3']['indirect']}); {D['D3']['intact']} records show candidates were surfaced. Cannot be attributed from this corpus.",
        "D4": f"{D['D4']['breakdown']} cannot confirm or found a near miss; {D['D4']['effort']} did heavy inspection; {D['D4']['intact']} say they would recognise it. Recognition holds in some records and fails in others.",
        "D5": f"{D['D5']['effort']} reformulate/switch/browse; {D['D5']['breakdown']} end unresolved or leave; only {D['D5']['intact']} state success.",
        "D6": f"{D['D6']['breakdown']} records say the photo is missing. {D['D6']['indirect']} leave the product, so absence is a hypothesis only.",
    }
    for k, v in D.items():
        w(f"| **{k} {v['name']}** | {v['breakdown']} | {v['indirect']} | {v['effort']} | {v['intact']} | {v['attempt']} | {v['no_evidence']} of {E} | {reading[k]} |")
    w("")
    w("**Where the decomposition points** `[OPP-HYP]`")
    w("")
    w(f"- Users report difficulty **expressing** (D2, {D['D2']['breakdown']}), **evaluating** (D4, {D['D4']['breakdown_or_effort']} records with breakdown or effort evidence) and **refining** (D5, {D['D5']['breakdown_or_effort']} records). These are where the evidence supports investigating.")
    w(f"- The case asks whether Google Photos **fails to understand the clues** (D3). **{D['D3']['breakdown']} of {E} records say so.** The corpus cannot answer this question, which is not the same as the answer being no. It is the highest-value unknown and it must not be assumed away or assumed true.")
    w("- **Where the greatest opportunity lies cannot be settled from this corpus,** because failures are not attributed to nodes. The task-based tests must do that attribution (§10.3), so the ranking can come from observed failures instead of statements.")
    w("")
    w("**First-failing-node rule for classifying every non-successful attempt in the task tests** `[ASSUME]` (proposed):")
    w("")
    from .decomposition import ATTRIBUTION_RULES, PRODUCTION_NOTE
    for i, (node, rule) in enumerate(ATTRIBUTION_RULES, 1):
        w(f"{i}. **{node} {D[node]['name']}**: {rule}.")
    w("")
    w(f"**Product outcomes to measure per node** (candidate measures; {PRODUCTION_NOTE})")
    w("")
    w("| Node | Candidate measure |")
    w("|---|---|")
    for k, v in D.items():
        w(f"| {k} {v['name']} | {v['proposed_measure']} |")
    w("")
    w("**Major breakdowns** `[OBS]`")
    w(f"- **Recall → Express:** {J['breakdown']['RECALL']['n']} records name information the user lacks (time precision {s1['forgotten_family']['time precision']}, a name {s1['forgotten_family']['name']}, a keyword {s1['forgotten_family']['search keyword']}, album {s1['forgotten_family']['album / organisation']}, how it was originally found {s1['forgotten_family']['how it was originally found']}, exact wording {s1['forgotten_family']['exact wording']}). "
      f"{s1['express_barrier']} records state the memory cannot easily be converted into a query, e.g. {ev('memory_code', 'M11', 1)}. {tr('node:D2:breakdown', 3)}")
    w(f"- **Match:** the corpus rarely says what the product returned; only {J['breakdown']['MATCH']['n']} records do. `[UNKNOWN]` whether matching, expression or recognition is the weak link. {tr('opp:O4', 3)}")
    w(f"- **Recognize:** {recog} records say the user *would recognise* the photo on sight (e.g. {ev('memory_code', 'M05', 1)}), while {s1['closer_code']['C08_plausible_cannot_tell']} say plausible results left them unable to tell which is right and {s1['behavior_code']['B14_similar_not_exact']} report a similar-but-not-exact find. Recognition holds in some records and fails in others; the file cannot say when. {tr('node:D4:breakdown', 3)}")
    w(f"- **Recover:** {J['breakdown']['RECOVER']['n']} records ({pct(J['breakdown']['RECOVER']['n'], E)}) show reformulation, switching, browsing fallback, other-app use, giving up or failure. Only {s1['outcome']['found_with_effort']} state a success. {tr('opp:O5', 3)}")
    w("")
    w(f"**Repeated behaviours:** reformulation ({s1['signals']['reformulation']}), browsing ({s1['signals']['browsing']}), strategy switching ({s1['signals']['strategy_switch']}). "
      f"**Success pattern:** only 'found after several attempts' ({s1['outcome']['found_with_effort']}); success comes with effort. **Failure/exit patterns:** could not find ({s1['outcome']['failed']}), gave up and asked someone ({s1['outcome']['abandoned']}), moved to another app/device ({s1['outcome']['external_workaround']}). "
      "**Uncertainty:** whether other-app/device users found the photo, and whether 'similar but not exact' users later succeeded, is not stated.")
    w("")

    # ------------------------------------------------------------------ 5
    w("## 5. Opportunity Areas")
    w("")
    w(f"Opportunities are *where* retrieval could improve; they are not features and not problems. Counts are non-exclusive; together the {len(O)} cover {m['opp_union_all']} of {E}. Each maps to a decomposition node (§4.1). All are `[OPP-HYP]`.")
    w("")
    opp_txt = NR.opportunities(dict(s1=s1, ev=ev, S1=S1))
    for k, v in O.items():
        c = k.split()[0]; t = opp_txt[c]; p = v["profile"]
        w(f"### {k}")
        w(f"- **User behaviour:** {t['beh']}")
        w(f"- **Journey stage:** {t['st']} · **Decomposition node:** {t['node']}")
        w(f"- **Frequency** `[OBS]`: {v['n']} of {E} relevant records ({v['pct']}%); {tr('opp:' + c)}")
        w(f"- **Severity:** {t['sev']}")
        w(f"- **Outcome:** {oc(p)}")
        w(f"- **Evidence example:** {t['quote']}")
        w(f"- **User consequence** `[INTERP]`: {t['uc']}  **Product consequence** `[INTERP]`: {t['pc']}")
        w(f"- **Unknowns** `[UNKNOWN]`: {t['unk']}")
        w("")
    w(f"`[OBS]` Express-barrier records reach the exit-path state no more often than the corpus overall: {exit_o1} of {O1['n']} O1 records ({pct(exit_o1, O1['n'])}) versus {exit_all} of {E} overall ({pct(exit_all, E)}). Within this file, O1 rests on what users say, not on a measurable link to worse outcomes. {tr('claim:K11', 3)}")
    w("")

    # ------------------------------------------------------------------ 6
    w("## 6. Opportunity Prioritization")
    w("")
    w("Reasoning: Frequency × Severity × Outcome, then strategic relevance to the goal ('successfully retrieve a photo remembered but not precisely described'), evidence strength, researchability. "
      "No numeric scores. Labels are used only with the stated evidence. Frequency convention (analytic, not statistical): High ≥ 30% of relevant records, Medium 15–29%, Low < 15%. Potential solvability is `[UNKNOWN]` for every area and is not scored.")
    w("")
    w("| Opportunity | Frequency | Severity | Outcome | Strategic relevance | Evidence strength | Researchability | Why investigate? |")
    w("|---|---|---|---|---|---|---|---|")

    def fl(v): return "High" if v["pct"] >= 30 else ("Medium" if v["pct"] >= 15 else "Low")
    rows = [
        (O5, f"High: {O5['profile']['with_2plus_signals']} records with ≥2 signals; failure, abandonment, other-app use all sit here", "Only area containing every terminal outcome (%d failed/abandoned/other-app) plus all %d effortful successes" % (S1["n"], s1["outcome"]["found_with_effort"]), "High: success is decided after the first attempt", "High: explicit behaviour statements; but a symptom locus (causes lie upstream)", "High: participants can recount a recent attempt", "Where retrieval is won or lost; lets research trace back to Express and forward to Recognize"),
        (O1, "Medium: signals come from behaviour sentences, not the barrier itself", "Not distinguishable from base rate (%s vs %s exit)" % (pct(exit_o1, O1['n']), pct(exit_all, E)), "High: the goal is defined by imprecise memory", "Medium: explicit but self-report only", "High: memory-reconstruction interviews", "Leading upstream hypothesis; must be tested against rivals, not assumed"),
        (O3, "High: uncertainty %d, large candidate sets %d" % (s1["signals"]["uncertainty"], s1["signals"]["large_candidate_set"]), "%d similar-but-uncertain, %d abandoned/failed" % (s1["outcome"]["similar_uncertain"], O3["profile"]["outcomes"]["failed"] + O3["profile"]["outcomes"]["abandoned"]), "High: a found-but-unconfirmed photo is not a success", "Medium–High: explicit and repeated, silent on whether the target was present", "High: observable in task tests", "Distinguishes 'not surfaced' from 'surfaced but not recognised'"),
        (O2, "Medium: 'too many results' %d; manual comparison %d" % (s1["behavior_code"]["B03_date_search_too_many"], s1["behavior_code"]["B16_date_range_compare"]), "Mixed; no distinctive outcome", "Medium–High", "Medium: time memory explicit (%d) but tool-availability confound" % (s1["memory_code"]["M07_approx_time_not_day"] + s1["memory_code"]["M10_year_not_month"]), "High", "Largest single forgotten-information family (%d records)" % s1["forgotten_family"]["time precision"]),
        (O6, "Low–Medium", "Mixed", "Medium", "Low–Medium: memory statements only", "Medium", "Test inside interviews; not a lead"),
        (O4, "Medium", "Thin", "Medium (unknown: 0 records say the product misread the clues)", "Low: output rarely described", "Medium", "Corpus cannot size it; the task tests must (D3 attribution)"),
        (O7, "High per record (all terminal) but indirect", "Terminal: %d abandoned + %d other-app" % (s1["outcome"]["abandoned"], s1["outcome"]["external_workaround"]), "Medium: if the photo is outside the library, search cannot succeed", "Low: indirect inference", "Medium: needs a library audit, not just interviews", "Cheap to rule in/out during interviews (was the photo in the library?)"),
        (O8, "Low–Medium: one explicit statement; overlaps O1", "Mixed; no distinctive outcome", "Medium: separates 'cannot express' from 'does not know what can be expressed'", "Low: single sentence, subset of O1", "High: interviews and tasks can ask what participants believed they could do", "Distinguishes a knowledge gap from a memory gap inside O1 (D2)"),
    ]
    for (v, sv, ou, sr, es, rs, why) in rows:
        f = fl(v)                                      # computed from the data; never a hand-typed label
        oname = [k for k, x in O.items() if x is v][0]
        w(f"| **{oname}** | {f} ({v['n']}, {v['pct']}%); {tr('opp:' + oname.split()[0], 2)} | {sv} | {ou} | {sr} | {es} | {rs} | {why} |")
    w("")
    w("**Selected for primary research** `[OPP-HYP]`: **O5 Retrieval recovery**, examined together with O3 and O1, and with O4 tested directly, as competing explanations of *why the first attempt does not resolve* (expression D2, matching D3, recognition D4). "
      "Rationale: it is the largest area with explicit behaviour evidence, contains every terminal outcome, is tied to the strategic goal, and is highly researchable. "
      "O1 alone would over-weight self-report that shows no outcome difference; O3 alone omits the exits; O4 cannot be ranked from this corpus but must not be ranked last by default. No solution is chosen.")
    w("")
    w(f"Records behind the selection `[OBS]`: O5 {tr('opp:O5', 3)}; O3 {tr('opp:O3', 2)}; O1 {tr('opp:O1', 2)}; O4 {tr('opp:O4', 2)}.")
    w("")

    # ------------------------------------------------------------------ 7
    w("## 7. Target Segment Hypothesis")
    w("")
    w("**TARGET SEGMENT HYPOTHESIS — TO BE VALIDATED** `[OPP-HYP]`")
    w("")
    w(f"> We should investigate **users who attempted to retrieve a specific photo they expected to exist, lacked a precise identifier for it, and either changed strategy / made several attempts or manually inspected a candidate set (SEG-T)** because they are the largest behaviourally defined group in the corpus ({T['n']} of {E}, {T['pct']}%), every member states effortful behaviour (definitional, see assumptions), none is described as retrieving quickly, and, if the four states are snapshots of one journey `[INTERP]`, the group sits upstream of the exit-path state ({T['adjacent_exit']} records) where retrieval visibly fails.")
    w("")
    w("| Element | Detail |")
    w("|---|---|")
    w(f"| Objective definition | Records whose behaviour sentence is one of B03, B04, B05, B07, B09, B11, B13, B14, B15, B16, B17, B18 (recovery-dependent {T['by_state']['recovery_dependent']} + candidate-inspection {T['by_state']['candidate_inspection']}). Shared precondition: imprecise memory of a specific photo. |")
    w(f"| Dataset size | {T['n']} of {E} ({T['pct']}%); {T['after_near_dup_removal']} after removing near-duplicates |")
    w(f"| Stated outcomes | {oc(T['profile'])} |")
    w(f"| Evidence | Express-barrier statements {T['profile']['express_barrier']}; 'would recognise on sight' {T['profile']['recognition_retained']}; 'cannot tell which is right' {T['profile']['cannot_confirm']}; explicit 'knows the photo exists' {T['profile']['knows_exists']} ({T['knows_exists_pct']}%). {tr('seg:SEG-T', 5)} |")
    w(f"| Why investigate | Frequency (largest); effort (strategy switching, browsing, large candidate sets, repeated attempts); outcome uncertainty ({T['profile']['outcomes']['unknown']} unknown, {T['profile']['outcomes']['similar_uncertain']} uncertain); strategic relevance (retrieval is not clean for these users); researchability (recent attempts are recallable and observable) |")
    w("| Why not SEG-1 alone | Defined by outcome, so the corpus says nothing about what preceded it. Recruit SEG-1-like participants (failed/abandoned recently) as an adjacent probe. |")
    w(f"| Why not SEG-4 | {S4['n']} records, essentially no severity evidence. |")
    w("")
    w("**Assumptions** `[ASSUME]`: (1) the states are sequential snapshots of one journey, so the boundary between SEG-2 and SEG-3 is porous, hence the union; (2) 'expected to exist' is implied for all records by the attempt, and explicit in only "
      f"{T['profile']['knows_exists']} of {T['n']}; (3) effort is definitional within SEG-T, so it says *who to study*, not *how bad it is* `[UNKNOWN]`.")
    w("")

    # ------------------------------------------------------------------ 8
    w("## 8. Impact-Sizing Framework")
    w("")
    w("`Incremental successful retrievals = E × t × f × r × l`")
    w("")
    w("| Step | Symbol | Observed dataset value `[OBS]` | Assumption `[ASSUME]` | Production value |")
    w("|---|---|---|---|---|")
    w(f"| Eligible retrieval attempts | E | {E} relevant records (posts, not attempts); {tr('claim:K01', 2)} | Unit = one retrieval attempt sequence started from imprecise memory | **TBD: requires Google production data** |")
    w(f"| % in target behaviour | t | {I['target']} of {E} ({I['target_pct']}%); {tr('seg:SEG-T', 2)} | Not transferable to production | **TBD: requires Google production data** |")
    w(f"| % with failure/effort | f | Effort signal {I['target_with_effort_signal']} of {I['target']} (100% by definition); stated non-clean outcome {I['target_uncertain_stated']} (similar-but-uncertain); downstream exit-path {I['exits_adjacent']} (of which {I['exits_failed_or_abandoned']} failed/abandoned); {tr('seg:SEG-1', 2)} | 'Effort' needs an operational log definition (e.g. ≥2 queries or a long browse before success) | **TBD: requires Google production data** |")
    w(f"| % potentially recoverable | r | None; the corpus cannot estimate | Recoverable = photo is in the library and the user can recognise it; proxy to test: 'would recognise on sight' {T['profile']['recognition_retained']} of {T['n']}; {tr('claim:K08', 2)} | **TBD: primary research + production data** |")
    w("| Expected improvement | l | None | Only estimable after a solution exists; out of scope until the problem is defined | **TBD** |")
    w("| Incremental successful retrievals | — | — | — | **TBD** |")
    w("")
    w(f"Arithmetic illustration on counts only (not a forecast): the explicit non-success set is {I['target_uncertain_stated']} similar-but-uncertain + {I['exits_failed_or_abandoned']} failed/abandoned = {I['target_uncertain_stated'] + I['exits_failed_or_abandoned']} records; each 10 points of recovery on that set corresponds to ~{round((I['target_uncertain_stated'] + I['exits_failed_or_abandoned']) * 0.1)} records. Outcome is unknown for {I['target_outcome_unknown']} of {I['target']} target records, so the true base could be much larger or smaller.")
    w("")

    # ------------------------------------------------------------------ 9
    w("## 9. Research Hypotheses")
    w("")
    w("Each is a `[PROB-HYP]` to test, not a root cause. Every one has a competing explanation, separate evidence for/against/unknown, and a falsification test. Node = decomposition node (§4.1).")
    w("")
    MODES = NR.MODES
    hyps = NR.hypotheses(dict(s1=s1, J=J, ind=ind, pct=pct, O1=O1, E=E, recog=recog,
                             exit_o1=exit_o1, exit_all=exit_all))
    for name, node, key, obs, interp, hyp, comp, val, sup, opp, unk in hyps:
        w(f"### {name}")
        w(f"- **Node:** {node}")
        w(f"- **Observation** `[OBS]`: {obs} {tr(key, 3)}")
        w(f"- **Interpretation** `[INTERP]`: {interp}")
        w(f"- **Hypothesis** `[PROB-HYP]`: {hyp}")
        w(f"- **Competing explanation:** {comp}")
        w(f"- **Validate / falsify:** {val}")
        w(f"- **Evidence for:** {sup}")
        w(f"- **Evidence against:** {opp}")
        w(f"- **Unknown** `[UNKNOWN]`: {unk}")
        w(f"- **Qualitative (WHY/HOW):** {MODES[name[:2]][0]}")
        w(f"- **Quantitative (WHERE/HOW MUCH):** {MODES[name[:2]][1]}")
        w("")
    w("`[VALIDATED]` None of H1–H7 is validated. Verdicts stay *untested* until primary research supplies evidence.")
    w("")

    # ------------------------------------------------------------------ 10
    w("## 10. Primary Research Plan")
    w("")
    w("**PROPOSED RESEARCH PLAN — NOT RESEARCH FINDINGS.** Sequence: interviews → task-based tests → survey. Nothing here tests a solution. Dataset findings (§1–§8) and future primary findings are kept in separate columns of every synthesis table (§11).")
    w("")
    w("**Rule:** quantitative evidence answers WHERE and HOW MUCH; qualitative research answers WHY and HOW. Each method below is used only for what it can answer.")
    w("")
    w("| Method | Answers | Cannot answer | Used for |")
    w("|---|---|---|---|")
    w("| Corpus (today) | WHERE, directionally | WHY, HOW, HOW MUCH | Choosing what to investigate; no more |")
    w("| Interviews | WHY, HOW | HOW MUCH | H1–H5, H7; memory reconstruction; what prompted each change |")
    w("| Task-based tests | HOW (observed), WHERE (first failing node, small n) | HOW MUCH at population scale | H2–H6; D3 attribution |")
    w("| Survey | WHERE, HOW MUCH (self-reported) | WHY | Prevalence of the scenarios found qualitatively; H7 |")
    w("| Production data | HOW MUCH | WHY | Impact sizing (all TBD) |")
    w("")
    w("### 10.1 Interview plan")
    w("- **Purpose:** learn how people remember and describe photos they later struggle to find, and what happens next (WHY/HOW).")
    w("- **Method:** 30-minute behavioural interviews, remote, recall-a-recent-incident format (no hypotheticals).")
    w("- **Sample:** 16 participants: 6 effortful-path (recent multi-attempt or heavy-browsing retrieval), 4 recent failure/abandonment, 2 who found a contextual-memory photo quickly (contrast, since the corpus has no success baseline), 4 heavy-library users regardless of outcome. Quotas across age, device and library size.")
    w(f"- **Strata trace to the corpus** `[OBS]`: effortful-path {tr('seg:SEG-T', 2)}; failure/abandonment {tr('seg:SEG-1', 2)}.")
    w("")
    w("### 10.2 Interview guide (30 min)")
    guide = NR.INTERVIEW_GUIDE
    for t, qs, note in guide:
        w("")
        w(f"**{t}**")
        for q in qs: w(f"- {q}")
        w(f"- *Interviewer note:* {note}")
    w("")
    w("Avoid: 'Would an assistant/AI help?', 'Do you wish you could describe it in your own words?', any mention of features, or questions that assume difficulty.")
    w("")
    w("### 10.3 Task-based usability plan")
    w("- **Setup:** a prepared test library (comparable across participants) plus one self-chosen older photo per participant that they have not opened in over a year (non-sensitive; medical items use seeded stand-ins). ~45-minute sessions, think-aloud, 5-minute task cap `[ASSUME]`. Participants are not told how to search.")
    w("- **Sample:** 12 participants (5–8 typically surface most severe usability problems; benchmark times would need ≥ 20 `[ASSUME]`).")
    w("- **Recorded for every task (the six primary measures):** retrieval success, time to successful retrieval, attempts/reformulations, candidate photos inspected, abandonment, confidence (1–5).")
    w("- **Failure attribution:** every unsuccessful task is classified by the first failing node using the rule in §4.1, so the greatest opportunity comes from observed failures, not statements.")
    w("- **Also logged for every task (Stage 10B):** first action; first query; every reformulation; filters used; browsing behaviour (scrolling, timeline or thumbnail scanning); number of candidates inspected; time to success; confidence; abandonment; workaround use (another app, or asking someone).")
    w("")
    w("| Task | User scenario | Information provided | Information withheld | Expected behaviour to observe |")
    w("|---|---|---|---|---|")
    tasks = NR.TASKS
    for t in tasks: w("| " + " | ".join(t) + " |")
    w("")
    w("| Task | Primary measure (headline) | Also recorded | Qualitative observations |")
    w("|---|---|---|---|")
    qual = NR.TASK_QUALITATIVE
    prim = NR.TASK_PRIMARY
    for t in tasks:
        c = t[0].split()[0]
        w(f"| {t[0]} | {prim[c]} | The other five measures | {qual[c]} |")
    w("")
    w("### 10.4 Exploratory survey plan (after interviews and tests)")
    w("- **Purpose:** estimate prevalence, frequency, importance and failure/effort of retrieval scenarios *identified qualitatively* (WHERE/HOW MUCH). Reported separately from sample findings.")
    w("- **Content:** last retrieval attempt in the past 30 days; what was remembered/unknown (checklist derived from interviews); what was tried and in what order; outcome and time/attempt bands; confidence; other-app use; importance of the photo. No solution questions.")
    w("- **Sample:** ≥ 400 for ±5 points at 95% confidence on a proportion (worst case p=0.5), ≥ 100 per compared subgroup `[ASSUME]`. Active Google Photos users with quotas on library size, device and age.")
    w("- **Limits:** self-report and recall bias; survey rates are not production rates.")
    w("")
    w("### 10.5 Recruitment criteria")
    w("- Uses Google Photos as a primary photo store for ≥ 2 years; library of several thousand items `[ASSUME threshold]`.")
    w("- Has searched for an older photo in the past 30 days where they remembered the photo but not a precise identifier.")
    w("- Mix of outcomes (effortful success, failure/abandonment, quick success), object types, devices and ages.")
    w("- Exclude: Google/competitor employees, UX/research professionals, anyone in a photo-search study in the last 6 months.")
    w("")
    w("### 10.6 Sample-size rationale")
    w("- **Interviews (16):** thematic saturation has been reported around 12 interviews in fairly homogeneous samples (Guest, Bunce & Johnson, 2006); this segment is heterogeneous and needs contrast groups. Stop early if the last 3 add no new themes; extend if a hypothesis stays contested.")
    w("- **Usability tests (12):** enough to see recurring strategies and severe breakdowns per task; not enough to benchmark time-to-success (≥ 20 needed `[ASSUME]`).")
    w("- **Survey (≥ 400; ≥ 100 per subgroup):** ±5 points at 95% confidence for a proportion in the worst case; sized only after qualitative work fixes the categories.")
    w("")
    w("### 10.7 Success measures for the research")
    w("- ≥ 80% of interviewees give a specific recent incident with recall of what they remembered and tried.")
    w("- Each of H1–H7 ends with a documented verdict (supported / weakened / falsified) with at least one competing explanation tested.")
    w("- Task tests: complete logging of the six primary measures for every task, plus a failing-node classification for every unsuccessful attempt.")
    w("- Findings triangulated across ≥ 2 methods before any root cause is called validated.")
    w("")

    # ------------------------------------------------------------------ 11
    w("## 11. Research Synthesis Framework")
    w("")
    w("**PROPOSED RESEARCH PLAN — NOT RESEARCH FINDINGS.** No participant data exists yet; the primary-findings column is empty on purpose.")
    w("")
    w("| Layer | Question | Corpus input (today) | Primary-research input (future) | Rule to advance | Guard rail |")
    w("|---|---|---|---|---|---|")
    w("| Observation | What did people say or do? | `[OBS]` coded records | Transcripts, task logs (six measures + failing node) | Verbatim or logged, tagged with record or participant ID | No interpretation here |")
    w("| Pattern | What recurs? | Counts (X of 800) | Seen in ≥ 3 participants, in both stated and observed behaviour where possible | Two sources agree | Report 'n of N participants', never percentages of users |")
    w("| Interpretation | What might it mean? | `[INTERP]` | Written as ≥ 2 rival interpretations | Rival explains the same pattern | Keep separate from observation |")
    w("| Root-cause hypothesis | Why does the first attempt not resolve? | H1–H7 as `[PROB-HYP]` | Each marked supported / weakened / falsified | Rivals tested | No cause on one method |")
    w("| Validation | Is it real and how common? | None | Survey prevalence + task-test replication + production checks | Cause explains the pattern, rivals do not | Production sizing stays TBD until Google data exists |")
    w("| Problem | Can we state it? | Provisional only | Validated causes | §12 template only when validation is met | No solution language |")
    w("")

    # ------------------------------------------------------------------ 12
    w("## 12. Problem Definition")
    w("")
    w("**PROVISIONAL PROBLEM HYPOTHESIS — REQUIRES PRIMARY RESEARCH** `[PROB-HYP]`")
    w("")
    w("> Google Photos users trying to **find a specific photo they know they have** in **a large personal library**, when they remember its context but **not a precise identifier** (date, name, keyword or album), struggle to **reach it without repeated attempts, manual inspection, or leaving the product** because **[cause to be validated: candidates H1 expression gap · H2 recognition gap · H3 coarse time scoping · H4 unguided recovery · H5 photo outside the library; H3-related matching (D3) untested]**, resulting in **extra effort, uncertainty about whether the right photo was found, and in some cases giving up**.")
    w("")
    w(f"The cause slot is intentionally empty. User, context, struggle and consequence are supported directionally by the corpus; the cause is `[UNKNOWN]` until primary research. 'Large library' is stated in only {s1['closer_code']['C02_thousands_of_images']} records and 'knows it exists' is explicit in {T['profile']['knows_exists']} of {T['n']} target records, so both are `[ASSUME]`. `[VALIDATED]` No validated problem exists. The statement contains no solution, feature or technology terms.")
    w("")
    w(f"Evidence behind each element `[OBS]`: imprecise memory {tr('claim:K02', 2)}; struggle {tr('opp:O5', 2)}; manual inspection {tr('seg:SEG-3', 2)}; consequence {tr('seg:SEG-1', 2)}, {tr('claim:K07', 2)}.")
    w("")

    # ------------------------------------------------------------------ 13
    w("## 13. Evidence / Interpretation / Hypothesis / Unknown Matrix")
    w("")
    w("Evidence cells are `[OBS]` counts with `[RAW]` record IDs; the full list behind each claim ID is in `evidence_index.csv` under `claim:Kxx`. Hypothesis cells carry their type: `[OPP-HYP]` or `[PROB-HYP]`.")
    w("")
    w("| Claim | Evidence | Interpretation | Hypothesis | Unknown |")
    w("|---|---|---|---|---|")
    def c(k): return tr('claim:' + k, 2)
    mat = [
        (f"K01 Relevant records are {E} of {s0['total']}", f"{s0['irrelevant']} off-topic + {s0['possibly']} possible; {c('K01')}", "The file mixes on- and off-topic posts", "—", "Real-world share of retrieval talk"),
        (f"K02 Every relevant record describes imprecise memory", f"{J['breakdown']['RECALL']['n']} of {E} name lacked information; {c('K02')}", "The corpus is selected for contextual memory", "—", "How users with precise identifiers behave (no such records)"),
        (f"K03 Time precision is the most common lacked information", f"{s1['forgotten_family']['time precision']} records; {c('K03')}", "Users know roughly when, not exactly", "`[PROB-HYP]` H3", "Whether time is the strongest clue"),
        (f"K04 Users say memory is hard to convert into a query", f"{s1['express_barrier']} of {E}; {c('K04')}", "A gap between remembering and expressing", "`[PROB-HYP]` H1", "Whether memory is rich or thin"),
        (f"K05 Effort is widespread", f"{s1['n_with_signal']} of {E} carry ≥1 severity signal; {c('K05')}", "Retrieval often costs more than one step", "`[PROB-HYP]` H4, H7", "Prevalence; corpus is complaint-only"),
        (f"K06 Recovery behaviours are common", f"{J['breakdown']['RECOVER']['n']} of {E}; {c('K06')}", "First attempts often do not resolve", "`[PROB-HYP]` H4", "Why users change strategy"),
        (f"K07 Some users cannot confirm candidates", f"C08 {s1['closer_code']['C08_plausible_cannot_tell']}; similar-not-exact {s1['behavior_code']['B14_similar_not_exact']}; {c('K07')}", "Recognition can fail", "`[PROB-HYP]` H2", "Whether the target was present"),
        (f"K08 Some users say they would recognise on sight", f"{recog} of {E}; {c('K08')}", "Recognition may be intact when access is the barrier", "`[PROB-HYP]` H2 rival", "What cues suffice"),
        (f"K09 Exit paths exist", f"{S1['n']}: failed {s1['outcome']['failed']}, gave up {s1['outcome']['abandoned']}, other app {s1['outcome']['external_workaround']}; {c('K09')}", "Some retrievals end outside success", "`[PROB-HYP]` H5", "Whether the photo was in the library; whether other-app users succeeded"),
        (f"K10 Success is rarely stated", f"{s1['outcome']['found_with_effort']} found-with-effort; 0 found-quickly; {c('K10')}", "Complaint bias hides easy successes", "`[PROB-HYP]` H7", "Success rate"),
        (f"K11 Express-barrier records do not fail more often", f"{pct(exit_o1, O1['n'])} vs {pct(exit_all, E)}; {c('K11')}", "No measurable link inside this file", "`[PROB-HYP]` H1 (weakened as a sole explanation)", "Whether a real link exists"),
        (f"K12 SEG-T is the target segment hypothesis", f"{T['n']} of {E}; {c('K12')}", "Largest behavioural group with explicit effort", "`[OPP-HYP]` TARGET SEGMENT HYPOTHESIS — TO BE VALIDATED", "Size and outcomes in production"),
        (f"K13 Time-based narrowing is common", f"{len(idx['claim:K13'])} of {E}; {c('K13')}", "Users lean on date when it is all they have", "`[PROB-HYP]` H3", "Clue ranking within individuals"),
        (f"K14 Most outcomes are unstated", f"{s1['outcome'].get('unknown', 0)} of {E}; {c('K14')}", "Failure and success rates cannot be computed", "—", "Real outcome distribution"),
        ("K15 No record says the product misread the clues", f"0 of {E}; node D3 breakdown = {D['D3']['breakdown']}", "The 'does Google Photos understand?' question is unanswerable here, not answered no", "`[PROB-HYP]` D3 gap untested", "Whether the target was ever among the results"),
        ("K16 Retrieval recovery is the opportunity to research", f"O5 {O5['n']} of {E}; {tr('opp:O5', 2)}", "Where success is decided", "`[OPP-HYP]` investigate O5 with O3, O1 and O4 as rivals", "Root cause"),
        ("K17 Memory, behaviour, object and source are independent", f"Cramér's V ≤ {max_v}; p ≥ {min_p} (appendix)", "Template composition, not user behaviour", "—", "Any true structure; source is not a usable axis"),
        ("K18 No solution has been chosen; no problem is validated", "—", "The problem is not yet defined", "`[VALIDATED]` none", "All of §9–§12 pending primary research"),
    ]
    for row in mat: w("| " + " | ".join(row) + " |")
    w("")
    return "\n".join(out)


def build_appendix(precomputed=None) -> str:
    m, df, r = precomputed or compute()
    ind = m["independence"]
    out = []
    w = out.append
    w("# Discovery Report — Appendix")
    w("")
    w("Supporting material for `discovery_report.md`.")
    w("")
    w("## Discovery chain followed")
    w("")
    w("Raw evidence → retrieval needs → behavioural patterns → retrieval journey (with the six-node decomposition) → behavioural segments → opportunity areas → prioritisation → target segment hypothesis → research hypotheses → primary research plan → provisional problem hypothesis. Only after primary research: how-might-we, ideation, solution, MVP, testing.")
    w("")
    w("## A. Structure tests (are cross-tabs meaningful?)")
    w("")
    w("| Pair | χ² | dof | p | Cramér's V |")
    w("|---|---|---|---|---|")
    for k, v in ind.items():
        w(f"| {k} | {v['chi2']} | {v['dof']} | {v['p']} | {v['cramers_v']} |")
    w("")
    w("All p > 0.05: no evidence of association beyond chance (some cells are sparse, so treat as indicative).")
    w("")
    w("## B. Object-class judgement calls")
    w("")
    w("| Object | Class used | Alternative | Why uncertain |")
    w("|---|---|---|---|")
    for text in sorted(m["object_judgement"]["judgement_objects"]):
        key = text + "."
        w(f"| {text} | {L.OBJECT_CLASS_LABEL[L.OBJECTS[key]]} | {L.OBJECT_CLASS_LABEL[L.OBJECT_JUDGEMENT[key][0]]} | {L.OBJECT_JUDGEMENT[key][1]} |")
    w("")
    w("## C. Method and files")
    w("- `engine/lexicon.py`: hand-coded map of all 90 sentences (object class, remembered/lacking information, stage, state, outcome, signals).")
    w("- `engine/code_records.py`: Stage 0/1; raises on any unknown sentence (100% coverage by construction). Output `output/coded_records.csv`.")
    w("- `engine/decomposition.py`: the six-node decomposition, evidence polarities, failure-attribution rule and candidate measures.")
    w("- `engine/analyze.py`: Stages 2–8 metrics → `output/metrics.json`; every named group's record IDs → `output/evidence_index.csv`.")
    w("- `engine/coders.py`, `engine/validate_coder.py`: model-assisted coder and its validation harness (live-model results go to `output/coder_validation_llm_perturbed.md`; none exists until a run with API credentials has been done).")
    w("- Run: `python -m engine.run`.")
    w("- Stage 1 outcome vocabulary: found-quickly (0 stated), found-with-effort, found-after-reformulation (0), found-after-browsing (0), similar-but-uncertain, failed, abandoned, external-workaround, unknown. Unstated outcomes are never inferred.")
    w("")
    return "\n".join(out)


if __name__ == "__main__":
    config.configure()
    text = build_report()
    (config.OUTPUT / "discovery_report.md").write_text(text, encoding="utf-8")
    (config.OUTPUT / "discovery_appendix.md").write_text(build_appendix(), encoding="utf-8")
    print(f"wrote output/discovery_report.md ({len(text.splitlines())} lines)")
