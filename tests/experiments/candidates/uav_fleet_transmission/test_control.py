"""Correctness fixtures only: never expose a declared B01 study world."""

from itertools import product
import json

import numpy as np
import pytest

from envs.pettingzoo import uav_radio
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from experiments.candidates.load_critical_member_generalization.load_probe.scenes import matched_world
from experiments.candidates.uav_fleet_transmission import control, host


@pytest.fixture
def make_fleet(monkeypatch):
    monkeypatch.setattr(host, "world", lambda _: matched_world(0))
    return lambda n=4: host.FleetS1(n, 0, horizon=20)


def _rng_equal(left, right):
    assert left[0] == right[0]
    np.testing.assert_array_equal(left[1], right[1])
    assert left[2:] == right[2:]


def _oracle(users, positions, mask):
    loss = uav_radio.free_space_user_path_loss(positions, users)
    sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=host.mask_bits(mask, len(positions)))
    connections = uav_radio.greedy_connection_assignment(sinr, 0, 10)
    # Scalar reward accumulation independently retains native member/user order.
    total = 0
    for member in range(len(positions)):
        for user in range(50):
            if connections[member, user]:
                total += np.clip(sinr[member, user] / 30, 0, 1)
    served = int(connections.sum())
    quality = total / max(served, 1)
    height = (np.mean(positions[:, 2]) - 50) / 100 * .1
    return dict(J=.7 * (served / 50) + .3 * quality - height,
                served=served, quality=quality, energy_penalty=height)


@pytest.mark.parametrize("n", [4, 8])
def test_all_on_native_equivalence_and_rng(make_fleet, n):
    fleet = make_fleet(n)
    native = UAVBaseStationEnv(n_uavs=n, n_users=50, max_steps=20, seed=31)
    native.reset(seed=31)
    fleet.reset(seed=31)
    native.user_positions[:] = fleet.user_positions
    native.uav_positions[:] = fleet.uav_positions
    native._begin_path_loss_step()
    native._update_channel_state()
    _rng_equal(native.np_random.get_state(), fleet.np_random.get_state())
    for tick in range(3):
        actions = {a: np.asarray([.137 * (i+1), -.2, .3], dtype=np.float32)
                   for i, a in enumerate(fleet.agents)}
        observed = fleet.set_transmitter_mask(np.ones(n, dtype=bool))
        for a in observed:
            np.testing.assert_array_equal(observed[a]["obs"], native._get_observation(a)["obs"])
        actual, expected = fleet.step(actions), native.step(actions)
        np.testing.assert_array_equal(fleet.uav_positions, native.uav_positions)
        np.testing.assert_array_equal(fleet.sinr_matrix, native.sinr_matrix)
        np.testing.assert_array_equal(fleet.connections, native.connections)
        for a in fleet.agents:
            np.testing.assert_array_equal(actual[0][a]["obs"], expected[0][a]["obs"])
            assert actual[1][a] == expected[1][a]
        _rng_equal(native.np_random.get_state(), fleet.np_random.get_state())


def test_muting_visibility_motion_height_reward_and_reset(make_fleet):
    fleet = make_fleet()
    before_rng = fleet.np_random.get_state()
    generation = fleet._path_loss_cache_generation
    loss = fleet._uav_user_path_loss_matrix.copy()
    all_on_sinr = fleet.sinr_matrix.copy()
    observations = fleet.set_transmitter_mask(host.mask_bits(1, 4))
    assert fleet._path_loss_cache_generation == generation
    np.testing.assert_array_equal(loss, fleet._uav_user_path_loss_matrix)
    assert np.all(fleet.sinr_matrix[0] >= all_on_sinr[0])
    assert np.isneginf(fleet.sinr_matrix[1:]).all()
    assert not fleet.connections[1:].any()
    assert fleet.connections[0].sum() == 10
    assert not (fleet.sinr_matrix[1:] >= 0).any()
    assert np.isneginf(fleet.uav_sinr_matrix[1:]).all()
    for member in range(4):
        assert fleet._local_uav_entries(member)[0].size == 0
    for member in range(1, 4):
        assert fleet._local_user_entries(member)[0].size == 0
        assert not observations[f"uav_{member}"]["obs"][3:-1].any()
    _rng_equal(before_rng, fleet.np_random.get_state())
    positions = fleet.uav_positions.copy()
    actions = {a: np.ones(3, dtype=np.float32) for a in fleet.agents}
    _, rewards, _, _, _ = fleet.step(actions)
    np.testing.assert_array_equal(fleet.uav_positions, control.predict_next(positions, np.ones((4, 3), np.float32)))
    assert fleet.reward_info["energy_penalty"] == (fleet.uav_positions[:, 2].mean() - 50) / 100 * .1
    assert rewards["uav_3"] == fleet._compute_reward() / 4
    fleet.reset()
    assert fleet.transmitter_mask.all()


@pytest.mark.parametrize("n", [4, 8])
def test_score_every_mask_exact_native_oracle(make_fleet, n):
    fleet = make_fleet(n)
    adapter = CountAdapter(ParallelToArrayAdapter(fleet))
    positions, users = control.decode_public_state(adapter._count_state(), n)
    fleet.uav_positions[:] = positions
    fleet.user_positions[:] = users
    fleet._begin_path_loss_step()
    fleet._update_channel_state()
    masks = list(range(1, 1 << n))
    scores = control.public_scores(users, positions, masks)
    for mask, score in zip(masks, scores):
        fleet.set_transmitter_mask(host.mask_bits(mask, n))
        assert score == _oracle(users, positions, mask)
        assert score["J"] == fleet._compute_reward()
        assert score["served"] == int(fleet.connections.sum())
    selected, trace = control.choose_mask(users, positions, (1 << n) - 1)
    expected = max(masks, key=lambda m: (scores[m-1]["J"], scores[m-1]["served"],
                                         m == (1 << n) - 1, -m))
    assert selected == expected
    assert trace["requested_candidates"] == trace["scored_candidates"] == len(masks)
    assert trace["geometry_rows_computed"] == n


def test_score_batch_random_boundary_and_duplicates():
    rng = np.random.RandomState(31)
    users = rng.uniform(0, 1000, (50, 2))
    positions = rng.uniform(0, 1000, (12, 8, 3))
    positions[:, :, 2] = rng.uniform(50, 150, (12, 8))
    positions[0, :, :2] = 0
    positions[1, :, :2] = 1000
    masks = [1, 255, 2, 3, 17, 127, 128, 15, 16, 31, 63, 254]
    for team, mask, score in zip(positions, masks, control.public_scores(users, positions, masks)):
        assert score == _oracle(users, team, mask)
    scorer = control._Scores(users)
    scorer.score(np.repeat(positions[:1], 3, axis=0), [1, 1, 1])
    assert scorer.counts["requested_candidates"] == 3
    assert scorer.counts["scored_candidates"] == 1
    assert scorer.counts["cached_candidates"] == 2
    scorer.score(positions[0], [1])
    assert scorer.counts["cached_candidates"] == 3


def test_exact_ties_mask_old_then_integer(monkeypatch):
    def tied(loss, positions, active):
        return [dict(J=0., served=0, quality=0., energy_penalty=0.) for _ in positions]
    monkeypatch.setattr(control, "_score_batch", tied)
    positions = np.tile([500., 500., 100.], (4, 1))
    assert control.choose_mask(np.zeros((50, 2)), positions, 12)[0] == 12
    # Give oldmask lower service on a J tie: smallest maximally served mask wins.
    def service_tie(loss, positions, active):
        return [dict(J=0., served=0 if host.mask_integer(a) == 12 else 1,
                     quality=0., energy_penalty=0.) for a in active]
    monkeypatch.setattr(control, "_score_batch", service_tie)
    assert control.choose_mask(np.zeros((50, 2)), positions, 12)[0] == 1


def test_native_float32_action_arithmetic_and_diagonal():
    positions = np.asarray([[995., 1., 149.], [100., 100., 100.]])
    commands = np.asarray([[1., -1., 1.], [.137, .137, .137]], dtype=np.float32)
    expected = positions.copy()
    for i, action in enumerate(commands):
        expected[i] += (action * 30) * 1.0
        expected[i] = np.clip(expected[i], [0, 0, 50], [1000, 1000, 150])
    np.testing.assert_array_equal(control.predict_next(positions, commands), expected)
    diagonal = control.predict_next(np.full((4, 3), 100.), np.ones((4, 3), np.float32))
    np.testing.assert_array_equal(diagonal, np.full((4, 3), 130.))
    assert np.linalg.norm(diagonal[0] - 100) == np.sqrt(2700)


def test_decode_anchor_clock_and_propagation(make_fleet):
    fleet = make_fleet()
    adapter = CountAdapter(ParallelToArrayAdapter(fleet))
    state = adapter._count_state()
    positions, users = control.decode_public_state(state, 4)
    assert positions.dtype == users.dtype == np.float64
    assert np.any(positions != fleet.uav_positions)
    policy = control.OrdinaryController(4)
    action, predicted, trace = policy.select(0, state, 15)
    assert trace["anchored"] and trace["motion_mask"] == 15
    np.testing.assert_array_equal(predicted, control.predict_next(positions, action))
    with pytest.raises(ValueError, match="forbidden"):
        policy.select(1, state, 15)
    # Hidden environment fields are never supplied between boundaries.
    prior = predicted.copy()
    for tick in range(1, 10):
        action, predicted, trace = policy.select(tick, None, 1)
        assert not trace["anchored"]
        assert trace["member_order"] == [(tick+j) % 4 for j in range(4)]
        np.testing.assert_array_equal(predicted, control.predict_next(prior, action))
        prior = predicted.copy()
    with pytest.raises(ValueError, match="requires"):
        policy.select(10, None, 1)
    action, predicted, _ = policy.select(10, state, 1)
    np.testing.assert_array_equal(predicted, control.predict_next(positions, action))


@pytest.mark.parametrize("n,oldmask", [(4, 15), (4, 1), (8, 255), (8, 1)])
def test_motion_one_pass_matches_independent_scalar_enumeration(make_fleet, n, oldmask):
    adapter = CountAdapter(ParallelToArrayAdapter(make_fleet(n)))
    state = adapter._count_state()
    base, users = control.decode_public_state(state, n)
    chosen = np.zeros((n, 3), dtype=np.float32)
    commands = np.asarray(list(product((-1, 0, 1), repeat=3)), dtype=np.float32)
    for member in range(n):
        entering = chosen[member].copy()
        candidates = []
        for index, command in enumerate(commands):
            trial = chosen.copy()
            trial[member] = command
            predicted = control.predict_next(base, trial)
            score = _oracle(users, predicted, oldmask)
            movement = sum(np.linalg.norm(row) for row in predicted - base)
            candidates.append((score["J"], score["served"], -movement,
                               np.array_equal(command, entering), -index))
        chosen[member] = commands[max(range(27), key=lambda i: candidates[i])]
    actual, prediction, trace = control.OrdinaryController(n).select(0, state, oldmask)
    np.testing.assert_array_equal(actual, chosen)
    np.testing.assert_array_equal(prediction, control.predict_next(base, chosen))
    assert trace["requested_candidates"] == n * 27
    assert trace["scored_candidates"] + trace["cached_candidates"] == n * 27
    assert trace["motion_mask"] == oldmask
    assert len(trace["choices"][0]["score_digest"]) == 64
    json.dumps(trace, allow_nan=False)


def test_keep_issued_command_after_boundary_clipping(monkeypatch):
    monkeypatch.setattr(control, "_score_batch", lambda loss, positions, active:
        [dict(J=0., served=0, quality=0., energy_penalty=0.) for _ in positions])
    state = np.zeros(133, dtype=np.float32)
    state[:24].reshape(8, 3)[:4] = [1., 0., 1.]
    state[24:28] = 1
    policy = control.OrdinaryController(4)
    policy.commands[:] = [1., -1., 1.]
    issued, prediction, _ = policy.select(0, state, 15)
    np.testing.assert_array_equal(issued, np.tile([1., -1., 1.], (4, 1)))
    np.testing.assert_array_equal(prediction, np.tile([1000., 0., 150.], (4, 1)))
    issued_again, _, _ = policy.select(1, None, 15)
    np.testing.assert_array_equal(issued_again, issued)


def test_world_streams_immutable_without_study_world_exposure(monkeypatch):
    monkeypatch.setattr(host, "WORLD_IDS", (7,))
    before = np.random.get_state()
    fixture = host.world(7)
    expected_seed = int(np.random.SeedSequence([260930, 14, 7, 1]).generate_state(1)[0])
    assert fixture.user_seed == expected_seed
    uav_seed = int(np.random.SeedSequence([260930, 14, 7, 2]).generate_state(1)[0])
    assert fixture.uav_seed == uav_seed
    np.testing.assert_array_equal(fixture.user_positions,
                                  np.random.RandomState(expected_seed).uniform(0, 1000, (50, 2)))
    unit = np.random.RandomState(uav_seed).uniform(0, 1, (8, 3))
    expected_uavs = unit * [1000, 1000, 100] + [0, 0, 50]
    np.testing.assert_array_equal(fixture.uav_positions, expected_uavs)
    assert host.runtime_seed(7, 4) == int(np.random.SeedSequence(
        [260930, 14, 7, 3, 4]).generate_state(1)[0])
    assert host.runtime_seed(7, 4) != host.runtime_seed(7, 8)
    assert not fixture.user_positions.flags.writeable
    assert not fixture.uav_positions.flags.writeable
    np.testing.assert_array_equal(host.world(7).uav_positions, fixture.uav_positions)
    _rng_equal(before, np.random.get_state())
    with pytest.raises(ValueError):
        fixture.uav_positions[0, 0] = 0
