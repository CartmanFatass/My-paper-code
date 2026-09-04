"""Fresh paired finite-host population and environment execution."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterable

from .contract import CONTEXTS, K_EVAL, K_TRAIN, MARKS, WorkloadConfig, context_id
from .oracle import posterior_short, tail_q
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
    displayed_short_count: int | None
    belief_short: Fraction
    probe_primitive: float
    tail_return: float
    transition_count: int


@dataclass(frozen=True)
class Execution:
    displayed_short_count: int | None
    root_action: str
    tail_period: int
    external_return: float
    probe_primitive: float
    tail_return: float
    transition_count: int


def behavior_stratum(episode_index: int) -> tuple[str, int]:
    if type(episode_index) is not int or episode_index < 0:
        raise ValueError("episode index must be nonnegative")
    offset = episode_index % 10
    return ("PROBE", K_TRAIN[offset]) if offset < 5 else ("IMMEDIATE", K_TRAIN[offset - 5])


def group_fold(episode_index: int) -> int:
    return (episode_index // 10) % 2


def execute_episode(
    context: tuple[str, Fraction, Fraction], *, ancestry: tuple[object, ...], episode_index: int,
    root_action: str, support: tuple[int, ...], immediate_period: int | None = None,
    tail_selector: Callable[[int], int] | None = None, evaluation: bool = False,
) -> Execution:
    if root_action not in {"PROBE", "IMMEDIATE"} or support not in (K_TRAIN, K_EVAL):
        raise ValueError("invalid execution action/support")
    link, reliability, cost = context
    prefix = "eval-" if evaluation else ""
    regime = "SHORT" if bernoulli(0.5, f"{prefix}regime", *ancestry, episode_index) else "LONG"
    displayed = None
    primitive = 0.0
    if root_action == "PROBE":
        if tail_selector is None or immediate_period is not None:
            raise ValueError("PROBE requires one tail selector")
        display_regime = regime if link == "LINKED" else ("SHORT" if bernoulli(0.5, f"{prefix}display-regime", *ancestry, episode_index) else "LONG")
        namespace = f"{prefix}mark" if link == "LINKED" else f"{prefix}display-mark"
        displayed = sum(bernoulli(float(reliability if display_regime == "SHORT" else 1 - reliability), namespace, *ancestry, episode_index, counter=mark) for mark in range(MARKS))
        period = tail_selector(displayed)
        actual = sum(bernoulli(float(reliability if regime == "SHORT" else 1 - reliability), f"{prefix}mark", *ancestry, episode_index, counter=mark) for mark in range(MARKS))
        primitive = float(Fraction(2, 25) * Fraction(actual, MARKS)) - 0.03 - float(cost - Fraction(3, 100))
    else:
        if tail_selector is not None or type(immediate_period) is not int:
            raise ValueError("IMMEDIATE requires one period")
        period = immediate_period
    if period not in support:
        raise ValueError("selected period outside execution support")
    service = float(bernoulli(float(tail_q(regime, period)), f"{prefix}tail-service", *ancestry, episode_index))
    tail_value = service - period / 100.0 - period * period / 1000.0
    return Execution(displayed, root_action, period, primitive + tail_value, primitive, tail_value, 2 + (MARKS if root_action == "PROBE" else 0))


def generate_population(config: WorkloadConfig, seed_id: str) -> tuple[Episode, ...]:
    config.validate()
    if seed_id not in config.seed_ids:
        raise ValueError("seed is outside workload binding")
    rows = []
    for episode_index in range(config.episodes_per_context):
        action, period = behavior_stratum(episode_index)
        for context in CONTEXTS:
            link, reliability, cost = context
            execution = execute_episode(
                context, ancestry=(config.run_id, seed_id), episode_index=episode_index,
                root_action=action, support=K_TRAIN,
                immediate_period=period if action == "IMMEDIATE" else None,
                tail_selector=(lambda _count, fixed=period: fixed) if action == "PROBE" else None,
            )
            belief = posterior_short(link, reliability, execution.displayed_short_count) if execution.displayed_short_count is not None else Fraction(1, 2)
            rows.append(Episode(seed_id, episode_index, group_fold(episode_index), context_id(context), link, reliability, cost, action, period, execution.displayed_short_count, belief, execution.probe_primitive, execution.tail_return, execution.transition_count))
    validate_population(config, seed_id, rows)
    return tuple(rows)


def validate_population(config: WorkloadConfig, seed_id: str, rows: Iterable[Episode]) -> dict[str, int]:
    values = tuple(rows)
    expected = config.episodes_per_context * len(CONTEXTS)
    if len(values) != expected:
        raise ValueError("population size drift")
    counts = {(context_id(c), fold, action, period): 0 for c in CONTEXTS for fold in (0, 1) for action in ("PROBE", "IMMEDIATE") for period in K_TRAIN}
    for row in values:
        if row.seed_id != seed_id or row.fold_id != group_fold(row.episode_index):
            raise ValueError("population ancestry/fold drift")
        counts[(row.context_id, row.fold_id, row.behavior_action, row.behavior_period)] += 1
    if set(counts.values()) != {config.episodes_per_context // 20}:
        raise ValueError("population stratum drift")
    return {"episodes": expected, "transitions": sum(row.transition_count for row in values), "root_rows": expected, "tail_rows": expected // 2}


def ordered_rows(population: Iterable[Episode], *, fold_id: int, stage: str) -> tuple[Episode, ...]:
    if fold_id not in (0, 1) or stage not in {"tail", "root"}:
        raise ValueError("invalid fold/stage")
    owner = 1 - fold_id if stage == "tail" else fold_id
    rows = [row for row in population if row.fold_id == owner and (stage != "tail" or row.behavior_action == "PROBE")]
    return tuple(sorted(rows, key=lambda row: (row.episode_index, row.context_id)))
