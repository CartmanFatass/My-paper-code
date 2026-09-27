import numpy as np
import pytest

from experiments.candidates.energy_relay_diagnostics.b01 import readout as rd


def test_nonsaturated_outward_command_can_be_stationary_at_spatial_boundary():
    proposed = np.zeros((2, 8, 4), dtype=np.float32)
    proposed[..., 0] = .2
    positions = np.tile([8000., 4000., 100.], (2, 8, 1)).astype(np.float32)
    result = {"arrays": {"mode": np.zeros((2, 8), dtype=bool)},
              "row": {"action_mode": "deterministic"},
              "observation": {"proposal_t": proposed, "submitted_t": proposed.copy(),
                              "own_xyz_t": positions, "own_xyz_t1": positions.copy(),
                              "actor_mean_raw": np.arctanh(proposed),
                              "actor_scale_raw": np.full_like(proposed, .4),
                              "actor_distribution": "tanh_gaussian", "held_age": [0, 1]}}
    reading = rd.action_reading(result)
    assert reading["proposal_saturated_xy_uav_share_normal"] == 0
    assert reading["outward_submitted_share_at_boundary_normal"] == 1
    assert reading["xy_stationary_share_outward_submitted_normal"] == 1
    assert reading["shield_changed_uav_share"] == 0


def test_paired_reading_keeps_the_adverse_world_and_refuses_missing_pair():
    baseline = [{"seed": 1, "qos_per_step": .4}, {"seed": 2, "qos_per_step": .4}]
    candidate = [{"seed": 1, "qos_per_step": .3}, {"seed": 2, "qos_per_step": .7}]
    result = rd.paired(candidate, baseline)["metrics"]["qos_per_step"]
    assert result["mean"] == pytest.approx(.1)
    assert result["positive"] == result["negative"] == 1
    assert result["per_world"][0]["delta"] == pytest.approx(-.1)
    with pytest.raises(ValueError, match="identical world"):
        rd.paired(candidate[:1], baseline)


def test_common_window_and_first_divergence_follow_native_step(tmp_path):
    metrics = np.zeros((4, len(rd.ev.TRACE_FIELDS)))
    a = metrics.copy()
    a[:, rd.ev.QOS] = [.2, .9, .9, .9]
    b = metrics.copy()
    b[:, rd.ev.QOS] = [.1, .1, .1, .1]
    identity_a, identity_b = np.zeros((4, 32), dtype=np.uint8), np.zeros((4, 32), dtype=np.uint8)
    identity_a[0, 0] = 1
    np.savez(tmp_path / "a.npz", metrics=a, obs_input_digest_t=identity_a)
    np.savez(tmp_path / "b.npz", metrics=b, obs_input_digest_t=identity_b)
    left = [{"seed": 1, "actual_length": 4, "first_entry_step": 1, "raw_path": "a.npz"}]
    right = [{"seed": 1, "actual_length": 4, "first_entry_step": 3, "raw_path": "b.npz"}]
    result = rd._raw_comparison(left, right, tmp_path)
    assert result["worlds"][0]["common_pre_entry_steps"] == 1
    assert result["mean_world_qos_delta_common_pre_entry"] == pytest.approx(.1)
    assert result["worlds"][0]["first_divergence"]["first_field_in_dataflow_order"] == "obs_input_digest_t"
