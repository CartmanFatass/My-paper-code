"""Explicit TEST-only bounded B4 checkpoint-induction falsifier.

This module never exposes scientific values and is not a production launch
surface.  Its single public entry creates one create-once TEST transaction,
performs fresh admission, and probes two resumed transitions at each
nonterminal checkpoint coordinate.
"""

from __future__ import annotations

import json
import base64
import multiprocessing
import os
import random
import shutil
import struct
import subprocess
import sys
import time
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from ..arms import initialize_paired_arms
from ..native_adapter import (
    build_package_native_artifact, load_package_native_adapter,
    package_native_artifact_path,
)
from ..policy import FRRIEActorCritic
from ..rng import AddressedRNG
from ..state_codec import encode_optimizer_state, load_actor_and_optimizer_state
from ..training import make_optimizer
from .batch_collector import _collect_b01_test_arm_update, make_test_update_inputs
from .checkpoint import (
    decode_checkpoint,
    reopen_decode_restore_test_checkpoint, restore_runtime,
    restore_trainer_continuation_state, snapshot_runtime,
)
from .constants import CHECKPOINTS, LEARNED_ARMS, TEST_SEED_LABEL
from .contract import (
    B01ContractError, bind_invocation_resource, canonical_json_bytes,
    make_test_manifest, named_compute_profile, validate_resource_receipt,
)
from .recon import _AReconProcessTreeMonitor, _sample_windows_process_tree
from .seed_packet import create_test_seed_packet, read_test_seed_packet
from .trainer import PairedB01Trainer
from .training_runner import (
    PILOT_BOUNDARY_SUFFIXES, PILOT_PEAK_RSS_BYTES,
    PILOT_SCRATCH_DURABLE_BYTES, PILOT_WALL_SECONDS,
    exact512_induction_contract, validate_b4_induction_receipt,
)
from .training_shards import (
    ActualDirectTrainingRow,
    actual_direct_training_row, validate_actual_direct_row_chain_step,
    validate_actual_paired_direct_rows,
)


def _write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _tree_bytes(path: Path) -> int:
    return sum(row.stat().st_size for row in path.rglob("*") if row.is_file())


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes_b64__": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    return value


def _direct_row_persistence_bytes(row: ActualDirectTrainingRow) -> bytes:
    return canonical_json_bytes(_json_safe({
        "schema": "FRRIE_B01_TEST_DIRECT_ROW_PERSISTENCE_V1",
        "update": row.update, "arm": row.arm,
        "array_shards": row.array_shards, "state_blobs": row.state_blobs,
        "typed_exogenous_receipts": row.typed_exogenous_receipts,
    }))


def _append_paired_rows_transaction(
    directory: Path, rows: Mapping[str, ActualDirectTrainingRow], *, fault: str | None = None,
) -> dict[str, int]:
    """Append both direct rows or truncate both files to their exact prior offsets."""

    paths = {arm: directory / f"{arm}.paired-rows.bin" for arm in LEARNED_ARMS}
    directory.mkdir(parents=True, exist_ok=True)
    offsets = {arm: paths[arm].stat().st_size if paths[arm].exists() else 0 for arm in LEARNED_ARMS}
    try:
        for index, arm in enumerate(LEARNED_ARMS):
            payload = _direct_row_persistence_bytes(rows[arm])
            with paths[arm].open("ab") as stream:
                stream.write(struct.pack("<Q", len(payload)))
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if fault == f"AFTER_ARM_{index + 1}":
                raise OSError("injected paired-row append failure")
        for arm in LEARNED_ARMS:
            with paths[arm].open("rb") as stream:
                stream.seek(offsets[arm])
                size = struct.unpack("<Q", stream.read(8))[0]
                observed = stream.read(size)
            if observed != _direct_row_persistence_bytes(rows[arm]):
                raise OSError("paired-row append readback differs")
        if fault == "READBACK":
            raise OSError("injected paired-row readback failure")
        return {arm: paths[arm].stat().st_size for arm in LEARNED_ARMS}
    except BaseException:
        for arm in LEARNED_ARMS:
            with paths[arm].open("r+b") as stream:
                stream.truncate(offsets[arm])
                stream.flush()
                os.fsync(stream.fileno())
        raise


def _persist_checkpoint_transaction(
    path: Path, data: bytes, *, fault: str | None = None,
) -> None:
    temporary = path.with_name(path.name + ".creating")
    if path.exists() or temporary.exists():
        raise FileExistsError("checkpoint create-once target/staging already exists")
    temporary_owned = False
    target_owned = False
    try:
        _write_once(temporary, data)
        temporary_owned = True
        if fault == "WRITE":
            raise OSError("injected checkpoint write failure")
        if temporary.read_bytes() != data or fault == "READBACK":
            raise OSError("checkpoint readback differs")
        os.link(temporary, path)
        target_owned = True
        temporary.unlink()
        temporary_owned = False
    except BaseException:
        if temporary_owned and temporary.exists():
            temporary.unlink()
        if target_owned and path.exists():
            path.unlink()
        raise


def _publish_create_once_transaction(
    staging: Path, final: Path, incomplete: Path, *, fault: str | None = None,
) -> None:
    """Create-once publication with quarantine on rename/readback failure."""

    if final.exists() or incomplete.exists():
        raise FileExistsError("publication target already exists")
    try:
        if fault == "BEFORE_RENAME":
            raise OSError("injected pre-publication failure")
        staging.replace(final)
        if fault == "AFTER_RENAME":
            raise OSError("injected post-rename failure")
        receipt = final / "B4-induction-receipt.json"
        if not receipt.is_file() or fault == "READBACK":
            raise OSError("publication readback failure")
    except BaseException:
        if final.exists():
            final.replace(incomplete)
        elif staging.exists():
            staging.replace(incomplete)
        raise


def _fixture_work(update: int) -> dict[str, Any]:
    """Coordinate-frontier fixture, never an observed prefix-work claim."""

    row = {
        "training_update": update, "episodes": update * 64,
        "environment_slots": update * 4_928, "backward_calls": update,
        "adam_steps": update, "native_batch_calls": update,
        "native_batch_ledger": {
            "reset_calls": update, "observe_calls": 0, "step_calls": 0,
            "environment_slots": update * 4_928,
        },
        "worker_count": 4, "thread_count": 1,
    }
    return {
        arm: {**row, "native_batch_ledger": dict(row["native_batch_ledger"])}
        for arm in LEARNED_ARMS
    }


def _audit0() -> dict[str, Any]:
    return {
        "first_tight_contact_update": None, "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 0,
        "tight_projection_changed_indices": [], "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.0, "cumulative_tight_displacement": 0.0,
    }


def _frontier(update: int) -> dict[str, Any]:
    return {
        "training_update": update, "training_episode_cursor": update * 64,
        "evaluation_checkpoint_cursor": 0,
        "completed_checkpoints": [item for item in CHECKPOINTS if item <= update],
    }


def _runtime_at(root: bytes, checkpoint: int):
    phy, edge = initialize_paired_arms(AddressedRNG(root), TEST_SEED_LABEL)
    models = {
        "PHY_TRUST": FRRIEActorCritic(phy), "EDGE_FLEX": FRRIEActorCritic(edge),
    }
    optimizers = {arm: make_optimizer(models[arm]) for arm in LEARNED_ARMS}
    if checkpoint:
        for arm in LEARNED_ARMS:
            encoded = bytearray(encode_optimizer_state(models[arm], optimizers[arm]))
            struct.pack_into("<Q", encoded, len(encoded) - 8, checkpoint)
            load_actor_and_optimizer_state(
                models[arm], optimizers[arm], models[arm].parameter_bytes(), bytes(encoded),
                expected_update=checkpoint,
            )
    trainer = PairedB01Trainer(models, optimizers)
    state = {
        "schema": "FRRIE_B01_TRAINER_CONTINUATION_STATE_V1",
        "seed_label": TEST_SEED_LABEL, "update": checkpoint,
        "first_tight_contact_update": None, "precontact_full_state_equal": True,
        "tight_projection_changed_indices": [], "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.0, "cumulative_tight_displacement": 0.0,
        "work": _fixture_work(checkpoint), "frontier": _frontier(checkpoint),
    }
    if checkpoint in CHECKPOINTS:
        trainer.restore_checkpoint_continuation_state(state)
    else:
        # TEST coordinate fixture used only to induce the real update-64 contact.
        trainer._continuation_seed_label = TEST_SEED_LABEL
        trainer._continuation_update = checkpoint
        trainer._continuation_work = deepcopy(state["work"])
        trainer._continuation_frontier = deepcopy(state["frontier"])
    return models, optimizers, trainer


def _actual_pair_step(*, adapter: Any, root: bytes, update: int, models, trainer):
    tapes, origins = make_test_update_inputs(root, seed_label=TEST_SEED_LABEL, update=update)
    collections = {
        arm: _collect_b01_test_arm_update(
            model=models[arm], adapter=adapter, tapes=tapes, origins=origins, update=update,
        )
        for arm in LEARNED_ARMS
    }
    committed = trainer.update_with_direct_rows(
        {arm: collections[arm].batch for arm in LEARNED_ARMS},
        collection_audits={arm: collections[arm].audit for arm in LEARNED_ARMS},
        update=update, expected_seed_label=TEST_SEED_LABEL,
        expected_root=root,
    )
    return committed["rows"], committed["paired"], committed["continuation"]


def _genuine_contact_runtime(*, adapter: Any, root: bytes):
    """Produce checkpoint 64 through a real trainer projection at update 64."""

    import torch

    models, optimizers, trainer = _runtime_at(root, 63)
    with torch.no_grad():
        for arm in LEARNED_ARMS:
            models[arm].beta.reshape(-1)[0] = torch.tensor(0.75, dtype=torch.float32)
    rows, _paired, continuation = _actual_pair_step(
        adapter=adapter, root=root, update=64, models=models, trainer=trainer,
    )
    audit = trainer.projection_audit()
    phy_changed = tuple(np.flatnonzero(np.frombuffer(
        rows["PHY_TRUST"].array_shards["changed_mask"], dtype="|u1",
    )).tolist())
    if (
        audit["first_tight_contact_update"] != 64
        or phy_changed != (0,)
        or audit["tight_projection_changed_indices"] != [0]
        or continuation["update"] != 64
    ):
        raise B01ContractError("B4 genuine contact fixture did not produce tight contact")
    # Preserve the genuine contact state, then place one seen and one unseen
    # beta coordinate exactly on the tight boundary with serialized Adam
    # moments that force the next real Adam transition outward.  Gradient
    # clipping bounds every component by five, so m=-1 remains negative after
    # the next beta update and both coordinates must be projected.
    phy = models["PHY_TRUST"]
    with torch.no_grad():
        phy.beta.reshape(-1)[:2] = torch.tensor([0.15, 0.15], dtype=torch.float32)
        state = optimizers["PHY_TRUST"].state[phy.beta]
        state["exp_avg"].reshape(-1)[:2] = -1.0
        state["exp_avg_sq"].reshape(-1)[:2] = 1.0e-6
    return models, optimizers, trainer


def _must_reject(call, category: str, rejected: set[str]) -> None:
    try:
        call()
    except B01ContractError:
        rejected.add(category)
        return
    raise B01ContractError(f"B4 {category} tamper was not rejected")


def _row_tamper_matrix(
    *, rows: Mapping[str, ActualDirectTrainingRow], expected_update: int,
    previous: Mapping[str, tuple[bytes, bytes]], root: bytes,
) -> set[str]:
    rejected: set[str] = set()
    left = rows["PHY_TRUST"]
    right = rows["EDGE_FLEX"]

    def typed(category: str, field: str, mutate):
        receipts = [dict(item) for item in right.typed_exogenous_receipts]
        receipts[0][field] = mutate(receipts[0][field])
        changed = replace(right, typed_exogenous_receipts=tuple(receipts))
        _must_reject(
            lambda: validate_actual_paired_direct_rows({
                "PHY_TRUST": left, "EDGE_FLEX": changed,
            }, expected_update=expected_update, expected_seed_label=TEST_SEED_LABEL,
                expected_root=root), category, rejected,
        )

    typed("TAPE", "tape_bytes", lambda value: bytes([value[0] ^ 1]) + value[1:])
    typed("ORIGIN_ADDRESS", "origin_addresses", lambda value: (
        bytes([value[0][0] ^ 1]) + value[0][1:], *value[1:],
    ))
    typed("LAW_REVISION", "law_revisions", lambda value: ("TAMPERED", *value[1:]))
    typed("ROLE_MASK", "masks_bytes", lambda value: bytes([value[0] ^ 1]) + value[1:])

    common = []
    for value in left.typed_exogenous_receipts:
        row = dict(value)
        row["tape_bytes"] = bytes([row["tape_bytes"][0] ^ 1]) + row["tape_bytes"][1:]
        common.append(row)
    both_wrong = {
        arm: replace(rows[arm], typed_exogenous_receipts=tuple(common))
        for arm in LEARNED_ARMS
    }
    _must_reject(
        lambda: validate_actual_paired_direct_rows(
            both_wrong, expected_update=expected_update,
            expected_seed_label=TEST_SEED_LABEL,
            expected_root=root,
        ), "COMMON_MODE_TAPE", rejected,
    )

    def payload(category: str, field: str, mutate, *, expected=expected_update):
        arrays = dict(left.array_shards)
        arrays[field] = mutate(arrays[field])
        changed = replace(left, array_shards=arrays)
        _must_reject(
            lambda: validate_actual_direct_row_chain_step(
                changed, expected_update=expected,
                previous_model_post_projection=previous["PHY_TRUST"][0],
                previous_optimizer_post_projection=previous["PHY_TRUST"][1],
            ), category, rejected,
        )

    payload("WORK", "work", lambda value: value[:-1] + bytes([value[-1] ^ 1]))
    payload("LOSS_BITS", "loss_aggregate_bits", lambda value: bytes([value[0] ^ 1]) + value[1:])
    payload("PROJECTION_MASK", "changed_mask", lambda value: bytes([value[0] ^ 1]) + value[1:])
    payload("ROW_ORDER", "work", lambda value: value, expected=expected_update + 1)
    return rejected


def _checkpoint_tamper_matrix(
    *, data: bytes, manifest: Mapping[str, Any], checkpoint: int,
) -> set[str]:
    payload0 = json.loads(data)
    rejected: set[str] = set()

    def mutate(category: str, edit, *, expected_seed=TEST_SEED_LABEL):
        payload = deepcopy(payload0)
        edit(payload)
        tampered = canonical_json_bytes(payload)
        _must_reject(
            lambda: decode_checkpoint(
                tampered, manifest=manifest, expected_seed_label=expected_seed,
                expected_update=checkpoint, expected_test_only=True,
            ), category, rejected,
        )

    mutate("MODEL", lambda value: value["arm_state_b64"].__setitem__("PHY_TRUST", ""))
    mutate("OPTIMIZER", lambda value: value["optimizer_state_b64"].__setitem__("PHY_TRUST", ""))

    def bad_step(value):
        import base64
        blob = bytearray(base64.b64decode(value["optimizer_state_b64"]["PHY_TRUST"]))
        struct.pack_into("<Q", blob, len(blob) - 8, checkpoint + 1)
        value["optimizer_state_b64"]["PHY_TRUST"] = base64.b64encode(blob).decode("ascii")

    mutate("ADAM_STEP", bad_step)
    mutate("FRONTIER", lambda value: value["frontier"].__setitem__(
        "training_episode_cursor", value["frontier"]["training_episode_cursor"] + 1,
    ))
    mutate("AUDIT", lambda value: value["projection_audit"].__setitem__(
        "tight_projection_changed_coordinates", 1,
    ))
    mutate("WORK", lambda value: value["work"]["PHY_TRUST"].__setitem__(
        "environment_slots", value["work"]["PHY_TRUST"]["environment_slots"] + 1,
    ))
    substitute = "FRRIE-B01-TEST-ONLY-BLOCK-002"
    mutate("SEED_PHASE", lambda value: value.__setitem__("seed_label", substitute),
           expected_seed=substitute)
    return rejected


def _fresh_admission(repository: Path, receipt_path: Path) -> dict[str, Any]:
    completed = subprocess.run([
        str(Path(sys.executable).resolve(strict=True)),
        str((repository / "scripts" / "hmasd_resource_preflight.py").resolve(strict=True)),
        "admit-memory", "--out", str(receipt_path),
    ], cwd=repository, check=False, capture_output=True, text=True, timeout=60)
    if completed.returncode != 0:
        raise B01ContractError("B4 pilot fresh memory admission failed")
    admission = validate_resource_receipt(json.loads(receipt_path.read_text("utf-8")))
    if min(admission["available_physical_bytes"], admission["effective_available_bytes"]) < 4 * 1024**3:
        raise B01ContractError("B4 pilot admission is below 4 GiB")
    return admission


def _configure_child_native_build_directory(module: Any, directory: Path) -> Path:
    """Bind a fresh interpreter to one absent TEST-only native build directory."""

    resolved = directory.resolve(strict=False)
    if (
        resolved.exists()
        or getattr(module, "_LIVE_ADAPTER", None) is not None
        or getattr(module, "_FRESH_ARTIFACT_PATH", None) is not None
        or getattr(module, "_FRESH_ARTIFACT_BYTES", None) is not None
    ):
        raise B01ContractError("B4 resumed child native build state is not fresh")
    module._NATIVE_DIR = resolved
    return resolved


def _resumed_probe_worker(
    connection: Any, *, root: bytes, checkpoint: int, data: bytes,
    manifest: Mapping[str, Any], admission_path: str, native_build_directory: str,
) -> None:
    """Fresh spawned resume side with an independent adapter and global RNG states."""

    try:
        repository = Path(__file__).resolve().parents[4]
        admission = _fresh_admission(repository, Path(admission_path))
        random.seed(0xB4010000 + checkpoint)
        np.random.seed(0xB4020000 + checkpoint)
        import torch
        torch.manual_seed(0xB4030000 + checkpoint)
        from .. import native_adapter as native_adapter_module
        _configure_child_native_build_directory(
            native_adapter_module, Path(native_build_directory),
        )
        native_adapter_module.build_package_native_artifact()
        adapter = native_adapter_module.load_package_native_adapter(
            named_compute_profile()
        )
        models, optimizers, trainer = _runtime_at(root, 0)
        decoded = restore_runtime(
            data, manifest=manifest, seed_label=TEST_SEED_LABEL, update=checkpoint,
            models=models, optimizers=optimizers,
        )
        restore_receipt = restore_trainer_continuation_state(trainer, decoded)
        prior = {
            arm: (
                models[arm].parameter_bytes(),
                encode_optimizer_state(models[arm], optimizers[arm]),
            )
            for arm in LEARNED_ARMS
        }
        steps = []
        for update in PILOT_BOUNDARY_SUFFIXES[checkpoint]:
            rows, paired, continuation = _actual_pair_step(
                adapter=adapter, root=root, update=update,
                models=models, trainer=trainer,
            )
            validated = {}
            for arm in LEARNED_ARMS:
                checked = validate_actual_direct_row_chain_step(
                    rows[arm], expected_update=update,
                    previous_model_post_projection=prior[arm][0],
                    previous_optimizer_post_projection=prior[arm][1],
                )
                prior[arm] = (
                    checked["next_model_bytes"], checked["next_optimizer_bytes"],
                )
                validated[arm] = checked
            steps.append({
                "update": update, "rows": rows, "paired": paired,
                "continuation": continuation, "validated": validated,
            })
        connection.send({
            "ok": True, "restore_receipt": restore_receipt, "steps": steps,
            "final_continuation": trainer.checkpoint_continuation_state(),
            "projection_audit": trainer.projection_audit(),
            "admission_minimum_bytes": min(
                admission["available_physical_bytes"], admission["effective_available_bytes"],
            ),
            "global_rng_states_perturbed": True, "fresh_native_adapter": True,
        })
    except BaseException as error:
        connection.send({"ok": False, "error": repr(error)})
    finally:
        connection.close()


def _spawn_resumed_probe(
    *, root: bytes, checkpoint: int, data: bytes, manifest: Mapping[str, Any],
    admission_path: Path,
) -> dict[str, Any]:
    context = multiprocessing.get_context("spawn")
    native_build_directory = staging_native = admission_path.with_name(
        admission_path.name.removesuffix("-admit-memory.json") + "-native"
    )
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_resumed_probe_worker,
        kwargs={
            "connection": child, "root": root, "checkpoint": checkpoint,
            "data": data, "manifest": dict(manifest),
            "admission_path": str(admission_path),
            "native_build_directory": str(native_build_directory),
        },
        name=f"frrie-b4-resume-{checkpoint:03d}",
    )
    started = False
    try:
        process.start()
        started = True
        child.close()
        if not parent.poll(PILOT_WALL_SECONDS):
            raise B01ContractError("B4 fresh resumed child did not return within ceiling")
        try:
            result = parent.recv()
        except EOFError as error:
            raise B01ContractError("B4 fresh resumed child pipe closed before result") from error
        process.join(timeout=10)
        if process.is_alive():
            raise B01ContractError("B4 fresh resumed child did not exit")
        if process.exitcode != 0 or not isinstance(result, Mapping) or result.get("ok") is not True:
            raise B01ContractError(
                f"B4 fresh resumed child failed: "
                f"{result.get('error') if isinstance(result, Mapping) else result!r}"
            )
        return dict(result)
    finally:
        try:
            parent.close()
        finally:
            try:
                child.close()
            except BaseException:
                pass
        if started and process.is_alive():
            try:
                _terminate_owned_process_tree(process.pid)
            finally:
                process.join(timeout=30)
        if staging_native.exists() and not (started and process.is_alive()):
            shutil.rmtree(staging_native)


def _run_probe(*, adapter: Any, root: bytes, checkpoint: int, data: bytes,
               checkpoint_path: Path, manifest: Mapping[str, Any],
               left_models: Mapping[str, Any], left_optimizers: Mapping[str, Any],
               left_trainer: PairedB01Trainer, staging: Path):
    decoded = decode_checkpoint(
        data, manifest=manifest, expected_seed_label=TEST_SEED_LABEL,
        expected_update=checkpoint, expected_test_only=True,
    )
    literal = reopen_decode_restore_test_checkpoint(
        checkpoint_path, manifest=manifest, seed_label=TEST_SEED_LABEL,
        update=checkpoint,
    )
    if not literal["paired_restore_complete"]:
        raise B01ContractError("B4 literal/model/audit restore is incomplete")
    prior = {
        arm: (
            left_models[arm].parameter_bytes(),
            encode_optimizer_state(left_models[arm], left_optimizers[arm]),
        )
        for arm in LEARNED_ARMS
    }
    initial_audit = left_trainer.projection_audit()
    contact_union_validated = None
    left_steps = []
    tamper_rejections: set[str] = set()
    for update in PILOT_BOUNDARY_SUFFIXES[checkpoint]:
        step_previous = dict(prior)
        left_rows, left_pair, left_continuation = _actual_pair_step(
            adapter=adapter, root=root, update=update,
            models=left_models, trainer=left_trainer,
        )
        for arm in LEARNED_ARMS:
            validated = validate_actual_direct_row_chain_step(
                left_rows[arm], expected_update=update,
                previous_model_post_projection=prior[arm][0],
                previous_optimizer_post_projection=prior[arm][1],
            )
            prior[arm] = (
                validated["next_model_bytes"], validated["next_optimizer_bytes"],
            )
        left_steps.append({
            "update": update, "rows": left_rows, "paired": left_pair,
            "continuation": left_continuation,
        })
        if checkpoint == 64 and update == 65:
            after_audit = left_trainer.projection_audit()
            contact_union_validated = (
                initial_audit["first_tight_contact_update"] == 64
                and initial_audit["tight_projection_changed_indices"] == [0]
                and after_audit["first_tight_contact_update"] == 64
                and set(after_audit["tight_projection_changed_indices"]).issuperset({0, 1})
                and after_audit["maximum_tight_overshoot"]
                >= initial_audit["maximum_tight_overshoot"]
                and after_audit["cumulative_tight_displacement"]
                > initial_audit["cumulative_tight_displacement"]
            )
            if not contact_union_validated:
                raise B01ContractError("B4 resumed contact audit set-union fixture differs")
        _append_paired_rows_transaction(
            staging / "suffix-shards" / f"checkpoint-{checkpoint:03d}" / "uninterrupted",
            left_rows,
        )
        if checkpoint == 0 and update == 1:
            tamper_rejections.update(_row_tamper_matrix(
                rows=left_rows, expected_update=update,
                previous=step_previous, root=root,
            ))
    resumed = _spawn_resumed_probe(
        root=root, checkpoint=checkpoint, data=data, manifest=manifest,
        admission_path=staging / f"resume-{checkpoint:03d}-admit-memory.json",
    )
    if not resumed["restore_receipt"]["complete"]:
        raise B01ContractError("B4 fresh child literal restore is incomplete")
    if len(left_steps) != len(resumed["steps"]):
        raise B01ContractError("B4 uninterrupted/resumed suffix length differs")
    for left, right in zip(left_steps, resumed["steps"]):
        _append_paired_rows_transaction(
            staging / "suffix-shards" / f"checkpoint-{checkpoint:03d}" / "resumed",
            right["rows"],
        )
        if (
            left["update"] != right["update"]
            or left["rows"] != right["rows"]
            or left["paired"] != right["paired"]
            or left["continuation"] != right["continuation"]
        ):
            raise B01ContractError("B4 uninterrupted/resumed direct transition differs")
    left_shards = staging / "suffix-shards" / f"checkpoint-{checkpoint:03d}" / "uninterrupted"
    right_shards = staging / "suffix-shards" / f"checkpoint-{checkpoint:03d}" / "resumed"
    if any(
        (left_shards / f"{arm}.paired-rows.bin").read_bytes()
        != (right_shards / f"{arm}.paired-rows.bin").read_bytes()
        for arm in LEARNED_ARMS
    ):
        raise B01ContractError("B4 uninterrupted/resumed persisted shard frontier differs")
    left_final = left_trainer.checkpoint_continuation_state()
    if (
        left_final != resumed["final_continuation"]
        or left_trainer.projection_audit() != resumed["projection_audit"]
    ):
        raise B01ContractError("B4 uninterrupted/resumed audit/work/frontier readback differs")
    return {
        "checkpoint": checkpoint,
        "updates": list(PILOT_BOUNDARY_SUFFIXES[checkpoint]),
        "literal_restore_complete": True,
        "uninterrupted_resumed_direct_equal": True,
        "typed_tape_address_equal": True, "native_work_equal": True,
        "frontier_equal": left_final == resumed["final_continuation"],
        "loss_projection_equal": True,
        "fresh_spawned_resume_process": True,
        "fresh_native_adapter": resumed["fresh_native_adapter"],
        "global_rng_states_perturbed": resumed["global_rng_states_perturbed"],
        "audit_state_equal": left_trainer.projection_audit() == resumed["projection_audit"],
        "persistence_frontier_equal": True,
        "contact_audit_set_union_validated": contact_union_validated,
        "checkpoint_prefix_role": "TEST_COORDINATE_FIXTURE_NOT_OBSERVED_PREFIX_WORK",
        "audit_branch_fixture": (
            "POSTCONTACT_RESTORE"
            if decoded["projection_audit"]["first_tight_contact_update"] is not None
            else "NO_CONTACT"
        ),
        "_tamper_rejections": sorted(tamper_rejections),
        "_sample_rows": left_steps[0]["rows"],
    }


def _rollback_probe(
    *, adapter: Any, root: bytes, sample_rows: Mapping[str, ActualDirectTrainingRow],
    staging: Path, checkpoint_data: bytes,
) -> dict[str, Any]:
    models, optimizers, trainer = _runtime_at(root, 0)
    tapes, origins = make_test_update_inputs(root, seed_label=TEST_SEED_LABEL, update=1)
    collections = {
        arm: _collect_b01_test_arm_update(
            model=models[arm], adapter=adapter, tapes=tapes, origins=origins, update=1,
        )
        for arm in LEARNED_ARMS
    }
    before = {
        arm: (models[arm].parameter_bytes(), encode_optimizer_state(models[arm], optimizers[arm]))
        for arm in LEARNED_ARMS
    }
    audit_before = trainer.projection_audit()
    continuation_before = trainer.checkpoint_continuation_state()
    original = trainer.trainers["EDGE_FLEX"].update

    def fail(*args, **kwargs):
        raise RuntimeError("injected second-arm failure")

    trainer.trainers["EDGE_FLEX"].update = fail
    rejected = False
    try:
        trainer.update(
            {arm: collections[arm].batch for arm in LEARNED_ARMS}, update=1,
        )
    except B01ContractError:
        rejected = True
    finally:
        trainer.trainers["EDGE_FLEX"].update = original
    after_equal = all(
        models[arm].parameter_bytes() == before[arm][0]
        and encode_optimizer_state(models[arm], optimizers[arm]) == before[arm][1]
        for arm in LEARNED_ARMS
    )
    if (
        not rejected or not after_equal or trainer.projection_audit() != audit_before
        or trainer.checkpoint_continuation_state() != continuation_before
    ):
        raise B01ContractError("B4 injected second-arm rollback differs")
    validation_models, validation_optimizers, validation_trainer = _runtime_at(root, 0)
    validation_collections = {
        arm: _collect_b01_test_arm_update(
            model=validation_models[arm], adapter=adapter,
            tapes=tapes, origins=origins, update=1,
        )
        for arm in LEARNED_ARMS
    }
    validation_before = {
        arm: (
            validation_models[arm].parameter_bytes(),
            encode_optimizer_state(validation_models[arm], validation_optimizers[arm]),
        )
        for arm in LEARNED_ARMS
    }
    validation_rejected = False
    try:
        validation_trainer.update_with_direct_rows(
            {arm: validation_collections[arm].batch for arm in LEARNED_ARMS},
            collection_audits={
                arm: validation_collections[arm].audit for arm in LEARNED_ARMS
            },
            update=1, expected_seed_label=TEST_SEED_LABEL,
            expected_root=bytes([root[0] ^ 1]) + root[1:],
        )
    except B01ContractError:
        validation_rejected = True
    if (
        not validation_rejected
        or validation_trainer.checkpoint_continuation_state() != continuation_before
        or validation_trainer.projection_audit() != audit_before
        or any(
            validation_models[arm].parameter_bytes() != validation_before[arm][0]
            or encode_optimizer_state(
                validation_models[arm], validation_optimizers[arm],
            ) != validation_before[arm][1]
            for arm in LEARNED_ARMS
        )
    ):
        raise B01ContractError("B4 direct-row validation rollback differs")
    persistence = staging / "rollback-faults" / "paired"
    paired_faults = {}
    for fault in ("AFTER_ARM_1", "AFTER_ARM_2", "READBACK"):
        before_offsets = {
            arm: (persistence / f"{arm}.paired-rows.bin").stat().st_size
            if (persistence / f"{arm}.paired-rows.bin").exists() else 0
            for arm in LEARNED_ARMS
        }
        try:
            _append_paired_rows_transaction(persistence, sample_rows, fault=fault)
        except OSError:
            pass
        else:
            raise B01ContractError("B4 paired persistence fault was not injected")
        after_offsets = {
            arm: (persistence / f"{arm}.paired-rows.bin").stat().st_size
            for arm in LEARNED_ARMS
        }
        paired_faults[fault] = after_offsets == before_offsets
    checkpoint_faults = {}
    for fault in ("WRITE", "READBACK"):
        path = staging / "rollback-faults" / f"checkpoint-{fault}.json"
        try:
            _persist_checkpoint_transaction(path, checkpoint_data, fault=fault)
        except OSError:
            pass
        else:
            raise B01ContractError("B4 checkpoint persistence fault was not injected")
        checkpoint_faults[fault] = not path.exists() and not path.with_name(
            path.name + ".creating"
        ).exists()
    publication_faults = {}
    for fault in ("BEFORE_RENAME", "AFTER_RENAME", "READBACK"):
        base = staging / "rollback-faults" / f"publication-{fault}"
        creating = base.with_name(base.name + ".creating")
        incomplete = base.with_name(base.name + ".incomplete")
        creating.mkdir(parents=True)
        _write_once(creating / "B4-induction-receipt.json", b"{}")
        try:
            _publish_create_once_transaction(creating, base, incomplete, fault=fault)
        except OSError:
            pass
        else:
            raise B01ContractError("B4 publication fault was not injected")
        publication_faults[fault] = not base.exists() and incomplete.is_dir()
    if not all((*paired_faults.values(), *checkpoint_faults.values(), *publication_faults.values())):
        raise B01ContractError("B4 persistence rollback fault matrix differs")
    return {
        "second_arm_failure_injected": True,
        "both_arm_model_optimizer_rollback_equal": True,
        "audit_and_uncommitted_work_rollback_equal": True,
        "direct_row_validation_failure_rolled_back": True,
        "paired_shard_append_faults_rolled_back": True,
        "checkpoint_write_readback_faults_rolled_back": True,
        "create_once_publication_faults_quarantined": True,
    }


def _execute_actual_b4_checkpoint_induction_pilot(root: str | Path) -> dict[str, Any]:
    """Effectful child implementation; public entry always supervises this process."""

    final = Path(root).resolve(strict=False)
    staging = final.with_name(final.name + ".creating")
    incomplete = final.with_name(final.name + ".incomplete")
    receipt_path = final.with_name(final.name + ".admit-memory.json")
    packet_path = final.with_name(final.name + ".test-seed-packet.json")
    if any(path.exists() for path in (final, staging, incomplete, receipt_path, packet_path)):
        raise B01ContractError("B4 pilot requires fresh create-once paths")
    staging.mkdir(parents=True)
    monitor = _AReconProcessTreeMonitor(
        scratch_root=staging, durable_root=staging, interval_seconds=0.01,
    )
    started = time.perf_counter()
    published = False
    try:
        repository = Path(__file__).resolve().parents[4]
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        # Fresh admission is immediately before packet/native/RNG/model/optimizer creation.
        admission = _fresh_admission(repository, receipt_path)
        create_test_seed_packet(packet_path)
        manifest = make_test_manifest(
            seed_packet_path=packet_path,
            roots={name: str((final / name).resolve(strict=False)) for name in (
                "output", "checkpoint", "scratch",
            )},
            compute=named_compute_profile(), base_commit=head,
            worktree_state="DIRTY_UNCOMMITTED_TEST_ONLY",
        )
        binding = bind_invocation_resource(
            invocation_id="FRRIE-B01-B4-INDUCTION-PILOT-001",
            operation="TEST_SMOKE", receipt_path=receipt_path,
            receipt=admission, test_only=True,
        )
        monitor.start()
        build_package_native_artifact()
        adapter = load_package_native_adapter(named_compute_profile())
        packet = read_test_seed_packet(packet_path)
        test_root = bytes.fromhex(packet["roots_hex"][0])
        probes = []
        tamper_rejections: set[str] = set()
        base = None
        terminal = None
        sample_rows = None
        checkpoint0_data = None
        for checkpoint in CHECKPOINTS:
            if checkpoint == 64:
                models, optimizers, trainer = _genuine_contact_runtime(
                    adapter=adapter, root=test_root,
                )
            else:
                models, optimizers, trainer = _runtime_at(test_root, checkpoint)
            trainer.checkpoint_boundary_state_inventory()
            data = snapshot_runtime(
                manifest=manifest, seed_label=TEST_SEED_LABEL, update=checkpoint,
                models=models, optimizers=optimizers,
                work=trainer.checkpoint_continuation_state()["work"],
                invocation_binding=binding, projection_audit=trainer.projection_audit(),
            )
            checkpoint_path = staging / "checkpoints" / f"checkpoint-{checkpoint:03d}.json"
            _persist_checkpoint_transaction(checkpoint_path, data)
            if checkpoint == 0:
                checkpoint0_data = data
                tamper_rejections.update(_checkpoint_tamper_matrix(
                    data=data, manifest=manifest, checkpoint=0,
                ))
            if checkpoint == 0:
                base = {
                    "literal_restore_complete": True,
                    "model_optimizer_bytes_equal": True,
                    "zero_work_untouched_audit": True,
                }
            if checkpoint == 512:
                restored = reopen_decode_restore_test_checkpoint(
                    checkpoint_path, manifest=manifest, seed_label=TEST_SEED_LABEL,
                    update=512,
                )
                if not restored["paired_restore_complete"]:
                    raise B01ContractError("B4 checkpoint512 restore is incomplete")
                terminal = {
                    "checkpoint": 512, "literal_restore_complete": True,
                    "restore_only": True, "suffix_updates": [],
                    "checkpoint_prefix_role": (
                        "TEST_COORDINATE_FIXTURE_NOT_OBSERVED_PREFIX_WORK"
                    ),
                }
            else:
                probe = _run_probe(
                    adapter=adapter, root=test_root, checkpoint=checkpoint, data=data,
                    checkpoint_path=checkpoint_path, manifest=manifest,
                    left_models=models, left_optimizers=optimizers,
                    left_trainer=trainer, staging=staging,
                )
                tamper_rejections.update(probe.pop("_tamper_rejections"))
                if sample_rows is None:
                    sample_rows = probe.pop("_sample_rows")
                else:
                    probe.pop("_sample_rows")
                probes.append(probe)
            if time.perf_counter() - started > PILOT_WALL_SECONDS:
                raise B01ContractError("B4 pilot exceeded the 10 minute wall ceiling")
        if sample_rows is None or checkpoint0_data is None:
            raise B01ContractError("B4 persistence rollback fixture is absent")
        rollback = _rollback_probe(
            adapter=adapter, root=test_root, sample_rows=sample_rows,
            staging=staging, checkpoint_data=checkpoint0_data,
        )
        expected_tampers = {
            "MODEL", "OPTIMIZER", "ADAM_STEP", "FRONTIER", "WORK", "AUDIT",
            "SEED_PHASE", "TAPE", "COMMON_MODE_TAPE", "ORIGIN_ADDRESS", "LAW_REVISION", "ROLE_MASK",
            "LOSS_BITS", "PROJECTION_MASK", "ROW_ORDER",
        }
        if tamper_rejections != expected_tampers:
            raise B01ContractError("B4 pilot tamper rejection inventory differs")
        telemetry = monitor.stop()
        peak_rss = telemetry["end_to_end"]["peak_rss_bytes"]
        high_water = max(
            _tree_bytes(staging), telemetry["end_to_end"]["scratch_peak_bytes"],
            telemetry["end_to_end"]["durable_peak_bytes"],
        )
        if peak_rss > PILOT_PEAK_RSS_BYTES or high_water > PILOT_SCRATCH_DURABLE_BYTES:
            raise B01ContractError("B4 pilot exceeded RSS or scratch/durable ceiling")
        receipt = {
            "schema": "FRRIE_B01_B4_INDUCTION_RECEIPT_V1",
            "seed_label": TEST_SEED_LABEL, "checkpoint_schedule": list(CHECKPOINTS),
            "base_checkpoint0": base, "nonterminal_probes": probes,
            "terminal_checkpoint512": terminal,
            "rollback_fault": rollback,
            "tamper_matrix": {
                "injections": [
                    "MODEL", "OPTIMIZER", "ADAM_STEP", "FRONTIER", "WORK", "AUDIT",
                    "SEED_PHASE", "TAPE", "COMMON_MODE_TAPE", "ORIGIN_ADDRESS", "LAW_REVISION", "ROLE_MASK",
                    "LOSS_BITS", "PROJECTION_MASK", "ROW_ORDER",
                ],
                "all_rejected": True,
            },
            "transition_induction_contract": exact512_induction_contract(),
            "resource_observation": {
                "wall_seconds": time.perf_counter() - started,
                "scratch_durable_bytes": high_water, "peak_rss_bytes": peak_rss,
                "admission_minimum_bytes": min(
                    admission["available_physical_bytes"], admission["effective_available_bytes"],
                ),
                "active_supervisor_enforced": True,
            },
            "b4_complete": True, "test_component_only": True, "production_token": False,
        }
        validate_b4_induction_receipt(receipt)
        # Checkpoint payloads contain TEST parameters; do not publish them.
        shutil.rmtree(staging / "checkpoints")
        shutil.rmtree(staging / "suffix-shards")
        shutil.rmtree(staging / "rollback-faults")
        _write_once(staging / "B4-induction-receipt.json", canonical_json_bytes(receipt))
        _write_once(staging / "telemetry.json", canonical_json_bytes(telemetry))
        _publish_create_once_transaction(staging, final, incomplete)
        published = True
        final_receipt_bytes = (final / "B4-induction-receipt.json").read_bytes()
        final_receipt = json.loads(final_receipt_bytes.decode("ascii"))
        if canonical_json_bytes(final_receipt) != final_receipt_bytes:
            raise B01ContractError("B4 final receipt literal bytes differ")
        validate_b4_induction_receipt(final_receipt)
        if final_receipt != receipt:
            raise B01ContractError("B4 final receipt readback differs")
        return receipt
    except BaseException:
        try:
            monitor.stop()
        except BaseException:
            pass
        if published and final.exists():
            final.replace(incomplete)
        elif staging.exists():
            staging.replace(incomplete)
        raise


def _pilot_worker_entry(connection: Any, root: str) -> None:
    try:
        connection.send({
            "ok": True,
            "receipt": _execute_actual_b4_checkpoint_induction_pilot(root),
        })
    except BaseException as error:
        connection.send({"ok": False, "error": repr(error)})
    finally:
        connection.close()


def _terminate_owned_process_tree(pid: int) -> None:
    """Terminate the supervised worker and every descendant on Windows."""

    completed = subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        check=False, capture_output=True, text=True, timeout=30,
    )
    if completed.returncode not in (0, 128):
        raise B01ContractError("B4 supervisor could not terminate its process tree")


def _cleanup_exited_worker_native_artifacts(
    artifact: Path, *, worker_pid: int, artifact_preexisted: bool,
) -> None:
    """Delete only artifacts created by the now-exited supervised worker."""

    if artifact_preexisted:
        return
    candidates = _worker_native_artifact_paths(artifact, worker_pid=worker_pid)
    failures = []
    for path in candidates:
        try:
            if path.exists():
                path.unlink()
        except OSError as error:
            failures.append(f"{path}:{error}")
    if failures:
        raise B01ContractError(
            "B4 supervising parent could not clean exited-worker native artifacts: "
            + ";".join(failures)
        )


def _worker_native_artifact_paths(
    artifact: Path, *, worker_pid: int,
) -> tuple[Path, ...]:
    temporary = artifact.with_name(
        f"{artifact.stem}.building-{worker_pid}{artifact.suffix}"
    )
    return (
        artifact, temporary,
        *(temporary.with_suffix(suffix) for suffix in (".obj", ".pdb", ".lib", ".exp")),
    )


def _quarantine_supervised_transaction(
    *, final: Path, staging: Path, incomplete: Path,
) -> None:
    if incomplete.exists():
        return
    if final.exists():
        final.replace(incomplete)
    elif staging.exists():
        staging.replace(incomplete)


def _terminate_cleanup_quarantine(
    process: Any, *, artifact: Path, artifact_preexisted: bool,
    final: Path, staging: Path, incomplete: Path,
) -> None:
    failures = []
    try:
        _terminate_owned_process_tree(process.pid)
    except BaseException as error:
        failures.append(f"termination:{error!r}")
    finally:
        process.join(timeout=30)
        if process.is_alive():
            failures.append("process-still-alive")
        else:
            try:
                _cleanup_exited_worker_native_artifacts(
                    artifact, worker_pid=process.pid,
                    artifact_preexisted=artifact_preexisted,
                )
            except BaseException as error:
                failures.append(f"native-cleanup:{error!r}")
        try:
            _quarantine_supervised_transaction(
                final=final, staging=staging, incomplete=incomplete,
            )
        except BaseException as error:
            failures.append(f"quarantine:{error!r}")
    if failures:
        raise B01ContractError(
            "B4 supervisor termination/cleanup/quarantine failed: " + ";".join(failures)
        )


def _accept_supervised_worker_result(
    parent: Any, process: Any, *, final: Path, staging: Path, incomplete: Path,
    peak_rss: int, peak_storage: int,
) -> dict[str, Any]:
    accepted = False
    try:
        if not parent.poll(1):
            raise B01ContractError("B4 supervised worker returned no receipt")
        try:
            result = parent.recv()
        except EOFError as error:
            raise B01ContractError("B4 supervised worker pipe closed before receipt") from error
        if not isinstance(result, Mapping):
            raise B01ContractError("B4 supervised worker result fields differ")
        if process.exitcode != 0 or result.get("ok") is not True:
            raise B01ContractError(f"B4 supervised worker failed: {result.get('error')}")
        receipt = result.get("receipt")
        resource = receipt.get("resource_observation") if isinstance(receipt, Mapping) else None
        if not isinstance(receipt, Mapping) or not isinstance(resource, Mapping) or resource.get(
            "active_supervisor_enforced"
        ) is not True:
            raise B01ContractError("B4 active supervisor receipt is absent")
        if peak_rss > PILOT_PEAK_RSS_BYTES or peak_storage > PILOT_SCRATCH_DURABLE_BYTES:
            raise B01ContractError("B4 supervisor observed an over-ceiling completed worker")
        accepted = True
        return dict(receipt)
    finally:
        try:
            parent.close()
        finally:
            if not accepted:
                _quarantine_supervised_transaction(
                    final=final, staging=staging, incomplete=incomplete,
                )


def _supervised_storage_bytes(paths: tuple[Path, ...]) -> int:
    total = 0
    for path in paths:
        if path.is_file():
            total += path.stat().st_size
        elif path.is_dir():
            total += _tree_bytes(path)
    return total


def _active_ceiling_breach(*, elapsed: float, rss: int, storage: int) -> str | None:
    if elapsed > PILOT_WALL_SECONDS:
        return "WALL_SECONDS"
    if rss > PILOT_PEAK_RSS_BYTES:
        return "PROCESS_TREE_RSS"
    if storage > PILOT_SCRATCH_DURABLE_BYTES:
        return "SCRATCH_DURABLE_BYTES"
    return None


def run_actual_b4_checkpoint_induction_pilot(root: str | Path) -> dict[str, Any]:
    """Run once in a child with active wall/RSS/storage termination and quarantine."""

    final = Path(root).resolve(strict=False)
    staging = final.with_name(final.name + ".creating")
    incomplete = final.with_name(final.name + ".incomplete")
    receipt_path = final.with_name(final.name + ".admit-memory.json")
    packet_path = final.with_name(final.name + ".test-seed-packet.json")
    tracked = (final, staging, incomplete, receipt_path, packet_path)
    if any(path.exists() for path in tracked):
        raise B01ContractError("B4 pilot requires fresh create-once paths")
    context = multiprocessing.get_context("spawn")
    artifact = package_native_artifact_path().resolve(strict=False)
    artifact_preexisted = artifact.exists()
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_pilot_worker_entry, args=(child, str(final)),
        name="frrie-b4-supervised-pilot",
    )
    started = time.monotonic()
    process_started = False
    try:
        process.start()
        process_started = True
        run_native_paths = _worker_native_artifact_paths(
            artifact, worker_pid=process.pid,
        )
        child.close()
    except BaseException:
        try:
            child.close()
        finally:
            parent.close()
        if process_started:
            _terminate_cleanup_quarantine(
                process, artifact=artifact, artifact_preexisted=artifact_preexisted,
                final=final, staging=staging, incomplete=incomplete,
            )
        raise
    breach = None
    peak_rss = 0
    peak_storage = 0
    while process.is_alive():
        elapsed = time.monotonic() - started
        try:
            rss = sum(row.rss_bytes for row in _sample_windows_process_tree())
            storage = _supervised_storage_bytes((*tracked, *run_native_paths))
        except BaseException as error:
            breach = f"RESOURCE_OBSERVATION_FAILED:{error!r}"
            break
        peak_rss = max(peak_rss, rss)
        peak_storage = max(peak_storage, storage)
        breach = _active_ceiling_breach(
            elapsed=elapsed, rss=rss, storage=storage,
        )
        if breach is not None:
            break
        process.join(timeout=0.02)
    if breach is not None:
        try:
            _terminate_cleanup_quarantine(
                process, artifact=artifact, artifact_preexisted=artifact_preexisted,
                final=final, staging=staging, incomplete=incomplete,
            )
        finally:
            parent.close()
        raise B01ContractError(f"B4 active supervisor ceiling breach: {breach}")
    process.join(timeout=30)
    if process.is_alive():
        try:
            _terminate_cleanup_quarantine(
                process, artifact=artifact, artifact_preexisted=artifact_preexisted,
                final=final, staging=staging, incomplete=incomplete,
            )
        finally:
            parent.close()
        raise B01ContractError("B4 supervised worker did not exit")
    try:
        _cleanup_exited_worker_native_artifacts(
            artifact, worker_pid=process.pid,
            artifact_preexisted=artifact_preexisted,
        )
    except BaseException:
        _quarantine_supervised_transaction(
            final=final, staging=staging, incomplete=incomplete,
        )
        raise
    return _accept_supervised_worker_result(
        parent, process, final=final, staging=staging, incomplete=incomplete,
        peak_rss=peak_rss, peak_storage=peak_storage,
    )
