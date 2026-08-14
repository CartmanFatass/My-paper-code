from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

import torch

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
    if (
        certificate.get("revision") != REVISION
        or certificate.get("passed") is not True
        or certificate.get("registered_stochastic_object_materialized") is not False
    ):
        raise RuntimeError("passing exact-B2-r02 preactivity certificate is required")
    expected_sources = certificate.get("source_sha256")
    if not isinstance(expected_sources, dict):
        raise RuntimeError("certificate lacks exact source bindings")
    current_sources = {
        source.name: hashlib.sha256(source.read_bytes()).hexdigest()
        for source in sorted(Path(__file__).parent.glob("*.py"))
    }
    if expected_sources != current_sources:
        raise RuntimeError("current RCLE source differs from the certified exact revision")
    return certificate


def create_result_root(
    root: Path,
    certificate_path: Path,
    stage_boundary: str,
) -> None:
    require_certificate(certificate_path)
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
            "registered_wall_seconds": REGISTERED.max_wall_minutes * 60,
        }))
        os.replace(temporary, root)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def validate_root(root: Path, certificate_path: Path, stage_boundary: str) -> dict[str, object]:
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    require_certificate(certificate_path)
    if (
        manifest.get("direction") != DIRECTION
        or manifest.get("revision") != REVISION
        or manifest.get("schema") != SCHEMA
        or manifest.get("registered_config") != REGISTERED.manifest()
        or manifest.get("registered_seeds") != list(SEEDS)
        or manifest.get("required_arms") != list(ARMS)
        or manifest.get("certificate_sha256") != _sha256(certificate_path)
        or manifest.get("stage_boundary") != stage_boundary
        or manifest.get("seed_replacement_allowed") is not False
        or manifest.get("partial_result_interpretation_allowed") is not False
    ):
        raise RuntimeError("result root exact-revision lifecycle mismatch")
    return manifest


def runtime_state(root: Path) -> dict[str, object]:
    return json.loads((root / "RUNTIME.json").read_text(encoding="utf-8"))


def update_runtime(root: Path, elapsed_seconds: float, peak_rss_bytes: int) -> None:
    current = runtime_state(root)
    current["cumulative_active_seconds"] = float(current["cumulative_active_seconds"]) + elapsed_seconds
    current["peak_rss_bytes"] = max(int(current["peak_rss_bytes"]), int(peak_rss_bytes))
    _replace_json(root / "RUNTIME.json", current)


def write_atomic_seed_packet(
    root: Path,
    training: TrainingResult,
    packet: dict[str, object],
) -> Path:
    seed = training.seed
    if seed not in SEEDS or set(training.actors) != set(ARMS) or set(training.posteriors) != set(ARMS):
        raise ValueError("one registered seed and both frozen arms are required")
    destination = root / f"seed-{seed}"
    if destination.exists():
        raise FileExistsError(f"registered seed may not be replaced: {seed}")
    temporary = root / f".seed-{seed}.{uuid.uuid4().hex}.tmp"
    temporary.mkdir(exist_ok=False)
    try:
        checkpoint = temporary / "checkpoint-update-2000.pt"
        torch.save({
            "actors": {arm: training.actors[arm].state_dict() for arm in ARMS},
            "posteriors": {arm: training.posteriors[arm].state_dict() for arm in ARMS},
            "common_baselines": {arm: training.common_baselines[arm] for arm in training.common_baselines},
        }, checkpoint)
        packet_path = temporary / "packet.json"
        _write_exclusive(packet_path, _json_bytes(packet))
        _write_exclusive(temporary / "COMPLETE.json", _json_bytes({
            "seed": seed,
            "revision": REVISION,
            "schema": SCHEMA,
            "arms": list(ARMS),
            "checkpoint_sha256": _sha256(checkpoint),
            "packet_sha256": _sha256(packet_path),
            "atomic_complete": True,
        }))
        os.replace(temporary, destination)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return destination


def load_seed_packet(root: Path, seed: int) -> dict[str, object]:
    directory = root / f"seed-{seed}"
    complete = json.loads((directory / "COMPLETE.json").read_text(encoding="utf-8"))
    packet_path = directory / "packet.json"
    checkpoint_path = directory / "checkpoint-update-2000.pt"
    if (
        complete.get("seed") != seed
        or complete.get("revision") != REVISION
        or complete.get("schema") != SCHEMA
        or complete.get("arms") != list(ARMS)
        or complete.get("atomic_complete") is not True
        or complete.get("packet_sha256") != _sha256(packet_path)
        or complete.get("checkpoint_sha256") != _sha256(checkpoint_path)
    ):
        raise RuntimeError(f"seed {seed} is not atomically complete")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (
        packet.get("revision") != REVISION
        or packet.get("seed") != seed
        or packet.get("arms") != list(ARMS)
        or packet.get("atomic_payload_complete") is not True
    ):
        raise RuntimeError(f"seed {seed} packet metadata mismatch")
    return packet


def write_analysis(path: Path, value: object) -> None:
    if path.exists():
        raise FileExistsError(f"analysis output must be fresh: {path}")
    _replace_json(path, value)
