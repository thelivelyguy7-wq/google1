# google-photos-ai-engine

An evidence-linked discovery pipeline for one question:

> How do people retrieve photos they remember but cannot precisely describe, and where does that break down?

It turns a corpus of public-conversation records into coded evidence, a six-node decomposition of successful
retrieval, behavioural segments, opportunity areas, research hypotheses and a **provisional** problem statement —
with every conclusion traceable back to the records behind it.

> **The bundled corpus is a real dataset.** `google_photos_raw_dataset.csv` contains real
> records. Every count is *X of Y records in that file*. No interviews, usability tests or surveys have been run: the research plan and the
> hypotheses are proposals, not findings.

## Run it

Ensure you have your API keys in a `.env` file in the root directory:
```
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here    # Optional: Used as an automatic fallback if Gemini quota is exhausted
```

```bash
pip install -r requirements.txt
python -m engine.run                                   # regenerates every output and the web app's data
python -m engine.run --input other.csv --output out    # any corpus with the same columns
python -m pytest tests -q                              # 37 invariant, snapshot and guardrail tests
```

Browse the results:

```bash
python server.py                                       # then open http://localhost:8080
```

## What it produces

| Output | What it is |
|---|---|
| `output/discovery_report.md` | The analysis in the 13 sections the case brief prescribes |
| `output/discovery_appendix.md` | Method, the discovery chain, structure tests, object judgement calls |
| `output/coded_records.csv` | One row per record: the verbatim sentences beside every code derived from them |
| `output/evidence_index.csv` | Every named group (need, segment, opportunity, node, claim, hypothesis) → every record ID behind it |
| `output/metrics.json` | All computed numbers; the report and the web app both read from here |
| `output/sensitivity.md` | Does the target segment and the ranking survive alternative definitions? |
| `output/decision_log.md` | Each coding judgement that moves a headline number, and by how much |
| `site/` | Static offline web app: 11 pages, every count clickable down to its records |

`output/` is committed on purpose: the report is the deliverable, and a reader should not have to run Python to see it.

## How it works

```
corpus CSV → code_records.py → analyze.py ─┬→ report.py     → discovery_report.md
              (lexicon.py)    (decomposition.py)
                                           ├→ sensitivity.py → sensitivity.md, decision_log.md
                                           └→ export_site.py → site/site_data.js → site/app.js
```

| Module | Job |
|---|---|
| `lexicon.py` | Hand-coded meaning of all 90 sentences in the corpus: object, memory, behaviour, outcome, signals |
| `code_records.py` | Stage 0 relevance filtering and Stage 1 evidence extraction. Raises on any unknown sentence, so coverage is total by construction |
| `decomposition.py` | The six nodes success requires, the evidence rules per node, and the first-failing-node rule for research |
| `analyze.py` | Needs, segments, opportunities, journey, target segment, impact framework, structure tests, evidence index |
| `narrative.py` | Prose shared by the report and the web app. Numbers are referenced by key, never pasted into text |
| `report.py` | Renders the 13 sections. Every figure is interpolated from metrics |
| `coders.py` / `validate_coder.py` | Two coders behind one schema (hand lexicon, model-assisted) and the harness that scores either against the other |

## Rules the engine enforces

- **Evidence, interpretation and hypothesis never merge.** Claims carry `[RAW]`, `[OBS]`, `[INTERP]`,
  `[OPP-HYP]`, `[PROB-HYP]`, `[VALIDATED]` (none yet), `[ASSUME]`, `[UNKNOWN]`.
- **Nothing is inferred.** An unstated outcome stays `unknown`; an object whose class the text does not settle keeps
  an alternative class; sentiment is never treated as behaviour.
- **No solution before the problem.** No feature, technology or product wording appears in the problem statement,
  and tests enforce that.
- **No hard-coded numbers in the UI.** Every figure in `site/` is generated into `site_data.js` by the pipeline.

## Status and what is not done

- **The model-assisted coder is unvalidated.** `LLMCoder` is written and unit-tested against fake clients, but has
  never run against the live API, so nothing is known about its accuracy. The hand lexicon is the coder of record.
  To validate: `python -m engine.validate_coder --coder llm --n 100 --perturb` (needs credentials; spends money).
- **No second human coder** has reviewed the lexicon, so it reflects one analyst's judgement.
- **No primary research has been run**, so the problem statement stays provisional and impact sizing stays `TBD`.

`implementationplan.md` tracks all of this phase by phase; `architecture.md` explains the design;
`problemstatement.md` holds the provisional problem hypothesis.
