import numpy as np
import torch

from ha_ctse_process.team_effect_targets import (
    TeamEffectTargetProbe,
    TEAM_EFFECT_TARGET_METRIC_FIELDS,
    empty_team_effect_target_metrics,
    summarize_joint_actions,
    group_env_sequences,
    build_windows,
)


def test_probe_recovers_Z_from_informative_target_only():
    torch.manual_seed(0)
    C, n = 8, 512
    labels = torch.randint(0, C, (n,))
    code_means = torch.randn(C, 12)
    informative = code_means[labels] + 0.3 * torch.randn(n, 12)  # carries Z
    noise = torch.randn(n, 12)                                    # carries nothing
    prior = torch.full((C,), 1.0 / C)
    eval_labels = torch.randint(0, C, (n,))
    eval_inf = code_means[eval_labels] + 0.3 * torch.randn(n, 12)
    eval_noise = torch.randn(n, 12)
    probe = TeamEffectTargetProbe(target_dims={"good": 12, "bad": 12}, num_team_codes=C)
    for _ in range(250):
        probe.update({"good": informative, "bad": noise}, labels, prior)
    m = probe.evaluate({"good": eval_inf, "bad": eval_noise}, eval_labels, prior)
    assert m["q_d_acc_good"] > m["q_d_acc_bad"] + 0.15
    assert m["q_d_residual_gain_good"] > 0.0
    assert m["q_d_best_target_good"] == 1.0  # 'good' flagged as best


def test_summarize_joint_actions_shape_and_normalization():
    acts = torch.randint(0, 5, (16, 6))  # 16 boundaries, 6 agents, discrete in [0,5)
    summ = summarize_joint_actions(acts, num_actions=5)
    assert summ.shape == (16, 5)
    assert torch.allclose(summ.sum(-1), torch.ones(16), atol=1e-5)


def test_group_env_sequences_preserves_time_order():
    env_ids = [0, 1, 0, 1, 0]
    seqs = group_env_sequences(env_ids)
    assert seqs[0] == [0, 2, 4]
    assert seqs[1] == [1, 3]


def test_build_windows_delta_and_horizon():
    # states as scalars in a single env; effect window = state[i+H]-state[i]
    states = np.arange(10, dtype=np.float32).reshape(10, 1)
    seqs = {0: list(range(10))}
    idxs, deltas = build_windows(seqs, states, horizon=3)
    # boundary i can form a window iff i+H < len -> i in 0..6
    assert idxs == [0, 1, 2, 3, 4, 5, 6]
    assert np.allclose(deltas, 3.0)  # each delta = 3


def test_metric_fields_and_empty():
    assert any("q_d_acc" in f for f in TEAM_EFFECT_TARGET_METRIC_FIELDS)
    # windowed targets are horizon-keyed; s_next is single-step (unkeyed).
    m = empty_team_effect_target_metrics(("joint_action", "s_next"), (10, 20))
    assert "q_d_acc_joint_action_h10" in m
    assert "q_d_acc_joint_action_h20" in m
    assert "q_d_acc_s_next" in m
    assert "q_d_acc_s_next_h10" not in m
