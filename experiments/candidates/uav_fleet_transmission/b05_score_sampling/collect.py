"""Complete native episodes, without evaluator information entering any policy."""
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.collect import _check_all_on, _timed_query
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import LOW, HIGH, array_digest
from .policies import FixedPolicy, ORDINARY_ARMS
from .reading import episode_metrics


def collect_episode(env, *, arm, world, tape, protocol, actor, out, counts, inflight):
    started = time.perf_counter(), time.process_time()
    times = {f"{component}_{clock}_seconds": 0. for component in
             ("reset", "decision_query", "native_step", "raw_write") for clock in ("wall", "cpu")}
    root = protocol.sampling_roots[max(tape, 0)]
    policies = [FixedPolicy(arm, actor, world=world, agent=i, sampling_root=root) for i in range(5)]
    raw = {key: [] for key in ("observations", "commands", "positions", "reward", "served", "sinr_quality",
                               "sinr", "connections", "transmitter_mask")}
    decision = {key: [] for key in ("nav_pre", "nav_next", "features", "fallback", "action_index", "memo_hit",
                                    "n_current", "n_peers", "probabilities", "innovation", "entropy",
                                    "behavior_entropy", "chosen_probability", "logp")}
    if arm in ORDINARY_ARMS:
        decision.update(c_index=[], policy_scores=[], policy_served=[])
    else:
        decision["logits"] = []
    inflight.update(arm=arm, world=int(world), tape=tape, tick=0, native_steps=0, policy_counts={})
    target = Path(out) / "raw" / f"{arm}_{world}_t{tape}.npz"
    if target.exists() or target.with_suffix(".partial.npz").exists():
        raise FileExistsError("episode output already exists")
    users, obs = None, None
    try:
        wall, cpu = time.perf_counter(), time.process_time()
        counts["explicit_resets"] += 1
        obs, info = env.reset(seed=int(world))
        times["reset_wall_seconds"] += time.perf_counter() - wall
        times["reset_cpu_seconds"] += time.process_time() - cpu
        obs = np.asarray(obs, dtype=np.float32)
        if obs.shape != (5, 104) or not np.isfinite(obs).all():
            raise ValueError("five finite original local observation rows required")
        _check_all_on(env)
        positions = np.array(info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
        users = np.array(info["state_info"]["user_positions"], dtype=np.float64, copy=True)
        raw["positions"].append(positions)
        navs = np.array([initial_nav(r) for r in obs], dtype=np.int64)
        commands = np.zeros((5, 3), dtype=np.float32)
        for tick in range(protocol.horizon):
            inflight["tick"] = tick
            if tick % 4 == 0:
                decision["nav_pre"].append(navs.copy())
                diagnostics = []
                for agent, policy in enumerate(policies):
                    count_key = "ordinary_queries" if arm in ORDINARY_ARMS else "student_queries"
                    counts[count_key] += 1
                    pd = _timed_query(policy, obs[agent], tick, navs[agent], times, "decision_query")
                    counts["sampled_draws"] += int(arm != "C")
                    counts["score_tail_evaluations"] += int(arm == "G")
                    if not np.array_equal(pd["command"], COMMANDS[int(pd["action_index"])]):
                        raise AssertionError("category/command disagreement")
                    commands[agent] = pd["command"]
                    navs[agent] = pd["next_nav"]
                    diagnostics.append(pd)
                decision["nav_next"].append(navs.copy())
                for key in decision:
                    if key in ("nav_pre", "nav_next"):
                        continue
                    source = {"policy_scores": "scores", "policy_served": "served"}.get(key, key)
                    decision[key].append([pd[source] for pd in diagnostics])
            raw["observations"].append(obs.copy())
            raw["commands"].append(commands.copy())
            raw["transmitter_mask"].append(_check_all_on(env))
            wall, cpu = time.perf_counter(), time.process_time()
            counts["native_step_calls"] += 1
            next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
            counts["native_steps"] += 1
            inflight["native_steps"] += 1
            times["native_step_wall_seconds"] += time.perf_counter() - wall
            times["native_step_cpu_seconds"] += time.process_time() - cpu
            reward, served, quality = native_reading(next_info)
            after = np.array(next_info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
            if not np.array_equal(after, np.clip(positions + commands.astype(np.float64) * 30., LOW, HIGH)):
                raise AssertionError("native motion changed")
            if not np.array_equal(users, next_info["state_info"]["user_positions"]):
                raise AssertionError("static world user positions changed")
            global_info = next_info["infos_dict"]["uav_0"]["global"]
            raw["positions"].append(after)
            raw["reward"].append(reward)
            raw["served"].append(served)
            raw["sinr_quality"].append(quality)
            raw["sinr"].append(np.array(global_info["sinr_matrix"], dtype=np.float64, copy=True))
            raw["connections"].append(np.array(global_info["connections"], dtype=bool, copy=True))
            if bool(terminated or truncated) != (tick + 1 == protocol.horizon):
                raise AssertionError("native termination boundary changed")
            obs = np.asarray(next_obs, dtype=np.float32)
            if obs.shape != (5, 104) or not np.isfinite(obs).all():
                raise AssertionError("invalid next local observation")
            positions = after
        arrays = {name: np.asarray(values) for name, values in {**raw, **decision}.items()}
        arrays.update(initial_users=users, terminal_observation=obs.copy(),
                      decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64))
        wall, cpu = time.perf_counter(), time.process_time()
        np.savez_compressed(target, **arrays)
        identity = file_identity(target)
        identity["path"] = str(target.relative_to(out))
        times["raw_write_wall_seconds"] += time.perf_counter() - wall
        times["raw_write_cpu_seconds"] += time.process_time() - cpu
        row = dict(arm=arm, world=int(world), tape=tape, sampling_root=None if arm == "C" else root,
                   **episode_metrics(arrays), **times, policy_counts=sum_counts(p.counters for p in policies),
                   raw=identity, initial_state_sha256=array_digest(arrays["positions"][0], users),
                   cpu_seconds=time.process_time() - started[1], wall_seconds=time.perf_counter() - started[0])
        counts["complete_episodes"] += 1
        inflight.clear()
        return row
    except BaseException:
        inflight["policy_counts"] = sum_counts(p.counters for p in policies)
        inflight["times"] = times
        # Even a failing query or native call remains charged in counts/inflight.
        partial = {name: np.asarray(values) for name, values in {**raw, **decision}.items()}
        if users is not None:
            partial["initial_users"] = users
        if obs is not None:
            partial["last_observation"] = obs
        partial_path = target.with_suffix(".partial.npz")
        np.savez_compressed(partial_path, **partial)
        inflight["partial_raw"] = file_identity(partial_path)
        raise
