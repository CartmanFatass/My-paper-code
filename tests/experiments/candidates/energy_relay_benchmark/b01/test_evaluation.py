from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    PRODUCTION_PARAMS,
    FeedbackParams,
    apply_feedback_params,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    VARIANTS,
    LayoutHeuristic,
    UnobservedRegime,
    estimator_kmeans,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import own_positions
from experiments.candidates.uav_service_auxiliary.b01.native import (
    initialization_fingerprint,
    make_env,
    seed_everything,
)
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS
from experiments.candidates.uav_service_auxiliary.b07 import native as b07
from hmasd.agent import HMASDAgent

POLICY_SEED = 925031

VOLATILE = {"wall_seconds", "worker_peak_rss_kib"}


def _assert_b07_parity(ours, arrays, b07_result, steps):
    assert ours["row"]["actual_length"] == steps == len(arrays["episode_0_native_reward"])
    assert np.array_equal(ours["arrays"]["reward"], arrays["episode_0_native_reward"])
    assert np.array_equal(ours["arrays"]["metrics"], arrays["episode_0_metrics"])
    assert np.array_equal(ours["arrays"]["mode"], arrays["episode_0_mode"])
    assert np.array_equal(ours["arrays"]["dock_bit"], arrays["episode_0_submitted_action"][:, :, 3] > 0.5)
    assert np.array_equal(ours["arrays"]["charging"], arrays["episode_0_uav_charging"])
    assert np.array_equal(ours["arrays"]["waiting_steps"], arrays["episode_0_charging_wait_age"])
    np.testing.assert_allclose(ours["arrays"]["battery"], arrays["episode_0_post_legal_battery"], rtol=0, atol=0)
    assert ours["row"]["raw_native_J"] == b07_result["worlds"][0]["raw_native_J"]
    # Mechanism fields are the shield's own decision-time decode (B07 pre-step records).
    mine = ours["arrays"]
    assert np.array_equal(mine["return_margin"], arrays["episode_0_pre_legal_margin"])
    assert np.array_equal(mine["nearest_station"], arrays["episode_0_selected_station"])
    assert np.array_equal(mine["nearest_station_distance_m"],
                          arrays["episode_0_station_distance_m"].astype(np.float32))
    np.testing.assert_allclose(mine["own_xyz"], arrays["episode_0_pre_position_m"], rtol=0, atol=0.01)
    assert mine["own_xyz"].shape == (steps, 8, 3) and "target_xy" not in mine
    assert mine["station_occupancy"].shape == mine["station_queue"].shape == (steps, 2)
    assert np.array_equal(mine["station_occupancy"].sum(axis=1)[1:],
                          mine["charging"].sum(axis=1)[:-1])   # decision time = previous post-step
    assert ours["row"]["controller_information"] == ev.N_CONTROLLER_INFORMATION


# Shield-ON parity: 50 steps at (0.25, 0.45) on 952001 enter but never exit with the fresh
# agent (first exit at step 99, implementation probe), so this variant runs 120 steps.
SHIELD_ON = FeedbackParams(0.25, 0.45)
SHIELD_ON_STEPS = 120


@pytest.mark.parametrize("params,steps", [(PRODUCTION_PARAMS, 50), (SHIELD_ON, SHIELD_ON_STEPS)],
                         ids=["production", "shield_on"])
def test_equals_b07_serial_path_bit_for_bit_at_production_margins(tmp_path, monkeypatch, params, steps):
    """Fresh agent, world 952001: B07 evaluate_panel vs the B01 path at the same margins.

    Production margins use B07 unchanged; the shield-ON variant replaces B07's module-level
    ``apply_feedback`` (called positionally) by the parametrised shield at the same margins."""
    device = torch.device("cpu")
    config = ev.make_eval_config(steps, POLICY_SEED)
    seed_everything(POLICY_SEED, device)
    agent = HMASDAgent(config, log_dir=str(tmp_path / "agent"), device=device)
    checkpoint = tmp_path / "agent.pt"
    agent.save_model(checkpoint)
    threads = torch.get_num_threads()
    task = ev.WorldTask(controller="N", seed=952001, params=params, horizon=steps,
                        policy_seed=POLICY_SEED, threads=threads, checkpoint=str(checkpoint),
                        expected_policy_fingerprint=initialization_fingerprint(agent),
                        log_dir=str(tmp_path))
    ours = ev.evaluate_task(task)
    if params != PRODUCTION_PARAMS:
        monkeypatch.setattr(b07, "apply_feedback",
                            lambda o, a, m: apply_feedback_params(o, a, m, params))
    b07_result, arrays = b07.evaluate_panel(
        agent, config, (952001,), device, policy_seed=POLICY_SEED, mode="F",
        log_dir=tmp_path / "b07", trace_path=tmp_path / "b07.npz")
    _assert_b07_parity(ours, arrays, b07_result, steps)
    assert ours["identity"]["policy_fingerprint"] == initialization_fingerprint(agent)
    if params != PRODUCTION_PARAMS:
        assert ours["arrays"]["mode"].any() and ours["row"]["feedback_exit_count"] >= 1
        assert ours["row"]["feedback_entry_count"] >= 1


def test_parallel_spawn_equals_serial(tmp_path, fresh_checkpoint):
    tasks = [ev.WorldTask(controller="N", seed=seed, params=PRODUCTION_PARAMS, horizon=60,
                          policy_seed=POLICY_SEED, threads=1, checkpoint=str(fresh_checkpoint),
                          log_dir=str(tmp_path)) for seed in (953002, 952001)]
    serial = ev.run_tasks(tasks, workers=1)
    parallel = ev.run_tasks(tasks, workers=2)
    assert [item["row"]["seed"] for item in serial] == [952001, 953002]
    for left, right in zip(serial, parallel, strict=True):
        assert {k: v for k, v in left["row"].items() if k not in VOLATILE} == \
               {k: v for k, v in right["row"].items() if k not in VOLATILE}
        assert left["arrays"].keys() == right["arrays"].keys()
        for key in left["arrays"]:
            assert np.array_equal(left["arrays"][key], right["arrays"][key]), key
        assert left["identity"] == right["identity"]
    traces = ev.trace_arrays(serial)
    assert traces["world_0_reward"].dtype == np.float32 and traces["world_1_mode"].shape == (60, 8)


def test_local_heuristic_world_runs_from_legal_observations(tmp_path):
    task = ev.WorldTask(controller="Hlocal", seed=955001, params=PRODUCTION_PARAMS, horizon=40,
                        policy_seed=POLICY_SEED, threads=1,
                        heuristic=replace(VARIANTS["H1"], information="local"),
                        log_dir=str(tmp_path))
    result = ev.evaluate_task(task)
    row = result["row"]
    assert row["failed"] is False and row["actual_length"] == 40
    assert row["plan_source"] == "legal-observation" and row["plan_input_steps"] == 0
    assert row["controller_information"] == \
        "legal-observation pooled central planner (station-1 ring search prior)"
    assert row["replans"] == 2 and 1 <= row["search_replans"] <= 2
    assert isinstance(row["guard_checked_actions"], int) and row["guard_blocked_actions"] >= 0
    arrays = result["arrays"]
    assert arrays["guard_checked"].shape == (40,)
    assert arrays["target_xy"].shape == (40, 8, 2)
    assert np.isfinite(arrays["target_xy"][0]).all()   # every UAV available at reset
    assert len(row["station_xy"]) == 2 and all(len(xy) == 2 for xy in row["station_xy"])
    assert isinstance(row["mean_nearest_station_distance_m"], float)
    assert row["post_exit_recapture_count"] == len(row["post_exit_recapture_distances_m"])
    traces = ev.trace_arrays([result])
    expected = {"own_xyz": ((40, 8, 3), np.float32), "return_margin": ((40, 8), np.float32),
                "nearest_station": ((40, 8), np.int8),
                "nearest_station_distance_m": ((40, 8), np.float32),
                "guard_checked": ((40,), np.int32), "guard_blocked": ((40,), np.int32),
                "station_occupancy": ((40, 2), np.int8), "station_queue": ((40, 2), np.int8),
                "target_xy": ((40, 8, 2), np.float32)}
    for key, (shape, dtype) in expected.items():
        assert traces[f"world_0_{key}"].shape == shape and traces[f"world_0_{key}"].dtype == dtype, key


def test_unobserved_regime_marks_the_world_failed(tmp_path, monkeypatch):
    def refuse(self, observations, modes, plan_inputs=None):
        raise UnobservedRegime("forced")

    monkeypatch.setattr(LayoutHeuristic, "plan", refuse)
    task = ev.WorldTask(controller="Hlocal", seed=955001, params=PRODUCTION_PARAMS, horizon=10,
                        policy_seed=POLICY_SEED, threads=1,
                        heuristic=replace(VARIANTS["H1"], information="local"),
                        log_dir=str(tmp_path))
    failed = ev.evaluate_task(task)
    assert failed["row"]["failed"] is True and "UnobservedRegime: forced" in failed["row"]["failure"]
    assert failed["arrays"] == {} and failed["row"]["controller"] == "Hlocal"
    monkeypatch.undo()
    ok = ev.evaluate_task(replace(task, seed=955002))
    agg = ev.aggregate([failed["row"], ok["row"]])
    assert agg["worlds"] == 2 and agg["completed_worlds"] == 1 and agg["failed_worlds"] == [955001]
    assert agg["mean_raw_native_J"] == ok["row"]["raw_native_J"]
    traces = ev.trace_arrays([failed, ok])
    assert bool(traces["world_0_failed"]) and traces["world_1_reward"].shape == (10,)
    assert ev.aggregate([failed["row"]])["completed_worlds"] == 0


class RecordingController(ev.HeuristicController):
    def __init__(self, params, env):
        super().__init__(params, env)
        self.records = []

    def propose(self, observations, state, step, previous_done, modes):
        replan = self.heuristic.replans_next()
        truth = ev.central_plan_inputs(self.env)
        actions = super().propose(observations, state, step, previous_done, modes)
        self.records.append({"step": step, "replan": replan, "truth": truth,
                             "plan": self.heuristic.last_plan,
                             "targets": self.heuristic.targets_xy.copy(),
                             "own": own_positions(observations)})
        return actions


def test_central_heuristic_plans_from_ground_truth_and_moves(config_60):
    env = make_env(config_60, 953001)
    try:
        controller = RecordingController(VARIANTS["H1"], env)
        row, arrays = ev.evaluate_world(controller, env, config_60, 953001, PRODUCTION_PARAMS)
    finally:
        env.close()
    assert row["actual_length"] == 60 and controller.plan_input_steps == [0, 30]
    replans = [record for record in controller.records if record["replan"]]
    assert [record["step"] for record in replans] == [0, 30]
    for record in replans:
        plan = record["plan"]
        assert plan["call"] == record["step"] and plan["information"] == "central"
        assert np.array_equal(plan["users"], record["truth"]["users_xy"])
        assert np.array_equal(plan["bs_xy"], record["truth"]["bs_xy"].mean(axis=0))
        centroids, counts = estimator_kmeans(record["truth"]["users_xy"], 6, 30)
        assert np.array_equal(plan["centroids"], centroids)
    # users move between replans, so the second plan uses the positions at step 30
    assert not np.array_equal(replans[0]["plan"]["users"], replans[1]["plan"]["users"])
    first, last = controller.records[0], controller.records[29]
    start = np.linalg.norm(first["own"][:, :2] - first["targets"], axis=1)
    end = np.linalg.norm(last["own"][:, :2] - first["targets"], axis=1)
    assert np.isfinite(first["targets"]).all() and not arrays["mode"][:30].any()
    assert np.all(end < start - 500.0)   # ~29 s at up to 30 m/s toward fixed targets


def test_world_row_definitions():
    length = 6
    rewards = np.arange(length, dtype=np.float64)
    metrics = np.zeros((length, len(TRACE_FIELDS)))
    metrics[:, ev.QOS] = (0.0, 0.5, 0.5, 0.0, 1.0, 0.0)
    metrics[:, ev.CHARGER_INPUT] = 2.0
    metrics[:, ev.BATTERY_MIN] = (0.9, 0.8, 0.3, 0.4, 0.5, 0.6)
    ends = np.zeros((length, 2), dtype=bool)
    ends[-1, 1] = True
    mode = np.zeros((length, 8), dtype=bool)
    mode[2:4, 0] = True
    entered = np.zeros((length, 8), dtype=bool)
    entered[2, 0] = True
    charging = np.zeros((length, 8), dtype=bool)
    charging[1, 1] = True            # one-tick spell
    charging[3:5, 1] = True          # two-tick spell
    charging[5, 2] = True            # right-censored one-tick spell
    waiting = np.zeros((length, 8), dtype=np.int64)
    waiting[4, 3], waiting[5, 3] = 1, 2
    steps = {"mode": mode, "entered": entered, "exited": np.zeros_like(mode),
             "charging": charging, "waiting_steps": waiting,
             "battery": np.full((length, 8), 0.7, np.float32), "dock_bit": mode.copy()}
    steps["guard_checked"] = np.asarray((0, 2, 1, 0, 0, 3))
    steps["guard_blocked"] = np.asarray((0, 1, 0, 0, 0, 2))
    row = ev.world_row(7, rewards, metrics, ends, steps, time_step_s=1.0)
    assert not [key for key in row if "presen" in key]
    assert row["mode_uav_step_fraction"] == 2 / (8 * length)
    assert (row["first_entry_step"], row["first_input_step"]) == (2, 0)
    assert row["input_before_entry"] is True
    # pre_entry = steps 0-1, entry_to_input empty (input precedes entry), post_input = all
    assert (row["steps_pre_entry"], row["steps_entry_to_input"], row["steps_post_input"]) == (2, 0, 6)
    assert row["qos_per_step_pre_entry"] == 0.25 and row["qos_per_step_entry_to_input"] is None
    assert row["qos_per_step_post_input"] == 2.0 / 6
    assert (row["guard_checked_actions"], row["guard_blocked_actions"]) == (6, 3)
    assert (row["charging_spell_count"], row["one_tick_spell_count"]) == (3, 2)
    assert row["one_tick_spell_share"] == 2 / 3
    assert row["wait_ticks_total"] == 2
    assert row["charger_input_wh"] == 12.0
    assert row["episode_minimum_battery_ratio"] == 0.3
    assert row["terminal_type"] == "truncated" and row["zero_service"] is False
    assert row["raw_native_J"] == 15.0 and row["dock_bit_uav_steps"] == 2
    # Ordered phases: input first at step 4 -> pre 0-1, entry_to_input 2-3, post 4-5.
    metrics[:, ev.CHARGER_INPUT] = (0.0, 0.0, 0.0, 0.0, 2.0, 0.0)
    ordered = ev.world_row(7, rewards, metrics, ends, steps, time_step_s=1.0)
    assert (ordered["first_input_step"], ordered["input_before_entry"]) == (4, False)
    assert (ordered["steps_pre_entry"], ordered["steps_entry_to_input"],
            ordered["steps_post_input"]) == (2, 2, 2)
    assert ordered["qos_per_step_pre_entry"] == 0.25
    assert ordered["qos_per_step_entry_to_input"] == 0.25
    assert ordered["qos_per_step_post_input"] == 0.5
    # No entry and no input: everything is pre-entry, the other phases are empty.
    metrics[:, ev.CHARGER_INPUT] = 0.0
    quiet_steps = dict(steps, entered=np.zeros_like(entered))
    quiet = ev.world_row(7, rewards, metrics, ends, quiet_steps, time_step_s=1.0)
    assert (quiet["first_entry_step"], quiet["first_input_step"]) == (None, None)
    assert (quiet["steps_pre_entry"], quiet["steps_entry_to_input"], quiet["steps_post_input"]) == (6, 0, 0)
    assert quiet["qos_per_step_entry_to_input"] is None and quiet["qos_per_step_post_input"] is None
    agg = ev.aggregate([dict(row, failed=False), dict(quiet, seed=8, zero_service=True, failed=False)])
    assert agg["mean_first_entry_step"] == 2.0 and agg["observed_first_entry_step"] == 1
    assert agg["mean_qos_per_step_post_input"] == 2.0 / 6
    assert agg["observed_qos_per_step_post_input"] == 1
    assert agg["observed_qos_per_step_pre_entry"] == 2    # always reported for phase splits
    assert agg["zero_service_worlds"] == 1 and agg["actual_transitions"] == 12
    assert agg["input_before_entry_worlds"] == 1 and agg["failed_worlds"] == []
    assert not [key for key in agg if "presen" in key]


def test_mechanism_readings_definitions(config_60):
    entered = np.zeros((8, 8), dtype=bool)
    exited = np.zeros((8, 8), dtype=bool)
    distances = np.arange(64, dtype=np.float32).reshape(8, 8)
    entered[0, 0] = True                     # entry before any exit: no recapture
    exited[2, 0], entered[5, 0] = True, True  # exit -> next entry at step 5
    entered[7, 0] = True                     # second entry without an exit in between
    exited[1, 3], entered[4, 3] = True, True  # earlier exit, listed first
    exited[6, 5] = True                      # exit never followed by an entry
    assert ev.recapture_distances(entered, exited, distances) == [
        float(distances[4, 3]), float(distances[5, 0])]
    assert ev.recapture_distances(entered, np.zeros_like(exited), distances) == []
    steps = {"entered": entered, "exited": exited, "nearest_station_distance_m": distances}
    row = ev.mechanism_row(steps, [[1.0, 2.0], [3.0, 4.0]])
    assert row["post_exit_recapture_count"] == 2
    assert row["post_exit_recapture_median_m"] == float(np.median([distances[4, 3], distances[5, 0]]))
    assert row["mean_nearest_station_distance_m"] == 31.5
    empty = ev.mechanism_row(dict(steps, exited=np.zeros_like(exited)), [[1.0, 2.0], [3.0, 4.0]])
    assert empty["post_exit_recapture_distances_m"] == [] and empty["post_exit_recapture_median_m"] is None
    counts = ev.station_counts(np.asarray((0, 1, 1, 0, 1, 1, 1, 0)),
                               np.asarray((1, 1, 0, 0, 1, 1, 1, 1), dtype=bool))
    assert counts.dtype == np.int8 and counts.tolist() == [2, 4]
    # Absolute station xy from the first legal observation equals the environment's stations.
    env = make_env(config_60, 955001)
    try:
        obs, _ = env.reset(seed=955001)
        truth = np.asarray(env.env.charging_station_positions, dtype=np.float64)[:2, :2]
    finally:
        env.close()
    np.testing.assert_allclose(ev.absolute_station_xy(np.asarray(obs, dtype=np.float32)), truth,
                               rtol=0, atol=0.01)
