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


SCHEMA_VERSION = 4
RESET_DECISION_OUTCOMES = frozenset({"DECISION_NOT_FORMED", "BLOCKED"})
THREAD_ID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

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
    "CONTEXT_RESET_PENDING",
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


def validate_source_thread_id(value: object) -> str:
    """Validate the task UUID that authored the handoff."""

    if not isinstance(value, str) or not re.fullmatch(THREAD_ID_RE, value):
        raise ValueError("source_thread_id must be the canonical creator Codex task UUID")
    return value


def validate_parent_thread_id(value: object) -> str:
    """Validate the parent task UUID used as the sole return destination."""

    if not isinstance(value, str) or not re.fullmatch(THREAD_ID_RE, value):
        raise ValueError("parent_thread_id must be the canonical parent Codex task UUID")
    return value


def receipt_has_delivery_evidence(receipt: Mapping[str, Any] | None) -> bool:
    """Return whether any old or current route may already have been attempted.

    Migration is allowed only for a provably unsent outbox entry.  Older records
    can store a blocked primary route beside a successfully delivered fallback,
    so checking the primary ``status`` or ``attempt_count`` alone is unsafe.
    """

    if not isinstance(receipt, Mapping):
        return False
    if receipt.get("status") in {"SENT", "UNCERTAIN", "FAILED"}:
        return True
    if receipt.get("fallback_status") in {"SENT", "UNCERTAIN", "FAILED"}:
        return True
    for field in ("attempt_count", "fallback_attempt_count"):
        value = receipt.get(field, 0)
        if isinstance(value, bool):
            if value:
                return True
        else:
            try:
                if int(value or 0) > 0:
                    return True
            except (TypeError, ValueError):
                return True
    for field in (
        "sent_at",
        "delivery_status",
        "fallback_sent_at",
        "fallback_delivery_status",
    ):
        value = receipt.get(field)
        if value is not None and str(value).strip():
            return True
    return False


def validate_provider_context_reset_evidence(value: object) -> dict[str, object]:
    """Validate the narrow, caller-supplied evidence needed to quarantine a binding."""

    if not isinstance(value, dict):
        raise ValueError("provider_context_reset_evidence must be an object")
    previous_request_id = value.get("previous_request_id")
    if not isinstance(previous_request_id, str) or not previous_request_id.strip():
        raise ValueError("provider_context_reset_evidence.previous_request_id must be non-empty")
    decision_outcome = value.get("decision_outcome")
    if decision_outcome not in RESET_DECISION_OUTCOMES:
        raise ValueError("provider_context_reset_evidence.decision_outcome must be DECISION_NOT_FORMED or BLOCKED")
    paths_read = value.get("repository_paths_read")
    if isinstance(paths_read, bool) or paths_read != 0:
        raise ValueError("provider_context_reset_evidence.repository_paths_read must be exactly 0")
    if value.get("provider_context_contamination_acknowledged") is not True:
        raise ValueError("provider_context_contamination_acknowledged must be true")
    prompt_defect = value.get("acknowledged_prompt_defect")
    if not isinstance(prompt_defect, str) or not prompt_defect.strip():
        raise ValueError("provider_context_reset_evidence.acknowledged_prompt_defect must be non-empty")
    return {
        "previous_request_id": previous_request_id,
        "decision_outcome": decision_outcome,
        "repository_paths_read": 0,
        "provider_context_contamination_acknowledged": True,
        "acknowledged_prompt_defect": prompt_defect,
    }


def archived_provider_context_reset_facts(record: Mapping[str, Any]) -> dict[str, object]:
    """Read the immutable archive facts that, rather than caller prose, admit a reset."""

    archive = record.get("archive")
    if not isinstance(archive, Mapping):
        raise ValueError("archived provider-context reset facts are missing")
    facts = archive.get("provider_context_reset_facts")
    if not isinstance(facts, Mapping):
        raise ValueError("archived provider-context reset facts are missing")
    request_id = facts.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("archived provider-context reset facts have no request_id")
    decision_outcome = facts.get("decision_outcome")
    if not isinstance(decision_outcome, str) or not decision_outcome.strip():
        raise ValueError("archived provider-context reset facts have no decision_outcome")
    paths_read = facts.get("repository_paths_read")
    if isinstance(paths_read, bool) or not isinstance(paths_read, int) or paths_read < 0:
        raise ValueError("archived provider-context reset facts have invalid repository_paths_read")
    contamination = facts.get("provider_context_contamination_acknowledged")
    if not isinstance(contamination, bool):
        raise ValueError("archived provider-context reset facts have invalid contamination acknowledgement")
    prompt_defect = facts.get("acknowledged_prompt_defect")
    if contamination and (not isinstance(prompt_defect, str) or not prompt_defect.strip()):
        raise ValueError("archived provider-context reset facts have no acknowledged_prompt_defect")
    return {
        "request_id": request_id,
        "decision_outcome": decision_outcome,
        "repository_paths_read": paths_read,
        "provider_context_contamination_acknowledged": contamination,
        "acknowledged_prompt_defect": prompt_defect,
    }


def persist_archived_provider_context_reset_facts(
    record: MutableMapping[str, Any],
    *,
    decision_outcome: str,
    repository_paths_read: int,
    provider_context_contamination_acknowledged: bool,
    acknowledged_prompt_defect: str | None,
) -> MutableMapping[str, Any]:
    """Persist the archive observation that may later be compared for a reset."""

    if str(record.get("state")) != "ARCHIVED":
        raise ValueError("provider-context reset facts may be persisted only after ARCHIVED")
    request_id = record.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("archived record has no request_id")
    if not isinstance(decision_outcome, str) or not decision_outcome.strip():
        raise ValueError("decision_outcome must be non-empty")
    if isinstance(repository_paths_read, bool) or not isinstance(repository_paths_read, int) or repository_paths_read < 0:
        raise ValueError("repository_paths_read must be a non-negative integer")
    if not isinstance(provider_context_contamination_acknowledged, bool):
        raise ValueError("provider_context_contamination_acknowledged must be boolean")
    if provider_context_contamination_acknowledged and (
        not isinstance(acknowledged_prompt_defect, str) or not acknowledged_prompt_defect.strip()
    ):
        raise ValueError("acknowledged_prompt_defect is required when contamination is acknowledged")
    archive = dict(record.get("archive") or {})
    archive["provider_context_reset_facts"] = {
        "request_id": request_id,
        "decision_outcome": decision_outcome,
        "repository_paths_read": repository_paths_read,
        "provider_context_contamination_acknowledged": provider_context_contamination_acknowledged,
        "acknowledged_prompt_defect": acknowledged_prompt_defect,
    }
    record["archive"] = archive
    return record


def stage_receipt(
    record: MutableMapping[str, Any],
    archive_paths: Mapping[str, str],
    response_sha256: str,
    *,
    now: str | None = None,
) -> MutableMapping[str, Any]:
    """Stage one completion receipt to the handoff's exact parent task."""

    if str(record.get("state")) != "ARCHIVED":
        raise ValueError("completion receipt may be staged only after ARCHIVED")
    monitor_identity_key(record)
    timestamp = now or utc_now()
    existing = dict(record.get("return_receipt") or {})
    if receipt_has_delivery_evidence(existing):
        return record
    try:
        parent_thread_id = validate_parent_thread_id(record.get("parent_thread_id"))
    except ValueError as exc:
        for key in tuple(existing):
            if key.startswith("fallback_") or key == "primary_destination_thread_id":
                existing.pop(key, None)
        existing.update(
            {
                "required": False,
                "source_thread_id": record.get("source_thread_id"),
                "parent_thread_id": record.get("parent_thread_id"),
                "destination_thread_id": None,
                "status": "BLOCKED",
                "attempt_count": int(existing.get("attempt_count", 0)),
                "message_key": None,
                "retry_allowed": False,
                "routing_mode": "PARENT_SESSION",
                "fallback_enabled": False,
                "receipt_state": "RETURN_RECEIPT_BLOCKED",
                "error": f"RETURN_RECEIPT_BLOCKED: {exc}",
                "blocked_at": timestamp,
            }
        )
        for key in ("fallback_enabled", "fallback_thread_id", "fallback_thread_url"):
            record.pop(key, None)
        record["return_receipt"] = existing
        record["return_receipt_state"] = "RETURN_RECEIPT_BLOCKED"
        record["updated_at"] = timestamp
        return record
    source_thread_id = record.get("source_thread_id")
    if source_thread_id is not None:
        source_thread_id = validate_source_thread_id(source_thread_id)
    creator_thread_id = record.get("creator_thread_id")
    if creator_thread_id is not None and creator_thread_id != source_thread_id:
        raise ValueError("creator_thread_id must equal source_thread_id")
    message_key = receipt_message_key(
        str(record["request_id"]),
        str(record["direction_id"]),
        str(record["conversation_id"]),
        response_sha256,
    )
    if existing.get("message_key") and existing["message_key"] != message_key:
        raise ValueError("completion receipt message key conflicts with the archived response")
    if existing.get("status") == "PENDING" and existing.get("message_key"):
        if (
            existing.get("destination_thread_id") == parent_thread_id
            and existing.get("routing_mode") == "PARENT_SESSION"
            and existing.get("fallback_enabled") is False
        ):
            return record
    elif existing.get("status") == "BLOCKED":
        existing.pop("error", None)
    for key in tuple(existing):
        if key.startswith("fallback_") or key == "primary_destination_thread_id":
            existing.pop(key, None)
    existing.pop("receipt_state", None)
    for key in ("fallback_enabled", "fallback_thread_id", "fallback_thread_url"):
        record.pop(key, None)
    existing.update(
        {
            "required": True,
            "source_thread_id": source_thread_id,
            "parent_thread_id": parent_thread_id,
            "destination_thread_id": parent_thread_id,
            "status": "PENDING",
            "message_key": message_key,
            "attempt_count": int(existing.get("attempt_count", 0)),
            "retry_allowed": False,
            "delivery_mode": "bounded_single_attempt",
            "return_control_after_attempt": True,
            "archive_paths": dict(archive_paths),
            "response_sha256": response_sha256,
            "staged_at": timestamp,
            "routing_mode": "PARENT_SESSION",
            "fallback_enabled": False,
        }
    )
    record["creator_thread_id"] = source_thread_id
    record["parent_thread_id"] = parent_thread_id
    record["return_route"] = "PARENT_SESSION"
    record["return_receipt"] = existing
    return record


def stage_blocker_receipt(
    record: MutableMapping[str, Any],
    blocker_state: str,
    error: str,
    *,
    now: str | None = None,
) -> MutableMapping[str, Any]:
    """Stage one terminal-blocker receipt to the handoff's exact parent task."""

    if blocker_state not in TERMINAL_STATES or blocker_state == "ARCHIVED":
        raise ValueError("blocker_state must be a non-archive terminal transport state")
    if str(record.get("state")) != blocker_state:
        raise ValueError("record state must equal blocker_state")
    monitor_identity_key(record)
    timestamp = now or utc_now()
    existing = dict(record.get("return_receipt") or {})
    if receipt_has_delivery_evidence(existing):
        return record
    try:
        parent_thread_id = validate_parent_thread_id(record.get("parent_thread_id"))
    except ValueError as exc:
        for key in tuple(existing):
            if key.startswith("fallback_") or key == "primary_destination_thread_id":
                existing.pop(key, None)
        existing.update(
            {
                "kind": "TERMINAL_BLOCKER",
                "blocker_state": blocker_state,
                "error": f"RETURN_RECEIPT_BLOCKED: {exc}; transport blocker: {error}",
                "required": False,
                "source_thread_id": record.get("source_thread_id"),
                "parent_thread_id": record.get("parent_thread_id"),
                "destination_thread_id": None,
                "status": "BLOCKED",
                "attempt_count": int(existing.get("attempt_count", 0)),
                "message_key": None,
                "retry_allowed": False,
                "routing_mode": "PARENT_SESSION",
                "fallback_enabled": False,
                "receipt_state": "RETURN_RECEIPT_BLOCKED",
                "blocked_at": timestamp,
            }
        )
        for key in ("fallback_enabled", "fallback_thread_id", "fallback_thread_url"):
            record.pop(key, None)
        record["return_receipt"] = existing
        record["return_receipt_state"] = "RETURN_RECEIPT_BLOCKED"
        record["updated_at"] = timestamp
        return record
    source_thread_id = record.get("source_thread_id")
    if source_thread_id is not None:
        source_thread_id = validate_source_thread_id(source_thread_id)
    creator_thread_id = record.get("creator_thread_id")
    if creator_thread_id is not None and creator_thread_id != source_thread_id:
        raise ValueError("creator_thread_id must equal source_thread_id")
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
    if existing.get("message_key") and existing["message_key"] != base_key:
        raise ValueError("blocker receipt message key conflicts with the terminal state")
    if existing.get("status") == "PENDING" and existing.get("message_key"):
        if (
            existing.get("destination_thread_id") == parent_thread_id
            and existing.get("routing_mode") == "PARENT_SESSION"
            and existing.get("fallback_enabled") is False
        ):
            return record
    for key in tuple(existing):
        if key.startswith("fallback_") or key == "primary_destination_thread_id":
            existing.pop(key, None)
    existing.pop("receipt_state", None)
    for key in ("fallback_enabled", "fallback_thread_id", "fallback_thread_url"):
        record.pop(key, None)
    existing.update(
        {
            "kind": "TERMINAL_BLOCKER",
            "blocker_state": blocker_state,
            "error": error,
            "required": True,
            "source_thread_id": source_thread_id,
            "parent_thread_id": parent_thread_id,
            "destination_thread_id": parent_thread_id,
            "status": "PENDING",
            "message_key": base_key,
            "attempt_count": int(existing.get("attempt_count", 0)),
            "retry_allowed": False,
            "delivery_mode": "bounded_single_attempt",
            "return_control_after_attempt": True,
            "staged_at": timestamp,
            "routing_mode": "PARENT_SESSION",
            "fallback_enabled": False,
        }
    )
    record["creator_thread_id"] = source_thread_id
    record["parent_thread_id"] = parent_thread_id
    record["return_route"] = "PARENT_SESSION"
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
    if receipt.get("status") != "PENDING":
        raise ValueError("receipt result requires one pending, unsent receipt")
    parent_thread_id = validate_parent_thread_id(
        receipt.get("parent_thread_id") or record.get("parent_thread_id")
    )
    if receipt.get("destination_thread_id") != parent_thread_id:
        raise ValueError("receipt result destination must equal parent_thread_id")
    if receipt.get("routing_mode") != "PARENT_SESSION" or receipt.get("fallback_enabled") is not False:
        raise ValueError("receipt result requires the parent-session route")
    receipt["status"] = status
    receipt["delivery_status"] = delivery_status
    receipt["updated_at"] = timestamp
    receipt["attempt_count"] = int(receipt.get("attempt_count", 0)) + 1
    receipt["retry_allowed"] = False
    if status == "SENT":
        receipt["sent_at"] = timestamp
    if error:
        receipt["error"] = error
    receipt["destination_thread_id"] = parent_thread_id
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
        if receipt.get("receipt_state") != "RETURN_RECEIPT_BLOCKED":
            raise ValueError("tab close requires a staged or explicitly blocked completion receipt")
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
