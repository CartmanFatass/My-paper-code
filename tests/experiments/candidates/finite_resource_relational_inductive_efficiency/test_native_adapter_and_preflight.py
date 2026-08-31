from __future__ import annotations

import ctypes
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import (
    ContractError, manifest_packet_contract,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import core
from experiments.candidates.finite_resource_relational_inductive_efficiency.host import (
    NativeBackendUnavailable,
    TestOnlyNativeBackend,
    Trajectory,
    admit_native_backend,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.native_adapter import (
    REQUIRED_NATIVE_CAPABILITIES,
    admit_package_native_adapter,
    build_package_native_artifact,
    load_package_native_adapter,
    package_native_artifact_path,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency import native_adapter as native_adapter_module
from experiments.candidates.finite_resource_relational_inductive_efficiency import preflight as preflight_module
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import (
    ccic_control, vqfp_controls,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency import state_codec as state_codec_module
from experiments.candidates.finite_resource_relational_inductive_efficiency.native.native_abi import (
    ABI_SYMBOLS, NATIVE_STEP_ABI,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.preflight import (
    SEED_PACKET_SCHEMA, prospective_preflight,
)


BLOCKS = tuple(f"FRRIE-FRESH-BLOCK-{index:03d}" for index in range(1, 25))


def _packet(manifest):
    return {
        "schema": SEED_PACKET_SCHEMA,
        "version": 2,
        "manifest_contract": manifest_packet_contract(manifest),
        "blocks": list(manifest["seed_blocks"]),
        "addressed_rng_roots": [f"{index:064x}" for index in range(1, 25)],
        "generation_provenance": "TEST_ONLY_DIRECT_GENERATION_PROVENANCE",
        "no_prior_use": True,
        "sealed": True,
        "complete": True,
    }


def _manifest(manifest_factory):
    """Normalize across the concurrent manifest-v2 fixture update."""
    manifest = manifest_factory()
    manifest["seed_blocks"] = list(BLOCKS)
    if hasattr(core, "INFERENCE_CONTRACT"):
        manifest.pop("generic_competence", None)
        manifest.pop("work_to_threshold", None)
        manifest["thresholds"] = deepcopy(core.THRESHOLDS)
        manifest["inference"] = deepcopy(core.INFERENCE_CONTRACT)
    return manifest


def test_missing_package_artifact_is_a_normal_fail_closed_report(manifest_factory):
    manifest = _manifest(manifest_factory)
    assert not package_native_artifact_path().exists()

    report = prospective_preflight(
        manifest,
        _packet(manifest),
        resource_ceiling=manifest["resource_ceiling"],
    )

    assert report["schema"] == "FRRIE_PROSPECTIVE_PREFLIGHT_V2"
    assert report["status"] == "BLOCKED"
    assert report["ready"] is False
    assert report["blockers"] == [
        "SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS",
        "RESOURCE_RUNTIME_CONFORMANCE_UNOBSERVED",
        "PACKAGE_NATIVE_ARTIFACT_ABSENT",
    ]
    assert report["ready_for_result_activity"] is False
    assert report["native"]["adapter_loaded"] is False
    assert report["native"]["required_capabilities"] == list(REQUIRED_NATIVE_CAPABILITIES)
    assert report["resource"]["direct_equal_to_manifest"] is True
    assert report["resource"]["observed_conformance_claimed"] is False
    assert report["resource"]["runtime_conformance_observed"] is False
    assert report["resource"]["monitor_contract"]["ceilings"] == manifest["resource_ceiling"]
    assert report["resource"]["monitor_contract"]["host_availability_snapshot"] is None
    assert report["implementation_contract"]["passed"] is True
    assert report["implementation_contract"]["source_inventory_sorted"] is True
    assert report["implementation_contract"]["all_declared_sources_present"] is True
    assert report["implementation_contract"]["origin_schedule_derived_from_runtime"] is True
    assert report["controls"]["passed"] is True
    assert report["controls"]["ccic"]["canonical_typed_wedge_m3_equal"] is True
    assert report["controls"]["egrcr"]["exact_fraction_rao_blackwell_equal"] is True
    assert report["controls"]["raw_value"]["balanced_accuracy_half"] is True
    assert report["controls"]["vqfp"]["action_seam_absent"] is True
    assert report["controls"]["vqfp"]["output_disconnected"] is True
    assert report["controls"]["fixture_contracts"]["passed"] is True
    assert report["controls"]["dependency_output_firewall"]["passed"] is True
    assert report["controls"]["scientific_result_values_read"] is False
    assert report["fresh_roots"]["created"] is False
    assert report["fresh_roots"]["sibling_children"] is True
    assert report["fresh_roots"]["common_run_parent"] == str(
        Path(manifest["roots"]["output"]).parent.resolve(strict=False)
    )
    assert report["fresh_roots"]["common_run_parent_absent"] is True
    assert report["fresh_roots"]["claim_staging_parent_absent"] is True
    assert report["fresh_roots"]["atomic_claim"] == "ONE_COMMON_PARENT_RENAME"
    assert report["fresh_roots"]["protected_inputs_and_source_areas_disjoint"] is True
    assert report["scientific_values_read"] is False
    assert report["scientific_activity_started"] is False
    assert not Path(manifest["roots"]["output"]).exists()
    assert not Path(manifest["roots"]["checkpoint"]).exists()


def test_package_adapter_rejects_fakes_callbacks_and_test_only():
    assert REQUIRED_NATIVE_CAPABILITIES == tuple(ABI_SYMBOLS)
    assert NATIVE_STEP_ABI == "FRRIE_NATIVE_STEP_ABI_V2_FP32"
    assert not {"TRAIN_PAIR", "EVALUATE", "CHECKPOINT_SAVE", "CHECKPOINT_RESTORE"}.intersection(
        REQUIRED_NATIVE_CAPABILITIES
    )
    with pytest.raises(NativeBackendUnavailable, match="package-owned"):
        admit_package_native_adapter(object())
    callback = ctypes.CFUNCTYPE(ctypes.c_int)(lambda: 0)
    with pytest.raises(NativeBackendUnavailable, match="callbacks"):
        admit_package_native_adapter(callback)
    with pytest.raises(NativeBackendUnavailable, match="TEST_ONLY"):
        admit_native_backend(TestOnlyNativeBackend(), production=True)
    with pytest.raises(NativeBackendUnavailable, match="absent"):
        load_package_native_adapter()

    test_only = TestOnlyNativeBackend()
    with pytest.raises(ContractError, match=r"\[0,7\]"):
        test_only.rollout({"trajectory_kind": "SHADOW", "step": 8})


def test_build_is_create_only_and_stale_artifact_is_not_reused(
    manifest_factory, tmp_path, monkeypatch,
):
    monkeypatch.setattr(native_adapter_module, "_NATIVE_DIR", tmp_path / "package-native")
    monkeypatch.setattr(native_adapter_module, "_FRESH_ARTIFACT_PATH", None)
    monkeypatch.setattr(native_adapter_module, "_FRESH_ARTIFACT_BYTES", None)
    monkeypatch.setattr(native_adapter_module, "_LIVE_ADAPTER", None)
    artifact = native_adapter_module.package_native_artifact_path()
    artifact.parent.mkdir()
    artifact.write_bytes(b"caller-or-stale-artifact")
    with pytest.raises(NativeBackendUnavailable, match="outside this fresh build transaction"):
        build_package_native_artifact()
    assert artifact.read_bytes() == b"caller-or-stale-artifact"

    manifest = _manifest(manifest_factory)
    report = prospective_preflight(
        manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
    )
    assert "PACKAGE_NATIVE_FRESH_BUILD_REQUIRED" in report["blockers"]
    assert report["native"]["adapter_loaded"] is False


def test_preflight_blocks_control_and_fixture_drift(manifest_factory, tmp_path, monkeypatch):
    manifest = _manifest(manifest_factory)
    original_ccic = ccic_control.canonical_ccic_fixture

    def broken_ccic():
        fixture = original_ccic()
        fixture["A"]["wedge"] = 0
        return fixture

    monkeypatch.setattr(ccic_control, "canonical_ccic_fixture", broken_ccic)
    report = prospective_preflight(
        manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
    )
    assert "CCIC_CONTROL_FAILED" in report["blockers"]
    assert report["controls"]["ccic"]["passed"] is False

    monkeypatch.setattr(ccic_control, "canonical_ccic_fixture", original_ccic)
    fixture_dir = tmp_path / "fixtures"
    shutil.copytree(preflight_module._FIXTURE_DIR, fixture_dir)
    ccic_path = fixture_dir / "ccic_control_v1.json"
    mutated = json.loads(ccic_path.read_text(encoding="utf-8"))
    mutated["expected"]["A"]["wedge"] = 0
    ccic_path.write_text(json.dumps(mutated), encoding="utf-8")
    monkeypatch.setattr(preflight_module, "_FIXTURE_DIR", fixture_dir)
    report = prospective_preflight(
        manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
    )
    assert "FIXTURE_CONTRACT_FAILED" in report["blockers"]
    assert report["controls"]["fixture_contracts"]["direct_equal"]["ccic"] is False


def test_preflight_blocks_vqfp_output_connection_and_ast_firewall(
    manifest_factory, tmp_path, monkeypatch,
):
    manifest = _manifest(manifest_factory)
    monkeypatch.setattr(vqfp_controls, "OUTPUT_DISCONNECTED", False)
    report = prospective_preflight(
        manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
    )
    assert "VQFP_CONTROL_FAILED" in report["blockers"]
    assert report["controls"]["vqfp"]["passed"] is False

    monkeypatch.setattr(vqfp_controls, "OUTPUT_DISCONNECTED", True)
    firewall_dir = tmp_path / "firewall-package"
    firewall_dir.mkdir()
    (firewall_dir / "evil.py").write_text(
        "from envs.native import production_backend\nclass ActionCodec: pass\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(preflight_module, "_FIREWALL_PACKAGE_DIR", firewall_dir)
    report = prospective_preflight(
        manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
    )
    assert "DEPENDENCY_OUTPUT_FIREWALL_FAILED" in report["blockers"]
    assert report["controls"]["dependency_output_firewall"]["passed"] is False


def test_preflight_blocks_runtime_implementation_drift(manifest_factory, monkeypatch):
    manifest = _manifest(manifest_factory)
    monkeypatch.setattr(state_codec_module, "OPTIMIZER_STATE_VERSION", 999)
    report = prospective_preflight(
        manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
    )
    assert "IMPLEMENTATION_CONTRACT_FAILED" in report["blockers"]
    assert report["implementation_contract"]["passed"] is False


def test_preflight_rejects_runtime_false_shared_pair_side_origin_claim(
    manifest_factory, monkeypatch,
):
    from experiments.candidates.finite_resource_relational_inductive_efficiency import tapes

    manifest = _manifest(manifest_factory)
    false_law = deepcopy(tapes.origin_schedule_contract())
    false_law["role_local_entity_shared_across_pair_sides"] = True
    monkeypatch.setattr(tapes, "origin_schedule_contract", lambda: deepcopy(false_law))
    report = prospective_preflight(
        manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
    )
    assert "IMPLEMENTATION_CONTRACT_FAILED" in report["blockers"]
    assert report["implementation_contract"]["passed"] is False
    assert report["implementation_contract"]["origin_schedule_derived_from_runtime"] is False


def test_preflight_rejects_claim_paths_overlapping_inputs_package_and_history(
    manifest_factory, tmp_path,
):
    manifest = _manifest(manifest_factory)
    common_parent = tmp_path / "input-overlap"
    manifest["roots"] = {
        "output": str(common_parent / "output"),
        "checkpoint": str(common_parent / "checkpoint"),
    }
    manifest["sealed_seed_packet"] = {"path": str(common_parent / "packet.json")}
    with pytest.raises(ContractError, match="protected sealed_seed_packet"):
        prospective_preflight(
            manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
        )

    manifest = _manifest(manifest_factory)
    package_parent = preflight_module._PACKAGE_DIR / "forbidden-result-parent"
    manifest["roots"] = {
        "output": str(package_parent / "output"),
        "checkpoint": str(package_parent / "checkpoint"),
    }
    with pytest.raises(ContractError, match="protected package_source_tree"):
        prospective_preflight(
            manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
        )

    manifest = _manifest(manifest_factory)
    docs_parent = preflight_module._REPO_ROOT / "docs" / "forbidden-result-parent"
    manifest["roots"] = {
        "output": str(docs_parent / "output"),
        "checkpoint": str(docs_parent / "checkpoint"),
    }
    with pytest.raises(ContractError, match="protected docs"):
        prospective_preflight(
            manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
        )


def test_preflight_requires_absolute_distinct_nonexistent_unnested_roots(manifest_factory, tmp_path):
    manifest = _manifest(manifest_factory)
    manifest["roots"] = {"output": "relative-out", "checkpoint": str(tmp_path / "checkpoint")}
    with pytest.raises(ContractError, match="absolute"):
        prospective_preflight(
            manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
        )

    manifest = _manifest(manifest_factory)
    manifest["roots"] = {
        "output": str(tmp_path / "outer"),
        "checkpoint": str(tmp_path / "outer" / "checkpoint"),
    }
    with pytest.raises(ContractError, match="nested|contain one another"):
        prospective_preflight(
            manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
        )

    manifest = _manifest(manifest_factory)
    manifest["roots"] = {
        "output": str(tmp_path / "run-a" / "output"),
        "checkpoint": str(tmp_path / "run-b" / "checkpoint"),
    }
    with pytest.raises(ContractError, match="sibling children"):
        prospective_preflight(
            manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
        )

    manifest = _manifest(manifest_factory)
    common_parent = tmp_path / "run-existing"
    manifest["roots"] = {
        "output": str(common_parent / "output"),
        "checkpoint": str(common_parent / "checkpoint"),
    }
    common_parent.mkdir()
    with pytest.raises(ContractError, match="common run parent must not already exist"):
        prospective_preflight(
            manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
        )

    manifest = _manifest(manifest_factory)
    common_parent = tmp_path / "run-stale"
    manifest["roots"] = {
        "output": str(common_parent / "output"),
        "checkpoint": str(common_parent / "checkpoint"),
    }
    stale_staging = common_parent.with_name(common_parent.name + ".FRRIE_CLAIM_V2.tmp")
    stale_staging.mkdir()
    with pytest.raises(ContractError, match="stale V2 common-run staging"):
        prospective_preflight(
            manifest, _packet(manifest), resource_ceiling=manifest["resource_ceiling"]
        )


@pytest.mark.parametrize("bad_root", ["f" * 63, "F" * 64, "g" * 64])
def test_preflight_inspects_exact_seed_root_shape_without_using_rng(manifest_factory, bad_root):
    manifest = _manifest(manifest_factory)
    packet = _packet(manifest)
    packet["addressed_rng_roots"][7] = bad_root
    with pytest.raises(ContractError, match="lowercase-hex 256-bit"):
        prospective_preflight(
            manifest, packet, resource_ceiling=manifest["resource_ceiling"]
        )


def test_preflight_rejects_duplicate_addressed_rng_roots(manifest_factory):
    manifest = _manifest(manifest_factory)
    packet = _packet(manifest)
    packet["addressed_rng_roots"][9] = packet["addressed_rng_roots"][8]
    with pytest.raises(ContractError, match="24 unique ordered"):
        prospective_preflight(
            manifest, packet, resource_ceiling=manifest["resource_ceiling"]
        )


def test_preflight_rejects_legacy_v1_seed_packet(manifest_factory):
    manifest = _manifest(manifest_factory)
    packet = _packet(manifest)
    packet["schema"] = "FRRIE_SEALED_SEED_PACKET_V1"
    packet["version"] = 1
    with pytest.raises(ContractError, match="schema/version mismatch"):
        prospective_preflight(
            manifest, packet, resource_ceiling=manifest["resource_ceiling"]
        )


def test_preflight_requires_direct_resource_equality(manifest_factory):
    manifest = _manifest(manifest_factory)
    ceiling = deepcopy(manifest["resource_ceiling"])
    ceiling["wall_seconds"] += 1
    with pytest.raises(ContractError, match="directly equal"):
        prospective_preflight(manifest, _packet(manifest), resource_ceiling=ceiling)


def test_trajectory_retains_roles_masks_and_exact_endpoint_primitives():
    backend = TestOnlyNativeBackend()
    request = {
        "trajectory_kind": "SHADOW",
        "purpose": "TEST_ONLY",
        "intervention": "TEST_ONLY",
        "roster": 3,
        "seed_block": "TEST_ONLY",
        "update": 0,
        "episode": 0,
        "tape_contract": {
            "schema": "FRRIE_ADDRESSED_TAPE_V1",
            "seed_block": "TEST_ONLY",
            "purpose": "TEST_ONLY",
            "roster": 3,
            "update": 0,
            "episode": 0,
        },
    }
    raw = backend.rollout(request)
    trajectory = Trajectory.from_backend(raw, "SHADOW", request)
    assert trajectory.roles == tuple(raw["roles"])
    assert trajectory.legal_role_masks == tuple(raw["legal_role_masks"])
    assert trajectory.endpoint_primitives == {"dw": 0, "de": 0, "waste": 0.0}

    raw["endpoint_primitives"] = {"dw": 0, "de": 0, "waste": 0.0, "return": 0.1}
    with pytest.raises(ContractError, match="exactly dw, de, and waste"):
        Trajectory.from_backend(raw, "SHADOW", request)
