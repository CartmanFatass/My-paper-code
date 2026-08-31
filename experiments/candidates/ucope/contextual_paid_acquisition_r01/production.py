"""Create-once production preflight and complete-only BELIEF orchestration.

Importing this module is runtime-light: PyTorch and all learner/result modules are loaded only
inside the production operations that require them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import ctypes
import importlib
import json
import os
import shutil
import sys
import tempfile

from .contract import (
    BATCH_SIZE,
    CONTRACT_ID,
    DISPLAYED_COUNT_FLOOR,
    INFERENCE_READINESS,
    PRODUCTION_MODE,
    PRODUCTION_WORKLOAD,
    RESOURCE_CEILING,
    SCHEMA_VERSION,
    SEED_SLOTS,
    default_manifest,
    validate_contract,
)
from .schema import canonical_bytes


PRODUCTION_PREFLIGHT_FORMAT = "UCOPE_CPA_PRODUCTION_RESOURCE_SUPPORT_PREFLIGHT_V2"
RESULT_FILENAME = "belief-result.json"
SUPPORT_ARTIFACT_RELATIVE = "support/support-preflight.json"
REQUIRED_PYTHON = (3, 10)
REQUIRED_TORCH = "2.7.0+cpu"
ESTIMATED_PEAK_MEMORY_BYTES = 2 * 1024**3
MINIMUM_LIVE_AVAILABLE_MEMORY_BYTES = 4 * 1024**3
MINIMUM_FREE_DISK_BYTES = 4 * 1024**3
MAXIMUM_RESULT_WALL_SECONDS = 1_800
# 2026-08-31 bounded accepted-runtime benchmark at 640 episodes/context:
# 1.876490 s exact seed-row replay + 7.055924 s for 20 cadence-1 updates.
# Linear 32x episode/update scaling across ten seeds with a 25% guard rounds up to 3,600 s.
PROJECTED_RESULT_WALL_SECONDS = 3_600


class ProductionPreflightError(RuntimeError):
    """Raised before support materialization when the production host is ineligible."""


def _all_mapping_keys(value: Any):
    if isinstance(value, Mapping):
        yield from value
        for item in value.values():
            yield from _all_mapping_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _all_mapping_keys(item)


def _atomic_create_bytes(path: str | Path, payload: bytes) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
        os.unlink(temporary)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return destination


def create_production_manifest(path: str | Path) -> Path:
    """Create exactly one immutable default PRODUCTION manifest."""
    return _atomic_create_bytes(path, canonical_bytes(default_manifest(PRODUCTION_MODE)))


def _available_memory_bytes() -> int:
    if os.name == "nt":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("GlobalMemoryStatusEx failed")
        return int(status.available_physical)
    page_size = int(os.sysconf("SC_PAGE_SIZE"))
    available_pages = int(os.sysconf("SC_AVPHYS_PAGES"))
    return page_size * available_pages


def _disk_probe(path: str | Path) -> Path:
    candidate = Path(path).resolve()
    while not candidate.exists():
        if candidate.parent == candidate:
            raise ProductionPreflightError(f"no existing ancestor for disk probe: {path}")
        candidate = candidate.parent
    return candidate


def _runtime_resource_record(output_root: str | Path) -> dict[str, Any]:
    """Measure and enforce the exact CPU runtime before any support rows are created."""
    issues: list[str] = []
    python_major_minor = tuple(sys.version_info[:2])
    if python_major_minor != REQUIRED_PYTHON:
        issues.append(
            f"Python 3.10 required; observed {python_major_minor[0]}.{python_major_minor[1]}"
        )

    torch = None
    torch_version = None
    torch_cuda_version = None
    torch_cuda_available = None
    torch_intraop_threads = None
    torch_interop_threads = None
    deterministic_algorithms = None
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        issues.append(f"torch 2.7.0+cpu required but unavailable: {exc}")
    if torch is not None:
        torch_version = getattr(torch, "__version__", None)
        if torch_version != REQUIRED_TORCH:
            issues.append(f"torch 2.7.0+cpu required; observed {torch_version!r}")
        torch_cuda_version = getattr(getattr(torch, "version", None), "cuda", None)
        try:
            torch_cuda_available = bool(torch.cuda.is_available())
        except Exception as exc:
            issues.append(f"CPU-only torch CUDA probe failed: {exc}")
        if torch_cuda_version is not None or torch_cuda_available is not False:
            issues.append(
                "CPU-only torch required; CUDA build/runtime availability must both be absent"
            )
        try:
            torch.set_num_threads(RESOURCE_CEILING["torch_intraop_threads"])
            torch_intraop_threads = int(torch.get_num_threads())
        except Exception as exc:
            issues.append(f"unable to enforce one torch thread: {exc}")
        if torch_intraop_threads != RESOURCE_CEILING["torch_intraop_threads"]:
            issues.append(f"one torch intra-op thread required; observed {torch_intraop_threads!r}")
        try:
            torch.set_num_interop_threads(RESOURCE_CEILING["torch_interop_threads"])
            torch_interop_threads = int(torch.get_num_interop_threads())
        except Exception as exc:
            issues.append(f"unable to enforce one torch inter-op thread: {exc}")
        if torch_interop_threads != RESOURCE_CEILING["torch_interop_threads"]:
            issues.append(f"one torch inter-op thread required; observed {torch_interop_threads!r}")
        try:
            torch.use_deterministic_algorithms(True)
            deterministic_algorithms = bool(torch.are_deterministic_algorithms_enabled())
        except Exception as exc:
            issues.append(f"unable to enforce deterministic torch algorithms: {exc}")
        if deterministic_algorithms is not True:
            issues.append("deterministic torch algorithms must be enabled")

    try:
        live_memory = _available_memory_bytes()
    except Exception as exc:
        live_memory = -1
        issues.append(f"unable to measure live available memory: {exc}")
    if live_memory < MINIMUM_LIVE_AVAILABLE_MEMORY_BYTES:
        issues.append(
            "insufficient live memory: at least 4 GiB available RAM is required; "
            f"observed {max(live_memory, 0)} bytes"
        )

    try:
        free_disk = int(shutil.disk_usage(_disk_probe(output_root)).free)
    except Exception as exc:
        free_disk = -1
        issues.append(f"unable to measure free disk: {exc}")
    if free_disk < MINIMUM_FREE_DISK_BYTES:
        issues.append(
            "insufficient free disk: at least 4 GiB is required; "
            f"observed {max(free_disk, 0)} bytes"
        )

    projected_wall = PROJECTED_RESULT_WALL_SECONDS
    wall_safe = (
        type(projected_wall) is int
        and 0 < projected_wall <= MAXIMUM_RESULT_WALL_SECONDS
    )
    if not wall_safe:
        observed = "unavailable" if projected_wall is None else repr(projected_wall)
        issues.append(
            "bounded Torch result-wall projection must be positive and no greater than "
            f"1800 seconds; observed {observed}"
        )

    if issues:
        raise ProductionPreflightError(
            "production preflight failed before support materialization: " + " | ".join(issues)
        )
    return {
        "python_major_minor": list(REQUIRED_PYTHON),
        "torch_version": REQUIRED_TORCH,
        "torch_cuda_version": None,
        "torch_cuda_available": False,
        "workers": RESOURCE_CEILING["workers"],
        "torch_intraop_threads": RESOURCE_CEILING["torch_intraop_threads"],
        "torch_interop_threads": RESOURCE_CEILING["torch_interop_threads"],
        "batch_size": BATCH_SIZE,
        "model_checkpoints_per_seed": RESOURCE_CEILING["model_checkpoints_per_seed"],
        "checkpoint_cadence_batches": RESOURCE_CEILING["checkpoint_cadence_batches"],
        "deterministic_algorithms": deterministic_algorithms,
        "estimated_peak_memory_bytes": ESTIMATED_PEAK_MEMORY_BYTES,
        "minimum_live_available_memory_bytes": MINIMUM_LIVE_AVAILABLE_MEMORY_BYTES,
        "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
        "live_available_memory_bytes": live_memory,
        "live_free_disk_bytes": free_disk,
        "projected_result_wall_seconds": projected_wall,
        "maximum_result_wall_seconds": MAXIMUM_RESULT_WALL_SECONDS,
        "wall_safe": wall_safe,
    }


def _materialize_support(manifest: str | Path | Mapping[str, Any], output_root: str | Path):
    from .support import preflight_support

    return preflight_support(manifest, output_root)


def _validate_support(path: str | Path, manifest: str | Path | Mapping[str, Any]):
    from .support import validate_support_structure

    return validate_support_structure(path, manifest)


def _expected_resources(value: Mapping[str, Any]) -> bool:
    fixed = {
        "python_major_minor": list(REQUIRED_PYTHON),
        "torch_version": REQUIRED_TORCH,
        "torch_cuda_version": None,
        "torch_cuda_available": False,
        "workers": 1,
        "torch_intraop_threads": 1,
        "torch_interop_threads": 1,
        "batch_size": BATCH_SIZE,
        "model_checkpoints_per_seed": 1,
        "checkpoint_cadence_batches": 1,
        "deterministic_algorithms": True,
        "estimated_peak_memory_bytes": ESTIMATED_PEAK_MEMORY_BYTES,
        "minimum_live_available_memory_bytes": MINIMUM_LIVE_AVAILABLE_MEMORY_BYTES,
        "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
        "maximum_result_wall_seconds": MAXIMUM_RESULT_WALL_SECONDS,
        "wall_safe": True,
    }
    return (
        isinstance(value, Mapping)
        and set(value) == {
            *fixed,
            "live_available_memory_bytes",
            "live_free_disk_bytes",
            "projected_result_wall_seconds",
        }
        and all(value.get(key) == expected for key, expected in fixed.items())
        and type(value.get("live_available_memory_bytes")) is int
        and value["live_available_memory_bytes"] >= MINIMUM_LIVE_AVAILABLE_MEMORY_BYTES
        and type(value.get("live_free_disk_bytes")) is int
        and value["live_free_disk_bytes"] >= MINIMUM_FREE_DISK_BYTES
        and type(value.get("projected_result_wall_seconds")) is int
        and value["projected_result_wall_seconds"] == PROJECTED_RESULT_WALL_SECONDS
        and 0 < value["projected_result_wall_seconds"] <= MAXIMUM_RESULT_WALL_SECONDS
    )


def _displayed_count_support(support_record: Mapping[str, Any]) -> dict[str, int]:
    try:
        counts = support_record["seed_context_counts"]
        observed = [
            value
            for cell in counts.values()
            for value in cell["displayed_short_count"].values()
        ]
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError("production displayed-count support structure mismatch") from exc
    if not observed or any(type(value) is not int or value < 0 for value in observed):
        raise ValueError("production displayed-count support values must be nonnegative integers")
    value = {"floor": DISPLAYED_COUNT_FLOOR, "global_minimum": min(observed)}
    if value["global_minimum"] != 361:
        raise ValueError(
            "production global displayed-count minimum must be exactly 361; "
            f"observed {value['global_minimum']}"
        )
    return value


def validate_production_preflight(
    artifact: str | Path,
    manifest: str | Path | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_path = Path(artifact)
    if artifact_path.is_symlink() or not artifact_path.is_file():
        raise ValueError("production preflight artifact must be a regular non-symlink file")
    with artifact_path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    required = {
        "format", "schema_version", "contract_id", "mode", "manifest", "resources",
        "workload", "displayed_count_support", "support_artifact", "support_record", "complete", "optimizer_updates",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("production preflight field inventory mismatch")
    manifest_value = validate_contract(value["manifest"] if manifest is None else manifest)
    if manifest_value["mode"] != PRODUCTION_MODE or value["manifest"] != manifest_value:
        raise ValueError("production preflight requires the exact PRODUCTION manifest")
    if (
        value["format"] != PRODUCTION_PREFLIGHT_FORMAT
        or type(value["schema_version"]) is not int
        or value["schema_version"] != SCHEMA_VERSION
        or value["contract_id"] != CONTRACT_ID
        or value["mode"] != PRODUCTION_MODE
        or type(value["complete"]) is not bool
        or not value["complete"]
        or type(value["optimizer_updates"]) is not int
        or value["optimizer_updates"] != 0
        or value["workload"] != PRODUCTION_WORKLOAD
        or not _expected_resources(value["resources"])
        or value["support_artifact"] != SUPPORT_ARTIFACT_RELATIVE
    ):
        raise ValueError("production preflight frozen value mismatch")
    forbidden = ("hash", "digest", "lease", "approval", "identity")
    if any(any(token in str(key).lower() for token in forbidden) for key in _all_mapping_keys(value)):
        raise ValueError("production preflight contains forbidden coordination or identity fields")
    support_root = artifact_path.parent / "support"
    if support_root.is_symlink() or not support_root.is_dir():
        raise ValueError("production support root must be a regular non-symlink directory")
    support_path = artifact_path.parent / Path(SUPPORT_ARTIFACT_RELATIVE)
    if support_path.resolve().parent != (artifact_path.parent / "support").resolve():
        raise ValueError("production support path escaped its fixed location")
    if support_path.is_symlink():
        raise ValueError("production support artifact must not be a symlink")
    support_record = _validate_support(support_path, manifest_value)
    if support_record != value["support_record"]:
        raise ValueError("production preflight embedded support record mismatch")
    if value["displayed_count_support"] != _displayed_count_support(support_record):
        raise ValueError("production displayed-count envelope mismatch")
    return value


def preflight_production(
    manifest: str | Path | Mapping[str, Any], output_root: str | Path
) -> Path:
    """Gate resources, materialize support, then atomically expose one complete directory."""
    manifest_value = validate_contract(manifest)
    if manifest_value["mode"] != PRODUCTION_MODE:
        raise ValueError("production preflight rejects TEST_ONLY manifests")
    root = Path(output_root)
    if root.exists():
        raise FileExistsError(f"output root must not already exist: {root}")
    resources = _runtime_resource_record(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.staging-", dir=root.parent))
    try:
        support_path = _materialize_support(manifest_value, staging / "support")
        with Path(support_path).open("r", encoding="utf-8") as stream:
            support_record = json.load(stream)
        displayed_count_support = _displayed_count_support(support_record)
        envelope = {
            "format": PRODUCTION_PREFLIGHT_FORMAT,
            "schema_version": SCHEMA_VERSION,
            "contract_id": CONTRACT_ID,
            "mode": PRODUCTION_MODE,
            "manifest": manifest_value,
            "resources": resources,
            "workload": PRODUCTION_WORKLOAD,
            "displayed_count_support": displayed_count_support,
            "support_artifact": SUPPORT_ARTIFACT_RELATIVE,
            "support_record": support_record,
            "complete": True,
            "optimizer_updates": 0,
        }
        artifact_path = staging / "production-preflight.json"
        _atomic_create_bytes(artifact_path, canonical_bytes(envelope))
        validate_production_preflight(artifact_path, manifest_value)
        os.rename(staging, root)
        return root / artifact_path.name
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def checkpoint_path(output_root: str | Path, seed_slot: str) -> Path:
    if seed_slot not in SEED_SLOTS:
        raise ValueError("unknown seed slot")
    return Path(output_root) / "checkpoints" / f"checkpoint-{SEED_SLOTS.index(seed_slot):02d}.pt"


def _load_seed_training_rows(support_artifact, seed_slot, support_record):
    from .training import _load_seed_rows

    return _load_seed_rows(Path(support_artifact), seed_slot, support_record)


def _train_seed(
    seed_slot, support_artifact, checkpoint, support_record, rows, resume_from=None
):
    from .training import _train_one_seed_from_validated_support

    return _train_one_seed_from_validated_support(
        seed_slot,
        support_artifact,
        checkpoint,
        support_record=support_record,
        rows=rows,
        resume_from=resume_from,
    )


def _evaluate_checkpoint(checkpoint):
    from .evaluation import evaluate_heldout_cells

    return evaluate_heldout_cells(checkpoint)


def _load_checkpoint(checkpoint):
    from .checkpoint import load_checkpoint

    return load_checkpoint(checkpoint)


def _build_complete_result(**kwargs):
    from .artifact import build_complete_result

    return build_complete_result(**kwargs)


def _publish_complete_result(value, path):
    from .artifact import publish_complete_result

    return publish_complete_result(value, path)


def _checkpoint_record(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in raw.items() if key not in ("model_state", "optimizer_state")}


def _validate_checkpoint_binding(
    raw: Mapping[str, Any],
    seed_slot: str,
    support_record: Mapping[str, Any],
    *,
    require_complete: bool,
) -> None:
    expected_batches = PRODUCTION_WORKLOAD["optimizer_updates"] // len(SEED_SLOTS)
    completed = raw.get("completed_batches")
    bound = (
        raw.get("seed_slot") == seed_slot
        and raw.get("mode") == PRODUCTION_MODE
        and raw.get("support_record") == support_record
        and type(completed) is int
        and 0 <= completed <= expected_batches
        and raw.get("total_batches") == expected_batches
        and raw.get("optimizer_updates") == completed
    )
    if require_complete:
        bound = bound and completed == expected_batches
    if not bound:
        state = "complete " if require_complete else ""
        raise RuntimeError(f"fixed checkpoint is not a {state}deterministic checkpoint for {seed_slot}")


def _complete_production_checkpoints(
    output_root: str | Path,
    support_path: str | Path,
    support_record: Mapping[str, Any],
) -> tuple[dict[str, Path], dict[str, dict[str, Any]]]:
    """Phase 1: finish all optimizer work without loading held-out/result modules."""
    root = Path(output_root)
    checkpoint_root = root / "checkpoints"
    if checkpoint_root.exists():
        if checkpoint_root.is_symlink() or not checkpoint_root.is_dir():
            raise RuntimeError("fixed checkpoint root must be a regular directory")
        allowed = {checkpoint_path(root, seed) for seed in SEED_SLOTS}
        if set(checkpoint_root.iterdir()) - allowed:
            raise RuntimeError("fixed checkpoint root contains an unexpected entry")
    paths: dict[str, Path] = {}
    records: dict[str, dict[str, Any]] = {}
    for seed_slot in SEED_SLOTS:
        destination = checkpoint_path(root, seed_slot)
        rows = _load_seed_training_rows(support_path, seed_slot, support_record)
        if destination.is_symlink():
            raise RuntimeError(f"fixed checkpoint must not be a symlink: {destination}")
        resume_from = None
        if destination.exists():
            raw = _load_checkpoint(destination)
            _validate_checkpoint_binding(raw, seed_slot, support_record, require_complete=False)
            expected_batches = PRODUCTION_WORKLOAD["optimizer_updates"] // len(SEED_SLOTS)
            if raw["completed_batches"] < expected_batches:
                resume_from = destination
            else:
                paths[seed_slot] = destination
                records[seed_slot] = _checkpoint_record(raw)
                continue
        outcome = _train_seed(
            seed_slot,
            support_path,
            destination,
            support_record,
            rows,
            resume_from=resume_from,
        )
        if not isinstance(outcome, Mapping) or outcome.get("complete_pass") is not True:
            raise RuntimeError(
                f"training did not publish a complete deterministic checkpoint: {destination}"
            )
        raw = _load_checkpoint(destination)
        _validate_checkpoint_binding(raw, seed_slot, support_record, require_complete=True)
        paths[seed_slot] = destination
        records[seed_slot] = _checkpoint_record(raw)
    if set(paths) != set(SEED_SLOTS) or set(records) != set(SEED_SLOTS):
        raise RuntimeError("all ten complete checkpoints are required before phase 2")
    return paths, records


def run_belief(
    manifest: str | Path | Mapping[str, Any],
    preflight: str | Path,
    output_root: str | Path,
) -> Path:
    """Resume at cadence-1 per-batch checkpoints and publish only the complete BELIEF result."""
    manifest_value = validate_contract(manifest)
    if manifest_value["mode"] != PRODUCTION_MODE:
        raise ValueError("result-bearing execution requires the PRODUCTION manifest")
    _runtime_resource_record(output_root)
    accepted = validate_production_preflight(preflight, manifest_value)
    root = Path(output_root)
    result_path = root / RESULT_FILENAME
    if result_path.exists():
        raise FileExistsError(f"complete result already exists: {result_path}")
    root.mkdir(parents=True, exist_ok=True)
    support_path = Path(preflight).parent / SUPPORT_ARTIFACT_RELATIVE
    support_record = accepted["support_record"]
    checkpoint_paths, checkpoint_records = _complete_production_checkpoints(
        root, support_path, support_record
    )
    evaluations = []
    # Phase 2 begins only after Phase 1 returned all ten terminal checkpoints.
    for seed_slot in SEED_SLOTS:
        destination = checkpoint_paths[seed_slot]
        record = checkpoint_records[seed_slot]
        evaluation = _evaluate_checkpoint(destination)
        if (
            evaluation.seed_slot != seed_slot
            or evaluation.result_eligible is not True
            or evaluation.checkpoint_record != record
        ):
            raise RuntimeError("held-out evaluation/checkpoint binding mismatch")
        evaluations.append(evaluation)
    result = _build_complete_result(
        preflight_record=support_record,
        checkpoint_records=checkpoint_records,
        seed_evaluations=tuple(evaluations),
    )
    if not isinstance(result, Mapping) or result.get("result", {}).get("complete") is not True:
        raise RuntimeError("complete BELIEF result required before publication")
    _publish_complete_result(result, result_path)
    return result_path


__all__ = [
    "PRODUCTION_PREFLIGHT_FORMAT",
    "PRODUCTION_WORKLOAD",
    "ProductionPreflightError",
    "checkpoint_path",
    "create_production_manifest",
    "preflight_production",
    "run_belief",
    "validate_production_preflight",
]
