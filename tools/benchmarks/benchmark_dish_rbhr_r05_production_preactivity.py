"""Result-blind production preactivity benchmark for DISH RBHR r05."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import time

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_preactivity import (
    HIGH_GATES,
    _rss_bytes,
    benchmark_native_rollout,
    process_io_bytes,
    process_memory_bytes,
    run_native_connected_training_seam,
    run_preactivity_acceptance,
)


def _worker(_: int) -> dict[str, object]:
    return benchmark_native_rollout(32, steps=512)


def native_worker_sweep() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for workers in (1, 2, 4, 8):
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as executor:
            rows = list(executor.map(_worker, range(workers)))
        elapsed = time.perf_counter() - started
        lane_ticks = sum(int(row["lane_ticks"]) for row in rows)
        results.append({
            "workers": workers,
            "complete_native_units": workers,
            "wall_seconds": elapsed,
            "lane_ticks": lane_ticks,
            "aggregate_lane_ticks_per_second": lane_ticks / elapsed,
            "all_finite": all(bool(row["all_finite"]) for row in rows),
            "unit_digests": [str(row["output_sha256"]) for row in rows],
        })
    return results


def _training_worker(_: int) -> dict[str, object]:
    value = run_native_connected_training_seam()
    return {"wall_seconds": value["wall_seconds"], "rss_bytes": _rss_bytes(), "checkpoint_resume_bytes": value["checkpoint_resume_bytes"]}


def training_worker_sweep() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    baseline = None
    for workers in (1, 2, 4, 8):
        started = time.perf_counter()
        with ProcessPoolExecutor(max_workers=workers) as executor:
            rows = list(executor.map(_training_worker, range(workers)))
        elapsed = time.perf_counter() - started
        if baseline is None:
            baseline = elapsed
        results.append({
            "workers": workers,
            "complete_full_4096_update_units": workers,
            "wall_seconds": elapsed,
            "effective_throughput_speedup": workers * baseline / elapsed,
            "aggregate_child_rss_bytes": sum(int(row["rss_bytes"]) for row in rows),
            "worker_update_wall_seconds": [float(row["wall_seconds"]) for row in rows],
            "checkpoint_resume_bytes": sorted({int(row["checkpoint_resume_bytes"]) for row in rows}),
        })
    return results


def _held_full_chain_worker(index: int, connection, release) -> None:
    try:
        io_before = process_io_bytes(os.getpid())
        started = time.perf_counter()
        rollout = benchmark_native_rollout(32, steps=1_200)
        training = run_native_connected_training_seam()
        io_after = process_io_bytes(os.getpid())
        connection.send({
            "index": index,
            "pid": os.getpid(),
            "rollout_lane_ticks": rollout["lane_ticks"],
            "training_transitions": training["transitions"],
            "wall_seconds": time.perf_counter() - started,
            "io_delta": {name: io_after[name] - io_before[name] for name in io_before},
        })
        release.wait(60.0)
    except BaseException as error:  # pragma: no cover - child failure is surfaced in parent evidence
        connection.send({"index": index, "pid": os.getpid(), "error": f"{type(error).__name__}: {error}"})
    finally:
        connection.close()


def simultaneous_process_group_rss_canary(workers: int = 8) -> dict[str, object]:
    """Hold all production-chain children live and measure parent+children together."""

    context = multiprocessing.get_context("spawn")
    release = context.Event()
    children = []
    parents = []
    for index in range(workers):
        parent_connection, child_connection = context.Pipe(duplex=False)
        process = context.Process(target=_held_full_chain_worker, args=(index, child_connection, release))
        process.start(); child_connection.close()
        children.append(process); parents.append(parent_connection)
    try:
        rows = []
        for connection in parents:
            if not connection.poll(60.0):
                raise RuntimeError("simultaneous RSS canary child did not reach the hold barrier")
            row = connection.recv()
            if "error" in row:
                raise RuntimeError(str(row["error"]))
            rows.append(row)
        parent = process_memory_bytes(os.getpid())
        child_memory = [process_memory_bytes(int(row["pid"])) for row in rows]
        current_bytes = parent["current"] + sum(row["current"] for row in child_memory)
        peak_bytes_sum = parent["peak"] + sum(row["peak"] for row in child_memory)
        return {
            "workers": workers,
            "all_processes_live_at_measurement": all(process.is_alive() for process in children),
            "parent_current_rss_bytes": parent["current"],
            "child_current_rss_bytes": [row["current"] for row in child_memory],
            "simultaneous_parent_plus_children_current_rss_bytes": current_bytes,
            "simultaneous_parent_plus_children_current_rss_gib": current_bytes / (1024**3),
            "parent_plus_child_individual_peak_rss_bytes_sum": peak_bytes_sum,
            "parent_plus_child_individual_peak_rss_gib_sum": peak_bytes_sum / (1024**3),
            "worker_chain": rows,
        }
    finally:
        release.set()
        for connection in parents:
            connection.close()
        for process in children:
            process.join(timeout=30.0)
            if process.is_alive():
                process.terminate(); process.join(timeout=10.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository_root = Path(__file__).resolve().parents[2]
    process_started = time.process_time(); wall_started = time.perf_counter(); io_started = process_io_bytes(os.getpid())
    acceptance = run_preactivity_acceptance(repository_root)
    native_workers = native_worker_sweep()
    training_workers = training_worker_sweep()
    process_group_rss = simultaneous_process_group_rss_canary()
    projection = dict(acceptance["measured_component_projection"])
    selected = training_workers[-1]
    speedup = float(selected["effective_throughput_speedup"])
    cpu_lower = float(projection["cpu_core_hours_lower_bound_excluding_rejected_candidates"])
    wall_lower = cpu_lower / speedup
    process_group_rss_gib = float(process_group_rss["simultaneous_parent_plus_children_current_rss_gib"])
    storage = acceptance["storage_measurement"]
    measured_projection = {
        "cpu_core_hours_lower_bound_excluding_rejected_candidates": cpu_lower,
        "wall_hours_lower_bound_excluding_rejected_candidates": wall_lower,
        "measured_eight_worker_speedup": speedup,
        "measured_process_group_rss_gib": process_group_rss_gib,
        "measured_formula_scratch_gib": storage["measured_formula_scratch_gib"],
        "measured_formula_durable_gib": storage["measured_formula_durable_gib"],
        "measured_formula_total_io_gib": storage["measured_formula_total_io_gib"],
        "rejected_candidate_attempt_count": "UNKNOWN_BEFORE_VALUE_BLIND_MASTER",
        "cpu_formula": projection["formula"],
        "wall_formula": "cpu_formula / measured_eight_worker_effective_throughput_speedup",
        "exact_high_gates": dict(HIGH_GATES),
        "high_gate_pass": False,
        "high_gate_status": "NOT_ESTABLISHED_CANDIDATE_REJECTION_DISTRIBUTION_PENDING",
    }
    io_finished = process_io_bytes(os.getpid())
    payload = {
        "schema": "DISH_RBHR_R05_PRODUCTION_PREACTIVITY_BENCHMARK_V4",
        "test_only": True,
        "scientific_master": False,
        "coordinate": False,
        "lease": False,
        "scientific_model_or_checkpoint": False,
        "production_training_or_evaluation": False,
        "question_relevant_output": False,
        "acceptance": acceptance,
        "native_worker_sweep": native_workers,
        "full_4096_update_process_worker_sweep": training_workers,
        "simultaneous_process_group_rss_canary": process_group_rss,
        "measured_full_chain_projection": measured_projection,
        "process_cpu_seconds": time.process_time() - process_started,
        "parent_process_io_delta": {name: io_finished[name] - io_started[name] for name in io_started},
        "held_worker_io_delta_sum": {
            name: sum(int(row["io_delta"][name]) for row in process_group_rss["worker_chain"])
            for name in io_started
        },
        "wall_seconds": time.perf_counter() - wall_started,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(json.dumps({
        "output": str(args.output),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "high_gate_pass": measured_projection["high_gate_pass"],
        "high_gate_status": measured_projection["high_gate_status"],
        "wall_seconds": payload["wall_seconds"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
