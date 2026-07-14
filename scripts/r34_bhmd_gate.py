"""Run the three-arm R34-BHMD Alice--Bob mechanism gate.

R34 discovers balanced focal displacement modes from natural source episodes,
distils those hindsight labels into the recurrent low actor, and evaluates the
result against both a max-Hamming episode-sequence sham and the untouched source
policy.  Reward, value, GAE, the high controller, and every posterior remain
outside the objective.  The runner writes one result JSON only.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from ha_ctse_process import train as train_mod  # noqa: E402
from ha_ctse_process.config_alice_bob_asymmetric import Config  # noqa: E402
from ha_ctse_process.r30_fixed_clock import KEEP_TOKEN, SET_TOKEN  # noqa: E402
from ha_ctse_process.r34_balanced_hindsight_mode_distillation import (  # noqa: E402
    InteractionModeDescriptor,
    between_within_mode_ratio,
    build_max_hamming_episode_sham,
    causal_mode_fidelity,
    fit_exact_balanced_prototypes,
    full_episode_distillation_loss,
    hungarian_align_to_existing_skills,
    nearest_prototype,
    parameter_drift_metrics,
    replay_actor_prefix_hidden,
)


SCHEMA_VERSION = 1
WINDOW = 10
EPISODE_STEPS = 80
BLOCKS_PER_EPISODE = EPISODE_STEPS // WINDOW
N_AGENTS = 2
N_SKILLS = 4
SOURCE_EPISODES = 32
TRAIN_SOURCE_EPISODES = 24
HELDOUT_SOURCE_EPISODES = 8
TRAIN_DESCRIPTOR_ROWS = TRAIN_SOURCE_EPISODES * BLOCKS_PER_EPISODE * N_AGENTS
HELDOUT_DESCRIPTOR_ROWS = HELDOUT_SOURCE_EPISODES * BLOCKS_PER_EPISODE * N_AGENTS
ROWS_PER_MODE = TRAIN_DESCRIPTOR_ROWS // N_SKILLS
DISTILL_EPOCHS = 10
SEQUENCES_PER_BATCH = 8
TRAIN_SEQUENCES = TRAIN_SOURCE_EPISODES * N_AGENTS
OPTIMIZER_CALLS = DISTILL_EPOCHS * (TRAIN_SEQUENCES // SEQUENCES_PER_BATCH)
DISTILL_LR = 3e-4
GRAD_CLIP = 0.5
REPLICAS = 2
NATURAL_EPISODES = 64
POSITION_BINS = 5
DESCRIPTOR_EPSILON = 1e-8

THRESHOLDS = {
    "paired_initial_parameter_max_abs": 1e-8,
    "source_replay_logp_max_error": 1e-5,
    "other_parameter_max_abs_drift": 1e-8,
    "max_hamming_label_agreement_max": 0.50,
    "forced_fidelity_real_min": 0.60,
    "forced_fidelity_per_skill_real_min": 0.45,
    "forced_fidelity_real_minus_sham_min": 0.20,
    "forced_fidelity_real_minus_source_min": 0.15,
    "forced_fidelity_gain_ci_lower": 0.0,
    "forced_snr_real_median_min": 1.50,
    "forced_snr_real_ci_lower": 1.0,
    "forced_snr_real_minus_sham_median_min": 0.30,
    "forced_snr_real_minus_source_median_min": 0.20,
    "forced_snr_gain_ci_lower": 0.0,
    "natural_consistency_real_min": 0.45,
    "natural_consistency_real_minus_sham_min": 0.15,
    "natural_consistency_real_minus_source_min": 0.10,
    "natural_consistency_gain_ci_lower": 0.0,
    "natural_coverage_real_over_sham_min": 1.10,
    "natural_coverage_real_over_source_min": 1.05,
    "natural_coverage_gain_ci_lower": 0.0,
    "full_sync_set_rate_max": 0.50,
    "set_skill_entropy_norm_min": 0.80,
    "set_skill_share_min": 0.05,
    "lifetime_min_share": 0.05,
}

DESCRIPTOR_SCHEMA = (
    "focal normalized displacement sequence only: 10x2; no teammate, absolute "
    "position, action, reward, task/contact/phase, old skill, age, agent id, or OPT"
)


@dataclass(frozen=True)
class SourceEpisode:
    episode_id: int
    observations: np.ndarray = field(repr=False, compare=False)
    actions: np.ndarray = field(repr=False, compare=False)
    old_log_probs: np.ndarray = field(repr=False, compare=False)
    old_skills: np.ndarray = field(repr=False, compare=False)
    team_codes: np.ndarray = field(repr=False, compare=False)
    block_snapshots: tuple[Any, ...] = field(repr=False, compare=False)
    block_observations: np.ndarray = field(repr=False, compare=False)
    block_position_paths: np.ndarray = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.observations.shape[0] != EPISODE_STEPS:
            raise ValueError("R34 source episode must contain 80 observation rows")
        if self.actions.shape[:2] != (EPISODE_STEPS, N_AGENTS):
            raise ValueError("R34 source actions must have shape [80,2,A]")
        if self.old_log_probs.shape != (EPISODE_STEPS, N_AGENTS):
            raise ValueError("R34 source log probabilities must have shape [80,2]")
        if self.old_skills.shape != (EPISODE_STEPS, N_AGENTS):
            raise ValueError("R34 source skills must have shape [80,2]")
        if self.team_codes.shape != (EPISODE_STEPS,):
            raise ValueError("R34 source team codes must have shape [80]")
        if len(self.block_snapshots) != BLOCKS_PER_EPISODE:
            raise ValueError("R34 source episode must contain eight block snapshots")
        if self.block_position_paths.shape != (
            BLOCKS_PER_EPISODE,
            WINDOW + 1,
            N_AGENTS,
            2,
        ):
            raise ValueError("R34 block position paths must have shape [8,11,2,2]")


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
        raise ValueError("R34 requires a frozen R30 fixed-clock checkpoint")
    if str(metadata.get("scenario")) != "alice_bob_asymmetric_cycles":
        raise ValueError("R34 requires an Alice--Bob checkpoint")
    if int(metadata.get("n_agents") or 0) != N_AGENTS or int(
        metadata.get("n_skills") or 0
    ) != N_SKILLS:
        raise ValueError("R34 requires the two-agent, four-skill source")
    contract = metadata.get("r30_contract") or {}
    if int(contract.get("k0") or metadata.get("skill_interval") or 0) != WINDOW:
        raise ValueError("R34 requires source k0=W=10")
    algorithm = manifest.get("algorithm_config") if isinstance(manifest, dict) else None
    if not isinstance(algorithm, dict) or "r30_force_refresh_every_check" not in algorithm:
        raise ValueError("R34 cannot verify the adaptive-R30 source")
    if bool(algorithm["r30_force_refresh_every_check"]):
        raise ValueError("R34 rejects the shared-k comparator source")
    forbidden_nonzero = {
        "alice_bob_semantic_reward_enabled": False,
        "transition_skill_reward_coef": 0.0,
        "alice_bob_progress_reward_coef": 0.0,
    }
    for name, expected in forbidden_nonzero.items():
        if getattr(config, name, expected) != expected:
            raise ValueError(f"R34 sparse reward boundary rejects {name}")
    if str(getattr(config, "r28_g1_arm", "off")) != "off":
        raise ValueError("R34 forbids R28 online reward")
    if str(getattr(config, "r29_action_info_mode", "off")) != "off":
        raise ValueError("R34 forbids R29 online reward")
    if str(getattr(config, "r31_effect_mode", "off")) == "real_reward":
        raise ValueError("R34 rejects the retired R31 reward path")
    for name in (
        "process_reward_injection",
        "outcome_residual_injection",
        "topology_role_injection",
        "topology_potential_injection",
        "skill_effect_reward_injection",
        "skill_force_reward_injection",
    ):
        if str(getattr(config, name, "none")).lower() != "none":
            raise ValueError(f"R34 forbids {name}")


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
    if not callable(getattr(agent.low, "evaluate_focal_sequence_log_probs", None)):
        raise RuntimeError("strict low actor lacks recurrent sequence replay")
    action_out = agent.low.actor_act.action_out
    if type(action_out).__name__ != "TanhDiagGaussian":
        raise RuntimeError("R34 requires the registered continuous tanh-Gaussian actor")
    if not hasattr(action_out, "fc_mean"):
        raise RuntimeError("R34 requires a trainable action mean head")
    return checkpoint, config, env, agent, metadata, total_steps, update_idx, device


def _clear_episode_buffers(agent) -> None:
    agent.segments.flush(env_id=0, reason="episode")
    agent.segments.pop_completed()
    agent.high_check_buffer.pop_completed()


def _descriptor_values(position_path: np.ndarray, focal_agent: int) -> np.ndarray:
    return np.asarray(
        InteractionModeDescriptor.build_raw(
            np.asarray(position_path, dtype=np.float64)[:, int(focal_agent), :]
        ),
        dtype=np.float64,
    )


def _collect_source_bank(
    *, env, agent, source_update: int, base_seed: int, device: torch.device
) -> list[SourceEpisode]:
    raw_env = env.env
    episodes: list[SourceEpisode] = []
    for episode_id in range(SOURCE_EPISODES):
        reset_seed = int(base_seed) + episode_id
        _set_seed(reset_seed, device)
        observations, info = env.reset(seed=reset_seed)
        state = np.asarray(info["state"], dtype=np.float32)
        agent.reset_env_state(0)
        obs_rows: list[np.ndarray] = []
        action_rows: list[np.ndarray] = []
        logp_rows: list[np.ndarray] = []
        skill_rows: list[np.ndarray] = []
        team_rows: list[int] = []
        block_snapshots: list[Any] = []
        block_observations: list[np.ndarray] = []
        block_position_paths: list[np.ndarray] = []
        done = False
        for block in range(BLOCKS_PER_EPISODE):
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
            pending = agent.high_check_buffer.pending[0]
            if pending is None or not bool(pending.decision_mask):
                raise RuntimeError("R34 source block did not start at a real R30 check")
            skills = np.asarray(agent.active_skills[0], dtype=np.int64).copy()
            if skills.shape != (N_AGENTS,) or np.any(skills < 0):
                raise RuntimeError("R34 source block lacks a complete active roster")
            block_snapshots.append(copy.deepcopy(raw_env.get_probe_snapshot()))
            block_observations.append(np.asarray(observations, dtype=np.float32).copy())
            positions = [raw_env.intrinsic_effect_view()]
            for primitive in range(WINDOW):
                obs_rows.append(np.asarray(observations, dtype=np.float32).copy())
                skill_rows.append(np.asarray(agent.active_skills[0], dtype=np.int64).copy())
                team_rows.append(int(agent.active_team_codes[0]))
                actions, logp, _values = agent.act_low(
                    observations,
                    env_id=0,
                    deterministic=False,
                    state=state,
                )
                actions_array = np.asarray(actions, dtype=np.float32)
                logp_array = np.asarray(logp, dtype=np.float32).reshape(N_AGENTS)
                action_rows.append(actions_array.copy())
                logp_rows.append(logp_array.copy())
                observations, reward, terminated, truncated, next_info = env.step(actions)
                state = np.asarray(next_info["next_state"], dtype=np.float32)
                positions.append(raw_env.intrinsic_effect_view())
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
                    block == BLOCKS_PER_EPISODE - 1 and primitive == WINDOW - 1
                ):
                    raise RuntimeError("Alice--Bob ended before a complete R34 source episode")
            block_position_paths.append(np.asarray(positions, dtype=np.float32))
        if not done:
            raise RuntimeError("R34 source episode did not terminate at 80 steps")
        episodes.append(
            SourceEpisode(
                episode_id=episode_id,
                observations=np.asarray(obs_rows, dtype=np.float32),
                actions=np.asarray(action_rows, dtype=np.float32),
                old_log_probs=np.asarray(logp_rows, dtype=np.float32),
                old_skills=np.asarray(skill_rows, dtype=np.int64),
                team_codes=np.asarray(team_rows, dtype=np.int64),
                block_snapshots=tuple(block_snapshots),
                block_observations=np.asarray(block_observations, dtype=np.float32),
                block_position_paths=np.asarray(block_position_paths, dtype=np.float32),
            )
        )
        _clear_episode_buffers(agent)
    if len(episodes) != SOURCE_EPISODES:
        raise RuntimeError("R34 source episode count mismatch")
    return episodes


def _source_descriptors(
    episodes: Sequence[SourceEpisode],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    descriptors: list[np.ndarray] = []
    old_labels: list[int] = []
    coordinates: list[tuple[int, int, int]] = []
    for episode in episodes:
        for block in range(BLOCKS_PER_EPISODE):
            for focal in range(N_AGENTS):
                descriptors.append(
                    _descriptor_values(episode.block_position_paths[block], focal)
                )
                old_labels.append(int(episode.old_skills[block * WINDOW, focal]))
                coordinates.append((int(episode.episode_id), block, focal))
    values = np.asarray(descriptors, dtype=np.float64)
    if values.shape != (SOURCE_EPISODES * BLOCKS_PER_EPISODE * N_AGENTS, WINDOW * 2):
        raise RuntimeError(f"R34 descriptor matrix has unexpected shape {values.shape}")
    if not np.all(np.isfinite(values)):
        raise RuntimeError("R34 source descriptors are non-finite")
    return (
        values,
        np.asarray(old_labels, dtype=np.int64),
        np.asarray(coordinates, dtype=np.int64),
    )


def _full_episode_replay_error(low, episodes: Sequence[SourceEpisode]) -> float:
    maximum = 0.0
    device = low.device
    zero = torch.zeros(low.hidden_dim, dtype=torch.float32, device=device)
    masks = torch.ones(EPISODE_STEPS, dtype=torch.float32, device=device)
    with torch.no_grad():
        for episode in episodes:
            for focal in range(N_AGENTS):
                replay = low.evaluate_focal_sequence_log_probs(
                    torch.as_tensor(
                        episode.observations[:, focal], dtype=torch.float32, device=device
                    ),
                    torch.as_tensor(
                        episode.old_skills[:, focal], dtype=torch.long, device=device
                    ),
                    torch.as_tensor(
                        episode.actions[:, focal], dtype=torch.float32, device=device
                    ),
                    zero,
                    team_codes_seq=torch.as_tensor(
                        episode.team_codes, dtype=torch.long, device=device
                    ),
                    masks_seq=masks,
                )
                stored = torch.as_tensor(
                    episode.old_log_probs[:, focal], dtype=torch.float32, device=device
                )
                maximum = max(
                    maximum,
                    float(torch.max(torch.abs(replay - stored)).detach().cpu().item()),
                )
    return maximum


def _run_length_multiset(label_sequences: np.ndarray) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for sequence in np.asarray(label_sequences, dtype=np.int64).reshape(-1, BLOCKS_PER_EPISODE):
        start = 0
        while start < sequence.size:
            end = start + 1
            while end < sequence.size and int(sequence[end]) == int(sequence[start]):
                end += 1
            result.append((int(sequence[start]), end - start))
            start = end
    return sorted(result)


def _sequence_multiset(label_sequences: np.ndarray) -> list[tuple[int, ...]]:
    return sorted(
        tuple(int(value) for value in row)
        for row in np.asarray(label_sequences, dtype=np.int64).reshape(-1, BLOCKS_PER_EPISODE)
    )


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
    if not snapshot or not any(name.startswith("low.actor_film.") for name in snapshot):
        raise RuntimeError("R34 could not inventory the strict low actor")
    return snapshot


def _parameter_max_difference(
    left: Mapping[str, torch.Tensor], right: Mapping[str, torch.Tensor]
) -> float:
    if set(left) != set(right):
        raise RuntimeError("paired R34 arms expose different parameter sets")
    return max(
        float(torch.max(torch.abs(left[name] - right[name])).item()) for name in left
    )


def _allowed_parameters(agent) -> tuple[list[torch.nn.Parameter], set[int]]:
    parameters = (
        list(agent.low.actor_film.parameters())
        + list(agent.low.actor_rnn.parameters())
        + list(agent.low.actor_act.action_out.fc_mean.parameters())
    )
    ids = {id(parameter) for parameter in parameters}
    if len(ids) != len(parameters) or not parameters:
        raise RuntimeError("R34 allowed actor parameter scope is malformed")
    return parameters, ids


def _all_agent_parameters(agent) -> list[torch.nn.Parameter]:
    result: list[torch.nn.Parameter] = []
    seen: set[int] = set()
    for module in vars(agent).values():
        if not isinstance(module, torch.nn.Module):
            continue
        for parameter in module.parameters():
            if id(parameter) not in seen:
                seen.add(id(parameter))
                result.append(parameter)
    return result


def _training_schedule(seed: int) -> list[list[int]]:
    rng = np.random.default_rng(int(seed) + 1_000_000)
    schedule: list[list[int]] = []
    for _epoch in range(DISTILL_EPOCHS):
        order = rng.permutation(TRAIN_SEQUENCES)
        for start in range(0, TRAIN_SEQUENCES, SEQUENCES_PER_BATCH):
            batch = [int(value) for value in order[start : start + SEQUENCES_PER_BATCH]]
            if len(batch) != SEQUENCES_PER_BATCH:
                raise RuntimeError("R34 distillation batch is not eight full sequences")
            schedule.append(batch)
    if len(schedule) != OPTIMIZER_CALLS:
        raise RuntimeError("R34 training schedule is not exactly 60 Adam calls")
    return schedule


def _distill_arm(
    *,
    arm: str,
    agent,
    train_episodes: Sequence[SourceEpisode],
    block_labels: np.ndarray,
    schedule: Sequence[Sequence[int]],
) -> dict[str, Any]:
    if arm not in {"real_modes", "max_hamming_episode_sequence_sham"}:
        raise ValueError(f"unknown R34 distillation arm {arm!r}")
    if block_labels.shape != (TRAIN_SOURCE_EPISODES, N_AGENTS, BLOCKS_PER_EPISODE):
        raise ValueError("R34 arm labels must have shape [24,2,8]")
    before = _parameter_snapshot(agent)
    allowed, allowed_ids = _allowed_parameters(agent)
    all_parameters = _all_agent_parameters(agent)
    original_requires_grad = {
        id(parameter): bool(parameter.requires_grad) for parameter in all_parameters
    }
    for parameter in all_parameters:
        parameter.requires_grad_(id(parameter) in allowed_ids)
    agent.low.actor_rnn.train()
    optimizer = torch.optim.Adam(allowed, lr=DISTILL_LR)
    updates: list[dict[str, Any]] = []
    escaped_tensor_count = 0
    escaped_max_abs = 0.0
    finite = True
    for update_index, batch in enumerate(schedule):
        observations_batch: list[np.ndarray] = []
        actions_batch: list[np.ndarray] = []
        labels_batch: list[np.ndarray] = []
        teams_batch: list[np.ndarray] = []
        for sequence_index in batch:
            episode_index = int(sequence_index) // N_AGENTS
            focal = int(sequence_index) % N_AGENTS
            episode = train_episodes[episode_index]
            step_labels = np.repeat(block_labels[episode_index, focal], WINDOW)
            observations_batch.append(episode.observations[:, focal])
            actions_batch.append(episode.actions[:, focal])
            labels_batch.append(step_labels)
            teams_batch.append(episode.team_codes)
        batch_loss = full_episode_distillation_loss(
            agent.low,
            np.asarray(observations_batch, dtype=np.float32),
            np.asarray(actions_batch, dtype=np.float32),
            np.asarray(labels_batch, dtype=np.int64),
            np.zeros(
                (SEQUENCES_PER_BATCH, int(agent.low.hidden_dim)), dtype=np.float32
            ),
            team_codes=np.asarray(teams_batch, dtype=np.int64),
        )
        for parameter in all_parameters:
            parameter.grad = None
        optimizer.zero_grad(set_to_none=True)
        batch_loss.backward()
        escaped = [
            parameter
            for parameter in all_parameters
            if id(parameter) not in allowed_ids and parameter.grad is not None
        ]
        escaped_tensor_count += len(escaped)
        if escaped:
            escaped_max_abs = max(
                escaped_max_abs,
                max(
                    float(parameter.grad.detach().abs().max().cpu().item())
                    for parameter in escaped
                ),
            )
            raise RuntimeError("R34 gradient escaped the registered low-actor scope")
        grad_norm = torch.nn.utils.clip_grad_norm_(allowed, GRAD_CLIP)
        finite_step = bool(
            torch.isfinite(batch_loss).item()
            and torch.isfinite(grad_norm).item()
            and all(
                parameter.grad is None or bool(torch.isfinite(parameter.grad).all().item())
                for parameter in allowed
            )
        )
        finite = finite and finite_step
        if not finite_step:
            raise RuntimeError("R34 distillation produced a non-finite loss or gradient")
        optimizer.step()
        updates.append(
            {
                "optimizer_call": update_index + 1,
                "epoch": update_index // (TRAIN_SEQUENCES // SEQUENCES_PER_BATCH) + 1,
                "sequence_indices": list(batch),
                "loss": float(batch_loss.detach().cpu().item()),
                "gradient_norm": float(grad_norm.detach().cpu().item()),
            }
        )
        print(
            f"[R34] arm={arm} optimizer_call={update_index + 1}/{OPTIMIZER_CALLS} "
            f"loss={float(batch_loss.detach().cpu().item()):.6g}",
            flush=True,
        )
    for parameter in all_parameters:
        parameter.requires_grad_(original_requires_grad[id(parameter)])
    agent.low.eval()
    after = _parameter_snapshot(agent)
    drift = parameter_drift_metrics(
        before,
        after,
        allowed_prefixes=(
            "low.actor_film.",
            "low.actor_rnn.",
            "low.actor_act.action_out.fc_mean.",
        ),
    )
    return {
        "arm": arm,
        "optimizer_calls": len(updates),
        "epochs": DISTILL_EPOCHS,
        "sequence_batch_size": SEQUENCES_PER_BATCH,
        "full_sequence_replay_calls": len(updates) * SEQUENCES_PER_BATCH,
        "finite_optimizer": finite,
        "updates": updates,
        "parameter_drift": drift,
        "escaped_gradient_tensor_count": escaped_tensor_count,
        "escaped_gradient_max_abs": escaped_max_abs,
        "task_reward_objective_reads": 0,
        "value_or_gae_reads": 0,
        "critic_updates": 0,
        "high_policy_updates": 0,
        "posterior_updates": 0,
        "normal_ppo_updates": 0,
    }


def _single_actor_act(
    low,
    *,
    observation: np.ndarray,
    skill: int,
    team_code: int,
    actor_hidden: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    device = low.device
    obs_t = torch.as_tensor(observation, dtype=torch.float32, device=device).reshape(1, -1)
    skill_t = torch.tensor([int(skill)], dtype=torch.long, device=device)
    team_t = torch.tensor([int(team_code)], dtype=torch.long, device=device)
    hidden_t = torch.as_tensor(actor_hidden, dtype=torch.float32, device=device)
    if hidden_t.ndim == 1:
        hidden_t = hidden_t.unsqueeze(0)
    with torch.no_grad():
        features = low._actor_features(obs_t, skill_t, team_t)
        features, next_hidden = low.actor_rnn(
            features,
            hidden_t,
            torch.ones(1, 1, dtype=torch.float32, device=device),
        )
        action, _logp = low.actor_act(features, deterministic=False)
    return (
        action.detach().cpu().numpy().astype(np.float32).reshape(-1),
        next_hidden.detach().cpu().numpy().astype(np.float32).reshape(1, -1),
    )


def _prefix_hidden(low, episode: SourceEpisode, focal: int, stop: int) -> np.ndarray:
    if int(stop) == 0:
        return np.zeros((1, int(low.hidden_dim)), dtype=np.float32)
    hidden = replay_actor_prefix_hidden(
        low,
        episode.observations[:stop, focal],
        episode.old_skills[:stop, focal],
        team_codes=episode.team_codes[:stop],
        detach=True,
    )
    if isinstance(hidden, torch.Tensor):
        hidden = hidden.detach().cpu().numpy()
    return np.asarray(hidden, dtype=np.float32).reshape(1, -1)


def _run_forced_branch(
    *,
    env,
    focal_low,
    source_low,
    episode: SourceEpisode,
    block: int,
    focal: int,
    skill: int,
    branch_seed: int,
    scaler,
    device: torch.device,
) -> np.ndarray:
    raw_env = env.env
    raw_env.set_probe_snapshot(copy.deepcopy(episode.block_snapshots[block]))
    raw_env.np_random = np.random.default_rng(int(branch_seed))
    _set_seed(int(branch_seed), device)
    start = int(block) * WINDOW
    observations = np.asarray(episode.block_observations[block], dtype=np.float32).copy()
    focal_hidden = _prefix_hidden(focal_low, episode, focal, start)
    teammate = 1 - int(focal)
    teammate_hidden = _prefix_hidden(source_low, episode, teammate, start)
    teammate_skill = int(episode.old_skills[start, teammate])
    team_code = int(episode.team_codes[start])
    position_path = [raw_env.intrinsic_effect_view()]
    for primitive in range(WINDOW):
        focal_action, focal_hidden = _single_actor_act(
            focal_low,
            observation=observations[focal],
            skill=int(skill),
            team_code=team_code,
            actor_hidden=focal_hidden,
        )
        teammate_action, teammate_hidden = _single_actor_act(
            source_low,
            observation=observations[teammate],
            skill=teammate_skill,
            team_code=team_code,
            actor_hidden=teammate_hidden,
        )
        actions = np.zeros((N_AGENTS, focal_action.size), dtype=np.float32)
        actions[focal] = focal_action
        actions[teammate] = teammate_action
        observations, _reward, terminated, truncated, _info = env.step(actions)
        position_path.append(raw_env.intrinsic_effect_view())
        if (terminated or truncated) and primitive != WINDOW - 1:
            raise RuntimeError("R34 forced branch terminated before W=10")
    raw_descriptor = scaler.build_raw(
        np.asarray(position_path, dtype=np.float64)[:, focal, :]
    )
    standardized = scaler.transform(raw_descriptor)
    return np.asarray(standardized, dtype=np.float64).reshape(-1)


def _forced_evaluation(
    *,
    arm: str,
    env,
    agent,
    source_low,
    heldout_episodes: Sequence[SourceEpisode],
    scaler,
    base_seed: int,
    device: torch.device,
) -> dict[str, Any]:
    if len(heldout_episodes) != HELDOUT_SOURCE_EPISODES:
        raise RuntimeError("R34 forced evaluator requires eight heldout source episodes")
    descriptor_dim = int(np.asarray(scaler.mean).size)
    values = np.empty(
        (
            HELDOUT_SOURCE_EPISODES * BLOCKS_PER_EPISODE,
            N_AGENTS,
            N_SKILLS,
            REPLICAS,
            descriptor_dim,
        ),
        dtype=np.float64,
    )
    branch_seeds = np.empty(
        (
            HELDOUT_SOURCE_EPISODES * BLOCKS_PER_EPISODE,
            N_AGENTS,
            N_SKILLS,
            REPLICAS,
        ),
        dtype=np.int64,
    )
    for local_episode, episode in enumerate(heldout_episodes):
        for block in range(BLOCKS_PER_EPISODE):
            context = local_episode * BLOCKS_PER_EPISODE + block
            for focal in range(N_AGENTS):
                for skill in range(N_SKILLS):
                    for replica in range(REPLICAS):
                        branch_seed = (
                            int(base_seed)
                            + 20_000_000
                            + context * 100
                            + focal * 10
                            + replica
                        )
                        values[context, focal, skill, replica] = _run_forced_branch(
                            env=env,
                            focal_low=agent.low,
                            source_low=source_low,
                            episode=episode,
                            block=block,
                            focal=focal,
                            skill=skill,
                            branch_seed=branch_seed,
                            scaler=scaler,
                            device=device,
                        )
                        branch_seeds[context, focal, skill, replica] = branch_seed
    within_skill_crn = bool(
        np.all(branch_seeds == branch_seeds[:, :, :1, :])
    )
    replica_independent = bool(
        np.all(branch_seeds[..., 0] != branch_seeds[..., 1])
    )
    unique_context_agent_replica = bool(
        np.unique(branch_seeds[:, :, 0, :]).size
        == values.shape[0] * N_AGENTS * REPLICAS
    )
    if not within_skill_crn or not replica_independent or not unique_context_agent_replica:
        raise RuntimeError("R34 forced random-stream contract is invalid")
    return {
        "arm": arm,
        "descriptors": values,
        "branch_seeds": branch_seeds,
        "branch_count": int(np.prod(values.shape[:-1])),
        "primitive_steps": int(np.prod(values.shape[:-1])) * WINDOW,
        "branch_length": WINDOW,
        "within_replica_skill_crn": within_skill_crn,
        "replicas_independent": replica_independent,
        "unique_context_agent_replica_streams": unique_context_agent_replica,
    }


def _position_cell(position_view: np.ndarray) -> int:
    positions = np.asarray(position_view, dtype=np.float64)
    if positions.shape != (N_AGENTS, 2):
        raise ValueError("R34 coverage requires normalized [2,2] positions")
    clipped = np.clip(positions, 0.0, np.nextafter(1.0, 0.0))
    bins = np.floor(clipped * POSITION_BINS).astype(np.int64).reshape(-1)
    cell = 0
    for value in bins:
        cell = cell * POSITION_BINS + int(value)
    return cell


def _natural_transport(
    *,
    arm: str,
    env,
    agent,
    source_update: int,
    scaler,
    prototypes: np.ndarray,
    base_seed: int,
    device: torch.device,
) -> dict[str, Any]:
    raw_env = env.env
    consistency_by_reset: list[float] = []
    coverage_by_reset: list[float] = []
    global_cells: set[int] = set()
    task_reward: list[float] = []
    final_task_metrics: list[dict[str, float]] = []
    all_rows = []
    for episode_id in range(NATURAL_EPISODES):
        reset_seed = int(base_seed) + 30_000_000 + episode_id
        _set_seed(reset_seed, device)
        observations, info = env.reset(seed=reset_seed)
        state = np.asarray(info["state"], dtype=np.float32)
        agent.reset_env_state(0)
        episode_cells: set[int] = set()
        consistency_rows: list[float] = []
        episode_reward = 0.0
        last_reward_info: dict[str, Any] = {}
        done = False
        for block in range(BLOCKS_PER_EPISODE):
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
            active_skills = np.asarray(agent.active_skills[0], dtype=np.int64).copy()
            position_path = [raw_env.intrinsic_effect_view()]
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
                position_path.append(view)
                episode_cells.add(_position_cell(view))
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
                    block == BLOCKS_PER_EPISODE - 1 and primitive == WINDOW - 1
                ):
                    raise RuntimeError("R34 natural episode ended before 80 steps")
            path = np.asarray(position_path, dtype=np.float64)
            for focal in range(N_AGENTS):
                raw_descriptor = scaler.build_raw(path[:, focal, :])
                standardized = scaler.transform(raw_descriptor)
                predicted = int(nearest_prototype(standardized, prototypes))
                consistency_rows.append(float(predicted == int(active_skills[focal])))
        if not done:
            raise RuntimeError("R34 natural episode did not terminate at 80 steps")
        consistency_by_reset.append(float(np.mean(consistency_rows)))
        coverage_by_reset.append(
            len(episode_cells) / float(POSITION_BINS ** (N_AGENTS * 2))
        )
        global_cells.update(episode_cells)
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
            np.asarray(switch_skills, dtype=np.int64), minlength=N_SKILLS
        ).astype(np.float64)
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
    task_diagnostics = {"mean_sparse_task_reward": float(np.mean(task_reward))}
    for name in final_task_metrics[0]:
        task_diagnostics[f"mean_final_{name}"] = float(
            np.mean([row[name] for row in final_task_metrics])
        )
    return {
        "arm": arm,
        "episode_count": NATURAL_EPISODES,
        "primitive_steps": NATURAL_EPISODES * EPISODE_STEPS,
        "consistency_by_reset": np.asarray(consistency_by_reset, dtype=np.float64),
        "consistency_mean": float(np.mean(consistency_by_reset)),
        "coverage_by_reset": np.asarray(coverage_by_reset, dtype=np.float64),
        "coverage_union_cells": len(global_cells),
        "coverage_union_fraction": len(global_cells)
        / float(POSITION_BINS ** (N_AGENTS * 2)),
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


def _cluster_bootstrap_ci(
    values: np.ndarray,
    *,
    repetitions: int,
    rng: np.random.Generator,
    statistic: Callable[[np.ndarray], float],
) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim < 1 or array.shape[0] <= 1 or not np.all(np.isfinite(array)):
        raise ValueError("R34 cluster bootstrap requires finite independent clusters")
    draws = np.empty(int(repetitions), dtype=np.float64)
    for index in range(int(repetitions)):
        sampled = rng.integers(0, array.shape[0], size=array.shape[0])
        draws[index] = float(statistic(array[sampled]))
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def _result_fields(value: Any) -> dict[str, Any]:
    if hasattr(value, "__dataclass_fields__"):
        return {name: getattr(value, name) for name in value.__dataclass_fields__}
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"cannot serialize R34 result value of type {type(value)!r}")


def _drift_max_matching(drift: Mapping[str, Any], predicate: Callable[[str], bool]) -> float:
    selected = [
        float(row["max_abs"])
        for name, row in drift["parameters"].items()
        if predicate(str(name))
    ]
    return max(selected, default=0.0)


def _normalized_mutual_information(overlap: np.ndarray) -> float:
    counts = np.asarray(overlap, dtype=np.float64)
    total = float(np.sum(counts))
    if counts.ndim != 2 or total <= 0.0:
        raise ValueError("R34 old-skill overlap must be a non-empty matrix")
    joint = counts / total
    left = np.sum(joint, axis=1, keepdims=True)
    right = np.sum(joint, axis=0, keepdims=True)
    expected = left @ right
    positive = joint > 0.0
    mutual_information = float(
        np.sum(joint[positive] * np.log(joint[positive] / expected[positive]))
    )
    left_positive = left[left > 0.0]
    right_positive = right[right > 0.0]
    left_entropy = float(-np.sum(left_positive * np.log(left_positive)))
    right_entropy = float(-np.sum(right_positive * np.log(right_positive)))
    denominator = math.sqrt(left_entropy * right_entropy)
    return mutual_information / denominator if denominator > 0.0 else 0.0


def _forced_metrics(evaluation: Mapping[str, Any], prototypes: np.ndarray) -> dict[str, Any]:
    descriptors = np.asarray(evaluation["descriptors"], dtype=np.float64)
    targets = np.broadcast_to(
        np.arange(N_SKILLS, dtype=np.int64)[None, None, :, None],
        descriptors.shape[:-1],
    )
    fidelity = causal_mode_fidelity(descriptors, targets, prototypes)
    separation = between_within_mode_ratio(
        descriptors,
        epsilon=DESCRIPTOR_EPSILON,
    )
    correct = (
        np.asarray(fidelity.assignments, dtype=np.int64) == targets
    ).astype(np.float64)
    # Contexts are ordered as eight blocks inside each of eight source episodes.
    fidelity_clusters = correct.reshape(
        HELDOUT_SOURCE_EPISODES,
        BLOCKS_PER_EPISODE,
        N_AGENTS,
        N_SKILLS,
        REPLICAS,
    )
    snr_clusters = np.asarray(separation.ratio, dtype=np.float64).reshape(
        HELDOUT_SOURCE_EPISODES,
        BLOCKS_PER_EPISODE,
        N_AGENTS,
    )
    return {
        "fidelity": float(fidelity.fidelity),
        "fidelity_per_skill": np.asarray(fidelity.per_skill, dtype=np.float64),
        "fidelity_counts": np.asarray(fidelity.counts, dtype=np.int64),
        "fidelity_correct": np.asarray(fidelity.correct, dtype=np.int64),
        "fidelity_clusters": fidelity_clusters,
        "assignments": np.asarray(fidelity.assignments, dtype=np.int64),
        "between": np.asarray(separation.between, dtype=np.float64),
        "within": np.asarray(separation.within, dtype=np.float64),
        "ratio": np.asarray(separation.ratio, dtype=np.float64),
        "snr_clusters": snr_clusters,
        "median_ratio": float(separation.median_ratio),
    }


def _forced_metric_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        name: item
        for name, item in value.items()
        if name not in {"fidelity_clusters", "snr_clusters"}
    }


def _natural_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    return dict(value)


def _gate_decision(
    *,
    m0: bool,
    degenerate_sham: bool,
    m1: bool,
    m2a: bool,
    m2b: bool,
    m3: bool,
) -> tuple[str, str]:
    if not m0:
        return (
            "INVALID_R34_IMPLEMENTATION",
            "repair only the concrete count, replay, scope, random-stream, or finite defect",
        )
    if degenerate_sham:
        return (
            "FAIL_M1_DEGENERATE_LABEL_SEQUENCE",
            "retire the registered R34 gate because max-Hamming sham cannot sufficiently break label attribution",
        )
    if not m1:
        return (
            "FAIL_M1_RETIRE_R34_BHMD",
            "retire balanced hindsight mode distillation",
        )
    if not m2a:
        return (
            "PASS_CODEBOOK_FAIL_ZERO_SHOT_SELECTOR",
            "preserve causal codebook evidence but reject zero-shot use by the frozen R30 selector",
        )
    if not m2b:
        return (
            "PASS_MODE_USE_FAIL_EXPLORATION_TRANSPORT",
            "preserve natural mode-use evidence but reject exploration transport",
        )
    if not m3:
        return (
            "FAIL_M3_R30_COLLAPSE",
            "retire R34 because mode use coincides with R30 skill-supply or lifetime collapse",
        )
    return (
        "PASS_R34_BHMD",
        "authorize only preparation of sparse-source real-modes versus max-Hamming-sham normal training",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    print("[R34] phase=source_natural_episode_bank", flush=True)
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
    source_before = _parameter_snapshot(source_agent)
    source_episodes = _collect_source_bank(
        env=source_env,
        agent=source_agent,
        source_update=source_update,
        base_seed=int(args.seed),
        device=device,
    )
    source_replay_error = _full_episode_replay_error(source_agent.low, source_episodes)
    raw_descriptors, old_labels, coordinates = _source_descriptors(source_episodes)
    train_mask = coordinates[:, 0] < TRAIN_SOURCE_EPISODES
    heldout_mask = ~train_mask
    train_raw = raw_descriptors[train_mask]
    heldout_raw = raw_descriptors[heldout_mask]
    train_old_labels = old_labels[train_mask]
    if train_raw.shape != (TRAIN_DESCRIPTOR_ROWS, WINDOW * 2):
        raise RuntimeError("R34 train descriptor split is not 384x20")
    if heldout_raw.shape != (HELDOUT_DESCRIPTOR_ROWS, WINDOW * 2):
        raise RuntimeError("R34 heldout descriptor split is not 128x20")

    print("[R34] phase=balanced_train_only_mode_discovery", flush=True)
    scaler = InteractionModeDescriptor.fit(
        train_raw,
        window=WINDOW,
        zero_std_epsilon=DESCRIPTOR_EPSILON,
    )
    train_standardized = scaler.transform(train_raw)
    prototype_fit = fit_exact_balanced_prototypes(
        train_standardized,
        n_modes=N_SKILLS,
        seed=int(args.seed),
        max_iter=50,
        expected_rows=TRAIN_DESCRIPTOR_ROWS,
    )
    alignment = hungarian_align_to_existing_skills(
        prototype_fit.prototypes,
        prototype_fit.assignments,
        train_old_labels,
        n_skills=N_SKILLS,
    )
    old_skill_nmi = _normalized_mutual_information(alignment.overlap)
    prototypes = np.asarray(alignment.prototypes_by_skill, dtype=np.float64)
    real_sequences = np.empty(
        (TRAIN_SOURCE_EPISODES, N_AGENTS, BLOCKS_PER_EPISODE), dtype=np.int64
    )
    train_coordinates = coordinates[train_mask]
    for label, (episode_id, block, focal) in zip(
        alignment.aligned_assignments,
        train_coordinates,
        strict=True,
    ):
        real_sequences[int(episode_id), int(focal), int(block)] = int(label)
    sham_result = build_max_hamming_episode_sham(real_sequences)
    sham_sequences = np.asarray(sham_result.sequences, dtype=np.int64)
    label_agreement = float(np.mean(real_sequences == sham_sequences))

    train_episodes = source_episodes[:TRAIN_SOURCE_EPISODES]
    heldout_episodes = source_episodes[TRAIN_SOURCE_EPISODES:]
    frozen_source_low = copy.deepcopy(source_agent.low).to(device)
    frozen_source_low.eval()
    for parameter in frozen_source_low.parameters():
        parameter.requires_grad_(False)

    print("[R34] phase=create_source_real_sham_arms", flush=True)
    real = _make_agent_and_env(args, seed_offset=10_000)
    sham = _make_agent_and_env(args, seed_offset=20_000)
    real_env, real_agent = real[2], real[3]
    sham_env, sham_agent = sham[2], sham[3]
    real_before = _parameter_snapshot(real_agent)
    sham_before = _parameter_snapshot(sham_agent)
    initial_source_real = _parameter_max_difference(source_before, real_before)
    initial_source_sham = _parameter_max_difference(source_before, sham_before)
    initial_real_sham = _parameter_max_difference(real_before, sham_before)
    schedule = _training_schedule(int(args.seed))

    try:
        print("[R34] phase=real_mode_distillation", flush=True)
        real_train = _distill_arm(
            arm="real_modes",
            agent=real_agent,
            train_episodes=train_episodes,
            block_labels=real_sequences,
            schedule=schedule,
        )
        print("[R34] phase=max_hamming_sham_distillation", flush=True)
        sham_train = _distill_arm(
            arm="max_hamming_episode_sequence_sham",
            agent=sham_agent,
            train_episodes=train_episodes,
            block_labels=sham_sequences,
            schedule=schedule,
        )

        print("[R34] phase=three_arm_heldout_forced_evaluation", flush=True)
        source_forced = _forced_evaluation(
            arm="frozen_source",
            env=source_env,
            agent=source_agent,
            source_low=frozen_source_low,
            heldout_episodes=heldout_episodes,
            scaler=scaler,
            base_seed=int(args.seed),
            device=device,
        )
        real_forced = _forced_evaluation(
            arm="real_modes",
            env=real_env,
            agent=real_agent,
            source_low=frozen_source_low,
            heldout_episodes=heldout_episodes,
            scaler=scaler,
            base_seed=int(args.seed),
            device=device,
        )
        sham_forced = _forced_evaluation(
            arm="max_hamming_episode_sequence_sham",
            env=sham_env,
            agent=sham_agent,
            source_low=frozen_source_low,
            heldout_episodes=heldout_episodes,
            scaler=scaler,
            base_seed=int(args.seed),
            device=device,
        )
        source_metrics = _forced_metrics(source_forced, prototypes)
        real_metrics = _forced_metrics(real_forced, prototypes)
        sham_metrics = _forced_metrics(sham_forced, prototypes)

        print("[R34] phase=three_arm_paired_natural_transport", flush=True)
        source_natural = _natural_transport(
            arm="frozen_source",
            env=source_env,
            agent=source_agent,
            source_update=source_update,
            scaler=scaler,
            prototypes=prototypes,
            base_seed=int(args.seed),
            device=device,
        )
        real_natural = _natural_transport(
            arm="real_modes",
            env=real_env,
            agent=real_agent,
            source_update=source_update,
            scaler=scaler,
            prototypes=prototypes,
            base_seed=int(args.seed),
            device=device,
        )
        sham_natural = _natural_transport(
            arm="max_hamming_episode_sequence_sham",
            env=sham_env,
            agent=sham_agent,
            source_update=source_update,
            scaler=scaler,
            prototypes=prototypes,
            base_seed=int(args.seed),
            device=device,
        )
    finally:
        source_env.close()
        real_env.close()
        sham_env.close()

    source_after = _parameter_snapshot(source_agent)
    real_after = _parameter_snapshot(real_agent)
    sham_after = _parameter_snapshot(sham_agent)
    source_drift = parameter_drift_metrics(
        source_before,
        source_after,
        allowed_prefixes=(
            "low.actor_film.",
            "low.actor_rnn.",
            "low.actor_act.action_out.fc_mean.",
        ),
    )
    real_drift = parameter_drift_metrics(
        real_before,
        real_after,
        allowed_prefixes=(
            "low.actor_film.",
            "low.actor_rnn.",
            "low.actor_act.action_out.fc_mean.",
        ),
    )
    sham_drift = parameter_drift_metrics(
        sham_before,
        sham_after,
        allowed_prefixes=(
            "low.actor_film.",
            "low.actor_rnn.",
            "low.actor_act.action_out.fc_mean.",
        ),
    )

    bootstrap_rng = np.random.default_rng(40_034_031)
    real_fidelity = np.asarray(real_metrics["fidelity_clusters"], dtype=np.float64)
    sham_fidelity = np.asarray(sham_metrics["fidelity_clusters"], dtype=np.float64)
    source_fidelity = np.asarray(source_metrics["fidelity_clusters"], dtype=np.float64)
    fidelity_real_sham = real_fidelity - sham_fidelity
    fidelity_real_source = real_fidelity - source_fidelity
    fidelity_real_sham_ci = _cluster_bootstrap_ci(
        fidelity_real_sham,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.mean(rows)),
    )
    fidelity_real_source_ci = _cluster_bootstrap_ci(
        fidelity_real_source,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.mean(rows)),
    )

    real_snr = np.asarray(real_metrics["snr_clusters"], dtype=np.float64)
    sham_snr = np.asarray(sham_metrics["snr_clusters"], dtype=np.float64)
    source_snr = np.asarray(source_metrics["snr_clusters"], dtype=np.float64)
    snr_real_ci = _cluster_bootstrap_ci(
        real_snr,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.median(rows)),
    )
    snr_real_sham = real_snr - sham_snr
    snr_real_source = real_snr - source_snr
    snr_real_sham_ci = _cluster_bootstrap_ci(
        snr_real_sham,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.median(rows)),
    )
    snr_real_source_ci = _cluster_bootstrap_ci(
        snr_real_source,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.median(rows)),
    )

    natural_real_consistency = np.asarray(
        real_natural["consistency_by_reset"], dtype=np.float64
    )
    natural_sham_consistency = np.asarray(
        sham_natural["consistency_by_reset"], dtype=np.float64
    )
    natural_source_consistency = np.asarray(
        source_natural["consistency_by_reset"], dtype=np.float64
    )
    consistency_real_sham = natural_real_consistency - natural_sham_consistency
    consistency_real_source = natural_real_consistency - natural_source_consistency
    consistency_real_sham_ci = _cluster_bootstrap_ci(
        consistency_real_sham,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.mean(rows)),
    )
    consistency_real_source_ci = _cluster_bootstrap_ci(
        consistency_real_source,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.mean(rows)),
    )

    real_coverage = np.asarray(real_natural["coverage_by_reset"], dtype=np.float64)
    sham_coverage = np.asarray(sham_natural["coverage_by_reset"], dtype=np.float64)
    source_coverage = np.asarray(source_natural["coverage_by_reset"], dtype=np.float64)
    coverage_real_sham_ci = _cluster_bootstrap_ci(
        real_coverage - sham_coverage,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.mean(rows)),
    )
    coverage_real_source_ci = _cluster_bootstrap_ci(
        real_coverage - source_coverage,
        repetitions=int(args.bootstrap_repetitions),
        rng=bootstrap_rng,
        statistic=lambda rows: float(np.mean(rows)),
    )

    fidelity_gain_sham = float(real_metrics["fidelity"] - sham_metrics["fidelity"])
    fidelity_gain_source = float(real_metrics["fidelity"] - source_metrics["fidelity"])
    snr_gain_sham = float(np.median(snr_real_sham))
    snr_gain_source = float(np.median(snr_real_source))
    consistency_gain_sham = float(
        real_natural["consistency_mean"] - sham_natural["consistency_mean"]
    )
    consistency_gain_source = float(
        real_natural["consistency_mean"] - source_natural["consistency_mean"]
    )
    coverage_ratio_sham = float(real_natural["coverage_union_fraction"]) / (
        float(sham_natural["coverage_union_fraction"]) + 1e-12
    )
    coverage_ratio_source = float(real_natural["coverage_union_fraction"]) / (
        float(source_natural["coverage_union_fraction"]) + 1e-12
    )

    global_counts_real = np.bincount(real_sequences.reshape(-1), minlength=N_SKILLS)
    global_counts_sham = np.bincount(sham_sequences.reshape(-1), minlength=N_SKILLS)
    agent_counts_real = np.stack(
        [np.bincount(real_sequences[:, agent].reshape(-1), minlength=N_SKILLS) for agent in range(N_AGENTS)]
    )
    agent_counts_sham = np.stack(
        [np.bincount(sham_sequences[:, agent].reshape(-1), minlength=N_SKILLS) for agent in range(N_AGENTS)]
    )
    exact_forced_branches = (
        HELDOUT_SOURCE_EPISODES
        * BLOCKS_PER_EPISODE
        * N_AGENTS
        * N_SKILLS
        * REPLICAS
    )
    no_forbidden_updates = all(
        int(arm[name]) == 0
        for arm in (real_train, sham_train)
        for name in (
            "task_reward_objective_reads",
            "value_or_gae_reads",
            "critic_updates",
            "high_policy_updates",
            "posterior_updates",
            "normal_ppo_updates",
        )
    )
    m0_checks = {
        "source_episode_split_32_24_8": (
            len(source_episodes) == SOURCE_EPISODES
            and len(train_episodes) == TRAIN_SOURCE_EPISODES
            and len(heldout_episodes) == HELDOUT_SOURCE_EPISODES
        ),
        "descriptor_counts_384_128": (
            train_raw.shape[0] == TRAIN_DESCRIPTOR_ROWS
            and heldout_raw.shape[0] == HELDOUT_DESCRIPTOR_ROWS
        ),
        "descriptor_schema_focal_only": (
            train_raw.shape[1] == WINDOW * 2
            and tuple(scaler.feature_names)
            == tuple(
                f"focal_d{axis}_t{step}"
                for step in range(1, WINDOW + 1)
                for axis in ("x", "y")
            )
        ),
        "train_only_scaler": scaler.n_fit_rows == TRAIN_DESCRIPTOR_ROWS,
        "exact_balanced_mode_counts": np.array_equal(
            np.asarray(prototype_fit.counts),
            np.full(N_SKILLS, ROWS_PER_MODE, dtype=np.int64),
        ),
        "finite_prototypes": bool(np.all(np.isfinite(prototypes))),
        "hungarian_bijection": (
            np.unique(alignment.prototype_to_skill).size == N_SKILLS
            and np.unique(alignment.skill_to_prototype).size == N_SKILLS
        ),
        "sham_no_self_donor": bool(
            np.all(
                np.asarray(sham_result.donor_map)
                != np.arange(TRAIN_SOURCE_EPISODES, dtype=np.int64)[:, None]
            )
        ),
        "sham_global_label_counts": np.array_equal(global_counts_real, global_counts_sham),
        "sham_per_agent_label_counts": np.array_equal(agent_counts_real, agent_counts_sham),
        "sham_block_position_label_counts": all(
            np.array_equal(
                np.bincount(
                    real_sequences[:, agent, block], minlength=N_SKILLS
                ),
                np.bincount(
                    sham_sequences[:, agent, block], minlength=N_SKILLS
                ),
            )
            for agent in range(N_AGENTS)
            for block in range(BLOCKS_PER_EPISODE)
        ),
        "sham_sequence_multiset": all(
            _sequence_multiset(real_sequences[:, agent])
            == _sequence_multiset(sham_sequences[:, agent])
            for agent in range(N_AGENTS)
        ),
        "sham_run_length_multiset": all(
            _run_length_multiset(real_sequences[:, agent])
            == _run_length_multiset(sham_sequences[:, agent])
            for agent in range(N_AGENTS)
        ),
        "three_arm_initial_parameters": max(
            initial_source_real,
            initial_source_sham,
            initial_real_sham,
        )
        <= THRESHOLDS["paired_initial_parameter_max_abs"],
        "source_full_episode_replay": source_replay_error
        <= THRESHOLDS["source_replay_logp_max_error"],
        "optimizer_calls_exact": (
            real_train["optimizer_calls"] == OPTIMIZER_CALLS
            and sham_train["optimizer_calls"] == OPTIMIZER_CALLS
        ),
        "finite_optimizer": bool(
            real_train["finite_optimizer"] and sham_train["finite_optimizer"]
        ),
        "nonzero_allowed_gradient_in_each_trained_arm": all(
            any(float(update["gradient_norm"]) > 0.0 for update in arm["updates"])
            for arm in (real_train, sham_train)
        ),
        "gradient_scope": all(
            arm["escaped_gradient_tensor_count"] == 0
            and arm["escaped_gradient_max_abs"] == 0.0
            for arm in (real_train, sham_train)
        ),
        "all_frozen_parameters_static": max(
            float(real_drift["other_max_abs"]),
            float(sham_drift["other_max_abs"]),
            float(source_drift["all_max_abs"]),
        )
        <= THRESHOLDS["other_parameter_max_abs_drift"],
        "source_anchor_present_and_static": float(source_drift["all_max_abs"])
        <= THRESHOLDS["other_parameter_max_abs_drift"],
        "forced_branch_counts": all(
            evaluation["branch_count"] == exact_forced_branches
            and evaluation["primitive_steps"] == exact_forced_branches * WINDOW
            for evaluation in (source_forced, real_forced, sham_forced)
        ),
        "forced_random_stream_contract": all(
            evaluation["within_replica_skill_crn"]
            and evaluation["replicas_independent"]
            and evaluation["unique_context_agent_replica_streams"]
            for evaluation in (source_forced, real_forced, sham_forced)
        ),
        "cross_arm_common_random_numbers": (
            np.array_equal(source_forced["branch_seeds"], real_forced["branch_seeds"])
            and np.array_equal(source_forced["branch_seeds"], sham_forced["branch_seeds"])
        ),
        "high_controller_and_keep_policy_static": max(
            _drift_max_matching(real_drift, lambda name: name.startswith("high.")),
            _drift_max_matching(sham_drift, lambda name: name.startswith("high.")),
            _drift_max_matching(source_drift, lambda name: name.startswith("high.")),
        )
        <= THRESHOLDS["other_parameter_max_abs_drift"],
        "low_critic_and_action_log_std_static": max(
            _drift_max_matching(
                real_drift,
                lambda name: name.startswith("low.critic")
                or name.startswith("low.value_head")
                or "log_std" in name,
            ),
            _drift_max_matching(
                sham_drift,
                lambda name: name.startswith("low.critic")
                or name.startswith("low.value_head")
                or "log_std" in name,
            ),
            _drift_max_matching(
                source_drift,
                lambda name: name.startswith("low.critic")
                or name.startswith("low.value_head")
                or "log_std" in name,
            ),
        )
        <= THRESHOLDS["other_parameter_max_abs_drift"],
        "natural_episode_counts": all(
            natural["episode_count"] == NATURAL_EPISODES
            for natural in (source_natural, real_natural, sham_natural)
        ),
        "no_forbidden_updates_or_objective_reads": no_forbidden_updates,
    }
    m0 = all(m0_checks.values())
    degenerate_sham = label_agreement > THRESHOLDS["max_hamming_label_agreement_max"]
    m1 = bool(
        real_metrics["fidelity"] >= THRESHOLDS["forced_fidelity_real_min"]
        and np.all(
            np.asarray(real_metrics["fidelity_per_skill"])
            >= THRESHOLDS["forced_fidelity_per_skill_real_min"]
        )
        and fidelity_gain_sham
        >= THRESHOLDS["forced_fidelity_real_minus_sham_min"]
        and fidelity_gain_source
        >= THRESHOLDS["forced_fidelity_real_minus_source_min"]
        and fidelity_real_sham_ci[0]
        > THRESHOLDS["forced_fidelity_gain_ci_lower"]
        and fidelity_real_source_ci[0]
        > THRESHOLDS["forced_fidelity_gain_ci_lower"]
        and real_metrics["median_ratio"]
        >= THRESHOLDS["forced_snr_real_median_min"]
        and snr_real_ci[0] > THRESHOLDS["forced_snr_real_ci_lower"]
        and snr_gain_sham
        >= THRESHOLDS["forced_snr_real_minus_sham_median_min"]
        and snr_gain_source
        >= THRESHOLDS["forced_snr_real_minus_source_median_min"]
        and snr_real_sham_ci[0] > THRESHOLDS["forced_snr_gain_ci_lower"]
        and snr_real_source_ci[0] > THRESHOLDS["forced_snr_gain_ci_lower"]
    )
    m2a = bool(
        real_natural["consistency_mean"]
        >= THRESHOLDS["natural_consistency_real_min"]
        and consistency_gain_sham
        >= THRESHOLDS["natural_consistency_real_minus_sham_min"]
        and consistency_gain_source
        >= THRESHOLDS["natural_consistency_real_minus_source_min"]
        and consistency_real_sham_ci[0]
        > THRESHOLDS["natural_consistency_gain_ci_lower"]
        and consistency_real_source_ci[0]
        > THRESHOLDS["natural_consistency_gain_ci_lower"]
    )
    m2b = bool(
        coverage_ratio_sham
        >= THRESHOLDS["natural_coverage_real_over_sham_min"]
        and coverage_ratio_source
        >= THRESHOLDS["natural_coverage_real_over_source_min"]
        and coverage_real_sham_ci[0]
        > THRESHOLDS["natural_coverage_gain_ci_lower"]
        and coverage_real_source_ci[0]
        > THRESHOLDS["natural_coverage_gain_ci_lower"]
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
    status, next_action = _gate_decision(
        m0=m0,
        degenerate_sham=degenerate_sham,
        m1=m1,
        m2a=m2a,
        m2b=m2b,
        m3=m3,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "experiment": "R34 balanced hindsight mode-distillation gate",
        "status": status,
        "authorized_next_action": next_action,
        "scope": "single three-arm Alice-Bob mechanism seed; no task-efficacy claim",
        "seed": int(args.seed),
        "source": {
            "checkpoint": str(checkpoint),
            "checkpoint_total_steps": int(source_total_steps),
            "checkpoint_update": int(source_update),
            "high_controller": metadata.get("high_controller"),
            "environment": "alice_bob_asymmetric_cycles",
            "source_full_episode_replay_max_error": source_replay_error,
            "external_reward": "runtime_diagnostic_only_never_enters_distillation_or_gate",
            "initial_parameter_max_abs": {
                "source_real": initial_source_real,
                "source_sham": initial_source_sham,
                "real_sham": initial_real_sham,
            },
        },
        "contract": {
            "source_natural_episodes": SOURCE_EPISODES,
            "source_natural_steps": SOURCE_EPISODES * EPISODE_STEPS,
            "train_episodes": TRAIN_SOURCE_EPISODES,
            "heldout_episodes": HELDOUT_SOURCE_EPISODES,
            "train_descriptor_rows": TRAIN_DESCRIPTOR_ROWS,
            "heldout_descriptor_rows": HELDOUT_DESCRIPTOR_ROWS,
            "descriptor_schema": DESCRIPTOR_SCHEMA,
            "descriptor_standardization": "train_only_population_mean_std; epsilon=1e-8 for zero-std handling and SNR denominator",
            "modes": N_SKILLS,
            "rows_per_mode": ROWS_PER_MODE,
            "distillation_epochs": DISTILL_EPOCHS,
            "full_episode_sequence_batch_size": SEQUENCES_PER_BATCH,
            "optimizer_calls_per_trained_arm": OPTIMIZER_CALLS,
            "distillation_lr": DISTILL_LR,
            "gradient_clip": GRAD_CLIP,
            "updated_parameters": "low.actor_film + low.actor_rnn + low.actor_act.action_out.fc_mean",
            "heldout_forced_branches_per_arm": exact_forced_branches,
            "heldout_forced_steps_per_arm": exact_forced_branches * WINDOW,
            "natural_episodes_per_arm": NATURAL_EPISODES,
            "natural_steps_per_arm": NATURAL_EPISODES * EPISODE_STEPS,
            "total_environment_steps": (
                SOURCE_EPISODES * EPISODE_STEPS
                + 3 * exact_forced_branches * WINDOW
                + 3 * NATURAL_EPISODES * EPISODE_STEPS
            ),
            "bootstrap_repetitions": int(args.bootstrap_repetitions),
            "bootstrap_seed": 40_034_031,
            "device": str(device),
            "task_reward_objective_reads": 0,
            "result_artifacts": 1,
        },
        "thresholds": THRESHOLDS,
        "gates": {"M0": m0, "M1": m1, "M2a": m2a, "M2b": m2b, "M3": m3},
        "M0_implementation": {
            "checks": m0_checks,
            "descriptor_scaler": _result_fields(scaler),
            "prototype_fit": _result_fields(prototype_fit),
            "alignment": _result_fields(alignment),
            "max_hamming_sham": _result_fields(sham_result),
            "max_hamming_label_agreement": label_agreement,
            "degenerate_label_sequence": degenerate_sham,
            "real_training": real_train,
            "sham_training": sham_train,
            "parameter_drift": {
                "frozen_source": source_drift,
                "real_modes": real_drift,
                "max_hamming_episode_sequence_sham": sham_drift,
            },
            "forced_evaluation_counts": {
                arm["arm"]: {
                    name: arm[name]
                    for name in (
                        "branch_count",
                        "primitive_steps",
                        "branch_length",
                        "within_replica_skill_crn",
                        "replicas_independent",
                        "unique_context_agent_replica_streams",
                    )
                }
                for arm in (source_forced, real_forced, sham_forced)
            },
        },
        "M1_causal_mode_reproduction": {
            "fidelity_real_minus_sham": fidelity_gain_sham,
            "fidelity_real_minus_sham_ci95": fidelity_real_sham_ci,
            "fidelity_real_minus_source": fidelity_gain_source,
            "fidelity_real_minus_source_ci95": fidelity_real_source_ci,
            "real_snr_ci95": snr_real_ci,
            "snr_real_minus_sham_median": snr_gain_sham,
            "snr_real_minus_sham_ci95": snr_real_sham_ci,
            "snr_real_minus_source_median": snr_gain_source,
            "snr_real_minus_source_ci95": snr_real_source_ci,
            "frozen_source": _forced_metric_summary(source_metrics),
            "real_modes": _forced_metric_summary(real_metrics),
            "max_hamming_episode_sequence_sham": _forced_metric_summary(sham_metrics),
        },
        "M2a_natural_mode_use": {
            "consistency_real_minus_sham": consistency_gain_sham,
            "consistency_real_minus_sham_ci95": consistency_real_sham_ci,
            "consistency_real_minus_source": consistency_gain_source,
            "consistency_real_minus_source_ci95": consistency_real_source_ci,
            "frozen_source": source_natural["consistency_mean"],
            "real_modes": real_natural["consistency_mean"],
            "max_hamming_episode_sequence_sham": sham_natural["consistency_mean"],
        },
        "M2b_exploration_transport": {
            "coverage_real_over_sham": coverage_ratio_sham,
            "coverage_real_minus_sham_ci95": coverage_real_sham_ci,
            "coverage_real_over_source": coverage_ratio_source,
            "coverage_real_minus_source_ci95": coverage_real_source_ci,
            "frozen_source": _natural_summary(source_natural),
            "real_modes": _natural_summary(real_natural),
            "max_hamming_episode_sequence_sham": _natural_summary(sham_natural),
        },
        "M3_r30_safety": {
            "real_full_sync_set_rate": real_natural["full_sync_set_rate"],
            "real_set_skill_entropy_norm": real_natural["set_skill_entropy_norm"],
            "real_set_skill_share_min": real_natural["set_skill_share_min"],
            "real_lifetime_min_share": real_natural["lifetime_min_share"],
        },
        "diagnostic_only": {
            "cluster_old_skill_agreement": alignment.agreement,
            "cluster_old_skill_normalized_mutual_information": old_skill_nmi,
            "cluster_old_skill_overlap": alignment.overlap,
            "source_task": source_natural["task_diagnostics_only"],
            "real_task": real_natural["task_diagnostics_only"],
            "sham_task": sham_natural["task_diagnostics_only"],
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
        description="Run the three-arm R34 balanced hindsight mode-distillation gate."
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=34031)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap_repetitions", type=int, default=10_000)
    args = parser.parse_args()
    if int(args.seed) != 34031:
        parser.error("R34 contract fixes --seed at 34031")
    if int(args.bootstrap_repetitions) != 10_000:
        parser.error("R34 contract fixes --bootstrap_repetitions at 10000")
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
    print(f"[R34] phase=complete status={result['status']} output={output}", flush=True)


if __name__ == "__main__":
    main()
