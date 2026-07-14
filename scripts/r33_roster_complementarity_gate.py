"""Run the paired R33 roster-complementarity Alice--Bob abandonment gate."""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from ha_ctse_process import train as train_mod  # noqa: E402
from ha_ctse_process.config_alice_bob_asymmetric import Config  # noqa: E402
from ha_ctse_process.r30_fixed_clock import (  # noqa: E402
    INVALID_SKILL,
    KEEP_TOKEN,
    SET_TOKEN,
    FixedClockAREditPolicy,
)
from ha_ctse_process.r33_interventional_roster_complementarity import (  # noqa: E402
    JointRosterBranch,
    RosterInterventionContext,
    agent_persistent_effect,
    enumerate_final_rosters,
    exact_expected_complementarity_loss,
    exact_roster_probabilities,
    parameter_drift_metrics,
    role_swap_complementarity_u,
    standardized_roster_scores,
)


SCHEMA_VERSION = 1
WINDOW = 10
EPISODE_STEPS = 80
N_AGENTS = 2
N_SKILLS = 4
SOURCE_EPISODES = 24
TRAIN_SOURCE_EPISODES = 16
TRAIN_CONTEXTS = 128
HELDOUT_CONTEXTS = 64
ROSTERS = enumerate_final_rosters(N_SKILLS, N_AGENTS)
REPLICAS = 2
AUX_UPDATES = 8
CONTEXTS_PER_UPDATE = 16
HEAD_LR = 3e-4
GRAD_CLIP = 0.5
NATURAL_EPISODES = 64
POSITION_BINS = 5
STANDARDIZE_EPSILON = 1e-8
PAIR_SHAM_SOURCE = np.asarray([5, 4, 3, 2, 1, 0], dtype=np.int64)

THRESHOLDS = {
    "probability_sum_max_error": 1e-6,
    "natural_high_replay_max_error": 1e-5,
    "paired_initial_parameter_max_abs": 1e-8,
    "score_multiset_max_error": 1e-8,
    "other_parameter_max_abs_drift": 1e-8,
    "keep_probability_max_abs_drift": 1e-8,
    "heldout_expected_alignment_gain": 0.20,
    "heldout_expected_alignment_ci_lower": 0.0,
    "heldout_top2_mass_gain": 0.10,
    "heldout_top2_mass_gain_ci_lower": 0.0,
    "natural_joint_coverage_ratio": 1.10,
    "natural_joint_coverage_gain_ci_lower": 0.0,
    "natural_nonredundant_ratio": 1.15,
    "natural_nonredundant_gain_ci_lower": 0.0,
    "full_sync_set_rate_max": 0.50,
    "set_skill_entropy_norm_min": 0.80,
    "set_skill_share_min": 0.05,
    "lifetime_min_share": 0.05,
}

_RUNTIME_ARRAY_FIELDS = (
    "active_skills",
    "active_duration_indices",
    "duration_remaining",
    "skill_age",
    "has_active_skill",
    "active_team_codes",
    "episode_steps",
    "episode_ids",
    "steps_to_check",
    "low_actor_hxs",
    "low_critic_hxs",
)


def _set_seed(seed: int, device: torch.device) -> None:
    np.random.seed(int(seed) % (2**32 - 1))
    torch.manual_seed(int(seed))
    if device.type == "cuda":
        torch.cuda.manual_seed_all(int(seed))


def _set_eval_mode(agent) -> None:
    seen: set[int] = set()
    for value in vars(agent).values():
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, torch.nn.Module):
            value.eval()


def _capture_policy_runtime(agent) -> dict[str, np.ndarray]:
    return {
        name: np.asarray(getattr(agent, name)).copy()
        for name in _RUNTIME_ARRAY_FIELDS
    }


def _restore_policy_runtime(agent, snapshot: dict[str, np.ndarray]) -> None:
    for name in _RUNTIME_ARRAY_FIELDS:
        getattr(agent, name)[...] = snapshot[name]
    agent._last_low_context[0] = None


def _checkpoint_manifest(path: Path) -> dict[str, Any]:
    loader = getattr(train_mod, "_load_adjacent_run_manifest", None)
    return loader(path) if callable(loader) else {}


def _fail_closed_config(config, metadata: dict[str, Any], manifest: dict[str, Any]) -> None:
    if str(metadata.get("high_controller")) != "r30_fixed_clock_ar_edit":
        raise ValueError("R33 requires a frozen R30 fixed-clock checkpoint")
    if str(metadata.get("scenario")) != "alice_bob_asymmetric_cycles":
        raise ValueError("R33 requires the Alice--Bob source")
    if int(metadata.get("n_agents") or 0) != N_AGENTS:
        raise ValueError("R33 requires exactly two agents")
    if int(metadata.get("n_skills") or 0) != N_SKILLS:
        raise ValueError("R33 requires exactly four skills")
    contract = metadata.get("r30_contract") or {}
    if int(contract.get("k0") or metadata.get("skill_interval") or 0) != WINDOW:
        raise ValueError("R33 requires source k0=W=10")
    algorithm = manifest.get("algorithm_config") if isinstance(manifest, dict) else None
    if not isinstance(algorithm, dict) or "r30_force_refresh_every_check" not in algorithm:
        raise ValueError("R33 cannot verify the adaptive-R30 source")
    if bool(algorithm["r30_force_refresh_every_check"]):
        raise ValueError("R33 rejects the shared-k source")
    required_zero = {
        "alice_bob_semantic_reward_enabled": False,
        "transition_skill_reward_coef": 0.0,
        "alice_bob_progress_reward_coef": 0.0,
    }
    for name, expected in required_zero.items():
        if getattr(config, name, expected) != expected:
            raise ValueError(f"R33 sparse boundary rejects {name}")
    if str(getattr(config, "r28_g1_arm", "off")) != "off":
        raise ValueError("R33 forbids R28 online reward")
    if str(getattr(config, "r29_action_info_mode", "off")) != "off":
        raise ValueError("R33 forbids R29 online reward")
    if str(getattr(config, "r31_effect_mode", "off")) == "real_reward":
        raise ValueError("R33 forbids the retired R31 reward")
    for name in (
        "process_reward_injection",
        "outcome_residual_injection",
        "topology_role_injection",
        "topology_potential_injection",
        "skill_effect_reward_injection",
        "skill_force_reward_injection",
    ):
        if str(getattr(config, name, "none")).lower() != "none":
            raise ValueError(f"R33 forbids {name}")


def _make_agent_and_env(args: argparse.Namespace, *, seed_offset: int = 0):
    checkpoint = Path(args.checkpoint).resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested but CUDA is unavailable")
    device = torch.device(args.device)
    config = Config()
    config.scenario = "alice_bob_asymmetric_cycles"
    config.skill_interval = WINDOW
    config.r31_effect_mode = "off"
    metadata = train_mod.load_checkpoint_metadata(checkpoint)
    train_mod.apply_checkpoint_structure(
        config,
        argparse.Namespace(high_controller="", n_agents=0),
        metadata,
    )
    manifest = _checkpoint_manifest(checkpoint)
    _fail_closed_config(config, metadata, manifest)
    env = train_mod.create_env(
        config,
        scenario=config.scenario,
        seed=int(args.seed) + int(seed_offset),
        rank=0,
        scale_mode="eval",
    )
    _set_seed(int(args.seed) + 500_000 + int(seed_offset), device)
    agent = train_mod.create_agent(
        config,
        argparse.Namespace(device=str(args.device)),
        env,
        num_envs=1,
        state_dim=int(env.state_dim),
    )
    total_steps, update_idx = train_mod.load_checkpoint(
        checkpoint,
        agent,
        load_optimizers=False,
    )
    _set_eval_mode(agent)
    if not isinstance(agent.high, FixedClockAREditPolicy):
        raise RuntimeError("R33 source does not expose the R30 edit policy")
    return checkpoint, config, env, agent, metadata, total_steps, update_idx, device


def _clear_episode_buffers(agent) -> None:
    agent.segments.flush(env_id=0, reason="episode")
    agent.segments.pop_completed()
    agent.high_check_buffer.pop_completed()


def _r30_context_tensors(agent, context: RosterInterventionContext):
    with torch.no_grad():
        values = agent._r30_context_tensors(context.state, context.observations)
    joint_t = values[1].squeeze(0).detach()
    compact = values[2].detach()
    team_vector = values[4].detach()
    omega = values[8].detach() if agent.high_condition_on_omega else None
    relevance = values[11].detach() if agent.use_agent_prototype_relevance else None
    device = agent.device
    return {
        "joint_obs": joint_t,
        "compact": compact,
        "team_vector": team_vector,
        "prev_skills": torch.as_tensor(
            context.prev_skills, dtype=torch.long, device=device
        ),
        "prev_ages": torch.as_tensor(
            context.prev_ages, dtype=torch.long, device=device
        ),
        "prev_active": torch.as_tensor(
            context.prev_active, dtype=torch.bool, device=device
        ),
        "agent_order": torch.as_tensor(
            context.agent_order, dtype=torch.long, device=device
        ),
        "omega": omega,
        "agent_relevance": relevance,
    }


def _natural_token_replay(agent, context: RosterInterventionContext) -> np.ndarray:
    values = _r30_context_tensors(agent, context)
    with torch.no_grad():
        logp, _entropy = agent.high.evaluate_sequence(
            **values,
            token_kind=torch.as_tensor(
                context.natural_token_kind, dtype=torch.long, device=agent.device
            ),
            set_skill=torch.as_tensor(
                context.natural_set_skill, dtype=torch.long, device=agent.device
            ),
        )
    return logp.detach().cpu().numpy().astype(np.float64)


def _stored_prefix_keep_probabilities(
    agent,
    context: RosterInterventionContext,
) -> np.ndarray:
    values = _r30_context_tensors(agent, context)
    working_skills = values["prev_skills"].clone()
    working_ages = values["prev_ages"].clone()
    working_active = values["prev_active"].clone()
    result = np.full(N_AGENTS, np.nan, dtype=np.float64)
    with torch.no_grad():
        for position, raw_agent_id in enumerate(values["agent_order"]):
            agent_id = int(raw_agent_id.item())
            _hidden, keep_logit, _skill_logits, _entropy_logits = agent.high._token_context(
                values["joint_obs"],
                values["compact"],
                values["team_vector"],
                working_skills,
                working_ages,
                working_active,
                agent_id,
                values["omega"],
                values["agent_relevance"],
            )
            if bool(working_active[agent_id].item()):
                result[position] = float(torch.sigmoid(keep_logit).item())
            if int(context.natural_token_kind[position]) == SET_TOKEN:
                working_skills[agent_id] = int(context.natural_set_skill[position])
                working_ages[agent_id] = 0
                working_active[agent_id] = True
    return result


def _collect_context_bank(
    *,
    env,
    agent,
    source_update: int,
    base_seed: int,
    device: torch.device,
) -> tuple[list[RosterInterventionContext], float, np.ndarray]:
    raw_env = env.env
    contexts: list[RosterInterventionContext] = []
    replay_error = 0.0
    for reset_group in range(SOURCE_EPISODES):
        reset_seed = int(base_seed) + reset_group
        _set_seed(reset_seed, device)
        observations, info = env.reset(seed=reset_seed)
        state = np.asarray(info["state"], dtype=np.float32)
        agent.reset_env_state(0)
        done = False
        for block in range(EPISODE_STEPS // WINDOW):
            agent.maybe_assign_skills(
                observations,
                state=state,
                step=block * WINDOW,
                k=WINDOW,
                env_id=0,
                deterministic=False,
                policy_update=int(source_update),
                collect_r31=False,
            )
            row = agent.high_check_buffer.pending[0]
            if row is None or not bool(row.decision_mask):
                raise RuntimeError("R33 context did not start at a real R30 check")
            context = RosterInterventionContext(
                context_id=len(contexts),
                reset_group=reset_group,
                observations=np.asarray(observations, dtype=np.float32).copy(),
                state=state.copy(),
                prev_skills=np.asarray(row.prev_skills, dtype=np.int64).copy(),
                prev_ages=np.asarray(row.prev_ages, dtype=np.int64).copy(),
                prev_active=np.asarray(row.prev_active, dtype=np.bool_).copy(),
                agent_order=np.asarray(row.agent_order, dtype=np.int64).copy(),
                natural_token_kind=np.asarray(row.token_kind, dtype=np.int64).copy(),
                natural_set_skill=np.asarray(row.set_skill, dtype=np.int64).copy(),
                natural_old_token_logp=np.asarray(
                    row.old_token_logp, dtype=np.float64
                ).copy(),
                env_snapshot=copy.deepcopy(raw_env.get_probe_snapshot()),
                policy_runtime=_capture_policy_runtime(agent),
                team_code=int(agent.active_team_codes[0]),
                metadata={"block": block},
            )
            replay = _natural_token_replay(agent, context)
            replay_error = max(
                replay_error,
                float(np.max(np.abs(replay - context.natural_old_token_logp))),
            )
            contexts.append(context)
            for primitive in range(WINDOW):
                actions, _logp, _values = agent.act_low(
                    observations,
                    env_id=0,
                    deterministic=False,
                    state=state,
                )
                observations, reward, terminated, truncated, next_info = env.step(actions)
                state = np.asarray(next_info["next_state"], dtype=np.float32)
                done = bool(terminated or truncated)
                agent.record_environment_step(
                    0,
                    reward=float(reward),
                    next_obs=observations,
                    next_state=state,
                    done=done,
                    collect_r31=False,
                )
                if done and not (
                    block == EPISODE_STEPS // WINDOW - 1
                    and primitive == WINDOW - 1
                ):
                    raise RuntimeError("Alice--Bob ended before a complete R33 source window")
        if not done:
            raise RuntimeError("R33 source episode did not terminate at 80 steps")
        _clear_episode_buffers(agent)
    if len(contexts) != SOURCE_EPISODES * (EPISODE_STEPS // WINDOW):
        raise RuntimeError(f"R33 context count mismatch: {len(contexts)}")
    train = [row for row in contexts if row.reset_group < TRAIN_SOURCE_EPISODES]
    heldout = [row for row in contexts if row.reset_group >= TRAIN_SOURCE_EPISODES]
    if len(train) != TRAIN_CONTEXTS or len(heldout) != HELDOUT_CONTEXTS:
        raise RuntimeError("R33 episode-disjoint context split is not 128/64")
    keep_probabilities = np.stack(
        [_stored_prefix_keep_probabilities(agent, row) for row in contexts]
    )
    return contexts, replay_error, keep_probabilities


def _run_roster_branch(
    *,
    env,
    agent,
    context: RosterInterventionContext,
    roster: np.ndarray,
    replica: int,
    branch_seed: int,
    device: torch.device,
) -> JointRosterBranch:
    raw_env = env.env
    raw_env.set_probe_snapshot(copy.deepcopy(context.env_snapshot))
    raw_env.np_random = np.random.default_rng(int(branch_seed))
    _restore_policy_runtime(agent, dict(context.policy_runtime))
    agent.active_skills[0, :] = np.asarray(roster, dtype=np.int64)
    agent.has_active_skill[0, :] = True
    _set_seed(int(branch_seed), device)
    observations = np.asarray(context.observations, dtype=np.float32).copy()
    state = np.asarray(context.state, dtype=np.float32).copy()
    effect_views = [raw_env.intrinsic_effect_view()]
    for primitive in range(WINDOW):
        actions, _logp, _values = agent.act_low(
            observations,
            env_id=0,
            deterministic=False,
            state=state,
        )
        observations, _ignored_reward, terminated, truncated, info = env.step(actions)
        state = np.asarray(info["next_state"], dtype=np.float32)
        effect_views.append(raw_env.intrinsic_effect_view())
        if (terminated or truncated) and primitive != WINDOW - 1:
            raise RuntimeError("R33 roster branch ended before W=10")
    effect = np.asarray(
        agent_persistent_effect(np.asarray(effect_views, dtype=np.float64)),
        dtype=np.float64,
    )
    return JointRosterBranch(
        context_id=int(context.context_id),
        roster=np.asarray(roster, dtype=np.int64).copy(),
        replica=int(replica),
        effect=effect,
        steps=WINDOW,
        branch_seed=int(branch_seed),
    )


def _collect_shared_interventions(
    *,
    env,
    agent,
    contexts: list[RosterInterventionContext],
    base_seed: int,
    device: torch.device,
) -> tuple[np.ndarray, dict[str, Any]]:
    effects = np.empty(
        (len(contexts), N_SKILLS, N_SKILLS, REPLICAS, N_AGENTS, 4),
        dtype=np.float64,
    )
    branch_count = 0
    branch_steps = 0
    replica_seed_pairs: list[tuple[int, int]] = []
    for context_index, context in enumerate(contexts):
        seeds = (
            int(base_seed) + 1_000_000 + int(context.context_id) * 2,
            int(base_seed) + 1_000_000 + int(context.context_id) * 2 + 1,
        )
        replica_seed_pairs.append(seeds)
        for replica, branch_seed in enumerate(seeds):
            for roster in ROSTERS:
                branch = _run_roster_branch(
                    env=env,
                    agent=agent,
                    context=context,
                    roster=roster,
                    replica=replica,
                    branch_seed=branch_seed,
                    device=device,
                )
                left, right = (int(value) for value in roster)
                effects[context_index, left, right, replica] = branch.effect
                branch_count += 1
                branch_steps += int(branch.steps)
    expected = len(contexts) * len(ROSTERS) * REPLICAS
    if branch_count != expected:
        raise RuntimeError("R33 shared branch count mismatch")
    replica_independent = all(left != right for left, right in replica_seed_pairs)
    unique_replica_streams = len(
        {seed for pair in replica_seed_pairs for seed in pair}
    ) == 2 * len(contexts)
    return effects, {
        "branch_count": branch_count,
        "primitive_steps": branch_steps,
        "branch_length": WINDOW,
        "within_replica_roster_crn": True,
        "replica_independent": replica_independent,
        "unique_context_replica_streams": unique_replica_streams,
    }


def _score_tables(roster_effects: np.ndarray) -> dict[str, Any]:
    n_contexts = int(roster_effects.shape[0])
    pair_scores = np.empty((n_contexts, 6), dtype=np.float64)
    true_raw = np.empty((n_contexts, len(ROSTERS)), dtype=np.float64)
    true_standardized = np.empty_like(true_raw)
    sham_raw = np.empty_like(true_raw)
    sham_standardized = np.empty_like(true_raw)
    pair_indices: np.ndarray | None = None
    multiset_error = 0.0
    for context_index in range(n_contexts):
        scores, pairs = role_swap_complementarity_u(
            np.asarray(roster_effects[context_index], dtype=np.float64)
        )
        scores = np.asarray(scores, dtype=np.float64)
        if pair_indices is None:
            pair_indices = np.asarray(pairs, dtype=np.int64)
        elif not np.array_equal(pair_indices, pairs):
            raise RuntimeError("R33 unordered pair order changed")
        pair_scores[context_index] = scores
        true_raw[context_index], true_standardized[context_index] = (
            standardized_roster_scores(
                scores,
                pairs,
                n_skills=N_SKILLS,
                epsilon=STANDARDIZE_EPSILON,
            )
        )
        sham_raw[context_index], sham_standardized[context_index] = (
            standardized_roster_scores(
                scores,
                pairs,
                n_skills=N_SKILLS,
                pair_source_indices=PAIR_SHAM_SOURCE,
                epsilon=STANDARDIZE_EPSILON,
            )
        )
        multiset_error = max(
            multiset_error,
            float(
                np.max(
                    np.abs(
                        np.sort(true_standardized[context_index])
                        - np.sort(sham_standardized[context_index])
                    )
                )
            ),
        )
    if pair_indices is None:
        raise RuntimeError("R33 score table is empty")
    return {
        "pair_scores": pair_scores,
        "pairs": pair_indices,
        "true_raw": true_raw,
        "true_standardized": true_standardized,
        "sham_raw": sham_raw,
        "sham_standardized": sham_standardized,
        "score_multiset_max_error": multiset_error,
    }


def _parameter_snapshot(agent) -> dict[str, torch.Tensor]:
    snapshot: dict[str, torch.Tensor] = {}
    seen_parameters: set[int] = set()
    for attribute, module in sorted(vars(agent).items()):
        if not isinstance(module, torch.nn.Module):
            continue
        for name, parameter in module.named_parameters():
            if id(parameter) in seen_parameters:
                continue
            seen_parameters.add(id(parameter))
            snapshot[f"{attribute}.{name}"] = parameter.detach().cpu().clone()
    if "high.skill_head.weight" not in snapshot or "high.skill_head.bias" not in snapshot:
        raise RuntimeError("R33 could not inventory high.skill_head")
    return snapshot


def _initial_parameter_difference(
    left: dict[str, torch.Tensor],
    right: dict[str, torch.Tensor],
) -> float:
    if set(left) != set(right):
        raise RuntimeError("paired R33 arms expose different parameter sets")
    return max(
        float(torch.max(torch.abs(left[name] - right[name])).item())
        for name in left
    )


def _roster_probabilities(
    agent,
    context: RosterInterventionContext,
) -> torch.Tensor:
    values = _r30_context_tensors(agent, context)
    return exact_roster_probabilities(
        agent.high,
        **values,
        final_rosters=ROSTERS,
    )


def _freeze_to_skill_head(agent) -> list[torch.nn.Parameter]:
    seen: set[int] = set()
    for value in vars(agent).values():
        if not isinstance(value, torch.nn.Module):
            continue
        for parameter in value.parameters():
            if id(parameter) in seen:
                continue
            seen.add(id(parameter))
            parameter.requires_grad_(False)
            parameter.grad = None
    selected = list(agent.high.skill_head.parameters())
    if len(selected) != 2:
        raise RuntimeError("R33 expected skill_head weight and bias")
    for parameter in selected:
        parameter.requires_grad_(True)
    return selected


def _train_arm(
    *,
    arm: str,
    agent,
    train_contexts: list[RosterInterventionContext],
    scores: np.ndarray,
    all_contexts: list[RosterInterventionContext],
    source_keep_probabilities: np.ndarray,
) -> dict[str, Any]:
    if arm not in {"real_complementarity", "pair_sham"}:
        raise ValueError(f"unknown R33 arm {arm!r}")
    if len(train_contexts) != TRAIN_CONTEXTS:
        raise ValueError("R33 train arm requires exactly 128 contexts")
    if scores.shape != (TRAIN_CONTEXTS, len(ROSTERS)):
        raise ValueError("R33 train score table has the wrong shape")
    before = _parameter_snapshot(agent)
    selected = _freeze_to_skill_head(agent)
    optimizer = torch.optim.Adam(selected, lr=HEAD_LR)
    losses: list[float] = []
    grad_norms: list[float] = []
    probability_sum_max_error = 0.0
    non_head_gradient_tensor_count = 0
    non_head_gradient_max_abs = 0.0
    optimizer_calls = 0
    nonzero_gradient_updates = 0
    for update in range(AUX_UPDATES):
        start = update * CONTEXTS_PER_UPDATE
        stop = start + CONTEXTS_PER_UPDATE
        batch = train_contexts[start:stop]
        if len(batch) != CONTEXTS_PER_UPDATE:
            raise RuntimeError("R33 auxiliary batch is not 16 contexts")
        probabilities = torch.stack(
            [_roster_probabilities(agent, context) for context in batch]
        )
        probability_sum_max_error = max(
            probability_sum_max_error,
            float(
                torch.max(torch.abs(probabilities.sum(dim=-1) - 1.0))
                .detach()
                .cpu()
                .item()
            ),
        )
        loss = exact_expected_complementarity_loss(
            probabilities,
            scores[start:stop],
        )
        if not bool(torch.isfinite(loss).item()):
            raise RuntimeError("R33 exact-expectation loss became non-finite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        selected_sq = 0.0
        selected_finite = True
        selected_ids = {id(parameter) for parameter in selected}
        seen: set[int] = set()
        for value in vars(agent).values():
            if not isinstance(value, torch.nn.Module):
                continue
            for parameter in value.parameters():
                if id(parameter) in seen:
                    continue
                seen.add(id(parameter))
                if parameter.grad is None:
                    continue
                grad = parameter.grad.detach()
                if id(parameter) in selected_ids:
                    selected_finite = selected_finite and bool(torch.isfinite(grad).all())
                    selected_sq += float(torch.sum(grad.float() ** 2).item())
                else:
                    non_head_gradient_tensor_count += 1
                    non_head_gradient_max_abs = max(
                        non_head_gradient_max_abs,
                        float(torch.max(torch.abs(grad)).item()),
                    )
        if not selected_finite:
            raise RuntimeError("R33 skill-head gradient became non-finite")
        gradient_norm = math.sqrt(selected_sq)
        if gradient_norm > 0.0:
            nonzero_gradient_updates += 1
        torch.nn.utils.clip_grad_norm_(selected, GRAD_CLIP)
        optimizer.step()
        optimizer_calls += 1
        losses.append(float(loss.detach().cpu().item()))
        grad_norms.append(gradient_norm)
    after = _parameter_snapshot(agent)
    drift = parameter_drift_metrics(
        before,
        after,
        selected_prefix="high.skill_head",
    )
    keep_after = np.stack(
        [_stored_prefix_keep_probabilities(agent, row) for row in all_contexts]
    )
    keep_mask = np.isfinite(source_keep_probabilities) & np.isfinite(keep_after)
    if not bool(np.any(keep_mask)):
        raise RuntimeError("R33 found no active stored-prefix KEEP probabilities")
    keep_probability_max_abs_drift = float(
        np.max(
            np.abs(
                keep_after[keep_mask]
                - source_keep_probabilities[keep_mask]
            )
        )
    )
    final_probability_error = 0.0
    with torch.no_grad():
        for context in all_contexts:
            probabilities = _roster_probabilities(agent, context)
            final_probability_error = max(
                final_probability_error,
                float(torch.abs(probabilities.sum() - 1.0).cpu().item()),
            )
    probability_sum_max_error = max(
        probability_sum_max_error,
        final_probability_error,
    )
    finite_optimizer = bool(
        len(losses) == AUX_UPDATES
        and len(grad_norms) == AUX_UPDATES
        and np.all(np.isfinite(losses))
        and np.all(np.isfinite(grad_norms))
    )
    nonzero_gradient_implies_drift = bool(
        nonzero_gradient_updates == 0 or drift["selected_max_abs"] > 0.0
    )
    return {
        "arm": arm,
        "optimizer_calls": optimizer_calls,
        "losses": np.asarray(losses, dtype=np.float64),
        "gradient_norms": np.asarray(grad_norms, dtype=np.float64),
        "nonzero_gradient_updates": nonzero_gradient_updates,
        "finite_optimizer": finite_optimizer,
        "nonzero_gradient_implies_drift": nonzero_gradient_implies_drift,
        "probability_sum_max_error": probability_sum_max_error,
        "parameter_drift": drift,
        "keep_probability_max_abs_drift": keep_probability_max_abs_drift,
        "non_head_gradient_tensor_count": non_head_gradient_tensor_count,
        "non_head_gradient_max_abs": non_head_gradient_max_abs,
        "task_reward_objective_reads": 0,
        "low_updates": 0,
        "critic_updates": 0,
        "posterior_updates": 0,
        "normal_high_ppo_updates": 0,
    }


def _cluster_bootstrap_ci(
    values: np.ndarray,
    cluster_ids: np.ndarray,
    *,
    repetitions: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    cluster_ids = np.asarray(cluster_ids, dtype=np.int64).reshape(-1)
    if values.shape != cluster_ids.shape or not np.all(np.isfinite(values)):
        raise ValueError("cluster bootstrap inputs are invalid")
    clusters = np.unique(cluster_ids)
    rows = {int(cluster): np.flatnonzero(cluster_ids == cluster) for cluster in clusters}
    draws = np.empty(int(repetitions), dtype=np.float64)
    for draw in range(int(repetitions)):
        sampled = rng.choice(clusters, size=clusters.size, replace=True)
        index = np.concatenate([rows[int(cluster)] for cluster in sampled])
        draws[draw] = float(np.mean(values[index]))
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def _heldout_alignment(
    *,
    real_agent,
    sham_agent,
    contexts: list[RosterInterventionContext],
    true_standardized: np.ndarray,
    pair_scores: np.ndarray,
    pairs: np.ndarray,
    repetitions: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    if len(contexts) != HELDOUT_CONTEXTS:
        raise ValueError("R33 heldout alignment requires 64 contexts")
    with torch.no_grad():
        real_probability = np.stack(
            [
                _roster_probabilities(real_agent, context).detach().cpu().numpy()
                for context in contexts
            ]
        ).astype(np.float64)
        sham_probability = np.stack(
            [
                _roster_probabilities(sham_agent, context).detach().cpu().numpy()
                for context in contexts
            ]
        ).astype(np.float64)
    real_value = np.sum(real_probability * true_standardized, axis=1)
    sham_value = np.sum(sham_probability * true_standardized, axis=1)
    value_gain = real_value - sham_value
    real_top2 = np.zeros(len(contexts), dtype=np.float64)
    sham_top2 = np.zeros(len(contexts), dtype=np.float64)
    top2_pair_indices: list[list[int]] = []
    for index in range(len(contexts)):
        top2 = np.argsort(-pair_scores[index], kind="stable")[:2]
        top2_pair_indices.append([int(value) for value in top2])
        roster_indices: list[int] = []
        for pair_index in top2:
            left, right = (int(value) for value in pairs[int(pair_index)])
            roster_indices.extend([left * N_SKILLS + right, right * N_SKILLS + left])
        real_top2[index] = float(np.sum(real_probability[index, roster_indices]))
        sham_top2[index] = float(np.sum(sham_probability[index, roster_indices]))
    top2_gain = real_top2 - sham_top2
    clusters = np.asarray([row.reset_group for row in contexts], dtype=np.int64)
    return {
        "real_probability": real_probability,
        "sham_probability": sham_probability,
        "real_expected_value": real_value,
        "sham_expected_value": sham_value,
        "expected_value_gain": value_gain,
        "expected_value_gain_mean": float(np.mean(value_gain)),
        "expected_value_gain_ci95": _cluster_bootstrap_ci(
            value_gain,
            clusters,
            repetitions=repetitions,
            rng=rng,
        ),
        "real_top2_mass": real_top2,
        "sham_top2_mass": sham_top2,
        "top2_mass_gain": top2_gain,
        "top2_mass_gain_mean": float(np.mean(top2_gain)),
        "top2_mass_gain_ci95": _cluster_bootstrap_ci(
            top2_gain,
            clusters,
            repetitions=repetitions,
            rng=rng,
        ),
        "top2_pair_indices": top2_pair_indices,
        "cluster_ids": clusters,
    }


def _joint_position_cell(effect_view: np.ndarray) -> int:
    positions = np.asarray(effect_view, dtype=np.float64)
    if positions.shape != (N_AGENTS, 2):
        raise ValueError("R33 coverage requires normalized [2,2] positions")
    clipped = np.clip(positions, 0.0, np.nextafter(1.0, 0.0))
    bins = np.floor(clipped * POSITION_BINS).astype(np.int64).reshape(-1)
    cell = 0
    for value in bins:
        cell = cell * POSITION_BINS + int(value)
    return cell


def _agent_position_cells(effect_view: np.ndarray) -> tuple[int, int]:
    positions = np.asarray(effect_view, dtype=np.float64)
    clipped = np.clip(positions, 0.0, np.nextafter(1.0, 0.0))
    bins = np.floor(clipped * POSITION_BINS).astype(np.int64)
    return tuple(
        int(row[0]) * POSITION_BINS + int(row[1])
        for row in bins
    )


def _natural_transport(
    *,
    env,
    agent,
    source_update: int,
    base_seed: int,
    device: torch.device,
) -> dict[str, Any]:
    raw_env = env.env
    coverage_by_reset: list[float] = []
    nonredundant_by_reset: list[float] = []
    global_joint_cells: set[int] = set()
    task_reward: list[float] = []
    final_task_metrics: list[dict[str, float]] = []
    all_rows = []
    for episode in range(NATURAL_EPISODES):
        reset_seed = int(base_seed) + 30_000_000 + episode
        _set_seed(reset_seed, device)
        observations, info = env.reset(seed=reset_seed)
        state = np.asarray(info["state"], dtype=np.float32)
        agent.reset_env_state(0)
        joint_cells: set[int] = set()
        agent_cells = [set(), set()]
        episode_reward = 0.0
        last_reward_info: dict[str, Any] = {}
        done = False
        for block in range(EPISODE_STEPS // WINDOW):
            agent.maybe_assign_skills(
                observations,
                state=state,
                step=block * WINDOW,
                k=WINDOW,
                env_id=0,
                deterministic=False,
                policy_update=int(source_update),
                collect_r31=False,
            )
            for primitive in range(WINDOW):
                actions, _logp, _values = agent.act_low(
                    observations,
                    env_id=0,
                    deterministic=False,
                    state=state,
                )
                observations, reward, terminated, truncated, next_info = env.step(actions)
                state = np.asarray(next_info["next_state"], dtype=np.float32)
                view = raw_env.intrinsic_effect_view()
                joint_cells.add(_joint_position_cell(view))
                left_cell, right_cell = _agent_position_cells(view)
                agent_cells[0].add(left_cell)
                agent_cells[1].add(right_cell)
                episode_reward += float(reward)
                last_reward_info = dict(next_info.get("reward_info", {}) or {})
                done = bool(terminated or truncated)
                agent.record_environment_step(
                    0,
                    reward=float(reward),
                    next_obs=observations,
                    next_state=state,
                    done=done,
                    collect_r31=False,
                )
                if done and not (
                    block == EPISODE_STEPS // WINDOW - 1
                    and primitive == WINDOW - 1
                ):
                    raise RuntimeError("R33 natural episode ended before 80 steps")
        if not done:
            raise RuntimeError("R33 natural episode did not terminate at 80 steps")
        coverage_by_reset.append(
            len(joint_cells) / float(POSITION_BINS ** (N_AGENTS * 2))
        )
        nonredundant_by_reset.append(
            len(agent_cells[0].symmetric_difference(agent_cells[1]))
            / float(POSITION_BINS**2)
        )
        global_joint_cells.update(joint_cells)
        task_reward.append(episode_reward)
        final_task_metrics.append(
            {
                name: float(last_reward_info.get(name, 0.0))
                for name in (
                    "alice_bob_targets_completed",
                    "alice_bob_button_occupancy_fraction",
                    "alice_bob_target_contact_fraction",
                    "alice_bob_joint_coordination_fraction",
                )
            }
        )
        all_rows.extend(agent.high_check_buffer.pop_completed())
        agent.segments.flush(env_id=0, reason="episode")
        agent.segments.pop_completed()
    normal_rows = [
        row
        for row in all_rows
        if row.decision_mask and bool(np.all(np.asarray(row.prev_active)))
    ]
    full_sync = [
        float(np.all(np.asarray(row.token_kind, dtype=np.int64) == SET_TOKEN))
        for row in normal_rows
    ]
    switch_skills: list[int] = []
    spell_gt_4k0 = 0
    spell_le_4k0 = 0
    for row in normal_rows:
        for position, agent_id in enumerate(np.asarray(row.agent_order, dtype=np.int64)):
            age = int(row.prev_ages[int(agent_id)])
            token = int(row.token_kind[position])
            if token == SET_TOKEN:
                switch_skills.append(int(row.set_skill[position]))
                if age <= 4 * WINDOW:
                    spell_le_4k0 += 1
            elif token == KEEP_TOKEN and age == 4 * WINDOW:
                spell_gt_4k0 += 1
    if switch_skills:
        counts = np.bincount(
            np.asarray(switch_skills, dtype=np.int64),
            minlength=N_SKILLS,
        ).astype(np.float64)
        shares = counts / float(np.sum(counts))
        positive = shares[shares > 0.0]
        entropy_norm = float(
            -np.sum(positive * np.log(positive)) / math.log(N_SKILLS)
        )
    else:
        counts = np.zeros(N_SKILLS, dtype=np.float64)
        shares = counts.copy()
        entropy_norm = 0.0
    spell_total = spell_gt_4k0 + spell_le_4k0
    lifetime_breadth = (
        min(spell_gt_4k0, spell_le_4k0) / float(spell_total)
        if spell_total
        else 0.0
    )
    task_diagnostics = {"mean_sparse_task_reward": float(np.mean(task_reward))}
    for name in final_task_metrics[0]:
        task_diagnostics[f"mean_final_{name}"] = float(
            np.mean([row[name] for row in final_task_metrics])
        )
    return {
        "episode_count": NATURAL_EPISODES,
        "primitive_steps": NATURAL_EPISODES * EPISODE_STEPS,
        "coverage_by_reset": np.asarray(coverage_by_reset, dtype=np.float64),
        "coverage_union_cells": len(global_joint_cells),
        "coverage_union_fraction": len(global_joint_cells)
        / float(POSITION_BINS ** (N_AGENTS * 2)),
        "nonredundant_by_reset": np.asarray(
            nonredundant_by_reset, dtype=np.float64
        ),
        "nonredundant_mean": float(np.mean(nonredundant_by_reset)),
        "normal_decision_rows": len(normal_rows),
        "full_sync_set_rate": float(np.mean(full_sync)) if full_sync else 1.0,
        "set_skill_counts": counts,
        "set_skill_shares": shares,
        "set_skill_share_min": float(np.min(shares)) if shares.size else 0.0,
        "set_skill_entropy_norm": entropy_norm,
        "spell_gt_4k0_count": spell_gt_4k0,
        "spell_le_4k0_count": spell_le_4k0,
        "lifetime_min_share": lifetime_breadth,
        "task_diagnostics_only": task_diagnostics,
    }


def _gate_decision(
    *,
    m0: bool,
    m1: bool,
    m2: bool,
    m3: bool,
) -> tuple[str, str]:
    if not m0:
        return (
            "INVALID_R33_IMPLEMENTATION",
            "repair only the concrete implementation defect",
        )
    if not m1:
        return (
            "FAIL_M1_RETIRE_R33_IRSC",
            "retire direct intervention-scored roster complementarity selection",
        )
    if not m2:
        return (
            "FAIL_M2_COUNTERFACTUAL_ONLY",
            "retire counterfactual-only roster fitting",
        )
    if not m3:
        return (
            "FAIL_M3_R30_COLLAPSE",
            "retire R33 as skill-supply or lifetime collapse",
        )
    return (
        "PASS_R33_IRSC",
        "authorize only preparation of a sparse-source real versus pair-sham comparison",
    )


def _natural_summary(value: dict[str, Any]) -> dict[str, Any]:
    return dict(value)


def run(args: argparse.Namespace) -> dict[str, Any]:
    print("[R33] phase=source_context_bank", flush=True)
    source = _make_agent_and_env(args, seed_offset=0)
    (
        checkpoint,
        _config,
        source_env,
        source_agent,
        metadata,
        source_total_steps,
        source_update,
        device,
    ) = source
    try:
        contexts, source_replay_error, source_keep_probabilities = (
            _collect_context_bank(
                env=source_env,
                agent=source_agent,
                source_update=source_update,
                base_seed=int(args.seed),
                device=device,
            )
        )
        print("[R33] phase=shared_complete_roster_interventions", flush=True)
        roster_effects, intervention_counts = _collect_shared_interventions(
            env=source_env,
            agent=source_agent,
            contexts=contexts,
            base_seed=int(args.seed),
            device=device,
        )
    finally:
        source_env.close()
    score_tables = _score_tables(roster_effects)
    train_contexts = contexts[:TRAIN_CONTEXTS]
    heldout_contexts = contexts[TRAIN_CONTEXTS:]

    del source_agent, source_env, source
    if device.type == "cuda":
        torch.cuda.empty_cache()

    print("[R33] phase=create_paired_high_arms", flush=True)
    real = _make_agent_and_env(args, seed_offset=10_000)
    sham = _make_agent_and_env(args, seed_offset=20_000)
    real_env, real_agent = real[2], real[3]
    sham_env, sham_agent = sham[2], sham[3]
    real_before = _parameter_snapshot(real_agent)
    sham_before = _parameter_snapshot(sham_agent)
    initial_parameter_difference = _initial_parameter_difference(
        real_before,
        sham_before,
    )
    try:
        print("[R33] phase=real_exact_expectation_updates", flush=True)
        real_train = _train_arm(
            arm="real_complementarity",
            agent=real_agent,
            train_contexts=train_contexts,
            scores=score_tables["true_standardized"][:TRAIN_CONTEXTS],
            all_contexts=contexts,
            source_keep_probabilities=source_keep_probabilities,
        )
        print("[R33] phase=pair_sham_exact_expectation_updates", flush=True)
        sham_train = _train_arm(
            arm="pair_sham",
            agent=sham_agent,
            train_contexts=train_contexts,
            scores=score_tables["sham_standardized"][:TRAIN_CONTEXTS],
            all_contexts=contexts,
            source_keep_probabilities=source_keep_probabilities,
        )
        bootstrap_rng = np.random.default_rng(int(args.seed) + 40_000_000)
        print("[R33] phase=heldout_exact_distribution", flush=True)
        alignment = _heldout_alignment(
            real_agent=real_agent,
            sham_agent=sham_agent,
            contexts=heldout_contexts,
            true_standardized=score_tables["true_standardized"][TRAIN_CONTEXTS:],
            pair_scores=score_tables["pair_scores"][TRAIN_CONTEXTS:],
            pairs=score_tables["pairs"],
            repetitions=int(args.bootstrap_repetitions),
            rng=bootstrap_rng,
        )
        print("[R33] phase=paired_natural_transport", flush=True)
        real_natural = _natural_transport(
            env=real_env,
            agent=real_agent,
            source_update=source_update,
            base_seed=int(args.seed),
            device=device,
        )
        sham_natural = _natural_transport(
            env=sham_env,
            agent=sham_agent,
            source_update=source_update,
            base_seed=int(args.seed),
            device=device,
        )
    finally:
        real_env.close()
        sham_env.close()

    exact_shared_branches = len(contexts) * len(ROSTERS) * REPLICAS
    finite_arm_fields = all(
        bool(arm["finite_optimizer"])
        for arm in (real_train, sham_train)
    )
    scoped_gradients = all(
        int(arm["non_head_gradient_tensor_count"]) == 0
        and float(arm["non_head_gradient_max_abs"]) == 0.0
        for arm in (real_train, sham_train)
    )
    other_parameters_static = all(
        float(arm["parameter_drift"]["other_max_abs"])
        <= THRESHOLDS["other_parameter_max_abs_drift"]
        for arm in (real_train, sham_train)
    )
    no_forbidden_updates = all(
        int(arm[name]) == 0
        for arm in (real_train, sham_train)
        for name in (
            "task_reward_objective_reads",
            "low_updates",
            "critic_updates",
            "posterior_updates",
            "normal_high_ppo_updates",
        )
    )
    max_probability_error = max(
        float(real_train["probability_sum_max_error"]),
        float(sham_train["probability_sum_max_error"]),
    )
    m0_checks = {
        "source_context_count": len(contexts) == 192,
        "train_context_count": len(train_contexts) == TRAIN_CONTEXTS,
        "heldout_context_count": len(heldout_contexts) == HELDOUT_CONTEXTS,
        "shared_branch_count": (
            intervention_counts["branch_count"] == exact_shared_branches
        ),
        "branch_length_and_steps": (
            intervention_counts["branch_length"] == WINDOW
            and intervention_counts["primitive_steps"]
            == exact_shared_branches * WINDOW
        ),
        "within_replica_roster_crn": bool(
            intervention_counts["within_replica_roster_crn"]
        ),
        "replicas_independent": bool(
            intervention_counts["replica_independent"]
            and intervention_counts["unique_context_replica_streams"]
        ),
        "probability_enumeration": (
            max_probability_error
            <= THRESHOLDS["probability_sum_max_error"]
        ),
        "source_natural_high_replay": (
            source_replay_error
            <= THRESHOLDS["natural_high_replay_max_error"]
        ),
        "paired_initial_parameters": (
            initial_parameter_difference
            <= THRESHOLDS["paired_initial_parameter_max_abs"]
        ),
        "score_multiset_parity": (
            score_tables["score_multiset_max_error"]
            <= THRESHOLDS["score_multiset_max_error"]
        ),
        "optimizer_calls": (
            real_train["optimizer_calls"] == AUX_UPDATES
            and sham_train["optimizer_calls"] == AUX_UPDATES
        ),
        "finite_loss_and_gradients": finite_arm_fields,
        "nonzero_gradient_steps_move_head": (
            real_train["nonzero_gradient_implies_drift"]
            and sham_train["nonzero_gradient_implies_drift"]
        ),
        "gradient_scope_skill_head_only": scoped_gradients,
        "all_other_parameters_static": other_parameters_static,
        "stored_prefix_keep_probability_static": all(
            float(arm["keep_probability_max_abs_drift"])
            <= THRESHOLDS["keep_probability_max_abs_drift"]
            for arm in (real_train, sham_train)
        ),
        "no_forbidden_updates": no_forbidden_updates,
        "natural_episode_counts": (
            real_natural["episode_count"] == NATURAL_EPISODES
            and sham_natural["episode_count"] == NATURAL_EPISODES
        ),
    }
    m0 = all(m0_checks.values())

    expected_gain = float(alignment["expected_value_gain_mean"])
    expected_ci = alignment["expected_value_gain_ci95"]
    top2_gain = float(alignment["top2_mass_gain_mean"])
    top2_ci = alignment["top2_mass_gain_ci95"]
    m1 = bool(
        expected_gain >= THRESHOLDS["heldout_expected_alignment_gain"]
        and expected_ci[0] > THRESHOLDS["heldout_expected_alignment_ci_lower"]
        and top2_gain >= THRESHOLDS["heldout_top2_mass_gain"]
        and top2_ci[0] > THRESHOLDS["heldout_top2_mass_gain_ci_lower"]
    )

    coverage_ratio = float(real_natural["coverage_union_fraction"]) / (
        float(sham_natural["coverage_union_fraction"]) + 1e-12
    )
    coverage_gain = (
        np.asarray(real_natural["coverage_by_reset"], dtype=np.float64)
        - np.asarray(sham_natural["coverage_by_reset"], dtype=np.float64)
    )
    coverage_gain_ci = _cluster_bootstrap_ci(
        coverage_gain,
        np.arange(NATURAL_EPISODES, dtype=np.int64),
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
    )
    nonredundant_ratio = float(real_natural["nonredundant_mean"]) / (
        float(sham_natural["nonredundant_mean"]) + 1e-12
    )
    nonredundant_gain = (
        np.asarray(real_natural["nonredundant_by_reset"], dtype=np.float64)
        - np.asarray(sham_natural["nonredundant_by_reset"], dtype=np.float64)
    )
    nonredundant_gain_ci = _cluster_bootstrap_ci(
        nonredundant_gain,
        np.arange(NATURAL_EPISODES, dtype=np.int64),
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
    )
    m2 = bool(
        coverage_ratio >= THRESHOLDS["natural_joint_coverage_ratio"]
        and coverage_gain_ci[0]
        > THRESHOLDS["natural_joint_coverage_gain_ci_lower"]
        and nonredundant_ratio >= THRESHOLDS["natural_nonredundant_ratio"]
        and nonredundant_gain_ci[0]
        > THRESHOLDS["natural_nonredundant_gain_ci_lower"]
    )

    m3 = bool(
        real_natural["full_sync_set_rate"]
        <= THRESHOLDS["full_sync_set_rate_max"]
        and real_natural["set_skill_entropy_norm"]
        >= THRESHOLDS["set_skill_entropy_norm_min"]
        and real_natural["set_skill_share_min"]
        >= THRESHOLDS["set_skill_share_min"]
        and real_natural["lifetime_min_share"]
        >= THRESHOLDS["lifetime_min_share"]
    )
    status, next_action = _gate_decision(m0=m0, m1=m1, m2=m2, m3=m3)
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment": "R33 residualized interventional role-swap complementarity gate",
        "status": status,
        "authorized_next_action": next_action,
        "scope": "single paired Alice-Bob mechanism seed; no task-efficacy claim",
        "seed": int(args.seed),
        "source": {
            "checkpoint": str(checkpoint),
            "checkpoint_total_steps": int(source_total_steps),
            "checkpoint_update": int(source_update),
            "high_controller": metadata.get("high_controller"),
            "environment": "alice_bob_asymmetric_cycles",
            "external_reward": "diagnostic_only_never_enters_score_loss_or_gradient",
            "natural_high_replay_max_error": source_replay_error,
            "paired_arm_initial_max_abs_parameter_difference": initial_parameter_difference,
        },
        "contract": {
            "source_natural_episodes": SOURCE_EPISODES,
            "source_natural_steps": SOURCE_EPISODES * EPISODE_STEPS,
            "contexts": len(contexts),
            "train_contexts": TRAIN_CONTEXTS,
            "heldout_contexts": HELDOUT_CONTEXTS,
            "joint_rosters_per_context": len(ROSTERS),
            "replicas_per_roster": REPLICAS,
            "window": WINDOW,
            "shared_train_intervention_steps": (
                TRAIN_CONTEXTS * len(ROSTERS) * REPLICAS * WINDOW
            ),
            "shared_heldout_intervention_steps": (
                HELDOUT_CONTEXTS * len(ROSTERS) * REPLICAS * WINDOW
            ),
            "auxiliary_updates_per_arm": AUX_UPDATES,
            "contexts_per_update": CONTEXTS_PER_UPDATE,
            "head_lr": HEAD_LR,
            "gradient_clip": GRAD_CLIP,
            "updated_parameters": "FixedClockAREditPolicy.skill_head_only",
            "natural_episodes_per_arm": NATURAL_EPISODES,
            "natural_steps_per_arm": NATURAL_EPISODES * EPISODE_STEPS,
            "total_environment_steps": (
                SOURCE_EPISODES * EPISODE_STEPS
                + len(contexts) * len(ROSTERS) * REPLICAS * WINDOW
                + 2 * NATURAL_EPISODES * EPISODE_STEPS
            ),
            "bootstrap_repetitions": int(args.bootstrap_repetitions),
            "bootstrap_seed": int(args.seed) + 40_000_000,
            "pair_sham_source_indices": PAIR_SHAM_SOURCE,
            "score": (
                "per-replica two-way roster residual; antisymmetric role-swap "
                "cross-replica U minus symmetric-orientation cross-replica U"
            ),
            "score_standardization": "population_std_plus_1e-8",
            "task_reward_objective_reads": 0,
            "device": str(device),
            "result_artifacts": 1,
        },
        "thresholds": THRESHOLDS,
        "gates": {"M0": m0, "M1": m1, "M2": m2, "M3": m3},
        "M0_implementation": {
            "checks": m0_checks,
            "shared_interventions": intervention_counts,
            "score_multiset_max_error": score_tables["score_multiset_max_error"],
            "probability_sum_max_error": max_probability_error,
            "real_training": real_train,
            "pair_sham_training": sham_train,
        },
        "M1_heldout_causal_alignment": alignment,
        "M2_natural_transport": {
            "coverage_real_over_sham": coverage_ratio,
            "paired_coverage_gain_ci95": coverage_gain_ci,
            "nonredundant_real_over_sham": nonredundant_ratio,
            "paired_nonredundant_gain_ci95": nonredundant_gain_ci,
            "real": _natural_summary(real_natural),
            "pair_sham": _natural_summary(sham_natural),
        },
        "M3_r30_safety": {
            "real_full_sync_set_rate": real_natural["full_sync_set_rate"],
            "real_set_skill_entropy_norm": real_natural["set_skill_entropy_norm"],
            "real_set_skill_share_min": real_natural["set_skill_share_min"],
            "real_lifetime_min_share": real_natural["lifetime_min_share"],
        },
        "diagnostic_only": {
            "heldout_pair_scores": score_tables["pair_scores"][TRAIN_CONTEXTS:],
            "heldout_pairs": score_tables["pairs"],
            "real_task": real_natural["task_diagnostics_only"],
            "pair_sham_task": sham_natural["task_diagnostics_only"],
        },
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the R33 complete-roster complementarity gate."
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=33031)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap_repetitions", type=int, default=10_000)
    args = parser.parse_args()
    if int(args.seed) != 33031:
        parser.error("R33 contract fixes --seed at 33031")
    if int(args.bootstrap_repetitions) != 10_000:
        parser.error("R33 contract fixes --bootstrap_repetitions at 10000")
    return args


def main() -> None:
    args = parse_args()
    result = _json_ready(run(args))
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"[R33] phase=complete status={result['status']} output={output}",
        flush=True,
    )


if __name__ == "__main__":
    main()
