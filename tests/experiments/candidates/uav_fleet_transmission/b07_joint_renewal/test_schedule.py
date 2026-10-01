"""Clock algebra only: no native environment or scientific policy queries."""
from collections import Counter
from dataclasses import replace
import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b06_cadence.policies import indexed_uniform
from experiments.candidates.uav_fleet_transmission.b07_joint_renewal.contract import FROZEN, Protocol
from experiments.candidates.uav_fleet_transmission.b07_joint_renewal.schedule import (
    hold_ticks, physical_hold_changed, query_due,
)


def test_full_clock_holds_and_equal_individual_draw_sequences():
    protocol = Protocol(worlds=(113, 117), sampling_roots=(171, 173), phase_root=181, bootstrap_seed=189)
    for phase in range(4):
        ticks = [tick for tick in range(256) if query_due(tick, phase)]
        assert ticks == [0, *range(4 + phase, 256, 4)] and len(ticks) == 64
        holds = [hold_ticks(tick, phase, 256) for tick in ticks]
        assert holds == [4 + phase, *([4] * 62), 4 - phase]
        assert sum(holds) == 256
    for world in protocol.worlds:
        offsets = protocol.phase_offsets(world)
        assert sorted(offsets.tolist()) == [0, 0, 1, 2, 3]
        expected = np.random.default_rng(np.random.SeedSequence([181, world])).permutation([0, 0, 1, 2, 3])
        np.testing.assert_array_equal(offsets, expected)
        for agent in range(5):
            for root in protocol.sampling_roots:
                samples = {}
                for schedule in ("SYNC", "DISPERSED"):
                    samples[schedule] = []
                    for q in range(4):
                        p = int(protocol.phases(world, q, schedule)[agent])
                        clock = tuple(t for t in range(256) if query_due(t, p))
                        draws = tuple(indexed_uniform(root, world, t, agent) for t in clock)
                        samples[schedule].append((clock, draws))
                assert sorted(samples["SYNC"]) == sorted(samples["DISPERSED"])


def test_complete_balanced_order_and_exact_price():
    assert FROZEN.expected()["complete_episodes"] == 768
    assert FROZEN.expected()["native_steps"] == 196608
    assert FROZEN.expected()["ordinary_queries"] == 245760
    assert FROZEN.expected()["sampled_draws"] == 163840
    assert 275 * (196608 + 768 + 1) == 54278675
    assert FROZEN.model_ceiling() == dict(trajectories=6635520, model_ticks=26542080,
        objective_reductions=26542080, candidate_link_evaluations=530841600, setup_link_evaluations=24576000)
    first = Counter()
    for wi in range(32):
        cells = FROZEN.episode_order(wi)
        assert len(cells) == len(set(cells)) == 24
        for a, b in zip(cells[::2], cells[1::2]):
            assert (a[0], a[2], a[3]) == (b[0], b[2], b[3])
            assert {a[1], b[1]} == {"SYNC", "DISPERSED"}
            first[a] += 1
    assert len(first) == 24 and set(first.values()) == {16}
    assert FROZEN.episode_order(0)[:6] == [
        ("C", "SYNC", 0, -1), ("C", "DISPERSED", 0, -1),
        ("Q10", "DISPERSED", 0, 0), ("Q10", "SYNC", 0, 0),
        ("Q10", "SYNC", 0, 1), ("Q10", "DISPERSED", 0, 1)]
    for a, b in zip(FROZEN.episode_order(0), FROZEN.episode_order(1)):
        assert (a[0], a[2], a[3]) == (b[0], b[2], b[3]) and a[1] != b[1]
    FROZEN.check_counts(FROZEN.expected())
    bad = FROZEN.expected()
    bad["ordinary_queries"] -= 1
    with pytest.raises(AssertionError):
        FROZEN.check_counts(bad)


@pytest.mark.parametrize("phase", range(4))
def test_only_own_deadlines_and_terminal_truncation(phase):
    assert [t for t in range(8) if query_due(t, phase)] == [0, 4 + phase]
    assert hold_ticks(4 + phase, phase, 8) == 4 - phase
    with pytest.raises(ValueError):
        hold_ticks(1, phase, 8)
    with pytest.raises(ValueError):
        hold_ticks(256, phase, 256)


@pytest.mark.parametrize("tick,phase", [(False, 0), (-1, 0), (0., 0), (0, True), (0, -1), (0, 4)])
def test_bad_addresses(tick, phase):
    with pytest.raises(ValueError):
        query_due(tick, phase)


def test_clipped_alias_and_changed_hold():
    assert not physical_hold_changed([0., 0., 50.], [-1., -1., -1.], [0., 0., 0.], 7)
    assert physical_hold_changed([500., 500., 100.], [1., 0., 0.], [-1., 0., 0.], 1)
    assert physical_hold_changed([990., 500., 100.], [1., 0., 0.], [0., 0., 0.], 4)
    assert not physical_hold_changed([1000., 500., 100.], [1., 0., 0.], [0., 0., 0.], 4)


@pytest.mark.parametrize("changes", [{"worlds": (1, 1)}, {"phase_root": 29750101}, {"horizon": 7},
                                   {"bootstrap_resamples": False}, {"worlds": (True,)}])
def test_invalid_protocol(changes):
    with pytest.raises(ValueError):
        replace(FROZEN, **changes).validate()
