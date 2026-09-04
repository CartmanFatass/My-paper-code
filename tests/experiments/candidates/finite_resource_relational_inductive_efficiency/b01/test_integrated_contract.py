from __future__ import annotations

import inspect
import json
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
from experiments.candidates.finite_resource_relational_inductive_efficiency.host import native_endpoint
from experiments.candidates.finite_resource_relational_inductive_efficiency.native_adapter import (
    _validate_vcvars_compiler, _windows_build_environment, _windows_vcvars64,
    package_native_artifact_path,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import LEGAL_ACTION_INDICES
from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import FRRIEActorCritic
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
    OPTIMIZER_PAYLOAD_BYTE_COUNT, OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.checkpoint import encode_checkpoint
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import (
    derive_native_primitive_endpoint,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import (
    LEARNED_ARMS, TEST_SEED_LABEL,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError, bind_invocation_resource, canonical_json_bytes, make_test_manifest,
    named_compute_profile,
)
import experiments.candidates.finite_resource_relational_inductive_efficiency.b01.integrated_test as integrated_module
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.integrated_test import (
    _publish_integrated_test_root, exact_integrated_test_contract,
    integrated_telemetry_stage_order, launch_integrated_test, run_integrated_test_worker,
    validate_integrated_test_artifact,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.seed_packet import (
    create_test_seed_packet, read_test_seed_packet,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.tapes import evaluation_tape
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer import (
    create_paired_parameter_state_container_once,
)


def test_integrated_contract_admits_before_build_and_never_invents_update1_checkpoint():
    contract = exact_integrated_test_contract()
    stages = contract["stage_order"]
    assert stages.index("FRESH_4GIB_MEMORY_ADMISSION") < stages.index("NATIVE_BUILD")
    assert stages.index("NATIVE_BUILD") < stages.index(
        "CANONICAL_NATIVE_LOAD_AND_PAIRED_RUNTIME_CREATE"
    )
    assert stages.index("CHECKPOINT0_CREATE_READBACK_DECODE_TEMPORARY_RESTORE") < stages.index(
        "REAL_NATIVE_WIDTH32_BOTH_ARM_COLLECTION"
    )
    assert contract["curve_checkpoint"] == 0
    assert contract["update1_state_role"] == "NONCHECKPOINT_NONRESUMABLE_DIAGNOSTIC_ONLY"
    assert all("CHECKPOINT1" not in stage and "UPDATE1_CHECKPOINT" not in stage for stage in stages)
    assert contract["representative_eval"]["satisfies_production_inventory"] is False
    assert contract["scientific_values"] is None
    assert contract["production_roots_created"] is False
    assert contract["artifact_role"] == "INTEGRATED_RUNTIME_SMOKE_NOT_INDEPENDENTLY_REPLAYABLE"
    assert contract["implementation_critical"] is False
    assert contract["production_readiness"] is False


def test_native_primitive_endpoint_uses_exact_cpp_fp32_waste_and_rejects_tamper():
    one_third = float(np.float32(np.float32(1) / np.float32(3)))
    receipt = derive_native_primitive_endpoint(
        dw=2, de=1, radio_actions=3, waste_actions=1, abi_waste=one_third,
    )
    assert receipt.abi_waste == one_third
    assert receipt.abi_waste_f32_bits_u32 == int(
        np.asarray([one_third], dtype="<f4").view("<u4")[0]
    )
    assert derive_native_primitive_endpoint(
        dw=2, de=1, radio_actions=3, waste_actions=1, abi_waste=one_third,
        observed_return=receipt.endpoint,
    ) == receipt

    zero = derive_native_primitive_endpoint(
        dw=0, de=0, radio_actions=0, waste_actions=0, abi_waste=0.0,
    )
    assert zero.abi_waste_f32_bits_u32 == 0
    with pytest.raises(B01ContractError, match="count/support"):
        derive_native_primitive_endpoint(
            dw=0, de=0, radio_actions=0, waste_actions=1, abi_waste=0.0,
        )
    with pytest.raises(B01ContractError, match="waste bits"):
        derive_native_primitive_endpoint(
            dw=2, de=1, radio_actions=3, waste_actions=2, abi_waste=one_third,
        )
    drifted_waste = float(np.nextafter(np.float32(one_third), np.float32(np.inf)))
    with pytest.raises(B01ContractError, match="waste bits"):
        derive_native_primitive_endpoint(
            dw=2, de=1, radio_actions=3, waste_actions=1, abi_waste=drifted_waste,
        )
    with pytest.raises(B01ContractError, match="endpoint binary64"):
        derive_native_primitive_endpoint(
            dw=2, de=1, radio_actions=3, waste_actions=1, abi_waste=one_third,
            observed_return=float(np.nextafter(receipt.endpoint, np.inf)),
        )


def test_integrated_runtime_has_no_public_adapter_or_model_injection():
    assert list(inspect.signature(run_integrated_test_worker).parameters) == ["root"]
    assert list(inspect.signature(launch_integrated_test).parameters) == ["root"]


def _optimizer(step: int) -> bytes:
    value = struct.pack(
        "<8sII", OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
        OPTIMIZER_PAYLOAD_BYTE_COUNT,
    ) + bytes(OPTIMIZER_PAYLOAD_BYTE_COUNT)
    result = bytearray(value)
    result[-8:] = struct.pack("<Q", step)
    return bytes(result)


def _receipt():
    return {
        "schema_version": 1, "captured_at": "2026-09-01T00:00:00Z",
        "assessed_at": "2026-09-01T00:00:01Z", "measurement_source": "STATIC_TEST",
        "minimum_available_bytes": 4 * 1024**3, "available_physical_bytes": 8 * 1024**3,
        "cgroup_memory_max_bytes": None, "cgroup_memory_current_bytes": None,
        "cgroup_headroom_bytes": None, "effective_available_bytes": 8 * 1024**3,
        "physical_floor_pass": True, "effective_floor_pass": True,
        "passed": True, "failure_reasons": [],
    }


def _zero_work():
    row = {
        "training_update": 0, "episodes": 0, "environment_slots": 0,
        "backward_calls": 0, "adam_steps": 0, "native_batch_calls": 0,
        "native_batch_ledger": {
            "reset_calls": 0, "observe_calls": 0, "step_calls": 0,
            "environment_slots": 0,
        }, "worker_count": 4, "thread_count": 1,
    }
    return {arm: {**row, "native_batch_ledger": dict(row["native_batch_ledger"])} for arm in LEARNED_ARMS}


def _static_loss_reduction_receipt():
    one = int(np.asarray([1.0], dtype="<f4").view("<u4")[0])
    zero = int(np.asarray([0.0], dtype="<f4").view("<u4")[0])
    return {
        "schema": "FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1",
        "component_order": ["loss", "score", "entropy", "critic"],
        "roster_order": list((9, 15) * 32),
        "per_episode_u32_bits": [[one, one, zero, zero] for _ in range(64)],
        "reduction_law": "PYTHON_SUM_INT0_LEFT_FOLD_THEN_DIVIDE_FLOAT64_LITERAL_64",
        "divisor": 64, "dtype": "CPU_FP32",
        "aggregate_u32_bits": [one, one, zero, zero],
    }


def _fake_deep_artifact(tmp_path: Path):
    root = (tmp_path / "integrated-final").resolve()
    for name in ("output", "checkpoint", "scratch"):
        (root / name).mkdir(parents=True, exist_ok=True)
    packet_path = (tmp_path / "integrated-final.test-seed-packet.json").resolve()
    create_test_seed_packet(packet_path)
    repository = Path(__file__).resolve().parents[5]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--",
         "experiments/candidates/finite_resource_relational_inductive_efficiency",
         "scripts/hmasd_resource_preflight.py"], cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.splitlines()
    manifest = make_test_manifest(
        seed_packet_path=packet_path,
        roots={name: str((root / name).resolve()) for name in ("output", "checkpoint", "scratch")},
        compute=named_compute_profile(), base_commit=head,
        worktree_state="DIRTY_UNCOMMITTED_TEST_ONLY",
    )
    receipt = _receipt()
    receipt_path = (tmp_path / "integrated-final.admit-memory.json").resolve()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    binding = bind_invocation_resource(
        invocation_id="STATIC-INTEGRATED-TEST", operation="TEST_SMOKE",
        receipt_path=receipt_path, receipt=receipt, test_only=True,
    )
    phy, edge = initialize_paired_arms(AddressedRNG(b"Q" * 32), TEST_SEED_LABEL)
    state = phy.parameter_bytes()
    assert state == edge.parameter_bytes()
    checkpoint = encode_checkpoint(
        manifest=manifest, seed_label=TEST_SEED_LABEL, update=0,
        arm_state_bytes={arm: state for arm in LEARNED_ARMS},
        optimizer_state_bytes={arm: _optimizer(0) for arm in LEARNED_ARMS},
        work=_zero_work(), invocation_binding=binding,
        projection_audit={
            "first_tight_contact_update": None, "precontact_full_state_equal": True,
            "tight_projection_changed_coordinates": 0, "wide_boundary_contact": False,
            "maximum_tight_overshoot": 0.0, "cumulative_tight_displacement": 0.0,
        },
    )
    checkpoint_path = root / "checkpoint" / "checkpoint-000.json"
    checkpoint_path.write_bytes(checkpoint)
    diagnostic = create_paired_parameter_state_container_once(
        root / "output" / "update-001-diagnostic-state",
        seed_label=TEST_SEED_LABEL, update=1, phy_state_bytes=state,
        edge_state_bytes=state, test_only_component=True,
    )

    beta = np.frombuffer(state[107_928:108_000], dtype="<f4")
    direct_update = {}
    for arm in LEARNED_ARMS:
        files = {}
        values = {
            "model_pre_bytes": state, "optimizer_pre_bytes": _optimizer(0),
            "model_post_adam_bytes": state, "optimizer_post_adam_bytes": _optimizer(1),
            "model_post_projection_bytes": state,
            "optimizer_post_projection_bytes": _optimizer(1),
        }
        for field, data in values.items():
            relative = Path("direct-update") / arm / f"{field}.bin"
            path = root / "output" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            files[field] = {"relative_path": relative.as_posix(), "byte_count": len(data)}
        direct_update[arm] = {
            "scalars": {
                "arm": arm, "update": 1, "loss": 1.0, "score": 1.0,
                "entropy": 0.0, "critic": 0.0, "preclip_global_norm": 0.0,
                "loss_reduction_receipt": _static_loss_reduction_receipt(),
                "backward_calls": 1, "adam_steps": 1,
                "projection_changed_indices": [], "box_contact": False,
                "maximum_box_overshoot": 0.0, "projection_displacement": 0.0,
                "preprojection_beta": beta.tolist(), "postprojection_beta": beta.tolist(),
                "optimizer_moments_unchanged_by_projection": True,
            },
            "direct_state_files": files,
        }

    import torch
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        parity_inputs = {}
        for roster in (9, 15):
            parity_uniforms = np.stack([
                evaluation_tape(
                    bytes.fromhex(read_test_seed_packet(packet_path)["roots_hex"][0]),
                    seed_label=TEST_SEED_LABEL, roster=roster, episode=episode,
                ).action_uniform
                for episode in range(32)
            ]).astype("<f4")
            parity_inputs[roster] = {
                "observations": np.zeros((32, 12, roster, 22), dtype="<f4"),
                "roles": np.broadcast_to(
                    np.repeat(np.arange(3, dtype="<i8"), roster // 3), (32, roster),
                ).copy(),
                "action_uniforms": parity_uniforms,
            }
        parity = integrated_module._policy_width32_parity_from_inputs(
            FRRIEActorCritic(phy), parity_inputs,
        )
        parity.update({
            "input_source": "DIRECT_COLLECTED_UPDATE_PRESTATE_OBSERVATIONS_AND_ADDRESSED_TAPES",
            "model_state_stage": "UPDATE_PRESTATE_BEFORE_OPTIMIZER_STEP",
        })
        parity_index = integrated_module._write_policy_parity_arrays(root / "output", parity)
    finally:
        torch.set_num_threads(previous_threads)

    packet = read_test_seed_packet(packet_path)
    test_root = bytes.fromhex(packet["roots_hex"][0])
    uniforms = np.stack([
        evaluation_tape(test_root, seed_label=TEST_SEED_LABEL, roster=6, episode=episode).action_uniform
        for episode in range(32)
    ]).astype("<f4")
    roles = np.broadcast_to(np.repeat(np.arange(3, dtype="<i8"), 2), (32, 12, 6)).copy()
    masks_one = np.zeros((6, 6), dtype=np.uint8)
    probs_one = np.zeros((6, 6), dtype=np.float32)
    for entity, role in enumerate(roles[0, 0]):
        legal = list(LEGAL_ACTION_INDICES[int(role)])
        masks_one[entity, legal] = 1
        probs_one[entity, legal] = np.float32(1.0 / len(legal))
    masks = np.broadcast_to(masks_one, (32, 12, 6, 6)).copy()
    probabilities = np.broadcast_to(probs_one, (32, 12, 6, 6)).copy()
    actions = (uniforms[..., None] >= np.cumsum(probabilities, axis=3)).sum(axis=3).clip(max=5).astype(np.uint8)
    arrays = {
        "observations": np.zeros((32, 12, 6, 22), dtype="<f4"),
        "probabilities": probabilities, "actions": actions,
        "roles": roles, "masks": masks, "action_uniforms": uniforms,
        "returns": np.full(32, native_endpoint(0, 0, 0.0), dtype="<f8"),
    }
    axes = {
        "observations": ["episode", "slot", "entity", "observation_field"],
        "probabilities": ["episode", "slot", "entity", "action"],
        "actions": ["episode", "slot", "entity"], "roles": ["episode", "slot", "entity"],
        "masks": ["episode", "slot", "entity", "action"],
        "action_uniforms": ["episode", "slot", "entity"], "returns": ["episode"],
    }
    descriptors = {}
    replay_descriptors = {}
    for name, array in arrays.items():
        relative = Path("representative-eval") / f"{name}.bin"
        path = root / "output" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(array.tobytes())
        descriptors[name] = {
            "relative_path": relative.as_posix(), "dtype": array.dtype.str,
            "shape": list(array.shape), "order": "C", "byte_count": array.nbytes,
            "axis_order": axes[name],
        }
        replay_relative = Path("representative-eval-live-replay") / f"{name}.bin"
        replay_path = root / "output" / replay_relative
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        replay_path.write_bytes(array.tobytes())
        replay_descriptors[name] = {
            **descriptors[name], "relative_path": replay_relative.as_posix(),
        }
    primitive = {
        "dw": 0, "de": 0, "waste": 0.0, "duplicate": 0, "expired": 0,
        "collision": 0, "empty_radio": 0, "radio_actions": 0,
        "waste_actions": 0, "successful_deliveries": 0,
    }
    audit = {
        "schema": "FRRIE_B01_BATCH_COLLECTION_AUDIT_V1", "update": 1,
        "factual_episodes": 64, "native_width": 32, "factual_slots": 768,
        "factual_suffix_audit_slots": 1_248, "nonfactual_suffix_slots": 2_912,
        "total_environment_slots": 4_928, "factual_suffixes_audited": 192,
        "alternative_suffixes_executed": 448, "factual_trace_direct_equal": True,
        "model_bytes_unchanged": True, "torch_actor_batch_calls": 25,
        "torch_critic_batch_calls": 2, "maximum_actor_lanes": 32,
        "shared_model_worker_count": 1,
    }
    index = {
        "schema": "FRRIE_B01_INTEGRATED_TEST_TYPED_INDEX_V1", "seed_label": TEST_SEED_LABEL,
        "update": 1, "arm_collection_audits": {arm: dict(audit) for arm in LEARNED_ARMS},
        "direct_update": direct_update,
        "checkpoint0": {
            "relative_path": "checkpoint/checkpoint-000.json",
            "historical_staging_readback_decode_temporary_restore": {"historical": True},
            "final_locator_revalidation_required": True,
        },
        "update1_diagnostic_state": {
            "relative_path": "output/update-001-diagnostic-state/index.json",
            "historical_staging_container_path": diagnostic["container_path"],
            "resume_or_evaluation_capable": False, "final_locator_revalidation_required": True,
        },
        "parameter_distance_update1": {
            "available": False,
            "availability_reason": "TEST_PREFIX_PRE_TIGHT_CONTACT_KAPPA_UNRESOLVED",
            "raw_relative_path": None, "literal_readback_validated": False,
        },
        "policy_width32_parity": parity_index,
        "representative_eval": {
            "arrays": descriptors, "primitives": [dict(primitive) for _ in range(32)],
            "work_ledger": {
                "lanes": 32, "native_reset_calls": 1, "native_observe_calls": 12,
                "native_step_calls": 12, "environment_slots": 384,
            },
            "tape_binding": {
                "schema": "FRRIE_B01_INTEGRATED_TEST_EVAL_ADDRESS_V1",
                "seed_label": TEST_SEED_LABEL, "purpose": "EVALUATE", "roster": 6,
                "episodes": list(range(32)),
                "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
                "checkpoint_and_model_state_role": "METADATA_ONLY_OPERATIVE_UPDATE1_TEST",
                "checkpoint_independent": True, "fixed_test_root_from_packet": True,
            }, "satisfies_production_inventory": False,
        },
        "representative_eval_live_replay": {
            "arrays": replay_descriptors,
            "primitives": [dict(primitive) for _ in range(32)],
            "work_ledger": {
                "lanes": 32, "native_reset_calls": 1, "native_observe_calls": 12,
                "native_step_calls": 12, "environment_slots": 384,
            },
            "tape_binding": {
                "schema": "FRRIE_B01_INTEGRATED_TEST_EVAL_ADDRESS_V1",
                "seed_label": TEST_SEED_LABEL, "purpose": "EVALUATE", "roster": 6,
                "episodes": list(range(32)),
                "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
                "checkpoint_and_model_state_role": "METADATA_ONLY_OPERATIVE_UPDATE1_TEST",
                "checkpoint_independent": True, "fixed_test_root_from_packet": True,
            },
            "same_live_model_and_test_tapes_as_representative_eval": True,
            "direct_arrays_primitives_and_work_equal": True,
            "independent_replay": False, "satisfies_production_inventory": False,
        }, "complete": True,
    }
    (root / "output" / "typed-index.json").write_bytes(canonical_json_bytes(index))
    retained = root / "output" / "native-build-artifact.dll"
    retained.write_bytes(b"STATIC-RETAINED-NATIVE")
    vcvars = _windows_vcvars64()
    compiler, _ = _windows_build_environment(vcvars)
    compiler_path = _validate_vcvars_compiler(vcvars, compiler)
    def telemetry_row(*, wall=0.01, cpu=0.005, samples=2):
        core = cpu / wall if wall else 0.0
        return {
            "wall_seconds": wall, "cpu_seconds": cpu,
            "cpu_core_equivalents": core,
            "host_cpu_occupancy_fraction": core / 8,
            "logical_cpu_count": 8, "peak_rss_bytes": 1,
            "scratch_peak_bytes": 0, "durable_peak_bytes": 1,
            "io_read_transfer_bytes": 0, "io_write_transfer_bytes": 1,
            "peak_process_count": 1, "peak_thread_count": 1,
            "sample_count": samples,
        }

    telemetry = {
        "schema": "FRRIE_B01_A_RECON_PROCESS_TREE_TELEMETRY_V2",
        "stages": [
            {"stage_id": stage, "telemetry": telemetry_row()}
            for stage in integrated_telemetry_stage_order()
        ],
        "end_to_end": telemetry_row(wall=1.0, cpu=0.5, samples=16),
    }
    artifact = {
        "schema": "FRRIE_B01_INTEGRATED_ONE_UPDATE_TEST_ARTIFACT_V1",
        "contract": exact_integrated_test_contract(), "manifest_contract": manifest,
        "invocation_binding": binding, "typed_index_relative_path": "output/typed-index.json",
        "external_create_once_locators": {
            "test_seed_packet": str(packet_path), "memory_admission_receipt": str(receipt_path),
        },
        "native_build_artifact": {
            "historical_package_path": str(package_native_artifact_path()),
            "retained_relative_path": "output/native-build-artifact.dll",
            "byte_count": retained.stat().st_size,
            "cleaned_by_outer_launcher_after_child_exit": True,
        },
        "source_and_toolchain": {
            "actual_head": head,
            "scoped_source_status": {
                "schema": "FRRIE_B01_SCOPED_SOURCE_STATUS_V1",
                "scope": [
                    "experiments/candidates/finite_resource_relational_inductive_efficiency",
                    "scripts/hmasd_resource_preflight.py",
                ],
                "porcelain_v1_untracked_all": status,
            },
            "vcvars64_path": str(vcvars), "resolved_compiler_path": str(compiler_path),
            "vc_tools_root": str((vcvars.resolve(strict=True).parents[2] / "Tools").resolve()),
            "compiler_within_vc_tools": True,
        },
        "execution_identity": {
            "child_argv": ["python", "-m", "...", "--worker"],
            "child_cwd": str(repository),
            "worker_module": "experiments.candidates.finite_resource_relational_inductive_efficiency.b01.integrated_test",
        },
        "process_tree_telemetry": telemetry, "scientific_values": None,
        "artifact_role": "INTEGRATED_RUNTIME_SMOKE_NOT_INDEPENDENTLY_REPLAYABLE",
        "implementation_critical": False, "production_readiness": False,
        "result_bearing": False, "production_roots_created": False,
        "production_panel_token_minted": False, "performance_disposition": "REPAIR_REQUIRED",
        "performance_blockers": exact_integrated_test_contract()["performance_blockers"],
        "complete": True,
    }
    (root / "artifact.json").write_bytes(canonical_json_bytes(artifact))
    return root, artifact, index


def test_deep_static_artifact_and_tamper_matrix(tmp_path):
    root, artifact, index = _fake_deep_artifact(tmp_path)
    assert validate_integrated_test_artifact(root)["complete"] is True

    checkpoint = root / "checkpoint" / "checkpoint-000.json"
    original = checkpoint.read_bytes()
    checkpoint.write_bytes(original + b"x")
    with pytest.raises(B01ContractError):
        validate_integrated_test_artifact(root)
    checkpoint.write_bytes(original)

    artifact_path = root / "artifact.json"
    bad_artifact = json.loads(artifact_path.read_text())
    bad_artifact["external_create_once_locators"]["test_seed_packet"] = str(tmp_path / "absent")
    artifact_path.write_bytes(canonical_json_bytes(bad_artifact))
    with pytest.raises((B01ContractError, FileNotFoundError)):
        validate_integrated_test_artifact(root)
    artifact_path.write_bytes(canonical_json_bytes(artifact))

    receipt_path = Path(artifact["external_create_once_locators"]["memory_admission_receipt"])
    receipt_original = receipt_path.read_bytes()
    receipt_bad = json.loads(receipt_original)
    receipt_bad["available_physical_bytes"] -= 1
    receipt_path.write_text(json.dumps(receipt_bad), encoding="utf-8")
    with pytest.raises(B01ContractError, match="receipt"):
        validate_integrated_test_artifact(root)
    receipt_path.write_bytes(receipt_original)

    bad_artifact = json.loads(artifact_path.read_text())
    bad_artifact["typed_index_relative_path"] = "../typed-index.json"
    artifact_path.write_bytes(canonical_json_bytes(bad_artifact))
    with pytest.raises(B01ContractError, match="relative locator"):
        validate_integrated_test_artifact(root)
    artifact_path.write_bytes(canonical_json_bytes(artifact))

    probability_path = root / "output" / index["representative_eval"]["arrays"]["probabilities"]["relative_path"]
    probability_original = probability_path.read_bytes()
    probability = bytearray(probability_original)
    probability[:4] = np.asarray([np.nan], dtype="<f4").tobytes()
    probability_path.write_bytes(probability)
    with pytest.raises(B01ContractError, match="probabilities"):
        validate_integrated_test_artifact(root)
    probability_path.write_bytes(probability_original)

    mask_path = root / "output" / index["representative_eval"]["arrays"]["masks"]["relative_path"]
    mask_original = mask_path.read_bytes()
    mask = bytearray(mask_original)
    mask[0] ^= 1
    mask_path.write_bytes(mask)
    with pytest.raises(B01ContractError, match="legal masks"):
        validate_integrated_test_artifact(root)
    mask_path.write_bytes(mask_original)

    action_path = root / "output" / index["representative_eval"]["arrays"]["actions"]["relative_path"]
    action_original = action_path.read_bytes()
    action = bytearray(action_original)
    action[0] = (action[0] + 1) % 6
    action_path.write_bytes(action)
    with pytest.raises(B01ContractError, match="actions"):
        validate_integrated_test_artifact(root)
    action_path.write_bytes(action_original)

    index_path = root / "output" / "typed-index.json"
    bad_index = json.loads(index_path.read_text())
    bad_index["representative_eval"]["work_ledger"]["environment_slots"] = 383
    index_path.write_bytes(canonical_json_bytes(bad_index))
    with pytest.raises(B01ContractError, match="work/primitives"):
        validate_integrated_test_artifact(root)
    index_path.write_bytes(canonical_json_bytes(index))

    bad_index = json.loads(index_path.read_text())
    bad_index["arm_collection_audits"]["PHY_TRUST"]["total_environment_slots"] = 4_927
    index_path.write_bytes(canonical_json_bytes(bad_index))
    with pytest.raises(B01ContractError, match="collection work"):
        validate_integrated_test_artifact(root)
    index_path.write_bytes(canonical_json_bytes(index))

    bad_index = json.loads(index_path.read_text())
    bad_index["arm_collection_audits"]["PHY_TRUST"]["factual_suffixes_audited"] = 96
    bad_index["arm_collection_audits"]["PHY_TRUST"]["alternative_suffixes_executed"] = 224
    index_path.write_bytes(canonical_json_bytes(bad_index))
    with pytest.raises(B01ContractError, match="collection work"):
        validate_integrated_test_artifact(root)
    index_path.write_bytes(canonical_json_bytes(index))

    bad_artifact = json.loads(artifact_path.read_text())
    bad_artifact["process_tree_telemetry"]["stages"].reverse()
    artifact_path.write_bytes(canonical_json_bytes(bad_artifact))
    with pytest.raises(B01ContractError, match="stage inventory"):
        validate_integrated_test_artifact(root)
    artifact_path.write_bytes(canonical_json_bytes(artifact))

    bad_artifact = json.loads(artifact_path.read_text())
    bad_artifact["process_tree_telemetry"]["end_to_end"]["cpu_core_equivalents"] = 99.0
    artifact_path.write_bytes(canonical_json_bytes(bad_artifact))
    with pytest.raises(B01ContractError, match="CPU denominator"):
        validate_integrated_test_artifact(root)
    artifact_path.write_bytes(canonical_json_bytes(artifact))

    parity_path = root / "output" / index["policy_width32_parity"]["arrays_by_roster"]["15"][
        "logits"
    ]["relative_path"]
    parity_original = parity_path.read_bytes()
    parity_bad = bytearray(parity_original)
    parity_bad[0] ^= 1
    parity_path.write_bytes(parity_bad)
    with pytest.raises(B01ContractError, match="parity recomputation"):
        validate_integrated_test_artifact(root)
    parity_path.write_bytes(parity_original)

    replay_path = root / "output" / index["representative_eval_live_replay"]["arrays"][
        "actions"
    ]["relative_path"]
    replay_original = replay_path.read_bytes()
    replay_bad = bytearray(replay_original)
    replay_bad[0] ^= 1
    replay_path.write_bytes(replay_bad)
    with pytest.raises(B01ContractError, match="live eval replay direct arrays"):
        validate_integrated_test_artifact(root)
    replay_path.write_bytes(replay_original)


def test_postpublish_validation_failure_moves_exact_root_to_incomplete(monkeypatch, tmp_path):
    staging = tmp_path / "wave.creating"
    root = tmp_path / "wave"
    incomplete = tmp_path / "wave.incomplete"
    staging.mkdir()
    (staging / "marker").write_text("direct", encoding="utf-8")
    monkeypatch.setattr(
        integrated_module, "validate_integrated_test_artifact",
        lambda root: (_ for _ in ()).throw(B01ContractError("deliberate final failure")),
    )
    with pytest.raises(B01ContractError, match="deliberate final"):
        _publish_integrated_test_root(staging, root, incomplete)
    assert not root.exists() and incomplete.is_dir()
    assert (incomplete / "marker").read_text(encoding="utf-8") == "direct"


def test_outer_refuses_preexisting_sidecar_and_cleans_only_fresh_owned_files(monkeypatch, tmp_path):
    native = (tmp_path / "_native" / "frrie_ridgegate2z_external.dll").resolve()
    native.parent.mkdir()
    monkeypatch.setattr(integrated_module, "package_native_artifact_path", lambda: native)
    sidecar = native.with_suffix(".obj")
    sidecar.write_bytes(b"preexisting")
    with pytest.raises(B01ContractError, match="pre-existing"):
        launch_integrated_test(tmp_path / "refused")
    sidecar.unlink()

    def fake_run(command, check, cwd, timeout):
        assert timeout == 1_200
        native.write_bytes(b"fresh")
        native.with_suffix(".pdb").write_bytes(b"fresh-sidecar")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(integrated_module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        integrated_module, "validate_integrated_test_artifact", lambda root: {"complete": True},
    )
    assert launch_integrated_test(tmp_path / "accepted") == 0
    assert not list(native.parent.glob(f"{native.stem}*"))

    postcleanup_root = tmp_path / "postcleanup-invalid"

    def fake_run_postcleanup(command, check, cwd, timeout):
        native.write_bytes(b"fresh")
        postcleanup_root.mkdir()
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(integrated_module.subprocess, "run", fake_run_postcleanup)
    monkeypatch.setattr(
        integrated_module, "validate_integrated_test_artifact",
        lambda root: (_ for _ in ()).throw(B01ContractError("retained failure")),
    )
    with pytest.raises(B01ContractError, match="retained failure"):
        launch_integrated_test(postcleanup_root)
    assert not postcleanup_root.exists()
    assert postcleanup_root.with_name(postcleanup_root.name + ".incomplete").is_dir()
    assert not list(native.parent.glob(f"{native.stem}*"))

    timed_root = tmp_path / "timed"

    def fake_timeout(command, check, cwd, timeout):
        native.write_bytes(b"fresh-timeout")
        staging = timed_root.with_name(timed_root.name + ".creating")
        staging.mkdir()
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(integrated_module.subprocess, "run", fake_timeout)
    with pytest.raises(B01ContractError, match="1200-second"):
        launch_integrated_test(timed_root)
    assert not list(native.parent.glob(f"{native.stem}*"))
    assert not timed_root.with_name(timed_root.name + ".creating").exists()
    assert timed_root.with_name(timed_root.name + ".incomplete").is_dir()


def test_outer_cleanup_failure_quarantines_published_final_before_raising(monkeypatch, tmp_path):
    native = (tmp_path / "cleanup-native" / "frrie_ridgegate2z_external.dll").resolve()
    native.parent.mkdir()
    root = tmp_path / "cleanup-failure-final"
    monkeypatch.setattr(integrated_module, "package_native_artifact_path", lambda: native)

    def fake_run(command, check, cwd, timeout):
        native.write_bytes(b"fresh-owned-native")
        root.mkdir()
        (root / "artifact.json").write_text("published", encoding="utf-8")
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(integrated_module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        integrated_module, "_unlink_owned_native_file",
        lambda path: (_ for _ in ()).throw(PermissionError("deliberate unlink refusal")),
    )
    with pytest.raises(B01ContractError, match="cleanup failed; final root quarantined"):
        launch_integrated_test(root)
    incomplete = root.with_name(root.name + ".incomplete")
    assert not root.exists() and incomplete.is_dir()
    assert (incomplete / "artifact.json").read_text(encoding="utf-8") == "published"
    assert native.exists()
    native.unlink()
