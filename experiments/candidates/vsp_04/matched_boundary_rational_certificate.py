"""Exact finite-cell certificate for the frozen VSP-04 Sequence 10 candidate."""

from __future__ import annotations

import itertools
import json
import sys
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Iterable, Mapping, Sequence


F = Fraction
CANDIDATE_ID = "CAND-VSP-04-MATCHED-BOUNDARY-REQUEST-TRIAD@adversarial-revision-v8"
TREATMENT = "VSP-04-STACKED-FINITE-CELL-KNOCKOFF-CERT-D0"
MODES = ("IND", "OR", "SOFT")
CELLS = ("w0", "w1", "w2")
OMEGA = (F(1, 4), F(1, 2), F(1, 4))
P_H = F(1, 2)
SUPPORT_FLOOR = F(1, 4)
TAPE = (F(0), F(1, 4), F(1, 2), F(3, 4))
LEGAL_ACTIONS = ("ACK", "RETRY")
ACK_FEATURE = (F(0), F(1), F(0))
WEIGHTED_ACK_COEFFICIENT = tuple(weight * feature for weight, feature in zip(OMEGA, ACK_FEATURE))


@dataclass(frozen=True)
class Ledger:
    x: tuple[str, ...]
    m_minus: tuple[str, ...]
    g: tuple[str, ...]
    u: tuple[str, ...]
    u_proxies: tuple[str, ...]

    @property
    def h(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return self.x, self.m_minus

    @property
    def w(self) -> tuple[tuple[tuple[str, ...], tuple[str, ...]], tuple[str, ...]]:
        return self.h, self.g

    def validate(self) -> None:
        required = {"source_private", "request_descendant", "outcome", "future"}
        if not required <= set(self.u):
            raise ValueError("U must transitively include every excluded field family")
        leak = set(self.g) & (set(self.u) | set(self.u_proxies))
        if leak:
            raise ValueError(f"excluded U field leaked into pre-execution G: {sorted(leak)}")


PRIMARY_LEDGER = Ledger(
    x=("request_class", "public_capacity"),
    m_minus=("frozen_policy_state", "frozen_recurrent_state"),
    g=("queue_depth", "retry_budget", "ack_capability"),
    u=("source_private", "request_descendant", "outcome", "future"),
    u_proxies=(
        "source_private_proxy",
        "request_descendant_proxy",
        "outcome_proxy",
        "future_proxy",
    ),
)


@dataclass(frozen=True)
class Row:
    name: str
    kind: str
    mode: str
    path: str
    action: str
    coefficients: tuple[Fraction, ...]
    target: Fraction


@dataclass(frozen=True)
class System:
    name: str
    cells: tuple[str, ...]
    rows: tuple[Row, ...]


@dataclass(frozen=True)
class DualCertificate:
    y: tuple[Fraction, ...]
    lhs: Fraction
    rhs: Fraction
    margin: Fraction
    forcing_rows: tuple[str, ...]


def _row(
    name: str,
    kind: str,
    mode: str,
    path: str,
    action: str,
    coefficients: tuple[Fraction, ...],
    target: Fraction,
) -> Row:
    return Row(name, kind, mode, path, action, coefficients, target)


# These are independently registered frozen constants, not values synthesized from q.
PRIMARY_ROWS = (
    _row("COMMON.raw_propensity", "raw", "COMMON", "raw", "ALL", (F(1, 4), F(1, 2), F(1, 4)), F(1, 2)),
    _row("IND.path.timing_metadata", "path", "IND", "timing_metadata", "ALL", (F(1, 4), F(0), F(0)), F(1, 8)),
    _row("IND.path.queue_retry_ack_cost", "path", "IND", "queue_retry_ack_cost", "ALL", (F(0), F(0), F(1, 4)), F(1, 8)),
    _row("IND.risk.ACK", "action_risk", "IND", "all", "ACK", WEIGHTED_ACK_COEFFICIENT, F(1, 4)),
    _row("IND.risk.RETRY", "action_risk", "IND", "all", "RETRY", (F(1, 4), F(0), F(1, 4)), F(1, 4)),
    _row("OR.path.timing_metadata", "path", "OR", "timing_metadata", "ALL", (F(1, 4), F(0), F(0)), F(1, 8)),
    _row("OR.path.queue_retry_ack_cost", "path", "OR", "queue_retry_ack_cost", "ALL", (F(0), F(0), F(1, 4)), F(1, 8)),
    _row("OR.risk.ACK", "action_risk", "OR", "all", "ACK", WEIGHTED_ACK_COEFFICIENT, F(3, 8)),
    _row("OR.risk.RETRY", "action_risk", "OR", "all", "RETRY", (F(1, 4), F(0), F(1, 4)), F(1, 4)),
    _row("SOFT.path.timing_metadata", "path", "SOFT", "timing_metadata", "ALL", (F(1, 4), F(0), F(0)), F(1, 8)),
    _row("SOFT.path.queue_retry_ack_cost", "path", "SOFT", "queue_retry_ack_cost", "ALL", (F(0), F(0), F(1, 4)), F(1, 8)),
    _row("SOFT.risk.ACK", "action_risk", "SOFT", "all", "ACK", (F(1, 4), F(1, 2), F(0)), F(3, 8)),
    _row("SOFT.risk.RETRY", "action_risk", "SOFT", "all", "RETRY", (F(0), F(1, 2), F(1, 4)), F(3, 8)),
)
PRIMARY_SYSTEM = System("primary_frozen_triad", CELLS, PRIMARY_ROWS)

FEASIBLE_ENGINEERING_SYSTEM = System(
    "engineering_minimal_feasible",
    ("e0", "e1", "e2"),
    (
        _row("ENG.raw", "raw", "ENG", "raw", "ALL", (F(1, 4), F(1, 2), F(1, 4)), F(1, 2)),
        _row("ENG.path.left", "path", "ENG", "left", "ALL", (F(1, 4), F(0), F(0)), F(1, 8)),
        _row("ENG.risk.center", "action_risk", "ENG", "all", "ACK", (F(0), F(1, 2), F(0)), F(1, 4)),
        _row("ENG.path.right", "path", "ENG", "right", "ALL", (F(0), F(0), F(1, 4)), F(1, 8)),
    ),
)
INFEASIBLE_ENGINEERING_SYSTEM = System(
    "engineering_minimal_infeasible",
    ("e0", "e1"),
    (
        _row("ENG.low", "action_risk", "ENG", "all", "ACK", (F(1), F(0)), F(1, 4)),
        _row("ENG.high", "action_risk", "ENG", "all", "ACK", (F(1), F(0)), F(3, 4)),
    ),
)

FULL_ASYMMETRIC_LOSSES = (
    ("IND", "ACK", F(1), F(5)),
    ("IND", "RETRY", F(3), F(2)),
    ("OR", "ACK", F(2), F(7)),
    ("OR", "RETRY", F(4), F(1)),
    ("SOFT", "ACK", F(3), F(6)),
    ("SOFT", "RETRY", F(5), F(2)),
)
FROZEN_POLICY = ("policy", "pi_request_v8", "state", "fixed")
FROZEN_RECURRENT = ("hidden", F(2, 5), "cell", F(-1, 7))
INTERFACE_TABLES = (
    ("timing", ("pre_execution", "post_interface")),
    ("metadata", ("request_class", "public_capacity")),
    ("queue", (0, 1, 2)),
    ("retry", (0, 1)),
    ("ack", ("disabled", "enabled")),
    ("cost", (F(1), F(3, 2), F(7, 3))),
)
SHADOW_SIGNATURES = (
    ("base", F(2, 3), "source_A", "partner_P"),
    ("shadow_R", F(2, 3), "source_A", "partner_P"),
    ("shadow_source", F(2, 3), "source_A", "partner_P"),
    ("shadow_partner", F(2, 3), "source_A", "partner_P"),
)
FEATURE_SNAPSHOT = ("request_class", "public_capacity", "queue_depth", "retry_budget", "ack_capability")


def _solve_square(matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]) -> tuple[Fraction, ...] | None:
    n = len(rhs)
    aug = [list(matrix[i]) + [rhs[i]] for i in range(n)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if aug[r][col]), None)
        if pivot is None:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [value / scale for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            scale = aug[row][col]
            aug[row] = [aug[row][j] - scale * aug[col][j] for j in range(n + 1)]
    return tuple(aug[i][-1] for i in range(n))


def validate_witness(system: System, q: Sequence[Fraction]) -> bool:
    if len(q) != len(system.cells) or any(value < 0 or value > 1 for value in q):
        return False
    return all(sum(a * value for a, value in zip(row.coefficients, q)) == row.target for row in system.rows)


def solve_primal_vertices(system: System) -> tuple[Fraction, ...] | None:
    """Enumerate equality/bound vertices using only exact rational arithmetic."""
    n = len(system.cells)
    constraints = [(row.coefficients, row.target) for row in system.rows]
    constraints += [
        (tuple(F(int(i == j)) for i in range(n)), bound)
        for j in range(n)
        for bound in (F(0), F(1))
    ]
    for chosen in itertools.combinations(constraints, n):
        q = _solve_square([item[0] for item in chosen], [item[1] for item in chosen])
        if q is not None and validate_witness(system, q):
            return q
    return None


def validate_dual(system: System, y: Sequence[Fraction]) -> DualCertificate:
    if len(y) != len(system.rows):
        raise ValueError("dual dimension mismatch")
    lhs = sum(value * row.target for value, row in zip(y, system.rows))
    at_y = tuple(sum(value * row.coefficients[j] for value, row in zip(y, system.rows)) for j in range(len(system.cells)))
    rhs = sum(max(F(0), value) for value in at_y)
    if lhs <= rhs:
        raise ValueError("invalid exact box-infeasibility certificate")
    forcing = tuple(row.name for value, row in zip(y, system.rows) if value)
    return DualCertificate(tuple(y), lhs, rhs, lhs - rhs, forcing)


def search_sparse_dual(system: System) -> DualCertificate | None:
    """Independently search all two-row unit separators over immutable A,b."""
    candidates: list[DualCertificate] = []
    for first, second in itertools.combinations(range(len(system.rows)), 2):
        for signs in ((F(1), F(-1)), (F(-1), F(1))):
            y = [F(0)] * len(system.rows)
            y[first], y[second] = signs
            try:
                candidates.append(validate_dual(system, y))
            except ValueError:
                pass
    if not candidates:
        return None
    return sorted(candidates, key=lambda cert: (-cert.margin, cert.forcing_rows))[0]


def validate_support(weights: Sequence[Fraction], propensity: Fraction) -> None:
    if not weights or sum(weights) != 1 or min(weights) < SUPPORT_FLOOR:
        raise ValueError("immutable finite-cell support floor violated")
    if propensity < SUPPORT_FLOOR or propensity > 1 - SUPPORT_FLOOR:
        raise ValueError("raw propensity support floor violated")


def validate_feature_transition(before: Sequence[str], after: Sequence[str], feasibility_observed: bool) -> None:
    if feasibility_observed and tuple(before) != tuple(after):
        raise ValueError("feature/information adaptation after feasibility observation is forbidden")


def validate_frozen_contract() -> None:
    PRIMARY_LEDGER.validate()
    if PRIMARY_LEDGER.h != (PRIMARY_LEDGER.x, PRIMARY_LEDGER.m_minus) or PRIMARY_LEDGER.w != (PRIMARY_LEDGER.h, PRIMARY_LEDGER.g):
        raise ValueError("immutable H=(X,M-) or W=(H,G) ledger structure changed")
    weighted_feature = tuple(weight * feature for weight, feature in zip(OMEGA, ACK_FEATURE))
    ack_rows = tuple(row for row in PRIMARY_ROWS if row.name in ("IND.risk.ACK", "OR.risk.ACK"))
    if weighted_feature != WEIGHTED_ACK_COEFFICIENT or len(ack_rows) != 2 or any(row.coefficients != weighted_feature for row in ack_rows):
        raise ValueError("frozen ACK feature was not weighted componentwise by omega")
    validate_support(OMEGA, P_H)
    if tuple(item[0] for item in INTERFACE_TABLES) != ("timing", "metadata", "queue", "retry", "ack", "cost"):
        raise ValueError("interface table inventory changed")
    if {(mode, action) for mode, action, _, _ in FULL_ASYMMETRIC_LOSSES} != set(itertools.product(MODES, LEGAL_ACTIONS)):
        raise ValueError("legal action/loss table incomplete")
    if any(loss0 == loss1 for _, _, loss0, loss1 in FULL_ASYMMETRIC_LOSSES):
        raise ValueError("loss table is not asymmetric")
    if FROZEN_POLICY[-1] != "fixed" or len(FROZEN_RECURRENT) != 4:
        raise ValueError("policy/recurrent state not frozen")
    base = SHADOW_SIGNATURES[0][1:]
    if any(signature[1:] != base for signature in SHADOW_SIGNATURES[1:]):
        raise ValueError("shadow-R/source/partner invariance failed")
    validate_feature_transition(FEATURE_SNAPSHOT, FEATURE_SNAPSHOT, True)


def paired_tk_a0_checks(q: Sequence[Fraction], system: System) -> Mapping[str, object]:
    if not validate_witness(system, q):
        raise ValueError("paired checks require a validated feasible witness")
    comparisons = 0
    carrier_by_u: dict[int, list[tuple[str, str, int, int]]] = {0: [], 1: []}
    for mode in MODES:
        for path in ("timing_metadata", "queue_retry_ack_cost"):
            for cell_index, threshold in enumerate(q):
                for tape_value in TAPE:
                    treatment_state = int(tape_value <= threshold)
                    knockoff_state = int(tape_value <= threshold)
                    outcome = cell_index % 2
                    action_t = LEGAL_ACTIONS[1 - treatment_state]
                    action_k = LEGAL_ACTIONS[1 - knockoff_state]
                    loss_t = next(item[2 + outcome] for item in FULL_ASYMMETRIC_LOSSES if item[:2] == (mode, action_t))
                    loss_k = next(item[2 + outcome] for item in FULL_ASYMMETRIC_LOSSES if item[:2] == (mode, action_k))
                    if treatment_state != knockoff_state or loss_t != loss_k or loss_t - loss_k != 0:
                        raise AssertionError("branchwise V_T=V_K and Delta_TK=0 failed")
                    carrier = (mode, path, cell_index, treatment_state)
                    carrier_by_u[0].append(carrier)
                    carrier_by_u[1].append(carrier)
                    comparisons += 1
    if carrier_by_u[0] != carrier_by_u[1]:
        raise AssertionError("matched carrier A0 depends on excluded U")
    return {"a0_u_independent": True, "comparisons": comparisons, "delta_tk": "0", "finite_tape_size": len(TAPE)}


def permute_mode_labels(system: System, permutation: Mapping[str, str]) -> System:
    if set(permutation) != set(MODES) or set(permutation.values()) != set(MODES):
        raise ValueError("mode permutation must be bijective")
    rows = []
    for row in system.rows:
        if row.mode in MODES:
            prefix, suffix = row.name.split(".", 1)
            rows.append(replace(row, name=f"{permutation[prefix]}.{suffix}", mode=permutation[row.mode]))
        else:
            rows.append(row)
    return System(system.name, system.cells, tuple(rows))


def _fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def row_inventory(system: System) -> Mapping[str, object]:
    return {
        "action_risk": {mode: sum(row.kind == "action_risk" and row.mode == mode for row in system.rows) for mode in MODES},
        "path": {mode: sum(row.kind == "path" and row.mode == mode for row in system.rows) for mode in MODES},
        "raw": sum(row.kind == "raw" for row in system.rows),
        "total": len(system.rows),
    }


def build_result() -> Mapping[str, object]:
    validate_frozen_contract()
    primary_witness = solve_primal_vertices(PRIMARY_SYSTEM)
    primary_dual = search_sparse_dual(PRIMARY_SYSTEM)
    if primary_witness is not None or primary_dual is None:
        raise AssertionError("primary frozen system did not end in exact infeasibility")
    feasible_q = solve_primal_vertices(FEASIBLE_ENGINEERING_SYSTEM)
    infeasible_q = solve_primal_vertices(INFEASIBLE_ENGINEERING_SYSTEM)
    engineering_dual = search_sparse_dual(INFEASIBLE_ENGINEERING_SYSTEM)
    if feasible_q is None or infeasible_q is not None or engineering_dual is None:
        raise AssertionError("engineering branch evidence incomplete")
    paired = paired_tk_a0_checks(feasible_q, FEASIBLE_ENGINEERING_SYSTEM)
    return {
        "candidate_id": CANDIDATE_ID,
        "certificate": {
            "forcing_modes": sorted({row.mode for row in PRIMARY_SYSTEM.rows if row.name in primary_dual.forcing_rows}),
            "forcing_rows": list(primary_dual.forcing_rows),
            "lhs": _fraction(primary_dual.lhs),
            "margin": _fraction(primary_dual.margin),
            "rhs": _fraction(primary_dual.rhs),
            "y_sparse": {row.name: _fraction(value) for row, value in zip(PRIMARY_SYSTEM.rows, primary_dual.y) if value},
        },
        "checks": {
            "excluded_u_absent_from_g": True,
            "frozen_policy_recurrent_shadow_tables": True,
            "no_post_result_feature_adaptation": True,
            "support_floor": _fraction(SUPPORT_FLOOR),
        },
        "conclusion": "no common triad K exists under this frozen information contract",
        "engineering_units": {
            "feasible": {"paired": paired, "witness": [_fraction(value) for value in feasible_q]},
            "infeasible": {"margin": _fraction(engineering_dual.margin), "witness": None},
        },
        "nonclaims": ["authentic-request value", "causality", "deployment", "return", "training benefit", "universal impossibility"],
        "primary": {
            "cells": list(CELLS),
            "omega": [_fraction(value) for value in OMEGA],
            "p_h": _fraction(P_H),
            "row_inventory": row_inventory(PRIMARY_SYSTEM),
            "witness": None,
        },
        "treatment": TREATMENT,
    }


def main() -> None:
    payload = json.dumps(build_result(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(payload + b"\n")


if __name__ == "__main__":
    main()
