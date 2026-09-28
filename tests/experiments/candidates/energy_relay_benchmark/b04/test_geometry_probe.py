"""Block 1 / Block 2 of b04_geometry_probe_a01: constructed worlds, query isolation, readings."""
import copy
import json
import random
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01.evaluation import make_eval_config
from experiments.candidates.energy_relay_benchmark.b04 import geometry_probe as gp
from experiments.candidates.energy_relay_benchmark.b04 import probe_run as pr
from experiments.candidates.energy_relay_benchmark.b04 import readings as rd
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

CHECKPOINT = pr.ROOT / pr.CHECKPOINT
needs_checkpoint = pytest.mark.skipif(not (CHECKPOINT / "agent.pt").is_file(),
                                      reason="saved SET c06 checkpoint not on this host")


@pytest.fixture(scope="module")
def config():
    return make_eval_config(gp.HORIZON, 925031)


def _reset(config, seed):
    adapter = make_env(config, seed)
    record, obs, info = gp.reset_with_record(adapter, seed)
    return adapter, record, np.asarray(obs, dtype=np.float32), np.asarray(info["state"], dtype=np.float32)


@pytest.mark.parametrize("seed", [955001, 955017])
def test_constructed_id_equals_plain_reset_bitwise(config, seed):
    adapter, record, obs, state = _reset(config, seed)
    plain = make_env(config, seed)
    plain_obs, plain_info = plain.reset(seed=seed)
    assert np.array_equal(obs, plain_obs) and np.array_equal(state, plain_info["state"])
    plans = gp.plan_conditions(adapter, record)
    rng_before = adapter.env.np_random.get_state()[1].copy()
    built, id_obs, id_state = gp.construct_world(adapter, "ID", rng_offsets=plans, t=0)
    assert id_obs.dtype == plain_obs.dtype and id_state.dtype == np.asarray(plain_info["state"]).dtype
    assert np.array_equal(id_obs, plain_obs) and np.array_equal(id_state, plain_info["state"])
    assert np.array_equal(adapter.env.np_random.get_state()[1], rng_before)   # replay restored RNG
    assert built is not adapter


@pytest.mark.parametrize("condition", ["ROT", "MIR_X", "MIR_Y"])
def test_reflection_geometry_regenerated_grid_and_matching(config, condition):
    adapter, record, _, _ = _reset(config, 955003)
    raw = adapter.env
    plans = gp.plan_conditions(adapter, record)
    plan = plans[condition]
    built, _, _ = gp.construct_world(adapter, condition, rng_offsets=plans, t=0)
    new, signs = built.env, plan["signs"]
    for name in ("ground_bs_positions", "user_positions", "charging_station_positions"):
        assert np.allclose(getattr(new, name)[:, :2], gp.reflect_xy(raw, getattr(raw, name)[:, :2], signs))
    for name in ("user_waypoints", "cluster_centers_history", "cluster_waypoints"):
        assert np.allclose(getattr(new, name), gp.reflect_xy(raw, getattr(raw, name), signs))
    assert np.allclose(new.user_velocities[:, :2], raw.user_velocities[:, :2] * np.asarray(signs))
    corner = gp.spawn_corner(raw, new.uav_positions[:, :2])
    assert corner == plan["corner"] and corner != record.corner
    assert np.allclose(new.uav_positions[:, :2] - gp.slot_centres(raw, corner), record.jitter)
    assert sorted(plan["matching"]) == list(range(raw.n_uavs))
    assert sum(plan["exact_match"]) == raw.n_uavs - 1
    far = int(np.flatnonzero(~np.asarray(plan["exact_match"]))[0])
    assert plan["matching_distance_m"][far] > 250.0
    assert plan["in_support"] is True and plan["support"]["producible"]
    assert set(plan["support"]["rules"]) == set(gp.SUPPORT_RULES)


def test_rot_keep_and_station_recomputation(config):
    adapter, record, _, _ = _reset(config, 955004)
    raw = adapter.env
    plans = gp.plan_conditions(adapter, record)
    keep = plans["ROT_KEEP"]
    assert keep["in_support"] is False and keep["matching"] == list(range(raw.n_uavs))
    assert not keep["support"]["rules"]["spawn_grid"]
    bs = plans["BS_A"]
    move = np.asarray(bs["bs_displacement_m"])
    assert np.isclose(np.abs(move).sum(), gp.DISPLACEMENT_M)
    assert gp.bs_edge(raw, bs["bs_xy"]) == gp.bs_edge(raw, record.bs_xy[0])
    assert np.allclose(gp.remote_corner_of(raw, bs["bs_xy"]), gp.remote_corner_of(raw, record.bs_xy[0]))
    # station 0 re-anchored with the same jitter draw: shift = 0.7 x BS move unless clipped
    shift = np.asarray(bs["stations"][0]) - record.stations_xy[0]
    low, high = 0.08 * raw.area_size, 0.92 * raw.area_size
    if low < bs["stations"][0][0] < high and low < bs["stations"][0][1] < high:
        assert np.allclose(shift, 0.7 * move)
    assert np.allclose(plans["BS_B"]["stations"], record.stations_xy)
    cl = plans["CL_1"]
    assert cl["members"] == list(range(6, 12)) and np.isclose(np.abs(cl["shift"]).sum(), gp.DISPLACEMENT_M)
    built, _, _ = gp.construct_world(adapter, "CL_1", rng_offsets=plans, t=0)
    moved = np.flatnonzero(np.any(built.env.user_positions != raw.user_positions, axis=1))
    assert moved.tolist() == cl["members"]


def test_wrap_and_symmetry_error_arithmetic():
    assert np.isclose(rd.symmetry_error(np.radians(-10.0), np.radians(170.0), "ROT"), 0.0)
    assert np.isclose(rd.symmetry_error(np.radians(10.0), np.radians(170.0), "MIR_X"), 0.0)
    assert np.isclose(rd.symmetry_error(np.radians(-30.0), np.radians(30.0), "MIR_Y"), 0.0)
    assert np.isclose(np.degrees(rd.symmetry_error(np.radians(170.0), np.radians(170.0), "ROT")), 180.0)
    assert np.isclose(rd.wrap(np.radians(190.0)), np.radians(-170.0))


def test_readings_matching_shield_drop_and_sign_agreement():
    worlds, steps, n = 2, len(gp.QUERY_STEPS), 3
    c = len(gp.CONDITIONS)
    base = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    proposals = np.zeros((worlds, steps, c, n, 4), dtype=np.float32)
    proposals[..., :2] = base
    k_rot, k_bs = gp.CONDITIONS.index("ROT"), gp.CONDITIONS.index("BS_A")
    matching = np.tile(np.arange(n), (worlds, c, 1))
    matching[:, k_rot] = [2, 0, 1]
    proposals[:, :, k_rot, :, :2] = -base[[2, 0, 1]]       # perfect equivariance under m
    angle = np.radians(40.0)
    proposals[:, :, k_bs, 0, :2] = [np.cos(angle), np.sin(angle)]   # agent 0 turns +40 deg
    modes = np.zeros((worlds, steps, c, n), dtype=bool)
    modes[:, :, k_bs, 2] = True
    planner = np.repeat(proposals[:, :1], 2, axis=1)
    arrays = {"proposals": proposals, "modes": modes, "planner_proposals": planner,
              "planner_modes": np.zeros((worlds, 2, c, n), dtype=bool)}
    exact = np.ones((worlds, c, n), dtype=bool)
    exact[:, k_rot, 1] = False
    out = rd.readings(arrays, matching, exact)
    assert out["symmetry_error"]["ROT"]["t0"]["exact_matches"]["median"] == 0.0
    assert out["symmetry_error"]["ROT"]["t0"]["non_exact"]["n"] == worlds
    assert out["rule_inputs"]["median_e_rot"]["t0"] == 0.0
    assert out["dropped_shield_pairs"]["BS_A"]["t0"] == worlds
    assert out["t0"]["BS_A"]["abs_dtheta_deg"]["n"] == 2 * worlds
    assert out["sign_agreement"]["H_local"]["BS_A"] == {"pairs": worlds, "share": 1.0}


def test_paired_rotation_triples_primary_on_one_host():
    rot = [{"seed": s, "qos_per_step": q, "raw_native_J": j, "in_support": True}
           for s, q, j in ((1, 0.5, 10.0), (2, 0.4, 8.0), (3, 0.6, 9.0))]
    local = [{"seed": s, "qos_per_step": q, "raw_native_J": 9.0} for s, q in ((1, 0.4), (2, 0.4), (3, 0.4))]
    panel = {"worlds": [{"seed": s, "qos_per_step": 0.5, "raw_native_J": 9.0} for s in (3, 1, 2)]}
    out = gp.paired_rotation(rot, local, panel)
    first = out["triples"][0]
    assert (first["qos_per_step_local_id"], first["qos_per_step_local_rot"], first["qos_per_step_node_panel"]) == (0.4, 0.5, 0.5)
    primary = out["summary"]["primary_rot_minus_local_id"]
    assert np.isclose(primary["qos_per_step"]["mean_paired_difference"], 0.1)
    assert np.isclose(primary["qos_per_step"]["paired_se"], 0.1 / np.sqrt(3))
    assert np.isclose(primary["raw_native_J"]["mean_paired_difference"], 0.0)
    diagnostic = out["summary"]["diagnostic_local_id_minus_node"]["qos_per_step"]
    assert np.isclose(diagnostic["mean_paired_difference"], -0.1) and np.isclose(diagnostic["paired_se"], 0.0)
    secondary = out["summary"]["secondary_rot_minus_node"]["qos_per_step"]
    assert np.isclose(secondary["mean_paired_difference"], 0.0)


def test_capacity_curve_reports_relaxed_and_actual(config):
    curve = gp.capacity_vs_distance(config, 955001, distances=[100.0, 3000.0, 8000.0])
    access = curve["rows"]["access"]
    assert [row["distance_m"] for row in access] == [100.0, 3000.0, 8000.0]
    assert all(row["actual_bps"] == 0.0 for row in access if row["sinr_db"] < curve["config"]["min_sinr_db"])
    assert all(row["relaxed_bps"] > 0.0 for row in access)   # relaxed Shannon form: no SINR cut
    assert access[0]["sinr_db"] > access[-1]["sinr_db"]
    assert curve["rows"]["uav_to_bs"][0]["relaxed_bps"] > 0 and curve["config"]["min_sinr_db"] == 3.0


def test_runner_root_and_arguments():
    from experiments.candidates.energy_relay_benchmark.b04 import run_geometry_probe as runner
    assert (runner.ROOT / "scripts" / "hmasd_launch.py").is_file() and runner.ROOT == pr.ROOT
    args = runner.parse_args(["block1", "--out", "runs/energy_relay_benchmark/x", "--launch-sha", "abc"])
    assert args.threads == 2 and args.workers == 1 and args.worlds == "955001-955032"
    assert args.checkpoint is None          # resolved under --data-root by probe_run.run
    assert args.data_root == runner.ROOT
    other = runner.parse_args(["block1", "--out", "x", "--launch-sha", "abc", "--data-root", "/elsewhere"])
    assert other.data_root == Path("/elsewhere")
    assert runner.DEFAULT_CHECKPOINT == runner.ROOT / runner.CHECKPOINT_REL


def _global_rng():
    return (random.getstate(), np.random.get_state()[1].copy(), torch.random.get_rng_state().clone())


def _same_rng(a, b):
    return a[0] == b[0] and np.array_equal(a[1], b[1]) and torch.equal(a[2], b[2])


def _helpers(agent):
    """repr of the two lock-holding helpers shared (not copied) by the query deepcopy."""
    return tuple(repr({k: v for k, v in sorted(vars(obj).items()) if "lock" not in k})
                 for obj in (agent.env_state_manager, agent.metrics_collector))


@needs_checkpoint
def test_query_is_side_effect_free(tmp_path):
    task = gp.ProbeTask(seed=955002, checkpoint_dir=str(CHECKPOINT), threads=2)
    world, record, cfg = gp._learner(task, torch.device("cpu"))
    from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
        PolicyController, load_learner_policy)
    agent, _ = load_learner_policy(world, record, cfg, torch.device("cpu"), str(tmp_path))
    controller = PolicyController(agent, deterministic=True)
    adapter = make_env(cfg, task.seed)
    controller.reset()
    rec, obs, info = gp.reset_with_record(adapter, task.seed)
    obs, state = np.asarray(obs, np.float32), np.asarray(info["state"], np.float32)
    plans = gp.plan_conditions(adapter, rec)
    done, modes, previous = np.ones(1, dtype=bool), np.zeros(8, dtype=bool), None
    for step in range(11):
        if step in (0, 10):
            built, id_obs, id_state = gp.construct_world(adapter, "ID", rng_offsets=plans, t=step,
                                                         previous_serving_sets=previous)
            rng, env_rng = _global_rng(), adapter.env.np_random.get_state()[1].copy()
            managed = _helpers(agent)
            alone = gp.query_policy(controller, built, id_obs, id_state, step, done, modes)["proposal"]
            other, o_obs, o_state = gp.construct_world(adapter, "BS_A", rng_offsets=plans, t=step,
                                                       previous_serving_sets=previous)
            gp.query_policy(controller, other, o_obs, o_state, step, done, modes)
            again = gp.query_policy(controller, built, id_obs, id_state, step, done, modes)["proposal"]
            assert np.array_equal(alone, again)
            assert _same_rng(rng, _global_rng())
            assert np.array_equal(env_rng, adapter.env.np_random.get_state()[1])
            assert managed == _helpers(agent)
            real = controller.propose(obs, state, step, done, modes.copy())
            assert np.array_equal(real, alone)
        else:
            real = controller.propose(obs, state, step, done, modes.copy())
        previous = copy.deepcopy(adapter.env.user_serving_sets)
        obs, _, terminated, truncated, info = adapter.step(real)
        obs, state = np.asarray(obs, np.float32), np.asarray(info["next_state"], np.float32)
        done[:] = terminated or truncated


@needs_checkpoint
def test_block2_constructed_reset_and_short_episode(config, tmp_path):
    adapter, record, _, _ = _reset(config, 955005)
    plans = gp.plan_conditions(adapter, record, conditions=("ROT",))
    _, rot_obs, rot_state = gp.construct_world(adapter, "ROT", rng_offsets=plans, t=0)
    wrapped = gp.ConstructedResetEnv(make_env(config, 955005), "ROT")
    obs, info = wrapped.reset(seed=955005)
    assert np.array_equal(obs, rot_obs) and np.array_equal(info["state"], rot_state)
    assert wrapped.construction["condition"] == "ROT"
    checkpoint_record = json.loads((CHECKPOINT / "record.json").read_text())
    from experiments.candidates.energy_relay_benchmark.b01.evaluation import WorldTask
    from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
    task = WorldTask(controller="L", seed=955005, params=PRODUCTION_PARAMS, horizon=12,
                     policy_seed=int(checkpoint_record["training_seed"]), threads=2,
                     checkpoint=str(CHECKPOINT / "agent.pt"), log_dir=str(tmp_path),
                     checkpoint_record=str(CHECKPOINT / "record.json"))
    result = gp.rotated_episode(task)
    assert result["row"]["actual_length"] == 12 and result["construction"]["condition"] == "ROT"
    assert "arrays" not in result
