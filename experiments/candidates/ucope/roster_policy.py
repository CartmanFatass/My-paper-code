"""UCOPE count-state policy on the continuous-roster toy environment.

This is the algorithm-implementation step for Sequence 03: it moves UCOPE out
of the exact-rational enumerator and into code that the real toy runner calls.

WHAT UCOPE CLAIMS, AND WHAT THIS MODULE BINDS IT TO
---------------------------------------------------
``acquisition_park_certificate`` proves, in a registered finite family, that a
*count* statistic can change the Bayes-optimal next-period choice while a
count-blind comparator cannot.  The mechanism needs a persistent count that
carries information the instantaneous observation does not.

The six-coordinate observation already exposes ``obs[5] = log active count``.
That is an INSTANTANEOUS count and is therefore NOT the UCOPE statistic -- a
policy reading it is already count-aware in the trivial sense.  The statistic
bound here is the *persistent lifecycle* count the task list names: how much
membership churn has accumulated so far, per member and per roster.  That is a
function of history, not of the current frame, and it is not recoverable from
any single six-coordinate observation.

Two arms are provided, and they are matched:

``UcopeCountStatePolicy``   sees the persistent count features.
``UcopeCountBlindPolicy``   identical architecture, identical parameter count,
                            identical input width -- the count channels are
                            replaced by a fixed constant.  Information is
                            ablated; capacity and compute are not.

HONEST BOUNDARY -- READ THIS BEFORE INTERPRETING ANY RESULT
------------------------------------------------------------
The reward of this environment is

    reward = clip(1 - mean(|served - target| / target), 0, 1)

and ``runtime_capacity.constructive_actions`` sets ``effort_i = load`` and
``mix_i = target_mix``, which in observation terms is the fixed affine map

    action_0 = 2 * obs[3] - 1        action_1 = 2 * obs[4] - 1

External ruling (ENV_CAPABILITY_EXTENSION_REQUIRED, archived at
``local_research/pro_reviews/env_capability_v1_continuous_roster_toy/``)
confirmed this is the **analytic argmax** and settled the exact wording, which
is narrower than an earlier draft of this docstring claimed:

* It is an analytic argmax and an executable NEAR-oracle.  It is NOT certified
  as the exact discrete binary32 argmax.  The native backend forms each
  per-member service contribution in binary32 and accumulates into double,
  while the target multiplies double-converted load and mix by a double
  capability aggregate; those operation orders are not generally bit-identical.
  A printed ``1.000000`` is consistent with a reward microscopically below one.
* The correct independence claim is that **there exists** a stationary, shared,
  owner-agnostic optimal policy ignoring active count, capabilities, priority,
  age, previous action, explicit clock, membership history and member identity.
  The action is not constant over time -- it tracks the observed load and mix.
  What is unnecessary is explicit time or memory.
* The COMPLETE optimal set is *not* independent of capabilities or roster
  composition; heterogeneous optimal allocations can depend on them.  What is
  roster-independent is the existence of the uniform optimizer above.  At the
  constructive interior point the optimal set is locally (2n-2) dimensional for
  n active members, and globally may be a union of pieces rather than one
  smooth manifold.

CONSEQUENCE FOR THIS MODULE.  The ruling classifies UCOPE as *structurally
untestable* on this environment: current load and mix are disclosed before the
action, actions do not acquire observations or alter future opportunities, and
the lifecycle is exogenous -- so there is no Bayesian information problem for a
count statistic to solve.  A count-aware and a count-severed policy contain the
same affine optimum.

This module is therefore a PIPELINE-VALIDATION AND NULL-CONTROL arm, not a test
of UCOPE.  A null here is expected and is not evidence against the candidate;
retiring the mechanism on such a null would be a construct-validity error.  A
*positive* difference would be a diagnostic warning of an optimization,
regularization, capacity or state-leakage confound, since the intended
information channel has zero support.  Acceptance reference is the affine
oracle.  The scientific test requires the separately registered UCOPE-capable
sibling environment, which must pass an exact finite-state capability
certificate before any training run.
"""

from __future__ import annotations

from typing import Any

import torch

from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process import continuous_roster_native_six_coordinate_training_g39 as g39
from ha_ctse_process import continuous_roster_six_coordinate_cs_g38 as g38
from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35

RAW_OUTPUT_BINDING = "ucope.roster_policy.v1"

#: Persistent lifecycle count channels appended to the six coordinates.
#: 0 -- per-member accumulated membership transitions (own churn)
#: 1 -- roster-level accumulated membership transitions (shared churn)
UCOPE_COUNT_DIM = 2

RETAINED_OBSERVATION_DIM = g38.RETAINED_OBSERVATION_DIM
UCOPE_OBSERVATION_DIM = RETAINED_OBSERVATION_DIM + UCOPE_COUNT_DIM

#: Value written into the count channels by the count-blind arm.  Any constant
#: works; it is fixed so the two arms differ ONLY in information content.
COUNT_BLIND_CONSTANT = 0.0

#: Counts are divided by this before entering the network, so the channels stay
#: on the same scale as the other coordinates across H=48.
COUNT_SCALE = float(roster_env.HORIZON)


class _PersistentCountMixin:
    """Accumulates membership churn across a rollout.

    The counter is a pure function of the ``active_mask`` sequence the runner
    already supplies, so nothing is read that the policy is not entitled to
    see, and no future information can enter.  It is reset explicitly by
    :meth:`reset_count_state`; a shape change also resets it, which is what
    happens when a new batch or a new capacity begins.
    """

    _prev_active: torch.Tensor | None
    _member_churn: torch.Tensor | None

    def reset_count_state(self) -> None:
        self._prev_active = None
        self._member_churn = None

    def _update_counts(self, active_mask: torch.Tensor) -> torch.Tensor:
        """Return (batch, capacity, UCOPE_COUNT_DIM) persistent count features."""
        current = active_mask.to(torch.float32)
        prev = getattr(self, "_prev_active", None)
        churn = getattr(self, "_member_churn", None)
        if prev is None or churn is None or prev.shape != current.shape:
            churn = torch.zeros_like(current)
        else:
            churn = churn + (current != prev).to(torch.float32)
        self._prev_active = current.detach()
        self._member_churn = churn.detach()

        own = churn / COUNT_SCALE
        shared = churn.sum(dim=-1, keepdim=True).expand_as(churn) / COUNT_SCALE
        return torch.stack((own, shared), dim=-1)

    def _count_channels(self, active_mask: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError


def _widen_linear(layer: torch.nn.Linear, extra: int) -> torch.nn.Linear:
    """Return a copy of ``layer`` with ``extra`` additional zero-valued inputs.

    Zero initialization is the point: immediately after construction the widened
    graph computes EXACTLY what the six-coordinate graph computed, so both UCOPE
    arms start behaviourally identical to the unmodified G39 baseline and any
    later difference is attributable to what flows through the new columns.
    """
    widened = torch.nn.Linear(
        layer.in_features + int(extra),
        layer.out_features,
        bias=layer.bias is not None,
    )
    with torch.no_grad():
        widened.weight.zero_()
        widened.weight[:, : layer.in_features].copy_(layer.weight)
        if layer.bias is not None:
            widened.bias.copy_(layer.bias)
    return widened


#: Entry points whose fan-in is the six-coordinate observation.  All of them are
#: widened together so the actor input has one consistent width.
_OBSERVATION_ENTRY_POINTS = (
    ("policy", "member_encoder", 0),
    ("policy", "current_observation_residual", None),
    ("credit_baselines", None, 0),
)


class UcopeCountStatePolicy(_PersistentCountMixin, g39.G39NativeSixPolicy):
    """Six coordinates plus the persistent lifecycle count statistic."""

    def __init__(self, *, member_capacity: int) -> None:
        # Build the unmodified six-coordinate graph first, so the candidate is
        # a strict extension of the accepted G39 policy rather than a rebuild.
        super().__init__(member_capacity=int(member_capacity))
        self._widen_observation_entry_points()
        self.reset_count_state()

    def _widen_observation_entry_points(self) -> None:
        for root, child, index in _OBSERVATION_ENTRY_POINTS:
            holder = getattr(self, root)
            if child is not None:
                holder = getattr(holder, child)
            if index is None:
                setattr(
                    getattr(self, root),
                    child,
                    _widen_linear(holder, UCOPE_COUNT_DIM),
                )
            else:
                holder[index] = _widen_linear(holder[index], UCOPE_COUNT_DIM)

    def _count_channels(self, active_mask: torch.Tensor) -> torch.Tensor:
        return self._update_counts(active_mask)

    def actor_input(
        self, source_observations: torch.Tensor, active_mask: torch.Tensor
    ) -> torch.Tensor:
        if source_observations.shape[-1] != RETAINED_OBSERVATION_DIM:
            raise ValueError("UCOPE actor consumes exactly six source coordinates")
        folded = g38.build_g38_folded_actor_input(source_observations, active_mask)
        counts = self._count_channels(active_mask)
        counts = torch.where(
            active_mask.unsqueeze(-1), counts, torch.zeros_like(counts)
        )
        return torch.cat((folded, counts), dim=-1)

    def forward_step(
        self, *, observations: torch.Tensor, active_mask: torch.Tensor, **kwargs: Any
    ) -> Any:
        if observations.shape[-1] != RETAINED_OBSERVATION_DIM:
            raise ValueError("UCOPE actor accepts exactly six source coordinates")
        return g35.ReturnToGoDirectionBalancedFullActorPolicy.forward_step(
            self,
            observations=self.actor_input(observations, active_mask),
            active_mask=active_mask,
            **kwargs,
        )


class UcopeCountBlindPolicy(UcopeCountStatePolicy):
    """Matched comparator: same graph and parameter count, no count information.

    The count channels are present -- so the input width, the first-layer shape
    and the parameter count are identical to the candidate arm -- but they carry
    a constant.  The churn accumulator is still advanced so that the two arms
    execute the same code path and consume the same RNG; only the value handed
    to the network is severed.
    """

    def _count_channels(self, active_mask: torch.Tensor) -> torch.Tensor:
        live = self._update_counts(active_mask)
        return torch.full_like(live, COUNT_BLIND_CONSTANT)


def make_ucope_pair(
    member_capacity: int, *, initialization_seed: int
) -> dict[str, UcopeCountStatePolicy]:
    """Candidate and comparator with byte-identical initial parameters.

    Both arms are built under the same seeded RNG state, so any divergence in a
    paired experiment is attributable to the count information and not to
    initialization.
    """
    arms: dict[str, UcopeCountStatePolicy] = {}
    for name, factory in (
        ("UCOPE_COUNT_STATE", UcopeCountStatePolicy),
        ("UCOPE_COUNT_BLIND", UcopeCountBlindPolicy),
    ):
        state = torch.random.get_rng_state()
        try:
            torch.manual_seed(int(initialization_seed))
            arms[name] = factory(member_capacity=int(member_capacity))
        finally:
            torch.random.set_rng_state(state)
    blind = arms["UCOPE_COUNT_BLIND"]
    blind.load_state_dict(arms["UCOPE_COUNT_STATE"].state_dict())
    return arms
