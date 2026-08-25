import inspect
from types import SimpleNamespace

import numpy as np
import pytest
import torch
import torch.nn.functional as F

from hmasd.baselines import ALGORITHM_CHOICES, apply_algorithm_config
from hmasd.agent import HMASDAgent
from hmasd.ha_ctse import (
    CompactIndividualDiscriminator,
    CompactTeamBridge,
    CompactTeamDiscriminator,
    HorizonSkillEditor,
    OPTCompactExtractor,
)
from hmasd.networks import IndividualDiscriminator, R_Actor, SkillDiscoverer, TeamDiscriminator
from hmasd.utils import RolloutBuffer, SkillProcessSegmentBuffer
from config_1 import Config
from hmasd.process_exploration import (
    PROCESS_OUTCOME_FIELDS,
    SkillOutcomePredictor,
    SkillProcessContrastiveHead,
    SkillProcessEncoder,
    SkillProcessOutcomeExtractor,
    duration_only_baseline_accuracy,
    process_positive_skill_labels,
)


def make_config(**overrides):
    cfg = SimpleNamespace(
        state_dim=5,
        obs_dim=4,
        n_agents=2,
        n_Z=3,
        n_z=3,
        action_dim=3,
        k=10,
        action_bound=1.0,
        action_space_type="discrete",
        hidden_size=16,
        embedding_dim=16,
        n_heads=2,
        n_encoder_layers=1,
        n_decoder_layers=1,
        gru_hidden_size=16,
        use_opt_compact=True,
        opt_compact_dim=8,
        opt_num_prototypes=2,
        opt_layers=1,
        use_compact_in_low_level_actor=False,
        team_code_dim=8,
        num_team_codes=3,
        team_bridge_type="deterministic",
        H_min=1,
        H_max=2,
        force_termination_after_H_max=True,
        clip_epsilon=0.2,
        max_grad_norm=0.5,
        value_loss_coef=1.0,
        lambda_h=0.0,
        term_entropy_coef=0.01,
        skill_entropy_coef=0.01,
        duration_entropy_coef=0.01,
        use_process_exploration=False,
        use_discrete_skill_lifetimes=False,
        skill_lifetime_candidates=(1, 2, 3),
        allow_early_duration_termination=False,
        process_segment_mode="skill_lifetime",
        process_max_segment_len=8,
        process_segment_buffer_size=32,
        high_level_assignment_mode="parallel",
        use_team_code_discriminator=False,
        use_individual_skill_discriminator=True,
        discriminator_condition_on_compact=False,
        discriminator_condition_on_team_code=True,
        use_segment_discriminator=False,
        use_orthogonal=True,
        gain=0.01,
        use_valuenorm=False,
        continuous_action_distribution="gaussian",
        continuous_logstd_init=0.0,
        continuous_logstd_min=-20.0,
        continuous_logstd_max=2.0,
    )
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def sample_inputs(batch=3):
    state = torch.randn(batch, 5)
    obs = torch.randn(batch, 2, 4)
    return state, obs


def set_term_bias(editor, keep_logit, edit_logit):
    with torch.no_grad():
        editor.term_head.weight.zero_()
        editor.term_head.bias[:] = torch.tensor([keep_logit, edit_logit])


def set_skill_bias(editor, skill):
    with torch.no_grad():
        editor.skill_head.weight.zero_()
        editor.skill_head.bias.fill_(-10.0)
        editor.skill_head.bias[skill] = 10.0


def set_duration_bias(editor, candidate_idx):
    with torch.no_grad():
        editor.duration_head.weight.zero_()
        editor.duration_head.bias.fill_(-10.0)
        editor.duration_head.bias[candidate_idx] = 10.0


def test_original_hmasd_runs():
    cfg = make_config()
    apply_algorithm_config(cfg, "hmasd_original")
    assert cfg.algorithm == "hmasd_original"
    assert not cfg.use_horizon_window


def test_opt_compact_shape():
    cfg = make_config()
    extractor = OPTCompactExtractor(cfg)
    state, obs = sample_inputs()
    compact, cd_loss, cmi_loss, weights, entropy = extractor(state, obs)
    assert compact.shape == (3, cfg.opt_compact_dim)
    assert weights.shape == (3, cfg.opt_num_prototypes)
    assert cd_loss.ndim == 0
    assert cmi_loss.ndim == 0
    assert entropy.shape == (3,)


def test_bridge_shape():
    cfg = make_config(team_bridge_type="stochastic")
    bridge = CompactTeamBridge(cfg)
    compact = torch.randn(4, cfg.opt_compact_dim)
    team_code, team_vector, log_prob, entropy, logits = bridge(compact)
    assert team_code.shape == (4,)
    assert team_vector.shape == (4, cfg.team_code_dim)
    assert log_prob.shape == (4,)
    assert entropy.shape == (4,)
    assert logits.shape == (4, cfg.num_team_codes)


def test_discrete_lifetime_duration_head_outputs():
    cfg = make_config(use_discrete_skill_lifetimes=True, skill_lifetime_candidates=(1, 3), H_min=0, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=-10.0, edit_logit=10.0)
    set_duration_bias(editor, candidate_idx=1)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state,
        obs,
        torch.tensor([[0, 1]]),
        torch.ones(1, 2, dtype=torch.long),
        torch.zeros(1, 2, dtype=torch.bool),
        deterministic=True,
    )
    assert torch.all(out["executed_edit_mask"] == 1)
    assert torch.all(out["duration_candidate"] == 1)
    assert torch.all(out["duration_target"] == 3)
    assert torch.isfinite(out["log_prob_duration"]).all()


def test_forced_keep_mask_suppresses_edit_until_duration_expires():
    cfg = make_config(H_min=0, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=-10.0, edit_logit=10.0)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state,
        obs,
        torch.tensor([[0, 1]]),
        torch.ones(1, 2, dtype=torch.long),
        torch.zeros(1, 2, dtype=torch.bool),
        deterministic=True,
        forced_keep_mask=torch.ones(1, 2, dtype=torch.bool),
    )
    assert torch.all(out["executed_edit_mask"] == 0)
    torch.testing.assert_close(out["active_skill"], torch.tensor([[0, 1]]))


def test_compact_conditioned_discriminators_backward():
    cfg = make_config()
    team_disc = CompactTeamDiscriminator(cfg)
    ind_disc = CompactIndividualDiscriminator(cfg)
    state = torch.randn(4, cfg.state_dim)
    compact = torch.randn(4, cfg.opt_compact_dim)
    team_logits = team_disc(state, compact)
    assert team_logits.shape == (4, cfg.num_team_codes)
    team_loss = F.cross_entropy(team_logits, torch.tensor([0, 1, 2, 0]))

    obs = torch.randn(4, cfg.obs_dim)
    team_code = torch.tensor([0, 1, 2, 0])
    ind_logits = ind_disc(obs, team_code, compact)
    assert ind_logits.shape == (4, cfg.n_z)
    ind_loss = F.cross_entropy(ind_logits, torch.tensor([0, 1, 2, 0]))
    loss = team_loss + ind_loss
    loss.backward()
    assert any(p.grad is not None for p in team_disc.parameters())
    assert any(p.grad is not None for p in ind_disc.parameters())


def test_initial_skill_assignment():
    cfg = make_config()
    editor = HorizonSkillEditor(cfg)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state,
        obs,
        torch.full((1, 2), -1),
        torch.zeros(1, 2, dtype=torch.long),
        torch.ones(1, 2, dtype=torch.bool),
        deterministic=True,
    )
    assert torch.all(out["executed_edit_mask"] == 1)
    assert torch.all(out["initial_assignment_mask"] == 1)
    assert torch.all(out["skill_age"] == 0)
    assert torch.all((out["active_skill"] >= 0) & (out["active_skill"] < cfg.n_z))


def test_no_edit_preserves_skill():
    cfg = make_config(H_min=0, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=10.0, edit_logit=-10.0)
    set_skill_bias(editor, skill=2)
    state, obs = sample_inputs(batch=1)
    prev = torch.tensor([[1, 2]])
    out = editor.assign_and_value_batch(
        state, obs, prev, torch.ones(1, 2, dtype=torch.long), torch.zeros(1, 2, dtype=torch.bool), deterministic=True
    )
    torch.testing.assert_close(out["active_skill"], prev)
    assert torch.all(out["executed_edit_mask"] == 0)


def test_edit_replaces_skill():
    cfg = make_config(H_min=0, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=-10.0, edit_logit=10.0)
    set_skill_bias(editor, skill=2)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state,
        obs,
        torch.tensor([[0, 1]]),
        torch.ones(1, 2, dtype=torch.long),
        torch.zeros(1, 2, dtype=torch.bool),
        deterministic=True,
    )
    assert torch.all(out["executed_edit_mask"] == 1)
    assert torch.all(out["active_skill"] == 2)


def test_age_increment_on_no_edit():
    cfg = make_config(H_min=0, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=10.0, edit_logit=-10.0)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state, obs, torch.tensor([[0, 1]]), torch.tensor([[3, 4]]), torch.zeros(1, 2, dtype=torch.bool), deterministic=True
    )
    torch.testing.assert_close(out["skill_age"], torch.tensor([[4, 5]]))


def test_age_reset_on_edit():
    cfg = make_config(H_min=0, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=-10.0, edit_logit=10.0)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state, obs, torch.tensor([[0, 1]]), torch.tensor([[3, 4]]), torch.zeros(1, 2, dtype=torch.bool), deterministic=True
    )
    assert torch.all(out["skill_age"] == 0)


def test_H_min_action_masking():
    cfg = make_config(H_min=2, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=-10.0, edit_logit=10.0)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state, obs, torch.tensor([[0, 1]]), torch.zeros(1, 2, dtype=torch.long), torch.zeros(1, 2, dtype=torch.bool), deterministic=True
    )
    assert torch.all(out["executed_edit_mask"] == 0)
    assert torch.all(out["h_min_mask"] == 1)


def test_H_max_force_or_bias_termination():
    cfg = make_config(H_min=0, H_max=2, force_termination_after_H_max=True)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=10.0, edit_logit=-10.0)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state, obs, torch.tensor([[0, 1]]), torch.tensor([[2, 2]]), torch.zeros(1, 2, dtype=torch.bool), deterministic=True
    )
    assert torch.all(out["executed_edit_mask"] == 1)
    assert torch.all(out["h_max_force_mask"] == 1)


def test_logprob_matches_executed_mask():
    cfg = make_config(H_min=2, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=-10.0, edit_logit=10.0)
    state, obs = sample_inputs(batch=1)
    out = editor.assign_and_value_batch(
        state, obs, torch.tensor([[0, 1]]), torch.zeros(1, 2, dtype=torch.long), torch.zeros(1, 2, dtype=torch.bool), deterministic=True
    )
    assert torch.isfinite(out["log_prob_term"]).all()
    assert torch.all(out["executed_edit_mask"] == 0)
    assert torch.all(out["log_prob_skill"] == 0)


def test_candidate_skill_not_used_when_no_edit():
    cfg = make_config(H_min=0, H_max=10)
    editor = HorizonSkillEditor(cfg)
    set_term_bias(editor, keep_logit=10.0, edit_logit=-10.0)
    set_skill_bias(editor, skill=2)
    state, obs = sample_inputs(batch=1)
    prev = torch.tensor([[0, 1]])
    out = editor.assign_and_value_batch(
        state, obs, prev, torch.ones(1, 2, dtype=torch.long), torch.zeros(1, 2, dtype=torch.bool), deterministic=True
    )
    assert torch.all(out["candidate_skill"] == 2)
    torch.testing.assert_close(out["active_skill"], prev)


def test_autoregressive_editor_later_agent_depends_on_previous_decision():
    cfg = make_config(high_level_assignment_mode="autoregressive", H_min=0, H_max=10)
    editor = HorizonSkillEditor(cfg)
    with torch.no_grad():
        editor.term_head.weight.zero_()
        editor.term_head.bias.zero_()
        editor.term_head.weight[1, 0] = 10.0
        editor.skill_head.weight.zero_()
        editor.skill_head.bias.zero_()
        editor.ar_context_proj.weight.zero_()
        editor.ar_context_proj.bias.zero_()
        editor.ar_context_proj.weight[0, 0] = 1.0
        editor.ar_skill_embedding.weight.zero_()
        editor.ar_skill_embedding.weight[2, 0] = 1.0
        editor.ar_edit_embedding.weight.zero_()

    state, obs = sample_inputs(batch=1)
    common = dict(
        state=state,
        observations=obs,
        team_code=torch.tensor([0]),
        candidate_skill=torch.tensor([[0, 0]]),
        skill_age_prev=torch.ones(1, 2, dtype=torch.long),
        executed_edit_mask=torch.zeros(1, 2),
        initial_assignment_mask=torch.zeros(1, 2),
    )
    out_prev0 = editor.evaluate_training_batch(
        active_skill_prev=torch.tensor([[0, 0]]),
        **common,
    )
    out_prev2 = editor.evaluate_training_batch(
        active_skill_prev=torch.tensor([[2, 0]]),
        **common,
    )
    later_edit_logit_delta = out_prev2["term_logits"][0, 1, 1] - out_prev0["term_logits"][0, 1, 1]
    assert later_edit_logit_delta.item() > 5.0


def test_discriminator_uses_active_skill():
    cfg = make_config()
    disc = IndividualDiscriminator(cfg)
    obs = torch.randn(2, cfg.obs_dim)
    team_code = torch.tensor([0, 1])
    active_skill = torch.tensor([1, 2])
    logits = disc(obs, team_code)
    loss = F.cross_entropy(logits, active_skill)
    loss.backward()
    assert loss.item() > 0


def test_low_level_actor_no_compact_by_default():
    signature = inspect.signature(R_Actor.forward)
    assert "obs" in signature.parameters
    assert "agent_skill" in signature.parameters
    assert "compact" not in signature.parameters
    assert "team_code" not in signature.parameters


def test_rollout_buffer_contains_required_fields():
    buffer = RolloutBuffer(
        num_steps=2,
        num_envs=1,
        n_agents=2,
        obs_dim=4,
        action_dim=3,
        gru_hidden_size=4,
        n_Z=3,
        n_z=3,
        state_dim=5,
        action_space_type="discrete",
        compact_dim=8,
    )
    assert buffer.add(
        0,
        state=np.zeros(5, dtype=np.float32),
        obs=np.zeros((2, 4), dtype=np.float32),
        action=np.zeros(2, dtype=np.int64),
        reward=np.zeros(2, dtype=np.float32),
        done=np.zeros(2, dtype=bool),
        value=np.zeros(2, dtype=np.float32),
        log_prob=np.zeros(2, dtype=np.float32),
        gru_hidden_state=np.zeros((2, 4), dtype=np.float32),
        critic_gru_hidden_state=np.zeros((2, 4), dtype=np.float32),
        env_idx=0,
        team_skill=1,
        agent_skills=np.array([0, 1]),
    )
    assert buffer.add_high_level_data(
        0,
        0,
        compact=np.ones(8, dtype=np.float32),
        team_code=1,
        active_skill_prev=np.array([0, 1]),
        active_skill=np.array([1, 2]),
        candidate_skill=np.array([1, 2]),
        skill_age_prev=np.array([1, 1]),
        skill_age=np.array([0, 0]),
        requested_edit_mask=np.ones(2),
        executed_edit_mask=np.ones(2),
        log_prob_term=np.zeros(2),
        log_prob_skill=np.zeros(2),
        duration_candidate=np.array([0, 1]),
        duration_target=np.array([1, 2]),
        duration_remaining=np.array([1, 2]),
        log_prob_duration=np.zeros(2),
        entropy_term=np.zeros(2),
        entropy_skill=np.zeros(2),
        entropy_duration=np.zeros(2),
        initial_assignment_mask=np.zeros(2),
        opt_aggregation_entropy=0.5,
        elapsed_steps=20,
        terminal=False,
        close_reason_code=1,
    )
    data = buffer._get_full_rollout_data()
    for key in (
        "compact",
        "team_code",
        "log_prob_team_code",
        "high_level_elapsed_steps",
        "high_level_terminal",
        "high_level_close_reason",
        "active_skill_prev",
        "active_skill",
        "candidate_skill",
        "skill_age_prev",
        "skill_age",
        "requested_edit_mask",
        "executed_edit_mask",
        "log_prob_term",
        "log_prob_skill",
        "duration_candidate",
        "duration_target",
        "duration_remaining",
        "log_prob_duration",
        "entropy_term",
        "entropy_skill",
        "entropy_duration",
        "initial_assignment_mask",
        "opt_aggregation_entropy",
    ):
        assert key in data
    assert data["high_level_elapsed_steps"][0, 0] == 20
    assert data["high_level_close_reason"][0, 0] == 1


def test_skill_process_segment_buffer_tracks_lifetime_segments():
    buffer = SkillProcessSegmentBuffer(capacity=4, max_segment_len=3)
    buffer.open_segment(0, 1, skill=2, team_code=1, compact=np.ones(3), start_step=5, duration_target=3)
    assert buffer.append_transition(
        0,
        1,
        obs=np.zeros(4),
        action=np.array([1]),
        reward=1.5,
        done=False,
        next_obs=np.ones(4),
        step=6,
    )
    segment = buffer.close_segment(0, 1, reason="skill_edit", end_step=7)
    assert segment["skill"] == 2
    assert segment["duration_target"] == 3
    assert segment["length"] == 1
    assert segment["return"] == pytest.approx(1.5)
    stats = buffer.stats()
    assert stats["process_segments_completed"] == 1
    assert stats["process_duration_target_histogram"][3] == 1


def test_process_outcome_extractor_masks_missing_fields_and_uses_fallback():
    extractor = SkillProcessOutcomeExtractor()
    segment = {
        "obs_seq": [np.array([0.0, 1.0], dtype=np.float32)],
        "next_obs_seq": [np.array([1.0, 3.0], dtype=np.float32)],
        "reward_seq": [2.5],
        "reward_info_seq": [
            {"coverage_ratio": 0.2},
            {"coverage_ratio": 0.5, "system_throughput_mbps": 10.0},
        ],
    }

    result = extractor.transform_segment(segment, update=True)
    field_to_idx = {name: idx for idx, name in enumerate(PROCESS_OUTCOME_FIELDS)}

    assert result["outcome_vector"].shape == (len(PROCESS_OUTCOME_FIELDS),)
    assert result["outcome_mask"].shape == (len(PROCESS_OUTCOME_FIELDS),)
    assert result["outcome_mask"][field_to_idx["delta_coverage_ratio"]]
    assert result["outcome_vector"][field_to_idx["delta_coverage_ratio"]] == pytest.approx(0.3)
    assert not result["outcome_mask"][field_to_idx["delta_effective_connected_users"]]
    assert result["outcome_mask"][field_to_idx["fallback_obs_delta_l2"]]
    assert result["outcome_mask"][field_to_idx["fallback_reward_return"]]


def test_process_outcome_normalization_does_not_update_in_eval_mode():
    extractor = SkillProcessOutcomeExtractor()
    segment = {
        "obs_seq": [np.array([0.0], dtype=np.float32)],
        "next_obs_seq": [np.array([2.0], dtype=np.float32)],
        "reward_seq": [1.0],
        "reward_info_seq": [{"coverage_ratio": 0.1}, {"coverage_ratio": 0.4}],
    }

    extractor.transform_segment(segment, update=True)
    count_before = extractor.normalizer.count.copy()
    extractor.transform_segment(segment, update=False)

    np.testing.assert_array_equal(extractor.normalizer.count, count_before)


def test_process_segment_buffer_attaches_outcome_on_close():
    extractor = SkillProcessOutcomeExtractor()
    buffer = SkillProcessSegmentBuffer(
        capacity=4,
        max_segment_len=3,
        outcome_extractor=extractor,
    )
    buffer.open_segment(0, 0, skill=1, team_code=2, start_step=0, duration_target=2)
    buffer.append_transition(
        0,
        0,
        obs=np.array([0.0], dtype=np.float32),
        action=np.array([1], dtype=np.int64),
        reward=1.0,
        done=False,
        next_obs=np.array([1.0], dtype=np.float32),
        step=0,
        reward_info={"coverage_ratio": 0.2},
    )
    buffer.append_transition(
        0,
        0,
        obs=np.array([1.0], dtype=np.float32),
        action=np.array([0], dtype=np.int64),
        reward=2.0,
        done=False,
        next_obs=np.array([1.5], dtype=np.float32),
        step=1,
        reward_info={"coverage_ratio": 0.7},
    )

    segment = buffer.close_segment(0, 0, reason="skill_edit", end_step=1)
    stats = buffer.stats()
    field_to_idx = {name: idx for idx, name in enumerate(PROCESS_OUTCOME_FIELDS)}

    assert "outcome_vector" in segment
    assert segment["outcome_mask"][field_to_idx["delta_coverage_ratio"]]
    assert segment["outcome_vector"][field_to_idx["delta_coverage_ratio"]] == pytest.approx(0.5)
    assert stats["process_outcome_available_rate"] > 0.0
    assert stats["process_outcome_field_availability"]["delta_coverage_ratio"] == pytest.approx(1.0)


def test_process_encoder_masks_padded_steps():
    torch.manual_seed(11)
    encoder = SkillProcessEncoder(obs_dim=2, action_dim=1, hidden_dim=8, embedding_dim=8)
    obs = torch.tensor([[[1.0, 0.0], [2.0, 1.0], [100.0, 100.0]]])
    next_obs = obs + 0.5
    actions = torch.zeros(1, 3, 1)
    rewards = torch.zeros(1, 3)
    mask = torch.tensor([[1.0, 1.0, 0.0]])

    changed_padding_obs = obs.clone()
    changed_padding_obs[:, 2] = torch.tensor([-999.0, 999.0])
    changed_padding_next = next_obs.clone()
    changed_padding_next[:, 2] = torch.tensor([999.0, -999.0])

    output_a = encoder(obs, actions, next_obs, rewards, mask)
    output_b = encoder(changed_padding_obs, actions, changed_padding_next, rewards, mask)

    torch.testing.assert_close(output_a, output_b, atol=1e-6, rtol=1e-6)


def test_process_encoder_predictor_contrastive_gradients_flow():
    torch.manual_seed(13)
    encoder = SkillProcessEncoder(obs_dim=3, action_dim=2, hidden_dim=12, embedding_dim=10)
    predictor = SkillOutcomePredictor(segment_dim=10, outcome_dim=4)
    contrastive = SkillProcessContrastiveHead(segment_dim=10, num_skills=3, embedding_dim=8)

    obs = torch.randn(5, 4, 3)
    next_obs = obs + 0.1 * torch.randn(5, 4, 3)
    actions = torch.randn(5, 4, 2)
    rewards = torch.randn(5, 4)
    mask = torch.ones(5, 4)
    outcomes = torch.randn(5, 4)
    outcome_mask = torch.ones(5, 4)
    labels = torch.tensor([0, 1, 2, 1, 0])

    segment_embedding = encoder(obs, actions, next_obs, rewards, mask)
    predicted = predictor(segment_embedding)
    outcome_loss = predictor.masked_mse_loss(predicted, outcomes, outcome_mask)
    contrastive_loss = contrastive(segment_embedding, labels)["loss"]
    loss = outcome_loss + contrastive_loss
    loss.backward()

    encoder_grad = encoder.step_encoder[0].weight.grad
    skill_grad = contrastive.skill_embedding.weight.grad
    assert encoder_grad is not None and torch.sum(torch.abs(encoder_grad)).item() > 0.0
    assert skill_grad is not None and torch.sum(torch.abs(skill_grad)).item() > 0.0


def test_process_positive_labels_use_executed_skill_not_candidate():
    segments = [
        {"skill": 1, "candidate_skill": 2},
        {"skill": 0, "candidate_skill": 1},
    ]
    np.testing.assert_array_equal(process_positive_skill_labels(segments), np.array([1, 0]))


def test_duration_only_baseline_accuracy_is_independent_diagnostic():
    durations = np.array([1, 1, 2, 2, 2])
    skills = np.array([0, 0, 1, 1, 0])
    assert duration_only_baseline_accuracy(durations, skills) == pytest.approx(0.8)


def test_agent_process_update_trains_and_writes_discoverer_reward():
    class DummyRolloutBuffer:
        def __init__(self):
            self.calls = []

        def add_process_rewards(self, env_idx, agent_idx, step_indices, rewards):
            self.calls.append((env_idx, agent_idx, np.asarray(step_indices), np.asarray(rewards)))
            return len(step_indices)

    torch.manual_seed(17)
    cfg = make_config(
        use_process_exploration=True,
        use_discrete_skill_lifetimes=True,
        process_encoder_hidden_dim=8,
        process_encoder_embedding_dim=8,
        process_contrastive_dim=8,
        process_contrastive_temperature=0.2,
        process_encoder_epochs=1,
        process_encoder_batch_size=4,
        process_outcome_coef=0.25,
        process_contrastive_coef=1.0,
        process_reward_coef=0.1,
        process_reward_clip=1.0,
        process_reward_distribution="mean_over_segment",
        process_reward_warmup_steps=0,
        use_process_reward_for_discoverer=True,
        lr_process_encoder=1e-3,
        max_grad_norm=1.0,
    )

    extractor = SkillProcessOutcomeExtractor()
    segment_buffer = SkillProcessSegmentBuffer(capacity=8, max_segment_len=4, outcome_extractor=extractor)
    segment_buffer.open_segment(0, 1, skill=2, team_code=0, start_step=0, duration_target=2)
    for step in range(2):
        segment_buffer.append_transition(
            0,
            1,
            obs=np.full(cfg.obs_dim, float(step), dtype=np.float32),
            action=np.array(step % 2, dtype=np.int64),
            reward=1.0 + step,
            done=False,
            next_obs=np.full(cfg.obs_dim, float(step) + 0.5, dtype=np.float32),
            step=step,
            reward_info={"coverage_ratio": 0.2 + 0.2 * step},
        )
    segment_buffer.close_segment(0, 1, reason="skill_edit", end_step=1)

    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = cfg
    agent.device = torch.device("cpu")
    agent.use_process_exploration = True
    agent.process_encoder = SkillProcessEncoder(cfg.obs_dim, 1, hidden_dim=8, embedding_dim=8)
    agent.process_outcome_predictor = SkillOutcomePredictor(8, len(PROCESS_OUTCOME_FIELDS))
    agent.process_contrastive_head = SkillProcessContrastiveHead(8, cfg.n_z, embedding_dim=8, temperature=0.2)
    agent.process_optimizer = torch.optim.Adam(
        list(agent.process_encoder.parameters())
        + list(agent.process_outcome_predictor.parameters())
        + list(agent.process_contrastive_head.parameters()),
        lr=1e-3,
    )
    agent.process_segment_buffer = segment_buffer
    agent.rollout_buffer = DummyRolloutBuffer()
    agent.global_step = 1

    before = agent.process_encoder.step_encoder[0].weight.detach().clone()
    metrics = agent.update_process_exploration_from_segments()
    after = agent.process_encoder.step_encoder[0].weight.detach().clone()

    assert metrics["process_segments_trained"] == 1.0
    assert metrics["process_reward_applied_steps"] == 2.0
    assert len(agent.rollout_buffer.calls) == 1
    assert not torch.allclose(before, after)


def test_process_lifetime_high_level_sample_closes_only_on_expiry():
    cfg = make_config(k=10)
    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = cfg
    agent.use_ha_ctse = True
    agent.use_discrete_skill_lifetimes = True
    agent.env_skill_duration_remaining = {0: np.array([2, 3], dtype=np.int64)}

    assert not agent._should_close_high_level_sample(
        env_id=0,
        skill_timer=cfg.k - 1,
        any_done=False,
        force_collection=False,
    )

    agent.env_skill_duration_remaining[0] = np.array([1, 3], dtype=np.int64)
    assert agent._should_close_high_level_sample(
        env_id=0,
        skill_timer=cfg.k - 1,
        any_done=False,
        force_collection=False,
    )
    assert not agent._should_close_high_level_sample(
        env_id=0,
        skill_timer=cfg.k - 2,
        any_done=False,
        force_collection=False,
    )


def test_process_lifetime_pending_opens_only_on_new_decision():
    cfg = make_config()
    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = cfg
    agent.use_ha_ctse = True
    agent.use_discrete_skill_lifetimes = True

    assert agent._is_new_high_level_decision({"new_high_level_decision": True})
    assert not agent._is_new_high_level_decision({"new_high_level_decision": False})
    assert not agent._is_new_high_level_decision({"state_value": 1.0})

    agent.use_ha_ctse = False
    assert agent._is_new_high_level_decision({"state_value": 1.0})


def test_high_level_ppo_backward():
    cfg = make_config(H_min=0, H_max=10, team_bridge_type="stochastic")
    editor = HorizonSkillEditor(cfg)
    state, obs = sample_inputs(batch=2)
    out = editor.assign_and_value_batch(
        state,
        obs,
        torch.zeros(2, 2, dtype=torch.long),
        torch.ones(2, 2, dtype=torch.long),
        torch.zeros(2, 2, dtype=torch.bool),
    )
    loss = -(out["log_prob_term"].mean() + out["log_prob_skill"].mean() + out["log_prob_team_code"].mean())
    loss = loss + out["state_values"].mean()
    loss.backward()
    grads = [p.grad for p in editor.parameters() if p.grad is not None]
    assert grads
    assert any(torch.isfinite(g).all() and g.abs().sum() > 0 for g in grads)


def test_low_level_ppo_backward():
    cfg = make_config()
    discoverer = SkillDiscoverer(cfg)
    obs = torch.randn(2, cfg.obs_dim)
    skills = torch.tensor([0, 1])
    hidden = torch.zeros(2, cfg.gru_hidden_size)
    actions, _, _, _ = discoverer(obs, skills, hidden)
    log_probs, entropy = discoverer.actor.evaluate_actions(obs, hidden, actions, torch.ones(2, 1), skills)
    loss = -(log_probs.mean() + entropy)
    loss.backward()
    assert any(p.grad is not None for p in discoverer.actor.parameters())


def test_low_level_compact_context_branch_backward():
    cfg = make_config(use_compact_in_low_level_actor=True)
    discoverer = SkillDiscoverer(cfg)
    obs = torch.randn(2, cfg.obs_dim)
    state = torch.randn(2, cfg.state_dim)
    compact_context = torch.randn(2, cfg.opt_compact_dim)
    skills = torch.tensor([0, 1])
    team_skills = torch.tensor([0, 1])
    hidden = torch.zeros(2, cfg.gru_hidden_size)
    actions, log_probs, _, _ = discoverer(obs, skills, hidden, compact_context=compact_context)
    values, _ = discoverer.get_value(state, team_skills, hidden, compact_context=compact_context)
    loss = -log_probs.mean() + values.mean()
    loss.backward()
    assert discoverer.actor_context_adapter is not None
    assert discoverer.critic_context_adapter is not None
    assert any(p.grad is not None for p in discoverer.actor_context_adapter.parameters())
    assert any(p.grad is not None for p in discoverer.critic_context_adapter.parameters())


def test_discriminator_backward():
    cfg = make_config()
    team_disc = TeamDiscriminator(cfg)
    logits = team_disc(torch.randn(4, cfg.state_dim))
    loss = F.cross_entropy(logits, torch.tensor([0, 1, 2, 0]))
    loss.backward()
    assert any(p.grad is not None for p in team_disc.parameters())


def test_one_rollout_one_update():
    buffer = RolloutBuffer(2, 1, 2, 4, 3, 4, 3, 3, 5, action_space_type="discrete", compact_dim=8)
    assert buffer.add(
        0,
        np.zeros(5, dtype=np.float32),
        np.zeros((2, 4), dtype=np.float32),
        np.zeros(2, dtype=np.int64),
        np.ones(2, dtype=np.float32),
        np.zeros(2, dtype=bool),
        np.zeros(2, dtype=np.float32),
        np.zeros(2, dtype=np.float32),
        np.zeros((2, 4), dtype=np.float32),
        np.zeros((2, 4), dtype=np.float32),
        0,
        team_skill=0,
        agent_skills=np.array([0, 1]),
    )
    assert buffer.add_high_level_data(0, 0, state_value=0.0, agent_values=[0.0, 0.0], accumulated_reward=1.0)
    buffer.compute_high_level_advantages({"state": np.zeros(1), "agents": np.zeros((1, 2))}, gamma=1.0, gae_lambda=1.0)
    assert buffer.high_level_returns[0, 0] == pytest.approx(1.0)


def test_discoverer_sampler_provides_joint_observations():
    buffer = RolloutBuffer(2, 1, 2, 4, 3, 4, 3, 3, 5, action_space_type="discrete", compact_dim=8)
    for t in range(2):
        assert buffer.add(
            t,
            np.full(5, t, dtype=np.float32),
            np.full((2, 4), t + 1, dtype=np.float32),
            np.zeros(2, dtype=np.int64),
            np.ones(2, dtype=np.float32),
            np.zeros(2, dtype=bool),
            np.zeros(2, dtype=np.float32),
            np.zeros(2, dtype=np.float32),
            np.zeros((2, 4), dtype=np.float32),
            np.zeros((2, 4), dtype=np.float32),
            0,
            team_skill=0,
            agent_skills=np.array([0, 1]),
        )
    sampler = buffer.get_discoverer_sampler(ppo_epochs=1, num_sequences_per_batch=2, chunk_length=1)
    batch = next(iter(sampler))
    assert "joint_observations" in batch
    assert batch["joint_observations"].shape[-2:] == (2, 4)


def test_ablation_configs_load():
    for algorithm in (
        "hmasd_original",
        "opt_mappo_k",
        "opt_full_sync_skill",
        "ctb_sse_no_horizon",
        "horizon_ctb_sse_core",
        "horizon_ctb_sse_no_discriminator",
        "horizon_ctb_sse_compact_low_level_ablation",
        "deterministic_bridge",
        "stochastic_bridge",
        "parallel_editor",
        "autoregressive_editor",
    ):
        assert algorithm in ALGORITHM_CHOICES
        cfg = make_config()
        cfg.calculate_and_set_buffer_sizes = lambda: None
        apply_algorithm_config(cfg, algorithm)
        assert cfg.algorithm == algorithm


def test_research_core_enables_exploration_objectives():
    cfg = make_config(
        opt_cd_coef=0.0,
        opt_cmi_coef=0.0,
        opt_aggregation_entropy_coef=0.0,
        lambda_l=0.005,
    )
    cfg.calculate_and_set_buffer_sizes = lambda: None
    apply_algorithm_config(cfg, "horizon_ctb_sse_core")
    assert cfg.team_bridge_type == "stochastic"
    assert not cfg.use_prior_corrected_intrinsic
    assert not cfg.normalize_intrinsic_mi
    assert cfg.disable_discriminator_training
    assert cfg.disable_discriminator_rewards
    assert not cfg.use_team_code_discriminator
    assert not cfg.use_individual_skill_discriminator
    assert not cfg.discriminator_condition_on_compact
    assert not cfg.discriminator_condition_on_team_code
    assert cfg.legacy_mi_reward_coef == 0.0
    assert cfg.use_entropy_targets
    assert cfg.use_process_exploration
    assert cfg.use_discrete_skill_lifetimes
    assert not cfg.strict_hmasd_alignment
    assert cfg.opt_cd_coef > 0
    assert cfg.opt_cmi_coef > 0
    assert cfg.opt_aggregation_entropy_coef > 0
    assert cfg.lambda_l >= 0.02


def test_deterministic_bridge_is_explicit_ablation():
    cfg = make_config()
    cfg.calculate_and_set_buffer_sizes = lambda: None
    apply_algorithm_config(cfg, "deterministic_bridge")
    assert cfg.team_bridge_type == "deterministic"


def test_original_hmasd_preserves_strict_alignment_flag():
    cfg = make_config(strict_hmasd_alignment=True)
    cfg.calculate_and_set_buffer_sizes = lambda: None
    apply_algorithm_config(cfg, "hmasd_original")
    assert cfg.strict_hmasd_alignment


def test_process_mode_disables_legacy_high_level_force_monitor():
    agent = HMASDAgent.__new__(HMASDAgent)
    agent.use_process_exploration = True
    agent.use_discrete_skill_lifetimes = True
    assert agent._uses_process_high_level_flow()
    assert not agent._should_use_legacy_high_level_contribution_monitor()

    agent.use_discrete_skill_lifetimes = False
    assert not agent._uses_process_high_level_flow()
    assert agent._should_use_legacy_high_level_contribution_monitor()


def test_process_mode_clear_buffers_invalidates_old_policy_state():
    class DummyResetBuffer:
        def __init__(self):
            self.reset_called = False

        def reset(self):
            self.reset_called = True

    class DummyDiscriminatorBuffer:
        def __init__(self):
            self.clear_called = False

        def clear(self):
            self.clear_called = True

    cfg = SimpleNamespace(num_envs=2, n_agents=2, use_valuenorm=False)
    rollout_buffer = DummyResetBuffer()
    process_buffer = DummyResetBuffer()
    discriminator_buffer = DummyDiscriminatorBuffer()

    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = cfg
    agent.rollout_buffer = rollout_buffer
    agent.discriminator_buffer = discriminator_buffer
    agent.process_segment_buffer = process_buffer
    agent.use_process_exploration = True
    agent.use_discrete_skill_lifetimes = True
    agent.env_team_skills = {0: 1, 1: 2}
    agent.env_agent_skills = {
        0: np.array([1, 2], dtype=np.int64),
        1: np.array([2, 1], dtype=np.int64),
    }
    agent.env_log_probs = {0: {"new_high_level_decision": True}}
    agent.env_hidden_states = {0: "stale"}
    agent.env_prev_hidden_states = {0: "stale"}
    agent.actor_hidden_np = np.ones((2, 2, 4), dtype=np.float32)
    agent.critic_hidden_np = np.ones((2, 2, 4), dtype=np.float32)
    agent.prev_actor_hidden_np = np.ones((2, 2, 4), dtype=np.float32)
    agent.prev_critic_hidden_np = np.ones((2, 2, 4), dtype=np.float32)
    agent._hidden_state_array_valid = np.ones((2,), dtype=np.bool_)

    agent.clear_buffers()

    assert rollout_buffer.reset_called
    assert process_buffer.reset_called
    assert discriminator_buffer.clear_called
    assert agent.env_team_skills == {0: -1, 1: -1}
    for skills in agent.env_agent_skills.values():
        np.testing.assert_array_equal(skills, np.array([-1, -1], dtype=np.int64))
    assert agent.env_log_probs == {}
    assert agent.env_hidden_states == {}
    assert agent.env_prev_hidden_states == {}
    assert not agent._hidden_state_array_valid.any()
    assert np.all(agent.actor_hidden_np == 0.0)
    assert np.all(agent.critic_hidden_np == 0.0)


def test_process_buffer_sizing_uses_duration_lifetime_estimate():
    cfg = Config()
    cfg.num_envs = 4
    cfg.n_agents = 2
    cfg.rollout_length = 100
    cfg.k = 10
    cfg.num_mini_batch = 1
    cfg.use_process_exploration = True
    cfg.use_discrete_skill_lifetimes = True
    cfg.skill_lifetime_candidates = (1, 3)

    cfg.calculate_and_set_buffer_sizes()

    assert cfg.high_level_buffer_size == 20
    assert cfg.high_level_batch_size == 20
