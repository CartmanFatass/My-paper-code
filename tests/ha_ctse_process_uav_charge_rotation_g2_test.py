from dataclasses import replace

import numpy as np
import pytest
import torch

import ha_ctse_process.uav_charge_rotation_g2 as g2_source
from ha_ctse_process.uav_charge_rotation_g2 import (
    ACTION_DIM,
    CONSTRUCTIVE_CHARGE_ROTATION,
    ENERGY_PROFILE_VALUES,
    FIXED_MASK_REC,
    HORIZON,
    NO_PROACTIVE_ROTATION,
    PHYSICAL_UAVS,
    PREFIX_NORMALIZED_OPEN_ROSTER,
    REJOIN_BATTERY_RATIO,
    REJOIN_WINDOW,
    ConstructiveChargeRotationController,
    EnergyProfile,
    G2EpisodeMetrics,
    G2Replay,
    G2Trajectory,
    LifecycleEvent,
    LifecycleEventKind,
    LifecycleState,
    MatchedChargeRotationPolicy,
    NoProactiveRotationController,
    PersistentG2VectorEnv,
    UAVChargeRotationEnv,
    cell_access,
    action_path_digest,
    compute_episode_metrics,
    compute_gae,
    collect_g2_trajectory,
    make_action_noise,
    make_g2_episode_ledger,
    g2_checkpoint_state,
    load_g2_checkpoint_state,
    model_state_copy,
    maximum_state_difference,
    ppo_loss,
    replay_errors,
    replay_g2_trajectory,
    source_support_facts,
)


def _env(profile=EnergyProfile.IID, episode_id=3, seed=91):
    ledger = make_g2_episode_ledger(profile, episode_id, energy_seed=177_100)
    env = UAVChargeRotationEnv(ledger, environment_seed=seed)
    env.reset()
    return env


def test_energy_profiles_are_exact_permutations_and_rng_separated():
    for profile, values in ENERGY_PROFILE_VALUES.items():
        first = make_g2_episode_ledger(profile, 7, energy_seed=12_300)
        again = make_g2_episode_ledger(profile, 7, energy_seed=12_300)
        other_episode = make_g2_episode_ledger(profile, 8, energy_seed=12_300)
        np.testing.assert_array_equal(first.initial_energy_ratios, again.initial_energy_ratios)
        np.testing.assert_array_equal(np.sort(first.initial_energy_ratios), np.sort(values))
        np.testing.assert_array_equal(
            first.initial_energy_ratios, np.asarray(values)[first.energy_permutation]
        )
        assert sorted(first.energy_permutation.tolist()) == list(range(PHYSICAL_UAVS))
        assert first.ledger_id != other_episode.ledger_id

    low = make_g2_episode_ledger(EnergyProfile.LOW_ENERGY, 4, energy_seed=1)
    sync = make_g2_episode_ledger(EnergyProfile.SYNCHRONIZED_PRESSURE, 4, energy_seed=2)
    env_a = UAVChargeRotationEnv(low, environment_seed=444)
    env_b = UAVChargeRotationEnv(sync, environment_seed=444)
    try:
        env_a.reset()
        env_b.reset()
        np.testing.assert_array_equal(env_a.uav_positions, env_b.uav_positions)
        np.testing.assert_array_equal(env_a.user_positions, env_b.user_positions)
        np.testing.assert_array_equal(
            env_a.charging_station_positions, env_b.charging_station_positions
        )
        np.testing.assert_array_equal(env_a.uav_battery_ratios, low.initial_energy_ratios)
        np.testing.assert_array_equal(env_b.uav_battery_ratios, sync.initial_energy_ratios)
    finally:
        env_a.close()
        env_b.close()


def test_pre_action_leave_queue_charge_rejoin_and_terminal_boundaries():
    env = _env()
    try:
        station = env.charging_station_positions[0].copy()
        env.uav_positions[0] = station
        env.uav_positions[1] = station
        env.uav_battery_ratios[:2] = 0.50
        env.uav_dock_requests[:2] = True
        env.uav_target_stations[:2] = 0
        events = env._synchronize_lifecycle(force=True)
        assert env.lifecycle_states[:2].tolist() == [
            LifecycleState.CHARGE_ABSENT,
            LifecycleState.CHARGE_ABSENT,
        ]
        assert [(e.owner, e.kind) for e in events] == [
            (0, LifecycleEventKind.LEAVE),
            (1, LifecycleEventKind.LEAVE),
        ]

        env.uav_charging[:] = False
        env.last_charging_eligible[:2] = True
        env.station_occupancy[0] = 1
        env.station_queue_lengths[0] = 1
        env.uav_charging[0] = True
        env._last_lifecycle_boundary = -1
        events = env._synchronize_lifecycle(force=True)
        assert {(e.owner, e.kind) for e in events} == {
            (0, LifecycleEventKind.CHARGE),
            (1, LifecycleEventKind.QUEUE),
        }

        env.uav_battery_ratios[0] = REJOIN_BATTERY_RATIO
        env._last_lifecycle_boundary = -1
        events = env._synchronize_lifecycle(force=True)
        assert env.lifecycle_states[0] is LifecycleState.ACTIVE
        assert events[0].kind is LifecycleEventKind.REJOIN

        env.uav_positions[2] = station + np.array([200.0, 0.0, 0.0])
        env.uav_battery_ratios[2] = 0.0
        env._last_lifecycle_boundary = -1
        events = env._synchronize_lifecycle(force=True)
        assert env.lifecycle_states[2] is LifecycleState.TERMINAL
        assert any(e.owner == 2 and e.kind is LifecycleEventKind.TERMINAL for e in events)
    finally:
        env.close()


def test_inactive_rows_get_no_policy_action_but_continue_deterministic_docking():
    env = _env()
    try:
        env._lifecycle_state[3] = int(LifecycleState.CHARGE_ABSENT)
        env._assigned_station[3] = 0
        env.uav_positions[3] = env.charging_station_positions[0] + np.array([80.0, 0.0, 0.0])
        policy_actions = np.full((PHYSICAL_UAVS, ACTION_DIM), -0.25, dtype=np.float32)
        action_dict, physical_mask = env._physical_action_dict(policy_actions)
        assert not env.service_active_mask[3]
        assert physical_mask[3]
        assert action_dict["uav_3"][3] == 1.0
        assert action_dict["uav_3"][0] < 0.0

        env._lifecycle_state[4] = int(LifecycleState.TERMINAL)
        action_dict, physical_mask = env._physical_action_dict(policy_actions)
        np.testing.assert_array_equal(action_dict["uav_4"], np.array([0, 0, 0, -1], np.float32))
        assert not physical_mask[4]
    finally:
        env.close()


def test_actor_view_is_current_anonymous_and_critic_contains_service_mask():
    env = _env()
    try:
        env._lifecycle_state[3] = int(LifecycleState.CHARGE_ABSENT)
        before = env.current_view()
        assert np.count_nonzero(before.observations[3]) == 0
        assert before.critic_state.shape == (env.state_dim + PHYSICAL_UAVS,)
        np.testing.assert_array_equal(before.critic_state[-PHYSICAL_UAVS:], before.active_mask)

        active_row_before = before.observations[2].copy()
        env.uav_battery_ratios[3] -= 0.10
        env.charging_wait_steps[3] += 4
        after = env.current_view()
        assert not np.array_equal(active_row_before, after.observations[2])
        assert not hasattr(before, "future_schedule")
        assert not hasattr(before, "queue_order")
        assert not hasattr(before, "desired_rotation")
    finally:
        env.close()


def _policy_inputs(batch=2, observation_dim=9, critic_dim=13, hidden_dim=8):
    generator = torch.Generator().manual_seed(123)
    observations = torch.randn(batch, PHYSICAL_UAVS, observation_dim, generator=generator)
    critic = torch.randn(batch, critic_dim, generator=generator)
    hidden = torch.randn(batch, PHYSICAL_UAVS, hidden_dim, generator=generator)
    noise = torch.randn(batch, PHYSICAL_UAVS, ACTION_DIM, generator=generator)
    return observations, critic, hidden, noise


def test_matched_arms_have_parameter_support_parity_and_inactive_hidden_exactness():
    torch.manual_seed(88)
    fixed = MatchedChargeRotationPolicy(9, 13, hidden_dim=8, routing_mode=FIXED_MASK_REC)
    torch.manual_seed(88)
    opened = MatchedChargeRotationPolicy(
        9, 13, hidden_dim=8, routing_mode=PREFIX_NORMALIZED_OPEN_ROSTER
    )
    assert fixed.parameter_count == opened.parameter_count
    for name, tensor in fixed.state_dict().items():
        torch.testing.assert_close(tensor, opened.state_dict()[name], rtol=0, atol=0)
    observations, critic, hidden, noise = _policy_inputs()
    active = torch.ones(2, PHYSICAL_UAVS, dtype=torch.bool)
    active[:, 3] = False
    fixed_out = fixed.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=critic,
        hidden=hidden,
        sampling_noise=noise,
    )
    open_out = opened.forward_step(
        observations=observations,
        active_mask=active,
        critic_state=critic,
        hidden=hidden,
        sampling_noise=noise,
    )
    assert fixed_out.actions.shape == open_out.actions.shape == (2, PHYSICAL_UAVS, ACTION_DIM)
    assert torch.count_nonzero(fixed_out.actions[:, 3]) == 0
    assert torch.count_nonzero(fixed_out.token_log_probs[:, 3]) == 0
    torch.testing.assert_close(fixed_out.next_hidden[:, 3], hidden[:, 3], rtol=0, atol=0)
    torch.testing.assert_close(open_out.next_hidden[:, 3], hidden[:, 3], rtol=0, atol=0)
    torch.testing.assert_close(fixed_out.value, open_out.value, rtol=0, atol=0)


def test_empty_service_roster_has_zero_support_and_frozen_owned_state():
    model = MatchedChargeRotationPolicy(9, 13, hidden_dim=8, routing_mode=FIXED_MASK_REC)
    observations, critic, hidden, _noise = _policy_inputs(batch=1)
    output = model.forward_step(
        observations=observations,
        active_mask=torch.zeros(1, PHYSICAL_UAVS, dtype=torch.bool),
        critic_state=critic,
        hidden=hidden,
        deterministic=True,
    )
    assert torch.count_nonzero(output.actions) == 0
    assert torch.count_nonzero(output.token_log_probs) == 0
    torch.testing.assert_close(output.next_hidden, hidden, rtol=0, atol=0)
    assert torch.isfinite(output.value).all()


def _synthetic_trajectory(model):
    observations, critic, hidden, _ = _policy_inputs()
    generator = torch.Generator().manual_seed(98)
    obs = torch.randn(4, 2, PHYSICAL_UAVS, 9, generator=generator)
    states = torch.randn(4, 2, 13, generator=generator)
    masks = torch.ones(4, 2, PHYSICAL_UAVS, dtype=torch.bool)
    masks[1:3, :, 3] = False
    noise = torch.randn(4, 2, PHYSICAL_UAVS, ACTION_DIM, generator=generator)
    outputs = []
    hidden_before = []
    current = hidden
    with torch.no_grad():
        for t in range(4):
            hidden_before.append(current.clone())
            out = model.forward_step(
                observations=obs[t], active_mask=masks[t], critic_state=states[t],
                hidden=current, sampling_noise=noise[t]
            )
            outputs.append(out)
            current = out.next_hidden
    return G2Trajectory(
        observations=obs,
        active_mask=masks,
        critic_states=states,
        actions=torch.stack([x.actions for x in outputs]),
        pre_tanh_actions=torch.stack([x.pre_tanh_actions for x in outputs]),
        old_log_probs=torch.stack([x.token_log_probs for x in outputs]),
        old_values=torch.stack([x.value for x in outputs]),
        rewards=torch.zeros(4, 2),
        dones=torch.zeros(4, 2, dtype=torch.bool),
        hidden_before=torch.stack(hidden_before),
        hidden_after=torch.stack([x.next_hidden for x in outputs]),
        prefix_action_sums=torch.stack([x.prefix_action_sums for x in outputs]),
        qos=np.ones((4, 2)),
        safety_scores=np.ones((4, 2)),
        return_costs=np.zeros((4, 2)),
        cutoff_counts=np.zeros((4, 2), dtype=np.int64),
        depletion_counts=np.zeros((4, 2), dtype=np.int64),
        station_occupancy=np.zeros((4, 2, 2), dtype=np.int64),
        queue_lengths=np.zeros((4, 2, 2), dtype=np.int64),
        lifecycle_states=np.zeros((4, 2, PHYSICAL_UAVS), dtype=np.int8),
        next_lifecycle_states=np.zeros((4, 2, PHYSICAL_UAVS), dtype=np.int8),
        physical_consistency=np.ones((4, 2), dtype=np.bool_),
        events=((), ()),
        ledger_ids=("a", "b"),
    )


def test_replay_gae_and_ppo_exclude_inactive_rows_exactly():
    model = MatchedChargeRotationPolicy(9, 13, hidden_dim=8, routing_mode=FIXED_MASK_REC)
    trajectory = _synthetic_trajectory(model)
    replay = replay_g2_trajectory(model, trajectory, device=torch.device("cpu"))
    assert max(replay_errors(replay, trajectory).values()) <= 1e-6
    advantages, returns = compute_gae(trajectory.rewards, trajectory.old_values, trajectory.dones)
    baseline, _ = ppo_loss(replay, trajectory, advantages, returns)
    perturbed = replace(
        replay,
        log_probs=torch.where(
            replay.active_mask, replay.log_probs, torch.full_like(replay.log_probs, 50.0)
        ),
        entropies=torch.where(
            replay.active_mask, replay.entropies, torch.full_like(replay.entropies, -50.0)
        ),
    )
    changed, _ = ppo_loss(perturbed, trajectory, advantages, returns)
    torch.testing.assert_close(baseline, changed, rtol=0, atol=0)


def test_action_noise_is_episode_addressed_and_arm_pairable():
    a = make_action_noise([3, 4], action_seed=700, horizon=5)
    b = make_action_noise([3, 4], action_seed=700, horizon=5)
    c = make_action_noise([4, 3], action_seed=700, horizon=5)
    np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(a[:, 0], c[:, 1])
    np.testing.assert_array_equal(a[:, 1], c[:, 0])


def test_spawn_vector_collects_batched_masks_metrics_and_recurrent_rows():
    ledger = make_g2_episode_ledger(EnergyProfile.IID, 12, energy_seed=717)
    with PersistentG2VectorEnv([ledger], [818]) as vector:
        spec = vector.spec()
        assert spec["physical_width"] == PHYSICAL_UAVS
        assert spec["action_dim"] == ACTION_DIM
        model = MatchedChargeRotationPolicy(
            spec["observation_dim"],
            spec["critic_state_dim"],
            hidden_dim=8,
            routing_mode=FIXED_MASK_REC,
        )
        trajectory = collect_g2_trajectory(
            model,
            vector,
            episode_ids=[12],
            action_seed=919,
            device=torch.device("cpu"),
            horizon=2,
        )
        assert trajectory.observations.shape[:3] == (2, 1, PHYSICAL_UAVS)
        assert trajectory.actions.shape == (2, 1, PHYSICAL_UAVS, ACTION_DIM)
        assert trajectory.qos.shape == trajectory.safety_scores.shape == (2, 1)
        assert trajectory.physical_consistency.all()


def test_controls_share_initial_layout_then_only_constructive_requests_docking():
    env = _env(profile=EnergyProfile.LOW_ENERGY)
    try:
        constructive = ConstructiveChargeRotationController()
        no_proactive = NoProactiveRotationController()
        constructive.reset(env)
        no_proactive.reset(env)
        np.testing.assert_array_equal(constructive.service_targets, no_proactive.service_targets)
        constructive.force_departure_for_test(0)
        c_action = constructive.act(env)
        n_action = no_proactive.act(env)
        assert c_action.shape == n_action.shape == (PHYSICAL_UAVS, ACTION_DIM)
        assert c_action[0, 3] == 1.0
        assert np.all(n_action[:, 3] == -1.0)
        assert not constructive.trains and not no_proactive.trains
        assert constructive.name == CONSTRUCTIVE_CHARGE_ROTATION
        assert no_proactive.name == NO_PROACTIVE_ROTATION
    finally:
        env.close()


def test_constructive_exact_projection_candidate_order_and_strict_nearest_station():
    env = _env(profile=EnergyProfile.LOW_ENERGY)
    try:
        controller = ConstructiveChargeRotationController()
        controller.reset(env)
        evidence = controller.source_evidence()
        assert evidence["projection_mode"] == "exact_scripted_target_tracking_energy"
        expected = tuple(
            int(owner)
            for owner in np.argsort(controller.projected_terminal_margins, kind="stable")
            if controller.projected_terminal_margins[int(owner)] < 0.0
        )
        assert controller.candidate_order == expected
        assert evidence["candidate_iff_negative_terminal_margin"]
        for owner in controller.candidate_order:
            nearest = int(
                np.argmin(
                    np.linalg.norm(
                        env.charging_station_positions[: env.n_charging_stations]
                        - env.uav_positions[owner],
                        axis=1,
                    )
                )
            )
            assert controller.station_assignments[owner] == nearest
        assert evidence["strict_nearest_station_assignment"]
        assert not evidence["future_user_channel_queue_policy_rng_used"]
    finally:
        env.close()


def test_no_proactive_tracks_common_layout_until_departure_then_freezes():
    env = _env(profile=EnergyProfile.LOW_ENERGY)
    try:
        constructive = ConstructiveChargeRotationController()
        no_proactive = NoProactiveRotationController()
        constructive.reset(env)
        no_proactive.reset(env)
        constructive.departure_steps[:] = HORIZON + 1
        no_proactive._common_planner.departure_steps[:] = HORIZON + 1
        constructive.departure_steps[0] = 5
        no_proactive._common_planner.departure_steps[0] = 5
        env.current_step = 4
        np.testing.assert_array_equal(constructive.act(env), no_proactive.act(env))

        env.current_step = 5
        frozen = no_proactive.service_targets.copy()
        constructive_action = constructive.act(env)
        no_action = no_proactive.act(env)
        assert constructive_action[0, 3] == 1.0
        assert no_action[0, 3] == -1.0
        assert no_proactive.source_evidence()["targets_frozen_at_first_departure"]
        env.user_positions[:] = env.user_positions[::-1]
        no_proactive.act(env)
        np.testing.assert_array_equal(no_proactive.service_targets, frozen)
    finally:
        env.close()


def test_constructive_departure_evidence_is_fail_closed_when_no_safe_slot_exists():
    env = _env(profile=EnergyProfile.LOW_ENERGY)
    try:
        env.uav_battery_ratios[:] = env.service_cutoff_threshold + 1e-6
        controller = ConstructiveChargeRotationController()
        controller.reset(env)
        assert controller.candidate_order
        assert not controller.source_evidence()["latest_safe_departure_verified"]
    finally:
        env.close()


def test_constructive_reallocates_at_every_leave_and_rejoin_boundary():
    env = _env(profile=EnergyProfile.LOW_ENERGY)
    try:
        controller = ConstructiveChargeRotationController()
        controller.reset(env)
        env._lifecycle_state[0] = int(LifecycleState.CHARGE_ABSENT)
        env._episode_lifecycle_events.append(
            LifecycleEvent(10, 0, LifecycleEventKind.LEAVE, 0, 0.5)
        )
        controller._consume_boundary_events(env)
        env._lifecycle_state[0] = int(LifecycleState.ACTIVE)
        env._episode_lifecycle_events.append(
            LifecycleEvent(20, 0, LifecycleEventKind.REJOIN, 0, 0.8)
        )
        controller._consume_boundary_events(env)
        evidence = controller.source_evidence()
        assert evidence["lifecycle_boundary_steps"] == (10, 20)
        assert evidence["reallocation_event_steps"] == (10, 20)
        assert evidence["reallocation_after_every_leave_rejoin"]
    finally:
        env.close()


def test_rejoin_replan_preserves_overlapping_absent_station_and_completion():
    env = _env(profile=EnergyProfile.LOW_ENERGY)
    try:
        controller = ConstructiveChargeRotationController()
        controller.reset(env)
        env.current_step = 50
        env.uav_battery_ratios[:] = 1.0
        env.uav_battery_ratios[0] = 0.50
        env._lifecycle_state[0] = int(LifecycleState.CHARGE_ABSENT)
        env._assigned_station[0] = 0
        controller.departure_steps[0] = 10
        controller.station_assignments[0] = 0
        controller.planned_completion_steps[0] = 120

        controller.departure_steps[1] = 5
        controller.station_assignments[1] = 1
        controller.planned_completion_steps[1] = 50
        controller._plan_consistency = True
        env._episode_lifecycle_events.append(
            LifecycleEvent(50, 1, LifecycleEventKind.REJOIN, 1, 0.8)
        )
        controller._consume_boundary_events(env)

        assert controller.departure_steps[0] == 10
        assert controller.station_assignments[0] == 0
        assert controller.planned_completion_steps[0] == 120
        audit = controller.source_evidence()["projection_audit_history"][-1]
        assert audit.trigger == "REJOIN"
        assert audit.station_assignments[0] == 0
        assert audit.departure_steps[0] == 10
        assert audit.planned_completion_steps[0] == 120
        assert 0 not in audit.candidate_order
        assert controller.source_evidence()["plan_consistency"]
    finally:
        env.close()


def test_projection_history_keeps_initial_pressure_and_earlier_audit_failure():
    env = _env(profile=EnergyProfile.LOW_ENERGY)
    try:
        controller = ConstructiveChargeRotationController()
        controller.reset(env)
        initial = controller.source_evidence()
        assert initial["projection_audit_count"] == 1
        assert initial["initial_candidate_order"] == initial["candidate_order"]
        assert initial["initial_source_pressure"] == bool(initial["candidate_order"])

        env.current_step = HORIZON - REJOIN_WINDOW
        env.uav_battery_ratios[:] = 1.0
        controller.service_targets = g2_source.deterministic_service_layout(env)
        controller._project_schedule(env, trigger="REJOIN")
        evidence = controller.source_evidence()
        audits = evidence["projection_audit_history"]
        assert isinstance(audits, tuple) and len(audits) == 2
        assert not audits[0].passed
        assert audits[-1].candidate_order == ()
        assert evidence["initial_candidate_order"] == audits[0].candidate_order
        assert evidence["initial_source_pressure"] == bool(audits[0].candidate_order)
        assert evidence["all_projection_audits_pass"] == all(
            audit.passed for audit in audits
        )
        assert not evidence["all_projection_audits_pass"]
        assert all(audit.current_only_planning for audit in audits)
    finally:
        env.close()


def test_episode_metric_boundaries_and_source_support_facts():
    qos = np.full(HORIZON, 0.90)
    safety = np.full(HORIZON, 0.90)
    return_cost = np.zeros(HORIZON)
    cutoff = np.zeros(HORIZON, dtype=np.int64)
    depletion = np.zeros(HORIZON, dtype=np.int64)
    active = np.ones((HORIZON, PHYSICAL_UAVS), dtype=np.bool_)
    active[100:140, 0] = False
    occupancy = np.zeros((HORIZON, 2), dtype=np.int64)
    occupancy[100:140, 0] = 1
    queues = np.zeros((HORIZON, 2), dtype=np.int64)
    queues[100:140, 0] = 1
    actions = np.zeros((HORIZON, PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32)
    events = (
        LifecycleEvent(100, 0, LifecycleEventKind.LEAVE, 0, 0.5),
        LifecycleEvent(140, 0, LifecycleEventKind.REJOIN, 0, 0.8),
    )
    metrics = compute_episode_metrics(
        qos=qos,
        safety_scores=safety,
        return_costs=return_cost,
        cutoff_counts=cutoff,
        depletion_counts=depletion,
        active_masks=active,
        station_occupancy=occupancy,
        queue_lengths=queues,
        service_actions=actions,
        executed_action_masks=active,
        events=events,
        physical_consistency=True,
    )
    assert isinstance(metrics, G2EpisodeMetrics)
    assert metrics.phi == pytest.approx(0.90)
    assert metrics.j_event == pytest.approx(1.0)
    assert metrics.j_rejoin == pytest.approx(1.0)
    assert metrics.q_ordinary == pytest.approx(0.90)
    assert metrics.catastrophe_episode == 0
    assert metrics.complete_charge_cycles == 1
    assert metrics.complete_recovery_windows
    assert metrics.queue_uav_steps == 40
    assert metrics.max_queue_length == 1
    assert len(metrics.action_path_sha256) == 64
    assert metrics.action_path_sha256 == metrics.action_path_sha256.lower()
    assert cell_access(0.80, 0.90) == pytest.approx(1.0)
    facts = source_support_facts([metrics])
    assert facts["constructive_cutoff_events"] == 0
    assert facts["constructive_depletion_events"] == 0
    assert facts["constructive_return_cost_zero"]
    assert facts["station_used_every_episode"]
    assert facts["physical_consistency"]


def test_incomplete_rejoin_window_is_not_imputed():
    events = (
        LifecycleEvent(1441, 0, LifecycleEventKind.LEAVE, 0, 0.5),
        LifecycleEvent(1490, 0, LifecycleEventKind.REJOIN, 0, 0.8),
    )
    active = np.ones((HORIZON, PHYSICAL_UAVS), dtype=np.bool_)
    active[1441:1490, 0] = False
    metrics = compute_episode_metrics(
        qos=np.ones(HORIZON),
        safety_scores=np.ones(HORIZON),
        return_costs=np.zeros(HORIZON),
        cutoff_counts=np.zeros(HORIZON, dtype=np.int64),
        depletion_counts=np.zeros(HORIZON, dtype=np.int64),
        active_masks=active,
        station_occupancy=np.zeros((HORIZON, 2), dtype=np.int64),
        queue_lengths=np.zeros((HORIZON, 2), dtype=np.int64),
        service_actions=np.zeros(
            (HORIZON, PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32
        ),
        executed_action_masks=active,
        events=events,
        physical_consistency=True,
    )
    assert metrics.j_rejoin is None
    assert not metrics.complete_recovery_windows


def test_action_path_digest_is_stable_and_binds_dense_actions_plus_support():
    actions = np.zeros((7, PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32)
    masks = np.ones((7, PHYSICAL_UAVS), dtype=np.bool_)
    first = action_path_digest(actions, masks)
    second = action_path_digest(actions.copy(), masks.copy())
    assert first == second
    assert len(first) == 64 and first == first.lower()
    changed_action = actions.copy()
    changed_action[3, 2, 1] = np.float32(0.25)
    assert action_path_digest(changed_action, masks) != first
    changed_mask = masks.copy()
    changed_mask[3, 2] = False
    assert action_path_digest(actions, changed_mask) != first

    model = MatchedChargeRotationPolicy(9, 13, hidden_dim=8, routing_mode=FIXED_MASK_REC)
    observations, critic, initial_hidden, _noise = _policy_inputs(batch=1)
    active = torch.ones(1, PHYSICAL_UAVS, dtype=torch.bool)

    def deterministic_path():
        hidden = initial_hidden.clone()
        rows = []
        with torch.no_grad():
            for _ in range(4):
                output = model.forward_step(
                    observations=observations,
                    active_mask=active,
                    critic_state=critic,
                    hidden=hidden,
                    deterministic=True,
                )
                rows.append(output.actions[0].numpy())
                hidden = output.next_hidden
        return action_path_digest(np.stack(rows), np.ones((4, PHYSICAL_UAVS), bool))

    assert deterministic_path() == deterministic_path()


def test_terminal_hidden_is_deleted_while_charge_absence_only_freezes():
    model = MatchedChargeRotationPolicy(9, 13, hidden_dim=8, routing_mode=FIXED_MASK_REC)
    trajectory = _synthetic_trajectory(model)
    # Owner 3 was temporarily absent at t=1 and therefore retains its state.
    torch.testing.assert_close(
        trajectory.hidden_after[1, :, 3], trajectory.hidden_before[1, :, 3], rtol=0, atol=0
    )
    # Convert that boundary to terminal ownership deletion and make the stored
    # recurrent sequence reflect the frozen collector rule.
    trajectory.next_lifecycle_states[1:, :, 3] = int(LifecycleState.TERMINAL)
    trajectory.lifecycle_states[2:, :, 3] = int(LifecycleState.TERMINAL)
    trajectory.hidden_after[1:, :, 3] = 0.0
    trajectory.hidden_before[2:, :, 3] = 0.0
    replay = replay_g2_trajectory(model, trajectory, device=torch.device("cpu"))
    assert torch.count_nonzero(replay.hidden_after[1:, :, 3]) == 0


def test_policy_evaluation_deletes_terminal_hidden_before_next_action(monkeypatch):
    class RecordingPolicy(MatchedChargeRotationPolicy):
        def __init__(self):
            super().__init__(9, 13, hidden_dim=8, routing_mode=FIXED_MASK_REC)
            self.hidden_inputs = []

        def forward_step(self, **kwargs):
            self.hidden_inputs.append(kwargs["hidden"].detach().clone())
            return super().forward_step(**kwargs)

    rng = np.random.default_rng(707)
    active = np.ones((1, PHYSICAL_UAVS), dtype=np.bool_)
    initial_view = g2_source.G2CurrentView(
        observations=rng.standard_normal((1, PHYSICAL_UAVS, 9)).astype(np.float32),
        active_mask=active.copy(),
        critic_state=rng.standard_normal((1, 13)).astype(np.float32),
        lifecycle_state=np.zeros((1, PHYSICAL_UAVS), dtype=np.int8),
        physical_positions=np.zeros((1, PHYSICAL_UAVS, 3), dtype=np.float64),
        battery_ratios=np.ones((1, PHYSICAL_UAVS), dtype=np.float64),
        station_occupancy=np.zeros((1, 2), dtype=np.int64),
        queue_lengths=np.zeros((1, 2), dtype=np.int64),
        physical_step=0,
    )
    terminal_active = active.copy()
    terminal_active[0, 2] = False
    terminal_state = np.zeros((1, PHYSICAL_UAVS), dtype=np.int8)
    terminal_state[0, 2] = int(LifecycleState.TERMINAL)
    next_view = replace(
        initial_view,
        active_mask=terminal_active,
        lifecycle_state=terminal_state,
        physical_step=1,
    )

    class FakeVector:
        count = 1
        current_view = initial_view

        def step(self, actions):
            self.current_view = next_view
            return g2_source.G2VectorTransition(
                view=next_view,
                rewards=np.zeros(1, dtype=np.float32),
                qos=np.ones(1),
                safety_scores=np.ones(1),
                return_costs=np.zeros(1),
                cutoff_counts=np.zeros(1, dtype=np.int64),
                depletion_counts=np.zeros(1, dtype=np.int64),
                dones=np.zeros(1, dtype=np.bool_),
                executed_action_mask=active.copy(),
                physical_action_mask=active.copy(),
                service_actions=np.asarray(actions, dtype=np.float32).copy(),
                events=((),),
                source_facts=({"physical_consistency": True},),
            )

    model = RecordingPolicy()

    def two_step_rollout(vector, provider):
        first = provider(0, initial_view)
        provider(1, first.view)
        assert torch.count_nonzero(model.hidden_inputs[1][0, 2]) == 0
        assert torch.count_nonzero(model.hidden_inputs[1][0, 0]) > 0
        return (), ()

    monkeypatch.setattr(g2_source, "_evaluate_g2_rollout", two_step_rollout)
    assert g2_source.evaluate_g2_policy(
        model,
        FakeVector(),
        episode_ids=[0],
        action_seed=1,
        device=torch.device("cpu"),
        deterministic=True,
    ) == ()


def test_checkpoint_payload_restores_model_optimizer_clock_seed_and_torch_rng():
    torch.manual_seed(303)
    model = MatchedChargeRotationPolicy(9, 13, hidden_dim=8, routing_mode=FIXED_MASK_REC)
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    sum(parameter.sum() for parameter in model.parameters()).backward()
    optimizer.step()
    expected_state = model_state_copy(model)
    payload = g2_checkpoint_state(
        model=model,
        optimizer=optimizer,
        completed_updates=17,
        next_episode_id=136,
        seed_contract={"model": 101, "environment": 202, "action": 303},
    )
    expected_random = torch.rand(5)
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.add_(10.0)
    torch.manual_seed(999)
    restored = load_g2_checkpoint_state(
        payload,
        model=model,
        optimizer=optimizer,
        expected_seed_contract={"model": 101, "environment": 202, "action": 303},
    )
    assert maximum_state_difference(expected_state, model_state_copy(model)) == 0.0
    torch.testing.assert_close(torch.rand(5), expected_random, rtol=0, atol=0)
    assert restored == {"completed_updates": 17, "next_episode_id": 136}
    with pytest.raises(ValueError, match="seed contract"):
        load_g2_checkpoint_state(
            payload,
            model=model,
            optimizer=optimizer,
            expected_seed_contract={"model": 0},
        )
