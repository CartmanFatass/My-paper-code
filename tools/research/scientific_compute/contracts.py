from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np


Mode = Literal["exact", "approximate"]
NanPolicy = Literal["forbid", "equal", "unequal"]
InfPolicy = Literal["forbid", "equal", "unequal"]
SignedZeroPolicy = Literal["distinguish", "equal"]
Order = Literal["C", "F"]

_NUMERIC_KINDS = frozenset("biufc")


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _json_value(value.item())
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, float):
        if np.isnan(value):
            return {"nonfinite": "nan"}
        if np.isposinf(value):
            return {"nonfinite": "+inf"}
        if np.isneginf(value):
            return {"nonfinite": "-inf"}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return repr(value)


@dataclass(frozen=True)
class ArrayContract:
    dtype: str
    shape: tuple[int, ...]
    order: Order
    nan_policy: NanPolicy
    inf_policy: InfPolicy
    signed_zero_policy: SignedZeroPolicy
    units: str
    device: str

    def __post_init__(self) -> None:
        if not isinstance(self.dtype, str):
            raise ValueError("dtype must be an explicit NumPy dtype string")
        try:
            parsed_dtype = np.dtype(self.dtype)
        except TypeError as exc:
            raise ValueError(f"invalid dtype {self.dtype!r}") from exc
        if parsed_dtype.kind not in _NUMERIC_KINDS or parsed_dtype.hasobject:
            raise ValueError("dtype must be a non-object boolean, integer, floating, or complex dtype")
        if any(isinstance(size, bool) or not isinstance(size, int) or size < 0 for size in self.shape):
            raise ValueError("shape dimensions must be non-negative integers")
        if self.order not in ("C", "F"):
            raise ValueError("order must be 'C' or 'F'")
        if self.nan_policy not in ("forbid", "equal", "unequal"):
            raise ValueError("nan_policy must be forbid, equal, or unequal")
        if self.inf_policy not in ("forbid", "equal", "unequal"):
            raise ValueError("inf_policy must be forbid, equal, or unequal")
        if self.signed_zero_policy not in ("distinguish", "equal"):
            raise ValueError("signed_zero_policy must be distinguish or equal")
        if self.device != "cpu":
            raise ValueError("NumPy artifact contracts support only the explicit device 'cpu'")
        if not isinstance(self.units, str) or not self.units.strip():
            raise ValueError("units must be explicit; use 'dimensionless' when applicable")

    @property
    def numpy_dtype(self) -> np.dtype[Any]:
        return np.dtype(self.dtype)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device": self.device,
            "dtype": self.dtype,
            "dtype_canonical": self.numpy_dtype.str,
            "inf_policy": self.inf_policy,
            "nan_policy": self.nan_policy,
            "order": self.order,
            "shape": list(self.shape),
            "signed_zero_policy": self.signed_zero_policy,
            "units": self.units,
        }


@dataclass(frozen=True)
class ToleranceContract:
    atol: float
    rtol: float
    justification: str

    def __post_init__(self) -> None:
        for name, value in (("atol", self.atol), ("rtol", self.rtol)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a finite non-negative number")
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative number")
        if not isinstance(self.justification, str) or not self.justification.strip():
            raise ValueError("approximate comparison requires a tolerance justification")

    def to_dict(self) -> dict[str, Any]:
        return {
            "atol": float(self.atol),
            "formula": "abs(actual - expected) <= atol + rtol * abs(expected)",
            "justification": self.justification,
            "rtol": float(self.rtol),
        }


@dataclass(frozen=True)
class ComparisonContract:
    mode: Mode
    array: ArrayContract
    oracle: str
    algorithm: str
    algorithm_version: str
    tolerance: ToleranceContract | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("exact", "approximate"):
            raise ValueError("mode must be exact or approximate")
        labels = (self.oracle, self.algorithm, self.algorithm_version)
        if any(not isinstance(value, str) or not value.strip() for value in labels):
            raise ValueError("oracle, algorithm, and algorithm_version must be explicit")
        if self.mode == "exact":
            if self.tolerance is not None:
                raise ValueError("exact mode rejects tolerances; exact identity is a byte comparison")
            if self.array.signed_zero_policy != "distinguish":
                raise ValueError("exact mode requires signed_zero_policy='distinguish'")
        elif self.tolerance is None:
            raise ValueError("approximate mode requires an explicit ToleranceContract")

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "algorithm_version": self.algorithm_version,
            "array": self.array.to_dict(),
            "mode": self.mode,
            "oracle": self.oracle,
            "tolerance": None if self.tolerance is None else self.tolerance.to_dict(),
        }


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    expected: Any
    actual: Any
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "actual": _json_value(self.actual),
            "expected": _json_value(self.expected),
            "name": self.name,
            "ok": self.ok,
        }
        if self.details is not None:
            result["details"] = _json_value(self.details)
        return result


def _layout_matches(array: np.ndarray[Any, Any], order: Order) -> bool:
    return bool(array.flags.c_contiguous if order == "C" else array.flags.f_contiguous)


def _layout_label(array: np.ndarray[Any, Any]) -> str:
    if array.flags.c_contiguous and array.flags.f_contiguous:
        return "C+F"
    if array.flags.c_contiguous:
        return "C"
    if array.flags.f_contiguous:
        return "F"
    return "noncontiguous"


def canonical_array_bytes(array: np.ndarray[Any, Any], *, order: Order) -> bytes:
    """Return a documented canonical identity encoding without dtype/value coercion."""
    if array.dtype.hasobject:
        raise ValueError("object arrays have no stable canonical byte identity")
    if not _layout_matches(array, order):
        raise ValueError(f"array is not {order}-contiguous; refusing to normalize its layout")
    header = json.dumps(
        {
            "dtype": array.dtype.str,
            "order": order,
            "schema_version": 1,
            "shape": list(array.shape),
        },
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return len(header).to_bytes(8, "big") + header + array.tobytes(order=order)


def canonical_array_sha256(array: np.ndarray[Any, Any], *, order: Order) -> str:
    return hashlib.sha256(canonical_array_bytes(array, order=order)).hexdigest()


def _array_checks(label: str, array: np.ndarray[Any, Any], contract: ArrayContract) -> list[Check]:
    numeric = array.dtype.kind in _NUMERIC_KINDS and not array.dtype.hasobject
    nan_count = int(np.count_nonzero(np.isnan(array))) if numeric else None
    inf_count = int(np.count_nonzero(np.isinf(array))) if numeric else None
    return [
        Check(f"{label}.dtype", array.dtype == contract.numpy_dtype, contract.numpy_dtype.str, array.dtype.str),
        Check(f"{label}.shape", array.shape == contract.shape, list(contract.shape), list(array.shape)),
        Check(f"{label}.order", _layout_matches(array, contract.order), contract.order, _layout_label(array)),
        Check(f"{label}.nan_policy", numeric and (contract.nan_policy != "forbid" or nan_count == 0), contract.nan_policy, {"nan_count": nan_count}),
        Check(f"{label}.inf_policy", numeric and (contract.inf_policy != "forbid" or inf_count == 0), contract.inf_policy, {"inf_count": inf_count}),
    ]


def _summary(array: np.ndarray[Any, Any], contract: ArrayContract) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "byte_count": int(array.nbytes),
        "dtype": array.dtype.str,
        "shape": list(array.shape),
    }
    if _layout_matches(array, contract.order) and not array.dtype.hasobject:
        identity = canonical_array_bytes(array, order=contract.order)
        summary["canonical_byte_count"] = len(identity)
        summary["canonical_sha256"] = hashlib.sha256(identity).hexdigest()
    else:
        summary["canonical_byte_count"] = None
        summary["canonical_sha256"] = None
    return summary


def _pair_policy_checks(expected: np.ndarray[Any, Any], actual: np.ndarray[Any, Any], contract: ArrayContract) -> tuple[Check, Check, Check]:
    expected_nan = np.isnan(expected)
    actual_nan = np.isnan(actual)
    if contract.nan_policy == "equal":
        nan_ok = bool(np.array_equal(expected_nan, actual_nan))
    else:
        nan_ok = not bool(np.any(expected_nan) or np.any(actual_nan))

    expected_inf = np.isinf(expected)
    actual_inf = np.isinf(actual)
    if contract.inf_policy == "equal":
        inf_ok = bool(np.array_equal(expected_inf, actual_inf))
        if inf_ok and np.any(expected_inf):
            inf_ok = bool(np.array_equal(expected[expected_inf], actual[actual_inf]))
    else:
        inf_ok = not bool(np.any(expected_inf) or np.any(actual_inf))

    zero_pairs = (expected == 0) & (actual == 0)
    if contract.signed_zero_policy == "distinguish" and np.any(zero_pairs):
        if expected.dtype.kind == "c" or actual.dtype.kind == "c":
            expected_signs = np.stack(
                (np.signbit(expected.real[zero_pairs]), np.signbit(expected.imag[zero_pairs])),
                axis=-1,
            )
            actual_signs = np.stack(
                (np.signbit(actual.real[zero_pairs]), np.signbit(actual.imag[zero_pairs])),
                axis=-1,
            )
            signed_zero_ok = bool(np.array_equal(expected_signs, actual_signs))
        elif expected.dtype.kind == "f" or actual.dtype.kind == "f":
            signed_zero_ok = bool(np.array_equal(np.signbit(expected[zero_pairs]), np.signbit(actual[zero_pairs])))
        else:
            signed_zero_ok = True
    else:
        signed_zero_ok = True
    return (
        Check("values.nan_policy", nan_ok, contract.nan_policy, {"actual_nan_count": int(np.count_nonzero(actual_nan)), "expected_nan_count": int(np.count_nonzero(expected_nan))}),
        Check("values.inf_policy", inf_ok, contract.inf_policy, {"actual_inf_count": int(np.count_nonzero(actual_inf)), "expected_inf_count": int(np.count_nonzero(expected_inf))}),
        Check("values.signed_zero_policy", signed_zero_ok, contract.signed_zero_policy, contract.signed_zero_policy),
    )


def _approximate_check(expected: np.ndarray[Any, Any], actual: np.ndarray[Any, Any], tolerance: ToleranceContract) -> Check:
    comparable = np.isfinite(expected) & np.isfinite(actual)
    if not np.any(comparable):
        return Check("values.approximate", True, tolerance.to_dict(), {"compared_count": 0}, {"max_abs_error": None, "max_allowed_error": None})

    work_dtype = np.result_type(expected.dtype, actual.dtype, np.float64)
    expected_values = expected[comparable].astype(work_dtype, copy=False)
    actual_values = actual[comparable].astype(work_dtype, copy=False)
    with np.errstate(over="ignore", invalid="ignore"):
        errors = np.abs(actual_values - expected_values)
        allowed = tolerance.atol + tolerance.rtol * np.abs(expected_values)
        within = errors <= allowed
    max_error = float(np.max(errors))
    max_allowed = float(np.max(allowed))
    return Check(
        "values.approximate",
        bool(np.all(within)),
        tolerance.to_dict(),
        {"compared_count": int(np.count_nonzero(comparable))},
        {"max_abs_error": max_error, "max_allowed_error": max_allowed},
    )


def compare_arrays(expected: np.ndarray[Any, Any], actual: np.ndarray[Any, Any], contract: ComparisonContract) -> dict[str, Any]:
    if not isinstance(expected, np.ndarray) or not isinstance(actual, np.ndarray):
        raise TypeError("expected and actual must be NumPy arrays")

    checks = _array_checks("expected", expected, contract.array)
    checks.extend(_array_checks("actual", actual, contract.array))
    same_shape = expected.shape == actual.shape
    numeric_pair = (
        expected.dtype.kind in _NUMERIC_KINDS
        and actual.dtype.kind in _NUMERIC_KINDS
        and not expected.dtype.hasobject
        and not actual.dtype.hasobject
    )
    if same_shape and numeric_pair:
        checks.extend(_pair_policy_checks(expected, actual, contract.array))
    else:
        reason = "shape mismatch" if not same_shape else "unsupported non-numeric dtype"
        checks.extend(
            [
                Check("values.nan_policy", False, contract.array.nan_policy, f"not compared: {reason}"),
                Check("values.inf_policy", False, contract.array.inf_policy, f"not compared: {reason}"),
                Check("values.signed_zero_policy", False, contract.array.signed_zero_policy, f"not compared: {reason}"),
            ]
        )

    layouts_ok = _layout_matches(expected, contract.array.order) and _layout_matches(actual, contract.array.order)
    if contract.mode == "exact":
        byte_equal = False
        if layouts_ok and not expected.dtype.hasobject and not actual.dtype.hasobject:
            byte_equal = canonical_array_bytes(expected, order=contract.array.order) == canonical_array_bytes(actual, order=contract.array.order)
        checks.append(Check("values.exact_canonical_bytes", byte_equal, "identical canonical bytes", "identical" if byte_equal else "different"))
    elif same_shape and numeric_pair:
        assert contract.tolerance is not None
        checks.append(_approximate_check(expected, actual, contract.tolerance))
    else:
        reason = "shape mismatch" if not same_shape else "unsupported non-numeric dtype"
        checks.append(Check("values.approximate", False, contract.tolerance.to_dict() if contract.tolerance else None, f"not compared: {reason}"))

    result_checks = [check.to_dict() for check in checks]
    ok = all(check.ok for check in checks)
    return {
        "actual": _summary(actual, contract.array),
        "checks": result_checks,
        "contract": contract.to_dict(),
        "expected": _summary(expected, contract.array),
        "mode": contract.mode,
        "ok": ok,
        "schema_version": 1,
        "status": "PASS" if ok else "MISMATCH",
        "tool": "scientific_compute.compare",
    }


def load_array(path: str | Path) -> np.ndarray[Any, Any]:
    loaded = np.load(Path(path), allow_pickle=False)
    if not isinstance(loaded, np.ndarray):
        if hasattr(loaded, "close"):
            loaded.close()
        raise ValueError("artifact must contain exactly one NumPy .npy array; .npz archives are not implicit")
    return loaded


def compare_artifacts(expected_path: str | Path, actual_path: str | Path, contract: ComparisonContract) -> dict[str, Any]:
    expected = load_array(expected_path)
    actual = load_array(actual_path)
    result = compare_arrays(expected, actual, contract)
    result["artifacts"] = {
        "actual": str(actual_path),
        "expected": str(expected_path),
    }
    return result
