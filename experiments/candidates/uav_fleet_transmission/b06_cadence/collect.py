"""Native collection with agent-private asynchronous queries and original block deadlines."""
from pathlib import Path
import time
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.collect import _check_all_on, _timed_query
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import LOW, HIGH, array_digest
from .gate import Cadence, remaining_motion_changed
from .policies import FixedPolicy, ORDINARY_ARMS
from .reading import episode_metrics


def collect_episode(env, *, arm, mode, world, tape, protocol, actor, out, counts, inflight):
    started = time.perf_counter(), time.process_time()
    times = {f"{part}_{clock}_seconds": 0. for part in
             ("reset", "gate", "decision_query", "native_step", "raw_write") for clock in ("wall", "cpu")}
    root = protocol.sampling_roots[max(tape, 0)]
    policies = [FixedPolicy(arm, actor, world=world, agent=i, sampling_root=root) for i in range(5)]
    gates = [Cadence(mode) for _ in range(5)]
    raw = {key: [] for key in ("observations", "commands", "positions", "reward", "served", "sinr_quality",
                               "sinr", "connections", "transmitter_mask", "query_mask", "own_count",
                               "count_loss", "extra_available", "extra_used")}
    decision = {key: [] for key in ("decision_ticks", "decision_agents", "query_kind", "held_before",
                 "remaining_motion_changed", "nav_pre", "nav_next", "features", "fallback", "action_index",
                 "memo_hit", "n_current", "n_peers", "probabilities", "innovation", "entropy",
                 "behavior_entropy", "chosen_probability", "logp")}
    decision.update(dict(c_index=[], policy_scores=[], policy_served=[]) if arm in ORDINARY_ARMS else dict(logits=[]))
    inflight.update(arm=arm, mode=mode, world=int(world), tape=tape, tick=0, native_steps=0, policy_counts={})
    target = Path(out) / "raw" / f"{arm}_{mode}_{world}_t{tape}.npz"
    if target.exists() or target.with_suffix(".partial.npz").exists():
        raise FileExistsError("episode output already exists")
    users = obs = initial_sinr = initial_connections = None
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
        # Native reset infos are empty. These evaluator-only copies never enter
        # a gate or policy; the latter receive only their original local row.
        initial_sinr = np.array(env.env.sinr_matrix, dtype=np.float64, copy=True)
        initial_connections = np.array(env.env.connections, dtype=bool, copy=True)
        raw["positions"].append(positions)
        navs = np.array([initial_nav(r) for r in obs], dtype=np.int64)
        commands = np.zeros((5, 3), dtype=np.float32)
        held = np.full(5, -1, dtype=np.int64)
        for tick in range(protocol.horizon):
            inflight["tick"] = tick
            wall, cpu = time.perf_counter(), time.process_time()
            if mode == "E":
                counts["count_decodes"] += 5
                counts["event_gate_checks"] += 5 * int(tick % 4 != 0)
            decisions = [gates[i].step(obs[i], tick) for i in range(5)]
            times["gate_wall_seconds"] += time.perf_counter() - wall
            times["gate_cpu_seconds"] += time.process_time() - cpu
            for field, source in (("query_mask", "query"), ("own_count", "count"), ("count_loss", "loss"),
                                  ("extra_available", "available"), ("extra_used", "used")):
                raw[field].append([d[source] for d in decisions])
            for agent, policy in enumerate(policies):
                if not decisions[agent]["query"]:
                    continue
                counts["ordinary_queries" if arm in ORDINARY_ARMS else "student_queries"] += 1
                pd = _timed_query(policy, obs[agent], tick, navs[agent], times, "decision_query")
                counts["sampled_draws"] += int(arm != "C")
                counts["score_tail_evaluations"] += int(arm == "G")
                if not np.array_equal(pd["command"], COMMANDS[int(pd["action_index"])]):
                    raise AssertionError("category/command disagreement")
                custom = dict(decision_ticks=tick, decision_agents=agent, query_kind=decisions[agent]["kind"],
                              held_before=int(held[agent]), nav_pre=int(navs[agent]), nav_next=int(pd["next_nav"]),
                              remaining_motion_changed=bool(held[agent] >= 0 and remaining_motion_changed(
                                  positions[agent], commands[agent], pd["command"], tick)))
                for key in decision:
                    source = {"policy_scores": "scores", "policy_served": "served"}.get(key, key)
                    decision[key].append(custom[key] if key in custom else pd[source])
                commands[agent], held[agent], navs[agent] = pd["command"], pd["action_index"], pd["next_nav"]
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
                raise AssertionError("static user positions changed")
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
                      initial_sinr=initial_sinr, initial_connections=initial_connections)
        wall, cpu = time.perf_counter(), time.process_time()
        np.savez_compressed(target, **arrays)
        identity = file_identity(target)
        identity["path"] = str(target.relative_to(out))
        times["raw_write_wall_seconds"] += time.perf_counter() - wall
        times["raw_write_cpu_seconds"] += time.process_time() - cpu
        row = dict(arm=arm, mode=mode, world=int(world), tape=tape, sampling_root=None if arm == "C" else root,
                   **episode_metrics(arrays), **times, policy_counts=sum_counts(p.counters for p in policies),
                   raw=identity, initial_state_sha256=array_digest(arrays["positions"][0], users,
                                                                   initial_sinr, initial_connections),
                   cpu_seconds=time.process_time() - started[1], wall_seconds=time.perf_counter() - started[0])
        counts["complete_episodes"] += 1
        inflight.clear()
        return row
    except BaseException:
        inflight["policy_counts"] = sum_counts(p.counters for p in policies)
        inflight["times"] = times
        partial = {name: np.asarray(values) for name, values in {**raw, **decision}.items()}
        for key, value in (("initial_users", users), ("last_observation", obs),
                           ("initial_sinr", initial_sinr), ("initial_connections", initial_connections)):
            if value is not None:
                partial[key] = value
        partial_path = target.with_suffix(".partial.npz")
        np.savez_compressed(partial_path, **partial)
        inflight["partial_raw"] = file_identity(partial_path)
        raise
