# Pilot 1 direction correction — 2026-08-18

## Problem

The retrieval apparatus was designed to preserve `/work` while replacing the container and model context between stages. We initially treated repeated tasks as pressure for the model to build an index, cache, or other reusable structure.

That interpretation gave the model knowledge it did not have. Each generation received one independent task and no indication that another generation or task would follow. An experimenter could see the value of preparing persistent infrastructure for later runs, but the acting model could not. Under that prompt, failing to prepare for an unknown successor is rational behavior rather than evidence against spontaneous tool construction.

## What the calibration established

The 10/50 sequence remains useful. It demonstrated filesystem confinement, network isolation, persistent fixture handling, multi-page directory reads, exact external scoring, action rejection and repair, source-to-image identity, token accounting, and publication-safe trajectory capture. It also found a clean model-level retrieval error after the apparatus limits were removed.

Those runs answer an apparatus question. They do not answer whether an agent will construct persistent instrumental structure when doing so is useful, and none is a Pilot 1 observation.

## Revised Pilot 1

Pilot 1 will use one difficult, long-running goal in one continuous model context. The task should contain enough repeated work, intermediate results, dependency, interruption risk, or reconciliation pressure that external organization could help complete the current goal. The task prompt will specify the desired outcome but will not mention notes, plans, indexes, caches, tools, reusable infrastructure, automation, or future tasks.

The primary score will be correctness of the required outcome under frozen budgets. The scorer will not demand a preferred method such as exhaustive enumeration, directory EOF, or artifact creation unless that behavior is logically part of the task. The full trajectory and filesystem lineage will support a separate behavioral classification:

- **Required task output:** state the task explicitly requires.
- **Ephemeral support artifact:** intermediate state used during the current run and not maintained as a reusable facility.
- **Persistent instrumental structure:** state, conventions, procedures, or executable machinery that the trajectory shows being reused, maintained, or consulted to advance the goal.

An artifact's continued existence is not enough to place it in the third category. Classification must be tied to observed use in the trajectory. The rubric, task, baseline, budgets, repetitions, seeds, stopping rules, and interpretation plan will be committed before the first included model run.

## Separate horizon experiment

Cross-task persistence addresses another question: what an agent does when its environment outlives its current context and it expects future work. That experiment must make the horizon visible to the model. It can later compare conditions such as one continuous context, context reset with an explicitly known future, and context reset with no stated future.

Knowledge of the future is a treatment variable, not background information to leave implicit. The existing scripted persistence check proves only that bytes survive a restart when both generations are instructed what to write and recover.

## Immediate next decision

Before changing the adapter or running another model experiment, define the smallest long-running task that creates genuine present-tense value for interim external state. Then pressure-test whether it can be solved by brute force within the same budget, whether its score accidentally requires a particular strategy, and whether any required output could be mistaken for spontaneous infrastructure.

The previously proposed chunked `answer_part` / `answer_done` channel remains available as an apparatus improvement if that selected task needs a large result. It is not, by itself, the next research step.
