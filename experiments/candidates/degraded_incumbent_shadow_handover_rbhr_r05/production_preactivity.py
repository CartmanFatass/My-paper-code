"""Result-blind production construction acceptance for DISH RBHR r05."""

from __future__ import annotations

import hashlib
import ctypes
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Iterable

import numpy as np
import torch

from .production_analysis import (
    complete_estimand_source_manifest, complete_hypothesis_inventory,
    estimand_manifest_identity, run_native_connected_analyzer_seam,
    run_result_blind_analyzer_seam,
)
from .production_backend import (
    TestNativeBatch, TestProtocolNativeBatch, artifact_identity, empty_step_rows,
    native_natural_protocol_trace, native_protocol_audit,
    native_protocol_transition_probe, rng_words_test_native,
    scan_test_candidate_attempts,
)
from .production_contract import (
    BLOCKS, PREACTIVITY_NAMESPACE, SCIENCE_FILES, ARMS, PreactivityAuthority,
    complete_inventory, science_root,
)
from .production_lifecycle import (
    BINDING_COMPONENTS, BlindedFrontierPlan, run_real_byte_lifecycle_seam,
    run_result_blind_lifecycle_seam,
)
from .production_protocol import test_wire_fixture_inventory
from .production_tapes import candidate_accounting_identity
from .production_training import run_full_4096_dry_update


class PreactivityAcceptanceError(RuntimeError):
    pass


def _rss_bytes() -> int:
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    counters = Counters(); counters.cb = ctypes.sizeof(counters)
    if os.name != "nt":
        return 0
    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.argtypes = []; get_process.restype = ctypes.c_void_p
    get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    get_memory.restype = ctypes.c_int
    if not get_memory(get_process(), ctypes.byref(counters), counters.cb):
        raise PreactivityAcceptanceError("process RSS could not be measured")
    return int(counters.WorkingSetSize)


def process_memory_bytes(pid: int) -> dict[str, int]:
    """Measure current and lifetime-peak working set for one live Windows PID."""

    if os.name != "nt" or pid <= 0:
        raise PreactivityAcceptanceError("process-group RSS measurement requires one live Windows PID")

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    PROCESS_VM_READ = 0x0010
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = ctypes.c_int
    handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, 0, int(pid))
    if not handle:
        raise PreactivityAcceptanceError(f"could not open process for RSS measurement: pid={pid}")
    try:
        counters = Counters(); counters.cb = ctypes.sizeof(counters)
        get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
        get_memory.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
        get_memory.restype = ctypes.c_int
        if not get_memory(handle, ctypes.byref(counters), counters.cb):
            raise PreactivityAcceptanceError(f"process RSS could not be measured: pid={pid}")
        return {"current": int(counters.WorkingSetSize), "peak": int(counters.PeakWorkingSetSize)}
    finally:
        kernel.CloseHandle(handle)


def process_io_bytes(pid: int) -> dict[str, int]:
    """Read cumulative process I/O counters for one live Windows PID."""

    if os.name != "nt" or pid <= 0:
        raise PreactivityAcceptanceError("process I/O measurement requires one live Windows PID")

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64), ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64), ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64), ("OtherTransferCount", ctypes.c_uint64),
        ]

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = ctypes.c_int
    kernel.GetProcessIoCounters.argtypes = [ctypes.c_void_p, ctypes.POINTER(IoCounters)]
    kernel.GetProcessIoCounters.restype = ctypes.c_int
    handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, int(pid))
    if not handle:
        raise PreactivityAcceptanceError(f"could not open process for I/O measurement: pid={pid}")
    try:
        counters = IoCounters()
        if not kernel.GetProcessIoCounters(handle, ctypes.byref(counters)):
            raise PreactivityAcceptanceError(f"process I/O could not be measured: pid={pid}")
        return {
            "read_operations": int(counters.ReadOperationCount),
            "write_operations": int(counters.WriteOperationCount),
            "other_operations": int(counters.OtherOperationCount),
            "read_bytes": int(counters.ReadTransferCount),
            "write_bytes": int(counters.WriteTransferCount),
            "other_bytes": int(counters.OtherTransferCount),
        }
    finally:
        kernel.CloseHandle(handle)


HIGH_GATES = {
    "cpu_core_hours": 560.0,
    "wall_hours": 110.0,
    "aggregate_rss_gib": 40.0,
    "scratch_gib": 120.0,
    "durable_gib": 16.0,
    "total_io_gib": 400.0,
}

BASELINE_PLANNING_PROJECTION = {
    "cpu_core_hours": {"low": 220.0, "central": 320.0, "high": 560.0},
    "wall_hours": {"low": 45.0, "central": 65.0, "high": 110.0},
    "aggregate_rss_gib": {"low": 14.0, "central": 24.0, "high": 40.0},
    "scratch_gib": {"low": 12.0, "central": 40.0, "high": 120.0},
    "durable_gib": {"low": 2.0, "central": 6.0, "high": 16.0},
    "total_io_gib": {"low": 25.0, "central": 100.0, "high": 400.0},
}


def verify_science_composite(repository_root: Path) -> dict[str, str]:
    root = science_root(repository_root)
    observed: dict[str, str] = {}
    for name, expected in SCIENCE_FILES:
        path = root / name
        if not path.is_file():
            raise PreactivityAcceptanceError(f"science composite member is absent: {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise PreactivityAcceptanceError(f"science composite member changed: {name}")
        observed[name] = digest
    return observed


def _rollout_rows(width: int, steps: int) -> np.ndarray:
    base = empty_step_rows(width)
    rows = np.repeat(base[None, :], steps, axis=0)
    tick = np.arange(steps, dtype=np.float64)[:, None]
    lane = np.arange(width, dtype=np.float64)[None, :]
    rows["raw_action"][:, :, 0] = 0.7 * np.sin(tick * 0.03 + lane * 0.01)
    rows["raw_action"][:, :, 1] = 0.7 * np.cos(tick * 0.02 + lane * 0.01)
    rows["raw_action"][:, :, 2] = -rows["raw_action"][:, :, 0]
    rows["raw_action"][:, :, 3] = -rows["raw_action"][:, :, 1]
    rows["prediction_mean"][:, :, 0] = tick * 0.4
    rows["prediction_mean"][:, :, 1] = -120.0
    rows["prediction_mean"][:, :, 4] = tick * 0.4
    rows["prediction_mean"][:, :, 5] = -120.0
    rows["prepare"][:, :, :] = 1
    rows["commit"][:, :, :] = 1
    return rows


def benchmark_native_rollout(width: int, *, steps: int = 256) -> dict[str, object]:
    authority = PreactivityAuthority(); batch = TestNativeBatch(width, authority); rows = _rollout_rows(width, steps)
    started = time.perf_counter(); output = batch.rollout(rows); elapsed = time.perf_counter() - started
    digest = hashlib.sha256()
    for key in ("service", "terminal", "tick", "protocol_bytes", "total_energy"):
        digest.update(np.ascontiguousarray(output[key]).tobytes())
    scripts = batch.scripted_actions()
    return {
        "width": width, "steps": steps, "lane_ticks": width * steps,
        "wall_seconds": elapsed, "lane_ticks_per_second": width * steps / elapsed,
        "output_sha256": digest.hexdigest(), "script_rows": int(scripts.size),
        "all_finite": bool(np.isfinite(output["actor"]).all() and np.isfinite(output["critic"]).all()),
    }


def _native_training_fragments() -> tuple[dict[str, torch.Tensor], dict[str, object]]:
    """Connect one exact 4096-transition native host rollout to PPO replay."""

    width, steps = 32, 128
    rows = _rollout_rows(width, steps)
    batch = TestProtocolNativeBatch(width, PreactivityAuthority())
    rows["prepare"] = 1; rows["commit"] = 1; rows["promotion_alpha"] = 1.0
    output = batch.rollout(rows)

    def fragment(value: np.ndarray) -> np.ndarray:
        return np.ascontiguousarray(value.transpose(1, 0, *range(2, value.ndim)).reshape(64, 64, *value.shape[2:]))

    observation_np = fragment(output["actor"])
    critic_np = np.ascontiguousarray(output["critic"].transpose(1, 0, 2).reshape(4_096, 58))
    renew_np = fragment(output["renew"]).astype(bool)
    terminal_lane_tick = np.ascontiguousarray(output["terminal"].T)
    action_np = fragment(rows["raw_action"])
    prepare_np = fragment(rows["prepare"][:, :, 0]).astype(np.float32)
    commit_np = fragment(rows["commit"][:, :, 0]).astype(np.float32)
    service_lane_tick = np.ascontiguousarray(output["service"].T).astype(np.float32)
    actor_flat = observation_np.reshape(4_096, 4, 54)
    snapshot_np = fragment(output["snapshot_payload"])
    snapshot_mask_np = fragment(output["snapshot_delivery_mask"]).astype(bool)
    promotion_np = fragment(output["cas_applied"]).astype(bool)
    reset_np = np.ones((64, 64), dtype=np.float32)
    reset_np[terminal_lane_tick.reshape(64, 64).astype(bool)] = 0.0
    target_np = critic_np[:, :4].copy()
    links_np = fragment(output["readiness_candidate"]).reshape(4_096, 2)
    missing_np = actor_flat[:, 0, 14].copy()
    q_np = np.repeat((service_lane_tick.T.reshape(4_096, 1) > 0).astype(np.float32), 20, axis=1)
    fragments = {
        "observation": torch.from_numpy(observation_np).to(torch.float32),
        "critic": torch.from_numpy(critic_np).to(torch.float32),
        "snapshot": torch.from_numpy(snapshot_np).to(torch.float32),
        "snapshot_mask": torch.from_numpy(snapshot_mask_np),
        "promotion_mask": torch.from_numpy(promotion_np),
        "promotion_alpha": torch.ones((64, 64), dtype=torch.float32),
        "reset_mask": torch.from_numpy(reset_np),
        "renew": torch.from_numpy(renew_np),
        "prepare_mask": torch.from_numpy(renew_np),
        "commit_mask": torch.from_numpy(renew_np & fragment(output["version_match"]).astype(bool)),
        "action": torch.from_numpy(action_np).to(torch.float32),
        "prepare_outcome": torch.from_numpy(prepare_np),
        "commit_outcome": torch.from_numpy(commit_np),
        "reward": torch.from_numpy(service_lane_tick),
        "done": torch.from_numpy(terminal_lane_tick.astype(np.float32)),
        "target": torch.from_numpy(target_np).to(torch.float32),
        "links": torch.from_numpy(links_np).to(torch.float32),
        "missing": torch.from_numpy(missing_np).to(torch.float32),
        "q_labels": torch.from_numpy(q_np),
    }
    identity = hashlib.sha256()
    for name in sorted(output):
        identity.update(name.encode("ascii") + b"\0")
        identity.update(np.ascontiguousarray(output[name]).tobytes())
    return fragments, {
        "schema": "DISH_RBHR_R05_NATIVE_CONNECTED_FRAGMENT_BINDING_V1",
        "native_ticks": width * steps, "fragments": 64, "ticks_per_fragment": 64,
        "physical_controller_copies": 4, "source_sha256": identity.hexdigest(),
        "test_only": True, "question_relevant_output": False,
    }


def run_native_connected_training_seam() -> dict[str, object]:
    fragments, binding = _native_training_fragments()
    result = run_full_4096_dry_update(
        fragments=fragments, source_label="CPP20_NATIVE_PROTOCOL_TEST_ROLLOUT",
    )
    result["native_fragment_binding"] = binding
    return result


def run_native_connected_analyzer_acceptance() -> dict[str, object]:
    width, steps = 16, 1_200
    batch = TestNativeBatch(width, PreactivityAuthority())
    native_rows = batch.rollout(_rollout_rows(width, steps))
    return run_native_connected_analyzer_seam(native_rows)


def _real_component_payloads(
    repository_root: Path,
    *,
    native: dict[str, object],
    training: dict[str, object],
    candidate_accounting: dict[str, object],
    analyzer: dict[str, object],
    estimands: dict[str, object],
    wire: dict[str, object],
) -> dict[str, bytes]:
    science_bytes = b"".join((science_root(repository_root) / name).read_bytes() for name, _ in SCIENCE_FILES)
    source_paths = (
        Path(__file__), Path(__file__).with_name("production_backend.py"),
        Path(__file__).with_name("production_training.py"),
        Path(__file__).with_name("production_analysis.py"),
        Path(__file__).with_name("production_protocol.py"),
        Path(__file__).with_name("native") / "rbhr_production_backend.cpp",
    )
    source_bytes = b"".join(path.read_bytes() for path in source_paths)
    native_bytes = Path(str(native["artifact"])).read_bytes()

    def encoded(value: object) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")

    payloads = {
        "science_composite": science_bytes,
        "production_source": source_bytes,
        "native_artifact": native_bytes,
        "model": encoded({"state_sha256": training["model_state_sha256"]}),
        "optimizer": encoded({"state_sha256": training["optimizer_state_sha256"]}),
        "actor_welford": encoded({"count": training["welford_counts"]["actor"]}),
        "snapshot_welford": encoded({"count": training["welford_counts"]["snapshot"]}),
        "critic_welford": encoded({"count": training["welford_counts"]["critic"]}),
        "rng_frontier": encoded(training["native_fragment_binding"]),
        "accepted_tape_frontier": encoded(candidate_accounting),
        "fork_frontier": encoded({"schema": "TEST_REAL_SHAM_FRONTIER_V1", "wire": wire["sha256"]}),
        "reducer_frontier": encoded(estimands),
        "analyzer_frontier": encoded(analyzer),
    }
    if tuple(sorted(payloads)) != tuple(sorted(BINDING_COMPONENTS)):
        raise PreactivityAcceptanceError("real component payload inventory differs")
    return payloads


def _storage_projection(checkpoint_bytes: int) -> dict[str, object]:
    jobs = BLOCKS * len(ARMS)
    plan = BlindedFrontierPlan()
    checkpoint_generation_write_bytes = checkpoint_bytes * jobs * plan.resume_generations_per_job
    final_checkpoint_bytes = checkpoint_bytes * jobs
    inventory = complete_inventory()
    frontier_metadata_bytes = int(768 * jobs * plan.resume_generations_per_job)
    tape_audit_bytes = int(inventory["accepted_tapes"]) * 160
    compact_evaluation_bytes = int(inventory["evaluation_episodes"]) * 512
    compact_fork_bytes = int(inventory["fork_pairs_max"]) * 2 * 384
    hypothesis = complete_hypothesis_inventory()["total"]
    analyzer_scratch_bytes = 512 * 24 * 256 * 8 + 99_999 * 8 + 24 * hypothesis * 8
    measured_io_bytes = (
        2 * checkpoint_generation_write_bytes + final_checkpoint_bytes
        + frontier_metadata_bytes + tape_audit_bytes + compact_evaluation_bytes
        + compact_fork_bytes + analyzer_scratch_bytes
    )
    durable_bytes = final_checkpoint_bytes + frontier_metadata_bytes + tape_audit_bytes + compact_evaluation_bytes + compact_fork_bytes
    scratch_bytes = max(8 * checkpoint_bytes * 2, analyzer_scratch_bytes, 240 * 1_200 * (2_280 + 192))
    return {
        "jobs": jobs,
        "checkpoint_stride_updates": plan.checkpoint_stride_updates,
        "resume_generations_per_job": plan.resume_generations_per_job,
        "checkpoint_generation_write_gib": checkpoint_generation_write_bytes / (1024**3),
        "checkpoint_generation_write_plus_one_resume_read_gib": 2 * checkpoint_generation_write_bytes / (1024**3),
        "final_checkpoint_durable_gib": final_checkpoint_bytes / (1024**3),
        "frontier_metadata_gib": frontier_metadata_bytes / (1024**3),
        "accepted_tape_audit_gib": tape_audit_bytes / (1024**3),
        "compact_evaluation_rows_gib": compact_evaluation_bytes / (1024**3),
        "compact_fork_rows_gib": compact_fork_bytes / (1024**3),
        "analyzer_scratch_gib": analyzer_scratch_bytes / (1024**3),
        "measured_formula_total_io_gib": measured_io_bytes / (1024**3),
        "measured_formula_durable_gib": durable_bytes / (1024**3),
        "measured_formula_scratch_gib": scratch_bytes / (1024**3),
        "baseline_planning_projection_only": dict(BASELINE_PLANNING_PROJECTION),
    }


def _component_projection(
    *, rollout: dict[str, object], training: dict[str, object], analyzer: dict[str, object],
    scanner: dict[str, object],
) -> dict[str, object]:
    inventory = complete_inventory()
    throughput = float(rollout["lane_ticks_per_second"])
    known_native_ticks = (
        int(inventory["training_transitions"]) + int(inventory["evaluation_ticks"])
        + int(inventory["accepted_advantage_branch_ticks"])
        + int(inventory["recovery_witness_ticks"]) + int(inventory["fork_ticks_max"])
        + int(inventory["candidate_slots"]) * 1_200
    )
    known_native_cpu_hours = known_native_ticks / throughput / 3_600.0
    full_updates = int(inventory["training_jobs"]) * int(inventory["updates_per_job"])
    replay_cpu_hours = float(training["wall_seconds"]) * full_updates / 3_600.0
    hypotheses = complete_hypothesis_inventory()["total"]
    analyzer_cpu_hours = float(analyzer["wall_seconds"]) * hypotheses / int(analyzer["estimands"]) / 3_600.0
    lower_bound = known_native_cpu_hours + replay_cpu_hours + analyzer_cpu_hours
    seconds_per_rejected_candidate = 1.0 / float(scanner["attempts_per_second"])
    remaining_cpu_seconds = max(0.0, HIGH_GATES["cpu_core_hours"] * 3_600.0 - lower_bound * 3_600.0)
    max_rejected_before_cpu_gate = int(remaining_cpu_seconds / seconds_per_rejected_candidate)
    return {
        "formula": "known_native_ticks/native_lane_ticks_per_second + full_updates*native_connected_4096_update_seconds + analyzer_seconds_per_estimand*6990 + rejected_candidate_attempts/measured_native_scanner_attempts_per_second",
        "known_native_ticks_excluding_rejected_candidates": known_native_ticks,
        "native_lane_ticks_per_second": throughput,
        "known_native_cpu_hours": known_native_cpu_hours,
        "full_dry_update_seconds": float(training["wall_seconds"]),
        "full_updates": full_updates,
        "recurrent_replay_backward_cpu_hours": replay_cpu_hours,
        "hypothesis_count": hypotheses,
        "analyzer_cpu_hours_linear_projection": analyzer_cpu_hours,
        "cpu_core_hours_lower_bound_excluding_rejected_candidates": lower_bound,
        "seconds_per_rejected_candidate_attempt_at_measured_native_rate": seconds_per_rejected_candidate,
        "rejected_candidate_attempt_count": "UNKNOWN_BEFORE_VALUE_BLIND_MASTER",
        "max_rejected_candidate_attempts_before_560_cpu_hour_gate": max_rejected_before_cpu_gate,
        "max_mean_rejected_attempts_per_accepted_slot_before_560_cpu_hour_gate": max_rejected_before_cpu_gate / int(inventory["candidate_slots"]),
        "candidate_attempt_cap_worst_case_cpu_hours": int(inventory["candidate_attempts_max"]) * seconds_per_rejected_candidate / 3_600.0,
        "cpu_gate_status": "INDETERMINATE_UNTIL_CANDIDATE_REJECTION_COUNT_IS_BOUND",
    }


def run_preactivity_acceptance(repository_root: Path, *, widths: Iterable[int] = (32, 48, 240)) -> dict[str, object]:
    rss_before = _rss_bytes(); io_before = process_io_bytes(os.getpid()); started = time.perf_counter()
    science = verify_science_composite(repository_root)
    native = artifact_identity()
    rng_words = rng_words_test_native(
        (
            "DISH/RBHR/R05/INIT/NONE/TRAIN/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/PARAMETER_UNIFORM/0",
            "DISH/RBHR/R05/INFERENCE/NONE/BOOTSTRAP/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/NONE/1/BOOTSTRAP_BLOCK/0",
        ),
        PreactivityAuthority(),
    )
    rollouts = [benchmark_native_rollout(int(width), steps=1_200) for width in widths]
    training = run_native_connected_training_seam()
    analyzer = run_result_blind_analyzer_seam()
    native_analyzer = run_native_connected_analyzer_acceptance()
    estimand_manifest = estimand_manifest_identity()
    estimand_sources = complete_estimand_source_manifest()
    candidate_accounting = candidate_accounting_identity()
    wire = test_wire_fixture_inventory()
    native_wire = native_protocol_audit()
    native_transition = native_protocol_transition_probe()
    native_natural_trace = native_natural_protocol_trace()
    if native_wire["wire_sizes"] != [40, 64, 64, 96, 48, 32, 32, 24]:
        raise PreactivityAcceptanceError("native wire sizes differ from the frozen protocol")
    scan_started = time.perf_counter()
    scanner_rows = scan_test_candidate_attempts(48, PreactivityAuthority())
    scanner_elapsed = time.perf_counter() - scan_started
    clear_scan_started = time.perf_counter()
    clear_scanner_rows = scan_test_candidate_attempts(
        48, PreactivityAuthority(), clear_channel_fixture=True,
    )
    clear_scanner_elapsed = time.perf_counter() - clear_scan_started
    scanner = {
        "schema": "DISH_RBHR_R05_NATIVE_TEST_CANDIDATE_SCANNER_V1",
        "attempts": int(scanner_rows.size),
        "eligible": int(np.count_nonzero(scanner_rows["eligible"])),
        "positive": int(np.count_nonzero(scanner_rows["stratum"] == 1)),
        "near_zero": int(np.count_nonzero(scanner_rows["stratum"] == 0)),
        "negative": int(np.count_nonzero(scanner_rows["stratum"] == -1)),
        "intermediate_or_ineligible": int(np.count_nonzero(scanner_rows["stratum"] == 2)),
        "ordinary_window_opportunities_checked": int(scanner_rows["opportunities_checked"].sum()),
        "aggregate_rejection_mask": int(np.bitwise_or.reduce(scanner_rows["rejection_mask"], initial=0)),
        "wall_seconds": scanner_elapsed,
        "attempts_per_second": float(scanner_rows.size / scanner_elapsed),
        "test_only": True, "scientific_master": False, "coordinate": False,
        "question_relevant_output": False,
        "native_scanner_complete": True,
        "controlled_clear_channel_fixture": {
            "attempts": int(clear_scanner_rows.size),
            "eligible": int(np.count_nonzero(clear_scanner_rows["eligible"])),
            "positive": int(np.count_nonzero(clear_scanner_rows["stratum"] == 1)),
            "near_zero": int(np.count_nonzero(clear_scanner_rows["stratum"] == 0)),
            "negative": int(np.count_nonzero(clear_scanner_rows["stratum"] == -1)),
            "intermediate_or_ineligible": int(np.count_nonzero(clear_scanner_rows["stratum"] == 2)),
            "wall_seconds": clear_scanner_elapsed,
            "attempts_per_second": float(clear_scanner_rows.size / clear_scanner_elapsed),
            "projection_authority": False,
        },
    }
    with tempfile.TemporaryDirectory(prefix="dish-rbhr-r05-production-preactivity-") as temporary:
        temporary_root = Path(temporary)
        lifecycle = run_result_blind_lifecycle_seam(temporary_root / "opaque", int(training["checkpoint_resume_bytes"]))
        real_lifecycle = run_real_byte_lifecycle_seam(
            temporary_root / "real",
            _real_component_payloads(
                repository_root, native=native, training=training,
                candidate_accounting=candidate_accounting, analyzer=analyzer,
                estimands=estimand_sources, wire=wire,
            ),
        )
        measured_lifecycle_disk_bytes = sum(path.stat().st_size for path in temporary_root.rglob("*") if path.is_file())
    storage = _storage_projection(int(training["checkpoint_resume_bytes"]))
    projection = _component_projection(rollout=rollouts[0], training=training, analyzer=analyzer, scanner=scanner)
    rss_after = _rss_bytes()
    io_after = process_io_bytes(os.getpid())
    io_delta = {name: io_after[name] - io_before[name] for name in io_before}
    if native.get("full_reset_step_cpp") is not True or native.get("python_environment_fallback") is not False:
        raise PreactivityAcceptanceError("native-first production boundary differs")
    return {
        "schema": "DISH_RBHR_R05_PRODUCTION_PREACTIVITY_ACCEPTANCE_V1",
        "namespace": PREACTIVITY_NAMESPACE,
        "test_only": True,
        "scientific_master": False,
        "coordinate": False,
        "lease": False,
        "scientific_model_or_checkpoint": False,
        "production_training_or_evaluation": False,
        "question_relevant_output": False,
        "science_composite": science,
        "inventory": complete_inventory(),
        "native": native,
        "native_rng_address_measurement": {
            "request_count": len(rng_words),
            "words_sha256": hashlib.sha256(np.asarray(rng_words, dtype=">u8").tobytes()).hexdigest(),
            "master_class": "TEST_ONLY_256_BIT_NONSCIENTIFIC",
        },
        "rollout_measurements": rollouts,
        "training_measurement": training,
        "analyzer_measurement": analyzer,
        "native_connected_analyzer_measurement": native_analyzer,
        "estimand_identity_manifest": estimand_manifest,
        "estimand_source_manifest": estimand_sources,
        "candidate_accounting_manifest": candidate_accounting,
        "native_candidate_scanner_measurement": scanner,
        "wire_protocol_measurement": wire,
        "native_wire_protocol_measurement": native_wire,
        "native_protocol_transition_measurement": native_transition,
        "native_natural_protocol_trace": native_natural_trace,
        "lifecycle_measurement": lifecycle,
        "real_byte_lifecycle_measurement": real_lifecycle,
        "measured_lifecycle_disk_bytes": measured_lifecycle_disk_bytes,
        "process_io_delta": io_delta,
        "storage_measurement": storage,
        "process_rss_before_bytes": rss_before,
        "process_rss_after_bytes": rss_after,
        "process_rss_observed_max_bytes": max(rss_before, rss_after),
        "high_gates": dict(HIGH_GATES),
        "measured_component_projection": projection,
        "baseline_planning_projection_only": dict(BASELINE_PLANNING_PROJECTION),
        "high_gate_pass": False,
        "high_gate_status": "NOT_ESTABLISHED_CANDIDATE_REJECTION_DISTRIBUTION_PENDING",
        "gpu_required": False,
        "native_first": True,
        "python_environment_or_rollout_fallback": False,
        "selected_worker_plan": {"workers": 8, "torch_threads_per_worker": 1, "native_rollout_batched": True},
        "dominant_bottleneck": "batched current-parameter recurrent replay/backward; native reset-step rollout is not dominant",
        "wall_seconds": time.perf_counter() - started,
    }


__all__ = [
    "BASELINE_PLANNING_PROJECTION", "HIGH_GATES", "PreactivityAcceptanceError",
    "benchmark_native_rollout", "process_io_bytes", "process_memory_bytes", "run_native_connected_training_seam",
    "run_native_connected_analyzer_acceptance", "run_preactivity_acceptance", "verify_science_composite",
]
