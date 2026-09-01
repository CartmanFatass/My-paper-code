"""Create-once TEST-only one-update native/trainer/checkpoint/eval assessment.

The outer launcher owns and cleans only the fresh package-native DLL created by
its child.  The child retains direct non-result evidence under one unique TEST
root.  This module exposes no production seed creator or result command.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..arms import initialize_paired_arms
from ..native_adapter import (
    build_package_native_artifact, load_package_native_adapter,
    package_native_artifact_path, _windows_vcvars64, _windows_build_environment,
    _validate_vcvars_compiler,
)
from ..policy import FRRIEActorCritic
from ..policy import LEGAL_ACTION_INDICES
from ..rng import AddressedRNG
from ..state_codec import OPTIMIZER_STATE_BYTE_COUNT, encode_optimizer_state
from ..training import make_optimizer, validate_loss_reduction_receipt
from ..contracts.core import ContractError
from .batch_collector import _collect_b01_test_arm_update, make_test_update_inputs
from .checkpoint import (
    decode_checkpoint, reopen_decode_restore_test_checkpoint0, snapshot_runtime,
)
from .constants import LEARNED_ARMS, TEST_SEED_LABEL, TEST_SEED_LABELS
from .contract import (
    B01ContractError, bind_invocation_resource, canonical_json_bytes,
    make_test_manifest, named_compute_profile, validate_resource_receipt,
)
from .native_batch import B01NativeBatchEnvironment, derive_native_primitive_endpoint
from .recon import _AReconProcessTreeMonitor
from .seed_packet import create_test_seed_packet, read_test_seed_packet
from .tapes import evaluation_tape
from .trainer import (
    PairedB01Trainer, create_paired_parameter_state_container_once,
    _parameter_distance_from_state_pair,
    _resolve_parameter_state_binding,
    exact_parameter_layout, validate_parameter_distance_raw_record,
)


def exact_integrated_test_contract() -> dict[str, Any]:
    return {
        "schema": "FRRIE_B01_INTEGRATED_ONE_UPDATE_TEST_CONTRACT_V1",
        "test_only": True, "result_bearing": False, "scientific_values": None,
        "seed_namespace": list(TEST_SEED_LABELS),
        "selected_seed": TEST_SEED_LABEL,
        "stage_order": [
            "TEST_MANIFEST_AND_FIXED_PACKET",
            "FRESH_4GIB_MEMORY_ADMISSION",
            "NATIVE_BUILD",
            "CANONICAL_NATIVE_LOAD_AND_PAIRED_RUNTIME_CREATE",
            "CHECKPOINT0_CREATE_READBACK_DECODE_TEMPORARY_RESTORE",
            "REAL_NATIVE_WIDTH32_BOTH_ARM_COLLECTION",
            "ACTUAL_ATOMIC_PAIRED_OPTIMIZER_STEP_AND_PROJECTION",
            "UPDATE1_NONRESUMABLE_DIAGNOSTIC_STATE",
            "REPRESENTATIVE_TEST_EVAL_N6_WIDTH32",
            "DIRECT_TYPED_INDEX_AND_RUNTIME_RECEIPTS",
            "PROCESS_TREE_TELEMETRY_FINALIZE",
            "CREATE_ONCE_TEST_ROOT_PUBLICATION",
        ],
        "curve_checkpoint": 0,
        "update1_state_role": "NONCHECKPOINT_NONRESUMABLE_DIAGNOSTIC_ONLY",
        "representative_eval": {
            "roster": 6, "lanes": 32, "episodes": 32, "horizon": 12,
            "satisfies_production_inventory": False,
        },
        "native_width": 32, "torch_threads": 1,
        "artifact_role": "INTEGRATED_RUNTIME_SMOKE_NOT_INDEPENDENTLY_REPLAYABLE",
        "implementation_critical": False,
        "production_readiness": False,
        "performance_disposition": "REPAIR_REQUIRED",
        "performance_blockers": [
            "NAMED_WORKERS4_NOT_EFFECTIVE_IN_PRODUCTION_COLLECTOR",
            "FULL_512_UPDATE_AND_COMPLETE_EVALUATION_PANEL_NOT_EXECUTED",
        ],
        "production_roots_created": False, "production_panel_token_minted": False,
        "telemetry_stage_order": list(integrated_telemetry_stage_order()),
    }


def integrated_telemetry_stage_order() -> tuple[str, ...]:
    return (
        "FRESH_4GIB_MEMORY_ADMISSION", "NATIVE_BUILD",
        "CANONICAL_NATIVE_LOAD_AND_PAIRED_RUNTIME_CREATE",
        "CHECKPOINT0_CREATE_READBACK_DECODE_TEMPORARY_RESTORE",
        "REAL_NATIVE_WIDTH32_BOTH_ARM_COLLECTION_AND_ATOMIC_UPDATE",
        "UPDATE1_NONRESUMABLE_DIAGNOSTIC_STATE",
        "REPRESENTATIVE_TEST_EVAL_N6_WIDTH32",
        "DIRECT_TYPED_INDEX_AND_RUNTIME_RECEIPTS",
    )


def _validate_process_tree_telemetry(value: Any) -> dict[str, Any]:
    fields = {
        "wall_seconds", "cpu_seconds", "cpu_core_equivalents",
        "host_cpu_occupancy_fraction", "logical_cpu_count", "peak_rss_bytes",
        "scratch_peak_bytes", "durable_peak_bytes", "io_read_transfer_bytes",
        "io_write_transfer_bytes", "peak_process_count", "peak_thread_count",
        "sample_count",
    }

    def row(value: Any, *, end_to_end: bool) -> dict[str, Any]:
        if not isinstance(value, Mapping) or set(value) != fields:
            raise B01ContractError("integrated telemetry row fields differ")
        result = dict(value)
        float_fields = {
            "wall_seconds", "cpu_seconds", "cpu_core_equivalents",
            "host_cpu_occupancy_fraction",
        }
        int_fields = fields - float_fields
        if any(
            isinstance(result[name], bool) or not isinstance(result[name], (int, float))
            or not np.isfinite(result[name]) or result[name] < 0.0
            for name in float_fields
        ) or any(type(result[name]) is not int or result[name] < 0 for name in int_fields):
            raise B01ContractError("integrated telemetry row types/ranges differ")
        if result["logical_cpu_count"] <= 0:
            raise B01ContractError("integrated telemetry logical CPU denominator is absent")
        wanted_core = (
            0.0 if result["wall_seconds"] == 0.0
            else result["cpu_seconds"] / result["wall_seconds"]
        )
        if result["cpu_core_equivalents"] != wanted_core or result[
            "host_cpu_occupancy_fraction"
        ] != wanted_core / result["logical_cpu_count"]:
            raise B01ContractError("integrated telemetry CPU denominator semantics differ")
        if result["peak_process_count"] <= 0 or result["peak_thread_count"] <= 0 or result[
            "sample_count"
        ] <= 0:
            raise B01ContractError("integrated telemetry process/thread/sample evidence is absent")
        if end_to_end and (
            result["wall_seconds"] <= 0.0 or result["cpu_seconds"] <= 0.0
            or result["peak_rss_bytes"] <= 0 or result["sample_count"] < 2
        ):
            raise B01ContractError("integrated end-to-end telemetry evidence is absent")
        return result

    if not isinstance(value, Mapping) or set(value) != {"schema", "stages", "end_to_end"} or value[
        "schema"
    ] != "FRRIE_B01_A_RECON_PROCESS_TREE_TELEMETRY_V2" or not isinstance(value["stages"], list):
        raise B01ContractError("integrated process-tree telemetry envelope differs")
    if any(
        not isinstance(item, Mapping) or set(item) != {"stage_id", "telemetry"}
        for item in value["stages"]
    ) or [item["stage_id"] for item in value["stages"]] != list(
        integrated_telemetry_stage_order()
    ):
        raise B01ContractError("integrated telemetry stage inventory/order differs")
    for item in value["stages"]:
        row(item["telemetry"], end_to_end=False)
    row(value["end_to_end"], end_to_end=True)
    return dict(value)


def _zero_work() -> dict[str, Any]:
    row = {
        "training_update": 0, "episodes": 0, "environment_slots": 0,
        "backward_calls": 0, "adam_steps": 0, "native_batch_calls": 0,
        "native_batch_ledger": {
            "reset_calls": 0, "observe_calls": 0, "step_calls": 0,
            "environment_slots": 0,
        },
        "worker_count": 4, "thread_count": 1,
    }
    return {arm: {**row, "native_batch_ledger": dict(row["native_batch_ledger"])} for arm in LEARNED_ARMS}


def _zero_audit() -> dict[str, Any]:
    return {
        "first_tight_contact_update": None, "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 0, "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.0, "cumulative_tight_displacement": 0.0,
    }


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _publish_integrated_test_root(
    staging: Path, root: Path, incomplete: Path,
) -> dict[str, Any]:
    """Publish once, then quarantine this exact final on validation failure."""

    staging.replace(root)
    try:
        return validate_integrated_test_artifact(root)
    except BaseException:
        if root.exists() and not incomplete.exists():
            root.replace(incomplete)
        raise


def _run_preflight(path: Path) -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[4]
    completed = subprocess.run(
        [sys.executable, str(repository / "scripts" / "hmasd_resource_preflight.py"),
         "admit-memory", "--out", str(path)],
        cwd=repository, check=False, capture_output=True, text=True, timeout=60,
    )
    if completed.returncode != 0:
        raise B01ContractError(completed.stderr or completed.stdout or "memory admission failed")
    return validate_resource_receipt(json.loads(path.read_text(encoding="utf-8")))


def _policy_width32_parity_from_inputs(
    model: FRRIEActorCritic, inputs: Mapping[int, Mapping[str, np.ndarray]],
) -> dict[str, Any]:
    """Exact scalar/batch recurrence parity at production width for N9 and N15."""

    import torch

    if torch.get_num_threads() != 1 or set(inputs) != {9, 15}:
        raise B01ContractError("policy parity requires threads1 and exact N9/N15 inputs")
    was_training = bool(model.training)
    model.eval()
    result = {}
    try:
        with torch.no_grad():
            for roster in (9, 15):
                row = inputs[roster]
                if not isinstance(row, Mapping) or set(row) != {
                    "observations", "roles", "action_uniforms",
                }:
                    raise B01ContractError("policy parity input fields differ")
                observations = np.asarray(row["observations"])
                roles = np.asarray(row["roles"])
                uniforms = np.asarray(row["action_uniforms"])
                if (
                    observations.dtype != np.dtype("<f4")
                    or observations.shape != (32, 12, roster, 22)
                    or roles.dtype != np.dtype("<i8") or roles.shape != (32, roster)
                    or uniforms.dtype != np.dtype("<f4")
                    or uniforms.shape != (32, 12, roster)
                    or not observations.flags.c_contiguous or not roles.flags.c_contiguous
                    or not uniforms.flags.c_contiguous
                    or not np.isfinite(observations).all() or not np.isfinite(uniforms).all()
                    or np.any((uniforms < 0.0) | (uniforms >= 1.0))
                ):
                    raise B01ContractError("policy parity input dtype/shape/value differs")
                expected_roles = np.repeat(np.arange(3, dtype=np.int64), roster // 3)
                if not np.array_equal(roles, np.broadcast_to(expected_roles, roles.shape)):
                    raise B01ContractError("policy parity fixed roles differ")
                obs_t = torch.from_numpy(observations)
                roles_t = torch.from_numpy(roles)
                uniforms_t = torch.from_numpy(uniforms)
                batch_hidden = torch.zeros((32, roster, 64), dtype=torch.float32)
                scalar_hidden = [torch.zeros((roster, 64), dtype=torch.float32) for _ in range(32)]
                collected: dict[str, list[Any]] = {
                    name: [] for name in (
                        "logits", "probabilities", "hidden", "messages", "summary",
                        "denominator", "actions",
                    )
                }
                for slot in range(12):
                    batch = model.actor_step_batch(
                        obs_t[:, slot], roles_t, batch_hidden,
                    )
                    scalar = [
                        model.actor_step(obs_t[lane, slot], roles_t[lane], scalar_hidden[lane])
                        for lane in range(32)
                    ]
                    for field in (
                        "logits", "probabilities", "hidden", "messages", "summary", "denominator",
                    ):
                        scalar_value = torch.stack([getattr(item, field) for item in scalar])
                        if not torch.equal(getattr(batch, field), scalar_value):
                            raise B01ContractError(
                                f"policy width32 scalar/batch {field} differs at N{roster}/slot{slot}"
                            )
                        collected[field].append(getattr(batch, field).detach().clone())
                    batch_actions = model.actions_from_uniforms_batch(
                        batch.probabilities, uniforms_t[:, slot],
                    )
                    scalar_actions = torch.stack([
                        model.actions_from_uniforms(
                            scalar[lane].probabilities, uniforms_t[lane, slot],
                        ) for lane in range(32)
                    ])
                    if not torch.equal(batch_actions, scalar_actions):
                        raise B01ContractError(
                            f"policy width32 scalar/batch actions differ at N{roster}/slot{slot}"
                        )
                    collected["actions"].append(batch_actions.detach().clone())
                    batch_hidden = batch.hidden
                    scalar_hidden = [item.hidden for item in scalar]
                critic_batch = model.critic_values_batch(obs_t, roles_t)
                critic_scalar = torch.stack([
                    model.critic_values(obs_t[lane], roles_t[lane]) for lane in range(32)
                ])
                if not torch.equal(critic_batch, critic_scalar):
                    raise B01ContractError(f"policy width32 scalar/batch critic differs at N{roster}")
                arrays = {
                    "observations": observations.copy(order="C"),
                    "roles": roles.copy(order="C"),
                    "action_uniforms": uniforms.copy(order="C"),
                    **{
                        name: torch.stack(values, dim=1).cpu().numpy().copy(order="C")
                        for name, values in collected.items()
                    },
                    "critic_values": critic_batch.cpu().numpy().copy(order="C"),
                }
                result[roster] = arrays
    finally:
        model.train(was_training)
    return {
        "schema": "FRRIE_B01_POLICY_WIDTH32_PARITY_RECEIPT_V1",
        "native_width": 32, "torch_threads": 1, "rosters": [9, 15],
        "slots": 12, "actor_fields": [
            "logits", "probabilities", "hidden", "messages", "summary", "denominator",
        ],
        "actions_direct_equal": True, "critic_direct_equal": True,
        "arrays_by_roster": result, "production_readiness_from_parity": False,
    }


def production_width_policy_parity_receipt(
    model: FRRIEActorCritic, *, collected_batch: Any, tapes: Sequence[Any],
) -> dict[str, Any]:
    """Bind parity inputs to direct addressed observations from one collected update."""

    if len(tapes) != 64 or len(collected_batch.exogenous_receipts) != 64:
        raise B01ContractError("integrated policy parity requires the exact 64-episode batch")
    inputs = {}
    for roster, positions in (
        (9, tuple(range(0, 64, 2))), (15, tuple(range(1, 64, 2))),
    ):
        observations = []
        roles = []
        uniforms = []
        for position in positions:
            receipt = collected_batch.exogenous_receipts[position]
            tape = tapes[position]
            direct_tape = b"".join(
                getattr(tape, field).tobytes(order="C") for field in (
                    "event_times", "detection_uniform", "uplink_uniform", "base_uniform",
                    "action_uniform",
                )
            )
            if receipt.roster != roster or receipt.tape_bytes != direct_tape:
                raise B01ContractError("policy parity tape/receipt binding differs")
            observations.append(np.frombuffer(
                receipt.observations_bytes, dtype="<f4",
            ).reshape(12, roster, 22))
            roles.append(np.frombuffer(receipt.relations_bytes, dtype="<i8"))
            uniforms.append(tape.action_uniform)
        inputs[roster] = {
            "observations": np.ascontiguousarray(np.stack(observations), dtype="<f4"),
            "roles": np.ascontiguousarray(np.stack(roles), dtype="<i8"),
            "action_uniforms": np.ascontiguousarray(np.stack(uniforms), dtype="<f4"),
        }
    receipt = _policy_width32_parity_from_inputs(model, inputs)
    return {
        **receipt,
        "input_source": "DIRECT_COLLECTED_UPDATE_PRESTATE_OBSERVATIONS_AND_ADDRESSED_TAPES",
        "model_state_stage": "UPDATE_PRESTATE_BEFORE_OPTIMIZER_STEP",
    }


def _representative_eval(
    adapter: Any, model: FRRIEActorCritic, *, test_root: bytes,
) -> dict[str, Any]:
    import torch

    tapes = tuple(evaluation_tape(
        test_root, seed_label=TEST_SEED_LABEL, roster=6, episode=index,
    ) for index in range(32))
    environment = B01NativeBatchEnvironment(adapter, roster=6, lanes=32)
    environment.reset(tapes)
    observations = np.empty((12, 32, 6, 22), dtype="<f4")
    probabilities = np.empty((12, 32, 6, 6), dtype="<f4")
    actions = np.empty((12, 32, 6), dtype="|u1")
    roles_array = np.empty((12, 32, 6), dtype="<i8")
    masks = np.empty((12, 32, 6, 6), dtype="|u1")
    action_uniforms = np.empty((12, 32, 6), dtype="<f4")
    hidden = torch.zeros((32, 6, 64), dtype=torch.float32)
    terminal_step = None
    was_training = bool(model.training)
    model.eval()
    try:
        with torch.no_grad():
            for slot in range(12):
                frame = environment.observe()
                obs = torch.from_numpy(np.ascontiguousarray(frame.observations))
                roles = torch.from_numpy(np.ascontiguousarray(frame.roles))
                actor = model.actor_step_batch(obs, roles, hidden)
                uniforms_array = np.ascontiguousarray(np.stack([
                    tape.action_uniform[slot] for tape in tapes
                ]).astype(np.float32))
                uniforms = torch.from_numpy(uniforms_array)
                selected = model.actions_from_uniforms_batch(actor.probabilities, uniforms)
                terminal_step = environment.step(selected.numpy())
                observations[slot] = frame.observations
                probabilities[slot] = actor.probabilities.detach().numpy()
                actions[slot] = selected.numpy().astype(np.uint8)
                roles_array[slot] = frame.roles
                masks[slot] = frame.legal_masks.astype(np.uint8)
                action_uniforms[slot] = uniforms_array
                hidden = actor.hidden
    finally:
        model.train(was_training)
    if terminal_step is None or terminal_step.terminals != (True,) * 32:
        raise B01ContractError("representative TEST evaluation did not terminate all lanes")
    return {
        "observations": observations.transpose(1, 0, 2, 3).copy(order="C"),
        "probabilities": probabilities.transpose(1, 0, 2, 3).copy(order="C"),
        "actions": actions.transpose(1, 0, 2).copy(order="C"),
        "roles": roles_array.transpose(1, 0, 2).copy(order="C"),
        "masks": masks.transpose(1, 0, 2, 3).copy(order="C"),
        "action_uniforms": action_uniforms.transpose(1, 0, 2).copy(order="C"),
        "returns": np.asarray(terminal_step.returns, dtype="<f8"),
        "primitives": [asdict(row) for row in terminal_step.primitives],
        "work_ledger": asdict(environment.work_ledger()),
    }


def _direct_update_artifacts(output: Path, receipts: Mapping[str, Any]) -> dict[str, Any]:
    byte_fields = (
        "model_pre_bytes", "optimizer_pre_bytes", "model_post_adam_bytes",
        "optimizer_post_adam_bytes", "model_post_projection_bytes",
        "optimizer_post_projection_bytes",
    )
    index = {}
    for arm in LEARNED_ARMS:
        receipt = receipts[arm]
        scalars = asdict(receipt)
        files = {}
        for field in byte_fields:
            data = scalars.pop(field)
            relative = Path("direct-update") / arm / f"{field}.bin"
            _write_bytes(output / relative, data)
            files[field] = {"relative_path": relative.as_posix(), "byte_count": len(data)}
        index[arm] = {"scalars": scalars, "direct_state_files": files}
    return index


def _write_eval_arrays(
    output: Path, evaluation: Mapping[str, Any], *, directory: str = "representative-eval",
) -> dict[str, Any]:
    result = {}
    axis_orders = {
        "observations": ["episode", "slot", "entity", "observation_field"],
        "probabilities": ["episode", "slot", "entity", "action"],
        "actions": ["episode", "slot", "entity"],
        "roles": ["episode", "slot", "entity"],
        "masks": ["episode", "slot", "entity", "action"],
        "action_uniforms": ["episode", "slot", "entity"],
        "returns": ["episode"],
    }
    for name in axis_orders:
        array = evaluation[name]
        relative = Path(directory) / f"{name}.bin"
        _write_bytes(output / relative, array.tobytes(order="C"))
        result[name] = {
            "relative_path": relative.as_posix(), "dtype": array.dtype.str,
            "shape": list(array.shape), "order": "C", "byte_count": array.nbytes,
            "axis_order": axis_orders[name],
        }
    return result


def _write_policy_parity_arrays(output: Path, receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Retain direct width32 recurrence facts in canonical roster/field files."""

    result: dict[str, Any] = {
        key: receipt[key] for key in (
            "schema", "native_width", "torch_threads", "rosters", "slots",
            "actor_fields", "actions_direct_equal", "critic_direct_equal",
            "production_readiness_from_parity", "input_source", "model_state_stage",
        )
    }
    result["arrays_by_roster"] = {}
    for roster in (9, 15):
        descriptors = {}
        arrays = receipt["arrays_by_roster"][roster]
        for name in (
            "observations", "roles", "action_uniforms", "logits", "probabilities",
            "hidden", "messages", "summary", "denominator", "actions", "critic_values",
        ):
            array = np.asarray(arrays[name])
            relative = Path("policy-width32-parity") / f"N{roster}" / f"{name}.bin"
            _write_bytes(output / relative, array.tobytes(order="C"))
            descriptors[name] = {
                "relative_path": relative.as_posix(), "dtype": array.dtype.str,
                "shape": list(array.shape), "order": "C", "byte_count": array.nbytes,
            }
        result["arrays_by_roster"][str(roster)] = descriptors
    return result


def run_integrated_test_worker(root: Path) -> dict[str, Any]:
    """Child-only execution; caller must own a previously absent fixed DLL."""

    root = root.resolve(strict=False)
    staging = root.with_name(root.name + ".creating")
    incomplete = root.with_name(root.name + ".incomplete")
    receipt_path = root.with_name(root.name + ".admit-memory.json")
    packet_path = root.with_name(root.name + ".test-seed-packet.json")
    if any(path.exists() for path in (root, staging, incomplete, receipt_path, packet_path)):
        raise B01ContractError("integrated TEST root/receipt is not fresh")
    create_test_seed_packet(packet_path)
    staging.mkdir(parents=True, exist_ok=False)
    for name in ("output", "checkpoint", "scratch"):
        (staging / name).mkdir()
    repository = Path(__file__).resolve().parents[4]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    source_scope = [
        "experiments/candidates/finite_resource_relational_inductive_efficiency",
        "scripts/hmasd_resource_preflight.py",
    ]
    scoped_source_status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--",
         *source_scope],
        cwd=repository, check=True, capture_output=True, text=True, timeout=30,
    ).stdout.splitlines()
    manifest = make_test_manifest(
        seed_packet_path=packet_path,
        roots={name: str((root / name).resolve(strict=False)) for name in ("output", "checkpoint", "scratch")},
        compute=named_compute_profile(), base_commit=head,
        worktree_state="DIRTY_UNCOMMITTED_TEST_ONLY",
    )
    _write_bytes(staging / "manifest.json", canonical_json_bytes(manifest))
    monitor = _AReconProcessTreeMonitor(
        scratch_root=staging / "scratch", durable_root=staging, interval_seconds=0.005,
    )
    monitor.set_stage(integrated_telemetry_stage_order()[0])
    monitor.start()
    stopped = False
    published_by_this_transaction = False
    try:
        receipt = _run_preflight(receipt_path)
        monitor.set_stage(integrated_telemetry_stage_order()[1])
        vcvars = _windows_vcvars64()
        compiler, _ = _windows_build_environment(vcvars)
        compiler_path = _validate_vcvars_compiler(vcvars, compiler)
        vc_tools_root = (vcvars.resolve(strict=True).parents[2] / "Tools").resolve(strict=True)
        native_path = build_package_native_artifact()
        native_bytes = native_path.stat().st_size
        binding = bind_invocation_resource(
            invocation_id="FRRIE-B01-INTEGRATED-ONE-UPDATE-TEST-001",
            operation="TEST_SMOKE", receipt_path=receipt_path,
            receipt=receipt, test_only=True,
        )
        monitor.set_stage(integrated_telemetry_stage_order()[2])
        import torch
        torch.set_num_threads(1)
        adapter = load_package_native_adapter(named_compute_profile())
        packet = read_test_seed_packet(packet_path)
        test_root = bytes.fromhex(packet["roots_hex"][0])
        phy, edge = initialize_paired_arms(AddressedRNG(test_root), TEST_SEED_LABEL)
        models = {"PHY_TRUST": FRRIEActorCritic(phy), "EDGE_FLEX": FRRIEActorCritic(edge)}
        optimizers = {arm: make_optimizer(models[arm]) for arm in LEARNED_ARMS}
        paired = PairedB01Trainer(models, optimizers)

        monitor.set_stage(integrated_telemetry_stage_order()[3])
        checkpoint0 = snapshot_runtime(
            manifest=manifest, seed_label=TEST_SEED_LABEL, update=0,
            models=models, optimizers=optimizers, work=_zero_work(),
            invocation_binding=binding, projection_audit=_zero_audit(),
        )
        checkpoint_path = staging / "checkpoint" / "checkpoint-000.json"
        _write_bytes(checkpoint_path, checkpoint0)
        checkpoint_receipt = reopen_decode_restore_test_checkpoint0(
            checkpoint_path, manifest=manifest, seed_label=TEST_SEED_LABEL,
        )

        monitor.set_stage(integrated_telemetry_stage_order()[4])
        tapes, origins = make_test_update_inputs(test_root, seed_label=TEST_SEED_LABEL, update=1)
        collections = {
            arm: _collect_b01_test_arm_update(
                model=models[arm], adapter=adapter, tapes=tapes, origins=origins, update=1,
            ) for arm in LEARNED_ARMS
        }
        policy_parity = production_width_policy_parity_receipt(
            models["PHY_TRUST"], collected_batch=collections["PHY_TRUST"].batch,
            tapes=tapes,
        )
        receipts = paired.update(
            {arm: row.batch for arm, row in collections.items()}, update=1,
        )

        monitor.set_stage(integrated_telemetry_stage_order()[5])
        diagnostic = create_paired_parameter_state_container_once(
            staging / "output" / "update-001-diagnostic-state",
            seed_label=TEST_SEED_LABEL, update=1,
            phy_state_bytes=models["PHY_TRUST"].parameter_bytes(),
            edge_state_bytes=models["EDGE_FLEX"].parameter_bytes(),
            test_only_component=True,
        )
        kappa = paired.first_tight_contact_update
        if kappa == 1:
            final_container_path = str(
                (root / "output" / "update-001-diagnostic-state" / "index.json").resolve(
                    strict=False,
                )
            )
            bindings = {
                arm: {
                    "binding_kind": "IMMUTABLE_STATE_REF",
                    "container_schema": "FRRIE_B01_PAIRED_PARAMETER_DISTANCE_STATE_BLOB_V1",
                    "container_path": final_container_path, "seed_block": TEST_SEED_LABEL,
                    "training_update": 1, "arm_id": arm, "field": "arm_state_bytes",
                    "decoded_parameter_byte_count": 142_052, "state_stage": "POSTPROJECTION",
                }
                for arm in LEARNED_ARMS
            }
            direct_parameter = _parameter_distance_from_state_pair(
                models["PHY_TRUST"].parameter_bytes(), models["EDGE_FLEX"].parameter_bytes(),
            )
            if not direct_parameter["available"]:
                raise B01ContractError("integrated contact parameter state is nonfinite")
            parameter_row = {
                "schema": "FRRIE_B01_PARAMETER_DISTANCE_RAW_V1",
                "seed_block": TEST_SEED_LABEL, "training_update": 1,
                "first_tight_contact_update": 1, "available": True,
                "state_stage": "POSTPROJECTION",
                "capture_boundary": "AFTER_ADAM_AND_ARM_PROJECTION_BEFORE_NEXT_MODEL_MUTATION",
                "parameter_layout": exact_parameter_layout(),
                "phy_state_binding": bindings["PHY_TRUST"],
                "edge_state_binding": bindings["EDGE_FLEX"],
                "derived": direct_parameter["derived"],
            }
            _write_bytes(
                staging / "output" / "parameter-distance-update-001.json",
                canonical_json_bytes(parameter_row),
            )
            parameter_diagnostic = {
                "available": True, "availability_reason": None,
                "raw_relative_path": "output/parameter-distance-update-001.json",
                "historical_staging_write_only": True,
                "final_locator_literal_readback_required": True,
            }
        else:
            parameter_diagnostic = {
                "available": False,
                "availability_reason": "TEST_PREFIX_PRE_TIGHT_CONTACT_KAPPA_UNRESOLVED",
                "raw_relative_path": None, "literal_readback_validated": False,
            }

        monitor.set_stage(integrated_telemetry_stage_order()[6])
        evaluation = _representative_eval(adapter, models["PHY_TRUST"], test_root=test_root)
        evaluation_live_replay = _representative_eval(
            adapter, models["PHY_TRUST"], test_root=test_root,
        )
        if any(
            evaluation[name].tobytes(order="C")
            != evaluation_live_replay[name].tobytes(order="C")
            for name in (
                "observations", "probabilities", "actions", "roles", "masks",
                "action_uniforms", "returns",
            )
        ) or evaluation["primitives"] != evaluation_live_replay["primitives"] or evaluation[
            "work_ledger"
        ] != evaluation_live_replay["work_ledger"]:
            raise B01ContractError("integrated bounded live eval replay differs")
        monitor.set_stage(integrated_telemetry_stage_order()[7])
        direct_update = _direct_update_artifacts(staging / "output", receipts)
        eval_arrays = _write_eval_arrays(staging / "output", evaluation)
        eval_replay_arrays = _write_eval_arrays(
            staging / "output", evaluation_live_replay,
            directory="representative-eval-live-replay",
        )
        parity_arrays = _write_policy_parity_arrays(staging / "output", policy_parity)
        retained_native_relative = "output/native-build-artifact.dll"
        _write_bytes(staging / retained_native_relative, native_path.read_bytes())
        typed_index = {
            "schema": "FRRIE_B01_INTEGRATED_TEST_TYPED_INDEX_V1",
            "seed_label": TEST_SEED_LABEL, "update": 1,
            "arm_collection_audits": {arm: asdict(row.audit) for arm, row in collections.items()},
            "direct_update": direct_update,
            "checkpoint0": {
                "relative_path": "checkpoint/checkpoint-000.json",
                "historical_staging_readback_decode_temporary_restore": checkpoint_receipt,
                "final_locator_revalidation_required": True,
            },
            "update1_diagnostic_state": {
                "relative_path": "output/update-001-diagnostic-state/index.json",
                "historical_staging_container_path": diagnostic["container_path"],
                "resume_or_evaluation_capable": diagnostic["resume_or_evaluation_capable"],
                "final_locator_revalidation_required": True,
            },
            "parameter_distance_update1": parameter_diagnostic,
            "policy_width32_parity": parity_arrays,
            "representative_eval": {
                "arrays": eval_arrays, "primitives": evaluation["primitives"],
                "work_ledger": evaluation["work_ledger"],
                "tape_binding": {
                    "schema": "FRRIE_B01_INTEGRATED_TEST_EVAL_ADDRESS_V1",
                    "seed_label": TEST_SEED_LABEL, "purpose": "EVALUATE",
                    "roster": 6, "episodes": list(range(32)),
                    "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
                    "checkpoint_and_model_state_role": "METADATA_ONLY_OPERATIVE_UPDATE1_TEST",
                    "checkpoint_independent": True,
                    "fixed_test_root_from_packet": True,
                },
                "satisfies_production_inventory": False,
            },
            "representative_eval_live_replay": {
                "arrays": eval_replay_arrays,
                "primitives": evaluation_live_replay["primitives"],
                "work_ledger": evaluation_live_replay["work_ledger"],
                "tape_binding": {
                    "schema": "FRRIE_B01_INTEGRATED_TEST_EVAL_ADDRESS_V1",
                    "seed_label": TEST_SEED_LABEL, "purpose": "EVALUATE",
                    "roster": 6, "episodes": list(range(32)),
                    "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
                    "checkpoint_and_model_state_role": "METADATA_ONLY_OPERATIVE_UPDATE1_TEST",
                    "checkpoint_independent": True,
                    "fixed_test_root_from_packet": True,
                },
                "same_live_model_and_test_tapes_as_representative_eval": True,
                "direct_arrays_primitives_and_work_equal": True,
                "independent_replay": False,
                "satisfies_production_inventory": False,
            },
            "complete": True,
        }
        _write_bytes(staging / "output" / "typed-index.json", canonical_json_bytes(typed_index))
        telemetry = monitor.stop()
        stopped = True
        artifact = {
            "schema": "FRRIE_B01_INTEGRATED_ONE_UPDATE_TEST_ARTIFACT_V1",
            "contract": exact_integrated_test_contract(), "manifest_contract": manifest,
            "invocation_binding": binding,
            "typed_index_relative_path": "output/typed-index.json",
            "external_create_once_locators": {
                "test_seed_packet": str(packet_path.resolve(strict=True)),
                "memory_admission_receipt": str(receipt_path.resolve(strict=True)),
            },
            "native_build_artifact": {
                "historical_package_path": str(native_path.resolve()),
                "retained_relative_path": retained_native_relative,
                "byte_count": native_bytes,
                "cleaned_by_outer_launcher_after_child_exit": True,
            },
            "source_and_toolchain": {
                "actual_head": head,
                "scoped_source_status": {
                    "schema": "FRRIE_B01_SCOPED_SOURCE_STATUS_V1",
                    "scope": source_scope, "porcelain_v1_untracked_all": scoped_source_status,
                },
                "vcvars64_path": str(vcvars), "resolved_compiler_path": str(compiler_path),
                "vc_tools_root": str(vc_tools_root), "compiler_within_vc_tools": True,
            },
            "execution_identity": {
                "child_argv": list(sys.argv),
                "child_cwd": str(Path.cwd().resolve()),
                "worker_module": (
                    "experiments.candidates.finite_resource_relational_inductive_efficiency."
                    "b01.integrated_test"
                ),
            },
            "process_tree_telemetry": telemetry,
            "artifact_role": "INTEGRATED_RUNTIME_SMOKE_NOT_INDEPENDENTLY_REPLAYABLE",
            "implementation_critical": False, "production_readiness": False,
            "scientific_values": None, "result_bearing": False,
            "production_roots_created": False, "production_panel_token_minted": False,
            "performance_disposition": "REPAIR_REQUIRED",
            "performance_blockers": exact_integrated_test_contract()["performance_blockers"],
            "complete": True,
        }
        _write_bytes(staging / "artifact.json", canonical_json_bytes(artifact))
        published_by_this_transaction = True
        return _publish_integrated_test_root(staging, root, incomplete)
    except BaseException as error:
        if not stopped:
            try:
                monitor.stop()
            except BaseException:
                pass
        if staging.exists() and not incomplete.exists():
            marker = {
                "schema": "FRRIE_B01_INTEGRATED_TEST_INCOMPLETE_V1",
                "scientific_values": None, "result_bearing": False,
                "exception_type": type(error).__name__, "exception_message": str(error),
                "external_test_seed_packet": str(packet_path),
                "external_memory_receipt": str(receipt_path),
            }
            _write_bytes(staging / "incomplete.json", canonical_json_bytes(marker))
            staging.replace(incomplete)
        elif published_by_this_transaction and root.exists() and not incomplete.exists():
            root.replace(incomplete)
        raise


def validate_integrated_test_artifact(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    def final_relative(literal: Any, expected: str) -> Path:
        if literal != expected or not isinstance(literal, str) or (
            "\\" in literal or Path(literal).is_absolute() or ".." in Path(literal).parts
        ):
            raise B01ContractError("integrated final relative locator differs")
        candidate = (root / Path(literal)).resolve(strict=True)
        if not candidate.is_relative_to(root) or candidate.is_symlink():
            raise B01ContractError("integrated final locator escaped through a symlink")
        return candidate

    try:
        artifact = json.loads((root / "artifact.json").read_text(encoding="utf-8"))
        index_path = final_relative(
            artifact["typed_index_relative_path"], "output/typed-index.json",
        )
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, KeyError) as error:
        raise B01ContractError("integrated TEST artifact/index is unreadable") from error
    if (
        artifact.get("schema") != "FRRIE_B01_INTEGRATED_ONE_UPDATE_TEST_ARTIFACT_V1"
        or artifact.get("contract") != exact_integrated_test_contract()
        or artifact.get("scientific_values") is not None
        or artifact.get("result_bearing") is not False
        or artifact.get("production_roots_created") is not False
        or artifact.get("production_panel_token_minted") is not False
        or artifact.get("performance_disposition") != "REPAIR_REQUIRED"
        or artifact.get("artifact_role")
        != "INTEGRATED_RUNTIME_SMOKE_NOT_INDEPENDENTLY_REPLAYABLE"
        or artifact.get("implementation_critical") is not False
        or artifact.get("production_readiness") is not False
        or artifact.get("complete") is not True
        or index.get("schema") != "FRRIE_B01_INTEGRATED_TEST_TYPED_INDEX_V1"
        or index.get("seed_label") != TEST_SEED_LABEL or index.get("update") != 1
        or index.get("representative_eval", {}).get("satisfies_production_inventory") is not False
        or index.get("update1_diagnostic_state", {}).get("resume_or_evaluation_capable") is not False
        or index.get("complete") is not True
    ):
        raise B01ContractError("integrated TEST artifact identity/claim ceiling differs")
    from .contract import validate_invocation_binding, validate_test_manifest
    manifest = validate_test_manifest(artifact.get("manifest_contract"))
    external = artifact.get("external_create_once_locators")
    if not isinstance(external, Mapping) or set(external) != {
        "test_seed_packet", "memory_admission_receipt",
    }:
        raise B01ContractError("integrated external locator inventory differs")
    try:
        packet_path = Path(external["test_seed_packet"]).resolve(strict=True)
        manifest_packet_path = Path(manifest["seed_packet"]["path"]).resolve(strict=True)
        packet = read_test_seed_packet(packet_path)
    except OSError as error:
        raise B01ContractError("integrated external TEST packet is unreadable") from error
    if packet_path != manifest_packet_path:
        raise B01ContractError("integrated manifest TEST packet locator differs")
    binding = validate_invocation_binding(
        artifact.get("invocation_binding"), require_test_only=True,
    )
    if (
        Path(binding["receipt_path"]).resolve(strict=True)
        != Path(external["memory_admission_receipt"]).resolve(strict=True)
        or binding["operation"] != "TEST_SMOKE"
    ):
        raise B01ContractError("integrated invocation receipt locator differs")
    try:
        stored_receipt = validate_resource_receipt(json.loads(
            Path(external["memory_admission_receipt"]).read_text(encoding="utf-8")
        ))
    except (OSError, json.JSONDecodeError) as error:
        raise B01ContractError("integrated external memory receipt is unreadable") from error
    if stored_receipt != binding["receipt"]:
        raise B01ContractError("integrated external receipt differs from invocation binding")
    if manifest["roots"] != {
        name: str((root / name).resolve(strict=False))
        for name in ("output", "checkpoint", "scratch")
    }:
        raise B01ContractError("integrated final root differs from TEST manifest")

    checkpoint_descriptor = index.get("checkpoint0")
    if not isinstance(checkpoint_descriptor, Mapping) or checkpoint_descriptor.get(
        "relative_path"
    ) != "checkpoint/checkpoint-000.json" or checkpoint_descriptor.get(
        "final_locator_revalidation_required"
    ) is not True:
        raise B01ContractError("integrated checkpoint0 locator contract differs")
    final_checkpoint = final_relative(
        checkpoint_descriptor["relative_path"], "checkpoint/checkpoint-000.json",
    )
    final_checkpoint_receipt = reopen_decode_restore_test_checkpoint0(
        final_checkpoint, manifest=manifest, seed_label=TEST_SEED_LABEL,
    )
    if final_checkpoint_receipt["paired_restore_complete"] is not True:
        raise B01ContractError("integrated final checkpoint0 restore is incomplete")
    checkpoint_decoded = decode_checkpoint(
        final_checkpoint.read_bytes(), manifest=manifest, expected_seed_label=TEST_SEED_LABEL,
        expected_update=0, expected_test_only=True,
    )

    expected_model_bytes = 142_052
    direct_state_bytes: dict[str, dict[str, bytes]] = {}
    import math
    from ..arms import LearnedArm, PROJECTION_BOXES
    from ..state_codec import decode_optimizer_state
    for arm in LEARNED_ARMS:
        arm_row = index["direct_update"][arm]
        scalars = arm_row["scalars"]
        if (
            scalars.get("arm") != arm or scalars.get("update") != 1
            or scalars.get("backward_calls") != 1 or scalars.get("adam_steps") != 1
            or scalars.get("optimizer_moments_unchanged_by_projection") is not True
        ):
            raise B01ContractError("integrated arm update scalar receipt differs")
        direct = arm_row["direct_state_files"]
        if set(direct) != {
            "model_pre_bytes", "optimizer_pre_bytes", "model_post_adam_bytes",
            "optimizer_post_adam_bytes", "model_post_projection_bytes",
            "optimizer_post_projection_bytes",
        }:
            raise B01ContractError("integrated direct update state inventory differs")
        direct_state_bytes[arm] = {}
        for field, descriptor in direct.items():
            expected_relative = f"direct-update/{arm}/{field}.bin"
            path = final_relative(
                f"output/{descriptor['relative_path']}", f"output/{expected_relative}",
            )
            if not path.is_file() or path.stat().st_size != descriptor["byte_count"]:
                raise B01ContractError("integrated direct state file bytes differ")
            expected = OPTIMIZER_STATE_BYTE_COUNT if field.startswith("optimizer") else expected_model_bytes
            if descriptor["byte_count"] != expected:
                raise B01ContractError("integrated direct model/Adam byte count differs")
            direct_state_bytes[arm][field] = path.read_bytes()
        if (
            direct_state_bytes[arm]["optimizer_post_adam_bytes"]
            != direct_state_bytes[arm]["optimizer_post_projection_bytes"]
        ):
            raise B01ContractError("integrated projection changed Adam bytes")
        for field in ("model_pre_bytes", "model_post_adam_bytes", "model_post_projection_bytes"):
            LearnedArm.from_parameter_bytes(arm, direct_state_bytes[arm][field])
        if (
            decode_optimizer_state(direct_state_bytes[arm]["optimizer_pre_bytes"]).step != 0
            or decode_optimizer_state(direct_state_bytes[arm]["optimizer_post_adam_bytes"]).step != 1
            or decode_optimizer_state(direct_state_bytes[arm]["optimizer_post_projection_bytes"]).step != 1
        ):
            raise B01ContractError("integrated Adam step frontier differs")
        if (
            checkpoint_decoded["arm_state_bytes"][arm]
            != direct_state_bytes[arm]["model_pre_bytes"]
            or checkpoint_decoded["optimizer_state_bytes"][arm]
            != direct_state_bytes[arm]["optimizer_pre_bytes"]
        ):
            raise B01ContractError("integrated checkpoint0 restore does not bind update1 pre-state")
        post_adam = direct_state_bytes[arm]["model_post_adam_bytes"]
        post_projection = direct_state_bytes[arm]["model_post_projection_bytes"]
        if post_adam[:107_928] + post_adam[108_000:] != (
            post_projection[:107_928] + post_projection[108_000:]
        ):
            raise B01ContractError("integrated projection changed non-beta model bytes")
        beta_adam = np.frombuffer(post_adam[107_928:108_000], dtype="<f4")
        beta_projection = np.frombuffer(post_projection[107_928:108_000], dtype="<f4")
        low, high = PROJECTION_BOXES[arm]
        wanted = np.clip(beta_adam, np.float32(low), np.float32(high)).astype("<f4")
        if wanted.tobytes() != beta_projection.tobytes():
            raise B01ContractError("integrated beta projection differs from exact arm box")
        changed_indices = tuple(int(item) for item in np.flatnonzero(beta_adam != beta_projection))
        displacement = math.fsum(
            abs(float(after) - float(before))
            for before, after in zip(beta_adam, beta_projection)
        )
        overshoot = max(
            max((float(low) - float(item) for item in beta_adam), default=0.0),
            max((float(item) - float(high) for item in beta_adam), default=0.0), 0.0,
        )
        if (
            tuple(scalars.get("projection_changed_indices", ())) != changed_indices
            or scalars.get("box_contact") is not bool(changed_indices)
            or float(scalars.get("projection_displacement", -1.0)).hex() != displacement.hex()
            or float(scalars.get("maximum_box_overshoot", -1.0)).hex() != float(overshoot).hex()
            or np.asarray(scalars.get("preprojection_beta"), dtype="<f4").tobytes()
            != beta_adam.tobytes()
            or np.asarray(scalars.get("postprojection_beta"), dtype="<f4").tobytes()
            != beta_projection.tobytes()
        ):
            raise B01ContractError("integrated projection receipt scalars differ from state bytes")
        terms = [scalars.get(name) for name in ("loss", "score", "entropy", "critic", "preclip_global_norm")]
        if not all(isinstance(item, (int, float)) and np.isfinite(item) for item in terms):
            raise B01ContractError("integrated update loss/gradient receipt is nonfinite")
        try:
            validate_loss_reduction_receipt(
                scalars.get("loss_reduction_receipt"),
                aggregate_scalars={name: scalars[name] for name in (
                    "loss", "score", "entropy", "critic",
                )},
            )
        except ContractError as error:
            raise B01ContractError(
                "integrated update loss reduction provenance differs"
            ) from error
    if any(
        direct_state_bytes["PHY_TRUST"][field]
        != direct_state_bytes["EDGE_FLEX"][field]
        for field in (
            "model_pre_bytes", "optimizer_pre_bytes", "model_post_adam_bytes",
            "optimizer_post_adam_bytes", "optimizer_post_projection_bytes",
        )
    ):
        raise B01ContractError("integrated paired pre/postAdam state laws differ")
    phy_post = direct_state_bytes["PHY_TRUST"]["model_post_projection_bytes"]
    edge_post = direct_state_bytes["EDGE_FLEX"]["model_post_projection_bytes"]
    beta_start, beta_end = 107_928, 108_000
    if phy_post[:beta_start] + phy_post[beta_end:] != edge_post[:beta_start] + edge_post[beta_end:]:
        raise B01ContractError("integrated first-update projection changed non-beta bytes")

    parity = index.get("policy_width32_parity")
    parity_identity = {
        "schema": "FRRIE_B01_POLICY_WIDTH32_PARITY_RECEIPT_V1",
        "native_width": 32, "torch_threads": 1, "rosters": [9, 15], "slots": 12,
        "actor_fields": [
            "logits", "probabilities", "hidden", "messages", "summary", "denominator",
        ],
        "actions_direct_equal": True, "critic_direct_equal": True,
        "production_readiness_from_parity": False,
        "input_source": "DIRECT_COLLECTED_UPDATE_PRESTATE_OBSERVATIONS_AND_ADDRESSED_TAPES",
        "model_state_stage": "UPDATE_PRESTATE_BEFORE_OPTIMIZER_STEP",
    }
    if not isinstance(parity, Mapping) or any(
        parity.get(name) != value for name, value in parity_identity.items()
    ) or set(parity.get("arrays_by_roster", {})) != {"9", "15"}:
        raise B01ContractError("integrated width32 policy parity identity differs")
    parity_inputs: dict[int, dict[str, np.ndarray]] = {}
    retained_parity: dict[int, dict[str, np.ndarray]] = {}
    for roster in (9, 15):
        shapes = {
            "observations": [32, 12, roster, 22], "roles": [32, roster],
            "action_uniforms": [32, 12, roster], "logits": [32, 12, roster, 6],
            "probabilities": [32, 12, roster, 6], "hidden": [32, 12, roster, 64],
            "messages": [32, 12, roster, 32], "summary": [32, 12, roster, 32],
            "denominator": [32, 12, roster], "actions": [32, 12, roster],
            "critic_values": [32, 12],
        }
        dtypes = {name: "<f4" for name in shapes}
        dtypes.update({"roles": "<i8", "actions": "<i8"})
        descriptors = parity["arrays_by_roster"][str(roster)]
        if set(descriptors) != set(shapes):
            raise B01ContractError("integrated width32 policy parity array inventory differs")
        retained_parity[roster] = {}
        for name in shapes:
            descriptor = descriptors[name]
            expected_relative = f"output/policy-width32-parity/N{roster}/{name}.bin"
            path = final_relative(f"output/{descriptor.get('relative_path')}", expected_relative)
            byte_count = int(np.prod(shapes[name])) * np.dtype(dtypes[name]).itemsize
            if (
                descriptor.get("dtype") != dtypes[name]
                or descriptor.get("shape") != shapes[name]
                or descriptor.get("order") != "C"
                or descriptor.get("byte_count") != byte_count
                or path.stat().st_size != byte_count
            ):
                raise B01ContractError("integrated width32 policy parity descriptor differs")
            retained_parity[roster][name] = np.fromfile(path, dtype=dtypes[name]).reshape(
                shapes[name]
            )
        parity_inputs[roster] = {
            name: retained_parity[roster][name]
            for name in ("observations", "roles", "action_uniforms")
        }
    import torch
    old_threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        reconstructed_parity = _policy_width32_parity_from_inputs(
            FRRIEActorCritic(LearnedArm.from_parameter_bytes(
                "PHY_TRUST", direct_state_bytes["PHY_TRUST"]["model_pre_bytes"],
            )),
            parity_inputs,
        )
    finally:
        torch.set_num_threads(old_threads)
    for roster in (9, 15):
        for name, array in reconstructed_parity["arrays_by_roster"][roster].items():
            if array.tobytes(order="C") != retained_parity[roster][name].tobytes(order="C"):
                raise B01ContractError("integrated width32 policy parity recomputation differs")

    state_descriptor = index.get("update1_diagnostic_state")
    final_state_index = final_relative(
        state_descriptor["relative_path"], "output/update-001-diagnostic-state/index.json",
    )
    for arm, expected in (("PHY_TRUST", phy_post), ("EDGE_FLEX", edge_post)):
        resolved = _resolve_parameter_state_binding({
            "binding_kind": "IMMUTABLE_STATE_REF",
            "container_schema": "FRRIE_B01_PAIRED_PARAMETER_DISTANCE_STATE_BLOB_V1",
            "container_path": str(final_state_index), "seed_block": TEST_SEED_LABEL,
            "training_update": 1, "arm_id": arm, "field": "arm_state_bytes",
            "decoded_parameter_byte_count": 142_052, "state_stage": "POSTPROJECTION",
        }, seed_label=TEST_SEED_LABEL, update=1, arm=arm, manifest=None)
        if resolved != expected:
            raise B01ContractError("integrated final diagnostic state differs from live update bytes")
    parameter = index.get("parameter_distance_update1")
    if parameter.get("available") is True:
        raw_path = final_relative(
            parameter["raw_relative_path"], "output/parameter-distance-update-001.json",
        )
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        for arm, field in (("PHY_TRUST", "phy_state_binding"), ("EDGE_FLEX", "edge_state_binding")):
            if raw.get(field) != {
                "binding_kind": "IMMUTABLE_STATE_REF",
                "container_schema": "FRRIE_B01_PAIRED_PARAMETER_DISTANCE_STATE_BLOB_V1",
                "container_path": str(final_state_index), "seed_block": TEST_SEED_LABEL,
                "training_update": 1, "arm_id": arm, "field": "arm_state_bytes",
                "decoded_parameter_byte_count": 142_052, "state_stage": "POSTPROJECTION",
            }:
                raise B01ContractError("integrated parameter raw state binding differs")
        parameter_validated = validate_parameter_distance_raw_record(
            raw, test_only_component=True,
        )
        if not parameter_validated["available"]:
            raise B01ContractError("integrated final parameter raw record is invalid")
        if (
            _resolve_parameter_state_binding(
                raw["phy_state_binding"], seed_label=TEST_SEED_LABEL, update=1,
                arm="PHY_TRUST", manifest=None,
            ) != phy_post
            or _resolve_parameter_state_binding(
                raw["edge_state_binding"], seed_label=TEST_SEED_LABEL, update=1,
                arm="EDGE_FLEX", manifest=None,
            ) != edge_post
        ):
            raise B01ContractError("integrated parameter raw is not cross-bound to update states")
    elif parameter != {
        "available": False,
        "availability_reason": "TEST_PREFIX_PRE_TIGHT_CONTACT_KAPPA_UNRESOLVED",
        "raw_relative_path": None, "literal_readback_validated": False,
    }:
        raise B01ContractError("integrated precontact parameter availability differs")

    audits = index.get("arm_collection_audits")
    exact_audit = {
        "schema": "FRRIE_B01_BATCH_COLLECTION_AUDIT_V1", "update": 1,
        "factual_episodes": 64, "native_width": 32, "factual_slots": 768,
        "factual_suffix_audit_slots": 1_248, "nonfactual_suffix_slots": 2_912,
        "total_environment_slots": 4_928, "factual_suffixes_audited": 192,
        "alternative_suffixes_executed": 448, "factual_trace_direct_equal": True,
        "model_bytes_unchanged": True, "torch_critic_batch_calls": 2,
        "maximum_actor_lanes": 32, "shared_model_worker_count": 1,
    }
    if (
        not isinstance(audits, Mapping) or set(audits) != set(LEARNED_ARMS)
        or any(
            not isinstance(row, Mapping)
            or set(row) != {*exact_audit, "torch_actor_batch_calls"}
            or any(row[field] != wanted for field, wanted in exact_audit.items())
            or type(row["torch_actor_batch_calls"]) is not int
            or row["torch_actor_batch_calls"] <= 24
            for row in audits.values()
        )
    ):
        raise B01ContractError("integrated collection work/runtime audit differs")

    eval_row = index["representative_eval"]
    expected_tape_binding = {
        "schema": "FRRIE_B01_INTEGRATED_TEST_EVAL_ADDRESS_V1",
        "seed_label": TEST_SEED_LABEL, "purpose": "EVALUATE", "roster": 6,
        "episodes": list(range(32)),
        "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
        "checkpoint_and_model_state_role": "METADATA_ONLY_OPERATIVE_UPDATE1_TEST",
        "checkpoint_independent": True, "fixed_test_root_from_packet": True,
    }
    if eval_row.get("tape_binding") != expected_tape_binding:
        raise B01ContractError("integrated representative eval tape binding differs")
    expected_arrays = {
        "observations": ("<f4", [32, 12, 6, 22]),
        "probabilities": ("<f4", [32, 12, 6, 6]),
        "actions": ("|u1", [32, 12, 6]),
        "roles": ("<i8", [32, 12, 6]),
        "masks": ("|u1", [32, 12, 6, 6]),
        "action_uniforms": ("<f4", [32, 12, 6]),
        "returns": ("<f8", [32]),
    }
    arrays = {}
    if set(eval_row["arrays"]) != set(expected_arrays):
        raise B01ContractError("integrated representative eval array inventory differs")
    for name, (dtype, shape) in expected_arrays.items():
        descriptor = eval_row["arrays"][name]
        if descriptor.get("dtype") != dtype or descriptor.get("shape") != shape:
            raise B01ContractError("integrated representative eval dtype/shape differs")
        path = final_relative(
            f"output/{descriptor['relative_path']}", f"output/representative-eval/{name}.bin",
        )
        expected_bytes = int(np.prod(shape)) * np.dtype(dtype).itemsize
        if descriptor.get("byte_count") != expected_bytes or path.stat().st_size != expected_bytes:
            raise B01ContractError("integrated representative eval typed bytes differ")
        arrays[name] = np.fromfile(path, dtype=dtype).reshape(shape)
    expected_roles = np.repeat(np.arange(3, dtype=np.int64), 2)
    expected_masks = np.zeros((6, 6), dtype=np.uint8)
    for entity, role in enumerate(expected_roles):
        expected_masks[entity, list(LEGAL_ACTION_INDICES[int(role)])] = 1
    if not np.array_equal(arrays["roles"], np.broadcast_to(expected_roles, (32, 12, 6))):
        raise B01ContractError("integrated representative eval roles differ")
    if not np.array_equal(arrays["masks"], np.broadcast_to(expected_masks, (32, 12, 6, 6))):
        raise B01ContractError("integrated representative eval legal masks differ")
    if not np.isfinite(arrays["probabilities"]).all() or not np.allclose(
        arrays["probabilities"].sum(axis=3), 1.0, rtol=0.0, atol=2e-7,
    ) or np.any(arrays["probabilities"][arrays["masks"] == 0] != 0.0):
        raise B01ContractError("integrated representative eval probabilities differ")
    legal_counts = arrays["masks"].sum(axis=3)
    floors = np.float32(0.04) / legal_counts.astype(np.float32)
    legal_probabilities = np.where(arrays["masks"] == 1, arrays["probabilities"], np.inf)
    if np.any(legal_probabilities.min(axis=3) + np.float32(2e-7) < floors):
        raise B01ContractError("integrated representative eval exploration floor differs")
    reconstructed_actions = (
        arrays["action_uniforms"][..., None]
        >= np.cumsum(arrays["probabilities"], axis=3)
    ).sum(axis=3).clip(max=5).astype(np.uint8)
    if not np.array_equal(reconstructed_actions, arrays["actions"]):
        raise B01ContractError("integrated representative eval actions differ from direct uniforms")
    if not np.all(np.take_along_axis(
        arrays["masks"], arrays["actions"][..., None].astype(np.int64), axis=3,
    ) == 1):
        raise B01ContractError("integrated representative eval selected an illegal action")
    test_root = bytes.fromhex(packet["roots_hex"][0])
    regenerated_uniforms = np.stack([
        evaluation_tape(
            test_root, seed_label=TEST_SEED_LABEL, roster=6, episode=episode,
        ).action_uniform
        for episode in range(32)
    ])
    if regenerated_uniforms.tobytes(order="C") != arrays["action_uniforms"].tobytes(order="C"):
        raise B01ContractError("integrated representative eval tape address/root differs")
    work = eval_row["work_ledger"]
    if work != {
        "lanes": 32, "native_reset_calls": 1, "native_observe_calls": 12,
        "native_step_calls": 12, "environment_slots": 384,
    } or len(eval_row["primitives"]) != 32:
        raise B01ContractError("integrated representative eval work/primitives differ")
    if not np.isfinite(arrays["observations"]).all() or not np.isfinite(arrays["returns"]).all():
        raise B01ContractError("integrated representative eval observation/return is nonfinite")
    for episode, primitive in enumerate(eval_row["primitives"]):
        required = {
            "dw", "de", "waste", "duplicate", "expired", "collision", "empty_radio",
            "radio_actions", "waste_actions", "successful_deliveries",
        }
        if not isinstance(primitive, Mapping) or set(primitive) != required or any(
            type(primitive[name]) is not int or primitive[name] < 0
            for name in required - {"waste"}
        ) or not isinstance(primitive["waste"], (int, float)) or not np.isfinite(primitive["waste"]):
            raise B01ContractError("integrated representative primitive fields/types differ")
        derive_native_primitive_endpoint(
            dw=primitive["dw"], de=primitive["de"],
            radio_actions=primitive["radio_actions"],
            waste_actions=primitive["waste_actions"], abi_waste=primitive["waste"],
            observed_return=float(arrays["returns"][episode]),
        )
        if primitive["successful_deliveries"] != primitive["dw"] + primitive["de"]:
            raise B01ContractError("integrated representative delivery ledger differs")
    replay_row = index.get("representative_eval_live_replay")
    if (
        not isinstance(replay_row, Mapping)
        or replay_row.get("tape_binding") != expected_tape_binding
        or replay_row.get("primitives") != eval_row["primitives"]
        or replay_row.get("work_ledger") != work
        or replay_row.get("same_live_model_and_test_tapes_as_representative_eval") is not True
        or replay_row.get("direct_arrays_primitives_and_work_equal") is not True
        or replay_row.get("independent_replay") is not False
        or replay_row.get("satisfies_production_inventory") is not False
        or set(replay_row.get("arrays", {})) != set(expected_arrays)
    ):
        raise B01ContractError("integrated bounded live eval replay identity differs")
    for name, (dtype, shape) in expected_arrays.items():
        descriptor = replay_row["arrays"][name]
        path = final_relative(
            f"output/{descriptor.get('relative_path')}",
            f"output/representative-eval-live-replay/{name}.bin",
        )
        expected_bytes = int(np.prod(shape)) * np.dtype(dtype).itemsize
        if (
            descriptor.get("dtype") != dtype or descriptor.get("shape") != shape
            or descriptor.get("order") != "C" or descriptor.get("byte_count") != expected_bytes
            or path.stat().st_size != expected_bytes
            or path.read_bytes() != arrays[name].tobytes(order="C")
        ):
            raise B01ContractError("integrated bounded live eval replay direct arrays differ")
    telemetry = artifact.get("process_tree_telemetry")
    _validate_process_tree_telemetry(telemetry)
    source = artifact.get("source_and_toolchain")
    try:
        compiler = Path(source["resolved_compiler_path"])
        vc_tools = Path(source["vc_tools_root"])
        vcvars = Path(source["vcvars64_path"])
    except (KeyError, TypeError) as error:
        raise B01ContractError("integrated source/toolchain identity is incomplete") from error
    if (
        not compiler.is_absolute() or not vc_tools.is_absolute() or not vcvars.is_absolute()
        or source.get("compiler_within_vc_tools") is not True
        or not compiler.resolve(strict=False).is_relative_to(vc_tools.resolve(strict=False))
    ):
        raise B01ContractError("integrated compiler is outside the bound VC/Tools tree")
    expected_scope = [
        "experiments/candidates/finite_resource_relational_inductive_efficiency",
        "scripts/hmasd_resource_preflight.py",
    ]
    source_status = source.get("scoped_source_status")
    if (
        source.get("actual_head") != manifest["source_state"]["base_commit"]
        or not isinstance(source_status, Mapping)
        or source_status.get("schema") != "FRRIE_B01_SCOPED_SOURCE_STATUS_V1"
        or source_status.get("scope") != expected_scope
        or not isinstance(source_status.get("porcelain_v1_untracked_all"), list)
        or any(not isinstance(row, str) for row in source_status["porcelain_v1_untracked_all"])
    ):
        raise B01ContractError("integrated retained historical source identity is internally inconsistent")
    execution = artifact.get("execution_identity")
    if (
        not isinstance(execution, Mapping)
        or execution.get("worker_module")
        != "experiments.candidates.finite_resource_relational_inductive_efficiency.b01.integrated_test"
        or not isinstance(execution.get("child_argv"), list)
        or not isinstance(execution.get("child_cwd"), str)
    ):
        raise B01ContractError("integrated child argv/cwd provenance is absent")
    native = artifact.get("native_build_artifact")
    retained_native = final_relative(
        native["retained_relative_path"], "output/native-build-artifact.dll",
    )
    if (
        Path(native["historical_package_path"]).resolve(strict=False)
        != package_native_artifact_path().resolve(strict=False)
        or retained_native.stat().st_size != native["byte_count"]
    ):
        raise B01ContractError("integrated retained native build artifact differs")
    return artifact


def launch_integrated_test(root: Path) -> int:
    """Outer process: enforce fresh DLL ownership and clean it after child exit."""

    root = root.resolve(strict=False)
    native = package_native_artifact_path().resolve(strict=False)
    native_dir = native.parent
    owned_prefix = native.stem
    before = {
        path.resolve(strict=False) for path in native_dir.glob(f"{owned_prefix}*")
    } if native_dir.exists() else set()
    if before:
        raise B01ContractError("integrated TEST refuses pre-existing native DLL/sidecars")
    command = [
        sys.executable, "-m",
        "experiments.candidates.finite_resource_relational_inductive_efficiency.b01.integrated_test",
        "--worker", "--root", str(root),
    ]
    returncode: int | None = None
    timeout_error: subprocess.TimeoutExpired | None = None
    cleanup_error: BaseException | None = None
    try:
        completed = subprocess.run(
            command, check=False, cwd=Path(__file__).resolve().parents[4], timeout=1_200,
        )
        returncode = completed.returncode
    except subprocess.TimeoutExpired as error:
        timeout_error = error
        staging = root.with_name(root.name + ".creating")
        incomplete = root.with_name(root.name + ".incomplete")
        if staging.exists() and not incomplete.exists():
            marker = {
                "schema": "FRRIE_B01_INTEGRATED_TEST_INCOMPLETE_V1",
                "scientific_values": None, "result_bearing": False,
                "exception_type": "TimeoutExpired",
                "exception_message": "outer launcher bounded timeout after 1200 seconds",
                "outer_quarantine": True,
            }
            _write_bytes(staging / "outer-timeout-incomplete.json", canonical_json_bytes(marker))
            staging.replace(incomplete)
    finally:
        try:
            after = {
                path.resolve(strict=False) for path in native_dir.glob(f"{owned_prefix}*")
            } if native_dir.exists() else set()
            for path in sorted(after - before, key=str):
                if path.is_file():
                    _unlink_owned_native_file(path)
            remaining = {
                path.resolve(strict=False) for path in native_dir.glob(f"{owned_prefix}*")
            } if native_dir.exists() else set()
            if remaining != before:
                raise B01ContractError("integrated TEST native owned-file cleanup was incomplete")
        except BaseException as error:
            cleanup_error = error
    if cleanup_error is not None:
        incomplete = root.with_name(root.name + ".incomplete")
        if root.exists():
            if incomplete.exists():
                ordinal = 1
                collision = root.with_name(root.name + f".cleanup-incomplete-{ordinal}")
                while collision.exists():
                    ordinal += 1
                    collision = root.with_name(root.name + f".cleanup-incomplete-{ordinal}")
                root.replace(collision)
                raise B01ContractError(
                    "integrated TEST cleanup failed; final root used collision quarantine"
                ) from cleanup_error
            root.replace(incomplete)
        raise B01ContractError(
            "integrated TEST native owned-file cleanup failed; final root quarantined"
        ) from cleanup_error
    if timeout_error is not None:
        raise B01ContractError(
            "integrated TEST child exceeded the 1200-second bound"
        ) from timeout_error
    if returncode != 0:
        return int(returncode)
    try:
        validate_integrated_test_artifact(root)
    except BaseException:
        incomplete = root.with_name(root.name + ".incomplete")
        if root.exists() and not incomplete.exists():
            root.replace(incomplete)
        raise
    return 0


def _unlink_owned_native_file(path: Path) -> None:
    """Narrow TEST seam; cleanup remains owned by the outer launcher."""

    path.unlink()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="frrie-b01-integrated-test")
    result.add_argument("--root")
    result.add_argument("--worker", action="store_true")
    result.add_argument("--describe", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.describe:
        print(canonical_json_bytes(exact_integrated_test_contract()).decode("ascii"))
        return 0
    if not args.root:
        raise SystemExit("--root is required unless --describe is used")
    if args.worker:
        run_integrated_test_worker(Path(args.root))
        return 0
    return launch_integrated_test(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
