"""One fixed B03 D/G recurrence fit using the frozen B01 learner."""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import pickle
import random
import resource
import sys
import time
import traceback

import numpy as np
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b01.learning import ComplementaryAgent
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from scripts import run_fsd_uav_individual_renewal_b01 as support


DIRECTION = "complementary_skill_learning"
OBJECT = "complementary_skill_b03"
EXPECTED_NATIVE_OPTIMIZER_CALLS = {
    "coordinator": 675,
    "discoverer_actor": 101250,
    "discoverer_critic": 101250,
    "team_discriminator": 675,
    "individual_discriminator": 2700,
}
# Generated once from the frozen B01 convention: PCG64 seed 262624105, at each
# k10 renewal draw team labels (32,) before individual labels (32, 6), and hash
# [t], team, individuals through b01.update_digest in that order.
EXPECTED_UNIFORM_LABEL_STREAM_SHA256 = (
    "a45d59f80fca20321df3803745068bb841f30e6c25b6b8c01dd7d0d250a67190"
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
    init_seed: int = 260923921
    head_seed: int = 260923922
    train_rng_seed: int = 260923923
    aux_seed: int = 260923924
    eval_rng_seed: int = 260923905
    train_world_base: int = 2000000
    eval_world_base: int = 1700200
    threads: int = 4
    small_model: bool = False  # technical checks only; the CLI cannot enable it


DEFAULT_SPEC = Spec()
jsonable = b01.jsonable
write_json = b01.write_json
seed_rng = b01.seed_rng
update_digest = b01.update_digest
native_digest = b01.native_digest
frozen_digest = b01.frozen_digest
make_envs = b01.make_envs
make_config = b01.make_config
physical_step = b01.physical_step
low_actions = b01.low_actions
select_skills = b01.select_skills
evaluation_context = b01.evaluation_context


class AuditedComplementaryAgent(ComplementaryAgent):
    """Frozen B01 learner with fail-closed reward-path observations only."""

    def _empty_intrinsic_batch_result(self, *args, **kwargs):
        raise RuntimeError("native intrinsic-reward batch fell back to env-only reward")

    def _team_discriminator_logits(self, *args, **kwargs):
        logits = super()._team_discriminator_logits(*args, **kwargs)
        if not bool(logits.isfinite().all()):
            raise FloatingPointError("nonfinite team discriminator logits")
        return logits

    def _individual_discriminator_logits(self, *args, **kwargs):
        logits = super()._individual_discriminator_logits(*args, **kwargs)
        if not bool(logits.isfinite().all()):
            raise FloatingPointError("nonfinite individual discriminator logits")
        return logits

    def _discriminator_mi_reward(self, *args, **kwargs):
        values = np.asarray(super()._discriminator_mi_reward(*args, **kwargs))
        if not np.isfinite(values).all():
            raise FloatingPointError("nonfinite discriminator-score transformation")
        return values

    def _compute_intrinsic_rewards_batch(self, *args, **kwargs):
        result = super()._compute_intrinsic_rewards_batch(*args, **kwargs)
        keys = ("intrinsic", "env", "team_disc", "ind_disc", "uncertainty")
        arrays = {key: np.asarray(result[key], dtype=np.float32) for key in keys}
        shape = arrays["intrinsic"].shape
        if any(value.shape != shape or not np.isfinite(value).all() for value in arrays.values()):
            raise FloatingPointError("nonfinite or mis-shaped native reward components")
        reconstructed = (
            arrays["env"] + arrays["team_disc"] + arrays["ind_disc"]
            + arrays["uncertainty"]
        )
        if not np.allclose(arrays["intrinsic"], reconstructed, rtol=1e-6, atol=2e-6):
            raise ValueError("native intrinsic reward component identity failed")
        return result


def rng_state_digest() -> str:
    """Digest the actual process RNG states without advancing any generator."""
    digest = hashlib.sha256()
    digest.update(pickle.dumps(random.getstate(), protocol=4))
    numpy_state = np.random.get_state()
    digest.update(str(numpy_state[0]).encode())
    update_digest(digest, numpy_state[1], np.asarray(numpy_state[2:], dtype=np.float64))
    update_digest(digest, torch.get_rng_state().cpu().numpy())
    if torch.cuda.is_available():
        for state in torch.cuda.get_rng_state_all():
            update_digest(digest, state.cpu().numpy())
    return digest.hexdigest()


def _uniform_stream_digest(spec: Spec) -> str:
    """Independent audit helper for tests; it never participates in evaluation."""
    rng = np.random.Generator(np.random.PCG64(spec.eval_rng_seed + spec.eval_world_base))
    digest = hashlib.sha256()
    for t in range(0, spec.horizon, spec.k):
        team = rng.integers(0, 6, size=spec.eval_lanes)
        individual = rng.integers(0, 6, size=(spec.eval_lanes, spec.n_agents))
        update_digest(digest, np.asarray([t], np.int64), team, individual)
    return digest.hexdigest()


def evaluate_panel(agent, spec: Spec, rule: str, *, counter=None):
    """B01 panel with passive audits of physical starts and selected labels."""
    returns = np.zeros(spec.eval_lanes, dtype=np.float64)
    sums = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in b01.COMPONENTS}
    saturation = total_action_coordinates = renewals = 0
    label_digest = hashlib.sha256()
    initial_digest = hashlib.sha256()
    envs = []
    with evaluation_context(agent):
        seed = spec.eval_rng_seed + spec.eval_world_base
        seed_rng(seed)
        label_rng = np.random.Generator(np.random.PCG64(seed))
        try:
            envs = make_envs(spec, spec.eval_lanes, spec.eval_world_base)
            states, observations = b01.native._reset_all(envs)
            update_digest(initial_digest, states, observations)
            hidden = np.zeros(
                (spec.eval_lanes, spec.n_agents, agent.config.gru_hidden_size), np.float32
            )
            for t in range(spec.horizon):
                if t % spec.k == 0:
                    # Exactly one frozen-B01 selection call per renewal. Auditing only
                    # observes its returned arrays and consumes no random values.
                    team, skills = select_skills(
                        agent, states, observations, rule, label_rng
                    )
                    update_digest(
                        label_digest, np.asarray([t], np.int64), team, skills
                    )
                    renewals += 1
                actions, hidden = low_actions(
                    agent, observations, skills, hidden, deterministic=True
                )
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
                    for name in b01.COMPONENTS:
                        sums[name][lane] += parts[name]
                    states[lane], observations[lane] = state, obs
        finally:
            for env in envs:
                env.close()
    scores = spec.n_agents * returns / spec.horizon
    np.testing.assert_allclose(
        scores, sums["total_reward"] / spec.horizon, atol=1e-7, rtol=1e-7
    )
    result = {
        "status": "complete",
        "rule": rule,
        "low_actions": "mean_clipped",
        "world_seeds": list(
            range(spec.eval_world_base, spec.eval_world_base + spec.eval_lanes)
        ),
        "transitions": spec.eval_lanes * spec.horizon,
        "optimizer_calls": 0,
        "normalizer_updates": 0,
        "returns_U": returns,
        "native_scores_J": scores,
        "mean_J": float(scores.mean()),
        "component_means": {name: value / spec.horizon for name, value in sums.items()},
        "connected_users_per_step": (
            sums["coverage_reward"] * spec.n_users / spec.horizon
        ),
        "raw_saturation_fraction": saturation / total_action_coordinates,
        "physical_initial_state_sha256": initial_digest.hexdigest(),
        "physical_initial_state_fields": ["native_state", "joint_observations"],
        "selected_label_stream_sha256": label_digest.hexdigest(),
        "selected_label_renewals": renewals,
        "selected_label_stream_seed": seed,
        "selected_label_stream_bit_generator": type(label_rng.bit_generator).__name__,
        "selected_label_stream_order": (
            "at each k10 renewal: int64 time, team[lanes], individual[lanes,n_agents]"
        ),
    }
    if rule == "uniform" and spec == DEFAULT_SPEC:
        result["frozen_b01_uniform_stream_sha256"] = EXPECTED_UNIFORM_LABEL_STREAM_SHA256
        result["frozen_b01_uniform_stream_match"] = (
            label_digest.hexdigest() == EXPECTED_UNIFORM_LABEL_STREAM_SHA256
        )
        if not result["frozen_b01_uniform_stream_match"]:
            raise ValueError("uniform label stream differs from the frozen B01 convention")
    return result


def save_checkpoint(agent, path: Path, config: dict, stage: int):
    body = {
        "object_id": OBJECT,
        "arm": agent.arm,
        "stage": stage,
        "config": config,
        "native": {
            name: getattr(agent, name).state_dict()
            for name in b01.MODULES
            if getattr(agent, name) is not None
        },
        "normalizers": {
            name: copy.deepcopy(getattr(agent, name)) for name in b01.NORMALIZERS
        },
        "auxiliary": agent.auxiliary_state_dict(),
    }
    torch.save(body, path)
    return {
        "file": path.name,
        "sha256": b01.native._sha256_file(path),
        "bytes": path.stat().st_size,
        "native_digest": native_digest(agent),
        "frozen_digest": frozen_digest(agent),
    }


def _storage_failure(telemetry: dict, reason: str, step: int, env_id: int) -> None:
    telemetry["failures"] += 1
    telemetry["last_failure"] = {
        "reason": reason,
        "rollout_step": int(step),
        "env_id": int(env_id),
        "verified_rows_before_failure": int(telemetry["verified_rows"]),
    }
    raise RuntimeError(
        f"native rollout storage verification failed at t={step}, env={env_id}: {reason}"
    )


def _assert_stored_array(
    telemetry: dict,
    actual,
    expected,
    name: str,
    step: int,
    env_id: int,
) -> None:
    actual = np.asarray(actual, dtype=np.float32)
    expected = np.asarray(expected, dtype=np.float32)
    if (
        actual.shape != expected.shape
        or not np.isfinite(actual).all()
        or not np.isfinite(expected).all()
        or not np.allclose(actual, expected, rtol=1e-6, atol=2e-6)
    ):
        _storage_failure(telemetry, name, step, env_id)


def store_verified_batch(agent, telemetry: dict, **kwargs) -> int:
    """Store and verify every native row before it contributes to actual counts."""
    step = kwargs.get("rollout_step_idx")
    if step is None:
        raise ValueError("B03 storage verification requires rollout_step_idx")
    step = int(step)
    rows = int(len(kwargs["rewards"]))
    telemetry["batch_calls"] += 1
    telemetry["expected_rows"] += rows
    result = agent.store_transition_batch(**kwargs)
    if not isinstance(result, list) or len(result) != rows:
        _storage_failure(telemetry, "native batch return row count", step, -1)
    required = ("env", "team_disc", "ind_disc", "process")
    buffer = agent.rollout_buffer
    for env_id, returned in enumerate(result):
        if not isinstance(returned, dict) or any(name not in returned for name in required):
            _storage_failure(telemetry, "native row refused or incomplete", step, env_id)
        if not bool(buffer.masks[step, env_id]):
            _storage_failure(telemetry, "rollout buffer mask is false", step, env_id)
        components = {
            name: np.asarray(returned[name], dtype=np.float32) for name in required
        }
        expected_shape = (int(agent.config.n_agents),)
        if any(
            value.shape != expected_shape or not np.isfinite(value).all()
            for value in components.values()
        ):
            _storage_failure(telemetry, "returned component shape or finiteness", step, env_id)
        expected_low = sum(components.values(), np.zeros(expected_shape, np.float32))
        _assert_stored_array(
            telemetry, buffer.rewards[step, env_id], expected_low,
            "stored low reward", step, env_id,
        )
        for returned_name, buffer_name in (
            ("env", "reward_env"),
            ("team_disc", "reward_team_disc"),
            ("ind_disc", "reward_ind_disc"),
            ("process", "reward_process"),
        ):
            _assert_stored_array(
                telemetry,
                getattr(buffer, buffer_name)[step, env_id],
                components[returned_name],
                f"stored {returned_name} component",
                step,
                env_id,
            )
        telemetry["verified_rows"] += 1
    return rows


def _validate_completed_contract(summary: dict, spec: Spec) -> None:
    expected = {
        "started_fits": 1,
        "model_constructions": 1,
        "training_transitions": spec.lanes * spec.horizon * spec.rollouts,
        "stored_transitions": spec.lanes * spec.horizon * spec.rollouts,
        "training_episodes": spec.lanes * spec.rollouts,
        "native_updates": spec.rollouts,
        "evaluation_transitions": 4 * spec.eval_lanes * spec.horizon,
        "evaluation_episodes": 4 * spec.eval_lanes,
    }
    if summary["counts"] != expected:
        raise ValueError(f"B03 transition/update counts differ: {summary['counts']} != {expected}")
    storage = summary["storage_verification"]
    if (
        storage["batch_calls"] != spec.horizon * spec.rollouts
        or storage["expected_rows"] != expected["stored_transitions"]
        or storage["verified_rows"] != expected["stored_transitions"]
        or storage["failures"] != 0
    ):
        raise ValueError("B03 did not verify every native rollout storage row")
    panels = summary["panels"]
    if set(panels) != {
        "initial_own", "initial_uniform", "final_own", "final_uniform"
    }:
        raise ValueError("B03 requires exactly four fixed evaluation panels")
    initial_states = {
        panel["physical_initial_state_sha256"] for panel in panels.values()
    }
    if len(initial_states) != 1:
        raise ValueError("fixed evaluation panels did not repeat one physical initial state")
    if (
        panels["initial_uniform"]["selected_label_stream_sha256"]
        != panels["final_uniform"]["selected_label_stream_sha256"]
    ):
        raise ValueError("initial/final uniform panels did not repeat one label stream")
    if any(panel["optimizer_calls"] or panel["normalizer_updates"] for panel in panels.values()):
        raise ValueError("evaluation changed optimizer or normalizer state")
    if not spec.small_model:
        if summary["native_optimizer_calls"] != EXPECTED_NATIVE_OPTIMIZER_CALLS:
            raise ValueError("production native optimizer counts differ from the fixed protocol")
        auxiliary_steps = {
            "head_G": sum(
                row["auxiliary"]["head_optimizer_steps"]["G"]
                for row in summary["training_rows"]
            ),
            "head_P": sum(
                row["auxiliary"]["head_optimizer_steps"]["P"]
                for row in summary["training_rows"]
            ),
            "trunk": sum(
                row["auxiliary"]["trunk_optimizer_steps"]
                for row in summary["training_rows"]
            ),
        }
        expected_auxiliary = {
            "head_G": 315,
            "head_P": 315,
            "trunk": 315 if summary["arm"] == "G" else 0,
        }
        if auxiliary_steps != expected_auxiliary:
            raise ValueError("production auxiliary optimizer counts differ from the fixed protocol")
        summary["auxiliary_optimizer_calls"] = auxiliary_steps


def run_fit(arm, out, launch_sha, *, spec=DEFAULT_SPEC, device="cuda", admission=None):
    if arm not in ("D", "G"):
        raise ValueError(arm)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists():
        raise ValueError("a fit never overwrites an existing summary")
    torch.set_num_threads(spec.threads)
    logging.getLogger().setLevel(logging.WARNING)
    started = time.perf_counter()
    cpu_started = resource.getrusage(resource.RUSAGE_SELF)
    counts = dict.fromkeys(
        (
            "started_fits", "model_constructions", "training_transitions",
            "stored_transitions", "training_episodes", "native_updates",
            "evaluation_transitions", "evaluation_episodes",
        ),
        0,
    )
    summary = {
        "object_id": OBJECT,
        "direction": DIRECTION,
        "arm": arm,
        "launch_sha": launch_sha,
        "status": "incomplete",
        "spec": asdict(spec),
        "device": str(device),
        "admission": admission,
        "counts": counts,
        "training_rows": [],
        "panels": {},
        "checkpoints": {},
        "storage_verification": {
            "batch_calls": 0,
            "expected_rows": 0,
            "verified_rows": 0,
            "failures": 0,
            "last_failure": None,
        },
    }
    summary["runtime"] = {
        "python": sys.version,
        "numpy": np.__version__,
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "torch_threads": torch.get_num_threads(),
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
        },
        "learner_dtype": "float32",
        "reward_return_dtype": "float64",
        "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
    }
    write_json(
        out / "config.json",
        {
            "object_id": OBJECT,
            "arm": arm,
            "spec": asdict(spec),
            "launch_sha": launch_sha,
            "device": str(device),
        },
    )
    envs = []
    agent = counters = None
    try:
        if torch.device(device).type == "cuda":
            torch.cuda.reset_peak_memory_stats(torch.device(device))
            summary["runtime"]["cuda_device"] = torch.cuda.get_device_name(torch.device(device))
        envs = make_envs(spec, spec.lanes, spec.train_world_base)
        config = make_config(spec, envs)
        summary["learner_config"] = effective_config(config)
        seed_rng(spec.init_seed)
        agent = AuditedComplementaryAgent(
            config=config,
            arm=arm,
            head_seed=spec.head_seed,
            aux_seed=spec.aux_seed,
            log_dir=str(out / "learner_logs"),
            device=torch.device(device),
        )
        counts["model_constructions"] += 1
        theta0 = b01.native._capture_theta0(agent)
        counters = support.optimizer_counters(agent)
        summary["initial_native_digest"] = native_digest(agent)
        summary["initial_frozen_digest"] = frozen_digest(agent)
        summary["initial_rng_state_sha256"] = rng_state_digest()
        summary["auxiliary_parameter_counts"] = jsonable(agent.parameter_counts)
        summary["auxiliary_architecture"] = jsonable(agent.auxiliary_architecture)
        summary["checkpoints"]["initial"] = save_checkpoint(
            agent, out / "initial.pt", summary["learner_config"], 0
        )
        seed_rng(spec.train_rng_seed)
        summary["panels"]["initial_own"] = evaluate_panel(
            agent, spec, "own", counter=counts
        )
        summary["panels"]["initial_uniform"] = evaluate_panel(
            agent, spec, "uniform", counter=counts
        )
        write_json(out / "summary.json", summary)

        states, observations = b01.native._reset_all(envs)
        env_steps = np.zeros(spec.lanes, np.int64)
        dones = np.zeros(spec.lanes, bool)
        agent.train(True)
        counts["started_fits"] += 1
        first_digest = hashlib.sha256()
        label_hist = np.zeros((spec.n_agents, 6), np.int64)
        joint_hist: dict[str, int] = {}
        for rollout in range(spec.rollouts):
            began = time.perf_counter()
            returns = np.zeros(spec.lanes, np.float64)
            saturation = action_coordinates = 0
            before = support.optimizer_counts(counters)
            for t in range(spec.horizon):
                actions, _, data = agent.step(
                    states,
                    observations,
                    env_steps,
                    dones,
                    deterministic=False,
                    return_step_data=True,
                    build_infos=False,
                )
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
                    update_digest(
                        first_digest,
                        states,
                        observations,
                        actions,
                        rewards,
                        data["team_skills"],
                        data["agent_skills"],
                        data["action_logprobs"],
                    )
                if t % spec.k == 0:
                    if not np.asarray(data["d2_team_decision"]).all():
                        raise ValueError("fixed k10 boundary was not a full native team decision")
                    for lane, skill in enumerate(data["agent_skills"]):
                        label_hist[np.arange(spec.n_agents), skill] += 1
                        key = ",".join(
                            map(
                                str,
                                [int(data["team_skills"][lane]), *map(int, skill)],
                            )
                        )
                        joint_hist[key] = joint_hist.get(key, 0) + 1
                saturation += int((np.abs(actions) > 1).sum())
                action_coordinates += actions.size
                verified = store_verified_batch(
                    agent,
                    summary["storage_verification"],
                    states=states,
                    next_states=next_states.copy(),
                    observations=observations,
                    next_observations=next_obs.copy(),
                    actions=actions,
                    rewards=rewards,
                    dones=next_dones,
                    infos_batch=None,
                    rollout_step_idx=t,
                    step_data=data,
                )
                counts["stored_transitions"] += verified
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
            losses = agent.update(
                last_values=np.zeros((spec.lanes, spec.n_agents), np.float32),
                dones=dones.copy(),
                steps_in_buffer=spec.horizon,
                last_state=states.copy(),
                last_observations=observations.copy(),
            )
            counts["native_updates"] += 1
            after = support.optimizer_counts(counters)
            aux = agent.auxiliary_history[-1]
            expected_windows = spec.lanes * spec.horizon // spec.k
            expected_aux_steps = (expected_windows + 127) // 128
            if (
                aux["samples"] != expected_windows
                or aux["discarded_terminal_windows"] != 0
                or aux["head_optimizer_steps"]
                != {"G": expected_aux_steps, "P": expected_aux_steps}
                or aux["trunk_optimizer_steps"]
                != (0 if arm == "D" else expected_aux_steps)
            ):
                raise ValueError("auxiliary factual exposure differs from the fixed protocol")
            if any(after[key] <= before[key] for key in after):
                raise ValueError("a native optimizer group did not update")
            predictions = {
                "rollout": rollout + 1,
                **jsonable(aux.pop("raw_prediction_rows")),
            }
            prediction_bytes = (json.dumps(predictions, allow_nan=False) + "\n").encode()
            with (out / "auxiliary_predictions.jsonl").open("ab") as stream:
                stream.write(prediction_bytes)
            aux["raw_predictions"] = {
                "file": "auxiliary_predictions.jsonl",
                "line": rollout + 1,
                "sha256": hashlib.sha256(prediction_bytes).hexdigest(),
                "rows": aux["samples"],
                "timing": "after this rollout's auxiliary update",
            }
            if rollout == 0:
                summary["first_rollout_facts_sha256"] = first_digest.hexdigest()
            row = {
                "rollout": rollout + 1,
                "training_transitions": counts["training_transitions"],
                "returns_U": returns,
                "training_J": spec.n_agents * returns / spec.horizon,
                "native_losses": losses,
                "native_optimizer_calls": after,
                "optimizer_delta": {key: after[key] - before[key] for key in after},
                "auxiliary": aux,
                "relative_initialization_displacement": b01.native._exposure_line(
                    agent, theta0
                ),
                "raw_saturation_fraction": saturation / action_coordinates,
                "wall_seconds": time.perf_counter() - began,
            }
            summary["training_rows"].append(jsonable(row))
            summary["native_optimizer_calls"] = after
            summary["actual_label_occupancy"] = label_hist
            summary["actual_joint_occupancy"] = joint_hist
            with (out / "training.jsonl").open("a") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            agent.clear_buffers()
            write_json(out / "summary.json", summary)

        summary["checkpoints"]["final"] = save_checkpoint(
            agent, out / "final.pt", summary["learner_config"], spec.rollouts
        )
        summary["panels"]["final_own"] = evaluate_panel(
            agent, spec, "own", counter=counts
        )
        write_json(out / "summary.json", summary)
        summary["panels"]["final_uniform"] = evaluate_panel(
            agent, spec, "uniform", counter=counts
        )
        summary["auxiliary_predictions"] = {
            "file": "auxiliary_predictions.jsonl",
            "sha256": b01.native._sha256_file(out / "auxiliary_predictions.jsonl"),
            "batches": spec.rollouts,
        }
        summary["final_native_digest"] = native_digest(agent)
        summary["final_frozen_digest"] = frozen_digest(agent)
        _validate_completed_contract(summary, spec)
        summary["status"] = "complete"
    except BaseException as exc:
        summary["status"] = "failed"
        summary["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "process_wall_seconds": time.perf_counter() - started,
            "user_cpu_seconds": usage.ru_utime - cpu_started.ru_utime,
            "system_cpu_seconds": usage.ru_stime - cpu_started.ru_stime,
            "peak_process_rss_kib": usage.ru_maxrss,
            "scope": (
                "runner body; process RSS lifetime peak; shared-node occupancy unmeasured"
            ),
        }
        if torch.device(device).type == "cuda" and torch.cuda.is_initialized():
            summary["resources"]["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated(
                torch.device(device)
            )
            summary["resources"]["peak_cuda_reserved_bytes"] = torch.cuda.max_memory_reserved(
                torch.device(device)
            )
        if agent is not None:
            summary["auxiliary_history"] = jsonable(agent.auxiliary_history)
        counts["stored_transitions"] = int(
            summary["storage_verification"]["verified_rows"]
        )
        if counters is not None:
            summary["native_optimizer_calls"] = support.optimizer_counts(counters)
        write_json(out / "summary.json", summary)
        for env in envs:
            env.close()
    return summary


__all__ = [
    "DEFAULT_SPEC",
    "EXPECTED_NATIVE_OPTIMIZER_CALLS",
    "EXPECTED_UNIFORM_LABEL_STREAM_SHA256",
    "Spec",
    "evaluate_panel",
    "make_config",
    "rng_state_digest",
    "run_fit",
    "save_checkpoint",
]
