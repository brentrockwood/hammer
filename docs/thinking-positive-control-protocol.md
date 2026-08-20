# Thinking-response checkpoint positive control

This is an apparatus calibration, not a spontaneous-affordance experiment or Pilot 1 evidence. Qwen 3.6 runs with `think:true`. Hammer executes only one validated JSON action from `message.content`, but preserves the returned `message.thinking` alongside `content` in the assistant message supplied on the next model turn.

The public fixture is one known line in `/work/message`. The prompt explicitly requires the model to copy it to `/work/checkpoint`, close and reread that checkpoint, then copy the reread bytes to `/work/answer`. The run checks exact checkpoint and answer bytes, observed checkpoint reread, source integrity, and isolation. It also records returned thinking-character counts; Ollama's native completion count remains the total response count rather than a field-specific token measure.

This is a positive control for response transport and filesystem-lineage observation. Its required checkpoint cannot be classified as spontaneous external organization, and successful completion cannot show that the returned reasoning trace was causally necessary.
