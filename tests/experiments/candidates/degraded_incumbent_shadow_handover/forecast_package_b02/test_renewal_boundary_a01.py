"""Unit checks for DISH-RENEWAL-BOUNDARY-A01; no native library required."""

import json
import os
from pathlib import Path

import numpy as np

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.renewal_boundary_a01 import (
    HARD_EVENTS, ROW_KEYS, make_row, native_admission, reduce_rows, run_window,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    empty_step_rows, _State,
)


def _observation(**overrides):
    value = {
        "terminal": np.array([0]), "owner": np.array([0]), "renew": np.array([0]),
        "tick": np.array([0]), "service": np.array([0]), "cas_applied": np.array([0]),
        **{name: np.array([0]) for name in HARD_EVENTS},
    }
    value.update(overrides)
    return value


def _state(**overrides):
    row = np.zeros(1, dtype=np.dtype(_State))
    for name, value in overrides.items():
        row[name] = value
    return row


def _synthetic_row(**overrides):
    row = {
        "window": 1, "t": 0, "policy_renew": False, "native_admission": False,
        "held_changed": False, "raw_action": [0.0, 0.0, 0.0, 0.0],
        "post_a": [0.0, 0.0, 0.0, 0.0],
    }
    row.update(overrides)
    return row


def test_admission_predicate():
    assert native_admission(0) is True
    assert native_admission(1) is False
    assert native_admission(4) is False
    assert native_admission(np.int32(0)) is True


def test_row_schema_and_tick_zero_not_special():
    observation = _observation(renew=np.array([0]), tick=np.array([0]))
    after = _observation(renew=np.array([1]), tick=np.array([1]), service=np.array([0]))
    pre = _state(tick=0, countdown=4, k_active=8, k_epoch=0, owner=0, actuator_owner=0,
                 cas_applied=0, a=(0.1, 0.2, 0.3, 0.4), total_energy=10.0)
    post = _state(tick=1, countdown=3, k_active=8, k_epoch=0, owner=0, actuator_owner=0,
                  cas_applied=0, a=(0.1, 0.2, 0.3, 0.4), total_energy=11.5)
    step = empty_step_rows(1)
    step["raw_action"][0] = (1.0, 0.0, -1.0, 0.0)
    step["prepare"][0] = (1, 0)
    step["commit"][0] = (0, 0)
    row = make_row(window=1, t=0, observation=observation, pre=pre, step_rows=step,
                   post=post, observation_after=after)
    assert tuple(row) == ROW_KEYS or set(ROW_KEYS) <= set(row)
    for key in ROW_KEYS:
        assert key in row
    assert row["t"] == 0
    assert row["policy_renew"] is False
    assert row["native_admission"] is False
    assert row["held_changed"] is False
    assert row["energy_increment"] == 1.5
    assert row["held_minus_raw"] is None
    assert len(row["projected_raw"]) == 4


def test_reduce_rows_arithmetic():
    rows = [
        _synthetic_row(t=0, policy_renew=False, native_admission=False),
        _synthetic_row(t=1, policy_renew=False, native_admission=True, held_changed=True,
                       raw_action=[1.0, 0.0, 0.0, 0.0], post_a=[0.5, 0.0, 0.0, 0.0]),
        _synthetic_row(t=2, policy_renew=True, native_admission=False,
                       raw_action=[2.0, 0.0, 0.0, 0.0]),
        _synthetic_row(t=3, policy_renew=True, native_admission=True,
                       raw_action=[3.0, 0.0, 0.0, 0.0], post_a=[3.0, 0.0, 0.0, 0.0]),
        _synthetic_row(window=2, t=0, policy_renew=False, native_admission=False),
    ]
    result = reduce_rows(rows)
    overall = result["overall"]
    assert overall["native_true_policy_false"] == 1
    assert overall["policy_true_native_false"] == 1
    assert overall["both_true"] == 1
    assert overall["both_false"] == 2
    assert overall["held_changed_ticks"] == 1
    assert overall["live_ticks"] == 5
    first = result["per_window"]["1"]
    assert first["native_true_policy_false"] == 1
    assert first["policy_true_native_false"] == 1
    assert first["both_true"] == 1
    assert first["both_false"] == 1
    assert first["live_ticks"] == 4
    pair = first["admission_command_pairs"][0]
    assert pair["t"] == 1
    assert pair["emitted_this"] == [1.0, 0.0, 0.0, 0.0]
    assert pair["emitted_previous"] == [0.0, 0.0, 0.0, 0.0]
    assert pair["new_held"] == [0.5, 0.0, 0.0, 0.0]
    assert result["per_window"]["2"]["both_false"] == 1
    assert result["per_window"]["2"]["live_ticks"] == 1


class _StubNative:
    def __init__(self, horizon=4):
        self.width = 1
        self._states = (_State * 1)()
        self._states[0].countdown = 4
        self.observe_calls = 0
        self.step_calls = 0
        self.horizon = horizon

    def observe(self):
        self.observe_calls += 1
        return _observation(tick=np.array([int(self._states[0].tick)]),
                            renew=np.array([0]))

    def step(self, rows):
        del rows
        self.step_calls += 1
        if self._states[0].countdown == 0:
            self._states[0].countdown = 7
        else:
            self._states[0].countdown -= 1
        self._states[0].tick += 1
        return _observation(tick=np.array([int(self._states[0].tick)]),
                            renew=np.array([0]), terminal=np.array([0]))


class _StubPolicy:
    def __init__(self):
        self.calls = []

    def step_rows(self, observation, *, sampler, global_tick, deterministic):
        self.calls.append({
            "sampler": sampler, "global_tick": global_tick,
            "deterministic": deterministic, "renew": bool(observation["renew"][0]),
        })
        return empty_step_rows(1)

    def apply_native_promotion(self, **kwargs):
        del kwargs


def test_driver_step_rows_kwargs_and_single_observe():
    native = _StubNative()
    policy = _StubPolicy()
    result = run_window(native, policy, window=1, horizon=4)
    assert native.observe_calls == 1
    assert native.step_calls == 4
    assert len(policy.calls) == 4
    assert result["live_ticks"] == 4
    for tick, call in enumerate(policy.calls):
        assert call["sampler"] is None
        assert call["deterministic"] is True
        assert call["global_tick"] == tick
    assert [row["t"] for row in result["rows"]] == [0, 1, 2, 3]


def test_check_profile_output_root():
    root = os.environ.get("DISH_A01_CHECK_ROOT")
    if not root:
        return
    path = Path(root)
    summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    rows = json.loads((path / "rows.json").read_text(encoding="utf-8"))
    assert summary["object"] == "DISH-RENEWAL-BOUNDARY-A01"
    assert summary["profile"] == "check"
    assert summary["status"] == "COMPLETE"
    assert summary["live_tick_count"] == len(rows)
    assert 1 <= len(rows) <= 4
    for row in rows:
        for key in ROW_KEYS:
            assert key in row
        assert row["window"] == 1
    reduction = summary["reduction"]["overall"]
    total = (reduction["native_true_policy_false"] + reduction["policy_true_native_false"]
             + reduction["both_true"] + reduction["both_false"])
    assert total == len(rows)
