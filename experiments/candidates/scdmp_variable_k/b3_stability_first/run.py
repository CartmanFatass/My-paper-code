from __future__ import annotations

import os

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
              "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
import copy
import json
import sys
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from .config import (
    ALGORITHM_SEEDS, ARMS, CALIBRATION_AUXILIARY_FORWARD_TOTAL,
    CALIBRATION_AUXILIARY_GRADIENT_TOTAL, CALIBRATION_ENDPOINT_FORWARD_TOTAL,
    CALIBRATION_ENDPOINT_GRADIENT_TOTAL, CANDIDATE, DHOM_FORWARD_TOTAL,
    FACTOR_TRANSITIONS_PER_PANEL_KIND, MICROSTEP_LEDGER, MICROSTEP_TOTAL,
    FRONTIER_UPDATE_INTERVAL, MODEL_PARAMETER_COUNT, NUMPY_VERSION, OPTIMIZER_UPDATES, ORDERED_PARAMETER_NAMES,
    PHYSICAL_FULL_JOINT_TOTAL, RESOURCES, REVISION, TORCH_VERSION,
    TRAINING_AUXILIARY_GRADIENT_TOTAL, TRAINING_ENDPOINT_GRADIENT_TOTAL,
    TRAINING_FORWARD_TOTAL, TREATMENT_FORWARD_TOTAL,
)
from .manifest import complete_coordinate_manifest

BoundaryT = TypeVar("BoundaryT")


class CorpusCache:
    """Materialize each seed corpus at most once in one process slice."""

    def __init__(self, builder: Callable[[int], object]) -> None:
        self._builder = builder
        self._values: dict[int, object] = {}
        self.build_counts: dict[int, int] = {}

    def get(self, seed: int):
        if seed not in ALGORITHM_SEEDS:
            raise ValueError(f"B3 seed outside frozen block: {seed}")
        if seed not in self._values:
            self._values[seed] = self._builder(seed)
            self.build_counts[seed] = self.build_counts.get(seed, 0) + 1
        return self._values[seed]


def credit_seed_ledger(ledger: dict[str, int], *, corpus_microsteps: int,
                       audit_ledger: dict[str, int], scored_steps: int) -> None:
    expected = {"common_training_corpus": 12_288, "three_arm_scored": 138_240,
                "common_audit_warmup": 3_072, "audit_target_words": 46_656,
                "audit_reverse_twins": 46_656}
    observed = {"common_training_corpus": corpus_microsteps,
                "three_arm_scored": scored_steps, **audit_ledger}
    if observed != expected:
        raise RuntimeError(f"B3 per-seed analytic ledger mismatch: {observed}")
    for name, value in observed.items():
        ledger[name] += value


def _atomic_json(path: Path, value: object) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _write_fresh_json(path: Path, value: object) -> None:
    if path.resolve().exists():
        raise FileExistsError(f"refusing to overwrite B3 artifact: {path.resolve()}")
    _atomic_json(path, value)


def reconcile_installed_result(output: Path, frontier_path: Path,
                               installed: dict[str, object],
                               frontier: dict[str, object] | None = None) -> dict[str, object]:
    """Idempotently finish both durable locators after atomic result installation."""
    from .frontier import atomic_save, load

    output, frontier_path = output.resolve(), frontier_path.resolve()
    sidecar = Path(str(output) + ".activity.json").resolve()
    if installed.get("candidate") != CANDIDATE or installed.get("revision") != REVISION \
            or installed.get("complete") is not True:
        raise RuntimeError("cannot reconcile a nonterminal or wrong-identity B3 result")
    if Path(str(installed.get("retained_frontier"))).resolve() != frontier_path \
            or Path(str(installed.get("activity_sidecar"))).resolve() != sidecar:
        raise RuntimeError("installed B3 result locator mismatch")
    retained = load(frontier_path) if frontier is None else frontier
    lifecycle = installed["lifecycle"]
    retained["phase"] = lifecycle["phase"]
    retained["lifecycle"] = copy.deepcopy(lifecycle)
    retained["final_result"] = str(output)
    retained["question_relevant_output_exists"] = True
    retained["terminal_artifact_kind"] = installed["artifact_kind"]
    retained["finalization"] = {"result": str(output), "sidecar": str(sidecar),
                                "frontier": str(frontier_path), "reconciled": True}
    atomic_save(frontier_path, retained)
    _atomic_json(sidecar, {"artifact_kind": "SCDMP_B3_ACTIVITY_SIDECAR",
        "candidate": CANDIDATE, "revision": REVISION, "result_path": str(output),
        "frontier_path": str(frontier_path), "lifecycle": lifecycle,
        "final_result_installed": True, "terminal_artifact_kind": installed["artifact_kind"],
        "partial_selection_permitted": False})
    return installed


def static_conformance() -> dict[str, object]:
    checks = {
        "revision_exact": REVISION == "SCDMP-B3-SCIENCE-20260814-01",
        "candidate_exact": CANDIDATE == "SCDMP-B3-STABILITY-FIRST-RELATION-SPECIFICITY",
        "arms_exact": ARMS == ("FREE-DIRECT", "SCDMP-CORRECT", "SCDMP-ORDER-SHUFFLE"),
        "fresh_seeds_exact": ALGORITHM_SEEDS == tuple(range(200, 208)),
        "ordered_parameters_exact_24": len(ORDERED_PARAMETER_NAMES) == 24
            and len(set(ORDERED_PARAMETER_NAMES)) == 24,
        "ledger_exact": MICROSTEP_LEDGER == {"common_training_corpus": 98_304,
            "three_arm_scored": 1_105_920, "common_audit_warmup": 24_576,
            "audit_target_words": 373_248, "audit_reverse_twins": 373_248},
        "ledger_total_exact": sum(MICROSTEP_LEDGER.values()) == MICROSTEP_TOTAL == 1_975_296,
        "training_forwards_exact": TRAINING_FORWARD_TOTAL == 216_000,
        "calibration_forwards_exact": CALIBRATION_ENDPOINT_FORWARD_TOTAL == 24
            and CALIBRATION_AUXILIARY_FORWARD_TOTAL == 144
            and TREATMENT_FORWARD_TOTAL == 216_168,
        "gradient_traversals_exact": TRAINING_ENDPOINT_GRADIENT_TOTAL == 24_000
            and TRAINING_AUXILIARY_GRADIENT_TOTAL == 24_000
            and CALIBRATION_ENDPOINT_GRADIENT_TOTAL == 8
            and CALIBRATION_AUXILIARY_GRADIENT_TOTAL == 24,
        "dhom_forwards_exact": DHOM_FORWARD_TOTAL == 144,
        "frontier_interval_exact_coordinate_resume": OPTIMIZER_UPDATES % FRONTIER_UPDATE_INTERVAL == 0,
        "update_major_fixed_arm_schedule": list(update_major_dispatch(0, 1))[0][1]
            == tuple((0, arm) for arm in ARMS),
        "single_thread_cpu_exact": RESOURCES.cpu_workers == 1 and not RESOURCES.gpu_allowed,
    }
    return {"checks": checks, "conforming": all(checks.values()),
            "science_card": "docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B3_STABILITY_FIRST_SCIENCE_CARD.md",
            "owner_intake": "docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B3_CHATGPT_PRO_CLOSED_OWNER_INTAKE.md",
            "production_command_module": "experiments.candidates.scdmp_variable_k.b3_stability_first"}


def preactivity_certificate(seed: int, corpus=None) -> dict[str, object]:
    """Structural checks only: no loss, gradient, support value, or evaluation statistic."""
    from .corpus import LockedBatchPlan, build_corpus, structural_certificate, support_certificate
    from .model import SCDMPModel
    from .relations import homogeneous_relation_certificate
    from .training import model_state_digest, ordered_parameters

    corpus = build_corpus(seed) if corpus is None else corpus
    structural = structural_certificate(corpus)
    relation = homogeneous_relation_certificate(
        [row for bank in ("C_22", "C_44") for row in corpus.banks[bank]])
    locked = support_certificate(corpus, LockedBatchPlan(corpus, seed).batch_for_update(0))
    models = [SCDMPModel(seed) for _ in ARMS]
    digests = [model_state_digest(model) for model in models]
    shapes = [[name, list(parameter.shape)] for name, parameter in models[0].named_parameters()]
    checks = {"corpus_structure": structural["conforming"],
              "homogeneous_relation_identity": relation["conforming"],
              "locked_update_zero_shape_support": locked["conforming"],
              "initialized_arm_tensors_byte_identical": len(set(digests)) == 1,
              "ordered_parameter_tuple": all(len(ordered_parameters(model)) == 24 for model in models),
              "parameter_count": sum(p.numel() for p in models[0].parameters()) == MODEL_PARAMETER_COUNT}
    return {"algorithm_seed": seed, "checks": checks, "conforming": all(checks.values()),
            "structural_certificate": structural, "homogeneous_relation_certificate": relation,
            "locked_update_zero_support_certificate": locked,
            "initial_model_sha256": digests[0], "parameter_shapes": shapes,
            "scientific_activity_started": False}


def prepare_preactivity_certificates(cache: CorpusCache,
                                     certificate: Callable[[int, object], dict[str, object]]
                                     = preactivity_certificate) -> list[dict[str, object]]:
    return [certificate(seed, cache.get(seed)) for seed in ALGORITHM_SEEDS]


def prepare_static(*, structural_seed: int | None = None) -> dict[str, object]:
    result: dict[str, object] = {"artifact_kind": "SCDMP_B3_STATIC",
        "candidate": CANDIDATE, "revision": REVISION, "scientific_activity_started": False,
        "question_relevant_output_exists": False, "static_conformance": static_conformance(),
        "fresh_coordinate_manifest": complete_coordinate_manifest(),
        "registered_resources": {"cpu": 1, "gpu": False},
        "resume_contract": {"atomic_update_interval": FRONTIER_UPDATE_INTERVAL,
            "hard_interruption_replays_only_the_same_locked_coordinates": True,
            "atomic_boundary": "after_complete_three_arm_update",
            "schedule": "update_major_fixed_arm_order",
            "partial_selection_permitted": False},
        "heavy_production_executed": False}
    if structural_seed is not None:
        result["preactivity_certificate"] = preactivity_certificate(structural_seed)
    return result


def _seed_key(seed: int) -> str:
    return str(seed)


def update_major_dispatch(start_update: int, stop_update: int = OPTIMIZER_UPDATES):
    """Yield each update with the exact fixed arm order as one atomic frontier unit."""
    if not 0 <= start_update <= stop_update <= OPTIMIZER_UPDATES:
        raise ValueError("invalid B3 update-major dispatch bounds")
    for update in range(start_update, stop_update):
        yield update, tuple((update, arm) for arm in ARMS)


def execute_update_major_step(update: int, step_arm: Callable[[str], None],
                              commit_boundary: Callable[[int], BoundaryT]) -> BoundaryT:
    """Commit only after all three arm steps for one update return successfully."""
    _, dispatches = next(update_major_dispatch(update, update + 1))
    for dispatched_update, arm in dispatches:
        if dispatched_update != update:
            raise RuntimeError("B3 update-major dispatch coordinate mismatch")
        step_arm(arm)
    return commit_boundary(update + 1)


def _calibration_lookup(rows: list[dict[str, object]], seed: int, arm: str) -> dict[str, object]:
    matched = [row for row in rows if int(row["algorithm_seed"]) == seed and row["arm"] == arm]
    if len(matched) != 1:
        raise RuntimeError(f"expected exactly one calibration for seed={seed} arm={arm}")
    return matched[0]


def production(output: Path, frontier_path: Path, *, resume: bool) -> dict[str, object]:
    import numpy as np
    import torch

    from ..rng import require_numpy_version
    from .audit import analyze_audit
    from .corpus import LockedBatchPlan, build_corpus, structural_certificate
    from .evaluation import evaluate_scored, serialize_scored
    from .frontier import active_seed_snapshot, atomic_save, load, model_state
    from .inference import complete_inference
    from .lifecycle import Lifecycle
    from .model import SCDMPModel
    from .resources import ResourceMonitor
    from .result import complete_packet, invalid_calibration_packet
    from .training import (
        calibrate_seed, checkpoint, initialize_cell, summarize_trace,
        train_support_competence, train_update,
    )

    output, frontier_path = output.resolve(), frontier_path.resolve()
    sidecar = Path(str(output) + ".activity.json")
    if output.exists():
        if resume:
            installed = json.loads(output.read_text(encoding="utf-8"))
            if installed.get("candidate") == CANDIDATE and installed.get("revision") == REVISION \
                    and installed.get("complete") is True:
                return reconcile_installed_result(output, frontier_path, installed)
        raise FileExistsError(f"refusing to overwrite complete B3 output: {output}")
    static = static_conformance()
    if not static["conforming"]:
        raise RuntimeError("B3 static conformance failed")
    require_numpy_version()
    if np.__version__ != NUMPY_VERSION or torch.__version__ != TORCH_VERSION:
        raise RuntimeError(f"version mismatch numpy={np.__version__}, torch={torch.__version__}")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
        raise RuntimeError("B3 one-thread binding failed")
    corpus_cache = CorpusCache(build_corpus)

    if resume:
        if not frontier_path.exists():
            raise FileNotFoundError(f"B3 resume frontier does not exist: {frontier_path}")
        frontier = load(frontier_path)
        if sidecar.exists():
            sidecar_value = json.loads(sidecar.read_text(encoding="utf-8"))
            stored_lifecycle = sidecar_value.get("lifecycle")
            if stored_lifecycle and bool(stored_lifecycle["scientific_activity_started"]):
                frontier["lifecycle"] = stored_lifecycle
    else:
        if frontier_path.exists() or sidecar.exists():
            raise FileExistsError("fresh B3 production requires fresh frontier and sidecar paths")
        preactivity = prepare_preactivity_certificates(corpus_cache)
        if not all(row["conforming"] for row in preactivity):
            raise RuntimeError("B3 preactivity structural conformance failed")
        frontier = {"artifact_kind": "SCDMP_B3_BLINDED_ATOMIC_FRONTIER",
            "candidate": CANDIDATE, "revision": REVISION, "phase": "calibration",
            "partial_selection_permitted": False, "scientific_interpretation": None,
            "lifecycle": {"phase": "preactivity", "scientific_activity_started": False,
                          "question_relevant_output_exists": False, "events": []},
            "fresh_coordinate_manifest": complete_coordinate_manifest(),
            "preactivity_certificates": preactivity, "calibration_table": [],
            "training_schedule": {"major_axis": "update", "arm_order": list(ARMS),
                                  "atomic_boundary": "complete_three_arm_update"},
            "completed_seeds": {}, "active_seed": None, "seed_packets": [],
            "ledger": {name: 0 for name in MICROSTEP_LEDGER}, "resource_slices": [],
            "anomalies": []}
        atomic_save(frontier_path, frontier)

    def persist_activity(facts: dict[str, object]) -> None:
        _atomic_json(sidecar, {"artifact_kind": "SCDMP_B3_ACTIVITY_SIDECAR",
            "candidate": CANDIDATE, "revision": REVISION, "result_path": str(output),
            "frontier_path": str(frontier_path), "lifecycle": facts,
            "partial_selection_permitted": False})

    lifecycle = Lifecycle.from_facts(frontier["lifecycle"], persist=persist_activity)
    monitor = ResourceMonitor()
    try:
        calibration_table: list[dict[str, object]] = frontier["calibration_table"]
        calibrated_seeds = {int(row["algorithm_seed"]) for row in calibration_table}
        for seed in ALGORITHM_SEEDS:
            if seed in calibrated_seeds:
                continue
            corpus = corpus_cache.get(seed)
            new_rows = calibrate_seed(corpus, seed, lifecycle, monitor.check)
            calibration_table.extend(new_rows)
            frontier["lifecycle"] = lifecycle.facts()
            frontier["calibration_table"] = calibration_table
            atomic_save(frontier_path, frontier)
        expected = [(seed, arm) for seed in ALGORITHM_SEEDS for arm in ARMS]
        observed = [(int(row["algorithm_seed"]), str(row["arm"])) for row in calibration_table]
        if observed != expected:
            raise RuntimeError("training cannot begin without complete ordered 24-cell calibration")
        invalid_calibrations = [row for row in calibration_table if not row["calibration_valid"]]
        if invalid_calibrations:
            invalid_resources = monitor.snapshot()
            invalid_resources.update({"numpy_version": np.__version__,
                                      "torch_version": torch.__version__,
                                      "cpu_workers": 1, "gpu_used": False})
            frontier["anomalies"].append({"kind": "invalid_update_zero_calibration",
                "invalid_cell_count": len(invalid_calibrations),
                "training_invoked": False, "evaluation_invoked": False})
            lifecycle.persist = None
            result = invalid_calibration_packet(lifecycle, static=static,
                coordinate_manifest=frontier["fresh_coordinate_manifest"],
                calibrations=calibration_table, resources=invalid_resources,
                frontier_path=str(frontier_path), activity_sidecar=str(sidecar),
                anomalies=frontier["anomalies"])
            _atomic_json(output, result)
            return reconcile_installed_result(output, frontier_path, result, frontier)
        if lifecycle.phase == "calibration":
            lifecycle.begin_training()
            frontier["lifecycle"] = lifecycle.facts()
            frontier["phase"] = "training"
            atomic_save(frontier_path, frontier)

        completed_seeds: dict[str, dict[str, object]] = frontier["completed_seeds"]
        for seed in ALGORITHM_SEEDS:
            seed_key = _seed_key(seed)
            if seed_key in completed_seeds:
                continue
            corpus = corpus_cache.get(seed)
            plan = LockedBatchPlan(corpus, seed)
            calibrations = {arm: _calibration_lookup(calibration_table, seed, arm) for arm in ARMS}
            coefficients = {arm: float(calibrations[arm]["lambda_s_m"]) for arm in ARMS}
            active = frontier.get("active_seed")
            if active is None:
                models: dict[str, SCDMPModel] = {}
                optimizers: dict[str, torch.optim.Adam] = {}
                for arm in ARMS:
                    model, optimizer = initialize_cell(seed)
                    models[arm] = model
                    optimizers[arm] = optimizer
                traces: dict[str, list[dict[str, object]]] = {arm: [] for arm in ARMS}
                final_losses: dict[str, dict[str, float]] = {arm: {} for arm in ARMS}
                next_update = 0
            else:
                if int(active["algorithm_seed"]) != seed or tuple(active["arm_order"]) != ARMS:
                    raise RuntimeError("frontier active seed does not match fixed seed/arm order")
                models = {}
                optimizers = {}
                for arm in ARMS:
                    model, optimizer = initialize_cell(seed)
                    model.load_state_dict(active["model_states"][arm], strict=True)
                    optimizer.load_state_dict(active["optimizer_states"][arm])
                    models[arm] = model
                    optimizers[arm] = optimizer
                traces = {arm: copy.deepcopy(list(active["gradient_traces"][arm])) for arm in ARMS}
                final_losses = {arm: copy.deepcopy(active["final_losses"][arm]) for arm in ARMS}
                if {arm: float(active["fixed_coefficients"][arm]) for arm in ARMS} != coefficients:
                    raise RuntimeError("frontier fixed coefficients do not match retained calibrations")
                next_update = int(active["next_update"])
            for update, _dispatches in update_major_dispatch(next_update):
                def step_arm(arm: str) -> None:
                    monitor.check()
                    row, arm_losses = train_update(
                        models[arm], optimizers[arm], corpus, seed, arm, update,
                        calibrations[arm], plan,
                    )
                    traces[arm].append(row)
                    final_losses[arm] = arm_losses
                frontier["active_seed"] = execute_update_major_step(
                    update, step_arm,
                    lambda next_complete_update: active_seed_snapshot(
                        algorithm_seed=seed, next_update=next_complete_update, models=models,
                        optimizers=optimizers, traces=traces, final_losses=final_losses,
                        fixed_coefficients=coefficients,
                    ),
                )
                if (update + 1) % FRONTIER_UPDATE_INTERVAL == 0 \
                        or update + 1 == OPTIMIZER_UPDATES:
                    atomic_save(frontier_path, frontier)
            arm_cells = {arm: {"algorithm_seed": seed, "arm": arm,
                    "model_state": model_state(models[arm]),
                    "gradient_trace": traces[arm], "gradient_summary": summarize_trace(traces[arm]),
                    "final_losses": final_losses[arm], "fixed_lambda": coefficients[arm],
                    "update_zero_delivered_minus_target":
                        float(traces[arm][0]["D"]) - float(calibrations[arm]["T_s"]),
                    "updates": OPTIMIZER_UPDATES} for arm in ARMS}
            completed_seeds[seed_key] = {"algorithm_seed": seed, "arms": arm_cells,
                "schedule": {"major_axis": "update", "arm_order": list(ARMS)}}
            frontier["completed_seeds"] = completed_seeds
            frontier["active_seed"] = None
            atomic_save(frontier_path, frontier)

        if list(completed_seeds) != [str(seed) for seed in ALGORITHM_SEEDS]:
            raise RuntimeError("B3 evaluation requires all eight update-major trained seeds")
        if lifecycle.phase == "training":
            lifecycle.begin_evaluation()
            frontier["lifecycle"] = lifecycle.facts()
            frontier["phase"] = "evaluation"
            atomic_save(frontier_path, frontier)

        seed_packets: list[dict[str, object]] = frontier["seed_packets"]
        completed_seed_ids = {int(packet["algorithm_seed"]) for packet in seed_packets}
        ledger: dict[str, int] = frontier["ledger"]
        for seed in ALGORITHM_SEEDS:
            if seed in completed_seed_ids:
                continue
            corpus = corpus_cache.get(seed)
            structural = structural_certificate(corpus)
            completed_seed = completed_seeds[_seed_key(seed)]
            models: dict[str, SCDMPModel] = {}
            for arm in ARMS:
                model = SCDMPModel(seed)
                model.load_state_dict(completed_seed["arms"][arm]["model_state"], strict=True)
                models[arm] = model
            train_support = {arm: train_support_competence(models[arm], corpus) for arm in ARMS}
            audit, audit_ledger = analyze_audit(seed, models, corpus, monitor.check)
            scored, scored_steps = evaluate_scored(seed, models, monitor.check)
            next_ledger = dict(ledger)
            credit_seed_ledger(next_ledger, corpus_microsteps=corpus.microsteps,
                               audit_ledger=audit_ledger, scored_steps=scored_steps)
            arm_cells = completed_seed["arms"]
            packet = {"algorithm_seed": seed, "scalers": corpus.scales.as_dict(),
                "fit_target_means": {name: float(value) for name, value in corpus.means.items()},
                "structural_certificate": structural,
                "homogeneous_relation_certificate": frontier["preactivity_certificates"][seed - 200]["homogeneous_relation_certificate"],
                "training": {"arm_order": list(ARMS), "updates_per_arm": OPTIMIZER_UPDATES,
                    "calibrations": {arm: _calibration_lookup(calibration_table, seed, arm) for arm in ARMS},
                    "fixed_coefficients": {arm: float(_calibration_lookup(calibration_table, seed, arm)["lambda_s_m"]) for arm in ARMS},
                    "gradient_trace": {arm: arm_cells[arm]["gradient_trace"] for arm in ARMS},
                    "gradient_quarter_summaries": {arm: arm_cells[arm]["gradient_summary"] for arm in ARMS},
                    "final_losses": {arm: arm_cells[arm]["final_losses"] for arm in ARMS},
                    "update_zero_delivery_checks": {arm: arm_cells[arm]["update_zero_delivered_minus_target"] for arm in ARMS},
                    "endpoint_gradient_traversals": len(ARMS) * OPTIMIZER_UPDATES,
                    "auxiliary_gradient_traversals": len(ARMS) * OPTIMIZER_UPDATES},
                "train_support": train_support, "audit": audit,
                "scored_episodes": serialize_scored(scored),
                "checkpoints": {arm: checkpoint(models[arm]) for arm in ARMS}}
            seed_packets = [*seed_packets, packet]
            ledger = next_ledger
            frontier["seed_packets"] = seed_packets
            frontier["ledger"] = ledger
            atomic_save(frontier_path, frontier)

        if ledger != MICROSTEP_LEDGER or sum(ledger.values()) != MICROSTEP_TOTAL:
            raise RuntimeError(f"B3 analytic ledger mismatch: {ledger}")
        if len(seed_packets) != 8 or sum(len(p["scored_episodes"]) for p in seed_packets) != 4_608:
            raise RuntimeError("B3 retained panel denominator mismatch")
        inference = complete_inference(seed_packets)
        monitor.check()
        resources = monitor.snapshot()
        resources.update({"numpy_version": np.__version__, "torch_version": torch.__version__,
            "parameter_count_per_arm": MODEL_PARAMETER_COUNT, "arms": 3,
            "updates_per_arm_seed": OPTIMIZER_UPDATES,
            "training_forwards": TRAINING_FORWARD_TOTAL,
            "calibration_endpoint_forwards": CALIBRATION_ENDPOINT_FORWARD_TOTAL,
            "calibration_auxiliary_forwards": CALIBRATION_AUXILIARY_FORWARD_TOTAL,
            "treatment_definition_and_training_forwards": TREATMENT_FORWARD_TOTAL,
            "training_endpoint_gradient_traversals": TRAINING_ENDPOINT_GRADIENT_TOTAL,
            "training_auxiliary_gradient_traversals": TRAINING_AUXILIARY_GRADIENT_TOTAL,
            "calibration_endpoint_gradient_traversals": CALIBRATION_ENDPOINT_GRADIENT_TOTAL,
            "calibration_auxiliary_gradient_traversals": CALIBRATION_AUXILIARY_GRADIENT_TOTAL,
            "dhom_forwards": DHOM_FORWARD_TOTAL,
            "physical_full_joint_steps": PHYSICAL_FULL_JOINT_TOTAL,
            "target_scalar_agent_factor_transitions": FACTOR_TRANSITIONS_PER_PANEL_KIND,
            "reverse_scalar_agent_factor_transitions": FACTOR_TRANSITIONS_PER_PANEL_KIND})
        frontier["resource_slices"].append(resources)
        lifecycle.persist = None
        result = complete_packet(lifecycle, static=static,
            coordinate_manifest=frontier["fresh_coordinate_manifest"],
            calibrations=calibration_table, seeds=seed_packets, inference=inference,
            resources={"slices": frontier["resource_slices"], **resources}, ledger=ledger,
            frontier_path=str(frontier_path), activity_sidecar=str(sidecar),
            anomalies=frontier["anomalies"])
        _atomic_json(output, result)
        return reconcile_installed_result(output, frontier_path, result, frontier)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            kind = type(exc).__name__
        else:
            kind = "exception"
        frontier["lifecycle"] = lifecycle.facts()
        frontier["resource_slices"].append(monitor.snapshot())
        frontier["anomalies"].append({"kind": kind, "message": str(exc),
                                      "traceback": traceback.format_exc()})
        atomic_save(frontier_path, frontier)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Exact SCDMP-B3 stability-first runner")
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--frontier", type=Path)
    parser.add_argument("--preactivity-smoke-seed", type=int, choices=ALGORITHM_SEEDS)
    args = parser.parse_args(argv)
    if args.production and (args.output is None or args.frontier is None):
        parser.error("--production requires --output and --frontier")
    if args.resume and not args.production:
        parser.error("--resume requires --production")
    try:
        if args.production:
            result = production(args.output, args.frontier, resume=args.resume)
        else:
            result = prepare_static(structural_seed=args.preactivity_smoke_seed)
            if args.output is not None:
                _write_fresh_json(args.output, result)
        print(json.dumps({"candidate": CANDIDATE, "revision": REVISION,
            "complete": result.get("complete", False),
            "scientific_activity_started": result.get("scientific_activity_started", False),
            "question_relevant_output_exists": result.get("question_relevant_output_exists", False),
            "output": str(args.output.resolve()) if args.output else None,
            "frontier": str(args.frontier.resolve()) if args.frontier else None}, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"candidate": CANDIDATE, "revision": REVISION,
            "complete": False, "question_relevant_output_exists": False,
            "error": str(exc), "output": str(args.output.resolve()) if args.output else None,
            "frontier": str(args.frontier.resolve()) if args.frontier else None}, sort_keys=True),
            file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
