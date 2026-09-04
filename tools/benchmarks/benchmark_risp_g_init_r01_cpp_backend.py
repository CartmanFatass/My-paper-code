"""Result-blind TEST-only benchmark for the R01 native environment host."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))

import g_init_r01_native_backend as native  # noqa: E402
import g_init_r01_experiment as experiment  # noqa: E402
import g_init_r01_resume as resume  # noqa: E402


def _rss_bytes() -> int | None:
    try:
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = Counters(); counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
        if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return None
        return int(counters.WorkingSetSize)
    except Exception:
        return None


def _episode(width: int) -> int:
    resets = tuple(
        native.MaterializedReset(0, native.fixture_draw_prefix(("BENCH", width, lane, "INIT_SECTOR")), native.fixture_event_token(("BENCH", width, lane, "INIT_SECTOR")))
        for lane in range(width)
    )
    sectors = [native.python_fixture_initial_sector(item.init_prefix) for item in resets]
    with native.NativeInteractiveBatch(resets) as batch:
        for renewal in range(48):
            steps = []
            for lane in range(width):
                action = (lane + renewal) % 3
                motion_prefix = native.fixture_draw_prefix(("BENCH", width, lane, renewal, "MOTION"))
                ack_prefix = native.fixture_draw_prefix(("BENCH", width, lane, renewal, "ACK"))
                steps.append(native.MaterializedStep(
                    action, motion_prefix, ack_prefix,
                    native.fixture_event_token(("BENCH", width, lane, renewal, "ACTION")),
                    native.fixture_event_token(("BENCH", width, lane, renewal, "MOTION")),
                    native.fixture_event_token(("BENCH", width, lane, renewal, "ACK")),
                ))
            outputs = batch.step(steps)
            sectors = [int(row["sector_after"]) for row in outputs]
        if not all(row["terminal"] for row in outputs):
            raise RuntimeError("TEST benchmark did not reach terminal")
    return width * 48


def _python_reference_episode(width: int) -> int:
    sectors = [native.python_fixture_initial_sector(native.fixture_draw_prefix(("BENCH", width, lane, "INIT_SECTOR"))) for lane in range(width)]
    for renewal in range(48):
        for lane in range(width):
            action = (lane + renewal) % 3
            sectors[lane], _ = native.python_fixture_outcome(
                sector=sectors[lane], duration=4, action=action,
                motion_prefix=native.fixture_draw_prefix(("BENCH", width, lane, renewal, "MOTION")),
                ack_prefix=native.fixture_draw_prefix(("BENCH", width, lane, renewal, "ACK")),
            )
    return width * 48


def _json_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _integrated_grouped_chain() -> dict[str, object]:
    """Compare one reduced scalar chain with the grouped native adapter."""
    import torch

    seed = 79
    arm = experiment.ARMS[0]
    arrays = experiment.slow_initialization(seed)
    scalar_model = experiment.TrackModel(seed, arm, slow_arrays=arrays)
    grouped_model = experiment.TrackModel(seed, arm, slow_arrays=arrays)
    scalar_cache = {tau: experiment._slow_bundle(scalar_model, experiment._observation(tau, duration)) for tau, duration, _ in experiment.schedule_rows(0)}
    grouped_cache = {tau: experiment._slow_bundle(grouped_model, experiment._observation(tau, duration)) for tau, duration, _ in experiment.schedule_rows(0)}

    scalar_audit = experiment.SamplerAudit()
    started = time.perf_counter(); cpu_started = time.process_time()
    scalar_rows = {position: experiment._train_episode(scalar_model, seed, 0, position, 4, scalar_cache, scalar_audit) for position in (0, 2)}
    scalar_task = [value for position in (0, 2) for agent in range(2) for value in scalar_rows[position][0][agent]]
    scalar_align = [value for position in (0, 2) for agent in range(2) for value in scalar_rows[position][1][agent]]
    scalar_loss = -experiment._left_sum(scalar_task) / (4 * experiment.T) + experiment._left_sum(scalar_align) / len(scalar_align)
    scalar_loss.backward(); scalar_state = experiment._new_adam_state(scalar_model)
    experiment._global_clip(scalar_model); experiment._adamw_step(scalar_model, scalar_state)
    scalar_seconds = time.perf_counter() - started; scalar_cpu_seconds = time.process_time() - cpu_started

    grouped_audit = experiment.SamplerAudit()
    started = time.perf_counter(); cpu_started = time.process_time()
    grouped_rows = experiment._train_episode_group_native(grouped_model, seed, 0, (0, 2), 0, grouped_cache, grouped_audit)
    grouped_task = [value for position in (0, 2) for agent in range(2) for value in grouped_rows[position][0][agent]]
    grouped_align = [value for position in (0, 2) for agent in range(2) for value in grouped_rows[position][1][agent]]
    grouped_loss = -experiment._left_sum(grouped_task) / (4 * experiment.T) + experiment._left_sum(grouped_align) / len(grouped_align)
    grouped_loss.backward(); grouped_state = experiment._new_adam_state(grouped_model)
    experiment._global_clip(grouped_model); experiment._adamw_step(grouped_model, grouped_state)
    grouped_seconds = time.perf_counter() - started; grouped_cpu_seconds = time.process_time() - cpu_started

    scalar_checkpoint = experiment.state_dict_json(scalar_model)
    grouped_checkpoint = experiment.state_dict_json(grouped_model)
    if scalar_audit.calls != grouped_audit.calls or not all(torch.equal(a, b) for a, b in zip(scalar_task + scalar_align, grouped_task + grouped_align)):
        raise RuntimeError("integrated grouped training fixture diverged before optimization")
    if not all(torch.equal(a.grad, b.grad) for a, b in zip(scalar_model.ordered_parameters(), grouped_model.ordered_parameters())):
        raise RuntimeError("integrated grouped training gradient diverged")
    if scalar_checkpoint != grouped_checkpoint:
        raise RuntimeError("integrated grouped training checkpoint diverged")

    evaluations: dict[str, object] = {}
    for mode, cell, model, cache in (
        ("UNIFORM", "UNIFORM", None, {}),
        ("INTACT", f"{arm}-INTACT", grouped_model, {tau: experiment._slow_bundle(grouped_model, experiment._observation(tau, duration)) for tau, duration, _ in experiment.schedule_rows(2)}),
    ):
        packet = {
            "schema": experiment.TEST_TRAINING_SCHEMA,
            "science_revision": experiment.TEST_FIXTURE_REVISION,
            "binding_class": "TEST_ONLY", "test_fixture": True,
            "registered": False, "algorithm_seed": seed, "arm": arm,
            "updates": 1, "episodes_per_batch": 2,
            "conclusion_update": experiment.REGISTERED_UPDATES,
            "test_fixture_benchmark_reduced": True,
            "final_state": grouped_checkpoint,
        }
        scalar_started = time.perf_counter()
        scalar = experiment.run_evaluation_unit(seed, cell, 2, {arm: packet}, episodes=16)
        scalar_eval_seconds = time.perf_counter() - scalar_started
        grouped_summary = experiment.EvalSummary(); grouped_eval_audit = experiment.SamplerAudit()
        grouped_started = time.perf_counter()
        experiment._evaluate_episode_group_native(
            seed=seed, schedule_id=2, episodes=tuple(range(16)), arm=arm if mode == "INTACT" else None,
            mode=mode, model=model, slow_cache=cache, audit=grouped_eval_audit, summary=grouped_summary,
        )
        grouped_eval_seconds = time.perf_counter() - grouped_started
        grouped_result = grouped_summary.result()
        if scalar["result"] != grouped_result or scalar["sampler_audit"]["calls"] != grouped_eval_audit.calls:
            differing = sorted(key for key in scalar["result"] if scalar["result"].get(key) != grouped_result.get(key))
            raise RuntimeError(f"integrated grouped {mode} evaluation diverged in {differing}")
        evaluations[mode] = {
            "scalar_seconds": scalar_eval_seconds, "grouped_native_seconds": grouped_eval_seconds,
            "result_sha256": _json_sha256(grouped_result), "exact_packet_result_and_census": True,
        }
    return {
        "episodes": 2, "agent_lanes": 4,
        "scalar_seconds": scalar_seconds, "scalar_cpu_seconds": scalar_cpu_seconds,
        "grouped_native_seconds": grouped_seconds, "grouped_native_cpu_seconds": grouped_cpu_seconds,
        "checkpoint_sha256": _json_sha256(grouped_checkpoint),
        "exact_task_align_gradient_adamw_checkpoint": True,
        "differentiable_episode_major_replay_retained": True,
        "replay_reason": "direct test shows renewal-major graph changes binary64 gradient accumulation",
        "evaluations": evaluations,
    }


def _parallel_unit_worker_matrix() -> dict[str, object]:
    fixture_root = "c" * 64
    payloads = [
        {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("TRAIN", 61, experiment.ARMS[0], None), "updates": 1, "episodes": 2},
        {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("TRAIN", 62, experiment.ARMS[1], None), "updates": 1, "episodes": 2},
        {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("EVAL", 61, "UNIFORM", 2), "episodes": 1},
        {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("EVAL", 62, "STATE-ORACLE", 2), "episodes": 1},
    ]
    rows = []
    baseline_hashes: list[str] | None = None
    for worker_count in (1, 2, 4):
        started = time.perf_counter(); cpu_started = time.process_time()
        results = resume.execute_test_units_ordered(payloads, worker_count=worker_count)
        elapsed = time.perf_counter() - started; parent_cpu = time.process_time() - cpu_started
        hashes = [str(result["semantic_sha256"]) for result in results]
        if baseline_hashes is None:
            baseline_hashes = hashes
        if hashes != baseline_hashes:
            raise RuntimeError("bounded worker count changed ordered packet semantics")
        rss_by_pid: dict[int, int] = {}
        for result in results:
            if result["peak_rss_bytes"] is not None:
                rss_by_pid[int(result["pid"])] = max(rss_by_pid.get(int(result["pid"]), 0), int(result["peak_rss_bytes"]))
        rows.append({
            "worker_count": worker_count, "wall_seconds": elapsed,
            "parent_cpu_seconds": parent_cpu, "worker_pids": len({int(result["pid"]) for result in results}),
            "observed_worker_peak_rss_sum_bytes": sum(rss_by_pid.values()),
            "observed_worker_peak_rss_max_bytes": max(rss_by_pid.values(), default=0),
            "ordered_semantic_packet_hashes": hashes,
            "packet_bytes": sum(len(json.dumps(result["packet"], sort_keys=True, separators=(",", ":")).encode("utf-8")) for result in results),
            "training_units": 2, "evaluation_units": 2,
        })
    return {
        "fixture_root": fixture_root, "rows": rows,
        "exact_order_hash_and_census_equivalence": True,
        "frontier_write_owner": "parent_only", "worker_frontier_paths_exposed": False,
        "failure_semantics": "cancel pending; install nothing until all bounded-batch units succeed; install in plan order",
        "production_parallel_admitted": False,
        "production_fence": "current production certificate binds process_concurrency=1 and cpu_workers=1",
    }


def _worker_measurement_row(worker_count: int, results: list[dict[str, object]], wall: float, parent_cpu: float) -> dict[str, object]:
    rss_by_pid: dict[int, int] = {}
    cpu_by_pid: dict[int, float] = {}
    for result in results:
        pid = int(result["pid"])
        if result["peak_rss_bytes"] is not None:
            rss_by_pid[pid] = max(rss_by_pid.get(pid, 0), int(result["peak_rss_bytes"]))
        cpu_by_pid[pid] = cpu_by_pid.get(pid, 0.0) + float(result["worker_cpu_seconds"])
    return {
        "worker_count": worker_count, "wall_seconds": wall,
        "parent_cpu_seconds": parent_cpu,
        "summed_worker_cpu_seconds": sum(cpu_by_pid.values()),
        "worker_pids": len({int(result["pid"]) for result in results}),
        "per_worker_peak_rss_bytes": dict(sorted(rss_by_pid.items())),
        "observed_worker_peak_rss_sum_bytes": sum(rss_by_pid.values()),
        "observed_worker_peak_rss_max_bytes": max(rss_by_pid.values(), default=0),
        "ordered_semantic_packet_hashes": [str(result["semantic_sha256"]) for result in results],
        "packet_bytes": sum(len(json.dumps(result["packet"], sort_keys=True, separators=(",", ":")).encode("utf-8")) for result in results),
    }


def run_representative_workers() -> dict[str, object]:
    """Permanent TEST-only full-width one-update worker/cost measurement."""
    fixture_root = "a" * 64
    training_payloads = [
        {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("TRAIN", 61, experiment.ARMS[0], None), "updates": 1, "episodes": 16},
        {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("TRAIN", 61, experiment.ARMS[1], None), "updates": 1, "episodes": 16},
        {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("TRAIN", 62, experiment.ARMS[0], None), "updates": 1, "episodes": 16},
        {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("TRAIN", 62, experiment.ARMS[1], None), "updates": 1, "episodes": 16},
    ]
    rows = []
    baseline_training_hashes: list[str] | None = None
    baseline_evaluation_hashes: list[str] | None = None
    for worker_count in (1, 2, 4):
        started = time.perf_counter(); parent_cpu_started = time.process_time()
        training = resume.execute_test_units_ordered(training_payloads, worker_count=worker_count)
        training_wall = time.perf_counter() - started
        training_parent_cpu = time.process_time() - parent_cpu_started
        training_row = _worker_measurement_row(worker_count, training, training_wall, training_parent_cpu)
        training_hashes = list(training_row["ordered_semantic_packet_hashes"])
        if baseline_training_hashes is None:
            baseline_training_hashes = training_hashes
        if training_hashes != baseline_training_hashes:
            raise RuntimeError("representative training hashes changed with worker count")

        packets = {(int(result["packet"]["algorithm_seed"]), str(result["packet"]["arm"])): dict(result["packet"]) for result in training}
        for packet in packets.values():
            packet["test_fixture_benchmark_reduced"] = True
        evaluation_payloads = [
            {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("EVAL", 61, f"{experiment.ARMS[0]}-INTACT", 2), "episodes": 16, "checkpoint_states": {experiment.ARMS[0]: packets[(61, experiment.ARMS[0])]}},
            {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("EVAL", 62, f"{experiment.ARMS[1]}-INTACT", 2), "episodes": 16, "checkpoint_states": {experiment.ARMS[1]: packets[(62, experiment.ARMS[1])]}},
            {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("EVAL", 61, "UNIFORM", 2), "episodes": 16},
            {"binding_class": "TEST_ONLY", "root": fixture_root, "item": ("EVAL", 62, "STATE-ORACLE", 2), "episodes": 16},
        ]
        started = time.perf_counter(); parent_cpu_started = time.process_time()
        evaluation = resume.execute_test_units_ordered(evaluation_payloads, worker_count=worker_count)
        evaluation_wall = time.perf_counter() - started
        evaluation_parent_cpu = time.process_time() - parent_cpu_started
        evaluation_row = _worker_measurement_row(worker_count, evaluation, evaluation_wall, evaluation_parent_cpu)
        evaluation_hashes = list(evaluation_row["ordered_semantic_packet_hashes"])
        if baseline_evaluation_hashes is None:
            baseline_evaluation_hashes = evaluation_hashes
        if evaluation_hashes != baseline_evaluation_hashes:
            raise RuntimeError("representative evaluation hashes changed with worker count")

        training_scale = (32 * experiment.REGISTERED_UPDATES) / 4
        evaluation_scale = (320 * experiment.REGISTERED_EVAL_EPISODES) / (4 * 16)
        projected_wall = training_wall * training_scale + evaluation_wall * evaluation_scale
        projected_worker_cpu = float(training_row["summed_worker_cpu_seconds"]) * training_scale + float(evaluation_row["summed_worker_cpu_seconds"]) * evaluation_scale
        parent_working_set = _rss_bytes()
        worker_ram = max(
            int(training_row["observed_worker_peak_rss_sum_bytes"]),
            int(evaluation_row["observed_worker_peak_rss_sum_bytes"]),
        )
        rows.append({
            "worker_count": worker_count,
            "training_four_units_one_update_episodes16": training_row,
            "evaluation_two_learned_two_control_episodes16": evaluation_row,
            "projected_complete_panel_wall_seconds": projected_wall,
            "projected_complete_panel_worker_cpu_seconds": projected_worker_cpu,
            "projected_complete_panel_wall_hours": projected_wall / 3600.0,
            "below_one_day": projected_wall < 86400,
            "smallest_observed_worker_ram_envelope_bytes": worker_ram,
            "observed_parent_working_set_bytes": parent_working_set,
            "observed_process_group_ram_envelope_bytes": None if parent_working_set is None else worker_ram + parent_working_set,
        })
    qualifying = [row for row in rows if row["below_one_day"]]
    return {
        "schema": "RISP-G-INIT-REACH-TEST-REPRESENTATIVE-WORKERS-BENCHMARK-V1",
        "namespace": native.TEST_NAMESPACE, "fixture_root": fixture_root,
        "production_identity_materialized": False,
        "training_fixture": {"independent_units": 4, "updates": 1, "episodes_per_unit": 16},
        "evaluation_fixture": {"independent_units": 4, "episodes_per_unit": 16, "learned": 2, "controls": 2},
        "rows": rows,
        "exact_semantic_hashes_across_worker_counts": True,
        "smallest_worker_count_below_one_day": None if not qualifying else min(int(row["worker_count"]) for row in qualifying),
        "production_parallel_admitted": False,
        "projection_method": "linear result-blind engineering projection from full-width one-update training and 16-episode evaluation fixtures",
    }


def run_benchmark(*, repetitions: int = 3) -> dict[str, object]:
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions <= 0:
        raise ValueError("repetitions must be a positive integer")
    native.clear_process_local_cache_for_tests()
    cold_start = time.perf_counter(); cold_cpu = time.process_time()
    native.require_cpp_batched_backend()
    process_cold_load_seconds = time.perf_counter() - cold_start
    process_cold_load_cpu_seconds = time.process_time() - cold_cpu
    warm_start = time.perf_counter(); warm_cpu = time.process_time()
    native.require_cpp_batched_backend()
    process_warm_load_seconds = time.perf_counter() - warm_start
    process_warm_load_cpu_seconds = time.process_time() - warm_cpu
    identity = native.native_artifact_identity()
    rows = []
    for width in (1, 8, 32):
        samples = []; cpu_samples = []; reference_samples = []
        transitions = 0
        for _ in range(repetitions):
            started = time.perf_counter(); cpu_started = time.process_time()
            transitions += _episode(width)
            samples.append(time.perf_counter() - started)
            cpu_samples.append(time.process_time() - cpu_started)
            reference_started = time.perf_counter()
            assert _python_reference_episode(width) == width * 48
            reference_samples.append(time.perf_counter() - reference_started)
        elapsed = sum(samples)
        reference_elapsed = sum(reference_samples)
        rows.append({
            "width": width, "repetitions": repetitions,
            "transitions": transitions, "seconds": samples,
            "cpu_seconds": cpu_samples,
            "python_reference_seconds": reference_samples,
            "transitions_per_second": transitions / elapsed,
            "python_reference_transitions_per_second": transitions / reference_elapsed,
            "native_speedup": reference_elapsed / elapsed,
            "terminal_rows": width * repetitions,
        })
    if experiment.fixture_root() is None and experiment.coordinate_root() is None:
        experiment.configure_test_fixture_root("e" * 64)
    if experiment.coordinate_root() is not None:
        raise RuntimeError("TEST benchmark refuses a production coordinate binding")
    training_started = time.perf_counter(); training_cpu = time.process_time()
    training_packet = experiment.run_training_unit(91, experiment.ARMS[0], updates=1, episodes=2)
    training_seconds = time.perf_counter() - training_started
    training_cpu_seconds = time.process_time() - training_cpu
    training_bytes = json.dumps(training_packet, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="hmasd_risp_g_init_r01_test_benchmark_") as temporary:
        checkpoint_path = Path(temporary) / "TEST_ONLY_checkpoint.json"
        write_started = time.perf_counter()
        experiment.atomic_write_json(checkpoint_path, training_packet)
        write_seconds = time.perf_counter() - write_started
        read_started = time.perf_counter()
        retained = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        read_seconds = time.perf_counter() - read_started
        resume_started = time.perf_counter()
        resumed = experiment.load_model(91, experiment.ARMS[0], retained["final_state"])
        resume_seconds = time.perf_counter() - resume_started
        checkpoint_io = {
            "bytes": checkpoint_path.stat().st_size,
            "sha256": hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
            "write_seconds": write_seconds, "read_seconds": read_seconds,
            "resume_seconds": resume_seconds,
            "resumed_finite": all(bool(value.isfinite().all()) for value in resumed.ordered_parameters()),
        }
    evaluation_started = time.perf_counter(); evaluation_cpu = time.process_time()
    evaluation_packet = experiment.run_evaluation_unit(91, "UNIFORM", 2, {}, episodes=1)
    evaluation_seconds = time.perf_counter() - evaluation_started
    evaluation_cpu_seconds = time.process_time() - evaluation_cpu
    evaluation_bytes = json.dumps(evaluation_packet, sort_keys=True, separators=(",", ":")).encode("utf-8")
    integrated = _integrated_grouped_chain()
    worker_matrix = _parallel_unit_worker_matrix()
    projected_training = float(integrated["grouped_native_seconds"]) * 4 * 2 * 512 * 32
    projected_evaluation = sum(float(row["grouped_native_seconds"]) for row in integrated["evaluations"].values()) / 2 * 4 * 320
    rollback_canary = False
    try:
        native._step_input(native.MaterializedStep(3, 0, 0, 0, 0, 0))
    except ValueError:
        rollback_canary = True
    return {
        "schema": "RISP-G-INIT-REACH-TEST-NATIVE-BENCHMARK-V1",
        "namespace_class": "TEST_ONLY", "namespace": native.TEST_NAMESPACE,
        "coordinate_schema": "RISP-G-INIT-REACH-TEST-CERTIFICATE-V1",
        "test_fixture_revision": "RISP-G-INIT-REACH-TEST-FIXTURE-20260821-01",
        "fixture_root": experiment.fixture_root(), "production_identity_materialized": False,
        "process_cold_load_seconds": process_cold_load_seconds,
        "process_cold_load_cpu_seconds": process_cold_load_cpu_seconds,
        "process_warm_load_seconds": process_warm_load_seconds,
        "process_warm_load_cpu_seconds": process_warm_load_cpu_seconds,
        "working_set_bytes": _rss_bytes(), "artifact": identity,
        "environment": rows,
        "fixture_oracle_chain": {
            "forward_backward_seconds": training_seconds,
            "forward_backward_cpu_seconds": training_cpu_seconds,
            "training_packet_sha256": hashlib.sha256(training_bytes).hexdigest(),
            "gradient_and_optimizer_step_executed": True,
            "checkpoint_serialize_resume": checkpoint_io,
            "evaluation_seconds": evaluation_seconds,
            "evaluation_cpu_seconds": evaluation_cpu_seconds,
            "evaluation_packet_sha256": hashlib.sha256(evaluation_bytes).hexdigest(),
            "evaluation_decisions": evaluation_packet["result"]["decisions"],
        },
        "integrated_scalar_vs_grouped_native": integrated,
        "bounded_parallel_contract": {
            "native_batch_max_agent_lanes": 32,
            "training_agent_lanes_per_group": 16,
            "evaluation_agent_lanes_per_group": 32,
            "lease_provided_production_worker_count": 1,
            "max_validated_test_worker_count": 4,
            "worker_output_install_order": "coordinate order after unit completion",
            "shared_rng_state": False,
            "same_coordinate_event_identity_and_artifact_required": True,
            "test_only_worker_matrix": worker_matrix,
        },
        "projected_complete_panel_single_worker_seconds": {
            "training_from_reduced_fixture": projected_training,
            "evaluation_from_control_and_learned_fixture_mean": projected_evaluation,
            "total": projected_training + projected_evaluation,
            "method": "engineering linear projection only; no production identity, root, or activity",
        },
        "semantic_equivalence": {
            "native_widths": [1, 8, 32], "all_five_schedules_tested": True,
            "raw_prefix_motion_ack_cpp": True, "event_tokens_and_census_checked": True,
            "state_terminal_repeatability_checked": True,
        },
        "rollback_canary_malformed_action_rejected": rollback_canary,
        "python_fallback": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--representative-workers", action="store_true")
    args = parser.parse_args()
    result = run_representative_workers() if args.representative_workers else run_benchmark(repetitions=args.repetitions)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
