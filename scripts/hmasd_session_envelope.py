#!/usr/bin/env python3
"""Build and verify HMASD v3 session-envelope transport artifacts."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts import hmasd_control_release, hmasd_path_policy, hmasd_state
except ImportError:
    import hmasd_control_release, hmasd_path_policy, hmasd_state


EPOCH = 3
DIRECTION = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}")
MANAGER = re.compile(r"(EM|CM)/([a-z0-9][a-z0-9_-]{1,63})/g[1-9][0-9]*")
SHA256 = re.compile(r"[0-9a-f]{64}")
GIT_SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
KINDS = {"ASSIGNMENT", "RETURN", "PORTFOLIO_RETURN", "CONTROL_NOTICE"}
STATUSES = {
    "REQUEST_EM", "REQUEST_CM", "REQUEST_PORTFOLIO", "REQUEST_USER",
    "WAIT_RESOURCE", "FAILED",
}
ASSIGN_FIELDS = {
    "objective", "context_refs", "owned_paths", "effects", "constraints",
    "done_when", "workspace_mode",
}
RETURN_FIELDS = {
    "status", "summary", "changed_paths", "artifact_refs", "next_objective",
    "failure", "wait_resource", "git_closure",
}
FAIL_FIELDS = {
    "scope", "code", "fingerprint", "responsible_role", "retryable", "attempt",
    "max_attempts", "summary",
}
WAIT_FIELDS = {
    "resource_fingerprint", "frozen_command_or_operation", "immutable_refs",
    "retry_condition", "earliest_retry_at", "direction_id", "run_id", "heartbeat",
}
PORT_FIELDS = {
    "registry_revision", "snapshot_digest", "considered", "transitions", "capacity",
    "summary", "decision_ref", "artifact_refs", "failure",
}
NOTICE_FIELDS = {"action", "reason", "target_identity", "scope"}
RELEASE_FIELDS = {
    "control_release_id", "protocol_epoch", "head", "origin_main", "branch",
    "control_paths", "dirty_control_paths", "publishable", "observed_at",
}
ACTIONS = {"PAUSE", "RESUME", "OVERRIDE", "CANCEL", "REANCHOR"}
LINE = re.compile(
    r"HMASD_SESSION_ENVELOPE_V3 "
    r"kind=(?P<kind>ASSIGNMENT|RETURN|PORTFOLIO_RETURN|CONTROL_NOTICE) "
    r"direction=(?P<direction>\S+) from=(?P<sender>\S+) to=(?P<recipient>\S+) "
    r"next=(?P<next>\S+) id=(?P<id>[0-9a-f-]{36}) "
    r"locator=(?P<locator>\S+)"
)


class EnvelopeError(ValueError):
    pass


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnvelopeError(f"{label} is not readable JSON: {exc}") from exc
    if not isinstance(value, Mapping):
        raise EnvelopeError(f"{label} must be a JSON object")
    return dict(value)


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")


def normalized_path(value: Any, label: str, *, prefix: bool = False) -> str:
    if not isinstance(value, str):
        raise EnvelopeError(f"{label} must be a repository-relative POSIX path")
    trailing = value.endswith("/")
    raw = value[:-1] if trailing else value
    try:
        normalized = hmasd_path_policy.normalize_repo_path(raw, label=label)
    except hmasd_path_policy.PathPolicyError as exc:
        raise EnvelopeError(str(exc)) from exc
    if normalized != raw or (trailing and not prefix):
        raise EnvelopeError(f"{label} is not canonical")
    return normalized + ("/" if trailing else "")


def resolved_path(repo: Path, relative: str, label: str, *, require_file: bool = False) -> Path:
    try:
        return hmasd_path_policy.resolve_repo_path(
            repo, relative, label=label, require_file=require_file,
        )
    except hmasd_path_policy.PathPolicyError as exc:
        raise EnvelopeError(str(exc)) from exc


def strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise EnvelopeError(f"{label} must be a list of non-empty strings")
    return list(value)


def refs(value: Any, label: str, repo: Path, *, verify: bool = True) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise EnvelopeError(f"{label} must be a list")
    result: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        item = f"{label}[{index}]"
        if not isinstance(raw, Mapping) or set(raw) != {"path", "sha256"}:
            raise EnvelopeError(f"{item} must contain path and sha256")
        path = normalized_path(raw["path"], f"{item}.path")
        digest = raw["sha256"]
        if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
            raise EnvelopeError(f"{item}.sha256 is invalid")
        if verify:
            try:
                observed = hashlib.sha256(
                    resolved_path(repo, path, f"{item}.path", require_file=True).read_bytes()
                ).hexdigest()
            except OSError as exc:
                raise EnvelopeError(f"{item}.path is not readable") from exc
            if observed != digest:
                raise EnvelopeError(f"{item}.sha256 does not match path bytes")
        result.append({"path": path, "sha256": digest})
    return result


def endpoint(value: Any, direction: str, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"identity", "thread_id"}:
        raise EnvelopeError(f"{label} must contain identity and thread_id")
    identity, thread_id = value["identity"], value["thread_id"]
    if not isinstance(identity, str) or not identity or not isinstance(thread_id, str) or not thread_id:
        raise EnvelopeError(f"{label} is invalid")
    match = MANAGER.fullmatch(identity)
    if match and match.group(2) != direction:
        raise EnvelopeError(f"{label} direction does not match direction_id")
    return {"identity": identity, "thread_id": thread_id}


def role(identity: str) -> str:
    match = MANAGER.fullmatch(identity)
    return match.group(1) if match else identity


def is_participant(identity: str) -> bool:
    return identity in {"Root", "Portfolio"} or MANAGER.fullmatch(identity) is not None


def validate_target(identity: str, direction: str) -> None:
    if not is_participant(identity):
        raise EnvelopeError("CONTROL_NOTICE target_identity is invalid")
    match = MANAGER.fullmatch(identity)
    if match and match.group(2) != direction:
        raise EnvelopeError("CONTROL_NOTICE target_identity direction is invalid")
    if identity == "Portfolio" and direction != "portfolio":
        raise EnvelopeError("Portfolio CONTROL_NOTICE requires direction_id portfolio")


def assignment_route(sender: str, recipient: str, direction: str) -> None:
    if sender == "Root" and recipient == "Workflow-Clerk":
        return
    if sender != "Workflow-Clerk":
        raise EnvelopeError("ASSIGNMENT edge must be Root to Clerk or Clerk to a participant")
    if recipient == "Root":
        return
    if recipient == "Portfolio" and direction == "portfolio":
        return
    match = MANAGER.fullmatch(recipient)
    if not match or match.group(2) != direction:
        raise EnvelopeError("ASSIGNMENT recipient route is invalid")


def release_record(value: Any, *, require_publishable: bool = False) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != RELEASE_FIELDS:
        raise EnvelopeError("control release has an invalid exact shape")
    release_id = value["control_release_id"]
    if not isinstance(release_id, str) or SHA256.fullmatch(release_id) is None:
        raise EnvelopeError("control release control_release_id must be 64 lowercase hex")
    if value["protocol_epoch"] != EPOCH or isinstance(value["protocol_epoch"], bool):
        raise EnvelopeError(f"control release protocol_epoch must be {EPOCH}")
    for key in ("head", "origin_main"):
        item = value[key]
        if item is not None and (not isinstance(item, str) or GIT_SHA.fullmatch(item) is None):
            raise EnvelopeError(f"control release {key} must be a full Git SHA or null")
    branch = value["branch"]
    if branch is not None and (not isinstance(branch, str) or not branch):
        raise EnvelopeError("control release branch must be a non-empty string or null")
    control_paths = strings(value["control_paths"], "control release control_paths")
    dirty_paths = strings(value["dirty_control_paths"], "control release dirty_control_paths")
    for index, path in enumerate(control_paths):
        normalized_path(path, f"control release control_paths[{index}]")
    for index, path in enumerate(dirty_paths):
        normalized_path(path, f"control release dirty_control_paths[{index}]")
    if control_paths != sorted(set(control_paths)) or dirty_paths != sorted(set(dirty_paths)):
        raise EnvelopeError("control release path lists must be sorted and unique")
    if not isinstance(value["publishable"], bool):
        raise EnvelopeError("control release publishable must be boolean")
    expected_publishable = bool(
        branch == "main" and value["head"] and value["head"] == value["origin_main"]
        and not dirty_paths
    )
    if value["publishable"] != expected_publishable:
        raise EnvelopeError("control release publishability facts are inconsistent")
    observed = value["observed_at"]
    if not isinstance(observed, str) or not observed:
        raise EnvelopeError("control release observed_at must be non-empty")
    try:
        parsed = datetime.datetime.fromisoformat(observed.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EnvelopeError("control release observed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EnvelopeError("control release observed_at must include a timezone")
    if require_publishable and not value["publishable"]:
        raise EnvelopeError("control release must be publishable")
    return dict(value)


def assignment_body(value: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    if set(value) != ASSIGN_FIELDS:
        raise EnvelopeError("assignment body fields are invalid")
    if not isinstance(value["objective"], str) or not value["objective"]:
        raise EnvelopeError("assignment objective must be non-empty")
    if value["workspace_mode"] not in {"shared-main", "separate-worktree"}:
        raise EnvelopeError("assignment workspace_mode is invalid")
    owned = [
        normalized_path(item, f"assignment owned_paths[{index}]", prefix=True)
        for index, item in enumerate(strings(value["owned_paths"], "assignment owned_paths"))
    ]
    return {
        "objective": value["objective"],
        "context_refs": refs(
            value["context_refs"], "assignment context_refs", repo, verify=False,
        ),
        "owned_paths": owned,
        "effects": strings(value["effects"], "assignment effects"),
        "constraints": strings(value["constraints"], "assignment constraints"),
        "done_when": strings(value["done_when"], "assignment done_when"),
        "workspace_mode": value["workspace_mode"],
    }


def current_ref(repo: Path, path: str, label: str) -> dict[str, str]:
    canonical = normalized_path(path, label)
    try:
        payload = resolved_path(repo, canonical, label, require_file=True).read_bytes()
    except OSError as exc:
        raise EnvelopeError(f"{label} is not readable") from exc
    return {"path": canonical, "sha256": hashlib.sha256(payload).hexdigest()}


def brief_defaults(direction: str, recipient_identity: str) -> tuple[list[str], list[str]]:
    recipient_role = role(recipient_identity)
    prompt = {
        "Root": ".codex/prompts/hmasd-root.md",
        "Workflow-Clerk": ".codex/prompts/hmasd-workflow-clerk.md",
        "Portfolio": ".codex/prompts/hmasd-portfolio.md",
        "EM": ".codex/prompts/hmasd-em.md",
        "CM": ".codex/prompts/hmasd-cm.md",
    }.get(recipient_role)
    if prompt is None:
        raise EnvelopeError("assignment-from-brief recipient role is invalid")
    context_paths = ["docs/project/WORKFLOW_PROTOCOL.md", prompt]
    if recipient_role in {"EM", "CM"}:
        base = f"docs/research/candidates/{direction}"
        context_paths.extend([
            f"{base}/DIRECTION.md",
            f"{base}/workflow/research/state.json",
            f"{base}/workflow/engineering/state.json",
        ])
    elif recipient_role == "Portfolio":
        context_paths.extend([
            "docs/research/portfolio/PORTFOLIO.md",
            "docs/research/portfolio/workflow/registry.json",
        ])
    constraints = [
        f"Work only inside this bounded {recipient_role}"
        + (" direction slice." if recipient_role in {"EM", "CM"} else " slice."),
    ]
    if recipient_role != "Workflow-Clerk":
        constraints.append(
            "Return to Workflow-Clerk; do not contact another top-level manager."
        )
    return context_paths, constraints


def is_unknown_effect_failure(value: Mapping[str, Any]) -> bool:
    canonical_code = re.sub(r"[^A-Z0-9]+", "_", str(value.get("code", "")).upper())
    return value.get("scope") == "effect" and "UNKNOWN" in canonical_code.split("_")


def failure(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != FAIL_FIELDS:
        raise EnvelopeError("failure fields are invalid")
    if value["scope"] not in {"project", "direction", "feature", "effect"}:
        raise EnvelopeError("failure scope is invalid")
    for key in ("code", "fingerprint", "responsible_role", "summary"):
        if not isinstance(value[key], str) or not value[key]:
            raise EnvelopeError(f"failure {key} must be non-empty")
    if not isinstance(value["retryable"], bool):
        raise EnvelopeError("failure retryable must be boolean")
    if is_unknown_effect_failure(value) and value["retryable"]:
        raise EnvelopeError("UNKNOWN external Effect failure must set retryable=false")
    attempt, maximum = value["attempt"], value["max_attempts"]
    if (
        not isinstance(attempt, int) or isinstance(attempt, bool)
        or not isinstance(maximum, int) or isinstance(maximum, bool)
        or not 1 <= attempt <= maximum <= 3
    ):
        raise EnvelopeError("failure attempts must satisfy 1 <= attempt <= max_attempts <= 3")
    return dict(value)


def git_closure(value: Any, changed_paths: Sequence[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise EnvelopeError("return git_closure must be an object")
    if not changed_paths:
        if dict(value) != {"kind": "NO_CHANGES"}:
            raise EnvelopeError("empty changed_paths requires exact NO_CHANGES git_closure")
        return {"kind": "NO_CHANGES"}
    fields = {"kind", "branch", "commit_sha", "remote", "ref", "push_outcome"}
    if set(value) != fields or value.get("kind") != "PUBLISHED":
        raise EnvelopeError("non-empty changed_paths requires exact PUBLISHED git_closure")
    if not isinstance(value["branch"], str) or not value["branch"]:
        raise EnvelopeError("git_closure branch must be non-empty")
    if not isinstance(value["commit_sha"], str) or GIT_SHA.fullmatch(value["commit_sha"]) is None:
        raise EnvelopeError("git_closure commit_sha must be a full Git SHA")
    for key in ("remote", "ref"):
        if not isinstance(value[key], str) or not value[key]:
            raise EnvelopeError(f"git_closure {key} must be non-empty")
    if value["push_outcome"] != "SUCCEEDED":
        raise EnvelopeError("git_closure push_outcome must be SUCCEEDED")
    return dict(value)


def wait_contract(
    value: Any, repo: Path, direction: str, sender_thread_id: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != WAIT_FIELDS:
        raise EnvelopeError("WAIT_RESOURCE wait_resource fields are invalid")
    fingerprint = value["resource_fingerprint"]
    if not isinstance(fingerprint, str) or SHA256.fullmatch(fingerprint) is None:
        raise EnvelopeError("WAIT_RESOURCE resource_fingerprint must be 64 lowercase hex")
    operation = value["frozen_command_or_operation"]
    if not isinstance(operation, Mapping) or set(operation) != {"kind", "value"}:
        raise EnvelopeError("WAIT_RESOURCE frozen command/operation is invalid")
    if operation["kind"] == "command":
        normalized_operation: dict[str, Any] = {
            "kind": "command", "value": strings(operation["value"], "WAIT_RESOURCE command"),
        }
        if not normalized_operation["value"]:
            raise EnvelopeError("WAIT_RESOURCE command must not be empty")
    elif operation["kind"] == "operation":
        if not isinstance(operation["value"], str) or not operation["value"]:
            raise EnvelopeError("WAIT_RESOURCE operation identity must be non-empty")
        normalized_operation = {"kind": "operation", "value": operation["value"]}
    else:
        raise EnvelopeError("WAIT_RESOURCE frozen command/operation kind is invalid")
    for key in ("retry_condition", "run_id"):
        if not isinstance(value[key], str) or not value[key]:
            raise EnvelopeError(f"WAIT_RESOURCE {key} must be non-empty")
    if value["direction_id"] != direction:
        raise EnvelopeError("WAIT_RESOURCE direction_id does not match envelope")
    earliest = value["earliest_retry_at"]
    if not isinstance(earliest, str):
        raise EnvelopeError("WAIT_RESOURCE earliest_retry_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.datetime.fromisoformat(earliest.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EnvelopeError("WAIT_RESOURCE earliest_retry_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EnvelopeError("WAIT_RESOURCE earliest_retry_at must include a timezone")
    heartbeat = value["heartbeat"]
    if not isinstance(heartbeat, Mapping) or set(heartbeat) != {"binding_id", "target_thread_id"}:
        raise EnvelopeError("WAIT_RESOURCE heartbeat binding is invalid")
    if not isinstance(heartbeat["binding_id"], str) or not heartbeat["binding_id"]:
        raise EnvelopeError("WAIT_RESOURCE heartbeat binding_id must be non-empty")
    if heartbeat["target_thread_id"] != sender_thread_id:
        raise EnvelopeError("WAIT_RESOURCE heartbeat must target the returning manager thread")
    return {
        "resource_fingerprint": fingerprint,
        "frozen_command_or_operation": normalized_operation,
        "immutable_refs": refs(value["immutable_refs"], "WAIT_RESOURCE immutable_refs", repo),
        "retry_condition": value["retry_condition"],
        "earliest_retry_at": earliest,
        "direction_id": direction,
        "run_id": value["run_id"],
        "heartbeat": dict(heartbeat),
    }


def return_body(
    value: Mapping[str, Any], repo: Path, owned: list[str], direction: str,
    sender_thread_id: str,
) -> dict[str, Any]:
    if set(value) != RETURN_FIELDS:
        raise EnvelopeError("return body fields are invalid")
    status, summary, next_objective = value["status"], value["summary"], value["next_objective"]
    if status not in STATUSES:
        raise EnvelopeError("return status is invalid")
    if not isinstance(summary, str) or not summary:
        raise EnvelopeError("return summary must be non-empty")
    if status.startswith("REQUEST_") and (not isinstance(next_objective, str) or not next_objective):
        raise EnvelopeError("request return requires next_objective")
    if next_objective is not None and (not isinstance(next_objective, str) or not next_objective):
        raise EnvelopeError("next_objective must be null or non-empty")
    typed_failure = failure(value["failure"])
    if (status == "FAILED") != (typed_failure is not None):
        raise EnvelopeError("only FAILED return requires typed failure")
    changed = [
        normalized_path(item, f"return changed_paths[{index}]")
        for index, item in enumerate(strings(value["changed_paths"], "return changed_paths"))
    ]
    for index, path in enumerate(changed):
        try:
            owned_path = hmasd_path_policy.path_is_owned(path, owned)
        except hmasd_path_policy.PathPolicyError as exc:
            raise EnvelopeError(str(exc)) from exc
        if not owned_path:
            raise EnvelopeError(f"return changed_paths[{index}] is outside assignment owned_paths")
    if status == "WAIT_RESOURCE":
        if typed_failure is not None:
            raise EnvelopeError("WAIT_RESOURCE failure must be null")
        wait = wait_contract(value["wait_resource"], repo, direction, sender_thread_id)
    else:
        if value["wait_resource"] is not None:
            raise EnvelopeError("only WAIT_RESOURCE may carry wait_resource")
        wait = None
    return {
        "status": status, "summary": summary, "changed_paths": changed,
        "artifact_refs": refs(value["artifact_refs"], "return artifact_refs", repo),
        "next_objective": next_objective, "failure": typed_failure,
        "wait_resource": wait, "git_closure": git_closure(value["git_closure"], changed),
    }


def portfolio_body(value: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    if set(value) != PORT_FIELDS:
        raise EnvelopeError("portfolio return body fields are invalid; decision_ref is required")
    normalized = {
        "registry_revision": value["registry_revision"],
        "snapshot_digest": value["snapshot_digest"], "considered": value["considered"],
        "transitions": value["transitions"],
        "capacity": dict(value["capacity"]) if isinstance(value["capacity"], Mapping) else value["capacity"],
        "summary": value["summary"],
        "decision_ref": dict(value["decision_ref"]) if isinstance(value["decision_ref"], Mapping) else value["decision_ref"],
        "artifact_refs": refs(value["artifact_refs"], "portfolio artifact_refs", repo),
        "failure": failure(value["failure"]),
    }
    try:
        hmasd_state.validate_portfolio_return(repo, normalized)
    except hmasd_state.StateError as exc:
        raise EnvelopeError(f"portfolio return validation failed: {exc}") from exc
    return normalized


def notice_body(value: Mapping[str, Any], direction: str) -> dict[str, Any]:
    if set(value) != NOTICE_FIELDS or value.get("action") not in ACTIONS:
        raise EnvelopeError("control notice body is invalid")
    if (
        not isinstance(value["reason"], str) or not value["reason"]
        or not isinstance(value["target_identity"], str) or not value["target_identity"]
        or not isinstance(value["scope"], Mapping)
    ):
        raise EnvelopeError("control notice body is invalid")
    validate_target(value["target_identity"], direction)
    scope = dict(value["scope"])
    if "direction_id" not in scope or "affected_locator" not in scope:
        raise EnvelopeError("CONTROL_NOTICE scope requires direction_id and affected_locator")
    if scope.get("direction_id") != direction:
        raise EnvelopeError("CONTROL_NOTICE scope.direction_id must match envelope")
    affected = scope.get("affected_locator")
    if affected is not None:
        scope["affected_locator"] = normalized_path(affected, "CONTROL_NOTICE affected_locator")
    action = value["action"]
    if action in {"PAUSE", "CANCEL"} and affected is None:
        raise EnvelopeError(f"{action} requires an affected locator")
    if action == "OVERRIDE":
        replacement = scope.get("replacement")
        if not isinstance(replacement, Mapping) or set(replacement) != {"objective", "effects"}:
            raise EnvelopeError("OVERRIDE requires exact scope.replacement objective/effects")
        if not isinstance(replacement["objective"], str) or not replacement["objective"].strip():
            raise EnvelopeError("OVERRIDE replacement.objective must be non-empty")
        replacement_effects = replacement["effects"]
        if not isinstance(replacement_effects, list) or not all(
            isinstance(item, str) and bool(item.strip()) for item in replacement_effects
        ):
            raise EnvelopeError("OVERRIDE replacement.effects must be a string array")
        scope["replacement"] = {
            "objective": replacement["objective"], "effects": list(replacement_effects),
        }
    if action == "REANCHOR":
        expected = scope.get("expected_control_release_id")
        if not isinstance(expected, str) or SHA256.fullmatch(expected) is None:
            raise EnvelopeError("REANCHOR requires scope.expected_control_release_id")
    return {
        "action": action, "reason": value["reason"],
        "target_identity": value["target_identity"], "scope": scope,
    }


def notice_semantics(value: Mapping[str, Any]) -> dict[str, Any]:
    scope = dict(value["scope"])
    scope.pop("affected_locator", None)
    return {
        "action": value["action"], "reason": value["reason"],
        "target_identity": value["target_identity"], "scope": scope,
    }


def write_new(path: Path, value: Mapping[str, Any]) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        if path.read_bytes() == payload:
            return
        raise EnvelopeError("existing envelope content conflicts") from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())


def make(
    kind: str, direction: str, sender: dict[str, str], recipient: dict[str, str],
    body: dict[str, Any], release: Mapping[str, Any], reply: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": 3, "protocol_epoch": EPOCH, "message_id": str(uuid.uuid4()),
        "direction_id": direction, "sender": sender, "recipient": recipient,
        "kind": kind, "reply_to": reply,
        "control_release": dict(release), "body": body,
    }


def next_role(env: Mapping[str, Any]) -> str:
    if env["kind"] in {"ASSIGNMENT", "PORTFOLIO_RETURN", "CONTROL_NOTICE"}:
        return "NONE"
    status = env["body"]["status"]
    mapping = {
        "REQUEST_EM": "EM", "REQUEST_CM": "CM", "REQUEST_PORTFOLIO": "Portfolio",
        "REQUEST_USER": "Root",
    }
    if status in mapping:
        return mapping[status]
    if status == "WAIT_RESOURCE":
        return role(env["sender"]["identity"])
    responsible = env["body"]["failure"]["responsible_role"]
    return responsible if responsible in {"Root", "Workflow-Clerk", "Portfolio", "EM", "CM"} else "NONE"


def message(env: Mapping[str, Any], locator: str) -> str:
    return (
        f"HMASD_SESSION_ENVELOPE_V3 kind={env['kind']} direction={env['direction_id']} "
        f"from={env['sender']['identity']} to={env['recipient']['identity']} "
        f"next={next_role(env)} id={env['message_id']} "
        f"locator={locator}"
    )


def output(env: Mapping[str, Any], locator: str) -> dict[str, Any]:
    return {
        "locator": locator, "message": message(env, locator),
        "recipient_thread_id": env["recipient"]["thread_id"],
    }


def raw(repo: Path, locator: str) -> tuple[Path, dict[str, Any]]:
    normalized = normalized_path(locator, "envelope locator")
    relative = Path(*normalized.split("/"))
    return relative, load(
        resolved_path(repo, normalized, "envelope locator", require_file=True),
        "session envelope",
    )


def common(value: Mapping[str, Any], kind: str) -> dict[str, Any]:
    fields = {
        "schema_version", "protocol_epoch", "message_id", "direction_id", "sender",
        "recipient", "kind", "reply_to", "control_release", "body",
    }
    if (
        set(value) != fields or value.get("schema_version") != 3
        or value.get("protocol_epoch") != EPOCH or value.get("kind") != kind
    ):
        raise EnvelopeError("envelope header is invalid")
    try:
        uuid.UUID(str(value["message_id"]))
    except (ValueError, TypeError) as exc:
        raise EnvelopeError("message_id is invalid") from exc
    reply = value["reply_to"]
    if reply is not None:
        try:
            uuid.UUID(str(reply))
        except (ValueError, TypeError) as exc:
            raise EnvelopeError("reply_to is invalid") from exc
    direction = value["direction_id"]
    if not isinstance(direction, str) or DIRECTION.fullmatch(direction) is None:
        raise EnvelopeError("direction_id is invalid")
    if not isinstance(value["body"], Mapping):
        raise EnvelopeError("envelope body must be an object")
    result = dict(value)
    result["sender"] = endpoint(value["sender"], direction, "sender")
    result["recipient"] = endpoint(value["recipient"], direction, "recipient")
    result["control_release"] = release_record(value["control_release"])
    result["body"] = dict(value["body"])
    return result


def _validated(repo: Path, locator: str, seen: set[str] | None = None) -> tuple[Path, dict[str, Any]]:
    relative, value = raw(repo, locator)
    normalized_locator = relative.as_posix()
    visited = set() if seen is None else set(seen)
    if normalized_locator in visited:
        raise EnvelopeError("CONTROL_NOTICE affected locator cycle is invalid")
    visited.add(normalized_locator)
    kind = value.get("kind")
    if kind not in KINDS:
        raise EnvelopeError("session envelope kind is invalid")
    env = common(value, str(kind))
    direction = env["direction_id"]
    sender_identity = env["sender"]["identity"]
    recipient_identity = env["recipient"]["identity"]
    if kind == "ASSIGNMENT":
        assignment_route(sender_identity, recipient_identity, direction)
        if env["reply_to"] is not None:
            raise EnvelopeError("assignment reply_to must be null")
        release_record(env["control_release"], require_publishable=True)
        env["body"] = assignment_body(env["body"], repo)
    elif kind in {"RETURN", "PORTFOLIO_RETURN"}:
        suffix = ".return.json" if kind == "RETURN" else ".portfolio-return.json"
        if not normalized_locator.endswith(suffix):
            raise EnvelopeError("return locator suffix is invalid")
        assignment_locator = normalized_locator.removesuffix(suffix) + ".assignment.json"
        _, assignment = _validated(repo, assignment_locator, visited)
        if (
            env["reply_to"] != assignment["message_id"]
            or env["sender"] != assignment["recipient"]
            or env["recipient"] != assignment["sender"]
            or direction != assignment["direction_id"]
        ):
            raise EnvelopeError("return correlation or endpoints are invalid")
        if canonical_bytes(env["control_release"]) != canonical_bytes(assignment["control_release"]):
            raise EnvelopeError("return control release does not byte-semantically match assignment")
        if kind == "RETURN":
            if not is_participant(sender_identity) or sender_identity == "Portfolio" or recipient_identity != "Workflow-Clerk":
                raise EnvelopeError("RETURN edge must be Root/EM/CM to Workflow-Clerk")
            env["body"] = return_body(
                env["body"], repo, assignment["body"]["owned_paths"], direction,
                env["sender"]["thread_id"],
            )
        else:
            if sender_identity != "Portfolio" or recipient_identity != "Workflow-Clerk" or direction != "portfolio":
                raise EnvelopeError("PORTFOLIO_RETURN edge must be Portfolio to Workflow-Clerk")
            env["body"] = portfolio_body(env["body"], repo)
    else:
        env["body"] = notice_body(env["body"], direction)
        target_identity = env["body"]["target_identity"]
        affected_locator = env["body"]["scope"].get("affected_locator")
        affected = None
        if affected_locator is not None:
            _, affected = _validated(repo, affected_locator, visited)
            if affected["direction_id"] != direction:
                raise EnvelopeError("CONTROL_NOTICE affected direction is invalid")
            if env["reply_to"] != affected["message_id"]:
                raise EnvelopeError("CONTROL_NOTICE reply_to does not match affected locator")
        elif env["reply_to"] is not None:
            raise EnvelopeError("CONTROL_NOTICE reply_to requires affected_locator")
        if sender_identity == "Workflow-Clerk":
            if recipient_identity != target_identity:
                raise EnvelopeError("Clerk CONTROL_NOTICE recipient must equal target_identity")
            if affected is None or affected["kind"] != "CONTROL_NOTICE":
                raise EnvelopeError("Clerk CONTROL_NOTICE must reply to an initiating CONTROL_NOTICE")
            if affected["recipient"]["identity"] != "Workflow-Clerk":
                raise EnvelopeError("Clerk CONTROL_NOTICE must reply to a participant-to-Clerk notice")
            if affected["body"]["target_identity"] != target_identity or affected["body"]["action"] != env["body"]["action"]:
                raise EnvelopeError("relayed CONTROL_NOTICE action or target does not match initiation")
            if canonical_bytes(notice_semantics(env["body"])) != canonical_bytes(
                notice_semantics(affected["body"])
            ):
                raise EnvelopeError("CONTROL_NOTICE relay must copy initiating body semantics")
            if canonical_bytes(env["control_release"]) != canonical_bytes(affected["control_release"]):
                raise EnvelopeError("relayed CONTROL_NOTICE must copy initiating control release")
        elif is_participant(sender_identity) and recipient_identity == "Workflow-Clerk":
            if env["body"]["action"] == "RESUME":
                if (
                    affected is None or affected["kind"] != "CONTROL_NOTICE"
                    or affected["body"]["action"] not in {"PAUSE", "CANCEL"}
                    or affected["body"]["target_identity"] != target_identity
                ):
                    raise EnvelopeError(
                        "RESUME must correlate to PAUSE or CANCEL for the same target"
                    )
            elif affected is not None:
                affected_targets = {
                    affected["sender"]["identity"], affected["recipient"]["identity"],
                }
                if affected["kind"] == "CONTROL_NOTICE":
                    affected_targets.add(affected["body"]["target_identity"])
                if target_identity not in affected_targets:
                    raise EnvelopeError(
                        "CONTROL_NOTICE target is not an endpoint of the affected message"
                    )
            release_record(env["control_release"], require_publishable=True)
        else:
            raise EnvelopeError("CONTROL_NOTICE edge must be participant to Clerk or Clerk to target")
        if env["body"]["action"] == "REANCHOR":
            expected = env["body"]["scope"]["expected_control_release_id"]
            if expected != env["control_release"]["control_release_id"]:
                raise EnvelopeError("REANCHOR expected_control_release_id does not match control release")
            if (
                sender_identity != "Workflow-Clerk" and affected is not None
                and affected["control_release"]["control_release_id"] == expected
            ):
                raise EnvelopeError("REANCHOR must carry a new control release")
            release_record(env["control_release"], require_publishable=True)
    return relative, env


def read_assignment(repo: Path, locator: str) -> tuple[Path, dict[str, Any]]:
    relative, env = _validated(repo, locator)
    if env["kind"] != "ASSIGNMENT":
        raise EnvelopeError("assignment locator does not contain ASSIGNMENT")
    return relative, env


def assignment_endpoints(
    args: argparse.Namespace, direction: str,
) -> tuple[dict[str, str], dict[str, str]]:
    sender = endpoint(
        {"identity": args.sender_identity, "thread_id": args.sender_thread_id},
        direction, "sender",
    )
    recipient = endpoint(
        {"identity": args.recipient_identity, "thread_id": args.recipient_thread_id},
        direction, "recipient",
    )
    assignment_route(sender["identity"], recipient["identity"], direction)
    return sender, recipient


def emit_assignment(
    repo: Path,
    direction: str,
    sender: dict[str, str],
    recipient: dict[str, str],
    body: dict[str, Any],
    release: Mapping[str, Any],
) -> dict[str, Any]:
    env = make("ASSIGNMENT", direction, sender, recipient, body, release, None)
    relative = (
        Path(".codex/runtime/session-envelopes")
        / direction
        / f"{env['message_id']}.assignment.json"
    )
    write_new(repo / relative, env)
    return output(env, relative.as_posix())


def create_assignment_from_brief(args: argparse.Namespace) -> dict[str, Any]:
    repo, direction = Path(args.repo).resolve(), args.direction_id
    if DIRECTION.fullmatch(direction) is None:
        raise EnvelopeError("direction_id is invalid")
    sender, recipient = assignment_endpoints(args, direction)
    default_paths, default_constraints = brief_defaults(direction, recipient["identity"])
    recipient_identity = recipient["identity"]
    context_paths: list[str] = []
    seen: set[str] = set()
    for index, path in enumerate([*default_paths, *args.context_path]):
        canonical = normalized_path(path, f"context_path[{index}]")
        if canonical.casefold() not in seen:
            seen.add(canonical.casefold())
            context_paths.append(canonical)
    generated = {
        "objective": args.objective,
        "context_refs": [
            current_ref(repo, path, f"context_path[{index}]")
            for index, path in enumerate(context_paths)
        ],
        "owned_paths": list(args.owned_path),
        "effects": (
            list(args.effect) if recipient_identity == "Workflow-Clerk"
            else ["native_message_send:Workflow-Clerk", *args.effect]
        ),
        "constraints": [*default_constraints, *args.constraint],
        "done_when": ([
            "Before final, complete every ready native send and the bounded final drain."
        ] if recipient_identity == "Workflow-Clerk" else [
            "Before final, send exactly one correlated v3 "
            + ("PORTFOLIO_RETURN" if recipient_identity == "Portfolio" else "RETURN")
            + " to Workflow-Clerk."
        ]) + list(args.done_when),
        "workspace_mode": args.workspace_mode,
    }
    body = assignment_body(generated, repo)
    if sender["identity"] == "Root":
        if recipient_identity != "Workflow-Clerk" or not args.current_control_release:
            raise EnvelopeError(
                "Root assignment-from-brief requires Workflow-Clerk and current control release"
            )
        release_value = hmasd_control_release.inspect_repo(repo)
    elif sender["identity"] == "Workflow-Clerk":
        if not args.control_release_envelope:
            raise EnvelopeError(
                "Workflow-Clerk assignment-from-brief requires an ingress envelope"
            )
        _, source = _validated(repo, args.control_release_envelope)
        if source["recipient"]["identity"] != "Workflow-Clerk":
            raise EnvelopeError("control release source recipient must be Workflow-Clerk")
        release_value = source["control_release"]
    else:
        raise EnvelopeError("assignment-from-brief sender is invalid")
    release = release_record(release_value, require_publishable=True)
    return emit_assignment(repo, direction, sender, recipient, body, release)


def create_return(args: argparse.Namespace, portfolio: bool = False) -> dict[str, Any]:
    repo = Path(args.repo).resolve()
    assignment_path, assignment = read_assignment(repo, args.assignment)
    if portfolio:
        if assignment["recipient"]["identity"] != "Portfolio" or assignment["direction_id"] != "portfolio":
            raise EnvelopeError("portfolio-return requires global Portfolio assignment")
        kind, suffix = "PORTFOLIO_RETURN", ".portfolio-return.json"
        body = portfolio_body(load(Path(args.body), "portfolio return body"), repo)
    else:
        if assignment["recipient"]["identity"] == "Portfolio":
            raise EnvelopeError("global Portfolio assignment requires portfolio-return")
        if (
            assignment["sender"]["identity"] != "Workflow-Clerk"
            or assignment["recipient"]["identity"] == "Portfolio"
            or not is_participant(assignment["recipient"]["identity"])
        ):
            raise EnvelopeError("ordinary RETURN requires a Clerk-to-Root/EM/CM assignment")
        kind, suffix = "RETURN", ".return.json"
        body = return_body(
            load(Path(args.body), "return body"), repo, assignment["body"]["owned_paths"],
            assignment["direction_id"], assignment["recipient"]["thread_id"],
        )
    base = assignment_path.name.removesuffix(".assignment.json")
    if base == assignment_path.name:
        raise EnvelopeError("assignment locator must end with .assignment.json")
    relative = assignment_path.with_name(base + suffix)
    if (repo / relative).exists():
        existing = read_envelope(argparse.Namespace(repo=str(repo), envelope=relative.as_posix()))["envelope"]
        if existing["body"] != body:
            raise EnvelopeError("existing envelope content conflicts")
        return output(existing, relative.as_posix())
    env = make(
        kind, assignment["direction_id"], assignment["recipient"], assignment["sender"],
        body, assignment["control_release"], assignment["message_id"],
    )
    write_new(repo / relative, env)
    _validated(repo, relative.as_posix())
    return output(env, relative.as_posix())


def create_notice(args: argparse.Namespace) -> dict[str, Any]:
    repo, direction = Path(args.repo).resolve(), args.direction_id
    if DIRECTION.fullmatch(direction) is None:
        raise EnvelopeError("direction_id is invalid")
    sender = endpoint({"identity": args.sender_identity, "thread_id": args.sender_thread_id}, direction, "sender")
    recipient = endpoint({"identity": args.recipient_identity, "thread_id": args.recipient_thread_id}, direction, "recipient")
    body = notice_body(load(Path(args.body), "control notice body"), direction)
    release = release_record(load(Path(args.control_release), "control release"))
    affected_locator = body["scope"].get("affected_locator")
    reply = None
    if affected_locator is not None:
        _, affected = _validated(repo, affected_locator)
        reply = affected["message_id"]
    env = make("CONTROL_NOTICE", direction, sender, recipient, body, release, reply)
    relative = Path(".codex/runtime/session-envelopes") / direction / f"{env['message_id']}.control-notice.json"
    write_new(repo / relative, env)
    try:
        _validated(repo, relative.as_posix())
    except EnvelopeError:
        relative.unlink(missing_ok=True)
        raise
    return output(env, relative.as_posix())


def read_envelope(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo).resolve()
    relative, env = _validated(repo, args.envelope)
    locator = relative.as_posix()
    return {"envelope": env, **output(env, locator)}


def read_message(args: argparse.Namespace) -> dict[str, Any]:
    match = LINE.fullmatch(args.message)
    if not match:
        raise EnvelopeError("message must be exactly one HMASD_SESSION_ENVELOPE_V3 locator line")
    result = read_envelope(argparse.Namespace(repo=args.repo, envelope=match.group("locator")))
    if result["message"] != args.message:
        raise EnvelopeError("message metadata does not match envelope")
    return result


def failure_history(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo).resolve()
    locators = list(args.returns)
    if len(set(locator.casefold() for locator in locators)) != len(locators):
        raise EnvelopeError("failure history contains a duplicate RETURN locator")
    failures: list[dict[str, Any]] = []
    message_ids: set[str] = set()
    normalized_locators: list[str] = []
    for locator in locators:
        relative, env = _validated(repo, locator)
        if env["kind"] != "RETURN" or env["body"]["status"] != "FAILED":
            raise EnvelopeError("failure history locators must be FAILED RETURN envelopes")
        if env["message_id"] in message_ids:
            raise EnvelopeError("failure history contains a duplicate RETURN message")
        message_ids.add(env["message_id"])
        failures.append(env["body"]["failure"])
        normalized_locators.append(relative.as_posix())
    first = failures[0]
    immutable_keys = ("scope", "code", "fingerprint", "responsible_role", "retryable", "max_attempts")
    expected = tuple(first[key] for key in immutable_keys)
    if first["fingerprint"] != args.fingerprint:
        raise EnvelopeError("failure history fingerprint does not match requested fingerprint")
    for index, item in enumerate(failures, start=1):
        if tuple(item[key] for key in immutable_keys) != expected:
            raise EnvelopeError("failure history immutable fingerprint facts or max_attempts changed")
        if item["attempt"] != index:
            raise EnvelopeError("failure history must contain attempts 1..N exactly once")
    observed = len(failures)
    maximum = first["max_attempts"]
    retry_eligible = bool(
        first["retryable"] and not is_unknown_effect_failure(first) and observed < maximum
    )
    return {
        "fingerprint": args.fingerprint, "observed_attempts": observed,
        "max_attempts": maximum, "retry_eligible": retry_eligible,
        "exhausted": not retry_eligible, "responsible_role": first["responsible_role"],
        "next_attempt": observed + 1 if retry_eligible else None,
        "return_locators": normalized_locators,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    command = commands.add_parser("control-notice")
    for flag in (
        "repo", "direction-id", "sender-identity", "sender-thread-id",
        "recipient-identity", "recipient-thread-id", "body", "control-release",
    ):
        command.add_argument(f"--{flag}", required=True)
    command = commands.add_parser("assignment-from-brief")
    for flag in (
        "repo", "direction-id", "sender-identity", "sender-thread-id",
        "recipient-identity", "recipient-thread-id", "objective",
    ):
        command.add_argument(f"--{flag}", required=True)
    release_source = command.add_mutually_exclusive_group(required=True)
    release_source.add_argument("--control-release-envelope")
    release_source.add_argument("--current-control-release", action="store_true")
    command.add_argument("--context-path", action="append", default=[])
    command.add_argument("--owned-path", action="append", default=[])
    command.add_argument("--effect", action="append", default=[])
    command.add_argument("--constraint", action="append", default=[])
    command.add_argument("--done-when", action="append", default=[])
    command.add_argument(
        "--workspace-mode", choices=("shared-main", "separate-worktree"),
        default="shared-main",
    )
    for name in ("return", "portfolio-return"):
        command = commands.add_parser(name)
        command.add_argument("--repo", required=True)
        command.add_argument("--assignment", required=True)
        command.add_argument("--body", required=True)
    command = commands.add_parser("read")
    command.add_argument("--repo", required=True); command.add_argument("--envelope", required=True)
    command = commands.add_parser("read-message")
    command.add_argument("--repo", required=True); command.add_argument("--message", required=True)
    command = commands.add_parser("failure-history")
    command.add_argument("--repo", required=True); command.add_argument("--fingerprint", required=True)
    command.add_argument("--return", dest="returns", action="append", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "assignment-from-brief":
            result = create_assignment_from_brief(args)
        elif args.command == "return":
            result = create_return(args)
        elif args.command == "portfolio-return":
            result = create_return(args, True)
        elif args.command == "control-notice":
            result = create_notice(args)
        elif args.command == "read":
            result = read_envelope(args)
        elif args.command == "read-message":
            result = read_message(args)
        else:
            result = failure_history(args)
    except EnvelopeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
