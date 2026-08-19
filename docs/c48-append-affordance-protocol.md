# C48 append-affordance pair — frozen protocol

## Question

Does making a reopenable append operation visible and available change the trajectory of the C48 H0 full-reset treatment? This is a small mechanism ablation, not Pilot 1 and not a test of spontaneous tool creation.

## Pair

Both members use the existing C48 fixture seed `20260819`, H0 full transcript resets after turns 70 and 140, a 280-turn maximum, `qwen3.6:35b`, sampling seed `3301`, temperature 0, `think:false`, a 32,768-token context, and a 512-token response cap. They use the same apparatus implementation. The control launches the agent without extra arguments and lists the existing three `openat` modes. The append condition launches the same agent as `/agent --append` and adds exactly this otherwise absent grammar example:

```json
{"action":"syscall","op":"openat","path":"/work/FILENAME","mode":"write_append_create"}
```

That mode maps to the same confined `openat2` syscall with `O_WRONLY | O_CREAT | O_APPEND`. It is opt-in: an unflagged agent rejects it at adapter validation, so the control does not silently possess an undocumented usable mode.

Each run is committed and pushed before the next run. The frozen-image workflow therefore advances the append member's recorded revision by the control run artifacts; before comparing them, verify that the implementation diff contains only those publication artifacts.

## Outcome and classification

The required task outcome and C48 route validator are unchanged. The existing instruction that delays `/work/answer` until after the second declared checkpoint is retained to hold the historical H0 task constant; this pair cannot resolve the answer-gating pathology observed in H12.

The primary descriptive measures are append-mode requests, accepted append opens, writes to non-output paths, post-reset reads of model-created paths, route validity, terminal completion, action counts, rejections, and snapshots. Append use alone establishes only uptake of a newly visible primitive. A model-created file is classified as potentially useful support state only if the post-reset trajectory reads it and the later action sequence visibly uses its contents toward the route. It is not a persistent instrumental structure merely because it exists or was written with append.

## Interpretation boundary

One seed per condition is exploratory. A difference is a candidate affordance effect, not an estimate of effect size or proof of causality. A null result does not show that append is generally irrelevant. The pair is retained because it separates the model-visible append affordance from the otherwise fixed C48 H0 treatment; it does not establish a suitable Pilot 1 task.
