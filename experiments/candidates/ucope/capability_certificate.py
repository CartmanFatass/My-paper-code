"""Exact capability certificate for a UCOPE-testable sibling environment.

External ruling ``ENV_CAPABILITY_EXTENSION_REQUIRED`` (archived at
``local_research/pro_reviews/env_capability_v1_continuous_roster_toy/``) held
that the unchanged continuous-roster toy environment is structurally incapable
of testing UCOPE, and specified both the minimal sibling capability and a gate
that must pass *before* any training run:

    exists reachable z1, z2 with  a*(z1) != a*(z2),
    and  V_count_informed > V_matched_count_blind,
    with the gap vanishing under the registered count-severing ablation.

    "That exact calculation is the decisive proof that the environment now
     contains the mechanism.  Training should begin only after this capability
     certificate is positive."

This module is that calculation. It is exact rational arithmetic end to end --
no floats, no sampling, no training -- so it either proves the mechanism is
present or proves it is not.

THE SIBLING DYNAMICS BEING CERTIFIED
------------------------------------
Built to the three ingredients the ruling required, and to nothing more:

1. *One hidden, persistent, payoff-relevant regime.*  A binary regime
   ``Theta in {S, L}`` fixed for the episode, affecting ONLY the load
   coordinate.  Capabilities, roster dynamics, target mix, action dimension and
   the service reward are untouched.

2. *The oracle disclosure for that coordinate is removed.*  The realized load is
   NOT published in the observation.  Target mix remains exactly observed, so
   the mix half of the action stays solved and the certificate isolates the
   effort half.

3. *Sequential evidence whose count moves the posterior.*  After each decision a
   binary outcome is emitted with precommitted likelihoods under the two
   regimes.  The count of positive evidence is a sufficient statistic.

The ruling also named five insufficient changes; none is used here.  In
particular the load is withheld rather than merely made stochastic, and the
count is never rewarded through an auxiliary bonus -- it earns its value only
by improving the effort decision.

WHY THE EFFORT DECISION HAS A SWITCHING THRESHOLD
--------------------------------------------------
With mix matched exactly, the environment's own reward

    reward = clip(1 - mean(|served - target| / target), 0, 1)

collapses for a uniform effort ``e`` against realized load ``l`` to

    reward(e, l) = clip(1 - |e - l| / l, 0, 1)

which is a tent peaking at ``e = l`` and vanishing outside ``(0, 2l)``.  A
belief ``rho = P(Theta = S)`` therefore faces a two-peaked objective whose
maximizer is one of the two regime loads, and the optimal choice SWITCHES at a
threshold in ``rho``.  That switch is precisely the UCOPE mechanism: a count
that moves ``rho`` across the threshold changes the Bayes-optimal action.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product

RAW_OUTPUT_BINDING = "ucope.capability_certificate.v1"

S = "S"
L = "L"
REGIMES = (S, L)

#: Regime loads.  Both interior to (0, 1) so the induced efforts are inside the
#: registered action support, exactly as the base environment requires.
LOAD = {S: Fraction(1, 4), L: Fraction(3, 4)}

#: Prior on the hidden regime.
PRIOR_S = Fraction(1, 2)

#: Precommitted likelihoods of the positive binary evidence under each regime.
#: They must differ or the evidence is uninformative.
EVIDENCE_POSITIVE = {S: Fraction(3, 4), L: Fraction(1, 4)}

#: Number of decision periods.  Each period emits one evidence bit AFTER the
#: decision, so period t decides under the count accumulated over t-1 periods.
PERIODS = 3

#: Candidate efforts.  The optimum of a two-peaked tent objective is attained at
#: a peak, so the two regime loads are a complete argmax search set.
CANDIDATE_EFFORTS = tuple(sorted({LOAD[S], LOAD[L]}))


def reward(effort: Fraction, realized_load: Fraction) -> Fraction:
    """The base environment's service reward, exactly, for a uniform effort."""
    deviation = abs(effort - realized_load) / realized_load
    if deviation >= 1:
        return Fraction(0)
    return Fraction(1) - deviation


def posterior_s(positive: int, trials: int) -> Fraction:
    """P(Theta = S | count of positive evidence), exactly."""
    if positive < 0 or trials < 0 or positive > trials:
        raise ValueError("invalid evidence count")
    negative = trials - positive
    weight_s = PRIOR_S * EVIDENCE_POSITIVE[S] ** positive * (
        1 - EVIDENCE_POSITIVE[S]
    ) ** negative
    weight_l = (1 - PRIOR_S) * EVIDENCE_POSITIVE[L] ** positive * (
        1 - EVIDENCE_POSITIVE[L]
    ) ** negative
    return weight_s / (weight_s + weight_l)


def expected_reward(effort: Fraction, rho: Fraction) -> Fraction:
    return rho * reward(effort, LOAD[S]) + (1 - rho) * reward(effort, LOAD[L])


def optimal_effort(rho: Fraction) -> Fraction:
    """Bayes-optimal effort at belief ``rho``; ties break to the smaller effort."""
    best = None
    for effort in CANDIDATE_EFFORTS:
        value = expected_reward(effort, rho)
        if best is None or value > best[0] or (value == best[0] and effort < best[1]):
            best = (value, effort)
    assert best is not None
    return best[1]


def action_switches() -> tuple[bool, tuple[tuple[int, int], ...]]:
    """Ingredient 3: are there two reachable count states with different optima?"""
    seen: dict[Fraction, tuple[int, int]] = {}
    witnesses: list[tuple[int, int]] = []
    for trials in range(PERIODS):
        for positive in range(trials + 1):
            action = optimal_effort(posterior_s(positive, trials))
            if action not in seen:
                seen[action] = (positive, trials)
    if len(seen) < 2:
        return False, ()
    witnesses = [seen[action] for action in sorted(seen)]
    return True, tuple(witnesses)


@dataclass(frozen=True)
class Valuation:
    informed: Fraction
    blind: Fraction
    severed: Fraction


def _episode_value(*, informed: bool, severed: bool) -> Fraction:
    """Exact expected total reward over the full evidence tree.

    ``informed``  -- the policy conditions its effort on the accumulated count.
    ``blind``     -- (informed=False) the policy always acts on the prior.
    ``severed``   -- the registered ablation: the count is accumulated but
                     deterministically severed before the decision, so the
                     policy is informationally identical to blind while
                     executing the same code path.
    """
    total = Fraction(0)
    for regime in REGIMES:
        regime_prior = PRIOR_S if regime is S else 1 - PRIOR_S
        p_positive = EVIDENCE_POSITIVE[regime]
        for outcomes in product((1, 0), repeat=PERIODS):
            path_probability = Fraction(1)
            for bit in outcomes:
                path_probability *= p_positive if bit else (1 - p_positive)
            positive = 0
            episode_reward = Fraction(0)
            for period in range(PERIODS):
                if informed and not severed:
                    rho = posterior_s(positive, period)
                else:
                    rho = PRIOR_S
                episode_reward += reward(optimal_effort(rho), LOAD[regime])
                positive += outcomes[period]
            total += regime_prior * path_probability * episode_reward
    return total


def valuations() -> Valuation:
    return Valuation(
        informed=_episode_value(informed=True, severed=False),
        blind=_episode_value(informed=False, severed=False),
        severed=_episode_value(informed=True, severed=True),
    )


def certificate() -> dict[str, object]:
    """Run the full gate the external ruling requires."""
    switches, witnesses = action_switches()
    value = valuations()
    gap = value.informed - value.blind
    severed_gap = value.severed - value.blind
    passed = bool(switches) and gap > 0 and severed_gap == 0
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "regime_loads": {k: str(v) for k, v in LOAD.items()},
        "evidence_positive": {k: str(v) for k, v in EVIDENCE_POSITIVE.items()},
        "prior_s": str(PRIOR_S),
        "periods": PERIODS,
        "action_switch_exists": switches,
        "switch_witness_counts": witnesses,
        "value_count_informed": str(value.informed),
        "value_count_blind": str(value.blind),
        "value_count_severed": str(value.severed),
        "informed_minus_blind": str(gap),
        "severed_minus_blind": str(severed_gap),
        "terminal": (
            "UCOPE_CAPABILITY_PRESENT" if passed else "UCOPE_CAPABILITY_ABSENT"
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(certificate(), indent=2, default=str))
