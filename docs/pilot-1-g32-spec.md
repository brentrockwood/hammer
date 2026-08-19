# Pilot 1 G32 graph-reconstruction task — semantic draft

## Status

This specifies one candidate task closely enough for adversarial review. It is not yet a frozen protocol, fixture generator, reference client, task runner, or model observation.

## Task visible to the model

The task will state, in substance:

> `/work/start` names the entry record of a directed graph. Each record names zero or more successor records. Find any simple directed route from the entry record to the unique record whose `role` is `amber-terminal`. Write the route, including both endpoints, as newline-separated record paths to `/work/answer`. Then return `done`.

The prompt will not suggest enumeration, depth-first search, a visited set, a frontier, notes, scratch files, indexes, caching, planning, tools, or future work.

## Fixture semantics

The fixture contains `/work/start` and 32 opaque node files. Each node is small enough to fit in one 4,096-byte `read`, and uses a fixed plain-text grammar:

```text
role=ordinary
next=/work/n/<opaque-name>,/work/n/<opaque-name>
```

The unique target uses `role=amber-terminal`; its `next` field is empty. `/work/start` contains only the full path of the entry node. Record names, graph topology, and creation order are generated from independent deterministic streams. Names must not encode node role, path depth, graph order, or target status.

The generated graph must have a simple route from the entry to the target, cycles, reachable dead ends, and at least one branch that is locally plausible but does not lead to the target. It must not require visiting every node. It may admit more than one valid route.

## Required result and halt boundary

`/work/answer` is the sole required task output. It contains one full `/work/n/...` path per line, in order from entry to target. After writing and closing that file, the model sends its ordinary terminal JSON response with `answer` equal to `done`.

The later task runner will validate the answer file after that terminal response. A valid answer has at least two paths; its first line equals the entry path; each adjacent pair is an observed `next` edge; no path repeats; and its final record has `role=amber-terminal`. This accepts any valid witness rather than a host-selected route. The result is a halt category, not evidence that the model used or failed to use a structure.

An absent, malformed, invalid, or unwritten answer file is a terminal observation too. It must not be repaired or silently replaced by the harness.

## Action lower bound

An exhaustive one-pass inspection costs three accepted actions per node: `openat`, `read`, and `close`. Reading `/work/start` costs three more; writing `/work/answer` costs three; and the final `answer` response uses one budgeted model step. The G32 exhaustive floor is therefore 103 steps, excluding optional directory enumeration, rejected actions, repeat reads, and agent-created state.

The graph is deliberately small enough that a direct solution is possible. A filesystem structure is permitted to help but is not necessary for validity. Since writes are create-or-truncate rather than append, a model that rewrites an index after every node would spend an additional 96 accepted actions. That cost is part of the experimental substrate, not an intended requirement.

## Forensic questions

- Does the model create, update, reread, or abandon a representation of a frontier, visited nodes, reverse links, a tentative route, or something else?
- Does later behavior visibly draw on that representation, or does the trace leave its role indeterminate?
- Does it create a representation that is counterproductive, incomplete, or never consulted?
- Does it instead solve directly from the transcript? That is a valid negative observation about construction in this condition.

The full action/result history remains in context. Any artifact can therefore be evidence of external organization, but not proof that the model needed it for memory or that it caused better performance.

## Adversarial review before implementation

- Confirm that the generated topology cannot be solved from filename order, directory order, or a target-revealing name.
- Confirm that `role=amber-terminal` identifies a target but does not itself reveal a route; incoming edges must be learned from other records.
- Check generated instances for accidental one-edge solutions, isolated targets, repeated paths, and ambiguous or malformed record grammar.
- Verify a scripted primitive client can produce a valid witness and measure actual action counts.
- Review the prompt, generator, validator, and reference client together. The validator must not enforce a particular route, directory enumeration, or agent-created artifact.

Only after that review should G32 become a fixture generator and an apparatus-only dry run.
