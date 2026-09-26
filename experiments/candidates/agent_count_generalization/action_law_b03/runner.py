"""Four fixed B03 fits differing only in package and training execution law."""
from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import random
import resource
import sys
import time
import traceback
from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC,
    DIRECTION,
    FitSpec,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent, strict_sync
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    capture_parameters,
    digest_agent,
    finite,
    jsonable,
    model_modules,
    native_components,
    optimizer_counts,
    parameter_motion,
    preserve_rng,
    reset_all,
    save_checkpoint,
    seed_rng,
    write_json,
)


OBJECT_ID = "s1_action_law_b03"
EVALUATION_SEED_BASE = 1_200_000


@dataclass(frozen=True)
class TrainingCell:
    index: int
    key: str
    arm: str
    law: str
    seed: int
    tag: str
    initial_digest_source: str | None = None


CELLS = (
    TrainingCell(1, "h6_raw", "H6", "raw", 942201, "s1_action_law_b03_h6_raw_s942201"),
    TrainingCell(2, "set_clip", "SET", "clip", 943201, "s1_action_law_b03_set_clip_s943201"),
    TrainingCell(3, "h6_clip", "H6", "clip", 942201, "s1_action_law_b03_h6_clip_s942201",
                 "s1_action_law_b03_h6_raw_s942201"),
    TrainingCell(4, "set_raw", "SET", "raw", 943201, "s1_action_law_b03_set_raw_s943201",
                 "s1_action_law_b03_set_clip_s943201"),
)
CELL_BY_KEY = {cell.key: cell for cell in CELLS}


def map_training_actions(raw_actions: np.ndarray, law: str) -> np.ndarray:
    if law == "raw":
        return raw_actions.copy()
    if law == "clip":
        return np.clip(raw_actions, -1.0, 1.0)
    raise ValueError(f"unknown B03 action law {law!r}")


def _rng_digest() -> str:
    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    state = np.random.get_state()
    digest.update(state[0].encode("ascii"))
    digest.update(state[1].tobytes())
    digest.update(repr(state[2:]).encode("ascii"))
    digest.update(torch.get_rng_state().cpu().numpy().tobytes())
    return digest.hexdigest()


_RUNTIME_FIELDS = (
    "env_timers", "env_team_skills", "env_agent_skills", "env_log_probs",
    "env_hidden_states", "env_prev_hidden_states", "env_reward_sums",
    "env_pending_high_level", "env_skill_ages", "env_skill_duration_remaining",
    "env_skill_duration_target", "actor_hidden_np", "critic_hidden_np",
    "prev_actor_hidden_np", "prev_critic_hidden_np", "_hidden_state_array_valid",
    "_central_snapshot_states", "_central_snapshot_obs", "_central_snapshot_valid",
)


def runtime_state_digest(agent: Any) -> str:
    digest = hashlib.sha256()
    for name in _RUNTIME_FIELDS:
        if hasattr(agent, name):
            digest.update(name.encode("utf-8"))
            digest.update(pickle.dumps(copy.deepcopy(getattr(agent, name)), protocol=5))
    buffer = getattr(agent, "rollout_buffer", None)
    if buffer is not None and hasattr(buffer, "get_sampler_rng_state"):
        digest.update(b"rollout_buffer.sampler_rng")
        digest.update(pickle.dumps(buffer.get_sampler_rng_state(), protocol=5))
    return digest.hexdigest()


def raw_sigma(agent: Any) -> list[float]:
    action_out = agent.skill_discoverer.actor.act.action_out
    if type(action_out).__name__ != "DiagGaussian":
        raise ValueError("B03 requires the unchanged raw DiagGaussian action distribution")
    bias = action_out.logstd._bias.detach().cpu().reshape(-1)
    return torch.exp(bias).tolist()


def _new_motion() -> dict[str, Any]:
    return {
        "team_steps": 0, "raw_coordinate_violations": 0, "raw_uav_violations": 0,
        "raw_team_step_violations": 0, "raw_excess_sum": 0.0, "raw_excess_max": 0.0,
        "raw_attempted_l2_sum": 0.0, "executed_attempted_l2_sum": 0.0,
        "realized_l2_sum": 0.0, "boundary_truncated_coordinates": 0,
        "boundary_visited_coordinates": 0, "executed_min": float("inf"),
        "executed_max": float("-inf"), "diagnostic_rng_unchanged": True,
        "policy_output_unchanged": True, "old_logprob_unchanged": True,
        "position_storage_dtypes": [], "first_overrange_witness": None,
    }


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {"numerator": int(numerator), "denominator": int(denominator),
            "rate": float(numerator / denominator) if denominator else None}


def _finish_motion(row: dict[str, Any], n: int) -> dict[str, Any]:
    coord = row["team_steps"] * n * 3
    uav = row["team_steps"] * n
    result = dict(row)
    result["raw_coordinate_violations"] = _rate(row["raw_coordinate_violations"], coord)
    result["raw_uav_violations"] = _rate(row["raw_uav_violations"], uav)
    result["raw_team_step_violations"] = _rate(
        row["raw_team_step_violations"], row["team_steps"]
    )
    result["boundary_truncated_coordinates"] = _rate(row["boundary_truncated_coordinates"], coord)
    result["boundary_visited_coordinates"] = _rate(row["boundary_visited_coordinates"], coord)
    result["raw_excess_mean_per_coordinate"] = row["raw_excess_sum"] / coord if coord else None
    result["raw_attempted_l2_mean_per_uav_step"] = row["raw_attempted_l2_sum"] / uav if uav else None
    result["executed_attempted_l2_mean_per_uav_step"] = (
        row["executed_attempted_l2_sum"] / uav if uav else None
    )
    result["realized_l2_mean_per_uav_step"] = row["realized_l2_sum"] / uav if uav else None
    if not row["team_steps"]:
        result["executed_min"] = result["executed_max"] = None
    return jsonable(result)


def _observe_motion(
    telemetry: dict[str, Any], native: Any, before: np.ndarray,
    raw_action: np.ndarray, executed_action: np.ndarray, after: np.ndarray,
    *, rollout: int, t: int, lane: int, reward: float, components: dict[str, float],
) -> None:
    violations = np.abs(raw_action) > 1.0
    excess = np.maximum(np.abs(raw_action) - 1.0, 0.0)
    raw_attempt = raw_action * native.max_speed * native.time_step
    executed_attempt = executed_action * native.max_speed * native.time_step
    unbounded = before + executed_attempt
    bounds_low = np.asarray([0.0, 0.0, native.height_range[0]], dtype=before.dtype)
    bounds_high = np.asarray(
        [native.area_size, native.area_size, native.height_range[1]], dtype=before.dtype
    )
    predicted = np.clip(unbounded, bounds_low, bounds_high)
    tolerance = 8 * np.finfo(before.dtype).eps * max(1.0, float(native.area_size))
    if not np.allclose(after, predicted, atol=tolerance, rtol=8 * np.finfo(before.dtype).eps):
        raise ValueError("native movement differs from B03 executed-action prediction")
    truncated = unbounded != predicted
    visited = np.isclose(after, bounds_low, atol=tolerance, rtol=0.0) | np.isclose(
        after, bounds_high, atol=tolerance, rtol=0.0
    )
    telemetry["team_steps"] += 1
    dtype_name = str(before.dtype)
    if dtype_name not in telemetry["position_storage_dtypes"]:
        telemetry["position_storage_dtypes"].append(dtype_name)
    telemetry["raw_coordinate_violations"] += int(violations.sum())
    telemetry["raw_uav_violations"] += int(violations.any(axis=1).sum())
    telemetry["raw_team_step_violations"] += int(violations.any())
    telemetry["raw_excess_sum"] += float(excess.sum())
    telemetry["raw_excess_max"] = max(telemetry["raw_excess_max"], float(excess.max()))
    telemetry["raw_attempted_l2_sum"] += float(np.linalg.norm(raw_attempt, axis=1).sum())
    telemetry["executed_attempted_l2_sum"] += float(np.linalg.norm(executed_attempt, axis=1).sum())
    telemetry["realized_l2_sum"] += float(np.linalg.norm(after - before, axis=1).sum())
    telemetry["boundary_truncated_coordinates"] += int(truncated.sum())
    telemetry["boundary_visited_coordinates"] += int(visited.sum())
    telemetry["executed_min"] = min(telemetry["executed_min"], float(executed_action.min()))
    telemetry["executed_max"] = max(telemetry["executed_max"], float(executed_action.max()))
    if violations.any() and telemetry["first_overrange_witness"] is None:
        telemetry["first_overrange_witness"] = {
            "rollout": rollout, "step_index_zero_based": t, "lane": lane,
            "raw_action": raw_action.tolist(), "executed_action": executed_action.tolist(),
            "position_before": before.tolist(), "position_after": after.tolist(),
            "predicted_position_after": predicted.tolist(), "reward": float(reward),
            "native_components": components,
        }


def _assert_config_contract(
    config: Any, cell: TrainingCell, *, expected_n: int = 6,
) -> None:
    if float(config.lambda_l) != .05:
        raise ValueError("B03 must retain raw Gaussian entropy coefficient 0.05")
    if str(getattr(config, "continuous_action_distribution", "gaussian")) != "gaussian":
        raise ValueError("B03 must retain the raw Gaussian action distribution")
    if int(config.k) != 10 or int(config.n_agents) != expected_n:
        raise ValueError(f"B03 requires N{expected_n} and k10 for this phase")
    if str(config.count_arm) != cell.arm:
        raise ValueError("B03 package/config mismatch")


def _panel_world_seed(rollout: int, n: int) -> int:
    return EVALUATION_SEED_BASE + rollout * 1000 + n * 100


def evaluate_panel(
    learner: Any, cell: TrainingCell, rollout: int, out: Path,
    summary: dict[str, Any], spec: FitSpec, publish: Callable[[str], None],
) -> None:
    learner_model_before = digest_agent(learner)
    learner_runtime_before = runtime_state_digest(learner)
    learner_rng_before = _rng_digest()
    with preserve_rng():
        for n in spec.test_ns:
            world_seed = _panel_world_seed(rollout, n)
            seed_rng(world_seed + 51)
            envs = make_envs(spec.eval_lanes, world_seed, n, spec.horizon)
            target, hooks = None, []
            row = {
                "after_rollout": rollout,
                "training_team_steps": rollout * spec.train_lanes * spec.horizon,
                "test_n": n,
                "world_seeds": list(range(world_seed, world_seed + spec.eval_lanes)),
                "execution_law": "clip",
                "status": "running", "steps": 0, "episodes": 0,
            }
            summary["panels"].append(row)
            publish(f"evaluation {rollout} N={n} starting")
            try:
                config = make_config(cell.arm, envs, cell.seed, spec)
                _assert_config_contract(config, cell, expected_n=n)
                target = build_agent(config, str(out / "evaluation_logs" / f"r{rollout}_n{n}"))
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                target_before = digest_agent(target)
                states, observations = reset_all(envs)
                steps = np.zeros(spec.eval_lanes, dtype=np.int64)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                components = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
                executed_min, executed_max = float("inf"), float("-inf")
                with torch.no_grad():
                    for t in range(spec.horizon):
                        raw_actions, _, _data = target.step(
                            states, observations, steps, dones, deterministic=True,
                            return_step_data=True, build_infos=False,
                        )
                        finite((raw_actions, _data), "B03 evaluation policy output")
                        raw_before = raw_actions.copy()
                        executed = map_training_actions(raw_actions, "clip")
                        if not np.array_equal(raw_actions, raw_before):
                            raise ValueError("evaluation mapping mutated policy actions")
                        executed_min = min(executed_min, float(executed.min()))
                        executed_max = max(executed_max, float(executed.max()))
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(executed[lane])
                            done = bool(term or trunc)
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_episodes"] += int(done)
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                components[name][lane] += parts[name]
                            states[lane], observations[lane] = info["next_state"], obs
                            dones[lane] = done
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected B03 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B03 evaluation missed fixed terminal boundary")
                j = n * returns / spec.horizon
                means = {name: value / spec.horizon for name, value in components.items()}
                if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6):
                    raise ValueError("B03 evaluation native J/component identity failed")
                if any(calls.values()) or digest_agent(target) != target_before:
                    raise ValueError("B03 evaluation modified target parameters/normalizers")
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                    component_means=jsonable(means), optimizer_calls=calls.copy(),
                    frozen_weights_and_normalizers=True,
                    executed_action_bounds={"minimum": executed_min, "maximum": executed_max},
                    config=config_dict(config),
                )
                write_json(out / f"panel_{rollout:02d}_n{n}.json", row)
                publish(f"evaluation {rollout} N={n} complete")
            except Exception as exc:
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                write_json(out / f"panel_{rollout:02d}_n{n}.json", row)
                raise
            finally:
                for hook in hooks:
                    hook.remove()
                for env in envs:
                    env.close()
                del target
    if digest_agent(learner) != learner_model_before:
        raise ValueError("B03 evaluation modified learner parameters/normalizers")
    if runtime_state_digest(learner) != learner_runtime_before:
        raise ValueError("B03 evaluation modified learner runtime state")
    if _rng_digest() != learner_rng_before:
        raise ValueError("B03 evaluation modified learner/global RNG state")


def collect_rollout(
    agent: Any, envs: list[Any], states: np.ndarray, observations: np.ndarray,
    steps: np.ndarray, dones: np.ndarray, cell: TrainingCell, rollout: int,
    summary: dict[str, Any], spec: FitSpec,
    *, training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any], np.ndarray]:
    telemetry = _new_motion()
    returns = np.zeros(spec.train_lanes, dtype=np.float64)
    component_sums = {
        name: np.zeros(spec.train_lanes, dtype=np.float64) for name in COMPONENTS
    }
    decision_steps: set[int] = set()
    summary["_active_training_rollout"] = {
        "rollout": rollout,
        "phase": "collecting",
        "_telemetry": telemetry,
        "component_sums": component_sums,
        "scalar_returns": returns,
    }
    for t in range(spec.horizon):
        raw_actions, _, data = agent.step(
            states, observations, steps, dones, deterministic=False,
            return_step_data=True, build_infos=False,
        )
        finite((raw_actions, data), "B03 training policy output")
        raw_before = raw_actions.copy()
        logprob_before = np.asarray(data["action_logprobs"]).copy()
        rng_before = _rng_digest()
        executed = map_training_actions(raw_actions, cell.law)
        telemetry["diagnostic_rng_unchanged"] &= rng_before == _rng_digest()
        telemetry["policy_output_unchanged"] &= np.array_equal(raw_actions, raw_before)
        telemetry["old_logprob_unchanged"] &= np.array_equal(
            np.asarray(data["action_logprobs"]), logprob_before
        )
        if np.asarray(data["skill_changed"]).any():
            decision_steps.add(t)
        next_states, next_observations = [], []
        rewards = np.zeros(spec.train_lanes, dtype=np.float64)
        next_dones = np.zeros(spec.train_lanes, dtype=bool)
        for lane, env in enumerate(envs):
            native = env.env.env
            before = np.asarray(native.uav_positions).copy()
            obs, reward, term, trunc, info = env.step(executed[lane])
            after = np.asarray(native.uav_positions).copy()
            done = bool(term or trunc)
            rewards[lane] = reward
            next_dones[lane] = done
            returns[lane] += reward
            summary["counts"]["training_team_steps"] += 1
            summary["counts"]["training_episodes"] += int(done)
            parts = native_components(info, reward, spec.train_n)
            for name in COMPONENTS:
                component_sums[name][lane] += parts[name]
            _observe_motion(
                telemetry, native, before, raw_actions[lane], executed[lane], after,
                rollout=rollout, t=t, lane=lane, reward=reward, components=parts,
            )
            next_states.append(info["next_state"])
            next_observations.append(obs)
            if training_step_hook is not None:
                training_step_hook({"rollout": rollout, "t": t, "lane": lane,
                                    "summary": summary, "telemetry": telemetry})
        next_states = np.stack(next_states)
        next_observations = np.stack(next_observations)
        agent.store_transition_batch(
            states=states, next_states=next_states.copy(), observations=observations,
            next_observations=next_observations.copy(), actions=raw_actions, rewards=rewards,
            dones=next_dones, infos_batch=None, rollout_step_idx=t, step_data=data,
        )
        summary["counts"]["stored_team_steps"] += spec.train_lanes
        if not np.array_equal(agent.rollout_buffer.actions[t], raw_actions):
            raise ValueError("B03 buffer did not retain raw sampled actions")
        if not np.array_equal(agent.rollout_buffer.log_probs[t], logprob_before):
            raise ValueError("B03 buffer did not retain original old log-probabilities")
        witness = telemetry["first_overrange_witness"]
        if witness is not None and witness["step_index_zero_based"] == t:
            lane = int(witness["lane"])
            witness.update(
                transition_indexing=(
                    "action[t] and old_logprob[t] map state/position[t] to "
                    "state/position[t+1]; indices are zero-based"
                ),
                old_logprob=logprob_before[lane].tolist(),
                stored_raw_action=agent.rollout_buffer.actions[t, lane].tolist(),
                stored_old_logprob=agent.rollout_buffer.log_probs[t, lane].tolist(),
                stored_action_exact=bool(np.array_equal(
                    agent.rollout_buffer.actions[t, lane], raw_before[lane]
                )),
                stored_old_logprob_exact=bool(np.array_equal(
                    agent.rollout_buffer.log_probs[t, lane], logprob_before[lane]
                )),
            )
        for lane, env in enumerate(envs):
            if next_dones[lane]:
                obs, info = env.reset()
                next_states[lane], next_observations[lane] = info["state"], obs
                agent.reset_env_state(lane)
                steps[lane] = 0
                summary["counts"]["terminal_resets"] += 1
            else:
                steps[lane] += 1
        states, observations, dones = next_states, next_observations, next_dones
        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
            raise ValueError("unexpected B03 training terminal boundary")
    if not dones.all():
        raise ValueError("B03 training rollout missed full episodes")
    telemetry["decision_step_indices_zero_based"] = sorted(decision_steps)
    telemetry["native_component_means_per_world"] = {
        name: (values / spec.horizon).tolist() for name, values in component_sums.items()
    }
    if not all((telemetry["diagnostic_rng_unchanged"], telemetry["policy_output_unchanged"],
                telemetry["old_logprob_unchanged"])):
        raise ValueError("B03 mapping/diagnostics mutated policy data or consumed RNG")
    if cell.law == "clip" and (telemetry["executed_min"] < -1.0 or telemetry["executed_max"] > 1.0):
        raise ValueError("B03 clipped training law exceeded declared action bounds")
    finished = _finish_motion(telemetry, spec.train_n)
    summary["_active_training_rollout"] = {
        "rollout": rollout,
        "phase": "collected",
        "action_motion_telemetry": finished,
        "native_component_sums": jsonable(component_sums),
        "scalar_returns": returns.tolist(),
    }
    return states, observations, steps, dones, finished, returns


def run_fit(
    out: Path, cell: TrainingCell, launch_sha: str, admission: dict[str, Any],
    expected_initial_digest: str | None, spec: FitSpec = DEFAULT_SPEC,
    *, command_start: float | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    out = Path(out)
    if out.name != cell.tag:
        raise ValueError(f"B03 output basename must be fixed tag {cell.tag}")
    if (out / "summary.json").exists():
        raise ValueError("existing B03 scientific summary; reconcile original attempt")
    if cell.initial_digest_source and not expected_initial_digest:
        raise ValueError("paired second B03 cell requires the first cell's initial digest")
    if not cell.initial_digest_source and expected_initial_digest is not None:
        raise ValueError("first B03 package cell must not accept an expected initial digest")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if command_start is None:
        command_start = started
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
        "cell": jsonable(vars(cell)), "arm": cell.arm, "training_action_law": cell.law,
        "seed": cell.seed, "tag": cell.tag, "launch_sha": launch_sha, "admission": admission,
        "status": "initializing", "fit_started": False, "failure": None,
        "spec": jsonable(vars(spec)), "panels": [], "checkpoints": [], "rollouts": [],
        "expected_initial_parameter_normalizer_digest": expected_initial_digest,
        "expected_initial_digest_source": cell.initial_digest_source,
        "counts": {"training_team_steps": 0, "stored_team_steps": 0,
                   "training_episodes": 0, "terminal_resets": 0, "updates": 0,
                   "evaluation_team_steps": 0, "evaluation_episodes": 0},
        "evaluation_action_law": "clip",
        "transition_indexing": (
            "action[t] and old_logprob[t] map state/position[t] to "
            "state/position[t+1]; indices are zero-based"
        ),
        "evaluation_seed_base": EVALUATION_SEED_BASE,
        "reward_units": {"training": "native R / train_N=6",
                         "J": "test_N * scalar_return / horizon"},
        "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                    "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
                    "thread_environment": {name: os.environ.get(name) for name in
                        ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")}},
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_fit_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    publish("admitted")
    envs, agent, hooks, calls = [], None, [], {}
    try:
        torch.set_num_threads(spec.torch_threads)
        seed_rng(cell.seed)
        envs = make_envs(spec.train_lanes, cell.seed, spec.train_n, spec.horizon)
        config = make_config(cell.arm, envs, cell.seed, spec)
        _assert_config_contract(config, cell)
        summary["config"] = config_dict(config)
        summary["action_distribution"] = {
            "kind": str(getattr(config, "continuous_action_distribution", "gaussian")),
            "lambda_l": float(config.lambda_l), "mapping_is_environment_only": True,
        }
        write_json(out / "config.json", {"launch_sha": launch_sha, "cell": vars(cell),
                                         "spec": vars(spec), "config": summary["config"]})
        agent = build_agent(config, str(out / "learner_logs"))
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        calls, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = calls
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        initial_parameters = capture_parameters(agent)
        observed_initial = digest_agent(agent)
        summary["observed_initial_parameter_normalizer_digest"] = observed_initial
        summary["initial_digest_matches_expected"] = (
            expected_initial_digest is None or observed_initial == expected_initial_digest
        )
        if not summary["initial_digest_matches_expected"]:
            raise ValueError("B03 paired initial parameter/normalizer digest mismatch")
        summary["initial_raw_sigma"] = raw_sigma(agent)
        agent.train(True)
        if 0 in spec.panels:
            summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
            evaluate_panel(agent, cell, 0, out, summary, spec, publish)
        states, observations = reset_all(envs)
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"], summary["fit_started"] = "training", True
        publish("training starts")
        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            optimizer_before = calls.copy()
            sigma_before = raw_sigma(agent)
            states, observations, steps, dones, motion, returns = collect_rollout(
                agent, envs, states, observations, steps, dones, cell, rollout, summary, spec,
                training_step_hook=training_step_hook,
            )
            publish(f"rollout {rollout} collected")
            summary["_active_training_rollout"].update(
                phase="updating",
                raw_sigma_before_update=sigma_before,
                optimizer_calls_before_update=optimizer_before,
            )
            losses = agent.update(
                last_values=np.zeros((spec.train_lanes, spec.train_n), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon, last_state=states.copy(),
                last_observations=observations.copy(),
            )
            summary["counts"]["updates"] += 1
            finite(losses, "B03 training losses")
            if float(agent.config.lambda_l) != .05:
                raise ValueError("B03 update changed the raw Gaussian entropy coefficient")
            motion_parameters = parameter_motion(agent, initial_parameters)
            row = {
                "rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": {name: calls[name] - optimizer_before[name] for name in calls},
                "optimizer_total": calls.copy(), "parameter_motion": motion_parameters,
                "raw_sigma_before_update": sigma_before, "raw_sigma_after_update": raw_sigma(agent),
                "action_motion_telemetry": motion,
                "rollout_wall_seconds": time.perf_counter() - rollout_start,
            }
            with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            summary["rollouts"].append(row)
            summary["parameter_motion"] = motion_parameters
            agent.clear_buffers()
            summary.pop("_active_training_rollout", None)
            publish(f"rollout {rollout} updated")
            if rollout in spec.panels:
                summary["checkpoints"].append(save_checkpoint(agent, out, rollout, config, launch_sha))
                evaluate_panel(agent, cell, rollout, out, summary, spec, publish)
        expected_training = spec.rollouts * spec.train_lanes * spec.horizon
        expected_eval = len(spec.panels) * len(spec.test_ns) * spec.eval_lanes * spec.horizon
        if summary["counts"]["training_team_steps"] != expected_training:
            raise ValueError("B03 training exposure incomplete")
        if summary["counts"]["stored_team_steps"] != expected_training:
            raise ValueError("B03 stored exposure incomplete")
        if summary["counts"]["evaluation_team_steps"] != expected_eval:
            raise ValueError("B03 evaluation exposure incomplete")
        required = ("discoverer_actor", "discoverer_critic") + (
            ("coordinator", "team_discriminator", "individual_discriminator")
            if cell.arm == "H6" else ()
        )
        for name in required:
            if calls[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"required B03 learner module did not update: {name}")
        if cell.arm == "SET" and any(
            calls[name] for name in ("coordinator", "team_discriminator", "individual_discriminator")
        ):
            raise ValueError("SET unexpectedly updated disabled skill modules")
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_raw_sigma"] = raw_sigma(agent)
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                telemetry = active.pop("_telemetry")
                component_sums = active.pop("component_sums")
                active["action_motion_telemetry_partial"] = _finish_motion(
                    telemetry, spec.train_n
                )
                active["native_component_sums_partial"] = jsonable(component_sums)
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = calls.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: count - int(before.get(name, 0)) for name, count in calls.items()
            }
            if agent is not None:
                active["raw_sigma_observed_after_failure"] = raw_sigma(agent)
            summary["incomplete_rollout"] = jsonable(active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "command_wall_seconds": time.perf_counter() - command_start,
            "run_fit_wall_seconds": time.perf_counter() - started,
            "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss,
            "rss_scope": "scientific process Linux RUSAGE_SELF",
            "resources_unmeasured": ["peak_scratch_bytes"],
        }
        publish(summary["status"])
    return return_code
