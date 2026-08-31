from fractions import Fraction

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01.contract import MARK_COUNT, SEED_SLOTS
from experiments.candidates.ucope.contextual_paid_acquisition_r01.host import (
    belief_for_record,
    primitive_probe_components,
    simulate_episode,
)
from experiments.candidates.ucope.contextual_paid_acquisition_r01.oracle import tail_energy, tail_time
from experiments.candidates.ucope.contextual_paid_acquisition_r01.schema import PlanEntry


@pytest.mark.parametrize("cost", [Fraction(9, 100), Fraction(14, 100)])
@pytest.mark.parametrize("short_count", range(7))
def test_probe_primitive_ledger_uses_actual_six_mark_tape(cost, short_count):
    marks = ("SHORT",) * short_count + ("LONG",) * (MARK_COUNT - short_count)
    service, time, energy = primitive_probe_components(marks, cost)
    assert service == Fraction(2, 25) * Fraction(short_count, 6)
    assert time == -Fraction(3, 100)
    assert energy == -(cost - Fraction(3, 100))
    assert service + time + energy == Fraction(2, 25) * Fraction(short_count, 6) - cost


def test_episode_counters_and_unshaped_ledger_are_event_time_period_explicit():
    context = {"link": "LINKED", "reliability": Fraction(17, 20), "total_cost": Fraction(9, 100)}
    probe = simulate_episode(SEED_SLOTS[0], context, PlanEntry(7, "PROBE", 5), "SHORT")
    immediate = simulate_episode(SEED_SLOTS[0], context, PlanEntry(7, "IMMEDIATE", 5), "SHORT")
    assert (probe.primitive_ledger.executed_probe_count, probe.primitive_ledger.executed_probe_mark_count, probe.primitive_ledger.executed_probe_time_units) == (1, 6, 2)
    assert (immediate.primitive_ledger.executed_probe_count, immediate.primitive_ledger.executed_probe_mark_count, immediate.primitive_ledger.executed_probe_time_units) == (0, 0, 0)
    for record in (probe, immediate):
        ledger = record.primitive_ledger
        assert ledger.executed_tail_commit_count == 1
        assert ledger.executed_tail_period_units == 5
        assert ledger.tail_time == float(tail_time(5))
        assert ledger.tail_energy == float(tail_energy(5))
        assert record.tail_return == ledger.tail_total
        assert record.unshaped_return == ledger.total
    assert immediate.primitive_ledger.probe_total == 0
    assert immediate.immediate_return == immediate.tail_return
    assert probe.immediate_return == 0


def test_severed_display_tape_is_independent_and_cannot_change_service():
    context = {"link": "SEVERED", "reliability": Fraction(17, 20), "total_cost": Fraction(9, 100)}
    pair = None
    for index in range(100):
        short_display = simulate_episode(SEED_SLOTS[1], context, PlanEntry(index, "PROBE", 3), "LONG", "SHORT")
        long_display = simulate_episode(SEED_SLOTS[1], context, PlanEntry(index, "PROBE", 3), "LONG", "LONG")
        if short_display.displayed_marks != long_display.displayed_marks:
            pair = short_display, long_display
            break
    assert pair is not None
    first, second = pair
    assert first.actual_marks == second.actual_marks
    assert first.primitive_ledger.probe_service == second.primitive_ledger.probe_service
    expected = float(Fraction(2, 25) * Fraction(first.actual_marks.count("SHORT"), 6))
    assert first.primitive_ledger.probe_service == expected
    assert first.displayed_marks != first.actual_marks or second.displayed_marks != second.actual_marks
    assert belief_for_record(first.to_dict()) == belief_for_record(second.to_dict()) == Fraction(1, 2)


def test_linked_display_is_the_actual_tape_and_mismatch_is_rejected():
    context = {"link": "LINKED", "reliability": Fraction(13, 20), "total_cost": Fraction(14, 100)}
    record = simulate_episode(SEED_SLOTS[2], context, PlanEntry(1, "PROBE", 7), "SHORT")
    assert record.displayed_regime == record.regime
    assert record.displayed_marks == record.actual_marks
    with pytest.raises(ValueError):
        simulate_episode(SEED_SLOTS[2], context, PlanEntry(1, "PROBE", 7), "SHORT", "LONG")


def test_episode_rejects_seed_outside_frozen_slots():
    context = {"link": "LINKED", "reliability": Fraction(13, 20), "total_cost": Fraction(9, 100)}
    with pytest.raises(ValueError):
        simulate_episode("not-a-frozen-seed", context, PlanEntry(1, "PROBE", 3), "SHORT")


@pytest.mark.parametrize("marks", [(), ("SHORT",) * 5, ("SHORT",) * 7, ("BAD",) * 6])
def test_primitive_tape_shape_and_alphabet_fail_closed(marks):
    with pytest.raises(ValueError):
        primitive_probe_components(marks, Fraction(9, 100))
