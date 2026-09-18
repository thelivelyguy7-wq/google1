"""Evidence strength (spec §28). Rules are explicit so a PM can challenge them."""
from __future__ import annotations

from .config import settings

RULES = {
    "HIGH": {"min_records": 30, "min_sources": 4, "min_behavioral_share": 0.6, "max_contradiction_ratio": 0.2},
    "MEDIUM": {"min_records": 12, "min_sources": 3, "min_behavioral_share": 0.4, "max_contradiction_ratio": 0.35},
    "LOW": {"min_records": 5, "min_sources": 2, "min_behavioral_share": 0.0, "max_contradiction_ratio": 1.0},
}


def strength(records: int, sources: int, behavioral_share: float, contradicting: float, synthetic_share: float = 0.0) -> dict:
    ratio = contradicting / (records + contradicting) if (records + contradicting) else 0.0
    checks = []
    level = "DIRECTIONAL"
    for name, r in RULES.items():
        passed = {
            f"records >= {r['min_records']}": records >= r["min_records"],
            f"independent sources >= {r['min_sources']}": sources >= r["min_sources"],
            f"first-person behavioural share >= {r['min_behavioral_share']}": behavioral_share >= r["min_behavioral_share"],
            f"contradiction ratio <= {r['max_contradiction_ratio']}": ratio <= r["max_contradiction_ratio"],
        }
        if all(passed.values()):
            level = name
            checks = [f"PASS {k}" for k in passed]
            break
        checks = [f"{'PASS' if v else 'FAIL'} {k}" for k, v in passed.items()]
    caveats = []
    if synthetic_share > 0 and settings.provenance == "auto":
        caveats.append(f"{round(100 * synthetic_share)}% of supporting records come from generated text; strength reflects that data, not users.")
    return {
        "level": level, "records": records, "sources": sources,
        "behavioral_share": round(behavioral_share, 2), "contradicting_records": contradicting,
        "contradiction_ratio": round(ratio, 2), "checks": checks, "caveats": caveats,
        "rules": RULES,
    }
