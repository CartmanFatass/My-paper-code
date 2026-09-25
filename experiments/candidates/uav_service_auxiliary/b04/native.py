"""B04: a fixed change to real risk weight in both native hierarchy returns."""

from __future__ import annotations

import resource
import time
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch

from hmasd.agent import HMASDAgent
from ..b01.native import (
    NativeSpec, _bootstrap_values, _json_default, _module_parameters, _write_progress,
    active_config, initialization_fingerprint, make_config, make_env, optimizer_steps,
    parameter_displacement, seed_everything, sha256_file,
)
from ..b03.facts import array_digest
from ..b03.native import assert_finite
from .evaluation import TRACE_FIELDS, evaluate, metric_row

OBJECT_ID = "UAV-SERVICE-RISK-B04"
TRAINING_SEED = 914021
EXTRA_COST = {"N": 0.0, "R": 2.0}


@dataclass(frozen=True)
class B04Spec(NativeSpec):
    seed: int = TRAINING_SEED
    eval_seeds: tuple[int, ...] = tuple(range(937001, 937009))
    final_seeds: tuple[int, ...] = tuple(range(938001, 938033))
    eval_rollouts: tuple[int, ...] = (0, 10, 20, 30)
    fact_seeds: tuple[int, ...] = ()


def production_spec(seed: int) -> B04Spec:
    if seed != TRAINING_SEED:
        raise ValueError("unplanned training seed")
    return B04Spec()


def training_reward(arm, native_reward, reward_info):
    metric_row(native_reward, reward_info)
    return float(native_reward) - EXTRA_COST[arm] * float(reward_info["return_constraint_cost"])


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, default=_json_default, allow_nan=False) + "\n")


def optimizer_state_steps(agent):
    names = {"high": "coordinator_optimizer", "low_actor": "discoverer_actor_optimizer",
             "low_critic": "discoverer_critic_optimizer", "team_disc": "team_discriminator_optimizer",
             "individual_disc": "individual_discriminator_optimizer"}
    result = {}
    for name, attr in names.items():
        optimizer = getattr(agent, attr)
        steps = [int(state["step"].item() if torch.is_tensor(state["step"]) else state["step"])
                 for state in optimizer.state.values() if "step" in state]
        result[name] = {"initialized_parameters": len(steps), "min": min(steps, default=0),
                        "max": max(steps, default=0), "sum": sum(steps)}
    return result


def run_native(*, arm: str, out: Path, launch_sha: str, device_name="cuda", threads=4,
               spec: B04Spec | None = None, object_id: str = OBJECT_ID):
    spec = spec or B04Spec()
    if arm not in EXTRA_COST:
        raise ValueError("arm must be N or R")
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    torch.set_num_threads(threads)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json", "progress.jsonl")):
        raise FileExistsError(f"output already contains scientific records: {out}")
    out.mkdir(parents=True, exist_ok=True)
    started, cpu_started = time.time(), resource.getrusage(resource.RUSAGE_SELF)
    timings = {key: 0.0 for key in ("preparation", "collection", "native_update", "evaluation", "checkpoint")}
    summary = {"object_id": object_id, "status": "INCOMPLETE", "failure": None,
               "arm": arm, "seed": spec.seed, "launch_sha": launch_sha,
               "device": str(device), "torch_threads": torch.get_num_threads(),
               "training_return_coefficient": 2.0 + EXTRA_COST[arm],
               "evaluation_return_coefficient": 2.0,
               "counts": {key: 0 for key in ("transitions", "agent_rows", "rollouts", "episodes",
                                             "evaluations", "evaluation_transitions")},
               "stage_wall_seconds": timings, "evaluations": {}, "updates": [],
               "training_rollouts": [], "artifacts": {}}
    envs = []
    write_json(out / "summary.json", summary)
    try:
        stage_start = time.perf_counter()
        seed_everything(spec.seed, device)
        config = make_config(spec)
        if config.lambda_return != 2.0 or config.lambda_e != 1.0:
            raise ValueError("native S7 reward coefficients changed")
        write_json(out / "config.json", {
            "spec": asdict(spec), "active": json.loads(json.dumps(active_config(config)), parse_constant=str),
            "arm": arm, "extra_training_cost_coefficient": EXTRA_COST[arm],
            "reward_units": "shared S7 scalar, no division by N",
            "training_objective": "native_reward - extra_coefficient * actual_post_transition_return_cost",
        })
        summary["config_sha256"] = sha256_file(out / "config.json")
        agent = HMASDAgent(config, log_dir=str(out / "logs"), device=device)
        initial = _module_parameters(agent)
        summary["initialization_sha256"] = initialization_fingerprint(agent)
        timings["preparation"] += time.perf_counter() - stage_start

        def panel(label, seeds):
            stage_start = time.perf_counter()
            trace_path = out / "trajectories" / f"evaluation_{label}.npz"
            result = evaluate(agent, config, seeds, device, policy_seed=spec.seed,
                              log_dir=out / "evaluation_logs", trace_path=trace_path)
            summary["counts"]["evaluations"] += len(result["worlds"])
            summary["counts"]["evaluation_transitions"] += result["actual_transitions"]
            summary["artifacts"][str(trace_path.relative_to(out))] = result["trace_sha256"]
            timings["evaluation"] += time.perf_counter() - stage_start
            return result

        if 0 in spec.eval_rollouts:
            summary["evaluations"]["0"] = panel("0", spec.eval_seeds)
        envs = [make_env(config, spec.seed + lane) for lane in range(spec.lanes)]
        resets = [env.reset(seed=spec.seed + lane) for lane, env in enumerate(envs)]
        observations = np.asarray([row[0] for row in resets], dtype=np.float32)
        states = np.asarray([row[1]["state"] for row in resets], dtype=np.float32)
        dones, env_steps = np.ones(spec.lanes, dtype=bool), np.zeros(spec.lanes, dtype=np.int64)
        straddling_boundaries = 0
        for rollout in range(1, spec.rollouts + 1):
            stage_start = time.perf_counter()
            shape = (spec.rollout_length, spec.lanes)
            native_rewards, train_rewards = np.empty(shape), np.empty(shape)
            metrics = np.empty((*shape, len(TRACE_FIELDS)))
            commands = np.empty((*shape, config.n_agents, config.action_dim), dtype=np.float32)
            ends = np.empty((*shape, 2), dtype=bool)
            for step in range(spec.rollout_length):
                current_obs, current_states = observations.copy(), states.copy()
                actions, _, step_data = agent.step(
                    current_states, current_obs, env_steps, dones, deterministic=False,
                    return_step_data=True, build_infos=False)
                commands[step] = actions
                next_obs, next_states, infos = [], [], []
                for lane, env in enumerate(envs):
                    obs, reward, terminated, truncated, info = env.step(actions[lane])
                    native_rewards[step, lane] = float(reward)
                    metrics[step, lane] = metric_row(reward, info["reward_info"])
                    train_rewards[step, lane] = training_reward(arm, reward, info["reward_info"])
                    ends[step, lane] = (terminated, truncated)
                    next_obs.append(np.asarray(obs, dtype=np.float32))
                    next_states.append(np.asarray(info["next_state"], dtype=np.float32))
                    infos.append(info)
                next_obs, next_states = np.asarray(next_obs), np.asarray(next_states)
                next_dones = ends[step].any(axis=-1)
                # The sole objective intervention: both native return paths consume this scalar.
                agent.store_transition_batch(
                    current_states, next_states, current_obs, next_obs, actions,
                    train_rewards[step].astype(np.float32), next_dones,
                    infos_batch=infos, rollout_step_idx=step, step_data=step_data)
                # DiscriminatorBuffer retains row views of terminal inputs when
                # normalizers are off. Reset into distinct collector arrays.
                collector_obs, collector_states = next_obs.copy(), next_states.copy()
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        summary["counts"]["episodes"] += 1
                        agent.reset_env_state(lane)
                        obs, info = env.reset(seed=None)
                        collector_obs[lane] = np.asarray(obs, dtype=np.float32)
                        collector_states[lane] = np.asarray(info["state"], dtype=np.float32)
                        env_steps[lane] = 0
                    else:
                        env_steps[lane] += 1
                observations, states, dones = collector_obs, collector_states, next_dones
                summary["counts"]["transitions"] += spec.lanes
                summary["counts"]["agent_rows"] += spec.lanes * config.n_agents
                if (step + 1) % 100 == 0 or step + 1 == spec.rollout_length:
                    _write_progress(out, summary, {"event": "collection", "rollout": rollout,
                                    "step": step + 1, "transitions": summary["counts"]["transitions"]})
            timings["collection"] += time.perf_counter() - stage_start
            data = agent.rollout_buffer._get_full_rollout_data()
            if data is None or data["num_actual_steps"] != spec.rollout_length:
                raise RuntimeError("incomplete rollout storage")
            np.testing.assert_allclose(data["reward_env"],
                                       np.broadcast_to(train_rewards.astype(np.float32)[..., None], data["reward_env"].shape),
                                       rtol=0, atol=0)
            trace = out / "trajectories" / f"training_{rollout:02d}.npz"
            trace.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(trace, native_reward=native_rewards, training_reward=train_rewards,
                                metrics=metrics, metric_fields=np.asarray(TRACE_FIELDS), actions=commands, ends=ends)
            summary["artifacts"][str(trace.relative_to(out))] = sha256_file(trace)
            audit = None
            if rollout == 1:
                summary["first_collection_sha256"] = array_digest(
                    observations=data["obs"], skills=data["agent_skills"], actions=commands,
                    native_rewards=native_rewards, metrics=metrics, ends=ends,
                    hidden=data["gru_hidden_states"][0])
                audit = {key: np.asarray(data[key]).copy() for key in (
                    "rewards", "reward_env", "reward_team_disc", "reward_ind_disc", "values",
                    "dones", "masks", "high_level_rewards", "high_level_valid_mask",
                    "high_level_state_values", "high_level_agent_values",
                    "high_level_elapsed_steps", "high_level_terminal")}
                audit.update(native_reward=native_rewards, training_reward=train_rewards,
                             return_cost=metrics[..., TRACE_FIELDS.index("return_constraint_cost")])
            stage_start = time.perf_counter()
            before = _module_parameters(agent)
            last_values = _bootstrap_values(agent, states, dones)
            native_update = agent.update(last_values=last_values, dones=dones,
                                         steps_in_buffer=spec.rollout_length,
                                         last_state=states, last_observations=observations)
            assert_finite(native_update)
            movement = parameter_displacement(before, agent)
            timings["native_update"] += time.perf_counter() - stage_start
            if audit is not None:
                audit.update(advantages=agent.rollout_buffer.advantages.copy(),
                             returns=agent.rollout_buffer.returns.copy(), last_values=last_values,
                             final_dones=dones, gamma=np.asarray(config.gamma), gae_lambda=np.asarray(config.gae_lambda))
                for name in ("high_level_team_advantages", "high_level_agent_advantages",
                             "high_level_team_returns", "high_level_agent_returns"):
                    audit[name] = getattr(agent.rollout_buffer, name).copy()
                audit_path = out / "first_rollout_audit.npz"
                np.savez_compressed(audit_path, **audit)
                summary["artifacts"][audit_path.name] = sha256_file(audit_path)
                summary["first_update_policy_sha256"] = initialization_fingerprint(agent)
            summary["updates"].append({"rollout": rollout, "native": native_update,
                "native_parameter_displacement_l2": movement, "optimizer_steps": optimizer_steps(agent),
                "optimizer_state_steps": optimizer_state_steps(agent)})
            summary["training_rollouts"].append({
                "rollout": rollout, "raw_native_J_by_lane": native_rewards.sum(axis=0),
                "training_return_by_lane": train_rewards.sum(axis=0),
                "metrics_by_lane": {field: metrics[..., col].sum(axis=0) for col, field in enumerate(TRACE_FIELDS)},
                "terminated": int(ends[..., 0].sum()), "truncated": int(ends[..., 1].sum()),
                "rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)})
            agent.clear_buffers()
            if rollout < spec.rollouts:
                straddling_boundaries += int(np.count_nonzero(~dones))
            summary["counts"]["rollouts"] = rollout
            if rollout in spec.eval_rollouts:
                summary["evaluations"][str(rollout)] = panel(str(rollout), spec.eval_seeds)
            _write_progress(out, summary, {"event": "rollout_complete", "rollout": rollout,
                            "transitions": summary["counts"]["transitions"]})
            print(f"arm={arm} rollout={rollout}/{spec.rollouts}", flush=True)
        steps, displacement = optimizer_steps(agent), parameter_displacement(initial, agent)
        if summary["counts"]["transitions"] != spec.transitions:
            raise RuntimeError("native transition count mismatch")
        if any(value <= 0 for value in steps.values()) or any(value <= 0 for value in displacement.values()):
            raise RuntimeError("one or more native learners did not update/move")
        summary["final_evaluation"] = panel("final", spec.final_seeds)
        stage_start = time.perf_counter()
        checkpoint = out / "checkpoint_final" / "agent.pt"
        checkpoint.parent.mkdir()
        agent.save_model(checkpoint)
        summary["artifacts"][str(checkpoint.relative_to(out))] = sha256_file(checkpoint)
        timings["checkpoint"] += time.perf_counter() - stage_start
        summary.update(status="COMPLETE", optimizer_steps=steps,
                       optimizer_state_steps=optimizer_state_steps(agent),
                       initialization_displacement_l2=displacement,
                       straddling_rollout_boundaries=straddling_boundaries,
                       final_policy_sha256=initialization_fingerprint(agent))
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary.update(wall_seconds=time.time() - started,
                       cpu_user_seconds=usage.ru_utime - cpu_started.ru_utime,
                       cpu_system_seconds=usage.ru_stime - cpu_started.ru_stime,
                       peak_rss_kib=int(usage.ru_maxrss), rss_scope="runner process high-water mark")
        write_json(out / "summary.json", summary)
