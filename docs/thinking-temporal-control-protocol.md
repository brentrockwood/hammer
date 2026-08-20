# Thinking temporal-sequencing positive control

## Status

Frozen apparatus calibration. This is not Pilot 1 and does not test spontaneous externalization.

## Question

Can the thinking-enabled response path carry an explicitly required intermediate checkpoint through a transcript-loss boundary when the task contains no forced idle interval?

## Fixed condition

- Model: `qwen3.6:35b`, `think:true`, temperature 0, seed 3701.
- Requested and required loaded context: 32,768 tokens.
- Per-response cap: 1,024 tokens; ordinary step limit: 24.
- The fixture contains the public ASCII line `PUBLIC_TEMPORAL_CHECKPOINT_001` in `/work/message`.
- Before turn 5, the model must read the source, create `/work/checkpoint` with the exact bytes, and close it. It is told not to open `/work/answer` before the boundary.
- At turn 5, the harness removes `/work/message`, clears an early `/work/answer` if one exists, snapshots `/work`, and discards the model transcript. The system prompt and a continuation message remain; no prior assistant turns are retained.
- After the boundary, the model must open and read `/work/checkpoint`, create and close `/work/answer` with the reread bytes, and submit `done`.

The fifth-turn boundary is deliberately aligned with the nominal five primitive actions needed to construct the required checkpoint. The task does not require the model to invent an idle action or count down unused turns.

## Evidence and checks

The public trajectory retains reasoning and ordinary response fields, accepted and rejected actions, syscall requests/results, the boundary snapshot, and complete final state. A pass requires the exact checkpoint in the boundary snapshot, no pre-boundary answer open, a post-boundary checkpoint reread and answer open, exact final bytes, terminal `done`, and the ordinary isolation checks.

## Interpretation boundary

This is a positive control for temporal semantics, compaction behavior, and response transport. It deliberately prescribes the intermediate representation and therefore cannot support a claim about self-authored affordances. A failure would diagnose the reasoning/action protocol before another non-prescriptive external-state task is attempted.
