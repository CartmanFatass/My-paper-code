"""Complete own-history native episodes, with critic truth kept outside actors."""
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.collect import _check_all_on, _timed_query
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import episode_metrics, sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import critic_features
from .contract import array_digest, candidate_spec, policy_identity
from .policies import LocalPolicy, shadow_on_features


ROLLOUT_KEYS = ("features", "logits", "probabilities", "action_index", "logp", "critic_features", "values", "macro_rewards")


def collect_episode(env, *, lineage, kind, arm, candidate, world, sampling_root,
                    protocol, out, counts, actor=None, actor_sha=None, critic=None,
                    group=None, shadow_actor=None, shadow_sha=None, inflight=None):
    if kind not in ("training", "calibration", "evaluation"):
        raise ValueError("undeclared episode kind")
    training = kind == "training"
    if training != (critic is not None) or (training and (arm != "R" or candidate != "S_T1" or group is None)):
        raise ValueError("only the fixed R training collector may query a critic")
    if shadow_actor is not None and (kind != "evaluation" or arm != "R" or not shadow_sha):
        raise ValueError("frozen S shadows belong only on R final histories")
    family = candidate_spec(candidate)["family"]
    if (actor is not None) != (family == "S") or (family == "S" and not actor_sha):
        raise ValueError("policy source/actor binding missing")
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    times = {f"{component}_{clock}_seconds": 0. for component in
             ("decision_query", "critic", "shadow", "native_step", "reset", "raw_write")
             for clock in ("wall", "cpu")}
    raw = {key: [] for key in ("observations", "commands", "positions", "reward", "served", "sinr_quality",
                               "sinr", "connections", "transmitter_mask")}
    decision = {key: [] for key in ("nav_pre", "nav_next", "fallback", "action_index", "memo_hit", "features",
                                    "n_current", "n_peers", "probabilities", "innovation", "entropy",
                                    "behavior_entropy", "chosen_probability", "logp")}
    if family == "S":
        decision["logits"] = []
    else:
        decision.update(c_index=[], policy_scores=[], policy_served=[])
    if training:
        decision.update(critic_states=[], critic_features=[], values=[])
    if shadow_actor is not None:
        for name in ("logits", "probabilities", "action_index", "positions"):
            decision["shadow_" + name] = []
    path = Path(out) / "raw" / f"L{lineage}_{kind}_{arm}_{world}.npz"
    if path.exists() or path.with_name(path.stem + "_partial.npz").exists():
        raise FileExistsError("this exact episode already has evidence")
    policies = [LocalPolicy(candidate, actor, world=world, agent=i, sampling_root=sampling_root) for i in range(5)]
    if inflight is not None:
        inflight.update(lineage=lineage, kind=kind, arm=arm, candidate=candidate, world=int(world),
                        group=group, policy_agents=[p.counters for p in policies], times=times, last_tick=None)
    users = None
    try:
        wall, cpu = time.perf_counter(), time.process_time()
        counts["explicit_reset_calls"] += 1
        obs, info = env.reset(seed=int(world))
        counts["explicit_resets"] += 1
        times["reset_wall_seconds"] += time.perf_counter() - wall
        times["reset_cpu_seconds"] += time.process_time() - cpu
        obs = np.asarray(obs, dtype=np.float32)
        positions = np.array(info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
        users = np.array(info["state_info"]["user_positions"], dtype=np.float64, copy=True)
        state = np.array(info["state"], dtype=np.float32, copy=True) if training else None
        navs = np.array([initial_nav(row) for row in obs], dtype=np.int64)
        raw["positions"].append(positions.copy())
        commands = np.zeros((5, 3), dtype=np.float32)
        for tick in range(protocol.horizon):
            if inflight is not None:
                inflight["last_tick"] = tick
            if obs.shape != (5, 104) or not np.isfinite(obs).all():
                raise ValueError("five finite ordered local observations required")
            _check_all_on(env)
            if tick % 4 == 0:
                if training:
                    if state.shape != (116,) or not np.isfinite(state).all():
                        raise ValueError("critic state must remain separate finite116-vector")
                    critic_row = critic_features(state, commands, np.zeros(5, dtype=np.int64))
                    wall, cpu = time.perf_counter(), time.process_time()
                    with torch.inference_mode():
                        value = critic(torch.from_numpy(critic_row).reshape(1, 136)).reshape(-1)[0]
                    counts["collected_critic_rows"] += 1
                    if not torch.isfinite(value):
                        raise FloatingPointError("nonfinite collected critic value")
                    times["critic_wall_seconds"] += time.perf_counter() - wall
                    times["critic_cpu_seconds"] += time.process_time() - cpu
                    decision["critic_states"].append(state.copy())
                    decision["critic_features"].append(critic_row.copy())
                    decision["values"].append(np.float32(value.item()))
                decision["nav_pre"].append(navs.copy())
                answers = [_timed_query(policies[i], obs[i], tick, navs[i], times, "decision_query") for i in range(5)]
                for i, answer in enumerate(answers):
                    feature = answer["features"]
                    if feature.shape != (114,) or not np.array_equal(feature[:103], obs[i, :103]):
                        raise AssertionError("lawful feature provenance changed")
                    commands[i] = answer["command"]
                    navs[i] = answer["next_nav"]
                    if not np.array_equal(commands[i], COMMANDS[answer["action_index"]]):
                        raise AssertionError("requested category/command mismatch")
                decision["nav_next"].append(navs.copy())
                fields = ("fallback", "action_index", "memo_hit", "features", "n_current", "n_peers",
                          "probabilities", "innovation", "entropy", "behavior_entropy", "chosen_probability", "logp")
                for key in fields:
                    decision[key].append([a[key] for a in answers])
                if family == "S":
                    decision["logits"].append([a["logits"] for a in answers])
                else:
                    for target, source in (("c_index", "c_index"), ("policy_scores", "scores"), ("policy_served", "served")):
                        decision[target].append([a[source] for a in answers])
                if shadow_actor is not None:
                    wall, cpu = time.perf_counter(), time.process_time()
                    shadow = shadow_on_features(shadow_actor, [a["features"] for a in answers],
                                                [a["innovation"] for a in answers], positions, counts)
                    for key, value in shadow.items():
                        decision["shadow_" + key].append(value)
                    times["shadow_wall_seconds"] += time.perf_counter() - wall
                    times["shadow_cpu_seconds"] += time.process_time() - cpu
            raw["observations"].append(obs.copy())
            raw["commands"].append(commands.copy())
            raw["transmitter_mask"].append(_check_all_on(env))
            wall, cpu = time.perf_counter(), time.process_time()
            counts["native_step_calls"] += 1
            next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
            counts["native_steps"] += 1
            counts[kind + "_native_steps"] += 1
            times["native_step_wall_seconds"] += time.perf_counter() - wall
            times["native_step_cpu_seconds"] += time.process_time() - cpu
            reward, served, quality = native_reading(next_info)
            global_info = next_info["infos_dict"]["uav_0"]["global"]
            after = np.array(next_info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
            if not np.array_equal(after, np.clip(positions + commands.astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])):
                raise AssertionError("source-bound native kinematics changed")
            raw["positions"].append(after.copy())
            for key, value in (("reward", reward), ("served", served), ("sinr_quality", quality),
                               ("sinr", np.array(global_info["sinr_matrix"], dtype=np.float64, copy=True)),
                               ("connections", np.array(global_info["connections"], dtype=bool, copy=True))):
                raw[key].append(value)
            if bool(terminated or truncated) != (tick + 1 == protocol.horizon):
                raise AssertionError("complete episode boundary changed")
            obs, positions = np.asarray(next_obs, dtype=np.float32), after
            if training:
                state = np.array(next_info["next_state"], dtype=np.float32, copy=True)
        arrays = {key: np.asarray(value) for key, value in {**raw, **decision}.items()}
        arrays.update(initial_users=users, terminal_observation=obs.copy(),
                      decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64),
                      macro_rewards=np.asarray(raw["reward"], dtype=np.float64).reshape(-1, 4).sum(axis=1, dtype=np.float64))
        if shadow_actor is not None:
            arrays["shadow_requested_change"] = arrays["shadow_action_index"] != arrays["action_index"]
            arrays["shadow_physical_change"] = np.any(arrays["shadow_positions"] != arrays["positions"][1:].reshape(-1, 4, 5, 3), axis=(1, 3))
            arrays["shadow_modal_change"] = arrays["shadow_logits"].argmax(-1) != arrays["logits"].argmax(-1)
            arrays["shadow_total_variation"] = .5 * np.abs(arrays["shadow_probabilities"] - arrays["probabilities"]).sum(axis=-1)
        wall, cpu = time.perf_counter(), time.process_time()
        np.savez_compressed(path, **arrays)
        artifact = file_identity(path); artifact["path"] = str(path.relative_to(out))
        times["raw_write_wall_seconds"] += time.perf_counter() - wall
        times["raw_write_cpu_seconds"] += time.process_time() - cpu
        row = {"lineage": lineage, "kind": kind, "arm": arm, "candidate": candidate, "world": int(world),
               "group": group, "sampling_root": int(sampling_root), "policy_sha256": actor_sha,
               "policy_identity": policy_identity(candidate, actor_sha, sampling_root),
               "shadow_sha256": shadow_sha, "raw": artifact, **episode_metrics(arrays), **times,
               "policy_counts": sum_counts(p.counters for p in policies),
               "initial_state_sha256": array_digest(arrays["positions"][0], users),
               "nominal_entropy_mean": float(arrays["entropy"].mean()),
               "behavior_entropy_mean": float(arrays["behavior_entropy"].mean()),
               "cpu_seconds": time.process_time() - start_cpu, "wall_seconds": time.perf_counter() - start_wall,
               "timing_scope": "whole episode including reset, all paid policy/critic/shadow queries, native steps and raw write/hash; component timers disjoint"}
        if shadow_actor is not None:
            row["shadow"] = {"rows": int(arrays["action_index"].size),
                             "requested_changes": int(arrays["shadow_requested_change"].sum()),
                             "physical_changes": int(arrays["shadow_physical_change"].sum()),
                             "modal_changes": int(arrays["shadow_modal_change"].sum()),
                             "total_variation_mean": float(arrays["shadow_total_variation"].mean()),
                             "total_variation_max": float(arrays["shadow_total_variation"].max())}
        counts["complete_episodes"] += 1
        counts[kind + "_episodes"] += 1
        if inflight is not None:
            inflight.clear()
        return row, {key: arrays[key] for key in ROLLOUT_KEYS} if training else None
    except BaseException:
        partial = path.with_name(path.stem + "_partial.npz")
        try:
            if not partial.exists():
                arrays = {key: np.asarray(value) for key, value in {**raw, **decision}.items()}
                if users is not None:
                    arrays["initial_users"] = users
                np.savez_compressed(partial, **arrays)
                if inflight is not None:
                    identity = file_identity(partial); identity["path"] = str(partial.relative_to(out))
                    inflight["partial_raw"] = identity
        except BaseException as save_error:
            # Preserve the original effect failure even if disk/serialization also fails.
            if inflight is not None:
                inflight["partial_raw_save_error"] = repr(save_error)
        raise
