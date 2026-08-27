"""One complete registered R03 transaction behind the immutable launch gate."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

import torch

from . import native_backend
from .contract import Panel, TRAINING_BATCHES
from .model import make_paired_bundles
from .production_checkpoint import (
    FrontierIdentity,
    final_checkpoint_bytes,
    save_frontier_atomic,
    write_final_checkpoint_atomic,
)
from .production_contract import OUTPUT_ROOT, RUN_ID, checkpoint_slots
from .production_learner import LearningBoundary, prepare_production_batch, support_for_arm
from .production_manifest import complete_checkpoint_manifest, write_canonical_json_atomic
from .production_result import evaluate_publish_complete
from .training import ReductionFrontier, SupportCounters, apply_training_batch


class ProductionExecutionRefusal(PermissionError):
    pass


@dataclass(frozen=True)
class RuntimePaths:
    repository_root: Path
    output_root: Path
    checkpoints: Path
    artifacts: Path
    metrics: Path

    @classmethod
    def from_repository(cls, repository_root: Path) -> "RuntimePaths":
        root = Path(repository_root).resolve(strict=True)
        output = (root / Path(*OUTPUT_ROOT.split("/"))).resolve(strict=True)
        return cls(root, output, output / "checkpoints", output / "artifacts", output / "metrics")

    def require_fresh_prepared_outputs(self) -> None:
        for path in (self.checkpoints, self.artifacts, self.metrics):
            if not path.is_dir() or path.is_symlink() or any(path.iterdir()):
                raise ProductionExecutionRefusal("prepared output directory is not empty/create-only")
        for name in ("checkpoint-manifest.json",):
            if (self.output_root / name).exists():
                raise ProductionExecutionRefusal("transaction evidence already exists; rerun is forbidden")


def _require_launch(launch: Mapping[str, object], paths: RuntimePaths) -> tuple[str, str]:
    if set(launch) != {
        "run_id", "output_root", "code_sha", "validated", "complete_only", "rerun_permitted"
    }:
        raise ProductionExecutionRefusal("validated launch fields differ")
    run_id = launch.get("run_id")
    code_sha = launch.get("code_sha")
    if (
        launch.get("validated") is not True
        or launch.get("complete_only") is not True
        or launch.get("rerun_permitted") is not False
        or launch.get("output_root") != OUTPUT_ROOT
        or run_id != RUN_ID
        or not isinstance(run_id, str)
        or not isinstance(code_sha, str)
        or len(code_sha) != 40
    ):
        raise ProductionExecutionRefusal("launch is not the immutable complete-only release")
    try:
        bytes.fromhex(code_sha)
    except ValueError as exc:
        raise ProductionExecutionRefusal("launch code SHA differs") from exc
    manifest = paths.output_root / "manifest.json"
    if not manifest.is_file():
        raise ProductionExecutionRefusal("hmasd_run manifest is absent")
    return run_id, code_sha


def execute_registered_transaction(
    launch: Mapping[str, object], *, repository_root: Path
) -> Mapping[str, object]:
    """Execute once; only the final sealed package/evidence exposes completion."""

    paths = RuntimePaths.from_repository(repository_root)
    run_id, code_sha = _require_launch(launch, paths)
    paths.require_fresh_prepared_outputs()
    boundary = LearningBoundary.registered_runtime()
    torch.set_num_threads(1)
    native_identity = native_backend.native_artifact_identity()
    frontier_root = paths.checkpoints / ".frontiers"
    frontier_root.mkdir()
    produced: dict[tuple[str, str, int], dict[str, object]] = {}
    final_paths: dict[tuple[str, str, int], Path] = {}
    try:
        for master_seed in boundary.seeds:
            for panel in Panel:
                panel_value = int(panel)
                bundles = make_paired_bundles(seed=master_seed, panel=panel_value)
                support = SupportCounters.empty()
                frontier_path = frontier_root / f"{panel.name.lower()}-{master_seed}.pt"
                latest_reduction: ReductionFrontier | None = None
                latest_counter = ""
                identity = FrontierIdentity(
                    run_id=run_id,
                    code_sha=code_sha,
                    master_seed=master_seed,
                    panel=panel_value,
                    namespace=boundary.namespace,
                    registered=True,
                )
                for batch_index in range(TRAINING_BATCHES):
                    prepared = prepare_production_batch(
                        bundles,
                        boundary=boundary,
                        master_seed=master_seed,
                        panel=panel_value,
                        batch_index=batch_index,
                    )
                    apply_training_batch(
                        bundles, support, prepared, batch_number=batch_index + 1
                    )
                    latest_reduction = prepared["reduction_frontier"]  # type: ignore[assignment]
                    latest_counter = str(prepared["counter_frontier"])
                    if not isinstance(latest_reduction, ReductionFrontier):
                        raise ProductionExecutionRefusal("training reduction frontier is malformed")
                    save_frontier_atomic(
                        frontier_path,
                        bundles,
                        support,
                        latest_reduction,
                        identity=identity,
                        boundary=boundary,
                        completed_batch=batch_index + 1,
                        counter_frontier=latest_counter,
                        native_source_sha256=str(native_identity["source_sha256"]),
                        native_artifact_sha256=str(native_identity["artifact_sha256"]),
                    )
                if latest_reduction is None:
                    raise ProductionExecutionRefusal("training produced no final frontier")
                for arm, bundle in enumerate(bundles):
                    arm_name = ("COUNT", "RAW", "BELIEF_FEATURE")[arm]
                    key = (arm_name, panel.name, master_seed)
                    relative = next(
                        row["path"]
                        for row in checkpoint_slots()
                        if (row["arm"], row["panel"], row["master_seed"]) == key
                    )
                    path = paths.output_root / Path(*str(relative).split("/"))
                    payload = final_checkpoint_bytes(
                        bundle,
                        arm=arm,
                        panel=panel_value,
                        master_seed=master_seed,
                        support=support_for_arm(support, arm=arm, panel=panel_value),
                        boundary=boundary,
                    )
                    checkpoint_sha = write_final_checkpoint_atomic(path, payload)
                    decoded = json.loads(payload)
                    produced[key] = {
                        "arm": arm_name,
                        "panel": panel.name,
                        "master_seed": master_seed,
                        "batch": TRAINING_BATCHES,
                        "path": str(relative),
                        "sha256": checkpoint_sha,
                        "model_sha256": decoded["model_sha256"],
                    }
                    final_paths[key] = path
                frontier_path.unlink()
        frontier_root.rmdir()
        ordered_rows = [
            produced[(str(row["arm"]), str(row["panel"]), int(row["master_seed"]))]
            for row in checkpoint_slots()
        ]
        checkpoint_manifest = complete_checkpoint_manifest(ordered_rows)
        checkpoint_manifest_path = paths.output_root / "checkpoint-manifest.json"
        checkpoint_ref = write_canonical_json_atomic(
            checkpoint_manifest_path, checkpoint_manifest
        )
        ordered_paths = [
            final_paths[(str(row["arm"]), str(row["panel"]), int(row["master_seed"]))]
            for row in checkpoint_slots()
        ]
        return evaluate_publish_complete(
            ordered_paths,
            checkpoint_root=paths.checkpoints,
            output_root=paths.output_root,
            destination=paths.artifacts / "complete-r03.sealed",
            evidence_path=paths.metrics / "complete-evidence.json",
            checkpoint_manifest_sha256=checkpoint_ref["sha256"],
            run_id=run_id,
            code_sha=code_sha,
        )
    except Exception:
        # No retry/replay is authorized. Preserve fail-closed residue for terminal observation.
        raise
