from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
import torch

from config_1 import Config
from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv
from ha_ctse_process import uav_temp_loss_g1 as uav_source
from ha_ctse_process.uav_temp_loss_g1 import (
    ACTION_DIM,
    FIXED_MASK_REC,
    FullLedgerConstructiveController,
    HORIZON,
    PHYSICAL_UAVS,
    PREFIX_NORMALIZED_OPEN_ROSTER,
    ContinuousStepOutput,
    LossCell,
    LossInterval,
    MatchedContinuousRecurrentPolicy,
    NoReallocationController,
    PersistentUAVVectorEnv,
    UAVCurrentView,
    UAVLossLedger,
    UAVReplay,
    UAVTrajectory,
    cell_access,
    compute_episode_metrics,
    constructive_target_layout,
    constructive_target_slots,
    evaluate_uav_controller,
    evaluate_uav_policy,
    load_uav_checkpoint,
    make_uav_environment,
    make_uav_loss_ledger,
    optimize_uav_update,
    ppo_loss,
    replay_errors,
    replay_uav_trajectory,
    save_uav_checkpoint,
)


torch.set_num_threads(1)


def _ledger(owner: int = 2, onset: int = 120, duration: int = 30) -> UAVLossLedger:
    return UAVLossLedger(
        LossCell.IID_SINGLE,
        7,
        (LossInterval(owner=owner, onset=onset, duration=duration),),
    )


def _policy_inputs(batch: int = 2):
    generator = torch.Generator().manual_seed(17)
    observations = torch.randn(batch, PHYSICAL_UAVS, 5, generator=generator)
    state = torch.randn(batch, 7, generator=generator)
    hidden = torch.randn(batch, PHYSICAL_UAVS, 8, generator=generator)
    noise = torch.randn(batch, PHYSICAL_UAVS, ACTION_DIM, generator=generator)
    return observations, state, hidden, noise


def test_registered_ledgers_are_exact_deterministic_and_immutable():
    supports = {
        LossCell.IID_SINGLE: (120, 240, 30, 60),
        LossCell.LATE_LONG_SINGLE: (280, 330, 70, 100),
    }
    for cell, (onset_low, onset_high, duration_low, duration_high) in supports.items():
        rows = [make_uav_loss_ledger(cell, episode, ledger_seed=181400) for episode in range(512)]
        assert min(row.intervals[0].onset for row in rows) == onset_low
        assert max(row.intervals[0].onset for row in rows) == onset_high
        assert min(row.intervals[0].duration for row in rows) == duration_low
        assert max(row.intervals[0].duration for row in rows) == duration_high
        assert rows[11] == make_uav_loss_ledger(cell, 11, ledger_seed=181400)

    doubles = [
        make_uav_loss_ledger(LossCell.OVERLAPPING_DOUBLE, episode, ledger_seed=181400)
        for episode in range(512)
    ]
    assert min(row.intervals[0].onset for row in doubles) == 140
    assert max(row.intervals[0].onset for row in doubles) == 200
    assert min(row.intervals[1].onset - row.intervals[0].onset for row in doubles) == 10
    assert max(row.intervals[1].onset - row.intervals[0].onset for row in doubles) == 20
    assert min(entry.duration for row in doubles for entry in row.intervals) == 50
    assert max(entry.duration for row in doubles for entry in row.intervals) == 80
    assert all(row.intervals[0].owner != row.intervals[1].owner for row in doubles)
    with pytest.raises(Exception):
        doubles[0].intervals = ()


def test_environment_applies_leave_before_action_and_exposes_current_only():
    future_a = _ledger(owner=2, onset=120, duration=30)
    future_b = UAVLossLedger(
        LossCell.LATE_LONG_SINGLE,
        7,
        (LossInterval(owner=6, onset=300, duration=80),),
    )
    env_a = make_uav_environment(future_a, 181600)
    env_b = make_uav_environment(future_b, 181600)
    try:
        env_a.reset()
        env_b.reset()
        view_a = env_a.current_view()
        view_b = env_b.current_view()
        assert [field.name for field in fields(UAVCurrentView)] == [
            "observations",
            "active_mask",
            "critic_state",
            "physical_positions",
            "physical_step",
        ]
        np.testing.assert_array_equal(view_a.observations, view_b.observations)
        np.testing.assert_array_equal(view_a.critic_state, view_b.critic_state)

        env_a.current_step = 120
        leaving_view = env_a.current_view()
        assert not leaving_view.active_mask[2]
        assert np.count_nonzero(leaving_view.observations[2]) == 0
        before = leaving_view.physical_positions.copy()
        actions = np.full((PHYSICAL_UAVS, ACTION_DIM), 0.75, dtype=np.float32)
        transition = env_a.step(actions)
        assert not transition.executed_action_mask[2]
        np.testing.assert_array_equal(transition.view.physical_positions[2], before[2])
        assert not env_a.uav_connections[2].any()
        assert not env_a.uav_connections[:, 2].any()
        assert not env_a.uav_bs_connections[2].any()

        env_a.current_step = 150
        assert env_a.current_view().active_mask[2]
    finally:
        env_a.close()
        env_b.close()


def test_step_reuses_raw_view_inputs_without_crossing_lifecycle_boundaries():
    ledger = _ledger(owner=2, onset=120, duration=30)
    fast = make_uav_environment(ledger, 181601)
    scalar = make_uav_environment(ledger, 181601)
    scalar._disable_step_view_reuse = True
    try:
        fast.reset()
        scalar.reset()
        fast._get_observation = Mock(wraps=fast._get_observation)
        scalar._get_observation = Mock(wraps=scalar._get_observation)
        actions = np.zeros((PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32)

        for physical_step in (118, 119, 149, 150):
            fast.current_step = physical_step
            scalar.current_step = physical_step
            left = fast.step(actions)
            right = scalar.step(actions)
            np.testing.assert_array_equal(left.view.observations, right.view.observations)
            np.testing.assert_array_equal(left.view.active_mask, right.view.active_mask)
            np.testing.assert_array_equal(left.view.critic_state, right.view.critic_state)
            np.testing.assert_array_equal(
                left.view.physical_positions, right.view.physical_positions
            )
            np.testing.assert_array_equal(
                left.executed_action_mask, right.executed_action_mask
            )
            assert left.view.physical_step == right.view.physical_step
            assert left.reward == right.reward
            assert left.qos_satisfaction_ratio == right.qos_satisfaction_ratio
            assert left.terminated == right.terminated
            assert left.truncated == right.truncated

        assert fast._get_observation.call_count < scalar._get_observation.call_count
    finally:
        fast.close()
        scalar.close()


def test_wrapper_preserves_protected_s7_s1_configuration():
    reference = UAVEnergyAwareRelayEnv(config=Config("S7-S1"), seed=91)
    wrapped = make_uav_environment(UAVLossLedger(LossCell.NO_DISTURBANCE, 0, ()), 91)
    try:
        protected = (
            "n_uavs",
            "n_users",
            "n_ground_bs",
            "area_size",
            "height_range",
            "max_speed",
            "time_step",
            "max_steps",
            "bandwidth",
            "use_fdma",
            "obs_dim",
            "state_dim",
            "action_dim",
            "action_space_type",
            "scenario7_reward_model",
            "scenario7_reward_variant",
            "user_qos_rate_mbps",
            "qos_target_ratio",
            "battery_enabled",
            "charging_enabled",
            "failure_enabled",
        )
        for name in protected:
            assert getattr(wrapped, name) == getattr(reference, name), name
        assert wrapped.area_size == 8000
        assert wrapped.max_steps == HORIZON
        reference.reset(seed=91)
        wrapped.reset()
        zero_dict = {
            agent: np.zeros(ACTION_DIM, dtype=np.float32)
            for agent in reference.possible_agents
        }
        _obs, reference_rewards, _terms, _truncs, reference_infos = reference.step(zero_dict)
        wrapped_transition = wrapped.step(
            np.zeros((PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32)
        )
        reference_info = reference_infos[reference.possible_agents[0]]["reward_info"]
        assert reference_info["qos_satisfaction_ratio"] == pytest.approx(
            reference.last_constrained_reward_metrics["qos_satisfaction_ratio"], abs=0.0
        )
        assert wrapped_transition.qos_satisfaction_ratio == pytest.approx(
            wrapped.last_constrained_reward_metrics["qos_satisfaction_ratio"], abs=0.0
        )
        assert wrapped_transition.reward == pytest.approx(
            wrapped.last_constrained_reward_metrics["scenario7_reward"], abs=0.0
        )
        assert np.mean(tuple(reference_rewards.values())) == pytest.approx(
            reference.last_constrained_reward_metrics["scenario7_reward"], abs=0.0
        )
        with pytest.raises(ValueError, match="cannot override"):
            make_uav_environment(
                UAVLossLedger(LossCell.NO_DISTURBANCE, 0, ()),
                91,
                {"area_size": 1},
            )
    finally:
        reference.close()
        wrapped.close()


@pytest.mark.parametrize("seed", [181600, 181601, 181602])
def test_constructive_static_layout_certifies_representative_s7_s1_qos(seed: int):
    env = make_uav_environment(UAVLossLedger(LossCell.NO_DISTURBANCE, seed, ()), seed)
    try:
        env.reset()
        masks = [np.ones(PHYSICAL_UAVS, dtype=np.bool_)]
        if seed == 181600:
            single = masks[0].copy()
            single[2] = False
            double = single.copy()
            double[5] = False
            masks.extend((single, double))
        for mask in masks:
            env.reset()
            targets = constructive_target_layout(
                physical_positions=env.uav_positions,
                user_positions=env.user_positions,
                ground_bs_positions=env.ground_bs_positions,
                active_mask=mask,
                height_range=env.height_range,
            )
            env._service_active_mask = mask.copy()
            env.uav_positions = targets.copy()
            env._update_channel_state()
            env._update_uav_connections()
            env._compute_routing_paths()
            rates, _access, _backhaul = env._calculate_end_to_end_user_rates()
            qos = float(np.mean(np.clip(rates / (env.user_qos_rate_mbps * 1e6), 0.0, 1.0)))
            assert qos >= env.qos_target_ratio
    finally:
        env.close()


def test_matched_arms_have_exact_parameters_and_current_information():
    torch.manual_seed(23)
    fixed = MatchedContinuousRecurrentPolicy(
        5, 7, hidden_dim=8, routing_mode=FIXED_MASK_REC
    )
    torch.manual_seed(23)
    opened = MatchedContinuousRecurrentPolicy(
        5, 7, hidden_dim=8, routing_mode=PREFIX_NORMALIZED_OPEN_ROSTER
    )
    assert fixed.parameter_count == opened.parameter_count
    assert fixed.state_dict().keys() == opened.state_dict().keys()
    for name in fixed.state_dict():
        torch.testing.assert_close(fixed.state_dict()[name], opened.state_dict()[name], rtol=0, atol=0)

    observations, state, hidden, _noise = _policy_inputs()
    active = torch.ones(2, PHYSICAL_UAVS, dtype=torch.bool)
    active[0, 3] = False
    fixed_out = fixed.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=state,
        hidden=hidden,
        deterministic=True,
    )
    open_out = opened.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=state,
        hidden=hidden,
        deterministic=True,
    )
    torch.testing.assert_close(fixed_out.actions, open_out.actions, rtol=0, atol=0)
    torch.testing.assert_close(fixed_out.value, open_out.value, rtol=0, atol=0)


def test_actor_rows_are_permutation_equivariant_and_hide_inactive_physics():
    ledger = _ledger(owner=3, onset=120, duration=30)
    env = make_uav_environment(ledger, 5)
    try:
        env.reset()
        raw = np.asarray(env._get_observation("uav_2")["obs"], dtype=np.float32)
        sanitized = env._actor_observation(2)
        user_fields = 6  # frozen S7-S1 soft-handover local-user record
        peer_start = 11 + env.max_observed_users * user_fields
        peer_stop = peer_start + env.max_observed_uavs * 4
        energy_start = env.obs_dim - env.energy_obs_extra_dim
        energy_stop = energy_start + env.max_energy_observed_uavs * env.energy_uav_obs_dim
        unchanged = np.ones(env.obs_dim, dtype=np.bool_)
        unchanged[3:6] = False
        unchanged[peer_start:peer_stop] = False
        unchanged[energy_start:energy_stop] = False
        # Local user SINR/connection/service records, BS records, overload,
        # existing clock, and station information remain exact raw S7-S1.
        np.testing.assert_array_equal(sanitized[unchanged], raw[unchanged])
        owner_records = raw[energy_start:energy_stop].reshape(
            env.max_energy_observed_uavs, env.energy_uav_obs_dim
        )
        anonymous_records = sanitized[energy_start:energy_stop].reshape(
            env.max_energy_observed_uavs, env.energy_uav_obs_dim
        )
        np.testing.assert_array_equal(anonymous_records[0], owner_records[2])

        env.current_step = 120
        before = env.current_view()
        assert np.count_nonzero(before.observations[3]) == 0
        env.uav_positions[3] = [7999.0, 1.0, 199.0]
        after = env.current_view()
        np.testing.assert_array_equal(
            before.observations[before.active_mask],
            after.observations[after.active_mask],
        )
    finally:
        env.close()

    permutation = np.asarray([5, 2, 7, 0, 3, 6, 1, 4])
    model = MatchedContinuousRecurrentPolicy(
        5, 7, hidden_dim=8, routing_mode=PREFIX_NORMALIZED_OPEN_ROSTER
    )
    observations, state, hidden, _noise = _policy_inputs(batch=1)
    mask = torch.ones(1, PHYSICAL_UAVS, dtype=torch.bool)
    mask[:, 3] = False
    baseline = model.forward_step(
        observations=observations,
        active_mask=mask,
        critic_state=state,
        hidden=hidden,
        deterministic=True,
    )
    torch_permutation = torch.as_tensor(permutation)
    transformed = model.forward_step(
        observations=observations[:, torch_permutation],
        active_mask=mask[:, torch_permutation],
        critic_state=state,
        hidden=hidden[:, torch_permutation],
        deterministic=True,
    )
    inverse = torch.argsort(torch_permutation)
    torch.testing.assert_close(
        transformed.actions[:, inverse], baseline.actions, rtol=1e-6, atol=1e-6
    )
    torch.testing.assert_close(
        transformed.token_log_probs[:, inverse], baseline.token_log_probs, rtol=1e-6, atol=1e-6
    )
    torch.testing.assert_close(
        transformed.next_hidden[:, inverse], baseline.next_hidden, rtol=1e-6, atol=1e-6
    )


def test_hidden_freezes_restores_and_survivor_storage_does_not_move():
    model = MatchedContinuousRecurrentPolicy(
        5, 7, hidden_dim=8, routing_mode=PREFIX_NORMALIZED_OPEN_ROSTER
    )
    observations, state, hidden, noise = _policy_inputs()
    active = torch.ones(2, PHYSICAL_UAVS, dtype=torch.bool)
    active[:, 3] = False
    leave = model.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=state,
        hidden=hidden,
        sampling_noise=noise,
    )
    torch.testing.assert_close(leave.next_hidden[:, 3], hidden[:, 3], rtol=0, atol=0)
    assert torch.count_nonzero(leave.actions[:, 3]) == 0
    assert torch.count_nonzero(leave.token_log_probs[:, 3]) == 0
    # Every survivor remains in its own immutable owner row; there is no compact
    # hidden-array shift into the absent row.
    assert not torch.equal(leave.next_hidden[:, 4], hidden[:, 3])

    rejoined = torch.ones_like(active)
    restored = model.forward_step(
        observations=observations,
        active_mask=rejoined,
        critic_state=state,
        hidden=leave.next_hidden,
        deterministic=True,
    )
    assert not torch.equal(restored.next_hidden[:, 3], leave.next_hidden[:, 3])


def test_only_constructive_control_receives_future_ledger():
    env = make_uav_environment(UAVLossLedger(LossCell.NO_DISTURBANCE, 0, ()), 77)
    try:
        env.reset()
        view = env.current_view()
        no_loss = FullLedgerConstructiveController(
            UAVLossLedger(LossCell.NO_DISTURBANCE, 0, ())
        )
        future_loss = FullLedgerConstructiveController(_ledger(owner=7, onset=153, duration=40))
        common = dict(
            physical_positions=view.physical_positions,
            user_positions=env.user_positions,
            ground_bs_positions=env.ground_bs_positions,
            active_mask=view.active_mask,
            max_speed=env.max_speed,
            max_vertical_speed=env.max_vertical_speed_mps,
            time_step=env.time_step,
            height_range=env.height_range,
        )
        no_loss_action = no_loss.act(**common)
        future_action = future_loss.act(**common)
        assert no_loss_action.shape == future_action.shape == (PHYSICAL_UAVS, ACTION_DIM)
        assert not np.array_equal(
            no_loss._protected_targets, future_loss._protected_targets
        )
        assert 0.0 < future_loss.reachability_scale <= 1.0
        affected_target = future_loss._affected_targets[7]
        ordinary_slots = constructive_target_slots(
            user_positions=env.user_positions,
            ground_bs_positions=env.ground_bs_positions,
            active_count=PHYSICAL_UAVS,
            relay_count=future_loss.relay_count,
            height_range=env.height_range,
        )
        assert any(
            np.array_equal(affected_target, service_target)
            for service_target in ordinary_slots[future_loss.relay_count :]
        )
        assert not np.array_equal(
            affected_target[:2], env.ground_bs_positions[:, :2].mean(axis=0)
        )

        lost_mask = view.active_mask.copy()
        lost_mask[7] = False
        frozen_action = future_loss.act(**{**common, "active_mask": lost_mask})
        np.testing.assert_array_equal(frozen_action[7], np.zeros(ACTION_DIM))
        np.testing.assert_array_equal(future_loss._affected_targets[7], affected_target)
        assert FullLedgerConstructiveController.uses_complete_ledger
        assert not NoReallocationController.uses_complete_ledger

        candidate = constructive_target_layout(
            physical_positions=view.physical_positions,
            user_positions=env.user_positions,
            ground_bs_positions=env.ground_bs_positions,
            active_mask=view.active_mask,
            height_range=env.height_range,
        )
        blind_a = NoReallocationController()
        blind_b = NoReallocationController()
        blind_kwargs = dict(
            candidate_targets=candidate,
            physical_positions=view.physical_positions,
            active_mask=view.active_mask,
            max_speed=env.max_speed,
            max_vertical_speed=env.max_vertical_speed_mps,
            time_step=env.time_step,
        )
        np.testing.assert_array_equal(
            blind_a.act_for_layout(**blind_kwargs), blind_b.act_for_layout(**blind_kwargs)
        )
        assert "ledger" not in {field.name for field in fields(UAVCurrentView)}
    finally:
        env.close()


def _synthetic_trajectory(model: MatchedContinuousRecurrentPolicy) -> UAVTrajectory:
    observations, state, hidden, _noise = _policy_inputs(batch=2)
    masks = torch.ones(4, 2, PHYSICAL_UAVS, dtype=torch.bool)
    masks[1:3, :, 3] = False
    generator = torch.Generator().manual_seed(71)
    observation_rows = torch.randn(4, 2, PHYSICAL_UAVS, 5, generator=generator)
    state_rows = torch.randn(4, 2, 7, generator=generator)
    noise_rows = torch.randn(4, 2, PHYSICAL_UAVS, ACTION_DIM, generator=generator)
    hidden_before = []
    outputs: list[ContinuousStepOutput] = []
    current = hidden.clone()
    with torch.no_grad():
        for time in range(4):
            hidden_before.append(current.clone())
            output = model.forward_step(
                observations=observation_rows[time],
                active_mask=masks[time],
                critic_state=state_rows[time],
                hidden=current,
                sampling_noise=noise_rows[time],
            )
            outputs.append(output)
            current = output.next_hidden
    return UAVTrajectory(
        observations=observation_rows,
        active_mask=masks,
        critic_states=state_rows,
        actions=torch.stack([row.actions for row in outputs]),
        pre_tanh_actions=torch.stack([row.pre_tanh_actions for row in outputs]),
        old_log_probs=torch.stack([row.token_log_probs for row in outputs]),
        old_values=torch.stack([row.value for row in outputs]),
        rewards=torch.zeros(4, 2),
        dones=torch.zeros(4, 2, dtype=torch.bool),
        hidden_before=torch.stack(hidden_before),
        hidden_after=torch.stack([row.next_hidden for row in outputs]),
        prefix_action_sums=torch.stack([row.prefix_action_sums for row in outputs]),
        qos=np.ones((4, 2)),
        ledger_ids=("a", "b"),
    )


def test_bounded_action_replay_and_inactive_ppo_exclusion():
    model = MatchedContinuousRecurrentPolicy(
        5, 7, hidden_dim=8, routing_mode=FIXED_MASK_REC
    )
    trajectory = _synthetic_trajectory(model)
    assert bool((trajectory.actions.abs() < 1.0).all())
    replay = replay_uav_trajectory(model, trajectory, device=torch.device("cpu"))
    errors = replay_errors(replay, trajectory)
    assert max(errors.values()) <= 1e-6

    advantages = torch.ones_like(trajectory.rewards)
    returns = trajectory.old_values.clone()
    baseline, _ = ppo_loss(replay, trajectory, advantages, returns)
    perturbed = UAVReplay(
        log_probs=torch.where(replay.active_mask, replay.log_probs, torch.full_like(replay.log_probs, 50.0)),
        entropies=torch.where(replay.active_mask, replay.entropies, torch.full_like(replay.entropies, -50.0)),
        values=replay.values,
        hidden_after=replay.hidden_after,
        prefix_action_sums=replay.prefix_action_sums,
        active_mask=replay.active_mask,
    )
    changed, _ = ppo_loss(perturbed, trajectory, advantages, returns)
    torch.testing.assert_close(baseline, changed, rtol=0, atol=0)


def test_uav_update_reuses_preflight_replay_for_first_pass(
    monkeypatch: pytest.MonkeyPatch,
):
    model = MatchedContinuousRecurrentPolicy(
        5, 7, hidden_dim=8, routing_mode=FIXED_MASK_REC
    )
    trajectory = _synthetic_trajectory(model)
    replay_calls = [0]
    original_replay = uav_source.replay_uav_trajectory

    def counted_replay(*args, **kwargs):
        replay_calls[0] += 1
        return original_replay(*args, **kwargs)

    monkeypatch.setattr(uav_source, "replay_uav_trajectory", counted_replay)
    metrics = optimize_uav_update(
        model,
        torch.optim.Adam(model.parameters(), lr=1e-3),
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=2,
    )

    assert metrics["finite_update"] == 1.0
    assert replay_calls[0] == 2


def test_extreme_tanh_latents_execute_and_replay_exact_finite_density():
    model = MatchedContinuousRecurrentPolicy(
        5, 7, hidden_dim=8, routing_mode=FIXED_MASK_REC
    )
    observations, state, hidden, _noise = _policy_inputs(batch=1)
    active = torch.ones(1, PHYSICAL_UAVS, dtype=torch.bool)
    extreme = torch.full((1, PHYSICAL_UAVS, ACTION_DIM), 100.0)
    sampled = model.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=state,
        hidden=hidden,
        sampling_noise=extreme,
    )
    assert bool(torch.isfinite(sampled.pre_tanh_actions).all())
    assert bool(torch.isfinite(sampled.token_log_probs).all())
    assert bool((sampled.actions.abs() <= 1.0).all())
    assert bool((sampled.actions == 1.0).any())
    replayed = model.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=state,
        hidden=hidden,
        teacher_pre_tanh=sampled.pre_tanh_actions,
    )
    torch.testing.assert_close(replayed.actions, sampled.actions, rtol=0, atol=0)
    torch.testing.assert_close(
        replayed.pre_tanh_actions, sampled.pre_tanh_actions, rtol=0, atol=0
    )
    torch.testing.assert_close(
        replayed.token_log_probs, sampled.token_log_probs, rtol=0, atol=0
    )


def test_metric_boundaries_and_no_reallocation_latch():
    no_loss = UAVLossLedger(LossCell.NO_DISTURBANCE, 1, ())
    perfect = compute_episode_metrics(np.ones(HORIZON), no_loss)
    assert perfect == {"J_event": 1.0, "Q_ordinary": 1.0, "J_rejoin": None}

    ledger = _ledger()
    boundary = compute_episode_metrics(np.full(HORIZON, 0.90), ledger)
    assert boundary["J_event"] == pytest.approx(1.0)
    assert boundary["J_rejoin"] == pytest.approx(1.0)
    assert boundary["Q_ordinary"] == pytest.approx(0.90)
    assert cell_access(0.80, 0.90) == pytest.approx(1.0)

    controller = NoReallocationController()
    all_active = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
    absent = all_active.copy()
    absent[2] = False
    first = np.full((PHYSICAL_UAVS, ACTION_DIM), 0.25, dtype=np.float32)
    second = np.full_like(first, 0.75)
    controller.act(first, all_active)
    during = controller.act(second, absent)
    after = controller.act(second, all_active)
    assert np.count_nonzero(during[2]) == 0
    np.testing.assert_array_equal(during[all_active & (np.arange(PHYSICAL_UAVS) != 2)], first[all_active & (np.arange(PHYSICAL_UAVS) != 2)])
    np.testing.assert_array_equal(after, first)


def test_checkpoint_restores_parameters_optimizer_and_rng(tmp_path: Path):
    model = MatchedContinuousRecurrentPolicy(
        5, 7, hidden_dim=8, routing_mode=FIXED_MASK_REC
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    sum(parameter.sum() for parameter in model.parameters()).backward()
    optimizer.step()
    seed_contract = {"model": 181200, "ledger": 181400, "action": 181800}
    action_rng_state = np.random.default_rng(33).bit_generator.state
    path = tmp_path / "checkpoint.pt"
    save_uav_checkpoint(
        path,
        model=model,
        optimizer=optimizer,
        completed_updates=9,
        next_episode_id=144,
        seed_contract=seed_contract,
        action_rng_state=action_rng_state,
    )
    expected_state = {name: value.detach().clone() for name, value in model.state_dict().items()}
    expected_random = torch.rand(5)
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.add_(10.0)
    torch.manual_seed(999)
    payload = load_uav_checkpoint(
        path,
        model=model,
        optimizer=optimizer,
        expected_seed_contract=seed_contract,
    )
    for name, value in model.state_dict().items():
        torch.testing.assert_close(value, expected_state[name], rtol=0, atol=0)
    torch.testing.assert_close(torch.rand(5), expected_random, rtol=0, atol=0)
    assert payload["action_rng_state"] == action_rng_state
    assert payload["completed_updates"] == 9
    with pytest.raises(ValueError, match="seed contract"):
        load_uav_checkpoint(
            path,
            model=model,
            optimizer=optimizer,
            expected_seed_contract={**seed_contract, "action": 0},
        )


def test_spawn_vector_worker_reset_step_spec_and_close():
    ledger = UAVLossLedger(LossCell.NO_DISTURBANCE, 2, ())
    with PersistentUAVVectorEnv([ledger], [182200]) as vector:
        spec = vector.spec()
        assert spec["physical_width"] == PHYSICAL_UAVS
        assert spec["action_dim"] == ACTION_DIM
        assert vector.current_view.observations.shape == (1, PHYSICAL_UAVS, spec["observation_dim"])
        view, rewards, qos, dones, executed = vector.step(
            np.zeros((1, PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32)
        )
        assert view.physical_step == 1
        assert rewards.shape == qos.shape == dones.shape == (1,)
        assert executed.shape == (1, PHYSICAL_UAVS)
        assert executed.all()
        vector.reset(ledgers=[ledger], environment_seeds=[182200])
        model = MatchedContinuousRecurrentPolicy(
            spec["observation_dim"],
            spec["critic_state_dim"],
            hidden_dim=8,
            routing_mode=FIXED_MASK_REC,
        )
        learned_qos = evaluate_uav_policy(
            model,
            vector,
            episode_ids=[2],
            action_seed=182400,
            device=torch.device("cpu"),
            deterministic=True,
            horizon=1,
        )
        assert learned_qos.shape == (1, 1)
        vector.reset(ledgers=[ledger], environment_seeds=[182200])
        control_qos = evaluate_uav_controller(vector, kind="constructive", horizon=1)
        assert control_qos.shape == (1, 1)
