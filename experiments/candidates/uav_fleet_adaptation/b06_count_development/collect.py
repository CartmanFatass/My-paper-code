"""Complete own-history native trajectories, including the charged H8 fixture."""
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import array_digest
from .controllers import COMMANDS, FeatureMemo, MemoC, fleet_count, initial_nav
from .environment import reset_layout
from .policies import OrdinaryPolicy, StudentPolicy
from .reading import episode_metrics


def _query(policy, row, tick, nav, times, component):
    wall, cpu = time.perf_counter(), time.process_time()
    result = policy.query(row.copy(), tick, int(nav))
    times[component + "_wall_seconds"] += time.perf_counter() - wall
    times[component + "_cpu_seconds"] += time.process_time() - cpu
    return result


def _all_on(env, n):
    mask = np.asarray(env.env.transmitter_mask)
    if mask.dtype != np.dtype(bool) or mask.shape != (n,) or not mask.all():
        raise AssertionError("all-on native contract violated")
    return mask.copy()


def collect_episode(env, *, arm, lineage, world, n, out, protocol, counts, kind,
                    actor=None, phase=None, tape=None, policy_sha=None, inflight=None):
    started, cpu_started = time.perf_counter(), time.process_time()
    n = fleet_count(n)
    training, fixture = kind == "acquisition", kind == "fixture"
    if kind not in ("acquisition", "evaluation", "fixture") or env.n_uavs != n:
        raise ValueError("invalid collection kind/fleet")
    if training and (phase not in (0, 1, 2) or arm not in ("F", "M") or lineage not in (0, 1)):
        raise ValueError("invalid acquisition identity")
    if fixture and (arm != "C" or world != protocol.fixture_world or actor is not None):
        raise ValueError("only the fixed C_N native correctness trajectory is allowed")
    neural = actor is not None
    if training and (neural != (phase != 0)):
        raise ValueError("C roll-in then current greedy student are fixed")
    if kind == "evaluation" and (neural != (arm in ("P", "F", "M", "Bstar"))):
        raise ValueError("final program/actor mismatch")
    stochastic = kind == "evaluation" and arm != "C"
    if stochastic and tape not in (0, 1) or not stochastic and tape is not None:
        raise ValueError("invalid private tape assignment")
    root = protocol.evaluation_roots[tape] if stochastic else None
    temperature = 2. if arm == "Bstar" else 1.
    if arm == "Bstar" and lineage != 0:
        raise ValueError("lineage1 Bstar is exact P metadata reuse")
    horizon = protocol.fixture_horizon if fixture else protocol.horizon
    times = {f"{component}_{clock}_seconds": 0. for component in
             ("reset_layout", "decision_query", "expert_label", "expert_features", "native_step", "raw_write")
             for clock in ("wall", "cpu")}
    wall, cpu = time.perf_counter(), time.process_time()
    obs, info, seven = reset_layout(env, world, protocol, counts)
    times["reset_layout_wall_seconds"] = time.perf_counter() - wall
    times["reset_layout_cpu_seconds"] = time.process_time() - cpu
    obs = np.asarray(obs, dtype=np.float32)
    if obs.shape != (n, 104) or not np.isfinite(obs).all():
        raise ValueError("invalid initial local observations")
    _all_on(env, n)
    positions = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64).copy()
    users = np.asarray(info["state_info"]["user_positions"], dtype=np.float64).copy()
    initial = dict(initial_users=users, initial_seven_uavs=seven,
                   initial_sinr=np.asarray(env.env.sinr_matrix).copy(),
                   initial_peer_sinr=np.asarray(env.env.uav_sinr_matrix).copy(),
                   initial_connections=np.asarray(env.env.connections).copy())
    navs = np.asarray([initial_nav(obs[i], n) for i in range(n)], dtype=np.int64)
    teachers = [MemoC(n) for _ in range(n)] if training else []
    feature_memos = [FeatureMemo(n) for _ in range(n)] if fixture or training and phase == 0 else []
    if training and phase == 0:
        policies = teachers
    elif neural:
        policies = [StudentPolicy(actor, n=n, world=world, agent=i, sampling_root=root,
                                  temperature=temperature) for i in range(n)]
    elif arm in ("C", "Q"):
        policies = [OrdinaryPolicy(n=n, world=world, agent=i, sampling_root=root) for i in range(n)]
    else:
        raise ValueError("missing policy")
    if inflight is not None:
        inflight.update(kind=kind, arm=arm, lineage=lineage, world=world, n=n, phase=phase, neural=neural,
                        tape=tape, policy_agents=[p.counters for p in policies],
                        expert_agents=[p.counters for p in teachers],
                        feature_agents=[p.counters for p in feature_memos], times=times)
    raw = {key: [] for key in ("observations", "commands", "reward", "served", "sinr_quality",
                               "sinr", "peer_sinr", "connections", "transmitter_mask", "terminated", "truncated")}
    raw["positions"] = [positions.copy()]
    decision = {key: [] for key in ("nav_pre", "nav_next", "fallback", "action_index", "memo_hit",
                                    "features", "n_current", "n_peers")}
    if neural:
        decision.update({key: [] for key in ("logits", "probabilities", "innovation", "entropy")})
    if training:
        decision.update({key: [] for key in ("expert_action_index", "expert_fallback", "expert_nav_next",
                                            "expert_memo_hit", "expert_scores", "expert_served")})
    elif not neural:
        decision.update({key: [] for key in ("policy_scores", "policy_served", "mode_index", "probabilities", "innovation")})
    commands = np.zeros((n, 3), dtype=np.float32)
    for tick in range(horizon):
        if tick % protocol.period == 0:
            diagnostics, features, labels, pre = [], [], [], navs.copy()
            for agent in range(n):
                component = "expert_label" if training and phase == 0 else "decision_query"
                pd = _query(policies[agent], obs[agent], tick, navs[agent], times, component)
                fd = (_query(feature_memos[agent], obs[agent], tick, navs[agent], times, "expert_features")
                      if feature_memos else pd)
                ed = (pd if phase == 0 else
                      _query(teachers[agent], obs[agent], tick, navs[agent], times, "expert_label")) if training else None
                if training or fixture:
                    reference = ed if training else pd
                    if (bool(fd["fallback"]) != bool(reference["fallback"])
                            or int(fd["next_nav"]) != int(reference["next_nav"])):
                        raise AssertionError(f"count-aware C/helper mismatch at N{n}/{world}/{tick}/{agent}")
                if training:
                    counts["expert_labels"] += 1
                    labels.append(ed)
                x = np.asarray(fd["features"], dtype=np.float32)
                if x.shape != (114,) or not np.array_equal(x[:103], obs[agent, :103]):
                    raise AssertionError("feature provenance mismatch")
                features.append(x.copy())
                navs[agent], commands[agent] = int(pd["next_nav"]), pd["command"]
                if not np.array_equal(commands[agent], COMMANDS[int(pd["action_index"])]):
                    raise AssertionError("requested category/command mismatch")
                diagnostics.append(pd)
            decision["nav_pre"].append(pre)
            decision["nav_next"].append(navs.copy())
            decision["features"].append(features)
            for key in ("fallback", "action_index", "memo_hit", "n_current", "n_peers"):
                decision[key].append([p[key] for p in diagnostics])
            if neural:
                for key in ("logits", "probabilities", "innovation", "entropy"):
                    decision[key].append([p[key] for p in diagnostics])
            if training:
                for target, source in (("expert_action_index", "action_index"), ("expert_fallback", "fallback"),
                                       ("expert_nav_next", "next_nav"), ("expert_memo_hit", "memo_hit"),
                                       ("expert_scores", "scores"), ("expert_served", "served")):
                    decision[target].append([p[source] for p in labels])
            elif not neural:
                for target, source in (("policy_scores", "scores"), ("policy_served", "served"),
                                       ("mode_index", "mode_index"), ("probabilities", "probabilities"),
                                       ("innovation", "innovation")):
                    decision[target].append([p[source] for p in diagnostics])
        if commands.shape != (n, 3) or not np.isfinite(commands).all():
            raise AssertionError("invalid held joint commands")
        raw["observations"].append(obs.copy())
        raw["commands"].append(commands.copy())
        raw["transmitter_mask"].append(_all_on(env, n))
        wall, cpu = time.perf_counter(), time.process_time()
        counts["native_step_calls"] += 1
        next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
        counts["native_steps"] += 1
        counts["native_uav_ticks"] += n
        counts["native_dense_slots"] += n * (50 + n)
        counts[kind + "_native_steps"] += 1
        times["native_step_wall_seconds"] += time.perf_counter() - wall
        times["native_step_cpu_seconds"] += time.process_time() - cpu
        if set(next_info["rewards_dict"]) != {f"uav_{i}" for i in range(n)}:
            raise AssertionError("native reward roster changed")
        reward, served, quality = native_reading(next_info)
        global_info = next_info["infos_dict"]["uav_0"]["global"]
        after = np.asarray(next_info["state_info"]["uav_positions"], dtype=np.float64).copy()
        expected = np.clip(positions + commands.astype(np.float64) * 30.,
                           [0., 0., 50.], [1000., 1000., 150.])
        if not np.array_equal(after, expected):
            raise AssertionError("native held command/motion mismatch")
        raw["positions"].append(after)
        for name, value in (("reward", reward), ("served", served), ("sinr_quality", quality),
                            ("sinr", np.asarray(global_info["sinr_matrix"]).copy()),
                            ("peer_sinr", np.asarray(env.env.uav_sinr_matrix).copy()),
                            ("connections", np.asarray(global_info["connections"]).copy()),
                            ("terminated", bool(terminated)), ("truncated", bool(truncated))):
            raw[name].append(value)
        if bool(terminated) != (tick + 1 == protocol.horizon) or bool(truncated):
            raise AssertionError("unexpected native terminal boundary")
        obs = np.asarray(next_obs, dtype=np.float32)
        if obs.shape != (n, 104) or not np.isfinite(obs).all():
            raise AssertionError("invalid next observation")
        positions = after
    arrays = {name: np.asarray(values) for name, values in {**raw, **decision}.items()}
    arrays.update(initial, terminal_observation=obs.copy(), decision_ticks=np.arange(0, horizon, 4, dtype=np.int64))
    identifier = f"{kind}_L{lineage}_{arm}_N{n}_w{world}_p{phase}_t{tape}"
    path = Path(out) / "raw" / (identifier + ".npz")
    if path.exists():
        raise FileExistsError("raw trajectory identity already exists")
    wall, cpu = time.perf_counter(), time.process_time()
    np.savez_compressed(path, **arrays)
    artifact = file_identity(path)
    artifact["path"] = str(path.relative_to(out))
    times["raw_write_wall_seconds"] += time.perf_counter() - wall
    times["raw_write_cpu_seconds"] += time.process_time() - cpu
    cases = (arrays["features"].reshape(-1, 114).copy(),
             arrays["expert_action_index"].reshape(-1).astype(np.int64),
             np.full(arrays["features"].shape[0] * n, n, dtype=np.int64)) if training else None
    row = dict(id=identifier, kind=kind, arm=arm, lineage=lineage, world=int(world), n=n,
               phase=phase, tape=tape, sampling_root=root, temperature=temperature if neural else None,
               policy_sha256=policy_sha, neural=neural, **episode_metrics(arrays), **times,
               policy_counts=sum_counts(p.counters for p in policies),
               expert_counts=sum_counts(p.counters for p in teachers),
               feature_counts=sum_counts(p.counters for p in feature_memos), raw=artifact,
               initial_state_sha256=array_digest(arrays["positions"][0], users),
               shared_layout_sha256=array_digest(users, seven),
               label_data_sha256=array_digest(*cases) if cases is not None else None,
               cpu_seconds=time.process_time() - cpu_started, wall_seconds=time.perf_counter() - started,
               timing_scope="episode includes discarded reset/layout refresh, collection, checks and compressed raw write; query components are disjoint")
    if fixture:
        counts["fixture_trajectories"] += 1
    else:
        counts["complete_episodes"] += 1
        counts[kind + "_episodes"] += 1
    if inflight is not None:
        inflight.clear()
    return row, cases
