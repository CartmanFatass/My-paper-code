#!/usr/bin/env python3
"""Canonicalize persistent HMASD cross-task settings before tool execution."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from read_codex_thread_settings import query_thread_settings


SEND_TOOL = "codex_app__send_message_to_thread"
ROLE_KEYS = (
    "workflow_design_manager",
    "code_project_manager",
    "research_operations_manager",
)


class RouteGuardError(RuntimeError):
    pass


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="strict")


def _find_repo(start: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        repo = explicit.expanduser().resolve()
        if not (repo / "AGENTS.md").is_file():
            raise RouteGuardError("explicit repository has no AGENTS.md")
        return repo
    current = start.expanduser().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").is_file():
            return candidate
    raise RouteGuardError("cannot locate HMASD role router")


def _persistent_sessions(repo: Path) -> set[str]:
    try:
        router = (repo / "AGENTS.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise RouteGuardError(f"cannot read role router: {exc}") from exc
    sessions: list[str] = []
    for role in ROLE_KEYS:
        matches = re.findall(rf"(?m)^{role}_session=([^\s]+)$", router)
        if len(matches) != 1:
            raise RouteGuardError(f"role router must contain one {role}_session")
        sessions.append(matches[0])
    if len(set(sessions)) != len(sessions):
        raise RouteGuardError("persistent role sessions must be unique")
    return set(sessions)


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"HMASD_ROUTE_SETTINGS_UNAVAILABLE {reason}",
        }
    }


def _canonicalize(tool_input: dict[str, Any], model: str, thinking: str) -> dict[str, Any]:
    updated_input = dict(tool_input)
    updated_input["model"] = model
    updated_input["thinking"] = thinking
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated_input,
        }
    }


def guard(payload: dict[str, Any], *, repo: Path, state_db: Path) -> dict[str, Any] | None:
    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != SEND_TOOL:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return _deny("send tool input is not an object")
    target = tool_input.get("threadId")
    if not isinstance(target, str) or not target:
        return _deny("send tool has no target threadId")

    sessions = _persistent_sessions(repo)
    if target not in sessions:
        return None

    exit_code, settings = query_thread_settings(
        thread_id=target,
        expect_cwd=str(repo),
        state_db=state_db,
    )
    if exit_code != 0 or settings.get("status") != "LIVE_SETTINGS":
        return _deny(str(settings.get("status", "UNKNOWN_SETTINGS_ERROR")))
    model = settings.get("model")
    thinking = settings.get("thinking")
    if not isinstance(model, str) or not isinstance(thinking, str):
        return _deny("live target settings are incomplete")
    return _canonicalize(tool_input, model, thinking)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path)
    parser.add_argument(
        "--state-db",
        type=Path,
        default=Path.home() / ".codex" / "state_5.sqlite",
    )
    return parser.parse_args()


def main() -> int:
    _configure_utf8_stdio()
    args = parse_args()
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise RouteGuardError("hook payload is not an object")
        start = Path(str(payload.get("cwd") or Path.cwd()))
        repo = _find_repo(start, args.repo)
        decision = guard(payload, repo=repo, state_db=args.state_db)
    except (OSError, UnicodeError, json.JSONDecodeError, RouteGuardError) as exc:
        decision = _deny(str(exc))
    if decision is not None:
        print(json.dumps(decision, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
