from __future__ import annotations

import inspect
from dataclasses import fields

import pytest

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    clock_controls as clocks,
)


class SpyUniform:
    def __init__(self, value: float = 0.0) -> None:
        self.value = value
        self.calls = 0

    def uniform(self) -> float:
        self.calls += 1
        return self.value


class SpyReceiver:
    def __init__(self) -> None:
        self.events = []

    def receive_rate_event(self, event: clocks.ExecutedRateEvent) -> None:
        self.events.append(event)


def test_rate_contract_types_expose_only_rate_spacing_and_real_boundary_eligibility():
    assert clocks.RateEvent is clocks.ExecutedRateEvent
    assert clocks.ExecutedRateReceipt is clocks.RateEventReceipt
    assert clocks.UniformSource is clocks.RateUniformSource
    assert clocks.RateReceiver is clocks.RateControlReceiver
    assert tuple(field.name for field in fields(clocks.ClockControlSpec)) == (
        "events_per_primitive_tick",
        "nonstacking_service",
        "service_before_boundary_action",
    )
    assert tuple(field.name for field in fields(clocks.PrimitiveSpacing)) == ("primitive_ticks",)
    assert tuple(field.name for field in fields(clocks.EligibleBoundary)) == ("eligible", "spacing")
    assert tuple(inspect.signature(clocks.execute_rate_event).parameters) == (
        "spec",
        "boundary",
        "uniform_source",
        "receiver",
    )
    exposed = {
        field.name
        for kind in (clocks.ClockControlSpec, clocks.PrimitiveSpacing, clocks.EligibleBoundary)
        for field in fields(kind)
    }
    assert not exposed & {
        "graph",
        "order",
        "action",
        "logits",
        "task",
        "age",
        "tape",
        "reward",
        "outcome",
        "result",
    }


def test_rate_probability_is_min_one_spacing_times_physical_rate_and_rejects_coercion():
    spec = clocks.ClockControlSpec(events_per_primitive_tick=0.03)
    assert clocks.rate_probability(spec, clocks.PrimitiveSpacing(13)) == pytest.approx(0.39)
    assert clocks.rate_probability(spec, clocks.PrimitiveSpacing(50)) == 1.0
    with pytest.raises((TypeError, clocks.ClockControlError)):
        clocks.rate_probability(spec, True)
    with pytest.raises((TypeError, clocks.ClockControlError)):
        clocks.rate_probability(spec, "13")


@pytest.mark.parametrize("label", ("dummy", "masked", "inactive"))
def test_dummy_masked_or_inactive_boundary_calls_neither_rng_nor_receiver(label: str):
    source = SpyUniform()
    receiver = SpyReceiver()
    receipt = clocks.execute_rate_event(
        clocks.ClockControlSpec(0.5),
        clocks.EligibleBoundary(False, clocks.PrimitiveSpacing(13)),
        source,
        receiver,
    )

    assert label in {"dummy", "masked", "inactive"}  # three host no-call meanings, one seam value
    assert (receipt.eligible, receipt.sampled, receipt.executed, receipt.receiver_called) == (
        False,
        False,
        False,
        False,
    )
    assert source.calls == 0
    assert receiver.events == []


def test_real_eligible_boundary_samples_once_and_receives_only_on_execution():
    spec = clocks.ClockControlSpec(0.02)
    boundary = clocks.EligibleBoundary(True, clocks.PrimitiveSpacing(13))
    source = SpyUniform(0.25)
    receiver = SpyReceiver()
    receipt = clocks.execute_rate_event(spec, boundary, source, receiver)
    assert receipt.executed is True and receipt.probability == pytest.approx(0.26)
    assert source.calls == 1 and len(receiver.events) == 1

    source = SpyUniform(0.26)  # strict inverse-CDF boundary: contact does not execute
    receiver = SpyReceiver()
    receipt = clocks.execute_rate_event(spec, boundary, source, receiver)
    assert receipt.executed is False
    assert source.calls == 1 and receiver.events == []


def test_service_minus_cost_accounting_and_age_ceiling_are_separate_pure_diagnostics():
    value = clocks.service_cost_breakdown(
        service=8.0,
        event_count=3,
        primitive_ticks=20.0,
        event_cost=0.5,
    )
    assert value.net_total == 6.5
    assert value.service_per_tick == 0.4
    assert value.event_rate_per_tick == 0.15
    assert value.net_per_tick == 0.325

    spec = clocks.ClockControlSpec(0.1)
    assert clocks.age_ceiling(spec, clocks.PrimitiveSpacing(4), 10.0, 1.0) == 9.0 / 12.0
