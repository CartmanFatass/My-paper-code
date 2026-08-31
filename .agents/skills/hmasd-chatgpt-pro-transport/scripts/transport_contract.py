#!/usr/bin/env python3
"""Small, deterministic helpers for the Pro transport control plane.

The browser operator remains responsible for page actions.  This module only
defines the durable packet names, state transitions, monitor identity, tab
lease bookkeeping, and completion-receipt outbox semantics that make those
actions restartable and testable.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping


SCHEMA_VERSION = 2
DEFAULT_FALLBACK_THREAD_ID = "01a04f5a-1c9f-7331-b1d9-249fb767362e"
DEFAULT_FALLBACK_THREAD_URL = f"codex://threads/{DEFAULT_FALLBACK_THREAD_ID}"

STATES = (
    "RECEIVED",
    "DIRECTION_VERIFIED",
    "TAB_OPEN",
    "PAGE_READY",
    "PRO_VERIFIED",
    "PROMPT_READY",
    "UPLOAD_PENDING",
    "UPLOAD_CONFIRMED",
    "SEND_ATTEMPTED",
    "SEND_CONFIRMED",
    "WAITING_GENERATION",
    "WAITING_HEARTBEAT",
    "WAITING_UNKNOWN",
    "WAITING_TIMEOUT",
    "NATURAL_COMPLETION",
    "ARCHIVE_PENDING",
    "ARCHIVED",
    "SEND_UNCERTAIN",
    "SENT_INPUT_MISMATCH",
    "UPLOAD_READY_SEND_DISABLED",
    "MODEL_UNVERIFIED",
    "DIRECTION_UNVERIFIED",
    "ARCHIVE_CONFLICT",
    "RECOVERY_URL_MISMATCH",
    "MONITOR_IDENTITY_MISMATCH",
    "RETURN_RECEIPT_UNCERTAIN",
    "RETURN_RECEIPT_BLOCKED",
    "BLOCKED",
)

PENDING_STATES = frozenset(
    {
        "WAITING_GENERATION",
        "WAITING_HEARTBEAT",
        "WAITING_UNKNOWN",
        "WAITING_TIMEOUT",
        "ARCHIVE_PENDING",
    }
)

TERMINAL_STATES = frozenset(
    {
        "ARCHIVED",
        "SEND_UNCERTAIN",
        "SENT_INPUT_MISMATCH",
        "UPLOAD_READY_SEND_DISABLED",
        "MODEL_UNVERIFIED",
        "DIRECTION_UNVERIFIED",
        "ARCHIVE_CONFLICT",
        "RECOVERY_URL_MISMATCH",
        "MONITOR_IDENTITY_MISMATCH",
        "RETURN_RECEIPT_UNCERTAIN",
        "RETURN_RECEIPT_BLOCKED",
        "BLOCKED",
    }
)

ALLOWED_TRANSITIONS = {
    "RECEIVED": {"DIRECTION_VERIFIED", "DIRECTION_UNVERIFIED", "BLOCKED"},
    "DIRECTION_VERIFIED": {"TAB_OPEN", "PAGE_READY", "BLOCKED"},
    "TAB_OPEN": {"PAGE_READY", "RECOVERY_URL_MISMATCH", "BLOCKED"},
    "PAGE_READY": {"PRO_VERIFIED", "MODEL_UNVERIFIED", "BLOCKED"},
    "PRO_VERIFIED": {"PROMPT_READY", "BLOCKED"},
    "PROMPT_READY": {"UPLOAD_PENDING", "SEND_ATTEMPTED", "BLOCKED"},
    "UPLOAD_PENDING": {"UPLOAD_CONFIRMED", "UPLOAD_READY_SEND_DISABLED", "BLOCKED"},
    "UPLOAD_CONFIRMED": {"SEND_ATTEMPTED", "BLOCKED"},
    "SEND_ATTEMPTED": {"SEND_CONFIRMED", "SEND_UNCERTAIN", "SENT_INPUT_MISMATCH", "BLOCKED"},
    "SEND_CONFIRMED": {"WAITING_GENERATION", "WAITING_UNKNOWN", "BLOCKED"},
    "WAITING_GENERATION": {"WAITING_HEARTBEAT", "WAITING_UNKNOWN", "NATURAL_COMPLETION", "WAITING_TIMEOUT", "BLOCKED"},
    "WAITING_HEARTBEAT": {"WAITING_GENERATION", "WAITING_UNKNOWN", "NATURAL_COMPLETION", "WAITING_TIMEOUT", "BLOCKED"},
    "WAITING_UNKNOWN": {"WAITING_HEARTBEAT", "WAITING_GENERATION", "NATURAL_COMPLETION", "WAITING_TIMEOUT", "BLOCKED"},
    "WAITING_TIMEOUT": {"WAITING_HEARTBEAT", "WAITING_GENERATION", "NATURAL_COMPLETION", "BLOCKED"},
    "NATURAL_COMPLETION": {"ARCHIVE_PENDING", "BLOCKED"},
    "ARCHIVE_PENDING": {"ARCHIVED", "ARCHIVE_CONFLICT", "BLOCKED"},
    "ARCHIVED": set(),
}

_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


def utc_now() -> str:
    """Return a stable ISO-8601 UTC timestamp for persisted control facts."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@contextmanager
def registry_lock(registry_path: Path):
    """Acquire a fail-closed per-registry lock for one bounded state mutation."""

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = registry_path.with_name(registry_path.name + ".lock")
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"REGISTRY_LOCK_BUSY: {lock_path}") from exc
    try:
        try:
            os.write(descriptor, f"pid={os.getpid()}\ncreated={time.time()}\n".encode("ascii"))
        finally:
            os.close(descriptor)
        yield lock_path
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def safe_slug(value: object, *, limit: int = 64) -> str:
    """Convert an external identifier or filename into a bounded filename token."""

    text = str(value).strip()
    text = _SLUG_RE.sub("-", text).strip("-._")
    return (text[:limit].rstrip("-._") or "item")


def packet_id(request_id: str, direction_id: str) -> str:
    """Build the stable logical packet identifier for one request and direction."""

    return f"{safe_slug(request_id)}--{safe_slug(direction_id)}"


def _safe_suffix(filename: str) -> str:
    suffix = Path(filename).suffix
    if not suffix or not re.fullmatch(r"\.[A-Za-z0-9]{1,12}", suffix):
        return ".md"
    return suffix.lower()


def packet_artifacts(
    request_id: str,
    direction_id: str,
    reference_filenames: list[str] | tuple[str, ...] = (),
    *,
    attempt: int = 1,
) -> dict[str, Any]:
    """Return deterministic packet and archive artifact names.

    The logical packet is stable across retries.  The archive directory carries
    an attempt number so a distinct response can never overwrite a prior one.
    """

    if attempt < 1:
        raise ValueError("attempt must be a positive integer")
    logical_id = packet_id(request_id, direction_id)
    archive_id = f"{logical_id}--attempt-{attempt:02d}"
    references = []
    for ordinal, filename in enumerate(reference_filenames, start=1):
        stem = safe_slug(Path(filename).stem, limit=48)
        references.append(
            {
                "ordinal": ordinal,
                "original_filename": Path(filename).name,
                "canonical_filename": f"{logical_id}__01_REF_{ordinal:03d}_{stem}{_safe_suffix(filename)}",
            }
        )
    return {
        "packet_id": logical_id,
        "canonical_form": "logical_packet_manifest",
        "body_filename": f"{logical_id}__00_PROMPT.md",
        "reference_filenames": references,
        "manifest_filename": f"{logical_id}__PACKET_MANIFEST.json",
        "archive_id": archive_id,
        "response_filename": f"{archive_id}__02_RESPONSE.md",
        "transport_facts_filename": f"{archive_id}__03_TRANSPORT_FACTS.json",
    }


def canonical_packet_manifest(
    request: Mapping[str, Any],
    validation: Mapping[str, Any],
    *,
    attempt: int = 1,
    materialized_dir: Path | None = None,
) -> dict[str, Any]:
    """Build the manifest that binds body and reference files into one packet."""

    reference_files = list(validation.get("reference_files", []))
    names = packet_artifacts(
        str(validation["request_id"]),
        str(validation["direction_id"]),
        [str(item["filename"]) for item in reference_files],
        attempt=attempt,
    )
    body_path = validation.get("prompt_path") or "<paste>"
    body = {
        "role": "prompt",
        "source_path": str(body_path),
        "canonical_filename": names["body_filename"],
        "bytes": int(validation["prompt_bytes"]),
        "sha256": str(validation["prompt_sha256"]),
    }
    references = []
    for item, named in zip(reference_files, names["reference_filenames"], strict=True):
        entry = {
            "role": "reference",
            "ordinal": named["ordinal"],
            "source_path": str(item["path"]),
            "source_filename": str(item["filename"]),
            "canonical_filename": named["canonical_filename"],
            "bytes": int(item["bytes"]),
            "sha256": str(item["sha256"]),
        }
        if materialized_dir is not None:
            entry["materialized_path"] = str((materialized_dir / named["canonical_filename"]).resolve())
        references.append(entry)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "packet_id": names["packet_id"],
        "attempt": attempt,
        "canonical_form": names["canonical_form"],
        "request_id": str(validation["request_id"]),
        "direction_id": str(validation["direction_id"]),
        "direction_ids": list(validation.get("direction_ids", [validation["direction_id"]])),
        "workflow_node": str(validation.get("workflow_node", "legacy")),
        "conversation_binding_key": str(
            validation.get("conversation_binding_key", f"legacy:{validation['direction_id']}")
        ),
        "decision_authority": validation.get("decision_authority"),
        "source_mode": str(validation["source_mode"]),
        "body": body,
        "references": references,
        "reference_order_is_authoritative": True,
        "provider_filename_policy": "record_observed_name_only",
        "companion_prompt_is_transport_ui_only": True,
    }
    if materialized_dir is not None:
        manifest["manifest_path"] = str((materialized_dir / names["manifest_filename"]).resolve())
    return manifest


def monitor_identity_key(record: Mapping[str, Any]) -> str:
    """Return the durable monitor identity; tab handles are deliberately excluded."""

    required = ("request_id", "conversation_id", "provider_url")
    missing = [
        key
        for key in required
        if record.get(key) is None or not str(record.get(key, "")).strip()
    ]
    if missing:
        raise ValueError(f"monitor identity missing: {', '.join(missing)}")
    binding_key = str(record.get("conversation_binding_key") or f"legacy:{record.get('direction_id', '')}")
    if binding_key in {"legacy:", "None", ""} or not binding_key.strip():
        raise ValueError("monitor identity missing: conversation_binding_key")
    return "|".join((str(record["request_id"]), binding_key, str(record["conversation_id"]), str(record["provider_url"])))


def validate_transition(current: str, next_state: str) -> None:
    if current == next_state:
        return
    if next_state == "BLOCKED" and current not in TERMINAL_STATES:
        return
    allowed = ALLOWED_TRANSITIONS.get(current)
    if allowed is None or next_state not in allowed:
        raise ValueError(f"invalid transport transition: {current} -> {next_state}")


def transition_record(
    record: MutableMapping[str, Any],
    next_state: str,
    *,
    now: str | None = None,
    **updates: Any,
) -> MutableMapping[str, Any]:
    """Apply one validated state transition and persist its update timestamp in memory."""

    current = str(record.get("state", "RECEIVED"))
    validate_transition(current, next_state)
    record["state"] = next_state
    record["updated_at"] = now or utc_now()
    record.update(updates)
    return record


def receipt_message_key(
    request_id: str,
    direction_id: str,
    conversation_id: str,
    response_sha256: str,
) -> str:
    return "|".join((request_id, direction_id, conversation_id, response_sha256))


def validate_fallback_thread_id(value: str) -> str:
    """Accept only the user-bound fallback session; never infer another target."""

    if value != DEFAULT_FALLBACK_THREAD_ID:
        raise ValueError(
            f"fallback_thread_id must be {DEFAULT_FALLBACK_THREAD_ID}"
        )
    return value


def stage_receipt(
    record: MutableMapping[str, Any],
    archive_paths: Mapping[str, str],
    response_sha256: str,
    *,
    fallback_thread_id: str | None = None,
    fallback_enabled: bool | None = None,
    now: str | None = None,
) -> MutableMapping[str, Any]:
    """Stage one completion receipt after archive verification, without sending it."""

    if str(record.get("state")) != "ARCHIVED":
        raise ValueError("completion receipt may be staged only after ARCHIVED")
    monitor_identity_key(record)
    timestamp = now or utc_now()
    source_thread_id = record.get("source_thread_id")
    enabled = bool(
        record.get("fallback_enabled", False)
        if fallback_enabled is None
        else fallback_enabled
    )
    configured_fallback = (
        fallback_thread_id
        or record.get("fallback_thread_id")
        or DEFAULT_FALLBACK_THREAD_ID
    )
    fallback_id = validate_fallback_thread_id(configured_fallback)
    fallback_used = source_thread_id is None and enabled
    destination_thread_id = fallback_id if fallback_used else source_thread_id
    base_key = receipt_message_key(
        str(record["request_id"]),
        str(record["direction_id"]),
        str(record["conversation_id"]),
        response_sha256,
    )
    message_key = f"{base_key}|fallback|{fallback_id}" if fallback_used else base_key
    existing = dict(record.get("return_receipt") or {})
    existing.update(
        {
            "required": True,
            "primary_destination_thread_id": source_thread_id,
            "destination_thread_id": destination_thread_id,
            "status": "PENDING" if destination_thread_id else "BLOCKED",
            "message_key": message_key,
            "attempt_count": int(existing.get("attempt_count", 0)),
            "retry_allowed": False,
            "delivery_mode": "bounded_single_attempt",
            "return_control_after_attempt": True,
            "archive_paths": dict(archive_paths),
            "response_sha256": response_sha256,
            "staged_at": timestamp,
            "fallback_enabled": enabled,
            "fallback_thread_id": fallback_id if enabled else None,
            "fallback_thread_url": f"codex://threads/{fallback_id}" if enabled else None,
            "fallback_destination_thread_id": fallback_id if enabled else None,
            "fallback_used": fallback_used,
            "fallback_status": "PENDING" if fallback_used else "NOT_NEEDED",
            "fallback_message_key": f"{base_key}|fallback|{fallback_id}" if enabled else None,
            "fallback_delivery_mode": "bounded_single_attempt" if enabled else None,
        }
    )
    if not source_thread_id and not enabled:
        existing["error"] = "source_thread_id is required for automatic return"
    elif fallback_used:
        existing["fallback_staged_at"] = timestamp
    record["return_receipt"] = existing
    return record


def stage_blocker_receipt(
    record: MutableMapping[str, Any],
    blocker_state: str,
    error: str,
    *,
    fallback_thread_id: str | None = None,
    fallback_enabled: bool | None = None,
    now: str | None = None,
) -> MutableMapping[str, Any]:
    """Stage a transport-only terminal blocker receipt without an archive."""

    if blocker_state not in TERMINAL_STATES or blocker_state == "ARCHIVED":
        raise ValueError("blocker_state must be a non-archive terminal transport state")
    if str(record.get("state")) != blocker_state:
        raise ValueError("record state must equal blocker_state")
    monitor_identity_key(record)
    timestamp = now or utc_now()
    source_thread_id = record.get("source_thread_id")
    enabled = bool(
        record.get("fallback_enabled", False)
        if fallback_enabled is None
        else fallback_enabled
    )
    configured_fallback = (
        fallback_thread_id
        or record.get("fallback_thread_id")
        or DEFAULT_FALLBACK_THREAD_ID
    )
    fallback_id = validate_fallback_thread_id(configured_fallback)
    fallback_used = source_thread_id is None and enabled
    destination_thread_id = fallback_id if fallback_used else source_thread_id
    binding = str(record.get("conversation_binding_key") or f"legacy:{record.get('direction_id', '')}")
    error_key = hashlib.sha256(error.encode("utf-8")).hexdigest()[:16]
    base_key = "|".join(
        (
            str(record["request_id"]),
            binding,
            str(record["conversation_id"]),
            "BLOCKER",
            blocker_state,
            error_key,
        )
    )
    existing = dict(record.get("return_receipt") or {})
    existing.update(
        {
            "kind": "TERMINAL_BLOCKER",
            "blocker_state": blocker_state,
            "error": error,
            "required": True,
            "primary_destination_thread_id": source_thread_id,
            "destination_thread_id": destination_thread_id,
            "status": "PENDING" if destination_thread_id else "BLOCKED",
            "message_key": f"{base_key}|fallback|{fallback_id}" if fallback_used else base_key,
            "attempt_count": int(existing.get("attempt_count", 0)),
            "retry_allowed": False,
            "delivery_mode": "bounded_single_attempt",
            "return_control_after_attempt": True,
            "staged_at": timestamp,
            "fallback_enabled": enabled,
            "fallback_thread_id": fallback_id if enabled else None,
            "fallback_thread_url": f"codex://threads/{fallback_id}" if enabled else None,
            "fallback_destination_thread_id": fallback_id if enabled else None,
            "fallback_used": fallback_used,
            "fallback_status": "PENDING" if fallback_used else "NOT_NEEDED",
            "fallback_message_key": f"{base_key}|fallback|{fallback_id}" if enabled else None,
            "fallback_delivery_mode": "bounded_single_attempt" if enabled else None,
        }
    )
    if not source_thread_id and not enabled:
        existing["error"] = "source_thread_id is required for automatic return"
    elif fallback_used:
        existing["fallback_staged_at"] = timestamp
    record["return_receipt"] = existing
    return record


def record_receipt_result(
    record: MutableMapping[str, Any],
    status: str,
    *,
    delivery_status: str | None = None,
    error: str | None = None,
    now: str | None = None,
) -> MutableMapping[str, Any]:
    """Persist the single receipt outcome; uncertain delivery is never retryable here."""

    if status not in {"SENT", "UNCERTAIN", "BLOCKED", "FAILED"}:
        raise ValueError("receipt status must be SENT, UNCERTAIN, BLOCKED, or FAILED")
    timestamp = now or utc_now()
    receipt = dict(record.get("return_receipt") or {})
    receipt["status"] = status
    receipt["delivery_status"] = delivery_status
    receipt["updated_at"] = timestamp
    receipt["attempt_count"] = int(receipt.get("attempt_count", 0)) + (1 if status != "BLOCKED" else 0)
    receipt["retry_allowed"] = False
    if status == "SENT":
        receipt["sent_at"] = timestamp
    if error:
        receipt["error"] = error
    if status in {"BLOCKED", "FAILED"}:
        fallback_enabled = bool(receipt.get("fallback_enabled", False))
        fallback_id = receipt.get("fallback_thread_id") or DEFAULT_FALLBACK_THREAD_ID
        primary_id = receipt.get("primary_destination_thread_id")
        if receipt.get("fallback_thread_id") is not None or fallback_enabled:
            validate_fallback_thread_id(fallback_id)
        if fallback_enabled and fallback_id != primary_id and not receipt.get("fallback_used"):
            receipt["fallback_thread_id"] = fallback_id
            receipt["fallback_thread_url"] = f"codex://threads/{fallback_id}"
            receipt["fallback_destination_thread_id"] = fallback_id
            receipt["fallback_status"] = "PENDING"
            receipt["fallback_used"] = True
            receipt["fallback_staged_at"] = timestamp
            receipt["fallback_message_key"] = receipt.get("fallback_message_key") or (
                f"{receipt.get('message_key', '')}|fallback|{fallback_id}"
            )
            receipt["fallback_reason"] = error or "primary completion receipt send failed"
        elif not fallback_enabled:
            receipt["fallback_status"] = "NOT_AUTHORIZED"
            receipt["fallback_used"] = False
    elif status == "UNCERTAIN":
        # An uncertain primary delivery is deliberately not rerouted: it may have
        # been accepted remotely, and a second receipt could duplicate the result.
        receipt.setdefault("fallback_status", "NOT_NEEDED")
    record["return_receipt"] = receipt
    return record


def record_fallback_result(
    record: MutableMapping[str, Any],
    status: str,
    *,
    delivery_status: str | None = None,
    error: str | None = None,
    now: str | None = None,
) -> MutableMapping[str, Any]:
    """Persist the explicitly bound fallback outcome without blocking the primary task."""

    if status not in {"SENT", "UNCERTAIN", "BLOCKED"}:
        raise ValueError("fallback status must be SENT, UNCERTAIN, or BLOCKED")
    receipt = dict(record.get("return_receipt") or {})
    if receipt.get("fallback_status") != "PENDING":
        raise ValueError("fallback receipt is not pending")
    timestamp = now or utc_now()
    receipt["fallback_status"] = status
    receipt["fallback_delivery_status"] = delivery_status
    receipt["fallback_updated_at"] = timestamp
    receipt["fallback_attempt_count"] = int(receipt.get("fallback_attempt_count", 0)) + 1
    receipt["fallback_retry_allowed"] = False
    if status == "SENT":
        receipt["fallback_sent_at"] = timestamp
    if error:
        receipt["fallback_error"] = error
    record["return_receipt"] = receipt
    return record


def observe_monitor(
    record: MutableMapping[str, Any],
    *,
    observed_url: str,
    tab_handle: str | None,
    observed_state: str,
    cursor: str | None = None,
    now: str | None = None,
) -> MutableMapping[str, Any]:
    """Record a page observation only after exact conversation URL verification."""

    expected_url = str(record.get("provider_url", ""))
    if observed_url != expected_url:
        raise ValueError("MONITOR_IDENTITY_MISMATCH: observed URL does not match provider_url")
    timestamp = now or utc_now()
    identity = monitor_identity_key(record)
    monitor = dict(record.get("monitor") or {})
    monitor.update(
        {
            "identity_key": identity,
            "provider_url": expected_url,
            "last_observed_url": observed_url,
            "last_observed_state": observed_state,
            "last_observed_at": timestamp,
        }
    )
    if cursor is not None:
        monitor["cursor"] = cursor
    record["monitor"] = monitor
    lease = dict(record.get("tab_lease") or {})
    lease.update(
        {
            "handle": tab_handle,
            "lifecycle": "OPEN" if tab_handle else lease.get("lifecycle", "HANDOFF"),
            "last_observed_at": timestamp,
            "reusable": True,
        }
    )
    record["tab_lease"] = lease
    record["tab_id"] = tab_handle
    record["tab_lifecycle"] = lease["lifecycle"]
    return record


def close_tab_lease(
    record: MutableMapping[str, Any],
    *,
    reason: str,
    cleanup_authorized: bool = False,
    now: str | None = None,
) -> MutableMapping[str, Any]:
    """Close a tab only at completion, or with an explicit cleanup authorization."""

    state = str(record.get("state", ""))
    origin = str((record.get("tab_lease") or {}).get("origin", "agent"))
    receipt = record.get("return_receipt") or {}
    if state != "ARCHIVED" and not cleanup_authorized:
        raise ValueError("tab may close only after ARCHIVED or explicit cleanup authorization")
    if origin in {"user", "explicit"} and not cleanup_authorized:
        raise ValueError("user-owned or explicitly mentioned tab requires cleanup authorization")
    if state == "ARCHIVED" and not cleanup_authorized and not receipt.get("message_key"):
        raise ValueError("tab close requires a staged completion receipt")
    timestamp = now or utc_now()
    lease = dict(record.get("tab_lease") or {})
    lease.update(
        {
            "handle": None,
            "lifecycle": "CLOSED",
            "closed_at": timestamp,
            "close_reason": reason,
            "reusable": False,
        }
    )
    record["tab_lease"] = lease
    record["tab_id"] = None
    record["tab_lifecycle"] = "CLOSED"
    return record


def materialized_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
