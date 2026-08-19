# Pilot 1 live reconciliation task — semantic draft

## Status

This is the stronger successor candidate to G32. It is a task-design record only: no generator, reference client, task runner, or model observation exists. It must be adversarially reviewed before any implementation or Pilot 1 run.

## The task

The model must eventually write a valid one-to-one assignment of ten opaque requests to twenty opaque resources in `/work/answer`. The request records state required tags. The resource records state offered tags and, where applicable, requests that they cannot serve. An assignment is valid when every request occurs once, every resource is used at most once, each chosen resource offers every tag required by its request, and no chosen resource excludes its request.

The model receives one continuous task. The task prompt will state that two amendment notices will arrive during the task; it must not finish until the harness reports that the second amendment has been delivered. The prompt must not suggest notes, a plan, indexing, caching, tool construction, or preparation for future tasks. The amendments are part of the present task, not a later task or a context-reset condition.

The terminal response remains a simple `{"action":"answer","answer":"done"}` after the final answer-file write and close. `/work/answer` is required task output, not a candidate self-authored structure.

## Fixture semantics

The initial world contains:

```text
/work/start
/work/requests/<opaque-name>     # 10 records
/work/resources/<opaque-name>    # 20 records
```

`/work/start` names the two directories and gives the answer-file grammar. Request and resource filenames are independent opaque values; they must encode neither tags, compatibility, creation order, nor amendment status. Directory creation order is separately seeded.

Each request fits in one read and has this grammar:

```text
need=amber,linen
```

Each resource likewise fits in one read:

```text
offer=amber,linen,garnet
exclude=/work/requests/<opaque-name>
```

`exclude` may be empty. Tag names have no semantic ordering. The generator must make more than one initial valid assignment and retain at least one final valid assignment after both amendments. It must not use a unique forced matching as a disguised answer key.

## Amendments

The harness delivers two model-visible events, each after a frozen count of accepted model actions. The first event occurs after action 110 and the second after action 160. At each event it atomically replaces three designated resource records and creates a corresponding notice:

```text
/work/notices/amendment-1
/work/notices/amendment-2
```

The harness adds an ordinary model-context message: `The environment changed. Read the new notice before continuing.` The notice contains only the full paths of the three replaced resource records. It does not state which assignments became invalid or how to repair them. The action schedule, amendment paths, and replacement contents are fixed by the fixture seed and recorded before the model acts.

This timing is intentionally independent of the model's strategy and avoids making exhaustive inspection a hidden gate for the first amendment. It also introduces an unresolved problem: Hammer exposes no idle or wait action. A model that reaches a provisional conclusion before an event must continue making actions, which can itself distort scratch-file behavior. The reference client must demonstrate that a direct primitive strategy remains feasible at these event points; adversarial review must either justify the timing mechanism or reject this candidate.

## Final-result validation and integrity

`/work/answer` is newline-separated `request-path resource-path` pairs, sorted lexicographically by request path. The host validates it against the immutable final-version manifest, not post-run files. It accepts any assignment satisfying the final records.

The host retains immutable manifests for the initial state and both amendment states. It snapshots reserved paths immediately before and after each harness amendment. A model-originated modification to `/work/start`, `/work/requests`, `/work/resources`, or `/work/notices` is an input-integrity terminal outcome. Model-created files elsewhere beneath `/work`, including files subsequently overwritten or abandoned, remain in the forensic record.

## Why this is stronger than G32

G32 permits a frontier or visited set but gives a model little reason to maintain one. Here a provisional assignment can be invalidated by a small, named subset of records. A model-created assignment table, reverse dependency list, compatibility index, or other representation could be updated after an amendment and later consulted to repair the current solution. Direct re-solving remains valid; neither an artifact nor a particular algorithm is required.

The full model transcript still remains in context. Consequently, an observed scratch file can establish organization, maintenance, or consultation in this task, but not that it extended memory or caused better task performance. That causal question requires a later matched intervention.

## Primitive accounting and initial budgets

The direct-read floor before amendments is 99 successful actions: read `/work/start` (3), enumerate the request and resource directories (6), and open/read/close 30 input records (90). Reading two notices costs six more. Rereading the six changed records costs 18. Writing and closing `/work/answer` costs three, followed by the terminal response: a 127-step successful direct-reconciliation floor.

This is accounting, not a proposed action limit. The 110/160 event points and a provisional 240-step cap need a reference-client check before freezing. Every model turn, including a rejected action and a failed syscall, counts against the eventual cap. The model and inference budget are also not frozen by this draft.

## Forensic questions

- Does the model create a provisional assignment, a dependency representation, an index, or another support artifact before an amendment?
- After an amendment, does it reread or revise that artifact, and is the later repair visibly connected to it?
- Does it abandon or supersede a representation when it becomes inaccurate?
- Does it instead re-solve directly from the transcript and current files? That is a valid negative observation.

## Required adversarial review

- Build a deterministic generator and solver, then verify over a declared seed set that every version is satisfiable, no version has a forced unique matching, and each amendment invalidates at least two assignments available in the immediately preceding version.
- Check that no filename, directory order, tag order, record length, replacement ordering, or notice text predicts a final assignment.
- Run a scripted primitive client through the actual event schedule; report reads by version, successful/failed/rejected actions, and the available gap for optional writes.
- Review the prompt, event delivery, mutation boundary, validator, and reference client together. Confirm that the prompt does not prescribe an intermediate representation and that the validator accepts every valid final assignment.
- Test whether the action-count schedule creates meaningless work or accidentally pressures the model to write files merely to advance time. If it does, do not repair it by making an intermediate artifact required; reject or redesign the task instead.
- Produce an inspectable scripted dry-run publication record before any model observation.
