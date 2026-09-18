# google-photos-ai-engine


A research instrument for one discovery question: **what actually happens when people try to retrieve a photo they remember but cannot precisely describe?**
It turns user conversations into traceable evidence you can compare across sources and scenarios, then stops at research hypotheses and an interview brief. It does **not** propose features.

See [problemstatement.md](problemstatement.md) for the problem definition, [architecture.md](architecture.md) for system design, [edgecases.md](edgecases.md) for edge-case behaviour, [evals.md](evals.md) for the evaluation plan and baseline, and [implementationplan.md](implementationplan.md) for the phase-by-phase build.

## Setup

```bash
pip install -r requirements.txt
# Optional, for the Claude analyzer (recommended for real data):
export ANTHROPIC_API_KEY=...        # PowerShell: $env:ANTHROPIC_API_KEY="..."
```

## Quick start (current dataset: `google_photos_discovery_annotated`)

The engine's single data source is `google_photos_discovery_annotated.xlsx`, exported row for row as
`google_photos_discovery_annotated.csv`:

- 840 rows, 120 per source. There is no date column.
- Columns: `source`, `id`, `text`, and five annotation columns (`retrieval_intent`, `retrieval_scenario`,
  `retrieval_object`, `memory_clues`, `forgotten_information`).
- Ingested with no provenance flag, so the data itself carries no claim about where the text came from. The provenance check is recorded in [problemstatement.md](problemstatement.md) §22.5.
- Only `source`, `id` and `text` are ingested. The analyzers produce their own labels; the file's annotations are not
  used as input.
- Earlier datasets (`dataset_flat`, `data/synthetic/`) are no longer ingested.

```bash
python -m discovery_engine ingest google_photos_discovery_annotated.csv --dataset google_photos_discovery_annotated
python -m discovery_engine analyze          # heuristic unless Claude credentials are set
python -m discovery_engine synthesize       # writes reports/
python -m discovery_engine serve --port 8931
```

**Provenance mode** (`--provenance`, or `DE_PROVENANCE`) controls only how outputs *describe* the data:

| Mode | Reports and workspace show |
|---|---|
| `auto` (default) | The dataset, plus a banner, caveats and per-record tags **only if** records are flagged at ingest (`--synthetic`). Nothing is flagged in this project, so outputs stay neutral |
| `neutral` | The dataset name only, and no claim either way |

The per-record `is_synthetic` field and the provenance note in [problemstatement.md](problemstatement.md) §22.5 are unchanged by this setting.

To start clean, delete `data/discovery.db` first. `demo` still regenerates the old synthetic dataset and should not be used for this project.

## Commands

| Command | What it does |
|---|---|
| `generate-synthetic [--per-source 120]` | Writes `data/synthetic/`: 120 rows each for Play Store, App Store, Reddit, Google Photos Community, social media, YouTube, forums, plus a hidden `ground_truth.jsonl` |
| `ingest PATH... [--source X] [--dataset D] [--synthetic]` | CSV / XLSX / JSON / JSONL / TXT. Cleans text, scrubs emails and phone numbers, hashes authors, removes exact and near duplicates, chunks |
| `analyze [--analyzer auto\|claude\|heuristic]` | Relevance check, then structured extraction, then quote validation. `auto` uses Claude when credentials exist |
| `synthesize [--exclude-synthetic] [--refine-hypotheses]` | Builds the discovery bundle and writes `reports/discovery_report.md` and `reports/research_brief.md` |
| `evaluate` | Scores the current analyses against the synthetic ground truth |
| `ask "question"` | Answers a PM question from stored evidence |
| `serve` | Discovery workspace + JSON API (`/classic` keeps the original single-page dashboard) |

## Discovery workspace

`python -m discovery_engine serve` opens a workspace organised around the discovery chain:

| Area | Views | What you can do |
|---|---|---|
| Understand | Overview · Retrieval journey · Memory gap · Search behaviour · Scenarios | See the answers to the core discovery questions; click any bar, heatmap cell or journey stage to read the records behind it |
| Decide | Segments · Opportunities | See where the business metric is lost, stage by stage, with the share each stage could return; compare segments and opportunities dimension by dimension; choose the segment to take into research; open an opportunity for its evidence chain, strength checks and challenging evidence |
| Hand off | Research plan | Three tabs: **Plan & hypotheses** (hypotheses, JTBD, copyable interview guide, screener, falsification signals, Markdown downloads), **Method** (the research design, its rejected alternatives, ethics and validity threats), **Problem definition** (the draft definition and the chain from business metric to problem) |
| Investigate | Ask & explore · Review queue | Ask questions (also via **Ctrl K** or **/**), filter evidence, review low-confidence analyses, proposed labels, failed quotes and the correction log |

The **evidence inspector** opens as a side panel. It shows the raw text with every extracted quote highlighted by signal type, and next to it the AI interpretation, where you can *challenge* a field or *reject* a signal. The original AI output is always kept; click **Rebuild** to update all numbers. The workspace supports light and dark themes, keyboard navigation and mobile widths.

## From business metric to problem definition

The workspace carries the evidence through the four steps a PM has to make:

| Step | Where | What it produces |
|---|---|---|
| Break the metric down | Opportunities | Successful retrieval split into five things that must go right — **Recall → Express → Match → Recognize → Recover** — plus whether the item is retrievable at all. Each stage carries the share of attempts that break there, the share still unresolved, and the points it could return. Headroom is an upper bound, labelled `INTERPRETATION`, never a forecast |
| Find where the opportunity is | Opportunities · Segments | Opportunity areas under each stage, and two behavioural segments — **Direct, Contextual** — the only primary segmentation. Person/place/event/object/visual detail are memory clues, not segments. **Memory state**, **retrieval complexity** and **retrieval state** (including Candidate-Heavy and Recovery-dependent) are secondary lenses that characterize attempts within the two segments, plus an impact-mapping chain (WHY → WHO → HOW → WHAT) and a standing target-segment hypothesis. Each segment carries its research fit: role in the study, how to recruit it, whether its behaviour can be seen live, and how sensitive its content is. No composite score: you choose, and **Select** records the choice |
| Plan the research | Research plan · Method | A hybrid session on the participant's own library: memory elicited **before** the device is touched, an unaided live attempt, a walkthrough of a past failure, then assisted resolution to learn whether the photo was ever findable. Six rejected alternatives, ethics, validity threats with mitigations, and a screener and session shape specific to the chosen segment |
| Define the problem | Research plan · Problem definition | Target segment, retrieval scenario, product outcome, root cause (`HYPOTHESIS`), workarounds, user value, business rationale, the competing explanation to rule out, and what the problem is **not** |

The problem is deliberately **not** framed as "users find it difficult to search for old photos". The evidence supports a narrower claim: users arrive holding real clues and still fail, because what the retrieval path needs is what they no longer have. Every field stays a DRAFT until the interviews run.

## Checks

| Script | What it verifies |
|---|---|
| `python -m pytest -q` | 15 unit and end-to-end tests |
| `python tools/mission_check.py` | 86 checks against the built bundle, report and brief: §20 success criteria, §18 guardrails (quote verbatimness, rate consistency, no solution language, epistemic separation), §22 dataset rules, and case study Parts 2-4 |
| `python tools/ui_check.py` | 69 browser checks (Playwright, Edge) against a running `serve --port 8931`: every view in light and dark, drill-downs, corrections, research tabs, mobile widths, console and page errors. Set `UI_CHECK_OUT` to keep the screenshots |

## How evidence flows

```
records (RAW, never modified) ─► chunks ─► analyses (AI, versioned per analyzer/prompt)
                                               └─► signals (one row per claim, evidence ID, verbatim quote, quote_valid)
overrides (PM corrections, applied on read; original AI output kept)
syntheses (bundles: quant, segments, opportunities, contradictions, hypotheses, brief)
```

**Traceability.** Every signal carries a verbatim quote. The validator re-finds each quote in the source text, and any quote it cannot find is kept for audit but excluded from every count. In the dashboard you can click from an opportunity to its insights, then to the pattern behind each insight, then to the source records. Any classification can be challenged, or a signal rejected, from the record view.

**Counting.** Rates count distinct records and always carry numerator, denominator, denominator definition and scope. A † mark means the denominator is below `DE_MIN_SAMPLE` (default 30), so treat the rate as directional.

**Epistemic labels.** Outputs are tagged OBSERVATION, INSIGHT, INTERPRETATION or HYPOTHESIS. JTBD statements are INTERPRETATION.

**Evidence strength** follows explicit rules (`discovery_engine/evidence.py`): record volume, independent sources, share of first-person behavioural evidence, and contradiction ratio. The checks behind each level appear in the UI and in the report.

**Challenging evidence.** For every opportunity the engine searches for: explicit counter-evidence, vague-memory attempts that succeeded, alternative explanations (data or index limits), concentration in one source or scenario, and existing workarounds that other users recommend.

**No composite score.** Segments and opportunities are compared dimension by dimension. The "leading opportunity" is a proposal made by a stated rule (strength gate, then share of vague-memory cases, then unsuccessful share, then source count). The PM accepts or overrides it.

**Sentiment** is recorded only as supplementary information and never drives any output.

## Analyzers

- **Claude** (`claude-opus-5`, adaptive thinking, structured outputs, server-side refusal fallback `fallbacks: "default"`). It makes two calls per chunk: a low-effort relevance gate, then extraction at `DE_EFFORT` (default `medium`). Source text is wrapped and treated as untrusted data. Settings: `DE_MODEL`, `DE_EFFORT`, `DE_CONCURRENCY`.
- **Heuristic**: a lexicon baseline that runs offline and deterministically. Every quote is the exact sentence that triggered the match, and confidence stays at or below 0.5. Use it for pipeline testing and as a comparison baseline, not for real-world discovery.

The analyzer, model and prompt version are stored with every analysis and shown on every page.

## About the synthetic data

`data/synthetic/` is **SYNTHETIC / SIMULATED**. Every row has `is_synthetic: true` and a `synthetic://` URL, and the report and dashboard show a banner whenever synthetic rows are included. The generator recombines hand-written memory "episodes" using weights set in `discovery_engine/synthetic/episodes.py`. For example, it makes document and screenshot scenarios lean toward index-limitation failures, and wedding and event scenarios lean toward result-evaluation failures.

Anything the engine "discovers" in this dataset was designed into it. That makes the dataset useful for checking that the pipeline can surface, compare and trace patterns, and for scoring extraction against ground truth. It says nothing about real Google Photos users.

The `evaluate` scores also overstate accuracy on real text, especially for the heuristic analyzer.

For real discovery, ingest exported public data (for example review exports, Reddit or forum dumps, community threads) with `ingest`, run `analyze --analyzer claude`, and synthesize with `--exclude-synthetic`.

## Privacy

Only ingest publicly available content you are permitted to analyse. Authors are stored as salted hashes (`DE_AUTHOR_SALT`), and emails and phone numbers are scrubbed on ingest. The engine builds no per-person profiles.
