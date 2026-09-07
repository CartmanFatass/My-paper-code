"""Zero-trajectory helper checks; never construct a model or call rollout."""
import numpy as np

from experiments.candidates.vsp_03.vsp03_b02.b02 import (
    return_to_go, rule_actions, difference, write_json,
)


def test_remaining_team_reward_removes_actual_prefix():
    units = np.array([[186, 176], [-40, 164]])
    result = return_to_go(units, np.array([0, 0, 1]), np.array([0, 178, -52]))
    np.testing.assert_allclose(result, [362 / 400, 184 / 400, 176 / 400])


def test_readiness_yield_strict_age_future_clock_and_pending():
    x = np.zeros((5, 14), dtype=np.float32)
    x[:, [5, 10, 11]] = 1
    x[:, 2], x[:, 7], x[:, 13] = 0.1, 0.2, 0.5
    x[1, 7] = 0.1
    x[2, 13] = 1
    x[3, 11] = 0
    x[4, 5] = 0
    assert rule_actions(x, "R").tolist() == [False, True, True, True, False]
    assert rule_actions(x, "R0").tolist() == [True, True, True, True, False]


def test_primary_publication_from_literal_rows(tmp_path):
    left = [{"return": 0.25}, {"return": 0.5}]
    right = [{"return": 0.0}, {"return": 0.5}]
    primary = difference(left, right)
    assert primary["mean"] == 0.125
    assert np.isclose(primary["conditional_world_se"], 0.125)
    summary = {"primary": primary, "counts": {"optimizer_steps": 256}}
    assert write_json(tmp_path / "summary.json", summary) == summary
