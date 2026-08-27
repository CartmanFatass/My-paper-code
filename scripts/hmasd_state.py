"""Validation and atomic persistence for HMASD Phase 0 state contracts.

The module deliberately stays small and standard-library-only. JSON schemas are
loaded from ``scripts/schemas`` and provide the structural contract; the
cross-record invariants below provide the relationships that JSON Schema cannot
express (writer ownership, path ownership, the registry DAG, revision CAS, and
foreign archive byte integrity).
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as _datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any, Callable, Iterator, Mapping, NoReturn

try:
    from scripts import hmasd_platform
except ImportError:
    import hmasd_platform


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
SUPPORTED_SCHEMA_VERSION = 1

KIND_ALIASES = {
    "portfolio_registry": "portfolio_registry",
    "research_state": "research_state",
    "engineering_state": "engineering_state",
    "external_review_index": "external_review_index",
    "run_manifest": "run_manifest",
    "accepted_result": "accepted_result",
    "external_archive": "external_archive",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
DIRECTION_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?Z$"
)
PATH_RE = re.compile(
    r"^(?!/)(?![A-Za-z]:)(?!.*\\)(?!.*[\x00-\x1f\x7f-\x9f])(?!.*:)"
    r"(?!\.{1,2}(?:/|$))(?!.*//)(?!.*(?:^|/)\.{1,2}(?:/|$))"
    r"(?![^/]*[. ](?:/|$))(?!.*\/[^/]*[. ](?:/|$))[^/]+(?:/[^/]+)*$"
)
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SECRET_NAME_RE = re.compile(r"(?:secret|token|password|credential|private[_-]?key)", re.I)
PORTFOLIO_DECISION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")


class StateError(Exception):
    """Base error carrying the documented helper exit code."""

    exit_code = 1


class ValidationError(StateError):
    exit_code = 2


class UnsupportedVersionError(StateError):
    exit_code = 3


class RevisionConflictError(StateError):
    exit_code = 4


class OwnershipError(StateError):
    exit_code = 5


class ObservedConflictError(StateError):
    exit_code = 6


class _SchemaFailure(Exception):
    pass


# Public registry for one-way migrations. A migration must register N -> N+1;
# no downgrade or implicit rewrite is ever performed.
Migration = Callable[[dict[str, Any]], dict[str, Any]]
MIGRATIONS: dict[str, dict[int, Migration]] = {kind: {} for kind in KIND_ALIASES}


def normalize_kind(kind: str) -> str:
    value = kind.strip()
    if value.endswith(".schema.json"):
        value = value[: -len(".schema.json")]
    if value.startswith("hmasd_"):
        value = value[len("hmasd_") :]
    try:
        return KIND_ALIASES[value]
    except KeyError as exc:
        raise ValidationError(f"unknown state kind: {kind}") from exc


def schema_path(kind: str) -> Path:
    normalized = normalize_kind(kind)
    return SCHEMA_DIR / f"hmasd_{normalized}.schema.json"


def load_schema(kind: str) -> dict[str, Any]:
    path = schema_path(kind)
    try:
        with path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot load schema {path}: {exc}") from exc
    if not isinstance(schema, dict):
        raise ValidationError(f"schema is not an object: {path}")
    return schema


def _resolve_ref(ref: str, root: Mapping[str, Any]) -> Mapping[str, Any]:
    if not ref.startswith("#/"):
        raise _SchemaFailure(f"unsupported schema reference {ref}")
    value: Any = root
    for component in ref[2:].split("/"):
        value = value[component.replace("~1", "/").replace("~0", "~")]
    if not isinstance(value, Mapping):
        raise _SchemaFailure(f"schema reference is not an object: {ref}")
    return value


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _validate_schema(value: Any, schema: Mapping[str, Any], root: Mapping[str, Any], path: str) -> None:
    if "$ref" in schema:
        _validate_schema(value, _resolve_ref(str(schema["$ref"]), root), root, path)
        return

    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            matches = 0
            failures: list[str] = []
            for option in schema[keyword]:
                try:
                    _validate_schema(value, option, root, path)
                    matches += 1
                except _SchemaFailure as exc:
                    failures.append(str(exc))
            required = 1 if keyword == "anyOf" else 1
            if (keyword == "anyOf" and matches < required) or (
                keyword == "oneOf" and matches != 1
            ):
                raise _SchemaFailure(f"{path}: {keyword} failed ({'; '.join(failures)})")
            return

    if "const" in schema and value != schema["const"]:
        raise _SchemaFailure(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise _SchemaFailure(f"{path}: expected one of {schema['enum']!r}")

    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_json_type_matches(value, str(item)) for item in expected_types):
            raise _SchemaFailure(f"{path}: expected type {expected_type!r}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            raise _SchemaFailure(f"{path}: shorter than minLength")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            raise _SchemaFailure(f"{path}: longer than maxLength")
        if "pattern" in schema and re.search(str(schema["pattern"]), value) is None:
            raise _SchemaFailure(f"{path}: does not match pattern")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise _SchemaFailure(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise _SchemaFailure(f"{path}: above maximum")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise _SchemaFailure(f"{path}: below exclusiveMinimum")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            raise _SchemaFailure(f"{path}: above exclusiveMaximum")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            raise _SchemaFailure(f"{path}: fewer than minItems")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            raise _SchemaFailure(f"{path}: more than maxItems")
        if "items" in schema:
            for index, item in enumerate(value):
                _validate_schema(item, schema["items"], root, f"{path}[{index}]")

    if isinstance(value, dict):
        if "minProperties" in schema and len(value) < int(schema["minProperties"]):
            raise _SchemaFailure(f"{path}: fewer than minProperties")
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise _SchemaFailure(f"{path}: missing required key {key!r}")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                _validate_schema(item, properties[key], root, f"{path}.{key}")
            elif additional is False:
                raise _SchemaFailure(f"{path}: unknown key {key!r}")
            elif isinstance(additional, Mapping):
                _validate_schema(item, additional, root, f"{path}.{key}")


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_bytes(document: Mapping[str, Any]) -> bytes:
    """Return the durable two-space/sorted/newline-terminated representation."""

    return _canonical_bytes(document)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | os.PathLike[str]) -> str:
    with Path(path).open("rb") as handle:
        digest = hashlib.sha256()
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_timestamp(value: Any, name: str) -> None:
    if not isinstance(value, str) or TIMESTAMP_RE.fullmatch(value) is None:
        raise ValidationError(f"{name} is not a UTC RFC3339 timestamp with Z")
    try:
        # Codex's native host may emit seven fractional digits while Python's
        # datetime parser accepts at most six.  Validation still checks the
        # complete lexical timestamp; truncation is only for calendar parsing.
        parse_value = value[:-1]
        if "." in parse_value:
            whole, fraction = parse_value.split(".", 1)
            parse_value = f"{whole}.{fraction[:6]}"
        _datetime.datetime.fromisoformat(parse_value)
    except ValueError as exc:
        raise ValidationError(f"{name} is not a valid timestamp") from exc


def _ensure_path(value: Any, name: str, *, absolute: bool = False) -> None:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a path string")
    if absolute:
        if not (value.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", value)):
            raise ValidationError(f"{name} must be absolute")
        if "\x00" in value:
            raise ValidationError(f"{name} contains NUL")
        return
    if PATH_RE.fullmatch(value) is None:
        raise ValidationError(f"{name} is not a repository-relative POSIX path")


def _ensure_sha(value: Any, name: str, *, git: bool = False) -> None:
    expression = GIT_SHA_RE if git else SHA256_RE
    if not isinstance(value, str) or expression.fullmatch(value) is None:
        raise ValidationError(f"{name} is not a lowercase SHA value")


def _ref_path(ref: Any, name: str) -> str | None:
    if ref is None:
        return None
    if isinstance(ref, str):
        return ref
    if isinstance(ref, dict):
        path = ref.get("path")
        if isinstance(path, str):
            return path
    raise ValidationError(f"{name} is not a reference")


def _owner_error(message: str) -> OwnershipError:
    return OwnershipError(message)


def _is_alias(path: Path) -> bool:
    """Return whether *path* is a symlink or native reparse-point alias.

    ``Path.is_symlink()`` does not identify Windows junctions and other
    reparse points.  State paths are authority boundaries, so using the host
    adapter here keeps native Windows checks equivalent to the POSIX checks.
    """

    return hmasd_platform.is_reparse_or_symlink(path)


def _immutable_conflict(name: str) -> NoReturn:
    raise ObservedConflictError(f"{name} is immutable across replacement")


def _require_unchanged(current: Any, next_value: Any, name: str) -> None:
    if current != next_value:
        _immutable_conflict(name)


def _require_append_only(current: Any, next_value: Any, name: str) -> None:
    if current is not None and current != next_value:
        _immutable_conflict(name)


def _require_unchanged_fields(
    current: Mapping[str, Any],
    next_document: Mapping[str, Any],
    fields: tuple[str, ...],
    label: str,
) -> None:
    for field in fields:
        _require_unchanged(current[field], next_document[field], f"{label}.{field}")


def _matching_records(
    current_records: list[Mapping[str, Any]],
    next_records: list[Mapping[str, Any]],
    *,
    key: str,
    label: str,
) -> Iterator[tuple[Any, Mapping[str, Any], Mapping[str, Any]]]:
    next_by_key = {record[key]: record for record in next_records}
    for current in current_records:
        record_key = current[key]
        next_document = next_by_key.get(record_key)
        if next_document is None:
            _immutable_conflict(f"{label}[{record_key!r}]")
        yield record_key, current, next_document


def _validate_registry(document: Mapping[str, Any]) -> None:
    if document["writer"] != "Portfolio":
        raise _owner_error("portfolio registry writer must be Portfolio")
    goal = document["goal"]
    if goal["path"] != "docs/research/portfolio/PORTFOLIO.md":
        raise _owner_error("registry goal path must be PORTFOLIO.md")
    ids: set[str] = set()
    abbreviations: set[str] = set()
    paths: set[str] = set()
    logical: set[str] = set()
    jobs: set[str] = set()
    state_paths: set[str] = set()
    directions = document["directions"]
    for index, direction in enumerate(directions):
        prefix = f"directions[{index}]"
        direction_id = direction["id"]
        if direction_id in ids:
            raise ValidationError(f"duplicate direction id: {direction_id}")
        ids.add(direction_id)
        for key, seen in (
            ("abbreviation", abbreviations),
            ("path", paths),
            ("agent.logical_identity", logical),
            ("agent.job_name", jobs),
        ):
            current: Any = direction
            for part in key.split("."):
                current = current[part]
            if current in seen:
                raise ValidationError(f"duplicate {key}: {current}")
            seen.add(current)
        expected_dir = f"docs/research/candidates/{direction_id}"
        if direction["path"] != expected_dir:
            raise _owner_error(f"{prefix}.path is not owned by {direction_id}")
        expected_identity = f"EM-{direction_id}"
        if direction["agent"]["logical_identity"] != expected_identity:
            raise _owner_error(f"{prefix}.agent.logical_identity mismatch")
        expected_paths = {
            "research_state_path": f"{expected_dir}/workflow/research/state.json",
            "engineering_state_path": f"{expected_dir}/workflow/engineering/state.json",
            "external_review_index_path": f"{expected_dir}/workflow/external-review/index.json",
        }
        for key, expected in expected_paths.items():
            actual = direction[key]
            if actual != expected:
                raise _owner_error(f"{prefix}.{key} is not owned by {direction_id}")
            if actual in state_paths:
                raise ValidationError(f"duplicate state path: {actual}")
            state_paths.add(actual)
        decision_path = direction["lifecycle_decision_ref"]["path"]
        if not (
            decision_path == "docs/research/portfolio/PORTFOLIO.md"
            or (
                decision_path.startswith("docs/research/portfolio/decisions/")
                and decision_path.endswith(".json")
            )
        ):
            raise _owner_error(f"{prefix}.lifecycle_decision_ref path is not Portfolio-owned")
        condition = direction["reactivation_condition_ref"]
        if condition is not None:
            condition_path = condition["path"]
            if not (
                condition_path == "docs/research/portfolio/PORTFOLIO.md"
                or (
                    condition_path.startswith("docs/research/portfolio/decisions/")
                    and condition_path.endswith(".json")
                )
            ):
                raise _owner_error(f"{prefix}.reactivation_condition_ref path is not Portfolio-owned")
        for dependency in direction["dependencies"]:
            if dependency not in ids and dependency not in {item["id"] for item in directions}:
                raise ValidationError(f"unknown dependency {dependency}")
        if direction["lifecycle"] == "ACTIVE":
            # Counted after structural validation; no minimum is imposed.
            pass
    if sum(item["lifecycle"] == "ACTIVE" for item in directions) > 8:
        raise ValidationError("portfolio registry permits at most eight ACTIVE directions")
    graph = {item["id"]: set(item["dependencies"]) for item in directions}
    for node, dependencies in graph.items():
        if node in dependencies:
            raise ValidationError(f"direction dependency cycle at {node}")
        missing = dependencies - graph.keys()
        if missing:
            raise ValidationError(f"unknown dependencies for {node}: {sorted(missing)}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ValidationError(f"direction dependency cycle at {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def _reconcile_research_direction_ref(
    document: Mapping[str, Any], *, allow_stale_sha: bool = False
) -> None:
    """Check a research ref against the on-disk registry when available."""

    registry_path = ROOT / "docs" / "research" / "portfolio" / "workflow" / "registry.json"
    if not registry_path.is_file() or _is_alias(registry_path):
        return
    try:
        _, registry = _read_document(registry_path)
    except StateError:
        return
    if not isinstance(registry, dict):
        return
    registered = next(
        (
            item
            for item in registry.get("directions", [])
            if isinstance(item, dict) and item.get("id") == document["direction_id"]
        ),
        None,
    )
    if registered is None:
        return
    registered_path = registered.get("path")
    if not isinstance(registered_path, str):
        raise ValidationError("registry direction path is missing")
    _ensure_path(registered_path, "registry direction path")
    expected_path = f"{registered_path}/DIRECTION.md"
    reference = document["direction_ref"]
    if reference["path"] != expected_path:
        raise ValidationError("research direction_ref path is stale against registry")
    target = ROOT / Path(expected_path)
    if not target.is_file() or _is_alias(target):
        raise ValidationError("research direction_ref target is missing or symlinked")
    if sha256_file(target) != reference["sha256"] and not allow_stale_sha:
        raise ValidationError("research direction_ref SHA does not match exact file bytes")


def _validate_direction_state(
    document: Mapping[str, Any],
    kind: str,
    *,
    allow_stale_research_direction_sha: bool = False,
) -> str:
    direction_id = document["direction_id"]
    expected_prefix = "EM-" if kind in {"research_state", "external_review_index"} else "CM-"
    expected_writer = expected_prefix + direction_id
    if document["writer"] != expected_writer:
        raise _owner_error(f"{kind} writer must be {expected_writer}")
    expected_direction_path = f"docs/research/candidates/{direction_id}/DIRECTION.md"
    if kind == "research_state":
        if document["direction_ref"]["path"] != expected_direction_path:
            raise _owner_error("research direction_ref path is not direction-owned")
        _reconcile_research_direction_ref(
            document, allow_stale_sha=allow_stale_research_direction_sha
        )
    elif kind == "engineering_state":
        if document["scope_ref"]["path"] != expected_direction_path:
            raise _owner_error("engineering scope_ref path is not direction-owned")
    return direction_id


def _validate_external_index(document: Mapping[str, Any]) -> None:
    direction_id = _validate_direction_state(document, "external_review_index")
    workflow_version = document["workflow_version"]
    seen: set[str] = set()
    for index, round_document in enumerate(document["rounds"]):
        round_id = round_document["round_id"]
        if round_id in seen:
            raise ValidationError(f"duplicate external round id: {round_id}")
        seen.add(round_id)
        expected = sha256_bytes(
            (direction_id + "\n" + round_document["question_sha256"] + "\n" + round_document["evidence_set_sha256"] + "\n" + workflow_version).encode("utf-8")
        )[:20]
        if round_id != expected:
            raise ValidationError(f"rounds[{index}].round_id does not match frozen inputs")
        base = f"docs/external-review/directions/{direction_id}/"
        for key, ref in round_document["prompt_refs"].items():
            if ref is not None and not ref["path"].startswith(base):
                raise _owner_error(f"prompt_refs.{key} is outside the direction archive")
        for provider in round_document["providers"].values():
            if provider is None:
                continue
            for forbidden in ("sendCount", "send_count", "sendActionCount", "commitment"):
                if forbidden in provider:
                    raise ValidationError(f"provider result contains forbidden ledger field {forbidden}")


def _validate_run_manifest(document: Mapping[str, Any]) -> None:
    if document["writer"] != document["operator_identity"]:
        raise _owner_error("run manifest writer must equal operator_identity")
    command_bytes = b"\0".join(item.encode("utf-8") for item in document["command"])
    if document["command_sha256"] != sha256_bytes(command_bytes):
        raise ValidationError("command_sha256 does not match NUL-delimited argv")
    for key in document["environment"]["captured_variables"]:
        if SECRET_NAME_RE.search(key):
            raise ValidationError(f"captured variable name is secret-like: {key}")
    for key in ("stdout", "stderr", "checkpoints", "metrics", "artifacts"):
        _ensure_path(document["outputs"][key], f"outputs.{key}")
    _ensure_path(document["resources"]["preflight_ref"], "resources.preflight_ref")
    if document["status"] == "RUNNING":
        process = document["process"]
        if process["pid"] is not None and process["linux_boot_id"] is None:
            raise ValidationError("RUNNING manifest requires linux_boot_id")


def _validate_accepted_result(document: Mapping[str, Any]) -> None:
    direction_id = document["direction_id"]
    expected_writer = f"EM-{direction_id}"
    if document["writer"] != expected_writer or document["promoted_by"] != expected_writer:
        raise _owner_error("accepted result writer/promoted_by must be its EM")
    expected_conclusion = f"docs/research/candidates/{direction_id}/results/{document['result_id']}.md"
    if document["conclusion_path"] != expected_conclusion:
        raise _owner_error("accepted conclusion path is not direction-owned")
    expected_manifest = f"temp/directions/{direction_id}/exp/{document['source_run']['run_id']}/manifest.json"
    if document["source_run"]["manifest_path"] != expected_manifest:
        raise _owner_error("accepted source manifest path is not direction-owned")


def _validate_archive(document: Mapping[str, Any]) -> None:
    if document["terminalState"] != "NATURAL_COMPLETION_VERIFIED":
        raise ValidationError("archive is not a natural completion")
    if document["sendCount"] > 1 or document["sendActionCount"] > 1:
        raise ValidationError("archive exceeds Agentify at-most-once counts")
    expected = sha256_bytes(document["responseText"].encode("utf-8"))
    if document["responseSha256"] != expected:
        raise ValidationError("archive responseSha256 does not match responseText UTF-8 bytes")


def _validate_custom(
    kind: str,
    document: Mapping[str, Any],
    *,
    allow_stale_research_direction_sha: bool = False,
) -> None:
    if kind == "portfolio_registry":
        _validate_registry(document)
    elif kind in {"research_state", "engineering_state"}:
        _validate_direction_state(
            document,
            kind,
            allow_stale_research_direction_sha=allow_stale_research_direction_sha,
        )
    elif kind == "external_review_index":
        _validate_external_index(document)
    elif kind == "run_manifest":
        _validate_run_manifest(document)
    elif kind == "accepted_result":
        _validate_accepted_result(document)
    elif kind == "external_archive":
        _validate_archive(document)


def _precheck_writer_ownership(kind: str, document: Mapping[str, Any]) -> None:
    """Classify ownership failures before structural schema failures."""

    if kind == "portfolio_registry" and "writer" in document:
        if document["writer"] != "Portfolio":
            raise _owner_error("portfolio registry writer must be Portfolio")
    elif kind in {"research_state", "external_review_index"}:
        direction_id = document.get("direction_id")
        if isinstance(direction_id, str) and "writer" in document:
            expected = f"EM-{direction_id}"
            if document["writer"] != expected:
                raise _owner_error(f"{kind} writer must be {expected}")
    elif kind == "engineering_state":
        direction_id = document.get("direction_id")
        if isinstance(direction_id, str) and "writer" in document:
            expected = f"CM-{direction_id}"
            if document["writer"] != expected:
                raise _owner_error(f"engineering_state writer must be {expected}")
    elif kind == "run_manifest":
        operator = document.get("operator_identity")
        if isinstance(operator, str) and "writer" in document and document["writer"] != operator:
            raise _owner_error("run manifest writer must equal operator_identity")
    elif kind == "accepted_result":
        direction_id = document.get("direction_id")
        if isinstance(direction_id, str) and "writer" in document:
            expected = f"EM-{direction_id}"
            if document["writer"] != expected:
                raise _owner_error(f"accepted_result writer must be {expected}")


def _reject_symlink_components(value: str, name: str) -> None:
    """Reject an existing symlink anywhere in a repository-relative path."""

    candidate = ROOT
    for component in value.split("/"):
        if component in {"", "."}:
            continue
        candidate /= component
        if _is_alias(candidate):
            raise _owner_error(f"{name} traverses symlink or reparse component {candidate}")


def _check_document_paths(value: Any, prefix: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}"
            if key == "path" and isinstance(item, str) and PATH_RE.fullmatch(item):
                _reject_symlink_components(item, child)
            else:
                _check_document_paths(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_document_paths(item, f"{prefix}[{index}]")


def validate_document(
    kind: str,
    document: Mapping[str, Any],
    *,
    writer: str | None = None,
    allow_stale_research_direction_sha: bool = False,
) -> dict[str, Any]:
    """Validate and return a JSON object without mutating it."""

    normalized = normalize_kind(kind)
    if not isinstance(document, dict):
        raise ValidationError("state document must be a JSON object")
    if normalized == "external_archive":
        if any(key in document for key in ("schema_version", "revision", "writer")):
            raise ValidationError("foreign Agentify archive cannot contain HMASD metadata")
    else:
        version = document.get("schema_version")
        if isinstance(version, int) and not isinstance(version, bool) and version > SUPPORTED_SCHEMA_VERSION:
            raise UnsupportedVersionError(f"unsupported schema version {version}")
        _precheck_writer_ownership(normalized, document)
    schema = load_schema(normalized)
    try:
        _validate_schema(document, schema, schema, "$")
    except _SchemaFailure as exc:
        raise ValidationError(str(exc)) from exc
    _check_document_paths(document)
    if normalized != "external_archive":
        _ensure_timestamp(document["updated_at"], "updated_at")
        if writer is not None and document["writer"] != writer:
            raise _owner_error(f"writer {document['writer']!r} does not match requested writer {writer!r}")
    _validate_custom(
        normalized,
        document,
        allow_stale_research_direction_sha=allow_stale_research_direction_sha,
    )
    return document


# Aliases kept intentionally boring for callers that use verb-oriented names.
validate_state = validate_document
validate = validate_document


def _read_document(path: Path) -> tuple[bytes, dict[str, Any]]:
    if _is_alias(path):
        raise OwnershipError(f"refusing symlink or reparse state path: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise StateError(f"cannot read state path {path}: {exc}") from exc
    try:
        text = raw.decode("utf-8")
        document = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid UTF-8 JSON at {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise ValidationError(f"state path {path} does not contain an object")
    return raw, document


def read_state(kind: str, path: str | os.PathLike[str]) -> dict[str, Any]:
    target = Path(path)
    _, document = _read_document(target)
    return validate_document(kind, document)


def read(kind: str, path: str | os.PathLike[str]) -> dict[str, Any]:
    return read_state(kind, path)


def _input_document(value: Mapping[str, Any] | str | os.PathLike[str]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        result = copy.deepcopy(dict(value))
        if not isinstance(result, dict):
            raise ValidationError("input document must be an object")
        return result
    candidate = Path(value)
    if candidate.exists():
        _, result = _read_document(candidate)
        return result
    try:
        result = json.loads(str(value))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"input is neither a JSON path nor JSON object: {exc}") from exc
    if not isinstance(result, dict):
        raise ValidationError("input document must be an object")
    return result
def _input_document_and_bytes(
    value: Mapping[str, Any] | str | os.PathLike[str],
) -> tuple[dict[str, Any], bytes | None]:
    """Load input and retain original bytes when the caller supplied a file."""

    if isinstance(value, Mapping):
        return _input_document(value), None
    try:
        candidate = Path(value)
    except (OSError, TypeError):
        candidate = None
    if candidate is not None and candidate.exists():
        raw, document = _read_document(candidate)
        return document, raw
    return _input_document(value), None


def _lock_path(path: Path) -> Path:
    # Callers may spell one state path as ``docs/...`` and another time as a
    # native absolute path.  Hash a lexical, host-normalized absolute path so
    # both spellings share one lock.  ``abspath`` intentionally does not
    # resolve symlinks/reparse points; those are rejected by the authority
    # checks after the lock is acquired.
    lock_key = os.path.normcase(os.path.abspath(os.fspath(path)))
    digest = sha256_bytes(os.fsencode(lock_key))
    return ROOT / ".codex" / "runtime" / "locks" / f"{digest}.lock"


@contextlib.contextmanager
def state_lock(path: str | os.PathLike[str]) -> Iterator[None]:
    lock_path = _lock_path(Path(path))
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock_path.open("a+b") as handle:
            with hmasd_platform.exclusive_file_lock(handle.fileno()):
                yield
    except OSError as exc:
        raise StateError(f"cannot acquire state lock {lock_path}: {exc}") from exc


def _fsync_parent(path: Path) -> None:
    hmasd_platform.fsync_directory(path)


def atomic_write(path: str | os.PathLike[str], data: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if _is_alias(target):
        raise OwnershipError(f"refusing symlink or reparse state path: {target}")
    mode = 0o666
    try:
        mode = target.stat().st_mode & 0o777
    except FileNotFoundError:
        pass
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    temp_path = Path(temp_name)
    try:
        hmasd_platform.apply_fd_mode(fd, mode)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise StateError("short write while persisting state")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(temp_path, target)
        _fsync_parent(target.parent)
    except Exception:
        if fd >= 0:
            os.close(fd)
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()
        raise
def _initialize_unlocked(
    kind: str,
    target: Path,
    writer: str,
    document: dict[str, Any],
    input_bytes: bytes | None = None,
) -> dict[str, Any]:
    validate_document(kind, document, writer=writer)
    target.parent.mkdir(parents=True, exist_ok=True)
    if _is_alias(target):
        raise OwnershipError(f"refusing symlink or reparse state path: {target}")
    data = _canonical_bytes(document) if input_bytes is None else input_bytes
    # Stage the complete bytes in the same directory, then publish with a
    # hard-link create.  ``mkstemp`` supplies O_CREAT|O_EXCL and the final
    # link is also create-only, so a crash cannot expose a partial target.
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".init", dir=str(target.parent)
    )
    temp_path = Path(temp_name)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise StateError("short initialize write")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        try:
            os.link(temp_path, target)
        except FileExistsError as exc:
            raise RevisionConflictError(f"initialize refuses existing path: {target}") from exc
        _fsync_parent(target.parent)
    except OSError as exc:
        if isinstance(exc, RevisionConflictError):
            raise
        raise StateError(f"cannot initialize {target}: {exc}") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()
    return document


def initialize(
    kind: str,
    path: str | os.PathLike[str],
    writer: str,
    input: Mapping[str, Any] | str | os.PathLike[str],
) -> dict[str, Any]:
    target = Path(path)
    document, input_bytes = _input_document_and_bytes(input)
    with state_lock(target):
        return _initialize_unlocked(kind, target, writer, document, input_bytes)


def replace(
    kind: str,
    path: str | os.PathLike[str],
    writer: str,
    expected_revision: int,
    input: Mapping[str, Any] | str | os.PathLike[str],
) -> dict[str, Any]:
    normalized = normalize_kind(kind)
    if normalized == "external_archive":
        raise ObservedConflictError(f"{normalized} is an immutable record")
    target = Path(path)
    document = _input_document(input)
    validate_document(normalized, document, writer=writer)
    if not isinstance(expected_revision, int) or isinstance(expected_revision, bool) or expected_revision < 1:
        raise RevisionConflictError("expected_revision must be a positive integer")
    with state_lock(target):
        current_bytes, current = _read_document(target)
        validate_document(
            normalized,
            current,
            writer=writer,
            allow_stale_research_direction_sha=normalized == "research_state",
        )
        current_revision = current["revision"]
        if current_revision != expected_revision:
            raise RevisionConflictError(
                f"expected revision {expected_revision}, observed {current_revision}"
            )
        if document["revision"] != current_revision + 1:
            raise RevisionConflictError("replacement revision must increment exactly once")
        _validate_transition(normalized, current, document)
        validate_document(normalized, document, writer=writer)
        next_bytes = _canonical_bytes(document)
        if next_bytes == current_bytes:
            raise RevisionConflictError("replacement must change the revision/document")
        atomic_write(target, next_bytes)
    return document


def _validate_portfolio_registry_transition(
    current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    _require_unchanged(
        current["workflow_version"],
        next_document["workflow_version"],
        "portfolio registry workflow_version",
    )
    _require_unchanged(
        current["goal"]["path"],
        next_document["goal"]["path"],
        "portfolio registry goal.path",
    )
    for direction_id, current_direction, next_direction in _matching_records(
        current["directions"],
        next_document["directions"],
        key="id",
        label="portfolio direction",
    ):
        label = f"portfolio direction {direction_id!r}"
        _require_unchanged_fields(
            current_direction,
            next_direction,
            (
                "path",
                "research_state_path",
                "engineering_state_path",
                "external_review_index_path",
            ),
            label,
        )
        _require_unchanged(
            current_direction["agent"]["logical_identity"],
            next_direction["agent"]["logical_identity"],
            f"{label}.agent.logical_identity",
        )
        _require_unchanged(
            current_direction["agent"]["job_name"],
            next_direction["agent"]["job_name"],
            f"{label}.agent.job_name",
        )


def _validate_direction_state_transition(
    kind: str, current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    _require_unchanged_fields(current, next_document, ("direction_id", "writer"), kind)
    reference_key = "direction_ref" if kind == "research_state" else "scope_ref"
    _require_unchanged(
        current[reference_key]["path"],
        next_document[reference_key]["path"],
        f"{kind}.{reference_key}.path",
    )


def _validate_external_index_transition(
    current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    _require_unchanged_fields(
        current,
        next_document,
        ("direction_id", "writer", "workflow_version"),
        "external review index",
    )
    for round_id, current_round, next_round in _matching_records(
        current["rounds"],
        next_document["rounds"],
        key="round_id",
        label="external review round",
    ):
        label = f"external review round {round_id!r}"
        _require_unchanged_fields(
            current_round,
            next_round,
            ("question_sha256", "evidence_set_sha256", "prompt_refs", "created_at"),
            label,
        )
        _require_append_only(
            current_round["local_synthesis_ref"],
            next_round["local_synthesis_ref"],
            f"{label}.local_synthesis_ref",
        )
        _require_append_only(
            current_round["completed_at"],
            next_round["completed_at"],
            f"{label}.completed_at",
        )
        if current_round["status"] in {"COMPLETE", "BLOCKED"}:
            _require_unchanged(
                current_round["status"],
                next_round["status"],
                f"{label}.status",
            )
        for provider_name, current_provider in current_round["providers"].items():
            next_provider = next_round["providers"][provider_name]
            if current_provider is None:
                continue
            provider_label = f"{label}.providers.{provider_name}"
            if next_provider is None:
                _immutable_conflict(provider_label)
            _require_unchanged_fields(
                current_provider,
                next_provider,
                ("operation_id", "idempotency_key", "session_ref"),
                provider_label,
            )
            _require_append_only(
                current_provider["archive_ref"],
                next_provider["archive_ref"],
                f"{provider_label}.archive_ref",
            )
            _require_append_only(
                current_provider["handoff_ref"],
                next_provider["handoff_ref"],
                f"{provider_label}.handoff_ref",
            )
            _require_append_only(
                current_provider["completed_at"],
                next_provider["completed_at"],
                f"{provider_label}.completed_at",
            )
            if current_provider["completed_at"] is not None:
                _require_unchanged(
                    current_provider["terminal_state"],
                    next_provider["terminal_state"],
                    f"{provider_label}.terminal_state",
                )


def _validate_run_process_transition(
    current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    current_process = current["process"]
    next_process = next_document["process"]
    if current["status"] in {"SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"}:
        _require_unchanged(
            current_process,
            next_process,
            "terminal run process provenance",
        )
        return
    for field, current_value in current_process.items():
        next_value = next_process[field]
        if field == "group_quiescent":
            if current_value is True:
                _require_unchanged(
                    current_value,
                    next_value,
                    "run process.group_quiescent",
                )
            elif current_value is False and next_value not in (False, True):
                _immutable_conflict("run process.group_quiescent")
            continue
        _require_append_only(
            current_value,
            next_value,
            f"run process.{field}",
        )


def _validate_run_manifest_transition(
    current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    mutable_fields = {
        "revision",
        "updated_at",
        "status",
        "process",
        "resources",
        "observed_metrics",
    }
    for field, current_value in current.items():
        if field not in mutable_fields:
            _require_unchanged(current_value, next_document[field], f"run manifest.{field}")
    for field, current_value in current["resources"].items():
        if field != "memory_safe":
            _require_unchanged(
                current_value,
                next_document["resources"][field],
                f"run manifest.resources.{field}",
            )
    if (
        current["resources"]["memory_safe"] is False
        and next_document["resources"]["memory_safe"] is not False
    ):
        _immutable_conflict("run manifest.resources.memory_safe")

    old = current["status"]
    new = next_document["status"]
    allowed = {
        "PREPARED": {"PREPARED", "RUNNING"},
        "RUNNING": {"RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "UNKNOWN"},
        "SUCCEEDED": {"SUCCEEDED"},
        "FAILED": {"FAILED"},
        "CANCELLED": {"CANCELLED"},
        "UNKNOWN": {"UNKNOWN"},
    }
    if new not in allowed[old]:
        raise ObservedConflictError(f"illegal run status transition {old} -> {new}")
    _validate_run_process_transition(current, next_document)


def _validate_accepted_result_transition(
    current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    _require_unchanged_fields(
        current,
        next_document,
        (
            "writer",
            "result_id",
            "direction_id",
            "conclusion_path",
            "source_run",
            "promoted_at",
            "promoted_by",
        ),
        "accepted result",
    )


def _validate_transition(kind: str, current: Mapping[str, Any], next_document: Mapping[str, Any]) -> None:
    if kind == "portfolio_registry":
        _validate_portfolio_registry_transition(current, next_document)
    elif kind in {"research_state", "engineering_state"}:
        _validate_direction_state_transition(kind, current, next_document)
    elif kind == "external_review_index":
        _validate_external_index_transition(current, next_document)
    elif kind == "run_manifest":
        _validate_run_manifest_transition(current, next_document)
    elif kind == "accepted_result":
        _validate_accepted_result_transition(current, next_document)


def register_migration(kind: str, from_version: int, function: Migration) -> None:
    normalized = normalize_kind(kind)
    if not isinstance(from_version, int) or from_version < 1:
        raise ValueError("migration source version must be positive")
    if not callable(function):
        raise TypeError("migration must be callable")
    MIGRATIONS.setdefault(normalized, {})[from_version] = function


def migrate(
    kind: str,
    path: str | os.PathLike[str],
    writer: str,
    expected_revision: int,
    to_version: int,
) -> dict[str, Any]:
    normalized = normalize_kind(kind)
    if normalized == "external_archive":
        raise ObservedConflictError(f"{normalized} is an immutable record")
    target = Path(path)
    with state_lock(target):
        current_bytes, current = _read_document(target)
        validate_document(normalized, current, writer=writer)
        if current["revision"] != expected_revision:
            raise RevisionConflictError(
                f"expected revision {expected_revision}, observed {current['revision']}"
            )
        current_version = current["schema_version"]
        if to_version <= current_version:
            raise UnsupportedVersionError("migrations are one-way and cannot downgrade")
        transformed = copy.deepcopy(current)
        version = current_version
        while version < to_version:
            function = MIGRATIONS.get(normalized, {}).get(version)
            if function is None:
                raise UnsupportedVersionError(f"no migration registered for {normalized} {version} -> {version + 1}")
            transformed = function(copy.deepcopy(transformed))
            if not isinstance(transformed, dict):
                raise ValidationError("migration did not return an object")
            version += 1
            if transformed.get("schema_version") != version:
                raise ValidationError("migration must set schema_version to exactly the next version")
        transformed["revision"] = current["revision"] + 1
        transformed["writer"] = writer
        validate_document(normalized, transformed, writer=writer)
        _validate_transition(normalized, current, transformed)
        backup_dir = ROOT / "temp" / "runtime" / "migrations"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_name = f"{sha256_bytes(os.fsencode(str(target.absolute())))[:16]}-r{current['revision']}.json"
        atomic_write(backup_dir / backup_name, current_bytes)
        atomic_write(target, _canonical_bytes(transformed))
    return transformed


def _portfolio_decision_ref(
    decision: Mapping[str, Any], decision_path: str, decision_sha256: str
) -> dict[str, str]:
    return {
        "path": decision_path,
        "heading": str(decision["summary"]),
        "sha256": decision_sha256,
    }


def _portfolio_job_name(direction_id: str) -> str:
    return "EM" + "".join(component.capitalize() for component in re.split(r"[_-]", direction_id))


def _validate_portfolio_decision(
    decision: Mapping[str, Any],
    current: Mapping[str, Any],
    current_bytes: bytes,
    repo_root: Path,
) -> tuple[list[Mapping[str, Any]], set[str]]:
    required = {
        "schema_version",
        "decision_id",
        "decided_at",
        "summary",
        "expected_registry_revision",
        "expected_registry_sha256",
        "snapshot_digest",
        "proposed_candidates",
        "considered",
        "transitions",
        "capacity",
    }
    missing = sorted(required - decision.keys())
    if missing:
        raise ValidationError(f"portfolio decision missing required keys: {missing}")
    if decision["schema_version"] != 1:
        raise UnsupportedVersionError("portfolio decision schema_version must be 1")
    if "snapshot_sha256" in decision:
        raise ValidationError(
            "snapshot_sha256 is ambiguous; use expected_registry_sha256 and snapshot_digest"
        )
    decision_id = decision["decision_id"]
    if not isinstance(decision_id, str) or PORTFOLIO_DECISION_ID_RE.fullmatch(decision_id) is None:
        raise ValidationError("decision_id must be a lowercase path-safe identifier")
    _ensure_timestamp(decision["decided_at"], "decided_at")
    summary = decision["summary"]
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 256:
        raise ValidationError("summary must contain 1..256 characters")

    expected_revision = decision["expected_registry_revision"]
    if not isinstance(expected_revision, int) or isinstance(expected_revision, bool):
        raise RevisionConflictError("expected_registry_revision must be an integer")
    if expected_revision != current["revision"]:
        raise RevisionConflictError(
            f"expected revision {expected_revision}, observed {current['revision']}"
        )
    expected_registry_sha256 = decision["expected_registry_sha256"]
    observed_registry_sha256 = sha256_bytes(current_bytes)
    if (
        not isinstance(expected_registry_sha256, str)
        or SHA256_RE.fullmatch(expected_registry_sha256) is None
    ):
        raise ValidationError("expected_registry_sha256 must be a lowercase SHA-256")
    if expected_registry_sha256 != observed_registry_sha256:
        raise RevisionConflictError(
            "expected_registry_sha256 mismatch: "
            f"expected {expected_registry_sha256}, observed {observed_registry_sha256}"
        )
    snapshot_digest = decision["snapshot_digest"]
    if not isinstance(snapshot_digest, str) or SHA256_RE.fullmatch(snapshot_digest) is None:
        raise ValidationError("snapshot_digest must be a lowercase SHA-256 provenance digest")

    current_by_id = {item["id"]: item for item in current["directions"]}
    proposed_value = decision["proposed_candidates"]
    if not isinstance(proposed_value, list):
        raise ValidationError("proposed_candidates must be an array")
    proposed_ids: list[str] = []
    for index, item in enumerate(proposed_value):
        if not isinstance(item, dict) or set(item) != {"direction_id"}:
            raise ValidationError(
                f"proposed_candidates[{index}] must contain exactly direction_id"
            )
        direction_id = item["direction_id"]
        if not isinstance(direction_id, str) or DIRECTION_RE.fullmatch(direction_id) is None:
            raise ValidationError(f"proposed_candidates[{index}].direction_id is invalid")
        proposed_ids.append(direction_id)
    proposed = set(proposed_ids)
    if len(proposed) != len(proposed_ids):
        raise ValidationError("proposed_candidates contains duplicate direction_id")
    existing_proposals = proposed & set(current_by_id)
    if existing_proposals:
        raise ValidationError(
            f"proposed_candidates contains existing directions: {sorted(existing_proposals)}"
        )
    snapshot = {
        "registry_sha256": observed_registry_sha256,
        "proposed_candidates": [
            {"direction_id": direction_id} for direction_id in sorted(proposed)
        ],
    }
    observed_snapshot_digest = sha256_bytes(_canonical_bytes(snapshot))
    if snapshot_digest != observed_snapshot_digest:
        raise RevisionConflictError(
            "snapshot_digest mismatch for current registry and proposed candidates: "
            f"expected {snapshot_digest}, observed {observed_snapshot_digest}"
        )

    considered_value = decision["considered"]
    if not isinstance(considered_value, list):
        raise ValidationError("considered must be an array")
    considered_ids: list[str] = []
    considered_keys = {"direction_id", "disposition", "priority", "summary", "evidence_refs"}
    for index, item in enumerate(considered_value):
        if not isinstance(item, dict) or set(item) != considered_keys:
            raise ValidationError(f"considered[{index}] must contain exactly {sorted(considered_keys)}")
        direction_id = item["direction_id"]
        if not isinstance(direction_id, str) or DIRECTION_RE.fullmatch(direction_id) is None:
            raise ValidationError(f"considered[{index}].direction_id is invalid")
        considered_ids.append(direction_id)
        disposition = item["disposition"]
        if not isinstance(disposition, str) or re.fullmatch(r"[A-Z][A-Z0-9_-]{0,63}", disposition) is None:
            raise ValidationError(f"considered[{index}].disposition is invalid")
        priority = item["priority"]
        if not isinstance(priority, int) or isinstance(priority, bool) or priority < 1:
            raise ValidationError(f"considered[{index}].priority must be a positive integer")
        considered_summary = item["summary"]
        if not isinstance(considered_summary, str) or not considered_summary.strip():
            raise ValidationError(f"considered[{index}].summary is required")
        evidence_refs = item["evidence_refs"]
        if not isinstance(evidence_refs, list) or not evidence_refs:
            raise ValidationError(f"considered[{index}].evidence_refs must be a non-empty array")
        for ref_index, ref in enumerate(evidence_refs):
            prefix = f"considered[{index}].evidence_refs[{ref_index}]"
            if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
                raise ValidationError(f"{prefix} must contain exactly path and sha256")
            ref_path = ref["path"]
            _ensure_path(ref_path, f"{prefix}.path")
            lexical_target = repo_root / Path(ref_path)
            current_component = repo_root
            for component in Path(ref_path).parts:
                current_component /= component
                if _is_alias(current_component):
                    raise OwnershipError(f"{prefix}.path traverses a symlink or reparse point")
            if not lexical_target.is_file():
                raise ValidationError(f"{prefix}.path does not reference an existing file")
            ref_sha = ref["sha256"]
            if not isinstance(ref_sha, str) or SHA256_RE.fullmatch(ref_sha) is None:
                raise ValidationError(f"{prefix}.sha256 must be a lowercase SHA-256")
            if sha256_file(lexical_target) != ref_sha:
                raise ValidationError(f"{prefix}.sha256 does not match existing file bytes")
    considered = set(considered_ids)
    if len(considered) != len(considered_ids):
        raise ValidationError("considered contains duplicate direction_id")
    snapshot_direction_ids = set(current_by_id) | proposed
    missing_considered = snapshot_direction_ids - considered
    if missing_considered:
        raise ValidationError(
            f"considered does not cover snapshot directions: {sorted(missing_considered)}"
        )
    unknown_considered = considered - snapshot_direction_ids
    if unknown_considered:
        raise ValidationError(f"considered contains undefined directions: {sorted(unknown_considered)}")

    transitions_value = decision["transitions"]
    if not isinstance(transitions_value, list):
        raise ValidationError("transitions must be an array")
    transitions: list[Mapping[str, Any]] = []
    transition_ids: set[str] = set()
    allowed_lifecycles = {"REGISTERED", "ACTIVE", "PARKED", "CLOSED"}
    transition_keys = {
        "direction_id",
        "lifecycle",
        "summary",
        "next_role",
        "next_objective",
        "reactivation_condition",
        "new_direction",
    }
    for index, value in enumerate(transitions_value):
        if not isinstance(value, dict) or set(value) != transition_keys:
            raise ValidationError(f"transitions[{index}] must contain exactly {sorted(transition_keys)}")
        direction_id = value.get("direction_id")
        if not isinstance(direction_id, str) or DIRECTION_RE.fullmatch(direction_id) is None:
            raise ValidationError(f"transitions[{index}].direction_id is invalid")
        if direction_id in transition_ids:
            raise ValidationError(f"duplicate transition direction_id: {direction_id}")
        transition_ids.add(direction_id)
        if direction_id not in considered:
            raise ValidationError(f"transition direction is not considered: {direction_id}")
        lifecycle = value.get("lifecycle")
        if lifecycle not in allowed_lifecycles:
            raise ValidationError(f"transitions[{index}].lifecycle is invalid")
        transition_summary = value.get("summary")
        if not isinstance(transition_summary, str) or not transition_summary.strip():
            raise ValidationError(f"transitions[{index}].summary is required")
        next_role = value.get("next_role")
        next_objective = value.get("next_objective")
        reactivation_condition = value.get("reactivation_condition")
        if lifecycle == "ACTIVE":
            if next_role not in {"EM", "CM"}:
                raise ValidationError(f"transitions[{index}] ACTIVE next_role must be EM or CM")
            if not isinstance(next_objective, str) or not next_objective.strip():
                raise ValidationError(f"transitions[{index}] ACTIVE next_objective is required")
            if reactivation_condition is not None:
                raise ValidationError(
                    f"transitions[{index}] ACTIVE reactivation_condition must be null"
                )
        elif lifecycle == "PARKED":
            if next_role != "Root":
                raise ValidationError(f"transitions[{index}] PARKED next_role must be Root")
            if (
                not isinstance(next_objective, str)
                or not next_objective.strip()
            ):
                raise ValidationError(
                    f"transitions[{index}] PARKED next_objective must be an exact user question"
                )
            if not isinstance(reactivation_condition, str) or not reactivation_condition.strip():
                raise ValidationError(
                    f"transitions[{index}] PARKED reactivation_condition is required"
                )
        elif any(
            item is not None for item in (next_role, next_objective, reactivation_condition)
        ):
            raise ValidationError(
                f"transitions[{index}] {lifecycle} next fields must be null"
            )

        new_direction = value.get("new_direction")
        current_direction = current_by_id.get(direction_id)
        if current_direction is None:
            if direction_id not in proposed:
                raise ValidationError(f"new direction {direction_id} is not a proposed candidate")
            new_direction_keys = {
                "title",
                "abbreviation",
                "scientific_question",
                "dependencies",
                "base_sha",
            }
            if not isinstance(new_direction, dict) or set(new_direction) != new_direction_keys:
                raise ValidationError(
                    f"new direction {direction_id} new_direction must contain exactly "
                    f"{sorted(new_direction_keys)}"
                )
            if not isinstance(new_direction["title"], str) or not new_direction["title"].strip():
                raise ValidationError(f"new direction {direction_id} title is required")
            abbreviation = new_direction["abbreviation"]
            if not isinstance(abbreviation, str) or re.fullmatch(r"[A-Z][A-Z0-9]{1,15}", abbreviation) is None:
                raise ValidationError(f"new direction {direction_id} abbreviation is invalid")
            question = new_direction["scientific_question"]
            if not isinstance(question, str) or not question.strip():
                raise ValidationError(f"new direction {direction_id} scientific_question is required")
            dependencies = new_direction["dependencies"]
            if not isinstance(dependencies, list) or not all(
                isinstance(item, str) and DIRECTION_RE.fullmatch(item) is not None
                for item in dependencies
            ):
                raise ValidationError(f"new direction {direction_id} dependencies are invalid")
            if len(set(dependencies)) != len(dependencies):
                raise ValidationError(f"new direction {direction_id} dependencies contain duplicates")
            base_sha = new_direction["base_sha"]
            if not isinstance(base_sha, str) or GIT_SHA_RE.fullmatch(base_sha) is None:
                raise ValidationError(f"new direction {direction_id} base_sha is invalid")
            if lifecycle == "ACTIVE" and next_role != "EM":
                raise ValidationError(f"new ACTIVE direction {direction_id} next_role must be EM")
        else:
            if new_direction is not None:
                raise ValidationError(f"existing direction {direction_id} cannot redefine new_direction")
        transitions.append(value)

    lifecycle_by_id = {item["id"]: item["lifecycle"] for item in current["directions"]}
    for transition in transitions:
        lifecycle_by_id[str(transition["direction_id"])] = str(transition["lifecycle"])
    resulting_active = {
        direction_id for direction_id, lifecycle in lifecycle_by_id.items() if lifecycle == "ACTIVE"
    }
    capacity = decision["capacity"]
    capacity_keys = {
        "active_limit",
        "active_before",
        "active_after",
        "active_direction_ids",
        "resource_constraints",
        "unused_capacity_reason",
    }
    if not isinstance(capacity, dict) or set(capacity) != capacity_keys:
        raise ValidationError(f"capacity must contain exactly {sorted(capacity_keys)}")
    active_limit = capacity["active_limit"]
    active_before = capacity["active_before"]
    active_after = capacity["active_after"]
    active_ids = capacity["active_direction_ids"]
    if (
        not isinstance(active_limit, int)
        or isinstance(active_limit, bool)
        or active_limit < 0
        or active_limit > 8
    ):
        raise ValidationError("capacity active_limit must be an integer in 0..8")
    observed_active_before = sum(
        item["lifecycle"] == "ACTIVE" for item in current["directions"]
    )
    if (
        not isinstance(active_before, int)
        or isinstance(active_before, bool)
        or active_before != observed_active_before
    ):
        raise ValidationError(
            f"capacity active_before must equal observed registry count {observed_active_before}"
        )
    if (
        not isinstance(active_after, int)
        or isinstance(active_after, bool)
        or active_after != len(resulting_active)
    ):
        raise ValidationError(
            f"capacity active_after must equal resulting registry count {len(resulting_active)}"
        )
    if not isinstance(active_ids, list) or not all(isinstance(item, str) for item in active_ids):
        raise ValidationError("capacity active_direction_ids must be an array")
    if len(set(active_ids)) != len(active_ids):
        raise ValidationError("capacity active_direction_ids contains duplicates")
    if len(active_ids) != active_after or set(active_ids) != resulting_active:
        raise ValidationError("capacity active_direction_ids do not match resulting registry")
    if active_after > active_limit:
        raise ValidationError("capacity active_after exceeds active_limit")
    resource_constraints = capacity["resource_constraints"]
    if not isinstance(resource_constraints, list) or not all(
        isinstance(item, str) and bool(item.strip()) for item in resource_constraints
    ):
        raise ValidationError("capacity resource_constraints must be a string array")
    unused_capacity_reason = capacity["unused_capacity_reason"]
    if active_after < active_limit and (
        not isinstance(unused_capacity_reason, str) or not unused_capacity_reason.strip()
    ):
        raise ValidationError(
            "capacity unused_capacity_reason is required when active_after is below active_limit"
        )
    if unused_capacity_reason is not None and (
        not isinstance(unused_capacity_reason, str) or not unused_capacity_reason.strip()
    ):
        raise ValidationError("capacity unused_capacity_reason must be null or a non-empty string")
    return transitions, resulting_active


def _new_direction_documents(
    transition: Mapping[str, Any],
    decision: Mapping[str, Any],
    decision_ref: Mapping[str, str],
    next_registry_revision: int,
) -> tuple[bytes, dict[str, Any], dict[str, Any], dict[str, Any]]:
    direction_id = str(transition["direction_id"])
    definition = transition["new_direction"]
    assert isinstance(definition, Mapping)
    dependencies = list(definition["dependencies"])
    dependency_text = ", ".join(f"`{item}`" for item in dependencies) or "None"
    direction_text = (
        f"# Direction {direction_id}: {definition['title']}\n\n"
        "## Authority\n\n"
        f"- Stable direction ID: `{direction_id}`\n"
        f"- Registry abbreviation: `{definition['abbreviation']}`\n"
        f"- Initial registry lifecycle: `{transition['lifecycle']}`\n"
        f"- Portfolio decision: `{decision_ref['path']}`\n"
        f"- Dependencies: {dependency_text}\n\n"
        "## Scientific question\n\n"
        f"{definition['scientific_question'].strip()}\n\n"
        "## Initial objective\n\n"
        f"- Next role: `{transition['next_role']}`\n"
        f"- Next objective: {transition['next_objective']}\n\n"
        "## Provenance boundary\n\n"
        "This bootstrap records a Portfolio definition and routing objective. It records no "
        "scientific result, engineering acceptance, provider operation, checkpoint, or experiment.\n"
    )
    direction_bytes = direction_text.encode("utf-8")
    direction_sha = sha256_bytes(direction_bytes)
    question_sha = sha256_bytes(str(definition["scientific_question"]).strip().encode("utf-8"))
    active = transition["lifecycle"] == "ACTIVE"
    research = {
        "schema_version": 1,
        "revision": 1,
        "updated_at": decision["decided_at"],
        "writer": f"EM-{direction_id}",
        "direction_id": direction_id,
        "registry_revision_seen": next_registry_revision,
        "phase": "SCOPING" if active else "IDLE",
        "actionable": active,
        "blockers": [],
        "waiting_on": [],
        "direction_ref": {
            "path": f"docs/research/candidates/{direction_id}/DIRECTION.md",
            "sha256": direction_sha,
        },
        "question_sha256": question_sha,
        "evidence_set_sha256": decision_ref["sha256"],
        "active_round_id": None,
        "active_agents": [],
        "engineering_request": None,
        "last_checkpoint_sha": None,
        "next_action": {
            "kind": "PORTFOLIO_ASSIGNMENT" if active else "IDLE",
            "input_refs": (
                [{"path": decision_ref["path"], "sha256": decision_ref["sha256"]}]
                if active
                else []
            ),
        },
    }
    base_sha = str(definition["base_sha"])
    engineering = {
        "schema_version": 1,
        "revision": 1,
        "updated_at": decision["decided_at"],
        "writer": f"CM-{direction_id}",
        "direction_id": direction_id,
        "phase": "UNREQUESTED",
        "actionable": False,
        "blockers": [],
        "waiting_on": [],
        "scope_ref": {
            "path": f"docs/research/candidates/{direction_id}/DIRECTION.md",
            "heading": "Engineering request",
            "sha256": direction_sha,
        },
        "base_sha": base_sha,
        "worktree_ref": None,
        "candidate_sha": None,
        "changed_paths": [],
        "verification_refs": [],
        "run_refs": [],
        "integration": {
            "target_branch": "main",
            "target_sha_seen": base_sha,
            "integrated_sha": None,
        },
        "active_agents": [],
        "last_checkpoint_sha": None,
        "next_action": {"kind": "UNREQUESTED", "input_refs": []},
    }
    external = {
        "schema_version": 1,
        "revision": 1,
        "updated_at": decision["decided_at"],
        "writer": f"EM-{direction_id}",
        "direction_id": direction_id,
        "workflow_version": "hmasd-external-review-v1",
        "rounds": [],
    }
    validate_document("research_state", research, writer=f"EM-{direction_id}")
    validate_document("engineering_state", engineering, writer=f"CM-{direction_id}")
    validate_document("external_review_index", external, writer=f"EM-{direction_id}")
    return direction_bytes, research, engineering, external


@contextlib.contextmanager
def _portfolio_apply_lock(repo_root: Path, registry: Path) -> Iterator[None]:
    lock_key = os.path.normcase(os.path.abspath(os.fspath(registry)))
    lock_path = repo_root / ".codex" / "runtime" / "locks" / f"{sha256_bytes(os.fsencode(lock_key))}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock_path.open("a+b") as handle:
            with hmasd_platform.exclusive_file_lock(handle.fileno()):
                yield
    except OSError as exc:
        raise StateError(f"cannot acquire portfolio apply lock {lock_path}: {exc}") from exc


def portfolio_apply(
    repo_root: str | os.PathLike[str],
    registry_path: str | os.PathLike[str],
    input: Mapping[str, Any] | str | os.PathLike[str],
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    registry = Path(registry_path).resolve()
    expected_registry = (root / "docs/research/portfolio/workflow/registry.json").resolve()
    if registry != expected_registry:
        raise OwnershipError("portfolio-apply registry must be the standard path under repo-root")
    decision = _input_document(input)
    portfolio_path = root / "docs/research/portfolio/PORTFOLIO.md"
    if not portfolio_path.is_file() or _is_alias(portfolio_path):
        raise OwnershipError("portfolio-apply requires a regular PORTFOLIO.md")

    with _portfolio_apply_lock(root, registry):
        current_bytes, current = _read_document(registry)
        validate_document("portfolio_registry", current, writer="Portfolio")
        transitions, _ = _validate_portfolio_decision(decision, current, current_bytes, root)
        decision_bytes = _canonical_bytes(decision)
        decision_sha = sha256_bytes(decision_bytes)
        decision_relative = f"docs/research/portfolio/decisions/{decision['decision_id']}.json"
        decision_target = root / Path(decision_relative)
        if decision_target.exists():
            raise RevisionConflictError(f"decision authority already exists: {decision_relative}")
        decision_ref = _portfolio_decision_ref(decision, decision_relative, decision_sha)
        current_by_id = {item["id"]: item for item in current["directions"]}
        next_revision = current["revision"] + 1
        next_registry = copy.deepcopy(current)
        next_registry["revision"] = next_revision
        next_registry["updated_at"] = decision["decided_at"]
        next_directions = {item["id"]: item for item in next_registry["directions"]}
        new_documents: dict[str, tuple[bytes, dict[str, Any], dict[str, Any], dict[str, Any]]] = {}

        for transition in transitions:
            direction_id = str(transition["direction_id"])
            if direction_id in current_by_id:
                entry = next_directions[direction_id]
                entry["lifecycle"] = transition["lifecycle"]
                entry["lifecycle_decision_ref"] = copy.deepcopy(decision_ref)
                entry["reactivation_condition_ref"] = (
                    copy.deepcopy(decision_ref) if transition["lifecycle"] == "PARKED" else None
                )
                continue
            definition = transition["new_direction"]
            assert isinstance(definition, Mapping)
            direction_root = f"docs/research/candidates/{direction_id}"
            entry = {
                "id": direction_id,
                "abbreviation": definition["abbreviation"],
                "path": direction_root,
                "lifecycle": transition["lifecycle"],
                "dependencies": list(definition["dependencies"]),
                "lifecycle_decision_ref": copy.deepcopy(decision_ref),
                "reactivation_condition_ref": (
                    copy.deepcopy(decision_ref) if transition["lifecycle"] == "PARKED" else None
                ),
                "agent": {
                    "logical_identity": f"EM-{direction_id}",
                    "job_name": _portfolio_job_name(direction_id),
                    "generation": 1,
                    "runtime_ref": None,
                },
                "research_state_path": f"{direction_root}/workflow/research/state.json",
                "engineering_state_path": f"{direction_root}/workflow/engineering/state.json",
                "external_review_index_path": f"{direction_root}/workflow/external-review/index.json",
            }
            next_registry["directions"].append(entry)
            next_directions[direction_id] = entry
            new_documents[direction_id] = _new_direction_documents(
                transition, decision, decision_ref, next_revision
            )

        next_registry["directions"].sort(key=lambda item: item["id"])
        portfolio_before = portfolio_path.read_bytes()
        try:
            portfolio_text = portfolio_before.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError(f"PORTFOLIO.md is not UTF-8: {exc}") from exc
        transition_lines = "\n".join(
            f"- `{item['direction_id']}` -> `{item['lifecycle']}`: {item['summary']}"
            for item in transitions
        ) or "- No lifecycle transition."
        considered_lines = []
        for item in decision["considered"]:
            evidence = ", ".join(
                f"`{ref['path']}` @ `{ref['sha256']}`" for ref in item["evidence_refs"]
            )
            considered_lines.append(
                f"- Considered `{item['direction_id']}` — priority `{item['priority']}`, "
                f"disposition `{item['disposition']}`: {item['summary']} Evidence: {evidence}"
            )
        considered_text = "\n".join(considered_lines)
        capacity = decision["capacity"]
        resources = "; ".join(capacity["resource_constraints"]) or "None recorded."
        unused = capacity["unused_capacity_reason"] or "None; active capacity is fully allocated."
        portfolio_append = (
            f"\n## Decision {decision['decision_id']} — {decision['decided_at']}\n\n"
            f"{decision['summary']}\n\n"
            f"Snapshot provenance: `{decision['snapshot_digest']}`\n\n"
            f"### Considered\n\n{considered_text}\n\n"
            f"### Transitions\n\n{transition_lines}\n\n"
            f"### Capacity\n\n"
            f"- Active capacity: `{capacity['active_before']} -> {capacity['active_after']} / "
            f"{capacity['active_limit']}`\n"
            f"- Resource constraints: {resources}\n"
            f"- Unused capacity reason: {unused}\n\n"
            f"Authority: `{decision_relative}`\n"
        )
        portfolio_bytes = (portfolio_text.rstrip() + "\n" + portfolio_append).encode("utf-8")
        next_registry["goal"]["sha256"] = sha256_bytes(portfolio_bytes)
        validate_document("portfolio_registry", next_registry, writer="Portfolio")
        _validate_transition("portfolio_registry", current, next_registry)
        next_registry_bytes = _canonical_bytes(next_registry)

        stage = Path(tempfile.mkdtemp(prefix=".portfolio-apply-", dir=str(root)))
        published_directions: list[Path] = []
        decision_published = False
        portfolio_published = False
        committed = False
        try:
            staged_decision = stage / "decision.json"
            staged_decision.write_bytes(decision_bytes)
            staged_directions: dict[str, Path] = {}
            for direction_id, documents in new_documents.items():
                direction_bytes, research, engineering, external = documents
                staged_root = stage / "directions" / direction_id
                (staged_root / "workflow/research").mkdir(parents=True)
                (staged_root / "workflow/engineering").mkdir(parents=True)
                (staged_root / "workflow/external-review").mkdir(parents=True)
                (staged_root / "DIRECTION.md").write_bytes(direction_bytes)
                (staged_root / "workflow/research/state.json").write_bytes(_canonical_bytes(research))
                (staged_root / "workflow/engineering/state.json").write_bytes(_canonical_bytes(engineering))
                (staged_root / "workflow/external-review/index.json").write_bytes(_canonical_bytes(external))
                staged_directions[direction_id] = staged_root

            decision_target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_decision, decision_target)
            decision_published = True
            candidates_root = root / "docs/research/candidates"
            candidates_root.mkdir(parents=True, exist_ok=True)
            for direction_id, staged_root in staged_directions.items():
                target = candidates_root / direction_id
                if target.exists():
                    raise RevisionConflictError(f"new direction path already exists: {target}")
                os.replace(staged_root, target)
                published_directions.append(target)
            try:
                atomic_write(portfolio_path, portfolio_bytes)
                portfolio_published = True
            except Exception:
                if portfolio_path.is_file() and portfolio_path.read_bytes() == portfolio_bytes:
                    portfolio_published = True
                raise
            try:
                atomic_write(registry, next_registry_bytes)
                committed = True
            except Exception:
                if registry.is_file() and registry.read_bytes() == next_registry_bytes:
                    committed = True
                else:
                    raise
        except Exception:
            if not committed:
                if portfolio_published:
                    atomic_write(portfolio_path, portfolio_before)
                for target in reversed(published_directions):
                    shutil.rmtree(target)
                if decision_published:
                    decision_target.unlink()
                    with contextlib.suppress(OSError):
                        decision_target.parent.rmdir()
            raise
        finally:
            shutil.rmtree(stage, ignore_errors=True)
        return next_registry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--kind", required=True)
    validate_parser.add_argument("--path", required=True)

    initialize_parser = subparsers.add_parser("initialize")
    initialize_parser.add_argument("--kind", required=True)
    initialize_parser.add_argument("--path", required=True)
    initialize_parser.add_argument("--writer", required=True)
    initialize_parser.add_argument("--input", required=True)

    replace_parser = subparsers.add_parser("replace")
    replace_parser.add_argument("--kind", required=True)
    replace_parser.add_argument("--path", required=True)
    replace_parser.add_argument("--writer", required=True)
    replace_parser.add_argument("--expected-revision", required=True, type=int)
    replace_parser.add_argument("--input", required=True)

    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--kind", required=True)
    migrate_parser.add_argument("--path", required=True)
    migrate_parser.add_argument("--writer", required=True)
    migrate_parser.add_argument("--expected-revision", required=True, type=int)
    migrate_parser.add_argument("--to-version", required=True, type=int)

    portfolio_apply_parser = subparsers.add_parser("portfolio-apply")
    portfolio_apply_parser.add_argument("--repo-root", required=True)
    portfolio_apply_parser.add_argument("--registry", required=True)
    portfolio_apply_parser.add_argument("--input", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            target = Path(args.path)
            normalized = normalize_kind(args.kind)
            validate_document(normalized, _read_document(target)[1])
        elif args.command == "initialize":
            initialize(args.kind, args.path, args.writer, args.input)
        elif args.command == "replace":
            replace(args.kind, args.path, args.writer, args.expected_revision, args.input)
        elif args.command == "migrate":
            migrate(args.kind, args.path, args.writer, args.expected_revision, args.to_version)
        elif args.command == "portfolio-apply":
            portfolio_apply(args.repo_root, args.registry, args.input)
        else:
            raise ValidationError(f"unknown command {args.command}")
    except StateError as exc:
        print(f"hmasd_state: {exc}", file=sys.stderr)
        return exc.exit_code
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
