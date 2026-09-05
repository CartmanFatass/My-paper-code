from fractions import Fraction as F
from itertools import product

from experiments.candidates.variable_n_fleet_churn_causal_headroom.solver import (
    Option, Policy, solve_epoch, solve_epochs,
)


def option(command, x, y, baseline=False):
    return Option((command, 0, 0, 0), (F(x), F(y)), baseline)


def brute(epoch, classes):
    keys = sorted(classes)
    policies = []
    for choices in product(*(classes[key] for key in keys)):
        policies.append(Policy(
            epoch, tuple((key, o.command) for key, o in zip(keys, choices)),
            tuple(sum((o.zone_totals[z] for o in choices), F(0)) for z in range(2)),
            sum(not o.is_baseline for o in choices)))
    return policies


def assert_matches(solved, policies):
    tail = lambda p: (p.deviations, p.epoch, p.action_map)
    assert solved.robust == min(policies, key=lambda p: (
        -min(p.zone_totals), -sum(p.zone_totals), *tail(p)))
    assert solved.aggregate == min(policies, key=lambda p: (
        -sum(p.zone_totals), *tail(p)))
    for z in range(2):
        assert solved.zones[z] == min(policies, key=lambda p: (
            -p.zone_totals[z], *tail(p)))


def test_shared_cross_zone_classes_match_joint_brute_force():
    classes = {
        'b': [option(0, 0, 0, True), option(1, F(3, 7), F(-1, 5)),
              option(2, F(-1, 6), F(2, 3))],
        'a': [option(0, 0, 0, True), option(1, F(1, 2), F(-1, 4)),
              option(2, F(-1, 3), F(3, 5))],
    }
    result = solve_epoch(1, classes)
    assert_matches(result, brute(1, classes))
    assert result.robust.robust > 0
    assert result.stats.complete
    assert result.stats.created == result.stats.retained + result.stats.eliminated
    assert result.stats.action_records == 6
    assert result.stats.created == sum(stage[2] for stage in result.stats.stages)
    assert result.stats.retained == sum(stage[3] for stage in result.stats.stages)
    # Input iteration order cannot affect canonical map selection.
    reversed_input = {key: list(reversed(value)) for key, value in reversed(list(classes.items()))}
    assert solve_epoch(1, reversed_input) == result


def test_exact_small_frontiers_against_exhaustive_rational_panels():
    # Deterministic synthetic panels include ties, negatives and shared choices.
    for panel in range(12):
        classes = {str(k): [option(0, 0, 0, True)] + [
            option(j, F((panel + j * 3 + k) % 7 - 3, 11),
                   F((panel * 2 + j + k * 3) % 9 - 4, 13))
            for j in range(1, 4)] for k in range(3)}
        assert_matches(solve_epoch(0, classes), brute(0, classes))


def test_dominated_policy_still_wins_independent_zone_tie():
    classes = {'shared': [option(0, 0, 0, True), option(1, 0, 1)]}
    result = solve_epoch(0, classes)
    assert result.robust.action_map[0][1][0] == 1  # min ties, aggregate wins
    assert result.zones[0].deviations == 0  # zone ties, BCRH wins
    assert_matches(result, brute(0, classes))


def test_equal_totals_deviation_and_canonical_map_ties():
    classes = {'b': [option(0, 0, 0, True), option(2, 1, 1)],
               'a': [option(0, 0, 0, True), option(2, 1, 1), option(1, 1, 1)]}
    result = solve_epoch(2, classes)
    assert result.robust.action_map == (('a', (1, 0, 0, 0)), ('b', (2, 0, 0, 0)))
    assert_matches(result, brute(2, classes))
    zero = {'a': [option(0, 0, 0), option(9, 0, 0, True)]}
    assert solve_epoch(2, zero).robust.deviations == 0


def test_epoch_tie_order_after_deviation_count():
    early = {'a': [option(0, 0, 0, True), option(1, 1, 1)],
             'b': [option(0, 0, 0, True), option(1, 1, 1)]}
    later = {'a': [option(0, 0, 0, True), option(9, 2, 2)]}
    result = solve_epochs([solve_epoch(0, early), solve_epoch(2, later)])
    assert result.robust.epoch == 2  # fewer deviations outranks earlier epoch
    assert_matches(result, brute(0, early) + brute(2, later))
    same_early = {'z': [option(0, 0, 0, True), option(9, 2, 2)]}
    result = solve_epochs([solve_epoch(2, later), solve_epoch(0, same_early)])
    assert result.robust.epoch == 0  # epoch outranks lexicographic map
    assert_matches(result, brute(2, later) + brute(0, same_early))


def test_sub_float_gap_and_mean_denominators():
    tiny = F(1, 10**30)
    classes = {'a': [option(0, 0, 0, True), option(1, 1, 1),
                     option(9, 1 + tiny, 1 + tiny)]}
    result = solve_epoch(0, classes)
    assert result.robust.action_map[0][1][0] == 9
    assert result.robust.zone_means == ((1 + tiny) / 8,) * 2
    assert result.robust.aggregate == (1 + tiny) / 8
    assert_matches(result, brute(0, classes))
