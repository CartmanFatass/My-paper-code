"""Evaluate the registered R39A current-interface fixed-k HMASD anchor."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config_1 import Config
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from hmasd.baselines import apply_algorithm_config, create_agent


EXPERIMENT_ID = "EXP-20260715-r39a-current-fixed-hmasd-anchor"
RESULT_FILENAME = "r39a_fixed_hmasd_anchor.json"
COVERAGE_FILENAME = "r39a_step_coverage.csv"

TRAIN_SEED = 39_039
NUM_ENVS = 32
ROLLOUT_LENGTH = 500
EXPECTED_OUTER_UPDATES = 100
TOTAL_TIMESTEPS = 1_600_000
SKILL_INTERVAL = 10

EVAL_SEED_START = 139_039
EVAL_EPISODES = 100
EPISODE_STEPS = 500
POLICY_RNG_SEED = 239_039
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 40_039_039
HIGH_REPLAY_TOLERANCE = 1e-6

PASS_STATUS = "PASS_R39A_CURRENT_FIXED_HMASD_ANCHOR"
FAIL_STATUS = "VALID_FAIL_R39A_NO_CURRENT_HMASD_ANCHOR"
INVALID_STATUS = "INVALID_R39A_IMPLEMENTATION"

EXPECTED_POLICY_INTERFACE = {
    "action_dim": 4,
    "action_space_type": "continuous",
    "continuous_action_distribution": "tanh_gaussian",
    "scenario7_interface_version": 3,
    "scenario7_reward_model": "constrained_qos_safety_pbrs_v2",
    "scenario7_reward_variant": "qos_fixed_safety",
    "scenario7_experiment_arm": "C",
    "battery_capacity_wh": 160.0,
    "return_cost_cap": 1.0,
}

EXPECTED_CHECKPOINT_CONFIG = {
    "algorithm": "hmasd_original",
    "experiment_preset": "S7-S1",
    "energy_stage": "S1",
    "n_agents": 8,
    "action_dim": 4,
    "action_space_type": "continuous",
    "continuous_action_distribution": "tanh_gaussian",
    "scenario7_interface_version": 3,
    "scenario7_experiment_arm": "C",
    "scenario7_reward_variant": "qos_fixed_safety",
    "use_graph_pbrs": False,
    "n_Z": 6,
    "n_z": 6,
    "k": SKILL_INTERVAL,
    "coordinator_dropout": 0.0,
    "episode_length": EPISODE_STEPS,
    "rollout_length": ROLLOUT_LENGTH,
    "num_envs": NUM_ENVS,
    "total_timesteps": TOTAL_TIMESTEPS,
    "strict_hmasd_alignment": True,
    "use_horizon_window": False,
    "use_process_exploration": False,
    "use_opt": False,
    "use_team_bridge": False,
    "use_obsnorm": False,
    "use_statenorm": False,
    "lambda_e": 1.0,
    "lambda_D": 0.05,
    "lambda_d": 0.02,
    "lambda_h": 0.07,
    "lambda_l": 0.005,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "clip_epsilon": 0.20,
    "ppo_epochs": 15,
    "num_mini_batch": 4,
    "lr_coordinator": 1e-4,
    "lr_discoverer_actor": 1e-4,
    "lr_discoverer_critic": 1e-4,
    "lr_discriminator": 1e-4,
    "r39a_strict_contract": True,
    "audit_high_replay_likelihood": True,
}

SHAPING_FIELDS = (
    "w_first_contact",
    "w_energy_backhaul_potential",
    "w_energy_motion",
    "w_energy_efficiency",
    "w_low_battery",
    "w_depleted_battery",
    "w_charge_progress",
    "w_charging_queue",
    "w_station_approach",
    "w_charging_arrival",
    "w_energy_failure",
    "w_energy_failure_event",
)


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _write_result(output_dir: Path, result: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / RESULT_FILENAME
    with result_path.open("w", encoding="utf-8") as handle:
        json.dump(_json_value(result), handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    return result_path


def _add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def _equal(actual: Any, expected: Any) -> bool:
    if isinstance(expected, float):
        try:
            return math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=1e-12)
        except (TypeError, ValueError):
            return False
    return actual == expected


def _check_mapping(
    actual: Any,
    expected: dict[str, Any],
    *,
    prefix: str,
    failures: list[str],
) -> None:
    if not isinstance(actual, dict):
        _add_failure(failures, f"{prefix} is missing or is not an object")
        return
    for name, wanted in expected.items():
        value = actual.get(name)
        if not _equal(value, wanted):
            _add_failure(
                failures,
                f"{prefix}.{name}={value!r}, expected {wanted!r}",
            )


def _check_object_attributes(
    obj: Any,
    expected: dict[str, Any],
    *,
    prefix: str,
    failures: list[str],
) -> None:
    if obj is None:
        _add_failure(failures, f"{prefix} is missing")
        return
    for name, wanted in expected.items():
        value = getattr(obj, name, None)
        if not _equal(value, wanted):
            _add_failure(
                failures,
                f"{prefix}.{name}={value!r}, expected {wanted!r}",
            )


def _find_nonfinite(value: Any, path: str = "root") -> list[str]:
    failures: list[str] = []
    if isinstance(value, torch.Tensor):
        if (value.is_floating_point() or value.is_complex()) and not torch.isfinite(value).all():
            failures.append(path)
        return failures
    if isinstance(value, np.ndarray):
        if np.issubdtype(value.dtype, np.number) and not np.isfinite(value).all():
            failures.append(path)
        return failures
    if isinstance(value, (float, np.floating)):
        if not math.isfinite(float(value)):
            failures.append(path)
        return failures
    if isinstance(value, dict):
        for key, item in value.items():
            failures.extend(_find_nonfinite(item, f"{path}.{key}"))
        return failures
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            failures.extend(_find_nonfinite(item, f"{path}[{index}]"))
    return failures


def _validate_fixed_cli(args: argparse.Namespace, failures: list[str]) -> None:
    expected = {
        "eval_seed_start": EVAL_SEED_START,
        "eval_episodes": EVAL_EPISODES,
        "episode_steps": EPISODE_STEPS,
        "policy_rng_seed": POLICY_RNG_SEED,
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "device": "cuda",
    }
    for name, wanted in expected.items():
        value = getattr(args, name)
        if value != wanted:
            _add_failure(failures, f"CLI {name}={value!r}, expected {wanted!r}")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _load_checkpoint(path: Path, device: torch.device) -> dict[str, Any]:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    if not isinstance(checkpoint, dict):
        raise ValueError("checkpoint root must be a dictionary")
    return checkpoint


def _build_evaluation_runtime(output_dir: Path, device: torch.device):
    config = Config(preset="S7-S1")
    config.apply_scenario7_experiment_arm("C")
    config.apply_scenario7_reward_variant("qos_fixed_safety")
    config.scenario7_comparison_gate_enabled = False
    config.strict_hmasd_alignment = True
    config.r39a_strict_contract = True
    config.audit_high_replay_likelihood = True
    config.num_envs = 1
    config.rollout_length = ROLLOUT_LENGTH
    config.total_timesteps = TOTAL_TIMESTEPS
    apply_algorithm_config(config, "hmasd_original")

    raw_env = UAVEnergyAwareRelayEnv(
        config=config,
        render_mode=None,
        seed=EVAL_SEED_START,
        scale_mode="eval",
    )
    env = ParallelToArrayAdapter(raw_env, seed=EVAL_SEED_START)
    config.update_env_dims(env.state_dim, env.obs_dim, n_agents=env.n_uavs)
    config.action_dim = int(env.action_dim)
    agent = create_agent(
        config,
        "hmasd_original",
        log_dir=str(output_dir),
        device=device,
    )
    return config, env, agent


def _validate_state_dict(
    name: str,
    saved: Any,
    expected: dict[str, torch.Tensor],
    failures: list[str],
) -> None:
    if not isinstance(saved, dict):
        _add_failure(failures, f"checkpoint.{name} is missing")
        return
    saved_keys = set(saved)
    expected_keys = set(expected)
    if saved_keys != expected_keys:
        missing = sorted(expected_keys - saved_keys)
        unexpected = sorted(saved_keys - expected_keys)
        _add_failure(
            failures,
            f"checkpoint.{name} state keys differ: missing={missing}, unexpected={unexpected}",
        )
        return
    for key, expected_tensor in expected.items():
        saved_tensor = saved[key]
        if not isinstance(saved_tensor, torch.Tensor):
            _add_failure(failures, f"checkpoint.{name}.{key} is not a tensor")
        elif tuple(saved_tensor.shape) != tuple(expected_tensor.shape):
            _add_failure(
                failures,
                f"checkpoint.{name}.{key} shape={tuple(saved_tensor.shape)}, "
                f"expected {tuple(expected_tensor.shape)}",
            )


def _validate_optimizer(name: str, value: Any, failures: list[str]) -> None:
    if not isinstance(value, dict):
        _add_failure(failures, f"checkpoint.{name} is missing")
        return
    if not isinstance(value.get("param_groups"), list) or not value["param_groups"]:
        _add_failure(failures, f"checkpoint.{name}.param_groups is empty")
    if not isinstance(value.get("state"), dict) or not value["state"]:
        _add_failure(failures, f"checkpoint.{name}.state is empty")


def _validate_checkpoint_and_summary(
    checkpoint: dict[str, Any],
    summary: dict[str, Any],
    checkpoint_path: Path,
    agent: Any,
    env: ParallelToArrayAdapter,
    failures: list[str],
) -> dict[str, Any]:
    required_checkpoint_keys = {
        "skill_coordinator",
        "skill_discoverer",
        "team_discriminator",
        "individual_discriminator",
        "coordinator_optimizer",
        "discoverer_actor_optimizer",
        "discoverer_critic_optimizer",
        "discriminator_optimizer",
        "config",
        "policy_interface",
        "training_interface",
        "training_diagnostics",
        "scenario7_safety_dual_state",
        "valuenorm_state",
    }
    missing_checkpoint_keys = sorted(required_checkpoint_keys - set(checkpoint))
    if missing_checkpoint_keys:
        _add_failure(
            failures,
            f"checkpoint missing required keys: {missing_checkpoint_keys}",
        )

    checkpoint_config = checkpoint.get("config")
    _check_object_attributes(
        checkpoint_config,
        EXPECTED_CHECKPOINT_CONFIG,
        prefix="checkpoint.config",
        failures=failures,
    )
    for name in (
        "disable_high_level_training",
        "disable_discriminator_training",
        "disable_discriminator_rewards",
    ):
        if bool(getattr(checkpoint_config, name, False)):
            _add_failure(failures, f"checkpoint.config.{name} must be false")
    for name in SHAPING_FIELDS:
        if not _equal(getattr(checkpoint_config, name, None), 0.0):
            _add_failure(
                failures,
                f"checkpoint.config.{name}={getattr(checkpoint_config, name, None)!r}, expected 0.0",
            )

    _check_mapping(
        checkpoint.get("policy_interface"),
        EXPECTED_POLICY_INTERFACE,
        prefix="checkpoint.policy_interface",
        failures=failures,
    )
    _check_mapping(
        checkpoint.get("training_interface"),
        {
            "skill_interval": SKILL_INTERVAL,
            "rollout_length": ROLLOUT_LENGTH,
            "episode_length": EPISODE_STEPS,
        },
        prefix="checkpoint.training_interface",
        failures=failures,
    )

    if getattr(checkpoint_config, "state_dim", None) != env.state_dim:
        _add_failure(
            failures,
            f"checkpoint.config.state_dim={getattr(checkpoint_config, 'state_dim', None)!r}, "
            f"current environment state_dim={env.state_dim}",
        )
    if getattr(checkpoint_config, "obs_dim", None) != env.obs_dim:
        _add_failure(
            failures,
            f"checkpoint.config.obs_dim={getattr(checkpoint_config, 'obs_dim', None)!r}, "
            f"current environment obs_dim={env.obs_dim}",
        )

    native_modules = {
        "skill_coordinator": agent.skill_coordinator,
        "skill_discoverer": agent.skill_discoverer,
        "team_discriminator": agent.team_discriminator,
        "individual_discriminator": agent.individual_discriminator,
    }
    for name, module in native_modules.items():
        if module is None:
            _add_failure(failures, f"current native module {name} is absent")
            continue
        _validate_state_dict(name, checkpoint.get(name), module.state_dict(), failures)

    for name in (
        "coordinator_optimizer",
        "discoverer_actor_optimizer",
        "discoverer_critic_optimizer",
        "discriminator_optimizer",
    ):
        _validate_optimizer(name, checkpoint.get(name), failures)

    for name in (
        "ha_ctse_editor",
        "low_level_compact_extractor",
        "process_encoder",
        "process_outcome_predictor",
        "process_contrastive_head",
        "process_optimizer",
    ):
        if checkpoint.get(name) is not None:
            _add_failure(failures, f"checkpoint.{name} must be absent for native fixed-k HMASD")
    if checkpoint.get("scenario7_safety_dual_state") != {}:
        _add_failure(
            failures,
            "checkpoint.scenario7_safety_dual_state must be empty for fixed-safety R39A",
        )

    valuenorm = checkpoint.get("valuenorm_state")
    if not isinstance(valuenorm, dict):
        _add_failure(failures, "checkpoint.valuenorm_state is missing")
    else:
        for name in ("coordinator", "discoverer"):
            state = valuenorm.get(name)
            if not isinstance(state, dict):
                _add_failure(failures, f"checkpoint.valuenorm_state.{name} is missing")
                continue
            for field in ("mean", "var", "count"):
                if field not in state:
                    _add_failure(
                        failures,
                        f"checkpoint.valuenorm_state.{name}.{field} is missing",
                    )

    diagnostics = checkpoint.get("training_diagnostics")
    replay = diagnostics.get("high_replay_likelihood") if isinstance(diagnostics, dict) else None
    if not isinstance(replay, dict):
        _add_failure(failures, "checkpoint training high-replay audit is missing")
        replay = {}
    train_replay_max = replay.get("global_max_abs_error", float("inf"))
    try:
        train_replay_max = float(train_replay_max)
    except (TypeError, ValueError):
        train_replay_max = float("inf")
    if not math.isfinite(train_replay_max) or train_replay_max > HIGH_REPLAY_TOLERANCE:
        _add_failure(
            failures,
            f"training high replay max error={train_replay_max!r}, expected <= {HIGH_REPLAY_TOLERANCE}",
        )
    expected_high_samples = EXPECTED_OUTER_UPDATES * NUM_ENVS * (ROLLOUT_LENGTH // SKILL_INTERVAL)
    if not isinstance(replay.get("global_sample_count"), int) or replay.get("global_sample_count") <= 0:
        _add_failure(
            failures,
            f"training high replay sample count={replay.get('global_sample_count')!r}, expected > 0",
        )

    expected_summary = {
        "contract_total_steps": TOTAL_TIMESTEPS,
        "outer_updates": EXPECTED_OUTER_UPDATES,
        "successful_outer_updates": EXPECTED_OUTER_UPDATES,
        "failed_outer_updates": 0,
        "r39a_strict_contract": True,
    }
    _check_mapping(
        summary,
        expected_summary,
        prefix="training_summary",
        failures=failures,
    )
    if "total_steps" in summary and summary.get("total_steps") != TOTAL_TIMESTEPS:
        _add_failure(
            failures,
            f"training_summary.total_steps={summary.get('total_steps')!r}, expected {TOTAL_TIMESTEPS}",
        )
    _check_mapping(
        summary.get("r39a_contract"),
        {
            "seed": TRAIN_SEED,
            "preset": "S7-S1",
            "n_agents": 8,
            "action_dim": 4,
            "scenario7_interface_version": 3,
            "scenario7_experiment_arm": "C",
            "scenario7_reward_variant": "qos_fixed_safety",
            "use_graph_pbrs": False,
            "num_envs": NUM_ENVS,
            "rollout_length": ROLLOUT_LENGTH,
            "skill_interval": SKILL_INTERVAL,
            "total_timesteps": TOTAL_TIMESTEPS,
        },
        prefix="training_summary.r39a_contract",
        failures=failures,
    )
    summary_algorithm = str((summary.get("r39a_contract") or {}).get("algorithm", ""))
    if summary_algorithm != "hmasd_original":
        _add_failure(
            failures,
            f"training_summary.r39a_contract.algorithm={summary_algorithm!r}, expected 'hmasd_original'",
        )
    final_checkpoint_path = summary.get("final_checkpoint_path")
    if not final_checkpoint_path:
        _add_failure(failures, "training_summary.final_checkpoint_path is missing")
    elif Path(final_checkpoint_path).resolve() != checkpoint_path.resolve():
        _add_failure(
            failures,
            f"training summary points to {final_checkpoint_path!r}, not {str(checkpoint_path)!r}",
        )
    stability = summary.get("numerical_stability")
    if not isinstance(stability, dict):
        _add_failure(failures, "training_summary.numerical_stability is missing")
    elif int(stability.get("total_repairs", -1)) != 0:
        _add_failure(
            failures,
            f"training numerical repairs={stability.get('total_repairs')!r}, expected 0",
        )

    nonfinite_checkpoint = _find_nonfinite(
        {key: value for key, value in checkpoint.items() if key != "config"},
        "checkpoint",
    )
    if nonfinite_checkpoint:
        _add_failure(
            failures,
            f"checkpoint contains non-finite values at {nonfinite_checkpoint[:10]}",
        )
    nonfinite_summary = _find_nonfinite(summary, "training_summary")
    if nonfinite_summary:
        _add_failure(
            failures,
            f"training summary contains non-finite values at {nonfinite_summary[:10]}",
        )

    return {
        "training_high_replay": _json_value(replay),
        "expected_training_high_replay_samples": expected_high_samples,
        "checkpoint_native_modules": sorted(native_modules),
        "checkpoint_optimizer_states": [
            "coordinator_optimizer",
            "discoverer_actor_optimizer",
            "discoverer_critic_optimizer",
            "discriminator_optimizer",
        ],
    }


def _seed_policy_rng(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _immediate_high_replay(
    agent: Any,
    state: np.ndarray,
    observations: np.ndarray,
    info: dict[str, Any],
) -> tuple[float, float, bool]:
    log_probs = info.get("log_probs")
    if not isinstance(log_probs, dict):
        return float("inf"), float("inf"), False
    state_normalized = agent._normalize_states(np.asarray(state)[None, :], update=False)
    obs_normalized = agent._normalize_observations(
        np.asarray(observations)[None, :, :], update=False
    )
    state_tensor = torch.as_tensor(state_normalized, dtype=torch.float32, device=agent.device)
    obs_tensor = torch.as_tensor(obs_normalized, dtype=torch.float32, device=agent.device)
    team_skill = torch.as_tensor(
        [int(info["team_skill"])], dtype=torch.long, device=agent.device
    )
    agent_skills = torch.as_tensor(
        np.asarray(info["agent_skills"], dtype=np.int64)[None, :],
        dtype=torch.long,
        device=agent.device,
    )
    replay = agent.skill_coordinator.evaluate_training_batch(
        state_tensor,
        obs_tensor,
        team_skill,
        agent_skills,
    )
    old_team = torch.as_tensor(
        [float(log_probs["team_log_prob"])], dtype=torch.float32, device=agent.device
    )
    old_agents = torch.as_tensor(
        np.asarray(log_probs["agent_log_probs"], dtype=np.float32)[None, :],
        dtype=torch.float32,
        device=agent.device,
    )
    team_error = float(torch.abs(replay["team_log_probs"] - old_team).max().item())
    agent_error = float(torch.abs(replay["agent_log_probs"] - old_agents).max().item())
    values_finite = bool(
        torch.isfinite(replay["state_values"]).all()
        and torch.isfinite(replay["agent_values"]).all()
    )
    return team_error, agent_error, values_finite


def _run_evaluation(
    args: argparse.Namespace,
    env: ParallelToArrayAdapter,
    agent: Any,
    coverage_path: Path,
    failures: list[str],
) -> tuple[np.ndarray, dict[str, Any]]:
    coverage = np.full((EVAL_EPISODES, EPISODE_STEPS), np.nan, dtype=np.float64)
    max_team_error = 0.0
    max_agent_error = 0.0
    replay_checks = 0
    finite_actions = True
    finite_values = True
    finite_states = True

    _seed_policy_rng(args.policy_rng_seed)
    agent.eval()

    with coverage_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("episode", "reset_seed", "step", "coverage_ratio"),
        )
        writer.writeheader()

        with torch.no_grad():
            for episode_index in range(EVAL_EPISODES):
                reset_seed = args.eval_seed_start + episode_index
                agent.reset_env_state(0)
                observations, reset_info = env.reset(seed=reset_seed)
                state = np.asarray(reset_info.get("state"), dtype=np.float32)
                observations = np.asarray(observations, dtype=np.float32)
                if state.shape != (agent.config.state_dim,):
                    raise ValueError(
                        f"episode {episode_index + 1} reset state shape={state.shape}, "
                        f"expected {(agent.config.state_dim,)}"
                    )
                if observations.shape != (
                    agent.config.n_agents,
                    agent.config.obs_dim,
                ):
                    raise ValueError(
                        f"episode {episode_index + 1} reset observations shape={observations.shape}, "
                        f"expected {(agent.config.n_agents, agent.config.obs_dim)}"
                    )

                for step_index in range(EPISODE_STEPS):
                    finite_states = finite_states and bool(
                        np.all(np.isfinite(state)) and np.all(np.isfinite(observations))
                    )
                    actions, infos = agent.step(
                        state[None, :],
                        observations[None, :, :],
                        np.asarray([step_index], dtype=np.int64),
                        np.asarray([False], dtype=np.bool_),
                        deterministic=False,
                    )
                    if not isinstance(infos, list) or len(infos) != 1:
                        raise ValueError("agent.step did not return one evaluation info row")
                    info = infos[0]
                    action = np.asarray(actions[0], dtype=np.float32)
                    finite_actions = finite_actions and bool(
                        np.all(np.isfinite(action)) and np.all(np.abs(action) <= 1.000001)
                    )
                    finite_values = finite_values and bool(
                        np.all(np.isfinite(np.asarray(info.get("values"))))
                        and np.all(np.isfinite(np.asarray(info.get("action_logprobs"))))
                        and np.all(
                            np.isfinite(
                                np.asarray((info.get("log_probs") or {}).get("state_value"))
                            )
                        )
                        and np.all(
                            np.isfinite(
                                np.asarray((info.get("log_probs") or {}).get("agent_values"))
                            )
                        )
                    )

                    if step_index % SKILL_INTERVAL == 0:
                        if not bool(info.get("skill_changed")):
                            raise ValueError(
                                f"episode {episode_index + 1} step {step_index}: "
                                "native fixed-k high decision was not marked"
                            )
                        team_error, agent_error, replay_values_finite = _immediate_high_replay(
                            agent, state, observations, info
                        )
                        max_team_error = max(max_team_error, team_error)
                        max_agent_error = max(max_agent_error, agent_error)
                        finite_values = finite_values and replay_values_finite
                        replay_checks += 1

                    next_observations, _reward, terminated, truncated, step_info = env.step(action)
                    next_state = np.asarray(step_info.get("next_state"), dtype=np.float32)
                    next_observations = np.asarray(next_observations, dtype=np.float32)
                    reward_info = step_info.get("reward_info")
                    if not isinstance(reward_info, dict) or "coverage_ratio" not in reward_info:
                        raise ValueError(
                            f"episode {episode_index + 1} step {step_index + 1}: "
                            "reward_info.coverage_ratio is missing"
                        )
                    coverage_value = float(reward_info["coverage_ratio"])
                    if not math.isfinite(coverage_value) or not (-1e-8 <= coverage_value <= 1.0 + 1e-8):
                        raise ValueError(
                            f"episode {episode_index + 1} step {step_index + 1}: "
                            f"coverage_ratio={coverage_value!r} is outside [0, 1]"
                        )
                    coverage_value = float(np.clip(coverage_value, 0.0, 1.0))
                    coverage[episode_index, step_index] = coverage_value
                    writer.writerow(
                        {
                            "episode": episode_index + 1,
                            "reset_seed": reset_seed,
                            "step": step_index + 1,
                            "coverage_ratio": f"{coverage_value:.10g}",
                        }
                    )

                    if (terminated or truncated) and step_index != EPISODE_STEPS - 1:
                        raise ValueError(
                            f"episode {episode_index + 1} ended early at step {step_index + 1}"
                        )
                    if step_index == EPISODE_STEPS - 1 and not (terminated or truncated):
                        raise ValueError(
                            f"episode {episode_index + 1} did not close at {EPISODE_STEPS} steps"
                        )
                    state = next_state
                    observations = next_observations

    expected_replay_checks = EVAL_EPISODES * (EPISODE_STEPS // SKILL_INTERVAL)
    if replay_checks != expected_replay_checks:
        _add_failure(
            failures,
            f"evaluation high replay checks={replay_checks}, expected {expected_replay_checks}",
        )
    eval_replay_max = max(max_team_error, max_agent_error)
    if not math.isfinite(eval_replay_max) or eval_replay_max > HIGH_REPLAY_TOLERANCE:
        _add_failure(
            failures,
            f"evaluation high replay max error={eval_replay_max!r}, "
            f"expected <= {HIGH_REPLAY_TOLERANCE}",
        )
    if not finite_actions:
        _add_failure(failures, "evaluation actions are non-finite or outside [-1, 1]")
    if not finite_values:
        _add_failure(failures, "evaluation values or log probabilities are non-finite")
    if not finite_states:
        _add_failure(failures, "evaluation states or observations are non-finite")
    if not np.all(np.isfinite(coverage)):
        _add_failure(failures, "evaluation coverage table is incomplete or non-finite")

    return coverage, {
        "episodes": EVAL_EPISODES,
        "episode_steps": EPISODE_STEPS,
        "step_rows": int(coverage.size),
        "reset_seed_start": EVAL_SEED_START,
        "reset_seed_end": EVAL_SEED_START + EVAL_EPISODES - 1,
        "policy_rng_seed": POLICY_RNG_SEED,
        "high_replay_checks": replay_checks,
        "high_replay_team_max_abs_error": max_team_error,
        "high_replay_agent_max_abs_error": max_agent_error,
        "high_replay_max_abs_error": eval_replay_max,
        "actions_finite_and_bounded": finite_actions,
        "values_and_log_probs_finite": finite_values,
        "states_and_observations_finite": finite_states,
    }


def _bootstrap_interval(values: np.ndarray, draws: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    if values.shape != (EVAL_EPISODES,) or not np.all(np.isfinite(values)):
        raise ValueError("R39A bootstrap requires exactly 100 finite episode values")
    sampled = values[draws].mean(axis=1)
    return {
        "estimate": float(values.mean()),
        "lower": float(np.quantile(sampled, 0.025)),
        "upper": float(np.quantile(sampled, 0.975)),
    }


def _compute_m1(coverage: np.ndarray) -> dict[str, Any]:
    if coverage.shape != (EVAL_EPISODES, EPISODE_STEPS):
        raise ValueError(
            f"coverage shape={coverage.shape}, expected {(EVAL_EPISODES, EPISODE_STEPS)}"
        )
    episode_mean = coverage.mean(axis=1)
    episode_full_fraction = (coverage >= 1.0 - 1e-6).mean(axis=1)
    episode_zero = (coverage.max(axis=1) <= 1e-6).astype(np.float64)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = rng.integers(
        0,
        EVAL_EPISODES,
        size=(BOOTSTRAP_REPETITIONS, EVAL_EPISODES),
    )
    metrics = {
        "C_mean": _bootstrap_interval(episode_mean, draws),
        "C_full": _bootstrap_interval(episode_full_fraction, draws),
        "F_zero": _bootstrap_interval(episode_zero, draws),
    }
    checks = {
        "C_mean_lower_at_least_0_90": metrics["C_mean"]["lower"] >= 0.90,
        "C_full_lower_at_least_0_50": metrics["C_full"]["lower"] >= 0.50,
        "F_zero_upper_at_most_0_10": metrics["F_zero"]["upper"] <= 0.10,
    }
    return {
        "pass": bool(all(checks.values())),
        "checks": checks,
        "metrics": metrics,
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "resampling_unit": "whole_episode",
        "thresholds": {
            "C_mean_95pct_lower": 0.90,
            "C_full_95pct_lower": 0.50,
            "F_zero_95pct_upper": 0.10,
        },
    }


def _base_result(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir).resolve()
    return {
        "experiment_id": EXPERIMENT_ID,
        "status": INVALID_STATUS,
        "implementation_valid": False,
        "contract": {
            "train_seed": TRAIN_SEED,
            "num_envs": NUM_ENVS,
            "rollout_length": ROLLOUT_LENGTH,
            "outer_updates": EXPECTED_OUTER_UPDATES,
            "total_env_steps": TOTAL_TIMESTEPS,
            "eval_episodes": EVAL_EPISODES,
            "episode_steps": EPISODE_STEPS,
            "reset_seeds": [EVAL_SEED_START, EVAL_SEED_START + EVAL_EPISODES - 1],
            "policy_rng_seed": POLICY_RNG_SEED,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "artifacts": {
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "training_summary": str(Path(args.training_summary).resolve()),
            "step_coverage_csv": str(output_dir / COVERAGE_FILENAME),
            "result_json": str(output_dir / RESULT_FILENAME),
        },
        "m0": {"pass": False, "failures": []},
        "m1": None,
        "next_action": (
            "fix only the concrete current-HMASD wiring defect and rerun the identical Stage A contract"
        ),
    }


def analyze(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    result = _base_result(args)
    failures: list[str] = result["m0"]["failures"]
    env = None

    try:
        _validate_fixed_cli(args, failures)
        checkpoint_path = Path(args.checkpoint).resolve()
        summary_path = Path(args.training_summary).resolve()
        if not checkpoint_path.is_file():
            _add_failure(failures, f"checkpoint does not exist: {checkpoint_path}")
        if not summary_path.is_file():
            _add_failure(failures, f"training summary does not exist: {summary_path}")
        if failures:
            _write_result(output_dir, result)
            return 0

        if args.device != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("R39A final evaluation requires an available CUDA device")
        device = torch.device("cuda")
        summary = _load_json(summary_path)
        checkpoint = _load_checkpoint(checkpoint_path, device)
        _config, env, agent = _build_evaluation_runtime(output_dir, device)
        checkpoint_evidence = _validate_checkpoint_and_summary(
            checkpoint,
            summary,
            checkpoint_path,
            agent,
            env,
            failures,
        )
        result["m0"].update(checkpoint_evidence)
        if failures:
            _write_result(output_dir, result)
            return 0

        agent.load_model(str(checkpoint_path))
        coverage, evaluation_evidence = _run_evaluation(
            args,
            env,
            agent,
            output_dir / COVERAGE_FILENAME,
            failures,
        )
        result["m0"]["evaluation"] = evaluation_evidence
        if failures:
            _write_result(output_dir, result)
            return 0

        result["m0"]["pass"] = True
        result["implementation_valid"] = True
        result["m1"] = _compute_m1(coverage)
        if result["m1"]["pass"]:
            result["status"] = PASS_STATUS
            result["next_action"] = (
                "freeze this exact checkpoint and manifest, then authorize Stage B registration"
            )
        else:
            result["status"] = FAIL_STATUS
            result["next_action"] = (
                "stop the R39 temporal treatment and archive the current-interface fixed-HMASD/S7 substrate failure"
            )
        _write_result(output_dir, result)
        return 0
    except Exception as exc:
        _add_failure(failures, f"{type(exc).__name__}: {exc}")
        result["m0"]["pass"] = False
        result["implementation_valid"] = False
        result["status"] = INVALID_STATUS
        _write_result(output_dir, result)
        return 0
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:
                pass


def validate_result(args: argparse.Namespace) -> int:
    result_path = Path(args.output_dir).resolve() / RESULT_FILENAME
    if not result_path.is_file():
        print(f"missing result: {result_path}", file=sys.stderr)
        return 2
    try:
        result = _load_json(result_path)
    except Exception as exc:
        print(f"invalid result JSON: {exc}", file=sys.stderr)
        return 2
    status = result.get("status")
    implementation_valid = result.get("implementation_valid")
    if status == INVALID_STATUS:
        print(status)
        return 1
    if status not in {PASS_STATUS, FAIL_STATUS}:
        print(f"unknown R39A status: {status!r}", file=sys.stderr)
        return 2
    if implementation_valid is not True:
        print(
            f"scientific status {status} requires implementation_valid=true",
            file=sys.stderr,
        )
        return 2
    print(status)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="run the exact R39A final gate")
    analyze_parser.add_argument("--checkpoint", required=True)
    analyze_parser.add_argument("--training-summary", required=True)
    analyze_parser.add_argument("--output-dir", required=True)
    analyze_parser.add_argument("--device", default="cuda")
    analyze_parser.add_argument("--eval-seed-start", type=int, default=EVAL_SEED_START)
    analyze_parser.add_argument("--eval-episodes", type=int, default=EVAL_EPISODES)
    analyze_parser.add_argument("--episode-steps", type=int, default=EPISODE_STEPS)
    analyze_parser.add_argument("--policy-rng-seed", type=int, default=POLICY_RNG_SEED)
    analyze_parser.add_argument(
        "--bootstrap-repetitions", type=int, default=BOOTSTRAP_REPETITIONS
    )
    analyze_parser.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED)
    analyze_parser.set_defaults(handler=analyze)

    validate_parser = subparsers.add_parser(
        "validate-result",
        help="return nonzero only for invalid or malformed R39A results",
    )
    validate_parser.add_argument("--output-dir", required=True)
    validate_parser.set_defaults(handler=validate_result)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
