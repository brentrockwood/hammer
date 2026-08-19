# C48 declared-compaction treatment — frozen protocol

## Status and question

This is Hammer's first explicitly compaction-dependent treatment. It is not a test of whether a model with uninterrupted full context spontaneously needs filesystem state. The model is told that its transcript will be discarded twice while `/work` persists. The question is narrower: what external state, if any, does it create and consult when a visible context boundary makes retained state potentially useful to its current closed-ended goal?

The first observation is exploratory and forensic. A valid answer is a halt condition, not evidence that a particular artifact caused success. A continuous-context comparison is required before making a performance claim.

## Frozen task

The fixture seed is `20260819`. `/work/start` identifies the entry record of a directed graph in `/work/n`. The fixture contains 48 opaque node files. Each node names zero or more full-path successors and has either `role=ordinary` or the unique `role=amber-terminal`.

The model must find any simple directed route from the entry to the unique terminal, write the newline-separated node paths to `/work/answer`, close it, and return `{"action":"answer","answer":"done"}`. It must leave `/work/start` and `/work/n` unchanged. The prompt does not suggest notes, indexing, caching, a representation, tool construction, or a strategy.

`/work/answer` is reserved for final required output. Its presence before the second checkpoint is an invalid early-output condition. The model may create state elsewhere below `/work`; those paths are retained and classified from the trace.

## Declared compaction treatment

The model is told before it acts that its prior conversation will be discarded after model turns 70 and 140, while `/work` remains. At each checkpoint the host records the event and resets the model conversation to the same fixed task prompt plus a short statement that the prior transcript is unavailable and the task continues. No model-generated summary is injected. Every model turn, including a rejected action or failed syscall, counts toward the checkpoints and the total limit.

This is a forcing treatment for retained state, not a hidden event, an unknown stopping condition, or an action-clock amendment. The task continues throughout; there is no `wait` action and no reason to issue meaningless calls merely to make a new input arrive.

## Frozen inference and budget

- Model: `qwen3.6:35b`, verified by the run-time digest.
- Model sampling seed: `3001`.
- Temperature: `0`.
- Thinking: `false`.
- Requested context: `32,768` tokens.
- Maximum response: `512` tokens.
- Maximum model turns: `280`.

The exhaustive successful primitive floor is 154 turns: start-file read (3), one directory enumeration (3), 48 node reads (144), final answer-file write (3), and terminal response (1). The two checkpoint positions make a full restart-and-rescan after the second reset infeasible within the remaining 140 turns, while leaving room for a concise scratch representation and later consultation. This accounting does not require exhaustive enumeration or a scratch file for validity.

## Fixture, validation, and integrity

The deterministic generator uses independent streams for opaque names, graph topology, successor order, and creation order. It guarantees a route to the terminal, reachable cycles and dead ends, no target-revealing names, and no direct entry-to-terminal edge. A host-retained immutable manifest validates the final answer: entry first, every adjacent original edge valid, no repeated path, and terminal last. Any valid witness is accepted.

The host snapshots `/work` before the run, at both checkpoints, and after termination. Any model-originated change under `start` or `n/` is an input-integrity terminal outcome. The model-facing container remains network-disabled with its read-only root and `/work` as its sole writable mount.

## Interpretation and future comparison

The record can show creation, revision, rereading, maintenance, abandonment, or apparent consultation of external state. It cannot establish that a file extended memory or caused better performance from one trajectory. A later preregistered matched continuous-context condition will use the same generator family and output validator; it is the comparison needed to assess effects of the declared compaction treatment.

## Pre-run gates

- The generator must pass its deterministic topology and validation checks.
- A scripted primitive client must pass through both compactions, retain a compact route representation outside `/work/answer`, and produce a valid final answer within 280 turns.
- The complete publication-safe dry-run trajectory and report must be inspected for snapshots, compaction events, integrity checks, and absence of local endpoint details.
- The source must be clean, committed, and rebuilt so the agent image label equals the exact run commit.
