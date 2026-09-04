"""Source-keyed TEST-only C++ binding for the r05 measurement.

There is no production loader or Python execution fallback in this module.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Iterable, Sequence

from .contracts import NATIVE_ABI_VERSION, Q_E, TEST_SCHEMA, WIDTH_SWEEP


_ROOT = Path(__file__).resolve().parent
_NATIVE = _ROOT / "native"
_HEADER = _NATIVE / "vqfp_r05_measurement_abi.h"
_SOLVER_SOURCE = _NATIVE / "vqfp_r05_numeric_solver.cpp"
_CHECKER_SOURCE = _NATIVE / "vqfp_r05_checker.cpp"
_COMPILE_FLAGS = ("/nologo", "/std:c++20", "/O2", "/EHsc", "/LD", "/fp:strict")


class NativeMeasurementError(RuntimeError):
    """The frozen TEST-only native measurement failed closed."""


class NumericFixture(ctypes.Structure):
    _fields_ = [
        ("schema", ctypes.c_uint32),
        ("kind", ctypes.c_uint32),
        ("input_bits", ctypes.c_uint64),
        ("expected_bits", ctypes.c_uint64),
        ("argument_num", ctypes.c_uint64),
        ("argument_den", ctypes.c_uint64),
        ("lower_num", ctypes.c_uint64),
        ("lower_den", ctypes.c_uint64),
        ("upper_num", ctypes.c_uint64),
        ("upper_den", ctypes.c_uint64),
        ("certificate_kind", ctypes.c_uint32),
        ("precision_bits", ctypes.c_uint32),
    ]


class NumericResult(ctypes.Structure):
    _fields_ = [
        ("output_bits", ctypes.c_uint64),
        ("evaluated", ctypes.c_uint32),
        ("exact_match", ctypes.c_uint32),
        ("certificate_bytes", ctypes.c_uint64),
    ]


class AnalyticState(ctypes.Structure):
    _fields_ = [
        ("schema", ctypes.c_uint32),
        ("n_agents", ctypes.c_uint32),
        ("kind", ctypes.c_uint32),
        ("variant", ctypes.c_uint32),
        ("q_e", ctypes.c_uint64),
        ("relay_threshold", ctypes.c_uint64),
    ]


class AnalyticResult(ctypes.Structure):
    _fields_ = [
        ("counts", ctypes.c_uint64 * 24),
        ("objective_bits", ctypes.c_uint64),
        ("node_count", ctypes.c_uint64),
        ("certificate_bytes", ctypes.c_uint64),
        ("proof_kind", ctypes.c_uint32),
        ("solved", ctypes.c_uint32),
    ]


class CheckResult(ctypes.Structure):
    _fields_ = [
        ("accepted", ctypes.c_uint32),
        ("exact_counts", ctypes.c_uint32),
        ("exact_objective", ctypes.c_uint32),
        ("certificate_valid", ctypes.c_uint32),
    ]


def _source_digest() -> str:
    digest = hashlib.sha256()
    for path in (_HEADER, _SOLVER_SOURCE, _CHECKER_SOURCE):
        payload = path.read_bytes()
        name = path.name.encode("utf-8")
        digest.update(len(name).to_bytes(4, "big"))
        digest.update(name)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise NativeMeasurementError("Visual Studio locator is unavailable")
    completed = subprocess.run(
        [
            str(locator),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    installation = Path(completed.stdout.strip())
    if not installation.is_dir():
        raise NativeMeasurementError("MSVC build tools are unavailable")
    return installation


def _compiler_path() -> Path:
    candidates = tuple(
        path
        for path in (_vs_installation() / "VC" / "Tools" / "MSVC").glob(
            "*/bin/Hostx64/x64/cl.exe"
        )
        if path.is_file()
    )
    if not candidates:
        raise NativeMeasurementError("the x64 MSVC compiler is unavailable")
    return max(candidates, key=lambda path: tuple(int(part) for part in path.parts[-5].split(".")))


@functools.lru_cache(maxsize=1)
def native_build_key() -> str:
    compiler = _compiler_path().resolve()
    digest = hashlib.sha256()
    digest.update(b"VQFP-FERL-R05-TEST-NUMERIC-ANALYTIC-v1\0")
    digest.update(_source_digest().encode("ascii"))
    digest.update(hashlib.sha256(compiler.read_bytes()).digest())
    for flag in _COMPILE_FLAGS:
        digest.update(flag.encode("ascii"))
        digest.update(b"\0")
    digest.update(NATIVE_ABI_VERSION.to_bytes(4, "big"))
    return digest.hexdigest()


def _build_root() -> Path:
    configured = os.environ.get("HMASD_VQFP_R05_TEST_NATIVE_CACHE")
    root = (
        Path(configured).expanduser().resolve()
        if configured
        else Path(tempfile.gettempdir()).resolve() / "hmasd_vqfp_r05_test_native"
    )
    return root / native_build_key()


def _compile(source: Path, target: Path) -> None:
    if target.is_file():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    obj = target.with_suffix(".obj")
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(_COMPILE_FLAGS)} '
        f'/I"{_NATIVE}" "{source}" /Fo:"{obj}" /link /OUT:"{target}"'
    )
    completed = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=target.parent,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not target.is_file():
        raise NativeMeasurementError(
            f"native TEST-only compilation failed ({completed.returncode}):\n"
            f"{completed.stdout}\n{completed.stderr}"
        )


def _configure_solver(path: Path) -> ctypes.CDLL:
    library = ctypes.CDLL(str(path))
    library.vqfp_r05_measurement_abi_version.argtypes = []
    library.vqfp_r05_measurement_abi_version.restype = ctypes.c_uint32
    if library.vqfp_r05_measurement_abi_version() != NATIVE_ABI_VERSION:
        raise NativeMeasurementError("solver ABI mismatch")
    library.vqfp_r05_numeric_batch.argtypes = [
        ctypes.POINTER(NumericFixture),
        ctypes.c_uint32,
        ctypes.POINTER(NumericResult),
    ]
    library.vqfp_r05_numeric_batch.restype = ctypes.c_int32
    library.vqfp_r05_solve_analytic_batch.argtypes = [
        ctypes.POINTER(AnalyticState),
        ctypes.c_uint32,
        ctypes.POINTER(AnalyticResult),
    ]
    library.vqfp_r05_solve_analytic_batch.restype = ctypes.c_int32
    return library


def _configure_checker(path: Path) -> ctypes.CDLL:
    library = ctypes.CDLL(str(path))
    library.vqfp_r05_checker_abi_version.argtypes = []
    library.vqfp_r05_checker_abi_version.restype = ctypes.c_uint32
    if library.vqfp_r05_checker_abi_version() != NATIVE_ABI_VERSION:
        raise NativeMeasurementError("checker ABI mismatch")
    library.vqfp_r05_check_numeric_batch.argtypes = [
        ctypes.POINTER(NumericFixture),
        ctypes.POINTER(NumericResult),
        ctypes.c_uint32,
        ctypes.POINTER(CheckResult),
    ]
    library.vqfp_r05_check_numeric_batch.restype = ctypes.c_int32
    library.vqfp_r05_check_analytic_batch.argtypes = [
        ctypes.POINTER(AnalyticState),
        ctypes.POINTER(AnalyticResult),
        ctypes.c_uint32,
        ctypes.POINTER(CheckResult),
    ]
    library.vqfp_r05_check_analytic_batch.restype = ctypes.c_int32
    return library


@functools.lru_cache(maxsize=1)
def require_native_pair() -> tuple[ctypes.CDLL, ctypes.CDLL]:
    root = _build_root()
    solver_path = root / "vqfp_r05_test_solver.dll"
    checker_path = root / "vqfp_r05_test_checker.dll"
    _compile(_SOLVER_SOURCE, solver_path)
    _compile(_CHECKER_SOURCE, checker_path)
    return _configure_solver(solver_path), _configure_checker(checker_path)


def artifact_identity() -> dict[str, object]:
    started = time.perf_counter()
    require_native_pair()
    elapsed = time.perf_counter() - started
    root = _build_root()
    solver = root / "vqfp_r05_test_solver.dll"
    checker = root / "vqfp_r05_test_checker.dll"
    return {
        "schema": "VQFP_FERL_R05_TEST_NATIVE_PAIR_V1",
        "test_only": True,
        "source_sha256": _source_digest(),
        "build_key": native_build_key(),
        "abi_version": NATIVE_ABI_VERSION,
        "compile_or_load_wall_seconds": elapsed,
        "solver": {
            "path": str(solver),
            "sha256": hashlib.sha256(solver.read_bytes()).hexdigest(),
            "bytes": solver.stat().st_size,
        },
        "checker": {
            "path": str(checker),
            "sha256": hashlib.sha256(checker.read_bytes()).hexdigest(),
            "bytes": checker.stat().st_size,
        },
        "python_fallback": False,
        "production_registry_entry": False,
    }


def _require_width(width: int) -> int:
    if isinstance(width, bool) or width not in WIDTH_SWEEP:
        raise ValueError(f"width must be one of {WIDTH_SWEEP}")
    return width


def run_numeric_batch(fixtures: Sequence[NumericFixture]) -> tuple[NumericResult, ...]:
    width = _require_width(len(fixtures))
    solver, checker = require_native_pair()
    inputs = (NumericFixture * width)(*fixtures)
    outputs = (NumericResult * width)()
    checks = (CheckResult * width)()
    status = solver.vqfp_r05_numeric_batch(inputs, width, outputs)
    if status != 0:
        raise NativeMeasurementError(f"numeric batch failed with status {status}")
    status = checker.vqfp_r05_check_numeric_batch(inputs, outputs, width, checks)
    if status != 0 or any(not check.accepted for check in checks):
        raise NativeMeasurementError("numeric certificate checker rejected a fixture batch")
    return tuple(outputs)


def solve_analytic_batch(states: Sequence[AnalyticState]) -> tuple[AnalyticResult, ...]:
    width = _require_width(len(states))
    solver, checker = require_native_pair()
    inputs = (AnalyticState * width)(*states)
    outputs = (AnalyticResult * width)()
    checks = (CheckResult * width)()
    status = solver.vqfp_r05_solve_analytic_batch(inputs, width, outputs)
    if status != 0:
        raise NativeMeasurementError(f"analytic batch failed with status {status}")
    status = checker.vqfp_r05_check_analytic_batch(inputs, outputs, width, checks)
    if status != 0 or any(not check.accepted for check in checks):
        raise NativeMeasurementError("analytic checker rejected a fixture batch")
    return tuple(outputs)


def analytic_result_record(result: AnalyticResult) -> tuple[object, ...]:
    return (
        tuple(int(value) for value in result.counts),
        int(result.objective_bits),
        int(result.node_count),
        int(result.certificate_bytes),
        int(result.proof_kind),
        int(result.solved),
    )


def numeric_result_record(result: NumericResult) -> tuple[int, ...]:
    return (
        int(result.output_bits),
        int(result.evaluated),
        int(result.exact_match),
        int(result.certificate_bytes),
    )


__all__ = [
    "AnalyticResult",
    "AnalyticState",
    "CheckResult",
    "NativeMeasurementError",
    "NumericFixture",
    "NumericResult",
    "Q_E",
    "TEST_SCHEMA",
    "analytic_result_record",
    "artifact_identity",
    "numeric_result_record",
    "require_native_pair",
    "run_numeric_batch",
    "solve_analytic_batch",
]

