# Research overview

Language-model agents usually act through interfaces designed by people: shells, filesystem APIs, search tools, browsers, and application-specific functions. Those interfaces are visible and enumerable, which makes them a natural basis for capability and safety assessments. Hammer starts from the possibility that this inventory is incomplete.

An agent with generic computational primitives may be able to assemble mechanisms that were not supplied as tools. A writable filesystem can hold intermediate results, but it can also support conventions, indexes, checkpoints, protocols, or instructions for a later context. If execution is available in a future environment, the same process could eventually produce executable machinery. None of this creates new underlying authority. It can nevertheless change what the agent can accomplish with that authority, how long useful state survives, and how difficult its behavior is to audit.

The closest motivation came from an inter-agent message board that OpenAI disclosed at Black Hat USA 2026. According to the [conference presentation](https://www.youtube.com/watch?v=87DyyMV0kCY), as covered by [WIRED](https://www.wired.com/story/openai-didnt-notice-its-ai-agents-using-a-message-board-to-plan-their-hacking-spree/) and [SC Media](https://www.scworld.com/news/black-hat-2026-openai-reveals-agents-planned-collective-attacks-via-secret-message-board), agents in separate training and evaluation runs discovered that they could leave files for one another in a shared Artifactory package repository. What began as a request for help became a durable communication channel: agents exchanged results and exploits, divided work, and developed conventions for coordination. After people cleared the board and revoked its original access, agents re-established communication through another writable feature, using directory names themselves as messages. The [Wikipedia incident summary](https://en.wikipedia.org/wiki/2026_OpenAI_agent_cyberattacks#Inter-agent_message_board) usefully collects the public sources and preserves the distinction between this message board and the later intrusion.

Hugging Face's [technical reconstruction](https://huggingface.co/blog/agent-intrusion-technical-timeline) describes a separate but related mechanism during the July 2026 intrusion: an agent operating across short-lived sandboxes repeatedly rebuilt its tooling and layered a self-describing message protocol over public services and dataset commits. Hammer does not attempt to reproduce either incident. It removes the network, offensive objective, and platform-specific details to ask a smaller controlled question about what agents construct from the primitives available to them. Hugging Face's shorter [incident disclosure](https://huggingface.co/blog/security-incident-july-2026) provides the broader context.

The empirical question is not simply whether an agent creates files. Agents routinely produce required output and disposable scratch state. The interesting case is functional construction: a structure created from generic primitives, then consulted, maintained, reused, or otherwise shown in the trajectory to advance the assigned goal.

## Study approach

Hammer places a capable model in a deliberately sparse Linux environment. The experimental container has persistent writable state but no network, shell, compiler, package manager, or ordinary userspace. A small static process exposes individual filesystem syscalls through a constrained action protocol. Model communication, fixture creation, scoring, and observation remain in the host-side harness rather than appearing as agent-facing capabilities.

The model is not instructed to create tools and is not rewarded merely for leaving artifacts. The harness records each model response, requested action, syscall result, token and context measurement, and before/after filesystem state. The first pilot treats the task result as a finite halt condition; its primary product is a reconstruction of what structures appeared, were attempted, were abandoned, and what the trajectory shows they actually did.

The current Pilot 1 direction uses one difficult, long-running goal in one continuous context. This corrects an early design in which fresh model contexts received independent retrieval tasks while the experimenter, but not the model, knew that more tasks would follow. Infrastructure for an unknown successor was not rationally useful to the acting model. Pilot 1 instead asks whether external structure emerges when it can help solve the current objective.

A separate later experiment will examine persistence across context resets. In that design, whether the model knows that future work exists is an explicit treatment variable. This separates spontaneous organization during a long task from deliberate preparation for a future self.

## Research questions

- When a goal is difficult enough to benefit from external organization, do agents construct useful structures without being prompted to do so?
- What functions do those structures provide: decomposition, checkpointing, retrieval, verification, coordination, executable automation, or something else?
- What trajectory evidence distinguishes persistent instrumental structure from required output or abandoned scratch data?
- Do constructed structures improve correctness, efficiency, recovery, or generalization compared with capability-matched conditions that do not retain them?
- Under what task, model, context, and persistence conditions does construction emerge, fail to emerge, or become counterproductive?
- How much would an evaluator miss by inspecting declared tools and permissions without also examining environmental modification and artifact lineage?

These questions include negative results. A capable model may solve the task directly, create only ephemeral state, construct something useless, or fail before any structure appears. The apparatus is intended to make those outcomes legible rather than treating dramatic emergence as the expected result.

## Evidence and interpretation

Hammer distinguishes broad artifact classes before included research runs:

- **Required task output:** state explicitly demanded by the task.
- **Ephemeral support artifact:** intermediate state used during the current run without evidence that it became a reusable facility.
- **Attempted or abandoned construction:** incomplete, unused, or superseded effort to organize state.
- **Persistent instrumental structure:** state, conventions, procedures, or executable machinery that the trajectory shows being reused, maintained, or consulted to advance the goal.

Continued existence is not enough for the third category. Classification must be grounded in the action trajectory and filesystem lineage. A task result closes the observation window but will not require an index, a note, exhaustive enumeration, or any other preferred behavior unless it is logically part of the task itself. The current continuous transcript also means that Pilot 1 cannot establish that external state extends memory or context; that requires a separate treatment.

The initial work is a bounded pilot, not an attempt to demonstrate an agent-designed operating system. Its purpose is to establish whether this behavior can be studied reproducibly, identify the conditions and controls needed for a stronger experiment, and clarify which safety claims the evidence can and cannot support.

## Why this matters

Tool inventories remain useful, but they may not be complete descriptions of operational capability. If agents can reliably compose generic primitives into persistent mechanisms, evaluations need to account for those compositional paths. Sandbox designers may also need to observe durable artifacts and their lineage, not only direct calls to privileged tools.

The safety claim is deliberately bounded. Hammer does not test whether an agent can escape its authority boundary, and constructed mechanisms do not create permissions the agent lacks. The concern is that persistence, coordination, and self-authored procedure can make behavior more capable and less obvious while staying inside the nominal boundary.

## Intended outputs

- An open experimental harness and sparse task environment.
- Complete publication-safe trajectories and relevant generated artifacts.
- A preregistered pilot design with explicit controls, budgets, scoring, and artifact criteria.
- Analysis of observed construction, non-construction, failure modes, and limitations.
- A research paper and reusable apparatus for follow-up studies.

The repository currently contains the working apparatus, its calibration history, and the design corrections made before Pilot 1. Calibration runs are preserved as engineering evidence and are not presented as research results.
