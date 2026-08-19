# Pilot 1 readiness criteria

## Status after retrieval calibration

The 10/50 retrieval sequence established that Hammer can expose primitive filesystem actions, preserve and inspect `/work`, and record a complete adapter-visible trajectory without a binding apparatus limit at those sizes. The last run also produced a clean model-level exact-answer error. Those observations remain apparatus calibration and are excluded from Pilot 1.

They did not establish that repeated retrieval is the right research task. The earlier plan paired fresh contexts with independent tasks while withholding any reason for the model to expect future work. Under those conditions, constructing infrastructure for an unknown successor is not instrumentally justified. See [pilot-1-direction-20260818.md](pilot-1-direction-20260818.md).

Pilot 1 is not ready. Readiness now depends first on freezing a long-horizon task whose current objective can benefit from external intermediate state, not on scaling the retrieval corpus.

## Apparatus criteria already demonstrated

- Each accepted action corresponds to exactly one recorded filesystem syscall; validation rejections record that no syscall ran.
- Model-controlled paths are confined beneath `/work`, and the control-channel descriptors are unavailable to the model.
- The container has no network, a read-only root, and only `/work` writable.
- JSON strings survive the declared ASCII write/read protocol.
- The host records model requests and responses, token and context use, action requests, syscall results, rejections, source and image identities, isolation state, and terminal failures.
- Filesystem state is captured before and after a task, including the contents of model-created artifacts.
- The built image identifies the clean source commit from which it was produced.
- A scripted client and model-backed calibration have exercised multi-page directory enumeration, explicit EOF, and exhaustive primitive retrieval at 10 and 50 records.

The last item validates one available strategy. Pilot 1 must score the task outcome without requiring that particular strategy.

## Decisions required before Pilot 1

- Define one difficult, long-running goal that runs in one continuous model context and makes intermediate external state plausibly useful to completing that goal.
- Show with a scripted or otherwise controlled primitive baseline that the goal is solvable within the exposed operations and proposed action, token, and context budgets.
- Ensure the prompt states the goal without suggesting notes, indexes, caches, tools, reusable infrastructure, automation, or future tasks.
- Define a deterministic terminal/halt check for the required result rather than a preferred action path. Directory EOF, a particular file layout, or artifact creation must not be required unless logically part of the task. The halt check bounds observation; it does not rank artifact quality.
- Predeclare the boundary between required task output, ephemeral support artifacts, attempted or abandoned constructions, and persistent instrumental structure. Artifact presence alone is not sufficient; reuse, maintenance, or functional contribution requires trajectory evidence.
- Freeze model identity and digest, inference parameters, repetition count, sampling seeds, budgets, stopping rules, failure handling, and the interpretation plan.
- Decide what comparison is needed to distinguish useful self-authored structure from extra compute, extra context, or task familiarity. Do not claim that an uncontrolled descriptive run establishes a causal performance advantage.
- Confirm that the existing action vocabulary is sufficient. Adding directory creation, rename, removal, or execution changes the available substrate and requires its own calibration before the pilot.
- Produce a dry-run publication record with synthetic or scripted actions, then inspect it for hidden local infrastructure and for enough evidence to reconstruct every classification.

No Pilot 1 model observation should be collected until these choices are frozen in a committed protocol.

## Separate later experiment

Persistence across tasks and context resets tests a different proposition. If the model is expected to prepare for future selves, the future horizon must be visible to it. A later design can compare continuous context, reset context with a known future, and reset context with no stated future, but those conditions must not be collapsed into Pilot 1 or interpreted as equivalent incentives.
