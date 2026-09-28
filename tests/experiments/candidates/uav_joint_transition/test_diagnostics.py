import numpy as np
import pytest

from experiments.candidates.uav_joint_transition.diagnostics import execution_reading, probability_reading
from experiments.candidates.uav_joint_transition.motion import toward


def test_probability_audit_preserves_requested_labels():
    probabilities = np.tile([.8, .1, .05, .05], (8, 1))
    modes = np.array([1, 0, 0, 0, 0, 0, 0, 0])
    record = {"probabilities": probabilities.tolist(), "eligible": [True] * 8,
              "requested_modes": modes.tolist(), "any_non_direct_probability": 1 - .8 ** 8,
              "joint_entropy": 0, "sampled_log_probability": float(np.log(probabilities[np.arange(8), modes]).sum())}
    result = probability_reading([record], True)
    assert result["eligible_argmax_non_D_members"] == 0
    assert result["sampled_log_probability_max_error"] == 0
    record["requested_modes"][0] = 0
    with pytest.raises(ValueError, match="sampled log probability"):
        probability_reading([record], True)


def test_execution_audit_restricts_aliases_and_moving_changes():
    xyz = np.zeros((30, 8, 3))
    targets = np.tile([100., 0., 0.], (8, 1))
    actions = np.zeros((30, 8, 4))
    actions[:, :, :3] = toward(xyz, targets[None]) / [30, 30, 5]
    actions[:15, :2, 1] = .5
    submitted = actions.copy()
    submitted[0, 0, 1] = 0  # One changed proposal is overridden before native execution.
    physical = np.zeros((31, 8, 3))
    physical[1:, :2, 0] = np.arange(1, 31)[:, None]
    raw = {"physical_xyz_m": physical, "own_xyz": xyz,
           "proposal_actions": actions, "submitted_actions": submitted}
    record = {"step": 0, "eligible": [True, True] + [False] * 6,
              "requested_modes": [2, 3] + [0] * 6, "nominal_aliases": [1, 2] + [3] * 6,
              "R_targets_xyz": targets.tolist(), "candidate_scores": []}
    result = execution_reading(raw, [record])
    assert result["eligible_nominal_D_alias_mode_members"] == 3
    assert result["eligible_alternative_mode_members"] == 6
    assert result["requested_non_D_changed_proposal_member_ticks"] == 30
    assert result["requested_non_D_changed_submitted_moving_member_ticks"] == 29
    assert result["windows_at_least_two_members_with_changed_submitted_motion"] == 1
    assert result["ticks_with_simultaneous_changed_submitted_motion"] == 14
