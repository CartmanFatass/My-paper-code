#!/usr/bin/env python3
"""Pure HMASD protocol contract validation.

This module observes existing effect documents and validates exact shared-core
authority records.  It does not execute an effect, mutate workflow state, or
model workflow lifecycle.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping, Sequence

if __package__:
    from scripts import hmasd_external_review, hmasd_platform, hmasd_state
else:  # Direct script imports place this module beside its sibling modules.
    import hmasd_external_review
    import hmasd_platform
    import hmasd_state


FENCE_INFO = "hmasd-shared-core-action-v1"
_SHARED_CORE_FENCE_OPEN_RE = re.compile(rf"^```{re.escape(FENCE_INFO)}[ \t]*$")
_FENCE_OPEN_RE = re.compile(r"^(?: {0,3})(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
_FENCE_CLOSE_RE = re.compile(r"^(?: {0,3})(?P<marker>`{3,}|~{3,})[ \t]*$")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_GIT_SHA_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
_DIRECTION_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
_EFFECT_OPERATIONS = {
    "run_manifest": frozenset({"OBSERVE", "EXECUTE", "CANCEL", "PROMOTE"}),
    "worktree": frozenset(
        {
            "OBSERVE",
            "PROVISION",
            "RECORD_CANDIDATE",
            "PREPARE_INTEGRATION",
            "APPLY_INTEGRATION",
            "PUSH",
            "RELEASE",
            "RETAIN",
        }
    ),
    "external_operation": frozenset({"OBSERVE", "SEND", "ARCHIVE"}),
}
_SHARED_CORE_KEYS = frozenset(
    {
        "schema_version",
        "kind",
        "decision_owner",
        "base_sha",
        "paths",
        "objective",
        "non_goals",
        "allowed_effects",
        "action_digest",
    }
)


class ProtocolContractError(ValueError):
    """One exact protocol contract was not satisfied."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class EffectObservation:
    """Closed observation returned for one exact Effect reference."""

    kind: Literal["legacy", "run_manifest", "worktree", "external_operation"]
    resource_id: str
    state: Literal[
        "LEGACY_UNTYPED", "IN_PROGRESS", "SUCCEEDED", "FAILED", "UNKNOWN", "COMMITTED"
    ]
    path: str
    operation: str = "OBSERVE"


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _validate_relative_path(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProtocolContractError("INVALID_PATH", f"{field} must be a non-empty repository-relative path")
    if "\\" in value or ":" in value or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value):
        raise ProtocolContractError("INVALID_PATH", f"{field} contains a forbidden path spelling")
    raw_parts = value.split("/")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or any(part in {"", ".", ".."} for part in raw_parts)
        or pure.as_posix() != value
    ):
        raise ProtocolContractError("INVALID_PATH", f"{field} must be canonical repository-relative POSIX syntax")
    if any(part.endswith((".", " ")) for part in pure.parts):
        raise ProtocolContractError("INVALID_PATH", f"{field} contains a Windows-ambiguous component")
    return value


def _read_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    root = repo_root.resolve()
    candidate = root.joinpath(*PurePosixPath(relative_path).parts)
    current = root
    for part in PurePosixPath(relative_path).parts:
        current /= part
        try:
            info = current.lstat()
        except (FileNotFoundError, OSError) as exc:
            raise ProtocolContractError(
                "EFFECT_DOCUMENT_UNAVAILABLE",
                f"cannot read in-repository effect document {relative_path!r}",
            ) from exc
        if hmasd_platform.is_reparse_or_symlink(current, info):
            raise ProtocolContractError(
                "EFFECT_PATH_ALIAS",
                f"effect document path {relative_path!r} contains a symlink or reparse point",
            )
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise ProtocolContractError(
            "EFFECT_DOCUMENT_UNAVAILABLE", f"cannot read in-repository effect document {relative_path!r}"
        ) from exc
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolContractError(
            "INVALID_EFFECT_DOCUMENT", f"effect document {relative_path!r} is not valid UTF-8 JSON"
        ) from exc
    if not isinstance(value, dict):
        raise ProtocolContractError("INVALID_EFFECT_DOCUMENT", "effect document must be a JSON object")
    return value


def _require_typed_effect_ref(effect_ref: Mapping[str, Any]) -> tuple[str, str, str, str]:
    if set(effect_ref) == {"path"}:
        path = _validate_relative_path(effect_ref["path"], field="effect_ref.path")
        return "legacy", path, "", "OBSERVE"
    required = {"kind", "path", "resource_id"}
    allowed = required | {"operation"}
    if not required.issubset(effect_ref) or not set(effect_ref).issubset(allowed):
        raise ProtocolContractError(
            "INVALID_EFFECT_REF",
            "typed Effect ref must contain kind, path, and resource_id with optional operation",
        )
    kind = effect_ref["kind"]
    resource_id = effect_ref["resource_id"]
    if kind not in {"run_manifest", "worktree", "external_operation"}:
        raise ProtocolContractError("UNKNOWN_EFFECT_KIND", f"unsupported Effect kind {kind!r}")
    if not isinstance(resource_id, str) or not resource_id:
        raise ProtocolContractError("INVALID_EFFECT_REF", "resource_id must be a non-empty string")
    operation = effect_ref.get("operation", "OBSERVE")
    if operation not in _EFFECT_OPERATIONS[kind]:
        raise ProtocolContractError(
            "INVALID_EFFECT_OPERATION", f"operation {operation!r} is not valid for Effect kind {kind!r}"
        )
    if kind in {"run_manifest", "worktree"}:
        parts = resource_id.split("/")
        tail_pattern = _RUN_ID_RE if kind == "run_manifest" else _ID_RE
        if (
            len(parts) != 2
            or _DIRECTION_RE.fullmatch(parts[0]) is None
            or tail_pattern.fullmatch(parts[1]) is None
        ):
            raise ProtocolContractError(
                "INVALID_EFFECT_REF", f"{kind} resource_id has invalid direction/resource syntax"
            )
    path = _validate_relative_path(effect_ref["path"], field="effect_ref.path")
    return kind, path, resource_id, operation


def _observe_run_manifest(
    path: str, resource_id: str, operation: str, document: dict[str, Any]
) -> EffectObservation:
    try:
        hmasd_state.validate_document("run_manifest", document)
    except Exception as exc:
        raise ProtocolContractError("INVALID_EFFECT_DOCUMENT", str(exc)) from exc
    expected = f"{document['direction_id']}/{document['run_id']}"
    if resource_id != expected:
        raise ProtocolContractError(
            "EFFECT_IDENTITY_MISMATCH", f"run manifest identity is {expected!r}, not {resource_id!r}"
        )
    states = {
        "PREPARED": "IN_PROGRESS",
        "RUNNING": "IN_PROGRESS",
        "SUCCEEDED": "SUCCEEDED",
        "FAILED": "FAILED",
        "CANCELLED": "FAILED",
        "UNKNOWN": "UNKNOWN",
    }
    return EffectObservation("run_manifest", resource_id, states[document["status"]], path, operation)


def _observe_worktree(
    path: str, resource_id: str, operation: str, document: dict[str, Any]
) -> EffectObservation:
    try:
        hmasd_state.validate_document("runtime_worktrees", document)
    except Exception as exc:
        raise ProtocolContractError("INVALID_EFFECT_DOCUMENT", str(exc)) from exc
    matches = [
        row
        for row in document["worktrees"]
        if f"{row['direction_id']}/{row['assignment_id']}" == resource_id
    ]
    if not matches:
        raise ProtocolContractError(
            "EFFECT_IDENTITY_MISMATCH", f"worktree registry has no resource {resource_id!r}"
        )
    if len(matches) != 1:
        raise ProtocolContractError(
            "EFFECT_IDENTITY_NOT_UNIQUE", f"worktree registry has {len(matches)} rows for {resource_id!r}"
        )
    row = matches[0]
    lifecycle = row["lifecycle"]
    if row.get("unknown_outcome") is not None or lifecycle.endswith("_OUTCOME_UNKNOWN"):
        state = "UNKNOWN"
    elif lifecycle in {"INTEGRATED", "RELEASED"}:
        state = "SUCCEEDED"
    elif lifecycle == "RETAINED_FOR_RECOVERY":
        state = "FAILED"
    else:
        state = "IN_PROGRESS"
    return EffectObservation("worktree", resource_id, state, path, operation)


def _observe_external_operation(
    path: str, resource_id: str, operation: str, document: dict[str, Any]
) -> EffectObservation:
    commitment = document.get("commitment_state")
    if commitment not in {"UNKNOWN", "COMMITTED"}:
        raise ProtocolContractError(
            "INVALID_EFFECT_DOCUMENT", "external operation commitment_state must be UNKNOWN or COMMITTED"
        )
    validation_copy = dict(document)
    validation_copy["commitment_state"] = "COMMITTED"
    try:
        validated = hmasd_external_review.validate_operation_ref(validation_copy)
    except Exception as exc:
        raise ProtocolContractError("INVALID_EFFECT_DOCUMENT", str(exc)) from exc
    if resource_id != validated["operation_id"]:
        raise ProtocolContractError(
            "EFFECT_IDENTITY_MISMATCH",
            f"external operation identity is {validated['operation_id']!r}, not {resource_id!r}",
        )
    return EffectObservation("external_operation", resource_id, commitment, path, operation)


def observe_effect_ref(repo_root: Path | str, effect_ref: Mapping[str, Any]) -> EffectObservation:
    """Validate and observe one exact typed Effect reference without mutation."""

    if not isinstance(effect_ref, Mapping):
        raise ProtocolContractError("INVALID_EFFECT_REF", "Effect ref must be an object")
    kind, path, resource_id, operation = _require_typed_effect_ref(effect_ref)
    if kind == "legacy":
        return EffectObservation("legacy", "", "LEGACY_UNTYPED", path)
    document = _read_json(Path(repo_root), path)
    if kind == "run_manifest":
        return _observe_run_manifest(path, resource_id, operation, document)
    if kind == "worktree":
        return _observe_worktree(path, resource_id, operation, document)
    return _observe_external_operation(path, resource_id, operation, document)


def _sorted_unique_text(values: Sequence[str], *, field: str, require_sorted: bool) -> list[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ProtocolContractError("INVALID_SHARED_CORE_RECORD", f"{field} must be an array")
    result = list(values)
    if any(not isinstance(item, str) or not item.strip() for item in result):
        raise ProtocolContractError("INVALID_SHARED_CORE_RECORD", f"{field} entries must be non-empty strings")
    canonical = sorted(set(result))
    if len(canonical) != len(result):
        raise ProtocolContractError("INVALID_SHARED_CORE_RECORD", f"{field} entries must be unique")
    if require_sorted and result != canonical:
        code = "SHARED_CORE_PATHS_NOT_SORTED" if field == "paths" else "SHARED_CORE_LIST_NOT_SORTED"
        raise ProtocolContractError(code, f"{field} must be sorted")
    return canonical


def _validate_path_scope(paths: Sequence[str], *, require_sorted: bool) -> list[str]:
    result = _sorted_unique_text(paths, field="paths", require_sorted=require_sorted)
    for path in result:
        _validate_relative_path(path, field="paths[]")
    for index, parent in enumerate(result):
        prefix = parent + "/"
        if any(child.startswith(prefix) for child in result[index + 1 :]):
            raise ProtocolContractError("PATH_SCOPE_OVERLAP", f"path {parent!r} contains another exact path")
    return result


def _validated_shared_core_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping) or set(record) != _SHARED_CORE_KEYS:
        raise ProtocolContractError(
            "INVALID_SHARED_CORE_RECORD", "shared-core record has missing or unknown fields"
        )
    value = dict(record)
    if value["schema_version"] != 1 or value["kind"] != "shared_core_action":
        raise ProtocolContractError("INVALID_SHARED_CORE_RECORD", "unsupported shared-core record identity")
    if not isinstance(value["decision_owner"], str) or not value["decision_owner"].strip():
        raise ProtocolContractError("INVALID_SHARED_CORE_RECORD", "decision_owner must be non-empty")
    if not isinstance(value["base_sha"], str) or _GIT_SHA_RE.fullmatch(value["base_sha"]) is None:
        raise ProtocolContractError("INVALID_SHARED_CORE_RECORD", "base_sha must be a Git SHA")
    if not isinstance(value["objective"], str) or not value["objective"].strip():
        raise ProtocolContractError("INVALID_SHARED_CORE_RECORD", "objective must be non-empty")
    value["paths"] = _validate_path_scope(value["paths"], require_sorted=True)
    value["non_goals"] = _sorted_unique_text(value["non_goals"], field="non_goals", require_sorted=True)
    value["allowed_effects"] = _sorted_unique_text(
        value["allowed_effects"], field="allowed_effects", require_sorted=True
    )
    digest = value["action_digest"]
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        raise ProtocolContractError("INVALID_SHARED_CORE_RECORD", "action_digest must be lowercase SHA256")
    unsigned = {key: item for key, item in value.items() if key != "action_digest"}
    expected = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    if digest != expected:
        raise ProtocolContractError("ACTION_DIGEST_MISMATCH", "action_digest does not bind canonical record bytes")
    return value


def build_shared_core_action_record(
    *,
    decision_owner: str,
    base_sha: str,
    paths: Sequence[str],
    objective: str,
    non_goals: Sequence[str],
    allowed_effects: Sequence[str],
) -> dict[str, Any]:
    """Build the one canonical JSON value placed in an exact authority fence."""

    unsigned: dict[str, Any] = {
        "schema_version": 1,
        "kind": "shared_core_action",
        "decision_owner": decision_owner,
        "base_sha": base_sha,
        "paths": _validate_path_scope(paths, require_sorted=False),
        "objective": objective,
        "non_goals": _sorted_unique_text(non_goals, field="non_goals", require_sorted=False),
        "allowed_effects": _sorted_unique_text(
            allowed_effects, field="allowed_effects", require_sorted=False
        ),
    }
    record = dict(unsigned)
    record["action_digest"] = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    return _validated_shared_core_record(record)


def render_shared_core_action_record(record: Mapping[str, Any]) -> str:
    """Render a validated record as the exact supported Markdown fence."""

    validated = _validated_shared_core_record(record)
    body = json.dumps(validated, ensure_ascii=False, sort_keys=True, indent=2)
    return f"```{FENCE_INFO}\n{body}\n```"


def parse_shared_core_action_records(markdown: str) -> list[dict[str, Any]]:
    """Parse exact top-level shared-core fences from Markdown authority text."""

    if not isinstance(markdown, str):
        raise ProtocolContractError("INVALID_SHARED_CORE_MARKDOWN", "authority bytes must decode as text")

    bodies: list[str] = []
    lines = markdown.splitlines()
    in_html_comment = False
    outer_fence: tuple[str, int] | None = None
    index = 0
    while index < len(lines):
        line = lines[index]

        if outer_fence is not None:
            close = _FENCE_CLOSE_RE.fullmatch(line)
            if close is not None:
                marker = close.group("marker")
                if marker[0] == outer_fence[0] and len(marker) >= outer_fence[1]:
                    outer_fence = None
            index += 1
            continue

        if in_html_comment:
            end = line.find("-->")
            if end >= 0:
                in_html_comment = "<!--" in line[end + 3 :]
            index += 1
            continue

        if _SHARED_CORE_FENCE_OPEN_RE.fullmatch(line):
            closing = index + 1
            while closing < len(lines) and not re.fullmatch(r"```[ \t]*", lines[closing]):
                closing += 1
            if closing == len(lines):
                break
            bodies.append("\n".join(lines[index + 1 : closing]))
            index = closing + 1
            continue

        fence = _FENCE_OPEN_RE.fullmatch(line)
        if fence is not None:
            marker = fence.group("marker")
            outer_fence = (marker[0], len(marker))
            index += 1
            continue

        comment_start = line.find("<!--")
        if comment_start >= 0 and line.find("-->", comment_start + 4) < 0:
            in_html_comment = True
        index += 1

    if not bodies:
        raise ProtocolContractError("SHARED_CORE_RECORD_NOT_FOUND", "no exact shared-core action fence exists")
    records: list[dict[str, Any]] = []
    for body in bodies:
        try:
            value = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProtocolContractError("INVALID_SHARED_CORE_JSON", str(exc)) from exc
        records.append(_validated_shared_core_record(value))
    return records


def validate_shared_core_action_record(
    markdown: str,
    *,
    action_digest: str,
    decision_owner: str,
    current_base_sha: str,
    owned_paths: Sequence[str],
    objective: str,
    non_goals: Sequence[str],
    allowed_effects: Sequence[str],
) -> dict[str, Any]:
    """Select one digest and prove exact byte-record-to-packet field equality.

    This proves only that matching structured bytes occur in the referenced
    authority.  It does not prove the real-world identity of their author.
    """

    records = parse_shared_core_action_records(markdown)
    matches = [record for record in records if record["action_digest"] == action_digest]
    if len(matches) != 1:
        raise ProtocolContractError(
            "SHARED_CORE_RECORD_NOT_UNIQUE",
            f"action digest selects {len(matches)} records instead of exactly one",
        )
    record = matches[0]
    actual = {
        "decision_owner": decision_owner,
        "base_sha": current_base_sha,
        "paths": _validate_path_scope(owned_paths, require_sorted=False),
        "objective": objective,
        "non_goals": _sorted_unique_text(non_goals, field="non_goals", require_sorted=False),
        "allowed_effects": _sorted_unique_text(
            allowed_effects, field="allowed_effects", require_sorted=False
        ),
    }
    for field, value in actual.items():
        if record[field] != value:
            raise ProtocolContractError(
                "SHARED_CORE_FIELD_MISMATCH", f"{field} differs from the authority record"
            )
    return record


__all__ = [
    "EffectObservation",
    "FENCE_INFO",
    "ProtocolContractError",
    "build_shared_core_action_record",
    "observe_effect_ref",
    "parse_shared_core_action_records",
    "render_shared_core_action_record",
    "validate_shared_core_action_record",
]
