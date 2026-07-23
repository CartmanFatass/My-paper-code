"""Matched TEAM_REC/DUM/EHC PPO core for cross-lifecycle handoff G2."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
import os
from pathlib import Path
import re
import time
from typing import Any

import torch
from torch import Tensor, nn

from ha_ctse_process.cross_lifecycle_handoff_g2 import (
    ACTION_VALUES,
    ACTOR_WIDTH,
    CRITIC_WIDTH,
    MAXIMUM_CAPACITY,
    CrossLifecycleHandoffG2Env,
    make_episode_spec,
)


SOURCE_FAMILY = "CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2"
CHECKPOINT_SCHEMA = "cross_lifecycle_commitment_handoff_g2_checkpoint_v1"
ARM_NAMES = ("TEAM_REC", "DUM", "EHC")
HIDDEN_WIDTH = 32

GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
PRIMITIVE_ENTROPY_COEFFICIENT = 0.01
MARK_ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50
LEARNING_RATE = 0.0003
PPO_PASSES = 4

_ATOMIC_REPLACE_ATTEMPTS = 100
_ATOMIC_REPLACE_RETRY_DELAY_SECONDS = 0.05


@dataclass(frozen=True, slots=True)
class SeedRegistry:
    model: int = 273401
    train_task: int = 273501
    train_membership: int = 273601
    train_nuisance: int = 273701
    train_primitive: int = 273801
    train_mark: int = 273901
    evaluation_task: int = 274001
    evaluation_membership: int = 274101
    evaluation_nuisance: int = 274201
    evaluation_primitive: int = 274301
    evaluation_mark: int = 274401
    audit: int = 274501
    bootstrap: int = 274601
    replicate_offset: int = 1000


class HandoffPolicy(nn.Module):
    """Same complete module inventory for every arm."""

    def __init__(self) -> None:
        super().__init__()
        self.actor_encoder = nn.Linear(ACTOR_WIDTH, HIDDEN_WIDTH)
        self.member_recurrent = nn.GRUCell(HIDDEN_WIDTH, HIDDEN_WIDTH)
        self.team_recurrent = nn.GRUCell(HIDDEN_WIDTH, HIDDEN_WIDTH)
        self.primitive_head = nn.Linear(HIDDEN_WIDTH, len(ACTION_VALUES))
        self.team_treatment = nn.Linear(HIDDEN_WIDTH, len(ACTION_VALUES), bias=False)
        self.mark_head = nn.Linear(HIDDEN_WIDTH, 2)
        self.mark_embedding = nn.Parameter(torch.empty(HIDDEN_WIDTH))
        self.mark_treatment = nn.Linear(HIDDEN_WIDTH, len(ACTION_VALUES), bias=False)
        self.critic_encoder = nn.Linear(CRITIC_WIDTH, HIDDEN_WIDTH)
        self.value_head = nn.Sequential(
            nn.Linear(HIDDEN_WIDTH, HIDDEN_WIDTH),
            nn.Tanh(),
            nn.Linear(HIDDEN_WIDTH, 1),
        )
        nn.init.normal_(self.mark_embedding, mean=0.0, std=0.02)

    def actor_features(self, actor: Tensor) -> Tensor:
        if actor.shape[-1] != ACTOR_WIDTH:
            raise ValueError("actor tensor has the wrong width")
        return torch.tanh(self.actor_encoder(actor))

    def primitive_logits(
        self,
        arm: str,
        member_hidden: Tensor,
        team_hidden: Tensor,
        held_mark: Tensor,
    ) -> Tensor:
        if arm not in ARM_NAMES:
            raise ValueError("unknown G2 arm")
        if member_hidden.shape[-1] != HIDDEN_WIDTH:
            raise ValueError("member hidden tensor has the wrong width")
        if team_hidden.shape[-1] != HIDDEN_WIDTH:
            raise ValueError("team hidden tensor has the wrong width")
        base = self.primitive_head(member_hidden)
        if arm == "TEAM_REC":
            treatment = self.team_treatment(team_hidden)
            while treatment.ndim < base.ndim:
                treatment = treatment.unsqueeze(-2)
            return base + treatment
        if arm == "EHC":
            signed_embedding = held_mark.to(base.dtype).unsqueeze(-1) * self.mark_embedding
            treatment = self.mark_treatment(signed_embedding)
            while treatment.ndim < base.ndim:
                treatment = treatment.unsqueeze(-2)
            return base + treatment
        return base

    def values(self, critic: Tensor, active_mask: Tensor) -> Tensor:
        if critic.shape[-1] != CRITIC_WIDTH:
            raise ValueError("critic tensor has the wrong width")
        if active_mask.shape != critic.shape[:-1]:
            raise ValueError("critic active mask has the wrong shape")
        encoded = torch.tanh(self.critic_encoder(critic))
        weights = active_mask.to(encoded.dtype).unsqueeze(-1)
        counts = weights.sum(dim=-2).clamp_min(1.0)
        pooled = (encoded * weights).sum(dim=-2) / counts
        return self.value_head(pooled).squeeze(-1)


@dataclass(slots=True)
class ArmState:
    arm: str
    replicate: int
    model: HandoffPolicy
    optimizer: torch.optim.Optimizer
    primitive_generator: torch.Generator
    mark_generator: torch.Generator
    optimizer_steps: int = 0
    completed_updates: int = 0
    episodes_completed: int = 0


@dataclass(slots=True)
class RolloutBatch:
    arm: str
    actor: Tensor
    critic: Tensor
    active_mask: Tensor
    reset_mask: Tensor
    episode_reset: Tensor
    create_mask: Tensor
    held_mark: Tensor
    actions: Tensor
    marks: Tensor
    old_primitive_logp: Tensor
    old_mark_logp: Tensor
    old_values: Tensor
    rewards: Tensor
    dones: Tensor
    advantages: Tensor
    returns: Tensor
    episode_records: list[dict[str, Any]]


@dataclass(slots=True)
class ReplayOutputs:
    primitive_logp: Tensor
    mark_logp: Tensor
    values: Tensor
    primitive_entropy: Tensor
    mark_entropy: Tensor


def _generator(seed: int) -> torch.Generator:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return generator


def initialize_matched_arms(
    *, replicate: int, seed_registry: SeedRegistry = SeedRegistry()
) -> dict[str, ArmState]:
    if type(replicate) is not int or replicate < 0:
        raise ValueError("replicate must be a nonnegative integer")
    model_seed = seed_registry.model + replicate * seed_registry.replicate_offset
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(model_seed)
        reference = HandoffPolicy()
    states: dict[str, ArmState] = {}
    for arm in ARM_NAMES:
        model = deepcopy(reference)
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
        states[arm] = ArmState(
            arm=arm,
            replicate=replicate,
            model=model,
            optimizer=optimizer,
            primitive_generator=_generator(
                seed_registry.train_primitive
                + replicate * seed_registry.replicate_offset
            ),
            mark_generator=_generator(
                seed_registry.train_mark + replicate * seed_registry.replicate_offset
            ),
        )
    return states


def _sample_indices(logits: Tensor, generator: torch.Generator) -> Tensor:
    probabilities = torch.softmax(logits, dim=-1)
    return torch.multinomial(
        probabilities.reshape(-1, probabilities.shape[-1]),
        1,
        generator=generator,
    ).reshape(logits.shape[:-1])


def _episode_environment(
    state: ArmState,
    *,
    update_index: int,
    environment_index: int,
    episode_index: int,
    seed_registry: SeedRegistry,
) -> CrossLifecycleHandoffG2Env:
    pair_index = environment_index // 2
    sign_mate = -1 if environment_index % 2 == 0 else 1
    base_id = (
        state.replicate * 1_000_000
        + update_index * 10_000
        + pair_index * 100
        + episode_index
    )
    return CrossLifecycleHandoffG2Env(
        make_episode_spec(
            "train",
            base_id=base_id,
            sign_mate=sign_mate,
            task_seed=seed_registry.train_task,
            membership_seed=seed_registry.train_membership,
            nuisance_seed=seed_registry.train_nuisance,
        )
    )


def _pack_observations(
    environments: list[CrossLifecycleHandoffG2Env],
) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    count = len(environments)
    actor = torch.zeros(count, MAXIMUM_CAPACITY, ACTOR_WIDTH)
    critic = torch.zeros(count, MAXIMUM_CAPACITY, CRITIC_WIDTH)
    active = torch.zeros(count, MAXIMUM_CAPACITY, dtype=torch.bool)
    reset = torch.zeros_like(active)
    create = torch.zeros_like(active)
    for environment_index, environment in enumerate(environments):
        for slot, observation in environment.observe().items():
            actor[environment_index, slot] = torch.tensor(observation.actor)
            critic[environment_index, slot] = torch.tensor(observation.critic)
            active[environment_index, slot] = True
            reset[environment_index, slot] = observation.actor[2] == 1.0
            create[environment_index, slot] = observation.opportunity_kind == "CREATE"
    return actor, critic, active, reset, create


def _advance_hidden(
    model: HandoffPolicy,
    actor: Tensor,
    active: Tensor,
    reset: Tensor,
    episode_reset: Tensor,
    member_hidden: Tensor,
    team_hidden: Tensor,
) -> tuple[Tensor, Tensor, Tensor]:
    member_hidden = torch.where(
        reset.unsqueeze(-1), torch.zeros_like(member_hidden), member_hidden
    )
    team_hidden = torch.where(
        episode_reset.unsqueeze(-1), torch.zeros_like(team_hidden), team_hidden
    )
    features = model.actor_features(actor)
    candidate = model.member_recurrent(
        features.reshape(-1, HIDDEN_WIDTH),
        member_hidden.reshape(-1, HIDDEN_WIDTH),
    ).reshape_as(member_hidden)
    # This source has terminal leave and JOIN only: inactive member state is
    # deleted, never frozen in a physical slot.
    member_hidden = torch.where(
        active.unsqueeze(-1), candidate, torch.zeros_like(candidate)
    )
    weights = active.to(features.dtype).unsqueeze(-1)
    pooled = (features * weights).sum(dim=1) / weights.sum(dim=1).clamp_min(1.0)
    team_hidden = model.team_recurrent(pooled, team_hidden)
    return features, member_hidden, team_hidden


def compute_gae(
    rewards: Tensor,
    values: Tensor,
    dones: Tensor,
    last_values: Tensor,
) -> tuple[Tensor, Tensor]:
    advantages = torch.zeros_like(rewards)
    next_advantage = torch.zeros(rewards.shape[0], dtype=rewards.dtype)
    next_value = last_values
    for time_index in reversed(range(rewards.shape[1])):
        not_done = (~dones[:, time_index]).to(rewards.dtype)
        delta = (
            rewards[:, time_index]
            + GAMMA * next_value * not_done
            - values[:, time_index]
        )
        next_advantage = delta + GAMMA * GAE_LAMBDA * not_done * next_advantage
        advantages[:, time_index] = next_advantage
        next_value = values[:, time_index]
    return advantages, advantages + values


def collect_rollout(
    state: ArmState,
    *,
    environments: int,
    horizon: int,
    update_index: int,
    seed_registry: SeedRegistry = SeedRegistry(),
) -> RolloutBatch:
    if state.arm not in ARM_NAMES:
        raise ValueError("state has an unknown arm")
    if type(environments) is not int or environments <= 0 or environments % 2:
        raise ValueError("environments must be a positive even integer")
    if type(horizon) is not int or horizon <= 0:
        raise ValueError("horizon must be a positive integer")
    if type(update_index) is not int or update_index < 0:
        raise ValueError("update_index must be a nonnegative integer")

    shape = (environments, horizon, MAXIMUM_CAPACITY)
    actor_store = torch.zeros(*shape, ACTOR_WIDTH)
    critic_store = torch.zeros(*shape, CRITIC_WIDTH)
    active_store = torch.zeros(shape, dtype=torch.bool)
    reset_store = torch.zeros(shape, dtype=torch.bool)
    episode_reset_store = torch.zeros(environments, horizon, dtype=torch.bool)
    create_store = torch.zeros(shape, dtype=torch.bool)
    held_store = torch.zeros(environments, horizon)
    action_store = torch.full(shape, -1, dtype=torch.long)
    mark_store = torch.full((environments, horizon), -1, dtype=torch.long)
    old_primitive_logp = torch.zeros(environments, horizon)
    old_mark_logp = torch.zeros(environments, horizon)
    value_store = torch.zeros(environments, horizon)
    reward_store = torch.zeros(environments, horizon)
    done_store = torch.zeros(environments, horizon, dtype=torch.bool)

    episode_indices = [0 for _ in range(environments)]
    environment_states = [
        _episode_environment(
            state,
            update_index=update_index,
            environment_index=index,
            episode_index=0,
            seed_registry=seed_registry,
        )
        for index in range(environments)
    ]
    member_hidden = torch.zeros(environments, MAXIMUM_CAPACITY, HIDDEN_WIDTH)
    team_hidden = torch.zeros(environments, HIDDEN_WIDTH)
    held_mark = torch.zeros(environments)
    current_marks = [0 for _ in range(environments)]
    episode_records: list[dict[str, Any]] = []

    state.model.eval()
    with torch.no_grad():
        for time_index in range(horizon):
            actor, critic, active, reset, create = _pack_observations(
                environment_states
            )
            episode_reset = torch.tensor(
                [environment.time == 0 for environment in environment_states],
                dtype=torch.bool,
            )
            features, member_hidden, team_hidden = _advance_hidden(
                state.model,
                actor,
                active,
                reset,
                episode_reset,
                member_hidden,
                team_hidden,
            )

            mark_logits = state.model.mark_head(features)
            if torch.any(create.sum(dim=-1) != episode_reset.to(torch.int64)):
                raise RuntimeError("CREATE inventory diverged from episode resets")
            if create.any():
                selected_marks = _sample_indices(
                    mark_logits[create], state.mark_generator
                )
                mark_store[:, time_index][create.any(dim=-1)] = selected_marks
                selected_values = 2 * selected_marks - 1
                create_environments = create.any(dim=-1)
                held_mark[create_environments] = selected_values.to(torch.float32)
                selected_logp = torch.log_softmax(mark_logits[create], dim=-1).gather(
                    -1, selected_marks.unsqueeze(-1)
                ).squeeze(-1)
                old_mark_logp[:, time_index][create_environments] = selected_logp
                for environment_index, selected in zip(
                    torch.nonzero(create_environments, as_tuple=False).flatten().tolist(),
                    selected_values.tolist(),
                    strict=True,
                ):
                    current_marks[environment_index] = int(selected)

            logits = state.model.primitive_logits(
                state.arm, member_hidden, team_hidden, held_mark
            )
            selected_actions = _sample_indices(logits[active], state.primitive_generator)
            action_store[:, time_index][active] = selected_actions
            selected_logp = torch.log_softmax(logits[active], dim=-1).gather(
                -1, selected_actions.unsqueeze(-1)
            ).squeeze(-1)
            row_logp = torch.zeros_like(active, dtype=torch.float32)
            row_logp[active] = selected_logp
            old_primitive_logp[:, time_index] = row_logp.sum(dim=-1)
            values = state.model.values(critic, active)

            actor_store[:, time_index] = actor
            critic_store[:, time_index] = critic
            active_store[:, time_index] = active
            reset_store[:, time_index] = reset
            episode_reset_store[:, time_index] = episode_reset
            create_store[:, time_index] = create
            held_store[:, time_index] = held_mark
            value_store[:, time_index] = values

            for environment_index, environment in enumerate(environment_states):
                action_dict = {
                    slot: ACTION_VALUES[int(action_store[environment_index, time_index, slot])]
                    for slot in torch.nonzero(active[environment_index], as_tuple=False)
                    .flatten()
                    .tolist()
                }
                transition = environment.step(action_dict)
                reward_store[environment_index, time_index] = float(
                    transition["reward"]
                )
                done = bool(transition["done"])
                done_store[environment_index, time_index] = done
                if done:
                    spec = environment.spec
                    episode_records.append(
                        {
                            "environment": environment_index,
                            "base_id": spec.base_id,
                            "sign_mate": spec.sign_mate,
                            "bit": spec.bit,
                            "utility": float(transition["utility"]),
                            "mark": current_marks[environment_index],
                            "profile": spec.profile,
                        }
                    )
                    episode_indices[environment_index] += 1
                    environment_states[environment_index] = _episode_environment(
                        state,
                        update_index=update_index,
                        environment_index=environment_index,
                        episode_index=episode_indices[environment_index],
                        seed_registry=seed_registry,
                    )
                    member_hidden[environment_index].zero_()
                    team_hidden[environment_index].zero_()
                    held_mark[environment_index] = 0
                    current_marks[environment_index] = 0
                else:
                    next_active = set(environment.observe())
                    for slot in range(MAXIMUM_CAPACITY):
                        if slot not in next_active:
                            member_hidden[environment_index, slot].zero_()

        last_actor, last_critic, last_active, _, _ = _pack_observations(
            environment_states
        )
        del last_actor
        last_values = state.model.values(last_critic, last_active)
        advantages, returns = compute_gae(
            reward_store, value_store, done_store, last_values
        )

    batch = RolloutBatch(
        arm=state.arm,
        actor=actor_store,
        critic=critic_store,
        active_mask=active_store,
        reset_mask=reset_store,
        episode_reset=episode_reset_store,
        create_mask=create_store,
        held_mark=held_store,
        actions=action_store,
        marks=mark_store,
        old_primitive_logp=old_primitive_logp,
        old_mark_logp=old_mark_logp,
        old_values=value_store,
        rewards=reward_store,
        dones=done_store,
        advantages=advantages,
        returns=returns,
        episode_records=episode_records,
    )
    validate_rollout(batch, arm=state.arm)
    return batch


def _all_finite(tensor: Tensor) -> bool:
    return bool(torch.isfinite(tensor).all())


def validate_rollout(batch: RolloutBatch, *, arm: str) -> None:
    if type(batch) is not RolloutBatch:
        raise TypeError("batch must be an exact RolloutBatch")
    if arm not in ARM_NAMES or batch.arm != arm:
        raise ValueError("rollout arm mismatch")
    environment_count, horizon, capacity = batch.active_mask.shape
    if capacity != MAXIMUM_CAPACITY:
        raise ValueError("rollout capacity mismatch")
    if batch.actor.shape != (environment_count, horizon, capacity, ACTOR_WIDTH):
        raise ValueError("actor rollout shape mismatch")
    if batch.critic.shape != (environment_count, horizon, capacity, CRITIC_WIDTH):
        raise ValueError("critic rollout shape mismatch")
    for tensor in (batch.active_mask, batch.reset_mask, batch.create_mask, batch.dones):
        if tensor.dtype != torch.bool:
            raise ValueError("rollout masks must be boolean")
    if batch.episode_reset.shape != (environment_count, horizon):
        raise ValueError("episode reset shape mismatch")
    if batch.episode_reset.dtype != torch.bool:
        raise ValueError("episode reset must be boolean")
    if torch.any(batch.reset_mask & ~batch.active_mask):
        raise ValueError("only active lifecycle rows may reset")
    if torch.any(batch.create_mask & ~batch.active_mask):
        raise ValueError("CREATE must belong to an active row")
    if torch.any(batch.create_mask.sum(dim=-1) != batch.episode_reset.to(torch.int64)):
        raise ValueError("each episode reset must have exactly one CREATE")
    if torch.any(batch.actions[batch.active_mask] < 0) or torch.any(
        batch.actions[batch.active_mask] >= len(ACTION_VALUES)
    ):
        raise ValueError("active primitive action is outside support")
    if torch.any(batch.actions[~batch.active_mask] != -1):
        raise ValueError("inactive row stores a primitive action")
    create_environment = batch.create_mask.any(dim=-1)
    if torch.any(batch.marks[create_environment] < 0) or torch.any(
        batch.marks[create_environment] > 1
    ):
        raise ValueError("CREATE mark is outside support")
    if torch.any(batch.marks[~create_environment] != -1):
        raise ValueError("non-CREATE row stores a mark")
    if torch.any((batch.held_mark != -1) & (batch.held_mark != 1)):
        raise ValueError("held mark must be -1 or +1 after CREATE")
    if torch.any((batch.rewards != 0) & (batch.rewards != 1)):
        raise ValueError("external reward must be zero or one")
    expected_scalar_shape = (environment_count, horizon)
    for name in (
        "old_primitive_logp",
        "old_mark_logp",
        "old_values",
        "rewards",
        "advantages",
        "returns",
    ):
        tensor = getattr(batch, name)
        if tensor.shape != expected_scalar_shape or not _all_finite(tensor):
            raise ValueError(f"{name} is nonfinite or has the wrong shape")


def replay_rollout(model: HandoffPolicy, arm: str, batch: RolloutBatch) -> ReplayOutputs:
    validate_rollout(batch, arm=arm)
    environment_count, horizon, _ = batch.active_mask.shape
    member_hidden = torch.zeros(environment_count, MAXIMUM_CAPACITY, HIDDEN_WIDTH)
    team_hidden = torch.zeros(environment_count, HIDDEN_WIDTH)
    primitive_rows: list[Tensor] = []
    mark_rows: list[Tensor] = []
    value_rows: list[Tensor] = []
    primitive_entropy_rows: list[Tensor] = []
    mark_entropy_rows: list[Tensor] = []

    for time_index in range(horizon):
        actor = batch.actor[:, time_index]
        critic = batch.critic[:, time_index]
        active = batch.active_mask[:, time_index]
        reset = batch.reset_mask[:, time_index]
        episode_reset = batch.episode_reset[:, time_index]
        features, member_hidden, team_hidden = _advance_hidden(
            model,
            actor,
            active,
            reset,
            episode_reset,
            member_hidden,
            team_hidden,
        )
        logits = model.primitive_logits(
            arm, member_hidden, team_hidden, batch.held_mark[:, time_index]
        )
        log_probs = torch.log_softmax(logits, dim=-1)
        selected = log_probs.gather(
            -1, batch.actions[:, time_index].clamp_min(0).unsqueeze(-1)
        ).squeeze(-1)
        selected = torch.where(active, selected, torch.zeros_like(selected))
        primitive_rows.append(selected.sum(dim=-1))
        entropy = -(log_probs.exp() * log_probs).sum(dim=-1)
        active_counts = active.sum(dim=-1).clamp_min(1)
        primitive_entropy_rows.append(
            (entropy * active.to(entropy.dtype)).sum(dim=-1) / active_counts
        )

        create = batch.create_mask[:, time_index]
        mark_logits = model.mark_head(features)
        mark_log_probs = torch.log_softmax(mark_logits, dim=-1)
        mark_selected = mark_log_probs.gather(
            -1,
            batch.marks[:, time_index]
            .clamp_min(0)
            .unsqueeze(-1)
            .unsqueeze(-1)
            .expand(-1, MAXIMUM_CAPACITY, 1),
        ).squeeze(-1)
        mark_rows.append(
            torch.where(create, mark_selected, torch.zeros_like(mark_selected)).sum(
                dim=-1
            )
        )
        mark_entropy = -(mark_log_probs.exp() * mark_log_probs).sum(dim=-1)
        mark_entropy_rows.append(
            torch.where(create, mark_entropy, torch.zeros_like(mark_entropy)).sum(
                dim=-1
            )
        )
        value_rows.append(model.values(critic, active))

    return ReplayOutputs(
        primitive_logp=torch.stack(primitive_rows, dim=1),
        mark_logp=torch.stack(mark_rows, dim=1),
        values=torch.stack(value_rows, dim=1),
        primitive_entropy=torch.stack(primitive_entropy_rows, dim=1),
        mark_entropy=torch.stack(mark_entropy_rows, dim=1),
    )


def assert_replay_equal(
    batch: RolloutBatch, replay: ReplayOutputs, *, tolerance: float = 1e-6
) -> dict[str, float]:
    errors = {
        "primitive": float(
            (replay.primitive_logp.detach() - batch.old_primitive_logp).abs().max()
        ),
        "mark": float((replay.mark_logp.detach() - batch.old_mark_logp).abs().max()),
        "value": float((replay.values.detach() - batch.old_values).abs().max()),
    }
    if errors["primitive"] > tolerance:
        raise ValueError(f"primitive replay mismatch: {errors['primitive']}")
    if errors["mark"] > tolerance:
        raise ValueError(f"mark replay mismatch: {errors['mark']}")
    if errors["value"] > tolerance:
        raise ValueError(f"value replay mismatch: {errors['value']}")
    return errors


def _module_gradient_norm(module: nn.Module) -> float:
    squared = 0.0
    for parameter in module.parameters():
        if parameter.grad is not None:
            squared += float(parameter.grad.detach().square().sum())
    return math.sqrt(squared)


def optimize_rollout(
    state: ArmState, batch: RolloutBatch, *, ppo_passes: int = PPO_PASSES
) -> dict[str, float | int]:
    if type(ppo_passes) is not int or ppo_passes != PPO_PASSES:
        raise ValueError("G2 requires exactly four PPO passes")
    validate_rollout(batch, arm=state.arm)
    state.model.train()
    normalized_advantages = (batch.advantages - batch.advantages.mean()) / (
        batch.advantages.std(unbiased=False) + 1e-8
    )
    old_joint = batch.old_primitive_logp + batch.old_mark_logp
    last_report: dict[str, float | int] = {}
    for _ in range(ppo_passes):
        replay = replay_rollout(state.model, state.arm, batch)
        new_joint = replay.primitive_logp + replay.mark_logp
        ratio = torch.exp((new_joint - old_joint).clamp(-20, 20))
        unclipped = ratio * normalized_advantages
        clipped = ratio.clamp(1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * normalized_advantages
        policy_loss = -torch.minimum(unclipped, clipped).mean()

        value_delta = replay.values - batch.old_values
        clipped_values = batch.old_values + value_delta.clamp(-VALUE_CLIP, VALUE_CLIP)
        value_loss = 0.5 * torch.maximum(
            (replay.values - batch.returns).square(),
            (clipped_values - batch.returns).square(),
        ).mean()
        primitive_entropy = replay.primitive_entropy.mean()
        create_count = batch.create_mask.any(dim=-1).sum().clamp_min(1)
        mark_entropy = replay.mark_entropy.sum() / create_count
        loss = (
            policy_loss
            + VALUE_COEFFICIENT * value_loss
            - PRIMITIVE_ENTROPY_COEFFICIENT * primitive_entropy
            - MARK_ENTROPY_COEFFICIENT * mark_entropy
        )
        if not torch.isfinite(loss):
            raise RuntimeError("G2 PPO loss is nonfinite")
        state.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        team_gradient = _module_gradient_norm(state.model.team_treatment)
        mark_gradient = _module_gradient_norm(state.model.mark_treatment)
        gradient_norm = float(
            nn.utils.clip_grad_norm_(state.model.parameters(), GRADIENT_CLIP)
        )
        if not math.isfinite(gradient_norm):
            raise RuntimeError("G2 PPO gradient norm is nonfinite")
        state.optimizer.step()
        state.optimizer_steps += 1
        last_report = {
            "loss": float(loss.detach()),
            "policy_loss": float(policy_loss.detach()),
            "value_loss": float(value_loss.detach()),
            "gradient_norm": gradient_norm,
            "team_treatment_gradient_norm": team_gradient,
            "mark_treatment_gradient_norm": mark_gradient,
            "optimizer_steps": ppo_passes,
        }
    return last_report


def _replace_with_permission_retry(temporary: Path, destination: Path) -> None:
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        try:
            os.replace(temporary, destination)
            return
        except PermissionError:
            if attempt + 1 == _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(_ATOMIC_REPLACE_RETRY_DELAY_SECONDS)


def _validate_source_commit(source_commit: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("source commit must be 40 lowercase hex chars")


def save_checkpoint(
    path: Path,
    state: ArmState,
    *,
    source_commit: str,
    update: int,
) -> None:
    _validate_source_commit(source_commit)
    if type(update) is not int or update < 0:
        raise ValueError("checkpoint update must be nonnegative")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": CHECKPOINT_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "backend": "cpu",
        "torch_threads": 1,
        "arm": state.arm,
        "replicate": state.replicate,
        "update": update,
        "optimizer_steps": state.optimizer_steps,
        "episodes_completed": state.episodes_completed,
        "model": state.model.state_dict(),
        "optimizer": state.optimizer.state_dict(),
        "primitive_generator": state.primitive_generator.get_state(),
        "mark_generator": state.mark_generator.get_state(),
    }
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        torch.save(payload, temporary)
        _replace_with_permission_retry(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_checkpoint(
    path: Path,
    *,
    expected_source_commit: str,
    expected_arm: str,
    expected_replicate: int,
) -> ArmState:
    _validate_source_commit(expected_source_commit)
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or payload.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError("checkpoint schema mismatch")
    if payload.get("source_family") != SOURCE_FAMILY:
        raise ValueError("checkpoint source family mismatch")
    if payload.get("source_commit") != expected_source_commit:
        raise ValueError("checkpoint source commit mismatch")
    if payload.get("backend") != "cpu" or payload.get("torch_threads") != 1:
        raise ValueError("checkpoint backend/thread contract mismatch")
    if payload.get("arm") != expected_arm:
        raise ValueError("checkpoint arm mismatch")
    if payload.get("replicate") != expected_replicate:
        raise ValueError("checkpoint replicate mismatch")
    state = initialize_matched_arms(replicate=expected_replicate)[expected_arm]
    state.model.load_state_dict(payload["model"], strict=True)
    state.optimizer.load_state_dict(payload["optimizer"])
    state.primitive_generator.set_state(payload["primitive_generator"])
    state.mark_generator.set_state(payload["mark_generator"])
    state.optimizer_steps = int(payload["optimizer_steps"])
    state.completed_updates = int(payload["update"])
    state.episodes_completed = int(payload["episodes_completed"])
    return state
