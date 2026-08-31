"""Canonical FRRIE paired checkpoint with direct contract equality."""

from __future__ import annotations

import base64
import json
from dataclasses import asdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from .arms import LearnedArm, PARAMETER_BYTE_COUNT, PROJECTION_BOXES
from .contracts.core import (
    FRRIE_CHECKPOINT_V2, FRRIE_MANIFEST_V1, FRRIE_MANIFEST_V2,
    FRRIE_SEALED_SEED_PACKET_V2, LEARNED_ARMS, ContractError,
    canonical_json_bytes, validate_manifest,
)
from .native_adapter import expected_native_contract
from .state_codec import decode_optimizer_state
from .work import validate_cumulative_checkpoint_work


class CheckpointMismatch(ContractError):
    pass


GENERIC_REQUIRED_PAYLOAD_FIELDS = (
    "manifest_contract", "native_contract", "seed_packet_contract", "update",
    "frontiers", "arm_state_bytes", "optimizer_state_bytes", "work_receipts",
    "rng_frontier",
)
FRRIE_V2_REQUIRED_PAYLOAD_FIELDS = (*GENERIC_REQUIRED_PAYLOAD_FIELDS, "seed_block")
GENERIC_FRONTIER_FIELDS = (
    "training_update", "minibatch_cursor", "environment_cursor",
    "evaluation_checkpoint_cursor",
)
FRRIE_V2_FRONTIER_FIELDS = (
    "training_update", "minibatch_cursor", "factual_episode_cursor",
    "factual_environment_slot_cursor",
    "alternative_suffix_environment_slot_cursor",
    "evaluation_checkpoint_cursor",
)
SEED_BINDING_FIELDS = (
    "packet_path", "schema", "version", "block_index", "block_label",
    "generation_provenance", "no_prior_use",
)
GENERIC_WORK_RECEIPT_FIELDS = (
    "arm_id", "update", "environment_slots", "learned_decisions",
    "backward_calls", "adam_steps", "parameter_bytes", "flops", "workers",
    "threads", "native_width", "dtype", "checkpoint_io",
    "evaluation_opportunities", "tape_contract",
)
RNG_FRONTIER_FIELDS = ("schema", "stateless", "tape_contract")


def _direct_equal(left: Any, right: Any) -> bool:
    try:
        return canonical_json_bytes(left) == canonical_json_bytes(right)
    except ContractError:
        return False


def _seed_binding(
    packet: Mapping[str, Any], manifest: Mapping[str, Any],
    packet_path: str | Path, seed_block: str,
) -> dict[str, Any]:
    from .preflight import _validate_seed_packet

    try:
        validated = _validate_seed_packet(packet, manifest)
    except ContractError as exc:
        raise CheckpointMismatch("current V2 seed packet is invalid") from exc
    manifest_path = manifest["sealed_seed_packet"]["path"]
    if str(packet_path) != manifest_path:
        raise CheckpointMismatch("seed packet path differs from manifest binding")
    blocks = manifest["seed_blocks"]
    if seed_block not in blocks:
        raise CheckpointMismatch("checkpoint seed block is not in the ordered manifest inventory")
    index = blocks.index(seed_block)
    if validated["blocks"][index] != seed_block:
        raise CheckpointMismatch("seed packet block order differs from manifest")
    return {
        "packet_path": manifest_path,
        "schema": FRRIE_SEALED_SEED_PACKET_V2,
        "version": 2,
        "block_index": index,
        "block_label": seed_block,
        "generation_provenance": validated["generation_provenance"],
        "no_prior_use": True,
    }


def _validate_sanitized_seed_binding(
    value: Any, manifest: Mapping[str, Any], seed_block: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != set(SEED_BINDING_FIELDS):
        raise CheckpointMismatch("checkpoint seed binding fields must be exact")
    blocks = manifest["seed_blocks"]
    index = blocks.index(seed_block) if seed_block in blocks else -1
    expected_path = manifest["sealed_seed_packet"]["path"]
    if (
        value["packet_path"] != expected_path
        or value["schema"] != FRRIE_SEALED_SEED_PACKET_V2
        or type(value["version"]) is not int or value["version"] != 2
        or type(value["block_index"]) is not int or value["block_index"] != index
        or value["block_label"] != seed_block
        or not isinstance(value["generation_provenance"], str)
        or not value["generation_provenance"]
        or value["no_prior_use"] is not True
    ):
        raise CheckpointMismatch("checkpoint sanitized seed binding differs from V2 inputs")


def learned_arm_state_bytes(arms: Mapping[str, LearnedArm]) -> dict[str, bytes]:
    """Return the exact arm-keyed bytes accepted by the canonical checkpoint."""
    if not isinstance(arms, Mapping) or set(arms) != set(LEARNED_ARMS):
        raise CheckpointMismatch("learned arms must bind exactly both arm IDs")
    state: dict[str, bytes] = {}
    for arm_id in LEARNED_ARMS:
        arm = arms[arm_id]
        if not isinstance(arm, LearnedArm) or arm.arm_id != arm_id:
            raise CheckpointMismatch("learned arm object ID differs from its checkpoint key")
        if arm.projection_box != PROJECTION_BOXES[arm_id]:
            raise CheckpointMismatch("learned arm projection box drift")
        try:
            state[arm_id] = arm.parameter_bytes()
        except ContractError as exc:
            raise CheckpointMismatch("learned arm parameter state is invalid") from exc
    return state


def restore_learned_arms(state: Mapping[str, bytes]) -> dict[str, LearnedArm]:
    """Restore arm objects and revalidate their IDs and projection boxes."""
    if not isinstance(state, Mapping) or set(state) != set(LEARNED_ARMS):
        raise CheckpointMismatch("learned arm state must bind exactly both arm IDs")
    restored: dict[str, LearnedArm] = {}
    for arm_id in LEARNED_ARMS:
        try:
            arm = LearnedArm.from_parameter_bytes(arm_id, state[arm_id])
        except (ContractError, TypeError) as exc:
            raise CheckpointMismatch(f"checkpoint arm state for {arm_id} is invalid") from exc
        if arm.arm_id != arm_id or arm.projection_box != PROJECTION_BOXES[arm_id]:
            raise CheckpointMismatch("restored learned arm identity/projection contract drift")
        restored[arm_id] = arm
    return restored


def _encode_pair(value: Mapping[str, bytes], field: str) -> dict[str, str]:
    if set(value) != set(LEARNED_ARMS):
        raise CheckpointMismatch(f"{field} must bind exactly both learned arms")
    encoded: dict[str, str] = {}
    for arm in LEARNED_ARMS:
        blob = value[arm]
        if not isinstance(blob, bytes) or not blob:
            raise CheckpointMismatch(f"{field}.{arm} must be nonempty bytes")
        encoded[arm] = base64.b64encode(blob).decode("ascii")
    return encoded


def _validate_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise CheckpointMismatch("checkpoint payload must be an object")
    manifest0 = payload.get("manifest_contract")
    if not isinstance(manifest0, Mapping):
        raise CheckpointMismatch("checkpoint manifest_contract must be a nonempty mapping")
    production_v2 = manifest0.get("schema") == FRRIE_MANIFEST_V2
    required_fields = (
        FRRIE_V2_REQUIRED_PAYLOAD_FIELDS if production_v2 else GENERIC_REQUIRED_PAYLOAD_FIELDS
    )
    if set(payload) != set(required_fields):
        raise CheckpointMismatch("checkpoint payload is partial or has unknown fields")
    for field in ("manifest_contract", "native_contract", "seed_packet_contract"):
        if not isinstance(payload[field], Mapping) or not payload[field]:
            raise CheckpointMismatch(f"checkpoint {field} must be a nonempty mapping")
    update = payload["update"]
    if type(update) is not int or not 0 <= update <= 512:
        raise CheckpointMismatch("checkpoint update must be in [0,512]")
    manifest = payload["manifest_contract"]
    production_manifest: dict[str, Any] | None = None
    manifest_schema = manifest.get("schema")
    if manifest_schema == FRRIE_MANIFEST_V1:
        raise CheckpointMismatch("FRRIE manifest V1 is a rejected legacy scaffold")
    if manifest_schema == FRRIE_MANIFEST_V2:
        try:
            production_manifest = validate_manifest(manifest)
        except ContractError as exc:
            raise CheckpointMismatch("embedded manifest contract is invalid") from exc
        if update not in production_manifest["training"]["checkpoints"]:
            raise CheckpointMismatch("checkpoint update is not a prospective opportunity")
        seed_block = payload["seed_block"]
        if not isinstance(seed_block, str) or seed_block not in production_manifest["seed_blocks"]:
            raise CheckpointMismatch("checkpoint seed block is not one ordered manifest block")
        _validate_sanitized_seed_binding(
            payload["seed_packet_contract"], production_manifest, seed_block
        )
        try:
            expected_native = asdict(expected_native_contract(production_manifest["compute"]))
        except Exception as exc:
            raise CheckpointMismatch("manifest native/compute contract is invalid") from exc
        if not _direct_equal(payload["native_contract"], expected_native):
            raise CheckpointMismatch("checkpoint native contract differs from manifest/adapter V2")
    frontiers = payload["frontiers"]
    frontier_fields = (
        FRRIE_V2_FRONTIER_FIELDS if production_manifest is not None else GENERIC_FRONTIER_FIELDS
    )
    if not isinstance(frontiers, Mapping) or set(frontiers) != set(frontier_fields):
        raise CheckpointMismatch("checkpoint frontiers must use the exact replay schema")
    if any(type(frontiers[field]) is not int or frontiers[field] < 0 for field in frontier_fields):
        raise CheckpointMismatch("checkpoint frontiers must be nonnegative literal integers")
    if frontiers["training_update"] != update:
        raise CheckpointMismatch("training frontier differs from checkpoint update")
    completed_checkpoint_io: list[int] = []
    if production_manifest is not None:
        completed_checkpoint_io = [
            checkpoint for checkpoint in production_manifest["training"]["checkpoints"]
            if checkpoint <= update
        ]
        expected_frontiers = {
            "training_update": update,
            "minibatch_cursor": 0,
            "factual_episode_cursor": update * 64,
            "factual_environment_slot_cursor": 393_216,
            "alternative_suffix_environment_slot_cursor": 1_490_944,
            # The sole update-512 checkpoint is post-train and pre-evaluation.
            "evaluation_checkpoint_cursor": 0,
        }
        if dict(frontiers) != expected_frontiers:
            raise CheckpointMismatch("FRRIE checkpoint is not a completed-update boundary")
    receipts = payload["work_receipts"]
    if production_manifest is not None:
        try:
            validate_cumulative_checkpoint_work(receipts, production_manifest["compute"])
        except ValueError as exc:
            raise CheckpointMismatch("FRRIE cumulative work differs from the exact v2 boundary") from exc
        if receipts["training_update"] != update:
            raise CheckpointMismatch("FRRIE cumulative work update differs from checkpoint update")
        if receipts["arms"][LEARNED_ARMS[0]] != receipts["arms"][LEARNED_ARMS[1]]:
            raise CheckpointMismatch("checkpoint paired cumulative work differs")
        for arm in LEARNED_ARMS:
            row = receipts["arms"][arm]
            if (
                row["backward_calls"] != update
                or row["adam_steps"] != update
                or row["parameter_bytes"] != PARAMETER_BYTE_COUNT
                or row["checkpoint_io"] != len(completed_checkpoint_io)
                or row["evaluation_opportunities"] != 0
            ):
                raise CheckpointMismatch("FRRIE cumulative work completed counters are invalid")
    else:
        if not isinstance(receipts, Mapping) or set(receipts) != set(LEARNED_ARMS):
            raise CheckpointMismatch("work receipts must bind both learned arms")
        parity_rows = []
        for arm in LEARNED_ARMS:
            row = receipts[arm]
            if not isinstance(row, Mapping) or set(row) != set(GENERIC_WORK_RECEIPT_FIELDS):
                raise CheckpointMismatch("work receipt fields must be exact")
            if row["arm_id"] != arm or row["update"] != update or row["dtype"] != "float32":
                raise CheckpointMismatch("work receipt arm/update/dtype contract mismatch")
            numeric = set(GENERIC_WORK_RECEIPT_FIELDS) - {"arm_id", "dtype", "tape_contract"}
            if any(type(row[field]) is not int or row[field] < 0 for field in numeric):
                raise CheckpointMismatch("work receipt counters must be nonnegative literal integers")
            if not isinstance(row["tape_contract"], Mapping):
                raise CheckpointMismatch("work receipt requires a direct tape contract")
            parity_rows.append({
                key: row[key] for key in GENERIC_WORK_RECEIPT_FIELDS if key != "arm_id"
            })
        if parity_rows[0] != parity_rows[1]:
            raise CheckpointMismatch("checkpoint paired work receipts differ")
    rng = payload["rng_frontier"]
    if not isinstance(rng, Mapping) or set(rng) != set(RNG_FRONTIER_FIELDS):
        raise CheckpointMismatch("RNG frontier fields must be exact")
    if rng["schema"] != "FRRIE_STATELESS_RNG_FRONTIER_V1" or rng["stateless"] is not True:
        raise CheckpointMismatch("RNG frontier is not the frozen stateless contract")
    if not isinstance(rng["tape_contract"], (Mapping, list)):
        raise CheckpointMismatch("RNG frontier requires a direct tape contract")
    for field in ("arm_state_bytes", "optimizer_state_bytes"):
        pair = payload[field]
        if not isinstance(pair, Mapping) or set(pair) != set(LEARNED_ARMS):
            raise CheckpointMismatch(f"checkpoint {field} pair is partial")
        for arm in LEARNED_ARMS:
            try:
                decoded = base64.b64decode(pair[arm], validate=True)
            except (ValueError, TypeError) as exc:
                raise CheckpointMismatch(f"checkpoint {field} is invalid") from exc
            if not decoded:
                raise CheckpointMismatch(f"checkpoint {field} contains empty state")
            if field == "arm_state_bytes" and production_manifest is not None:
                try:
                    restored_arm = LearnedArm.from_parameter_bytes(arm, decoded)
                except ContractError as exc:
                    raise CheckpointMismatch(f"checkpoint arm state for {arm} is invalid") from exc
                if restored_arm.arm_id != arm or restored_arm.projection_box != PROJECTION_BOXES[arm]:
                    raise CheckpointMismatch("checkpoint arm identity/projection contract drift")
            if field == "optimizer_state_bytes" and production_manifest is not None:
                try:
                    optimizer = decode_optimizer_state(decoded)
                except ContractError as exc:
                    raise CheckpointMismatch(f"checkpoint optimizer state for {arm} is invalid") from exc
                if optimizer.step != update:
                    raise CheckpointMismatch("checkpoint Adam step differs from training update")
    canonical_json_bytes(payload)


def serialize_checkpoint(
    *, manifest_contract: Mapping[str, Any], native_contract: Mapping[str, Any],
    seed_packet_contract: Mapping[str, Any],
    update: int, frontiers: Mapping[str, Any], arm_state_bytes: Mapping[str, bytes],
    optimizer_state_bytes: Mapping[str, bytes], work_receipts: Mapping[str, Any],
    rng_frontier: Mapping[str, Any], seed_block: str | None = None,
    seed_packet_path: str | Path | None = None,
) -> bytes:
    for name, contract in (
        ("manifest_contract", manifest_contract),
        ("native_contract", native_contract),
        ("seed_packet_contract", seed_packet_contract),
    ):
        if not isinstance(contract, Mapping) or not contract:
            raise CheckpointMismatch(f"{name} must be a nonempty direct contract")
        canonical_json_bytes(contract)
    production_v2 = manifest_contract.get("schema") == FRRIE_MANIFEST_V2
    if production_v2:
        manifest = validate_manifest(manifest_contract)
        if seed_block is None or seed_packet_path is None:
            raise CheckpointMismatch("V2 checkpoint requires seed block and current packet path")
        seed_binding: Mapping[str, Any] = _seed_binding(
            seed_packet_contract, manifest, seed_packet_path, seed_block
        )
    else:
        seed_binding = seed_packet_contract
    payload = {
        "manifest_contract": deepcopy(dict(manifest_contract)),
        "native_contract": deepcopy(dict(native_contract)),
        "seed_packet_contract": deepcopy(dict(seed_binding)),
        "update": update,
        "frontiers": deepcopy(dict(frontiers)),
        "arm_state_bytes": _encode_pair(arm_state_bytes, "arm_state_bytes"),
        "optimizer_state_bytes": _encode_pair(optimizer_state_bytes, "optimizer_state_bytes"),
        "work_receipts": deepcopy(dict(work_receipts)),
        "rng_frontier": deepcopy(dict(rng_frontier)),
    }
    if production_v2:
        payload["seed_block"] = seed_block
    _validate_payload(payload)
    envelope = {
        "schema": FRRIE_CHECKPOINT_V2,
        "payload": payload,
        "complete": True,
    }
    return canonical_json_bytes(envelope)


def restore_checkpoint(
    data: bytes, *, manifest_contract: Mapping[str, Any], native_contract: Mapping[str, Any],
    seed_packet_contract: Mapping[str, Any], expected_update: int,
    expected_seed_block: str | None = None,
    seed_packet_path: str | Path | None = None,
) -> dict[str, Any]:
    try:
        envelope = json.loads(data.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckpointMismatch("checkpoint is not canonical JSON") from exc
    if not isinstance(envelope, dict) or set(envelope) != {"schema", "payload", "complete"} or envelope.get("schema") != FRRIE_CHECKPOINT_V2 or envelope.get("complete") is not True:
        raise CheckpointMismatch("checkpoint schema/completeness mismatch")
    if canonical_json_bytes(envelope) != data:
        raise CheckpointMismatch("checkpoint serialization is not canonical")
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise CheckpointMismatch("checkpoint payload must be an object")
    _validate_payload(payload)
    production_v2 = manifest_contract.get("schema") == FRRIE_MANIFEST_V2
    expected = {
        "manifest_contract": dict(manifest_contract),
        "native_contract": dict(native_contract),
    }
    if production_v2:
        manifest = validate_manifest(manifest_contract)
        if expected_seed_block is None or seed_packet_path is None:
            raise CheckpointMismatch("V2 restore requires current seed packet path and block")
        expected["seed_packet_contract"] = _seed_binding(
            seed_packet_contract, manifest, seed_packet_path, expected_seed_block
        )
        if payload["seed_block"] != expected_seed_block:
            raise CheckpointMismatch("checkpoint seed block mismatch")
    else:
        expected["seed_packet_contract"] = dict(seed_packet_contract)
    for field, value in expected.items():
        if payload[field] != value:
            raise CheckpointMismatch(f"checkpoint {field} mismatch")
    if type(expected_update) is not int or payload["update"] != expected_update:
        raise CheckpointMismatch("checkpoint update mismatch")
    for field in ("arm_state_bytes", "optimizer_state_bytes"):
        if set(payload[field]) != set(LEARNED_ARMS):
            raise CheckpointMismatch(f"checkpoint {field} pair is partial")
        try:
            payload[field] = {arm: base64.b64decode(payload[field][arm], validate=True) for arm in LEARNED_ARMS}
        except (ValueError, TypeError) as exc:
            raise CheckpointMismatch(f"checkpoint {field} is invalid") from exc
        if any(not blob for blob in payload[field].values()):
            raise CheckpointMismatch(f"checkpoint {field} contains empty state")
    return payload


def write_checkpoint_atomic(path: str | Path, data: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    if target.exists():
        raise CheckpointMismatch("checkpoint publication is create-only")
    if temporary.exists():
        raise CheckpointMismatch("stale checkpoint temporary exists")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            import os
            os.fsync(handle.fileno())
        # Hard-link publication gives create-only atomic visibility.
        os.link(temporary, target)
        temporary.unlink()
    finally:
        if temporary.exists():
            temporary.unlink()


def block_checkpoint_path(
    manifest_contract: Mapping[str, Any], seed_block: str, *, update: int = 512,
) -> Path:
    manifest = validate_manifest(manifest_contract)
    if seed_block not in manifest["seed_blocks"]:
        raise CheckpointMismatch("checkpoint seed block is outside the manifest inventory")
    if type(update) is not int or update != 512:
        raise CheckpointMismatch("FRRIE V2 exposes only the update-512 block checkpoint")
    root = Path(manifest["roots"]["checkpoint"]).resolve(strict=False)
    target = (root / seed_block / "update-512.json").resolve(strict=False)
    if target == root or not target.is_relative_to(root):
        raise CheckpointMismatch("block checkpoint path escapes the manifest checkpoint root")
    return target


def write_block_checkpoint_atomic(
    manifest_contract: Mapping[str, Any], seed_block: str, data: bytes,
) -> Path:
    manifest = validate_manifest(manifest_contract)
    try:
        envelope = json.loads(data.decode("ascii"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckpointMismatch("block checkpoint publication requires canonical V2 bytes") from exc
    if (
        not isinstance(envelope, dict)
        or envelope.get("schema") != FRRIE_CHECKPOINT_V2
        or envelope.get("complete") is not True
        or canonical_json_bytes(envelope) != data
        or not isinstance(envelope.get("payload"), Mapping)
        or envelope["payload"].get("seed_block") != seed_block
        or not _direct_equal(envelope["payload"].get("manifest_contract"), manifest)
    ):
        raise CheckpointMismatch("block checkpoint bytes differ from publication path binding")
    target = block_checkpoint_path(manifest_contract, seed_block)
    write_checkpoint_atomic(target, data)
    return target
