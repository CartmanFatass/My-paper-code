"""Physical transmitter silence and the base radio's pure planning kernel."""

import numpy as np
import pytest

from envs.pettingzoo import uav_radio
from envs.pettingzoo.uav_env import MultiUAVEnv


def _rng_equal(first, second):
    assert first[0] == second[0]
    np.testing.assert_array_equal(first[1], second[1])
    assert first[2:] == second[2:]


def _scalar_radio(uavs, users, mask, tx_power=23., noise_power=-80., frequency=2e9):
    """Independent direct free-space and interference formulas, row by row."""
    loss = np.empty((len(uavs), len(users)))
    sinr = np.full_like(loss, -np.inf)
    for i, uav in enumerate(uavs):
        for j, user in enumerate(users):
            distance = max(float(np.linalg.norm(uav - np.array([user[0], user[1], 0.]))), 1e-6)
            loss[i, j] = 20 * np.log10(distance) + 20 * np.log10(4 * np.pi * frequency / 3e8)
    for i in range(len(uavs)):
        if not mask[i]:
            continue
        for j in range(len(users)):
            interference = sum(
                10 ** ((tx_power - loss[k, j]) / 10)
                for k in range(len(uavs)) if k != i and mask[k]
            )
            sinr[i, j] = tx_power - loss[i, j] - 10 * np.log10(
                10 ** (noise_power / 10) + interference
            )
    return loss, sinr


def _scalar_assignment(sinr, threshold=3., capacity=10):
    pairs = [
        (i, j, sinr[i, j])
        for i in range(sinr.shape[0]) for j in range(sinr.shape[1])
        if sinr[i, j] >= threshold
    ]
    pairs.sort(key=lambda item: item[2], reverse=True)
    assigned = np.zeros(sinr.shape, dtype=bool)
    for i, j, _ in pairs:
        if not assigned[:, j].any() and assigned[i].sum() < capacity:
            assigned[i, j] = True
    return assigned


def _fixed_env(backend="vectorized", **kwargs):
    env = MultiUAVEnv(
        n_uavs=3, n_users=4, seed=79, channel_backend=backend,
        enable_transmitter_mask=True, **kwargs,
    )
    env.uav_positions[:] = np.array([
        [100., 100., 100.], [100., 100., 100.], [400., 400., 100.]
    ])
    env.user_positions[:] = np.array([
        [100., 100.], [110., 100.], [400., 400.], [300., 300.]
    ])
    env._begin_path_loss_step()
    env._update_channel_state()
    return env


def test_mask_opt_in_validation_copy_reset_and_default_parity():
    ordinary = MultiUAVEnv(n_uavs=3, n_users=4, seed=41)
    enabled = MultiUAVEnv(n_uavs=3, n_users=4, seed=41, enable_transmitter_mask=True)
    np.testing.assert_array_equal(enabled.transmitter_mask, [True] * 3)
    np.testing.assert_array_equal(ordinary.sinr_matrix, enabled.sinr_matrix)
    np.testing.assert_array_equal(ordinary.connections, enabled.connections)
    assert ordinary._compute_reward() == enabled._compute_reward()
    with pytest.raises(RuntimeError, match="not enabled"):
        ordinary.set_transmitter_mask(np.array([True, False, True]))
    with pytest.raises(TypeError, match="enable_transmitter_mask"):
        MultiUAVEnv(enable_transmitter_mask="yes")
    for invalid in ([1, 0, 1], np.array([True, False]), np.ones((3, 1), dtype=bool)):
        with pytest.raises(ValueError, match="boolean"):
            enabled.set_transmitter_mask(invalid)
    supplied = np.array([True, False, True])
    enabled.set_transmitter_mask(supplied)
    supplied[:] = False
    exported = enabled.transmitter_mask
    exported[:] = False
    np.testing.assert_array_equal(enabled.transmitter_mask, [True, False, True])
    np.testing.assert_array_equal(enabled.reset(seed=41)[0]["uav_0"]["obs"],
                                  ordinary.reset(seed=41)[0]["uav_0"]["obs"])
    np.testing.assert_array_equal(enabled.transmitter_mask, [True] * 3)
    actions = {agent: np.array([.1, -.2, .3]) for agent in ordinary.agents}
    left = ordinary.step(actions)
    right = enabled.step(actions)
    np.testing.assert_array_equal(left[0]["uav_0"]["obs"], right[0]["uav_0"]["obs"])
    assert left[1] == right[1]


@pytest.mark.parametrize("mask", [
    [True, True, True], [True, False, True], [False, True, False], [False, False, False]
])
def test_kernel_and_both_backends_match_independent_scalar_radio(mask):
    mask = np.array(mask, dtype=bool)
    vector = _fixed_env()
    scalar = _fixed_env("reference")
    observations = vector.set_transmitter_mask(mask)
    scalar.set_transmitter_mask(mask)
    loss_expected, sinr_expected = _scalar_radio(vector.uav_positions, vector.user_positions, mask)
    np.testing.assert_allclose(
        uav_radio.free_space_user_path_loss(vector.uav_positions, vector.user_positions),
        loss_expected, atol=1e-12,
    )
    np.testing.assert_allclose(
        uav_radio.user_sinr_from_path_loss(loss_expected, transmitter_mask=mask),
        sinr_expected, atol=1e-9,
    )
    np.testing.assert_allclose(vector.sinr_matrix, sinr_expected, atol=1e-9)
    np.testing.assert_allclose(scalar.sinr_matrix, sinr_expected, atol=1e-9)
    assignment = _scalar_assignment(sinr_expected)
    np.testing.assert_array_equal(vector.connections, assignment)
    np.testing.assert_array_equal(scalar.connections, assignment)
    metrics = uav_radio.service_metrics(sinr_expected, assignment)
    assert vector._compute_reward() == pytest.approx(metrics["J"], abs=1e-12)
    assert metrics["served"] == int(assignment.sum())
    assert all(value["obs"].shape == (vector.obs_dim,) for value in observations.values())
    if not mask.any():
        assert metrics["J"] == 0
        assert all(not vector._get_local_users(i) for i in range(3))


def test_single_active_is_snr_and_muting_relieves_interference():
    env = _fixed_env()
    all_on = env.sinr_matrix.copy()
    env.set_transmitter_mask(np.array([True, False, False]))
    expected = env.tx_power - env._uav_user_path_loss_matrix[0] - env.noise_power
    np.testing.assert_allclose(env.sinr_matrix[0], expected, atol=1e-12)
    assert np.all(np.isneginf(env.sinr_matrix[1:]))
    assert np.all(env.sinr_matrix[0] > all_on[0])
    assert not env.connections[1:].any()


def test_fdma_silence_removes_serving_without_changing_active_snr():
    env = _fixed_env(use_fdma=True)
    active_snr = env.sinr_matrix[0].copy()
    env.set_transmitter_mask(np.array([True, False, False]))
    np.testing.assert_array_equal(env.sinr_matrix[0], active_snr)
    assert np.all(np.isneginf(env.sinr_matrix[1:]))
    assert not env.connections[1:].any()


def test_assignment_capacity_exclusivity_and_equal_site_ties():
    values = np.array([[8., 8., 8., 2.], [8., 7., 6., 4.]])
    expected = np.array([[True, True, False, False], [False, False, True, True]])
    np.testing.assert_array_equal(
        uav_radio.greedy_connection_assignment(values, max_connections=2), expected
    )
    env = _fixed_env()
    env.set_transmitter_mask(np.array([True, True, False]))
    assert np.all(env.sinr_matrix[0] == env.sinr_matrix[1])
    assert np.all(env.connections.sum(axis=0) <= 1)
    assert not env.connections[2].any()


@pytest.mark.parametrize("backend", ["vectorized", "reference"])
def test_peer_discovery_requires_both_endpoints_and_mutes_interference(backend):
    env = _fixed_env(backend)
    env.set_transmitter_mask(np.array([True, True, True]))
    with_interference = env._compute_uav_to_uav_sinr(0, 1)
    env.set_transmitter_mask(np.array([True, True, False]))
    without_interference = env._compute_uav_to_uav_sinr(0, 1)
    assert without_interference > with_interference
    assert [idx for idx, _ in env._get_local_uavs(0)] == [1]
    env.set_transmitter_mask(np.array([True, False, False]))
    assert env._get_local_uavs(0) == []
    assert env._get_local_uavs(1) == []
    assert env._compute_uav_to_uav_sinr(0, 1) == -np.inf


@pytest.mark.parametrize("backend", ["vectorized", "reference"])
def test_mask_refresh_preserves_stochastic_realization_and_rng(backend):
    env = MultiUAVEnv(
        n_uavs=3, n_users=4, seed=91, channel_model="3gpp-36777",
        use_shadowing=True, channel_backend=backend, enable_transmitter_mask=True,
    )
    physical = env._uav_user_path_loss_matrix.copy()
    rng = env.np_random.get_state()
    generation = env._path_loss_cache_generation
    first = env.sinr_matrix.copy()
    env.set_transmitter_mask(np.array([True, False, True]))
    np.testing.assert_array_equal(env._uav_user_path_loss_matrix, physical)
    _rng_equal(rng, env.np_random.get_state())
    assert env._path_loss_cache_generation == generation
    assert np.all(np.isneginf(env.sinr_matrix[1]))
    env.set_transmitter_mask(np.array([True, True, True]))
    np.testing.assert_allclose(env.sinr_matrix, first, atol=1e-9)
    _rng_equal(rng, env.np_random.get_state())


@pytest.mark.parametrize("channel_model", [
    "free_space", "urban", "suburban", "3gpp-36777", "probabilistic"
])
@pytest.mark.parametrize("backend", ["vectorized", "reference"])
def test_all_on_opt_in_matches_default_across_channel_models(channel_model, backend):
    kwargs = dict(
        n_uavs=3, n_users=6, seed=227, channel_model=channel_model,
        channel_backend=backend, use_shadowing=channel_model == "3gpp-36777",
    )
    ordinary = MultiUAVEnv(**kwargs)
    masked = MultiUAVEnv(enable_transmitter_mask=True, **kwargs)
    np.testing.assert_array_equal(masked.sinr_matrix, ordinary.sinr_matrix)
    np.testing.assert_array_equal(masked.connections, ordinary.connections)
    _rng_equal(masked.np_random.get_state(), ordinary.np_random.get_state())
    actions = {agent: np.array([.2, -.1, .1]) for agent in ordinary.agents}
    for _ in range(2):
        normal_result = ordinary.step(actions)
        opt_in_result = masked.step(actions)
        np.testing.assert_array_equal(masked.sinr_matrix, ordinary.sinr_matrix)
        np.testing.assert_array_equal(masked.connections, ordinary.connections)
        assert opt_in_result[1] == normal_result[1]
        for agent in ordinary.agents:
            np.testing.assert_array_equal(
                opt_in_result[0][agent]["obs"], normal_result[0][agent]["obs"]
            )
        _rng_equal(masked.np_random.get_state(), ordinary.np_random.get_state())


@pytest.mark.parametrize("backend", ["vectorized", "reference"])
def test_mask_refresh_keeps_positions_and_state_but_changes_observation(backend):
    env = _fixed_env(backend)
    positions = env.uav_positions.copy()
    state = env._get_state().copy()
    before = env._get_observation("uav_0")["obs"].copy()
    refreshed = env.set_transmitter_mask(np.array([True, False, False]))
    np.testing.assert_array_equal(env.uav_positions, positions)
    np.testing.assert_array_equal(env._get_state(), state)
    assert refreshed["uav_0"]["obs"].shape == before.shape
    assert not np.array_equal(refreshed["uav_0"]["obs"], before)
