"""One complete native episode with pre-step private queries and held commands."""
from pathlib import Path
import time
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.collect import _check_all_on, _timed_query
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from experiments.candidates.uav_fleet_transmission.b06_cadence.policies import FixedPolicy
from .contract import LOW, HIGH, STRATA, array_digest
from .reading import TIMED_PARTS, episode_metrics
from .schedule import hold_ticks, physical_hold_changed, query_due


def collect_episode(env, *, arm, schedule, world, q, tape, protocol, out, counts, inflight):
    started = time.perf_counter(), time.process_time()
    if (arm, tape) not in STRATA:
        raise ValueError("undeclared program/tape stratum")
    times = {f"{part}_{clock}_seconds": 0. for part in TIMED_PARTS for clock in ("wall", "cpu")}
    wall, cpu = time.perf_counter(), time.process_time()
    offsets, phases = protocol.phase_offsets(world), protocol.phases(world, q, schedule)
    times["schedule_wall_seconds"] += time.perf_counter() - wall
    times["schedule_cpu_seconds"] += time.process_time() - cpu
    root = protocol.sampling_roots[max(tape, 0)]
    policies = [FixedPolicy(arm, None, world=world, agent=i, sampling_root=root) for i in range(5)]
    raw = {key: [] for key in ("observations", "commands", "positions", "reward", "served", "sinr_quality",
                               "sinr", "connections", "transmitter_mask", "query_mask")}
    decision = {key: [] for key in ("decision_ticks", "decision_agents", "decision_phases", "hold_ticks",
                 "next_deadline", "held_before", "category_changed", "physical_hold_changed",
                 "nav_pre", "nav_next", "features", "fallback", "action_index", "memo_hit", "n_current",
                 "n_peers", "probabilities", "innovation", "entropy", "behavior_entropy",
                 "chosen_probability", "logp", "c_index", "policy_scores", "policy_served")}
    inflight.update(arm=arm, schedule=schedule, world=world, q=q, tape=tape, phases=phases.tolist(),
                    tick=0, native_steps=0, policy_counts={})
    target = Path(out) / "raw" / f"{arm}_{schedule}_{world}_q{q}_t{tape}.npz"
    if target.exists() or target.with_suffix(".partial.npz").exists():
        raise FileExistsError("episode output already exists")
    users = obs = initial_sinr = initial_connections = None
    try:
        wall, cpu = time.perf_counter(), time.process_time()
        counts["explicit_resets"] += 1
        obs, info = env.reset(seed=world)
        times["reset_wall_seconds"] += time.perf_counter() - wall
        times["reset_cpu_seconds"] += time.process_time() - cpu
        obs = np.array(obs, dtype=np.float32, copy=True)
        if obs.shape != (5, 104) or not np.isfinite(obs).all():
            raise ValueError("five finite original local observation rows required")
        _check_all_on(env)
        positions = np.array(info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
        users = np.array(info["state_info"]["user_positions"], dtype=np.float64, copy=True)
        # Native reset info is empty. These evaluator-only arrays never enter a policy.
        initial_sinr = np.array(env.env.sinr_matrix, dtype=np.float64, copy=True)
        initial_connections = np.array(env.env.connections, dtype=bool, copy=True)
        raw["positions"].append(positions)
        navs = np.array([initial_nav(row) for row in obs], dtype=np.int64)
        commands, held = np.zeros((5, 3), dtype=np.float32), np.full(5, -1, dtype=np.int64)
        for tick in range(protocol.horizon):
            inflight["tick"] = tick
            obs.setflags(write=False)
            raw["observations"].append(obs.copy())
            wall, cpu = time.perf_counter(), time.process_time()
            query = np.array([query_due(tick, phase) for phase in phases], dtype=bool)
            lengths = [hold_ticks(tick, int(phases[i]), protocol.horizon) if query[i] else 0 for i in range(5)]
            counts["schedule_checks"] += 5
            times["schedule_wall_seconds"] += time.perf_counter() - wall
            times["schedule_cpu_seconds"] += time.process_time() - cpu
            raw["query_mask"].append(query)
            for agent, policy in enumerate(policies):
                if not query[agent]:
                    continue
                counts["ordinary_queries"] += 1
                pd = _timed_query(policy, obs[agent], tick, navs[agent], times, "decision_query")
                counts["sampled_draws"] += int(arm == "Q10")
                if not np.array_equal(pd["command"], COMMANDS[int(pd["action_index"])]):
                    raise AssertionError("category/command disagreement")
                previous_exists = bool(held[agent] >= 0)
                custom = dict(decision_ticks=tick, decision_agents=agent, decision_phases=int(phases[agent]),
                              hold_ticks=lengths[agent], next_deadline=tick + lengths[agent],
                              held_before=int(held[agent]), nav_pre=int(navs[agent]), nav_next=int(pd["next_nav"]),
                              category_changed=bool(previous_exists and held[agent] != pd["action_index"]),
                              physical_hold_changed=bool(previous_exists and physical_hold_changed(
                                  positions[agent], commands[agent], pd["command"], lengths[agent])))
                for key in decision:
                    source = {"policy_scores": "scores", "policy_served": "served"}.get(key, key)
                    decision[key].append(custom[key] if key in custom else pd[source])
                commands[agent], held[agent], navs[agent] = pd["command"], pd["action_index"], pd["next_nav"]
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
            if bool(terminated or truncated) != (tick == protocol.horizon - 1):
                raise AssertionError("complete fixed horizon changed")
            _check_all_on(env)
            global_info = next_info["infos_dict"]["uav_0"]["global"]
            raw["positions"].append(after)
            raw["reward"].append(reward)
            raw["served"].append(served)
            raw["sinr_quality"].append(quality)
            raw["sinr"].append(np.array(global_info["sinr_matrix"], dtype=np.float64, copy=True))
            raw["connections"].append(np.array(global_info["connections"], dtype=bool, copy=True))
            obs = np.array(next_obs, dtype=np.float32, copy=True)
            if obs.shape != (5, 104) or not np.isfinite(obs).all():
                raise AssertionError("invalid next local observation")
            positions = after
        arrays = {name: np.asarray(values) for name, values in {**raw, **decision}.items()}
        arrays.update(initial_users=users, terminal_observation=obs.copy(), phases=phases, phase_offsets=offsets,
                      initial_sinr=initial_sinr, initial_connections=initial_connections)
        wall, cpu = time.perf_counter(), time.process_time()
        np.savez_compressed(target, **arrays)
        identity = file_identity(target)
        identity["path"] = str(target.relative_to(out))
        times["raw_write_wall_seconds"] += time.perf_counter() - wall
        times["raw_write_cpu_seconds"] += time.process_time() - cpu
        row = dict(arm=arm, schedule=schedule, world=world, q=q, tape=tape,
                   phases=phases.tolist(), phase_offsets=offsets.tolist(), sampling_root=None if arm == "C" else root,
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
        partial.update(phases=phases, phase_offsets=offsets)
        for key, value in (("initial_users", users), ("last_observation", obs),
                           ("initial_sinr", initial_sinr), ("initial_connections", initial_connections)):
            if value is not None:
                partial[key] = value
        partial_path = target.with_suffix(".partial.npz")
        np.savez_compressed(partial_path, **partial)
        inflight["partial_raw"] = file_identity(partial_path)
        raise
