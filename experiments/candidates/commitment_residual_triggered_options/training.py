"""Exact finite-budget probe and recurrent PPO training laws for CRTO-B1 v4."""

from __future__ import annotations

import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import torch
from torch.nn import functional as F

from .models import (
    ArmKind,
    DecisionKind,
    DecodabilityProbe,
    OPTION_COUNT,
    PACKET_DIM,
    REVISION,
    RecurrentOptionActorCritic,
    decision_action_index,
    exact_immediate_charge,
    trainable_parameter_count,
)


EPISODE_HORIZON = 256
AGENT_COUNT = 4
TRAIN_EPISODES = 1024
EPISODES_PER_UPDATE = 32
PPO_EPOCHS = 4
MINIBATCH_EPISODES = 8
TRAINING_UPDATES = TRAIN_EPISODES // EPISODES_PER_UPDATE
GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.2
VALUE_COEFFICIENT = 0.5
Q_COEFFICIENT = 0.5
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.5


@dataclass(frozen=True)
class ProbeExample:
    episode_index: int
    commitment_time: int
    target_age: int
    environment_slot: int
    raw_packet: torch.Tensor
    explicit_coordinates: torch.Tensor

    @property
    def canonical_key(self) -> tuple[int, int, int, int]:
        return (
            self.episode_index,
            self.commitment_time,
            self.target_age,
            self.environment_slot,
        )

    def validate(self) -> None:
        if self.raw_packet.device.type != "cpu" or self.explicit_coordinates.device.type != "cpu":
            raise ValueError("registered probe records must be CPU tensors")
        if self.raw_packet.shape != (52,) or self.explicit_coordinates.shape != (24,):
            raise ValueError("probe record must contain one [52] raw and [24] explicit row")
        if not bool(torch.isfinite(self.raw_packet).all()) or not bool(torch.isfinite(self.explicit_coordinates).all()):
            raise ValueError("probe record contains non-finite data")


@dataclass(frozen=True)
class ProbeReport:
    revision: str
    algorithm_seed: int
    fit_examples: int
    development_examples: int
    optimizer_updates: int
    final_fit_mse: float
    normalized_mse: float
    sign_accuracy: float
    passed: bool


def fit_decodability_probe(
    algorithm_seed: int,
    predictor_fit_examples: Sequence[ProbeExample],
    calibration_examples: Sequence[ProbeExample],
    development_examples: Sequence[ProbeExample],
) -> tuple[DecodabilityProbe, ProbeReport]:
    """Fit the final-checkpoint scripted-support probe for exactly 1,000 updates."""

    fit_rows = sorted(
        [*predictor_fit_examples, *calibration_examples], key=lambda row: row.canonical_key
    )
    development_rows = sorted(development_examples, key=lambda row: row.canonical_key)
    if not fit_rows or not development_rows:
        raise ValueError("probe fit and untouched development populations must both be nonempty")
    for row in [*fit_rows, *development_rows]:
        row.validate()
    probe = DecodabilityProbe(algorithm_seed)
    optimizer = torch.optim.Adam(
        probe.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0
    )
    permutation = np.random.Generator(
        np.random.PCG64(600000 + int(algorithm_seed))
    ).permutation(len(fit_rows))
    cursor = 0
    final_loss = math.nan
    probe.train()
    for _update in range(1000):
        positions = (cursor + np.arange(256, dtype=np.int64)) % len(fit_rows)
        indices = permutation[positions]
        cursor = int((cursor + 256) % len(fit_rows))
        raw = torch.stack([fit_rows[int(index)].raw_packet for index in indices])
        target = torch.stack([fit_rows[int(index)].explicit_coordinates for index in indices])
        prediction = probe(raw)
        loss = F.mse_loss(prediction, target, reduction="mean")
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("decodability probe loss became non-finite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(probe.parameters(), max_norm=1.0)
        optimizer.step()
        final_loss = float(loss.detach())

    probe.eval()
    with torch.no_grad():
        fit_target = torch.stack([row.explicit_coordinates for row in fit_rows])
        development_raw = torch.stack([row.raw_packet for row in development_rows])
        development_target = torch.stack([row.explicit_coordinates for row in development_rows])
        development_prediction = probe(development_raw)
        coordinate_mse = (development_prediction - development_target).square().mean(dim=0)
        fit_variance = fit_target.var(dim=0, unbiased=False)
        normalized_mse = float((coordinate_mse / (fit_variance + 1e-8)).mean())
        sign_support = development_target.abs() >= 0.05
        if not bool(sign_support.any()):
            raise RuntimeError("probe development split has no registered sign-support coordinates")
        sign_accuracy = float(
            (torch.sign(development_prediction[sign_support]) == torch.sign(development_target[sign_support]))
            .to(torch.float32)
            .mean()
        )
    for parameter in probe.parameters():
        parameter.requires_grad_(False)
    report = ProbeReport(
        revision=REVISION,
        algorithm_seed=int(algorithm_seed),
        fit_examples=len(fit_rows),
        development_examples=len(development_rows),
        optimizer_updates=1000,
        final_fit_mse=final_loss,
        normalized_mse=normalized_mse,
        sign_accuracy=sign_accuracy,
        passed=normalized_mse <= 0.01 and sign_accuracy >= 0.95,
    )
    return probe, report


@dataclass(frozen=True)
class RecurrentEpisode:
    """One complete on-policy team trajectory at the documented record boundary.

    ``current_options`` is the predecision option.  At INITIAL records, where no
    physical previous option exists, the host stores ``selected_options`` in
    that field as a shape-valid placeholder; INITIAL likelihood and charge laws
    never inspect it.  ``adapter_packets`` must already be the arm-appropriate
    explicit or raw packet from the common frozen predictor.
    """

    episode_index: int
    deployable_observations: torch.Tensor  # [256,4,D]
    centralized_states: torch.Tensor       # [256,C]
    adapter_packets: torch.Tensor          # [256,4,52]
    current_options: torch.Tensor           # [256,4]
    legal_masks: torch.Tensor               # [256,4,7]
    decision_kinds: torch.Tensor            # [256,4], DecisionKind values
    selected_options: torch.Tensor          # [256,4], resulting active option
    replanning_costs: torch.Tensor           # [256,4]
    own_immediate_charges: torch.Tensor      # [256,4]
    rewards: torch.Tensor                    # [256], summed team reward
    dones: torch.Tensor                      # [256], terminal only at final step
    old_joint_log_probabilities: torch.Tensor  # [256], zero when no decision
    old_values: torch.Tensor                 # [256], centralized pre-action value

    def validate(self, model: RecurrentOptionActorCritic) -> None:
        tensors = (
            self.deployable_observations,
            self.centralized_states,
            self.adapter_packets,
            self.current_options,
            self.legal_masks,
            self.decision_kinds,
            self.selected_options,
            self.replanning_costs,
            self.own_immediate_charges,
            self.rewards,
            self.dones,
            self.old_joint_log_probabilities,
            self.old_values,
        )
        if any(tensor.device.type != "cpu" for tensor in tensors):
            raise ValueError("registered recurrent PPO records are CPU-only")
        if self.deployable_observations.shape != (
            EPISODE_HORIZON, AGENT_COUNT, model.observation_dim
        ):
            raise ValueError("deployable observations violate the [256,4,D] contract")
        if self.centralized_states.shape != (EPISODE_HORIZON, model.centralized_state_dim):
            raise ValueError("centralized states violate the [256,C] contract")
        if self.adapter_packets.shape != (EPISODE_HORIZON, AGENT_COUNT, PACKET_DIM):
            raise ValueError("adapter packets violate the [256,4,52] contract")
        pair_shape = (EPISODE_HORIZON, AGENT_COUNT)
        if any(tensor.shape != pair_shape for tensor in (
            self.current_options,
            self.decision_kinds,
            self.selected_options,
            self.replanning_costs,
            self.own_immediate_charges,
        )):
            raise ValueError("agent-time decision record shape mismatch")
        if self.legal_masks.shape != (EPISODE_HORIZON, AGENT_COUNT, OPTION_COUNT):
            raise ValueError("legal masks violate the [256,4,7] contract")
        if any(tensor.shape != (EPISODE_HORIZON,) for tensor in (
            self.rewards,
            self.dones,
            self.old_joint_log_probabilities,
            self.old_values,
        )):
            raise ValueError("primitive team record shape mismatch")
        floating = (
            self.deployable_observations,
            self.centralized_states,
            self.adapter_packets,
            self.replanning_costs,
            self.own_immediate_charges,
            self.rewards,
            self.old_joint_log_probabilities,
            self.old_values,
        )
        if any(not bool(torch.isfinite(tensor).all()) for tensor in floating):
            raise ValueError("trajectory contains non-finite learned-arm data")
        if bool(self.dones[:-1].any()) or not bool(self.dones[-1]):
            raise ValueError("training record must be one complete 256-step episode")
        valid_kinds = (
            (self.decision_kinds == int(DecisionKind.NONE))
            | (self.decision_kinds == int(DecisionKind.INITIAL))
            | (self.decision_kinds == int(DecisionKind.DISCRETIONARY))
            | (self.decision_kinds == int(DecisionKind.FORCED_RENEWAL))
        )
        if not bool(valid_kinds.all()):
            raise ValueError("trajectory contains an unknown decision kind")
        if bool(torch.any((self.current_options < 0) | (self.current_options >= OPTION_COUNT))):
            raise ValueError("current option outside the frozen option order")
        if bool(torch.any((self.selected_options < 0) | (self.selected_options >= OPTION_COUNT))):
            raise ValueError("selected option outside the frozen option order")
        decision_mask = self.decision_kinds != int(DecisionKind.NONE)
        if not bool(self.legal_masks[decision_mask].gather(
            1, self.selected_options[decision_mask].to(torch.int64).unsqueeze(1)
        ).all()):
            raise ValueError("a recorded selected option is illegal")
        if not bool(torch.all(
            (self.replanning_costs == 0.25) | (self.replanning_costs == 4.0)
        )):
            raise ValueError("every record must carry the frozen cost regime")
        for time_index in range(EPISODE_HORIZON):
            for agent_index in range(AGENT_COUNT):
                kind = DecisionKind(int(self.decision_kinds[time_index, agent_index]))
                expected = exact_immediate_charge(
                    kind,
                    int(self.selected_options[time_index, agent_index]),
                    int(self.current_options[time_index, agent_index]),
                    float(self.replanning_costs[time_index, agent_index]),
                )
                observed = float(self.own_immediate_charges[time_index, agent_index])
                if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-6):
                    raise ValueError(
                        f"immediate charge mismatch at t={time_index}, agent={agent_index}: "
                        f"expected {expected}, observed {observed}"
                    )
        no_decision = ~decision_mask.any(dim=1)
        if not bool(torch.all(self.old_joint_log_probabilities[no_decision] == 0)):
            raise ValueError("joint old log probability must be zero when nobody reviews")


@dataclass(frozen=True)
class ForwardEpisode:
    values: torch.Tensor
    joint_log_probabilities: torch.Tensor
    joint_entropies: torch.Tensor
    q_selected: torch.Tensor
    decision_mask: torch.Tensor


@dataclass(frozen=True)
class BatchForwardEpisode:
    values: torch.Tensor                   # [batch,256]
    joint_log_probabilities: torch.Tensor  # [batch,256]
    joint_entropies: torch.Tensor          # [batch,256]
    q_selected: torch.Tensor               # [batch,256,4]
    decision_mask: torch.Tensor             # [batch,256,4]


def _evaluate_recurrent_batch(
    model: RecurrentOptionActorCritic,
    episodes: Sequence[RecurrentEpisode],
) -> BatchForwardEpisode:
    """Vectorize episodes while retaining exact primitive recurrent order."""

    if not episodes:
        raise ValueError("cannot replay an empty episode minibatch")
    batch_size = len(episodes)
    observations = torch.stack([row.deployable_observations for row in episodes])
    centralized = torch.stack([row.centralized_states for row in episodes])
    packets = torch.stack([row.adapter_packets for row in episodes])
    current_options = torch.stack([row.current_options for row in episodes])
    legal_masks = torch.stack([row.legal_masks for row in episodes])
    decision_kinds = torch.stack([row.decision_kinds for row in episodes])
    selected_options = torch.stack([row.selected_options for row in episodes])
    replanning_costs = torch.stack([row.replanning_costs for row in episodes])
    hidden = model.initial_hidden(batch_size * AGENT_COUNT).reshape(batch_size, AGENT_COUNT, -1)
    values: list[torch.Tensor] = []
    joint_log_probabilities: list[torch.Tensor] = []
    joint_entropies: list[torch.Tensor] = []
    q_selected: list[torch.Tensor] = []

    for time_index in range(EPISODE_HORIZON):
        step = model.forward_step(
            observations[:, time_index],
            hidden,
            centralized[:, time_index],
            packets[:, time_index],
        )
        hidden = step.hidden
        q_selected.append(step.q.gather(
            2, selected_options[:, time_index].to(torch.int64).unsqueeze(2)
        ).squeeze(2))
        joint_log_probability = step.value.new_zeros((batch_size,))
        joint_entropy = step.value.new_zeros((batch_size,))
        for kind in (DecisionKind.INITIAL, DecisionKind.DISCRETIONARY, DecisionKind.FORCED_RENEWAL):
            coordinates = torch.nonzero(
                decision_kinds[:, time_index] == int(kind), as_tuple=False
            )
            if coordinates.numel() == 0:
                continue
            batch_coordinates = coordinates[:, 0]
            agent_coordinates = coordinates[:, 1]
            q = step.q[batch_coordinates, agent_coordinates]
            residual = step.residual_contribution[batch_coordinates, agent_coordinates]
            legal = legal_masks[batch_coordinates, time_index, agent_coordinates].to(torch.bool)
            current = current_options[batch_coordinates, time_index, agent_coordinates].to(torch.int64)
            cost = replanning_costs[batch_coordinates, time_index, agent_coordinates]
            if kind is DecisionKind.INITIAL:
                logits = model.initial_logits(q, legal)
            elif kind is DecisionKind.DISCRETIONARY:
                logits = model.discretionary_logits(q, residual, current, legal, cost)
            else:
                logits = model.forced_renewal_logits(q, residual, current, legal, cost)
            action_indices = torch.tensor([
                decision_action_index(
                    kind,
                    int(selected_options[int(batch), time_index, int(agent)]),
                    int(current_options[int(batch), time_index, int(agent)]),
                )
                for batch, agent in coordinates
            ], dtype=torch.int64)
            log_probability, entropy = model.log_probability_and_entropy(logits, action_indices)
            joint_log_probability = joint_log_probability.index_add(
                0, batch_coordinates, log_probability
            )
            joint_entropy = joint_entropy.index_add(0, batch_coordinates, entropy)
        values.append(step.value)
        joint_log_probabilities.append(joint_log_probability)
        joint_entropies.append(joint_entropy)
    return BatchForwardEpisode(
        values=torch.stack(values, dim=1),
        joint_log_probabilities=torch.stack(joint_log_probabilities, dim=1),
        joint_entropies=torch.stack(joint_entropies, dim=1),
        q_selected=torch.stack(q_selected, dim=1),
        decision_mask=decision_kinds != int(DecisionKind.NONE),
    )


def evaluate_recurrent_episode(
    model: RecurrentOptionActorCritic, episode: RecurrentEpisode,
) -> ForwardEpisode:
    """Recompute one retained history and its joint review likelihoods."""

    episode.validate(model)
    batch = _evaluate_recurrent_batch(model, [episode])
    return ForwardEpisode(
        values=batch.values[0],
        joint_log_probabilities=batch.joint_log_probabilities[0],
        joint_entropies=batch.joint_entropies[0],
        q_selected=batch.q_selected[0],
        decision_mask=batch.decision_mask[0],
    )


def primitive_gae(episode: RecurrentEpisode) -> tuple[torch.Tensor, torch.Tensor]:
    """Primitive-time GAE from the summed team reward and frozen old values."""

    advantage = torch.zeros_like(episode.rewards)
    running = episode.rewards.new_zeros(())
    for time_index in range(EPISODE_HORIZON - 1, -1, -1):
        nonterminal = 1.0 - episode.dones[time_index].to(episode.rewards.dtype)
        next_value = (
            episode.old_values[time_index + 1]
            if time_index + 1 < EPISODE_HORIZON
            else episode.old_values.new_zeros(())
        )
        delta = (
            episode.rewards[time_index]
            + GAMMA * next_value * nonterminal
            - episode.old_values[time_index]
        )
        running = delta + GAMMA * GAE_LAMBDA * nonterminal * running
        advantage[time_index] = running
    return advantage, advantage + episode.old_values


def semi_markov_q_targets(episode: RecurrentEpisode) -> tuple[torch.Tensor, torch.Tensor]:
    """Option TD targets with the selected agent's current charge added back once.

    Other agents' simultaneous charges and all charges after the originating
    decision remain in the realized team reward.  The bootstrap is the frozen
    centralized value at that agent's next legal review and is stop-gradient.
    """

    decision_mask = episode.decision_kinds != int(DecisionKind.NONE)
    targets = torch.zeros_like(episode.own_immediate_charges)
    next_review: list[int | None] = [None] * AGENT_COUNT
    with torch.no_grad():
        for time_index in range(EPISODE_HORIZON - 1, -1, -1):
            for agent_index in range(AGENT_COUNT):
                if not bool(decision_mask[time_index, agent_index]):
                    continue
                next_time = next_review[agent_index]
                end_exclusive = EPISODE_HORIZON if next_time is None else next_time
                discounted_return = episode.rewards.new_zeros(())
                discount = 1.0
                for reward_time in range(time_index, end_exclusive):
                    discounted_return = discounted_return + discount * episode.rewards[reward_time]
                    discount *= GAMMA
                if next_time is not None:
                    discounted_return = discounted_return + discount * episode.old_values[next_time]
                targets[time_index, agent_index] = (
                    discounted_return + episode.own_immediate_charges[time_index, agent_index]
                )
            for agent_index in range(AGENT_COUNT):
                if bool(decision_mask[time_index, agent_index]):
                    next_review[agent_index] = time_index
    return targets.detach(), decision_mask


@dataclass(frozen=True)
class PPOUpdateReport:
    revision: str
    arm: str
    algorithm_seed: int
    update: int
    episodes_seen: int
    optimizer_steps: int
    mean_policy_loss: float
    mean_value_loss: float
    mean_q_loss: float
    mean_joint_entropy: float
    mean_gradient_norm: float


class RecurrentPPOTrainer:
    """32-episode updates, four shuffled epochs, and eight-episode minibatches."""

    def __init__(
        self,
        model: RecurrentOptionActorCritic,
        algorithm_seed: int,
        on_first_optimizer_step: Callable[[dict[str, object]], None] | None = None,
    ) -> None:
        if model.algorithm_seed != int(algorithm_seed):
            raise ValueError("model and trainer algorithm seeds differ")
        if next(model.parameters()).device.type != "cpu":
            raise ValueError("registered learned-arm training is CPU-only")
        self.model = model
        self.algorithm_seed = int(algorithm_seed)
        self.optimizer = torch.optim.Adam(
            model.parameters(), lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0
        )
        # Separate trainers for paired arms start identical streams, preserving
        # epoch/minibatch assignment without sharing mutable RNG state.
        self.shuffle_rng = np.random.Generator(np.random.PCG64(950000 + self.algorithm_seed))
        self.on_first_optimizer_step = on_first_optimizer_step
        self.activity_boundary_persisted = False
        self.completed_updates = 0
        self.episodes_seen = 0
        self.optimizer_steps = 0

    def update(self, episodes: Sequence[RecurrentEpisode]) -> PPOUpdateReport:
        if self.completed_updates >= TRAINING_UPDATES:
            raise RuntimeError("registered 1,024-episode training budget is already complete")
        if len(episodes) != EPISODES_PER_UPDATE:
            raise ValueError("each PPO update requires exactly 32 complete episodes")
        if len({episode.episode_index for episode in episodes}) != EPISODES_PER_UPDATE:
            raise ValueError("PPO update contains duplicate episode indices")
        for episode in episodes:
            episode.validate(self.model)

        raw_advantages: list[torch.Tensor] = []
        returns: list[torch.Tensor] = []
        q_targets: list[torch.Tensor] = []
        q_masks: list[torch.Tensor] = []
        for episode in episodes:
            advantage, value_return = primitive_gae(episode)
            q_target, q_mask = semi_markov_q_targets(episode)
            raw_advantages.append(advantage)
            returns.append(value_return.detach())
            q_targets.append(q_target)
            q_masks.append(q_mask)
        all_advantages = torch.cat(raw_advantages)
        advantage_mean = all_advantages.mean()
        advantage_scale = all_advantages.std(unbiased=False)
        standardized_advantages = [
            (advantage - advantage_mean) / (advantage_scale + 1e-8)
            for advantage in raw_advantages
        ]

        metrics: list[tuple[float, float, float, float, float]] = []
        self.model.train()
        for _epoch in range(PPO_EPOCHS):
            permutation = self.shuffle_rng.permutation(EPISODES_PER_UPDATE)
            for begin in range(0, EPISODES_PER_UPDATE, MINIBATCH_EPISODES):
                selected = [int(index) for index in permutation[begin:begin + MINIBATCH_EPISODES]]
                policy_terms: list[torch.Tensor] = []
                value_terms: list[torch.Tensor] = []
                q_terms: list[torch.Tensor] = []
                entropy_terms: list[torch.Tensor] = []
                selected_episodes = [episodes[index] for index in selected]
                forward = _evaluate_recurrent_batch(self.model, selected_episodes)
                joint_mask = forward.decision_mask.any(dim=2)
                if not bool(joint_mask.any(dim=1).all()):
                    raise RuntimeError("a complete training episode contains no option decision")
                old_log_probability = torch.stack([
                    episodes[index].old_joint_log_probabilities for index in selected
                ])
                actor_advantage = torch.stack([
                    standardized_advantages[index] for index in selected
                ])
                ratio = torch.exp(
                    forward.joint_log_probabilities[joint_mask]
                    - old_log_probability[joint_mask]
                )
                selected_advantage = actor_advantage[joint_mask]
                unclipped = ratio * selected_advantage
                clipped = torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * selected_advantage
                policy_terms.append(-torch.minimum(unclipped, clipped))
                value_target = torch.stack([returns[index] for index in selected])
                value_terms.append((forward.values - value_target).square().reshape(-1))
                q_mask = torch.stack([q_masks[index] for index in selected])
                if not bool(q_mask.any()):
                    raise RuntimeError("complete training minibatch contains no semi-Markov q target")
                q_target = torch.stack([q_targets[index] for index in selected])
                q_terms.append((forward.q_selected[q_mask] - q_target[q_mask]).square())
                entropy_terms.append(forward.joint_entropies[joint_mask])
                policy_loss = torch.cat(policy_terms).mean()
                value_loss = torch.cat(value_terms).mean()
                q_loss = torch.cat(q_terms).mean()
                joint_entropy = torch.cat(entropy_terms).mean()
                total_loss = (
                    policy_loss
                    + VALUE_COEFFICIENT * value_loss
                    + Q_COEFFICIENT * q_loss
                    - ENTROPY_COEFFICIENT * joint_entropy
                )
                if not bool(torch.isfinite(total_loss)):
                    raise RuntimeError("learned-arm PPO loss became non-finite")
                self.optimizer.zero_grad(set_to_none=True)
                total_loss.backward()
                gradient_norm = torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), max_norm=GRADIENT_CLIP
                )
                if (
                    self.optimizer_steps == 0
                    and self.on_first_optimizer_step is not None
                    and not self.activity_boundary_persisted
                ):
                    self.on_first_optimizer_step({
                        "revision": REVISION,
                        "arm": self.model.arm.value,
                        "algorithm_seed": self.algorithm_seed,
                        "optimizer_step": 1,
                        "scientific_activity_started": True,
                    })
                    # Returning from the callback certifies that the runner has
                    # atomically persisted the activity marker.  Set this before
                    # parameter mutation so an optimizer failure cannot cause a
                    # duplicate lifecycle event on retry.  A callback exception
                    # leaves both this flag and all optimizer counters unchanged.
                    self.activity_boundary_persisted = True
                self.optimizer.step()
                self.optimizer_steps += 1
                metrics.append((
                    float(policy_loss.detach()),
                    float(value_loss.detach()),
                    float(q_loss.detach()),
                    float(joint_entropy.detach()),
                    float(gradient_norm.detach()),
                ))

        self.completed_updates += 1
        self.episodes_seen += EPISODES_PER_UPDATE
        return PPOUpdateReport(
            revision=REVISION,
            arm=self.model.arm.value,
            algorithm_seed=self.algorithm_seed,
            update=self.completed_updates,
            episodes_seen=self.episodes_seen,
            optimizer_steps=self.optimizer_steps,
            mean_policy_loss=float(np.mean([row[0] for row in metrics])),
            mean_value_loss=float(np.mean([row[1] for row in metrics])),
            mean_q_loss=float(np.mean([row[2] for row in metrics])),
            mean_joint_entropy=float(np.mean([row[3] for row in metrics])),
            mean_gradient_norm=float(np.mean([row[4] for row in metrics])),
        )

    def final_checkpoint_payload(self, predictor_checkpoint_id: str) -> dict[str, object]:
        if self.completed_updates != TRAINING_UPDATES or self.episodes_seen != TRAIN_EPISODES:
            raise RuntimeError("only the exact last update of all 1,024 episodes may be retained")
        expected_steps = TRAINING_UPDATES * PPO_EPOCHS * (
            EPISODES_PER_UPDATE // MINIBATCH_EPISODES
        )
        if self.optimizer_steps != expected_steps:
            raise RuntimeError("optimizer-step count violates the frozen PPO schedule")
        if not predictor_checkpoint_id:
            raise ValueError("learned-arm checkpoint must bind the common frozen predictor")
        return {
            "schema": "CRTO-B1-LEARNED-ARM-v4",
            "revision": REVISION,
            "arm": self.model.arm.value,
            "algorithm_seed": self.algorithm_seed,
            "observation_dim": self.model.observation_dim,
            "centralized_state_dim": self.model.centralized_state_dim,
            "final_update": TRAINING_UPDATES,
            "episodes": self.episodes_seen,
            "optimizer_steps": self.optimizer_steps,
            "trainable_parameters": trainable_parameter_count(self.model),
            "predictor_checkpoint_id": predictor_checkpoint_id,
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
        }

    def save_final_checkpoint(self, path: Path, predictor_checkpoint_id: str) -> None:
        _atomic_torch_save(self.final_checkpoint_payload(predictor_checkpoint_id), Path(path))


def _atomic_torch_save(payload: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(descriptor)
    try:
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_final_checkpoint(
    path: Path, expected_predictor_checkpoint_id: str,
) -> tuple[RecurrentOptionActorCritic, dict[str, object]]:
    payload = torch.load(Path(path), map_location="cpu", weights_only=True)
    if payload.get("schema") != "CRTO-B1-LEARNED-ARM-v4" or payload.get("revision") != REVISION:
        raise ValueError("checkpoint is not an exact CRTO-B1 v4 learned arm")
    if payload.get("predictor_checkpoint_id") != expected_predictor_checkpoint_id:
        raise ValueError("learned arm is not bound to the expected frozen predictor")
    model = RecurrentOptionActorCritic(
        observation_dim=int(payload["observation_dim"]),
        centralized_state_dim=int(payload["centralized_state_dim"]),
        algorithm_seed=int(payload["algorithm_seed"]),
        arm=ArmKind(str(payload["arm"])),
    )
    model.load_state_dict(payload["model_state"], strict=True)
    model.eval()
    metadata = {
        key: value for key, value in payload.items()
        if key not in ("model_state", "optimizer_state")
    }
    return model, metadata
