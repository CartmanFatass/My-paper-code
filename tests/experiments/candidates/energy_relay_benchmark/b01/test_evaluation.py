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
    FixedWaypointHeuristic,
    LayoutHeuristic,
    UnobservedRegime,
    estimator_kmeans,
    park_assignment,
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


# --- stochastic-check phase and the additive position diagnostics ---------------------------

STOCHASTIC_H = 20


def _stochastic_task(checkpoint, tmp_path, draw, **changes):
    values = dict(controller="N", seed=955001, params=PRODUCTION_PARAMS, horizon=STOCHASTIC_H,
                  policy_seed=POLICY_SEED, threads=1, checkpoint=str(checkpoint),
                  log_dir=str(tmp_path), action_mode="stochastic", draw=draw)
    return ev.WorldTask(**(values | changes))


def _same_result(left, right):
    assert {k: v for k, v in left["row"].items() if k not in VOLATILE} == \
           {k: v for k, v in right["row"].items() if k not in VOLATILE}
    assert left["arrays"].keys() == right["arrays"].keys()
    for key in left["arrays"]:
        assert np.array_equal(left["arrays"][key], right["arrays"][key]), key


def test_sample_seed_rule():
    seed = ev.sample_seed(POLICY_SEED, 955001, 0)
    assert seed == hash((POLICY_SEED, 955001, 0)) & 0xFFFFFFFF and 0 <= seed < 2 ** 32
    assert seed == ev.sample_seed(np.int64(POLICY_SEED), np.int64(955001), 0)
    assert len({ev.sample_seed(POLICY_SEED, world, draw)
                for world in (955001, 955002) for draw in (0, 1)}) == 4


def test_stochastic_draws_repeat_bit_for_bit_and_differ(tmp_path, fresh_checkpoint):
    first = ev.evaluate_task(_stochastic_task(fresh_checkpoint, tmp_path, 0))
    again = ev.evaluate_task(_stochastic_task(fresh_checkpoint, tmp_path, 0))
    other = ev.evaluate_task(_stochastic_task(fresh_checkpoint, tmp_path, 1))
    mean = ev.evaluate_task(_stochastic_task(fresh_checkpoint, tmp_path, None,
                                             action_mode="deterministic"))
    _same_result(first, again)
    row = first["row"]
    assert (row["action_mode"], row["draw"]) == ("stochastic", 0)
    assert row["sample_seed"] == ev.sample_seed(POLICY_SEED, 955001, 0)
    assert other["row"]["sample_seed"] == ev.sample_seed(POLICY_SEED, 955001, 1) != row["sample_seed"]
    assert not np.array_equal(first["arrays"]["own_xyz"], other["arrays"]["own_xyz"])
    assert not np.array_equal(first["arrays"]["own_xyz"], mean["arrays"]["own_xyz"])
    assert mean["row"]["action_mode"] == "deterministic"
    assert "draw" not in mean["row"] and "sample_seed" not in mean["row"]
    assert row["actual_length"] == STOCHASTIC_H and row["failed"] is False
    # Spawn workers reproduce the serial draws (the seed is set inside the worker).
    tasks = [_stochastic_task(fresh_checkpoint, tmp_path, draw) for draw in (0, 1)]
    for left, right in zip(ev.run_tasks(tasks, workers=1), ev.run_tasks(tasks, workers=2),
                           strict=True):
        _same_result(left, right)
    agg = ev.aggregate([first["row"], other["row"]])
    assert "mean_draw" not in agg and "mean_sample_seed" not in agg


def test_stochastic_mode_is_refused_outside_n(tmp_path, fresh_checkpoint):
    with pytest.raises(ValueError, match="controller N and a draw"):
        ev.evaluate_task(_stochastic_task(fresh_checkpoint, tmp_path, None))
    with pytest.raises(ValueError, match="controller N and a draw"):
        ev.evaluate_task(replace(_stochastic_task(fresh_checkpoint, tmp_path, 0),
                                 controller="Hlocal", checkpoint=None))
    with pytest.raises(ValueError, match="action_mode"):
        ev.evaluate_task(_stochastic_task(fresh_checkpoint, tmp_path, 0, action_mode="sampled"))
    with pytest.raises(ValueError, match="sample_seed"):
        ev.PolicyController(object(), deterministic=False)


@pytest.mark.parametrize("deterministic", [True, False], ids=["mean", "sampled"])
def test_sampling_flag_reaches_coordinator_and_actor(tmp_path, deterministic):
    """The batched ``HMASDAgent.step`` route: the flag arrives at the coordinator's
    ``assign_and_value_batch``, the ``SkillDiscoverer`` forward and the actor's action head."""
    device = torch.device("cpu")
    config = ev.make_eval_config(STOCHASTIC_H, POLICY_SEED)
    seed_everything(POLICY_SEED, device)
    evaluator = HMASDAgent(config, log_dir=str(tmp_path / "agent"), device=device)
    evaluator.train(False)
    assert not (evaluator.use_ha_ctse or evaluator.d2_enabled
                or evaluator.r39_native_toy_fixed_primitives or evaluator.use_low_level_compact
                or evaluator.use_central_snapshot)   # the plain batched route is the live one
    seen = {"coordinator": [], "discoverer": [], "action_head": []}

    def spy(name, function, position):
        def wrapped(*args, **kwargs):
            flag = kwargs["deterministic"] if "deterministic" in kwargs else args[position]
            seen[name].append(bool(flag))
            return function(*args, **kwargs)
        return wrapped

    coordinator = evaluator.skill_coordinator
    coordinator.assign_and_value_batch = spy(
        "coordinator", coordinator.assign_and_value_batch, 2)
    discoverer = evaluator.skill_discoverer
    discoverer.forward = spy("discoverer", discoverer.forward, 3)
    head = discoverer.actor.act.action_out
    head.forward = spy("action_head", head.forward, 2)
    controller = ev.PolicyController(evaluator, deterministic=deterministic,
                                     sample_seed=None if deterministic else 12345)
    env = make_env(config, 955001)
    try:
        row, _ = ev.evaluate_world(controller, env, config, 955001, PRODUCTION_PARAMS)
    finally:
        env.close()
    assert row["actual_length"] == STOCHASTIC_H
    assert len(seen["coordinator"]) == STOCHASTIC_H // config.k   # reassignment at 0 and k
    assert len(seen["discoverer"]) == len(seen["action_head"]) == STOCHASTIC_H
    for name, flags in seen.items():
        assert set(flags) == {deterministic}, name


def test_position_diagnostics_definitions():
    length, area, floor = 4, 8000.0, 50.0
    xyz = np.zeros((length, 8, 3))
    xyz[..., :2] = 4000.0
    xyz[..., 2] = 120.0
    xyz[0, 0, 0] = 0.5                 # x near 0: boundary
    xyz[1, 1, 1] = area - 0.2          # y near area: boundary
    xyz[2, 2, 0] = 1.0                 # exactly 1 m: not boundary (strict <)
    xyz[0, 3, 2] = floor               # on the floor
    xyz[1, 3, 2] = floor + 0.5         # floor + 0.5: counted (<=)
    xyz[2, 3, 2] = floor + 0.6         # above tolerance
    mode = np.zeros((length, 8), dtype=bool)
    mode[:, 7] = True                  # UAV 7 in shield mode throughout: excluded
    xyz[:, 7, 0] = 0.0                 # would be boundary...
    xyz[:, 7, 2] = floor               # ...and floor, but it is not in normal mode
    distance = np.full((length, 8), 1000.0, dtype=np.float32)
    station = np.zeros((length, 8), dtype=np.int8)
    distance[0, :3] = 100.0            # three anchor UAV-steps within 300 m
    distance[1, 4], station[1, 4] = 299.9, 1   # one centre UAV-step
    distance[2, 5], station[2, 5] = 300.0, 1   # exactly 300 m: not counted (strict <)
    distance[3, 7], station[3, 7] = 10.0, 1    # shield-mode UAV still counted (no mode filter)
    metrics = np.zeros((length, len(TRACE_FIELDS)))
    metrics[:, ev.QOS] = (0.0, 0.0, 0.3, 0.0)
    steps = {"own_xyz": xyz, "mode": mode, "nearest_station": station,
             "nearest_station_distance_m": distance}
    result = ev.position_diagnostics(metrics, steps, area_size_m=area, floor_m=floor)
    normal = length * 7
    assert result["boundary_share_normal_mode"] == 2 / normal
    assert result["altitude_floor_share_normal_mode"] == 2 / normal
    assert result["anchor_uav_steps_within_300m"] == 3
    assert result["centre_uav_steps_within_300m"] == 2
    assert result["first_service_step"] == 2
    metrics[:, ev.QOS] = 0.0
    quiet = ev.position_diagnostics(metrics, dict(steps, mode=np.ones_like(mode)),
                                    area_size_m=area, floor_m=floor)
    assert quiet["first_service_step"] is None
    assert quiet["boundary_share_normal_mode"] is None
    assert quiet["altitude_floor_share_normal_mode"] is None


def test_live_rows_carry_diagnostics_from_env_config(tmp_path, config_60):
    """Floor and area come from the config the env is built with (not hard-coded)."""
    assert (config_60.area_size, config_60.height_range[0]) == (8000, 50)
    env = make_env(config_60, 953001)
    try:
        row, arrays = ev.evaluate_world(ev.HeuristicController(VARIANTS["H1"], env), env,
                                        config_60, 953001, PRODUCTION_PARAMS)
    finally:
        env.close()
    expected = ev.position_diagnostics(arrays["metrics"], arrays,
                                       area_size_m=config_60.area_size,
                                       floor_m=config_60.height_range[0])
    assert {key: row[key] for key in expected} == expected
    assert 0.0 <= row["altitude_floor_share_normal_mode"] <= 1.0


# --- stage0-references: fixed-waypoint controllers and H_central@10 ---------------------------

FIXED_PARAMS = replace(VARIANTS["H1"], information="local")


class RecordingFixed(ev.FixedWaypointController):
    def __init__(self, params, kind):
        super().__init__(params, kind)
        self.actions = []

    def propose(self, observations, state, step, previous_done, modes):
        actions = super().propose(observations, state, step, previous_done, modes)
        self.actions.append((own_positions(observations).copy(), actions.copy()))
        return actions


def _run_fixed(config, seed, kind):
    env = make_env(config, seed)
    try:
        obs, _ = env.reset(seed=seed)
        truth = {"uav_xyz": np.asarray(env.env.uav_positions, dtype=np.float64).copy(),
                 "stations_xy": np.asarray(env.env.charging_station_positions,
                                           dtype=np.float64)[:2, :2].copy(),
                 "obs": np.asarray(obs, dtype=np.float32)}
        controller = RecordingFixed(FIXED_PARAMS, kind)
        row, arrays = ev.evaluate_world(controller, env, config, seed, PRODUCTION_PARAMS)
    finally:
        env.close()
    return controller, row, arrays, truth


def test_spawn_targets_are_reset_xy_at_100m_and_never_change(config_60):
    controller, row, arrays, truth = _run_fixed(config_60, 955001, "spawn")
    reset_xy = own_positions(truth["obs"])[:, :2]
    np.testing.assert_allclose(reset_xy, truth["uav_xyz"][:, :2], rtol=0, atol=0.01)
    targets = arrays["target_xy"]
    assert targets.shape == (60, 8, 2)
    assert np.array_equal(targets, np.broadcast_to(reset_xy, targets.shape))   # never change
    assert controller.heuristic.calls == 60 and controller.plan_input_steps == []
    assert controller.park_assignment == []
    # Altitude target 100 m: the vertical action heads for 100 m at the 5 m/s cap (H1 primitive).
    for own, actions in controller.actions:
        expected = np.clip((100.0 - own[:, 2]) / 5.0, -1.0, 1.0)
        np.testing.assert_allclose(actions[:, 2], expected.astype(np.float32), rtol=0, atol=1e-6)
    final_z = arrays["own_xyz"][-1, :, 2]
    assert np.all(np.abs(final_z - 100.0) < np.abs(arrays["own_xyz"][0, :, 2] - 100.0) + 1e-3)


def test_fixed_targets_survive_mode_changes(live_frames):
    heuristic = FixedWaypointHeuristic(FIXED_PARAMS, "spawn")
    first = live_frames[0]
    heuristic.act(first, np.zeros(8, dtype=bool))
    planned = heuristic.targets_xy.copy()
    modes = np.zeros(8, dtype=bool)
    modes[[1, 4]] = True                      # shield holds two UAVs; later released
    for frame in live_frames[1:10]:
        actions = heuristic.act(frame, modes)
        modes = ~modes
        assert np.array_equal(heuristic.targets_xy, planned)
        assert np.all(np.abs(actions[:, :2]) <= 1.0)
    # A UAV released far from its waypoint heads straight back at the 30 m/s cap.
    far = live_frames[1].copy()
    own = own_positions(far)
    heuristic.targets_xy[0] = own[0, :2] + np.asarray((3000.0, -4000.0))
    actions = heuristic.act(far, np.zeros(8, dtype=bool))
    np.testing.assert_allclose(actions[0, :2], (0.6, -0.8), rtol=0, atol=1e-6)
    with pytest.raises(ValueError, match="kind"):
        FixedWaypointHeuristic(FIXED_PARAMS, "ring")
    with pytest.raises(ValueError, match="legal observation"):
        ev.FixedWaypointController(VARIANTS["H1"], "spawn")


def test_park_assignment_rule_on_synthetic_geometry():
    own = np.asarray([[0.0, 0.0], [10.0, 0.0], [5.0, 50.0], [100.0, 100.0],
                      [-10.0, 0.0], [50.0, 50.0], [0.0, 90.0], [100.0, 100.0]])
    # Station 0 at (0, 0): UAV 0 is nearest.  Station 1 at (100, 100): UAVs 3 and 7 tie ->
    # lower index 3.
    assert park_assignment(own, [(0.0, 0.0), (100.0, 100.0)]) == [[0, 0], [3, 1]]
    # Without UAV 0 near station 0, UAVs 1 and 4 tie at 10 m -> lower index 1.
    tie = own.copy()
    tie[0] = (500.0, 500.0)
    assert park_assignment(tie, [(0.0, 0.0), (100.0, 100.0)]) == [[1, 0], [3, 1]]
    # UAV 0 is nearest both stations: station 0 (first) takes it, station 1 takes the nearest
    # remaining UAV (1 at 84.9 m, not 2 at 197.9 m).
    both = np.asarray([[60.0, 60.0], [0.0, 0.0], [200.0, 200.0]])
    assert park_assignment(both, [(50.0, 50.0), (60.0, 60.0)]) == [[0, 0], [1, 1]]


def test_park2_targets_are_station_xy_and_reset_xy(config_60, tmp_path):
    controller, row, arrays, truth = _run_fixed(config_60, 955001, "park2")
    reset_xy = own_positions(truth["obs"])[:, :2].astype(np.float64)
    stations = np.asarray(ev.absolute_station_xy(truth["obs"]), dtype=np.float64)
    np.testing.assert_allclose(stations, truth["stations_xy"], rtol=0, atol=0.01)
    assignment = controller.park_assignment
    assert assignment == park_assignment(reset_xy, list(stations))
    assert [station for _, station in assignment] == [0, 1]
    expected = reset_xy.copy()
    for uav, station in assignment:
        expected[uav] = stations[station]
    targets = arrays["target_xy"]
    assert np.array_equal(targets, np.broadcast_to(expected, targets.shape))
    parked = [uav for uav, _ in assignment]
    assert all(not np.allclose(expected[uav], reset_xy[uav]) for uav in parked)
    task = ev.WorldTask(controller="Hpark2", seed=955001, params=PRODUCTION_PARAMS, horizon=20,
                        policy_seed=POLICY_SEED, threads=1, heuristic=FIXED_PARAMS,
                        log_dir=str(tmp_path))
    result = ev.evaluate_task(task)
    assert result["row"]["park_assignment"] == assignment
    assert result["row"]["controller_information"] == ev.REFERENCE_INFORMATION["Hpark2"]
    assert result["row"]["replans"] == 1 and result["row"]["search_replans"] == 0


def test_h1_period_30_is_the_grid_h1_and_period_10_replans_every_10(tmp_path):
    from experiments.candidates.energy_relay_benchmark.b01 import native

    spec = replace(native.B01Spec(), worlds=(955001,), controllers=("H1",),
                   grid_settings=((0.0, 0.05),), horizon=40, workers=1, threads=1,
                   checkpoint_sha256=None, policy_fingerprint=None)
    grid = native.run_native(out=tmp_path / "grid", launch_sha="fixture", checkpoint=None,
                             phase="grid", spec=spec, argv=["fixture"])
    grid_row = grid["panels"]["grid/H1_e0.00_x0.05"]["worlds"][0]
    explicit = ev.evaluate_task(ev.WorldTask(
        controller="H1", seed=955001, params=PRODUCTION_PARAMS, horizon=40,
        policy_seed=POLICY_SEED, threads=1,
        heuristic=replace(VARIANTS["H1"], replan_period=30), log_dir=str(tmp_path)))
    volatile = VOLATILE | {"width", "matched_pair_id"}
    assert {k: v for k, v in explicit["row"].items() if k not in volatile} == \
           {k: v for k, v in grid_row.items() if k not in volatile}
    assert grid_row["replans"] == 2 and grid_row["plan_input_steps"] == 2
    config_30 = ev.make_eval_config(30, POLICY_SEED)
    env = make_env(config_30, 955001)
    try:
        ten = ev.HeuristicController(native.heuristic_params("H1r10", spec), env)
        row, _ = ev.evaluate_world(ten, env, config_30, 955001, PRODUCTION_PARAMS)
    finally:
        env.close()
    assert row["actual_length"] == 30 and ten.plan_input_steps == [0, 10, 20]
