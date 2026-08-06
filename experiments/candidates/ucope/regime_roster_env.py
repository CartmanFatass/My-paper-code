"""UCOPE sibling environment: hidden load regime with sequential evidence.

Sequence 03 environment implementation.  External ruling
``ENV_CAPABILITY_EXTENSION_REQUIRED`` held that the unchanged continuous-roster
toy is structurally incapable of testing UCOPE and specified the minimal sibling
capability plus a gate that must pass *before* any training run:

    "That exact calculation is the decisive proof that the environment now
     contains the mechanism.  Training should begin only after this capability
     certificate is positive."

``capability_certificate.certificate()`` returns ``UCOPE_CAPABILITY_PRESENT``,
so the gate is open.  This module is the environment that realizes exactly the
dynamics that certificate scores -- no more.

WHAT IS ADDED TO THE BASE, AND WHAT IS NOT
------------------------------------------
Three ingredients, matching the ruling one for one:

1. *One hidden, persistent, payoff-relevant regime.*  ``Theta in {S, L}`` is
   drawn once per episode and fixes the realized load for the whole episode.
   Capabilities, roster dynamics, target mix, action dimension, action legality
   and the service reward formula are untouched.

2. *The oracle disclosure for that coordinate is removed.*  The realized load is
   used to compute the service target but is NOT published in the observation --
   the load coordinate is replaced by a constant.  Target mix remains exactly
   observed, so the mix half of the action stays solved and the experiment
   isolates the effort half.

3. *Sequential evidence whose count moves the posterior.*  Each decision epoch
   ends with a binary outcome drawn at the precommitted likelihoods.  The count
   of positive evidence is a sufficient statistic for the regime.

The ruling named five insufficient changes; none is used.  In particular the
load is *withheld* rather than merely made stochastic, and the count is never
rewarded through an auxiliary bonus -- it earns its value only by improving the
effort decision.

EXACT BASE PROJECTION
---------------------
The sibling does not replace ``RuntimeCapacityRosterEnv``; it wraps one.  With
``intervention_enabled=False`` it reproduces the base environment exactly --
same realized load, same published observation, no evidence.
``test_disabled_projection_reproduces_the_base_environment`` pins that over a
full episode, step by step.

WHY THE CERTIFICATE'S ARITHMETIC APPLIES HERE EXACTLY
-----------------------------------------------------
With mix matched and a uniform effort ``e`` against realized load ``l``, the
base reward

    served_k  = e * m_k * A_k,      target_k = l * m_k * A_k
    reward    = clip(1 - mean_k |served_k - target_k| / target_k, 0, 1)

collapses term by term to ``clip(1 - |e - l| / l, 0, 1)`` -- identically
``capability_certificate.reward``.  The episode is divided into ``PERIODS``
equal epochs of ``EPOCH_LENGTH`` steps, so an episode's total reward is exactly
``EPOCH_LENGTH`` times the certificate's episode value.  That correspondence is
checked exactly, by enumerating the whole evidence tree, in
``regime_conformance.py`` -- not by sampling.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

import numpy as np

from envs.continuous_roster import runtime_capacity as roster_env

from experiments.candidates.ucope import capability_certificate as cc

RAW_OUTPUT_BINDING = "ucope.regime_roster_env.v1"

#: The episode is split into the certificate's decision periods.
PERIODS = cc.PERIODS
EPOCH_LENGTH = roster_env.HORIZON // PERIODS
if EPOCH_LENGTH * PERIODS != roster_env.HORIZON:
    raise RuntimeError("UCOPE sibling requires HORIZON divisible by PERIODS")

#: What the observation publishes in place of the withheld load.  It carries no
#: information about the regime by construction: it is a constant.
WITHHELD_LOAD_VALUE = np.float32(0.0)

#: Observation index of the load coordinate in the base ten-dim observation.
LOAD_INDEX = 3


@dataclass(frozen=True)
class RegimeView:
    """A base view plus the sibling's count state.  The load is NOT here.

    This type is deliberately fail-closed on the withheld coordinate.  An
    earlier revision carried the true load as a ``realized_load`` field and also
    stored it in the nested ``CapacityRosterView.load`` slot, so the training
    path was closed only because ``policy_features`` happened not to read either
    one.  External Pro named that:

        The hidden load is absent from observations, but remains
        programmatically accessible as RegimeView.realized_load and as the load
        field of the nested CapacityRosterView. The current policy_features read
        set does not access either field, so this training path is closed; the
        reusable environment boundary itself is not fail-closed.

    The environment still needs the true load to compute the service target, so
    it keeps it privately and exposes it only through the explicit
    ``UcopeRegimeRosterEnv.realized_load()`` accessor.  A policy that is handed a
    view cannot reach it at all.
    """

    base: roster_env.CapacityRosterView
    positive_count: int
    completed_epochs: int

    @property
    def observations(self) -> np.ndarray:
        return self.base.observations

    @property
    def active_mask(self) -> np.ndarray:
        return self.base.active_mask

    @property
    def target_mix(self) -> float:
        return self.base.target_mix


#: Seed root for the sibling's own draws.
#:
#: The previous values were ``0`` and ``1``, which is exactly what
#: ``runtime_capacity.make_ledger`` uses for its temporary-leave and
#: terminal-leave choices.  Because ``paired_training`` passes one seed as BOTH
#: the regime seed and the ledger master seed, ``default_rng((seed, episode, 0))``
#: was literally the same generator state as the base ledger's stream 0, and the
#: comment claiming independence from every base stream was false.  Pro found no
#: operative leak -- the policy does not observe which members leave -- but a
#: reusable environment must not depend on that.
#:
#: The fix is a reserved namespace on two axes at once: a distinct domain word in
#: front of the entropy tuple (so the tuple has a different length and content
#: from any base tuple), and stream ids far outside every base stream, which are
#: ``0, 1, 3, 4`` and ``100+key`` / ``200+key`` for ``key`` below the member
#: capacity.  ``test_sibling_streams_are_disjoint_from_the_base_ledger`` pins the
#: disjointness by enumeration rather than by this comment.
_SIBLING_SEED_DOMAIN = 0x_5C0_9E_03
_REGIME_STREAM = 900_001
_EVIDENCE_STREAM = 900_002


def _sibling_rng(seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        (_SIBLING_SEED_DOMAIN, int(seed), int(episode_id), int(stream))
    )


def draw_regime(episode_id: int, *, regime_seed: int) -> str:
    """Owner-agnostic regime draw at the certificate's prior."""
    rng = _sibling_rng(regime_seed, episode_id, _REGIME_STREAM)
    return cc.S if rng.random() < float(cc.PRIOR_S) else cc.L


def draw_evidence(
    episode_id: int, regime: str, *, evidence_seed: int
) -> tuple[int, ...]:
    """The episode's evidence bits, drawn at the precommitted likelihoods."""
    rng = _sibling_rng(evidence_seed, episode_id, _EVIDENCE_STREAM)
    probability = float(cc.EVIDENCE_POSITIVE[regime])
    return tuple(int(rng.random() < probability) for _ in range(PERIODS))


class UcopeRegimeRosterEnv:
    """The registered UCOPE sibling.  Wraps, never replaces, the base env."""

    def __init__(
        self,
        ledger: roster_env.CapacityRosterLedger,
        *,
        regime: str | None = None,
        evidence_bits: Sequence[int] | None = None,
        intervention_enabled: bool = True,
    ):
        if regime is not None and regime not in cc.REGIMES:
            raise ValueError("UCOPE sibling regime outside the registered support")
        if evidence_bits is not None and len(evidence_bits) != PERIODS:
            raise ValueError("UCOPE sibling requires one evidence bit per period")
        self._base = roster_env.RuntimeCapacityRosterEnv(ledger)
        self.intervention_enabled = bool(intervention_enabled)
        self.regime = regime
        self._evidence_bits = (
            None if evidence_bits is None else tuple(int(b) for b in evidence_bits)
        )
        self.positive_count = 0
        self.completed_epochs = 0
        self.reward_trace: list[float] = []

    @property
    def time(self) -> int:
        return self._base.time

    def realized_load(self) -> float:
        """The load the service target is actually computed against."""
        if not self.intervention_enabled:
            return float(self._base.ledger.load[self._base.time])
        if self.regime is None:
            raise RuntimeError("UCOPE sibling intervention requires a regime")
        return float(cc.LOAD[self.regime])

    def observe(self) -> RegimeView:
        base_view = self._base.observe()
        if not self.intervention_enabled:
            # The disabled path IS the base environment and claims no
            # withholding, so the base view passes through untouched -- true
            # load coordinate and all.  That is what makes the exact projection
            # check in `regime_conformance.disabled_projection_matches_base`
            # meaningful.
            return RegimeView(base_view, 0, 0)

        # Ingredient 2: withhold the load coordinate.  Target mix is untouched.
        # The view's own `load` slot is withheld too, not just the published
        # observation column -- otherwise the coordinate is severed from the
        # network's input while remaining one attribute access away.
        observations = base_view.observations.copy()
        observations[base_view.active_mask, LOAD_INDEX] = WITHHELD_LOAD_VALUE
        withheld = roster_env.CapacityRosterView(
            base_view.time,
            observations,
            base_view.active_mask,
            base_view.critic_state,
            base_view.membership_change,
            float(WITHHELD_LOAD_VALUE),
            base_view.target_mix,
        )
        return RegimeView(withheld, self.positive_count, self.completed_epochs)

    def step(self, actions: np.ndarray) -> tuple[float, bool, dict[str, float]]:
        """Base step semantics with the realized load as the service target."""
        view = self.observe()
        values = np.asarray(actions, dtype=np.float32)
        expected = (self._base.ledger.member_capacity, roster_env.ACTION_DIM)
        if values.shape != expected or not np.isfinite(values).all():
            raise ValueError("UCOPE sibling action shape/finite mismatch")
        if np.any(np.abs(values) > 1.0) or np.count_nonzero(
            values[~view.active_mask]
        ):
            raise ValueError("UCOPE sibling action support mismatch")

        keys = np.flatnonzero(view.active_mask)
        effort = (values[keys, 0] + 1.0) / 2.0
        mix = (values[keys, 1] + 1.0) / 2.0
        capabilities = self._base.ledger.capabilities[keys]
        served = np.asarray((
            np.sum(effort * mix * capabilities[:, 0], dtype=np.float64),
            np.sum(effort * (1.0 - mix) * capabilities[:, 1], dtype=np.float64),
        ))
        aggregate = capabilities.sum(axis=0, dtype=np.float64)
        # The load comes from the environment's private accessor, never from the
        # view -- the view no longer carries it, which is the point.
        load, target_mix = self.realized_load(), view.target_mix
        target = np.asarray((
            load * target_mix * aggregate[0],
            load * (1.0 - target_mix) * aggregate[1],
        ))
        relative_error = np.abs(served - target) / np.maximum(target, 1e-8)
        reward = float(np.clip(1.0 - relative_error.mean(), 0.0, 1.0))

        # Advance the base roster with the same action so lifecycle, ages and
        # membership evolve exactly as in the base environment.
        self._base.previous_actions[keys] = values[keys]
        self._base.age[keys] += 1
        self._base.reward_trace.append(reward)
        self._base.roster_sizes.append(len(keys))
        self._base.time += 1
        self._base._prepared_time = None
        self._base._change = roster_env.MembershipChange()
        self._base._terminated = self._base.time == roster_env.HORIZON

        self.reward_trace.append(reward)
        if self.intervention_enabled and self._base.time % EPOCH_LENGTH == 0:
            # Ingredient 3: evidence is emitted AFTER the epoch's decisions, so
            # epoch t decides under the count accumulated over epochs < t.
            if self._evidence_bits is None:
                raise RuntimeError("UCOPE sibling requires registered evidence bits")
            self.positive_count += self._evidence_bits[self.completed_epochs]
            self.completed_epochs += 1

        return reward, self._base._terminated, {"service_utility": reward}

    def episode_total(self) -> float:
        return float(sum(self.reward_trace))


def uniform_effort_actions(view: RegimeView, effort: float) -> np.ndarray:
    """Uniform effort with the mix matched exactly to the observed target."""
    capacity = len(view.active_mask)
    actions = np.zeros((capacity, roster_env.ACTION_DIM), dtype=np.float32)
    actions[view.active_mask, 0] = np.float32(2.0 * float(effort) - 1.0)
    actions[view.active_mask, 1] = np.float32(2.0 * view.target_mix - 1.0)
    return actions
