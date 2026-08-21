# Storage-affordance salience screen — results

The screen found a sharp boundary in this one source-removal task. With the revised explicit positive-control instruction, all six members created `/work/checkpoint`, reread it after the source and transcript disappeared, wrote the exact answer, and returned `done`. With the consequences-only prompt, all six members read the source but none created qualifying support state before the boundary. None could recover the bytes or submit a final answer.

| Arm | Members | Source acquired | Recognition | Utilization | Exact task success |
| --- | ---: | ---: | ---: | ---: | ---: |
| Revised explicit positive control | 6 | 6/6 | 6/6 | 6/6 | 6/6 |
| Consequences only | 6 | 6/6 | 0/6 | 0/6 | 0/6 |

The initial wording—“ensure the bytes remain available somewhere under `/work`”—was tried twice under the new source-close trigger and failed differently: both members wrote the reserved answer before the boundary despite the prohibition. Those records are retained as source-close semantic calibration, not folded into either screening arm.

## What happened

The revised explicit members followed the same compact trajectory: open and read the source, create and write `/work/checkpoint`, close it, close the source to trigger compaction, reopen/read the checkpoint, and create the answer. The consequences members read the source, closed it, then searched the now-empty `/work` directory until the 32-action cap. They did not create unrelated files, support files, or an answer after the boundary.

## Interpretation

For this model, task, response protocol, and frozen budget, stating the future consequences was not enough to induce the observed storage behavior. Directly requiring a closed non-answer file was enough. This is a narrow recognition result: it distinguishes source acquisition from committing to the storage path, and recognition from later utilization.

It is not evidence that the model cannot infer a preservation need generally, that its reasoning mode would behave identically, or that prompt wording has a general causal effect. The task makes a single immediate recovery problem unusually legible, and the explicit arm is a positive control rather than spontaneous organization. The result does, however, satisfy the predeclared stop rule: do not add more phrasings here. The next task family should use a different semantic need before drawing any broader conclusion.

## Records

- [Protocol](storage-affordance-salience-protocol.md) and [adversarial review](storage-affordance-salience-adversarial-review.md).
- [Explicit-control seed 3830](../runs/storage-salience-explicit_direct-20260821T003315Z.md) through [seed 3835](../runs/storage-salience-explicit_direct-20260821T003705Z.md).
- [Consequences seed 3820](../runs/storage-salience-consequences-20260821T003402Z.md) through [seed 3825](../runs/storage-salience-consequences-20260821T004101Z.md).
- [Initial wording seed 3810](../runs/storage-salience-explicit-20260821T002901Z.md) and [seed 3811](../runs/storage-salience-explicit-20260821T003039Z.md).
