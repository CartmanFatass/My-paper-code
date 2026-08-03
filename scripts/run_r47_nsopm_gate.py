"""Collect the registered reward-off R47-NSOPM-G0 evidence."""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from ha_ctse_process import checkpoint_io  # noqa: E402
from ha_ctse_process.standalone_cli import create_agent, create_env  # noqa: E402
from ha_ctse_process.config_alice_bob_asymmetric import Config  # noqa: E402
from r47_nsopm import (  # noqa: E402
    BRANCH_SEED,
    CAUSAL_CONTEXTS,
    EPISODE_STEPS,
    EXPERIMENT_ID,
    FORCED_BRANCHES,
    FORCED_HORIZON,
    FORCED_STEPS,
    K0,
    NATURAL_GROUPS,
    NATURAL_SEED,
    NATURAL_WINDOWS,
    NATURAL_WINDOWS_PER_GROUP,
    N_AGENTS,
    N_SKILLS,
    REPLICAS,
    SCHEMA_VERSION,
    SOURCE_CHECKPOINT,
    SOURCE_TOTAL_STEPS,
    SOURCE_UPDATE,
    VIEW_DIM,
    WORLD_SIZE,
    json_ready,
    seven_dimensional_process_view,
)


@dataclass
class ForcedContext:
    context_id: int
    reset_group: int
    focal_agent: int
    check_index: int
    observations: np.ndarray
    state: np.ndarray
    environment_snapshot: dict[str, object]
    adapter_rng_state: dict[str, Any]
    active_skills: np.ndarray
    active_mask: np.ndarray
    skill_ages: np.ndarray
    team_code: int
    steps_to_check: int
    episode_step: int
    episode_id: int
    actor_hxs: np.ndarray
    critic_hxs: np.ndarray
    python_rng_state: object
    numpy_rng_state: tuple[Any, ...]
    torch_cpu_rng_state: torch.Tensor
    torch_cuda_rng_states: list[torch.Tensor]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_progress(path: Path, phase: str, **values: Any) -> None:
    write_json(path, {"phase": phase, **values})


def set_all_seeds(seed: int, device: torch.device) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed) % (2**32 - 1))
    torch.manual_seed(int(seed))
    if device.type == "cuda":
        torch.cuda.manual_seed_all(int(seed))


def checkpoint_manifest(path: Path) -> dict[str, Any]:
    return checkpoint_io._load_adjacent_run_manifest(path)


def validate_source(
    config: Config,
    metadata: dict[str, Any],
    manifest: dict[str, Any],
    total_steps: int,
    update_index: int,
) -> dict[str, bool]:
    contract = metadata.get("r30_contract") or {}
    algorithm = manifest.get("algorithm_config") if isinstance(manifest, dict) else None
    checks = {
        "checkpoint_total_steps": int(total_steps) == SOURCE_TOTAL_STEPS,
        "checkpoint_update": int(update_index) == SOURCE_UPDATE,
        "scenario": str(metadata.get("scenario")) == "alice_bob_asymmetric_cycles",
        "high_controller": str(metadata.get("high_controller")) == "r30_fixed_clock_ar_edit",
        "n_agents": int(metadata.get("n_agents") or 0) == N_AGENTS,
        "n_skills": int(metadata.get("n_skills") or 0) == N_SKILLS,
        "k0": int(contract.get("k0") or metadata.get("skill_interval") or 0) == K0,
        "episode_length": int(config.episode_length) == EPISODE_STEPS,
        "observation_dimension": int(config.obs_dim) == 12,
        "state_dimension": int(config.state_dim) == 19,
        "action_dimension": int(config.action_dim) == 2,
        "continuous_action": str(metadata.get("action_space_type")) == "continuous",
        "recurrent_low": bool(metadata.get("use_recurrent_low_level")),
        "low_actor_team_code_absent": not bool(
            metadata.get("low_actor_condition_on_team_code")
        ),
        "adaptive_r30_source": bool(
            isinstance(algorithm, dict)
            and not bool(algorithm.get("r30_force_refresh_every_check", True))
        ),
        "r31_reward_off": str(getattr(config, "r31_effect_mode", "off")) != "real_reward",
        "transition_reward_off": float(
            getattr(config, "transition_skill_reward_coef", 0.0)
        )
        == 0.0,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"R47 source contract mismatch: {failed}")
    return checks


def set_eval_and_freeze(agent: Any) -> None:
    seen: set[int] = set()
    for value in vars(agent).values():
        if id(value) in seen or not isinstance(value, torch.nn.Module):
            continue
        seen.add(id(value))
        value.eval()
        value.requires_grad_(False)


def module_state(agent: Any) -> dict[str, torch.Tensor]:
    snapshot: dict[str, torch.Tensor] = {}
    seen: set[int] = set()
    for attribute in sorted(vars(agent)):
        module = getattr(agent, attribute)
        if not isinstance(module, torch.nn.Module) or id(module) in seen:
            continue
        seen.add(id(module))
        for name, value in module.state_dict().items():
            snapshot[f"{attribute}.{name}"] = value.detach().cpu().clone()
    return snapshot


def module_drift(
    before: dict[str, torch.Tensor], after: dict[str, torch.Tensor]
) -> dict[str, Any]:
    if tuple(before) != tuple(after):
        return {"inventory_equal": False, "max_abs": float("inf"), "all_exact": False}
    maximum = 0.0
    exact = True
    for name in before:
        left = before[name]
        right = after[name]
        if left.shape != right.shape or left.dtype != right.dtype:
            return {"inventory_equal": False, "max_abs": float("inf"), "all_exact": False}
        if not torch.equal(left, right):
            exact = False
            if left.numel():
                maximum = max(maximum, float((left - right).abs().max().item()))
    return {"inventory_equal": True, "max_abs": maximum, "all_exact": exact}


def make_source(checkpoint: Path, device_name: str):
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    if device_name != "cuda":
        raise RuntimeError("R47 formal and focused dry runs require CUDA")
    if not torch.cuda.is_available():
        raise RuntimeError("R47 requested CUDA but CUDA is unavailable")
    device = torch.device("cuda")
    config = Config()
    config.scenario = "alice_bob_asymmetric_cycles"
    config.skill_interval = K0
    config.r31_effect_mode = "off"
    metadata = checkpoint_io.load_checkpoint_metadata(checkpoint)
    checkpoint_io.apply_checkpoint_structure(
        config,
        argparse.Namespace(high_controller="", n_agents=0),
        metadata,
    )
    # ``configure_r30_mode`` normally applies these reward-pure construction
    # values before agent creation.  This standalone loader does not traverse
    # the training CLI, so reproduce only those source-construction constants;
    # no behavior parameter or checkpoint tensor is changed.
    config.edit_penalty_alpha = 0.0
    config.switch_penalty_beta = 0.0
    config.duration_entropy_floor_enabled = False
    environment = create_env(
        config,
        scenario=config.scenario,
        seed=NATURAL_SEED,
        rank=0,
        scale_mode="eval",
    )
    set_all_seeds(NATURAL_SEED, device)
    agent = create_agent(
        config,
        argparse.Namespace(device="cuda"),
        environment,
        num_envs=1,
        state_dim=int(environment.state_dim),
    )
    total_steps, update_index = checkpoint_io.load_checkpoint(
        checkpoint, agent, load_optimizers=False
    )
    manifest = checkpoint_manifest(checkpoint)
    source_checks = validate_source(
        config, metadata, manifest, total_steps, update_index
    )
    set_eval_and_freeze(agent)
    return (
        config,
        environment,
        agent,
        metadata,
        int(total_steps),
        int(update_index),
        device,
        source_checks,
    )


def clear_episode_buffers(agent: Any) -> None:
    agent.segments.flush(env_id=0, reason="episode")
    agent.segments.pop_completed()
    agent.high_check_buffer.pop_completed()


def capture_context(
    environment: Any,
    agent: Any,
    *,
    context_id: int,
    reset_group: int,
    focal_agent: int,
    check_index: int,
    observations: np.ndarray,
    state: np.ndarray,
) -> ForcedContext:
    return ForcedContext(
        context_id=int(context_id),
        reset_group=int(reset_group),
        focal_agent=int(focal_agent),
        check_index=int(check_index),
        observations=np.asarray(observations, dtype=np.float32).copy(),
        state=np.asarray(state, dtype=np.float32).copy(),
        environment_snapshot=copy.deepcopy(environment.env.get_probe_snapshot()),
        adapter_rng_state=copy.deepcopy(environment.np_random.bit_generator.state),
        active_skills=agent.active_skills[0].astype(np.int64, copy=True),
        active_mask=agent.has_active_skill[0].astype(np.bool_, copy=True),
        skill_ages=agent.skill_age[0].astype(np.int64, copy=True),
        team_code=int(agent.active_team_codes[0]),
        steps_to_check=int(agent.steps_to_check[0]),
        episode_step=int(agent.episode_steps[0]),
        episode_id=int(agent.episode_ids[0]),
        actor_hxs=agent.low_actor_hxs[0].astype(np.float32, copy=True),
        critic_hxs=agent.low_critic_hxs[0].astype(np.float32, copy=True),
        python_rng_state=copy.deepcopy(random.getstate()),
        numpy_rng_state=copy.deepcopy(np.random.get_state()),
        torch_cpu_rng_state=torch.get_rng_state().clone(),
        torch_cuda_rng_states=[state.clone() for state in torch.cuda.get_rng_state_all()],
    )


def collect_natural(
    environment: Any,
    agent: Any,
    device: torch.device,
    *,
    groups: int,
    causal_contexts: int,
) -> tuple[dict[str, np.ndarray], list[ForcedContext], dict[str, Any]]:
    raw_environment = environment.env
    windows: list[np.ndarray] = []
    group_ids: list[int] = []
    focal_ids: list[int] = []
    check_ids: list[int] = []
    focal_start: list[np.ndarray] = []
    teammate_start: list[np.ndarray] = []
    age_start: list[int] = []
    action_windows: list[np.ndarray] = []
    contexts: list[ForcedContext] = []
    incomplete_windows = 0
    early_natural_resets = 0
    literal_zero_clock_steps = 0

    for group in range(groups):
        seed = NATURAL_SEED + group
        set_all_seeds(seed, device)
        observations, info = environment.reset(seed=seed)
        state = np.asarray(info["state"], dtype=np.float32)
        agent.reset_env_state(0)
        context_check = (group // 2) % 4
        selected_checks = {0, 2, 4, 6} if group % 2 == 0 else {1, 3, 5, 7}
        done = False

        for check_index in range(EPISODE_STEPS // K0):
            agent.maybe_assign_skills(
                observations,
                state=state,
                step=check_index * K0,
                k=K0,
                env_id=0,
                deterministic=False,
                policy_update=SOURCE_UPDATE,
                collect_r31=False,
            )
            if not bool(np.all(agent.has_active_skill[0])):
                raise RuntimeError("R47 natural high check did not commit a complete roster")
            if int(agent.steps_to_check[0]) != K0:
                raise RuntimeError("R47 natural high check did not reset k0 clock")
            if group < causal_contexts and check_index == context_check:
                contexts.append(
                    capture_context(
                        environment,
                        agent,
                        context_id=len(contexts),
                        reset_group=group,
                        focal_agent=group % N_AGENTS,
                        check_index=check_index,
                        observations=observations,
                        state=state,
                    )
                )

            selected = check_index in selected_checks
            position_frames = [raw_environment.agent_pos.astype(np.float32, copy=True)]
            actions_in_window: list[np.ndarray] = []
            start_skills_age = agent.skill_age[0].astype(np.int64, copy=True)
            completed_steps = 0
            for _primitive in range(K0):
                actions, _log_probabilities, _values = agent.act_low(
                    observations,
                    env_id=0,
                    deterministic=False,
                    state=state,
                )
                if selected:
                    actions_in_window.append(np.asarray(actions, dtype=np.float32).copy())
                observations, _ignored_external_reward, terminated, truncated, next_info = (
                    environment.step(actions)
                )
                state = np.asarray(next_info["next_state"], dtype=np.float32)
                position_frames.append(
                    raw_environment.agent_pos.astype(np.float32, copy=True)
                )
                done = bool(terminated or truncated)
                agent.record_environment_step(
                    0,
                    reward=0.0,
                    next_obs=observations,
                    next_state=state,
                    done=done,
                    collect_r31=False,
                )
                literal_zero_clock_steps += 1
                completed_steps += 1
                if done:
                    break

            if selected:
                if completed_steps == K0:
                    views = seven_dimensional_process_view(
                        np.asarray(position_frames, dtype=np.float32)
                    )
                    action_array = np.asarray(actions_in_window, dtype=np.float32)
                    for focal in range(N_AGENTS):
                        windows.append(views[focal])
                        group_ids.append(group)
                        focal_ids.append(focal)
                        check_ids.append(check_index)
                        normalized_start = position_frames[0] / WORLD_SIZE
                        focal_start.append(normalized_start[focal].copy())
                        teammate_start.append(normalized_start[1 - focal].copy())
                        age_start.append(int(start_skills_age[focal]))
                        action_windows.append(action_array.copy())
                else:
                    incomplete_windows += N_AGENTS
            if done:
                if not (check_index == 7 and completed_steps == K0):
                    early_natural_resets += 1
                break
        if not done:
            early_natural_resets += 1
        clear_episode_buffers(agent)

    evidence = {
        "natural_views": np.asarray(windows, dtype=np.float32),
        "natural_group": np.asarray(group_ids, dtype=np.int64),
        "natural_focal": np.asarray(focal_ids, dtype=np.int64),
        "natural_check": np.asarray(check_ids, dtype=np.int64),
        "natural_focal_start": np.asarray(focal_start, dtype=np.float32),
        "natural_teammate_start": np.asarray(teammate_start, dtype=np.float32),
        "natural_age_start": np.asarray(age_start, dtype=np.int64),
        "natural_actions": np.asarray(action_windows, dtype=np.float32),
    }
    metadata = {
        "natural_groups": int(groups),
        "natural_windows": int(len(windows)),
        "expected_natural_windows": int(groups * NATURAL_WINDOWS_PER_GROUP),
        "causal_contexts": int(len(contexts)),
        "incomplete_natural_windows": int(incomplete_windows),
        "early_natural_resets": int(early_natural_resets),
        "literal_zero_clock_steps": int(literal_zero_clock_steps),
    }
    return evidence, contexts, metadata


def restore_context(environment: Any, context: ForcedContext) -> dict[str, float]:
    environment.env.set_probe_snapshot(copy.deepcopy(context.environment_snapshot))
    environment.np_random.bit_generator.state = copy.deepcopy(context.adapter_rng_state)
    current_positions = np.asarray(environment.env.agent_pos, dtype=np.float32)
    expected_positions = np.asarray(
        context.environment_snapshot["agent_pos"], dtype=np.float32
    )
    position_error = float(np.max(np.abs(current_positions - expected_positions)))
    current_observations = environment._dict_to_array(environment.env._get_obs()).astype(
        np.float32
    )
    observation_error = float(
        np.max(np.abs(current_observations - context.observations))
    )
    current_state = np.asarray(environment._state_array(), dtype=np.float32)
    state_error = float(np.max(np.abs(current_state - context.state)))
    return {
        "position_max_error": position_error,
        "observation_max_error": observation_error,
        "state_max_error": state_error,
    }


def low_policy_step(
    low: Any,
    *,
    observations: np.ndarray,
    state: np.ndarray,
    skills: np.ndarray,
    team_code: int,
    actor_hxs: np.ndarray,
    critic_hxs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    device = low.device
    observations_t = torch.as_tensor(observations, dtype=torch.float32, device=device)
    skills_t = torch.as_tensor(skills, dtype=torch.long, device=device)
    states_t = torch.as_tensor(
        np.broadcast_to(np.asarray(state, dtype=np.float32), (N_AGENTS, len(state))).copy(),
        dtype=torch.float32,
        device=device,
    )
    team_t = torch.full((N_AGENTS,), int(team_code), dtype=torch.long, device=device)
    actor_t = torch.as_tensor(actor_hxs, dtype=torch.float32, device=device)
    critic_t = torch.as_tensor(critic_hxs, dtype=torch.float32, device=device)
    agent_ids = torch.arange(N_AGENTS, dtype=torch.long, device=device)
    with torch.no_grad():
        actions, _logp, _unused, _values, next_actor, next_critic = low.act(
            observations_t,
            skills_t,
            actor_t,
            states_t,
            team_t,
            critic_t,
            agent_ids,
            deterministic=False,
        )
    return (
        actions.detach().cpu().numpy().astype(np.float32),
        next_actor.detach().cpu().numpy().astype(np.float32),
        next_critic.detach().cpu().numpy().astype(np.float32),
    )


def run_forced_branch(
    environment: Any,
    agent: Any,
    context: ForcedContext,
    *,
    skill: int,
    replica: int,
    device: torch.device,
) -> tuple[np.ndarray, int, bool, dict[str, float]]:
    restore_errors = restore_context(environment, context)
    seed = BRANCH_SEED + 2 * int(context.context_id) + int(replica)
    set_all_seeds(seed, device)
    observations = context.observations.copy()
    state = context.state.copy()
    skills = context.active_skills.copy()
    skills[int(context.focal_agent)] = int(skill)
    actor_hxs = context.actor_hxs.copy()
    critic_hxs = context.critic_hxs.copy()
    position_frames = [environment.env.agent_pos.astype(np.float32, copy=True)]
    completed = 0
    early = False
    for _step in range(FORCED_HORIZON):
        actions, actor_hxs, critic_hxs = low_policy_step(
            agent.low,
            observations=observations,
            state=state,
            skills=skills,
            team_code=context.team_code,
            actor_hxs=actor_hxs,
            critic_hxs=critic_hxs,
        )
        observations, _ignored_external_reward, terminated, truncated, info = (
            environment.step(actions)
        )
        state = np.asarray(info["next_state"], dtype=np.float32)
        position_frames.append(environment.env.agent_pos.astype(np.float32, copy=True))
        completed += 1
        if terminated or truncated:
            early = completed < FORCED_HORIZON
            break
    output = np.zeros((FORCED_HORIZON, VIEW_DIM), dtype=np.float32)
    if completed:
        views = seven_dimensional_process_view(
            np.asarray(position_frames, dtype=np.float32)
        )[int(context.focal_agent)]
        output[:completed] = views
    return output, completed, early, restore_errors


def collect_forced(
    environment: Any,
    agent: Any,
    contexts: list[ForcedContext],
    device: torch.device,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    views = np.zeros(
        (len(contexts), N_SKILLS, REPLICAS, FORCED_HORIZON, VIEW_DIM),
        dtype=np.float32,
    )
    lengths = np.zeros((len(contexts), N_SKILLS, REPLICAS), dtype=np.int64)
    early = np.zeros((len(contexts), N_SKILLS, REPLICAS), dtype=np.bool_)
    seed_table = np.zeros((len(contexts), N_SKILLS, REPLICAS), dtype=np.int64)
    restore_error = 0.0
    for context_index, context in enumerate(contexts):
        for skill in range(N_SKILLS):
            for replica in range(REPLICAS):
                seed_table[context_index, skill, replica] = (
                    BRANCH_SEED + 2 * context.context_id + replica
                )
                branch, completed, ended_early, errors = run_forced_branch(
                    environment,
                    agent,
                    context,
                    skill=skill,
                    replica=replica,
                    device=device,
                )
                views[context_index, skill, replica] = branch
                lengths[context_index, skill, replica] = completed
                early[context_index, skill, replica] = ended_early
                restore_error = max(restore_error, *errors.values())
    evidence = {
        "forced_views": views,
        "forced_lengths": lengths,
        "forced_early": early,
        "forced_seed": seed_table,
        "forced_context_group": np.asarray(
            [context.reset_group for context in contexts], dtype=np.int64
        ),
        "forced_context_focal": np.asarray(
            [context.focal_agent for context in contexts], dtype=np.int64
        ),
        "forced_context_check": np.asarray(
            [context.check_index for context in contexts], dtype=np.int64
        ),
        "forced_context_roster": np.asarray(
            [context.active_skills for context in contexts], dtype=np.int64
        ),
        "forced_context_age": np.asarray(
            [context.skill_ages for context in contexts], dtype=np.int64
        ),
        "forced_context_mask": np.asarray(
            [context.active_mask for context in contexts], dtype=np.bool_
        ),
    }
    complete_context = np.all(lengths == FORCED_HORIZON, axis=(1, 2)) & ~np.any(
        early, axis=(1, 2)
    )
    metadata = {
        "branch_count": int(np.prod(lengths.shape)),
        "completed_branch_steps": int(lengths.sum()),
        "complete_contexts": int(complete_context.sum()),
        "early_branch_reset_contexts": int((~complete_context).sum()),
        "snapshot_restore_max_error": float(restore_error),
        "crn_seed_equal_across_skills": bool(
            np.all(seed_table == seed_table[:, 0:1, :])
        ),
        "replica_seed_independent": bool(np.all(seed_table[:, :, 0] != seed_table[:, :, 1])),
    }
    return evidence, metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=str(ROOT / SOURCE_CHECKPOINT))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    progress_path = output_root / "progress.json"
    result_path = output_root / "seed_result.json"
    evidence_path = output_root / "r47_nsopm_evidence.npz"
    checkpoint = Path(args.checkpoint).resolve()
    natural_groups = 2 if args.dry_run else NATURAL_GROUPS
    causal_contexts = 1 if args.dry_run else CAUSAL_CONTEXTS

    write_progress(progress_path, "source_load", natural_groups=natural_groups)
    (
        _config,
        environment,
        agent,
        metadata,
        total_steps,
        update_index,
        device,
        source_checks,
    ) = make_source(checkpoint, args.device)
    before = module_state(agent)
    try:
        write_progress(progress_path, "natural_collection", natural_groups_completed=0)
        natural, contexts, natural_metadata = collect_natural(
            environment,
            agent,
            device,
            groups=natural_groups,
            causal_contexts=causal_contexts,
        )
        write_progress(
            progress_path,
            "forced_audit",
            natural_windows=natural_metadata["natural_windows"],
            forced_contexts=0,
        )
        forced, forced_metadata = collect_forced(
            environment, agent, contexts, device
        )
    finally:
        environment.close()
    after = module_state(agent)
    drift = module_drift(before, after)
    covariance_abs_max = 0.0
    if natural["natural_views"].size:
        covariance_abs_max = float(
            np.max(np.abs(natural["natural_views"][..., 4:7]))
        )

    np.savez_compressed(evidence_path, **natural, **forced)
    formal = not bool(args.dry_run)
    expected_groups = NATURAL_GROUPS if formal else 2
    expected_windows = NATURAL_WINDOWS if formal else 16
    expected_contexts = CAUSAL_CONTEXTS if formal else 1
    expected_branches = FORCED_BRANCHES if formal else 8
    expected_steps = FORCED_STEPS if formal else 320
    payload = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "scope": "formal" if formal else "dry_run",
        "state": "completed",
        "device": str(device),
        "source": {
            "checkpoint": str(checkpoint),
            "checkpoint_total_steps": total_steps,
            "checkpoint_update": update_index,
            "high_controller": metadata.get("high_controller"),
            "scenario": metadata.get("scenario"),
            "source_checks": source_checks,
        },
        "telemetry": {
            **natural_metadata,
            **forced_metadata,
            "expected_groups": expected_groups,
            "expected_natural_windows": expected_windows,
            "expected_causal_contexts": expected_contexts,
            "expected_forced_branches": expected_branches,
            "expected_forced_steps": expected_steps,
            "policy_optimizer_steps": 0,
            "high_optimizer_steps": 0,
            "critic_optimizer_steps": 0,
            "intrinsic_optimizer_steps": 0,
        },
        "view": {
            "name": "task_blind_relative_moment_delta_v1",
            "shape": list(natural["natural_views"].shape),
            "field_order": [
                "delta_focal_x",
                "delta_focal_y",
                "delta_mean_relative_x",
                "delta_mean_relative_y",
                "delta_covariance_xx",
                "delta_covariance_xy",
                "delta_covariance_yy",
            ],
            "covariance_last_three_max_abs": covariance_abs_max,
            "world_size": WORLD_SIZE,
        },
        "parameter_drift": drift,
        "algorithm_boundary": {
            "standalone_reward_off_gate": True,
            "external_reward_discarded": True,
            "external_reward_stored": False,
            "environment_reward_field_in_evidence": False,
            "task_field_in_process_view": False,
            "action_field_in_process_view": False,
            "skill_field_in_process_view": False,
            "forced_data_used_for_basis_fit": False,
            "high_controller_suppressed_in_forced_branch": True,
            "policy_or_critic_update": False,
            "normal_trainer_modified": False,
        },
        "artifacts": {"evidence": str(evidence_path)},
    }
    write_json(result_path, payload)
    write_progress(
        progress_path,
        "completed",
        scope=payload["scope"],
        natural_windows=natural_metadata["natural_windows"],
        forced_steps=forced_metadata["completed_branch_steps"],
        result_path=str(result_path),
    )
    print(
        f"R47 worker completed scope={payload['scope']} evidence={evidence_path}",
        flush=True,
    )


if __name__ == "__main__":
    main()
