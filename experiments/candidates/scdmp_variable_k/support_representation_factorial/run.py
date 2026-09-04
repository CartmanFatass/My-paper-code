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

from .accounting import complete_count_accounting, final_prefix_n10, train_cell_examples
from .config import (
    BASE_CARD_SHA256,
    BRANCHES,
    CANDIDATE,
    CELLS,
    COUNT_CORRECTION_SHA256,
    DIRECT_PANEL_EXPECTED_EXAMPLES,
    DIRECT_PANEL_MAX_EXAMPLES,
    DIRECT_PANEL_MIN_EXAMPLES,
    DOMAIN_LABELS,
    HMAC_SEED_NAMESPACE,
    HISTORICAL_SUPERSEDED_COST,
    LOGICAL_STEPS,
    MODEL_PARAMETER_COUNTS,
    PROSPECTIVE_COST,
    PRO_CLOSED_INTAKE_SHA256,
    RESULT_OBJECT,
    REVISION,
    SEED_INDICES,
    static_contract,
)
from .corpus import materialize_seed, output_scales, seed_manifest
from .evaluation import evaluate_cell
from .frontier import atomic_save as save_frontier
from .frontier import load as load_frontier
from .frontier import model_state
from .inference import complete_inference
from .lifecycle import Lifecycle
from .model import SegmentModel, initialized_representation_pair, model_state_digest
from .result import _json_safe, complete_packet
from .rng import HMACStream, identity_digests, manifest_digests, sample_fresh_master
from .training import ExactAdamW, MinibatchPlan, SegmentStore, train_checkpoint


def _write_json_temporary(path: Path, value: object) -> Path:
    temporary = Path(str(path.resolve()) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    return temporary


def _atomic_replace_json(path: Path, value: object) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _write_json_temporary(target, value)
    os.replace(temporary, target)


def _atomic_create_json(path: Path, value: object) -> None:
    """Publish JSON atomically without replacing an existing target."""
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _write_json_temporary(target, value)
    try:
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def static_conformance() -> dict[str, object]:
    owner_root = Path(__file__).resolve().parents[4] / (
        "docs/research/candidates/semigroup_consistent_duration_model_policy"
    )
    card_path = owner_root / (
        "SCDMP_TBOV_SUPPORT_REPRESENTATION_FACTORIAL_CHECKPOINT_SCIENCE_CARD_20260819.md"
    )
    correction_path = owner_root / (
        "SCDMP_TBOV_SRF_CHECKPOINT_COUNT_SEMANTICS_CORRECTION_REVISION_03_20260820.md"
    )
    pro_closed_path = owner_root / (
        "SCDMP_TBOV_SRF_CHECKPOINT_R03_CHATGPT_PRO_CLOSED_INTAKE_20260820.md"
    )
    actual_card_sha256 = hashlib.sha256(
        card_path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
    actual_correction_sha256 = hashlib.sha256(
        correction_path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
    actual_pro_closed_sha256 = hashlib.sha256(
        pro_closed_path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
    required_labels = {
        "train/S0/state", "train/S0/word_cells", "train/S0/action",
        "train/S1/word_action", "eval/fit_support/state",
        "eval/fit_support/word_cells", "eval/fit_support/action",
        "init/shared", "init/R0_input", "init/R1_context", "init/R1_input",
        "minibatch/S0", "minibatch/S1",
    }
    checks = {
        "candidate_exact": CANDIDATE
            == "SCDMP-TBOV-SUPPORT-REPRESENTATION-FACTORIAL-CHECKPOINT",
        "result_object_exact": RESULT_OBJECT == "SCDMP-TBOV-SRF-R02-FULL-FACTORIAL",
        "revision_exact": REVISION == "SCDMP-TBOV-SRF-CHECKPOINT-SCIENCE-20260820-03",
        "base_card_sha256_exact": actual_card_sha256 == BASE_CARD_SHA256,
        "count_correction_sha256_exact":
            actual_correction_sha256 == COUNT_CORRECTION_SHA256,
        "pro_closed_intake_sha256_exact":
            actual_pro_closed_sha256 == PRO_CLOSED_INTAKE_SHA256,
        "hmac_namespace_exact": HMAC_SEED_NAMESPACE
            == b"SCDMP-TBOV-SRF-CHECKPOINT-r02/seed/",
        "domain_labels_complete": required_labels.issubset(DOMAIN_LABELS)
            and len(DOMAIN_LABELS) == 37,
        "ten_paired_seed_blocks": SEED_INDICES == tuple(range(10)),
        "four_cells_exact": CELLS == ("S0R0", "S1R0", "S0R1", "S1R1"),
        "model_parameter_specs_exact": MODEL_PARAMETER_COUNTS
            == {"R0": 97_706, "R1": 101_258},
        "logical_steps_exact": LOGICAL_STEPS == 600,
        "eight_first_true_branches_exact": len(BRANCHES) == 8,
        "r03_expected_direct_accounting_exact":
            DIRECT_PANEL_EXPECTED_EXAMPLES == 204_697_600,
        "r03_realized_range_exact":
            (DIRECT_PANEL_MIN_EXAMPLES, DIRECT_PANEL_MAX_EXAMPLES)
            == (202_854_400, 206_540_800),
        "train_cell_formula_exact":
            train_cell_examples(0) == 4_945_920
            and train_cell_examples(1_024) == 4_992_000
            and train_cell_examples(2_048) == 5_038_080,
        "expectation_not_executed_equality":
            PROSPECTIVE_COST["expected_equals_realized_asserted"] is False,
        "r02_count_only_historical_superseded":
            HISTORICAL_SUPERSEDED_COST["superseded_executed_example_assertion"]
                == 224_604_160
            and HISTORICAL_SUPERSEDED_COST["active_prospective_cost"] is False,
        "stage_b_absent": True,
    }
    return {
        "artifact_kind": "SCDMP_TBOV_SRF_R03_PREACTIVITY_STATIC_CONFORMANCE",
        "candidate": CANDIDATE,
        "result_object": RESULT_OBJECT,
        "revision": REVISION,
        "checks": checks,
        "conforming": all(checks.values()),
        "scientific_activity_started": False,
        "question_relevant_output_exists": False,
        "master_seed_coordinate_scale_or_parameter_materialized": False,
        "heavy_compute_executed": False,
        "cost_conformance_fact": {
            "prospective_expected_direct_examples": DIRECT_PANEL_EXPECTED_EXAMPLES,
            "realized_direct_examples": None,
            "realized_formula": "202_854_400 + 90*sum_n10",
            "lattice_step": 90,
            "range": [DIRECT_PANEL_MIN_EXAMPLES, DIRECT_PANEL_MAX_EXAMPLES],
            "expectation_is_not_executed_equality": True,
            "partial_count_output_permitted": False,
            "superseded_r02_assertion": dict(HISTORICAL_SUPERSEDED_COST),
        },
        "resource_recalculation": {
            "expected_direct_example_delta_from_superseded_r02": -19_906_560,
            "expected_direct_example_reduction_percent": 8.86295249384517,
            "checkpoint_count": 40,
            "logical_adamw_steps": 24_000,
            "resource_class": "formal_cpu_heavy_unchanged",
        },
        "static_contract": static_contract(),
        "science_composite": [str(card_path), str(correction_path)],
        "pro_closed_intake": str(pro_closed_path),
        "production_module":
            "experiments.candidates.scdmp_variable_k.support_representation_factorial",
    }


def _validate_lease(path: Path, result_root: Path) -> dict[str, object]:
    lease = json.loads(path.resolve().read_text(encoding="utf-8"))
    try:
        not_after = datetime.fromisoformat(
            str(lease.get("not_after_utc", "")).replace("Z", "+00:00"),
        )
        unexpired = not_after.tzinfo is not None and not_after > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        unexpired = False
    checks = {
        "lease_kind": lease.get("lease_kind")
            == "SCDMP_TBOV_SRF_R03_ROOT_COMPUTE_LEASE",
        "issued_by": lease.get("issued_by") == "operational_root",
        "lease_id": isinstance(lease.get("lease_id"), str)
            and bool(str(lease.get("lease_id"))),
        "direction": lease.get("direction")
            == "semigroup_consistent_duration_model_policy",
        "candidate": lease.get("candidate") == CANDIDATE,
        "result_object": lease.get("result_object") == RESULT_OBJECT,
        "revision": lease.get("revision") == REVISION,
        "production_authorized": lease.get("production_authorized") is True,
        "scientific_activity_authorized":
            lease.get("scientific_activity_authorized") is True,
        "not_revoked": lease.get("revoked", False) is False,
        "authorized_seeds": lease.get("authorized_seeds") == list(SEED_INDICES),
        "authorized_cells": lease.get("authorized_cells") == list(CELLS),
        "max_workers": int(lease.get("max_workers", 0)) == 1,
        "cpu_cores": int(lease.get("cpu_cores", 0)) >= 1,
        "gpu_count": int(lease.get("gpu_count", -1)) == 0,
        "unexpired": unexpired,
        "result_root": Path(str(lease.get("result_root"))).resolve()
            == result_root.resolve(),
        "stage_boundary": lease.get("stage_boundary") == RESULT_OBJECT,
        "stage_b_not_authorized": lease.get("stage_b_authorized") is False,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Root lease does not authorize exact SRF r03 production: {checks}")
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


def _new_frontier(
    master: bytes, lifecycle: Lifecycle, microbatch_examples: int,
) -> dict[str, object]:
    panel_digest, seed_digests = identity_digests(master)
    return {
        "candidate": CANDIDATE,
        "result_object": RESULT_OBJECT,
        "revision": REVISION,
        "partial_inspection_permitted": False,
        "master_M_hex_sealed": master.hex(),
        "panel_digest": panel_digest,
        "seed_digests": list(seed_digests),
        "manifest": None,
        "next_packet_index": 0,
        "active_cell": None,
        "cell_packets": [],
        "cell_packet_digests": [],
        "training_direct_example_counters": {},
        "checkpoint_states": {},
        "lifecycle": lifecycle.facts(),
        "implementation_facts": _implementation_facts(microbatch_examples),
    }


def _validate_frontier_identity(frontier: dict[str, object]) -> bytes:
    try:
        master = bytes.fromhex(str(frontier["master_M_hex_sealed"]))
    except (KeyError, ValueError) as error:
        raise RuntimeError("frontier has no valid sealed master") from error
    if len(master) != 32:
        raise RuntimeError("frontier sealed master is not 256 bits")
    panel_digest, seed_digests = identity_digests(master)
    if frontier.get("panel_digest") != panel_digest \
            or frontier.get("seed_digests") != list(seed_digests):
        raise RuntimeError("frontier master and public identity digests disagree")
    return master


def _validate_bound_manifest(frontier: dict[str, object], master: bytes) -> None:
    manifest = frontier.get("manifest")
    if manifest is None:
        return
    panel_digest, seed_digests = identity_digests(master)
    checks = {
        "kind": isinstance(manifest, dict)
            and manifest.get("artifact_kind")
            == "SCDMP_TBOV_SRF_R03_CREATE_ONLY_BLINDED_MANIFEST",
        "candidate": isinstance(manifest, dict) and manifest.get("candidate") == CANDIDATE,
        "result_object": isinstance(manifest, dict)
            and manifest.get("result_object") == RESULT_OBJECT,
        "revision": isinstance(manifest, dict) and manifest.get("revision") == REVISION,
        "panel_digest": isinstance(manifest, dict)
            and manifest.get("panel_digest") == panel_digest,
        "seed_digests": isinstance(manifest, dict)
            and manifest.get("seed_digests") == list(seed_digests),
        "per_seed": isinstance(manifest, dict)
            and isinstance(manifest.get("per_seed"), list)
            and len(manifest["per_seed"]) == 10,
    }
    if not all(checks.values()):
        raise RuntimeError(f"frontier manifest identity mismatch: {checks}")


def _cell_packet_digest(packet: dict[str, object]) -> str:
    encoded = json.dumps(
        packet, sort_keys=True, separators=(",", ":"), allow_nan=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_cell_packet_frontier(frontier: dict[str, object]) -> None:
    packets = frontier.get("cell_packets")
    digests = frontier.get("cell_packet_digests")
    counters = frontier.get("training_direct_example_counters")
    if not isinstance(packets, list) or not isinstance(digests, list) \
            or not isinstance(counters, dict) \
            or len(packets) != len(digests) \
            or int(frontier.get("next_packet_index", -1)) != len(packets):
        raise RuntimeError("blinded cell-packet frontier shape mismatch")
    completed_keys = {
        f"{int(packet['seed_index'])}:{str(packet['cell'])}" for packet in packets
    }
    if set(counters) != completed_keys or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in counters.values()
    ):
        raise RuntimeError("internal direct-example counters do not match completed cells")
    actual = [_cell_packet_digest(packet) for packet in packets]
    if actual != digests:
        raise RuntimeError("a create-only blinded cell packet changed after installation")


def _checkpoint_state_digest(state: object) -> str | None:
    if not isinstance(state, dict):
        return None
    digest = hashlib.sha256()
    for name, value in state.items():
        if not isinstance(name, str) or not isinstance(value, torch.Tensor):
            return None
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _representation_models(
    master: bytes, seed_index: int,
) -> tuple[dict[str, SegmentModel], dict[str, object]]:
    return initialized_representation_pair(
        HMACStream.for_domain(master, seed_index, "init/shared"),
        HMACStream.for_domain(master, seed_index, "init/R0_input"),
        HMACStream.for_domain(master, seed_index, "init/R1_context"),
        HMACStream.for_domain(master, seed_index, "init/R1_input"),
    )


def _minibatch_plans(
    master: bytes, seed_index: int,
) -> dict[str, MinibatchPlan]:
    return {
        support: MinibatchPlan(
            HMACStream.for_domain(master, seed_index, f"minibatch/{support}"),
        )
        for support in ("S0", "S1")
    }


def _derive_complete_count_accounting(
    master: bytes, frontier: dict[str, object],
) -> dict[str, object]:
    executed = frontier.get("training_direct_example_counters")
    if not isinstance(executed, dict):
        raise RuntimeError("complete frontier lacks internal direct-training counters")
    n10_by_seed_support: dict[str, int] = {}
    for seed_index in SEED_INDICES:
        corpus = materialize_seed(master, seed_index)
        plans = _minibatch_plans(master, seed_index)
        for support in ("S0", "S1"):
            n10_by_seed_support[f"{seed_index}:{support}"] = final_prefix_n10(
                corpus.train[support], plans[support],
            )
    return complete_count_accounting(n10_by_seed_support, executed)


def _build_manifest(
    master: bytes,
    manifest_root: Path,
    before_boundary: Callable[[], None] | None = None,
) -> dict[str, object]:
    per_seed: list[dict[str, object]] = []
    for seed_index in SEED_INDICES:
        if before_boundary is not None:
            before_boundary()
        corpus = materialize_seed(master, seed_index)
        models, initialization = _representation_models(master, seed_index)
        plans = _minibatch_plans(master, seed_index)
        if model_state_digest(models["S0R0"]) != model_state_digest(models["S1R0"]) \
                or model_state_digest(models["S0R1"]) != model_state_digest(models["S1R1"]):
            raise RuntimeError("support-level initialized models are not byte-identical clones")
        per_seed.append(seed_manifest(
            master,
            corpus,
            initialization,
            {f"minibatch/{support}": plan.draw_count for support, plan in plans.items()},
        ))
    panel_digest, seed_digests = identity_digests(master)
    manifest = {
        "artifact_kind": "SCDMP_TBOV_SRF_R03_CREATE_ONLY_BLINDED_MANIFEST",
        "candidate": CANDIDATE,
        "result_object": RESULT_OBJECT,
        "revision": REVISION,
        "panel_digest": panel_digest,
        "seed_digests": list(seed_digests),
        "hmac_seed_namespace": HMAC_SEED_NAMESPACE.decode("ascii"),
        "domain_labels": list(DOMAIN_LABELS),
        "per_seed": per_seed,
        "raw_master_present": False,
        "raw_coordinates_present": False,
        "partial_effects_present": False,
    }
    path = manifest_root.resolve() / f"{panel_digest}.json"
    if before_boundary is not None:
        before_boundary()
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != manifest:
            raise RuntimeError("existing SRF create-only manifest differs from reconstruction")
    else:
        _atomic_create_json(path, manifest)
    return {**manifest, "path": str(path)}


def _reconcile_installed_result(
    output: Path,
    frontier_path: Path,
    installed: dict[str, object],
    before_update: Callable[[], None] | None = None,
) -> dict[str, object]:
    output, frontier_path = output.resolve(), frontier_path.resolve()
    sidecar_path = Path(str(output) + ".activity.json").resolve()
    if not frontier_path.exists():
        raise RuntimeError("installed SRF result lacks its retained atomic frontier")
    retained = load_frontier(frontier_path)
    master = _validate_frontier_identity(retained)
    _validate_bound_manifest(retained, master)
    _validate_cell_packet_frontier(retained)
    manifest = installed.get("manifest")
    retained_packets = retained.get("cell_packets")
    retained_checkpoints = retained.get("checkpoint_states")
    expected_identities = [
        (seed_index, cell) for seed_index in SEED_INDICES for cell in CELLS
    ]
    retained_identities = [
        (int(packet.get("seed_index", -1)), str(packet.get("cell", "")))
        for packet in retained_packets
    ] if isinstance(retained_packets, list) else []
    expected_checkpoint_keys = {
        f"{seed_index}:{cell}" for seed_index, cell in expected_identities
    }
    checkpoint_digests_match = False
    if isinstance(retained_packets, list) and isinstance(retained_checkpoints, dict) \
            and set(retained_checkpoints) == expected_checkpoint_keys:
        checkpoint_digests_match = all(
            _checkpoint_state_digest(retained_checkpoints.get(f"{seed_index}:{cell}"))
            == packet.get("checkpoint_digest")
            for (seed_index, cell), packet in zip(retained_identities, retained_packets)
        )
    safe_retained_packets, _packet_nonfinite = _json_safe(
        retained_packets, "$.cell_packets",
    )
    exact_retained_packet_set = isinstance(retained_packets, list) \
        and len(retained_packets) == 40 \
        and retained_identities == expected_identities
    recomputed_inference = complete_inference(retained_packets) \
        if exact_retained_packet_set else {}
    safe_recomputed_inference, _inference_nonfinite = _json_safe(
        recomputed_inference, "$.inference",
    )
    recomputed_count_accounting = _derive_complete_count_accounting(master, retained) \
        if exact_retained_packet_set else {}
    installed_lifecycle = installed.get("lifecycle")
    retained_lifecycle = retained.get("lifecycle")
    retained_events = retained_lifecycle.get("events") \
        if isinstance(retained_lifecycle, dict) else None
    installed_events = installed_lifecycle.get("events") \
        if isinstance(installed_lifecycle, dict) else None
    terminal_event = installed_events[-1] \
        if isinstance(installed_events, list) and installed_events else None
    promotion_lifecycle_provenance = isinstance(retained_events, list) \
        and isinstance(installed_events, list) \
        and len(installed_events) == len(retained_events) + 1 \
        and installed_events[:-1] == retained_events \
        and isinstance(terminal_event, dict) \
        and set(terminal_event) == {"event", "utc"} \
        and terminal_event.get("event") \
            == "complete_atomic_four_cell_ten_seed_packet" \
        and isinstance(terminal_event.get("utc"), str) \
        and bool(terminal_event.get("utc"))
    promotion_lifecycle_window = isinstance(retained_lifecycle, dict) \
        and retained_lifecycle.get("phase") == "blinded_cell_evaluation" \
        and retained_lifecycle.get("scientific_activity_started") is True \
        and retained_lifecycle.get("question_relevant_output_exists") is False
    already_finalized = isinstance(retained_lifecycle, dict) \
        and retained_lifecycle == installed_lifecycle \
        and retained_lifecycle.get("phase") == "complete" \
        and retained_lifecycle.get("scientific_activity_started") is True \
        and retained_lifecycle.get("question_relevant_output_exists") is True \
        and retained.get("question_relevant_output_exists") is True \
        and retained.get("final_result") == str(output)
    try:
        revealed = bytes.fromhex(str(installed.get(
            "master_M_hex_revealed_only_in_complete_result",
        )))
    except ValueError:
        revealed = b""
    panel_digest, seed_digests = identity_digests(master)
    checks = {
        "artifact_kind": installed.get("artifact_kind")
            == "SCDMP_TBOV_SRF_R03_COMPLETE_FACTORIAL_RESULT",
        "candidate": installed.get("candidate") == CANDIDATE,
        "result_object": installed.get("result_object") == RESULT_OBJECT,
        "revision": installed.get("revision") == REVISION,
        "complete_atomic_panel": installed.get("complete") is True
            and installed.get("scientific_activity_started") is True
            and installed.get("question_relevant_output_exists") is True
            and installed.get("partial_inspection_permitted") is False,
        "retained_complete_inactive_panel": retained.get("active_cell") is None
            and retained.get("next_packet_index") == 40
            and exact_retained_packet_set,
        "lifecycle_provenance": already_finalized or (
            promotion_lifecycle_window and promotion_lifecycle_provenance
        ),
        "retained_checkpoint_set": isinstance(retained_checkpoints, dict)
            and len(retained_checkpoints) == 40
            and set(retained_checkpoints) == expected_checkpoint_keys
            and checkpoint_digests_match,
        "installed_packets_equal_retained":
            installed.get("cell_packets") == safe_retained_packets,
        "retained_frontier": installed.get("retained_frontier") == str(frontier_path),
        "activity_sidecar": installed.get("activity_sidecar") == str(sidecar_path),
        "master": revealed == master,
        "manifest": isinstance(manifest, dict)
            and manifest == retained.get("manifest")
            and manifest.get("panel_digest") == panel_digest
            and manifest.get("seed_digests") == list(seed_digests),
        "inference": installed.get("inference") == safe_recomputed_inference
            and installed.get("selected_branch") == recomputed_inference.get("branch")
            and installed.get("competence_modifier")
                == recomputed_inference.get("competence_modifier"),
        "count_accounting":
            installed.get("count_accounting") == recomputed_count_accounting,
        "installed_complete_lifecycle": isinstance(installed_lifecycle, dict)
            and installed_lifecycle.get("phase") == "complete"
            and installed_lifecycle.get("scientific_activity_started") is True
            and installed_lifecycle.get("question_relevant_output_exists") is True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"installed SRF result/frontier identity mismatch: {checks}")
    if before_update is not None:
        before_update()
    retained["final_result"] = str(output)
    retained["question_relevant_output_exists"] = True
    retained["lifecycle"] = installed["lifecycle"]
    save_frontier(frontier_path, retained)
    if before_update is not None:
        before_update()
    _atomic_replace_json(sidecar_path, {
        "candidate": CANDIDATE,
        "result_object": RESULT_OBJECT,
        "revision": REVISION,
        "lifecycle": installed["lifecycle"],
        "scientific_activity_started": True,
        "activity_pending": False,
        "identity_pending_crossed_boundary": False,
        "final_result_installed": True,
        "result": str(output),
        "frontier": str(frontier_path),
        "partial_inspection_permitted": False,
    })
    return installed


def production(
    *,
    output: Path,
    frontier_path: Path,
    manifest_root: Path,
    lease_path: Path,
    resume: bool,
    microbatch_examples: int = 2_048,
) -> dict[str, object]:
    output = output.resolve()
    frontier_path = frontier_path.resolve()
    manifest_root = manifest_root.resolve()
    result_root = output.parent.resolve()
    sidecar_path = Path(str(output) + ".activity.json").resolve()
    if microbatch_examples <= 0:
        raise ValueError("physical microbatch size must be positive")
    if len({output, frontier_path, sidecar_path}) != 3:
        raise ValueError("result, frontier and activity-sidecar paths must be distinct")
    _validate_lease(lease_path, result_root)

    if output.exists():
        installed = json.loads(output.read_text(encoding="utf-8"))
        _validate_lease(lease_path, result_root)
        return _reconcile_installed_result(
            output,
            frontier_path,
            installed,
            before_update=lambda: _validate_lease(lease_path, result_root),
        )

    if frontier_path.exists():
        if not resume:
            raise FileExistsError("SRF frontier exists; explicit --resume is required")
        frontier = load_frontier(frontier_path)
        master = _validate_frontier_identity(frontier)
        _validate_bound_manifest(frontier, master)
        _validate_cell_packet_frontier(frontier)
        lifecycle = Lifecycle.from_facts(frontier["lifecycle"])
        frozen_microbatch = int(frontier["implementation_facts"]["microbatch_examples"])
        if microbatch_examples != frozen_microbatch:
            raise RuntimeError(
                "same-coordinate continuation must retain the initial physical microbatch size"
            )
    else:
        if resume:
            raise FileNotFoundError("--resume requested but no SRF frontier exists")
        if sidecar_path.exists():
            prior_sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            prior_lifecycle = prior_sidecar.get("lifecycle")
            safe_preactivity_sidecar = isinstance(prior_lifecycle, dict) \
                and prior_lifecycle.get("scientific_activity_started") is False \
                and prior_sidecar.get("scientific_activity_started", False) is False \
                and prior_sidecar.get("identity_pending_crossed_boundary", False) is False
            if not safe_preactivity_sidecar:
                raise RuntimeError(
                    "sidecar does not durably prove preactivity while its sealed frontier is absent"
                )
        lifecycle = Lifecycle()
        _atomic_replace_json(sidecar_path, {
            "candidate": CANDIDATE,
            "result_object": RESULT_OBJECT,
            "revision": REVISION,
            "lifecycle": lifecycle.facts(),
            "scientific_activity_started": False,
            "activity_pending": True,
            "identity_pending_crossed_boundary": False,
            "final_result_installed": False,
            "partial_inspection_permitted": False,
        })
        _validate_lease(lease_path, result_root)
        occupied_identities = manifest_digests(manifest_root)
        lifecycle.begin_panel()
        _atomic_replace_json(sidecar_path, {
            "candidate": CANDIDATE,
            "result_object": RESULT_OBJECT,
            "revision": REVISION,
            "lifecycle": lifecycle.facts(),
            "scientific_activity_started": True,
            "activity_pending": True,
            "identity_pending_crossed_boundary": True,
            "final_result_installed": False,
            "partial_inspection_permitted": False,
        })
        master = sample_fresh_master(occupied_identities)
        frontier = _new_frontier(master, lifecycle, microbatch_examples)
        save_frontier(frontier_path, frontier)
        _atomic_replace_json(sidecar_path, {
            "candidate": CANDIDATE,
            "result_object": RESULT_OBJECT,
            "revision": REVISION,
            "lifecycle": lifecycle.facts(),
            "scientific_activity_started": True,
            "activity_pending": False,
            "identity_pending_crossed_boundary": False,
            "final_result_installed": False,
            "partial_inspection_permitted": False,
        })

    if frontier["manifest"] is None:
        frontier["manifest"] = _build_manifest(
            master,
            manifest_root,
            before_boundary=lambda: _validate_lease(lease_path, result_root),
        )
        lifecycle.record("complete_create_only_blinded_manifest")
        frontier["lifecycle"] = lifecycle.facts()
        save_frontier(frontier_path, frontier)

    _validate_bound_manifest(frontier, master)
    _validate_cell_packet_frontier(frontier)

    expected_packets = [(seed_index, cell) for seed_index in SEED_INDICES for cell in CELLS]
    for packet_index in range(int(frontier["next_packet_index"]), len(expected_packets)):
        seed_index, cell = expected_packets[packet_index]
        _validate_lease(lease_path, result_root)
        corpus = materialize_seed(master, seed_index)
        models, _initialization = _representation_models(master, seed_index)
        plans = _minibatch_plans(master, seed_index)
        support = cell[:2]
        model = models[cell]
        scale_f, scale_g = output_scales(corpus.train[support])
        optimizer = ExactAdamW(model)
        active = frontier.get("active_cell")
        if isinstance(active, dict):
            if int(active["packet_index"]) != packet_index \
                    or int(active["seed_index"]) != seed_index \
                    or str(active["cell"]) != cell:
                raise RuntimeError("active frontier cell does not match the next atomic packet")
            model.load_state_dict(active["model_state"])
            optimizer.load_state_dict(active["optimizer_state"])
            first_step = int(active["next_step"])
            executed_direct_examples = int(active["training_direct_examples"])
        else:
            first_step = 1
            executed_direct_examples = 0
        lifecycle.begin_training(seed_index, cell)
        last_complete_step_facts = active.get("last_complete_step_facts") \
            if isinstance(active, dict) else None

        def persist_active(next_step: int, executed: int) -> None:
            active_value: dict[str, object] = {
                "packet_index": packet_index,
                "seed_index": seed_index,
                "cell": cell,
                "next_step": next_step,
                "training_direct_examples": executed,
                "model_state": model_state(model),
                "optimizer_state": optimizer.state_dict(),
            }
            if last_complete_step_facts is not None:
                active_value["last_complete_step_facts"] = last_complete_step_facts
            frontier["active_cell"] = active_value
            frontier["lifecycle"] = lifecycle.facts()
            save_frontier(frontier_path, frontier)

        def before_step(n: int) -> None:
            try:
                _validate_lease(lease_path, result_root)
            except Exception:
                persist_active(n, executed_direct_examples)
                raise

        def persist_step(
            n: int,
            current_model: SegmentModel,
            current_optimizer: ExactAdamW,
            loss: float,
            norm: float,
            executed: int,
        ) -> None:
            del current_model, current_optimizer
            nonlocal last_complete_step_facts, executed_direct_examples
            executed_direct_examples = executed
            last_complete_step_facts = {
                "n": n,
                "loss": loss,
                "preclip_gradient_norm": norm,
            }
            if n % 25 == 0 or n == LOGICAL_STEPS:
                persist_active(n + 1, executed)

        store = SegmentStore(corpus.train[support])
        _trace, executed_direct_examples = train_checkpoint(
            model,
            optimizer,
            plans[support],
            store,
            scale_f,
            scale_g,
            first_step=first_step,
            initial_direct_examples=executed_direct_examples,
            before_step=before_step,
            on_step=persist_step,
            microbatch_examples=microbatch_examples,
        )
        if optimizer.step_number != LOGICAL_STEPS:
            raise RuntimeError("SRF cell checkpoint is not theta_600")
        _validate_lease(lease_path, result_root)
        packet = evaluate_cell(
            model,
            corpus,
            cell,
            scale_f,
            scale_g,
        )
        _validate_lease(lease_path, result_root)
        frontier["cell_packets"].append(packet)
        frontier["cell_packet_digests"].append(_cell_packet_digest(packet))
        frontier["training_direct_example_counters"][
            f"{seed_index}:{cell}"
        ] = executed_direct_examples
        frontier["checkpoint_states"][f"{seed_index}:{cell}"] = model_state(model)
        frontier["next_packet_index"] = packet_index + 1
        frontier["active_cell"] = None
        lifecycle.complete_cell(seed_index, cell)
        frontier["lifecycle"] = lifecycle.facts()
        save_frontier(frontier_path, frontier)

    _validate_lease(lease_path, result_root)
    count_accounting = _derive_complete_count_accounting(master, frontier)
    inference = complete_inference(frontier["cell_packets"])
    lifecycle.complete()
    packet = complete_packet(
        master_hex=master.hex(),
        manifest=frontier["manifest"],
        cell_packets=frontier["cell_packets"],
        inference=inference,
        count_accounting=count_accounting,
        lifecycle=lifecycle.facts(),
        frontier_path=str(frontier_path),
        activity_sidecar=str(sidecar_path),
        implementation_facts=frontier["implementation_facts"],
    )
    _validate_lease(lease_path, result_root)
    _atomic_create_json(output, packet)
    _validate_lease(lease_path, result_root)
    frontier["lifecycle"] = lifecycle.facts()
    frontier["final_result"] = str(output)
    frontier["question_relevant_output_exists"] = True
    save_frontier(frontier_path, frontier)
    _atomic_replace_json(sidecar_path, {
        "candidate": CANDIDATE,
        "result_object": RESULT_OBJECT,
        "revision": REVISION,
        "lifecycle": lifecycle.facts(),
        "scientific_activity_started": True,
        "activity_pending": False,
        "identity_pending_crossed_boundary": False,
        "final_result_installed": True,
        "result": str(output),
        "frontier": str(frontier_path),
        "partial_inspection_permitted": False,
    })
    return packet


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="SCDMP-TBOV SRF r03 isolated four-cell checkpoint factorial",
    )
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
            _atomic_replace_json(args.output, payload)
        return 0 if payload["conforming"] else 2
    required = {
        "output": args.output,
        "frontier": args.frontier,
        "manifest_root": args.manifest_root,
        "lease": args.lease,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"production requires: {', '.join(missing)}")
    try:
        lock_path = Path(str(args.frontier.resolve()) + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as error:
            raise RuntimeError(
                f"another or unreconciled SRF production owner holds {lock_path}",
            ) from error
        try:
            os.write(
                descriptor,
                f"pid={os.getpid()} started_ns={time.time_ns()}\n".encode("ascii"),
            )
            os.fsync(descriptor)
            production(
                output=args.output,
                frontier_path=args.frontier,
                manifest_root=args.manifest_root,
                lease_path=args.lease,
                resume=args.resume,
                microbatch_examples=args.microbatch_examples,
            )
        finally:
            os.close(descriptor)
            lock_path.unlink(missing_ok=True)
    except Exception:
        traceback.print_exc()
        return 1
    return 0
