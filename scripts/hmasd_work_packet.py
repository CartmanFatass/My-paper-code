#!/usr/bin/env python3
"""Build, publish, validate, and reconcile runtime-only HMASD Work Packets.

Packets carry immutable pointers to existing authority.  They are deliberately
not a durable state kind and contain no lifecycle, claim, result, or checkpoint
field.  A packet remains runnable only while all frozen authority references
still match the repository.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any, Callable, Mapping, Sequence
import unicodedata

try:
    from scripts import (
        hmasd_platform,
        hmasd_protocol_contracts,
        hmasd_state,
        hmasd_worktree,
    )
except ImportError:
    import hmasd_platform
    import hmasd_protocol_contracts
    import hmasd_state
    import hmasd_worktree


SCHEMA_VERSION = 1
SCHEMA_PATH = Path(__file__).with_name("schemas") / "hmasd_work_packet.schema.json"
WORK_RELATIVE_ROOT = Path(".codex/runtime/work")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}\Z")
_DIRECTION = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
_UNORDERED_STRING_LISTS = ("non_goals", "owned_paths", "done_criteria")
_BARE_DIRECTION_ROOTS = {
    "experiments/candidates",
    "tests/experiments/candidates",
    "docs/research/candidates",
    "temp/directions",
}
_REQUIRED = {
    "schema_version",
    "work_id",
    "scope_ref",
    "sender_identity",
    "target_identity",
    "authority_refs",
    "objective",
    "non_goals",
    "owned_paths",
    "done_criteria",
    "effect_refs",
}
_PROTOCOL_NEXT_ACTIONS = {
    "NONE",
    "RESUME_SAME_SLICE",
    "REQUEST_PORTFOLIO_DECISION",
    "REQUEST_EM_DECISION",
    "REQUEST_CM_ENGINEERING",
    "REQUEST_ROOT_ACTION",
    "OBSERVE_EFFECT",
    "WAIT_FOR_REF",
}
_REQUEST_ACTIONS = {
    "REQUEST_PORTFOLIO_DECISION",
    "REQUEST_EM_DECISION",
    "REQUEST_CM_ENGINEERING",
    "REQUEST_ROOT_ACTION",
}
_REUSABLE_TASK_LIFECYCLES = {"CREATED", "RUNNING", "ACTIVE", "PARKED", "IDLE"}
_EFFECT_OPERATIONS = {
    "run_manifest": {"OBSERVE", "EXECUTE", "CANCEL", "PROMOTE"},
    "worktree": {
        "OBSERVE",
        "PROVISION",
        "RECORD_CANDIDATE",
        "PREPARE_INTEGRATION",
        "APPLY_INTEGRATION",
        "PUSH",
        "RELEASE",
        "RETAIN",
    },
    "external_operation": {"OBSERVE", "SEND", "ARCHIVE"},
}
_WORKFLOW_CLERK_IDENTITY = "Workflow-Clerk"
_PORTFOLIO_WRITER_PATHS = {
    "docs/research/portfolio/portfolio.md",
    "docs/research/portfolio/workflow/registry.json",
}


class WorkPacketError(RuntimeError):
    code = 1


class InvalidPacket(WorkPacketError):
    code = 2


class StaleAuthority(WorkPacketError):
    code = 4


class PathRefusal(WorkPacketError):
    code = 5


class PacketConflict(WorkPacketError):
    code = 6


def _json_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize_path(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        raise PathRefusal(f"{label} must be a repository-relative POSIX path")
    if re.match(r"^[A-Za-z]:", value):
        raise PathRefusal(f"{label} must not have an absolute drive prefix")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PathRefusal(f"{label} contains an alias component")
    if any(":" in part for part in parts):
        raise PathRefusal(f"{label} contains a colon or Windows ADS component")
    if any(part.endswith((".", " ")) for part in parts):
        raise PathRefusal(f"{label} contains a Windows-ambiguous trailing dot or space")
    if any(unicodedata.category(character) == "Cc" for character in value):
        raise PathRefusal(f"{label} contains a control character")
    return "/".join(parts)


def _assert_no_alias(path: Path, *, label: str, require_existing: bool) -> None:
    current = path
    while True:
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            info = None
        if info is not None and hmasd_platform.is_reparse_or_symlink(current, info):
            raise PathRefusal(f"{label} traverses a symlink or reparse point: {current}")
        parent = current.parent
        if parent == current:
            break
        current = parent
    if require_existing and not path.is_file():
        raise StaleAuthority(f"{label} does not exist: {path}")


def _repo_path(repo: Path, relative: str, *, label: str, require_existing: bool) -> Path:
    normalized = _normalize_path(relative, label=label)
    candidate = repo.joinpath(*normalized.split("/"))
    try:
        candidate.relative_to(repo)
    except ValueError as exc:
        raise PathRefusal(f"{label} escaped repository") from exc
    _assert_no_alias(candidate, label=label, require_existing=require_existing)
    return candidate


def _normalize_authority_ref(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidPacket(f"{label} must be an object")
    keys = set(value)
    if keys == {"path", "revision"}:
        revision = value["revision"]
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
            raise InvalidPacket(f"{label}.revision must be a non-negative integer")
        return {"path": _normalize_path(value["path"], label=f"{label}.path"), "revision": revision}
    if keys == {"path", "sha256"}:
        digest = value["sha256"]
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise InvalidPacket(f"{label}.sha256 must be a lowercase SHA256")
        return {"path": _normalize_path(value["path"], label=f"{label}.path"), "sha256": digest}
    raise InvalidPacket(f"{label} must contain path and exactly one of revision or sha256")


def _normalize_effect_ref(value: Any, *, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise InvalidPacket(f"{label} must be an object")
    if set(value) == {"path"}:
        return {"path": _normalize_path(value["path"], label=f"{label}.path")}
    keys = set(value)
    if keys not in (
        {"kind", "path", "resource_id"},
        {"kind", "operation", "path", "resource_id"},
    ):
        raise InvalidPacket(
            f"{label} must be legacy path-only or typed kind+path+resource_id with optional operation"
        )
    kind = value["kind"]
    resource_id = value["resource_id"]
    if kind not in _EFFECT_OPERATIONS:
        raise InvalidPacket(f"{label}.kind is unsupported")
    operation = value.get("operation")
    if operation is not None and operation not in _EFFECT_OPERATIONS[kind]:
        raise InvalidPacket(f"{label}.operation is unsupported for {kind}")
    if (
        not isinstance(resource_id, str)
        or not resource_id
        or len(resource_id) > 512
        or any(unicodedata.category(character) == "Cc" for character in resource_id)
    ):
        raise InvalidPacket(f"{label}.resource_id is invalid")
    if kind == "run_manifest" and re.fullmatch(
        r"[a-z0-9][a-z0-9_-]{1,63}/[a-z0-9][a-z0-9_-]{1,63}",
        resource_id,
    ) is None:
        raise InvalidPacket(f"{label}.resource_id is not a run identity")
    if kind == "worktree" and re.fullmatch(
        r"[a-z0-9][a-z0-9_-]{1,63}/[A-Za-z0-9][A-Za-z0-9._-]{0,127}",
        resource_id,
    ) is None:
        raise InvalidPacket(f"{label}.resource_id is not a worktree identity")
    result = {
        "kind": kind,
        "path": _normalize_path(value["path"], label=f"{label}.path"),
        "resource_id": resource_id,
    }
    if operation is not None:
        result["operation"] = operation
    return result


def _normalize_unique(values: Any, *, label: str, item: Callable[[Any, str], Any]) -> list[Any]:
    if not isinstance(values, list):
        raise InvalidPacket(f"{label} must be an array")
    normalized = [item(value, f"{label}[{index}]") for index, value in enumerate(values)]
    ordered = sorted(normalized, key=_json_key)
    if len({_json_key(value) for value in ordered}) != len(ordered):
        raise InvalidPacket(f"{label} contains duplicates")
    return ordered


def normalize_content(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return canonical packet content, excluding ``work_id``."""

    if not isinstance(document, Mapping):
        raise InvalidPacket("packet must be a JSON object")
    allowed = _REQUIRED - {"work_id"}
    unknown = set(document) - _REQUIRED
    missing = allowed - set(document)
    if unknown or missing:
        raise InvalidPacket(
            f"packet keys mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    version = document.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool) or version != SCHEMA_VERSION:
        raise InvalidPacket(f"schema_version must be {SCHEMA_VERSION}")
    objective = document.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        raise InvalidPacket("objective must be a non-empty string")
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "scope_ref": _normalize_authority_ref(document["scope_ref"], label="scope_ref"),
        "sender_identity": document.get("sender_identity"),
        "target_identity": document.get("target_identity"),
        "authority_refs": _normalize_unique(
            document.get("authority_refs"),
            label="authority_refs",
            item=lambda value, label: _normalize_authority_ref(value, label=label),
        ),
        "objective": objective.strip(),
        "effect_refs": _normalize_unique(
            document.get("effect_refs"),
            label="effect_refs",
            item=lambda value, label: _normalize_effect_ref(value, label=label),
        ),
    }
    for identity_key in ("sender_identity", "target_identity"):
        identity = result[identity_key]
        if not isinstance(identity, str) or _IDENTITY.fullmatch(identity) is None:
            raise InvalidPacket(f"{identity_key} is not a safe logical identity")
    if result["target_identity"] == _WORKFLOW_CLERK_IDENTITY:
        raise InvalidPacket(
            "ordinary Work Packet target_identity must not be Workflow-Clerk; "
            "use the dedicated program-generated exception task entry"
        )
    for key in _UNORDERED_STRING_LISTS:
        def normalize_string(value: Any, label: str, *, path: bool = key == "owned_paths") -> str:
            if path:
                return _normalize_path(value, label=label)
            if not isinstance(value, str) or not value.strip():
                raise InvalidPacket(f"{label} must be a non-empty string")
            return value.strip()

        result[key] = _normalize_unique(document.get(key), label=key, item=normalize_string)
    bare_roots = sorted(set(result["owned_paths"]) & _BARE_DIRECTION_ROOTS)
    if bare_roots:
        raise PathRefusal(
            "owned_paths must identify a bounded child below bare direction roots: "
            + ", ".join(bare_roots)
        )
    return result


def packet_id(document: Mapping[str, Any]) -> str:
    """Return the SHA256 identity of canonical content without ``work_id``."""

    return hmasd_state.sha256_bytes(hmasd_state.canonical_bytes(normalize_content(document)))


def build_packet(document: Mapping[str, Any], *, repo: str | os.PathLike[str] = ".") -> dict[str, Any]:
    content = normalize_content(document)
    work_id = hmasd_state.sha256_bytes(hmasd_state.canonical_bytes(content))
    supplied = document.get("work_id")
    if supplied is not None and supplied != work_id:
        raise InvalidPacket("supplied work_id does not match canonical packet content")
    packet = {"work_id": work_id, **content}
    validate_packet(packet, repo=repo)
    return packet


def validate_packet(document: Mapping[str, Any], *, repo: str | os.PathLike[str] = ".") -> dict[str, Any]:
    if set(document) != _REQUIRED:
        missing = _REQUIRED - set(document)
        unknown = set(document) - _REQUIRED
        raise InvalidPacket(f"packet keys mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}")
    packet = build_packet_without_recursion(document)
    repository = Path(repo).absolute()
    _assert_no_alias(repository, label="repository", require_existing=False)
    for label, reference in [("scope_ref", packet["scope_ref"]), *[
        (f"authority_refs[{index}]", ref) for index, ref in enumerate(packet["authority_refs"])
    ]]:
        _repo_path(repository, reference["path"], label=f"{label}.path", require_existing=False)
    for index, ref in enumerate(packet["effect_refs"]):
        _repo_path(repository, ref["path"], label=f"effect_refs[{index}].path", require_existing=False)
    for index, path in enumerate(packet["owned_paths"]):
        _repo_path(repository, path, label=f"owned_paths[{index}]", require_existing=False)
    _validate_direction_consistency(packet)
    return packet


def build_packet_without_recursion(document: Mapping[str, Any]) -> dict[str, Any]:
    content = normalize_content(document)
    expected = hmasd_state.sha256_bytes(hmasd_state.canonical_bytes(content))
    supplied = document.get("work_id")
    if not isinstance(supplied, str) or supplied != expected:
        raise InvalidPacket("work_id does not match canonical packet content")
    return {"work_id": expected, **content}


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_alias(path.parent, label="packet parent", require_existing=False)
    _assert_no_alias(path, label="packet target", require_existing=False)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(hmasd_state.canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        hmasd_platform.fsync_directory(path.parent)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _work_root(repo: Path) -> Path:
    root = repo / WORK_RELATIVE_ROOT
    _assert_no_alias(root, label="work packet runtime", require_existing=False)
    return root


def _lock(path: Path):
    _assert_no_alias(path.parent, label="lock parent", require_existing=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_alias(path.parent, label="lock parent", require_existing=False)
    _assert_no_alias(path, label="lock path", require_existing=False)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        _verify_lock_identity(path, descriptor)
    except Exception:
        os.close(descriptor)
        raise
    return os.fdopen(descriptor, "r+b", buffering=0)


def _verify_lock_identity(path: Path, descriptor: int) -> None:
    _assert_no_alias(path, label="lock path", require_existing=True)
    descriptor_info = os.fstat(descriptor)
    path_info = os.stat(path, follow_symlinks=False)
    if not stat.S_ISREG(descriptor_info.st_mode) or not os.path.samestat(
        descriptor_info, path_info
    ):
        raise PathRefusal("lock path identity changed while opening or locking")


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    _assert_no_alias(path, label=label, require_existing=True)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidPacket(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise InvalidPacket(f"{label} is not a JSON object")
    return value


def publish_packet(
    document: Mapping[str, Any], *, repo: str | os.PathLike[str] = "."
) -> dict[str, Any]:
    """Atomically publish one validated packet from staging to ready."""

    repository = Path(repo).absolute()
    packet = validate_packet(document, repo=repository)
    root = _work_root(repository)
    for child in (root / "staging", root / "ready", root / "locks"):
        _assert_no_alias(child, label="work packet directory", require_existing=False)
        child.mkdir(parents=True, exist_ok=True)
        _assert_no_alias(child, label="work packet directory", require_existing=False)
    work_id = packet["work_id"]
    lock_path = root / "locks" / f"publish-{work_id}.lock"
    with _lock(lock_path) as stream, hmasd_platform.exclusive_file_lock(stream.fileno()):
        _verify_lock_identity(lock_path, stream.fileno())
        ready_dir = root / "ready" / work_id
        ready_packet = ready_dir / "packet.json"
        if ready_packet.is_file():
            existing = validate_packet(_load_json(ready_packet, label="ready packet"), repo=repository)
            if hmasd_state.canonical_bytes(existing) != hmasd_state.canonical_bytes(packet):
                raise PacketConflict("ready work_id has conflicting content")
            return {"ok": True, "operation": "publish", "work_id": work_id, "published": False, "path": str(ready_packet)}
        if ready_dir.exists():
            raise PacketConflict("ready work_id exists without a complete packet")
        staging_dir = root / "staging" / work_id
        if staging_dir.exists():
            _assert_no_alias(staging_dir, label="staging work_id", require_existing=False)
            if not staging_dir.is_dir():
                raise PacketConflict("staging work_id is not a directory")
            staged_packet = staging_dir / "packet.json"
            existing: dict[str, Any] | None = None
            try:
                staged_value = _load_json(staged_packet, label="staged packet")
            except (InvalidPacket, StaleAuthority):
                staged_value = None
            if staged_value is not None:
                try:
                    existing = validate_packet(staged_value, repo=repository)
                except WorkPacketError as exc:
                    raise PacketConflict("staging work_id has conflicting content") from exc
            if existing is None:
                # Staging is explicitly rebuildable runtime transport.  Clean
                # only regular files inside this exact digest directory; an
                # unexpected directory or alias remains a hard refusal.
                for residue in staging_dir.iterdir():
                    _assert_no_alias(residue, label="staging residue", require_existing=False)
                    if not residue.is_file():
                        raise PacketConflict("staging work_id contains unexpected residue")
                    residue.unlink()
                staging_dir.rmdir()
                staging_dir.mkdir()
                _atomic_json(staging_dir / "packet.json", packet)
            else:
                if hmasd_state.canonical_bytes(existing) != hmasd_state.canonical_bytes(packet):
                    raise PacketConflict("staging work_id has conflicting content")
                for residue in staging_dir.iterdir():
                    if residue == staged_packet:
                        continue
                    _assert_no_alias(residue, label="staging residue", require_existing=False)
                    if not residue.is_file():
                        raise PacketConflict("staging work_id contains unexpected residue")
                    residue.unlink()
        else:
            staging_dir.mkdir()
            _atomic_json(staging_dir / "packet.json", packet)
        try:
            os.replace(staging_dir, ready_dir)
        except OSError:
            if not ready_packet.is_file():
                raise
            existing = validate_packet(_load_json(ready_packet, label="ready packet"), repo=repository)
            if hmasd_state.canonical_bytes(existing) != hmasd_state.canonical_bytes(packet):
                raise PacketConflict("concurrent ready work_id has conflicting content")
        hmasd_platform.fsync_directory(ready_dir.parent)
        return {"ok": True, "operation": "publish", "work_id": work_id, "published": True, "path": str(ready_packet)}


def _return_path(repo: Path, work_id: str) -> Path:
    return _work_root(repo) / "returns" / work_id / "return.json"


def _validate_return_witness(
    value: Mapping[str, Any],
    *,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    allowed = {
        "schema_version",
        "work_id",
        "receiver",
        "agent_result",
        "next_packet_draft",
    }
    required = allowed - {"next_packet_draft"}
    if not isinstance(value, Mapping) or not required <= set(value) <= allowed:
        raise InvalidPacket("return witness has invalid fields")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise InvalidPacket(f"return witness schema_version must be {SCHEMA_VERSION}")
    if value.get("work_id") != packet["work_id"]:
        raise PacketConflict("return witness work_id does not match packet")
    receiver = value.get("receiver")
    if not isinstance(receiver, Mapping) or set(receiver) != {
        "logical_identity",
        "generation",
    }:
        raise InvalidPacket("return witness receiver must contain identity and generation")
    identity = receiver.get("logical_identity")
    generation = receiver.get("generation")
    manager = _manager_identity(str(packet["target_identity"]))
    expected_identity = manager[3] if manager is not None else packet["target_identity"]
    if identity != expected_identity:
        raise PacketConflict("return witness receiver does not match packet target")
    if (
        not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 1
    ):
        raise InvalidPacket("return witness receiver generation must be positive")
    agent_result = value.get("agent_result")
    if not isinstance(agent_result, Mapping):
        raise InvalidPacket("return witness agent_result must be an object")
    if agent_result.get("assignment_id") != packet["work_id"]:
        raise PacketConflict("return witness result assignment does not match work_id")
    if agent_result.get("logical_identity") != identity:
        raise PacketConflict("return witness result identity does not match receiver")
    if agent_result.get("generation") != generation:
        raise PacketConflict("return witness result generation does not match receiver")
    draft = value.get("next_packet_draft")
    if "next_packet_draft" in value and not isinstance(draft, Mapping):
        raise InvalidPacket("return witness next_packet_draft must be an object")
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "work_id": packet["work_id"],
        "receiver": {
            "logical_identity": identity,
            "generation": generation,
        },
        "agent_result": dict(agent_result),
    }
    if draft is not None:
        result["next_packet_draft"] = dict(draft)
    return result


def _load_ready_packet(repo: Path, work_id: str) -> dict[str, Any]:
    packet_path = _work_root(repo) / "ready" / work_id / "packet.json"
    _assert_no_alias(packet_path, label="ready packet", require_existing=False)
    if not packet_path.is_file():
        raise InvalidPacket(f"ready packet is missing for work_id {work_id}")
    packet = validate_packet(_load_json(packet_path, label="ready packet"), repo=repo)
    if packet["work_id"] != work_id:
        raise PacketConflict("ready directory does not match work_id")
    return packet


def read_return(
    *, work_id: str, repo: str | os.PathLike[str] = "."
) -> dict[str, Any] | None:
    """Read one exact immutable return witness without scanning siblings."""

    if not isinstance(work_id, str) or _SHA256.fullmatch(work_id) is None:
        raise InvalidPacket("work_id must be a lowercase SHA256")
    repository = Path(repo).absolute()
    packet = _load_ready_packet(repository, work_id)
    path = _return_path(repository, work_id)
    _assert_no_alias(path, label="return witness", require_existing=False)
    if not path.is_file():
        return None
    witness = _validate_return_witness(
        _load_json(path, label="return witness"), packet=packet
    )
    if path.read_bytes() != hmasd_state.canonical_bytes(witness):
        raise PacketConflict("return witness is not canonical JSON")
    return witness


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = [part.casefold() for part in left.split("/")]
    right_parts = [part.casefold() for part in right.split("/")]
    common = min(len(left_parts), len(right_parts))
    return left_parts[:common] == right_parts[:common]


def _packet_authorities(packet: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_path: dict[str, list[dict[str, Any]]] = {}
    references = [packet["scope_ref"], *packet["authority_refs"]]
    for reference in references:
        key = str(reference["path"]).casefold()
        normalized = dict(reference)
        normalized["path"] = key
        by_path.setdefault(key, []).append(normalized)
    return by_path


def _authority_display_path(
    key: str, left: Mapping[str, Any], right: Mapping[str, Any]
) -> str:
    paths = [
        str(reference["path"])
        for packet in (left, right)
        for reference in [packet["scope_ref"], *packet["authority_refs"]]
        if str(reference["path"]).casefold() == key
    ]
    return sorted(paths, key=lambda value: (value.casefold(), value))[0]


def _packet_read_paths(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    reads = [
        {"field": "scope_ref", "path": str(packet["scope_ref"]["path"])},
        *[
            {"field": f"authority_refs[{index}]", "path": str(reference["path"])}
            for index, reference in enumerate(packet["authority_refs"])
        ],
        *[
            {"field": f"effect_refs[{index}]", "path": str(reference["path"])}
            for index, reference in enumerate(packet["effect_refs"])
        ],
    ]
    return sorted(reads, key=_json_key)


def _effect_observations(
    repo: Path, packet: Mapping[str, Any]
) -> tuple[list[hmasd_protocol_contracts.EffectObservation], list[dict[str, Any]]]:
    observations: list[hmasd_protocol_contracts.EffectObservation] = []
    unknown: list[dict[str, Any]] = []
    for reference in packet["effect_refs"]:
        try:
            observation = hmasd_protocol_contracts.observe_effect_ref(repo, reference)
        except hmasd_protocol_contracts.ProtocolContractError as exc:
            unknown.append(
                {
                    "type": "EFFECT_OBSERVATION_UNKNOWN",
                    "path": reference["path"],
                    "code": exc.code,
                }
            )
            continue
        if observation.kind == "legacy" or observation.state == "LEGACY_UNTYPED":
            unknown.append(
                {"type": "EFFECT_UNTYPED", "path": observation.path}
            )
        else:
            observations.append(observation)
            if observation.state == "UNKNOWN":
                unknown.append(
                    {
                        "type": "EFFECT_STATE_UNKNOWN",
                        "kind": observation.kind,
                        "resource_id": observation.resource_id,
                    }
                )
    return observations, unknown


def _compare_packet_pair(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    left_effect_data: tuple[
        list[hmasd_protocol_contracts.EffectObservation], list[dict[str, Any]]
    ],
    right_effect_data: tuple[
        list[hmasd_protocol_contracts.EffectObservation], list[dict[str, Any]]
    ],
) -> dict[str, Any]:
    conflicts: list[dict[str, Any]] = []
    for left_path in left["owned_paths"]:
        for right_path in right["owned_paths"]:
            if _paths_overlap(str(left_path), str(right_path)):
                conflicts.append(
                    {
                        "type": "OWNED_PATH_OVERLAP",
                        "left": left_path,
                        "right": right_path,
                    }
                )
    for writer_side, writer, reader_side, reader in (
        ("left", left, "right", right),
        ("right", right, "left", left),
    ):
        for write_path in writer["owned_paths"]:
            for read in _packet_read_paths(reader):
                if _paths_overlap(str(write_path), read["path"]):
                    conflicts.append(
                        {
                            "type": "READ_WRITE_OVERLAP",
                            "writer": writer_side,
                            "write": write_path,
                            "reader": reader_side,
                            "read": read["path"],
                            "read_field": read["field"],
                        }
                    )
    left_authorities = _packet_authorities(left)
    right_authorities = _packet_authorities(right)
    for path in sorted(set(left_authorities) & set(right_authorities)):
        left_bindings = sorted(
            {_json_key(value) for value in left_authorities[path]}
        )
        right_bindings = sorted(
            {_json_key(value) for value in right_authorities[path]}
        )
        if left_bindings != right_bindings:
            conflicts.append(
                {
                    "type": "AUTHORITY_BINDING_CONFLICT",
                    "path": _authority_display_path(path, left, right),
                    "left": [json.loads(value) for value in left_bindings],
                    "right": [json.loads(value) for value in right_bindings],
                }
            )
    left_effects, left_unknown = left_effect_data
    right_effects, right_unknown = right_effect_data
    left_resources = {(effect.kind, effect.resource_id) for effect in left_effects}
    right_resources = {(effect.kind, effect.resource_id) for effect in right_effects}
    for kind, resource_id in sorted(left_resources & right_resources):
        conflicts.append(
            {
                "type": "EFFECT_RESOURCE_OVERLAP",
                "kind": kind,
                "resource_id": resource_id,
            }
        )
    conflicts = [json.loads(value) for value in sorted({_json_key(value) for value in conflicts})]
    reasons = [*conflicts, *left_unknown, *right_unknown]
    reasons.sort(key=_json_key)
    if conflicts:
        outcome = "CONFLICT"
    elif left_unknown or right_unknown:
        outcome = "UNKNOWN"
    else:
        outcome = "DISJOINT"
    return {
        "left_work_id": left["work_id"],
        "right_work_id": right["work_id"],
        "outcome": outcome,
        "reasons": reasons,
    }


def compare_work_ids(
    repo: str | os.PathLike[str], work_ids: Sequence[str]
) -> dict[str, Any]:
    """Compare explicit ready Work Packets without discovering other work."""

    if isinstance(work_ids, (str, bytes)) or not isinstance(work_ids, Sequence):
        raise InvalidPacket("compare requires at least two explicit work_ids")
    ordered = sorted(work_ids)
    if len(ordered) < 2:
        raise InvalidPacket("compare requires at least two explicit work_ids")
    if len(set(ordered)) != len(ordered):
        raise InvalidPacket("compare work_ids must be unique")
    if any(not isinstance(work_id, str) or _SHA256.fullmatch(work_id) is None for work_id in ordered):
        raise InvalidPacket("each work_id must be a lowercase SHA256")
    repository = Path(repo).absolute()
    packets = {
        work_id: _load_ready_packet(repository, work_id) for work_id in ordered
    }
    packet_conflicts = [
        conflict
        for work_id in ordered
        for conflict in [_packet_precondition_conflict(repository, packets[work_id])]
        if conflict is not None
    ]
    effects = {
        work_id: _effect_observations(repository, packet)
        for work_id, packet in packets.items()
    }
    pairs = [
        _compare_packet_pair(
            packets[left], packets[right], effects[left], effects[right]
        )
        for index, left in enumerate(ordered)
        for right in ordered[index + 1 :]
    ]
    outcomes = {pair["outcome"] for pair in pairs}
    outcome = (
        "CONFLICT"
        if packet_conflicts or "CONFLICT" in outcomes
        else "UNKNOWN"
        if "UNKNOWN" in outcomes
        else "DISJOINT"
    )
    return {
        "ok": True,
        "operation": "compare",
        "work_ids": ordered,
        "outcome": outcome,
        "pairs": pairs,
        "packet_conflicts": packet_conflicts,
    }


def _authority_matches(repo: Path, reference: Mapping[str, Any], *, label: str) -> None:
    path = _repo_path(repo, str(reference["path"]), label=label, require_existing=True)
    raw = path.read_bytes()
    if "sha256" in reference:
        observed = hmasd_state.sha256_bytes(raw)
        if observed != reference["sha256"]:
            raise StaleAuthority(f"{label} sha256 advanced")
        return
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidPacket(f"{label} revision reference is not JSON") from exc
    if not isinstance(value, dict) or value.get("revision") != reference["revision"]:
        raise StaleAuthority(f"{label} revision advanced")


def _current_git_head(repo: Path) -> str:
    try:
        value = hmasd_worktree.observe_current_head(repo)
    except hmasd_worktree.WorktreeError as exc:
        raise InvalidPacket(f"cannot observe current Git HEAD: {exc}") from exc
    if re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", value) is None:
        raise InvalidPacket("current Git HEAD is not a full commit SHA")
    return value


def _shared_core_paths(repo: Path, packet: Mapping[str, Any]) -> list[str]:
    try:
        facts = hmasd_worktree.observe_path_classifications(repo, packet["owned_paths"])
    except hmasd_worktree.WorktreeError as exc:
        raise InvalidPacket(f"cannot classify owned_paths: {exc}") from exc
    return sorted(
        str(item["path"])
        for item in facts["classifications"]
        if item["classification"] == "shared-core"
        and not (
            packet["target_identity"] == "Portfolio"
            and str(item["path"]).casefold() in _PORTFOLIO_WRITER_PATHS
        )
    )


def _shared_core_target_allowed(target_identity: str) -> bool:
    if target_identity == "Root":
        return True
    manager = _manager_identity(target_identity)
    return (
        manager is not None
        and manager[0] == "cm"
        and target_identity == manager[3]
    )


def _shared_core_authority_path_allowed(
    packet: Mapping[str, Any], path: str
) -> bool:
    normalized = path.casefold()
    if normalized in {
        "agents.md",
        "docs/project/workflow_protocol.md",
        "docs/research/portfolio/portfolio.md",
    }:
        return True
    match = re.fullmatch(
        r"docs/research/candidates/([a-z0-9][a-z0-9_-]{1,63})/direction\.md",
        normalized,
    )
    if match is None:
        return False
    if packet["target_identity"] == "Root":
        return True
    manager = _manager_identity(str(packet["target_identity"]))
    return manager is not None and manager[0] == "cm" and manager[1] == match.group(1)


def _shared_core_error_field(code: str, *, prefix: str = "") -> str:
    if code == "SHARED_CORE_TARGET_FORBIDDEN":
        field = "target_identity"
    elif code.startswith("SHARED_CORE_AUTHORITY"):
        field = "authority_refs"
    else:
        field = "owned_paths"
    return f"{prefix}.{field}" if prefix else field


def _derived_allowed_effects(packet: Mapping[str, Any]) -> list[str]:
    effects = {"MODIFY_PATHS"}
    for reference in packet["effect_refs"]:
        kind = reference.get("kind")
        if not isinstance(kind, str):
            raise hmasd_protocol_contracts.ProtocolContractError(
                "UNTYPED_EFFECT_REF",
                "shared-core action cannot derive an allowed effect from a legacy ref",
            )
        operation = reference.get("operation")
        effects.add(
            f"{kind.upper()}_{operation}"
            if isinstance(operation, str)
            else f"OBSERVE_{kind.upper()}"
        )
    return sorted(effects)


def _expected_shared_core_record(
    repo: Path, packet: Mapping[str, Any]
) -> dict[str, Any] | None:
    shared_paths = _shared_core_paths(repo, packet)
    if not shared_paths:
        return None
    target_identity = str(packet["target_identity"])
    if not _shared_core_target_allowed(target_identity):
        raise hmasd_protocol_contracts.ProtocolContractError(
            "SHARED_CORE_TARGET_FORBIDDEN",
            "shared-core owned_paths require target_identity Root or one canonical CM-<direction>",
        )
    return hmasd_protocol_contracts.build_shared_core_action_record(
        decision_owner="Root",
        base_sha=_current_git_head(repo),
        paths=packet["owned_paths"],
        objective=packet["objective"],
        non_goals=packet["non_goals"],
        allowed_effects=_derived_allowed_effects(packet),
    )


def _validate_shared_core_packet(
    repo: Path, packet: Mapping[str, Any]
) -> dict[str, Any] | None:
    expected = _expected_shared_core_record(repo, packet)
    if expected is None:
        return None
    markdown_refs = [
        reference
        for reference in [packet["scope_ref"], *packet["authority_refs"]]
        if str(reference["path"]).lower().endswith(".md")
        and "sha256" in reference
    ]
    if not markdown_refs:
        raise hmasd_protocol_contracts.ProtocolContractError(
            "SHARED_CORE_AUTHORITY_REQUIRED",
            "CM/Root shared-core work requires a fresh Markdown authority ref",
        )
    allowed_refs = [
        reference
        for reference in markdown_refs
        if _shared_core_authority_path_allowed(packet, str(reference["path"]))
    ]
    if not allowed_refs:
        raise hmasd_protocol_contracts.ProtocolContractError(
            "SHARED_CORE_AUTHORITY_PATH_FORBIDDEN",
            "shared-core records require an exact v1 durable Markdown authority path",
        )
    tracked_refs: list[dict[str, Any]] = []
    for reference in allowed_refs:
        try:
            tracked = hmasd_worktree.path_is_tracked_at_commit(
                repo, expected["base_sha"], str(reference["path"])
            )
        except hmasd_worktree.WorktreeError as exc:
            raise hmasd_protocol_contracts.ProtocolContractError(
                "SHARED_CORE_BASE_OBSERVATION_FAILED", str(exc)
            ) from exc
        if tracked:
            tracked_refs.append(reference)
    if not tracked_refs:
        raise hmasd_protocol_contracts.ProtocolContractError(
            "SHARED_CORE_AUTHORITY_NOT_TRACKED_AT_BASE",
            "no allowed Markdown authority ref was tracked in the record base_sha",
        )
    matches: list[dict[str, Any]] = []
    saw_record = False
    for reference in tracked_refs:
        path = _repo_path(
            repo,
            str(reference["path"]),
            label="shared-core authority",
            require_existing=True,
        )
        try:
            raw = path.read_bytes()
        except (OSError, UnicodeError) as exc:
            raise hmasd_protocol_contracts.ProtocolContractError(
                "INVALID_SHARED_CORE_MARKDOWN", str(exc)
            ) from exc
        observed_sha = hmasd_state.sha256_bytes(raw)
        if observed_sha != reference["sha256"]:
            raise hmasd_protocol_contracts.ProtocolContractError(
                "SHARED_CORE_AUTHORITY_STALE",
                "shared-core authority bytes advanced after reference validation",
            )
        try:
            markdown = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise hmasd_protocol_contracts.ProtocolContractError(
                "INVALID_SHARED_CORE_MARKDOWN", str(exc)
            ) from exc
        try:
            records = hmasd_protocol_contracts.parse_shared_core_action_records(markdown)
        except hmasd_protocol_contracts.ProtocolContractError as exc:
            if exc.code == "SHARED_CORE_RECORD_NOT_FOUND":
                continue
            raise
        saw_record = True
        matches.extend(record for record in records if record == expected)
    if len(matches) != 1:
        code = (
            "SHARED_CORE_RECORD_NOT_UNIQUE"
            if len(matches) > 1
            else "SHARED_CORE_RECORD_NOT_FOUND"
        )
        detail = (
            f"found {len(matches)} exact Root records"
            if saw_record
            else "no structured shared-core record exists in fresh Markdown refs"
        )
        raise hmasd_protocol_contracts.ProtocolContractError(code, detail)
    return matches[0]


def build_shared_core_record(
    document: Mapping[str, Any], *, repo: str | os.PathLike[str] = "."
) -> dict[str, Any]:
    """Render the exact Root confirmation record for one packet draft."""

    repository = Path(repo).absolute()
    packet = normalize_content(document)
    record = _expected_shared_core_record(repository, packet)
    if record is None:
        raise InvalidPacket("packet does not require shared-core confirmation")
    return {
        "ok": True,
        "operation": "shared-core-record",
        "record": record,
        "fence": hmasd_protocol_contracts.render_shared_core_action_record(record),
    }


def _packet_precondition_conflict(
    repo: Path, packet: Mapping[str, Any]
) -> dict[str, Any] | None:
    references = [("scope_ref", packet["scope_ref"]), *[
        (f"authority_refs[{index}]", reference)
        for index, reference in enumerate(packet["authority_refs"])
    ]]
    for field_path, reference in references:
        try:
            _authority_matches(repo, reference, label=field_path)
        except StaleAuthority:
            return {
                "work_id": packet["work_id"],
                "code": "STALE_AUTHORITY",
                "field_path": field_path,
            }
        except WorkPacketError:
            return {
                "work_id": packet["work_id"],
                "code": "INVALID_AUTHORITY_REF",
                "field_path": field_path,
            }
    try:
        _validate_shared_core_packet(repo, packet)
    except hmasd_protocol_contracts.ProtocolContractError as exc:
        return {
            "work_id": packet["work_id"],
            "code": exc.code,
            "field_path": _shared_core_error_field(exc.code),
        }
    return None


def load_observed_tasks(
    source: Sequence[Mapping[str, Any]] | str | os.PathLike[str] | None = None,
    *,
    repo: str | os.PathLike[str] = ".",
) -> list[dict[str, Any]]:
    """Load a read-only runtime task observation or return an empty snapshot."""

    if source is None:
        path = Path(repo).absolute() / ".codex" / "runtime" / "tasks.json"
        if not path.is_file():
            return []
        _assert_no_alias(path, label="observed task snapshot", require_existing=True)
        value: Any = _load_json(path, label="observed task snapshot")
    elif isinstance(source, (str, os.PathLike)):
        path = Path(source)
        if not path.is_absolute():
            path = Path(repo).absolute() / path
        value = _load_json(path, label="observed task snapshot")
    elif isinstance(source, Sequence):
        value = list(source)
    else:
        raise InvalidPacket("observed_tasks must be a sequence or JSON path")
    if isinstance(value, Mapping):
        if not isinstance(value.get("tasks"), list):
            raise InvalidPacket("observed task snapshot must contain a tasks array")
        value = value["tasks"]
    if not isinstance(value, list):
        raise InvalidPacket("observed_tasks must be an array")
    tasks: list[dict[str, Any]] = []
    for index, task in enumerate(value):
        if not isinstance(task, Mapping):
            raise InvalidPacket(f"observed_tasks[{index}] must be an object")
        tasks.append(dict(task))
    return tasks


def _manager_identity(
    identity: str,
) -> tuple[str, str | None, int | None, str] | None:
    if identity == "Portfolio":
        return "portfolio", None, None, "Portfolio"
    match = re.fullmatch(r"(EM|CM)/([a-z0-9][a-z0-9_-]{1,63})/g([1-9][0-9]*)", identity)
    if match is not None:
        kind = match.group(1).lower()
        direction = match.group(2)
        return kind, direction, int(match.group(3)), f"{match.group(1)}-{direction}"
    for prefix, kind in (("EM-", "em"), ("CM-", "cm")):
        if identity.startswith(prefix):
            direction = identity[len(prefix) :]
            if _DIRECTION.fullmatch(direction) is not None:
                return kind, direction, None, identity
    return None


def _path_direction(path: str) -> str | None:
    parts = path.split("/")
    for prefix in (("docs", "research", "candidates"), ("temp", "directions")):
        if tuple(parts[: len(prefix)]) == prefix and len(parts) > len(prefix):
            direction = parts[len(prefix)]
            if _DIRECTION.fullmatch(direction) is not None:
                return direction
    return None


def _validate_direction_consistency(packet: Mapping[str, Any]) -> None:
    scope_direction = _path_direction(str(packet["scope_ref"]["path"]))
    manager = _manager_identity(str(packet["target_identity"]))
    target_direction = (
        manager[1]
        if manager is not None and manager[0] in {"em", "cm"}
        else None
    )
    if (
        scope_direction is not None
        and target_direction is not None
        and scope_direction != target_direction
    ):
        raise InvalidPacket(
            "scope_ref direction does not match EM/CM target direction"
        )
    expected_direction = scope_direction or target_direction
    if expected_direction is None:
        return
    for index, path in enumerate(packet["owned_paths"]):
        owned_direction = _path_direction(str(path))
        if owned_direction is not None and owned_direction != expected_direction:
            raise InvalidPacket(
                f"owned_paths[{index}] direction does not match packet direction"
            )


def resolve_target_task(
    target_identity: str,
    observed_tasks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Resolve one logical target without creating or mutating a task."""

    manager = _manager_identity(target_identity)
    canonical_identity = manager[3] if manager is not None else target_identity
    nonterminal_scope: list[dict[str, Any]] = []
    if manager is not None:
        kind, direction, _, _ = manager
        nonterminal_scope = [
            dict(task)
            for task in observed_tasks
            if task.get("kind") == kind
            and (direction is None or task.get("direction_id") == direction)
            and task.get("lifecycle") not in {"COMPLETED", "RETIRED"}
        ]
    exact = [
        dict(task)
        for task in observed_tasks
        if task.get("logical_identity") == canonical_identity
    ]
    if len(nonterminal_scope) > 1:
        identities = sorted(
            str(task.get("logical_identity", "")) for task in nonterminal_scope
        )
        return {
            "status": "TASK_IDENTITY_CONFLICT",
            "logical_identity": canonical_identity,
            "reason": "multiple observed tasks represent the same non-terminal manager scope: "
            + ", ".join(identities),
        }
    if len(exact) == 1:
        task = exact[0]
        generation = task.get("generation")
        thread_id = task.get("thread_id")
        compatible = (
            isinstance(generation, int)
            and not isinstance(generation, bool)
            and generation >= 1
            and task.get("lifecycle") in _REUSABLE_TASK_LIFECYCLES
            and isinstance(thread_id, str)
            and bool(thread_id.strip())
        )
        if manager is not None:
            kind, direction, expected_generation, _ = manager
            compatible = compatible and task.get("kind") == kind
            if direction is not None:
                compatible = compatible and task.get("direction_id") == direction
            if expected_generation is not None:
                compatible = compatible and generation == expected_generation
        if nonterminal_scope and nonterminal_scope[0].get("logical_identity") != canonical_identity:
            compatible = False
        if compatible:
            return {
                "status": "REUSE",
                "logical_identity": canonical_identity,
                "kind": task.get("kind"),
                "generation": generation,
                "lifecycle": task.get("lifecycle"),
                "thread_id": thread_id,
            }
        return {
            "status": "TASK_IDENTITY_CONFLICT",
            "logical_identity": canonical_identity,
            "reason": "exact logical identity has incompatible kind, direction, generation, lifecycle, or task locator",
        }
    if len(exact) > 1:
        return {
            "status": "TASK_IDENTITY_CONFLICT",
            "logical_identity": canonical_identity,
            "reason": "multiple observed tasks use the same logical identity",
        }
    if manager is None:
        return {
            "status": "TASK_IDENTITY_CONFLICT",
            "logical_identity": canonical_identity,
            "reason": "non-manager target is absent and cannot be created by reconcile",
        }
    kind, direction, expected_generation, _ = manager
    if nonterminal_scope:
        return {
            "status": "TASK_IDENTITY_CONFLICT",
            "logical_identity": canonical_identity,
            "reason": "manager scope is already represented by a different logical identity",
        }
    return {
        "status": "CREATE_TASK",
        "logical_identity": canonical_identity,
        "kind": kind,
        "direction_id": direction,
        "generation": expected_generation or 1,
    }


def _observe_effect_refs(
    repo: Path, references: Sequence[Mapping[str, Any]], *, field_prefix: str
) -> tuple[list[str], dict[str, Any] | None]:
    unknown: list[str] = []
    for index, reference in enumerate(references):
        field_path = f"{field_prefix}[{index}]"
        if set(reference) == {"path"}:
            return unknown, {
                "code": "UNTYPED_EFFECT_REF",
                "field_path": field_path,
                "expected": "typed kind+path+resource_id Effect ref",
                "actual": reference,
                "ref": dict(reference),
            }
        try:
            observation = hmasd_protocol_contracts.observe_effect_ref(repo, reference)
        except hmasd_protocol_contracts.ProtocolContractError as exc:
            return unknown, {
                "code": exc.code,
                "field_path": field_path,
                "expected": "valid typed Effect contract",
                "actual": exc.detail,
                "ref": dict(reference),
            }
        if observation.state == "UNKNOWN":
            unknown.append(observation.path)
    return unknown, None


def _plan_packet(
    repo: Path,
    packet: Mapping[str, Any],
    observed_tasks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return one deterministic plan without executing any effect."""

    _authority_matches(repo, packet["scope_ref"], label="scope_ref")
    for index, reference in enumerate(packet["authority_refs"]):
        _authority_matches(repo, reference, label=f"authority_refs[{index}]")
    task_resolution = resolve_target_task(str(packet["target_identity"]), observed_tasks)
    resolution_status = task_resolution["status"]
    plan = {
        "verb": "DISPATCH_EXISTING",
        "delivery_key": packet["work_id"],
        "delivery_semantics": "AT_LEAST_ONCE_IDEMPOTENT_INTAKE",
        "unknown_effect_refs": [],
        "work_id": packet["work_id"],
        "target_identity": task_resolution["logical_identity"],
        "requested_target_identity": packet["target_identity"],
        "task_resolution": task_resolution,
    }
    try:
        shared_record = _validate_shared_core_packet(repo, packet)
    except hmasd_protocol_contracts.ProtocolContractError as exc:
        field_path = _shared_core_error_field(exc.code)
        return _protocol_defect(
            plan,
            code=exc.code,
            field_path=field_path,
            expected=(
                "Root or canonical CM target"
                if field_path == "target_identity"
                else "one exact fresh Root shared-core record"
            ),
            actual=exc.detail,
        )
    if shared_record is not None:
        plan["shared_core_action_digest"] = shared_record["action_digest"]
    if resolution_status == "TASK_IDENTITY_CONFLICT":
        plan["verb"] = "CONFLICT"
        plan["conflict_type"] = "TASK_IDENTITY_CONFLICT"
        return plan
    unknown, effect_defect = _observe_effect_refs(
        repo, packet["effect_refs"], field_prefix="effect_refs"
    )
    if effect_defect is not None:
        return _protocol_defect(
            plan,
            **effect_defect,
            failure_scope="effect",
        )
    plan["unknown_effect_refs"] = unknown
    if unknown:
        plan["verb"] = "OBSERVE_EFFECT_ONLY"
    elif resolution_status == "CREATE_TASK":
        plan["verb"] = "CREATE_TASK_INTENT"
    return plan


def _stable_stale_reason(error: StaleAuthority) -> str:
    """Remove host-local path data from a stale-authority diagnostic."""

    reason = str(error)
    marker = " does not exist:"
    if marker in reason:
        return reason.split(marker, 1)[0] + " does not exist"
    return reason


def _stable_protocol_actual(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _stable_protocol_actual(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_stable_protocol_actual(item) for item in value]
    if isinstance(value, str):
        if value.startswith(("/", "\\\\")) or re.match(r"^[A-Za-z]:[\\/]", value):
            return "<absolute-path>"
        value = re.sub(r"[A-Za-z]:[\\/][^\r\n]*", "<absolute-path>", value)
        value = re.sub(r"(?<![A-Za-z0-9._-])/{1,2}[^\r\n,;)]*", "<absolute-path>", value)
        return re.sub(r"(?<![A-Za-z0-9._-])\\\\[^\r\n,;)]*", "<absolute-path>", value)
    return value


def _protocol_defect(
    base_plan: Mapping[str, Any],
    *,
    code: str,
    field_path: str,
    expected: Any,
    actual: Any,
    failure_scope: str = "feature",
    ref: Any = None,
) -> dict[str, Any]:
    plan = dict(base_plan)
    plan["verb"] = "CONFLICT"
    plan["conflict_type"] = "PROTOCOL_DEFECT"
    plan["defect"] = {
        "code": code,
        "field_path": field_path,
        "expected": expected,
        "actual": _stable_protocol_actual(actual),
        "ref": _stable_protocol_actual(ref),
        "failure_scope": failure_scope,
        "producing_command": "hmasd_work_packet.reconcile_once",
        "responsible_owner": "Root",
    }
    return plan


def _state_error_field(error: hmasd_state.StateError) -> str:
    message = str(error)
    for field in (
        "failure_scope",
        "failure_ref",
        "assignment_id",
        "logical_identity",
        "generation",
        "changed_paths",
        "next_action",
    ):
        if field in message:
            return field
    match = re.match(r"^\$\.([A-Za-z0-9_]+)", message)
    return match.group(1) if match is not None else "agent_result"


def _path_is_within(path: str, owned_root: str) -> bool:
    path_parts = path.casefold().split("/")
    root_parts = owned_root.casefold().split("/")
    return len(path_parts) >= len(root_parts) and path_parts[: len(root_parts)] == root_parts


def _iter_structured_refs(value: Any, field_path: str):
    if isinstance(value, Mapping):
        if "path" in value and "sha256" in value:
            yield field_path, value
            return
        for key, item in value.items():
            yield from _iter_structured_refs(item, f"{field_path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_structured_refs(item, f"{field_path}[{index}]")


def _absolute_string_path(value: Any, field_path: str) -> str | None:
    if isinstance(value, str):
        if value.startswith(("/", "\\\\")) or re.match(r"^[A-Za-z]:[\\/]", value):
            return field_path
        return None
    if isinstance(value, Mapping):
        for key, item in value.items():
            found = _absolute_string_path(item, f"{field_path}.{key}")
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found = _absolute_string_path(item, f"{field_path}[{index}]")
            if found is not None:
                return found
    return None


def _packet_direction(packet: Mapping[str, Any]) -> str | None:
    scope_direction = _path_direction(str(packet["scope_ref"]["path"]))
    if scope_direction is not None:
        return scope_direction
    manager = _manager_identity(str(packet["target_identity"]))
    return manager[1] if manager is not None else None


def _draft_target_matches(
    action_kind: str,
    target_identity: Any,
    inbound_packet: Mapping[str, Any],
) -> bool:
    if not isinstance(target_identity, str):
        return False
    if action_kind == "REQUEST_PORTFOLIO_DECISION":
        return target_identity == "Portfolio"
    if action_kind == "REQUEST_ROOT_ACTION":
        return target_identity == "Root"
    manager = _manager_identity(target_identity)
    if manager is None:
        return False
    expected_kind = "em" if action_kind == "REQUEST_EM_DECISION" else "cm"
    inbound_direction = _packet_direction(inbound_packet)
    return manager[0] == expected_kind and (
        inbound_direction is None or manager[1] == inbound_direction
    )


def _bind_agent_result(
    repo: Path,
    packet: Mapping[str, Any],
    base_plan: Mapping[str, Any],
    agent_result: Mapping[str, Any],
    next_packet_draft: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if base_plan.get("task_resolution", {}).get("status") != "REUSE":
        return _protocol_defect(
            base_plan,
            code="RESULT_TASK_NOT_REUSED",
            field_path="task_resolution.status",
            expected="REUSE",
            actual=base_plan.get("task_resolution", {}).get("status"),
        )
    try:
        hmasd_state.validate_document("agent_result", agent_result)
    except hmasd_state.StateError as exc:
        return _protocol_defect(
            base_plan,
            code="INVALID_AGENT_RESULT",
            field_path=_state_error_field(exc),
            expected="valid agent_result",
            actual=str(exc),
        )

    resolution = base_plan["task_resolution"]
    checks = (
        (
            "assignment_id",
            packet["work_id"],
            agent_result["assignment_id"],
            "ASSIGNMENT_ID_MISMATCH",
        ),
        (
            "logical_identity",
            resolution["logical_identity"],
            agent_result["logical_identity"],
            "RESULT_IDENTITY_MISMATCH",
        ),
        (
            "generation",
            resolution["generation"],
            agent_result["generation"],
            "RESULT_GENERATION_MISMATCH",
        ),
    )
    for field_path, expected, actual, code in checks:
        if actual != expected:
            return _protocol_defect(
                base_plan,
                code=code,
                field_path=field_path,
                expected=expected,
                actual=actual,
            )

    for collection_name in ("state_refs", "artifact_refs"):
        for index, reference in enumerate(agent_result[collection_name]):
            field_path = f"{collection_name}[{index}]"
            if not isinstance(reference, Mapping) or set(reference) != {"path", "sha256"}:
                return _protocol_defect(
                    base_plan,
                    code="INVALID_RESULT_REF",
                    field_path=field_path,
                    expected="path+sha256 mapping",
                    actual=reference,
                )
            try:
                _authority_matches(repo, reference, label=field_path)
            except (OSError, WorkPacketError) as exc:
                return _protocol_defect(
                    base_plan,
                    code="STALE_RESULT_REF",
                    field_path=field_path,
                    expected="fresh path+sha256 ref",
                    actual=str(exc),
                )
    for field_path, reference in _iter_structured_refs(
        agent_result["payload"], "payload"
    ):
        try:
            _authority_matches(repo, reference, label=field_path)
        except (OSError, WorkPacketError) as exc:
            return _protocol_defect(
                base_plan,
                code="STALE_RESULT_REF",
                field_path=field_path,
                expected="fresh path+sha256 ref",
                actual=str(exc),
            )

    changed_paths: list[str] = []
    for index, path in enumerate(agent_result["changed_paths"]):
        try:
            changed_paths.append(
                _normalize_path(path, label=f"changed_paths[{index}]")
            )
        except PathRefusal as exc:
            return _protocol_defect(
                base_plan,
                code="INVALID_CHANGED_PATH",
                field_path=f"changed_paths[{index}]",
                expected="strict repository-relative POSIX path",
                actual=str(exc),
            )
    changed_path_keys = [path.casefold() for path in changed_paths]
    if len(set(changed_path_keys)) != len(changed_path_keys):
        return _protocol_defect(
            base_plan,
            code="DUPLICATE_CHANGED_PATH",
            field_path="changed_paths",
            expected="unique Windows-casefolded repository-relative paths",
            actual=changed_paths,
        )
    owned_paths = [
        _normalize_path(path, label=f"owned_paths[{index}]")
        for index, path in enumerate(packet["owned_paths"])
    ]
    outside = [
        path
        for path in changed_paths
        if not any(_path_is_within(path, root) for root in owned_paths)
    ]
    if outside:
        return _protocol_defect(
            base_plan,
            code="CHANGED_PATH_OUTSIDE_OWNERSHIP",
            field_path="changed_paths",
            expected=owned_paths,
            actual=outside,
        )
    payload = agent_result["payload"]
    if payload["kind"] in {"git", "implementation"}:
        payload_changed_paths: list[str] = []
        for index, path in enumerate(payload["changed_paths"]):
            try:
                payload_changed_paths.append(
                    _normalize_path(path, label=f"payload.changed_paths[{index}]")
                )
            except PathRefusal as exc:
                return _protocol_defect(
                    base_plan,
                    code="INVALID_CHANGED_PATH",
                    field_path=f"payload.changed_paths[{index}]",
                    expected="strict repository-relative POSIX path",
                    actual=str(exc),
                )
        payload_changed_path_keys = [path.casefold() for path in payload_changed_paths]
        if len(set(payload_changed_path_keys)) != len(payload_changed_path_keys):
            return _protocol_defect(
                base_plan,
                code="DUPLICATE_CHANGED_PATH",
                field_path="payload.changed_paths",
                expected="unique Windows-casefolded repository-relative paths",
                actual=payload_changed_paths,
            )
        if set(payload_changed_path_keys) != set(changed_path_keys):
            return _protocol_defect(
                base_plan,
                code="PAYLOAD_CHANGED_PATHS_MISMATCH",
                field_path="payload.changed_paths",
                expected=sorted(changed_paths, key=str.casefold),
                actual=sorted(payload_changed_paths, key=str.casefold),
            )

    next_action = agent_result["next_action"]
    if next_action is None:
        return _protocol_defect(
            base_plan,
            code="NEXT_ACTION_REQUIRED",
            field_path="next_action",
            expected="non-null next_action",
            actual=None,
        )
    action_kind = next_action["kind"]
    if action_kind not in _PROTOCOL_NEXT_ACTIONS:
        return _protocol_defect(
            base_plan,
            code="UNSUPPORTED_NEXT_ACTION",
            field_path="next_action.kind",
            expected=sorted(_PROTOCOL_NEXT_ACTIONS),
            actual=action_kind,
        )
    absolute_ref_path = _absolute_string_path(
        next_action["input_refs"], "next_action.input_refs"
    )
    if absolute_ref_path is not None:
        return _protocol_defect(
            base_plan,
            code="ABSOLUTE_INPUT_REF",
            field_path=absolute_ref_path,
            expected="opaque or repository-relative ref",
            actual=next_action["input_refs"],
        )
    allowed_statuses = {
        "NONE": {"COMPLETED"},
        "RESUME_SAME_SLICE": {"PARTIAL"},
        "WAIT_FOR_REF": {"PARTIAL", "BLOCKED"},
    }.get(action_kind)
    if allowed_statuses is not None and agent_result["status"] not in allowed_statuses:
        return _protocol_defect(
            base_plan,
            code="STATUS_ACTION_MISMATCH",
            field_path="status",
            expected=sorted(allowed_statuses),
            actual=agent_result["status"],
        )

    if action_kind in _REQUEST_ACTIONS:
        if next_packet_draft is None:
            return _protocol_defect(
                base_plan,
                code="NEXT_PACKET_DRAFT_REQUIRED",
                field_path="next_packet_draft",
                expected="complete Work Packet draft",
                actual=None,
            )
        missing = sorted((_REQUIRED - {"work_id"}) - set(next_packet_draft))
        if missing:
            field = missing[0]
            return _protocol_defect(
                base_plan,
                code="INVALID_NEXT_PACKET_DRAFT",
                field_path=f"next_packet_draft.{field}",
                expected="present",
                actual=None,
            )
        if next_packet_draft.get("sender_identity") != agent_result["logical_identity"]:
            return _protocol_defect(
                base_plan,
                code="NEXT_PACKET_SENDER_MISMATCH",
                field_path="next_packet_draft.sender_identity",
                expected=agent_result["logical_identity"],
                actual=next_packet_draft.get("sender_identity"),
            )
        if next_packet_draft.get("target_identity") == _WORKFLOW_CLERK_IDENTITY:
            return _protocol_defect(
                base_plan,
                code="ORDINARY_PACKET_CLERK_TARGET",
                field_path="next_packet_draft.target_identity",
                expected="Root, Portfolio, or the matching EM/CM identity",
                actual=_WORKFLOW_CLERK_IDENTITY,
            )
        if not _draft_target_matches(
            action_kind, next_packet_draft.get("target_identity"), packet
        ):
            return _protocol_defect(
                base_plan,
                code="NEXT_PACKET_TARGET_MISMATCH",
                field_path="next_packet_draft.target_identity",
                expected=action_kind,
                actual=next_packet_draft.get("target_identity"),
                failure_scope="direction",
            )
        try:
            canonical_draft = build_packet(next_packet_draft, repo=repo)
        except WorkPacketError as exc:
            return _protocol_defect(
                base_plan,
                code="INVALID_NEXT_PACKET_DRAFT",
                field_path="next_packet_draft",
                expected="valid Work Packet draft",
                actual=str(exc),
            )
        if canonical_draft["work_id"] == packet["work_id"]:
            return _protocol_defect(
                base_plan,
                code="NEXT_PACKET_SELF_CYCLE",
                field_path="next_packet_draft.work_id",
                expected="different from inbound work_id",
                actual=canonical_draft["work_id"],
            )
        expected_input_refs = [canonical_draft["work_id"]]
        if next_action["input_refs"] != expected_input_refs:
            return _protocol_defect(
                base_plan,
                code="NEXT_PACKET_BINDING_MISMATCH",
                field_path="next_action.input_refs",
                expected=expected_input_refs,
                actual=next_action["input_refs"],
            )
        try:
            _authority_matches(repo, canonical_draft["scope_ref"], label="scope_ref")
            for index, reference in enumerate(canonical_draft["authority_refs"]):
                _authority_matches(repo, reference, label=f"authority_refs[{index}]")
        except StaleAuthority as exc:
            field_path = (
                "next_packet_draft.scope_ref"
                if str(exc).startswith("scope_ref")
                else "next_packet_draft.authority_refs"
            )
            return _protocol_defect(
                base_plan,
                code="STALE_NEXT_PACKET_AUTHORITY",
                field_path=field_path,
                expected="fresh frozen authority refs",
                actual=_stable_stale_reason(exc),
            )
        except (OSError, WorkPacketError) as exc:
            return _protocol_defect(
                base_plan,
                code="INVALID_NEXT_PACKET_AUTHORITY",
                field_path="next_packet_draft.authority_refs",
                expected="readable valid frozen authority refs",
                actual=str(exc),
            )
        unknown_draft_effects, draft_effect_defect = _observe_effect_refs(
            repo,
            canonical_draft["effect_refs"],
            field_prefix="next_packet_draft.effect_refs",
        )
        if draft_effect_defect is not None:
            return _protocol_defect(
                base_plan,
                **draft_effect_defect,
                failure_scope="effect",
            )
        try:
            shared_record = _validate_shared_core_packet(repo, canonical_draft)
        except hmasd_protocol_contracts.ProtocolContractError as exc:
            return _protocol_defect(
                base_plan,
                code=exc.code,
                field_path=_shared_core_error_field(
                    exc.code, prefix="next_packet_draft"
                ),
                expected="one exact fresh Root shared-core record",
                actual=exc.detail,
            )
        if unknown_draft_effects:
            return {
                "verb": "OBSERVE_EFFECT_ONLY",
                "work_id": packet["work_id"],
                "unknown_effect_refs": unknown_draft_effects,
            }
        requested_next_target = str(canonical_draft["target_identity"])
        next_manager = _manager_identity(requested_next_target)
        next_plan = {
            "verb": "PUBLISH_PACKET_INTENT",
            "work_id": packet["work_id"],
            "next_work_id": canonical_draft["work_id"],
            "next_target_identity": (
                next_manager[3] if next_manager is not None else requested_next_target
            ),
            "packet": canonical_draft,
        }
        if shared_record is not None:
            next_plan["shared_core_action_digest"] = shared_record["action_digest"]
        return next_plan

    if next_packet_draft is not None:
        return _protocol_defect(
            base_plan,
            code="NEXT_PACKET_DRAFT_FORBIDDEN",
            field_path="next_packet_draft",
            expected=None,
            actual="provided",
        )
    if action_kind == "NONE":
        plan = dict(base_plan)
        plan["verb"] = "NOOP_TERMINAL"
        return plan
    if action_kind == "RESUME_SAME_SLICE":
        return dict(base_plan)
    if action_kind == "WAIT_FOR_REF":
        input_refs = next_action["input_refs"]
        if not input_refs:
            return _protocol_defect(
                base_plan,
                code="WAIT_INPUT_REFS_REQUIRED",
                field_path="next_action.input_refs",
                expected="non-empty refs",
                actual=[],
            )
        plan = dict(base_plan)
        plan["verb"] = "WAIT_FOR_REF"
        plan["input_refs"] = input_refs
        return plan
    return _protocol_defect(
        base_plan,
        code="UNKNOWN_EFFECT_REQUIRED",
        field_path="next_action.input_refs",
        expected="inbound UNKNOWN Effect ref",
        actual=next_action["input_refs"],
        failure_scope="effect",
    )


def _return_observed_task(
    packet: Mapping[str, Any], receiver: Mapping[str, Any]
) -> dict[str, Any]:
    manager = _manager_identity(str(packet["target_identity"]))
    task: dict[str, Any] = {
        "logical_identity": receiver["logical_identity"],
        "generation": receiver["generation"],
        "lifecycle": "PARKED",
        "thread_id": "return-witness",
    }
    if manager is not None:
        task["kind"] = manager[0]
        if manager[1] is not None:
            task["direction_id"] = manager[1]
    return task


def _reconstruct_return_plan(
    repo: Path,
    packet: Mapping[str, Any],
    witness: Mapping[str, Any],
) -> dict[str, Any]:
    receiver = witness["receiver"]
    base_plan = _plan_packet(
        repo, packet, [_return_observed_task(packet, receiver)]
    )
    if base_plan["verb"] in {"CONFLICT", "OBSERVE_EFFECT_ONLY"}:
        return base_plan
    plan = _bind_agent_result(
        repo,
        packet,
        base_plan,
        witness["agent_result"],
        witness.get("next_packet_draft"),
    )
    if plan["verb"] != "CONFLICT":
        plan["task_resolution"] = {
            "status": "RETURN_WITNESS",
            "logical_identity": receiver["logical_identity"],
            "generation": receiver["generation"],
        }
    return plan


def _return_conflict_plan(packet: Mapping[str, Any]) -> dict[str, Any]:
    manager = _manager_identity(str(packet["target_identity"]))
    return {
        "verb": "CONFLICT",
        "conflict_type": "RETURN_CONFLICT",
        "delivery_key": packet["work_id"],
        "delivery_semantics": "AT_LEAST_ONCE_IDEMPOTENT_INTAKE",
        "requested_target_identity": packet["target_identity"],
        "target_identity": manager[3] if manager is not None else packet["target_identity"],
        "unknown_effect_refs": [],
        "work_id": packet["work_id"],
    }


def publish_return(
    *,
    work_id: str,
    observed_tasks: Sequence[Mapping[str, Any]] | str | os.PathLike[str],
    agent_result: Mapping[str, Any],
    next_packet_draft: Mapping[str, Any] | None = None,
    repo: str | os.PathLike[str] = ".",
) -> dict[str, Any]:
    """Validate and atomically freeze one receiver-owned return envelope."""

    if not isinstance(work_id, str) or _SHA256.fullmatch(work_id) is None:
        raise InvalidPacket("work_id must be a lowercase SHA256")
    repository = Path(repo).absolute()
    packet = _load_ready_packet(repository, work_id)
    current_tasks = load_observed_tasks(observed_tasks, repo=repository)
    resolution = resolve_target_task(str(packet["target_identity"]), current_tasks)
    if resolution.get("status") != "REUSE":
        raise InvalidPacket("return-publish requires a freshly observed reusable receiver")
    reconciled = reconcile_once(
        repo=repository,
        work_id=work_id,
        observed_tasks=current_tasks,
        agent_result=agent_result,
        next_packet_draft=next_packet_draft,
    )
    plan = reconciled["plan"]
    if plan["verb"] == "RESUME_SAME_SLICE" or (
        plan["verb"] == "DISPATCH_EXISTING"
        and agent_result.get("next_action", {}).get("kind") == "RESUME_SAME_SLICE"
    ):
        raise InvalidPacket("RESUME_SAME_SLICE is not a replaceable terminal return")
    if plan.get("conflict_type") == "RETURN_CONFLICT":
        raise PacketConflict("work_id has a conflicting return witness")
    if plan["verb"] not in {
        "NOOP_TERMINAL",
        "PUBLISH_PACKET_INTENT",
        "WAIT_FOR_REF",
    }:
        detail = plan.get("defect", {}).get("code", plan["verb"])
        raise InvalidPacket(f"return does not close the current attempt: {detail}")

    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "work_id": work_id,
        "receiver": {
            "logical_identity": resolution["logical_identity"],
            "generation": resolution["generation"],
        },
        "agent_result": dict(agent_result),
    }
    if plan["verb"] == "PUBLISH_PACKET_INTENT":
        witness["next_packet_draft"] = plan["packet"]
    witness = _validate_return_witness(witness, packet=packet)
    witness_bytes = hmasd_state.canonical_bytes(witness)

    root = _work_root(repository)
    for child in (root / "returns", root / "return-staging", root / "locks"):
        _assert_no_alias(child, label="return directory", require_existing=False)
        child.mkdir(parents=True, exist_ok=True)
        _assert_no_alias(child, label="return directory", require_existing=False)
    lock_path = root / "locks" / f"return-{work_id}.lock"
    with _lock(lock_path) as stream, hmasd_platform.exclusive_file_lock(stream.fileno()):
        _verify_lock_identity(lock_path, stream.fileno())
        final_dir = root / "returns" / work_id
        final_path = final_dir / "return.json"
        if final_path.is_file():
            existing = _validate_return_witness(
                _load_json(final_path, label="return witness"), packet=packet
            )
            if final_path.read_bytes() != witness_bytes or (
                hmasd_state.canonical_bytes(existing) != witness_bytes
            ):
                raise PacketConflict("work_id has a conflicting return witness")
            return {
                "ok": True,
                "operation": "return-publish",
                "work_id": work_id,
                "published": False,
                "path": str(final_path),
                "plan": plan,
            }
        if final_dir.exists():
            _assert_no_alias(final_dir, label="return directory", require_existing=False)
            if not final_dir.is_dir() or any(final_dir.iterdir()):
                raise PacketConflict("return directory exists without a complete return")
        staging_dir = root / "return-staging" / work_id
        if staging_dir.exists():
            _assert_no_alias(staging_dir, label="return staging", require_existing=False)
            if not staging_dir.is_dir():
                raise PacketConflict("return staging path is not a directory")
            for residue in staging_dir.iterdir():
                _assert_no_alias(residue, label="return staging residue", require_existing=False)
                if not residue.is_file():
                    raise PacketConflict("return staging contains unexpected residue")
                residue.unlink()
            staging_dir.rmdir()
        staging_dir.mkdir()
        staged_path = staging_dir / "return.json"
        _atomic_json(staged_path, witness)
        final_dir.mkdir(exist_ok=True)
        try:
            os.replace(staged_path, final_path)
        except OSError:
            if not final_path.is_file() or final_path.read_bytes() != witness_bytes:
                raise
        if staging_dir.exists():
            staging_dir.rmdir()
        hmasd_platform.fsync_directory(final_dir.parent)
        return {
            "ok": True,
            "operation": "return-publish",
            "work_id": work_id,
            "published": True,
            "path": str(final_path),
            "plan": plan,
        }


def reconcile_once(
    *,
    work_id: str,
    repo: str | os.PathLike[str] = ".",
    observed_tasks: Sequence[Mapping[str, Any]] | str | os.PathLike[str] | None = None,
    agent_result: Mapping[str, Any] | None = None,
    next_packet_draft: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Plan one exact ready packet under its work-id lock.

    The packet and task observation are read inside the lock. The result is a
    closed, handlerless plan; this function never sends, creates, waits, runs an
    Effect, or mutates Git.
    """

    if not isinstance(work_id, str) or _SHA256.fullmatch(work_id) is None:
        raise InvalidPacket("work_id must be a lowercase SHA256")
    if observed_tasks is None:
        raise InvalidPacket("observed_tasks must be explicit")
    repository = Path(repo).absolute()
    root = _work_root(repository)
    locks = root / "locks"
    _assert_no_alias(locks, label="reconcile locks directory", require_existing=False)
    locks.mkdir(parents=True, exist_ok=True)
    _assert_no_alias(locks, label="reconcile locks directory", require_existing=False)
    packet_path = root / "ready" / work_id / "packet.json"
    lock_path = locks / f"reconcile-{work_id}.lock"
    with _lock(lock_path) as stream, hmasd_platform.exclusive_file_lock(stream.fileno()):
        _verify_lock_identity(lock_path, stream.fileno())
        _assert_no_alias(packet_path, label="ready packet", require_existing=False)
        if not packet_path.is_file():
            raise InvalidPacket(f"ready packet is missing for work_id {work_id}")
        packet = validate_packet(
            _load_json(packet_path, label="ready packet"), repo=repository
        )
        if packet["work_id"] != work_id:
            raise PacketConflict("ready directory does not match work_id")
        current_tasks = load_observed_tasks(observed_tasks, repo=repository)
        try:
            return_path = _return_path(repository, work_id)
            _assert_no_alias(return_path, label="return witness", require_existing=False)
            witness = (
                _validate_return_witness(
                    _load_json(return_path, label="return witness"), packet=packet
                )
                if return_path.is_file()
                else None
            )
            if witness is not None:
                if return_path.read_bytes() != hmasd_state.canonical_bytes(witness):
                    raise PacketConflict("return witness is not canonical JSON")
                if agent_result is not None:
                    explicit: dict[str, Any] = {
                        "agent_result": dict(agent_result),
                    }
                    existing: dict[str, Any] = {
                        "agent_result": witness["agent_result"],
                    }
                    if next_packet_draft is not None:
                        try:
                            explicit["next_packet_draft"] = build_packet(
                                next_packet_draft, repo=repository
                            )
                        except WorkPacketError:
                            plan = _return_conflict_plan(packet)
                        else:
                            if "next_packet_draft" in witness:
                                existing["next_packet_draft"] = witness[
                                    "next_packet_draft"
                                ]
                            plan = (
                                _reconstruct_return_plan(repository, packet, witness)
                                if hmasd_state.canonical_bytes(explicit)
                                == hmasd_state.canonical_bytes(existing)
                                else _return_conflict_plan(packet)
                            )
                    else:
                        if "next_packet_draft" in witness:
                            existing["next_packet_draft"] = witness[
                                "next_packet_draft"
                            ]
                        plan = (
                            _reconstruct_return_plan(repository, packet, witness)
                            if hmasd_state.canonical_bytes(explicit)
                            == hmasd_state.canonical_bytes(existing)
                            else _return_conflict_plan(packet)
                        )
                elif next_packet_draft is not None:
                    plan = _return_conflict_plan(packet)
                else:
                    plan = _reconstruct_return_plan(repository, packet, witness)
            else:
                plan = _plan_packet(repository, packet, current_tasks)
                if plan["verb"] not in {"CONFLICT", "OBSERVE_EFFECT_ONLY"}:
                    if agent_result is None:
                        if next_packet_draft is not None:
                            plan = _protocol_defect(
                                plan,
                                code="AGENT_RESULT_REQUIRED",
                                field_path="agent_result",
                                expected="typed agent_result",
                                actual=None,
                            )
                    else:
                        plan = _bind_agent_result(
                            repository,
                            packet,
                            plan,
                            agent_result,
                            next_packet_draft,
                        )
        except StaleAuthority as exc:
            requested_target = str(packet["target_identity"])
            manager = _manager_identity(requested_target)
            plan = {
                "verb": "CONFLICT",
                "conflict_type": "STALE_AUTHORITY",
                "delivery_key": work_id,
                "delivery_semantics": "AT_LEAST_ONCE_IDEMPOTENT_INTAKE",
                "reason": _stable_stale_reason(exc),
                "requested_target_identity": requested_target,
                "target_identity": manager[3] if manager is not None else requested_target,
                "unknown_effect_refs": [],
                "work_id": work_id,
            }
    return {
        "ok": True,
        "operation": "reconcile",
        "once": True,
        "work_id": work_id,
        "plan": plan,
    }


def _read_input(path: str) -> dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise InvalidPacket("input must be a JSON object")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    build = sub.add_parser("build")
    build.add_argument("--input", required=True)
    build.add_argument("--output")
    build.add_argument("--repo", default=".")
    publish = sub.add_parser("publish")
    publish.add_argument("--packet", required=True)
    publish.add_argument("--repo", default=".")
    validate = sub.add_parser("validate")
    validate.add_argument("--packet", required=True)
    validate.add_argument("--repo", default=".")
    reconcile = sub.add_parser("reconcile")
    reconcile.add_argument("--once", action="store_true", required=True)
    reconcile.add_argument("--repo", default=".")
    reconcile.add_argument("--work-id", required=True)
    reconcile.add_argument("--observed-tasks", required=True)
    reconcile.add_argument("--agent-result")
    reconcile.add_argument("--next-packet-draft")
    return_publish = sub.add_parser("return-publish")
    return_publish.add_argument("--repo", default=".")
    return_publish.add_argument("--work-id", required=True)
    return_publish.add_argument("--observed-tasks", required=True)
    return_publish.add_argument("--agent-result", required=True)
    return_publish.add_argument("--next-packet-draft")
    return_read = sub.add_parser("return-read")
    return_read.add_argument("--repo", default=".")
    return_read.add_argument("--work-id", required=True)
    compare = sub.add_parser("compare")
    compare.add_argument("--repo", default=".")
    compare.add_argument("--work-id", action="append", required=True)
    shared_core_record = sub.add_parser("shared-core-record")
    shared_core_record.add_argument("--repo", default=".")
    shared_core_record.add_argument("--packet", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    operation = "unknown"
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        operation = args.operation
        if operation == "build":
            repository = Path(args.repo).absolute()
            result = build_packet(_read_input(args.input), repo=repository)
            if args.output and args.output != "-":
                output_text = _normalize_path(args.output, label="build output")
                output = _repo_path(
                    repository,
                    output_text,
                    label="build output",
                    require_existing=False,
                )
                _atomic_json(output, result)
                result = {"ok": True, "operation": "build", "work_id": result["work_id"], "path": str(output)}
        elif operation == "publish":
            result = publish_packet(_read_input(args.packet), repo=args.repo)
        elif operation == "validate":
            packet = validate_packet(_read_input(args.packet), repo=args.repo)
            result = {"ok": True, "operation": "validate", "work_id": packet["work_id"]}
        elif operation == "reconcile":
            result = reconcile_once(
                repo=args.repo,
                work_id=args.work_id,
                observed_tasks=args.observed_tasks,
                agent_result=(
                    _read_input(args.agent_result) if args.agent_result else None
                ),
                next_packet_draft=(
                    _read_input(args.next_packet_draft)
                    if args.next_packet_draft
                    else None
                ),
            )
        elif operation == "return-publish":
            result = publish_return(
                repo=args.repo,
                work_id=args.work_id,
                observed_tasks=args.observed_tasks,
                agent_result=_read_input(args.agent_result),
                next_packet_draft=(
                    _read_input(args.next_packet_draft)
                    if args.next_packet_draft
                    else None
                ),
            )
        elif operation == "return-read":
            repository = Path(args.repo).absolute()
            witness = read_return(repo=repository, work_id=args.work_id)
            if witness is None:
                raise InvalidPacket(
                    f"return witness is missing for work_id {args.work_id}"
                )
            result = {
                "ok": True,
                "operation": "return-read",
                "work_id": args.work_id,
                "path": str(_return_path(repository, args.work_id)),
                "witness": witness,
                "plan": reconcile_once(
                    repo=repository,
                    work_id=args.work_id,
                    observed_tasks=[],
                )["plan"],
            }
        elif operation == "compare":
            result = compare_work_ids(args.repo, args.work_id)
        else:
            result = build_shared_core_record(
                _read_input(args.packet), repo=args.repo
            )
    except WorkPacketError as exc:
        print(json.dumps({"ok": False, "operation": operation, "error": str(exc), "code": exc.code}, ensure_ascii=False, sort_keys=True))
        return exc.code
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "operation": operation, "error": str(exc), "code": 2}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
