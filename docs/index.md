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

## Read in this order

1. [Research overview](research-overview.md) — the broader question and scope.
2. [Calibration summary](calibration-summary-20260818.md) — what the retrieval apparatus did and did not establish.
3. [Pilot direction correction](pilot-1-direction-20260818.md) and [task selection](pilot-1-task-selection.md) — why repeated independent tasks were not retained as Pilot 1.
4. [C48 frozen protocol](pilot-1-c48-compaction-protocol.md) — the declared-compaction treatment and its interpretation limits.
5. [C48 run report](../runs/c48-compaction-20260819T113718Z.md) and its [machine trajectory](../runs/c48-compaction-20260819T113718Z.jsonl) — the completed negative result.
6. [C48 horizon-information protocol](c48-horizon-information-protocol.md), [C48-L report](../runs/c48-labeled-20260819T154515Z.md), and [C48-H report](../runs/c48-horizon-20260819T155857Z.md) — the frozen follow-up and its two observations.
7. [VM execution design](vm-execution-design.md) — the separate future condition for native self-authored execution.

## Reading a run

Every experimental run has a human Markdown report and a machine JSONL trajectory in `runs/`. The report supplies the question, attempt, result, surprise, and interpretation boundary. The JSONL is the adapter-visible record: model response, accepted or rejected action, corresponding filesystem syscall result, snapshots, and terminal checks. It is not a kernel-wide trace.

Run records are append-only publication artifacts. A failed task is still a result when its terminal condition, action trajectory, and state lineage are preserved.
