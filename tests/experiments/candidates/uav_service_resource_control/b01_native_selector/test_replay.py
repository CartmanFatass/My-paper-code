"""Complete-reader wiring with fake effects and pure recorded-menu arithmetic.

No native, nominal, RF, public-law or Adam calls. Each wiring fixture is only
two primitive fake proposals, not another full scientific mock controller stream.
"""
from itertools import combinations
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_service_resource_control.b01_native_selector import replay
from experiments.candidates.uav_service_resource_control.b01_native_selector.contract import (
    diagnostic_bytes, expected_counts,
)
from experiments.candidates.uav_service_resource_control.b01_native_selector.controller import CHOICE_DTYPE
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.trace import CANDIDATE_DTYPE

FAKE_PROTOCOL_PROPOSALS = 0


def choice():
    result = np.zeros((), CHOICE_DTYPE)
    result["completed"] = result["features_available"] = True
    result["previous_targets"] = np.nan
    result["previous_requested_action"] = -1
    return result


class FakeLearner:
    def __init__(self, updates=0):
        self.updates = updates
        self.starts = []
        self.events = []

    def counts(self):
        return dict(updates=self.updates)

    def digests(self):
        return dict(online=str(self.updates), target="0", optimizer=str(self.updates))

    def start_episode(self, index, training):
        self.starts.append((index, training))
        self.training = training
        self.rewards = []
        self.ends = []
        self.update_rows = []

    def decide(self, features, h_eligible, step):
        self.events.append(("decide", step, self.updates))
        assert features.shape == (327,) and not h_eligible
        return dict(action=0, epsilon=1. if self.training else 0., updates=self.updates)

    def observe_reward(self, value, terminal):
        self.events.append(("reward", value, terminal))
        self.rewards.append(value)
        self.ends.append(terminal)
        if terminal and self.training:
            self.updates += 1
            self.update_rows.append(self.updates)

    def episode_arrays(self):
        return dict(action_action=np.array([0], np.int64), reward_native_J=np.asarray(self.rewards, np.float64),
                    reward_terminal=np.asarray(self.ends, bool), update_number=np.asarray(self.update_rows, np.int64))


@pytest.fixture
def wiring(monkeypatch):
    """Mock every effect-bearing construction/check, keeping orchestration real."""
    def setup(program="C", phase="audit", initial_updates=0):
        n = 2
        raw = dict(observations=np.zeros((n + 1, 8, 365), np.float32),
                   proposed=np.zeros((n, 8, 4), np.float32),
                   submitted=np.zeros((n, 8, 4), np.float32),
                   target_xy=np.zeros((n, 8, 2), np.float64),
                   decision_targets_xyz=np.tile([0., 0., 100.], (n, 8, 1)),
                   plan_step=np.array([0], np.int32), candidate_records=np.empty(0, CANDIDATE_DTYPE),
                   native_reward=np.array([.1, .2], np.float64), reward=np.array([.1, .2], np.float64),
                   metrics=np.zeros((n, 1)), ends=np.array([[False, False], [False, True]]),
                   native_ends=np.array([[False, False], [False, True]]))
        raw["observations"][1, 0, 0] = 1
        raw["observations"][2, 0, 0] = 2
        modes = np.zeros((n, 8), bool)
        modes[0, 0] = True
        raw.update(mode=modes, entered=modes.copy(), exited=modes[::-1].copy(),
                   return_margin=np.full((n, 8), .1), nearest_station=np.zeros((n, 8), np.int64),
                   nearest_station_distance_m=np.zeros((n, 8)), own_xyz=np.zeros((n, 8, 3)),
                   dock_bit=np.zeros((n, 8), bool), station_occupancy=np.zeros((n, 2), np.int64),
                   station_queue=np.zeros((n, 2), np.int64), charging=np.zeros((n, 8), bool),
                   waiting_steps=np.zeros((n, 8), np.int64), battery=np.ones((n, 8)))
        if program != "C":
            raw["trace_dummy"] = np.arange(n, dtype=np.int64)
        if program not in ("C", "H_T"):
            raw["choice_records"] = np.asarray([choice()], CHOICE_DTYPE)
        learned = program == "SELECTOR"
        agent = FakeLearner(initial_updates) if learned else None
        diagnostics = ([dict(action=0, epsilon=1. if phase == "train" else 0., updates=initial_updates)]
                       if learned else [dict(action=0)] if program not in ("C", "H_T") else [])
        raw["choice_diagnostics_json"] = diagnostic_bytes(diagnostics)
        updates = initial_updates + int(learned and phase == "train")
        row = dict(program=program, phase=phase, actual_length=n, limit=3000, status="completed",
                   seed=40039001, episode_index=16, job_key="mock/one", policy_counts=expected_counts(program, n),
                   total_native_J=.1 + .2, independent_metric=3.)
        if learned:
            raw.update(learn_action_action=np.array([0], np.int64), learn_reward_native_J=raw["native_reward"].copy(),
                       learn_reward_terminal=np.array([False, True]),
                       learn_update_number=np.array([updates] if phase == "train" else [], np.int64))
            row.update(learner_counts=dict(updates=updates),
                       learner_digests=dict(online=str(updates), target="0", optimizer=str(updates)))
        controllers, calls = [], []

        class Controller:
            def __init__(self, chooser):
                self.chooser = chooser
                self.heuristic = SimpleNamespace(calls=0, targets_xy=np.zeros((8, 2)))
                self.targets_xy = self.heuristic.targets_xy
                self.choice_diagnostics = []
                self.closed = False
                self.read_truth = False

            def reset(self):
                self.heuristic.calls = 0
                self.counters = dict(proposals=0, plans=0, canonicalizations=0, associations=0)
                self.choice_diagnostics = []

            def propose(self, obs, state, step, previous_done, prior_modes):
                global FAKE_PROTOCOL_PROPOSALS
                FAKE_PROTOCOL_PROPOSALS += 1
                assert self.replay_prefix is raw["candidate_records"]
                if program not in ("C", "H_T"):
                    assert self.replay_choice_prefix is raw["choice_records"]
                if self.read_truth:
                    state.secret
                assert bool(previous_done[0]) == (step == 0)
                np.testing.assert_array_equal(prior_modes, np.zeros(8, bool) if step == 0 else raw["mode"][step - 1])
                self.counters["proposals"] += 1
                if program != "C":
                    self.counters["associations"] += 1
                    self.counters["canonicalizations"] += 1
                if step == 0:
                    self.counters["plans"] += 1
                    self.counters["canonicalizations"] += 1
                    if program not in ("C", "H_T"):
                        self.choice_diagnostics.append(self.chooser(np.zeros(327, np.float32), False, 0)
                                                      if self.chooser else dict(action=0))
                self.heuristic.calls += 1
                calls.append(("propose", step))
                return np.zeros((8, 4), np.float32)

            @property
            def last_trace(self):
                return dict(step=self.heuristic.calls - 1, replanned=self.heuristic.calls == 1)

            def audit_arrays(self):
                result = dict(candidate_records=np.empty(0, CANDIDATE_DTYPE))
                if program not in ("C", "H_T"):
                    result["choice_records"] = np.asarray([choice()], CHOICE_DTYPE)
                return result

            def close(self):
                self.closed = True

        def factory(actual_program, **kwargs):
            assert actual_program == program
            controller = Controller(kwargs["chooser"])
            controllers.append(controller)
            return controller

        def feedback(obs, proposal, prior, params):
            tick = int(obs[0, 0])
            calls.append(("feedback", tick))
            return SimpleNamespace(submitted_actions=proposal.copy(), modes=raw["mode"][tick].copy(),
                                   entered=raw["entered"][tick], exited=raw["exited"][tick],
                                   margins=raw["return_margin"][tick], selected_stations=raw["nearest_station"][tick],
                                   station_distances_m=raw["nearest_station_distance_m"][tick])

        def native(actual_raw, actual_row, actual_phase):
            assert actual_raw is raw and actual_row is row and actual_phase == phase
            calls.append(("native_arithmetic", phase))
            assert not actual_raw["native_ends"][:-1].any() and actual_raw["native_ends"][-1].any()
            return dict(native_transitions_checked=n, full_rf_resimulation=False, new_native_steps=0)

        monkeypatch.setattr(replay, "make_controller", factory)
        monkeypatch.setattr(replay, "apply_feedback_params", feedback)
        monkeypatch.setattr(replay, "check_native", native)
        monkeypatch.setattr(replay, "_check_assignment_menu", lambda *args: None)
        monkeypatch.setattr(replay, "_check_choices", lambda actual_raw, *args: actual_raw.get("choice_records", np.empty(0, CHOICE_DTYPE)))
        monkeypatch.setattr(replay, "own_positions", lambda obs: np.zeros((8, 3)))
        monkeypatch.setattr(replay, "own_energy", lambda obs: dict(charging=np.zeros(8, bool), waiting_steps=np.zeros(8, np.int64), battery=np.ones(8)))
        monkeypatch.setattr(replay, "station_counts", lambda *args: np.zeros(2, np.int64))
        monkeypatch.setattr(replay, "plan_record", lambda controller, tick: dict(plan_step=np.int32(tick)))
        monkeypatch.setattr(replay, "memory_record", lambda trace: dict(trace_dummy=np.int64(trace["step"])))
        monkeypatch.setattr(replay, "world_row", lambda seed, rewards, *args, **kwargs: dict(total_native_J=float(sum(rewards))))
        monkeypatch.setattr(replay, "mechanism_row", lambda *args: {})
        monkeypatch.setattr(replay, "position_diagnostics", lambda *args, **kwargs: {})
        monkeypatch.setattr(replay, "absolute_station_xy", lambda obs: np.zeros((2, 2)))
        monkeypatch.setattr(replay, "episode_metrics", lambda actual_raw: dict(independent_metric=3.))
        return SimpleNamespace(raw=raw, row=row, learner=agent, controllers=controllers, calls=calls)

    return setup


def test_canonical_complete_replay_has_one_act_feedback_and_no_terminal_plan(wiring):
    fixture = wiring()
    result = replay.replay_episode(fixture.raw, fixture.row)
    assert result["success"] and result["new_native_steps"] == 0
    assert result["verified_actual_proposals"] == result["verified_feedback_calls"] == 2
    assert result["plans_checked"] == 1 and result["candidate_records_checked"] == 0
    assert result["verification_optimizer_updates"] == result["replay_presentations"] == 0
    assert result["native_arithmetic"]["native_transitions_checked"] == 2
    assert result["raw_array_checksums"].keys() == fixture.raw.keys()
    assert fixture.calls == [("native_arithmetic", "audit"), ("propose", 0), ("feedback", 0), ("propose", 1), ("feedback", 1)]
    assert fixture.controllers[0].closed


def test_persistent_training_learner_is_not_reset_and_partial_terminal_updates(wiring):
    fixture = wiring("SELECTOR", "train", initial_updates=7)
    result = replay.replay_episode(fixture.raw, fixture.row, learner=fixture.learner)
    assert fixture.learner.starts == [(16, True)]
    assert fixture.learner.events == [("decide", 0, 7), ("reward", .1, False), ("reward", .2, True)]
    assert result["verification_optimizer_updates"] == 1 and result["replay_presentations"] == 64
    assert result["learner_counts"] == dict(updates=8)
    assert result["choices_checked"] == 1 and fixture.controllers[0].closed


def test_fixed_final_no_optimizer_and_canonical_diagnostic_comparison(wiring):
    fixture = wiring("SELECTOR", "final", initial_updates=7)
    result = replay.replay_episode(fixture.raw, fixture.row, learner=fixture.learner)
    assert fixture.learner.starts == [(16, False)]
    assert result["verification_optimizer_updates"] == result["replay_presentations"] == 0
    assert result["learner_digests"]["online"] == "7"
    fixture.raw["choice_diagnostics_json"] = diagnostic_bytes([dict(action=1)])
    with pytest.raises(AssertionError, match="choice diagnostics"):
        replay.replay_episode(fixture.raw, fixture.row, learner=fixture.learner)


@pytest.mark.parametrize("kind", ["learner_array", "learner_digest", "policy_count", "plan_extra", "native_metric", "proposed"])
def test_mutations_refuse_complete_read_without_retry(wiring, kind):
    fixture = wiring("SELECTOR", "train")
    if kind == "learner_array":
        fixture.raw["learn_action_action"][0] = 1
    elif kind == "learner_digest":
        fixture.row["learner_digests"]["online"] = "wrong"
    elif kind == "policy_count":
        fixture.row["policy_counts"]["proposals"] = 999
    elif kind == "plan_extra":
        fixture.raw["plan_unrecognized"] = np.array([0])
    elif kind == "native_metric":
        fixture.row["independent_metric"] = -1000
    else:
        fixture.raw["proposed"][0, 0, 0] = .5
    with pytest.raises(AssertionError):
        replay.replay_episode(fixture.raw, fixture.row, learner=fixture.learner)
    assert len(fixture.controllers) <= 1
    if fixture.controllers:
        assert fixture.controllers[0].closed


def test_first_effect_failure_and_budget_stop_propagate_and_close(wiring, monkeypatch):
    fixture = wiring()
    def feedback(*unused):
        raise RuntimeError("first feedback failure")
    monkeypatch.setattr(replay, "apply_feedback_params", feedback)
    with pytest.raises(RuntimeError, match="first feedback failure"):
        replay.replay_episode(fixture.raw, fixture.row)
    assert fixture.controllers[0].closed and fixture.controllers[0].heuristic.calls == 1
    fixture = wiring()
    def stop():
        if fixture.controllers:
            raise RuntimeError("budget stop before next costly section")
    with pytest.raises(RuntimeError, match="budget stop"):
        replay.replay_episode(fixture.raw, fixture.row, stop_check=stop)
    assert fixture.controllers[0].closed and fixture.controllers[0].heuristic.calls == 0


def test_central_truth_poison_is_passed_to_real_policy_boundary(wiring, monkeypatch):
    fixture = wiring()
    factory = replay.make_controller
    def poisoning_factory(*args, **kwargs):
        controller = factory(*args, **kwargs)
        controller.read_truth = True
        return controller
    monkeypatch.setattr(replay, "make_controller", poisoning_factory)
    with pytest.raises(AssertionError, match="central-state access"):
        replay.replay_episode(fixture.raw, fixture.row)
    assert fixture.controllers[0].closed


def test_partial_and_early_continuation_are_rejected_before_controller(wiring):
    fixture = wiring()
    fixture.row["status"] = "failed"
    with pytest.raises(AssertionError, match="partial prefixes"):
        replay.replay_episode(fixture.raw, fixture.row)
    assert not fixture.controllers
    fixture.row["status"] = "completed"
    fixture.raw["native_ends"][0, 0] = True
    with pytest.raises(AssertionError):
        replay.replay_episode(fixture.raw, fixture.row)
    assert not fixture.controllers


def menu_fixture(scores=(1., 2., 2., 0.), travel=(100., 50., 25., 1.), alias=False):
    ordinary = np.full((8, 2), np.nan)
    ordinary[:3] = [[10., 0.], [20., 0.], [30., 0.]]
    if alias:
        ordinary[1] = ordinary[0]
    records = np.zeros(4, CANDIDATE_DTYPE)
    pairs = [(-1, -1)] + list(combinations(range(3), 2))
    winner = 0 if scores[0] == max(scores) else min((i for i, s in enumerate(scores) if s == max(scores)), key=lambda i: (travel[i], i))
    incumbent = -np.inf
    for index, pair in enumerate(pairs):
        candidate = ordinary.copy()
        if index:
            candidate[list(pair)] = candidate[list(pair[::-1])]
        row = records[index]
        row["index"], row["pair_left"], row["pair_right"] = index, pair[0], pair[1]
        row["targets"] = np.column_stack((candidate, np.full(8, 100.)))
        row["alias_base"] = bool(index and np.array_equal(candidate, ordinary, equal_nan=True))
        row["hold_xy"] = np.isnan(ordinary).all(axis=1)
        row["q"] = 1
        row["ticks"] = row["ticks_started"] = 30
        row["rf_completed"] = row["rf_started"] = 3
        row["completed"] = True
        row["score"], row["forecast_travel"] = scores[index], travel[index]
        row["qos"][0] = scores[index] / 10
        row["selected"] = index == winner
        if scores[index] > incumbent:
            row["accepted"] = True
            incumbent = scores[index]
    role = np.zeros(8, np.int8)
    role[:3] = 2
    call = np.zeros(8, np.int8)
    call[:3] = 1
    columns = np.full(8, -1, np.int16)
    columns[:3] = np.arange(3)
    users = np.full((1, 30, 2), np.nan)
    users[0, 0] = [10., 10.]
    prediction = np.full((1, 3, 30, 2), np.nan)
    prediction[0, :, 0] = users[0, 0]
    raw = dict(candidate_records=records, plan_step=np.array([0], np.int32),
               plan_assignment_role=role[None], plan_assignment_call=call[None], plan_assignment_column=columns[None],
               plan_ordinary_targets=ordinary[None], mode=np.zeros((2, 8), bool), plan_eligible=(role == 2)[None],
               plan_priority_count=np.array([3]), plan_priority=ordinary[None], plan_ring_count=np.array([0]),
               plan_ring=np.full((1, 8, 2), np.nan), plan_relay_count=np.array([0]), plan_candidate_first=np.array([0]),
               plan_bs=np.array([[0., 0.]]), plan_fallback=np.array([0]), plan_user_count=np.array([1]),
               trace_current_count=np.array([1, 1]), plan_users=users, trace_canonical=np.repeat(users, 2, axis=0),
               plan_candidate_count=np.array([4]), plan_selected_candidate=np.array([winner]),
               plan_selected_pair=np.array([pairs[winner]], np.int8), plan_targets=records[winner]["targets"][None, :, :2],
               plan_prediction_xy=prediction)
    return raw


@pytest.mark.parametrize("scores,travel,winner", [
    ((1., 2., 2., 0.), (100., 50., 25., 1.), 2),
    ((2., 2., 2., 0.), (100., 50., 25., 1.), 0),
    ((1., 2., 2., 0.), (100., 25., 25., 1.), 1),
    ((1., 2., 2., 0.), (100., 25., np.nextafter(25., 0.), 1.), 2),
    ((1., 2., np.nextafter(2., np.inf), 0.), (100., 1., 50., 1.), 2),
])
def test_independent_literal_ht_menu_without_model_calls(scores, travel, winner):
    raw = menu_fixture(scores, travel)
    replay.validate_candidate_records(raw, "H_A", True)
    replay._check_assignment_menu(raw, "H_T", np.empty(0, CHOICE_DTYPE))
    assert raw["plan_selected_candidate"].tolist() == [winner]
    if winner:
        raw["plan_selected_candidate"][0] = 0
        with pytest.raises(AssertionError, match="H_T"):
            replay._check_assignment_menu(raw, "H_T", np.empty(0, CHOICE_DTYPE))


def test_candidate_menu_rejects_unpurchased_c_work_and_reordered_pairs():
    raw = menu_fixture()
    with pytest.raises(AssertionError, match="C-selected"):
        replay._check_assignment_menu(raw, "C", np.empty(0, CHOICE_DTYPE))
    raw["candidate_records"][1]["pair_left"] = 2
    with pytest.raises(AssertionError, match="lexicographic"):
        replay._check_assignment_menu(raw, "H_T", np.empty(0, CHOICE_DTYPE))


def test_selected_coordinate_alias_remains_actual_h_query_menu():
    raw = menu_fixture(scores=(1., 2., 0., 0.), alias=True)
    replay._check_assignment_menu(raw, "H_T", np.empty(0, CHOICE_DTYPE))
    assert raw["candidate_records"][1]["alias_base"]
    assert raw["candidate_records"][1]["selected"]
    np.testing.assert_array_equal(raw["plan_targets"], raw["plan_ordinary_targets"])


def test_choice_history_uses_actual_committed_previous_targets():
    rows = np.asarray([choice(), choice()], CHOICE_DTYPE)
    rows[1]["step"] = 30
    rows[1]["has_previous_choice"] = True
    rows[1]["previous_requested_action"] = 0
    rows[1]["previous_same_choice_count"] = 1
    rows[1]["previous_targets"] = 1.
    raw = dict(choice_records=rows, plan_targets=np.ones((2, 8, 2)))
    replay._check_choices(raw, "forced_C", 31)
    raw["choice_records"][1]["previous_targets"] = 0.
    with pytest.raises(AssertionError, match="previous committed"):
        replay._check_choices(raw, "forced_C", 31)


def test_diagnostic_encoding_is_recursive_finite_canonical_uint8():
    first = diagnostic_bytes(dict(q=np.array([np.nan, 1.], np.float32), action=np.int64(0)))
    second = diagnostic_bytes(dict(action=0, q=[None, 1.]))
    np.testing.assert_array_equal(first, second)
    assert first.dtype == np.uint8
