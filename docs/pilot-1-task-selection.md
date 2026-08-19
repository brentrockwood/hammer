# Pilot 1 task selection — draft

## Status

This is a task-design note, not a fixture, protocol, or model observation. It narrows the next design work to a graph-reconstruction family and records why the other initially plausible families are not suitable for the sparse adapter yet.

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

This is the recommended family. A model may solve it by direct reasoning, selectively explore, construct a small frontier or visited record, make and abandon one, or fail. None of those behaviors is required for task validity.

## Candidate sizes and action accounting

Assume every node fits in one read and the model learns successor paths from node contents. The lower bound below is an exhaustive one-pass inspection of all nodes, a required answer file, and the terminal `answer` action; it excludes model-action repairs, directory enumeration, repeated reads, and scratch work.

| Variant | Node records | Node-read floor | Answer-file floor | Terminal action | Total floor |
|---|---:|---:|---:|---:|---:|
| G24 | 24 | 72 | 3 | 1 | 76 |
| G32 | 32 | 96 | 3 | 1 | 100 |
| G40 | 40 | 120 | 3 | 1 | 124 |

One directory listing that fits in a single `getdents64` page adds three actions: open directory, read entries, close directory. One scratch-file checkpoint adds at least three actions to write; consulting it later adds three more. A model that rewrites one index after each of 32 node reads would add 96 actions, so a 150–200-action budget would leave little or no room for navigation mistakes. This is why the first fixture should make batching possible rather than silently require per-node bookkeeping.

## Recommended next candidate

Begin with G32. It leaves a meaningful but bounded gap between the 100-action exhaustive floor and a future frozen budget. The graph should be constructed so that reading every node is valid but not mandatory, the final witness is short, and no local puzzle or arithmetic transformation is needed to interpret a node. The design must avoid a target that can be found by one filename lookup or a graph so regular that a path is mechanically obvious.

The required `/work/answer` is task output and excluded from artifact interpretation. Any other state is observed without a preferred-file-layout requirement. The current runner already permits a write followed by the terminal JSON answer, but a later task runner must verify the answer file separately; no such runner is implemented by this note.

## Questions for adversarial review

- Does the target predicate accidentally force exhaustive enumeration or a particular graph algorithm?
- Can a model solve the task from one or a few records because names or layout leak the answer?
- Is every answer uniquely and deterministically checkable without inspecting how the model worked?
- Is the reference-client baseline feasible while leaving room for optional, batched external organization?
- Does the report distinguish an observed artifact from demonstrated instrumental use, especially because the full transcript remains in context?

Only after those questions have answers should we generate a deterministic fixture, build a scripted reference client, or choose the action and context budgets.
