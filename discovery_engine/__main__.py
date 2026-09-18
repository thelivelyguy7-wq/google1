"""CLI: python -m discovery_engine <command>"""
from __future__ import annotations

import argparse
import json
import sys

from .config import ROOT, settings
from .store import Store


def main(argv=None):
    ap = argparse.ArgumentParser(prog="discovery_engine")
    ap.add_argument("--db", default=str(settings.db_path))
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate-synthetic", help="Write the SYNTHETIC dataset (120 rows x 7 sources by default)")
    g.add_argument("--out", default=str(ROOT / "data" / "synthetic"))
    g.add_argument("--per-source", type=int, default=120)
    g.add_argument("--seed", type=int, default=7)

    i = sub.add_parser("ingest", help="Ingest CSV/XLSX/JSON/JSONL/TXT")
    i.add_argument("paths", nargs="+")
    i.add_argument("--source", help="default source name when the file has no 'source' column")
    i.add_argument("--dataset", default="default")
    i.add_argument("--synthetic", action="store_true", help="force is_synthetic=true for every row")

    a = sub.add_parser("analyze", help="Run relevance + extraction + validation")
    a.add_argument("--analyzer", choices=["auto", "claude", "heuristic"], default="auto")
    a.add_argument("--reanalyze", action="store_true")
    a.add_argument("--limit", type=int)
    a.add_argument("--dataset")

    s = sub.add_parser("synthesize", help="Build the discovery bundle and write reports/")
    s.add_argument("--exclude-synthetic", action="store_true")
    s.add_argument("--sources", nargs="*")
    s.add_argument("--refine-hypotheses", action="store_true", help="optional Claude wording pass (citations validated)")
    s.add_argument("--provenance", choices=["auto", "neutral"], help="how outputs describe the data source: auto flags generated records, neutral names only the dataset")

    e = sub.add_parser("evaluate", help="Score analyzer output against synthetic ground truth")
    e.add_argument("--truth", default=str(ROOT / "data" / "synthetic" / "ground_truth.jsonl"))

    q = sub.add_parser("ask", help="Ask a discovery question")
    q.add_argument("question")

    v = sub.add_parser("serve", help="Run the dashboard")
    v.add_argument("--port", type=int, default=8000)
    v.add_argument("--provenance", choices=["auto", "neutral"], help="presentation mode used when the dashboard rebuilds")

    d = sub.add_parser("demo", help="generate-synthetic -> ingest -> analyze (heuristic) -> synthesize -> evaluate")
    d.add_argument("--per-source", type=int, default=120)

    args = ap.parse_args(argv)
    settings.db_path = args.db

    if args.cmd == "generate-synthetic":
        from .synthetic.generate import write_dataset
        print(json.dumps(write_dataset(args.out, args.per_source, args.seed), indent=2))
        return

    if args.cmd == "serve":
        if getattr(args, "provenance", None):
            settings.provenance = args.provenance
        import uvicorn
        from . import server  # noqa: F401  (imports the store at settings.db_path)
        uvicorn.run("discovery_engine.server:app", host="127.0.0.1", port=args.port)
        return

    store = Store(args.db)
    if args.cmd == "ingest":
        from .ingest import ingest_file
        for p in args.paths:
            print(p, json.dumps(ingest_file(store, p, args.source, args.dataset, True if args.synthetic else None)))
    elif args.cmd == "analyze":
        from .analyze.runner import run_analysis
        print(json.dumps(run_analysis(store, args.analyzer, args.reanalyze, args.limit, args.dataset), indent=2))
    elif args.cmd == "synthesize":
        if args.provenance:
            settings.provenance = args.provenance
        from .report import build_bundle, write_reports
        b = build_bundle(store, not args.exclude_synthetic, args.sources)
        if args.refine_hypotheses:
            from .hypotheses import refine_with_claude
            b["hypotheses"] = refine_with_claude(b["hypotheses"])
            store.save_synthesis("discovery", b, b["params"])
        rp, bp = write_reports(b)
        print(f"Report: {rp}\nBrief:  {bp}")
        print(json.dumps({"scope": b["scope"]["label"], "leading": b["leading"] and b["leading"]["leading"],
                          "opportunities": [(o["opportunity"], o["evidence_strength"]["level"], o["records"]) for o in b["opportunities"]]}, indent=2))
    elif args.cmd == "evaluate":
        from .evaluate import evaluate
        print(json.dumps(evaluate(store, args.truth), indent=2))
    elif args.cmd == "ask":
        from .ask import answer
        print(json.dumps(answer(store, args.question), indent=2, default=str)[:20000])
    elif args.cmd == "demo":
        from .analyze.runner import run_analysis
        from .evaluate import evaluate
        from .ingest import ingest_file
        from .report import build_bundle, write_reports
        from .synthetic.generate import write_dataset
        out = ROOT / "data" / "synthetic"
        print(json.dumps(write_dataset(out, args.per_source), indent=2))
        print(json.dumps(ingest_file(store, out / "synthetic_all.jsonl", dataset="synthetic", is_synthetic=True)))
        print(json.dumps(run_analysis(store, "heuristic"), indent=2))
        rp, bp = write_reports(build_bundle(store))
        print(f"Report: {rp}\nBrief:  {bp}")
        print(json.dumps(evaluate(store, out / "ground_truth.jsonl"), indent=2))


if __name__ == "__main__":
    sys.exit(main())
