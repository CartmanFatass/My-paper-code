#!/usr/bin/env python3
"""Read-only local HMASD dashboard.

The dashboard is deliberately a projection, not another workflow authority.  It
reads the small set of authoritative HMASD files, validates their shape, and
returns field-allowlisted data.  It never writes the repository and never
serves a path selected by a request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit


SCHEMA_VERSION = 1
SERVICE_VERSION = "hmasd-dashboard-v1"
BIND_HOST = "127.0.0.1"
MAX_SNAPSHOT_ATTEMPTS = 3
EPOCH = "1970-01-01T00:00:00Z"

REGISTRY_REL = "docs/research/portfolio/workflow/registry.json"
# Codex runtime references are disposable observations.  Keep the old OMP
# locations as a read-only fallback so a historical checkout remains visible
# during cutover, but do not make their absence an error condition.
RUNTIME_AGENTS_REL = ".codex/runtime/agents.json"
RUNTIME_WORKTREES_REL = ".codex/runtime/worktrees.json"
RUNTIME_TASKS_REL = ".codex/runtime/tasks.json"
LEGACY_RUNTIME_AGENTS_REL = ".omp/runtime/agents.json"
LEGACY_RUNTIME_WORKTREES_REL = ".omp/runtime/worktrees.json"
LEGACY_RUNTIME_TASKS_REL = ".omp/runtime/tasks.json"

ASSET_NAMES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}
API_NAMES = {
    "/api/health",
    "/api/snapshot",
    "/api/portfolio",
    "/api/agents",
    "/api/runs",
    "/api/external-reviews",
    "/api/worktrees",
}

_STATUS_RANK = {"ok": 0, "missing": 1, "stale": 2, "invalid": 3}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:"
    r"[0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]{1,6})?)?Z$"
)


class DashboardError(Exception):
    """Base class for user-visible dashboard failures."""


class InvalidRootError(DashboardError):
    """The requested path is not an HMASD checkout."""


class UnstableSnapshotError(DashboardError):
    """The source generation changed for every bounded aggregation attempt."""


@dataclass(frozen=True)
class Document:
    """One read-only document observation."""

    status: str
    value: dict[str, Any] | None
    revision: int | None
    updated_at: str | None
    digest: str | None
    warning: str | None = None


@dataclass(frozen=True)
class Root:
    """Validated checkout root and its fixed asset directory."""

    path: Path

    @property
    def asset_dir(self) -> Path:
        return Path(__file__).resolve().parent / "dashboard"


def resolve_root(raw: str | os.PathLike[str]) -> Root:
    """Resolve and validate an HMASD checkout.

    The marker is intentionally part of the contract.  It prevents accidentally
    exposing a user's arbitrary directory when the CLI is pointed at a typo.
    """

    try:
        candidate = Path(raw).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, TypeError) as exc:
        raise InvalidRootError("root is not a readable directory") from exc
    if not candidate.is_dir():
        raise InvalidRootError("root is not a directory")
    markers = (
        candidate / "AGENTS.md",
        candidate / ".codex" / "config.toml",
        candidate / ".omp" / "AGENTS.md",
    )
    def has_marker(path: Path) -> bool:
        try:
            return path.is_file() and path.stat().st_size > 0
        except OSError:
            return False

    if not any(has_marker(marker) for marker in markers):
        raise InvalidRootError("root is missing AGENTS.md or Codex/OMP project metadata")
    return Root(candidate)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _json_text(value: Any) -> str:
    return _json_bytes(value).decode("utf-8")


def _write_json_stdout(value: Any) -> None:
    """Write CLI JSON as UTF-8 bytes regardless of the console code page."""

    body = _json_bytes(value)
    stdout_buffer = getattr(sys.stdout, "buffer", None)
    if stdout_buffer is not None:
        stdout_buffer.write(body)
        stdout_buffer.flush()
        return
    # Embedded callers may provide a text-only stream (for example, a test
    # capture object).  The real CLI always has ``stdout.buffer``.
    sys.stdout.write(body.decode("utf-8"))


def _under_root(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _safe_relative_path(root: Path, value: Any, *, must_exist: bool = False) -> Path | None:
    """Return an in-root path for a tracked repo-relative POSIX reference."""

    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts or "." in posix.parts:
        return None
    # PurePosixPath collapses repeated slashes; reject them rather than silently
    # changing a reference selected by another writer.
    if "//" in value or value.startswith("./") or value.endswith("/"):
        return None
    candidate = root.joinpath(*posix.parts)
    try:
        resolved = candidate.resolve(strict=must_exist)
    except (OSError, RuntimeError):
        return None
    if not _under_root(root, resolved):
        return None
    if must_exist and (not resolved.is_file() or resolved.is_symlink()):
        return None
    return resolved


def _read_bytes(path: Path) -> tuple[bytes | None, str | None]:
    try:
        if path.is_symlink() or not path.is_file():
            return None, "not_file"
        data = path.read_bytes()
    except OSError:
        return None, "unreadable"
    return data, None


def _load_schema(root: Path, kind: str) -> tuple[dict[str, Any] | None, Path | None]:
    schema_path = root / "scripts" / "schemas" / f"hmasd_{kind}.schema.json"
    if not schema_path.is_file():
        # A temporary isolated fixture may contain only the authoritative files.
        # The checkout's schema is a safe fallback for read-only validation.
        schema_path = Path(__file__).resolve().parent / "schemas" / f"hmasd_{kind}.schema.json"
    try:
        raw = schema_path.read_bytes()
        schema = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, None
    return schema if isinstance(schema, dict) else None, schema_path


def _resolve_ref(schema: Mapping[str, Any], root_schema: Mapping[str, Any]) -> Mapping[str, Any] | None:
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return schema
    current: Any = root_schema
    for part in ref[2:].split("/"):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current if isinstance(current, Mapping) else None


def _schema_type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _schema_valid(value: Any, schema: Mapping[str, Any], root_schema: Mapping[str, Any]) -> bool:
    schema = _resolve_ref(schema, root_schema) or {}
    if "$ref" in schema and _resolve_ref(schema, root_schema) is None:
        return False
    if "const" in schema and value != schema["const"]:
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    expected = schema.get("type")
    if isinstance(expected, list):
        if not any(_schema_type_ok(value, item) for item in expected if isinstance(item, str)):
            return False
    elif isinstance(expected, str) and not _schema_type_ok(value, expected):
        return False
    if isinstance(value, str):
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            return False
        if isinstance(schema.get("maxLength"), int) and len(value) > schema["maxLength"]:
            return False
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            try:
                if re.search(pattern, value) is None:
                    return False
            except re.error:
                return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(schema.get("minimum"), (int, float)) and value < schema["minimum"]:
            return False
        if isinstance(schema.get("maximum"), (int, float)) and value > schema["maximum"]:
            return False
    if isinstance(value, list):
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
            return False
        if isinstance(schema.get("maxItems"), int) and len(value) > schema["maxItems"]:
            return False
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping) and not all(
            _schema_valid(item, item_schema, root_schema) for item in value
        ):
            return False
    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list) and any(key not in value for key in required):
            return False
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            properties = {}
        if schema.get("additionalProperties") is False:
            if any(key not in properties for key in value):
                return False
        for key, child in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, Mapping) and not _schema_valid(child, child_schema, root_schema):
                return False
            if child_schema is None and isinstance(schema.get("additionalProperties"), Mapping):
                if not _schema_valid(child, schema["additionalProperties"], root_schema):
                    return False
    for keyword in ("allOf", "anyOf", "oneOf"):
        choices = schema.get(keyword)
        if isinstance(choices, list) and choices:
            outcomes = [
                _schema_valid(value, item, root_schema)
                for item in choices
                if isinstance(item, Mapping)
            ]
            if keyword == "allOf" and not all(outcomes):
                return False
            if keyword == "anyOf" and not any(outcomes):
                return False
            if keyword == "oneOf" and sum(outcomes) != 1:
                return False
    if isinstance(schema.get("not"), Mapping) and _schema_valid(value, schema["not"], root_schema):
        return False
    return True


def _basic_kind_shape(kind: str, value: Mapping[str, Any]) -> bool:
    """Fallback when an isolated fixture omits the schema files."""

    required: dict[str, tuple[str, ...]] = {
        "portfolio_registry": ("schema_version", "revision", "updated_at", "writer", "workflow_version", "goal", "directions"),
        "research_state": ("schema_version", "revision", "updated_at", "writer", "direction_id", "phase"),
        "engineering_state": ("schema_version", "revision", "updated_at", "writer", "direction_id", "phase"),
        "external_review_index": ("schema_version", "revision", "updated_at", "writer", "direction_id", "rounds"),
        "run_manifest": ("schema_version", "revision", "updated_at", "writer", "run_id", "direction_id", "status"),
        "accepted_result": ("schema_version", "revision", "updated_at", "writer", "result_id", "direction_id"),
        "runtime_agents": ("schema_version", "revision", "updated_at", "writer", "agents"),
        "runtime_worktrees": ("schema_version", "revision", "updated_at", "writer", "worktrees"),
        "runtime_tasks": ("schema_version", "revision", "updated_at", "writer", "tasks"),
    }
    if kind == "external_archive":
        return value.get("schema") == "agentify_review_natural_completion_archive_v1"
    if kind == "agent_result":
        return value.get("schema_version") == 1 and isinstance(value.get("role"), str)
    keys = required.get(kind)
    if keys is None or any(key not in value for key in keys):
        return False
    return value.get("schema_version") == 1 and isinstance(value.get("revision"), int)


def _semantic_valid(kind: str, value: Mapping[str, Any]) -> bool:
    """Cross-document invariants not expressible in the small JSON schemas."""

    if kind == "portfolio_registry":
        directions = value.get("directions")
        if not isinstance(directions, list):
            return False
        raw_ids = [item.get("id") for item in directions if isinstance(item, dict)]
        if (
            len(raw_ids) != len(directions)
            or any(not isinstance(identifier, str) for identifier in raw_ids)
        ):
            return False
        ids = [identifier for identifier in raw_ids if isinstance(identifier, str)]
        if len(ids) != len(set(ids)):
            return False
        if sum(item.get("lifecycle") == "ACTIVE" for item in directions if isinstance(item, dict)) > 8:
            return False
        known = set(ids)
        graph: dict[str, list[str]] = {}
        for item in directions:
            if not isinstance(item, dict):
                return False
            identifier = item.get("id")
            deps = item.get("dependencies", [])
            if not isinstance(identifier, str) or not isinstance(deps, list) or any(
                not isinstance(dep, str) or dep not in known for dep in deps
            ):
                return False
            graph[identifier] = deps
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(identifier: str) -> bool:
            if identifier in visiting:
                return False
            if identifier in visited:
                return True
            visiting.add(identifier)
            if any(not visit(dep) for dep in graph.get(identifier, [])):
                return False
            visiting.remove(identifier)
            visited.add(identifier)
            return True

        return all(visit(identifier) for identifier in graph)
    if kind in {"runtime_agents", "runtime_worktrees"}:
        values = value.get("agents" if kind == "runtime_agents" else "worktrees")
        if not isinstance(values, list):
            return False
        key = "logical_identity" if kind == "runtime_agents" else "worktree_ref"
        ids = [item.get(key) for item in values if isinstance(item, dict)]
        if len(ids) != len(values) or any(not isinstance(identifier, str) for identifier in ids):
            return False
        return len(ids) == len(set(ids))
    if kind == "runtime_tasks":
        values = value.get("tasks")
        if not isinstance(values, list):
            return False
        identities = [
            item.get("logical_identity")
            for item in values
            if isinstance(item, Mapping)
        ]
        if len(identities) != len(values) or any(
            not isinstance(identity, str) for identity in identities
        ):
            return False
        return len(identities) == len(set(identities))
    return True


def _read_document(root: Path, relative: str, kind: str, *, required: bool = False) -> Document:
    path = _safe_relative_path(root, relative, must_exist=False)
    if path is None:
        return Document("invalid", None, None, None, None, f"invalid_ref:{relative}")
    if not path.exists():
        status = "invalid" if required else "missing"
        return Document(status, None, None, None, None, f"missing:{relative}")
    raw, error = _read_bytes(path)
    if raw is None:
        status = "invalid" if required else "missing"
        return Document(status, None, None, None, None, f"unreadable:{relative}")
    digest = hashlib.sha256(raw).hexdigest()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return Document("invalid", None, None, None, digest, f"malformed:{relative}")
    if not isinstance(value, dict):
        return Document("invalid", None, None, None, digest, f"not_object:{relative}")
    schema, _schema_path = _load_schema(root, kind)
    valid = _schema_valid(value, schema, schema) if schema is not None else _basic_kind_shape(kind, value)
    valid = valid and _semantic_valid(kind, value)
    if not valid:
        return Document("invalid", None, None, None, digest, f"invalid_schema:{kind}")
    revision = value.get("revision") if isinstance(value.get("revision"), int) else None
    updated_at = value.get("updated_at") if isinstance(value.get("updated_at"), str) else None
    return Document("ok", value, revision, updated_at, digest)


@dataclass(frozen=True)
class _DirectoryObservation:
    entries: tuple[tuple[Path, str], ...]
    signature: tuple[str, tuple[tuple[str, str], ...]]


def _scan_directory(path: Path) -> _DirectoryObservation:
    if path.is_symlink() or not path.is_dir():
        return _DirectoryObservation((), ("not_directory", ()))
    try:
        children = sorted(path.iterdir(), key=lambda child: child.name)
    except OSError:
        return _DirectoryObservation((), ("unreadable", ()))
    entries: list[tuple[Path, str]] = []
    signature: list[tuple[str, str]] = []
    for child in children:
        if child.is_symlink():
            kind = "symlink"
        elif child.is_dir():
            kind = "directory"
        elif child.is_file():
            kind = "file"
        else:
            kind = "other"
        entries.append((child, kind))
        signature.append((child.name, kind))
    return _DirectoryObservation(tuple(entries), ("ok", tuple(signature)))


class _SnapshotAttempt:
    """Caches one generation and verifies every observed source before use."""

    def __init__(self, root: Path):
        self.root = root
        self._documents: dict[str, tuple[str, Document]] = {}
        self._file_digests: dict[Path, str | None] = {}
        self._file_labels: dict[Path, str] = {}
        self._directories: dict[Path, _DirectoryObservation] = {}
        self._directory_labels: dict[Path, str] = {}

    def read_document(
        self,
        relative: str,
        kind: str,
        *,
        required: bool = False,
    ) -> Document:
        cached = self._documents.get(relative)
        if cached is not None:
            cached_kind, document = cached
            if cached_kind != kind:
                return Document(
                    "invalid",
                    None,
                    None,
                    None,
                    document.digest,
                    f"invalid_kind:{relative}",
                )
            return document
        document = _read_document(self.root, relative, kind, required=required)
        self._documents[relative] = (kind, document)
        path = _safe_relative_path(self.root, relative, must_exist=False)
        if path is not None:
            self._file_digests[path] = document.digest
            self._file_labels[path] = relative
        return document

    def read_runtime_document(
        self,
        relative: str,
        legacy_relative: str,
        kind: str,
        empty_value: Mapping[str, Any],
    ) -> Document:
        """Read the active runtime map, falling back to the OMP map.

        Runtime maps are disposable task/process observations rather than
        workflow authorities.  A fresh Codex checkout normally has neither
        map, so both missing paths intentionally collapse to an empty, healthy
        projection.  Malformed or otherwise unreadable data is still surfaced
        when a map exists; that keeps real runtime corruption observable while
        avoiding noisy ``cannot open file`` failures during normal startup.
        """

        active = self.read_document(relative, kind)
        if active.status != "missing":
            return active
        legacy = self.read_document(legacy_relative, kind)
        if legacy.status != "missing":
            return legacy
        return Document("ok", dict(empty_value), None, None, None)

    def read_digest(self, relative: str) -> str | None:
        path = _safe_relative_path(self.root, relative, must_exist=False)
        if path is None:
            return None
        if path in self._file_digests:
            return self._file_digests[path]
        raw, _ = _read_bytes(path)
        digest = hashlib.sha256(raw).hexdigest() if raw is not None else None
        self._file_digests[path] = digest
        self._file_labels[path] = relative
        return digest

    def directory_entries(self, path: Path, label: str) -> tuple[tuple[Path, str], ...]:
        observed = self._directories.get(path)
        if observed is None:
            observed = _scan_directory(path)
            self._directories[path] = observed
            self._directory_labels[path] = label
        return observed.entries

    def changed_sources(self) -> tuple[str, ...]:
        changed: list[str] = []
        for path, expected in self._file_digests.items():
            raw, _ = _read_bytes(path)
            observed = hashlib.sha256(raw).hexdigest() if raw is not None else None
            if observed != expected:
                changed.append(self._file_labels[path])
        for path, expected in self._directories.items():
            if _scan_directory(path).signature != expected.signature:
                changed.append(self._directory_labels[path])
        return tuple(sorted(set(changed)))


def _warning_add(warnings: list[str], value: str | None) -> None:
    if value and value not in warnings:
        warnings.append(value)


def _status_join(statuses: Iterable[str]) -> str:
    statuses = list(statuses)
    if not statuses:
        return "ok"
    return max(statuses, key=lambda status: _STATUS_RANK.get(status, 3))


def _projection(
    *,
    status: str,
    generated_at: str,
    revision_refs: Mapping[str, int],
    data: Any,
    warnings: Iterable[str],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at if _TIMESTAMP_RE.match(generated_at) else EPOCH,
        "status": status if status in _STATUS_RANK else "invalid",
        "revision_refs": {key: revision_refs[key] for key in sorted(revision_refs)},
        "data": data,
        "warnings": sorted(set(warnings)),
    }


def _max_timestamp(values: Iterable[str | None]) -> str:
    usable = [value for value in values if isinstance(value, str) and _TIMESTAMP_RE.match(value)]
    return max(usable) if usable else EPOCH


def _sha_ref(value: Any) -> dict[str, str] | None:
    if not isinstance(value, Mapping):
        return None
    path = value.get("path")
    sha = value.get("sha256")
    if not isinstance(path, str) or not isinstance(sha, str) or not _SHA256_RE.fullmatch(sha):
        return None
    return {"path": path, "sha256": sha}


def _safe_metric(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    result: dict[str, Any] = {}
    for key in ("value", "unit", "split", "aggregation", "sample_count"):
        if key in value and isinstance(value[key], (str, int, float)) and not isinstance(value[key], bool):
            result[key] = value[key]
    return result or None


def _safe_research(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ("direction_id", "phase", "actionable", "active_round_id", "last_checkpoint_sha"):
        if key in value and isinstance(value[key], (str, bool)):
            result[key] = value[key]
    blockers = value.get("blockers")
    if isinstance(blockers, list):
        blocker_codes = [
            item["code"]
            for item in blockers
            if isinstance(item, Mapping) and isinstance(item.get("code"), str)
        ]
        result["blocker_codes"] = sorted(set(blocker_codes))
    waiting = value.get("waiting_on")
    if isinstance(waiting, list):
        waiting_kinds = [
            item["kind"]
            for item in waiting
            if isinstance(item, Mapping) and isinstance(item.get("kind"), str)
        ]
        result["waiting_kinds"] = sorted(set(waiting_kinds))
    next_action = value.get("next_action")
    if isinstance(next_action, Mapping) and isinstance(next_action.get("kind"), str):
        result["next_action_kind"] = next_action["kind"]
    return result


def _safe_engineering(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ("direction_id", "phase", "actionable", "base_sha", "candidate_sha", "worktree_ref", "last_checkpoint_sha"):
        if key in value and (isinstance(value[key], (str, bool)) or value[key] is None):
            result[key] = value[key]
    changed = value.get("changed_paths")
    if isinstance(changed, list):
        safe_paths = [
            path
            for path in changed
            if isinstance(path, str) and ".." not in PurePosixPath(path).parts
        ]
        result["changed_paths"] = sorted(safe_paths)
    refs = value.get("verification_refs")
    if isinstance(refs, list):
        result["verification_count"] = len(refs)
    integration = value.get("integration")
    if isinstance(integration, Mapping):
        result["integration"] = {
            key: integration[key]
            for key in ("target_branch", "target_sha_seen", "integrated_sha")
            if key in integration and (isinstance(integration[key], str) or integration[key] is None)
        }
    next_action = value.get("next_action")
    if isinstance(next_action, Mapping) and isinstance(next_action.get("kind"), str):
        result["next_action_kind"] = next_action["kind"]
    return result


def _registry_direction(registry: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    directions = registry.get("directions")
    if not isinstance(directions, list):
        return []
    return sorted((item for item in directions if isinstance(item, Mapping)), key=lambda item: str(item.get("id", "")))


def _build_portfolio(root: Path, registry_doc: Document, sources: _SnapshotAttempt) -> dict[str, Any]:
    warnings: list[str] = []
    if registry_doc.status != "ok" or registry_doc.value is None:
        _warning_add(warnings, registry_doc.warning)
        return _projection(
            status=registry_doc.status,
            generated_at=registry_doc.updated_at or EPOCH,
            revision_refs={},
            data={"goal": None, "directions": []},
            warnings=warnings,
        )
    registry = registry_doc.value
    refs: dict[str, int] = {"registry": registry_doc.revision or 1}
    statuses = ["ok"]
    goal = _sha_ref(registry.get("goal"))
    if goal is None or _safe_relative_path(root, goal["path"], must_exist=False) is None:
        _warning_add(warnings, "invalid:portfolio_goal_ref")
        statuses.append("invalid")
        goal = None
    directions: list[dict[str, Any]] = []
    generated_values: list[str | None] = [registry_doc.updated_at]
    for item in _registry_direction(registry):
        identifier = item.get("id")
        if not isinstance(identifier, str):
            continue
        output: dict[str, Any] = {
            key: item[key]
            for key in ("id", "abbreviation", "path", "lifecycle", "dependencies")
            if key in item
        }
        agent = item.get("agent")
        if isinstance(agent, Mapping):
            output["agent"] = {
                key: agent[key]
                for key in ("logical_identity", "job_name", "generation")
                if key in agent and isinstance(agent[key], (str, int))
            }
        for state_key, kind, safe_fn in (
            ("research_state_path", "research_state", _safe_research),
            ("engineering_state_path", "engineering_state", _safe_engineering),
        ):
            state_ref = item.get(state_key)
            if not isinstance(state_ref, str):
                _warning_add(warnings, f"invalid:{identifier}:{state_key}")
                statuses.append("invalid")
                output[state_key.removesuffix("_path") + "_status"] = "invalid"
                continue
            document = sources.read_document(state_ref, kind)
            generated_values.append(document.updated_at)
            if document.revision is not None:
                refs[f"{kind}:{identifier}"] = document.revision
            output[state_key.removesuffix("_path") + "_status"] = document.status
            if document.status == "ok" and document.value is not None:
                output[state_key.removesuffix("_path")] = safe_fn(document.value)
            else:
                statuses.append(document.status)
                _warning_add(warnings, document.warning)
        ext_ref = item.get("external_review_index_path")
        if isinstance(ext_ref, str):
            ext_doc = sources.read_document(ext_ref, "external_review_index")
            generated_values.append(ext_doc.updated_at)
            if ext_doc.revision is not None:
                refs[f"external_review_index:{identifier}"] = ext_doc.revision
            output["external_review_status"] = ext_doc.status
            if ext_doc.status == "ok" and ext_doc.value is not None:
                rounds = ext_doc.value.get("rounds")
                if isinstance(rounds, list):
                    output["external_round_count"] = len(rounds)
                    output["external_round_statuses"] = sorted(
                        str(round_item.get("status"))
                        for round_item in rounds
                        if isinstance(round_item, Mapping) and isinstance(round_item.get("status"), str)
                    )
            else:
                statuses.append(ext_doc.status)
                _warning_add(warnings, ext_doc.warning)
        else:
            output["external_review_status"] = "invalid"
            statuses.append("invalid")
            _warning_add(warnings, f"invalid:{identifier}:external_review_index_path")
        directions.append(output)
    return _projection(
        status=_status_join(statuses),
        generated_at=_max_timestamp(generated_values),
        revision_refs=refs,
        data={"goal": goal, "directions": directions},
        warnings=warnings,
    )


def _agent_type(logical_identity: str) -> str:
    if logical_identity == "Root":
        return "hmasd-root"
    if logical_identity == "Portfolio":
        return "hmasd-portfolio"
    if logical_identity.startswith("EM-"):
        return "hmasd-em"
    if logical_identity.startswith("CM-"):
        return "hmasd-cm"
    return "hmasd-agent"


def _manager_job_name(prefix: str, direction_id: str) -> str:
    return prefix + "".join(part[:1].upper() + part[1:] for part in re.split(r"[-_]+", direction_id) if part)


def _build_agents(registry_doc: Document, sources: _SnapshotAttempt) -> dict[str, Any]:
    warnings: list[str] = []
    statuses: list[str] = []
    refs: dict[str, int] = {}
    generated_values: list[str | None] = [registry_doc.updated_at]
    logical: dict[str, dict[str, Any]] = {
        "Root": {
            "logical_identity": "Root",
            "agent_type": "hmasd-root",
            "task_level": "top-level",
            "generation": 1,
            "lifecycle": "ACTIVE",
            "job_name": "Root",
            "parent_identity": "Root",
        },
        # Portfolio is a user-facing top-level task in Codex.  It is not
        # derived from a direction registry entry and therefore remains
        # visible even when no disposable runtime map has been created.
        "Portfolio": {
            "logical_identity": "Portfolio",
            "agent_type": "hmasd-portfolio",
            "task_level": "top-level",
            "generation": 1,
            "lifecycle": "ACTIVE",
            "job_name": "Portfolio",
        },
    }
    if registry_doc.status == "ok" and registry_doc.value is not None:
        refs["registry"] = registry_doc.revision or 1
        for item in _registry_direction(registry_doc.value):
            identifier = item.get("id")
            agent = item.get("agent")
            if not isinstance(identifier, str) or not isinstance(agent, Mapping):
                continue
            identity = agent.get("logical_identity")
            generation = agent.get("generation", 1)
            if isinstance(identity, str):
                logical[identity] = {
                    "logical_identity": identity,
                    "agent_type": _agent_type(identity),
                    "task_level": "top-level",
                    "generation": generation,
                    "lifecycle": item.get("lifecycle", "UNKNOWN"),
                    "job_name": agent.get("job_name", identity),
                    "parent_identity": "Root",
                    "direction_id": identifier,
                }

            engineering_ref = item.get("engineering_state_path")
            if not isinstance(engineering_ref, str):
                statuses.append("invalid")
                _warning_add(warnings, f"invalid:{identifier}:engineering_state_path")
                continue
            engineering = sources.read_document(engineering_ref, "engineering_state")
            generated_values.append(engineering.updated_at)
            if engineering.revision is not None:
                refs[f"engineering_state:{identifier}"] = engineering.revision
            if engineering.status != "ok" or engineering.value is None:
                statuses.append(engineering.status)
                _warning_add(warnings, engineering.warning)
                continue
            phase = engineering.value.get("phase")
            active_agents = engineering.value.get("active_agents")
            cm_expected = (
                phase != "UNREQUESTED"
                or engineering.value.get("actionable") is True
                or isinstance(active_agents, list) and bool(active_agents)
            )
            if cm_expected:
                cm_identity = f"CM-{identifier}"
                logical[cm_identity] = {
                    "logical_identity": cm_identity,
                    "agent_type": "hmasd-cm",
                    "task_level": "top-level",
                    "generation": generation,
                    "lifecycle": phase if isinstance(phase, str) else "UNKNOWN",
                    "job_name": _manager_job_name("CM", identifier),
                    "parent_identity": "Root",
                    "direction_id": identifier,
                    "phase": phase if isinstance(phase, str) else "UNKNOWN",
                }
    else:
        statuses.append(registry_doc.status)
        _warning_add(warnings, registry_doc.warning)

    runtime = sources.read_runtime_document(
        RUNTIME_AGENTS_REL,
        LEGACY_RUNTIME_AGENTS_REL,
        "runtime_agents",
        {"schema_version": 1, "revision": 0, "agents": []},
    )
    generated_values.append(runtime.updated_at)
    if runtime.revision is not None:
        refs["runtime_agents"] = runtime.revision
    if runtime.status != "ok" or runtime.value is None:
        statuses.append(runtime.status)
        _warning_add(warnings, runtime.warning)
    else:
        expected_identities = set(logical)
        runtime_items = runtime.value.get("agents", [])
        if not isinstance(runtime_items, list):
            statuses.append("invalid")
            _warning_add(warnings, "invalid:runtime_agents")
            runtime_items = []
        for item in sorted(
            (entry for entry in runtime_items if isinstance(entry, Mapping)),
            key=lambda entry: str(entry.get("logical_identity", "")),
        ):
            identity = item.get("logical_identity")
            if not isinstance(identity, str):
                statuses.append("invalid")
                _warning_add(warnings, "invalid:runtime_agents_identity")
                continue
            runtime_only = identity not in expected_identities
            entry = logical.setdefault(
                identity,
                {
                    "logical_identity": identity,
                    "agent_type": item.get("agent_type", _agent_type(identity)),
                    "task_level": "leaf",
                    "generation": item.get("generation", 1),
                    "lifecycle": "UNKNOWN",
                    "job_name": item.get("job_ref", identity),
                },
            )
            expected_generation = entry.get("generation")
            observed_generation = item.get("generation")
            if runtime_only:
                statuses.append("stale")
                _warning_add(warnings, f"stale:unknown_agent:{identity}")
            elif expected_generation != observed_generation:
                statuses.append("stale")
                _warning_add(warnings, f"stale:agent_generation:{identity}")
            expected_parent = entry.get("parent_identity")
            observed_parent = item.get("parent_identity")
            if not runtime_only and expected_parent != observed_parent:
                statuses.append("stale")
                _warning_add(warnings, f"stale:agent_parent:{identity}")
            for source, target in (
                ("agent_type", "agent_type"),
                ("generation", "generation"),
                ("lifecycle", "lifecycle"),
                ("job_ref", "job_name"),
                ("parent_identity", "parent_identity"),
                ("last_seen_at", "last_seen_at"),
            ):
                if source in item and isinstance(item[source], (str, int)):
                    entry[target] = item[source]

    # The Codex task map carries live task/thread references in ignored
    # runtime state.  Project only the non-sensitive identity/lifecycle fields;
    # missing maps are quiet, while malformed maps remain visible as invalid.
    tasks = sources.read_runtime_document(
        RUNTIME_TASKS_REL,
        LEGACY_RUNTIME_TASKS_REL,
        "runtime_tasks",
        {"schema_version": 1, "revision": 0, "tasks": []},
    )
    generated_values.append(tasks.updated_at)
    if tasks.revision is not None:
        refs["runtime_tasks"] = tasks.revision
    if tasks.status != "ok" or tasks.value is None:
        statuses.append(tasks.status)
        _warning_add(warnings, tasks.warning)
    else:
        task_items = tasks.value.get("tasks", [])
        if not isinstance(task_items, list):
            statuses.append("invalid")
            _warning_add(warnings, "invalid:runtime_tasks")
            task_items = []
        kind_types = {
            "root": "hmasd-root",
            "portfolio": "hmasd-portfolio",
            "em": "hmasd-em",
            "cm": "hmasd-cm",
        }
        top_level_kinds = set(kind_types)
        for item in sorted(
            (entry for entry in task_items if isinstance(entry, Mapping)),
            key=lambda entry: str(entry.get("logical_identity", "")),
        ):
            identity = item.get("logical_identity")
            if not isinstance(identity, str):
                statuses.append("invalid")
                _warning_add(warnings, "invalid:runtime_tasks_identity")
                continue
            kind = item.get("kind")
            task_type = item.get("agent_type")
            if not isinstance(task_type, str):
                task_type = kind_types.get(kind, _agent_type(identity))
            task_level = "top-level" if kind in top_level_kinds else "leaf"
            entry = logical.setdefault(
                identity,
                {
                    "logical_identity": identity,
                    "agent_type": task_type,
                    "task_level": task_level,
                    "generation": item.get("generation", 1),
                    "lifecycle": "UNKNOWN",
                    "job_name": item.get("task_title", identity),
                },
            )
            expected_generation = entry.get("generation")
            observed_generation = item.get("generation")
            if isinstance(observed_generation, int) and expected_generation != observed_generation:
                statuses.append("stale")
                _warning_add(warnings, f"stale:task_generation:{identity}")
            for source, target in (
                ("agent_type", "agent_type"),
                ("generation", "generation"),
                ("task_title", "job_name"),
                ("direction_id", "direction_id"),
                ("lifecycle", "lifecycle"),
                ("parent_identity", "parent_identity"),
                ("last_seen_at", "last_seen_at"),
            ):
                if source in item and isinstance(item[source], (str, int)):
                    entry[target] = item[source]
            entry["task_level"] = task_level

    agents: list[dict[str, Any]] = []
    for identity in sorted(logical):
        entry = logical[identity]
        output = {
            key: entry[key]
            for key in (
                "logical_identity",
                "agent_type",
                "task_level",
                "parent_identity",
                "direction_id",
                "generation",
                "lifecycle",
                "phase",
                "job_name",
                "last_seen_at",
            )
            if key in entry and isinstance(entry[key], (str, int))
        }
        agents.append(output)
    if not statuses:
        statuses = ["ok"]
    return _projection(
        status=_status_join(statuses),
        generated_at=_max_timestamp(generated_values),
        revision_refs=refs,
        data={"agents": agents},
        warnings=warnings,
    )


def _safe_run(value: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key in ("run_id", "direction_id", "assignment_id", "operator_identity", "status", "command_sha256", "code_sha"):
        if key in value and isinstance(value[key], str):
            output[key] = value[key]
    estimate = value.get("estimate")
    if isinstance(estimate, Mapping):
        output["estimate"] = {
            key: estimate[key]
            for key in ("wall_seconds", "peak_memory_gib")
            if key in estimate and isinstance(estimate[key], (int, float)) and not isinstance(estimate[key], bool)
        }
    resources = value.get("resources")
    if isinstance(resources, Mapping):
        output["resources"] = {
            key: resources[key]
            for key in ("workers", "threads_per_worker", "memory_safe")
            if key in resources and isinstance(resources[key], (int, bool))
        }
    process = value.get("process")
    if isinstance(process, Mapping):
        output["process"] = {
            key: process[key]
            for key in ("started_at", "ended_at", "exit_code", "terminal_reason")
            if key in process and (isinstance(process[key], (str, int)) or process[key] is None)
        }
    metrics = value.get("observed_metrics")
    if isinstance(metrics, Mapping):
        safe_metrics: dict[str, Any] = {}
        for name, metric in sorted(metrics.items()):
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", name):
                continue
            if isinstance(metric, (int, float)) and not isinstance(metric, bool):
                safe_metrics[name] = metric
            elif isinstance(metric, Mapping):
                safe = _safe_metric(metric)
                if safe is not None:
                    safe_metrics[name] = safe
        output["observed_metrics"] = safe_metrics
    return output


def _safe_result(value: Mapping[str, Any]) -> dict[str, Any]:
    output = {
        key: value[key]
        for key in ("result_id", "direction_id", "promoted_at", "promoted_by", "conclusion_path")
        if key in value and isinstance(value[key], str)
    }
    source = value.get("source_run")
    if isinstance(source, Mapping):
        output["source_run"] = {
            key: source[key]
            for key in ("run_id", "code_sha")
            if key in source and isinstance(source[key], str)
        }
    metrics = value.get("metrics")
    if isinstance(metrics, Mapping):
        output["metrics"] = {
            name: safe
            for name, metric in sorted(metrics.items())
            if isinstance(name, str) and (safe := _safe_metric(metric)) is not None
        }
    return output


def _manifest_paths(root: Path, registry_doc: Document, sources: _SnapshotAttempt) -> list[tuple[str, Path]]:
    if registry_doc.status != "ok" or registry_doc.value is None:
        return []
    result: list[tuple[str, Path]] = []
    for direction in _registry_direction(registry_doc.value):
        identifier = direction.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,63}", identifier):
            continue
        base = _safe_relative_path(root, f"temp/directions/{identifier}/exp", must_exist=False)
        if base is None:
            continue
        for child, kind in sources.directory_entries(base, f"run_directory:{identifier}"):
            if kind != "directory" or child.name in {".", ".."}:
                continue
            manifest = child / "manifest.json"
            if _under_root(root, manifest.resolve(strict=False)):
                result.append((f"{identifier}:{child.name}", manifest))
    return result


def _result_paths(root: Path, registry_doc: Document, sources: _SnapshotAttempt) -> list[Path]:
    if registry_doc.status != "ok" or registry_doc.value is None:
        return []
    paths: list[Path] = []
    for direction in _registry_direction(registry_doc.value):
        identifier = direction.get("id")
        if not isinstance(identifier, str):
            continue
        base = _safe_relative_path(root, f"docs/research/candidates/{identifier}/results", must_exist=False)
        if base is None:
            continue
        for child, kind in sources.directory_entries(base, f"result_directory:{identifier}"):
            if kind == "file" and child.suffix == ".json" and _under_root(root, child.resolve(strict=False)):
                paths.append(child)
    return paths


def _build_runs(root: Path, registry_doc: Document, sources: _SnapshotAttempt) -> dict[str, Any]:
    warnings: list[str] = []
    refs: dict[str, int] = {}
    statuses: list[str] = []
    generated_values: list[str | None] = [registry_doc.updated_at]
    runs: list[dict[str, Any]] = []
    manifests = _manifest_paths(root, registry_doc, sources)
    if not manifests:
        statuses.append("missing")
        _warning_add(warnings, "missing:run_manifests")
    for label, path in manifests:
        relative = path.relative_to(root).as_posix()
        doc = sources.read_document(relative, "run_manifest")
        generated_values.append(doc.updated_at)
        if doc.revision is not None:
            refs[f"run:{label}"] = doc.revision
        if doc.status == "ok" and doc.value is not None:
            runs.append(_safe_run(doc.value))
        else:
            statuses.append(doc.status)
            _warning_add(warnings, doc.warning)
    results: list[dict[str, Any]] = []
    result_paths = _result_paths(root, registry_doc, sources)
    for path in result_paths:
        relative = path.relative_to(root).as_posix()
        doc = sources.read_document(relative, "accepted_result")
        generated_values.append(doc.updated_at)
        if doc.revision is not None:
            refs[f"result:{path.stem}"] = doc.revision
        if doc.status == "ok" and doc.value is not None:
            results.append(_safe_result(doc.value))
        else:
            statuses.append(doc.status)
            _warning_add(warnings, doc.warning)
    if result_paths == [] and not manifests:
        statuses.append("missing")
    if runs or results:
        if not any(status in {"invalid", "stale"} for status in statuses):
            statuses = ["ok"]
    return _projection(
        status=_status_join(statuses),
        generated_at=_max_timestamp(generated_values),
        revision_refs=refs,
        data={"runs": sorted(runs, key=lambda item: str(item.get("run_id", ""))), "results": sorted(results, key=lambda item: str(item.get("result_id", "")))},
        warnings=warnings,
    )


def _safe_provider(
    provider: Any,
    root: Path,
    warnings: list[str],
    round_id: str,
    name: str,
    sources: _SnapshotAttempt,
) -> dict[str, Any] | None:
    if not isinstance(provider, Mapping):
        return None
    result: dict[str, Any] = {}
    for source, target in (
        ("operation_id", "operation_id"),
        ("operationId", "operation_id"),
        ("terminal_state", "terminal_state"),
        ("terminalState", "terminal_state"),
        ("completed_at", "completed_at"),
        ("completedAt", "completed_at"),
        ("provider", "provider"),
        ("mode", "mode"),
    ):
        if source in provider and isinstance(provider[source], str):
            result[target] = provider[source]
    for source, target in (("archive_ref", "archive"), ("handoff_ref", "handoff")):
        reference = _sha_ref(provider.get(source))
        if reference is None:
            # Some providers use the explicit path/SHA pair in the index.
            prefix = source.removesuffix("_ref")
            path = provider.get(f"{prefix}_path")
            sha = provider.get(f"{prefix}_sha256")
            reference = _sha_ref({"path": path, "sha256": sha})
        if reference is None:
            continue
        result[target] = reference
        reference_path = reference["path"]
        if not reference_path.startswith("docs/external-review/directions/"):
            _warning_add(warnings, f"invalid:external_ref:{round_id}:{name}:{target}")
            continue
        candidate = _safe_relative_path(root, reference_path, must_exist=False)
        if candidate is None:
            _warning_add(warnings, f"stale:external_ref:{round_id}:{name}:{target}")
            continue
        observed_sha = sources.read_digest(reference_path)
        if observed_sha is None:
            _warning_add(warnings, f"stale:external_ref:{round_id}:{name}:{target}")
            continue
        if observed_sha != reference["sha256"]:
            _warning_add(warnings, f"stale:external_sha:{round_id}:{name}:{target}")
    return result or None


def _build_external(root: Path, registry_doc: Document, sources: _SnapshotAttempt) -> dict[str, Any]:
    warnings: list[str] = []
    refs: dict[str, int] = {}
    statuses: list[str] = []
    generated_values: list[str | None] = [registry_doc.updated_at]
    rounds: list[dict[str, Any]] = []
    directions = _registry_direction(registry_doc.value) if registry_doc.status == "ok" and registry_doc.value else []
    if not directions:
        statuses.append(registry_doc.status if registry_doc.status != "ok" else "missing")
    for direction in directions:
        identifier = direction.get("id")
        reference = direction.get("external_review_index_path")
        if not isinstance(identifier, str) or not isinstance(reference, str):
            statuses.append("invalid")
            _warning_add(warnings, f"invalid:{identifier}:external_review_index_path")
            continue
        doc = sources.read_document(reference, "external_review_index")
        generated_values.append(doc.updated_at)
        if doc.revision is not None:
            refs[f"external_review_index:{identifier}"] = doc.revision
        if doc.status != "ok" or doc.value is None:
            statuses.append(doc.status)
            _warning_add(warnings, doc.warning)
            continue
        source_rounds = doc.value.get("rounds")
        if not isinstance(source_rounds, list):
            statuses.append("invalid")
            _warning_add(warnings, f"invalid:rounds:{identifier}")
            continue
        for source_round in sorted(
            (item for item in source_rounds if isinstance(item, Mapping)),
            key=lambda item: str(item.get("round_id", "")),
        ):
            round_id = source_round.get("round_id")
            if not isinstance(round_id, str):
                statuses.append("invalid")
                _warning_add(warnings, f"invalid:round:{identifier}")
                continue
            projected: dict[str, Any] = {
                key: source_round[key]
                for key in ("round_id", "question_sha256", "evidence_set_sha256", "status", "created_at", "completed_at")
                if key in source_round and (isinstance(source_round[key], str) or source_round[key] is None)
            }
            prompt_refs = source_round.get("prompt_refs")
            if isinstance(prompt_refs, Mapping):
                prompt_values: dict[str, dict[str, str]] = {}
                for name, value in sorted(prompt_refs.items()):
                    reference = _sha_ref(value)
                    if value is None:
                        continue
                    if not isinstance(name, str) or reference is None:
                        statuses.append("invalid")
                        _warning_add(warnings, f"invalid:prompt_ref:{identifier}:{round_id}")
                        continue
                    if not reference["path"].startswith("docs/external-review/directions/"):
                        statuses.append("invalid")
                        _warning_add(warnings, f"invalid:prompt_ref:{identifier}:{round_id}:{name}")
                        continue
                    prompt_values[name] = reference
                projected["prompt_refs"] = prompt_values
            providers = source_round.get("providers")
            if isinstance(providers, Mapping):
                provider_values: dict[str, Any] = {}
                for name, value in sorted(providers.items()):
                    before_warnings = len(warnings)
                    safe = _safe_provider(value, root, warnings, round_id, str(name), sources)
                    if len(warnings) > before_warnings:
                        statuses.append(
                            "invalid"
                            if any(item.startswith("invalid:") for item in warnings[before_warnings:])
                            else "stale"
                        )
                    if safe is not None:
                        provider_values[str(name)] = safe
                projected["providers"] = provider_values
            rounds.append(projected)
    if rounds and not any(status in {"invalid", "stale"} for status in statuses):
        statuses = ["ok"]
    return _projection(
        status=_status_join(statuses),
        generated_at=_max_timestamp(generated_values),
        revision_refs=refs,
        data={"rounds": rounds},
        warnings=warnings,
    )


def _build_worktrees(registry_doc: Document, sources: _SnapshotAttempt) -> dict[str, Any]:
    warnings: list[str] = []
    statuses: list[str] = []
    refs: dict[str, int] = {}
    generated_values: list[str | None] = [registry_doc.updated_at]
    if registry_doc.status != "ok":
        statuses.append(registry_doc.status)
    doc = sources.read_runtime_document(
        RUNTIME_WORKTREES_REL,
        LEGACY_RUNTIME_WORKTREES_REL,
        "runtime_worktrees",
        {"schema_version": 1, "revision": 0, "worktrees": []},
    )
    generated_values.append(doc.updated_at)
    if doc.revision is not None:
        refs["runtime_worktrees"] = doc.revision
    if doc.status != "ok" or doc.value is None:
        statuses.append(doc.status)
        _warning_add(warnings, doc.warning)
        return _projection(
            status=_status_join(statuses),
            generated_at=_max_timestamp(generated_values),
            revision_refs=refs,
            data={"worktrees": []},
            warnings=warnings,
        )
    known = {
        item.get("id")
        for item in _registry_direction(registry_doc.value)
        if isinstance(item.get("id"), str)
    } if registry_doc.value else set()
    entries: list[dict[str, Any]] = []
    source = doc.value.get("worktrees", [])
    for item in sorted((entry for entry in source if isinstance(entry, Mapping)), key=lambda entry: str(entry.get("worktree_ref", ""))):
        direction = item.get("direction_id")
        if isinstance(direction, str) and direction not in known:
            statuses.append("stale")
            _warning_add(warnings, f"stale:worktree_direction:{direction}")
        output: dict[str, Any] = {
            key: item[key]
            for key in ("worktree_ref", "direction_id", "kind", "assignment_id", "branch", "base_sha", "candidate_sha", "integrated_sha", "lifecycle", "receipt_path")
            if key in item and (isinstance(item[key], str) or item[key] is None)
        }
        absolute = item.get("canonical_absolute_path")
        if isinstance(absolute, str):
            # A basename is useful in the view without disclosing machine paths.
            output["path_name"] = Path(absolute).name
        entries.append(output)
    if not statuses:
        statuses = ["ok"]
    return _projection(
        status=_status_join(statuses),
        generated_at=_max_timestamp(generated_values),
        revision_refs=refs,
        data={"worktrees": entries},
        warnings=warnings,
    )




def _unstable_snapshot(
    registry_doc: Document | None = None,
    changed_sources: Iterable[str] = (),
) -> dict[str, Any]:
    refs: dict[str, int] = {}
    if registry_doc is not None and registry_doc.revision is not None:
        refs["registry"] = registry_doc.revision
    warnings = ["stale:snapshot_sources_changed"]
    if REGISTRY_REL in changed_sources:
        warnings.append("stale:registry_revision_changed")
    return _projection(
        status="stale",
        generated_at=(registry_doc.updated_at if registry_doc else EPOCH) or EPOCH,
        revision_refs=refs,
        data={},
        warnings=warnings,
    )


def build_snapshot(root: Root | Path | str) -> dict[str, Any]:
    """Build one digest-stable deterministic snapshot, or raise instability."""

    validated = root if isinstance(root, Root) else resolve_root(root)
    root_path = validated.path
    last_registry: Document | None = None
    last_changed: tuple[str, ...] = ()
    for _ in range(MAX_SNAPSHOT_ATTEMPTS):
        sources = _SnapshotAttempt(root_path)
        registry = sources.read_document(
            REGISTRY_REL,
            "portfolio_registry",
            required=True,
        )
        last_registry = registry
        sections = {
            "portfolio": _build_portfolio(root_path, registry, sources),
            "agents": _build_agents(registry, sources),
            "runs": _build_runs(root_path, registry, sources),
            "external_reviews": _build_external(root_path, registry, sources),
            "worktrees": _build_worktrees(registry, sources),
        }
        last_changed = sources.changed_sources()
        if last_changed:
            continue
        all_refs: dict[str, int] = {}
        if registry.revision is not None:
            all_refs["registry"] = registry.revision
        for section in sections.values():
            all_refs.update(section["revision_refs"])
        return _projection(
            status=_status_join(section["status"] for section in sections.values()),
            generated_at=_max_timestamp(section["generated_at"] for section in sections.values()),
            revision_refs=all_refs,
            data=sections,
            warnings=sorted({warning for section in sections.values() for warning in section["warnings"]}),
        )
    raise UnstableSnapshotError(_json_text(_unstable_snapshot(last_registry, last_changed)))


def build_projection(root: Root | Path | str, name: str) -> dict[str, Any]:
    """Return one named API projection using the same coherence boundary."""

    snapshot = build_snapshot(root)
    if name == "snapshot":
        return snapshot
    key = {"portfolio": "portfolio", "agents": "agents", "runs": "runs", "external-reviews": "external_reviews", "worktrees": "worktrees"}.get(name)
    if key is None:
        raise KeyError(name)
    return snapshot["data"][key]


def _health(root: Root) -> dict[str, Any]:
    registry = _read_document(root.path, REGISTRY_REL, "portfolio_registry")
    refs = {"registry": registry.revision} if registry.revision is not None else {}
    status = "ok" if registry.status in {"ok", "missing"} else registry.status
    warnings = [] if registry.status == "ok" else [registry.warning or f"{registry.status}:registry"]
    return _projection(
        status=status,
        generated_at=registry.updated_at or EPOCH,
        revision_refs=refs,
        data={
            "service": "hmasd-dashboard",
            "version": SERVICE_VERSION,
            "read_only": True,
            "bind_host": BIND_HOST,
        },
        warnings=warnings,
    )


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP adapter with an exact route and method allowlist."""

    server_version = "hmasd-dashboard"
    sys_version = ""

    @property
    def dashboard_root(self) -> Root:
        return self.server.dashboard_root  # type: ignore[attr-defined]

    def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, value: Any) -> None:
        self._send_bytes(status, "application/json; charset=utf-8", _json_bytes(value))

    def _send_error_json(self, status: HTTPStatus, code: str) -> None:
        body = _json_bytes({"error": code, "status": int(status)})
        self.send_response(int(status))
        if status == HTTPStatus.METHOD_NOT_ALLOWED:
            self.send_header("Allow", "GET")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib HTTP API
        route = urlsplit(self.path).path
        if route in ASSET_NAMES:
            asset_name, content_type = ASSET_NAMES[route]
            path = self.dashboard_root.asset_dir / asset_name
            # Assets are resolved relative to this script, not the caller's root.
            if not path.is_file() or path.is_symlink():
                self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "asset_unavailable")
                return
            try:
                body = path.read_bytes()
            except OSError:
                self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "asset_unavailable")
                return
            self._send_bytes(HTTPStatus.OK, content_type, body)
            return
        if route not in API_NAMES:
            self._send_error_json(HTTPStatus.NOT_FOUND, "not_found")
            return
        try:
            if route == "/api/health":
                response = _health(self.dashboard_root)
            elif route == "/api/snapshot":
                response = build_projection(self.dashboard_root, "snapshot")
            else:
                response = build_projection(self.dashboard_root, route.removeprefix("/api/"))
        except UnstableSnapshotError as exc:
            try:
                payload = json.loads(str(exc))
            except json.JSONDecodeError:
                payload = _unstable_snapshot()
            self._send_json(HTTPStatus.CONFLICT, payload)
            return
        except DashboardError:
            self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "dashboard_failure")
            return
        self._send_json(HTTPStatus.OK, response)

    def _read_only_method(self) -> None:
        self._send_error_json(HTTPStatus.METHOD_NOT_ALLOWED, "read_only")

    def do_POST(self) -> None:  # noqa: N802
        self._read_only_method()

    def do_PUT(self) -> None:  # noqa: N802
        self._read_only_method()

    def do_PATCH(self) -> None:  # noqa: N802
        self._read_only_method()

    def do_DELETE(self) -> None:  # noqa: N802
        self._read_only_method()

    def do_HEAD(self) -> None:  # noqa: N802
        self._read_only_method()

    def log_message(self, format: str, *args: Any) -> None:
        # Keep service diagnostics compact and free of response data.
        sys.stderr.write("hmasd-dashboard: " + (format % args) + "\n")


class DashboardServer(ThreadingHTTPServer):
    """Threaded loopback-only server carrying a validated root."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, root: Root, port: int) -> None:
        super().__init__((BIND_HOST, port), DashboardRequestHandler)
        self.dashboard_root = root


def serve(root: Root | Path | str, port: int) -> None:
    validated = root if isinstance(root, Root) else resolve_root(root)
    if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
        raise DashboardError("port must be between 0 and 65535")
    server = DashboardServer(validated, port)
    print(f"HMASD dashboard listening on http://{BIND_HOST}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only HMASD local dashboard")
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve_parser = subparsers.add_parser("serve", help="serve the dashboard")
    serve_parser.add_argument("--root", required=True)
    serve_parser.add_argument("--port", required=True, type=int)
    snapshot_parser = subparsers.add_parser("snapshot", help="print one deterministic snapshot")
    snapshot_parser.add_argument("--root", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = resolve_root(args.root)
        if args.command == "snapshot":
            try:
                snapshot = build_projection(root, "snapshot")
            except UnstableSnapshotError as exc:
                try:
                    snapshot = json.loads(str(exc))
                except json.JSONDecodeError:
                    snapshot = _unstable_snapshot()
                _write_json_stdout(snapshot)
                return 4
            _write_json_stdout(snapshot)
            if snapshot.get("status") == "invalid":
                return 2
            return 0
        serve(root, args.port)
        return 0
    except InvalidRootError as exc:
        print(f"hmasd-dashboard: {exc}", file=sys.stderr)
        return 2
    except DashboardError as exc:
        print(f"hmasd-dashboard: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
