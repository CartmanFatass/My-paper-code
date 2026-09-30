"""Actual-mask local proposals, source-exact deliveries and recoverable trajectories."""
from __future__ import annotations

import copy
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_radio_activation.b01 import protocol as ep
from experiments.candidates.uav_radio_activation.b01.scheduler import Scheduler as EScheduler
from experiments.candidates.uav_radio_activation.b03.scheduler import Scheduler as JointScheduler
from .contract import arm_parts
from .policies import LocalTeam
from .reading import episode_metrics

COORD_COUNTERS = ("candidate_plans", "candidate_requests", "candidate_request_upper",
                  "state_reductions", "geometry_snapshots", "prefix_ticks", "recurring_bytes")


def allocate_raw(horizon, coordinator):
    d, r = horizon // 4, 0 if coordinator == "all" else horizon // 4
    raw = dict(
        observations=np.full((horizon, 5, 104), np.nan, np.float32),
        positions=np.full((horizon + 1, 5, 3), np.nan),
        commands=np.full((horizon, 5, 3), np.nan, np.float32),
        proposals=np.full((d, 5, 3), np.nan, np.float32),
        transmitter_mask=np.zeros((horizon, 5), bool),
        reward=np.full(horizon, np.nan), served=np.full(horizon, -1, np.int16),
        sinr_quality=np.full(horizon, np.nan), sinr=np.full((horizon, 5, 50), np.nan),
        connections=np.zeros((horizon, 5, 50), bool),
        decision_ticks=np.arange(0, horizon, 4, dtype=np.int64),
        completed_steps=np.array(0), completed_decisions=np.array(0), completed_rounds=np.array(0),
        coord_tick=np.arange(0, horizon, 4, dtype=np.int64) if r else np.empty(0, np.int64),
        coord_started=np.zeros(r, bool), coord_due=np.full(r, -1, np.int64),
        coord_actual=np.full((r, 5, 3), np.nan, np.float32),
        coord_commands=np.full((r, 5, 3), np.nan, np.float32),
        coord_mask_before=np.full(r, -1, np.int16), coord_mask=np.full(r, -1, np.int16),
        coord_timely=np.zeros(r, bool), coord_selected_mask=np.full(r, -1, np.int16),
        coord_selected_q=np.full(r, -1, np.int16),
        coord_reports=np.zeros((r, 5, 24), np.uint8), coord_report_count=np.zeros(r, np.int16),
        coord_command_packet=np.zeros((r, 16), np.uint8), coord_has_command=np.zeros(r, bool),
        coord_wall_seconds=np.zeros(r), coord_cpu_seconds=np.zeros(r),
        coord_forecast_lengths=np.zeros(r, np.int16), coord_sequential_pair=np.full((r, 2), -1, np.int16),
        coord_sequential_score=np.full((r, 3), np.nan),
    )
    for key in COORD_COUNTERS:
        raw["coord_" + key] = np.zeros(r, np.int64)
    if coordinator == "E":
        raw.update(coord_forecast=np.full((r, 4, 5, 3), np.nan),
                   coord_scores=np.full((r, 32, 3), np.nan),
                   coord_per_state=np.full((r, 32, 4, 3), np.nan),
                   coord_order=np.full((r, 31), -1, np.int16))
    elif coordinator != "all":
        raw.update(coord_forecast=np.full((r, 27, 4, 5, 3), np.nan),
                   coord_scores=np.full((r, 27, 32, 3), np.nan),
                   coord_order=np.full((r, 837, 2), -1, np.int16))
    return raw


def record_round(raw, result, j, coordinator):
    """Copy the actual returned search, including partial late work and packet absence."""
    raw["coord_timely"][j] = bool(result["timely"])
    raw["coord_mask"][j] = int(result["mask"])
    raw["coord_selected_mask"][j] = -1 if result["selected_mask"] is None else result["selected_mask"]
    raw["coord_selected_q"][j] = -1 if result.get("selected_q") is None else result["selected_q"]
    raw["coord_commands"][j] = result.get("commands", raw["coord_actual"][j])
    raw["coord_wall_seconds"][j], raw["coord_cpu_seconds"][j] = result["wall_seconds"], result["cpu_seconds"]
    reports, packet = result["reports"], result["command_packet"]
    raw["coord_report_count"][j] = len(reports)
    for i, report in enumerate(reports):
        raw["coord_reports"][j, i] = np.frombuffer(report, np.uint8)
    raw["coord_has_command"][j] = bool(packet)
    if packet:
        raw["coord_command_packet"][j] = np.frombuffer(packet, np.uint8)
    raw["coord_scores"][j] = result["scores"]
    order = result["evaluated_masks"] if coordinator == "E" else result["evaluated_pairs"]
    if order:
        raw["coord_order"][j, :len(order)] = order
    length = len(result["forecast"]) if coordinator == "E" else result["forecast"].shape[1]
    raw["coord_forecast_lengths"][j] = length
    if coordinator == "E":
        raw["coord_forecast"][j, :length] = result["forecast"]
        raw["coord_per_state"][j] = result["per_state"]
    else:
        raw["coord_forecast"][j, :, :length] = result["forecast"]
        if result["sequential_pair"] is not None:
            raw["coord_sequential_pair"][j] = result["sequential_pair"]
            raw["coord_sequential_score"][j] = result["sequential_score"]
    for key in ("candidate_plans", "state_reductions", "geometry_snapshots", "recurring_bytes"):
        raw["coord_" + key][j] = int(result[key])
    raw["coord_prefix_ticks"][j] = int(result.get("prefix_ticks", 0))
    if coordinator == "E":
        # B01 exposes completed masks and every completed state reduction, not
        # entry into an evaluate() that immediately hits its first clock check.
        lower = max(len(order), (int(result["state_reductions"]) + max(length, 1) - 1) // max(length, 1))
        upper = lower if result["timely"] else min(31, lower + 1)
    else:
        lower = upper = int(result["candidate_requests"])
    raw["coord_candidate_requests"][j], raw["coord_candidate_request_upper"][j] = lower, upper
    raw["completed_rounds"][...] = j + 1


def _observation(value):
    obs = np.asarray(value)
    if obs.shape != (5, 104) or obs.dtype != np.float32 or not np.isfinite(obs).all():
        raise AssertionError("expected five finite FP32 native local observations")
    return obs


def _mask(env, expected):
    value = np.asarray(env.env.transmitter_mask)
    if value.dtype != bool or value.shape != (5,) or not np.array_equal(value, ep.mask_array(expected)):
        raise AssertionError("physical transmitter mask differs from delivered mask")
    return value.copy()


def collect_episode(env, *, arm, world, tape, bundle, out, protocol, counts, actor,
                    policy_sha, inflight, check, team_type=LocalTeam, coordinator_factory=None,
                    clock=time.perf_counter, cpu_clock=time.process_time):
    family, coordinator = arm_parts(arm)
    if (family == "C") != (tape == -1) or (family != "C" and (tape not in protocol.tapes or bundle is None)):
        raise ValueError("program/tape identity mismatch")
    path = Path(out) / "raw" / f"{arm}_w{world}_t{tape}.npz"
    if path.exists():
        raise FileExistsError("episode already has evidence; do not repeat it")
    start_wall, start_cpu = clock(), cpu_clock()
    inflight.clear()
    inflight.update(arm=arm, world=int(world), tape=int(tape), phase="reset", completed_steps=0)
    check()
    counts["explicit_reset_calls"] += 1
    obs, info = env.reset(seed=int(world))
    counts["explicit_resets"] += 1
    obs = _observation(obs)
    _mask(env, ep.ALL_ON)
    users = np.asarray(info["state_info"]["user_positions"], dtype=np.float64).copy()
    raw = allocate_raw(protocol.horizon, coordinator)
    raw["positions"][0] = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64)
    raw["initial_users"] = users
    map_packet = ep.encode_map(users) if coordinator != "all" else b""
    raw["map_packet"] = np.frombuffer(map_packet, np.uint8).copy()
    team = None
    records = []
    times = {f"{part}_{clock_name}_seconds": 0. for part in
             ("decision_query", "sampler", "local_block", "native_step", "mask_refresh", "raw_write")
             for clock_name in ("wall", "cpu")}
    current_mask, pending, pending_at = ep.ALL_ON, None, None
    actual = np.zeros((5, 3), np.float32)
    completed = False
    try:
        team = team_type(family, obs.copy(), actor=actor if family == "S_I" else None)
        if coordinator_factory is not None:
            scheduler = coordinator_factory(coordinator, map_packet, protocol.horizon)
        elif coordinator == "E":
            scheduler = EScheduler("E", map_packet, clock=clock, cpu_clock=cpu_clock)
        elif coordinator in ("S2", "T2"):
            scheduler = JointScheduler(coordinator, map_packet, clock=clock, cpu_clock=cpu_clock,
                                       horizon=protocol.horizon)
        else:
            scheduler = None
        for tick in range(protocol.horizon):
            check()
            raw["observations"][tick] = obs
            if tick % 4 == 0:
                if pending is not None:
                    raise AssertionError("overlapping pending control rounds")
                j = tick // 4
                local_wall, local_cpu = clock(), cpu_clock()
                inflight.update(phase="local_decision", tick=tick)

                def coins():
                    counts["private_integer_reads"] += 10
                    return {key: bundle[key][j].copy() for key in ("private_depart", "private_tail")}

                counts["policy_block_calls"] += 1
                decision = team.decide(obs.copy(), tick, coin_provider=coins if family != "C" else None)
                counts["policy_blocks"] += 1
                counts["sampling_decisions"] += int(decision["sampling_decisions"])
                for key, value in decision["timing"].items():
                    times[key] += value
                times["local_block_wall_seconds"] += clock() - local_wall
                times["local_block_cpu_seconds"] += cpu_clock() - local_cpu
                records.append(copy.deepcopy(decision["record"]))
                proposals = np.asarray(decision["commands"], dtype=np.float32).copy()
                raw["proposals"][j] = proposals
                raw["completed_decisions"][...] = j + 1
                if coordinator in ("all", "E") or tick == 0:
                    actual = proposals.copy()
                if scheduler is not None:
                    raw["coord_started"][j] = True
                    raw["coord_due"][j] = tick + (1 if coordinator == "E" else 2)
                    raw["coord_actual"][j] = actual
                    raw["coord_mask_before"][j] = current_mask
                    inflight["phase"] = "coordinator_call"
                    counts["coordinator_round_calls"] += 1
                    if coordinator == "E":
                        pending = scheduler.decide(obs[:, :3].copy(), actual.copy(), tick, current_mask)
                    else:
                        pending = scheduler.decide(obs[:, :3].copy(), actual.copy(), proposals.copy(), tick,
                                                   current_mask, started=local_wall, cpu_started=local_cpu)
                    counts["coordinator_round_returns"] += 1
                    pending_at = int(raw["coord_due"][j])
                    record_round(raw, pending, j, coordinator)
            raw["commands"][tick] = actual
            raw["transmitter_mask"][tick] = _mask(env, current_mask)
            inflight["phase"] = "native_step"
            check()
            wall, cpu = clock(), cpu_clock()
            counts["native_step_calls"] += 1
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            counts["native_steps"] += 1
            times["native_step_wall_seconds"] += clock() - wall
            times["native_step_cpu_seconds"] += cpu_clock() - cpu
            global_info = info["infos_dict"]["uav_0"]["global"]
            # set_transmitter_mask mutates these arrays: preserve this endpoint first.
            sinr = np.asarray(global_info["sinr_matrix"], dtype=np.float64).copy()
            connected = np.asarray(global_info["connections"], dtype=bool).copy()
            active = raw["transmitter_mask"][tick]
            if (sinr.shape != (5, 50) or connected.shape != (5, 50)
                    or not np.isfinite(sinr[active]).all() or not np.isneginf(sinr[~active]).all()):
                raise AssertionError("only silent native SINR rows may be negative infinity")
            served = int(connected.sum())
            quality = float(np.clip((sinr[connected] - 3.) / 30., 0., 1.).sum() / max(served, 1))
            reward = sum(float(x) for x in info["rewards_dict"].values())
            if not np.isclose(reward, .7 * served / 50. + .3 * quality, rtol=0., atol=1e-12):
                raise AssertionError("native reward differs from its preserved endpoint")
            after = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64).copy()
            expected = np.clip(raw["positions"][tick] + actual.astype(np.float64) * 30., ep.LOW, ep.HIGH)
            if not np.array_equal(after, expected):
                raise AssertionError("native discrete motion law changed")
            raw["positions"][tick + 1] = after
            raw["sinr"][tick], raw["connections"][tick] = sinr, connected
            raw["served"][tick], raw["sinr_quality"][tick], raw["reward"][tick] = served, quality, reward
            raw["completed_steps"][...] = tick + 1
            inflight["completed_steps"] = tick + 1
            if bool(terminated or truncated) != (tick + 1 == protocol.horizon):
                raise AssertionError("unexpected native episode boundary")
            if pending is not None and tick + 1 == pending_at:
                inflight["phase"] = "mask_arrival"
                wall, cpu = clock(), cpu_clock()
                if coordinator != "E":
                    actual = np.asarray(pending["commands"], dtype=np.float32).copy()
                current_mask = int(pending["mask"])
                counts["mask_setter_calls"] += 1
                env.env.set_transmitter_mask(ep.mask_array(current_mask))
                counts["mask_setter_returns"] += 1
                next_obs = env._dict_to_array({agent: env.env._get_observation(agent) for agent in env.agents})
                times["mask_refresh_wall_seconds"] += clock() - wall
                times["mask_refresh_cpu_seconds"] += cpu_clock() - cpu
                pending, pending_at = None, None
            obs = _observation(next_obs)
        check()
        if pending is not None:
            raise AssertionError("terminal pending delivery violates selected clock")
        completed = True
    finally:
        raw["terminal_observation"] = obs.copy()
        raw["terminal_mask"] = ep.mask_array(current_mask)
        if records:
            for key in records[0]:
                raw[key] = np.asarray([record[key] for record in records])
        raw["episode_complete"] = np.array(completed)
        wall, cpu = clock(), cpu_clock()
        np.savez_compressed(path, **raw)
        identity = file_identity(path)
        identity["path"] = str(path.relative_to(out))
        times["raw_write_wall_seconds"] += clock() - wall
        times["raw_write_cpu_seconds"] += cpu_clock() - cpu
        inflight.update(raw=identity, policy_counts={} if team is None else team.counts(),
                        times=times.copy(), partial_coordinator_work_may_be_unknown=(inflight["phase"] == "coordinator_call"),
                        partial_local_work_may_be_unknown=(inflight["phase"] == "local_decision"))
    row = dict(arm=arm, world=int(world), tape=int(tape), policy_sha256=policy_sha,
               **episode_metrics(raw, arm), **times, policy_counts=team.counts(),
               coordinator_counts={key: int(raw["coord_" + key].sum()) for key in COORD_COUNTERS},
               scheduler_wall_seconds=float(raw["coord_wall_seconds"].sum()),
               scheduler_cpu_seconds=float(raw["coord_cpu_seconds"].sum()),
               raw=identity, initial_state_sha256=array_digest(raw["positions"][0], users),
               bundle_sha256=array_digest(bundle["public"], bundle["private_depart"], bundle["private_tail"])
               if family != "C" else None,
               cpu_seconds=cpu_clock() - start_cpu, wall_seconds=clock() - start_wall)
    counts["complete_episodes"] += 1
    inflight.clear()
    return row
