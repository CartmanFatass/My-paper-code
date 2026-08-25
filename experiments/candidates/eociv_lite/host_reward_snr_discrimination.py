"""EOCIV-B5 matched host-reward gradient-SNR discrimination experiment.

The only treatment is the critical hidden-shock sampler used to form each
four-complete-episode optimizer update.  Both conditions otherwise drive the
unchanged real sibling environment, receipt-validated segment latch, GAE
actor/critic and Adam optimizer.  Evaluation always uses the registered
natural shock prior.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import torch
from torch import nn

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate
from experiments.candidates.eociv_lite import payload_content_learnability as b2
from experiments.candidates.eociv_lite import real_valve_learning as b1
from experiments.candidates.eociv_lite import recurrent_retention_learnability as b4
from experiments.candidates.eociv_lite import sibling_env as sib


TREATMENT = "EOCIV-B5-HOST-REWARD-SNR-DISCRIMINATION"
CONDITIONS = ("IID_SHOCK_BLOCK", "BALANCED_SHOCK_BLOCK")
CHECKPOINTS = ("INIT", "MID", "FINAL")
ACTOR_SEEDS = (87031, 87032, 87033)
PROFILES = b1.PROFILES
EVALUATION_ARMS = b2.EVALUATION_ARMS
CRITICAL_TUPLES = (
    (sib.SHOCK_A, sib.SHOCK_A),
    (sib.SHOCK_A, sib.SHOCK_B),
    (sib.SHOCK_B, sib.SHOCK_A),
    (sib.SHOCK_B, sib.SHOCK_B),
)
BLOCK_SIZE = 4
GAE_LAMBDA = 0.95
NORMALIZATION_EPSILON = 1e-8
IID_TAPE_SEED = 870_500


@dataclass(frozen=True)
class ExperimentPlan:
    mode: str
    conditions: tuple[str, ...]
    actor_seeds: tuple[int, ...]
    profiles: tuple[roster_env.RosterProfile, ...]
    blocks_per_profile: int
    mid_update: int
    evaluation_roots_per_checkpoint_profile: int

    @property
    def updates_per_condition_seed(self) -> int:
        return len(self.profiles) * self.blocks_per_profile

    @property
    def training_episodes(self) -> int:
        return (
            len(self.conditions)
            * len(self.actor_seeds)
            * self.updates_per_condition_seed
            * BLOCK_SIZE
        )

    @property
    def optimizer_updates(self) -> int:
        return len(self.conditions) * len(self.actor_seeds) * self.updates_per_condition_seed

    @property
    def training_transitions(self) -> int:
        return self.training_episodes * roster_env.HORIZON

    @property
    def evaluation_episodes(self) -> int:
        return (
            len(self.conditions)
            * len(self.actor_seeds)
            * len(CHECKPOINTS)
            * len(self.profiles)
            * self.evaluation_roots_per_checkpoint_profile
            * len(EVALUATION_ARMS)
        )

    @property
    def evaluation_transitions(self) -> int:
        return self.evaluation_episodes * roster_env.HORIZON

    @property
    def maximum_transitions(self) -> int:
        return self.training_transitions + self.evaluation_transitions


FULL_PLAN = ExperimentPlan("full", CONDITIONS, ACTOR_SEEDS, PROFILES, 8, 12, 4)
SMOKE_PLAN = ExperimentPlan("smoke", CONDITIONS, ACTOR_SEEDS[:1], PROFILES, 1, 2, 1)


def plan_for_mode(mode: str) -> ExperimentPlan:
    if mode == "smoke":
        return SMOKE_PLAN
    if mode == "full":
        return FULL_PLAN
    raise ValueError("mode must be 'smoke' or 'full'")


def episode_id(stage: str, actor_index: int, profile_index: int, root: int) -> int:
    bases = {"train": 14_000_000, "INIT": 15_000_000, "MID": 16_000_000, "FINAL": 17_000_000}
    if stage not in bases or min(actor_index, profile_index, root) < 0:
        raise ValueError("unregistered B5 episode-id coordinate")
    # Condition and block position are deliberately absent.  The four block
    # episodes and both estimators therefore clone one public world and tape.
    return bases[stage] + actor_index * 100_000 + profile_index * 10_000 + root


def _snapshot(actor: b1.RecurrentActorCritic) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in actor.state_dict().items()}


def _actor_from_snapshot(seed: int, state: Mapping[str, torch.Tensor]) -> b1.RecurrentActorCritic:
    actor = b1.RecurrentActorCritic(PROFILES[0].member_capacity, seed, encoder_kind="content_separating")
    actor.load_state_dict(state, strict=True)
    actor.set_capture(False)
    for parameter in actor.parameters():
        parameter.requires_grad_(False)
    return actor


def _make_env(
    profile: roster_env.RosterProfile,
    registered_id: int,
    shock_tuple: tuple[str, str] | None = None,
) -> sib.EocivSiblingRosterEnv:
    world_seed = sib.profile_stream_identity(sib.BASE_WORLD_STREAM, b1.MASTER_SEED, profile.name)
    ledger = roster_env.make_ledger(registered_id, master_seed=world_seed, profile=profile)
    shocks = None if shock_tuple is None else (shock_tuple[0], sib.SHOCK_NONE, shock_tuple[1])
    return sib.EocivSiblingRosterEnv(ledger, sibling_seed=b1.SIBLING_SEED, shock_states=shocks)


def _digest_parts(parts: Sequence[bytes]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(len(part).to_bytes(8, "little"))
        digest.update(part)
    return digest.hexdigest()


def public_world_digest(env: sib.EocivSiblingRosterEnv) -> str:
    """Digest every public ledger fact while intentionally excluding shocks."""
    ledger = env.ledger
    scalar = json.dumps(
        {
            "episode_id": ledger.episode_id,
            "profile": asdict(ledger.profile),
            "initial_keys": ledger.initial_keys,
            "temporarily_absent": ledger.temporarily_absent,
            "fresh_join": ledger.fresh_join,
            "terminal_leave": ledger.terminal_leave,
            "expected_roster_sizes": ledger.expected_roster_sizes,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    arrays = (
        ledger.capabilities,
        ledger.load,
        ledger.target_mix,
        ledger.presentation_priority,
    )
    return _digest_parts([scalar, *(np.ascontiguousarray(row).tobytes() for row in arrays)])


def action_noise_digest(runner: b4.RetentionEpisodeRunner) -> str:
    return b2._array_digest(runner.noise)


def lifecycle_digest(runner: b4.RetentionEpisodeRunner) -> str:
    material = [
        (
            asdict(record.receipt.opportunity_identity),
            record.receipt.physical_tick,
            record.actuation_route,
        )
        for record in runner.boundary_records
    ]
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def iid_critical_tuple(
    actor_seed: int, profile_name: str, block_root: int, block_position: int
) -> tuple[str, str]:
    """Frozen candidate-local IID tape; depends on no outcome or condition."""
    if block_position not in range(BLOCK_SIZE) or block_root < 0:
        raise ValueError("unregistered B5 block coordinate")
    states: list[str] = []
    for critical_index in range(2):
        material = (
            f"{IID_TAPE_SEED}|{actor_seed}|{profile_name}|{block_root}|"
            f"{block_position}|{critical_index}"
        ).encode("ascii")
        states.append(sib.SHOCK_A if hashlib.sha256(material).digest()[0] < 128 else sib.SHOCK_B)
    return states[0], states[1]


def shock_tuples_for_block(
    condition: str, actor_seed: int, profile_name: str, block_root: int
) -> tuple[tuple[str, str], ...]:
    if condition == "BALANCED_SHOCK_BLOCK":
        return CRITICAL_TUPLES
    if condition == "IID_SHOCK_BLOCK":
        return tuple(
            iid_critical_tuple(actor_seed, profile_name, block_root, position)
            for position in range(BLOCK_SIZE)
        )
    raise ValueError(f"unknown B5 condition: {condition}")


def _episode_loss_tensors(
    actor: b1.RecurrentActorCritic, rewards: Sequence[float]
) -> tuple[torch.Tensor, torch.Tensor, dict[str, float]]:
    """Exact tensor form of B4's episode-local normalized terminal GAE."""
    if len(rewards) != roster_env.HORIZON or len(actor._log_probs) != roster_env.HORIZON:
        raise RuntimeError("B5 actor capture does not match one complete episode")
    reward_tensor = torch.as_tensor(tuple(float(value) for value in rewards), dtype=torch.float32)
    values = torch.stack(actor._values)
    log_probs = torch.stack(actor._log_probs)
    detached_values = values.detach()
    next_values = torch.cat((detached_values[1:], torch.zeros_like(detached_values[-1:])))
    deltas = reward_tensor + b1.GAMMA * next_values - detached_values
    raw_advantages = torch.empty_like(deltas)
    carry = torch.zeros((), dtype=deltas.dtype)
    for index in range(len(deltas) - 1, -1, -1):
        carry = deltas[index] + b1.GAMMA * GAE_LAMBDA * carry
        raw_advantages[index] = carry
    advantage_std = raw_advantages.std(unbiased=False)
    normalized = (raw_advantages - raw_advantages.mean()) / torch.clamp(
        advantage_std, min=NORMALIZATION_EPSILON
    )
    target = (raw_advantages + values).detach()
    error = target - values
    actor_loss = -(log_probs * normalized.detach()).mean()
    critic_loss = torch.square(error).mean()
    diagnostics = {
        "actor_loss": float(actor_loss.detach()),
        "critic_loss": float(critic_loss.detach()),
        "value_target_mean": float(target.mean()),
        "value_target_population_std": float(target.std(unbiased=False)),
        "value_target_error": float(torch.abs(error).mean().detach()),
        "raw_advantage_mean": float(raw_advantages.mean()),
        "raw_advantage_population_std": float(advantage_std),
        "normalized_advantage_mean": float(normalized.mean()),
        "normalized_advantage_population_std": float(normalized.std(unbiased=False)),
    }
    return actor_loss, critic_loss, diagnostics


def gradient_moments_from_vectors(vectors: Sequence[torch.Tensor]) -> dict[str, object]:
    if len(vectors) != BLOCK_SIZE:
        raise ValueError("B5 gradient moments require exactly four contributions")
    total = torch.zeros_like(vectors[0], dtype=torch.float64)
    norm_sum = 0.0
    norms: list[float] = []
    for vector in vectors:
        value = vector.detach().to(dtype=torch.float64)
        total += value
        squared = float(torch.sum(value * value))
        norm_sum += squared
        norms.append(float(np.sqrt(squared)))
    mean = total / BLOCK_SIZE
    signal_sq = float(torch.sum(mean * mean))
    noise_sq = max(norm_sum / BLOCK_SIZE - signal_sq, 0.0)
    return {
        "signal_sq": signal_sq,
        "noise_sq": noise_sq,
        "snr": signal_sq / max(noise_sq, 1e-12),
        "episode_contribution_norms": norms,
        "degenerate_noise": noise_sq <= 1e-12,
    }


def _gradient_moments(
    losses: Sequence[torch.Tensor], parameters: Sequence[nn.Parameter]
) -> dict[str, object]:
    if len(losses) != BLOCK_SIZE:
        raise ValueError("B5 gradient moments require four episode losses")
    sums = [torch.zeros_like(parameter, memory_format=torch.preserve_format) for parameter in parameters]
    squared_norm_sum = 0.0
    episode_norms: list[float] = []
    for loss in losses:
        gradients = torch.autograd.grad(loss, parameters, retain_graph=True, allow_unused=True)
        episode_sq = 0.0
        for index, gradient in enumerate(gradients):
            if gradient is None:
                continue
            detached = gradient.detach()
            sums[index].add_(detached)
            episode_sq += float(torch.sum(detached.double() * detached.double()))
        squared_norm_sum += episode_sq
        episode_norms.append(float(np.sqrt(episode_sq)))
    signal_sq = sum(float(torch.sum((value.double() / BLOCK_SIZE) ** 2)) for value in sums)
    noise_sq = max(squared_norm_sum / BLOCK_SIZE - signal_sq, 0.0)
    result = {
        "signal_sq": signal_sq,
        "noise_sq": noise_sq,
        "snr": signal_sq / max(noise_sq, 1e-12),
        "episode_contribution_norms": episode_norms,
        "degenerate_noise": noise_sq <= 1e-12,
    }
    if not all(np.isfinite(float(result[key])) for key in ("signal_sq", "noise_sq", "snr")):
        raise RuntimeError("nonfinite B5 gradient moment")
    return result


def _make_runner(
    actor: b1.RecurrentActorCritic,
    profile: roster_env.RosterProfile,
    registered_id: int,
    body_fn,
    shock_tuple: tuple[str, str] | None = None,
) -> b4.RetentionEpisodeRunner:
    env = _make_env(profile, registered_id, shock_tuple)
    policy = b4.RetentionPolicy(actor, "SEGMENT_LATCH_RNN")
    runner = b4.RetentionEpisodeRunner(
        env,
        "LR",
        tape_seed=b1.TAPE_SEED,
        d_learned_fn=lambda _: True,
        body_fn=body_fn,
        policy=policy,
    )
    runner.run_episode()
    return runner


def _train_block(
    actor: b1.RecurrentActorCritic,
    optimizer: torch.optim.Optimizer,
    condition: str,
    actor_seed: int,
    profile: roster_env.RosterProfile,
    registered_id: int,
    block_root: int,
) -> dict[str, object]:
    tuples = shock_tuples_for_block(condition, actor_seed, profile.name, block_root)
    parameters = tuple(actor.parameters())
    actor_losses: list[torch.Tensor] = []
    critic_losses: list[torch.Tensor] = []
    episodes: list[dict[str, object]] = []
    public_digests: list[str] = []
    lifecycle_digests: list[str] = []
    noise_digests: list[str] = []
    actor.set_capture(True)
    optimizer.zero_grad(set_to_none=True)
    for position, shock_tuple in enumerate(tuples):
        runner = _make_runner(actor, profile, registered_id, b2._correct_body, shock_tuple)
        actor_loss, critic_loss, diagnostics = _episode_loss_tensors(actor, runner.env.reward_trace)
        actor_losses.append(actor_loss)
        critic_losses.append(critic_loss)
        public_digests.append(public_world_digest(runner.env))
        lifecycle_digests.append(lifecycle_digest(runner))
        noise_digests.append(action_noise_digest(runner))
        episodes.append(
            {
                "block_position": position,
                "critical_shock_tuple": list(shock_tuple),
                "full_shock_tuple": [shock_tuple[0], sib.SHOCK_NONE, shock_tuple[1]],
                "episode_id": registered_id,
                "return": float(sum(runner.env.reward_trace)),
                "accepted_boundary_ticks": list(runner.accepted_boundary_ticks),
                "latch_started_zero": runner.policy.started_zero,
                "latch_ended_zero": runner.policy.ended_zero,
                **diagnostics,
            }
        )
    if any(parameter.grad is not None for parameter in parameters):
        raise RuntimeError("B5 episode collection mutated optimizer gradients")
    actor_moments = _gradient_moments(actor_losses, parameters)
    critic_moments = _gradient_moments([0.5 * loss for loss in critic_losses], parameters)
    if any(parameter.grad is not None for parameter in parameters):
        raise RuntimeError("B5 diagnostic autograd mutated optimizer gradients")
    for episode, actor_norm, critic_norm in zip(
        episodes,
        actor_moments["episode_contribution_norms"],
        critic_moments["episode_contribution_norms"],
    ):
        episode["actor_gradient_contribution_norm"] = actor_norm
        episode["critic_gradient_contribution_norm"] = critic_norm
    actor_mean = torch.stack(actor_losses).mean()
    critic_mean = torch.stack(critic_losses).mean()
    total_loss = actor_mean + 0.5 * critic_mean
    optimizer.zero_grad(set_to_none=True)
    total_loss.backward()
    pre_clip = float(nn.utils.clip_grad_norm_(parameters, b1.GRAD_NORM_CAP))
    if not np.isfinite(pre_clip):
        raise RuntimeError("nonfinite B5 block gradient norm")
    optimizer.step()
    actor.set_capture(False)
    matching = {
        "same_public_world_within_block": len(set(public_digests)) == 1,
        "same_lifecycle_within_block": len(set(lifecycle_digests)) == 1,
        "same_action_noise_tape_within_block": len(set(noise_digests)) == 1,
        "exact_four_complete_episodes": len(episodes) == BLOCK_SIZE
        and all(row["accepted_boundary_ticks"] == list(sib.EVENT_TIMES) for row in episodes),
        "latch_zero_at_episode_boundaries": all(
            row["latch_started_zero"] and row["latch_ended_zero"] for row in episodes
        ),
        "registered_shock_tuple_rule": tuple(tuple(row["critical_shock_tuple"]) for row in episodes)
        == tuples,
    }
    if not all(matching.values()):
        raise RuntimeError(f"B5 training block matching failed: {matching}")
    finite_fields = [
        float(total_loss.detach()),
        float(actor_mean.detach()),
        float(critic_mean.detach()),
        pre_clip,
        *[float(row[key]) for row in episodes for key in (
            "return", "actor_loss", "critic_loss", "value_target_mean",
            "value_target_population_std", "value_target_error",
            "raw_advantage_mean", "raw_advantage_population_std",
            "normalized_advantage_mean", "normalized_advantage_population_std",
        )],
    ]
    nonfinite = not np.isfinite(np.asarray(finite_fields, dtype=np.float64)).all()
    if nonfinite:
        raise RuntimeError("nonfinite B5 training diagnostic")
    return {
        "condition": condition,
        "profile": profile.name,
        "block_root": block_root,
        "episode_id": registered_id,
        "public_world_digest": public_digests[0],
        "lifecycle_digest": lifecycle_digests[0],
        "action_noise_tape_digest": noise_digests[0],
        "shock_tuples": [list(value) for value in tuples],
        "matching": matching,
        "episodes": episodes,
        "actor_gradient_moments": actor_moments,
        "critic_gradient_moments": critic_moments,
        "block_actor_loss": float(actor_mean.detach()),
        "block_critic_loss": float(critic_mean.detach()),
        "block_total_loss": float(total_loss.detach()),
        "total_grad_norm_before_clip": pre_clip,
        "grad_clip_exceeded": pre_clip > b1.GRAD_NORM_CAP,
        "nonfinite": nonfinite,
        "degenerate_actor_noise": bool(actor_moments["degenerate_noise"]),
        "degenerate_critic_noise": bool(critic_moments["degenerate_noise"]),
        "optimizer_steps": 1,
        "clip_calls": 1,
    }


def _train_actor(
    actor: b1.RecurrentActorCritic,
    condition: str,
    actor_seed: int,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[list[dict[str, object]], dict[str, dict[str, torch.Tensor]]]:
    optimizer = torch.optim.Adam(actor.parameters(), lr=b1.ACTOR_LR)
    checkpoints = {"INIT": _snapshot(actor)}
    blocks: list[dict[str, object]] = []
    for root in range(plan.blocks_per_profile):
        for profile_index, profile in enumerate(plan.profiles):
            registered_id = episode_id("train", actor_index, profile_index, root)
            row = _train_block(
                actor, optimizer, condition, actor_seed, profile, registered_id, root
            )
            row["update"] = len(blocks) + 1
            row["order_index"] = len(blocks)
            blocks.append(row)
            counts["environment_transitions"] += BLOCK_SIZE * roster_env.HORIZON
            counts["policy_calls"] += BLOCK_SIZE * roster_env.HORIZON
            counts["learner_episodes"] += BLOCK_SIZE
            counts["trainer_blocks"] += 1
            counts["optimizer_updates"] += 1
            counts["clip_calls"] += 1
            if len(blocks) == plan.mid_update:
                checkpoints["MID"] = _snapshot(actor)
    checkpoints["FINAL"] = _snapshot(actor)
    if len(blocks) != plan.updates_per_condition_seed or set(checkpoints) != set(CHECKPOINTS):
        raise RuntimeError("B5 checkpoint/update schedule drifted")
    return blocks, checkpoints


def _evaluate_checkpoint(
    actor: b1.RecurrentActorCritic,
    condition: str,
    checkpoint: str,
    actor_seed: int,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    lag_rows: list[dict[str, object]] = []
    for root in range(plan.evaluation_roots_per_checkpoint_profile):
        for profile_index, profile in enumerate(plan.profiles):
            registered_id = episode_id(checkpoint, actor_index, profile_index, root)
            runners = {
                arm: _make_runner(actor, profile, registered_id, b2.BODY_RULES[arm])
                for arm in EVALUATION_ARMS
            }
            counts["environment_transitions"] += len(EVALUATION_ARMS) * roster_env.HORIZON
            counts["policy_calls"] += len(EVALUATION_ARMS) * roster_env.HORIZON
            counts["evaluation_episodes"] += len(EVALUATION_ARMS)
            correct = runners["CORRECT"]
            matching = {
                "natural_prior_no_forced_shock": all(
                    runner.env._shock_states == correct.env._shock_states for runner in runners.values()
                ),
                "same_public_world": len({public_world_digest(runner.env) for runner in runners.values()}) == 1,
                "same_lifecycle": len({lifecycle_digest(runner) for runner in runners.values()}) == 1,
                "same_action_noise_tape": len({action_noise_digest(runner) for runner in runners.values()}) == 1,
                "same_initial_hidden_zero_latch": all(runner.policy.started_zero for runner in runners.values()),
                "all_latches_zero_at_end": all(runner.policy.ended_zero for runner in runners.values()),
                "real_route_and_receipts": all(
                    len(runner.boundary_records) == len(sib.EVENT_TIMES)
                    and {record.actuation_route for record in runner.boundary_records} == {"REAL"}
                    for runner in runners.values()
                ),
            }
            if not all(matching.values()):
                raise RuntimeError(f"B5 evaluation matching failed: {matching}")
            arms = {arm: b4._arm_record(runner) for arm, runner in runners.items()}
            row = {
                "condition": condition,
                "checkpoint": checkpoint,
                "actor_seed": actor_seed,
                "profile": profile.name,
                "root": root,
                "episode_id": registered_id,
                "natural_shock_tuple": list(correct.env._shock_states),
                "public_world_digest": public_world_digest(correct.env),
                "action_noise_tape_digest": action_noise_digest(correct),
                "lifecycle_digest": lifecycle_digest(correct),
                "matching": matching,
                "arms": arms,
                "correct_minus_swapped": float(arms["CORRECT"]["episode_return"])
                - float(arms["SWAPPED"]["episode_return"]),
                "correct_minus_native_neutral": float(arms["CORRECT"]["episode_return"])
                - float(arms["NATIVE_NEUTRAL"]["episode_return"]),
            }
            rows.append(row)
            lag_rows.extend(
                b4._paired_lag_rows(condition, checkpoint, actor_seed, profile.name, root, arms)
            )
    return rows, lag_rows


def _summary(values: Sequence[float]) -> dict[str, object]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0 or not np.isfinite(array).all():
        raise RuntimeError("B5 summary requires finite nonempty input")
    return {
        "values": [float(value) for value in values],
        "count": int(array.size),
        "mean": float(array.mean()),
        "population_std": float(array.std(ddof=0)),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def _evaluation_summaries(
    rows: Sequence[Mapping[str, object]], plan: ExperimentPlan
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    summaries: list[dict[str, object]] = []
    changes: dict[tuple[str, int, str], dict[str, float]] = {}
    for condition in plan.conditions:
        for actor_seed in plan.actor_seeds:
            for profile in plan.profiles:
                means: dict[str, dict[str, float]] = {}
                for checkpoint in CHECKPOINTS:
                    selected = [row for row in rows if row["condition"] == condition and row["actor_seed"] == actor_seed and row["profile"] == profile.name and row["checkpoint"] == checkpoint]
                    swapped = _summary([float(row["correct_minus_swapped"]) for row in selected])
                    neutral = _summary([float(row["correct_minus_native_neutral"]) for row in selected])
                    means[checkpoint] = {"correct_minus_swapped": float(swapped["mean"]), "correct_minus_native_neutral": float(neutral["mean"])}
                    summaries.append({"condition": condition, "actor_seed": actor_seed, "profile": profile.name, "checkpoint": checkpoint, "correct_minus_swapped": swapped, "correct_minus_native_neutral": neutral})
                for checkpoint in ("MID", "FINAL"):
                    delta = {key: means[checkpoint][key] - means["INIT"][key] for key in ("correct_minus_swapped", "correct_minus_native_neutral")}
                    summaries.append({"condition": condition, "actor_seed": actor_seed, "profile": profile.name, "checkpoint_change": f"{checkpoint}_MINUS_INIT", **delta})
                    if checkpoint == "FINAL":
                        changes[(condition, actor_seed, profile.name)] = delta
    cells: list[dict[str, object]] = []
    for actor_seed in plan.actor_seeds:
        for profile in plan.profiles:
            iid = changes[("IID_SHOCK_BLOCK", actor_seed, profile.name)]
            balanced = changes[("BALANCED_SHOCK_BLOCK", actor_seed, profile.name)]
            cells.append({
                "actor_seed": actor_seed,
                "profile": profile.name,
                "correct_minus_swapped": float(balanced["correct_minus_swapped"] - iid["correct_minus_swapped"]),
                "correct_minus_native_neutral": float(balanced["correct_minus_native_neutral"] - iid["correct_minus_native_neutral"]),
            })
    aggregate: dict[str, object] = {}
    for key in ("correct_minus_swapped", "correct_minus_native_neutral"):
        values = [float(row[key]) for row in cells]
        aggregate[key] = {
            "summary": _summary(values),
            "positive_count": sum(value > 0.0 for value in values),
            "zero_count": sum(value == 0.0 for value in values),
            "negative_count": sum(value < 0.0 for value in values),
        }
    return summaries, cells, aggregate


def _snr_summaries(
    actors: Sequence[Mapping[str, object]], plan: ExperimentPlan
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    indexed: dict[tuple[str, int, str], dict[str, object]] = {}
    block_index: dict[tuple[str, int, str, int], Mapping[str, object]] = {}
    for actor_row in actors:
        condition = str(actor_row["condition"])
        seed = int(actor_row["actor_seed"])
        blocks = actor_row["training_blocks"]
        for block in blocks:
            block_index[(condition, seed, str(block["profile"]), int(block["block_root"]))] = block
        for profile in plan.profiles:
            selected = [row for row in blocks if row["profile"] == profile.name]
            item = {
                "condition": condition,
                "actor_seed": seed,
                "profile": profile.name,
                "actor_snr": _summary([float(row["actor_gradient_moments"]["snr"]) for row in selected]),
                "critic_snr": _summary([float(row["critic_gradient_moments"]["snr"]) for row in selected]),
            }
            rows.append(item)
            indexed[(condition, seed, profile.name)] = item
    paired: list[dict[str, object]] = []
    for seed in plan.actor_seeds:
        for profile in plan.profiles:
            iid = indexed[("IID_SHOCK_BLOCK", seed, profile.name)]
            balanced = indexed[("BALANCED_SHOCK_BLOCK", seed, profile.name)]
            actor_differences: list[float] = []
            critic_differences: list[float] = []
            block_rows: list[dict[str, object]] = []
            for root in range(plan.blocks_per_profile):
                iid_block = block_index[("IID_SHOCK_BLOCK", seed, profile.name, root)]
                balanced_block = block_index[("BALANCED_SHOCK_BLOCK", seed, profile.name, root)]
                actor_difference = float(balanced_block["actor_gradient_moments"]["snr"]) - float(iid_block["actor_gradient_moments"]["snr"])
                critic_difference = float(balanced_block["critic_gradient_moments"]["snr"]) - float(iid_block["critic_gradient_moments"]["snr"])
                actor_differences.append(actor_difference)
                critic_differences.append(critic_difference)
                block_rows.append({
                    "block_root": root,
                    "actor_snr_balanced_minus_iid": actor_difference,
                    "critic_snr_balanced_minus_iid": critic_difference,
                })
            paired.append({
                "actor_seed": seed,
                "profile": profile.name,
                "block_differences": block_rows,
                "actor_snr_balanced_minus_iid": _summary(actor_differences),
                "critic_snr_balanced_minus_iid": _summary(critic_differences),
                "difference_of_condition_means": {
                    "actor_snr": float(balanced["actor_snr"]["mean"] - iid["actor_snr"]["mean"]),
                    "critic_snr": float(balanced["critic_snr"]["mean"] - iid["critic_snr"]["mean"]),
                },
            })
    return rows, paired


def _final_late_lag_confirmation(
    rows: Sequence[Mapping[str, object]], plan: ExperimentPlan
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for condition in plan.conditions:
        for seed in plan.actor_seeds:
            for profile in plan.profiles:
                for event_time in b4.CRITICAL_EVENT_TIMES:
                    for contrast in b4.CONTRASTS:
                        selected = [
                            row for row in rows
                            if row["condition"] == condition and row["checkpoint"] == "FINAL"
                            and row["actor_seed"] == seed and row["profile"] == profile.name
                            and row["event_time"] == event_time and row["contrast"] == contrast
                            and 4 <= row["lag"] <= 11
                        ]
                        output.append({
                            "condition": condition,
                            "actor_seed": seed,
                            "profile": profile.name,
                            "event_time": event_time,
                            "contrast": contrast,
                            "lag_range": [4, 11],
                            "absolute_reward_difference": _summary([float(row["absolute_reward_difference"]) for row in selected]),
                            "recurrent_state_l1": _summary([float(row["recurrent_state_l1"]) for row in selected]),
                        })
    return output


def run_experiment(mode: str = "smoke") -> dict[str, object]:
    plan = plan_for_mode(mode)
    if (
        FULL_PLAN.training_transitions != 27_648
        or FULL_PLAN.evaluation_transitions != 31_104
        or FULL_PLAN.maximum_transitions != 58_752
        or FULL_PLAN.training_episodes != 576
        or FULL_PLAN.optimizer_updates != 144
        or FULL_PLAN.evaluation_episodes != 648
    ):
        raise RuntimeError("registered B5 full budget drifted")
    counts = {
        "environment_transitions": 0,
        "policy_calls": 0,
        "learner_episodes": 0,
        "trainer_blocks": 0,
        "optimizer_updates": 0,
        "clip_calls": 0,
        "training_episodes": 0,
        "evaluation_episodes": 0,
    }
    actors: list[dict[str, object]] = []
    evaluations: list[dict[str, object]] = []
    lag_rows: list[dict[str, object]] = []
    initial_digests: dict[tuple[str, int], str] = {}
    training_matching: dict[tuple[str, int, str, int], tuple[str, str, str]] = {}
    evaluation_matching: dict[tuple[str, int, str, int], tuple[object, ...]] = {}
    for condition in plan.conditions:
        for actor_index, actor_seed in enumerate(plan.actor_seeds):
            actor = b1.RecurrentActorCritic(PROFILES[0].member_capacity, actor_seed, encoder_kind="content_separating")
            initial_digests[(condition, actor_seed)] = b2._state_digest(actor)
            training_blocks, checkpoints = _train_actor(actor, condition, actor_seed, actor_index, plan, counts)
            counts["training_episodes"] += len(training_blocks) * BLOCK_SIZE
            for row in training_blocks:
                key = (condition, actor_seed, str(row["profile"]), int(row["block_root"]))
                training_matching[key] = (
                    str(row["public_world_digest"]),
                    str(row["lifecycle_digest"]),
                    str(row["action_noise_tape_digest"]),
                )
            checkpoint_digests: dict[str, str] = {}
            for checkpoint in CHECKPOINTS:
                frozen = _actor_from_snapshot(actor_seed, checkpoints[checkpoint])
                checkpoint_digests[checkpoint] = b2._state_digest(frozen)
                checkpoint_rows, checkpoint_lags = _evaluate_checkpoint(
                    frozen, condition, checkpoint, actor_seed, actor_index, plan, counts
                )
                evaluations.extend(checkpoint_rows)
                lag_rows.extend(checkpoint_lags)
                for row in checkpoint_rows:
                    key = (condition, actor_seed, str(row["checkpoint"]), str(row["profile"]), int(row["root"]))
                    evaluation_matching[key] = (
                        int(row["episode_id"]), tuple(row["natural_shock_tuple"]),
                        str(row["public_world_digest"]), str(row["lifecycle_digest"]),
                        str(row["action_noise_tape_digest"]),
                    )
            actors.append({
                "condition": condition,
                "actor_seed": actor_seed,
                "initial_state_digest": initial_digests[(condition, actor_seed)],
                "checkpoint_state_digests": checkpoint_digests,
                "training_blocks": training_blocks,
            })
    cross_training = all(
        training_matching[("IID_SHOCK_BLOCK", seed, profile.name, root)]
        == training_matching[("BALANCED_SHOCK_BLOCK", seed, profile.name, root)]
        for seed in plan.actor_seeds for profile in plan.profiles for root in range(plan.blocks_per_profile)
    )
    cross_evaluation = all(
        evaluation_matching[("IID_SHOCK_BLOCK", seed, checkpoint, profile.name, root)]
        == evaluation_matching[("BALANCED_SHOCK_BLOCK", seed, checkpoint, profile.name, root)]
        for seed in plan.actor_seeds for checkpoint in CHECKPOINTS for profile in plan.profiles
        for root in range(plan.evaluation_roots_per_checkpoint_profile)
    )
    matching_proof = {
        "same_initial_actor_by_seed": all(
            initial_digests[("IID_SHOCK_BLOCK", seed)] == initial_digests[("BALANCED_SHOCK_BLOCK", seed)]
            for seed in plan.actor_seeds
        ),
        "root_major_profile_interleaved_blocks": all(
            [(row["block_root"], row["profile"]) for row in actor["training_blocks"]]
            == [(root, profile.name) for root in range(plan.blocks_per_profile) for profile in plan.profiles]
            for actor in actors
        ),
        "same_public_world_lifecycle_noise_between_conditions": cross_training,
        "natural_prior_evaluation_coordinates_and_shocks_match_conditions": cross_evaluation,
        "balanced_expected_ordinary_prior_exact": tuple(CRITICAL_TUPLES) == shock_tuples_for_block("BALANCED_SHOCK_BLOCK", 0, PROFILES[0].name, 0),
        "ordinary_external_team_reward_only": True,
        "condition_absent_from_actor_input_and_episode_id": True,
        "same_latched_gae_actor_optimizer": True,
    }
    if not all(matching_proof.values()):
        raise RuntimeError(f"B5 condition matching proof failed: {matching_proof}")
    expected_counts = {
        "environment_transitions": plan.maximum_transitions,
        "policy_calls": plan.maximum_transitions,
        "learner_episodes": plan.training_episodes,
        "trainer_blocks": plan.optimizer_updates,
        "optimizer_updates": plan.optimizer_updates,
        "clip_calls": plan.optimizer_updates,
        "training_episodes": plan.training_episodes,
        "evaluation_episodes": plan.evaluation_episodes,
    }
    if counts != expected_counts:
        raise RuntimeError(f"actual B5 counts drifted: {counts} != {expected_counts}")
    summaries, cells, aggregate_cells = _evaluation_summaries(evaluations, plan)
    snr_summaries, paired_snr = _snr_summaries(actors, plan)
    all_blocks = [row for actor in actors for row in actor["training_blocks"]]
    final_lag_confirmation = _final_late_lag_confirmation(lag_rows, plan)
    expected_shapes = {
        "actors": len(plan.conditions) * len(plan.actor_seeds),
        "training_blocks": plan.optimizer_updates,
        "evaluation_root_rows": plan.evaluation_episodes // len(EVALUATION_ARMS),
        "condition_summary_rows": (
            len(plan.conditions) * len(plan.actor_seeds) * len(plan.profiles) * 5
        ),
        "paired_semantic_cells": len(plan.actor_seeds) * len(plan.profiles),
        "snr_summary_rows": len(plan.conditions) * len(plan.actor_seeds) * len(plan.profiles),
        "paired_snr_rows": len(plan.actor_seeds) * len(plan.profiles),
        "final_lag_confirmation_rows": (
            len(plan.conditions) * len(plan.actor_seeds) * len(plan.profiles)
            * len(b4.CRITICAL_EVENT_TIMES) * len(b4.CONTRASTS)
        ),
    }
    observed_shapes = {
        "actors": len(actors),
        "training_blocks": len(all_blocks),
        "evaluation_root_rows": len(evaluations),
        "condition_summary_rows": len(summaries),
        "paired_semantic_cells": len(cells),
        "snr_summary_rows": len(snr_summaries),
        "paired_snr_rows": len(paired_snr),
        "final_lag_confirmation_rows": len(final_lag_confirmation),
    }
    if observed_shapes != expected_shapes:
        raise RuntimeError(f"B5 artifact shape drifted: {observed_shapes} != {expected_shapes}")
    gradient_summary = {
        "all_finite": all(not row["nonfinite"] for row in all_blocks),
        "grad_clip_exceed_count": sum(bool(row["grad_clip_exceeded"]) for row in all_blocks),
        "grad_clip_exceed_fraction": sum(bool(row["grad_clip_exceeded"]) for row in all_blocks) / len(all_blocks),
        "pre_clip_norm": _summary([float(row["total_grad_norm_before_clip"]) for row in all_blocks]),
        "block_total_loss": _summary([float(row["block_total_loss"]) for row in all_blocks]),
        "critic_loss": _summary([float(row["block_critic_loss"]) for row in all_blocks]),
        "degenerate_actor_noise_count": sum(bool(row["degenerate_actor_noise"]) for row in all_blocks),
        "degenerate_critic_noise_count": sum(bool(row["degenerate_critic_noise"]) for row in all_blocks),
    }
    return {
        "treatment": TREATMENT,
        "stage": "B_EXPLORATORY_REAL_TOY_EXPERIMENT",
        "mode": mode,
        "scientific_disposition": None,
        "registered_c_outcome_experiment_licensed": capability_gate.REGISTERED_OUTCOME_EXPERIMENT["licensed"],
        "real_implementation": True,
        "real_environment_calls": counts["environment_transitions"] > 0,
        "real_policy_calls": counts["policy_calls"] > 0,
        "real_gae_learner_calls": counts["learner_episodes"] > 0,
        "real_block_trainer_calls": counts["trainer_blocks"] > 0,
        "real_optimizer_updates": counts["optimizer_updates"] > 0,
        "real_three_arm_evaluation_calls": counts["evaluation_episodes"] > 0,
        "configuration": {
            "conditions": list(plan.conditions), "actor_seeds": list(plan.actor_seeds),
            "profiles": [profile.name for profile in plan.profiles], "checkpoints": list(CHECKPOINTS),
            "evaluation_arms": list(EVALUATION_ARMS), "horizon": roster_env.HORIZON,
            "block_size": BLOCK_SIZE, "blocks_per_profile": plan.blocks_per_profile,
            "mid_update": plan.mid_update, "final_update": plan.updates_per_condition_seed,
            "evaluation_roots_per_checkpoint_profile": plan.evaluation_roots_per_checkpoint_profile,
            "actor_lr": b1.ACTOR_LR, "gamma": b1.GAMMA, "gae_lambda": GAE_LAMBDA,
            "normalization_epsilon": NORMALIZATION_EPSILON, "grad_norm_cap": b1.GRAD_NORM_CAP,
            "balanced_tuple_order": [list(value) for value in CRITICAL_TUPLES],
            "iid_tape_seed": IID_TAPE_SEED, "training_transitions": plan.training_transitions,
            "evaluation_transitions": plan.evaluation_transitions, "maximum_transitions": plan.maximum_transitions,
            "k_search": 0, "hypothetical_transitions": 0,
        },
        "matching_proof": matching_proof,
        "counts": counts,
        "actors": actors,
        "evaluation_rows": evaluations,
        "condition_summaries": summaries,
        "paired_balanced_minus_iid_final_minus_init_cells": cells,
        "paired_cell_aggregate": aggregate_cells,
        "snr_summaries": snr_summaries,
        "paired_snr_differences": paired_snr,
        "gradient_and_critic_summary": gradient_summary,
        "artifact_shapes": observed_shapes,
        "final_lag_4_to_11_retention_confirmation": final_lag_confirmation,
        "mechanical_status": "MECHANICAL_B5_COMPLETE",
        "interpretation_boundary": (
            "One frozen IID-versus-balanced B5 estimator comparison only. No outcome licenses "
            "a rescue or second B5, favorable-seed selection, reward shaping, valve, auxiliary "
            "loss, model widening, VSP learner comparison, External Pro, or C treatment."
        ),
    }


def write_result(result: Mapping[str, object], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
