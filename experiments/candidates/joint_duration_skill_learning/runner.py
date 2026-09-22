"""B01 full Scenario1 learning; result CLI requires native launch admission."""
from __future__ import annotations

import time

PROCESS_START = time.perf_counter()

import argparse
import contextlib
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import random
import resource
import socket
import sys
import traceback

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from scripts import run_flexible_skill_duration_e0 as native
from scripts.hmasd_admission import require_admission
from experiments.candidates.joint_duration_skill_learning.learning import DurationAgent

DIRECTION = "joint_duration_skill_learning"
SEEDS = {"fixed": 2026092201, "factored": 2026092202, "ar": 2026092203}
COMPONENTS = ("coverage_reward", "quality_reward", "energy_penalty", "total_reward")
NETWORKS = ("coordinator", "discoverer_actor", "discoverer_critic",
            "team_discriminator", "individual_discriminator")


@dataclass(frozen=True)
class StudySpec:
    arm: str
    seed: int
    lanes: int = 16
    horizon: int = 500
    rollouts: int = 45
    eval_lanes: int = 32
    eval_seed: int = 740000
    eval_rollouts: tuple[int, ...] = (0, 15, 30, 45)
    n_agents: int = 6
    n_users: int = 50
    epochs: int = 15
    threads: int = 4
    coordinator_batch_size: int = 1280


def finite_json(value):
    if isinstance(value, dict):
        return {str(key): finite_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [finite_json(item) for item in value]
    if isinstance(value, torch.Tensor):
        return finite_json(value.detach().cpu().numpy())
    if isinstance(value, np.ndarray):
        return finite_json(value.tolist())
    if isinstance(value, np.generic):
        return finite_json(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"nonfinite recorded measurement: {value}")
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"unsupported measurement type {type(value).__name__}")


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(finite_json(value), indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def resource_facts(started):
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "wall_seconds": time.perf_counter() - started,
        "process_user_cpu_seconds": own.ru_utime,
        "process_system_cpu_seconds": own.ru_stime,
        "process_peak_rss_kib_linux": own.ru_maxrss,
        "children_user_cpu_seconds": children.ru_utime,
        "children_system_cpu_seconds": children.ru_stime,
        "children_peak_rss_kib_linux_not_added_to_process_peak": children.ru_maxrss,
        "rss_scope": "scientific process and separate reaped-child maxima; not node occupancy",
    }


@contextlib.contextmanager
def preserve_rng():
    python_state, numpy_state = random.getstate(), np.random.get_state()
    cpu_state = torch.get_rng_state()
    cuda_states = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    try:
        yield
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.set_rng_state(cpu_state)
        if cuda_states is not None:
            torch.cuda.set_rng_state_all(cuda_states)


def seed_rng(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_config(spec, envs):
    config = native._make_config(
        "D0", spec.seed, len(envs), spec.horizon, spec.horizon, spec.n_agents,
        spec.n_users, spec.rollouts, envs[0].state_dim, envs[0].obs_dim,
    )
    config.n_Z = config.n_z = 6
    config.duration_mode = spec.arm
    config.duration_lambda_10 = .95
    config.coordinator_batch_size = spec.coordinator_batch_size
    config.ppo_epochs = spec.epochs
    config.sequence_batch_size = 32
    config.coordinator_dropout = 0.0
    assert not config.use_obsnorm and not config.use_statenorm
    assert config.k == config.skill_cap_k_max == config.team_cap_k_Z == 10
    return config


def config_snapshot(config):
    names = native.CONFIG_DUMP_FIELDS + (
        "duration_mode", "duration_lambda_10", "coordinator_dropout", "clip_epsilon",
        "sequence_batch_size", "n_encoder_layers", "n_decoder_layers", "value_clip",
    )
    # Infinity is a declared disabled-gap threshold, never a measured quantity.
    return {name: native._jsonable(getattr(config, name)) for name in names if hasattr(config, name)}


def count_optimizers(agent):
    return {name: native._StepCounter(getattr(agent, name + "_optimizer"))
            for name in NETWORKS if getattr(agent, name + "_optimizer", None) is not None}


def optimizer_counts(counters):
    return {name: counter.count for name, counter in counters.items()}


def close_envs(envs):
    for env in envs:
        env.close()


def evaluate(learner, spec, out, device, after_rollout, summary):
    """Recreate exactly the declared world panel, with no learner RNG mutation."""
    started = time.perf_counter()
    result = {
        "status": "incomplete", "after_rollout": after_rollout,
        "training_transitions": after_rollout * spec.lanes * spec.horizon,
        "world_seeds": list(range(spec.eval_seed, spec.eval_seed + spec.eval_lanes)),
        "deterministic": True, "transitions": 0, "episodes": 0,
        "steps_per_lane": [0] * spec.eval_lanes,
    }
    summary["evaluations"].append(result)
    with preserve_rng():
        seed_rng(spec.eval_seed)
        envs = native._make_envs(spec.eval_lanes, spec.eval_seed, spec.n_agents,
                                 spec.n_users, spec.horizon)
        try:
            evaluator = DurationAgent(make_config(spec, envs),
                                      log_dir=str(out / "evaluation_logs"), device=device)
            for name in ("skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator"):
                target, source = getattr(evaluator, name), getattr(learner, name)
                if source is not None:
                    target.load_state_dict(source.state_dict())
            for name in ("obs_norm", "state_norm", "value_norm_coordinator", "value_norm_discoverer"):
                setattr(evaluator, name, copy.deepcopy(getattr(learner, name)))
            evaluator.train(False)
            counters = count_optimizers(evaluator)
            states, observations = native._reset_all(envs)
            steps = np.zeros(spec.eval_lanes, dtype=np.int64)
            dones = np.zeros(spec.eval_lanes, dtype=bool)
            returns = np.zeros(spec.eval_lanes, dtype=np.float64)
            components = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
            with torch.no_grad():
                for t in range(spec.horizon):
                    actions, _, _ = evaluator.step(states, observations, steps, dones,
                        deterministic=True, return_step_data=True, build_infos=False)
                    finite_json(actions)
                    for lane, env in enumerate(envs):
                        obs, reward, terminated, truncated, info = env.step(actions[lane])
                        result["transitions"] += 1
                        result["steps_per_lane"][lane] += 1
                        summary["counts"]["evaluation_transitions"] += 1
                        dones[lane] = bool(terminated or truncated)
                        result["episodes"] += int(dones[lane])
                        summary["counts"]["evaluation_episodes"] += int(dones[lane])
                        returns[lane] += reward
                        for name in COMPONENTS:
                            components[name][lane] += info["reward_components"]["reward_info"][name]
                        states[lane] = info["next_state"]
                        observations[lane] = obs
                    steps += 1
                    if dones.any() != (t == spec.horizon - 1) or (t == spec.horizon - 1 and not dones.all()):
                        raise ValueError("evaluation did not match the declared finite episode boundary")
            evaluator.finish_evaluation_episode(dones)
            calls = optimizer_counts(counters)
            assert all(count == 0 for count in calls.values())
            result.update(finite_json({
                "returns_U": returns,
                "native_scores_J": spec.n_agents * returns / spec.horizon,
                "mean_native_J": float(np.mean(spec.n_agents * returns / spec.horizon)),
                "component_means": {name: value / spec.horizon for name, value in components.items()},
                "optimizer_calls": calls,
                "duration": evaluator.get_duration_metrics(),
                "wall_seconds": time.perf_counter() - started,
            }))
            result["status"] = "complete"
            return result
        finally:
            close_envs(envs)


def train_rollout(agent, envs, spec, states, observations, dones, counters, rollout, summary):
    started = time.perf_counter()
    before = optimizer_counts(counters)
    returns = np.zeros(spec.lanes, dtype=np.float64)
    steps = np.zeros(spec.lanes, dtype=np.int64)
    agent.train(True)
    for t in range(spec.horizon):
        actions, _, step_data = agent.step(states, observations, steps, dones,
            deterministic=False, return_step_data=True, build_infos=False)
        finite_json(actions)
        next_states, next_obs = [], []
        rewards = np.zeros(spec.lanes, dtype=np.float64)
        next_dones = np.zeros(spec.lanes, dtype=bool)
        for lane, env in enumerate(envs):
            obs, reward, terminated, truncated, info = env.step(actions[lane])
            next_states.append(np.asarray(info["next_state"], dtype=np.float64))
            next_obs.append(np.asarray(obs, dtype=np.float32))
            rewards[lane] = reward
            next_dones[lane] = bool(terminated or truncated)
            summary["counts"]["training_transitions"] += 1
            summary["counts"]["training_episodes"] += int(next_dones[lane])
        next_states, next_obs = np.stack(next_states), np.stack(next_obs)
        finite_json((rewards, next_states, next_obs))
        if next_dones.any() != (t == spec.horizon - 1) or (t == spec.horizon - 1 and not next_dones.all()):
            raise ValueError("training did not match the declared finite episode boundary")
        agent.store_transition_batch(states=states, next_states=next_states, observations=observations,
            next_observations=next_obs, actions=actions, rewards=rewards, dones=next_dones,
            rollout_step_idx=t, step_data=step_data)
        summary["counts"]["stored_training_transitions"] += spec.lanes
        returns += rewards
        steps += 1
        states, observations, dones = next_states, next_obs, next_dones
    collection_wall = time.perf_counter() - started
    # The true finite task ended in every lane; do not use the reset world as bootstrap.
    update_started = time.perf_counter()
    try:
        losses = agent.update(last_values=np.zeros((spec.lanes, spec.n_agents), dtype=np.float32),
                              dones=dones.copy(), steps_in_buffer=spec.horizon)
    finally:
        summary["optimizer_calls"] = optimizer_counts(counters)
    summary["counts"]["update_stages"] += 1
    row = {
        "rollout": rollout, "transitions": spec.lanes * spec.horizon,
        "episode_returns_U": returns, "losses": losses,
        "optimizer_calls_delta": {name: count - before[name] for name, count in summary["optimizer_calls"].items()},
        "optimizer_calls_total": summary["optimizer_calls"],
        "duration": agent.get_duration_metrics(),
        "collection_wall_seconds": collection_wall,
        "update_wall_seconds": time.perf_counter() - update_started,
    }
    # Complete terminal storage is consumed by update before resets/clearing.
    for lane in range(spec.lanes):
        agent.reset_env_state(lane)
    agent.clear_buffers()
    states, observations = native._reset_all(envs)
    return states, observations, dones, finite_json(row)


def save_checkpoint(agent, out, transitions):
    path = out / f"checkpoint_{transitions}.pt"
    agent.save_model(str(path))
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": path.name, "sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def execute(spec, out, launch_sha, device, *, started=PROCESS_START):
    """Scientific body. Tests call with a tiny explicit spec; CLI never exposes that route."""
    out = Path(out)
    if (out / "summary.json").exists():
        raise FileExistsError("refusing to overwrite an existing scientific attempt")
    if spec.arm not in SEEDS or spec.horizon % 10 or spec.eval_rollouts[-1] != spec.rollouts:
        raise ValueError("invalid duration study binding")
    out.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": "joint_duration_skill_learning_b01_v1", "status": "incomplete",
        "direction": DIRECTION, "launch_sha": launch_sha, "spec": asdict(spec),
        "device": str(device), "host": socket.gethostname(),
        "torch_version": torch.__version__, "numpy_version": np.__version__,
        "thread_environment": {name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "counts": {"training_transitions": 0, "stored_training_transitions": 0,
                   "training_episodes": 0, "update_stages": 0,
                   "evaluation_transitions": 0, "evaluation_episodes": 0,
                   "training_starts": 0, "checkpoint_loads": 0},
        "optimizer_calls": {}, "evaluations": [], "checkpoints": [], "training_rows": [],
        "resource_limits": "native admission; no score-dependent extension or automatic retry",
        "scientific_scope": "one fresh training instance per arm, exploratory package comparison",
    }
    envs = []

    def publish(stage):
        summary["stage"] = stage
        summary["resources"] = resource_facts(started)
        write_json(out / "summary.json", summary)
        print(json.dumps({"stage": stage, "training_transitions": summary["counts"]["training_transitions"],
                          "wall_seconds": summary["resources"]["wall_seconds"]}), flush=True)

    try:
        torch.set_num_threads(spec.threads)
        if str(device).startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("declared CUDA device is unavailable; no implicit device fallback")
        seed_rng(spec.seed)
        envs = native._make_envs(spec.lanes, spec.seed, spec.n_agents, spec.n_users, spec.horizon)
        config = make_config(spec, envs)
        summary["config"] = config_snapshot(config)
        agent = DurationAgent(config, log_dir=str(out / "learner_logs"), device=device)
        summary["counts"]["training_starts"] = 1
        theta0 = native._capture_theta0(agent)
        summary["initial_parameter_norms"] = finite_json({key: value["norm"] for key, value in theta0.items()})
        summary["parameter_counts"] = {key: sum(param.numel() for param in params)
                                       for key, params in native._parameter_groups(agent).items()}
        counters = count_optimizers(agent)
        summary["optimizer_calls"] = optimizer_counts(counters)
        publish("constructed")

        def evaluate_boundary(rollout):
            evaluate(agent, spec, out, device, rollout, summary)
            summary["checkpoints"].append(save_checkpoint(agent, out, rollout * spec.lanes * spec.horizon))
            publish(f"evaluated_{rollout}")

        if 0 in spec.eval_rollouts:
            evaluate_boundary(0)
        states, observations = native._reset_all(envs)
        dones = np.zeros(spec.lanes, dtype=bool)
        for rollout in range(1, spec.rollouts + 1):
            states, observations, dones, row = train_rollout(
                agent, envs, spec, states, observations, dones, counters, rollout, summary)
            row["relative_initialization_displacement"] = finite_json(native._exposure_line(agent, theta0))
            summary["training_rows"].append(row)
            with (out / "training.jsonl").open("a") as stream:
                stream.write(json.dumps(finite_json(row), allow_nan=False) + "\n")
            publish(f"updated_{rollout}")
            if rollout in spec.eval_rollouts:
                evaluate_boundary(rollout)
        expected = spec.lanes * spec.horizon * spec.rollouts
        assert summary["counts"]["training_transitions"] == summary["counts"]["stored_training_transitions"] == expected
        if not all(count > 0 for count in summary["optimizer_calls"].values()):
            raise RuntimeError("an expected native learner optimizer received no updates")
        summary["final_relative_initialization_displacement"] = finite_json(native._exposure_line(agent, theta0))
        if not all(value is not None and value > 0 for value in summary["final_relative_initialization_displacement"].values()):
            raise RuntimeError("an expected native learner parameter group did not move")
        summary["status"] = "complete"
        publish("complete")
        return summary
    except BaseException as error:
        summary["status"] = "incomplete"
        summary["error"] = f"{type(error).__name__}: {error}"
        (out / "error.txt").write_text(traceback.format_exc())
        publish("technical_failure")
        raise
    finally:
        close_envs(envs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True, choices=tuple(SEEDS))
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    args = parser.parse_args(argv)
    if args.seed != SEEDS[args.arm]:
        parser.error("seed must match the predeclared B01 arm")
    admission = require_admission(__file__, direction="joint_duration_skill_learning")
    if admission["sha"] != args.launch_sha:
        raise ValueError("CLI launch SHA differs from native admission")
    execute(StudySpec(args.arm, args.seed), args.out, args.launch_sha, torch.device(args.device))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
