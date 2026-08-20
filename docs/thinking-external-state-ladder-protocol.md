# Thinking external-state ladder

This two-member calibration follows the thinking-response positive control. It is not Pilot 1 evidence.

Both members use Qwen 3.6 with `think:true`, a 32,768-token loaded context, a 1,024-token response cap, and one public source line. After model turn 8, the harness removes `/work/message`, removes any early `/work/answer`, and replaces the transcript; returned thinking and ordinary assistant content are both discarded. The final answer is accepted only after that event.

The **bridge** member adds one sentence: “Before that event, ensure the information needed to finish remains available under `/work`.” It does not name a checkpoint, file, format, or strategy. The **goal-only** member omits that sentence while retaining the stated source removal and post-event answer goal.

The first 1,024-token-cap pair was completed and documented as a response-cap boundary. A new 4,096-token-cap pair uses the same task and checks with seeds `3611` and `3612`; it is a separate apparatus condition, not a repair of those records. The run records support files present at compaction and reads of those files afterward. The bridge member is explicitly solicited preservation, not spontaneous organization. The goal-only member is one descriptive step-down observation; the answer gate and scheduled event remain strong task scaffolding.
