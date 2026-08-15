from __future__ import annotations

import hashlib
from datetime import timedelta
import json
import os
from pathlib import Path
import shutil
import uuid

import torch

from .authorization import parse_lease_timestamp
from .config import ARMS, DIRECTION, REGISTERED, REVISION, SCHEMA, SEEDS
from .policies import SharedSGSPPolicy


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


def require_exact_certificate(path: Path) -> dict[str, object]:
    certificate = json.loads(path.read_text(encoding="utf-8"))
    if certificate.get("revision") != REVISION or certificate.get("passed") is not True:
        raise RuntimeError("a passing exact-revision preactivity certificate is required")
    if certificate.get("registered_stochastic_object_materialized") is not False:
        raise RuntimeError("certificate must attest no registered stochastic materialization")
    return certificate


def create_fresh_result_root(
    path: Path, certificate_path: Path, lease_binding: dict[str, object],
) -> None:
    require_exact_certificate(certificate_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"result root must be fresh: {path}")
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    temporary.mkdir(exist_ok=False)
    try:
        _write_bytes(temporary / "MANIFEST.json", _json_bytes({
            "direction": DIRECTION,
            "revision": REVISION,
            "schema": SCHEMA,
            "registered_config": REGISTERED.manifest(),
            "registered_seeds": list(SEEDS),
            "preactivity_certificate_sha256": _sha256(certificate_path),
            "fresh_result_root": True,
            "seed_replacement_allowed": False,
            "required_arm_count": 4,
            "all_or_nothing_inference_seed_count": 16,
        }))
        _write_bytes(temporary / "LEASE_BINDING.json", _json_bytes(lease_binding))
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def validate_result_root(path: Path) -> dict[str, object]:
    manifest = json.loads((path / "MANIFEST.json").read_text(encoding="utf-8"))
    if (
        manifest.get("direction") != DIRECTION
        or manifest.get("revision") != REVISION
        or manifest.get("schema") != SCHEMA
    ):
        raise RuntimeError("result root revision/schema mismatch")
    if manifest.get("registered_seeds") != list(SEEDS):
        raise RuntimeError("result root seed registry mismatch")
    if manifest.get("registered_config") != REGISTERED.manifest():
        raise RuntimeError("result root registered configuration mismatch")
    if (
        manifest.get("seed_replacement_allowed") is not False
        or manifest.get("required_arm_count") != len(ARMS)
        or manifest.get("all_or_nothing_inference_seed_count") != len(SEEDS)
    ):
        raise RuntimeError("result root lifecycle contract mismatch")
    return manifest


def validate_certificate_binding(root: Path, certificate_path: Path) -> None:
    manifest = validate_result_root(root)
    require_exact_certificate(certificate_path)
    if manifest.get("preactivity_certificate_sha256") != _sha256(certificate_path):
        raise RuntimeError("result root is not bound to this exact certificate")


def validate_lease_binding(root: Path, authorization: dict[str, object]) -> None:
    """Keep retries inside the first lease's continuous cumulative time envelope."""
    binding = json.loads((root / "LEASE_BINDING.json").read_text(encoding="utf-8"))
    if binding.get("stage_boundary") != authorization.get("stage_boundary"):
        raise PermissionError("continuation lease changed the frozen stage boundary")
    first_issued = parse_lease_timestamp(
        binding["issued_at_utc"], issued_boundary=True,
    )
    current_issued = parse_lease_timestamp(
        authorization["issued_at_utc"], issued_boundary=True,
    )
    current_expiry = parse_lease_timestamp(
        authorization["not_after_utc"], issued_boundary=False,
    )
    cap_hours = float(binding["cumulative_wall_clock_cap_hours"])
    deadline = first_issued + timedelta(hours=cap_hours)
    if current_issued < first_issued or current_expiry > deadline:
        raise PermissionError("continuation lease exceeds the original cumulative wall-clock window")
    if float(authorization["cumulative_wall_clock_cap_hours"]) > cap_hours:
        raise PermissionError("continuation lease expands the original cumulative wall-clock cap")


def write_atomic_seed_packet(
    root: Path, seed: int, models: dict[str, SharedSGSPPolicy], packet: dict[str, object],
) -> Path:
    validate_result_root(root)
    if seed not in SEEDS or set(models) != set(ARMS):
        raise ValueError("atomic packet requires one registered seed and all four arms")
    destination = root / f"seed-{seed}"
    if destination.exists():
        raise FileExistsError(f"registered seed may not be replaced: {seed}")
    temporary = root / f".seed-{seed}.{uuid.uuid4().hex}.tmp"
    temporary.mkdir(exist_ok=False)
    try:
        checkpoint_path = temporary / "checkpoint-update-240.pt"
        torch.save({arm: model.state_dict() for arm, model in models.items()}, checkpoint_path)
        packet_path = temporary / "packet.json"
        _write_bytes(packet_path, _json_bytes(packet))
        complete = {
            "seed": seed,
            "revision": REVISION,
            "schema": SCHEMA,
            "arms": list(ARMS),
            "checkpoint_sha256": _sha256(checkpoint_path),
            "packet_sha256": _sha256(packet_path),
            "atomic_complete": True,
        }
        _write_bytes(temporary / "COMPLETE.json", _json_bytes(complete))
        os.replace(temporary, destination)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return destination


def load_complete_seed_packet(root: Path, seed: int) -> dict[str, object]:
    directory = root / f"seed-{seed}"
    complete_path = directory / "COMPLETE.json"
    packet_path = directory / "packet.json"
    checkpoint_path = directory / "checkpoint-update-240.pt"
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    if (
        complete.get("atomic_complete") is not True
        or complete.get("seed") != seed
        or complete.get("revision") != REVISION
        or complete.get("schema") != SCHEMA
        or complete.get("arms") != list(ARMS)
    ):
        raise RuntimeError(f"seed {seed} is not atomically complete")
    if complete.get("packet_sha256") != _sha256(packet_path):
        raise RuntimeError(f"seed {seed} packet digest mismatch")
    if complete.get("checkpoint_sha256") != _sha256(checkpoint_path):
        raise RuntimeError(f"seed {seed} checkpoint digest mismatch")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (
        packet.get("revision") != REVISION
        or packet.get("seed") != seed
        or packet.get("arms") != list(ARMS)
        or packet.get("atomic_payload_complete") is not True
    ):
        raise RuntimeError(f"seed {seed} packet metadata mismatch")
    return packet
