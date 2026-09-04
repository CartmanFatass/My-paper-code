"""Thin ctypes binding for the separately built VNFC headroom analysis adapter."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import subprocess
import sys

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.contracts import MSVC_COMPILE_FLAGS
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
    _EpisodeInput,
    _episode_input,
    _vs_installation,
)


_SOURCE = Path(__file__).with_name("native") / "headroom_backend.cpp"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_BUILD_ROOT = (
    _REPOSITORY_ROOT
    / "temp/directions/variable_n_fleet_churn/build/controller_headroom"
)


def _analysis_binary_path(platform_name: str | None = None) -> Path:
    platform_name = sys.platform if platform_name is None else platform_name
    if platform_name == "win32":
        suffix = ".dll"
    elif platform_name.startswith("linux"):
        suffix = ".so"
    else:
        raise RuntimeError(f"unsupported headroom analysis platform: {platform_name}")
    return _BUILD_ROOT / f"headroom_analysis{suffix}"


def _linux_build_command(binary: Path, compiler: str | None = None) -> tuple[str, ...]:
    return (
        compiler or os.environ.get("CXX", "c++"),
        "-std=c++20",
        "-O2",
        "-fPIC",
        "-shared",
        "-fno-fast-math",
        "-ffp-contract=off",
        f"-I{_SOURCE.parent}",
        str(_SOURCE),
        "-o",
        str(binary),
    )


class _BCRHCandidateRecord(ctypes.Structure):
    _fields_ = [
        ("command", ctypes.c_int32 * 4),
        ("floor_num", ctypes.c_int32),
        ("floor_den", ctypes.c_int32),
        ("releases", ctypes.c_int32),
        ("objective_limbs", ctypes.c_uint64 * 4),
        ("checker_floor_num", ctypes.c_int32),
        ("checker_floor_den", ctypes.c_int32),
        ("checker_releases", ctypes.c_int32),
        ("checker_objective_limbs", ctypes.c_uint64 * 4),
        ("exact_match", ctypes.c_int32),
    ]


class _SelectorInput(ctypes.Structure):
    _fields_ = [
        ("score", ctypes.c_int64),
        ("prefix", ctypes.c_int32 * 12),
    ]


class _HeadroomOutput(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int32),
        ("failed_rank", ctypes.c_int32),
        ("beam_width", ctypes.c_int32),
        ("numerator", ctypes.c_int64 * 3),
        ("denominator", ctypes.c_int64 * 3),
        ("commands", (ctypes.c_int32 * 24) * 3),
        ("terminal_completion_commands", (ctypes.c_int32 * 12) * 2),
        ("terminal", ctypes.c_int32 * 3),
        ("safety_violation", ctypes.c_int32 * 3),
        ("exclusivity_violation", ctypes.c_int32 * 3),
        ("bcrh_candidate_count", ctypes.c_int32 * 6),
        ("bcrh_scorer_checker_equal", ctypes.c_int32 * 6),
        ("bcrh_independent_enumerator_equal", ctypes.c_int32 * 6),
        ("bcrh_all_candidate_records_exact", ctypes.c_int32 * 6),
        ("bcrh_scorer_command", (ctypes.c_int32 * 4) * 6),
        ("bcrh_checker_command", (ctypes.c_int32 * 4) * 6),
        ("bcrh_candidate_digest", ctypes.c_uint64 * 6),
        ("bcrh_checker_digest", ctypes.c_uint64 * 6),
        ("bcrh_candidate_records", (_BCRHCandidateRecord * 1961) * 6),
        ("beam_states_before", ctypes.c_int64 * 3),
        ("beam_legal_commands", ctypes.c_int64 * 3),
        ("beam_expansions", ctypes.c_int64 * 3),
        ("beam_states_retained", ctypes.c_int64 * 3),
        ("beam_native_ticks", ctypes.c_int64 * 3),
        ("beam_current_nodes_high_water", ctypes.c_int64 * 3),
        ("beam_next_nodes_high_water", ctypes.c_int64 * 3),
        ("beam_transient_nodes_high_water", ctypes.c_int64 * 3),
        ("beam_live_nodes_high_water", ctypes.c_int64 * 3),
        ("beam_current_capacity_high_water", ctypes.c_int64 * 3),
        ("beam_next_capacity_high_water", ctypes.c_int64 * 3),
        ("beam_current_agent_capacity_high_water", ctypes.c_int64 * 3),
        ("beam_next_agent_capacity_high_water", ctypes.c_int64 * 3),
        ("beam_transient_agent_capacity_high_water", ctypes.c_int64 * 3),
        ("beam_current_owned_bytes_high_water", ctypes.c_int64 * 3),
        ("beam_next_owned_bytes_high_water", ctypes.c_int64 * 3),
        ("beam_transient_owned_bytes_high_water", ctypes.c_int64 * 3),
        ("beam_total_owned_bytes_high_water", ctypes.c_int64 * 3),
        ("beam_replacements", ctypes.c_int64 * 3),
        ("beam_enumerator_count_high_water", ctypes.c_int64 * 3),
        ("beam_fixed_enumerator_scratch_bytes", ctypes.c_int64),
        ("beam_conservative_fixed_storage_allowance_bytes", ctypes.c_int64),
        ("persist_candidate_count", ctypes.c_int32),
        ("persist_sensitivity_agreement", ctypes.c_int32),
        ("persist_native_ticks", ctypes.c_int64),
        ("bcrh_native_ticks", ctypes.c_int64),
        ("terminal_completion_native_ticks", ctypes.c_int64),
    ]


def build_analysis_backend() -> Path:
    """Build the single analysis library outside the scientific result root."""
    binary = _analysis_binary_path()
    binary.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        installation = _vs_installation()
        vcvars = installation / "VC/Auxiliary/Build/vcvars64.bat"
        obj = binary.with_suffix(".obj")
        command: str | tuple[str, ...] = (
            f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
            f'"{_SOURCE}" /Fo:"{obj}" /link /OUT:"{binary}"'
        )
        completed = subprocess.run(
            command,
            shell=True,
            executable=os.environ.get("COMSPEC", "cmd.exe"),
            cwd=binary.parent,
            capture_output=True,
            text=True,
        )
    elif sys.platform.startswith("linux"):
        command = _linux_build_command(binary)
        completed = subprocess.run(
            command,
            cwd=binary.parent,
            capture_output=True,
            text=True,
        )
    else:
        raise RuntimeError(f"unsupported headroom analysis platform: {sys.platform}")
    if completed.returncode or not binary.is_file():
        raise RuntimeError(
            f"headroom analysis backend build failed ({completed.returncode}):\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return binary


def require_analysis_backend() -> ctypes.CDLL:
    """Load the prebuilt adapter without compiling inside a result invocation."""
    binary = _analysis_binary_path()
    if not binary.is_file():
        raise RuntimeError(
            "headroom analysis backend is not prebuilt; call build_analysis_backend before launch"
        )
    library = ctypes.CDLL(str(binary))
    library.vnfc_headroom_sizeof_output.argtypes = []
    library.vnfc_headroom_sizeof_output.restype = ctypes.c_size_t
    library.vnfc_headroom_run.argtypes = [
        ctypes.POINTER(_EpisodeInput), ctypes.c_int32, ctypes.POINTER(_HeadroomOutput)
    ]
    library.vnfc_headroom_run.restype = ctypes.c_int32
    library.vnfc_headroom_sizeof_selector_input.argtypes = []
    library.vnfc_headroom_sizeof_selector_input.restype = ctypes.c_size_t
    library.vnfc_headroom_select_top_k.argtypes = [
        ctypes.POINTER(_SelectorInput),
        ctypes.c_int32,
        ctypes.c_int32,
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int64),
    ]
    library.vnfc_headroom_select_top_k.restype = ctypes.c_int32
    if library.vnfc_headroom_sizeof_output() != ctypes.sizeof(_HeadroomOutput):
        raise RuntimeError("headroom analysis output layout differs")
    if library.vnfc_headroom_sizeof_selector_input() != ctypes.sizeof(_SelectorInput):
        raise RuntimeError("headroom selector input layout differs")
    return library


def _command_rows(values: object, rows: int) -> tuple[tuple[int | None, ...], ...]:
    flat = tuple(int(value) for value in values)  # type: ignore[arg-type]
    return tuple(
        tuple(None if value == 255 else value for value in flat[4 * row : 4 * row + 4])
        for row in range(rows)
    )


def _candidate_record(record: _BCRHCandidateRecord) -> dict[str, object]:
    return {
        "command": _command_rows(record.command, 1)[0],
        "floor": (int(record.floor_num), int(record.floor_den)),
        "releases": int(record.releases),
        "objective_limbs": tuple(int(value) for value in record.objective_limbs),
        "checker_floor": (
            int(record.checker_floor_num), int(record.checker_floor_den)
        ),
        "checker_releases": int(record.checker_releases),
        "checker_objective_limbs": tuple(
            int(value) for value in record.checker_objective_limbs
        ),
        "exact_match": bool(record.exact_match),
    }


def select_top_k_fixture(
    inventory: object, width: int, prefix_size: int
) -> tuple[tuple[int, ...], int]:
    """Exercise the same native fixed-capacity reducer used by the beam."""
    rows = tuple(inventory)  # type: ignore[arg-type]
    inputs = (_SelectorInput * len(rows))()
    for index, row in enumerate(rows):
        score, prefix = row
        values = tuple(int(value) for value in prefix)
        if len(values) != prefix_size:
            raise ValueError("selector prefix length differs from prefix_size")
        inputs[index].score = int(score)
        for position, value in enumerate(values):
            inputs[index].prefix[position] = value
    selected = (ctypes.c_int32 * min(len(rows), width))()
    selected_count = ctypes.c_int32()
    replacements = ctypes.c_int64()
    status = require_analysis_backend().vnfc_headroom_select_top_k(
        inputs,
        len(rows),
        int(width),
        int(prefix_size),
        selected,
        ctypes.byref(selected_count),
        ctypes.byref(replacements),
    )
    if status:
        raise RuntimeError(f"headroom selector fixture failed with status {status}")
    return (
        tuple(int(selected[index]) for index in range(selected_count.value)),
        int(replacements.value),
    )


def run_headroom_fixture(fixture: object, beam_width: int) -> dict[str, object]:
    native_input = _episode_input(fixture)
    output = _HeadroomOutput()
    status = require_analysis_backend().vnfc_headroom_run(
        ctypes.byref(native_input), int(beam_width), ctypes.byref(output)
    )
    if status or output.status:
        raise RuntimeError(
            f"headroom native execution failed with status {status}/{output.status}"
        )
    policies = ("BCRH", "PERSIST_MAX_C60", "ORACLE_BEAM_FAIL60")
    return {
        "failed_rank": int(output.failed_rank),
        "beam_width": int(output.beam_width),
        "endpoints": {
            policy: (int(output.numerator[index]), int(output.denominator[index]))
            for index, policy in enumerate(policies)
        },
        "trajectories": {
            policy: _command_rows(output.commands[index], 6)
            for index, policy in enumerate(policies)
        },
        "terminal_completion_commands": {
            "PERSIST_MAX_C60": _command_rows(output.terminal_completion_commands[0], 3),
            "ORACLE_BEAM_FAIL60": _command_rows(output.terminal_completion_commands[1], 3),
        },
        "validity": {
            policy: {
                "terminal": bool(output.terminal[index]),
                "safety": not bool(output.safety_violation[index]),
                "exclusivity": not bool(output.exclusivity_violation[index]),
            }
            for index, policy in enumerate(policies)
        },
        "bcrh_decisions": tuple(
            {
                "epoch": epoch,
                "candidate_count": int(output.bcrh_candidate_count[epoch]),
                "scorer_command": _command_rows(output.bcrh_scorer_command[epoch], 1)[0],
                "checker_command": _command_rows(output.bcrh_checker_command[epoch], 1)[0],
                "scorer_checker_equal": bool(output.bcrh_scorer_checker_equal[epoch]),
                "independent_enumerator_equal": bool(
                    output.bcrh_independent_enumerator_equal[epoch]
                ),
                "all_candidate_records_exact": bool(
                    output.bcrh_all_candidate_records_exact[epoch]
                ),
                "candidate_digest": int(output.bcrh_candidate_digest[epoch]),
                "checker_digest": int(output.bcrh_checker_digest[epoch]),
                "candidate_records": tuple(
                    _candidate_record(output.bcrh_candidate_records[epoch][index])
                    for index in range(output.bcrh_candidate_count[epoch])
                ),
            }
            for epoch in range(6)
        ),
        "beam_depths": tuple(
            {
                "depth": depth,
                "states_before": int(output.beam_states_before[depth]),
                "legal_commands": int(output.beam_legal_commands[depth]),
                "expansions": int(output.beam_expansions[depth]),
                "states_retained": int(output.beam_states_retained[depth]),
                "native_ticks": int(output.beam_native_ticks[depth]),
                "current_frontier": {
                    "nodes_high_water": int(
                        output.beam_current_nodes_high_water[depth]
                    ),
                    "capacity_high_water": int(
                        output.beam_current_capacity_high_water[depth]
                    ),
                    "agent_capacity_high_water": int(
                        output.beam_current_agent_capacity_high_water[depth]
                    ),
                    "owned_bytes_high_water": int(
                        output.beam_current_owned_bytes_high_water[depth]
                    ),
                },
                "next_selector": {
                    "nodes_high_water": int(output.beam_next_nodes_high_water[depth]),
                    "capacity_high_water": int(
                        output.beam_next_capacity_high_water[depth]
                    ),
                    "agent_capacity_high_water": int(
                        output.beam_next_agent_capacity_high_water[depth]
                    ),
                    "owned_bytes_high_water": int(
                        output.beam_next_owned_bytes_high_water[depth]
                    ),
                },
                "transient": {
                    "nodes_high_water": int(
                        output.beam_transient_nodes_high_water[depth]
                    ),
                    "agent_capacity_high_water": int(
                        output.beam_transient_agent_capacity_high_water[depth]
                    ),
                    "owned_bytes_high_water": int(
                        output.beam_transient_owned_bytes_high_water[depth]
                    ),
                },
                "live_nodes_high_water": int(
                    output.beam_live_nodes_high_water[depth]
                ),
                "total_owned_bytes_high_water": int(
                    output.beam_total_owned_bytes_high_water[depth]
                ),
                "replacements": int(output.beam_replacements[depth]),
                "enumerator_count_high_water": int(
                    output.beam_enumerator_count_high_water[depth]
                ),
            }
            for depth in range(3)
        ),
        "counts": {
            "persist_candidates": int(output.persist_candidate_count),
            "persist_native_ticks": int(output.persist_native_ticks),
            "bcrh_decision_calls": 6,
            "bcrh_native_ticks": int(output.bcrh_native_ticks),
            "terminal_completion_native_ticks": int(
                output.terminal_completion_native_ticks
            ),
        },
        "persist_sensitivity_agreement": bool(output.persist_sensitivity_agreement),
        "search_storage": {
            "fixed_enumerator_scratch_bytes": int(
                output.beam_fixed_enumerator_scratch_bytes
            ),
            "conservative_fixed_storage_allowance_bytes": int(
                output.beam_conservative_fixed_storage_allowance_bytes
            ),
            "max_live_nodes_high_water": max(output.beam_live_nodes_high_water),
            "max_total_owned_bytes_high_water": max(
                output.beam_total_owned_bytes_high_water
            ),
            "max_current_frontier_capacity": max(
                output.beam_current_capacity_high_water
            ),
            "max_next_selector_capacity": max(
                output.beam_next_capacity_high_water
            ),
            "replacement_count": sum(output.beam_replacements),
        },
    }
