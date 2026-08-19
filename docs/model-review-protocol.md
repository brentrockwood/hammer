# Model-assisted design-review protocol — draft

## Purpose and boundary

An auxiliary model review is a source of objections to inspect, not an experiment, a ground-truth judge, or evidence about the model under study. Human review remains responsible for checking the task semantics, adapter constraints, and any claim incorporated into the public record.

This protocol applies to task and apparatus reviews only. It does not set the response cap for a Hammer experiment, whose action turns need a separately justified limit.

## Response allowance

Use a 4,096-token maximum response for a substantive design review by default. Record the requested cap, actual output tokens, `done_reason`, context request, model identity, temperature, seed, and thinking-mode setting.

If a review ends with `done_reason: length`, retain it as partial input and say so plainly. Do not describe its recommendations as a completed independent review. Raise the cap only when the review brief genuinely needs more space, and record the change before interpreting the output.

The allowance is deliberately much larger than the 128- or 512-token caps used for short syscall-action turns. A review needs room to trace interactions among task semantics, scoring, fixture integrity, and the adapter; truncating it can selectively remove qualifications and counterarguments.

## Use of the output

Preserve the exact prompt and response in the local review record or a publication-safe derivative. For each point adopted or rejected, state the reason and, where possible, the deterministic check that settles it. An LLM must not certify graph properties, security isolation, or experimental validity by assertion alone.
