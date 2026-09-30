"""Own-trajectory local policy queries followed by the fixed joint sampler."""
from __future__ import annotations

from pathlib import Path
import time
import numpy as np

from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, MemoC, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.policies import StudentPolicy
from experiments.candidates.uav_fleet_adaptation.b02.collect import _check_all_on
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from .contract import ARMS
from .reading import episode_metrics
from .sampling import decode


def collect_episode(env, *, arm, world, tape, bundle, out, protocol, counts, actor, policy_sha, inflight):
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    if arm not in ARMS or ((arm == "C") != (tape == -1)):
        raise ValueError("unknown arm or deterministic tape identity")
    stochastic, student = arm != "C", arm.startswith("S_")
    if stochastic and bundle is None:
        raise ValueError("stochastic policy requires its evaluator-owned tape bundle")
    counts["explicit_reset_calls"] += 1
    obs, info = env.reset(seed=int(world))
    counts["explicit_resets"] += 1
    obs = np.asarray(obs, dtype=np.float32)
    if obs.shape != (5, 104) or not np.isfinite(obs).all():
        raise ValueError("five finite local observations required")
    _check_all_on(env)
    positions = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64).copy()
    users = np.asarray(info["state_info"]["user_positions"], dtype=np.float64).copy()
    navs = np.array([initial_nav(row) for row in obs], dtype=np.int64)
    # The disabled historical sampler never receives a scene seed or an actual ID.
    policies = ([StudentPolicy(actor, world=0, agent=0, sampled=False) for _ in range(5)]
                if student else [MemoC() for _ in range(5)])
    times = {f"{part}_{clock}_seconds": 0.0 for part in
             ("decision_query", "sampler", "native_step", "raw_write") for clock in ("wall", "cpu")}
    inflight.update(arm=arm, world=int(world), tape=int(tape),
                    policy_agents=[p.counters for p in policies], times=times)
    raw = {name: [] for name in ("observations", "commands", "reward", "served", "sinr_quality",
                                 "sinr", "connections", "transmitter_mask")}
    raw["positions"] = [positions.copy()]
    decision = {name: [] for name in ("nav_pre", "nav_next", "fallback", "action_index", "memo_hit",
                                      "features", "n_current", "n_peers", "modal_index", "probabilities")}
    decision.update({"logits": []} if student else {"policy_scores": [], "policy_served": []})
    if stochastic:
        decision.update({name: [] for name in ("departure_threshold", "tail_thresholds", "effective_probabilities",
                                              "departure_integer", "requested_departure", "public_integer",
                                              "private_depart_integer", "private_tail_integer")})
    commands = np.zeros((5, 3), dtype=np.float32)
    for tick in range(protocol.horizon):
        if tick % 4 == 0:
            pre, diagnostics, probabilities = navs.copy(), [], []
            # Every local base distribution is built before this decision's coin access.
            for agent in range(5):
                wall, cpu = time.perf_counter(), time.process_time()
                pd = policies[agent].query(obs[agent].copy(), tick, int(pre[agent]))
                times["decision_query_wall_seconds"] += time.perf_counter() - wall
                times["decision_query_cpu_seconds"] += time.process_time() - cpu
                p = (np.asarray(pd["probabilities"], dtype=np.float64).copy() if student
                     else np.full(27, .1 / 26 if stochastic else 0., dtype=np.float64))
                if not student:
                    p[int(pd["action_index"])] = .9 if stochastic else 1.
                if pd["features"].shape != (114,) or not np.array_equal(pd["features"][:103], obs[agent, :103]):
                    raise AssertionError("lawful feature provenance mismatch")
                probabilities.append(p)
                diagnostics.append(pd)
            sampled = []
            for agent, (pd, p) in enumerate(zip(diagnostics, probabilities)):
                navs[agent] = int(pd["next_nav"])
                if stochastic:
                    j = tick // 4
                    wall, cpu = time.perf_counter(), time.process_time()
                    result = decode(p, law=arm[-1], rank=agent, public=int(bundle["public"][j]),
                                    private_depart=int(bundle["private_depart"][j, agent]),
                                    private_tail=int(bundle["private_tail"][j, agent]))
                    times["sampler_wall_seconds"] += time.perf_counter() - wall
                    times["sampler_cpu_seconds"] += time.process_time() - cpu
                    counts["sampling_decisions"] += 1
                    sampled.append(result)
                    choice = result["action_index"]
                else:
                    choice = int(pd["action_index"])
                commands[agent] = COMMANDS[choice]
            decision["nav_pre"].append(pre)
            decision["nav_next"].append(navs.copy())
            for key in ("fallback", "memo_hit", "features", "n_current", "n_peers"):
                decision[key].append([d[key] for d in diagnostics])
            decision["action_index"].append([r["action_index"] for r in sampled] if stochastic
                                             else [d["action_index"] for d in diagnostics])
            decision["modal_index"].append([int(np.argmax(p)) for p in probabilities])
            decision["probabilities"].append(probabilities)
            if student:
                decision["logits"].append([d["logits"] for d in diagnostics])
            else:
                decision["policy_scores"].append([d["scores"] for d in diagnostics])
                decision["policy_served"].append([d["served"] for d in diagnostics])
            if stochastic:
                for key in ("departure_threshold", "tail_thresholds", "effective_probabilities",
                            "departure_integer", "requested_departure"):
                    decision[key].append([r[key] for r in sampled])
                decision["public_integer"].append(bundle["public"][j])
                decision["private_depart_integer"].append(bundle["private_depart"][j].copy())
                decision["private_tail_integer"].append(bundle["private_tail"][j].copy())
        raw["observations"].append(obs.copy())
        raw["commands"].append(commands.copy())
        raw["transmitter_mask"].append(_check_all_on(env))
        wall, cpu = time.perf_counter(), time.process_time()
        counts["native_step_calls"] += 1
        next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
        counts["native_steps"] += 1
        times["native_step_wall_seconds"] += time.perf_counter() - wall
        times["native_step_cpu_seconds"] += time.process_time() - cpu
        reward, served, quality = native_reading(next_info)
        after = np.asarray(next_info["state_info"]["uav_positions"], dtype=np.float64).copy()
        expected = np.clip(positions + commands.astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        if not np.array_equal(after, expected):
            raise AssertionError("fixed native motion contract changed")
        global_info = next_info["infos_dict"]["uav_0"]["global"]
        for key, value in (("positions", after), ("reward", reward), ("served", served), ("sinr_quality", quality),
                           ("sinr", np.asarray(global_info["sinr_matrix"], dtype=np.float64).copy()),
                           ("connections", np.asarray(global_info["connections"], dtype=bool).copy())):
            raw[key].append(value)
        if bool(terminated or truncated) != (tick + 1 == protocol.horizon):
            raise AssertionError("unexpected episode boundary")
        obs = np.asarray(next_obs, dtype=np.float32)
        if obs.shape != (5, 104) or not np.isfinite(obs).all():
            raise AssertionError("invalid next observation")
        positions = after
    arrays = {name: np.asarray(values) for name, values in {**raw, **decision}.items()}
    for name in ("departure_threshold", "tail_thresholds", "departure_integer", "public_integer",
                 "private_depart_integer", "private_tail_integer"):
        if name in arrays:
            arrays[name] = arrays[name].astype(np.uint64)
    arrays.update(initial_users=users, terminal_observation=obs.copy(),
                  decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64))
    path = Path(out) / "raw" / f"{arm}_w{world}_t{tape}.npz"
    if path.exists():
        raise FileExistsError("episode already exists; reconcile rather than repeat")
    wall, cpu = time.perf_counter(), time.process_time()
    np.savez_compressed(path, **arrays)
    identity = file_identity(path)
    identity["path"] = str(path.relative_to(out))
    times["raw_write_wall_seconds"] += time.perf_counter() - wall
    times["raw_write_cpu_seconds"] += time.process_time() - cpu
    row = dict(arm=arm, world=int(world), tape=int(tape), policy_sha256=policy_sha,
               **episode_metrics(arrays), **times, policy_counts=sum_counts(p.counters for p in policies),
               raw=identity, initial_state_sha256=array_digest(arrays["positions"][0], users),
               bundle_sha256=array_digest(bundle["public"], bundle["private_depart"], bundle["private_tail"])
               if stochastic else None,
               cpu_seconds=time.process_time() - start_cpu, wall_seconds=time.perf_counter() - start_wall)
    counts["complete_episodes"] += 1
    inflight.clear()
    return row
