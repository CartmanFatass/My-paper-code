"""Create-only atomic FRRIE root and terminal publication."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Mapping

from .contracts.core import FRRIE_TERMINAL_V2, ContractError, canonical_json_bytes, validate_manifest
from .work import final_cumulative_work


class LifecycleError(ContractError):
    pass


ROOT_MARKER_NAME = ".FRRIE_FRESH_ROOT_V2.json"
ROOT_MARKER_SCHEMA = "FRRIE_FRESH_ROOT_MARKER_V2"


def _root_marker(manifest: Mapping[str, Any], kind: str) -> dict[str, Any]:
    roots = manifest["roots"]
    peer = "checkpoint" if kind == "output" else "output"
    return {
        "schema": ROOT_MARKER_SCHEMA,
        "root_kind": kind.upper(),
        "root": str(Path(roots[kind]).resolve(strict=False)),
        "peer_root": str(Path(roots[peer]).resolve(strict=False)),
        "manifest_contract": dict(manifest),
    }


def _write_marker(directory: Path, marker: Mapping[str, Any]) -> None:
    path = directory / ROOT_MARKER_NAME
    with path.open("xb") as handle:
        handle.write(canonical_json_bytes(marker))
        handle.flush()
        os.fsync(handle.fileno())


def _remove_preactivity_root(directory: Path) -> None:
    """Rollback only a root containing the single direct marker."""
    if not directory.is_dir():
        return
    entries = list(directory.iterdir())
    if not entries:
        directory.rmdir()
        return
    if len(entries) == 1 and entries[0].name == ROOT_MARKER_NAME and entries[0].is_file():
        entries[0].unlink()
        directory.rmdir()


def _remove_preactivity_parent(parent: Path, child_names: set[str]) -> None:
    if not parent.is_dir():
        return
    entries = list(parent.iterdir())
    if any(entry.name not in child_names or not entry.is_dir() for entry in entries):
        return
    for entry in entries:
        _remove_preactivity_root(entry)
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()


def _fsync_directory(directory: Path) -> None:
    """Persist directory entries where the platform exposes directory fsync."""
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def claim_fresh_roots(manifest0: Mapping[str, Any]) -> tuple[Path, Path]:
    """Claim both V2 sibling roots with one atomic parent-directory rename."""
    manifest = validate_manifest(manifest0)
    output = Path(manifest["roots"]["output"]).resolve(strict=False)
    checkpoint = Path(manifest["roots"]["checkpoint"]).resolve(strict=False)
    paths = (output, checkpoint)
    final_parent = output.parent
    staging_parent = final_parent.with_name(final_parent.name + ".FRRIE_CLAIM_V2.tmp")
    if final_parent.exists() or staging_parent.exists():
        raise LifecycleError("fresh common run parent or stale V2 staging parent already exists")
    staging_roots = (
        staging_parent / output.name,
        staging_parent / checkpoint.name,
    )
    child_names = {output.name, checkpoint.name}
    try:
        final_parent.parent.mkdir(parents=True, exist_ok=True)
        staging_parent.mkdir(exist_ok=False)
        for staging_root, kind in zip(staging_roots, ("output", "checkpoint")):
            staging_root.mkdir(exist_ok=False)
            _write_marker(staging_root, _root_marker(manifest, kind))
            _fsync_directory(staging_root)
        _fsync_directory(staging_parent)
        os.rename(staging_parent, final_parent)
        _validate_v2_root_markers(manifest)
    except (OSError, LifecycleError) as exc:
        _remove_preactivity_parent(staging_parent, child_names)
        _remove_preactivity_parent(final_parent, child_names)
        raise LifecycleError(f"paired fresh-root transaction failed: {exc}") from exc
    return paths


def _validate_v2_root_markers(manifest: Mapping[str, Any]) -> None:
    for kind in ("output", "checkpoint"):
        root = Path(manifest["roots"][kind]).resolve(strict=False)
        try:
            observed = json.loads((root / ROOT_MARKER_NAME).read_text(encoding="ascii"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LifecycleError(f"{kind} V2 root marker is absent or invalid: {exc}") from exc
        if observed != _root_marker(manifest, kind):
            raise LifecycleError(f"{kind} V2 root marker does not directly match the manifest")


def claim_fresh_root(path: str | Path) -> Path:
    root = Path(path)
    staging = root.with_name(root.name + ".FRRIE_CLAIM.tmp")
    marker = staging / ".FRRIE_FRESH_ROOT_V1"
    if root.exists() or staging.exists():
        raise LifecycleError("fresh root or claim staging path already exists")
    try:
        root.parent.mkdir(parents=True, exist_ok=True)
        staging.mkdir(exist_ok=False)
        with marker.open("xb") as handle:
            handle.write(b"FRRIE_FRESH_ROOT_V1\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.rename(staging, root)
    except OSError as exc:
        if marker.exists():
            marker.unlink()
        if staging.exists():
            staging.rmdir()
        raise LifecycleError(f"fresh root is unavailable: {exc}") from exc
    return root


def publish_create_only(path: str | Path, value: Mapping[str, Any]) -> Path:
    target = Path(path)
    temporary = target.with_name(target.name + ".tmp")
    if target.exists() or temporary.exists():
        raise LifecycleError("publication target or temporary already exists")
    data = canonical_json_bytes(value)
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, target)
        temporary.unlink()
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def publish_terminal(
    root: str | Path, *, status: str, manifest_contract: Mapping[str, Any],
    analysis: Mapping[str, Any] | None = None,
) -> Path:
    statuses = {
        "UNRESOLVED_ANALYSIS_METHOD_UNFROZEN",
        "NONIDENTIFICATION_ENDPOINT_SUPPORT",
        "INVALID", "TECHNICAL_FAILURE",
    }
    if status not in statuses:
        raise LifecycleError("unknown terminal status")
    if not isinstance(manifest_contract, Mapping) or not manifest_contract:
        raise LifecycleError("terminal requires the direct manifest contract")
    try:
        validated_manifest = validate_manifest(manifest_contract)
    except ContractError as exc:
        raise LifecycleError(f"terminal requires a V2 manifest: {exc}") from exc
    if validated_manifest != manifest_contract:
        raise LifecycleError("terminal manifest must be the direct validated V2 contract")
    analysis_statuses = statuses - {"INVALID", "TECHNICAL_FAILURE"}
    if status in analysis_statuses:
        if (
            not isinstance(analysis, Mapping)
            or analysis.get("complete") is not True
            or analysis.get("status") != status
            or analysis.get("manifest_contract") != manifest_contract
            or analysis.get("scientific_polarity") is not None
            or analysis.get("final_cumulative_receipt") != final_cumulative_work(validated_manifest["compute"])
        ):
            raise LifecycleError("analysis terminal requires a matching complete analysis")
    elif analysis is not None:
        raise LifecycleError("failure terminal cannot expose scientific values")
    root_path = Path(root)
    if root_path.resolve(strict=False) != Path(validated_manifest["roots"]["output"]).resolve(strict=False):
        raise LifecycleError("V2 terminal must publish to the directly bound output root")
    _validate_v2_root_markers(validated_manifest)
    terminal: dict[str, Any] = {
        "schema": FRRIE_TERMINAL_V2, "status": status,
        "manifest_contract": dict(manifest_contract), "complete": True,
    }
    if analysis is not None:
        terminal["analysis"] = dict(analysis)
        terminal["final_cumulative_receipt"] = dict(analysis["final_cumulative_receipt"])
    return publish_create_only(root_path / "terminal.json", terminal)
