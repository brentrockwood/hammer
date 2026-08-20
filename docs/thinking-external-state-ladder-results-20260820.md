# Thinking external-state ladder — results

Neither member created a support file before the declared source-removal and transcript-loss boundary. Both therefore failed their final answer, exhausted the 28-turn budget, and left no evidence of a filesystem affordance.

| Rung | Source read before boundary | Support file at boundary | Post-boundary reread | Terminal answer | `done_reason:length` responses |
| --- | --- | --- | --- | --- | ---: |
| Bridge | Yes | No | No | No | 21 of 28 |
| Goal-only | No completed source read | No | No | No | 24 of 28 |

The bridge member did receive the representation-unspecified preservation instruction. Its returned reasoning initially proposed retaining the source in context rather than writing it. After the context boundary removed that continuity, it produced long thinking traces with empty `content`, so the adapter correctly rejected 21 malformed actions. The goal-only member exhibited the same response-cap pattern even earlier.

This is an apparatus and task-interface boundary, not evidence that a thinking model does not externalize state. The 1,024-token response cap was repeatedly reached before an executable JSON action appeared, so the ladder did not cleanly test its intended preservation contrast. The recorded `done_reason:length` values make that failure visible rather than silently treating thinking text as an action.

Do not repair these completed records. A future reasoning-agent task needs a separately calibrated action response policy—for example, a larger response cap or a protocol that makes a bounded action channel available after reasoning—before it can answer the externalization question. Any such change is a new apparatus condition, not a retry of this ladder.

[Bridge report](../runs/thinking-bridge-20260820T203211Z.md) and [goal-only report](../runs/thinking-goal-only-20260820T204239Z.md).

## Separate 4,096-token-cap bridge calibration

The planned larger-cap bridge member used the same task and checks, Qwen 3.6 with `think:true`, a 32,768-token loaded context, a 4,096-token response cap, and seed 3611. It still failed: eight primitive actions were executed across 28 calls, including one post-compaction action and a late open of `/work/answer`, but no support file existed at compaction, no support state was reread, and no terminal answer was submitted. Nineteen calls ended with `done_reason:length`; 20 response turns had no executable `content` and were rejected. The run returned 298,249 thinking characters and reached only 5,629 live context tokens (17.2% of the loaded context).

The wider cap therefore delayed rather than removed the response-policy failure. It is not evidence about the bridge prompt's effect on external state. Because this member still did not provide a working action channel, the planned 4,096-cap goal-only partner was not launched: that comparison would not isolate the intended prompt difference. A new condition needs a separately frozen response protocol, rather than another cap-only escalation.

[4,096-cap bridge report](../runs/thinking-bridge-20260820T213601Z.md).
