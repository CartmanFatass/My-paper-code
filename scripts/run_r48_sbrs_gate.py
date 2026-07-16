"""Collect and analyze the registered reward-off R48-SBRS-G0 gate."""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from r47_nsopm import SOURCE_UPDATE  # noqa: E402
from run_r47_nsopm_gate import (  # noqa: E402
    ForcedContext,
    capture_context,
    clear_episode_buffers,
    make_source,
    module_drift,
    module_state,
    restore_context,
    set_all_seeds,
)
from r48_sbrs import (  # noqa: E402
    ARMS,
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    BRANCHES_PER_ARM,
    BRANCH_HORIZON,
    CONTEXTS,
    EPISODE_STEPS,
    EXPERIMENT_ID,
    FORCED_BRANCH_STEPS,
    HORIZONS,
    INNOVATION_SEED,
    K0,
    N_AGENTS,
    N_SKILLS,
    NATURAL_SOURCE_STEPS,
    PROCESS_DIM,
    REPLICAS,
    SCHEMA_VERSION,
    SOURCE_CHECKPOINT,
    SOURCE_SEED,
    SOURCE_TOTAL_STEPS,
    TARGETS_PER_CONTEXT,
    between_within_statistics,
    bootstrap_gate_metrics,
    json_ready,
    per_skill_rho,
    task_blind_process_trajectory,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def normalizer_state(agent: Any) -> dict[str, dict[str, float] | None]:
    state: dict[str, dict[str, float] | None] = {}
    for name in ("high_value_norm", "low_value_norm"):
        value = getattr(agent, name, None)
        state[name] = None if value is None else dict(value.state_dict())
    return state


def normalizer_drift(
    before: dict[str, dict[str, float] | None],
    after: dict[str, dict[str, float] | None],
) -> dict[str, Any]:
    inventory_equal = tuple(before) == tuple(after)
    maximum = 0.0
    exact = inventory_equal
    if inventory_equal:
        for name in before:
            if before[name] is None or after[name] is None:
                exact = exact and before[name] is after[name]
                continue
            if tuple(before[name] or {}) != tuple(after[name] or {}):
                exact = False
                inventory_equal = False
                continue
            for key, left in (before[name] or {}).items():
                right = float((after[name] or {})[key])
                maximum = max(maximum, abs(float(left) - right))
                exact = exact and float(left) == right
    return {
        "inventory_equal": bool(inventory_equal),
        "max_abs": float(maximum),
        "all_exact": bool(exact),
    }


def collect_contexts(
    environment: Any,
    agent: Any,
    device: torch.device,
    groups: int,
) -> tuple[list[ForcedContext], dict[str, Any]]:
    contexts: list[ForcedContext] = []
    completed_source_steps = 0
    early_resets = 0
    literal_zero_clock_steps = 0

    for group in range(groups):
        seed = SOURCE_SEED + group
        set_all_seeds(seed, device)
        observations, info = environment.reset(seed=seed)
        state = np.asarray(info["state"], dtype=np.float32)
        agent.reset_env_state(0)
        context_check = 1 + (group // 2) % 4
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
                raise RuntimeError("R48 source check did not commit a complete roster")
            if int(agent.steps_to_check[0]) != K0:
                raise RuntimeError("R48 source check did not reset the k0 clock")
            if check_index == context_check:
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

            completed_block_steps = 0
            for _ in range(K0):
                actions, _log_probabilities, _values = agent.act_low(
                    observations,
                    env_id=0,
                    deterministic=False,
                    state=state,
                )
                observations, _unused_return, terminated, truncated, next_info = (
                    environment.step(actions)
                )
                state = np.asarray(next_info["next_state"], dtype=np.float32)
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
                completed_source_steps += 1
                completed_block_steps += 1
                if done:
                    break
            if done:
                if not (check_index == 7 and completed_block_steps == K0):
                    early_resets += 1
                break
        if not done:
            early_resets += 1
        clear_episode_buffers(agent)

    return contexts, {
        "natural_source_groups": int(groups),
        "natural_source_steps": int(completed_source_steps),
        "literal_zero_clock_steps": int(literal_zero_clock_steps),
        "early_source_resets": int(early_resets),
        "contexts": int(len(contexts)),
    }


def low_policy_step_with_innovation(
    low: Any,
    *,
    observations: np.ndarray,
    state: np.ndarray,
    skills: np.ndarray,
    team_code: int,
    actor_hxs: np.ndarray,
    critic_hxs: np.ndarray,
    innovation: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    device = low.device
    observations_t = torch.as_tensor(observations, dtype=torch.float32, device=device)
    skills_t = torch.as_tensor(skills, dtype=torch.long, device=device)
    team_t = torch.full((N_AGENTS,), int(team_code), dtype=torch.long, device=device)
    states_t = torch.as_tensor(
        np.broadcast_to(np.asarray(state, dtype=np.float32), (N_AGENTS, len(state))).copy(),
        dtype=torch.float32,
        device=device,
    )
    actor_t = torch.as_tensor(actor_hxs, dtype=torch.float32, device=device)
    critic_t = torch.as_tensor(critic_hxs, dtype=torch.float32, device=device)
    innovation_t = torch.as_tensor(innovation, dtype=torch.float32, device=device)
    if tuple(innovation_t.shape) != (N_AGENTS, int(low.action_dim)):
        raise ValueError("R48 innovation shape does not match the low actor")

    with torch.no_grad():
        masks = torch.ones(N_AGENTS, 1, dtype=torch.float32, device=device)
        actor_features = low._actor_features(observations_t, skills_t, team_t)
        actor_features, next_actor = low.actor_rnn(actor_features, actor_t, masks)
        action_out = low.actor_act.action_out
        if type(action_out).__name__ != "TanhDiagGaussian":
            raise TypeError("R48 requires the source tanh-Gaussian action head")
        distribution = action_out._distribution(actor_features)
        raw_action = distribution.mean + distribution.stddev * innovation_t
        actions = torch.tanh(raw_action)

        critic_features = low._critic_features(states_t, team_t)
        critic_features, next_critic = low.critic_rnn(critic_features, critic_t, masks)
        _unused_values = low.value_head(critic_features).squeeze(-1)

    return (
        actions.detach().cpu().numpy().astype(np.float32),
        next_actor.detach().cpu().numpy().astype(np.float32),
        next_critic.detach().cpu().numpy().astype(np.float32),
    )


def run_branch(
    environment: Any,
    agent: Any,
    context: ForcedContext,
    *,
    arm_index: int,
    target_skill: int,
    innovation_tape: np.ndarray,
) -> tuple[dict[str, np.ndarray], int, bool, dict[str, float]]:
    restore_errors = restore_context(environment, context)
    observations = context.observations.copy()
    state = context.state.copy()
    skills = context.active_skills.copy()
    skills[int(context.focal_agent)] = int(target_skill)
    actor_hxs = context.actor_hxs.copy()
    critic_hxs = context.critic_hxs.copy()
    if ARMS[int(arm_index)] == "reset_on_set":
        actor_hxs[int(context.focal_agent)] = 0.0

    start = {
        "observation": observations.copy(),
        "state": state.copy(),
        "roster": skills.copy(),
        "team_code": np.asarray(context.team_code, dtype=np.int64),
        "actor_hxs": actor_hxs.copy(),
        "critic_hxs": critic_hxs.copy(),
    }
    position_frames = [environment.env.agent_pos.astype(np.float32, copy=True)]
    completed = 0
    early = False
    for step in range(BRANCH_HORIZON):
        actions, actor_hxs, critic_hxs = low_policy_step_with_innovation(
            agent.low,
            observations=observations,
            state=state,
            skills=skills,
            team_code=context.team_code,
            actor_hxs=actor_hxs,
            critic_hxs=critic_hxs,
            innovation=innovation_tape[step],
        )
        observations, _unused_return, terminated, truncated, info = environment.step(
            actions
        )
        state = np.asarray(info["next_state"], dtype=np.float32)
        position_frames.append(environment.env.agent_pos.astype(np.float32, copy=True))
        completed += 1
        if terminated or truncated:
            early = completed < BRANCH_HORIZON
            break

    trajectory = np.full((BRANCH_HORIZON, PROCESS_DIM), np.nan, dtype=np.float32)
    if completed == BRANCH_HORIZON:
        trajectory[:] = task_blind_process_trajectory(
            np.asarray(position_frames, dtype=np.float32), context.focal_agent
        )
    start["trajectory"] = trajectory
    return start, completed, early, restore_errors


def collect_branches(
    environment: Any,
    agent: Any,
    contexts: list[ForcedContext],
    innovation: np.ndarray,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    count = len(contexts)
    hidden_dim = int(agent.low.hidden_dim)
    action_dim = int(agent.low.action_dim)
    target_skills = np.zeros((count, TARGETS_PER_CONTEXT), dtype=np.int64)
    incumbents = np.zeros(count, dtype=np.int64)
    trajectories = np.full(
        (
            len(ARMS),
            count,
            TARGETS_PER_CONTEXT,
            REPLICAS,
            BRANCH_HORIZON,
            PROCESS_DIM,
        ),
        np.nan,
        dtype=np.float32,
    )
    lengths = np.zeros(
        (len(ARMS), count, TARGETS_PER_CONTEXT, REPLICAS), dtype=np.int64
    )
    early = np.zeros_like(lengths, dtype=np.bool_)
    start_observations = np.zeros(
        (len(ARMS), count, TARGETS_PER_CONTEXT, REPLICAS, N_AGENTS, 12),
        dtype=np.float32,
    )
    start_states = np.zeros(
        (len(ARMS), count, TARGETS_PER_CONTEXT, REPLICAS, 19), dtype=np.float32
    )
    start_rosters = np.zeros(
        (len(ARMS), count, TARGETS_PER_CONTEXT, REPLICAS, N_AGENTS), dtype=np.int64
    )
    start_team_codes = np.zeros(
        (len(ARMS), count, TARGETS_PER_CONTEXT, REPLICAS), dtype=np.int64
    )
    start_actor_hxs = np.zeros(
        (
            len(ARMS),
            count,
            TARGETS_PER_CONTEXT,
            REPLICAS,
            N_AGENTS,
            hidden_dim,
        ),
        dtype=np.float32,
    )
    start_critic_hxs = np.zeros_like(start_actor_hxs)
    used_innovations = np.zeros(
        (
            len(ARMS),
            count,
            TARGETS_PER_CONTEXT,
            REPLICAS,
            BRANCH_HORIZON,
            N_AGENTS,
            action_dim,
        ),
        dtype=np.float32,
    )
    restore_max = 0.0

    for context_index, context in enumerate(contexts):
        focal = int(context.focal_agent)
        incumbent = int(context.active_skills[focal])
        targets = [skill for skill in range(N_SKILLS) if skill != incumbent]
        if len(targets) != TARGETS_PER_CONTEXT:
            raise RuntimeError("R48 did not construct exactly three nonincumbent targets")
        incumbents[context_index] = incumbent
        target_skills[context_index] = targets
        for arm_index in range(len(ARMS)):
            for target_index, target_skill in enumerate(targets):
                for replica in range(REPLICAS):
                    tape = innovation[context_index, replica]
                    start, completed, ended_early, errors = run_branch(
                        environment,
                        agent,
                        context,
                        arm_index=arm_index,
                        target_skill=target_skill,
                        innovation_tape=tape,
                    )
                    trajectories[arm_index, context_index, target_index, replica] = (
                        start["trajectory"]
                    )
                    lengths[arm_index, context_index, target_index, replica] = completed
                    early[arm_index, context_index, target_index, replica] = ended_early
                    start_observations[
                        arm_index, context_index, target_index, replica
                    ] = start["observation"]
                    start_states[arm_index, context_index, target_index, replica] = start[
                        "state"
                    ]
                    start_rosters[arm_index, context_index, target_index, replica] = start[
                        "roster"
                    ]
                    start_team_codes[
                        arm_index, context_index, target_index, replica
                    ] = int(start["team_code"])
                    start_actor_hxs[
                        arm_index, context_index, target_index, replica
                    ] = start["actor_hxs"]
                    start_critic_hxs[
                        arm_index, context_index, target_index, replica
                    ] = start["critic_hxs"]
                    used_innovations[
                        arm_index, context_index, target_index, replica
                    ] = tape
                    restore_max = max(restore_max, *errors.values())

    complete = (lengths == BRANCH_HORIZON) & ~early
    evidence = {
        "context_group": np.asarray([row.reset_group for row in contexts], dtype=np.int64),
        "context_focal": np.asarray([row.focal_agent for row in contexts], dtype=np.int64),
        "context_check": np.asarray([row.check_index for row in contexts], dtype=np.int64),
        "context_observations": np.asarray(
            [row.observations for row in contexts], dtype=np.float32
        ),
        "context_states": np.asarray([row.state for row in contexts], dtype=np.float32),
        "context_rosters": np.asarray(
            [row.active_skills for row in contexts], dtype=np.int64
        ),
        "context_team_codes": np.asarray(
            [row.team_code for row in contexts], dtype=np.int64
        ),
        "context_actor_hxs": np.asarray(
            [row.actor_hxs for row in contexts], dtype=np.float32
        ),
        "context_critic_hxs": np.asarray(
            [row.critic_hxs for row in contexts], dtype=np.float32
        ),
        "incumbent_skills": incumbents,
        "target_skills": target_skills,
        "process_trajectories": trajectories,
        "branch_lengths": lengths,
        "branch_early": early,
        "start_observations": start_observations,
        "start_states": start_states,
        "start_rosters": start_rosters,
        "start_team_codes": start_team_codes,
        "start_actor_hxs": start_actor_hxs,
        "start_critic_hxs": start_critic_hxs,
        "innovation_tape": innovation,
        "used_innovations": used_innovations,
    }
    metadata = {
        "branches_per_arm": int(np.prod(lengths.shape[1:])),
        "total_branches": int(np.prod(lengths.shape)),
        "completed_branch_steps": int(lengths.sum()),
        "complete_branches": int(complete.sum()),
        "early_branches": int((~complete).sum()),
        "snapshot_restore_max_error": float(restore_max),
    }
    return evidence, metadata


def maximum_error(left: np.ndarray, right: np.ndarray) -> float:
    left_array = np.asarray(left)
    right_array = np.asarray(right)
    if left_array.shape != right_array.shape:
        return float("inf")
    if not left_array.size:
        return 0.0
    return float(np.max(np.abs(left_array.astype(np.float64) - right_array.astype(np.float64))))


def implementation_checks(
    worker: dict[str, Any],
    arrays: dict[str, np.ndarray],
    *,
    formal: bool,
) -> tuple[dict[str, bool], list[str], dict[str, Any]]:
    contexts = CONTEXTS if formal else 2
    expected_branches_per_arm = contexts * TARGETS_PER_CONTEXT * REPLICAS
    expected_total_steps = len(ARMS) * expected_branches_per_arm * BRANCH_HORIZON
    source_steps = contexts * EPISODE_STEPS
    targets = arrays["target_skills"]
    incumbents = arrays["incumbent_skills"]
    target_contract = all(
        sorted(int(value) for value in targets[index])
        == [skill for skill in range(N_SKILLS) if skill != int(incumbents[index])]
        for index in range(contexts)
    )
    support = {
        str(skill): int(np.sum(targets == skill)) for skill in range(N_SKILLS)
    }

    carry = ARMS.index("carry_hidden")
    reset = ARMS.index("reset_on_set")
    focal = arrays["context_focal"].astype(np.int64)
    actor_starts = arrays["start_actor_hxs"]
    context_actor = arrays["context_actor_hxs"]
    carry_expected = np.broadcast_to(
        context_actor[:, None, None, :, :], actor_starts[carry].shape
    )
    reset_expected = carry_expected.copy()
    for context_index, focal_agent in enumerate(focal):
        reset_expected[context_index, :, :, focal_agent, :] = 0.0

    arm_obs_error = maximum_error(
        arrays["start_observations"][carry], arrays["start_observations"][reset]
    )
    arm_state_error = maximum_error(
        arrays["start_states"][carry], arrays["start_states"][reset]
    )
    arm_roster_error = maximum_error(
        arrays["start_rosters"][carry], arrays["start_rosters"][reset]
    )
    arm_team_error = maximum_error(
        arrays["start_team_codes"][carry], arrays["start_team_codes"][reset]
    )
    critic_error = maximum_error(
        arrays["start_critic_hxs"][carry], arrays["start_critic_hxs"][reset]
    )
    carry_actor_error = maximum_error(actor_starts[carry], carry_expected)
    reset_actor_error = maximum_error(actor_starts[reset], reset_expected)
    innovation_expected = np.broadcast_to(
        arrays["innovation_tape"][None, :, None, :, :, :, :],
        arrays["used_innovations"].shape,
    )
    innovation_error = maximum_error(
        arrays["used_innovations"], innovation_expected
    )

    finite_arrays = all(
        np.all(np.isfinite(value))
        for name, value in arrays.items()
        if value.dtype.kind in "fc" and name != "process_trajectories"
    ) and np.all(np.isfinite(arrays["process_trajectories"]))
    finite_statistics = True
    try:
        for indices in HORIZONS.values():
            statistics = between_within_statistics(
                arrays["process_trajectories"], targets, indices
            )
            finite_statistics = finite_statistics and all(
                np.all(np.isfinite(statistics[name]))
                for name in ("between", "within")
            )
            global_rho = statistics["between"].mean(axis=1) / (
                statistics["within"].mean(axis=1) + 1e-8
            )
            finite_statistics = finite_statistics and bool(
                np.all(np.isfinite(global_rho))
            )
            if formal:
                finite_statistics = finite_statistics and all(
                    np.isfinite(value)
                    for value in per_skill_rho(
                        statistics, "reset_on_set"
                    ).values()
                )
    except (ValueError, FloatingPointError):
        finite_statistics = False
    evidence_names_clean = not any(
        token in name.lower() for name in arrays for token in ("reward", "task")
    )
    source_checks = worker["source"]["source_checks"]
    telemetry = worker["telemetry"]
    checks = {
        "exact_source_checkpoint_and_config": bool(all(source_checks.values())),
        "context_count_exact": int(telemetry["contexts"]) == contexts,
        "natural_source_steps_exact": int(telemetry["natural_source_steps"])
        == source_steps,
        "context_schedule_exact": bool(
            np.array_equal(arrays["context_group"], np.arange(contexts))
            and np.array_equal(arrays["context_focal"], np.arange(contexts) % N_AGENTS)
            and np.array_equal(
                arrays["context_check"],
                1 + (np.arange(contexts) // 2) % 4,
            )
        ),
        "three_nonincumbent_targets_each": bool(target_contract),
        "branches_per_arm_exact": int(telemetry["branches_per_arm"])
        == expected_branches_per_arm,
        "total_branch_steps_exact": int(telemetry["completed_branch_steps"])
        == expected_total_steps,
        "no_early_reset_or_truncation": bool(
            int(telemetry["early_source_resets"]) == 0
            and int(telemetry["early_branches"]) == 0
            and np.all(arrays["branch_lengths"] == BRANCH_HORIZON)
        ),
        "snapshot_restore_exact": float(telemetry["snapshot_restore_max_error"])
        == 0.0,
        "arm_start_environment_equal": arm_state_error == 0.0,
        "arm_start_observation_equal": arm_obs_error == 0.0,
        "arm_start_roster_equal": arm_roster_error == 0.0,
        "arm_start_team_code_equal": arm_team_error == 0.0,
        "common_innovation_tape_exact": innovation_error == 0.0,
        "carry_actor_hidden_is_snapshot": carry_actor_error == 0.0,
        "reset_only_focal_actor_hidden": reset_actor_error == 0.0,
        "critic_hidden_equal_at_boundary": critic_error == 0.0,
        "parameter_freeze_exact": bool(worker["parameter_drift"]["all_exact"]),
        "normalizer_freeze_exact": bool(worker["normalizer_drift"]["all_exact"]),
        "all_optimizer_steps_zero": all(
            int(value) == 0 for value in worker["optimizer_steps"].values()
        ),
        "evidence_has_no_task_or_reward_field": bool(evidence_names_clean),
        "target_support_floor": (not formal)
        or all(value >= 32 for value in support.values()),
        "all_evidence_finite": bool(finite_arrays),
        "all_distances_between_within_and_rho_finite": bool(finite_statistics),
    }
    reasons = [name for name, passed in checks.items() if not passed]
    diagnostics = {
        "target_support": support,
        "arm_start_observation_max_error": arm_obs_error,
        "arm_start_environment_max_error": arm_state_error,
        "arm_start_roster_max_error": arm_roster_error,
        "arm_start_team_code_max_error": arm_team_error,
        "common_innovation_max_error": innovation_error,
        "carry_actor_hidden_snapshot_max_error": carry_actor_error,
        "reset_actor_hidden_contract_max_error": reset_actor_error,
        "critic_hidden_boundary_max_error": critic_error,
        "focal_snapshot_hidden_min_l2": float(
            min(
                np.linalg.norm(context_actor[index, focal_agent])
                for index, focal_agent in enumerate(focal)
            )
        ),
    }
    return checks, reasons, diagnostics


def analyze_formal(
    worker: dict[str, Any], arrays: dict[str, np.ndarray]
) -> dict[str, Any]:
    m0_checks, invalid_reasons, diagnostics = implementation_checks(
        worker, arrays, formal=True
    )
    m0_pass = bool(all(m0_checks.values()))
    common = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "contract": {
            "source_seed": SOURCE_SEED,
            "innovation_seed": INNOVATION_SEED,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "contexts": CONTEXTS,
            "targets_per_context": TARGETS_PER_CONTEXT,
            "replicas_per_target": REPLICAS,
            "arms": list(ARMS),
            "branch_horizon": BRANCH_HORIZON,
            "forced_branch_steps": FORCED_BRANCH_STEPS,
            "natural_source_steps": NATURAL_SOURCE_STEPS,
            "horizons": {
                name: (indices + 1).tolist() for name, indices in HORIZONS.items()
            },
        },
        "source": worker["source"],
        "telemetry": worker["telemetry"],
        "parameter_drift": worker["parameter_drift"],
        "normalizer_drift": worker["normalizer_drift"],
        "optimizer_steps": worker["optimizer_steps"],
        "algorithm_boundary": worker["algorithm_boundary"],
        "artifacts": worker["artifacts"],
    }
    if not m0_pass:
        return {
            **common,
            "status": "INVALID_R48_SBRS_WIRING",
            "implementation_valid": False,
            "m0": {
                "passed": False,
                "checks": m0_checks,
                "invalid_reasons": invalid_reasons,
                "diagnostics": diagnostics,
            },
            "m1": {"passed": False, "not_evaluated": "M0 invalid"},
            "decision": {
                "next_action": "repair only the identified wiring defect and rerun unchanged",
                "no_underpowered_branch": True,
                "no_rescue_by_seed_budget_model_threshold_reward_or_environment": True,
            },
        }
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    samples = rng.integers(
        0, CONTEXTS, size=(BOOTSTRAP_REPETITIONS, CONTEXTS), dtype=np.int64
    )
    horizons: dict[str, Any] = {}
    finite_metrics = True
    for name, indices in HORIZONS.items():
        statistics = between_within_statistics(
            arrays["process_trajectories"], arrays["target_skills"], indices
        )
        metrics = bootstrap_gate_metrics(statistics, samples)
        metrics["rho_reset_by_target_skill"] = per_skill_rho(
            statistics, "reset_on_set"
        )
        horizons[name] = metrics
        finite_metrics = finite_metrics and all(
            np.isfinite(value)
            for interval_name in (
                "rho_reset_over_carry",
                "within_reset_over_carry",
                "between_reset_over_carry",
            )
            for value in metrics[interval_name].values()
        ) and all(
            np.isfinite(value)
            for interval in metrics["rho"].values()
            for value in interval.values()
        ) and all(
            np.isfinite(value)
            for value in metrics["rho_reset_by_target_skill"].values()
        )

    gate_checks: dict[str, bool] = {}
    for horizon_name in HORIZONS:
        metrics = horizons[horizon_name]
        gate_checks[f"{horizon_name}_rho_reset_lcb_gt_1"] = (
            float(metrics["rho"]["reset_on_set"]["lower_95"]) > 1.0
        )
        gate_checks[f"{horizon_name}_rho_ratio_lcb_gt_1_25"] = (
            float(metrics["rho_reset_over_carry"]["lower_95"]) > 1.25
        )
        gate_checks[f"{horizon_name}_within_ratio_ucb_lt_0_80"] = (
            float(metrics["within_reset_over_carry"]["upper_95"]) < 0.80
        )
        gate_checks[f"{horizon_name}_between_ratio_lcb_gt_0_90"] = (
            float(metrics["between_reset_over_carry"]["lower_95"]) > 0.90
        )
    gate_checks["h40_late_every_target_skill_rho_gt_1"] = all(
        float(value) > 1.0
        for value in horizons["h40_late"]["rho_reset_by_target_skill"].values()
    )
    gate_checks["all_registered_metrics_finite"] = bool(finite_metrics)
    m1_pass = bool(all(gate_checks.values()))

    if m1_pass:
        status = "PASS_R48_SBRS_G0"
        next_action = (
            "authorize only a mechanism-matched reward-pure R30 "
            "carry_on_SET versus reset_on_SET pair"
        )
    else:
        status = "VALID_FAIL_R48_SBRS"
        next_action = (
            "retire skill-boundary reset and stop fixed-N skill/lifetime "
            "algorithm exploration"
        )
    return {
        **common,
        "status": status,
        "implementation_valid": m0_pass,
        "m0": {
            "passed": m0_pass,
            "checks": m0_checks,
            "invalid_reasons": invalid_reasons,
            "diagnostics": diagnostics,
        },
        "m1": {"passed": m1_pass, "checks": gate_checks, "horizons": horizons},
        "decision": {
            "next_action": next_action,
            "no_underpowered_branch": True,
            "no_rescue_by_seed_budget_model_threshold_reward_or_environment": True,
        },
    }


def analyze_dry_run(
    worker: dict[str, Any], arrays: dict[str, np.ndarray]
) -> dict[str, Any]:
    checks, reasons, diagnostics = implementation_checks(worker, arrays, formal=False)
    for indices in HORIZONS.values():
        statistics = between_within_statistics(
            arrays["process_trajectories"], arrays["target_skills"], indices
        )
        checks["dry_run_statistics_finite"] = all(
            np.all(np.isfinite(statistics[name]))
            for name in ("between", "within")
        )
    valid = bool(all(checks.values()))
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "scope": "dry_run",
        "dry_run_valid": valid,
        "checks": checks,
        "invalid_reasons": reasons + ([] if valid else ["dry_run_statistics_finite"]),
        "diagnostics": diagnostics,
        "scientific_thresholds_evaluated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=str(ROOT / SOURCE_CHECKPOINT))
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    seed_root = run_root / "seed"
    result_root = run_root / "result"
    seed_root.mkdir(parents=True, exist_ok=True)
    result_root.mkdir(parents=True, exist_ok=True)
    progress_path = seed_root / "progress.json"
    evidence_path = seed_root / "r48_sbrs_evidence.npz"
    worker_path = seed_root / "seed_result.json"
    result_path = (
        result_root / "dry_run_check.json"
        if args.dry_run
        else result_root / "r48_sbrs.json"
    )
    checkpoint = Path(args.checkpoint).resolve()
    groups = 2 if args.dry_run else CONTEXTS

    write_json(progress_path, {"phase": "source_load", "groups": groups})
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
    if int(total_steps) != SOURCE_TOTAL_STEPS:
        raise ValueError("R48 source step count mismatch")
    parameter_before = module_state(agent)
    normalizer_before = normalizer_state(agent)
    innovation_rng = np.random.default_rng(INNOVATION_SEED)
    innovation = innovation_rng.standard_normal(
        (groups, REPLICAS, BRANCH_HORIZON, N_AGENTS, int(agent.low.action_dim))
    ).astype(np.float32)

    try:
        write_json(progress_path, {"phase": "natural_context_collection", "groups": groups})
        contexts, natural_metadata = collect_contexts(
            environment, agent, device, groups
        )
        write_json(
            progress_path,
            {"phase": "paired_forced_branches", "contexts": len(contexts)},
        )
        evidence, branch_metadata = collect_branches(
            environment, agent, contexts, innovation
        )
    finally:
        environment.close()

    parameter_after = module_state(agent)
    normalizer_after = normalizer_state(agent)
    np.savez_compressed(evidence_path, **evidence)
    worker = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "scope": "dry_run" if args.dry_run else "formal",
        "state": "completed",
        "device": str(device),
        "source": {
            "checkpoint": str(checkpoint),
            "checkpoint_total_steps": int(total_steps),
            "checkpoint_update": int(update_index),
            "high_controller": metadata.get("high_controller"),
            "scenario": metadata.get("scenario"),
            "source_checks": source_checks,
        },
        "telemetry": {**natural_metadata, **branch_metadata},
        "parameter_drift": module_drift(parameter_before, parameter_after),
        "normalizer_drift": normalizer_drift(normalizer_before, normalizer_after),
        "optimizer_steps": {
            "policy": 0,
            "high": 0,
            "critic": 0,
            "intrinsic": 0,
        },
        "algorithm_boundary": {
            "standalone_reward_off_gate": True,
            "external_return_discarded": True,
            "external_return_stored": False,
            "task_field_in_evidence": False,
            "high_controller_suppressed_in_forced_branch": True,
            "only_intervention_is_focal_actor_hidden_reset": True,
            "policy_or_critic_update": False,
            "normal_trainer_modified": False,
        },
        "artifacts": {"evidence": str(evidence_path)},
    }
    write_json(worker_path, worker)
    with np.load(evidence_path, allow_pickle=False) as loaded:
        arrays = {name: loaded[name] for name in loaded.files}
    result = (
        analyze_dry_run(worker, arrays)
        if args.dry_run
        else analyze_formal(worker, arrays)
    )
    write_json(result_path, result)
    write_json(
        progress_path,
        {"phase": "completed", "result_path": str(result_path)},
    )
    print(
        f"R48 completed scope={worker['scope']} result={result_path}", flush=True
    )


if __name__ == "__main__":
    main()
