"""Result-blind, same-coordinate continuation for RISP-B1 revision-07 Lock 2.

This module does not define a new experiment.  It rematerializes the exact
revision-07 event keys and numerical path, commits complete engineering units,
and exposes scientific values only after every registered unit is present.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

from lock2_experiment import (
    ARCHITECTURES,
    FEEDBACKS,
    LOCK2_SCHEMA,
    SCHEDULE_LABELS,
    EvalAccumulator,
    RISPModel,
    ResourceGuard,
    ResourceLimitExceeded,
    SamplerAudit,
    _load_frozen_checkpoint,
    _peak_rss_or_none,
    analyse,
    evaluate_cell,
    evaluate_control,
    materialize_initialization,
    train_model,
)


SCIENCE_REVISION = "RISP-B1-SCIENCE-20260813-07"
RESUME_SCHEMA = "RISP-B1-LOCK2-RESUME-20260813-07"
UNIT_SCHEMA = "RISP-B1-LOCK2-UNIT-20260813-07"
COMMIT_SCHEMA = "RISP-B1-LOCK2-UNIT-COMMIT-20260813-07"
FINAL_COMMIT_SCHEMA = "RISP-B1-LOCK2-FINAL-COMMIT-20260813-07"
IMPLEMENTATION_LOCK_SCHEMA = "RISP-B1-LOCK2-RESUME-IMPLEMENTATION-20260813-07"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _atomic_replace(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_create(path: Path, payload: bytes) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to replace committed object: {path}")
    _atomic_replace(path, payload)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _checkpoint_paths(checkpoint_dir: Path) -> dict[tuple[int, str], Path]:
    expected = {
        (seed, architecture): checkpoint_dir / f"seed_{seed}_{architecture}.npz"
        for seed in range(8)
        for architecture in ARCHITECTURES
    }
    actual = {path.name for path in checkpoint_dir.glob("*.npz")}
    expected_names = {path.name for path in expected.values()}
    if actual != expected_names or any(not path.is_file() for path in expected.values()):
        raise RuntimeError("retained revision-07 checkpoint barrier is incomplete or contains foreign NPZ files")
    return expected


def _manifest_payload(
    resume_root: Path,
    checkpoint_dir: Path,
    lock1_path: Path,
    activity_marker: Path,
    incomplete_receipt: Path,
) -> dict[str, Any]:
    checkpoints = _checkpoint_paths(checkpoint_dir)
    return {
        "schema": RESUME_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "one_scientific_campaign": True,
        "same_coordinate_rematerialization": True,
        "partial_value_exposure_forbidden": True,
        "resume_root": str(resume_root.resolve()),
        "checkpoint_dir": str(checkpoint_dir.resolve()),
        "lock1": {"path": str(lock1_path.resolve()), "sha256": _sha256_file(lock1_path)},
        "activity_marker": {"path": str(activity_marker.resolve()), "sha256": _sha256_file(activity_marker)},
        "original_incomplete_receipt": {
            "path": str(incomplete_receipt.resolve()),
            "sha256": _sha256_file(incomplete_receipt),
        },
        "core_source_sha256": _sha256_file(Path(__file__).with_name("lock2_experiment.py")),
        "checkpoints": {
            f"{seed}:{architecture}": {
                "path": str(path.resolve()),
                "sha256": _sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for (seed, architecture), path in sorted(checkpoints.items())
        },
        "expected_units": {"training": 16, "factorial": 160, "control": 80},
        "order": {
            "training": "seed,architecture,all_256_updates",
            "factorial": "seed,architecture,feedback,schedule",
            "control": "seed,controller,schedule",
        },
    }


def _prepare_manifest(
    resume_root: Path,
    checkpoint_dir: Path,
    lock1_path: Path,
    activity_marker: Path,
    incomplete_receipt: Path,
) -> dict[str, Any]:
    lock1 = _load_json(lock1_path)
    marker = _load_json(activity_marker)
    receipt = _load_json(incomplete_receipt)
    if lock1.get("certificate_result") != "PASS" or lock1.get("scientific_activity_started") is not False:
        raise RuntimeError("retained Lock-1 certificate is not the exact preactivity PASS")
    if marker.get("science_revision") != SCIENCE_REVISION or marker.get("scientific_activity_started") is not True:
        raise RuntimeError("retained activity marker does not establish active revision-07 campaign")
    if receipt.get("science_revision") != SCIENCE_REVISION or receipt.get("scientific_activity_started") is not True:
        raise RuntimeError("retained lifecycle receipt does not belong to active revision-07 campaign")
    if receipt.get("complete_panel_retained") is not False or receipt.get("result_written") is not False:
        raise RuntimeError("retained lifecycle receipt is not the expected incomplete no-result frontier")

    expected = _manifest_payload(resume_root, checkpoint_dir, lock1_path, activity_marker, incomplete_receipt)
    manifest_path = resume_root / "manifest.json"
    if manifest_path.exists():
        observed = _load_json(manifest_path)
        if observed != expected:
            raise RuntimeError("resume manifest identity differs from the retained revision-07 campaign")
    else:
        _atomic_create(manifest_path, _json_bytes(expected))
    return expected


def _prepare_implementation_lock(resume_root: Path, output: Path) -> dict[str, Any]:
    expected = {
        "schema": IMPLEMENTATION_LOCK_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "output": str(output.resolve()),
        "core_source_sha256": _sha256_file(Path(__file__).with_name("lock2_experiment.py")),
        "resume_source_sha256": _sha256_file(Path(__file__)),
        "runner_source_sha256": _sha256_file(Path(__file__).with_name("run_lock2_resume.py")),
    }
    path = resume_root / "IMPLEMENTATION.lock.json"
    if path.exists():
        observed = _load_json(path)
        if observed != expected:
            raise RuntimeError("resume implementation or retained output identity differs from the accepted frontier")
    else:
        _atomic_create(path, _json_bytes(expected))
    return expected


def _unit_paths(resume_root: Path, unit_id: str) -> tuple[Path, Path]:
    base = resume_root / "units" / unit_id
    return base.with_suffix(".json"), base.with_suffix(".commit.json")


def _committed_unit(resume_root: Path, unit_id: str) -> dict[str, Any] | None:
    payload_path, commit_path = _unit_paths(resume_root, unit_id)
    if not commit_path.exists():
        return None
    commit = _load_json(commit_path)
    if commit.get("schema") != COMMIT_SCHEMA or commit.get("unit_id") != unit_id:
        raise RuntimeError(f"malformed commit leaf: {commit_path}")
    if not payload_path.is_file():
        raise RuntimeError(f"committed unit payload is missing: {payload_path}")
    if payload_path.stat().st_size != commit.get("bytes") or _sha256_file(payload_path) != commit.get("sha256"):
        raise RuntimeError(f"committed unit payload digest mismatch: {payload_path}")
    return commit


def _commit_unit(resume_root: Path, unit_id: str, payload: dict[str, Any]) -> None:
    payload_path, commit_path = _unit_paths(resume_root, unit_id)
    if commit_path.exists():
        raise RuntimeError(f"unit is already committed: {unit_id}")
    encoded = _json_bytes(payload)
    _atomic_replace(payload_path, encoded)
    commit = {
        "schema": COMMIT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "unit_id": unit_id,
        "payload": str(payload_path.resolve()),
        "bytes": len(encoded),
        "sha256": _sha256_bytes(encoded),
    }
    _atomic_create(commit_path, _json_bytes(commit))


def _read_unit_after_complete(resume_root: Path, unit_id: str) -> dict[str, Any]:
    if _committed_unit(resume_root, unit_id) is None:
        raise RuntimeError(f"attempted to read uncommitted unit: {unit_id}")
    payload_path, _ = _unit_paths(resume_root, unit_id)
    payload = _load_json(payload_path)
    if payload.get("schema") != UNIT_SCHEMA or payload.get("unit_id") != unit_id:
        raise RuntimeError(f"unit payload identity mismatch: {unit_id}")
    return payload


def _accumulator_payload(accumulator: EvalAccumulator) -> dict[str, Any]:
    return {
        "reward_by_tick": accumulator.reward_by_tick.tolist(),
        "reward_by_renewal": accumulator.reward_by_renewal.tolist(),
        "renewal_observations": accumulator.renewal_observations.tolist(),
        "action_counts": accumulator.action_counts.tolist(),
        "entropy_sum": accumulator.entropy_sum,
        "decisions": accumulator.decisions,
        "updates": accumulator.updates,
        "projection_active": accumulator.projection_active,
        "nonzero_sign_packets": accumulator.nonzero_sign_packets,
        "eligibility_gt_005": accumulator.eligibility_gt_005,
        "tv_rows": accumulator.tv_rows,
        "tv_ge_0005": accumulator.tv_ge_0005,
        "support_min": accumulator.support_min,
        "residual_sign_errors": accumulator.residual_sign_errors,
        "terminal_residual_diagnostics": accumulator.terminal_residual_diagnostics,
        "zero_signs": accumulator.zero_signs,
        "mechanism_read": accumulator.mechanism_read,
        "pbar_min": accumulator.pbar_min,
        "pbar_max": accumulator.pbar_max,
        "twin_rows": accumulator.twin_rows,
        "recipient_sign_counts": dict(accumulator.recipient_sign_counts),
        "twin_sign_counts": dict(accumulator.twin_sign_counts),
        "discordance_counts": dict(accumulator.discordance_counts),
        "fork_tv_sum": accumulator.fork_tv_sum,
        "fork_return_realized_sum": accumulator.fork_return_realized_sum,
        "fork_return_twin_sum": accumulator.fork_return_twin_sum,
        "fork_agent_rows": accumulator.fork_agent_rows,
    }


def _accumulator_from_payload(payload: dict[str, Any]) -> EvalAccumulator:
    accumulator = EvalAccumulator()
    accumulator.reward_by_tick = np.asarray(payload["reward_by_tick"], dtype=np.float64)
    accumulator.reward_by_renewal = np.asarray(payload["reward_by_renewal"], dtype=np.float64)
    accumulator.renewal_observations = np.asarray(payload["renewal_observations"], dtype=np.int64)
    accumulator.action_counts = np.asarray(payload["action_counts"], dtype=np.int64)
    for name in (
        "entropy_sum", "decisions", "updates", "projection_active", "nonzero_sign_packets",
        "eligibility_gt_005", "tv_rows", "tv_ge_0005", "support_min",
        "residual_sign_errors", "terminal_residual_diagnostics", "zero_signs", "mechanism_read",
        "pbar_min", "pbar_max", "twin_rows", "fork_tv_sum", "fork_return_realized_sum",
        "fork_return_twin_sum", "fork_agent_rows",
    ):
        setattr(accumulator, name, payload[name])
    accumulator.recipient_sign_counts = defaultdict(lambda: [0, 0], {key: list(value) for key, value in payload["recipient_sign_counts"].items()})
    accumulator.twin_sign_counts = defaultdict(lambda: [0, 0], {key: list(value) for key, value in payload["twin_sign_counts"].items()})
    accumulator.discordance_counts = defaultdict(lambda: [0, 0], {key: list(value) for key, value in payload["discordance_counts"].items()})
    return accumulator


def _merge_sampler(target: SamplerAudit, payload: dict[str, Any]) -> None:
    for kind, count in payload["calls"].items():
        target.calls[kind] += int(count)
    for kind, count in payload["attempts"].items():
        target.attempts[kind] += int(count)
    for kind, count in payload["raw_words"].items():
        target.words[kind] += int(count)
    for kind, count in payload["rejections"].items():
        target.rejections[kind] += int(count)
    for kind, count in payload["max_attempts"].items():
        target.max_attempts[kind] = max(target.max_attempts[kind], int(count))
    for kind, histogram in payload["attempt_histogram"].items():
        for attempts, count in histogram.items():
            target.attempt_histogram[kind][int(attempts)] += int(count)


def _models_equal(candidate: RISPModel, retained: RISPModel) -> bool:
    left = dict(candidate.named_parameters())
    right = dict(retained.named_parameters())
    if left.keys() != right.keys():
        return False
    return all(
        torch.equal(left[name].detach().view(torch.int32), right[name].detach().view(torch.int32))
        for name in left
    )


def _checkpoint_info(manifest: dict[str, Any], seed: int, architecture: str) -> dict[str, Any]:
    value = manifest["checkpoints"][f"{seed}:{architecture}"]
    return {
        "path": value["path"],
        "sha256": value["sha256"],
        "learned_scalars": 117,
        "slow_parameters_frozen_before_evaluation": True,
    }


def _training_unit_id(seed: int, architecture: str) -> str:
    return f"training/seed_{seed}_{architecture}"


def _factorial_unit_id(seed: int, architecture: str, feedback: str, schedule: int) -> str:
    return f"factorial/seed_{seed}_{architecture}_{feedback}_schedule_{schedule}"


def _control_unit_id(seed: int, controller: str, schedule: int) -> str:
    return f"control/seed_{seed}_{controller}_schedule_{schedule}"


def _all_unit_ids() -> list[str]:
    return (
        [_training_unit_id(seed, architecture) for seed in range(8) for architecture in ARCHITECTURES]
        + [_factorial_unit_id(seed, architecture, feedback, schedule) for seed in range(8) for architecture in ARCHITECTURES for feedback in FEEDBACKS for schedule in range(5)]
        + [_control_unit_id(seed, controller, schedule) for seed in range(8) for controller in ("UNIFORM", "STATE_ORACLE") for schedule in range(5)]
    )


def _frontier_counts(resume_root: Path) -> dict[str, int]:
    counts = {"training": 0, "factorial": 0, "control": 0}
    for unit_id in _all_unit_ids():
        if _committed_unit(resume_root, unit_id) is not None:
            counts[unit_id.split("/", 1)[0]] += 1
    return counts


def _write_slice_receipt(resume_root: Path, status: str, guard: ResourceGuard, detail: str | None = None) -> Path:
    receipt_dir = resume_root / "slice_receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    index = len(list(receipt_dir.glob("slice_*.json")))
    path = receipt_dir / f"slice_{index:04d}.json"
    payload = {
        "schema": "RISP-B1-LOCK2-SLICE-RECEIPT-20260813-07",
        "science_revision": SCIENCE_REVISION,
        "status": status,
        "elapsed_seconds": guard.elapsed(),
        "peak_rss_bytes": _peak_rss_or_none(),
        "frontier": _frontier_counts(resume_root),
        "detail": detail,
        "partial_scientific_values_exposed": False,
    }
    _atomic_create(path, _json_bytes(payload))
    return path


def _finalize(
    output: Path,
    resume_root: Path,
    manifest: dict[str, Any],
    lock1_path: Path,
    activity_marker: Path,
    guard: ResourceGuard,
) -> dict[str, Any]:
    missing = [unit_id for unit_id in _all_unit_ids() if _committed_unit(resume_root, unit_id) is None]
    if missing:
        raise RuntimeError(f"finalization refused with {len(missing)} uncommitted units")

    lock1 = _load_json(lock1_path)
    audit = SamplerAudit()
    seed_results: list[dict[str, Any]] = []
    accumulators: dict[tuple[str, str, int], list[EvalAccumulator]] = defaultdict(list)
    for seed in range(8):
        seed_result: dict[str, Any] = {
            "seed": seed,
            "training": {},
            "checkpoints": {},
            "cells": {},
            "controls": {},
            "all_16_checkpoints_frozen_before_any_evaluation": True,
        }
        for architecture in ARCHITECTURES:
            training = _read_unit_after_complete(resume_root, _training_unit_id(seed, architecture))
            seed_result["training"][architecture] = training["training"]
            seed_result["checkpoints"][architecture] = _checkpoint_info(manifest, seed, architecture)
            _merge_sampler(audit, training["sampler"])
            seed_result["cells"][architecture] = {}
            for feedback in FEEDBACKS:
                seed_result["cells"][architecture][feedback] = {}
                for schedule in range(5):
                    payload = _read_unit_after_complete(resume_root, _factorial_unit_id(seed, architecture, feedback, schedule))
                    seed_result["cells"][architecture][feedback][str(schedule)] = payload["result"]
                    accumulators[(architecture, feedback, schedule)].append(_accumulator_from_payload(payload["accumulator"]))
                    _merge_sampler(audit, payload["sampler"])
        for controller in ("UNIFORM", "STATE_ORACLE"):
            seed_result["controls"][controller] = {}
            for schedule in range(5):
                payload = _read_unit_after_complete(resume_root, _control_unit_id(seed, controller, schedule))
                seed_result["controls"][controller][str(schedule)] = payload["result"]
                _merge_sampler(audit, payload["sampler"])
        for architecture in ARCHITECTURES:
            for feedback in FEEDBACKS:
                for schedule in range(5):
                    cell = seed_result["cells"][architecture][feedback][str(schedule)]
                    oracle_j = seed_result["controls"]["STATE_ORACLE"][str(schedule)]["J"]
                    cell["physical_time_regret_to_state_oracle_J"] = oracle_j - cell["J"]
        seed_results.append(seed_result)

    analysis = analyse(seed_results, accumulators, audit, lock1)
    sampler_audit = audit.result()
    peak_candidates = [_peak_rss_or_none() or 0]
    original_receipt = _load_json(Path(manifest["original_incomplete_receipt"]["path"]))
    peak_candidates.append(int(original_receipt.get("peak_rss_bytes") or 0))
    for receipt_path in sorted((resume_root / "slice_receipts").glob("slice_*.json")):
        peak_candidates.append(int(_load_json(receipt_path).get("peak_rss_bytes") or 0))
    result = {
        "schema": LOCK2_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "activity": {
            "scientific_activity_started": True,
            "boundary": "first retained revision-07 PCG64 initialization-family object",
            "activity_marker": str(activity_marker.resolve()),
            "complete_panel_retained": True,
            "one_scientific_campaign": True,
            "same_coordinate_engineering_resume": True,
        },
        "lock1": {"path": str(lock1_path.resolve()), "sha256": _sha256_file(lock1_path), "passed_before_activity": True},
        "execution_order": {
            "phase_1": "same-coordinate training audit replay matched all retained 8x2 final checkpoints",
            "checkpoint_barrier_count": 16,
            "phase_2": "complete factorial/control/fork cells committed before aggregation",
            "any_evaluation_before_checkpoint_barrier": False,
        },
        "frozen_panel": {
            "algorithm_seeds": list(range(8)),
            "architectures": list(ARCHITECTURES),
            "feedbacks": list(FEEDBACKS),
            "schedules": SCHEDULE_LABELS,
            "training_updates": 256,
            "batch_size": 16,
            "training_k": [4, 8],
            "evaluation_episodes_per_cell": 64,
            "optimizer": {"name": "AdamW", "learning_rate": 3e-4, "betas": [0.9, 0.999], "epsilon": 1e-8, "decoupled_weight_decay": 1e-4, "global_gradient_clip": 1.0},
            "processes": 1,
            "cpu_threads": 1,
            "gpu_visible": False,
        },
        "sampler_audit": {**sampler_audit, "initialization_family_raw_words": 800, "all_registered_raw_words_including_initialization": sampler_audit["total_raw_words"] + 800},
        "seed_results": seed_results,
        "analysis": analysis,
        "runtime": {
            "completed_via_blinded_atomic_resume": True,
            "wall_seconds": guard.elapsed(),
            "wall_below_60_minutes": False,
            "finalization_slice_wall_seconds": guard.elapsed(),
            "per_slice_wall_limit_seconds": guard.wall_limit_seconds,
            "peak_rss_bytes": max(peak_candidates),
            "peak_rss_below_1_gib": max(peak_candidates) < (1 << 30),
            "rss_limit_bytes": guard.rss_limit_bytes,
            "active_in_process_guard": True,
        },
        "anomalies": [],
    }
    encoded = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    if output.exists():
        raise FileExistsError(f"refusing to replace retained complete result: {output}")
    _atomic_create(output, encoded)
    final_commit = {
        "schema": FINAL_COMMIT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "result": str(output.resolve()),
        "bytes": len(encoded),
        "sha256": _sha256_bytes(encoded),
        "complete_units": len(_all_unit_ids()),
    }
    _atomic_create(resume_root / "FINAL_COMPLETE.commit.json", _json_bytes(final_commit))
    return result


def run_resume(
    output: Path,
    checkpoint_dir: Path,
    lock1_path: Path,
    activity_marker: Path,
    incomplete_receipt: Path,
    resume_root: Path,
    wall_limit_seconds: float,
) -> dict[str, Any]:
    resume_root.mkdir(parents=True, exist_ok=True)
    orphan_result = False
    final_commit_path = resume_root / "FINAL_COMPLETE.commit.json"
    if output.exists():
        if final_commit_path.exists():
            final_commit = _load_json(final_commit_path)
            expected_commit_fields = {
                "schema": FINAL_COMMIT_SCHEMA,
                "science_revision": SCIENCE_REVISION,
                "result": str(output.resolve()),
                "bytes": output.stat().st_size,
                "complete_units": len(_all_unit_ids()),
            }
            if any(final_commit.get(key) != value for key, value in expected_commit_fields.items()):
                raise RuntimeError("retained FINAL_COMPLETE identity is malformed")
            if _sha256_file(output) != final_commit.get("sha256"):
                raise RuntimeError("retained result digest differs from FINAL_COMPLETE")
            return {"status": "COMPLETE", "result": str(output.resolve()), "already_complete": True}
        # A crash after result rename but before its commit leaf leaves an
        # internal orphan.  Never parse it; defer disposal until the exact
        # campaign manifest and complete unit ledger have been re-established.
        orphan_result = True
    elif final_commit_path.exists():
        raise RuntimeError("FINAL_COMPLETE exists without its retained result")

    manifest = _prepare_manifest(resume_root, checkpoint_dir, lock1_path, activity_marker, incomplete_receipt)
    _prepare_implementation_lock(resume_root, output)
    guard = ResourceGuard(wall_limit_seconds=wall_limit_seconds, rss_limit_bytes=1 << 30)

    try:
        for seed in range(8):
            for architecture in ARCHITECTURES:
                unit_id = _training_unit_id(seed, architecture)
                if _committed_unit(resume_root, unit_id) is not None:
                    continue
                guard.check("before_training_replay_unit", phase="training_replay", seed=seed, architecture=architecture)
                initialization = materialize_initialization(seed)
                model = RISPModel(initialization, architecture)
                audit = SamplerAudit()
                training_result = train_model(model, seed, audit, guard)
                checkpoint = _checkpoint_info(manifest, seed, architecture)
                retained = _load_frozen_checkpoint(Path(checkpoint["path"]), architecture, checkpoint["sha256"])
                if not _models_equal(model, retained):
                    raise RuntimeError(f"same-coordinate training replay disagrees with retained checkpoint: seed={seed} architecture={architecture}")
                guard.check("training_replay_unit_complete", phase="training_replay", seed=seed, architecture=architecture)
                _commit_unit(resume_root, unit_id, {
                    "schema": UNIT_SCHEMA,
                    "science_revision": SCIENCE_REVISION,
                    "unit_id": unit_id,
                    "training": training_result,
                    "sampler": audit.result(),
                    "retained_checkpoint_sha256": checkpoint["sha256"],
                    "bit_identical_to_retained_checkpoint": True,
                })
                del model, retained, initialization

        for seed in range(8):
            # Preserve the original revision-07 seed-local order: both learned
            # architectures/cells first, then both descriptive controllers.
            for architecture in ARCHITECTURES:
                checkpoint = _checkpoint_info(manifest, seed, architecture)
                for feedback in FEEDBACKS:
                    for schedule in range(5):
                        unit_id = _factorial_unit_id(seed, architecture, feedback, schedule)
                        if _committed_unit(resume_root, unit_id) is not None:
                            continue
                        guard.check("before_factorial_unit", phase="evaluation", seed=seed, architecture=architecture, feedback=feedback, schedule_id=schedule)
                        model = _load_frozen_checkpoint(Path(checkpoint["path"]), architecture, checkpoint["sha256"])
                        audit = SamplerAudit()
                        result, accumulator = evaluate_cell(model, seed, schedule, feedback, audit, guard)
                        guard.check("factorial_unit_complete", phase="evaluation", seed=seed, architecture=architecture, feedback=feedback, schedule_id=schedule)
                        _commit_unit(resume_root, unit_id, {
                            "schema": UNIT_SCHEMA,
                            "science_revision": SCIENCE_REVISION,
                            "unit_id": unit_id,
                            "result": result,
                            "accumulator": _accumulator_payload(accumulator),
                            "sampler": audit.result(),
                        })
                        del model
            for controller in ("UNIFORM", "STATE_ORACLE"):
                for schedule in range(5):
                    unit_id = _control_unit_id(seed, controller, schedule)
                    if _committed_unit(resume_root, unit_id) is not None:
                        continue
                    guard.check("before_control_unit", phase="control", seed=seed, controller=controller, schedule_id=schedule)
                    audit = SamplerAudit()
                    result = evaluate_control(seed, schedule, controller, audit, guard)
                    guard.check("control_unit_complete", phase="control", seed=seed, controller=controller, schedule_id=schedule)
                    _commit_unit(resume_root, unit_id, {
                        "schema": UNIT_SCHEMA,
                        "science_revision": SCIENCE_REVISION,
                        "unit_id": unit_id,
                        "result": result,
                        "sampler": audit.result(),
                    })

        if orphan_result:
            if any(_committed_unit(resume_root, unit_id) is None for unit_id in _all_unit_ids()):
                raise RuntimeError("orphan result exists before the complete committed unit ledger")
            output.unlink()
        result = _finalize(output, resume_root, manifest, lock1_path, activity_marker, guard)
        receipt = _write_slice_receipt(resume_root, "COMPLETE", guard)
        return {"status": "COMPLETE", "result": str(output.resolve()), "receipt": str(receipt.resolve()), "analysis": result["analysis"]}
    except ResourceLimitExceeded as exc:
        receipt = _write_slice_receipt(resume_root, "PAUSED_RESOURCE", guard, str(exc))
        return {"status": "PAUSED_RESOURCE", "receipt": str(receipt.resolve()), "frontier": _frontier_counts(resume_root)}
