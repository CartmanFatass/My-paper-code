"""The selected 672 complete native trajectories, with full saved policy laws."""
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b06_count_development.collect import _all_on, _query
from experiments.candidates.uav_fleet_adaptation.b06_count_development.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b06_count_development.environment import reset_layout
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import ARMS, DIRECT, NEURAL, ORDINARY, array_digest
from .policies import Policy
from .reading import episode_metrics


def collect_episode(env, *, arm, world, tape, actor, policy_sha, out, protocol, counts, inflight):
    wall, cpu = time.perf_counter(), time.process_time()
    if (arm not in ARMS or world not in protocol.worlds or env.n_uavs != 5
            or ((actor is None) != (arm in ORDINARY))
            or ((tape is None) != (arm == "C")) or tape not in (None, 0, 1)):
        raise ValueError("invalid B07 final episode identity")
    root = None if arm == "C" else protocol.evaluation_roots[tape]
    times = {f"{component}_{clock}_seconds": 0. for component in
             ("reset_layout", "decision_query", "native_step", "raw_write") for clock in ("wall", "cpu")}
    reset_wall, reset_cpu = time.perf_counter(), time.process_time()
    obs, info, seven = reset_layout(env, world, protocol, counts)
    times["reset_layout_wall_seconds"] = time.perf_counter() - reset_wall
    times["reset_layout_cpu_seconds"] = time.process_time() - reset_cpu
    obs = np.asarray(obs, dtype=np.float32)
    if obs.shape != (5, 104) or not np.isfinite(obs).all():
        raise ValueError("invalid initial local observations")
    _all_on(env, 5)
    positions = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64).copy()
    users = np.asarray(info["state_info"]["user_positions"], dtype=np.float64).copy()
    initial = dict(initial_users=users, initial_seven_uavs=seven,
                   initial_sinr=np.asarray(env.env.sinr_matrix).copy(),
                   initial_peer_sinr=np.asarray(env.env.uav_sinr_matrix).copy(),
                   initial_connections=np.asarray(env.env.connections).copy())
    navs = np.asarray([initial_nav(obs[i], 5) for i in range(5)], dtype=np.int64)
    policies = [Policy(arm, actor, world=world, agent=i, sampling_root=root) for i in range(5)]
    inflight.update(arm=arm, world=world, tape=tape, policy_agents=[p.counters for p in policies], times=times)
    raw = {k: [] for k in ("observations", "commands", "reward", "served", "sinr_quality", "sinr", "peer_sinr",
                           "connections", "transmitter_mask", "terminated", "truncated")}
    raw["positions"] = [positions.copy()]
    decision = {k: [] for k in ("nav_pre", "nav_next", "fallback", "action_index", "memo_hit", "features",
                                "n_current", "n_peers", "probabilities", "innovation", "entropy")}
    if arm not in NEURAL:
        decision.update({k: [] for k in ("policy_scores", "policy_served", "c_index")})
    if arm in (*NEURAL, *DIRECT):
        decision["logits"] = []
    if arm in DIRECT:
        decision["parent_probabilities"] = []
    commands = np.zeros((5, 3), dtype=np.float32)
    for tick in range(protocol.horizon):
        inflight["tick"] = tick
        if tick % 4 == 0:
            answers, before = [], navs.copy()
            for agent in range(5):
                counts["policy_query_calls"] += 1
                answer = _query(policies[agent], obs[agent], tick, navs[agent], times, "decision_query")
                counts["policy_decisions"] += 1
                counts["sampled_draws"] += int(arm != "C")
                if (answer["features"].shape != (114,)
                        or not np.array_equal(answer["features"][:103], obs[agent, :103])):
                    raise AssertionError("feature provenance mismatch")
                commands[agent], navs[agent] = answer["command"], int(answer["next_nav"])
                if not np.array_equal(commands[agent], COMMANDS[answer["action_index"]]):
                    raise AssertionError("categorical command mismatch")
                answers.append(answer)
            decision["nav_pre"].append(before)
            decision["nav_next"].append(navs.copy())
            for key in decision:
                if key in ("nav_pre", "nav_next"):
                    continue
                source = {"policy_scores": "scores", "policy_served": "served"}.get(key, key)
                decision[key].append([answer[source] for answer in answers])
        raw["observations"].append(obs.copy())
        raw["commands"].append(commands.copy())
        raw["transmitter_mask"].append(_all_on(env, 5))
        step_wall, step_cpu = time.perf_counter(), time.process_time()
        counts["native_step_calls"] += 1
        next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
        counts["native_steps"] += 1
        counts["native_uav_ticks"] += 5
        counts["native_dense_slots"] += 275
        times["native_step_wall_seconds"] += time.perf_counter() - step_wall
        times["native_step_cpu_seconds"] += time.process_time() - step_cpu
        if set(next_info["rewards_dict"]) != {f"uav_{i}" for i in range(5)}:
            raise AssertionError("native reward roster changed")
        reward, served, quality = native_reading(next_info)
        global_info = next_info["infos_dict"]["uav_0"]["global"]
        after = np.asarray(next_info["state_info"]["uav_positions"], dtype=np.float64).copy()
        if not np.array_equal(after, np.clip(positions + commands.astype(np.float64) * 30.,
                                            [0., 0., 50.], [1000., 1000., 150.])):
            raise AssertionError("native requested motion mismatch")
        raw["positions"].append(after)
        for key, value in (("reward", reward), ("served", served), ("sinr_quality", quality),
                           ("sinr", np.asarray(global_info["sinr_matrix"]).copy()),
                           ("peer_sinr", np.asarray(env.env.uav_sinr_matrix).copy()),
                           ("connections", np.asarray(global_info["connections"]).copy()),
                           ("terminated", bool(terminated)), ("truncated", bool(truncated))):
            raw[key].append(value)
        if bool(terminated) != (tick + 1 == protocol.horizon) or bool(truncated):
            raise AssertionError("unexpected native terminal boundary")
        obs = np.asarray(next_obs, dtype=np.float32)
        if obs.shape != (5, 104) or not np.isfinite(obs).all():
            raise AssertionError("invalid next observations")
        positions = after
    arrays = {key: np.asarray(value) for key, value in {**raw, **decision}.items()}
    arrays.update(initial, terminal_observation=obs.copy(),
                  decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64))
    identifier = f"evaluation_{arm}_w{world}_t{tape}"
    path = Path(out) / "raw" / (identifier + ".npz")
    if path.exists():
        raise FileExistsError("episode identity already exists")
    write_wall, write_cpu = time.perf_counter(), time.process_time()
    np.savez_compressed(path, **arrays)
    artifact = file_identity(path)
    artifact["path"] = str(path.relative_to(out))
    times["raw_write_wall_seconds"] = time.perf_counter() - write_wall
    times["raw_write_cpu_seconds"] = time.process_time() - write_cpu
    row = dict(id=identifier, kind="evaluation", arm=arm, world=world, tape=tape, n=5,
               sampling_root=root, temperature=2. if arm == "Bstar0" else (1. if actor is not None else None),
               policy_sha256=policy_sha, **episode_metrics(arrays), **times,
               policy_counts=sum_counts(p.counters for p in policies), raw=artifact,
               initial_state_sha256=array_digest(arrays["positions"][0], users),
               shared_layout_sha256=array_digest(users, seven),
               cpu_seconds=time.process_time() - cpu, wall_seconds=time.perf_counter() - wall,
               timing_scope="discarded reset, paired refresh, all queries/transitions/checks and compressed raw write")
    counts["evaluation_episodes"] += 1
    inflight.clear()
    return row
