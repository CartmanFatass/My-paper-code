from __future__ import annotations

import os

# These bindings precede NumPy/Torch imports.  The production process exposes
# one CPU worker and no GPU; all model tensors are also created on CPU.
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import argparse
import json
from pathlib import Path
import sys
import time
import traceback

from .config import (
    ADAM, ALGORITHM_SEEDS, ARMS, BANK_ORDER, CANDIDATE, COMPOSITION_WEIGHT,
    MICROSTEP_LEDGER, MICROSTEP_MAXIMUM, MODEL_PARAMETER_ABORT_CEILING,
    MODEL_PARAMETER_BREAKDOWN, MODEL_PARAMETER_COUNT, NUMPY_VERSION,
    OPTIMIZER_UPDATES, REGISTERED_RESOURCES, REVISION, SCALER_ATOMS_PER_OUTPUT,
    SCALER_DDOF, SCALER_NUMPY_CALL, SCORED_REGIMES, STRATUM_ORDER,
    TARGET_DURATIONS, TARGET_REGIMES, TRAIN_DURATIONS, target_decomposition_certificate,
)
from .lifecycle import Lifecycle
from .result import complete_result_packet, incomplete_result


def _operation_projection() -> dict[str, object]:
    boundaries_per_episode_by_regime = {
        "fixed_4": 60, "fixed_8": 30, "fixed_6": 40, "fixed_12": 20,
        "switch_6_to_12": 30, "switch_12_to_6": 30,
    }
    scored_boundaries = (
        sum(boundaries_per_episode_by_regime.values()) * 32 * len(ARMS) * len(ALGORITHM_SEEDS)
    )
    return {
        "training_row_model_evaluations_per_arm_update": 576,
        "training_batched_model_calls_per_arm_update": 9,
        "training_row_model_evaluations_all_arms_seeds": 576 * 2 * 1_000 * 8,
        "training_batched_model_calls_all_arms_seeds": 9 * 2 * 1_000 * 8,
        "scored_actor_boundaries": scored_boundaries,
        "actor_factor_rows_per_boundary": {"node_action": 12, "directed_edge_action_pair": 36},
        "audit_analytic_word_action_evaluations": 8 * 128 * 81,
        "audit_physical_factor_trajectories": 8 * 128 * 12,
        "audit_directly_rolled_candidates_per_word_state": 12,
        "composition_bank_replay_transitions": 0,
        "superseded_uncharged_composition_replay_transitions_removed": 49_152,
        "audit_learned_word_state_panels": 8 * 2 * 128,
        "scored_environment_episodes": 8 * 2 * 6 * 32,
        "wall_statement": (
            "No benchmark was authorized; runtime is guarded by the exact 5,400-second abort ceiling. "
            "The implementation replaces 576 row-level training calls per arm/update with nine "
            "equal-row batched calls and replaces 48 tiny actor factor calls per boundary with one "
            "12-node-action batch and one 36-edge-pair batch."
        ),
    }


def _static_conformance() -> dict[str, object]:
    from .analysis import analysis_contract
    from .evaluation import audit_denominators

    parameter_sum = sum(MODEL_PARAMETER_BREAKDOWN.values())
    ledger_sum = sum(MICROSTEP_LEDGER.values())
    estimated_model_parameter_bytes = len(ARMS) * MODEL_PARAMETER_COUNT * 4
    estimated_adam_parameter_bytes = len(ARMS) * MODEL_PARAMETER_COUNT * 8
    estimated_corpus_upper_bytes = 98_304 * 512
    projected_rss_bytes = (
        estimated_model_parameter_bytes + estimated_adam_parameter_bytes
        + estimated_corpus_upper_bytes + 512 * 1024**2
    )
    checks = {
        "revision_exact_v5": REVISION == "SCDMP-B1-SCIENCE-20260812-05",
        "parameter_breakdown_sum_exact": parameter_sum == MODEL_PARAMETER_COUNT,
        "nominal_parameters_below_abort_ceiling": MODEL_PARAMETER_COUNT < MODEL_PARAMETER_ABORT_CEILING,
        "microstep_ledger_sum_exact": ledger_sum == MICROSTEP_MAXIMUM,
        "one_cpu": REGISTERED_RESOURCES.cpu_workers == 1,
        "gpu_disabled": REGISTERED_RESOURCES.gpu_allowed is False,
        "optimizer_updates_exact": REGISTERED_RESOURCES.optimizer_updates_per_arm_seed == OPTIMIZER_UPDATES == 1000,
        "projected_rss_below_two_gib": projected_rss_bytes < REGISTERED_RESOURCES.rss_limit_bytes,
        "training_support_only_2_4_8": TRAIN_DURATIONS == (2, 4, 8),
        "targets_only_6_12": TARGET_DURATIONS == (6, 12),
        "paired_arm_objective_only_differs_in_composition_weight": COMPOSITION_WEIGHT == {
            "SCDMP": 0.5, "SCDMP-NOCOMP": 0.0,
        },
        "bank_order_exact": BANK_ORDER == ("E_2", "E_4", "E_8", "C_22", "C_44"),
        "eight_strata": len(STRATUM_ORDER) == 8,
        "six_scored_regimes": len(SCORED_REGIMES) == 6,
        "eight_algorithm_seeds": ALGORITHM_SEEDS == tuple(range(8)),
        "scaler_population_ddof_zero": SCALER_DDOF == 0,
        "scaler_atoms_exact": SCALER_ATOMS_PER_OUTPUT == 10_752,
        "audit_factorized_candidate_count_within_ceiling": 12 <= 16,
        "audit_factorized_transitions_within_16H": all(
            12 * duration <= 16 * duration for duration in TARGET_DURATIONS
        ),
        "every_target_word_has_both_registered_train_supported_decompositions": bool(
            target_decomposition_certificate()["conforming"]
        ),
    }
    return {
        "checks": checks,
        "production_conforming": all(checks.values()),
        "constants": {
            "candidate": CANDIDATE,
            "revision": REVISION,
            "numpy_required": NUMPY_VERSION,
            "arms": list(ARMS),
            "parameter_count_per_arm": MODEL_PARAMETER_COUNT,
            "parameter_breakdown": MODEL_PARAMETER_BREAKDOWN,
            "adam": ADAM,
            "scaler": {
                "atoms_per_output_per_seed": SCALER_ATOMS_PER_OUTPUT,
                "ddof": SCALER_DDOF,
                "numpy_call": SCALER_NUMPY_CALL,
                "floor_float64": 1.0e-3,
                "final_cast": "numpy.float32_once",
                "sharing": "paired_arms",
            },
            "microstep_ledger": MICROSTEP_LEDGER,
            "microstep_maximum": MICROSTEP_MAXIMUM,
            "wall_limit_seconds": REGISTERED_RESOURCES.wall_limit_seconds,
            "rss_limit_bytes": REGISTERED_RESOURCES.rss_limit_bytes,
            "projected_rss_bytes_conservative": projected_rss_bytes,
            "operation_projection": _operation_projection(),
            "audit_denominators": audit_denominators(),
            "analysis_contract": analysis_contract(),
            "evidence_complexity": {
                "directly_rolled_candidates_per_audit_word_state": 12,
                "candidate_ceiling": 16,
                "physical_factor_transitions_per_word_state": {
                    str(duration): 12 * duration for duration in TARGET_DURATIONS
                },
                "transition_ceiling_per_word_state": {
                    str(duration): 16 * duration for duration in TARGET_DURATIONS
                },
                "joint_action_panel_evaluation": "exact analytic fixed-degree factors plus cycle DP",
                "joint_action_trajectory_enumeration": False,
                "composition_bank_environment_replay": False,
            },
            "target_decomposition_certificate": target_decomposition_certificate(),
            "science_source": (
                "docs/research/candidates/semigroup_consistent_duration_model_policy/"
                "SCDMP_B1_SCIENCE_CARD.md"
            ),
        },
    }


def prepare_static() -> dict[str, object]:
    lifecycle = Lifecycle()
    lifecycle.record("static_support_prepared", production_requested=False)
    return incomplete_result(
        lifecycle,
        reason=(
            "Static support preparation only; production was not explicitly requested. "
            "No corpus, bank, random draw, model forward, optimizer, evaluation, or inference ran."
        ),
        static_conformance=_static_conformance(),
    )


def _gate_facts(
    seed_packets: list[dict[str, object]], inference: dict[str, object],
) -> dict[str, object]:
    audit_vectors = inference["audit_seed_vectors"]
    def mean(values: list[float]) -> float:
        return float(sum(float(value) for value in values) / len(values))

    nocomp_h = mean(audit_vectors["headroom_fraction"]["SCDMP-NOCOMP"]["REAL"])
    nocomp_r = mean(audit_vectors["headroom_regret"]["SCDMP-NOCOMP"]["REAL"])
    nocomp_d = mean(audit_vectors["D_comp"]["SCDMP-NOCOMP"]["REAL"])
    actor_difference = mean(audit_vectors["actor_disagreement"]["REAL"])
    score_sensitivity = {
        arm: mean(audit_vectors["score_sensitivity"][arm]["REAL"])
        for arm in ARMS
    }
    e_pred = {
        arm: mean(audit_vectors["E_pred"][arm]["REAL"])
        for arm in ARMS
    }
    main = inference["main_estimands"]
    regimes = inference["regime_estimands"]
    word_groups = inference["real_word_subgroups"]
    performance_route = main["Delta_task"]["bounds"]["lower_97_5"]["bound"] > 0.015
    failure_route = (
        main["Delta_fail_target_mean"]["bounds"]["lower_97_5"]["bound"] > 0.05
        and main["Delta_task"]["bounds"]["lower_95"]["bound"] > -0.005
    )
    simultaneous_nonharm = all(
        regimes[regime]["Delta_J"]["bounds"]["lower_98_75"]["bound"] > -0.005
        for regime in SCORED_REGIMES
    )
    composition_bound = main["Delta_comp_REAL"]["bounds"]["lower_95"]["bound"] > 0.10
    prediction_bound = main["Delta_pred_REAL"]["bounds"]["lower_95"]["bound"] > 0.05
    robustness_bound = main["Delta_rob"]["bounds"]["lower_95"]["bound"] > 0.010
    specificity_bound = main["Delta_spec"]["bounds"]["lower_95"]["bound"] > 0.005
    target_no_use = {
        regime: {
            "Delta_J_upper_95_below_0_010": (
                regimes[regime]["Delta_J"]["bounds"]["upper_95"]["bound"] < 0.010
            ),
            "Delta_fail_upper_95_below_0_03": (
                regimes[regime]["Delta_fail"]["bounds"]["upper_95"]["bound"] < 0.03
            ),
        } for regime in TARGET_REGIMES
    }
    word_no_use = {
        word_row: report["bounds"]["upper_95"]["bound"] < 0.010
        for word_row, report in word_groups.items()
    }
    return {
        "update_zero_coverage_all_seeds": all(
            bool(seed["training"]["support_certificate"]["conforming"]) for seed in seed_packets
        ),
        "joint_action_support_at_least_four_all_duration_seed_cells": all(
            bool(report["all_at_least_four"])
            for seed in seed_packets for report in seed["action_support"].values()
        ),
        "scalers_exact_v5_all_seeds": all(
            seed["scalers"]["atoms_per_output"] == 10_752
            and seed["scalers"]["ddof"] == 0 for seed in seed_packets
        ),
        "audit_denominators_exact_all_seeds": all(
            seed["audit"]["denominators"]["real_word_state_instances_per_seed"] == 64
            and seed["audit"]["denominators"]["sham_word_state_instances_per_seed"] == 64
            and seed["audit"]["denominators"]["real_action_panels_per_seed"] == 64 * 81
            for seed in seed_packets
        ),
        "state_support_fraction_by_seed": [
            seed["audit"]["state_support"][
                "fraction_states_all_normalized_physical_coordinates_in_range"
            ] for seed in seed_packets
        ],
        "state_support_ge_0_90_all_seeds": all(
            seed["audit"]["state_support"][
                "fraction_states_all_normalized_physical_coordinates_in_range"
            ] >= 0.90 for seed in seed_packets
        ),
        "REAL_order_median_ge_0_01_all_seeds": all(
            seed["audit"]["physical_order_and_sham_identity"]["REAL"][
                "median_max_score_difference_per_step"
            ] >= 0.01 for seed in seed_packets
        ),
        "REAL_oracle_reversal_fraction_ge_0_10_all_seeds": all(
            seed["audit"]["physical_order_and_sham_identity"]["REAL"][
                "oracle_action_difference_fraction"
            ] >= 0.10 for seed in seed_packets
        ),
        "SHAM_identity_max_le_1e_10_all_seeds": all(
            seed["audit"]["physical_order_and_sham_identity"]["SHAM"][
                "maximum_absolute_difference"
            ] <= 1.0e-10 for seed in seed_packets
        ),
        "NOCOMP_REAL_headroom": {
            "mean_h_s": nocomp_h, "required_h": 0.20, "h_pass": nocomp_h >= 0.20,
            "mean_r_s": nocomp_r, "required_r": 0.01, "r_pass": nocomp_r >= 0.01,
        },
        "NOCOMP_REAL_D_comp_mean": nocomp_d,
        "NOCOMP_REAL_D_comp_ge_0_05": nocomp_d >= 0.05,
        "REAL_actor_disagreement_mean": actor_difference,
        "REAL_actor_disagreement_ge_0_10": actor_difference >= 0.10,
        "finite_outputs_all_arm_seed_panels": all(
            not seed["audit"]["arms"][arm]["nonfinite_output_present"]
            for seed in seed_packets for arm in ARMS
        ),
        "F_bound_hit_le_0_01_all_arm_seed_panels": all(
            seed["audit"]["arms"][arm]["direct_and_recursive_F_bound_hit_fraction"] <= 0.01
            for seed in seed_packets for arm in ARMS
        ),
        "train_support_probe_composite_by_arm_seed": {
            arm: [seed["train_support_probe"][arm]["composite_standardized_rmse"]
                  for seed in seed_packets] for arm in ARMS
        },
        "train_support_probe_le_0_35_all_arm_seeds": all(
            seed["train_support_probe"][arm]["composite_standardized_rmse"] <= 0.35
            for seed in seed_packets for arm in ARMS
        ),
        "REAL_E_pred_across_seed_mean": e_pred,
        "NOCOMP_REAL_E_pred_le_0_75": e_pred["SCDMP-NOCOMP"] <= 0.75,
        "SCDMP_REAL_E_pred_le_0_50": e_pred["SCDMP"] <= 0.50,
        "SCDMP_F_variance_ratio_by_seed": [
            seed["audit"]["arms"]["SCDMP"]["F_output_variance_ratio"]
            for seed in seed_packets
        ],
        "SCDMP_F_variance_ratio_in_0_25_4_all_seed_coordinates": all(
            0.25 <= float(ratio) <= 4.0
            for seed in seed_packets
            for ratio in seed["audit"]["arms"]["SCDMP"]["F_output_variance_ratio"].values()
        ),
        "REAL_candidate_score_sensitivity_mean": score_sensitivity,
        "REAL_candidate_score_sensitivity_ge_0_20": {
            arm: value >= 0.20 for arm, value in score_sensitivity.items()
        },
        "direct_value_routes": {
            "performance": performance_route,
            "failure_robustness": failure_route,
            "simultaneous_target_and_seen_nonharm": simultaneous_nonharm,
            "any_route_with_nonharm": (performance_route or failure_route) and simultaneous_nonharm,
        },
        "mechanism_bound_comparisons": {
            "Delta_comp_REAL_lcb_95_above_0_10": composition_bound,
            "Delta_pred_REAL_lcb_95_above_0_05": prediction_bound,
            "Delta_rob_lcb_95_above_0_010": robustness_bound,
            "Delta_spec_lcb_95_above_0_005": specificity_bound,
        },
        "convoy_deletion_no_use_comparisons": {
            "target_regimes": target_no_use,
            "Delta_spec_upper_95_below_0_005": (
                main["Delta_spec"]["bounds"]["upper_95"]["bound"] < 0.005
            ),
            "real_initial_word_rows": word_no_use,
            "all_eight_subgroups_below_registered_margins": (
                all(all(item.values()) for item in target_no_use.values())
                and all(word_no_use.values())
            ),
        },
        "adverse_triggering_estimands": inference["adverse_family"]["triggering_members"],
        "gate_comparisons_are_factual_only": True,
        "scientific_branch_assignment": None,
    }


def _activity_sidecar_path(output: Path) -> Path:
    return Path(str(output.resolve()) + ".activity.json")


def _atomic_replace_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def production(output: Path) -> dict[str, object]:
    import numpy as np
    import torch

    from .analysis import complete_inference
    from .audit import analyze_audit
    from .corpus import action_support_report, build_corpus, corpus_conformance_certificate
    from .evaluation import evaluate_scored_pair, scored_rows_as_dicts
    from .resources import ResourceMonitor
    from .rng import require_numpy_version
    from .training import train_paired, train_support_probe

    sidecar = _activity_sidecar_path(output)
    if output.resolve().exists():
        raise FileExistsError(f"refusing to overwrite existing result: {output.resolve()}")
    if sidecar.exists():
        raise FileExistsError(f"refusing to reuse existing activity sidecar: {sidecar}")

    def persist_activity(facts: dict[str, object]) -> None:
        if not bool(facts["scientific_activity_started"]) and facts["phase"] not in (
            "aborted", "complete",
        ):
            return
        _atomic_replace_json(sidecar, {
            "artifact_kind": "SCDMP_B1_V5_ACTIVITY_SIDECAR",
            "candidate": CANDIDATE,
            "revision": REVISION,
            "final_result_path": str(output.resolve()),
            "lifecycle": facts,
        })

    lifecycle = Lifecycle(phase="production_preflight", persist=persist_activity)
    lifecycle.record("production_explicitly_requested", argv=list(sys.argv))
    static = _static_conformance()
    partial: dict[str, object] = {"completed_seeds": []}
    monitor = None
    try:
        if not static["production_conforming"]:
            raise RuntimeError("static v5 conformance preflight failed")
        require_numpy_version()
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
            raise RuntimeError("Torch did not bind to one CPU worker")
        if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
            raise RuntimeError("GPU visibility was not disabled before Torch import")
        monitor = ResourceMonitor()
        monitor.check()
        seed_packets: list[dict[str, object]] = []
        scored_rows = []
        audits: list[dict[str, object]] = []
        microsteps = {name: 0 for name in MICROSTEP_LEDGER}
        for algorithm_seed in ALGORITHM_SEEDS:
            monitor.check()
            corpus = build_corpus(algorithm_seed)
            corpus_certificate = corpus_conformance_certificate(corpus, algorithm_seed)
            if not corpus_certificate["conforming"]:
                raise RuntimeError(f"seed={algorithm_seed} corpus/leakage certificate failed")
            if corpus.microsteps != MICROSTEP_LEDGER["common_training_corpus"] // 8:
                raise RuntimeError("per-seed corpus microstep category mismatch")
            microsteps["common_training_corpus"] += corpus.microsteps
            models, training = train_paired(
                corpus, algorithm_seed, lifecycle, resource_check=monitor.check,
            )
            if any(next(model.parameters()).device.type != "cpu" for model in models.values()):
                raise RuntimeError("a model left the registered CPU")
            probe = {arm: train_support_probe(model, corpus) for arm, model in models.items()}
            audit, audit_steps = analyze_audit(
                algorithm_seed, models, corpus, resource_check=monitor.check,
            )
            for category, count in audit_steps.items():
                expected = MICROSTEP_LEDGER[category] // 8
                if count != expected:
                    raise RuntimeError(
                        f"seed={algorithm_seed} audit category {category}={count}, expected {expected}"
                    )
                microsteps[category] += count
            seed_scored_rows, scored_steps = evaluate_scored_pair(
                algorithm_seed, models, resource_check=monitor.check,
            )
            if scored_steps != MICROSTEP_LEDGER["scored_evaluation"] // 8:
                raise RuntimeError("per-seed scored-evaluation microstep category mismatch")
            microsteps["scored_evaluation"] += scored_steps
            scored_rows.extend(seed_scored_rows)
            audits.append(audit)
            seed_packets.append({
                "algorithm_seed": algorithm_seed,
                "scalers": corpus.scales.as_dict(),
                "scaler_arm_sharing": "one corpus Scales object used by both arms",
                "scaler_certificate": {
                    "source_population": "E_2,E_4,E_8 fit targets only",
                    "atom_count_per_output": 10_752,
                    "array_dtype_and_layout": "C-contiguous numpy.float64",
                    "reduction": SCALER_NUMPY_CALL,
                    "floor": "numpy.maximum(sigma64,numpy.float64(1e-3))",
                    "stored_dtype": "numpy.float32 after one cast",
                    "shared_before_update_zero": True,
                    "arm_specific_recomputation": False,
                    "standardized_use_locations": [
                        "L_endpoint", "L_comp", "D_comp_init",
                        "untouched_train_support_endpoint_node_edge_RMSE",
                        "REAL_SHAM_POOLED_D_comp", "REAL_SHAM_POOLED_E_pred",
                    ],
                    "raw_nonuses": [
                        "neural_inputs", "task_returns", "failures", "oracle_scores_actions_regret",
                        "state_support", "output_variance_ratios", "reversal_effects",
                        "action_disagreement", "candidate_score_sensitivity", "treatment_estimands",
                        "confidence_bounds", "resource_counts",
                    ],
                },
                "corpus_and_no_test_leakage_certificate": corpus_certificate,
                "evaluation_traversal_certificate": {
                    "scored_rng_seeds": [
                        750_000 + 1_000 * algorithm_seed + index
                        for index in range(len(SCORED_REGIMES))
                    ],
                    "regime_order": list(SCORED_REGIMES),
                    "episodes_per_regime": 32,
                    "evaluation_after_both_final_checkpoints": True,
                    "audit_opened_after_both_final_checkpoints": True,
                    "evaluation_or_audit_used_for_optimization_or_checkpoint": False,
                },
                "training": training,
                "action_support": action_support_report(corpus),
                "train_support_probe": probe,
                "audit": audit,
                "scored_episodes": scored_rows_as_dicts(seed_scored_rows),
            })
            lifecycle.seed_complete(algorithm_seed)
            partial["completed_seeds"] = list(range(algorithm_seed + 1))
        if microsteps != MICROSTEP_LEDGER:
            raise RuntimeError(
                f"registered analytic-panel microstep categories {microsteps} != {MICROSTEP_LEDGER}"
            )
        inference = complete_inference(scored_rows, audits)
        inference["gate_facts"] = _gate_facts(seed_packets, inference)
        if len(scored_rows) != 8 * 2 * 6 * 32:
            raise RuntimeError("complete scored panel row count mismatch")
        for seed_packet in seed_packets:
            denominators = seed_packet["audit"]["denominators"]
            if denominators["real_word_state_instances_per_seed"] != 64:
                raise RuntimeError("REAL audit denominator is not 64 word-state instances")
            if denominators["sham_word_state_instances_per_seed"] != 64:
                raise RuntimeError("SHAM audit denominator is not 64 word-state instances")
        resource_actuals = monitor.facts()
        resource_actuals.update({
            "numpy_version": np.__version__, "torch_version": torch.__version__,
            "parameter_count_per_arm": MODEL_PARAMETER_COUNT,
            "optimizer_updates_per_arm_seed": OPTIMIZER_UPDATES,
        })
        return complete_result_packet(
            lifecycle, static_conformance=static, seeds=seed_packets,
            inference=inference, resource_actuals=resource_actuals, microsteps=microsteps,
            activity_sidecar={
                "path": str(sidecar), "exists": sidecar.exists(),
                "atomic_updates": True,
                "status": "terminal_complete_update_after_atomic_final_result_install",
            },
        )
    except Exception as exc:
        lifecycle.abort(str(exc))
        partial["traceback"] = traceback.format_exc()
        return incomplete_result(
            lifecycle, reason=str(exc), static_conformance=static, partial=partial,
            resource_actuals=monitor.snapshot() if monitor is not None else None,
            activity_sidecar={
                "path": str(sidecar), "exists": sidecar.exists(),
                "atomic_updates": True, "terminal_phase": "aborted",
            },
        )


def _write_fresh(path: Path, value: object) -> None:
    resolved = path.resolve()
    if resolved.exists():
        raise FileExistsError(f"refusing to overwrite existing result: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(resolved) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.rename(temporary, resolved)


def _finalize_complete_sidecar(output: Path, result: dict[str, object]) -> None:
    sidecar_facts = result.get("activity_sidecar")
    if not isinstance(sidecar_facts, dict) or "path" not in sidecar_facts:
        raise RuntimeError("complete production result lacks its activity sidecar path")
    _atomic_replace_json(Path(str(sidecar_facts["path"])), {
        "artifact_kind": "SCDMP_B1_V5_ACTIVITY_SIDECAR",
        "candidate": CANDIDATE,
        "revision": REVISION,
        "final_result_path": str(output.resolve()),
        "final_result_installed": True,
        "lifecycle": result["lifecycle"],
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SCDMP-B1 exact v5; default is static-only and production is explicit one-shot",
    )
    parser.add_argument("--production", action="store_true", help="run the exact one-shot v5 production")
    parser.add_argument("--output", type=Path, help="fresh result JSON path; required for production")
    args = parser.parse_args(argv)
    if args.production and args.output is None:
        parser.error("--production requires --output <fresh-result.json>")
    result = production(args.output) if args.production else prepare_static()  # type: ignore[arg-type]
    if args.output is not None:
        _write_fresh(args.output, result)
        if args.production and result["question_relevant_output_exists"]:
            _finalize_complete_sidecar(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if not args.production else (0 if result["question_relevant_output_exists"] else 2)


if __name__ == "__main__":
    raise SystemExit(main())
