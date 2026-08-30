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
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterator, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
SUPPORTED_SCHEMA_VERSION = 2

KIND_ALIASES = {
    "portfolio_registry": "portfolio_registry",
    "research_state": "research_state",
    "engineering_state": "engineering_state",
    "external_review_index": "external_review_index",
    "run_manifest": "run_manifest",
    "accepted_result": "accepted_result",
    "agent_result": "agent_result",
    "runtime_agents": "runtime_agents",
    "runtime_worktrees": "runtime_worktrees",
    "runtime_browser_assignments": "runtime_browser_assignments",
}

CURRENT_WRITE_SCHEMA_VERSIONS = {
    "research_state": 2,
    "engineering_state": 2,
    "agent_result": 2,
    "runtime_agents": 2,
    "runtime_worktrees": 2,
    "runtime_browser_assignments": 2,
    "external_review_index": 4,
}


DIRECTION_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z$"
)
PATH_RE = re.compile(r"^(?!/)(?![A-Za-z]:)(?!.*(?:^|/)\.\.(?:/|$))(?!.*\\)[^\x00]+$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SECRET_NAME_RE = re.compile(r"(?:secret|token|password|credential|private[_-]?key)", re.I)



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
            if (keyword == "anyOf" and matches < 1) or (
                keyword == "oneOf" and matches != 1
            ):
                raise _SchemaFailure(f"{path}: {keyword} failed ({'; '.join(failures)})")

    if "not" in schema:
        try:
            _validate_schema(value, schema["not"], root, path)
        except _SchemaFailure:
            pass
        else:
            raise _SchemaFailure(f"{path}: not failed")

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
        _datetime.datetime.fromisoformat(value[:-1])
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






def _owner_error(message: str) -> OwnershipError:
    return OwnershipError(message)

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
        if direction["lifecycle_decision_ref"]["path"] != "docs/research/portfolio/PORTFOLIO.md":
            raise _owner_error(f"{prefix}.lifecycle_decision_ref path is not Portfolio-owned")
        condition = direction["reactivation_condition_ref"]
        if condition is not None and condition["path"] != "docs/research/portfolio/PORTFOLIO.md":
            raise _owner_error(f"{prefix}.reactivation_condition_ref path is not Portfolio-owned")
        if direction["lifecycle"] == "PARKED" and condition is None:
            raise ValidationError(f"{prefix}.reactivation_condition_ref is required for PARKED")
        for dependency in direction["dependencies"]:
            if dependency not in ids and dependency not in {item["id"] for item in directions}:
                raise ValidationError(f"unknown dependency {dependency}")
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
    document: Mapping[str, Any], *, allow_live_sha_drift: bool = False
) -> None:
    """Check a research ref against the on-disk registry when available."""

    registry_path = ROOT / "docs" / "research" / "portfolio" / "workflow" / "registry.json"
    if not registry_path.is_file() or registry_path.is_symlink():
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
    if not target.is_file() or target.is_symlink():
        raise ValidationError("research direction_ref target is missing or symlinked")
    if sha256_file(target) != reference["sha256"] and not allow_live_sha_drift:
        raise ValidationError("research direction_ref SHA does not match exact file bytes")


def _validate_direction_state(
    document: Mapping[str, Any],
    kind: str,
    *,
    allow_stale_research_direction_ref: bool = False,
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
            document, allow_live_sha_drift=allow_stale_research_direction_ref
        )
    elif kind == "engineering_state":
        if document["scope_ref"]["path"] != expected_direction_path:
            raise _owner_error("engineering scope_ref path is not direction-owned")
    if kind in {"research_state", "engineering_state"} and document["schema_version"] >= 2:
        if "owner" not in document["next_action"]:
            raise ValidationError("schema v2 next_action requires an explicit owner")
    return direction_id


def _validate_external_index(document: Mapping[str, Any]) -> None:
    direction_id = _validate_direction_state(document, "external_review_index")
    workflow_version = document["workflow_version"]

    seen_rounds: set[str] = set()
    for index, round_document in enumerate(document["rounds"]):
        round_id = round_document["round_id"]
        if round_id in seen_rounds:
            raise ValidationError(f"duplicate external round id: {round_id}")
        seen_rounds.add(round_id)
        expected = sha256_bytes(
            (
                direction_id
                + "\n"
                + round_document["question_sha256"]
                + "\n"
                + round_document["evidence_set_sha256"]
                + "\n"
                + workflow_version
            ).encode("utf-8")
        )[:20]
        if round_id != expected:
            raise ValidationError(f"rounds[{index}].round_id does not match frozen inputs")
        base = f"docs/external-review/directions/{direction_id}/"
        for key, ref in round_document["prompt_refs"].items():
            if ref is not None and not ref["path"].startswith(base):
                raise _owner_error(f"prompt_refs.{key} is outside the direction archive")
        for provider in round_document["providers"].values():
            if provider is not None:
                _validate_transport_facts(
                    provider,
                    f"rounds[{index}].providers result",
                )


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




def _validate_transport_facts(facts: Mapping[str, Any], label: str) -> None:
    """Enforce the shared minimal BrowserTransport receipt invariants."""

    if facts["provider"] == "chatgpt" and (
        facts["product_model"] != "GPT-5.6 Sol"
        or facts["reasoning_effort"] != "Pro"
    ):
        raise ValidationError(
            f"{label} ChatGPT target must use product_model GPT-5.6 Sol and reasoning_effort Pro"
        )
    if facts["provider"] == "gemini" and facts["reasoning_effort"] is not None:
        raise ValidationError(f"{label} Gemini target must use reasoning_effort null")

    send_attempted = facts["send_attempted"]
    send_attempted_at = facts["send_attempted_at"]
    if send_attempted != (send_attempted_at is not None):
        raise ValidationError(
            f"{label}.send_attempted and send_attempted_at must be paired"
        )
    user_message_id = facts["provider_user_message_id"]
    assistant_message_id = facts["provider_assistant_message_id"]
    archive = facts["archive"]
    if user_message_id is not None and not send_attempted:
        raise ValidationError(
            f"{label}.provider_user_message_id requires send_attempted"
        )
    if assistant_message_id is not None and user_message_id is None:
        raise ValidationError(
            f"{label}.provider_assistant_message_id requires provider_user_message_id"
        )
    if archive is not None and assistant_message_id is None:
        raise ValidationError(
            f"{label}.archive requires provider_assistant_message_id"
        )
    if archive is not None and archive["path"] != facts["response_path"]:
        raise ValidationError(
            f"{label}.archive.path must equal response_path"
        )


def _validate_agent_result(document: Mapping[str, Any]) -> None:
    payload = document["payload"]
    payload_kind = payload["kind"]
    role = document["role"]
    identity = document["logical_identity"]
    action_ids: set[str] = set()
    for action in document["next_actions"]:
        action_id = action["action_id"]
        if action_id in action_ids:
            raise ValidationError(f"duplicate next action id: {action_id}")
        action_ids.add(action_id)
    if payload_kind == "root":
        if role != "root" or identity != "Root":
            raise OwnershipError("Root result must be owned by Root")
    elif payload_kind == "git":
        if role != "hmasd-git-integration":
            raise OwnershipError("Git integration result must use hmasd-git-integration role")
        actor = payload["actor"]
        if actor == "root":
            expected_identity = "Root"
        else:
            actor_role, actor_direction = actor.split(":", 1)
            if actor_direction != payload["direction_id"]:
                raise OwnershipError("Git integration actor does not match its direction")
            expected_identity = f"{actor_role.upper()}-{actor_direction}"
        if identity != expected_identity:
            raise OwnershipError("Git integration result does not match its actor")
    elif payload_kind == "portfolio":
        if role != "root" or identity != "Root":
            raise OwnershipError("portfolio result must be owned by Root")
    elif payload_kind == "em":
        if role != "hmasd-em" or identity != f"EM-{payload['direction_id']}":
            raise OwnershipError("EM result does not match its direction manager")
    elif payload_kind == "cm":
        if role != "hmasd-cm" or identity != f"CM-{payload['direction_id']}":
            raise OwnershipError("CM result does not match its direction manager")
    elif payload_kind == "clerk":
        if role != "hmasd-clerk":
            raise OwnershipError("Clerk result must use hmasd-clerk role")
        if identity != "Clerk":
            raise OwnershipError("Clerk result must use the stable Clerk identity")
        if payload["job_id"] != document["assignment_id"]:
            raise OwnershipError("Clerk result job_id must match its sequential assignment")
        if document["decision_requests"]:
            raise OwnershipError("Clerk result cannot request a decision")
        if document["next_actions"]:
            raise OwnershipError("Clerk result cannot choose a successor")
    else:
        permitted_roles = {
            "implementation": {"hmasd-implementer", "hmasd-implementer-terra"},
            "review": {
                "librarian",
                "hmasd-project-scout",
                "hmasd-code-scout",
                "hmasd-research-scout",
                "hmasd-research-innovator",
                "hmasd-research-critic",
                "hmasd-research-principles-analyst",
                "hmasd-reviewer",
            },
            "verification": {"hmasd-verifier"},
            "run": {"hmasd-experiment-operator"},
            "transport": {"hmasd-browser-transport"},
            "artifact": {"hmasd-research-artifact-writer"},
            "recovery": {"hmasd-workflow-recovery-manager"},
        }
        if role not in permitted_roles[payload_kind]:
            raise OwnershipError("agent result role does not own payload")
        if role == "hmasd-browser-transport":
            if identity != "BrowserTransport":
                raise OwnershipError("BrowserTransport result must use BrowserTransport identity")
            _validate_transport_facts(payload, "transport payload")
        elif identity != role:
            raise OwnershipError("specialist result does not match its logical identity")
    if document["decision_requests"] and document["materiality"] != "USER":
        raise OwnershipError("decision requests are reserved for USER materiality")
    if "event_id" in document:
        raise ValidationError("ordinary event_id is forbidden")


def _validate_runtime_agents(document: Mapping[str, Any]) -> None:
    identities: set[str] = set()
    for agent in document["agents"]:
        identity = agent["logical_identity"]
        if identity in identities:
            raise ValidationError(f"duplicate runtime logical identity: {identity}")
        identities.add(identity)
        if agent["agent_type"] == "hmasd-clerk":
            if identity != "Clerk":
                raise OwnershipError("runtime Clerk must use the stable Clerk identity")
            if agent["parent_identity"] != "Root":
                raise OwnershipError("runtime Clerk must be a Root child")
        if identity == "Root" and agent["parent_identity"] != "Root":
            raise OwnershipError("Root runtime agent must be self-parented")
        if identity == "BrowserTransport":
            if agent["agent_type"] != "hmasd-browser-transport":
                raise OwnershipError("BrowserTransport runtime agent type mismatch")
            if agent["parent_identity"] != "Root":
                raise OwnershipError("BrowserTransport runtime agent must be a Root child")
        elif agent["agent_type"] == "hmasd-browser-transport":
            raise OwnershipError("hmasd-browser-transport type is reserved for BrowserTransport")


def _validate_runtime_browser_assignments(document: Mapping[str, Any]) -> None:
    assignment_ids: set[str] = set()
    for assignment in document["assignments"]:
        assignment_id = assignment["assignment_id"]
        if assignment_id in assignment_ids:
            raise ValidationError(f"duplicate BrowserTransport assignment id: {assignment_id}")
        assignment_ids.add(assignment_id)
        _validate_transport_facts(
            assignment,
            f"BrowserTransport assignment {assignment_id!r}",
        )

def _validate_runtime_worktrees(document: Mapping[str, Any]) -> None:
    seen_refs: set[str] = set()
    seen_paths: set[str] = set()
    for worktree in document["worktrees"]:
        ref = worktree["worktree_ref"]
        path = worktree["canonical_absolute_path"]
        if ref in seen_refs or path in seen_paths:
            raise ValidationError("runtime worktree refs and paths must be unique")
        seen_refs.add(ref)
        seen_paths.add(path)
        if worktree["lifecycle"] == "PROVISIONING" and worktree["operation_token"] is None:
            raise ObservedConflictError("PROVISIONING worktree requires operation_token")
        expected_branch = f"omp/{worktree['direction_id']}/{worktree['kind']}/{worktree['assignment_id']}"
        if worktree["branch"] != expected_branch:
            raise OwnershipError("runtime worktree branch is not assignment-owned")
        candidate = Path(path)
        if candidate.exists() and candidate.is_symlink():
            raise OwnershipError("runtime worktree canonical path is a symlink")




def _validate_custom(
    kind: str,
    document: Mapping[str, Any],
    *,
    allow_stale_research_direction_ref: bool = False,
) -> None:
    if kind == "portfolio_registry":
        _validate_registry(document)
    elif kind in {"research_state", "engineering_state"}:
        _validate_direction_state(
            document,
            kind,
            allow_stale_research_direction_ref=allow_stale_research_direction_ref,
        )
    elif kind == "external_review_index":
        _validate_external_index(document)
    elif kind == "run_manifest":
        _validate_run_manifest(document)
    elif kind == "accepted_result":
        _validate_accepted_result(document)
    elif kind == "agent_result":
        _validate_agent_result(document)
    elif kind == "runtime_agents":
        _validate_runtime_agents(document)
    elif kind == "runtime_browser_assignments":
        _validate_runtime_browser_assignments(document)
    elif kind == "runtime_worktrees":
        _validate_runtime_worktrees(document)


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
    elif kind in {
        "runtime_agents",
        "runtime_worktrees",
        "runtime_browser_assignments",
    } and "writer" in document:
        if document["writer"] != "Root":
            raise _owner_error(f"{kind} writer must be Root")


def _reject_symlink_components(value: str, name: str) -> None:
    """Reject an existing symlink anywhere in a repository-relative path."""

    candidate = ROOT
    for component in value.split("/"):
        if component in {"", "."}:
            continue
        candidate /= component
        if candidate.is_symlink():
            raise _owner_error(f"{name} traverses symlink component {candidate}")


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


def _validate_document(
    kind: str,
    document: Mapping[str, Any],
    *,
    writer: str | None = None,
    allow_stale_research_direction_ref: bool = False,
) -> dict[str, Any]:
    """Validate a document with an internal current-state relaxation."""

    normalized = normalize_kind(kind)
    if not isinstance(document, dict):
        raise ValidationError("state document must be a JSON object")
    version = document.get("schema_version")
    supported_version = 4 if normalized == "external_review_index" else SUPPORTED_SCHEMA_VERSION
    if isinstance(version, int) and not isinstance(version, bool) and version > supported_version:
        raise UnsupportedVersionError(f"unsupported schema version {version}")
    _precheck_writer_ownership(normalized, document)
    schema = load_schema(normalized)
    try:
        _validate_schema(document, schema, schema, "$")
    except _SchemaFailure as exc:
        raise ValidationError(str(exc)) from exc
    _check_document_paths(document)
    if normalized != "agent_result":
        _ensure_timestamp(document["updated_at"], "updated_at")
        if writer is not None and document["writer"] != writer:
            raise _owner_error(f"writer {document['writer']!r} does not match requested writer {writer!r}")
    _validate_custom(
        normalized,
        document,
        allow_stale_research_direction_ref=allow_stale_research_direction_ref,
    )
    return document

def validate_document(
    kind: str,
    document: Mapping[str, Any],
    *,
    writer: str | None = None,
) -> dict[str, Any]:
    """Validate and return a JSON object without mutating it."""

    return _validate_document(kind, document, writer=writer)


def _validate_current_document(
    kind: str,
    document: Mapping[str, Any],
    *,
    writer: str | None = None,
) -> dict[str, Any]:
    """Validate persisted state while allowing only research live-ref SHA drift."""

    return _validate_document(
        kind,
        document,
        writer=writer,
        allow_stale_research_direction_ref=normalize_kind(kind) == "research_state",
    )


# Aliases kept intentionally boring for callers that use verb-oriented names.
validate_state = validate_document
validate = validate_document


def _read_document(path: Path) -> tuple[bytes, dict[str, Any]]:
    if path.is_symlink():
        raise OwnershipError(f"refusing symlink state path: {path}")
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
    _, document = _read_document(Path(path))
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
    digest = sha256_bytes(os.fsencode(str(path.absolute())))
    return ROOT / ".omp" / "runtime" / "locks" / f"{digest}.lock"


@contextlib.contextmanager
def state_lock(path: str | os.PathLike[str]) -> Iterator[None]:
    lock_path = _lock_path(Path(path))
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock_path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError as exc:
        raise StateError(f"cannot acquire state lock {lock_path}: {exc}") from exc


def _fsync_parent(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(str(path), flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(path: str | os.PathLike[str], data: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise OwnershipError(f"refusing symlink state path: {target}")
    mode = 0o666
    try:
        mode = target.stat().st_mode & 0o777
    except FileNotFoundError:
        pass
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    temp_path = Path(temp_name)
    try:
        os.fchmod(fd, mode)
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

def _require_current_write_schema(kind: str, document: Mapping[str, Any]) -> None:
    normalized = normalize_kind(kind)
    expected = CURRENT_WRITE_SCHEMA_VERSIONS.get(normalized)
    if expected is not None and document.get("schema_version") != expected:
        raise UnsupportedVersionError(
            f"{normalized} requires current schema version {expected}"
        )


def _initialize_unlocked(
    kind: str,
    target: Path,
    writer: str,
    document: dict[str, Any],
    input_bytes: bytes | None = None,
) -> dict[str, Any]:
    _require_current_write_schema(kind, document)
    validate_document(kind, document, writer=writer)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise OwnershipError(f"refusing symlink state path: {target}")
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
    if normalized == "agent_result":
        raise ObservedConflictError("agent_result is an immutable record")
    target = Path(path)
    document = _input_document(input)
    _require_current_write_schema(normalized, document)
    validate_document(normalized, document, writer=writer)
    if not isinstance(expected_revision, int) or isinstance(expected_revision, bool) or expected_revision < 1:
        raise RevisionConflictError("expected_revision must be a positive integer")
    with state_lock(target):
        current_bytes, current = _read_document(target)
        _validate_current_document(normalized, current, writer=writer)
        if (
            normalized in CURRENT_WRITE_SCHEMA_VERSIONS
            and document["schema_version"] != current["schema_version"]
        ):
            raise UnsupportedVersionError("schema version is immutable and must already be current")
        current_revision = current["revision"]
        if current_revision != expected_revision:
            raise RevisionConflictError(
                f"expected revision {expected_revision}, observed {current_revision}"
            )
        if document["revision"] != current_revision + 1:
            raise RevisionConflictError("replacement revision must increment exactly once")
        _validate_transition(normalized, current, document)
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
    _require_unchanged(
        current["schema_version"],
        next_document["schema_version"],
        "external review index.schema_version",
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
            _validate_transport_update(
                current_provider,
                next_provider,
                provider_label,
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


def _validate_runtime_agents_transition(
    current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    for identity, current_agent, next_agent in _matching_records(
        current["agents"],
        next_document["agents"],
        key="logical_identity",
        label="runtime agent",
    ):
        label = f"runtime agent {identity!r}"
        _require_unchanged_fields(
            current_agent,
            next_agent,
            ("agent_type", "parent_identity"),
            label,
        )
        if next_agent["generation"] < current_agent["generation"]:
            _immutable_conflict(f"{label}.generation")
        if next_agent["generation"] == current_agent["generation"]:
            _require_unchanged(
                current_agent["runtime_ref"],
                next_agent["runtime_ref"],
                f"{label}.runtime_ref",
            )


def _validate_transport_update(
    current: Mapping[str, Any],
    next_document: Mapping[str, Any],
    label: str,
) -> None:
    _require_unchanged_fields(
        current,
        next_document,
        (
            "provider",
            "product_model",
            "reasoning_effort",
            "target_conversation_url",
            "target_conversation_id",
            "prompt_ref",
            "response_path",
            "operation_id",
            "idempotency_key",
            "request_fingerprint",
            "stable_key",
            "operation_ref",
            "created_at",
        ),
        label,
    )
    for field in (
        "observed_conversation_url",
        "observed_conversation_id",
        "provider_user_message_id",
        "provider_assistant_message_id",
        "archive",
    ):
        _require_append_only(current[field], next_document[field], f"{label}.{field}")
    if current["send_attempted"] and not next_document["send_attempted"]:
        _immutable_conflict(f"{label}.send_attempted")
    _require_append_only(
        current["send_attempted_at"],
        next_document["send_attempted_at"],
        f"{label}.send_attempted_at",
    )
    if next_document["updated_at"] < current["updated_at"]:
        _immutable_conflict(f"{label}.updated_at")


def _validate_runtime_browser_assignments_transition(
    current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    for assignment_id, current_assignment, next_assignment in _matching_records(
        current["assignments"],
        next_document["assignments"],
        key="assignment_id",
        label="BrowserTransport assignment",
    ):
        label = f"BrowserTransport assignment {assignment_id!r}"
        _require_unchanged_fields(
            current_assignment,
            next_assignment,
            (
                "browser_identity",
                "requester_identity",
                "request_ref",
                "direction_id",
                "mode",
            ),
            label,
        )
        _require_append_only(
            current_assignment["effect_ref"],
            next_assignment["effect_ref"],
            f"{label}.effect_ref",
        )
        _validate_transport_update(current_assignment, next_assignment, label)


def _validate_runtime_worktrees_transition(
    current: Mapping[str, Any], next_document: Mapping[str, Any]
) -> None:
    for worktree_ref, current_worktree, next_worktree in _matching_records(
        current["worktrees"],
        next_document["worktrees"],
        key="worktree_ref",
        label="runtime worktree",
    ):
        label = f"runtime worktree {worktree_ref!r}"
        _require_unchanged_fields(
            current_worktree,
            next_worktree,
            (
                "direction_id",
                "kind",
                "assignment_id",
                "canonical_absolute_path",
                "branch",
                "base_sha",
                "receipt_path",
            ),
            label,
        )
        _require_append_only(
            current_worktree["operation_token"],
            next_worktree["operation_token"],
            f"{label}.operation_token",
        )
        _require_append_only(
            current_worktree["candidate_sha"],
            next_worktree["candidate_sha"],
            f"{label}.candidate_sha",
        )
        _require_append_only(
            current_worktree["integrated_sha"],
            next_worktree["integrated_sha"],
            f"{label}.integrated_sha",
        )
        if current_worktree["lifecycle"] in {"RELEASED", "RETAINED_FOR_RECOVERY"}:
            _require_unchanged(
                current_worktree,
                next_worktree,
                f"{label} terminal provenance",
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
    elif kind == "runtime_agents":
        _validate_runtime_agents_transition(current, next_document)
    elif kind == "runtime_browser_assignments":
        _validate_runtime_browser_assignments_transition(current, next_document)
    elif kind == "runtime_worktrees":
        _validate_runtime_worktrees_transition(current, next_document)




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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            validate_document(args.kind, _read_document(Path(args.path))[1])
        elif args.command == "initialize":
            initialize(args.kind, args.path, args.writer, args.input)
        elif args.command == "replace":
            replace(args.kind, args.path, args.writer, args.expected_revision, args.input)
        else:
            raise ValidationError(f"unknown command {args.command}")
    except StateError as exc:
        print(f"hmasd_state: {exc}", file=sys.stderr)
        return exc.exit_code
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
