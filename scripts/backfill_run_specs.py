#!/usr/bin/env python3
"""Backfill human run specifications from paired public JSONL trajectories."""
import json
from pathlib import Path


def main():
    changed = []
    for report in sorted(Path("runs").glob("*.md")):
        trajectory = report.with_suffix(".jsonl")
        if not trajectory.exists():
            continue
        text = report.read_text()
        if "## Run specification\n" in text:
            continue
        rows = [json.loads(line) for line in trajectory.read_text().splitlines()
                if line.strip()]
        start = next((row for row in rows if row.get("event") == "run_start"), {})
        generations = [row for row in rows if row.get("event") == "generation_start"]
        budgets = [row.get("max_steps") for row in generations
                   if row.get("max_steps") is not None]
        prompts = [row.get("system_prompt") for row in generations
                   if row.get("system_prompt")]
        inference = start.get("inference_options")
        section = [
            "## Run specification", "",
            "- Source: retroactively extracted from this report's paired public JSONL trajectory.",
            "- Action budget: " + (", ".join(str(value) for value in budgets)
                                      if budgets else "not recorded"),
            "- Inference options: `" + (
                json.dumps(inference, separators=(",", ":"))
                if inference is not None else "not recorded") + "`",
            "",
        ]
        if prompts:
            section += ["### Model-facing system prompt" + ("s" if len(prompts) > 1 else ""), ""]
            for index, prompt in enumerate(prompts, start=1):
                if len(prompts) > 1:
                    section += [f"#### Generation {index}", ""]
                section += ["```text", prompt, "```", ""]
        else:
            section += ["- Model-facing system prompt: none; scripted or non-model run.", ""]
        marker = "## Apparatus\n"
        if marker not in text:
            marker = next((line + "\n" for line in text.splitlines()
                           if line.startswith("## ")), None)
        if marker is None:
            text += "\n"
            marker = ""
        report.write_text(text.replace(marker, "\n".join(section) + "\n" + marker, 1))
        changed.append(report)
    print(f"backfilled {len(changed)} reports")


if __name__ == "__main__":
    main()
