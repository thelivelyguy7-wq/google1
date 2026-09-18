"""Mission check: problem statement §20 success criteria + §18 guardrails, against real outputs."""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run from anywhere
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # arrows and section signs on a cp1252 console

from discovery_engine.store import Store
from discovery_engine.validate import quote_is_valid
from discovery_engine.hypotheses import LEADING

DATASET = "google_photos_discovery_contextual_resegmented"
s = Store("data/discovery.db")
b = s.latest_synthesis("discovery")["payload"]
report = Path("reports/discovery_report.md").read_text(encoding="utf-8")
brief = Path("reports/research_brief.md").read_text(encoding="utf-8")
records = {r["record_id"]: r for r in s.q("SELECT record_id, text, title, duplicate_of, dataset FROM records")}
results = []


def check(group, name, ok, detail=""):
    results.append((group, name, bool(ok), detail))


# ---------------- walk the bundle ----------------
rates, evidence = [], []


def walk(x, path="bundle"):
    if isinstance(x, dict):
        if {"numerator", "denominator", "pct"} <= x.keys():
            rates.append((path, x))
        if "quote" in x and "record_id" in x and "source" in x:
            evidence.append((path, x))
        for k, v in x.items():
            walk(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, f"{path}[{i}]")


walk(b)

# ---------------- §20 success criteria ----------------
o = b["overview"]
failing = [f for f in b["failures"] if f["label"] not in ("none_observed", "unclear")]
check("§20", "1 What are users trying to retrieve?", len([x for x in b["scenarios"] if x["label"] != "other"]) >= 5, f"{len(b['scenarios'])} scenarios")
check("§20", "2 What do they remember?", len(b["memory"]) >= 5 and all(m["examples"] for m in b["memory"][:5]), f"{len(b['memory'])} clue types, top: {b['memory'][0]['label']}")
check("§20", "3 What do they forget?", len(b["forgotten"]) >= 3 and all("unsuccessful_when_forgotten" in f for f in b["forgotten"]), f"{len(b['forgotten'])} gap types, top: {b['forgotten'][0]['label']}")
check("§20", "4 How do they attempt retrieval?", b["search"]["queries_extracted"] > 0 and b["search"]["strategies"], f"{b['search']['queries_extracted']} queries, {len(b['search']['strategies'])} strategies")
check("§20", "5 Where does retrieval fail?", len(failing) >= 4 and b["journey"], f"{len(failing)} failure stages")
check("§20", "6 Why does retrieval fail?", all(set(op["root_cause_chain"]) == {"symptom", "behavior", "barrier", "potential_root_cause"} for op in b["opportunities"]), "root-cause chain on every opportunity")
check("§20", "7 What workarounds do users use?", len(b["workarounds"]) >= 5, f"{len(b['workarounds'])} workarounds")
check("§20", "8 Which segments/scenarios are most affected?",
      len(b["segments"]) == 2 and all("evidence_strength" in x for x in b["segments"]) and len(b["scenarios"]) >= 5,
      f"{len(b['segments'])} behavioural segments, {len(b['scenarios'])} scenarios")
check("§20", "9 Which opportunities have the strongest evidence?", b["opportunities"] and all(op["evidence_strength"]["checks"] for op in b["opportunities"]), ", ".join(f"{op['opportunity']}={op['evidence_strength']['level']}" for op in b["opportunities"][:3]))
check("§20", "10 What evidence supports each opportunity?", all(any(i["evidence"] for i in op["insights"]) for op in b["opportunities"]), "insight evidence on every opportunity")
check("§20", "11 What evidence challenges each opportunity?", all(op["contradictions"] for op in b["opportunities"]), f"{sum(len(op['contradictions']) for op in b['opportunities'])} contradiction groups")
rb = b["research_brief"]
check("§20", "12 What should primary research validate?", rb.get("hypotheses") and rb.get("interview_questions") and rb.get("falsification_signals") and rb.get("unknowns"),
      f"{len(rb.get('hypotheses', []))} hypotheses, {len(rb.get('interview_questions', []))} questions")

# ---------------- §18 guardrails ----------------
bad_rates = [p for p, r in rates if r["denominator"] and r["pct"] is not None and abs(round(100 * r["numerator"] / r["denominator"], 1) - r["pct"]) > 0.05]
check("§18", "Every rate carries numerator/denominator and a consistent %", not bad_rates and all(r.get("denominator_definition") is not None for _, r in rates), f"{len(rates)} rates checked, {len(bad_rates)} inconsistent")
check("§18", "No rate exceeds its denominator", all(r["numerator"] <= r["denominator"] for _, r in rates if r["denominator"]))
check("§18", "Funnel is monotonic", o["unique_records"] <= o["total_records"] and o["relevant"]["numerator"] <= o["unique_records"] and o["retrieval_attempts"]["numerator"] <= o["relevant"]["numerator"],
      f"{o['total_records']} → {o['unique_records']} → {o['relevant']['numerator']} → {o['retrieval_attempts']['numerator']}")

unverifiable, dup_cited, foreign = [], [], []
for p, e in evidence:
    rec = records.get(e["record_id"])
    if rec is None or rec["dataset"] != DATASET:
        foreign.append(e["record_id"]); continue
    if rec["duplicate_of"]:
        dup_cited.append(e["record_id"])
    src = f"{rec['title']}\n{rec['text']}" if rec["title"] else rec["text"]
    if e.get("kind") != "advice" and e.get("quote") and not quote_is_valid(e["quote"], src):
        unverifiable.append((e.get("evidence_id"), e["quote"][:60]))
check("§18", "Every cited quote is found verbatim in its source record", not unverifiable, f"{len(evidence)} cited quotes, {len(unverifiable)} not found")
check("§18", "Evidence comes only from the raw dataset", not foreign, f"{len(foreign)} foreign record ids")
check("§18", "No evidence cited from duplicate records", not dup_cited, f"{len(dup_cited)} duplicates cited")

rate_keys = {(r["numerator"], r["denominator"]) for _, r in rates}
extra = set()
for op in b["opportunities"]:  # counts also appear as plain integers in insight text
    extra |= {(op["unsuccessful"]["numerator"], op["unsuccessful"]["denominator"])}
report_fracs = [(int(n), int(d)) for n, d in re.findall(r"(\d+)/(\d+) \(\d+(?:\.\d+)?%\)", report)]
untraced = [f for f in report_fracs if f not in rate_keys | extra]
check("§18", "Every 'n/d (x%)' in the report traces to the bundle", not untraced, f"{len(report_fracs)} figures, {len(untraced)} untraced {untraced[:5]}")

SOLUTION = re.compile(r"\b(chatbot|assistant|conversational|feature|build|add (a|an)|AI-powered|semantic search|redesign)\b", re.I)
sol_hits = [(op["opportunity"], m.group(0)) for op in b["opportunities"] for m in [SOLUTION.search(op["opportunity"] + " " + op["description"])] if m]
sol_hits += [("hypothesis:" + h["opportunity"], m.group(0)) for h in b["hypotheses"] for m in [SOLUTION.search(h["we_believe"] + " ".join(h["we_expect_to_observe"]))] if m]
check("§18", "No solution language in opportunities or hypotheses", not sol_hits, str(sol_hits[:4]))
_d, _pd = b.get("decomposition") or {}, b.get("problem_definition") or {}
outcome_hits = [(x["stage"], m.group(0)) for x in _d.get("stages", [])
                for m in [SOLUTION.search(x["product_outcome"] + " " + x["outcome_detail"])] if m]
outcome_hits += [("problem:" + k, m.group(0)) for k, v in _pd.items() if isinstance(v, dict) and v.get("text")
                 for m in [SOLUTION.search(v["text"])] if m]
check("§18", "No solution language in stage outcomes or problem definition", not outcome_hits, str(outcome_hits[:4]))
leading = [q for q in rb.get("interview_questions", []) if LEADING.search(q)]
check("§18", "Interview questions are behavioural and non-leading", not leading and any("last time" in q.lower() for q in rb["interview_questions"]), f"{len(leading)} leading")
check("§18", "Research brief contains no invented findings", "Not yet collected" in brief and rb["status"].startswith("PLAN ONLY"))
check("§18", "Brief tests the proposed lead", b["leading"]["leading"] in {h["opportunity"] for h in rb["hypotheses"]}, f"lead={b['leading']['leading']}")
levels = {i["level"] for op in b["opportunities"] for i in op["insights"]} | {v["level"] for op in b["opportunities"] for v in op["root_cause_chain"].values()}
check("§18", "Epistemic levels kept separate (OBSERVATION/INSIGHT/HYPOTHESIS)", {"OBSERVATION", "INSIGHT", "HYPOTHESIS"} <= levels, str(sorted(levels)))
check("§18", "JTBD labelled as interpretation", all(j["level"] == "INTERPRETATION" for j in b["jtbd"]))
prov = b["provenance"]
if prov["flagged_records"]:
    check("§18", "Flagged data is disclosed in report and brief", "SIMULATED" in report and "SYNTHETIC" in brief, f"{prov['flagged_records']} flagged")
else:
    unsupported = [w for w in ("SYNTHETIC", "SIMULATED", "real users", "collected from") if w in report or w in brief]
    check("§18", "Neutral provenance: dataset named, no claim either way",
          prov["datasets"] == [DATASET] and not unsupported, f"mode={prov['mode']}, unsupported claims={unsupported}")
check("§18", "Sentiment not used to rank opportunities", "sentiment" not in json.dumps(b["leading"]).lower())
check("§18", "Leading opportunity presented as a proposal", "proposal" in b["leading"]["rule"].lower())
check("§22", "Only the current dataset is in the database", [r["dataset"] for r in s.q("SELECT DISTINCT dataset FROM records")] == [DATASET])
# Reference-label comparison (Store.reference_labels + the "Engine vs the dataset's own labels" report
# section) is designed but not built: Store has no reference_labels() method, and no
# f"{DATASET}.csv" reference file with a labeller's own columns exists at the project root
# (Book16.csv exists but is named differently and was never wired to this DATASET constant, and its
# 42 labeller-commentary rows would need stripping before ingest for the second check below to hold).
# Recorded as a single explicit gap rather than crashing the rest of this script.
if hasattr(s, "reference_labels") and (Path(__file__).resolve().parents[1] / f"{DATASET}.csv").exists():
    labels = s.reference_labels(DATASET)
    label_cols = sorted({k for v in labels.values() for k in v})
    # Column names and the dataset's own label values must never appear in what the analyzer reads.
    label_values = sorted({v for lab in labels.values() for k, v in lab.items()
                           if k in ("primary_retrieval_mode", "retrieval_complexity", "retrieval_outcome_effort") and v != "Not applicable"})
    probes = label_cols + label_values + ["Not retrieval-related", "The user remembers"]
    leak = s.q("SELECT COUNT(*) n FROM chunks WHERE " + " OR ".join("instr(text, ?) > 0" for _ in probes), tuple(probes))[0]["n"]
    check("§22", "Labels, label values and the labeller's sentences never reach analyzer input", leak == 0,
          f"{leak} chunks contain label text ({len(probes)} probes)")
    check("§22", "The dataset's own labels are stored for comparison, one row per record",
          len(labels) == len(records) and "primary_retrieval_mode" in label_cols, f"{len(labels)} of {len(records)} records, {len(label_cols)} label columns")
    _src = {r["source_id"]: r["text"] for r in s.q("SELECT source_id, text FROM records")}
    import pandas as _pd
    _orig = _pd.read_csv(Path(__file__).resolve().parents[1] / f"{DATASET}.csv", dtype=str, keep_default_na=False)
    _touched = [(i, t) for i, t in zip(_orig.id, _orig.text) if _src.get(i) is not None and _src[i] != t]
    check("§22", "Ingested text differs from the file only where the labeller's sentences were removed",
          all("The user remembers" in t for _, t in _touched), f"{len(_touched)} texts restored, all of them carried the appended sentence")
else:
    check("§22", "Reference-label comparison against the dataset's own labels (Store.reference_labels)",
          False, "NOT IMPLEMENTED: no reference_labels() method on Store and no {DATASET}.csv reference file at project root")

# ---------------- case study Part 2: the business metric broken down ----------------
d = b.get("decomposition") or {}
stages = [x for x in d.get("stages", []) if x["breaks_here"]["numerator"]]
check("Part 2", "Business metric is decomposed into stage outcomes", len(stages) >= 5 and all(x["product_outcome"] for x in stages),
      f"{len(stages)} stages with measured breakdowns")
check("Part 2", "Stage breakdowns never exceed the attempts they are drawn from",
      all(x["breaks_here"]["numerator"] <= d["baseline"]["denominator"] and x["unresolved_here"]["numerator"] <= x["breaks_here"]["numerator"] for x in stages))
check("Part 2", "Stage shares plus 'no breakdown' and 'unclear' account for every attempt",
      abs(sum(x["breaks_here"]["numerator"] for x in stages) + d["no_breakdown_described"]["numerator"] + d["breakdown_unclear"]["numerator"] - d["baseline"]["denominator"]) <= 1,
      f"{sum(x['breaks_here']['numerator'] for x in stages)} + {d['no_breakdown_described']['numerator']} + {d['breakdown_unclear']['numerator']} of {d['baseline']['denominator']}")
STAGE_MODEL = ["recall", "express", "match", "recognize", "recover"]
check("Part 2", "The journey is the five-stage model, in order",
      [x["stage"] for x in d.get("stages", []) if x["in_journey"]] == STAGE_MODEL,
      " -> ".join(STAGE_MODEL))
check("Part 2", "Every stage states the user capability it stands for",
      all(x.get("condition") for x in d.get("stages", [])))
check("Part 2", "Data and index is reported outside the user's journey",
      not next(x for x in d["stages"] if x["stage"] == "data")["in_journey"])
_match = next((x for x in d["stages"] if x["stage"] == "match"), None)
check("Part 2", "A merged stage shows the failure codes underneath it",
      _match and sum(cp["breaks_here"]["numerator"] for cp in _match["components"]) == _match["breaks_here"]["numerator"],
      ", ".join(f"{cp['code'][0]}={cp['breaks_here']['numerator']}" for cp in (_match or {}).get("components", [])))
check("Part 2", "Headroom is labelled an upper bound, not a forecast",
      "INTERPRETATION" in d.get("headroom_note", "") and "upper bound" in d.get("headroom_note", ""))
check("Part 2", "Each stage names the opportunity areas that sit under it", all(x["opportunities"] for x in stages))
check("Part 2", "Opportunities are ranked by recoverable share, not by volume alone",
      d["ranked_by_headroom"][0] == d["largest_headroom"]["stage"], f"largest={d['largest_headroom']['stage']} (+{d['largest_headroom']['max_headroom_pts']} pts)")

# ---------------- case study Part 3: methodology ----------------
m = rb.get("methodology") or {}
check("Part 3", "A method is named and justified", m.get("method") and len(m.get("why", [])) >= 3, m.get("method", "")[:60])
check("Part 3", "Alternatives are considered and rejected with a reason",
      len(m.get("alternatives_considered", [])) >= 3 and all(a["rejected_because"] for a in m.get("alternatives_considered", [])),
      f"{len(m.get('alternatives_considered', []))} alternatives")
check("Part 3", "Sample size matches the brief (5-6 interviews)", "5" in m.get("participants", "") and "6" in m.get("participants", ""))
check("Part 3", "Sessions are coded with the engine's own taxonomy so results compare",
      any("taxonomy" in x for x in m.get("analysis", []) + m.get("instrumentation", [])))
check("Part 3", "Validity threats are stated with mitigations",
      len(m.get("validity_threats", [])) >= 3 and all("Mitigation" in x for x in m.get("validity_threats", [])))
check("Part 3", "Methodology reaches the brief that gets handed off", "## Methodology" in brief and m.get("method", "x")[:30] in brief)

# ---------------- segments: binary primary (Direct/Contextual) + three secondary lenses ----------------
so = b["segment_overview"]
attempts_n = so["attempts"]
SEGMENTS = ["Direct Retrieval", "Contextual Retrieval"]
check("Segments", "The two primary segments exist, and are exhaustive", [x["segment"] for x in b["segments"]] == SEGMENTS,
      " / ".join(x["segment"] for x in b["segments"]))
check("Segments", "Every attempt is placed exactly once (binary partition sums to all attempts)",
      sum(x["records"] for x in b["segments"]) == attempts_n
      and len({r for x in b["segments"] for r in x["record_ids"]}) == sum(x["records"] for x in b["segments"]),
      f"{sum(x['records'] for x in b['segments'])} = {attempts_n}")
# Recovery-dependent means the initial attempt failed: recompute from the stored analyses, independently of the bundle.
from discovery_engine.quant import Corpus as _Corpus
from discovery_engine import behavior_segments as _bs
_c = _Corpus(s, b["params"]["include_synthetic"])  # match the scope the loaded bundle was actually built with
_cls = _bs.classify(_c)
_rec = [v for v in _cls.values() if v["secondary"]["retrieval_state"] == "recovery_dependent"]
def _failed_first(v):
    p = v["analysis"]["payload"]
    q = [x for x in _c.signals_by_analysis[v["analysis"]["analysis_id"]] if x["kind"] == "query"]
    return (any(str(x.get("precision", "")).split("|")[-1] in ("not_found", "wrong_results", "too_many_results") for x in q)
            or p.get("failure_stage") not in (None, "none_observed", "unclear")
            or p.get("success_status") in ("not_found", "abandoned", "partially_found", "uncertain"))
_rec_state = next(x for x in b["retrieval_states"] if x["key"] == "recovery_dependent")
check("Segments", "Every Recovery-dependent attempt shows its first attempt failed (a route change after a working search is not recovery)",
      len(_rec) == _rec_state["records"] and all(_failed_first(v) for v in _rec),
      f"{sum(_failed_first(v) for v in _rec)}/{len(_rec)}")
check("Segments", "Every segment states its definition and the rule that places an attempt there",
      all(x["definition"] and x["rule"] for x in b["segments"]) and so["rules"]["precedence"])
check("Segments", "Every segment shows the behaviour in the users' own words",
      all(len(x["defining_evidence"]) >= 2 for x in b["segments"]))
check("Segments", "Defining quotes are not repeated within a segment",
      all(len({" ".join(e["quote"].lower().split()) for e in x["defining_evidence"]}) == len(x["defining_evidence"]) for x in b["segments"]))
check("Segments", "Retrieval states (candidate-heavy, recovery-dependent, unresolved, unavailable, direct/low-effort) sum to all attempts",
      sum(x["records"] for x in b["retrieval_states"]) == attempts_n,
      "; ".join(f"{x['state']} {x['records']}" for x in b["retrieval_states"]))
check("Segments", "Direct's small share is explained as a property of the corpus", "corpus" in so["note_on_direct"])
check("Segments", "Impact mapping and the target-segment hypothesis are stated", bool(so.get("impact_map", {}).get("who")) and bool(so.get("target_segment_hypothesis")))
check("Segments", "A stale target choice is set aside rather than carried into the plan",
      not b.get("target_segment_stale") or b.get("target_segment") is None,
      f"stale={b.get('target_segment_stale')!r}")
for lens, L in so["secondary"].items():
    check("Segments", f"Secondary lens '{L['name']}' places every attempt once",
          sum(c["rate"]["numerator"] for c in L["categories"]) == attempts_n
          and all(sum(v["numerator"] for v in L["by_segment"][x["key"]].values()) == x["records"] for x in b["segments"]),
          f"{len(L['categories'])} categories")
ms = so["secondary"]["memory_state"]["categories"]
check("Segments", "Lens find rates use only attempts that state an outcome",
      all(c["found"]["denominator"] <= c["rate"]["numerator"] for c in ms)
      and any(c["found"]["denominator"] < c["rate"]["numerator"] for c in ms))
cx = {c["key"]: c["found"]["pct"] for c in so["secondary"]["complexity"]["categories"]}
check("Segments", "Retrieval complexity is not flat: the lens carries information about outcome",
      len({round(cx["low"], 1), round(cx.get("medium", cx["low"]), 1), round(cx["high"], 1)}) > 1,
      f"low {cx['low']}%, medium {cx.get('medium')}%, high {cx['high']}%")
check("Segments", "Segments and lenses reach the written report",
      "## 10. Retrieval Segments (by user behaviour)" in report and "### Secondary segmentation" in report)

# ---------------- engine vs the dataset's own labels ----------------
rc = b.get("reference_comparison") or {}
check("Labels", "The comparison covers every unique record once",
      rc and sum(rc["cells"][l][e] for l in rc["label_order"] for e in rc["engine_order"]) == rc["records"] == len([r for r in records.values() if not r["duplicate_of"]]),
      f"{rc.get('records')} records")
check("Labels", "Every comparison cell drills into exactly its records",
      rc and all(len(rc["record_ids"][l][e]) == rc["cells"][l][e] for l in rc["label_order"] for e in rc["engine_order"]))
check("Labels", "Where the labels say Contextual and the engine does not, the engine's contextual reading is reported",
      rc and rc["contextual_elsewhere"] and all(0 <= x["engine_sees_contextual_memory"] <= x["records"] for x in rc["contextual_elsewhere"]),
      "; ".join(f"{x['engine']} {x['engine_sees_contextual_memory']}/{x['records']}" for x in rc.get("contextual_elsewhere", [])))
check("Labels", "The comparison says neither side is ground truth", "ground truth" in rc.get("note", ""))
check("Labels", "The comparison reaches the report", "### Engine vs the dataset's own labels" in report)

# ---------------- Part 3: research fit per segment ----------------
rf = b.get("research_fit") or {}
seg_names = {x["segment"] for x in b["segments"]}
check("Part 3", "Every segment carries a research fit", set(rf) == seg_names, f"{len(rf)} of {len(seg_names)} segments")
check("Part 3", "Every segment has a screener with a must-be-yes qualifier",
      all(f["screener"] and any("must be" in q for q in f["screener"]) for f in rf.values()))
check("Part 3", "Screeners ask for a recent incident, not a habit",
      all(any("last 3 months" in q for q in f["screener"]) for f in rf.values()))
check("Part 3", "Screeners exclude domain insiders", all(any("machine learning" in q for q in f["screener"]) for f in rf.values()))
sens_high = [n for n, f in rf.items() if f["sensitivity"]["level"] == "high"]
check("Part 3", "High-sensitivity segments run without a screen share",
      all(any("No screen share" in c for c in rf[n]["session_shape"]["changes"]) for n in sens_high),
      f"{len(sens_high)} high-sensitivity segments")
check("Part 3", "Sensitivity is measured against each segment's own attempts",
      all(f["sensitivity"]["rate"]["denominator"] == next(x["records"] for x in b["segments"] if x["segment"] == n) for n, f in rf.items()))
check("Part 3", "Retrieval-state mix is measured per segment, so a choice is not made blind",
      all(0 <= (r.get("pct") or 0) <= 100 for f in rf.values() for r in f["retrieval_states"].values())
      and any(f["retrieval_states"] for f in rf.values()),
      f"{sum(len(f['retrieval_states']) for f in rf.values())} segment x state cells")
check("Part 3", "Every segment has a stated role in the study",
      all(f["role"]["headline"] and f["role"]["why"] for f in rf.values()),
      ", ".join(f"{n.split()[0]}: {f['role']['headline']}" for n, f in rf.items()))
rfs = b.get("research_fit_by_state") or {}
check("Part 3", "Recovery-dependent is not assumed to be fully observable live (abandoned recoveries are recalled)",
      bool(rfs) and rfs["Recovery-dependent"]["observability"]["key"] == "mixed")
check("Part 3", "The session design states what each part buys",
      len(m.get("design", [])) >= 4 and all(d["buys"] for d in m.get("design", [])),
      f"{len(m.get('design', []))} elements")
check("Part 3", "The method produces evidence the corpus cannot: observation and ground truth",
      any("ground truth" in x.lower() for x in m["why"]) and any("resolution" in x.lower() for x in m["instrumentation"]))
check("Part 3", "The earlier retrospective-only plan is recorded as rejected",
      any("Retrospective interview only" in a["method"] for a in m["alternatives_considered"]))
check("Part 3", "The brief's screener is the chosen segment's screener",
      (not b.get("target_segment")) or rb.get("screener") == rf[b["target_segment"]]["screener"],
      f"segment-specific={rb.get('screener_is_segment_specific')}")

# ---------------- case study Part 4: problem definition ----------------
pd = b.get("problem_definition") or {}
FIELDS = ["target_user_segment", "retrieval_scenario", "product_outcome", "root_cause",
          "existing_workarounds", "user_value", "business_rationale"]
check("Part 4", "Problem definition covers every required field", all(pd.get(f, {}).get("text") for f in FIELDS),
      f"{sum(1 for f in FIELDS if pd.get(f, {}).get('text'))}/{len(FIELDS)} fields")
check("Part 4", "Every field carries an epistemic level",
      all(pd[f]["level"] in {"OBSERVATION", "INSIGHT", "INTERPRETATION", "HYPOTHESIS", "GIVEN", "OPEN"} for f in FIELDS),
      ", ".join(sorted({pd[f]["level"] for f in FIELDS})))
check("Part 4", "Root cause is a hypothesis, not a finding", pd["root_cause"]["level"] == "HYPOTHESIS" and pd["root_cause"].get("confirm_in_research"))
BANNED = re.compile(r"users? find it difficult to search for old photos", re.I)
banned_hits = [f for f in FIELDS if BANNED.search(pd[f]["text"])]
check("Part 4", "Problem is not framed as 'users find it difficult to search for old photos'",
      not banned_hits and BANNED.search(pd["not_this_problem"]["text"]) is not None, "explicitly ruled out in 'what this problem is not'")
check("Part 4", "Problem statement names the memory the user still holds",
      any(w in pd["root_cause"]["text"].lower() + pd["retrieval_scenario"]["text"].lower() for w in ("remember", "recall", "retain", "clue")))
check("Part 4", "Business rationale ties back to the metric's headroom",
      pd["product_outcome"].get("max_headroom_pts") is not None and pd["business_rationale"].get("open_questions"),
      f"+{pd['product_outcome'].get('max_headroom_pts')} pts, {len(pd['business_rationale'].get('open_questions', []))} open questions")
check("Part 4", "A competing explanation is named to rule out", bool(pd.get("competing_explanation", {}).get("text")))
check("Part 4", "The evolution from business metric to problem is traceable",
      len(pd.get("evolution", [])) == 5 and "metric" in pd["evolution"][0]["step"].lower() and "problem" in pd["evolution"][-1]["step"].lower(),
      " -> ".join(e["step"] for e in pd.get("evolution", [])))
check("Part 4", "Problem definition is marked a draft awaiting interviews", pd.get("status", "").startswith("DRAFT"))
check("Part 4", "Problem definition reaches the written report", "## 15. Problem Definition" in report and "How the thinking evolved" in report)

width = max(len(n) for _, n, _, _ in results)
fails = 0
for g, n, ok, d in results:
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  [{g}] {n.ljust(width)}  {d}")
print(f"\n{len(results) - fails}/{len(results)} passed")
sys.exit(1 if fails else 0)
