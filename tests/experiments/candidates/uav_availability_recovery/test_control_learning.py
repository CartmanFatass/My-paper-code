import json

import numpy as np
import pytest
import torch

from experiments.candidates.uav_availability_recovery.control import FEATURE_DIM, RecoveryControl
from experiments.candidates.uav_availability_recovery.learning import (
    EVAL_IDS, FIT_SEEDS, MacroTransition, Policy, episode_gae, parameter_vector, ppo_update,
    training_world_ids,
)
from experiments.candidates.uav_availability_recovery.runner import run_episode, write_episode
from ha_ctse_process.uav_episode_schema import Cell
from ha_ctse_process.uav_g0_environment import UAVSourceIdentifiabilityEnv
from ha_ctse_process.uav_g0_geometry import make_episode_source


@pytest.fixture(scope="module")
def source():
    return make_episode_source(91723)


class HoldPolicy:
    def choose(self, feature, **kwargs):
        assert feature.shape == (FEATURE_DIM,)
        return 15, 0.0, 0.0, 0.0


@pytest.fixture(scope="module")
def complete_paths(source):
    return {arm: run_episode(source, arm=arm, policy=HoldPolicy() if arm == "L" else None)
            for arm in ("S", "L", "P")}


def test_complete_native_boundary_reward_and_prefix(source, complete_paths):
    onset, rejoin = source.event.onset, source.event.rejoin
    expected_decisions = sorted({onset, rejoin, *range(((onset+9)//10)*10, 500, 10)})
    for arm, (metrics, arrays, transitions) in complete_paths.items():
        assert metrics["steps"] == 500
        assert metrics["cutoff_events"] == metrics["depletion_events"] == 0
        native = arrays["native_metrics"]
        np.testing.assert_allclose(native[:, 0], native[:, 5]+native[:, 2], atol=1e-12)
        potential_next = native[:, 4].copy()
        potential_next[-1] = 0
        np.testing.assert_allclose(native[:, 2], .99*potential_next-native[:, 3], atol=1e-12)
        np.testing.assert_allclose(native[:, 1], np.minimum(arrays["user_rates_mbps"], 1).mean(axis=1), atol=1e-12)
        events = json.loads(str(arrays["events_json"]))
        assert [(row["kind"], row["physical_step"]) for row in events] == [("LEAVE", onset), ("REJOIN", rejoin)]
        assert events[1]["previous_handle"] != events[1]["current_handle"]
        assert np.all(arrays["active_mask"][:onset])
        assert np.all(arrays["active_mask"][rejoin:])
        assert np.all(arrays["active_mask"][onset:rejoin].sum(axis=1) == 7)
        if arm != "S":
            assert arrays["decision_step"].tolist() == expected_decisions
            np.testing.assert_array_equal(arrays["requested_actions"][:onset], complete_paths["S"][1]["requested_actions"][:onset])
            np.testing.assert_array_equal(native[:onset], complete_paths["S"][1]["native_metrics"][:onset])
        if arm == "L":
            assert transitions[0].start == onset
            assert transitions[-1].stop == 500
            for row in transitions:
                assert row.reward == pytest.approx(native[row.start:row.stop, 0].sum(), abs=1e-11)
                np.testing.assert_array_equal(arrays["targets"][row.start:row.stop, 6:],
                                              np.broadcast_to(arrays["positions"][row.start, 6:], (row.stop-row.start, 2, 3)))
        if arm == "P":
            predictions = json.loads(str(arrays["predictions_json"]))
            assert metrics["service_snapshot_calls"] == sum(row["snapshot_calls_this_decision"] for row in predictions)
            assert metrics["service_snapshot_calls"] == predictions[-1]["snapshot_calls"]
            assert metrics["service_snapshot_calls"] <= 33*16*4*2
            assert all(row["step"]+max(row["horizons"]) <= 500 for row in predictions)


def test_arrays_retained_without_pickle(tmp_path, complete_paths):
    raw = tmp_path / "raw"
    raw.mkdir()
    row, arrays, _ = complete_paths["P"]
    saved = write_episode(tmp_path, "fixture", dict(row), arrays)
    with np.load(tmp_path / saved["raw"], allow_pickle=False) as restored:
        np.testing.assert_array_equal(restored["native_metrics"], arrays["native_metrics"])
        assert restored["public_user_xy"].dtype == np.float32


def test_independent_saved_episode_reading_and_corruption(complete_paths):
    from experiments.candidates.uav_availability_recovery.read_saved import verify_episode

    for row, arrays, _ in complete_paths.values():
        error, calls = verify_episode(row, arrays)
        assert error <= 1e-9
        assert calls == row["service_snapshot_calls"]
    row, arrays, _ = complete_paths["L"]
    broken = dict(arrays)
    broken["native_metrics"] = arrays["native_metrics"].copy()
    broken["native_metrics"][20, 0] += .001
    with pytest.raises(ValueError, match="native J equation"):
        verify_episode(row, broken)


def test_public_map_features_and_association_alignment(source):
    env = UAVSourceIdentifiabilityEnv(source, Cell.EVENT)
    try:
        env.reset()
        control = RecoveryControl(source, env)
        view = control.view(env, ())
        # Current feature map slice follows geometry and uses the same 240-byte payload as P.
        start = 24+24+8+240+30+30+2+12+12+4
        np.testing.assert_array_equal(view["feature"][start:start+60], control.user_xy.ravel()/8000)
        np.testing.assert_array_equal(view["association"], env.connections)
        assert control.user_xy.nbytes == 240
        assert "source" not in vars(control)
        assert "g0_source" not in vars(control.shadow)
    finally:
        env.close()


def test_shadow_readiness_observes_consecutive_steps(source):
    env = UAVSourceIdentifiabilityEnv(source, Cell.EVENT)
    try:
        env.reset()
        control = RecoveryControl(source, env)
        events = ()
        for t in range(source.event.rejoin+3):
            view = control.view(env, events)
            actions, _ = control.commands(env, view, arm="L", joint_action=15 if view["decision"] else None)
            transition = env.step_dense(actions)
            events = transition.boundary_events
        assert control.shadow._complete_primary_steps >= 1
    finally:
        env.close()


def test_macro_gae_stops_at_finite_horizon():
    feature = np.zeros(FEATURE_DIM, dtype=np.float32)
    rows = [MacroTransition(feature, 0, 0, 2, 180, 187, 7),
            MacroTransition(feature, 0, 0, 3, 187, 500, 11)]
    advantage, returns = episode_gae(rows)
    np.testing.assert_allclose(advantage, [7+3-2+.95*(11-3), 11-3])
    np.testing.assert_allclose(returns, advantage+[2, 3])
    _, undiscounted = episode_gae(rows, lam=1)
    np.testing.assert_allclose(undiscounted, [18, 11])


def test_event_metric_window_matches_inherited_g0():
    from experiments.candidates.uav_availability_recovery.runner import episode_metrics
    from ha_ctse_process.uav_episode_schema import Control
    from ha_ctse_process.uav_g0_statistics import compute_episode_metrics

    service = np.ones(500)
    service[330:340] = .5
    inherited = compute_episode_metrics(service, episode_id=1, control=Control.SAME_INFORMATION,
                                        cell=Cell.EVENT, onset=190, duration=90)
    arrays = {"native_metrics": np.zeros((500, 9)), "weakest_service": service,
              "positions": np.zeros((501, 8, 3)), "joint_action": np.zeros(0, dtype=np.int64),
              "incumbent_action": np.zeros(0, dtype=np.int64), "native_guard_count": np.zeros(500),
              "motion_modified": np.zeros((500, 8), dtype=bool)}
    own = episode_metrics(arrays, world=1, arm="S", onset=190, duration=90, event=True)
    assert own["J_event"] == inherited.j_event
    assert own["event_catastrophe"] == inherited.c_cat == 1
    service[330] = 1
    inherited = compute_episode_metrics(service, episode_id=1, control=Control.SAME_INFORMATION,
                                        cell=Cell.EVENT, onset=190, duration=90)
    own = episode_metrics(arrays, world=1, arm="S", onset=190, duration=90, event=True)
    assert own["event_catastrophe"] == inherited.c_cat == 0


def test_independent_worlds_and_actual_optimizer_updates():
    worlds = [training_world_ids(seed) for seed in FIT_SEEDS]
    assert len(set(world for sequence in worlds for world in sequence)) == 1536
    assert not set(EVAL_IDS).intersection(world for sequence in worlds for world in sequence)
    torch.set_num_threads(1)
    torch.manual_seed(913)
    policy = Policy()
    before = parameter_vector(policy)
    generator = torch.Generator().manual_seed(914)
    episodes = []
    for episode in range(4):
        rows = []
        for index in range(5):
            feature = np.full(FEATURE_DIM, .01*(index+episode), dtype=np.float32)
            action, log_prob, value, _ = policy.choose(feature, generator=generator)
            rows.append(MacroTransition(feature, action, log_prob, value, 180+index*10,
                                       190+index*10, float(index+episode)))
        episodes.append(rows)
    optimizer = torch.optim.Adam(policy.parameters(), lr=3e-4)
    metrics = ppo_update(policy, optimizer, episodes, np.random.default_rng(917))
    assert metrics["optimizer_updates"] == 16
    assert metrics["macro_rows"] == 20
    assert metrics["optimizer_row_exposures"] == 80
    assert torch.linalg.vector_norm(parameter_vector(policy)-before) > 0
    assert {int(state["step"]) for state in optimizer.state.values()} == {16}


def test_missing_admission_precedes_output_creation(tmp_path, monkeypatch):
    from experiments.candidates.uav_availability_recovery import runner
    import scripts.hmasd_admission

    out = tmp_path / "forbidden"
    def rejected(*args, **kwargs):
        raise RuntimeError("no test admission")
    monkeypatch.setattr(scripts.hmasd_admission, "require_admission", rejected)
    monkeypatch.setattr("sys.argv", ["runner", "--out", str(out), "--launch-sha", "0"*40])
    with pytest.raises(RuntimeError, match="no test admission"):
        runner.main()
    assert not out.exists()


def test_runner_matches_launcher_static_guard_contract():
    from pathlib import Path
    from experiments.candidates.uav_availability_recovery import runner
    from scripts.hmasd_launch import _validate_guard_contract

    _validate_guard_contract(Path(runner.__file__), "uav_availability_recovery")
