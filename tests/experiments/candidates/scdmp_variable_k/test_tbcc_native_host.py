from __future__ import annotations

import ctypes
import math
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import (
    NativeBackendError,
    NativeBatch,
    RenewalLane,
    ResetLane,
    constant_disturbance_lane,
    native_artifact_identity,
    public_first_renewal_observation,
    require_cpp_batched_backend,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import native_backend as nb
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.config import (
    FIXTURE_MAGIC,
    FORMATION_ROTATE,
    FUNCTIONAL_BATCH_WIDTHS,
    HOOK_HANDOFF,
    MAX_BATCH_WIDTH,
    NATIVE_ABI_VERSION,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.oracle import (
    TEST_ONLY_ORACLE,
    TestOnlyState as _TestOnlyState,
    test_only_compose_setup as _oracle_compose_setup,
    test_only_output as _oracle_output,
    test_only_public_first_renewal as _oracle_public_first_renewal,
    test_only_primitive as _oracle_primitive,
    test_only_renewal as _oracle_renewal,
    test_only_reset as _oracle_reset,
)


HR = (HOOK_HANDOFF, FORMATION_ROTATE)
RH = (FORMATION_ROTATE, HOOK_HANDOFF)


def reset(
    events: tuple[int, int] = HR,
    *,
    k: int = 7,
    k_after: int | None = None,
    switch_tick: int | None = None,
    active: bool = True,
) -> ResetLane:
    return ResetLane(
        middle_events=events,
        k_initial=k,
        k_after=k_after,
        switch_tick=switch_tick,
        initial_v=0.017,
        initial_y=-0.004,
        initial_phi=0.006,
        active=active,
    )


def row(action: int = 0, *, active: bool = True, sign: int = 1) -> RenewalLane:
    return constant_disturbance_lane(
        action,
        eta_v=sign * 0.003,
        eta_y=-sign * 0.002,
        eta_omega=sign * 0.004,
        active=active,
    )


def assert_outputs_equal(native, oracle) -> None:
    for name in (
        "advanced",
        "active",
        "terminal",
        "ticks_advanced",
        "tick",
        "hold_k",
        "next_k",
        "safe_dock",
        "timeout",
        "cable_overload",
        "gantry_contact",
        "attitude_loss",
        "formation_loss",
        "energy_ticks",
        "dock_tick",
        "last_hold_reward_count",
    ):
        assert getattr(native, name) == getattr(oracle, name), name
    assert native.observation == pytest.approx(oracle.observation, rel=0.0, abs=2e-14)
    assert native.cumulative_reward == pytest.approx(oracle.cumulative_reward, rel=0.0, abs=2e-14)
    assert native.cumulative_energy == pytest.approx(oracle.cumulative_energy, rel=0.0, abs=2e-14)
    assert native.last_hold_rewards == pytest.approx(oracle.last_hold_rewards, rel=0.0, abs=2e-14)
    assert native.last_hold_reward_count == native.ticks_advanced
    assert native.last_hold_rewards[native.last_hold_reward_count :] == (0.0,) * (
        13 - native.last_hold_reward_count
    )


def test_artifact_identity_abi_sizes_warm_cache_and_no_fallback() -> None:
    first = require_cpp_batched_backend()
    second = require_cpp_batched_backend()
    assert first is second
    identity = native_artifact_identity()
    assert identity["component"] == "scdmp.tbcc_order_value.r02.full_host"
    assert identity["host"] == "QUAD-UAV-PALLET-GANTRY-24P5M-v1"
    assert identity["abi_version"] == NATIVE_ABI_VERSION
    assert identity["fixture_magic"] == FIXTURE_MAGIC
    assert identity["max_batch_width"] == MAX_BATCH_WIDTH
    assert identity["functional_batch_widths"] == list(FUNCTIONAL_BATCH_WIDTHS)
    assert identity["full_reset_step_cpp"] is True
    assert identity["python_environment_state"] is False
    assert identity["python_plant_transition"] is False
    assert identity["python_fallback"] is False
    artifact = Path(identity["artifact_path"])
    assert artifact.is_file() and artifact.stat().st_size == identity["artifact_size"]
    assert len(identity["artifact_sha256"]) == len(identity["build_key"]) == 64
    assert identity["runtime_abi"]["struct_sizes"] == {
        "reset_input": 64,
        "renewal_input": 320,
        "host_output": 336,
        "setup_fixture_input": 24,
        "setup_fixture_output": 24,
        "primitive_fixture_input": 160,
    }
    with pytest.raises(ValueError, match="one fixed candidate build root"):
        require_cpp_batched_backend(build_root="alternate")


def test_setup_composition_and_public_first_renewal_alias() -> None:
    native = nb.test_only_setup_composition((HR, RH))
    assert native == (((4, 2, 1, 3), 1), ((1, 4, 2, 3), 0))
    assert native == (_oracle_compose_setup(HR), _oracle_compose_setup(RH))
    hr = reset(HR)
    rh = reset(RH)
    assert public_first_renewal_observation(hr) == public_first_renewal_observation(rh)
    assert public_first_renewal_observation(hr) == _oracle_public_first_renewal(hr)
    assert public_first_renewal_observation(rh) == _oracle_public_first_renewal(rh)
    assert TEST_ONLY_ORACLE is True


@pytest.mark.parametrize("width", FUNCTIONAL_BATCH_WIDTHS)
def test_functional_widths_preserve_positions(width: int) -> None:
    resets = tuple(reset(HR if index % 2 == 0 else RH, k=7) for index in range(width))
    oracle_states = tuple(_oracle_reset(value) for value in resets)
    rows = tuple(row(sign=1 if index % 2 == 0 else -1) for index in range(width))
    with NativeBatch(resets) as batch:
        assert batch.width == width
        assert batch.active_lanes == tuple(range(width))
        outputs = batch.renew(rows)
        assert len(outputs) == width
        assert all(output.tick == 7 and output.ticks_advanced == 7 for output in outputs)
        assert all(output.active and not output.terminal for output in outputs)
        for native, oracle_state, materialized in zip(outputs, oracle_states, rows):
            oracle_state, advanced = _oracle_renewal(oracle_state, materialized)
            assert_outputs_equal(native, _oracle_output(oracle_state, advanced=advanced, hold_k=7))


@pytest.mark.parametrize("events", (HR, RH))
@pytest.mark.parametrize("k", (5, 7, 11, 13))
def test_oracle_native_complete_hold_equality(events: tuple[int, int], k: int) -> None:
    fixture = reset(events, k=k)
    oracle_state = _oracle_reset(fixture)
    with NativeBatch((fixture,)) as batch:
        assert_outputs_equal(batch.initial[0], _oracle_output(oracle_state, advanced=0, hold_k=0))
        for renewal in range(3):
            materialized = row(action=(renewal * 5) % 18, sign=1 if renewal % 2 == 0 else -1)
            oracle_state, advanced = _oracle_renewal(oracle_state, materialized)
            native = batch.renew((materialized,))[0]
            assert_outputs_equal(native, _oracle_output(oracle_state, advanced=advanced, hold_k=k))
            if native.terminal:
                break


@pytest.mark.parametrize(
    ("k_initial", "k_after", "switch_tick", "renewals"),
    ((7, 13, 91, 13), (13, 7, 91, 7), (7, 13, 273, 39), (13, 7, 273, 21)),
)
def test_fixed_position_switch_is_revealed_only_at_renewal(
    k_initial: int, k_after: int, switch_tick: int, renewals: int
) -> None:
    fixture = reset(k=k_initial, k_after=k_after, switch_tick=switch_tick)
    with NativeBatch((fixture,)) as batch:
        output = batch.initial[0]
        for _ in range(renewals):
            output = batch.renew((row(),))[0]
            assert not output.terminal
        assert output.tick == switch_tick
        assert output.hold_k == k_initial
        assert output.next_k == k_after
        next_output = batch.renew((row(),))[0]
        assert next_output.hold_k == k_after


def test_absorbed_lane_remains_masked_without_position_shift_or_energy() -> None:
    resets = tuple(reset(HR if index == 0 else RH, k=13) for index in range(8))
    with NativeBatch(resets) as batch:
        first = batch.renew((row(action=12), *(row() for _ in range(7))))
        assert first[0].terminal and first[0].cable_overload
        assert first[0].ticks_advanced < first[1].ticks_advanced
        frozen = first[0]
        assert frozen.last_hold_reward_count == frozen.ticks_advanced
        assert frozen.last_hold_rewards[frozen.last_hold_reward_count :] == (0.0,) * (
            13 - frozen.last_hold_reward_count
        )
        second = batch.renew((row(active=False), *(row() for _ in range(7))))
        assert second[0] == frozen
        assert [value.tick for value in second[1:]] == [26] * 7
        assert batch.active_lanes == tuple(range(1, 8))
        with pytest.raises(NativeBackendError, match="status 15"):
            batch.renew(tuple(row() for _ in range(8)))


def test_failure_dominates_same_tick_docking_and_labels_are_nonexclusive() -> None:
    output = nb.test_only_primitive(
        q=1,
        tick=120,
        x=24.49,
        v=1.6,
        y=0.0,
        w=0.0,
        phi=0.40,
        omega=0.0,
        z=(0.30, 0.0, 0.0, 0.0),
        formation=0.0,
        prior_a=1,
        prior_r=(0, 0, 0, 0),
        action=9,
        eta_v=0.003,
        eta_y=0.002,
        eta_omega=0.004,
    )
    assert output.tick == 121
    assert output.terminal
    assert output.cable_overload
    assert output.attitude_loss
    assert not output.safe_dock
    assert output.dock_tick is None
    assert output.energy_ticks == 1
    assert output.last_hold_reward_count == 1
    assert output.last_hold_rewards[1:] == (0.0,) * 12


def test_test_only_primitive_reward_is_independently_equal() -> None:
    state = _TestOnlyState(
        x=3.0,
        v=0.5,
        y=0.02,
        w=-0.01,
        phi=0.03,
        omega=-0.02,
        z=(0.01, 0.02, 0.03, 0.04),
        formation=0.02,
        prior_a=1,
        prior_r=(0, 0, 0, 0),
        p=(4, 2, 1, 3),
        q=1,
        tick=40,
        current_k=7,
        k_after=7,
        switch_tick=0,
        switched=False,
    )
    oracle = _oracle_primitive(state, 10, -0.003, 0.002, -0.004)
    native = nb.test_only_primitive(
        q=1,
        tick=40,
        x=3.0,
        v=0.5,
        y=0.02,
        w=-0.01,
        phi=0.03,
        omega=-0.02,
        z=(0.01, 0.02, 0.03, 0.04),
        formation=0.02,
        prior_a=1,
        prior_r=(0, 0, 0, 0),
        action=10,
        eta_v=-0.003,
        eta_y=0.002,
        eta_omega=-0.004,
    )
    assert native.last_hold_reward_count == native.ticks_advanced == 1
    assert native.last_hold_rewards[0] == pytest.approx(
        oracle.last_primitive_reward, rel=0.0, abs=2e-14
    )
    assert native.last_hold_rewards[1:] == (0.0,) * 12
    assert native.cumulative_reward == pytest.approx(oracle.cumulative_reward, rel=0.0, abs=2e-14)


def test_timeout_is_not_a_physical_failure() -> None:
    output = nb.test_only_primitive(
        q=0,
        tick=363,
        x=0.0,
        v=0.0,
        y=0.0,
        w=0.0,
        phi=0.0,
        omega=0.0,
        z=(0.0, 0.0, 0.0, 0.0),
        formation=0.0,
        prior_a=1,
        prior_r=(0, 0, 0, 0),
        action=0,
        eta_v=0.003,
        eta_y=0.002,
        eta_omega=0.004,
    )
    assert output.terminal and output.timeout and not output.safe_dock
    assert not any(
        (output.cable_overload, output.gantry_contact, output.attitude_loss, output.formation_loss)
    )
    assert output.completion_value == 0.0
    assert output.completion_time_seconds == 36.4


def test_full_batch_validation_rejects_illegal_and_nonfinite_without_mutation() -> None:
    with NativeBatch((reset(), reset(RH))) as batch:
        before = batch.initial
        with pytest.raises(ValueError, match="action"):
            batch.renew((row(), RenewalLane(18, (0.003,) * 13, (0.002,) * 13, (0.004,) * 13)))
        assert batch._last == before
        bad = RenewalLane(0, (math.nan,) + (0.003,) * 12, (0.002,) * 13, (0.004,) * 13)
        with pytest.raises(ValueError, match="eta_v"):
            batch.renew((row(), bad))
        assert batch._last == before
        valid = batch.renew((row(), row()))
        assert [value.tick for value in valid] == [7, 7]


def test_duplicate_cross_session_and_lane_order_are_rejected_premutation() -> None:
    a = NativeBatch((reset(), reset(RH)))
    b = NativeBatch((reset(), reset(RH)))
    try:
        inputs = (nb._RenewalInput * 2)(nb._renewal_input(row()), nb._renewal_input(row()))
        outputs = (nb._HostOutput * 2)()
        duplicate = (ctypes.c_uint64 * 2)(a._handles[0], a._handles[0])
        assert a._library.tbcc_r02_renew_batch(duplicate, inputs, 2, outputs) == 11
        crossed = (ctypes.c_uint64 * 2)(a._handles[0], b._handles[1])
        assert a._library.tbcc_r02_renew_batch(crossed, inputs, 2, outputs) == 12
        reversed_handles = (ctypes.c_uint64 * 2)(a._handles[1], a._handles[0])
        assert a._library.tbcc_r02_renew_batch(reversed_handles, inputs, 2, outputs) == 13
        assert [value.tick for value in a.renew((row(), row()))] == [7, 7]
        assert [value.tick for value in b.renew((row(), row()))] == [7, 7]
    finally:
        a.close()
        b.close()


def test_post_close_use_and_raw_malformed_width_are_rejected() -> None:
    batch = NativeBatch((reset(),))
    handles = batch._handles
    library = batch._library
    batch.close()
    with pytest.raises(NativeBackendError, match="closed"):
        batch.renew((row(),))
    inputs = (nb._RenewalInput * 1)(nb._renewal_input(row()))
    outputs = (nb._HostOutput * 1)()
    assert library.tbcc_r02_renew_batch(handles, inputs, 1, outputs) == 10
    assert library.tbcc_r02_renew_batch(handles, inputs, 0, outputs) == 1


def test_reset_validation_rejects_illegal_event_schedule_nonfinite_and_width() -> None:
    with pytest.raises(ValueError, match="H/R"):
        NativeBatch((ResetLane((HOOK_HANDOFF, HOOK_HANDOFF), 7, 0.0, 0.0, 0.0),))
    with pytest.raises(ValueError, match="7->13 or 13->7"):
        NativeBatch((reset(k=5, k_after=11, switch_tick=91),))
    with pytest.raises(ValueError, match="finite"):
        NativeBatch((ResetLane(HR, 7, math.nan, 0.0, 0.0),))
    with pytest.raises(ValueError, match="width"):
        NativeBatch(())
    with pytest.raises(ValueError, match="width"):
        NativeBatch(tuple(reset() for _ in range(MAX_BATCH_WIDTH + 1)))


def test_native_reset_failure_is_atomic_across_batch() -> None:
    library = require_cpp_batched_backend()
    valid = nb._reset_input(reset())
    invalid = nb._reset_input(reset(RH))
    invalid.initial_v = math.nan
    inputs = (nb._ResetInput * 2)(valid, invalid)
    handles = (ctypes.c_uint64 * 2)()
    outputs = (nb._HostOutput * 2)()
    assert library.tbcc_r02_reset_batch(inputs, 2, handles, outputs) == 3
    assert tuple(handles) == (0, 0)


def test_abi_v1_reset_and_malformed_output_size_are_rejected() -> None:
    library = require_cpp_batched_backend()
    stale = nb._reset_input(reset())
    stale.abi_version = 1
    handles = (ctypes.c_uint64 * 1)()
    outputs = (nb._HostOutput * 1)()
    assert library.tbcc_r02_reset_batch((nb._ResetInput * 1)(stale), 1, handles, outputs) == 3
    assert handles[0] == 0
    assert library.tbcc_r02_abi_version() == 2
    assert library.tbcc_r02_sizeof_host_output() == ctypes.sizeof(nb._HostOutput) == 336


def test_endpoint_accounting_matches_oracle_through_absorption() -> None:
    fixture = reset(HR, k=5)
    oracle_state: _TestOnlyState = _oracle_reset(fixture)
    with NativeBatch((fixture,)) as batch:
        native = batch.initial[0]
        while not native.terminal:
            materialized = row(action=0, sign=1 if (native.tick // 5) % 2 == 0 else -1)
            held_k = oracle_state.current_k
            oracle_state, advanced = _oracle_renewal(oracle_state, materialized)
            native = batch.renew((materialized,))[0]
            assert_outputs_equal(
                native,
                _oracle_output(oracle_state, advanced=advanced, hold_k=held_k),
            )
        assert native.energy_ticks == native.tick
        assert native.last_hold_reward_count == native.ticks_advanced
        assert native.terminal
        assert 0 < native.last_hold_reward_count < fixture.k_initial
        assert sum(native.last_hold_rewards[: native.last_hold_reward_count]) == pytest.approx(
            native.cumulative_reward
            - (oracle_state.cumulative_reward - sum(oracle_state.last_hold_rewards)),
            rel=0.0,
            abs=2e-14,
        )
        energy = native.cumulative_energy
        masked = batch.renew((row(active=False),))[0]
        assert masked == native
        assert masked.cumulative_energy == energy
