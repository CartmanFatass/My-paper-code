"""Pure, output-disconnected physical-rate receiver seam.

The functions in this module cannot observe an FCEOV graph, action, model,
tape, reward, outcome, result, task field, or service age.  Caller-supplied
service-age algebra is separate from event execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol, runtime_checkable


class ClockControlError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ClockControlSpec:
    events_per_primitive_tick: float
    nonstacking_service: bool = True
    service_before_boundary_action: bool = True

    def validate(self) -> None:
        value = self.events_per_primitive_tick
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ClockControlError("physical event rate must be finite and nonnegative")
        if self.nonstacking_service is not True or self.service_before_boundary_action is not True:
            raise ClockControlError("age ceiling requires nonstacking, service-before-boundary ordering")


@dataclass(frozen=True, slots=True)
class PrimitiveSpacing:
    primitive_ticks: float

    def validate(self) -> None:
        if (
            isinstance(self.primitive_ticks, bool)
            or not isinstance(self.primitive_ticks, (int, float))
            or not math.isfinite(self.primitive_ticks)
            or self.primitive_ticks <= 0
        ):
            raise ClockControlError("primitive spacing must be finite and positive")


@dataclass(frozen=True, slots=True)
class EligibleBoundary:
    eligible: bool
    spacing: PrimitiveSpacing

    def validate(self) -> None:
        if not isinstance(self.eligible, bool):
            raise ClockControlError("boundary eligibility must be bool")
        self.spacing.validate()


@dataclass(frozen=True, slots=True)
class ExecutedRateEvent:
    spacing: PrimitiveSpacing


@dataclass(frozen=True, slots=True)
class RateEventReceipt:
    eligible: bool
    sampled: bool
    executed: bool
    probability: float
    receiver_called: bool


@dataclass(frozen=True, slots=True)
class ServiceCostBreakdown:
    service: float
    event_count: int
    primitive_ticks: float
    event_cost: float
    net_total: float
    service_per_tick: float
    event_rate_per_tick: float
    net_per_tick: float


@runtime_checkable
class RateUniformSource(Protocol):
    def uniform(self) -> float: ...


@runtime_checkable
class RateControlReceiver(Protocol):
    def receive_rate_event(self, event: ExecutedRateEvent) -> None: ...


def rate_probability(spec: ClockControlSpec, spacing: PrimitiveSpacing | float) -> float:
    spec.validate()
    if isinstance(spacing, PrimitiveSpacing):
        value = spacing
    elif isinstance(spacing, bool) or not isinstance(spacing, (int, float)):
        raise ClockControlError("primitive spacing must be a real scalar or PrimitiveSpacing")
    else:
        value = PrimitiveSpacing(float(spacing))
    value.validate()
    return min(1.0, value.primitive_ticks * float(spec.events_per_primitive_tick))


def execute_rate_event(
    spec: ClockControlSpec,
    boundary: EligibleBoundary,
    uniform_source: RateUniformSource,
    receiver: RateControlReceiver,
) -> RateEventReceipt:
    spec.validate()
    boundary.validate()
    probability = rate_probability(spec, boundary.spacing)
    if not boundary.eligible:
        return RateEventReceipt(False, False, False, probability, False)
    if not isinstance(uniform_source, RateUniformSource) or not isinstance(receiver, RateControlReceiver):
        raise TypeError("eligible RATE execution requires uniform source and receiver protocols")
    uniform = uniform_source.uniform()
    if isinstance(uniform, bool) or not isinstance(uniform, (int, float)) or not math.isfinite(uniform) or not 0 <= uniform < 1:
        raise ClockControlError("RATE uniform must lie in [0,1)")
    executed = float(uniform) < probability
    if executed:
        receiver.receive_rate_event(ExecutedRateEvent(boundary.spacing))
    return RateEventReceipt(True, True, executed, probability, executed)


def service_cost_breakdown(
    service: float,
    event_count: int,
    primitive_ticks: float,
    event_cost: float,
) -> ServiceCostBreakdown:
    values = (service, primitive_ticks, event_cost)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
        raise ClockControlError("service accounting inputs must be finite real values")
    if isinstance(event_count, bool) or not isinstance(event_count, int) or event_count < 0:
        raise ClockControlError("event count must be a nonnegative integer")
    if primitive_ticks <= 0 or event_cost < 0:
        raise ClockControlError("primitive ticks must be positive and event cost nonnegative")
    net = float(service) - float(event_cost) * event_count
    return ServiceCostBreakdown(
        float(service), event_count, float(primitive_ticks), float(event_cost), net,
        float(service) / primitive_ticks,
        event_count / primitive_ticks,
        net / primitive_ticks,
    )


def age_conditioned_ceiling(
    spec: ClockControlSpec,
    spacing: PrimitiveSpacing | float,
    service_lifetime: float,
    event_cost: float,
) -> float:
    spec.validate()
    if isinstance(spacing, PrimitiveSpacing):
        value = spacing
    elif isinstance(spacing, bool) or not isinstance(spacing, (int, float)):
        raise ClockControlError("primitive spacing must be a real scalar or PrimitiveSpacing")
    else:
        value = PrimitiveSpacing(float(spacing))
    value.validate()
    if any(
        isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item)
        for item in (service_lifetime, event_cost)
    ):
        raise ClockControlError("age-ceiling inputs must be finite real values")
    if service_lifetime <= 0 or event_cost < 0:
        raise ClockControlError("service lifetime must be positive and event cost nonnegative")
    tau = value.primitive_ticks * math.ceil(service_lifetime / value.primitive_ticks)
    return (service_lifetime - event_cost) / tau


age_ceiling = age_conditioned_ceiling
service_cost = service_cost_breakdown
RateEvent = ExecutedRateEvent
ExecutedRateReceipt = RateEventReceipt
UniformSource = RateUniformSource
RateReceiver = RateControlReceiver


__all__ = [
    "ClockControlError", "ClockControlSpec", "EligibleBoundary", "ExecutedRateEvent",
    "ExecutedRateReceipt", "PrimitiveSpacing", "RateControlReceiver", "RateEvent", "RateEventReceipt",
    "RateReceiver", "RateUniformSource", "ServiceCostBreakdown", "UniformSource",
    "age_ceiling", "age_conditioned_ceiling", "execute_rate_event", "rate_probability",
    "service_cost", "service_cost_breakdown",
]
