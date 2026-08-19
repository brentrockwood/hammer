# G32 adversarial review — 2026-08-19

## Scope

This is a design review, not a Hammer run. No G32 fixture, reference client, task runner, or model-under-study trajectory exists. The review combines an adapter-grounded human audit with one fresh, blind review from local `qwen3.6:35b` using a 32,768-token request, non-thinking mode, temperature 0, and seed 2006. The Qwen response stopped at its 768-token cap (`done_reason: length`), so it is retained as partial design input rather than a complete independent review.

## Decision

G32 should not yet be frozen as the central Pilot 1 task. It remains useful as a future apparatus-only dry run: it has a concise witness, deterministic validation, and legible filesystem lineage. But it does not yet create a compelling present-tense reason to externalize state. The complete action/result transcript stays in context, and create-or-truncate files make frequent note maintenance costly. A model may reasonably solve the graph directly and leave no structure. That is a valid observation, but it would not strongly test the proposed pressure mechanism.

## Human attack memo

### The task permits organization but may not reward it

The graph asks for a witness path through 32 small records. A direct traversal fits inside the current 32K context and the successful primitive floor is only 103 model steps. A frontier or visited file costs at least three actions to write and another three to consult; updating it after every node costs 96 additional successful calls. With the full transcript available, the file has no demonstrated memory advantage. G32 therefore cannot support a claim that it created a valuable current-goal use for external state. It can support a descriptive claim about whether a model nevertheless chooses to externalize its reasoning.

**Disposition:** retain G32 as a dry-run candidate, and design a stronger current-state pressure task before the first included Pilot 1 observation.

### Input mutation must not become a shortcut

The adapter permits `write_create_truncate` anywhere beneath `/work`, including a graph record. A model could alter an edge or target role and then submit a route that is valid only in the altered world. A validator that reads the post-run fixture would incorrectly accept it.

**Repair:** validate against a host-retained immutable graph manifest and record any change to `/work/start` or `/work/n/` as an input-integrity terminal outcome. The task may still allow unprompted writes elsewhere beneath `/work`.

### The budget language needs to include failed attempts

The runner charges every model turn against the ordinary step limit. That includes a failed syscall response and a rejected model action as well as a successful syscall and the terminal `answer`. The 103 number is a successful direct-path floor, not a complete action budget or a promise that probing is free.

**Repair:** state this directly in the semantic draft and make a reference client report successful, failed, and rejected action counts separately.

### Topology language must become generator properties

“Locally plausible” and “not mechanically obvious” are useful warnings but not testable generator invariants. Without explicit topology checks, a deterministic generator can accidentally make the target a direct child, put it in an isolated component, or encode a trivial route in creation order.

**Repair:** before fixture implementation, translate those phrases into measurable graph properties and test them over a seed set. Do not use an LLM to certify them.

## Qwen review: accepted and rejected points

The Qwen review correctly identified the missing failed-action accounting and the need to make the primitive baseline explicit. It also argued that opaque node names make the graph undiscoverable without a directory listing. That does not apply to the stated G32 semantics: `/work/start` names the entry, and every opened node exposes full successor paths. Directory enumeration is available but optional; the successful direct-path floor excludes it.

This disagreement is useful. The model review found an ambiguity worth repairing, but it also demonstrates why a reviewer output is evidence to inspect rather than a verdict to adopt.

## Next design action

Keep G32 for a later scripted dry run after the integrity and budget repairs. The next task-design effort should seek a goal where an external representation can plausibly reduce current repeated work despite a full transcript, while remaining solvable from the existing primitives and without naming the desired representation in the prompt.
