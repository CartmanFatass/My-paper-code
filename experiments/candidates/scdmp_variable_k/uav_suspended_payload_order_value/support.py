"""Exact qualification-only support-panel calculations."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Final, Iterable


SUPPORT_K: Final[tuple[int, int]] = (6, 14)
HISTORIES: Final[tuple[str, str]] = ("RG", "GR")
ACTION_CODES: Final[tuple[int, ...]] = tuple(range(27))
QUOTIENT_REPRESENTATIVES: Final[tuple[int, ...]] = (0, 1, 2, 4, 5, 8, 13, 14, 17, 26)
ZERO_ACTION_CODE: Final[int] = 0
MAX_ACTION_CODE: Final[int] = 26


class SupportContractError(RuntimeError):
    pass


def decode_action(action_code: int) -> tuple[int, int, int]:
    if action_code not in ACTION_CODES:
        raise SupportContractError("action code must lie in [0,27)")
    return (action_code // 9, (action_code // 3) % 3, action_code % 3)


def encode_action(command: tuple[int, int, int]) -> int:
    if len(command) != 3 or any(value not in (0, 1, 2) for value in command):
        raise SupportContractError("joint command must contain three values from {0,1,2}")
    return command[0] * 9 + command[1] * 3 + command[2]


def quotient_representative(action_code: int) -> int:
    """Map a joint action to its nondecreasing carrier-permutation representative."""

    return encode_action(tuple(sorted(decode_action(action_code))))


def _physics_signature(action_code: int) -> tuple[Fraction, Fraction, Fraction]:
    """Exact permutation-invariant action terms read by the support dynamics."""

    command = decode_action(action_code)
    mean = Fraction(sum(command), 3)
    imbalance = max(abs(Fraction(value) - mean) for value in command)
    max_tension_action_term = max(
        Fraction(17, 100) * value + Fraction(11, 100) * abs(Fraction(value) - mean)
        for value in command
    )
    return mean, imbalance, max_tension_action_term


def support_quotient_certificate() -> dict[str, object]:
    """Exhaustively certify the lossless 27-to-10 carrier-permutation quotient."""

    classes = {
        representative: tuple(
            action for action in ACTION_CODES
            if quotient_representative(action) == representative
        )
        for representative in QUOTIENT_REPRESENTATIVES
    }
    covers = tuple(sorted(action for members in classes.values() for action in members))
    invariant = all(
        all(_physics_signature(action) == _physics_signature(representative) for action in members)
        for representative, members in classes.items()
    )
    return {
        "schema": "SCDMP_UAV_SP_R02_SUPPORT_QUOTIENT_CERTIFICATE_V1",
        "registered_action_count": 27,
        "representative_count": 10,
        "representatives": QUOTIENT_REPRESENTATIVES,
        "classes": classes,
        "all_27_actions_covered_once": covers == ACTION_CODES,
        "permutation_invariant_physics_signature": invariant,
        "signature_terms": ("mean_demand_a", "imbalance_b", "max_tension_action_term"),
        "prior_individual_tensions_read_by_later_support_dynamics": False,
        "effort_enters_support_J": False,
        "candidate_trajectory_count": 10,
        "maximum_transitions_per_boundary": 10 * 14,
        "complexity": "O(k*10)",
        "nested_replanning": False,
    }


def expand_quotient_scores(scores: dict[int, float]) -> dict[int, float]:
    if set(scores) != set(QUOTIENT_REPRESENTATIVES):
        raise SupportContractError("support simulation must contain exactly 10 quotient representatives")
    if not all(math.isfinite(float(value)) for value in scores.values()):
        raise SupportContractError("support representative scores must all be finite")
    return {
        action: float(scores[quotient_representative(action)])
        for action in ACTION_CODES
    }


def support_score(
    *,
    delta_x: float,
    k: int,
    physical_failure: bool,
    z_end: float,
    phi_end: float,
    f_end: float,
) -> float:
    values = (delta_x, z_end, phi_end, f_end)
    if k not in SUPPORT_K or not all(math.isfinite(value) for value in values):
        raise SupportContractError("support score inputs are nonfinite or use an unregistered k")
    return (
        delta_x / (0.18 * k)
        - 2.0 * int(bool(physical_failure))
        - 0.5 * (z_end / 0.55)
        - 0.25 * (abs(phi_end) / 0.48)
        - 0.25 * (f_end / 0.42)
    )


def exact_max_set(scores: dict[int, float]) -> tuple[tuple[int, ...], float]:
    if set(scores) != set(ACTION_CODES):
        raise SupportContractError("a support cell must contain all 27 legal actions")
    if not all(math.isfinite(float(value)) for value in scores.values()):
        raise SupportContractError("support action scores must all be finite")
    maximum = max(float(value) for value in scores.values())
    # The science card requires exact ties, so there is deliberately no tolerance.
    maximizers = tuple(action for action in ACTION_CODES if float(scores[action]) == maximum)
    return maximizers, maximum


@dataclass(frozen=True)
class SupportActionRow:
    replicate: int
    k: int
    state_index: int
    history: str
    action_code: int
    public_state_digest: str
    disturbance_digest: str
    score: float


def _digest(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise SupportContractError(f"{field} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise SupportContractError(f"{field} must be a SHA-256 hex digest") from error
    return value.lower()


def support_metrics(rows: Iterable[SupportActionRow], *, replicate: int) -> dict[str, float]:
    """Compute Q_order, D_order, D_action with exact 144/144/288 denominators."""

    if isinstance(replicate, bool) or replicate not in range(18):
        raise SupportContractError("replicate must lie in [0,18)")
    values = tuple(rows)
    expected_count = 2 * 72 * 2 * 10
    if len(values) != expected_count:
        raise SupportContractError(f"support replicate must contain exactly {expected_count} rows")
    lookup: dict[tuple[int, int, str, int], SupportActionRow] = {}
    for row in values:
        if row.replicate != replicate or row.k not in SUPPORT_K or row.state_index not in range(72):
            raise SupportContractError("support row identity differs from the frozen panel")
        if row.history not in HISTORIES or row.action_code not in QUOTIENT_REPRESENTATIVES:
            raise SupportContractError("support history/action identity is invalid")
        _digest(row.public_state_digest, "public_state_digest")
        _digest(row.disturbance_digest, "disturbance_digest")
        if not math.isfinite(row.score):
            raise SupportContractError("support score is nonfinite")
        key = (row.k, row.state_index, row.history, row.action_code)
        if key in lookup:
            raise SupportContractError("support row identity is duplicated")
        lookup[key] = row
    expected = {
        (k, state_index, history, action)
        for k in SUPPORT_K for state_index in range(72)
        for history in HISTORIES for action in QUOTIENT_REPRESENTATIVES
    }
    if set(lookup) != expected:
        raise SupportContractError("support panel has missing or extra identities")

    q_numerator = 0.0
    d_order_numerator = 0.0
    d_action_numerator = 0.0
    for k in SUPPORT_K:
        for state_index in range(72):
            public_digests = {
                lookup[(k, state_index, history, action)].public_state_digest
                for history in HISTORIES for action in QUOTIENT_REPRESENTATIVES
            }
            disturbance_digests = {
                lookup[(k, state_index, history, action)].disturbance_digest
                for history in HISTORIES for action in QUOTIENT_REPRESENTATIVES
            }
            if len(public_digests) != 1 or len(disturbance_digests) != 1:
                raise SupportContractError(
                    "public state and disturbance tape must be shared across histories/actions"
                )
            maxima: dict[str, tuple[tuple[int, ...], float]] = {}
            for history in HISTORIES:
                representative_scores = {
                    action: lookup[(k, state_index, history, action)].score
                    for action in QUOTIENT_REPRESENTATIVES
                }
                scores = expand_quotient_scores(representative_scores)
                maxima[history] = exact_max_set(scores)
                d_action_numerator += abs(scores[ZERO_ACTION_CODE] - scores[MAX_ACTION_CODE])
            q_numerator += float(maxima["RG"][0] != maxima["GR"][0])
            d_order_numerator += abs(maxima["RG"][1] - maxima["GR"][1])

    return {
        "Q_order": q_numerator / 144.0,
        "D_order": d_order_numerator / 144.0,
        "D_action": d_action_numerator / 288.0,
        "Q_order_denominator": 144.0,
        "D_order_denominator": 144.0,
        "D_action_denominator": 288.0,
    }
