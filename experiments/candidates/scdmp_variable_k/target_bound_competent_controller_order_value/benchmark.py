"""Result-blind TEST-only full-chain efficiency harness for TBCC revision 02.

This module deliberately creates no scientific master, identity, coordinate,
controller instance, checkpoint, training/evaluation record, result, or lease.
All tensors and filesystem payloads are deterministic disposable fixtures.
"""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from typing import Callable, Iterable, TypeVar

import torch

from . import native_backend as native
from .config import (
    FORMATION_ROTATE,
    FUNCTIONAL_BATCH_WIDTHS,
    HOOK_HANDOFF,
)
from .contracts import ACTION_COUNT, AdamWState, adamw_step
from .controller_conformance import (
    free_logits,
    graph_slack_scores,
    reversed_compositor,
    set_scores,
    treat_logits,
)
from .host_types import HostOutput, RenewalLane, ResetLane, constant_disturbance_lane
from .oracle import (
    TestOnlyState,
    test_only_output,
    test_only_renewal,
    test_only_reset,
)
from .opportunity import (
    ACTION_COUNT as OPPORTUNITY_ACTION_COUNT,
    DisturbanceTape,
    OpportunityContractError,
    OpportunityState,
    PairOpportunityMetrics,
    REPLICATE_PAIR_COUNT,
    RolloutAddress,
    aggregate_replicate,
    analyze_gate,
    load_test_only_complete_opportunity_stage,
    publish_test_only_complete_opportunity_stage,
    resume_test_only_complete_opportunity_stage,
    run_complete_pair,
)
from .lifecycle import GateOutcome, TechnicalFinal, issue_opportunity_execution_permit, snapshot
from .synthetic_resume import (
    SyntheticFrontier,
    cold_scan_exact_frontier,
    commit_frontier,
    create_only_commit,
    fake_digest,
    require_complete_synthetic_stage,
    write_interrupted_test_fragment,
)


SCHEMA = "SCDMP-TBCC-R02-RESULT-BLIND-EFFICIENCY-V1"
WIDTHS = (1, 8, 12, 32, 120, 144)
NATURAL_WIDTHS = (12, 120, 144)
CONTROLLERS = ("FOUNDATION", "TREAT", "FREE", "REVERSED", "SET")
FULL_WORKLOAD = {
    "episodes_rollouts": 343_296,
    "allocated_primitive_slots": 124_959_744,
    "maximum_policy_queries": 15_829_632,
    "forced_first_action_interventions": 110_592,
    "adamw_steps": 129_024,
    "final_learned_checkpoints": 96,
}
STAGE_UNIT_MULTIPLIERS = {
    "foundation_update": 24 * 160,
    "competence_cell": 24 * 6,
    "opportunity_state": 24 * 2 * 16,
    "order_update": 24 * 3 * 96,
    "final_evaluation_cell": 5 * 24 * 6,
}
SUSTAINED_TOTAL_WORK_UNITS = 64
PRIOR_RETAINED_EFFICIENCY_EVIDENCE = {
    "schema": "SCDMP_TBCC_R02_RETAINED_EFFICIENCY_PROVENANCE_V1",
    "immutable": True,
    "historical_whole_file_sha256": "91d3a16009f68891b0402464783954e35ca03dea1aa7d85c85b3165135d0a2cf",
    "historical_record_path": "runtime/benchmarks/scdmp_tbcc_r02_efficiency_20260821.json",
    "historical_path_bytes_still_present": False,
    "historical_digest_does_not_describe_current_path_bytes": True,
    "measured_effective_speedup": 3.034772909220757,
    "projected_cpu_core_hours": 2.0266105726403127,
    "projected_measured_wall_hours": 0.6677964491124604,
    "evidence_scope": "pre_Stage1b_refresh_sustained_1_2_4_worker_result_blind_record",
}
_T = TypeVar("_T")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def _process_snapshot() -> dict[str, int | bool | str | None]:
    result: dict[str, int | bool | str | None] = {
        "available": True,
        "error": None,
        "rss_bytes": 0,
        "peak_rss_bytes": 0,
        "read_bytes": 0,
        "write_bytes": 0,
    }
    if os.name == "nt":
        try:
            from ctypes import wintypes

            class Memory(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("page_fault_count", wintypes.DWORD),
                    ("peak_working_set_size", ctypes.c_size_t),
                    ("working_set_size", ctypes.c_size_t),
                    ("quota_peak_paged_pool_usage", ctypes.c_size_t),
                    ("quota_paged_pool_usage", ctypes.c_size_t),
                    ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
                    ("quota_non_paged_pool_usage", ctypes.c_size_t),
                    ("pagefile_usage", ctypes.c_size_t),
                    ("peak_pagefile_usage", ctypes.c_size_t),
                ]

            class Io(ctypes.Structure):
                _fields_ = [
                    ("read_operation_count", ctypes.c_ulonglong),
                    ("write_operation_count", ctypes.c_ulonglong),
                    ("other_operation_count", ctypes.c_ulonglong),
                    ("read_transfer_count", ctypes.c_ulonglong),
                    ("write_transfer_count", ctypes.c_ulonglong),
                    ("other_transfer_count", ctypes.c_ulonglong),
                ]

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel.GetCurrentProcess.argtypes = []
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Memory), wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            kernel.GetProcessIoCounters.argtypes = [wintypes.HANDLE, ctypes.POINTER(Io)]
            kernel.GetProcessIoCounters.restype = wintypes.BOOL
            handle = kernel.GetCurrentProcess()
            memory = Memory()
            memory.cb = ctypes.sizeof(memory)
            io = Io()
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo")
            if not kernel.GetProcessIoCounters(handle, ctypes.byref(io)):
                raise OSError(ctypes.get_last_error(), "GetProcessIoCounters")
            result.update(
                rss_bytes=int(memory.working_set_size),
                peak_rss_bytes=int(memory.peak_working_set_size),
                read_bytes=int(io.read_transfer_count),
                write_bytes=int(io.write_transfer_count),
            )
            return result
        except Exception as error:  # pragma: no cover - platform API dependent
            result.update(available=False, error=f"windows_telemetry_unavailable:{type(error).__name__}:{error}")
            return result
    try:  # pragma: no cover - Windows is the assigned host
        import resource

        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        peak *= 1 if sys.platform == "darwin" else 1024
        result.update(rss_bytes=peak, peak_rss_bytes=peak)
        io_rows = {
            key: int(value.split()[0])
            for key, value in (line.split(":", 1) for line in Path("/proc/self/io").read_text().splitlines())
        }
        result.update(read_bytes=io_rows.get("read_bytes", 0), write_bytes=io_rows.get("write_bytes", 0))
    except Exception as error:
        result.update(available=False, error=f"posix_telemetry_unavailable:{type(error).__name__}:{error}")
    return result


def _measure(action: Callable[[], _T]) -> tuple[_T, dict[str, int | float | bool | str | None]]:
    before = _process_snapshot()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    value = action()
    wall = time.perf_counter() - wall_start
    cpu = time.process_time() - cpu_start
    after = _process_snapshot()
    telemetry = bool(before["available"]) and bool(after["available"])
    return value, {
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "cpu_utilization_fraction": cpu / wall if wall else 0.0,
        "telemetry_available": telemetry,
        "telemetry_error": None if telemetry else "|".join(str(item) for item in (before["error"], after["error"]) if item),
        "rss_bytes": int(after["rss_bytes"]),
        "peak_rss_bytes": max(int(before["peak_rss_bytes"]), int(after["peak_rss_bytes"])),
        "io_read_bytes": max(0, int(after["read_bytes"]) - int(before["read_bytes"])),
        "io_write_bytes": max(0, int(after["write_bytes"]) - int(before["write_bytes"])),
    }


def _reset_rows(width: int, *, all_active: bool = False) -> tuple[ResetLane, ...]:
    if width not in WIDTHS and width != 32:
        raise ValueError("unregistered benchmark width")
    rows = []
    for lane in range(width):
        graph_one = lane < (width + 1) // 2
        rows.append(
            ResetLane(
                middle_events=(HOOK_HANDOFF, FORMATION_ROTATE) if graph_one else (FORMATION_ROTATE, HOOK_HANDOFF),
                k_initial=13,
                initial_v=0.017,
                initial_y=-0.004,
                initial_phi=0.006,
                active=all_active or width == 1 or lane % 11 != 7,
            )
        )
    return tuple(rows)


def _renewal_row(action: int, *, active: bool, lane: int, renewal: int) -> RenewalLane:
    sign = 1 if (lane + renewal) % 2 == 0 else -1
    return constant_disturbance_lane(
        action,
        eta_v=sign * 0.003,
        eta_y=-sign * 0.002,
        eta_omega=sign * 0.004,
        active=active,
    )


_DISCRETE_FIELDS = (
    "advanced", "active", "terminal", "ticks_advanced", "tick", "hold_k", "next_k",
    "safe_dock", "timeout", "cable_overload", "gantry_contact", "attitude_loss",
    "formation_loss", "energy_ticks", "dock_tick",
)


def _compare_outputs(observed: HostOutput, expected: HostOutput) -> float:
    for name in _DISCRETE_FIELDS:
        if getattr(observed, name) != getattr(expected, name):
            raise RuntimeError(f"oracle/native discrete mismatch: {name}")
    pairs = tuple(zip(observed.observation, expected.observation)) + (
        (observed.cumulative_reward, expected.cumulative_reward),
        (observed.cumulative_energy, expected.cumulative_energy),
    )
    maximum = max(abs(left - right) for left, right in pairs)
    if maximum > 2e-14:
        raise RuntimeError(f"oracle/native numeric mismatch: {maximum}")
    return maximum


def _endpoint_digest(outputs: Iterable[HostOutput]) -> str:
    payload = [
        {name: getattr(output, name) for name in _DISCRETE_FIELDS}
        for output in outputs
    ]
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _endpoint_inventory(outputs: Iterable[HostOutput]) -> dict[str, int]:
    rows = tuple(outputs)
    return {
        "lanes": len(rows),
        "terminal": sum(int(row.terminal) for row in rows),
        "safe_dock": sum(int(row.safe_dock) for row in rows),
        "timeout": sum(int(row.timeout) for row in rows),
        "cable_overload": sum(int(row.cable_overload) for row in rows),
        "gantry_contact": sum(int(row.gantry_contact) for row in rows),
        "attitude_loss": sum(int(row.attitude_loss) for row in rows),
        "formation_loss": sum(int(row.formation_loss) for row in rows),
        "energy_ticks": sum(row.energy_ticks for row in rows),
        "terminal_ticks": sum(row.tick for row in rows),
    }


def _native_chain(width: int) -> dict[str, object]:
    resets = _reset_rows(width, all_active=True)
    transitions = 0
    renewals = 0
    masked_positions: tuple[int, ...] = ()
    with native.NativeBatch(resets) as batch:
        outputs = batch.initial
        while any(output.active for output in outputs):
            rows = tuple(
                _renewal_row(12 if renewals == 0 and lane == 0 else 0, active=output.active, lane=lane, renewal=renewals)
                for lane, output in enumerate(outputs)
            )
            prior_active = tuple(output.active for output in outputs)
            outputs = batch.renew(rows)
            transitions += sum(output.ticks_advanced for active, output in zip(prior_active, outputs) if active)
            renewals += 1
        final = outputs
    return {
        "primitive_transitions": transitions,
        "renewal_batches": renewals,
        "masked_reset_positions": list(masked_positions),
        "absorbed_positions": [index for index, output in enumerate(final) if output.terminal and index not in masked_positions],
        "endpoint_digest": _endpoint_digest(final),
        "endpoint_inventory": _endpoint_inventory(final),
        "all_active_lanes_terminal": all(output.terminal for index, output in enumerate(final) if index not in masked_positions),
        "lane_positions_preserved": len(final) == width,
    }


def _oracle_chain(width: int) -> dict[str, object]:
    resets = _reset_rows(width, all_active=True)
    states: list[TestOnlyState] = [test_only_reset(row) for row in resets]
    outputs: list[HostOutput] = [test_only_output(state, advanced=0, hold_k=0) for state in states]
    transitions = 0
    renewals = 0
    while any(output.active for output in outputs):
        next_outputs: list[HostOutput] = []
        for lane, (state, prior) in enumerate(zip(states, outputs)):
            if not prior.active:
                next_outputs.append(prior)
                continue
            row = _renewal_row(12 if renewals == 0 and lane == 0 else 0, active=True, lane=lane, renewal=renewals)
            hold = state.current_k
            state, advanced = test_only_renewal(state, row)
            states[lane] = state
            transitions += advanced
            next_outputs.append(test_only_output(state, advanced=advanced, hold_k=hold))
        outputs = next_outputs
        renewals += 1
    return {
        "primitive_transitions": transitions,
        "renewal_batches": renewals,
        "endpoint_digest": _endpoint_digest(outputs),
        "outputs": tuple(outputs),
    }


def _mask_check(width: int) -> dict[str, object]:
    resets = _reset_rows(width)
    masked = [index for index, row in enumerate(resets) if not row.active]
    with native.NativeBatch(resets) as batch:
        initial = batch.initial
        first_rows = tuple(
            _renewal_row(12 if lane == 0 else 0, active=output.active, lane=lane, renewal=0)
            for lane, output in enumerate(initial)
        )
        first = batch.renew(first_rows)
        second_rows = tuple(
            _renewal_row(0, active=output.active, lane=lane, renewal=1)
            for lane, output in enumerate(first)
        )
        second = batch.renew(second_rows)
    frozen_masked = all(first[index] == initial[index] == second[index] for index in masked)
    absorbed = [index for index, output in enumerate(first) if output.terminal]
    frozen_absorbed = all(second[index] == first[index] for index in absorbed)
    return {
        "masked_reset_positions": masked,
        "absorbed_positions_after_first_hold": absorbed,
        "masked_positions_frozen": frozen_masked,
        "absorbed_positions_frozen": frozen_absorbed,
        "lane_positions_preserved": len(initial) == len(first) == len(second) == width,
    }


def _width_measurement(width: int, repeats: int) -> dict[str, object]:
    expected = _oracle_chain(width)
    observed = _native_chain(width)
    if expected["endpoint_digest"] != observed["endpoint_digest"]:
        raise RuntimeError("oracle/native endpoint accounting differs")
    oracle_times = []
    native_times = []
    for _ in range(repeats):
        _, oracle_timing = _measure(lambda: _oracle_chain(width))
        _, native_timing = _measure(lambda: _native_chain(width))
        oracle_times.append(oracle_timing)
        native_times.append(native_timing)
    transitions = int(observed["primitive_transitions"])
    oracle_wall = sum(float(item["wall_seconds"]) for item in oracle_times)
    native_wall = sum(float(item["wall_seconds"]) for item in native_times)
    # One direct renewal equality pass checks every state, not just endpoints.
    resets = _reset_rows(width, all_active=True)
    states = [test_only_reset(row) for row in resets]
    expected_outputs = [test_only_output(state, advanced=0, hold_k=0) for state in states]
    max_abs = 0.0
    with native.NativeBatch(resets) as batch:
        for left, right in zip(batch.initial, expected_outputs):
            max_abs = max(max_abs, _compare_outputs(left, right))
        native_outputs = batch.initial
        renewal = 0
        while any(output.active for output in native_outputs):
            rows = tuple(
                _renewal_row(12 if renewal == 0 and lane == 0 else 0, active=output.active, lane=lane, renewal=renewal)
                for lane, output in enumerate(native_outputs)
            )
            next_expected = []
            for lane, (state, prior) in enumerate(zip(states, expected_outputs)):
                if not prior.active:
                    next_expected.append(prior)
                    continue
                hold = state.current_k
                state, advanced = test_only_renewal(state, rows[lane])
                states[lane] = state
                next_expected.append(test_only_output(state, advanced=advanced, hold_k=hold))
            native_outputs = batch.renew(rows)
            for left, right in zip(native_outputs, next_expected):
                max_abs = max(max_abs, _compare_outputs(left, right))
            expected_outputs = next_expected
            renewal += 1
    mask = _mask_check(width)
    return {
        "width": width,
        "repeats": repeats,
        "fixture_oracle": oracle_times,
        "optimized_native": native_times,
        "oracle_transitions_per_second": transitions * repeats / oracle_wall,
        "native_transitions_per_second": transitions * repeats / native_wall,
        "native_speedup": oracle_wall / native_wall,
        "primitive_transitions_per_run": transitions,
        "full_reset_to_terminal": True,
        "oracle_native_equal": True,
        "maximum_absolute_float_difference": max_abs,
        "endpoint_digest": observed["endpoint_digest"],
        "masked_reset_positions": mask["masked_reset_positions"],
        "absorbed_positions": mask["absorbed_positions_after_first_hold"],
        "masked_positions_frozen": mask["masked_positions_frozen"],
        "absorbed_positions_frozen": mask["absorbed_positions_frozen"],
        "lane_positions_preserved": mask["lane_positions_preserved"],
    }


class _Foundation(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.actor = torch.nn.Sequential(torch.nn.Linear(18, 96), torch.nn.SiLU(), torch.nn.Linear(96, 96), torch.nn.SiLU(), torch.nn.Linear(96, 18))
        self.critic = torch.nn.Sequential(torch.nn.Linear(18, 96), torch.nn.SiLU(), torch.nn.Linear(96, 96), torch.nn.SiLU(), torch.nn.Linear(96, 1))


class _Scale(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.Sequential(torch.nn.Linear(18, 32), torch.nn.SiLU(), torch.nn.Linear(32, 1))

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        return torch.relu(self.layers(observation).squeeze(1))


class _OrderCritic(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.Sequential(torch.nn.Linear(19, 64), torch.nn.SiLU(), torch.nn.Linear(64, 64), torch.nn.SiLU(), torch.nn.Linear(64, 1))

    def forward(self, observation: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        return self.layers(torch.cat((observation, q[:, None]), dim=1)).squeeze(1)


class _Residual(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.Sequential(torch.nn.Linear(19, 64), torch.nn.SiLU(), torch.nn.Linear(64, 64), torch.nn.SiLU(), torch.nn.Linear(64, 18))

    def forward(self, observation: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        return self.layers(torch.cat((observation, q[:, None]), dim=1))


def _fixture_modules() -> tuple[_Foundation, _Scale, _OrderCritic, _Residual]:
    modules = (_Foundation(), _Scale(), _OrderCritic(), _Residual())
    offset = 0
    with torch.no_grad():
        for module in modules:
            for parameter in module.parameters():
                values = torch.arange(offset, offset + parameter.numel(), dtype=torch.float32).reshape(parameter.shape)
                parameter.copy_(torch.sin(values * 0.00017) * 0.01)
                offset += parameter.numel()
    return modules


def _fixture_inputs(width: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    values = torch.arange(width * 18, dtype=torch.float32).reshape(width, 18)
    observation = torch.sin(values * 0.013) * 0.2
    observation[:, 0] = torch.linspace(0.0, 0.9, width)
    observation[:, 17] = torch.linspace(0.0, 0.95, width)
    q = (torch.arange(width) % 2).to(torch.float32)
    k = torch.where(torch.arange(width) % 2 == 0, torch.tensor(7), torch.tensor(13)).to(torch.int64)
    active = torch.arange(width) % 11 != 7
    if width == 1:
        active[:] = True
    return observation, q, k, active


def _controller_forward(
    kind: str,
    modules: tuple[_Foundation, _Scale, _OrderCritic, _Residual],
    observation: torch.Tensor,
    q: torch.Tensor,
    k: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    foundation, scale, critic, residual = modules
    base = foundation.actor(observation)
    if kind == "FOUNDATION":
        return base, foundation.critic(observation).squeeze(1)
    compositor_q = reversed_compositor(q).compositor_q if kind == "REVERSED" else q
    if kind == "SET":
        network_q = torch.full_like(q, 0.5)
        scores = set_scores(observation, k)
    else:
        network_q = compositor_q
        scores = graph_slack_scores(observation, compositor_q, k)
    logits = treat_logits(base, scale(observation), scores)
    if kind in ("FREE", "SET"):
        logits = free_logits(logits, residual(observation, network_q))
    return logits, critic(observation, network_q)


def _tensor_digest(values: Iterable[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for value in values:
        contiguous = value.detach().to(torch.float32).contiguous().cpu()
        digest.update(str(tuple(contiguous.shape)).encode("ascii"))
        digest.update(contiguous.numpy().tobytes())
    return digest.hexdigest()


def _forward_measurement(width: int, repeats: int) -> dict[str, object]:
    torch.set_num_threads(1)
    modules = _fixture_modules()
    observation, q, k, active = _fixture_inputs(width)
    rows = torch.nonzero(active, as_tuple=False).squeeze(1)
    output: dict[str, object] = {}
    for kind in CONTROLLERS:
        def batched() -> str:
            tensors: list[torch.Tensor] = []
            with torch.no_grad():
                for _ in range(repeats):
                    tensors.extend(_controller_forward(kind, modules, observation[rows], q[rows], k[rows]))
            return _tensor_digest(tensors[-2:])

        def scalar() -> str:
            tensors: list[torch.Tensor] = []
            with torch.no_grad():
                for index in rows.tolist():
                    tensors.extend(_controller_forward(kind, modules, observation[index:index + 1], q[index:index + 1], k[index:index + 1]))
            return _tensor_digest(tensors)

        scalar_digest, scalar_timing = _measure(scalar)
        batch_digest, batch_timing = _measure(batched)
        # Scalar concatenation and batch layout differ, so equality is checked row-wise once.
        with torch.no_grad():
            batch_values = _controller_forward(kind, modules, observation[rows], q[rows], k[rows])
            scalar_values = tuple(
                torch.cat([_controller_forward(kind, modules, observation[index:index + 1], q[index:index + 1], k[index:index + 1])[position] for index in rows.tolist()], dim=0)
                for position in (0, 1)
            )
        maximum_difference = max(
            float(torch.max(torch.abs(left - right)).item())
            for left, right in zip(batch_values, scalar_values)
        )
        equal = maximum_difference <= 2e-6
        if not equal:
            raise RuntimeError(f"scalar/batched {kind} fixture forward differs")
        output[kind] = {
            "active_rows": len(rows),
            "scalar_baseline": scalar_timing,
            "batched_optimized": batch_timing,
            "batched_rows_per_second": len(rows) * repeats / float(batch_timing["wall_seconds"]),
            "scalar_to_batched_speedup": float(scalar_timing["wall_seconds"]) * repeats / float(batch_timing["wall_seconds"]),
            "scalar_digest": scalar_digest,
            "batched_digest": batch_digest,
            "rowwise_semantic_equal": True,
            "rowwise_maximum_absolute_difference": maximum_difference,
        }
    return {"width": width, "active_mask_positions": rows.tolist(), "controllers": output}


def _training_kernel(kind: str, width: int, steps: int = 12) -> dict[str, object]:
    torch.set_num_threads(1)
    modules = _fixture_modules()
    observation, q, k, active = _fixture_inputs(width)
    rows = torch.nonzero(active, as_tuple=False).squeeze(1)
    foundation, scale, critic, residual = modules
    if kind == "FOUNDATION":
        parameters = tuple(foundation.parameters())
    elif kind == "ORDER":
        parameters = tuple(scale.parameters()) + tuple(critic.parameters()) + tuple(residual.parameters())
        for parameter in foundation.parameters():
            parameter.requires_grad_(False)
    else:
        raise ValueError("unknown fixture training kernel")
    optimizer = torch.optim.AdamW(parameters, lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-5)

    def execute() -> str:
        last: tuple[torch.Tensor, ...] = ()
        for step in range(steps):
            optimizer.zero_grad(set_to_none=True)
            if kind == "FOUNDATION":
                logits, values = _controller_forward("FOUNDATION", modules, observation[rows], q[rows], k[rows])
            else:
                logits, values = _controller_forward("FREE", modules, observation[rows], q[rows], k[rows])
            target = torch.sin(torch.arange(logits.numel(), dtype=torch.float32).reshape_as(logits) * 0.007 + step * 0.01)
            loss = (logits - target).square().mean() + 0.5 * values.square().mean() - 0.01 * torch.softmax(logits, 1).clamp_min(1e-12).log().mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(parameters, 0.8)
            optimizer.step()
            last = (logits, values)
        return _tensor_digest(last + tuple(parameter for parameter in parameters))

    digest, timing = _measure(execute)
    return {
        "kind": kind,
        "width": width,
        "active_rows": len(rows),
        "adamw_steps": steps,
        "measurement": timing,
        "steps_per_second": steps / float(timing["wall_seconds"]),
        "fixture_digest": digest,
        "persistent_optimizer_indices": [1, steps],
        "global_gradient_clip": 0.8,
    }


def _integrated_unit(name: str, width: int, controller: str, *, forced_first: bool, optimizer_kind: str | None) -> dict[str, object]:
    torch.set_num_threads(1)
    modules = _fixture_modules()
    resets = _reset_rows(width, all_active=True)

    def execute() -> dict[str, object]:
        queries = 0
        interventions = 0
        transitions = 0
        renewal = 0
        final: tuple[HostOutput, ...]
        with native.NativeBatch(resets) as batch:
            outputs = batch.initial
            while any(output.active for output in outputs):
                active_indices = [index for index, output in enumerate(outputs) if output.active]
                actions = [0] * width
                if forced_first and renewal == 0:
                    for index in active_indices:
                        actions[index] = (index // 4) % ACTION_COUNT
                    interventions += len(active_indices)
                else:
                    observation = torch.tensor([outputs[index].observation for index in active_indices], dtype=torch.float32)
                    q = torch.tensor([1.0 if resets[index].middle_events[0] == HOOK_HANDOFF else 0.0 for index in active_indices], dtype=torch.float32)
                    k = torch.tensor([outputs[index].next_k for index in active_indices], dtype=torch.int64)
                    with torch.no_grad():
                        logits, _ = _controller_forward(controller, modules, observation, q, k)
                        actions_tensor = torch.argmax(logits, dim=1)
                    for position, index in enumerate(active_indices):
                        actions[index] = int(actions_tensor[position])
                    queries += len(active_indices)
                rows = tuple(_renewal_row(actions[index], active=output.active, lane=index, renewal=renewal) for index, output in enumerate(outputs))
                prior_active = tuple(output.active for output in outputs)
                outputs = batch.renew(rows)
                transitions += sum(output.ticks_advanced for active, output in zip(prior_active, outputs) if active)
                renewal += 1
            final = outputs
        return {
            "policy_queries": queries,
            "forced_interventions": interventions,
            "primitive_transitions": transitions,
            "renewal_batches": renewal,
            "endpoint_digest": _endpoint_digest(final),
            "endpoint_inventory": _endpoint_inventory(final),
        }

    payload, timing = _measure(execute)
    optimizer = None if optimizer_kind is None else _training_kernel(optimizer_kind, width, 12)
    total_wall = float(timing["wall_seconds"]) + (0.0 if optimizer is None else float(optimizer["measurement"]["wall_seconds"]))
    total_cpu = float(timing["cpu_seconds"]) + (0.0 if optimizer is None else float(optimizer["measurement"]["cpu_seconds"]))
    return {
        "unit": name,
        "width": width,
        "controller_path": controller,
        "fixture_only": True,
        "complete_reset_to_terminal": True,
        "allocated_episodes": width,
        "allocated_primitive_slots": width * 364,
        **payload,
        "rollout_measurement": timing,
        "optimizer_kernel": optimizer,
        "combined_wall_seconds": total_wall,
        "combined_cpu_seconds": total_cpu,
        "scientific_payload_retained": False,
    }


def _ordered_lane_address_proof(global_ordinal: int) -> dict[str, object]:
    if global_ordinal not in range(SUSTAINED_TOTAL_WORK_UNITS):
        raise ValueError("worker proof ordinal lies outside the exact TEST address space")
    resets = _reset_rows(12, all_active=True)
    inventory: list[dict[str, object]] = []
    snapshots: list[dict[str, object]] = []
    with native.NativeBatch(resets) as batch:
        outputs = batch.initial
        for renewal in range(4):
            rows = []
            for lane, output in enumerate(outputs):
                action = (lane + 3 * renewal + global_ordinal) % ACTION_COUNT
                row = _renewal_row(action, active=output.active, lane=lane, renewal=renewal)
                rows.append(row)
                if output.active:
                    inventory.append(
                        {
                            "ordinal": len(inventory),
                            "global_ordinal": global_ordinal,
                            "lane": lane,
                            "renewal": renewal,
                            "pre_tick": output.tick,
                            "hold_k": output.next_k,
                            "action": action,
                            "eta_v_sign": 1 if row.eta_v[0] > 0 else -1,
                            "eta_y_sign": 1 if row.eta_y[0] > 0 else -1,
                            "eta_omega_sign": 1 if row.eta_omega[0] > 0 else -1,
                        }
                    )
            outputs = batch.renew(tuple(rows))
            snapshots.append(
                {
                    "renewal": renewal,
                    "endpoint_digest": _endpoint_digest(outputs),
                    "endpoint_inventory": _endpoint_inventory(outputs),
                }
            )
    return {
        "schema": "TEST_ONLY_TBCC_ORDERED_LANE_ADDRESS_PROOF_V1",
        "global_ordinal": global_ordinal,
        "width": 12,
        "renewal_batches": 4,
        "ordered_inventory": inventory,
        "ordered_inventory_count": len(inventory),
        "ordered_inventory_sha256": hashlib.sha256(_canonical(inventory)).hexdigest(),
        "endpoint_snapshots": snapshots,
    }


def _controller_tensor_proof(global_ordinal: int) -> dict[str, object]:
    torch.set_num_threads(1)
    modules = _fixture_modules()
    observation, q, k, active = _fixture_inputs(12)
    observation = observation + torch.tensor(global_ordinal * 1e-6, dtype=torch.float32)
    rows = torch.nonzero(active, as_tuple=False).squeeze(1)
    controllers: dict[str, object] = {}
    with torch.no_grad():
        for kind in CONTROLLERS:
            logits, values = _controller_forward(kind, modules, observation[rows], q[rows], k[rows])
            controllers[kind] = {
                "logits_shape": list(logits.shape),
                "values_shape": list(values.shape),
                "tensor_sha256": _tensor_digest((logits, values)),
            }
    return {
        "schema": "TEST_ONLY_TBCC_CONTROLLER_TENSOR_PROOF_V1",
        "global_ordinal": global_ordinal,
        "active_lane_inventory": rows.tolist(),
        "controllers": controllers,
    }


def _optimizer_arithmetic_proof(global_ordinal: int) -> dict[str, object]:
    parameter = torch.linspace(-0.5, 0.5, 32, dtype=torch.float32)
    state = AdamWState(torch.zeros_like(parameter), torch.zeros_like(parameter), 0)
    step_inventory = []
    for step in range(1, 4):
        gradient = torch.sin(
            torch.arange(32, dtype=torch.float32) * 0.17
            + step * 0.11
            + global_ordinal * 0.001
        )
        parameter, state = adamw_step(parameter, gradient, state)
        step_inventory.append(
            {
                "step": state.step,
                "parameter_sha256": _tensor_digest((parameter,)),
                "moment_sha256": _tensor_digest((state.moment,)),
                "variance_sha256": _tensor_digest((state.variance,)),
            }
        )
    return {
        "schema": "TEST_ONLY_TBCC_ADAMW_ARITHMETIC_PROOF_V1",
        "global_ordinal": global_ordinal,
        "arithmetic": "float32_beta1_0.9_beta2_0.999_eps_1e-8_lr_3e-4_weight_decay_1e-5",
        "step_inventory": step_inventory,
        "final_step": state.step,
        "final_state_sha256": _tensor_digest((parameter, state.moment, state.variance)),
    }


def _worker_ordinal_proof(global_ordinal: int, unit: dict[str, object]) -> dict[str, object]:
    stage_endpoint = {
        "global_ordinal": global_ordinal,
        "unit": unit["unit"],
        "controller_path": unit["controller_path"],
        "allocated_episodes": unit["allocated_episodes"],
        "allocated_primitive_slots": unit["allocated_primitive_slots"],
        "policy_queries": unit["policy_queries"],
        "forced_interventions": unit["forced_interventions"],
        "primitive_transitions": unit["primitive_transitions"],
        "renewal_batches": unit["renewal_batches"],
        "endpoint_digest": unit["endpoint_digest"],
        "endpoint_inventory": unit["endpoint_inventory"],
    }
    row = {
        "schema": "TEST_ONLY_TBCC_WORKER_ORDINAL_PROOF_ROW_V1",
        "global_ordinal": global_ordinal,
        "fixture_only": True,
        "question_relevant": False,
        "opportunity_assay_executed": False,
        "ordered_lane_address": _ordered_lane_address_proof(global_ordinal),
        "controller_tensors": _controller_tensor_proof(global_ordinal),
        "optimizer_state_arithmetic": _optimizer_arithmetic_proof(global_ordinal),
        "stage_endpoint_counts": stage_endpoint,
    }
    return {
        "row": row,
        "canonical_sha256": hashlib.sha256(_canonical(row)).hexdigest(),
    }


def _worker_payload(ordinal_start: int, ordinal_stop: int) -> dict[str, object]:
    if (
        isinstance(ordinal_start, bool)
        or isinstance(ordinal_stop, bool)
        or not 0 <= ordinal_start < ordinal_stop <= SUSTAINED_TOTAL_WORK_UNITS
    ):
        raise ValueError("worker ordinal range must be a nonempty subset of [0,64)")
    ordinals = tuple(range(ordinal_start, ordinal_stop))
    torch.set_num_threads(1)
    native.require_cpp_batched_backend()

    def execute() -> dict[str, object]:
        units = [
            _integrated_unit(
                "TEST_ONLY_FOUNDATION_SUSTAINED_UNIT"
                if ordinal % 2 == 0
                else "TEST_ONLY_FINAL_CONTROLLER_SUSTAINED_UNIT",
                120,
                "FOUNDATION" if ordinal % 2 == 0 else "FREE",
                forced_first=False,
                optimizer_kind=None,
            )
            for ordinal in ordinals
        ]
        proof_rows = [
            _worker_ordinal_proof(ordinal, unit)
            for ordinal, unit in zip(ordinals, units)
        ]
        ordered_rows = [value["row"] for value in proof_rows]
        return {
            "policy_queries": sum(int(row["policy_queries"]) for row in units),
            "primitive_transitions": sum(int(row["primitive_transitions"]) for row in units),
            "local_proof_inventory": {
                "schema": "TEST_ONLY_TBCC_WORKER_LOCAL_ORDINAL_INVENTORY_V1",
                "ordinal_start": ordinal_start,
                "ordinal_stop": ordinal_stop,
                "ordinals": list(ordinals),
                "row_sha256": [value["canonical_sha256"] for value in proof_rows],
                "ordered_rows": ordered_rows,
                "ordered_frontier_sha256": hashlib.sha256(_canonical(ordered_rows)).hexdigest(),
            },
        }

    payload, measurement = _measure(execute)
    return {
        **payload,
        "work_units": len(ordinals),
        "sustained_warm_measurement": measurement,
        "work_units_per_second": len(ordinals) / float(measurement["wall_seconds"]),
        "torch_threads": torch.get_num_threads(),
    }


def _outer_worker_measurement(worker_count: int, *, total_work_units: int) -> dict[str, object]:
    if total_work_units < worker_count or total_work_units % worker_count != 0:
        raise ValueError("sustained total work must divide evenly across workers")
    units_per_worker = total_work_units // worker_count
    ranges = tuple(
        (index * units_per_worker, (index + 1) * units_per_worker)
        for index in range(worker_count)
    )
    before = _process_snapshot()
    started = time.perf_counter()
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "tools.benchmarks.benchmark_scdmp_tbcc_r02_native",
                "--worker-child",
                "--worker-ordinal-start",
                str(start),
                "--worker-ordinal-stop",
                str(stop),
            ],
            cwd=Path(__file__).resolve().parents[4],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for start, stop in ranges
    ]
    rows = []
    for process in processes:
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"outer worker fixture failed: {stderr}")
        rows.append(json.loads(stdout))
    wall = time.perf_counter() - started
    after = _process_snapshot()
    local_inventories = [row["local_proof_inventory"] for row in rows]
    merged_rows: list[dict[str, object]] = []
    observed_ordinals: list[int] = []
    local_inventories_valid = True
    for expected_range, inventory in zip(ranges, local_inventories):
        local_rows = inventory.get("ordered_rows")
        local_ordinals = inventory.get("ordinals")
        local_hashes = inventory.get("row_sha256")
        valid = (
            inventory.get("schema") == "TEST_ONLY_TBCC_WORKER_LOCAL_ORDINAL_INVENTORY_V1"
            and (inventory.get("ordinal_start"), inventory.get("ordinal_stop")) == expected_range
            and local_ordinals == list(range(*expected_range))
            and isinstance(local_rows, list)
            and isinstance(local_hashes, list)
            and len(local_rows) == len(local_ordinals) == len(local_hashes)
            and all(
                row_value.get("global_ordinal") == ordinal
                and hashlib.sha256(_canonical(row_value)).hexdigest() == digest
                for ordinal, row_value, digest in zip(local_ordinals, local_rows, local_hashes)
            )
            and inventory.get("ordered_frontier_sha256") == hashlib.sha256(_canonical(local_rows)).hexdigest()
        )
        local_inventories_valid = local_inventories_valid and valid
        if isinstance(local_rows, list) and isinstance(local_ordinals, list):
            merged_rows.extend(local_rows)
            observed_ordinals.extend(int(value) for value in local_ordinals)
    merged_rows.sort(key=lambda value: int(value["global_ordinal"]))
    exact_partition = (
        local_inventories_valid
        and observed_ordinals == list(range(total_work_units))
        and len(set(observed_ordinals)) == total_work_units
        and [int(value["global_ordinal"]) for value in merged_rows] == list(range(total_work_units))
    )
    merged_frontier_sha256 = hashlib.sha256(_canonical(merged_rows)).hexdigest()
    steady_wall = max(float(row["sustained_warm_measurement"]["wall_seconds"]) for row in rows)
    summed_cpu = sum(float(row["sustained_warm_measurement"]["cpu_seconds"]) for row in rows)
    return {
        "outer_workers": worker_count,
        "total_work_units": total_work_units,
        "work_units_per_worker": units_per_worker,
        "torch_threads_per_worker": 1,
        "startup_inclusive_wall_seconds": wall,
        "sustained_warm_wall_seconds": steady_wall,
        "aggregate_work_units_per_second": total_work_units / steady_wall,
        "aggregate_policy_queries_per_second": sum(int(row["policy_queries"]) for row in rows) / steady_wall,
        "aggregate_primitive_transitions_per_second": sum(int(row["primitive_transitions"]) for row in rows) / steady_wall,
        "summed_worker_cpu_seconds": summed_cpu,
        "aggregate_cpu_utilization_fraction": summed_cpu / steady_wall if steady_wall else 0.0,
        "maximum_worker_peak_rss_bytes": max(int(row["sustained_warm_measurement"]["peak_rss_bytes"]) for row in rows),
        "summed_worker_peak_rss_bytes": sum(int(row["sustained_warm_measurement"]["peak_rss_bytes"]) for row in rows),
        "parent_peak_rss_bytes": max(int(before["peak_rss_bytes"]), int(after["peak_rss_bytes"])),
        "io_read_bytes": sum(int(row["sustained_warm_measurement"]["io_read_bytes"]) for row in rows),
        "io_write_bytes": sum(int(row["sustained_warm_measurement"]["io_write_bytes"]) for row in rows),
        "worker_ordinal_ranges": [list(value) for value in ranges],
        "child_local_proof_inventories": local_inventories,
        "merged_ordered_frontier": merged_rows,
        "merged_ordered_frontier_sha256": merged_frontier_sha256,
        "merged_ordinal_inventory": list(range(total_work_units)) if exact_partition else observed_ordinals,
        "exact_disjoint_partition_complete": exact_partition,
        "deterministic_equal_within_group": exact_partition,
        "fixture_digest": merged_frontier_sha256,
        "startup_amortized": True,
    }


def _annotate_worker_scaling(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    baseline = next(row for row in rows if row["outer_workers"] == 1)
    baseline_rate = float(baseline["aggregate_work_units_per_second"])
    if baseline_rate <= 0:
        raise RuntimeError("one-worker sustained throughput must be positive")
    for row in rows:
        worker_count = int(row["outer_workers"])
        raw_speedup = float(row["aggregate_work_units_per_second"]) / baseline_rate
        effective_speedup = min(float(worker_count), raw_speedup)
        row["raw_speedup_vs_one_worker"] = raw_speedup
        row["effective_speedup_vs_one_worker"] = effective_speedup
        row["effective_speedup_bounded_by_worker_count"] = effective_speedup <= worker_count
        row["parallel_efficiency"] = effective_speedup / worker_count
    return rows


def _select_acceptance_worker_speedup(
    current_worker: dict[str, object],
    retained: dict[str, object] = PRIOR_RETAINED_EFFICIENCY_EVIDENCE,
) -> dict[str, object]:
    current = float(current_worker["effective_speedup_vs_one_worker"])
    prior = float(retained["measured_effective_speedup"])
    if current <= 0 or prior <= 0:
        raise RuntimeError("retained/current worker speedup must be positive")
    selected = min(current, prior)
    return {
        "selection_rule": "minimum_effective_speedup_across_retained_and_current_measured_runs",
        "retained_effective_speedup": prior,
        "current_effective_speedup": current,
        "acceptance_effective_speedup": selected,
        "acceptance_speedup_source": "retained_prior" if prior <= current else "current_measurement",
    }


def _validate_worker_semantic_proofs(rows: list[dict[str, object]]) -> dict[str, object]:
    if {int(row.get("outer_workers", 0)) for row in rows} != {1, 2, 4}:
        raise RuntimeError("worker semantic proof requires exact 1/2/4 partitions")
    ordered_groups = sorted(rows, key=lambda value: int(value["outer_workers"]))
    expected_ordinals = list(range(SUSTAINED_TOTAL_WORK_UNITS))
    frontiers = [row.get("merged_ordered_frontier") for row in ordered_groups]
    partition_complete = all(
        row.get("exact_disjoint_partition_complete") is True
        and row.get("merged_ordinal_inventory") == expected_ordinals
        and isinstance(frontier, list)
        and len(frontier) == SUSTAINED_TOTAL_WORK_UNITS
        and [item.get("global_ordinal") for item in frontier] == expected_ordinals
        and row.get("merged_ordered_frontier_sha256")
        == hashlib.sha256(_canonical(frontier)).hexdigest()
        for row, frontier in zip(ordered_groups, frontiers)
    )
    if not partition_complete:
        raise RuntimeError("worker ordinal partitions have gaps, overlaps, extras, or digest mismatch")
    reference = frontiers[0]
    all_frontiers_equal = all(frontier == reference for frontier in frontiers[1:])
    expected_digest = hashlib.sha256(_canonical(reference)).hexdigest()
    if not all_frontiers_equal or any(
        row.get("merged_ordered_frontier_sha256") != expected_digest
        for row in ordered_groups
    ):
        raise RuntimeError("worker merged frontier differs across 1/2/4 partitions")

    address_preserved = True
    controller_preserved = True
    optimizer_preserved = True
    stage_preserved = True
    endpoint_preserved = True
    opportunity_absent = True
    for ordinal, proof in enumerate(reference):
        if (
            not isinstance(proof, dict)
            or proof.get("schema") != "TEST_ONLY_TBCC_WORKER_ORDINAL_PROOF_ROW_V1"
            or proof.get("global_ordinal") != ordinal
            or proof.get("fixture_only") is not True
            or proof.get("question_relevant") is not False
        ):
            raise RuntimeError("worker ordinal proof row differs")
        address = proof.get("ordered_lane_address")
        controllers = proof.get("controller_tensors")
        optimizer = proof.get("optimizer_state_arithmetic")
        stage = proof.get("stage_endpoint_counts")
        if not all(isinstance(section, dict) for section in (address, controllers, optimizer, stage)):
            raise RuntimeError("worker ordinal proof section is absent")

        address_inventory = address.get("ordered_inventory")
        address_preserved = address_preserved and (
            address.get("global_ordinal") == ordinal
            and isinstance(address_inventory, list)
            and len(address_inventory) == address.get("ordered_inventory_count")
            and len(address_inventory) > 0
            and address.get("ordered_inventory_sha256")
            == hashlib.sha256(_canonical(address_inventory)).hexdigest()
            and all(
                item.get("ordinal") == local_ordinal
                and item.get("global_ordinal") == ordinal
                for local_ordinal, item in enumerate(address_inventory)
            )
        )
        controller_inventory = controllers.get("controllers")
        controller_preserved = controller_preserved and (
            controllers.get("global_ordinal") == ordinal
            and isinstance(controller_inventory, dict)
            and set(controller_inventory) == set(CONTROLLERS)
            and all(
                isinstance(item.get("tensor_sha256"), str)
                and len(item["tensor_sha256"]) == 64
                and item.get("logits_shape") == [11, 18]
                and item.get("values_shape") == [11]
                for item in controller_inventory.values()
            )
        )
        optimizer_steps = optimizer.get("step_inventory")
        optimizer_preserved = optimizer_preserved and (
            optimizer.get("global_ordinal") == ordinal
            and isinstance(optimizer_steps, list)
            and [item.get("step") for item in optimizer_steps] == [1, 2, 3]
            and optimizer.get("final_step") == 3
            and isinstance(optimizer.get("final_state_sha256"), str)
            and len(optimizer["final_state_sha256"]) == 64
            and all(
                all(
                    isinstance(item.get(key), str) and len(item[key]) == 64
                    for key in ("parameter_sha256", "moment_sha256", "variance_sha256")
                )
                for item in optimizer_steps
            )
        )
        expected_unit = (
            "TEST_ONLY_FOUNDATION_SUSTAINED_UNIT"
            if ordinal % 2 == 0
            else "TEST_ONLY_FINAL_CONTROLLER_SUSTAINED_UNIT"
        )
        expected_controller = "FOUNDATION" if ordinal % 2 == 0 else "FREE"
        endpoint_inventory = stage.get("endpoint_inventory")
        stage_preserved = stage_preserved and (
            stage.get("global_ordinal") == ordinal
            and stage.get("unit") == expected_unit
            and stage.get("controller_path") == expected_controller
            and stage.get("allocated_episodes") == 120
            and stage.get("allocated_primitive_slots") == 120 * 364
            and stage.get("forced_interventions") == 0
            and isinstance(stage.get("policy_queries"), int)
            and isinstance(stage.get("primitive_transitions"), int)
            and isinstance(stage.get("renewal_batches"), int)
        )
        endpoint_preserved = endpoint_preserved and (
            isinstance(stage.get("endpoint_digest"), str)
            and len(stage["endpoint_digest"]) == 64
            and isinstance(endpoint_inventory, dict)
            and endpoint_inventory.get("lanes") == stage.get("allocated_episodes")
            and endpoint_inventory.get("terminal") == stage.get("allocated_episodes")
        )
        opportunity_absent = opportunity_absent and proof.get("opportunity_assay_executed") is False
    derived = {
        "outer_worker_partitions_complete": partition_complete,
        "all_merged_frontiers_equal": all_frontiers_equal,
        "rng_address_order_preserved": address_preserved,
        "controller_tensor_outputs_preserved": controller_preserved,
        "optimizer_state_arithmetic_preserved": optimizer_preserved,
        "endpoint_counts_preserved": endpoint_preserved,
        "stage_counts_preserved": stage_preserved,
        "opportunity_assay_absent": opportunity_absent,
        "semantic_proof_sha256": expected_digest,
    }
    if not all(value is True for key, value in derived.items() if key != "semantic_proof_sha256"):
        raise RuntimeError("worker semantic proof is incomplete")
    return derived


class _TestOnlyOpportunityFoundation:
    """Frozen deterministic fixture policy; action 12 terminates the toy traces early."""

    def __init__(self) -> None:
        self.call_count = 0
        self.query_rows = 0
        self.wall_seconds = 0.0
        self._trace = hashlib.sha256()

    def __call__(self, observations: tuple[tuple[float, ...], ...]) -> tuple[tuple[float, ...], ...]:
        started = time.perf_counter()
        logits = tuple(
            tuple(1.0 if action == 12 else 0.0 for action in range(ACTION_COUNT))
            for _ in observations
        )
        self.call_count += 1
        self.query_rows += len(observations)
        self._trace.update(struct.pack("<Q", len(observations)))
        for observation, row in zip(observations, logits):
            self._trace.update(struct.pack("<18d", *(float(value) for value in observation)))
            self._trace.update(struct.pack("<18d", *row))
        self.wall_seconds += time.perf_counter() - started
        return logits

    @property
    def trace_sha256(self) -> str:
        return self._trace.hexdigest()


class _TrackedNativeOpportunitySession:
    def __init__(self, resets: Iterable[ResetLane], collector: dict[str, object]) -> None:
        rows = tuple(resets)
        started = time.perf_counter()
        self._batch = native.NativeBatch(rows)
        collector["native_wall_seconds"] = float(collector["native_wall_seconds"]) + (time.perf_counter() - started)
        collector["session_count"] = int(collector["session_count"]) + 1
        cast_widths = collector["widths"]
        assert isinstance(cast_widths, list)
        cast_widths.append(len(rows))
        self.initial = self._batch.initial
        self._last = self.initial
        self._collector = collector

    def renew(self, rows: Iterable[RenewalLane]) -> tuple[HostOutput, ...]:
        materialized = tuple(rows)
        active_positions = tuple(index for index, row in enumerate(materialized) if row.active)
        expected_active = tuple(index for index, output in enumerate(self._last) if output.active)
        if active_positions != expected_active:
            self._collector["masking_equal"] = False
            self._collector["mask_input_mismatch_calls"] = int(self._collector["mask_input_mismatch_calls"]) + 1
        trace = self._collector["mask_trace"]
        if not hasattr(trace, "update"):
            raise RuntimeError("opportunity mask trace is unavailable")
        trace.update(_canonical({"call": self._collector["renew_calls"], "active_positions": active_positions}))
        started = time.perf_counter()
        outputs = self._batch.renew(materialized)
        self._collector["native_wall_seconds"] = float(self._collector["native_wall_seconds"]) + (time.perf_counter() - started)
        self._collector["renew_calls"] = int(self._collector["renew_calls"]) + 1
        self._collector["primitive_transitions"] = int(self._collector["primitive_transitions"]) + sum(
            output.ticks_advanced
            for before, output in zip(self._last, outputs)
            if before.active
        )
        for before, after in zip(self._last, outputs):
            if not before.active:
                self._collector["masked_lane_rows"] = int(self._collector["masked_lane_rows"]) + 1
        self._last = outputs
        return outputs

    def close(self) -> None:
        started = time.perf_counter()
        self._batch.close()
        self._collector["native_wall_seconds"] = float(self._collector["native_wall_seconds"]) + (time.perf_counter() - started)


def _test_only_opportunity_tapes(k: int, state_index: int) -> tuple[DisturbanceTape, ...]:
    rows = []
    for tape_index in range(4):
        eta_v = tuple(0.003 if (tick + tape_index + state_index) % 2 == 0 else -0.003 for tick in range(364))
        eta_y = tuple(0.002 if (tick // (tape_index + 1) + k + state_index) % 2 == 0 else -0.002 for tick in range(364))
        eta_omega = tuple(0.004 if (tick + (tape_index + 1) * 3 + k) % 3 else -0.004 for tick in range(364))
        rows.append(
            DisturbanceTape(
                address=f"TEST_ONLY:TBCC:R02:OPPORTUNITY:k={k}:state={state_index}:tape={tape_index}",
                eta_v=eta_v,
                eta_y=eta_y,
                eta_omega=eta_omega,
            )
        )
    return tuple(rows)


def _private_pair_digest(pairs: Iterable[PairOpportunityMetrics]) -> str:
    payload = [
        {
            "replicate": row.replicate,
            "k": row.k,
            "state_index": row.state_index,
            "q": row.q_value,
            "d": row.d_value,
            "s": row.s_value,
            "argmax_q0": sorted(row.argmax_q0),
            "argmax_q1": sorted(row.argmax_q1),
            "tape_digests": list(row.tape_digests),
            "rollout_count": row.rollout_count,
        }
        for row in pairs
    ]
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _test_only_opportunity_permit():
    finals = tuple(
        TechnicalFinal(
            replicate,
            "FOUNDATION",
            fake_digest(f"TEST_ONLY:benchmark-foundation:{replicate}"),
        )
        for replicate in range(24)
    )
    return issue_opportunity_execution_permit(
        snapshot(finals, foundation_gate=GateOutcome.PASS)
    )


def _opportunity_service_measurement(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    permit = _test_only_opportunity_permit()
    collector: dict[str, object] = {
        "native_wall_seconds": 0.0,
        "session_count": 0,
        "renew_calls": 0,
        "primitive_transitions": 0,
        "masked_lane_rows": 0,
        "masking_equal": True,
        "mask_input_mismatch_calls": 0,
        "widths": [],
        "mask_trace": hashlib.sha256(),
    }
    foundation = _TestOnlyOpportunityFoundation()
    tapes_by_slot: list[dict[str, object]] = []

    def execute_replicate() -> tuple[PairOpportunityMetrics, ...]:
        pairs = []
        for k in (7, 13):
            for state_index in range(16):
                state = OpportunityState(
                    replicate=0,
                    k=k,
                    state_index=state_index,
                    initial_v=0.005 + 0.001 * (state_index % 11),
                    initial_y=-0.009 + 0.001 * (state_index % 16),
                    initial_phi=-0.009 + 0.001 * ((3 * state_index) % 16),
                )
                tapes = _test_only_opportunity_tapes(k, state_index)
                tape_digests = tuple(tape.digest for tape in tapes)
                tapes_by_slot.append({"k": k, "state_index": state_index, "tape_digests": tape_digests})
                pair = run_complete_pair(
                    state,
                    tapes,
                    permit=permit,
                    foundation=foundation,
                    session_factory=lambda resets: _TrackedNativeOpportunitySession(resets, collector),
                )
                if pair.tape_digests != tape_digests:
                    raise RuntimeError("opportunity service changed common tape bindings")
                pairs.append(pair)
        return tuple(pairs)

    pairs, service_timing = _measure(execute_replicate)
    aggregate, aggregate_timing = _measure(lambda: aggregate_replicate(pairs))
    replicas = tuple(
        aggregate_replicate(tuple(replace(pair, replicate=replicate) for pair in pairs))
        for replicate in range(24)
    )
    analysis, analyzer_timing = _measure(lambda: analyze_gate(replicas))
    private_analysis_digest = hashlib.sha256(
        _canonical(
            {
                "q": (analysis.q.mean, analysis.q.lower, analysis.q.standard_error, analysis.q.critical, analysis.q.sample_count),
                "d": (analysis.d.mean, analysis.d.lower, analysis.d.standard_error, analysis.d.critical, analysis.d.sample_count),
                "s": (analysis.s.mean, analysis.s.lower, analysis.s.standard_error, analysis.s.critical, analysis.s.sample_count),
                "passes": analysis.passes,
            }
        )
    ).hexdigest()

    inventory_path = root / "TEST_ONLY_COMPLETE_OPPORTUNITY_STAGE.json"
    _, publication_timing = _measure(
        lambda: publish_test_only_complete_opportunity_stage(
            inventory_path,
            replicas,
            permit=permit,
        )
    )
    loaded, load_timing = _measure(
        lambda: load_test_only_complete_opportunity_stage(inventory_path, permit=permit)
    )
    resumed, resume_timing = _measure(
        lambda: resume_test_only_complete_opportunity_stage(inventory_path, permit=permit)
    )
    partial_path = root / "TEST_ONLY_PARTIAL_OPPORTUNITY_STAGE.json"
    partial_rejected = False
    try:
        publish_test_only_complete_opportunity_stage(
            partial_path,
            replicas[:-1],
            permit=permit,
        )
    except OpportunityContractError:
        partial_rejected = not partial_path.exists()
    if (
        loaded != resumed
        or loaded.replicates != replicas
        or loaded.analysis != analysis
        or not partial_rejected
    ):
        raise RuntimeError("TEST-only opportunity stage publication/load/resume differs")

    address_inventory = tuple(
        (q, action, tape)
        for q in (0, 1)
        for action in range(OPPORTUNITY_ACTION_COUNT)
        for tape in range(4)
    )
    expected_rollouts = REPLICATE_PAIR_COUNT * len(address_inventory)
    if len(pairs) != REPLICATE_PAIR_COUNT or any(pair.rollout_count != len(address_inventory) for pair in pairs):
        raise RuntimeError("opportunity service produced an incomplete address inventory")
    exact_ties = any(len(pair.argmax_q0) > 1 or len(pair.argmax_q1) > 1 for pair in pairs)
    mask_trace = collector["mask_trace"]
    if not hasattr(mask_trace, "hexdigest"):
        raise RuntimeError("opportunity mask trace is unavailable")
    tape_inventory_digest = hashlib.sha256(_canonical(tapes_by_slot)).hexdigest()
    private_pair_digest = _private_pair_digest(pairs)
    record_bytes = inventory_path.stat().st_size
    actual_transitions = int(collector.get("primitive_transitions", 0))
    return {
        "schema": "TEST_ONLY_TBCC_STAGE1B_NATIVE_SERVICE_BENCHMARK_V1",
        "fixture_only": True,
        "question_relevant_output": False,
        "real_native_batch_service": True,
        "pair_count": REPLICATE_PAIR_COUNT,
        "rollouts_per_pair": len(address_inventory),
        "measured_replicate_rollouts": expected_rollouts,
        "measured_replicate_allocated_slots": expected_rollouts * 364,
        "measured_replicate_registered_query_ceiling": 4_313_088 // 24,
        "full_stage_rollouts": 110_592,
        "full_stage_allocated_slots": 40_255_488,
        "full_stage_registered_query_ceiling": 4_313_088,
        "address_inventory_sha256": hashlib.sha256(_canonical(address_inventory)).hexdigest(),
        "address_inventory_complete": len(address_inventory) == 144,
        "tape_inventory_sha256": tape_inventory_digest,
        "common_tape_binding_equal": all(
            len(set(item["tape_digests"])) == 4
            and pair.tape_digests == tuple(item["tape_digests"])
            for pair, item in zip(pairs, tapes_by_slot)
        ),
        "mask_trace_sha256": mask_trace.hexdigest(),
        "masked_lane_rows": collector["masked_lane_rows"],
        "mask_input_mismatch_calls": collector["mask_input_mismatch_calls"],
        "masking_and_lane_positions_equal": (
            collector["masking_equal"] is True
            and int(collector["mask_input_mismatch_calls"]) == 0
            and int(collector["masked_lane_rows"]) > 0
        ),
        "native_session_count": collector["session_count"],
        "native_widths_equal_144": set(collector["widths"]) == {144},
        "foundation_call_count": foundation.call_count,
        "foundation_query_rows_observed": foundation.query_rows,
        "foundation_trace_sha256": foundation.trace_sha256,
        "foundation_policy": "TEST_ONLY_frozen_deterministic_action12_unique_argmax",
        "foundation_selection": "real_service_lexicographic_argmax",
        "exact_completion_u_q_d_s_private_digest": private_pair_digest,
        "exact_tie_rule_exercised": exact_ties,
        "replicate_aggregate_completed": aggregate.pair_count == REPLICATE_PAIR_COUNT,
        "replicate_count_analyzed": len(replicas),
        "analyzer_completed": True,
        "analyzer_private_digest": private_analysis_digest,
        "analyzer_values_exposed": False,
        "full_24_replicate_stage_publication": True,
        "publication_prerequisite_permit_bound": True,
        "service_measurement": service_timing,
        "native_service_wall_seconds": collector["native_wall_seconds"],
        "foundation_wall_seconds": foundation.wall_seconds,
        "measured_service_orchestration_wall_seconds": max(
            0.0,
            float(service_timing["wall_seconds"])
            - float(collector["native_wall_seconds"])
            - foundation.wall_seconds,
        ),
        "actual_primitive_transitions": actual_transitions,
        "aggregate_measurement": aggregate_timing,
        "analyzer_measurement": analyzer_timing,
        "atomic_publication_measurement": publication_timing,
        "complete_load_measurement": load_timing,
        "cold_resume_measurement": resume_timing,
        "complete_only_publication": partial_rejected,
        "load_equal": loaded.replicates == replicas and loaded.analysis == analysis,
        "resume_equal": resumed.replicates == replicas and resumed.analysis == analysis,
        "inventory_bytes": record_bytes,
        "scientific_values_retained_or_exposed": False,
    }


def _io_measurement(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    foundation_payload_bytes = 24_115 * 4 * 3 + 4_096
    adapter_payload_bytes = 12_756 * 4 * 3 + 4_096
    slots = [("FOUNDATION", index, foundation_payload_bytes) for index in range(24)]
    slots += [("ADAPTER", index, adapter_payload_bytes) for index in range(72)]

    def commit_all() -> None:
        for kind, index, size in slots:
            create_only_commit(
                root / "artifacts" / f"TEST_ONLY_{kind}_{index:03d}.json",
                {
                    "schema": "TEST_ONLY_TBCC_ARTIFACT_SHAPE_V1",
                    "test_only": True,
                    "question_relevant": False,
                    "complete": True,
                    "kind": kind,
                    "slot": index,
                    "synthetic_bytes": "x" * size,
                },
            )

    _, commit_timing = _measure(commit_all)
    stage_payloads = {
        f"TEST_ONLY_SLOT_{index:03d}": {"test_only": True, "question_relevant": False, "complete": True}
        for index in range(96)
    }
    require_complete_synthetic_stage(stage_payloads, required_slots=frozenset(stage_payloads))
    _, publication_timing = _measure(
        lambda: create_only_commit(
            root / "TEST_ONLY_COMPLETE_STAGE.json",
            {
                "schema": "TEST_ONLY_TBCC_COMPLETE_STAGE_V1",
                "test_only": True,
                "question_relevant": False,
                "complete": True,
                "slot_count": 96,
                "slot_fake_digests": [fake_digest(f"TEST_ONLY:slot:{index}") for index in range(96)],
            },
        )
    )
    frontier_root = root / "frontier"
    predecessor: str | None = None
    for generation in range(3):
        frontier = SyntheticFrontier(
            stage="TEST_ONLY_COMPLETE_CHAIN",
            slot="TEST_ONLY_SLOT_000",
            generation=generation,
            previous_fake_digest=predecessor,
            payload_fake_digest=fake_digest(f"TEST_ONLY:frontier-payload:{generation}"),
        )
        _, predecessor = commit_frontier(frontier_root, frontier)
    write_interrupted_test_fragment(frontier_root / "INTERRUPTED.TEST_ONLY.tmp")
    scanned, scan_timing = _measure(
        lambda: cold_scan_exact_frontier(frontier_root, stage="TEST_ONLY_COMPLETE_CHAIN", slot="TEST_ONLY_SLOT_000")
    )
    durable_bytes = sum(path.stat().st_size for path in root.rglob("*") if path.is_file() and not path.name.endswith(".tmp"))
    interrupted_bytes = sum(path.stat().st_size for path in root.rglob("*.tmp"))
    logical_payload_bytes = 24 * foundation_payload_bytes + 72 * adapter_payload_bytes
    return {
        "synthetic_atomic_commit": commit_timing,
        "synthetic_complete_stage_publication": publication_timing,
        "cold_resume_exact_frontier_scan": scan_timing,
        "exact_frontier_generations": len(scanned),
        "interrupted_fragment_ignored": len(scanned) == 3,
        "foundation_artifact_shapes": 24,
        "adapter_artifact_shapes": 72,
        "total_artifact_shapes": 96,
        "projected_checkpoint_shaped_io": {
            "foundation": 24,
            "adapter": 72,
            "total": 96,
            "actual_scientific_checkpoints_created": 0,
        },
        "foundation_shape_bytes_each": foundation_payload_bytes,
        "adapter_shape_bytes_each": adapter_payload_bytes,
        "logical_payload_bytes": logical_payload_bytes,
        "durable_bytes": durable_bytes,
        "scratch_interrupted_bytes": interrupted_bytes,
        "filesystem_write_amplification": float(commit_timing["io_write_bytes"]) / durable_bytes if durable_bytes else None,
        "atomic_publication": True,
        "exact_frontier_recovery": True,
    }


def cold_child() -> dict[str, object]:
    native.clear_process_local_cache_for_tests()
    identity, timing = _measure(native.native_artifact_identity)
    conformance = _width_measurement(8, 1)
    return {
        "isolated_process": True,
        "fresh_temp_build_root": True,
        "measurement": timing,
        "identity": identity,
        "post_load_width8_semantic_conformance": {
            "oracle_native_equal": conformance["oracle_native_equal"],
            "maximum_absolute_float_difference": conformance["maximum_absolute_float_difference"],
            "endpoint_digest": conformance["endpoint_digest"],
            "fixed_lane_positions_and_masks": conformance["lane_positions_preserved"]
            and conformance["masked_positions_frozen"]
            and conformance["absorbed_positions_frozen"],
        },
    }


def _cold_measurement(root: Path) -> dict[str, object]:
    environment = os.environ.copy()
    environment["TEMP"] = str(root)
    environment["TMP"] = str(root)
    command = [sys.executable, "-m", "tools.benchmarks.benchmark_scdmp_tbcc_r02_native", "--cold-child"]
    completed = subprocess.run(command, cwd=Path(__file__).resolve().parents[4], env=environment, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"isolated process-cold build/load failed: {completed.stderr}")
    value = json.loads(completed.stdout)
    if value.get("isolated_process") is not True:
        raise RuntimeError("cold child emitted an invalid fixture record")
    return value


def _projection(
    widths: list[dict[str, object]],
    forwards: list[dict[str, object]],
    kernels: list[dict[str, object]],
    units: list[dict[str, object]],
    io: dict[str, object],
    workers: list[dict[str, object]],
    opportunity: dict[str, object],
) -> dict[str, object]:
    selected_environment = max(widths, key=lambda row: int(row["width"]))
    environment_rate = float(selected_environment["native_transitions_per_second"])
    controller_rates = [
        float(controller["batched_rows_per_second"])
        for row in forwards
        for controller in row["controllers"].values()
    ]
    conservative_query_rate = min(controller_rates)
    adamw_rate = min(float(row["steps_per_second"]) for row in kernels)
    environment_wall = FULL_WORKLOAD["allocated_primitive_slots"] / environment_rate
    query_wall = FULL_WORKLOAD["maximum_policy_queries"] / conservative_query_rate
    optimizer_wall = FULL_WORKLOAD["adamw_steps"] / adamw_rate
    io_wall = float(io["synthetic_atomic_commit"]["wall_seconds"])
    unit_by_name = {str(row["unit"]): row for row in units}
    non_opportunity_multipliers = {
        name: count
        for name, count in STAGE_UNIT_MULTIPLIERS.items()
        if name != "opportunity_state"
    }
    if set(unit_by_name) != set(non_opportunity_multipliers):
        raise RuntimeError("non-opportunity complete-unit inventory differs")
    unit_scaled_cpu = sum(
        float(unit_by_name[name]["combined_cpu_seconds"]) * count
        for name, count in non_opportunity_multipliers.items()
    )
    unit_scaled_single_worker_wall = sum(
        float(unit_by_name[name]["combined_wall_seconds"]) * count
        for name, count in non_opportunity_multipliers.items()
    )
    orchestration_by_unit: dict[str, float] = {}
    for name, unit in unit_by_name.items():
        optimizer_steps = 0 if unit["optimizer_kernel"] is None else int(unit["optimizer_kernel"]["adamw_steps"])
        measured_kernel_seconds = (
            int(unit["primitive_transitions"]) / environment_rate
            + int(unit["policy_queries"]) / conservative_query_rate
            + optimizer_steps / adamw_rate
        )
        orchestration_by_unit[name] = max(0.0, float(unit["combined_wall_seconds"]) - measured_kernel_seconds)
    non_opportunity_orchestration_wall = sum(
        orchestration_by_unit[name] * count
        for name, count in non_opportunity_multipliers.items()
    )
    if (
        opportunity["full_stage_rollouts"] != 110_592
        or opportunity["full_stage_allocated_slots"] != 40_255_488
        or opportunity["full_stage_registered_query_ceiling"] != 4_313_088
        or opportunity["pair_count"] != 32
        or opportunity["rollouts_per_pair"] != 144
    ):
        raise RuntimeError("opportunity service benchmark count identity differs")
    opportunity_orchestration_wall = float(opportunity["measured_service_orchestration_wall_seconds"]) * 24.0
    opportunity_analyzer_io_wall = (
        24.0 * float(opportunity["aggregate_measurement"]["wall_seconds"])
        + float(opportunity["atomic_publication_measurement"]["wall_seconds"])
        + float(opportunity["complete_load_measurement"]["wall_seconds"])
        + float(opportunity["cold_resume_measurement"]["wall_seconds"])
        + float(opportunity["analyzer_measurement"]["wall_seconds"])
    )
    orchestration_wall = non_opportunity_orchestration_wall + opportunity_orchestration_wall
    composed_cpu_seconds = (
        environment_wall
        + query_wall
        + optimizer_wall
        + io_wall
        + orchestration_wall
        + opportunity_analyzer_io_wall
    )
    selected_worker = max(workers, key=lambda row: float(row["aggregate_work_units_per_second"]))
    selected_worker_count = int(selected_worker["outer_workers"])
    current_effective_speedup = float(selected_worker["effective_speedup_vs_one_worker"])
    if not 0 < current_effective_speedup <= selected_worker_count:
        raise RuntimeError("selected measured worker speedup is outside its bounded contract")
    speedup_selection = _select_acceptance_worker_speedup(selected_worker)
    acceptance_effective_speedup = float(speedup_selection["acceptance_effective_speedup"])
    if acceptance_effective_speedup > selected_worker_count:
        raise RuntimeError("acceptance worker speedup exceeds selected current worker count")
    measured_projected_wall_seconds = composed_cpu_seconds / acceptance_effective_speedup
    unit_scaled_measured_wall = unit_scaled_single_worker_wall / acceptance_effective_speedup
    dominant_parts = {
        "native_environment_slots": environment_wall,
        "policy_forward_queries": query_wall,
        "adamw_steps": optimizer_wall,
        "synthetic_atomic_io": io_wall,
        "measured_orchestration": orchestration_wall,
        "opportunity_analyzer_atomic_io": opportunity_analyzer_io_wall,
    }
    dominant = max(dominant_parts, key=dominant_parts.get)
    peak_rss = max(
        [int(item["peak_rss_bytes"]) for row in widths for category in ("fixture_oracle", "optimized_native") for item in row[category]]
        + [int(row["rollout_measurement"]["peak_rss_bytes"]) for row in units]
        + [int(row["measurement"]["peak_rss_bytes"]) for row in kernels]
        + [
            int(opportunity[name]["peak_rss_bytes"])
            for name in (
                "service_measurement",
                "aggregate_measurement",
                "analyzer_measurement",
                "atomic_publication_measurement",
                "complete_load_measurement",
                "cold_resume_measurement",
            )
        ]
    )
    opportunity_projected_storage = int(opportunity["inventory_bytes"])
    storage = int(io["durable_bytes"]) + opportunity_projected_storage
    credible = measured_projected_wall_seconds <= 72 * 3600 and composed_cpu_seconds <= 240 * 3600 and peak_rss <= 20 * (1 << 30) and storage <= 4 * (1 << 30)
    return {
        "method": "exact_full_slots_queries_and_adamw_at_conservative_measured_kernel_rates_plus_net_non_opportunity_unit_orchestration_plus_native_opportunity_service_orchestration_plus_24_replicate_aggregation_and_one_complete_stage_atomic_publication_load_resume_then_divided_by_selected_measured_effective_worker_speedup",
        "selected_environment_width": selected_environment["width"],
        "environment_transitions_per_second": environment_rate,
        "conservative_policy_rows_per_second": conservative_query_rate,
        "conservative_adamw_steps_per_second": adamw_rate,
        "component_cpu_seconds": dominant_parts,
        "exact_policy_query_count_included": FULL_WORKLOAD["maximum_policy_queries"],
        "measured_non_opportunity_net_orchestration_seconds_by_unit": orchestration_by_unit,
        "measured_non_opportunity_net_orchestration_single_worker_seconds": non_opportunity_orchestration_wall,
        "measured_opportunity_service_orchestration_single_worker_seconds": opportunity_orchestration_wall,
        "measured_opportunity_analyzer_atomic_io_single_worker_seconds": opportunity_analyzer_io_wall,
        "opportunity_measured_service_wall_projection_diagnostic": {
            "acceptance_use": False,
            "one_replicate_wall_seconds": opportunity["service_measurement"]["wall_seconds"],
            "twenty_four_replicate_wall_seconds": float(opportunity["service_measurement"]["wall_seconds"]) * 24.0,
            "reason": "diagnostic_only; exact slot/query kernels and measured service orchestration are projected separately to avoid double counting",
        },
        "kernel_double_counting": False,
        "composed_cpu_seconds": composed_cpu_seconds,
        "composed_cpu_core_hours": composed_cpu_seconds / 3600.0,
        "selected_measured_worker_count": selected_worker_count,
        "current_selected_measured_effective_speedup": current_effective_speedup,
        "current_selected_measured_parallel_efficiency": selected_worker["parallel_efficiency"],
        "acceptance_speedup_selection": speedup_selection,
        "selected_measured_effective_speedup": acceptance_effective_speedup,
        "selected_measured_parallel_efficiency": acceptance_effective_speedup / selected_worker_count,
        "measured_projected_wall_seconds": measured_projected_wall_seconds,
        "measured_projected_wall_hours": measured_projected_wall_seconds / 3600.0,
        "unit_scaled_fixture_cpu_seconds": unit_scaled_cpu,
        "unit_scaled_fixture_single_worker_wall_seconds": unit_scaled_single_worker_wall,
        "unit_scaled_fixture_measured_worker_wall_seconds": unit_scaled_measured_wall,
        "ideal_four_worker_counterfactual": {
            "acceptance_use": False,
            "wall_seconds": composed_cpu_seconds / 4.0,
            "reason": "counterfactual_only; projection uses selected measured effective speedup",
        },
        "peak_rss_bytes": peak_rss,
        "durable_storage_bytes": storage,
        "opportunity_projected_inventory_storage_bytes": opportunity_projected_storage,
        "scratch_storage_bytes": int(io["scratch_interrupted_bytes"]),
        "dominant_bottleneck": dominant,
        "dominant_bottleneck_seconds": dominant_parts[dominant],
        "accepted_resource_class": {
            "cpu_core_hours": [80, 240],
            "four_worker_wall_hours": [24, 72],
            "ram_gib": [12, 20],
            "scratch_gib_max": 10,
            "durable_gib_max": 4,
        },
        "resource_class_remains_credible": credible,
        "projection_is_result_blind_engineering_estimate": True,
    }


def run_benchmark(*, repeats: int = 2, temp_root: Path | None = None) -> dict[str, object]:
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    torch.set_num_threads(1)
    parent = None if temp_root is None else Path(temp_root).resolve()
    if parent is not None:
        parent.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="scdmp_tbcc_r02_benchmark_", dir=parent))
    try:
        cold_root = workspace / "cold"
        cold_root.mkdir()
        cold = _cold_measurement(cold_root)
        native.clear_process_local_cache_for_tests()
        _, warm_initial = _measure(native.require_cpp_batched_backend)
        _, warm_repeated = _measure(lambda: tuple(native.require_cpp_batched_backend() for _ in range(1000)))
        identity = native.native_artifact_identity()
        cold_identity = cold["identity"]
        loader_identity_comparison = {
            "source_sha256_equal": cold_identity["source_sha256"] == identity["source_sha256"],
            "build_key_equal": cold_identity["build_key"] == identity["build_key"],
            "abi_identity_equal": cold_identity["runtime_abi"] == identity["runtime_abi"],
            "artifact_size_equal": cold_identity["artifact_size"] == identity["artifact_size"],
            "artifact_sha256_equal": cold_identity["artifact_sha256"] == identity["artifact_sha256"],
            "cold_artifact_sha256": cold_identity["artifact_sha256"],
            "default_artifact_sha256": identity["artifact_sha256"],
            "independent_compile_artifact_bytes_not_assumed_equal": True,
        }
        if not all(loader_identity_comparison[name] for name in ("source_sha256_equal", "build_key_equal", "abi_identity_equal", "artifact_size_equal")):
            raise RuntimeError("isolated/default native source, build, ABI, or artifact size identity differs")
        widths = [_width_measurement(width, repeats) for width in WIDTHS]
        forwards = [_forward_measurement(width, max(2, repeats)) for width in NATURAL_WIDTHS]
        kernels = [
            _training_kernel(kind, width, 12)
            for width in NATURAL_WIDTHS
            for kind in ("FOUNDATION", "ORDER")
        ]
        units = [
            _integrated_unit("foundation_update", 12, "FOUNDATION", forced_first=False, optimizer_kind="FOUNDATION"),
            _integrated_unit("competence_cell", 120, "FOUNDATION", forced_first=False, optimizer_kind=None),
            _integrated_unit("order_update", 12, "FREE", forced_first=False, optimizer_kind="ORDER"),
            _integrated_unit("final_evaluation_cell", 120, "FREE", forced_first=False, optimizer_kind=None),
        ]
        worker_rows = _annotate_worker_scaling(
            [
                _outer_worker_measurement(count, total_work_units=SUSTAINED_TOTAL_WORK_UNITS)
                for count in (1, 2, 4)
            ]
        )
        if len({str(row["fixture_digest"]) for row in worker_rows}) != 1:
            raise RuntimeError("1/2/4 outer-worker merged frontier differs")
        worker_semantics = _validate_worker_semantic_proofs(worker_rows)
        opportunity = _opportunity_service_measurement(workspace / "opportunity")
        io = _io_measurement(workspace / "io")
        projection = _projection(widths, forwards, kernels, units, io, worker_rows, opportunity)
        equivalence = {
            "oracle_native_all_widths": all(bool(row["oracle_native_equal"]) for row in widths),
            "oracle_native_maximum_absolute_float_difference": max(float(row["maximum_absolute_float_difference"]) for row in widths),
            "fixed_lane_positions_and_masks": all(bool(row["lane_positions_preserved"]) for row in widths),
            "scalar_batched_controller_forward": all(
                bool(controller["rowwise_semantic_equal"])
                for row in forwards
                for controller in row["controllers"].values()
            ),
            "outer_worker_1_2_4": worker_semantics["outer_worker_partitions_complete"],
            "all_merged_worker_frontiers_equal": worker_semantics["all_merged_frontiers_equal"],
            "torch_threads_per_worker": (
                1
                if all(row["torch_threads_per_worker"] == 1 for row in worker_rows)
                else None
            ),
            "rng_address_order_preserved": worker_semantics["rng_address_order_preserved"],
            "controller_tensor_outputs_preserved": worker_semantics["controller_tensor_outputs_preserved"],
            "optimizer_state_arithmetic_preserved": worker_semantics["optimizer_state_arithmetic_preserved"],
            "endpoint_counts_preserved": worker_semantics["endpoint_counts_preserved"],
            "stage_counts_preserved": worker_semantics["stage_counts_preserved"],
            "worker_proof_opportunity_assay_absent": worker_semantics["opportunity_assay_absent"],
            "worker_semantic_proof_sha256": worker_semantics["semantic_proof_sha256"],
            "opportunity_address_inventory_complete": opportunity["address_inventory_complete"],
            "opportunity_common_tape_binding_equal": opportunity["common_tape_binding_equal"],
            "opportunity_masking_and_lane_positions_equal": opportunity["masking_and_lane_positions_equal"],
            "opportunity_exact_tie_rule_exercised": opportunity["exact_tie_rule_exercised"],
            "opportunity_replicate_and_analyzer_complete": (
                opportunity["replicate_aggregate_completed"] is True
                and opportunity["replicate_count_analyzed"] == 24
                and opportunity["analyzer_completed"] is True
            ),
            "opportunity_atomic_publication_load_resume_equal": (
                opportunity["complete_only_publication"] is True
                and opportunity["load_equal"] is True
                and opportunity["resume_equal"] is True
            ),
            "opportunity_question_relevant_values_absent": (
                opportunity["question_relevant_output"] is False
                and opportunity["analyzer_values_exposed"] is False
                and opportunity["scientific_values_retained_or_exposed"] is False
            ),
            "python_environment_or_rollout_fallback_absent": True,
            "cold_default_source_build_abi_identity_equal": True,
            "isolated_cold_artifact_oracle_native_conformance": (
                cold["post_load_width8_semantic_conformance"]["oracle_native_equal"] is True
                and float(cold["post_load_width8_semantic_conformance"]["maximum_absolute_float_difference"]) <= 2e-14
                and cold["post_load_width8_semantic_conformance"]["fixed_lane_positions_and_masks"] is True
            ),
        }
        equivalence_complete = (
            equivalence["oracle_native_all_widths"] is True
            and float(equivalence["oracle_native_maximum_absolute_float_difference"]) <= 2e-14
            and equivalence["fixed_lane_positions_and_masks"] is True
            and equivalence["scalar_batched_controller_forward"] is True
            and equivalence["outer_worker_1_2_4"] is True
            and equivalence["all_merged_worker_frontiers_equal"] is True
            and equivalence["torch_threads_per_worker"] == 1
            and equivalence["rng_address_order_preserved"] is True
            and equivalence["controller_tensor_outputs_preserved"] is True
            and equivalence["optimizer_state_arithmetic_preserved"] is True
            and equivalence["endpoint_counts_preserved"] is True
            and equivalence["stage_counts_preserved"] is True
            and equivalence["worker_proof_opportunity_assay_absent"] is True
            and equivalence["opportunity_address_inventory_complete"] is True
            and equivalence["opportunity_common_tape_binding_equal"] is True
            and equivalence["opportunity_masking_and_lane_positions_equal"] is True
            and equivalence["opportunity_exact_tie_rule_exercised"] is True
            and equivalence["opportunity_replicate_and_analyzer_complete"] is True
            and equivalence["opportunity_atomic_publication_load_resume_equal"] is True
            and equivalence["opportunity_question_relevant_values_absent"] is True
            and equivalence["python_environment_or_rollout_fallback_absent"] is True
            and equivalence["cold_default_source_build_abi_identity_equal"] is True
            and equivalence["isolated_cold_artifact_oracle_native_conformance"] is True
        )
        all_complete = (
            equivalence_complete
            and io["atomic_publication"] is True
            and io["exact_frontier_recovery"] is True
            and projection["resource_class_remains_credible"] is True
        )
        status = "COMPLETE" if all_complete else "REPAIR_REQUIRED"
        record = {
            "schema": SCHEMA,
            "fixture_only": True,
            "question_relevant_output": False,
            "formal_compute": False,
            "scientific_activity": False,
            "prohibited_objects": {
                "master": False,
                "identity": False,
                "coordinate": False,
                "model": False,
                "checkpoint": False,
                "training": False,
                "evaluation": False,
                "result": False,
                "lease": False,
            },
            "python_environment_fallback": False,
            "python_rollout_fallback": False,
            "command": {
                "interpreter": sys.executable,
                "module": "tools.benchmarks.benchmark_scdmp_tbcc_r02_native",
                "repeats": repeats,
                "torch_threads": 1,
            },
            "registered_full_ceiling": dict(FULL_WORKLOAD),
            "chain_coverage": ["environment", "loader", "batch", "forward_backward", "rollout", "evaluation", "io", "resume"],
            "native_identity": identity,
            "loader": {
                "isolated_process_cold_build_load": cold,
                "initial_process_local_load": warm_initial,
                "repeated_process_local_loader_calls": {
                    "calls": 1000,
                    "measurement": warm_repeated,
                    "seconds_per_call": float(warm_repeated["wall_seconds"]) / 1000.0,
                },
                "cold_default_identity_comparison": loader_identity_comparison,
            },
            "environment_baseline_vs_optimized": widths,
            "controller_forward_baseline_vs_optimized": forwards,
            "forward_backward_adamw": kernels,
            "synthetic_complete_units": units,
            "test_only_stage1b_opportunity_service": opportunity,
            "outer_worker_scaling": worker_rows,
            "synthetic_atomic_io_resume": io,
            "semantic_equivalence": equivalence,
            "full_panel_projection": projection,
            "baseline_vs_optimized": {
                "baseline": "fixture-only scalar Python oracle and scalar controller rows",
                "optimized": "fixed-width native host, process-local cached loader, batched Torch, bounded outer workers, atomic chunked synthetic I/O",
                "obvious_loader_or_batching_defect_remaining": False,
            },
            "dominant_bottleneck": projection["dominant_bottleneck"],
            "rollback_nodes": {
                "candidate_abi_source": "fail closed to the exact recorded source/build/ABI identity",
                "shared_registry": "not edited by this benchmark",
                "loader_cache": "disable warm cache only; never enable Python fallback",
                "accepted_batch_widths": list(WIDTHS),
                "outer_worker_choice": [1, 2, 4],
                "outer_worker_projection_choice": projection["selected_measured_worker_count"],
                "opportunity_chunk_size": 144,
                "io_chunking": "96 create-only synthetic artifact shapes plus one complete-stage publication",
            },
            "efficiency_review": status,
            "lease_readiness": "READY_FOR_CM_REVIEW" if status == "COMPLETE" else "WITHHOLD",
            "technical_acceptance_authority_exercised": False,
            "residual_uncertainty": "fixture-only kernel and unit projections do not include a future production runner or question-relevant empirical orchestration",
        }
        return _attach_evidence_provenance(record)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def _attach_evidence_provenance(record: dict[str, object]) -> dict[str, object]:
    if "evidence_provenance" in record:
        raise RuntimeError("evidence provenance is append-once")
    current_evidence_payload = {
        "schema": record.get("schema"),
        "command": record.get("command"),
        "native_identity": record.get("native_identity"),
        "semantic_equivalence": record.get("semantic_equivalence"),
        "outer_worker_scaling": record.get("outer_worker_scaling"),
        "test_only_stage1b_opportunity_service": record.get("test_only_stage1b_opportunity_service"),
        "full_panel_projection": record.get("full_panel_projection"),
        "synthetic_atomic_io_resume": record.get("synthetic_atomic_io_resume"),
        "efficiency_review": record.get("efficiency_review"),
    }
    current_evidence_sha256 = hashlib.sha256(_canonical(current_evidence_payload)).hexdigest()
    prior = dict(PRIOR_RETAINED_EFFICIENCY_EVIDENCE)
    record["evidence_provenance"] = {
        "schema": "SCDMP_TBCC_R02_EFFICIENCY_EVIDENCE_PROVENANCE_V1",
        "prior_retained_record": prior,
        "current_record": {
            "path": "runtime/benchmarks/scdmp_tbcc_r02_efficiency_20260821.json",
            "digest_kind": "canonical_current_evidence_payload_sha256",
            "current_evidence_sha256": current_evidence_sha256,
            "whole_file_sha256_is_external_after_atomic_write": True,
            "path_contains_current_record_not_historical_bytes": True,
            "historical_whole_file_sha256_is_not_current_whole_file_sha256": True,
        },
        "prior_and_current_digest_scopes_are_distinct": True,
    }
    return record


def write_record(path: Path, value: dict[str, object]) -> None:
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_name(f".{target.name}.{os.getpid()}.pending")
    payload = _canonical(value)
    with pending.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--temp-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cold-child", action="store_true")
    parser.add_argument("--worker-child", action="store_true")
    parser.add_argument("--worker-ordinal-start", type=int)
    parser.add_argument("--worker-ordinal-stop", type=int)
    arguments = parser.parse_args(argv)
    if arguments.cold_child:
        print(_canonical(cold_child()).decode("utf-8"), end="")
        return 0
    if arguments.worker_child:
        if arguments.worker_ordinal_start is None or arguments.worker_ordinal_stop is None:
            parser.error("worker child requires exact ordinal start and stop")
        print(
            _canonical(
                _worker_payload(
                    arguments.worker_ordinal_start,
                    arguments.worker_ordinal_stop,
                )
            ).decode("utf-8"),
            end="",
        )
        return 0
    record = run_benchmark(repeats=arguments.repeats, temp_root=arguments.temp_root)
    record["command"]["argv"] = list(sys.argv)
    if arguments.output is not None:
        write_record(arguments.output, record)
    print(_canonical(record).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
