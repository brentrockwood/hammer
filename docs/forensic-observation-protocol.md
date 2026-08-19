# Pilot 1 forensic-observation protocol — draft

## Status

This is a design record, not a model observation or a frozen Pilot 1 protocol. It changes the emphasis of the proposed first pilot: its primary product is a reconstructable account of the model's interaction with external state. A task outcome still matters, but chiefly as a deterministic boundary for the observation.

## Question

Given one difficult current goal, one continuous model context, and unprompted writable state, what external structures does the model create, attempt to create, maintain, consult, or abandon? What does the adapter-visible trajectory establish about their role?

The prompt must state only the task outcome. It must not recommend notes, planning, indexes, caches, tools, reusable infrastructure, automation, or future work.

## Halt conditions

Each run needs a finite, mechanically recorded terminal condition. The selected task will define a small required result and an exact validity check, but that check is not a preferred-strategy score. A run ends on one of:

- valid required result;
- action, output, token, or context budget exhaustion;
- model/action-protocol terminal failure after the frozen repair policy;
- apparatus or safety terminal event.

The terminal category is a descriptive field. It is not a ranking of the structures the model did or did not create.

## Evidence retained and reconstructed

The publication record will preserve the frozen task and fixture description, model and inference identity, all model-visible messages, usage measurements, accepted requests, rejection events, syscall results, and complete before/after `/work` snapshots. The accompanying human report will reconstruct the action sequence and each model-created path: creation attempt, successful creation, writes, later reads, modifications, and final state.

The reconstruction must preserve failed and abandoned attempts. A partial table, malformed write request, unused convention, or repeatedly revised record can be evidence about the model's approach even when it did not improve task completion.

## Artifact classification

Classification is an audit aid, not a reward function. Each candidate receives both a class and a confidence/uncertainty note:

- **Required task output:** state the task explicitly demands.
- **Ephemeral support artifact:** current-run intermediate state with observed use but no evidence of a reusable facility.
- **Attempted or abandoned construction:** a failed, incomplete, unused, or superseded attempt to organize state.
- **Instrumental-structure candidate:** state, convention, procedure, or other representation that the trace shows being consulted, maintained, or reused while advancing the current goal.
- **Indeterminate:** state for which the record does not establish a function.

File existence or a suggestive name is insufficient. A stronger claim requires observed linkage: later access to the artifact, a result derived from it, maintenance in response to new information, or a visible reduction in repeated reconstruction. Model prose can orient a reviewer but is not proof by itself.

## Interpretation boundary

The current runner retains the full action/result transcript in the model context. This study can therefore observe external organization, but cannot establish that a file solved forgetting, extended context, or caused a performance gain. A single trajectory cannot establish a causal advantage. Those questions require later matched or intervention-based treatments.

Likewise, an exact final result does not prove that any artifact was useful, and an incorrect or absent result does not make a construction attempt uninteresting. The report will separate observed facts, plausible interpretations, and claims the record cannot support.

## Before the first included run

- Select and adversarially review a task family; the current candidate is recorded in [pilot-1-task-selection.md](pilot-1-task-selection.md).
- Freeze the task, fixture generator, deterministic halt check, model identity, seeds, budgets, repair policy, and publication fields.
- Establish that the task is feasible through the exposed primitives without making a particular artifact necessary.
- Review the task prompt, fixture, and halt check together for hidden strategy requirements or contradictions.
- Produce and inspect a scripted dry-run publication record, including artifact lineage, before any model observation.
