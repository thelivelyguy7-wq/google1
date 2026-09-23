# Decision log

Coding choices that move a headline number, with the size of the move, so a reader can price the judgement rather than take it on trust. Dataset only.

| Decision | Records affected | Why | What a different choice would do |
|---|---|---|---|
| Off-topic records excluded from every denominator | 37 records | The `SIM-N…` records describe sharing, storage, battery and editing, with no retrieval angle. | Including them would dilute every share by about 4.4 points and mix two populations. |
| Deleted-photo restore treated as possibly relevant, not relevant | 3 records | The intent is to get a photo back, but it is a restore flow carrying no memory or search evidence. | Moving it into the relevant set adds 3 records and no coded behaviour. |
| B08 switched to another device or app counted as an exit path | 0 records | The record ends outside Google Photos and never states whether the photo was found. | Counting it as recovery would move 0 records from SEG-1 into SEG-2 and raise the target segment to 404. |
| B14 similar-but-not-exact counted as candidate inspection | 0 records | The user was inspecting candidates and states an uncertain outcome, not a terminal one. | Counting it as an exit cuts the target segment to 404: variant (e) in `sensitivity.md`. |
| Unstated outcome coded unknown, never inferred | 0 records | The brief forbids inferring outcomes, and most records simply do not say how the search ended. | Any inference would manufacture a success or failure rate this corpus cannot support. |
| Opener sentences excluded from behaviour evidence | 0 records with an affect or vendor-request opener | The search is frustrating is sentiment; please make this easier is a solution request. Neither is behaviour. | Using them would make sentiment a discovery method, which the brief rules out. |
| D3 left at zero rather than inferred from too many results | 0 records carry indirect signs | A broad result set does not state that the product misunderstood the input. | Inferring it would invent a matching problem no record states, and pre-empt the task-test attribution. |
| Object classes flagged where the text does not settle them | 308 records across 11 objects | The old meme I saved and our Diwali family photo fit more than one class; a yellow truck fits none. | No finding depends on object class: object is statistically independent of memory and behaviour. |
| C04 easier with an exact date or name counted as an expression barrier | 0 records | It is a statement about the input step, contrasting imprecise memory with precise identifiers. | Dropping it reduces opportunity O1 from 322 to 322 records. |
| SEG-2 and SEG-3 pooled into one target segment | 404 records | The states are snapshots of one journey; each record shows only the step its sentence names. | Keeping them apart leaves neither a majority: variants (a) and (b) in `sensitivity.md`. |

Choices deliberately **not** made: no outcome inferred from sentiment; no population percentage derived from any count; no opportunity turned into a feature; no numeric priority score.
