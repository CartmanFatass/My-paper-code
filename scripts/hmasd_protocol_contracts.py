#!/usr/bin/env python3
"""Pure validation for exact HMASD shared-core authority records."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence


FENCE_INFO = "hmasd-shared-core-action-v1"
_SHARED_CORE_FENCE_OPEN_RE = re.compile(rf"^```{re.escape(FENCE_INFO)}[ \t]*$")
_FENCE_OPEN_RE = re.compile(r"^(?: {0,3})(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
_FENCE_CLOSE_RE = re.compile(r"^(?: {0,3})(?P<marker>`{3,}|~{3,})[ \t]*$")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_GIT_SHA_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
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
    "FENCE_INFO",
    "ProtocolContractError",
    "build_shared_core_action_record",
    "parse_shared_core_action_records",
    "render_shared_core_action_record",
    "validate_shared_core_action_record",
]
