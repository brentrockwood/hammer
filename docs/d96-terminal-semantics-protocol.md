# D96 blind-terminal wording study — frozen protocol

## Status and question

This is terminal-semantics calibration, not Pilot 1 evidence. It follows the first D96 candidate trajectory, where the model submitted an invalid partial answer under wording that did not explicitly state the submission was irreversible.

The question is narrow: does explicitly stating that a blind terminal submission ends the run change the action trajectory or outcome? Neither condition returns correctness feedback.

## Matched conditions

Both arms use the same deterministic 96-record dependency fixture (fixture seed `20260820`), `qwen3.6:35b`, `think:false`, temperature 0, a requested and server-loaded 32,768-token context, a 2,048-token response cap, append-enabled primitive adapter, one continuous context, and 480 model turns. The primitive scripted baseline remains the published 297-action D96 baseline.

The prompt, fixture, output validator, action grammar, model, and all budgets are identical except for one sentence.

| Arm | Sampling seeds | Additional wording |
| --- | --- | --- |
| Original | 3402, 3403, 3404 | None. It retains the original instruction to return `done` when the answer file is complete. |
| Explicit finality | 3411, 3412, 3413 | `Submitting {"action":"answer","answer":"done"} ends this run. No further actions or feedback will be available.` |

`answer: done` is blind and terminal in both arms. The harness scores only after the run ends; it never reports validity, cardinality, missing paths, ordering errors, or remaining budget to the model.

## Measurements

The public trajectory retains the exact prompt and arm, all model actions, rejected actions, syscall results, snapshots, terminal check, and usage. Each run additionally records an answer diagnostic that does not alter scoring: nonempty and unique path counts, unknown paths, missing fixture nodes, duplicate entries, and dependency-order violations among listed valid nodes.

The report also records directory-call count, EOF observation, distinct records opened for reading, model calls, and turns remaining at terminal submission. The loaded-context gate rejects the run before a container starts unless Ollama reports 32,768 as the active context for the requested model.

## Interpretation plan

Report the distribution of terminal outcomes and forensic trajectory classes across all six predeclared members. Do not select a best run. A difference between the three-member arms would be preliminary: it may reflect sampling variation, prompt interpretation, or other uncontrolled model behavior. No result establishes useful external organization or persistent instrumental structure merely from artifact presence, task success, or failure.
