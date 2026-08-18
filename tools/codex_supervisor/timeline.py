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


def mailbox_timeline(store: ObserverStore, *, target_actor_context_id: str | None = None) -> list[dict[str, object]]:
    sql = "SELECT * FROM mailbox_messages"
    params: list[object] = []
    if target_actor_context_id:
        sql += " WHERE target_actor_context_id = ?"
        params.append(target_actor_context_id)
    sql += " ORDER BY created_at, message_id"
    rows = store.connection.execute(sql, params).fetchall()
    events = []
    for row in rows:
        events.append(
            {
                "message_id": row["message_id"],
                "kind": row["message_kind"],
                "delivery_state": row["delivery_state"],
                "intake_state": row["intake_state"],
                "target_actor_context_id": row["target_actor_context_id"],
                "subject_ref": row["subject_ref"],
                "payload_ref": row["payload_ref"],
                "created_at": row["created_at"],
            }
        )
    return events


def wake_timeline(store: ObserverStore, wake_batch_id: str | None = None) -> list[dict[str, object]]:
    sql = "SELECT * FROM wake_batches"
    params: list[object] = []
    if wake_batch_id:
        sql += " WHERE wake_batch_id = ?"
        params.append(wake_batch_id)
    sql += " ORDER BY prepared_at, wake_batch_id"
    rows = store.connection.execute(sql, params).fetchall()
    events = []
    for row in rows:
        events.append(
            {
                "wake_batch_id": row["wake_batch_id"],
                "binding_id": row["binding_id"],
                "thread_id": row["thread_id"],
                "state": row["state"],
                "client_user_message_id": row["client_user_message_id"],
                "app_server_request_id": row["app_server_request_id"],
                "app_server_turn_id": row["app_server_turn_id"],
                "prepared_at": row["prepared_at"],
                "submitted_at": row["submitted_at"],
                "completed_at": row["completed_at"],
            }
        )
    return events


def binding_timeline(store: ObserverStore, binding_id: str) -> list[dict[str, object]]:
    rows = store.connection.execute(
        """SELECT * FROM managed_binding_events
        WHERE binding_id = ? ORDER BY binding_event_seq""",
        (binding_id,),
    ).fetchall()
    return [
        {
            "binding_event_seq": row["binding_event_seq"],
            "binding_id": row["binding_id"],
            "event_kind": row["event_kind"],
            "payload_json": row["payload_json"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


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
