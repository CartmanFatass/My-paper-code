"""Complete paired interventions and complete final own-history deployments."""
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.collect import _check_all_on, _timed_query
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_index, categorical_probabilities, indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b02.reading import episode_metrics, sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import HEADS, array_digest, policy_identity
from .policies import LocalPolicy, shadow_from_answers


def collect_episode(env, *, lineage, kind, arm, world, protocol, out, counts, actor=None,
                    initial_sha=None, head=None, head_sha=None, intervention=None, inflight=None):
    acquisition = kind == "acquisition"
    if kind not in ("acquisition", "evaluation") or acquisition != (intervention is not None):
        raise ValueError("exactly acquisition episodes carry one intervention")
    if acquisition and (arm != "S" or head is not None):
        raise ValueError("only the unchanged student acquires paired consequences")
    ordinary = arm in ("C", "Q")
    if ordinary != (actor is None) or (not ordinary and not initial_sha) or (arm in HEADS) != (head is not None):
        raise ValueError("actor/head source binding missing")
    if (head is not None) != (head_sha is not None):
        raise ValueError("head identity missing")
    if intervention is not None:
        intervention = dict(intervention)
        if (intervention["branch"] not in ("a", "b") or not 0 <= intervention["tick"] < protocol.horizon
                or intervention["tick"] % 4 or not 0 <= intervention["agent"] < 5):
            raise ValueError("invalid intervention address")
    root = (protocol.acquisition_roots if acquisition else protocol.evaluation_roots)[lineage]
    suffix = "_" + intervention["branch"] if acquisition else ""
    path = Path(out) / "raw" / f"L{lineage}_{kind}_{arm}_{world}{suffix}.npz"
    if path.exists() or path.with_name(path.stem + "_partial.npz").exists():
        raise FileExistsError("this exact complete episode already has evidence")
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    times = {key: 0. for key in ("reset_wall_seconds", "reset_cpu_seconds", "decision_query_wall_seconds",
                                 "decision_query_cpu_seconds", "native_step_wall_seconds", "native_step_cpu_seconds",
                                 "intervention_wall_seconds", "intervention_cpu_seconds",
                                 "shadow_wall_seconds", "shadow_cpu_seconds",
                                 "raw_write_wall_seconds", "raw_write_cpu_seconds")}
    raw = {key: [] for key in ("observations", "commands", "positions", "reward", "served",
                               "sinr_quality", "sinr", "connections", "transmitter_mask")}
    decision = {key: [] for key in ("nav_pre", "nav_next", "fallback", "action_index", "nominal_action_index",
                                    "memo_hit", "features", "n_current", "n_peers", "probabilities", "innovation",
                                    "entropy", "behavior_entropy", "chosen_probability", "logp")}
    if ordinary:
        decision.update(c_index=[], policy_scores=[], policy_served=[])
    else:
        decision["logits"] = []
    if head is not None:
        decision.update(base_logits=[], shadow_probabilities=[], shadow_action_index=[], shadow_positions=[])
    policies = [LocalPolicy(arm, actor, lineage=lineage, head=head, world=world, agent=i, sampling_root=root) for i in range(5)]
    if inflight is not None:
        inflight.update(lineage=lineage, kind=kind, arm=arm, world=int(world), intervention=intervention,
                        policy_agents=[p.counters for p in policies], times=times, last_tick=None)
    users, context = None, None
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
        navs = np.array([initial_nav(row) for row in obs], dtype=np.int64)
        raw["positions"].append(positions.copy())
        commands = np.zeros((5, 3), dtype=np.float32)
        for tick in range(protocol.horizon):
            if inflight is not None:
                inflight["last_tick"] = tick
            if obs.shape != (5, 104) or not np.isfinite(obs).all():
                raise ValueError("five finite local observations required")
            _check_all_on(env)
            if tick % 4 == 0:
                decision["nav_pre"].append(navs.copy())
                answers = [_timed_query(policies[i], obs[i], tick, navs[i], times, "decision_query") for i in range(5)]
                nominal = np.array([a["action_index"] for a in answers], dtype=np.int64)
                actual = nominal.copy()
                for i, answer in enumerate(answers):
                    if (answer["features"].shape != (114,)
                            or not np.array_equal(answer["features"][:103], obs[i, :103])
                            or not np.array_equal(answer["command"], COMMANDS[nominal[i]])):
                        raise AssertionError("lawful feature/category mapping changed")
                    commands[i] = answer["command"]
                    navs[i] = answer["next_nav"]
                if intervention is not None and tick == intervention["tick"]:
                    wall, cpu = time.perf_counter(), time.process_time()
                    i = intervention["agent"]
                    answer = answers[i]
                    mu = .5 * answer["probabilities"] + .5 / 27.
                    u = indexed_uniform(intervention["root"], world, tick, i)
                    counts["intervention_draws"] += 1
                    forced = categorical_index(mu, u)
                    actual[i], commands[i] = forced, COMMANDS[forced]
                    context = dict(features=answer["features"].copy(), hidden=answer["hidden"].copy(),
                                   logits=answer["base_logits"].copy(), mu=mu.copy(),
                                   action=int(forced), uniform=u, nominal_action=int(nominal[i]))
                    times["intervention_wall_seconds"] += time.perf_counter() - wall
                    times["intervention_cpu_seconds"] += time.process_time() - cpu
                decision["action_index"].append(actual)
                decision["nominal_action_index"].append(nominal)
                decision["nav_next"].append(navs.copy())
                for key in ("fallback", "memo_hit", "features", "n_current", "n_peers", "probabilities",
                            "innovation", "entropy", "behavior_entropy", "chosen_probability", "logp"):
                    decision[key].append([a[key] for a in answers])
                if ordinary:
                    for target, source in (("c_index", "c_index"), ("policy_scores", "scores"), ("policy_served", "served")):
                        decision[target].append([a[source] for a in answers])
                else:
                    decision["logits"].append([a["logits"] for a in answers])
                if head is not None:
                    decision["base_logits"].append([a["base_logits"] for a in answers])
                    wall, cpu = time.perf_counter(), time.process_time()
                    shadow = shadow_from_answers(answers, positions, counts)
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
            if not np.array_equal(after, np.clip(positions + commands.astype(np.float64) * 30.,
                                                [0., 0., 50.], [1000., 1000., 150.])):
                raise AssertionError("source native kinematics changed")
            raw["positions"].append(after.copy())
            for key, value in (("reward", reward), ("served", served), ("sinr_quality", quality),
                               ("sinr", np.array(global_info["sinr_matrix"], dtype=np.float64, copy=True)),
                               ("connections", np.array(global_info["connections"], dtype=bool, copy=True))):
                raw[key].append(value)
            if bool(terminated or truncated) != (tick + 1 == protocol.horizon):
                raise AssertionError("complete episode boundary changed")
            obs, positions = np.asarray(next_obs, dtype=np.float32), after
        arrays = {key: np.asarray(value) for key, value in {**raw, **decision}.items()}
        arrays.update(initial_users=users, terminal_observation=obs.copy(),
                      decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64))
        if acquisition:
            if context is None:
                raise AssertionError("declared intervention never executed")
            arrays.update({"intervention_" + key: np.asarray(value) for key, value in context.items()})
        if head is not None:
            arrays["shadow_requested_change"] = arrays["shadow_action_index"] != arrays["action_index"]
            arrays["shadow_physical_change"] = np.any(
                arrays["shadow_positions"] != arrays["positions"][1:].reshape(-1, 4, 5, 3), axis=(1, 3))
            arrays["shadow_modal_change"] = arrays["base_logits"].argmax(-1) != arrays["logits"].argmax(-1)
            arrays["shadow_total_variation"] = .5 * np.abs(arrays["shadow_probabilities"] - arrays["probabilities"]).sum(-1)
        wall, cpu = time.perf_counter(), time.process_time()
        np.savez_compressed(path, **arrays)
        artifact = file_identity(path)
        artifact["path"] = str(path.relative_to(out))
        times["raw_write_wall_seconds"] += time.perf_counter() - wall
        times["raw_write_cpu_seconds"] += time.process_time() - cpu
        row = dict(lineage=lineage, kind=kind, arm=arm, world=int(world), sampling_root=int(root),
                   initial_sha256=initial_sha, head_sha256=head_sha,
                   policy_identity=policy_identity(arm, lineage, initial_sha, head_sha, root),
                   intervention=intervention, raw=artifact, **episode_metrics(arrays), **times,
                   policy_counts=sum_counts(p.counters for p in policies),
                   initial_state_sha256=array_digest(arrays["positions"][0], users),
                   nominal_entropy_mean=float(arrays["entropy"].mean()),
                   behavior_entropy_mean=float(arrays["behavior_entropy"].mean()),
                   cpu_seconds=time.process_time() - start_cpu, wall_seconds=time.perf_counter() - start_wall,
                   timing_scope="complete episode reset, policy, intervention/shadow, native, serialization/hash; components disjoint",
                   proposal_scope="normal policy probabilities/actions are saved separately from the one actual forced category")
        if context is not None:
            row["intervention_result"] = dict(action=context["action"], nominal_action=context["nominal_action"],
                                              uniform=context["uniform"], context_sha256=array_digest(
                                                  context["features"], context["hidden"], context["logits"], context["mu"]))
        if head is not None:
            row["shadow"] = dict(rows=int(arrays["action_index"].size),
                                 requested_changes=int(arrays["shadow_requested_change"].sum()),
                                 physical_changes=int(arrays["shadow_physical_change"].sum()),
                                 modal_changes=int(arrays["shadow_modal_change"].sum()),
                                 total_variation_mean=float(arrays["shadow_total_variation"].mean()),
                                 total_variation_max=float(arrays["shadow_total_variation"].max()))
        counts["complete_episodes"] += 1
        counts[kind + "_episodes"] += 1
        if inflight is not None:
            inflight.clear()
        return row, context
    except BaseException:
        try:
            partial = path.with_name(path.stem + "_partial.npz")
            arrays = {key: np.asarray(value) for key, value in {**raw, **decision}.items()}
            if users is not None:
                arrays["initial_users"] = users
            if context is not None:
                arrays.update({"intervention_" + key: np.asarray(value) for key, value in context.items()})
            if not partial.exists():
                np.savez_compressed(partial, **arrays)
            if inflight is not None:
                found = file_identity(partial); found["path"] = str(partial.relative_to(out))
                inflight["partial_raw"] = found
        except BaseException as save_error:
            if inflight is not None:
                inflight["partial_raw_save_error"] = repr(save_error)
        raise
