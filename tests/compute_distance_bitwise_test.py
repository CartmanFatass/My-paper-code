"""`_compute_distance` must equal the numpy expression it replaced, bit for bit.

It is 23.3% of a scenario-7 step at 2,896 calls/step, and almost none of that is
arithmetic -- it is numpy's per-call overhead paid on three elements. Scalar math
retires the overhead. But this function feeds every path loss, every routing
decision and every interference term in the D7.S audit, so "bitwise" is the only
acceptable standard and a tolerance here would be meaningless.

TWO THINGS THESE TESTS EXIST TO CATCH, both found by verification rather than by
reading:

1. **Grouping.** `np.sum` over a 3-element float64 array sums left to right, so
   `(dx*dx + dy*dy) + dz*dz` reproduces it and `dx*dx + (dy*dy + dz*dz)` does not.
   The re-associated control below differs on ~9% of adversarial pairs, which is
   what proves the comparison can see grouping at all. A test that only checked
   the current grouping against itself would pass under any regrouping.

2. **dtype.** `float()` promotes to double. A float32 position would be subtracted
   in double here and in single by the old expression. Measured: float64 gives 0
   mismatches over 20,500 pairs, **float32 gives 12,000**. Every position array is
   float64 today; this file pins that, so a future narrowing fails here instead of
   silently changing every distance in the audit.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def _old(pos1, pos2):
    """The expression that was replaced."""
    return np.sqrt(np.sum((pos1 - pos2) ** 2))


def _reassociated(pos1, pos2):
    """The control. Same values, different grouping."""
    dx = float(pos1[0]) - float(pos2[0])
    dy = float(pos1[1]) - float(pos2[1])
    dz = float(pos1[2]) - float(pos2[2])
    return np.float64(math.sqrt(dx * dx + (dy * dy + dz * dz)))


def _cases(dtype, seed=4242):
    rng = np.random.default_rng(seed)
    out = []
    for scale in (1.0, 1e-8, 1e8, 1e150, 5e-324):
        out.append((rng.random((300, 3)).astype(dtype) * scale,
                    rng.random((300, 3)).astype(dtype) * scale))
    same = rng.random((100, 3)).astype(dtype)
    out.append((same, same.copy()))          # coincident points
    return out


def _env():
    import audit_d7_s_event_aligned as audit

    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=20260725)
    return audit.build_pinned_env(config, episode_seed=20260725, coords=coords,
                                  coord_hash=coord_hash, energy_stage="S3",
                                  user_world_seed=20260725)


def test_float64_is_bitwise_identical_to_the_replaced_expression() -> None:
    env = _env()
    mismatches = total = 0
    for left, right in _cases(np.float64):
        for a, b in zip(left, right):
            total += 1
            got = env._compute_distance(a, b)
            want = _old(a, b)
            if np.float64(got).tobytes() != np.float64(want).tobytes():
                mismatches += 1
    assert total > 1500
    assert mismatches == 0, f"{mismatches} of {total} distances differ from numpy"


def test_the_comparison_can_tell_grouping_apart() -> None:
    """Without this, the test above passes under any regrouping."""

    differing = total = 0
    for left, right in _cases(np.float64):
        for a, b in zip(left, right):
            total += 1
            if np.float64(_reassociated(a, b)).tobytes() != np.float64(_old(a, b)).tobytes():
                differing += 1
    assert differing > 0, (
        "a re-associated sum matched numpy everywhere, so this comparison cannot "
        "see grouping and the bitwise test above proves nothing")


def test_every_position_array_is_float64() -> None:
    """THE dtype GUARD. float32 gave 12,000 mismatches of 20,500, so a narrowed
    position array would silently change every distance in the audit."""

    env = _env()
    for name in ("uav_positions", "user_positions", "ground_bs_positions",
                 "charging_station_positions"):
        value = getattr(env, name, None)
        assert value is not None, f"{name} is absent"
        assert np.asarray(value).dtype == np.float64, (
            f"{name} is {np.asarray(value).dtype}, not float64. `_compute_distance` "
            f"promotes via float() and is only bitwise-faithful for float64 inputs.")


def test_float32_would_diverge_which_is_why_the_guard_exists() -> None:
    """Pins the hazard itself, so the guard above cannot be dismissed as
    theoretical. If numpy ever made these agree, this test says so loudly rather
    than leaving a stale warning in the docstring."""

    env = _env()
    mismatches = total = 0
    for left, right in _cases(np.float32, seed=99):
        for a, b in zip(left, right):
            total += 1
            if np.float64(env._compute_distance(a, b)).tobytes() != np.float64(_old(a, b)).tobytes():
                mismatches += 1
    assert mismatches > 0, (
        "float32 inputs now agree; the dtype guard's rationale has changed and the "
        "docstring needs updating rather than the guard being relaxed")


def test_coincident_points_stay_divisible() -> None:
    """The np.float64 return is load-bearing: a Python float raises
    ZeroDivisionError where np.float64 yields inf, and uav-against-itself in the
    air-to-air loop makes a zero distance reachable."""

    env = _env()
    zero = np.zeros(3, dtype=np.float64)
    distance = env._compute_distance(zero, zero)
    assert float(distance) == 0.0
    with np.errstate(divide="ignore"):
        assert np.isinf(1.0 / distance), (
            "a zero distance must divide to inf, not raise -- the air-to-air loop "
            "relies on it")
