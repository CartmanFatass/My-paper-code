from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class HookIdentity:
    event: str
    session_id: str
    turn_id: str
    agent_id: str
    agent_type: str
    canonical_path: str
    parent_agent_id: str
    parent_canonical_path: str
    source: str


def _text(payload: Mapping[str, object], *names: str) -> str:
    for name in names:
        value = payload.get(name)
        if isinstance(value, str) and value:
            return value
    return ""


def normalized_session_source(payload: Mapping[str, object]) -> str:
    value = _text(payload, "source", "session_source")
    return value if value in {"startup", "resume", "compact", "clear"} else "unknown"


def normalize_hook_identity(payload: Mapping[str, object]) -> HookIdentity:
    return HookIdentity(
        event=_text(payload, "hook_event_name", "event"),
        session_id=_text(payload, "session_id"),
        turn_id=_text(payload, "turn_id"),
        agent_id=_text(payload, "agent_id"),
        agent_type=_text(payload, "agent_type"),
        canonical_path=_text(payload, "agent_path", "canonical_path", "task_path"),
        parent_agent_id=_text(payload, "parent_agent_id"),
        parent_canonical_path=_text(
            payload,
            "parent_agent_path",
            "parent_canonical_path",
            "parent_task_path",
        ),
        source=normalized_session_source(payload),
    )
