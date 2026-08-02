"""Matched recurrent/current-state policy and paired sources for G35-P0."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.anchored_residual_g19 import (
    ENTROPY_COEFFICIENT,
    VALUE_CLIP,
    VALUE_COEFFICIENT,
    ResidualContinuousRosterPolicy,
    _channel_policy_loss,
    replay_trajectory,
)
from ha_ctse_process.return_to_go_direction_balanced_full_actor_g31 import (
    ReturnToGoDirectionBalancedFullActorPolicy,
    compute_return_to_go_credit,
)


ALGORITHM_ID = "CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35"
SOURCE_ID = "CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0"
REC_ARM = "REC"
CS_ARM = "CS"
ARMS = (REC_ARM, CS_ARM)
HIDDEN_DIM = 32
INITIAL_LOG_STD = -1.0
GRADIENT_LIVE_TOLERANCE = 1e-12
INITIAL_EQUALITY_TOLERANCE = 1e-7
CURRENT_STATE_WITNESS_FLOOR = 0.94048
EPISODE_SUPPORT = 128
NONFORMAL_SEED_OFFSET = 900_000

SEED_BASES = {
    "model": 10_351_000,
    "training_ledger": 10_352_000,
    "training_action": 10_353_000,
    "evaluation_base_ledger": 10_354_000,
    "evaluation_process": 10_355_000,
    "evaluation_action": 10_356_000,
    "initial_gradient_probe": 10_357_000,
}
BOOTSTRAP_SEED = 10_358_035


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if not 0 <= int(replicate) < 3:
        raise ValueError("G35 replicate outside registered support")
    offset = int(replicate) + (0 if formal else NONFORMAL_SEED_OFFSET)
    return {name: base + offset for name, base in SEED_BASES.items()}


def bootstrap_seed(*, formal: bool) -> int:
    return BOOTSTRAP_SEED + (0 if formal else NONFORMAL_SEED_OFFSET)


class G35MatchedStateCarryActor(ResidualContinuousRosterPolicy):
    """One shared actor graph whose only treatment is nonserialized carry."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.current_observation_residual is None:
            raise ValueError("G35 requires the common current-observation readout")
        nn.init.zeros_(self.current_observation_residual.weight)
        nn.init.zeros_(self.current_observation_residual.bias)
        self.carry_mode = REC_ARM

    @property
    def current_readout(self) -> nn.Linear:
        row = self.current_observation_residual
        assert isinstance(row, nn.Linear)
        return row

    def set_carry_mode(self, carry_mode: str) -> None:
        if carry_mode not in ARMS:
            raise ValueError("G35 carry mode must be REC or CS")
        self.carry_mode = carry_mode

    @property
    def carry_constant(self) -> int:
        return int(self.carry_mode == REC_ARM)

    def _initialize_next_hidden(self, hidden: torch.Tensor) -> torch.Tensor:
        return hidden.clone() if self.carry_constant else torch.zeros_like(hidden)

    def _actor_hidden_input(
        self, encoded_member: torch.Tensor, stored_hidden: torch.Tensor
    ) -> torch.Tensor:
        return encoded_member + self.carry_constant * stored_hidden

    def _carried_hidden(self, candidate: torch.Tensor) -> torch.Tensor:
        return self.carry_constant * candidate


class G35MatchedStateCarryPolicy(ReturnToGoDirectionBalancedFullActorPolicy):
    """G31 optimizer graph with the exact G35 carry treatment."""

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        member_capacity: int,
        action_dim: int,
        carry_mode: str,
        hidden_dim: int = HIDDEN_DIM,
    ) -> None:
        super().__init__(
            observation_dim,
            critic_state_dim,
            member_capacity=member_capacity,
            action_dim=action_dim,
            hidden_dim=hidden_dim,
            current_observation_residual=True,
            policy_type=G35MatchedStateCarryActor,
        )
        actor = self.policy
        assert isinstance(actor, G35MatchedStateCarryActor)
        actor.set_carry_mode(carry_mode)

    @property
    def carry_mode(self) -> str:
        actor = self.policy
        assert isinstance(actor, G35MatchedStateCarryActor)
        return actor.carry_mode

    @property
    def current_readout(self) -> nn.Linear:
        actor = self.policy
        assert isinstance(actor, G35MatchedStateCarryActor)
        return actor.current_readout


def make_model(
    member_capacity: int, *, carry_mode: str, initialization_seed: int
) -> G35MatchedStateCarryPolicy:
    torch.manual_seed(int(initialization_seed))
    model = G35MatchedStateCarryPolicy(
        roster_env.OBSERVATION_DIM,
        roster_env.CRITIC_STATE_DIM,
        member_capacity=int(member_capacity),
        action_dim=roster_env.ACTION_DIM,
        carry_mode=carry_mode,
        hidden_dim=HIDDEN_DIM,
    )
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def make_paired_models(
    member_capacity: int, *, initialization_seed: int
) -> dict[str, G35MatchedStateCarryPolicy]:
    rec = make_model(
        member_capacity,
        carry_mode=REC_ARM,
        initialization_seed=initialization_seed,
    )
    cs = make_model(
        member_capacity,
        carry_mode=CS_ARM,
        initialization_seed=initialization_seed,
    )
    cs.load_state_dict(rec.state_dict(), strict=True)
    assert_parameter_match(rec, cs, require_byte_identity=True)
    return {REC_ARM: rec, CS_ARM: cs}


def _state_bytes(model: nn.Module) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        (
            name,
            value.detach().cpu().contiguous().numpy().tobytes(),
        )
        for name, value in model.state_dict().items()
    )


def assert_parameter_match(
    rec: G35MatchedStateCarryPolicy,
    cs: G35MatchedStateCarryPolicy,
    *,
    require_byte_identity: bool,
) -> None:
    rec_state, cs_state = rec.state_dict(), cs.state_dict()
    if tuple(rec_state) != tuple(cs_state):
        raise ValueError("G35 arm state-dict key mismatch")
    if any(rec_state[name].shape != cs_state[name].shape for name in rec_state):
        raise ValueError("G35 arm state-dict shape mismatch")
    rec_mask = tuple((name, row.requires_grad) for name, row in rec.named_parameters())
    cs_mask = tuple((name, row.requires_grad) for name, row in cs.named_parameters())
    if rec_mask != cs_mask:
        raise ValueError("G35 arm trainable-mask mismatch")
    if rec.parameter_count != cs.parameter_count:
        raise ValueError("G35 arm parameter-count mismatch")
    if require_byte_identity and _state_bytes(rec) != _state_bytes(cs):
        raise ValueError("G35 initial state is not byte-identical")


def forced_initial_equality(
    rec: G35MatchedStateCarryPolicy,
    cs: G35MatchedStateCarryPolicy,
    *,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
    critic_state: torch.Tensor,
    sampling_noise: torch.Tensor,
) -> dict[str, float]:
    capacity = rec.member_capacity
    hidden = torch.zeros((observations.shape[0], capacity, rec.hidden_dim))
    arguments = {
        "observations": observations,
        "active_mask": active_mask,
        "critic_state": critic_state,
        "hidden": hidden,
        "sampling_noise": sampling_noise,
    }
    rec_output = rec.forward_step(**arguments)
    cs_output = cs.forward_step(**arguments)
    return {
        "pre_tanh": float((rec_output.pre_tanh_actions - cs_output.pre_tanh_actions).abs().max()),
        "actions": float((rec_output.actions - cs_output.actions).abs().max()),
        "token_log_prob": float((rec_output.token_log_probs - cs_output.token_log_probs).abs().max()),
        "value": float((rec_output.value - cs_output.value).abs().max()),
    }


def _process_rng(
    seed: int, capacity: int, local_episode_id: int, stream: int
) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence(
            [int(seed), int(capacity), int(local_episode_id), int(stream)]
        )
    )


def _balanced_assignments(
    categories: Sequence[object],
    *,
    replicate: int,
    capacity: int,
    process_seed: int,
    stream: int,
) -> tuple[object, ...]:
    if len(categories) != 3:
        raise ValueError("G35 balanced source requires three categories")
    counts = [43, 43, 43]
    counts[int(replicate) % 3] = 42
    order = sorted(
        range(EPISODE_SUPPORT),
        key=lambda episode: (
            int(
                _process_rng(
                    process_seed, capacity, episode, stream
                ).integers(0, 2**63)
            ),
            episode,
        ),
    )
    assigned: list[object | None] = [None] * EPISODE_SUPPORT
    offset = 0
    for category, count in zip(categories, counts):
        for episode in order[offset : offset + count]:
            assigned[episode] = category
        offset += count
    if offset != EPISODE_SUPPORT or any(row is None for row in assigned):
        raise RuntimeError("G35 balanced assignment did not close")
    return tuple(assigned)  # type: ignore[arg-type]


def _time_assignments(
    *, capacity: int, process_seed: int
) -> tuple[tuple[int, int, int, int], ...]:
    unused = list(g34.TIME_TUPLES)
    rows: list[tuple[int, int, int, int]] = []
    for episode in range(EPISODE_SUPPORT):
        rng = _process_rng(process_seed, capacity, episode, 0)
        rows.append(unused.pop(int(rng.integers(0, len(unused)))))
    return tuple(rows)


def _profile_assignments(
    *, replicate: int, capacity: int, process_seed: int
) -> tuple[roster_env.RosterProfile, ...]:
    if capacity == 6:
        return (roster_env.SMALL_CAPACITY_6,) * EPISODE_SUPPORT
    if capacity == 12:
        return (roster_env.LARGE_CAPACITY_12,) * EPISODE_SUPPORT
    if capacity == 8:
        return _balanced_assignments(
            roster_env.TRAIN_PROFILES,
            replicate=replicate,
            capacity=capacity,
            process_seed=process_seed,
            stream=2,
        )  # type: ignore[return-value]
    raise ValueError("G35 capacity outside registered support")


def make_process_ledgers(
    *, replicate: int, capacity: int, episode_count: int, formal: bool
) -> tuple[g34.RandomProcessLedger, ...]:
    if capacity not in g34.CAPACITIES or not 1 <= int(episode_count) <= EPISODE_SUPPORT:
        raise ValueError("G35 process request outside registered support")
    seeds = seed_block(replicate, formal=formal)
    times = _time_assignments(
        capacity=capacity, process_seed=seeds["evaluation_process"]
    )
    orders = _balanced_assignments(
        g34.EVENT_ORDERS,
        replicate=replicate,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
        stream=1,
    )
    profiles = _profile_assignments(
        replicate=replicate,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
    )
    rows: list[g34.RandomProcessLedger] = []
    for local_episode in range(int(episode_count)):
        base = roster_env.make_ledger(
            g34.episode_address(capacity, local_episode),
            master_seed=seeds["evaluation_base_ledger"],
            profile=profiles[local_episode],
        )
        expected, trajectory = g34._expected_roster_schedule(
            base, times[local_episode], orders[local_episode]  # type: ignore[arg-type]
        )
        row = g34.RandomProcessLedger(
            base=base,
            local_episode_id=local_episode,
            event_times=times[local_episode],
            event_order=orders[local_episode],  # type: ignore[arg-type]
            expected_roster_sizes=expected,
            count_trajectory=trajectory,
        )
        row.validate()
        rows.append(row)
    if len({row.signature for row in rows}) != len(rows):
        raise ValueError("G35 process signatures must be unique")
    return tuple(rows)


def _gradient_norm(loss: torch.Tensor, parameters: Sequence[nn.Parameter]) -> float:
    rows = torch.autograd.grad(
        loss, tuple(parameters), retain_graph=True, allow_unused=True
    )
    total = sum(
        torch.zeros((), dtype=torch.float64)
        if row is None
        else row.to(torch.float64).square().sum()
        for row in rows
    )
    value = torch.sqrt(total)
    return float(value.detach().cpu())


def g35_initial_gradient_audit(
    model: G35MatchedStateCarryPolicy,
    trajectory: Any,
    *,
    gamma: float,
    device: torch.device = torch.device("cpu"),
) -> dict[str, object]:
    """Audit live paths with the actual inherited objectives, without a step."""

    slow_critic_trainable = tuple(
        parameter.requires_grad for parameter in model.slow_critic.parameters()
    )
    for parameter in model.slow_critic.parameters():
        parameter.requires_grad_(True)
    model.train()
    replay = replay_trajectory(model, trajectory, device=device)
    rewards = trajectory.rewards.to(device)
    advantage = (rewards - trajectory.old_immediate_baselines.to(device)).detach()
    fast_policy = _channel_policy_loss(replay, trajectory, advantage)
    immediate_loss = F.mse_loss(
        replay.immediate_baselines, rewards.detach()
    )
    active_count = replay.active_mask.sum(dim=-1).clamp_min(1)
    entropy = (
        torch.where(replay.active_mask, replay.entropies, 0.0).sum(dim=-1)
        / active_count
    ).mean()
    fast_objective = (
        fast_policy
        + VALUE_COEFFICIENT * immediate_loss
        - ENTROPY_COEFFICIENT * entropy
    )

    terminals = torch.zeros_like(rewards, dtype=torch.bool)
    terminals[-1] = True
    credit = compute_return_to_go_credit(
        rewards=rewards,
        slow_values=trajectory.old_values.to(device),
        immediate_baselines=trajectory.old_immediate_baselines.to(device),
        successor_baselines=trajectory.old_successor_baselines.to(device),
        terminals=terminals,
        gamma=float(gamma),
    )
    immediate_actor = _channel_policy_loss(
        replay, trajectory, credit.immediate_residual
    )
    successor_actor = _channel_policy_loss(
        replay, trajectory, credit.successor_residual
    )
    old_values = trajectory.old_values.to(device)
    clipped = old_values + torch.clamp(
        replay.values - old_values, -VALUE_CLIP, VALUE_CLIP
    )
    slow_loss = torch.maximum(
        torch.square(replay.values - credit.slow_return_targets),
        torch.square(clipped - credit.slow_return_targets),
    ).mean()
    successor_loss = F.mse_loss(
        replay.successor_baselines, credit.successor_targets
    )
    rtg_actor_objective = 0.5 * (immediate_actor + successor_actor)

    actor = model.policy
    assert isinstance(actor, G35MatchedStateCarryActor)
    groups: dict[str, tuple[Sequence[nn.Parameter], torch.Tensor, torch.Tensor]] = {
        "member_encoder": (tuple(actor.member_encoder.parameters()), fast_objective, rtg_actor_objective),
        "context_encoder": (tuple(actor.context_encoder.parameters()), fast_objective, rtg_actor_objective),
        "gated_cell_input_weights": ((actor.actor_rnn.weight_ih,), fast_objective, rtg_actor_objective),
        "gated_cell_recurrent_weights": ((actor.actor_rnn.weight_hh,), fast_objective, rtg_actor_objective),
        "gated_cell_biases": ((actor.actor_rnn.bias_ih, actor.actor_rnn.bias_hh), fast_objective, rtg_actor_objective),
        "action_head": (tuple(actor.action_mean.parameters()), fast_objective, rtg_actor_objective),
        "current_readout": (tuple(actor.current_readout.parameters()), fast_objective, rtg_actor_objective),
        "log_std": ((actor.log_std,), fast_objective, rtg_actor_objective),
        "centralized_slow_critic": (tuple(model.slow_critic.parameters()), slow_loss * 0.0, slow_loss),
        "immediate_baseline": (tuple(model.credit_baselines.parameters()), immediate_loss, immediate_loss),
        "successor_baseline": (tuple(model.credit_baselines.parameters()), successor_loss * 0.0, successor_loss),
    }
    result: dict[str, object] = {}
    for name, (parameters, fast_loss, rtg_loss) in groups.items():
        fast_norm = _gradient_norm(fast_loss, parameters)
        rtg_norm = _gradient_norm(rtg_loss, parameters)
        live = (
            np.isfinite(fast_norm)
            and np.isfinite(rtg_norm)
            and max(fast_norm, rtg_norm) > GRADIENT_LIVE_TOLERANCE
        )
        result[name] = {
            "fast_objective_gradient_norm": fast_norm,
            "return_to_go_objective_gradient_norm": rtg_norm,
            "finite": bool(np.isfinite(fast_norm) and np.isfinite(rtg_norm)),
            "live": bool(live),
        }
    result["passed"] = all(bool(row["live"]) for row in result.values())
    for parameter, requires_grad in zip(
        model.slow_critic.parameters(), slow_critic_trainable
    ):
        parameter.requires_grad_(requires_grad)
    return result


def current_state_witness_utility(load: float, target_mix: float) -> float:
    effort = 0.5 * (1.0 + np.tanh(2.0 * float(load) - 1.0))
    mix = 0.5 * (1.0 + np.tanh(2.0 * float(target_mix) - 1.0))
    ratios = (
        effort * mix / (float(load) * float(target_mix)),
        effort * (1.0 - mix) / (float(load) * (1.0 - float(target_mix))),
    )
    return float(1.0 - 0.5 * sum(abs(row - 1.0) for row in ratios))


def source_controls() -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "horizon": roster_env.HORIZON,
        "training_capacity": roster_env.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "fixed_event_times": list(roster_env.EVENT_TIMES),
        "fixed_event_process": ["L", "R+J", "T"],
        "random_event_orders": [list(row) for row in g34.EVENT_ORDERS],
        "random_time_minimum": 5,
        "random_time_maximum": 43,
        "random_minimum_separation": 5,
        "random_load_boundary_modulus_excluded": 4,
        "seed_bases": dict(SEED_BASES),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "nonformal_seed_offset": NONFORMAL_SEED_OFFSET,
        "current_state_witness_floor": CURRENT_STATE_WITNESS_FLOOR,
        "carry_modes": list(ARMS),
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
    }
