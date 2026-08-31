#!/usr/bin/env python3
"""Bind one direction to one provider conversation without overwriting conflicts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from transport_contract import (  # noqa: E402
    DEFAULT_FALLBACK_THREAD_ID,
    monitor_identity_key,
    packet_artifacts,
    packet_id,
    registry_lock,
    validate_fallback_thread_id,
)


UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _result(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def _load(path: Path) -> dict:
    if not path.exists():
        return {"version": 2, "directions": {}, "bindings": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("directions", {}), dict):
        raise ValueError("registry must be an object with a directions object")
    if not isinstance(value.get("bindings", {}), dict):
        raise ValueError("registry bindings must be an object")
    value.setdefault("version", 2)
    value.setdefault("directions", {})
    value.setdefault("bindings", {})
    return value


def _tab_handle(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text.strip().lower() in {"", "null", "none"}:
        return None
    return text


def _record_defaults(record: dict, args: argparse.Namespace) -> dict:
    """Add v2 control-plane fields without replacing existing transport facts."""

    handle = _tab_handle(args.tab_id) or _tab_handle(record.get("tab_id"))
    logical_packet_id = record.get("packet_id") or getattr(args, "packet_id", None) or packet_id(args.request_id, args.direction_id)
    source_thread_id = record.get("source_thread_id") or getattr(args, "source_thread_id", None)
    fallback_enabled = bool(getattr(args, "fallback_enabled", False))
    fallback_thread_id = getattr(args, "fallback_thread_id", None)
    if fallback_enabled:
        fallback_thread_id = validate_fallback_thread_id(
            fallback_thread_id or DEFAULT_FALLBACK_THREAD_ID
        )
    binding_key = getattr(args, "conversation_binding_key", None)
    workflow_node = getattr(args, "workflow_node", "legacy")
    direction_ids = getattr(args, "direction_ids", [args.direction_id])
    decision_authority = getattr(args, "decision_authority", None)
    record.setdefault("schema_version", 2)
    record.setdefault("conversation_binding_key", binding_key)
    record.setdefault("workflow_node", workflow_node)
    record.setdefault("direction_ids", direction_ids)
    record.setdefault("decision_authority", decision_authority)
    record.setdefault("packet_id", logical_packet_id)
    record.setdefault(
        "packet",
        {
            "packet_id": logical_packet_id,
            "canonical_form": "logical_packet_manifest",
            "manifest_path": getattr(args, "packet_manifest", None),
        },
    )
    record.setdefault("source_thread_id", source_thread_id)
    if not record.get("source_thread_id") and source_thread_id:
        record["source_thread_id"] = source_thread_id
    record.setdefault("tab_id", handle)
    record.setdefault("tab_lifecycle", "OPEN" if handle else "HANDOFF")
    record.setdefault(
        "tab_lease",
        {
            "handle": handle,
            "lifecycle": "OPEN" if handle else "HANDOFF",
            "origin": getattr(args, "tab_origin", "agent"),
            "reusable": True,
            "last_observed_at": None,
            "lease_expires_at": None,
        },
    )
    record.setdefault(
        "monitor",
        {
            "identity_key": monitor_identity_key(record),
            "provider_url": record["provider_url"],
            "last_observed_url": None,
            "last_observed_state": None,
            "last_observed_at": None,
            "cursor": None,
        },
    )
    if not record["monitor"].get("identity_key"):
        record["monitor"]["identity_key"] = monitor_identity_key(record)
    record.setdefault(
        "return_receipt",
        {
            "required": True,
            "destination_thread_id": source_thread_id,
            "status": "PENDING" if source_thread_id else "BLOCKED",
            "attempt_count": 0,
            "message_key": None,
            "retry_allowed": False,
            "fallback_enabled": fallback_enabled,
            "fallback_thread_id": fallback_thread_id if fallback_enabled else None,
            "fallback_destination_thread_id": fallback_thread_id if fallback_enabled else None,
            "fallback_status": "NOT_NEEDED",
            "fallback_used": False,
        },
    )
    record.setdefault("fallback_enabled", fallback_enabled)
    record.setdefault("fallback_thread_id", fallback_thread_id if fallback_enabled else None)
    record.setdefault(
        "fallback_thread_url",
        f"codex://threads/{fallback_thread_id}" if fallback_enabled else None,
    )
    record.setdefault(
        "heartbeat",
        {
            "automation_id": None,
            "status": "PENDING",
            "next_wake_at": None,
            "retired_at": None,
            "retirement_verified": False,
        },
    )
    record.setdefault("updated_at", None)
    return record


def _atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _expected_binding_key(workflow_node: str, direction_id: str, direction_ids: list[str]) -> str:
    if workflow_node == "em_innovator":
        if direction_ids != [direction_id]:
            raise ValueError("em_innovator requires exactly its direction_id")
        return f"em:{direction_id}:innovator"
    if workflow_node == "em_convergence":
        if direction_ids != [direction_id]:
            raise ValueError("em_convergence requires exactly its direction_id")
        return f"em:{direction_id}:convergence"
    if workflow_node == "portfolio_decision":
        if direction_id != "portfolio" or not direction_ids:
            raise ValueError("portfolio_decision requires direction_id=portfolio and a non-empty scope")
        return "portfolio:cross_direction"
    if workflow_node == "legacy":
        if direction_ids != [direction_id]:
            raise ValueError("legacy binding requires exactly one direction")
        return f"legacy:{direction_id}"
    raise ValueError("unknown workflow_node")


def bind(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.direction_id):
        return _result({"bound": False, "state": "DIRECTION_UNVERIFIED", "error": "invalid direction_id"}, 2)
    if not UUID_RE.fullmatch(args.conversation_id):
        return _result({"bound": False, "state": "CONVERSATION_UNVERIFIED", "error": "conversation_id must be UUID"}, 2)
    expected_url = f"https://chatgpt.com/c/{args.conversation_id}"
    if args.provider_url != expected_url:
        return _result({"bound": False, "state": "CONVERSATION_UNVERIFIED", "error": "provider_url does not match conversation_id"}, 2)
    try:
        direction_ids = json.loads(args.direction_ids_json)
        if not isinstance(direction_ids, list) or not direction_ids:
            raise ValueError("direction_ids_json must be a non-empty list")
        if any(not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value) for value in direction_ids):
            raise ValueError("direction_ids_json entries must be direction tokens")
        if len(set(direction_ids)) != len(direction_ids):
            raise ValueError("direction_ids_json must not contain duplicates")
        expected_binding_key = _expected_binding_key(args.workflow_node, args.direction_id, direction_ids)
        if args.conversation_binding_key is None:
            args.conversation_binding_key = expected_binding_key
        if args.conversation_binding_key != expected_binding_key:
            raise ValueError(f"conversation_binding_key must be {expected_binding_key}")
        if args.workflow_node != "legacy" and args.decision_authority != "pro_final":
            raise ValueError("decision_authority must be pro_final")
        args.direction_ids = direction_ids
    except (json.JSONDecodeError, ValueError) as exc:
        return _result({"bound": False, "state": "BINDING_SCOPE_INVALID", "error": str(exc)}, 2)
    if args.source_thread_id is not None and not UUID_RE.fullmatch(args.source_thread_id):
        return _result({"bound": False, "state": "SOURCE_THREAD_UNVERIFIED", "error": "source_thread_id must be UUID"}, 2)
    if args.fallback_thread_id is not None:
        try:
            args.fallback_thread_id = validate_fallback_thread_id(args.fallback_thread_id)
        except ValueError as exc:
            return _result({"bound": False, "state": "FALLBACK_UNVERIFIED", "error": str(exc)}, 2)
    if args.fallback_enabled:
        args.fallback_thread_id = args.fallback_thread_id or DEFAULT_FALLBACK_THREAD_ID
    if args.packet_manifest is not None and not Path(args.packet_manifest).is_absolute():
        return _result({"bound": False, "state": "PACKET_UNVERIFIED", "error": "packet_manifest must be absolute"}, 2)
    try:
        reference_files = json.loads(args.reference_files_json)
    except json.JSONDecodeError as exc:
        return _result({"bound": False, "state": "REFERENCE_METADATA_INVALID", "error": str(exc)}, 2)
    if not isinstance(reference_files, list):
        return _result({"bound": False, "state": "REFERENCE_METADATA_INVALID", "error": "reference_files_json must be a list"}, 2)
    for item in reference_files:
        if not isinstance(item, dict):
            return _result({"bound": False, "state": "REFERENCE_METADATA_INVALID", "error": "each reference metadata entry must be an object"}, 2)

    registry_path = args.registry.resolve()
    with registry_lock(registry_path):
        registry = _load(registry_path)
        bindings = registry["bindings"]
        directions = registry["directions"]
        old = bindings.get(args.conversation_binding_key)
        if old is None and args.conversation_binding_key == f"legacy:{args.direction_id}":
            old = directions.get(args.direction_id)
        for other_key, other_record in bindings.items():
            if (
                other_key != args.conversation_binding_key
                and isinstance(other_record, dict)
                and other_record.get("conversation_id") == args.conversation_id
            ):
                return _result(
                    {
                        "bound": False,
                        "state": "CONVERSATION_REUSE_CONFLICT",
                        "conversation_binding_key": args.conversation_binding_key,
                        "existing_binding_key": other_key,
                        "conversation_id": args.conversation_id,
                    },
                    3,
                )
        if old is not None:
            if old.get("conversation_id") != args.conversation_id:
                return _result(
                    {
                        "bound": False,
                        "state": "BINDING_CONFLICT",
                        "conversation_binding_key": args.conversation_binding_key,
                        "direction_id": args.direction_id,
                        "existing_conversation_id": old.get("conversation_id"),
                        "requested_conversation_id": args.conversation_id,
                    },
                    3,
                )
            if old.get("request_id") != args.request_id:
                if old.get("state") != "ARCHIVED":
                    return _result(
                        {
                            "bound": False,
                            "state": "BINDING_BUSY",
                            "conversation_binding_key": args.conversation_binding_key,
                            "active_request_id": old.get("request_id"),
                            "requested_request_id": args.request_id,
                        },
                        4,
                    )
                history = list(old.get("request_history") or [])
                history.append(
                    {
                        "request_id": old.get("request_id"),
                        "packet_id": old.get("packet_id"),
                        "state": old.get("state"),
                        "archive": old.get("archive"),
                        "return_receipt": old.get("return_receipt"),
                    }
                )
                packet_names = packet_artifacts(
                    args.request_id,
                    args.direction_id,
                    [
                        str(item.get("filename", f"reference-{index}"))
                        for index, item in enumerate(reference_files, start=1)
                    ],
                )
                canonical_refs = []
                for index, item in enumerate(reference_files):
                    enriched = dict(item)
                    enriched.setdefault(
                        "canonical_filename",
                        packet_names["reference_filenames"][index]["canonical_filename"],
                    )
                    canonical_refs.append(enriched)
                tab_handle = _tab_handle(args.tab_id)
                logical_packet_id = args.packet_id or packet_id(args.request_id, args.direction_id)
                old.update(
                    {
                        "direction_ids": direction_ids,
                        "request_id": args.request_id,
                        "request_history": history,
                        "packet_id": logical_packet_id,
                        "packet": {
                            "packet_id": logical_packet_id,
                            "canonical_form": "logical_packet_manifest",
                            "manifest_path": args.packet_manifest,
                        },
                        "source_thread_id": args.source_thread_id,
                        "tab_id": tab_handle,
                        "tab_lifecycle": "OPEN" if tab_handle else "HANDOFF",
                        "tab_lease": {
                            "handle": tab_handle,
                            "lifecycle": "OPEN" if tab_handle else "HANDOFF",
                            "origin": args.tab_origin,
                            "reusable": True,
                            "last_observed_at": None,
                            "lease_expires_at": None,
                        },
                        "visible_model": args.visible_model,
                        "underlying_model": args.underlying_model,
                        "thinking_effort": args.thinking_effort,
                        "source_mode": args.source_mode,
                        "prompt_sha256": args.prompt_sha256,
                        "reference_files": canonical_refs,
                        "state": "DIRECTION_VERIFIED",
                        "send_click_count": 0,
                        "monitor": {
                            "identity_key": None,
                            "provider_url": args.provider_url,
                            "last_observed_url": None,
                            "last_observed_state": None,
                            "last_observed_at": None,
                            "cursor": None,
                        },
                        "return_receipt": {
                            "required": True,
                            "destination_thread_id": args.source_thread_id,
                            "status": "PENDING" if args.source_thread_id else "BLOCKED",
                            "attempt_count": 0,
                            "message_key": None,
                            "retry_allowed": False,
                            "fallback_enabled": args.fallback_enabled,
                            "fallback_thread_id": args.fallback_thread_id if args.fallback_enabled else None,
                            "fallback_status": "NOT_NEEDED",
                            "fallback_used": False,
                        },
                        "heartbeat": {
                            "automation_id": None,
                            "status": "PENDING",
                            "next_wake_at": None,
                            "retired_at": None,
                            "retirement_verified": False,
                        },
                        "archive": None,
                        "response_sha256": None,
                        "updated_at": None,
                    }
                )
                old["monitor"]["identity_key"] = monitor_identity_key(old)
                bindings[args.conversation_binding_key] = old
                directions[args.direction_id] = old
                _atomic_write(registry_path, registry)
                return _result(
                    {"bound": True, "idempotent": False, "new_round": True, "state": "BOUND", "record": old}
                )
            updated = _record_defaults(old, args)
            bindings[args.conversation_binding_key] = updated
            directions[args.direction_id] = updated
            _atomic_write(registry_path, registry)
            return _result({"bound": True, "idempotent": True, "state": "BOUND", "record": updated})

        tab_handle = _tab_handle(args.tab_id)
        logical_packet_id = args.packet_id or packet_id(args.request_id, args.direction_id)
        packet_names = packet_artifacts(
            args.request_id,
            args.direction_id,
            [str(item.get("filename", f"reference-{index}")) for index, item in enumerate(reference_files, start=1)],
        )
        canonical_refs = []
        for index, item in enumerate(reference_files):
            enriched = dict(item)
            enriched.setdefault("canonical_filename", packet_names["reference_filenames"][index]["canonical_filename"])
            canonical_refs.append(enriched)
        record = {
            "schema_version": 2,
            "conversation_binding_key": args.conversation_binding_key,
            "workflow_node": args.workflow_node,
            "direction_id": args.direction_id,
            "direction_ids": direction_ids,
            "decision_authority": args.decision_authority,
            "conversation_id": args.conversation_id,
            "provider_url": args.provider_url,
            "packet_id": logical_packet_id,
            "packet": {
                "packet_id": logical_packet_id,
                "canonical_form": "logical_packet_manifest",
                "manifest_path": args.packet_manifest,
            },
            "tab_id": tab_handle,
            "tab_lifecycle": "OPEN" if tab_handle else "HANDOFF",
            "last_reopened_at": None,
            "tab_lease": {
                "handle": tab_handle,
                "lifecycle": "OPEN" if tab_handle else "HANDOFF",
                "origin": args.tab_origin,
                "reusable": True,
                "last_observed_at": None,
                "lease_expires_at": None,
            },
            "request_id": args.request_id,
            "source_thread_id": args.source_thread_id,
            "fallback_enabled": args.fallback_enabled,
            "fallback_thread_id": args.fallback_thread_id if args.fallback_enabled else None,
            "fallback_thread_url": (
                f"codex://threads/{args.fallback_thread_id}" if args.fallback_enabled else None
            ),
            "visible_model": args.visible_model,
            "underlying_model": args.underlying_model,
            "thinking_effort": args.thinking_effort,
            "source_mode": args.source_mode,
            "prompt_sha256": args.prompt_sha256,
            "reference_files": canonical_refs,
            "state": "DIRECTION_VERIFIED",
            "send_click_count": 1,
            "monitor": {
                "identity_key": None,
                "provider_url": args.provider_url,
                "last_observed_url": None,
                "last_observed_state": None,
                "last_observed_at": None,
                "cursor": None,
            },
            "return_receipt": {
                "required": True,
                "destination_thread_id": args.source_thread_id,
                "status": "PENDING" if args.source_thread_id else "BLOCKED",
                "attempt_count": 0,
                "message_key": None,
                "retry_allowed": False,
                "fallback_enabled": args.fallback_enabled,
                "fallback_thread_id": args.fallback_thread_id if args.fallback_enabled else None,
                "fallback_destination_thread_id": args.fallback_thread_id if args.fallback_enabled else None,
                "fallback_status": "NOT_NEEDED",
                "fallback_used": False,
            },
            "heartbeat": {
                "automation_id": None,
                "status": "PENDING",
                "next_wake_at": None,
                "retired_at": None,
                "retirement_verified": False,
            },
            "updated_at": None,
        }
        record["monitor"]["identity_key"] = monitor_identity_key(record)
        bindings[args.conversation_binding_key] = record
        directions[args.direction_id] = record
        _atomic_write(registry_path, registry)
        return _result({"bound": True, "idempotent": False, "state": "BOUND", "record": record})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--direction-id", required=True)
    parser.add_argument("--direction-ids-json", default=None)
    parser.add_argument(
        "--workflow-node",
        choices=("em_innovator", "em_convergence", "portfolio_decision", "legacy"),
        default="legacy",
    )
    parser.add_argument("--conversation-binding-key", default=None)
    parser.add_argument("--decision-authority", choices=("pro_final", "legacy"), default="legacy")
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--provider-url", required=True)
    parser.add_argument("--tab-id", default=None)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--visible-model", required=True)
    parser.add_argument("--underlying-model", required=True)
    parser.add_argument("--thinking-effort", required=True)
    parser.add_argument("--source-mode", choices=("paste", "upload"), required=True)
    parser.add_argument("--prompt-sha256", required=True)
    parser.add_argument("--reference-files-json", default="[]")
    parser.add_argument("--source-thread-id", default=None)
    parser.add_argument("--fallback-enabled", action="store_true")
    parser.add_argument("--fallback-thread-id", default=None)
    parser.add_argument("--packet-id", default=None)
    parser.add_argument("--packet-manifest", default=None)
    parser.add_argument("--tab-origin", choices=("agent", "user", "explicit"), default="agent")
    args = parser.parse_args()
    if args.direction_ids_json is None:
        args.direction_ids_json = json.dumps([args.direction_id])
    if args.conversation_binding_key is None:
        args.conversation_binding_key = f"legacy:{args.direction_id}"
    try:
        return bind(args)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _result({"bound": False, "state": "REGISTRY_ERROR", "error": str(exc)}, 2)


if __name__ == "__main__":
    raise SystemExit(main())
