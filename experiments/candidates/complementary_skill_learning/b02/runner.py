"""Prospective B02 M/T fit with a single native reward-objective treatment."""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import resource
import sys
import time
import traceback

import numpy as np
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from scripts import run_fsd_uav_individual_renewal_b01 as support


DIRECTION = "complementary_skill_learning"
OBJECT = "complementary_skill_b02"
EXPECTED_NATIVE_OPTIMIZER_CALLS = {
    "coordinator": 675,
    "discoverer_actor": 101250,
    "discoverer_critic": 101250,
    "team_discriminator": 675,
    "individual_discriminator": 2700,
}
EFFECTIVE_FIELDS = (
    "lambda_e", "lambda_D", "lambda_d", "legacy_mi_reward_coef",
    "use_prior_corrected_intrinsic", "normalize_intrinsic_mi",
    "intrinsic_mi_clip", "enhanced_state", "w_entropy", "process_reward_coef", "process_reward_clip",
    "use_process_reward_for_discoverer", "use_process_exploration",
    "use_discrete_skill_lifetimes", "use_horizon_window",
)


@dataclass(frozen=True)
class Spec:
    n_agents: int = 6
    n_users: int = 50
    k: int = 10
    horizon: int = 500
    lanes: int = 16
    rollouts: int = 45
    eval_lanes: int = 32
    init_seed: int = 260923911
    head_seed: int = 260923912
    train_rng_seed: int = 260923913
    aux_seed: int = 260923914
    eval_rng_seed: int = 260923915
    train_world_base: int = 1800000
    eval_world_base: int = 1900000
    threads: int = 4
    small_model: bool = False


DEFAULT_SPEC = Spec()
jsonable = b01.jsonable
write_json = b01.write_json
seed_rng = b01.seed_rng
update_digest = b01.update_digest
native_digest = b01.native_digest
frozen_digest = b01.frozen_digest
make_envs = b01.make_envs
physical_step = b01.physical_step
evaluate_panel = b01.evaluate_panel


def make_config(spec: Spec, envs, arm: str):
    if arm not in ("M", "T"):
        raise ValueError(arm)
    config = b01.make_config(spec, envs)
    config.legacy_mi_reward_coef = 0.5 if arm == "M" else 0.0
    return config


def effective_config(config) -> dict:
    result = support.config_snapshot(config)
    result.update({name: getattr(config, name) for name in EFFECTIVE_FIELDS
                   if hasattr(config, name)})
    result["effective_team_discriminator_reward_coef"] = (
        float(config.legacy_mi_reward_coef) * float(config.lambda_D)
    )
    result["effective_individual_discriminator_reward_coef"] = (
        float(config.legacy_mi_reward_coef) * float(config.lambda_d)
    )
    result["resolved_switches"] = {
        "disable_discriminator_rewards": bool(
            getattr(config, "disable_discriminator_rewards", False)),
        "disable_discriminator_training": bool(
            getattr(config, "disable_discriminator_training", False)),
        "ha_ctse": bool(getattr(config, "use_horizon_window", False)),
        "process_exploration": bool(getattr(config, "use_process_exploration", False)),
        "discrete_skill_lifetimes": bool(
            getattr(config, "use_discrete_skill_lifetimes", False)),
        "process_reward_active_for_discoverer": bool(
            getattr(config, "use_process_exploration", False)
            and getattr(config, "use_process_reward_for_discoverer", False)),
    }
    return jsonable(result)


def save_checkpoint(agent, path: Path, config: dict, stage: int):
    body = {
        "object_id": OBJECT, "arm": agent.objective_arm, "stage": stage,
        "config": config,
        "native": {name: getattr(agent, name).state_dict() for name in b01.MODULES
                   if getattr(agent, name) is not None},
        "normalizers": {name: copy.deepcopy(getattr(agent, name)) for name in b01.NORMALIZERS},
        "auxiliary": agent.auxiliary_state_dict(),
        "reward_telemetry": agent.reward_telemetry(),
    }
    torch.save(body, path)
    return {"file": path.name, "sha256": b01.native._sha256_file(path),
            "bytes": path.stat().st_size, "native_digest": native_digest(agent)}


def _independent_low_gae(buffer, steps: int, gamma: float, gae_lambda: float):
    rewards = buffer.rewards[:steps].astype(np.float32)
    values = buffer.values[:steps].astype(np.float32)
    dones = buffer.dones[:steps]
    masks = buffer.masks[:steps]
    expected = np.zeros_like(rewards)
    last = np.zeros_like(rewards[0])
    for t in reversed(range(steps)):
        next_values = np.zeros_like(values[t]) if t == steps - 1 else values[t + 1]
        nonterminal = np.zeros_like(rewards[t]) if t == steps - 1 else 1.0 - dones[t]
        delta = rewards[t] + gamma * next_values * nonterminal - values[t]
        last = delta + gamma * gae_lambda * nonterminal * last
        expected[t] = last * masks[t, :, None]
    return expected, expected + values


def _first_rollout_audit(agent, raw_rewards: np.ndarray, steps: int, out: Path):
    buffer = agent.rollout_buffer
    expected_adv, expected_returns = _independent_low_gae(
        buffer, steps, float(agent.config.gamma), float(agent.config.gae_lambda)
    )
    np.testing.assert_allclose(buffer.advantages[:steps], expected_adv, rtol=2e-5, atol=2e-5)
    np.testing.assert_allclose(buffer.returns[:steps], expected_returns, rtol=2e-5, atol=2e-5)
    d2 = buffer.get_d2_tables(steps)
    if d2 is None:
        raise ValueError("B02 requires the native D2 table")
    expected_team_rows = raw_rewards.shape[1] * steps // int(agent.config.k)
    expected_agent_rows = expected_team_rows * int(agent.config.n_agents)
    if (int(d2["team_valid"].sum()) != expected_team_rows
            or int(d2["agent_valid"].sum()) != expected_agent_rows):
        raise ValueError("D2 audit did not contain every fixed k10 segment")
    if (not np.all(d2["team_elapsed"][d2["team_valid"]] == int(agent.config.k))
            or not np.all(d2["agent_elapsed"][d2["agent_valid"]] == int(agent.config.k))):
        raise ValueError("D2 audit contained a non-k10 segment")
    if (int(d2["team_terminal"].sum()) != raw_rewards.shape[1]
            or int(d2["agent_terminal"].sum())
            != raw_rewards.shape[1] * int(agent.config.n_agents)):
        raise ValueError("D2 audit did not retain every terminal segment")
    np.testing.assert_allclose(
        buffer.reward_env[:steps],
        np.repeat(raw_rewards[:, :, None], int(agent.config.n_agents), axis=2),
        rtol=1e-6, atol=1e-6,
    )
    gamma = float(agent.config.gamma)
    for env in range(raw_rewards.shape[1]):
        for start in np.flatnonzero(d2["team_valid"][:, env]):
            elapsed = int(d2["team_elapsed"][start, env])
            expected = float(np.dot(raw_rewards[start:start + elapsed, env],
                                    gamma ** np.arange(elapsed)))
            if not np.isclose(d2["team_reward"][start, env], expected, rtol=1e-5, atol=1e-5):
                raise ValueError("D2 team segment did not retain raw environment rewards")
        for member in range(agent.config.n_agents):
            for start in np.flatnonzero(d2["agent_valid"][:, env, member]):
                elapsed = int(d2["agent_elapsed"][start, env, member])
                expected = float(np.dot(raw_rewards[start:start + elapsed, env],
                                        gamma ** np.arange(elapsed)))
                if not np.isclose(d2["agent_reward"][start, env, member], expected,
                                  rtol=1e-5, atol=1e-5):
                    raise ValueError("D2 agent segment did not retain raw environment rewards")
    team_scores, individual_scores = agent.reward_score_arrays()
    if team_scores.shape != (steps, raw_rewards.shape[1]):
        raise ValueError("unweighted team discriminator score audit is incomplete")
    if individual_scores.shape != (steps, raw_rewards.shape[1], agent.config.n_agents):
        raise ValueError("unweighted individual discriminator score audit is incomplete")
    arrays = {
        "raw_environment_rewards": raw_rewards,
        "unweighted_team_discriminator_scores": team_scores,
        "unweighted_individual_discriminator_scores": individual_scores,
        "stored_low_rewards": buffer.rewards[:steps],
        "reward_env": buffer.reward_env[:steps],
        "reward_team_disc": buffer.reward_team_disc[:steps],
        "reward_ind_disc": buffer.reward_ind_disc[:steps],
        "low_values": buffer.values[:steps],
        "low_dones": buffer.dones[:steps],
        "low_masks": buffer.masks[:steps],
        "low_advantages": buffer.advantages[:steps],
        "low_returns": buffer.returns[:steps],
        "independent_low_advantages": expected_adv,
        "independent_low_returns": expected_returns,
    }
    arrays.update({"d2_" + key: value for key, value in d2.items()})
    path = out / "first_rollout_reward_gae_audit.npz"
    np.savez_compressed(path, **arrays)
    digest = hashlib.sha256()
    update_digest(digest, *arrays.values())
    return {
        "file": path.name, "sha256": b01.native._sha256_file(path),
        "content_sha256": digest.hexdigest(), "array_shapes": {
            key: list(np.asarray(value).shape) for key, value in arrays.items()
        },
        "low_gae_max_abs_error": float(np.max(np.abs(buffer.advantages[:steps] - expected_adv))),
        "low_returns_max_abs_error": float(np.max(np.abs(buffer.returns[:steps] - expected_returns))),
        "d2_team_rows": int(d2["team_valid"].sum()),
        "d2_agent_rows": int(d2["agent_valid"].sum()),
        "d2_team_terminal_rows": int(d2["team_terminal"].sum()),
        "d2_agent_terminal_rows": int(d2["agent_terminal"].sum()),
    }


def _telemetry_delta(after: dict, before: dict) -> dict:
    result = dict(after)
    for key in ("batch_calls", "environment_rows", "team_discriminator_forwards",
                "individual_discriminator_forwards", "finite_failures",
                "component_identity_failures", "fallbacks"):
        result[key] = int(after[key]) - int(before[key])
    for key in ("storage_batch_calls", "storage_expected_rows", "storage_verified_rows",
                "storage_failures"):
        result[key] = int(after[key]) - int(before[key])
    return result


def run_fit(arm, out, launch_sha, *, spec=DEFAULT_SPEC, device="cuda", admission=None):
    from .learning import ObjectiveComparisonAgent
    if arm not in ("M", "T"):
        raise ValueError(arm)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists():
        raise ValueError("a fit never overwrites an existing summary")
    torch.set_num_threads(spec.threads)
    logging.getLogger().setLevel(logging.WARNING)
    started = time.perf_counter()
    cpu_started = resource.getrusage(resource.RUSAGE_SELF)
    counts = dict.fromkeys(("started_fits", "model_constructions", "training_transitions",
                           "stored_transitions", "training_episodes", "native_updates",
                           "evaluation_transitions", "evaluation_episodes"), 0)
    summary = {
        "object_id": OBJECT, "direction": DIRECTION, "arm": arm, "launch_sha": launch_sha,
        "status": "incomplete", "spec": asdict(spec), "device": str(device),
        "admission": admission, "counts": counts, "training_rows": [], "panels": {},
        "checkpoints": {},
    }
    summary["runtime"] = {
        "python": sys.version, "numpy": np.__version__, "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda, "torch_threads": torch.get_num_threads(),
        "thread_environment": {key: os.environ.get(key) for key in
                               ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "learner_dtype": "float32", "reward_return_dtype": "float64",
    }
    write_json(out / "config.json", {"object_id": OBJECT, "arm": arm,
                                     "spec": asdict(spec), "launch_sha": launch_sha,
                                     "device": str(device)})
    envs = []
    agent = counters = None
    try:
        if torch.device(device).type == "cuda":
            torch.cuda.reset_peak_memory_stats(torch.device(device))
            summary["runtime"]["cuda_device"] = torch.cuda.get_device_name(torch.device(device))
        envs = make_envs(spec, spec.lanes, spec.train_world_base)
        config = make_config(spec, envs, arm)
        summary["learner_config"] = effective_config(config)
        seed_rng(spec.init_seed)
        agent = ObjectiveComparisonAgent(config, arm, spec.head_seed, spec.aux_seed,
                                         str(out / "learner_logs"), torch.device(device))
        counts["model_constructions"] += 1
        theta0 = b01.native._capture_theta0(agent)
        counters = support.optimizer_counters(agent)
        summary["initial_native_digest"] = native_digest(agent)
        summary["auxiliary_parameter_counts"] = jsonable(agent.parameter_counts)
        summary["auxiliary_architecture"] = jsonable(agent.auxiliary_architecture)
        summary["checkpoints"]["initial"] = save_checkpoint(
            agent, out / "initial.pt", summary["learner_config"], 0
        )
        seed_rng(spec.train_rng_seed)
        initial_eval_started = time.perf_counter()
        summary["panels"]["initial_own"] = evaluate_panel(
            agent, spec, spec.eval_world_base, "own", counter=counts
        )
        summary["panels"]["initial_uniform"] = evaluate_panel(
            agent, spec, spec.eval_world_base, "uniform", counter=counts
        )
        summary.setdefault("timing", {})["initial_evaluation_wall_seconds"] = (
            time.perf_counter() - initial_eval_started
        )
        states, observations = b01.native._reset_all(envs)
        env_steps = np.zeros(spec.lanes, np.int64)
        dones = np.zeros(spec.lanes, bool)
        agent.train(True)
        counts["started_fits"] += 1
        first_digest = hashlib.sha256()
        label_hist = np.zeros((spec.n_agents, 6), np.int64)
        joint_hist: dict[str, int] = {}
        for rollout in range(spec.rollouts):
            rollout_started = time.perf_counter()
            collection_started = time.perf_counter()
            raw_returns = np.zeros(spec.lanes, np.float64)
            raw_rewards = np.zeros((spec.horizon, spec.lanes), np.float64)
            saturation = action_coordinates = 0
            before_counts = support.optimizer_counts(counters)
            before_reward = agent.reward_telemetry()
            for t in range(spec.horizon):
                actions, _, data = agent.step(states, observations, env_steps, dones,
                                              deterministic=False, return_step_data=True,
                                              build_infos=False)
                next_states, next_obs = [], []
                rewards = np.zeros(spec.lanes, np.float64)
                next_dones = np.zeros(spec.lanes, bool)
                for lane, env in enumerate(envs):
                    ns, no, reward, done, _, _ = physical_step(env, actions[lane])
                    counts["training_transitions"] += 1
                    counts["training_episodes"] += int(done)
                    next_states.append(ns); next_obs.append(no)
                    rewards[lane], next_dones[lane] = reward, done
                if not np.all(next_dones == (t == spec.horizon - 1)):
                    raise ValueError("unexpected training episode boundary")
                next_states, next_obs = np.stack(next_states), np.stack(next_obs)
                raw_rewards[t] = rewards
                if rollout == 0:
                    update_digest(first_digest, states, observations, actions, rewards,
                                  data["team_skills"], data["agent_skills"],
                                  data["action_logprobs"])
                if t % spec.k == 0:
                    if not np.asarray(data["d2_team_decision"]).all():
                        raise ValueError("fixed k10 boundary was not a full native team decision")
                    for lane, skills in enumerate(data["agent_skills"]):
                        label_hist[np.arange(spec.n_agents), skills] += 1
                        key = ",".join(map(str, [int(data["team_skills"][lane]), *map(int, skills)]))
                        joint_hist[key] = joint_hist.get(key, 0) + 1
                saturation += int((np.abs(actions) > 1).sum())
                action_coordinates += actions.size
                verified_before = int(agent.reward_telemetry()["storage_verified_rows"])
                stored_rows = agent.store_transition_batch(
                    states=states, next_states=next_states.copy(), observations=observations,
                    next_observations=next_obs.copy(), actions=actions, rewards=rewards,
                    dones=next_dones, infos_batch=None, rollout_step_idx=t, step_data=data,
                )
                verified_after = int(agent.reward_telemetry()["storage_verified_rows"])
                if (not isinstance(stored_rows, list)
                        or verified_after - verified_before != spec.lanes):
                    raise RuntimeError("B02 collector did not verify every native storage row")
                counts["stored_transitions"] += verified_after - verified_before
                raw_returns += rewards
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        reset_obs, info = env.reset()
                        next_obs[lane] = np.asarray(reset_obs, np.float32)
                        next_states[lane] = np.asarray(info["state"], np.float64)
                        agent.reset_env_state(lane); env_steps[lane] = 0
                    else:
                        env_steps[lane] += 1
                states, observations, dones = next_states, next_obs, next_dones
            collection_seconds = time.perf_counter() - collection_started
            update_started = time.perf_counter()
            losses = agent.update(
                last_values=np.zeros((spec.lanes, spec.n_agents), np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon,
                last_state=states.copy(), last_observations=observations.copy(),
            )
            update_seconds = time.perf_counter() - update_started
            counts["native_updates"] += 1
            after_counts = support.optimizer_counts(counters)
            aux = agent.auxiliary_history[-1]
            expected_windows = spec.lanes * spec.horizon // spec.k
            expected_aux_steps = (expected_windows + 127) // 128
            if (aux["samples"] != expected_windows or aux["discarded_terminal_windows"] != 0
                    or aux["head_optimizer_steps"] != {"G": expected_aux_steps, "P": expected_aux_steps}
                    or aux["trunk_optimizer_steps"] != 0):
                raise ValueError("detached auxiliary exposure differs from the fixed protocol")
            if any(after_counts[key] <= before_counts[key] for key in after_counts):
                raise ValueError("a native optimizer group did not update")
            reward_telemetry = _telemetry_delta(agent.reward_telemetry(), before_reward)
            if (reward_telemetry["fallbacks"] or reward_telemetry["finite_failures"]
                    or reward_telemetry["component_identity_failures"]
                    or reward_telemetry["storage_failures"]
                    or reward_telemetry["batch_calls"] != spec.horizon
                    or reward_telemetry["storage_batch_calls"] != spec.horizon
                    or reward_telemetry["storage_expected_rows"] != spec.horizon * spec.lanes
                    or reward_telemetry["storage_verified_rows"] != spec.horizon * spec.lanes
                    or reward_telemetry["team_discriminator_forwards"] < spec.horizon
                    or reward_telemetry["individual_discriminator_forwards"] < spec.horizon):
                raise ValueError("invalid native reward-path telemetry")
            predictions = {"rollout": rollout + 1, **jsonable(aux.pop("raw_prediction_rows"))}
            prediction_bytes = (json.dumps(predictions, allow_nan=False) + "\n").encode()
            with (out / "auxiliary_predictions.jsonl").open("ab") as stream:
                stream.write(prediction_bytes)
            aux["raw_predictions"] = {
                "file": "auxiliary_predictions.jsonl", "line": rollout + 1,
                "sha256": hashlib.sha256(prediction_bytes).hexdigest(), "rows": aux["samples"],
            }
            if rollout == 0:
                summary["first_rollout_facts_sha256"] = first_digest.hexdigest()
                summary["first_rollout_reward_gae_audit"] = _first_rollout_audit(
                    agent, raw_rewards, spec.horizon, out
                )
            row = {
                "rollout": rollout + 1, "training_transitions": counts["training_transitions"],
                "raw_returns_U": raw_returns, "training_J": spec.n_agents * raw_returns / spec.horizon,
                "stored_low_reward_mean": float(agent.rollout_buffer.rewards[:spec.horizon].mean()),
                "low_advantage_mean": float(agent.rollout_buffer.advantages[:spec.horizon].mean()),
                "low_return_mean": float(agent.rollout_buffer.returns[:spec.horizon].mean()),
                "native_losses": losses, "native_optimizer_calls": after_counts,
                "optimizer_delta": {key: after_counts[key] - before_counts[key]
                                    for key in after_counts},
                "reward_path": reward_telemetry, "auxiliary": aux,
                "relative_initialization_displacement": b01.native._exposure_line(agent, theta0),
                "raw_saturation_fraction": saturation / action_coordinates,
                "collection_wall_seconds": collection_seconds,
                "update_wall_seconds": update_seconds,
                "wall_seconds": time.perf_counter() - rollout_started,
            }
            summary["training_rows"].append(jsonable(row))
            summary["native_optimizer_calls"] = after_counts
            summary["actual_label_occupancy"] = label_hist
            summary["actual_joint_occupancy"] = joint_hist
            with (out / "training.jsonl").open("a") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            agent.clear_buffers()
            write_json(out / "summary.json", summary)
        if not spec.small_model and support.optimizer_counts(counters) != EXPECTED_NATIVE_OPTIMIZER_CALLS:
            raise ValueError("production native optimizer counts differ from the prospective contract")
        summary["checkpoints"]["final"] = save_checkpoint(
            agent, out / "final.pt", summary["learner_config"], spec.rollouts
        )
        final_eval_started = time.perf_counter()
        summary["panels"]["final_own"] = evaluate_panel(
            agent, spec, spec.eval_world_base, "own", counter=counts
        )
        summary["panels"]["final_uniform"] = evaluate_panel(
            agent, spec, spec.eval_world_base, "uniform", counter=counts
        )
        summary["timing"]["final_evaluation_wall_seconds"] = (
            time.perf_counter() - final_eval_started
        )
        summary["timing"]["training_collection_wall_seconds"] = sum(
            row["collection_wall_seconds"] for row in summary["training_rows"]
        )
        summary["timing"]["training_update_wall_seconds"] = sum(
            row["update_wall_seconds"] for row in summary["training_rows"]
        )
        summary["auxiliary_predictions"] = {
            "file": "auxiliary_predictions.jsonl",
            "sha256": b01.native._sha256_file(out / "auxiliary_predictions.jsonl"),
            "batches": spec.rollouts,
        }
        summary["final_native_digest"] = native_digest(agent)
        summary["final_reward_telemetry"] = agent.reward_telemetry()
        summary["status"] = "complete"
    except BaseException as exc:
        summary["status"] = "failed"
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc),
                              "traceback": traceback.format_exc()}
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "process_wall_seconds": time.perf_counter() - started,
            "user_cpu_seconds": usage.ru_utime - cpu_started.ru_utime,
            "system_cpu_seconds": usage.ru_stime - cpu_started.ru_stime,
            "peak_process_rss_kib": usage.ru_maxrss,
            "scope": "runner body; process RSS lifetime peak; shared-node occupancy unmeasured",
        }
        if torch.device(device).type == "cuda" and torch.cuda.is_initialized():
            summary["resources"]["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated(
                torch.device(device))
            summary["resources"]["peak_cuda_reserved_bytes"] = torch.cuda.max_memory_reserved(
                torch.device(device))
        if agent is not None:
            summary["auxiliary_history"] = jsonable(agent.auxiliary_history)
            summary["reward_telemetry"] = agent.reward_telemetry()
            counts["stored_transitions"] = int(
                summary["reward_telemetry"]["storage_verified_rows"]
            )
        if counters is not None:
            summary["native_optimizer_calls"] = support.optimizer_counts(counters)
        write_json(out / "summary.json", summary)
        for env in envs:
            env.close()
    return summary


__all__ = ["DEFAULT_SPEC", "EXPECTED_NATIVE_OPTIMIZER_CALLS", "Spec", "effective_config",
           "make_config", "run_fit", "save_checkpoint"]
