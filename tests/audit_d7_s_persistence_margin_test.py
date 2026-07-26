"""Focused regression tests for the D7.S part B persistence-margin audit.

Two defects found on 2026-07-25 when the G2-instance result came back with
`charge_steps = 647.5` and `dock_events = 0.0` in the same arm -- an arithmetically
impossible pair, since charging steps cannot accumulate without a rising edge.

  1. `dock_events` was structurally pinned to zero by numpy aliasing (fixed here).
  2. `set_flex` is definitionally identical to `constructive` (pinned, NOT fixed --
     it is a frozen design element and its correction is External Pro's ruling).
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "audit_d7_s_persistence_margin",
    _ROOT / "scripts" / "audit_d7_s_persistence_margin.py",
)
audit = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = audit
_SPEC.loader.exec_module(audit)


class FakeEnv:
    """Minimal stand-in exposing exactly the surface `run_arm_stepped` touches.

    `step` mutates `uav_charging` **in place**, which is what the real scenario
    does (`scenario7:1698,1747`) and is the precondition for the aliasing defect.
    """

    def __init__(self, schedule: np.ndarray):
        self.schedule = np.asarray(schedule, dtype=bool)
        self.n_uavs = 4
        self.n_users = 6
        self.action_dim = 4
        self.time_step = 1.0
        self.max_speed = 30.0
        self.dock_request_threshold = 0.5
        self.return_reserve_ratio = 0.10
        self.charging_capture_radius_m = 20.0
        self.n_charging_stations = 1
        self.charging_station_positions = np.array([[0.0, 0.0, 0.0]])
        self.ground_bs_positions = np.array([[0.0, 0.0, 0.0]])
        self.user_qos_rate_mbps = 1.0
        self.agents = [f"uav_{i}" for i in range(self.n_uavs)]
        self.uav_charging = np.zeros(self.n_uavs, dtype=bool)
        self._t = 0
        self.reset(seed=0)

    def reset(self, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.user_positions = rng.uniform(0.0, 1000.0, size=(self.n_users, 3))
        self.uav_positions = rng.uniform(0.0, 1000.0, size=(self.n_uavs, 3))
        self._drift = rng.uniform(-4.0, 4.0, size=(self.n_users, 2))
        self.uav_battery_ratios = np.full(self.n_uavs, 0.9)
        # in-place reset, mirroring the real env
        self.uav_charging[:] = False
        self._t = 0

    def _update_return_energy_state(self):
        pass

    def estimate_heuristic_qos_feasibility(self):
        return {"service_uavs": 2, "height_m": 100.0}

    def step(self, actions):
        # UAVs must actually move, or every arm is trivially identical and the
        # arm-semantics tests below pass vacuously. Mirrors the real integration:
        # act[:3] are normalized velocities scaled by max_speed.
        for idx, agent in enumerate(self.agents):
            act = np.asarray(actions[agent], dtype=float)
            self.uav_positions[idx] += act[:3] * self.max_speed * self.time_step
        # Users must drift, or a refreshed duty target equals the frozen one and
        # the keep arms collapse onto constructive.
        self.user_positions[:, :2] += self._drift
        row = self.schedule[min(self._t, len(self.schedule) - 1)]
        self.uav_charging[:] = row        # IN PLACE, as the real scenario does
        self._t += 1

    def _update_channel_state(self):
        pass

    def _update_uav_connections(self):
        pass

    def _compute_routing_paths(self):
        pass

    def _calculate_end_to_end_user_rates(self):
        # Deterministic and layout-sensitive, so arms can differ.
        spread = float(np.mean(np.linalg.norm(self.uav_positions[:, :2], axis=1)))
        rates = np.full(self.n_users, 1e6 * (1.0 + spread / 1e4))
        return rates, None, None


def _run_env(schedule, arm="constructive", horizon=None):
    env = FakeEnv(schedule)
    horizon = len(schedule) if horizon is None else horizon
    out = audit.run_arm_stepped(
        env, seed=0, horizon=horizon, check_every=10, arm=arm,
        focal_stable=0, focal_flex=2,
    )
    return env, out


def _run(schedule, arm="constructive", horizon=None):
    return _run_env(schedule, arm=arm, horizon=horizon)[1]


def test_numpy_asarray_returns_the_same_object_for_a_matching_dtype():
    """The root cause, asserted directly so the fix's necessity is self-evident."""
    buf = np.zeros(4, dtype=bool)
    assert np.asarray(buf, dtype=bool) is buf
    assert np.asarray(buf, dtype=bool).copy() is not buf


def test_dock_events_counts_rising_edges_on_an_in_place_buffer():
    # uav 0: off,on,on,off,on  -> 2 rising edges
    # uav 1: on,on,on,on,on    -> 1 rising edge (from the all-False start)
    schedule = np.array([
        [0, 1, 0, 0],
        [1, 1, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [1, 1, 0, 0],
    ], dtype=bool)
    out = _run(schedule)
    assert out["dock_events"] == 3
    # charge_steps was never affected by the defect; it stays a plain occupancy sum.
    assert out["charge_steps"] == int(schedule.sum())


def test_dock_events_is_nonzero_whenever_charge_steps_is():
    """The exact impossible pair observed in the G2 run must be unreachable."""
    for on_at in range(4):
        schedule = np.zeros((5, 4), dtype=bool)
        schedule[on_at:, 0] = True
        out = _run(schedule)
        assert out["charge_steps"] > 0
        assert out["dock_events"] > 0, "charging accumulated with no rising edge"


def test_no_charging_gives_no_dock_events():
    out = _run(np.zeros((5, 4), dtype=bool))
    assert out["charge_steps"] == 0
    assert out["dock_events"] == 0


def test_set_flex_is_currently_identical_to_constructive():
    """PINNED DEFECT, deliberately not fixed here.

    The frozen design (`D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md:215`) defines
    `set_flex` as "that service UAV re-decides each check" -- which, since every
    other UAV also re-decides under `constructive`, is the constructive arm itself.

    So `U*_flex = set_flex - keep_flex = constructive - keep_flex`, and because
    `B_H = constructive - null`, the treatment arm and the normalizer share a term.
    D0 forbids exactly that: `B_H` "is never estimated from the treatment outcome".

    Correcting the arm is a protected-semantics change and belongs to External Pro,
    not to this repository. This test pins the present behaviour so the degeneracy
    stays visible and any change to it fails loudly rather than silently altering
    what the flex margin means.
    """
    schedule = np.zeros((12, 4), dtype=bool)
    a = _run(schedule, arm="constructive")
    b = _run(schedule, arm="set_flex")
    assert a["return"] == b["return"]
    assert a["charge_steps"] == b["charge_steps"]


def test_set_stable_is_a_genuine_exchange_and_differs_from_constructive():
    """The other SET arm *is* a forced exchange -- the asymmetry that makes the
    two margins incommensurable on one symmetric gate."""
    schedule = np.zeros((12, 4), dtype=bool)
    a = _run(schedule, arm="constructive")
    b = _run(schedule, arm="set_stable")
    assert a["return"] != b["return"]


def test_keep_arms_hold_for_the_whole_horizon_not_one_check_interval():
    """Records the Delta mismatch: D0 freezes Delta at one check interval, while a
    keep arm freezes its focal duty for the entire window.

    Demonstrated positionally rather than by return, so it states what the arm
    physically does: after 4 check boundaries the held UAV is still tracking its
    t=0 post, not the post its duty would have been reassigned to.
    """
    schedule = np.zeros((40, 4), dtype=bool)
    focal_flex = 2
    n_relay, n_service, height = 2, 2, 100.0

    fresh_env = FakeEnv(schedule)
    frozen_target = audit.duty_targets(fresh_env, n_relay, n_service, height)[focal_flex]

    env, _ = _run_env(schedule, arm="keep_flex", horizon=40)
    end_target = audit.duty_targets(env, n_relay, n_service, height)[focal_flex]
    pos = env.uav_positions[focal_flex]

    assert not np.allclose(frozen_target, end_target), "users must drift for this test"
    d_frozen = float(np.linalg.norm(pos[:2] - frozen_target[:2]))
    d_end = float(np.linalg.norm(pos[:2] - end_target[:2]))
    assert d_frozen < d_end, (
        "keep_flex should still be tracking its t=0 post after 4 check boundaries; "
        f"distance to frozen {d_frozen:.1f} vs to current {d_end:.1f}"
    )


def test_keep_flex_differs_from_constructive_when_the_layout_moves():
    """Guards the test fixture itself: if users did not drift, a refreshed target
    would equal the frozen one and every keep arm would collapse onto
    constructive, making the arm-semantics tests pass vacuously."""
    schedule = np.zeros((40, 4), dtype=bool)
    a = _run(schedule, arm="constructive", horizon=40)
    b = _run(schedule, arm="keep_flex", horizon=40)
    assert a["return"] != b["return"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
