"""Atomic production frontier and final S2 checkpoint envelopes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

import torch

from .contract import COUNTER_LAYOUT_ID, OBJECT_REVISION, TRAINING_BATCHES
from .model import LearnerBundle, make_paired_bundles
from .production_learner import LearningBoundary
from .s2_construction import (
    FINAL_CHECKPOINT_SCHEMA,
    OBJECT_DIGEST,
    build_action_scorer_payload,
    validate_support_structure,
)
from .training import ReductionFrontier, SupportCounters


FRONTIER_SCHEMA = "UCOPE_R01_R03_PRODUCTION_FRONTIER_V1"


class ProductionCheckpointRefusal(ValueError):
    pass


def _require_digest(value: str, label: str) -> None:
    if len(value) != 64:
        raise ProductionCheckpointRefusal(f"{label} must be SHA-256")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise ProductionCheckpointRefusal(f"{label} must be SHA-256") from exc


@dataclass(frozen=True)
class FrontierIdentity:
    run_id: str
    code_sha: str
    master_seed: int
    panel: int
    namespace: str
    registered: bool

    def validate(self, boundary: LearningBoundary) -> None:
        boundary.require(self.master_seed)
        if (
            self.namespace != boundary.namespace
            or self.registered is not boundary.registered
            or self.panel not in (0, 1, 2)
            or len(self.code_sha) != 40
        ):
            raise ProductionCheckpointRefusal("frontier identity differs")
        try:
            bytes.fromhex(self.code_sha)
        except ValueError as exc:
            raise ProductionCheckpointRefusal("frontier code SHA differs") from exc


def _bundle_state(bundle: LearnerBundle) -> dict[str, object]:
    return {
        "scorer": bundle.scorer.state_dict(),
        "baseline": bundle.baseline.state_dict(),
        "optimizer": bundle.optimizer.state_dict(),
    }


def _atomic_torch(path: Path, payload: Mapping[str, object]) -> str:
    target = Path(path)
    if not target.parent.is_dir() or target.exists() and target.is_symlink():
        raise ProductionCheckpointRefusal("frontier path is not a real prepared directory")
    temporary = target.with_name(f".{target.name}.{os.getpid()}.pending")
    try:
        with temporary.open("xb") as stream:
            torch.save(dict(payload), stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def save_frontier_atomic(
    path: Path,
    bundles: Sequence[LearnerBundle],
    support: SupportCounters,
    reduction: ReductionFrontier,
    *,
    identity: FrontierIdentity,
    boundary: LearningBoundary,
    completed_batch: int,
    counter_frontier: str,
    native_source_sha256: str,
    native_artifact_sha256: str,
) -> str:
    identity.validate(boundary)
    support.validate()
    _require_digest(counter_frontier, "counter frontier")
    _require_digest(native_source_sha256, "native source")
    _require_digest(native_artifact_sha256, "native artifact")
    if len(bundles) != 3 or not 1 <= completed_batch <= TRAINING_BATCHES:
        raise ProductionCheckpointRefusal("frontier batch/bundle closure differs")
    payload = {
        "schema": FRONTIER_SCHEMA,
        "object_revision": OBJECT_REVISION,
        "object_digest": OBJECT_DIGEST,
        "run_id": identity.run_id,
        "code_sha": identity.code_sha,
        "master_seed": identity.master_seed,
        "panel": identity.panel,
        "namespace": identity.namespace,
        "registered": identity.registered,
        "completed_batch": completed_batch,
        "next_batch": completed_batch + 1,
        "counter_layout_id": COUNTER_LAYOUT_ID,
        "counter_frontier": counter_frontier,
        "native_source_sha256": native_source_sha256,
        "native_artifact_sha256": native_artifact_sha256,
        "reduction": reduction.as_dict(),
        "support": support.as_dict(),
        "bundles": [_bundle_state(bundle) for bundle in bundles],
        "question_relevant_output": False,
        "complete_r03_package": False,
    }
    return _atomic_torch(path, payload)


def load_frontier_cold(
    path: Path,
    *,
    identity: FrontierIdentity,
    boundary: LearningBoundary,
) -> tuple[list[LearnerBundle], SupportCounters, ReductionFrontier, dict[str, object]]:
    identity.validate(boundary)
    target = Path(path).resolve(strict=True)
    with target.open("rb") as stream:
        payload = torch.load(stream, map_location="cpu", weights_only=False)
    required_identity = {
        "schema": FRONTIER_SCHEMA,
        "object_revision": OBJECT_REVISION,
        "object_digest": OBJECT_DIGEST,
        "run_id": identity.run_id,
        "code_sha": identity.code_sha,
        "master_seed": identity.master_seed,
        "panel": identity.panel,
        "namespace": identity.namespace,
        "registered": identity.registered,
        "counter_layout_id": COUNTER_LAYOUT_ID,
        "question_relevant_output": False,
        "complete_r03_package": False,
    }
    if not isinstance(payload, Mapping) or any(payload.get(k) != v for k, v in required_identity.items()):
        raise ProductionCheckpointRefusal("frontier identity/firewall differs")
    completed = payload.get("completed_batch")
    if type(completed) is not int or not 1 <= completed <= TRAINING_BATCHES or payload.get("next_batch") != completed + 1:
        raise ProductionCheckpointRefusal("frontier next-batch law differs")
    states = payload.get("bundles")
    if not isinstance(states, list) or len(states) != 3:
        raise ProductionCheckpointRefusal("frontier learned state is incomplete")
    bundles = make_paired_bundles(seed=identity.master_seed, panel=identity.panel)
    for bundle, state in zip(bundles, states, strict=True):
        bundle.scorer.load_state_dict(state["scorer"], strict=True)
        bundle.baseline.load_state_dict(state["baseline"], strict=True)
        bundle.optimizer.load_state_dict(state["optimizer"])
    support_payload = payload.get("support")
    reduction_payload = payload.get("reduction")
    if not isinstance(support_payload, Mapping) or not isinstance(reduction_payload, Mapping):
        raise ProductionCheckpointRefusal("frontier support/reduction is incomplete")
    support = SupportCounters.from_dict(support_payload)
    reduction = ReductionFrontier(
        count=int(reduction_payload["count"]),
        ordered_values_sha256=str(reduction_payload["ordered_values_sha256"]),
        total_fp32_bits=int(reduction_payload["total_fp32_bits"]),
    )
    metadata = {
        key: payload[key]
        for key in (
            "completed_batch", "next_batch", "counter_frontier",
            "native_source_sha256", "native_artifact_sha256",
        )
    }
    for name in ("counter_frontier", "native_source_sha256", "native_artifact_sha256"):
        _require_digest(str(metadata[name]), name)
    return bundles, support, reduction, metadata


def final_checkpoint_bytes(
    bundle: LearnerBundle,
    *,
    arm: int,
    panel: int,
    master_seed: int,
    support: Mapping[str, object],
    boundary: LearningBoundary,
) -> bytes:
    boundary.require(master_seed)
    if arm not in (0, 1, 2) or panel not in (0, 1, 2) or not validate_support_structure(support, panel):
        raise ProductionCheckpointRefusal("final checkpoint identity/support differs")
    model_payload = build_action_scorer_payload(
        bundle.scorer, arm=arm, panel=panel, master_seed=master_seed
    )
    value = {
        "schema": FINAL_CHECKPOINT_SCHEMA,
        "arm": arm,
        "panel": panel,
        "master_seed": master_seed,
        "batch": TRAINING_BATCHES,
        "object_revision": OBJECT_REVISION,
        "object_digest": OBJECT_DIGEST,
        "support": dict(support),
        "model_payload_hex": model_payload.hex(),
        "model_sha256": hashlib.sha256(model_payload).hexdigest(),
    }
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def write_final_checkpoint_atomic(path: Path, payload: bytes) -> str:
    target = Path(path)
    if not payload or not target.parent.is_dir() or target.exists():
        raise ProductionCheckpointRefusal("final checkpoint is not create-only")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", suffix=".pending", delete=False
        ) as stream:
            temporary = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    return hashlib.sha256(target.read_bytes()).hexdigest()
