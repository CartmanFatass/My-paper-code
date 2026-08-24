"""Atomic blinded lifecycle contracts for DISH RBHR r05 production construction."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping

from .production_contract import ARMS, BLOCKS, PREACTIVITY_NAMESPACE, SOLE_EVALUATION_CHECKPOINT, UPDATES, complete_inventory


class ProductionLifecycleError(RuntimeError):
    pass


BINDING_COMPONENTS = (
    "science_composite", "production_source", "native_artifact", "model", "optimizer",
    "actor_welford", "snapshot_welford", "critic_welford", "rng_frontier",
    "accepted_tape_frontier", "fork_frontier", "reducer_frontier", "analyzer_frontier",
)


def canonical_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def atomic_create(path: Path, payload: Mapping[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_bytes(payload)
    handle, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(handle, "wb", closefd=True) as stream:
            stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise ProductionLifecycleError("lifecycle generations are create-only") from error
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(encoded).hexdigest()


def atomic_create_bytes(path: Path, payload: bytes) -> str:
    """Create one immutable binary component without replace-on-collision."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(handle, "wb", closefd=True) as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise ProductionLifecycleError("component generations are create-only") from error
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(payload).hexdigest()


def read_canonical(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ProductionLifecycleError("lifecycle generation is not canonical JSON") from error
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise ProductionLifecycleError("lifecycle generation bytes differ")
    return value


def append_generation(
    root: Path,
    *,
    job_id: str,
    generation: int,
    parent_sha256: str | None,
    components: Mapping[str, str],
) -> dict[str, object]:
    """Create one immutable, parent-linked frontier generation.

    Generation zero has no parent.  Every later generation must name the
    canonical SHA-256 of the immediately preceding generation.  Component
    values are opaque identity digests; this layer cannot inspect results.
    """

    if not job_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in job_id):
        raise ProductionLifecycleError("job id is outside the filesystem-safe contract")
    if generation < 0:
        raise ProductionLifecycleError("generation must be nonnegative")
    if tuple(sorted(components)) != tuple(sorted(BINDING_COMPONENTS)):
        raise ProductionLifecycleError("frontier component inventory differs")
    if any(len(value) != 64 or any(character not in "0123456789abcdef" for character in value) for value in components.values()):
        raise ProductionLifecycleError("frontier component identity is not a SHA-256 digest")
    job_root = root / job_id
    if generation == 0:
        if parent_sha256 is not None:
            raise ProductionLifecycleError("generation zero cannot have a parent")
    else:
        previous = job_root / f"generation-{generation - 1:04d}.json"
        if not previous.is_file():
            raise ProductionLifecycleError("previous frontier generation is absent")
        observed_parent = hashlib.sha256(previous.read_bytes()).hexdigest()
        if parent_sha256 != observed_parent:
            raise ProductionLifecycleError("frontier parent compare-and-swap failed")
    payload = {
        "schema": "DISH_RBHR_R05_ATOMIC_FRONTIER_GENERATION_V1",
        "namespace": PREACTIVITY_NAMESPACE,
        "test_only": True,
        "question_relevant_output": False,
        "job_id": job_id,
        "generation": generation,
        "parent_sha256": parent_sha256,
        "components": dict(components),
    }
    path = job_root / f"generation-{generation:04d}.json"
    digest = atomic_create(path, payload)
    return {"path": str(path), "sha256": digest, "bytes": path.stat().st_size, "payload": payload}


@dataclass(frozen=True)
class BlindedFrontierPlan:
    checkpoint_stride_updates: int = 16
    updates: int = UPDATES
    evaluation_checkpoint: int = SOLE_EVALUATION_CHECKPOINT
    partial_interpretation_permitted: bool = False

    def validate(self) -> None:
        if self.checkpoint_stride_updates <= 0 or self.updates % self.checkpoint_stride_updates:
            raise ProductionLifecycleError("checkpoint stride does not divide 1024 updates")
        if self.evaluation_checkpoint != self.updates or self.evaluation_checkpoint != 1_024:
            raise ProductionLifecycleError("only update 1024 may be evaluated")
        if self.partial_interpretation_permitted:
            raise ProductionLifecycleError("frontier cannot permit partial interpretation")

    @property
    def resume_generations_per_job(self) -> int:
        self.validate()
        return self.updates // self.checkpoint_stride_updates

    def payload(self) -> dict[str, object]:
        self.validate()
        return {
            "schema": "DISH_RBHR_R05_BLINDED_FRONTIER_PLAN_V1",
            "checkpoint_stride_updates": self.checkpoint_stride_updates,
            "updates": self.updates,
            "resume_generations_per_job": self.resume_generations_per_job,
            "evaluation_checkpoint": self.evaluation_checkpoint,
            "partial_interpretation_permitted": False,
            "atomic_scope": "one-arm-block-generation",
        }


@dataclass(frozen=True)
class CompletePanelLifecycleState:
    phase: str
    updates_completed: tuple[int, ...]
    final_checkpoints_accepted: int
    evaluation_episodes_completed: int
    fork_pairs_completed: int
    analyzer_resamples_completed: int
    result_exposed: bool = False

    @classmethod
    def preactivity(cls) -> "CompletePanelLifecycleState":
        return cls("PREACTIVITY", (0,) * (BLOCKS * len(ARMS)), 0, 0, 0, 0, False)

    def validate(self) -> None:
        inventory = complete_inventory()
        if self.phase not in ("PREACTIVITY", "TRAINING", "CHECKPOINT_BARRIER", "EVALUATION", "ANALYSIS", "COMPLETE"):
            raise ProductionLifecycleError("panel lifecycle phase differs")
        if len(self.updates_completed) != BLOCKS * len(ARMS) or any(not 0 <= value <= UPDATES for value in self.updates_completed):
            raise ProductionLifecycleError("training job frontier differs")
        if not 0 <= self.final_checkpoints_accepted <= BLOCKS * len(ARMS):
            raise ProductionLifecycleError("checkpoint barrier count differs")
        if not 0 <= self.evaluation_episodes_completed <= int(inventory["evaluation_episodes"]):
            raise ProductionLifecycleError("evaluation frontier differs")
        if not 0 <= self.fork_pairs_completed <= int(inventory["fork_pairs_max"]):
            raise ProductionLifecycleError("fork frontier differs")
        if not 0 <= self.analyzer_resamples_completed <= int(inventory["bootstrap_resamples"]):
            raise ProductionLifecycleError("analyzer frontier differs")
        if self.phase in ("EVALUATION", "ANALYSIS", "COMPLETE") and (
            any(value != UPDATES for value in self.updates_completed)
            or self.final_checkpoints_accepted != BLOCKS * len(ARMS)
        ):
            raise ProductionLifecycleError("evaluation crossed an incomplete global checkpoint barrier")
        if self.phase == "COMPLETE" and (
            self.evaluation_episodes_completed != int(inventory["evaluation_episodes"])
            or self.analyzer_resamples_completed != int(inventory["bootstrap_resamples"])
        ):
            raise ProductionLifecycleError("complete lifecycle lacks the indivisible panel")
        if self.result_exposed:
            raise ProductionLifecycleError("CM lifecycle state may not expose a result")

    def payload(self) -> dict[str, object]:
        self.validate()
        return {
            "schema": "DISH_RBHR_R05_COMPLETE_PANEL_LIFECYCLE_STATE_V1",
            "phase": self.phase,
            "updates_completed": list(self.updates_completed),
            "final_checkpoints_accepted": self.final_checkpoints_accepted,
            "evaluation_episodes_completed": self.evaluation_episodes_completed,
            "fork_pairs_completed": self.fork_pairs_completed,
            "analyzer_resamples_completed": self.analyzer_resamples_completed,
            "result_exposed": False,
            "partial_interpretation_permitted": False,
        }


def run_result_blind_lifecycle_seam(root: Path, checkpoint_bytes: int) -> dict[str, object]:
    plan = BlindedFrontierPlan(); payload = {
        "schema": "DISH_RBHR_R05_PRODUCTION_PREACTIVITY_LIFECYCLE_V1",
        "namespace": PREACTIVITY_NAMESPACE,
        "test_only": True,
        "scientific_master": False,
        "coordinate": False,
        "lease": False,
        "model_or_checkpoint": False,
        "question_relevant_output": False,
        "frontier": plan.payload(),
        "complete_panel_state": CompletePanelLifecycleState.preactivity().payload(),
        "checkpoint_resume_projected_bytes_per_job": checkpoint_bytes,
    }
    path = root / "preactivity-generation-0001.json"
    digest = atomic_create(path, payload)
    if read_canonical(path) != payload:
        raise ProductionLifecycleError("lifecycle round trip differs")
    duplicate_rejected = False
    try:
        atomic_create(path, payload)
    except ProductionLifecycleError:
        duplicate_rejected = True
    if not duplicate_rejected:
        raise ProductionLifecycleError("duplicate generation was not rejected")
    opaque_components = {
        name: hashlib.sha256((PREACTIVITY_NAMESPACE + "/" + name).encode("ascii")).hexdigest()
        for name in BINDING_COMPONENTS
    }
    generation_zero = append_generation(
        root / "atomic-jobs", job_id="TEST-BLOCK00-STRUCTURED", generation=0,
        parent_sha256=None, components=opaque_components,
    )
    next_components = dict(opaque_components)
    next_components["optimizer"] = hashlib.sha256((PREACTIVITY_NAMESPACE + "/optimizer/1").encode("ascii")).hexdigest()
    generation_one = append_generation(
        root / "atomic-jobs", job_id="TEST-BLOCK00-STRUCTURED", generation=1,
        parent_sha256=str(generation_zero["sha256"]), components=next_components,
    )
    stale_parent_rejected = False
    try:
        append_generation(
            root / "atomic-jobs", job_id="TEST-BLOCK00-STRUCTURED", generation=2,
            parent_sha256=str(generation_zero["sha256"]), components=next_components,
        )
    except ProductionLifecycleError:
        stale_parent_rejected = True
    if not stale_parent_rejected:
        raise ProductionLifecycleError("stale frontier parent was not rejected")
    return {
        "schema": "DISH_RBHR_R05_PRODUCTION_LIFECYCLE_SEAM_V1",
        "test_only": True,
        "question_relevant_output": False,
        "path": str(path),
        "sha256": digest,
        "bytes": path.stat().st_size,
        "duplicate_rejected": True,
        "atomic_job_component_count": len(BINDING_COMPONENTS),
        "atomic_job_generation_zero_sha256": generation_zero["sha256"],
        "atomic_job_generation_one_sha256": generation_one["sha256"],
        "stale_parent_rejected": True,
        "resume_generations_per_job": plan.resume_generations_per_job,
    }


def run_real_byte_lifecycle_seam(
    root: Path,
    component_bytes: Mapping[str, bytes],
) -> dict[str, object]:
    """Install and resume all thirteen TEST component bytes atomically.

    Component contents remain opaque to the lifecycle.  The seam proves that
    exact bytes—not placeholder names—are create-only, digest-bound, parent-
    linked, reloadable, and reject stale-parent continuation.
    """

    if tuple(sorted(component_bytes)) != tuple(sorted(BINDING_COMPONENTS)):
        raise ProductionLifecycleError("real-byte component inventory differs")
    component_root = root / "components" / "generation-0000"
    identities: dict[str, str] = {}
    total_bytes = 0
    for name in BINDING_COMPONENTS:
        payload = bytes(component_bytes[name])
        if not payload:
            raise ProductionLifecycleError(f"component bytes are empty: {name}")
        path = component_root / f"{name}.bin"
        digest = atomic_create_bytes(path, payload)
        if path.read_bytes() != payload or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ProductionLifecycleError(f"component resume differs: {name}")
        identities[name] = digest
        total_bytes += len(payload)
    generation_zero = append_generation(
        root / "frontier", job_id="TEST-REAL-BYTE-CHAIN", generation=0,
        parent_sha256=None, components=identities,
    )
    generation_one = append_generation(
        root / "frontier", job_id="TEST-REAL-BYTE-CHAIN", generation=1,
        parent_sha256=str(generation_zero["sha256"]), components=identities,
    )
    stale_parent_rejected = False
    try:
        append_generation(
            root / "frontier", job_id="TEST-REAL-BYTE-CHAIN", generation=2,
            parent_sha256=str(generation_zero["sha256"]), components=identities,
        )
    except ProductionLifecycleError:
        stale_parent_rejected = True
    if not stale_parent_rejected:
        raise ProductionLifecycleError("real-byte stale parent was not rejected")
    return {
        "schema": "DISH_RBHR_R05_REAL_BYTE_LIFECYCLE_SEAM_V1",
        "test_only": True, "question_relevant_output": False,
        "component_count": len(identities), "component_bytes": total_bytes,
        "component_sha256": identities, "all_components_resume_equal": True,
        "create_only": True, "stale_parent_rejected": True,
        "generation_zero_sha256": generation_zero["sha256"],
        "generation_one_sha256": generation_one["sha256"],
    }


__all__ = [
    "BINDING_COMPONENTS", "BlindedFrontierPlan", "CompletePanelLifecycleState",
    "ProductionLifecycleError", "append_generation", "atomic_create_bytes",
    "run_real_byte_lifecycle_seam", "run_result_blind_lifecycle_seam",
]
