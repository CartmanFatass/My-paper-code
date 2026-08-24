from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import math

import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.contracts import (
    Arm,
    ContractError,
    GateAFixture,
    TEST_NAMESPACE,
    fixture_family,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.native_backend import (
    artifact_identity,
    certificate_native,
    filter_step_native,
    generator_scan_native,
    protocol_apply_native,
    redact_observation_native,
    rng_word_native,
    run_native_batch,
    wire_sizes_native,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.oracle import (
    generator_first_qualifying,
    filter_step_oracle,
    rng_u64,
    run_oracle,
)


def _assert_result_equal(native, oracle) -> None:
    for field in (
        "service_ticks", "owner", "service_epoch", "next_payload_sequence",
        "handover_used", "noop_count", "transaction_shell_bytes", "invalid_commit", "token_gap",
        "dual_owner", "dual_payload", "buffer_clear", "separation_breach",
        "protocol_bytes", "terminal_tick", "state_digest",
    ):
        assert getattr(native, field) == getattr(oracle, field), field
    assert native.final_separation == pytest.approx(oracle.final_separation, rel=1e-11, abs=1e-10)
    assert native.total_energy == pytest.approx(oracle.total_energy, rel=1e-11, abs=1e-8)


def test_source_keyed_loader_and_closed_abi() -> None:
    identity = artifact_identity()
    assert identity["python_fallback"] is False
    assert identity["test_only"] is True
    assert identity["abi"]["version"] == 1
    assert identity["source_sha256"]
    assert identity["sha256"]


@pytest.mark.parametrize("address", [
    "GENERATOR/0/ASSAY",
    "GENERATOR/99999/ASSAY",
    "RADIO/17/G_TO_U0/0",
    "SOURCE/1199/PX/1",
    "DISH/RBHR/R05/UTF8-\u03bc",
])
def test_native_rng_matches_sha256_oracle(address: str) -> None:
    key = 0xD15A123456789ABC
    assert rng_word_native(key, address) == rng_u64(key, address)


@pytest.mark.parametrize("width", [1, 8, 32])
def test_native_host_matches_fixture_oracle(width: int) -> None:
    fixtures = fixture_family(width)
    native = run_native_batch(fixtures)
    oracle = tuple(run_oracle(value) for value in fixtures)
    assert len(native) == width
    for observed, expected in zip(native, oracle, strict=True):
        _assert_result_equal(observed, expected)


def test_literal_structured_in_flex_zero_is_exact() -> None:
    structured = fixture_family(8, arm=Arm.STRUCTURED)
    flex = tuple(replace(value, arm=Arm.FLEX_ZERO) for value in structured)
    structured_result = run_native_batch(structured)
    flex_result = run_native_batch(flex)
    assert structured_result == flex_result


def test_never_noop_is_live_and_has_no_transfer_authority() -> None:
    fixtures = fixture_family(8, arm=Arm.NEVER)
    results = run_native_batch(fixtures)
    for fixture, result in zip(fixtures, results, strict=True):
        assert result.owner == fixture.initial_owner
        assert result.handover_used == 0
        assert result.service_epoch == 0
        assert result.noop_count > 0
        assert result.invalid_commit == 0


def test_real_sham_clone_allowlist() -> None:
    base = fixture_family(8, arm=Arm.FORK_REAL)
    real = run_native_batch(base)
    sham = run_native_batch(tuple(replace(value, arm=Arm.FORK_SHAM) for value in base))
    for fixture, r, s in zip(base, real, sham, strict=True):
        assert r.owner == 1 - fixture.initial_owner
        assert s.owner == fixture.initial_owner
        assert r.service_epoch == s.service_epoch == 1
        assert r.handover_used == s.handover_used == 1
        assert r.invalid_commit == s.invalid_commit == 0
        assert r.token_gap == s.token_gap == 0
        assert r.dual_owner == s.dual_owner == 0
        assert r.dual_payload == s.dual_payload == 0
        assert r.buffer_clear == s.buffer_clear == 0
        assert r.transaction_shell_bytes == s.transaction_shell_bytes == 24
        assert r.noop_count == s.noop_count == 0


def test_generator_lowest_qualifying_and_chunk_order_invariant() -> None:
    key = 0xD15A0BADF00D1234
    for stratum in (0, 1, 2):
        expected = generator_first_qualifying(key, start=0, count=10000, stratum=stratum)
        assert expected is not None
        direct = generator_scan_native([(key, 0, 10000, stratum)])[0][0]
        assert direct == expected
        chunks = [(key, start, 64, stratum) for start in range(0, 10048, 64)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            unordered = list(pool.map(lambda request: generator_scan_native([request])[0][0], reversed(chunks)))
        winners = [value for value in unordered if value is not None]
        assert min(winners) == expected


def test_namespace_and_shape_fail_closed_before_native() -> None:
    base = fixture_family(1)[0]
    with pytest.raises(ContractError):
        GateAFixture(**{**base.__dict__, "namespace": "PRODUCTION/DISH"})
    with pytest.raises(ContractError):
        GateAFixture(**{**base.__dict__, "k_initial": 7})


def _protocol_row(**changes: int) -> dict[str, int]:
    row = {
        "integrity": 1, "request_transfer": 1, "origin_pass": 1, "handover_unused": 1,
        "application_tick": 101, "origin_tick": 100, "readiness_tick": 99,
        "bound_readiness_tick": 99, "snapshot_tick": 100,
        "current_owner": 0, "old_owner": 0, "new_owner": 1,
        "current_epoch": 4, "intent_epoch": 4,
        "current_next_sequence": 91, "intent_next_sequence": 91,
        "source0_sequence": 73, "source1_sequence": 73, "intent_source_sequence": 73,
        "current_k_epoch": 2, "intent_k_epoch": 2, "terminal": 0,
        "batteries_positive": 1, "buffers_present": 1,
        "separation_current": 1, "separation_next": 1, "slew_ok": 1,
        "sham": 0, "never_arm": 0,
    }
    row.update(changes)
    return row


def test_protocol_application_first_false_order_and_atomic_cas() -> None:
    success, sequence_failure, lineage_failure, terminal_failure = protocol_apply_native([
        _protocol_row(),
        _protocol_row(current_next_sequence=92),
        _protocol_row(source1_sequence=74),
        _protocol_row(terminal=1),
    ])
    assert success == {
        "success": 1, "reason_code": 0, "invalid_commit": 0, "noop_count": 0,
        "owner": 1, "service_epoch": 5, "next_sequence": 91, "handover_used": 1,
        "source_buffers_preserved": 1, "base_buffer_preserved": 1,
        "transaction_shell_bytes": 24, "forbidden_leak_count": 0,
    }
    assert sequence_failure["reason_code"] == 7 and sequence_failure["invalid_commit"] == 1
    assert lineage_failure["reason_code"] == 8 and lineage_failure["invalid_commit"] == 1
    assert terminal_failure["reason_code"] == 10 and terminal_failure["invalid_commit"] == 1
    for failure in (sequence_failure, lineage_failure, terminal_failure):
        assert failure["owner"] == 0
        assert failure["service_epoch"] == 4
        assert failure["source_buffers_preserved"] == failure["base_buffer_preserved"] == 1


def test_protocol_real_sham_and_never_authority_fences() -> None:
    real, sham, never = protocol_apply_native([
        _protocol_row(), _protocol_row(sham=1), _protocol_row(never_arm=1),
    ])
    assert real["owner"] == 1 and sham["owner"] == 0
    assert real["service_epoch"] == sham["service_epoch"] == 5
    assert real["transaction_shell_bytes"] == sham["transaction_shell_bytes"] == 24
    assert never["success"] == 0 and never["noop_count"] == 1
    assert never["invalid_commit"] == 0 and never["owner"] == 0 and never["service_epoch"] == 4


def test_native_observation_fence_ignores_forbidden_values() -> None:
    causal = [tuple(float(index) for index in range(54))]
    first = redact_observation_native(causal, [tuple(float(index) for index in range(8))])
    second = redact_observation_native(causal, [tuple(10_000.0 + index for index in range(8))])
    assert first == second == tuple(causal)


@pytest.mark.parametrize("camera_present", [False, True])
def test_native_camera_filter_matches_joseph_oracle(camera_present: bool) -> None:
    mean = (10.0, -4.0, 1.5, -0.5)
    covariance = tuple(float(value) for value in (
        20, 1, 2, 0, 1, 18, 0, 3, 2, 0, 5, 0.2, 0, 3, 0.2, 4,
    ))
    row = {"mean": mean, "covariance": covariance, "camera_present": int(camera_present), "z": (11.5, -3.5)}
    native = filter_step_native([row])[0]
    oracle_mean, oracle_covariance = filter_step_oracle(mean, covariance, camera_present=camera_present, z=row["z"])
    assert native["finite"] is True
    assert native["mean"] == pytest.approx(oracle_mean, rel=1e-12, abs=1e-12)
    assert native["covariance"] == pytest.approx(oracle_covariance, rel=1e-11, abs=1e-11)


def test_origin_certificate_exact_thresholds_and_fail_closed_inputs() -> None:
    base = {
        "renew": 1, "unused": 1, "match": 1, "age": 1, "warm": 1,
        "maintain": 1, "separation": 1, "slew": 1, "g_latch": 1,
        "mahalanobis_squared": 5.99, "q95": 0.60,
    }
    assert certificate_native([base])[0] is True
    failures = [
        {**base, "mahalanobis_squared": 5.9900001},
        {**base, "q95": 0.5999999},
        {**base, "match": 0},
        {**base, "mahalanobis_squared": math.nan},
    ]
    assert certificate_native(failures) == (False, False, False, False)


def test_wire_sizes_are_literal() -> None:
    assert wire_sizes_native() == {
        "SOURCE": 40, "SERVICE_RELAY": 64, "STATE": 64, "SNAPSHOT": 96,
        "READINESS": 48, "COMMIT_INTENT": 32, "NOOP_INTENT": 32, "COMMIT_RESULT": 24,
    }
