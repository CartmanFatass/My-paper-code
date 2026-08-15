#!/usr/bin/env python3
"""Perform small, profile-aware terminal-shape checks for SubagentStop.

The hook never decides scientific or workflow acceptance.  It only asks a
known manager/leaf to return the minimum conclusion-first handoff shape.  An
unknown payload shape is left untouched so provider schema changes do not turn
every stop into a false failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Iterable


L1_TYPES = {
    "hmasd-workflow-design-manager",
    "hmasd-code-project-manager",
    "hmasd-independent-research-explorer",
}
L2_TYPES = {
    "hmasd-workflow-auditor",
    "hmasd-workflow-implementer",
    "hmasd-workflow-reviewer",
    "hmasd-code-scout",
    "hmasd-implementer",
    "hmasd-implementer-terra",
    "hmasd-reviewer",
    "hmasd-verifier",
    "hmasd-cpm-mechanical",
    "hmasd-experiment-operator",
    "hmasd-research-scout",
    "hmasd-research-innovator",
    "hmasd-research-critic",
    "hmasd-research-principles-analyst",
    "hmasd-explorer-mechanical",
    "hmasd-research-artifact-writer",
    "hmasd-agentify-transport",
}


def _agent_type(payload: dict[str, Any]) -> str:
    value = payload.get("agent_type") or payload.get("agentType") or payload.get("subagent_type")
    return value.strip().lower() if isinstance(value, str) else ""


def _strings(value: Any, keys: Iterable[str], depth: int = 0) -> list[str]:
    if depth > 3:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        found: list[str] = []
        for key in keys:
            item = value.get(key)
            if isinstance(item, str):
                found.append(item)
            elif isinstance(item, (dict, list)):
                found.extend(_strings(item, keys, depth + 1))
        if found:
            return found
        for item in value.values():
            if isinstance(item, (dict, list)):
                found.extend(_strings(item, keys, depth + 1))
        return found
    if isinstance(value, list):
        found: list[str] = []
        for item in value:
            found.extend(_strings(item, keys, depth + 1))
        return found
    return []


def _terminal_text(payload: dict[str, Any]) -> str:
    keys = (
        "last_assistant_message",
        "agent_message",
        "final_message",
        "message",
        "output",
        "result",
        "summary",
        "response",
    )
    return "\n".join(_strings(payload, keys)).strip()


def _has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE | re.DOTALL) is not None


def _failure(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("stop_hook_active") is True:
        return {
            "continue": False,
            "stopReason": "invalid_subagent_result",
            "systemMessage": reason,
        }
    return {"decision": "block", "reason": reason + " Return a conclusion-first handoff and continue once."}


def _check(agent_type: str, text: str) -> str | None:
    if agent_type in L2_TYPES:
        required = (
            ("conclusion", r"\b(conclusion|complete|completed|blocked|unresolved|status\s*=)\b"),
            ("artifact/change", r"(changed[_ ]paths?|owned[_ ]paths?|artifact|output|evidence|diff|proposal|result)"),
            ("direct check", r"(check|test|verify|validation|command|compile|smoke)"),
            ("residual issue", r"(residual|uncertain|uncertainty|limitation|remaining|blocker|unknown)"),
        )
    elif agent_type in L1_TYPES:
        required = (
            ("conclusion", r"\b(conclusion|accepted|acceptance|blocked|unresolved|status\s*=)\b"),
            ("child synthesis", r"(child|l2|integrat|synthesi|owner)"),
            ("canonical proposal", r"(proposal|canonical|based[_ ]on[_ ]revision|return[- ]to[- ]root|next action)"),
            ("residual/blocked reason", r"(residual|uncertain|uncertainty|limitation|blocked|remaining|next action)"),
        )
    else:
        return None
    missing = [label for label, pattern in required if not _has(text, pattern)]
    return "SubagentStop result is missing " + ", ".join(missing) if missing else None


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root-stop", action="store_true")
    args, _ = parser.parse_known_args()
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, TypeError):
        return 0
    if args.root_stop:
        return 0
    if not isinstance(payload, dict):
        return 0
    event = payload.get("hook_event_name") or payload.get("event_name") or payload.get("event")
    if str(event).replace("_", "").lower() != "subagentstop":
        return 0
    agent_type = _agent_type(payload)
    if agent_type not in L1_TYPES | L2_TYPES:
        return 0
    text = _terminal_text(payload)
    if not text:
        return 0
    reason = _check(agent_type, text)
    if reason:
        print(json.dumps(_failure(reason, payload), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
