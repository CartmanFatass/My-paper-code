"""Moving the finiteness scan must not lose it.

MEASURED 2026-07-30. `_float_array` ran `np.all(np.isfinite(...))` once per member
per array -- 18 calls per step on the generic-SHORT testbed, ~19% of a step -- while
`_observation_matrix` had already built one contiguous `(n, OBSERVATION_DIM)` block
that can be scanned in a single call. The scan was relocated to the matrix and
`BoundaryMember.make` is told `finite_checked=True`.

```text
np.all calls over 2000 steps    before 35,966   after 10,134
np.all cumulative time          before 0.158 s  after 0.034 s
```

Coverage is RELOCATED, not reduced: every value is still scanned exactly once, and
`_float_array` still copies every row. These tests pin that, because the risk of
this change is precisely that a skipped scan becomes an unscanned value.

Wall-clock is deliberately not asserted here. The box varied ~3x between
measurement blocks on identical code, so a timing assertion would be a flake
generator; the call-count reduction is exact and machine-independent.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ha_ctse_process import dynamic_roster_testbed as testbed  # noqa: E402
from ha_ctse_process.variable_roster_event import BoundaryMember, _float_array  # noqa: E402


def _env_with_active_member():
    """Lifecycles start NOT_JOINED and join over time, so `active_keys` is empty at
    construction. Advance until at least one member is ACTIVE."""

    env = testbed.GenericShortDynamicRosterEnv(
        testbed.make_dynamic_roster_ledger(1, master_seed=testbed.TRAIN_LEDGER_SEED))
    for _ in range(testbed.HORIZON):
        if env.active_keys:
            return env
        transaction = env.event_transaction()
        members = transaction.post_membership_pre_policy_snapshot.members
        env.step({int(m.lifecycle_key): testbed.IDLE for m in members})
    raise AssertionError("no lifecycle became active within the horizon")


def test_default_still_scans() -> None:
    """Every pre-existing caller keeps its own check."""

    with pytest.raises(ValueError, match="non-finite"):
        _float_array([1.0, np.nan, 3.0], size=3, name="observation")


def test_finite_checked_skips_only_the_scan() -> None:
    """It must skip the scan and NOTHING else -- shape check and copy both stay."""

    source = np.array([1.0, np.nan, 3.0], dtype=np.float32)
    out = _float_array(source, size=3, name="observation", finite_checked=True)
    assert np.isnan(out[1]), "the scan was supposed to be skipped here"

    # the copy is load-bearing: a digest over values cannot see a shared reference
    assert out is not source
    out[0] = 99.0
    assert float(source[0]) == 1.0, "the copy was dropped along with the scan"

    # the shape check must survive
    with pytest.raises(ValueError, match="must have shape"):
        _float_array([1.0, 2.0], size=3, name="observation", finite_checked=True)


def test_boundary_member_forwards_the_flag() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        BoundaryMember.make("k", 0, [np.nan, 0.0], [0.0, 0.0],
                            obs_dim=2, critic_member_dim=2)
    member = BoundaryMember.make("k", 0, [np.nan, 0.0], [0.0, 0.0],
                                 obs_dim=2, critic_member_dim=2, finite_checked=True)
    assert np.isnan(member.observation[0])


def test_the_matrix_scan_catches_a_non_finite_value() -> None:
    """THE RELOCATED GUARD. If this cannot go red, the change deleted a check.

    A non-finite value is injected through the one input `_observation_matrix`
    reads from the lifecycle state, so the scan is exercised the way a real
    corruption would exercise it.
    """

    env = _env_with_active_member()
    keys = env.active_keys
    assert keys, "need at least one active lifecycle to test the scan"

    # SHORT_STREAK_TARGET divides short_streak in the matrix builder, so a NaN
    # streak reaches the block through normal arithmetic.
    env.lifecycles[keys[0]].short_streak = float("nan")
    with pytest.raises(ValueError, match="observation matrix contains a non-finite"):
        env._observation_matrix(keys)


def test_a_snapshot_still_refuses_a_non_finite_observation() -> None:
    """End to end on the path that now passes finite_checked=True. Without the
    matrix scan this would hand a NaN observation to the collector silently."""

    env = _env_with_active_member()
    keys = env.active_keys
    env.lifecycles[keys[0]].active_steps = float("inf")
    with pytest.raises(ValueError, match="non-finite"):
        env._event_snapshot()


def test_the_scan_lives_with_the_only_writer() -> None:
    """It is inside `_observation_matrix`, not in its caller, so a coordinate added
    later cannot escape the scan by the caller forgetting to run it."""

    source = (ROOT / "ha_ctse_process" / "dynamic_roster_testbed.py").read_text(
        encoding="utf-8")
    start = source.index("def _observation_matrix")
    block = source[start:source.index("def _observation_for")]
    assert "np.all(np.isfinite(rows))" in block
    assert "return rows" in block.split("np.all(np.isfinite(rows))")[1], (
        "the scan must run BEFORE the rows are returned")
