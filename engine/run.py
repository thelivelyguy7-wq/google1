"""Run the whole pipeline.

    python -m engine.run
    python -m engine.run --input other_corpus.csv --output other_dir
"""
import argparse
import json

import pandas as pd

from . import config
from .analyze import compute
from .export_site import export_site
from .report import build_appendix, build_report
from .sensitivity import write_decision_log, write_sensitivity


def main() -> None:
    ap = argparse.ArgumentParser(description="Product discovery engine: corpus in, evidence-linked report out.")
    config.add_arguments(ap)
    ap.add_argument("--no-site", action="store_true", help="skip regenerating site/site_data.js")
    args = ap.parse_args()
    config.configure(args.input, args.output)
    out = config.OUTPUT

    metrics, df, r = compute()
    precomputed = (metrics, df, r)

    df.to_csv(out / "coded_records.csv", index=False, encoding="utf-8")
    index = metrics["evidence_index"]
    pd.DataFrame([(k, rid) for k, ids in index.items() for rid in ids],
                 columns=["evidence_key", "record_id"]).to_csv(out / "evidence_index.csv", index=False)
    (out / "discovery_report.md").write_text(build_report(precomputed), encoding="utf-8")
    (out / "discovery_appendix.md").write_text(build_appendix(precomputed), encoding="utf-8")
    write_sensitivity(precomputed)
    write_decision_log(precomputed)

    slim = {k: v for k, v in metrics.items() if k != "evidence_index"}     # the index has its own CSV
    (out / "metrics.json").write_text(json.dumps(slim, indent=2, default=int), encoding="utf-8")

    site = "" if args.no_site else f" | site_data.js: {export_site(precomputed)} records"
    print(f"{out}: {len(df)} coded records | {sum(len(v) for v in index.values())} evidence links{site}")


if __name__ == "__main__":
    main()
