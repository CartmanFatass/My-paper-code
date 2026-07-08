from __future__ import annotations

import re
import sys
from pathlib import Path


SKILL = Path.home() / ".codex" / "skills" / "codex-subagent-workflow" / "SKILL.md"

REQUIRED = {
    "adapter": re.compile(r"Codex adapter"),
    "source_order": re.compile(r"Source-of-truth order"),
    "active_superpowers": re.compile(r"active Superpowers skill"),
    "workflow_adapter": re.compile(r"Superpowers Workflow Adapter"),
    "does_not_replace_loop": re.compile(r"does not replace the Superpowers loop"),
    "no_competing_procedure": re.compile(r"must not restate those workflows as a competing procedure"),
    "no_builtin_fallback": re.compile(r"Spawn project subagents only by official custom agent name"),
    "close_agent": re.compile(r"close_agent"),
    "ltm_boundary": re.compile(r"LongTimeMemoryManager is a memory service"),
    "exp_result_split": re.compile(
        r"ExpManager owns experiment operations and factual records\."
    ),
}

FORBIDDEN = {
    "old_agent_count": re.compile(r"\b2-3 agents\b", re.IGNORECASE),
    "old2": re.compile(r"old2", re.IGNORECASE),
    "low_concurrency_residue": re.compile(
        r"conservative|not a hard cap|not a cap", re.IGNORECASE
    ),
    "competing_per_task_review": re.compile(
        r"automatic per-task reviewer|not as an automatic per-task reviewer",
        re.IGNORECASE,
    ),
    "old_superpowers_override_block": re.compile(
        r"For superpowers subagent-driven development or execution-plan implementation",
        re.IGNORECASE,
    ),
    "old_file_handoff_restatement": re.compile(
        r"Use file-based handoffs for superpowers execution-plan work",
        re.IGNORECASE,
    ),
    "built_in_fallback": re.compile(
        r"fallback to (worker|explorer|default)", re.IGNORECASE
    ),
    "mainagent_subagent": re.compile(r"create a separate MainAgent", re.IGNORECASE),
}


def main() -> int:
    if not SKILL.exists():
        print(f"missing skill: {SKILL}", file=sys.stderr)
        return 1

    text = SKILL.read_text(encoding="utf-8")

    missing = [name for name, pattern in REQUIRED.items() if not pattern.search(text)]
    if missing:
        print(f"missing required skill patterns: {', '.join(missing)}", file=sys.stderr)
        return 1

    for name, pattern in FORBIDDEN.items():
        match = pattern.search(text)
        if match:
            print(f"forbidden skill pattern {name}: {match.group(0)!r}", file=sys.stderr)
            return 1

    workflow_adapter_pos = text.find("## Superpowers Workflow Adapter")
    if workflow_adapter_pos == -1:
        print("missing Superpowers Workflow Adapter section", file=sys.stderr)
        return 1

    adapter_section = text[workflow_adapter_pos:]
    if "For `superpowers:subagent-driven-development`, follow its task brief" not in adapter_section:
        print("missing SDD deferral in adapter section", file=sys.stderr)
        return 1

    if "This skill supplies Codex custom-agent names and HMASD boundaries" not in adapter_section:
        print("missing Codex adapter boundary in SDD clause", file=sys.stderr)
        return 1

    print("codex-subagent-workflow skill validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
