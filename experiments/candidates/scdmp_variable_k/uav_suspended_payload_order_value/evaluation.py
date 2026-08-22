"""Deterministic evaluation action and direct endpoint aggregation laws."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Final, Iterable, Sequence


CONTROLLERS: Final[tuple[str, ...]] = ("TREAT", "FREE", "REVERSED", "SET")
REGIMES: Final[tuple[str, ...]] = (
    "fixed-4", "fixed-10", "fixed-6", "fixed-14", "6-to-14", "14-to-6"
)
TARGET_REGIMES: Final[tuple[str, ...]] = ("fixed-6", "fixed-14", "6-to-14", "14-to-6")
COMPETENCE_REGIMES: Final[tuple[str, str]] = ("fixed-4", "fixed-10")


class EvaluationContractError(RuntimeError):
    pass


def deterministic_lexicographic_argmax(logits: Sequence[float]) -> int:
    """Choose the first of 27 exact maxima; no tolerance or sampling exists."""

    if len(logits) != 27 or not all(math.isfinite(float(value)) for value in logits):
        raise EvaluationContractError("evaluation requires exactly 27 finite logits")
    maximum = max(float(value) for value in logits)
    return next(index for index, value in enumerate(logits) if float(value) == maximum)


def _digest(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise EvaluationContractError(f"{field} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise EvaluationContractError(f"{field} must be a SHA-256 hex digest") from error
    return value.lower()


@dataclass(frozen=True)
class EpisodeEndpoint:
    replicate: int
    controller: str
    regime: str
    scenario_index: int
    event_order: str
    switch_tick: int
    scenario_digest: str
    safe_delivery: bool
    physical_failure: bool
    timeout: bool
    overload: bool
    swing: bool
    formation: bool
    completion_time_seconds: float
    active_effort_sum: float
    active_ticks: int
    post_absorption_policy_queries: int = 0

    def validate(self) -> None:
        if isinstance(self.replicate, bool) or self.replicate not in range(18):
            raise EvaluationContractError("evaluation replicate lies outside [0,18)")
        if self.controller not in CONTROLLERS or self.regime not in REGIMES:
            raise EvaluationContractError("evaluation controller/regime is unregistered")
        if isinstance(self.scenario_index, bool) or self.scenario_index not in range(120):
            raise EvaluationContractError("scenario_index must lie in [0,120)")
        if self.event_order not in ("RG", "GR"):
            raise EvaluationContractError("event order must be RG or GR")
        if self.regime in ("6-to-14", "14-to-6"):
            if self.switch_tick not in (168, 252):
                raise EvaluationContractError("switch regime requires tick 168 or 252")
        elif self.switch_tick != 0:
            raise EvaluationContractError("fixed regime must use switch_tick=0")
        _digest(self.scenario_digest, "scenario_digest")
        terminal_labels = int(self.safe_delivery) + int(self.physical_failure) + int(self.timeout)
        if terminal_labels != 1:
            raise EvaluationContractError("exactly one delivery/failure/timeout class is required")
        if (self.overload or self.swing or self.formation) and not self.physical_failure:
            raise EvaluationContractError("physical failure labels require physical_failure")
        if self.physical_failure and not (self.overload or self.swing or self.formation):
            raise EvaluationContractError("physical failure must retain at least one named mode")
        if not math.isfinite(self.completion_time_seconds):
            raise EvaluationContractError("completion time is nonfinite")
        if self.safe_delivery:
            if not 0.0 < self.completion_time_seconds <= 42.0:
                raise EvaluationContractError("safe delivery time lies outside (0,42]")
        elif self.completion_time_seconds != 42.0:
            raise EvaluationContractError("failure/timeout completion time must be exactly 42 s")
        if not math.isfinite(self.active_effort_sum) or self.active_effort_sum < 0.0:
            raise EvaluationContractError("active effort sum is invalid")
        if isinstance(self.active_ticks, bool) or not 1 <= self.active_ticks <= 420:
            raise EvaluationContractError("active tick count lies outside [1,420]")
        if self.active_effort_sum > self.active_ticks:
            raise EvaluationContractError("normalized effort exceeds one per active tick")
        if self.post_absorption_policy_queries != 0:
            raise EvaluationContractError("post-absorption policy query is forbidden")


def validate_atomic_evaluation(rows: Iterable[EpisodeEndpoint], *, replicate: int) -> tuple[EpisodeEndpoint, ...]:
    values = tuple(rows)
    if len(values) != 4 * 6 * 120:
        raise EvaluationContractError("replicate evaluation must contain exactly 2,880 episodes")
    lookup: dict[tuple[str, str, int], EpisodeEndpoint] = {}
    for row in values:
        row.validate()
        if row.replicate != replicate:
            raise EvaluationContractError("evaluation mixes replicates")
        key = (row.controller, row.regime, row.scenario_index)
        if key in lookup:
            raise EvaluationContractError("evaluation episode identity is duplicated")
        lookup[key] = row
    expected = {
        (controller, regime, scenario)
        for controller in CONTROLLERS for regime in REGIMES for scenario in range(120)
    }
    if set(lookup) != expected:
        raise EvaluationContractError("evaluation episode inventory is incomplete")
    for regime in REGIMES:
        for scenario in range(120):
            paired = [lookup[(controller, regime, scenario)] for controller in CONTROLLERS]
            if len({row.scenario_digest for row in paired}) != 1:
                raise EvaluationContractError("controller scenario tapes are not paired")
            if len({(row.event_order, row.switch_tick) for row in paired}) != 1:
                raise EvaluationContractError("paired controller scenario labels differ")
        reference = [lookup[("TREAT", regime, scenario)] for scenario in range(120)]
        if regime in ("6-to-14", "14-to-6"):
            counts = {
                (order, tick): sum(
                    row.event_order == order and row.switch_tick == tick for row in reference
                )
                for order in ("RG", "GR") for tick in (168, 252)
            }
            if set(counts.values()) != {30}:
                raise EvaluationContractError("switch order/time cells must each contain 30 episodes")
        else:
            counts = {order: sum(row.event_order == order for row in reference) for order in ("RG", "GR")}
            if counts != {"RG": 60, "GR": 60}:
                raise EvaluationContractError("fixed-regime event orders must each contain 60 episodes")
    return values


def _fraction(values: Sequence[EpisodeEndpoint], field: str) -> float:
    return sum(bool(getattr(row, field)) for row in values) / len(values)


def aggregate_replicate_endpoints(
    rows: Iterable[EpisodeEndpoint], *, replicate: int
) -> dict[str, dict[str, object]]:
    values = validate_atomic_evaluation(rows, replicate=replicate)
    result: dict[str, dict[str, object]] = {}
    for controller in CONTROLLERS:
        controller_rows = tuple(row for row in values if row.controller == controller)
        competence: dict[str, float] = {}
        competence_pool: list[EpisodeEndpoint] = []
        for regime in COMPETENCE_REGIMES:
            for order in ("RG", "GR"):
                cell = [
                    row for row in controller_rows
                    if row.regime == regime and row.event_order == order
                ]
                if len(cell) != 60:
                    raise EvaluationContractError("competence cell denominator differs from 60")
                competence[f"{regime}/{order}"] = _fraction(cell, "safe_delivery")
                competence_pool.extend(cell)
        competence["pooled"] = _fraction(competence_pool, "safe_delivery")

        target_by_regime = {
            regime: [row for row in controller_rows if row.regime == regime]
            for regime in TARGET_REGIMES
        }
        if any(len(cell) != 120 for cell in target_by_regime.values()):
            raise EvaluationContractError("target regime denominator differs from 120")
        target = [row for regime in TARGET_REGIMES for row in target_by_regime[regime]]
        active_ticks = sum(row.active_ticks for row in target)
        result[controller] = {
            "competence": competence,
            "P": _fraction(target, "safe_delivery"),
            "W": min(_fraction(target_by_regime[regime], "safe_delivery") for regime in TARGET_REGIMES),
            "T": sum(row.completion_time_seconds for row in target) / 480.0,
            "E": sum(row.active_effort_sum for row in target) / active_ticks,
            "O": max(_fraction(target_by_regime[regime], "overload") for regime in TARGET_REGIMES),
            "G": max(_fraction(target_by_regime[regime], "swing") for regime in TARGET_REGIMES),
            "F": max(_fraction(target_by_regime[regime], "formation") for regime in TARGET_REGIMES),
            "target_episode_denominator": 480,
            "target_active_tick_denominator": active_ticks,
            "regime_episode_denominator": 120,
        }
    return result
