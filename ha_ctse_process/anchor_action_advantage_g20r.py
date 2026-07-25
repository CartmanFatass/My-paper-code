"""Anchor-policy conditional action advantage credit rule for G20R.

G20R keeps everything G20 kept unchanged from G19: the trained-then-frozen G17
fast actor, the exact-zero delayed-residual initialization with bitwise fast
freeze, and exact active-set centering of the applied pre-tanh residual. It
differs from G20 only in *what carries member-resolved credit*: not a
leave-one-out contrast over the centered residual table (retired -- see
``ha_ctse_process/centered_residual_g20.py`` and the fixed-point evidence note
that repairs it), but a prefix critic ``Q_j`` over the executed action at each
member's routing position, contrasted against an expectation over ``K``
actions resampled from the frozen anchor policy at the same decision history.

``Q_j`` is realized as a strict function of exactly four inputs -- critic
state, active mask, routing position, and the action-prefix through and
including that position -- and never receives any information about actions
at a later routing position.  This module owns the policy subclass, ``Q_j``,
the anchor-baseline advantage and both update rules; it stays neutral to the
calling environment/source exactly like its G17/G18/G19/G20 counterparts.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable

import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process.continuous_roster_policy import (
    ContinuousRosterPolicy,
    ContinuousStepOutput,
)


PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50
BASELINE_SAMPLES_K = 8


def center_residual_over_active_set(
    raw: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    """Exactly center an observation-only residual table over the active set.

    Member ``i`` receives ``f(o_i) - (1/N) * sum_{j active} f(o_j)``.  The
    result therefore sums to zero over the active set per action coordinate
    per batch row, and inactive rows receive exactly zero.  This is the
    retained, unchanged G20 centering operator; it is copied here (not
    imported from the retired module) because ``centered_residual_g20.py`` is
    kept only as frozen evidence and is not extended.
    """

    if raw.shape[:-1] != active_mask.shape:
        raise ValueError(
            "G20R centering shape mismatch between residual table and active mask"
        )
    if active_mask.dtype != torch.bool:
        raise ValueError("G20R centering active mask must be bool")
    dtype = raw.dtype
    mask = active_mask.to(dtype).unsqueeze(-1)
    active_count = active_mask.sum(dim=-1).to(dtype).clamp_min(1.0).unsqueeze(-1)
    active_mean = (raw * mask).sum(dim=-2) / active_count
    return torch.where(
        active_mask.unsqueeze(-1),
        raw - active_mean.unsqueeze(-2),
        torch.zeros_like(raw),
    )


@dataclass
class AnchorActionStepOutput:
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    token_log_probs: torch.Tensor
    token_entropies: torch.Tensor
    value: torch.Tensor
    next_hidden: torch.Tensor
    prefix_action_sums: torch.Tensor
    likelihood_mask: torch.Tensor
    centered_residual: torch.Tensor
    anchor_means: torch.Tensor
    position_value: torch.Tensor


class AnchorActionAdvantageRosterPolicy(ContinuousRosterPolicy):
    """Continuous policy whose additive delayed head is exactly active-set centered.

    Identical residual construction to G20's centered policy (observation-only
    delayed head, active-set centering).  The only addition is a side-channel
    capture of each routed member's *anchor* mean -- the base policy's mean
    before the (possibly nonzero) residual is added -- so the credit rule
    below can resample ``K`` actions from the frozen anchor distribution at
    the same decision history without duplicating the autoregressive routing
    loop that lives in the untouched base class.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.delayed_residual = nn.Sequential(
            nn.Linear(self.observation_dim, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.action_dim),
        )
        final = self.delayed_residual[-1]
        assert isinstance(final, nn.Linear)
        nn.init.zeros_(final.weight)
        nn.init.zeros_(final.bias)
        for parameter in self.delayed_residual.parameters():
            parameter.requires_grad_(False)
        self._pending_active_mean: torch.Tensor | None = None
        self._anchor_mean_capture: list[torch.Tensor] = []

    def forward_step(
        self,
        *,
        observations: torch.Tensor,
        active_mask: torch.Tensor,
        critic_state: torch.Tensor,
        hidden: torch.Tensor,
        sampling_noise: torch.Tensor | None = None,
        teacher_pre_tanh: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> AnchorActionStepOutput:
        expected_observation_shape = (self.member_capacity, self.observation_dim)
        if (
            observations.ndim != 3
            or observations.shape[1:] != expected_observation_shape
        ):
            raise ValueError("G20R policy observation shape mismatch")
        if active_mask.dtype != torch.bool:
            raise ValueError("G20R policy active mask must be bool")

        raw = self.delayed_residual(observations.detach())
        dtype = raw.dtype
        mask = active_mask.to(dtype).unsqueeze(-1)
        active_count = active_mask.sum(dim=-1).to(dtype).clamp_min(1.0).unsqueeze(-1)
        self._pending_active_mean = (raw * mask).sum(dim=-2) / active_count
        centered = center_residual_over_active_set(raw, active_mask)

        self._anchor_mean_capture = []
        base_output = super().forward_step(
            observations=observations,
            active_mask=active_mask,
            critic_state=critic_state,
            hidden=hidden,
            sampling_noise=sampling_noise,
            teacher_pre_tanh=teacher_pre_tanh,
            deterministic=deterministic,
        )
        self._pending_active_mean = None

        batch = observations.shape[0]
        anchor_means = torch.zeros(
            (self.member_capacity, batch, self.action_dim),
            dtype=dtype,
            device=observations.device,
        )
        if self._anchor_mean_capture:
            visited = torch.stack(self._anchor_mean_capture, dim=0)
            anchor_means[: visited.shape[0]] = visited
        self._anchor_mean_capture = []
        anchor_means = anchor_means.permute(1, 0, 2).contiguous()

        return AnchorActionStepOutput(
            actions=base_output.actions,
            pre_tanh_actions=base_output.pre_tanh_actions,
            token_log_probs=base_output.token_log_probs,
            token_entropies=base_output.token_entropies,
            value=base_output.value,
            next_hidden=base_output.next_hidden,
            prefix_action_sums=base_output.prefix_action_sums,
            likelihood_mask=base_output.likelihood_mask,
            centered_residual=centered,
            anchor_means=anchor_means,
            # Placeholder: this inner policy class has no knowledge of the
            # prefix critic (owned by the wrapper below).  The wrapper's own
            # forward_step overwrites both `value` and `position_value` with
            # the real Q_j-derived numbers via dataclasses.replace.
            position_value=torch.zeros(
                (observations.shape[0], self.member_capacity),
                dtype=dtype,
                device=observations.device,
            ),
        )

    def _action_mean_for_member(
        self,
        *,
        candidate: torch.Tensor,
        prefix_fraction: torch.Tensor,
        observation: torch.Tensor,
    ) -> torch.Tensor:
        anchor = super()._action_mean_for_member(
            candidate=candidate,
            prefix_fraction=prefix_fraction,
            observation=observation,
        )
        self._anchor_mean_capture.append(anchor.detach())
        if self._pending_active_mean is None:
            raise RuntimeError(
                "G20R policy requires forward_step to precompute the active mean"
            )
        raw_member = self.delayed_residual(observation.detach())
        return anchor + (raw_member - self._pending_active_mean)


def _prefix_critic_forward(
    model: Any,
    critic_state: torch.Tensor,
    active_mask: torch.Tensor,
    prefix_through: torch.Tensor,
) -> torch.Tensor:
    """Evaluate ``model.prefix_critic`` on the four-input feature set.

    ``critic_state``, ``active_mask`` and ``prefix_through`` may carry any
    common set of leading batch dimensions (e.g. ``[T,B]`` or ``[K,T,B]``);
    the position axis (size ``capacity``) is always introduced here, never
    supplied by the caller, and ``prefix_through`` never carries information
    about any routing position other than the one it is evaluated at -- it is
    built exclusively from the prefix strictly before that position plus the
    single action at that position.
    """

    dtype = critic_state.dtype
    device = critic_state.device
    capacity = active_mask.shape[-1]
    leading = active_mask.shape[:-1]
    position_onehot = torch.eye(capacity, dtype=dtype, device=device)
    for _ in range(len(leading)):
        position_onehot = position_onehot.unsqueeze(0)
    position_onehot = position_onehot.expand(*leading, capacity, capacity)
    critic_broadcast = critic_state.unsqueeze(-2).expand(
        *leading, capacity, critic_state.shape[-1]
    )
    mask_broadcast = active_mask.to(dtype).unsqueeze(-2).expand(
        *leading, capacity, capacity
    )
    features = torch.cat(
        (critic_broadcast, mask_broadcast, position_onehot, prefix_through), dim=-1
    )
    return model.prefix_critic(features).squeeze(-1)


def _batched_routing_order(
    policy: ContinuousRosterPolicy,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
) -> torch.Tensor:
    """Recompute the deterministic position->member routing order for a full trajectory.

    ``_routing_order`` is a pure function of the current active mask and the
    first three observation coordinates -- no parameters, no randomness, no
    dependence on the residual.  It is inherited unchanged from the untouched
    base policy; batching it over the whole ``[T,B]`` trajectory here is a
    convenience wrapper, not a reimplementation of routing logic.
    """

    time_steps, batch = observations.shape[:2]
    flat_observations = observations.reshape(time_steps * batch, *observations.shape[2:])
    flat_mask = active_mask.reshape(time_steps * batch, active_mask.shape[-1])
    order = policy._routing_order(flat_mask, flat_observations)
    return order.reshape(time_steps, batch, -1)


class FastAnchorActionAdvantagePolicy(nn.Module):
    """Two-phase policy: one immutable fast actor, one delayed centered head.

    The delayed phase's credit rule is a prefix critic ``Q_j`` over the
    executed action, contrasted against an anchor-policy baseline -- not a
    leave-one-out counterfactual over the residual table.
    """

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        member_capacity: int,
        action_dim: int,
        hidden_dim: int = 32,
        current_observation_residual: bool = True,
    ) -> None:
        super().__init__()
        self.member_capacity = int(member_capacity)
        self.critic_state_dim = int(critic_state_dim)
        self.action_dim = int(action_dim)
        self.policy = AnchorActionAdvantageRosterPolicy(
            observation_dim,
            critic_state_dim,
            member_capacity=member_capacity,
            action_dim=action_dim,
            hidden_dim=hidden_dim,
            current_observation_residual=current_observation_residual,
        )
        for parameter in self.policy.critic.parameters():
            parameter.requires_grad_(False)
        prefix_critic_input_dim = (
            self.critic_state_dim
            + self.member_capacity  # active mask
            + self.member_capacity  # routing-position one-hot
            + self.action_dim  # prefix through and including this position
        )
        self.prefix_critic = nn.Sequential(
            nn.Linear(prefix_critic_input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        for parameter in self.prefix_critic.parameters():
            parameter.requires_grad_(False)
        self.immediate_baseline = nn.Sequential(
            nn.Linear(self.critic_state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
        self.phase = "fast"

    @property
    def hidden_dim(self) -> int:
        return self.policy.hidden_dim

    @property
    def log_std(self) -> nn.Parameter:
        return self.policy.log_std

    @property
    def parameter_count(self) -> int:
        return int(sum(parameter.numel() for parameter in self.parameters()))

    def forward_step(self, **arguments: Any) -> AnchorActionStepOutput:
        output = self.policy.forward_step(**arguments)
        critic_state = arguments["critic_state"]
        active_mask = arguments["active_mask"]
        observations = arguments["observations"]
        order = self.policy._routing_order(active_mask, observations)
        position_actions = torch.gather(
            output.actions, 1, order.unsqueeze(-1).expand(-1, -1, self.action_dim)
        )
        prefix_through = output.prefix_action_sums + position_actions
        q_position = _prefix_critic_forward(
            self, critic_state, active_mask, prefix_through
        )
        capacity = active_mask.shape[-1]
        active_count = active_mask.sum(dim=-1)
        position_index = torch.arange(capacity, device=active_mask.device).unsqueeze(0)
        position_valid = position_index < active_count.unsqueeze(-1)
        position_value = torch.where(
            position_valid, q_position, torch.zeros_like(q_position)
        )
        # `value` must stay a single scalar per batch row: it is written into
        # a pre-shaped [horizon, batch] buffer by the untouched, source-shared
        # G17 collector (`continuous_service_roster_proxy_g17.collect_trajectory`).
        # The member/position-resolved Q_j table that actually carries credit
        # lives in `position_value`; `value` is its masked mean over active
        # routing positions, kept only for that external shape contract and
        # for a bit-exactness sanity check in `replay_errors`.
        scalar_value = position_value.sum(dim=-1) / active_count.clamp_min(1).to(
            position_value.dtype
        )
        return replace(output, value=scalar_value, position_value=position_value)

    def immediate_baseline_value(self, critic_states: torch.Tensor) -> torch.Tensor:
        if critic_states.shape[-1] != self.critic_state_dim:
            raise ValueError("G20R immediate baseline critic-state shape mismatch")
        return self.immediate_baseline(critic_states).squeeze(-1)

    def fast_actor_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(
            parameter
            for name, parameter in self.policy.named_parameters()
            if not name.startswith("delayed_residual.")
            and not name.startswith("critic.")
            and parameter.requires_grad
        )

    def residual_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(self.policy.delayed_residual.parameters())

    def critic_parameters(self) -> tuple[nn.Parameter, ...]:
        return tuple(self.prefix_critic.parameters())

    def anchor_state(self) -> dict[str, torch.Tensor]:
        return {
            name: value.detach().cpu().clone()
            for name, value in self.policy.state_dict().items()
            if not name.startswith("delayed_residual.")
        }

    def begin_delayed_phase(self) -> None:
        if self.phase != "fast":
            raise RuntimeError("G20R delayed phase may begin exactly once")
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G20R residual must be exact zero at phase change")
        for parameter in self.policy.parameters():
            parameter.requires_grad_(False)
        for parameter in self.immediate_baseline.parameters():
            parameter.requires_grad_(False)
        for parameter in self.policy.delayed_residual.parameters():
            parameter.requires_grad_(True)
        for parameter in self.prefix_critic.parameters():
            parameter.requires_grad_(True)
        self.phase = "delayed"

    def residual_maximum_absolute_value(self) -> float:
        return max(
            float(parameter.detach().abs().max().cpu())
            for parameter in self.policy.delayed_residual.parameters()
        )

    def residual_output_layer_maximum_absolute_value(self) -> float:
        final = self.policy.delayed_residual[-1]
        assert isinstance(final, nn.Linear)
        return max(
            float(parameter.detach().abs().max().cpu())
            for parameter in final.parameters()
        )


@dataclass
class AnchorActionTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    critic_states: torch.Tensor
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    old_immediate_baselines: torch.Tensor
    old_baseline: torch.Tensor
    old_prefix_advantage: torch.Tensor
    old_anchor_spread: torch.Tensor
    rewards: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    outcomes: tuple[Any, ...]
    ledgers: tuple[Any, ...]

    @property
    def active_token_count(self) -> int:
        return int(self.active_mask.sum().item())


@dataclass
class AnchorActionReplay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    value: torch.Tensor
    position_value: torch.Tensor
    immediate_baselines: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor
    centered_residual: torch.Tensor
    anchor_means: torch.Tensor


def replay_trajectory(
    model: FastAnchorActionAdvantagePolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> AnchorActionReplay:
    hidden = trajectory.hidden_before[0].to(device)
    outputs: list[AnchorActionStepOutput] = []
    for time in range(trajectory.rewards.shape[0]):
        output = model.forward_step(
            observations=trajectory.observations[time].to(device),
            active_mask=trajectory.active_mask[time].to(device),
            critic_state=trajectory.critic_states[time].to(device),
            hidden=hidden,
            teacher_pre_tanh=trajectory.pre_tanh_actions[time].to(device),
        )
        outputs.append(output)
        hidden = output.next_hidden
    immediate = model.immediate_baseline_value(trajectory.critic_states.to(device))
    return AnchorActionReplay(
        log_probs=torch.stack([row.token_log_probs for row in outputs]),
        entropies=torch.stack([row.token_entropies for row in outputs]),
        value=torch.stack([row.value for row in outputs]),
        position_value=torch.stack([row.position_value for row in outputs]),
        immediate_baselines=immediate,
        hidden_after=torch.stack([row.next_hidden for row in outputs]),
        prefix_action_sums=torch.stack([row.prefix_action_sums for row in outputs]),
        active_mask=trajectory.active_mask.to(device),
        centered_residual=torch.stack([row.centered_residual for row in outputs]),
        anchor_means=torch.stack([row.anchor_means for row in outputs]),
    )


def replay_errors(
    replay: AnchorActionReplay, trajectory: AnchorActionTrajectory
) -> dict[str, float]:
    device = replay.log_probs.device
    mask = replay.active_mask
    old_log_probs = trajectory.old_log_probs.to(device)
    return {
        "logp_max_error": float(
            torch.abs(replay.log_probs - old_log_probs)[mask].max().detach().cpu()
        ),
        "joint_logp_max_error": float(
            torch.abs(
                torch.where(mask, replay.log_probs - old_log_probs, 0.0).sum(dim=-1)
            )
            .max()
            .detach()
            .cpu()
        ),
        "value_max_error": float(
            torch.abs(replay.position_value - trajectory.old_values.to(device))
            .max()
            .detach()
            .cpu()
        ),
        "immediate_baseline_max_error": float(
            torch.abs(
                replay.immediate_baselines
                - trajectory.old_immediate_baselines.to(device)
            )
            .max()
            .detach()
            .cpu()
        ),
        "hidden_max_error": float(
            torch.abs(replay.hidden_after - trajectory.hidden_after.to(device))
            .max()
            .detach()
            .cpu()
        ),
        "prefix_max_error": float(
            torch.abs(
                replay.prefix_action_sums - trajectory.prefix_action_sums.to(device)
            )
            .max()
            .detach()
            .cpu()
        ),
        "inactive_logp_max_abs": float(
            torch.where(mask, 0.0, replay.log_probs).abs().max().detach().cpu()
        ),
    }


def _factual_prefix_through(
    model: FastAnchorActionAdvantagePolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> torch.Tensor:
    """The collection-time-constant action-prefix ``Q_j`` regresses against.

    Built exclusively from plain (already-detached) trajectory data -- never
    from a live forward pass through the residual head -- so the ``Q_j``
    regression is structurally detached from the residual head: there is no
    autograd path from this tensor back to any policy parameter.
    """

    order = _batched_routing_order(
        model.policy, trajectory.observations.to(device), trajectory.active_mask.to(device)
    )
    action_dim = trajectory.actions.shape[-1]
    position_actions = torch.gather(
        trajectory.actions.to(device).detach(),
        -2,
        order.unsqueeze(-1).expand(*order.shape, action_dim),
    )
    return trajectory.prefix_action_sums.to(device).detach() + position_actions


def prefix_critic_values(
    model: FastAnchorActionAdvantagePolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> torch.Tensor:
    """``Q_j`` evaluated at the factual (collection-time) action, position-indexed."""

    prefix_through = _factual_prefix_through(model, trajectory, device=device)
    return _prefix_critic_forward(
        model,
        trajectory.critic_states.to(device).detach(),
        trajectory.active_mask.to(device),
        prefix_through,
    )


def attach_prefix_credit(
    model: FastAnchorActionAdvantagePolicy,
    trajectory: Any,
    *,
    device: torch.device,
    baseline_seed: int,
    k: int = BASELINE_SAMPLES_K,
) -> AnchorActionTrajectory:
    """Compute and freeze this collection's member-resolved advantage.

    ``A_slow[j,t] = Q_j(h_j, a_j) - b_j(h_j)``, where ``b_j`` is the mean of
    ``Q_j`` over ``k`` actions resampled from the frozen anchor policy at the
    same decision history.  Held fixed across this update's PPO passes,
    mirroring how G19/G20 fixed their ``old_*`` fields.  The anchor-baseline
    sampling draws from a dedicated ``torch.Generator`` seeded by
    ``baseline_seed`` so it never perturbs any other RNG stream (environment
    action sampling, teacher-forced replay) and is independently reproducible.
    """

    with torch.no_grad():
        immediate = model.immediate_baseline_value(
            trajectory.critic_states.to(device)
        )
        replay = replay_trajectory(model, trajectory, device=device)

        std = torch.exp(model.log_std.clamp(-5.0, 2.0)).detach()
        generator = torch.Generator()
        generator.manual_seed(int(baseline_seed))
        anchor_means = replay.anchor_means.detach()
        prefix_before = trajectory.prefix_action_sums.to(device).detach()
        samples = int(k)
        if samples <= 0:
            raise ValueError("G20R baseline sample count must be positive")
        eps = torch.randn(
            (samples,) + anchor_means.shape, generator=generator, dtype=anchor_means.dtype
        )
        raw_samples = anchor_means.unsqueeze(0) + std * eps
        action_samples = torch.tanh(raw_samples)
        prefix_anchor_samples = prefix_before.unsqueeze(0) + action_samples

        critic_state_k = (
            trajectory.critic_states.to(device)
            .detach()
            .unsqueeze(0)
            .expand(samples, *trajectory.critic_states.shape)
        )
        active_mask_k = replay.active_mask.unsqueeze(0).expand(
            samples, *replay.active_mask.shape
        )
        q_anchor_samples = _prefix_critic_forward(
            model, critic_state_k, active_mask_k, prefix_anchor_samples
        )
        baseline = q_anchor_samples.mean(dim=0)
        spread = q_anchor_samples.std(dim=0, unbiased=False)

        capacity = replay.active_mask.shape[-1]
        active_count = replay.active_mask.sum(dim=-1)
        position_index = torch.arange(capacity, device=device).view(1, 1, capacity)
        position_valid = position_index < active_count.unsqueeze(-1)

        advantage_position = torch.where(
            position_valid, replay.position_value - baseline, torch.zeros_like(baseline)
        )
        order = _batched_routing_order(
            model.policy, trajectory.observations.to(device), replay.active_mask
        )
        member_advantage = torch.zeros_like(advantage_position)
        member_advantage.scatter_(-1, order, advantage_position)

        masked_baseline = torch.where(
            position_valid, baseline, torch.zeros_like(baseline)
        )
        masked_spread = torch.where(
            position_valid, spread, torch.zeros_like(spread)
        )

    return AnchorActionTrajectory(
        observations=trajectory.observations,
        active_mask=trajectory.active_mask,
        critic_states=trajectory.critic_states,
        actions=trajectory.actions,
        pre_tanh_actions=trajectory.pre_tanh_actions,
        old_log_probs=trajectory.old_log_probs,
        old_values=replay.position_value.detach().cpu(),
        old_immediate_baselines=immediate.detach().cpu(),
        old_baseline=masked_baseline.detach().cpu(),
        old_prefix_advantage=member_advantage.detach().cpu(),
        old_anchor_spread=masked_spread.detach().cpu(),
        rewards=trajectory.rewards,
        hidden_before=trajectory.hidden_before,
        hidden_after=trajectory.hidden_after,
        prefix_action_sums=trajectory.prefix_action_sums,
        outcomes=tuple(trajectory.outcomes),
        ledgers=tuple(trajectory.ledgers),
    )


def normalize_team_advantage(advantage: torch.Tensor) -> torch.Tensor:
    if advantage.ndim != 2 or not bool(torch.isfinite(advantage).all()):
        raise ValueError("G20R team advantage must be finite [time,batch]")
    return (advantage - advantage.mean()) / (advantage.std(unbiased=False) + 1e-8)


def normalize_masked_advantage(
    advantage: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    if advantage.shape != active_mask.shape:
        raise ValueError("G20R masked advantage/active-mask shape mismatch")
    if not bool(torch.isfinite(advantage).all()):
        raise ValueError("G20R masked advantage must be finite")
    active = active_mask.to(advantage.dtype)
    count = active.sum().clamp_min(1.0)
    mean = (advantage * active).sum() / count
    variance = (torch.square(advantage - mean) * active).sum() / count
    std = torch.sqrt(variance)
    normalized = (advantage - mean) / (std + 1e-8)
    return torch.where(active_mask, normalized, torch.zeros_like(normalized))


def _team_policy_loss(
    replay: AnchorActionReplay,
    trajectory: AnchorActionTrajectory,
    advantage: torch.Tensor,
) -> torch.Tensor:
    device = replay.log_probs.device
    mask = replay.active_mask
    ratio = torch.exp(replay.log_probs - trajectory.old_log_probs.to(device))
    expanded = normalize_team_advantage(advantage.to(device)).unsqueeze(-1)
    surrogate = torch.minimum(
        ratio * expanded,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * expanded,
    )
    active_count = mask.sum(dim=-1).clamp_min(1)
    return -(
        torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
    ).mean()


def _member_policy_loss(
    replay: AnchorActionReplay,
    trajectory: AnchorActionTrajectory,
    advantage: torch.Tensor,
) -> torch.Tensor:
    device = replay.log_probs.device
    mask = replay.active_mask
    ratio = torch.exp(replay.log_probs - trajectory.old_log_probs.to(device))
    normalized = normalize_masked_advantage(advantage.to(device), mask)
    surrogate = torch.minimum(
        ratio * normalized,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * normalized,
    )
    active_count = mask.sum().clamp_min(1)
    return -(torch.where(mask, surrogate, 0.0).sum() / active_count)


def _discounted_returns(
    rewards: torch.Tensor,
    terminals: torch.Tensor,
    bootstrap: torch.Tensor,
    *,
    gamma: float,
) -> torch.Tensor:
    targets = torch.empty_like(rewards)
    running = bootstrap.detach()
    for time in range(rewards.shape[0] - 1, -1, -1):
        running = rewards[time].detach() + float(gamma) * (
            ~terminals[time]
        ).to(rewards.dtype) * running
        targets[time] = running
    return targets


def optimize_fast_update(
    model: FastAnchorActionAdvantagePolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: AnchorActionTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
) -> dict[str, float]:
    if model.phase != "fast":
        raise RuntimeError("G20R fast update requires fast phase")
    with torch.no_grad():
        errors = replay_errors(
            replay_trajectory(model, trajectory, device=device), trajectory
        )
    advantage = (
        trajectory.rewards.to(device) - trajectory.old_immediate_baselines.to(device)
    ).detach()
    trainable = model.fast_actor_parameters() + tuple(
        model.immediate_baseline.parameters()
    )
    totals = {
        name: 0.0
        for name in (
            "fast_policy_loss",
            "immediate_baseline_loss",
            "entropy",
            "gradient_norm",
        )
    }
    finite = True
    model.train()
    for _ in range(int(ppo_passes)):
        replay = replay_trajectory(model, trajectory, device=device)
        policy_loss = _team_policy_loss(replay, trajectory, advantage)
        immediate_loss = F.mse_loss(
            replay.immediate_baselines, trajectory.rewards.to(device).detach()
        )
        active_count = replay.active_mask.sum(dim=-1).clamp_min(1)
        entropy = (
            torch.where(replay.active_mask, replay.entropies, 0.0).sum(dim=-1)
            / active_count
        ).mean()
        loss = (
            policy_loss
            + VALUE_COEFFICIENT * immediate_loss
            - ENTROPY_COEFFICIENT * entropy
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(trainable, GRADIENT_CLIP)
        finite = finite and bool(torch.isfinite(loss)) and bool(
            torch.isfinite(gradient_norm)
        )
        optimizer.step()
        totals["fast_policy_loss"] += float(policy_loss.detach().cpu())
        totals["immediate_baseline_loss"] += float(immediate_loss.detach().cpu())
        totals["entropy"] += float(entropy.detach().cpu())
        totals["gradient_norm"] += float(gradient_norm.detach().cpu())
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(ppo_passes)
    return totals


def optimize_delayed_update(
    model: FastAnchorActionAdvantagePolicy,
    residual_optimizer: torch.optim.Optimizer,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchorActionTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    if model.phase != "delayed":
        raise RuntimeError("G20R delayed update requires delayed phase")
    terminals = torch.zeros_like(
        trajectory.rewards, dtype=torch.bool, device=device
    )
    terminals[-1] = True
    bootstrap = torch.zeros(
        trajectory.rewards.shape[1], dtype=trajectory.rewards.dtype, device=device
    )
    slow_return_targets = _discounted_returns(
        trajectory.rewards.to(device), terminals, bootstrap, gamma=float(gamma)
    )
    advantage = trajectory.old_prefix_advantage.to(device).detach()
    with torch.no_grad():
        errors = replay_errors(
            replay_trajectory(model, trajectory, device=device), trajectory
        )
    residual_parameters = model.residual_parameters()
    critic_parameters = model.critic_parameters()
    totals = {
        name: 0.0
        for name in (
            "delayed_policy_loss",
            "slow_value_loss",
            "entropy",
            "residual_gradient_norm",
            "critic_gradient_norm",
        )
    }
    finite = True
    capacity = trajectory.active_mask.shape[-1]
    active_count = trajectory.active_mask.sum(dim=-1).to(device)
    position_index = torch.arange(capacity, device=device).view(1, 1, capacity)
    position_valid = position_index < active_count.unsqueeze(-1)
    position_count = position_valid.sum(dim=-1).clamp_min(1)
    old_q = trajectory.old_values.to(device)
    model.train()
    for _ in range(int(ppo_passes)):
        replay = replay_trajectory(model, trajectory, device=device)
        policy_loss = _member_policy_loss(replay, trajectory, advantage)
        active_count_member = replay.active_mask.sum(dim=-1).clamp_min(1)
        entropy = (
            torch.where(replay.active_mask, replay.entropies, 0.0).sum(dim=-1)
            / active_count_member
        ).mean()
        actor_loss = policy_loss
        residual_optimizer.zero_grad(set_to_none=True)
        actor_loss.backward()
        residual_gradient_norm = torch.nn.utils.clip_grad_norm_(
            residual_parameters, GRADIENT_CLIP
        )
        residual_optimizer.step()

        q_now = prefix_critic_values(model, trajectory, device=device)
        target_broadcast = slow_return_targets.unsqueeze(-1).expand_as(q_now)
        clipped_q = old_q + torch.clamp(q_now - old_q, -VALUE_CLIP, VALUE_CLIP)
        per_position_loss = torch.maximum(
            torch.square(q_now - target_broadcast),
            torch.square(clipped_q - target_broadcast),
        )
        slow_value_loss = (
            torch.where(
                position_valid, per_position_loss, torch.zeros_like(per_position_loss)
            ).sum(dim=-1)
            / position_count
        ).mean()
        critic_optimizer.zero_grad(set_to_none=True)
        slow_value_loss.backward()
        critic_gradient_norm = torch.nn.utils.clip_grad_norm_(
            critic_parameters, GRADIENT_CLIP
        )
        critic_optimizer.step()

        finite = finite and all(
            bool(torch.isfinite(value))
            for value in (
                actor_loss,
                slow_value_loss,
                residual_gradient_norm,
                critic_gradient_norm,
            )
        )
        totals["delayed_policy_loss"] += float(policy_loss.detach().cpu())
        totals["slow_value_loss"] += float(slow_value_loss.detach().cpu())
        totals["entropy"] += float(entropy.detach().cpu())
        totals["residual_gradient_norm"] += float(
            residual_gradient_norm.detach().cpu()
        )
        totals["critic_gradient_norm"] += float(
            critic_gradient_norm.detach().cpu()
        )
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(2 * ppo_passes)
    return totals


def maximum_state_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    if left.keys() != right.keys():
        return float("inf")
    return max(
        float(torch.max(torch.abs(left[name] - right[name])).item())
        for name in left
    )
