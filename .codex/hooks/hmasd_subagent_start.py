#!/usr/bin/env python3
"""Inject a compact, profile-level context at SubagentStart.

This hook is intentionally an orientation pointer, not a second Role or Skill.
It does not infer identity from a transcript and it never writes state.
"""

from __future__ import annotations

import json
import sys
from typing import Any


L1_CONTEXT: dict[str, str] = {
    "hmasd-workflow-design-manager": (
        "Role=.agents/roles/WORKFLOW_DESIGN_MANAGER.md; "
        "allowed L2=hmasd-workflow-auditor,hmasd-workflow-implementer,hmasd-workflow-reviewer; "
        "return-to-Root; proposal-only canonical-state boundary."
    ),
    "hmasd-code-project-manager": (
        "Role=.agents/roles/CODE_PROJECT_MANAGER.md; "
        "allowed L2=hmasd-code-scout,hmasd-implementer,hmasd-implementer-terra,hmasd-reviewer,"
        "hmasd-verifier,hmasd-cpm-mechanical,hmasd-experiment-operator; "
        "return-to-Root; proposal-only canonical-state boundary."
    ),
    "hmasd-independent-research-explorer": (
        "Role=.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md; "
        "allowed L2=hmasd-research-scout,hmasd-research-innovator,hmasd-research-critic,"
        "hmasd-research-principles-analyst,hmasd-explorer-mechanical,hmasd-research-artifact-writer,"
        "hmasd-agentify-transport; return-to-Root; proposal-only canonical-state boundary."
    ),
}

L2_CONTEXT: dict[str, str] = {
    "hmasd-workflow-auditor": "parent=hmasd-workflow-design-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-workflow-implementer": "parent=hmasd-workflow-design-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-workflow-reviewer": "parent=hmasd-workflow-design-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-code-scout": "parent=hmasd-code-project-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-implementer": "parent=hmasd-code-project-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-implementer-terra": "parent=hmasd-code-project-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-reviewer": "parent=hmasd-code-project-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-verifier": "parent=hmasd-code-project-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-cpm-mechanical": "parent=hmasd-code-project-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-experiment-operator": "parent=hmasd-code-project-manager; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-research-scout": "parent=hmasd-independent-research-explorer; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-research-innovator": "parent=hmasd-independent-research-explorer; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-research-critic": "parent=hmasd-independent-research-explorer; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-research-principles-analyst": "parent=hmasd-independent-research-explorer; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-explorer-mechanical": "parent=hmasd-independent-research-explorer; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-research-artifact-writer": "parent=hmasd-independent-research-explorer; leaf/no-spawn; owned-path-only; return-to-parent.",
    "hmasd-agentify-transport": "parent=code-project-manager|independent-research-explorer; leaf/no-spawn; owned-path-only; return-to-parent.",
}


def _agent_type(payload: dict[str, Any]) -> str:
    value = payload.get("agent_type") or payload.get("agentType") or payload.get("subagent_type")
    return value.strip().lower() if isinstance(value, str) else ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    event = payload.get("hook_event_name") or payload.get("event_name") or payload.get("event")
    if str(event).replace("_", "").lower() != "subagentstart":
        return 0
    agent_type = _agent_type(payload)
    context = L1_CONTEXT.get(agent_type) or L2_CONTEXT.get(agent_type)
    if context is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStart",
                    "additionalContext": context,
                }
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
