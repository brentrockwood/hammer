# Thinking temporal-sequencing control — results

The scorer-corrected member passed every predeclared check. Qwen 3.6 created and closed the exact required checkpoint in the first five actions, then—after the source and transcript were removed—opened and read that checkpoint, created the exact final answer, closed it, and submitted `done`.

| Run | Seed | Calls | Pre-boundary actions | Post-boundary actions | Rejections | Peak loaded context | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Initial member | 3701 | 11 | 5 | 5 | 0 | 3.0% | Model trajectory completed; scorer false negative retained. |
| Corrected member | 3702 | 11 | 5 | 5 | 0 | 3.0% | All checks passed. |

The seed-3701 record is not retroactively relabeled: its `run_end` remains false because the original check used a nonexistent snapshot field. The boundary snapshot nevertheless records the exact checkpoint and the final answer is exact. The scoring fix uses the snapshot's documented `text` field and adds a regression test.

This answers a narrow apparatus question. The model can follow the prescribed temporal sequence across a transcript-loss boundary without an idle interval, and returned thinking is compatible with executable `content` under this task. Because the checkpoint representation is explicitly required, the result is not evidence of spontaneous state externalization, affordance creation, or a bridge-prompt effect.

[Initial scorer-false-negative record](../runs/thinking-temporal-control-20260820T224022Z.md) and [corrected passing record](../runs/thinking-temporal-control-20260820T224339Z.md).
