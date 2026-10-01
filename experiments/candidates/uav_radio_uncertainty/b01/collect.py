"""Complete actual trajectories; manager inputs are copies of the paid reports only."""

from __future__ import annotations

from collections import Counter
import time

import numpy as np

from envs.pettingzoo.uav_radio import service_metrics
from experiments.candidates.uav_local_history.b01.controller import LocalController
from experiments.candidates.uav_user_waiting.b02.predictor import controller_nav_index
from experiments.candidates.uav_user_waiting.b02.storage import pack_records
from . import contract as c
from . import protocol as p
from .manager import Scheduler


def empty_raw(horizon, world, arm, sigma):
    n, u, k = c.N_UAVS, c.N_USERS, horizon // c.HOLD
    raw = dict(world=np.array(world), arm=np.array(arm), horizon=np.array(horizon),
               sigma=np.array(sigma), completed_steps=np.array(0), completed_reports=np.array(0))
    for name, shape in dict(positions=(horizon+1,n,3), residual=(horizon+1,n,u),
        loss=(horizon+1,n,u), state_sinr=(horizon+1,n,u), peer_sinr=(horizon+1,n,n),
        sinr=(horizon,n,u), reward=(horizon,), quality=(horizon,), served=(horizon,),
        c_wall=(k,), c_cpu=(k,), round_wall=(k,), round_cpu=(k,)).items():
        raw[name] = np.full(shape, np.nan, np.float64)
    for name, shape in dict(observations=(horizon+1,n,104), postmove_observations=(horizon,n,104),
        commands=(horizon,n,3), proposals=(k,n,3)).items():
        raw[name] = np.full(shape, np.nan, np.float32)
    raw.update(connections=np.zeros((horizon,n,u),bool), state_connections=np.zeros((horizon+1,n,u),bool),
        mask=np.full(horizon,-1,np.int64), state_mask=np.full(horizon+1,-1,np.int64),
        c_attempted=np.zeros((k,n),bool), c_completed=np.zeros((k,n),bool),
        post_c_nav=np.full((k,n),255,np.uint8), loss_codes=np.zeros((k,n,u),np.uint8),
        sensor_completed=np.zeros(k,bool), pilot_attempted=np.zeros(k,bool),
        refresh_attempted=np.zeros(horizon+1,bool), refresh_completed=np.zeros(horizon+1,bool))
    for name in ("clipped_low", "clipped_high", "edge_low", "edge_high"):
        raw[name] = np.zeros((k,n,u),bool)
    return raw


def save_state(raw, tick, snapshot, observation, mask):
    for target, source in (("positions","positions"),("residual","residual"),("loss","user_loss"),
        ("state_sinr","sinr"),("state_connections","connections"),("peer_sinr","peer_sinr")):
        raw[target][tick] = snapshot[source]
    raw["observations"][tick] = observation
    raw["state_mask"][tick] = mask


def constructor_witness(env):
    snapshot = env.env.physical_snapshot()
    observations, _ = env.env.constructor_reset_output
    return dict(**{key: np.asarray(value) for key, value in snapshot.items() if key != "counters"},
        observations=env._dict_to_array(observations),
        counter_names=np.asarray(list(snapshot["counters"])),
        counter_values=np.asarray(list(snapshot["counters"].values()),np.int64),
        horizon=np.array(env.env.max_steps),sigma=np.array(env.env.sigma))


def collect_episode(env, world, arm, *, horizon=c.HORIZON):
    wall, cpu = time.perf_counter(), time.process_time()
    initial_counts = env.env.physical_counters
    raw = empty_raw(horizon, world, arm, env.env.sigma)
    records, diagnostics, failure = [], [], None
    controllers = [LocalController(history=False) for _ in range(c.N_UAVS)]
    proposals = np.zeros((c.N_UAVS,3),np.float32)
    actual, mask, pending = proposals.copy(), p.ALL_ON, None
    try:
        obs, _ = env.reset(seed=int(world))
        snapshot = env.env.physical_snapshot()
        raw["users"] = snapshot["users"]
        map_packet = p.encode_map(raw["users"])
        raw["map_packet"] = np.frombuffer(map_packet,np.uint8).copy()
        manager = Scheduler(arm, map_packet, int(world), horizon=horizon)
        save_state(raw, 0, snapshot, obs, mask)
        for tick in range(horizon):
            if tick % c.HOLD == 0:
                index = tick // c.HOLD
                started, cpu_started = time.perf_counter(), time.process_time()
                raw["pilot_attempted"][index] = True
                # The sensor is state-boundary CSI; all 250 registered links are
                # measured even when payload transmitters are silent.
                codes, saturation = p.encode_losses(snapshot["user_loss"])
                raw["sensor_completed"][index] = True
                raw["loss_codes"][index] = codes
                for name, values in saturation.items():
                    raw[name][index] = values
                c_wall, c_cpu = time.perf_counter(), time.process_time()
                one_round = []
                try:
                    for member, controller in enumerate(controllers):
                        raw["c_attempted"][index,member] = True
                        command, diagnostic = controller.act(obs[member].copy(), tick)
                        raw["c_completed"][index,member] = True
                        proposals[member] = command
                        one_round.append(diagnostic)
                finally:
                    diagnostics.append(one_round)
                    raw["c_wall"][index] = time.perf_counter()-c_wall
                    raw["c_cpu"][index] = time.process_time()-c_cpu
                if tick == 0:
                    actual = proposals.copy()
                raw["proposals"][index] = proposals
                nav = np.asarray([controller_nav_index(x) for x in controllers],np.uint8)
                raw["post_c_nav"][index] = nav
                result = None
                try:
                    result = manager.decide(obs[:,:3].copy(), actual.copy(), proposals.copy(), tick,
                        mask, nav, codes.copy(), started=started, cpu_started=cpu_started)
                finally:
                    record = result["record"] if result is not None else manager.last_record
                    if record is not None:
                        records.append(record)
                        raw["round_wall"][index] = record.get("wall_seconds",time.perf_counter()-started)
                        raw["round_cpu"][index] = record.get("cpu_seconds",time.process_time()-cpu_started)
                pending = (tick + c.DELIVERY, result)
                raw["completed_reports"][...] = index+1
            raw["commands"][tick], raw["mask"][tick] = actual, mask
            next_obs, _, terminated, truncated, info = env.step(actual.copy())
            # The arrival refresh may mutate native arrays. Copy postmove service
            # and the actual emitted observation before the refresh.
            moved = env.env.physical_snapshot()
            raw["sinr"][tick], raw["connections"][tick] = moved["sinr"], moved["connections"]
            raw["postmove_observations"][tick] = next_obs
            reward = sum(float(value) for value in info["rewards_dict"].values())
            native = service_metrics(moved["sinr"], moved["connections"])
            p.require(abs(reward-native["J"]) <= 1e-12, "native team reward differs")
            raw["reward"][tick], raw["served"][tick], raw["quality"][tick] = reward,native["served"],native["quality"]
            raw["completed_steps"][...] = tick+1
            # Preserve the paid transition before a terminal check or arrival
            # refresh can fail. A successful refresh replaces only this state view.
            save_state(raw,tick+1,moved,next_obs,mask)
            p.require(bool(terminated or truncated) == (tick+1 == horizon), "terminal boundary differs")
            if pending is not None and tick+1 == pending[0]:
                result = pending[1]
                actual, mask = result["commands"].copy(), int(result["mask"])
                raw["refresh_attempted"][tick+1] = True
                refreshed = env.env.set_transmitter_mask(p.mask_array(mask))
                raw["refresh_completed"][tick+1] = True
                next_obs = env._dict_to_array(refreshed)
                snapshot = env.env.physical_snapshot()
                pending = None
            else:
                snapshot = moved
            obs = next_obs
            save_state(raw,tick+1,snapshot,obs,mask)
    except Exception as exc:
        failure = exc
    finally:
        final_counts = env.env.physical_counters
        raw["physical_counter_names"] = np.asarray(sorted(final_counts))
        raw["physical_counter_values"] = np.asarray([final_counts[k]-initial_counts.get(k,0)
                                                      for k in sorted(final_counts)],np.int64)
        raw["controller_counter_names"] = np.asarray(list(controllers[0].counters))
        raw["controller_counter_values"] = np.asarray([[x.counters[k] for k in controllers[0].counters]
                                                         for x in controllers],np.int64)
        final_snapshot = None
        if failure is not None:
            try:
                final_snapshot = env.env.physical_snapshot()
            except Exception as snapshot_error:
                final_snapshot = dict(error_type=type(snapshot_error).__name__,error_message=str(snapshot_error))
        raw.update(pack_records(dict(decisions=records,c_diagnostics=diagnostics,failure_snapshot=final_snapshot)))
        raw["failure_type"] = np.array("" if failure is None else type(failure).__name__)
        raw["failure_message"] = np.array("" if failure is None else str(failure))
    counts = Counter()
    for record in records:
        counts.update(record["counts"])
    metadata = dict(world=int(world),arm=arm,steps=int(raw["completed_steps"]),
        wall_seconds=time.perf_counter()-wall,cpu_seconds=time.process_time()-cpu,
        physical_counts=dict(zip(raw["physical_counter_names"].tolist(),raw["physical_counter_values"].tolist())),
        controller_counts=dict(zip(raw["controller_counter_names"].tolist(),
                                  raw["controller_counter_values"].sum(axis=0).tolist())),
        model_counts=dict(counts),failure=None if failure is None else dict(type=type(failure).__name__,message=str(failure)))
    return raw, metadata, failure
