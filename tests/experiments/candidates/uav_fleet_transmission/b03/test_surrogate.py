"""Pure synthetic checks; no native environment construction or transitions."""

from copy import deepcopy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from envs.pettingzoo import uav_radio
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from experiments.candidates.uav_fleet_transmission.b02 import option
from experiments.candidates.uav_fleet_transmission.b02.controller import Program
from experiments.candidates.uav_fleet_transmission.control import OrdinaryController, decode_public_state
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.b03 import surrogate


def adapter_report(positions, users, t, horizon):
    native = SimpleNamespace(uav_positions=positions, user_positions=users,
                             area_size=1000., height_range=(50., 150.),
                             max_steps=horizon, current_step=t)
    adapter = SimpleNamespace(n_uavs=8, env=SimpleNamespace(env=native))
    return CountAdapter._count_state(adapter)


@pytest.fixture
def fixture():
    rng = np.random.RandomState(71)
    positions = rng.uniform(0, 1000, (8, 3))
    positions[:, 2] = rng.uniform(50, 150, 8)
    users = rng.uniform(0, 1000, (50, 2))
    state = adapter_report(positions, users, 40, 53)
    decoded_positions, decoded_users = decode_public_state(state, 8)
    controller = OrdinaryController(8)
    controller.positions = decoded_positions + [.001, -.001, 0]
    controller.users = decoded_users.copy()
    controller.commands[:] = [1., -1., 0.]
    controller.next_t = 40
    return controller, state, users


def oracle_score(positions, users, mask):
    loss = uav_radio.free_space_user_path_loss(positions, users)
    sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=mask_bits(mask, 8))
    links = uav_radio.greedy_connection_assignment(sinr, 0, 10)
    score = uav_radio.service_metrics(sinr, links, 0)
    height = (positions[:, 2].mean() - 50) / 100 * .1
    return [float(score["J"] - height), int(score["served"]),
            float(score["quality"]), float(height)]


def test_codec_exact_first_cast_and_preserved_user_bits(fixture):
    controller, original, users = fixture
    positions = controller.positions.copy()
    positions.setflags(write=False)
    original.setflags(write=False)
    encoded = surrogate.encode_model_report(positions, original, 50, 53)
    expected = adapter_report(positions, users, 50, 53)
    np.testing.assert_array_equal(encoded, expected)
    np.testing.assert_array_equal(encoded[32:132], original[32:132])
    naive = positions.copy()
    naive[:, :2] /= 1000
    naive[:, 2] = (naive[:, 2]-50) / 100
    assert np.any(encoded[:24] != naive.astype(np.float32).reshape(-1))
    assert not np.shares_memory(encoded, original)
    with pytest.raises(ValueError):
        surrogate.encode_model_report(positions, original.astype(np.float64), 50, 53)


def test_complete_short_tail_history_order_physical_reward_and_counts(fixture):
    controller, state, raw_users = fixture
    result = surrogate.simulate_continuation(controller, state, 173, horizon=53)
    arrays, decisions, summary = result["arrays"], result["decisions"], result["summary"]
    assert arrays["positions"].shape == arrays["controller_estimates"].shape == (14, 8, 3)
    assert arrays["actions"].dtype == np.float32 and arrays["actions"].shape == (13, 8, 3)
    np.testing.assert_array_equal(arrays["controller_estimates"][0], controller.positions)
    physical, model_users = decode_public_state(state, 8)
    np.testing.assert_array_equal(arrays["positions"][0], physical)
    assert np.any(arrays["positions"][0] != arrays["controller_estimates"][0])
    program = Program("C", horizon=53)
    program.controller = deepcopy(controller)
    mask = 173
    totals = [0., 0, 0., 0.]
    path = 0.
    for index, t in enumerate(range(40, 53)):
        report = state.copy() if t == 40 else adapter_report(physical, raw_users, t, 53) if t % 10 == 0 else None
        command, mask, decision = program.select(t, report, mask)
        moved = physical.copy()
        for member in range(8):
            moved[member] += command[member] * 30 * 1.0
            moved[member] = np.clip(moved[member], [0, 0, 50], [1000, 1000, 150])
        reward = oracle_score(moved, model_users, mask)
        np.testing.assert_array_equal(arrays["positions"][index+1], moved)
        np.testing.assert_array_equal(arrays["controller_estimates"][index+1], program.controller.positions)
        np.testing.assert_array_equal(arrays["reward_components"][index], reward)
        np.testing.assert_array_equal(arrays["actions"][index], command)
        assert arrays["masks"][index] == mask
        assert decisions[index] == decision
        assert decision["motion"]["motion_mask"] == decision["old_mask"]
        assert decision["motion"]["member_order"] == [(t+j) % 8 for j in range(8)]
        for column in range(4):
            totals[column] += reward[column]
        path += float(np.linalg.norm(moved-physical, axis=1).sum())
        physical = moved
    assert [summary[k] for k in ("total_J", "total_served", "total_quality", "total_energy_penalty")] == totals
    assert summary["total_path"] == path
    assert summary["model_transitions"] == 13
    assert summary["ordinary_candidate_position_predictions"] == 13*216
    assert summary["controller_counts"]["motion"]["requested_candidates"] == 13*216
    assert summary["controller_counts"]["mask"]["requested_candidates"] == 2*255
    assert summary["reward_counts"]["requested_candidates"] == summary["reward_counts"]["scored_candidates"] == 13
    assert summary["reward_counts"]["cached_candidates"] == 0
    np.testing.assert_array_equal(arrays["report_times"], [40, 50])
    np.testing.assert_array_equal(arrays["reports"][0], state)
    np.testing.assert_array_equal(arrays["reports"][1], adapter_report(arrays["positions"][10], raw_users, 50, 53))
    json.dumps(dict(summary=summary, decisions=decisions), allow_nan=False)


def test_purity_no_alias_and_independent_branches(fixture):
    controller, state, _ = fixture
    before = deepcopy(controller.__dict__)
    original = state.copy()
    rng_before = np.random.get_state()
    first = surrogate.simulate_continuation(controller, state, 173, horizon=41)
    second = surrogate.simulate_continuation(controller, state, 173, horizon=41)
    for name, array in first["arrays"].items():
        np.testing.assert_array_equal(array, second["arrays"][name])
        assert not np.shares_memory(array, state)
        assert not np.shares_memory(array, controller.positions)
    assert first["decisions"] == second["decisions"] and first["summary"] == second["summary"]
    first["arrays"]["positions"][:] = 0
    first["decisions"][0]["t"] = 999
    assert second["decisions"][0]["t"] == 40 and second["arrays"]["positions"].any()
    for name, value in before.items():
        if isinstance(value, np.ndarray):
            np.testing.assert_array_equal(controller.__dict__[name], value)
        else:
            assert controller.__dict__[name] == value
    np.testing.assert_array_equal(state, original)
    rng_after = np.random.get_state()
    assert rng_before[0] == rng_after[0] and rng_before[2:] == rng_after[2:]
    np.testing.assert_array_equal(rng_before[1], rng_after[1])


def test_forced_transit_arrival_zero_resumption_without_replanning(monkeypatch, fixture):
    controller, state, _ = fixture
    positions, _ = decode_public_state(state, 8)
    commands = np.zeros((10, 8, 3), dtype=np.float32)
    commands[:2, 7, 0] = -1
    destination = positions.copy()
    destination[7, 0] = max(0, destination[7, 0]-60)
    plan = dict(initiated=True, member=7, duration=10, arrival_t=50,
                commands=commands.tolist(), predicted_destination=destination.tolist())
    original_plan = deepcopy(plan)
    monkeypatch.setattr(option, "plan_option", lambda *args, **kwargs:
                        pytest.fail("the surrogate must not enumerate R again"))
    result = surrogate.simulate_continuation(controller, state, 127, plan, horizon=53)
    arrays, decisions, summary = result["arrays"], result["decisions"], result["summary"]
    assert plan == original_plan
    assert [d["phase"] for d in decisions] == ["transit"]*10 + ["arrival", "ordinary", "ordinary"]
    np.testing.assert_array_equal(arrays["actions"][:10], commands)
    assert not arrays["actions"][10].any()
    assert (arrays["masks"][:10] == 127).all()
    assert arrays["masks"][10] & 128
    assert decisions[11]["motion"]["member_order"] == [(51+j) % 8 for j in range(8)]
    assert all(choice["entering"] == [0., 0., 0.] for choice in decisions[11]["motion"]["choices"])
    assert summary["controller_counts"]["motion"]["requested_candidates"] == 2*216
    assert summary["controller_counts"]["mask"]["requested_candidates"] == 0
    assert summary["controller_counts"]["arrival"]["requested_candidates"] == 128
    assert summary["controller_counts"]["option"]["requested_candidates"] == 0
    assert summary["reward_counts"]["requested_candidates"] == 13
    assert summary["ordinary_candidate_position_predictions"] == 2*216
    np.testing.assert_array_equal(arrays["controller_estimates"][11],
                                  decode_public_state(arrays["reports"][1], 8)[0])
    assert np.any(arrays["positions"][11] != arrays["controller_estimates"][11])


def test_fresh_reward_scorer_each_tick_and_declined_equivalence(monkeypatch, fixture):
    controller, state, _ = fixture
    instances = []
    original = surrogate._Scores
    class ObservedScores(original):
        def __init__(self, users):
            super().__init__(users)
            instances.append(self)
    monkeypatch.setattr(surrogate, "_Scores", ObservedScores)
    declined = surrogate.simulate_continuation(controller, state, 173,
                                              dict(initiated=False), horizon=43)
    ordinary = surrogate.simulate_continuation(controller, state, 173, horizon=43)
    assert len(instances) == 6 and len({id(s) for s in instances}) == 6
    assert all(s.counts["requested_candidates"] == s.counts["scored_candidates"] == 1 for s in instances)
    for name in declined["arrays"]:
        np.testing.assert_array_equal(declined["arrays"][name], ordinary["arrays"][name])
    assert declined["decisions"] == ordinary["decisions"]


def test_refuses_invalid_history_report_clock_and_plan(fixture):
    controller, state, _ = fixture
    for name, value in (("next_t", 39), ("n_uavs", 4),
                        ("commands", controller.commands.astype(np.float64)),
                        ("commands", np.full((8, 3), .5, dtype=np.float32)),
                        ("positions", np.full((8, 3), np.nan))):
        altered = deepcopy(controller)
        setattr(altered, name, value)
        with pytest.raises(ValueError):
            surrogate.simulate_continuation(altered, state, 173, horizon=41)
    invalid = state.copy()
    invalid[32] = np.nan
    with pytest.raises(ValueError):
        surrogate.simulate_continuation(controller, invalid, 173, horizon=41)
    for horizon in (40, 501, True):
        with pytest.raises(ValueError):
            surrogate.simulate_continuation(controller, state, 173, horizon=horizon)
    for mask in (0, 256):
        with pytest.raises(ValueError):
            surrogate.simulate_continuation(controller, state, mask, horizon=41)
    malformed = dict(initiated=True, duration=10, arrival_t=51, member=7,
                     commands=np.zeros((10, 8, 3)).tolist(), predicted_destination=controller.positions.tolist())
    with pytest.raises(ValueError):
        surrogate.simulate_continuation(controller, state, 127, malformed, horizon=41)
