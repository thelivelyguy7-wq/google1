import json

import pytest

from discovery_engine.analyze.heuristic import HeuristicAnalyzer
from discovery_engine.analyze.runner import run_analysis
from discovery_engine.hypotheses import non_leading
from discovery_engine.ingest import chunk_text, clean_text, ingest_file
from discovery_engine.quant import Corpus, rate
from discovery_engine.report import build_bundle, render_brief, render_report
from discovery_engine.search import EvidenceIndex, Filters
from discovery_engine.store import Store
from discovery_engine.synthetic.generate import MIX, Generator, write_dataset
from discovery_engine.validate import normalize_label, quote_is_valid, validate_analysis


@pytest.fixture()
def store(tmp_path):
    return Store(tmp_path / "t.db")


def test_quote_validation_is_verbatim_but_whitespace_tolerant():
    src = "I searched “beach dinner” and   nothing came up. Gave up."
    assert quote_is_valid('searched "beach dinner" and nothing came up', src)
    assert quote_is_valid("I searched ... nothing came up", src)
    assert not quote_is_valid("I searched for sunset photos", src)
    assert not quote_is_valid("up", src)


def test_unknown_labels_become_proposed_not_forced():
    assert normalize_label("remembered", "place") == "remembered_place"
    assert normalize_label("forgotten", "exact_date") == "exact_date_unknown"
    assert normalize_label("workaround", "prayed to the photo gods") == "proposed:prayed_to_the_photo_gods"


def test_fabricated_quotes_are_flagged_and_excluded(store):
    payload = {"relevant": True, "remembered_information": [
        {"label": "remembered_place", "value": "beach", "quote": "near the beach", "precision": "approximate"},
        {"label": "remembered_person", "value": "mom", "quote": "my mom was there", "precision": "exact"}],
        "failure_stage": "C_retrieval", "failure_quote": "nothing came up", "opportunity_areas": ["build a chatbot"]}
    p, signals, report = validate_analysis(payload, "It was near the beach and nothing came up.", "AN-1", "r1")
    assert report == {"quotes_total": 3, "quotes_invalid": 1}
    assert [s["quote_valid"] for s in signals if s["kind"] == "remembered"] == [1, 0]
    assert p["opportunity_areas"] == ["proposed:build_a_chatbot"]


def test_rate_always_carries_denominator_and_directional_flag():
    x = rate(3, 10, "attempts", {"label": "scope"})
    assert x["numerator"] == 3 and x["denominator"] == 10 and x["pct"] == 30.0 and x["directional"]
    assert rate(0, 0, "none", {"label": "s"})["pct"] is None


def test_clean_text_scrubs_pii_and_chunking():
    assert "[email removed]" in clean_text("mail me at a.b@example.com")
    assert "[number removed]" in clean_text("call +91 98765 43210 now")
    chunks = chunk_text("One. " * 400, 500)
    assert len(chunks) > 1 and all(len(c) <= 500 for c in chunks)


def test_ingest_dedupes_and_is_idempotent(store, tmp_path):
    rows = [{"id": "1", "text": "I searched for the wedding photo and nothing came up at all", "source": "reddit"},
            {"id": "2", "text": "I searched for the wedding photo and nothing came up at all!", "source": "reddit"},
            {"id": "3", "text": "short", "source": "reddit"}]
    p = tmp_path / "x.json"
    p.write_text(json.dumps(rows))
    s1 = ingest_file(store, p)
    assert s1["inserted"] == 2 and s1["exact_duplicates"] == 1 and s1["skipped_short"] == 1
    s2 = ingest_file(store, p)
    assert s2["inserted"] == 0 and s2["already_present"] == 2


def test_generator_counts_and_labels(tmp_path):
    assert all(sum(m.values()) == 120 for m in MIX.values())
    info = write_dataset(tmp_path, per_source=120, seed=1)
    assert info["rows"] == 840 and set(info["by_source"].values()) == {120}
    rows = [json.loads(l) for l in (tmp_path / "synthetic_all.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(r["is_synthetic"] and r["source_url"].startswith("synthetic://") for r in rows)
    assert (tmp_path / "README.md").read_text().startswith("# SYNTHETIC")


def test_heuristic_quotes_are_all_verbatim():
    gen = Generator(3)
    a = HeuristicAnalyzer()
    for i in range(60):
        row, _ = gen.render("reddit", i, "attempt")
        payload, _ = a.analyze(row["text"], {"title": row["title"]})
        source = f"{row['title']}\n{row['text']}"
        _, _, rep = validate_analysis(payload, source, f"AN-{i}", "r")
        assert rep["quotes_invalid"] == 0, payload


def test_noise_is_not_relevant():
    payload, _ = HeuristicAnalyzer().analyze("Storage is full again and now they want me to pay for more.", {})
    assert payload["relevant"] is False


def test_interview_questions_filter_leading():
    qs = ["What did you search first?", "Would you use an AI assistant for this?", "Would you like a feature that understands memories?"]
    assert non_leading(qs) == ["What did you search first?"]


def test_end_to_end_pipeline(store, tmp_path):
    write_dataset(tmp_path, per_source=30, seed=5)
    ingest_file(store, tmp_path / "synthetic_all.jsonl", dataset="synthetic", is_synthetic=True)
    stats = run_analysis(store, "heuristic", progress=lambda *_: None)
    assert stats["analyzed"] > 150 and stats["quotes_invalid"] == 0
    b = build_bundle(store, save=True)
    assert b["scope"]["synthetic_records"] == 210
    for o in b["opportunities"]:
        assert o["evidence_strength"]["level"] in {"HIGH", "MEDIUM", "LOW", "DIRECTIONAL"}
        assert o["records"] == len(o["record_ids"])
        assert any("generated" in c for c in o["evidence_strength"]["caveats"])
    if b["leading"]:
        tested = {h["opportunity"] for h in b["research_brief"]["hypotheses"]}
        assert b["leading"]["leading"] in tested, "research brief must include a hypothesis for the leading opportunity"
    assert "SYNTHETIC / SIMULATED DATA" in render_report(b)  # default provenance mode flags generated records
    assert "Not yet collected" in render_brief(b)
    # exclusion of synthetic data yields an empty but valid corpus
    assert Corpus(store, include_synthetic=False).attempts == []


def test_search_diversifies_sources(store, tmp_path):
    write_dataset(tmp_path, per_source=30, seed=9)
    ingest_file(store, tmp_path / "synthetic_all.jsonl", is_synthetic=True)
    run_analysis(store, "heuristic", progress=lambda *_: None)
    res = EvidenceIndex(store).search("wedding photo", Filters(attempts_only=True), k=7)
    assert res["results"]
    assert len({r["source"] for r in res["results"]}) >= min(4, len(res["source_distribution"]))
    filtered = EvidenceIndex(store).search("", Filters(forgotten=["exact_date_unknown"]), k=5)
    assert all(any(s["kind"] == "forgotten" and s["label"] == "exact_date_unknown" for s in r["signals"]) for r in filtered["results"])


def test_immediate_reanalysis_does_not_collide(store, tmp_path):
    write_dataset(tmp_path, per_source=3, seed=4)
    ingest_file(store, tmp_path / "synthetic_all.jsonl", is_synthetic=True)
    first = run_analysis(store, "heuristic", progress=lambda *_: None)
    second = run_analysis(store, "heuristic", reanalyze=True, progress=lambda *_: None)
    assert second["analyzed"] == first["analyzed"]
    assert store.q("SELECT COUNT(*) n FROM analyses WHERE is_current = 1")[0]["n"] == first["analyzed"]


def test_claude_without_credentials_exits_cleanly(store, monkeypatch):
    import discovery_engine.analyze.runner as runner
    monkeypatch.setattr(runner, "claude_available", lambda: False)
    with pytest.raises(SystemExit) as exc:
        run_analysis(store, "claude", progress=lambda *_: None)
    assert "No Claude credentials" in str(exc.value)


def test_overrides_keep_original_and_apply_on_read(store, tmp_path):
    write_dataset(tmp_path, per_source=5, seed=2)
    ingest_file(store, tmp_path / "synthetic_all.jsonl", is_synthetic=True)
    run_analysis(store, "heuristic", progress=lambda *_: None)
    a = next(x for x in store.current_analyses() if x["relevant"])
    store.add_override("analysis", a["analysis_id"], "relevant", True, False, "PM: not a retrieval post")
    after = next(x for x in store.current_analyses() if x["analysis_id"] == a["analysis_id"])
    assert after["relevant"] == 0 and after["pm_overrides"]
    raw = store.q("SELECT payload FROM analyses WHERE analysis_id = ?", (a["analysis_id"],))[0]
    assert json.loads(raw["payload"])["relevant"] is True
