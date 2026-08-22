from __future__ import annotations

from dataclasses import fields
from decimal import Decimal, localcontext
from fractions import Fraction
import math
import struct

import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.config import (
    FIXTURE_NAMESPACE,
    PRODUCTION_NAMESPACE,
    ControllerSpec,
    EncounterSpec,
    FixtureTape,
    RouteClass,
    block_specs,
    encounter_order,
    template_index,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.coordinates import (
    Coordinate,
    encode_coordinate,
    materialize_normal,
    materialize_normal_pair,
    materialize_uniform,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.event_transform import (
    event_transform,
    event_transform_bits,
    float_bits,
    reachable_rate_fractions,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.host import (
    Headland90Host,
    legal_linear_tick,
    legal_point,
    line_of_sight,
    project_legal,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.native_backend import (
    production_preflight,
    native_event_transform_bits,
    require_cpp_batched_backend,
    run_native_batch,
    source_sha256,
)


def _fixture(spec: EncounterSpec, shift: float = 0.0) -> FixtureTape:
    states, ticks = spec.total_ticks + 1, spec.total_ticks
    return FixtureTape.from_sequences(
        spec,
        target_lateral=[((index % 9) - 4) * 0.17 + shift for index in range(states)],
        wind_t=[(((index % 7) - 3) * 0.11, ((index % 5) - 2) * -0.13) for index in range(states)],
        wind_r=[(((index % 11) - 5) * -0.07, ((index % 6) - 3) * 0.09) for index in range(states)],
        sensor=[(((index % 4) - 1.5) * 0.2, ((index % 8) - 3.5) * -0.15) for index in range(states)],
        shadow_tr=[((index % 10) - 4.5) * 0.08 for index in range(states)],
        shadow_rb=[((index % 12) - 5.5) * -0.06 for index in range(states)],
        link_tr=[((index * 37) % 101 + 0.5) / 101.0 for index in range(ticks)],
        link_rb=[((index * 53) % 103 + 0.5) / 103.0 for index in range(ticks)],
        action=[((index * 29) % 107 + 0.5) / 107.0 for index in range(ticks)],
    )


def _assert_float_same(a: float, b: float) -> None:
    if math.isnan(a) and math.isnan(b):
        return
    if struct.pack("!d", a) == struct.pack("!d", b):
        return
    # Geometry/radio trig and log10 use independent Python and C++ CRT calls;
    # they may differ by one correctly-rounded ulp. The event transform is
    # separately required to match its frozen authoritative bits exactly.
    assert abs(a - b) <= 4.0 * max(math.ulp(a), math.ulp(b))


def _assert_value_same(a, b) -> None:
    if isinstance(a, float):
        _assert_float_same(a, b)
    elif isinstance(a, tuple):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            _assert_value_same(x, y)
    else:
        assert a == b


def _assert_results_same(python_result, native_result) -> None:
    for name in (
        "scored_valid_ticks", "voluntary_updates", "voluntary_keeps",
        "opportunity_rows", "safety_overrides", "hard_failure",
        "no_planner_solution", "no_safe_control", "battery_exhausted",
    ):
        assert getattr(python_result, name) == getattr(native_result, name)
    assert len(python_result.ticks) == len(native_result.ticks)
    for python_tick, native_tick in zip(python_result.ticks, native_result.ticks):
        for field in fields(python_tick):
            try:
                python_value = getattr(python_tick, field.name)
                native_value = getattr(native_tick, field.name)
                if field.name in ("rate_q", "event_lambda", "event_probability"):
                    assert float_bits(python_value) == float_bits(native_value)
                else:
                    _assert_value_same(python_value, native_value)
            except AssertionError as error:
                raise AssertionError(
                    f"tick {python_tick.tick} field {field.name}: "
                    f"{getattr(python_tick, field.name)!r} != {getattr(native_tick, field.name)!r}"
                ) from error


def test_coordinate_encoding_and_production_activity_fence() -> None:
    coordinate = Coordinate(
        PRODUCTION_NAMESPACE, "CAL", 2, 3, "SHORT", 3, 7, "action", 0
    )
    encoded = encode_coordinate(coordinate)
    assert encoded.startswith(b"32:ONLGR-TBH-HEADLAND90-20260815-v1|3:CAL|")
    with pytest.raises(PermissionError, match="production random-word"):
        materialize_uniform(coordinate)
    with pytest.raises(PermissionError, match="production activity"):
        production_preflight()
    assert len(source_sha256()) == 64
    assert require_cpp_batched_backend().headland90_abi_version() == 1


@pytest.mark.parametrize(
    "changes",
    (
        {"split": "FIXTURE"}, {"replicate": 48}, {"block": 20},
        {"route_class": "BEND"}, {"template": 4}, {"template": 1},
        {"tick": 48}, {"lane": -1},
    ),
)
def test_production_coordinate_schema_rejects_invalid_fields(changes) -> None:
    values = dict(
        namespace=PRODUCTION_NAMESPACE, split="CAL", replicate=0, block=0,
        route_class="SHORT", template=0, tick=0, stream="action", lane=0,
    )
    values.update(changes)
    with pytest.raises(ValueError):
        encode_coordinate(Coordinate(**values))


def test_coordinate_terminal_state_and_fixture_box_muller_order() -> None:
    terminal = Coordinate(
        PRODUCTION_NAMESPACE, "HOLD", 127, 19, "SHORT", 0, 48,
        "target_lateral", 0,
    )
    assert encode_coordinate(terminal)
    with pytest.raises(ValueError, match="physical encounter"):
        encode_coordinate(Coordinate(
            PRODUCTION_NAMESPACE, "HOLD", 127, 19, "SHORT", 0, 48,
            "link_TR", 0,
        ))
    lower = Coordinate(
        FIXTURE_NAMESPACE, "FIXTURE", 7, 2, "LONG", 1, 11, "wind_T", 4
    )
    u_radius = materialize_uniform(lower)
    upper = Coordinate(
        FIXTURE_NAMESPACE, "FIXTURE", 7, 2, "LONG", 1, 11, "wind_T", 5
    )
    u_angle = materialize_uniform(upper)
    radius = math.sqrt(-2.0 * math.log(u_radius))
    expected = (
        radius * math.cos(2.0 * math.pi * u_angle),
        radius * math.sin(2.0 * math.pi * u_angle),
    )
    assert materialize_normal_pair(lower) == expected
    assert materialize_normal(lower) == expected[0]
    assert materialize_normal(upper) == expected[1]
    with pytest.raises(ValueError, match="lower even lane"):
        materialize_normal_pair(upper)
    with pytest.raises(PermissionError, match="production random-word"):
        materialize_normal(terminal)


def _authoritative_event_bits(q: Fraction) -> tuple[int, int]:
    with localcontext() as context:
        context.prec = 220
        q_float = float(q)
        logarithm = (Decimal(1) - Decimal.from_float(q_float)).ln()
        event_lambda = float(-logarithm / Decimal(4))
        exponent = -(Decimal.from_float(event_lambda) * Decimal.from_float(0.25))
        event_probability = float(Decimal(1) - exponent.exp())
    return float_bits(event_lambda), float_bits(event_probability)


def test_all_reachable_event_transforms_match_authoritative_and_native_bits() -> None:
    rates = reachable_rate_fractions()
    assert len(rates) == 456
    assert max(rate.denominator for rate in rates) == 1024
    for rate in rates:
        q_bits, lambda_bits, probability_bits = event_transform_bits(rate)
        assert q_bits == float_bits(float(rate))
        assert (lambda_bits, probability_bits) == _authoritative_event_bits(rate)
        assert native_event_transform_bits(rate) == (lambda_bits, probability_bits)


def test_event_action_strict_comparison_at_adjacent_binary64_uniforms() -> None:
    spec = EncounterSpec(RouteClass.SHORT, 1, 8)
    controller = ControllerSpec.constant(Fraction(1, 2))
    _, _, probability = event_transform(Fraction(1, 2))
    uniforms = (
        math.nextafter(probability, 0.0),
        probability,
        math.nextafter(probability, 1.0),
    )
    fixtures = []
    for index, uniform in enumerate(uniforms):
        base = FixtureTape.constant(spec, uniform=0.5)
        actions = list(base.action)
        actions[16] = uniform
        tape = FixtureTape.from_sequences(
            spec,
            target_lateral=base.target_lateral,
            wind_t=base.wind_t,
            wind_r=base.wind_r,
            sensor=base.sensor,
            shadow_tr=base.shadow_tr,
            shadow_rb=base.shadow_rb,
            link_tr=base.link_tr,
            link_rb=base.link_rb,
            action=actions,
        )
        fixtures.append((spec, tape, controller, f"adjacent-{index}"))
    python_results = tuple(
        Headland90Host().run(specification, tape, policy, logical_tag=tag)
        for specification, tape, policy, tag in fixtures
    )
    native_results = run_native_batch(fixtures)
    assert [result.ticks[16].action for result in python_results] == [
        "JOINT-UPDATE", "KEEP", "KEEP"
    ]
    assert [result.ticks[16].action for result in native_results] == [
        "JOINT-UPDATE", "KEEP", "KEEP"
    ]
    for result in python_results + native_results:
        assert float_bits(result.ticks[16].event_probability) == float_bits(probability)


def test_closed_geometry_boundary_projection_and_radio_contact() -> None:
    assert legal_point((100.0, 0.0))
    assert not legal_point((99.999999, 0.0))
    assert project_legal((0.0, 0.0)) == (-100.0, 0.0)
    assert legal_linear_tick((100.0, 0.0), (0.0, 10.0))
    assert not legal_linear_tick((100.0, 0.0), (-1e-5, 0.0))
    # Open-segment boundary contact with the undilated prism is radio-blocked.
    assert not line_of_sight((-100.0, 80.0, 80.0), (100.0, 80.0, 80.0))
    # Contact only at the segment endpoint is excluded by the open-segment rule.
    assert line_of_sight((-100.0, 80.0, 80.0), (-80.0, 80.0, 80.0))


def test_route_manifest_order_templates_and_independent_specs() -> None:
    assert encounter_order(0, 0) == (RouteClass.SHORT, RouteClass.LONG)
    assert encounter_order(0, 1) == (RouteClass.LONG, RouteClass.SHORT)
    assert [template_index(0, block) for block in range(4)] == [0, 3, 2, 1]
    short, long = block_specs(4, 0)
    assert (short.route_class, long.route_class) == (RouteClass.SHORT, RouteClass.LONG)
    assert (short.direction, short.lateral_offset) == (1, 8)
    assert short is not long


def test_tick_boundaries_event_law_and_last_tick_are_exact() -> None:
    spec = EncounterSpec(RouteClass.SHORT, 1, 8)
    tape = FixtureTape.constant(spec, uniform=0.0)
    result = Headland90Host().run(spec, tape, ControllerSpec.constant(Fraction(7, 8)))
    assert len(result.ticks) == 48
    assert result.ticks[0].action == "BOOT"
    assert [result.ticks[index].blackout_active for index in range(5)] == [True] * 4 + [False]
    assert not result.ticks[15].legal_opportunity
    assert result.ticks[16].legal_opportunity
    assert result.ticks[16].action == "JOINT-UPDATE"
    assert result.ticks[16].event_probability == pytest.approx(
        1.0 - (1.0 - 7.0 / 8.0) ** (1.0 / 16.0), rel=0.0, abs=2e-16
    )
    assert [result.ticks[index].blackout_active for index in range(16, 21)] == [True] * 4 + [False]
    assert not result.ticks[31].legal_opportunity
    assert result.ticks[32].legal_opportunity

    never = Headland90Host().run(spec, tape, ControllerSpec.constant(0))
    terminal = never.ticks[-1]
    assert terminal.time == 7.75
    assert terminal.legal_opportunity
    assert terminal.action_uniform_consumed
    assert terminal.action == "KEEP"


def test_first_wind_and_shadow_transition_consumes_index_one_innovation() -> None:
    spec = EncounterSpec(RouteClass.SHORT, 1, 8)
    states, ticks = spec.total_ticks + 1, spec.total_ticks
    wind_t = [(0.0, 0.0)] * states
    wind_r = [(0.0, 0.0)] * states
    shadow_tr = [0.0] * states
    shadow_rb = [0.0] * states
    wind_t[0], wind_t[1] = (0.25, -0.5), (1.0, 0.5)
    wind_r[0], wind_r[1] = (-0.5, 0.25), (0.25, -1.0)
    shadow_tr[0], shadow_tr[1] = 0.2, -0.4
    shadow_rb[0], shadow_rb[1] = -0.3, 0.7
    tape = FixtureTape.from_sequences(
        spec,
        target_lateral=[0.0] * states,
        wind_t=wind_t,
        wind_r=wind_r,
        sensor=[(0.0, 0.0)] * states,
        shadow_tr=shadow_tr,
        shadow_rb=shadow_rb,
        link_tr=[0.5] * ticks,
        link_rb=[0.5] * ticks,
        action=[0.5] * ticks,
    )
    result = Headland90Host().run(spec, tape, ControllerSpec.constant(0))
    assert result.ticks[0].wind_tracker == (0.5, -1.0)
    assert result.ticks[0].wind_relay == (-1.0, 0.5)
    wind_scale = 2.0 * math.sqrt(1.0 - 0.90**2)
    expected_t = (0.90 * 0.5 + wind_scale * 1.0, 0.90 * -1.0 + wind_scale * 0.5)
    expected_r = (0.90 * -1.0 + wind_scale * 0.25, 0.90 * 0.5 + wind_scale * -1.0)
    assert result.ticks[1].wind_tracker == expected_t
    assert result.ticks[1].wind_relay == expected_r
    wrong_t_from_index_zero = (
        0.90 * 0.5 + wind_scale * 0.25,
        0.90 * -1.0 + wind_scale * -0.5,
    )
    assert result.ticks[1].wind_tracker != wrong_t_from_index_zero
    shadow_scale = 3.0 * math.sqrt(1.0 - 0.95**2)
    assert result.ticks[1].shadow_tr == 0.95 * result.ticks[0].shadow_tr + shadow_scale * -0.4
    assert result.ticks[1].shadow_rb == 0.95 * result.ticks[0].shadow_rb + shadow_scale * 0.7
    assert result.ticks[1].shadow_tr != 0.95 * result.ticks[0].shadow_tr + shadow_scale * 0.2


def test_alias_tag_does_not_enter_dynamics() -> None:
    spec = EncounterSpec(RouteClass.LONG, -1, -8)
    tape = _fixture(spec)
    controller = ControllerSpec.lookup(3, 3)
    first = Headland90Host().run(spec, tape, controller, logical_tag="GLOBAL-BEST")
    second = Headland90Host().run(spec, tape, controller, logical_tag="C_S<-L")
    assert first.ticks == second.ticks
    assert first.service_fraction == second.service_fraction


def test_python_cpp_complete_batch_conformance() -> None:
    fixtures = []
    controllers = (
        ControllerSpec(
            alpha_short=5, alpha_long=3,
            beta_short=1, beta_long=-1,
            gamma_short=0, gamma_long=0,
        ),
        ControllerSpec.explicit_rates([Fraction(index % 8, 8) for index in range(128)]),
    )
    for index, (route_class, direction, lateral) in enumerate(
        (
            (RouteClass.SHORT, 1, 8),
            (RouteClass.SHORT, -1, -8),
            (RouteClass.LONG, 1, -8),
            (RouteClass.LONG, -1, 8),
        )
    ):
        spec = EncounterSpec(route_class, direction, lateral)
        controller = controllers[0]
        if route_class is RouteClass.LONG and index == 3:
            controller = controllers[1]
        fixtures.append((spec, _fixture(spec, shift=index * 0.01), controller, f"alias-{index}"))
    python_results = tuple(
        Headland90Host().run(spec, tape, controller, logical_tag=tag)
        for spec, tape, controller, tag in fixtures
    )
    native_results = run_native_batch(fixtures)
    for python_result, native_result in zip(python_results, native_results):
        _assert_results_same(python_result, native_result)


def test_fixture_namespace_is_the_only_executable_namespace() -> None:
    production = EncounterSpec(
        RouteClass.SHORT, 1, 8, namespace=PRODUCTION_NAMESPACE
    )
    with pytest.raises(PermissionError, match="conformance namespace"):
        FixtureTape.constant(production)
    assert EncounterSpec(RouteClass.SHORT, 1, 8).namespace == FIXTURE_NAMESPACE
