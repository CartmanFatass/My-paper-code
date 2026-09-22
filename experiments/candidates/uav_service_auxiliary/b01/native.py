"""Native Scenario-7 comparison runner for UAV service auxiliary learning."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import resource
import shutil
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from configs.config_1 import Config
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from hmasd.agent import HMASDAgent
from hmasd.baselines import apply_algorithm_config

from .auxiliary import AuxiliaryReplay, future_window_targets


OBJECT_ID = "UAV-SERVICE-AUXILIARY-B01"
FACT_SEEDS = (930001, 930002)
EVAL_SEEDS = tuple(range(920001, 920009))
EVAL_ROLLOUTS = (0, 10, 20, 30)
METRIC_FIELDS = (
    "qos_satisfaction_ratio",
    "delivered_end_to_end_throughput_mbps",
    "return_constraint_cost",
    "cutoff_event_count",
    "depletion_event_count",
    "charging_uav_count",
    "step_charger_input_wh",
    "battery_min_ratio",
)


@dataclass(frozen=True)
class NativeSpec:
    seed: int = 910021
    lanes: int = 4
    rollouts: int = 30
    rollout_length: int = 1500
    episode_length: int = 1500
    window: int = 10
    threads: int = 4
    head_seed_offset: int = 200000
    eval_seeds: tuple[int, ...] = EVAL_SEEDS
    fact_seeds: tuple[int, ...] = FACT_SEEDS
    ppo_epochs: int | None = None
    hidden_size: int | None = None
    gru_hidden_size: int | None = None

    @property
    def transitions(self) -> int:
        return self.lanes * self.rollouts * self.rollout_length


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def seed_everything(seed: int, device: torch.device) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)


def _rng_state() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.random.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
    }


def _restore_rng(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.random.set_rng_state(state["torch"])
    if state["cuda"] is not None:
        torch.cuda.set_rng_state_all(state["cuda"])


@contextmanager
def preserved_rng():
    state = _rng_state()
    try:
        yield
    finally:
        _restore_rng(state)


def active_config(config: Config) -> dict[str, Any]:
    """Materialize scalar/list config including class defaults, not only instance vars."""
    result: dict[str, Any] = {}
    for name in dir(config):
        if name.startswith("_"):
            continue
        value = getattr(config, name)
        if callable(value):
            continue
        if isinstance(value, (str, int, float, bool, type(None))):
            result[name] = value
        elif isinstance(value, (list, tuple)) and all(
            isinstance(item, (str, int, float, bool, type(None))) for item in value
        ):
            result[name] = list(value)
    return result


def make_config(spec: NativeSpec, *, lanes: int | None = None) -> Config:
    config = Config("S7-S2")
    config.num_envs = spec.lanes if lanes is None else int(lanes)
    config.rollout_length = spec.rollout_length
    config.episode_length = spec.episode_length
    config.max_steps = spec.episode_length
    config.k = 10
    config.scenario7_comparison_gate_enabled = False
    config.scenario7_run_physical_feasibility_check = False
    config.seed = spec.seed
    config.total_timesteps = spec.transitions
    if spec.ppo_epochs is not None:
        config.ppo_epochs = int(spec.ppo_epochs)
    if spec.hidden_size is not None:
        config.hidden_size = int(spec.hidden_size)
        config.embedding_dim = int(spec.hidden_size)
    if spec.gru_hidden_size is not None:
        config.gru_hidden_size = int(spec.gru_hidden_size)
    apply_algorithm_config(config, "hmasd")
    probe = ParallelToArrayAdapter(UAVEnergyAwareRelayEnv(config=config, seed=spec.seed))
    try:
        config.state_dim = int(probe.state_dim)
        config.obs_dim = int(probe.obs_dim)
        config.action_dim = int(probe.action_space.shape[-1])
    finally:
        probe.close()
    config.calculate_and_set_buffer_sizes()
    return config


def make_env(config: Config, seed: int) -> ParallelToArrayAdapter:
    return ParallelToArrayAdapter(UAVEnergyAwareRelayEnv(config=config, seed=int(seed)))


def _module_parameters(agent: HMASDAgent) -> dict[str, list[torch.Tensor]]:
    modules = {
        "high": agent.skill_coordinator,
        "low_actor": agent.skill_discoverer.actor,
        "low_critic": agent.skill_discoverer.critic,
        "team_discriminator": agent.team_discriminator,
        "individual_discriminator": agent.individual_discriminator,
    }
    return {
        name: [parameter.detach().cpu().clone() for parameter in module.parameters()]
        for name, module in modules.items()
        if module is not None
    }


def initialization_fingerprint(agent: HMASDAgent) -> str:
    digest = hashlib.sha256()
    for module_name, tensors in sorted(_module_parameters(agent).items()):
        digest.update(module_name.encode("utf-8"))
        for tensor in tensors:
            array = tensor.contiguous().numpy()
            digest.update(str(array.dtype).encode("ascii"))
            digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
            digest.update(array.tobytes())
    return digest.hexdigest()


def parameter_displacement(before: dict[str, list[torch.Tensor]], agent: HMASDAgent) -> dict[str, float]:
    current = _module_parameters(agent)
    result: dict[str, float] = {}
    for name, initial in before.items():
        squared = 0.0
        for old, new in zip(initial, current[name], strict=True):
            squared += float(torch.sum((new - old) ** 2).item())
        result[name] = squared ** 0.5
    return result


def optimizer_steps(agent: HMASDAgent) -> dict[str, int]:
    optimizers = {
        "high": agent.coordinator_optimizer,
        "low_actor": agent.discoverer_actor_optimizer,
        "low_critic": agent.discoverer_critic_optimizer,
        "team_discriminator": agent.team_discriminator_optimizer,
        "individual_discriminator": agent.individual_discriminator_optimizer,
    }
    result: dict[str, int] = {}
    for name, optimizer in optimizers.items():
        if optimizer is None:
            result[name] = 0
            continue
        steps = []
        for state in optimizer.state.values():
            value = state.get("step", 0)
            steps.append(int(value.item() if torch.is_tensor(value) else value))
        result[name] = max(steps, default=0)
    return result


def _sync_agent(source: HMASDAgent, target: HMASDAgent) -> None:
    for name in (
        "skill_coordinator", "skill_discoverer", "team_discriminator",
        "individual_discriminator",
    ):
        source_module = getattr(source, name, None)
        target_module = getattr(target, name, None)
        if source_module is not None and target_module is not None:
            target_module.load_state_dict(source_module.state_dict())
    for name in ("obs_norm", "state_norm", "value_norm_coordinator", "value_norm_discoverer"):
        if hasattr(source, name):
            setattr(target, name, copy.deepcopy(getattr(source, name)))


def _terminal_kind(terminated: bool, truncated: bool) -> str:
    if terminated:
        return "terminated"
    if truncated:
        return "truncated"
    return "horizon"


def _episode(agent: HMASDAgent, env: ParallelToArrayAdapter, seed: int,
             *, collect_facts: bool = False) -> tuple[dict[str, Any], dict[str, np.ndarray] | None]:
    agent.reset_env_state(0)
    observations, info = env.reset(seed=int(seed))
    state = np.asarray(info["state"], dtype=np.float32)
    env_step = 0
    previous_done = np.ones(1, dtype=bool)
    totals = {field: 0.0 for field in METRIC_FIELDS}
    raw_j = 0.0
    fact_obs: list[np.ndarray] = []
    fact_skills: list[np.ndarray] = []
    fact_dones: list[bool] = []
    fact_qos: list[float] = []
    terminated = truncated = False
    while env_step < int(agent.config.episode_length):
        actions, _, step_data = agent.step(
            state[None, :], observations[None, ...], np.asarray([env_step]),
            previous_done, deterministic=True, return_step_data=True, build_infos=False,
        )
        if collect_facts:
            fact_obs.append(np.asarray(observations, dtype=np.float32).copy())
            fact_skills.append(np.asarray(step_data["agent_skills"][0], dtype=np.int64).copy())
        next_obs, reward, terminated, truncated, next_info = env.step(actions[0])
        done = bool(terminated or truncated)
        reward_info = next_info.get("reward_info", {})
        missing = [field for field in METRIC_FIELDS if field not in reward_info]
        if missing:
            raise KeyError(f"Scenario 7 reward_info is missing required metrics: {missing}")
        reward_value = float(reward)
        if not np.isfinite(reward_value):
            raise FloatingPointError("evaluation produced a non-finite native reward")
        raw_j += reward_value
        for field in METRIC_FIELDS:
            value = float(reward_info[field])
            if not np.isfinite(value):
                raise FloatingPointError(f"evaluation produced non-finite metric {field}")
            totals[field] += value
        if collect_facts:
            fact_dones.append(done)
            fact_qos.append(float(reward_info["qos_satisfaction_ratio"]))
        state = np.asarray(next_info["next_state"], dtype=np.float32)
        observations = np.asarray(next_obs, dtype=np.float32)
        previous_done[:] = done
        env_step += 1
        if done:
            break
    if not (terminated or truncated):
        raise RuntimeError("evaluation reached configured horizon without native termination/truncation")
    row = {
        "seed": int(seed), "raw_native_J": raw_j, "native_J_per_step": raw_j / env_step,
        "actual_length": env_step, "terminal_type": _terminal_kind(terminated, truncated),
    }
    for field, value in totals.items():
        row[f"{field}_sum"] = value
        row[f"{field}_per_step"] = value / env_step
    facts = None
    if collect_facts:
        facts = {
            "observations": np.asarray(fact_obs, dtype=np.float32),
            "skills": np.asarray(fact_skills, dtype=np.int64),
            "dones": np.asarray(fact_dones, dtype=np.bool_),
            "qos": np.asarray(fact_qos, dtype=np.float32),
        }
    return row, facts


def evaluate(agent: HMASDAgent, config: Config, seeds: Iterable[int], device: torch.device,
             *, policy_seed: int, log_dir: Path) -> list[dict[str, Any]]:
    with preserved_rng():
        seed_everything(policy_seed, device)
        eval_config = copy.deepcopy(config)
        eval_config.num_envs = 1
        eval_config.calculate_and_set_buffer_sizes()
        evaluator = HMASDAgent(eval_config, log_dir=str(log_dir), device=device)
        _sync_agent(agent, evaluator)
        evaluator.train(False)
        rows = []
        for seed in seeds:
            env = make_env(eval_config, int(seed))
            try:
                row, _ = _episode(evaluator, env, int(seed))
                rows.append(row)
            finally:
                env.close()
    return rows


def evaluation_panel(agent: HMASDAgent, config: Config, seeds: Iterable[int],
                     device: torch.device, *, policy_seed: int, log_dir: Path) -> dict[str, Any]:
    worlds = evaluate(
        agent, config, seeds, device, policy_seed=policy_seed, log_dir=log_dir
    )
    if not worlds:
        raise RuntimeError("evaluation seed panel is empty")
    numeric_fields = [
        key for key, value in worlds[0].items()
        if isinstance(value, (int, float)) and key not in {"seed", "actual_length"}
    ]
    aggregate = {
        f"mean_{field}": float(np.mean([float(world[field]) for world in worlds]))
        for field in numeric_fields
    }
    aggregate["worlds"] = len(worlds)
    aggregate["primary_native_J_mean"] = aggregate["mean_raw_native_J"]
    if not _finite_mapping(aggregate):
        raise FloatingPointError("evaluation aggregate contains a non-finite scalar")
    return {"worlds": worlds, "aggregate": aggregate}


def write_facts(agent: HMASDAgent, config: Config, seeds: Iterable[int], path: Path,
                device: torch.device, *, policy_seed: int, log_dir: Path,
                initialization_sha256: str) -> str:
    arrays: dict[str, np.ndarray] = {}
    with preserved_rng():
        seed_everything(policy_seed, device)
        fact_config = copy.deepcopy(config)
        fact_config.num_envs = 1
        fact_config.calculate_and_set_buffer_sizes()
        evaluator = HMASDAgent(fact_config, log_dir=str(log_dir), device=device)
        _sync_agent(agent, evaluator)
        evaluator.train(False)
        for index, seed in enumerate(seeds):
            env = make_env(fact_config, int(seed))
            try:
                _, facts = _episode(evaluator, env, int(seed), collect_facts=True)
            finally:
                env.close()
            assert facts is not None
            for name, value in facts.items():
                arrays[f"episode_{index}_{name}"] = value
            arrays[f"episode_{index}_seed"] = np.asarray(int(seed), dtype=np.int64)
        arrays["initialization_sha256"] = np.asarray(initialization_sha256)
        arrays["schema"] = np.asarray("uav_service_auxiliary_common_facts_v1")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)
    return sha256_file(path)


def verify_and_copy_facts(source: Path, digest: str, destination: Path, *,
                          expected_seeds: Iterable[int], initialization_sha256: str) -> str:
    observed = sha256_file(source)
    if observed != digest:
        raise ValueError(f"facts digest mismatch: expected {digest}, got {observed}")
    with np.load(source, allow_pickle=False) as archive:
        if str(archive["schema"].item()) != "uav_service_auxiliary_common_facts_v1":
            raise ValueError("facts schema mismatch")
        observed_initialization = str(archive["initialization_sha256"].item())
        if observed_initialization != initialization_sha256:
            raise ValueError("facts were collected from a different policy initialization")
        observed_seeds = tuple(
            int(archive[f"episode_{index}_seed"].item())
            for index, _ in enumerate(expected_seeds)
        )
        if observed_seeds != tuple(int(seed) for seed in expected_seeds):
            raise ValueError(f"facts seeds mismatch: {observed_seeds}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    copied = sha256_file(destination)
    if copied != digest:
        raise RuntimeError("copied facts digest changed")
    return copied


def facts_counts(path: Path) -> tuple[int, int]:
    with np.load(path, allow_pickle=False) as archive:
        observation_keys = sorted(key for key in archive.files if key.endswith("_observations"))
        return len(observation_keys), sum(int(archive[key].shape[0]) for key in observation_keys)


def prediction_replay(auxiliary: AuxiliaryReplay, actor: torch.nn.Module, facts_path: Path,
                      *, save_arrays: Path | None = None) -> dict[str, Any]:
    squared_error = 0.0
    valid_count = 0
    outputs: dict[str, np.ndarray] = {}
    with np.load(facts_path, allow_pickle=False) as archive:
        indices = sorted({int(key.split("_")[1]) for key in archive.files if key.endswith("_observations")})
        per_episode = []
        for index in indices:
            observations = archive[f"episode_{index}_observations"][:, None, ...]
            skills = archive[f"episode_{index}_skills"][:, None, ...]
            dones = archive[f"episode_{index}_dones"][:, None]
            qos = archive[f"episode_{index}_qos"][:, None]
            predictions = auxiliary.predict(actor, observations, skills, dones)
            targets, valid = future_window_targets(qos, dones, window=auxiliary.window)
            pred_np = predictions.detach().cpu().numpy() if torch.is_tensor(predictions) else np.asarray(predictions)
            target_np = targets.detach().cpu().numpy() if torch.is_tensor(targets) else np.asarray(targets)
            valid_np = valid.detach().cpu().numpy().astype(bool) if torch.is_tensor(valid) else np.asarray(valid, dtype=bool)
            if pred_np.ndim == 3:
                valid_agents = np.broadcast_to(valid_np[..., None], pred_np.shape)
                target_agents = np.broadcast_to(target_np[..., None], pred_np.shape)
            else:
                valid_agents = valid_np
                target_agents = target_np
            error = pred_np[valid_agents] - target_agents[valid_agents]
            if error.size == 0 or not np.isfinite(error).all():
                raise FloatingPointError("common-fact episode has empty or non-finite prediction errors")
            squared_error += float(np.sum(error ** 2))
            valid_count += int(error.size)
            per_episode.append({"index": index, "valid": int(error.size), "mse": float(np.mean(error ** 2))})
            outputs[f"episode_{index}_predictions"] = pred_np
            outputs[f"episode_{index}_targets"] = target_np
            outputs[f"episode_{index}_valid"] = valid_np
    if valid_count == 0:
        raise RuntimeError("common-fact replay has no complete target windows")
    if save_arrays is not None:
        np.savez_compressed(save_arrays, **outputs)
    return {"mse": squared_error / valid_count, "valid_predictions": valid_count, "episodes": per_episode}


def _bootstrap_values(agent: HMASDAgent, states: np.ndarray, dones: np.ndarray) -> np.ndarray:
    values = np.zeros((len(states), agent.config.n_agents), dtype=np.float32)
    live = np.flatnonzero(~dones)
    if not len(live):
        return values
    with torch.no_grad():
        for env_index in live:
            state = agent._normalize_states(states[env_index], update=False)
            team_skill = int(agent.env_team_skills[env_index])
            hidden = agent.get_current_critic_hidden_np(env_index)
            for agent_index in range(agent.config.n_agents):
                value, _ = agent.skill_discoverer.get_value(
                    torch.as_tensor(state[None], dtype=torch.float32, device=agent.device),
                    torch.as_tensor([team_skill], dtype=torch.long, device=agent.device),
                    torch.as_tensor(hidden[agent_index:agent_index + 1], dtype=torch.float32, device=agent.device),
                )
                if agent.config.use_valuenorm and agent.value_norm_discoverer is not None:
                    value = agent._denormalize_values(value, agent.value_norm_discoverer)
                values[env_index, agent_index] = float(value.reshape(-1)[0].cpu())
    return values


def _finite_mapping(mapping: dict[str, Any]) -> bool:
    return all(
        np.isfinite(float(value))
        for value in mapping.values()
        if isinstance(value, (int, float, np.integer, np.floating))
    )


def _write_progress(out: Path, summary: dict[str, Any], event: dict[str, Any]) -> None:
    with (out / "progress.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=_json_default, sort_keys=True) + "\n")
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=_json_default), encoding="utf-8"
    )


def run_native(*, arm: str, out: Path, launch_sha: str, device_name: str = "cuda",
               threads: int = 4, facts: Path | None = None, facts_sha256: str | None = None,
               spec: NativeSpec | None = None) -> dict[str, Any]:
    spec = spec or NativeSpec(threads=threads)
    arm = arm.lower()
    if arm not in {"detach", "joint"}:
        raise ValueError("arm must be detach or joint")
    if arm == "joint" and (facts is None or facts_sha256 is None):
        raise ValueError("joint arm requires --facts and --facts-sha256")
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    torch.set_num_threads(int(threads))
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    out = Path(out)
    if out.exists() and any((out / name).exists() for name in ("summary.json", "config.json", "progress.jsonl")):
        raise FileExistsError(f"output already contains scientific files: {out}")
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "status": "INCOMPLETE", "failure": None,
        "arm": arm, "seed": spec.seed, "launch_sha": launch_sha,
        "device": str(device), "torch_threads": torch.get_num_threads(),
        "counts": {
            "transitions": 0, "rollouts": 0, "evaluations": 0, "episodes": 0,
            "evaluation_transitions": 0, "fact_episodes": 0, "fact_transitions": 0,
        },
    }
    envs: list[ParallelToArrayAdapter] = []
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    try:
        seed_everything(spec.seed, device)
        config = make_config(spec)
        (out / "config.json").write_text(json.dumps({"spec": asdict(spec), "active": active_config(config)}, indent=2), encoding="utf-8")
        agent = HMASDAgent(config, log_dir=str(out / "logs"), device=device)
        initial = _module_parameters(agent)
        initial_sha256 = initialization_fingerprint(agent)
        auxiliary = AuxiliaryReplay(
            agent.skill_discoverer.actor, arm, initialization_seed=spec.seed + spec.head_seed_offset,
            window=spec.window, chunk_length=50, head_lr=3e-4,
            representation_lr=3e-5, max_grad_norm=0.5,
        )
        facts_local = out / "facts.npz"
        if arm == "detach":
            digest = write_facts(
                agent, config, spec.fact_seeds, facts_local, device,
                policy_seed=spec.seed, log_dir=out / "fact_evaluator",
                initialization_sha256=initial_sha256,
            )
        else:
            assert facts is not None and facts_sha256 is not None
            digest = verify_and_copy_facts(
                Path(facts), facts_sha256, facts_local,
                expected_seeds=spec.fact_seeds, initialization_sha256=initial_sha256,
            )
        summary["facts_sha256"] = digest
        summary["initialization_sha256"] = initial_sha256
        fact_episodes, fact_transitions = facts_counts(facts_local)
        summary["counts"]["fact_episodes"] = fact_episodes
        summary["counts"]["fact_transitions"] = fact_transitions
        _write_progress(out, summary, {
            "event": "facts_ready", "facts_sha256": digest,
            "initialization_sha256": initial_sha256,
        })
        evaluations: dict[str, Any] = {}
        update_rows: list[dict[str, Any]] = []
        training_rollouts: list[dict[str, Any]] = []
        rss_curve: list[dict[str, Any]] = []
        summary["evaluations"] = evaluations
        summary["updates"] = update_rows
        summary["training_rollouts"] = training_rollouts
        summary["rss_curve"] = rss_curve
        initial_panel = evaluation_panel(
            agent, config, spec.eval_seeds, device,
            policy_seed=spec.seed, log_dir=out / "native_evaluator",
        )
        evaluations["0"] = {
            "native": initial_panel,
            "common_fact": prediction_replay(auxiliary, agent.skill_discoverer.actor, facts_local),
        }
        summary["counts"]["evaluations"] += len(spec.eval_seeds)
        summary["counts"]["evaluation_transitions"] += sum(
            int(world["actual_length"]) for world in initial_panel["worlds"]
        )
        _write_progress(out, summary, {
            "event": "evaluation", "rollout": 0,
            "evaluation_transitions": summary["counts"]["evaluation_transitions"],
        })
        envs = [make_env(config, spec.seed + lane) for lane in range(spec.lanes)]
        observations = []
        states = []
        for lane, env in enumerate(envs):
            obs, info = env.reset(seed=spec.seed + lane)
            observations.append(obs)
            states.append(info["state"])
        observations_arr = np.asarray(observations, dtype=np.float32)
        states_arr = np.asarray(states, dtype=np.float32)
        dones = np.ones(spec.lanes, dtype=bool)
        env_steps = np.zeros(spec.lanes, dtype=np.int64)
        straddling_boundaries = 0
        for rollout in range(1, spec.rollouts + 1):
            qos = np.empty((spec.rollout_length, spec.lanes), dtype=np.float32)
            rollout_reward_sum = np.zeros(spec.lanes, dtype=np.float64)
            rollout_metric_sums = {
                field: np.zeros(spec.lanes, dtype=np.float64) for field in METRIC_FIELDS
            }
            rollout_terminal_types = {"terminated": 0, "truncated": 0}
            for step in range(spec.rollout_length):
                current_obs = observations_arr.copy()
                current_states = states_arr.copy()
                actions, _, step_data = agent.step(
                    current_states, current_obs, env_steps, dones, deterministic=False,
                    return_step_data=True, build_infos=False,
                )
                next_obs_rows = []
                next_state_rows = []
                rewards = np.empty(spec.lanes, dtype=np.float32)
                next_dones = np.empty(spec.lanes, dtype=bool)
                infos = []
                terminal_observations = []
                terminal_states = []
                for lane, env in enumerate(envs):
                    next_obs, reward, terminated, truncated, info = env.step(actions[lane])
                    terminal_obs = np.asarray(next_obs, dtype=np.float32)
                    terminal_state = np.asarray(info["next_state"], dtype=np.float32)
                    done = bool(terminated or truncated)
                    rewards[lane] = float(reward)
                    if not np.isfinite(rewards[lane]):
                        raise FloatingPointError("non-finite native training reward")
                    next_dones[lane] = done
                    reward_info = info.get("reward_info", {})
                    missing = [field for field in METRIC_FIELDS if field not in reward_info]
                    if missing:
                        raise KeyError(f"Scenario 7 reward_info is missing required metrics: {missing}")
                    qos[step, lane] = float(reward_info["qos_satisfaction_ratio"])
                    rollout_reward_sum[lane] += rewards[lane]
                    for field in METRIC_FIELDS:
                        value = float(reward_info[field])
                        if not np.isfinite(value):
                            raise FloatingPointError(f"non-finite Scenario 7 metric {field}")
                        rollout_metric_sums[field][lane] += value
                    if terminated:
                        rollout_terminal_types["terminated"] += 1
                    if truncated:
                        rollout_terminal_types["truncated"] += 1
                    infos.append(info)
                    terminal_observations.append(terminal_obs)
                    terminal_states.append(terminal_state)
                terminal_observations_arr = np.asarray(terminal_observations, dtype=np.float32)
                terminal_states_arr = np.asarray(terminal_states, dtype=np.float32)
                agent.store_transition_batch(
                    current_states, terminal_states_arr, current_obs,
                    terminal_observations_arr, actions, rewards, next_dones,
                    infos_batch=infos, rollout_step_idx=step, step_data=step_data,
                )
                # Reset only after the terminal transition and its terminal next input are stored.
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        summary["counts"]["episodes"] += 1
                        agent.reset_env_state(lane)
                        next_obs, reset_info = env.reset(seed=None)
                        next_obs_rows.append(np.asarray(next_obs, dtype=np.float32))
                        next_state_rows.append(np.asarray(reset_info["state"], dtype=np.float32))
                        env_steps[lane] = 0
                    else:
                        next_obs_rows.append(terminal_observations_arr[lane])
                        next_state_rows.append(terminal_states_arr[lane])
                        env_steps[lane] += 1
                observations_arr = np.asarray(next_obs_rows, dtype=np.float32)
                states_arr = np.asarray(next_state_rows, dtype=np.float32)
                dones = next_dones
                summary["counts"]["transitions"] += spec.lanes
                if (step + 1) % 100 == 0 or step + 1 == spec.rollout_length:
                    _write_progress(out, summary, {
                        "event": "collection", "rollout": rollout, "step": step + 1,
                        "transitions": summary["counts"]["transitions"],
                        "wall_seconds": time.time() - started,
                    })
            rollout_data = agent.rollout_buffer._get_full_rollout_data()
            if rollout_data is None:
                raise RuntimeError("native rollout buffer is empty")
            aux_obs = np.asarray(rollout_data["obs"], dtype=np.float32).copy()
            aux_skills = np.asarray(rollout_data["agent_skills"], dtype=np.int64).copy()
            aux_dones = np.asarray(rollout_data["dones"], dtype=bool).any(axis=-1)
            aux_hidden = np.asarray(rollout_data["gru_hidden_states"][0], dtype=np.float32).copy()
            normalized = np.asarray(agent._normalize_observations(aux_obs, update=False), dtype=np.float32)
            last_values = _bootstrap_values(agent, states_arr, dones)
            native_update = agent.update(
                last_values=last_values, dones=dones, steps_in_buffer=spec.rollout_length,
                last_state=states_arr, last_observations=observations_arr,
            )
            if not _finite_mapping(native_update):
                raise FloatingPointError("native update returned a non-finite scalar")
            auxiliary_update = auxiliary.update(
                agent.skill_discoverer.actor, aux_obs, aux_skills, aux_dones, qos,
                initial_hidden=aux_hidden, normalized_observations=normalized,
            )
            aux_row = asdict(auxiliary_update) if hasattr(auxiliary_update, "__dataclass_fields__") else dict(auxiliary_update)
            if not _finite_mapping(aux_row):
                raise FloatingPointError("auxiliary update returned a non-finite scalar")
            update_rows.append({"rollout": rollout, "native": native_update, "auxiliary": aux_row})
            agent.clear_buffers()
            if rollout < spec.rollouts:
                straddling_boundaries += int(np.count_nonzero(~dones))
            summary["counts"]["rollouts"] = rollout
            training_rollouts.append({
                "rollout": rollout,
                "raw_native_J_by_lane": rollout_reward_sum.tolist(),
                "metric_sums_by_lane": {
                    field: values.tolist() for field, values in rollout_metric_sums.items()
                },
                "terminal_types": rollout_terminal_types,
            })
            rss_curve.append({"rollout": rollout, "rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss), "wall_seconds": time.time() - started})
            if rollout in EVAL_ROLLOUTS or rollout == spec.rollouts:
                endpoint_panel = evaluation_panel(
                    agent, config, spec.eval_seeds, device,
                    policy_seed=spec.seed, log_dir=out / "native_evaluator",
                )
                evaluations[str(rollout)] = {
                    "native": endpoint_panel,
                    "common_fact": prediction_replay(
                        auxiliary, agent.skill_discoverer.actor, facts_local,
                        save_arrays=out / "final_prediction_replay.npz" if rollout == spec.rollouts else None,
                    ),
                }
                summary["counts"]["evaluations"] += len(spec.eval_seeds)
                summary["counts"]["evaluation_transitions"] += sum(
                    int(world["actual_length"]) for world in endpoint_panel["worlds"]
                )
                _write_progress(out, summary, {
                    "event": "evaluation", "rollout": rollout,
                    "evaluation_transitions": summary["counts"]["evaluation_transitions"],
                })
            _write_progress(out, summary, {
                "event": "rollout_complete", "rollout": rollout,
                "transitions": summary["counts"]["transitions"],
                "wall_seconds": time.time() - started,
            })
            print(f"rollout={rollout}/{spec.rollouts} transitions={summary['counts']['transitions']}", flush=True)
        if summary["counts"]["transitions"] != spec.transitions:
            raise RuntimeError("transition count mismatch")
        steps = optimizer_steps(agent)
        if any(value <= 0 for value in steps.values()):
            raise RuntimeError(f"one or more native optimizers did not update: {steps}")
        displacement = parameter_displacement(initial, agent)
        if any(value <= 0.0 for value in displacement.values()):
            raise RuntimeError(f"one or more native modules did not move: {displacement}")
        checkpoint_dir = out / "checkpoint_final"
        checkpoint_dir.mkdir()
        agent.save_model(checkpoint_dir / "agent.pt")
        torch.save(auxiliary.checkpoint_state(), checkpoint_dir / "auxiliary.pt")
        summary.update({
            "status": "COMPLETE", "facts_sha256": digest, "evaluations": evaluations,
            "updates": update_rows, "optimizer_steps": steps,
            "training_rollouts": training_rollouts,
            "initialization_displacement_l2": displacement, "rss_curve": rss_curve,
            "wall_seconds": time.time() - started,
            "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "straddling_rollout_boundaries": straddling_boundaries,
        })
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        summary["wall_seconds"] = time.time() - started
        raise
    finally:
        for env in envs:
            try:
                env.close()
            except Exception:
                pass
        (out / "summary.json").write_text(json.dumps(summary, indent=2, default=_json_default), encoding="utf-8")


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot JSON encode {type(value).__name__}")
