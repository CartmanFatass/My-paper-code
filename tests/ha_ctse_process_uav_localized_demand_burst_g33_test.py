import numpy as np

from ha_ctse_process.uav_localized_demand_burst_g33 import (
    BurstProfile,
    UAVLocalizedDemandBurstEnv,
    make_g33_episode_ledger,
)


def _expected_field_draw(seed, episode_id, profile, namespace, low, high):
    profile_index = tuple(BurstProfile).index(profile)
    rng = np.random.default_rng(
        np.random.SeedSequence([seed, episode_id, profile_index, 0x473333, namespace])
    )
    return int(rng.integers(low, high))


def test_exact_current_demand_normalization_table():
    ledger = make_g33_episode_ledger(BurstProfile.NO_BURST, 0, burst_seed=2)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=5)
    try:
        env.reset(seed=5)
        env.current_user_demand_bps[:5] = 1.0e6 * np.array(
            [1.0, 1.5, 2.0, 2.25, 2.5], dtype=np.float64
        )
        np.testing.assert_allclose(
            env._normalized_current_demand()[:5],
            np.array([0.0, 1.0 / 3.0, 2.0 / 3.0, 5.0 / 6.0, 1.0]),
            rtol=0.0,
            atol=1e-15,
        )
    finally:
        env.close()


def test_episode_ledger_is_immutable_and_does_not_touch_environment_rng():
    first = make_g33_episode_ledger(BurstProfile.IID_BURST, 7, burst_seed=19)
    second = make_g33_episode_ledger(BurstProfile.IID_BURST, 7, burst_seed=19)

    assert first == second
    assert first.onset in range(140, 261)
    assert first.duration in range(40, 81)
    assert first.multiplier in {1.5, 2.0}
    assert first.center_selector in range(30)
    assert first.onset == _expected_field_draw(19, 7, BurstProfile.IID_BURST, 101, 140, 261)
    assert first.duration == _expected_field_draw(19, 7, BurstProfile.IID_BURST, 102, 40, 81)
    assert first.multiplier == (1.5, 2.0)[
        _expected_field_draw(19, 7, BurstProfile.IID_BURST, 103, 0, 2)
    ]
    assert first.center_selector == _expected_field_draw(
        19, 7, BurstProfile.IID_BURST, 104, 0, 30
    )

    alternate = make_g33_episode_ledger(BurstProfile.REMOTE_STRONG, 7, burst_seed=113)
    first_env = UAVLocalizedDemandBurstEnv(first, environment_seed=41)
    second_env = UAVLocalizedDemandBurstEnv(alternate, environment_seed=41)
    try:
        first_env.reset(seed=41)
        second_env.reset(seed=41)
        np.testing.assert_array_equal(first_env.user_positions, second_env.user_positions)
        np.testing.assert_array_equal(first_env.uav_positions, second_env.uav_positions)
        np.testing.assert_array_equal(first_env.sinr_matrix, second_env.sinr_matrix)
        actions = {agent: np.zeros(first_env.action_dim, dtype=np.float32) for agent in first_env.agents}
        first_step = first_env.step(actions)
        second_step = second_env.step(actions)
        np.testing.assert_array_equal(first_env.user_positions, second_env.user_positions)
        np.testing.assert_array_equal(first_env.uav_positions, second_env.uav_positions)
        np.testing.assert_array_equal(first_env.sinr_matrix, second_env.sinr_matrix)
        np.testing.assert_array_equal(
            first_step[0][first_env.agents[0]]["obs"],
            second_step[0][second_env.agents[0]]["obs"],
        )
        assert first_step[1] == second_step[1]
    finally:
        first_env.close()
        second_env.close()


def test_pre_action_burst_boundaries_and_fixed_onset_cohort():
    ledger = make_g33_episode_ledger(BurstProfile.IID_BURST, 3, burst_seed=5)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=11)
    try:
        env.reset(seed=11)
        env.current_step = ledger.onset
        env.sync_burst_pre_action()
        cohort = env.affected_cohort.copy()
        assert np.all(env.current_user_demand_bps[cohort] == 1.0e6 * ledger.multiplier)

        env.user_positions[:] = np.flip(env.user_positions, axis=0)
        env.sync_burst_pre_action()
        np.testing.assert_array_equal(env.affected_cohort, cohort)

        env.current_step = ledger.onset + ledger.duration
        env.sync_burst_pre_action()
        np.testing.assert_array_equal(env.current_user_demand_bps, np.full(env.n_users, 1.0e6))
        diagnostic = env.source_diagnostics()["collective_onset_visibility"]
        assert diagnostic["onset_step"] == ledger.onset
        assert tuple(cohort) == diagnostic["affected_cohort"]
    finally:
        env.close()


def test_g33_actor_and_critic_exclude_time_and_future_but_include_current_demand():
    ledger = make_g33_episode_ledger(BurstProfile.EARLY_LONG, 1, burst_seed=3)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=13)
    try:
        observations, _ = env.reset(seed=13)
        assert observations[env.agents[0]]["obs"].shape == (env.obs_dim,)
        state = env._get_state()
        assert state.shape == (env.state_dim,)
        assert env.actor_user_record_width == 7
        assert env.critic_user_record_width == 7
        assert env.current_step == 0
        diagnostics = env.source_diagnostics()
        assert not diagnostics["future_ledger_exposed"]
        assert not diagnostics["assignment_exposed"]
    finally:
        env.close()


def test_fixed_physical_and_demand_snapshot_is_exactly_time_invariant_for_actor_and_critic():
    ledger = make_g33_episode_ledger(BurstProfile.NO_BURST, 1, burst_seed=7)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=43)
    try:
        observations, _ = env.reset(seed=43)
        actor_before = observations[env.agents[0]]["obs"].copy()
        critic_before = env._get_state().copy()
        env.current_step = 237
        actor_after = env._get_observation(env.agents[0])["obs"]
        critic_after = env._get_state()
        np.testing.assert_array_equal(actor_before, actor_after)
        np.testing.assert_array_equal(critic_before, critic_after)
    finally:
        env.close()


def test_actor_and_critic_demand_rows_follow_exact_frozen_mapping_at_onset():
    ledger = make_g33_episode_ledger(BurstProfile.IID_BURST, 12, burst_seed=31)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=47)
    try:
        env.reset(seed=47)
        env.current_step = ledger.onset
        env.sync_burst_pre_action()
        expected = np.clip(
            (env.current_user_demand_bps / 1.0e6 - 1.0) / 1.5, 0.0, 1.0
        )
        np.testing.assert_array_equal(env._normalized_current_demand(), expected)

        # Place all current records in one unchanged local sensing ball so every
        # source demand value must appear in anonymous actor rows.
        env.user_positions[:, :] = env.uav_positions[0]
        actor_rows = env._actor_user_rows(0)
        np.testing.assert_array_equal(
            np.sort(actor_rows[:, 5]), np.sort(expected.astype(np.float32))
        )

        state = env._get_state()
        prefix = env.n_uavs * 3 + env.n_uavs
        critic_rows = state[prefix : prefix + env.n_users * 7].reshape(env.n_users, 7)
        np.testing.assert_array_equal(critic_rows[:, 6], expected.astype(np.float32))
        assert env.source_diagnostics()["future_ledger_exposed"] is False
        assert env.source_diagnostics()["assignment_exposed"] is False
    finally:
        env.close()


def test_source_step_returns_next_pre_action_view_without_physics_rewrite():
    ledger = make_g33_episode_ledger(BurstProfile.IID_BURST, 4, burst_seed=41)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=37)
    try:
        env.reset(seed=37)
        actions = {agent: np.zeros(env.action_dim, dtype=np.float32) for agent in env.agents}
        observations, _rewards, _terminations, _truncations, infos = env.step(actions)
        assert env.current_step == 1
        assert all(row["obs"].shape == (env.obs_dim,) for row in observations.values())
        assert infos[env.agents[0]]["next_state"].shape == (env.state_dim,)
        np.testing.assert_array_equal(env.current_user_demand_bps, np.full(env.n_users, 1.0e6))
    finally:
        env.close()


def test_next_boundary_demand_is_installed_before_one_view_materialization(monkeypatch):
    ledger = make_g33_episode_ledger(BurstProfile.IID_BURST, 14, burst_seed=53)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=59)
    try:
        env.reset(seed=59)
        env.current_step = ledger.onset - 1
        env.sync_burst_pre_action()
        observation_calls = 0
        state_calls = 0
        original_observation = env._get_observation
        original_state = env._get_state

        def counted_observation(agent):
            nonlocal observation_calls
            observation_calls += 1
            return original_observation(agent)

        def counted_state():
            nonlocal state_calls
            state_calls += 1
            return original_state()

        monkeypatch.setattr(env, "_get_observation", counted_observation)
        monkeypatch.setattr(env, "_get_state", counted_state)
        actions = {
            agent: np.zeros(env.action_dim, dtype=np.float32)
            for agent in env.agents
        }
        observations, _rewards, _terminations, _truncations, infos = env.step(actions)

        assert env.current_step == ledger.onset
        assert observation_calls == len(env.agents)
        assert state_calls == 1
        assert env.affected_cohort.size == 8
        expected = env._normalized_current_demand().astype(np.float32)
        next_state = infos[env.agents[0]]["next_state"]
        prefix = env.n_uavs * 3 + env.n_uavs
        critic_rows = next_state[prefix : prefix + env.n_users * 7].reshape(
            env.n_users, 7
        )
        np.testing.assert_array_equal(critic_rows[:, 6], expected)
        assert all(row["obs"].shape == (env.obs_dim,) for row in observations.values())
        np.testing.assert_array_equal(
            env.last_reward_demand_bps,
            env.last_graph_potential_demand_bps,
        )
    finally:
        env.close()


def test_demand_only_change_preserves_raw_physics_and_changes_delivered_service(monkeypatch):
    ledger = make_g33_episode_ledger(BurstProfile.IID_BURST, 8, burst_seed=17)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=23)
    try:
        env.reset(seed=23)
        raw_capacity = np.full(env.n_users, 1.5e6, dtype=np.float64)
        monkeypatch.setattr(
            env,
            "_calculate_end_to_end_user_rates",
            lambda: (
                raw_capacity.copy(),
                np.zeros((env.n_uavs, env.n_users), dtype=np.float64),
                np.zeros(env.n_uavs, dtype=np.float64),
            ),
        )
        baseline = env.demand_only_invariance_diagnostic(
            np.full(env.n_users, 2.0e6, dtype=np.float64)
        )
        assert baseline["raw_physics_equal"]
        assert baseline["delivered_traffic_changed"]
        assert baseline["same_demand_vector_for_reward_and_potential"]
        env.current_user_demand_bps[:] = 2.0e6
        env._calculate_constrained_safety_reward(0.0, 0.0, 0.0, 0.0, False, 0.0, {})
        env._graph_service_potential()
        np.testing.assert_array_equal(
            env.last_reward_demand_bps,
            env.last_graph_potential_demand_bps,
        )
    finally:
        env.close()


def test_actor_user_rows_are_anonymous_under_equal_physical_row_permutation():
    ledger = make_g33_episode_ledger(BurstProfile.NO_BURST, 0, burst_seed=29)
    env = UAVLocalizedDemandBurstEnv(ledger, environment_seed=31)
    try:
        env.reset(seed=31)
        user = 0
        env.user_positions[1] = env.user_positions[user]
        env.current_user_demand_bps[[user, 1]] = 1.0e6
        first = env._actor_user_rows(0)
        env.user_positions[[user, 1]] = env.user_positions[[1, user]]
        second = env._actor_user_rows(0)
        np.testing.assert_array_equal(first, second)
    finally:
        env.close()
