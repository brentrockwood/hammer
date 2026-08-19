# Pilot 1 task selection — draft

## Status

This is a task-design note, not a fixture, protocol, or model observation. It records why the initial static candidates are not suitable for the sparse adapter. No central Pilot 1 task is currently selected.

## Constraint discovered in the adapter

Hammer charges one accepted filesystem syscall per model action. Reading one small file costs at least `openat`, `read`, and `close`: three actions. Writing or replacing one scratch file costs the same three actions. The only write mode is create-or-truncate; there is no append, rename, or directory creation. A model can maintain a note, but every update replaces the whole file.

The task fixture should therefore keep each node below the 4,096-byte read limit, make a concise final answer possible, and leave room for optional writes after the primitive read baseline. A large streaming ledger would chiefly measure chunked parsing and rewrite cost. A 150-file dependency graph has a 450-action read-only lower bound before directory discovery, output, branching, or any agent-created state.

## Candidate families

### Dependency order

Many small manifests name prerequisites and require a valid global order. It has real organization pressure, but a useful instance needs enough files that the primitive lower bound consumes the likely budget. The natural answer is also long. Defer this family until answer transport and a larger action envelope are deliberately studied.

### Interleaved ledger

Transactions distributed across large files might invite account-specific indexes. Under the present adapter, it also requires many bounded reads, manual parsing and arithmetic, and repeated whole-file scratch rewrites. Those are stronger explanations for failure or artifact shape than indexing behavior. Reject for the first observation.

### Bounded graph reconstruction

Small opaque node records form a directed graph with cycles, dead ends, and a hidden target predicate. The model receives a known starting node and must write a short witness path or target identifier to `/work/answer`, then return `done`. The prompt need not mention enumeration, a visited set, a frontier, scratch files, or future work.

This family is retained for an apparatus-only dry run, not yet selected as the central Pilot 1 task. A model may solve it by direct reasoning, selectively explore, construct a small frontier or visited record, make and abandon one, or fail. None of those behaviors is required for task validity. The current semantic candidate is [G32](pilot-1-g32-spec.md); its adversarial review explains the decision to demote it from the primary task candidate.

## Candidate sizes and action accounting

Assume every node fits in one read, the model first reads `/work/start`, and successor paths come from node contents. The lower bound below is an exhaustive one-pass inspection, a required answer file, and the terminal `answer` action; it excludes model-action repairs, directory enumeration, repeated reads, and scratch work.

| Variant | Node records | Node-read floor | Start-file floor | Answer-file floor | Terminal action | Total floor |
|---|---:|---:|---:|---:|---:|---:|
| G24 | 24 | 72 | 3 | 3 | 1 | 79 |
| G32 | 32 | 96 | 3 | 3 | 1 | 103 |
| G40 | 40 | 120 | 3 | 3 | 1 | 127 |

One directory listing that fits in a single `getdents64` page adds three actions: open directory, read entries, close directory. One scratch-file checkpoint adds at least three actions to write; consulting it later adds three more. A model that rewrites one index after each of 32 node reads would add 96 actions, so a 150–200-action budget would leave little or no room for navigation mistakes. This is why the first fixture should make batching possible rather than silently require per-node bookkeeping.

## Recommended next candidate

Use G32 only for a later apparatus dry run after its integrity and budget repairs. It leaves a meaningful but bounded gap between the 103-action exhaustive floor and a future frozen budget, but does not create strong present-tense pressure to maintain state.

The [live-reconciliation](pilot-1-live-reconciliation-spec.md) candidate was designed to create a role for maintaining a provisional representation when named inputs change. Its adversarial review rejected it: a model can rationally defer work until the final amendment, while fixed action-count delivery would create meaningless work in an adapter without a wait action. Do not implement it as Pilot 1; see the [review](pilot-1-live-reconciliation-adversarial-review.md).

The required `/work/answer` is task output and excluded from artifact interpretation. Any other state is observed without a preferred-file-layout requirement. The current runner already permits a write followed by the terminal JSON answer, but a later task runner must verify the answer file separately; no such runner is implemented by this note.

## Questions for adversarial review

- Does the target predicate accidentally force exhaustive enumeration or a particular graph algorithm?
- Can a model solve the task from one or a few records because names or layout leak the answer?
- Is every answer uniquely and deterministically checkable without inspecting how the model worked?
- Is the reference-client baseline feasible while leaving room for optional, batched external organization?
- Does the report distinguish an observed artifact from demonstrated instrumental use, especially because the full transcript remains in context?

Only after those questions have answers should we generate a deterministic fixture, build a scripted reference client, or choose the action and context budgets. The task search must first establish a pressure criterion that does not rely on an action clock, a hidden inspection gate, an explicitly required intermediate artifact, or a model-visible future task.
