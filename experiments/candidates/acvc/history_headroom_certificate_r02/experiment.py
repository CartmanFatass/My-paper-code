"""Exact lower witness and regime-oracle upper certificate for ACVC R02."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
import json
import os
from pathlib import Path
import time
from typing import Any, Iterable, Sequence

if os.name != "nt":
    import resource


OBJECT_ID = "ACVC-A-RECON-HISTORY-HEADROOM-CERTIFICATE-R02"
EVIDENCE_CLASS = "A/RECON"
HORIZON = 12
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
P_CONTEXT_FIELDS = Fraction(1, 6)


def _rational512(offset: int) -> Fraction:
    """Return one irreducible rational with 512-bit numerator and denominator."""
    big = 1 << 511
    return Fraction(big + 2 * offset + 1, big)


def _weighted_rational512(weight: int, offset: int) -> Fraction:
    big = 1 << 511
    return Fraction(weight * big + 2 * offset + 1, big)


def encoded(value: Fraction) -> dict[str, int | str]:
    """Return the exact numerator/denominator and a display-only decimal."""
    with localcontext() as context:
        context.prec = 40
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": format(decimal, ".30g"),
    }


def reward(action: str, unsafe: int) -> Fraction:
    if action == EXECUTE:
        return Fraction(-4 if unsafe else 1)
    if action == PROBE:
        return Fraction(-3, 5) if unsafe else Fraction(2, 5)
    return Fraction(0)


def action_values(unsafe_probability: Fraction) -> tuple[Fraction, Fraction, Fraction]:
    return (
        1 - 5 * unsafe_probability,
        Fraction(2, 5) - unsafe_probability,
        Fraction(0),
    )


def bayes_action(unsafe_probability: Fraction) -> str:
    values = action_values(unsafe_probability)
    return action_from_values(values)


def action_from_values(values: Sequence[Fraction]) -> str:
    return ACTIONS[max(range(3), key=lambda index: values[index])]


def likelihood(
    regime: str, verdict: int, unsafe: int, confidence: Fraction, age: int,
) -> Fraction:
    """Exact L_r(b,y|q,d)."""
    total = Fraction(0)
    for issuance in (0, 1):
        p_x = P_UNSAFE_ISSUANCE if issuance else 1 - P_UNSAFE_ISSUANCE
        if regime == CALIBRATED:
            p_b = confidence if verdict == issuance else 1 - confidence
        else:
            p_b = Fraction(1, 2)
        persistence = Fraction(4, 5) ** age
        p_y_unsafe = Fraction(1, 2) + (Fraction(issuance) - Fraction(1, 2)) * persistence
        total += p_x * p_b * (p_y_unsafe if unsafe else 1 - p_y_unsafe)
    return total


def marginal_verdict(regime: str, verdict: int, confidence: Fraction) -> Fraction:
    return sum(
        likelihood(regime, verdict, unsafe, confidence, 0) for unsafe in (0, 1)
    )


def posterior_anchor(
    verdict: int, confidence: Fraction, age: int, unsafe: int | None,
) -> Fraction:
    if unsafe is None:
        c = marginal_verdict(CALIBRATED, verdict, confidence)
        u = marginal_verdict(UNINFORMATIVE, verdict, confidence)
    else:
        c = likelihood(CALIBRATED, verdict, unsafe, confidence, age)
        u = likelihood(UNINFORMATIVE, verdict, unsafe, confidence, age)
    return c / (c + u)


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


def det_cf_probability(verdict: int, confidence: Fraction, age: int) -> Fraction:
    """Exact counterpart of the unchanged R01 DET-CF formula."""
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
    return Fraction(1, 2) + (p_issue - Fraction(1, 2)) * Fraction(4, 5) ** age


def det_cf_action(verdict: int, confidence: Fraction, age: int) -> str:
    return bayes_action(det_cf_probability(verdict, confidence, age))


@dataclass(frozen=True, order=True)
class VisibleAnchor:
    verdict: int
    confidence: Fraction
    age: int
    action: str
    revealed_truth: int | None
    belief: Fraction

    def key(self) -> tuple[int, Fraction, int, int, int]:
        reveal = -1 if self.revealed_truth is None else self.revealed_truth
        return self.verdict, self.confidence, self.age, ACTIONS.index(self.action), reveal

    def json(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "confidence": encoded(self.confidence),
            "age": self.age,
            "action": self.action,
            "truth_revealed": self.revealed_truth is not None,
            "revealed_truth": self.revealed_truth,
            "anchor_belief": encoded(self.belief),
        }


def enumerate_anchor_mass() -> dict[tuple[str, VisibleAnchor], Fraction]:
    """Integrate first-step atoms without ever adding truth after VETO."""
    masses: dict[tuple[str, VisibleAnchor], Fraction] = {}
    for regime in REGIMES:
        for confidence in CONFIDENCES:
            for age in AGES:
                for verdict in (0, 1):
                    action = det_cf_action(verdict, confidence, age)
                    for unsafe in (0, 1):
                        atom = (
                            P_REGIME * P_CONTEXT_FIELDS
                            * likelihood(regime, verdict, unsafe, confidence, age)
                        )
                        visible_truth = unsafe if action != VETO else None
                        anchor = VisibleAnchor(
                            verdict, confidence, age, action, visible_truth,
                            posterior_anchor(verdict, confidence, age, visible_truth),
                        )
                        key = (regime, anchor)
                        masses[key] = masses.get(key, Fraction(0)) + atom
    return masses


def _empty_totals() -> dict[str, Any]:
    return {
        "return": Fraction(0),
        "actions": {action: Fraction(0) for action in ACTIONS},
        "regime_return": {regime: Fraction(0) for regime in REGIMES},
        "unsafe_opportunities": Fraction(0),
        "safe_opportunities": Fraction(0),
        "unsafe_execute": Fraction(0),
        "clean_loss": Fraction(0),
    }


def _add_event(
    totals: dict[str, Any], regime: str, mass: Fraction, action: str, unsafe: int,
) -> None:
    event_reward = reward(action, unsafe)
    totals["return"] += mass * event_reward
    totals["actions"][action] += mass
    totals["regime_return"][regime] += mass * event_reward
    totals["unsafe_opportunities" if unsafe else "safe_opportunities"] += mass
    totals["unsafe_execute"] += mass * int(unsafe == 1 and action == EXECUTE)
    if not unsafe:
        totals["clean_loss"] += mass * (1 - event_reward)


def _policy_summary(totals: dict[str, Any]) -> dict[str, Any]:
    unsafe_rate = totals["unsafe_execute"] / totals["unsafe_opportunities"]
    clean_rate = totals["clean_loss"] / totals["safe_opportunities"]
    return {
        "expected_return": encoded(totals["return"]),
        "action_rates": {
            action: encoded(totals["actions"][action] / HORIZON) for action in ACTIONS
        },
        "regime_stratified_return": {
            regime: encoded(totals["regime_return"][regime] / P_REGIME)
            for regime in REGIMES
        },
        "unsafe_execution_rate": encoded(unsafe_rate),
        "clean_opportunity_loss": encoded(clean_rate),
        "_return": totals["return"],
        "_unsafe_rate": unsafe_rate,
        "_clean_rate": clean_rate,
    }


def evaluate_det_cf() -> dict[str, Any]:
    totals = _empty_totals()
    one_step_mass = Fraction(0)
    for regime in REGIMES:
        for confidence in CONFIDENCES:
            for age in AGES:
                for verdict in (0, 1):
                    action = det_cf_action(verdict, confidence, age)
                    for unsafe in (0, 1):
                        mass = (
                            P_REGIME * P_CONTEXT_FIELDS
                            * likelihood(regime, verdict, unsafe, confidence, age)
                        )
                        one_step_mass += mass
                        _add_event(totals, regime, HORIZON * mass, action, unsafe)
    if one_step_mass != 1:
        raise ArithmeticError("DET-CF host law did not normalize")
    result = _policy_summary(totals)
    result["normalization"] = {
        "one_opportunity_mass": encoded(one_step_mass),
        "episode_opportunity_mass": encoded(one_step_mass * HORIZON),
        "action_rate_sum": encoded(sum(
            totals["actions"].values(), Fraction(0)
        ) / HORIZON),
    }
    return result


def evaluate_lower() -> dict[str, Any]:
    anchors = enumerate_anchor_mass()
    totals = _empty_totals()
    anchor_total = sum(anchors.values(), Fraction(0))
    by_visible: dict[VisibleAnchor, Fraction] = {}
    for (regime, anchor), mass in anchors.items():
        by_visible[anchor] = by_visible.get(anchor, Fraction(0)) + mass
        # Recover the first event reward by summing only truths consistent with this visible path.
        if anchor.revealed_truth is not None:
            _add_event(totals, regime, mass, anchor.action, anchor.revealed_truth)
        else:
            for unsafe in (0, 1):
                conditional = likelihood(
                    regime, anchor.verdict, unsafe, anchor.confidence, anchor.age,
                ) / marginal_verdict(regime, anchor.verdict, anchor.confidence)
                _add_event(totals, regime, mass * conditional, anchor.action, unsafe)

    contexts = tuple(
        (verdict, confidence, age)
        for verdict in (0, 1) for confidence in CONFIDENCES for age in AGES
    )
    det_actions = {
        context: det_cf_action(*context) for context in contexts
    }
    decisions: dict[tuple[VisibleAnchor, tuple[int, Fraction, int]], dict[str, Any]] = {}
    for anchor in sorted(by_visible, key=VisibleAnchor.key):
        for context in contexts:
            unsafe_probability = current_unsafe_probability(anchor.belief, *context)
            values = action_values(unsafe_probability)
            lower_action = action_from_values(values)
            det_action = det_actions[context]
            decisions[(anchor, context)] = {
                "unsafe_probability": unsafe_probability,
                "values": values,
                "lower_action": lower_action,
                "det_action": det_action,
                "advantage": (
                    values[ACTIONS.index(lower_action)] - values[ACTIONS.index(det_action)]
                ),
            }

    disagreements: list[dict[str, Any]] = []
    disagreement_per_step = Fraction(0)
    weighted_advantage_per_step = Fraction(0)
    for (regime, anchor), anchor_mass in anchors.items():
        for verdict, confidence, age in contexts:
            lower_action = decisions[(anchor, (verdict, confidence, age))]["lower_action"]
            for unsafe in (0, 1):
                mass = (
                    anchor_mass * P_CONTEXT_FIELDS
                    * likelihood(regime, verdict, unsafe, confidence, age)
                )
                _add_event(
                    totals, regime, (HORIZON - 1) * mass, lower_action, unsafe,
                )
    for anchor, anchor_mass in sorted(by_visible.items(), key=lambda row: row[0].key()):
        for verdict, confidence, age in contexts:
            frame_mass = sum(
                anchors.get((regime, anchor), Fraction(0))
                * P_CONTEXT_FIELDS
                * marginal_verdict(regime, verdict, confidence)
                for regime in REGIMES
            )
            decision = decisions[(anchor, (verdict, confidence, age))]
            lower_action = decision["lower_action"]
            det_action = decision["det_action"]
            if lower_action == det_action:
                continue
            advantage = decision["advantage"]
            disagreement_per_step += frame_mass
            weighted_advantage_per_step += frame_mass * advantage
            disagreements.append({
                "first_opportunity_history": anchor.json(),
                "later_current_context": {
                    "verdict": verdict, "confidence": encoded(confidence), "age": age,
                },
                "opportunity_indices": list(range(2, HORIZON + 1)),
                "positive_mass_per_opportunity": encoded(frame_mass),
                "expected_episode_count": encoded((HORIZON - 1) * frame_mass),
                "lower_action": lower_action,
                "forced_det_cf_action": det_action,
                "forced_det_cf_native_q_advantage": encoded(advantage),
                "weighted_advantage_per_opportunity": encoded(frame_mass * advantage),
            })

    witness_candidates: list[tuple[Any, ...]] = []
    visible = sorted(by_visible, key=VisibleAnchor.key)
    for left_index, left in enumerate(visible):
        for right in visible[left_index + 1:]:
            for verdict, confidence, age in contexts:
                context = (verdict, confidence, age)
                left_action = decisions[(left, context)]["lower_action"]
                right_action = decisions[(right, context)]["lower_action"]
                if left_action != right_action:
                    witness_candidates.append((
                        left.key(), right.key(), (verdict, confidence, age),
                        left, right, left_action, right_action,
                    ))
    witness = None
    if witness_candidates:
        _, _, context, left, right, left_action, right_action = min(witness_candidates)
        verdict, confidence, age = context
        witness = {
            "selection_order": "(left_visible_history,right_visible_history,current_context)",
            "left": left.json(),
            "right": right.json(),
            "identical_later_current_context": {
                "verdict": verdict, "confidence": encoded(confidence), "age": age,
            },
            "left_action": left_action,
            "right_action": right_action,
            "left_positive_mass": encoded(by_visible[left]),
            "right_positive_mass": encoded(by_visible[right]),
        }

    result = _policy_summary(totals)
    result.update({
        "anchor_histories": [
            {"history": anchor.json(), "positive_mass": encoded(mass)}
            for anchor, mass in sorted(by_visible.items(), key=lambda row: row[0].key())
        ],
        "disagreement": {
            "states": disagreements,
            "positive_state_count": len(disagreements) * (HORIZON - 1),
            "opportunity_mass": encoded(
                (HORIZON - 1) * disagreement_per_step / HORIZON
            ),
            "expected_count_per_episode": encoded(
                (HORIZON - 1) * disagreement_per_step
            ),
            "probability_weighted_forced_det_cf_advantage": encoded(
                (HORIZON - 1) * weighted_advantage_per_step
            ),
        },
        "history_action_witness": witness,
        "no_witness_certificate": None if witness else {
            "exact": True,
            "positive_anchor_histories_checked": len(visible),
            "later_contexts_checked_per_pair": len(contexts),
        },
        "normalization": {
            "first_atom_mass": encoded(anchor_total),
            "visible_anchor_mass": encoded(sum(by_visible.values(), Fraction(0))),
            "later_event_mass_per_opportunity": encoded(sum(
                anchor_mass * P_CONTEXT_FIELDS
                * likelihood(regime, verdict, unsafe, confidence, age)
                for (regime, _anchor), anchor_mass in anchors.items()
                for verdict, confidence, age in contexts for unsafe in (0, 1)
            )),
            "episode_opportunity_mass": encoded(
                totals["unsafe_opportunities"] + totals["safe_opportunities"]
            ),
            "action_rate_sum": encoded(sum(
                totals["actions"].values(), Fraction(0)
            ) / HORIZON),
        },
        "information_boundary": {
            "anchor_uses_only_first_opportunity": True,
            "later_frame_update_is_transient": True,
            "later_outcomes_change_anchor": False,
            "hidden_regime_used_for_action": False,
            "truth_inserted_after_veto": False,
        },
        "exact_lower_action_score_evaluations": len(by_visible) * len(contexts) * 3,
    })
    return result


@dataclass(frozen=True)
class Cell:
    label: str
    weight: Fraction
    unsafe_probability: Fraction
    gains: tuple[Fraction, Fraction, Fraction]
    unsafe: tuple[Fraction, Fraction, Fraction]
    clean_loss: tuple[Fraction, Fraction, Fraction]


def oracle_cells() -> tuple[Cell, ...]:
    cells = []
    for regime in REGIMES:
        for verdict in (0, 1):
            for confidence in CONFIDENCES:
                for age in AGES:
                    marginal = marginal_verdict(regime, verdict, confidence)
                    p = likelihood(regime, verdict, 1, confidence, age) / marginal
                    cells.append(Cell(
                        f"{regime}|b={verdict}|q={confidence}|d={age}",
                        P_REGIME * P_CONTEXT_FIELDS * marginal,
                        p,
                        action_values(p),
                        (p, Fraction(0), Fraction(0)),
                        (Fraction(0), Fraction(3, 5) * (1 - p), 1 - p),
                    ))
    return tuple(cells)


def _inverse(matrix: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    n = len(matrix)
    rows = [list(row) + [Fraction(int(i == j)) for j in range(n)]
            for i, row in enumerate(matrix)]
    for column in range(n):
        pivot = next(row for row in range(column, n) if rows[row][column])
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        rows[column] = [value / scale for value in rows[column]]
        for row in range(n):
            if row == column or not rows[row][column]:
                continue
            factor = rows[row][column]
            rows[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(rows[row], rows[column])
            ]
    return [row[n:] for row in rows]


def _mat_vec(matrix: Sequence[Sequence[Fraction]], vector: Sequence[Fraction]) -> list[Fraction]:
    return [sum((a * b for a, b in zip(row, vector)), Fraction(0)) for row in matrix]


def _simplex(
    matrix: list[list[Fraction]], rhs: list[Fraction], objective: list[Fraction],
    basis: list[int], entering: set[int], deadline: float | None,
) -> tuple[list[int], list[Fraction], list[Fraction], int]:
    iterations = 0
    while True:
        columns = [[matrix[row][column] for row in range(len(rhs))]
                   for column in basis]
        inverse = _inverse([list(row) for row in zip(*columns)])
        basic = _mat_vec(inverse, rhs)
        costs = [objective[column] for column in basis]
        dual = [sum((costs[i] * inverse[i][j] for i in range(len(rhs))), Fraction(0))
                for j in range(len(rhs))]
        nonbasic = sorted(entering.difference(basis))
        reduced = {
            column: objective[column] - sum(
                (dual[row] * matrix[row][column] for row in range(len(rhs))), Fraction(0)
            ) for column in nonbasic
        }
        eligible = [column for column in nonbasic if reduced[column] > 0]
        if not eligible:
            return basis, basic, dual, iterations
        enter = min(eligible)
        direction = _mat_vec(inverse, [row[enter] for row in matrix])
        ratios = [
            (basic[row] / direction[row], basis[row], row)
            for row in range(len(rhs)) if direction[row] > 0
        ]
        if not ratios:
            raise ArithmeticError("exact LP is unbounded")
        _, _, leave_row = min(ratios)
        basis[leave_row] = enter
        iterations += 1
        if deadline is not None and iterations % 8 == 0 and time.perf_counter() > deadline:
            raise TimeoutError("wall cap reached at an exact simplex pivot block")


def _exact_primal(
    cells: Sequence[Cell], caps: tuple[Fraction, Fraction], deadline: float | None,
) -> dict[str, Any]:
    count = len(cells)
    original = count * 3
    slack_u, slack_l = original, original + 1
    artificial_start = original + 2
    variables = artificial_start + count
    rows = count + 2
    matrix = [[Fraction(0) for _ in range(variables)] for _ in range(rows)]
    rhs = [cell.weight for cell in cells] + [caps[0], caps[1]]
    for index, cell in enumerate(cells):
        for action in range(3):
            column = 3 * index + action
            matrix[index][column] = Fraction(1)
            matrix[count][column] = cell.unsafe[action]
            matrix[count + 1][column] = cell.clean_loss[action]
        matrix[index][artificial_start + index] = Fraction(1)
    matrix[count][slack_u] = Fraction(1)
    matrix[count + 1][slack_l] = Fraction(1)
    basis = [artificial_start + index for index in range(count)] + [slack_u, slack_l]
    phase_one = [Fraction(0) for _ in range(variables)]
    for index in range(count):
        phase_one[artificial_start + index] = -1
    permitted = set(range(artificial_start))
    basis, basic, _, _ = _simplex(
        matrix, rhs, phase_one, basis, permitted, deadline,
    )
    if sum((phase_one[column] * value for column, value in zip(basis, basic)), Fraction(0)) != 0:
        raise ArithmeticError("upper program is infeasible")
    for row_index, variable in enumerate(tuple(basis)):
        if variable < artificial_start:
            continue
        columns = [[matrix[row][column] for row in range(rows)] for column in basis]
        inverse = _inverse([list(row) for row in zip(*columns)])
        replacement = None
        for column in sorted(permitted.difference(basis)):
            direction = _mat_vec(inverse, [row[column] for row in matrix])
            if direction[row_index] != 0:
                replacement = column
                break
        if replacement is None:
            raise ArithmeticError("could not remove a zero artificial variable")
        basis[row_index] = replacement
    objective = [Fraction(0) for _ in range(variables)]
    for index, cell in enumerate(cells):
        for action in range(3):
            objective[3 * index + action] = cell.gains[action]
    basis, basic, dual, _ = _simplex(
        matrix, rhs, objective, basis, permitted, deadline,
    )
    values = [Fraction(0) for _ in range(variables)]
    for column, value in zip(basis, basic):
        values[column] = value
    return {
        "values": values[:original],
        "dual": dual,
    }


def _tie_lines(cells: Sequence[Cell]) -> list[tuple[Fraction, Fraction, Fraction]]:
    lines = []
    for cell in cells:
        for left, right in ((0, 1), (0, 2), (1, 2)):
            lines.append((
                cell.unsafe[left] - cell.unsafe[right],
                cell.clean_loss[left] - cell.clean_loss[right],
                cell.gains[left] - cell.gains[right],
            ))
    return lines


def _dual_value(
    cells: Sequence[Cell], caps: tuple[Fraction, Fraction], point: tuple[Fraction, Fraction],
) -> Fraction:
    lam, mu = point
    return lam * caps[0] + mu * caps[1] + sum((
        cell.weight * max(
            cell.gains[action] - lam * cell.unsafe[action] - mu * cell.clean_loss[action]
            for action in range(3)
        ) for cell in cells
    ), Fraction(0))


def dual_candidate_search(
    cells: Sequence[Cell], caps: tuple[Fraction, Fraction], deadline: float | None,
) -> dict[str, Any]:
    lines = _tie_lines(cells)
    slots: list[tuple[Fraction, Fraction] | None] = [(Fraction(0), Fraction(0))]
    for a, b, c in lines:
        slots.append((c / a, Fraction(0)) if a and c / a >= 0 else None)
        slots.append((Fraction(0), c / b) if b and c / b >= 0 else None)
    for first in range(len(lines)):
        a1, b1, c1 = lines[first]
        for second in range(first + 1, len(lines)):
            a2, b2, c2 = lines[second]
            determinant = a1 * b2 - a2 * b1
            if not determinant:
                slots.append(None)
                continue
            lam = (c1 * b2 - c2 * b1) / determinant
            mu = (a1 * c2 - a2 * c1) / determinant
            slots.append((lam, mu) if lam >= 0 and mu >= 0 else None)
    best_point: tuple[Fraction, Fraction] | None = None
    best_value: Fraction | None = None
    valid = 0
    for index, point in enumerate(slots):
        workload_point = point if point is not None else (Fraction(0), Fraction(0))
        value = _dual_value(cells, caps, workload_point)
        if point is not None:
            valid += 1
            if (
                best_value is None or value < best_value
                or (value == best_value and (best_point is None or point < best_point))
            ):
                best_point, best_value = point, value
        if deadline is not None and (index + 1) % 64 == 0 and time.perf_counter() > deadline:
            raise TimeoutError("wall cap reached at a dual-candidate block")
    if best_point is None or best_value is None:
        raise ArithmeticError("dual candidate arrangement contained no nonnegative point")
    return {
        "point": best_point,
        "objective": best_value,
        "tie_line_count": len(lines),
        "candidate_slots": len(slots),
        "valid_nonnegative_candidates": valid,
        "exact_action_score_evaluations": len(slots) * len(cells) * 3,
    }


def solve_upper(
    cells: Sequence[Cell], caps: tuple[Fraction, Fraction], deadline: float | None,
) -> dict[str, Any]:
    candidate = dual_candidate_search(cells, caps, deadline)
    solved = _exact_primal(cells, caps, deadline)
    values: list[Fraction] = solved["values"]
    dual: list[Fraction] = solved["dual"]
    alpha, lam, mu = dual[:-2], dual[-2], dual[-1]
    primal_u = sum((
        values[3 * index + action] * cell.unsafe[action]
        for index, cell in enumerate(cells) for action in range(3)
    ), Fraction(0))
    primal_l = sum((
        values[3 * index + action] * cell.clean_loss[action]
        for index, cell in enumerate(cells) for action in range(3)
    ), Fraction(0))
    primal_objective = sum((
        values[3 * index + action] * cell.gains[action]
        for index, cell in enumerate(cells) for action in range(3)
    ), Fraction(0))
    dual_slacks = [
        alpha[index] + lam * cell.unsafe[action] + mu * cell.clean_loss[action]
        - cell.gains[action]
        for index, cell in enumerate(cells) for action in range(3)
    ]
    dual_objective = sum((
        cell.weight * alpha[index] for index, cell in enumerate(cells)
    ), Fraction(0)) + lam * caps[0] + mu * caps[1]
    cell_residuals = [
        sum(values[3 * index:3 * index + 3], Fraction(0)) - cell.weight
        for index, cell in enumerate(cells)
    ]
    variable_cs = [value * slack for value, slack in zip(values, dual_slacks)]
    resource_cs = (lam * (caps[0] - primal_u), mu * (caps[1] - primal_l))
    if any(cell_residuals) or any(value < 0 for value in values):
        raise ArithmeticError("exact primal certificate is infeasible")
    if primal_u > caps[0] or primal_l > caps[1]:
        raise ArithmeticError("exact primal harm constraint is infeasible")
    if lam < 0 or mu < 0 or any(slack < 0 for slack in dual_slacks):
        raise ArithmeticError("exact dual certificate is infeasible")
    if any(variable_cs) or any(resource_cs) or primal_objective != dual_objective:
        raise ArithmeticError("exact complementary slackness or objective equality failed")
    if candidate["objective"] != dual_objective:
        raise ArithmeticError("dual arrangement and exact simplex objectives differ")
    coefficient_table = []
    primal_rows = []
    dual_rows = []
    for index, cell in enumerate(cells):
        coefficient_table.append({
            "cell": cell.label,
            "weight": encoded(cell.weight),
            "unsafe_probability": encoded(cell.unsafe_probability),
            "actions": [{
                "action": ACTIONS[action],
                "gain": encoded(cell.gains[action]),
                "unsafe_numerator": encoded(cell.unsafe[action]),
                "clean_loss_numerator": encoded(cell.clean_loss[action]),
            } for action in range(3)],
        })
        primal_rows.append({
            "cell": cell.label,
            "action_mass": {
                ACTIONS[action]: encoded(values[3 * index + action]) for action in range(3)
            },
            "normalization_residual": encoded(cell_residuals[index]),
        })
        dual_rows.append({
            "cell": cell.label,
            "alpha": encoded(alpha[index]),
            "action_slacks": {
                ACTIONS[action]: encoded(dual_slacks[3 * index + action])
                for action in range(3)
            },
        })
    return {
        "per_opportunity_objective": primal_objective,
        "coefficient_table": coefficient_table,
        "primal": {
            "rows": primal_rows,
            "unsafe_numerator": encoded(primal_u),
            "unsafe_cap": encoded(caps[0]),
            "clean_loss_numerator": encoded(primal_l),
            "clean_loss_cap": encoded(caps[1]),
            "feasible": True,
            "objective": encoded(primal_objective),
        },
        "dual": {
            "rows": dual_rows,
            "unsafe_multiplier": encoded(lam),
            "clean_loss_multiplier": encoded(mu),
            "feasible": True,
            "objective": encoded(dual_objective),
        },
        "complementary_slackness": {
            "variable_products": [encoded(value) for value in variable_cs],
            "resource_products": [encoded(value) for value in resource_cs],
            "all_zero": True,
        },
        "equal_primal_dual_objective": True,
        "candidate_arrangement": {
            key: encoded(value) if isinstance(value, Fraction) else value
            for key, value in candidate.items() if key != "point"
        } | {
            "selected_multipliers": [encoded(value) for value in candidate["point"]],
        },
    }


def probability_checks(cells: Sequence[Cell]) -> dict[str, Any]:
    likelihood_rows = []
    for regime in REGIMES:
        for confidence in CONFIDENCES:
            for age in AGES:
                total = sum((
                    likelihood(regime, verdict, unsafe, confidence, age)
                    for verdict in (0, 1) for unsafe in (0, 1)
                ), Fraction(0))
                likelihood_rows.append({
                    "regime": regime, "confidence": encoded(confidence), "age": age,
                    "sum_b_y": encoded(total),
                })
    return {
        "likelihood_rows": likelihood_rows,
        "oracle_cell_weight_sum": encoded(sum((cell.weight for cell in cells), Fraction(0))),
        "all_exactly_normalized": all(
            row["sum_b_y"]["numerator"] == row["sum_b_y"]["denominator"]
            for row in likelihood_rows
        ) and sum((cell.weight for cell in cells), Fraction(0)) == 1,
    }


BRANCH_MAPPINGS = {
    "HC-X / NO_OBSERVATION": "Quarantine; outcome-blind repair only and no scientific polarity.",
    "HC-A / MATERIAL_COMPATIBLE_HEADROOM_WITNESS": (
        "Admit but do not launch one learner-competence B/EXPLORE object."
    ),
    "HC-C / MATERIAL_COMPATIBLE_HEADROOM_CERTIFIED_IMPOSSIBLE": (
        "Close the current host learner target and park ACVC at its local boundary."
    ),
    "HC-B / MATERIAL_NATIVE_WITNESS_OUTSIDE_ENVELOPE": (
        "Admit no learner; park pending an independently justified consequence envelope."
    ),
    "HC-D / CERTIFICATE_INTERVAL_UNRESOLVED": (
        "Admit no learner; park at the exact certificate dependency."
    ),
}


def learner_exposure() -> dict[str, int | str]:
    return {
        "trainable_parameter_count": 0,
        "initialization_l2": "N/A",
        "initialization_rms": "N/A",
        "initialization_scale": "N/A",
        "parameter_displacement_l2": 0,
        "parameter_displacement_rms": 0,
        "displacement_to_initialization": "N/A",
        "gradient_bearing_updates": 0,
        "optimizer_transitions": 0,
        "training_episodes": 0,
        "checkpoints": 0,
        "selection_exposure": 0,
    }


def apply_result_rule(
    *, delta_lower: Fraction, delta_upper: Fraction, lower_compatible: bool,
    disagreement_mass: Fraction, witness_exists: bool, aggregate_advantage: Fraction,
    integrity_failures: Iterable[str] = (),
) -> dict[str, Any]:
    failures = list(integrity_failures)
    if failures:
        branch = "HC-X / NO_OBSERVATION"
    elif (
        delta_lower >= Fraction(1, 4) and lower_compatible
        and disagreement_mass > 0 and witness_exists and aggregate_advantage > 0
    ):
        branch = "HC-A / MATERIAL_COMPATIBLE_HEADROOM_WITNESS"
    elif delta_upper < Fraction(1, 4):
        branch = "HC-C / MATERIAL_COMPATIBLE_HEADROOM_CERTIFIED_IMPOSSIBLE"
    elif (
        delta_upper >= Fraction(1, 4) and delta_lower >= Fraction(1, 4)
        and disagreement_mass > 0 and witness_exists and aggregate_advantage > 0
        and not lower_compatible
    ):
        branch = "HC-B / MATERIAL_NATIVE_WITNESS_OUTSIDE_ENVELOPE"
    else:
        branch = "HC-D / CERTIFICATE_INTERVAL_UNRESOLVED"
    return {
        "branch": branch,
        "integrity_failures": failures,
        "mapping": BRANCH_MAPPINGS[branch],
        "ordered_precedence": ["HC-X", "HC-A", "HC-C", "HC-B", "HC-D"],
    }


def _peak_rss_bytes() -> int | None:
    if os.name != "nt":
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # type: ignore[name-defined]
        return int(value * 1024)
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


def _read_admission(path: str | Path) -> dict[str, Any]:
    admission = json.loads(Path(path).read_text(encoding="utf-8"))
    if not (
        admission.get("passed") is True
        and int(admission.get("available_physical_bytes", 0)) >= ADMISSION_FLOOR_BYTES
        and int(admission.get("effective_available_bytes", 0)) >= ADMISSION_FLOOR_BYTES
    ):
        raise RuntimeError("fresh 4 GiB physical/effective memory admission did not pass")
    return admission


def _fraction(record: dict[str, Any]) -> Fraction:
    return Fraction(int(record["numerator"]), int(record["denominator"]))


def _write_summary(output_root: str | Path, record: dict[str, Any]) -> Path:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    summary = output / "summary.json"
    summary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _terminal_hc_x(
    *, error: TimeoutError | ArithmeticError, stage: str, launch_sha: str,
    argv: Sequence[str], admission_receipt: str | Path, admission: dict[str, Any],
    wall: float, peak: int | None, det: dict[str, Any] | None,
    lower: dict[str, Any] | None, upper: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "object_id": OBJECT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "result_bearing": True,
        "complete": False,
        "scientific_polarity": None,
        "terminal_reason": f"{type(error).__name__}: {error}",
        "arithmetic": "fractions.Fraction exact rational",
        "no_rng": True,
        "one_process_one_thread": True,
        "launch_sha": launch_sha,
        "argv": list(argv),
        "admission_receipt": {
            "path": str(Path(admission_receipt)),
            "record": admission,
        },
        "primary": {key: None for key in ("J_D", "J_L", "J_U", "Delta_L", "Delta_U")},
        "policies": {"DET-CF": det, "HIST-1UPDATE-CF": lower},
        "harm_compatibility": None,
        "REGIME-ORACLE-ENVELOPE": upper,
        "normalization_checks": None,
        "available_stage_counts": {
            "terminal_stage": stage,
            "det_cf_complete": det is not None,
            "lower_complete": lower is not None,
            "certificate_complete": upper is not None,
            "lower_action_score_evaluations": (
                lower.get("exact_lower_action_score_evaluations") if lower is not None else None
            ),
        },
        "static_work_counts": {
            "first_contexts": 12,
            "latent_first_step_atoms": 48,
            "maximum_visible_anchor_histories": 24,
            "later_contexts": 12,
            "oracle_cells": 24,
            "oracle_action_variables": 72,
            "normalization_equalities": 24,
            "harm_inequalities": 2,
            "dual_tie_lines": 72,
            "dual_candidate_slots": 2701,
        },
        "result_rule": {
            "branch": "HC-X / NO_OBSERVATION",
            "integrity_failures": [str(error)],
            "mapping": BRANCH_MAPPINGS["HC-X / NO_OBSERVATION"],
            "ordered_precedence": ["HC-X", "HC-A", "HC-C", "HC-B", "HC-D"],
        },
        "learner_exposure": learner_exposure(),
        "resources": {
            "wall_seconds": wall,
            "wall_cap_seconds": WALL_CAP_SECONDS,
            "peak_rss_bytes": peak,
            "peak_rss_cap_bytes": RSS_CAP_BYTES,
            "status": "measured" if peak is not None else "resources_unmeasured",
        },
    }


def run_result(
    output_root: str | Path, *, admission_receipt: str | Path, launch_sha: str,
    argv: Sequence[str],
) -> Path:
    """Execute the sole formal exact calculation and publish one summary."""
    admission = _read_admission(admission_receipt)
    started = time.perf_counter()
    deadline = started + WALL_CAP_SECONDS
    Path(output_root).mkdir(parents=True, exist_ok=True)
    stage = "DET-CF"
    det_public: dict[str, Any] | None = None
    lower_public: dict[str, Any] | None = None
    upper_public: dict[str, Any] | None = None
    try:
        det_public = evaluate_det_cf()
        j_det = det_public.pop("_return")
        det_unsafe = det_public.pop("_unsafe_rate")
        det_clean = det_public.pop("_clean_rate")
        stage = "HIST-1UPDATE-CF"
        lower_public = evaluate_lower()
        j_lower = lower_public.pop("_return")
        lower_unsafe = lower_public.pop("_unsafe_rate")
        lower_clean = lower_public.pop("_clean_rate")
        stage = "REGIME-ORACLE-ENVELOPE"
        cells = oracle_cells()
        unsafe_probability = sum((
            cell.weight * cell.unsafe_probability for cell in cells
        ), Fraction(0))
        safe_probability = 1 - unsafe_probability
        caps = (
            (det_unsafe + Fraction(1, 50)) * unsafe_probability,
            (det_clean + Fraction(1, 20)) * safe_probability,
        )
        upper_public = solve_upper(cells, caps, deadline)
        j_upper = HORIZON * upper_public.pop("per_opportunity_objective")
        stage = "INTEGRITY-AND-PUBLICATION"
        delta_lower, delta_upper = j_lower - j_det, j_upper - j_det
        disagreement_mass = _fraction(lower_public["disagreement"]["opportunity_mass"])
        aggregate_advantage = _fraction(
            lower_public["disagreement"]["probability_weighted_forced_det_cf_advantage"]
        )
        compatible = (
            lower_unsafe <= det_unsafe + Fraction(1, 50)
            and lower_clean <= det_clean + Fraction(1, 20)
        )
        checks = probability_checks(cells)
        if not checks["all_exactly_normalized"]:
            raise ArithmeticError("probability normalization failed")
        if j_upper < j_det:
            raise ArithmeticError("J_U is below J_D")
        if compatible and j_lower > j_upper:
            raise ArithmeticError("compatible J_L is above J_U")
    except (TimeoutError, ArithmeticError) as error:
        terminal = _terminal_hc_x(
            error=error, stage=stage, launch_sha=launch_sha, argv=argv,
            admission_receipt=admission_receipt, admission=admission,
            wall=time.perf_counter() - started, peak=_peak_rss_bytes(),
            det=det_public, lower=lower_public, upper=upper_public,
        )
        return _write_summary(output_root, terminal)

    rule = apply_result_rule(
        delta_lower=delta_lower, delta_upper=delta_upper,
        lower_compatible=compatible, disagreement_mass=disagreement_mass,
        witness_exists=lower_public["history_action_witness"] is not None,
        aggregate_advantage=aggregate_advantage,
    )
    record = {
        "object_id": OBJECT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "result_bearing": True,
        "complete": False,
        "scientific_polarity": None,
        "arithmetic": "fractions.Fraction exact rational",
        "no_rng": True,
        "one_process_one_thread": True,
        "launch_sha": launch_sha,
        "argv": list(argv),
        "admission_receipt": {
            "path": str(Path(admission_receipt)),
            "record": admission,
        },
        "primary": {
            "J_D": encoded(j_det), "J_L": encoded(j_lower), "J_U": encoded(j_upper),
            "Delta_L": encoded(delta_lower), "Delta_U": encoded(delta_upper),
        },
        "policies": {"DET-CF": det_public, "HIST-1UPDATE-CF": lower_public},
        "harm_compatibility": {
            "lower_compatible": compatible,
            "unsafe_allowance": encoded(Fraction(1, 50)),
            "clean_loss_allowance": encoded(Fraction(1, 20)),
        },
        "REGIME-ORACLE-ENVELOPE": {
            "certificate_only_extra_information": True,
            "legal_treatment": False,
            "unsafe_opportunity_probability": encoded(unsafe_probability),
            "safe_opportunity_probability": encoded(safe_probability),
            **upper_public,
        },
        "normalization_checks": checks,
        "static_work_counts": {
            "first_contexts": 12,
            "latent_first_step_atoms": 48,
            "visible_anchor_histories": len(lower_public["anchor_histories"]),
            "lower_action_score_evaluations": lower_public[
                "exact_lower_action_score_evaluations"
            ],
            "later_contexts": 12,
            "oracle_cells": len(cells),
            "oracle_action_variables": len(cells) * 3,
            "normalization_equalities": len(cells),
            "harm_inequalities": 2,
            "dual_tie_lines": 72,
            "dual_candidate_slots": 2701,
        },
        "result_rule": None,
        "learner_exposure": learner_exposure(),
        "resources": {
            "wall_seconds": None,
            "wall_cap_seconds": WALL_CAP_SECONDS,
            "peak_rss_bytes": None,
            "peak_rss_cap_bytes": RSS_CAP_BYTES,
            "status": "pending_post_publication_measurement",
        },
    }
    _write_summary(output_root, record)
    wall = time.perf_counter() - started
    peak = _peak_rss_bytes()
    cap_failures = []
    if wall > WALL_CAP_SECONDS:
        cap_failures.append("post-publication wall time exceeded 120 seconds")
    if peak is not None and peak > RSS_CAP_BYTES:
        cap_failures.append("post-publication peak RSS exceeded 1.5 GiB")
    if cap_failures:
        terminal = _terminal_hc_x(
            error=ArithmeticError("; ".join(cap_failures)),
            stage="POST-PUBLICATION-CAP", launch_sha=launch_sha, argv=argv,
            admission_receipt=admission_receipt, admission=admission,
            wall=wall, peak=peak, det=det_public, lower=lower_public, upper=upper_public,
        )
        return _write_summary(output_root, terminal)
    record["resources"] = {
        "wall_seconds": wall,
        "wall_cap_seconds": WALL_CAP_SECONDS,
        "peak_rss_bytes": peak,
        "peak_rss_cap_bytes": RSS_CAP_BYTES,
        "status": "measured" if peak is not None else "resources_unmeasured",
    }
    record["complete"] = True
    record["result_rule"] = rule
    return _write_summary(output_root, record)


def _synthetic_surface() -> tuple[tuple[Cell, ...], list[Fraction]]:
    """Build a deterministic, non-ACVC surface and its 512-bit raw inputs."""
    weight_raw = [
        _weighted_rational512(index + 1, 10_000 + index) for index in range(24)
    ]
    weight_total = sum(weight_raw, Fraction(0))
    raw_inputs = list(weight_raw)
    cells = []
    for index in range(24):
        base_u = _rational512(101 * index + 1)
        base_l = _rational512(101 * index + 7)
        du1 = _rational512(101 * index + 17)
        dl1 = _rational512(101 * index + 31)
        du2 = _rational512(101 * index + 53)
        dl2 = _rational512(101 * index + 79)
        unsafe_raw = (
            _weighted_rational512(index + 1, 20_000 + 2 * index),
            _weighted_rational512(24 - index, 20_001 + 2 * index),
        )
        unsafe_probability = unsafe_raw[0] / sum(unsafe_raw, Fraction(0))
        raw_inputs.extend((base_u, base_l, du1, dl1, du2, dl2, *unsafe_raw))
        unsafe = (base_u + du1 + du2, base_u + du1, base_u)
        clean = (base_l + dl1 + dl2, base_l + dl1, base_l)
        gains = tuple(unsafe[action] + clean[action] for action in range(3))
        cells.append(Cell(
            f"synthetic-{index:02d}", weight_raw[index] / weight_total,
            unsafe_probability,
            gains, unsafe, clean,
        ))
    return tuple(cells), raw_inputs


def synthetic_cells() -> tuple[Cell, ...]:
    return _synthetic_surface()[0]


def _synthetic_lower_path(
    cells: Sequence[Cell],
) -> tuple[dict[str, int], list[Fraction]]:
    """Complete a generic 12-opportunity lower calculation, then discard outcomes."""
    regime_raw = [
        _weighted_rational512(regime + 2, 30_000 + regime) for regime in range(2)
    ]
    regime_total = sum(regime_raw, Fraction(0))
    regime_weights = [value / regime_total for value in regime_raw]
    atom_raw = [
        [
            _weighted_rational512(
                (visible + 1) if regime == 0 else (24 - visible),
                31_000 + 100 * regime + visible,
            )
            for visible in range(24)
        ]
        for regime in range(2)
    ]
    atom_conditional = [
        [value / sum(atom_raw[regime], Fraction(0)) for value in atom_raw[regime]]
        for regime in range(2)
    ]
    context_raw = [
        [
            _weighted_rational512(
                (context + 1) if regime == 0 else (12 - context),
                34_000 + 100 * regime + context,
            )
            for context in range(12)
        ]
        for regime in range(2)
    ]
    context_conditional = [
        [value / sum(context_raw[regime], Fraction(0)) for value in context_raw[regime]]
        for regime in range(2)
    ]
    third_raw = [
        (
            _weighted_rational512(context + 1, 37_000 + 2 * context),
            _weighted_rational512(12 - context, 37_001 + 2 * context),
        ) for context in range(12)
    ]
    third_scores = [left / (left + right) for left, right in third_raw]
    raw_inputs = [
        *regime_raw,
        *(value for row in atom_raw for value in row),
        *(value for row in context_raw for value in row),
        *(value for pair in third_raw for value in pair),
    ]

    joint_atoms = [
        [regime_weights[regime] * atom_conditional[regime][visible] for visible in range(24)]
        for regime in range(2)
    ]
    visible_mass = [joint_atoms[0][visible] + joint_atoms[1][visible] for visible in range(24)]
    anchors = [joint_atoms[0][visible] / visible_mass[visible] for visible in range(24)]
    actions: dict[tuple[int, int], int] = {}
    scores_by_state: dict[tuple[int, int], tuple[Fraction, Fraction, Fraction]] = {}
    score_evaluations = 0
    for visible, anchor in enumerate(anchors):
        for context in range(12):
            mixed_likelihood = (
                anchor * context_conditional[0][context]
                + (1 - anchor) * context_conditional[1][context]
            )
            transient = anchor * context_conditional[0][context] / mixed_likelihood
            scores = (transient, 1 - transient, third_scores[context])
            scores_by_state[(visible, context)] = scores
            actions[(visible, context)] = max(range(3), key=lambda index: scores[index])
            score_evaluations += 3

    returns = [Fraction(0), Fraction(0)]
    action_counts = [Fraction(0), Fraction(0), Fraction(0)]
    unsafe_denominator = safe_denominator = Fraction(0)
    unsafe_execute = clean_loss = Fraction(0)
    episode_mass = Fraction(0)
    disagreement = forced_advantage = Fraction(0)
    for regime in range(2):
        for visible in range(24):
            atom_mass = joint_atoms[regime][visible]
            first_action = visible % 3
            first_cell = cells[visible]
            first_unsafe = first_cell.unsafe_probability
            returns[regime] += atom_mass * first_cell.gains[first_action]
            action_counts[first_action] += atom_mass
            unsafe_denominator += atom_mass * first_unsafe
            safe_denominator += atom_mass * (1 - first_unsafe)
            unsafe_execute += atom_mass * first_cell.unsafe[first_action]
            clean_loss += atom_mass * first_cell.clean_loss[first_action]
            episode_mass += atom_mass
            for context in range(12):
                state_mass = atom_mass * context_conditional[regime][context]
                action = actions[(visible, context)]
                comparator = context % 3
                cell = cells[context]
                unsafe_probability = cell.unsafe_probability
                scaled = 11 * state_mass
                returns[regime] += scaled * cell.gains[action]
                action_counts[action] += scaled
                unsafe_denominator += scaled * unsafe_probability
                safe_denominator += scaled * (1 - unsafe_probability)
                unsafe_execute += scaled * cell.unsafe[action]
                clean_loss += scaled * cell.clean_loss[action]
                episode_mass += scaled
                if action != comparator:
                    disagreement += scaled
                    forced_advantage += scaled * (
                        scores_by_state[(visible, context)][action]
                        - scores_by_state[(visible, context)][comparator]
                    )

    pair_context_scans = 0
    first_witness: tuple[int, int, int] | None = None
    for left in range(24):
        for right in range(left + 1, 24):
            for context in range(12):
                pair_context_scans += 1
                if (
                    first_witness is None
                    and actions[(left, context)] != actions[(right, context)]
                ):
                    first_witness = (left, right, context)

    regime_returns = [returns[index] / regime_weights[index] for index in range(2)]
    action_rates = [count / 12 for count in action_counts]
    harm_rates = (unsafe_execute / unsafe_denominator, clean_loss / safe_denominator)
    if (
        len(joint_atoms) * len(joint_atoms[0]) != 48
        or any(mass <= 0 for row in joint_atoms for mass in row)
        or any(sum(row, Fraction(0)) != 1 for row in atom_conditional)
        or any(sum(row, Fraction(0)) != 1 for row in context_conditional)
        or sum(regime_weights, Fraction(0)) != 1
        or sum(visible_mass, Fraction(0)) != 1
        or score_evaluations != 864
        or pair_context_scans != 24 * 23 // 2 * 12
        or episode_mass != 12
        or sum(action_counts, Fraction(0)) != 12
        or sum(action_rates, Fraction(0)) != 1
        or unsafe_denominator + safe_denominator != 12
        or disagreement <= 0
        or forced_advantage < 0
        or first_witness is None
        or any(value <= 0 for value in (*regime_returns, *harm_rates))
    ):
        raise ArithmeticError("synthetic lower path failed exact completion")
    return ({
        "latent_first_step_atoms": 48,
        "regimes": 2,
        "visible_anchors": 24,
        "later_contexts": 12,
        "episode_opportunities": 12,
        "regime_return_count": 2,
        "action_count": 3,
        "harm_rate_count": 2,
        "lower_action_score_evaluations": score_evaluations,
        "history_pair_context_scans": pair_context_scans,
    }, raw_inputs)


def run_synthetic(*, full_candidates: bool = True) -> dict[str, Any]:
    """Exercise the publication computations without retaining synthetic outcomes."""
    started = time.perf_counter()
    cells, upper_raw_inputs = _synthetic_surface()
    lower_counts, lower_specific_raw_inputs = _synthetic_lower_path(cells)
    lower_raw_inputs = [*upper_raw_inputs, *lower_specific_raw_inputs]
    caps = (
        sum((cell.weight * cell.unsafe[1] for cell in cells), Fraction(0)),
        sum((cell.weight * cell.clean_loss[1] for cell in cells), Fraction(0)),
    )
    if full_candidates:
        certificate = solve_upper(cells, caps, started + WALL_CAP_SECONDS)
        candidate_slots = certificate["candidate_arrangement"]["candidate_slots"]
        score_evaluations = certificate["candidate_arrangement"]["exact_action_score_evaluations"]
    else:
        reduced = cells[:3]
        reduced_caps = (
            sum((cell.weight * cell.unsafe[1] for cell in reduced), Fraction(0)),
            sum((cell.weight * cell.clean_loss[1] for cell in reduced), Fraction(0)),
        )
        certificate = solve_upper(reduced, reduced_caps, started + 60.0)
        candidate_slots = certificate["candidate_arrangement"]["candidate_slots"]
        score_evaluations = certificate["candidate_arrangement"]["exact_action_score_evaluations"]
    del certificate
    wall = time.perf_counter() - started
    peak = _peak_rss_bytes()
    return {
        "wall_seconds": wall,
        "peak_rss_bytes": peak,
        "static_counts": {
            "cells": len(cells),
            "actions_per_cell": 3,
            "harm_constraints": 2,
            **lower_counts,
            "dual_candidate_slots": candidate_slots,
            "exact_action_score_evaluations": score_evaluations,
            "minimum_lower_input_numerator_bits": min(
                value.numerator.bit_length() for value in lower_raw_inputs
            ),
            "minimum_lower_input_denominator_bits": min(
                value.denominator.bit_length() for value in lower_raw_inputs
            ),
            "minimum_upper_input_numerator_bits": min(
                value.numerator.bit_length() for value in upper_raw_inputs
            ),
            "minimum_upper_input_denominator_bits": min(
                value.denominator.bit_length() for value in upper_raw_inputs
            ),
        },
    }


def run_mock_publication(output_root: str | Path, *, argv: Sequence[str]) -> Path:
    """Use the formal JSON writer on a reduced, result-blind synthetic record."""
    cost = run_synthetic(full_candidates=False)
    mock = {
        "object_id": "SYNTHETIC-PUBLICATION-SMOKE",
        "evidence_class": None,
        "result_bearing": False,
        "result_blind": True,
        "mocked_formal_publication": True,
        "complete": True,
        "scientific_polarity": None,
        "launch_sha": "synthetic-not-a-launch",
        "argv": list(argv),
        "admission_receipt": None,
        "primary": {
            "J_D": encoded(Fraction(5, 17)),
            "J_L": encoded(Fraction(7, 19)),
            "J_U": encoded(Fraction(11, 23)),
            "Delta_L": encoded(Fraction(24, 323)),
            "Delta_U": encoded(Fraction(72, 391)),
        },
        "policies": {
            "SYNTHETIC-LOWER": {"action_rate": encoded(Fraction(2, 7))},
            "SYNTHETIC-COMPARATOR": {"action_rate": encoded(Fraction(3, 11))},
        },
        "REGIME-ORACLE-ENVELOPE": {
            "primal": {"objective": encoded(Fraction(13, 29))},
            "dual": {"objective": encoded(Fraction(13, 29))},
            "equal_primal_dual_objective": True,
        },
        "result_rule": None,
        "resources": {
            "wall_seconds": cost["wall_seconds"],
            "peak_rss_bytes": cost["peak_rss_bytes"],
        },
        "static_work_counts": cost["static_counts"],
    }
    return _write_summary(output_root, mock)
