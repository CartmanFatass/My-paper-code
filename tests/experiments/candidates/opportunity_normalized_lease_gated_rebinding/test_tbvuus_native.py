from __future__ import annotations

import ctypes
from dataclasses import fields
import math
from pathlib import Path

import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import (
    Arm,
    EncounterSpec,
    FixtureCase,
    FixtureTape,
    RouteClass,
    ROAD_TEMPLATES,
    native_abi_identity,
    native_artifact_identity,
    native_build_key,
    native_toolchain_identity,
    require_cpp_batched_backend,
    run_native_batch,
    run_reference_batch,
    source_sha256,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import native_backend


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
    )


def _same(left, right) -> None:
    if isinstance(left, float):
        if math.isnan(left) and math.isnan(right):
            return
        assert math.isclose(left, right, rel_tol=2e-14, abs_tol=2e-12)
    elif isinstance(left, tuple):
        assert len(left) == len(right)
        for one, two in zip(left, right):
            _same(one, two)
    else:
        assert left == right


def _same_result(reference, native) -> None:
    for field in fields(reference):
        if field.name == "ticks":
            continue
        _same(getattr(reference, field.name), getattr(native, field.name))
    assert len(reference.ticks) == len(native.ticks)
    for reference_tick, native_tick in zip(reference.ticks, native.ticks):
        for field in fields(reference_tick):
            try:
                _same(getattr(reference_tick, field.name), getattr(native_tick, field.name))
            except AssertionError as error:
                raise AssertionError(f"tick={reference_tick.tick} field={field.name}") from error


def _cases(count: int) -> tuple[FixtureCase, ...]:
    cases = []
    for index in range(count):
        route = RouteClass.LONG if count == 8 and index % 4 == 3 else RouteClass.SHORT
        spec = EncounterSpec(route, -1 if index % 2 else 1, -8 if (index // 2) % 2 else 8)
        cases.append(FixtureCase(spec, _fixture(spec, index * 0.002), Arm(index % 4), f"case-{count}-{index}"))
    return tuple(cases)


def test_fixture_boundary_has_no_action_word_or_production_namespace() -> None:
    spec = EncounterSpec(RouteClass.SHORT, 1, 8)
    tape = FixtureTape.constant(spec)
    assert not hasattr(tape, "action")
    assert "action" not in {name for name, _ in native_backend._Input._fields_}
    with pytest.raises(PermissionError, match="conformance fixtures only"):
        EncounterSpec(RouteClass.SHORT, 1, 8, namespace="ONLGR-TBVUUS-HEADLAND90-20260821-v1")
    source = Path(native_backend._SOURCE).read_text(encoding="utf-8")
    input_declaration = source.split("struct TBInput", 1)[1].split("};", 1)[0]
    assert "action" not in input_declaration.lower()
    assert "<random>" not in source and "rand(" not in source
    assert ROAD_TEMPLATES == (
        (RouteClass.SHORT, -1, -8),
        (RouteClass.SHORT, -1, 8),
        (RouteClass.SHORT, 1, -8),
        (RouteClass.SHORT, 1, 8),
        (RouteClass.LONG, -1, -8),
        (RouteClass.LONG, -1, 8),
        (RouteClass.LONG, 1, -8),
        (RouteClass.LONG, 1, 8),
    )


def test_source_toolchain_build_artifact_and_abi_are_bound() -> None:
    assert len(source_sha256()) == 64
    assert len(native_build_key()) == 64
    toolchain = native_toolchain_identity()
    assert toolchain["compile_flags"] == ["/nologo", "/std:c++17", "/O2", "/EHsc", "/LD", "/fp:strict"]
    abi = native_abi_identity()
    assert abi == {
        "abi_version": 1,
        "input_size": ctypes.sizeof(native_backend._Input),
        "tick_size": ctypes.sizeof(native_backend._Tick),
        "output_size": ctypes.sizeof(native_backend._Output),
    }
    artifact = native_artifact_identity()
    assert artifact["source_sha256"] == source_sha256()
    assert artifact["build_key"] == native_build_key()
    assert len(artifact["sha256"]) == 64


def test_same_process_source_change_selects_distinct_key_artifact_and_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolated_source = tmp_path / "tbvuus_backend.cpp"
    original_bytes = Path(native_backend._SOURCE).read_bytes()
    isolated_source.write_bytes(original_bytes)
    monkeypatch.setattr(native_backend, "_SOURCE", isolated_source)

    first_key = native_build_key()
    first_source = source_sha256()
    first_library = require_cpp_batched_backend()
    first_artifact = native_artifact_identity()
    assert require_cpp_batched_backend() is first_library

    mutation = f"\n// isolated hot-source mutation {tmp_path.as_posix()}\n".encode("utf-8")
    isolated_source.write_bytes(original_bytes + mutation)
    second_key = native_build_key()
    second_source = source_sha256()
    try:
        second_library = require_cpp_batched_backend()
    except OSError as exc:
        if getattr(exc, "winerror", None) == 4551:
            pytest.skip("Windows Application Control blocks the mutated test DLL")
        raise
    second_artifact = native_artifact_identity()

    assert second_key != first_key
    assert second_source != first_source
    assert second_library is not first_library
    assert second_artifact["path"] != first_artifact["path"]
    assert second_artifact["sha256"] != first_artifact["sha256"]
    assert second_artifact["build_key"] == second_key
    assert second_artifact["source_sha256"] == second_source
    assert require_cpp_batched_backend() is second_library
    assert isolated_source.read_bytes() == original_bytes + mutation


def test_abi_size_and_malformed_input_fail_closed() -> None:
    library = require_cpp_batched_backend()
    inputs = (native_backend._Input * 1)()
    outputs = (native_backend._Output * 1)()
    assert library.tbvuus_run_batch(inputs, 1, ctypes.sizeof(native_backend._Input) - 1, outputs, ctypes.sizeof(native_backend._Output)) == 2
    inputs[0].route_class = 7
    assert library.tbvuus_run_batch(inputs, 1, ctypes.sizeof(native_backend._Input), outputs, ctypes.sizeof(native_backend._Output)) == 1001
    with pytest.raises(ValueError, match="non-finite"):
        FixtureTape.from_sequences(
            EncounterSpec(RouteClass.SHORT, 1, 8),
            target_lateral=[math.nan] * 49,
            wind_t=[(0.0, 0.0)] * 49,
            wind_r=[(0.0, 0.0)] * 49,
            sensor=[(0.0, 0.0)] * 49,
            shadow_tr=[0.0] * 49,
            shadow_rb=[0.0] * 49,
            link_tr=[0.5] * 48,
            link_rb=[0.5] * 48,
        )


def test_cross_route_tape_shape_mismatch_is_rejected_before_native_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    short_spec = EncounterSpec(RouteClass.SHORT, 1, 8)
    long_spec = EncounterSpec(RouteClass.LONG, 1, 8)
    short_tape = FixtureTape.constant(short_spec)
    long_tape = FixtureTape.constant(long_spec)
    native_calls = 0

    def forbidden_native_call():
        nonlocal native_calls
        native_calls += 1
        raise AssertionError("shape mismatch reached native loading")

    monkeypatch.setattr(native_backend, "require_cpp_batched_backend", forbidden_native_call)
    with pytest.raises(ValueError, match="LONG expected state count 145"):
        FixtureCase(long_spec, short_tape, Arm.NEVER_UPDATE)
    with pytest.raises(ValueError, match="SHORT expected state count 49"):
        FixtureCase(short_spec, long_tape, Arm.NEVER_UPDATE)
    assert native_calls == 0

    # Defense in depth: even an internal caller that bypasses the frozen
    # dataclass constructor cannot reach ctypes packing or the DLL.
    bypassed = FixtureCase(short_spec, short_tape, Arm.NEVER_UPDATE)
    object.__setattr__(bypassed, "spec", long_spec)
    with pytest.raises(ValueError, match="LONG expected state count 145"):
        run_native_batch((bypassed,))
    assert native_calls == 0


@pytest.mark.parametrize("count", (1, 8, 32))
def test_batched_python_cpp_reset_to_terminal_conformance(count: int) -> None:
    cases = _cases(count)
    reference = run_reference_batch(cases)
    native = run_native_batch(cases)
    for expected, observed in zip(reference, native):
        _same_result(expected, observed)


def test_four_arm_t0_shell_payload_waypoint_and_later_keep_law() -> None:
    spec = EncounterSpec(RouteClass.SHORT, 1, 8)
    tape = _fixture(spec)
    cases = tuple(FixtureCase(spec, tape, arm, arm.name) for arm in Arm)
    results = run_native_batch(cases)
    never, sham, raw, road = results
    assert [result.scheduled_t0_decisions for result in results] == [1, 1, 1, 1]
    assert [result.action_shells for result in results] == [0, 1, 1, 1]
    assert [result.ticks[16].action for result in results] == ["KEEP", "OVERHEAD-SHAM", "RAW-PATCH", "ROAD-PATCH"]
    for result in results:
        decision = result.ticks[16]
        assert decision.time == 0.0
        assert decision.sensor_visible
        assert decision.fit_t2 == 0.0
        assert decision.fit_z2 == decision.sensor_observation
        assert decision.buffer_count_pre == 2
        assert all(tick.action == "KEEP" for tick in result.ticks[17:])
        assert sum(tick.scheduled_t0_decision for tick in result.ticks) == 1
    assert sham.ticks[16].estimator_position == sham.ticks[16].estimator_position_pre
    assert sham.ticks[16].estimator_velocity == sham.ticks[16].estimator_velocity_pre
    assert raw.ticks[16].estimator_position == raw.ticks[16].fit_z2
    assert road.ticks[16].estimator_position == road.ticks[16].patch_position
    assert road.ticks[16].estimator_velocity == road.ticks[16].patch_velocity
    for index in range(len(never.ticks)):
        expected_waypoints = (never.ticks[index].tracker_waypoint, never.ticks[index].relay_waypoint)
        for result in (sham, raw, road):
            assert (result.ticks[index].tracker_waypoint, result.ticks[index].relay_waypoint) == expected_waypoints
    assert never.ticks[16].tracker_energy_after - sham.ticks[16].tracker_energy_after == 200.0
    assert [sham.ticks[index].blackout_active for index in range(16, 21)] == [True, True, True, True, False]
    assert [sham.ticks[index].lockout_active for index in (15, 16, 31, 32)] == [True, True, True, False]
    for index in range(len(never.ticks)):
        assert sham.ticks[index].service <= never.ticks[index].service
        if index >= 20:
            assert sham.ticks[index].service == never.ticks[index].service


def test_public_registry_order_and_exact_tie_precedence() -> None:
    from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03.oracle import _road_fit, route_at_time

    base1_minus, _, _ = route_at_time(RouteClass.SHORT, -1, -8, -0.25)
    base1_plus, _, _ = route_at_time(RouteClass.SHORT, -1, 8, -0.25)
    base2_minus, _, _ = route_at_time(RouteClass.SHORT, -1, -8, 0.0)
    base2_plus, _, _ = route_at_time(RouteClass.SHORT, -1, 8, 0.0)
    midpoint1 = ((base1_minus[0] + base1_plus[0]) / 2.0, (base1_minus[1] + base1_plus[1]) / 2.0)
    midpoint2 = ((base2_minus[0] + base2_plus[0]) / 2.0, (base2_minus[1] + base2_plus[1]) / 2.0)
    available, selected, residuals, *_ = _road_fit([(-0.25, midpoint1), (0.0, midpoint2)], (0.0, 0.0), (0.0, 0.0))
    assert available
    assert residuals[0] == residuals[1]
    assert selected == 0  # SHORT, then d=-1, then ell=-8.

    fallback = _road_fit([], (3.0, 4.0), (5.0, 6.0))
    assert fallback[0] is False
    assert fallback[5] == (3.0, 4.0)
    assert fallback[6] == (5.0, 6.0)
    assert fallback[7] is False


def test_input_order_and_grouped_four_arm_batches_are_equivalent() -> None:
    interleaved = _cases(32)
    grouped = tuple(sorted(interleaved, key=lambda case: (int(case.arm), case.logical_tag)))
    interleaved_results = {result.logical_tag: result for result in run_native_batch(interleaved)}
    grouped_results = {result.logical_tag: result for result in run_native_batch(grouped)}
    assert interleaved_results.keys() == grouped_results.keys()
    for tag in interleaved_results:
        _same_result(interleaved_results[tag], grouped_results[tag])
