from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (
    empirical_contract as contract,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
    LEARNED_PACKAGES,
    SCIENCE_REVISION,
    SCRIPTED_PACKAGES,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_contract import (
    BENCHMARK_EVIDENCE_LOGICAL_PATH,
    CM_ACCEPTED_BINDING_SCHEMA,
    EMPIRICAL_OBJECT,
    PANEL_COUNTS,
    ROOT_LEASE_SCHEMA,
    SOURCE_REPAIR_LEASE_SCHEMA,
    SOURCE_REPAIR_REASON,
    EmpiricalContractError,
    LeaseError,
    RootLeasePermit,
    SYNTHETIC_TEST_IDENTITIES,
    analyzer_identity,
    build_preactivity_certificate,
    build_source_repair_bootstrap,
    build_source_repair_failed_terminal,
    build_source_repair_transition,
    build_test_preactivity_certificate,
    canonical_json_bytes,
    coordinate_proposal,
    document_sha256,
    frozen_config_identity,
    materialize_coordinates,
    native_identity_from_observation,
    production_source_paths,
    resource_request_proposal,
    stage_binding_identity,
    validate_accepted_binding,
    validate_archived_accepted_binding,
    validate_archived_initial_lease_for_source_repair,
    validate_archived_preactivity_certificate,
    validate_archived_resource_request,
    validate_benchmark_evidence_payload,
    validate_native_identity,
    validate_preactivity_certificate,
    validate_root_lease,
    validate_frozen_run_identity,
    validate_source_repair_replacement_lease,
    validate_source_repair_operator_terminal,
    validate_source_repair_transition,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (
    BRANCHES,
    HELDOUT_CELLS,
    TAIL_COUNT,
    TRAINING_CELLS,
)


def _synthetic_native_observation() -> dict[str, object]:
    return {
        "path": "SYNTHETIC-TEST-NATIVE-ARTIFACT.dll",
        "sha256": "023eecbc0a69710ee6a4fe06aa8e1b0b5165870bbcfc5a7ae2198e86372baf15",
        "size": 1234,
        "mtime_ns": 0,
        "source_sha256": "ddb14c33d822924b21b872713745f242fee92f16b4329efed439a1e2b816a910",
        "build_key": "8e80ba3cf3ba026c486d75d330aa9a99f820fe60803334dce7841032a48a5f91",
        "resolved_build_root": "SYNTHETIC-TEST-BUILD-ROOT",
        "runtime_abi": {"fixture_only": True, "label": "SYNTHETIC-TEST-RUNTIME"},
        "toolchain": {"fixture_only": True, "label": "SYNTHETIC-TEST-TOOLCHAIN"},
        "abi": {
            "abi_version": 2,
            "fixture_magic": 0x52434C4554424347,
            "fixture_input_size": 224,
            "step_input_size": 64,
            "event_input_size": 64,
            "snapshot_size": 464,
        },
        "load_seconds": 0.0,
    }


def _certificate(tmp_path: Path) -> dict[str, object]:
    del tmp_path
    return build_preactivity_certificate(
        source_paths=production_source_paths(),
        native_identity=native_identity_from_observation(_synthetic_native_observation()),
    )


def _test_certificate(tmp_path: Path) -> dict[str, object]:
    source = tmp_path / "SYNTHETIC_TEST_CONTRACT_SOURCE.txt"
    source.write_text("SYNTHETIC TEST SOURCE ONLY\n", encoding="ascii")
    native = native_identity_from_observation(_synthetic_native_observation())
    return build_test_preactivity_certificate(
        source_paths={"TEST/contract_source": source},
        native_identity=native,
    )


def _accepted_binding(certificate: dict[str, object]) -> dict[str, object]:
    body = {
        "schema": CM_ACCEPTED_BINDING_SCHEMA,
        "issuer": "/root/cm_rcle_cpc_r04",
        "technically_accepted": True,
        "direction_id": "roster_consistent_latent_exploration",
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "preactivity_certificate_sha256": certificate["certificate_sha256"],
        "source_set_sha256": certificate["source"]["source_set_sha256"],
        "config_sha256": certificate["config"]["config_sha256"],
        "native_identity_sha256": certificate["native"]["native_identity_sha256"],
        "analyzer_sha256": certificate["analyzer"]["analyzer_sha256"],
        "coordinate_proposal_sha256": certificate["coordinate_proposal"]["proposal_sha256"],
        "result_blind": True,
        "scientific_activity_started": False,
    }
    return {**body, "binding_sha256": document_sha256(body)}


def _synthetic_lease(
    certificate: dict[str, object],
    binding: dict[str, object],
    request: dict[str, object],
    *,
    lease_id: str,
    origin_lease_id: str,
    predecessor_lease_id: str | None,
    replacement_index: int,
    issued_at: str,
    expires_at: str,
) -> dict[str, object]:
    stage = stage_binding_identity(
        certificate=certificate,
        accepted_binding=binding,
        resource_request=request,
    )
    return {
        "schema": ROOT_LEASE_SCHEMA,
        "issuer": "SYNTHETIC-TEST-ONLY",
        "fixture_only": True,
        "lease_id": lease_id,
        "origin_lease_id": origin_lease_id,
        "predecessor_lease_id": predecessor_lease_id,
        "replacement_index": replacement_index,
        "stage_binding_sha256": stage["stage_binding_sha256"],
        "activity_authorized": False,
        "coordinate_materialization_authorized": False,
        "direction_id": "roster_consistent_latent_exploration",
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "preactivity_certificate_sha256": certificate["certificate_sha256"],
        "accepted_binding_sha256": binding["binding_sha256"],
        "coordinate_proposal_sha256": certificate["coordinate_proposal"]["proposal_sha256"],
        "source_set_sha256": certificate["source"]["source_set_sha256"],
        "config_sha256": certificate["config"]["config_sha256"],
        "native_identity_sha256": certificate["native"]["native_identity_sha256"],
        "analyzer_sha256": certificate["analyzer"]["analyzer_sha256"],
        "component": "rcle.tbcfv.r04.full_host",
        "abi_version": 2,
        "batch_width": 8,
        "paths": request["paths"],
        "resources": request["resources"],
        "counts": PANEL_COUNTS,
        "complete_panel_only": True,
        "result_blind_until_complete": True,
        "python_fallback": False,
    }


def _repaired_certificate(original: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    repaired = json.loads(json.dumps(original))
    label = (
        "experiments/candidates/roster_consistent_latent_exploration_tbcfv/"
        "empirical_artifacts.py"
    )
    old_row = dict(repaired["source"]["files"][label])
    new_row = {"bytes": old_row["bytes"] + 1, "sha256": "a" * 64}
    repaired["source"]["files"][label] = new_row
    source_body = {
        "files": repaired["source"]["files"],
        "ordering": repaired["source"]["ordering"],
    }
    repaired["source"]["source_set_sha256"] = document_sha256(source_body)
    certificate_body = {
        key: value for key, value in repaired.items() if key != "certificate_sha256"
    }
    repaired["certificate_sha256"] = document_sha256(certificate_body)
    delta = {
        "logical_path": label,
        "old_sha256": old_row["sha256"],
        "new_sha256": new_row["sha256"],
        "reason": SOURCE_REPAIR_REASON,
    }
    return repaired, delta


def _repaired_request(
    original_request: dict[str, object], repaired_certificate: dict[str, object]
) -> dict[str, object]:
    repaired = json.loads(json.dumps(original_request))
    repaired["preactivity_certificate_sha256"] = repaired_certificate[
        "certificate_sha256"
    ]
    repaired["source_set_sha256"] = repaired_certificate["source"][
        "source_set_sha256"
    ]
    repaired["benchmark_evidence"]["source_set_sha256"] = repaired_certificate[
        "source"
    ]["source_set_sha256"]
    return repaired


def _repair_fixture(tmp_path: Path) -> dict[str, object]:
    original_certificate = _certificate(tmp_path)
    original_binding = _accepted_binding(original_certificate)
    repository = Path(__file__).resolve().parents[4]
    result_root = repository / ".tmp" / f"SYNTHETIC_TEST_REPAIR_{tmp_path.name}"
    original_request = resource_request_proposal(
        original_certificate,
        repository_root=repository,
        result_root=result_root,
    )
    initial_lease = _synthetic_lease(
        original_certificate,
        original_binding,
        original_request,
        lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=None,
        replacement_index=0,
        issued_at="2026-08-21T10:00:00Z",
        expires_at="2026-08-21T12:00:00Z",
    )
    original_permit = validate_root_lease(
        initial_lease,
        certificate=original_certificate,
        accepted_binding=original_binding,
        resource_request=original_request,
        now=datetime(2026, 8, 21, 11, tzinfo=timezone.utc),
        synthetic_fixture=True,
    )
    run_identity_path = Path(original_permit.paths["run_identity_path"])
    run_identity_path.parent.mkdir(parents=True, exist_ok=True)
    identity_body = {
        "schema": "RCLE_TBCFV_R04_MATERIALIZED_COORDINATE_BINDING_V1",
        "identity": "SYNTHETIC-TEST-FROZEN-RUN-IDENTITY",
        "science_revision": SCIENCE_REVISION,
        "empirical_object": "SYNTHETIC-TEST-ONLY",
        "fixture_only": True,
        "non_scientific": True,
        "authority": original_permit.origin_lease_id,
        "stage_binding_sha256": original_permit.stage_binding_sha256,
        "numeric_seed_present": False,
        "master_material_exposed": False,
        "master_digest": "5" * 64,
        "run_block_count": 20,
        "run_block_roots": [
            {"block_index": index, "root_digest": f"{index + 1:064x}"}
            for index in range(20)
        ],
    }
    run_identity = {
        **identity_body,
        "binding_sha256": document_sha256(identity_body),
    }
    run_identity_path.write_bytes(canonical_json_bytes(run_identity))
    run_facts = validate_frozen_run_identity(
        run_identity_path, original_permit, synthetic_fixture=True
    )
    operator_terminal_path = tmp_path / "SYNTHETIC_TEST_OPERATOR_TERMINAL.json"
    operator_terminal_document = {
        "command": ["SYNTHETIC-TEST-OPERATOR", "run"],
        "cwd": "SYNTHETIC-TEST-CWD",
        "started_at": "2026-08-21T10:05:54.011589+00:00",
        "ended_at": "2026-08-21T10:05:58.128668+00:00",
        "exit_code": 2,
        "direct_error": "command exited with code 2",
        "output_paths": ["SYNTHETIC-TEST-RUN_IDENTITY.json"],
        "scientific_activity_predicate": "SYNTHETIC TEST activity predicate",
        "scientific_activity_started": True,
    }
    operator_terminal_path.write_bytes(
        (json.dumps(operator_terminal_document, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
    )
    operator_terminal = validate_source_repair_operator_terminal(
        operator_terminal_path, synthetic_fixture=True
    )
    failed_terminal = build_source_repair_failed_terminal(
        run_facts,
        original_permit,
        operator_terminal,
        synthetic_fixture=True,
    )
    failed_terminal_path = result_root / "FAILED_TERMINAL.json"
    failed_terminal_path.write_bytes(canonical_json_bytes(failed_terminal))

    repaired_certificate, source_delta = _repaired_certificate(original_certificate)
    repaired_binding = _accepted_binding(repaired_certificate)
    repaired_request = _repaired_request(original_request, repaired_certificate)
    transition_kwargs = {
        "original_certificate": original_certificate,
        "original_binding": original_binding,
        "original_request": original_request,
        "original_permit": original_permit,
        "repaired_certificate": repaired_certificate,
        "repaired_binding": repaired_binding,
        "repaired_request": repaired_request,
        "run_identity_path": run_identity_path,
        "failed_terminal_path": failed_terminal_path,
        "source_deltas": [source_delta],
        "synthetic_fixture": True,
    }
    transition = build_source_repair_transition(**transition_kwargs)
    repaired_stage = transition["repaired"]["stage_binding_sha256"]
    replacement_lease = {
        "schema": SOURCE_REPAIR_LEASE_SCHEMA,
        "issuer": "SYNTHETIC-TEST-ONLY",
        "fixture_only": True,
        "lease_id": SYNTHETIC_TEST_IDENTITIES[1],
        "origin_lease_id": original_permit.origin_lease_id,
        "predecessor_lease_id": original_permit.lease_id,
        "replacement_index": 1,
        "stage_binding_sha256": repaired_stage,
        "repair_transition_sha256": transition["repair_transition_sha256"],
        "activity_authorized": False,
        "coordinate_materialization_authorized": False,
        "direction_id": "roster_consistent_latent_exploration",
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "issued_at": "2026-08-21T12:00:00Z",
        "expires_at": "2026-08-21T14:00:00Z",
        "preactivity_certificate_sha256": repaired_certificate["certificate_sha256"],
        "accepted_binding_sha256": repaired_binding["binding_sha256"],
        "coordinate_proposal_sha256": repaired_certificate["coordinate_proposal"][
            "proposal_sha256"
        ],
        "source_set_sha256": repaired_certificate["source"]["source_set_sha256"],
        "config_sha256": repaired_certificate["config"]["config_sha256"],
        "native_identity_sha256": repaired_certificate["native"][
            "native_identity_sha256"
        ],
        "analyzer_sha256": repaired_certificate["analyzer"]["analyzer_sha256"],
        "component": "rcle.tbcfv.r04.full_host",
        "abi_version": 2,
        "batch_width": 8,
        "paths": repaired_request["paths"],
        "resources": repaired_request["resources"],
        "counts": PANEL_COUNTS,
        "complete_panel_only": True,
        "result_blind_until_complete": True,
        "python_fallback": False,
    }
    return {
        **transition_kwargs,
        "transition": transition,
        "replacement_lease": replacement_lease,
    }


def test_frozen_full_panel_counts_inventories_cells_and_analyzer() -> None:
    assert len(LEARNED_PACKAGES) == 5
    assert len(SCRIPTED_PACKAGES) == 3
    assert len(TRAINING_CELLS) == 8
    assert len(HELDOUT_CELLS) == 8
    assert PANEL_COUNTS == {
        "run_blocks": 20,
        "learned_arms": 5,
        "scripted_packages": 3,
        "updates_per_learned_arm_block": 800,
        "episodes_per_update": 64,
        "learned_arm_block_updates": 80_000,
        "training_episodes": 5_120_000,
        "learned_heldout_episodes_per_cell": 2_048,
        "learned_heldout_episodes": 1_638_400,
        "scripted_heldout_episodes_per_cell": 2_048,
        "scripted_heldout_episodes": 983_040,
        "total_episodes": 7_741_440,
        "environment_ticks": 495_452_160,
        "agent_ticks": 4_299_161_600,
        "agent_claim_decisions": 1_074_790_400,
        "candidate_pointer_scores": 6_448_742_400,
        "registered_tails": 72,
        "result_branches": 12,
    }
    analyzer = analyzer_identity()
    assert analyzer["registered_tails"] == TAIL_COUNT == 72
    assert analyzer["branches"] == list(BRANCHES) and len(BRANCHES) == 12
    config = frozen_config_identity()
    assert config["counts"] == PANEL_COUNTS
    assert config["native"] == {
        "component": "rcle.tbcfv.r04.full_host",
        "abi_version": 2,
        "supported_widths": [1, 8, 32],
        "selected_width": 8,
        "event_time_newcomer_position_input": True,
        "event_input_size": 64,
        "atomic_t24_event_input_before_claim": True,
        "stable_physical_agent_transport_keys": True,
        "transport_keys_actor_model_visible": False,
        "public_observation_excludes_transport_keys": True,
        "python_fallback": False,
    }


def test_coordinate_proposal_is_unmaterialized_and_identity_free() -> None:
    proposal = coordinate_proposal()
    assert proposal["materialized"] is False
    assert proposal["namespace"] is None
    assert proposal["run_block_identities"] is None
    assert proposal["numeric_seeds"] is None
    assert proposal["master"] is None and proposal["master_digest"] is None
    assert proposal["coordinate_rows"] is None
    assert proposal["random_scientific_state"] is None
    assert proposal["run_block_count"] == 20


def test_native_and_preactivity_certificate_bind_exact_identity_without_activity(
    tmp_path: Path,
) -> None:
    native = native_identity_from_observation(_synthetic_native_observation())
    assert validate_native_identity(native) == native
    assert native["component"] == "rcle.tbcfv.r04.full_host"
    assert native["supported_batch_widths"] == [1, 8, 32]
    assert native["selected_batch_width"] == 8
    assert native["python_fallback"] is False
    assert native["abi"] == {
        "abi_version": 2,
        "fixture_magic": 0x52434C4554424347,
        "fixture_input_size": 224,
        "step_input_size": 64,
        "event_input_size": 64,
        "snapshot_size": 464,
    }
    assert native["atomic_t24_event_input_before_claim"] is True
    assert native["event_batch_prevalidated_before_mutation"] is True
    assert native["stable_physical_agent_transport_keys"] is True
    assert native["transport_keys_actor_model_visible"] is False
    assert native["public_observation_excludes_transport_keys"] is True

    certificate = _test_certificate(tmp_path)
    assert validate_preactivity_certificate(certificate, allow_test_fixture=True) == certificate
    with pytest.raises(EmpiricalContractError, match="not production-admissible"):
        validate_preactivity_certificate(certificate)
    assert certificate["fixture_only"] is True
    assert certificate["non_scientific"] is True
    assert certificate["schema"].endswith("SYNTHETIC_TEST_PREACTIVITY_CERTIFICATE_V1")
    assert certificate["counts"] == PANEL_COUNTS
    assert certificate["activity_boundary"] == {
        "scientific_activity_started": False,
        "identity_present": False,
        "numeric_seed_present": False,
        "coordinate_present": False,
        "random_scientific_state_present": False,
        "model_or_checkpoint_present": False,
        "training_or_evaluation_present": False,
        "result_or_endpoint_present": False,
        "lease_present": False,
        "production_launch": False,
    }
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "SYNTHETIC_TEST_CONTRACT_SOURCE.txt"
    ]


def test_certificate_and_native_tampering_fail_closed(tmp_path: Path) -> None:
    native = native_identity_from_observation(_synthetic_native_observation())
    with pytest.raises(EmpiricalContractError, match="digest differs"):
        validate_native_identity({**native, "artifact_sha256": "9" * 64})

    certificate = _test_certificate(tmp_path)
    changed = dict(certificate)
    changed["counts"] = {**PANEL_COUNTS, "run_blocks": 19}
    changed_body = {key: value for key, value in changed.items() if key != "certificate_sha256"}
    changed["certificate_sha256"] = document_sha256(changed_body)
    with pytest.raises(EmpiricalContractError, match="frozen object differs"):
        validate_preactivity_certificate(changed, allow_test_fixture=True)

    materialized = dict(certificate)
    materialized_proposal = dict(certificate["coordinate_proposal"])
    materialized_proposal["numeric_seeds"] = [999_999]
    materialized["coordinate_proposal"] = materialized_proposal
    materialized_body = {
        key: value for key, value in materialized.items() if key != "certificate_sha256"
    }
    materialized["certificate_sha256"] = document_sha256(materialized_body)
    with pytest.raises(EmpiricalContractError, match="contains material"):
        validate_preactivity_certificate(materialized, allow_test_fixture=True)


def test_abi1_and_missing_event_input_size_fail_closed() -> None:
    abi1 = _synthetic_native_observation()
    abi1["abi"] = {
        "abi_version": 1,
        "fixture_magic": 0x52434C4554424346,
        "fixture_input_size": 224,
        "step_input_size": 64,
        "event_input_size": 64,
        "snapshot_size": 408,
    }
    with pytest.raises(EmpiricalContractError, match="ABI differs"):
        native_identity_from_observation(abi1)

    missing_event = _synthetic_native_observation()
    missing_event_abi = dict(missing_event["abi"])
    del missing_event_abi["event_input_size"]
    missing_event["abi"] = missing_event_abi
    with pytest.raises(EmpiricalContractError, match="ABI field inventory differs"):
        native_identity_from_observation(missing_event)


def test_production_certificate_requires_exact_live_logical_path_inventory(
    tmp_path: Path,
) -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (
        empirical_runner,
    )

    del tmp_path
    native = native_identity_from_observation(_synthetic_native_observation())
    paths = production_source_paths()
    certificate = build_preactivity_certificate(
        source_paths=paths,
        native_identity=native,
    )
    assert validate_preactivity_certificate(certificate) == certificate
    assert certificate["fixture_only"] is False
    assert certificate["non_scientific"] is False
    assert set(certificate["source"]["files"]) == set(paths)
    empirical_runner._validate_live_source_set(certificate)

    omitted = dict(paths)
    omitted.pop(next(iter(omitted)))
    with pytest.raises(EmpiricalContractError, match="inventory differs"):
        build_preactivity_certificate(source_paths=omitted, native_identity=native)

    extra = {**paths, "experiments/candidates/roster_consistent_latent_exploration_tbcfv/EXTRA.py": next(iter(paths.values()))}
    with pytest.raises(EmpiricalContractError, match="inventory differs"):
        build_preactivity_certificate(source_paths=extra, native_identity=native)

    labels = tuple(paths)
    mislabelled = dict(paths)
    mislabelled[labels[0]] = paths[labels[1]]
    with pytest.raises(EmpiricalContractError, match="misbound"):
        build_preactivity_certificate(source_paths=mislabelled, native_identity=native)


def test_production_certificate_rejects_resealed_live_byte_drift(tmp_path: Path) -> None:
    del tmp_path
    certificate = _certificate(Path("SYNTHETIC-TEST-IGNORED"))
    changed = dict(certificate)
    source = dict(certificate["source"])
    files = {label: dict(row) for label, row in source["files"].items()}
    label = next(iter(files))
    files[label]["sha256"] = "f" * 64
    source_body = {"files": files, "ordering": source["ordering"]}
    changed["source"] = {
        **source_body,
        "source_set_sha256": document_sha256(source_body),
    }
    changed_body = {
        key: value for key, value in changed.items() if key != "certificate_sha256"
    }
    changed["certificate_sha256"] = document_sha256(changed_body)
    with pytest.raises(EmpiricalContractError, match="live production source bytes drifted"):
        validate_preactivity_certificate(changed)


def test_test_certificate_cannot_enter_cm_binding_or_resource_admission(
    tmp_path: Path,
) -> None:
    certificate = _test_certificate(tmp_path)
    binding = _accepted_binding(certificate)
    with pytest.raises(EmpiricalContractError, match="not production-admissible"):
        validate_accepted_binding(binding, certificate)
    with pytest.raises(EmpiricalContractError, match="not production-admissible"):
        resource_request_proposal(
            certificate,
            repository_root=Path(__file__).resolve().parents[4],
            result_root=Path(__file__).resolve().parents[4]
            / ".tmp"
            / "SYNTHETIC_TEST_FORBIDDEN_ADMISSION",
        )


def test_benchmark_evidence_is_canonical_abi2_complete_and_result_blind() -> None:
    path = production_source_paths()[BENCHMARK_EVIDENCE_LOGICAL_PATH]
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    evidence = validate_benchmark_evidence_payload(payload, expected_sha256=digest)
    assert evidence["sha256"] == digest
    assert evidence["projected_cpu_core_hours"] == pytest.approx(24.795777452256944)
    assert evidence["projected_wall_hours_one_worker"] == pytest.approx(8.675334549445355)
    assert evidence["projected_wall_hours_four_workers_lower"] == pytest.approx(
        2.1739627069446595
    )
    assert evidence["measured_basis"]["rss_per_worker_bytes"] == 486_055_936

    with pytest.raises(EmpiricalContractError, match="SHA-256 differs"):
        validate_benchmark_evidence_payload(payload, expected_sha256="0" * 64)
    malformed = b"{SYNTHETIC-TEST-MALFORMED\n"
    with pytest.raises(EmpiricalContractError, match="canonical ASCII JSON"):
        validate_benchmark_evidence_payload(
            malformed, expected_sha256=hashlib.sha256(malformed).hexdigest()
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    (
        ("abi1", "ABI2 identity differs"),
        ("stale_source", "source identity is stale"),
        ("missing_chain", "chain coverage is incomplete"),
        ("fallback", "activity/result-blind boundary differs"),
        ("incomplete_analyzer", "analyzer evidence differs"),
    ),
)
def test_benchmark_evidence_rejects_stale_or_incomplete_payload(
    mutation: str, match: str
) -> None:
    value = json.loads(
        production_source_paths()[BENCHMARK_EVIDENCE_LOGICAL_PATH].read_text("ascii")
    )
    if mutation == "abi1":
        value["component_identity"]["abi"]["abi_version"] = 1
    elif mutation == "stale_source":
        value["component_identity"]["source_sha256"] = "0" * 64
    elif mutation == "missing_chain":
        del value["chain_coverage"]["resume"]
    elif mutation == "fallback":
        value["python_fallback"] = True
    elif mutation == "incomplete_analyzer":
        value["synthetic_72_tail_analyzer"]["completed"] = False
    else:  # pragma: no cover - parametrization is closed above
        raise AssertionError(mutation)
    payload = canonical_json_bytes(value)
    with pytest.raises(EmpiricalContractError, match=match):
        validate_benchmark_evidence_payload(
            payload, expected_sha256=hashlib.sha256(payload).hexdigest()
        )


def test_result_blind_resource_request_is_proposal_only(tmp_path: Path) -> None:
    certificate = _certificate(tmp_path)
    repository = Path(__file__).resolve().parents[4]
    result_root = repository / ".tmp" / "SYNTHETIC_TEST_RCTF_RESULT_ROOT"
    request = resource_request_proposal(
        certificate, repository_root=repository, result_root=result_root
    )
    assert request["authority"] == "REQUEST_ONLY"
    assert request["lease_issued"] is False
    assert request["activity_authorized"] is False
    assert request["production_launch"] is False
    assert request["result_blind"] is True
    assert request["coordinate_materialization"] == (
        "ONLY_AFTER_ROOT_LEASE_AND_CM_ACCEPTED_BINDING"
    )
    assert request["renewal"] == {
        "same_coordinate_resume_only": True,
        "immutable_origin_lease_id": True,
        "immutable_stage_binding_sha256": True,
        "immediate_predecessor_required": True,
        "replacement_index_increments_by_one": True,
        "windows_are_contiguous_and_nonoverlapping": True,
        "accepted_preactivity_and_coordinate_proposal_preserved": True,
        "source_config_native_analyzer_preserved": True,
        "result_root_preserved": True,
        "worker_and_resource_stage_ceiling_preserved": True,
        "replacement_coordinate_materialization": False,
    }
    assert request["resources"] == {
        "cpu_only": True,
        "gpu_count": 0,
        "one_thread_per_worker": True,
        "max_independent_workers": 4,
        "projected_cpu_core_hours": 24.795777452256946,
        "cpu_core_hours_upper": 30.0,
        "projected_wall_hours_one_worker": 8.675334549445355,
        "projected_wall_hours_four_workers_lower": 2.173962706944659,
        "measured_rss_bytes_per_worker": 486_055_936,
        "measured_io_read_bytes": 2_558_500,
        "measured_io_write_bytes": 656_876,
        "measured_durable_fixture_bytes": 634_160,
        "measured_scratch_fixture_bytes_peak": 156_160,
        "rss_gib_per_worker_upper": 4.0,
        "scratch_gib_upper": 12.0,
        "durable_artifacts_gib_upper": 1.0,
        "validity_hours": 24,
    }
    assert request["benchmark_evidence"] == {
        "logical_path": BENCHMARK_EVIDENCE_LOGICAL_PATH,
        "sha256": "565514e31c68155c728b9283af87e26bd33e4034034c865ab2e59aa5931a5b50",
        "schema": "RCLE_TBCFV_R04_FIXTURE_EFFICIENCY_REVIEW_V1",
        "native_source_sha256": "ddb14c33d822924b21b872713745f242fee92f16b4329efed439a1e2b816a910",
        "projected_cpu_core_hours": 24.795777452256946,
        "projected_wall_hours_one_worker": 8.675334549445355,
        "projected_wall_hours_four_workers_lower": 2.173962706944659,
        "measured_basis": {
            "rss_per_worker_bytes": 486_055_936,
            "measured_read_bytes": 2_558_500,
            "measured_write_bytes": 656_876,
            "durable_fixture_bytes_for_20_blocks": 634_160,
            "scratch_fixture_bytes_peak": 156_160,
        },
        "source_set_sha256": certificate["source"]["source_set_sha256"],
    }
    assert not result_root.exists()


def test_cm_binding_validator_is_exact_and_result_blind(tmp_path: Path) -> None:
    certificate = _certificate(tmp_path)
    binding = _accepted_binding(certificate)
    assert validate_accepted_binding(binding, certificate) == binding
    with pytest.raises(EmpiricalContractError, match="digest differs"):
        validate_accepted_binding({**binding, "source_set_sha256": "f" * 64}, certificate)


def test_root_lease_validator_rejects_request_and_synthetic_lease_identity(
    tmp_path: Path,
) -> None:
    certificate = _certificate(tmp_path)
    binding = _accepted_binding(certificate)
    repository = Path(__file__).resolve().parents[4]
    request = resource_request_proposal(
        certificate,
        repository_root=repository,
        result_root=repository / ".tmp" / "SYNTHETIC_TEST_RCTF_RESULT_ROOT",
    )
    now = datetime(2026, 8, 21, 12, tzinfo=timezone.utc)
    with pytest.raises(LeaseError, match="Root lease field inventory differs"):
        validate_root_lease(
            request,
            certificate=certificate,
            accepted_binding=binding,
            resource_request=request,
            now=now,
        )

    synthetic_lease = _synthetic_lease(
        certificate,
        binding,
        request,
        lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=None,
        replacement_index=0,
        issued_at="2026-08-21T11:00:00Z",
        expires_at="2026-08-21T13:00:00Z",
    )
    with pytest.raises(LeaseError, match="cannot impersonate"):
        validate_root_lease(
            synthetic_lease,
            certificate=certificate,
            accepted_binding=binding,
            resource_request=request,
            now=now,
        )


def test_synthetic_lineage_fixture_proves_initial_and_exact_replacement_contract(
    tmp_path: Path,
) -> None:
    certificate = _certificate(tmp_path)
    binding = _accepted_binding(certificate)
    repository = Path(__file__).resolve().parents[4]
    request = resource_request_proposal(
        certificate,
        repository_root=repository,
        result_root=repository / ".tmp" / "SYNTHETIC_TEST_RCTF_LINEAGE_ROOT",
    )
    initial = _synthetic_lease(
        certificate,
        binding,
        request,
        lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=None,
        replacement_index=0,
        issued_at="2026-08-21T10:00:00Z",
        expires_at="2026-08-21T12:00:00Z",
    )
    first = validate_root_lease(
        initial,
        certificate=certificate,
        accepted_binding=binding,
        resource_request=request,
        now=datetime(2026, 8, 21, 11, tzinfo=timezone.utc),
        synthetic_fixture=True,
    )
    assert first.fixture_only is True
    assert first.lease_id == first.origin_lease_id == SYNTHETIC_TEST_IDENTITIES[0]
    assert first.replacement_index == 0 and first.predecessor_lease_id is None
    assert first.lease_lineage == (SYNTHETIC_TEST_IDENTITIES[0],)

    replacement = _synthetic_lease(
        certificate,
        binding,
        request,
        lease_id=SYNTHETIC_TEST_IDENTITIES[1],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        replacement_index=1,
        issued_at="2026-08-21T12:00:00Z",
        expires_at="2026-08-21T14:00:00Z",
    )
    second = validate_root_lease(
        replacement,
        certificate=certificate,
        accepted_binding=binding,
        resource_request=request,
        now=datetime(2026, 8, 21, 13, tzinfo=timezone.utc),
        predecessor_permit=first,
        synthetic_fixture=True,
    )
    assert second.lease_id == SYNTHETIC_TEST_IDENTITIES[1]
    assert second.origin_lease_id == first.origin_lease_id
    assert second.predecessor_lease_id == first.lease_id
    assert second.replacement_index == 1
    assert second.lease_lineage == SYNTHETIC_TEST_IDENTITIES
    assert second.stage_binding_sha256 == first.stage_binding_sha256
    assert second.paths == first.paths and second.resources == first.resources
    assert second.immutable_frontier_lease_binding() == first.immutable_frontier_lease_binding()
    assert second.immutable_frontier_lease_binding() == {
        "origin_lease_id": SYNTHETIC_TEST_IDENTITIES[0],
        "lease_id": SYNTHETIC_TEST_IDENTITIES[0],
        "lease_binding_sha256": first.stage_binding_sha256,
    }
    with pytest.raises(LeaseError, match="production validated"):
        second.runtime_authority()

    with pytest.raises(LeaseError, match="synthetic lease fixture cannot authorize"):
        materialize_coordinates(
            "SYNTHETIC-LIKE-BUT-NOT-REGISTERED",
            master_material=b"x" * 32,
            permit=first,
            accepted_binding=binding,
            certificate=certificate,
            now=datetime(2026, 8, 21, 11, tzinfo=timezone.utc),
        )


@pytest.mark.parametrize(
    ("field", "value", "match"),
    (
        ("replacement_index", 2, "lineage gap"),
        ("predecessor_lease_id", SYNTHETIC_TEST_IDENTITIES[1], "lineage gap"),
        ("origin_lease_id", SYNTHETIC_TEST_IDENTITIES[1], "lineage gap"),
        ("issued_at", "2026-08-21T11:59:59Z", "gap or overlap"),
        ("issued_at", "2026-08-21T12:00:01Z", "gap or overlap"),
        ("expires_at", "2026-08-21T12:30:00Z", "inactive"),
        ("stage_binding_sha256", "f" * 64, "binding differs"),
        ("resources", {"SYNTHETIC_TEST_DRIFT": True}, "binding differs"),
    ),
)
def test_replacement_lineage_gap_overlap_and_drift_fail_closed(
    tmp_path: Path, field: str, value: object, match: str
) -> None:
    certificate = _certificate(tmp_path)
    binding = _accepted_binding(certificate)
    repository = Path(__file__).resolve().parents[4]
    request = resource_request_proposal(
        certificate,
        repository_root=repository,
        result_root=repository / ".tmp" / "SYNTHETIC_TEST_RCTF_LINEAGE_REJECT_ROOT",
    )
    initial = _synthetic_lease(
        certificate,
        binding,
        request,
        lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=None,
        replacement_index=0,
        issued_at="2026-08-21T10:00:00Z",
        expires_at="2026-08-21T12:00:00Z",
    )
    first = validate_root_lease(
        initial,
        certificate=certificate,
        accepted_binding=binding,
        resource_request=request,
        now=datetime(2026, 8, 21, 11, tzinfo=timezone.utc),
        synthetic_fixture=True,
    )
    replacement = _synthetic_lease(
        certificate,
        binding,
        request,
        lease_id=SYNTHETIC_TEST_IDENTITIES[1],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        replacement_index=1,
        issued_at="2026-08-21T12:00:00Z",
        expires_at="2026-08-21T14:00:00Z",
    )
    replacement[field] = value
    with pytest.raises(LeaseError, match=match):
        validate_root_lease(
            replacement,
            certificate=certificate,
            accepted_binding=binding,
            resource_request=request,
            now=datetime(2026, 8, 21, 13, tzinfo=timezone.utc),
            predecessor_permit=first,
            synthetic_fixture=True,
        )


def test_only_fixed_synthetic_test_identities_materialize_without_authority() -> None:
    first = materialize_coordinates(SYNTHETIC_TEST_IDENTITIES[0])
    repeated = materialize_coordinates(SYNTHETIC_TEST_IDENTITIES[0])
    second = materialize_coordinates(SYNTHETIC_TEST_IDENTITIES[1])
    assert first == repeated and first != second
    assert first["fixture_only"] is True and first["non_scientific"] is True
    assert first["empirical_object"] == "SYNTHETIC-TEST-ONLY"
    assert first["numeric_seed_present"] is False
    assert first["master_material_exposed"] is False
    assert first["run_block_count"] == 2
    assert all(set(row) == {"block_index", "root_digest"} for row in first["run_block_roots"])

    with pytest.raises(LeaseError, match="requires Root lease"):
        materialize_coordinates("SYNTHETIC-LIKE-BUT-NOT-REGISTERED")
    with pytest.raises(EmpiricalContractError, match="accepts no authority"):
        materialize_coordinates(SYNTHETIC_TEST_IDENTITIES[0], master_material=b"x" * 32)


def test_source_repair_transition_and_index1_replacement_preserve_original_authority(
    tmp_path: Path,
) -> None:
    fixture = _repair_fixture(tmp_path)
    transition = fixture["transition"]
    original_certificate_sha = fixture["original_certificate"]["certificate_sha256"]
    original_request_sha = document_sha256(fixture["original_request"])
    assert validate_source_repair_transition(
        transition,
        **{key: value for key, value in fixture.items() if key not in {"transition", "replacement_lease"}},
    ) == transition
    assert fixture["original_certificate"]["certificate_sha256"] == original_certificate_sha
    assert document_sha256(fixture["original_request"]) == original_request_sha
    assert (
        validate_archived_preactivity_certificate(fixture["original_certificate"])
        == fixture["original_certificate"]
    )
    assert (
        validate_archived_accepted_binding(
            fixture["original_binding"], fixture["original_certificate"]
        )
        == fixture["original_binding"]
    )
    assert (
        validate_archived_resource_request(
            fixture["original_request"], fixture["original_certificate"]
        )
        == fixture["original_request"]
    )
    assert transition["reason"] == SOURCE_REPAIR_REASON
    assert transition["science_change"] is False
    assert transition["coordinate_materialization_authorized"] is False
    assert len(transition["run_identity"]["run_block_roots"]) == 20
    assert transition["failed_terminal"]["terminal"] is True
    assert transition["original"]["stage_binding_sha256"] != transition["repaired"][
        "stage_binding_sha256"
    ]

    repaired = validate_source_repair_replacement_lease(
        fixture["replacement_lease"],
        repair_transition=transition,
        original_permit=fixture["original_permit"],
        repaired_certificate=fixture["repaired_certificate"],
        repaired_binding=fixture["repaired_binding"],
        repaired_request=fixture["repaired_request"],
        now=datetime(2026, 8, 21, 13, tzinfo=timezone.utc),
        synthetic_fixture=True,
    )
    assert repaired.lease_id == SYNTHETIC_TEST_IDENTITIES[1]
    assert repaired.origin_lease_id == SYNTHETIC_TEST_IDENTITIES[0]
    assert repaired.predecessor_lease_id == SYNTHETIC_TEST_IDENTITIES[0]
    assert repaired.replacement_index == 1
    assert repaired.stage_binding_sha256 == transition["repaired"][
        "stage_binding_sha256"
    ]
    assert repaired.repair_transition_sha256 == transition["repair_transition_sha256"]
    assert repaired.coordinate_proposal_sha256 == fixture["original_permit"].coordinate_proposal_sha256
    with pytest.raises(LeaseError, match="cannot authorize production materialization"):
        materialize_coordinates(
            "SYNTHETIC-LIKE-BUT-NOT-REGISTERED",
            master_material=b"x" * 32,
            permit=repaired,
            accepted_binding=fixture["repaired_binding"],
            certificate=fixture["repaired_certificate"],
            now=datetime(2026, 8, 21, 13, tzinfo=timezone.utc),
        )


def test_archived_initial_lease_requires_exact_repair_bridge_and_cannot_run(
    tmp_path: Path,
) -> None:
    fixture = _repair_fixture(tmp_path)
    original_lease = _synthetic_lease(
        fixture["original_certificate"],
        fixture["original_binding"],
        fixture["original_request"],
        lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=None,
        replacement_index=0,
        issued_at="2026-08-21T10:00:00Z",
        expires_at="2026-08-21T12:00:00Z",
    )
    archived = validate_archived_initial_lease_for_source_repair(
        original_lease,
        certificate=fixture["original_certificate"],
        accepted_binding=fixture["original_binding"],
        resource_request=fixture["original_request"],
        repair_transition=fixture["transition"],
        synthetic_fixture=True,
    )
    assert archived.archived_only is True
    assert archived.stage_binding_sha256 == fixture["original_permit"].stage_binding_sha256
    with pytest.raises(LeaseError, match="archived initial lease cannot authorize activity"):
        archived.require_active(now=datetime(2026, 8, 21, 11, tzinfo=timezone.utc))

    kwargs = {
        key: value
        for key, value in fixture.items()
        if key not in {"transition", "replacement_lease", "original_permit"}
    }
    kwargs["original_permit"] = archived
    assert build_source_repair_transition(**kwargs) == fixture["transition"]
    repaired = validate_source_repair_replacement_lease(
        fixture["replacement_lease"],
        repair_transition=fixture["transition"],
        original_permit=archived,
        repaired_certificate=fixture["repaired_certificate"],
        repaired_binding=fixture["repaired_binding"],
        repaired_request=fixture["repaired_request"],
        now=datetime(2026, 8, 21, 13, tzinfo=timezone.utc),
        synthetic_fixture=True,
    )
    assert repaired.archived_only is False
    assert repaired.repair_transition_sha256 == fixture["transition"][
        "repair_transition_sha256"
    ]

    changed_bridge = json.loads(json.dumps(fixture["transition"]))
    changed_bridge["source_deltas"][0]["old_sha256"] = "0" * 64
    bridge_body = {
        key: value
        for key, value in changed_bridge.items()
        if key != "repair_transition_sha256"
    }
    changed_bridge["repair_transition_sha256"] = document_sha256(bridge_body)
    with pytest.raises(LeaseError, match="old-source row differs"):
        validate_archived_initial_lease_for_source_repair(
            original_lease,
            certificate=fixture["original_certificate"],
            accepted_binding=fixture["original_binding"],
            resource_request=fixture["original_request"],
            repair_transition=changed_bridge,
            synthetic_fixture=True,
        )


def test_source_repair_bootstrap_closes_real_shape_source_drift_cycle(
    tmp_path: Path,
) -> None:
    fixture = _repair_fixture(tmp_path)
    Path(fixture["failed_terminal_path"]).unlink()
    original_lease = _synthetic_lease(
        fixture["original_certificate"],
        fixture["original_binding"],
        fixture["original_request"],
        lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=None,
        replacement_index=0,
        issued_at="2026-08-21T10:00:00Z",
        expires_at="2026-08-21T12:00:00Z",
    )
    bootstrap_kwargs = {
        "original_certificate": fixture["original_certificate"],
        "original_binding": fixture["original_binding"],
        "original_request": fixture["original_request"],
        "original_lease": original_lease,
        "repaired_certificate": fixture["repaired_certificate"],
        "repaired_binding": fixture["repaired_binding"],
        "repaired_request": fixture["repaired_request"],
        "run_identity_path": fixture["run_identity_path"],
        "operator_terminal_path": tmp_path / "SYNTHETIC_TEST_OPERATOR_TERMINAL.json",
        "source_deltas": fixture["source_deltas"],
        "synthetic_fixture": True,
    }
    bootstrap = build_source_repair_bootstrap(**bootstrap_kwargs)
    assert bootstrap["archived_permit_authoritative"] is False
    assert bootstrap["activity_authorized"] is False
    assert bootstrap["coordinate_materialization_authorized"] is False
    failed_path = Path(bootstrap["failed_terminal_path"])
    assert not failed_path.exists()
    assert bootstrap["failed_terminal_document"]["operator_terminal"][
        "exit_code"
    ] == 2
    failed_path.write_bytes(canonical_json_bytes(bootstrap["failed_terminal_document"]))
    with pytest.raises(EmpiricalContractError, match="refuses an existing"):
        build_source_repair_bootstrap(**bootstrap_kwargs)
    archived = validate_archived_initial_lease_for_source_repair(
        original_lease,
        certificate=fixture["original_certificate"],
        accepted_binding=fixture["original_binding"],
        resource_request=fixture["original_request"],
        repair_transition=bootstrap["repair_transition_document"],
        synthetic_fixture=True,
    )
    assert archived.archived_only is True
    with pytest.raises(LeaseError, match="archived initial lease cannot authorize activity"):
        archived.require_active(now=datetime(2026, 8, 21, 11, tzinfo=timezone.utc))


@pytest.mark.parametrize(
    "mutation",
    ("command", "exit_code", "activity", "timestamps", "duplicate_key"),
)
def test_source_repair_bootstrap_rejects_operator_terminal_drift(
    tmp_path: Path, mutation: str
) -> None:
    fixture = _repair_fixture(tmp_path)
    Path(fixture["failed_terminal_path"]).unlink()
    operator_path = tmp_path / "SYNTHETIC_TEST_OPERATOR_TERMINAL.json"
    document = json.loads(operator_path.read_text(encoding="utf-8"))
    if mutation == "command":
        document["command"] = ["SYNTHETIC-TEST-OPERATOR", "changed"]
    elif mutation == "exit_code":
        document["exit_code"] = 0
    elif mutation == "activity":
        document["scientific_activity_started"] = False
    elif mutation == "timestamps":
        document["ended_at"] = document["started_at"]
    if mutation == "duplicate_key":
        operator_path.write_text(
            '{"command":[],"command":[],"cwd":"SYNTHETIC-TEST-CWD"}\n',
            encoding="utf-8",
        )
    else:
        operator_path.write_bytes(
            (json.dumps(document, separators=(",", ":")) + "\n").encode("utf-8")
        )
    original_lease = _synthetic_lease(
        fixture["original_certificate"],
        fixture["original_binding"],
        fixture["original_request"],
        lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=None,
        replacement_index=0,
        issued_at="2026-08-21T10:00:00Z",
        expires_at="2026-08-21T12:00:00Z",
    )
    with pytest.raises((EmpiricalContractError, LeaseError)):
        build_source_repair_bootstrap(
            original_certificate=fixture["original_certificate"],
            original_binding=fixture["original_binding"],
            original_request=fixture["original_request"],
            original_lease=original_lease,
            repaired_certificate=fixture["repaired_certificate"],
            repaired_binding=fixture["repaired_binding"],
            repaired_request=fixture["repaired_request"],
            run_identity_path=fixture["run_identity_path"],
            operator_terminal_path=operator_path,
            source_deltas=fixture["source_deltas"],
            synthetic_fixture=True,
        )


@pytest.mark.parametrize(
    "field",
    (
        "stage_binding_sha256",
        "source_set_sha256",
        "config_sha256",
        "native_identity_sha256",
        "analyzer_sha256",
        "coordinate_proposal_sha256",
        "resources",
    ),
)
def test_archived_initial_lease_rejects_any_original_binding_drift(
    tmp_path: Path, field: str
) -> None:
    fixture = _repair_fixture(tmp_path)
    original_lease = _synthetic_lease(
        fixture["original_certificate"],
        fixture["original_binding"],
        fixture["original_request"],
        lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        origin_lease_id=SYNTHETIC_TEST_IDENTITIES[0],
        predecessor_lease_id=None,
        replacement_index=0,
        issued_at="2026-08-21T10:00:00Z",
        expires_at="2026-08-21T12:00:00Z",
    )
    changed = json.loads(json.dumps(original_lease))
    changed[field] = {"SYNTHETIC_TEST_DRIFT": True} if field == "resources" else "0" * 64
    with pytest.raises(LeaseError, match=f"binding differs: {field}"):
        validate_archived_initial_lease_for_source_repair(
            changed,
            certificate=fixture["original_certificate"],
            accepted_binding=fixture["original_binding"],
            resource_request=fixture["original_request"],
            repair_transition=fixture["transition"],
            synthetic_fixture=True,
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    (
        ("omitted", "incomplete or out of order"),
        ("old_hash", "hash/reason differs"),
        ("new_hash", "hash/reason differs"),
        ("reason", "hash/reason differs"),
    ),
)
def test_source_repair_delta_must_be_exactly_enumerated(
    tmp_path: Path, mutation: str, match: str
) -> None:
    fixture = _repair_fixture(tmp_path)
    kwargs = {key: value for key, value in fixture.items() if key not in {"transition", "replacement_lease"}}
    deltas = json.loads(json.dumps(kwargs["source_deltas"]))
    if mutation == "omitted":
        deltas = []
    elif mutation == "old_hash":
        deltas[0]["old_sha256"] = "0" * 64
    elif mutation == "new_hash":
        deltas[0]["new_sha256"] = "0" * 64
    elif mutation == "reason":
        deltas[0]["reason"] = "SYNTHETIC-TEST-WRONG-REASON"
    kwargs["source_deltas"] = deltas
    with pytest.raises(EmpiricalContractError, match=match):
        build_source_repair_transition(**kwargs)


def test_shared_policy_delta_is_one_exact_non_generalized_exception() -> None:
    old_row = {
        "bytes": 23_403,
        "sha256": contract.SOURCE_REPAIR_SHARED_POLICY_OLD_SHA256,
    }
    new_row = {
        "bytes": contract.SOURCE_REPAIR_SHARED_POLICY_NEW_BYTES,
        "sha256": contract.SOURCE_REPAIR_SHARED_POLICY_NEW_SHA256,
    }
    assert contract._expected_source_repair_delta(
        contract.SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH, old_row, new_row
    ) == {
        "logical_path": contract.SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH,
        "old_sha256": contract.SOURCE_REPAIR_SHARED_POLICY_OLD_SHA256,
        "new_sha256": contract.SOURCE_REPAIR_SHARED_POLICY_NEW_SHA256,
        "reason": contract.SOURCE_REPAIR_SHARED_POLICY_REASON,
    }
    for changed_path, changed_new in (
        ("docs/project/UNRELATED_POLICY.md", new_row),
        (
            contract.SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH,
            {**new_row, "sha256": "0" * 64},
        ),
        (
            contract.SOURCE_REPAIR_SHARED_POLICY_LOGICAL_PATH,
            {**new_row, "bytes": 23_619},
        ),
    ):
        with pytest.raises(EmpiricalContractError):
            contract._expected_source_repair_delta(changed_path, old_row, changed_new)


@pytest.mark.parametrize(
    ("field", "match"),
    (
        ("config", "frozen object differs"),
        ("native", "native identity digest differs"),
        ("analyzer", "frozen object differs"),
        ("coordinate_proposal", "coordinate proposal differs"),
    ),
)
def test_source_repair_rejects_config_native_analyzer_or_coordinate_drift(
    tmp_path: Path, field: str, match: str
) -> None:
    fixture = _repair_fixture(tmp_path)
    changed = json.loads(json.dumps(fixture["repaired_certificate"]))
    if field == "config":
        changed["config"]["host"]["horizon"] = 63
    elif field == "native":
        changed["native"]["artifact_sha256"] = "0" * 64
    elif field == "analyzer":
        changed["analyzer"]["registered_tails"] = 71
    else:
        changed["coordinate_proposal"]["run_block_count"] = 19
    changed_body = {
        key: value for key, value in changed.items() if key != "certificate_sha256"
    }
    changed["certificate_sha256"] = document_sha256(changed_body)
    kwargs = {key: value for key, value in fixture.items() if key not in {"transition", "replacement_lease"}}
    kwargs["repaired_certificate"] = changed
    with pytest.raises(EmpiricalContractError, match=match):
        build_source_repair_transition(**kwargs)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    (
        ("paths", {"SYNTHETIC_TEST_DRIFT": True}, "path inventory differs"),
        ("resources", {"SYNTHETIC_TEST_DRIFT": True}, "measurements differ"),
    ),
)
def test_source_repair_rejects_result_path_or_resource_drift(
    tmp_path: Path, field: str, value: object, match: str
) -> None:
    fixture = _repair_fixture(tmp_path)
    kwargs = {key: item for key, item in fixture.items() if key not in {"transition", "replacement_lease"}}
    request = json.loads(json.dumps(fixture["repaired_request"]))
    request[field] = value
    kwargs["repaired_request"] = request
    with pytest.raises(EmpiricalContractError, match=match):
        build_source_repair_transition(**kwargs)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    (
        ("origin_lease_id", SYNTHETIC_TEST_IDENTITIES[1], "origin_lease_id"),
        ("predecessor_lease_id", SYNTHETIC_TEST_IDENTITIES[1], "predecessor_lease_id"),
        ("replacement_index", 2, "replacement_index"),
        ("coordinate_materialization_authorized", True, "coordinate_materialization_authorized"),
        ("repair_transition_sha256", "f" * 64, "repair_transition_sha256"),
        ("issued_at", "2026-08-21T11:59:59Z", "gap or overlap"),
    ),
)
def test_source_repair_replacement_rejects_lineage_or_authority_drift(
    tmp_path: Path, field: str, value: object, match: str
) -> None:
    fixture = _repair_fixture(tmp_path)
    lease = dict(fixture["replacement_lease"])
    lease[field] = value
    with pytest.raises(LeaseError, match=match):
        validate_source_repair_replacement_lease(
            lease,
            repair_transition=fixture["transition"],
            original_permit=fixture["original_permit"],
            repaired_certificate=fixture["repaired_certificate"],
            repaired_binding=fixture["repaired_binding"],
            repaired_request=fixture["repaired_request"],
            now=datetime(2026, 8, 21, 13, tzinfo=timezone.utc),
            synthetic_fixture=True,
        )


def test_unsealed_permit_cannot_authorize_materialization() -> None:
    permit = RootLeasePermit(
        lease_id="SYNTHETIC-TEST-UNSEALED-PERMIT",
        origin_lease_id="SYNTHETIC-TEST-UNSEALED-PERMIT",
        predecessor_lease_id=None,
        replacement_index=0,
        lease_lineage=("SYNTHETIC-TEST-UNSEALED-PERMIT",),
        stage_binding_sha256="4" * 64,
        accepted_binding_sha256="1" * 64,
        preactivity_certificate_sha256="2" * 64,
        coordinate_proposal_sha256="3" * 64,
        issued_at="2026-08-21T11:00:00Z",
        expires_at="2026-08-21T13:00:00Z",
        paths={},
        resources={},
        fixture_only=True,
        repair_transition_sha256=None,
    )
    with pytest.raises(LeaseError, match="unvalidated"):
        permit.require_active(now=datetime(2026, 8, 21, 12, tzinfo=timezone.utc))
