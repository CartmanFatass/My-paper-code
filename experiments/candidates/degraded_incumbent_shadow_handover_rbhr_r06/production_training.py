"""Fresh r06 binding to the scientifically retained policy/training bytes."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

import torch

from .production_training_engine import (
    ExactPolicyGraph,
    TrainingBoundaryError,
    arm_mask_inventory,
    run_full_4096_dry_update as _retained_full_update,
)
from .production_contract import TestAuthority


RETAINED_SOURCE = (
    Path(__file__).resolve().parents[0].with_name("degraded_incumbent_shadow_handover_rbhr_r05")
    / "production_training.py"
)


def retained_training_binding() -> dict[str, object]:
    source = RETAINED_SOURCE.read_bytes()
    return {
        "schema": "DISH_RBHR_R06_RETAINED_TRAINING_BINDING_V1",
        "r06_science_semantics": "R05_POLICY_PPO_OPTIMIZER_CHECKPOINT_RETAINED",
        "retained_source": RETAINED_SOURCE.as_posix(),
        "retained_source_sha256": hashlib.sha256(source).hexdigest(),
        "fresh_r06_model_or_checkpoint": False,
        "test_only": True,
    }


def run_full_4096_test_update(
    authority: TestAuthority,
    *,
    arm: str = "STRUCTURED",
    fragments: Mapping[str, torch.Tensor] | None = None,
    source_label: str = "R06_TEST_ONLY_NONSCIENTIFIC_FIXTURE",
) -> dict[str, object]:
    authority.require_test_only()
    result = _retained_full_update(arm=arm, fragments=fragments, source_label=source_label)
    result.pop("private_checkpoint_bytes", None)
    return {
        **result,
        "schema": "DISH_RBHR_R06_PRODUCTION_FULL_4096_TEST_UPDATE_V1",
        "r06_scientific_model": False,
        "r06_checkpoint_created": False,
        "r06_training_rollout": False,
        "retained_training_source_sha256": retained_training_binding()["retained_source_sha256"],
    }


class PersistentTrainer:
    """Private model/optimizer state carried through exactly 1,024 updates."""

    def __init__(self, *, arm: str, checkpoint_bytes: bytes | None = None,
                 forecast_package: bool = False, progress: dict | None = None,
                 deadline: float | None = None) -> None:
        self.arm = arm
        self.forecast_package = forecast_package
        self.progress = progress
        self.deadline = deadline
        self.checkpoint_bytes = checkpoint_bytes
        self.update = 0

    def run_update(self, fragments: Mapping[str, torch.Tensor], *, source_label: str) -> dict[str, object]:
        if self.update >= 1_024:
            raise TrainingBoundaryError("training job already reached sole checkpoint")
        result = _retained_full_update(
            arm=self.arm, fragments=fragments, source_label=source_label,
            resume_checkpoint_bytes=self.checkpoint_bytes,
            forecast_package=self.forecast_package, progress=self.progress, deadline=self.deadline,
        )
        self.checkpoint_bytes = bytes(result.pop("private_checkpoint_bytes"))
        self.update = int(result["update"])
        return result

    def sole_checkpoint(self) -> bytes:
        if self.update != 1_024 or self.checkpoint_bytes is None:
            raise TrainingBoundaryError("sole evaluation checkpoint is not complete")
        return self.checkpoint_bytes


def run_persistent_training_job(
    fragments_by_update: Mapping[int, Mapping[str, torch.Tensor]], *, arm: str,
) -> tuple[bytes, list[dict[str, object]]]:
    if set(fragments_by_update) != set(range(1, 1_025)):
        raise TrainingBoundaryError("persistent training update inventory differs")
    trainer = PersistentTrainer(arm=arm); receipts = []
    for update in range(1, 1_025):
        receipts.append(trainer.run_update(fragments_by_update[update], source_label=f"R06_PRODUCTION_UPDATE_{update}"))
    return trainer.sole_checkpoint(), receipts


__all__ = [
    "ExactPolicyGraph", "TrainingBoundaryError", "arm_mask_inventory",
    "PersistentTrainer", "retained_training_binding", "run_full_4096_test_update", "run_persistent_training_job",
]
