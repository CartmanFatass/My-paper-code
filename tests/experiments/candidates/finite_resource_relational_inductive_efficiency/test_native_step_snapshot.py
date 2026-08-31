from __future__ import annotations

import ctypes
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.native import native_abi as abi
from experiments.candidates.finite_resource_relational_inductive_efficiency import native_adapter


SOURCE = (
    Path(__file__).resolve().parents[4]
    / "experiments/candidates/finite_resource_relational_inductive_efficiency/native"
    / "frrie_ridgegate2z_external.cpp"
)


@pytest.fixture(scope="module")
def native():
    """Build at the package's create-only artifact seam, then clean it.

    The local wrapper tightens every build/discovery subprocess to at most 60
    seconds without changing the production adapter implementation.
    """

    artifact = native_adapter.package_native_artifact_path()
    if artifact.exists():
        pytest.fail("focused native test requires an absent create-only package artifact")
    if sys.platform == "win32":
        # Use the adapter's bounded MSVC discovery, but invoke the discovered
        # environment through the Windows shell directly.  This avoids
        # cmd.exe list-argument quote rewriting while preserving the adapter's
        # source, flags, staging names, and create-only publication rule.
        vcvars = native_adapter._windows_vcvars64()
        artifact.parent.mkdir(exist_ok=True)
        temporary = artifact.parent / f"{artifact.stem}.building-test-{os.getpid()}{artifact.suffix}"
        sidecars = tuple(temporary.with_suffix(suffix) for suffix in (".obj", ".pdb", ".lib", ".exp"))
        if temporary.exists() or any(path.exists() for path in sidecars):
            pytest.fail("focused native build staging path already exists")
        command = " ".join([
            f'call "{vcvars}" >nul && cl.exe',
            "/nologo", "/std:c++17", "/O2", "/EHsc", "/LD", "/fp:strict",
            f'/Fo:"{temporary.with_suffix(".obj")}"',
            f'/Fd:"{temporary.with_suffix(".pdb")}"',
            f'/Fe:"{temporary}"', f'"{SOURCE}"', "/link", "/NOIMPLIB",
        ])
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command, shell=True, cwd=artifact.parent, check=False,
                capture_output=True, text=True, timeout=60,
            )
            elapsed = time.perf_counter() - started
            if completed.returncode != 0:
                pytest.fail(f"bounded package MSVC build failed: {completed.stderr or completed.stdout}")
            if not temporary.is_file():
                pytest.fail("bounded package MSVC build produced no artifact")
            try:
                os.link(temporary, artifact)
            except FileExistsError:
                pytest.fail("package native artifact appeared during create-only publication")
        finally:
            for path in (temporary, *sidecars):
                path.unlink(missing_ok=True)
        library_path = artifact.resolve(strict=True)
        print(
            "FRRIE_NATIVE_BUILD "
            f"command={command!r} cwd={str(artifact.parent)!r} "
            f"elapsed_seconds={elapsed:.3f} artifact={str(library_path)!r}"
        )
    else:
        original_run = native_adapter.subprocess.run

        def bounded_run(*args, **kwargs):
            kwargs["timeout"] = min(kwargs.get("timeout", 60), 60)
            return original_run(*args, **kwargs)

        native_adapter.subprocess.run = bounded_run
        try:
            library_path = native_adapter.build_package_native_artifact()
        except Exception as exc:
            pytest.skip(f"no bounded local package-native build: {exc}")
        finally:
            native_adapter.subprocess.run = original_run

    library = ctypes.CDLL(str(library_path))
    abi.bind_native_abi(library, native_width=2)
    try:
        yield library
    finally:
        if sys.platform == "win32":
            import _ctypes

            handle = library._handle
            library._handle = 0
            _ctypes.FreeLibrary(handle)
        library_path.unlink(missing_ok=False)
        if library_path.exists():
            pytest.fail("focused native test left its package artifact behind")
        try:
            library_path.parent.rmdir()
        except OSError:
            pass


def _reset_input(roster: int = 6) -> abi.ResetInputV1:
    value = abi.ResetInputV1()
    value.abi_version = abi.ABI_VERSION
    value.state_version = abi.STATE_VERSION
    value.roster = roster
    for basin, times in enumerate(((0, 2, 4), (1, 3, 5))):
        for ordinal, time in enumerate(times):
            value.event_times[basin][ordinal] = time
    for slot in range(abi.HORIZON):
        for sender in range(abi.MAX_AGENTS):
            value.detection_uniforms[slot][sender] = 0.999
            value.base_uniforms[slot][sender] = 0.999
            for receiver in range(abi.MAX_AGENTS):
                value.uplink_uniforms[slot][sender][receiver] = 0.999
    return value


def _reset(native, value: abi.ResetInputV1 | None = None) -> abi.NativeStateV1:
    state = abi.NativeStateV1()
    reset = value or _reset_input()
    assert native.frrie_reset_batch_v1(ctypes.byref(state), ctypes.byref(reset), 1, 2) == abi.ERR_OK
    return state


def _actions(state: abi.NativeStateV1, overrides: dict[int, int] | None = None) -> abi.StepInputV1:
    value = abi.StepInputV1()
    value.abi_version = abi.ABI_VERSION
    for agent in range(state.roster):
        value.actions[agent] = abi.ACTION_HOLD
    for agent, action in (overrides or {}).items():
        value.actions[agent] = action
    return value


def _step(native, state, overrides=None) -> abi.StepOutputV1:
    action = _actions(state, overrides)
    output = abi.StepOutputV1()
    assert native.frrie_step_batch_v1(
        ctypes.byref(state), ctypes.byref(action), ctypes.byref(output), 1, 2
    ) == abi.ERR_OK
    return output


def _observe(native, state) -> abi.ObservationOutputV1:
    output = abi.ObservationOutputV1()
    assert native.frrie_observe_batch_v1(ctypes.byref(state), ctypes.byref(output), 1, 2) == abi.ERR_OK
    return output


def test_packed_abi_layout_and_source_contract_are_frozen():
    assert abi.ABI_VERSION == 2
    assert abi.NATIVE_STEP_ABI == "FRRIE_NATIVE_STEP_ABI_V2_FP32"
    assert abi.STATE_VERSION == 1
    assert abi.STATE_SIZE == ctypes.sizeof(abi.NativeStateV1) == 24_321
    assert ctypes.sizeof(abi.ReportV1) == 8
    assert ctypes.sizeof(abi.PendingUplinkV1) == 13
    assert ctypes.sizeof(abi.PendingBaseV1) == 12
    assert ctypes.sizeof(abi.MetricsV1) == 44
    assert abi.REGISTERED_ROSTERS == (6, 9, 15, 21)
    assert abi.LEGAL_MASKS == (
        (1, 1, 0, 0, 0, 1),
        (1, 1, 0, 0, 0, 1),
        (0, 0, 1, 1, 1, 1),
    )

    source = SOURCE.read_text(encoding="utf-8")
    for symbol in abi.ABI_SYMBOLS:
        assert symbol in source
    assert "#pragma pack(push, 1)" in source
    assert "std::memmove(snapshot_bytes, states, byte_count)" in source
    assert "std::memmove(states, snapshot_bytes, byte_count)" in source
    lowered = source.lower()
    for forbidden in ("actioncodec", "torch", "cuda", "socket", "sha256", "checkpoint_id"):
        assert forbidden not in lowered


def test_initial_observation_is_exact_and_roles_masks_are_stable(native):
    state = _reset(native)
    observation = _observe(native, state)
    assert native.frrie_native_abi_v1() == abi.ABI_VERSION
    assert native.frrie_native_state_size_v1() == abi.STATE_SIZE
    assert observation.roster == 6 and observation.slot == 0 and observation.terminal == 0
    assert list(observation.roles[:6]) == [0, 0, 1, 1, 2, 2]
    assert list(observation.legal_masks[0]) == list(abi.LEGAL_MASKS[0])
    assert list(observation.legal_masks[4]) == list(abi.LEGAL_MASKS[2])
    west = list(observation.observations[0])
    assert west[:4] == [1.0, 0.0, 0.0, 0.0]
    assert west[4:7] == pytest.approx([2 / 7, 2 / 7, 2 / 7])
    assert west[7:] == [0.0] * 15


def test_scan_radio_arrival_ack_order_and_endpoint_primitives(native):
    tape = _reset_input()
    tape.detection_uniforms[0][1] = 0.0
    tape.uplink_uniforms[1][1][4] = 0.0
    tape.base_uniforms[2][4] = 0.0
    state = _reset(native, tape)

    first = _step(native, state, {0: abi.ACTION_UPLINK, 1: abi.ACTION_SCAN})
    observation = _observe(native, state)
    assert first.metrics.empty_actions == 1
    assert observation.observations[1][7] == 1.0
    assert observation.observations[1][8] == pytest.approx(1 / 3)

    _step(native, state, {1: abi.ACTION_UPLINK, 4: abi.ACTION_LISTEN_WEST})
    observation = _observe(native, state)
    assert state.fifo_sizes[1] == 0
    assert state.fifo_sizes[4] == 1
    assert state.fifos[4][0].event_time == 0
    assert observation.observations[4][8] == pytest.approx(2 / 3)
    assert observation.observations[1][21] == 1.0
    assert observation.observations[4][21] == 1.0

    output = _step(native, state, {4: abi.ACTION_FORWARD_BASE})
    assert output.metrics.dw == 1
    assert output.metrics.de == 0
    assert output.metrics.new_timely_deliveries == 1
    assert state.fifo_sizes[4] == 0
    assert output.previous_success[4] == 1
    expected = 0.65 / 6 + 0.10 * (1.0 - output.metrics.waste)
    assert output.metrics.terminal_audit == pytest.approx(expected, abs=1e-6)


def test_late_decode_acknowledges_but_expires_without_policy_success(native):
    tape = _reset_input()
    tape.detection_uniforms[0][0] = 0.0
    tape.uplink_uniforms[3][0][4] = 0.0
    state = _reset(native, tape)
    _step(native, state, {0: abi.ACTION_SCAN})
    _step(native, state)
    _step(native, state)
    output = _step(native, state, {0: abi.ACTION_UPLINK, 4: abi.ACTION_LISTEN_WEST})
    assert state.slot == 4
    assert state.fifo_sizes[0] == 0  # decoded link acknowledgement dequeues
    assert state.fifo_sizes[4] == 0  # expired arrival is not enqueued
    assert output.previous_success[0] == 0
    assert output.previous_success[4] == 0
    assert output.metrics.expired_arrivals == 1


def test_collision_is_complete_and_does_not_dequeue(native):
    tape = _reset_input()
    tape.detection_uniforms[0][0] = tape.detection_uniforms[0][1] = 0.0
    tape.uplink_uniforms[1][0][4] = tape.uplink_uniforms[1][1][4] = 0.0
    state = _reset(native, tape)
    _step(native, state, {0: abi.ACTION_SCAN, 1: abi.ACTION_SCAN})
    output = _step(
        native,
        state,
        {0: abi.ACTION_UPLINK, 1: abi.ACTION_UPLINK, 4: abi.ACTION_LISTEN_WEST},
    )
    assert list(state.fifo_sizes[:2]) == [1, 1]
    assert state.fifo_sizes[4] == 0
    assert output.metrics.collision_loss == 2
    assert output.metrics.radio_actions == 3
    assert output.metrics.waste_actions == 3


def test_snapshot_restore_is_direct_bit_exact_and_branches_are_isolated(native):
    tape = _reset_input()
    tape.detection_uniforms[0][0] = 0.0
    state = _reset(native, tape)
    _step(native, state, {0: abi.ACTION_SCAN})
    snapshot = (ctypes.c_uint8 * abi.STATE_SIZE)()
    assert native.frrie_snapshot_batch_v1(
        ctypes.byref(state), snapshot, abi.STATE_SIZE, 1, 2
    ) == abi.ERR_OK
    frozen = bytes(snapshot)

    branch = abi.NativeStateV1()
    assert native.frrie_restore_batch_v1(
        ctypes.byref(branch), snapshot, abi.STATE_SIZE, 1, 2
    ) == abi.ERR_OK
    assert bytes(branch) == frozen
    _step(native, branch)
    assert bytes(snapshot) == frozen
    assert bytes(state) == frozen

    _step(native, state, {0: abi.ACTION_UPLINK})
    assert bytes(state) != bytes(branch)
    assert native.frrie_restore_batch_v1(
        ctypes.byref(state), snapshot, abi.STATE_SIZE, 1, 2
    ) == abi.ERR_OK
    restored = (ctypes.c_uint8 * abi.STATE_SIZE)()
    assert native.frrie_snapshot_batch_v1(
        ctypes.byref(state), restored, abi.STATE_SIZE, 1, 2
    ) == abi.ERR_OK
    assert bytes(restored) == frozen


def test_slot_11_radio_cannot_succeed_or_schedule_arrival(native):
    state = _reset(native)
    for _ in range(11):
        _step(native, state)
    before_radio = state.metrics.radio_actions
    before_empty = state.metrics.empty_actions
    output = _step(native, state, {4: abi.ACTION_FORWARD_BASE})
    assert output.terminal == 1 and state.slot == abi.HORIZON
    assert state.pending_base_present == 0 and state.pending_uplink_count == 0
    assert output.metrics.dw == output.metrics.de == 0
    assert output.metrics.radio_actions == before_radio + 1
    assert output.metrics.empty_actions == before_empty + 1
    assert output.metrics.waste_actions == 1
    assert output.metrics.waste == 1.0
    assert output.metrics.terminal_audit == 0.0


def test_validation_is_distinct_and_batch_failures_are_atomic(native):
    ResetArray = abi.ResetInputV1 * 2
    StateArray = abi.NativeStateV1 * 2
    resets = ResetArray(_reset_input(), _reset_input())
    resets[1].event_times[0][1] = resets[1].event_times[0][0]
    states = StateArray()
    before = bytes(states)
    assert native.frrie_reset_batch_v1(states, resets, 2, 2) == abi.ERR_EVENT_TIMES
    assert bytes(states) == before

    state = _reset(native)
    invalid = _actions(state, {0: abi.ACTION_FORWARD_BASE})
    output = abi.StepOutputV1()
    before = bytes(state)
    assert native.frrie_step_batch_v1(
        ctypes.byref(state), ctypes.byref(invalid), ctypes.byref(output), 1, 2
    ) == abi.ERR_ACTION_ILLEGAL
    assert bytes(state) == before

    tape = _reset_input()
    tape.detection_uniforms[0][0] = math.nan
    untouched = abi.NativeStateV1()
    assert native.frrie_reset_batch_v1(
        ctypes.byref(untouched), ctypes.byref(tape), 1, 2
    ) == abi.ERR_UNIFORM_NONFINITE
    assert bytes(untouched) == b"\x00" * abi.STATE_SIZE
