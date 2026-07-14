"""Run the paired R32-IFEPG Alice--Bob mechanism gate.

R32 is a shadow, intervention-only actor auxiliary.  This runner never turns
the score into reward, never invokes task/high/critic/posterior updates, and
writes one result JSON only.
"""

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
from ha_ctse_process.r30_fixed_clock import KEEP_TOKEN, SET_TOKEN  # noqa: E402
from ha_ctse_process.r31_effect_information import (  # noqa: E402
    build_effect_and_context,
    causal_between_within_metrics,
)
from ha_ctse_process.r32_interventional_effect_pg import (  # noqa: E402
    ForcedEffectBranch,
    InterventionalContext,
    context_effect_score,
    focal_ppo_clipped_surrogate,
    leave_one_context_advantage,
    parameter_drift_metrics,
)


SCHEMA_VERSION = 1
WINDOW = 10
EPISODE_STEPS = 80
N_AGENTS = 2
N_SKILLS = 4
SOURCE_EPISODES = 24
TRAIN_SOURCE_EPISODES = 16
TRAIN_CONTEXTS = 256
HELDOUT_CONTEXTS = 128
AUX_UPDATES = 20
CONTEXTS_PER_UPDATE = 32
REPLICAS = 2
FILM_LR = 3e-4
PPO_CLIP = 0.10
GRAD_CLIP = 0.5
NATURAL_EPISODES = 64
POSITION_BINS = 5

THRESHOLDS = {
    "replay_logp_max_error": 1e-5,
    "probe_film_max_abs_drift": 1e-8,
    "real_film_relative_l2_drift_min": 1e-6,
    "real_non_film_max_abs_drift": 1e-8,
    "real_causal_ratio_median": 1.5,
    "real_causal_ratio_ci_lower": 1.0,
    "paired_causal_ratio_median_gain": 0.40,
    "paired_causal_ratio_gain_ci_lower": 0.0,
    "per_skill_pooled_ratio": 1.0,
    "between_mean_ratio": 1.50,
    "paired_between_gain_ci_lower": 0.0,
    "within_mean_ratio_max": 1.25,
    "natural_coverage_ratio": 1.10,
    "paired_coverage_gain_ci_lower": 0.0,
    "full_sync_set_rate_max": 0.50,
    "set_skill_entropy_norm_min": 0.80,
    "lifetime_min_share": 0.05,
}


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


def _checkpoint_manifest(path: Path) -> dict[str, Any]:
    loader = getattr(train_mod, "_load_adjacent_run_manifest", None)
    return loader(path) if callable(loader) else {}


def _fail_closed_config(config, metadata: dict[str, Any], manifest: dict[str, Any]) -> None:
    if str(metadata.get("high_controller")) != "r30_fixed_clock_ar_edit":
        raise ValueError("R32 requires a frozen R30 fixed-clock checkpoint")
    if str(metadata.get("scenario")) != "alice_bob_asymmetric_cycles":
        raise ValueError("R32 requires an Alice--Bob checkpoint")
    if int(metadata.get("n_agents") or 0) != N_AGENTS or int(metadata.get("n_skills") or 0) != N_SKILLS:
        raise ValueError("R32 requires the two-agent, four-skill source")
    contract = metadata.get("r30_contract") or {}
    if int(contract.get("k0") or metadata.get("skill_interval") or 0) != WINDOW:
        raise ValueError("R32 requires source k0=W=10")
    algorithm = manifest.get("algorithm_config") if isinstance(manifest, dict) else None
    if not isinstance(algorithm, dict) or "r30_force_refresh_every_check" not in algorithm:
        raise ValueError("R32 cannot verify the adaptive-R30 source")
    if bool(algorithm["r30_force_refresh_every_check"]):
        raise ValueError("R32 rejects the shared-k comparator source")
    forbidden_nonzero = {
        "alice_bob_semantic_reward_enabled": False,
        "transition_skill_reward_coef": 0.0,
        "alice_bob_progress_reward_coef": 0.0,
    }
    for name, expected in forbidden_nonzero.items():
        if getattr(config, name, expected) != expected:
            raise ValueError(f"R32 sparse reward boundary rejects {name}")
    if str(getattr(config, "r28_g1_arm", "off")) != "off":
        raise ValueError("R32 forbids R28 online reward")
    if str(getattr(config, "r29_action_info_mode", "off")) != "off":
        raise ValueError("R32 forbids R29 online reward")
    if str(getattr(config, "r31_effect_mode", "off")) == "real_reward":
        raise ValueError("R31 effect reward is retired")
    for name in (
        "process_reward_injection",
        "outcome_residual_injection",
        "topology_role_injection",
        "topology_potential_injection",
        "skill_effect_reward_injection",
        "skill_force_reward_injection",
    ):
        if str(getattr(config, name, "none")).lower() != "none":
            raise ValueError(f"R32 forbids {name}")


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
    if not callable(getattr(agent.low, "film_update_parameters", None)):
        raise RuntimeError("strict low actor lacks the R32 FiLM-only parameter hook")
    if not callable(getattr(agent.low, "evaluate_focal_sequence_log_probs", None)):
        raise RuntimeError("strict low actor lacks the R32 focal replay hook")
    return checkpoint, config, env, agent, metadata, total_steps, update_idx, device


def _clear_episode_buffers(agent) -> None:
    agent.segments.flush(env_id=0, reason="episode")
    agent.segments.pop_completed()
    agent.high_check_buffer.pop_completed()


def _collect_context_bank(
    *, env, agent, source_update: int, base_seed: int, device: torch.device
) -> list[InterventionalContext]:
    raw_env = env.env
    contexts: list[InterventionalContext] = []
    snapshot_id = 0
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
                raise RuntimeError("R32 context did not start after a real R30 check")
            skills = agent.active_skills[0].astype(np.int64, copy=True)
            if np.any(skills < 0):
                raise RuntimeError("R30 did not assign every skill before snapshot")
            snapshot = copy.deepcopy(raw_env.get_probe_snapshot())
            actor_hxs = agent.low_actor_hxs[0].copy()
            critic_hxs = agent.low_critic_hxs[0].copy()
            team_code = int(agent.active_team_codes[0])
            for focal_agent in range(N_AGENTS):
                contexts.append(
                    InterventionalContext(
                        context_id=len(contexts),
                        reset_group=reset_group,
                        focal_agent=focal_agent,
                        observations=np.asarray(observations, dtype=np.float32).copy(),
                        state=state.copy(),
                        active_skills=skills.copy(),
                        actor_rnn_states=actor_hxs.copy(),
                        critic_rnn_states=critic_hxs.copy(),
                        env_snapshot=copy.deepcopy(snapshot),
                        metadata={
                            "snapshot_id": snapshot_id,
                            "block": block,
                            "team_code": team_code,
                        },
                    )
                )
            snapshot_id += 1
            for primitive in range(WINDOW):
                actions, _logp, _values = agent.act_low(
                    observations, env_id=0, deterministic=False, state=state
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
                    block == EPISODE_STEPS // WINDOW - 1 and primitive == WINDOW - 1
                ):
                    raise RuntimeError("Alice--Bob ended before a complete R32 source window")
        if not done:
            raise RuntimeError("R32 source episode did not end at 80 steps")
        _clear_episode_buffers(agent)
    if len(contexts) != TRAIN_CONTEXTS + HELDOUT_CONTEXTS:
        raise RuntimeError(f"R32 context count mismatch: {len(contexts)}")
    train = [row for row in contexts if row.reset_group < TRAIN_SOURCE_EPISODES]
    heldout = [row for row in contexts if row.reset_group >= TRAIN_SOURCE_EPISODES]
    if len(train) != TRAIN_CONTEXTS or len(heldout) != HELDOUT_CONTEXTS:
        raise RuntimeError("R32 episode-disjoint context split is not 256/128")
    if sum(row.focal_agent == 0 for row in train) != TRAIN_CONTEXTS // 2:
        raise RuntimeError("R32 train focal contexts are not balanced")
    if sum(row.focal_agent == 0 for row in heldout) != HELDOUT_CONTEXTS // 2:
        raise RuntimeError("R32 heldout focal contexts are not balanced")
    return contexts


def _single_low_act(
    low,
    *,
    observations: np.ndarray,
    state: np.ndarray,
    skill: int,
    team_code: int,
    actor_hxs: np.ndarray,
    critic_hxs: np.ndarray,
    agent_id: int,
) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    device = low.device
    obs_t = torch.as_tensor(observations, dtype=torch.float32, device=device).reshape(1, -1)
    skills_t = torch.tensor([int(skill)], dtype=torch.long, device=device)
    state_t = torch.as_tensor(state, dtype=torch.float32, device=device).reshape(1, -1)
    team_t = torch.tensor([int(team_code)], dtype=torch.long, device=device)
    actor_t = torch.as_tensor(actor_hxs, dtype=torch.float32, device=device).reshape(1, -1)
    critic_t = torch.as_tensor(critic_hxs, dtype=torch.float32, device=device).reshape(1, -1)
    agent_ids = torch.tensor([int(agent_id)], dtype=torch.long, device=device)
    with torch.no_grad():
        actions, logp, _unused, _values, next_actor, next_critic = low.act(
            obs_t,
            skills_t,
            actor_t,
            state_t,
            team_t,
            critic_t,
            agent_ids,
            deterministic=False,
        )
    return (
        actions.detach().cpu().numpy().astype(np.float32).reshape(-1),
        float(logp.detach().cpu().reshape(-1)[0].item()),
        next_actor.detach().cpu().numpy().astype(np.float32).reshape(-1),
        next_critic.detach().cpu().numpy().astype(np.float32).reshape(-1),
    )


def _run_forced_branch(
    *,
    env,
    current_low,
    behavior_low,
    context: InterventionalContext,
    skill: int,
    replica: int,
    branch_seed: int,
    device: torch.device,
) -> ForcedEffectBranch:
    raw_env = env.env
    raw_env.set_probe_snapshot(copy.deepcopy(context.env_snapshot))
    raw_env.np_random = np.random.default_rng(int(branch_seed))
    _set_seed(int(branch_seed), device)
    focal = int(context.focal_agent)
    teammate = 1 - focal
    observations = np.asarray(context.observations, dtype=np.float32).copy()
    state = np.asarray(context.state, dtype=np.float32).copy()
    skills = np.asarray(context.active_skills, dtype=np.int64).copy()
    skills[focal] = int(skill)
    team_code = int(context.metadata["team_code"])
    actor_snapshot = np.asarray(context.actor_rnn_states, dtype=np.float32)
    critic_snapshot = np.asarray(context.critic_rnn_states, dtype=np.float32)
    current_actor = actor_snapshot[focal].copy()
    current_critic = critic_snapshot[focal].copy()
    behavior_actor = actor_snapshot[teammate].copy()
    behavior_critic = critic_snapshot[teammate].copy()
    initial_focal_hxs = current_actor.copy()
    focal_obs: list[np.ndarray] = []
    focal_actions: list[np.ndarray] = []
    focal_logp: list[float] = []
    effect_views = [raw_env.intrinsic_effect_view()]
    for primitive in range(WINDOW):
        current_action, current_logp, current_actor, current_critic = _single_low_act(
            current_low,
            observations=observations[focal],
            state=state,
            skill=int(skills[focal]),
            team_code=team_code,
            actor_hxs=current_actor,
            critic_hxs=current_critic,
            agent_id=focal,
        )
        behavior_action, _behavior_logp, behavior_actor, behavior_critic = _single_low_act(
            behavior_low,
            observations=observations[teammate],
            state=state,
            skill=int(skills[teammate]),
            team_code=team_code,
            actor_hxs=behavior_actor,
            critic_hxs=behavior_critic,
            agent_id=teammate,
        )
        actions = np.zeros((N_AGENTS, current_action.size), dtype=np.float32)
        actions[focal] = current_action
        actions[teammate] = behavior_action
        focal_obs.append(observations[focal].copy())
        focal_actions.append(actions[focal].copy())
        focal_logp.append(float(current_logp))
        observations, _ignored_reward, terminated, truncated, info = env.step(actions)
        state = np.asarray(info["next_state"], dtype=np.float32)
        effect_views.append(raw_env.intrinsic_effect_view())
        if (terminated or truncated) and primitive != WINDOW - 1:
            raise RuntimeError("R32 forced branch ended before W=10")
    effect, _unused_context = build_effect_and_context(
        np.asarray(effect_views, dtype=np.float32),
        skills,
        focal,
        N_SKILLS,
    )
    return ForcedEffectBranch(
        context_id=int(context.context_id),
        focal_agent=focal,
        skill=int(skill),
        replica=int(replica),
        effect=effect,
        observations=np.asarray(focal_obs, dtype=np.float32),
        actions=np.asarray(focal_actions, dtype=np.float32),
        old_log_probs=np.asarray(focal_logp, dtype=np.float32),
        initial_actor_rnn_state=initial_focal_hxs,
        masks=np.ones(WINDOW, dtype=np.float32),
        metadata={"team_code": team_code, "branch_seed": int(branch_seed)},
    )


def _collect_branch_tensor(
    *,
    env,
    current_low,
    behavior_low,
    contexts: list[InterventionalContext],
    seed_for: Callable[[InterventionalContext, int, int], int],
    device: torch.device,
) -> tuple[list[ForcedEffectBranch], np.ndarray]:
    branches: list[ForcedEffectBranch] = []
    effects = np.empty((len(contexts), N_SKILLS, REPLICAS, 8), dtype=np.float32)
    seeds: set[int] = set()
    for context_index, context in enumerate(contexts):
        for skill in range(N_SKILLS):
            for replica in range(REPLICAS):
                branch_seed = int(seed_for(context, skill, replica))
                branch = _run_forced_branch(
                    env=env,
                    current_low=current_low,
                    behavior_low=behavior_low,
                    context=context,
                    skill=skill,
                    replica=replica,
                    branch_seed=branch_seed,
                    device=device,
                )
                branches.append(branch)
                effects[context_index, skill, replica] = np.asarray(branch.effect)
                seeds.add(branch_seed)
    if len(branches) != len(contexts) * N_SKILLS * REPLICAS:
        raise RuntimeError("R32 forced branch count mismatch")
    return branches, effects


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
    if not snapshot or not any("actor_film" in name.split(".") for name in snapshot):
        raise RuntimeError("R32 could not inventory the strict low actor FiLM")
    return snapshot


def _initial_parameter_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    if set(left) != set(right):
        raise RuntimeError("paired R32 arms do not expose identical parameter sets")
    return max(
        float(torch.max(torch.abs(left[name] - right[name])).item())
        for name in left
    )


def _training_batches(
    contexts: list[InterventionalContext], *, seed: int
) -> list[list[InterventionalContext]]:
    by_snapshot: dict[int, list[InterventionalContext]] = {}
    for context in contexts:
        by_snapshot.setdefault(int(context.metadata["snapshot_id"]), []).append(context)
    pairs = []
    for snapshot_id in sorted(by_snapshot):
        pair = sorted(by_snapshot[snapshot_id], key=lambda row: row.focal_agent)
        if len(pair) != N_AGENTS or [row.focal_agent for row in pair] != [0, 1]:
            raise RuntimeError("R32 train snapshot does not contain both focal agents")
        pairs.append(pair)
    if len(pairs) != TRAIN_CONTEXTS // N_AGENTS:
        raise RuntimeError("R32 train bank does not contain 128 paired snapshots")
    generator = np.random.default_rng(int(seed))
    required_pairs = AUX_UPDATES * (CONTEXTS_PER_UPDATE // N_AGENTS)
    schedule: list[int] = []
    while len(schedule) < required_pairs:
        schedule.extend(int(index) for index in generator.permutation(len(pairs)))
    schedule = schedule[:required_pairs]
    result: list[list[InterventionalContext]] = []
    width = CONTEXTS_PER_UPDATE // N_AGENTS
    for update in range(AUX_UPDATES):
        selected = schedule[update * width : (update + 1) * width]
        batch = [context for pair_index in selected for context in pairs[pair_index]]
        if len(batch) != CONTEXTS_PER_UPDATE:
            raise RuntimeError("R32 auxiliary context batch is not 32")
        if len({int(row.context_id) for row in batch}) != CONTEXTS_PER_UPDATE:
            raise RuntimeError("R32 repeated a context within one auxiliary update")
        if sum(row.focal_agent == 0 for row in batch) != CONTEXTS_PER_UPDATE // 2:
            raise RuntimeError("R32 auxiliary update is not focal-balanced")
        result.append(batch)
    return result


def _replay_branch(low, branch: ForcedEffectBranch) -> torch.Tensor:
    device = low.device
    team_code = int(branch.metadata["team_code"])
    return low.evaluate_focal_sequence_log_probs(
        torch.as_tensor(branch.observations, dtype=torch.float32, device=device),
        torch.full((WINDOW,), int(branch.skill), dtype=torch.long, device=device),
        torch.as_tensor(branch.actions, dtype=torch.float32, device=device),
        torch.as_tensor(
            branch.initial_actor_rnn_state,
            dtype=torch.float32,
            device=device,
        ),
        team_codes_seq=torch.full(
            (WINDOW,), team_code, dtype=torch.long, device=device
        ),
        masks_seq=torch.as_tensor(branch.masks, dtype=torch.float32, device=device),
    )


def _train_arm(
    *,
    arm: str,
    env,
    agent,
    train_contexts: list[InterventionalContext],
    base_seed: int,
    device: torch.device,
) -> tuple[dict[str, Any], torch.nn.Module]:
    if arm not in {"probe_only", "real_update"}:
        raise ValueError(f"unknown R32 arm {arm!r}")
    before = _parameter_snapshot(agent)
    film_parameters = list(agent.low.film_update_parameters())
    registered_film = list(agent.low.actor_film.parameters())
    if {id(value) for value in film_parameters} != {id(value) for value in registered_film}:
        raise RuntimeError("R32 FiLM hook exposes parameters outside actor_film")
    all_parameters: list[torch.nn.Parameter] = []
    seen_parameters: set[int] = set()
    for module in vars(agent).values():
        if not isinstance(module, torch.nn.Module):
            continue
        for parameter in module.parameters():
            if id(parameter) not in seen_parameters:
                seen_parameters.add(id(parameter))
                all_parameters.append(parameter)
    original_requires_grad = {
        id(parameter): bool(parameter.requires_grad)
        for parameter in all_parameters
    }
    if arm == "real_update":
        film_ids = {id(parameter) for parameter in film_parameters}
        for parameter in all_parameters:
            parameter.requires_grad_(id(parameter) in film_ids)
        # cuDNN requires the GRU module itself to be in training mode for
        # backward, even though every recurrent parameter remains frozen.
        agent.low.actor_rnn.train()
    optimizer = (
        torch.optim.Adam(film_parameters, lr=FILM_LR)
        if arm == "real_update"
        else None
    )
    updates: list[dict[str, Any]] = []
    replay_error_max = 0.0
    branch_count = 0
    non_film_gradient_tensor_count = 0
    non_film_gradient_max_abs = 0.0
    batches = _training_batches(
        train_contexts,
        seed=int(base_seed) + 1_000_000,
    )
    for update_index, contexts in enumerate(batches):
        behavior_low = copy.deepcopy(agent.low).to(device)
        behavior_low.eval()
        for parameter in behavior_low.parameters():
            parameter.requires_grad_(False)
        seed_values = [
            int(base_seed)
            + 2_000_000
            + update_index * 100_000
            + int(context.context_id) * 100
            + skill * REPLICAS
            + replica
            for context in contexts
            for skill in range(N_SKILLS)
            for replica in range(REPLICAS)
        ]
        if len(set(seed_values)) != len(seed_values):
            raise RuntimeError("R32 training skill/replica streams are not independent")

        def training_seed(context, skill, replica):
            return (
                int(base_seed)
                + 2_000_000
                + update_index * 100_000
                + int(context.context_id) * 100
                + int(skill) * REPLICAS
                + int(replica)
            )

        branches, effects = _collect_branch_tensor(
            env=env,
            current_low=agent.low,
            behavior_low=behavior_low,
            contexts=contexts,
            seed_for=training_seed,
            device=device,
        )
        branch_count += len(branches)
        scores = np.asarray(context_effect_score(effects), dtype=np.float64)
        advantages = np.asarray(
            leave_one_context_advantage(scores), dtype=np.float64
        )
        current_logp = torch.stack([_replay_branch(agent.low, row) for row in branches])
        current_logp = current_logp.reshape(
            CONTEXTS_PER_UPDATE, N_SKILLS, REPLICAS, WINDOW
        )
        old_logp = np.stack(
            [np.asarray(row.old_log_probs, dtype=np.float32) for row in branches]
        ).reshape(CONTEXTS_PER_UPDATE, N_SKILLS, REPLICAS, WINDOW)
        replay_error = float(
            torch.max(
                torch.abs(
                    current_logp.detach()
                    - torch.as_tensor(old_logp, device=device)
                )
            ).cpu().item()
        )
        replay_error_max = max(replay_error_max, replay_error)
        loss = focal_ppo_clipped_surrogate(
            current_logp,
            old_logp,
            advantages,
            clip=PPO_CLIP,
        )
        grad_norm = 0.0
        if optimizer is not None:
            for parameter in all_parameters:
                parameter.grad = None
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            film_ids = {id(parameter) for parameter in film_parameters}
            escaped = [
                parameter
                for parameter in all_parameters
                if id(parameter) not in film_ids and parameter.grad is not None
            ]
            non_film_gradient_tensor_count += len(escaped)
            if escaped:
                non_film_gradient_max_abs = max(
                    non_film_gradient_max_abs,
                    max(float(parameter.grad.detach().abs().max().cpu().item()) for parameter in escaped),
                )
                raise RuntimeError("R32 gradient escaped actor_film")
            grad_norm = float(
                torch.nn.utils.clip_grad_norm_(film_parameters, GRAD_CLIP)
                .detach()
                .cpu()
                .item()
            )
            optimizer.step()
        updates.append(
            {
                "update": update_index + 1,
                "contexts": len(contexts),
                "context_ids": [int(row.context_id) for row in contexts],
                "branches": len(branches),
                "score_mean": float(np.mean(scores)),
                "score_std": float(np.std(scores)),
                "advantage_mean": float(np.mean(advantages)),
                "loss": float(loss.detach().cpu().item()),
                "replay_logp_max_error": replay_error,
                "film_grad_norm": grad_norm,
            }
        )
        print(
            f"[R32] arm={arm} aux_update={update_index + 1}/{AUX_UPDATES} "
            f"score={float(np.mean(scores)):.6g} replay_error={replay_error:.3g}",
            flush=True,
        )
    for parameter in all_parameters:
        parameter.requires_grad_(original_requires_grad[id(parameter)])
    agent.low.eval()
    final_behavior_low = copy.deepcopy(agent.low).to(device)
    final_behavior_low.eval()
    for parameter in final_behavior_low.parameters():
        parameter.requires_grad_(False)
    after = _parameter_snapshot(agent)
    drift = parameter_drift_metrics(before, after)
    expected_branches = AUX_UPDATES * CONTEXTS_PER_UPDATE * N_SKILLS * REPLICAS
    if branch_count != expected_branches:
        raise RuntimeError(f"R32 {arm} train branches={branch_count}, expected={expected_branches}")
    return (
        {
            "arm": arm,
            "updates": updates,
            "auxiliary_update_count": int(optimizer is not None) * AUX_UPDATES,
            "training_context_exposures": AUX_UPDATES * CONTEXTS_PER_UPDATE,
            "training_branch_count": branch_count,
            "training_shadow_steps": branch_count * WINDOW,
            "replay_logp_max_error": replay_error_max,
            "parameter_drift": drift,
            "optimizer": "Adam" if optimizer is not None else None,
            "film_lr": FILM_LR if optimizer is not None else None,
            "low_critic_updates": 0,
            "high_policy_updates": 0,
            "posterior_updates": 0,
            "task_reward_objective_reads": 0,
            "non_film_gradient_tensor_count": non_film_gradient_tensor_count,
            "non_film_gradient_max_abs": non_film_gradient_max_abs,
        },
        final_behavior_low,
    )


def _heldout_effect_evaluation(
    *,
    env,
    agent,
    behavior_low,
    contexts: list[InterventionalContext],
    base_seed: int,
    device: torch.device,
) -> dict[str, Any]:
    if len(contexts) != HELDOUT_CONTEXTS:
        raise RuntimeError("R32 heldout evaluator requires 128 contexts")

    def crn_seed(context, _skill, replica):
        return (
            int(base_seed)
            + 20_000_000
            + int(context.context_id) * 10
            + int(replica)
        )

    branches, effects = _collect_branch_tensor(
        env=env,
        current_low=agent.low,
        behavior_low=behavior_low,
        contexts=contexts,
        seed_for=crn_seed,
        device=device,
    )
    for context_index in range(len(contexts)):
        rows = branches[context_index * N_SKILLS * REPLICAS : (context_index + 1) * N_SKILLS * REPLICAS]
        for replica in range(REPLICAS):
            seeds = {
                int(row.metadata["branch_seed"])
                for row in rows
                if int(row.replica) == replica
            }
            if len(seeds) != 1:
                raise RuntimeError("R32 heldout evaluator is not cross-skill CRN")
    causal = causal_between_within_metrics(effects)
    pairs = np.asarray(causal["skill_pairs"], dtype=np.int64)
    between = np.asarray(causal["between"], dtype=np.float64)
    within = np.asarray(causal["within"], dtype=np.float64)
    ratio = np.asarray(causal["ratio"], dtype=np.float64)
    pooled: dict[str, float] = {}
    for skill in range(N_SKILLS):
        involved = np.any(pairs == skill, axis=1)
        pooled[str(skill)] = float(np.mean(between[:, involved])) / (
            float(np.mean(within[:, involved])) + 1e-8
        )
    return {
        "branch_count": len(branches),
        "shadow_steps": len(branches) * WINDOW,
        "effects": effects,
        "skill_pairs": pairs,
        "between": between,
        "within": within,
        "ratio": ratio,
        "pooled_ratio_by_skill": pooled,
    }


def _cluster_bootstrap_ci(
    values: np.ndarray,
    *,
    repetitions: int,
    rng: np.random.Generator,
    statistic: Callable[[np.ndarray], float],
) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim < 1 or array.shape[0] <= 1 or not np.all(np.isfinite(array)):
        raise ValueError("cluster bootstrap requires finite context/reset rows")
    draws = np.empty(int(repetitions), dtype=np.float64)
    for index in range(int(repetitions)):
        sampled = rng.integers(0, array.shape[0], size=array.shape[0])
        draws[index] = float(statistic(array[sampled]))
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def _position_cell(effect_view: np.ndarray) -> int:
    positions = np.asarray(effect_view, dtype=np.float32)
    if positions.shape != (N_AGENTS, 2):
        raise ValueError("R32 natural coverage requires normalized [2,2] positions")
    clipped = np.clip(positions, 0.0, np.nextafter(1.0, 0.0))
    bins = np.floor(clipped * POSITION_BINS).astype(np.int64).reshape(-1)
    cell = 0
    for value in bins:
        cell = cell * POSITION_BINS + int(value)
    return cell


def _natural_transport(
    *, env, agent, source_update: int, base_seed: int, device: torch.device
) -> dict[str, Any]:
    raw_env = env.env
    coverage: list[float] = []
    global_cells: set[int] = set()
    task_reward: list[float] = []
    final_task_metrics: list[dict[str, float]] = []
    all_rows = []
    for episode in range(NATURAL_EPISODES):
        reset_seed = int(base_seed) + 30_000_000 + episode
        _set_seed(reset_seed, device)
        observations, info = env.reset(seed=reset_seed)
        state = np.asarray(info["state"], dtype=np.float32)
        agent.reset_env_state(0)
        cells: set[int] = set()
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
                    observations, env_id=0, deterministic=False, state=state
                )
                observations, reward, terminated, truncated, next_info = env.step(actions)
                state = np.asarray(next_info["next_state"], dtype=np.float32)
                cells.add(_position_cell(raw_env.intrinsic_effect_view()))
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
                    block == EPISODE_STEPS // WINDOW - 1 and primitive == WINDOW - 1
                ):
                    raise RuntimeError("R32 natural episode ended before 80 steps")
        if not done:
            raise RuntimeError("R32 natural transport episode did not terminate at 80 steps")
        coverage.append(len(cells) / float(POSITION_BINS ** (N_AGENTS * 2)))
        global_cells.update(cells)
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
        row for row in all_rows if row.decision_mask and bool(np.all(row.prev_active))
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
        counts = np.bincount(np.asarray(switch_skills), minlength=N_SKILLS).astype(np.float64)
        shares = counts / float(np.sum(counts))
        positive = shares[shares > 0.0]
        entropy_norm = float(-np.sum(positive * np.log(positive)) / math.log(N_SKILLS))
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
    task_diagnostics = {
        "mean_sparse_task_reward": float(np.mean(task_reward)),
    }
    for name in final_task_metrics[0]:
        task_diagnostics[f"mean_final_{name}"] = float(
            np.mean([row[name] for row in final_task_metrics])
        )
    return {
        "episode_count": NATURAL_EPISODES,
        "primitive_steps": NATURAL_EPISODES * EPISODE_STEPS,
        "coverage_by_reset": np.asarray(coverage, dtype=np.float64),
        "coverage_mean": float(np.mean(coverage)),
        "coverage_union_cells": len(global_cells),
        "coverage_union_fraction": len(global_cells)
        / float(POSITION_BINS ** (N_AGENTS * 2)),
        "normal_decision_rows": len(normal_rows),
        "full_sync_set_rate": float(np.mean(full_sync)) if full_sync else 1.0,
        "set_skill_counts": counts,
        "set_skill_shares": shares,
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
        return "INVALID", "repair implementation only; do not interpret R32"
    if not m1:
        return (
            "FAIL_M1_RETIRE_R32_IFEPG",
            "retire direct interventional FiLM-effect policy gradient",
        )
    if not m2:
        return (
            "FAIL_M2_STOCHASTIC_NOISE_EXPLOITATION",
            "retire R32 as stochastic/noise exploitation",
        )
    if not m3:
        return (
            "FAIL_M3_FORCED_ONLY_OR_R30_SAFETY",
            "retire R32 as forced-only capacity or R30-safety failure",
        )
    return (
        "PASS_R32_IFEPG_GATE",
        "authorize only sparse-source R30 training with one FiLM-only IFEPG auxiliary step",
    )


def _effect_summary(evaluation: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_count": evaluation["branch_count"],
        "shadow_steps": evaluation["shadow_steps"],
        "skill_pairs": evaluation["skill_pairs"],
        "ratio_by_context_pair": evaluation["ratio"],
        "between_by_context_pair": evaluation["between"],
        "within_by_context_pair": evaluation["within"],
        "median_ratio": float(np.median(evaluation["ratio"])),
        "mean_between": float(np.mean(evaluation["between"])),
        "mean_within": float(np.mean(evaluation["within"])),
        "pooled_ratio_by_skill": evaluation["pooled_ratio_by_skill"],
    }


def _natural_summary(transport: dict[str, Any]) -> dict[str, Any]:
    return {
        name: value
        for name, value in transport.items()
        if name != "coverage_by_reset"
    } | {"coverage_by_reset": transport["coverage_by_reset"]}


def run(args: argparse.Namespace) -> dict[str, Any]:
    print("[R32] phase=source_context_bank", flush=True)
    source = _make_agent_and_env(args, seed_offset=0)
    (
        checkpoint,
        config,
        source_env,
        source_agent,
        metadata,
        source_total_steps,
        source_update,
        device,
    ) = source
    try:
        contexts = _collect_context_bank(
            env=source_env,
            agent=source_agent,
            source_update=source_update,
            base_seed=int(args.seed),
            device=device,
        )
    finally:
        source_env.close()
    del source_agent, source_env, source
    if device.type == "cuda":
        torch.cuda.empty_cache()
    train_contexts = [
        row for row in contexts if row.reset_group < TRAIN_SOURCE_EPISODES
    ]
    heldout_contexts = [
        row for row in contexts if row.reset_group >= TRAIN_SOURCE_EPISODES
    ]

    print("[R32] phase=create_paired_arms", flush=True)
    probe = _make_agent_and_env(args, seed_offset=10_000)
    real = _make_agent_and_env(args, seed_offset=20_000)
    probe_env, probe_agent = probe[2], probe[3]
    real_env, real_agent = real[2], real[3]
    probe_before = _parameter_snapshot(probe_agent)
    real_before = _parameter_snapshot(real_agent)
    initial_difference = _initial_parameter_difference(probe_before, real_before)
    try:
        print("[R32] phase=probe_shadow_training", flush=True)
        probe_train, probe_behavior = _train_arm(
            arm="probe_only",
            env=probe_env,
            agent=probe_agent,
            train_contexts=train_contexts,
            base_seed=int(args.seed),
            device=device,
        )
        print("[R32] phase=real_film_training", flush=True)
        real_train, real_behavior = _train_arm(
            arm="real_update",
            env=real_env,
            agent=real_agent,
            train_contexts=train_contexts,
            base_seed=int(args.seed),
            device=device,
        )
        print("[R32] phase=heldout_crn_evaluation", flush=True)
        probe_effect = _heldout_effect_evaluation(
            env=probe_env,
            agent=probe_agent,
            behavior_low=probe_behavior,
            contexts=heldout_contexts,
            base_seed=int(args.seed),
            device=device,
        )
        real_effect = _heldout_effect_evaluation(
            env=real_env,
            agent=real_agent,
            behavior_low=real_behavior,
            contexts=heldout_contexts,
            base_seed=int(args.seed),
            device=device,
        )
        print("[R32] phase=natural_transport", flush=True)
        probe_natural = _natural_transport(
            env=probe_env,
            agent=probe_agent,
            source_update=source_update,
            base_seed=int(args.seed),
            device=device,
        )
        real_natural = _natural_transport(
            env=real_env,
            agent=real_agent,
            source_update=source_update,
            base_seed=int(args.seed),
            device=device,
        )
    finally:
        probe_env.close()
        real_env.close()

    bootstrap_rng = np.random.default_rng(int(args.seed) + 40_000_000)
    real_ratio = np.asarray(real_effect["ratio"], dtype=np.float64)
    probe_ratio = np.asarray(probe_effect["ratio"], dtype=np.float64)
    ratio_gain = real_ratio - probe_ratio
    real_ratio_ci = _cluster_bootstrap_ci(
        real_ratio,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.median(rows)),
    )
    ratio_gain_ci = _cluster_bootstrap_ci(
        ratio_gain,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.median(rows)),
    )
    between_gain = np.asarray(real_effect["between"]) - np.asarray(
        probe_effect["between"]
    )
    between_gain_ci = _cluster_bootstrap_ci(
        between_gain,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.mean(rows)),
    )
    coverage_gain = np.asarray(real_natural["coverage_by_reset"]) - np.asarray(
        probe_natural["coverage_by_reset"]
    )
    coverage_gain_ci = _cluster_bootstrap_ci(
        coverage_gain,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.mean(rows)),
    )

    probe_drift = probe_train["parameter_drift"]
    real_drift = real_train["parameter_drift"]
    exact_train_branches = AUX_UPDATES * CONTEXTS_PER_UPDATE * N_SKILLS * REPLICAS
    exact_eval_branches = HELDOUT_CONTEXTS * N_SKILLS * REPLICAS
    m0_checks = {
        "paired_initial_parameters": initial_difference <= THRESHOLDS["real_non_film_max_abs_drift"],
        "source_context_count": len(train_contexts) == TRAIN_CONTEXTS,
        "heldout_context_count": len(heldout_contexts) == HELDOUT_CONTEXTS,
        "probe_training_counts": probe_train["training_branch_count"] == exact_train_branches,
        "real_training_counts": real_train["training_branch_count"] == exact_train_branches,
        "heldout_evaluator_counts": (
            probe_effect["branch_count"] == exact_eval_branches
            and real_effect["branch_count"] == exact_eval_branches
        ),
        "paired_training_context_schedule": (
            [row["context_ids"] for row in probe_train["updates"]]
            == [row["context_ids"] for row in real_train["updates"]]
        ),
        "natural_episode_counts": (
            probe_natural["episode_count"] == NATURAL_EPISODES
            and real_natural["episode_count"] == NATURAL_EPISODES
        ),
        "probe_replay": probe_train["replay_logp_max_error"] <= THRESHOLDS["replay_logp_max_error"],
        "real_replay": real_train["replay_logp_max_error"] <= THRESHOLDS["replay_logp_max_error"],
        "probe_film_static": probe_drift["film_max_abs"] <= THRESHOLDS["probe_film_max_abs_drift"],
        "probe_non_film_static": probe_drift["non_film_max_abs"] <= THRESHOLDS["real_non_film_max_abs_drift"],
        "real_film_changed": (
            np.isfinite(real_drift["film_relative_l2"])
            and real_drift["film_relative_l2"] > THRESHOLDS["real_film_relative_l2_drift_min"]
        ),
        "real_non_film_static": real_drift["non_film_max_abs"] <= THRESHOLDS["real_non_film_max_abs_drift"],
        "real_non_film_gradient_absent": (
            real_train["non_film_gradient_tensor_count"] == 0
            and real_train["non_film_gradient_max_abs"] == 0.0
        ),
        "no_forbidden_updates": all(
            int(row[name]) == 0
            for row in (probe_train, real_train)
            for name in (
                "low_critic_updates",
                "high_policy_updates",
                "posterior_updates",
                "task_reward_objective_reads",
            )
        ),
    }
    m0 = all(m0_checks.values())

    real_ratio_median = float(np.median(real_ratio))
    paired_ratio_gain_median = float(np.median(ratio_gain))
    per_skill_pass = all(
        float(value) > THRESHOLDS["per_skill_pooled_ratio"]
        for value in real_effect["pooled_ratio_by_skill"].values()
    )
    m1 = bool(
        real_ratio_median >= THRESHOLDS["real_causal_ratio_median"]
        and real_ratio_ci[0] > THRESHOLDS["real_causal_ratio_ci_lower"]
        and paired_ratio_gain_median >= THRESHOLDS["paired_causal_ratio_median_gain"]
        and ratio_gain_ci[0] > THRESHOLDS["paired_causal_ratio_gain_ci_lower"]
        and per_skill_pass
    )

    mean_between_probe = float(np.mean(probe_effect["between"]))
    mean_between_real = float(np.mean(real_effect["between"]))
    mean_within_probe = float(np.mean(probe_effect["within"]))
    mean_within_real = float(np.mean(real_effect["within"]))
    between_ratio = mean_between_real / (mean_between_probe + 1e-8)
    within_ratio = mean_within_real / (mean_within_probe + 1e-8)
    m2 = bool(
        between_ratio >= THRESHOLDS["between_mean_ratio"]
        and between_gain_ci[0] > THRESHOLDS["paired_between_gain_ci_lower"]
        and within_ratio <= THRESHOLDS["within_mean_ratio_max"]
    )

    coverage_ratio = float(real_natural["coverage_union_fraction"]) / (
        float(probe_natural["coverage_union_fraction"]) + 1e-8
    )
    m3 = bool(
        coverage_ratio >= THRESHOLDS["natural_coverage_ratio"]
        and coverage_gain_ci[0] > THRESHOLDS["paired_coverage_gain_ci_lower"]
        and real_natural["full_sync_set_rate"] <= THRESHOLDS["full_sync_set_rate_max"]
        and real_natural["set_skill_entropy_norm"] >= THRESHOLDS["set_skill_entropy_norm_min"]
        and real_natural["lifetime_min_share"] >= THRESHOLDS["lifetime_min_share"]
    )
    status, next_action = _gate_decision(m0=m0, m1=m1, m2=m2, m3=m3)
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment": "R32-IFEPG paired Alice-Bob mechanism gate",
        "status": status,
        "authorized_next_action": next_action,
        "scope": "single paired mechanism seed; no task-efficacy or cooperation claim",
        "seed": int(args.seed),
        "source": {
            "checkpoint": str(checkpoint),
            "checkpoint_total_steps": int(source_total_steps),
            "checkpoint_update": int(source_update),
            "high_controller": metadata.get("high_controller"),
            "environment": "alice_bob_asymmetric_cycles",
            "external_reward": "collection_only_diagnostic_never_objective",
            "paired_arm_initial_max_abs_parameter_difference": initial_difference,
        },
        "contract": {
            "source_natural_episodes": SOURCE_EPISODES,
            "source_natural_primitive_steps": SOURCE_EPISODES * EPISODE_STEPS,
            "contexts_per_r30_check": N_AGENTS,
            "train_source_contexts": TRAIN_CONTEXTS,
            "heldout_contexts": HELDOUT_CONTEXTS,
            "focal_balance_per_split": "exact_50_50",
            "auxiliary_updates": AUX_UPDATES,
            "contexts_per_update": CONTEXTS_PER_UPDATE,
            "skills_per_context": N_SKILLS,
            "independent_training_replicas_per_skill": REPLICAS,
            "heldout_crn_replicas_per_skill": REPLICAS,
            "window": WINDOW,
            "training_shadow_steps_per_arm": exact_train_branches * WINDOW,
            "heldout_shadow_steps_per_arm": exact_eval_branches * WINDOW,
            "natural_episodes_per_arm": NATURAL_EPISODES,
            "natural_steps_per_arm": NATURAL_EPISODES * EPISODE_STEPS,
            "post_bank_steps_per_arm": (
                exact_train_branches * WINDOW
                + exact_eval_branches * WINDOW
                + NATURAL_EPISODES * EPISODE_STEPS
            ),
            "ppo_epochs_per_update": 1,
            "ppo_clip": PPO_CLIP,
            "film_lr": FILM_LR,
            "gradient_clip": GRAD_CLIP,
            "updated_parameters": "low.actor_film_only",
            "task_reward_in_objective": False,
            "low_value_or_gae": False,
            "entropy_bonus": False,
            "high_policy_update": False,
            "posterior_or_scorer_training": False,
            "bootstrap_repetitions": int(args.bootstrap_repetitions),
            "bootstrap_seed": int(args.seed) + 40_000_000,
            "device": str(device),
            "result_artifacts": 1,
        },
        "thresholds": THRESHOLDS,
        "gates": {"M0": m0, "M1": m1, "M2": m2, "M3": m3},
        "M0_implementation": {
            "checks": m0_checks,
            "probe_training": probe_train,
            "real_training": real_train,
        },
        "M1_causal_effect_snr": {
            "real_median_ratio": real_ratio_median,
            "real_median_ratio_ci95": real_ratio_ci,
            "paired_median_ratio_gain": paired_ratio_gain_median,
            "paired_median_ratio_gain_ci95": ratio_gain_ci,
            "real_per_skill_pooled_ratio": real_effect["pooled_ratio_by_skill"],
            "probe": _effect_summary(probe_effect),
            "real": _effect_summary(real_effect),
        },
        "M2_noise_pathology": {
            "between_mean_probe": mean_between_probe,
            "between_mean_real": mean_between_real,
            "between_real_over_probe": between_ratio,
            "paired_between_gain_ci95": between_gain_ci,
            "within_mean_probe": mean_within_probe,
            "within_mean_real": mean_within_real,
            "within_real_over_probe": within_ratio,
        },
        "M3_natural_transport_and_r30_safety": {
            "coverage_real_over_probe": coverage_ratio,
            "paired_coverage_gain_ci95": coverage_gain_ci,
            "probe": _natural_summary(probe_natural),
            "real": _natural_summary(real_natural),
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
        description="Run the paired R32 FiLM-only interventional-effect gate."
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=32031)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap_repetitions", type=int, default=10_000)
    args = parser.parse_args()
    if int(args.bootstrap_repetitions) != 10_000:
        parser.error("R32 contract fixes --bootstrap_repetitions at 10000")
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
    print(f"[R32] phase=complete status={result['status']} output={output}", flush=True)


if __name__ == "__main__":
    main()
