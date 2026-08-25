"""Complete TEST-only Gate-B synthetic seam for DISH RBHR r05."""

from __future__ import annotations

import hashlib
from pathlib import Path
import time

import numpy as np

from .analysis import joint_max_t, load_and_validate_branch_fixture
from .contracts import TEST_NAMESPACE
from .lifecycle import SyntheticResumeRecord, read_verified, write_once_atomic
from .model import run_synthetic_update


def _synthetic_evaluation() -> dict[str, object]:
    tape = np.arange(48, dtype=np.float64)[:, None, None]
    arm = np.arange(5, dtype=np.float64)[None, :, None]
    view = np.arange(2, dtype=np.float64)[None, None, :]
    # Fixed non-scientific values provide shape, pairing and reducer coverage.
    service = np.clip(0.55 + 0.08 * np.sin(tape * 0.17 + arm * 0.31 + view * 0.07), 0.0, 1.0)
    deficit = 20.0 * (1.0 - service)
    delay = np.maximum(0.0, 4.0 - 3.0 * service)
    ordered = np.sort(service, axis=0)
    cvar = ordered[:5].mean(axis=0)
    real = np.clip(service[:, 0, 0] + 0.015 * np.sin(np.arange(48) * 0.23), 0.0, 1.0)
    sham = np.clip(service[:, 0, 0] - 0.015 * np.sin(np.arange(48) * 0.23), 0.0, 1.0)
    return {
        "schema": "DISH_RBHR_R05_GATE_B_SYNTHETIC_EVALUATION_V1",
        "test_only": True,
        "tapes": 48,
        "arms": 5,
        "mask_views": 2,
        "complete_rows": int(service.size),
        "all_finite": bool(np.isfinite(service).all() and np.isfinite(deficit).all() and np.isfinite(delay).all()),
        "paired_fork_count": 48,
        "fork_pairing_exact": bool(real.shape == sham.shape),
        "reducer_digest": hashlib.sha256(
            np.concatenate((service.ravel(), deficit.ravel(), delay.ravel(), cvar.ravel(), real, sham)).tobytes()
        ).hexdigest(),
        "question_relevant_output": False,
    }


def _synthetic_blocks() -> np.ndarray:
    block = np.arange(24, dtype=np.float64)[:, None]
    estimand = np.arange(15, dtype=np.float64)[None, :]
    values = 0.1 * np.sin((block + 1.0) * (estimand + 1.0) * 0.07) + 0.01 * estimand
    values[:, 0] = 0.0  # Exercise the point-interval branch.
    return values


def run_gate_b_fixture(root: Path, *, resamples: int = 99_999) -> dict[str, object]:
    started = time.perf_counter()
    branch = load_and_validate_branch_fixture()
    update = run_synthetic_update()
    evaluation = _synthetic_evaluation()
    inference_started = time.perf_counter()
    inference = joint_max_t(_synthetic_blocks(), resamples=resamples)
    inference_wall = time.perf_counter() - inference_started
    record = SyntheticResumeRecord(
        namespace=TEST_NAMESPACE,
        fixture_schema=str(update["schema"]),
        synthetic_update_count=1,
        lane_count=int(update["lanes"]),
        transition_count=int(update["transitions"]),
        model_state_digest=str(update["model_state_digest"]),
        optimizer_state_digest=str(update["optimizer_state_digest"]),
        welford_state_digest=str(update["welford_state_digest"]),
    )
    resume_path = root / "resume" / "synthetic-update-0001.json"
    resume_digest = write_once_atomic(resume_path, record.payload())
    verified = read_verified(resume_path)
    if verified != record.payload():
        raise RuntimeError("synthetic resume round-trip mismatch")
    return {
        "schema": "DISH_RBHR_R05_GATE_B_SYNTHETIC_FULL_CHAIN_V1",
        "namespace": TEST_NAMESPACE,
        "test_only": True,
        "scientific_master": False,
        "scientific_model_or_checkpoint": False,
        "question_relevant_output": False,
        "branch_case_count": len(branch["cases"]),
        "branch_first_match_complete": True,
        "synthetic_update": update,
        "synthetic_evaluation": evaluation,
        "synthetic_inference": inference,
        "inference_wall_seconds": inference_wall,
        "resume_path": str(resume_path),
        "resume_digest": resume_digest,
        "resume_evaluable": False,
        "wall_seconds": time.perf_counter() - started,
    }
