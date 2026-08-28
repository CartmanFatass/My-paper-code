#!/usr/bin/env python3
"""Validate and atomically update the current HMASD EM/CM milestone snapshot."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DIRECTION_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,127}\Z")
STATUSES = {"ACTIVE", "WAITING", "FAILED", "COMPLETE"}
MILESTONES = {
    "research": {"SCOPE_FROZEN", "SYNTHESIS_READY", "REVIEW_RESOLVED", "HANDOFF_READY"},
    "engineering": {"SCOPE_FROZEN", "CANDIDATE_READY", "REVIEW_RESOLVED", "RUN_OR_HANDOFF_READY"},
}
ROLES = {"research": "EM", "engineering": "CM"}
COMMON_FIELDS = {
    "direction", "role", "revision", "updated_at", "milestone", "status",
    "completed_summary", "refs", "blockers", "reentry_condition", "next_action",
}
FIELDS = {
    "research": COMMON_FIELDS | {"claim_ceiling", "next_discriminator", "research_cycle"},
    "engineering": COMMON_FIELDS | {"worktree", "branch", "changed_paths", "verification_summary", "run"},
}
PRO_STATUSES = {"PENDING", "COMPLETE", "WAITING", "WAIVED"}
RUN_STATUSES = {"PREPARED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"}
MILESTONE_ORDER = {
    kind: {milestone: index for index, milestone in enumerate(order)}
    for kind, order in {
        "research": ("SCOPE_FROZEN", "SYNTHESIS_READY", "REVIEW_RESOLVED", "HANDOFF_READY"),
        "engineering": ("SCOPE_FROZEN", "CANDIDATE_READY", "REVIEW_RESOLVED", "RUN_OR_HANDOFF_READY"),
    }.items()
}


class StateError(Exception):
    pass


def _text(value: Any, label: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise StateError(f"{label} must be a {'string' if empty else 'non-empty string'}")
    return value


def _nullable_text(value: Any, label: str) -> None:
    if value is not None:
        _text(value, label)


def _timestamp(value: Any, label: str) -> None:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StateError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise StateError(f"{label} must include a timezone")


def _text_list(value: Any, label: str) -> None:
    if not isinstance(value, list):
        raise StateError(f"{label} must be an array")
    seen: set[str] = set()
    for index, item in enumerate(value):
        text = _text(item, f"{label}[{index}]")
        if text in seen:
            raise StateError(f"{label} must not contain duplicates")
        seen.add(text)


def _validate_pro_review(value: Any, label: str) -> None:
    if not isinstance(value, dict) or set(value) != {"status", "response"}:
        raise StateError(f"{label} must contain only status and response")
    if value["status"] not in PRO_STATUSES:
        raise StateError(f"{label}.status is invalid")
    _nullable_text(value["response"], f"{label}.response")
    if value["status"] == "COMPLETE" and value["response"] is None:
        raise StateError(f"{label}.response is required when COMPLETE")


def _validate_cycle(value: Any) -> None:
    if value is None:
        return
    required = {"label", "opened_at", "reason", "pro_innovator", "pro_convergence"}
    if not isinstance(value, dict) or set(value) != required:
        raise StateError("research_cycle fields are invalid")
    _text(value["label"], "research_cycle.label")
    _timestamp(value["opened_at"], "research_cycle.opened_at")
    _text(value["reason"], "research_cycle.reason")
    _validate_pro_review(value["pro_innovator"], "research_cycle.pro_innovator")
    _validate_pro_review(value["pro_convergence"], "research_cycle.pro_convergence")
    innovator = value["pro_innovator"]["status"]
    convergence = value["pro_convergence"]["status"]
    if convergence in {"COMPLETE", "WAIVED", "WAITING"} and innovator not in {"COMPLETE", "WAIVED"}:
        raise StateError("Pro Convergence cannot start before Pro Innovator is resolved")


def _validate_run(value: Any) -> None:
    if value is None:
        return
    required = {"run_id", "status", "manifest", "result"}
    if not isinstance(value, dict) or set(value) != required:
        raise StateError("run fields are invalid")
    _text(value["run_id"], "run.run_id")
    if value["status"] not in RUN_STATUSES:
        raise StateError("run.status is invalid")
    _text(value["manifest"], "run.manifest")
    _nullable_text(value["result"], "run.result")


def validate_document(kind: str, document: Mapping[str, Any]) -> dict[str, Any]:
    if kind not in FIELDS:
        raise StateError(f"unknown kind: {kind}")
    if not isinstance(document, dict) or set(document) != FIELDS[kind]:
        missing = sorted(FIELDS[kind] - set(document)) if isinstance(document, dict) else sorted(FIELDS[kind])
        extra = sorted(set(document) - FIELDS[kind]) if isinstance(document, dict) else []
        raise StateError(f"{kind} state fields are invalid; missing={missing}, extra={extra}")
    direction = _text(document["direction"], "direction")
    if DIRECTION_RE.fullmatch(direction) is None:
        raise StateError("direction is invalid")
    if document["role"] != ROLES[kind]:
        raise StateError(f"role must be {ROLES[kind]}")
    revision = document["revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise StateError("revision must be a positive integer")
    _timestamp(document["updated_at"], "updated_at")
    if document["milestone"] not in MILESTONES[kind]:
        raise StateError("milestone is invalid")
    if document["status"] not in STATUSES:
        raise StateError("status is invalid")
    _text(document["completed_summary"], "completed_summary")
    _text_list(document["refs"], "refs")
    _text_list(document["blockers"], "blockers")
    _nullable_text(document["reentry_condition"], "reentry_condition")
    _text(document["next_action"], "next_action")
    if document["status"] == "WAITING" and document["reentry_condition"] is None:
        raise StateError("WAITING requires reentry_condition")
    if document["status"] in {"ACTIVE", "COMPLETE"} and document["blockers"]:
        raise StateError(f"{document['status']} requires empty blockers")
    if kind == "research":
        _text(document["claim_ceiling"], "claim_ceiling")
        _nullable_text(document["next_discriminator"], "next_discriminator")
        _validate_cycle(document["research_cycle"])
        cycle = document["research_cycle"]
        if cycle is not None:
            innovator = cycle["pro_innovator"]["status"]
            convergence = cycle["pro_convergence"]["status"]
            if document["milestone"] == "SCOPE_FROZEN" and convergence != "PENDING":
                raise StateError("Pro Convergence cannot start before SYNTHESIS_READY")
            if document["milestone"] in {"SYNTHESIS_READY", "REVIEW_RESOLVED", "HANDOFF_READY"} and innovator not in {"COMPLETE", "WAIVED"}:
                raise StateError(f"{document['milestone']} requires resolved Pro Innovator")
            if document["milestone"] in {"REVIEW_RESOLVED", "HANDOFF_READY"} and convergence not in {"COMPLETE", "WAIVED"}:
                raise StateError(f"{document['milestone']} requires resolved Pro Convergence")
    else:
        _nullable_text(document["worktree"], "worktree")
        _nullable_text(document["branch"], "branch")
        _text_list(document["changed_paths"], "changed_paths")
        _text(document["verification_summary"], "verification_summary", empty=True)
        _validate_run(document["run"])
    return dict(document)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StateError(f"cannot read state {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateError("state must be a JSON object")
    return value


def _check_path(path: Path, kind: str, direction: str, root: Path) -> Path:
    root_resolved = root.resolve()
    resolved = (path if path.is_absolute() else root_resolved / path).resolve()
    expected = (
        root_resolved / "docs" / "research" / "candidates" / direction /
        "workflow" / kind / "state.json"
    )
    if resolved != expected:
        raise StateError(f"state path must be {expected}")
    return resolved


def _pro_transition(current: Mapping[str, Any], next_value: Mapping[str, Any], label: str) -> None:
    old = current["status"]
    new = next_value["status"]
    allowed = {
        "PENDING": {"PENDING", "WAITING", "COMPLETE", "WAIVED"},
        "WAITING": {"WAITING", "COMPLETE", "WAIVED"},
        "COMPLETE": {"COMPLETE"},
        "WAIVED": {"WAIVED"},
    }
    if new not in allowed[old]:
        raise StateError(f"{label} cannot regress from {old} to {new}")
    if old in {"COMPLETE", "WAIVED"} and dict(current) != dict(next_value):
        raise StateError(f"resolved {label} cannot change")


def _validate_transition(kind: str, current: Mapping[str, Any], next_document: Mapping[str, Any]) -> None:
    if current["direction"] != next_document["direction"] or current["role"] != next_document["role"]:
        raise StateError("state identity cannot change")
    if kind == "research":
        old_cycle = current["research_cycle"]
        new_cycle = next_document["research_cycle"]
        if old_cycle is not None and new_cycle is None:
            raise StateError("current research_cycle cannot be removed")
        is_new_cycle = old_cycle is None and new_cycle is not None
        if old_cycle is not None and new_cycle is not None:
            is_new_cycle = old_cycle["label"] != new_cycle["label"]
            if not is_new_cycle:
                for field in ("label", "opened_at", "reason"):
                    if old_cycle[field] != new_cycle[field]:
                        raise StateError(f"research_cycle.{field} cannot change within a cycle")
                _pro_transition(old_cycle["pro_innovator"], new_cycle["pro_innovator"], "Pro Innovator")
                _pro_transition(old_cycle["pro_convergence"], new_cycle["pro_convergence"], "Pro Convergence")
        if is_new_cycle:
            if next_document["milestone"] != "SCOPE_FROZEN":
                raise StateError("a new research cycle must start at SCOPE_FROZEN")
            for field in ("pro_innovator", "pro_convergence"):
                if new_cycle[field] != {"status": "PENDING", "response": None}:
                    raise StateError(f"a new research cycle requires pending {field}")
        elif MILESTONE_ORDER[kind][next_document["milestone"]] < MILESTONE_ORDER[kind][current["milestone"]]:
            raise StateError("research milestone cannot regress within a cycle")
    elif MILESTONE_ORDER[kind][next_document["milestone"]] < MILESTONE_ORDER[kind][current["milestone"]]:
        if not (current["status"] == "COMPLETE" and next_document["milestone"] == "SCOPE_FROZEN"):
            raise StateError("engineering milestone cannot regress within a work slice")


def _atomic_write(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def update_state(
    kind: str, path: Path, writer: str, incoming: Mapping[str, Any], *, root: Path = ROOT
) -> dict[str, Any]:
    if writer != ROLES[kind]:
        raise StateError(f"writer must be {ROLES[kind]}")
    next_document = dict(incoming)
    direction = _text(next_document.get("direction"), "direction")
    target = _check_path(path, kind, direction, root)
    if target.exists():
        current = validate_document(kind, _load(target))
        if current["direction"] != next_document.get("direction") or current["role"] != writer:
            raise StateError("existing state identity does not match update")
        revision = int(current["revision"]) + 1
    else:
        revision = 1
    next_document["role"] = writer
    next_document["revision"] = revision
    next_document["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    validated = validate_document(kind, next_document)
    if target.exists():
        _validate_transition(kind, current, validated)
    _atomic_write(target, validated)
    return validated


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--kind", choices=sorted(FIELDS), required=True)
    validate.add_argument("--path", required=True)
    update = commands.add_parser("update")
    update.add_argument("--kind", choices=sorted(FIELDS), required=True)
    update.add_argument("--path", required=True)
    update.add_argument("--writer", choices=sorted(ROLES.values()), required=True)
    update.add_argument("--input", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            raw = _load(Path(args.path))
            result = validate_document(args.kind, raw)
            _check_path(Path(args.path), args.kind, result["direction"], ROOT)
        else:
            result = update_state(
                args.kind, Path(args.path), args.writer, _load(Path(args.input))
            )
    except StateError as exc:
        print(f"hmasd state refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
