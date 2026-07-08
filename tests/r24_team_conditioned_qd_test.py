import numpy as np
import torch

from ha_ctse_process.config import Config
from ha_ctse_process.standalone_agent import Segment, SegmentManager, StandaloneProcessAgent
from ha_ctse_process.team_conditioned_qd import (
    TEAM_CONDITIONED_QD_METRIC_FIELDS,
    TeamConditionedQDConfig,
    TeamConditionedQDProbe,
    empty_team_conditioned_qd_metrics,
)


def _synthetic_split(
    n=512,
    num_skills=6,
    action_dim=7,
    effect_dim=14,
    condition_dim=5,
    seed=0,
    effect_carries_label=True,
):
    generator = torch.Generator().manual_seed(seed)
    action_means = torch.randn(num_skills, action_dim, generator=generator)
    effect_means = torch.randn(num_skills, effect_dim, generator=generator)

    def make(count, gen):
        labels = torch.randint(0, num_skills, (count,), generator=gen)
        condition = torch.randn(count, condition_dim, generator=gen)
        if effect_carries_label:
            action = action_means[labels] + 0.35 * torch.randn(count, action_dim, generator=gen)
            effect = effect_means[labels] + 0.35 * torch.randn(count, effect_dim, generator=gen)
        else:
            action = torch.randn(count, action_dim, generator=gen)
            effect = torch.randn(count, effect_dim, generator=gen)
        return action, effect, condition, labels

    train = make(n, generator)
    eval_ = make(n, torch.Generator().manual_seed(seed + 1000))
    return train, eval_


def _train(probe, batch, steps=250, lr=5e-3):
    action, effect, condition, labels = batch
    optimizer = torch.optim.Adam(probe.parameters(), lr=lr)
    for _ in range(steps):
        optimizer.zero_grad()
        terms = probe.losses(action, effect, condition, labels)
        terms["loss"].backward()
        optimizer.step()


def test_full_classifier_beats_prior_when_effect_carries_skill_label():
    torch.manual_seed(10)
    train, eval_ = _synthetic_split(effect_carries_label=True, seed=11)
    probe = TeamConditionedQDProbe(action_dim=7, effect_dim=14, condition_dim=5, num_skills=6, hidden_dim=48)

    _train(probe, train)
    terms = probe.losses(*eval_)

    assert terms["acc_full"].item() > terms["acc_prior"].item() + 0.20
    assert terms["residual_gain"].item() > 0.0
    assert terms["residual_mean"].item() > 0.0
    assert terms["positive_frac"].item() > 0.60


def test_full_classifier_does_not_strongly_beat_prior_when_effect_is_noise():
    torch.manual_seed(20)
    train, eval_ = _synthetic_split(effect_carries_label=False, seed=21)
    probe = TeamConditionedQDProbe(action_dim=7, effect_dim=14, condition_dim=5, num_skills=6, hidden_dim=48)

    _train(probe, train)
    terms = probe.losses(*eval_)

    assert terms["acc_full"].item() < terms["acc_prior"].item() + 0.12
    assert terms["residual_gain"].item() < 0.12


def test_losses_detach_effect_condition_and_labels_from_policy_graph():
    torch.manual_seed(30)
    action, effect, condition, labels = _synthetic_split(seed=31)[0]
    action = action.clone().requires_grad_(True)
    effect = effect.clone().requires_grad_(True)
    condition = condition.clone().requires_grad_(True)
    probe = TeamConditionedQDProbe(action_dim=7, effect_dim=14, condition_dim=5, num_skills=6, hidden_dim=32)

    terms = probe.losses(action, effect, condition, labels)
    terms["loss"].backward()

    assert action.grad is None
    assert effect.grad is None
    assert condition.grad is None


def test_losses_report_behavior_pre_and_label_null_controls():
    torch.manual_seed(35)
    action, effect, condition, labels = _synthetic_split(seed=36)[0]
    pre_action = torch.randn_like(action)
    pre_effect = torch.randn_like(effect)
    pre_mask = torch.ones(labels.shape[0], dtype=torch.bool)
    probe = TeamConditionedQDProbe(action_dim=7, effect_dim=14, condition_dim=5, num_skills=6, hidden_dim=32)

    terms = probe.losses(
        action,
        effect,
        condition,
        labels,
        pre_action=pre_action,
        pre_effect=pre_effect,
        pre_mask=pre_mask,
    )

    for key in (
        "loss_behavior",
        "loss_pre",
        "acc_behavior",
        "acc_pre",
        "behavior_gain_over_prior",
        "pre_gain_over_prior",
        "full_minus_behavior_acc",
        "full_minus_pre_acc",
        "shuffle_residual_mean",
        "shuffle_positive_frac",
        "shuffle_acc_gap",
        "fake_residual_mean",
        "fake_positive_frac",
        "fake_acc_gap",
        "label_entropy",
        "label_max_frac",
    ):
        assert key in terms
        assert torch.isfinite(terms[key])
    assert terms["pre_valid_frac"].item() == 1.0
    assert 0.0 <= terms["label_max_frac"].item() <= 1.0


def test_metric_field_names_are_r24_qd_prefixed_and_empty_metrics_match():
    assert TEAM_CONDITIONED_QD_METRIC_FIELDS
    assert all(name.startswith("r24_qd_") for name in TEAM_CONDITIONED_QD_METRIC_FIELDS)

    metrics = empty_team_conditioned_qd_metrics()

    assert set(metrics) == set(TEAM_CONDITIONED_QD_METRIC_FIELDS)
    assert all(value == 0.0 for value in metrics.values())


def test_default_config_is_probe_off():
    class EmptyConfig:
        pass

    cfg = TeamConditionedQDConfig.from_config(EmptyConfig())

    assert not cfg.probe_on


def test_config_defaults_probe_off():
    config = Config()
    cfg = TeamConditionedQDConfig.from_config(config)

    assert config.enable_team_conditioned_qd_probe is False
    assert config.team_conditioned_qd_hidden_dim == 128
    assert config.team_conditioned_qd_lr == 1e-3
    assert config.team_conditioned_qd_min_samples == 64
    assert cfg.probe_on is False
    assert cfg.hidden_dim == 128


def _make_probe_agent():
    config = Config()
    config.n_z = 4
    config.num_team_codes = 3
    config.hidden_size = 32
    config.opt_compact_dim = 8
    config.opt_num_prototypes = 2
    config.low_level_architecture = "feedforward"
    config.use_recurrent_low_level = False
    config.use_outcome_residual_probe = False
    config.use_topology_role_probe = False
    config.use_transition_skill_discriminator = False
    config.enable_team_conditioned_qd_probe = True
    config.team_conditioned_qd_min_samples = 1
    return StandaloneProcessAgent(
        obs_dim=3,
        action_dim=2,
        n_agents=2,
        config=config,
        device="cpu",
        action_space_type="discrete",
        num_envs=1,
        state_dim=6,
    )


def _segment_for_qd(skill, teammate_skill=2):
    segment = Segment(
        env_id=0,
        agent_id=0,
        skill=skill,
        duration_idx=1,
        start_step=10,
        high_obs=np.asarray([1.0, 2.0, 3.0], dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
        skill_age_prev=2,
        team_code=1,
        duration_target=7,
        rewards=[0.0, 0.0],
        end_obs=np.asarray([1.5, 1.0, 4.0], dtype=np.float32),
        omega_start=np.asarray([0.25, 0.75], dtype=np.float32),
        roster_active_skills_start=np.asarray([skill, teammate_skill], dtype=np.int64),
    )
    segment.obs = [
        np.asarray([1.0, 2.0, 3.0], dtype=np.float32),
        np.asarray([1.2, 1.8, 3.5], dtype=np.float32),
    ]
    segment.actions = [
        np.asarray([0.0], dtype=np.float32),
        np.asarray([1.0], dtype=np.float32),
        np.asarray([1.0], dtype=np.float32),
    ]
    return segment


def test_standalone_qd_returns_action_effect_streams_and_excludes_focal_skill_from_context():
    agent = _make_probe_agent()
    segments = [_segment_for_qd(0, teammate_skill=2), _segment_for_qd(3, teammate_skill=2)]

    action, effect, condition, labels, pre_action, pre_effect, pre_valid = agent._r24_qd_segment_tensors(segments)

    assert action.shape == (2, agent._r24_qd_action_stream_dim)
    assert effect.shape == (2, agent._r24_qd_effect_stream_dim)
    assert pre_action.shape == (2, agent._r24_qd_action_stream_dim)
    assert pre_effect.shape == (2, agent._r24_qd_effect_stream_dim)
    assert pre_valid.shape == (2,)
    assert not pre_valid.any()
    assert torch.equal(labels, torch.tensor([0, 3]))
    assert torch.allclose(condition[0], condition[1])


def test_standalone_qd_context_includes_teammate_skill_but_not_focal_skill():
    agent = _make_probe_agent()
    same_teammate = [_segment_for_qd(0, teammate_skill=2), _segment_for_qd(3, teammate_skill=2)]
    different_teammate = [_segment_for_qd(0, teammate_skill=2), _segment_for_qd(0, teammate_skill=1)]

    _action, _effect, same_condition, _labels, *_ = agent._r24_qd_segment_tensors(same_teammate)
    _action, _effect, different_condition, _labels, *_ = agent._r24_qd_segment_tensors(different_teammate)

    assert torch.allclose(same_condition[0], same_condition[1])
    assert not torch.allclose(different_condition[0], different_condition[1])


def test_standalone_qd_pre_assignment_window_is_separate_control_stream():
    agent = _make_probe_agent()
    previous = _segment_for_qd(1, teammate_skill=2)
    current = _segment_for_qd(3, teammate_skill=2)
    previous.actions = [
        np.asarray([0.0], dtype=np.float32),
        np.asarray([0.0], dtype=np.float32),
        np.asarray([0.0], dtype=np.float32),
    ]
    previous.end_obs = np.asarray([3.0, 2.5, 1.0], dtype=np.float32)
    current.pre_assignment_high_obs = previous.high_obs.copy()
    current.pre_assignment_obs = [row.copy() for row in previous.obs]
    current.pre_assignment_actions = [row.copy() for row in previous.actions]
    current.pre_assignment_end_obs = previous.end_obs.copy()

    action, effect, _condition, _labels, pre_action, pre_effect, pre_valid = agent._r24_qd_segment_tensors([current])

    assert bool(pre_valid.item())
    assert not torch.allclose(action, pre_action)
    assert not torch.allclose(effect, pre_effect)


def test_standalone_qd_export_writes_detached_window_shard(tmp_path):
    agent = _make_probe_agent()
    agent.r24_qd_export_windows = True
    agent.r24_qd_export_dir = tmp_path
    agent.r24_qd_export_max_rows_per_update = 8
    agent.r24_qd_export_seed = 3

    metrics = agent._team_conditioned_qd_update(
        [_segment_for_qd(1), _segment_for_qd(2)],
        total_steps=320000,
        update_idx=10,
    )

    shards = sorted(tmp_path.glob("*.npz"))
    assert metrics["r24_qd_samples"] == 2.0
    assert metrics["r24_qd_export_rows"] == 2.0
    assert len(shards) == 1
    assert shards[0].name == "update_000010_steps_000000320000.npz"
    with np.load(shards[0]) as data:
        assert data["action"].shape[0] == 2
        assert data["effect"].shape[0] == 2
        assert data["condition"].shape[0] == 2
        assert data["pre_action"].shape[0] == 2
        assert data["pre_effect"].shape[0] == 2
        assert data["labels"].tolist() == [1, 2]
        assert data["labels"].dtype == np.int64
        assert data["pre_valid"].dtype == np.float32


def test_segment_manager_carries_previous_window_into_new_assignment():
    manager = SegmentManager(n_envs=1, n_agents=1)
    manager.renew(
        env_id=0,
        agent_id=0,
        skill=1,
        duration_idx=0,
        step=0,
        high_obs=np.asarray([0.0, 0.0, 0.0], dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
    )
    manager.append(
        0,
        obs=np.asarray([[0.0, 0.0, 0.0]], dtype=np.float32),
        actions=np.asarray([[1.0]], dtype=np.float32),
        rewards=np.asarray([0.0], dtype=np.float32),
        next_obs=np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32),
        rollout_idx=0,
    )
    manager.renew(
        env_id=0,
        agent_id=0,
        skill=2,
        duration_idx=0,
        step=1,
        high_obs=np.asarray([1.0, 0.0, 0.0], dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
    )

    current = manager.active[0][0]

    assert current is not None
    assert current.pre_assignment_high_obs is not None
    assert len(current.pre_assignment_actions) == 1
    assert len(current.pre_assignment_obs) == 1
    assert current.pre_assignment_end_obs is not None


def test_standalone_qd_update_returns_empty_metrics_when_disabled():
    config = Config()
    config.n_z = 4
    config.low_level_architecture = "feedforward"
    config.use_recurrent_low_level = False
    config.enable_team_conditioned_qd_probe = False
    agent = StandaloneProcessAgent(
        obs_dim=3,
        action_dim=2,
        n_agents=2,
        config=config,
        device="cpu",
        action_space_type="discrete",
        num_envs=1,
        state_dim=6,
    )

    assert agent._team_conditioned_qd_update([_segment_for_qd(1)]) == empty_team_conditioned_qd_metrics()
