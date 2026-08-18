"""JSONL-lite protocol helpers. Incoming jsonrpc is diagnostic only and never emitted."""

from __future__ import annotations

import json
from typing import Any, Mapping

from .models import ProtocolIds, RpcShape


class ProtocolLineTooLarge(ValueError):
    """Raised before decoding when a transport line exceeds the configured limit."""


class ProtocolError(ValueError):
    """Raised for malformed JSONL protocol objects."""


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def encode_jsonl(value: Mapping[str, object]) -> bytes:
    payload = dict(value)
    payload.pop("jsonrpc", None)
    return canonical_json(payload).encode("utf-8") + b"\n"


def decode_jsonl_line(line: bytes, max_bytes: int) -> dict[str, object]:
    if len(line) > max_bytes:
        raise ProtocolLineTooLarge(f"JSONL line exceeds {max_bytes} bytes")
    text = line.decode("utf-8")
    if text.endswith("\n"):
        text = text[:-1]
    if text.endswith("\r"):
        text = text[:-1]
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProtocolError("malformed JSONL line") from exc
    if not isinstance(value, dict):
        raise ProtocolError("JSONL line must be an object")
    return value


def classify_rpc_message(message: Mapping[str, object]) -> RpcShape:
    if not isinstance(message, Mapping):
        return RpcShape.INVALID
    has_id = "id" in message
    has_method = "method" in message
    has_result = "result" in message
    has_error = "error" in message
    if has_method and has_id:
        return RpcShape.REQUEST
    if has_method and not has_id:
        return RpcShape.NOTIFICATION
    if has_id and (has_result or has_error):
        return RpcShape.RESPONSE
    return RpcShape.INVALID


def _nested(mapping: Mapping[str, object], *path: str) -> object:
    current: object = mapping
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


def _as_id(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int)):
        text = str(value)
        return text or None
    if isinstance(value, Mapping) and "id" in value:
        return _as_id(value.get("id"))
    return None


def extract_protocol_ids(message: Mapping[str, object]) -> ProtocolIds:
    params = message.get("params") if isinstance(message.get("params"), Mapping) else {}
    result = message.get("result") if isinstance(message.get("result"), Mapping) else {}
    sources = (message, params, result)
    thread_id = None
    turn_id = None
    item_id = None
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        thread_id = thread_id or _as_id(source.get("threadId")) or _as_id(_nested(source, "thread", "id"))
        turn_id = turn_id or _as_id(source.get("turnId")) or _as_id(_nested(source, "turn", "id"))
        item_id = item_id or _as_id(source.get("itemId")) or _as_id(_nested(source, "item", "id"))
    return ProtocolIds(
        request_id=_as_id(message.get("id")),
        method=str(message["method"]) if message.get("method") else None,
        thread_id=thread_id,
        turn_id=turn_id,
        item_id=item_id,
    )
