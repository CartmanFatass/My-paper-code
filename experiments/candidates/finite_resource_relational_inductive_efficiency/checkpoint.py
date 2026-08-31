"""Canonical FRRIE paired checkpoint with direct contract equality."""

from __future__ import annotations

import base64
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from .contracts.core import (
    FRRIE_CHECKPOINT_V1, FRRIE_MANIFEST_V1, LEARNED_ARMS, ContractError,
    canonical_json_bytes, validate_manifest,
)


class CheckpointMismatch(ContractError):
    pass


REQUIRED_PAYLOAD_FIELDS = (
    "manifest_contract", "native_contract", "seed_packet_contract", "update",
    "frontiers", "arm_state_bytes", "optimizer_state_bytes", "work_receipts",
    "rng_frontier",
)
FRONTIER_FIELDS = (
    "training_update", "minibatch_cursor", "environment_cursor",
    "evaluation_checkpoint_cursor",
)
WORK_RECEIPT_FIELDS = (
    "arm_id", "update", "environment_slots", "learned_decisions",
    "backward_calls", "adam_steps", "parameter_bytes", "flops", "workers",
    "threads", "native_width", "dtype", "checkpoint_io",
    "evaluation_opportunities", "tape_contract",
)
RNG_FRONTIER_FIELDS = ("schema", "stateless", "tape_contract")


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
    if set(payload) != set(REQUIRED_PAYLOAD_FIELDS):
        raise CheckpointMismatch("checkpoint payload is partial or has unknown fields")
    for field in ("manifest_contract", "native_contract", "seed_packet_contract"):
        if not isinstance(payload[field], Mapping) or not payload[field]:
            raise CheckpointMismatch(f"checkpoint {field} must be a nonempty mapping")
    update = payload["update"]
    if type(update) is not int or not 0 <= update <= 512:
        raise CheckpointMismatch("checkpoint update must be in [0,512]")
    manifest = payload["manifest_contract"]
    if manifest.get("schema") == FRRIE_MANIFEST_V1:
        try:
            validated_manifest = validate_manifest(manifest)
        except ContractError as exc:
            raise CheckpointMismatch("embedded manifest contract is invalid") from exc
        if update not in validated_manifest["training"]["checkpoints"]:
            raise CheckpointMismatch("checkpoint update is not a prospective opportunity")
    frontiers = payload["frontiers"]
    if not isinstance(frontiers, Mapping) or set(frontiers) != set(FRONTIER_FIELDS):
        raise CheckpointMismatch("checkpoint frontiers must use the exact replay schema")
    if any(type(frontiers[field]) is not int or frontiers[field] < 0 for field in FRONTIER_FIELDS):
        raise CheckpointMismatch("checkpoint frontiers must be nonnegative literal integers")
    if frontiers["training_update"] != update:
        raise CheckpointMismatch("training frontier differs from checkpoint update")
    receipts = payload["work_receipts"]
    if not isinstance(receipts, Mapping) or set(receipts) != set(LEARNED_ARMS):
        raise CheckpointMismatch("work receipts must bind both learned arms")
    parity_rows = []
    for arm in LEARNED_ARMS:
        row = receipts[arm]
        if not isinstance(row, Mapping) or set(row) != set(WORK_RECEIPT_FIELDS):
            raise CheckpointMismatch("work receipt fields must be exact")
        if row["arm_id"] != arm or row["update"] != update or row["dtype"] != "float32":
            raise CheckpointMismatch("work receipt arm/update/dtype contract mismatch")
        numeric = set(WORK_RECEIPT_FIELDS) - {"arm_id", "dtype", "tape_contract"}
        if any(type(row[field]) is not int or row[field] < 0 for field in numeric):
            raise CheckpointMismatch("work receipt counters must be nonnegative literal integers")
        if not isinstance(row["tape_contract"], Mapping):
            raise CheckpointMismatch("work receipt requires a direct tape contract")
        parity_rows.append({key: row[key] for key in WORK_RECEIPT_FIELDS if key != "arm_id"})
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
    canonical_json_bytes(payload)


def serialize_checkpoint(
    *, manifest_contract: Mapping[str, Any], native_contract: Mapping[str, Any],
    seed_packet_contract: Mapping[str, Any],
    update: int, frontiers: Mapping[str, Any], arm_state_bytes: Mapping[str, bytes],
    optimizer_state_bytes: Mapping[str, bytes], work_receipts: Mapping[str, Any],
    rng_frontier: Mapping[str, Any],
) -> bytes:
    for name, contract in (
        ("manifest_contract", manifest_contract),
        ("native_contract", native_contract),
        ("seed_packet_contract", seed_packet_contract),
    ):
        if not isinstance(contract, Mapping) or not contract:
            raise CheckpointMismatch(f"{name} must be a nonempty direct contract")
        canonical_json_bytes(contract)
    payload = {
        "manifest_contract": deepcopy(dict(manifest_contract)),
        "native_contract": deepcopy(dict(native_contract)),
        "seed_packet_contract": deepcopy(dict(seed_packet_contract)),
        "update": update,
        "frontiers": deepcopy(dict(frontiers)),
        "arm_state_bytes": _encode_pair(arm_state_bytes, "arm_state_bytes"),
        "optimizer_state_bytes": _encode_pair(optimizer_state_bytes, "optimizer_state_bytes"),
        "work_receipts": deepcopy(dict(work_receipts)),
        "rng_frontier": deepcopy(dict(rng_frontier)),
    }
    _validate_payload(payload)
    envelope = {
        "schema": FRRIE_CHECKPOINT_V1,
        "payload": payload,
        "complete": True,
    }
    return canonical_json_bytes(envelope)


def restore_checkpoint(
    data: bytes, *, manifest_contract: Mapping[str, Any], native_contract: Mapping[str, Any],
    seed_packet_contract: Mapping[str, Any], expected_update: int,
) -> dict[str, Any]:
    try:
        envelope = json.loads(data.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckpointMismatch("checkpoint is not canonical JSON") from exc
    if not isinstance(envelope, dict) or set(envelope) != {"schema", "payload", "complete"} or envelope.get("schema") != FRRIE_CHECKPOINT_V1 or envelope.get("complete") is not True:
        raise CheckpointMismatch("checkpoint schema/completeness mismatch")
    if canonical_json_bytes(envelope) != data:
        raise CheckpointMismatch("checkpoint serialization is not canonical")
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise CheckpointMismatch("checkpoint payload must be an object")
    _validate_payload(payload)
    expected = {
        "manifest_contract": dict(manifest_contract),
        "native_contract": dict(native_contract),
        "seed_packet_contract": dict(seed_packet_contract),
    }
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
