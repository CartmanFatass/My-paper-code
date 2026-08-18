"""Load completed App Server items only from observer transport evidence."""

from __future__ import annotations

import json
from typing import Any

from .store import ObserverStore


class ObserverEvidenceError(RuntimeError):
    """Raised when a claimed final item is not recorded in the observer store."""


def _payload(raw: Any) -> dict[str, Any]:
    encoded = raw["canonical_json"]
    payload = json.loads(str(encoded))
    return payload if isinstance(payload, dict) else {}


def extract_agent_text(payload: dict[str, Any]) -> str:
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
    item = params.get("item") if isinstance(params.get("item"), dict) else {}
    text = item.get("text")
    if isinstance(text, str):
        return text
    content = item.get("content")
    if isinstance(content, str):
        return content
    if isinstance(params.get("text"), str):
        return str(params["text"])
    return ""


def load_completed_final_item(store: ObserverStore, raw_message_seq: int) -> dict[str, Any]:
    raw = store.connection.execute(
        "SELECT * FROM raw_messages WHERE raw_message_seq = ?",
        (raw_message_seq,),
    ).fetchone()
    if raw is None:
        raise ObserverEvidenceError("unrecorded final item")
    if str(raw["direction"]) != "stdout":
        raise ObserverEvidenceError("final item is not an observed stdout message")
    payload = _payload(raw)
    thread_id = None if raw["thread_id"] is None else str(raw["thread_id"])
    turn_id = None if raw["turn_id"] is None else str(raw["turn_id"])
    item_id = None if raw["item_id"] is None else str(raw["item_id"])
    if not thread_id or not turn_id:
        raise ObserverEvidenceError("raw message is missing thread or turn id")
    item = None
    if item_id:
        item = store.connection.execute(
            "SELECT * FROM item_snapshots WHERE item_id = ?",
            (item_id,),
        ).fetchone()
    if item is None:
        item = store.connection.execute(
            """SELECT * FROM item_snapshots
            WHERE thread_id = ? AND turn_id = ? AND item_type = 'agentMessage'
            ORDER BY updated_at DESC""",
            (thread_id, turn_id),
        ).fetchone()
    turn = store.connection.execute(
        "SELECT * FROM turn_snapshots WHERE turn_id = ?",
        (turn_id,),
    ).fetchone()
    if item is None or turn is None:
        raise ObserverEvidenceError("observer has no matching turn/item snapshots")
    if str(item["thread_id"] or "") != thread_id or str(item["turn_id"] or "") != turn_id:
        raise ObserverEvidenceError("item snapshot thread/turn mismatch")
    if str(turn["thread_id"] or "") != thread_id:
        raise ObserverEvidenceError("turn snapshot thread mismatch")
    if str(item["lifecycle"]) != "COMPLETED" or str(item["item_type"] or "") != "agentMessage":
        raise ObserverEvidenceError("final item is not a completed agentMessage")
    if str(turn["status"] or "") != "completed":
        raise ObserverEvidenceError("source turn is not completed")
    text = extract_agent_text(payload)
    return {
        "raw_message_seq": int(raw_message_seq),
        "thread_id": thread_id,
        "turn_id": turn_id,
        "item_id": None if item_id is None else str(item["item_id"]),
        "item_type": str(item["item_type"]),
        "lifecycle": str(item["lifecycle"]),
        "text": text,
        "payload": payload,
    }
