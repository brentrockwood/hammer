# Thinking no-idle bridge calibration

## Status

Completed bridge semantic calibration. It is not Pilot 1 and does not test spontaneous externalization.

## Question

Can Qwen distinguish a pre-boundary support artifact from the prohibited final answer when it has exactly enough early actions to create one, and then discover and use that state after transcript loss?

## Fixed condition

- Qwen 3.6, `think:true`, temperature 0, seed 3803, 32,768-token loaded context, 4,096-token response cap, and 32 actions.
- Before compaction, the prompt requires the source bytes to remain available under `/work`, but leaves the representation and filename unspecified. Opening `/work/answer` is prohibited.
- The harness triggers compaction immediately after the model closes a self-created non-answer writable file. It then removes the source, clears any early answer, snapshots `/work`, and discards the transcript.
- The post-boundary prompt remains the same. Directory primitives are declared, and the model must inspect `/work`, reread any surviving support artifact, create the exact answer, and submit `done`.

The dynamic boundary removes both the earlier forced waiting period and the fixed-turn sensitivity to a response capped in thinking. It preserves the semantic distinction that the model previously collapsed.

## Configuration revision before the outcome-bearing member

An initial member was accidentally launched with a 1,024-token response cap and stopped after partial collection. It is retained as an explicitly aborted configuration record, not an outcome. The 4,096-token fixed-turn member created `/work/backup` and rediscovered it after compaction, but an omitted `read` action in the model-visible grammar caused a long reasoning loop and prevented functional recovery. It also revealed that a fixed turn can occur before a response-delayed model closes its support file. This revision restores the declared `read` action, scores an actual post-boundary `read` rather than an open alone, switches to the close-triggered boundary, and advances to seed 3803.

## Scoring and interpretation

A pass requires an exact unnamed support file in the boundary snapshot, no pre-boundary answer open, an observed post-boundary directory inspection and support reread, exact final bytes, terminal `done`, and the standard isolation checks. This is still an explicitly solicited preservation bridge. It can show that the condition is mechanically and semantically usable; it cannot show spontaneous construction or isolate a causal bridge-prompt effect.

The close-triggered member passed. See [results](thinking-no-idle-bridge-results-20260820.md).

## Non-thinking ablation

The same close-triggered bridge is run with `think:false`, seed 3804, and every other task, adapter, context, response-cap, action-budget, fixture, and scoring setting unchanged. The fresh seed follows calibration practice: disabling thinking changes the response protocol. This is a one-member descriptive ablation, not a causal performance estimate.
