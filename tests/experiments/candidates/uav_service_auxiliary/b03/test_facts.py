from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.uav_service_auxiliary.b03.facts import effective_rank, score_arrays


def _episode(index, length, value):
    prefix = f"episode_{index}_"
    observations = np.broadcast_to(np.arange(length, dtype=np.float32)[:, None, None], (length, 2, 3)).copy()
    dones = np.zeros(length, dtype=bool)
    dones[-1] = True
    return {
        prefix + "normalized_observations": observations,
        prefix + "service_predictions": np.full((length, 2), value, np.float32),
        prefix + "observation_predictions": np.zeros((length, 2, 3), np.float32),
        prefix + "qos": np.zeros(length, np.float32), prefix + "dones": dones,
        prefix + "seed": np.asarray(index),
    }


def test_episode_equal_mse_is_not_window_weighted_and_missing_is_not_zero():
    arrays = {**_episode(0, 6, 1), **_episode(1, 10, 3), **_episode(2, 2, 100)}
    result = score_arrays(arrays, calibration=None, window=3)
    assert result["service_mse"] == 5.0  # equal episodes: (1 + 9) / 2
    assert result["episodes_without_valid_windows"] == 1
    assert result["service_mse_episodes"] == 2
    assert result["episodes"][2]["service_mse"] is None
    assert result["valid_agent_rows"] == (4 + 8) * 2
    assert result["observation_mse"] is None


def test_next_observation_reference_uses_same_valid_rows_and_scale():
    arrays = _episode(0, 6, 1)
    scale = {"mu": [2.0] * 3, "scale": [2.0] * 3, "service_target_mean": 0.5}
    result = score_arrays(arrays, calibration=scale, window=3)
    # Valid starts 0..3, next values 1..4 -> transformed [-.5, 0, .5, 1].
    assert result["observation_mse"] == pytest.approx(0.375)
    assert result["training_mean_mse"] == pytest.approx(0.375)
    assert result["persistence_mse"] == pytest.approx(0.25)
    assert result["service_training_mean_mse"] == pytest.approx(0.25)
    assert result["new_optimizer_updates"] == 0


def test_effective_rank_keeps_total_variance_and_zero_degeneracy():
    degenerate = effective_rank(np.ones((10, 4)))
    assert degenerate["degenerate"] is True
    assert degenerate["total_variance"] == degenerate["effective_rank"] == 0.0
    values = np.asarray([[1, 0], [-1, 0], [0, 1], [0, -1]], dtype=float)
    result = effective_rank(values)
    assert result["total_variance"] == pytest.approx(1.0)
    assert result["effective_rank"] == pytest.approx(2.0)
    assert effective_rank(np.zeros((0, 2)))["effective_rank"] is None
