"""Anchor-policy conditional action-advantage credit rule, re-registered (G20R2).

This module implements the frozen contract in
``docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2.md``. It supersedes
``anchor_action_advantage_g20r.py``, which stays in the tree unmodified as the
evidence that produced the re-registration ruling
(``docs/external-review/rounds/20260724_g20r_identification_floor/``). Nothing in
this module imports from that retired module; the shared pieces (active-set
centering, exact-zero anchor initialization, the frozen fast path, the Adam
parameter groups) are copied here exactly as G20R itself copied them from G20,
because a retired module is frozen evidence and is not extended.

Two things change relative to G20R:

1. ``Q_j``'s input contract is rebuilt to design section 1: the full masked
   per-member observation table and detached pre-action recurrent state (both
   in anonymous routing order), active/lifecycle state, routing position, the
   *full ordered* action prefix paired with its member context (not a sum),
   and the focal action -- never an action at a later routing position, next
   state, future reward, or unannounced future membership event.
2. The delayed phase is split into two stages: a critic-only ``qualification``
   phase at the exact fast anchor (residual parameters stay frozen and their
   output layer stays exactly zero throughout), followed by the ``delayed``
   phase, which may begin only once the caller has established that Stage A
   and Stage B (implemented below as ``stage_a_source_effect``,
   ``stage_b1_contrast_alignment``, ``stage_b1_recalibrated_r2``, and
   ``stage_b2_gradient_alignment``) have passed. That precondition is enforced
   structurally by ``FastAnchorActionAdvantagePolicy.begin_delayed_phase``,
   which raises unless the caller affirms ``stage_b_passed=True``.

This module stays neutral to the calling environment/source, exactly like its
G17/G18/G19/G20/G20R counterparts: it owns the policy subclass, ``Q_j``, the
anchor-baseline advantage, the two update rules, and the generic (source-
independent) Stage A/B1/B2 statistical estimators. Source-specific paired-
replay collection (resetting an environment from a ledger and replaying a
prefix to realize the oracle contrast ``A*(h,a)``) lives in
``scripts/screen_anchor_action_advantage_g20r2.py``, which is the only caller
allowed to know about G17/G18 environment mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy


PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50

# Design section 11: "baseline_samples_K=8" is the only frozen identification
# constant with an explicit numeric value.
BASELINE_SAMPLES_K = 8

# Design section 2 defines `epsilon_audit` as "only the numerical /
# paired-rollout resolution floor" -- explicitly *not* an effect-size
# threshold. Section 11 ("`epsilon_audit` is not yet registered -- the screen
# is withheld") freezes no module default for it and requires that a missing
# registration fail closed rather than silently substitute one: `epsilon_audit`
# is a measured property of the audit estimator (via the registered
# replicate-split null calibration, `scripts/calibrate_epsilon_audit_g20r2.py`),
# never a chosen constant, so `stage_a_source_effect` below takes it as a
# required keyword argument with no default -- omitting it is a `TypeError`.

# Numeric tolerance for the P2 authority check's literal "|g*_res| = 0" test
# (design section 2). Floating point can never produce an exact zero from a
# nonzero-but-tiny true value and vice versa, so a tolerance is required; this
# one is deliberately much tighter than any registered `epsilon_audit` value
# because it is testing exact cancellation (centering orthogonality), not
# measurement resolution.
P2_AUTHORITY_ZERO_TOLERANCE = 1e-8


def center_residual_over_active_set(
    raw: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    """Exactly center an observation-only residual table over the active set.

    Member ``i`` receives ``f(o_i) - (1/N) * sum_{j active} f(o_j)``.  The
    result therefore sums to zero over the active set per action coordinate
    per batch row, and inactive rows receive exactly zero.  Copied unchanged
    from the retired ``anchor_action_advantage_g20r.py`` (which itself copied
    it from the retired ``centered_residual_g20.py``); this repair changes
    only what carries credit, not how the residual is centered.
    """

    if raw.shape[:-1] != active_mask.shape:
        raise ValueError(
            "G20R2 centering shape mismatch between residual table and active mask"
        )
    if active_mask.dtype != torch.bool:
        raise ValueError("G20R2 centering active mask must be bool")
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

    Identical construction to G20R's policy: an observation-only delayed
    head, active-set centering, and a side-channel capture of each routed
    member's *anchor* mean (the base policy's mean before the residual is
    added) so the credit rule below can resample ``K`` actions from the
    frozen anchor distribution at the same decision history. This class is
    unchanged from G20R by design -- the re-registered contract changes what
    ``Q_j`` sees, not the fast/anchor/centering mechanics.
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
            raise ValueError("G20R2 policy observation shape mismatch")
        if active_mask.dtype != torch.bool:
            raise ValueError("G20R2 policy active mask must be bool")

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
            # prefix critic (owned by the wrapper below). The wrapper's own
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
                "G20R2 policy requires forward_step to precompute the active mean"
            )
        raw_member = self.delayed_residual(observation.detach())
        return anchor + (raw_member - self._pending_active_mean)


def _batched_routing_order(
    policy: ContinuousRosterPolicy,
    observations: torch.Tensor,
    active_mask: torch.Tensor,
) -> torch.Tensor:
    """Recompute the deterministic position->member routing order for a full trajectory.

    ``_routing_order`` is a pure function of the current active mask and the
    first three observation coordinates -- no parameters, no randomness, no
    dependence on the residual. It is inherited unchanged from the untouched
    base policy; batching it over the whole ``[T,B]`` trajectory here is a
    convenience wrapper, not a reimplementation of routing logic.
    """

    time_steps, batch = observations.shape[:2]
    flat_observations = observations.reshape(time_steps * batch, *observations.shape[2:])
    flat_mask = active_mask.reshape(time_steps * batch, active_mask.shape[-1])
    order = policy._routing_order(flat_mask, flat_observations)
    return order.reshape(time_steps, batch, -1)


def _gather_by_order(table: torch.Tensor, order: torch.Tensor) -> torch.Tensor:
    """Reindex a member/slot-indexed table into routing-position order.

    ``table`` has shape ``[..., capacity, feature]`` indexed by lifecycle
    slot; ``order[..., position]`` names the slot occupying each routing
    position. Returns the same shape, reindexed so row ``position`` holds
    the slot that occupies that routing position -- i.e. ``X_t[sigma_t]``.
    """

    index = order.unsqueeze(-1).expand(*order.shape, table.shape[-1])
    return torch.gather(table, -2, index)


def _qj_forward(
    model: Any,
    *,
    critic_state: torch.Tensor,
    active_mask: torch.Tensor,
    observations: torch.Tensor,
    hidden_before: torch.Tensor,
    order: torch.Tensor,
    prefix_actions: torch.Tensor,
    focal_actions: torch.Tensor,
) -> torch.Tensor:
    """Evaluate ``model.prefix_critic`` on the design-section-1 input contract.

    All tensors may carry any common set of leading batch dimensions (e.g.
    ``[T,B]`` or ``[K,T,B]``). ``order[..., position]`` is the routing-order
    permutation (position -> lifecycle slot) for that leading index.

    ``prefix_actions`` and ``focal_actions`` are both position-indexed
    (``[..., capacity, action_dim]``, row ``k`` = the action executed by
    whichever member occupies routing position ``k``) but serve two
    deliberately distinct roles so that a counterfactual probe at position
    ``j`` cannot leak into position ``j``'s own *history*:

    * ``prefix_actions`` supplies the *actual* (factual) prefix -- row ``k``
      is read only for query positions ``j > k``, building ``A_<j,t``. It is
      held fixed to the collection-time factual trajectory even when
      resampling counterfactual actions for the anchor baseline, because the
      history a position actually saw did not change.
    * ``focal_actions`` supplies ``a_j,t`` -- the (possibly counterfactual,
      e.g. anchor-resampled) action being queried *at* each position ``j``.

    Returns ``Q_j`` for every routing position at once: shape
    ``[..., capacity]``.

    Fail-closed by construction against every prohibited input in design
    section 1: ``prefix_actions`` contributes to query ``j`` only through a
    strict lower-triangular mask (``k < j``), so no action at a later
    routing position ever reaches ``Q_j``; there is no next-state, future-
    reward, membership-event-beyond-now, or ledger-identity argument in this
    signature at all; and no observation coordinate is semantically
    interpreted here (the raw table is passed through unchanged).
    """

    leading = active_mask.shape[:-1]
    capacity = active_mask.shape[-1]
    dtype = critic_state.dtype
    device = critic_state.device
    observation_dim = observations.shape[-1]
    hidden_dim = hidden_before.shape[-1]
    action_dim = prefix_actions.shape[-1]

    # X_t[sigma_t]: full masked per-member observation table, routing order.
    x_ordered = _gather_by_order(observations, order)
    mask_ordered = torch.gather(active_mask, -1, order)
    mask_ordered_f = mask_ordered.to(dtype)
    x_masked = x_ordered * mask_ordered_f.unsqueeze(-1)
    x_flat = x_masked.reshape(*leading, capacity * observation_dim)

    # R_t[sigma_t]: detached pre-action recurrent state, routing order.
    r_ordered = _gather_by_order(hidden_before.detach(), order)
    r_masked = r_ordered * mask_ordered_f.unsqueeze(-1)
    r_flat = r_masked.reshape(*leading, capacity * hidden_dim)

    # M_t[sigma_t]: active/lifecycle state available at action time. The
    # only such state exposed to this module without touching either
    # (out-of-scope) source module is the active mask itself -- age,
    # previous-effort, rotating/spike-phase and similar lifecycle fields are
    # already columns of X_t (both G17 and G18 include them in their
    # per-member observation), so this is not an omission relative to what
    # is available at decision time, only a non-duplication of it.
    m_flat = mask_ordered_f

    # j: routing-position one-hot.
    position_onehot = torch.eye(capacity, dtype=dtype, device=device)
    for _ in range(len(leading)):
        position_onehot = position_onehot.unsqueeze(0)
    position_onehot = position_onehot.expand(*leading, capacity, capacity)

    # A_<j,t[sigma_t]: full ordered prefix table, member-context-paired via
    # shared routing-position indexing with X_t[sigma_t]/R_t[sigma_t] above
    # -- not a sum. strict_lower[j, k] = 1 iff k < j.
    strict_lower = torch.tril(
        torch.ones(capacity, capacity, dtype=dtype, device=device), diagonal=-1
    )
    for _ in range(len(leading)):
        strict_lower = strict_lower.unsqueeze(0)
    strict_lower = strict_lower.expand(*leading, capacity, capacity)
    prefix_table = strict_lower.unsqueeze(-1) * prefix_actions.unsqueeze(-3)
    prefix_flat = prefix_table.reshape(*leading, capacity, capacity * action_dim)

    critic_broadcast = critic_state.unsqueeze(-2).expand(
        *leading, capacity, critic_state.shape[-1]
    )
    x_broadcast = x_flat.unsqueeze(-2).expand(*leading, capacity, x_flat.shape[-1])
    r_broadcast = r_flat.unsqueeze(-2).expand(*leading, capacity, r_flat.shape[-1])
    m_broadcast = m_flat.unsqueeze(-2).expand(*leading, capacity, capacity)

    features = torch.cat(
        (
            critic_broadcast,
            x_broadcast,
            r_broadcast,
            m_broadcast,
            position_onehot,
            prefix_flat,
            focal_actions,
        ),
        dim=-1,
    )
    return model.prefix_critic(features).squeeze(-1)


def prefix_critic_input_dim(
    *,
    critic_state_dim: int,
    member_capacity: int,
    observation_dim: int,
    hidden_dim: int,
    action_dim: int,
) -> int:
    return (
        critic_state_dim
        + member_capacity * observation_dim  # X_t[sigma_t]
        + member_capacity * hidden_dim  # R_t[sigma_t]
        + member_capacity  # M_t[sigma_t] (active mask)
        + member_capacity  # routing-position one-hot j
        + member_capacity * action_dim  # A_<j,t[sigma_t]
        + action_dim  # a_j,t
    )


class FastAnchorActionAdvantagePolicy(nn.Module):
    """Three-phase policy: one immutable fast actor, a critic-only qualification
    phase, and a delayed centered residual head.

    Phases, in order: ``"fast"`` (unchanged G17-style fast training) ->
    ``"qualification"`` (only ``prefix_critic`` trains, at the exact fast
    anchor; residual stays frozen and its output layer must stay exactly
    zero throughout, design section 6) -> ``"delayed"`` (residual unfreezes,
    only reachable by affirming ``stage_b_passed=True``).
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
        self.observation_dim = int(observation_dim)
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
        input_dim = prefix_critic_input_dim(
            critic_state_dim=self.critic_state_dim,
            member_capacity=self.member_capacity,
            observation_dim=self.observation_dim,
            hidden_dim=self.policy.hidden_dim,
            action_dim=self.action_dim,
        )
        self.prefix_critic = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
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
        hidden_before = arguments["hidden"].detach()
        order = self.policy._routing_order(active_mask, observations)
        position_actions = torch.gather(
            output.actions, 1, order.unsqueeze(-1).expand(-1, -1, self.action_dim)
        )
        q_position = _qj_forward(
            self,
            critic_state=critic_state,
            active_mask=active_mask,
            observations=observations,
            hidden_before=hidden_before,
            order=order,
            prefix_actions=position_actions,
            focal_actions=position_actions,
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
            raise ValueError("G20R2 immediate baseline critic-state shape mismatch")
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

    def begin_qualification_phase(self) -> None:
        """Open the critic-only qualification phase at the exact fast anchor.

        Design section 6: the delayed phase "opens with a critic-only
        qualification phase at the exact fast anchor". Every fast-path and
        immediate-baseline parameter freezes here (same freeze set G20R
        applied at `begin_delayed_phase`); only `prefix_critic` unfreezes.
        The residual stays exactly at its frozen zero -- this method does not
        touch `delayed_residual`'s `requires_grad` at all.
        """

        if self.phase != "fast":
            raise RuntimeError(
                "G20R2 qualification phase begins exactly once, from the fast phase"
            )
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G20R2 residual must be exact zero at phase change")
        for parameter in self.policy.parameters():
            parameter.requires_grad_(False)
        for parameter in self.immediate_baseline.parameters():
            parameter.requires_grad_(False)
        for parameter in self.prefix_critic.parameters():
            parameter.requires_grad_(True)
        self.phase = "qualification"

    def begin_delayed_phase(self, *, stage_b_passed: bool) -> None:
        """Open the delayed (residual-training) phase.

        Design section 6, mandatory: "No residual-actor update may occur
        until the critic has passed out-of-sample Stage B qualification
        under the policy snapshot whose actions it will credit." This is
        enforced structurally, not just documented: the residual head's
        `requires_grad` only ever flips True here, and only when the caller
        affirms `stage_b_passed=True` -- there is no other path in this
        class that unfreezes `delayed_residual`.
        """

        if self.phase != "qualification":
            raise RuntimeError(
                "G20R2 delayed phase requires the qualification phase to run first"
            )
        if not stage_b_passed:
            raise RuntimeError(
                "G20R2 forbids a residual-actor update before Stage B "
                "qualification passes under the credited policy snapshot "
                "(design section 6)"
            )
        if self.residual_output_layer_maximum_absolute_value() != 0.0:
            raise RuntimeError("G20R2 residual must be exact zero at phase change")
        for parameter in self.policy.delayed_residual.parameters():
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


def _factual_position_actions(
    model: FastAnchorActionAdvantagePolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    """The collection-time-constant, position-indexed factual action table.

    Built exclusively from plain (already-detached) trajectory data -- never
    from a live forward pass through the residual head -- so the ``Q_j``
    regression is structurally detached from the residual head: there is no
    autograd path from this tensor back to any policy parameter. Returns
    ``(order, position_actions)``.
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
    return order, position_actions


def prefix_critic_values(
    model: FastAnchorActionAdvantagePolicy,
    trajectory: Any,
    *,
    device: torch.device,
) -> torch.Tensor:
    """``Q_j`` evaluated at the factual (collection-time) action, position-indexed."""

    order, position_actions = _factual_position_actions(model, trajectory, device=device)
    return _qj_forward(
        model,
        critic_state=trajectory.critic_states.to(device).detach(),
        active_mask=trajectory.active_mask.to(device),
        observations=trajectory.observations.to(device).detach(),
        hidden_before=trajectory.hidden_before.to(device).detach(),
        order=order,
        prefix_actions=position_actions,
        focal_actions=position_actions,
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
    same decision history, with the factual prefix (positions ``< j``) held
    fixed to what actually happened -- only the queried position's own action
    is counterfactual. Held fixed across this update's PPO passes, mirroring
    how G19/G20/G20R fixed their ``old_*`` fields. The anchor-baseline
    sampling draws from a dedicated ``torch.Generator`` seeded by
    ``baseline_seed`` so it never perturbs any other RNG stream (environment
    action sampling, teacher-forced replay) and is independently reproducible.

    Used for both the qualification split (``D_fit``, whose caller ignores
    the advantage/baseline fields and reads only ``old_values``) and the
    credit split (``D_credit``, which uses the advantage to drive the
    residual actor) -- the baseline is cheap enough (``k=8``) that a single
    code path for both is simpler and no less correct than special-casing
    qualification to skip it.
    """

    with torch.no_grad():
        immediate = model.immediate_baseline_value(
            trajectory.critic_states.to(device)
        )
        replay = replay_trajectory(model, trajectory, device=device)
        order, factual_position_actions = _factual_position_actions(
            model, trajectory, device=device
        )

        std = torch.exp(model.log_std.clamp(-5.0, 2.0)).detach()
        generator = torch.Generator()
        generator.manual_seed(int(baseline_seed))
        anchor_means = replay.anchor_means.detach()
        samples = int(k)
        if samples <= 0:
            raise ValueError("G20R2 baseline sample count must be positive")
        eps = torch.randn(
            (samples,) + anchor_means.shape, generator=generator, dtype=anchor_means.dtype
        )
        raw_samples = anchor_means.unsqueeze(0) + std * eps
        action_samples = torch.tanh(raw_samples)

        critic_state_k = (
            trajectory.critic_states.to(device)
            .detach()
            .unsqueeze(0)
            .expand(samples, *trajectory.critic_states.shape)
        )
        active_mask_k = replay.active_mask.unsqueeze(0).expand(
            samples, *replay.active_mask.shape
        )
        observations_k = (
            trajectory.observations.to(device)
            .detach()
            .unsqueeze(0)
            .expand(samples, *trajectory.observations.shape)
        )
        hidden_before_k = (
            trajectory.hidden_before.to(device)
            .detach()
            .unsqueeze(0)
            .expand(samples, *trajectory.hidden_before.shape)
        )
        order_k = order.unsqueeze(0).expand(samples, *order.shape)
        prefix_actions_k = factual_position_actions.unsqueeze(0).expand(
            samples, *factual_position_actions.shape
        )
        q_anchor_samples = _qj_forward(
            model,
            critic_state=critic_state_k,
            active_mask=active_mask_k,
            observations=observations_k,
            hidden_before=hidden_before_k,
            order=order_k,
            prefix_actions=prefix_actions_k,
            focal_actions=action_samples,
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
        raise ValueError("G20R2 team advantage must be finite [time,batch]")
    return (advantage - advantage.mean()) / (advantage.std(unbiased=False) + 1e-8)


def normalize_masked_advantage(
    advantage: torch.Tensor, active_mask: torch.Tensor
) -> torch.Tensor:
    if advantage.shape != active_mask.shape:
        raise ValueError("G20R2 masked advantage/active-mask shape mismatch")
    if not bool(torch.isfinite(advantage).all()):
        raise ValueError("G20R2 masked advantage must be finite")
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
        raise RuntimeError("G20R2 fast update requires fast phase")
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


def _slow_value_loss(
    model: FastAnchorActionAdvantagePolicy,
    trajectory: AnchorActionTrajectory,
    *,
    device: torch.device,
    gamma: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Shared Q_j regression loss used by both qualification and delayed updates."""

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
    capacity = trajectory.active_mask.shape[-1]
    active_count = trajectory.active_mask.sum(dim=-1).to(device)
    position_index = torch.arange(capacity, device=device).view(1, 1, capacity)
    position_valid = position_index < active_count.unsqueeze(-1)
    position_count = position_valid.sum(dim=-1).clamp_min(1)
    old_q = trajectory.old_values.to(device)

    q_now = prefix_critic_values(model, trajectory, device=device)
    target_broadcast = slow_return_targets.unsqueeze(-1).expand_as(q_now)
    clipped_q = old_q + torch.clamp(q_now - old_q, -VALUE_CLIP, VALUE_CLIP)
    per_position_loss = torch.maximum(
        torch.square(q_now - target_broadcast),
        torch.square(clipped_q - target_broadcast),
    )
    loss = (
        torch.where(
            position_valid, per_position_loss, torch.zeros_like(per_position_loss)
        ).sum(dim=-1)
        / position_count
    ).mean()
    return loss, q_now


def optimize_qualification_update(
    model: FastAnchorActionAdvantagePolicy,
    critic_optimizer: torch.optim.Optimizer,
    trajectory: AnchorActionTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float,
) -> dict[str, float]:
    """Critic-only fit against the ``D_fit`` split, at the exact fast anchor.

    Design section 6: the qualification phase updates only ``prefix_critic``.
    No residual/actor loss is constructed here at all -- there is no
    `.backward()` call anywhere in this function that could touch
    `residual_parameters()`, and the guard below additionally refuses to run
    if the residual head were ever (incorrectly) left trainable.
    """

    if model.phase != "qualification":
        raise RuntimeError("G20R2 qualification update requires the qualification phase")
    if any(parameter.requires_grad for parameter in model.residual_parameters()):
        raise RuntimeError(
            "G20R2 residual parameters must stay frozen during qualification"
        )
    with torch.no_grad():
        errors = replay_errors(
            replay_trajectory(model, trajectory, device=device), trajectory
        )
    critic_parameters = model.critic_parameters()
    totals = {name: 0.0 for name in ("slow_value_loss", "critic_gradient_norm")}
    finite = True
    model.train()
    for _ in range(int(ppo_passes)):
        loss, _ = _slow_value_loss(model, trajectory, device=device, gamma=gamma)
        critic_optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(critic_parameters, GRADIENT_CLIP)
        finite = finite and bool(torch.isfinite(loss)) and bool(
            torch.isfinite(gradient_norm)
        )
        critic_optimizer.step()
        totals["slow_value_loss"] += float(loss.detach().cpu())
        totals["critic_gradient_norm"] += float(gradient_norm.detach().cpu())
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(ppo_passes)
    totals["residual_output_layer_maximum_absolute_value"] = (
        model.residual_output_layer_maximum_absolute_value()
    )
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
        raise RuntimeError("G20R2 delayed update requires delayed phase")
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

        slow_value_loss, _ = _slow_value_loss(model, trajectory, device=device, gamma=gamma)
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


# ---------------------------------------------------------------------------
# Data roles (design section 5): D_fit / D_credit / D_audit must be
# structurally disjoint, not merely incidentally distinct.
# ---------------------------------------------------------------------------


def validate_disjoint_roles(
    fit_episode_ids: Sequence[int],
    credit_episode_ids: Sequence[int],
    audit_episode_ids: Sequence[int],
) -> None:
    """Raise if any two of the three data roles share an episode id.

    This is a structural guard on the *identifiers that select the data*,
    not a hope that different seeds happened not to collide. Design section
    5: "the three data roles must be genuinely disjoint" -- ``D_audit`` in
    particular must never touch critic or actor updates.
    """

    fit = set(int(value) for value in fit_episode_ids)
    credit = set(int(value) for value in credit_episode_ids)
    audit = set(int(value) for value in audit_episode_ids)
    overlaps = {
        "fit_credit": fit & credit,
        "fit_audit": fit & audit,
        "credit_audit": credit & audit,
    }
    colliding = {name: value for name, value in overlaps.items() if value}
    if colliding:
        raise ValueError(f"G20R2 data roles are not disjoint: {colliding}")


# ---------------------------------------------------------------------------
# Generic clustered-bootstrap confidence machinery (design section 5:
# "clustered at the episode-ledger and suffix-replication level").
# ---------------------------------------------------------------------------


def cluster_bootstrap_lcb(
    cluster_rows: Sequence[torch.Tensor],
    statistic_fn: Callable[[torch.Tensor], float],
    *,
    generator: torch.Generator,
    num_resamples: int = 2000,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Cluster-bootstrap point estimate and one-sided lower confidence bound.

    ``cluster_rows[c]`` holds every raw per-token row belonging to cluster
    ``c`` (one episode/ledger, or one suffix-replication group), shape
    ``[n_tokens_c, D]``. ``statistic_fn`` maps a pooled ``[N, D]`` tensor
    (concatenated rows from a set of clusters) to the scalar statistic of
    interest. Clusters -- not individual tokens -- are resampled with
    replacement; this is what "clustered" means here, and it applies
    uniformly to any of Stage A/B1/B2's statistics without needing a
    distinct closed-form standard error per statistic (active tokens are not
    independent samples, design section 5).

    Returns ``(point_estimate, lcb)``.
    """

    clusters = list(cluster_rows)
    n = len(clusters)
    if n < 2:
        raise ValueError("cluster bootstrap requires at least two clusters")
    point_estimate = float(statistic_fn(torch.cat(clusters, dim=0)))
    resampled = torch.empty(int(num_resamples), dtype=torch.float64)
    for index in range(int(num_resamples)):
        pick = torch.randint(0, n, (n,), generator=generator)
        pooled = torch.cat([clusters[int(i)] for i in pick], dim=0)
        resampled[index] = float(statistic_fn(pooled))
    quantile = 1.0 - float(confidence)
    lcb = float(torch.quantile(resampled, quantile))
    return point_estimate, lcb


# ---------------------------------------------------------------------------
# Stage A -- design section 2: is there a source action effect to identify?
# ---------------------------------------------------------------------------


def stage_a_source_effect(
    oracle_advantage_clusters: Sequence[torch.Tensor],
    *,
    generator: torch.Generator,
    epsilon_audit: float,
    num_resamples: int = 2000,
) -> dict[str, Any]:
    """``S_source = E[(A*(h,a))^2]``; pass iff ``LCB95(S_source) > epsilon_audit^2``.

    ``oracle_advantage_clusters[c]`` holds one column of raw ``A*(h,a)``
    values (shape ``[n_c, 1]``) per audit cluster (an episode-ledger, with
    suffix-Monte-Carlo noise already averaged down within each probe by the
    caller before this function sees it). ``epsilon_audit`` is only the
    numerical/paired-rollout resolution floor (design section 2) -- not an
    effect-size threshold, so this deliberately does not take an effect-size
    parameter at all.
    """

    def statistic(pooled: torch.Tensor) -> float:
        return float(torch.mean(torch.square(pooled)))

    point, lcb = cluster_bootstrap_lcb(
        list(oracle_advantage_clusters),
        statistic,
        generator=generator,
        num_resamples=num_resamples,
    )
    threshold = float(epsilon_audit) ** 2
    return {
        "s_source": point,
        "s_source_lcb95": lcb,
        "epsilon_audit_squared": threshold,
        "passed": bool(lcb > threshold),
    }


def stage_a_p2_authority_check(
    oracle_advantage_clusters: Sequence[torch.Tensor],
    residual_score_clusters: Sequence[torch.Tensor],
    *,
    zero_tolerance: float = P2_AUTHORITY_ZERO_TOLERANCE,
) -> dict[str, Any]:
    """``g*_res = E[s_res(h,a) A*(h,a)]``; flags a source-authority mismatch.

    Design section 2: "If S_source > 0 but |g*_res| = 0, the source has an
    action effect lying outside P2's authority." Each cluster's rows must
    already be paired: ``oracle_advantage_clusters[c]`` is ``[n_c, 1]``,
    ``residual_score_clusters[c]`` is ``[n_c, action_dim]``, aligned by row.
    This is a fail-closed numeric-equality audit, not a hypothesis test --
    unlike Stage A/B1/B2's LCB gates, section 2 states this as a literal
    equality condition, so a numeric tolerance (not a confidence bound)
    decides "exactly zero" here.
    """

    oracle = torch.cat(list(oracle_advantage_clusters), dim=0)
    score = torch.cat(list(residual_score_clusters), dim=0)
    if oracle.shape[0] != score.shape[0]:
        raise ValueError("G20R2 P2 authority check requires row-aligned clusters")
    g_star = (score * oracle).mean(dim=0)
    magnitude = float(torch.linalg.vector_norm(g_star))
    return {
        "g_star_res": g_star.detach().cpu().tolist(),
        "g_star_res_magnitude": magnitude,
        "outside_authority": bool(magnitude < float(zero_tolerance)),
    }


# ---------------------------------------------------------------------------
# Stage B1 -- design section 3: did the critic identify the contrast?
# ---------------------------------------------------------------------------


def stage_b1_contrast_alignment(
    oracle_response_clusters: Sequence[torch.Tensor],
    critic_response_clusters: Sequence[torch.Tensor],
    *,
    generator: torch.Generator,
    num_resamples: int = 2000,
) -> dict[str, Any]:
    """``rho = E[qg] / sqrt(E[q^2] E[g^2])``; pass iff ``LCB95(rho) > 0``.

    Each cluster's rows are already within-history-centered
    ``(g_hk, q_hk)`` pairs (design section 3), shape ``[n_c, 2]`` with
    columns ``(g, q)``.
    """

    def statistic(pooled: torch.Tensor) -> float:
        g = pooled[:, 0]
        q = pooled[:, 1]
        numerator = float((q * g).mean())
        denominator = float(torch.sqrt((q * q).mean() * (g * g).mean()))
        if denominator <= 0.0:
            return 0.0
        return numerator / denominator

    paired_clusters = [
        torch.stack((g, q), dim=-1)
        for g, q in zip(oracle_response_clusters, critic_response_clusters)
    ]
    point, lcb = cluster_bootstrap_lcb(
        paired_clusters,
        statistic,
        generator=generator,
        num_resamples=num_resamples,
    )
    return {"rho": point, "rho_lcb95": lcb, "passed": bool(lcb > 0.0)}


def _positive_scale_fit(g_cal: torch.Tensor, q_cal: torch.Tensor) -> float:
    """``alpha* = argmin_{alpha>=0} E_cal[(g - alpha q)^2]``, closed form."""

    denominator = float((q_cal * q_cal).mean())
    if denominator <= 0.0:
        return 0.0
    numerator = float((g_cal * q_cal).mean())
    return max(0.0, numerator / denominator)


def stage_b1_recalibrated_r2(
    calibration_g: torch.Tensor,
    calibration_q: torch.Tensor,
    audit_response_clusters: Sequence[torch.Tensor],
    *,
    generator: torch.Generator,
    num_resamples: int = 2000,
) -> dict[str, Any]:
    """Positive-scale recalibrated held-out R^2 (design section 3).

    ``alpha*`` is fit once on the (already disjoint) calibration split, then
    frozen while ``audit_response_clusters`` (the untouched audit split,
    within-history-centered ``(g, q)`` pairs per cluster, shape ``[n_c, 2]``)
    supplies the clustered LCB of ``R2_plus``.
    """

    alpha = _positive_scale_fit(calibration_g, calibration_q)

    def statistic(pooled: torch.Tensor) -> float:
        g = pooled[:, 0]
        q = pooled[:, 1]
        residual = g - alpha * q
        denominator = float((g * g).mean())
        if denominator <= 0.0:
            return 0.0
        return 1.0 - float((residual * residual).mean()) / denominator

    point, lcb = cluster_bootstrap_lcb(
        list(audit_response_clusters),
        statistic,
        generator=generator,
        num_resamples=num_resamples,
    )
    return {
        "alpha_star": alpha,
        "r2_plus": point,
        "r2_plus_lcb95": lcb,
        "passed": bool(lcb > 0.0),
    }


# ---------------------------------------------------------------------------
# Stage B2 -- design section 4: does the credit move the actor the right way?
# ---------------------------------------------------------------------------


def residual_action_space_score(
    raw_action: torch.Tensor, mean: torch.Tensor, std: torch.Tensor
) -> torch.Tensor:
    """The per-token score seen by the residual's additive mean-shift.

    Realized as the standard Gaussian location score in *action space*,
    ``(raw_action - mean) / std**2``. The residual enters the action mean
    only through an additive, active-set-centered shift (a fixed linear
    projection of the residual network's raw output), so this action-space
    score is the immediate factor every residual parameter's score shares
    before the (advantage-independent) network Jacobian; comparing two
    advantage-weighted sums of this shared factor is the smallest reasonable
    realization of "the score ... seen by the centered residual parameters"
    (Pro's ruling, section on Stage B2) that avoids an expensive explicit
    per-token parameter-space Jacobian, which this frozen contract does not
    itself mandate ("score or Jacobian").
    """

    return (raw_action - mean) / torch.square(std)


def stage_b2_gradient_alignment(
    score_clusters: Sequence[torch.Tensor],
    learned_advantage_clusters: Sequence[torch.Tensor],
    oracle_advantage_clusters: Sequence[torch.Tensor],
    *,
    generator: torch.Generator,
    zero_tolerance: float = P2_AUTHORITY_ZERO_TOLERANCE,
    num_resamples: int = 2000,
) -> dict[str, Any]:
    """``ghat_res``, ``g*_res`` and their clustered-LCB cosine (design section 4).

    Each cluster supplies row-aligned ``score`` (``[n_c, action_dim]``),
    ``learned_advantage`` (``[n_c, 1]``) and ``oracle_advantage``
    (``[n_c, 1]``). Requires ``|g*_res| > 0`` (point estimate) and
    ``LCB95(cos(ghat_res, g*_res)) > 0``.
    """

    rows = [
        torch.cat((score, learned, oracle), dim=-1)
        for score, learned, oracle in zip(
            score_clusters, learned_advantage_clusters, oracle_advantage_clusters
        )
    ]
    action_dim = score_clusters[0].shape[-1]

    def split(pooled: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return (
            pooled[:, :action_dim],
            pooled[:, action_dim : action_dim + 1],
            pooled[:, action_dim + 1 :],
        )

    def cosine(pooled: torch.Tensor) -> float:
        score, learned, oracle = split(pooled)
        g_hat = (score * learned).mean(dim=0)
        g_star = (score * oracle).mean(dim=0)
        norm_hat = torch.linalg.vector_norm(g_hat)
        norm_star = torch.linalg.vector_norm(g_star)
        denominator = float(norm_hat * norm_star)
        if denominator <= 0.0:
            return 0.0
        return float(torch.dot(g_hat, g_star) / denominator)

    point_cosine, lcb_cosine = cluster_bootstrap_lcb(
        rows, cosine, generator=generator, num_resamples=num_resamples
    )

    pooled_all = torch.cat(rows, dim=0)
    score_all, learned_all, oracle_all = split(pooled_all)
    g_hat_res = (score_all * learned_all).mean(dim=0)
    g_star_res = (score_all * oracle_all).mean(dim=0)
    g_star_magnitude = float(torch.linalg.vector_norm(g_star_res))

    return {
        "g_hat_res": g_hat_res.detach().cpu().tolist(),
        "g_star_res": g_star_res.detach().cpu().tolist(),
        "g_star_res_magnitude": g_star_magnitude,
        "cosine": point_cosine,
        "cosine_lcb95": lcb_cosine,
        "passed": bool(
            g_star_magnitude > zero_tolerance and lcb_cosine > 0.0
        ),
    }
