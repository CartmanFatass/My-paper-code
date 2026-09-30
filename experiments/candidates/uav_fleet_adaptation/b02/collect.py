"""Complete native episodes with actor-only local inputs and evaluator-only truth."""
from __future__ import annotations

from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import array_digest
from .controllers import COMMANDS, MemoC, MemoC7, initial_nav
from .policies import FeatureMemo, StudentPolicy
from .reading import episode_metrics, sum_counts


def _timed_query(controller, row, tick, nav, times, component):
    wall, cpu = time.perf_counter(), time.process_time()
    value = controller.query(row.copy(), tick, int(nav))
    times[component + "_wall_seconds"] += time.perf_counter() - wall
    times[component + "_cpu_seconds"] += time.process_time() - cpu
    return value


def _check_all_on(env):
    mask = np.asarray(env.env.transmitter_mask)
    if mask.dtype != np.dtype(bool) or mask.shape != (5,) or not mask.all():
        raise AssertionError("current all-on host contract violated")
    return mask.copy()


def collect_episode(env, *, arm, world, out, protocol, counts, kind,
                    actor=None, phase=None, policy_sha=None, inflight=None):
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    training = kind == "training"
    if kind not in ("training", "evaluation"):
        raise ValueError("unknown collection kind")
    if training and phase not in (0, 1, 2):
        raise ValueError("training phase must be declared")
    obs, info = env.reset(seed=int(world))
    counts["explicit_resets"] += 1
    obs = np.asarray(obs, dtype=np.float32)
    if obs.shape != (5, 104) or not np.isfinite(obs).all():
        raise ValueError("five finite 104-field observation rows required")
    _check_all_on(env)
    # These copies never enter a controller, feature builder or label query.
    positions = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64).copy()
    users = np.asarray(info["state_info"]["user_positions"], dtype=np.float64).copy()
    navs = np.array([initial_nav(obs[i]) for i in range(5)], dtype=np.int64)
    teachers = [MemoC() for _ in range(5)] if training else []
    feature_memos = [FeatureMemo() for _ in range(5)] if training and phase == 0 else []
    if training and phase == 0:
        policies = teachers  # One original-C query supplies execution and label.
    elif actor is not None:
        policies = [StudentPolicy(actor, world=world, agent=i, sampled=arm == "S_sampled",
                                  sampling_root=protocol.sampling_root) for i in range(5)]
    elif arm == "C_memo":
        policies = [MemoC() for _ in range(5)]
    elif arm == "C7_memo":
        policies = [MemoC7() for _ in range(5)]
    else:
        raise ValueError("no policy for arm")
    times = {f"{component}_{clock}_seconds": 0.0 for component in
             ("decision_query", "expert_label", "expert_features", "native_step", "raw_write")
             for clock in ("wall", "cpu")}
    if inflight is not None:
        # Retain live references, not a stale pre-episode snapshot. The study's
        # exception path can recover actual recorded query work even before a
        # complete trajectory/row exists. Interrupted-call internals stay unknown.
        inflight.update(arm=arm, world=int(world), kind=kind, phase=phase,
                        policy_agents=[p.counters for p in policies],
                        expert_agents=[p.counters for p in teachers],
                        feature_agents=[p.counters for p in feature_memos], times=times)
    raw = {name: [] for name in ("observations", "commands", "reward", "served", "sinr_quality",
                                 "sinr", "connections", "transmitter_mask")}
    raw["positions"] = [positions.copy()]
    decision = {name: [] for name in ("nav_pre", "nav_next", "fallback", "action_index", "memo_hit",
                                      "features", "n_current", "n_peers")}
    if actor is not None:
        decision.update({name: [] for name in ("logits", "probabilities", "innovation", "entropy")})
    if training:
        decision.update({name: [] for name in ("expert_action_index", "expert_fallback", "expert_nav_next",
                                               "expert_memo_hit", "expert_scores", "expert_served")})
    elif actor is None:
        decision.update(policy_scores=[], policy_served=[])
    commands = np.zeros((5, 3), dtype=np.float32)
    for tick in range(protocol.horizon):
        if tick % 4 == 0:
            diagnostics, features, labels, pre = [], [], [], navs.copy()
            for agent in range(5):
                component = "expert_label" if training and phase == 0 else "decision_query"
                pd = _timed_query(policies[agent], obs[agent], tick, navs[agent], times, component)
                if training and phase == 0:
                    fd = _timed_query(feature_memos[agent], obs[agent], tick, navs[agent],
                                      times, "expert_features")
                    ed = pd
                else:
                    fd = pd
                    ed = (_timed_query(teachers[agent], obs[agent], tick, navs[agent],
                                       times, "expert_label") if training else None)
                if training:
                    if bool(fd["fallback"]) != bool(ed["fallback"]) or int(fd["next_nav"]) != int(ed["next_nav"]):
                        raise AssertionError(f"analytic/source C navigation mismatch at {world}/{tick}/{agent}")
                    counts["expert_label_requests"] += 1
                    labels.append(ed)
                # Ordinary C is not given these features; a diagnostic encoding
                # from its paid fallback is sufficient on its evaluation panel.
                if "features" in fd:
                    x = np.asarray(fd["features"], dtype=np.float32)
                else:
                    x = np.r_[obs[agent, :103], np.eye(10, dtype=np.float32)[navs[agent]],
                              np.float32(pd["fallback"])].astype(np.float32)
                if x.shape != (114,) or not np.array_equal(x[:103], obs[agent, :103]):
                    raise AssertionError("actor feature provenance/shape mismatch")
                features.append(x.copy())
                navs[agent] = int(pd["next_nav"])
                commands[agent] = pd["command"]
                if not np.array_equal(commands[agent], COMMANDS[int(pd["action_index"])]):
                    raise AssertionError("category/physical-command disagreement")
                diagnostics.append(pd)
            decision["nav_pre"].append(pre)
            decision["nav_next"].append(navs.copy())
            decision["features"].append(features)
            for key in ("fallback", "action_index", "memo_hit", "n_current", "n_peers"):
                decision[key].append([pd[key] for pd in diagnostics])
            if actor is not None:
                for key in ("logits", "probabilities", "innovation", "entropy"):
                    decision[key].append([pd[key] for pd in diagnostics])
            if training:
                for target, source in (("expert_action_index", "action_index"), ("expert_fallback", "fallback"),
                                       ("expert_nav_next", "next_nav"), ("expert_memo_hit", "memo_hit"),
                                       ("expert_scores", "scores"), ("expert_served", "served")):
                    decision[target].append([ed[source] for ed in labels])
            elif actor is None:
                decision["policy_scores"].append([pd["scores"] for pd in diagnostics])
                decision["policy_served"].append([pd["served"] for pd in diagnostics])
        if commands.shape != (5, 3) or not np.isfinite(commands).all():
            raise AssertionError("invalid joint action")
        raw["observations"].append(obs.copy())
        raw["commands"].append(commands.copy())
        raw["transmitter_mask"].append(_check_all_on(env))
        wall, cpu = time.perf_counter(), time.process_time()
        counts["native_step_calls"] += 1
        next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
        counts["native_steps"] += 1
        counts["training_native_steps" if training else "evaluation_native_steps"] += 1
        times["native_step_wall_seconds"] += time.perf_counter() - wall
        times["native_step_cpu_seconds"] += time.process_time() - cpu
        reward, served, quality = native_reading(next_info)
        global_info = next_info["infos_dict"]["uav_0"]["global"]
        after = np.asarray(next_info["state_info"]["uav_positions"], dtype=np.float64).copy()
        expected_positions = np.clip(positions + commands.astype(np.float64) * 30.0,
                                     [0.0, 0.0, 50.0], [1000.0, 1000.0, 150.0])
        if not np.array_equal(after, expected_positions):
            raise AssertionError("native motion no longer matches the fixed command contract")
        raw["positions"].append(after)
        raw["reward"].append(reward)
        raw["served"].append(served)
        raw["sinr_quality"].append(quality)
        raw["sinr"].append(np.asarray(global_info["sinr_matrix"], dtype=np.float64).copy())
        raw["connections"].append(np.asarray(global_info["connections"], dtype=bool).copy())
        if bool(terminated or truncated) != (tick + 1 == protocol.horizon):
            raise AssertionError("unexpected native terminal boundary")
        obs = np.asarray(next_obs, dtype=np.float32)
        if obs.shape != (5, 104) or not np.isfinite(obs).all():
            raise AssertionError("invalid next local observations")
        positions = after
    arrays = {name: np.asarray(values) for name, values in {**raw, **decision}.items()}
    arrays.update(initial_users=users, terminal_observation=obs.copy(),
                  decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64))
    path = Path(out) / "raw" / f"{arm}_{world}.npz"
    if path.exists():
        raise FileExistsError("raw trajectory already exists")
    wall, cpu = time.perf_counter(), time.process_time()
    np.savez_compressed(path, **arrays)
    identity = file_identity(path)
    identity["path"] = str(path.relative_to(out))
    times["raw_write_wall_seconds"] += time.perf_counter() - wall
    times["raw_write_cpu_seconds"] += time.process_time() - cpu
    cases = (arrays["features"].reshape(-1, 114).copy(),
             arrays["expert_action_index"].reshape(-1).astype(np.int64)) if training else None
    row = {"arm": arm, "world": int(world), "kind": kind, "phase": phase,
           "policy_sha256": policy_sha, **episode_metrics(arrays), **times,
           "policy_counts": sum_counts(p.counters for p in policies),
           "expert_counts": sum_counts(p.counters for p in teachers),
           "feature_counts": sum_counts(p.counters for p in feature_memos),
           "raw": identity, "initial_state_sha256": array_digest(arrays["positions"][0], users),
           "label_data_sha256": array_digest(*cases) if cases is not None else None,
           "cpu_seconds": time.process_time() - start_cpu, "wall_seconds": time.perf_counter() - start_wall,
           "timing_scope": "episode includes reset, native steps, checks, raw compression/hash; query components "
                           "are disjoint; expert roll-in C query counted as expert_label, not decision_query"}
    counts["complete_episodes"] += 1
    counts["training_episodes" if training else "evaluation_episodes"] += 1
    if inflight is not None:
        inflight.clear()
    return row, cases
