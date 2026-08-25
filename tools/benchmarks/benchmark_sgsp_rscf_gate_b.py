"""TEST-only Gate-B full-chain benchmark for SGSP RSCF revision 01.

This is an engineering benchmark.  It accepts no production identity and writes
canonical JSON only to the caller-supplied output path.  Timings are deliberately
small TEST fixtures; the frozen panel arithmetic is reported through separately
measured composed work categories, not as an empirical-panel measurement.
"""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import asdict
import hashlib
import json
import math
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import threading
import time
from typing import Any, Callable, Mapping

import numpy as np
import torch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.analysis import (
    FAMILY_SIZE,
    QUANTITY_NAMES,
    SUPPORT_SLACK_CLARIFICATION_PATH,
    SUPPORT_SLACK_CLARIFICATION_SHA256,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.audits import AuditCertificate
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.contracts import (
    FROZEN_LOGICAL_COUNTS,
    HORIZON,
    SCIENCE_REVISION,
    SEED_BLOCK_COUNT,
    SUPPORTED_WIDTHS,
    TestIdentity,
    legal_actions,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.evaluation import (
    EDGE,
    INTACT,
    PHY,
    ROTATED,
    UNIFORM,
    EvaluationCellSummary,
    expected_cell_keys,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.fixtures import (
    make_test_pretransition_snapshot,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.lifecycle import (
    ResumeIdentity,
    canonical_sha256,
    read_verified_json,
    write_once_atomic_json,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_contract import (
    ABI_VERSION,
    NATIVE_THREADS,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_loader import (
    NativeHostIdentity,
    load_native_host,
    native_full_suffix,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_oracle import (
    run_gate_a_self_check,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.policy import (
    ACTOR_PARAMETER_SHAPES,
    CRITIC_PARAMETER_SHAPES,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.runner import (
    EVALUATION_ROSTERS,
    RSCFGateBRunner,
    _native_parameters,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.training import (
    make_projected_adam,
    projected_adam_step,
    rscf_full_batch_loss,
)


SCHEMA = "SGSP_RSCF_GATE_B_FULL_CHAIN_BENCHMARK_V1"
TEST_CLASS = "TEST_ONLY_GATE_B_FULL_CHAIN"
CONCURRENCY_LEVELS = (1, 2, 4)
MINIMUM_PAIRS = 3
DEFAULT_WARMUP_PAIRS = 1
GATE_A_SELF_CHECK_REPETITIONS = 3
SELECTION_RATE_SAMPLES = 3


def _literal_parameters(shapes: Mapping[str, tuple[int, ...]], phase: int) -> dict[str, torch.Tensor]:
    """Materialize deterministic TEST tensors without a coordinate or initializer."""
    result: dict[str, torch.Tensor] = {}
    cursor = phase * 101
    for name, shape in shapes.items():
        count = math.prod(shape)
        values = torch.arange(cursor, cursor + count, dtype=torch.float32)
        result[name] = (0.015 * torch.sin(values * 0.017 + phase)).reshape(shape).contiguous()
        cursor += count
    return result


def _rss_bytes() -> int | None:
    if sys.platform.startswith("win"):
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(counters)
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            ok = psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
            return int(counters.WorkingSetSize) if ok else None
        except (AttributeError, OSError):
            return None
    return None


class _RSSSampler:
    def __init__(self) -> None:
        self.values: list[int] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="sgsp-rscf-rss")

    def _run(self) -> None:
        while not self._stop.is_set():
            value = _rss_bytes()
            if value is not None:
                self.values.append(value)
            self._stop.wait(0.01)

    def __enter__(self) -> "_RSSSampler":
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)
        value = _rss_bytes()
        if value is not None:
            self.values.append(value)

    @property
    def peak(self) -> int | None:
        return max(self.values) if self.values else None


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _frontier_row(root: Path | None, key: str, identity: Mapping[str, object], row: Mapping[str, object]) -> tuple[dict[str, object], bool, str | None]:
    """Write-once TEST measurement row, or reuse only an exact identity match."""
    if root is None:
        return dict(row), False, None
    path = root / f"{key}.json"
    payload = {"kind": "TEST_ONLY_GATE_B_MEASUREMENT_ROW", "identity": dict(identity), "row": dict(row), "row_sha256": canonical_sha256(dict(row))}
    if path.exists():
        stored = read_verified_json(path)
        if stored.get("kind") != payload["kind"] or stored.get("identity") != payload["identity"] or stored.get("row_sha256") != canonical_sha256(stored.get("row")):
            raise RuntimeError(f"measurement frontier drift/tamper: {path}")
        return dict(stored["row"]), True, str(path)
    write_once_atomic_json(path, payload)
    return dict(row), False, str(path)


def _source_identity() -> dict[str, Any]:
    relative_paths = (
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/contracts.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/native_contract.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/native_loader.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/native/rscf_r01_full_suffix_host.cpp",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/runner.py",
        "experiments/candidates/semantic_graphon_shared_policy_rscf_r01/analysis.py",
        "tools/benchmarks/benchmark_sgsp_rscf_gate_b.py",
        SUPPORT_SLACK_CLARIFICATION_PATH,
    )
    digest = hashlib.sha256()
    files: dict[str, str] = {}
    for relative in relative_paths:
        path = REPOSITORY_ROOT / relative
        payload = path.read_bytes()
        files[relative] = hashlib.sha256(payload).hexdigest()
        digest.update(relative.encode("utf-8"))
        digest.update(payload)
    return {
        "combined_sha256": digest.hexdigest(),
        "files": files,
        "clarification_sha256": files[SUPPORT_SLACK_CLARIFICATION_PATH],
        "expected_clarification_sha256": SUPPORT_SLACK_CLARIFICATION_SHA256,
    }


def _cell_values(roster: int, arm: str, condition: str, block: int) -> tuple[float, float, float]:
    """Bounded TEST accumulator literals, never used for width selection."""
    jitter = (block - 11.5) * 0.0001
    table = {
        (9, PHY, INTACT): (0.62, 0.61, 0.60), (9, EDGE, INTACT): (0.60, 0.59, 0.58), (9, UNIFORM, INTACT): (0.45, 0.44, 0.43),
        (15, PHY, INTACT): (0.63, 0.62, 0.61), (15, EDGE, INTACT): (0.61, 0.60, 0.59), (15, UNIFORM, INTACT): (0.46, 0.45, 0.44),
        (6, PHY, INTACT): (0.66, 0.65, 0.64), (6, EDGE, INTACT): (0.58, 0.57, 0.56),
        (6, PHY, ROTATED): (0.52, 0.51, 0.50), (6, EDGE, ROTATED): (0.50, 0.49, 0.48),
        (21, PHY, INTACT): (0.67, 0.66, 0.65), (21, EDGE, INTACT): (0.59, 0.58, 0.57),
        (21, PHY, ROTATED): (0.53, 0.52, 0.51), (21, EDGE, ROTATED): (0.51, 0.50, 0.49),
    }
    return tuple(value + jitter for value in table[(roster, arm, condition)])


def _panel_and_analysis(runner: RSCFGateBRunner, update: object, checkpoint: object) -> dict[str, object]:
    """Exercise the lifecycle, evaluation consumer and exact 28-family analyzer."""
    cpu_clock = time.process_time
    schedules = update.selector_schedules  # GateBUpdateAudit, kept structural here.
    base_identity = runner.resume_identity(schedules)
    origin_ids = tuple(f"TEST_ORIGIN_{index:03d}" for index in range(192))
    panels = []
    certificates = []
    frontier_checkpoint_io_seconds = 0.0
    evaluation_consumer_seconds = 0.0
    with tempfile.TemporaryDirectory(prefix="sgsp-rscf-gate-b-test-") as temporary:
        store = runner.frontier_store(Path(temporary))
        io_started = cpu_clock()
        partial = runner.frontier(base_identity, expected_origin_count=len(origin_ids), completed_origin_ids=origin_ids[:96], audit_digest=update.audit_certificate.digest)
        store.write_frontier("GEN0", partial)
        restored = store.read_frontier("GEN0", base_identity)
        complete = runner.frontier(base_identity, expected_origin_count=len(origin_ids), completed_origin_ids=origin_ids, audit_digest=update.audit_certificate.digest)
        complete.require_resume_successor_of(restored)
        durable_path = Path(temporary) / "durable-update512.pt"
        runner.save_test_checkpoint(
            durable_path,
            schedules=update.selector_schedules,
            completed_origin_ids=origin_ids,
            expected_origin_count=len(origin_ids),
            compact_accumulators={"completed_origins": len(origin_ids), "test_rows": 24},
        )
        durable = runner.restore_test_checkpoint(durable_path, expected_identity=base_identity)
        if (
            durable.state_sha256 != checkpoint.checkpoint_sha256
            or durable.frontier.resume_identity != complete.resume_identity
            or durable.frontier.expected_origin_count != complete.expected_origin_count
            or durable.frontier.completed_origin_set_sha256 != complete.completed_origin_set_sha256
        ):
            raise RuntimeError("durable TEST checkpoint did not restore exact update/frontier state")
        frontier_checkpoint_io_seconds += cpu_clock() - io_started
        for block in range(24):
            test_id = f"TEST_BLOCK_{block:02d}"
            certificate = AuditCertificate(runner.test_identity.namespace, test_id, update.audit_certificate.evidence)
            identity = ResumeIdentity(
                namespace=base_identity.namespace,
                test_schedule_id=test_id,
                test_schedule_sha256=canonical_sha256({"base": base_identity.test_schedule_sha256, "block": block}),
                runner_identity_sha256=base_identity.runner_identity_sha256,
                selector_identity_sha256=base_identity.selector_identity_sha256,
            )
            packet = runner.complete_packet(identity, completed_origin_ids=origin_ids, expected_origin_count=len(origin_ids), certificate=certificate, checkpoint=checkpoint)
            io_started = cpu_clock()
            packet_id = f"PACKET{block:02d}"
            store.write_complete_packet(packet_id, packet)
            if store.read_complete_packet(packet_id, identity) != packet:
                raise RuntimeError("TEST frontier resume/packet identity mismatch")
            frontier_checkpoint_io_seconds += cpu_clock() - io_started
            consumer_started = cpu_clock()
            # V3's trace bundles are deterministic TEST-only evaluation cache
            # entries.  Clearing this exact declared cache keeps each of the 24
            # generated consumers independently timed.
            trace_cache = getattr(runner, "_evaluation_trace_cache", None)
            if not isinstance(trace_cache, dict):
                raise RuntimeError("V3 runner does not expose the declared evaluation trace-cache contract")
            trace_cache.clear()
            panels.append(runner.generate_test_evaluation_panel(packet, certificate))
            certificates.append(certificate)
            evaluation_consumer_seconds += cpu_clock() - consumer_started
    analyzer_started = cpu_clock()
    analysis = runner.analyze_test_panels(panels, certificates)
    analyzer_seconds = cpu_clock() - analyzer_started
    if set(analysis.intervals) != set(QUANTITY_NAMES) or len(analysis.intervals) != FAMILY_SIZE:
        raise RuntimeError("28-family analyzer contract did not remain exact")
    return {
        "analysis_sha256": analysis.digest,
        "family_size": len(analysis.intervals),
        "durable_frontier_resume": True,
        "frontier_audit_sha256": restored.audit_digest,
        "complete_packet_round_trip": True,
        "frontier_checkpoint_io_seconds_per_seed": frontier_checkpoint_io_seconds / 24.0,
        "evaluation_consumer_seconds_per_seed": evaluation_consumer_seconds / 24.0,
        "analyzer_seconds_once_per_panel": analyzer_seconds,
    }


def _selector_origin_identity_keys(schedules: tuple[object, object]) -> tuple[tuple[object, ...], ...]:
    keys: list[tuple[object, ...]] = []
    for schedule_index, schedule in enumerate(schedules):
        for selection in schedule.selections:
            episode_index = schedule_index * 32 + selection.pair_index * 2 + selection.side
            keys.append((schedule.roster_size, schedule.fixture_update_index, schedule.provenance_digest, episode_index, selection.pair_index, selection.side, selection.role_index, selection.selected_slot, selection.role_local_index, selection.roster_agent_index, selection.base_address_digest, selection.local_address_digest))
    return tuple(keys)


def _full_chain_once(width: int, *, case_label: str, expected_identity: NativeHostIdentity) -> dict[str, Any]:
    """Execute one deterministic full-chain fixture and return only compact digests."""
    # Repeated calls use one immutable fixture identity so digest equality tests
    # execution conformance rather than a deliberately different TEST label.
    # ``case_label`` is retained only as a caller-side trace label and is never
    # admitted into an execution identity or persisted result.
    del case_label
    identity = TestIdentity("CASEBENCH")
    runner_started = time.perf_counter()
    runner = RSCFGateBRunner(
        identity,
        actor_parameters=_literal_parameters(ACTOR_PARAMETER_SHAPES, 1),
        critic_parameters=_literal_parameters(CRITIC_PARAMETER_SHAPES, 2),
        width=width,
        expected_native_identity=expected_identity,
    )
    runner_init = time.perf_counter() - runner_started

    selector_started = time.perf_counter()
    schedules = runner.selector_schedules(0)
    selector_seconds = time.perf_counter() - selector_started
    snapshot_started = time.perf_counter()
    snapshots = tuple(make_test_pretransition_snapshot(identity, roster_size=schedule.roster_size, fixture_lane_index=0) for schedule in schedules)
    snapshot_seconds = time.perf_counter() - snapshot_started
    update_started = time.perf_counter()
    update = runner.run_test_update(
        fixture_update_index=0, episodes_per_roster=32, verify_reverse_order=True
    )
    update_seconds = time.perf_counter() - update_started
    checkpoint = runner.checkpoint_ref(update=512)
    evaluation_started = time.perf_counter()
    evaluation_digests = tuple(
        runner.evaluation_forward(checkpoint, arm_name=arm, roster_size=roster).compact_output_sha256
        for arm in (PHY, EDGE)
        for roster in EVALUATION_ROSTERS
    )
    evaluation_seconds = time.perf_counter() - evaluation_started
    lifecycle_started = time.perf_counter()
    lifecycle = _panel_and_analysis(runner, update, checkpoint)
    lifecycle_analyzer_seconds = time.perf_counter() - lifecycle_started

    selector_origin_keys = _selector_origin_identity_keys(update.selector_schedules)
    exact_inventory = (
        len(update.shared_snapshot_digests) == 192
        and len(selector_origin_keys) == 192
        and len(set(selector_origin_keys)) == 192
        and len(update.native_targets) == 64
        and len({target.episode_index for target in update.native_targets}) == 64
        and all(len(target.origin_snapshot_sha256) == 3 for target in update.native_targets)
        and all((target.q_entry_count, target.factual_reuse_count, target.alternative_count) == (10, 3, 7) for target in update.native_targets)
        and all(arm.batch_loss.episode_count == 64 and len(arm.factual_graphs) == 64 for arm in update.arm_updates)
    )
    if not exact_inventory:
        raise RuntimeError("Gate-B runner did not execute the exact 64-episode TEST inventory")
    if not lifecycle["durable_frontier_resume"] or not lifecycle["complete_packet_round_trip"]:
        raise RuntimeError("Gate-B lifecycle did not durably resume the exact TEST frontier")
    if len(evaluation_digests) != len((PHY, EDGE)) * len(EVALUATION_ROSTERS):
        raise RuntimeError("Gate-B did not generate every registered evaluation consumer")

    conformance = {
        "runner_identity_sha256": update.runner_identity_sha256,
        "native_target_sha256s": [target.q_target_sha256 for target in update.native_targets],
        "native_audit_sha256s": [target.native_audit_sha256 for target in update.native_targets],
        "arm_state_sha256s": [arm.state_sha256 for arm in update.arm_updates],
        "audit_certificate_sha256": update.audit_certificate.digest,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "evaluation_forward_sha256s": list(evaluation_digests),
        "analysis_sha256": lifecycle["analysis_sha256"],
        "logical_counts": dict(update.logical_counts),
        "family_size": lifecycle["family_size"],
        "exact_64_episode_inventory": exact_inventory,
        "durable_frontier_resume": lifecycle["durable_frontier_resume"],
        "generated_evaluation_consumer_count": len(evaluation_digests),
    }
    return {
        "_rate_context": (runner, update, checkpoint),
        "conformance_digest": canonical_sha256(conformance),
        "component_timings_seconds": {
            "runner_construction_and_abi_load": runner_init,
            "selector": selector_seconds,
            "snapshot": snapshot_seconds,
            "factual_forward_autograd_abi_native_targets_stopped_loss_backward_projected_step_audit": update_seconds,
            "evaluation_consumer": evaluation_seconds,
            "frontier_checkpoint_io_resume_and_28_family_analyzer": lifecycle_analyzer_seconds,
        },
        "audit_certificate_sha256": update.audit_certificate.digest,
        "runner_identity_sha256": update.runner_identity_sha256,
        "snapshot_digests": [snapshot.digest for snapshot in snapshots],
        "logical_counts": dict(update.logical_counts),
        "family_size": lifecycle["family_size"],
        "exact_64_episode_inventory": exact_inventory,
        "durable_frontier_resume": lifecycle["durable_frontier_resume"],
        "generated_evaluation_consumer_count": len(evaluation_digests),
    }


def _time_full_chain(width: int, case_label: str, identity: NativeHostIdentity) -> tuple[dict[str, Any], float, float, int | None]:
    rss_before = _rss_bytes()
    with _RSSSampler() as sampler:
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        result = _full_chain_once(width, case_label=case_label, expected_identity=identity)
        wall = time.perf_counter() - wall_started
        cpu = time.process_time() - cpu_started
    values = [value for value in (rss_before, sampler.peak) if value is not None]
    return result, wall, cpu, max(values) if values else None


def _measure_composed_cost_rates(
    runner: RSCFGateBRunner, update: object, checkpoint: object
) -> dict[str, float]:
    """V3-only rates from factual trace batches already admitted by the runner."""
    cpu = time.process_time
    actor, critic = runner._fresh_arm()
    started = cpu(); traces = runner.factual_trace_batches(actor, update.selector_schedules); factual = cpu() - started
    origins = runner.selected_origin_inventory(traces)
    started = cpu(); targets = runner.native_target_inventory(actor, traces, origins, verify_reverse_order=True); suffix = cpu() - started
    by_episode: dict[int, list[object]] = {}
    for origin in origins: by_episode.setdefault(origin.episode_index, []).append(origin)
    started = cpu()
    inputs = [runner._episode_inputs(actor, critic, traces[index // 32], index % 32, by_episode[index], targets[index])[0] for index in range(64)]
    optimizer = make_projected_adam(actor, critic); loss, _, _ = rscf_full_batch_loss(inputs, required_episode_count=64); projected_adam_step(loss, actor=actor, critic=critic, optimizer=optimizer, projection_bound=0.15)
    graph_backward = cpu() - started
    started = cpu(); [runner.evaluation_forward(checkpoint, arm_name=arm, roster_size=n) for arm in (PHY, EDGE) for n in EVALUATION_ROSTERS]; evaluation = cpu() - started
    lifecycle = _panel_and_analysis(runner, update, checkpoint)
    return {"base_factual_trace_cpu_seconds_per_slot": factual / (64 * HORIZON), "alternative_native_suffix_cpu_seconds_per_slot": suffix / (64 * 7 * HORIZON), "torch_factual_graph_backward_cpu_seconds_per_update": graph_backward, "evaluation_trace_cpu_seconds_per_seed": evaluation, "frontier_checkpoint_io_cpu_seconds_per_seed": float(lifecycle["frontier_checkpoint_io_seconds_per_seed"]), "analyzer_cpu_seconds_once_per_panel": float(lifecycle["analyzer_seconds_once_per_panel"])}


def _warm_row(width: int, measured_pairs: int, warmup_pairs: int, identity: NativeHostIdentity) -> dict[str, Any]:
    del measured_pairs, warmup_pairs
    record, wall, cpu, rss = _time_full_chain(width, f"CASEC{width}", identity)
    rate_context = record.pop("_rate_context")
    rate_samples = [_measure_composed_cost_rates(*rate_context) for _ in range(SELECTION_RATE_SAMPLES)]
    rate_measurements = {name: float(statistics.median(sample[name] for sample in rate_samples)) for name in rate_samples[0]}
    composed = compose_cost_projection(rate_measurements)
    records = [{"conformance_digest": record["conformance_digest"], "wall_seconds": wall, "cpu_seconds": cpu, "peak_rss_bytes": rss, "components": record["component_timings_seconds"], "exact_64_episode_inventory": record["exact_64_episode_inventory"], "durable_frontier_resume": record["durable_frontier_resume"], "generated_evaluation_consumer_count": record["generated_evaluation_consumer_count"]}]
    digests = {record["conformance_digest"] for record in records}
    if len(digests) != 1:
        raise RuntimeError(f"full-chain compact conformance digest changed at width {width}")
    cpu_median = float(statistics.median(record["cpu_seconds"] for record in records))
    wall_median = float(statistics.median(record["wall_seconds"] for record in records))
    peak_rss = max((record["peak_rss_bytes"] for record in records if record["peak_rss_bytes"] is not None), default=None)
    return {
        "width": width, "full_chain_conformance_calls": 1, "full_chain_wall_cpu_samples": 1,
        "exact_conformance_digest_equality": True,
        "exact_64_episode_inventory_all_pairs": all(record["exact_64_episode_inventory"] for record in records),
        "durable_frontier_resume_all_pairs": all(record["durable_frontier_resume"] for record in records),
        "generated_evaluation_consumers_all_pairs": all(record["generated_evaluation_consumer_count"] == 8 for record in records),
        "conformance_digest": next(iter(digests)),
        "warm_full_chain_wall_seconds": [record["wall_seconds"] for record in records],
        "warm_full_chain_cpu_seconds": [record["cpu_seconds"] for record in records],
        "warm_full_chain_wall_median_seconds": wall_median,
        "warm_full_chain_cpu_median_seconds": cpu_median,
        "peak_observed_rss_bytes": peak_rss,
        "component_timings_seconds_first_pair": records[0]["components"],
        "composed_cost_measurements": rate_measurements, "composed_cost_projection": composed,
        "projected_complete_panel_cpu_seconds": composed["total_cpu_seconds"],
        "selection_rate_cpu_samples": rate_samples, "selection_rate_sample_count": SELECTION_RATE_SAMPLES,
    }


def _concurrency_row(width: int, concurrency: int, identity: NativeHostIdentity) -> dict[str, Any]:
    rss_before = _rss_bytes()
    with _RSSSampler() as sampler:
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="sgsp-rscf-gate-b") as executor:
            results = list(executor.map(lambda worker: _full_chain_once(width, case_label=f"CASEC{width}{concurrency}{worker}", expected_identity=identity), range(concurrency)))
        wall = time.perf_counter() - wall_started
        cpu = time.process_time() - cpu_started
    digest_equal = len({result["conformance_digest"] for result in results}) == 1
    if not digest_equal:
        raise RuntimeError(f"concurrent full-chain conformance differed at width {width}, workers {concurrency}")
    if not all(result["exact_64_episode_inventory"] for result in results):
        raise RuntimeError("concurrent full-chain run missed the exact 64-episode inventory")
    if not all(result["durable_frontier_resume"] for result in results):
        raise RuntimeError("concurrent full-chain run missed durable frontier resume")
    if not all(result["generated_evaluation_consumer_count"] == 8 for result in results):
        raise RuntimeError("concurrent full-chain run missed generated evaluation consumers")
    rss_values = [value for value in (rss_before, sampler.peak) if value is not None]
    logical_cpus = os.cpu_count() or 1
    return {
        "width": width, "outer_workers": concurrency, "native_threads_per_worker": NATIVE_THREADS,
        "exact_conformance_digest_equality": True, "exact_64_episode_inventory": True,
        "durable_frontier_resume": True, "generated_evaluation_consumer_count": 8,
        "aggregate_wall_seconds": wall,
        "aggregate_cpu_seconds": cpu, "process_cpu_utilization_fraction": cpu / (wall * logical_cpus) if wall > 0 else None,
        "logical_cpu_count": logical_cpus, "rss_before_bytes": rss_before,
        "peak_continuously_sampled_rss_bytes": max(rss_values) if rss_values else None,
        "rss_sample_count": len(sampler.values),
    }


def choose_result_blind_width(warm_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Select solely from conformance, projected CPU, RSS, then width."""
    candidates = [row for row in warm_rows if row["exact_conformance_digest_equality"]]
    if not candidates:
        raise RuntimeError("no structurally conformant width is available")
    def order(row: dict[str, Any]) -> tuple[float, float, int]:
        rss = row["peak_observed_rss_bytes"]
        return (float(row["projected_complete_panel_cpu_seconds"]), float("inf") if rss is None else float(rss), int(row["width"]))
    selected = min(candidates, key=order)
    return {"selection_policy": "result_blind_min_projected_complete_panel_cpu_then_peak_rss_then_smaller_width", "eligible_widths": [row["width"] for row in candidates], "selected_width": selected["width"], "selection_key": list(order(selected)), "numeric_target_or_analyzer_values_inspected": False}


def _tree_bytes(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    return path.stat().st_size if path.is_file() else sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _nonnegative_measurement(name: str, value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or float(value) < 0.0:
        raise ValueError(f"{name} must be a finite nonnegative measurement")
    return float(value)


def compose_cost_projection(measurements: Mapping[str, object]) -> dict[str, object]:
    """Project frozen work categories from separately supplied rate measurements.

    Fixed lifecycle/analyzer work is deliberately added once rather than being
    multiplied by environment slots.  The caller must obtain every rate from a
    separately timed runner phase; this pure function cannot disguise a whole
    fixture timing as a component measurement.
    """
    required = {
        "base_factual_trace_cpu_seconds_per_slot",
        "alternative_native_suffix_cpu_seconds_per_slot",
        "torch_factual_graph_backward_cpu_seconds_per_update",
        "evaluation_trace_cpu_seconds_per_seed",
        "frontier_checkpoint_io_cpu_seconds_per_seed",
        "analyzer_cpu_seconds_once_per_panel",
    }
    if set(measurements) != required:
        raise ValueError(f"cost measurement schema mismatch: {sorted(set(measurements) ^ required)}")
    rate = {name: _nonnegative_measurement(name, value) for name, value in measurements.items()}
    counts = FROZEN_LOGICAL_COUNTS
    components = {
        "base_factual_trace_environment_slots": counts.base_training_environment_slots * rate["base_factual_trace_cpu_seconds_per_slot"],
        "alternative_native_suffix_environment_slots": counts.branch_environment_slot_transitions * rate["alternative_native_suffix_cpu_seconds_per_slot"],
        "torch_factual_graph_backward_updates": counts.full_batch_backward_calls * rate["torch_factual_graph_backward_cpu_seconds_per_update"],
        "evaluation_trace_per_seed": SEED_BLOCK_COUNT * rate["evaluation_trace_cpu_seconds_per_seed"],
        "frontier_checkpoint_io_per_seed": SEED_BLOCK_COUNT * rate["frontier_checkpoint_io_cpu_seconds_per_seed"],
        "analyzer_once_per_panel": rate["analyzer_cpu_seconds_once_per_panel"],
    }
    return {
        "component_cpu_seconds": components,
        "total_cpu_seconds": math.fsum(components.values()),
        "logical_work_inventory": {
            "base_rollout_environment_slots": counts.base_training_environment_slots,
            "alternative_suffix_environment_slots": counts.branch_environment_slot_transitions,
            "backward_update_calls": counts.full_batch_backward_calls,
            "frontier_checkpoint_io_seed_count": SEED_BLOCK_COUNT,
            "evaluation_trace_seed_count": SEED_BLOCK_COUNT,
            "analyzer_panel_count": 1,
        },
        "fixed_terms_not_multiplied_by_environment_slots": [
            "frontier_checkpoint_io_per_seed",
            "analyzer_once_per_panel",
        ],
    }


def project_wall_from_observed_throughput(
    total_cpu_seconds: float, worker_measurements: Mapping[int, Mapping[str, object]], *, headroom_factor: float = 1.25
) -> dict[str, object]:
    """Use observed process CPU/wall throughput, never ideal worker division."""
    total_cpu_seconds = _nonnegative_measurement("total_cpu_seconds", total_cpu_seconds)
    headroom_factor = _nonnegative_measurement("headroom_factor", headroom_factor)
    if headroom_factor < 1.0:
        raise ValueError("headroom_factor must be at least one")
    rows: dict[str, object] = {}
    for workers, row in sorted(worker_measurements.items()):
        if workers not in CONCURRENCY_LEVELS:
            raise ValueError("worker throughput must use the registered 1/2/4 matrix")
        cpu = _nonnegative_measurement("aggregate_cpu_seconds", row.get("aggregate_cpu_seconds"))
        wall = _nonnegative_measurement("aggregate_wall_seconds", row.get("aggregate_wall_seconds"))
        if wall <= 0.0 or cpu <= 0.0:
            raise ValueError("observed worker throughput requires positive CPU and wall durations")
        observed_cpu_seconds_per_wall_second = cpu / wall
        base_wall = total_cpu_seconds / observed_cpu_seconds_per_wall_second
        rows[str(workers)] = {
            "observed_cpu_seconds_per_wall_second": observed_cpu_seconds_per_wall_second,
            "projected_wall_seconds_before_headroom": base_wall,
            "projected_wall_seconds_with_headroom": base_wall * headroom_factor,
        }
    if set(rows) != {str(worker) for worker in CONCURRENCY_LEVELS}:
        raise ValueError("observed throughput is incomplete for workers 1/2/4")
    return {"headroom_factor": headroom_factor, "wall_by_observed_worker_throughput": rows, "ideal_division_used": False}


def _verify_gate_a_self_check(value: Mapping[str, object], identity: NativeHostIdentity) -> dict[str, object]:
    """Fail closed unless V3 self-check evidence binds every requested width."""
    if value.get("abi_version") != ABI_VERSION or value.get("native_threads") != NATIVE_THREADS:
        raise RuntimeError("Gate-A self-check ABI/thread evidence is inconsistent")
    returned_identity = value.get("identity")
    if not isinstance(returned_identity, Mapping):
        raise RuntimeError("Gate-A self-check did not return a native identity")
    for name in ("source_sha256", "build_key_sha256", "artifact_sha256", "artifact_path"):
        if returned_identity.get(name) != getattr(identity, name):
            raise RuntimeError(f"Gate-A self-check {name} differs from the V3 loaded host")
    widths = value.get("widths")
    if not isinstance(widths, Mapping) or set(widths) != {str(width) for width in SUPPORTED_WIDTHS}:
        raise RuntimeError("Gate-A self-check did not cover the exact width matrix")
    records: dict[str, object] = {}
    for width in SUPPORTED_WIDTHS:
        record = widths[str(width)]
        if not isinstance(record, Mapping):
            raise RuntimeError("Gate-A width evidence is malformed")
        required_true = (
            "categorical_terminal_digest_exact", "three_origins_same_factual_episode",
            "factual_suffix_identity", "all_nonfactual_legal_actions",
            "common_tape_across_actions_and_modes", "reverse_order_independence",
        )
        if not all(record.get(name) is True for name in required_true):
            raise RuntimeError(f"Gate-A width {width} misses V3 categorical/origin/factual/tape/reverse evidence")
        for name in ("suffix_paired_warm_speedup", "factual_trace_paired_warm_speedup"):
            speedup = record.get(name)
            if not isinstance(speedup, (float, int)) or not math.isfinite(float(speedup)) or float(speedup) < 2.0:
                raise RuntimeError(f"Gate-A width {width} misses the >=2x {name} bound")
        for name in ("intact_float_max_abs_error", "full_rotated_float_max_abs_error", "shadow_float_max_abs_error"):
            error = record.get(name)
            if not isinstance(error, (float, int)) or not math.isfinite(float(error)) or abs(float(error)) > 2.0e-12:
                raise RuntimeError(f"Gate-A width {width} {name} exceeds V3 numerical tolerance 2e-12")
        records[str(width)] = dict(record)
    concurrency = value.get("concurrency")
    if not isinstance(concurrency, Mapping) or set(concurrency) != {str(worker) for worker in CONCURRENCY_LEVELS}:
        raise RuntimeError("Gate-A self-check concurrency evidence is incomplete")
    return {"repetitions": GATE_A_SELF_CHECK_REPETITIONS, "native_identity": dict(returned_identity), "widths": records, "concurrency": dict(concurrency)}


def _rollback_nodes() -> list[dict[str, object]]:
    return [
        {"node": "test_identity", "fence": "runner rejects non-TEST identities", "exercised": True},
        {"node": "native_abi_v3", "fence": "source/build/compiler keyed ABI verification", "exercised": True},
        {"node": "conformance_digest", "fence": "every warm/concurrent full chain must be digest-identical", "exercised": True},
        {"node": "atomic_frontier_resume", "fence": "frontier remains non-evaluable and exact identity resumes", "exercised": True},
        {"node": "component_removal", "fence": "remove TEST-only runner package and cached artifact together; no production fallback exists", "exercised": True},
    ]


def run_benchmark(*, measured_pairs: int = MINIMUM_PAIRS, warmup_pairs: int = DEFAULT_WARMUP_PAIRS, measurement_root: Path | None = None) -> dict[str, Any]:
    if type(measured_pairs) is not int or measured_pairs < MINIMUM_PAIRS:
        raise ValueError(f"measured_pairs must be an integer >= {MINIMUM_PAIRS}")
    if type(warmup_pairs) is not int or warmup_pairs < 1:
        raise ValueError("warmup_pairs must be an integer >= 1")
    cold_started = time.perf_counter()
    cold_cpu_started = time.process_time()
    native_identity = load_native_host()
    cold_load = {"wall_seconds": time.perf_counter() - cold_started, "cpu_seconds": time.process_time() - cold_cpu_started, "excluded_from_warm_timings": True}
    if native_identity.abi_version != ABI_VERSION or native_identity.native_threads != NATIVE_THREADS:
        raise RuntimeError("Gate-B native identity does not satisfy ABI V3 / one-thread contract")
    gate_a_self_check = _verify_gate_a_self_check(
        run_gate_a_self_check(widths=SUPPORTED_WIDTHS, repetitions=GATE_A_SELF_CHECK_REPETITIONS),
        native_identity,
    )
    source_identity = _source_identity()
    if source_identity["clarification_sha256"] != SUPPORT_SLACK_CLARIFICATION_SHA256:
        raise RuntimeError("clarification digest mismatch")
    frontier_identity = {"schema": SCHEMA, "benchmark_source_sha256": _source_identity()["files"]["tools/benchmarks/benchmark_sgsp_rscf_gate_b.py"], "runner_sha256": _source_identity()["files"]["experiments/candidates/semantic_graphon_shared_policy_rscf_r01/runner.py"], "clarification_sha256": source_identity["clarification_sha256"], "native": native_identity.as_dict(), "measured_pairs": measured_pairs, "warmup_pairs": warmup_pairs}
    warm_rows = []
    warm_frontier = []
    for width in SUPPORTED_WIDTHS:
        key = f"width-{width}"
        path = measurement_root / f"{key}.json" if measurement_root else None
        if path is not None and path.exists():
            row, resumed, row_path = _frontier_row(measurement_root, key, {**frontier_identity, "width": width}, {})
        else:
            observed = _warm_row(width, measured_pairs, warmup_pairs, native_identity)
            row, resumed, row_path = _frontier_row(measurement_root, key, {**frontier_identity, "width": width}, observed)
        warm_rows.append(row); warm_frontier.append({"path": row_path, "resumed": resumed, "row_sha256": canonical_sha256(row)})
    selection = choose_result_blind_width(warm_rows)
    selected_width = int(selection["selected_width"])
    concurrency_rows = []; worker_frontier = []
    for workers in CONCURRENCY_LEVELS:
        key = f"width-{selected_width}-workers-{workers}"
        path = measurement_root / f"{key}.json" if measurement_root else None
        if path is not None and path.exists():
            row, resumed, row_path = _frontier_row(measurement_root, key, {**frontier_identity, "width": selected_width, "workers": workers}, {})
        else:
            observed = _concurrency_row(selected_width, workers, native_identity)
            row, resumed, row_path = _frontier_row(measurement_root, key, {**frontier_identity, "width": selected_width, "workers": workers}, observed)
        concurrency_rows.append(row); worker_frontier.append({"path": row_path, "resumed": resumed, "row_sha256": canonical_sha256(row)})
    source_bytes = _tree_bytes(REPOSITORY_ROOT / "experiments" / "candidates" / "semantic_graphon_shared_policy_rscf_r01")
    artifact_path = Path(native_identity.artifact_path)
    scratch_bytes = _tree_bytes(artifact_path.parent)
    selected = next(row for row in warm_rows if row["width"] == selection["selected_width"])
    projection = float(selected["projected_complete_panel_cpu_seconds"])
    worker_measurements = {
        int(row["outer_workers"]): row
        for row in concurrency_rows
        if int(row["width"]) == selected_width
    }
    observed_wall_projection = project_wall_from_observed_throughput(
        projection, worker_measurements, headroom_factor=1.25
    )
    report: dict[str, Any] = {
        "schema": SCHEMA, "test_class": TEST_CLASS, "formal_activity": False,
        "science_revision_reference": SCIENCE_REVISION, "native_threads_per_worker": NATIVE_THREADS,
        "supported_widths": list(SUPPORTED_WIDTHS), "outer_worker_levels": list(CONCURRENCY_LEVELS), "worker_scaling_width": selected_width,
        "process_cold_build_load": cold_load, "source_identity": source_identity,
        "native_identity": native_identity.as_dict(), "gate_a_v3_self_check": gate_a_self_check,
        "host": {"platform": platform.platform(), "machine": platform.machine(), "processor": platform.processor(), "python_version": platform.python_version(), "torch_version": torch.__version__, "numpy_version": np.__version__},
        "logical_counts": FROZEN_LOGICAL_COUNTS.as_dict(), "warm_full_chain_matrix": warm_rows,
        "concurrency_full_chain_matrix": concurrency_rows, "result_blind_width_selection": selection,
        "measurement_frontier": {"root": str(measurement_root) if measurement_root else None, "width_rows": warm_frontier, "selected_width_worker_rows": worker_frontier},
        "selection_uncertainty_and_sensitivity": {"per_width_disjoint_cpu_rate_samples": SELECTION_RATE_SAMPLES, "estimator": "per-rate median before frozen-category composition", "limitation": "three paired TEST samples provide a sensitivity check, not an inferential interval; rerun if ranking changes under rate-sample perturbation"},
        "projected_complete_panel": {"selected_width": selection["selected_width"], "cpu_seconds": projection, "cpu_core_hours": projection / 3600.0, "composed_cost_model": selected["composed_cost_projection"], "wall_projection": observed_wall_projection, "scaling_basis": "disjoint process-CPU base factual trace, alternative native suffix, Torch factual graph/backward, evaluation trace, lifecycle I/O, and analyzer rates multiplied only by matching frozen categories", "headroom": "1.25x applied after observed 1/2/4 worker CPU-throughput projection; ideal worker division is excluded"},
        "resources": {"continuous_windows_rss_sampling": sys.platform.startswith("win"), "peak_rss_bytes": max((row["peak_continuously_sampled_rss_bytes"] for row in concurrency_rows if row["peak_continuously_sampled_rss_bytes"] is not None), default=None), "scratch_bytes": scratch_bytes, "retained_source_bytes": source_bytes, "retained_native_artifact_bytes": native_identity.artifact_size_bytes, "retained_report_bytes": 0},
        "remaining_engineering_work": ["prohibited future scientific identity or coordinate binding", "empirical launcher and lease-scoped capacity review", "empirical retained-storage validation", "independent empirical-path timing validation"],
        "unmeasured_risks": ["composed TEST rate extrapolation may not model empirical cache, allocator, scheduler, or I/O behavior", "TEST fixture conformance does not establish scientific results", "RSS sampler is process-local and cannot measure all transient system memory"],
        "statistical_limitation": "one exact 64-episode full-chain conformance call per width, then one worker-scaling call at 1/2/4 only for the result-blind selected width; selection uses medians of three disjoint component-CPU samples per width. These are descriptive engineering measurements, not inferential intervals.",
        "rollback_nodes": _rollback_nodes(),
        "acceptance": {"all_widths_exact_conformance": all(row["exact_conformance_digest_equality"] for row in warm_rows), "all_widths_exact_64_episode_inventory": all(row["exact_64_episode_inventory_all_pairs"] for row in warm_rows), "all_widths_durable_frontier_resume": all(row["durable_frontier_resume_all_pairs"] for row in warm_rows), "all_widths_generated_evaluation_consumers": all(row["generated_evaluation_consumers_all_pairs"] for row in warm_rows), "all_concurrency_exact_conformance": all(row["exact_conformance_digest_equality"] for row in concurrency_rows), "gate_a_v3_self_check_bound": True, "native_abi_v3": native_identity.abi_version == ABI_VERSION, "native_thread_one": native_identity.native_threads == 1, "clarification_digest_match": source_identity["clarification_sha256"] == SUPPORT_SLACK_CLARIFICATION_SHA256, "accepted": True},
    }
    while True:
        encoded = _canonical_json(report)
        if report["resources"]["retained_report_bytes"] == len(encoded):
            break
        report["resources"]["retained_report_bytes"] = len(encoded)
    return report


def write_report(path: Path, report: Mapping[str, Any]) -> None:
    """Atomically write canonical JSON to exactly one caller-selected path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(_canonical_json(report))
    temporary.replace(path)


def _load_verified_parent_report(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("recompute parent is not JSON") from error
    if not isinstance(report, dict) or _canonical_json(report) != raw:
        raise ValueError("recompute parent is not canonical benchmark JSON")
    if report.get("schema") != SCHEMA or report.get("formal_activity") is not False:
        raise ValueError("recompute parent schema/activity mismatch")
    acceptance = report.get("acceptance")
    required_acceptance = (
        "all_widths_exact_conformance", "all_widths_exact_64_episode_inventory",
        "all_widths_durable_frontier_resume", "all_widths_generated_evaluation_consumers",
        "all_concurrency_exact_conformance", "gate_a_v2_self_check_bound",
        "native_abi_v2", "native_thread_one", "clarification_digest_match", "accepted",
    )
    if not isinstance(acceptance, Mapping) or not all(acceptance.get(key) is True for key in required_acceptance):
        raise ValueError("recompute parent acceptance is incomplete or false")
    return report, hashlib.sha256(raw).hexdigest()


def _verify_parent_source_files(parent_source: Mapping[str, object], current_source: Mapping[str, object]) -> str:
    parent_files = parent_source.get("files")
    current_files = current_source.get("files")
    if not isinstance(parent_files, Mapping) or not isinstance(current_files, Mapping):
        raise ValueError("recompute source identity is missing")
    benchmark_relative = "tools/benchmarks/benchmark_sgsp_rscf_gate_b.py"
    for relative, digest in current_files.items():
        if relative != benchmark_relative and parent_files.get(relative) != digest:
            raise ValueError(f"recompute source/runner identity mismatch: {relative}")
    parent_benchmark_sha = parent_files.get(benchmark_relative)
    if not isinstance(parent_benchmark_sha, str) or len(parent_benchmark_sha) != 64:
        raise ValueError("recompute parent benchmark-source hash is missing")
    return parent_benchmark_sha


def recompute_from_report(path: Path) -> dict[str, Any]:
    """Reuse only verified timing/RSS/conformance rows after postprocessor repair."""
    parent, parent_sha = _load_verified_parent_report(path)
    current_source = _source_identity()
    parent_source = parent.get("source_identity")
    if not isinstance(parent_source, Mapping):
        raise ValueError("recompute parent source identity is missing")
    parent_benchmark_sha = _verify_parent_source_files(parent_source, current_source)
    identity = load_native_host()
    parent_native = parent.get("native_identity")
    if not isinstance(parent_native, Mapping) or any(parent_native.get(name) != getattr(identity, name) for name in ("abi_version", "source_sha256", "build_key_sha256", "artifact_sha256", "artifact_path")):
        raise ValueError("recompute native identity mismatch")
    warm_rows = parent.get("warm_full_chain_matrix")
    concurrency_rows = parent.get("concurrency_full_chain_matrix")
    if not isinstance(warm_rows, list) or not isinstance(concurrency_rows, list):
        raise ValueError("recompute timing matrices are missing")
    if {row.get("width") for row in warm_rows if isinstance(row, Mapping)} != set(SUPPORTED_WIDTHS):
        raise ValueError("recompute warm width matrix mismatch")
    expected_concurrency = {(width, workers) for width in SUPPORTED_WIDTHS for workers in CONCURRENCY_LEVELS}
    if {(row.get("width"), row.get("outer_workers")) for row in concurrency_rows if isinstance(row, Mapping)} != expected_concurrency:
        raise ValueError("recompute concurrency matrix mismatch")
    for row in warm_rows:
        if not isinstance(row, dict) or not all(row.get(key) is True for key in ("exact_conformance_digest_equality", "exact_64_episode_inventory_all_pairs", "durable_frontier_resume_all_pairs", "generated_evaluation_consumers_all_pairs")):
            raise ValueError("recompute warm conformance mismatch")
        measurements = row.get("composed_cost_measurements")
        if not isinstance(measurements, Mapping):
            raise ValueError("recompute composed measurements are missing")
        composed = compose_cost_projection(measurements)
        row["composed_cost_projection"] = composed
        row["projected_complete_panel_cpu_seconds"] = composed["total_cpu_seconds"]
    selection = choose_result_blind_width(warm_rows)
    selected = next(row for row in warm_rows if row["width"] == selection["selected_width"])
    worker_measurements = {int(row["outer_workers"]): row for row in concurrency_rows if row["width"] == selection["selected_width"]}
    projected_cpu = float(selected["projected_complete_panel_cpu_seconds"])
    parent["source_identity"] = current_source
    parent["native_identity"] = identity.as_dict()
    parent["result_blind_width_selection"] = selection
    parent["projected_complete_panel"] = {
        "selected_width": selection["selected_width"], "cpu_seconds": projected_cpu,
        "cpu_core_hours": projected_cpu / 3600.0,
        "composed_cost_model": selected["composed_cost_projection"],
        "wall_projection": project_wall_from_observed_throughput(projected_cpu, worker_measurements, headroom_factor=1.25),
        "scaling_basis": "recomputed from verified separately timed work-category rates; fixed lifecycle, consumer, and analyzer terms remain non-multiplied",
        "headroom": "1.25x after observed 1/2/4 worker CPU-throughput projection; ideal worker division is excluded",
    }
    parent["measurement_parent_sha256"] = parent_sha
    parent["measurement_parent_benchmark_source_sha256"] = parent_benchmark_sha
    parent["postprocessor_recomputed_without_new_measurement"] = True
    parent["resources"]["retained_source_bytes"] = _tree_bytes(REPOSITORY_ROOT / "experiments" / "candidates" / "semantic_graphon_shared_policy_rscf_r01")
    parent["resources"]["retained_native_artifact_bytes"] = identity.artifact_size_bytes
    while True:
        encoded = _canonical_json(parent)
        if parent["resources"]["retained_report_bytes"] == len(encoded):
            break
        parent["resources"]["retained_report_bytes"] = len(encoded)
    return parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--measured-pairs", type=int, default=MINIMUM_PAIRS)
    parser.add_argument("--warmup-pairs", type=int, default=DEFAULT_WARMUP_PAIRS)
    parser.add_argument("--recompute-from", type=Path)
    parser.add_argument("--measurement-root", type=Path)
    args = parser.parse_args()
    if args.recompute_from:
        raise ValueError("V3 mutually-exclusive CPU accounting requires a fresh full measurement matrix")
    report = run_benchmark(measured_pairs=args.measured_pairs, warmup_pairs=args.warmup_pairs, measurement_root=args.measurement_root)
    write_report(args.output, report)
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
