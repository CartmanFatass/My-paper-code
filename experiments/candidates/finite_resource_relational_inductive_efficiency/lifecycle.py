"""Create-only atomic FRRIE root and terminal publication."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from .contracts.core import FRRIE_TERMINAL_V1, ContractError, canonical_json_bytes


class LifecycleError(ContractError):
    pass


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
        "NONIDENTIFICATION_GENERIC_INCOMPETENCE",
        "NONIDENTIFICATION_ENDPOINT_SUPPORT",
        "INVALID", "TECHNICAL_FAILURE",
    }
    if status not in statuses:
        raise LifecycleError("unknown terminal status")
    if not isinstance(manifest_contract, Mapping) or not manifest_contract:
        raise LifecycleError("terminal requires the direct manifest contract")
    canonical_json_bytes(manifest_contract)
    analysis_statuses = statuses - {"INVALID", "TECHNICAL_FAILURE"}
    if status in analysis_statuses:
        if (
            not isinstance(analysis, Mapping)
            or analysis.get("complete") is not True
            or analysis.get("status") != status
            or analysis.get("manifest_contract") != manifest_contract
        ):
            raise LifecycleError("analysis terminal requires a matching complete analysis")
    elif analysis is not None:
        raise LifecycleError("failure terminal cannot expose scientific values")
    root_path = Path(root)
    if not (root_path / ".FRRIE_FRESH_ROOT_V1").is_file():
        raise LifecycleError("terminal publication requires a claimed fresh root")
    terminal: dict[str, Any] = {
        "schema": FRRIE_TERMINAL_V1, "status": status,
        "manifest_contract": dict(manifest_contract), "complete": True,
    }
    if analysis is not None:
        terminal["analysis"] = dict(analysis)
    return publish_create_only(root_path / "terminal.json", terminal)
