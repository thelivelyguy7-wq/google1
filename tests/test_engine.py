"""Invariant, snapshot and guardrail tests for the discovery engine. Run: python -m pytest tests -q"""
import random
import re
from types import SimpleNamespace

import pytest

from engine import decomposition as DC
from engine.analyze import compute
from engine.coders import Coding, LexiconCoder, LLMCoder, Quote, grounded
from engine.report import build_appendix, build_report
from engine.validate_coder import cohen_kappa, compare, perturb, truth_from_lexicon


@pytest.fixture(scope="module")
def run():
    m, df, r = compute()
    return m, df, r


@pytest.fixture(scope="module")
def report():
    return build_report()


# ------------------------------------------------------------------ invariants
def test_every_record_is_coded_and_classified(run):
    m, df, r = run
    s0 = m["stage0"]
    assert (s0["total"], s0["relevant"], s0["possibly"], s0["irrelevant"]) == (840, 800, 3, 37)
    assert len(df) == 840 and len(r) == 800


def test_segments_partition_the_relevant_records(run):
    m, _, _ = run
    four = [v["n"] for k, v in m["segments"].items() if not k.startswith("SEG-T")]
    assert sum(four) == 800
    seg_t = next(v["n"] for k, v in m["segments"].items() if k.startswith("SEG-T"))
    assert seg_t == m["segments"]["SEG-2 Recovery-dependent retrievers"]["n"] + m["segments"]["SEG-3 Candidate-inspection-dependent retrievers"]["n"]


def test_outcome_counts_sum_and_never_inferred(run):
    m, _, _ = run
    assert sum(m["outcome_all"].values()) == 800
    assert m["outcome_all"]["found_quickly"] == 0          # the corpus states no quick success; it must not be inferred
    assert m["stage1"]["outcome_stated"] == 210


def test_evidence_index_matches_every_named_count(run):
    m, _, _ = run
    for group, prefix in (("needs", "need"), ("segments", "seg"), ("opps", "opp")):
        for k, v in m[group].items():
            assert len(m["evidence_index"][f"{prefix}:{k.split()[0]}"]) == v["n"], k


def test_headline_snapshot(run):
    m, _, _ = run
    assert m["target"]["n"] == 503
    assert m["stage1"]["express_barrier"] == 322
    assert m["journey"]["breakdown"]["RECOVER"]["n"] == 371


def test_structure_tests_show_no_association_beyond_chance(run):
    m, _, _ = run
    assert all(v["p"] > 0.05 for v in m["independence"].values())


# ------------------------------------------------------------------ decomposition
def test_decomposition_has_no_explicit_evidence_that_the_product_misread_clues(run):
    m, _, _ = run
    assert m["decomposition"]["D3"]["breakdown"] == 0      # the finding that the case's question 2 is unanswerable here
    assert m["decomposition"]["D6"]["breakdown"] == 0


def test_every_node_maps_to_an_opportunity_and_measure():
    assert set(DC.NODES) == {"D1", "D2", "D3", "D4", "D5", "D6"}
    for n in DC.NODES.values():
        assert n["opportunity"] and n["proposed_measure"] and n["brief_question"]
    assert [n for n, _ in DC.ATTRIBUTION_RULES] == ["D6", "D1", "D2", "D3", "D4", "D5"]


def test_object_class_is_not_forced(run):
    _, _, r = run
    truck = r[r["object_text"] == "a yellow truck"]
    assert set(truck["object_class"]) == {"unspecified_object"}
    assert (r["object_class_basis"] == "judgement").any()


# ------------------------------------------------------------------ report guardrails
def test_report_uses_the_six_epistemic_labels(report):
    for tag in ("[RAW]", "`[OBS-SYN]`", "`[INTERP]`", "`[OPP-HYP]`", "`[PROB-HYP]`", "`[VALIDATED]`"):
        assert tag in report, tag
    # every observed count is marked synthetic (rule 20); bare [OBS] and the old merged [HYP] must not return
    assert "`[OBS]`" not in report and "`[HYP]`" not in report


def test_report_has_exactly_the_thirteen_sections_and_appendix_is_separate(report):
    heads = re.findall(r"^## (\d+)\. ", report, flags=re.M)
    assert heads == [str(i) for i in range(1, 14)]
    assert "Appendix" not in report
    assert "# Discovery Report" in build_appendix()


def test_report_sections_carry_record_ids(report):
    parts = re.split(r"^## ", report, flags=re.M)
    by_num = {p.split(".")[0]: p for p in parts[1:]}
    for num in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "12", "13"):
        assert re.search(r"SIM-\d{4}", by_num[num]), f"section {num} has no record IDs"


def test_problem_statement_has_no_solution_language(report):
    sec = report.split("## 12. Problem Definition")[1].split("## 13.")[0]
    stmt = next(l for l in sec.splitlines() if l.startswith(">")).lower()
    for word in ("ai ", "semantic", "chatbot", "assistant", "metadata", "embedding", "feature"):
        assert word not in stmt
    assert "PROVISIONAL PROBLEM HYPOTHESIS" in sec


def test_synthetic_and_not_findings_banners_present(report):
    assert "SYNTHETIC / REPRESENTATIVE DATASET" in report
    assert "NOT RESEARCH FINDINGS" in report
    assert "TARGET SEGMENT HYPOTHESIS — TO BE VALIDATED" in report


def test_every_task_records_the_six_primary_measures(report):
    sec = report.split("### 10.3")[1].split("### 10.4")[0]
    for measure in ("retrieval success", "time to successful retrieval", "attempts/reformulations",
                    "candidate photos inspected", "abandonment", "confidence"):
        assert measure in sec.lower()
    assert sec.count("| T") >= 10                          # design table and measures table, five tasks each


# ------------------------------------------------------------------ coder guardrails
def test_lexicon_coder_reads_original_but_not_reworded_text(run):
    _, df, _ = run
    text = df.loc[df["relevance"] == "retrieval_related", "raw_text"].iloc[0]
    assert LexiconCoder().code(text) is not None
    assert LexiconCoder().code(perturb(text, random.Random(1))) is None     # uncoded, never guessed


def test_validation_harness_scores_perfect_and_degraded_coders():
    import pandas as pd
    texts = pd.read_csv("google_photos_raw_dataset.csv")["text"].head(60).tolist()
    truth = truth_from_lexicon(pd.DataFrame({"text": texts}))
    perfect = compare(texts, truth, truth)
    assert perfect["outcome"]["kappa"] == pytest.approx(1.0) and perfect["all_single_fields_correct_of_n"] == 1.0
    wrong = [Coding(**{**t.model_dump(), "outcome": "failed"}) for t in truth]
    assert compare(texts, truth, wrong)["outcome"]["accuracy"] < 1.0
    none_coded = compare(texts, truth, [None] * len(texts))
    assert none_coded["uncoded"] == len(texts) and none_coded["coded"] == 0


def test_kappa_is_zero_for_chance_agreement_and_one_for_identical():
    assert cohen_kappa(list("aabb"), list("aabb")) == pytest.approx(1.0)
    assert cohen_kappa(list("abab"), list("aabb")) == pytest.approx(0.0)


def test_grounding_rejects_invented_quotes_and_unsupported_fields():
    text = "I could not find it."
    fabricated = Coding(relevance="retrieval_related", outcome="failed", quotes=[Quote(field="outcome", text="I gave up completely.")])
    assert not grounded(text, fabricated)["ok"]
    unsupported = Coding(relevance="retrieval_related", outcome="failed", quotes=[])
    assert grounded(text, unsupported)["unsupported_fields"] == ["outcome"]
    good = Coding(relevance="retrieval_related", outcome="failed", quotes=[Quote(field="outcome", text=text)])
    assert grounded(text, good)["ok"]


def _fake_client(stop_reason="end_turn", parsed=None):
    class FakeContent:
        parts = ["foo"]
    class FakeCandidate:
        content = FakeContent()
        
    if stop_reason == "refusal":
        candidates = []
        text = ""
    else:
        candidates = [FakeCandidate()]
        if parsed is None:
            text = "invalid json"
        else:
            text = parsed.model_dump_json()

    resp = SimpleNamespace(candidates=candidates, text=text)
    return SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kw: resp))


def test_llm_coder_handles_refusal_and_unparsed_output_without_guessing():
    ok = Coding(relevance="not_retrieval_related")
    assert LLMCoder(client=_fake_client(parsed=ok)).code("x") == ok
    refused = LLMCoder(client=_fake_client(stop_reason="refusal"))
    assert refused.code("x") is None and refused.stats["refused"] == 1
    empty = LLMCoder(client=_fake_client(parsed=None))
    assert empty.code("x") is None and empty.stats["invalid"] == 1


def test_llm_coder_default_model_is_configurable(monkeypatch):
    monkeypatch.setenv("DISCOVERY_CODER_MODEL", "gemini-1.5-pro")
    assert LLMCoder(client=_fake_client()).model == "gemini-1.5-pro"
    monkeypatch.delenv("DISCOVERY_CODER_MODEL")
    assert LLMCoder(client=_fake_client()).model == "gemini-3.6-flash"


# ------------------------------------------------------------------ second-audit gaps
def test_stage_10b_observation_fields_are_logged(report):
    sec = report.split("### 10.3")[1].split("### 10.4")[0].lower()
    for field in ("first action", "first query", "reformulation", "filters used", "browsing behaviour",
                  "candidates inspected", "time to success", "confidence", "abandonment", "workaround"):
        assert field in sec, field


def test_information_discovery_opportunity_is_assessed(run, report):
    m, _, _ = run
    assert any(k.startswith("O8 Information discovery") for k in m["opps"])
    assert "### O8 Information discovery" in report
    assert "| **O8 Information discovery" in report


def test_severity_signals_are_shown_per_segment(report):
    sec = report.split("**Severity signals by segment**")[1].split("Severity-signal vocabulary")[0]
    for seg in ("SEG-1", "SEG-2", "SEG-3", "SEG-4", "SEG-T"):
        assert f"| {seg} |" in sec
    assert "strategy switch" in sec and "abandonment" in sec


def test_methods_are_mapped_to_where_how_much_versus_why_how(report):
    assert "quantitative evidence answers WHERE and HOW MUCH; qualitative research answers WHY and HOW" in report
    assert report.count("**Qualitative (WHY/HOW):**") == 7 and report.count("**Quantitative (WHERE/HOW MUCH):**") == 7


def test_only_a_short_preface_precedes_section_one(report):
    pre = report.split("## 1. Dataset Quality")[0]
    lines = [l for l in pre.splitlines() if l.strip()]
    assert lines[0].startswith("# ") and len(lines) <= 8
    assert "Chain followed" not in report and "Discovery chain followed" in build_appendix()


# ------------------------------------------------------------------ phase 2: sensitivity and decision log
@pytest.fixture(scope="module")
def sensitivity_text(run):
    from engine.sensitivity import write_sensitivity
    return write_sensitivity(run)


@pytest.fixture(scope="module")
def decision_log_text(run):
    from engine.sensitivity import write_decision_log
    return write_decision_log(run)


def test_sensitivity_reports_every_target_variant(sensitivity_text, run):
    m, _, r = run
    from engine.sensitivity import target_variants
    tv = target_variants(r)
    assert len(tv) == 6 and tv[0]["n"] == m["target"]["n"]
    # splitting the pooled segment must leave neither half a majority: that is why it is pooled
    assert not tv[1]["largest"] and not tv[2]["largest"]
    # duplicate removal must not move the conclusion
    assert tv[3]["largest"] and tv[4]["largest"]
    for v in tv:
        assert v["variant"] in sensitivity_text


def test_sensitivity_names_threshold_dependent_labels(sensitivity_text, run):
    from engine.sensitivity import ranking_variants
    _, _, r = run
    rv = ranking_variants(r)
    assert rv["order"][0] == "O5"                                  # the selected opportunity leads on frequency
    assert all(rv["labels"][s]["O5"] == "High" for s in rv["labels"])
    unstable = [k for k in rv["order"] if len({rv["labels"][s][k] for s in rv["labels"]}) > 1]
    assert unstable and all(k in sensitivity_text for k in unstable)


def test_decision_log_prices_each_judgement(decision_log_text):
    for decision in ("Off-topic records excluded", "counted as an exit path", "never inferred",
                     "Opener sentences excluded", "D3 left at zero", "pooled into one target segment"):
        assert decision in decision_log_text, decision
    assert decision_log_text.count("|") > 50                       # a real table, not a stub


# ------------------------------------------------------------------ phase 1: configurable paths
def test_engine_runs_against_a_different_corpus(tmp_path):
    import subprocess
    import sys
    import pandas as pd
    src = pd.read_csv("google_photos_raw_dataset.csv")
    small = tmp_path / "small.csv"
    src.head(50).to_csv(small, index=False)
    out = tmp_path / "out"
    proc = subprocess.run([sys.executable, "-m", "engine.run", "--input", str(small), "--output", str(out), "--no-site"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert (out / "discovery_report.md").exists() and (out / "coded_records.csv").exists()
    assert len(pd.read_csv(out / "coded_records.csv")) == 50


# ------------------------------------------------------------------ phase 3: the web app
import json as _json
from pathlib import Path as _Path


@pytest.fixture(scope="module")
def site(run):
    from engine.export_site import export_site
    export_site(run)
    raw = _Path("site/site_data.js").read_text(encoding="utf-8")
    return _json.loads(raw.split("= ", 1)[1].rstrip().rstrip(";"))


APP_JS = _Path("site/app.js").read_text(encoding="utf-8")


def test_site_data_carries_every_metric_the_pages_read(site, run):
    m, df, _ = run
    for key in ("stage0", "stage1", "needs", "segments", "opps", "journey", "decomposition", "target",
                "impact", "outcome_all", "behavior_groups", "stage_questions", "independence", "narrative"):
        assert key in site, key
    assert len(site["records"]["rows"]) == len(df)
    assert site["derived"]["relevant"] == m["stage0"]["relevant"]


def test_every_ui_count_matches_the_computed_metrics(site, run):
    m, _, _ = run
    for group, prefix in (("needs", "need"), ("segments", "seg"), ("opps", "opp")):
        for k, v in m[group].items():
            assert len(site["evidence_index"][f"{prefix}:{k.split()[0]}"]) == v["n"], k
    assert site["stage0"] == m["stage0"] and site["target"]["n"] == m["target"]["n"]


def test_app_js_hard_codes_no_headline_number(run):
    """The previous engine's dashboard kept ranking numbers in JS and they went stale. This forbids that."""
    m, _, _ = run
    headline = {m["stage0"]["total"], m["stage0"]["relevant"], m["target"]["n"], m["stage1"]["express_barrier"],
                m["journey"]["breakdown"]["RECOVER"]["n"], m["decomposition"]["D4"]["breakdown_or_effort"]}
    for n in headline:
        assert re.search(rf"(?<![\w.]){n}(?![\w.])", APP_JS) is None, f"{n} is hard-coded in app.js"


def test_app_js_carries_no_solution_language():
    lowered = APP_JS.lower()
    for word in ("semantic search", "chatbot", "embedding", "ai assistant", "machine learning"):
        assert word not in lowered, word


def test_every_page_shows_denominators_and_the_synthetic_banner():
    html = _Path("site/index.html").read_text(encoding="utf-8")
    flat = " ".join(html.split())
    assert "Synthetic corpus." in flat and "never a Google Photos user statistic" in flat
    assert 'const pct = (n, of)' in APP_JS and '" of " + of' in APP_JS      # counts render as "X of Y"


def test_hypothesis_verdicts_are_untested_until_fieldwork(site):
    hyps = site["narrative"]["hypotheses"]
    assert len(hyps) == 7
    assert {h["verdict"] for h in hyps} == {"untested"}
    for h in hyps:                                  # three separate fields, never merged
        assert h["evidence_for"] and h["evidence_against"] and h["unknown"] and h["rival"]
        assert h["qualitative"] and h["quantitative"]


def test_site_narrative_comes_from_the_same_module_as_the_report(site):
    from engine import narrative as NR
    assert site["narrative"]["needs"] == {k: list(v) for k, v in NR.NEEDS.items()}   # JSON turns tuples into lists
    assert len(site["narrative"]["tasks"]) == len(NR.TASKS)
    assert len(site["narrative"]["interview_guide"]) == len(NR.INTERVIEW_GUIDE)
