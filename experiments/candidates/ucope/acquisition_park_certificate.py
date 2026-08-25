"""Exact acquisition-value park certificate for UCOPE (UCOPE-ACQ-PARK-CERT).

Certifies with rational arithmetic only, against the 2026-08-05 external
adversarial review that parked the forced-balanced acquisition route
(terminal PARK_SCIENTIFICALLY):

1. action-equivalent signal lemma: under the complementary hazards the
   evidence experiment is identical for both actions;
2. posterior-law coupling: the joint (Theta, Z4) law is identical under the
   SSLL, SSSS and GREEDY four-trial prefixes;
3. exact dominance identities: V_CAL - V_PASSIVE = -1 and
   V_CAL - V_GREEDY = -9107/5000 for every registered T;
4. no-horizon-rescue: a rigorous rational bound shows G_T < 1 for EVERY
   decision horizon T, hence N_T = G_T - 1 < 0 universally.

The CAL-CB table is retained only under its corrected name (total forced-
prefix count-adaptive commitment value versus count-blind S).  This module
performs no training, no rollout, no sampling and no floating arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json


S = "S"
L = "L"
THETAS = (S, L)
HORIZON = 3
DURATION = {S: 1, L: 2}
PREFIX_CAL = (S, S, L, L)
PREFIX_PASSIVE = (S, S, S, S)
REGISTERED_T = (0, 1, 2, 3, 4)
TAIL_T0 = 12
RAW_OUTPUT_BINDING = "ucope.acquisition_park_certificate.v1"


class Terminal(str, Enum):
    PARK = "PARK_CONFIRMED_FORCED_BALANCED_ACQUISITION_ROUTE"
    DISCREPANCY = "DISCREPANCY_LOOP_TO_EXTERNAL_REVIEW"


@dataclass(frozen=True)
class HazardFamily:
    """Aligned/misaligned uncensored first-hit hazards; no cell, partner,
    roster, owner-epoch or raw-alias field exists anywhere in this state."""

    aligned: Fraction
    misaligned: Fraction

    def hit(self, theta: str, action: str) -> Fraction:
        return self.aligned if theta == action else self.misaligned

    def evidence_up(self, theta: str, action: str) -> Fraction:
        """Probability that one observation moves net evidence toward S."""
        hit = self.hit(theta, action)
        return hit if action == S else 1 - hit

    def likelihood_ratio(self) -> Fraction:
        return self.aligned / self.misaligned


PRIMARY = HazardFamily(Fraction(9, 10), Fraction(1, 10))
HOMOGENEOUS = HazardFamily(Fraction(1, 2), Fraction(1, 2))
PRIOR_S = Fraction(1, 2)


def reward(theta: str, action: str, family: HazardFamily = PRIMARY) -> Fraction:
    return (HORIZON - DURATION[action]) * family.hit(theta, action)


def posterior_s(z: int, family: HazardFamily = PRIMARY) -> Fraction:
    ratio = family.likelihood_ratio()
    odds = ratio**z
    return odds / (1 + odds)


def _scores(rho: Fraction, family: HazardFamily) -> dict[str, Fraction]:
    return {
        action: (HORIZON - DURATION[action])
        * (rho * family.hit(S, action) + (1 - rho) * family.hit(L, action))
        for action in (S, L)
    }


def rule_action(z: int, family: HazardFamily = PRIMARY, *, reset_belief: bool = False) -> str:
    rho = PRIOR_S if reset_belief else posterior_s(z, family)
    score = _scores(rho, family)
    return S if score[S] >= score[L] else L


def _value(
    theta: str,
    z: int,
    schedule: tuple[str | None, ...],
    family: HazardFamily,
    *,
    reset_belief: bool = False,
    track_evidence: bool = True,
) -> Fraction:
    """Exact expected AUC of the remaining schedule; None slots follow the
    registered count-informed rule, named slots are forced actions."""

    if not schedule:
        return Fraction(0)
    forced = schedule[0]
    action = forced if forced else rule_action(z, family, reset_belief=reset_belief)
    hit = family.hit(theta, action)
    up = family.evidence_up(theta, action)
    step = 1 if track_evidence else 0
    z_hit = z + (step if action == S else -step)
    z_miss = z + (-step if action == S else step)
    gain = (HORIZON - DURATION[action]) * hit
    hit_branch = _value(
        theta, z_hit, schedule[1:], family,
        reset_belief=reset_belief, track_evidence=track_evidence,
    )
    miss_branch = _value(
        theta, z_miss, schedule[1:], family,
        reset_belief=reset_belief, track_evidence=track_evidence,
    )
    return gain + up * hit_branch + (1 - up) * miss_branch if action == S else (
        gain + (1 - up) * hit_branch + up * miss_branch
    )


def _policy_value(
    schedule: tuple[str | None, ...],
    family: HazardFamily = PRIMARY,
    *,
    reset_belief: bool = False,
    track_evidence: bool = True,
) -> Fraction:
    return sum(
        (PRIOR_S if theta == S else 1 - PRIOR_S)
        * _value(
            theta, 0, schedule, family,
            reset_belief=reset_belief, track_evidence=track_evidence,
        )
        for theta in THETAS
    )


def v_cal(T: int, family: HazardFamily = PRIMARY, *, reset_belief: bool = False) -> Fraction:
    return _policy_value(PREFIX_CAL + (None,) * T, family, reset_belief=reset_belief)


def v_passive(T: int, family: HazardFamily = PRIMARY, *, reset_belief: bool = False) -> Fraction:
    return _policy_value(PREFIX_PASSIVE + (None,) * T, family, reset_belief=reset_belief)


def v_greedy(T: int, family: HazardFamily = PRIMARY, *, reset_belief: bool = False) -> Fraction:
    return _policy_value((None,) * (4 + T), family, reset_belief=reset_belief)


def v_cb(T: int, family: HazardFamily = PRIMARY) -> Fraction:
    schedule = (S,) * (4 + T)
    if any(slot is None for slot in schedule):
        raise ValueError("the count-blind schedule must contain no rule slot")
    return _policy_value(schedule, family, track_evidence=False)


def v_cal_severed(T: int, family: HazardFamily = PRIMARY) -> Fraction:
    """Forced SSLL prefix rewards plus a decision phase that starts cold.
    The cold tail is computed through the independent full-tree path so the
    severance identity V_CAL - V_CAL_severed = G_T is not a syntactic
    cancellation against w_from_belief."""
    prefix = _policy_value(PREFIX_CAL, family)
    tail, mass = full_tree_value((None,) * T, family)
    if mass != 1:
        raise ValueError("severed tail enumeration lost probability mass")
    return prefix + tail


def w_from_belief(
    z: int, T: int, family: HazardFamily = PRIMARY, *, reset_belief: bool = False
) -> Fraction:
    rho = posterior_s(z, family)
    return rho * _value(
        S, z, (None,) * T, family, reset_belief=reset_belief
    ) + (1 - rho) * _value(L, z, (None,) * T, family, reset_belief=reset_belief)


def prefix_belief_law(
    prefix_kind: str, family: HazardFamily = PRIMARY
) -> dict[tuple[str, int], Fraction]:
    """Joint prior-predictive law of (Theta, Z4) after a four-trial prefix."""
    law: dict[tuple[str, int], Fraction] = {}
    for theta in THETAS:
        weight = PRIOR_S if theta == S else 1 - PRIOR_S
        states = {0: weight}
        for step in range(4):
            nxt: dict[int, Fraction] = {}
            for z, mass in states.items():
                if prefix_kind == "SSLL":
                    action = PREFIX_CAL[step]
                elif prefix_kind == "SSSS":
                    action = PREFIX_PASSIVE[step]
                elif prefix_kind == "GREEDY":
                    action = rule_action(z, family)
                else:
                    raise ValueError(f"unknown prefix kind {prefix_kind!r}")
                up = family.evidence_up(theta, action)
                nxt[z + 1] = nxt.get(z + 1, Fraction(0)) + mass * up
                nxt[z - 1] = nxt.get(z - 1, Fraction(0)) + mass * (1 - up)
            states = nxt
        for z, mass in states.items():
            law[(theta, z)] = law.get((theta, z), Fraction(0)) + mass
    return law


def gross_information_value(
    T: int, family: HazardFamily = PRIMARY, *, reset_belief: bool = False
) -> Fraction:
    law = prefix_belief_law("SSLL", family)
    downstream = Fraction(0)
    for (theta, z), mass in law.items():
        downstream += mass * _value(
            theta, z, (None,) * T, family, reset_belief=reset_belief
        )
    return downstream - w_from_belief(0, T, family, reset_belief=reset_belief)


def full_tree_value(
    schedule: tuple[str | None, ...], family: HazardFamily = PRIMARY
) -> tuple[Fraction, Fraction]:
    """Leaf-complete enumeration cross-check; returns (value, total mass)."""
    total = Fraction(0)
    mass = Fraction(0)
    n = len(schedule)
    for theta in THETAS:
        weight = PRIOR_S if theta == S else 1 - PRIOR_S
        for bits in product((0, 1), repeat=n):
            probability = weight
            value = Fraction(0)
            z = 0
            for slot, hit_bit in zip(schedule, bits):
                action = slot if slot else rule_action(z, family)
                hit = family.hit(theta, action)
                probability *= hit if hit_bit else 1 - hit
                if hit_bit:
                    value += HORIZON - DURATION[action]
                evidence = 1 if bool(hit_bit) == (action == S) else -1
                z += evidence
            total += probability * value
            mass += probability
    return total, mass


@lru_cache(maxsize=None)
def _occupancy(theta: str, t: int) -> dict[int, Fraction]:
    """Law of Z before decision trial t+1 under the count-informed rule."""
    if t == 0:
        return {0: Fraction(1)}
    prev = _occupancy(theta, t - 1)
    nxt: dict[int, Fraction] = {}
    for z, mass in prev.items():
        action = rule_action(z, PRIMARY)
        up = PRIMARY.evidence_up(theta, action)
        nxt[z + 1] = nxt.get(z + 1, Fraction(0)) + mass * up
        nxt[z - 1] = nxt.get(z - 1, Fraction(0)) + mass * (1 - up)
    return nxt


def _penalties() -> dict[str, Fraction]:
    return {
        S: reward(S, S) - reward(S, L),
        L: reward(L, L) - reward(L, S),
    }


def _exact_partial_regret(t0: int) -> Fraction:
    """Occupancy-path cumulative Bayes regret of the first t0 decision trials
    from cold start; must agree exactly with the DP path cumulative_regret."""
    penalty = _penalties()
    exact_partial = Fraction(0)
    for t in range(t0):
        for theta in THETAS:
            weight = PRIOR_S if theta == S else 1 - PRIOR_S
            optimal = S if theta == S else L
            wrong = sum(
                mass
                for z, mass in _occupancy(theta, t).items()
                if rule_action(z, PRIMARY) != optimal
            )
            exact_partial += weight * penalty[theta] * wrong
    return exact_partial


def _markov_tail(t0: int) -> Fraction:
    """Rational Markov tail from E[3^{-Z_t}|Theta=S] = (3/5)^t and its
    mirror.  The thresholds differ by regime: wrong under Theta=S means Z<0,
    i.e. 3^(-Z) >= 3 (bound (3/5)^t / 3); wrong under Theta=L means Z>=0,
    i.e. 3^(Z) >= 1 (bound (3/5)^t, no /3)."""
    penalty = _penalties()
    decay = Fraction(3, 5)
    tail_s = (decay**t0 / 3) / (1 - decay)
    tail_l = decay**t0 / (1 - decay)
    return PRIOR_S * penalty[S] * tail_s + (1 - PRIOR_S) * penalty[L] * tail_l


def no_horizon_rescue_bound(t0: int = TAIL_T0) -> Fraction:
    """Rational upper bound on cumulative Bayes regret from cold start, valid
    for every horizon T because per-trial regret is nonnegative, so
    CumRegret_T is nondecreasing in T and tiled exactly by the partial sum
    plus the tail.  Since G_T = CumRegret_T(B0) - E[CumRegret_T(B4)] <=
    CumRegret_T(B0) <= bound, bound < 1 certifies N_T = G_T - 1 < 0 for
    EVERY T."""
    return _exact_partial_regret(t0) + _markov_tail(t0)


def cumulative_regret(T: int, law: dict[tuple[str, int], Fraction] | None = None) -> Fraction:
    """Exact cumulative Bayes regret of T rule-driven trials from the given
    belief law (cold start when law is None)."""
    source = (
        law
        if law is not None
        else {(theta, 0): (PRIOR_S if theta == S else 1 - PRIOR_S) for theta in THETAS}
    )
    total = Fraction(0)
    for (theta, z), mass in source.items():
        oracle = max(reward(theta, action) for action in (S, L))
        total += mass * (T * oracle - _value(theta, z, (None,) * T, PRIMARY))
    return total


def _reachable_tie_is_absent(family: HazardFamily = PRIMARY, limit: int = 40) -> bool:
    """No reachable evidence state ties the two scores.  The tie posterior is
    derived from the family's own score algebra (for the primary family it
    sits at odds 7/17, while reachable odds are integer powers of the
    likelihood ratio 9; the prime-support argument is asserted in prose and
    checked here only over the scanned range)."""
    for z in range(-limit, limit + 1):
        score = _scores(posterior_s(z, family), family)
        if score[S] == score[L]:
            return False
    if family.aligned != family.misaligned:
        w_s = Fraction(HORIZON - DURATION[S])
        w_l = Fraction(HORIZON - DURATION[L])
        a, m = family.aligned, family.misaligned
        denominator = (w_s + w_l) * (a - m)
        tie_rho = (w_l * a - w_s * m) / denominator
        if 0 < tie_rho < 1:
            tie_odds = tie_rho / (1 - tie_rho)
            ratio = family.likelihood_ratio()
            if any(ratio**z == tie_odds for z in range(-limit, limit + 1)):
                return False
    return True


@dataclass(frozen=True)
class CertificateResult:
    terminal: Terminal
    commitment_table: tuple[tuple[int, Fraction, Fraction, Fraction], ...]
    greedy_table: tuple[tuple[int, Fraction], ...]
    information_table: tuple[tuple[int, Fraction, Fraction], ...]
    no_rescue_bound: Fraction
    invariants: tuple[tuple[str, bool], ...]

    def to_bytes(self) -> bytes:
        payload = {
            "binding": RAW_OUTPUT_BINDING,
            "commitment_value_vs_count_blind_S": [
                {
                    "T": T,
                    "V_CAL": _fraction(cal),
                    "V_CB": _fraction(cb),
                    "CAL_minus_CB": _fraction(cal - cb),
                }
                for T, cal, cb, _ in self.commitment_table
            ],
            "greedy": [
                {"T": T, "V_GREEDY": _fraction(value)} for T, value in self.greedy_table
            ],
            "information": [
                {"T": T, "G": _fraction(g), "N": _fraction(n)}
                for T, g, n in self.information_table
            ],
            "invariants": {name: passed for name, passed in self.invariants},
            "no_rescue_bound": _fraction(self.no_rescue_bound),
            "terminal": self.terminal.value,
        }
        return json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")


def run_certificate() -> CertificateResult:
    expected_cal = {
        0: Fraction(3),
        1: Fraction(86571, 20000),
        2: Fraction(2834139, 500000),
        3: Fraction(7011651, 1000000),
        4: Fraction(41791887, 5000000),
    }
    expected_g = {
        0: Fraction(0),
        1: Fraction(6571, 20000),
        2: Fraction(219139, 500000),
        3: Fraction(506651, 1000000),
        4: Fraction(2684887, 5000000),
    }
    expected_learning = {
        1: Fraction(0),
        2: Fraction(23, 100),
        3: Fraction(101, 200),
        4: Fraction(4107, 5000),
    }
    cal = {T: v_cal(T) for T in REGISTERED_T}
    passive = {T: v_passive(T) for T in REGISTERED_T}
    greedy = {T: v_greedy(T) for T in REGISTERED_T}
    blind = {T: v_cb(T) for T in REGISTERED_T}
    gross = {T: gross_information_value(T) for T in REGISTERED_T}
    laws = {kind: prefix_belief_law(kind) for kind in ("SSLL", "SSSS", "GREEDY")}
    bound = no_horizon_rescue_bound()

    tree_ok = True
    for T in REGISTERED_T:
        for schedule in (
            PREFIX_CAL + (None,) * T,
            PREFIX_PASSIVE + (None,) * T,
            (None,) * (4 + T),
        ):
            value, mass = full_tree_value(schedule)
            tree_ok = tree_ok and mass == 1 and value == _policy_value(schedule)

    hom = {
        "cal": {T: v_cal(T, HOMOGENEOUS) for T in REGISTERED_T},
        "passive": {T: v_passive(T, HOMOGENEOUS) for T in REGISTERED_T},
        "greedy": {T: v_greedy(T, HOMOGENEOUS) for T in REGISTERED_T},
        "cb": {T: v_cb(T, HOMOGENEOUS) for T in REGISTERED_T},
        "g": {T: gross_information_value(T, HOMOGENEOUS) for T in REGISTERED_T},
    }
    redraw = {
        "cal": {T: v_cal(T, reset_belief=True) for T in REGISTERED_T},
        "passive": {T: v_passive(T, reset_belief=True) for T in REGISTERED_T},
        "greedy": {T: v_greedy(T, reset_belief=True) for T in REGISTERED_T},
        "g": {T: gross_information_value(T, reset_belief=True) for T in REGISTERED_T},
    }
    severed = {T: v_cal_severed(T) for T in REGISTERED_T}
    regret_ok = all(
        gross[T] == cumulative_regret(T) - cumulative_regret(T, laws["SSLL"])
        for T in REGISTERED_T
    )
    cold_law = {(theta, 0): (PRIOR_S if theta == S else 1 - PRIOR_S) for theta in THETAS}
    oracle_nonnegative = all(
        T * max(reward(theta, action) for action in (S, L))
        - _value(theta, z, (None,) * T, PRIMARY)
        >= 0
        for T in REGISTERED_T
        for law in (cold_law, laws["SSLL"])
        for (theta, z) in law
    )

    invariants = (
        ("lemma1_action_equivalent_signals", all(
            PRIMARY.evidence_up(theta, S) == PRIMARY.evidence_up(theta, L)
            for theta in THETAS
        )),
        ("lemma2_posterior_law_coupling", laws["SSLL"] == laws["SSSS"] == laws["GREEDY"]),
        ("lemma3_passive_dominance", all(
            cal[T] - passive[T] == Fraction(-1) for T in REGISTERED_T
        )),
        ("lemma3_greedy_dominance", all(
            cal[T] - greedy[T] == Fraction(-9107, 5000) for T in REGISTERED_T
        )),
        ("lemma4_no_horizon_rescue", bound < 1),
        ("lemma4_regret_decomposition", regret_ok),
        ("lemma4_regret_nonnegative_pointwise", oracle_nonnegative),
        ("lemma4_partial_regret_paths_agree",
         _exact_partial_regret(TAIL_T0) == cumulative_regret(TAIL_T0)),
        ("lemma4_bound_dominates_prefix_horizons", all(
            cumulative_regret(T) <= bound for T in range(TAIL_T0 + 3)
        )),
        ("exact_cal_table", all(cal[T] == expected_cal[T] for T in REGISTERED_T)),
        ("exact_cb_table", all(blind[T] == 4 + T for T in REGISTERED_T)),
        ("exact_greedy_anchor", greedy[0] == Fraction(24107, 5000)),
        ("commitment_signs", tuple(
            (cal[T] - blind[T] > 0) for T in (1, 2, 3, 4)
        ) == (False, False, True, True)),
        ("exact_information_table", all(
            gross[T] == expected_g[T] and gross[T] - 1 < 0 for T in REGISTERED_T
        )),
        ("decision_phase_learning_table", all(
            w_from_belief(0, T) - T == expected_learning[T] for T in (1, 2, 3, 4)
        )),
        ("full_tree_cross_check", tree_ok),
        ("homogeneous_boundary_corrected", all(
            hom["cal"][T] == 3 + T
            and hom["cb"][T] == hom["greedy"][T] == hom["passive"][T] == 4 + T
            and hom["g"][T] == 0
            for T in REGISTERED_T
        )),
        ("independent_redraw_boundary_corrected", all(
            redraw["cal"][T] == 3 + T
            and redraw["passive"][T] == redraw["greedy"][T] == 4 + T
            and redraw["g"][T] == 0
            for T in REGISTERED_T
        )),
        ("severance_boundary_ties_g", all(
            cal[T] - severed[T] == gross[T] for T in REGISTERED_T
        )),
        ("tie_unreachable", _reachable_tie_is_absent()),
        ("greedy_rule_is_sign_rule", all(
            rule_action(z, PRIMARY) == (S if z >= 0 else L) for z in range(-12, 13)
        )),
        ("no_identity_fields", all(
            "partner" not in field.name and "cell" not in field.name
            and "owner" not in field.name and "roster" not in field.name
            for dataclass_type in (HazardFamily, CertificateResult)
            for field in fields(dataclass_type)
        )),
        ("ceiling_containment", cumulative_regret(TAIL_T0) <= Fraction(5, 8) <= bound),
    )
    passed = all(value for _, value in invariants)
    return CertificateResult(
        terminal=Terminal.PARK if passed else Terminal.DISCREPANCY,
        commitment_table=tuple(
            (T, cal[T], blind[T], cal[T] - blind[T]) for T in REGISTERED_T
        ),
        greedy_table=tuple((T, greedy[T]) for T in REGISTERED_T),
        information_table=tuple((T, gross[T], gross[T] - 1) for T in REGISTERED_T),
        no_rescue_bound=bound,
        invariants=invariants,
    )


def _fraction(value: Fraction) -> str:
    return (
        str(value.numerator)
        if value.denominator == 1
        else f"{value.numerator}/{value.denominator}"
    )


if __name__ == "__main__":
    result = run_certificate()
    print(result.to_bytes().decode("ascii"))
