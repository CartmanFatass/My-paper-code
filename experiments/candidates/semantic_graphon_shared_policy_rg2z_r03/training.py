"""Full-BPTT projected-Adam training for the one update-512 checkpoint."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import torch

from .authorization import ProductionPermit, require_active_permit
from .config import (
    ADAM_BETAS,
    ADAM_EPSILON,
    CRITIC_COEFFICIENT,
    ENTROPY_COEFFICIENT,
    EPISODES_PER_TRAIN_ROSTER,
    EPISODES_PER_UPDATE,
    GRADIENT_NORM_CLIP,
    HORIZON,
    LEARNING_RATE,
    SEEDS,
    TRAINING_DTYPE,
    TRAINING_UPDATES,
    TRAIN_ROSTERS,
    legal_action_indices,
)
from .policies import ArmModel, KernelCondition, TeamCritic, make_paired_models
from .rng import Coordinate, CounterRNG, inverse_cdf_index
from .world import EpisodeMetrics, RidgeGateWorld


Phase = Literal["training", "evaluation"]


def _require_local_permit(permit: ProductionPermit, seed: int) -> None:
    if not isinstance(permit, ProductionPermit):
        raise PermissionError("validated ProductionPermit is required")
    permit.assert_local_validity()
    if seed not in permit.payload["authorized_seeds"]:
        raise PermissionError("seed is outside the frozen registered panel")


@dataclass(frozen=True)
class EpisodeResult:
    return_value: float
    basin_delivery_rates: tuple[float, float]
    metrics: EpisodeMetrics
    loss: torch.Tensor | None
    shadow_tv_mean: float | None
    tv_support_mean: float | None


@dataclass(frozen=True)
class CompletedTrainingPair:
    seed: int
    update: int
    phy_trust: ArmModel
    edge_flex: ArmModel
    metadata: dict[str, object]


def training_batch_rosters() -> tuple[int, ...]:
    rosters = tuple(TRAIN_ROSTERS[index % 2] for index in range(EPISODES_PER_UPDATE))
    if any(rosters.count(n) != EPISODES_PER_TRAIN_ROSTER for n in TRAIN_ROSTERS):
        raise RuntimeError("the frozen alternating training batch is malformed")
    return rosters


def _action_uniform(
    rng: CounterRNG,
    coordinate: Coordinate,
    slot: int,
    role: int,
    role_local_index: int,
) -> float:
    return rng.uniform(
        *coordinate.address(),
        "slot", slot,
        "public-role", role,
        "role-local-simulator-index", role_local_index,
        "random-variable-kind", "inverse-cdf-action-uniform",
    )


def _sample_model_actions(
    probabilities: torch.Tensor,
    world: RidgeGateWorld,
    rng: CounterRNG,
    coordinate: Coordinate,
) -> tuple[list[int], torch.Tensor]:
    actions: list[int] = []
    selected: list[torch.Tensor] = []
    for agent_index, state in enumerate(world.agents):
        row = probabilities[agent_index]
        uniform = _action_uniform(
            rng, coordinate, world.slot, int(state.role), state.role_local_index
        )
        index = inverse_cdf_index(row.detach().to(torch.float64).tolist(), uniform)
        actions.append(index)
        selected.append(row[index])
    return actions, torch.stack(selected)


def _uniform_legal_actions(
    world: RidgeGateWorld, rng: CounterRNG, coordinate: Coordinate
) -> list[int]:
    actions: list[int] = []
    for state in world.agents:
        legal = legal_action_indices(state.role)
        probabilities = [1.0 / len(legal)] * len(legal)
        uniform = _action_uniform(
            rng, coordinate, world.slot, int(state.role), state.role_local_index
        )
        actions.append(legal[inverse_cdf_index(probabilities, uniform)])
    return actions


def _tv_support(probabilities: torch.Tensor, roles: torch.Tensor) -> torch.Tensor:
    values: list[torch.Tensor] = []
    for agent_index, role_value in enumerate(roles.tolist()):
        legal = legal_action_indices(role_value)
        legal_probabilities = probabilities[agent_index, list(legal)]
        floor = 0.04 / len(legal)
        values.append(1.0 - (len(legal) - 1) * floor - torch.min(legal_probabilities))
    return torch.stack(values)


def rollout_model_episode(
    permit: ProductionPermit,
    model: ArmModel,
    coordinate: Coordinate,
    *,
    rng: CounterRNG | None = None,
    condition: KernelCondition = "intact",
    require_loss: bool = False,
    capture_shadow_cut: bool = False,
) -> EpisodeResult:
    """Roll one complete addressed trajectory without truncating recurrent state."""
    if capture_shadow_cut and condition != "intact":
        raise ValueError("the shadow cut is defined only on intact histories")
    if require_loss and coordinate.phase != "training":
        raise ValueError("actor-critic loss is defined only on training coordinates")
    if not require_loss and coordinate.phase != "evaluation":
        raise ValueError("loss-free rollout is confined to evaluation coordinates")
    if condition == "rotated" and coordinate.roster not in (6, 21):
        raise ValueError("full rotated rollouts exist only at held-out rosters")
    if capture_shadow_cut and coordinate.roster not in (6, 21):
        raise ValueError("shadow cuts exist only at held-out rosters")
    _require_local_permit(permit, coordinate.seed)
    rng = rng or CounterRNG(permit)
    rng.require_same_permit(permit)
    world = RidgeGateWorld(permit, coordinate, rng)
    roles = world.roles_tensor()
    hidden = model.actor.zero_hidden(world.n_agents)
    log_probabilities: list[torch.Tensor] = []
    entropies: list[torch.Tensor] = []
    critic_values: list[torch.Tensor] = []
    shadow_tvs: list[torch.Tensor] = []
    tv_supports: list[torch.Tensor] = []

    for _ in range(HORIZON):
        observations = world.observations()
        incoming_hidden = hidden
        actor_step = model.actor.forward_step(
            observations, roles, incoming_hidden, condition=condition
        )
        if capture_shadow_cut:
            shadow = model.actor.shadow_rotated_probabilities(
                observations, roles, incoming_hidden
            )
            shadow_tvs.append(
                0.5 * torch.sum(torch.abs(actor_step.probabilities - shadow), dim=-1)
            )
        if capture_shadow_cut:
            tv_supports.append(_tv_support(actor_step.probabilities, roles))
        hidden = actor_step.hidden

        actions, selected = _sample_model_actions(
            actor_step.probabilities, world, rng, coordinate
        )
        if require_loss:
            log_probabilities.append(torch.log(selected))
            entropies.append(-torch.sum(torch.special.xlogy(
                actor_step.probabilities, actor_step.probabilities
            ), dim=-1))
            team_state = TeamCritic.team_state(observations, roles)
            critic_values.append(model.critic(team_state))
        world.step(actions)

    terminal_return = world.return_value()
    loss: torch.Tensor | None = None
    if require_loss:
        terminal = torch.tensor(terminal_return, dtype=TRAINING_DTYPE)
        values = torch.stack(critic_values)
        actor_terms: list[torch.Tensor] = []
        for slot in range(HORIZON):
            advantage = (terminal - values[slot]).detach()
            actor_terms.append(log_probabilities[slot] * advantage)
        actor_loss = -torch.cat(actor_terms).mean()
        entropy_loss = -ENTROPY_COEFFICIENT * torch.cat(entropies).mean()
        critic_loss = CRITIC_COEFFICIENT * torch.mean((values - terminal) ** 2)
        loss = actor_loss + entropy_loss + critic_loss

    shadow_tv_mean = (
        float(torch.cat(shadow_tvs).to(torch.float64).mean().item())
        if shadow_tvs else None
    )
    tv_support_mean = (
        float(torch.cat(tv_supports).to(torch.float64).mean().item())
        if tv_supports else None
    )
    return EpisodeResult(
        return_value=terminal_return,
        basin_delivery_rates=world.basin_delivery_rates(),
        metrics=world.metrics,
        loss=loss,
        shadow_tv_mean=shadow_tv_mean,
        tv_support_mean=tv_support_mean,
    )


def rollout_uniform_episode(
    permit: ProductionPermit,
    coordinate: Coordinate,
    *,
    rng: CounterRNG | None = None,
) -> EpisodeResult:
    _require_local_permit(permit, coordinate.seed)
    rng = rng or CounterRNG(permit)
    rng.require_same_permit(permit)
    world = RidgeGateWorld(permit, coordinate, rng)
    for _ in range(HORIZON):
        world.observations()
        world.step(_uniform_legal_actions(world, rng, coordinate))
    return EpisodeResult(
        return_value=world.return_value(),
        basin_delivery_rates=world.basin_delivery_rates(),
        metrics=world.metrics,
        loss=None,
        shadow_tv_mean=None,
        tv_support_mean=None,
    )


def _optimizer(model: ArmModel) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        betas=ADAM_BETAS,
        eps=ADAM_EPSILON,
        weight_decay=0.0,
        foreach=False,
    )


def _train_one_update_after_full_validation(
    permit: ProductionPermit,
    model: ArmModel,
    optimizer: torch.optim.Adam,
    *,
    seed: int,
    update: int,
    rng: CounterRNG | None = None,
) -> None:
    if update < 1 or update > TRAINING_UPDATES:
        raise ValueError("update must be in the frozen inclusive range 1..512")
    rng = rng or CounterRNG(permit)
    rng.require_same_permit(permit)
    model.train()
    episode_losses: list[torch.Tensor] = []
    for episode, roster in enumerate(training_batch_rosters()):
        result = rollout_model_episode(
            permit,
            model,
            Coordinate(
                phase="training", seed=seed, roster=roster,
                update=update, episode=episode,
            ),
            rng=rng,
            condition="intact",
            require_loss=True,
        )
        if result.loss is None:
            raise RuntimeError("training rollout did not produce its episode loss")
        episode_losses.append(result.loss)

    optimizer.zero_grad(set_to_none=True)
    full_batch_loss = torch.stack(episode_losses).mean()
    full_batch_loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_NORM_CLIP)
    optimizer.step()
    model.project_beta_()


def train_one_update(
    permit: ProductionPermit,
    model: ArmModel,
    optimizer: torch.optim.Adam,
    *,
    seed: int,
    update: int,
    rng: CounterRNG | None = None,
) -> None:
    """One standalone update boundary with full certificate/lease revalidation."""
    require_active_permit(permit)
    if seed not in permit.payload["authorized_seeds"]:
        raise PermissionError("seed is outside the frozen registered panel")
    _train_one_update_after_full_validation(
        permit, model, optimizer, seed=seed, update=update, rng=rng
    )


def train_complete_pair(
    permit: ProductionPermit,
    seed: int,
    result_root: Path,
    certificate_path: Path,
    rng: CounterRNG | None = None,
) -> CompletedTrainingPair:
    """Produce only the checkpoint immediately after matched update 512."""
    require_active_permit(permit)
    permit.require_seed(seed)
    if seed not in SEEDS:
        raise ValueError("the training seed is outside the frozen 24-seed panel")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    rng = rng or CounterRNG(permit)
    rng.require_same_permit(permit)
    from .artifacts import expected_training_metadata, load_training_frontier, write_training_frontier

    if not isinstance(result_root, Path) or not isinstance(certificate_path, Path):
        raise TypeError("training continuity requires Path result-root and certificate bindings")
    phy = ArmModel("PHY-TRUST")
    edge = ArmModel("EDGE-FLEX")
    phy_optimizer = _optimizer(phy)
    edge_optimizer = _optimizer(edge)
    models = {"PHY-TRUST": phy, "EDGE-FLEX": edge}
    optimizers = {"PHY-TRUST": phy_optimizer, "EDGE-FLEX": edge_optimizer}
    completed_update = load_training_frontier(
        result_root, permit, certificate_path, seed, models, optimizers
    )
    if completed_update is None:
        phy, edge = make_paired_models(permit, seed, rng)
        initial_equal = (
            set(phy.state_dict()) == set(edge.state_dict())
            and all(torch.equal(phy.state_dict()[name], edge.state_dict()[name]) for name in phy.state_dict())
        )
        if not initial_equal:
            raise RuntimeError("paired learned arms lack bitwise-equal initial common tensors")
        phy_optimizer = _optimizer(phy)
        edge_optimizer = _optimizer(edge)
        models = {"PHY-TRUST": phy, "EDGE-FLEX": edge}
        optimizers = {"PHY-TRUST": phy_optimizer, "EDGE-FLEX": edge_optimizer}
        completed_update = 0
    for update in range(completed_update + 1, TRAINING_UPDATES + 1):
        # One full external revocation/source check per matched update; the two
        # arm batches and all inner stochastic primitives use local expiry checks.
        permit.assert_active()
        if seed not in permit.payload["authorized_seeds"]:
            raise PermissionError("seed is outside the frozen registered panel")
        _train_one_update_after_full_validation(
            permit, phy, phy_optimizer, seed=seed, update=update, rng=rng
        )
        _train_one_update_after_full_validation(
            permit, edge, edge_optimizer, seed=seed, update=update, rng=rng
        )
        write_training_frontier(
            result_root, permit, certificate_path, seed, update, models, optimizers
        )
    return CompletedTrainingPair(
        seed, TRAINING_UPDATES, phy, edge, expected_training_metadata(seed)
    )
