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
_PORTFOLIO_RETURN_BODY_FIELDS = {
    "summary",
    "changed_paths",
    "artifact_refs",
    "actions",
    "failure",
}
_PORTFOLIO_ACTION_FIELDS = {
    "direction_id",
    "lifecycle",
    "status",
    "summary",
    "artifact_refs",
    "next_objective",
    "failure",
}
_PORTFOLIO_LIFECYCLE_STATUSES = {
    "ACTIVE": {"REQUEST_EM", "REQUEST_CM", "FAILED"},
    "PARKED": {"REQUEST_USER"},
    "CLOSED": {"DONE"},
}
_TRANSPORT_MESSAGE = re.compile(r"HMASD_SESSION_ENVELOPE_V1 ([^\s]+)")


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


def _validate_assignment_route(
    sender_identity: str, recipient_identity: str, direction_id: str
) -> None:
    if sender_identity == "Root":
        if recipient_identity != "Workflow-Clerk":
            raise EnvelopeError("Root coordination assignments must target Workflow-Clerk")
        return
    if sender_identity != "Workflow-Clerk":
        raise EnvelopeError("only Workflow-Clerk may assign a participant")
    if recipient_identity == "Portfolio":
        if direction_id != "portfolio":
            raise EnvelopeError("Portfolio assignment direction_id must be portfolio")
        return
    if recipient_identity == "Root":
        return
    manager = _MANAGER.fullmatch(recipient_identity)
    if manager is None or manager.group(2) != direction_id:
        raise EnvelopeError(
            "Workflow-Clerk assignment recipient must be Root, Portfolio, or a matching EM/CM"
        )


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
    sender = _validate_endpoint(value["sender"], "assignment sender", direction_id)
    recipient = _validate_endpoint(
        value["recipient"], "assignment recipient", direction_id
    )
    return {
        "schema_version": 1,
        "message_id": str(message_id),
        "direction_id": direction_id,
        "sender": sender,
        "recipient": recipient,
        "kind": "ASSIGNMENT",
        "reply_to": None,
        "body": _validate_assignment_body(body),
    }


def _validate_return_body(
    value: Mapping[str, Any], *, owned_paths: list[str], sender_identity: str
) -> dict[str, Any]:
    if set(value) != _RETURN_BODY_FIELDS:
        raise EnvelopeError("return body fields are invalid")
    status = value["status"]
    summary = value["summary"]
    next_objective = value["next_objective"]
    failure = value["failure"]
    if status not in _RETURN_STATUSES:
        raise EnvelopeError("return body status is invalid")
    if sender_identity == "Portfolio" and status == "REQUEST_PORTFOLIO":
        raise EnvelopeError("Portfolio cannot return REQUEST_PORTFOLIO")
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


def _validate_portfolio_failure(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    if (
        not isinstance(value, Mapping)
        or set(value) != {"scope", "summary"}
        or value.get("scope") not in {"project", "direction", "feature", "effect"}
        or not isinstance(value.get("summary"), str)
        or not value.get("summary")
    ):
        raise EnvelopeError("portfolio return failure is invalid")
    return {"scope": str(value["scope"]), "summary": str(value["summary"])}


def _validate_portfolio_action(value: Any, index: int) -> dict[str, Any]:
    label = f"portfolio return actions[{index}]"
    if not isinstance(value, Mapping) or set(value) != _PORTFOLIO_ACTION_FIELDS:
        raise EnvelopeError(f"{label} fields are invalid")
    direction_id = value["direction_id"]
    lifecycle = value["lifecycle"]
    status = value["status"]
    summary = value["summary"]
    next_objective = value["next_objective"]
    failure = _validate_portfolio_failure(value["failure"])
    if not isinstance(direction_id, str) or _DIRECTION.fullmatch(direction_id) is None:
        raise EnvelopeError(f"{label} direction_id is invalid")
    if lifecycle not in _PORTFOLIO_LIFECYCLE_STATUSES:
        raise EnvelopeError(f"{label} lifecycle is invalid")
    if status not in _PORTFOLIO_LIFECYCLE_STATUSES[lifecycle]:
        raise EnvelopeError(f"{label} lifecycle/status combination is invalid")
    if not isinstance(summary, str) or not summary:
        raise EnvelopeError(f"{label} summary must be non-empty")
    if status.startswith("REQUEST_"):
        if not isinstance(next_objective, str) or not next_objective:
            raise EnvelopeError(f"{label} request requires next_objective")
        if failure is not None:
            raise EnvelopeError(f"{label} request failure must be null")
    elif status == "FAILED":
        if not isinstance(next_objective, str) or not next_objective:
            raise EnvelopeError(f"{label} failure requires next_objective")
        if failure is None:
            raise EnvelopeError(f"{label} FAILED requires scoped failure")
    elif next_objective is not None:
        raise EnvelopeError(f"{label} terminal action requires null next_objective")
    elif failure is not None:
        raise EnvelopeError(f"{label} terminal failure must be null")
    artifact_refs = _validate_string_list(value["artifact_refs"], f"{label} artifact_refs")
    for ref_index, path in enumerate(artifact_refs):
        _validate_path(path, f"{label} artifact_refs[{ref_index}]")
    return {
        "direction_id": direction_id,
        "lifecycle": lifecycle,
        "status": status,
        "summary": summary,
        "artifact_refs": artifact_refs,
        "next_objective": next_objective,
        "failure": failure,
    }


def _validate_portfolio_actions_against_registry(
    repo: Path, actions: list[dict[str, Any]]
) -> None:
    registry = _load_object(
        repo / "docs/research/portfolio/workflow/registry.json",
        "Portfolio registry",
    )
    rows = registry.get("directions")
    if not isinstance(rows, list):
        raise EnvelopeError("Portfolio registry directions must be a list")
    lifecycles: dict[str, str] = {}
    for row in rows:
        if (
            not isinstance(row, Mapping)
            or not isinstance(row.get("id"), str)
            or not isinstance(row.get("lifecycle"), str)
        ):
            raise EnvelopeError("Portfolio registry direction row is invalid")
        key = row["id"].casefold()
        if key in lifecycles:
            raise EnvelopeError("Portfolio registry contains duplicate direction id")
        lifecycles[key] = row["lifecycle"]
    for action in actions:
        current = lifecycles.get(action["direction_id"].casefold())
        if current != action["lifecycle"]:
            raise EnvelopeError(
                f"portfolio action {action['direction_id']} does not match current "
                "Portfolio registry lifecycle"
            )


def _validate_portfolio_return_body(
    value: Mapping[str, Any], *, owned_paths: list[str]
) -> dict[str, Any]:
    if set(value) != _PORTFOLIO_RETURN_BODY_FIELDS:
        raise EnvelopeError("portfolio return body fields are invalid")
    summary = value["summary"]
    if not isinstance(summary, str) or not summary:
        raise EnvelopeError("portfolio return summary must be non-empty")
    changed_paths = _validate_string_list(
        value["changed_paths"], "portfolio return changed_paths"
    )
    artifact_refs = _validate_string_list(
        value["artifact_refs"], "portfolio return artifact_refs"
    )
    for index, path in enumerate(changed_paths):
        _validate_path(path, f"portfolio return changed_paths[{index}]")
        folded = path.casefold()
        if not any(
            folded.startswith(owned.casefold())
            if owned.endswith("/")
            else folded == owned.casefold()
            for owned in owned_paths
        ):
            raise EnvelopeError(
                f"portfolio return changed_paths[{index}] is outside assignment owned_paths"
            )
    for index, path in enumerate(artifact_refs):
        _validate_path(path, f"portfolio return artifact_refs[{index}]")
    actions_value = value["actions"]
    if not isinstance(actions_value, list):
        raise EnvelopeError("portfolio return actions must be a list")
    actions = [
        _validate_portfolio_action(action, index)
        for index, action in enumerate(actions_value)
    ]
    direction_keys = [action["direction_id"].casefold() for action in actions]
    if len(direction_keys) != len(set(direction_keys)):
        raise EnvelopeError("portfolio return actions contain duplicate direction_id")
    failure = _validate_portfolio_failure(value["failure"])
    if failure is not None and actions:
        raise EnvelopeError("failed portfolio return cannot contain direction actions")
    actions.sort(key=lambda action: action["direction_id"].casefold())
    return {
        "summary": summary,
        "changed_paths": changed_paths,
        "artifact_refs": artifact_refs,
        "actions": actions,
        "failure": failure,
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
        assignment["recipient"]["identity"] == "Portfolio"
        and assignment["direction_id"] == "portfolio"
    ):
        raise EnvelopeError("global Portfolio assignment requires portfolio-return")
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
            body,
            owned_paths=assignment["body"]["owned_paths"],
            sender_identity=sender["identity"],
        ),
    }


def _validate_portfolio_return_envelope(
    value: Mapping[str, Any], assignment: Mapping[str, Any], repo: Path
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
        raise EnvelopeError("portfolio return envelope fields are invalid")
    if assignment["recipient"]["identity"] != "Portfolio":
        raise EnvelopeError("portfolio return requires a Portfolio assignment")
    if assignment["direction_id"] != "portfolio":
        raise EnvelopeError("portfolio-return requires direction_id portfolio")
    if (
        value.get("kind") != "PORTFOLIO_RETURN"
        or value.get("direction_id") != assignment["direction_id"]
        or value.get("reply_to") != assignment["message_id"]
        or value.get("message_id")
        != f"{assignment['message_id']}:portfolio-return"
    ):
        raise EnvelopeError("portfolio return correlation is invalid")
    direction_id = assignment["direction_id"]
    sender = _validate_endpoint(value["sender"], "portfolio return sender", direction_id)
    recipient = _validate_endpoint(
        value["recipient"], "portfolio return recipient", direction_id
    )
    if sender != assignment["recipient"] or recipient != assignment["sender"]:
        raise EnvelopeError("portfolio return endpoints do not reverse assignment")
    body = value.get("body")
    if not isinstance(body, Mapping):
        raise EnvelopeError("portfolio return body must be an object")
    normalized_body = _validate_portfolio_return_body(
        body, owned_paths=assignment["body"]["owned_paths"]
    )
    _validate_portfolio_actions_against_registry(repo, normalized_body["actions"])
    return {
        "schema_version": 1,
        "message_id": str(value["message_id"]),
        "direction_id": direction_id,
        "sender": sender,
        "recipient": recipient,
        "kind": "PORTFOLIO_RETURN",
        "reply_to": assignment["message_id"],
        "body": normalized_body,
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
    _validate_assignment_route(
        args.sender_identity, args.recipient_identity, direction_id
    )
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
    if (
        assignment["recipient"]["identity"] == "Portfolio"
        and assignment["direction_id"] == "portfolio"
    ):
        raise EnvelopeError("global Portfolio assignment requires portfolio-return")
    body_value = _load_object(Path(args.body), "return body")
    body = _validate_return_body(
        body_value,
        owned_paths=assignment["body"]["owned_paths"],
        sender_identity=assignment["recipient"]["identity"],
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


def create_portfolio_return(args: argparse.Namespace) -> dict[str, str]:
    repo = Path(args.repo).resolve()
    locator_path = Path(args.assignment)
    _validate_path(locator_path.as_posix(), "assignment locator")
    assignment = _validate_assignment_envelope(
        _load_object(repo / locator_path, "assignment envelope")
    )
    if assignment["recipient"]["identity"] != "Portfolio":
        raise EnvelopeError("portfolio-return requires a Portfolio assignment")
    if assignment["direction_id"] != "portfolio":
        raise EnvelopeError("portfolio-return requires direction_id portfolio")
    body = _validate_portfolio_return_body(
        _load_object(Path(args.body), "portfolio return body"),
        owned_paths=assignment["body"]["owned_paths"],
    )
    _validate_portfolio_actions_against_registry(repo, body["actions"])
    envelope = {
        "schema_version": 1,
        "message_id": f"{assignment['message_id']}:portfolio-return",
        "direction_id": assignment["direction_id"],
        "sender": assignment["recipient"],
        "recipient": assignment["sender"],
        "kind": "PORTFOLIO_RETURN",
        "reply_to": assignment["message_id"],
        "body": body,
    }
    relative = locator_path.with_name(
        locator_path.name.removesuffix(".assignment.json")
        + ".portfolio-return.json"
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
    elif raw.get("kind") == "PORTFOLIO_RETURN":
        if not locator_path.name.endswith(".portfolio-return.json"):
            raise EnvelopeError(
                "portfolio return locator must end with .portfolio-return.json"
            )
        assignment_path = locator_path.with_name(
            locator_path.name.removesuffix(".portfolio-return.json")
            + ".assignment.json"
        )
        assignment = _validate_assignment_envelope(
            _load_object(repo / assignment_path, "paired assignment envelope")
        )
        envelope = _validate_portfolio_return_envelope(raw, assignment, repo)
    else:
        raise EnvelopeError("session envelope kind is invalid")
    locator = locator_path.as_posix()
    return {
        "envelope": envelope,
        "locator": locator,
        "message": f"HMASD_SESSION_ENVELOPE_V1 {locator}",
        "recipient_thread_id": envelope["recipient"]["thread_id"],
    }


def read_message(args: argparse.Namespace) -> dict[str, Any]:
    match = _TRANSPORT_MESSAGE.fullmatch(args.message)
    if match is None:
        raise EnvelopeError(
            "message must be exactly HMASD_SESSION_ENVELOPE_V1 plus one locator"
        )
    return read_envelope(
        argparse.Namespace(repo=args.repo, envelope=match.group(1))
    )


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
    portfolio_return = commands.add_parser("portfolio-return")
    portfolio_return.add_argument("--repo", required=True)
    portfolio_return.add_argument("--assignment", required=True)
    portfolio_return.add_argument("--body", required=True)
    read = commands.add_parser("read")
    read.add_argument("--repo", required=True)
    read.add_argument("--envelope", required=True)
    read_message_parser = commands.add_parser("read-message")
    read_message_parser.add_argument("--repo", required=True)
    read_message_parser.add_argument("--message", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "assignment":
            result = create_assignment(args)
        elif args.command == "return":
            result = create_return(args)
        elif args.command == "portfolio-return":
            result = create_portfolio_return(args)
        elif args.command == "read":
            result = read_envelope(args)
        elif args.command == "read-message":
            result = read_message(args)
        else:  # pragma: no cover
            raise EnvelopeError("unknown command")
    except EnvelopeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
