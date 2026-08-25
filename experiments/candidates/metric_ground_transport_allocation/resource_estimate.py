"""Non-scientific preactivity resource estimator for the MGTAP successor.

This module deliberately has no imports from the local MGTAP implementation.  It
uses only deterministic, schema-shaped fixtures and never takes an optimizer
step.  Numerical-library limits are installed before NumPy or Torch is loaded.
"""

from __future__ import annotations

import os


INTRA_OP_THREADS = 4
INTER_OP_THREADS = 1
CPU_PROCESSES = 1
ACCELERATORS = 0

_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
)
for _environment_name in _THREAD_ENVIRONMENT:
    os.environ[_environment_name] = str(INTRA_OP_THREADS)
for _environment_name in ("CUDA_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES", "ROCR_VISIBLE_DEVICES"):
    os.environ[_environment_name] = ""

import argparse
import builtins
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import gc
import importlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import resource
import shutil
import statistics
import sys
import tempfile
import time
from types import ModuleType
import zlib

import numpy as np
import torch


GATE_TRAINING_UPDATES = 24_576
VALIDATION_PANELS = 192
CONDITIONAL_TRAINING_UPDATES = 32_768
BASE_PLUS_REPLAY_FIT_EVALUATIONS = 64
FOUR_FIT_CONCATENATIONS = 16
PACKET_WRITES = 16
PACKET_READ_ACCESS_UNITS = 16
NEUTRAL_TABLE_IO_UNITS = 1
NEUTRAL_METADATA_JSON_IO_UNITS = 1

TRAINING_EPISODES = 48
TRAINING_EPOCHS = 2
VALIDATION_PANEL_ROWS = 2 * 12 * 2 * 16 * 2
EVALUATION_ROWS_PER_FIT = 4 * 12 * 2 * 64 * 2
BASE_PLUS_REPLAY_ROWS = 2 * EVALUATION_ROWS_PER_FIT
FOUR_FIT_MEMBERS = 4
COMBINED_PACKET_ROWS = FOUR_FIT_MEMBERS * EVALUATION_ROWS_PER_FIT
RAW_PACKET_PAYLOAD_BYTES = 110_000_000
SOURCE_TABLE_PAYLOAD_BYTES = 312_064
LOGICAL_PACKET_COUNT = 16
MEASUREMENT_REPETITIONS = 3

MEMORY_SOURCE_ENVELOPE_BYTES = 4 * 1024**3
DISK_SOURCE_ENVELOPE_BYTES = 8 * 1024**3
WALL_REVIEW_THRESHOLD_SECONDS = 7_200.0

TIMING_UNCERTAINTY_FACTOR = 1.25
PEAK_RSS_SAFETY_FACTOR = 1.20
TEMPORARY_STORAGE_SAFETY_FACTOR = 1.25
RETAINED_STORAGE_SAFETY_FACTOR = 1.10
CAPACITY_RESERVE_FACTOR = 0.80

WORKLOAD_COUNTS = {
    "gate_training_updates": GATE_TRAINING_UPDATES,
    "validation_panels": VALIDATION_PANELS,
    "conditional_training_updates": CONDITIONAL_TRAINING_UPDATES,
    "base_plus_replay_fit_evaluations": BASE_PLUS_REPLAY_FIT_EVALUATIONS,
    "four_fit_concatenations": FOUR_FIT_CONCATENATIONS,
    "packet_writes": PACKET_WRITES,
    "packet_read_access_units": PACKET_READ_ACCESS_UNITS,
    "neutral_table_io_units": NEUTRAL_TABLE_IO_UNITS,
    "neutral_metadata_json_io_units": NEUTRAL_METADATA_JSON_IO_UNITS,
}

GATE_FORMULA = (
    "24_576 * training_update_unit + 192 * validation_panel_unit"
)
ALL_PASS_FORMULA = (
    "gate_only + 32_768 * training_update_unit + "
    "64 * base_plus_replay_fit_unit + 16 * four_fit_concatenation_unit + "
    "16 * packet_compression_write_unit + 16 * packet_read_access_unit + "
    "1 * neutral_table_io_unit + 1 * neutral_metadata_json_io_unit"
)

_GATED_COMPONENTS = (
    ("gate_training_updates", "training_update_unit"),
    ("validation_panels", "validation_panel_unit"),
)
_ALL_PASS_COMPONENTS = _GATED_COMPONENTS + (
    ("conditional_training_updates", "training_update_unit"),
    ("base_plus_replay_fit_evaluations", "base_plus_replay_fit_unit"),
    ("four_fit_concatenations", "four_fit_concatenation_unit"),
    ("packet_writes", "packet_compression_write_unit"),
    ("packet_read_access_units", "packet_read_access_unit"),
    ("neutral_table_io_units", "neutral_table_io_unit"),
    ("neutral_metadata_json_io_units", "neutral_metadata_json_io_unit"),
)
_PROJECTED_TIMING_UNITS = tuple(dict.fromkeys(unit for _, unit in _ALL_PASS_COMPONENTS))
_ALL_TIMING_UNITS = _PROJECTED_TIMING_UNITS + ("compression_probe_unit",)

FORBIDDEN_MGTAP_MODULES = frozenset(
    {
        "experiments.candidates.metric_ground_transport_allocation.actor",
        "experiments.candidates.metric_ground_transport_allocation.analysis",
        "experiments.candidates.metric_ground_transport_allocation.artifacts",
        "experiments.candidates.metric_ground_transport_allocation.certificate",
        "experiments.candidates.metric_ground_transport_allocation.config",
        "experiments.candidates.metric_ground_transport_allocation.decoder",
        "experiments.candidates.metric_ground_transport_allocation.environment",
        "experiments.candidates.metric_ground_transport_allocation.evaluation",
        "experiments.candidates.metric_ground_transport_allocation.oracle",
        "experiments.candidates.metric_ground_transport_allocation.rng",
        "experiments.candidates.metric_ground_transport_allocation.run",
        "experiments.candidates.metric_ground_transport_allocation.trainer",
    }
)

_FORBIDDEN_CALL_TARGETS = {
    "experiments.candidates.metric_ground_transport_allocation.run": ("production",),
    "experiments.candidates.metric_ground_transport_allocation.trainer": (
        "_mark_registered_activity",
        "_training_group",
        "validation_value",
        "fit",
        "calibration_fit",
        "conclusion_fit",
    ),
    "experiments.candidates.metric_ground_transport_allocation.rng": (
        "generator",
        "tapes_for_decisions",
        "replay_permutations",
    ),
    "experiments.candidates.metric_ground_transport_allocation.analysis": (
        "seed_estimands",
        "analyze",
    ),
    "experiments.candidates.metric_ground_transport_allocation.artifacts": (
        "create_temp_root",
        "install",
        "json_write",
        "write_npz",
    ),
    "experiments.candidates.metric_ground_transport_allocation.evaluation": (
        "evaluate_fit",
        "combine_fits",
    ),
}

_FORBIDDEN_KEY_TOKENS = frozenset(
    {
        "reward",
        "rewards",
        "loss",
        "losses",
        "gradient",
        "gradients",
        "policy",
        "policies",
        "coupling",
        "couplings",
        "calibration",
        "calibrations",
        "efficacy",
        "efficacies",
        "result",
        "results",
        "seed",
        "seeds",
        "address",
        "addresses",
        "partial",
    }
)
_ALLOWED_VALIDATION_KEYS = frozenset(
    {"validation_panel", "validation_panels", "validation_panel_rows", "validation_panel_unit"}
)
_FORBIDDEN_STRING_TOKENS = _FORBIDDEN_KEY_TOKENS - {"partial"}


class ResourceEstimateError(RuntimeError):
    """Base class for a fail-closed estimator refusal."""


class UnsupportedPlatformError(ResourceEstimateError):
    """Raised when Linux process accounting is unavailable."""


class CollectionBoundaryError(ResourceEstimateError):
    """Raised when collection crosses a forbidden scientific boundary."""


class ArtifactFirewallError(ResourceEstimateError):
    """Raised when an artifact contains forbidden or non-finite data."""


class OutputPathError(ResourceEstimateError):
    """Raised when the output is not canonical, fresh, and safe."""


@dataclass(frozen=True)
class _FixtureSpec:
    training_episodes: int
    training_epochs: int
    validation_panel_rows: int
    base_plus_replay_rows: int
    four_fit_members: int
    raw_packet_payload_bytes: int
    source_table_payload_bytes: int
    repetitions: int


_DEFAULT_FIXTURE = _FixtureSpec(
    training_episodes=TRAINING_EPISODES,
    training_epochs=TRAINING_EPOCHS,
    validation_panel_rows=VALIDATION_PANEL_ROWS,
    base_plus_replay_rows=BASE_PLUS_REPLAY_ROWS,
    four_fit_members=FOUR_FIT_MEMBERS,
    raw_packet_payload_bytes=RAW_PACKET_PAYLOAD_BYTES,
    source_table_payload_bytes=SOURCE_TABLE_PAYLOAD_BYTES,
    repetitions=MEASUREMENT_REPETITIONS,
)


@dataclass(frozen=True)
class _OutputTarget:
    path: Path
    parent: Path
    final_name: str
    temporary_name: str
    directory_fd: int


def _require_linux() -> None:
    if sys.platform != "linux":
        raise UnsupportedPlatformError("Linux ru_maxrss accounting is required")


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ResourceEstimateError(f"{name} must be a positive integer")
    return value


def _validate_fixture_spec(spec: _FixtureSpec) -> None:
    for name in (
        "training_episodes",
        "training_epochs",
        "validation_panel_rows",
        "base_plus_replay_rows",
        "four_fit_members",
        "raw_packet_payload_bytes",
        "source_table_payload_bytes",
        "repetitions",
    ):
        _positive_int(getattr(spec, name), name)
    if spec.base_plus_replay_rows % 2:
        raise ResourceEstimateError("base_plus_replay_rows must be even")


def _read_proc_kib(path: Path, field: str) -> int | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    prefix = f"{field}:"
    for line in lines:
        if not line.startswith(prefix):
            continue
        parts = line[len(prefix) :].strip().split()
        if len(parts) != 2 or parts[1] != "kB":
            return None
        try:
            return int(parts[0]) * 1024
        except ValueError:
            return None
    return None


def _peak_rss_bytes() -> int:
    _require_linux()
    peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if isinstance(peak_kib, bool) or not isinstance(peak_kib, (int, float)):
        raise UnsupportedPlatformError("Linux ru_maxrss did not return a number")
    peak_bytes = int(peak_kib * 1024)
    if peak_bytes <= 0:
        raise UnsupportedPlatformError("Linux ru_maxrss did not return a positive peak")
    return peak_bytes


def _rss_snapshot() -> dict[str, int | None]:
    return {
        "peak_rss_bytes": _peak_rss_bytes(),
        "current_rss_bytes": _read_proc_kib(Path("/proc/self/status"), "VmRSS"),
        "proc_high_water_bytes": _read_proc_kib(Path("/proc/self/status"), "VmHWM"),
    }


def _cpu_model() -> str:
    try:
        lines = Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines()
    except OSError:
        return platform.processor() or "unknown"
    for line in lines:
        if line.lower().startswith("model name") and ":" in line:
            return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def _configure_runtime() -> dict[str, object]:
    _require_linux()
    torch.set_num_threads(INTRA_OP_THREADS)
    if torch.get_num_interop_threads() != INTER_OP_THREADS:
        try:
            torch.set_num_interop_threads(INTER_OP_THREADS)
        except RuntimeError as exc:
            raise ResourceEstimateError("Torch inter-op threads could not be fixed before collection") from exc
    if torch.get_num_threads() != INTRA_OP_THREADS:
        raise ResourceEstimateError("Torch intra-op thread configuration did not take effect")
    if torch.get_num_interop_threads() != INTER_OP_THREADS:
        raise ResourceEstimateError("Torch inter-op thread configuration did not take effect")

    accelerator_visible = bool(torch.cuda.is_available() or torch.cuda.device_count())
    xpu = getattr(torch, "xpu", None)
    if xpu is not None and callable(getattr(xpu, "is_available", None)):
        accelerator_visible = accelerator_visible or bool(xpu.is_available())
    mps = getattr(getattr(torch, "backends", None), "mps", None)
    if mps is not None and callable(getattr(mps, "is_available", None)):
        accelerator_visible = accelerator_visible or bool(mps.is_available())
    if accelerator_visible:
        raise ResourceEstimateError("An accelerator remained visible after the zero-accelerator configuration")

    torch.use_deterministic_algorithms(True)
    torch.set_default_dtype(torch.float64)
    uname = platform.uname()
    kernel_text = " ".join((uname.system, uname.release, uname.version))
    return {
        "operating_system": uname.system,
        "kernel_release": uname.release,
        "kernel_version": uname.version,
        "wsl_detected": "microsoft" in kernel_text.casefold() or "wsl" in kernel_text.casefold(),
        "machine": uname.machine,
        "cpu_model": _cpu_model(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "numpy_version": np.__version__,
        "torch_version": torch.__version__,
        "device": "cpu",
        "processes": CPU_PROCESSES,
        "intra_op_threads": torch.get_num_threads(),
        "inter_op_threads": torch.get_num_interop_threads(),
        "accelerators": ACCELERATORS,
    }


def _measure_operation(
    operation: Callable[[], object], repetitions: int
) -> tuple[dict[str, object], list[object]]:
    wall_observations: list[float] = []
    cpu_observations: list[float] = []
    outcomes: list[object] = []
    stage_peak = _peak_rss_bytes()
    for _ in range(repetitions):
        gc.collect()
        wall_start = time.perf_counter()
        cpu_start = time.process_time()
        outcome = operation()
        cpu_elapsed = time.process_time() - cpu_start
        wall_elapsed = time.perf_counter() - wall_start
        if not math.isfinite(wall_elapsed) or not math.isfinite(cpu_elapsed):
            raise ResourceEstimateError("A timing observation was non-finite")
        if wall_elapsed < 0.0 or cpu_elapsed < 0.0:
            raise ResourceEstimateError("A timing observation was negative")
        wall_observations.append(wall_elapsed)
        cpu_observations.append(cpu_elapsed)
        outcomes.append(outcome)
        stage_peak = max(stage_peak, _peak_rss_bytes())
    return (
        {
            "wall_seconds": wall_observations,
            "cpu_seconds": cpu_observations,
            "peak_rss_bytes": stage_peak,
        },
        outcomes,
    )


def _training_update_operation(spec: _FixtureSpec) -> None:
    features = torch.arange(
        spec.training_episodes * 6, dtype=torch.float64
    ).reshape(spec.training_episodes, 6)
    features = (features - 17.0) / 113.0
    actor_weights = (
        torch.arange(48, dtype=torch.float64).reshape(6, 8) / 47.0 - 0.5
    ).requires_grad_()
    idle_weights = (
        torch.arange(12, dtype=torch.float64).reshape(6, 2) / 11.0 - 0.5
    ).requires_grad_()
    edge_map = torch.eye(8, dtype=torch.float64)
    edge_map += torch.triu(torch.full((8, 8), 1.0 / 32.0, dtype=torch.float64), diagonal=1)
    for epoch in range(spec.training_epochs):
        raw_scores = features @ actor_weights
        mapped_scores = raw_scores @ edge_map
        idle_scores = features @ idle_weights
        activation = torch.tanh(
            torch.cat((mapped_scores, idle_scores), dim=1) + float(epoch) / 64.0
        )
        scalar = activation.square().mean() + activation[:, 0].mean() / 128.0
        scalar.backward()
        torch.nn.utils.clip_grad_norm_((actor_weights, idle_weights), max_norm=1.0)
        actor_weights.grad = None
        idle_weights.grad = None


def _validation_panel_operation(spec: _FixtureSpec) -> None:
    with torch.no_grad():
        features = torch.arange(
            spec.validation_panel_rows * 6, dtype=torch.float64
        ).reshape(spec.validation_panel_rows, 6)
        features = (features % 97.0 - 48.0) / 97.0
        actor_weights = torch.arange(48, dtype=torch.float64).reshape(6, 8) / 47.0 - 0.5
        idle_weights = torch.arange(12, dtype=torch.float64).reshape(6, 2) / 11.0 - 0.5
        edge_map = torch.eye(8, dtype=torch.float64)
        edge_map += torch.triu(
            torch.full((8, 8), 1.0 / 32.0, dtype=torch.float64), diagonal=1
        )
        mapped_scores = (features @ actor_weights) @ edge_map
        idle_scores = features @ idle_weights
        transformed = torch.tanh(torch.cat((mapped_scores, idle_scores), dim=1))
        float(transformed.square().sum())


def _base_plus_replay_fit_operation(spec: _FixtureSpec) -> None:
    rows_per_pass = spec.base_plus_replay_rows // 2
    base = np.arange(rows_per_pass * 6, dtype=np.float64).reshape(rows_per_pass, 6)
    base = (base % 251.0 - 125.0) / 251.0
    replay = base[::-1, ::-1]
    actor_weights = np.arange(48, dtype=np.float64).reshape(6, 8) / 47.0 - 0.5
    idle_weights = np.arange(12, dtype=np.float64).reshape(6, 2) / 11.0 - 0.5
    edge_map = np.eye(8, dtype=np.float64) + np.triu(
        np.full((8, 8), 1.0 / 32.0, dtype=np.float64), k=1
    )
    accessed = 0.0
    for features in (base, replay):
        mapped_scores = (features @ actor_weights) @ edge_map
        idle_scores = features @ idle_weights
        transformed = np.tanh(np.concatenate((mapped_scores, idle_scores), axis=1))
        accessed += float(np.sum(transformed))
    if not math.isfinite(accessed):
        raise ResourceEstimateError("The base-plus-replay fixture was non-finite")


def _neutral_fit_chunks(spec: _FixtureSpec) -> list[np.ndarray]:
    base_size, remainder = divmod(spec.raw_packet_payload_bytes, spec.four_fit_members)
    fits = []
    for index in range(spec.four_fit_members):
        size = base_size + (1 if index < remainder else 0)
        fixture = np.arange(size, dtype=np.uint8)
        fixture ^= np.uint8((index + 1) * 29)
        fits.append(fixture)
    return fits


def _four_fit_concatenation_operation(
    fits: list[np.ndarray], expected_payload_bytes: int
) -> None:
    concatenated = np.concatenate(fits)
    if concatenated.nbytes != expected_payload_bytes:
        raise ResourceEstimateError("The four-fit concatenation byte shape was not preserved")


def _neutral_payload_block() -> bytes:
    records = [
        (
            f'{{"fixture":"neutral_resource_row","row_index":"{index:08d}",'
            f'"column_a":"abcdefgh","column_b":"ABCDEFGH"}}\n'
        ).encode("ascii")
        for index in range(256)
    ]
    return b"".join(records)


def _payload_chunks(total_bytes: int, chunk_bytes: int = 1024 * 1024) -> Iterator[bytes]:
    block = _neutral_payload_block()
    remaining = total_bytes
    while remaining:
        size = min(chunk_bytes, remaining)
        repeats = (size + len(block) - 1) // len(block)
        yield (block * repeats)[:size]
        remaining -= size


def _neutral_packet_arrays(total_bytes: int) -> dict[str, np.ndarray]:
    wide_bytes = (total_bytes // 2) // 8 * 8
    remaining = total_bytes - wide_bytes
    narrow_bytes = (remaining // 4) * 4
    trailing_bytes = remaining - narrow_bytes

    wide = np.arange(wide_bytes // 8, dtype=np.uint64)
    wide *= np.uint64(6_364_136_223_846_793_005)
    wide += np.uint64(1_442_695_040_888_963_407)
    narrow = np.arange(narrow_bytes // 4, dtype=np.uint32)
    narrow *= np.uint32(1_664_525)
    narrow += np.uint32(1_013_904_223)
    trailing = np.arange(trailing_bytes, dtype=np.uint8)
    arrays = {
        "neutral_numeric_words_64": wide,
        "neutral_numeric_words_32": narrow,
        "neutral_trailing_bytes": trailing,
    }
    if sum(array.nbytes for array in arrays.values()) != total_bytes:
        raise ResourceEstimateError("The neutral packet arrays did not preserve raw payload bytes")
    return arrays


def _packet_compression_write_operation(
    root: Path, arrays: Mapping[str, np.ndarray], expected_raw_bytes: int
) -> dict[str, int]:
    packet_path = root / "neutral_packet.npz"
    np.savez_compressed(packet_path, **arrays)
    raw_bytes = sum(array.nbytes for array in arrays.values())
    compressed_bytes = packet_path.stat().st_size
    if raw_bytes != expected_raw_bytes or compressed_bytes <= 0:
        raise ResourceEstimateError("The neutral packet storage probe was incomplete")
    return {"raw_bytes": raw_bytes, "compressed_bytes": compressed_bytes}


def _compression_probe_operation(spec: _FixtureSpec) -> None:
    compressor = zlib.compressobj(level=6, wbits=zlib.MAX_WBITS)
    compressed_bytes = 0
    for chunk in _payload_chunks(spec.raw_packet_payload_bytes):
        compressed_bytes += len(compressor.compress(chunk))
    compressed_bytes += len(compressor.flush())
    if compressed_bytes <= 0:
        raise ResourceEstimateError("The neutral compression probe was incomplete")


def _packet_read_access_operation(root: Path, expected_raw_bytes: int) -> None:
    packet_path = root / "neutral_packet.npz"
    with np.load(packet_path, allow_pickle=False) as packet:
        arrays = [packet[name] for name in packet.files]
        accessed_bytes = sum(array.nbytes for array in arrays)
        edge_words = sum(
            int(array.reshape(-1)[0]) + int(array.reshape(-1)[-1])
            for array in arrays
            if array.size
        )
    if accessed_bytes != expected_raw_bytes or edge_words < 0:
        raise ResourceEstimateError("The neutral packet access probe was incomplete")




def _neutral_table_io_operation(root: Path, spec: _FixtureSpec) -> dict[str, int]:
    table_path = root / "neutral_source_table.npz"
    arrays = _neutral_packet_arrays(spec.source_table_payload_bytes)
    np.savez_compressed(table_path, **arrays)
    with np.load(table_path, allow_pickle=False) as table:
        accessed_bytes = sum(table[name].nbytes for name in table.files)
    compressed_bytes = table_path.stat().st_size
    if accessed_bytes != spec.source_table_payload_bytes or compressed_bytes <= 0:
        raise ResourceEstimateError("The neutral table I/O probe was incomplete")
    return {"raw_bytes": accessed_bytes, "compressed_bytes": compressed_bytes}


def _neutral_metadata_bytes() -> bytes:
    document = {
        "artifact_kind": "non_scientific_resource_packet_metadata",
        "fixture_kind": "neutral_schema_storage",
        "packet_count": LOGICAL_PACKET_COUNT,
        "schema_version": 1,
    }
    return (
        json.dumps(document, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        + b"\n"
    )


def _neutral_metadata_json_io_operation(root: Path) -> None:
    metadata_path = root / "neutral_metadata.json"
    payload = _neutral_metadata_bytes()
    with metadata_path.open("wb") as metadata_file:
        metadata_file.write(payload)
        metadata_file.flush()
        os.fsync(metadata_file.fileno())
    loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
    if loaded.get("fixture_kind") != "neutral_schema_storage":
        raise ResourceEstimateError("The neutral metadata I/O probe was incomplete")


def _collect_fixture_measurements(spec: _FixtureSpec, temporary_parent: Path) -> dict[str, object]:
    _validate_fixture_spec(spec)
    cold_rss = _rss_snapshot()
    timing_units: dict[str, object] = {}
    rss_stages: dict[str, int | None] = {
        "cold_imported_process": cold_rss["peak_rss_bytes"],
    }

    timing, _ = _measure_operation(lambda: _training_update_operation(spec), spec.repetitions)
    timing_units["training_update_unit"] = timing
    rss_stages["actor_autograd"] = _positive_int(
        timing["peak_rss_bytes"], "actor/autograd peak RSS"
    )

    timing, _ = _measure_operation(lambda: _validation_panel_operation(spec), spec.repetitions)
    timing_units["validation_panel_unit"] = timing
    rss_stages["validation_panel"] = _positive_int(
        timing["peak_rss_bytes"], "validation panel peak RSS"
    )

    timing, _ = _measure_operation(lambda: _base_plus_replay_fit_operation(spec), spec.repetitions)
    timing_units["base_plus_replay_fit_unit"] = timing
    rss_stages["base_plus_replay_fit"] = _positive_int(
        timing["peak_rss_bytes"], "base-plus-replay fit peak RSS"
    )

    fit_chunks = _neutral_fit_chunks(spec)
    timing, _ = _measure_operation(
        lambda: _four_fit_concatenation_operation(fit_chunks, spec.raw_packet_payload_bytes),
        spec.repetitions,
    )
    timing_units["four_fit_concatenation_unit"] = timing
    rss_stages["four_fit_concatenation"] = _positive_int(
        timing["peak_rss_bytes"], "four-fit concatenation peak RSS"
    )
    del fit_chunks
    gc.collect()

    temporary_path: Path | None = None
    storage: dict[str, int | None]
    with tempfile.TemporaryDirectory(
        prefix=".mgtap-nonscientific-preactivity-resource-", dir=temporary_parent
    ) as temporary_name:
        temporary_path = Path(temporary_name)

        packet_arrays = _neutral_packet_arrays(spec.raw_packet_payload_bytes)
        timing, packet_outcomes = _measure_operation(
            lambda: _packet_compression_write_operation(
                temporary_path, packet_arrays, spec.raw_packet_payload_bytes
            ),
            spec.repetitions,
        )
        timing_units["packet_compression_write_unit"] = timing
        rss_stages["packet_compression_write"] = _positive_int(
            timing["peak_rss_bytes"], "packet compression write peak RSS"
        )
        packet_sizes = [outcome for outcome in packet_outcomes if isinstance(outcome, dict)]
        if len(packet_sizes) != spec.repetitions:
            raise ResourceEstimateError("The neutral packet write observations were incomplete")
        compressed_sizes = {
            _positive_int(outcome.get("compressed_bytes"), "compressed packet bytes")
            for outcome in packet_sizes
        }
        if len(compressed_sizes) != 1:
            raise ResourceEstimateError("The deterministic packet size changed across repetitions")
        compressed_packet_bytes = compressed_sizes.pop()
        del packet_arrays
        gc.collect()

        timing, _ = _measure_operation(lambda: _compression_probe_operation(spec), spec.repetitions)
        timing_units["compression_probe_unit"] = timing
        rss_stages["compression"] = _positive_int(
            timing["peak_rss_bytes"], "compression probe peak RSS"
        )

        timing, _ = _measure_operation(
            lambda: _packet_read_access_operation(temporary_path, spec.raw_packet_payload_bytes),
            spec.repetitions,
        )
        timing_units["packet_read_access_unit"] = timing
        rss_stages["packet_read_access"] = _positive_int(
            timing["peak_rss_bytes"], "packet read access peak RSS"
        )

        timing, table_outcomes = _measure_operation(
            lambda: _neutral_table_io_operation(temporary_path, spec), spec.repetitions
        )
        timing_units["neutral_table_io_unit"] = timing
        rss_stages["neutral_table_io"] = _positive_int(
            timing["peak_rss_bytes"], "neutral table I/O peak RSS"
        )
        table_sizes = [outcome for outcome in table_outcomes if isinstance(outcome, dict)]
        if len(table_sizes) != spec.repetitions:
            raise ResourceEstimateError("The neutral table observations were incomplete")
        compressed_table_sizes = {
            _positive_int(outcome.get("compressed_bytes"), "compressed table bytes")
            for outcome in table_sizes
        }
        if len(compressed_table_sizes) != 1:
            raise ResourceEstimateError("The deterministic table size changed across repetitions")
        compressed_table_bytes = compressed_table_sizes.pop()

        timing, _ = _measure_operation(
            lambda: _neutral_metadata_json_io_operation(temporary_path), spec.repetitions
        )
        timing_units["neutral_metadata_json_io_unit"] = timing
        rss_stages["neutral_metadata_json_io"] = _positive_int(
            timing["peak_rss_bytes"], "neutral metadata JSON I/O peak RSS"
        )

        metadata_json_bytes = (temporary_path / "neutral_metadata.json").stat().st_size
        logical_sixteen_packet_bytes = compressed_packet_bytes * LOGICAL_PACKET_COUNT
        complete_tree_bytes = (
            logical_sixteen_packet_bytes
            + compressed_table_bytes
            + metadata_json_bytes
        )
        storage = {
            "raw_per_packet_payload_bytes": spec.raw_packet_payload_bytes,
            "compressed_per_packet_bytes": compressed_packet_bytes,
            "logical_sixteen_packet_bytes": logical_sixteen_packet_bytes,
            "raw_source_table_payload_bytes": spec.source_table_payload_bytes,
            "compressed_table_bytes": compressed_table_bytes,
            "metadata_json_bytes": metadata_json_bytes,
            "staging_temporary_bytes": complete_tree_bytes,
            "complete_tree_bytes": complete_tree_bytes,
        }

    if temporary_path is None or temporary_path.exists():
        raise ResourceEstimateError("The non-scientific temporary fixture was not fully removed")

    return {
        "cold_imported_process_rss": cold_rss,
        "measurement_repetitions": spec.repetitions,
        "timing_units": timing_units,
        "rss_stages_bytes": rss_stages,
        "storage_bytes": storage,
    }


def _is_forbidden_module(name: str) -> bool:
    return any(name == forbidden or name.startswith(f"{forbidden}.") for forbidden in FORBIDDEN_MGTAP_MODULES)


def _import_candidates(
    name: str,
    globals_dict: Mapping[str, object] | None,
    fromlist: Sequence[str] | None,
    level: int,
) -> set[str]:
    resolved = name
    if level:
        package = globals_dict.get("__package__") if globals_dict is not None else None
        if isinstance(package, str) and package:
            try:
                resolved = importlib.util.resolve_name("." * level + name, package)
            except (ImportError, ValueError):
                resolved = name
    candidates = {resolved}
    for item in fromlist or ():
        if isinstance(item, str) and item != "*":
            candidates.add(f"{resolved}.{item}")
    return candidates


@contextmanager
def _blocked_mgtap_imports() -> Iterator[None]:
    missing = object()
    before = {name: sys.modules.get(name, missing) for name in FORBIDDEN_MGTAP_MODULES}
    original_import = builtins.__import__
    original_import_module = importlib.import_module

    def guarded_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> ModuleType:
        candidates = _import_candidates(name, globals, fromlist, level)
        if any(_is_forbidden_module(candidate) for candidate in candidates):
            raise CollectionBoundaryError("A forbidden MGTAP module import was attempted")
        return original_import(name, globals, locals, fromlist, level)

    def guarded_import_module(name: str, package: str | None = None) -> ModuleType:
        resolved = importlib.util.resolve_name(name, package) if name.startswith(".") else name
        if _is_forbidden_module(resolved):
            raise CollectionBoundaryError("A forbidden MGTAP module import was attempted")
        return original_import_module(name, package)

    builtins.__import__ = guarded_import
    importlib.import_module = guarded_import_module
    try:
        yield
        changed = [
            name
            for name, previous in before.items()
            if sys.modules.get(name, missing) is not previous
        ]
        if changed:
            raise CollectionBoundaryError("A forbidden MGTAP module was loaded during collection")
    finally:
        builtins.__import__ = original_import
        importlib.import_module = original_import_module
        for name, previous in before.items():
            current = sys.modules.get(name, missing)
            if current is previous:
                continue
            if previous is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous  # type: ignore[assignment]


@contextmanager
def _blocked_scientific_calls() -> Iterator[None]:
    originals: list[tuple[ModuleType, str, object]] = []

    def reject(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise CollectionBoundaryError("A forbidden MGTAP callable was invoked during collection")

    for module_name, attribute_names in _FORBIDDEN_CALL_TARGETS.items():
        module = sys.modules.get(module_name)
        if module is None:
            continue
        for attribute_name in attribute_names:
            if not hasattr(module, attribute_name):
                continue
            original = getattr(module, attribute_name)
            originals.append((module, attribute_name, original))
            setattr(module, attribute_name, reject)
    try:
        yield
    finally:
        for module, attribute_name, original in reversed(originals):
            setattr(module, attribute_name, original)


def _optimizer_classes() -> list[type[object]]:
    root: type[object] = torch.optim.Optimizer
    classes: list[type[object]] = [root]
    cursor = 0
    while cursor < len(classes):
        for subclass in classes[cursor].__subclasses__():
            if subclass not in classes:
                classes.append(subclass)
        cursor += 1
    return classes


@contextmanager
def _blocked_optimizer_steps() -> Iterator[None]:
    originals: list[tuple[type[object], object]] = []

    def reject(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise CollectionBoundaryError("An optimizer step was attempted during collection")

    for optimizer_class in _optimizer_classes():
        if "step" not in vars(optimizer_class):
            continue
        original = vars(optimizer_class)["step"]
        originals.append((optimizer_class, original))
        setattr(optimizer_class, "step", reject)
    try:
        yield
    finally:
        for optimizer_class, original in reversed(originals):
            setattr(optimizer_class, "step", original)


def _run_guarded_collection(collector: Callable[[], dict[str, object]]) -> dict[str, object]:
    with _blocked_mgtap_imports(), _blocked_scientific_calls(), _blocked_optimizer_steps():
        collected = collector()
    if not isinstance(collected, dict):
        raise ResourceEstimateError("The measurement collector did not return an object")
    return collected


def _collect_default_measurements(temporary_parent: Path) -> dict[str, object]:
    identity = _configure_runtime()
    measurements = _collect_fixture_measurements(_DEFAULT_FIXTURE, temporary_parent)
    measurements["identity"] = identity
    return measurements


def _finite_nonnegative(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ResourceEstimateError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ResourceEstimateError(f"{name} must be finite and nonnegative")
    return number


def _optional_nonnegative_int(value: object, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ResourceEstimateError(f"{name} must be a nonnegative integer or null")
    return value


def _timing_summary(unit: object) -> dict[str, object]:
    if unit is None:
        unknown_series = {"observations": [], "median": None, "observed_max": None}
        return {
            "status": "unknown",
            "repetitions": 0,
            "wall_seconds": dict(unknown_series),
            "cpu_seconds": dict(unknown_series),
            "peak_rss_bytes": None,
            "reason": "The measured unit was not supplied.",
        }
    if not isinstance(unit, Mapping):
        raise ResourceEstimateError("A timing unit must be an object or null")
    wall_raw = unit.get("wall_seconds")
    cpu_raw = unit.get("cpu_seconds")
    if not isinstance(wall_raw, list) or not isinstance(cpu_raw, list):
        raise ResourceEstimateError("Timing observations must be lists")
    if not wall_raw or len(wall_raw) != len(cpu_raw):
        raise ResourceEstimateError("Wall and CPU timing observations must be paired and nonempty")
    wall = [_finite_nonnegative(value, "wall timing") for value in wall_raw]
    cpu = [_finite_nonnegative(value, "CPU timing") for value in cpu_raw]
    peak = _optional_nonnegative_int(unit.get("peak_rss_bytes"), "timing peak RSS")
    return {
        "status": "grounded",
        "repetitions": len(wall),
        "wall_seconds": {
            "observations": wall,
            "median": statistics.median(wall),
            "observed_max": max(wall),
        },
        "cpu_seconds": {
            "observations": cpu,
            "median": statistics.median(cpu),
            "observed_max": max(cpu),
        },
        "peak_rss_bytes": peak,
        "reason": None,
    }


def _metric(
    unit: str,
    central: int | float | None,
    conservative_upper: int | float | None,
    reason: str | None = None,
) -> dict[str, object]:
    grounded = central is not None and conservative_upper is not None
    return {
        "unit": unit,
        "status": "grounded" if grounded else "unknown",
        "central": central if grounded else None,
        "conservative_upper": conservative_upper if grounded else None,
        "reason": None if grounded else (reason or "The quantity is not grounded."),
    }


def _projection_components(
    component_spec: tuple[tuple[str, str], ...], timing: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    components: dict[str, object] = {}
    for count_name, unit_name in component_spec:
        count = WORKLOAD_COUNTS[count_name]
        summary = timing[unit_name]
        wall = summary["wall_seconds"]
        cpu = summary["cpu_seconds"]
        if summary["status"] == "grounded":
            assert isinstance(wall, Mapping) and isinstance(cpu, Mapping)
            central_wall = float(wall["median"]) * count
            upper_wall = float(wall["observed_max"]) * TIMING_UNCERTAINTY_FACTOR * count
            central_cpu = float(cpu["median"]) * count
            upper_cpu = float(cpu["observed_max"]) * TIMING_UNCERTAINTY_FACTOR * count
        else:
            central_wall = upper_wall = central_cpu = upper_cpu = None
        components[count_name] = {
            "measured_unit": unit_name,
            "count": count,
            "central_wall_seconds": central_wall,
            "conservative_upper_wall_seconds": upper_wall,
            "central_cpu_seconds": central_cpu,
            "conservative_upper_cpu_seconds": upper_cpu,
        }
    return components


def _sum_projected_metric(components: Mapping[str, object], central_key: str, upper_key: str) -> dict[str, object]:
    central_values: list[float] = []
    upper_values: list[float] = []
    for component in components.values():
        if not isinstance(component, Mapping):
            raise ResourceEstimateError("A projection component must be an object")
        central = component.get(central_key)
        upper = component.get(upper_key)
        if central is None or upper is None:
            return _metric("seconds", None, None, "At least one projected timing unit is unmeasured.")
        central_values.append(_finite_nonnegative(central, central_key))
        upper_values.append(_finite_nonnegative(upper, upper_key))
    return _metric("seconds", math.fsum(central_values), math.fsum(upper_values))


def _peak_rss_metric(
    rss_stages: Mapping[str, object], stage_names: tuple[str, ...]
) -> dict[str, object]:
    observed: list[int] = []
    for stage_name in stage_names:
        value = _optional_nonnegative_int(rss_stages.get(stage_name), f"{stage_name} RSS")
        if value is None:
            return _metric("bytes", None, None, "At least one required process peak is unmeasured.")
        observed.append(value)
    central = max(observed)
    return _metric("bytes", central, math.ceil(central * PEAK_RSS_SAFETY_FACTOR))


def _storage_metric(
    value: object, factor: float, reason: str
) -> dict[str, object]:
    size = _optional_nonnegative_int(value, "storage bytes")
    if size is None:
        return _metric("bytes", None, None, reason)
    return _metric("bytes", size, math.ceil(size * factor))


def _capacity(raw: int | None) -> dict[str, object]:
    if raw is None:
        return {
            "unit": "bytes",
            "status": "unknown",
            "raw_available": None,
            "reserve_factor": CAPACITY_RESERVE_FACTOR,
            "safe_available": None,
            "reason": "Available capacity could not be measured.",
        }
    return {
        "unit": "bytes",
        "status": "grounded",
        "raw_available": raw,
        "reserve_factor": CAPACITY_RESERVE_FACTOR,
        "safe_available": math.floor(raw * CAPACITY_RESERVE_FACTOR),
        "reason": None,
    }


def _comparison(
    estimate_upper: int | float | None,
    safe_available: int | None,
    source_envelope: int,
    formula: str,
) -> dict[str, object]:
    return {
        "unit": "bytes",
        "estimate_upper": estimate_upper,
        "estimate_formula": formula,
        "safe_available": safe_available,
        "source_envelope": source_envelope,
        "within_safe_available": (
            None if estimate_upper is None or safe_available is None else estimate_upper <= safe_available
        ),
        "within_source_envelope": (
            None if estimate_upper is None else estimate_upper <= source_envelope
        ),
    }


def _classify_wall(metric: Mapping[str, object]) -> str:
    upper = metric.get("conservative_upper") if metric.get("status") == "grounded" else None
    if upper is None:
        return "ungrounded"
    seconds = _finite_nonnegative(upper, "all-pass wall upper")
    if seconds <= WALL_REVIEW_THRESHOLD_SECONDS:
        return "at_or_below_7200_seconds"
    return "above_7200_seconds"


def _classify_memory(comparison: Mapping[str, object]) -> str:
    safe = comparison.get("within_safe_available")
    envelope = comparison.get("within_source_envelope")
    if safe is False or envelope is False:
        return "reduction_batching_or_sharding_required"
    if safe is True and envelope is True:
        return "within_safe_capacity_and_source_envelope"
    return "ungrounded"


def _classify_disk(comparison: Mapping[str, object]) -> str:
    safe = comparison.get("within_safe_available")
    envelope = comparison.get("within_source_envelope")
    if safe is False or envelope is False:
        return "capacity_or_source_envelope_exceeded"
    if safe is True and envelope is True:
        return "within_safe_capacity_and_source_envelope"
    return "ungrounded"


def _storage_fact(value: object, formula: str) -> dict[str, object]:
    size = _optional_nonnegative_int(value, "storage fact")
    return {
        "unit": "bytes",
        "status": "grounded" if size is not None else "unknown",
        "observed_or_derived": size,
        "formula": formula,
    }


def _build_report(
    measurements: Mapping[str, object], capacities: Mapping[str, object]
) -> dict[str, object]:
    identity = measurements.get("identity")
    if not isinstance(identity, Mapping):
        raise ResourceEstimateError("Runtime identity facts are required")
    raw_timing = measurements.get("timing_units")
    if not isinstance(raw_timing, Mapping):
        raise ResourceEstimateError("Timing units are required")
    timing = {name: _timing_summary(raw_timing.get(name)) for name in _ALL_TIMING_UNITS}

    rss_stages_raw = measurements.get("rss_stages_bytes")
    if not isinstance(rss_stages_raw, Mapping):
        raise ResourceEstimateError("RSS stage facts are required")
    rss_stages = {
        str(name): _optional_nonnegative_int(value, f"{name} RSS")
        for name, value in rss_stages_raw.items()
    }

    storage_raw = measurements.get("storage_bytes")
    if not isinstance(storage_raw, Mapping):
        raise ResourceEstimateError("Storage facts are required")
    storage_names = (
        "raw_per_packet_payload_bytes",
        "compressed_per_packet_bytes",
        "logical_sixteen_packet_bytes",
        "raw_source_table_payload_bytes",
        "compressed_table_bytes",
        "metadata_json_bytes",
        "staging_temporary_bytes",
        "complete_tree_bytes",
    )
    storage = {
        name: _optional_nonnegative_int(storage_raw.get(name), name) for name in storage_names
    }

    cold_raw = measurements.get("cold_imported_process_rss")
    if not isinstance(cold_raw, Mapping):
        raise ResourceEstimateError("Cold imported-process RSS facts are required")
    cold = {
        "peak_rss_bytes": _optional_nonnegative_int(cold_raw.get("peak_rss_bytes"), "cold peak RSS"),
        "current_rss_bytes": _optional_nonnegative_int(
            cold_raw.get("current_rss_bytes"), "cold current RSS"
        ),
        "proc_high_water_bytes": _optional_nonnegative_int(
            cold_raw.get("proc_high_water_bytes"), "cold proc high-water RSS"
        ),
    }

    gate_components = _projection_components(_GATED_COMPONENTS, timing)
    all_pass_components = _projection_components(_ALL_PASS_COMPONENTS, timing)
    gate_wall = _sum_projected_metric(
        gate_components, "central_wall_seconds", "conservative_upper_wall_seconds"
    )
    gate_cpu = _sum_projected_metric(
        gate_components, "central_cpu_seconds", "conservative_upper_cpu_seconds"
    )
    all_pass_wall = _sum_projected_metric(
        all_pass_components, "central_wall_seconds", "conservative_upper_wall_seconds"
    )
    all_pass_cpu = _sum_projected_metric(
        all_pass_components, "central_cpu_seconds", "conservative_upper_cpu_seconds"
    )

    gate_peak = _peak_rss_metric(
        rss_stages, ("cold_imported_process", "actor_autograd", "validation_panel")
    )
    all_pass_peak = _peak_rss_metric(
        rss_stages,
        (
            "cold_imported_process",
            "actor_autograd",
            "validation_panel",
            "base_plus_replay_fit",
            "four_fit_concatenation",
            "packet_compression_write",
            "packet_read_access",
            "compression",
            "neutral_table_io",
            "neutral_metadata_json_io",
        ),
    )

    gate_storage_reason = "No terminal gate-failure storage schema was provided."
    gate_temporary = _metric("bytes", None, None, gate_storage_reason)
    gate_retained = _metric("bytes", None, None, gate_storage_reason)
    all_pass_temporary = _storage_metric(
        storage["staging_temporary_bytes"],
        TEMPORARY_STORAGE_SAFETY_FACTOR,
        "The staging storage probe is unmeasured.",
    )
    all_pass_retained = _storage_metric(
        storage["complete_tree_bytes"],
        RETAINED_STORAGE_SAFETY_FACTOR,
        "The complete-tree storage projection is unmeasured.",
    )

    count_metrics = {
        "process_count": _metric("processes", CPU_PROCESSES, CPU_PROCESSES),
        "thread_count": _metric("threads", INTRA_OP_THREADS, INTRA_OP_THREADS),
        "accelerator_count": _metric("accelerators", ACCELERATORS, ACCELERATORS),
    }
    paths: dict[str, dict[str, object]] = {
        "gate_only": {
            "metrics": {
                "wall_seconds": gate_wall,
                "cpu_seconds": gate_cpu,
                "peak_rss_bytes": gate_peak,
                "temporary_bytes": gate_temporary,
                "retained_bytes": gate_retained,
                **count_metrics,
            }
        },
        "all_pass": {
            "metrics": {
                "wall_seconds": all_pass_wall,
                "cpu_seconds": all_pass_cpu,
                "peak_rss_bytes": all_pass_peak,
                "temporary_bytes": all_pass_temporary,
                "retained_bytes": all_pass_retained,
                **count_metrics,
            }
        },
    }

    memory_raw = _optional_nonnegative_int(
        capacities.get("memory_available_bytes"), "available memory"
    )
    disk_raw = _optional_nonnegative_int(capacities.get("disk_available_bytes"), "available disk")
    memory_capacity = _capacity(memory_raw)
    disk_capacity = _capacity(disk_raw)
    memory_safe_available = _optional_nonnegative_int(
        memory_capacity.get("safe_available"), "safe available memory"
    )
    disk_safe_available = _optional_nonnegative_int(
        disk_capacity.get("safe_available"), "safe available disk"
    )
    unknowns: list[dict[str, str]] = [
        {
            "quantity": "gate_only.temporary_bytes",
            "status": "unknown",
            "reason": gate_storage_reason,
        },
        {
            "quantity": "gate_only.retained_bytes",
            "status": "unknown",
            "reason": gate_storage_reason,
        },
    ]
    if memory_raw is None:
        unknowns.append(
            {
                "quantity": "capacity.memory_available_bytes",
                "status": "unknown",
                "reason": "Available memory could not be measured.",
            }
        )
    if disk_raw is None:
        unknowns.append(
            {
                "quantity": "capacity.disk_available_bytes",
                "status": "unknown",
                "reason": "Available disk could not be measured.",
            }
        )
    for unit_name, summary in timing.items():
        if summary["status"] == "unknown":
            unknowns.append(
                {
                    "quantity": f"timing.{unit_name}",
                    "status": "unknown",
                    "reason": str(summary["reason"]),
                }
            )

    for path_name, path in paths.items():
        metrics = path["metrics"]
        assert isinstance(metrics, Mapping)
        peak_upper = metrics["peak_rss_bytes"]["conservative_upper"]
        temporary_upper = metrics["temporary_bytes"]["conservative_upper"]
        retained_upper = metrics["retained_bytes"]["conservative_upper"]
        disk_upper = (
            None
            if temporary_upper is None or retained_upper is None
            else max(int(temporary_upper), int(retained_upper))
        )
        comparisons = {
            "memory": _comparison(
                peak_upper,
                memory_safe_available,
                MEMORY_SOURCE_ENVELOPE_BYTES,
                "peak_rss_bytes.conservative_upper",
            ),
            "disk": _comparison(
                disk_upper,
                disk_safe_available,
                DISK_SOURCE_ENVELOPE_BYTES,
                "max(temporary_bytes.conservative_upper, retained_bytes.conservative_upper)",
            ),
        }
        path["comparisons"] = comparisons
        path["memory_classification"] = _classify_memory(comparisons["memory"])
        path["disk_classification"] = _classify_disk(comparisons["disk"])

    all_pass_wall_classification = _classify_wall(all_pass_wall)
    all_pass_comparisons = paths["all_pass"]["comparisons"]
    assert isinstance(all_pass_comparisons, Mapping)
    all_pass_memory_classification = _classify_memory(all_pass_comparisons["memory"])
    all_pass_disk_classification = _classify_disk(all_pass_comparisons["disk"])
    above_threshold = all_pass_wall_classification == "above_7200_seconds"
    wall_ungrounded = all_pass_wall_classification == "ungrounded"
    memory_reduction_required = (
        True
        if all_pass_memory_classification == "reduction_batching_or_sharding_required"
        else None
        if all_pass_memory_classification == "ungrounded"
        else False
    )

    storage_facts = {
        "raw_per_packet_payload": _storage_fact(
            storage["raw_per_packet_payload_bytes"], "110_000_000 bytes"
        ),
        "compressed_per_packet": _storage_fact(
            storage["compressed_per_packet_bytes"], "observed compressed NPZ packet bytes"
        ),
        "logical_sixteen_packet": _storage_fact(
            storage["logical_sixteen_packet_bytes"], "16 * compressed_per_packet"
        ),
        "raw_source_table_payload": _storage_fact(
            storage["raw_source_table_payload_bytes"], "312_064 bytes"
        ),
        "compressed_table": _storage_fact(
            storage["compressed_table_bytes"], "observed compressed NPZ table bytes"
        ),
        "metadata_json": _storage_fact(storage["metadata_json_bytes"], "observed canonical JSON bytes"),
        "staging_temporary": _storage_fact(
            storage["staging_temporary_bytes"],
            "logical sixteen-packet + compressed table + metadata JSON",
        ),
        "complete_tree": _storage_fact(
            storage["complete_tree_bytes"],
            "logical sixteen-packet + compressed table + metadata JSON",
        ),
    }

    report: dict[str, object] = {
        "artifact": {
            "kind": "mgtap_non_scientific_preactivity_resource_estimate",
            "schema_version": 1,
        },
        "runtime_configuration": {
            "cpu_processes": CPU_PROCESSES,
            "numerical_library_and_torch_intra_op_threads": INTRA_OP_THREADS,
            "torch_inter_op_threads": INTER_OP_THREADS,
            "accelerators": ACCELERATORS,
            "thread_environment": {
                name: os.environ[name] for name in _THREAD_ENVIRONMENT
            },
        },
        "identity": dict(identity),
        "workload": {
            "counts": dict(WORKLOAD_COUNTS),
            "formulas": {
                "gate_only_wall_and_cpu": GATE_FORMULA,
                "all_pass_wall_and_cpu": ALL_PASS_FORMULA,
                "gate_only_peak_rss": "max(cold imported process, actor/autograd, validation panel)",
                "all_pass_peak_rss": "max(all observed process high-water stages)",
                "gate_only_storage": None,
                "all_pass_temporary_storage": "staging_temporary_bytes",
                "all_pass_retained_storage": "complete_tree_bytes",
            },
            "fixture_shapes": {
                "training_episodes": TRAINING_EPISODES,
                "training_epochs": TRAINING_EPOCHS,
                "validation_panel_rows": VALIDATION_PANEL_ROWS,
                "base_plus_replay_rows": BASE_PLUS_REPLAY_ROWS,
                "evaluation_rows_per_fit": EVALUATION_ROWS_PER_FIT,
                "combined_packet_rows": COMBINED_PACKET_ROWS,
                "four_fit_members": FOUR_FIT_MEMBERS,
                "raw_per_packet_payload_bytes": RAW_PACKET_PAYLOAD_BYTES,
                "source_table_payload_bytes": SOURCE_TABLE_PAYLOAD_BYTES,
                "logical_packet_count": LOGICAL_PACKET_COUNT,
            },
            "compression_probe_projection_count": 0,
            "compression_probe_projection_rationale": (
                "The probe establishes compression high-water behavior; packet write units already include compression."
            ),
        },
        "factors": {
            "timing_uncertainty": {
                "value": TIMING_UNCERTAINTY_FACTOR,
                "rationale": (
                    "Applied to each observed timing maximum for run-to-run variation; every projected unit remains explicit."
                ),
            },
            "peak_rss_safety": {
                "value": PEAK_RSS_SAFETY_FACTOR,
                "rationale": "Allows allocator and runtime high-water variation above the observed process peak.",
            },
            "temporary_storage_safety": {
                "value": TEMPORARY_STORAGE_SAFETY_FACTOR,
                "rationale": "Allows filesystem allocation and staging variation above measured bytes.",
            },
            "retained_storage_safety": {
                "value": RETAINED_STORAGE_SAFETY_FACTOR,
                "rationale": "Allows filesystem allocation variation above the complete-tree projection.",
            },
            "capacity_reserve": {
                "value": CAPACITY_RESERVE_FACTOR,
                "rationale": "Only this fraction of raw available capacity is treated as safely usable.",
            },
        },
        "measurements": {
            "measurement_repetitions": measurements.get("measurement_repetitions"),
            "peak_rss_observer": {
                "platform": "Linux",
                "source": "resource.getrusage(RUSAGE_SELF).ru_maxrss",
                "native_unit": "KiB",
                "conversion": "integer KiB * 1024 bytes",
            },
            "cold_imported_process_rss": cold,
            "timing_units": timing,
            "rss_stages_bytes": rss_stages,
            "storage_units": storage_facts,
        },
        "projection_components": {
            "gate_only": gate_components,
            "all_pass": all_pass_components,
        },
        "capacities": {
            "memory": memory_capacity,
            "disk": disk_capacity,
            "source_envelopes": {
                "memory_bytes": MEMORY_SOURCE_ENVELOPE_BYTES,
                "disk_bytes": DISK_SOURCE_ENVELOPE_BYTES,
            },
        },
        "paths": paths,
        "unknowns": unknowns,
        "actions": {
            "all_pass_wall_classification": all_pass_wall_classification,
            "all_pass_memory_classification": all_pass_memory_classification,
            "all_pass_disk_classification": all_pass_disk_classification,
            "unsafe_memory": {
                "reduction_batching_or_sharding_required": memory_reduction_required,
                "approval_route_available": False,
            },
            "later_high_cost_execution": {
                "performance_reasonableness_review_attempt_required": (
                    None if wall_ungrounded else above_threshold
                ),
                "explicit_user_approval_required": None if wall_ungrounded else above_threshold,
                "self_authorized": False,
            },
        },
    }
    _artifact_firewall(report)
    return report


def _read_capacities(output_parent: Path) -> dict[str, int | None]:
    memory_available = _read_proc_kib(Path("/proc/meminfo"), "MemAvailable")
    try:
        disk_available = shutil.disk_usage(output_parent).free
    except OSError:
        disk_available = None
    return {
        "memory_available_bytes": memory_available,
        "disk_available_bytes": disk_available,
    }


def _normalized_words(text: str) -> list[str]:
    normalized = "".join(character.casefold() if character.isalnum() else " " for character in text)
    return normalized.split()


def _check_field_name(name: str, location: str) -> None:
    words = _normalized_words(name)
    word_set = set(words)
    if word_set & _FORBIDDEN_KEY_TOKENS:
        raise ArtifactFirewallError(f"Forbidden field name at {location}")
    normalized_name = "_".join(words)
    if "validation" in word_set and normalized_name not in _ALLOWED_VALIDATION_KEYS:
        raise ArtifactFirewallError(f"Forbidden field name at {location}")
    if "validation" in word_set and ({"value", "values", "statistic", "statistics"} & word_set):
        raise ArtifactFirewallError(f"Forbidden field name at {location}")


def _check_string_tokens(value: str, location: str) -> None:
    words = set(_normalized_words(value))
    if words & _FORBIDDEN_STRING_TOKENS:
        raise ArtifactFirewallError(f"Forbidden string token at {location}")
    if "partial" in words and ({"value", "values"} & words):
        raise ArtifactFirewallError(f"Forbidden string token at {location}")
    if "validation" in words and ({"value", "values", "statistic", "statistics"} & words):
        raise ArtifactFirewallError(f"Forbidden string token at {location}")
    if "registered" in words and ({"seed", "seeds", "address", "addresses"} & words):
        raise ArtifactFirewallError(f"Forbidden string token at {location}")


def _artifact_firewall(value: object, location: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ArtifactFirewallError(f"Non-finite number at {location}")
        return
    if isinstance(value, str):
        _check_string_tokens(value, location)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _artifact_firewall(item, f"{location}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ArtifactFirewallError(f"Non-string field name at {location}")
            _check_field_name(key, f"{location}.{key}")
            _artifact_firewall(item, f"{location}.{key}")
        return
    raise ArtifactFirewallError(f"Unsupported artifact type at {location}")


def _canonical_json_bytes(report: Mapping[str, object]) -> bytes:
    _artifact_firewall(report)
    try:
        encoded = json.dumps(
            report,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ArtifactFirewallError("The estimate is not canonical finite JSON") from exc
    return encoded + b"\n"


def _canonical_output_path(raw_output: str | os.PathLike[str]) -> Path:
    _require_linux()
    raw = os.fspath(raw_output)
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise OutputPathError("The output path must be a nonempty string")
    if not os.path.isabs(raw):
        raise OutputPathError("The output path must be absolute")
    if os.path.normpath(raw) != raw:
        raise OutputPathError("The output path must already be canonical")
    path = Path(raw)
    if path.suffix != ".json":
        raise OutputPathError("The output path must have the .json suffix")
    parent = path.parent
    try:
        resolved_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise OutputPathError("The output parent must already exist") from exc
    if parent != resolved_parent or not resolved_parent.is_dir():
        raise OutputPathError("The output parent must be canonical and contain no symlink traversal")
    if path.name in ("", ".", ".."):
        raise OutputPathError("The output filename is invalid")
    return path


def _ensure_absent(directory_fd: int, name: str) -> None:
    try:
        os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise OutputPathError(f"Could not preflight fresh path {name!r}") from exc
    raise OutputPathError(f"Fresh path already exists: {name!r}")


@contextmanager
def _preflight_output(raw_output: str | os.PathLike[str]) -> Iterator[_OutputTarget]:
    path = _canonical_output_path(raw_output)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        directory_fd = os.open(path.parent, flags)
    except OSError as exc:
        raise OutputPathError("The canonical output parent could not be opened") from exc
    target = _OutputTarget(
        path=path,
        parent=path.parent,
        final_name=path.name,
        temporary_name=f"{path.name}.tmp",
        directory_fd=directory_fd,
    )
    try:
        _ensure_absent(directory_fd, target.final_name)
        _ensure_absent(directory_fd, target.temporary_name)
        yield target
    finally:
        os.close(directory_fd)


def _write_report_once(target: _OutputTarget, report: Mapping[str, object]) -> None:
    payload = _canonical_json_bytes(report)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    temporary_created = False
    try:
        try:
            file_descriptor = os.open(
                target.temporary_name,
                flags,
                0o600,
                dir_fd=target.directory_fd,
            )
        except FileExistsError as exc:
            raise OutputPathError("The fixed temporary sibling was created concurrently") from exc
        except OSError as exc:
            raise OutputPathError("The fixed temporary sibling could not be created exclusively") from exc
        temporary_created = True
        try:
            offset = 0
            while offset < len(payload):
                written = os.write(file_descriptor, payload[offset:])
                if written <= 0:
                    raise OutputPathError("The estimate bytes could not be written completely")
                offset += written
            os.fsync(file_descriptor)
        finally:
            os.close(file_descriptor)

        try:
            os.link(
                target.temporary_name,
                target.final_name,
                src_dir_fd=target.directory_fd,
                dst_dir_fd=target.directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise OutputPathError("The final output was created concurrently and was not overwritten") from exc
        except OSError as exc:
            raise OutputPathError("The final output could not be installed with no-replace semantics") from exc
        os.fsync(target.directory_fd)
    finally:
        if temporary_created:
            try:
                os.unlink(target.temporary_name, dir_fd=target.directory_fd)
            except FileNotFoundError:
                pass
            finally:
                os.fsync(target.directory_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure non-scientific MGTAP preactivity resource requirements."
    )
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args(argv)

    with _preflight_output(arguments.output) as target:
        capacities = _read_capacities(target.parent)
        measurements = _run_guarded_collection(
            lambda: _collect_default_measurements(target.parent)
        )
        report = _build_report(measurements, capacities)
        _write_report_once(target, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
