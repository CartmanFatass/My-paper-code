"""Pre-registered, result-blind technical slice frontiers for RUN-01."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

from .contracts import STATE_SPECS, TRAINING_SEEDS
from .orchestration import (
    Attempt, AttemptError, _read_regular_bytes, _require_direct_directory,
    validate_sealed_identity,
)
from .source_identity import compute_source_identity_bytes, validate_source_identity_bytes


def _frontier_ids() -> tuple[str, ...]:
    rows: list[str] = []
    for seed in TRAINING_SEEDS:
        rows.extend(f"training-{seed}-update-{update:03d}" for update in range(1, 161))
        rows.extend(f"curve-{seed}-update-{update:03d}" for update in range(0, 161, 20))
        rows.append(f"competence-{seed}")
    rows.append("competence-inventory")
    rows.extend(f"source-{spec.cell}" for spec in STATE_SPECS)
    rows.extend(f"development-{seed}-{spec.cell}" for seed in TRAINING_SEEDS for spec in STATE_SPECS)
    return tuple(rows)


TECHNICAL_FRONTIER_IDS = _frontier_ids()
TECHNICAL_FRONTIER_INDEX = {value: index for index, value in enumerate(TECHNICAL_FRONTIER_IDS)}
FRONTIER_SCHEMA = "SCDMP_MF_RS_MK_B01_TECHNICAL_FRONTIER_V1"
RESOURCE_SCHEMA = "SCDMP_MF_RS_MK_B01_TECHNICAL_SLICE_RESOURCE_V1"
_FRONTIER_KEYS = {
    "schema", "run_binding", "frontier_id", "frontier_index", "next_frontier_id",
    "completed_invocation_index", "resource_telemetry_file", "source_identity_sha256",
    "scientific_polarity", "ordered_branch", "heldout_slice_authorized",
    "tail_accounting",
}
_RESOURCE_KEYS = {
    "schema", "run_binding", "invocation_index", "source_identity_sha256",
    "frontier_id", "frontier_index", "invocation_telemetry", "tail_accounting",
    "sealed_identity_inventory", "scientific_polarity", "ordered_branch",
}
_ACCOUNTING_KEYS = {
    "prepublication_durable_bytes", "resource_exact_bytes", "frontier_exact_bytes",
    "exact_tail_bytes", "predicted_final_durable_bytes", "durable_cap_bytes",
}


@dataclass(frozen=True, slots=True)
class TechnicalSliceStop(Exception):
    frontier_id: str
    frontier_index: int


def _canonical(value: dict[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _source_identity_digest(root: Path) -> str:
    direct = _read_regular_bytes(
        root / "source-identity.json", label="technical frontier source identity",
    )
    return hashlib.sha256(direct).hexdigest()


def _optional_direct_file(path: Path) -> bytes | None:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return None
    return _read_regular_bytes(path, label="technical frontier artifact")


def technical_frontier_value(
    attempt: Attempt, *, stopped: TechnicalSliceStop,
    telemetry_relative_path: str, tail_accounting: dict[str, object],
) -> dict[str, object]:
    return {
        "schema": FRONTIER_SCHEMA,
        "run_binding": attempt.run_manifest.to_dict(),
        "frontier_id": stopped.frontier_id,
        "frontier_index": stopped.frontier_index,
        "next_frontier_id": (
            TECHNICAL_FRONTIER_IDS[stopped.frontier_index + 1]
            if stopped.frontier_index + 1 < len(TECHNICAL_FRONTIER_IDS) else None
        ),
        "completed_invocation_index": attempt.invocation_index,
        "resource_telemetry_file": telemetry_relative_path,
        "source_identity_sha256": _source_identity_digest(attempt.root),
        "scientific_polarity": None,
        "ordered_branch": None,
        "heldout_slice_authorized": False,
        "tail_accounting": tail_accounting,
    }


def _artifact_path(root: Path, frontier_id: str) -> tuple[Path, ...]:
    parts = frontier_id.split("-")
    if frontier_id.startswith("training-"):
        seed = parts[1]
        update = parts[-1]
        return (root / "foundations" / seed / "checkpoints" / f"update-{update}.json",)
    if frontier_id.startswith("curve-"):
        seed = parts[1]
        update = parts[-1]
        return (root / "foundations" / seed / "curves" / f"update-{update}.json",)
    if frontier_id.startswith("competence-") and frontier_id != "competence-inventory":
        return (root / "foundations" / parts[1] / "competence.json",)
    if frontier_id == "competence-inventory":
        return (root / "foundation-competence-gate.json",)
    if frontier_id.startswith("source-"):
        cell = frontier_id.removeprefix("source-")
        return (
            root / "source-states" / f"{cell}.json",
            root / "source-states" / f"{cell}-not-established.json",
        )
    if frontier_id.startswith("development-"):
        _prefix, seed, *cell = parts
        return (root / "development" / seed / f"{'-'.join(cell)}.json",)
    raise AttemptError("technical frontier artifact coordinate differs")


def _validate_frontier_artifacts(attempt: Attempt, index: int) -> None:
    binding = attempt.run_manifest.to_dict()
    for row_index, frontier_id in enumerate(TECHNICAL_FRONTIER_IDS):
        candidates = _artifact_path(attempt.root, frontier_id)
        present = tuple(
            (path, direct) for path in candidates
            if (direct := _optional_direct_file(path)) is not None
        )
        if row_index <= index:
            if len(present) != 1:
                raise AttemptError("technical frontier atomic artifact inventory differs")
            try:
                direct = present[0][1]
                value = json.loads(direct)
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise AttemptError("technical frontier atomic artifact is unreadable") from error
            if direct != _canonical(value) or value.get("run_binding") != binding:
                raise AttemptError("technical frontier atomic artifact binding differs")
        elif present:
            raise AttemptError("durable atomic artifact exists beyond technical frontier")


def _exact_indexed_paths(directory: Path, count: int) -> tuple[Path, ...]:
    _require_direct_directory(directory, label="technical frontier transaction directory")
    observed = tuple(sorted(directory.glob("invocation-*.json")))
    expected = tuple(directory / f"invocation-{index:06d}.json" for index in range(count))
    if observed != expected:
        raise AttemptError("technical frontier transaction chronology differs")
    return observed


def load_technical_frontier(attempt: Attempt) -> dict[str, object] | None:
    path = attempt.root / "technical-frontier.json"
    direct = _optional_direct_file(path)
    if direct is None:
        return None
    try:
        value = json.loads(direct)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AttemptError("technical frontier is unreadable") from error
    frontier_id = value.get("frontier_id")
    index = value.get("frontier_index")
    completed = attempt.invocation_index - 1
    expected_resource = f"resources/invocation-{completed:06d}.json"
    if (
        not isinstance(value, dict)
        or set(value) != _FRONTIER_KEYS
        or direct != _canonical(value)
        or value.get("schema") != FRONTIER_SCHEMA
        or value.get("run_binding") != attempt.run_manifest.to_dict()
        or value.get("source_identity_sha256") != _source_identity_digest(attempt.root)
        or value.get("completed_invocation_index") != completed
        or value.get("scientific_polarity") is not None
        or value.get("ordered_branch") is not None
        or value.get("heldout_slice_authorized") is not False
        or value.get("resource_telemetry_file") != expected_resource
        or not isinstance(value.get("tail_accounting"), dict)
        or set(value["tail_accounting"]) != _ACCOUNTING_KEYS
        or not isinstance(frontier_id, str)
        or TECHNICAL_FRONTIER_INDEX.get(frontier_id) != index
        or value.get("next_frontier_id") != (
            TECHNICAL_FRONTIER_IDS[index + 1] if index + 1 < len(TECHNICAL_FRONTIER_IDS) else None
        )
    ):
        raise AttemptError("technical frontier binding or chronology differs")
    source_direct = _read_regular_bytes(
        attempt.root / "source-identity.json", label="technical frontier source identity",
    )
    validate_source_identity_bytes(source_direct, compute_source_identity_bytes())
    _exact_indexed_paths(attempt.root / "admissions", attempt.invocation_index + 1)
    _exact_indexed_paths(attempt.root / "invocations", attempt.invocation_index + 1)
    _exact_indexed_paths(attempt.root / "resources", attempt.invocation_index)
    resource_path = attempt.root / expected_resource
    try:
        resource_direct = _read_regular_bytes(
            resource_path, label="prior technical frontier resource telemetry",
        )
        resource = json.loads(resource_direct)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AttemptError("technical frontier resource telemetry is unreadable") from error
    telemetry = resource.get("invocation_telemetry") if isinstance(resource, dict) else None
    sealed_inventory = resource.get("sealed_identity_inventory") if isinstance(resource, dict) else None
    current_inventory = list(validate_sealed_identity(attempt))
    expected_sealed_rows = 5 + completed + 1
    if (
        not isinstance(resource, dict) or set(resource) != _RESOURCE_KEYS
        or resource_direct != _canonical(resource)
        or resource.get("schema") != RESOURCE_SCHEMA
        or resource.get("run_binding") != attempt.run_manifest.to_dict()
        or resource.get("invocation_index") != completed
        or resource.get("source_identity_sha256") != value["source_identity_sha256"]
        or resource.get("frontier_id") != frontier_id
        or resource.get("frontier_index") != index
        or resource.get("tail_accounting") != value["tail_accounting"]
        or not isinstance(sealed_inventory, list)
        or len(sealed_inventory) != expected_sealed_rows
        or sealed_inventory != current_inventory[:expected_sealed_rows]
        or resource.get("scientific_polarity") is not None
        or resource.get("ordered_branch") is not None
        or not isinstance(telemetry, dict)
        or telemetry.get("passed") is not True
        or telemetry.get("failure_reasons") != []
        or telemetry.get("exit_status") != 0
        or value["tail_accounting"].get("resource_exact_bytes") != len(resource_direct)
        or value["tail_accounting"].get("frontier_exact_bytes") != len(direct)
    ):
        raise AttemptError("technical frontier resource binding or telemetry differs")
    _validate_frontier_artifacts(attempt, int(index))
    return value


class FrontierController:
    """Validate exact artifact order and stop only after the requested unit."""

    def __init__(self, attempt: Attempt, *, stop_after: str | None) -> None:
        if stop_after is not None and stop_after not in TECHNICAL_FRONTIER_INDEX:
            raise AttemptError("stop-after-frontier is not a preregistered result-blind coordinate")
        persisted = load_technical_frontier(attempt) if attempt.invocation_index else None
        if attempt.invocation_index and persisted is None:
            raise AttemptError("technical resume lacks a sealed frontier")
        if persisted is not None and stop_after is not None:
            raise AttemptError("a resumed invocation cannot create a second technical slice")
        self.persisted_index = -1 if persisted is None else int(persisted["frontier_index"])
        self.stop_after = stop_after
        self.observed_index = -1

    def unit(self, frontier_id: str, *, created: bool) -> None:
        index = TECHNICAL_FRONTIER_INDEX.get(frontier_id)
        if index is None or index != self.observed_index + 1:
            raise AttemptError("technical artifact frontier order differs")
        if index <= self.persisted_index:
            if created:
                raise AttemptError("resume repeated work at or before its sealed frontier")
        elif not created:
            raise AttemptError("durable work exists beyond the sealed technical frontier")
        self.observed_index = index
        if frontier_id == self.stop_after:
            raise TechnicalSliceStop(frontier_id, index)


__all__ = [
    "FRONTIER_SCHEMA", "RESOURCE_SCHEMA", "TECHNICAL_FRONTIER_IDS", "FrontierController",
    "TechnicalSliceStop", "load_technical_frontier", "technical_frontier_value",
]
