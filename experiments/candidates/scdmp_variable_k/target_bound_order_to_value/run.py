from __future__ import annotations

import os

for _name in (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
import hashlib
import json
import sys
import time
import traceback
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import torch

from .assay import evaluate_seed
from .checkpoint import ExactAdamW, MinibatchPlan, SegmentStore, train_checkpoint
from .config import (
    BRANCHES, CANDIDATE, CARD_SHA256, HMAC_SEED_NAMESPACE, LOGICAL_STEPS,
    MODEL_PARAMETER_COUNT, PROSPECTIVE_COST, REVISION, SEED_INDICES, static_contract,
)
from .corpus import materialize_seed, output_scales, seed_manifest
from .frontier import atomic_save as save_frontier
from .frontier import load as load_frontier
from .frontier import model_state
from .inference import complete_inference
from .lifecycle import Lifecycle
from .model import SegmentModel
from .result import complete_packet
from .rng import HMACStream, identity_digests, manifest_digests, sample_fresh_master


def _atomic_json(path: Path, value: object) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(target) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)


def static_conformance() -> dict[str, object]:
    model = SegmentModel()
    card_path = Path(__file__).resolve().parents[4] / (
        "docs/research/candidates/semigroup_consistent_duration_model_policy/"
        "SCDMP_TARGET_BOUND_ORDER_TO_VALUE_SCIENCE_CARD_REVISION_07.md"
    )
    actual_card_sha256 = hashlib.sha256(
        card_path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
    checks = {
        "candidate_exact": CANDIDATE == "SCDMP-TARGET-BOUND-ORDER-TO-VALUE",
        "revision_exact": REVISION == "SCDMP-TBOV-SCIENCE-20260815-07",
        "card_sha256_exact": actual_card_sha256 == CARD_SHA256,
        "literal_r06_hmac_namespace_retained": HMAC_SEED_NAMESPACE
            == b"SCDMP-TBOV-r06/STAGE-A/seed/",
        "stage_a_seed_count_exact": SEED_INDICES == tuple(range(10)),
        "model_parameter_count_exact": sum(p.numel() for p in model.parameters())
            == MODEL_PARAMETER_COUNT == 97_706,
        "one_based_adamw_steps_exact": LOGICAL_STEPS == 600,
        "nine_first_true_branches_exact": len(BRANCHES) == 9,
        "stage_a_cost_exact": PROSPECTIVE_COST["total_model_examples"] == 56_151_040,
        "stage_b_absent": True,
    }
    return {
        "artifact_kind": "SCDMP_TBOV_R07_PREACTIVITY_STATIC_CONFORMANCE",
        "candidate": CANDIDATE,
        "revision": REVISION,
        "checks": checks,
        "conforming": all(checks.values()),
        "scientific_activity_started": False,
        "question_relevant_output_exists": False,
        "heavy_compute_executed": False,
        "static_contract": static_contract(),
        "science_card": str(card_path),
        "production_module": "experiments.candidates.scdmp_variable_k.target_bound_order_to_value",
    }


def _validate_lease(path: Path, result_root: Path) -> dict[str, object]:
    lease = json.loads(path.resolve().read_text(encoding="utf-8"))
    try:
        not_after = datetime.fromisoformat(str(lease.get("not_after_utc", "")).replace("Z", "+00:00"))
        unexpired = not_after.tzinfo is not None and not_after > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        unexpired = False
    stage_boundary = str(lease.get("stage_boundary", ""))
    stage_boundary_lower = stage_boundary.lower()
    stage_b_excluded = "stage b" not in stage_boundary_lower or any(
        phrase in stage_boundary_lower
        for phrase in (
            "stage b is not authorized",
            "stage b not authorized",
            "no stage b",
        )
    )
    checks = {
        "direction": lease.get("direction") == "semigroup_consistent_duration_model_policy",
        "revision": lease.get("revision") == REVISION,
        "production_authorized": lease.get("production_authorized") is True,
        "not_revoked": lease.get("revoked", False) is False,
        "authorized_seeds": lease.get("authorized_seeds") == list(SEED_INDICES),
        "max_workers": int(lease.get("max_workers", 0)) == 1,
        "cpu_cores": int(lease.get("cpu_cores", 0)) >= 1,
        "gpu_count": int(lease.get("gpu_count", -1)) == 0,
        "unexpired": unexpired,
        "result_root": Path(str(lease.get("result_root"))).resolve() == result_root.resolve(),
        "stage_boundary": "stage a" in stage_boundary_lower and stage_b_excluded,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Root lease does not authorize exact r07 Stage A: {checks}")
    return lease


def _implementation_facts(microbatch_examples: int) -> dict[str, object]:
    import numpy as np
    import scipy

    return {
        "python": sys.version,
        "numpy": np.__version__,
        "torch": torch.__version__,
        "scipy": scipy.__version__,
        "cpu_threads": 1,
        "gpu_used": False,
        "microbatch_examples": microbatch_examples,
    }


def _new_frontier(master: bytes, lifecycle: Lifecycle,
                  microbatch_examples: int) -> dict[str, object]:
    panel_digest, seed_digests = identity_digests(master)
    return {
        "candidate": CANDIDATE,
        "revision": REVISION,
        "stage": "STAGE_A_ONLY",
        "partial_selection_permitted": False,
        "master_M_hex_sealed": master.hex(),
        "panel_digest": panel_digest,
        "seed_digests": list(seed_digests),
        "manifest": None,
        "next_seed_index": 0,
        "active_seed": None,
        "seed_results": [],
        "checkpoint_states": {},
        "lifecycle": lifecycle.facts(),
        "anomalies": [],
        "implementation_facts": _implementation_facts(microbatch_examples),
    }


def _build_manifest(master: bytes, manifest_root: Path,
                    before_boundary: Callable[[], None] | None = None) -> dict[str, object]:
    per_seed = []
    for seed_index in SEED_INDICES:
        if before_boundary is not None:
            before_boundary()
        corpus = materialize_seed(master, seed_index)
        initializer = HMACStream.for_domain(master, seed_index, "checkpoint_init")
        model = SegmentModel()
        model.exact_initialize(initializer)
        minibatches = MinibatchPlan(
            HMACStream.for_domain(master, seed_index, "checkpoint_minibatch"),
        )
        per_seed.append(seed_manifest(
            master, corpus, initializer.draw_count, minibatches.draw_count,
        ))
    panel_digest, seed_digests = identity_digests(master)
    manifest = {
        "artifact_kind": "SCDMP_TBOV_R07_CREATE_ONLY_STAGE_A_MANIFEST",
        "candidate": CANDIDATE,
        "revision": REVISION,
        "panel_digest": panel_digest,
        "seed_digests": list(seed_digests),
        "hmac_seed_namespace": HMAC_SEED_NAMESPACE.decode("ascii"),
        "per_seed": per_seed,
        "raw_master_present": False,
    }
    path = manifest_root.resolve() / f"{panel_digest}.json"
    if before_boundary is not None:
        before_boundary()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != manifest:
            raise RuntimeError("existing r07 create-only manifest differs from reconstruction")
    else:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
    return {**manifest, "path": str(path)}


def _reconcile_installed_result(output: Path, frontier_path: Path,
                                installed: dict[str, object],
                                before_update: Callable[[], None] | None = None) \
        -> dict[str, object]:
    """Fail closed unless a complete result names this exact retained frontier."""
    output, frontier_path = output.resolve(), frontier_path.resolve()
    sidecar_path = Path(str(output) + ".activity.json").resolve()
    if not frontier_path.exists():
        raise RuntimeError("installed r07 result lacks its retained atomic frontier")
    retained = load_frontier(frontier_path)
    manifest = installed.get("manifest")
    if not isinstance(manifest, dict):
        raise RuntimeError("installed r07 result lacks its identity manifest")
    raw_seed_digests = manifest.get("seed_digests")
    frontier_seed_digests = retained.get("seed_digests")
    master_hex = installed.get("master_M_hex_revealed_only_in_complete_result")
    master = b""
    try:
        master = bytes.fromhex(str(master_hex))
        derived_panel_digest, derived_seed_digests = identity_digests(master)
    except (TypeError, ValueError):
        derived_panel_digest, derived_seed_digests = None, ()
    retained_frontier = installed.get("retained_frontier")
    activity_sidecar = installed.get("activity_sidecar")
    checks = {
        "artifact_kind": installed.get("artifact_kind")
            == "SCDMP_TBOV_R07_COMPLETE_STAGE_A_RESULT",
        "candidate": installed.get("candidate") == CANDIDATE,
        "revision": installed.get("revision") == REVISION,
        "stage_a_only": installed.get("stage") == "STAGE_A_ONLY"
            and installed.get("stage_b") is None
            and installed.get("stage_b_implemented_or_executed") is False,
        "complete_atomic_panel": installed.get("complete") is True
            and installed.get("partial_selection_permitted") is False,
        "canonical_retained_frontier": isinstance(retained_frontier, str)
            and retained_frontier == str(frontier_path),
        "canonical_activity_sidecar": isinstance(activity_sidecar, str)
            and activity_sidecar == str(sidecar_path),
        "panel_digest": isinstance(manifest.get("panel_digest"), str)
            and manifest.get("panel_digest") == retained.get("panel_digest")
            == derived_panel_digest,
        "seed_digests": isinstance(raw_seed_digests, list)
            and isinstance(frontier_seed_digests, list)
            and raw_seed_digests == frontier_seed_digests == list(derived_seed_digests),
        "sealed_master": isinstance(master_hex, str) and len(master) == 32
            and retained.get("master_M_hex_sealed") == master_hex,
        "lifecycle": isinstance(installed.get("lifecycle"), dict),
    }
    retained_manifest = retained.get("manifest")
    if retained_manifest is not None:
        checks["frontier_manifest_identity"] = isinstance(retained_manifest, dict) \
            and retained_manifest.get("panel_digest") == derived_panel_digest \
            and retained_manifest.get("seed_digests") == list(derived_seed_digests)
    if not all(checks.values()):
        raise RuntimeError(f"installed r07 result/frontier identity mismatch: {checks}")
    if before_update is not None:
        before_update()
    retained["lifecycle"] = installed["lifecycle"]
    retained["final_result"] = str(output)
    retained["question_relevant_output_exists"] = True
    save_frontier(frontier_path, retained)
    if before_update is not None:
        before_update()
    _atomic_json(sidecar_path, {
        "candidate": CANDIDATE, "revision": REVISION,
        "lifecycle": installed["lifecycle"], "final_result_installed": True,
        "result": str(output), "frontier": str(frontier_path),
        "partial_selection_permitted": False,
    })
    return installed


def production(*, output: Path, frontier_path: Path, manifest_root: Path,
               lease_path: Path, resume: bool, microbatch_examples: int = 2_048) \
        -> dict[str, object]:
    output = output.resolve()
    frontier_path = frontier_path.resolve()
    manifest_root = manifest_root.resolve()
    result_root = output.parent.resolve()
    if microbatch_examples <= 0:
        raise ValueError("physical microbatch size must be positive")
    _validate_lease(lease_path, result_root)
    sidecar_path = Path(str(output) + ".activity.json")
    if output.exists():
        installed = json.loads(output.read_text(encoding="utf-8"))
        _validate_lease(lease_path, result_root)
        return _reconcile_installed_result(
            output, frontier_path, installed,
            before_update=lambda: _validate_lease(lease_path, result_root),
        )

    if frontier_path.exists():
        if not resume:
            raise FileExistsError("r07 frontier exists; explicit --resume is required")
        frontier = load_frontier(frontier_path)
        lifecycle = Lifecycle.from_facts(frontier["lifecycle"])
        master = bytes.fromhex(str(frontier["master_M_hex_sealed"]))
        frozen_microbatch = int(frontier["implementation_facts"]["microbatch_examples"])
        if microbatch_examples != frozen_microbatch:
            raise RuntimeError(
                "same-coordinate continuation must retain the initial physical microbatch size"
            )
    else:
        if resume:
            raise FileNotFoundError("--resume requested but no r07 frontier exists")
        lifecycle = Lifecycle()
        lifecycle.begin_panel()
        _atomic_json(sidecar_path, {
            "candidate": CANDIDATE, "revision": REVISION,
            "lifecycle": lifecycle.facts(), "final_result_installed": False,
            "partial_selection_permitted": False,
        })
        _validate_lease(lease_path, result_root)
        master = sample_fresh_master(manifest_digests(manifest_root))
        frontier = _new_frontier(master, lifecycle, microbatch_examples)
        save_frontier(frontier_path, frontier)

    if frontier["manifest"] is None:
        frontier["manifest"] = _build_manifest(
            master, manifest_root,
            before_boundary=lambda: _validate_lease(lease_path, result_root),
        )
        _validate_lease(lease_path, result_root)
        lifecycle.phase = "scaler_materialization"
        lifecycle.record("complete_create_only_manifest")
        frontier["lifecycle"] = lifecycle.facts()
        save_frontier(frontier_path, frontier)

    for seed_index in range(int(frontier["next_seed_index"]), 10):
        _validate_lease(lease_path, result_root)
        corpus = materialize_seed(master, seed_index)
        scale_f, scale_g = output_scales(corpus.fit)
        initializer = HMACStream.for_domain(master, seed_index, "checkpoint_init")
        model = SegmentModel()
        model.exact_initialize(initializer)
        plan = MinibatchPlan(HMACStream.for_domain(master, seed_index, "checkpoint_minibatch"))
        optimizer = ExactAdamW(model)
        active = frontier.get("active_seed")
        if isinstance(active, dict):
            if int(active["seed_index"]) != seed_index:
                raise RuntimeError("r07 active frontier seed does not match next seed")
            model.load_state_dict(active["model_state"])
            optimizer.load_state_dict(active["optimizer_state"])
            first_step = int(active["next_step"])
        else:
            first_step = 1
        lifecycle.begin_training()
        last_complete_step_facts = active.get("last_complete_step_facts") \
            if isinstance(active, dict) else None

        def persist_active(next_step: int) -> None:
            active_value = {
                "seed_index": seed_index, "next_step": next_step,
                "model_state": model_state(model),
                "optimizer_state": optimizer.state_dict(),
            }
            if last_complete_step_facts is not None:
                active_value["last_complete_step_facts"] = last_complete_step_facts
            frontier["active_seed"] = active_value
            frontier["lifecycle"] = lifecycle.facts()
            save_frontier(frontier_path, frontier)

        def before_step(n: int) -> None:
            try:
                _validate_lease(lease_path, result_root)
            except Exception:
                persist_active(n)
                raise

        def persist_step(n: int, current_model: SegmentModel, current_optimizer: ExactAdamW,
                         loss: float, norm: float) -> None:
            nonlocal last_complete_step_facts
            last_complete_step_facts = {
                "n": n, "loss": loss, "preclip_gradient_norm": norm,
            }
            if n % 25 == 0 or n == LOGICAL_STEPS:
                persist_active(n + 1)

        _validate_lease(lease_path, result_root)
        train_checkpoint(
            model, optimizer, plan, SegmentStore(corpus.fit), scale_f, scale_g,
            first_step=first_step, before_step=before_step, on_step=persist_step,
            microbatch_examples=microbatch_examples,
        )
        if optimizer.step_number != LOGICAL_STEPS:
            raise RuntimeError("r07 seed checkpoint is not theta_600")
        _validate_lease(lease_path, result_root)
        lifecycle.begin_assay()
        seed_result = evaluate_seed(model, corpus, scale_f, scale_g)
        _validate_lease(lease_path, result_root)
        frontier["seed_results"].append(seed_result)
        frontier["checkpoint_states"][str(seed_index)] = model_state(model)
        frontier["next_seed_index"] = seed_index + 1
        frontier["active_seed"] = None
        frontier["lifecycle"] = lifecycle.facts()
        save_frontier(frontier_path, frontier)

    _validate_lease(lease_path, result_root)
    inference = complete_inference(frontier["seed_results"])
    lifecycle.complete()
    packet = complete_packet(
        master_hex=master.hex(), manifest=frontier["manifest"],
        seed_results=frontier["seed_results"], inference=inference,
        lifecycle=lifecycle.facts(), frontier_path=str(frontier_path),
        activity_sidecar=str(sidecar_path), anomalies=frontier["anomalies"],
        implementation_facts=frontier["implementation_facts"],
    )
    _validate_lease(lease_path, result_root)
    _atomic_json(output, packet)
    _validate_lease(lease_path, result_root)
    frontier["lifecycle"] = lifecycle.facts()
    frontier["final_result"] = str(output)
    frontier["question_relevant_output_exists"] = True
    save_frontier(frontier_path, frontier)
    _validate_lease(lease_path, result_root)
    _atomic_json(sidecar_path, {
        "candidate": CANDIDATE, "revision": REVISION,
        "lifecycle": lifecycle.facts(), "final_result_installed": True,
        "result": str(output), "frontier": str(frontier_path),
        "partial_selection_permitted": False,
    })
    return packet


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="SCDMP-TBOV r07 Stage-A-only selector")
    value.add_argument("--mode", choices=("preactivity", "production"), default="preactivity")
    value.add_argument("--output", type=Path)
    value.add_argument("--frontier", type=Path)
    value.add_argument("--manifest-root", type=Path)
    value.add_argument("--lease", type=Path)
    value.add_argument("--resume", action="store_true")
    value.add_argument("--microbatch-examples", type=int, default=2_048)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.mode == "preactivity":
        payload = static_conformance()
        if args.output is None:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_json(args.output, payload)
        return 0 if payload["conforming"] else 2
    required = {"output": args.output, "frontier": args.frontier,
                "manifest_root": args.manifest_root, "lease": args.lease}
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"production requires: {', '.join(missing)}")
    try:
        lock_path = Path(str(args.frontier.resolve()) + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as error:
            raise RuntimeError(f"another or unreconciled r07 production owner holds {lock_path}") from error
        try:
            os.write(descriptor, f"pid={os.getpid()} started_ns={time.time_ns()}\n".encode("ascii"))
            os.fsync(descriptor)
            production(
                output=args.output, frontier_path=args.frontier,
                manifest_root=args.manifest_root, lease_path=args.lease,
                resume=args.resume, microbatch_examples=args.microbatch_examples,
            )
        finally:
            os.close(descriptor)
            lock_path.unlink(missing_ok=True)
    except Exception:
        traceback.print_exc()
        return 1
    return 0
