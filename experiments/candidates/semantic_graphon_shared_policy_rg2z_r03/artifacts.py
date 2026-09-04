"""Fresh-root and atomic-packet persistence for the frozen 24-seed panel."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Mapping
import uuid

import torch

from .authorization import ARMS, ACTION, ProductionPermit, parse_lease_timestamp, require_exact_certificate
from .config import (
    ADAM_BETAS,
    ADAM_EPSILON,
    COUNTER_ROOT,
    DEVICE,
    EDGE_BETA_BOUND,
    EPISODES_PER_TRAIN_ROSTER,
    EPISODES_PER_UPDATE,
    GRADIENT_NORM_CLIP,
    LEARNING_RATE,
    PHY_BETA_BOUND,
    DIRECTION,
    REVISION,
    SEEDS,
    TRAINING_UPDATES,
    TRAIN_ROSTERS,
)


SCHEMA = "SGSP-RG2Z-R03-ATOMIC-PANEL-20260819"
FRONTIER_SCHEMA = "SGSP-RG2Z-R03-NONEVALUABLE-TRAINING-FRONTIER-20260819"


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _write_bytes(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _lease_binding_from_permit(permit: ProductionPermit) -> dict[str, object]:
    authorization = permit.payload
    return {
        "lease_token_sha256": hashlib.sha256(
            str(authorization["lease_token"]).encode("utf-8")
        ).hexdigest(),
        "stage_boundary": authorization["stage_boundary"],
        "direction": DIRECTION,
        "revision": REVISION,
        "action": ACTION,
        "result_root": authorization["result_root"],
        "issued_at_utc": authorization["issued_at_utc"],
        "not_after_utc": authorization["not_after_utc"],
        "authorized_seeds_at_initialization": authorization["authorized_seeds"],
        "counter_root": COUNTER_ROOT,
        "device": authorization["device"],
        "certificate_sha256": authorization["certificate_sha256"],
    }


def create_fresh_result_root(
    path: Path,
    permit: ProductionPermit,
    certificate_path: Path,
) -> None:
    if not isinstance(permit, ProductionPermit):
        raise PermissionError("fresh result root requires a validated ProductionPermit")
    permit.assert_active()
    certificate = require_exact_certificate(certificate_path)
    if permit.payload.get("result_root") != str(path.resolve()):
        raise PermissionError("fresh result root differs from the active permit")
    if permit.payload.get("certificate_sha256") != _sha256(certificate_path):
        raise PermissionError("fresh result root certificate differs from the active permit")
    if certificate != require_exact_certificate(certificate_path):
        raise PermissionError("fresh result root certificate changed during validation")
    lease_binding = _lease_binding_from_permit(permit)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"result root must be fresh: {path}")
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    temporary.mkdir(exist_ok=False)
    try:
        _write_bytes(temporary / "MANIFEST.json", _json_bytes({
            "direction": DIRECTION,
            "revision": REVISION,
            "action": ACTION,
            "schema": SCHEMA,
            "registered_seeds": list(SEEDS),
            "counter_root": COUNTER_ROOT,
            "device": str(DEVICE),
            "preactivity_certificate_sha256": _sha256(certificate_path),
            "fresh_result_root": True,
            "seed_replacement_allowed": False,
            "required_arm_count": len(ARMS),
            "required_complete_seed_count": len(SEEDS),
        }))
        _write_bytes(temporary / "LEASE_BINDING.json", _json_bytes(lease_binding))
        permit.assert_active()
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def validate_result_root(path: Path) -> dict[str, object]:
    manifest = json.loads((path / "MANIFEST.json").read_text(encoding="utf-8"))
    required = {
        "direction": DIRECTION,
        "revision": REVISION,
        "action": ACTION,
        "schema": SCHEMA,
        "registered_seeds": list(SEEDS),
        "counter_root": COUNTER_ROOT,
        "device": str(DEVICE),
        "fresh_result_root": True,
        "seed_replacement_allowed": False,
        "required_arm_count": len(ARMS),
        "required_complete_seed_count": len(SEEDS),
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise RuntimeError(f"result root lifecycle mismatch for {key}")
    return manifest


def validate_certificate_binding(root: Path, certificate_path: Path) -> None:
    manifest = validate_result_root(root)
    require_exact_certificate(certificate_path)
    if manifest.get("preactivity_certificate_sha256") != _sha256(certificate_path):
        raise RuntimeError("result root is not bound to this exact certificate")


def validate_lease_binding(root: Path, authorization: dict[str, object]) -> None:
    binding = json.loads((root / "LEASE_BINDING.json").read_text(encoding="utf-8"))
    exact = {
        "direction": DIRECTION, "revision": REVISION, "action": ACTION,
        "result_root": str(root.resolve()), "counter_root": COUNTER_ROOT,
        "device": str(DEVICE), "stage_boundary": authorization.get("stage_boundary"),
        "certificate_sha256": authorization.get("certificate_sha256"),
    }
    for key, expected in exact.items():
        if binding.get(key) != expected:
            raise PermissionError(f"continuation lease changed frozen {key}")
    for key in ("stage_boundary", "counter_root", "device"):
        if binding.get(key) != authorization.get(key):
            raise PermissionError(f"continuation lease changed frozen {key}")
    parse_lease_timestamp(binding["issued_at_utc"], issued_boundary=True)
    parse_lease_timestamp(binding["not_after_utc"], issued_boundary=False)


def _require_bound_permit(root: Path, permit: ProductionPermit, certificate_path: Path) -> None:
    if not isinstance(permit, ProductionPermit):
        raise PermissionError("atomic artifacts require a validated ProductionPermit")
    permit.assert_active()
    validate_certificate_binding(root, certificate_path)
    validate_lease_binding(root, permit.payload)


def expected_training_metadata(seed: int) -> dict[str, object]:
    """Exact technical audit facts for one completed matched training pair."""
    return {
        "seed": seed,
        "completed_updates": TRAINING_UPDATES,
        "checkpoint": "immediately_after_update_512",
        "checkpoint_identity": "only_evaluable_state_immediately_after_update_512",
        "initial_common_tensors_bitwise_equal": True,
        "updates_per_arm": {arm: TRAINING_UPDATES for arm in ARMS},
        "training_worlds": TRAINING_UPDATES * EPISODES_PER_UPDATE,
        "learned_arm_unrolls": TRAINING_UPDATES * EPISODES_PER_UPDATE * len(ARMS),
        "backward_calls": TRAINING_UPDATES * len(ARMS),
        "batch_roster_order": list(TRAIN_ROSTERS) * EPISODES_PER_TRAIN_ROSTER,
        "episodes_per_update": EPISODES_PER_UPDATE,
        "episodes_per_roster_per_update": EPISODES_PER_TRAIN_ROSTER,
        "equal_episode_weighting": True,
        "same_optimizer_hyperparameters_and_work_per_arm": True,
        "optimizer": {
            "name": "Adam",
            "learning_rate": LEARNING_RATE,
            "betas": list(ADAM_BETAS),
            "epsilon": ADAM_EPSILON,
            "weight_decay": 0.0,
            "foreach": False,
        },
        "gradient_norm_clip": GRADIENT_NORM_CLIP,
        "beta_projection_after_every_update": True,
        "beta_projection_bounds": {
            "PHY-TRUST": PHY_BETA_BOUND,
            "EDGE-FLEX": EDGE_BETA_BOUND,
        },
        "full_bptt": True,
        "recurrent_state_truncated": False,
    }


def _require_training_metadata(value: object, seed: int) -> dict[str, object]:
    expected = expected_training_metadata(seed)
    if value != expected:
        raise RuntimeError("seed packet training audit metadata mismatch")
    return expected


def _require_semantic_packet(packet: dict[str, object], seed: int) -> dict[str, object]:
    required = {"revision": REVISION, "action": ACTION, "seed": seed, "arms": list(ARMS), "checkpoint_identity": "only_evaluable_state_immediately_after_update_512", "worlds_and_agents_are_inferential_replicates": False, "seed_is_inferential_unit": True, "atomic_payload_complete": True}
    for key, expected in required.items():
        if packet.get(key) != expected:
            raise RuntimeError(f"seed packet semantic mismatch for {key}")
    for key in ("training", "evaluation", "deterministic_checkpoint_audit", "structural_checkpoint_audit"):
        if not isinstance(packet.get(key), Mapping):
            raise RuntimeError(f"seed packet lacks complete {key} evidence")
    _require_training_metadata(packet["training"], seed)
    from .statistics import _default_packet_valid
    if not _default_packet_valid(packet):
        raise RuntimeError("seed packet fails the complete registered statistics audit")
    return dict(packet)


def _frontier_path(root: Path, seed: int) -> Path:
    return root / f".seed-{seed}.training-frontier.pt"


def _digest_value(digest: "hashlib._Hash", value: object) -> None:
    """Hash nested torch state independently of pickle/container encoding."""
    if isinstance(value, torch.Tensor):
        tensor = value.detach().cpu().contiguous()
        digest.update(b"tensor\0")
        digest.update(str(tensor.dtype).encode("ascii") + b"\0")
        digest.update(_json_bytes(list(tensor.shape)))
        # Adam stores its step counter as a zero-dimensional tensor. Flatten
        # before byte reinterpretation so scalar and non-scalar state tensors
        # share the same exact deterministic digest path.
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
    elif isinstance(value, Mapping):
        digest.update(b"mapping\0")
        for key in sorted(value, key=lambda item: (type(item).__name__, repr(item))):
            _digest_value(digest, key)
            _digest_value(digest, value[key])
    elif isinstance(value, (list, tuple)):
        digest.update(b"list\0" if isinstance(value, list) else b"tuple\0")
        for item in value:
            _digest_value(digest, item)
    elif value is None:
        digest.update(b"none\0")
    elif isinstance(value, bool):
        digest.update(b"bool\0" + (b"1" if value else b"0"))
    elif isinstance(value, int):
        digest.update(b"int\0" + str(value).encode("ascii") + b"\0")
    elif isinstance(value, float):
        digest.update(b"float\0" + _json_bytes(value))
    elif isinstance(value, str):
        digest.update(b"str\0" + value.encode("utf-8") + b"\0")
    else:
        raise TypeError(f"unsupported resume-state value type: {type(value).__name__}")


def _payload_digest(payload: Mapping[object, object]) -> str:
    digest = hashlib.sha256()
    _digest_value(digest, payload)
    return digest.hexdigest()


def _frontier_metadata(
    root: Path,
    certificate_path: Path,
    seed: int,
    update: int,
) -> dict[str, object]:
    certificate = require_exact_certificate(certificate_path)
    return {
        "schema": FRONTIER_SCHEMA,
        "direction": DIRECTION,
        "revision": REVISION,
        "action": ACTION,
        "counter_root": COUNTER_ROOT,
        "device": str(DEVICE),
        "certificate_sha256": _sha256(certificate_path),
        "source_hashes": certificate["source_hashes"],
        "result_root": str(root.resolve()),
        "seed": seed,
        "matched_update": update,
        "arms": list(ARMS),
        "checkpoint_identity": "non_evaluable_resume_state_after_matched_update",
        "evaluable": False,
        "partial_interpretation_allowed": False,
        "contains_returns": False,
        "contains_evaluation": False,
        "contains_endpoints": False,
        "contains_partial_summaries": False,
        "training": expected_training_metadata(seed),
    }


def write_training_frontier(
    root: Path,
    permit: ProductionPermit,
    certificate_path: Path,
    seed: int,
    update: int,
    models: Mapping[str, object],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> Path:
    """Atomically replace the sole non-evaluable state after a matched update."""
    _require_bound_permit(root, permit, certificate_path)
    permit.require_seed(seed)
    if seed not in SEEDS or update not in range(1, TRAINING_UPDATES + 1):
        raise ValueError("resume frontier requires a registered seed and matched update 1..512")
    if set(models) != set(ARMS) or set(optimizers) != set(ARMS):
        raise ValueError("resume frontier requires both learned arms and both optimizers")
    payload: dict[str, object] = {
        "metadata": _frontier_metadata(root, certificate_path, seed, update),
        "models": {arm: models[arm].state_dict() for arm in ARMS},
        "optimizers": {arm: optimizers[arm].state_dict() for arm in ARMS},
    }
    envelope = {"payload": payload, "payload_sha256": _payload_digest(payload)}
    destination = _frontier_path(root, seed)
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            torch.save(envelope, stream)
            stream.flush()
            os.fsync(stream.fileno())
        permit.assert_active()
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def load_training_frontier(
    root: Path,
    permit: ProductionPermit,
    certificate_path: Path,
    seed: int,
    models: Mapping[str, object],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> int | None:
    """Validate and restore the exact matched-update frontier, if present."""
    _require_bound_permit(root, permit, certificate_path)
    permit.require_seed(seed)
    path = _frontier_path(root, seed)
    if not path.exists():
        return None
    envelope = torch.load(path, map_location=DEVICE, weights_only=True)
    if not isinstance(envelope, Mapping) or set(envelope) != {"payload", "payload_sha256"}:
        raise RuntimeError("resume frontier envelope is malformed")
    payload = envelope["payload"]
    if not isinstance(payload, Mapping) or set(payload) != {"metadata", "models", "optimizers"}:
        raise RuntimeError("resume frontier payload is malformed")
    if envelope["payload_sha256"] != _payload_digest(payload):
        raise RuntimeError("resume frontier payload digest mismatch")
    metadata = payload["metadata"]
    if not isinstance(metadata, Mapping):
        raise RuntimeError("resume frontier metadata is malformed")
    update = metadata.get("matched_update")
    if not isinstance(update, int) or update not in range(1, TRAINING_UPDATES + 1):
        raise RuntimeError("resume frontier matched update is invalid")
    if dict(metadata) != _frontier_metadata(root, certificate_path, seed, update):
        raise RuntimeError("resume frontier exact binding mismatch")
    model_states, optimizer_states = payload["models"], payload["optimizers"]
    if not isinstance(model_states, Mapping) or set(model_states) != set(ARMS):
        raise RuntimeError("resume frontier model states are incomplete")
    if not isinstance(optimizer_states, Mapping) or set(optimizer_states) != set(ARMS):
        raise RuntimeError("resume frontier optimizer states are incomplete")
    if set(models) != set(ARMS) or set(optimizers) != set(ARMS):
        raise ValueError("resume restore requires both learned arms and both optimizers")
    for arm in ARMS:
        models[arm].load_state_dict(model_states[arm], strict=True)
        optimizers[arm].load_state_dict(optimizer_states[arm])
    return update


def write_atomic_seed_packet(root: Path, permit: ProductionPermit, certificate_path: Path, seed: int, models: Mapping[str, object], packet: dict[str, object]) -> Path:
    _require_bound_permit(root, permit, certificate_path)
    validate_result_root(root)
    if seed not in permit.payload["authorized_seeds"] or set(models) != set(ARMS):
        raise ValueError("atomic packet requires one registered seed and every learned arm")
    destination = root / f"seed-{seed}"
    if destination.exists():
        raise FileExistsError(f"registered seed may not be replaced: {seed}")
    validated_packet = _require_semantic_packet(packet, seed)
    temporary = root / f".seed-{seed}.{uuid.uuid4().hex}.tmp"
    temporary.mkdir(exist_ok=False)
    try:
        checkpoint_path = temporary / "checkpoint-update-512.pt"
        torch.save({arm: model.state_dict() for arm, model in models.items()}, checkpoint_path)
        packet_path = temporary / "packet.json"
        _write_bytes(packet_path, _json_bytes(validated_packet))
        _write_bytes(temporary / "COMPLETE.json", _json_bytes({
            "seed": seed,
            "revision": REVISION,
            "action": ACTION,
            "schema": SCHEMA,
            "arms": list(ARMS),
            "checkpoint_sha256": _sha256(checkpoint_path),
            "packet_sha256": _sha256(packet_path),
            "atomic_complete": True,
        }))
        permit.assert_active()
        os.replace(temporary, destination)
        frontier = _frontier_path(root, seed)
        if frontier.exists():
            frontier.unlink()
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return destination


def load_complete_seed_packet(root: Path, permit: ProductionPermit, certificate_path: Path, seed: int) -> dict[str, object]:
    _require_bound_permit(root, permit, certificate_path)
    permit.require_seed(seed)
    directory = root / f"seed-{seed}"
    complete_path, packet_path = directory / "COMPLETE.json", directory / "packet.json"
    checkpoint_path = directory / "checkpoint-update-512.pt"
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    required = {
        "atomic_complete": True, "seed": seed, "revision": REVISION,
        "action": ACTION, "schema": SCHEMA, "arms": list(ARMS),
    }
    for key, expected in required.items():
        if complete.get(key) != expected:
            raise RuntimeError(f"seed {seed} is not atomically complete")
    if complete.get("packet_sha256") != _sha256(packet_path) or complete.get("checkpoint_sha256") != _sha256(checkpoint_path):
        raise RuntimeError(f"seed {seed} packet digest mismatch")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (
        packet.get("revision") != REVISION or packet.get("action") != ACTION
        or packet.get("seed") != seed or packet.get("arms") != list(ARMS)
        or packet.get("atomic_payload_complete") is not True
    ):
        raise RuntimeError(f"seed {seed} packet metadata mismatch")
    return _require_semantic_packet(packet, seed)
