from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fractions import Fraction
import inspect
from pathlib import Path

import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import controllers
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import production
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import serialization


SHA = "a" * 64


def freeze() -> dict[str, object]:
    return {
        "schema": production.FREEZE_SCHEMA,
        "direction_id": production.DIRECTION_ID,
        "stage": production.STAGE,
        "card_revision": production.CARD_REVISION,
        "host": production.HOST_ID,
        "accepted": True,
        "activity_started": False,
        "preactivity_identity_sha256": "b" * 64,
        "technical_acceptance_sha256": "c" * 64,
        "source_set_sha256": "1" * 64,
        "config_sha256": "2" * 64,
        "schema_sha256": "3" * 64,
        "shared_guard_source_sha256": "4" * 64,
    }


def binding() -> dict[str, object]:
    proposal = production.coordinate_binding_proposal()
    return {
        "schema": production.BINDING_SCHEMA,
        "direction_id": production.DIRECTION_ID,
        "stage": production.STAGE,
        "card_revision": production.CARD_REVISION,
        "host": production.HOST_ID,
        "proposal_id": production.COORDINATE_PROPOSAL_ID,
        "proposal_schema_sha256": proposal["proposal_schema_sha256"],
        "namespace": production.PRODUCTION_NAMESPACE,
        "root_authorized": True,
        "complete_required_row_set": True,
        "production_words_materialized": False,
        "controller_identity_in_disturbance_key": False,
        "coordinate_rows_sha256": "d" * 64,
        "root_authorization_sha256": "e" * 64,
    }


def lease(root: Path) -> dict[str, object]:
    return {
        "schema": production.LEASE_SCHEMA,
        "direction_id": production.DIRECTION_ID,
        "stage": production.STAGE,
        "card_revision": production.CARD_REVISION,
        "host": production.HOST_ID,
        "authorized": True,
        "result_root": str(root.resolve()),
        "calibration_controller_replicates": 9216,
        "maximum_held_out_controller_replicates": 640,
        "total_controller_replicates": 9856,
        "total_physical_ticks": 37_847_040,
        "calibration_maps": 192,
        "calibration_replicates": 48,
        "held_out_replicates": 128,
        "maximum_unique_held_out_maps": 5,
        "batch_only": True,
        "backend": "cpp",
        "python_fallback": False,
        "cpu_workers": 8,
        "ram_bytes": 16 * 1024**3,
        "storage_bytes": 4 * 1024**3,
        "not_after_utc": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
        "lease_token_sha256": "f" * 64,
    }


def backend_receipt(component: str, width: int) -> dict[str, object]:
    return {
        "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
        "component": component,
        "backend": "cpp",
        "batch_width": width,
        "native_boundary": "full-host",
        "full_reset_step_cpp": True,
        "python_fallback": False,
        "native": {"artifact": "synthetic-test-only", "artifact_sha256": SHA},
    }


def admit(root: Path) -> production.ProductionPermit:
    return production._admit_production_fixture(
        preactivity_freeze=freeze(),
        coordinate_binding=binding(),
        direction_lease=lease(root),
        result_root=root,
        shared_guard=lambda component, backend, batch_width, build_root: backend_receipt(
            component, batch_width
        ),
        coordinate_row_verifier=lambda document: str(document["coordinate_rows_sha256"]),
        live_identity_verifier=lambda: {key: str(freeze()[key]) for key in ("source_set_sha256", "config_sha256", "schema_sha256", "preactivity_identity_sha256", "shared_guard_source_sha256")},
    )


def encounter(scored: int) -> dict[str, object]:
    return {
        "valid_ticks": scored // 2,
        "scored_ticks": scored,
        "tracking_valid_ticks": scored,
        "packet_valid_ticks": scored // 2,
        "raw_link_success_tr": scored,
        "raw_link_success_rb": scored,
        "blackout_ticks": 4,
        "lockout_ticks": 16,
        "voluntary_updates": 1,
        "voluntary_keeps": 2,
        "opportunity_rows": 3,
        "safety_overrides": 0,
        "override_causes": {"terrain": 0, "geofence": 0, "separation": 0},
        "failures": {
            "terrain_penetrations": 0,
            "geofence_exits": 0,
            "separation_breaches": 0,
            "no_safe_control": 0,
            "no_planner_solution": 0,
            "battery_exhaustions": 0,
            "numerical_faults": 0,
        },
        "tracker_energy_final": 30_000.0,
        "relay_energy_final": 35_000.0,
        "update_energy_joules_per_uav": 400,
    }


def blocks(replicate: int) -> list[dict[str, object]]:
    return [
        {
            "block": block,
            "template": (replicate + 3 * block) % 4,
            "encounter_order": list(
                ("SHORT", "LONG") if (replicate + block) % 2 == 0 else ("LONG", "SHORT")
            ),
            "SHORT": encounter(32),
            "LONG": encounter(128),
        }
        for block in range(20)
    ]


def cell_bindings() -> dict[str, str]:
    return {
        "preactivity_freeze_sha256": "1" * 64,
        "coordinate_binding_sha256": "2" * 64,
        "lease_scope_sha256": "3" * 64,
        "backend_receipt_sha256": "4" * 64,
        "source_set_sha256": "5" * 64,
        "config_sha256": "6" * 64,
        "schema_sha256": "7" * 64,
    }


def test_batch_plans_have_exact_batch_only_counts_and_frozen_order():
    cal, hold = production.batch_plan("CAL"), production.batch_plan("HOLD")
    assert len(cal) == 48 * 20 * 2 == 1920
    assert len(hold) == 128 * 20 * 2 == 5120
    assert cal[0] == production.BatchIdentity("CAL", 0, 0, "SHORT")
    assert cal[2] == production.BatchIdentity("CAL", 0, 1, "LONG")
    assert cal[3] == production.BatchIdentity("CAL", 0, 1, "SHORT")
    assert all(item.template == (item.replicate + 3 * item.block) % 4 for item in cal)
    source = inspect.getsource(production)
    assert "Headland90Host(" not in source
    assert "run_native_batch(fixtures)" in source


def test_formal_command_is_exact_batch_only_and_does_not_execute_during_parse(tmp_path: Path):
    arguments = production.build_parser().parse_args([
        "formal-run",
        "--preactivity-freeze", str(tmp_path / "freeze.json"),
        "--coordinate-binding", str(tmp_path / "binding.json"),
        "--lease", str(tmp_path / "lease.json"),
        "--result-root", str(tmp_path / "panel"),
        "--source-set-sha256", "1" * 64,
        "--config-sha256", "2" * 64,
        "--schema-sha256", "3" * 64,
    ])
    assert arguments.command == "formal-run"
    assert arguments.resume is False


@pytest.mark.parametrize("gate", ["freeze", "binding", "lease"])
def test_admission_rejects_before_shared_guard_and_before_any_root_creation(tmp_path: Path, gate: str):
    root = tmp_path / "panel"
    documents = {"freeze": freeze(), "binding": binding(), "lease": lease(root)}
    documents[gate] = dict(documents[gate])
    documents[gate]["host"] = "wrong"
    called = False

    def guard(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("shared guard must not run after an earlier rejected gate")

    with pytest.raises(production.ProductionAdmissionError):
        production._admit_production_fixture(
            preactivity_freeze=documents["freeze"],
            coordinate_binding=documents["binding"],
            direction_lease=documents["lease"],
            result_root=root,
            shared_guard=guard,
            live_identity_verifier=lambda: {key: str(freeze()[key]) for key in ("source_set_sha256", "config_sha256", "schema_sha256", "preactivity_identity_sha256", "shared_guard_source_sha256")},
            coordinate_row_verifier=lambda document: str(document["coordinate_rows_sha256"]),
        )
    assert not called and not root.exists()


def test_admission_requires_exact_full_host_receipt_and_never_creates_root(tmp_path: Path):
    root = tmp_path / "panel"
    with pytest.raises(production.ProductionAdmissionError, match="full-host"):
        production._admit_production_fixture(
            preactivity_freeze=freeze(),
            coordinate_binding=binding(),
            direction_lease=lease(root),
            result_root=root,
            shared_guard=lambda component, **kwargs: backend_receipt("wrong", 192),
            coordinate_row_verifier=lambda document: str(document["coordinate_rows_sha256"]),
            live_identity_verifier=lambda: {key: str(freeze()[key]) for key in ("source_set_sha256", "config_sha256", "schema_sha256", "preactivity_identity_sha256", "shared_guard_source_sha256")},
        )
    assert not root.exists()


def test_public_admission_has_fixed_dependencies_and_fixture_token_cannot_draw(tmp_path: Path):
    parameters = inspect.signature(production.admit_production).parameters
    assert not {"shared_guard", "coordinate_row_verifier", "live_identity_verifier", "now"} & set(parameters)
    permit = admit(tmp_path / "panel")
    coordinate = production._coordinate(production.BatchIdentity("CAL", 0, 0, "SHORT"), tick=0, stream="action", lane=0)
    with pytest.raises(production.ProductionAdmissionError, match="fixture admission"):
        production._word(permit, coordinate)
    with pytest.raises(production.ProductionAdmissionError, match="fixture admission"):
        production.run_full_panel(permit, source_set_sha256="1"*64, config_sha256="2"*64, schema_sha256="3"*64)


def test_resume_accepts_same_scope_lease_renewal_and_retains_both_receipts(tmp_path: Path):
    root = tmp_path / "panel"
    first = admit(root)
    production.initialize_private_panel(first, source_set_sha256="1"*64, config_sha256="2"*64, schema_sha256="3"*64)
    renewed = lease(root)
    renewed["lease_token_sha256"] = "9" * 64
    renewed["cpu_workers"] = 4
    second = production._admit_production_fixture(
        preactivity_freeze=freeze(), coordinate_binding=binding(), direction_lease=renewed,
        result_root=root, resume=True,
        shared_guard=lambda component, **kwargs: backend_receipt(component, 192),
        coordinate_row_verifier=lambda document: str(document["coordinate_rows_sha256"]),
        live_identity_verifier=lambda: {key:str(freeze()[key]) for key in ("source_set_sha256","config_sha256","schema_sha256","preactivity_identity_sha256","shared_guard_source_sha256")},
    )
    production.initialize_private_panel(second, source_set_sha256="1"*64, config_sha256="2"*64, schema_sha256="3"*64)
    assert first.lease_scope_sha256 == second.lease_scope_sha256
    assert len(tuple((root / "lease-receipts").glob("*.json"))) == 2


def test_resume_frontier_excludes_already_committed_same_coordinate_cell(tmp_path: Path):
    controller_set = controllers.CONTROLLER_REGISTRY[:3]
    identity = serialization.CellIdentity("CAL", "theta-001", 7)
    serialization.atomic_write_once(
        serialization.cell_path(tmp_path, identity), {"committed": True}, authorized_root=tmp_path,
    )
    serialization.atomic_write_bytes(
        serialization.sidecar_path(tmp_path, identity, "opportunity"), b"committed", authorized_root=tmp_path,
    )
    serialization.atomic_write_once(production._cell_commit_path(tmp_path,identity),{"committed":True},authorized_root=tmp_path)
    assert production._pending_controller_indices(tmp_path, "CAL", 7, controller_set, set()) == (0, 2)


def test_resume_frontier_replays_cell_when_required_trace_was_not_committed(tmp_path: Path):
    controller_set = controllers.CONTROLLER_REGISTRY[:1]
    identity = serialization.CellIdentity("CAL", "theta-000", 0)
    serialization.atomic_write_once(serialization.cell_path(tmp_path, identity), {"committed":True}, authorized_root=tmp_path)
    serialization.atomic_write_bytes(serialization.sidecar_path(tmp_path, identity, "opportunity"), b"committed", authorized_root=tmp_path)
    retained = {("theta-000",0)}
    assert production._pending_controller_indices(tmp_path,"CAL",0,controller_set,retained) == (0,)
    trace_path = tmp_path / "private-traces" / "CAL" / "theta-000" / "replicate-000.json"
    serialization.atomic_write_once(trace_path,{"committed":True},authorized_root=tmp_path)
    serialization.atomic_write_once(production._cell_commit_path(tmp_path,identity),{"committed":True},authorized_root=tmp_path)
    assert production._pending_controller_indices(tmp_path,"CAL",0,controller_set,retained) == ()
    source = inspect.getsource(production._run_split)
    assert source.index("_write_trace(root, identity, traces[index])") < source.index("write_cell_packet(root, packet)")
    assert source.index("write_cell_packet(root, packet)") < source.index("_seal_cell_transaction")


def test_cross_ledger_requires_exact_ordered_unique_sequence():
    expected = ((0,0,16,1),(0,0,17,2))
    production._validate_cross_rows(expected, expected)
    with pytest.raises(serialization.SerializationError, match="exact state replay"):
        production._validate_cross_rows(((0,0,16,1),(0,0,16,1)), expected)


def test_no_ungated_coordinate_uniform_or_fixture_replay_authority(tmp_path: Path):
    assert not hasattr(production, "_coordinate_uniform")
    with pytest.raises((FileNotFoundError, production.ProductionAdmissionError)):
        production._post_activity_replay_authority(tmp_path)


def test_activity_start_is_committed_only_by_first_word_boundary():
    run_source = inspect.getsource(production.run_full_panel)
    word_source = inspect.getsource(production._word)
    assert "_write_activity_intent(permit)" in run_source
    assert "ACTIVITY_STARTED.json" not in run_source
    assert "_commit_first_word" in word_source
    assert "_permit_word_value" in inspect.getsource(production._commit_first_word)


def test_exact_override_causes_detect_segment_and_in_tick_crossings():
    terrain = production._exact_override_causes((-110.0,0.0),(300.0,200.0),(880.0,0.0),(0.0,0.0))
    assert terrain == {"terrain":True,"geofence":False,"separation":False}
    crossing = production._exact_override_causes((-20.0,200.0),(20.0,200.0),(160.0,0.0),(-160.0,0.0))
    assert crossing["separation"] is True
    assert crossing["terrain"] is False and crossing["geofence"] is False


def test_native_fixture_encounter_summary_has_complete_exact_schema():
    spec = production.EncounterSpec(production.RouteClass.SHORT, 1, 8)
    tape = production.FixtureTape.constant(spec, normal=0.0, uniform=0.5)
    result = production.run_native_batch(((spec,tape,controllers.lookup_controller(0,0),"fixture-summary"),))[0]
    summary = production._encounter_summary(result)
    assert set(summary) == {
        "valid_ticks","scored_ticks","tracking_valid_ticks","packet_valid_ticks",
        "raw_link_success_tr","raw_link_success_rb","blackout_ticks","lockout_ticks",
        "voluntary_updates","voluntary_keeps","opportunity_rows","safety_overrides",
        "override_causes","failures","tracker_energy_final","relay_energy_final",
        "update_energy_joules_per_uav",
    }
    assert summary["override_causes"].keys() == {"terrain","geofence","separation"}
    assert all(0 <= count <= summary["safety_overrides"] for count in summary["override_causes"].values())
    if summary["safety_overrides"]:
        assert sum(summary["override_causes"].values()) >= summary["safety_overrides"]
    assert summary["voluntary_updates"] + summary["voluntary_keeps"] == summary["opportunity_rows"]


def test_retained_encounter_rejects_uncovered_override_cause_tamper():
    block = blocks(0)[0]
    block["SHORT"]["safety_overrides"] = 1
    block["SHORT"]["override_causes"] = {"terrain":0,"geofence":0,"separation":0}
    with pytest.raises(serialization.SerializationError, match="do not cover every override"):
        serialization.validate_block_summary(block,replicate=0)


@pytest.mark.parametrize("value", [False, 7.0, 6, None])
def test_first_word_receipt_requires_exact_integer_bits(value):
    with pytest.raises(production.ProductionAdmissionError, match="first-word bits"):
        production._require_exact_first_word_bits(value,7)
    production._require_exact_first_word_bits(7,7)


def test_complete_digest_binds_both_activity_receipts():
    source = inspect.getsource(production.validate_complete_package)
    assert "activity_intent_sha256" in source
    assert "activity_started_sha256" in source
    replay_source = inspect.getsource(production._post_activity_replay_authority)
    assert "ACTIVITY_INTENT.json" in replay_source
    assert "_require_exact_first_word_bits" in replay_source


def test_native_artifact_identity_requires_exact_loaded_path_and_sha(tmp_path: Path):
    artifact = tmp_path / "headland90_backend.dll"
    expected_sha = "a"*64
    observed = {"artifact_path":str(artifact.resolve()),"artifact_sha256":expected_sha}
    assert production._native_identity_matches(str(artifact),expected_sha,observed)
    assert not production._native_identity_matches(str(artifact),"b"*64,observed)
    assert not production._native_identity_matches(str(tmp_path / "substitute.dll"),expected_sha,observed)


@pytest.mark.parametrize("artifact", ["lease", "backend"])
def test_complete_validation_authenticates_panel_admission_receipts(
    tmp_path: Path, artifact: str,
):
    root = tmp_path / "panel"
    permit = admit(root)
    production.initialize_private_panel(permit, source_set_sha256="1"*64, config_sha256="2"*64, schema_sha256="3"*64)
    if artifact == "lease":
        path = next((root / "lease-receipts").glob("*.json"))
        changed = lease(root); changed["cpu_workers"] = 7
        path.write_bytes(serialization.canonical_json_bytes(changed))
        message = "retained direction lease"
    else:
        path = root / "BACKEND_RECEIPT.json"
        changed = backend_receipt(production.ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST, 192)
        changed["native"]["artifact_sha256"] = "0"*64
        path.write_bytes(serialization.canonical_json_bytes(changed))
        message = "backend receipt"
    with pytest.raises((serialization.SerializationError, production.ProductionAdmissionError), match=message):
        production.validate_complete_package(root)


@pytest.mark.parametrize(
    "tampered_field",
    ["source_set_sha256", "preactivity_identity_sha256", "shared_guard_source_sha256"],
)
def test_admission_recomputes_live_source_identity_before_rows_or_backend(
    tmp_path: Path, tampered_field: str,
):
    root = tmp_path / "panel"
    rows_called = guard_called = False
    def rows(_document):
        nonlocal rows_called; rows_called = True; return "d" * 64
    def guard(*args, **kwargs):
        nonlocal guard_called; guard_called = True; return backend_receipt(args[0], 192)
    live = {
        key: str(freeze()[key])
        for key in (
            "source_set_sha256", "config_sha256", "schema_sha256",
            "preactivity_identity_sha256", "shared_guard_source_sha256",
        )
    }
    live[tampered_field] = "0" * 64
    with pytest.raises(production.ProductionAdmissionError, match=f"live {tampered_field}"):
        production._admit_production_fixture(
            preactivity_freeze=freeze(), coordinate_binding=binding(),
            direction_lease=lease(root), result_root=root,
            live_identity_verifier=lambda: live,
            coordinate_row_verifier=rows, shared_guard=guard,
        )
    assert not rows_called and not guard_called and not root.exists()
    permit = admit(root)
    assert permit.backend_receipt["python_fallback"] is False
    assert not root.exists()


def test_synthetic_cell_schema_is_canonical_small_and_same_coordinate_idempotent(tmp_path: Path):
    identity = serialization.CellIdentity("CAL", "theta-000", 0)
    packet = serialization.build_cell_packet(
        identity, bindings=cell_bindings(), blocks=blocks(0), trace_retained=True
    )
    assert serialization.validate_cell_packet(packet) == identity
    assert len(serialization.canonical_json_bytes(packet)) <= 32 * 1024
    first = serialization.write_cell_packet(tmp_path, packet)
    second = serialization.write_cell_packet(tmp_path, packet)
    assert first == second
    assert serialization.read_cell_packet(tmp_path, identity) == packet
    changed = dict(packet)
    changed["trace_retained"] = False
    with pytest.raises(FileExistsError, match="differs"):
        serialization.write_cell_packet(tmp_path, changed)


def test_synthetic_cell_rejects_missing_block_tamper_and_root_escape(tmp_path: Path):
    identity = serialization.CellIdentity("CAL", "theta-000", 0)
    with pytest.raises(serialization.SerializationError, match="20"):
        serialization.build_cell_packet(
            identity, bindings=cell_bindings(), blocks=blocks(0)[:-1], trace_retained=False
        )
    packet = serialization.build_cell_packet(
        identity, bindings=cell_bindings(), blocks=blocks(0), trace_retained=False
    )
    packet["aggregate"]["short_valid_ticks"] += 1
    with pytest.raises(serialization.SerializationError, match="aggregate"):
        serialization.validate_cell_packet(packet)
    with pytest.raises(serialization.SerializationError, match="escapes"):
        serialization.atomic_write_once(
            tmp_path.parent / "escape.json", {"x": 1}, authorized_root=tmp_path
        )


def test_compact_opportunity_and_cross_sidecars_are_exact_and_tamper_evident():
    opportunity = [(0, 0, 17, 128, 0, 0x3FF0000000000000), (19, 1, 47, 0, 1, 0)]
    cross = [(0, 0, 17, -32), (19, 1, 47, 17)]
    assert serialization.decode_opportunity_rows(serialization.encode_opportunity_rows(opportunity)) == tuple(opportunity)
    assert serialization.decode_cross_rows(serialization.encode_cross_rows(cross)) == tuple(cross)
    with pytest.raises(serialization.SerializationError, match="framing"):
        serialization.decode_opportunity_rows(serialization.encode_opportunity_rows(opportunity) + b"x")


def test_opportunity_sidecar_counts_are_bound_to_encounter_summary(tmp_path: Path):
    identity = serialization.CellIdentity("CAL", "theta-000", 0)
    payload = serialization.encode_opportunity_rows([])
    ref = {"format": serialization.OPPORTUNITY_LEDGER_FORMAT, "row_count": 0, "sha256": serialization.sha256_bytes(payload)}
    packet = serialization.build_cell_packet(identity, bindings=cell_bindings(), blocks=blocks(0), trace_retained=False, opportunity_ledger=ref)
    serialization.atomic_write_bytes(serialization.sidecar_path(tmp_path, identity, "opportunity"), payload, authorized_root=tmp_path)
    with pytest.raises(serialization.SerializationError, match="action counts"):
        production._validate_opportunity_structure(identity, packet, ())


def test_opportunity_sidecar_rejects_unscored_row_without_coordinate_replay(tmp_path: Path):
    tick, updated = 15, 0
    identity = serialization.CellIdentity("CAL", "theta-000", 0)
    cell_blocks = blocks(0)
    for block in cell_blocks:
        for route_class in ("SHORT", "LONG"):
            row = block[route_class]
            row["opportunity_rows"] = row["voluntary_updates"] = row["voluntary_keeps"] = 0
            row["update_energy_joules_per_uav"] = 200
    target = cell_blocks[0]["LONG"]
    target["opportunity_rows"] = 1
    target["voluntary_updates"] = updated
    target["voluntary_keeps"] = 1-updated
    target["update_energy_joules_per_uav"] = 200*(1+updated)
    rows = [(0, 0, tick, 0, updated, 0)]
    payload = serialization.encode_opportunity_rows(rows)
    ref = {"format":serialization.OPPORTUNITY_LEDGER_FORMAT,"row_count":1,"sha256":serialization.sha256_bytes(payload)}
    packet = serialization.build_cell_packet(identity, bindings=cell_bindings(), blocks=cell_blocks, trace_retained=False, opportunity_ledger=ref)
    serialization.atomic_write_bytes(serialization.sidecar_path(tmp_path, identity, "opportunity"), payload, authorized_root=tmp_path)
    with pytest.raises(serialization.SerializationError, match="scored time"):
        production._validate_opportunity_structure(identity, packet, rows)


def test_pure_action_decision_uses_supplied_synthetic_uniform_only():
    assert production._action_decision(0.01, Fraction(1, 2))
    assert not production._action_decision(0.99, Fraction(1, 2))
    assert "Coordinate" not in inspect.signature(production._action_decision).parameters


@pytest.mark.parametrize(
    "rows,error",
    [
        ([(0, 0, 17, 0, 0, 0), (0, 0, 16, 0, 0, 0)], "canonical order"),
        ([(0, 0, 16, 0, 0, 0), (0, 0, 16, 0, 0, 0)], "duplicated"),
    ],
)
def test_opportunity_sidecar_rejects_out_of_order_and_duplicate_addresses(
    tmp_path: Path, rows, error: str,
):
    identity = serialization.CellIdentity("CAL", "theta-000", 0)
    cell_blocks = blocks(0)
    for block in cell_blocks:
        for route_class in ("SHORT", "LONG"):
            block[route_class]["opportunity_rows"] = 0
            block[route_class]["voluntary_updates"] = 0
            block[route_class]["voluntary_keeps"] = 0
            block[route_class]["update_energy_joules_per_uav"] = 200
    cell_blocks[0]["LONG"]["opportunity_rows"] = 2
    cell_blocks[0]["LONG"]["voluntary_keeps"] = 2
    payload = serialization.encode_opportunity_rows(rows)
    ref = {
        "format": serialization.OPPORTUNITY_LEDGER_FORMAT,
        "row_count": len(rows),
        "sha256": serialization.sha256_bytes(payload),
    }
    packet = serialization.build_cell_packet(
        identity, bindings=cell_bindings(), blocks=cell_blocks,
        trace_retained=False, opportunity_ledger=ref,
    )
    serialization.atomic_write_bytes(
        serialization.sidecar_path(tmp_path, identity, "opportunity"),
        payload, authorized_root=tmp_path,
    )
    with pytest.raises(serialization.SerializationError, match=error):
        production._validate_opportunity_structure(identity, packet, rows)


def test_fraction_competence_boundaries_do_not_round_to_float():
    from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import analysis
    support = {"S": analysis.SupportFacts(256,256,96), "L": analysis.SupportFacts(256,256,96)}
    assert analysis.global_competent(selected_nonharm=True, calibration_mean=Fraction(19,20), held_out_mean=Fraction(1,4), held_out_tail=Fraction(1,10), support_by_stratum=support)
    assert not analysis.global_competent(selected_nonharm=True, calibration_mean=Fraction(19,20)+Fraction(1,10**18), held_out_mean=Fraction(1,4), held_out_tail=Fraction(1,10), support_by_stratum=support)


def test_nonidentification_reasons_use_frozen_first_failure_order():
    assert production._common_nonidentification_reason(
        nonharm=False, calibration_headroom=False, heldout_mean=False,
        heldout_tail=False, support=False,
    ) == "GLOBAL_SELECTED_CONTROLLER_NONHARM_FAILED"
    assert production._common_nonidentification_reason(
        nonharm=True, calibration_headroom=False, heldout_mean=False,
        heldout_tail=False, support=False,
    ) == "GLOBAL_CALIBRATION_HEADROOM_FAILED"
    assert production._common_nonidentification_reason(
        nonharm=True, calibration_headroom=True, heldout_mean=True,
        heldout_tail=True, support=True,
    ) is None
    assert production._two_nonidentification_reason(
        response=False, support=False, nonharm=False, reciprocal=False,
    ) == "TWO_RATE_RESPONSE_NOT_IDENTIFIED"
    assert production._two_nonidentification_reason(
        response=True, support=False, nonharm=False, reciprocal=False,
    ) == "TWO_VOLUNTARY_ACTION_SUPPORT_FAILED"
    assert production._two_nonidentification_reason(
        response=True, support=True, nonharm=True, reciprocal=False,
    ) == "RECIPROCAL_CONTROLS_INVALID"
    assert production._flex_nonidentification_reason(
        support=True, nonharm=True, algebraically_distinct=False,
        realized_distinct=False, timing_member=False,
    ) == "FLEX_NOT_ALGEBRAICALLY_DISTINCT"


def test_result_release_rejects_technical_acceptance_not_bound_to_complete(
    tmp_path: Path, monkeypatch,
):
    recomputed = {"schema": production.COMPLETE_SCHEMA, "complete": True}
    analyzer_called = False

    def load(path: Path):
        if Path(path).name == "COMPLETE.json":
            return recomputed
        return {
            "schema": production.TECHNICAL_ACCEPTANCE_SCHEMA,
            "card_revision": production.CARD_REVISION,
            "host": production.HOST_ID,
            "accepted": True,
            "complete_package_sha256": "0" * 64,
            "cm_acceptance_sha256": "1" * 64,
        }

    def analyzer(_root: Path):
        nonlocal analyzer_called
        analyzer_called = True
        return {}

    monkeypatch.setattr(production, "validate_complete_package", lambda _root: recomputed)
    monkeypatch.setattr(production, "_load_exact_document", load)
    monkeypatch.setattr(production, "_complete_panel_analysis", analyzer)
    with pytest.raises(production.ProductionAdmissionError, match="technical acceptance"):
        production.release_result(tmp_path)
    assert not analyzer_called
    assert not (tmp_path / "RESULT.json").exists()


def test_alias_trace_plan_preserves_five_logical_tags_and_deduplicates_only_identity():
    ledger = production.alias_ledger(
        global_best=controllers.lookup_controller(0, 0),
        two_stratum=controllers.lookup_controller(0, 0),
        flex=controllers.lookup_controller(0, 0),
    )
    plan = production.retained_trace_plan(ledger["rows"])
    assert len(plan["calibration_physical"]) == 16
    assert len(plan["held_out_logical"]) == 40
    assert plan["maximum_logical_traces"] == 56
    assert plan["unique_physical_trace_count"] == 24


def test_result_firewall_does_not_invoke_analyzer_for_incomplete_panel(tmp_path: Path):
    root = tmp_path / "panel"
    permit = admit(root)
    production.initialize_private_panel(
        permit, source_set_sha256="1" * 64, config_sha256="2" * 64, schema_sha256="3" * 64
    )
    summaries = {
        f"theta-{index:03d}": {
            "mean_value": [0, 1],
            "tail_value": [0, 1],
            "voluntary_updates": 0,
            "mean_lambda": {
                "value": 0.0,
                "row_count": 1,
                "order_digest": "8" * 64,
                "content_digest": "9" * 64,
            },
        }
        for index in range(192)
    }
    selector = production.selector_ledger(
        global_best=controllers.lookup_controller(0, 0),
        two_stratum=controllers.lookup_controller(0, 0),
        flex=controllers.lookup_controller(0, 0),
        calibration_summaries=summaries,
    )
    aliases = production.alias_ledger(
        global_best=controllers.lookup_controller(0, 0),
        two_stratum=controllers.lookup_controller(0, 0),
        flex=controllers.lookup_controller(0, 0),
    )
    serialization.atomic_write_once(root / "SELECTORS.json", selector, authorized_root=root)
    serialization.atomic_write_once(root / "ALIASES.json", aliases, authorized_root=root)
    serialization.atomic_write_once(
        root / "TRACE_INDEX.json", production.retained_trace_plan(aliases["rows"]), authorized_root=root
    )
    with pytest.raises(production.ProductionAdmissionError, match="post-activity"):
        production.release_result(root)
    assert not (root / "RESULT.json").exists()
    assert "complete_panel_analyzer" not in inspect.signature(production.release_result).parameters
    source = inspect.getsource(production._complete_panel_analysis)
    assert "evaluate_result_map" in source and "decode_cross_rows" in source
    for required in (
        "coendpoints_by_logical_tag", "conditional_rate_response",
        "support_counts", "cal_hard_safety", "hold_hard_safety",
        "override_ucb95", "flex_constituents", "flex_nonidentification_reason",
    ):
        assert required in source
    release_source = inspect.getsource(production.release_result)
    assert "TECHNICAL_ACCEPTANCE.json" in release_source and "CM technical acceptance" in release_source
