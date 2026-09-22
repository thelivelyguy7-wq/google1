"""Validate a coder against the lexicon truth on this corpus.

    python -m engine.validate_coder --coder lexicon                 # harness self-check (agreement must be 1.0)
    python -m engine.validate_coder --coder lexicon --perturb       # shows the lexicon cannot read reworded text
    python -m engine.validate_coder --coder llm --n 100 --perturb   # the real test: needs API credentials

`--perturb` rewrites each record (lower-case, no sentence punctuation, sentences joined by ' / ') so exact sentence
matching cannot succeed. A coder that only memorised the template fails here; one that reads the text does not.
Agreement is measured per field, with Cohen's kappa for single-label fields and micro-F1 for multi-label fields.
Output: output/coder_validation_<coder>[_perturbed].md. The lexicon is the reference, so this measures *agreement with the reference*,
not truth about real users.
"""
from __future__ import annotations

import argparse
import random
import re
import sys
from collections import Counter

import pandas as pd

from . import config
from .coders import Coder, Coding, LexiconCoder, grounded

SINGLE = ["relevance", "object_class", "retrieval_state", "outcome"]
MULTI = ["remembered", "forgotten", "severity_signals"]


def perturb(text: str, rng: random.Random) -> str:
    parts = [p.strip().rstrip(".!?") for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    return " / ".join(p.lower() for p in parts)


def cohen_kappa(a: list, b: list) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def micro_f1(truth: list[set], pred: list[set]) -> float:
    tp = sum(len(t & p) for t, p in zip(truth, pred))
    fp = sum(len(p - t) for t, p in zip(truth, pred))
    fn = sum(len(t - p) for t, p in zip(truth, pred))
    return 1.0 if tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn)


def truth_from_lexicon(df: pd.DataFrame) -> list[Coding]:
    lex = LexiconCoder()
    return [lex.code(t) for t in df["text"]]


def compare(texts: list[str], truth: list[Coding], preds: list[Coding | None]) -> dict:
    """Agreement between predicted and reference codings. Uncoded records count as errors, not as skipped."""
    n = len(texts)
    coded = [(t, r, p) for t, r, p in zip(texts, truth, preds) if p is not None]
    res = {"n": n, "coded": len(coded), "uncoded": n - len(coded)}
    if not coded:
        return res
    for f in SINGLE:
        a = [getattr(r, f) for _, r, _ in coded]
        b = [getattr(p, f) for _, _, p in coded]
        res[f] = {"accuracy": sum(x == y for x, y in zip(a, b)) / len(a), "kappa": cohen_kappa(a, b)}
    for f in MULTI:
        res[f] = {"micro_f1": micro_f1([set(getattr(r, f)) for _, r, _ in coded], [set(getattr(p, f)) for _, _, p in coded])}
    res["express_barrier"] = {"accuracy": sum(r.express_barrier == p.express_barrier for _, r, p in coded) / len(coded)}
    g = [grounded(t, p) for t, _, p in coded]
    res["grounding"] = {"rate": sum(x["ok"] for x in g) / len(g), "ungrounded_quotes": sum(len(x["ungrounded_quotes"]) for x in g),
                        "unsupported_fields": sum(len(x["unsupported_fields"]) for x in g)}
    # coverage-adjusted: what share of ALL records the coder got right on the four single-label fields
    exact = sum(all(getattr(r, f) == getattr(p, f) for f in SINGLE) for _, r, p in coded)
    res["all_single_fields_correct_of_n"] = exact / n
    return res


def render(name: str, res: dict, perturbed: bool) -> str:
    o = [f"# Coder validation — `{name}`", "",
         f"Reference: hand-coded lexicon on the synthetic corpus. Perturbed text: **{perturbed}**. "
         "This measures agreement with the reference only; it says nothing about real users.", "",
         f"Records: {res['n']} · coded: {res['coded']} · uncoded (unreadable, refused or errored): {res['uncoded']}", ""]
    if res["coded"]:
        o += ["| Field | Accuracy | Cohen's kappa |", "|---|---|---|"]
        for f in SINGLE:
            o.append(f"| {f} | {res[f]['accuracy']:.3f} | {res[f]['kappa']:.3f} |")
        o.append(f"| express_barrier | {res['express_barrier']['accuracy']:.3f} | n/a |")
        o += ["", "| Multi-label field | Micro-F1 |", "|---|---|"]
        for f in MULTI:
            o.append(f"| {f} | {res[f]['micro_f1']:.3f} |")
        gr = res["grounding"]
        o += ["", f"Grounding: {gr['rate']:.3f} of coded records fully grounded; {gr['ungrounded_quotes']} quotes not found in the record; "
                  f"{gr['unsupported_fields']} populated fields without a quote.",
              f"All four single-label fields correct, as a share of every record: {res['all_single_fields_correct_of_n']:.3f}"]
    return "\n".join(o) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coder", choices=["lexicon", "llm"], default="lexicon")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--perturb", action="store_true")
    ap.add_argument("--model", default=None)
    config.add_arguments(ap)
    args = ap.parse_args()

    config.configure(args.input, args.output)
    df = pd.read_csv(config.INPUT)
    rng = random.Random(args.seed)
    idx = sorted(rng.sample(range(len(df)), min(args.n, len(df))))
    df = df.iloc[idx].reset_index(drop=True)
    truth = truth_from_lexicon(df)
    texts = [perturb(t, rng) if args.perturb else t for t in df["text"]]

    if args.coder == "llm":
        from .coders import LLMCoder
        import time
        coder: Coder = LLMCoder(model=args.model)
        preds = []
        print(f"Coding {len(texts)} records with {coder.name}... (adding 4s delay between requests to respect free tier rate limits)")
        for i, t in enumerate(texts):
            preds.append(coder.code(t))
            if i < len(texts) - 1:
                time.sleep(4.1)
    else:
        coder = LexiconCoder()
        preds = [coder.code(t) for t in texts]
    res = compare(texts, truth, preds)
    text = render(coder.name, res, args.perturb)
    fname = f"coder_validation_{args.coder}{'_perturbed' if args.perturb else ''}.md"
    (config.OUTPUT / fname).write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
