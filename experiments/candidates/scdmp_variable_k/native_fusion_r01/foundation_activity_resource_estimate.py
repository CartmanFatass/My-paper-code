"""Measure nonregistered primitives and project the exact S4 foundation workload."""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import tempfile
import time
from typing import Final, Mapping, Sequence

import torch

from .foundation_activity_executor import (
    AddressBook,
    ExecutionProfile,
    FoundationActivityExecutor,
)
from .foundation_network import build_technical_foundation
from .foundation_optimizer import build_adamw, clip_global_gradients
from .foundation_run_manifest import canonical_json_bytes


S4_OUTPUT_ROOT: Final[str] = (
    "temp/directions/semigroup_consistent_duration_model_policy/test/"
    "native_fusion_r01/s4/g1"
)
ESTIMATE_PATH: Final[str] = f"{S4_OUTPUT_ROOT}/S4_ACTIVITY_RESOURCE_ESTIMATE.json"
REPAIR_ESTIMATE_PATH: Final[str] = (
    f"{S4_OUTPUT_ROOT}/executor-repair/"
    "S4_EXECUTOR_REPAIR_ACTIVITY_RESOURCE_ESTIMATE.json"
)
WORKLOAD: Final[dict[str, int]] = {
    "replicates": 24,
    "updates_per_foundation": 192,
    "episodes_per_update": 16,
    "total_episodes": 73_728,
    "total_allocated_primitive_slots": 30_965_760,
    "total_maximum_policy_queries": 5_419_008,
    "total_adamw_steps": 73_728,
    "final_checkpoint_slots": 24,
}
UNCERTAINTY_FACTORS: Final[dict[str, float]] = {
    "low": 1.0,
    "central": 2.0,
    "high": 4.0,
}
SOURCE_PATHS: Final[tuple[str, ...]] = (
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_executor.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_production.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_resource_estimate.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_activity_validation.py",
    "experiments/candidates/scdmp_variable_k/native_fusion_r01/foundation_run_manifest.py",
    "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_foundation_activity_prelaunch.py",
)


@dataclass(frozen=True)
class MeasuredPrimitive:
    repetitions: int
    units_per_repetition: int
    wall_seconds_per_unit: float
    cpu_seconds_per_unit: float

    def __post_init__(self) -> None:
        values = (
            self.repetitions,
            self.units_per_repetition,
            self.wall_seconds_per_unit,
            self.cpu_seconds_per_unit,
        )
        if (
            isinstance(self.repetitions, bool)
            or not isinstance(self.repetitions, int)
            or self.repetitions < 3
            or isinstance(self.units_per_repetition, bool)
            or not isinstance(self.units_per_repetition, int)
            or self.units_per_repetition < 1
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
                for value in values[2:]
            )
        ):
            raise ValueError("measured primitive is incomplete")


@dataclass(frozen=True)
class ActivityPrimitiveMeasurements:
    allocated_slot: MeasuredPrimitive
    policy_query: MeasuredPrimitive
    adamw_step: MeasuredPrimitive
    baseline_peak_rss_bytes: int
    one_update_scratch_bytes: int
    one_checkpoint_retained_bytes: int
    one_checkpoint_io_bytes: int

    def __post_init__(self) -> None:
        for value in (
            self.baseline_peak_rss_bytes,
            self.one_update_scratch_bytes,
            self.one_checkpoint_retained_bytes,
            self.one_checkpoint_io_bytes,
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError("resource byte measurement is incomplete")


@dataclass(frozen=True)
class ExecutorPrimitiveMeasurement:
    initialization_wall_seconds: float
    initialization_cpu_seconds: float
    update_wall_seconds: float
    update_cpu_seconds: float
    peak_rss_bytes: int

    def __post_init__(self) -> None:
        for value in (
            self.initialization_wall_seconds,
            self.initialization_cpu_seconds,
            self.update_wall_seconds,
            self.update_cpu_seconds,
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError("executor primitive timing is incomplete")
        if (
            isinstance(self.peak_rss_bytes, bool)
            or not isinstance(self.peak_rss_bytes, int)
            or self.peak_rss_bytes <= 0
        ):
            raise ValueError("executor peak RSS is incomplete")


def project_activity_estimate(
    measured: ActivityPrimitiveMeasurements,
) -> dict[str, object]:
    raw_wall = (
        WORKLOAD["total_allocated_primitive_slots"]
        * measured.allocated_slot.wall_seconds_per_unit
        + WORKLOAD["total_maximum_policy_queries"]
        * measured.policy_query.wall_seconds_per_unit
        + WORKLOAD["total_adamw_steps"]
        * measured.adamw_step.wall_seconds_per_unit
    )
    raw_cpu = (
        WORKLOAD["total_allocated_primitive_slots"]
        * measured.allocated_slot.cpu_seconds_per_unit
        + WORKLOAD["total_maximum_policy_queries"]
        * measured.policy_query.cpu_seconds_per_unit
        + WORKLOAD["total_adamw_steps"]
        * measured.adamw_step.cpu_seconds_per_unit
    )
    estimates: dict[str, dict[str, object]] = {}
    for label, factor in UNCERTAINTY_FACTORS.items():
        memory_factor = {"low": 1.0, "central": 1.5, "high": 2.0}[label]
        storage_factor = {"low": 1.0, "central": 1.5, "high": 2.0}[label]
        scratch_factor = factor
        estimates[label] = {
            "wall_seconds": raw_wall * factor,
            "cpu_core_seconds": raw_cpu * factor,
            "cpu_core_hours": raw_cpu * factor / 3_600.0,
            "peak_memory_bytes": math.ceil(
                (
                    measured.baseline_peak_rss_bytes
                    + measured.one_update_scratch_bytes
                )
                * memory_factor
            ),
            "scratch_bytes": math.ceil(
                measured.one_update_scratch_bytes * scratch_factor
            ),
            "retained_storage_bytes": math.ceil(
                measured.one_checkpoint_retained_bytes
                * WORKLOAD["final_checkpoint_slots"]
                * storage_factor
            ),
            "io_bytes": math.ceil(
                measured.one_checkpoint_io_bytes
                * WORKLOAD["final_checkpoint_slots"]
                * storage_factor
            ),
        }
    high_wall = float(estimates["high"]["wall_seconds"])
    classification = "<=7200" if high_wall <= 7_200.0 else ">7200"
    high_peak = int(estimates["high"]["peak_memory_bytes"])
    unsafe_memory = high_peak > 12 * 1024**3
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S4_ACTIVITY_RESOURCE_ESTIMATE_V1",
        "workload": dict(WORKLOAD),
        "measured_primitives": {
            "allocated_slot": asdict(measured.allocated_slot),
            "policy_query": asdict(measured.policy_query),
            "adamw_step": asdict(measured.adamw_step),
            "baseline_peak_rss_bytes": measured.baseline_peak_rss_bytes,
            "one_update_scratch_bytes": measured.one_update_scratch_bytes,
            "one_checkpoint_retained_bytes": measured.one_checkpoint_retained_bytes,
            "one_checkpoint_io_bytes": measured.one_checkpoint_io_bytes,
            "registered": False,
            "reward_evaluated": False,
            "question_relevant_value_evaluated": False,
        },
        "repetition_policy": {"warmups": 2, "measured_repetitions": 7},
        "scaling_formulas": {
            "wall_seconds": (
                "slot.wall_per_unit*30965760 + query.wall_per_unit*5419008 + "
                "adamw.wall_per_unit*73728"
            ),
            "cpu_core_seconds": (
                "slot.cpu_per_unit*30965760 + query.cpu_per_unit*5419008 + "
                "adamw.cpu_per_unit*73728"
            ),
            "retained_storage_bytes": "checkpoint_retained_bytes*24",
            "io_bytes": "checkpoint_io_bytes*24",
            "scratch_bytes": "one sequential worker*one update scratch",
        },
        "uncertainty_factors": dict(UNCERTAINTY_FACTORS),
        "estimates": estimates,
        "runtime_classification": classification,
        "classification_basis": "high one-worker projected wall seconds versus 7200",
        "performance_reasonableness_review_required": classification == ">7200",
        "explicit_user_approval_required_before_activity": classification == ">7200",
        "device_limits": {
            "workers": 1,
            "cpu_threads": 1,
            "accelerators": 0,
            "foundations_concurrent": 1,
        },
        "memory_plan": "sequential foundations; one update resident; checkpoints emitted one at a time",
        "unsafe_memory_plan": unsafe_memory,
        "unmeasured_primitives": [],
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }


def apply_executor_projection(
    base_estimate: Mapping[str, object],
    measured: ExecutorPrimitiveMeasurement,
) -> dict[str, object]:
    estimate = copy.deepcopy(dict(base_estimate))
    estimates = estimate.get("estimates")
    if not isinstance(estimates, dict) or set(estimates) != {
        "low",
        "central",
        "high",
    }:
        raise ValueError("base estimate has no low/central/high rows")
    raw_wall = (
        24 * measured.initialization_wall_seconds
        + 4_608 * measured.update_wall_seconds
    )
    raw_cpu = (
        24 * measured.initialization_cpu_seconds
        + 4_608 * measured.update_cpu_seconds
    )
    memory_factors = {"low": 1.0, "central": 1.5, "high": 2.0}
    for label, factor in UNCERTAINTY_FACTORS.items():
        row = estimates[label]
        if not isinstance(row, dict):
            raise ValueError("base estimate resource row differs")
        row["wall_seconds"] = max(float(row["wall_seconds"]), raw_wall * factor)
        row["cpu_core_seconds"] = max(
            float(row["cpu_core_seconds"]), raw_cpu * factor
        )
        row["cpu_core_hours"] = float(row["cpu_core_seconds"]) / 3_600.0
        row["peak_memory_bytes"] = max(
            int(row["peak_memory_bytes"]),
            math.ceil(measured.peak_rss_bytes * memory_factors[label]),
        )
    measured_primitives = estimate.get("measured_primitives")
    if not isinstance(measured_primitives, dict):
        raise ValueError("base measured primitives differ")
    measured_primitives["foundation_executor"] = asdict(measured)
    estimate["executor_scaling_formulas"] = {
        "wall_seconds": "initialization_wall_seconds*24 + update_wall_seconds*4608",
        "cpu_core_seconds": "initialization_cpu_seconds*24 + update_cpu_seconds*4608",
        "uncertainty": "low*1, central*2, high*4",
    }
    high_wall = float(estimates["high"]["wall_seconds"])
    classification = "<=7200" if high_wall <= 7_200 else ">7200"
    estimate["runtime_classification"] = classification
    estimate["classification_basis"] = (
        "maximum of primitive and executor high one-worker projected wall seconds "
        "versus 7200"
    )
    estimate["performance_reasonableness_review_required"] = (
        classification == ">7200"
    )
    estimate["explicit_user_approval_required_before_activity"] = (
        classification == ">7200"
    )
    return estimate


def _median_timing(
    function: callable, *, units: int, invocations_per_repetition: int
) -> MeasuredPrimitive:
    for _ in range(2):
        for _ in range(invocations_per_repetition):
            function()
    wall_samples: list[float] = []
    cpu_samples: list[float] = []
    measured_units = units * invocations_per_repetition
    for _ in range(7):
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        for _ in range(invocations_per_repetition):
            function()
        cpu_samples.append((time.process_time() - cpu_started) / measured_units)
        wall_samples.append((time.perf_counter() - wall_started) / measured_units)
    return MeasuredPrimitive(
        repetitions=7,
        units_per_repetition=measured_units,
        wall_seconds_per_unit=statistics.median(wall_samples),
        cpu_seconds_per_unit=statistics.median(cpu_samples),
    )


def _slot_fixture() -> None:
    x, v, phi, omega, z, fatigue = 0.0, 0.4, 0.03, -0.02, 0.01, 0.02
    command, reserve, bias = 0.6, 0.55, -0.1
    for _ in range(1_024):
        tension = 0.42 + 0.17 * command + 0.11 * abs(command - reserve)
        excess = max(0.0, tension - (1.04 - 0.16 * reserve))
        omega = 0.90 * omega - 0.12 * phi + 0.055 * bias + 0.035 * reserve * command
        phi = min(0.70, max(-0.70, phi + 0.1 * omega))
        v = min(1.8, max(0.0, 0.94 * v + 0.06 * command - 0.018 * reserve * command**2 - 0.025 * abs(phi)))
        x += 0.1 * v
        z = 0.86 * z + excess
        fatigue = 0.84 * fatigue + 0.09 * bias + 0.08 * abs(phi)
    if not math.isfinite(x + v + phi + omega + z + fatigue):
        raise RuntimeError("nonregistered slot fixture became nonfinite")


def _policy_fixture(model: torch.nn.Module, observation: torch.Tensor) -> None:
    with torch.no_grad():
        actor = model.actor(observation)
        critic = model.critic(observation)
        if actor.shape != (512, 27) or critic.shape != (512,):
            raise RuntimeError("technical policy fixture shape differs")


def _adamw_fixture(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    observation: torch.Tensor,
) -> None:
    optimizer.zero_grad(set_to_none=True)
    actor = model.actor(observation)
    critic = model.critic(observation)
    loss = actor.square().mean() + critic.square().mean()
    loss.backward()
    clip_global_gradients(model.parameters())
    optimizer.step()


def _peak_rss_bytes() -> int:
    if os.name != "nt":
        return 1
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.argtypes = []
    get_current_process.restype = wintypes.HANDLE
    get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessMemoryCounters),
        wintypes.DWORD,
    ]
    get_process_memory_info.restype = wintypes.BOOL
    handle = get_current_process()
    if not get_process_memory_info(
        handle, ctypes.byref(counters), counters.cb
    ):
        raise RuntimeError("cannot observe process peak working set")
    return int(counters.PeakWorkingSetSize)


def measure_nonregistered_primitives() -> ActivityPrimitiveMeasurements:
    torch.set_num_threads(1)
    model = build_technical_foundation()
    policy_observation = torch.linspace(-0.5, 0.5, 512 * 14, dtype=torch.float32).reshape(512, 14)
    adamw_observation = policy_observation[:420].clone()
    optimizer = build_adamw(model.parameters())
    allocated = _median_timing(
        _slot_fixture, units=1_024, invocations_per_repetition=32
    )
    query = _median_timing(
        lambda: _policy_fixture(model, policy_observation),
        units=512,
        invocations_per_repetition=32,
    )
    adamw = _median_timing(
        lambda: _adamw_fixture(model, optimizer, adamw_observation),
        units=1,
        invocations_per_repetition=16,
    )
    maximum_records_per_update = 8 * (420 // 4) + 8 * (420 // 10)
    bytes_per_record = 128
    immutable_old_state_bytes = 17_628 * 4
    update_scratch = 4 * (
        maximum_records_per_update * bytes_per_record + immutable_old_state_bytes
    )
    checkpoint_retained = 17_628 * 4 * 3 + 4_096
    return ActivityPrimitiveMeasurements(
        allocated_slot=allocated,
        policy_query=query,
        adamw_step=adamw,
        baseline_peak_rss_bytes=_peak_rss_bytes(),
        one_update_scratch_bytes=update_scratch,
        one_checkpoint_retained_bytes=checkpoint_retained,
        one_checkpoint_io_bytes=checkpoint_retained * 2,
    )


def measure_nonregistered_executor() -> ExecutorPrimitiveMeasurement:
    executor = FoundationActivityExecutor(
        address_book=AddressBook(master=bytes(range(32)), registered=False),
        profile=ExecutionProfile.technical_single_foundation(),
    )
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    runtime = executor.new_runtime(replicate_index=0)
    initialization_cpu = time.process_time() - cpu_started
    initialization_wall = time.perf_counter() - wall_started
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    evidence = executor.run_next_update(runtime)
    update_cpu = time.process_time() - cpu_started
    update_wall = time.perf_counter() - wall_started
    if evidence.episodes != 16 or evidence.adamw_steps != 16:
        raise RuntimeError("executor measurement workload differs")
    return ExecutorPrimitiveMeasurement(
        initialization_wall_seconds=initialization_wall,
        initialization_cpu_seconds=initialization_cpu,
        update_wall_seconds=update_wall,
        update_cpu_seconds=update_cpu,
        peak_rss_bytes=_peak_rss_bytes(),
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_estimate_document(repository_root: Path) -> dict[str, object]:
    root = Path(repository_root).resolve()
    refs = []
    for relative in SOURCE_PATHS:
        target = root / relative
        if not target.is_file():
            raise RuntimeError(f"S4 source is absent: {relative}")
        refs.append({"path": relative, "sha256": _sha(target)})
    estimate = apply_executor_projection(
        project_activity_estimate(measure_nonregistered_primitives()),
        measure_nonregistered_executor(),
    )
    return {
        **estimate,
        "implementation_refs": refs,
        "runtime": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cpu_count": os.cpu_count(),
            "workers": 1,
            "torch_threads": torch.get_num_threads(),
            "accelerators": 0,
        },
        "measurement_attestation": {
            "nonregistered_deterministic_fixtures_only": True,
            "operating_system_master_drawn": False,
            "hmac_address_materialized": False,
            "registered_foundation_instantiated": False,
            "registered_optimizer_or_reward_activity": False,
            "question_relevant_value_visible": False,
        },
    }


def _emit_create_only(path: Path, value: Mapping[str, object]) -> None:
    target = Path(path)
    expected = {
        (Path.cwd().resolve() / ESTIMATE_PATH).resolve(strict=False),
        (Path.cwd().resolve() / REPAIR_ESTIMATE_PATH).resolve(strict=False),
    }
    if target.resolve(strict=False) not in expected:
        raise RuntimeError("estimator output path differs from the exact S4 path")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", delete=False
        ) as temporary:
            temporary.write(canonical_json_bytes(value))
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.link(temporary_name, target)
    except FileExistsError as exc:
        raise RuntimeError("S4 estimate is create-only") from exc
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Measure deterministic nonregistered SCDMP foundation primitives and "
            "write one complete S4 activity estimate."
        )
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    document = build_estimate_document(Path.cwd())
    _emit_create_only(args.output, document)
    print(
        json.dumps(
            {
                "classification": document["runtime_classification"],
                "output": str(args.output).replace("\\", "/"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
