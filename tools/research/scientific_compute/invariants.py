from __future__ import annotations

from typing import Any, Literal

import numpy as np
from scipy import linalg

from .contracts import ArrayContract, ToleranceContract


def assert_array_contract(array: np.ndarray[Any, Any], contract: ArrayContract, *, name: str = "array") -> None:
    if not isinstance(array, np.ndarray):
        raise AssertionError(f"{name} is not a NumPy array")
    if array.dtype != contract.numpy_dtype:
        raise AssertionError(f"{name} dtype {array.dtype.str} != required {contract.numpy_dtype.str}")
    if array.shape != contract.shape:
        raise AssertionError(f"{name} shape {array.shape!r} != required {contract.shape!r}")
    contiguous = array.flags.c_contiguous if contract.order == "C" else array.flags.f_contiguous
    if not contiguous:
        raise AssertionError(f"{name} is not {contract.order}-contiguous")
    nan_count = int(np.count_nonzero(np.isnan(array)))
    inf_count = int(np.count_nonzero(np.isinf(array)))
    if contract.nan_policy == "forbid" and nan_count:
        raise AssertionError(f"{name} contains {nan_count} NaN value(s)")
    if contract.inf_policy == "forbid" and inf_count:
        raise AssertionError(f"{name} contains {inf_count} infinite value(s)")


def assert_all_finite(array: np.ndarray[Any, Any], *, name: str = "array") -> None:
    invalid_count = int(np.count_nonzero(~np.isfinite(array)))
    if invalid_count:
        raise AssertionError(f"{name} contains {invalid_count} non-finite value(s)")


def assert_bounded(
    array: np.ndarray[Any, Any],
    *,
    lower: float,
    upper: float,
    name: str = "array",
    inclusive: bool = True,
) -> None:
    if not np.isfinite(lower) or not np.isfinite(upper) or lower > upper:
        raise ValueError("bounds must be finite and lower <= upper")
    assert_all_finite(array, name=name)
    valid = (array >= lower) & (array <= upper) if inclusive else (array > lower) & (array < upper)
    if not bool(np.all(valid)):
        violating = array[~valid]
        raise AssertionError(
            f"{name} has {violating.size} value(s) outside "
            f"{'[' if inclusive else '('}{lower}, {upper}{']' if inclusive else ')'}"
        )


def assert_monotonic(
    array: np.ndarray[Any, Any],
    *,
    axis: int = -1,
    direction: Literal["nondecreasing", "increasing", "nonincreasing", "decreasing"] = "nondecreasing",
    name: str = "array",
) -> None:
    if direction not in ("nondecreasing", "increasing", "nonincreasing", "decreasing"):
        raise ValueError("unsupported monotonic direction")
    assert_all_finite(array, name=name)
    differences = np.diff(array, axis=axis)
    predicates = {
        "nondecreasing": differences >= 0,
        "increasing": differences > 0,
        "nonincreasing": differences <= 0,
        "decreasing": differences < 0,
    }
    if not bool(np.all(predicates[direction])):
        count = int(np.count_nonzero(~predicates[direction]))
        raise AssertionError(f"{name} violates {direction} order at {count} adjacent pair(s) on axis {axis}")


def assert_normalized(
    weights: np.ndarray[Any, Any],
    *,
    axis: int,
    tolerance: ToleranceContract,
    name: str = "weights",
) -> None:
    assert_all_finite(weights, name=name)
    if np.any(weights < 0):
        raise AssertionError(f"{name} contains negative values")
    totals = np.sum(weights, axis=axis)
    allowed = tolerance.atol + tolerance.rtol
    errors = np.abs(totals - 1)
    if not bool(np.all(errors <= allowed)):
        raise AssertionError(
            f"{name} normalization max error {float(np.max(errors))!r} exceeds {float(allowed)!r}; "
            f"tolerance justification: {tolerance.justification}"
        )


def assert_linear_solution_residual(
    matrix: np.ndarray[Any, Any],
    solution: np.ndarray[Any, Any],
    right_hand_side: np.ndarray[Any, Any],
    *,
    tolerance: ToleranceContract,
    norm_order: int | float | str = 2,
    name: str = "linear solution",
) -> float:
    """Check ||A x - b|| <= atol + rtol ||b|| using SciPy's declared norm oracle."""
    assert_all_finite(matrix, name="matrix")
    assert_all_finite(solution, name="solution")
    assert_all_finite(right_hand_side, name="right_hand_side")
    residual = matrix @ solution - right_hand_side
    residual_norm = float(linalg.norm(residual, ord=norm_order))
    reference_norm = float(linalg.norm(right_hand_side, ord=norm_order))
    allowed = float(tolerance.atol + tolerance.rtol * reference_norm)
    if not np.isfinite(residual_norm):
        raise AssertionError(f"{name} residual norm is non-finite")
    if residual_norm > allowed:
        raise AssertionError(
            f"{name} residual norm {residual_norm!r} exceeds {allowed!r}; "
            f"tolerance justification: {tolerance.justification}"
        )
    return residual_norm
