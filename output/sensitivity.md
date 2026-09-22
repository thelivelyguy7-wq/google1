# Sensitivity analysis

Does the target segment, and the opportunity ranking, survive a different reasonable analyst? Synthetic corpus only: a variant that agrees still agrees about this file, not about users.

## 1. Target segment under alternative definitions

| Variant | Records | Of | Share | Still the largest group? |
|---|---|---|---|---|
| As published: recovery-dependent or candidate-inspection | 503 | 800 | 62.9% | yes |
| (a) Recovery-dependent only | 238 | 800 | 29.8% | no |
| (b) Candidate-inspection only | 265 | 800 | 33.1% | no |
| (c) Exact duplicates removed | 502 | 796 | 63.1% | yes |
| (d) Near-duplicates removed | 502 | 796 | 63.1% | yes |
| (e) Similar-but-not-exact counted as an exit, not effort | 462 | 759 | 60.9% | yes |

**Reading.** The published definition covers 503 of 800 records (62.9%); 3 of 5 variants still leave it the majority group. Splitting it (a, b) leaves neither half a majority, which is why the two states are pooled. Duplicate removal barely moves it. Treating similar-but-not-exact as an exit shrinks it without changing which group is largest.

## 2. Opportunity frequency labels under different thresholds

| Opportunity | Share of relevant records | as published (30 / 15) | stricter (40 / 25) | looser (25 / 10) |
|---|---|---|---|---|
| O5 | 46.4% | High | High | High |
| O1 | 45.5% | High | High | High |
| O2 | 33.5% | High | Medium | High |
| O3 | 32.4% | High | Medium | High |
| O6 | 15.8% | Medium | Low | Medium |
| O4 | 14.0% | Low | Low | Medium |
| O7 | 11.2% | Low | Low | Medium |
| O8 | 8.5% | Low | Low | Low |

**Reading.** Rank order by frequency is fixed: O5 > O1 > O2 > O3 > O6 > O4 > O7 > O8. The High/Medium/Low labels are threshold-dependent for O2, O3, O6, O4, O7, so those labels should never be quoted without the threshold. Frequency is one of seven prioritisation inputs, so a label change does not by itself move the selected opportunity: O5 leads on frequency under every threshold.

## 3. What this does not test

- Whether the lexicon codes each sentence correctly. That needs a second human coder (Phase 2.4).
- Whether the corpus resembles real behaviour. It cannot: the text is template-composed.
- Whether the ranking is right, only whether it is stable under these variants.
