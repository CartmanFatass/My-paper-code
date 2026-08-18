"""Mechanical thread timeline export. No lexical disposition."""

from __future__ import annotations

import json
from typing import Any

from .store import ObserverStore

FORBIDDEN_TIMELINE_PHRASES = (
    "workflow failed",
    "task blocked",
    "direction inactive",
)


def thread_timeline(store: ObserverStore, thread_id: str) -> dict[str, object]:
    events = []
    for row in store.events_for_thread(thread_id):
        payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
        events.append(
            {
                "event_seq": row["event_seq"],
                "observed_at": row["observed_at"],
                "event_kind": row["event_kind"],
                "thread_id": row["thread_id"],
                "turn_id": row["turn_id"],
                "item_id": row["item_id"],
                "mechanical_status": row["mechanical_status"],
                "payload": payload,
                "raw_message_seq": row["raw_message_seq"],
                "run_id": row["run_id"],
            }
        )
    snapshot = store.latest_thread_snapshot(thread_id)
    return {"thread_id": thread_id, "snapshot": snapshot, "events": events}


def render_thread_timeline_markdown(timeline: dict[str, Any]) -> str:
    lines = [f"# Thread {timeline.get('thread_id')}", ""]
    for event in timeline.get("events") or []:
        status = event.get("mechanical_status")
        suffix = f" status={status}" if status else ""
        lines.append(
            f"- seq={event.get('event_seq')} raw={event.get('raw_message_seq')} "
            f"run={event.get('run_id')} {event.get('event_kind')}{suffix}"
        )
    text = "\n".join(lines) + "\n"
    lowered = text.lower()
    for phrase in FORBIDDEN_TIMELINE_PHRASES:
        if phrase in lowered:
            raise ValueError(f"timeline leaked semantic phrase: {phrase}")
    return text
