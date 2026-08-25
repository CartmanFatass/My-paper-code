from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

import torch

from .authorization import ProductionPermit, require_active_permit
from .config import ARMS, DIRECTION, REGISTERED, REVISION, SCHEMA, SEEDS
from .training import TrainingResult


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _write_exclusive(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _replace_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _write_exclusive(temporary, _json_bytes(value))
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_certificate(path: Path) -> dict[str, object]:
    certificate = json.loads(path.read_text(encoding="utf-8"))
    if (certificate.get("revision") != REVISION or certificate.get("passed") is not True
            or certificate.get("registered_stochastic_object_materialized") is not False):
        raise RuntimeError("passing exact CPC-r04 preactivity certificate is required")
    expected = certificate.get("source_sha256")
    current = {
        source.name: hashlib.sha256(source.read_bytes()).hexdigest()
        for source in sorted(Path(__file__).parent.glob("*.py"))
    }
    if expected != current:
        raise RuntimeError("current CPC source differs from the certified exact revision")
    return certificate


def _require_lifecycle_binding(
    permit: ProductionPermit,
    root: Path,
    certificate_path: Path,
) -> dict[str, object]:
    require_active_permit(permit)
    if root.resolve() != permit.result_root.resolve():
        raise PermissionError("result root differs from the active production permit")
    if certificate_path.resolve() != permit.certificate_path.resolve():
        raise PermissionError("certificate path differs from the active production permit")
    certificate = require_certificate(certificate_path)
    if certificate != permit.certificate:
        raise PermissionError("certificate differs from the active production permit")
    return certificate


def create_result_root(
    permit: ProductionPermit,
    root: Path,
    certificate_path: Path,
    stage_boundary: str,
) -> None:
    _require_lifecycle_binding(permit, root, certificate_path)
    if stage_boundary != permit.payload["stage_boundary"]:
        raise PermissionError("stage boundary differs from the active production permit")
    if root.exists():
        raise FileExistsError(f"result root must be fresh: {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    temporary = root.parent / f".{root.name}.{uuid.uuid4().hex}.tmp"
    temporary.mkdir(exist_ok=False)
    try:
        _write_exclusive(temporary / "MANIFEST.json", _json_bytes({
            "direction": DIRECTION,
            "revision": REVISION,
            "schema": SCHEMA,
            "registered_config": REGISTERED.manifest(),
            "registered_seeds": list(SEEDS),
            "required_arms": list(ARMS),
            "certificate_sha256": _sha256(certificate_path),
            "stage_boundary": stage_boundary,
            "seed_replacement_allowed": False,
            "partial_result_interpretation_allowed": False,
        }))
        _write_exclusive(temporary / "RUNTIME.json", _json_bytes({
            "cumulative_active_seconds": 0.0,
            "peak_rss_bytes": 0,
            "lease_planning_wall_seconds": REGISTERED.max_wall_minutes * 60,
        }))
        _require_lifecycle_binding(permit, root, certificate_path)
        os.replace(temporary, root)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def validate_root(
    permit: ProductionPermit,
    root: Path,
    certificate_path: Path,
    stage_boundary: str,
) -> dict[str, object]:
    _require_lifecycle_binding(permit, root, certificate_path)
    if stage_boundary != permit.payload["stage_boundary"]:
        raise PermissionError("stage boundary differs from the active production permit")
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    expected = {
        "direction": DIRECTION, "revision": REVISION, "schema": SCHEMA,
        "registered_config": REGISTERED.manifest(), "registered_seeds": list(SEEDS),
        "required_arms": list(ARMS), "certificate_sha256": _sha256(certificate_path),
        "stage_boundary": stage_boundary, "seed_replacement_allowed": False,
        "partial_result_interpretation_allowed": False,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise RuntimeError("result root exact-revision lifecycle mismatch")
    return manifest


def runtime_state(permit: ProductionPermit, root: Path, certificate_path: Path) -> dict[str, object]:
    _require_lifecycle_binding(permit, root, certificate_path)
    return json.loads((root / "RUNTIME.json").read_text(encoding="utf-8"))


def update_runtime(
    permit: ProductionPermit,
    root: Path,
    certificate_path: Path,
    elapsed_seconds: float,
    peak_rss_bytes: int,
) -> None:
    current = runtime_state(permit, root, certificate_path)
    current["cumulative_active_seconds"] = float(current["cumulative_active_seconds"]) + elapsed_seconds
    current["peak_rss_bytes"] = max(int(current["peak_rss_bytes"]), int(peak_rss_bytes))
    _replace_json(root / "RUNTIME.json", current)


def write_atomic_seed_packet(
    permit: ProductionPermit,
    root: Path,
    certificate_path: Path,
    training: TrainingResult,
    packet: dict[str, object],
) -> Path:
    _require_lifecycle_binding(permit, root, certificate_path)
    seed = training.seed
    permit.require_seed(seed)
    if seed not in SEEDS or set(training.models) != set(ARMS):
        raise ValueError("one registered seed and all three frozen arms are required")
    if packet.get("seed") != seed:
        raise ValueError("training and packet seed must match")
    if training.metadata != packet.get("training"):
        raise ValueError("training metadata and packet training record must match")
    if packet.get("certificate_sha256") != _sha256(certificate_path):
        raise ValueError("packet certificate binding mismatch")
    if packet.get("stage_boundary") != permit.payload["stage_boundary"]:
        raise ValueError("packet stage-boundary binding mismatch")
    from .inference import packet_is_semantically_complete
    if not packet_is_semantically_complete(packet):
        raise ValueError("semantically complete exact-revision seed packet is required")
    destination = root / f"seed-{seed}"
    if destination.exists():
        raise FileExistsError(f"registered seed may not be replaced: {seed}")
    temporary = root / f".seed-{seed}.{uuid.uuid4().hex}.tmp"
    temporary.mkdir(exist_ok=False)
    try:
        _require_lifecycle_binding(permit, root, certificate_path)
        checkpoint = temporary / "checkpoint-update-1000.pt"
        torch.save({
            "models": {arm: training.models[arm].state_dict() for arm in ARMS},
            "baselines": training.baselines,
        }, checkpoint)
        packet_path = temporary / "packet.json"
        _write_exclusive(packet_path, _json_bytes(packet))
        _write_exclusive(temporary / "COMPLETE.json", _json_bytes({
            "seed": seed, "revision": REVISION, "schema": SCHEMA, "arms": list(ARMS),
            "checkpoint_sha256": _sha256(checkpoint), "packet_sha256": _sha256(packet_path),
            "atomic_complete": True,
        }))
        _require_lifecycle_binding(permit, root, certificate_path)
        os.replace(temporary, destination)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return destination


def load_seed_packet(
    permit: ProductionPermit,
    root: Path,
    certificate_path: Path,
    seed: int,
):
    _require_lifecycle_binding(permit, root, certificate_path)
    permit.require_seed(seed)
    directory = root / f"seed-{seed}"
    complete = json.loads((directory / "COMPLETE.json").read_text(encoding="utf-8"))
    packet_path, checkpoint = directory / "packet.json", directory / "checkpoint-update-1000.pt"
    if (complete.get("seed") != seed or complete.get("revision") != REVISION
            or complete.get("schema") != SCHEMA or complete.get("arms") != list(ARMS)
            or complete.get("atomic_complete") is not True
            or complete.get("packet_sha256") != _sha256(packet_path)
            or complete.get("checkpoint_sha256") != _sha256(checkpoint)):
        raise RuntimeError(f"seed {seed} is not atomically complete")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (packet.get("revision") != REVISION or packet.get("seed") != seed
            or packet.get("arms") != list(ARMS) or packet.get("atomic_payload_complete") is not True):
        raise RuntimeError(f"seed {seed} packet metadata mismatch")
    from .inference import packet_is_semantically_complete
    if not packet_is_semantically_complete(packet):
        raise RuntimeError(f"seed {seed} packet is semantically incomplete")
    if packet.get("certificate_sha256") != _sha256(certificate_path):
        raise RuntimeError(f"seed {seed} packet certificate binding mismatch")
    if packet.get("stage_boundary") != permit.payload["stage_boundary"]:
        raise RuntimeError(f"seed {seed} packet stage-boundary binding mismatch")
    _require_lifecycle_binding(permit, root, certificate_path)
    from .inference import _verified_seed_packet
    return _verified_seed_packet(packet)


def write_analysis(
    permit: ProductionPermit,
    root: Path,
    certificate_path: Path,
    path: Path,
    value: object,
) -> None:
    _require_lifecycle_binding(permit, root, certificate_path)
    from .inference import VerifiedAnalysis
    if not isinstance(value, VerifiedAnalysis):
        raise PermissionError("analysis installation requires a protected-analyzer result")
    payload = value.payload
    if payload.get("valid_complete") is not True or payload.get("completeness_ok") is not True:
        raise ValueError("only a complete exact-panel analysis may be installed")
    if path.resolve() != (root / "analysis.json").resolve():
        raise PermissionError("analysis must be installed at the protected result-root analysis.json")
    if path.exists():
        raise FileExistsError(f"analysis output must be fresh: {path}")
    _require_lifecycle_binding(permit, root, certificate_path)
    _replace_json(path, payload)
