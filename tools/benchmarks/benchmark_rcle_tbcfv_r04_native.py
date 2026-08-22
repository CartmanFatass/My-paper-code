"""Fixture-only efficiency review for the RCLE TBCFV r04 native host.

The harness deliberately keeps the production surface absent: every input is a
hand-written conformance fixture or a labelled synthetic payload.  Its compact
JSON record contains engineering timing/equivalence facts only, never host
endpoints, analyzer branches, empirical identities, or panel data.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Iterator, TypeVar


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (  # noqa: E402
    FLEX,
    LEARNED_PACKAGES,
    make_conformance_fixture_model,
    make_pointer_inputs,
    selected_claim_log_probability,
    stopped_actor_plan,
    stopped_normal_log_density,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv import native_backend as native  # noqa: E402
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.artifacts import (  # noqa: E402
    SyntheticFrontier,
    compute_source_digest,
    create_fixture_root,
    make_aggregate_manifest,
    make_baseline_manifest,
    make_scripted_panel_manifest,
    make_semantic_position_manifest,
    make_synthetic_model_state_manifest,
    publish_synthetic_frontier,
    scan_resume_root,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import SCRIPTED_PACKAGES  # noqa: E402
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import (  # noqa: E402
    ACTIVE_CONTINUATION,
    NEW_EPOCH,
    EpisodeTape,
    FixtureSpec,
    run_oracle_batch,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (  # noqa: E402
    BLOCK_COUNT,
    DIRECT_VALUE_VARIABLES,
    ANALYZER_SCHEMA_VERSION,
    FIXTURE_HOST_COMPONENT,
    HELDOUT_CELLS,
    MECHANISM_VARIABLES,
    PREREQUISITE_VARIABLES,
    SCIENCE_REVISION,
    TAIL_COUNT,
    TRAINING_CELLS,
    analyze_fixture_records,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.scripted import (  # noqa: E402
    coherent_scaffold,
    fragmented_scaffold,
    independent_nearest,
)

import torch  # noqa: E402


SCHEMA = "RCLE_TBCFV_R04_FIXTURE_EFFICIENCY_REVIEW_V1"
WIDTHS = (1, 8, 32)
# The frozen planning count is only a cost multiplier; no panel is materialized.
FULL_PANEL_TICKS = 495_452_160
LEARNED_UPDATES = 80_000
HELDOUT_AGENT_DECISIONS = 262_144_000
SCRIPTED_CLAIM_CLOCK_CALLS = 15_728_640
ATOMIC_RUN_BLOCKS = 20
UPDATE_EPISODES = 64
UPDATE_AGENT_DECISIONS = 8_192
UPDATE_CANDIDATE_SCORES = 6
SCRIPTED_MEASUREMENT_REPETITIONS = 128
ANALYZER_MEASUREMENT_INVOCATIONS = 64
WINDOWS_PROCESS_CPU_RESOLUTION_SECONDS = 1.0 / 64.0
T = TypeVar("T")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def _process_snapshot() -> dict[str, int | bool | str | None]:
    """Best-effort RSS and I/O counters, explicitly labelled if unavailable."""
    result: dict[str, int | bool | str | None] = {
        "available": True, "error": None, "rss_bytes": 0, "peak_rss_bytes": 0,
        "read_bytes": 0, "write_bytes": 0,
    }
    if os.name == "nt":
        try:
            from ctypes import wintypes

            class Memory(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("page_fault_count", wintypes.DWORD),
                    ("peak_working_set_size", ctypes.c_size_t), ("working_set_size", ctypes.c_size_t),
                    ("quota_peak_paged_pool_usage", ctypes.c_size_t), ("quota_paged_pool_usage", ctypes.c_size_t),
                    ("quota_peak_non_paged_pool_usage", ctypes.c_size_t), ("quota_non_paged_pool_usage", ctypes.c_size_t),
                    ("pagefile_usage", ctypes.c_size_t), ("peak_pagefile_usage", ctypes.c_size_t)]
            class Io(ctypes.Structure):
                _fields_ = [("read_operation_count", ctypes.c_ulonglong), ("write_operation_count", ctypes.c_ulonglong),
                    ("other_operation_count", ctypes.c_ulonglong), ("read_transfer_count", ctypes.c_ulonglong),
                    ("write_transfer_count", ctypes.c_ulonglong), ("other_transfer_count", ctypes.c_ulonglong)]
            kernel, psapi = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("psapi", use_last_error=True)
            kernel.GetCurrentProcess.argtypes = []
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Memory), wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            kernel.GetProcessIoCounters.argtypes = [wintypes.HANDLE, ctypes.POINTER(Io)]
            kernel.GetProcessIoCounters.restype = wintypes.BOOL
            handle = kernel.GetCurrentProcess()
            memory = Memory(); memory.cb = ctypes.sizeof(memory)
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo")
            io = Io()
            if not kernel.GetProcessIoCounters(handle, ctypes.byref(io)):
                raise OSError(ctypes.get_last_error(), "GetProcessIoCounters")
            result.update(rss_bytes=int(memory.working_set_size), peak_rss_bytes=int(memory.peak_working_set_size),
                          read_bytes=int(io.read_transfer_count), write_bytes=int(io.write_transfer_count))
            if not result["rss_bytes"] or not result["peak_rss_bytes"]:
                raise RuntimeError("zero Windows working-set counter")
            return result
        except Exception as exc:  # pragma: no cover - platform API dependent
            result.update(available=False, error=f"windows_telemetry_unavailable:{type(exc).__name__}:{exc}")
            return result
    try:
        import resource
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        result.update(rss_bytes=peak * (1 if sys.platform == "darwin" else 1024), peak_rss_bytes=peak * (1 if sys.platform == "darwin" else 1024))
        values = {key: int(value.split()[0]) for key, value in (line.split(":", 1) for line in Path("/proc/self/io").read_text().splitlines())}
        result.update(read_bytes=values.get("read_bytes", 0), write_bytes=values.get("write_bytes", 0))
    except Exception as exc:  # pragma: no cover - platform dependent
        result.update(available=False, error=f"posix_telemetry_unavailable:{type(exc).__name__}:{exc}")
    return result


def _measure(action: Callable[[], T]) -> tuple[T, dict[str, int | float | bool | str | None]]:
    before = _process_snapshot()
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    value = action()
    wall, cpu = time.perf_counter() - wall_start, time.process_time() - cpu_start
    after = _process_snapshot()
    available = bool(before["available"]) and bool(after["available"])
    errors = [str(item) for item in (before["error"], after["error"]) if item]
    return value, {
        "wall_seconds": wall, "cpu_seconds": cpu, "cpu_utilization_fraction": cpu / wall if wall else 0.0,
        "telemetry_available": available, "telemetry_error": None if available else "|".join(errors),
        "peak_rss_bytes": max(int(before["peak_rss_bytes"]), int(after["peak_rss_bytes"])),
        "io_read_bytes": max(0, int(after["read_bytes"]) - int(before["read_bytes"])),
        "io_write_bytes": max(0, int(after["write_bytes"]) - int(before["write_bytes"])),
    }


@contextmanager
def _isolated_native_cache(cache_root: Path) -> Iterator[None]:
    """Redirect only this fixture benchmark's source-keyed native cache."""
    cache_root = Path(cache_root).resolve()
    original_root = native._resolved_build_root
    with native._LIBRARY_LOCK:
        original_libraries = dict(native._WARM_LIBRARIES)
        native._WARM_LIBRARIES.clear()

    def resolved_build_root(build_root: str | Path | None) -> Path:
        # The benchmark has no caller-facing build-root API.  Keeping this
        # monkey patch local lets process-cold and warm measurements share one
        # caller-owned disposable cache without touching the default cache.
        return cache_root

    native._resolved_build_root = resolved_build_root
    try:
        yield
    finally:
        native._resolved_build_root = original_root
        with native._LIBRARY_LOCK:
            native._WARM_LIBRARIES.clear()
            native._WARM_LIBRARIES.update(original_libraries)


def _claim_rows(pre_n: int, post_n: int, salt: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple((rank + clock + salt) % 6 for rank in range(pre_n if clock < 6 else post_n)) for clock in range(16))


def _cases(width: int) -> tuple[EpisodeTape, ...]:
    if width not in WIDTHS:
        raise ValueError("width must be one of 1, 8, 32")
    expansion_keys = tuple(range(100, 107))
    expansion = EpisodeTape(
        FixtureSpec(expansion_keys, (3, 19, 34, 52, 68, 87, 103), expansion_keys + (107, 108), (-1,) * 7 + (-2, -2), ACTIVE_CONTINUATION),
        _claim_rows(7, 9, 0),
        (43, 116),
    )
    contraction_keys = tuple(range(200, 209))
    contraction = EpisodeTape(FixtureSpec(contraction_keys, (1, 14, 28, 41, 55, 70, 84, 99, 113), (200, 201, 203, 204, 206, 207, 208), (-1,) * 7, NEW_EPOCH, 10, 3), _claim_rows(9, 7, 2))
    static_keys = tuple(range(300, 311))
    static = EpisodeTape(FixtureSpec(static_keys, (2, 12, 23, 35, 46, 57, 69, 80, 91, 103, 114), static_keys, (-1,) * 11, NEW_EPOCH, 15, 5), _claim_rows(11, 11, 4))
    perfect = EpisodeTape(FixtureSpec(tuple(range(6)), (0, 20, 40, 60, 80, 100), tuple(range(6)), (-1,) * 6), tuple((0, 1, 2, 3, 4, 5) for _ in range(16)))
    templates = (expansion, contraction, static, perfect)
    return tuple(templates[index % len(templates)] for index in range(width))


def _run_width(width: int, repetitions: int) -> dict[str, object]:
    cases = _cases(width)
    oracle, native_times = [], []
    exact = terminal = True
    for _ in range(repetitions):
        expected, oracle_time = _measure(lambda: run_oracle_batch(cases))
        observed, native_time = _measure(lambda: native.run_native_trace_batch(cases))
        oracle.append(oracle_time); native_times.append(native_time)
        exact = exact and expected == observed
        terminal = terminal and all(trace[-1].terminal for trace in observed)
    ticks = width * 64 * repetitions
    wall = sum(float(item["wall_seconds"]) for item in native_times)
    return {"batch_width": width, "repetitions": repetitions, "ticks": ticks, "call_order": ["oracle", "native"],
            "oracle": oracle, "native": native_times, "ticks_per_second": ticks / wall if wall else 0.0,
            "exact_oracle_native_equality": exact, "full_reset_to_terminal": terminal}


def _order_and_chunk_checks() -> tuple[bool, bool]:
    cases = _cases(32)
    together = native.run_native_trace_batch(cases)
    scalar = tuple(native.run_native_trace_batch((case,))[0] for case in cases)
    chunks = tuple(trace for start in range(0, 32, 8) for trace in native.run_native_trace_batch(cases[start:start + 8]))
    return together == scalar, together == chunks


def _abi2_event_lifecycle_check() -> dict[str, bool]:
    """Exercise t24 event installation and keep transport linkage out of public input."""
    cases = _cases(8)
    batch = native.reset_native_batch(tuple(case.fixture for case in cases))
    try:
        snapshots = batch.snapshots
        for tick in range(24):
            actions = tuple(
                native.StepInput(case.claims_by_clock[tick // 4]) if tick % 4 == 0 else native.StepInput()
                for case in cases
            )
            snapshots = batch.step(actions)
        pre_event = snapshots
        pre_ready = all(snapshot.tick == 24 and snapshot.event_input_required and not snapshot.claim_required for snapshot in pre_event)
        pre_private = all(
            len(snapshot.transport_keys) == len(snapshot.positions)
            and len(set(snapshot.transport_keys)) == len(snapshot.transport_keys)
            for snapshot in pre_event
        )
        post_event = batch.apply_event(tuple(native.EventInput(case.event_newcomer_positions) for case in cases))
        post_ready = all(
            not snapshot.event_input_required and snapshot.claim_required
            and len(snapshot.transport_keys) == len(snapshot.positions)
            and len(set(snapshot.transport_keys)) == len(snapshot.transport_keys)
            for snapshot in post_event
        )
        survivor_transport = all(
            set(after.transport_keys) == set(case.fixture.after_keys)
            and (set(before.transport_keys) & set(case.fixture.after_keys)).issubset(
                set(after.transport_keys)
            )
            for before, after, case in zip(pre_event, post_event, cases)
        )
        public_without_keys = all(
            not hasattr(snapshot.public_observation(), "transport_keys")
            for snapshot in post_event
        )
        return {
            "pre_event_observed": pre_ready,
            "apply_event_batch_observed": post_ready,
            "stable_transport_alignment": pre_private and survivor_transport,
            "model_public_inputs_exclude_transport_keys": public_without_keys,
        }
    finally:
        if not batch.closed:
            batch.close()


def _fixture_model_inputs() -> tuple[torch.nn.Module, object, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Build one fixed 64-episode/8,192-decision construction fixture."""
    model = make_conformance_fixture_model()
    agent = torch.arange(UPDATE_EPISODES * 12 * 3, dtype=torch.float64).reshape(UPDATE_EPISODES, 12, 3) / 100.0
    beacon = torch.arange(UPDATE_EPISODES * 6 * 3, dtype=torch.float64).reshape(UPDATE_EPISODES, 6, 3) / 100.0
    context = torch.zeros((UPDATE_EPISODES, 4), dtype=torch.float64)
    manager = model.manager(agent, beacon, context)
    repeats = UPDATE_AGENT_DECISIONS // UPDATE_EPISODES
    if repeats * UPDATE_EPISODES != UPDATE_AGENT_DECISIONS:
        raise RuntimeError("representative decision count must divide the fixture episode count")
    return model, manager, context, manager.pooled_summary.repeat_interleave(repeats, dim=0), manager.public_summary.repeat_interleave(repeats, dim=0)


def _model_fixture_work() -> dict[str, bool | int]:
    """Measure a deterministic representative update without retaining model state."""
    model, manager, context, pooled, public = _fixture_model_inputs()
    sample = torch.full_like(manager.mean, 0.125)
    score = stopped_normal_log_density(sample, manager.mean, manager.raw_log_scale)
    decisions = pooled.shape[0]
    own = torch.zeros((decisions, 5), dtype=torch.float64)
    candidate = torch.zeros((decisions, UPDATE_CANDIDATE_SCORES, 4), dtype=torch.float64)
    plan = sample.repeat_interleave(decisions // UPDATE_EPISODES, dim=0)
    pointer = make_pointer_inputs(pooled, own, context.repeat_interleave(decisions // UPDATE_EPISODES, dim=0), candidate, stopped_actor_plan(plan))
    claims = torch.zeros(decisions, dtype=torch.int64)
    actor = selected_claim_log_probability(model.claim_probabilities(pointer), claims)
    flex_plan, common, agent_delta = model.event_plan(FLEX, plan, public, own, torch.zeros((decisions, 4), dtype=torch.float64))
    loss = score.mean() + actor.mean() + flex_plan.square().mean()
    loss.backward()
    gradients = tuple(parameter.grad for parameter in model.parameters())
    norm_squared = sum(float(gradient.square().sum().item()) for gradient in gradients if gradient is not None)
    fixed_norm_scale = 0.01 / max(norm_squared ** 0.5, 0.01)
    with torch.no_grad():
        for parameter in model.parameters():
            if parameter.grad is not None:
                parameter.add_(parameter.grad, alpha=-fixed_norm_scale)
    return {"deterministic_fixture": True, "episodes": UPDATE_EPISODES,
            "agent_decisions": UPDATE_AGENT_DECISIONS, "candidate_scores_per_decision": UPDATE_CANDIDATE_SCORES,
            "stopped_normal_score_path": model.manager_mean.weight.grad is not None,
            "actor_path": model.pointer_score.weight.grad is not None, "flex_path": common is not None and agent_delta is not None,
            "backward_completed": any(gradient is not None for gradient in gradients), "fixed_norm_update_completed": True}


def _heldout_forward_fixture_work() -> dict[str, bool | int]:
    """Exercise the fixed-width learned consumer forward path only."""
    model, _, context, pooled, _ = _fixture_model_inputs()
    decisions = pooled.shape[0]
    own = torch.zeros((decisions, 5), dtype=torch.float64)
    candidate = torch.zeros((decisions, UPDATE_CANDIDATE_SCORES, 4), dtype=torch.float64)
    plan = torch.full((decisions, 4), 0.125, dtype=torch.float64)
    pointer = make_pointer_inputs(pooled, own, context.repeat_interleave(decisions // UPDATE_EPISODES, dim=0), candidate, stopped_actor_plan(plan))
    probabilities = model.claim_probabilities(pointer)
    return {"deterministic_fixture": True, "agent_decisions": decisions,
            "candidate_scores_per_decision": UPDATE_CANDIDATE_SCORES,
            "forward_completed": bool(torch.isfinite(probabilities).all())}


def _scripted_fixture_work() -> dict[str, bool | int]:
    positions, beacons, demand = (0, 20, 40, 60, 80, 100), (0, 20, 40, 60, 80, 100), (1, 1, 1, 1, 1, 1)
    for _ in range(SCRIPTED_MEASUREMENT_REPETITIONS):
        for _ in range(16):
            coherent_scaffold(positions, beacons, demand)
            fragmented_scaffold(positions, beacons, demand, active_churn=True, post_event_claim_index=0)
            independent_nearest(positions, beacons)
    return {"completed": True, "fixture_repetitions": SCRIPTED_MEASUREMENT_REPETITIONS,
            "claim_clocks_per_fixture": 16, "claim_clocks": 16 * SCRIPTED_MEASUREMENT_REPETITIONS,
            "package_consumers": 3, "consumer_calls": 48 * SCRIPTED_MEASUREMENT_REPETITIONS}


def _fixture_source_digest() -> str:
    """Bind every temporary payload to this revision-scoped fixture source."""
    return compute_source_digest(
        {"benchmark": b"fixture-only", "schema": ANALYZER_SCHEMA_VERSION, "revision": SCIENCE_REVISION}
    )


def _synthetic_records(source_digest: str) -> list[dict[str, object]]:
    guards = {
        "complete_construction": True,
        "host_component": FIXTURE_HOST_COMPONENT,
        "host_source_digest": source_digest,
        "treatment_fidelity": True,
        "analytic_containment": True,
        "evaluation_adaptation": False,
        "forbidden_information": False,
        "unregistered_coordinate": False,
        "learned_arms": list(LEARNED_PACKAGES),
        "scripted_packages": list(SCRIPTED_PACKAGES),
        "training_cells": list(TRAINING_CELLS),
        "heldout_cells": list(HELDOUT_CELLS),
    }
    record: dict[str, object] = {
        "schema_version": ANALYZER_SCHEMA_VERSION,
        "revision": SCIENCE_REVISION,
        "source_digest": source_digest,
        "fixture_only": True,
        "non_scientific": True,
        "construction_guards": guards,
        "prerequisite": {name: 1.0 for name in PREREQUISITE_VARIABLES},
        "direct_value": {name: 0.0 for name in DIRECT_VALUE_VARIABLES},
        "mechanism": {name: 0.0 for name in MECHANISM_VARIABLES},
    }
    return [
        record.copy() | {
            "construction_guards": dict(guards),
            "prerequisite": dict(record["prerequisite"]),
            "direct_value": dict(record["direct_value"]),
            "mechanism": dict(record["mechanism"]),
        }
        for _ in range(BLOCK_COUNT)
    ]


def _analyzer_fixture_work() -> dict[str, object]:
    source_digest = _fixture_source_digest()
    records = _synthetic_records(source_digest)
    outcome = None
    for _ in range(ANALYZER_MEASUREMENT_INVOCATIONS):
        outcome = analyze_fixture_records(records, expected_source_digest=source_digest)
    if outcome is None:
        raise RuntimeError("analyzer fixture invocation count must be positive")
    return {"synthetic_tail_count": TAIL_COUNT, "fixture_only": outcome.fixture_only,
            "non_scientific": outcome.non_scientific, "completed": outcome.valid_complete_fixture,
            "analyzer_invocations": ANALYZER_MEASUREMENT_INVOCATIONS,
            "schema_identity_verified": outcome.schema_version == ANALYZER_SCHEMA_VERSION
            and outcome.revision == SCIENCE_REVISION and outcome.source_digest == source_digest,
            "construction_guards_verified": outcome.valid_complete_fixture,
            "interpretation_value_exposed": False}


def _frontier(label: str) -> SyntheticFrontier:
    digest = _fixture_source_digest()
    return SyntheticFrontier(
        label,
        digest,
        {arm: make_synthetic_model_state_manifest(arm, digest) for arm in LEARNED_PACKAGES},
        {package: make_scripted_panel_manifest(package, digest) for package in SCRIPTED_PACKAGES},
        make_baseline_manifest(digest),
        make_semantic_position_manifest(digest),
        LEARNED_PACKAGES,
        make_aggregate_manifest(digest),
    )


def _serialization_timing(workspace: Path) -> dict[str, object]:
    root = create_fixture_root(workspace / "frontier-root")
    source_digest = _fixture_source_digest()
    _, commit = _measure(
        lambda: tuple(
            publish_synthetic_frontier(root, _frontier(f"synthetic_fixture_benchmark_{index:02d}"))
            for index in range(ATOMIC_RUN_BLOCKS)
        )
    )
    restored, scan = _measure(lambda: scan_resume_root(root, expected_source_digest=source_digest))
    durable = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    scratch = max((path.stat().st_size for path in workspace.rglob("*") if path.is_file() and path.is_relative_to(root) is False), default=0)
    return {"atomic_write": commit, "resume_scan_restore": scan, "run_blocks": ATOMIC_RUN_BLOCKS,
            "resume_exact": len(restored) == ATOMIC_RUN_BLOCKS and all(item.fixture_only and item.non_scientific for item in restored),
            "durable_bytes": durable, "scratch_bytes_peak": scratch, "empirical_runner_measured": False}


def _cold_probe(cache_root: Path) -> dict[str, int | float | bool | str | None]:
    with _isolated_native_cache(cache_root):
        _, measurement = _measure(native.require_cpp_batched_backend)
    return {**measurement, "isolated_cache": True}


def _cold_subprocess(cache_root: Path) -> dict[str, int | float | bool | str | None]:
    command = [sys.executable, str(Path(__file__).resolve()), "--cold-probe", "--cache-root", str(cache_root)]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError("isolated native cold probe did not complete")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict) or value.get("isolated_cache") is not True:
        raise RuntimeError("isolated native cold probe emitted an invalid record")
    return value


def _write_output(path: Path, value: dict[str, object]) -> None:
    path = Path(path).resolve(); path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(f".{path.name}.pending")
    with pending.open("xb") as stream:
        stream.write(_canonical(value)); stream.flush(); os.fsync(stream.fileno())
    os.replace(pending, path)


def _project_component(
    name: str, measurement: dict[str, object], *, measured_units: int, total_units: int, batch_size: int
) -> dict[str, object]:
    if measured_units <= 0 or total_units <= 0:
        raise ValueError("projection units must be positive")
    multiplier = total_units / measured_units
    measured_cpu = float(measurement["cpu_seconds"])
    cpu_basis = measured_cpu if measured_cpu > 0.0 else WINDOWS_PROCESS_CPU_RESOLUTION_SECONDS
    return {
        "name": name,
        "measured_units": measured_units,
        "total_units": total_units,
        "measured_batch_size": batch_size,
        "multiplier": multiplier,
        "measurement": measurement,
        "cpu_basis_seconds": cpu_basis,
        "cpu_basis_kind": "measured" if measured_cpu > 0.0 else "timer_resolution_upper_bound",
        "projected_wall_seconds": float(measurement["wall_seconds"]) * multiplier,
        "projected_cpu_seconds": cpu_basis * multiplier,
    }


def _envelope_relation(value: float, low: float, high: float) -> str:
    return "below" if value < low else "above" if value > high else "within"


def _select_fastest_width(rows: list[dict[str, object]]) -> dict[str, object]:
    """Choose the measured maximum; exact ties deliberately prefer less width."""
    if not rows:
        raise ValueError("at least one accepted width measurement is required")
    return max(
        rows,
        key=lambda row: (float(row["ticks_per_second"]), -int(row["batch_width"])),
    )


def run_benchmark(*, repetitions: int = 1, temp_root: Path | None = None) -> dict[str, object]:
    """Run bounded construction fixtures only; all writes remain below ``temp_root``."""
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or not 1 <= repetitions <= 7:
        raise ValueError("repetitions must be an integer in 1..7")
    parent = None if temp_root is None else Path(temp_root).resolve()
    if parent is not None: parent.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="rcle_tbcfv_efficiency_", dir=parent))
    cold = _cold_subprocess(workspace / "cold-cache")
    # Re-enter the exact cache populated by the isolated process so this is a
    # true first warm load, followed by process-local warm reuse.
    with _isolated_native_cache(workspace / "cold-cache"):
        _, warm_initial = _measure(native.require_cpp_batched_backend)
        _, warm_reuse = _measure(native.require_cpp_batched_backend)
        widths = [_run_width(width, repetitions) for width in WIDTHS]
        order_equal, chunk_equal = _order_and_chunk_checks()
        abi = native.native_abi_identity()
        contract = native.backend_contract()
        if abi.get("abi_version") != 2 or native.NATIVE_ABI_VERSION != 2:
            raise RuntimeError("ABI1 identity is rejected; the benchmark requires ABI2")
        if contract.get("event_time_newcomer_position_input") is not True or contract.get("transport_keys_actor_model_visible") is not False:
            raise RuntimeError("ABI2 event/transport contract is incomplete")
        event_lifecycle = _abi2_event_lifecycle_check()
        identity = {"source_sha256": native.native_source_sha256(), "abi": abi, "contract": contract}
    model_detail, model_measurement = _measure(_model_fixture_work)
    heldout_detail, heldout_measurement = _measure(_heldout_forward_fixture_work)
    scripted_detail, scripted_measurement = _measure(_scripted_fixture_work)
    analyzer_detail, analyzer_measurement = _measure(_analyzer_fixture_work)
    serialization = _serialization_timing(workspace)
    selected, baseline = _select_fastest_width(widths), widths[0]
    native_measurements = [item for row in widths for item in row["native"]]
    selected_wall = sum(float(item["wall_seconds"]) for item in selected["native"])
    selected_cpu = sum(float(item["cpu_seconds"]) for item in selected["native"])
    selected_measurement: dict[str, object] = {
        "wall_seconds": selected_wall,
        "cpu_seconds": selected_cpu,
        "telemetry_available": all(item["telemetry_available"] is True for item in selected["native"]),
        "telemetry_error": next((item["telemetry_error"] for item in selected["native"] if item["telemetry_available"] is not True), None),
        "peak_rss_bytes": max(int(item["peak_rss_bytes"]) for item in selected["native"]),
        "io_read_bytes": sum(int(item["io_read_bytes"]) for item in selected["native"]),
        "io_write_bytes": sum(int(item["io_write_bytes"]) for item in selected["native"]),
    }
    io_measurement: dict[str, object] = {
        "wall_seconds": float(serialization["atomic_write"]["wall_seconds"]) + float(serialization["resume_scan_restore"]["wall_seconds"]),
        "cpu_seconds": float(serialization["atomic_write"]["cpu_seconds"]) + float(serialization["resume_scan_restore"]["cpu_seconds"]),
        "telemetry_available": serialization["atomic_write"]["telemetry_available"] is True and serialization["resume_scan_restore"]["telemetry_available"] is True,
        "telemetry_error": serialization["atomic_write"]["telemetry_error"] or serialization["resume_scan_restore"]["telemetry_error"],
        "peak_rss_bytes": max(int(serialization["atomic_write"]["peak_rss_bytes"]), int(serialization["resume_scan_restore"]["peak_rss_bytes"])),
        "io_read_bytes": int(serialization["atomic_write"]["io_read_bytes"]) + int(serialization["resume_scan_restore"]["io_read_bytes"]),
        "io_write_bytes": int(serialization["atomic_write"]["io_write_bytes"]) + int(serialization["resume_scan_restore"]["io_write_bytes"]),
    }
    components = [
        _project_component("cold_load_per_worker", cold, measured_units=1, total_units=1, batch_size=1),
        _project_component(f"native_host_width_{selected['batch_width']}", selected_measurement, measured_units=int(selected["ticks"]), total_units=FULL_PANEL_TICKS, batch_size=int(selected["batch_width"])),
        _project_component("learned_update_forward_backward", model_measurement, measured_units=1, total_units=LEARNED_UPDATES, batch_size=UPDATE_EPISODES),
        _project_component("learned_heldout_forward", heldout_measurement, measured_units=int(heldout_detail["agent_decisions"]), total_units=HELDOUT_AGENT_DECISIONS, batch_size=UPDATE_AGENT_DECISIONS),
        _project_component("scripted_claim_clock_consumers", scripted_measurement, measured_units=int(scripted_detail["consumer_calls"]), total_units=SCRIPTED_CLAIM_CLOCK_CALLS, batch_size=int(scripted_detail["claim_clocks"])),
        _project_component("synthetic_72_tail_analyzer", analyzer_measurement, measured_units=int(analyzer_detail["analyzer_invocations"]), total_units=1, batch_size=BLOCK_COUNT),
        _project_component("atomic_publish_resume", io_measurement, measured_units=ATOMIC_RUN_BLOCKS, total_units=ATOMIC_RUN_BLOCKS, batch_size=ATOMIC_RUN_BLOCKS),
    ]
    one_worker_wall = sum(float(component["projected_wall_seconds"]) for component in components)
    one_worker_cpu = sum(float(component["projected_cpu_seconds"]) for component in components)
    cold_wall, cold_cpu = float(components[0]["projected_wall_seconds"]), float(components[0]["projected_cpu_seconds"])
    other_wall, other_cpu = one_worker_wall - cold_wall, one_worker_cpu - cold_cpu
    four_worker_wall = cold_wall * 4 + other_wall / 4
    four_worker_cpu = cold_cpu * 4 + other_cpu
    dominant_component = max(components, key=lambda component: float(component["projected_wall_seconds"]))
    measurements: list[dict[str, object]] = [cold, warm_initial, warm_reuse, model_measurement, heldout_measurement, scripted_measurement, analyzer_measurement, serialization["atomic_write"], serialization["resume_scan_restore"], selected_measurement, *native_measurements]
    telemetry_complete = all(item.get("telemetry_available") is True and int(item.get("peak_rss_bytes", 0)) > 0 for item in measurements)
    equality_complete = all(row["exact_oracle_native_equality"] and row["full_reset_to_terminal"] for row in widths) and order_equal and chunk_equal
    serialization_complete = bool(serialization["resume_exact"])
    event_lifecycle_complete = all(event_lifecycle.values())
    component_equivalence = equality_complete and event_lifecycle_complete and bool(model_detail["backward_completed"]) and bool(model_detail["fixed_norm_update_completed"]) and bool(heldout_detail["forward_completed"]) and bool(scripted_detail["completed"]) and bool(analyzer_detail["schema_identity_verified"]) and bool(analyzer_detail["construction_guards_verified"]) and serialization_complete
    review = "COMPLETE" if telemetry_complete and component_equivalence else "REPAIR_REQUIRED"
    return {
        "schema": SCHEMA,
        "fixture_only": True, "formal_activity": False, "scientific_output_exposed": False, "empirical_runner_measured": False,
        "python_oracle_only": True, "python_fallback": False,
        "command": {"repetitions": repetitions, "batch_widths": list(WIDTHS), "bounded_fixture_only": True},
        "compile_load": {"process_cold": cold, "warm_loader_initial": warm_initial, "warm_loader_reuse": warm_reuse},
        "component_identity": identity,
        "batched_reset_to_terminal": widths,
        "abi2_event_lifecycle": event_lifecycle,
        "model_forward_backward": {"measurement": model_measurement, **model_detail},
        "learned_heldout_forward": {"measurement": heldout_measurement, **heldout_detail},
        "scripted_consumers": {"measurement": scripted_measurement, **scripted_detail, "outcome_values_exposed": False},
        "synthetic_72_tail_analyzer": {"measurement": analyzer_measurement, **analyzer_detail},
        "atomic_write_resume": serialization,
        "chain_coverage": {"environment": equality_complete, "abi2_event_lifecycle": event_lifecycle_complete, "loader": True, "batch": True, "forward_backward": bool(model_detail["backward_completed"]), "fixed_norm_update": bool(model_detail["fixed_norm_update_completed"]), "rollout": equality_complete, "learned_heldout_forward": bool(heldout_detail["forward_completed"]), "evaluation": bool(scripted_detail["completed"]), "analyzer": bool(analyzer_detail["schema_identity_verified"]), "io": serialization_complete, "resume": serialization_complete, "telemetry_complete": telemetry_complete},
        "semantic_equivalence": {"all_widths_exact": all(row["exact_oracle_native_equality"] for row in widths), "all_widths_terminal": all(row["full_reset_to_terminal"] for row in widths), "scalar_order_exact": order_equal, "chunk_order_exact": chunk_equal, "abi2_event_lifecycle_exact": event_lifecycle_complete},
        "baseline_optimized_summary": {"baseline_batch_width": 1, "baseline_ticks_per_second": baseline["ticks_per_second"], "selected_batch_width": selected["batch_width"], "selected_ticks_per_second": selected["ticks_per_second"], "selection_rule": "maximum measured ticks_per_second; exact ties choose lower batch width"},
        "projected_full_panel_cost": {
            "basis": "sum of named deterministic fixture components scaled only by frozen workload counts",
            "uncertainty": "fixture-only measurements use no empirical runner; four-worker range assumes independent equivalence-preserving workers and excludes unimplemented orchestration overhead",
            "frozen_component_counts": {"learned_arm_run_block_updates": LEARNED_UPDATES, "learned_heldout_agent_decisions": HELDOUT_AGENT_DECISIONS, "scripted_claim_clock_consumer_calls": SCRIPTED_CLAIM_CLOCK_CALLS, "native_host_ticks": FULL_PANEL_TICKS, "analyzer_invocations": 1, "atomic_run_blocks": ATOMIC_RUN_BLOCKS, "cold_loads_per_worker": 1},
            "components": components,
            "wall_seconds": {"one_worker": one_worker_wall, "up_to_four_equivalence_supported": {"lower": four_worker_wall, "upper": one_worker_wall}},
            "cpu_seconds": {"one_worker": one_worker_cpu, "up_to_four_workers": four_worker_cpu},
            "measured_resource_basis": {"rss_per_worker_bytes": max(int(item.get("peak_rss_bytes", 0)) for item in measurements), "measured_read_bytes": sum(int(item.get("io_read_bytes", 0)) for item in measurements), "measured_write_bytes": sum(int(item.get("io_write_bytes", 0)) for item in measurements), "durable_fixture_bytes_for_20_blocks": serialization["durable_bytes"], "scratch_fixture_bytes_peak": serialization["scratch_bytes_peak"]},
            "prior_envelope_comparison": {"cpu_core_hours": [80, 180], "wall_hours_up_to_four_workers": [24, 60], "rss_gib_per_worker": [2, 4], "durable_gib": [0.25, 1], "scratch_gib": [4, 12]},
            "material_delta": {"cpu_core_hours_relation": _envelope_relation(one_worker_cpu / 3600.0, 80.0, 180.0), "up_to_four_worker_wall_hours_relation": _envelope_relation(four_worker_wall / 3600.0, 24.0, 60.0), "reason": "this replaces the prior host-only multiplication with all measured fixture-chain components"},
        },
        "rollback_nodes": {"native_backend": "candidate-local C++ host", "batch_width": {"selected": selected["batch_width"], "fallback": 1, "selection_rule": "maximum measured ticks_per_second; exact ties choose lower batch width"}, "loader_cache": "source-keyed isolated cache", "consumer": "deterministic fixture only", "io": "atomic frontier plus exact scan"},
        "efficiency_review": review, "lease_readiness": "WITHHOLD", "dominant_projected_component": {"name": dominant_component["name"], "wall_seconds": dominant_component["projected_wall_seconds"]},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", "--repeats", dest="repetitions", type=int, default=1)
    parser.add_argument("--temp-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cold-probe", action="store_true")
    parser.add_argument("--cache-root", type=Path)
    args = parser.parse_args()
    if args.cold_probe:
        if args.cache_root is None: parser.error("--cold-probe requires --cache-root")
        print(_canonical(_cold_probe(args.cache_root)).decode("utf-8"), end="")
        return 0
    value = run_benchmark(repetitions=args.repetitions, temp_root=args.temp_root)
    if args.output is not None: _write_output(args.output, value)
    print(_canonical(value).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
