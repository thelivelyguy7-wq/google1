# Discovery Report — Appendix

Supporting material for `discovery_report.md`. Synthetic data only.

## Discovery chain followed

Raw evidence → retrieval needs → behavioural patterns → retrieval journey (with the six-node decomposition) → behavioural segments → opportunity areas → prioritisation → target segment hypothesis → research hypotheses → primary research plan → provisional problem hypothesis. Only after primary research: how-might-we, ideation, solution, MVP, testing.

## A. Structure tests (are cross-tabs meaningful?)

| Pair | χ² | dof | p | Cramér's V |
|---|---|---|---|---|
| object_class x memory_code | 63.3 | 66 | 0.57 | 0.115 |
| object_class x retrieval_state | 15.5 | 18 | 0.631 | 0.08 |
| memory_code x retrieval_state | 33.6 | 33 | 0.437 | 0.118 |
| memory_code x behavior_code | 208.3 | 187 | 0.136 | 0.154 |
| source x retrieval_state | 19.7 | 18 | 0.35 | 0.091 |
| source x memory_code | 65.3 | 66 | 0.502 | 0.117 |
| source x object_class | 32.3 | 36 | 0.647 | 0.082 |

All p > 0.05: no evidence of association beyond chance (some cells are sparse, so treat as indicative).

## B. Object-class judgement calls

| Object | Class used | Alternative | Why uncertain |
|---|---|---|---|
| a photo of my grandfather at the wedding | Family / person memory | Event / social occasion | both a person and an event |
| a photo of my grandparents' wedding album | Family / person memory | Event / social occasion | a family item and a wedding occasion; unclear whether it is a photographed print |
| a screenshot of a product I wanted | Document / screenshot / saved image | Physical object / product | a screenshot of a product; class depends on whether product or screenshot matters |
| a yellow truck | Unspecified (described by appearance only) | Physical object / product | described by appearance only; kind of object (toy, vehicle, photo subject) is not stated |
| my cousin at the concert | Family / person memory | Event / social occasion | both a person and an event |
| our Diwali family photo | Family / person memory | Event / social occasion | both a family photo and a festival occasion |
| the lamp I wanted to buy | Physical object / product | Document / screenshot / saved image | a product; may be a screenshot rather than a photo of the lamp |
| the medicine box I photographed | Medical-related image | Physical object / product | a physical object that is also medical |
| the old meme I saved | Document / screenshot / saved image | Event / social occasion | a saved image; may not be a screenshot or document |
| the photo from when I was sick | Medical-related image | Event / social occasion | a personal episode; medical only by inference |
| the picture I sent to my doctor | Medical-related image | Document / screenshot / saved image | a medical exchange; content of the picture not stated |

## C. Method and files
- `engine/lexicon.py`: hand-coded map of all 90 sentences (object class, remembered/lacking information, stage, state, outcome, signals).
- `engine/code_records.py`: Stage 0/1; raises on any unknown sentence (100% coverage by construction). Output `output/coded_records.csv`.
- `engine/decomposition.py`: the six-node decomposition, evidence polarities, failure-attribution rule and candidate measures.
- `engine/analyze.py`: Stages 2–8 metrics → `output/metrics.json`; every named group's record IDs → `output/evidence_index.csv`.
- `engine/coders.py`, `engine/validate_coder.py`: model-assisted coder and its validation harness (live-model results go to `output/coder_validation_llm_perturbed.md`; none exists until a run with API credentials has been done).
- Run: `python -m engine.run`.
- Stage 1 outcome vocabulary: found-quickly (0 stated), found-with-effort, found-after-reformulation (0), found-after-browsing (0), similar-but-uncertain, failed, abandoned, external-workaround, unknown. Unstated outcomes are never inferred.
