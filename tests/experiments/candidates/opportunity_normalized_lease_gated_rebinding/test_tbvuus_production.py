from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import copy
import uuid

import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import contracts
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import coordinates
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import lifecycle
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import preactivity
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import production
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import serialization
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03.config import (
    Arm,
    EncounterSpec,
    FixtureCase,
    FixtureTape,
    RouteClass,
)


NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def _live() -> dict[str, str]:
    return {
        "source_manifest_sha256": SHA_A,
        "source_set_sha256": SHA_A,
        "config_sha256": SHA_A,
        "schema_sha256": SHA_A,
        "shared_guard_source_sha256": SHA_A,
        "native_source_sha256": SHA_A,
    }


def _freeze() -> dict[str, object]:
    return {
        "schema": contracts.ACCEPTED_FREEZE_SCHEMA,
        "direction_id": contracts.DIRECTION_ID,
        "stage": contracts.STAGE,
        "science_revision": contracts.SCIENCE_REVISION,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "accepted": True,
        "activity_started": False,
        "preactivity_identity_sha256": SHA_A,
        "source_manifest_sha256": SHA_A,
        "source_set_sha256": SHA_A,
        "config_sha256": SHA_A,
        "schema_sha256": SHA_A,
        "shared_guard_source_sha256": SHA_A,
        "native_source_sha256": SHA_A,
        "native_artifact_sha256": SHA_B,
    }


def _binding(experiment_id: str) -> dict[str, object]:
    proposal = contracts.coordinate_proposal()
    return {
        "schema": contracts.COORDINATE_BINDING_SCHEMA,
        "direction_id": contracts.DIRECTION_ID,
        "stage": contracts.STAGE,
        "science_revision": contracts.SCIENCE_REVISION,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "split": "HOLD",
        "proposal_sha256": proposal["proposal_sha256"],
        "coordinate_row_count": coordinates.coordinate_row_count(),
        "root_authorized": True,
        "production_words_materialized": False,
        "action_word_domain_present": False,
        "experiment_id": experiment_id,
        "source_set_sha256": SHA_A,
        "coordinate_rows_sha256": SHA_C,
        "root_authorization_sha256": SHA_D,
    }


def _lease(
    experiment_id: str,
    result_root: Path,
    freeze_sha: str,
    binding_sha: str,
    *,
    lease_id: str | None = None,
    not_after: str = "2026-08-22T00:00:00Z",
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": contracts.DIRECTION_LEASE_SCHEMA,
        "direction_id": contracts.DIRECTION_ID,
        "stage": contracts.STAGE,
        "science_revision": contracts.SCIENCE_REVISION,
        "lease_id": lease_id or str(uuid.uuid4()),
        "experiment_id": experiment_id,
        "result_root": str(result_root.resolve()),
        "preactivity_freeze_sha256": freeze_sha,
        "coordinate_binding_sha256": binding_sha,
        "source_set_sha256": SHA_A,
        "max_cpu_workers": production.MAX_CPU_WORKERS,
        "max_ram_bytes": production.MAX_RAM_BYTES,
        "expected_storage_bytes": production.EXPECTED_STORAGE_BYTES,
        "max_storage_bytes": production.MAX_STORAGE_BYTES,
        "batch_width": production.PRODUCTION_BATCH_WIDTH,
        "not_before_utc": "2026-08-21T00:00:00Z",
        "not_after_utc": not_after,
        "root_authorized": True,
        "root_authorization_sha256": SHA_D,
        "lease_scope_sha256": "",
    }
    value["lease_scope_sha256"] = contracts.document_sha256(production.lease_scope_body(value))
    return value


def _guard(*args, **kwargs):
    assert args == ("onlgr.tbvuus.r03.full_host",)
    assert kwargs == {"backend": "cpp", "batch_width": 32}
    return {
        "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
        "component": "onlgr.tbvuus.r03.full_host",
        "backend": "cpp",
        "batch_width": 32,
        "native_boundary": "fixture-test",
        "full_reset_step_cpp": True,
        "python_fallback": False,
        "native": {"artifact_sha256": SHA_B},
    }


def _admission_documents():
    experiment_id = str(uuid.uuid4())
    freeze = _freeze()
    binding = _binding(experiment_id)
    freeze_sha = contracts.document_sha256(freeze)
    binding_sha = contracts.document_sha256(binding)
    result_root = production._repo_root() / "artifacts" / f"tbvuus-fixture-{experiment_id}"
    lease = _lease(experiment_id, result_root, freeze_sha, binding_sha)
    return freeze, binding, lease, result_root


def _panel_commit_fixture():
    body = {
        "schema": contracts.PANEL_COMMIT_SCHEMA,
        "science_revision": contracts.SCIENCE_REVISION,
        "stage": contracts.STAGE,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "cell_count": 512,
        "cells": [
            {"cell": identity.as_dict(), "commit_sha256": SHA_A}
            for identity in serialization.expected_cell_identities()
        ],
        "missing_cells": [],
        "duplicate_cells": [],
        "substituted_cells": [],
        "complete": True,
    }
    return {**body, "panel_commit_sha256": contracts.document_sha256(body)}


def _write_top_receipt_fixture(root: Path):
    root.mkdir()
    experiment_id = str(uuid.uuid4())
    binding = _binding(experiment_id)
    binding_sha = contracts.document_sha256(binding)
    lease = _lease(experiment_id, root, SHA_A, binding_sha)
    lease_sha = contracts.document_sha256(lease)
    bindings = {
        "preactivity_freeze_sha256": SHA_A,
        "coordinate_binding_sha256": binding_sha,
        "lease_scope_sha256": lease["lease_scope_sha256"],
        "source_set_sha256": SHA_A,
        "config_sha256": SHA_A,
        "schema_sha256": SHA_A,
        "native_artifact_sha256": SHA_B,
    }
    backend = _guard(
        "onlgr.tbvuus.r03.full_host", backend="cpp", batch_width=32
    )
    panel = {
        "schema": contracts.PRIVATE_PANEL_SCHEMA,
        "direction_id": contracts.DIRECTION_ID,
        "stage": contracts.STAGE,
        "science_revision": contracts.SCIENCE_REVISION,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "experiment_id": experiment_id,
        "private_blinded": True,
        "partial_interpretation_allowed": False,
        "arms": list(contracts.ARMS),
        "replicates": 128,
        "controller_replicates": 512,
        "arm_encounters": 20_480,
        "physical_ticks": 1_966_080,
        "batch_width": 32,
        "bindings": bindings,
        "backend_receipt_sha256": contracts.document_sha256(backend),
    }
    identity = {
        "experiment_id": experiment_id,
        "panel_sha256": contracts.document_sha256(panel),
        "coordinate_binding_sha256": binding_sha,
        "source_set_sha256": SHA_A,
        "native_artifact_sha256": SHA_B,
    }
    intent = {
        "schema": contracts.ACTIVITY_INTENT_SCHEMA,
        "first_coordinate": asdict(production._first_coordinate()),
        **identity,
    }
    started = {
        "schema": contracts.ACTIVITY_STARTED_SCHEMA,
        "activity_started": True,
        "first_coordinate": asdict(production._first_coordinate()),
        "first_word_bits": production._word_bits(
            production._counter_word(production._first_coordinate())
        ),
        **identity,
    }
    panel_commit = _panel_commit_fixture()
    documents = {
        production.PANEL_NAME: panel,
        production.BACKEND_RECEIPT_NAME: backend,
        production.COORDINATE_BINDING_NAME: binding,
        production.ACTIVITY_INTENT_NAME: intent,
        production.ACTIVITY_STARTED_NAME: started,
        lifecycle.PANEL_COMMIT_NAME: panel_commit,
        f"{production.LEASE_RECEIPT_DIR}/{lease_sha}.json": lease,
    }
    for name, value in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contracts.canonical_json_bytes(value))
    validation = {
        "panel_commit": panel_commit,
        "uniform_bindings": bindings,
        "validation_sha256": SHA_C,
    }
    return documents, validation


@pytest.fixture(scope="module")
def native_four_arm_results():
    spec = EncounterSpec(RouteClass.SHORT, 1, 8)
    tape = FixtureTape.constant(spec)
    cases = tuple(FixtureCase(spec, tape, arm, arm.name) for arm in Arm)
    return production.run_native_batch(cases)


def _replace_tick(result, index: int, **updates):
    ticks = list(result.ticks)
    ticks[index] = replace(ticks[index], **updates)
    return replace(result, ticks=tuple(ticks))


def test_admission_gate_order_and_preflight_have_no_activity_or_files():
    freeze, binding, lease, result_root = _admission_documents()
    calls: list[str] = []

    def rows():
        calls.append("rows")
        return SHA_C

    def guard(*args, **kwargs):
        calls.append("guard")
        return _guard(*args, **kwargs)

    permit = production._admit_for_test(
        preactivity_freeze=freeze,
        coordinate_binding=binding,
        direction_lease=lease,
        result_root=result_root,
        shared_guard=guard,
        row_verifier=rows,
        identity_verifier=_live,
        now=NOW,
    )
    assert calls == ["rows", "guard"]
    assert permit._token is production._TEST_PERMIT_TOKEN
    assert not result_root.exists()
    with pytest.raises(production.ProductionAdmissionError):
        production._word(permit, production._first_coordinate())
    assert not result_root.exists()

    calls.clear()
    with pytest.raises(production.ProductionAdmissionError):
        production._admit_for_test(
            preactivity_freeze={**freeze, "accepted": False},
            coordinate_binding=binding,
            direction_lease=lease,
            result_root=result_root,
            shared_guard=guard,
            row_verifier=rows,
            identity_verifier=_live,
            now=NOW,
        )
    assert calls == []


def test_no_action_domain_and_exact_grouped_four_arm_order():
    assert "action" not in coordinates.STREAMS
    assert contracts.ACTION_WORD_DOMAIN is None
    assert coordinates.coordinate_row_count() == 7_936_000
    group = production.native_group_plan(0)[0]
    materialized = []
    for encounter in group:
        direction, lateral = production._template(encounter)
        spec = EncounterSpec(RouteClass[encounter.route_class], direction, lateral)
        materialized.append((encounter, spec, FixtureTape.constant(spec)))
    cases = production.grouped_fixture_cases(materialized)
    assert len(cases) == 32
    assert [case.arm for case in cases[:4]] == list(Arm)
    assert all(cases[index].tape is cases[0].tape for index in range(4))
    assert all(cases[index].spec is cases[0].spec for index in range(4))
    assert [case.logical_tag.rsplit("|", 1)[-1] for case in cases[:4]] == list(contracts.ARMS)


def test_real_tape_materializer_computes_each_box_muller_pair_once(monkeypatch):
    observed: list[bytes] = []

    def word(unused_permit, coordinate):
        observed.append(coordinates.encode_coordinate(coordinate))
        return 0.25 if coordinate.lane % 2 == 0 else 0.75

    monkeypatch.setattr(production, "_word", word)
    encounter = coordinates.EncounterIdentity(0, 0, "SHORT")
    production._materialize_tape(object(), encounter)
    assert len(observed) == 782
    assert len(set(observed)) == 782
    assert not any(b"action" in row for row in observed)


def test_coordinate_row_digest_has_process_local_single_enumeration_cache():
    assert hasattr(coordinates.coordinate_rows_sha256, "cache_info")
    assert coordinates.coordinate_rows_sha256.cache_info().maxsize == 1


def test_road_validator_recomputes_residual_tie_patch_install_and_effective(
    native_four_arm_results,
):
    road = native_four_arm_results[3]
    assert production._road_fit_audit_facts(contracts.ROAD_TRACK_ESTIMATE_PATCH, road).valid
    t0 = road.ticks[16]
    mutations = (
        {"road_residuals": (t0.road_residuals[0] + 1.0, *t0.road_residuals[1:])},
        {"selected_template": (t0.selected_template + 1) % 8},
        {"eta_patch": t0.eta_patch + 1.0},
        {"patch_position": (t0.patch_position[0] + 1.0, t0.patch_position[1])},
        {"estimator_position": (t0.estimator_position[0] + 1.0, t0.estimator_position[1])},
        {"effective_road_patch": not t0.effective_road_patch},
    )
    for update in mutations:
        altered = _replace_tick(road, 16, **update)
        assert not production._road_fit_audit_facts(
            contracts.ROAD_TRACK_ESTIMATE_PATCH, altered
        ).valid


def test_road_fallback_must_preserve_estimator(native_four_arm_results):
    road = native_four_arm_results[3]
    t0 = road.ticks[16]
    fallback_tick = replace(
        t0,
        road_fit_available=False,
        selected_template=-1,
        road_residuals=(float("nan"),) * 8,
        fit_t1=float("nan"),
        fit_t2=float("nan"),
        fit_z1=(float("nan"), float("nan")),
        fit_z2=(float("nan"), float("nan")),
        eta_raw=float("nan"),
        eta_patch=float("nan"),
        patch_position=t0.estimator_position_pre,
        patch_velocity=t0.estimator_velocity_pre,
        estimator_position=t0.estimator_position_pre,
        estimator_velocity=t0.estimator_velocity_pre,
        effective_road_patch=False,
        buffer_count_pre=1,
    )
    fallback = replace(
        road,
        ticks=tuple(fallback_tick if index == 16 else tick for index, tick in enumerate(road.ticks)),
        road_fit_available_count=0,
        effective_road_patch_count=0,
    )
    assert production._road_fit_audit_facts(
        contracts.ROAD_TRACK_ESTIMATE_PATCH, fallback
    ).valid
    broken = _replace_tick(
        fallback,
        16,
        estimator_position=(fallback_tick.estimator_position_pre[0] + 1.0, fallback_tick.estimator_position_pre[1]),
    )
    assert not production._road_fit_audit_facts(
        contracts.ROAD_TRACK_ESTIMATE_PATCH, broken
    ).valid


@pytest.mark.parametrize(
    "index,updates",
    (
        (16, {"tracker_energy_after": 1.0}),
        (19, {"blackout_active": False}),
        (31, {"lockout_active": False}),
        (16, {"buffer_count_post": 1}),
        (16, {"tracker_waypoint": (1.0, 2.0)}),
        (17, {"action": "ROAD-PATCH"}),
    ),
)
def test_shell_validator_rejects_energy_blackout_lockout_buffer_waypoint_and_later_action_mutations(
    native_four_arm_results, index, updates
):
    sham = native_four_arm_results[1]
    assert production._arm_transition_audit_facts(contracts.OVERHEAD_SHAM, sham).valid
    altered = _replace_tick(sham, index, **updates)
    assert not production._arm_transition_audit_facts(contracts.OVERHEAD_SHAM, altered).valid


@pytest.mark.parametrize(
    "field_name",
    ("sensor_observation", "tracking_error", "margin_tr", "raw_trial_tr", "packet_valid", "service"),
)
def test_sham_validator_rejects_unregistered_sensor_tracking_radio_trial_packet_and_q_mutations(
    native_four_arm_results, field_name
):
    never, sham = native_four_arm_results[:2]
    assert production._sham_validity_facts(
        never, sham, common_tapes_equal=True
    ).valid
    index = 20
    original = getattr(sham.ticks[index], field_name)
    if isinstance(original, tuple):
        replacement = (original[0] + 1.0, original[1])
    elif isinstance(original, bool):
        replacement = not original
    elif isinstance(original, int):
        replacement = 1 - original
    else:
        replacement = original + 1.0
    altered = _replace_tick(sham, index, **{field_name: replacement})
    assert not production._sham_validity_facts(
        never, altered, common_tapes_equal=True
    ).valid


def test_sham_validator_requires_exact_common_tape(native_four_arm_results):
    never, sham = native_four_arm_results[:2]
    assert not production._sham_validity_facts(
        never, sham, common_tapes_equal=False
    ).valid


def test_sidecar_binary_is_structural_compact_and_tamper_detected():
    identity = serialization.CellIdentity(contracts.NEVER_UPDATE, 0)
    rows = [
        {"block": block, "short_valid": 32, "long_valid": 128, "digest": SHA_A}
        for block in range(20)
    ]
    payload = serialization.encode_sidecar_rows("endpoint_audit", identity, rows)
    serialization.validate_sidecar_payload("endpoint_audit", identity, payload)
    assert len(payload) < 1024
    tampered = bytearray(payload)
    tampered[0] ^= 1
    with pytest.raises(serialization.SerializationError):
        serialization.validate_sidecar_payload("endpoint_audit", identity, bytes(tampered))


def test_resume_identifies_uncommitted_crash_window_without_replacement(tmp_path):
    root = tmp_path / "run"
    identity = serialization.CellIdentity(contracts.NEVER_UPDATE, 0)
    path = serialization.sidecar_path(root, identity, "endpoint_audit")
    path.parent.mkdir(parents=True)
    path.write_bytes(b"crash-window")
    inventory = lifecycle.resume_inventory(root)
    assert inventory.uncommitted_packets == (identity,)
    assert identity not in inventory.committed
    assert len(inventory.missing) == 511


def test_lease_renewal_changes_receipt_but_preserves_scope_and_experiment():
    freeze, binding, first, result_root = _admission_documents()
    first_scope = production.validate_direction_lease(first, now=NOW)[1]
    renewed = _lease(
        str(binding["experiment_id"]),
        result_root,
        contracts.document_sha256(freeze),
        contracts.document_sha256(binding),
        lease_id=str(uuid.uuid4()),
        not_after="2026-08-23T00:00:00Z",
    )
    renewed_scope = production.validate_direction_lease(renewed, now=NOW)[1]
    assert contracts.document_sha256(first) != contracts.document_sha256(renewed)
    assert first_scope == renewed_scope
    assert first["experiment_id"] == renewed["experiment_id"]


def test_complete_receipt_bindings_authenticate_all_retained_top_level_objects(tmp_path):
    root = tmp_path / "receipts"
    _, validation = _write_top_receipt_fixture(root)
    bindings = production._retained_receipt_bindings(
        root,
        validation,
        row_verifier=lambda: SHA_C,
        enforce_artifact_root=False,
    )
    assert bindings["rebuilt_panel_commit_sha256"] == validation["panel_commit"]["panel_commit_sha256"]
    assert bindings["validation_sha256"] == SHA_C


@pytest.mark.parametrize(
    "target",
    (
        production.PANEL_NAME,
        production.BACKEND_RECEIPT_NAME,
        production.COORDINATE_BINDING_NAME,
        production.ACTIVITY_INTENT_NAME,
        production.ACTIVITY_STARTED_NAME,
        lifecycle.PANEL_COMMIT_NAME,
        "lease",
        "cell_bindings",
    ),
)
def test_complete_receipt_bindings_reject_top_level_and_cell_drift(tmp_path, target):
    root = tmp_path / target.replace(".", "-")
    documents, validation = _write_top_receipt_fixture(root)
    changed_validation = copy.deepcopy(validation)
    if target == "cell_bindings":
        changed_validation["uniform_bindings"]["source_set_sha256"] = SHA_D
    elif target == "lease":
        lease_paths = tuple((root / production.LEASE_RECEIPT_DIR).glob("*.json"))
        lease = lifecycle.read_canonical_json(lease_paths[0])
        lease["not_after_utc"] = "2026-08-24T00:00:00Z"
        lease_paths[0].write_bytes(contracts.canonical_json_bytes(lease))
    else:
        path = root / target
        value = lifecycle.read_canonical_json(path)
        if target == production.PANEL_NAME:
            value["physical_ticks"] += 1
        elif target == production.BACKEND_RECEIPT_NAME:
            value["native"]["artifact_sha256"] = SHA_D
        elif target == production.COORDINATE_BINDING_NAME:
            value["root_authorization_sha256"] = SHA_A
        elif target == production.ACTIVITY_INTENT_NAME:
            value["panel_sha256"] = SHA_D
        elif target == production.ACTIVITY_STARTED_NAME:
            value["first_word_bits"] += 1
        else:
            value["cells"][0]["commit_sha256"] = SHA_D
            body = {key: item for key, item in value.items() if key != "panel_commit_sha256"}
            value["panel_commit_sha256"] = contracts.document_sha256(body)
        path.write_bytes(contracts.canonical_json_bytes(value))
    with pytest.raises((lifecycle.LifecycleError, production.ProductionAdmissionError)):
        production._retained_receipt_bindings(
            root,
            changed_validation,
            row_verifier=lambda: SHA_C,
            enforce_artifact_root=False,
        )


def test_result_root_path_containment_is_fail_closed(tmp_path):
    with pytest.raises(production.ProductionAdmissionError):
        production._require_result_root(tmp_path / "outside")
    accepted = production._repo_root() / "artifacts" / "fixture-contained"
    assert production._require_result_root(accepted) == accepted.resolve()


def test_source_manifest_mutation_is_detected(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("y = 2\n", encoding="utf-8")
    manifest = preactivity.build_source_manifest(tmp_path, ("a.py", "b.py"))
    assert preactivity.validate_live_source_manifest(manifest, tmp_path) == manifest
    (tmp_path / "b.py").write_text("y = 3\n", encoding="utf-8")
    with pytest.raises(preactivity.PreactivityError):
        preactivity.validate_live_source_manifest(manifest, tmp_path)


def test_production_source_has_no_python_oracle_or_scalar_rollout_fallback():
    source = Path(production.__file__).read_text(encoding="utf-8")
    assert "run_reference" not in source
    assert "from .oracle" not in source
    assert "ONLGR_TBVUUS_R03_FULL_HOST" in source
    assert "require_cpp_batched_production" in source
    assert "run_native_batch" in source
    assert "PRODUCTION_BATCH_WIDTH = 32" in source


def test_fixture_benchmark_seam_is_native_commit_resume_analysis_without_activity(tmp_path):
    root = tmp_path / "fixture-native-panel"
    result = production.run_fixture_benchmark(root)
    assert result["native_calls"] == 5
    assert result["native_call_widths"] == [32] * 5
    assert result["production_words"] is False
    assert result["complete_or_result_written"] is False
    assert result["analysis_diagnostic_keys"] == ["nonharm_diagnostics", "support_counts"]
    inventory = lifecycle.resume_inventory(root)
    assert set(inventory.committed) == {
        serialization.CellIdentity(arm, 0) for arm in contracts.ARMS
    }
    assert len(inventory.missing) == 508
    packets = [
        lifecycle.read_canonical_json(
            serialization.cell_packet_path(root, serialization.CellIdentity(arm, 0))
        )
        for arm in contracts.ARMS
    ]
    assert all(packet["aggregate"]["tick_audit_valid"] for packet in packets)
    assert all(packet["aggregate"]["arm_transition_audit_valid"] for packet in packets)
    assert all(packet["aggregate"]["road_fit_audit_valid"] for packet in packets)
    assert all(packet["aggregate"]["endpoint_audit_valid"] for packet in packets)
    aggregate_panel = {
        arm: [packet["aggregate"]] * 128
        for arm, packet in zip(contracts.ARMS, packets)
    }
    analysis = production._analyze_aggregate_panel(aggregate_panel)
    route_counts = analysis["support_counts"]["effective_road_patch_by_route"]
    assert set(route_counts) == {"SHORT", "LONG"}
    assert set(analysis["nonharm_diagnostics"]) == {
        "paired_override_interval",
        "road_hard_failures",
        "never_hard_failures",
        "road_hard_safe",
        "never_hard_safe",
        "override_ucb95_at_most_0_01",
        "road_nonharm",
    }
    assert analysis["package_validity_facts"]["road_fit"]["patch_formula_exact"] is True
    assert analysis["sham_validity_facts"]["only_registered_shell_differences"] is True
    assert lifecycle.read_canonical_json(root / "FIXTURE_BENCHMARK.json")["namespace"] != contracts.PRODUCTION_NAMESPACE
    assert not (root / production.ACTIVITY_INTENT_NAME).exists()
    assert not (root / production.ACTIVITY_STARTED_NAME).exists()
    assert not (root / lifecycle.COMPLETE_NAME).exists()
    assert not (root / lifecycle.RESULT_V2_NAME).exists()
    resumed = production.run_fixture_benchmark(root)
    assert resumed["resume_only"] is True
    assert resumed["native_calls"] == 0


def test_fixture_benchmark_refuses_artifacts_root():
    root = production._repo_root() / "artifacts" / "forbidden-fixture-benchmark"
    with pytest.raises(production.ProductionAdmissionError):
        production.run_fixture_benchmark(root)


def _release_fixture(tmp_path):
    root = tmp_path / "accepted"
    root.mkdir()
    complete_body = {
        "schema": contracts.COMPLETE_SCHEMA,
        "science_revision": contracts.SCIENCE_REVISION,
        "stage": contracts.STAGE,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "panel_commit_sha256": "3" * 64,
        "panel_sha256": "5" * 64,
        "backend_receipt_sha256": "5" * 64,
        "coordinate_binding_sha256": "5" * 64,
        "lease_scope_sha256": "5" * 64,
        "lease_receipt_inventory_sha256": "5" * 64,
        "activity_intent_sha256": "5" * 64,
        "activity_started_sha256": "5" * 64,
        "rebuilt_panel_commit_sha256": "3" * 64,
        "validation_sha256": "5" * 64,
        "cell_count": 512,
        "all_assigned_cells_complete": True,
        "atomic_package": True,
        "partial_release_allowed": False,
    }
    complete = {**complete_body, "complete_sha256": contracts.document_sha256(complete_body)}
    acceptance = lifecycle.build_cm_acceptance(
        complete_sha256=complete["complete_sha256"], acceptance_facts_sha256="4" * 64
    )
    lifecycle.atomic_write_once(root / lifecycle.COMPLETE_NAME, complete, authorized_root=root)
    lifecycle.atomic_write_once(
        root / lifecycle.CM_ACCEPTANCE_NAME, acceptance, authorized_root=root
    )
    destination = root / lifecycle.RESULT_V2_NAME
    authorization_path = root / lifecycle.RESULT_V2_RELEASE_AUTHORIZATION_NAME
    em_receipt_path = root / lifecycle.PORTFOLIO_EM_SEQUENCING_RECEIPT_NAME
    em_receipt = {
        "schema": contracts.PORTFOLIO_EM_SEQUENCING_RECEIPT_SCHEMA,
        "serializer": contracts.SERIALIZER_ID,
        "science_revision": contracts.SCIENCE_REVISION,
        "stage": contracts.STAGE,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "result_root": str(root.resolve()),
        "result_destination_path": str(destination.resolve()),
        "complete_sha256": complete["complete_sha256"],
        "cm_acceptance_sha256": acceptance["cm_acceptance_sha256"],
        "receipt_id": "00000000-0000-4000-8000-000000000020",
        "portfolio_em_actor": lifecycle.PORTFOLIO_EM_ACTOR,
        "result_blind_accepted_complete_intake": True,
        "legacy_result_used": False,
        "root_release_authority_granted": False,
    }
    em_receipt_path.write_bytes(contracts.canonical_json_bytes(em_receipt))
    em_receipt_sha = hashlib.sha256(em_receipt_path.read_bytes()).hexdigest()
    authorization = {
        "schema": contracts.RESULT_RELEASE_AUTHORIZATION_SCHEMA,
        "science_revision": contracts.SCIENCE_REVISION,
        "stage": contracts.STAGE,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "result_root": str(root.resolve()),
        "result_destination_path": str(destination.resolve()),
        "complete_sha256": complete["complete_sha256"],
        "cm_acceptance_sha256": acceptance["cm_acceptance_sha256"],
        "authorization_id": "00000000-0000-4000-8000-000000000003",
        "operator": lifecycle.RELEASE_OPERATOR,
        "release_authorization_path": str(authorization_path.resolve()),
        "portfolio_em_sequencing_receipt_path": str(em_receipt_path.resolve()),
        "portfolio_em_sequencing_receipt_sha256": em_receipt_sha,
        "result_release_authorized": True,
    }
    return root, destination, authorization_path, em_receipt_path, complete, acceptance, authorization


def _release_for_test(paths, *, package_validator, analyzer):
    root = paths[0]
    return production._release_result_for_test(
        root=root,
        package_validator=package_validator,
        analyzer=analyzer,
    )


def test_public_release_api_and_analyze_cli_have_no_result_root_selector(monkeypatch):
    import inspect

    assert list(inspect.signature(production.release_result).parameters) == []
    assert production.build_parser().parse_args(["analyze"]).command == "analyze"
    with pytest.raises(SystemExit):
        production.build_parser().parse_args(["analyze", "--result-root", "elsewhere"])
    called = []
    monkeypatch.setattr(production, "release_result", lambda: called.append(True) or {"ok": True})
    assert production.main(["analyze"]) == 0
    assert called == [True]
    command = production.future_resource_request()["commands"][
        "analyze_after_root_release_authorization"
    ]
    assert command[-1] == "analyze"
    assert "--result-root" not in command


def test_canonical_result_v2_paths_are_frozen():
    expected_root = Path(
        "C:/Projects/HMASD/artifacts/onlgr_tbvuus_r03_full_panel_20260821"
    ).resolve()
    assert production.CANONICAL_RESULT_ROOT == expected_root
    assert production.CANONICAL_RESULT_V2_PATH == expected_root / "RESULT_V2.json"
    assert production.CANONICAL_RESULT_V2_RELEASE_AUTHORIZATION_PATH == (
        expected_root / "RESULT_V2_RELEASE_AUTHORIZATION.json"
    )
    assert production.CANONICAL_PORTFOLIO_EM_SEQUENCING_RECEIPT_PATH == (
        expected_root / "PORTFOLIO_EM_RESULT_INTAKE_SEQUENCING_RECEIPT.json"
    )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda token: {**token, "operator": "/root/cm"},
        lambda token: {**token, "complete_sha256": SHA_D},
        lambda token: {**token, "cm_acceptance_sha256": SHA_D},
        lambda token: {**token, "portfolio_em_sequencing_receipt_sha256": "D" * 64},
        lambda token: {**token, "result_release_authorized": False},
    ),
)
def test_absent_or_wrong_result_v2_token_fails_before_analyzer(tmp_path, mutation):
    paths = _release_fixture(tmp_path)
    (paths[0] / "RESULT.json").write_bytes(b"opaque legacy fallback bait\x00\xff")
    calls = []
    with pytest.raises(FileNotFoundError):
        _release_for_test(
            paths,
            package_validator=lambda root: {"stable": True},
            analyzer=lambda root: calls.append(root) or {"branch": "UNREACHABLE"},
        )
    assert calls == []
    authorization_path = paths[2]
    authorization_path.write_bytes(
        contracts.canonical_json_bytes(mutation(paths[-1]))
    )
    with pytest.raises(lifecycle.LifecycleError):
        _release_for_test(
            paths,
            package_validator=lambda root: {"stable": True},
            analyzer=lambda root: calls.append(root) or {"branch": "UNREACHABLE"},
        )
    assert calls == []


def test_noncanonical_or_path_tampered_token_fails_before_analyzer(tmp_path):
    paths = _release_fixture(tmp_path)
    calls = []
    paths[2].write_text(json.dumps(paths[-1], indent=2), encoding="utf-8")
    with pytest.raises(lifecycle.LifecycleError, match="canonical JSON"):
        _release_for_test(
            paths,
            package_validator=lambda root: {"stable": True},
            analyzer=lambda root: calls.append(root) or {"branch": "UNREACHABLE"},
        )
    assert calls == []


def test_valid_result_v2_is_atomic_and_legacy_result_is_opaque(tmp_path, monkeypatch):
    paths = _release_fixture(tmp_path)
    root, destination, authorization_path, _, _, _, authorization = paths
    opaque_legacy = root / "RESULT.json"
    opaque_bytes = b"opaque legacy bytes; not JSON\x00\xff"
    opaque_legacy.write_bytes(opaque_bytes)
    authorization_path.write_bytes(contracts.canonical_json_bytes(authorization))
    observed_reads = []
    production_reader = production.read_canonical_json
    lifecycle_reader = lifecycle.read_canonical_json

    def observe_production(path):
        observed_reads.append(Path(path).resolve())
        return production_reader(path)

    def observe_lifecycle(path):
        observed_reads.append(Path(path).resolve())
        return lifecycle_reader(path)

    monkeypatch.setattr(production, "read_canonical_json", observe_production)
    monkeypatch.setattr(lifecycle, "read_canonical_json", observe_lifecycle)
    result = _release_for_test(
        paths,
        package_validator=lambda root: {"stable": True},
        analyzer=lambda root: {"branch": "VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS"},
    )
    assert destination.read_bytes() == contracts.canonical_json_bytes(result)
    assert opaque_legacy.read_bytes() == opaque_bytes
    assert opaque_legacy.resolve() not in observed_reads
    assert '"RESULT.json"' not in Path(production.__file__).read_text(encoding="utf-8")
    assert result["release_receipt"]["release_authorization_sha256"] == (
        contracts.document_sha256(authorization)
    )
    with pytest.raises(FileExistsError):
        _release_for_test(
            paths,
            package_validator=lambda root: {"stable": True},
            analyzer=lambda root: pytest.fail("analyzer must not run on existing RESULT_V2"),
        )


def test_token_tamper_during_analysis_prevents_result_v2_publication(tmp_path):
    paths = _release_fixture(tmp_path)
    authorization_path = paths[2]
    authorization_path.write_bytes(contracts.canonical_json_bytes(paths[-1]))

    def analyzer(_root):
        authorization_path.write_bytes(
            contracts.canonical_json_bytes({**paths[-1], "operator": "/root/cm"})
        )
        return {"branch": "UNREACHABLE"}

    with pytest.raises(lifecycle.LifecycleError, match="changed during analysis"):
        _release_for_test(
            paths,
            package_validator=lambda root: {"stable": True},
            analyzer=analyzer,
        )
    assert not paths[1].exists()


def test_installed_receipt_change_during_analysis_prevents_result_v2_publication(tmp_path):
    paths = _release_fixture(tmp_path)
    authorization_path = paths[2]
    receipt_path = paths[3]
    authorization_path.write_bytes(contracts.canonical_json_bytes(paths[-1]))

    def analyzer(_root):
        receipt = lifecycle.read_canonical_json(receipt_path)
        receipt_path.write_bytes(
            contracts.canonical_json_bytes(
                {**receipt, "receipt_id": "00000000-0000-4000-8000-000000000021"}
            )
        )
        return {"branch": "UNREACHABLE"}

    with pytest.raises(lifecycle.LifecycleError):
        _release_for_test(
            paths,
            package_validator=lambda root: {"stable": True},
            analyzer=analyzer,
        )
    assert not paths[1].exists()
