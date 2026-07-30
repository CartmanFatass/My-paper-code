from __future__ import annotations

from dataclasses import replace
import copy
import math

import numpy as np
import pytest

from ha_ctse_process import uav_source_identifiability_g0 as g0


@pytest.fixture(scope="module")
def oracle_safety_bundle() -> tuple[
    g0.G0EpisodeSource,
    g0.OracleSafetyLedger,
    g0.OracleQualificationCertificate,
]:
    source = g0.make_episode_source(0)
    ledger = g0.build_oracle_safety_ledger(source)
    qualification = g0.oracle_qualification_from_safety_ledger(source, ledger)
    return source, ledger, qualification


def _rows(
    source: g0.G0EpisodeSource,
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
                position=np.asarray([xy[0], xy[1], g0.FIXED_ALTITUDE_M]),
                velocity=np.zeros(3),
                active=active,
                service_available=active,
            )
        )
    return tuple(rows)


def _information(
    source: g0.G0EpisodeSource,
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
    source = g0.make_episode_source(17)
    duplicate = g0.make_episode_source(17)
    assert source.to_primitive() == duplicate.to_primitive()
    geometry = source.geometry
    assert np.array_equal(geometry.base_xy, [4000.0, 4000.0])
    assert geometry.target_labels == g0.TARGET_LABELS
    assert tuple(source.assignment.primary_count_by_hotspot) == (2, 2, 2)
    assert source.assignment.staging_count == 2
    assert sorted(geometry.slot_to_target.tolist()) == list(range(8))
    assert np.array_equal(
        geometry.physical_xy,
        geometry.target_owned_initial_xy[geometry.slot_to_target],
    )
    assert source.event.owner_target.kind is g0.TargetKind.PRIMARY
    assert 180 <= source.event.onset <= 220
    assert 80 <= source.event.duration <= 100
    assert len({g0.channel_seed_word(17, step) for step in range(4)}) == 4

    with pytest.raises(g0.G0RealizationError, match="registered episode RNG"):
        replace(geometry, phi=np.nextafter(geometry.phi, math.inf))
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
        g0.make_episode_source(17, map_width=7999.0)
    with pytest.raises(g0.G0RealizationError, match="rectangular-map center"):
        g0.make_episode_source(17, base_xy=(3999.0, 4000.0))


def test_anonymous_assignment_tie_law_and_duplicate_rows_fail_closed() -> None:
    source = g0.make_episode_source(3)
    rows = np.concatenate((source.geometry.physical_xy, np.zeros((8, 2))), axis=1)
    certificate = g0.minimum_cost_target_assignment(
        physical_rows=rows,
        target_xy=source.geometry.target_xy,
    )
    order = np.asarray((3, 0, 7, 2, 6, 1, 5, 4))
    permuted = g0.minimum_cost_target_assignment(
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
        g0.minimum_cost_target_assignment(
            physical_rows=duplicate,
            target_xy=source.geometry.target_xy,
        )


def test_accepted_g1_tracker_and_shared_correction_are_qualified() -> None:
    source = g0.make_episode_source(0)
    physical = np.concatenate(
        (source.geometry.physical_xy, np.full((8, 1), g0.FIXED_ALTITUDE_M)),
        axis=1,
    )
    targets = np.stack(
        [
            np.concatenate(
                (
                    source.geometry.coordinate(g0.TargetLabel.parse(label)),
                    [g0.FIXED_ALTITUDE_M],
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
    source = g0.make_episode_source(4)
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
        owner_at_primary=True,
    )
    gate_targets = controller.target_map(
        _information(source, rejoin_rows, weakest_service=1.0),
        physical_step=source.event.rejoin,
    )
    assert np.array_equal(
        gate_targets[selected][:2], source.geometry.gate(source.event.owner_target)
    )
    controller.target_map(
        _information(source, rejoin_rows, weakest_service=1.0),
        physical_step=source.event.rejoin + 1,
    )
    returned = controller.target_map(
        _information(source, rejoin_rows, weakest_service=0.90),
        physical_step=source.event.rejoin + 2,
    )
    stage = g0.TargetLabel.parse(
        next(
            label
            for handle, label in controller.original_ownership.items()
            if handle == selected
        ).key
    )
    assert stage.kind is g0.TargetKind.STAGE
    assert np.array_equal(returned[selected][:2], source.geometry.coordinate(stage))


def test_no_reallocation_freezes_targets_and_no_event_maps_match() -> None:
    source = g0.make_episode_source(6)
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
        g0.G0EpisodeSource,
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
    assert all(row.physical_steps_advanced == 500 for row in certificate.candidates)
    assert all(row.hard_violation_count == 0 for row in certificate.candidates)
    assert certificate.selected_rank == min(row.rank for row in certificate.candidates)
    forged = replace(certificate, selected_reserve_target="stage/+1")
    if forged.to_primitive() != certificate.to_primitive():
        with pytest.raises(g0.G0RealizationError, match="forged"):
            g0.validate_oracle_qualification(
                source, forged, safety_ledger=ledger
            )


def test_registered_oracle_safety_ledger_is_exact_and_service_blind(
    oracle_safety_bundle: tuple[
        g0.G0EpisodeSource,
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


def test_oracle_safety_tamper_fails_closed_and_replay_is_two_trace_exact(
    oracle_safety_bundle: tuple[
        g0.G0EpisodeSource,
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
    tampered["content_sha256"] = g0.sha256_json(
        {key: value for key, value in tampered.items() if key != "content_sha256"}
    )
    proof = g0.analyze_proof_fixture(source, tampered)
    assert proof["operational_valid"] is False
    assert proof["result_branch"] == g0.INVALID_BRANCH

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
        g0.G0EpisodeSource,
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
    target_evidence = g0._NativeArrayEvidence.from_array(
        g0._expected_behavioral_target_schedule(source, ledger, None)
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
        trace_sha256=g0.sha256_json(body),
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
        trace_sha256=g0.sha256_json(forged_body),
    )
    with pytest.raises(g0.G0RealizationError, match="target switch"):
        g0.validate_oracle_branch_aware_replay(
            source, ledger, selected, forged, forged
        )


def test_branch_aware_replay_uses_internal_owner_mapping_and_causal_R_273(
    oracle_safety_bundle: tuple[
        g0.G0EpisodeSource,
        g0.OracleSafetyLedger,
        g0.OracleQualificationCertificate,
    ],
) -> None:
    source, ledger, _qualification = oracle_safety_bundle
    assert source.event.onset == 191
    assert source.event.rejoin == 272
    assert ledger.selected_candidate_id == "stage/+1"
    owner_internal = g0._target_internal_row(source.event.owner_target)
    owner_storage = source.assignment.row_to_target.index(
        source.event.owner_target.key
    )
    assert owner_internal == 2
    assert owner_storage == 7

    selected = next(
        candidate
        for candidate in ledger.candidates
        if candidate.candidate_id == ledger.selected_candidate_id
    )
    service = np.zeros(g0.PHYSICAL_HORIZON, dtype=np.float64)
    service[273:] = 1.0
    service_evidence = g0._NativeArrayEvidence.from_array(service)
    target_evidence = g0._NativeArrayEvidence.from_array(
        g0._expected_behavioral_target_schedule(source, ledger, 273)
    )
    # The target switches before step-273 action construction, while the
    # frozen contract explicitly permits a coincident raw-action byte row.
    behavior_steps = list(selected.steps)
    body = {
        "selected_candidate_id": ledger.selected_candidate_id,
        "return_ready_step": 273,
        "steps": [step.to_primitive() for step in behavior_steps],
        "target_schedule": target_evidence.to_primitive(),
        "pre_action_weakest_service": service_evidence.to_primitive(),
    }
    execution = g0.OracleBehavioralExecution(
        selected_candidate_id=ledger.selected_candidate_id,
        return_ready_step=273,
        steps=tuple(behavior_steps),
        target_schedule=target_evidence,
        pre_action_weakest_service=service_evidence,
        trace_sha256=g0.sha256_json(body),
    )
    certificate = g0.validate_oracle_branch_aware_replay(
        source, ledger, selected, execution, execution
    )
    assert certificate.return_ready_step == 273
    assert certificate.branchpoint_identity_ok is True

    stale_body = {**body, "return_ready_step": 280}
    stale = replace(
        execution,
        return_ready_step=280,
        trace_sha256=g0.sha256_json(stale_body),
    )
    with pytest.raises(g0.G0RealizationError, match="causally reconstructed"):
        g0.validate_oracle_branch_aware_replay(
            source, ledger, selected, stale, stale
        )


def test_environment_leave_and_rejoin_are_pre_action_epoch_boundaries() -> None:
    source = g0.make_episode_source(2)
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
    event = g0.compute_episode_metrics(
        service,
        episode_id=0,
        control=g0.Control.SAME_INFORMATION,
        cell=g0.Cell.EVENT,
        onset=180,
        duration=80,
    )
    no_event = g0.compute_episode_metrics(
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
    assert g0.compute_episode_metrics(
        nine,
        episode_id=0,
        control=g0.Control.SAME_INFORMATION,
        cell=g0.Cell.EVENT,
        onset=180,
        duration=80,
    ).c_cat == 0
    assert g0.compute_episode_metrics(
        ten,
        episode_id=0,
        control=g0.Control.SAME_INFORMATION,
        cell=g0.Cell.EVENT,
        onset=180,
        duration=80,
    ).c_cat == 1
    plan = g0.make_bootstrap_index_plan()
    assert plan.shape == (10_000, 128)
    assert g0.bootstrap_bounds(np.ones(128), plan) == (1.0, 1.0, 1.0)
    assert g0.clopper_pearson_one_sided(0)[0] == 0.0
    assert g0.clopper_pearson_one_sided(128)[1] == 1.0
    cases = {
        g0.INVALID_BRANCH: (False, "OPEN", "OPEN", "OPEN"),
        g0.INFEASIBLE_BRANCH: (True, "FAIL", "OPEN", "OPEN"),
        g0.ORACLE_ONLY_BRANCH: (True, "PASS", "FAIL", "OPEN"),
        g0.NON_CAUSAL_BRANCH: (True, "PASS", "PASS", "FAIL"),
        g0.UNDERPOWERED_BRANCH: (True, "PASS", "PASS", "OPEN"),
        g0.IDENTIFIED_BRANCH: (True, "PASS", "PASS", "PASS"),
    }
    for expected, arguments in cases.items():
        assert g0.select_result_branch(
            valid=arguments[0],
            oracle_status=arguments[1],
            sameinfo_status=arguments[2],
            causal_status=arguments[3],
        ) == expected


def test_no_learning_optimizer_checkpoint_or_formal_authority() -> None:
    assert g0.FORMAL_EXECUTION_AUTHORIZED is False
    assert g0.LEARNING_ENABLED is False
    assert g0.OPTIMIZER_ENABLED is False
    assert g0.CHECKPOINT_ENABLED is False
    assert g0.K_SEARCH == 2
    assert g0.K_SEARCH_CEILING == 16
