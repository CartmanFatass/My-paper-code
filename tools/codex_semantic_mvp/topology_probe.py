"""Bounded observational probe for Codex hook actor-identity capabilities.

Probe records are not scientific truth, technical acceptance, or a reason to
enable automatic L1/leaf rehydration. A capability may become true only from
unambiguous identity fields, never from a single ambiguous row.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hook_identity import HookIdentity, normalize_hook_identity

PROBE_SCHEMA_VERSION = 1
PROBE_RECORD_FIELDS = (
    "timestamp",
    "event",
    "source",
    "session_id",
    "turn_id",
    "agent_id",
    "agent_type",
    "canonical_path",
    "parent_agent_id",
    "parent_canonical_path",
    "payload_key_names",
)
FORBIDDEN_PROBE_KEYS = frozenset(
    {
        "transcript_path",
        "transcript",
        "last_assistant_message",
        "tool_input",
        "environment",
        "env",
    }
)
COMPACTION_EVENTS = frozenset({"PreCompact", "PostCompact"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def probe_record(
    identity: HookIdentity, payload: Mapping[str, object], *, timestamp: str | None = None
) -> dict[str, object]:
    """Build one redacted probe row from a normalized identity."""
    return {
        "timestamp": timestamp or _now(),
        "event": identity.event,
        "source": identity.source,
        "session_id": identity.session_id,
        "turn_id": identity.turn_id,
        "agent_id": identity.agent_id,
        "agent_type": identity.agent_type,
        "canonical_path": identity.canonical_path,
        "parent_agent_id": identity.parent_agent_id,
        "parent_canonical_path": identity.parent_canonical_path,
        "payload_key_names": sorted(str(key) for key in payload.keys()),
    }


def append_probe_record(
    path: Path, identity: HookIdentity, payload: Mapping[str, object]
) -> None:
    """Append one redacted probe record. Never persist transcript or prose."""
    record = probe_record(identity, payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def load_probe_records(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            records.append(value)
    return records


def _unambiguous_count(records: Iterable[Mapping[str, object]], field: str) -> int:
    seen: set[str] = set()
    for record in records:
        value = _text(record.get(field))
        if value:
            seen.add(value)
    return len(seen)


def _has_unambiguous_field(records: list[Mapping[str, object]], field: str) -> bool:
    """True only when at least two independent rows agree the field is present."""
    return _unambiguous_count(records, field) >= 1 and sum(
        1 for record in records if _text(record.get(field))
    ) >= 2


def summarize_probe(records: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = [dict(record) for record in records]
    compaction = [row for row in rows if _text(row.get("event")) in COMPACTION_EVENTS]
    starts = [row for row in rows if _text(row.get("event")) == "SubagentStart"]
    stops = [row for row in rows if _text(row.get("event")) == "SubagentStop"]
    session_root_compaction = _has_unambiguous_field(compaction, "session_id")
    subagent_compaction = _has_unambiguous_field(compaction, "agent_id")
    canonical_path_available = _has_unambiguous_field(rows, "canonical_path")
    parent_identity_available = _has_unambiguous_field(rows, "parent_agent_id")
    return {
        "schema_version": PROBE_SCHEMA_VERSION,
        "session_root_compaction_identity": session_root_compaction,
        "subagent_start_identity": _has_unambiguous_field(starts, "agent_id"),
        "subagent_stop_identity": _has_unambiguous_field(stops, "agent_id"),
        "subagent_compaction_identity": subagent_compaction,
        "canonical_path_available": canonical_path_available,
        "parent_identity_available": parent_identity_available,
        "automatic_root_rehydration": session_root_compaction,
        "automatic_portfolio_rehydration": session_root_compaction,
        "automatic_l1_rehydration": subagent_compaction and canonical_path_available,
        "automatic_leaf_rehydration": subagent_compaction and canonical_path_available,
        "narrow_pretool_matcher_verified": False,
    }


def write_capability_summary(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(summary), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def summarize_probe_file(probe_path: Path, output_path: Path) -> dict[str, object]:
    summary = summarize_probe(load_probe_records(probe_path))
    write_capability_summary(output_path, summary)
    return summary


def identity_from_payload(payload: Mapping[str, object]) -> HookIdentity:
    return normalize_hook_identity(payload)
