"""Thin ctypes binding for the separately built VNFC headroom analysis adapter."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import subprocess

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.contracts import MSVC_COMPILE_FLAGS
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
    _EpisodeInput,
    _episode_input,
    _vs_installation,
)


_SOURCE = Path(__file__).with_name("native") / "headroom_backend.cpp"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_BINARY = (
    _REPOSITORY_ROOT
    / "temp/directions/variable_n_fleet_churn/build/controller_headroom/headroom_analysis.dll"
)


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
        ("beam_states_before", ctypes.c_int64 * 3),
        ("beam_legal_commands", ctypes.c_int64 * 3),
        ("beam_expansions", ctypes.c_int64 * 3),
        ("beam_states_retained", ctypes.c_int64 * 3),
        ("beam_native_ticks", ctypes.c_int64 * 3),
        ("persist_candidate_count", ctypes.c_int32),
        ("persist_sensitivity_agreement", ctypes.c_int32),
        ("persist_native_ticks", ctypes.c_int64),
        ("bcrh_native_ticks", ctypes.c_int64),
        ("terminal_completion_native_ticks", ctypes.c_int64),
    ]


def build_analysis_backend() -> Path:
    """Build the single analysis DLL outside the scientific result root."""
    _BINARY.parent.mkdir(parents=True, exist_ok=True)
    installation = _vs_installation()
    vcvars = installation / "VC/Auxiliary/Build/vcvars64.bat"
    obj = _BINARY.with_suffix(".obj")
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
        f'"{_SOURCE}" /Fo:"{obj}" /link /OUT:"{_BINARY}"'
    )
    completed = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=_BINARY.parent,
        capture_output=True,
        text=True,
    )
    if completed.returncode or not _BINARY.is_file():
        raise RuntimeError(
            f"headroom analysis backend build failed ({completed.returncode}):\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return _BINARY


def require_analysis_backend() -> ctypes.CDLL:
    """Load the prebuilt adapter without compiling inside a result invocation."""
    if not _BINARY.is_file():
        raise RuntimeError(
            "headroom analysis backend is not prebuilt; call build_analysis_backend before launch"
        )
    library = ctypes.CDLL(str(_BINARY))
    library.vnfc_headroom_sizeof_output.argtypes = []
    library.vnfc_headroom_sizeof_output.restype = ctypes.c_size_t
    library.vnfc_headroom_run.argtypes = [
        ctypes.POINTER(_EpisodeInput), ctypes.c_int32, ctypes.POINTER(_HeadroomOutput)
    ]
    library.vnfc_headroom_run.restype = ctypes.c_int32
    if library.vnfc_headroom_sizeof_output() != ctypes.sizeof(_HeadroomOutput):
        raise RuntimeError("headroom analysis output layout differs")
    return library


def _command_rows(values: object, rows: int) -> tuple[tuple[int | None, ...], ...]:
    flat = tuple(int(value) for value in values)  # type: ignore[arg-type]
    return tuple(
        tuple(None if value == 255 else value for value in flat[4 * row : 4 * row + 4])
        for row in range(rows)
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
    }
