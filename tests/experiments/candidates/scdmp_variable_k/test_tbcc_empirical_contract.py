from __future__ import annotations

import copy
import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import (
    empirical_contract,
    lease,
    preactivity,
    rng,
    source_manifest,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.config import (
    COMPONENT,
    FIXTURE_MAGIC,
    FUNCTIONAL_BATCH_WIDTHS,
    HOST,
    NATIVE_ABI_VERSION,
)


REPO = Path(__file__).resolve().parents[4]
NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _native() -> dict[str, object]:
    source = REPO / source_manifest.PACKAGE_PREFIX / "native/tbcc_backend.cpp"
    digest = source_manifest._sha(source)
    return {
        "schema": "SCDMP-TBCC-R02-NATIVE-ARTIFACT-IDENTITY-V1",
        "component": COMPONENT,
        "host": HOST,
        "artifact_path": str((REPO / "TEST/tbcc_backend.dll").resolve()),
        "artifact_sha256": source_manifest.ACCEPTED_NATIVE_ARTIFACT_SHA256,
        "artifact_size": source_manifest.ACCEPTED_NATIVE_ARTIFACT_SIZE,
        "source_path": str(source.resolve()),
        "source_sha256": digest,
        "build_key": source_manifest.ACCEPTED_NATIVE_BUILD_KEY,
        "toolchain": {"TEST": True},
        "runtime_abi": {
            "abi_version": NATIVE_ABI_VERSION,
            "struct_sizes": dict(source_manifest.ACCEPTED_ABI_SIZES),
            "TEST": True,
        },
        "abi_version": NATIVE_ABI_VERSION,
        "fixture_magic": FIXTURE_MAGIC,
        "max_batch_width": 144,
        "functional_batch_widths": list(FUNCTIONAL_BATCH_WIDTHS),
        "full_reset_step_cpp": True,
        "python_environment_state": False,
        "python_plant_transition": False,
        "python_fallback": False,
        "load_seconds": 999.0,
    }


def _shared_guard(native: dict[str, object], calls: list[dict[str, object]] | None = None):
    def guard(component, *, backend, batch_width, build_root):
        if calls is not None:
            calls.append(
                {
                    "component": component,
                    "backend": backend,
                    "batch_width": batch_width,
                    "build_root": build_root,
                }
            )
        return {
            "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
            "component": COMPONENT,
            "backend": "cpp",
            "batch_width": batch_width,
            "full_reset_step_cpp": True,
            "python_fallback": False,
            "native": {
                "module": "CDLL",
                "binding_kind": "ctypes_cdll",
                "artifact": native["artifact_path"],
                "artifact_sha256": native["artifact_sha256"],
            },
        }

    return guard


def _validation() -> dict[str, bool]:
    return {
        "runner_to_card_counts": True,
        "controller_and_optimizer_arithmetic": True,
        "analyzer_branch_inventory": True,
        "worker_equivalence_1_2_4": True,
        "malformed_input_fail_closed": True,
        "interrupted_frontier_fail_closed": True,
        "atomic_io_and_resume": True,
        "end_to_end_result_blind_efficiency": True,
    }


def _acceptance_fixture():
    native = _native()
    manifest = source_manifest.build_source_manifest(REPO, native_identity=native)
    manifest_sha = source_manifest.manifest_digest(manifest)
    proposal = empirical_contract.coordinate_proposal(manifest_sha)
    receipt = preactivity.require_direction_cpp_batched_production(
        batch_width=144,
        shared_guard=_shared_guard(native),
        candidate_identity=lambda: native,
    )
    acceptance = preactivity.build_preactivity_acceptance(
        repository_root=REPO,
        source_manifest=manifest,
        native_identity=native,
        native_receipt=receipt,
        coordinate=proposal,
        efficiency_evidence_sha256="e" * 64,
        validation=_validation(),
    )
    return native, manifest, proposal, receipt, acceptance


def test_unmaterialized_proposal_has_exact_namespace_counts_domains_and_barriers():
    value = empirical_contract.coordinate_proposal()
    assert value["materialized"] is False
    assert value["replicate_namespace"] == (
        "SCDMP-TBCC-ORDER-VALUE-r01/replicate/<uint32_be(s)>"
    )
    assert value["replicates"] == list(range(24))
    assert value["rng"]["master"] is None
    assert len(empirical_contract.DOMAIN_LABELS) == len(set(empirical_contract.DOMAIN_LABELS))
    assert value["counts"]["complete_episodes_or_rollouts"] == 343_296
    assert value["counts"]["complete_allocated_slots"] == 124_959_744
    assert value["counts"]["complete_max_policy_queries"] == 15_829_632
    assert value["counts"]["complete_adamw_steps"] == 129_024
    assert value["counts"]["complete_final_checkpoints"] == 96
    assert value["barriers"]["opportunity_pass_before_order_materialization"] is True
    assert value["barriers"]["partial_publication_or_interpretation"] is False
    assert value["native_reward_trace"] == {
        "abi_version": 2,
        "capacity": 13,
        "count_field": "last_hold_reward_count",
        "values_field": "last_hold_rewards",
        "count_equals_ticks_advanced": True,
        "inactive_tail": "canonical_zero",
    }


def test_external_test_master_only_and_every_domain_is_separated():
    assert "os" not in rng.__dict__
    assert not any("fresh" in name or "sample" in name for name in rng.__dict__)
    test_master = bytes(range(32))
    proof = rng.domain_separation_proof(test_master)
    assert all(
        proof[field]
        for field in (
            "replicate_messages_injective",
            "domain_labels_disjoint",
            "derived_domain_key_digests_unique",
        )
    )
    first = rng.for_domain(test_master, 0, empirical_contract.DOMAIN_LABELS[0])
    second = rng.for_domain(test_master, 0, empirical_contract.DOMAIN_LABELS[1])
    assert first.raw_u64("TEST", 1) != second.raw_u64("TEST", 1)
    assert sorted(first.permutation(16, "TEST")) == list(range(16))
    address = {"tensor_group": "actor", "flat_index": 0}
    assert rng.raw_u64(
        test_master, 0, "foundation-initialization", **address
    ) == rng.raw_u64(test_master, 0, "foundation-initialization", **address)
    with pytest.raises(rng.RNGContractError):
        rng.raw_u64(test_master, 0, "foundation-initialization", tensor_group="actor")
    with pytest.raises(rng.RNGContractError):
        rng.validate_external_master(b"short")


def test_source_manifest_builder_is_in_memory_complete_and_detects_changes():
    native = _native()
    value = source_manifest.build_source_manifest(REPO, native_identity=native)
    assert value["status"] == "FINAL"
    paths = tuple(row["path"] for row in value["files"])
    assert paths == source_manifest.discover_production_source_paths(REPO)
    assert source_manifest.CARD_PATH in paths
    assert source_manifest.SHARED_SOURCE_PATH in paths
    assert not (REPO / source_manifest.PACKAGE_PREFIX / source_manifest.MANIFEST_NAME).exists()
    assert source_manifest.validate_source_manifest(
        value, REPO, native_identity=native
    ) == value
    stale_abi1 = {**native, "abi_version": 1}
    with pytest.raises(source_manifest.SourceManifestError):
        source_manifest.build_source_manifest(REPO, native_identity=stale_abi1)
    changed = copy.deepcopy(value)
    changed["files"][0]["sha256"] = "0" * 64
    with pytest.raises(source_manifest.SourceManifestError):
        source_manifest.validate_source_manifest(changed, REPO, native_identity=native)


def test_native_guard_requires_exact_shared_width_and_no_fallback():
    native = _native()
    calls: list[dict[str, object]] = []
    receipt = preactivity.require_direction_cpp_batched_production(
        batch_width=144,
        shared_guard=_shared_guard(native, calls),
        candidate_identity=lambda: native,
    )
    assert receipt["native_binding_sha256"] == empirical_contract.canonical_digest(native)
    assert calls == [
        {
            "component": COMPONENT,
            "backend": "cpp",
            "batch_width": 144,
            "build_root": None,
        }
    ]
    with pytest.raises(preactivity.PreactivityError):
        preactivity.require_direction_cpp_batched_production(
            batch_width=1,
            shared_guard=_shared_guard(native),
            candidate_identity=lambda: native,
        )
    altered = {**native, "python_fallback": True}
    with pytest.raises(preactivity.PreactivityError):
        preactivity.require_direction_cpp_batched_production(
            batch_width=8,
            shared_guard=_shared_guard(altered),
            candidate_identity=lambda: altered,
        )
    stale_abi1 = {**native, "abi_version": 1}
    with pytest.raises(preactivity.PreactivityError):
        preactivity.require_direction_cpp_batched_production(
            batch_width=8,
            shared_guard=_shared_guard(stale_abi1),
            candidate_identity=lambda: stale_abi1,
        )


def test_preactivity_acceptance_is_complete_and_stays_identity_free():
    native, manifest, _, receipt, acceptance = _acceptance_fixture()
    assert acceptance["accepted"] is True
    assert acceptance["materialized"] is False
    assert acceptance["master_present"] is False
    assert acceptance["empirical_objects_present"] is False
    assert acceptance["lease_issued"] is False
    assert acceptance["activity_authorized"] is False
    assert acceptance["question_relevant_output"] is False
    assert acceptance["native_reward_trace"]["capacity"] == 13
    assert "load_seconds" not in acceptance["native_binding"]
    assert preactivity.validate_preactivity_acceptance(
        acceptance,
        repository_root=REPO,
        source_manifest=manifest,
        native_identity=native,
        native_receipt=receipt,
    ) == acceptance


def _root_lease(tmp_path: Path):
    native, manifest, _, receipt, acceptance = _acceptance_fixture()
    manifest_sha = source_manifest.manifest_digest(manifest)
    acceptance_sha = empirical_contract.canonical_digest(acceptance)
    stable_native = acceptance["native_binding"]
    native_sha = empirical_contract.canonical_digest(stable_native)
    result_root = tmp_path / "TEST_TBCC"
    lease_path = tmp_path / "TEST_TBCC_ROOT_LEASE.json"
    request = lease.lease_request(
        repository_root=REPO,
        result_root=result_root,
        lease_path=lease_path,
        source_manifest_sha256=manifest_sha,
        preactivity_acceptance_sha256=acceptance_sha,
        native_binding_sha256=native_sha,
    )
    value = {
        key: request[key]
        for key in (
            "stage", "phase", "card_revision", "card_sha256", "component", "host",
            "abi_version", "source_manifest_sha256", "coordinate_proposal_digest",
            "preactivity_acceptance_sha256", "native_binding_sha256",
            "native_trace_contract_sha256", "paths",
            "execution", "resources", "counts", "complete_panel_only", "prohibitions",
        )
    }
    value.update(
        {
            "schema": lease.LEASE_SCHEMA,
            "lease_id": "TEST-TBCC-LEASE",
            "authority": "OPERATIONAL_ROOT",
            "activity_authorized": True,
            "issued_at": "2026-08-21T11:00:00Z",
            "expires_at": "2026-08-24T11:00:00Z",
        }
    )
    return value, lease_path, native, stable_native, manifest_sha, acceptance_sha, receipt


def _repair_lineage(*, native_sha: str) -> dict[str, object]:
    return {
        "schema": lease.REPAIR_LINEAGE_SCHEMA,
        "run_identity_sha256": "0" * 64,
        "origin_source_manifest_sha256": "1" * 64,
        "origin_preactivity_acceptance_sha256": "2" * 64,
        "frozen_shared_receipt_sha256": "3" * 64,
        "frozen_native_binding_sha256": native_sha,
        "frozen_coordinate_proposal_digest": "4" * 64,
        "coordinate_manifest_sha256": "5" * 64,
        "empirical_identity_sha256": "6" * 64,
        "master_commitment_sha256": "7" * 64,
        "card_revision": empirical_contract.CARD_REVISION,
        "card_sha256": empirical_contract.CARD_SHA256,
        "replicate_namespace": empirical_contract.REPLICATE_NAMESPACE,
        "domain_address_schemas_sha256": empirical_contract.canonical_digest(
            [
                {"domain": domain, "fields": list(fields)}
                for domain, fields in empirical_contract.DOMAIN_ADDRESS_SCHEMAS
            ]
        ),
        "counts_sha256": empirical_contract.canonical_digest(
            empirical_contract.PANEL_COUNTS
        ),
        "scientific_activity_started": False,
        "master_regenerated": False,
        "coordinate_domains_changed": False,
    }


def _successor_root_lease(tmp_path: Path):
    native, _, _, _, acceptance = _acceptance_fixture()
    stable_native = acceptance["native_binding"]
    native_sha = empirical_contract.canonical_digest(stable_native)
    result_root = tmp_path / "TEST_TBCC_SUCCESSOR"
    lease_path = tmp_path / "TEST_TBCC_SUCCESSOR_LEASE.json"
    current_manifest = "a" * 64
    current_acceptance = "b" * 64
    lineage = _repair_lineage(native_sha=native_sha)
    request = lease.successor_lease_request(
        repository_root=REPO,
        result_root=result_root,
        lease_path=lease_path,
        source_manifest_sha256=current_manifest,
        preactivity_acceptance_sha256=current_acceptance,
        native_binding_sha256=native_sha,
        same_coordinate_repair_lineage=lineage,
    )
    fields = (
        "stage", "phase", "card_revision", "card_sha256", "component", "host",
        "abi_version", "source_manifest_sha256", "coordinate_proposal_digest",
        "preactivity_acceptance_sha256", "native_binding_sha256",
        "native_trace_contract_sha256", "paths", "execution", "resources",
        "counts", "complete_panel_only", "prohibitions", "lease_kind",
        "same_coordinate_repair_lineage",
    )
    value = {field: request[field] for field in fields}
    value.update(
        {
            "schema": lease.SUCCESSOR_LEASE_SCHEMA,
            "lease_id": "TEST-TBCC-SUCCESSOR-LEASE",
            "authority": "OPERATIONAL_ROOT",
            "activity_authorized": True,
            "issued_at": "2026-08-21T11:00:00Z",
            "expires_at": "2026-08-24T11:00:00Z",
        }
    )
    return (
        value,
        request,
        lease_path,
        native,
        stable_native,
        current_manifest,
        current_acceptance,
        lineage,
    )


def test_lease_request_is_request_only_and_root_lease_yields_sealed_permit(tmp_path):
    value, lease_path, native, stable_native, manifest_sha, acceptance_sha, _ = _root_lease(tmp_path)
    calls: list[dict[str, object]] = []
    permit = lease.validate_root_lease(
        value,
        now=NOW,
        repository_root=REPO,
        lease_path=lease_path,
        source_manifest_sha256=manifest_sha,
        preactivity_acceptance_sha256=acceptance_sha,
        native_binding=stable_native,
        shared_guard=_shared_guard(native, calls),
    )
    permit.require_active(now=NOW)
    assert permit.workers == 4
    assert permit.native_batch_width == 144
    assert calls[0]["batch_width"] == 144
    assert set(inspect.signature(lease.ActivityPermit).parameters) >= {"_seal"}


def test_successor_request_and_permit_bind_current_source_to_frozen_coordinate(tmp_path):
    (
        value, request, lease_path, native, stable_native, current_manifest,
        current_acceptance, lineage,
    ) = _successor_root_lease(tmp_path)
    assert request["schema"] == lease.SUCCESSOR_LEASE_REQUEST_SCHEMA
    assert request["authority"] == "REQUEST_ONLY"
    assert request["lease_issued"] is False
    assert request["production_launch"] is False
    assert request["source_manifest_sha256"] == current_manifest
    assert request["preactivity_acceptance_sha256"] == current_acceptance
    assert request["same_coordinate_repair_lineage"] == lineage
    calls: list[dict[str, object]] = []
    permit = lease.validate_root_lease(
        value,
        now=NOW,
        repository_root=REPO,
        lease_path=lease_path,
        source_manifest_sha256=current_manifest,
        preactivity_acceptance_sha256=current_acceptance,
        native_binding=stable_native,
        shared_guard=_shared_guard(native, calls),
        frozen_identity_lineage=lineage,
    )
    assert permit.source_manifest_sha256 == current_manifest
    assert permit.preactivity_acceptance_sha256 == current_acceptance
    assert permit.coordinate_proposal_digest == lineage["frozen_coordinate_proposal_digest"]
    assert permit.same_coordinate_repair_lineage == lineage
    assert calls[0]["batch_width"] == 144


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("missing_lineage", "field inventory"),
        ("master_changed", "frozen identity lineage"),
        ("activity_true", "invariant"),
        ("current_source_changed", "binding"),
    ),
)
def test_successor_rejects_missing_or_changed_lineage_before_native(
    tmp_path, mutation, message
):
    (
        value, _, lease_path, native, stable_native, current_manifest,
        current_acceptance, lineage,
    ) = _successor_root_lease(tmp_path)
    supplied_manifest = current_manifest
    if mutation == "missing_lineage":
        value.pop("same_coordinate_repair_lineage")
    elif mutation == "master_changed":
        changed = copy.deepcopy(value["same_coordinate_repair_lineage"])
        changed["master_commitment_sha256"] = "8" * 64
        value["same_coordinate_repair_lineage"] = changed
    elif mutation == "activity_true":
        changed = copy.deepcopy(value["same_coordinate_repair_lineage"])
        changed["scientific_activity_started"] = True
        value["same_coordinate_repair_lineage"] = changed
    else:
        supplied_manifest = "c" * 64
    calls: list[dict[str, object]] = []
    with pytest.raises(lease.LeaseValidationError, match=message):
        lease.validate_root_lease(
            value,
            now=NOW,
            repository_root=REPO,
            lease_path=lease_path,
            source_manifest_sha256=supplied_manifest,
            preactivity_acceptance_sha256=current_acceptance,
            native_binding=stable_native,
            shared_guard=_shared_guard(native, calls),
            frozen_identity_lineage=lineage,
        )
    assert calls == []


def test_v1_lease_rejects_source_repaired_frozen_identity_before_native(tmp_path):
    value, lease_path, native, stable_native, manifest_sha, acceptance_sha, _ = _root_lease(
        tmp_path
    )
    lineage = _repair_lineage(
        native_sha=empirical_contract.canonical_digest(stable_native)
    )
    calls: list[dict[str, object]] = []
    with pytest.raises(lease.LeaseValidationError, match="V1 lease"):
        lease.validate_root_lease(
            value,
            now=NOW,
            repository_root=REPO,
            lease_path=lease_path,
            source_manifest_sha256=manifest_sha,
            preactivity_acceptance_sha256=acceptance_sha,
            native_binding=stable_native,
            shared_guard=_shared_guard(native, calls),
            frozen_identity_lineage=lineage,
        )
    assert calls == []


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("activity_authorized", False),
        ("abi_version", 1),
        ("source_manifest_sha256", "0" * 64),
        ("coordinate_proposal_digest", "0" * 64),
        ("preactivity_acceptance_sha256", "0" * 64),
        ("native_binding_sha256", "0" * 64),
        ("resources", {**lease.EXACT_RESOURCES, "independent_workers": 3}),
    ),
)
def test_malformed_root_lease_fails_before_shared_native_guard(tmp_path, field, replacement):
    value, lease_path, native, stable_native, manifest_sha, acceptance_sha, _ = _root_lease(tmp_path)
    value[field] = replacement
    calls: list[dict[str, object]] = []
    with pytest.raises(lease.LeaseValidationError):
        lease.validate_root_lease(
            value,
            now=NOW,
            repository_root=REPO,
            lease_path=lease_path,
            source_manifest_sha256=manifest_sha,
            preactivity_acceptance_sha256=acceptance_sha,
            native_binding=stable_native,
            shared_guard=_shared_guard(native, calls),
        )
    assert calls == []
