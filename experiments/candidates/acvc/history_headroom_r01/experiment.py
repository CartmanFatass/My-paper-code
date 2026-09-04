"""Exact finite-horizon ACVC history-headroom calculation."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import time
from typing import Any


OBJECT_ID = "ACVC-A-RECON-HISTORY-HEADROOM-R01"
EVIDENCE_CLASS = "A/RECON"
FORMAL_HORIZON = 12
TOY_HORIZON = 3
WALL_CAP_SECONDS = 120.0
RSS_CAP_BYTES = 3 * 1024 * 1024 * 1024 // 2
ADMISSION_FLOOR_BYTES = 4 * 1024 * 1024 * 1024

CALIBRATED = "CALIBRATED"
UNINFORMATIVE = "UNINFORMATIVE"
REGIMES = (CALIBRATED, UNINFORMATIVE)
EXECUTE = "EXECUTE"
PROBE = "PROBE"
VETO = "VETO"
ACTIONS = (EXECUTE, PROBE, VETO)
CONFIDENCES = (Fraction(7, 10), Fraction(9, 10))
AGES = (0, 1, 2)
P_UNSAFE_ISSUANCE = Fraction(3, 25)
P_REGIME = Fraction(1, 2)
P_CONFIDENCE_AGE = Fraction(1, 6)


def rational(value: Fraction) -> dict[str, int | str]:
    """Encode one exact value with a high-precision decimal rendering."""
    with localcontext() as context:
        context.prec = 32
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": format(decimal, ".24g"),
    }


def _reward(action: str, unsafe: int) -> Fraction:
    if action == EXECUTE:
        return Fraction(-4 if unsafe else 1)
    if action == PROBE:
        return Fraction(-3, 5) if unsafe else Fraction(2, 5)
    return Fraction(0)


def likelihood(regime: str, verdict: int, unsafe: int, confidence: Fraction, age: int) -> Fraction:
    """Return exact P(verdict,current truth | q, age, regime)."""
    total = Fraction(0)
    for issuance in (0, 1):
        p_x = P_UNSAFE_ISSUANCE if issuance else 1 - P_UNSAFE_ISSUANCE
        if regime == CALIBRATED:
            p_b = confidence if verdict == issuance else 1 - confidence
        else:
            p_b = Fraction(1, 2)
        persistence = Fraction(4, 5) ** age
        p_y_unsafe = Fraction(1, 2) + (Fraction(issuance) - Fraction(1, 2)) * persistence
        p_y = p_y_unsafe if unsafe else 1 - p_y_unsafe
        total += p_x * p_b * p_y
    return total


def marginal_verdict(regime: str, verdict: int, confidence: Fraction) -> Fraction:
    """Return exact P(verdict | q, regime), independent of age."""
    return sum(
        (P_UNSAFE_ISSUANCE if issuance else 1 - P_UNSAFE_ISSUANCE)
        * (
            (confidence if verdict == issuance else 1 - confidence)
            if regime == CALIBRATED else Fraction(1, 2)
        )
        for issuance in (0, 1)
    )


def posterior_after_frame(belief: Fraction, verdict: int, confidence: Fraction) -> Fraction:
    calibrated = belief * marginal_verdict(CALIBRATED, verdict, confidence)
    uninformative = (1 - belief) * marginal_verdict(UNINFORMATIVE, verdict, confidence)
    return calibrated / (calibrated + uninformative)


def posterior_after_reveal(
    belief: Fraction, verdict: int, unsafe: int, confidence: Fraction, age: int,
) -> Fraction:
    calibrated = belief * likelihood(CALIBRATED, verdict, unsafe, confidence, age)
    uninformative = (1 - belief) * likelihood(
        UNINFORMATIVE, verdict, unsafe, confidence, age,
    )
    return calibrated / (calibrated + uninformative)


def current_unsafe_probability(
    belief: Fraction, verdict: int, confidence: Fraction, age: int,
) -> Fraction:
    numerator = (
        belief * likelihood(CALIBRATED, verdict, 1, confidence, age)
        + (1 - belief) * likelihood(UNINFORMATIVE, verdict, 1, confidence, age)
    )
    denominator = (
        belief * marginal_verdict(CALIBRATED, verdict, confidence)
        + (1 - belief) * marginal_verdict(UNINFORMATIVE, verdict, confidence)
    )
    return numerator / denominator


def det_cf_action(verdict: int, confidence: Fraction, age: int) -> str:
    """Byte-semantic exact counterpart of the unchanged R01 DET-CF formula."""
    accuracy = (confidence + Fraction(1, 2)) / 2
    if verdict:
        p_issue = P_UNSAFE_ISSUANCE * accuracy / (
            P_UNSAFE_ISSUANCE * accuracy
            + (1 - P_UNSAFE_ISSUANCE) * (1 - accuracy)
        )
    else:
        p_issue = P_UNSAFE_ISSUANCE * (1 - accuracy) / (
            P_UNSAFE_ISSUANCE * (1 - accuracy)
            + (1 - P_UNSAFE_ISSUANCE) * accuracy
        )
    p_current = Fraction(1, 2) + (p_issue - Fraction(1, 2)) * Fraction(4, 5) ** age
    values = (1 - 5 * p_current, Fraction(2, 5) - p_current, Fraction(0))
    return ACTIONS[max(range(3), key=lambda index: values[index])]


@dataclass(frozen=True)
class Decision:
    frame_belief: Fraction
    reveal_beliefs: tuple[Fraction, Fraction]
    unsafe_probability: Fraction
    q_values: tuple[Fraction, Fraction, Fraction]
    action: str


class ExactSolver:
    """Exact two-regime alpha-vector Bellman recursion.

    The upper envelope removes only lines that are exactly dominated on the full
    belief interval.  It is an algebraic representation of the complete policy
    recursion, not a posterior grid or approximate pruning rule.
    """

    def __init__(self) -> None:
        self.alpha_vectors: dict[int, tuple[tuple[Fraction, Fraction], ...]] = {
            0: ((Fraction(0), Fraction(0)),),
        }
        self.decisions: dict[tuple[int, Fraction, int, Fraction, int], Decision] = {}
        self.queried_beliefs_by_horizon: dict[int, set[Fraction]] = {}
        self.backup_counts: dict[int, dict[str, int]] = {}

    @staticmethod
    def _upper_envelope(
        points: list[tuple[Fraction, Fraction]] | tuple[tuple[Fraction, Fraction], ...],
    ) -> tuple[tuple[Fraction, Fraction], ...]:
        """Keep exactly the lines optimal for some pi in [0,1]."""
        by_slope: dict[Fraction, tuple[Fraction, Fraction]] = {}
        for uninformative, calibrated in set(points):
            slope = calibrated - uninformative
            current = by_slope.get(slope)
            if current is None or uninformative > current[0]:
                by_slope[slope] = (uninformative, calibrated)
        lines = sorted(by_slope.values(), key=lambda point: point[1] - point[0])
        hull: list[tuple[Fraction, Fraction]] = []
        starts: list[Fraction | None] = []
        for point in lines:
            slope = point[1] - point[0]
            start: Fraction | None = None
            while hull:
                previous = hull[-1]
                previous_slope = previous[1] - previous[0]
                start = (previous[0] - point[0]) / (slope - previous_slope)
                if len(hull) == 1 or starts[-1] is None or start > starts[-1]:
                    break
                hull.pop()
                starts.pop()
            if not hull:
                start = None
            hull.append(point)
            starts.append(start)
        kept = []
        for index, point in enumerate(hull):
            start = starts[index]
            end = starts[index + 1] if index + 1 < len(starts) else None
            if (end is None or end >= 0) and (start is None or start <= 1):
                kept.append(point)
        return tuple(kept)

    @classmethod
    def _cross_sum(
        cls, left: tuple[tuple[Fraction, Fraction], ...],
        right: tuple[tuple[Fraction, Fraction], ...],
    ) -> tuple[tuple[Fraction, Fraction], ...]:
        """Exact Minkowski sum of two ordered upper envelopes."""
        def transition(
            points: tuple[tuple[Fraction, Fraction], ...], index: int,
        ) -> Fraction | None:
            if index + 1 >= len(points):
                return None
            current, following = points[index], points[index + 1]
            current_slope = current[1] - current[0]
            following_slope = following[1] - following[0]
            return (current[0] - following[0]) / (following_slope - current_slope)

        left_index = right_index = 0
        sums = [(left[0][0] + right[0][0], left[0][1] + right[0][1])]
        while left_index + 1 < len(left) or right_index + 1 < len(right):
            left_transition = transition(left, left_index)
            right_transition = transition(right, right_index)
            if right_transition is None or (
                left_transition is not None and left_transition < right_transition
            ):
                left_index += 1
            elif left_transition is None or right_transition < left_transition:
                right_index += 1
            else:
                left_index += 1
                right_index += 1
            sums.append((
                left[left_index][0] + right[right_index][0],
                left[left_index][1] + right[right_index][1],
            ))
        return cls._upper_envelope(sums)

    def _observation_vectors(
        self, previous: tuple[tuple[Fraction, Fraction], ...],
        verdict: int, confidence: Fraction, age: int,
    ) -> tuple[tuple[Fraction, Fraction], ...]:
        veto = tuple((
            marginal_verdict(UNINFORMATIVE, verdict, confidence) * alpha_u,
            marginal_verdict(CALIBRATED, verdict, confidence) * alpha_c,
        ) for alpha_u, alpha_c in previous)
        actions = [self._upper_envelope(veto)]
        for action in (EXECUTE, PROBE):
            revealed = []
            for unsafe in (0, 1):
                reward = _reward(action, unsafe)
                revealed.append(self._upper_envelope(tuple((
                    likelihood(UNINFORMATIVE, verdict, unsafe, confidence, age)
                    * (reward + alpha_u),
                    likelihood(CALIBRATED, verdict, unsafe, confidence, age)
                    * (reward + alpha_c),
                ) for alpha_u, alpha_c in previous)))
            actions.append(self._cross_sum(revealed[0], revealed[1]))
        return self._upper_envelope(tuple(point for action in actions for point in action))

    def _ensure(self, remaining: int) -> None:
        for current in range(1, remaining + 1):
            if current in self.alpha_vectors:
                continue
            previous = self.alpha_vectors[current - 1]
            combined = ((Fraction(0), Fraction(0)),)
            local_total = 0
            max_local = 0
            cross_candidates = 0
            for confidence in CONFIDENCES:
                for age in AGES:
                    for verdict in (0, 1):
                        local = self._observation_vectors(
                            previous, verdict, confidence, age,
                        )
                        local = tuple((
                            P_CONFIDENCE_AGE * alpha_u,
                            P_CONFIDENCE_AGE * alpha_c,
                        ) for alpha_u, alpha_c in local)
                        local_total += len(local)
                        max_local = max(max_local, len(local))
                        cross_candidates += len(combined) * len(local)
                        combined = self._cross_sum(combined, local)
            self.alpha_vectors[current] = combined
            self.backup_counts[current] = {
                "previous_alpha_vectors": len(previous),
                "observation_local_alpha_vectors_sum": local_total,
                "maximum_observation_local_alpha_vectors": max_local,
                "cross_sum_candidates_before_exact_envelopes": cross_candidates,
                "retained_alpha_vectors": len(combined),
            }

    def value(self, remaining: int, belief: Fraction) -> Fraction:
        self._ensure(remaining)
        self.queried_beliefs_by_horizon.setdefault(remaining, set()).add(belief)
        return max(
            (1 - belief) * alpha_u + belief * alpha_c
            for alpha_u, alpha_c in self.alpha_vectors[remaining]
        )

    def decision(
        self, remaining: int, belief: Fraction, verdict: int,
        confidence: Fraction, age: int,
    ) -> Decision:
        if remaining <= 0:
            raise ValueError("a decision needs at least one remaining opportunity")
        key = (remaining, belief, verdict, confidence, age)
        cached = self.decisions.get(key)
        if cached is not None:
            return cached
        frame_belief = posterior_after_frame(belief, verdict, confidence)
        reveal_beliefs = tuple(
            posterior_after_reveal(belief, verdict, unsafe, confidence, age)
            for unsafe in (0, 1)
        )
        p_unsafe = current_unsafe_probability(belief, verdict, confidence, age)
        probabilities = (1 - p_unsafe, p_unsafe)
        execute = sum(
            probabilities[unsafe]
            * (_reward(EXECUTE, unsafe) + self.value(remaining - 1, reveal_beliefs[unsafe]))
            for unsafe in (0, 1)
        )
        probe = sum(
            probabilities[unsafe]
            * (_reward(PROBE, unsafe) + self.value(remaining - 1, reveal_beliefs[unsafe]))
            for unsafe in (0, 1)
        )
        veto = self.value(remaining - 1, frame_belief)
        q_values = (execute, probe, veto)
        action = ACTIONS[max(range(3), key=lambda index: q_values[index])]
        result = Decision(frame_belief, reveal_beliefs, p_unsafe, q_values, action)
        self.decisions[key] = result
        return result


def transition_belief(decision: Decision, action: str, unsafe: int) -> Fraction:
    """Apply the information boundary; VETO never inserts truth."""
    return decision.frame_belief if action == VETO else decision.reveal_beliefs[unsafe]


HistoryEvent = tuple[int, Fraction, int, int, int]


@dataclass(frozen=True)
class Representative:
    history: tuple[HistoryEvent, ...]
    positive_mass_lower_bound: Fraction


def _empty_totals() -> dict[str, Any]:
    return {
        "return": Fraction(0),
        "actions": {action: Fraction(0) for action in ACTIONS},
        "unsafe_opportunities": Fraction(0),
        "safe_opportunities": Fraction(0),
        "unsafe_execute": Fraction(0),
        "probe_count": Fraction(0),
        "vetoed_safe": Fraction(0),
        "clean_loss": Fraction(0),
        "regime_return": {regime: Fraction(0) for regime in REGIMES},
    }


def _encoded_policy_metrics(totals: dict[str, Any], horizon: int) -> dict[str, Any]:
    unsafe_rate = totals["unsafe_execute"] / totals["unsafe_opportunities"]
    clean_loss = totals["clean_loss"] / totals["safe_opportunities"]
    return {
        "expected_return": rational(totals["return"]),
        "action_rates": {
            action: rational(totals["actions"][action] / horizon) for action in ACTIONS
        },
        "regime_stratified_expected_return": {
            regime: rational(totals["regime_return"][regime] / P_REGIME)
            for regime in REGIMES
        },
        "unsafe_execution_rate": rational(unsafe_rate),
        "clean_opportunity_loss": rational(clean_loss),
        "native_consequences": {
            "expected_unsafe_opportunities": rational(totals["unsafe_opportunities"]),
            "expected_safe_opportunities": rational(totals["safe_opportunities"]),
            "expected_unsafe_direct_executions": rational(totals["unsafe_execute"]),
            "expected_probe_expenditure_count": rational(totals["probe_count"]),
            "expected_vetoed_safe_service_count": rational(totals["vetoed_safe"]),
            "expected_clean_loss_numerator": rational(totals["clean_loss"]),
        },
        "_unsafe_execution_rate": unsafe_rate,
        "_clean_opportunity_loss": clean_loss,
        "_expected_return": totals["return"],
    }


def _history_json(history: tuple[HistoryEvent, ...]) -> list[dict[str, Any]]:
    rows = []
    for verdict, confidence, age, action_index, revealed_truth in history:
        rows.append({
            "verdict": verdict,
            "confidence": rational(confidence),
            "age": age,
            "action": ACTIONS[action_index],
            "revealed_truth": None if revealed_truth < 0 else revealed_truth,
        })
    return rows


def evaluate_history_policy(solver: ExactSolver, horizon: int) -> dict[str, Any]:
    """Forward-integrate treatment reachability, metrics, and a legal witness."""
    occupancy: dict[tuple[str, Fraction], Fraction] = {
        (regime, Fraction(1, 2)): P_REGIME for regime in REGIMES
    }
    representatives: dict[tuple[str, Fraction], Representative] = {
        key: Representative((), mass) for key, mass in occupancy.items()
    }
    totals = _empty_totals()
    disagreement_count = Fraction(0)
    disagreement_advantage = Fraction(0)
    normalization = []
    witness_candidate: tuple[Any, ...] | None = None
    witness_data: tuple[Any, ...] | None = None

    for step in range(horizon):
        remaining = horizon - step
        start_mass = sum(occupancy.values(), Fraction(0))
        receiver_representatives: dict[Fraction, Representative] = {}
        for (regime, belief), representative in representatives.items():
            current = receiver_representatives.get(belief)
            if current is None or representative.history < current.history:
                receiver_representatives[belief] = representative
        for verdict in (0, 1):
            for confidence in CONFIDENCES:
                for age in AGES:
                    choices = []
                    for belief, representative in receiver_representatives.items():
                        decision = solver.decision(remaining, belief, verdict, confidence, age)
                        choices.append((representative.history, belief, decision.action, representative))
                    for left_index, left in enumerate(choices):
                        for right in choices[left_index + 1:]:
                            if left[2] == right[2]:
                                continue
                            first, second = (left, right) if left[0] <= right[0] else (right, left)
                            candidate = (step, verdict, confidence, age, first[0], second[0])
                            if witness_candidate is None or candidate < witness_candidate:
                                witness_candidate = candidate
                                witness_data = (step, verdict, confidence, age, first, second)

        next_occupancy: dict[tuple[str, Fraction], Fraction] = {}
        next_representatives: dict[tuple[str, Fraction], Representative] = {}
        event_mass = Fraction(0)
        for (regime, belief), state_mass in occupancy.items():
            representative = representatives[(regime, belief)]
            for confidence in CONFIDENCES:
                for age in AGES:
                    for verdict in (0, 1):
                        decision = solver.decision(remaining, belief, verdict, confidence, age)
                        det_action = det_cf_action(verdict, confidence, age)
                        for unsafe in (0, 1):
                            mass = (
                                state_mass * P_CONFIDENCE_AGE
                                * likelihood(regime, verdict, unsafe, confidence, age)
                            )
                            event_mass += mass
                            action = decision.action
                            reward = _reward(action, unsafe)
                            totals["return"] += mass * reward
                            totals["actions"][action] += mass
                            totals["regime_return"][regime] += mass * reward
                            totals["unsafe_opportunities" if unsafe else "safe_opportunities"] += mass
                            totals["unsafe_execute"] += mass * int(unsafe == 1 and action == EXECUTE)
                            totals["probe_count"] += mass * int(action == PROBE)
                            totals["vetoed_safe"] += mass * int(unsafe == 0 and action == VETO)
                            if not unsafe:
                                totals["clean_loss"] += mass * (1 - reward)
                            if action != det_action:
                                disagreement_count += mass
                                det_index = ACTIONS.index(det_action)
                                disagreement_advantage += mass * (
                                    decision.q_values[ACTIONS.index(action)]
                                    - decision.q_values[det_index]
                                )
                            next_belief = transition_belief(decision, action, unsafe)
                            next_key = (regime, next_belief)
                            next_occupancy[next_key] = next_occupancy.get(next_key, Fraction(0)) + mass
                            revealed = unsafe if action != VETO else -1
                            event: HistoryEvent = (
                                verdict, confidence, age, ACTIONS.index(action), revealed,
                            )
                            path = Representative(
                                representative.history + (event,),
                                representative.positive_mass_lower_bound
                                * P_CONFIDENCE_AGE
                                * likelihood(regime, verdict, unsafe, confidence, age),
                            )
                            existing = next_representatives.get(next_key)
                            if existing is None or path.history < existing.history:
                                next_representatives[next_key] = path
        end_mass = sum(next_occupancy.values(), Fraction(0))
        if start_mass != 1 or event_mass != 1 or end_mass != 1:
            raise ArithmeticError("forward probability did not normalize exactly")
        normalization.append({
            "opportunity_index": step,
            "start_mass": rational(start_mass),
            "event_mass": rational(event_mass),
            "end_mass": rational(end_mass),
            "reachable_joint_regime_belief_states": len(occupancy),
            "reachable_receiver_beliefs": len({belief for _, belief in occupancy}),
        })
        occupancy = next_occupancy
        representatives = next_representatives

    metrics = _encoded_policy_metrics(totals, horizon)
    disagreement_mass = disagreement_count / horizon
    witness: dict[str, Any] | None = None
    if witness_data is not None:
        step, verdict, confidence, age, first, second = witness_data
        witness = {
            "opportunity_index": step,
            "identical_current_fields": {
                "verdict": verdict, "confidence": rational(confidence), "age": age,
            },
            "first": {
                "prior_visible_history": _history_json(first[0]),
                "belief": rational(first[1]),
                "action": first[2],
                "positive_mass_lower_bound": rational(first[3].positive_mass_lower_bound),
            },
            "second": {
                "prior_visible_history": _history_json(second[0]),
                "belief": rational(second[1]),
                "action": second[2],
                "positive_mass_lower_bound": rational(second[3].positive_mass_lower_bound),
            },
        }
    metrics.update({
        "disagreement": {
            "expected_count_per_episode": rational(disagreement_count),
            "opportunity_mass": rational(disagreement_mass),
            "probability_weighted_q_advantage_per_episode": rational(disagreement_advantage),
            "probability_weighted_q_advantage_per_opportunity": rational(
                disagreement_advantage / horizon,
            ),
            "conditional_mean_q_advantage": (
                rational(disagreement_advantage / disagreement_count)
                if disagreement_count else None
            ),
        },
        "history_action_witness": witness,
        "no_witness_certificate": None if witness is not None else {
            "exact": True,
            "checked_all_positive_mass_reachable_beliefs_and_current_frames": True,
        },
        "forward_probability_normalization": normalization,
    })
    return metrics


def evaluate_det_cf(horizon: int) -> dict[str, Any]:
    totals = _empty_totals()
    one_step_mass = Fraction(0)
    for regime in REGIMES:
        for confidence in CONFIDENCES:
            for age in AGES:
                for verdict in (0, 1):
                    action = det_cf_action(verdict, confidence, age)
                    for unsafe in (0, 1):
                        mass = (
                            P_REGIME * P_CONFIDENCE_AGE
                            * likelihood(regime, verdict, unsafe, confidence, age)
                        )
                        one_step_mass += mass
                        scaled = mass * horizon
                        reward = _reward(action, unsafe)
                        totals["return"] += scaled * reward
                        totals["actions"][action] += scaled
                        totals["regime_return"][regime] += scaled * reward
                        totals["unsafe_opportunities" if unsafe else "safe_opportunities"] += scaled
                        totals["unsafe_execute"] += scaled * int(unsafe == 1 and action == EXECUTE)
                        totals["probe_count"] += scaled * int(action == PROBE)
                        totals["vetoed_safe"] += scaled * int(unsafe == 0 and action == VETO)
                        if not unsafe:
                            totals["clean_loss"] += scaled * (1 - reward)
    if one_step_mass != 1:
        raise ArithmeticError("DET-CF one-step probability did not normalize exactly")
    metrics = _encoded_policy_metrics(totals, horizon)
    metrics["probability_normalization"] = {
        "one_step_mass": rational(one_step_mass),
        "episode_opportunity_mass": rational(one_step_mass * horizon),
    }
    return metrics


BRANCH_MAPPINGS = {
    "HR-X / NO_OBSERVATION": "Outcome-blind A/RECON repair only; no learner and no scientific polarity.",
    "HR-A / MATERIAL_COMPATIBLE_HEADROOM": (
        "Admit but do not automatically launch one B/EXPLORE learner-competence object."
    ),
    "HR-B / MATERIAL_HEADROOM_ONLY_WITH_HARM_TRADEOFF": (
        "Park the algorithm line pending an independently accepted objective or consequence envelope."
    ),
    "HR-C / SUBMATERIAL_HEADROOM": "Close the R01 host learner target and park ACVC.",
    "HR-D / NO_ACTIONABLE_HEADROOM": (
        "Close the uncertain/delayed R01 host family and park ACVC at its local boundary."
    ),
}


def apply_result_rule(
    *, delta: Fraction, disagreement_mass: Fraction,
    treatment_unsafe: Fraction, det_unsafe: Fraction,
    treatment_clean_loss: Fraction, det_clean_loss: Fraction,
    integrity_failures: tuple[str, ...] = (),
) -> dict[str, Any]:
    failures = list(integrity_failures)
    if delta < 0:
        failures.append("HIST-BAYES-DP scored below DET-CF")
    if failures:
        branch = "HR-X / NO_OBSERVATION"
    elif delta >= Fraction(1, 4) and disagreement_mass > 0:
        harm_compatible = (
            treatment_unsafe <= det_unsafe + Fraction(1, 50)
            and treatment_clean_loss <= det_clean_loss + Fraction(1, 20)
        )
        branch = (
            "HR-A / MATERIAL_COMPATIBLE_HEADROOM" if harm_compatible
            else "HR-B / MATERIAL_HEADROOM_ONLY_WITH_HARM_TRADEOFF"
        )
    elif delta >= Fraction(1, 10) and disagreement_mass > 0:
        branch = "HR-C / SUBMATERIAL_HEADROOM"
    else:
        branch = "HR-D / NO_ACTIONABLE_HEADROOM"
    return {
        "branch": branch,
        "integrity_failures": failures,
        "mapping": BRANCH_MAPPINGS[branch],
        "threshold_receipt": {
            "delta": rational(delta),
            "disagreement_mass": rational(disagreement_mass),
            "treatment_unsafe_execution_rate": rational(treatment_unsafe),
            "det_cf_unsafe_execution_rate": rational(det_unsafe),
            "treatment_clean_opportunity_loss": rational(treatment_clean_loss),
            "det_cf_clean_opportunity_loss": rational(det_clean_loss),
        },
    }


def _peak_rss_bytes() -> int | None:
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        psapi = ctypes.windll.psapi  # type: ignore[attr-defined]
        kernel32.GetCurrentProcess.argtypes = ()
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        ok = psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb,
        )
        return int(counters.PeakWorkingSetSize) if ok else None
    except (AttributeError, OSError):
        return None


def _launch_sha(project_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def _read_admission(path: str | Path) -> dict[str, Any]:
    admission = json.loads(Path(path).read_text(encoding="utf-8"))
    if not (
        admission.get("passed") is True
        and admission.get("physical_floor_pass") is True
        and admission.get("effective_floor_pass") is True
        and int(admission.get("available_physical_bytes", 0)) >= ADMISSION_FLOOR_BYTES
        and int(admission.get("effective_available_bytes", 0)) >= ADMISSION_FLOOR_BYTES
    ):
        raise RuntimeError("4 GiB physical/effective memory admission did not pass")
    return admission


def resource_integrity_failures(wall_seconds: float, peak_rss_bytes: int | None) -> tuple[str, ...]:
    failures = []
    if wall_seconds > WALL_CAP_SECONDS:
        failures.append("wall time exceeded 120 seconds")
    if peak_rss_bytes is not None and peak_rss_bytes > RSS_CAP_BYTES:
        failures.append("peak RSS exceeded 1.5 GiB")
    return tuple(failures)


def run_object(
    output_root: str | Path, *, admission_receipt: str | Path,
    argv: tuple[str, ...] = (), toy: bool = False,
) -> Path:
    """Calculate and publish one exact summary; formal execution is horizon twelve only."""
    started = time.perf_counter()
    admission = _read_admission(admission_receipt)
    project_root = Path(__file__).resolve().parents[4]
    launch_sha = _launch_sha(project_root)
    horizon = TOY_HORIZON if toy else FORMAL_HORIZON
    solver = ExactSolver()
    j_history = solver.value(horizon, Fraction(1, 2))
    history = evaluate_history_policy(solver, horizon)
    det = evaluate_det_cf(horizon)
    j_det = det.pop("_expected_return")
    history_return = history.pop("_expected_return")
    if history_return != j_history:
        raise ArithmeticError("Bellman and forward treatment return differ")
    delta = j_history - j_det
    treatment_unsafe = history.pop("_unsafe_execution_rate")
    treatment_clean = history.pop("_clean_opportunity_loss")
    det_unsafe = det.pop("_unsafe_execution_rate")
    det_clean = det.pop("_clean_opportunity_loss")
    disagreement_mass = Fraction(
        history["disagreement"]["opportunity_mass"]["numerator"],
        history["disagreement"]["opportunity_mass"]["denominator"],
    )
    wall_seconds = time.perf_counter() - started
    peak_rss = _peak_rss_bytes()
    resource_status = "measured" if peak_rss is not None else "resources_unmeasured"
    failures = resource_integrity_failures(wall_seconds, peak_rss)
    result_rule = None if toy else apply_result_rule(
        delta=delta,
        disagreement_mass=disagreement_mass,
        treatment_unsafe=treatment_unsafe,
        det_unsafe=det_unsafe,
        treatment_clean_loss=treatment_clean,
        det_clean_loss=det_clean,
        integrity_failures=failures,
    )
    alpha_counts = {
        str(remaining): len(solver.alpha_vectors[remaining])
        for remaining in range(horizon + 1)
    }
    queried_belief_counts = {
        str(remaining): len(solver.queried_beliefs_by_horizon.get(remaining, set()))
        for remaining in range(horizon + 1)
    }
    bellman_cross_sum_candidates = sum(
        row["cross_sum_candidates_before_exact_envelopes"]
        for row in solver.backup_counts.values()
    )
    forward_event_evaluations = sum(
        row["reachable_joint_regime_belief_states"]
        * len(CONFIDENCES) * len(AGES) * 2 * 2
        for row in history["forward_probability_normalization"]
    )
    work_units = bellman_cross_sum_candidates + forward_event_evaluations
    record = {
        "object_id": OBJECT_ID,
        "evidence_class": None if toy else EVIDENCE_CLASS,
        "complete": not toy and not failures,
        "result_bearing": not toy,
        "technical_only": toy,
        "toy": toy,
        "horizon": horizon,
        "no_rng": True,
        "one_process_one_thread": True,
        "launch_sha": launch_sha,
        "argv": list(argv),
        "admission": admission,
        "primary": {
            "J_H": rational(j_history),
            "J_D": rational(j_det),
            "Delta_H": rational(delta),
        },
        "policies": {"HIST-BAYES-DP": history, "DET-CF": det},
        "bellman": {
            "representation": "exact two-regime alpha-vector upper envelope",
            "exact_complete_policy_recursion": True,
            "approximate_pruning": False,
            "alpha_vector_counts_by_remaining_horizon": alpha_counts,
            "queried_belief_state_counts_by_remaining_horizon": queried_belief_counts,
            "backup_counts_by_remaining_horizon": {
                str(key): value for key, value in sorted(solver.backup_counts.items())
            },
            "decision_state_count": len(solver.decisions),
        },
        "information_boundary": {
            "policy_inputs": [
                "opportunity_index", "current_verdict", "current_confidence", "current_age",
                "prior_frames", "own_prior_actions", "legally_revealed_prior_truths",
            ],
            "hidden_regime_used_for_policy": False,
            "issuance_truth_used_for_policy": False,
            "unrevealed_current_truth_used_for_policy": False,
            "truth_inserted_after_veto": False,
            "veto_transition_uses_frame_posterior_only": True,
        },
        "result_rule": result_rule,
        "learner_exposure": "N/A",
        "cost_law": {
            "result_blind": True,
            "formula": (
                "work_units = exact Bellman state-frame evaluations + "
                "forward joint-state/frame/truth evaluations"
            ),
            "bellman_cross_sum_candidates": bellman_cross_sum_candidates,
            "forward_event_evaluations": forward_event_evaluations,
            "measured_work_units": work_units,
            "measured_wall_seconds_per_work_unit": wall_seconds / work_units,
        },
        "resources": {
            "wall_seconds": wall_seconds,
            "wall_cap_seconds": WALL_CAP_SECONDS,
            "wall_cap_pass": wall_seconds <= WALL_CAP_SECONDS,
            "peak_rss_bytes": peak_rss,
            "peak_rss_cap_bytes": RSS_CAP_BYTES,
            "peak_rss_cap_pass": None if peak_rss is None else peak_rss <= RSS_CAP_BYTES,
            "status": resource_status,
        },
    }
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    summary = output / "summary.json"
    summary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
