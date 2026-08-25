"""Exact post-anchor removal of G40's standalone slow critic for G41."""

from __future__ import annotations

import copy
import dis
import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process.anchored_residual_g19 import (
    AnchoredRosterTrajectory,
    normalize_advantage,
)


ALGORITHM_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41"
SOURCE_ID = "CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_P0"
ACCEPTED_G40_SOURCE_COMMIT = "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
ACCEPTED_G40_MANIFEST = (
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1/train_manifest.json"
)
ACCEPTED_G40_SCHEMA_VERSION = 1
ACCEPTED_G40_AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_FORMAL_AUTHORIZATION_V1"
)
ACCEPTED_G40_CHECKPOINT_KIND = "common_native6_fast_anchor"
ACCEPTED_G40_PAYLOAD_KIND = "anchor"
ACCEPTED_G40_COMPLETED_ANCHOR_UPDATES = 100
ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS = 200
ACCEPTED_G40_CONFIGURATION_FIELDS = (
    ("training_capacity", 8),
    ("anchor_updates", 100),
    ("ppo_passes", 2),
    ("environment_backend", "ContinuousRosterToyBatch_CPU_CPP_required"),
    ("common_anchor", "COMMON_NATIVE6_FAST_ANCHOR"),
    ("checkpoint_selection", "common_anchor_plus_branch_final_only"),
)
ACCEPTED_G40_CHECKPOINT_PAYLOAD_KEYS = frozenset(
    {
        "schema_version",
        "algorithm",
        "source_id",
        "source_commit",
        "formal",
        "replicate",
        "kind",
        "completed_anchor_updates",
        "completed_branch_updates",
        "configuration",
        "seeds",
        "model_state",
    }
)
FULL_PATH = "FULL_G40_G31"
NO_SLOW_PATH = "NO_SLOW_G41_G31"
PATHS = (FULL_PATH, NO_SLOW_PATH)
MAX_CONFORMANCE_TRANSITIONS = 8 * 48
PPO_PASSES = 2


@dataclass(frozen=True)
class AcceptedG40AnchorAuthority:
    replicate: int
    checkpoint_reference: str
    complete_state_digest: str
    anchor_model_seed: int
    anchor_ledger_seed: int
    anchor_action_seed: int


ACCEPTED_G40_ANCHOR_AUTHORITIES = (
    AcceptedG40AnchorAuthority(
        replicate=0,
        checkpoint_reference=(
            "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
            "20260727_97a8b23_r1/checkpoints/"
            "replicate_0_common_native6_fast_anchor.pt"
        ),
        complete_state_digest=(
            "8868edb01d7ecf93e0832606e5b433522cb9152e75cf972870e94d4116fc5fd6"
        ),
        anchor_model_seed=10_401_000,
        anchor_ledger_seed=10_402_000,
        anchor_action_seed=10_403_000,
    ),
    AcceptedG40AnchorAuthority(
        replicate=1,
        checkpoint_reference=(
            "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
            "20260727_97a8b23_r1/checkpoints/"
            "replicate_1_common_native6_fast_anchor.pt"
        ),
        complete_state_digest=(
            "2c256db95170e3882ef1f257cf5877e20ff74325b4f15592e5d386d0c689b888"
        ),
        anchor_model_seed=10_401_001,
        anchor_ledger_seed=10_402_001,
        anchor_action_seed=10_403_001,
    ),
    AcceptedG40AnchorAuthority(
        replicate=2,
        checkpoint_reference=(
            "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
            "20260727_97a8b23_r1/checkpoints/"
            "replicate_2_common_native6_fast_anchor.pt"
        ),
        complete_state_digest=(
            "8499c8943a965c5b2e7c089a9dddc256e1d195333838c6627ebe0a8720ebde51"
        ),
        anchor_model_seed=10_401_002,
        anchor_ledger_seed=10_402_002,
        anchor_action_seed=10_403_002,
    ),
)


@dataclass(frozen=True)
class G41ActorStep:
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    token_log_probs: torch.Tensor
    token_entropies: torch.Tensor
    next_hidden: torch.Tensor
    prefix_action_sums: torch.Tensor
    likelihood_mask: torch.Tensor


@dataclass(frozen=True)
class G41RetainedReplay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    immediate_baselines: torch.Tensor
    successor_baselines: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor


@dataclass(frozen=True)
class G41Credit:
    returns: torch.Tensor
    successor_targets: torch.Tensor
    immediate_advantage: torch.Tensor
    successor_advantage: torch.Tensor


def _state_rows(
    values: Mapping[str, torch.Tensor],
) -> tuple[tuple[str, str, tuple[int, ...], bytes], ...]:
    return tuple(
        (
            name,
            str(values[name].dtype),
            tuple(values[name].shape),
            values[name].detach().cpu().contiguous().numpy().tobytes(),
        )
        for name in sorted(values)
    )


def _state_digest(values: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name, dtype, shape, payload in _state_rows(values):
        digest.update(name.encode("utf-8"))
        digest.update(dtype.encode("ascii"))
        digest.update(np.asarray(shape, dtype=np.int64).tobytes())
        digest.update(payload)
    return digest.hexdigest()


def accepted_g40_anchor_authority(replicate: int) -> AcceptedG40AnchorAuthority:
    if isinstance(replicate, bool) or not isinstance(replicate, int):
        raise TypeError("G41 accepted anchor replicate must be an integer")
    if not 0 <= replicate < len(ACCEPTED_G40_ANCHOR_AUTHORITIES):
        raise ValueError("G41 accepted anchor replicate is not manifest-authorized")
    authority = ACCEPTED_G40_ANCHOR_AUTHORITIES[replicate]
    if authority.replicate != replicate:
        raise RuntimeError("G41 accepted anchor registry is internally inconsistent")
    return authority


def accepted_g40_anchor_identity(replicate: int) -> dict[str, object]:
    authority = accepted_g40_anchor_authority(replicate)
    return {
        "source_manifest": ACCEPTED_G40_MANIFEST,
        "source_commit": ACCEPTED_G40_SOURCE_COMMIT,
        "schema_version": ACCEPTED_G40_SCHEMA_VERSION,
        "algorithm": g40.ALGORITHM_ID,
        "source_id": g40.SOURCE_ID,
        "formal": True,
        "authorization_token": ACCEPTED_G40_AUTHORIZATION_TOKEN,
        "checkpoint_kind": ACCEPTED_G40_CHECKPOINT_KIND,
        "checkpoint_payload_kind": ACCEPTED_G40_PAYLOAD_KIND,
        "replicate": authority.replicate,
        "completed_anchor_updates": ACCEPTED_G40_COMPLETED_ANCHOR_UPDATES,
        "anchor_optimizer_steps": ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS,
        "checkpoint_reference": authority.checkpoint_reference,
        "complete_state_digest": authority.complete_state_digest,
        "anchor_model_seed": authority.anchor_model_seed,
        "anchor_ledger_seed": authority.anchor_ledger_seed,
        "anchor_action_seed": authority.anchor_action_seed,
        "configuration_identity": dict(ACCEPTED_G40_CONFIGURATION_FIELDS),
    }


def _validate_anchor_against_authority(
    anchor: g40.G40NativeSixPolicy, *, accepted_anchor_replicate: int
) -> AcceptedG40AnchorAuthority:
    if not isinstance(anchor, g40.G40NativeSixPolicy):
        raise TypeError("G41 paths require a G40 native-six anchor")
    if anchor.phase != "fast":
        raise ValueError("G41 paths require one common fast anchor")
    authority = accepted_g40_anchor_authority(accepted_anchor_replicate)
    if _state_digest(anchor.state_dict()) != authority.complete_state_digest:
        raise ValueError(
            "G41 anchor does not match immutable accepted G40 authority"
        )
    return authority


def load_accepted_g40_anchor_checkpoint(
    payload: Mapping[str, object], *, accepted_anchor_replicate: int
) -> g40.G40NativeSixPolicy:
    authority = accepted_g40_anchor_authority(accepted_anchor_replicate)
    if not isinstance(payload, Mapping) or set(payload) != set(
        ACCEPTED_G40_CHECKPOINT_PAYLOAD_KEYS
    ):
        raise ValueError("G41 accepted G40 checkpoint payload keys mismatch")
    expected = {
        "schema_version": ACCEPTED_G40_SCHEMA_VERSION,
        "algorithm": g40.ALGORITHM_ID,
        "source_id": g40.SOURCE_ID,
        "source_commit": ACCEPTED_G40_SOURCE_COMMIT,
        "formal": True,
        "replicate": authority.replicate,
        "kind": ACCEPTED_G40_PAYLOAD_KIND,
        "completed_anchor_updates": ACCEPTED_G40_COMPLETED_ANCHOR_UPDATES,
        "completed_branch_updates": 0,
    }
    if any(
        type(payload.get(name)) is not type(value)
        or payload.get(name) != value
        for name, value in expected.items()
    ):
        raise ValueError("G41 accepted G40 checkpoint identity mismatch")
    configuration = payload.get("configuration")
    if not isinstance(configuration, Mapping) or any(
        type(configuration.get(name)) is not type(value)
        or configuration.get(name) != value
        for name, value in ACCEPTED_G40_CONFIGURATION_FIELDS
    ):
        raise ValueError("G41 accepted G40 checkpoint configuration mismatch")
    seeds = payload.get("seeds")
    expected_seeds = g40.seed_block(authority.replicate, formal=True)
    if (
        not isinstance(seeds, Mapping)
        or set(seeds) != set(expected_seeds)
        or any(
            type(seeds.get(name)) is not int or seeds.get(name) != value
            for name, value in expected_seeds.items()
        )
    ):
        raise ValueError("G41 accepted G40 checkpoint seed identity mismatch")
    state = payload.get("model_state")
    if not isinstance(state, Mapping) or not all(
        isinstance(name, str) and isinstance(value, torch.Tensor)
        for name, value in state.items()
    ):
        raise ValueError("G41 accepted G40 checkpoint state missing")
    if _state_digest(state) != authority.complete_state_digest:  # type: ignore[arg-type]
        raise ValueError("G41 accepted G40 checkpoint state digest mismatch")
    anchor = g40.make_model(
        int(dict(ACCEPTED_G40_CONFIGURATION_FIELDS)["training_capacity"]),
        initialization_seed=authority.anchor_model_seed,
    )
    anchor.load_state_dict(state, strict=True)  # type: ignore[arg-type]
    _validate_anchor_against_authority(
        anchor, accepted_anchor_replicate=authority.replicate
    )
    return anchor


def retained_state_dict(
    model: nn.Module,
) -> dict[str, torch.Tensor]:
    return {
        name: value
        for name, value in model.state_dict().items()
        if not name.startswith("slow_critic.")
    }


def actor_head_parameter_names(model: nn.Module) -> tuple[str, ...]:
    return tuple(
        f"policy.{name}"
        for name, _ in model.policy.named_parameters()  # type: ignore[attr-defined]
        if not name.startswith("delayed_residual.")
        and not name.startswith("critic.")
    ) + tuple(
        name
        for name, _ in model.named_parameters()
        if name.startswith("credit_baselines.")
    )


def actor_head_parameters(model: nn.Module) -> tuple[nn.Parameter, ...]:
    named = dict(model.named_parameters())
    return tuple(named[name] for name in actor_head_parameter_names(model))


class G41NoSlowProjection(nn.Module):
    """G40 retained post-anchor graph with no standalone slow-critic module."""

    def __init__(
        self,
        anchor: g40.G40NativeSixPolicy,
        *,
        accepted_anchor_replicate: int,
    ) -> None:
        authority = _validate_anchor_against_authority(
            anchor, accepted_anchor_replicate=accepted_anchor_replicate
        )
        super().__init__()
        rng_before = torch.random.get_rng_state().clone()
        self.policy = copy.deepcopy(anchor.policy)
        self.credit_baselines = copy.deepcopy(anchor.credit_baselines)
        self.member_capacity = int(anchor.member_capacity)
        self.critic_state_dim = int(anchor.critic_state_dim)
        self.phase = "fast"
        self.accepted_g40_anchor_authority = authority
        self.projection_rng_unchanged = bool(
            torch.equal(rng_before, torch.random.get_rng_state())
        )
        if not self.projection_rng_unchanged:
            raise RuntimeError("G41 projection advanced global torch RNG")

    @property
    def hidden_dim(self) -> int:
        return int(self.policy.hidden_dim)

    @property
    def log_std(self) -> nn.Parameter:
        return self.policy.log_std

    @property
    def current_readout(self) -> nn.Linear:
        row = self.policy.current_observation_residual
        if not isinstance(row, nn.Linear):
            raise TypeError("G41 retained current readout is not linear")
        return row

    def actor_input(
        self, source_observations: torch.Tensor, active_mask: torch.Tensor
    ) -> torch.Tensor:
        return g40.g39.g38.build_g38_folded_actor_input(
            source_observations, active_mask
        )

    def baseline_values(
        self, critic_states: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if critic_states.shape[-1] != self.critic_state_dim:
            raise ValueError("G41 baseline critic-state shape mismatch")
        values = self.credit_baselines(critic_states)
        return values[..., 0], values[..., 1]

    def full_actor_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(
            parameter
            for name, parameter in self.policy.named_parameters()
            if not name.startswith("delayed_residual.")
            and not name.startswith("critic.")
        )

    def actor_credit_parameters(self) -> tuple[nn.Parameter, ...]:
        return self.full_actor_parameters() + tuple(
            self.credit_baselines.parameters()
        )

    def begin_credit_branch_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G41 no-slow branch may begin exactly once")
        final = self.policy.delayed_residual[-1]
        if not isinstance(final, nn.Linear) or any(
            bool(torch.count_nonzero(parameter)) for parameter in final.parameters()
        ):
            raise RuntimeError("G41 retained residual output is not exact zero")
        for name, parameter in self.policy.named_parameters():
            parameter.requires_grad_(
                not name.startswith("delayed_residual.")
                and not name.startswith("critic.")
            )
        for parameter in self.credit_baselines.parameters():
            parameter.requires_grad_(True)
        self.phase = "credit_branch"


def project_post_anchor_paths(
    anchor: g40.G40NativeSixPolicy,
    *,
    accepted_anchor_replicate: int,
) -> tuple[g40.G40NativeSixPolicy, G41NoSlowProjection]:
    authority = _validate_anchor_against_authority(
        anchor, accepted_anchor_replicate=accepted_anchor_replicate
    )
    rng_before = torch.random.get_rng_state().clone()
    full = copy.deepcopy(anchor)
    no_slow = G41NoSlowProjection(
        anchor,
        accepted_anchor_replicate=authority.replicate,
    )
    if not torch.equal(rng_before, torch.random.get_rng_state()):
        raise RuntimeError("G41 path construction advanced global torch RNG")
    if _state_rows(retained_state_dict(full)) != _state_rows(no_slow.state_dict()):
        raise RuntimeError("G41 projection changed retained anchor state")
    if g40.shared_tensor_storage_count((anchor, full, no_slow)) != 0:
        raise RuntimeError("G41 paths share retained tensor storage")
    return full, no_slow


def retained_actor_step(
    model: g40.G40NativeSixPolicy | G41NoSlowProjection,
    *,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
    critic_state: torch.Tensor,
    hidden: torch.Tensor,
    sampling_noise: torch.Tensor | None = None,
    teacher_pre_tanh: torch.Tensor | None = None,
    deterministic: bool = False,
) -> G41ActorStep:
    raw = model.policy.forward_step(
        observations=model.actor_input(observations, active_mask),
        active_mask=active_mask,
        critic_state=critic_state,
        hidden=hidden,
        sampling_noise=sampling_noise,
        teacher_pre_tanh=teacher_pre_tanh,
        deterministic=deterministic,
    )
    return G41ActorStep(
        actions=raw.actions,
        pre_tanh_actions=raw.pre_tanh_actions,
        token_log_probs=raw.token_log_probs,
        token_entropies=raw.token_entropies,
        next_hidden=raw.next_hidden,
        prefix_action_sums=raw.prefix_action_sums,
        likelihood_mask=raw.likelihood_mask,
    )


def retained_replay(
    model: g40.G40NativeSixPolicy | G41NoSlowProjection,
    trajectory: AnchoredRosterTrajectory,
) -> G41RetainedReplay:
    hidden = trajectory.hidden_before[0]
    outputs: list[G41ActorStep] = []
    resets = trajectory.terminal_hidden_reset_mask
    for time in range(trajectory.rewards.shape[0]):
        if resets is not None:
            hidden = torch.where(resets[time].unsqueeze(-1), 0.0, hidden)
        output = retained_actor_step(
            model,
            observations=trajectory.observations[time],
            active_mask=trajectory.active_mask[time],
            critic_state=trajectory.critic_states[time],
            hidden=hidden,
            teacher_pre_tanh=trajectory.pre_tanh_actions[time],
        )
        outputs.append(output)
        hidden = output.next_hidden
    immediate, successor = model.baseline_values(trajectory.critic_states)
    return G41RetainedReplay(
        log_probs=torch.stack([row.token_log_probs for row in outputs]),
        entropies=torch.stack([row.token_entropies for row in outputs]),
        immediate_baselines=immediate,
        successor_baselines=successor,
        hidden_after=torch.stack([row.next_hidden for row in outputs]),
        prefix_action_sums=torch.stack([row.prefix_action_sums for row in outputs]),
        active_mask=trajectory.active_mask,
    )


def retained_replay_errors(
    replay: G41RetainedReplay, trajectory: AnchoredRosterTrajectory
) -> dict[str, float]:
    mask = replay.active_mask
    return {
        "token_logprob_max_error": float(
            torch.abs(replay.log_probs - trajectory.old_log_probs)[mask].max()
        ),
        "immediate_baseline_max_error": float(
            torch.abs(
                replay.immediate_baselines - trajectory.old_immediate_baselines
            ).max()
        ),
        "successor_baseline_max_error": float(
            torch.abs(
                replay.successor_baselines - trajectory.old_successor_baselines
            ).max()
        ),
        "hidden_max_error": float(
            torch.abs(replay.hidden_after - trajectory.hidden_after).max()
        ),
        "prefix_max_error": float(
            torch.abs(
                replay.prefix_action_sums - trajectory.prefix_action_sums
            ).max()
        ),
    }


def compute_g31_credit_without_slow(
    *,
    rewards: torch.Tensor,
    immediate_baselines: torch.Tensor,
    successor_baselines: torch.Tensor,
    terminals: torch.Tensor,
    gamma: float = g40.GAMMA,
) -> G41Credit:
    if rewards.ndim != 2 or any(
        row.shape != rewards.shape
        for row in (immediate_baselines, successor_baselines, terminals)
    ):
        raise ValueError("G41 credit expects matching [time,batch] rows")
    if terminals.dtype != torch.bool or float(gamma) != g40.GAMMA:
        raise ValueError("G41 terminal/gamma left the frozen contract")
    if any(
        not bool(torch.isfinite(row).all())
        for row in (rewards, immediate_baselines, successor_baselines)
    ):
        raise ValueError("G41 credit received non-finite values")
    detached_rewards = rewards.detach()
    work_rewards = detached_rewards.to(torch.float64)
    nonterminal = (~terminals).to(torch.float64)
    work_returns = torch.empty_like(work_rewards)
    running = torch.zeros_like(work_rewards[0])
    for time in range(rewards.shape[0] - 1, -1, -1):
        running = work_rewards[time] + float(gamma) * nonterminal[time] * running
        work_returns[time] = running
    next_returns = torch.cat(
        (work_returns[1:], torch.zeros_like(work_returns[:1])), dim=0
    )
    returns = work_returns.to(rewards.dtype).detach()
    successor = (nonterminal * next_returns).to(rewards.dtype).detach()
    return G41Credit(
        returns=returns,
        successor_targets=successor,
        immediate_advantage=(
            detached_rewards - immediate_baselines.detach()
        ).detach(),
        successor_advantage=(successor - successor_baselines.detach()).detach(),
    )


def _normalized_g31_advantages(
    credit: G41Credit,
) -> tuple[torch.Tensor, torch.Tensor]:
    return (
        normalize_advantage(credit.immediate_advantage),
        normalize_advantage(credit.successor_advantage),
    )


def make_actor_head_optimizer(
    model: g40.G40NativeSixPolicy | G41NoSlowProjection,
) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.actor_credit_parameters(),
        lr=g40.LEARNING_RATE,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
    )


def make_full_slow_optimizer(
    model: g40.G40NativeSixPolicy,
) -> torch.optim.Adam:
    return torch.optim.Adam(
        model.slow_critic_parameters(),
        lr=g40.LEARNING_RATE,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
    )


def _retained_actor_head_pass(
    model: g40.G40NativeSixPolicy | G41NoSlowProjection,
    optimizer: torch.optim.Optimizer,
    replay: G41RetainedReplay,
    trajectory: AnchoredRosterTrajectory,
    credit: G41Credit,
    normalized_advantages: tuple[torch.Tensor, torch.Tensor],
) -> tuple[float, float, float]:
    actor_parameters = model.full_actor_parameters()
    actor_head = model.actor_credit_parameters()
    policy, actor_gradients = g40._actor_objective_gradients(
        g40.G31_ARM,
        model,
        replay,
        trajectory,
        normalized_advantages,
    )
    immediate_loss = F.mse_loss(
        replay.immediate_baselines, trajectory.rewards.detach()
    )
    successor_loss = F.mse_loss(
        replay.successor_baselines, credit.successor_targets
    )
    optimizer.zero_grad(set_to_none=True)
    (immediate_loss + successor_loss).backward()
    for parameter, gradient in zip(actor_parameters, actor_gradients):
        parameter.grad = gradient.clone()
    g40._optimizer_step(optimizer, actor_head)
    return (
        float(policy.detach()),
        float(immediate_loss.detach()),
        float(successor_loss.detach()),
    )


def optimize_retained_actor_head_update(
    model: g40.G40NativeSixPolicy | G41NoSlowProjection,
    optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if model.phase != "credit_branch" or int(ppo_passes) != PPO_PASSES:
        raise ValueError("G41 retained update requires two branch PPO passes")
    first_replay = retained_replay(model, trajectory)
    errors = retained_replay_errors(first_replay, trajectory)
    credit = compute_g31_credit_without_slow(
        rewards=trajectory.rewards,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(trajectory),
    )
    normalized = _normalized_g31_advantages(credit)
    metrics: list[tuple[float, float, float]] = []
    for pass_index in range(PPO_PASSES):
        replay = first_replay if pass_index == 0 else retained_replay(model, trajectory)
        metrics.append(
            _retained_actor_head_pass(
                model, optimizer, replay, trajectory, credit, normalized
            )
        )
    return {
        **errors,
        "actor_head_optimizer_steps": PPO_PASSES,
        "advantage_normalization_count": 2,
        "advantage_recomputed_between_passes": False,
        "baseline_gradients_enter_direction_norm": False,
        "gradient_clipping_applied": False,
        "pass_metrics": metrics,
    }


def optimize_full_slow_critic_update(
    model: g40.G40NativeSixPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: AnchoredRosterTrajectory,
    *,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, object]:
    if model.phase != "credit_branch" or int(ppo_passes) != PPO_PASSES:
        raise ValueError("G41 FULL slow update requires two PPO passes")
    credit = compute_g31_credit_without_slow(
        rewards=trajectory.rewards,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(trajectory),
    )
    parameters = model.slow_critic_parameters()
    losses: list[float] = []
    for _ in range(PPO_PASSES):
        values = torch.stack(
            [
                model.slow_critic(
                    torch.cat(
                        (
                            trajectory.critic_states[time],
                            torch.log1p(
                                trajectory.active_mask[time]
                                .sum(dim=-1)
                                .to(trajectory.critic_states.dtype)
                            ).unsqueeze(-1),
                        ),
                        dim=-1,
                    )
                ).squeeze(-1)
                for time in range(trajectory.rewards.shape[0])
            ]
        )
        loss = F.mse_loss(values, credit.returns)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        g40._optimizer_step(optimizer, parameters)
        losses.append(float(loss.detach()))
    return {"slow_critic_optimizer_steps": PPO_PASSES, "losses": losses}


def build_projected_checkpoint(
    model: G41NoSlowProjection,
) -> dict[str, object]:
    authority = model.accepted_g40_anchor_authority
    if authority != accepted_g40_anchor_authority(authority.replicate):
        raise RuntimeError("G41 projection lost immutable G40 anchor authority")
    state = {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }
    if any("slow_critic" in name for name in state):
        raise RuntimeError("G41 projected checkpoint retained a slow-critic key")
    return {
        "algorithm_id": ALGORITHM_ID,
        "checkpoint_kind": "NO_SLOW_POST_ANCHOR_G31",
        "accepted_g40_anchor_authority": accepted_g40_anchor_identity(
            authority.replicate
        ),
        "standalone_value_output_schema": False,
        "model_state": state,
        "model_state_digest": _state_digest(state),
    }


def evaluation_action_projection(step: G41ActorStep) -> torch.Tensor:
    return step.actions


def _bytecode_reads(function: Any) -> tuple[str, ...]:
    return tuple(
        str(instruction.argval)
        for instruction in dis.get_instructions(function)
        if instruction.opname in {"LOAD_ATTR", "LOAD_METHOD", "LOAD_GLOBAL"}
    )


def reconstruct_static_certificate(
    anchor: g40.G40NativeSixPolicy,
    full: g40.G40NativeSixPolicy,
    no_slow: G41NoSlowProjection,
    full_actor_optimizer: torch.optim.Optimizer,
    no_slow_actor_optimizer: torch.optim.Optimizer,
    checkpoint: Mapping[str, object],
) -> dict[str, object]:
    component_functions = {
        "actor_forward": (retained_actor_step, type(no_slow.policy).forward_step),
        "shared_baseline_forward": (retained_replay,),
        "immediate_target": (compute_g31_credit_without_slow,),
        "successor_target": (compute_g31_credit_without_slow,),
        "advantage_normalization": (_normalized_g31_advantages,),
        "direction_balance_entropy_clipping": (
            _retained_actor_head_pass,
            g40._actor_objective_gradients,
            g40._policy_loss_from_normalized_advantage,
            g40._entropy,
        ),
        "action_prefix": (retained_actor_step,),
        "checkpoint_selection": (build_projected_checkpoint,),
        "evaluation_metric": (evaluation_action_projection,),
        "rng_consumption": (project_post_anchor_paths,),
        "shared_retained_storage": (project_post_anchor_paths,),
    }
    reads = {
        name: sorted(
            {
                value
                for function in functions
                for value in _bytecode_reads(function)
            }
        )
        for name, functions in component_functions.items()
    }
    zero_slow_reads = {
        name: all("slow_critic" not in value for value in values)
        for name, values in reads.items()
    }
    full_names = actor_head_parameter_names(full)
    no_slow_names = actor_head_parameter_names(no_slow)
    full_named = dict(full.named_parameters())
    no_slow_named = dict(no_slow.named_parameters())
    parameter_contract_equal = bool(
        full_names == no_slow_names
        and all(
            full_named[name].shape == no_slow_named[name].shape
            and full_named[name].requires_grad == no_slow_named[name].requires_grad
            for name in full_names
        )
    )
    optimizer_order_equal = tuple(
        id(parameter)
        for group in full_actor_optimizer.param_groups
        for parameter in group["params"]
    ) == tuple(id(full_named[name]) for name in full_names) and tuple(
        id(parameter)
        for group in no_slow_actor_optimizer.param_groups
        for parameter in group["params"]
    ) == tuple(id(no_slow_named[name]) for name in no_slow_names)
    checkpoint_state = checkpoint.get("model_state")
    checkpoint_keys = (
        tuple(checkpoint_state)
        if isinstance(checkpoint_state, Mapping)
        else ("invalid",)
    )
    no_slow_names_all = tuple(name for name, _ in no_slow.named_parameters())
    no_slow_modules = tuple(name for name, _ in no_slow.named_modules())
    no_slow_state = tuple(no_slow.state_dict())
    no_standalone_slow = bool(
        not hasattr(no_slow, "slow_critic")
        and all("slow_critic" not in name for name in no_slow_names_all)
        and all("slow_critic" not in name for name in no_slow_modules)
        and all("slow_critic" not in name for name in no_slow_state)
        and all("slow_critic" not in name for name in checkpoint_keys)
    )
    retained_bytes_equal = _state_rows(retained_state_dict(full)) == _state_rows(
        no_slow.state_dict()
    )
    authority = no_slow.accepted_g40_anchor_authority
    expected_authority = accepted_g40_anchor_authority(authority.replicate)
    expected_identity = accepted_g40_anchor_identity(authority.replicate)
    registry_digests_well_formed = all(
        len(row.complete_state_digest) == 64
        and all(
            character in "0123456789abcdef"
            for character in row.complete_state_digest
        )
        for row in ACCEPTED_G40_ANCHOR_AUTHORITIES
    )
    source_bound = bool(
        registry_digests_well_formed
        and authority == expected_authority
        and _state_digest(anchor.state_dict())
        == expected_authority.complete_state_digest
        and checkpoint.get("accepted_g40_anchor_authority") == expected_identity
    )
    checkpoint_state_digest_valid = bool(
        isinstance(checkpoint_state, Mapping)
        and all(
            isinstance(name, str) and isinstance(value, torch.Tensor)
            for name, value in checkpoint_state.items()
        )
        and checkpoint.get("model_state_digest")
        == _state_digest(checkpoint_state)  # type: ignore[arg-type]
    )
    checkpoint_matches_projection = bool(
        isinstance(checkpoint_state, Mapping)
        and _state_rows(checkpoint_state)  # type: ignore[arg-type]
        == _state_rows(no_slow.state_dict())
    )
    output_schema_has_no_value = "value" not in {
        field.name for field in fields(G41ActorStep)
    }
    optimizer_states_empty = bool(
        full_actor_optimizer.state == {}
        and no_slow_actor_optimizer.state == {}
        and id(full_actor_optimizer.state) != id(no_slow_actor_optimizer.state)
    )
    retained_storage_disjoint = (
        g40.shared_tensor_storage_count((anchor, full, no_slow)) == 0
    )
    slow_retained_storage_disjoint = (
        g40.shared_tensor_storage_count(
            (full.policy, full.credit_baselines, full.slow_critic)
        )
        == 0
    )
    passed = bool(
        all(zero_slow_reads.values())
        and no_standalone_slow
        and parameter_contract_equal
        and optimizer_order_equal
        and optimizer_states_empty
        and retained_bytes_equal
        and retained_storage_disjoint
        and slow_retained_storage_disjoint
        and no_slow.projection_rng_unchanged
        and source_bound
        and checkpoint_state_digest_valid
        and checkpoint_matches_projection
        and output_schema_has_no_value
    )
    return {
        "component_bytecode_reads": reads,
        "zero_standalone_slow_reads": zero_slow_reads,
        "no_standalone_slow_module_parameter_or_checkpoint_key": no_standalone_slow,
        "actor_head_parameter_contract_equal": parameter_contract_equal,
        "actor_head_optimizer_order_equal": optimizer_order_equal,
        "actor_head_optimizer_states_empty_and_separate": optimizer_states_empty,
        "retained_state_bytes_equal": retained_bytes_equal,
        "retained_storage_disjoint": retained_storage_disjoint,
        "standalone_slow_retained_storage_disjoint": slow_retained_storage_disjoint,
        "projection_rng_unchanged": no_slow.projection_rng_unchanged,
        "checkpoint_bound_to_accepted_g40_source_and_anchor": source_bound,
        "manifest_backed_anchor_authority_valid": source_bound,
        "authority_registry_digests_well_formed": registry_digests_well_formed,
        "checkpoint_state_digest_valid": checkpoint_state_digest_valid,
        "checkpoint_matches_projection": checkpoint_matches_projection,
        "standalone_value_output_schema_absent": output_schema_has_no_value,
        "K_search": 0,
        "hypothetical_transitions": 0,
        "maximum_conformance_transitions": MAX_CONFORMANCE_TRANSITIONS,
        "passed": passed,
    }


def forward_equality_audit(
    full: g40.G40NativeSixPolicy,
    no_slow: G41NoSlowProjection,
    *,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
    critic_state: torch.Tensor,
    hidden: torch.Tensor,
    sampling_noise: torch.Tensor,
) -> dict[str, object]:
    left = retained_actor_step(
        full,
        observations=observations,
        active_mask=active_mask,
        critic_state=critic_state,
        hidden=hidden,
        sampling_noise=sampling_noise,
    )
    right = retained_actor_step(
        no_slow,
        observations=observations,
        active_mask=active_mask,
        critic_state=critic_state,
        hidden=hidden,
        sampling_noise=sampling_noise,
    )
    maximum_errors = {
        "pre_tanh": float((left.pre_tanh_actions - right.pre_tanh_actions).abs().max()),
        "actions": float((left.actions - right.actions).abs().max()),
        "prefix": float((left.prefix_action_sums - right.prefix_action_sums).abs().max()),
        "token_logprob": float((left.token_log_probs - right.token_log_probs).abs().max()),
    }
    inactive = ~active_mask
    exact_zero = bool(
        torch.count_nonzero(left.actions[inactive]) == 0
        and torch.count_nonzero(right.actions[inactive]) == 0
        and torch.count_nonzero(left.token_log_probs[inactive]) == 0
        and torch.count_nonzero(right.token_log_probs[inactive]) == 0
        and torch.count_nonzero(left.next_hidden) == 0
        and torch.count_nonzero(right.next_hidden) == 0
    )
    passed = bool(
        maximum_errors["pre_tanh"] <= 1e-7
        and maximum_errors["actions"] <= 1e-7
        and maximum_errors["prefix"] <= 1e-7
        and maximum_errors["token_logprob"] <= 1e-6
        and exact_zero
    )
    return {
        "maximum_errors": maximum_errors,
        "inactive_actions_likelihoods_and_hidden_exact_zero": exact_zero,
        "passed": passed,
    }
