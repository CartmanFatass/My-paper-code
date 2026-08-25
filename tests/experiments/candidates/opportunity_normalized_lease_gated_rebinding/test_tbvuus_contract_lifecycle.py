from __future__ import annotations

import hashlib
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import contracts
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import lifecycle
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import preactivity
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import serialization


SHA = "1" * 64


def _sidecars():
    return {
        kind: {"schema": schema, "row_count": rows, "sha256": SHA, "bytes": 7}
        for kind, (schema, rows) in contracts.SIDECAR_SCHEMAS.items()
    }


def _aggregate(identity: serialization.CellIdentity):
    return {
        "blocks": 20,
        "encounters": 40,
        "physical_ticks": 3840,
        "scored_ticks": 3200,
        "short_encounters": 20,
        "long_encounters": 20,
        "scheduled_t0_decisions": 40,
        "action_shell_count": 0 if identity.arm == contracts.NEVER_UPDATE else 40,
        "road_fit_available_count": 30,
        "effective_road_patch_count": 10,
        "effective_road_patch_by_route": {"SHORT": 5, "LONG": 5},
        "valid_scored_ticks": 2000,
        "safety_overrides": 0,
        "hard_failures": {key: 0 for key in contracts.HARD_FAILURE_KEYS},
        "mean_value": 0.625,
        "tail_value": 0.25,
        "tape_commitment_sha256": SHA,
        "tick_audit_valid": True,
        "road_fit_audit_valid": True,
        "arm_transition_audit_valid": True,
        "endpoint_audit_valid": True,
        "raw_conformant": True,
        "sham_valid": True,
        "road_fit_facts": {
            "every_encounter_audited": True,
            "availability_exact": True,
            "tie_order_exact": True,
            "selected_template_audited": True,
            "patch_formula_exact": True,
            "identity_fallback_exact": True,
            "no_future_or_hidden_input": True,
        },
        "arm_transition_facts": {
            "scheduled_exact": True,
            "shell_exact": True,
            "energy_debit_exact": True,
            "blackout_exact": True,
            "lockout_exact": True,
            "buffer_clear_exact": True,
            "waypoints_unchanged": True,
            "planner_not_invoked": True,
            "later_keep_exact": True,
        },
        "sham_validity_facts": {
            "common_pre_action_state_equal": True,
            "common_tapes_equal": True,
            "estimator_bitwise_unchanged": True,
            "waypoints_bitwise_unchanged": True,
            "only_registered_shell_differences": True,
            "tickwise_q_not_greater_than_never": True,
            "post_blackout_equal_absent_battery_exhaustion": True,
        },
    }


def _packet(identity: serialization.CellIdentity):
    return serialization.build_cell_packet(
        identity,
        bindings={key: SHA for key in contracts.BINDING_KEYS},
        aggregate=_aggregate(identity),
        sidecars=_sidecars(),
    )


def test_exact_panel_and_coordinate_free_proposal():
    assert contracts.CONTROLLER_REPLICATES == 512
    assert contracts.TOTAL_ARM_ENCOUNTERS == 20_480
    assert contracts.TOTAL_PHYSICAL_TICKS == 1_966_080
    assert contracts.SCHEDULED_T0_DECISIONS_PER_ARM == 5_120
    proposal = contracts.coordinate_proposal()
    assert contracts.validate_coordinate_proposal(proposal) == proposal
    assert proposal["bound"] is False
    assert proposal["controller_free_tape_law"]["action_stream_present"] is False
    altered = dict(proposal)
    altered["bound"] = True
    with pytest.raises(contracts.ContractError):
        contracts.validate_coordinate_proposal(altered)


def test_preactivity_requires_full_native_cpp_and_no_materialized_fields(tmp_path):
    source = tmp_path / "source.cpp"
    source.write_bytes(b"int x;\n")
    native = {
        "backend": "cpp",
        "python_fallback": False,
        "full_reset_step_cpp": True,
        "abi_version": "TBVUUS-R03-ABI-v1",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "artifact_sha256": "2" * 64,
        "toolchain": {"compiler": "test", "strict_fp": True},
    }
    value = preactivity.collect_preactivity_identity(
        source_paths={"native/source.cpp": source},
        config_facts={"batch_widths": [1, 8, 32]},
        native_identity=native,
    )
    assert preactivity.validate_preactivity_identity(value) == value
    with pytest.raises(preactivity.PreactivityError):
        preactivity.collect_preactivity_identity(
            source_paths={"native/source.cpp": source},
            config_facts={"coordinate_rows": []},
            native_identity=native,
        )
    with pytest.raises(preactivity.PreactivityError):
        preactivity.validate_native_identity({**native, "python_fallback": True})


def test_cell_sidecar_and_commit_contracts_are_exact():
    identity = serialization.CellIdentity(contracts.ROAD_TRACK_ESTIMATE_PATCH, 127)
    packet = _packet(identity)
    assert serialization.validate_cell_packet(packet) == identity
    commit = serialization.build_cell_commit(identity, packet)
    assert serialization.validate_cell_commit(commit) == identity
    broken = dict(packet)
    broken["aggregate"] = {**packet["aggregate"], "action_shell_count": 0}
    with pytest.raises(serialization.SerializationError):
        serialization.validate_cell_packet(broken)


def test_panel_commit_requires_every_exact_cell_in_frozen_order():
    commits = []
    for identity in serialization.expected_cell_identities():
        commits.append(serialization.build_cell_commit(identity, _packet(identity)))
    panel = serialization.build_panel_commit(commits)
    assert len(serialization.validate_panel_commit(panel)) == 512
    with pytest.raises(serialization.SerializationError):
        serialization.build_panel_commit(commits[:-1])
    validation = {
        "complete": True,
        "cell_count": 512,
        "panel_commit": panel,
        "validation_sha256": "7" * 64,
    }
    receipt_bindings = {
        key: (
            panel["panel_commit_sha256"]
            if key == "rebuilt_panel_commit_sha256"
            else validation["validation_sha256"]
            if key == "validation_sha256"
            else "5" * 64
        )
        for key in lifecycle.COMPLETE_BINDING_KEYS
    }
    complete = lifecycle.build_complete_marker(
        validation, receipt_bindings=receipt_bindings
    )
    assert lifecycle.validate_complete_marker(complete) == complete
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.validate_complete_marker(
            {**complete, "activity_started_sha256": "6" * 64}
        )


def test_write_once_is_idempotent_and_conflict_fails(tmp_path):
    root = tmp_path / "run"
    root.mkdir()
    path = root / "fact.json"
    lifecycle.atomic_write_once(path, {"x": 1}, authorized_root=root)
    lifecycle.atomic_write_once(path, {"x": 1}, authorized_root=root)
    with pytest.raises(FileExistsError):
        lifecycle.atomic_write_once(path, {"x": 2}, authorized_root=root)
    assert path.read_bytes() == b'{"x":1}\n'


def test_empty_resume_inventory_never_materializes_or_replaces_cells(tmp_path):
    inventory = lifecycle.resume_inventory(tmp_path)
    assert len(inventory.missing) == 512
    assert not inventory.committed
    assert not inventory.complete
    assert list(tmp_path.iterdir()) == []


def _complete_and_acceptance():
    panel_digest = "3" * 64
    complete_body = {
        "schema": contracts.COMPLETE_SCHEMA,
        "science_revision": contracts.SCIENCE_REVISION,
        "stage": contracts.STAGE,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "panel_commit_sha256": panel_digest,
        "panel_sha256": "5" * 64,
        "backend_receipt_sha256": "5" * 64,
        "coordinate_binding_sha256": "5" * 64,
        "lease_scope_sha256": "5" * 64,
        "lease_receipt_inventory_sha256": "5" * 64,
        "activity_intent_sha256": "5" * 64,
        "activity_started_sha256": "5" * 64,
        "rebuilt_panel_commit_sha256": panel_digest,
        "validation_sha256": "5" * 64,
        "cell_count": 512,
        "all_assigned_cells_complete": True,
        "atomic_package": True,
        "partial_release_allowed": False,
    }
    complete = {
        **complete_body,
        "complete_sha256": contracts.document_sha256(complete_body),
    }
    acceptance = lifecycle.build_cm_acceptance(
        complete_sha256=complete["complete_sha256"],
        acceptance_facts_sha256="4" * 64,
    )
    return complete, acceptance


def _release_paths(root):
    return (
        root / lifecycle.RESULT_V2_NAME,
        root / lifecycle.RESULT_V2_RELEASE_AUTHORIZATION_NAME,
        root / lifecycle.PORTFOLIO_EM_SEQUENCING_RECEIPT_NAME,
    )


def _portfolio_em_receipt(root, complete, acceptance):
    destination, _, _ = _release_paths(root)
    return {
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
        "receipt_id": "00000000-0000-4000-8000-000000000010",
        "portfolio_em_actor": lifecycle.PORTFOLIO_EM_ACTOR,
        "result_blind_accepted_complete_intake": True,
        "legacy_result_used": False,
        "root_release_authority_granted": False,
    }


def _install_portfolio_em_receipt(root, complete, acceptance):
    receipt = _portfolio_em_receipt(root, complete, acceptance)
    path = _release_paths(root)[2]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contracts.canonical_json_bytes(receipt))
    return receipt


def _release_authorization(root, complete, acceptance):
    destination, authorization_path, em_receipt_path = _release_paths(root)
    installed = lifecycle.validate_installed_portfolio_em_sequencing_receipt(
        result_root=root, complete=complete, cm_acceptance=acceptance
    )
    return {
        "schema": contracts.RESULT_RELEASE_AUTHORIZATION_SCHEMA,
        "science_revision": contracts.SCIENCE_REVISION,
        "stage": contracts.STAGE,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "result_root": str(root.resolve()),
        "result_destination_path": str(destination.resolve()),
        "complete_sha256": complete["complete_sha256"],
        "cm_acceptance_sha256": acceptance["cm_acceptance_sha256"],
        "authorization_id": "00000000-0000-4000-8000-000000000001",
        "operator": lifecycle.RELEASE_OPERATOR,
        "release_authorization_path": str(authorization_path.resolve()),
        "portfolio_em_sequencing_receipt_path": str(em_receipt_path.resolve()),
        "portfolio_em_sequencing_receipt_sha256": installed.installed_bytes_sha256,
        "result_release_authorized": True,
    }


def _release_receipt(root, complete, acceptance):
    return lifecycle.build_result_release_receipt(
        _release_authorization(root, complete, acceptance),
        result_root=root,
        complete=complete,
        cm_acceptance=acceptance,
    )


def test_result_v2_firewall_is_exact_and_result_blind(tmp_path):
    complete, acceptance = _complete_and_acceptance()
    destination, _, em_receipt_path = _release_paths(tmp_path)
    installed_document = _install_portfolio_em_receipt(tmp_path, complete, acceptance)
    installed = lifecycle.validate_installed_portfolio_em_sequencing_receipt(
        result_root=tmp_path, complete=complete, cm_acceptance=acceptance
    )
    assert installed.document == installed_document
    assert installed.path == em_receipt_path.resolve()
    assert installed.installed_bytes_sha256 == hashlib.sha256(
        em_receipt_path.read_bytes()
    ).hexdigest()
    authorization = _release_authorization(tmp_path, complete, acceptance)
    receipt = _release_receipt(tmp_path, complete, acceptance)
    result = {
        "schema": contracts.RESULT_SCHEMA,
        "science_revision": contracts.SCIENCE_REVISION,
        "stage": contracts.STAGE,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "complete_sha256": complete["complete_sha256"],
        "cm_acceptance_sha256": acceptance["cm_acceptance_sha256"],
        "complete_panel": True,
        "analysis": {"branch": "VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS"},
        "release_receipt": _release_receipt(tmp_path, complete, acceptance),
    }
    assert lifecycle.validate_result_firewall(
        result_root=tmp_path,
        complete=complete,
        cm_acceptance=acceptance,
        result_envelope=result,
        release_authorization=authorization,
    ) == result
    assert receipt["release_authorization_sha256"] == contracts.document_sha256(authorization)
    assert receipt["release_id"] == lifecycle.derive_result_release_id(authorization)
    assert receipt["result_destination_path"] == str(destination.resolve())
    assert receipt["portfolio_em_sequencing_receipt_path"] == str(em_receipt_path)
    assert receipt["portfolio_em_sequencing_receipt_sha256"] == authorization[
        "portfolio_em_sequencing_receipt_sha256"
    ]
    assert receipt["portfolio_em_sequencing_receipt_id"] == installed_document["receipt_id"]
    assert receipt["result_blind"] is True
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.validate_result_firewall(
            result_root=tmp_path,
            complete=complete,
            cm_acceptance=acceptance,
            result_envelope={**result, "analysis": {"partial_result": True}},
            release_authorization=authorization,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda token: {key: value for key, value in token.items() if key != "operator"},
        lambda token: {**token, "extra": True},
        lambda token: {**token, "complete_sha256": "7" * 64},
        lambda token: {**token, "cm_acceptance_sha256": "7" * 64},
        lambda token: {**token, "authorization_id": "NOT-A-UUID"},
        lambda token: {**token, "operator": "/root/cm"},
        lambda token: {**token, "portfolio_em_sequencing_receipt_path": "relative.json"},
        lambda token: {**token, "portfolio_em_sequencing_receipt_sha256": "A" * 64},
        lambda token: {**token, "result_release_authorized": False},
    ),
)
def test_result_v2_authorization_rejects_missing_extra_or_wrong_bindings(tmp_path, mutation):
    complete, acceptance = _complete_and_acceptance()
    _install_portfolio_em_receipt(tmp_path, complete, acceptance)
    token = mutation(_release_authorization(tmp_path, complete, acceptance))
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.validate_result_release_authorization(
            token,
            result_root=tmp_path,
            complete=complete,
            cm_acceptance=acceptance,
        )


@pytest.mark.parametrize(
    "field",
    ("result_root", "result_destination_path", "release_authorization_path", "portfolio_em_sequencing_receipt_path"),
)
def test_result_v2_authorization_rejects_wrong_claimed_path(tmp_path, field):
    root = tmp_path / "accepted"
    root.mkdir()
    complete, acceptance = _complete_and_acceptance()
    _install_portfolio_em_receipt(root, complete, acceptance)
    token = _release_authorization(root, complete, acceptance)
    token[field] = str((tmp_path / "wrong" / Path(token[field]).name).resolve())
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.validate_result_release_authorization(
            token, result_root=root, complete=complete, cm_acceptance=acceptance
        )


@pytest.mark.parametrize(
    "payload",
    (
        b"\xef\xbb\xbf{}\n",
        b"{}\r\n",
        b"{ \"x\": 1 }\n",
        b"{}",
        b"{}\nextra",
        b"\xff\xfe",
        b"{not-json}\n",
    ),
)
def test_installed_portfolio_receipt_rejects_malformed_or_noncanonical_bytes(tmp_path, payload):
    complete, acceptance = _complete_and_acceptance()
    path = _release_paths(tmp_path)[2]
    path.write_bytes(payload)
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.validate_installed_portfolio_em_sequencing_receipt(
            result_root=tmp_path, complete=complete, cm_acceptance=acceptance
        )


def test_installed_portfolio_receipt_rejects_missing_directory_and_symlink(tmp_path, monkeypatch):
    complete, acceptance = _complete_and_acceptance()
    path = _release_paths(tmp_path)[2]
    (tmp_path / "alternate-receipt.json").write_bytes(
        contracts.canonical_json_bytes(_portfolio_em_receipt(tmp_path, complete, acceptance))
    )
    with pytest.raises(lifecycle.LifecycleError, match="missing"):
        lifecycle.validate_installed_portfolio_em_sequencing_receipt(
            result_root=tmp_path, complete=complete, cm_acceptance=acceptance
        )
    path.mkdir()
    with pytest.raises(lifecycle.LifecycleError, match="regular file"):
        lifecycle.validate_installed_portfolio_em_sequencing_receipt(
            result_root=tmp_path, complete=complete, cm_acceptance=acceptance
        )
    path.rmdir()
    target = tmp_path / "target.json"
    target.write_bytes(contracts.canonical_json_bytes(_portfolio_em_receipt(tmp_path, complete, acceptance)))
    try:
        path.symlink_to(target)
    except OSError:
        original_lstat = Path.lstat
        monkeypatch.setattr(
            Path,
            "lstat",
            lambda self: (
                SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
                if self == path
                else original_lstat(self)
            ),
        )
    with pytest.raises(lifecycle.LifecycleError, match="symlink or reparse"):
        lifecycle.validate_installed_portfolio_em_sequencing_receipt(
            result_root=tmp_path, complete=complete, cm_acceptance=acceptance
        )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda receipt: {**receipt, "extra": True},
        lambda receipt: {**receipt, "schema": "wrong"},
        lambda receipt: {**receipt, "serializer": "wrong"},
        lambda receipt: {**receipt, "complete_sha256": "7" * 64},
        lambda receipt: {**receipt, "cm_acceptance_sha256": "7" * 64},
        lambda receipt: {**receipt, "receipt_id": "NOT-A-UUID"},
        lambda receipt: {**receipt, "portfolio_em_actor": "/root"},
        lambda receipt: {**receipt, "result_blind_accepted_complete_intake": False},
        lambda receipt: {**receipt, "legacy_result_used": True},
        lambda receipt: {**receipt, "root_release_authority_granted": True},
    ),
)
def test_installed_portfolio_receipt_rejects_wrong_schema_identity_or_booleans(tmp_path, mutation):
    complete, acceptance = _complete_and_acceptance()
    document = mutation(_portfolio_em_receipt(tmp_path, complete, acceptance))
    _release_paths(tmp_path)[2].write_bytes(contracts.canonical_json_bytes(document))
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.validate_installed_portfolio_em_sequencing_receipt(
            result_root=tmp_path, complete=complete, cm_acceptance=acceptance
        )


def test_result_v2_publication_is_one_atomic_write_once_receipt(tmp_path):
    root = tmp_path / "accepted"
    root.mkdir()
    complete, acceptance = _complete_and_acceptance()
    destination, authorization_path, em_receipt_path = _release_paths(root)
    _install_portfolio_em_receipt(root, complete, acceptance)
    authorization = _release_authorization(root, complete, acceptance)
    lifecycle.atomic_write_once(root / lifecycle.COMPLETE_NAME, complete, authorized_root=root)
    lifecycle.atomic_write_once(
        root / lifecycle.CM_ACCEPTANCE_NAME, acceptance, authorized_root=root
    )
    result = {
        "schema": contracts.RESULT_SCHEMA,
        "science_revision": contracts.SCIENCE_REVISION,
        "stage": contracts.STAGE,
        "host": contracts.HOST_ID,
        "namespace": contracts.PRODUCTION_NAMESPACE,
        "complete_sha256": complete["complete_sha256"],
        "cm_acceptance_sha256": acceptance["cm_acceptance_sha256"],
        "complete_panel": True,
        "analysis": {"branch": "VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS"},
        "release_receipt": _release_receipt(root, complete, acceptance),
    }
    authorization_path.write_bytes(contracts.canonical_json_bytes(authorization))
    lifecycle.publish_result_once(
        root,
        result,
    )
    assert lifecycle.read_canonical_json(destination) == result
    assert not destination.with_name(f".{destination.name}.pending").exists()
    with pytest.raises(FileExistsError):
        lifecycle.publish_result_once(
            root,
            result,
        )
