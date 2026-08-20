# Hammer experiment index

This index is the shortest route into the record. It separates apparatus calibration, rejected task designs, and observed model runs so a label is not mistaken for a result.

## How labels work

Historical labels are retained exactly as published. `G32` names the 32-node graph proposal; `C48` names the 48-node declared-compaction treatment. The letter describes the treatment family used when the document was introduced and the number is the fixture size. A suffix identifies the execution or document type, for example `-scripted` or `-adversarial-review`.

Future experiment families should use the same compact form: an uppercase family label, a size where one is meaningful, then a descriptive suffix. The public run identifier adds its UTC start time, such as `c48-compaction-20260819T113718Z`. These identifiers are records, not performance rankings.

## Status at a glance

| Label or family | Status | What it establishes |
| --- | --- | --- |
| 10/50 retrieval | Apparatus calibration complete | The confined primitive interface, snapshots, malformed-action handling, and task scoring work under repeated fresh contexts. It is not Pilot 1 evidence. |
| G32 | Proposed, then demoted | The static graph proposal and adversarial review identified an incentive problem: external state had no demonstrated current-goal advantage. |
| Live reconciliation | Rejected before a run | A known future amendment would make deferral a rational strategy; it is not a clean persistence treatment. |
| C48 compaction | One exploratory observation recorded | Declared transcript loss did not produce a filesystem artifact in the observed trajectory; the run exhausted its action budget without an answer. It is not a general causal result. |
| C48-L / C48-H | One exploratory observation each | Exact checkpoint labels, and then labels plus a declared 280-turn horizon, still produced no model-created filesystem state or answer. C48-H did close descriptors; that is not persistent construction. |
| C48 H0 / H12 | One exploratory continuity-window pair | With the same fixture, seed, model settings, and budgets, H0 made no write attempt; H12 created one invalid candidate answer after checkpoint 1 and did not reuse it. One pair does not identify the cause of that difference or establish persistence. |
| C48 append affordance | One exploratory pair recorded | Scripted append calibration passed. The append-visible member did not request append or create state, but its action trajectory differed from the control. One pair does not isolate why. |
| D96 dependency ordering | One unreplicated candidate observation | The scripted baseline passed. The model read 48 of 96 records, wrote an invalid required answer, and ended with 376 turns unused; it created no support state. |
| D96 terminal semantics | Six-member calibration completed | Both blind arms failed. Explicit finality was associated with an earlier invalid submission, but seed assignment is confounded with wording, so no causal comparison is claimed. |
| Future experiment register | Design notes only | Candidate terminal-feedback treatments and their interpretation boundaries are preserved separately from observed runs. |

## Read in this order

1. [Research overview](research-overview.md) — the broader question and scope.
2. [Calibration summary](calibration-summary-20260818.md) — what the retrieval apparatus did and did not establish.
3. [Pilot direction correction](pilot-1-direction-20260818.md) and [task selection](pilot-1-task-selection.md) — why repeated independent tasks were not retained as Pilot 1.
4. [C48 frozen protocol](pilot-1-c48-compaction-protocol.md) — the declared-compaction treatment and its interpretation limits.
5. [C48 run report](../runs/c48-compaction-20260819T113718Z.md) and its [machine trajectory](../runs/c48-compaction-20260819T113718Z.jsonl) — the completed negative result.
6. [C48 horizon-information protocol](c48-horizon-information-protocol.md), [C48-L report](../runs/c48-labeled-20260819T154515Z.md), and [C48-H report](../runs/c48-horizon-20260819T155857Z.md) — the frozen follow-up and its two observations.
7. [C48 continuity-window protocol](c48-continuity-window-protocol.md), [H0 report](../runs/c48-h0-20260819T165510Z.md), and [H12 report](../runs/c48-h12-20260819T201228Z.md) — the full-reset and 12-exchange-tail exploratory pair.
8. [C48 append-affordance protocol](c48-append-affordance-protocol.md), [scripted calibration](../runs/append-calibration-20260819T211522Z.md), [control](../runs/c48-append-h0-control-20260819T211551Z.md), and [append-visible member](../runs/c48-append-h0-append-20260819T213005Z.md) — the completed small mechanism ablation.
9. [D96 protocol](pilot-d96-dependency-ordering-protocol.md), [scripted baseline](../runs/d96-scripted-20260820T004209Z.md), and [candidate observation](../runs/d96-pilot-candidate-20260820T004248Z.md) — the continuous-context task and its first task-level failure trajectory.
10. [D96 forensic addendum](d96-forensic-addendum-20260820.md), [terminal-semantics protocol](d96-terminal-semantics-protocol.md), and [six-member results](d96-terminal-semantics-results-20260820.md) — the post-hoc diagnostic, frozen blind-terminal follow-up, and its bounded result.
11. [Future experiment register](future-experiment-register.md) — candidate treatments retained for later design and review, not results.
12. [VM execution design](vm-execution-design.md) — the separate future condition for native self-authored execution.

## Reading a run

Every experimental run has a human Markdown report and a machine JSONL trajectory in `runs/`. The report supplies the question, attempt, result, surprise, and interpretation boundary. The JSONL is the adapter-visible record: model response, accepted or rejected action, corresponding filesystem syscall result, snapshots, and terminal checks. It is not a kernel-wide trace.

Run records are append-only publication artifacts. A failed task is still a result when its terminal condition, action trajectory, and state lineage are preserved.
