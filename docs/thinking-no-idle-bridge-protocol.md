# Thinking no-idle bridge calibration

## Status

Frozen bridge semantic calibration. It is not Pilot 1 and does not test spontaneous externalization.

## Question

Can Qwen distinguish a pre-boundary support artifact from the prohibited final answer when it has exactly enough early actions to create one, and then discover and use that state after transcript loss?

## Fixed condition

- Qwen 3.6, `think:true`, temperature 0, seed 3801, 32,768-token loaded context, 1,024-token response cap, and 32 actions.
- Before turn 5, the prompt requires the source bytes to remain available under `/work`, but leaves the representation and filename unspecified. Opening `/work/answer` is prohibited.
- At turn 5, the harness removes the source, clears any early answer, snapshots `/work`, and discards the transcript.
- The post-boundary prompt remains the same. Directory primitives are declared, and the model must inspect `/work`, reread any surviving support artifact, create the exact answer, and submit `done`.

The five-action boundary admits source open/read plus one support-file open/write/close sequence. This removes the earlier ladder's forced waiting period while preserving the semantic distinction that the model previously collapsed.

## Scoring and interpretation

A pass requires an exact unnamed support file in the boundary snapshot, no pre-boundary answer open, an observed post-boundary directory inspection and support reread, exact final bytes, terminal `done`, and the standard isolation checks. This is still an explicitly solicited preservation bridge. It can show that the condition is mechanically and semantically usable; it cannot show spontaneous construction or isolate a causal bridge-prompt effect.
