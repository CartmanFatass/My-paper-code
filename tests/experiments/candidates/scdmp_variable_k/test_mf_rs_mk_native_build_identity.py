from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

import pytest

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    native_backend as backend,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_backend import (
    NativeBackendError,
    NativeSession,
    native_abi_identity,
    verify_native_transition,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_state import (
    DisturbanceHold,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.source_identity import (
    OWNED_PRODUCTION_PATHS,
    compute_source_identity,
)


def _hold() -> DisturbanceHold:
    return DisturbanceHold(
        eta_v=tuple(0.003 if index % 2 == 0 else -0.003 for index in range(13)),
        eta_y=tuple(-0.002 if index % 3 == 0 else 0.002 for index in range(13)),
        eta_omega=tuple(0.004 if index % 2 == 0 else -0.004 for index in range(13)),
    )


def _post(pre: bytes, action: int, *, active: bool = True) -> bytes:
    session = NativeSession.from_state_bytes((pre,))
    session.step((action,), (_hold(),), active=(active,))
    return session.state_bytes()[0]


def test_build_identity_binds_direct_source_compiler_flags_runtime_receipt_and_dll() -> None:
    identity = native_abi_identity()
    binding = identity["build_binding"]
    facts = binding["build_facts"]
    dll = Path(identity["compiled_library_resolved_path"])
    receipt = Path(identity["build_receipt_resolved_path"])

    assert dll.parent.name == binding["cache_key_sha256"]
    assert binding["dll"]["byte_size"] == dll.stat().st_size
    assert len(binding["dll"]["sha256"]) == 64
    assert len(facts["native_cpp_source"]["sha256"]) == 64
    assert len(facts["compiler"]["sha256"]) == 64
    assert facts["compiler"]["resolved_executable"].lower().endswith("cl.exe")
    assert facts["compiler"]["version"]["output_utf8"]
    assert facts["compile_flags"] == list(backend._COMPILE_FLAGS)
    assert facts["runtime_architecture"]["pointer_bits"] == 64
    encoded = receipt.read_bytes()
    assert encoded == backend._canonical_json(json.loads(encoded))


def test_old_size_mtime_or_receipt_tamper_is_rejected_fail_closed(tmp_path: Path) -> None:
    identity = native_abi_identity()
    binding = identity["build_binding"]
    facts = binding["build_facts"]
    original = Path(identity["compiled_library_resolved_path"]).parent
    copied = tmp_path / binding["cache_key_sha256"]
    shutil.copytree(original, copied)
    dll = copied / "mf_rs_native.dll"
    before = dll.stat()
    changed = bytearray(dll.read_bytes())
    changed[len(changed) // 2] ^= 1
    dll.write_bytes(changed)
    os.utime(dll, ns=(before.st_atime_ns, before.st_mtime_ns))

    assert dll.stat().st_size == before.st_size
    assert dll.stat().st_mtime_ns == before.st_mtime_ns
    with pytest.raises(NativeBackendError, match="receipt, cache key, or DLL bytes"):
        backend._read_build_receipt(copied, facts)

    shutil.copy2(original / "mf_rs_native.dll", dll)
    receipt = copied / backend._BUILD_RECEIPT_NAME
    value = json.loads(receipt.read_text(encoding="utf-8"))
    value["cache_key_sha256"] = "0" * 64
    receipt.write_bytes(backend._canonical_json(value))
    with pytest.raises(NativeBackendError, match="receipt, cache key, or DLL bytes"):
        backend._read_build_receipt(copied, facts)


def test_pure_transition_accepts_correct_and_rejects_same_tick_k_q_wrong_post() -> None:
    pre = NativeSession.reset(width=1, k=7, pre_event_q=1).state_bytes()[0]
    correct = _post(pre, 0)
    wrong_same_coordinates = _post(pre, 1)

    accepted = verify_native_transition(
        pre_state_bytes=pre,
        action=0,
        active=True,
        disturbance_hold=_hold(),
        expected_post_state_bytes=correct,
    )
    rejected = verify_native_transition(
        pre_state_bytes=pre,
        action=0,
        active=True,
        disturbance_hold=_hold(),
        expected_post_state_bytes=wrong_same_coordinates,
    )
    correct_state = backend._NativeState.from_buffer_copy(correct)
    wrong_state = backend._NativeState.from_buffer_copy(wrong_same_coordinates)

    assert accepted["matched"] is True and accepted["native_status"] == 0
    assert rejected["matched"] is False and rejected["native_status"] == 4
    assert correct_state.n == wrong_state.n
    assert correct_state.current_k == wrong_state.current_k
    assert correct_state.q == wrong_state.q
    assert accepted["pre_state_sha256"] == rejected["pre_state_sha256"]
    assert pre == NativeSession.reset(width=1, k=7, pre_event_q=1).state_bytes()[0]


def test_pure_transition_accepts_terminal_transition_and_does_not_advance_source() -> None:
    reset = NativeSession.reset(width=1, k=7, pre_event_q=0).state_bytes()[0]
    prepared = backend._NativeState.from_buffer_copy(reset)
    prepared.n = 363
    prepared.energy_ticks = 363
    prepared.cached.n = 363
    prepared.cached.energy_ticks = 363
    prepared.cached.observation[17] = 363.0 / 364.0
    pre = bytes(memoryview(prepared))
    # This also establishes that the handcrafted full POD is ABI-valid.
    NativeSession.from_state_bytes((pre,))
    expected = _post(pre, 0)

    receipt = verify_native_transition(
        pre_state_bytes=pre,
        action=0,
        active=True,
        disturbance_hold=_hold(),
        expected_post_state_bytes=expected,
    )

    assert receipt["matched"] is True
    assert receipt["measured_terminal"] is True
    assert receipt["measured_tick"] == 364
    assert receipt["measured_ticks_advanced"] == 1
    assert bytes(memoryview(prepared)) == pre


def test_transition_rejects_abi_tamper_before_any_measured_advance() -> None:
    pre = NativeSession.reset(width=1, k=13, pre_event_q=0).state_bytes()[0]
    expected = _post(pre, 0)
    tampered = backend._NativeState.from_buffer_copy(pre)
    tampered.abi_version = 2

    with pytest.raises(NativeBackendError, match="status 2"):
        verify_native_transition(
            pre_state_bytes=bytes(memoryview(tampered)),
            action=0,
            active=True,
            disturbance_hold=_hold(),
            expected_post_state_bytes=expected,
        )


def test_source_identity_inventory_and_diff_bind_resource_helpers_and_build_receipt() -> None:
    assert "scripts/hmasd_resource_preflight.py" in OWNED_PRODUCTION_PATHS
    assert "scripts/hmasd_platform.py" in OWNED_PRODUCTION_PATHS
    identity = compute_source_identity()
    inventory = {row["relative_path"]: row for row in identity["owned_source_inventory"]}

    assert inventory["scripts/hmasd_resource_preflight.py"]["sha256"]
    assert inventory["scripts/hmasd_platform.py"]["sha256"]
    assert identity["native_build_receipt"] == identity["native_abi_identity"]["build_binding"]
    assert "scripts/hmasd_resource_preflight.py" in identity["git_diff_command"]
    assert "scripts/hmasd_platform.py" in identity["git_diff_command"]
