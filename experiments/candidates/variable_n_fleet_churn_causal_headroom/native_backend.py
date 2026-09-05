"""Explicit Linux build and timing-only binding for synthetic R03 calibration."""

import ctypes as ct
import os
from pathlib import Path
import subprocess

_SOURCE = Path(__file__).with_name("native") / "calibration.cpp"
_ROOT = Path(__file__).resolve().parents[3]
_BINARY = _ROOT / "temp/directions/variable_n_fleet_churn/build/causal_r03/calibration.so"
_INCLUDE = _SOURCE.parents[2] / "variable_n_fleet_churn_headroom/native"


class _Score(ct.Structure):
    _fields_ = [("seconds", ct.c_double)] + [
        (name, ct.c_int32) for name in ("count", "scorer_checker", "enumerator", "records")
    ]


class _Unit(ct.Structure):
    _fields_ = [("seconds", ct.c_double), ("count", ct.c_int32)]


class _Calibration(ct.Structure):
    _fields_ = [("scores", _Score * 6), ("ticks", _Unit * 4), ("prehistory", _Unit)]


def build_native_backend() -> Path:
    """Compile explicitly before the separately admitted calibration invocation."""
    _BINARY.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        os.environ.get("CXX", "c++"), "-std=c++20", "-O2", "-fPIC", "-shared",
        "-fno-fast-math", "-ffp-contract=off", f"-I{_INCLUDE}",
        str(_SOURCE), "-o", str(_BINARY),
    ], check=True)
    return _BINARY


def calibrate_native() -> dict:
    """Load the prebuilt binary; return no commands, worlds, or endpoint values."""
    library = ct.CDLL(str(_BINARY))
    library.vnfc_causal_calibrate.argtypes = [ct.POINTER(_Calibration)]
    library.vnfc_causal_calibrate.restype = ct.c_int
    output = _Calibration()
    status = library.vnfc_causal_calibrate(ct.byref(output))
    if status:
        raise RuntimeError(f"native synthetic calibration failed: {status}")
    scores = [dict(
        epoch=epoch, seconds=row.seconds, candidate_count=row.count,
        scorer_checker_equal=bool(row.scorer_checker),
        independent_enumerator_equal=bool(row.enumerator),
        all_candidate_records_exact=bool(row.records),
        agreement=bool(row.scorer_checker and row.enumerator and row.records),
    ) for epoch, row in enumerate(output.scores)]
    cases = [dict(case=name, seconds=row.seconds, count=row.count) for name, row in zip(
        ("moving_7", "acquiring_7", "serving_7", "preloss_8"), output.ticks
    )]
    slowest = max(cases, key=lambda row: row["seconds"] / row["count"])
    return dict(
        scores=scores,
        ticks=dict(seconds=slowest["seconds"], count=slowest["count"], cases=cases),
        prehistory=dict(seconds=output.prehistory.seconds, calls=output.prehistory.count,
                        agents=8),
    )
