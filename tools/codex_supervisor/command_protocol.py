"""Parse the managed-actor command envelope from a completed agent message."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from .managed_models import FORBIDDEN_COMMAND_KEYS, ManagedActionKind, STAGE4_ACTIONS

ENVELOPE_OPEN = "<HMASD_MANAGED_ACTOR_COMMAND_V1>"
ENVELOPE_CLOSE = "</HMASD_MANAGED_ACTOR_COMMAND_V1>"
_ENVELOPE_RE = re.compile(
    re.escape(ENVELOPE_OPEN) + r"(.*?)" + re.escape(ENVELOPE_CLOSE),
    re.DOTALL,
)


class CommandProtocolError(ValueError):
    """Raised when a managed command envelope is missing or invalid."""


def _forbid_keys(value: object, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in FORBIDDEN_COMMAND_KEYS:
                raise CommandProtocolError(f"forbidden command key: {key}")
            _forbid_keys(item, f"{path}.{key}")
    elif isinstance(value, list):
        for item in value:
            _forbid_keys(item, path)


def extract_managed_command(text: str) -> dict[str, Any] | None:
    matches = list(_ENVELOPE_RE.finditer(text or ""))
    if not matches:
        return None
    if len(matches) > 1:
        raise CommandProtocolError("more than one managed command envelope")
    raw = matches[0].group(1).strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CommandProtocolError("managed command is not JSON") from exc
    if not isinstance(payload, dict):
        raise CommandProtocolError("managed command must be an object")
    _forbid_keys(payload)
    action = payload.get("action_kind")
    try:
        kind = ManagedActionKind(str(action))
    except ValueError as exc:
        raise CommandProtocolError(f"unknown action_kind: {action}") from exc
    if kind not in STAGE4_ACTIONS:
        raise CommandProtocolError(f"action not allowed: {kind.value}")
    if payload.get("schema_version") != "1.0":
        raise CommandProtocolError("unsupported schema_version")
    if payload.get("packet_kind") != "MANAGED_ACTOR_COMMAND":
        raise CommandProtocolError("packet_kind must be MANAGED_ACTOR_COMMAND")
    if kind is ManagedActionKind.CONTEXT_REANCHOR_ACK:
        expected = payload.get("expected")
        if not isinstance(expected, Mapping):
            raise CommandProtocolError("CONTEXT_REANCHOR_ACK requires expected currentness fields")
        required = ("checkpoint_id", "state_version", "epoch_id", "epoch_revision")
        missing = [key for key in required if key not in expected]
        if missing:
            raise CommandProtocolError(f"CONTEXT_REANCHOR_ACK missing {missing}")
    if kind is ManagedActionKind.MAILBOX_ACK:
        inner = payload.get("payload")
        if not isinstance(inner, Mapping) or not isinstance(inner.get("message_ids"), list) or not inner["message_ids"]:
            raise CommandProtocolError("MAILBOX_ACK requires payload.message_ids")
    if kind is ManagedActionKind.MAILBOX_INTAKE:
        inner = payload.get("payload")
        items = inner.get("items") if isinstance(inner, Mapping) else None
        if not isinstance(items, list) or not items:
            raise CommandProtocolError("MAILBOX_INTAKE requires payload.items")
        for item in items:
            if not isinstance(item, Mapping) or "message_id" not in item or "intake_kind" not in item:
                raise CommandProtocolError("MAILBOX_INTAKE items require message_id and intake_kind")
    if kind is ManagedActionKind.MANAGED_PACKET_SEND:
        inner = payload.get("payload")
        if not isinstance(inner, Mapping):
            raise CommandProtocolError("MANAGED_PACKET_SEND requires payload")
        required = ("packet_kind", "target_alias", "payload_ref", "marker")
        missing = [key for key in required if not inner.get(key)]
        if missing:
            raise CommandProtocolError(f"MANAGED_PACKET_SEND missing {missing}")
    return payload


def extract_from_completed_item(*, item_type: str, lifecycle: str, text: str) -> dict[str, Any] | None:
    if lifecycle != "COMPLETED":
        raise CommandProtocolError("command source turn/item is not completed")
    if item_type != "agentMessage":
        raise CommandProtocolError("command source must be a completed agentMessage")
    return extract_managed_command(text)
