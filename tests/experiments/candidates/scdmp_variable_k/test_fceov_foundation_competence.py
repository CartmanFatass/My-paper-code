from __future__ import annotations

from dataclasses import fields
from math import comb
from types import SimpleNamespace

import pytest

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    contracts,
    foundation,
    rng as fceov_rng,
)


ALPHA = 0.05 / 7.0


def _binomial_tail(probability: float, successes: int, n: int) -> float:
    return sum(
        comb(n, count)
        * probability**count
        * (1.0 - probability) ** (n - count)
        for count in range(successes, n + 1)
    )


def _binomial_cdf(probability: float, successes: int, n: int) -> float:
    return sum(
        comb(n, count)
        * probability**count
        * (1.0 - probability) ** (n - count)
        for count in range(successes + 1)
    )


def _bisect_increasing(function, target: float) -> float:
    low, high = 0.0, 1.0
    for _ in range(100):
        middle = 0.5 * (low + high)
        if function(middle) < target:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def _bisect_decreasing(function, target: float) -> float:
    low, high = 0.0, 1.0
    for _ in range(100):
        middle = 0.5 * (low + high)
        if function(middle) > target:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def test_competence_inventory_is_exactly_120_fresh_missions_balanced_by_graph():
    inventory = foundation.competence_inventory()

    assert len(inventory) == 120
    assert [row.mission for row in inventory] == list(range(120))
    assert {graph: sum(row.graph == graph for row in inventory) for graph in ("HR", "RH")} == {
        "HR": 60,
        "RH": 60,
    }
    assert tuple(field.name for field in fields(foundation.CompetenceMission)) == (
        "mission",
        "graph",
        "graph_mission",
        "initialization_address",
        "disturbance_address_prefix",
    )
    assert len({row.initialization_address for row in inventory}) == 120
    assert len({row.disturbance_address_prefix for row in inventory}) == 120
    assert all(row.graph in row.initialization_address for row in inventory)
    assert all(row.graph in row.disturbance_address_prefix for row in inventory)
    namespaces = {
        row.initialization_address[0] for row in inventory
    } | {row.disturbance_address_prefix[0] for row in inventory}
    assert namespaces == {
        "foundation-competence-initialization",
        "foundation-competence-disturbance",
    }
    assert not namespaces & {
        "foundation-initialization",
        "foundation-training-initialization",
        "foundation-training-disturbance",
        "assay-disturbance",
    }

    assert foundation.validate_competence_rng_contract() == {
        "initial_state_addresses": 120,
        "disturbance_prefixes": 120,
        "domains": 8,
    }
    source = fceov_rng.TestAddressRNG(bytes(reversed(range(32))))
    first_hr, first_rh = inventory[0], inventory[1]
    for mission in (first_hr, first_rh):
        v, y, phi = foundation.competence_initial_draws(source, mission)
        assert 0.0 <= v < 0.03 and -0.01 <= y < 0.01 and -0.01 <= phi < 0.01
        assert foundation.competence_disturbance(
            source, mission, tick=0, component="eta_omega"
        ) in (-0.004, 0.004)
    assert "tape" not in {field.name for field in fields(foundation.CompetenceRecord)}


@pytest.mark.parametrize(
    ("successes", "n", "side"),
    ((0, 60, "lower"), (49, 60, "lower"), (110, 120, "lower"), (0, 120, "upper"), (7, 120, "upper"), (120, 120, "upper")),
)
def test_exact_one_sided_clopper_pearson_bounds(successes: int, n: int, side: str):
    observed = foundation.exact_binomial_bound(successes, n, side=side)

    if side == "lower":
        expected = (
            0.0
            if successes == 0
            else _bisect_increasing(lambda p: _binomial_tail(p, successes, n), ALPHA)
        )
    else:
        expected = (
            1.0
            if successes == n
            else _bisect_decreasing(lambda p: _binomial_cdf(p, successes, n), ALPHA)
        )
    assert observed == pytest.approx(expected, abs=2e-12, rel=0.0)


def _complete_records(*, safe: bool = True):
    return tuple(
        foundation.CompetenceRecord(
            mission=row.mission,
            graph=row.graph,
            complete=True,
            safe_dock=safe,
        )
        for row in foundation.competence_inventory()
    )


def test_competence_uses_one_seven_member_family_and_all_thresholds_are_strict(monkeypatch):
    calls: list[tuple[int, int, str, float]] = []
    boundary_values = iter((0.72, 0.73, 0.85, 0.09, 0.09, 0.09, 0.09))

    def boundary_bound(successes: int, n: int, *, side: str, alpha: float = ALPHA) -> float:
        calls.append((successes, n, side, alpha))
        return next(boundary_values)

    monkeypatch.setattr(foundation, "exact_binomial_bound", boundary_bound)
    gate = foundation.analyze_competence(_complete_records())

    assert gate.complete is True
    assert gate.passed is False  # graph-HR lower bound contacts 0.72
    assert len(calls) == 7
    assert [(n, side) for _, n, side, _ in calls] == [
        (60, "lower"),
        (60, "lower"),
        (120, "lower"),
        (120, "upper"),
        (120, "upper"),
        (120, "upper"),
        (120, "upper"),
    ]
    assert all(alpha == pytest.approx(ALPHA) for *_, alpha in calls)

    failure_boundary = iter((0.73, 0.73, 0.85, 0.10, 0.09, 0.09, 0.09))
    monkeypatch.setattr(
        foundation,
        "exact_binomial_bound",
        lambda successes, n, *, side, alpha=ALPHA: next(failure_boundary),
    )
    assert foundation.analyze_competence(_complete_records()).passed is False

    pooled_boundary = iter((0.73, 0.73, 0.84, 0.09, 0.09, 0.09, 0.09))
    monkeypatch.setattr(
        foundation,
        "exact_binomial_bound",
        lambda successes, n, *, side, alpha=ALPHA: next(pooled_boundary),
    )
    assert foundation.analyze_competence(_complete_records()).passed is False


def test_complete_all_safe_inventory_passes_and_incomplete_inventory_stops_closed():
    passed = foundation.analyze_competence(_complete_records())
    assert passed.complete is True
    assert passed.passed is True
    assert len(passed.graph_lower_bounds) + 1 + len(passed.failure_upper_bounds) == 7

    incomplete = list(_complete_records())
    row = incomplete[0]
    incomplete[0] = foundation.CompetenceRecord(
        mission=row.mission,
        graph=row.graph,
        complete=False,
        safe_dock=False,
    )
    stopped = foundation.analyze_competence(incomplete)
    assert stopped.complete is False
    assert stopped.passed is False
    assert stopped.graph_lower_bounds == ()
    assert stopped.failure_upper_bounds == ()


def test_strict_clopper_pearson_gate_has_exact_integer_count_equivalents():
    assert foundation.exact_binomial_bound(52, 60, side="lower") > 0.72
    assert foundation.exact_binomial_bound(51, 60, side="lower") <= 0.72
    assert foundation.exact_binomial_bound(111, 120, side="lower") > 0.84
    assert foundation.exact_binomial_bound(110, 120, side="lower") <= 0.84
    assert foundation.exact_binomial_bound(4, 120, side="upper") < 0.10
    assert foundation.exact_binomial_bound(5, 120, side="upper") >= 0.10


def test_competence_rejects_bool_mission_alias_and_non_bool_endpoint_flags():
    rows = list(_complete_records())
    rows[0] = foundation.CompetenceRecord(False, "HR", True, True)
    with pytest.raises(foundation.FoundationContractError, match="mission IDs"):
        foundation.analyze_competence(rows)

    rows = list(_complete_records())
    first = rows[0]
    rows[0] = foundation.CompetenceRecord(first.mission, first.graph, 1, True)  # type: ignore[arg-type]
    with pytest.raises(foundation.FoundationContractError, match="flags"):
        foundation.analyze_competence(rows)


def test_native_competence_is_one_fresh_width_120_complete_batch(monkeypatch):
    from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import host_bridge

    captured = []

    def output(*, tick, active, terminal, safe=False, ticks_advanced=None, observation=None):
        return SimpleNamespace(
            observation=(0.0,) * 18 if observation is None else observation,
            tick=tick, active=active, terminal=terminal,
            advanced=tick != 0, hold_k=0 if tick == 0 else 13, next_k=13,
            ticks_advanced=tick if ticks_advanced is None else ticks_advanced,
            safe_dock=safe, dock_tick=tick if safe else None,
            timeout=terminal and not safe and tick == 364,
            cable_overload=terminal and not safe and tick < 364,
            gantry_contact=False, attitude_loss=False, formation_loss=False,
            cumulative_reward=0.0, cumulative_energy=0.0, energy_ticks=tick,
            last_hold_reward_count=0 if tick == 0 else 13,
            last_hold_rewards=(0.0,) * 13,
        )

    class Batch:
        def __init__(self, resets):
            reset_rows = tuple(resets)
            captured.append(reset_rows)
            self.initial = tuple(
                output(
                    tick=0, active=True, terminal=False,
                    observation=contracts.PublicClaimState(
                        v=row.initial_v, y=row.initial_y, phi=row.initial_phi
                    ).observation(),
                )
                for row in reset_rows
            )

        def __enter__(self): return self
        def __exit__(self, *_): return None
        def renew(self, rows):
            assert len(tuple(rows)) == 120
            return tuple(output(tick=13, active=False, terminal=True) for _ in range(120))

    monkeypatch.setattr(host_bridge, "NativeBatch", Batch)
    source = fceov_rng.TestAddressRNG(bytes(range(32)))
    actor_critic = foundation.FoundationActorCritic(source)
    records = foundation.execute_native_competence(foundation.freeze_foundation(actor_critic), source)
    assert len(captured) == 1 and len(captured[0]) == 120
    assert len(records) == 120 and all(row.complete for row in records)
    assert {graph: sum(row.graph == graph for row in records) for graph in ("HR", "RH")} == {"HR": 60, "RH": 60}


def test_native_competence_rejects_initial_terminal_shortcut_and_terminal_endpoint_mutation(monkeypatch):
    from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import host_bridge

    def output(*, tick, active, terminal, safe=False, ticks_advanced=0, observation=None):
        return SimpleNamespace(
            observation=(0.0,) * 18 if observation is None else observation,
            tick=tick, active=active, terminal=terminal,
            advanced=tick != 0, hold_k=0 if tick == 0 else 13, next_k=13,
            ticks_advanced=ticks_advanced, safe_dock=safe,
            timeout=terminal and not safe and tick == 364,
            cable_overload=terminal and not safe and tick < 364,
            gantry_contact=False, attitude_loss=False, formation_loss=False,
            cumulative_reward=0.0, cumulative_energy=0.0, energy_ticks=tick,
            dock_tick=tick if safe else None,
            last_hold_reward_count=0 if tick == 0 else 13,
            last_hold_rewards=(0.0,) * 13,
        )

    class InitialTerminal:
        def __init__(self, resets):
            self.initial = tuple(
                output(
                    tick=0, active=False, terminal=True,
                    observation=contracts.PublicClaimState(
                        v=row.initial_v, y=row.initial_y, phi=row.initial_phi
                    ).observation(),
                )
                for row in resets
            )
        def __enter__(self): return self
        def __exit__(self, *_): return None

    source = fceov_rng.TestAddressRNG(bytes(range(32)))
    frozen = foundation.freeze_foundation(foundation.FoundationActorCritic(source))

    class BadResetCounter:
        def __init__(self, resets):
            rows = []
            for index, row in enumerate(resets):
                value = output(
                    tick=0, active=True, terminal=False,
                    observation=contracts.PublicClaimState(
                        v=row.initial_v, y=row.initial_y, phi=row.initial_phi
                    ).observation(),
                )
                if index == 0:
                    value.cumulative_energy = 1.0
                rows.append(value)
            self.initial = tuple(rows)
        def __enter__(self): return self
        def __exit__(self, *_): return None

    monkeypatch.setattr(host_bridge, "NativeBatch", BadResetCounter)
    with pytest.raises(foundation.FoundationContractError, match="reset state/counters"):
        foundation.execute_native_competence(frozen, source)

    monkeypatch.setattr(host_bridge, "NativeBatch", InitialTerminal)
    with pytest.raises(foundation.FoundationContractError, match="reset state/counters"):
        foundation.execute_native_competence(frozen, source)

    class EndpointMutation:
        def __init__(self, resets):
            self.initial = tuple(
                output(
                    tick=0, active=True, terminal=False,
                    observation=contracts.PublicClaimState(
                        v=row.initial_v, y=row.initial_y, phi=row.initial_phi
                    ).observation(),
                )
                for row in resets
            )
            self.calls = 0
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def renew(self, rows):
            self.calls += 1
            if self.calls == 1:
                return (
                    output(tick=13, active=False, terminal=True, ticks_advanced=13),
                    *(output(tick=13, active=True, terminal=False, ticks_advanced=13) for _ in range(119)),
                )
            return (
                output(tick=13, active=False, terminal=True, safe=True),
                *(output(tick=26, active=False, terminal=True, ticks_advanced=13) for _ in range(119)),
            )

    monkeypatch.setattr(host_bridge, "NativeBatch", EndpointMutation)
    with pytest.raises(foundation.FoundationContractError, match="absorbed.*mutated"):
        foundation.execute_native_competence(frozen, source)


@pytest.mark.parametrize(("safe", "dock_tick", "timeout"), ((True, None, False), (False, None, False)))
def test_native_competence_rejects_malformed_terminal_endpoint_coherence(
    monkeypatch, safe, dock_tick, timeout
):
    from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import host_bridge

    def value(*, reset=None, terminal=False):
        observation = contracts.PublicClaimState(
            v=reset.initial_v, y=reset.initial_y, phi=reset.initial_phi
        ).observation() if reset is not None else (0.0,) * 18
        return SimpleNamespace(
            observation=observation, tick=13 if terminal else 0,
            active=not terminal, terminal=terminal, ticks_advanced=13 if terminal else 0,
            advanced=terminal, hold_k=13 if terminal else 0, next_k=13,
            safe_dock=safe if terminal else False, dock_tick=dock_tick if terminal else None,
            timeout=timeout if terminal else False, cable_overload=False, gantry_contact=False,
            attitude_loss=False, formation_loss=False, cumulative_reward=0.0,
            cumulative_energy=0.0, energy_ticks=13 if terminal else 0,
            last_hold_reward_count=13 if terminal else 0,
            last_hold_rewards=(0.0,) * 13,
        )

    class MalformedEndpoint:
        def __init__(self, resets):
            self.initial = tuple(value(reset=row) for row in resets)
        def __enter__(self): return self
        def __exit__(self, *_): return None
        def renew(self, rows): return tuple(value(terminal=True) for _ in range(120))

    monkeypatch.setattr(host_bridge, "NativeBatch", MalformedEndpoint)
    source = fceov_rng.TestAddressRNG(bytes(range(32)))
    frozen = foundation.freeze_foundation(foundation.FoundationActorCritic(source))
    with pytest.raises(foundation.FoundationContractError, match="terminal"):
        foundation.execute_native_competence(frozen, source)
