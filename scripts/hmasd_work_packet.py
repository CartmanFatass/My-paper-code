#!/usr/bin/env python3
"""Build, publish, validate, and reconcile runtime-only HMASD Work Packets.

Packets carry immutable pointers to existing authority.  They are deliberately
not a durable state kind and contain no lifecycle, claim, result, or checkpoint
field.  A packet remains runnable only while all frozen authority references
still match the repository.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any, Callable, Iterable, Mapping, Sequence
import unicodedata

try:
    from scripts import hmasd_platform, hmasd_state
except ImportError:
    import hmasd_platform
    import hmasd_state


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
    if not isinstance(value, Mapping) or set(value) != {"path"}:
        raise InvalidPacket(f"{label} must contain only path")
    return {"path": _normalize_path(value["path"], label=f"{label}.path")}


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


def _unknown_effect(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered == "unknown_outcome" and item is not None:
                return True
            if (lowered in {"status", "lifecycle", "outcome"} or lowered.endswith("_outcome")) and isinstance(item, str) and (item == "UNKNOWN" or item.endswith("_UNKNOWN")):
                return True
            if _unknown_effect(item):
                return True
    elif isinstance(value, list):
        return any(_unknown_effect(item) for item in value)
    return False


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
        compatible = isinstance(generation, int) and not isinstance(generation, bool) and generation >= 1
        if manager is not None:
            kind, direction, expected_generation, _ = manager
            compatible = compatible and task.get("kind") == kind
            if direction is not None:
                compatible = compatible and task.get("direction_id") == direction
            if expected_generation is not None:
                compatible = compatible and generation == expected_generation
        if task.get("lifecycle") in {"COMPLETED", "RETIRED"}:
            compatible = False
        if nonterminal_scope and nonterminal_scope[0].get("logical_identity") != canonical_identity:
            compatible = False
        if compatible:
            return {
                "status": "REUSE",
                "logical_identity": canonical_identity,
                "kind": task.get("kind"),
                "generation": generation,
                "lifecycle": task.get("lifecycle"),
                "thread_id": task.get("thread_id"),
            }
        return {
            "status": "TASK_IDENTITY_CONFLICT",
            "logical_identity": canonical_identity,
            "reason": "exact logical identity has incompatible kind, direction, generation, or lifecycle",
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


def _direction(packet: Mapping[str, Any]) -> str:
    scope_direction = _path_direction(str(packet["scope_ref"]["path"]))
    if scope_direction is not None:
        return scope_direction
    manager = _manager_identity(str(packet["target_identity"]))
    if manager is not None and manager[1] is not None:
        return manager[1]
    return "_project"


def _reconcile_key(packet: Mapping[str, Any]) -> str:
    requested_target = str(packet["target_identity"])
    manager = _manager_identity(requested_target)
    canonical_target = manager[3] if manager is not None else requested_target
    frozen = {
        "scope_ref": packet["scope_ref"],
        "target_identity": canonical_target,
        "authority_refs": packet["authority_refs"],
    }
    return hmasd_state.sha256_bytes(hmasd_state.canonical_bytes(frozen))


def _action(
    repo: Path,
    packet: Mapping[str, Any],
    observed_tasks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    _authority_matches(repo, packet["scope_ref"], label="scope_ref")
    for index, reference in enumerate(packet["authority_refs"]):
        _authority_matches(repo, reference, label=f"authority_refs[{index}]")
    task_resolution = resolve_target_task(str(packet["target_identity"]), observed_tasks)
    unknown: list[str] = []
    for index, reference in enumerate(packet["effect_refs"]):
        path = _repo_path(repo, reference["path"], label=f"effect_refs[{index}]", require_existing=True)
        effect = _load_json(path, label=f"effect_refs[{index}]")
        if _unknown_effect(effect):
            unknown.append(reference["path"])
    resolution_status = task_resolution["status"]
    if resolution_status == "TASK_IDENTITY_CONFLICT":
        action_name = "TASK_IDENTITY_CONFLICT"
    elif unknown:
        action_name = "OBSERVE_EFFECT"
    elif resolution_status == "CREATE_TASK":
        action_name = "CREATE_TASK"
    else:
        action_name = "DISPATCH"
    return {
        "action": action_name,
        "delivery_key": packet["work_id"],
        "delivery_semantics": "AT_LEAST_ONCE_IDEMPOTENT_INTAKE",
        "direction": _direction(packet),
        "key": _reconcile_key(packet),
        "observe_only": bool(unknown),
        "unknown_effect_refs": unknown,
        "work_id": packet["work_id"],
        "target_identity": packet["target_identity"],
        "requested_target_identity": packet["target_identity"],
        "task_resolution": task_resolution,
    }


def reconcile_once(
    *,
    repo: str | os.PathLike[str] = ".",
    handler: Callable[[Mapping[str, Any], Mapping[str, Any]], Any] | None = None,
    capacity: int | None = None,
    observed_tasks: Sequence[Mapping[str, Any]] | str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Advance at most one packet per direction for this bounded invocation.

    The optional handler runs while the scope/target/revision key lock is held.
    Delivery is intentionally at-least-once: a handler or receiver must use
    ``work_id`` as its idempotent intake key. A path-backed task observation is
    reloaded inside that lock. A supplied in-memory sequence is a test/embedder
    snapshot whose caller is responsible for updating it between calls.
    """

    repository = Path(repo).absolute()
    dynamic_task_snapshot = observed_tasks is None or isinstance(
        observed_tasks, (str, os.PathLike)
    )
    task_snapshot = (
        None
        if dynamic_task_snapshot
        else load_observed_tasks(observed_tasks, repo=repository)
    )
    root = _work_root(repository)
    ready = root / "ready"
    locks = root / "locks"
    _assert_no_alias(locks, label="reconcile locks directory", require_existing=False)
    locks.mkdir(parents=True, exist_ok=True)
    _assert_no_alias(locks, label="reconcile locks directory", require_existing=False)
    observation_semantics = (
        "RELOAD_PATH_UNDER_KEY_LOCK"
        if dynamic_task_snapshot
        else "CALLER_MANAGED_IN_MEMORY_SNAPSHOT"
    )
    if capacity is not None and (not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1):
        raise InvalidPacket("reconcile capacity must be a positive integer")
    if not ready.is_dir():
        return {
            "ok": True,
            "operation": "reconcile",
            "once": True,
            "task_observation_semantics": observation_semantics,
            "actions": [],
            "stale": [],
            "errors": [],
        }
    _assert_no_alias(ready, label="ready directory", require_existing=False)
    grouped: dict[str, list[dict[str, Any]]] = {}
    errors: list[dict[str, Any]] = []
    for packet_dir in sorted(ready.iterdir(), key=lambda value: value.name):
        if not packet_dir.is_dir() or _SHA256.fullmatch(packet_dir.name) is None:
            continue
        packet_path = packet_dir / "packet.json"
        try:
            packet = validate_packet(_load_json(packet_path, label="ready packet"), repo=repository)
            if packet["work_id"] != packet_dir.name:
                raise PacketConflict("ready directory does not match work_id")
            grouped.setdefault(_direction(packet), []).append(packet)
        except Exception as exc:
            errors.append({"work_id": packet_dir.name, "error": str(exc), "type": type(exc).__name__})
    def advance_direction(packets: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
        local_stale: list[dict[str, Any]] = []
        local_errors: list[dict[str, Any]] = []
        packets_by_key: dict[str, list[Mapping[str, Any]]] = {}
        for packet in packets:
            packets_by_key.setdefault(_reconcile_key(packet), []).append(packet)
        conflicted_keys: set[str] = set()
        for key, keyed_packets in sorted(packets_by_key.items()):
            work_ids = sorted({str(packet["work_id"]) for packet in keyed_packets})
            if len(work_ids) > 1:
                conflicted_keys.add(key)
                local_errors.append(
                    {
                        "code": "PACKET_KEY_CONFLICT",
                        "error": "one reconcile key has multiple Work Packets",
                        "key": key,
                        "type": "PacketConflict",
                        "work_id": work_ids[0],
                        "work_ids": work_ids,
                    }
                )
        for key, keyed_packets in sorted(packets_by_key.items()):
            if key in conflicted_keys:
                continue
            packet = keyed_packets[0]
            try:
                lock_path = locks / f"reconcile-{key}.lock"
                with _lock(lock_path) as stream, hmasd_platform.exclusive_file_lock(stream.fileno()):
                    _verify_lock_identity(lock_path, stream.fileno())
                    current_tasks = (
                        load_observed_tasks(observed_tasks, repo=repository)
                        if dynamic_task_snapshot
                        else list(task_snapshot or [])
                    )
                    action = _action(repository, packet, current_tasks)
                    # UNKNOWN is an observation boundary.  A generic dispatch
                    # handler is intentionally never called for this action.
                    if (
                        handler is not None
                        and not action["observe_only"]
                        and action["action"] != "TASK_IDENTITY_CONFLICT"
                    ):
                        try:
                            action["handler_result"] = handler(packet, action)
                        except Exception as exc:
                            local_errors.append(
                                {
                                    "work_id": packet["work_id"],
                                    "error": str(exc),
                                    "type": type(exc).__name__,
                                }
                            )
                            return None, local_stale, local_errors
                    return action, local_stale, local_errors
            except StaleAuthority as exc:
                local_stale.append({"work_id": packet["work_id"], "reason": str(exc)})
            except Exception as exc:
                local_errors.append({"work_id": packet["work_id"], "error": str(exc), "type": type(exc).__name__})
        return None, local_stale, local_errors

    ordered_groups = [grouped[direction] for direction in sorted(grouped)]
    max_workers = capacity or min(32, max(1, len(ordered_groups)))
    actions: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    if ordered_groups:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for action, group_stale, group_errors in executor.map(advance_direction, ordered_groups):
                if action is not None:
                    actions.append(action)
                stale.extend(group_stale)
                errors.extend(group_errors)
    actions.sort(key=lambda value: (value["direction"], value["work_id"]))
    stale.sort(key=lambda value: value["work_id"])
    errors.sort(key=lambda value: value["work_id"])
    return {
        "ok": not errors,
        "operation": "reconcile",
        "once": True,
        "task_observation_semantics": observation_semantics,
        "actions": actions,
        "stale": stale,
        "errors": errors,
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
    reconcile.add_argument("--capacity", type=int)
    reconcile.add_argument("--observed-tasks")
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
        else:
            result = reconcile_once(
                repo=args.repo,
                capacity=args.capacity,
                observed_tasks=args.observed_tasks,
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
