"""Run one fixed fresh B14 H6 or ordinary-SET fit with symmetric stage evaluation."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import pickle
import resource
import sys
import time
import traceback
from types import MethodType
from typing import Any, Callable, Mapping

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC, DIRECTION, FitSpec, config_dict, make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent, strict_sync
from experiments.candidates.agent_count_generalization.ordinary_control_b13 import runner as b13
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS, OPTIMIZERS, capture_parameters, digest_agent, finite, jsonable,
    model_modules, native_components, optimizer_counts, parameter_motion, preserve_rng,
    save_checkpoint, seed_rng, write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11


OBJECT_ID = "s1_fresh_learning_b14"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SEED = 974201
TRAINING_ENV_SEED_BASE = 1_974_200
EVALUATION_ORDER = (8, 6)
WORLD_SEED_BASES = {8: 1_645_800, 6: 1_645_600}
FINAL_ROLLOUT = 45
ATOL = 1e-7
RTOL = 1e-6


@dataclass(frozen=True)
class TrainingCell:
    key: str
    arm: str
    tag: str
    seed: int = SEED
    train_n: int = 6
    law: str = "clip"
    lambda_l: float = .05


CELLS = (
    TrainingCell("h6", "H6", "s1_fresh_learning_b14_h6_s974201"),
    TrainingCell("set", "SET", "s1_fresh_learning_b14_set_s974201"),
)
CELL_BY_KEY = {cell.key: cell for cell in CELLS}
B14_BASE_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=EVALUATION_ORDER, eval_lanes=32,
    panels=(0, FINAL_ROLLOUT),
)


def spec_for(cell: TrainingCell, base: FitSpec = B14_BASE_SPEC) -> FitSpec:
    if cell not in CELLS:
        raise ValueError("B14 accepts only its fixed H6/SET cells")
    return replace(
        base, train_n=6, test_ns=EVALUATION_ORDER, panels=(0, base.rollouts),
    )


def file_sha256(path: Path) -> str:
    return b11.file_sha256(Path(path))


def _config_record(config: Any) -> dict[str, Any]:
    return {
        **config_dict(config),
        "lambda_l_initial": float(config.lambda_l_initial),
        "lambda_l_final": float(config.lambda_l_final),
        "use_entropy_annealing": bool(config.use_entropy_annealing),
        "use_entropy_targets": bool(config.use_entropy_targets),
    }


def _assert_config(config: Any, cell: TrainingCell, expected_n: int) -> None:
    if cell.arm not in {"H6", "SET"} or str(config.count_arm) != cell.arm:
        raise ValueError("B14 cell/config package mismatch")
    if int(config.n_agents) != expected_n or int(config.n_uavs) != expected_n:
        raise ValueError(f"B14 config has wrong physical roster for N={expected_n}")
    if int(config.k) != 10 or bool(config.use_central_snapshot_in_flat_actor) != (cell.arm == "SET"):
        raise ValueError("B14 package information route or k10 clock changed")
    if str(getattr(config, "continuous_action_distribution", "gaussian")) != "gaussian":
        raise ValueError("B14 requires the native Gaussian action distribution")
    if any(float(value) != .05 for value in (
        config.lambda_l, config.lambda_l_initial, config.lambda_l_final,
    )) or bool(config.use_entropy_annealing) or bool(config.use_entropy_targets):
        raise ValueError("B14 fixed .05 entropy treatment changed")


def make_b14_config(
    cell: TrainingCell, envs: list[Any], spec: FitSpec, *, expected_n: int | None = None,
) -> Any:
    config = make_config(cell.arm, envs, cell.seed, spec)
    config.lambda_l = config.lambda_l_initial = config.lambda_l_final = cell.lambda_l
    config.use_entropy_annealing = False
    config.use_entropy_targets = False
    config.validate_config()
    _assert_config(config, cell, spec.train_n if expected_n is None else expected_n)
    return config


def _world_seed(n: int) -> int:
    try:
        return WORLD_SEED_BASES[int(n)]
    except KeyError as exc:
        raise ValueError(f"B14 has no evaluation panel at N={n}") from exc


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        Path(__file__).resolve().with_name("__init__.py"),
        REPOSITORY_ROOT / "scripts/run_agent_count_fresh_learning_b14.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/training_condition_b11/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/ordinary_control_b13/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
    )


def _source_hashes() -> dict[str, str]:
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path) for path in _source_paths()}


def _hash_tree(value: Any, digest: Any) -> None:
    if torch.is_tensor(value):
        tensor = value.detach().cpu().contiguous()
        digest.update(b"tensor" + str(tensor.dtype).encode() + repr(tuple(tensor.shape)).encode())
        digest.update(tensor.numpy().tobytes())
    elif isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        digest.update(b"array" + str(array.dtype).encode() + repr(array.shape).encode())
        digest.update(array.tobytes())
    elif isinstance(value, Mapping):
        digest.update(b"mapping")
        for key in sorted(value, key=repr):
            _hash_tree(key, digest)
            _hash_tree(value[key], digest)
    elif isinstance(value, (tuple, list)):
        digest.update(type(value).__name__.encode())
        for item in value:
            _hash_tree(item, digest)
    else:
        digest.update(type(value).__name__.encode() + repr(value).encode())


def _optimizer_state_digest(agent: Any) -> str:
    digest = hashlib.sha256()
    for name in OPTIMIZERS:
        digest.update(name.encode())
        optimizer = getattr(agent, name + "_optimizer", None)
        _hash_tree(None if optimizer is None else optimizer.state_dict(), digest)
    return digest.hexdigest()


def _sampler_digest(agent: Any) -> str:
    return hashlib.sha256(
        pickle.dumps(agent.rollout_buffer.get_sampler_rng_state(), protocol=5)
    ).hexdigest()


def _buffer_content_digest(agent: Any) -> str:
    buffer = agent.rollout_buffer
    digest = hashlib.sha256()
    for name, value in sorted(vars(buffer).items()):
        if isinstance(value, np.ndarray):
            digest.update(name.encode())
            _hash_tree(value, digest)
    return digest.hexdigest()


def _environment_digest(envs: list[Any]) -> str:
    payload = []
    for env in envs:
        native = env.env.env
        payload.append({
            "seed": int(native.seed_val), "current_step": int(native.current_step),
            "rng": native.np_random.get_state(),
            "uav_positions": np.asarray(native.uav_positions).copy(),
            "user_positions": np.asarray(native.user_positions).copy(),
            "connections": np.asarray(native.connections).copy(),
            "sinr_matrix": np.asarray(native.sinr_matrix).copy(),
        })
    return hashlib.sha256(pickle.dumps(payload, protocol=5)).hexdigest()


def _isolation_snapshot(agent: Any, envs: list[Any]) -> dict[str, Any]:
    return {
        "parameter_normalizer_digest": digest_agent(agent),
        "runtime_digest": b03.runtime_state_digest(agent),
        "global_rng_digest": b03._rng_digest(),
        "sampler_rng_digest": _sampler_digest(agent),
        "optimizer_state_digest": _optimizer_state_digest(agent),
        "training_mode": bool(agent.training),
        "buffer_content_digest": _buffer_content_digest(agent),
        "buffer_env_lengths": np.asarray(agent.rollout_buffer.env_lengths).tolist(),
        "buffer_last_t_per_env": np.asarray(agent.rollout_buffer.last_t_per_env).tolist(),
        "training_environment_digest": _environment_digest(envs),
    }


class _ResetSceneRecorder:
    def __init__(self, env: Any, lane: int):
        self._env, self.lane, self.records = env, int(lane), []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._env, name)

    def reset(self, *args: Any, **kwargs: Any) -> Any:
        observation, info = self._env.reset(*args, **kwargs)
        native = self._env.env.env
        rng_digest = hashlib.sha256(
            pickle.dumps(native.np_random.get_state(), protocol=5)
        ).hexdigest()
        self.records.append({
            "state": np.asarray(info["state"]).copy(),
            "observation": np.asarray(observation).copy(),
            "uav_positions": np.asarray(native.uav_positions).copy(),
            "user_positions": np.asarray(native.user_positions).copy(),
            "rng_sha256": rng_digest,
        })
        return observation, info

    def close(self) -> None:
        return self._env.close()


def _write_training_resets(path: Path, envs: list[_ResetSceneRecorder]) -> dict[str, Any]:
    counts = [len(env.records) for env in envs]
    if not counts or len(set(counts)) != 1 or counts[0] == 0:
        raise ValueError(f"B14 training reset evidence is incomplete across lanes: {counts}")
    names = {
        "states": "state", "observations": "observation",
        "uav_positions": "uav_positions", "user_positions": "user_positions",
    }
    arrays = {
        output_name: np.stack([
            np.stack([env.records[index][name] for env in envs])
            for index in range(counts[0])
        ])
        for output_name, name in names.items()
    }
    arrays["rng_sha256"] = np.asarray([
        [env.records[index]["rng_sha256"] for env in envs]
        for index in range(counts[0])
    ], dtype="S64")
    arrays["lane_world_seeds"] = np.asarray(
        [TRAINING_ENV_SEED_BASE + lane for lane in range(len(envs))], dtype=np.int64,
    )
    identity = b11._write_trace(path, arrays)
    identity["reset_calls_per_lane"] = counts[0]
    identity["semantics"] = "actual post-reset training scenes in reset-call order"
    return identity


def _initialization(
    cell: TrainingCell, config: Any, out: Path,
) -> tuple[Any, dict[str, Any]]:
    if cell.arm == "SET":
        agent, evidence = b11.construct_common_initialized_agent(
            config, out / "initialization_logs",
        )
        evidence = {"method": "canonical_n6_sync_to_fresh_true_n_target", **evidence}
        return agent, evidence
    agent = build_agent(config, str(out / "initialization_logs" / "native_h6"))
    parameter_ids: set[int] = set()
    ownership = b11._optimizer_ownership(agent, parameter_ids)
    evidence = {
        "method": "native_h6_construction_no_cross_architecture_copy",
        "canonical_n": None, "target_n": int(config.n_agents),
        "post_initialization_rng_digest": b03._rng_digest(),
        "parameter_normalizer_digest": digest_agent(agent),
        "tensor_manifest": b11._tensor_manifest(agent),
        "normalizers": b11._normalizer_manifest(agent),
        "target_optimizer_ownership": ownership,
        "target_initial_buffer": b11._buffer_initial_record(agent),
        "target_fresh_runtime_digest": b03.runtime_state_digest(agent),
        "actual_config": _config_record(config),
    }
    return agent, evidence


def _new_panel_trace(spec: FitSpec, n: int) -> dict[str, np.ndarray]:
    trace = b11._new_trace(spec, n)
    trace.update({
        "states": np.zeros((spec.horizon, spec.eval_lanes, 133), dtype=np.float32),
        "observations": np.zeros((spec.horizon, spec.eval_lanes, n, 104), dtype=np.float32),
        "next_states": np.zeros((spec.horizon, spec.eval_lanes, 133), dtype=np.float32),
        "next_observations": np.zeros(
            (spec.horizon, spec.eval_lanes, n, 104), dtype=np.float32,
        ),
        "raw_actions": np.zeros((spec.horizon, spec.eval_lanes, n, 3), dtype=np.float32),
        "executed_actions": np.zeros((spec.horizon, spec.eval_lanes, n, 3), dtype=np.float32),
    })
    return trace


def _evaluate_stage(
    learner: Any, training_envs: list[Any], cell: TrainingCell, stage: int,
    out: Path, summary: dict[str, Any], spec: FitSpec, publish: Callable[[str], None],
) -> None:
    isolation_before = _isolation_snapshot(learner, training_envs)
    with preserve_rng():
        for n in EVALUATION_ORDER:
            world_seed = _world_seed(n)
            seed_rng(world_seed + 51)
            envs = make_envs(spec.eval_lanes, world_seed, n, spec.horizon)
            target, inference, hooks = None, None, []
            storage_calls = 0
            original_store = None
            row = {
                "status": "running", "arm": cell.arm, "cell_key": cell.key,
                "policy_stage": stage, "after_rollout": stage,
                "prior_training_team_steps": stage * spec.train_lanes * spec.horizon,
                "test_n": n,
                "world_seeds": list(range(world_seed, world_seed + spec.eval_lanes)),
                "runtime_seed": world_seed + 51, "execution_law": "clip",
                "steps": 0, "episodes": 0, "resets": 0, "policy_step_calls": 0,
            }
            summary["panels"].append(row)
            publish(f"stage {stage} evaluation N={n} starting")
            try:
                b11._assert_native_envs(envs, n)
                config = make_b14_config(cell, envs, replace(spec, train_n=n), expected_n=n)
                target = build_agent(config, str(out / "evaluation_logs" / f"stage{stage:02d}_n{n}"))
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                before = digest_agent(target)
                if before != digest_agent(learner):
                    raise ValueError("B14 evaluation target did not strictly load learner")
                normals_before = b11._normalizer_manifest(target)
                runtime_before = b03.runtime_state_digest(target)
                original_store = target.store_transition_batch

                def reject_store(_target: Any, *args: Any, **kwargs: Any) -> None:
                    nonlocal storage_calls
                    storage_calls += 1
                    summary["counts"]["evaluation_storage_calls"] += 1
                    raise ValueError("B14 evaluation attempted training storage")

                target.store_transition_batch = MethodType(reject_store, target)
                inference = b13._InferenceCounter(target, cell.arm, n)
                pairs = [env.reset() for env in envs]
                row["resets"] = len(pairs)
                summary["counts"]["evaluation_resets"] += len(pairs)
                states = np.stack([info["state"] for observation, info in pairs])
                observations = np.stack([observation for observation, info in pairs])
                steps = np.zeros(spec.eval_lanes, dtype=np.int64)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                sums = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
                trace = _new_panel_trace(spec, n)
                trace["initial_states"] = states.copy()
                trace["initial_observations"] = observations.copy()
                action_min, action_max = float("inf"), float("-inf")
                with torch.no_grad():
                    for t in range(spec.horizon):
                        trace["states"][t] = states
                        trace["observations"][t] = observations
                        raw_actions, _, data = target.step(
                            states, observations, steps, dones, deterministic=True,
                            return_step_data=True, build_infos=False,
                        )
                        row["policy_step_calls"] += 1
                        summary["counts"]["evaluation_policy_step_calls"] += 1
                        finite((raw_actions, data), "B14 deterministic evaluation output")
                        inference.observe_choices(data)
                        raw_before = raw_actions.copy()
                        executed = b03.map_training_actions(raw_actions, "clip")
                        if not np.array_equal(raw_actions, raw_before):
                            raise ValueError("B14 evaluation clip changed raw policy output")
                        trace["raw_actions"][t] = raw_actions
                        trace["executed_actions"][t] = executed
                        action_min = min(action_min, float(executed.min()))
                        action_max = max(action_max, float(executed.max()))
                        next_states, next_observations = [], []
                        for lane, env in enumerate(envs):
                            observation, reward, terminated, truncated, info = env.step(executed[lane])
                            done = bool(terminated or truncated)
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_uav_steps"] += n
                            summary["counts"]["evaluation_episodes"] += int(done)
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                sums[name][lane] += parts[name]
                            b11._observe_post_transition(trace, t, lane, env, reward, parts, n)
                            next_states.append(info["next_state"])
                            next_observations.append(observation)
                            dones[lane] = done
                        states = np.stack(next_states)
                        observations = np.stack(next_observations)
                        trace["next_states"][t] = states
                        trace["next_observations"][t] = observations
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected B14 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B14 evaluation missed fixed terminal boundary")
                means = {name: value / spec.horizon for name, value in sums.items()}
                j = n * returns / spec.horizon
                native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means[
                    "energy_penalty"
                ]
                if not np.allclose(j, means["total_reward"], atol=ATOL, rtol=RTOL) \
                        or not np.allclose(j, native_j, atol=ATOL, rtol=RTOL):
                    raise ValueError("B14 native J/component identity failed")
                service = trace["served_user_counts"].mean(axis=0)
                eligibility = trace["eligible_user_counts"].mean(axis=0)
                unserved = trace["eligible_unserved_user_counts"].mean(axis=0)
                if not np.allclose(service, 50 * means["coverage_reward"], atol=ATOL, rtol=RTOL) \
                        or not np.allclose(unserved, eligibility - service, atol=ATOL, rtol=RTOL):
                    raise ValueError("B14 native C/S or E/S/U identity failed")
                inference_counts = inference.finish(spec)
                model_after = digest_agent(target)
                if any(calls.values()) or storage_calls or model_after != before:
                    raise ValueError("B14 evaluation optimized, stored, or changed target parameters")
                if b11._normalizer_manifest(target) != normals_before:
                    raise ValueError("B14 evaluation changed target normalizers")
                if np.any(target.rollout_buffer.env_lengths):
                    raise ValueError("B14 evaluation populated training storage")
                trace_identity = b11._write_trace(out / f"trace_stage{stage:02d}_n{n}.npz", trace)
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                    component_means=jsonable(means),
                    service_arrays={
                        "E_eligible_users_per_step": eligibility.tolist(),
                        "S_served_users_per_step": service.tolist(),
                        "U_eligible_unserved_users_per_step": unserved.tolist(),
                    },
                    optimizer_calls=calls.copy(), training_storage_calls=storage_calls,
                    rollout_storage_env_lengths=target.rollout_buffer.env_lengths.tolist(),
                    frozen_weights_and_normalizers=True,
                    parameter_normalizer_digest_before=before,
                    parameter_normalizer_digest_after=model_after,
                    normalizers_before=normals_before,
                    normalizers_after=b11._normalizer_manifest(target),
                    runtime_digest_before=runtime_before,
                    runtime_digest_after=b03.runtime_state_digest(target),
                    runtime_evolved=runtime_before != b03.runtime_state_digest(target),
                    executed_action_bounds={"minimum": action_min, "maximum": action_max},
                    inference_counts=inference_counts, trace=trace_identity,
                    config=_config_record(config), post_transition_semantics=True,
                    actual_sinr_threshold=float(envs[0].env.env.min_sinr),
                    max_connections_per_uav=int(envs[0].env.env.max_connections),
                    height_range=[float(value) for value in envs[0].env.env.height_range],
                    n_users=int(envs[0].env.env.n_users),
                )
                summary["counts"]["panels"] += 1
                summary["counts"]["evaluation_optimizer_calls"] += sum(calls.values())
                write_json(out / f"panel_stage{stage:02d}_n{n}.json", row)
                publish(f"stage {stage} evaluation N={n} complete")
            except Exception as exc:
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                write_json(out / f"panel_stage{stage:02d}_n{n}.json", row)
                raise
            finally:
                if inference is not None:
                    inference.close()
                if target is not None and original_store is not None:
                    target.store_transition_batch = original_store
                for hook in hooks:
                    hook.remove()
                for env in envs:
                    env.close()
                del target
    isolation_after = _isolation_snapshot(learner, training_envs)
    preservation = {
        "before": isolation_before, "after": isolation_after,
        **{name + "_preserved": isolation_before[name] == isolation_after[name]
           for name in isolation_before},
    }
    summary["stage_isolation"][str(stage)] = preservation
    if not all(value for key, value in preservation.items() if key.endswith("_preserved")):
        raise ValueError("B14 evaluation changed learner, optimizer, sampler, RNG, or training environments")


class _CountingAgent:
    def __init__(
        self, agent: Any, counts: dict[str, int], summary: dict[str, Any],
        inference: b13._InferenceCounter,
    ):
        self._agent, self._counts, self._summary = agent, counts, summary
        self._inference = inference
        self.optimizer_before: dict[str, int] = {}

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)

    def step(self, *args: Any, **kwargs: Any) -> Any:
        active = self._summary.get("_active_training_rollout")
        if active is not None:
            active.setdefault("optimizer_calls_before_update", self.optimizer_before.copy())
        result = self._agent.step(*args, **kwargs)
        self._inference.observe_choices(result[2])
        self._counts["training_policy_step_calls"] += 1
        return result


def _expected_counts(spec: FitSpec, *, initial_evaluation: bool = True) -> dict[str, int]:
    stages = 2 if initial_evaluation else 1
    panels = stages * len(EVALUATION_ORDER)
    training = spec.rollouts * spec.train_lanes * spec.horizon
    evaluation = panels * spec.eval_lanes * spec.horizon
    return {
        "fits": 1, "training_team_steps": training, "stored_team_steps": training,
        "training_uav_steps": training * spec.train_n,
        "training_episodes": spec.rollouts * spec.train_lanes,
        "terminal_resets": spec.rollouts * spec.train_lanes, "updates": spec.rollouts,
        "training_policy_step_calls": spec.rollouts * spec.horizon,
        "panels": panels, "evaluation_team_steps": evaluation,
        "evaluation_uav_steps": stages * spec.eval_lanes * spec.horizon * sum(EVALUATION_ORDER),
        "evaluation_episodes": panels * spec.eval_lanes,
        "evaluation_resets": panels * spec.eval_lanes,
        "evaluation_policy_step_calls": panels * spec.horizon,
        "evaluation_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }


def _expected_optimizer_calls(cell: TrainingCell) -> dict[str, int]:
    if cell.arm == "H6":
        return {
            "coordinator": 675, "discoverer_actor": 101_250,
            "discoverer_critic": 101_250, "team_discriminator": 675,
            "individual_discriminator": 2_700,
        }
    return {
        "coordinator": 0, "discoverer_actor": 101_250,
        "discoverer_critic": 101_250, "team_discriminator": 0,
        "individual_discriminator": 0,
    }


def _new_inference_totals(agent: Any) -> dict[str, Any]:
    return {
        "coordinator_batched_calls": 0, "coordinator_rows": 0,
        "coordinator_batch_sizes": [], "decoder_team_calls": 0,
        "decoder_team_rows": 0, "decoder_individual_calls": 0,
        "decoder_individual_rows": 0, "team_selections": 0,
        "individual_selections": 0,
        "team_choice_counts": [0] * int(agent.config.n_Z),
        "individual_choice_counts": [0] * int(agent.config.n_z),
        "set_snapshot_refresh_steps": 0, "set_snapshot_lane_refreshes": 0,
    }


def _add_inference_counts(total: dict[str, Any], observed: Mapping[str, Any]) -> None:
    for key in total:
        if key == "coordinator_batch_sizes":
            total[key].extend(observed[key])
        elif key in {"team_choice_counts", "individual_choice_counts"}:
            total[key] = [left + int(right) for left, right in zip(total[key], observed[key])]
        else:
            total[key] += int(observed[key])


def _finish_training_inference(
    observed: Mapping[str, Any], cell: TrainingCell, spec: FitSpec,
) -> dict[str, Any]:
    result = dict(observed)
    decisions = spec.rollouts * (spec.horizon // 10)
    rows = decisions * spec.train_lanes
    expected = {
        "coordinator_batched_calls": decisions, "coordinator_rows": rows,
        "decoder_team_calls": decisions, "decoder_team_rows": rows,
        "decoder_individual_calls": decisions * spec.train_n,
        "decoder_individual_rows": rows * spec.train_n,
        "team_selections": rows, "individual_selections": rows * spec.train_n,
    }
    if any(result[key] != value for key, value in expected.items()) \
            or result["coordinator_batch_sizes"] != [spec.train_lanes] * decisions:
        raise ValueError(f"B14 training inference exposure changed: {result} != {expected}")
    if sum(result["team_choice_counts"]) != rows \
            or sum(result["individual_choice_counts"]) != rows * spec.train_n:
        raise ValueError("B14 training inference choice counts are incomplete")
    if cell.arm == "SET":
        if result["set_snapshot_refresh_steps"] != decisions \
                or result["set_snapshot_lane_refreshes"] != rows:
            raise ValueError("B14 SET training snapshot refresh exposure changed")
    else:
        result["set_snapshot_refresh_steps"] = None
        result["set_snapshot_lane_refreshes"] = None
    return result


def _aggregate_evaluation_inference(panels: list[dict[str, Any]], cell: TrainingCell) -> dict[str, Any]:
    keys = (
        "coordinator_batched_calls", "coordinator_rows", "decoder_team_calls",
        "decoder_team_rows", "decoder_individual_calls", "decoder_individual_rows",
        "team_selections", "individual_selections",
    )
    result = {key: sum(int(row["inference_counts"][key]) for row in panels) for key in keys}
    result["set_snapshot_refresh_steps"] = (
        sum(int(row["inference_counts"]["set_snapshot_refresh_steps"]) for row in panels)
        if cell.arm == "SET" else None
    )
    result["set_snapshot_lane_refreshes"] = (
        sum(int(row["inference_counts"]["set_snapshot_lane_refreshes"]) for row in panels)
        if cell.arm == "SET" else None
    )
    return result


def _stats(values: np.ndarray, worlds: list[int]) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    minimum, maximum = int(np.argmin(values)), int(np.argmax(values))
    return {
        "per_world": values.tolist(), "mean": float(values.mean()),
        "median": float(np.median(values)),
        "signs": {"positive": int((values > 0).sum()), "zero": int((values == 0).sum()),
                  "negative": int((values < 0).sum())},
        "minimum": {"value": float(values[minimum]), "world_seed": worlds[minimum]},
        "maximum": {"value": float(values[maximum]), "world_seed": worlds[maximum]},
    }


def _quantities(row: dict[str, Any]) -> dict[str, np.ndarray]:
    return {
        "J": np.asarray(row["J"]),
        "C": np.asarray(row["component_means"]["coverage_reward"]),
        "Q": np.asarray(row["component_means"]["quality_reward"]),
        "P": np.asarray(row["component_means"]["energy_penalty"]),
        "E": np.asarray(row["service_arrays"]["E_eligible_users_per_step"]),
        "S": np.asarray(row["service_arrays"]["S_served_users_per_step"]),
        "U": np.asarray(row["service_arrays"]["U_eligible_unserved_users_per_step"]),
    }


def _stage_readings(panels: list[dict[str, Any]], final_stage: int) -> dict[str, Any]:
    joined = {(row["policy_stage"], row["test_n"]): row for row in panels}
    if set(joined) != {(stage, n) for stage in (0, final_stage) for n in EVALUATION_ORDER}:
        raise ValueError("B14 readings require exactly stage0/final45 N8/N6 panels")
    result = {}
    for n in EVALUATION_ORDER:
        initial, final = joined[(0, n)], joined[(final_stage, n)]
        if initial["world_seeds"] != final["world_seeds"]:
            raise ValueError("B14 within-arm stage worlds differ")
        worlds = initial["world_seeds"]
        q0, q45 = _quantities(initial), _quantities(final)
        result[str(n)] = {
            "world_seeds": worlds,
            "stage0": {key: _stats(value, worlds) for key, value in q0.items()},
            "stage45": {key: _stats(value, worlds) for key, value in q45.items()},
            "stage45_minus_stage0": {
                key: _stats(q45[key] - q0[key], worlds) for key in q0
            },
        }
    return {"by_test_n": result, "cross_n_aggregate": None}


def run_fit(
    out: Path, cell: TrainingCell, launch_sha: str, admission: dict[str, Any],
    spec: FitSpec, *, command_start: float | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
    evaluate_initial: bool = True,
) -> int:
    out = Path(out)
    if cell not in CELLS or out.name != cell.tag:
        raise ValueError("B14 accepts only fixed H6/SET cells and matching output tags")
    if spec.train_n != 6 or tuple(spec.test_ns) != EVALUATION_ORDER \
            or tuple(spec.panels) != (0, spec.rollouts):
        raise ValueError("B14 spec must bind N6 training and stage0/final N8 then N6 evaluation")
    if spec == spec_for(cell) and not evaluate_initial:
        raise ValueError("B14 production execution cannot omit initial evaluation")
    if (out / "summary.json").exists():
        raise ValueError("existing B14 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected = _expected_counts(spec, initial_evaluation=evaluate_initial)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
        "cell": jsonable(vars(cell)), "arm": cell.arm, "tag": cell.tag,
        "seed": cell.seed, "launch_sha": launch_sha, "admission": admission,
        "training_action_law": "clip", "status": "initializing", "fit_started": False,
        "failure": None, "spec": jsonable(vars(spec)), "panels": [], "checkpoints": [],
        "rollouts": [], "stage_isolation": {}, "stage_readings": None,
        "initial_evaluation_enabled": bool(evaluate_initial),
        "counts": {key: 0 for key in expected}, "expected_counts": expected,
        "training_world_seeds": list(range(
            TRAINING_ENV_SEED_BASE, TRAINING_ENV_SEED_BASE + spec.train_lanes,
        )),
        "evaluation_order": [
            {"stage": stage, "test_n": n}
            for stage in ((0, spec.rollouts) if evaluate_initial else (spec.rollouts,))
            for n in EVALUATION_ORDER
        ],
        "world_seed_bases": WORLD_SEED_BASES, "source_hashes_before": _source_hashes(),
        "reward_units": {
            "training": "native R / train_N=6", "J": "test_N * scalar_return / horizon",
            "C": "coverage fraction", "S": "served users per step = 50*C",
            "U": "eligible unserved users per step = E-S",
        },
        "runtime": {
            "python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
            "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
        },
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_fit_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    envs: list[_ResetSceneRecorder] = []
    agent, hooks, optimizer_call_counts = None, [], {}
    active_training_counter = None
    reset_identity_written = False
    publish("admitted")
    try:
        torch.set_num_threads(spec.torch_threads)
        envs = [
            _ResetSceneRecorder(env, lane)
            for lane, env in enumerate(make_envs(
                spec.train_lanes, TRAINING_ENV_SEED_BASE, 6, spec.horizon,
            ))
        ]
        b11._assert_native_envs(envs, 6)
        seed_rng(cell.seed)
        config = make_b14_config(cell, envs, spec)
        summary["config"] = _config_record(config)
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "cell": vars(cell), "spec": vars(spec),
            "config": summary["config"], "evaluation_order": summary["evaluation_order"],
            "world_seed_bases": WORLD_SEED_BASES,
        })
        agent, initialization = _initialization(cell, config, out)
        agent.train(True)
        summary["initialization"] = initialization
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        optimizer_call_counts, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = optimizer_call_counts
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        initial_parameters = capture_parameters(agent)
        summary["observed_initial_parameter_normalizer_digest"] = digest_agent(agent)
        summary["initial_raw_sigma"] = b03.raw_sigma(agent)
        summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
        summary["fit_started"] = True
        summary["counts"]["fits"] = 1
        if evaluate_initial:
            _evaluate_stage(agent, envs, cell, 0, out, summary, spec, publish)
        pairs = [env.reset() for env in envs]
        states = np.stack([info["state"] for observation, info in pairs])
        observations = np.stack([observation for observation, info in pairs])
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"] = "training"
        publish("training starts")
        training_inference_totals = _new_inference_totals(agent)
        b03_cell = b03.TrainingCell(1, cell.key, cell.arm, "clip", cell.seed, cell.tag)
        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            optimizer_before = optimizer_call_counts.copy()
            active_training_counter = b13._InferenceCounter(agent, cell.arm, 6)
            counted_agent = _CountingAgent(
                agent, summary["counts"], summary, active_training_counter,
            )
            counted_agent.optimizer_before = optimizer_before
            sigma_before = b03.raw_sigma(agent)
            try:
                states, observations, steps, dones, motion, returns = b03.collect_rollout(
                    counted_agent, envs, states, observations, steps, dones, b03_cell, rollout,
                    summary, spec, training_step_hook=training_step_hook,
                )
            finally:
                active_training_counter.close()
            _add_inference_counts(training_inference_totals, active_training_counter.data)
            active_training_counter = None
            summary["counts"]["training_uav_steps"] = (
                summary["counts"]["training_team_steps"] * 6
            )
            publish(f"rollout {rollout} collected")
            summary["_active_training_rollout"].update(
                phase="updating", raw_sigma_before_update=sigma_before,
                optimizer_calls_before_update=optimizer_before,
            )
            losses = agent.update(
                last_values=np.zeros((spec.train_lanes, 6), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon,
                last_state=states.copy(), last_observations=observations.copy(),
            )
            summary["counts"]["updates"] += 1
            finite(losses, "B14 training losses")
            _assert_config(agent.config, cell, 6)
            motion_parameters = parameter_motion(agent, initial_parameters)
            row = {
                "rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": {
                    name: optimizer_call_counts[name] - optimizer_before[name]
                    for name in optimizer_call_counts
                },
                "optimizer_total": optimizer_call_counts.copy(),
                "parameter_motion": motion_parameters,
                "raw_sigma_before_update": sigma_before,
                "raw_sigma_after_update": b03.raw_sigma(agent),
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
        summary["training_inference_counts"] = _finish_training_inference(
            training_inference_totals, cell, spec,
        )
        summary["training_reset_trace"] = _write_training_resets(
            out / "training_reset_scenes.npz", envs,
        )
        reset_identity_written = True
        summary["checkpoints"].append(save_checkpoint(
            agent, out, spec.rollouts, config, launch_sha,
        ))
        _evaluate_stage(agent, envs, cell, spec.rollouts, out, summary, spec, publish)
        if summary["counts"] != expected:
            raise ValueError(f"B14 exposure mismatch: {summary['counts']} != {expected}")
        if spec == spec_for(cell) and optimizer_call_counts != _expected_optimizer_calls(cell):
            raise ValueError("B14 production optimizer exposure differs from fixed contract")
        required = (
            ("coordinator", "discoverer_actor", "discoverer_critic",
             "team_discriminator", "individual_discriminator")
            if cell.arm == "H6" else ("discoverer_actor", "discoverer_critic")
        )
        for name in required:
            if optimizer_call_counts[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"B14 required learner module did not update: {name}")
        if cell.arm == "SET" and any(optimizer_call_counts[name] for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        )):
            raise ValueError("B14 SET unexpectedly optimized disabled modules")
        if [row["path"] for row in summary["checkpoints"]] != [
            "checkpoint_00.pt", f"checkpoint_{spec.rollouts:02d}.pt",
        ]:
            raise ValueError("B14 requires actual checkpoint00 and final checkpoint only")
        final_panels = [row for row in summary["panels"] if row["status"] == "complete"]
        summary["evaluation_inference_counts"] = _aggregate_evaluation_inference(
            final_panels, cell,
        )
        if evaluate_initial:
            summary["stage_readings"] = _stage_readings(final_panels, spec.rollouts)
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_raw_sigma"] = b03.raw_sigma(agent)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B14 source bytes changed during fit")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        summary["counts"]["training_uav_steps"] = summary["counts"]["training_team_steps"] * 6
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                telemetry = active.pop("_telemetry")
                component_sums = active.pop("component_sums")
                active["action_motion_telemetry_partial"] = b03._finish_motion(telemetry, 6)
                active["native_component_sums_partial"] = jsonable(component_sums)
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = optimizer_call_counts.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: count - int(before.get(name, 0))
                for name, count in optimizer_call_counts.items()
            }
            summary["incomplete_rollout"] = jsonable(active)
        if envs and any(env.records for env in envs) and not reset_identity_written:
            try:
                summary["training_reset_trace"] = _write_training_resets(
                    out / "training_reset_scenes.npz", envs,
                )
            except Exception as trace_exc:
                summary["training_reset_trace_failure"] = f"{type(trace_exc).__name__}: {trace_exc}"
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        if active_training_counter is not None:
            active_training_counter.close()
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
            "resources_unmeasured": ["peak_scratch_bytes", "other_processes"],
        }
        publish(summary["status"])
    return return_code
