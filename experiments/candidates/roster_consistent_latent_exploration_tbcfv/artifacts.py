"""Atomic, fixture-only frontier artifacts for RCLE-TBCFV r04 construction.

The lifecycle in this module cannot represent an empirical coordinate or model
checkpoint.  It persists deterministic synthetic payloads solely to exercise
completeness, durability, tamper detection, and exact resume behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Mapping, Sequence
import uuid

from .config import (
    LEARNED_PACKAGES,
    SCIENCE_REVISION,
    SCRIPTED_PACKAGES as CONFIG_SCRIPTED_PACKAGES,
)
from .inference import (
    DIRECT_VALUE_VARIABLES,
    HELDOUT_CELLS,
    MECHANISM_VARIABLES,
    PREREQUISITE_VARIABLES,
    TRAINING_CELLS,
)

REVISION_DIGEST = hashlib.sha256(SCIENCE_REVISION.encode("utf-8")).hexdigest()
SCHEMA_VERSION = "rcle-tbcfv-r04-synthetic-frontier-v2"
MODEL_STATE_SCHEMA_VERSION = "rcle-tbcfv-r04-synthetic-model-state-v1"
SCRIPTED_PANEL_SCHEMA_VERSION = "rcle-tbcfv-r04-synthetic-scripted-panel-v1"
BASELINE_SCHEMA_VERSION = "rcle-tbcfv-r04-synthetic-baselines-v1"
SEMANTIC_POSITION_SCHEMA_VERSION = "rcle-tbcfv-r04-synthetic-position-v1"
AGGREGATE_SCHEMA_VERSION = "rcle-tbcfv-r04-synthetic-aggregates-v1"

LEARNED_ARMS = LEARNED_PACKAGES
SCRIPTED_PACKAGES = CONFIG_SCRIPTED_PACKAGES
MODEL_TENSOR_SPECS = (
    ("agent_encoder.first.weight", (32, 3)),
    ("agent_encoder.first.bias", (32,)),
    ("agent_encoder.second.weight", (32, 32)),
    ("agent_encoder.second.bias", (32,)),
    ("beacon_encoder.first.weight", (32, 3)),
    ("beacon_encoder.first.bias", (32,)),
    ("beacon_encoder.second.weight", (32, 32)),
    ("beacon_encoder.second.bias", (32,)),
    ("manager_first.weight", (64, 68)),
    ("manager_first.bias", (64,)),
    ("manager_second.weight", (64, 64)),
    ("manager_second.bias", (64,)),
    ("manager_mean.weight", (4, 64)),
    ("manager_mean.bias", (4,)),
    ("manager_raw_log_scale.weight", (4, 64)),
    ("manager_raw_log_scale.bias", (4,)),
    ("pointer_first.weight", (64, 81)),
    ("pointer_first.bias", (64,)),
    ("pointer_second.weight", (64, 64)),
    ("pointer_second.bias", (64,)),
    ("pointer_score.weight", (1, 64)),
    ("pointer_score.bias", (1,)),
    ("common_update_hidden.weight", (32, 72)),
    ("common_update_hidden.bias", (32,)),
    ("common_update_final.weight", (4, 32)),
    ("common_update_final.bias", (4,)),
    ("agent_update_hidden.weight", (32, 81)),
    ("agent_update_hidden.bias", (32,)),
    ("agent_update_final.weight", (4, 32)),
    ("agent_update_final.bias", (4,)),
)
MODEL_PARAMETER_COUNT = sum(math.prod(shape) for _, shape in MODEL_TENSOR_SPECS)
assert MODEL_PARAMETER_COUNT == 26_161

_HEX_DIGEST = re.compile(r"[0-9a-f]{64}")
_FIXTURE_LABEL = re.compile(r"synthetic_fixture_[a-z0-9][a-z0-9_-]{0,63}")
_FORBIDDEN_KEYS = {
    "checkpoint",
    "coordinate",
    "evaluation",
    "model_checkpoint",
    "result",
    "run_block_id",
    "run_id",
    "scientific_identity",
    "seed",
    "training",
}


class ArtifactError(ValueError):
    """The fixture frontier is malformed, incomplete, duplicate, or corrupt."""


@dataclass(frozen=True)
class SyntheticFrontier:
    fixture_label: str
    source_digest: str
    learned_model_state: Mapping[str, Any]
    scripted_payloads: Mapping[str, Any]
    baselines: Mapping[str, Any]
    semantic_position: Mapping[str, Any]
    arm_order: tuple[str, ...]
    aggregates: Mapping[str, Any]
    fixture_only: bool = True
    non_scientific: bool = True
    revision: str = SCIENCE_REVISION


def compute_source_digest(sources: Mapping[str, bytes | str]) -> str:
    """Hash named source bytes without depending on filesystem ordering."""

    if not isinstance(sources, Mapping) or not sources:
        raise ArtifactError("at least one named source is required")
    digest = hashlib.sha256()
    for name in sorted(sources):
        if not isinstance(name, str) or not name:
            raise ArtifactError("source names must be nonempty strings")
        value = sources[name]
        if isinstance(value, str):
            payload = value.encode("utf-8")
        elif isinstance(value, bytes):
            payload = value
        else:
            raise ArtifactError("source payloads must be bytes or text")
        encoded_name = name.encode("utf-8")
        digest.update(len(encoded_name).to_bytes(8, "big"))
        digest.update(encoded_name)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def create_fixture_root(parent: str | os.PathLike[str]) -> Path:
    """Create a uniquely named construction-fixture root under ``parent``."""

    parent_path = Path(parent)
    parent_path.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="rcle_tbcfv_fixture_", dir=parent_path))


def _canonical_json(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise ArtifactError("fixture payload must be finite canonical JSON") from exc
    return (text + "\n").encode("ascii")


def _reject_forbidden_keys(value: object, location: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ArtifactError(f"{location} contains a non-string key")
            if key.casefold() in _FORBIDDEN_KEYS:
                raise ArtifactError(f"{location} contains forbidden empirical field {key!r}")
            _reject_forbidden_keys(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{location}[{index}]")
    elif isinstance(value, tuple):
        raise ArtifactError(f"{location} contains a tuple that cannot be restored exactly")


def _mapping_exact(value: object, keys: tuple[str, ...], location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise ArtifactError(f"{location} must contain exactly {list(keys)!r}")
    return value


_IDENTITY_KEYS = (
    "schema_version",
    "revision",
    "source_digest",
    "fixture_only",
    "non_scientific",
)
_VALIDITY_FLAGS = {
    "complete_fixture": True,
    "host_source_identity": True,
    "treatment_fidelity": True,
    "analytic_containment": True,
    "evaluation_adaptation": False,
    "forbidden_information": False,
    "unregistered_coordinate": False,
    "finite": True,
}


def _identity(schema_version: str, source_digest: str) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "revision": SCIENCE_REVISION,
        "source_digest": source_digest,
        "fixture_only": True,
        "non_scientific": True,
    }


def _tensor_inventory() -> list[dict[str, object]]:
    return [
        {
            "name": name,
            "shape": list(shape),
            "dtype": "float64",
            "numel": math.prod(shape),
        }
        for name, shape in MODEL_TENSOR_SPECS
    ]


def make_synthetic_model_state_manifest(arm: str, source_digest: str) -> dict[str, object]:
    """Return the exact compact 26,161-entry synthetic state schema for one arm."""

    if arm not in LEARNED_ARMS:
        raise ArtifactError("unknown learned arm")
    result = _identity(MODEL_STATE_SCHEMA_VERSION, source_digest)
    result.update(
        arm=arm,
        parameter_count=MODEL_PARAMETER_COUNT,
        tensors=_tensor_inventory(),
        training_cells=list(TRAINING_CELLS),
        heldout_cells=list(HELDOUT_CELLS),
        learned_panel_inventory={
            "arms": list(LEARNED_ARMS),
            "training_cells": list(TRAINING_CELLS),
            "heldout_cells": list(HELDOUT_CELLS),
        },
        validity=dict(_VALIDITY_FLAGS),
    )
    return result


def make_scripted_panel_manifest(package: str, source_digest: str) -> dict[str, object]:
    """Return the exact deterministic eight-cell scripted construction panel schema."""

    if package not in SCRIPTED_PACKAGES:
        raise ArtifactError("unknown scripted package")
    result = _identity(SCRIPTED_PANEL_SCHEMA_VERSION, source_digest)
    result.update(
        package=package,
        heldout_cells=list(HELDOUT_CELLS),
        scripted_panel_inventory={
            "packages": list(SCRIPTED_PACKAGES),
            "heldout_cells": list(HELDOUT_CELLS),
        },
        validity=dict(_VALIDITY_FLAGS),
    )
    return result


def make_baseline_manifest(
    source_digest: str, *, value: float = 0.0
) -> dict[str, object]:
    """Return stopped finite baselines for exactly eight training cells per arm."""

    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ArtifactError("synthetic baseline value must be finite")
    result = _identity(BASELINE_SCHEMA_VERSION, source_digest)
    result.update(
        cells={arm: {cell: float(value) for cell in TRAINING_CELLS} for arm in LEARNED_ARMS},
        validity=dict(_VALIDITY_FLAGS),
    )
    return result


def make_semantic_position_manifest(
    source_digest: str,
    *,
    phase: str = "fixture_ready",
    update_block_offset: int = 0,
    episode_offset: int = 0,
    host_tick_offset: int = 0,
    claim_clock_offset: int = 0,
    arm_cursor: int = 0,
) -> dict[str, object]:
    """Return bounded semantic fixture position, never an empirical coordinate."""

    result = _identity(SEMANTIC_POSITION_SCHEMA_VERSION, source_digest)
    result.update(
        phase=phase,
        update_block_offset=update_block_offset,
        episode_offset=episode_offset,
        host_tick_offset=host_tick_offset,
        claim_clock_offset=claim_clock_offset,
        arm_cursor=arm_cursor,
        validity=dict(_VALIDITY_FLAGS),
    )
    return result


def _aggregate_family(names: Sequence[str], count: int, value: float) -> dict[str, object]:
    return {
        name: {"count": count, "sum": float(value), "sum_squares": float(value * value)}
        for name in names
    }


def make_aggregate_manifest(
    source_digest: str, *, count: int = 0, value: float = 0.0
) -> dict[str, object]:
    """Return exact finite synthetic accumulators for all 58 registered variables."""

    if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 20:
        raise ArtifactError("synthetic aggregate count must be an integer in [0,20]")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ArtifactError("synthetic aggregate value must be finite")
    result = _identity(AGGREGATE_SCHEMA_VERSION, source_digest)
    result.update(
        families={
            "prerequisite": _aggregate_family(PREREQUISITE_VARIABLES, count, float(value)),
            "direct_value": _aggregate_family(DIRECT_VALUE_VARIABLES, count, float(value)),
            "mechanism": _aggregate_family(MECHANISM_VARIABLES, count, float(value)),
        },
        validity=dict(_VALIDITY_FLAGS),
    )
    return result


def _validate_identity(
    value: object, *, schema_version: str, source_digest: str, extra_keys: tuple[str, ...], location: str
) -> Mapping[str, Any]:
    expected_keys = (*_IDENTITY_KEYS, *extra_keys)
    mapping = _mapping_exact(value, expected_keys, location)
    expected = _identity(schema_version, source_digest)
    if any(mapping[key] != expected[key] for key in _IDENTITY_KEYS):
        raise ArtifactError(f"{location} identity/schema mismatch")
    return mapping


def _validate_validity(value: object, location: str) -> None:
    if not isinstance(value, Mapping) or dict(value) != _VALIDITY_FLAGS:
        raise ArtifactError(f"{location} validity flags are incomplete or failed")


def _validate_learned_state(value: object, arm: str, source_digest: str) -> None:
    mapping = _validate_identity(
        value,
        schema_version=MODEL_STATE_SCHEMA_VERSION,
        source_digest=source_digest,
        extra_keys=(
            "arm",
            "parameter_count",
            "tensors",
            "training_cells",
            "heldout_cells",
            "learned_panel_inventory",
            "validity",
        ),
        location=f"learned_model_state.{arm}",
    )
    expected = make_synthetic_model_state_manifest(arm, source_digest)
    if dict(mapping) != expected:
        raise ArtifactError(f"learned_model_state.{arm} tensor or panel schema mismatch")


def _validate_scripted_panel(value: object, package: str, source_digest: str) -> None:
    mapping = _validate_identity(
        value,
        schema_version=SCRIPTED_PANEL_SCHEMA_VERSION,
        source_digest=source_digest,
        extra_keys=("package", "heldout_cells", "scripted_panel_inventory", "validity"),
        location=f"scripted_payloads.{package}",
    )
    expected = make_scripted_panel_manifest(package, source_digest)
    if dict(mapping) != expected:
        raise ArtifactError(f"scripted_payloads.{package} panel schema mismatch")


def _is_finite_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _validate_baselines(value: object, source_digest: str) -> None:
    mapping = _validate_identity(
        value,
        schema_version=BASELINE_SCHEMA_VERSION,
        source_digest=source_digest,
        extra_keys=("cells", "validity"),
        location="baselines",
    )
    _validate_validity(mapping["validity"], "baselines")
    cells = _mapping_exact(mapping["cells"], LEARNED_ARMS, "baselines.cells")
    for arm in LEARNED_ARMS:
        arm_cells = _mapping_exact(cells[arm], TRAINING_CELLS, f"baselines.cells.{arm}")
        if any(not _is_finite_number(arm_cells[cell]) for cell in TRAINING_CELLS):
            raise ArtifactError(f"baselines.cells.{arm} contains a nonfinite value")


def _bounded_int(value: object, low: int, high: int, location: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ArtifactError(f"{location} must be an integer in [{low},{high}]")


def _validate_semantic_position(value: object, source_digest: str) -> None:
    mapping = _validate_identity(
        value,
        schema_version=SEMANTIC_POSITION_SCHEMA_VERSION,
        source_digest=source_digest,
        extra_keys=(
            "phase",
            "update_block_offset",
            "episode_offset",
            "host_tick_offset",
            "claim_clock_offset",
            "arm_cursor",
            "validity",
        ),
        location="semantic_position",
    )
    if mapping["phase"] not in ("fixture_ready", "fixture_after_synthetic_step"):
        raise ArtifactError("semantic_position.phase is unsupported")
    _bounded_int(mapping["update_block_offset"], 0, 800, "semantic_position.update_block_offset")
    _bounded_int(mapping["episode_offset"], 0, 64, "semantic_position.episode_offset")
    _bounded_int(mapping["host_tick_offset"], 0, 64, "semantic_position.host_tick_offset")
    _bounded_int(mapping["claim_clock_offset"], 0, 16, "semantic_position.claim_clock_offset")
    _bounded_int(mapping["arm_cursor"], 0, len(LEARNED_ARMS), "semantic_position.arm_cursor")
    _validate_validity(mapping["validity"], "semantic_position")


def _validate_aggregates(value: object, source_digest: str) -> None:
    mapping = _validate_identity(
        value,
        schema_version=AGGREGATE_SCHEMA_VERSION,
        source_digest=source_digest,
        extra_keys=("families", "validity"),
        location="aggregates",
    )
    _validate_validity(mapping["validity"], "aggregates")
    families = _mapping_exact(
        mapping["families"], ("prerequisite", "direct_value", "mechanism"), "aggregates.families"
    )
    for family, names in (
        ("prerequisite", PREREQUISITE_VARIABLES),
        ("direct_value", DIRECT_VALUE_VARIABLES),
        ("mechanism", MECHANISM_VARIABLES),
    ):
        variables = _mapping_exact(families[family], names, f"aggregates.families.{family}")
        for name in names:
            summary = _mapping_exact(
                variables[name], ("count", "sum", "sum_squares"), f"aggregates.{family}.{name}"
            )
            _bounded_int(summary["count"], 0, 20, f"aggregates.{family}.{name}.count")
            if not _is_finite_number(summary["sum"]) or not _is_finite_number(
                summary["sum_squares"]
            ):
                raise ArtifactError(f"aggregates.{family}.{name} is nonfinite")
            if float(summary["sum_squares"]) < 0.0:
                raise ArtifactError(f"aggregates.{family}.{name}.sum_squares must be nonnegative")


def _validate_frontier(frontier: SyntheticFrontier) -> None:
    if frontier.fixture_only is not True or frontier.non_scientific is not True:
        raise ArtifactError("frontier must be explicitly fixture-only and non-scientific")
    if frontier.revision != SCIENCE_REVISION:
        raise ArtifactError("science revision mismatch")
    if not isinstance(frontier.fixture_label, str) or not _FIXTURE_LABEL.fullmatch(
        frontier.fixture_label
    ):
        raise ArtifactError("fixture_label must match synthetic_fixture_<safe-label>")
    if not isinstance(frontier.source_digest, str) or not _HEX_DIGEST.fullmatch(
        frontier.source_digest
    ):
        raise ArtifactError("source_digest must be a lowercase SHA-256 digest")
    if tuple(frontier.arm_order) != LEARNED_ARMS:
        raise ArtifactError("arm_order must equal the frozen five-arm order")
    _mapping_exact(frontier.learned_model_state, LEARNED_ARMS, "learned_model_state")
    _mapping_exact(frontier.scripted_payloads, SCRIPTED_PACKAGES, "scripted_payloads")
    for arm in LEARNED_ARMS:
        _validate_learned_state(frontier.learned_model_state[arm], arm, frontier.source_digest)
    for package in SCRIPTED_PACKAGES:
        _validate_scripted_panel(
            frontier.scripted_payloads[package], package, frontier.source_digest
        )
    _validate_baselines(frontier.baselines, frontier.source_digest)
    _validate_semantic_position(frontier.semantic_position, frontier.source_digest)
    _validate_aggregates(frontier.aggregates, frontier.source_digest)
    for name, value in (
        ("learned_model_state", frontier.learned_model_state),
        ("scripted_payloads", frontier.scripted_payloads),
        ("baselines", frontier.baselines),
        ("semantic_position", frontier.semantic_position),
        ("aggregates", frontier.aggregates),
    ):
        if not isinstance(value, Mapping):
            raise ArtifactError(f"{name} must be a mapping")
        if not value:
            raise ArtifactError(f"{name} must be nonempty")
        _reject_forbidden_keys(value, name)
        _canonical_json(value)


def _write_exclusive(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source_revision_digest(source_digest: str) -> str:
    return _sha256(f"{source_digest}:{REVISION_DIGEST}".encode("ascii"))


def _payload_files(frontier: SyntheticFrontier) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for arm in LEARNED_ARMS:
        files[f"learned/{arm}.json"] = _canonical_json(frontier.learned_model_state[arm])
    for package in SCRIPTED_PACKAGES:
        files[f"scripted/{package}.json"] = _canonical_json(frontier.scripted_payloads[package])
    files["baselines.json"] = _canonical_json(frontier.baselines)
    files["semantic_position.json"] = _canonical_json(frontier.semantic_position)
    files["aggregates.json"] = _canonical_json(frontier.aggregates)
    return files


def publish_synthetic_frontier(
    root: str | os.PathLike[str], frontier: SyntheticFrontier
) -> Path:
    """Durably publish one complete deterministic synthetic frontier.

    Every payload file is created exclusively and fsynced.  The COMPLETE marker
    is itself published by atomic rename, followed by an atomic staging-directory
    rename.  An existing label is always a duplicate error.
    """

    _validate_frontier(frontier)
    root_path = Path(root)
    if not root_path.is_dir():
        raise ArtifactError("fixture root must already exist and be a directory")
    final_path = root_path / frontier.fixture_label
    if final_path.exists():
        raise ArtifactError(f"duplicate fixture frontier {frontier.fixture_label!r}")

    staging = root_path / f".{frontier.fixture_label}.tmp-{uuid.uuid4().hex}"
    try:
        staging.mkdir()
        (staging / "learned").mkdir()
        (staging / "scripted").mkdir()
        payloads = _payload_files(frontier)
        for relative_name, payload in payloads.items():
            _write_exclusive(staging / relative_name, payload)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "revision": SCIENCE_REVISION,
            "revision_digest": REVISION_DIGEST,
            "source_digest": frontier.source_digest,
            "source_revision_digest": _source_revision_digest(frontier.source_digest),
            "fixture_label": frontier.fixture_label,
            "fixture_only": True,
            "non_scientific": True,
            "arm_order": list(LEARNED_ARMS),
            "learned_arms": list(LEARNED_ARMS),
            "scripted_packages": list(SCRIPTED_PACKAGES),
            "file_digests": {name: _sha256(payload) for name, payload in sorted(payloads.items())},
        }
        manifest_payload = _canonical_json(manifest)
        _write_exclusive(staging / "manifest.json", manifest_payload)
        marker_payload = _canonical_json(
            {
                "manifest_sha256": _sha256(manifest_payload),
                "fixture_only": True,
                "non_scientific": True,
            }
        )
        marker_temp = staging / f".COMPLETE.tmp-{uuid.uuid4().hex}"
        _write_exclusive(marker_temp, marker_payload)
        os.replace(marker_temp, staging / "COMPLETE")
        if final_path.exists():
            raise ArtifactError(f"duplicate fixture frontier {frontier.fixture_label!r}")
        os.rename(staging, final_path)
        return final_path
    except Exception:
        if staging.exists() and staging.parent.resolve() == root_path.resolve():
            shutil.rmtree(staging)
        raise


def _read_bytes(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ArtifactError(f"required regular file is missing: {path.name}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ArtifactError(f"cannot read fixture artifact {path.name}") from exc


def _read_json(path: Path) -> Any:
    payload = _read_bytes(path)
    try:
        return json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"malformed JSON artifact {path.name}") from exc


def restore_synthetic_frontier(
    path: str | os.PathLike[str], *, expected_source_digest: str | None = None
) -> SyntheticFrontier:
    """Validate every byte and exactly restore a complete synthetic frontier."""

    directory = Path(path)
    if not directory.is_dir() or directory.is_symlink():
        raise ArtifactError("frontier path must be a regular directory")
    marker_payload = _read_bytes(directory / "COMPLETE")
    manifest_payload = _read_bytes(directory / "manifest.json")
    try:
        marker = json.loads(marker_payload.decode("ascii"))
        manifest = json.loads(manifest_payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactError("marker or manifest is malformed") from exc
    if not isinstance(marker, Mapping) or marker != {
        "fixture_only": True,
        "manifest_sha256": _sha256(manifest_payload),
        "non_scientific": True,
    }:
        raise ArtifactError("COMPLETE marker does not bind the manifest")
    if not isinstance(manifest, Mapping):
        raise ArtifactError("manifest must be a mapping")
    expected_manifest_keys = {
        "schema_version",
        "revision",
        "revision_digest",
        "source_digest",
        "source_revision_digest",
        "fixture_label",
        "fixture_only",
        "non_scientific",
        "arm_order",
        "learned_arms",
        "scripted_packages",
        "file_digests",
    }
    if set(manifest) != expected_manifest_keys:
        raise ArtifactError("manifest schema is not exact")
    arm_order = manifest["arm_order"]
    learned_arms = manifest["learned_arms"]
    scripted_packages = manifest["scripted_packages"]
    if not all(isinstance(value, list) for value in (arm_order, learned_arms, scripted_packages)):
        raise ArtifactError("manifest frozen inventories are malformed")
    if (
        manifest["schema_version"] != SCHEMA_VERSION
        or manifest["revision"] != SCIENCE_REVISION
        or manifest["revision_digest"] != REVISION_DIGEST
        or manifest["fixture_only"] is not True
        or manifest["non_scientific"] is not True
        or manifest["fixture_label"] != directory.name
        or tuple(arm_order) != LEARNED_ARMS
        or tuple(learned_arms) != LEARNED_ARMS
        or tuple(scripted_packages) != SCRIPTED_PACKAGES
    ):
        raise ArtifactError("manifest identity or frozen schema mismatch")
    source_digest = manifest["source_digest"]
    if not isinstance(source_digest, str) or not _HEX_DIGEST.fullmatch(source_digest):
        raise ArtifactError("manifest source digest is malformed")
    if manifest["source_revision_digest"] != _source_revision_digest(source_digest):
        raise ArtifactError("manifest source/revision digest mismatch")
    if expected_source_digest is not None and source_digest != expected_source_digest:
        raise ArtifactError("source digest mismatch")
    file_digests = manifest["file_digests"]
    if not isinstance(file_digests, Mapping):
        raise ArtifactError("manifest file digests are malformed")

    expected_payload_names = set(_payload_files(
        SyntheticFrontier(
            fixture_label=directory.name,
            source_digest=source_digest,
            learned_model_state={arm: {} for arm in LEARNED_ARMS},
            scripted_payloads={package: {} for package in SCRIPTED_PACKAGES},
            baselines={},
            semantic_position={},
            arm_order=LEARNED_ARMS,
            aggregates={},
        )
    ))
    if set(file_digests) != expected_payload_names:
        raise ArtifactError("manifest payload inventory is incomplete or unexpected")
    actual_top = {child.name for child in directory.iterdir()}
    if actual_top != {"learned", "scripted", "baselines.json", "semantic_position.json", "aggregates.json", "manifest.json", "COMPLETE"}:
        raise ArtifactError("frontier contains incomplete or unexpected top-level artifacts")
    if {child.name for child in (directory / "learned").iterdir()} != {
        f"{arm}.json" for arm in LEARNED_ARMS
    }:
        raise ArtifactError("learned-arm payload inventory is incomplete or unexpected")
    if {child.name for child in (directory / "scripted").iterdir()} != {
        f"{package}.json" for package in SCRIPTED_PACKAGES
    }:
        raise ArtifactError("scripted-package payload inventory is incomplete or unexpected")

    decoded: dict[str, Any] = {}
    for relative_name in sorted(expected_payload_names):
        payload = _read_bytes(directory / relative_name)
        if file_digests[relative_name] != _sha256(payload):
            raise ArtifactError(f"tamper or corruption detected in {relative_name}")
        try:
            decoded[relative_name] = json.loads(payload.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArtifactError(f"malformed JSON artifact {relative_name}") from exc

    restored = SyntheticFrontier(
        fixture_label=directory.name,
        source_digest=source_digest,
        learned_model_state={arm: decoded[f"learned/{arm}.json"] for arm in LEARNED_ARMS},
        scripted_payloads={
            package: decoded[f"scripted/{package}.json"] for package in SCRIPTED_PACKAGES
        },
        baselines=decoded["baselines.json"],
        semantic_position=decoded["semantic_position.json"],
        arm_order=LEARNED_ARMS,
        aggregates=decoded["aggregates.json"],
    )
    _validate_frontier(restored)
    return restored


def scan_resume_root(
    root: str | os.PathLike[str], *, expected_source_digest: str | None = None
) -> tuple[SyntheticFrontier, ...]:
    """Fail closed unless every child is one complete, untampered frontier."""

    root_path = Path(root)
    if not root_path.is_dir() or root_path.is_symlink():
        raise ArtifactError("resume root must be a regular directory")
    restored: list[SyntheticFrontier] = []
    labels: set[str] = set()
    for child in sorted(root_path.iterdir(), key=lambda item: item.name):
        if not child.is_dir() or child.is_symlink() or child.name.startswith("."):
            raise ArtifactError(f"incomplete or unexpected resume entry {child.name!r}")
        frontier = restore_synthetic_frontier(child, expected_source_digest=expected_source_digest)
        if frontier.fixture_label in labels:
            raise ArtifactError(f"duplicate fixture frontier {frontier.fixture_label!r}")
        labels.add(frontier.fixture_label)
        restored.append(frontier)
    return tuple(restored)


__all__ = [
    "ArtifactError",
    "AGGREGATE_SCHEMA_VERSION",
    "BASELINE_SCHEMA_VERSION",
    "LEARNED_ARMS",
    "MODEL_PARAMETER_COUNT",
    "MODEL_STATE_SCHEMA_VERSION",
    "MODEL_TENSOR_SPECS",
    "REVISION_DIGEST",
    "SCHEMA_VERSION",
    "SCIENCE_REVISION",
    "SCRIPTED_PACKAGES",
    "SCRIPTED_PANEL_SCHEMA_VERSION",
    "SEMANTIC_POSITION_SCHEMA_VERSION",
    "SyntheticFrontier",
    "compute_source_digest",
    "create_fixture_root",
    "make_aggregate_manifest",
    "make_baseline_manifest",
    "make_scripted_panel_manifest",
    "make_semantic_position_manifest",
    "make_synthetic_model_state_manifest",
    "publish_synthetic_frontier",
    "restore_synthetic_frontier",
    "scan_resume_root",
]
