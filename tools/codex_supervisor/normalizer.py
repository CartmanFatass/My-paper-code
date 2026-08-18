"""Map App Server protocol objects to mechanical normalized events."""

from __future__ import annotations

from typing import Any, Mapping

from .models import FORBIDDEN_EVENT_KINDS, NormalizedEvent, RpcShape
from .protocol import classify_rpc_message, extract_protocol_ids
from .store import ObserverStore

# Notification methods observed in official docs and host ServerNotification.json
# (codex-cli 0.147.0). Unknown methods become UNKNOWN_NOTIFICATION_OBSERVED.
NOTIFICATION_KINDS = {
    "thread/started": "THREAD_STARTED_OBSERVED",
    "thread/archived": "THREAD_ARCHIVED_OBSERVED",
    "thread/unarchived": "THREAD_UNARCHIVED_OBSERVED",
    "thread/closed": "THREAD_CLOSED_OBSERVED",
    "turn/started": "TURN_STARTED_OBSERVED",
    "turn/completed": "TURN_COMPLETED_OBSERVED",
    "turn/diff/updated": "TURN_DIFF_UPDATED_OBSERVED",
    "turn/plan/updated": "TURN_PLAN_UPDATED_OBSERVED",
    "item/started": "ITEM_STARTED_OBSERVED",
    "item/completed": "ITEM_COMPLETED_OBSERVED",
    "thread/tokenUsage/updated": "TOKEN_USAGE_UPDATED_OBSERVED",
    "configWarning": "CONFIG_WARNING_OBSERVED",
    "warning": "SERVER_WARNING_OBSERVED",
}


def _delta_payload(params: Mapping[str, Any]) -> dict[str, Any]:
    text = params.get("delta")
    if isinstance(text, str):
        return {"delta_present": True, "delta_bytes": len(text.encode("utf-8"))}
    return {"delta_present": False, "delta_bytes": 0}


def _warning_payload(params: Mapping[str, Any]) -> dict[str, Any]:
    text = params.get("message")
    if text is None:
        text = params.get("warning")
    length = len(str(text).encode("utf-8")) if text is not None else 0
    return {"warning_present": text is not None, "warning_bytes": length}


def _item_type(params: Mapping[str, Any]) -> str | None:
    item = params.get("item")
    if isinstance(item, Mapping) and item.get("type") is not None:
        return str(item.get("type"))
    return None


def _status_type(thread: Mapping[str, Any]) -> object:
    status = thread.get("status")
    if isinstance(status, Mapping):
        return status.get("type")
    return status


def thread_snapshot_fields(thread: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status_type": _status_type(thread),
        "preview": thread.get("preview"),
        "ephemeral": thread.get("ephemeral"),
        "path": thread.get("path"),
    }


def normalize_message(
    message: Mapping[str, Any],
    raw_message_seq: int,
    run_id: str,
    observed_at: str,
) -> NormalizedEvent | None:
    shape = classify_rpc_message(message)
    ids = extract_protocol_ids(message)
    params = message.get("params") if isinstance(message.get("params"), Mapping) else {}
    result = message.get("result") if isinstance(message.get("result"), Mapping) else {}
    if shape is RpcShape.RESPONSE:
        if "error" in message:
            error = message.get("error") if isinstance(message.get("error"), Mapping) else {}
            code = error.get("code") if isinstance(error, Mapping) else None
            kind = "SERVER_OVERLOAD_OBSERVED" if code == -32001 else "RPC_ERROR_OBSERVED"
            payload = {
                "error_present": True,
                "error_code_present": code is not None,
                "error_code": code,
            }
            return NormalizedEvent(
                kind, raw_message_seq, run_id, ids.thread_id, ids.turn_id, ids.item_id, None, payload, observed_at
            )
        payload: dict[str, Any] = {"method": ids.method}
        thread = result.get("thread") if isinstance(result.get("thread"), Mapping) else None
        if isinstance(thread, Mapping):
            payload.update(thread_snapshot_fields(thread))
        elif isinstance(result.get("data"), list):
            payload["thread_count"] = sum(1 for item in result["data"] if isinstance(item, Mapping))
        return NormalizedEvent(
            "RPC_RESPONSE_OBSERVED",
            raw_message_seq,
            run_id,
            ids.thread_id,
            ids.turn_id,
            ids.item_id,
            None,
            payload,
            observed_at,
        )
    if shape is RpcShape.REQUEST:
        return NormalizedEvent(
            "SERVER_REQUEST_OBSERVED",
            raw_message_seq,
            run_id,
            ids.thread_id,
            ids.turn_id,
            ids.item_id,
            None,
            {"method": ids.method},
            observed_at,
        )
    if shape is not RpcShape.NOTIFICATION:
        return None
    method = ids.method or ""
    if method.endswith("/delta"):
        kind = "ITEM_DELTA_OBSERVED"
        payload = _delta_payload(params)
        payload["item_type"] = _item_type(params)
    elif method in NOTIFICATION_KINDS:
        kind = NOTIFICATION_KINDS[method]
        payload = {}
        if kind in {"CONFIG_WARNING_OBSERVED", "SERVER_WARNING_OBSERVED"}:
            payload = _warning_payload(params)
        elif kind == "TURN_COMPLETED_OBSERVED":
            turn = params.get("turn") if isinstance(params.get("turn"), Mapping) else {}
            status = turn.get("status") if isinstance(turn, Mapping) else None
            error = turn.get("error") if isinstance(turn, Mapping) else None
            payload = {
                "status": status,
                "error_present": error is not None,
                "error_code_present": isinstance(error, Mapping) and "code" in error,
            }
            if isinstance(error, Mapping):
                payload["error"] = {key: error.get(key) for key in ("type", "code") if key in error}
        elif kind == "TURN_STARTED_OBSERVED":
            payload = {"status": "inProgress"}
        elif kind in {"ITEM_STARTED_OBSERVED", "ITEM_COMPLETED_OBSERVED"}:
            payload = {"item_type": _item_type(params)}
        elif kind == "THREAD_STARTED_OBSERVED":
            thread = params.get("thread") if isinstance(params.get("thread"), Mapping) else {}
            payload = thread_snapshot_fields(thread) if isinstance(thread, Mapping) else {}
    else:
        kind = "UNKNOWN_NOTIFICATION_OBSERVED"
        payload = {"method": method}
    if kind in FORBIDDEN_EVENT_KINDS:
        raise ValueError(f"forbidden event kind: {kind}")
    status = None
    if kind == "TURN_COMPLETED_OBSERVED":
        raw_status = payload.get("status")
        status = str(raw_status) if raw_status is not None else None
    elif kind == "TURN_STARTED_OBSERVED":
        status = "inProgress"
    return NormalizedEvent(
        kind,
        raw_message_seq,
        run_id,
        ids.thread_id,
        ids.turn_id,
        ids.item_id,
        status,
        payload,
        observed_at,
    )


def apply_normalized_event(store: ObserverStore, event: NormalizedEvent) -> int:
    return store.apply_normalized_event(event)
