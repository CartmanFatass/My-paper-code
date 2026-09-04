"""Fresh paired finite-host population and deterministic behavior schedule."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterable

from .contract import CONTEXTS, K_TRAIN, MARKS, ScoutConfig, context_id
from .oracle import posterior_short, tail_q, tail_return
from .rng import bernoulli


@dataclass(frozen=True)
class Episode:
    seed_id: str
    episode_index: int
    fold_id: int
    context_id: str
    link: str
    reliability: Fraction
    total_cost: Fraction
    behavior_action: str
    behavior_period: int
    regime: str
    displayed_short_count: int | None
    belief_short: Fraction
    probe_primitive: float
    tail_return: float
    transition_count: int


@dataclass(frozen=True)
class PolicyExecution:
    regime: str
    displayed_short_count: int | None
    root_action: str
    tail_period: int
    probe_service: float
    probe_time: float
    probe_energy: float
    tail_service: float
    tail_time: float
    tail_energy: float
    external_return: float
    transition_count: int


def behavior_stratum(episode_index: int) -> tuple[str, int]:
    if type(episode_index) is not int or episode_index < 0:
        raise ValueError("episode index must be nonnegative")
    offset = episode_index % 10
    return ("PROBE", K_TRAIN[offset]) if offset < 5 else ("IMMEDIATE", K_TRAIN[offset - 5])


def group_fold(episode_index: int) -> int:
    return (episode_index // 10) % 2


def _marks(regime: str, p: Fraction, namespace: str, seed: str, index: int) -> int:
    chance = p if regime == "SHORT" else 1 - p
    return sum(bernoulli(float(chance), namespace, seed, index, counter=mark) for mark in range(MARKS))


def execute_policy_episode(
    context: tuple[str, Fraction, Fraction],
    *,
    ancestry: tuple[object, ...],
    episode_index: int,
    root_action: str,
    immediate_period: int | None = None,
    tail_selector: Callable[[int], int] | None = None,
    evaluation: bool = False,
) -> PolicyExecution:
    """Execute the shared root/mark/tail environment law for behavior or evaluation."""
    if root_action not in {"PROBE", "IMMEDIATE"}:
        raise ValueError("root action must be PROBE or IMMEDIATE")
    link, p, cost = context
    prefix = "eval-" if evaluation else ""
    regime = "SHORT" if bernoulli(0.5, f"{prefix}regime", *ancestry, episode_index) else "LONG"
    displayed_count = None
    probe_service = probe_time = probe_energy = 0.0
    if root_action == "PROBE":
        if tail_selector is None or immediate_period is not None:
            raise ValueError("PROBE requires exactly one tail selector")
        display_regime = regime if link == "LINKED" else ("SHORT" if bernoulli(0.5, f"{prefix}display-regime", *ancestry, episode_index) else "LONG")
        mark_namespace = f"{prefix}mark" if link == "LINKED" else f"{prefix}display-mark"
        displayed_count = sum(
            bernoulli(float(p if display_regime == "SHORT" else 1 - p), mark_namespace, *ancestry, episode_index, counter=mark)
            for mark in range(MARKS)
        )
        period = tail_selector(displayed_count)
        actual_count = sum(
            bernoulli(float(p if regime == "SHORT" else 1 - p), f"{prefix}mark", *ancestry, episode_index, counter=mark)
            for mark in range(MARKS)
        )
        probe_service = float(Fraction(2, 25) * Fraction(actual_count, MARKS))
        probe_time = -0.03
        probe_energy = -float(cost - Fraction(3, 100))
    else:
        if tail_selector is not None or type(immediate_period) is not int:
            raise ValueError("IMMEDIATE requires exactly one period")
        period = immediate_period
    if period not in K_TRAIN and evaluation is False:
        raise ValueError("training execution requires odd-K action")
    if evaluation and period not in (2, 4, 6, 8):
        raise ValueError("evaluation execution requires held-out even-K action")
    # The episode-root uniform is shared across arms; the selected period changes only its
    # threshold. This is the paired evaluation law, not action-indexed RNG resampling.
    service = float(bernoulli(float(tail_q(regime, period)), f"{prefix}tail-service", *ancestry, episode_index))
    tail_time_value = -period / 100.0
    tail_energy_value = -period * period / 1000.0
    external = probe_service + probe_time + probe_energy + service + tail_time_value + tail_energy_value
    return PolicyExecution(
        regime, displayed_count, root_action, period, probe_service, probe_time, probe_energy,
        service, tail_time_value, tail_energy_value, external, 2 + (MARKS if root_action == "PROBE" else 0),
    )


def generate_population(config: ScoutConfig, seed_id: str) -> tuple[Episode, ...]:
    config.validate()
    if seed_id not in config.seed_ids:
        raise ValueError("seed is not bound to configuration")
    rows = []
    for index in range(config.episodes_per_context):
        action, period = behavior_stratum(index)
        for link, p, cost in CONTEXTS:
            execution = execute_policy_episode(
                (link, p, cost), ancestry=(seed_id,), episode_index=index, root_action=action,
                immediate_period=period if action == "IMMEDIATE" else None,
                tail_selector=(lambda _count, period=period: period) if action == "PROBE" else None,
                evaluation=False,
            )
            count = execution.displayed_short_count
            belief = posterior_short(link, p, count) if count is not None else Fraction(1, 2)
            rows.append(
                Episode(
                    seed_id=seed_id,
                    episode_index=index,
                    fold_id=group_fold(index),
                    context_id=context_id((link, p, cost)),
                    link=link,
                    reliability=p,
                    total_cost=cost,
                    behavior_action=action,
                    behavior_period=period,
                    regime=execution.regime,
                    displayed_short_count=count,
                    belief_short=belief,
                    probe_primitive=execution.probe_service + execution.probe_time + execution.probe_energy,
                    tail_return=execution.tail_service + execution.tail_time + execution.tail_energy,
                    transition_count=execution.transition_count,
                )
            )
    validate_population(config, seed_id, rows)
    return tuple(rows)


def validate_population(config: ScoutConfig, seed_id: str, rows: Iterable[Episode]) -> dict[str, object]:
    values = tuple(rows)
    expected = config.episodes_per_context * len(CONTEXTS)
    if len(values) != expected:
        raise ValueError("population size drift")
    cells = {context_id(context) for context in CONTEXTS}
    counts = {(cell, fold, action, period): 0 for cell in cells for fold in (0, 1) for action in ("PROBE", "IMMEDIATE") for period in K_TRAIN}
    displayed = {(cell, fold): {count: 0 for count in range(7)} for cell in cells for fold in (0, 1)}
    group_folds = {}
    for row in values:
        if row.seed_id != seed_id or row.context_id not in cells or row.fold_id != group_fold(row.episode_index):
            raise ValueError("population binding/fold mismatch")
        if row.behavior_period not in K_TRAIN or row.behavior_action not in {"PROBE", "IMMEDIATE"}:
            raise ValueError("held-out or invalid action reached training population")
        prior = group_folds.setdefault(row.episode_index, row.fold_id)
        if prior != row.fold_id:
            raise ValueError("context group split across folds")
        counts[(row.context_id, row.fold_id, row.behavior_action, row.behavior_period)] += 1
        if row.behavior_action == "PROBE":
            if row.displayed_short_count is None:
                raise ValueError("PROBE row lacks displayed-count support")
            displayed[(row.context_id, row.fold_id)][row.displayed_short_count] += 1
        elif row.displayed_short_count is not None:
            raise ValueError("IMMEDIATE row contains counterfactual displayed marks")
    expected_per_stratum = config.episodes_per_context // 20
    if set(counts.values()) != {expected_per_stratum}:
        raise ValueError("behavior/fold stratum parity drift")
    missing = {key: tuple(count for count, n in counter.items() if n == 0) for key, counter in displayed.items() if any(n == 0 for n in counter.values())}
    return {
        "episodes": len(values),
        "transitions": sum(row.transition_count for row in values),
        "root_rows": len(values),
        "tail_rows": len(values) // 2,
        "displayed_count_support": displayed,
        "support_limited": bool(missing),
        "missing_displayed_counts": missing,
    }


def expected_tail_mean(record: Episode) -> float:
    return float(record.belief_short * tail_return("SHORT", record.behavior_period) + (1 - record.belief_short) * tail_return("LONG", record.behavior_period))
