from __future__ import annotations

from dataclasses import fields, replace
import copy
import math

import numpy as np
import pytest

from ha_ctse_process import uav_episode_schema as episode_schema
from ha_ctse_process import uav_g0_geometry as geometry
from ha_ctse_process import uav_g0_statistics as statistics
from ha_ctse_process import uav_source_identifiability_g0 as g0


def test_shared_episode_schema_exports_and_layout_are_exact() -> None:
    expected_exports = (
        "PHYSICAL_HORIZON",
        "PHYSICAL_UAVS",
        "GROUND_USERS",
        "ACTION_DIM",
        "SERVICE_TARGET",
        "G0RealizationError",
        "Cell",
        "Control",
        "LifecycleBoundaryEvent",
        "EpisodeMetrics",
        "EpisodeRunEvidence",
        "EPISODE_RUN_ARRAY_SPECS",
        "_readonly_array",
    )
    assert all(
        getattr(g0, name) is getattr(episode_schema, name) for name in expected_exports
    )
    assert (
        g0.PHYSICAL_HORIZON,
        g0.PHYSICAL_UAVS,
        g0.GROUND_USERS,
        g0.ACTION_DIM,
        g0.SERVICE_TARGET,
    ) == (500, 8, 30, 4, 0.90) == (
        episode_schema.PHYSICAL_HORIZON,
        episode_schema.PHYSICAL_UAVS,
        episode_schema.GROUND_USERS,
        episode_schema.ACTION_DIM,
        episode_schema.SERVICE_TARGET,
    )
    assert [item.name for item in fields(episode_schema.LifecycleBoundaryEvent)] == [
        "kind",
        "physical_step",
        "previous_handle",
        "current_handle",
        "owner_target",
    ]
    assert [item.type for item in fields(episode_schema.LifecycleBoundaryEvent)] == [
        "str", "int", "str", "str | None", "str"
    ]
    assert [item.name for item in fields(episode_schema.EpisodeMetrics)] == [
        "episode_id",
        "control",
        "cell",
        "onset",
        "duration",
        "j_event",
        "q_ordinary",
        "m_event",
        "a_control",
        "b_access",
        "c_cat",
    ]
    assert [item.name for item in fields(episode_schema.EpisodeRunEvidence)] == [
        "episode_id",
        "control",
        "cell",
        "metrics",
        "source_sha256",
        "user_demand_input_mbps",
        "user_delivered_input_mbps",
        "channel_association_input",
        "delivered_user_rates_mbps",
        "target_trace",
        "raw_action_trace",
        "executed_velocity_trace",
        "position_trace",
        "active_mask_trace",
        "controller_evidence",
        "target_trace_sha256",
        "raw_action_trace_sha256",
        "executed_velocity_trace_sha256",
        "executed_position_trace_sha256",
        "service_trace_sha256",
        "controller_state_sha256",
        "lifecycle_events",
        "tracker_failures",
        "action_support_violations",
        "ownership_violations",
        "backhaul_guard_blocked_actions",
        "oracle_qualification_failures",
        "weakest_service",
    ]
    assert list(episode_schema.EPISODE_RUN_ARRAY_SPECS.items()) == [
        ("user_demand_input_mbps", ((500, 30), np.dtype(np.float64))),
        ("user_delivered_input_mbps", ((500, 30), np.dtype(np.float64))),
        ("channel_association_input", ((500, 8, 30), np.dtype(np.bool_))),
        ("delivered_user_rates_mbps", ((500, 30), np.dtype(np.float64))),
        ("target_trace", ((500, 8, 3), np.dtype(np.float64))),
        ("raw_action_trace", ((500, 8, 4), np.dtype(np.float32))),
        ("executed_velocity_trace", ((500, 8, 3), np.dtype(np.float64))),
        ("position_trace", ((501, 8, 3), np.dtype(np.float64))),
        ("active_mask_trace", ((500, 8), np.dtype(np.bool_))),
        ("weakest_service", ((500,), np.dtype(np.float64))),
    ]
    lifecycle = episode_schema.LifecycleBoundaryEvent("LEAVE", 1, "old", None, "p/0")
    assert list(lifecycle.to_primitive()) == [
        "kind",
        "physical_step",
        "previous_handle",
        "current_handle",
        "owner_target",
    ]
    metrics = episode_schema.EpisodeMetrics(
        0,
        episode_schema.Control.SAME_INFORMATION,
        episode_schema.Cell.NO_EVENT,
        200,
        80,
        1.0,
        0.90,
        0.0,
        1.0,
        1,
        0,
    )
    assert list(metrics.to_primitive()) == [
        "episode_id",
        "control",
        "cell",
        "onset",
        "duration",
        "J_event",
        "Q_ordinary",
        "M_event",
        "A_control",
        "B_access",
        "C_cat",
    ]


def test_callable_source_digests_are_cached_by_callable_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_getsource = g0.inspect.getsource
    calls: list[object] = []

    def counted_getsource(value: object) -> str:
        calls.append(value)
        return original_getsource(value)

    g0._callable_source_digest.cache_clear()
    monkeypatch.setattr(g0.inspect, "getsource", counted_getsource)
    first = g0.common_tracker_source_digest()
    second = g0.common_tracker_source_digest()
    assert first == second == g0.ACCEPTED_G1_TRACKER_SOURCE_SHA256
    assert calls == [geometry.actions_toward_targets]

    def replacement_tracker(**_kwargs: object) -> np.ndarray:
        return np.zeros((g0.PHYSICAL_UAVS, g0.ACTION_DIM), dtype=np.float32)

    monkeypatch.setattr(geometry, "actions_toward_targets", replacement_tracker)
    replacement = g0.common_tracker_source_digest()
    assert replacement != first
    assert calls == [geometry.g1_common_target_actions, replacement_tracker]


def test_validated_context_rejects_forgery_cross_source_and_nested_ledger_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = geometry.make_episode_source(0)
    candidates = tuple(
        g0.OracleCandidateSafetyTrace(
            candidate_id=label.key,
            target_schedule_sha256=geometry.sha256_json([]),
            common_prestate_sha256=geometry.sha256_json({}),
            steps=(),
            hard_violation_count=0,
            gate_arrival_time=g0.PHYSICAL_HORIZON + 1,
            gate_arrival_error=1.0,
            event_window_tracking_error=0.0,
            path_length=0.0,
            stage_coordinates=tuple(
                float(item) for item in source.geometry.coordinate(label)
            ),
            trace_sha256=geometry.sha256_json([]),
        )
        for label in geometry.TARGET_LABELS
        if label.kind is geometry.TargetKind.STAGE
    )
    provisional = g0.OracleSafetyLedger(
        source_sha256=source.to_primitive()["sha256"],
        common_prestate={},
        common_prestate_sha256=geometry.sha256_json({}),
        candidate_prestate_sha256=(geometry.sha256_json({}),) * 2,
        channel_draw_schema=(),
        shared_channel_draw_blocks=(),
        candidates=(candidates[0], candidates[1]),
        selected_candidate_id=candidates[0].candidate_id,
        selected_rank=candidates[0].rank,
        shared_action_method_sha256=g0.oracle_safety_method_digests(),
        content_sha256="",
    )
    ledger = replace(
        provisional,
        content_sha256=geometry.sha256_json(
            provisional.to_primitive(include_digest=False)
        ),
    )
    candidate_digests = tuple(item.trace_sha256 for item in ledger.candidates)
    certificate = g0.OracleSafetyCertificate(
        ledger_sha256=ledger.content_sha256,
        selected_candidate_id=ledger.selected_candidate_id,
        candidate_trace_sha256=candidate_digests,
    )
    with pytest.raises(TypeError):
        g0._ValidatedOracleSafetyContext(
            source=source,
            ledger=ledger,
            certificate=certificate,
            content_sha256=ledger.content_sha256,
            candidate_trace_sha256=candidate_digests,
        )
    forged = object.__new__(g0._ValidatedOracleSafetyContext)
    with pytest.raises(g0.G0RealizationError, match="not module-issued"):
        g0._require_validated_oracle_safety_context(forged)

    def validated(
        supplied_source: geometry.G0EpisodeSource,
        supplied_ledger: g0.OracleSafetyLedger,
    ) -> g0.OracleSafetyCertificate:
        assert supplied_source is source
        assert supplied_ledger is ledger
        return certificate

    monkeypatch.setattr(g0, "validate_oracle_safety_ledger", validated)
    context = g0._validated_oracle_safety_context(source, ledger)
    bound_source, bound_ledger, bound_certificate = (
        g0._require_validated_oracle_safety_context(context)
    )
    assert bound_source is source
    assert bound_ledger is ledger
    assert bound_certificate is certificate

    cross_source_context = g0._validated_oracle_safety_context(source, ledger)
    object.__setattr__(
        cross_source_context,
        "source",
        geometry.make_episode_source(1),
    )
    with pytest.raises(g0.G0RealizationError, match="context drifted"):
        g0._require_validated_oracle_safety_context(cross_source_context)
    ledger.common_prestate["tampered"] = True
    with pytest.raises(g0.G0RealizationError, match="context drifted"):
        g0._require_validated_oracle_safety_context(context)


@pytest.fixture(scope="module")
def oracle_safety_bundle() -> tuple[
    geometry.G0EpisodeSource,
    g0.OracleSafetyLedger,
    g0.OracleQualificationCertificate,
]:
    source = geometry.make_episode_source(0)
    ledger = g0.build_oracle_safety_ledger(source)
    qualification = g0.oracle_qualification_from_safety_ledger(source, ledger)
    return source, ledger, qualification


@pytest.fixture(scope="module")
def oracle_behavior_bundle(
    oracle_safety_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleQualificationCertificate,
    ],
) -> tuple[
    geometry.G0EpisodeSource,
    g0.OracleSafetyLedger,
    g0.OracleCandidateSafetyTrace,
    g0.OracleBehavioralExecution,
]:
    source, ledger, _qualification = oracle_safety_bundle
    selected = next(
        candidate
        for candidate in ledger.candidates
        if candidate.candidate_id == ledger.selected_candidate_id
    )
    behavior = g0._build_selected_oracle_behavioral_execution(source, ledger)
    return source, ledger, selected, behavior


def _reseal_behavioral_primitive(value: dict) -> dict:
    result = copy.deepcopy(value)
    result["trace_sha256"] = geometry.sha256_json(
        {key: item for key, item in result.items() if key != "trace_sha256"}
    )
    return result


def _rows(
    source: geometry.G0EpisodeSource,
    *,
    active_owner: bool,
    replacement: str | None = None,
    owner_at_primary: bool = False,
) -> tuple[g0.AnonymousLifecycleRow, ...]:
    handles = list(g0.initial_lifecycle_handles(source))
    owner = source.assignment.row_to_target.index(source.event.owner_target.key)
    if replacement is not None:
        handles[owner] = replacement
    rows: list[g0.AnonymousLifecycleRow] = []
    for index, handle in enumerate(handles):
        xy = source.geometry.physical_xy[index]
        if index == owner and owner_at_primary:
            xy = source.geometry.coordinate(source.event.owner_target)
        active = active_owner if index == owner else True
        rows.append(
            g0.AnonymousLifecycleRow(
                handle=handle,
                position=np.asarray([xy[0], xy[1], geometry.FIXED_ALTITUDE_M]),
                velocity=np.zeros(3),
                active=active,
                service_available=active,
            )
        )
    return tuple(rows)


def _information(
    source: geometry.G0EpisodeSource,
    rows: tuple[g0.AnonymousLifecycleRow, ...],
    *,
    weakest_service: float = 0.0,
) -> g0.G0CurrentInformation:
    rates = np.full(g0.GROUND_USERS, float(weakest_service), dtype=np.float64)
    return g0.make_current_information(
        source,
        rows=rows,
        user_demand_mbps=np.ones(g0.GROUND_USERS, dtype=np.float64),
        user_delivered_rate_mbps=rates,
        channel_association=np.zeros(
            (g0.PHYSICAL_UAVS, g0.GROUND_USERS), dtype=np.bool_
        ),
    )


def test_source_geometry_rng_assignment_and_support_are_exact() -> None:
    assert g0.DESIGN_ROUND == "20260730_uav_g0_executable_contract_addendum_v2"
    assert g0.DESIGN_PACKAGE_STAGE_COMMIT == "8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc"
    assert g0.DESIGN_ARCHIVE_COMMIT == "9c1566e1c6adefcd500facb1bb50d5a7428eae9c"
    assert g0.DESIGN_DISPOSITION == (
        "G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT"
    )
    source = geometry.make_episode_source(17)
    duplicate = geometry.make_episode_source(17)
    assert source.to_primitive() == duplicate.to_primitive()
    episode_geometry = source.geometry
    assert np.array_equal(episode_geometry.base_xy, [4000.0, 4000.0])
    assert episode_geometry.target_labels == geometry.TARGET_LABELS
    assert tuple(source.assignment.primary_count_by_hotspot) == (2, 2, 2)
    assert source.assignment.staging_count == 2
    assert sorted(episode_geometry.slot_to_target.tolist()) == list(range(8))
    assert np.array_equal(
        episode_geometry.physical_xy,
        episode_geometry.target_owned_initial_xy[episode_geometry.slot_to_target],
    )
    assert source.event.owner_target.kind is geometry.TargetKind.PRIMARY
    assert 180 <= source.event.onset <= 220
    assert 80 <= source.event.duration <= 100
    assert len({geometry.channel_seed_word(17, step) for step in range(4)}) == 4
    support = episode_geometry.to_primitive()["geometry_support_certificate"]
    assert support == geometry.geometry_support_certificate(
        map_width=episode_geometry.map_width,
        map_height=episode_geometry.map_height,
        base_xy=episode_geometry.base_xy,
    )
    assert support["certificate_kind"] == (
        "analytic_radial_complete_support_every_phi_v2"
    )
    assert support["passed"] is True
    assert support["violation_count"] == 0
    assert set(support["support_radial_bounds"]) == {
        "hotspot_centers",
        "user_disks",
        "primaries",
        "primary_perturbation_disks",
        "stages",
        "stage_perturbation_disks",
        "gates",
    }
    for width, height in ((1.0, 1.0), (1.0, 100.0), (100.0, 1.0)):
        universal = geometry.geometry_support_certificate(
            map_width=width,
            map_height=height,
            base_xy=np.asarray((width / 2.0, height / 2.0)),
        )
        assert universal["passed"] is True
        assert universal["violation_count"] == 0
    failed = geometry.geometry_support_certificate(
        map_width=1.0,
        map_height=1.0,
        base_xy=np.asarray((0.01, 0.5)),
    )
    assert failed["violation_count"] == len(failed["violations"]) > 0

    with pytest.raises(g0.G0RealizationError, match="registered episode RNG"):
        replace(
            episode_geometry,
            phi=np.nextafter(episode_geometry.phi, math.inf),
        )
    with pytest.raises(g0.G0RealizationError, match="event ledger"):
        replace(source.event, onset=180 if source.event.onset != 180 else 181)
    forged = replace(
        source.assignment,
        row_to_target=tuple(reversed(source.assignment.row_to_target)),
        passed=True,
    )
    with pytest.raises(g0.G0RealizationError, match="does not reconstruct"):
        replace(source, assignment=forged)
    with pytest.raises(g0.G0RealizationError, match="frozen S7-S1"):
        geometry.make_episode_source(17, map_width=7999.0)
    with pytest.raises(g0.G0RealizationError, match="rectangular-map center"):
        geometry.make_episode_source(17, base_xy=(3999.0, 4000.0))


def test_anonymous_assignment_tie_law_and_duplicate_rows_fail_closed() -> None:
    source = geometry.make_episode_source(3)
    rows = np.concatenate((source.geometry.physical_xy, np.zeros((8, 2))), axis=1)
    certificate = geometry.minimum_cost_target_assignment(
        physical_rows=rows,
        target_xy=source.geometry.target_xy,
    )
    order = np.asarray((3, 0, 7, 2, 6, 1, 5, 4))
    permuted = geometry.minimum_cost_target_assignment(
        physical_rows=rows[order],
        target_xy=source.geometry.target_xy,
    )
    original_world = {
        tuple(rows[index]): certificate.row_to_target[index] for index in range(8)
    }
    permuted_world = {
        tuple(rows[order][index]): permuted.row_to_target[index] for index in range(8)
    }
    assert original_world == permuted_world
    duplicate = rows.copy()
    duplicate[1] = duplicate[0]
    with pytest.raises(g0.G0RealizationError, match="bitwise-identical"):
        geometry.minimum_cost_target_assignment(
            physical_rows=duplicate,
            target_xy=source.geometry.target_xy,
        )


def test_accepted_g1_tracker_and_shared_correction_are_qualified() -> None:
    source = geometry.make_episode_source(0)
    physical = np.concatenate(
        (source.geometry.physical_xy, np.full((8, 1), geometry.FIXED_ALTITUDE_M)),
        axis=1,
    )
    targets = np.stack(
        [
            np.concatenate(
                (
                    source.geometry.coordinate(geometry.TargetLabel.parse(label)),
                    [geometry.FIXED_ALTITUDE_M],
                )
            )
            for label in source.assignment.row_to_target
        ]
    )
    active = np.asarray([True, False, True, True, True, True, True, True])
    certificate = g0.qualify_common_tracker(
        episode_source=source,
        physical_positions=physical,
        target_positions=targets,
        active_mask=active,
        max_speed=30.0,
        max_vertical_speed=5.0,
        time_step=1.0,
        permutation=(3, 1, 7, 0, 6, 2, 5, 4),
    )
    assert g0.common_tracker_source_digest() == g0.ACCEPTED_G1_TRACKER_SOURCE_SHA256
    assert certificate["accepted_g1_source_commit"] == g0.ACCEPTED_G1_SOURCE_COMMIT
    assert certificate["shared_action_method_identity"] is True
    assert certificate["permutation_equivariant"] is True
    assert certificate["executed_permutation_equivariant"] is True
    assert certificate["inactive_action_rows_zero"] is True
    assert certificate["passed"] is True


def test_same_information_rejoin_uses_gate_then_returns_to_stage() -> None:
    source = geometry.make_episode_source(4)
    handles = g0.initial_lifecycle_handles(source)
    owner_row = source.assignment.row_to_target.index(source.event.owner_target.key)
    controller = g0.SameInformationController(source, handles)
    leave_rows = _rows(source, active_owner=False)
    controller.on_leave(handles[owner_row], leave_rows)
    selected = controller.evidence()["selected_reserve"]
    assert selected is not None
    leave_targets = controller.target_map(
        _information(source, leave_rows),
        physical_step=source.event.onset,
    )
    assert np.array_equal(
        leave_targets[selected][:2], source.geometry.coordinate(source.event.owner_target)
    )

    replacement = g0.replacement_lifecycle_handle(source, handles[owner_row])
    controller.on_rejoin(handles[owner_row], replacement, source.event.rejoin)
    rejoin_rows = _rows(
        source,
        active_owner=True,
        replacement=replacement,
        owner_at_primary=False,
    )
    gate_targets = controller.target_map(
        _information(source, rejoin_rows, weakest_service=1.0),
        physical_step=source.event.rejoin,
    )
    assert np.array_equal(
        gate_targets[selected][:2], source.geometry.gate(source.event.owner_target)
    )
    returned = controller.target_map(
        _information(source, rejoin_rows, weakest_service=1.0),
        physical_step=source.event.rejoin + 1,
    )
    stage = geometry.TargetLabel.parse(
        next(
            label
            for handle, label in controller.original_ownership.items()
            if handle == selected
        ).key
    )
    assert stage.kind is geometry.TargetKind.STAGE
    assert np.array_equal(returned[selected][:2], source.geometry.coordinate(stage))
    owner = next(row for row in rejoin_rows if row.handle == replacement)
    assert not np.array_equal(
        owner.position[:2], source.geometry.coordinate(source.event.owner_target)
    )


def test_same_information_reserve_tie_ignores_vertical_fields() -> None:
    source = geometry.make_episode_source(4)
    handles = g0.initial_lifecycle_handles(source)
    ownership = {
        handle: geometry.TargetLabel.parse(target)
        for handle, target in zip(handles, source.assignment.row_to_target)
    }
    owner_handle = next(
        handle for handle, label in ownership.items() if label == source.event.owner_target
    )
    reserve_handles = [
        handle for handle, label in ownership.items() if label.kind is geometry.TargetKind.STAGE
    ]
    expected = min(
        reserve_handles,
        key=lambda handle: tuple(source.geometry.coordinate(ownership[handle])),
    )
    common_xy = source.geometry.base_xy.copy()
    rows = []
    for row in _rows(source, active_owner=False):
        if row.handle in reserve_handles:
            rows.append(
                replace(
                    row,
                    position=np.asarray(
                        [common_xy[0], common_xy[1], 100.0 if row.handle == expected else 1.0]
                    ),
                    velocity=np.asarray(
                        [0.0, 0.0, 100.0 if row.handle == expected else -100.0]
                    ),
                )
            )
        else:
            rows.append(row)
    controller = g0.SameInformationController(source, handles)
    controller.on_leave(owner_handle, tuple(rows))
    assert controller.evidence()["selected_reserve"] == expected


def test_no_reallocation_freezes_targets_and_no_event_maps_match() -> None:
    source = geometry.make_episode_source(6)
    handles = g0.initial_lifecycle_handles(source)
    rows = _rows(source, active_owner=True)
    same = g0.SameInformationController(source, handles)
    frozen = g0.NoReallocationController(source, handles)
    information = _information(source, rows)
    same_targets = same.target_map(information, physical_step=0)
    frozen_targets = frozen.target_map(information, physical_step=0)
    assert same_targets.keys() == frozen_targets.keys()
    assert all(
        np.array_equal(same_targets[handle], frozen_targets[handle])
        for handle in same_targets
    )
    owner_row = source.assignment.row_to_target.index(source.event.owner_target.key)
    leave_rows = _rows(source, active_owner=False)
    frozen.on_leave(handles[owner_row], leave_rows)
    after = frozen.target_map(
        _information(source, leave_rows),
        physical_step=source.event.onset,
    )
    assert all(
        np.array_equal(after[handle], frozen_targets[handle]) for handle in after
    )


def test_oracle_two_candidate_schedule_certificate_is_exact(
    oracle_safety_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleQualificationCertificate,
    ],
) -> None:
    source, ledger, certificate = oracle_safety_bundle
    g0.validate_oracle_qualification(
        source, certificate, safety_ledger=ledger
    )
    assert certificate.passed is True
    assert certificate.candidate_count == 2
    assert certificate.both_candidates_evaluated is True
    assert certificate.unaffected_primary_move_creates_vacancy is True
    assert certificate.candidate_owner_is_reserve is True
    assert certificate.shared_dynamics_action_safety_identity is True
    assert certificate.complexity == "O(H*K_search)"
    assert all(row.gate_arrival_time > 0 for row in certificate.candidates)
    assert all(
        row.gate_arrival_time <= source.event.onset
        or row.gate_arrival_time == g0.PHYSICAL_HORIZON + 1
        for row in certificate.candidates
    )
    assert all(row.physical_steps_advanced == 500 for row in certificate.candidates)
    assert all(row.hard_violation_count == 0 for row in certificate.candidates)
    primary = source.geometry.coordinate(source.event.owner_target)
    gate = np.concatenate(
        (source.geometry.gate(source.event.owner_target), [geometry.FIXED_ALTITUDE_M])
    )
    for row, trace in zip(certificate.candidates, ledger.candidates):
        reserve_internal = g0._target_internal_row(row.reserve_target)
        if row.gate_arrival_time <= source.event.onset:
            arrival_position = trace.steps[
                row.gate_arrival_time
            ].current_uav_positions.array()[reserve_internal]
            assert np.array_equal(arrival_position, gate)
        else:
            assert not any(
                np.array_equal(
                    trace.steps[step].current_uav_positions.array()[reserve_internal],
                    gate,
                )
                for step in range(row.latest_departure, source.event.onset + 1)
            )
        expected_tracking_error = sum(
            float(
                np.sum(
                    (
                        trace.steps[step].next_uav_positions.array()[
                            reserve_internal, :2
                        ]
                        - primary
                    )
                    ** 2
                )
            )
            for step in range(source.event.onset, source.event.rejoin)
        )
        assert row.event_window_tracking_error == expected_tracking_error
        assert any(
            any(
                step.real_guard_intervention_or_violation_output[
                    "intervention_by_uav"
                ]
            )
            for step in trace.steps
        )
    assert certificate.selected_rank == min(row.rank for row in certificate.candidates)
    forged = replace(certificate, selected_reserve_target="stage/+1")
    if forged.to_primitive() != certificate.to_primitive():
        with pytest.raises(g0.G0RealizationError, match="forged"):
            g0.validate_oracle_qualification(
                source, forged, safety_ledger=ledger
            )


def test_oracle_gate_arrival_is_bitwise_and_onset_bounded() -> None:
    gate = np.asarray((1.0, 2.0, geometry.FIXED_ALTITUDE_M), dtype=np.float64)
    near = gate.copy()
    near[0] = np.nextafter(near[0], math.inf)
    assert not g0._is_exact_gate_arrival(
        near,
        gate,
        physical_step=190,
        latest_departure=100,
        event_onset=191,
    )
    assert g0._is_exact_gate_arrival(
        gate,
        gate,
        physical_step=191,
        latest_departure=100,
        event_onset=191,
    )
    assert not g0._is_exact_gate_arrival(
        gate,
        gate,
        physical_step=192,
        latest_departure=100,
        event_onset=191,
    )


def test_negative_latest_departure_fails_builder_and_validator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = geometry.make_episode_source(0)
    environment = g0.UAVSourceIdentifiabilityEnv(source, g0.Cell.EVENT)
    try:
        environment.reset()
        prestate = g0._complete_oracle_prestate(environment)
    finally:
        environment.close()
    prestate_sha256 = geometry.sha256_json(prestate)
    candidates = tuple(
        g0.OracleCandidateSafetyTrace(
            candidate_id=label.key,
            target_schedule_sha256=geometry.sha256_json([]),
            common_prestate_sha256=prestate_sha256,
            steps=(),
            hard_violation_count=0,
            gate_arrival_time=g0.PHYSICAL_HORIZON + 1,
            gate_arrival_error=0.0,
            event_window_tracking_error=0.0,
            path_length=0.0,
            stage_coordinates=tuple(
                float(item) for item in source.geometry.coordinate(label)
            ),
            trace_sha256=geometry.sha256_json([]),
        )
        for label in geometry.TARGET_LABELS
        if label.kind is geometry.TargetKind.STAGE
    )
    provisional = g0.OracleSafetyLedger(
        source_sha256=source.to_primitive()["sha256"],
        common_prestate=prestate,
        common_prestate_sha256=prestate_sha256,
        candidate_prestate_sha256=(prestate_sha256, prestate_sha256),
        channel_draw_schema=(),
        shared_channel_draw_blocks=(),
        candidates=candidates,
        selected_candidate_id=candidates[0].candidate_id,
        selected_rank=candidates[0].rank,
        shared_action_method_sha256=g0.oracle_safety_method_digests(),
        content_sha256="",
    )
    ledger = replace(
        provisional,
        content_sha256=geometry.sha256_json(
            provisional.to_primitive(include_digest=False)
        ),
    )
    monkeypatch.setattr(
        g0,
        "_minimum_tracker_travel_steps",
        lambda *args, **kwargs: source.event.onset + 1,
    )
    reserve = next(
        label for label in geometry.TARGET_LABELS if label.kind is geometry.TargetKind.STAGE
    )
    with pytest.raises(g0.G0RealizationError, match="latest departure is negative"):
        g0._oracle_candidate_trace(source, reserve)
    with pytest.raises(g0.G0RealizationError, match="latest departure is negative"):
        g0.validate_oracle_safety_ledger(source, ledger)


def test_registered_oracle_safety_ledger_is_exact_and_service_blind(
    oracle_safety_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleQualificationCertificate,
    ],
) -> None:
    source, ledger, _qualification = oracle_safety_bundle
    certificate = g0.validate_oracle_safety_primitive(
        source, ledger.to_primitive()
    )
    assert certificate.ledger_sha256 == ledger.content_sha256
    assert ledger.channel_draw_schema == ()
    assert ledger.shared_channel_draw_blocks == ()
    assert ledger.candidate_prestate_sha256 == (
        ledger.common_prestate_sha256,
        ledger.common_prestate_sha256,
    )
    assert len(ledger.candidates) == 2
    assert sum(len(candidate.steps) for candidate in ledger.candidates) == 2 * 500
    assert ledger.selected_rank == min(
        candidate.rank for candidate in ledger.candidates
    )
    assert set(ledger.shared_action_method_sha256) >= {
        "g0_channel_update",
        "scenario7_connection_update",
        "native_routing_update",
        "scenario7_link_capacity",
        "g0_guard_capacity_capture",
        "g0_safety_only_transition",
    }
    first = ledger.candidates[0].steps[0]
    assert set(first.to_primitive()) == g0._ORACLE_SAFETY_ALLOWED_STEP_KEYS
    assert set(first.connections) == {"user", "uav", "uav_bs"}
    assert first.current_service_mask.array().dtype == np.bool_
    assert not any(
        token in str(first.to_primitive()).lower()
        for token in ("delivered_rate", "reward", "qos", "a_control", "c_cat")
    )


@pytest.mark.parametrize("tamper_kind", ("connection", "routing"))
def test_resealed_oracle_network_inputs_require_native_provenance(
    oracle_safety_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleQualificationCertificate,
    ],
    tamper_kind: str,
) -> None:
    source, ledger, _qualification = oracle_safety_bundle
    tampered = copy.deepcopy(ledger.to_primitive())
    candidate = tampered["candidates"][0]
    step = candidate["steps"][0]
    if tamper_kind == "connection":
        connections = g0._native_array_from_primitive(
            step["connections"]["user"]
        ).array()
        connections[0, 0] = ~connections[0, 0]
        step["connections"]["user"] = (
            g0._NativeArrayEvidence.from_array(connections).to_primitive()
        )
    else:
        assert len(step["routing_paths"]) > 1
        step["routing_paths"] = list(reversed(step["routing_paths"]))
    candidate["trace_sha256"] = geometry.sha256_json(candidate["steps"])
    tampered["content_sha256"] = geometry.sha256_json(
        {
            key: value
            for key, value in tampered.items()
            if key != "content_sha256"
        }
    )
    with pytest.raises(
        g0.G0RealizationError,
        match="oracle (connection|routing) input is not bound",
    ):
        g0.validate_oracle_safety_primitive(source, tampered)


def test_oracle_safety_tamper_fails_closed_and_replay_is_two_trace_exact(
    oracle_safety_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleQualificationCertificate,
    ],
) -> None:
    source, ledger, _qualification = oracle_safety_bundle
    primitive = ledger.to_primitive()
    tampered = copy.deepcopy(primitive)
    tampered["candidates"][0]["path_length"] = float(
        tampered["candidates"][0]["path_length"]
    ) + 1.0
    tampered["content_sha256"] = geometry.sha256_json(
        {key: value for key, value in tampered.items() if key != "content_sha256"}
    )
    proof = g0.analyze_proof_fixture(source, tampered)
    assert proof["operational_valid"] is False
    assert proof["result_branch"] == statistics.INVALID_BRANCH

    guard_tampered = copy.deepcopy(primitive)
    candidate = guard_tampered["candidates"][0]
    step = candidate["steps"][-1]
    reserve_row = g0._target_internal_row(candidate["candidate_id"])
    tampered_row = next(row for row in range(8) if row != reserve_row)
    current = g0._native_array_from_primitive(
        step["current_uav_positions"]
    ).array()
    original_next = g0._native_array_from_primitive(
        step["next_uav_positions"]
    ).array()
    guarded = g0._native_array_from_primitive(
        step["guarded_executed_action"]
    ).array()
    forged_next = original_next.copy()
    inward_x = 1.0 if current[tampered_row, 0] < source.geometry.base_xy[0] else -1.0
    forged_next[tampered_row] = current[tampered_row]
    forged_next[tampered_row, 0] += inward_x
    guarded[tampered_row] = np.asarray((inward_x, 0.0, 0.0))
    step["guarded_executed_action"] = g0._NativeArrayEvidence.from_array(
        guarded
    ).to_primitive()
    step["next_uav_positions"] = g0._NativeArrayEvidence.from_array(
        forged_next
    ).to_primitive()
    step["next_uav_velocities"] = g0._NativeArrayEvidence.from_array(
        forged_next - current
    ).to_primitive()
    guard_output = step["real_guard_intervention_or_violation_output"]
    guard_output["intervention_by_uav"][tampered_row] = True
    guard_output["blocked_actions"] = sum(
        bool(item) for item in guard_output["intervention_by_uav"]
    )
    guard_output["checked_actions"] = max(
        int(guard_output["checked_actions"]),
        int(guard_output["blocked_actions"]),
    )
    candidate["trace_sha256"] = geometry.sha256_json(candidate["steps"])

    def candidate_rank(value: dict) -> tuple[float, ...]:
        return (
            float(value["hard_violation_count"]),
            float(value["gate_arrival_time"]),
            float(value["event_window_tracking_error"]),
            float(value["path_length"]),
            float(value["stage_coordinates"][0]),
            float(value["stage_coordinates"][1]),
        )

    forged_winner = min(
        guard_tampered["candidates"], key=candidate_rank
    )
    guard_tampered["selected_candidate_id"] = forged_winner["candidate_id"]
    guard_tampered["selected_rank"] = list(candidate_rank(forged_winner))
    guard_tampered["content_sha256"] = geometry.sha256_json(
        {
            key: value
            for key, value in guard_tampered.items()
            if key != "content_sha256"
        }
    )
    with pytest.raises(
        g0.G0RealizationError,
        match="isolated real-guard reconstruction|reconstructed guarded action",
    ):
        g0.validate_oracle_safety_primitive(source, guard_tampered)

    selected = next(
        candidate
        for candidate in ledger.candidates
        if candidate.candidate_id == ledger.selected_candidate_id
    )
    registered = tuple(
        g0.oracle_safety_step_from_primitive(step.to_primitive())
        for step in selected.steps
    )
    replay = tuple(
        g0.oracle_safety_step_from_primitive(step.to_primitive())
        for step in selected.steps
    )
    replay_certificate = g0.validate_oracle_behavioral_replay(
        ledger, registered, replay
    )
    assert replay_certificate.behavioral_replay_sha256 is not None
    forged_rows = list(replay)
    forged_rows[0] = replace(forged_rows[0], candidate_id="stage/forged")
    with pytest.raises(g0.G0RealizationError, match="byte-for-byte"):
        g0.validate_oracle_behavioral_replay(
            ledger, registered, tuple(forged_rows)
        )


def test_branch_aware_replay_R_NONE_requires_full_identity(
    oracle_safety_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleQualificationCertificate,
    ],
) -> None:
    source, ledger, _qualification = oracle_safety_bundle
    selected = next(
        candidate
        for candidate in ledger.candidates
        if candidate.candidate_id == ledger.selected_candidate_id
    )
    context = g0._validated_oracle_safety_context(source, ledger)
    target_evidence = g0._NativeArrayEvidence.from_array(
        g0._expected_behavioral_target_schedule(context, None)
    )
    service_evidence = g0._NativeArrayEvidence.from_array(
        np.zeros(g0.PHYSICAL_HORIZON, dtype=np.float64)
    )
    body = {
        "selected_candidate_id": ledger.selected_candidate_id,
        "return_ready_step": None,
        "steps": [step.to_primitive() for step in selected.steps],
        "target_schedule": target_evidence.to_primitive(),
        "pre_action_weakest_service": service_evidence.to_primitive(),
    }
    execution = g0.OracleBehavioralExecution(
        selected_candidate_id=ledger.selected_candidate_id,
        return_ready_step=None,
        steps=selected.steps,
        target_schedule=target_evidence,
        pre_action_weakest_service=service_evidence,
        trace_sha256=geometry.sha256_json(body),
    )
    certificate = g0.validate_oracle_branch_aware_replay(
        source, ledger, selected, execution, execution
    )
    assert certificate.return_ready_step is None
    assert certificate.replay_ok is True
    forged_targets = execution.target_schedule.array()
    selected_row = g0._selected_reserve_storage_row(
        source, ledger.selected_candidate_id
    )
    forged_targets[279, selected_row, 0] += 1.0
    forged_target_evidence = g0._NativeArrayEvidence.from_array(forged_targets)
    forged_body = {
        **body,
        "target_schedule": forged_target_evidence.to_primitive(),
    }
    forged = replace(
        execution,
        target_schedule=forged_target_evidence,
        trace_sha256=geometry.sha256_json(forged_body),
    )
    with pytest.raises(
        g0.G0RealizationError,
        match="target switch|target schedule is not bound",
    ):
        g0.validate_oracle_branch_aware_replay(
            source, ledger, selected, forged, forged
        )


def test_branch_aware_replay_uses_internal_owner_mapping_and_causal_R_273(
    oracle_behavior_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleCandidateSafetyTrace,
        g0.OracleBehavioralExecution,
    ],
) -> None:
    source, ledger, selected, execution = oracle_behavior_bundle
    assert source.event.onset == 191
    assert source.event.rejoin == 272
    assert ledger.selected_candidate_id == "stage/+1"
    owner_internal = g0._target_internal_row(source.event.owner_target)
    owner_storage = source.assignment.row_to_target.index(
        source.event.owner_target.key
    )
    assert owner_internal == 2
    assert owner_storage == 7
    independent = g0.oracle_behavioral_execution_from_primitive(
        execution.to_primitive()
    )
    certificate = g0.validate_oracle_branch_aware_replay(
        source, ledger, selected, execution, independent
    )
    assert certificate.return_ready_step == 273
    assert certificate.branchpoint_identity_ok is True
    context = execution.steps[273].pre_action_context
    assert context == g0._expected_pre_action_context(
        source,
        ledger.common_prestate,
        physical_step=273,
        selected_candidate_id=ledger.selected_candidate_id,
    )
    selected_internal = g0._target_internal_row(ledger.selected_candidate_id)
    assert np.array_equal(
        selected.steps[273].raw_candidate_action.array()[selected_internal],
        execution.steps[273].raw_candidate_action.array()[selected_internal],
    )

    stale_primitive = execution.to_primitive()
    stale_primitive["return_ready_step"] = 280
    stale = g0.oracle_behavioral_execution_from_primitive(
        _reseal_behavioral_primitive(stale_primitive)
    )
    with pytest.raises(g0.G0RealizationError, match="causally reconstructed"):
        g0.validate_oracle_branch_aware_replay(
            source, ledger, selected, stale, stale
        )


@pytest.fixture(scope="module")
def episode_zero_all_control_cell_runs() -> tuple[
    geometry.G0EpisodeSource,
    dict[tuple[g0.Control, g0.Cell], g0.EpisodeRunEvidence],
]:
    source = geometry.make_episode_source(0)
    runs = {
        (control, cell): g0.run_g0_episode(source, control=control, cell=cell)
        for control in g0.Control
        for cell in g0.Cell
    }
    return source, runs


@pytest.fixture(scope="module")
def oracle_episode_zero_runs(
    episode_zero_all_control_cell_runs: tuple[
        geometry.G0EpisodeSource,
        dict[tuple[g0.Control, g0.Cell], g0.EpisodeRunEvidence],
    ],
) -> tuple[
    geometry.G0EpisodeSource,
    dict[g0.Cell, g0.EpisodeRunEvidence],
]:
    source, runs = episode_zero_all_control_cell_runs
    return source, {
        cell: runs[(g0.Control.ORACLE, cell)] for cell in g0.Cell
    }


def test_all_six_production_runs_bind_step_zero_tracker_and_storage_permutation(
    episode_zero_all_control_cell_runs: tuple[
        geometry.G0EpisodeSource,
        dict[tuple[g0.Control, g0.Cell], g0.EpisodeRunEvidence],
    ],
) -> None:
    source, runs = episode_zero_all_control_cell_runs
    expected_identities = {
        (control, cell) for control in g0.Control for cell in g0.Cell
    }
    assert set(runs) == expected_identities
    expected_initial_positions = np.concatenate(
        (
            source.geometry.physical_xy,
            np.full(
                (g0.PHYSICAL_UAVS, 1),
                geometry.FIXED_ALTITUDE_M,
                dtype=np.float64,
            ),
        ),
        axis=1,
    )
    permutation = np.asarray((3, 1, 7, 0, 6, 2, 5, 4), dtype=np.int64)

    for identity in sorted(
        expected_identities, key=lambda item: (item[0].value, item[1].value)
    ):
        run = runs[identity]
        assert np.array_equal(run.position_trace[0], expected_initial_positions)
        expected_action = geometry.actions_toward_targets(
            physical_positions=run.position_trace[0],
            target_positions=run.target_trace[0],
            active_mask=run.active_mask_trace[0],
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        assert np.array_equal(run.raw_action_trace[0], expected_action)

        permuted_action = geometry.actions_toward_targets(
            physical_positions=run.position_trace[0, permutation],
            target_positions=run.target_trace[0, permutation],
            active_mask=run.active_mask_trace[0, permutation],
            max_speed=30.0,
            max_vertical_speed=5.0,
            time_step=1.0,
        )
        restored_action = np.empty_like(permuted_action)
        restored_action[permutation] = permuted_action
        assert np.array_equal(restored_action, run.raw_action_trace[0])


def test_production_oracle_event_and_no_event_bind_branch_evidence(
    oracle_episode_zero_runs: tuple[
        geometry.G0EpisodeSource,
        dict[g0.Cell, g0.EpisodeRunEvidence],
    ],
) -> None:
    _source, runs = oracle_episode_zero_runs
    event = runs[g0.Cell.EVENT]
    no_event = runs[g0.Cell.NO_EVENT]

    assert [(item.kind, item.physical_step) for item in event.lifecycle_events] == [
        ("LEAVE", 191),
        ("REJOIN", 272),
    ]
    assert no_event.lifecycle_events == ()
    for run, expected_return_ready in ((event, 273), (no_event, None)):
        certificate = run.controller_evidence["behavioral_replay_certificate"]
        assert certificate["return_ready_step"] == expected_return_ready
        assert certificate["replay_ok"] is True
        assert certificate["prefix_identity_ok"] is True
        assert certificate["branchpoint_identity_ok"] is True
        assert certificate["shared_ledger_identity_ok"] is True
        assert certificate["behavioral_self_replay_ok"] is True
        assert certificate["safety_guard_ok"] is True
        assert run.raw_action_trace.shape == (
            g0.PHYSICAL_HORIZON,
            g0.PHYSICAL_UAVS,
            g0.ACTION_DIM,
        )
        assert run.tracker_failures == 0
        assert run.action_support_violations == 0
        assert run.ownership_violations == 0
        assert run.oracle_qualification_failures == 0


def test_valid_oracle_certificate_is_separate_from_base_controller_evidence(
    oracle_episode_zero_runs: tuple[
        geometry.G0EpisodeSource,
        dict[g0.Cell, g0.EpisodeRunEvidence],
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, runs = oracle_episode_zero_runs
    monkeypatch.setattr(g0, "_authoritative_replay_errors", lambda *_args: ())

    for cell in g0.Cell:
        _metrics, errors = g0._validate_run_primitives(source, runs[cell])
        assert "controller_evidence" not in errors
        assert "controller_evidence_certificate" not in errors


@pytest.mark.parametrize("mutation", ("missing", "tampered"))
def test_oracle_behavioral_replay_certificate_fails_closed_separately(
    oracle_episode_zero_runs: tuple[
        geometry.G0EpisodeSource,
        dict[g0.Cell, g0.EpisodeRunEvidence],
    ],
    mutation: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, runs = oracle_episode_zero_runs
    run = runs[g0.Cell.EVENT]
    controller_evidence = copy.deepcopy(dict(run.controller_evidence))
    if mutation == "missing":
        controller_evidence.pop("behavioral_replay_certificate")
    else:
        controller_evidence["behavioral_replay_certificate"]["return_ready_step"] = None
    altered = replace(run, controller_evidence=controller_evidence)
    monkeypatch.setattr(g0, "run_g0_episode", lambda *_args, **_kwargs: run)

    errors = g0._authoritative_replay_errors(source, altered)
    assert "environment_replay_certificate" in errors
    assert "environment_replay_controller_evidence" not in errors


def test_non_oracle_injected_replay_certificate_is_not_discarded(
    oracle_episode_zero_runs: tuple[
        geometry.G0EpisodeSource,
        dict[g0.Cell, g0.EpisodeRunEvidence],
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, runs = oracle_episode_zero_runs
    reference = replace(
        runs[g0.Cell.EVENT],
        control=g0.Control.NO_REALLOCATION,
        controller_evidence={},
    )
    injected = replace(
        reference,
        controller_evidence={"behavioral_replay_certificate": {}},
    )
    monkeypatch.setattr(g0, "run_g0_episode", lambda *_args, **_kwargs: reference)

    errors = g0._authoritative_replay_errors(source, injected)
    assert "environment_replay_controller_evidence" in errors


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_lifecycle",
        "missing_service_mask",
        "tampered_service_mask",
        "missing_rng",
        "missing_channel_cursor",
        "tampered_epoch",
    ),
)
def test_branchpoint_primitives_are_required_and_independently_reconstructed(
    oracle_behavior_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleCandidateSafetyTrace,
        g0.OracleBehavioralExecution,
    ],
    mutation: str,
) -> None:
    source, ledger, selected, execution = oracle_behavior_bundle
    primitive = execution.to_primitive()
    context = primitive["steps"][273]["pre_action_context"]
    if mutation == "missing_lifecycle":
        context.pop("lifecycle_owner_to_internal")
    elif mutation == "missing_service_mask":
        context.pop("service_active_mask")
    elif mutation == "tampered_service_mask":
        context["service_active_mask"][g0._target_internal_row(source.event.owner_target)] = False
    elif mutation == "missing_rng":
        context.pop("non_controller_rng_states")
    elif mutation == "missing_channel_cursor":
        context.pop("channel_tape_cursor")
    else:
        context["event_owner_epoch"] = 0
    tampered = _reseal_behavioral_primitive(primitive)
    with pytest.raises(g0.G0RealizationError, match="branchpoint|lifecycle"):
        g0.validate_oracle_branch_aware_replay(
            source, ledger, selected, tampered, tampered
        )


def test_target_schedule_requires_recomputed_common_transducer_binding(
    oracle_behavior_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleCandidateSafetyTrace,
        g0.OracleBehavioralExecution,
    ],
) -> None:
    source, ledger, selected, execution = oracle_behavior_bundle
    attached = execution.to_primitive()
    attached["steps"] = [step.to_primitive() for step in selected.steps]
    attached = _reseal_behavioral_primitive(attached)
    with pytest.raises(
        g0.G0RealizationError,
        match="target schedule is not bound|prefix differs",
    ):
        g0.validate_oracle_branch_aware_replay(
            source, ledger, selected, attached, attached
        )


@pytest.mark.parametrize("field", ("physical_positions", "raw_action"))
def test_tampered_common_transducer_input_or_output_fails_closed(
    oracle_behavior_bundle: tuple[
        geometry.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleCandidateSafetyTrace,
        g0.OracleBehavioralExecution,
    ],
    field: str,
) -> None:
    source, ledger, selected, execution = oracle_behavior_bundle
    primitive = execution.to_primitive()
    evidence = primitive["steps"][273]["common_transducer_evidence"]
    array = g0._native_array_from_primitive(evidence[field]).array()
    array.flat[0] += 1.0 if array.dtype == np.dtype(np.float64) else 0.125
    evidence[field] = g0._NativeArrayEvidence.from_array(array).to_primitive()
    tampered = _reseal_behavioral_primitive(primitive)
    with pytest.raises(
        g0.G0RealizationError,
        match="transducer|target schedule",
    ):
        g0.validate_oracle_branch_aware_replay(
            source, ledger, selected, tampered, tampered
        )


def test_environment_leave_and_rejoin_are_pre_action_epoch_boundaries() -> None:
    source = geometry.make_episode_source(2)
    env = g0.UAVSourceIdentifiabilityEnv(source, g0.Cell.EVENT)
    try:
        env.reset()
        owner = env.event_owner_row
        old_handle = env._handles[owner]
        env.current_step = source.event.onset
        env._synchronize_service_mask(force=True)
        leave = env.consume_boundary_events()
        assert [(event.kind, event.physical_step) for event in leave] == [
            ("LEAVE", source.event.onset)
        ]
        assert env.current_rows()[owner].active is False
        assert np.array_equal(env.current_rows()[owner].velocity, np.zeros(3))
        env.current_step = source.event.rejoin
        env._synchronize_service_mask(force=True)
        rejoin = env.consume_boundary_events()
        assert [(event.kind, event.physical_step) for event in rejoin] == [
            ("REJOIN", source.event.rejoin)
        ]
        assert rejoin[0].previous_handle == old_handle
        assert rejoin[0].current_handle != old_handle
        assert env.current_rows()[owner].active is True
    finally:
        env.close()


def test_metrics_bootstrap_cp_and_first_match_boundaries() -> None:
    service = np.full(g0.PHYSICAL_HORIZON, 0.90)
    event = statistics.compute_episode_metrics(
        service,
        episode_id=0,
        control=g0.Control.SAME_INFORMATION,
        cell=g0.Cell.EVENT,
        onset=180,
        duration=80,
    )
    no_event = statistics.compute_episode_metrics(
        service,
        episode_id=0,
        control=g0.Control.SAME_INFORMATION,
        cell=g0.Cell.NO_EVENT,
        onset=180,
        duration=80,
    )
    assert event.a_control == pytest.approx(1.0) and event.b_access == 1
    assert no_event.a_control == pytest.approx(1.0) and no_event.b_access == 1
    nine = service.copy()
    nine[180:189] = np.nextafter(0.60, 0.0)
    ten = service.copy()
    ten[180:190] = np.nextafter(0.60, 0.0)
    assert statistics.compute_episode_metrics(
        nine,
        episode_id=0,
        control=g0.Control.SAME_INFORMATION,
        cell=g0.Cell.EVENT,
        onset=180,
        duration=80,
    ).c_cat == 0
    assert statistics.compute_episode_metrics(
        ten,
        episode_id=0,
        control=g0.Control.SAME_INFORMATION,
        cell=g0.Cell.EVENT,
        onset=180,
        duration=80,
    ).c_cat == 1
    plan = statistics.make_bootstrap_index_plan()
    assert plan.shape == (10_000, 128)
    assert statistics.bootstrap_bounds(np.ones(128), plan) == (1.0, 1.0, 1.0)
    assert statistics.clopper_pearson_one_sided(0)[0] == 0.0
    assert statistics.clopper_pearson_one_sided(128)[1] == 1.0
    cases = {
        statistics.INVALID_BRANCH: (False, None, object(), object()),
        statistics.INFEASIBLE_BRANCH: (True, "FAIL", object(), object()),
        statistics.ORACLE_ONLY_BRANCH: (True, "PASS", "FAIL", object()),
        statistics.NON_CAUSAL_BRANCH: (True, "PASS", "PASS", "FAIL"),
        statistics.UNDERPOWERED_BRANCH: (True, "OPEN", object(), object()),
        statistics.IDENTIFIED_BRANCH: (True, "PASS", "PASS", "PASS"),
    }
    for expected, arguments in cases.items():
        assert statistics.select_result_branch(
            valid=arguments[0],
            oracle_status=arguments[1],
            sameinfo_status=arguments[2],
            causal_status=arguments[3],
        ) == expected


def test_analysis_serializes_unread_lower_statuses_as_null() -> None:
    rows = {}
    for control in g0.Control:
        for cell in g0.Cell:
            rows[(control, cell)] = tuple(
                statistics.compute_episode_metrics(
                    np.full(g0.PHYSICAL_HORIZON, 0.90),
                    episode_id=episode_id,
                    control=control,
                    cell=cell,
                    onset=180,
                    duration=80,
                )
                for episode_id in statistics.EPISODE_IDS
            )

    def validity(episode_id: int, *, geometry_errors: int) -> statistics.EpisodeValidityRecord:
        return statistics.EpisodeValidityRecord(
            episode_id=episode_id,
            source_event_digest="source",
            source_no_event_digest="source",
            sameinfo_no_event_digest="no-event",
            no_reallocation_no_event_digest="no-event",
            geometry_support_violations=geometry_errors,
            rng_namespace_violations=0,
            pairing_mismatches=0,
            assignment_failures=0,
            tracker_failures=0,
            oracle_qualification_failures=0,
            action_support_violations=0,
            information_visibility_violations=0,
            ownership_violations=0,
            survivor_continuity_violations=0,
            permutation_mismatches=0,
            metric_reconstruction_mismatches=0,
            missing_rows=0,
            nonfinite_rows=0,
        )

    invalid = statistics._build_analysis_from_reconstructed_rows(
        rows,
        tuple(validity(episode_id, geometry_errors=1) for episode_id in statistics.EPISODE_IDS),
    )
    assert invalid["result_branch"] == statistics.INVALID_BRANCH
    assert invalid["ORACLE_STATUS"] is None
    assert invalid["SAMEINFO_STATUS"] is None
    assert invalid["CAUSAL_STATUS"] is None


def test_no_learning_optimizer_checkpoint_or_formal_authority() -> None:
    assert g0.FORMAL_EXECUTION_AUTHORIZED is False
    assert g0.LEARNING_ENABLED is False
    assert g0.OPTIMIZER_ENABLED is False
    assert g0.CHECKPOINT_ENABLED is False
    assert g0.K_SEARCH == 2
    assert g0.K_SEARCH_CEILING == 16
