from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

import pytest

from experiments.candidates.variable_n_fleet_churn_b_explore import (
    BNativeTelemetryBatch,
    NativeTelemetryError,
    PairedPrimaryShadowBatch,
    derive_recovery_telemetry,
    native_artifact_identity,
    performance_readiness,
    require_boundary_equivalence,
)
from experiments.candidates.variable_n_fleet_churn_b_explore import native_backend as _b_native
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import (
    deterministic_general_episode,
)
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
    NativeInteractiveBatch,
)


def _fixtures(width: int):
    return tuple(deterministic_general_episode(1 + index % 2) for index in range(width))


@pytest.mark.parametrize("width", (8, 32))
def test_shadow_reset_step_and_tick_sums_are_exactly_equivalent(width: int) -> None:
    fixtures = _fixtures(width)
    primary = NativeInteractiveBatch(fixtures)
    shadow = BNativeTelemetryBatch(fixtures)
    try:
        assert shadow.initial == primary.initial
        prior = shadow.initial
        all_ticks = [[] for _ in range(width)]
        for epoch in range(6):
            commands = tuple(fixture.post_commands[epoch] for fixture in fixtures)
            primary_rows = primary.step(commands)
            shadow_rows = shadow.step(commands)
            require_boundary_equivalence(primary_rows, shadow_rows)
            for index, row in enumerate(shadow_rows):
                ticks = row["tick_rows"]
                assert len(ticks) == 20
                assert tuple(tick["post_loss_second"] for tick in ticks) == tuple(
                    range(20 * epoch, 20 * (epoch + 1))
                )
                assert tuple(tick["integrated_ticks"] for tick in ticks) == tuple(
                    range(121 + 20 * epoch, 141 + 20 * epoch)
                )
                assert all(
                    tick["failed_zone_delivery"]
                    == tick["zone1_delivery" if fixtures[index].failed_zone == 1 else "zone2_delivery"]
                    for tick in ticks
                )
                all_ticks[index].extend(ticks)
                assert row["receipt"]["raw_tick_rows"] == tuple(all_ticks[index])
            prior = primary_rows

        for index, (fixture, terminal, ticks) in enumerate(zip(fixtures, prior, all_ticks)):
            assert terminal["terminal"]
            assert sum(row["zone1_delivery"] + row["zone2_delivery"] for row in ticks) == terminal["total_endpoint"][0]
            failed = fixture.failed_zone - 1
            assert sum(row[("zone1_delivery", "zone2_delivery")[1 - failed]] for row in ticks) == terminal["intact_endpoint"][0]
            assert sum(
                row["failed_zone_delivery"]
                for row in ticks
                if row["post_loss_second"] < 60
            ) == terminal["fail_endpoint"][0]
            receipt = derive_recovery_telemetry(ticks)
            assert receipt["complete_0_60"]
            assert receipt["observed_failed_zone_seconds_0_60"] == 60
            transitions = [row for row in ticks if row["acquisition_transition"]]
            expected_reacquisition = transitions[0]["tick_end_second"] if transitions else None
            assert receipt["failed_zone_executor_reacquisition_time_seconds"] == expected_reacquisition
    finally:
        primary.close()
        shadow.close()


def test_malformed_batch_is_rejected_before_any_session_advances_and_close_is_safe() -> None:
    fixtures = _fixtures(8)
    shadow = BNativeTelemetryBatch(fixtures)
    fresh = BNativeTelemetryBatch(fixtures)
    try:
        malformed = [list(fixture.post_commands[0]) for fixture in fixtures]
        malformed[-1] = [2, 2, None, None]
        with pytest.raises(NativeTelemetryError, match="status 12"):
            shadow.step(malformed)
        valid = tuple(fixture.post_commands[0] for fixture in fixtures)
        assert shadow.step(valid) == fresh.step(valid)
    finally:
        shadow.close()
        shadow.close()
        fresh.close()
    with pytest.raises(NativeTelemetryError, match="closed"):
        shadow.step(tuple(fixture.post_commands[1] for fixture in fixtures))
    with pytest.raises(ValueError, match="B>=8"):
        BNativeTelemetryBatch(_fixtures(7))


def test_recovery_derivation_uses_delivery_tick_start_and_acquisition_tick_end() -> None:
    rows = tuple(
        {
            "post_loss_second": second,
            "tick_end_second": second + 1,
            "failed_zone_delivery": 1 if second >= 4 else 0,
            "acquisition_transition": second == 2,
        }
        for second in range(7)
    )
    receipt = derive_recovery_telemetry(rows)
    assert receipt["first_failed_zone_service_time_seconds"] == 4
    assert receipt["failed_zone_executor_reacquisition_time_seconds"] == 3
    assert receipt["failed_zone_zero_service_seconds_0_60"] == 4
    assert receipt["observed_failed_zone_seconds_0_60"] == 7
    assert receipt["complete_0_60"] is False
    no_event = tuple({**row, "failed_zone_delivery": 0, "acquisition_transition": False} for row in rows)
    receipt = derive_recovery_telemetry(no_event)
    assert receipt["first_failed_zone_service_time_seconds"] is None
    assert receipt["failed_zone_executor_reacquisition_time_seconds"] is None
    with pytest.raises(NativeTelemetryError, match="INCOMPLETE"):
        require_boundary_equivalence(
            ({"epoch": 1},), ({"interactive": {"epoch": 2}},)
        )


def test_b_artifact_has_own_identity_and_only_includes_unchanged_r09_sources() -> None:
    identity = native_artifact_identity()
    assert identity["included_r09_header"] is True
    assert identity["copied_routing_delivery_acquisition_energy_laws"] is False
    assert identity["registered_production_component"] is False
    assert identity["old_r09_exports_visible_from_b_artifact"] is False
    assert identity["artifact_path_distinct_from_registered_r09"] is True
    assert identity["artifact_sha256"] != identity["registered_r09_artifact_sha256"]
    assert identity["embedded_build_fingerprint"] == identity["build_key"]
    source = Path("experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp")
    assert identity["source_identity"]["included_r09_header_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert performance_readiness()["disposition"] == "PILOT_ONLY"
    assert performance_readiness()["process_tree_peak_rss_bytes"] is None


def test_paired_seam_materializes_one_input_and_passes_one_immutable_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert tuple(inspect.signature(PairedPrimaryShadowBatch).parameters) == ("fixtures",)
    with pytest.raises(TypeError):
        PairedPrimaryShadowBatch(_fixtures(8), _fixtures(8))  # type: ignore[call-arg]
    paired = PairedPrimaryShadowBatch(_fixtures(8))
    primary_ids: list[int] = []
    shadow_ids: list[int] = []
    original_primary = paired._primary.step
    original_shadow = paired._shadow.step

    def primary_step(commands):
        primary_ids.append(id(commands))
        return original_primary(commands)

    def shadow_step(commands):
        shadow_ids.append(id(commands))
        return original_shadow(commands)

    monkeypatch.setattr(paired._primary, "step", primary_step)
    monkeypatch.setattr(paired._shadow, "step", shadow_step)
    try:
        commands = tuple(fixture.post_commands[0] for fixture in _fixtures(8))
        result = paired.step(commands)
        assert primary_ids == shadow_ids
        assert result["primary_rows"] == tuple(
            row["interactive"] for row in result["shadow_rows"]
        )
        assert result["receipt"]["main_return_source"] == "registered_r09_native_interactive_primary"
        assert result["receipt"]["shadow_role"] == "telemetry_only_no_action_or_return_authority"
        with pytest.raises(ValueError, match="forbids"):
            paired.bcrh(include_candidate_records=True)
    finally:
        paired.close()


def test_paired_receipt_contains_six_exact_boundaries_and_canonical_digests() -> None:
    fixtures = _fixtures(8)
    paired = PairedPrimaryShadowBatch(fixtures)
    try:
        for epoch in range(6):
            result = paired.step(tuple(fixture.post_commands[epoch] for fixture in fixtures))
        receipt = result["receipt"]
        assert receipt["schema"] == "VNFC-BEXP-PAIRED-PRIMARY-SHADOW-RECEIPT-v1"
        assert len(receipt["input_digest"]) == 64
        assert len(receipt["action_digest"]) == 64
        assert receipt["initial"]["exact"] is True
        assert receipt["source_pre"] == receipt["source_post"]
        assert len(receipt["boundaries"]) == 6
        assert tuple(row["boundary_index"] for row in receipt["boundaries"]) == tuple(range(6))
        assert all(row["exact"] and row["source_exact_pre_post"] for row in receipt["boundaries"])
        assert all(row["primary_full_output_digest"] == row["shadow_full_output_digest"] for row in receipt["boundaries"])
        assert all(row["shadow_ticks_per_session"] == (20,) * 8 for row in receipt["boundaries"])
        assert receipt["boundaries"][-1]["primary_integrated_ticks"] == (240,) * 8
        assert receipt["boundaries"][-1]["shadow_integrated_ticks"] == (240,) * 8
    finally:
        paired.close()


def test_paired_boundary_drift_fails_incomplete_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures = _fixtures(8)
    paired = PairedPrimaryShadowBatch(fixtures)
    original_shadow = paired._shadow.step

    def drift(commands):
        rows = list(original_shadow(commands))
        first = dict(rows[0])
        interactive = dict(first["interactive"])
        interactive["epoch"] = int(interactive["epoch"]) + 1
        first["interactive"] = interactive
        rows[0] = first
        return tuple(rows)

    monkeypatch.setattr(paired._shadow, "step", drift)
    with pytest.raises(NativeTelemetryError, match="INCOMPLETE"):
        paired.step(tuple(fixture.post_commands[0] for fixture in fixtures))
    with pytest.raises(NativeTelemetryError, match="closed"):
        paired.step(tuple(fixture.post_commands[1] for fixture in fixtures))


def test_loaded_dll_cannot_be_rebound_after_source_identity_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures = _fixtures(8)
    batch = BNativeTelemetryBatch(fixtures)
    old_library = batch._library
    old_identity = _b_native._source_identity()
    changed_identity = dict(old_identity)
    changed_identity["b_adapter_source_sha256"] = "0" * 64
    monkeypatch.setattr(_b_native, "_source_identity", lambda: changed_identity)
    try:
        with pytest.raises(NativeTelemetryError, match="INCOMPLETE"):
            batch.step(tuple(fixture.post_commands[0] for fixture in fixtures))
        monkeypatch.setattr(_b_native, "_load_b_native_telemetry", lambda _: old_library)
        with pytest.raises(NativeTelemetryError, match="fingerprint"):
            BNativeTelemetryBatch(fixtures)
    finally:
        batch.close()


def test_paired_freezes_source_before_primary_reset_and_closes_on_between_reset_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures = _fixtures(8)
    stable = _b_native._source_identity()
    drifted = dict(stable)
    drifted["included_r09_header_sha256"] = "1" * 64
    state = {"identity": stable, "primary": None}
    original_primary_type = _b_native._r09.NativeInteractiveBatch

    def primary_reset(items):
        primary = original_primary_type(items)
        state["primary"] = primary
        state["identity"] = drifted
        return primary

    monkeypatch.setattr(_b_native, "_source_identity", lambda: state["identity"])
    monkeypatch.setattr(_b_native._r09, "NativeInteractiveBatch", primary_reset)
    with pytest.raises(NativeTelemetryError, match="across primary reset"):
        PairedPrimaryShadowBatch(fixtures)
    assert state["primary"] is not None
    assert state["primary"]._open is False


def test_b_native_reset_post_fence_drift_closes_created_handles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures = _fixtures(8)
    library = _b_native.require_b_native_telemetry()
    stable = _b_native._source_identity()
    drifted = dict(stable)
    drifted["b_adapter_source_sha256"] = "2" * 64
    state = {"identity": stable, "close_calls": 0}
    original_reset = library.vnfc_b_tick_reset_batch
    original_close = library.vnfc_b_tick_close_batch

    def reset_then_drift(inputs, width, handles, outputs):
        status = original_reset(inputs, width, handles, outputs)
        state["identity"] = drifted
        return status

    def recording_close(handles, width):
        state["close_calls"] += 1
        return original_close(handles, width)

    monkeypatch.setattr(_b_native, "_source_identity", lambda: state["identity"])
    monkeypatch.setattr(
        _b_native,
        "require_b_native_telemetry",
        lambda **_: library,
    )
    monkeypatch.setattr(library, "vnfc_b_tick_reset_batch", reset_then_drift)
    monkeypatch.setattr(library, "vnfc_b_tick_close_batch", recording_close)
    with pytest.raises(NativeTelemetryError, match="across native reset"):
        BNativeTelemetryBatch(fixtures, expected_source_identity=stable)
    assert state["close_calls"] == 1


def test_paired_rejects_stable_artifact_change_between_boundaries_before_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures = _fixtures(8)
    paired = PairedPrimaryShadowBatch(fixtures)
    paired_bcrh = PairedPrimaryShadowBatch(fixtures)
    paired_sensitivity = PairedPrimaryShadowBatch(fixtures)
    original_snapshot = _b_native._paired_source_snapshot

    def replaced_primary_artifact(primary, shadow):
        snapshot = original_snapshot(primary, shadow)
        snapshot["primary_artifact_sha256"] = "3" * 64
        return snapshot

    monkeypatch.setattr(
        _b_native, "_paired_source_snapshot", replaced_primary_artifact
    )
    with pytest.raises(NativeTelemetryError, match="between boundaries"):
        paired.step(tuple(fixture.post_commands[0] for fixture in fixtures))
    assert paired._open is False
    assert paired._primary._open is False
    assert paired._shadow._open is False
    with pytest.raises(NativeTelemetryError, match="before BCRH"):
        paired_bcrh.bcrh()
    assert paired_bcrh._open is False
    assert paired_bcrh._primary._open is False
    assert paired_bcrh._shadow._open is False
    with pytest.raises(NativeTelemetryError, match="before sensitivity"):
        paired_sensitivity.sensitivity()
    assert paired_sensitivity._open is False
    assert paired_sensitivity._primary._open is False
    assert paired_sensitivity._shadow._open is False


def test_primary_only_sensitivity_returns_width_rows_and_does_not_advance_state() -> None:
    fixtures = _fixtures(8)
    diagnosed = PairedPrimaryShadowBatch(fixtures)
    control = PairedPrimaryShadowBatch(fixtures)
    try:
        before = diagnosed.receipt
        rows = diagnosed.sensitivity()
        assert len(rows) == 8
        assert all(
            set(row)
            == {"candidate_count", "min_c60", "max_c60", "sensitive"}
            for row in rows
        )
        assert diagnosed.receipt == before
        commands = tuple(fixture.post_commands[0] for fixture in fixtures)
        diagnosed_step = diagnosed.step(commands)
        control_step = control.step(commands)
        assert diagnosed_step["primary_rows"] == control_step["primary_rows"]
        assert tuple(
            row["interactive"] for row in diagnosed_step["shadow_rows"]
        ) == tuple(row["interactive"] for row in control_step["shadow_rows"])
        assert diagnosed_step["receipt"]["action_digest"] == control_step["receipt"]["action_digest"]
        assert diagnosed_step["receipt"]["boundaries"] == control_step["receipt"]["boundaries"]
    finally:
        diagnosed.close()
        control.close()
