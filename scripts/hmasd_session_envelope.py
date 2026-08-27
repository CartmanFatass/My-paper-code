#!/usr/bin/env python3
"""Create fixed HMASD session-envelope transport around LLM-authored bodies."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping


_DIRECTION = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}")
_MANAGER = re.compile(r"(EM|CM)/([a-z0-9][a-z0-9_-]{1,63})/g[1-9][0-9]*")
_ASSIGNMENT_BODY_FIELDS = {
    "objective",
    "context_refs",
    "owned_paths",
    "constraints",
    "done_when",
}
_RETURN_BODY_FIELDS = {
    "status",
    "summary",
    "changed_paths",
    "artifact_refs",
    "next_objective",
    "failure",
}
_RETURN_STATUSES = {
    "DONE",
    "REQUEST_EM",
    "REQUEST_CM",
    "REQUEST_PORTFOLIO",
    "REQUEST_USER",
    "FAILED",
}


class EnvelopeError(ValueError):
    pass


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnvelopeError(f"{label} is not readable JSON: {exc}") from exc
    if not isinstance(value, Mapping):
        raise EnvelopeError(f"{label} must be a JSON object")
    return dict(value)


def _validate_identity(identity: str, direction_id: str) -> None:
    if not identity:
        raise EnvelopeError("identity must be non-empty")
    manager = _MANAGER.fullmatch(identity)
    if manager is not None and manager.group(2) != direction_id:
        raise EnvelopeError("manager identity direction does not match direction_id")


def _validate_path(path: str, label: str) -> None:
    normalized = path[:-1] if path.endswith("/") else path
    if (
        not normalized
        or "\\" in path
        or Path(path).is_absolute()
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise EnvelopeError(f"{label} must be a repository-relative POSIX path")


def _validate_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise EnvelopeError(f"{label} must be a list of non-empty strings")
    return list(value)


def _validate_assignment_body(value: Mapping[str, Any]) -> dict[str, Any]:
    if set(value) != _ASSIGNMENT_BODY_FIELDS:
        raise EnvelopeError("assignment body fields are invalid")
    objective = value["objective"]
    if not isinstance(objective, str) or not objective:
        raise EnvelopeError("assignment body objective must be non-empty")
    result = {
        "objective": objective,
        "context_refs": _validate_string_list(
            value["context_refs"], "assignment body context_refs"
        ),
        "owned_paths": _validate_string_list(
            value["owned_paths"], "assignment body owned_paths"
        ),
        "constraints": _validate_string_list(
            value["constraints"], "assignment body constraints"
        ),
        "done_when": _validate_string_list(
            value["done_when"], "assignment body done_when"
        ),
    }
    for index, path in enumerate(result["context_refs"]):
        _validate_path(path, f"assignment body context_refs[{index}]")
    for index, path in enumerate(result["owned_paths"]):
        _validate_path(path, f"assignment body owned_paths[{index}]")
    return result


def _validate_endpoint(value: Any, label: str, direction_id: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"identity", "thread_id"}:
        raise EnvelopeError(f"{label} must contain identity and thread_id")
    identity = value["identity"]
    thread_id = value["thread_id"]
    if not isinstance(identity, str) or not isinstance(thread_id, str) or not thread_id:
        raise EnvelopeError(f"{label} identity and thread_id must be non-empty strings")
    _validate_identity(identity, direction_id)
    return {"identity": identity, "thread_id": thread_id}


def _validate_assignment_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    fields = {
        "schema_version",
        "message_id",
        "direction_id",
        "sender",
        "recipient",
        "kind",
        "reply_to",
        "body",
    }
    if set(value) != fields or value.get("schema_version") != 1:
        raise EnvelopeError("assignment envelope fields are invalid")
    direction_id = value.get("direction_id")
    if not isinstance(direction_id, str) or _DIRECTION.fullmatch(direction_id) is None:
        raise EnvelopeError("assignment direction_id is invalid")
    message_id = value.get("message_id")
    try:
        uuid.UUID(str(message_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise EnvelopeError("assignment message_id is invalid") from exc
    if value.get("kind") != "ASSIGNMENT" or value.get("reply_to") is not None:
        raise EnvelopeError("assignment kind or reply_to is invalid")
    body = value.get("body")
    if not isinstance(body, Mapping):
        raise EnvelopeError("assignment body must be an object")
    return {
        "schema_version": 1,
        "message_id": str(message_id),
        "direction_id": direction_id,
        "sender": _validate_endpoint(value["sender"], "assignment sender", direction_id),
        "recipient": _validate_endpoint(
            value["recipient"], "assignment recipient", direction_id
        ),
        "kind": "ASSIGNMENT",
        "reply_to": None,
        "body": _validate_assignment_body(body),
    }


def _validate_return_body(
    value: Mapping[str, Any], *, owned_paths: list[str]
) -> dict[str, Any]:
    if set(value) != _RETURN_BODY_FIELDS:
        raise EnvelopeError("return body fields are invalid")
    status = value["status"]
    summary = value["summary"]
    next_objective = value["next_objective"]
    failure = value["failure"]
    if status not in _RETURN_STATUSES:
        raise EnvelopeError("return body status is invalid")
    if not isinstance(summary, str) or not summary:
        raise EnvelopeError("return body summary must be non-empty")
    if next_objective is not None and (
        not isinstance(next_objective, str) or not next_objective
    ):
        raise EnvelopeError("return body next_objective must be null or non-empty")
    if status.startswith("REQUEST_") and not isinstance(next_objective, str):
        raise EnvelopeError("request return requires next_objective")
    if failure is not None:
        if (
            not isinstance(failure, Mapping)
            or set(failure) != {"scope", "summary"}
            or failure.get("scope")
            not in {"project", "direction", "feature", "effect"}
            or not isinstance(failure.get("summary"), str)
            or not failure.get("summary")
        ):
            raise EnvelopeError("return body failure is invalid")
        normalized_failure: dict[str, str] | None = {
            "scope": str(failure["scope"]),
            "summary": str(failure["summary"]),
        }
    else:
        normalized_failure = None
    if status == "FAILED" and normalized_failure is None:
        raise EnvelopeError("FAILED return requires failure")
    changed_paths = _validate_string_list(
        value["changed_paths"], "return body changed_paths"
    )
    artifact_refs = _validate_string_list(
        value["artifact_refs"], "return body artifact_refs"
    )
    for index, path in enumerate(changed_paths):
        _validate_path(path, f"return body changed_paths[{index}]")
        folded = path.casefold()
        if not any(
            folded.startswith(owned.casefold())
            if owned.endswith("/")
            else folded == owned.casefold()
            for owned in owned_paths
        ):
            raise EnvelopeError(
                f"return body changed_paths[{index}] is outside assignment owned_paths"
            )
    for index, path in enumerate(artifact_refs):
        _validate_path(path, f"return body artifact_refs[{index}]")
    return {
        "status": status,
        "summary": summary,
        "changed_paths": changed_paths,
        "artifact_refs": artifact_refs,
        "next_objective": next_objective,
        "failure": normalized_failure,
    }


def _validate_return_envelope(
    value: Mapping[str, Any], assignment: Mapping[str, Any]
) -> dict[str, Any]:
    fields = {
        "schema_version",
        "message_id",
        "direction_id",
        "sender",
        "recipient",
        "kind",
        "reply_to",
        "body",
    }
    if set(value) != fields or value.get("schema_version") != 1:
        raise EnvelopeError("return envelope fields are invalid")
    if (
        value.get("kind") != "RETURN"
        or value.get("direction_id") != assignment["direction_id"]
        or value.get("reply_to") != assignment["message_id"]
        or value.get("message_id") != f"{assignment['message_id']}:return"
    ):
        raise EnvelopeError("return envelope correlation is invalid")
    direction_id = assignment["direction_id"]
    sender = _validate_endpoint(value["sender"], "return sender", direction_id)
    recipient = _validate_endpoint(
        value["recipient"], "return recipient", direction_id
    )
    if sender != assignment["recipient"] or recipient != assignment["sender"]:
        raise EnvelopeError("return envelope endpoints do not reverse assignment")
    body = value.get("body")
    if not isinstance(body, Mapping):
        raise EnvelopeError("return body must be an object")
    return {
        "schema_version": 1,
        "message_id": str(value["message_id"]),
        "direction_id": direction_id,
        "sender": sender,
        "recipient": recipient,
        "kind": "RETURN",
        "reply_to": assignment["message_id"],
        "body": _validate_return_body(
            body, owned_paths=assignment["body"]["owned_paths"]
        ),
    }


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        try:
            existing = path.read_bytes()
        except OSError as read_exc:
            raise EnvelopeError("existing envelope cannot be observed") from read_exc
        if existing == payload:
            return
        raise EnvelopeError("existing envelope content conflicts") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def create_assignment(args: argparse.Namespace) -> dict[str, str]:
    direction_id = args.direction_id
    if _DIRECTION.fullmatch(direction_id) is None:
        raise EnvelopeError("direction_id is invalid")
    _validate_identity(args.sender_identity, direction_id)
    _validate_identity(args.recipient_identity, direction_id)
    if not args.sender_thread_id or not args.recipient_thread_id:
        raise EnvelopeError("thread IDs must be non-empty")
    body = _validate_assignment_body(_load_object(Path(args.body), "assignment body"))
    message_id = str(uuid.uuid4())
    envelope = {
        "schema_version": 1,
        "message_id": message_id,
        "direction_id": direction_id,
        "sender": {
            "identity": args.sender_identity,
            "thread_id": args.sender_thread_id,
        },
        "recipient": {
            "identity": args.recipient_identity,
            "thread_id": args.recipient_thread_id,
        },
        "kind": "ASSIGNMENT",
        "reply_to": None,
        "body": body,
    }
    relative = Path(".codex") / "runtime" / "session-envelopes" / direction_id
    relative /= f"{message_id}.assignment.json"
    _write_new(Path(args.repo).resolve() / relative, envelope)
    locator = relative.as_posix()
    return {
        "locator": locator,
        "message": f"HMASD_SESSION_ENVELOPE_V1 {locator}",
        "recipient_thread_id": args.recipient_thread_id,
    }


def create_return(args: argparse.Namespace) -> dict[str, str]:
    repo = Path(args.repo).resolve()
    locator_path = Path(args.assignment)
    _validate_path(locator_path.as_posix(), "assignment locator")
    assignment = _validate_assignment_envelope(
        _load_object(repo / locator_path, "assignment envelope")
    )
    body_value = _load_object(Path(args.body), "return body")
    body = _validate_return_body(
        body_value, owned_paths=assignment["body"]["owned_paths"]
    )
    message_id = f"{assignment['message_id']}:return"
    envelope = {
        "schema_version": 1,
        "message_id": message_id,
        "direction_id": assignment["direction_id"],
        "sender": assignment["recipient"],
        "recipient": assignment["sender"],
        "kind": "RETURN",
        "reply_to": assignment["message_id"],
        "body": body,
    }
    relative = locator_path.with_name(
        locator_path.name.removesuffix(".assignment.json") + ".return.json"
    )
    if relative == locator_path:
        raise EnvelopeError("assignment locator must end with .assignment.json")
    _write_new(repo / relative, envelope)
    locator = relative.as_posix()
    return {
        "locator": locator,
        "message": f"HMASD_SESSION_ENVELOPE_V1 {locator}",
        "recipient_thread_id": assignment["sender"]["thread_id"],
    }


def read_envelope(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo).resolve()
    locator_path = Path(args.envelope)
    _validate_path(locator_path.as_posix(), "envelope locator")
    raw = _load_object(repo / locator_path, "session envelope")
    if raw.get("kind") == "ASSIGNMENT":
        envelope = _validate_assignment_envelope(raw)
    elif raw.get("kind") == "RETURN":
        if not locator_path.name.endswith(".return.json"):
            raise EnvelopeError("return locator must end with .return.json")
        assignment_path = locator_path.with_name(
            locator_path.name.removesuffix(".return.json") + ".assignment.json"
        )
        assignment = _validate_assignment_envelope(
            _load_object(repo / assignment_path, "paired assignment envelope")
        )
        envelope = _validate_return_envelope(raw, assignment)
    else:
        raise EnvelopeError("session envelope kind is invalid")
    locator = locator_path.as_posix()
    return {
        "envelope": envelope,
        "locator": locator,
        "message": f"HMASD_SESSION_ENVELOPE_V1 {locator}",
        "recipient_thread_id": envelope["recipient"]["thread_id"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build fixed session envelopes around semantic JSON bodies."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    assignment = commands.add_parser("assignment")
    assignment.add_argument("--repo", required=True)
    assignment.add_argument("--direction-id", required=True)
    assignment.add_argument("--sender-identity", required=True)
    assignment.add_argument("--sender-thread-id", required=True)
    assignment.add_argument("--recipient-identity", required=True)
    assignment.add_argument("--recipient-thread-id", required=True)
    assignment.add_argument("--body", required=True)
    returned = commands.add_parser("return")
    returned.add_argument("--repo", required=True)
    returned.add_argument("--assignment", required=True)
    returned.add_argument("--body", required=True)
    read = commands.add_parser("read")
    read.add_argument("--repo", required=True)
    read.add_argument("--envelope", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "assignment":
            result = create_assignment(args)
        elif args.command == "return":
            result = create_return(args)
        elif args.command == "read":
            result = read_envelope(args)
        else:  # pragma: no cover
            raise EnvelopeError("unknown command")
    except EnvelopeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
