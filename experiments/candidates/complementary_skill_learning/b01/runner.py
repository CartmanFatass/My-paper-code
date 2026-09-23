"""One prospective S1 D/G/P fit, with native learning and frozen execution panels."""
from __future__ import annotations

import contextlib
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import resource
import sys
import time
import traceback

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from scripts import run_flexible_skill_duration_e0 as native
from scripts import run_fsd_uav_individual_renewal_b01 as support

DIRECTION = "complementary_skill_learning"
OBJECT = "complementary_skill_b01"
COMPONENTS = ("coverage_reward", "quality_reward", "energy_penalty", "total_reward")
MODULES = ("skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator")
NORMALIZERS = ("obs_norm", "state_norm", "value_norm_coordinator", "value_norm_discoverer")


@dataclass(frozen=True)
class Spec:
    n_agents: int = 6
    n_users: int = 50
    k: int = 10
    horizon: int = 500
    lanes: int = 16
    rollouts: int = 45
    eval_lanes: int = 32
    diagnostic_lanes: int = 16
    prefix_steps: int = 200
    init_seed: int = 260923901
    head_seed: int = 260923902
    train_rng_seed: int = 260923903
    aux_seed: int = 260923904
    eval_rng_seed: int = 260923905
    train_world_base: int = 1600000
    own_initial_base: int = 1700000
    own_final_base: int = 1700100
    uniform_final_base: int = 1700200
    diagnostic_base: int = 1700300
    threads: int = 4
    small_model: bool = False  # internal technical checks only; absent from the CLI


DEFAULT_SPEC = Spec()


def jsonable(value):
    if isinstance(value, torch.Tensor):
        return jsonable(value.detach().cpu().numpy())
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    return value


def write_json(path, body):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(jsonable(body), ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def seed_rng(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


@contextlib.contextmanager
def preserve_rng():
    state = (random.getstate(), np.random.get_state(), torch.get_rng_state(),
             torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None)
    try:
        yield
    finally:
        random.setstate(state[0])
        np.random.set_state(state[1])
        torch.set_rng_state(state[2])
        if state[3] is not None:
            torch.cuda.set_rng_state_all(state[3])


def update_digest(digest, *arrays):
    for value in arrays:
        array = np.ascontiguousarray(value)
        digest.update(str(array.shape).encode())
        digest.update(array.dtype.str.encode())
        digest.update(array.tobytes())


def native_digest(agent):
    digest = hashlib.sha256()
    for name in MODULES:
        module = getattr(agent, name)
        if module is not None:
            for key, value in sorted(module.state_dict().items()):
                digest.update((name + ":" + key).encode())
                update_digest(digest, value.detach().cpu().numpy())
    return digest.hexdigest()


def frozen_digest(agent):
    """Include auxiliary weights and calibration/normalizers in the no-update check."""
    digest = hashlib.sha256(native_digest(agent).encode())
    for name in ("g_head", "p_head"):
        for key, value in sorted(getattr(agent, name).state_dict().items()):
            digest.update((name + ":" + key).encode())
            update_digest(digest, value.detach().cpu().numpy())
    metadata = {name: (vars(getattr(agent, name)) if getattr(agent, name) is not None else None)
                for name in NORMALIZERS}
    metadata.update(target_mean=agent.target_mean, target_std=agent.target_std,
                    value_norm_update_counter=agent.value_norm_update_counter)
    digest.update(json.dumps(jsonable(metadata), sort_keys=True, allow_nan=False).encode())
    return digest.hexdigest()


def make_envs(spec, count, world_base):
    return native._make_envs(count, world_base, spec.n_agents, spec.n_users, spec.horizon)


def make_config(spec, envs):
    cfg = native._make_config("D0", spec.init_seed, spec.lanes, spec.horizon, spec.horizon,
                              spec.n_agents, spec.n_users, spec.rollouts,
                              envs[0].state_dim, envs[0].obs_dim)
    cfg.n_Z = cfg.n_z = 6
    cfg.coordinator_batch_size = 1280
    cfg.use_obsnorm = cfg.use_statenorm = False
    if spec.small_model:
        cfg.hidden_size = cfg.embedding_dim = cfg.gru_hidden_size = 16
        cfg.n_heads = 4
        cfg.n_layers = 1
        cfg.ppo_epochs = 1
        cfg.num_mini_batch = 1
        cfg.coordinator_batch_size = 1280
    return cfg


def components(info):
    value = info["reward_components"]["reward_info"]
    result = {name: float(value[name]) for name in COMPONENTS}
    if not np.isfinite(list(result.values())).all():
        raise ValueError("nonfinite native reward component")
    return result


def physical_step(env, raw_action):
    raw = np.asarray(raw_action)
    if not np.isfinite(raw).all():
        raise ValueError("nonfinite raw action")
    executed = np.clip(raw, -1.0, 1.0)  # fresh array: PPO continues to store raw Gaussian samples
    obs, reward, term, trunc, info = env.step(executed)
    if not np.isfinite(reward):
        raise ValueError("nonfinite environment scalar")
    return (np.asarray(info["next_state"], dtype=np.float64),
            np.asarray(obs, dtype=np.float32), float(reward), bool(term or trunc),
            components(info), executed)


@torch.no_grad()
def low_actions(agent, observations, skills, hidden, *, deterministic):
    """The unchanged local actor; evaluation owns recurrent state outside training lanes."""
    obs = np.asarray(observations)
    batch, count, dim = obs.shape
    device = agent.device
    actions, _, _, next_hidden = agent.skill_discoverer(
        torch.as_tensor(obs.reshape(-1, dim), dtype=torch.float32, device=device),
        torch.as_tensor(np.asarray(skills).reshape(-1), dtype=torch.long, device=device),
        torch.as_tensor(np.asarray(hidden).reshape(-1, agent.config.gru_hidden_size),
                        dtype=torch.float32, device=device),
        deterministic=deterministic,
    )
    return (actions.cpu().numpy().reshape(batch, count, -1),
            next_hidden.cpu().numpy().reshape(batch, count, agent.config.gru_hidden_size))


@torch.no_grad()
def select_skills(agent, states, observations, rule, rng):
    batch, n_agents = observations.shape[:2]
    if rule == "uniform":
        return (rng.integers(0, agent.config.n_Z, size=batch),
                rng.integers(0, agent.config.n_z, size=(batch, n_agents)))
    if rule != "own":
        raise ValueError(rule)
    # Infinite-cost/cap=k native D2 renews every factor in canonical order.
    result = agent.skill_coordinator.assign_partial_batch(
        torch.as_tensor(states, dtype=torch.float32, device=agent.device),
        torch.as_tensor(observations, dtype=torch.float32, device=agent.device),
        torch.zeros(batch, dtype=torch.long, device=agent.device),
        torch.zeros((batch, n_agents), dtype=torch.long, device=agent.device),
        torch.ones(batch, dtype=torch.bool, device=agent.device),
        torch.ones((batch, n_agents), dtype=torch.bool, device=agent.device),
        deterministic=True,
    )
    return result["team_skills"].cpu().numpy(), result["agent_skills"].cpu().numpy()


@contextlib.contextmanager
def evaluation_context(agent):
    modes = [(module, module.training) for name in (*MODULES, "g_head", "p_head")
             for module in (getattr(agent, name),) if module is not None]
    before = frozen_digest(agent)
    with preserve_rng():
        for module, _ in modes:
            module.eval()
        try:
            with torch.no_grad():
                yield
        finally:
            for module, mode in modes:
                module.train(mode)
    if frozen_digest(agent) != before:
        raise ValueError("evaluation changed weights, buffers or calibration/normalizers")


def evaluate_panel(agent, spec, world_base, rule, *, counter=None):
    returns = np.zeros(spec.eval_lanes, dtype=np.float64)
    sums = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
    saturation = total_action_coordinates = 0
    with evaluation_context(agent):
        seed_rng(spec.eval_rng_seed + world_base)
        label_rng = np.random.default_rng(spec.eval_rng_seed + world_base)
        envs = make_envs(spec, spec.eval_lanes, world_base)
        states, observations = native._reset_all(envs)
        hidden = np.zeros((spec.eval_lanes, spec.n_agents, agent.config.gru_hidden_size), np.float32)
        for t in range(spec.horizon):
            if t % spec.k == 0:
                team, skills = select_skills(agent, states, observations, rule, label_rng)
            actions, hidden = low_actions(agent, observations, skills, hidden, deterministic=True)
            saturation += int((np.abs(actions) > 1).sum())
            total_action_coordinates += actions.size
            for lane, env in enumerate(envs):
                state, obs, reward, done, parts, _ = physical_step(env, actions[lane])
                if counter is not None:
                    counter["evaluation_transitions"] += 1
                    counter["evaluation_episodes"] += int(done)
                if done != (t == spec.horizon - 1):
                    raise ValueError("unexpected evaluation episode boundary")
                returns[lane] += reward
                for name in COMPONENTS:
                    sums[name][lane] += parts[name]
                states[lane], observations[lane] = state, obs
        for env in envs:
            env.close()
    scores = spec.n_agents * returns / spec.horizon
    np.testing.assert_allclose(scores, sums["total_reward"] / spec.horizon, atol=1e-7, rtol=1e-7)
    return {"status": "complete", "rule": rule, "low_actions": "mean_clipped",
            "world_seeds": list(range(world_base, world_base + spec.eval_lanes)),
            "transitions": spec.eval_lanes * spec.horizon, "optimizer_calls": 0,
            "normalizer_updates": 0, "returns_U": returns, "native_scores_J": scores,
            "mean_J": float(scores.mean()), "component_means": {k: v / spec.horizon for k, v in sums.items()},
            "connected_users_per_step": sums["coverage_reward"] * spec.n_users / spec.horizon,
            "raw_saturation_fraction": saturation / total_action_coordinates}


def rectangles():
    records = []
    for r, pair in enumerate(((0, 1), (2, 3), (4, 5), (1, 4))):
        labels = np.asarray([(r + i) % 6 for i in range(6)], dtype=np.int64)
        cells = []
        # aa, ab, ba, bb gives the explicit interaction coefficients +,-,-,+.
        for a, b in ((r, r + 2), (r, r + 3), (r + 1, r + 2), (r + 1, r + 3)):
            z = labels.copy()
            z[pair[0]], z[pair[1]] = a % 6, b % 6
            cells.append(z.tolist())
        records.append({"members": pair, "team_skill": r, "cells": cells})
    return records


def signed_pairing(predictions, actual):
    predictions = np.asarray(predictions, dtype=np.float64)
    weights = np.asarray([1., -1., -1., 1.])
    predicted_delta = float(np.dot(predictions, weights))
    sign = 1 if predicted_delta >= 0 else -1
    actual = np.asarray(actual, dtype=np.float64)
    delta = float(np.dot(actual, weights))
    independent = float(actual.mean())
    selected = (0, 3) if sign == 1 else (1, 2)
    matched = float(actual[list(selected)].mean())
    if not np.isclose(matched - independent, sign * delta / 4, rtol=1e-12, atol=1e-12):
        raise ValueError("signed pairing identity failed")
    reversal = bool((actual[0] - actual[2]) * (actual[1] - actual[3]) < 0)
    return {"predicted_delta": predicted_delta, "predicted_sign": sign,
            "tie": predicted_delta == 0, "delta": delta, "T": sign * delta / 4,
            "matched_value": matched, "independent_value": independent,
            "predicted_matched_value": float(predictions[list(selected)].mean()),
            "predicted_independent_value": float(predictions.mean()),
            "preference_reversal": reversal}


def execute_branch(agent, env_snapshot, state, observation, hidden, skill, spec, innovation_seed, *, counter=None):
    """Full object copy includes environment/adapter RNG, caches and connection state."""
    env = copy.deepcopy(env_snapshot)
    state, observation, hidden = state.copy(), observation.copy(), hidden.copy()
    rewards, component_rows, raw_rows, executed_rows, state_hashes = [], [], [], [], []
    with preserve_rng():
        seed_rng(innovation_seed)
        for _ in range(spec.k):
            raw, hidden = low_actions(agent, observation[None], np.asarray(skill)[None],
                                      hidden.reshape(1, spec.n_agents, -1), deterministic=False)
            hidden = hidden[0]
            state, observation, reward, done, parts, executed = physical_step(env, raw[0])
            if counter is not None:
                counter["evaluation_transitions"] += 1
                counter["diagnostic_branch_transitions"] += 1
            if done:
                raise ValueError("diagnostic branch crossed a terminal")
            rewards.append(reward)
            component_rows.append(parts)
            raw_rows.append(raw[0].tolist())
            executed_rows.append(executed.tolist())
            digest = hashlib.sha256()
            update_digest(digest, state, observation, hidden)
            state_hashes.append(digest.hexdigest())
    env.close()
    discount = .99 ** np.arange(spec.k)
    return {"Y": float(np.dot(rewards, discount)), "rewards": rewards,
            "component_rows": component_rows, "discounted_components": {
                name: float(np.dot([row[name] for row in component_rows], discount)) for name in COMPONENTS},
            "raw_actions": raw_rows, "executed_actions": executed_rows, "trajectory_hashes": state_hashes}


def combination_diagnostic(agent, spec, *, counter=None):
    if spec.n_agents != 6 or spec.k != 10 or spec.prefix_steps % spec.k:
        raise ValueError("diagnostic is bound to six members and a k10 boundary")
    rows = []
    with evaluation_context(agent):
        seed_rng(spec.eval_rng_seed + spec.diagnostic_base)
        label_rng = np.random.default_rng(spec.eval_rng_seed + spec.diagnostic_base)
        envs = make_envs(spec, spec.diagnostic_lanes, spec.diagnostic_base)
        states, observations = native._reset_all(envs)
        hidden = np.zeros((spec.diagnostic_lanes, 6, agent.config.gru_hidden_size), np.float32)
        for t in range(spec.prefix_steps):
            if t % spec.k == 0:
                _, skills = select_skills(agent, states, observations, "uniform", label_rng)
            actions, hidden = low_actions(agent, observations, skills, hidden, deterministic=True)
            for lane, env in enumerate(envs):
                state, obs, _, done, _, _ = physical_step(env, actions[lane])
                if counter is not None:
                    counter["evaluation_transitions"] += 1
                    counter["diagnostic_prefix_transitions"] += 1
                if done:
                    raise ValueError("diagnostic prefix crossed terminal")
                states[lane], observations[lane] = state, obs
        for lane, env in enumerate(envs):
            world = spec.diagnostic_base + lane
            for r, rectangle in enumerate(rectangles()):
                preds = agent.predict_returns(
                    np.repeat(states[lane:lane+1], 4, axis=0),
                    np.repeat(observations[lane:lane+1], 4, axis=0),
                    np.repeat(hidden[lane:lane+1], 4, axis=0), np.ones((4, 6), np.float32),
                    np.full(4, spec.prefix_steps), np.full(4, rectangle["team_skill"]),
                    np.asarray(rectangle["cells"], np.int64))
                predictions = {name: np.asarray(jsonable(value), dtype=np.float64).reshape(4)
                               for name, value in preds.items()}
                # Both choices are fixed before physical outcomes; G is prospectively primary.
                signs = {name: (1 if float(value @ np.array([1,-1,-1,1])) >= 0 else -1)
                         for name, value in predictions.items()}
                cells = []
                for skills in rectangle["cells"]:
                    cell = execute_branch(agent, env, states[lane], observations[lane], hidden[lane],
                                          skills, spec, spec.eval_rng_seed + world * 8 + r, counter=counter)
                    cells.append(cell)
                actual = [cell["Y"] for cell in cells]
                readings = {name: signed_pairing(value, actual) for name, value in predictions.items()}
                assert all(readings[name]["predicted_sign"] == signs[name] for name in signs)
                rows.append({"world_seed": world, "rectangle_index": r, **rectangle,
                             "predictions": predictions, "cells": cells, "readings": readings})
        for env in envs:
            env.close()
    aggregates = {}
    for readout in ("G", "P"):
        values = [float(np.mean([row["readings"][readout]["T"] for row in rows if row["world_seed"] == world]))
                  for world in range(spec.diagnostic_base, spec.diagnostic_base + spec.diagnostic_lanes)]
        aggregates[readout] = {"world_T_scalar": values, "mean_T_scalar": float(np.mean(values)),
                               "world_T_team": (spec.n_agents * np.asarray(values)).tolist(),
                               "tie_count": sum(row["readings"][readout]["tie"] for row in rows)}
    world_T = aggregates["G"]["world_T_scalar"]
    return {"status": "complete", "primary_readout": "G", "optimizer_calls": 0,
            "normalizer_updates": 0, "low_actions": "sampled_gaussian_clipped_common_innovations",
            "transitions": spec.diagnostic_lanes * (spec.prefix_steps + 16 * spec.k),
            "rows": rows, "world_T_scalar": world_T, "mean_T_scalar": float(np.mean(world_T)),
            "readout_aggregates": aggregates,
            "world_T_team": (spec.n_agents * np.asarray(world_T)).tolist()}


def save_checkpoint(agent, path, config, stage):
    body = {"object_id": OBJECT, "stage": stage, "config": config,
            "native": {name: getattr(agent, name).state_dict() for name in MODULES
                       if getattr(agent, name) is not None},
            "normalizers": {name: copy.deepcopy(getattr(agent, name)) for name in NORMALIZERS},
            "auxiliary": agent.auxiliary_state_dict()}
    torch.save(body, path)
    return {"file": path.name, "sha256": native._sha256_file(path), "bytes": path.stat().st_size,
            "native_digest": native_digest(agent)}


def run_fit(arm, out, launch_sha, *, spec=DEFAULT_SPEC, device="cuda", admission=None):
    from .learning import ComplementaryAgent
    if arm not in ("D", "G", "P"):
        raise ValueError(arm)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists():
        raise ValueError("a fit never overwrites an existing summary")
    torch.set_num_threads(spec.threads)
    logging.getLogger().setLevel(logging.WARNING)
    start = time.perf_counter()
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    counts = dict.fromkeys(("started_fits", "model_constructions", "training_transitions",
                           "stored_transitions", "training_episodes", "native_updates",
                           "evaluation_transitions", "evaluation_episodes",
                           "diagnostic_prefix_transitions", "diagnostic_branch_transitions"), 0)
    summary = {"object_id": OBJECT, "direction": DIRECTION, "arm": arm, "launch_sha": launch_sha,
               "status": "incomplete", "spec": asdict(spec), "device": device, "admission": admission,
               "counts": counts, "training_rows": [], "panels": {}, "checkpoints": {}}
    summary["runtime"] = {
        "python": sys.version, "numpy": np.__version__, "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda, "torch_threads": torch.get_num_threads(),
        "thread_environment": {key: os.environ.get(key) for key in
                               ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "learner_dtype": "float32", "reward_return_dtype": "float64",
        "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
    }
    write_json(out / "config.json", {"object_id": OBJECT, "arm": arm, "spec": asdict(spec),
                                    "launch_sha": launch_sha, "device": device})
    envs = []
    agent = counters = None
    try:
        if torch.device(device).type == "cuda":
            torch.cuda.reset_peak_memory_stats(torch.device(device))
            summary["runtime"]["cuda_device"] = torch.cuda.get_device_name(torch.device(device))
        envs = make_envs(spec, spec.lanes, spec.train_world_base)
        config = make_config(spec, envs)
        summary["learner_config"] = support.config_snapshot(config)
        seed_rng(spec.init_seed)
        agent = ComplementaryAgent(config=config, arm=arm, head_seed=spec.head_seed,
                                   aux_seed=spec.aux_seed, log_dir=str(out / "learner_logs"),
                                   device=torch.device(device))
        counts["model_constructions"] += 1
        theta0 = native._capture_theta0(agent)
        counters = support.optimizer_counters(agent)
        summary["initial_native_digest"] = native_digest(agent)
        summary["auxiliary_parameter_counts"] = jsonable(agent.parameter_counts)
        summary["auxiliary_architecture"] = jsonable(agent.auxiliary_architecture)
        summary["checkpoints"]["initial"] = save_checkpoint(agent, out / "initial.pt", summary["learner_config"], 0)
        seed_rng(spec.train_rng_seed)
        summary["panels"]["initial_own"] = evaluate_panel(agent, spec, spec.own_initial_base, "own", counter=counts)
        write_json(out / "summary.json", summary)
        states, observations = native._reset_all(envs)
        env_steps = np.zeros(spec.lanes, np.int64)
        dones = np.zeros(spec.lanes, bool)
        agent.train(True)
        counts["started_fits"] += 1
        first_digest = hashlib.sha256()
        label_hist = np.zeros((spec.n_agents, 6), np.int64)
        joint_hist = {}
        for rollout in range(spec.rollouts):
            began = time.perf_counter()
            returns = np.zeros(spec.lanes, np.float64)
            saturation = action_coordinates = 0
            before = support.optimizer_counts(counters)
            for t in range(spec.horizon):
                actions, _, data = agent.step(states, observations, env_steps, dones,
                                              deterministic=False, return_step_data=True, build_infos=False)
                next_states, next_obs = [], []
                rewards = np.zeros(spec.lanes, np.float64)
                next_dones = np.zeros(spec.lanes, bool)
                for lane, env in enumerate(envs):
                    ns, no, reward, done, _, _ = physical_step(env, actions[lane])
                    counts["training_transitions"] += 1
                    counts["training_episodes"] += int(done)
                    next_states.append(ns)
                    next_obs.append(no)
                    rewards[lane], next_dones[lane] = reward, done
                if not np.all(next_dones == (t == spec.horizon - 1)):
                    raise ValueError("unexpected training episode boundary")
                next_states, next_obs = np.stack(next_states), np.stack(next_obs)
                if rollout == 0:
                    update_digest(first_digest, states, observations, actions, rewards,
                                  data["team_skills"], data["agent_skills"], data["action_logprobs"])
                if t % spec.k == 0:
                    if not np.asarray(data["d2_team_decision"]).all():
                        raise ValueError("fixed k10 boundary was not a full native team decision")
                    for lane, skill in enumerate(data["agent_skills"]):
                        label_hist[np.arange(spec.n_agents), skill] += 1
                        key = ",".join(map(str, [int(data["team_skills"][lane]), *map(int, skill)]))
                        joint_hist[key] = joint_hist.get(key, 0) + 1
                saturation += int((np.abs(actions) > 1).sum())
                action_coordinates += actions.size
                agent.store_transition_batch(states=states, next_states=next_states.copy(),
                    observations=observations, next_observations=next_obs.copy(), actions=actions,
                    rewards=rewards, dones=next_dones, infos_batch=None, rollout_step_idx=t, step_data=data)
                counts["stored_transitions"] += spec.lanes
                returns += rewards
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        no, info = env.reset()
                        next_obs[lane] = np.asarray(no, np.float32)
                        next_states[lane] = np.asarray(info["state"], np.float64)
                        agent.reset_env_state(lane)
                        env_steps[lane] = 0
                    else:
                        env_steps[lane] += 1
                states, observations, dones = next_states, next_obs, next_dones
            losses = agent.update(last_values=np.zeros((spec.lanes, spec.n_agents), np.float32),
                                  dones=dones.copy(), steps_in_buffer=spec.horizon,
                                  last_state=states.copy(), last_observations=observations.copy())
            counts["native_updates"] += 1
            after = support.optimizer_counts(counters)
            aux = agent.auxiliary_history[-1]
            expected_windows = spec.lanes * spec.horizon // spec.k
            expected_aux_steps = (expected_windows + 127) // 128
            if (aux["samples"] != expected_windows or aux["discarded_terminal_windows"] != 0
                    or aux["head_optimizer_steps"] != dict(G=expected_aux_steps, P=expected_aux_steps)
                    or aux["trunk_optimizer_steps"] != (0 if arm == "D" else expected_aux_steps)):
                raise ValueError("auxiliary factual exposure differs from the fixed protocol")
            if any(after[key] <= before[key] for key in after):
                raise ValueError("a native optimizer group did not update")
            predictions = {"rollout": rollout + 1, **jsonable(aux.pop("raw_prediction_rows"))}
            prediction_bytes = (json.dumps(predictions, allow_nan=False) + "\n").encode()
            with (out / "auxiliary_predictions.jsonl").open("ab") as stream:
                stream.write(prediction_bytes)
            aux["raw_predictions"] = {
                "file": "auxiliary_predictions.jsonl", "line": rollout + 1,
                "sha256": hashlib.sha256(prediction_bytes).hexdigest(),
                "rows": aux["samples"], "timing": "after this rollout's auxiliary update",
            }
            if rollout == 0:
                summary["first_rollout_facts_sha256"] = first_digest.hexdigest()
            row = {"rollout": rollout + 1, "training_transitions": counts["training_transitions"],
                   "returns_U": returns, "training_J": spec.n_agents * returns / spec.horizon,
                   "native_losses": losses, "native_optimizer_calls": after,
                   "optimizer_delta": {k: after[k] - before[k] for k in after},
                   "auxiliary": aux,
                   "relative_initialization_displacement": native._exposure_line(agent, theta0),
                   "raw_saturation_fraction": saturation / action_coordinates,
                   "wall_seconds": time.perf_counter() - began}
            summary["training_rows"].append(jsonable(row))
            summary["native_optimizer_calls"] = after
            summary["actual_label_occupancy"] = label_hist
            summary["actual_joint_occupancy"] = joint_hist
            with (out / "training.jsonl").open("a") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            agent.clear_buffers()
            write_json(out / "summary.json", summary)
        summary["checkpoints"]["final"] = save_checkpoint(agent, out / "final.pt", summary["learner_config"], spec.rollouts)
        summary["panels"]["final_own"] = evaluate_panel(agent, spec, spec.own_final_base, "own", counter=counts)
        write_json(out / "summary.json", summary)
        summary["panels"]["final_uniform"] = evaluate_panel(agent, spec, spec.uniform_final_base, "uniform", counter=counts)
        write_json(out / "summary.json", summary)
        diagnostic = combination_diagnostic(agent, spec, counter=counts)
        write_json(out / "combination_diagnostic.json", diagnostic)
        summary["diagnostic"] = {k: v for k, v in diagnostic.items() if k != "rows"}
        summary["diagnostic"]["file"] = "combination_diagnostic.json"
        summary["diagnostic"]["sha256"] = native._sha256_file(out / "combination_diagnostic.json")
        summary["auxiliary_predictions"] = {
            "file": "auxiliary_predictions.jsonl",
            "sha256": native._sha256_file(out / "auxiliary_predictions.jsonl"),
            "batches": spec.rollouts,
        }
        summary["final_native_digest"] = native_digest(agent)
        summary["status"] = "complete"
    except BaseException as exc:
        summary["status"] = "failed"
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {"process_wall_seconds": time.perf_counter() - start,
                                "user_cpu_seconds": usage.ru_utime - cpu_start.ru_utime,
                                "system_cpu_seconds": usage.ru_stime - cpu_start.ru_stime,
                                "peak_process_rss_kib": usage.ru_maxrss,
                                "scope": "runner body; process RSS lifetime peak; shared-node occupancy unmeasured"}
        if torch.device(device).type == "cuda" and torch.cuda.is_initialized():
            summary["resources"]["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated(torch.device(device))
            summary["resources"]["peak_cuda_reserved_bytes"] = torch.cuda.max_memory_reserved(torch.device(device))
        if agent is not None:
            summary["auxiliary_history"] = jsonable(agent.auxiliary_history)
        if counters is not None:
            summary["native_optimizer_calls"] = support.optimizer_counts(counters)
        write_json(out / "summary.json", summary)
        for env in envs:
            env.close()
    return summary
