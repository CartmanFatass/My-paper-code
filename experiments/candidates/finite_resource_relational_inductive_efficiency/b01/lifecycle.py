"""Create-only B01 roots, checkpoints, panels, and quarantine publication."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from .constants import ROOT_MARKER_SCHEMA, TEST_MANIFEST_SCHEMA, TEST_ROOT_MARKER_SCHEMA
from .contract import (
    B01ContractError, canonical_json_bytes, validate_invocation_binding,
    validate_manifest, validate_test_manifest,
)


def publish_create_only(path: str | Path, value: bytes | Mapping[str, Any]) -> Path:
    target = Path(path)
    temporary = target.with_name(target.name + ".creating")
    if target.exists() or temporary.exists():
        raise B01ContractError("B01 publication target is not fresh")
    data = value if isinstance(value, bytes) else canonical_json_bytes(value)
    target.parent.mkdir(parents=True, exist_ok=True)
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


def claim_fresh_roots(manifest: Mapping[str, Any]) -> dict[str, Path]:
    test_only = manifest.get("schema") == TEST_MANIFEST_SCHEMA
    value = validate_test_manifest(manifest) if test_only else validate_manifest(manifest)
    paths = {name: Path(path).resolve(strict=False) for name, path in value["roots"].items()}
    final_parent = next(iter(paths.values())).parent
    if any(path.parent != final_parent for path in paths.values()):
        raise B01ContractError("B01 roots must share one atomic parent")
    if final_parent.exists():
        raise B01ContractError("B01 common run parent is not fresh")
    staging_parent = final_parent.with_name(final_parent.name + ".FRRIE_B01_CLAIMING")
    if staging_parent.exists():
        raise B01ContractError("B01 root staging parent already exists")
    marker_schema = TEST_ROOT_MARKER_SCHEMA if test_only else ROOT_MARKER_SCHEMA
    try:
        final_parent.parent.mkdir(parents=True, exist_ok=True)
        staging_parent.mkdir(exist_ok=False)
        for name, path in paths.items():
            staged = staging_parent / path.name
            staged.mkdir(exist_ok=False)
            publish_create_only(staged / ".FRRIE_B01_ROOT.json", {
                "schema": marker_schema, "kind": name,
                "root": str(path), "experiment_id": value["experiment_id"],
                "manifest_contract": value,
            })
        os.rename(staging_parent, final_parent)
    except (OSError, B01ContractError) as exc:
        if staging_parent.is_dir():
            for staged in list(staging_parent.iterdir()):
                entries = list(staged.iterdir()) if staged.is_dir() else []
                if len(entries) == 1 and entries[0].name == ".FRRIE_B01_ROOT.json":
                    entries[0].unlink()
                    staged.rmdir()
            if not any(staging_parent.iterdir()):
                staging_parent.rmdir()
        raise B01ContractError(f"B01 root claim failed: {exc}") from exc
    return paths


def publish_quarantine(
    output_root: str | Path, *, invocation_binding: Mapping[str, Any],
    technical_reason: str,
) -> Path:
    if not isinstance(technical_reason, str) or not technical_reason.strip():
        raise B01ContractError("quarantine requires an exact technical reason")
    binding = validate_invocation_binding(invocation_binding)
    return publish_create_only(Path(output_root) / "quarantine.json", {
        "schema": "FRRIE_B01_INCOMPLETE_QUARANTINE_V1",
        "status": "INCOMPLETE_IMPLEMENTATION_NO_SCIENTIFIC_OBSERVATION",
        "technical_reason": technical_reason,
        "invocation_binding": binding,
        "scientific_values": None,
        "complete": True,
    })


def publish_complete_panel(
    path: str | Path, *, panel: Mapping[str, Any], manifest: Mapping[str, Any],
) -> Path:
    from .panel import validate_complete_panel, validate_test_panel

    value = (
        validate_test_panel(panel, manifest)
        if manifest.get("schema") == TEST_MANIFEST_SCHEMA
        else validate_complete_panel(panel, manifest)
    )
    return publish_create_only(path, value)
