"""Exact finite causal action-map optimization; no native execution or RNG.

Each class contributes paired advantage totals over its worlds, separately by
zone. Classes may span zones: an option is chosen once for the whole class.
Inputs are nonempty finite classes keyed by canonical strings, each including
BCRH. Totals are Fractions, with eight worlds per zone (including worlds in
other classes). No tolerance, frontier truncation, or approximate pruning.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Option:
    command: tuple[int, int, int, int]
    zone_totals: tuple[Fraction, Fraction]
    is_baseline: bool


@dataclass(frozen=True)
class Policy:
    epoch: int
    action_map: tuple[tuple[str, tuple[int, int, int, int]], ...]
    zone_totals: tuple[Fraction, Fraction]
    deviations: int

    @property
    def zone_means(self):
        return tuple(value / 8 for value in self.zone_totals)

    @property
    def aggregate(self):
        return sum(self.zone_totals, Fraction(0)) / 16

    @property
    def robust(self):
        return min(self.zone_totals) / 8


@dataclass(frozen=True)
class Stats:
    # Cumulative counts across class expansions, not just the final frontier.
    created: int
    retained: int
    eliminated: int
    class_count: int
    action_records: int
    final_frontier: int
    complete: bool
    # (epoch, class key, expanded states, retained states) in execution order.
    stages: tuple[tuple[int, str, int, int], ...]


@dataclass(frozen=True)
class Solution:
    robust: Policy
    aggregate: Policy
    zones: tuple[Policy, Policy]
    stats: Stats


def _tie(policy):
    return policy.deviations, policy.epoch, policy.action_map


def _extend(policy, key, option):
    return Policy(
        policy.epoch,
        policy.action_map + ((key, option.command),),
        tuple(a + b for a, b in zip(policy.zone_totals, option.zone_totals)),
        policy.deviations + int(not option.is_baseline),
    )


def _frontier(states):
    """Equal totals keep the tie winner; strict dominance is safe for robust.

    If coordinate dominance ties the minimum, it strictly improves aggregate.
    Identical future extensions preserve both dominance and prefix tie ordering.
    Separate scalar optima below avoid dropping a zone-primary tie winner.
    """
    by_totals = {}
    for policy in states:
        old = by_totals.get(policy.zone_totals)
        if old is None or _tie(policy) < _tie(old):
            by_totals[policy.zone_totals] = policy
    retained = []
    highest_second = None
    for totals in sorted(by_totals, reverse=True):
        if highest_second is None or totals[1] > highest_second:
            retained.append(by_totals[totals])
            highest_second = totals[1]
    return retained


def _scalar_policy(epoch, classes, objective):
    # Additivity permits independent class choices for this scalar objective.
    # Ties: fewest deviations, earlier epoch, lexicographically smallest map.
    policy = Policy(epoch, (), (Fraction(0), Fraction(0)), 0)
    for key, options in classes:
        chosen = min(options, key=lambda o: (
            -objective(o.zone_totals), int(not o.is_baseline), o.command))
        policy = _extend(policy, key, chosen)
    return policy


def solve_epoch(epoch: int, classes: Mapping[str, Sequence[Option]]) -> Solution:
    """Complete exact optimization for one fixed epoch.

    State counts describe robust DP expansions; action_records counts all input
    options (including equivalent outcomes). Worst-case frontier size can be
    exponential; synthetic timings are not a universal complexity bound.
    """
    ordered = sorted(classes.items())
    frontier = [Policy(epoch, (), (Fraction(0), Fraction(0)), 0)]
    created = retained = 0
    stages = []
    for key, options in ordered:
        expanded = len(frontier) * len(options)
        created += expanded
        frontier = _frontier(
            _extend(policy, key, option)
            for policy in frontier for option in options
        )
        retained += len(frontier)
        stages.append((epoch, key, expanded, len(frontier)))
    robust = min(frontier, key=lambda p: (-p.robust, -p.aggregate, *_tie(p)))
    aggregate = _scalar_policy(epoch, ordered, lambda totals: sum(totals))
    zones = tuple(_scalar_policy(epoch, ordered, lambda totals: totals[z])
                  for z in range(2))
    return Solution(robust, aggregate, zones, Stats(
        created, retained, created - retained, len(ordered),
        sum(len(options) for _, options in ordered), len(frontier), True,
        tuple(stages)))


def solve_epochs(solutions: Iterable[Solution]) -> Solution:
    """Select across completed epochs using the card's robust tie ladder.

    Independent aggregate/zone objectives use the same deterministic tie tail
    (deviations, epoch, map), without adding another scientific objective.
    """
    solutions = tuple(solutions)
    robust = min((s.robust for s in solutions),
                 key=lambda p: (-p.robust, -p.aggregate, *_tie(p)))
    aggregate = min((s.aggregate for s in solutions),
                    key=lambda p: (-p.aggregate, *_tie(p)))
    zones = tuple(min((s.zones[z] for s in solutions),
                      key=lambda p: (-p.zone_means[z], *_tie(p)))
                  for z in range(2))
    return Solution(robust, aggregate, zones, Stats(
        *(sum(getattr(s.stats, field) for s in solutions) for field in (
            'created', 'retained', 'eliminated', 'class_count',
            'action_records', 'final_frontier')),
        all(s.stats.complete for s in solutions),
        tuple(stage for s in solutions for stage in s.stats.stages)))
