"""Analyze the exact standalone R47-NSOPM-G0 evidence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from r47_nsopm import (
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    CAUSAL_CONTEXTS,
    EXPERIMENT_ID,
    FEATURE_DIM,
    FIT_GROUPS,
    FORCED_BRANCHES,
    FORCED_HORIZON,
    FORCED_STEPS,
    HALF_A_GROUPS,
    HALF_B_GROUPS,
    HELDOUT_GROUPS,
    K0,
    LAGS,
    NATURAL_GROUPS,
    NATURAL_WINDOWS,
    NATURAL_WINDOWS_PER_GROUP,
    N_AGENTS,
    N_SKILLS,
    REPLICAS,
    SCHEMA_VERSION,
    SUPPORT_POINTS_MIN,
    SUPPORT_QUANTILE,
    SUPPORT_RATIO_MIN,
    TEMPORAL_NULL_REPLICATES,
    TEMPORAL_NULL_SEED,
    VIEW_DIM,
    align_half_to_primary,
    bootstrap_mean_interval,
    bootstrap_ratio_interval,
    centered_for_model,
    coherence_null_mean,
    fit_spectral,
    group_mean,
    json_ready,
    mode_activations,
    nuisance_ridge_audit,
    pearson_correlation,
    support_distances,
    temporal_null_eigenvalues,
    window_mode_statistics,
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def load_evidence(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def exact_selected_checks(group: int) -> set[int]:
    return {0, 2, 4, 6} if group % 2 == 0 else {1, 3, 5, 7}


def validate_m0(
    worker: dict[str, Any], arrays: dict[str, np.ndarray]
) -> list[str]:
    reasons: list[str] = []
    telemetry = worker.get("telemetry", {})
    source = worker.get("source", {})
    view = worker.get("view", {})
    boundary = worker.get("algorithm_boundary", {})
    drift = worker.get("parameter_drift", {})

    if worker.get("schema_version") != SCHEMA_VERSION:
        reasons.append("schema version mismatch")
    if worker.get("experiment_id") != EXPERIMENT_ID or worker.get("scope") != "formal":
        reasons.append("formal worker identity mismatch")
    if worker.get("state") != "completed" or worker.get("device") != "cuda":
        reasons.append("formal worker did not complete on CUDA")
    if not all((source.get("source_checks") or {}).values()):
        reasons.append("source checkpoint/config contract failed")
    expected_telemetry = {
        "natural_groups": NATURAL_GROUPS,
        "natural_windows": NATURAL_WINDOWS,
        "expected_natural_windows": NATURAL_WINDOWS,
        "causal_contexts": CAUSAL_CONTEXTS,
        "branch_count": FORCED_BRANCHES,
        "completed_branch_steps": FORCED_STEPS,
        "complete_contexts": CAUSAL_CONTEXTS,
        "early_branch_reset_contexts": 0,
        "literal_zero_clock_steps": NATURAL_GROUPS * 80,
        "policy_optimizer_steps": 0,
        "high_optimizer_steps": 0,
        "critic_optimizer_steps": 0,
        "intrinsic_optimizer_steps": 0,
    }
    for name, expected in expected_telemetry.items():
        if telemetry.get(name) != expected:
            reasons.append(f"telemetry mismatch: {name}")
    if telemetry.get("incomplete_natural_windows") != 0:
        reasons.append("natural collection contains incomplete windows")
    if telemetry.get("early_natural_resets") != 0:
        reasons.append("natural episode ended outside the registered boundary")
    if telemetry.get("snapshot_restore_max_error") != 0.0:
        reasons.append("snapshot restore/replay mismatch")
    if telemetry.get("crn_seed_equal_across_skills") is not True:
        reasons.append("common-random-number skill branches mismatch")
    if telemetry.get("replica_seed_independent") is not True:
        reasons.append("forced replicas do not use independent seeds")
    if list(view.get("shape", [])) != [NATURAL_WINDOWS, K0, VIEW_DIM]:
        reasons.append("registered process-view shape mismatch")
    if float(view.get("covariance_last_three_max_abs", math.inf)) > 1e-7:
        reasons.append("N=2 singleton covariance fields are nonzero")
    if drift.get("inventory_equal") is not True or drift.get("all_exact") is not True:
        reasons.append("frozen module state drifted")
    if float(drift.get("max_abs", math.inf)) != 0.0:
        reasons.append("nonzero frozen parameter drift")
    required_boundary = {
        "standalone_reward_off_gate": True,
        "external_reward_discarded": True,
        "external_reward_stored": False,
        "environment_reward_field_in_evidence": False,
        "task_field_in_process_view": False,
        "action_field_in_process_view": False,
        "skill_field_in_process_view": False,
        "forced_data_used_for_basis_fit": False,
        "high_controller_suppressed_in_forced_branch": True,
        "policy_or_critic_update": False,
        "normal_trainer_modified": False,
    }
    if boundary != required_boundary:
        reasons.append("algorithm boundary differs from registered reward-off G0")
    forbidden_names = [name for name in arrays if "reward" in name.lower()]
    if forbidden_names:
        reasons.append(f"reward field leaked into evidence: {forbidden_names}")

    required_shapes = {
        "natural_views": (NATURAL_WINDOWS, K0, VIEW_DIM),
        "natural_group": (NATURAL_WINDOWS,),
        "natural_focal": (NATURAL_WINDOWS,),
        "natural_check": (NATURAL_WINDOWS,),
        "natural_focal_start": (NATURAL_WINDOWS, 2),
        "natural_teammate_start": (NATURAL_WINDOWS, 2),
        "natural_age_start": (NATURAL_WINDOWS,),
        "natural_actions": (NATURAL_WINDOWS, K0, N_AGENTS, 2),
        "forced_views": (
            CAUSAL_CONTEXTS,
            N_SKILLS,
            REPLICAS,
            FORCED_HORIZON,
            VIEW_DIM,
        ),
        "forced_lengths": (CAUSAL_CONTEXTS, N_SKILLS, REPLICAS),
        "forced_early": (CAUSAL_CONTEXTS, N_SKILLS, REPLICAS),
        "forced_seed": (CAUSAL_CONTEXTS, N_SKILLS, REPLICAS),
        "forced_context_group": (CAUSAL_CONTEXTS,),
        "forced_context_focal": (CAUSAL_CONTEXTS,),
        "forced_context_check": (CAUSAL_CONTEXTS,),
    }
    for name, shape in required_shapes.items():
        if name not in arrays or tuple(arrays[name].shape) != shape:
            reasons.append(f"evidence shape mismatch: {name}")
    if reasons:
        return reasons
    if not all(np.isfinite(value).all() for value in arrays.values() if value.dtype.kind in "fci"):
        reasons.append("evidence contains non-finite numeric values")
    if float(np.max(np.abs(arrays["natural_views"][..., 4:7]))) > 1e-7:
        reasons.append("natural singleton covariance contract failed")
    if float(np.max(np.abs(arrays["forced_views"][..., 4:7]))) > 1e-7:
        reasons.append("forced singleton covariance contract failed")
    groups = arrays["natural_group"]
    focals = arrays["natural_focal"]
    checks = arrays["natural_check"]
    for group in range(NATURAL_GROUPS):
        mask = groups == group
        if int(mask.sum()) != NATURAL_WINDOWS_PER_GROUP:
            reasons.append(f"group {group} does not contain eight natural windows")
            break
        if set(checks[mask].tolist()) != exact_selected_checks(group):
            reasons.append(f"group {group} uses the wrong staggered check schedule")
            break
        for check in exact_selected_checks(group):
            row = mask & (checks == check)
            if sorted(focals[row].tolist()) != [0, 1]:
                reasons.append(f"group {group} check {check} lacks both focal agents")
                break
    context_group = arrays["forced_context_group"]
    context_focal = arrays["forced_context_focal"]
    context_check = arrays["forced_context_check"]
    if not np.array_equal(context_group, np.arange(CAUSAL_CONTEXTS)):
        reasons.append("forced context/reset schedule mismatch")
    if not np.array_equal(context_focal, np.arange(CAUSAL_CONTEXTS) % N_AGENTS):
        reasons.append("forced focal schedule mismatch")
    expected_check = (np.arange(CAUSAL_CONTEXTS) // 2) % 4
    if not np.array_equal(context_check, expected_check):
        reasons.append("forced check schedule mismatch")
    if not np.all(arrays["forced_lengths"] == FORCED_HORIZON):
        reasons.append("forced branch length mismatch")
    if bool(np.any(arrays["forced_early"])):
        reasons.append("early forced reset/truncation observed")
    if not np.all(arrays["forced_seed"] == arrays["forced_seed"][:, 0:1, :]):
        reasons.append("forced CRN seed table differs across skills")
    return reasons


def temporal_and_stability_analysis(
    views: np.ndarray,
    group_ids: np.ndarray,
    primary: dict[str, Any],
    half_a: dict[str, Any],
    half_b: dict[str, Any],
) -> dict[str, Any]:
    fit_mask = np.isin(group_ids, FIT_GROUPS)
    heldout_mask = np.isin(group_ids, HELDOUT_GROUPS)
    primary_centered = centered_for_model(primary, views[fit_mask])
    null_eigenvalues = temporal_null_eigenvalues(primary_centered)
    null_q95 = np.quantile(null_eigenvalues, 0.95, axis=0)
    real_eigenvalues = np.asarray(primary["eigenvalues"][:N_SKILLS], dtype=np.float64)
    eigenvalue_pass = np.asarray(
        [
            real_eigenvalues[q] > float(primary["gram_floor"])
            and real_eigenvalues[q] > null_q95[q]
            for q in range(N_SKILLS)
        ],
        dtype=np.bool_,
    )

    heldout_views = views[heldout_mask]
    primary_activation = mode_activations(primary, heldout_views)
    half_a_activation = mode_activations(half_a, heldout_views)
    half_b_activation = mode_activations(half_b, heldout_views)
    primary_flat = primary_activation.reshape(-1, N_SKILLS)
    aligned_a, permutation_a, match_a = align_half_to_primary(
        primary_flat, half_a_activation.reshape(-1, N_SKILLS)
    )
    aligned_b, permutation_b, match_b = align_half_to_primary(
        primary_flat, half_b_activation.reshape(-1, N_SKILLS)
    )
    stability = np.asarray(
        [pearson_correlation(aligned_a[:, q], aligned_b[:, q]) for q in range(N_SKILLS)],
        dtype=np.float64,
    )

    statistics = window_mode_statistics(primary_activation)
    real_coherence = statistics["lag_correlations"].mean(axis=1)
    null_coherence = coherence_null_mean(primary_activation)
    coherence_difference = real_coherence - null_coherence
    heldout_groups = group_ids[heldout_mask]
    _groups, grouped_difference = group_mean(coherence_difference, heldout_groups)
    coherence_intervals = [
        bootstrap_mean_interval(grouped_difference[:, lag_index])
        for lag_index in range(len(LAGS))
    ]
    return {
        "null_eigenvalues": null_eigenvalues,
        "null_q95": null_q95,
        "real_eigenvalues": real_eigenvalues,
        "eigenvalue_pass": eigenvalue_pass,
        "primary_activation": primary_activation,
        "primary_statistics": statistics,
        "stability": stability,
        "permutation_a_to_primary": permutation_a,
        "permutation_b_to_primary": permutation_b,
        "primary_match_a": match_a,
        "primary_match_b": match_b,
        "real_coherence": real_coherence,
        "null_coherence": null_coherence,
        "coherence_intervals": coherence_intervals,
    }


def nuisance_features(
    arrays: dict[str, np.ndarray], heldout_mask: np.ndarray
) -> np.ndarray:
    focals = arrays["natural_focal"][heldout_mask]
    actions = arrays["natural_actions"][heldout_mask]
    variances = np.var(actions, axis=1, ddof=0)
    rows = []
    for index, focal in enumerate(focals):
        teammate = 1 - int(focal)
        rows.append(
            np.concatenate(
                [
                    arrays["natural_focal_start"][heldout_mask][index],
                    arrays["natural_teammate_start"][heldout_mask][index],
                    np.asarray([float(focal == 1)], dtype=np.float64),
                    np.asarray(
                        [min(int(arrays["natural_age_start"][heldout_mask][index]), 80) / 80.0],
                        dtype=np.float64,
                    ),
                    variances[index, int(focal)],
                    variances[index, teammate],
                ]
            )
        )
    return np.asarray(rows, dtype=np.float64)


def causal_horizon_statistics(
    model: dict[str, Any],
    horizon_views: np.ndarray,
    support_threshold: float,
) -> dict[str, Any]:
    context_count = horizon_views.shape[0]
    flat = horizon_views.reshape(-1, K0, VIEW_DIM)
    distances = support_distances(model, flat).reshape(
        context_count, N_SKILLS, REPLICAS, K0
    )
    branch_valid = np.sum(distances <= support_threshold, axis=-1) >= SUPPORT_POINTS_MIN
    context_valid = np.all(branch_valid, axis=(1, 2))
    activations = mode_activations(model, flat)
    statistics = window_mode_statistics(activations)
    g = statistics["g"].reshape(context_count, N_SKILLS, REPLICAS, N_SKILLS)
    gbar = g.mean(axis=2)
    assigned = np.empty((context_count, N_SKILLS), dtype=np.float64)
    for skill in range(N_SKILLS):
        other = [mode for mode in range(N_SKILLS) if mode != skill]
        assigned[:, skill] = gbar[:, skill, skill] - gbar[:, skill, other].mean(axis=1)
    between = np.empty(context_count, dtype=np.float64)
    within = np.empty(context_count, dtype=np.float64)
    for context in range(context_count):
        pair_values = [
            float(np.sum(np.square(gbar[context, left] - gbar[context, right])))
            for left in range(N_SKILLS)
            for right in range(left + 1, N_SKILLS)
        ]
        between[context] = float(np.mean(pair_values))
        within[context] = float(
            np.mean(
                [
                    0.5 * np.sum(np.square(g[context, skill, 0] - g[context, skill, 1]))
                    for skill in range(N_SKILLS)
                ]
            )
        )
    endpoint_s = np.empty((context_count, N_SKILLS, REPLICAS), dtype=np.float64)
    for skill in range(N_SKILLS):
        endpoint_s[:, skill, :] = g[:, skill, :, skill] - g[:, skill, :, :].mean(axis=-1)
    valid_assigned = assigned[context_valid]
    valid_between = between[context_valid]
    valid_within = within[context_valid]
    pooled_rows = valid_assigned.mean(axis=1) if len(valid_assigned) else np.zeros(0)
    return {
        "distances": distances,
        "branch_valid": branch_valid,
        "context_valid": context_valid,
        "support_ratio": float(context_valid.mean()),
        "g": g,
        "assigned": assigned,
        "between": between,
        "within": within,
        "assigned_mean_by_skill": valid_assigned.mean(axis=0) if len(valid_assigned) else np.zeros(N_SKILLS),
        "assigned_mean": float(pooled_rows.mean()) if len(pooled_rows) else 0.0,
        "assigned_interval": bootstrap_mean_interval(pooled_rows)
        if len(pooled_rows)
        else {"lower_95": 0.0, "mean": 0.0, "upper_95": 0.0},
        "rho_interval": bootstrap_ratio_interval(valid_between, valid_within)
        if len(valid_between)
        else {"lower_95": 0.0, "mean": 0.0, "upper_95": 0.0},
        "endpoint_s_mean": float(endpoint_s[context_valid].mean())
        if bool(np.any(context_valid))
        else 0.0,
    }


def dry_run_analysis(
    worker: dict[str, Any], arrays: dict[str, np.ndarray]
) -> dict[str, Any]:
    views = arrays["natural_views"]
    model = fit_spectral(views)
    centered = centered_for_model(model, views)
    null = temporal_null_eigenvalues(centered, repetitions=2)
    checks = {
        "scope": worker.get("scope") == "dry_run",
        "cuda": worker.get("device") == "cuda",
        "natural_windows": tuple(views.shape) == (16, K0, VIEW_DIM),
        "forced_branches": tuple(arrays["forced_views"].shape)
        == (1, N_SKILLS, REPLICAS, FORCED_HORIZON, VIEW_DIM),
        "forced_steps": int(arrays["forced_lengths"].sum()) == 320,
        "covariance_zero": float(np.max(np.abs(views[..., 4:7]))) <= 1e-7,
        "spectral_finite": bool(
            np.isfinite(model["eigenvalues"]).all()
            and np.isfinite(model["w0"]).all()
            and np.isfinite(null).all()
        ),
        "forced_finite": bool(np.isfinite(arrays["forced_views"]).all()),
        "snapshot_restore": worker["telemetry"].get("snapshot_restore_max_error") == 0.0,
        "parameter_drift_zero": worker.get("parameter_drift", {}).get("all_exact") is True,
        "reward_not_stored": not any("reward" in name.lower() for name in arrays),
    }
    if int(model["nontrivial_mode_count"]) >= N_SKILLS:
        branch_h10 = arrays["forced_views"].reshape(-1, FORCED_HORIZON, VIEW_DIM)[:, :K0]
        activations = mode_activations(model, branch_h10)
        branch_score_finite = bool(
            np.isfinite(window_mode_statistics(activations)["g"]).all()
        )
    else:
        branch_score_finite = False
    checks["branch_scores_finite"] = branch_score_finite
    return {
        "experiment_id": EXPERIMENT_ID,
        "scope": "dry_run",
        "dry_run_valid": bool(all(checks.values())),
        "checks": checks,
        "nontrivial_mode_count": int(model["nontrivial_mode_count"]),
        "null_replicates": 2,
        "scientific_thresholds_evaluated": False,
    }


def analyze_formal(worker: dict[str, Any], arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    invalid_reasons = validate_m0(worker, arrays)
    if invalid_reasons:
        return {
            "schema_version": SCHEMA_VERSION,
            "experiment_id": EXPERIMENT_ID,
            "status": "INVALID_R47_NSOPM_WIRING",
            "implementation_valid": False,
            "gates": {"M0": False, "M1": False, "M2": False},
            "M0": {"invalid_reasons": invalid_reasons},
            "authorized_next_action": "repair only the identified wiring defect and rerun unchanged",
        }

    views = arrays["natural_views"].astype(np.float64)
    groups = arrays["natural_group"].astype(np.int64)
    primary = fit_spectral(views[np.isin(groups, FIT_GROUPS)])
    half_a = fit_spectral(views[np.isin(groups, HALF_A_GROUPS)])
    half_b = fit_spectral(views[np.isin(groups, HALF_B_GROUPS)])
    model_counts = {
        "primary": int(primary["nontrivial_mode_count"]),
        "half_a": int(half_a["nontrivial_mode_count"]),
        "half_b": int(half_b["nontrivial_mode_count"]),
    }
    four_modes_available = all(count >= N_SKILLS for count in model_counts.values())

    if not four_modes_available:
        m1 = False
        m2 = False
        temporal: dict[str, Any] = {
            "four_modes_available": False,
            "model_nontrivial_mode_counts": model_counts,
            "registered_valid_failure_not_wiring": True,
        }
        nuisance: dict[str, Any] = {"not_evaluated": "fewer than four nontrivial modes"}
        causal: dict[str, Any] = {"not_evaluated": "fewer than four nontrivial modes"}
    else:
        temporal = temporal_and_stability_analysis(
            views, groups, primary, half_a, half_b
        )
        heldout_mask = np.isin(groups, HELDOUT_GROUPS)
        nuisance_x = nuisance_features(arrays, heldout_mask)
        nuisance = nuisance_ridge_audit(
            nuisance_x,
            temporal["primary_statistics"]["g"],
            groups[heldout_mask],
        )
        m1 = bool(
            np.all(temporal["eigenvalue_pass"])
            and float(np.min(temporal["stability"])) >= 0.70
            and all(
                interval["lower_95"] > 0.0
                for interval in temporal["coherence_intervals"]
            )
            and nuisance["maximum_r2"] < 0.10
        )

        heldout_distances = support_distances(primary, views[heldout_mask])
        support_threshold = float(
            np.quantile(heldout_distances.reshape(-1), SUPPORT_QUANTILE, method="linear")
        )
        forced = arrays["forced_views"].astype(np.float64)
        h10 = forced[..., :K0, :]
        h40_late = forced[..., 30:40, :]
        h10_result = causal_horizon_statistics(primary, h10, support_threshold)
        h40_result = causal_horizon_statistics(primary, h40_late, support_threshold)
        intersection = h10_result["context_valid"] & h40_result["context_valid"]
        if bool(np.any(intersection)):
            persistence_d10 = float(h10_result["assigned"][intersection].mean())
            persistence_d40 = float(h40_result["assigned"][intersection].mean())
            persistence = persistence_d40 / (persistence_d10 + 1e-8)
        else:
            persistence_d10 = 0.0
            persistence_d40 = 0.0
            persistence = 0.0
        m2 = bool(
            h10_result["support_ratio"] >= SUPPORT_RATIO_MIN
            and h40_result["support_ratio"] >= SUPPORT_RATIO_MIN
            and h10_result["assigned_interval"]["lower_95"] > 0.0
            and h40_result["assigned_interval"]["lower_95"] > 0.0
            and np.all(h40_result["assigned_mean_by_skill"] > 0.0)
            and h10_result["rho_interval"]["lower_95"] > 1.0
            and h40_result["rho_interval"]["lower_95"] > 1.0
            and persistence >= 0.50
        )
        causal = {
            "support_threshold_d2": support_threshold,
            "h10": {
                key: value
                for key, value in h10_result.items()
                if key
                not in {"distances", "branch_valid", "context_valid", "g", "assigned", "between", "within"}
            },
            "h40_late": {
                key: value
                for key, value in h40_result.items()
                if key
                not in {"distances", "branch_valid", "context_valid", "g", "assigned", "between", "within"}
            },
            "h10_complete_support_contexts": int(h10_result["context_valid"].sum()),
            "h40_complete_support_contexts": int(h40_result["context_valid"].sum()),
            "intersection_contexts": int(intersection.sum()),
            "persistence_intersection_d10": persistence_d10,
            "persistence_intersection_d40": persistence_d40,
            "persistence_ratio": persistence,
            "candidate_intrinsic_score_logged_only": True,
            "candidate_intrinsic_score_applied_to_reward": False,
        }

    m0 = True
    status = (
        "PASS_R47_NSOPM_IDENTIFIABILITY"
        if m1 and m2
        else "VALID_FAIL_R47_NSOPM"
    )
    next_action = (
        "authorize only probe_only versus real_reward with identical basis, collector, and low PPO"
        if status == "PASS_R47_NSOPM_IDENTIFIABILITY"
        else "permanently retire the exact R47 view, spectral basis, score, and reward-on pair without rescue"
    )
    temporal_summary = dict(temporal)
    for large_name in (
        "null_eigenvalues",
        "primary_activation",
        "primary_statistics",
        "real_coherence",
        "null_coherence",
    ):
        temporal_summary.pop(large_name, None)
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "implementation_valid": True,
        "gates": {"M0": m0, "M1": m1, "M2": m2},
        "authorized_next_action": next_action,
        "scope": "fixed-N=2 reward-off identifiability only; no task efficacy, S7, open-roster, or variable-N claim",
        "contract": {
            "natural_groups": NATURAL_GROUPS,
            "natural_windows": NATURAL_WINDOWS,
            "forced_contexts": CAUSAL_CONTEXTS,
            "forced_branches": FORCED_BRANCHES,
            "forced_steps": FORCED_STEPS,
            "view_dim": VIEW_DIM,
            "feature_dim": FEATURE_DIM,
            "lags": list(LAGS),
            "temporal_null_replicates": TEMPORAL_NULL_REPLICATES,
            "temporal_null_seed": TEMPORAL_NULL_SEED,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "optimizer_steps": 0,
            "external_reward_used": False,
        },
        "M0": {
            "invalid_reasons": [],
            "worker_telemetry": worker["telemetry"],
            "view": worker["view"],
            "parameter_drift": worker["parameter_drift"],
            "algorithm_boundary": worker["algorithm_boundary"],
        },
        "M1_natural_modes": {
            "passed": m1,
            "model_nontrivial_mode_counts": model_counts,
            "primary_retained_c00_rank": int(primary["retained_c00_rank"]),
            "primary_retained_c11_rank": int(primary["retained_c11_rank"]),
            "primary_gram_floor": float(primary["gram_floor"]),
            "temporal_and_stability": temporal_summary,
            "nuisance_audit": nuisance,
        },
        "M2_forced_skill_occupancy": {"passed": m2, **causal},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    worker = load_json(run_root / "seed" / "seed_result.json")
    arrays = load_evidence(run_root / "seed" / "r47_nsopm_evidence.npz")
    if args.dry_run:
        result = dry_run_analysis(worker, arrays)
        output = run_root / "result" / "dry_run_check.json"
        write_json(output, result)
        if not result["dry_run_valid"]:
            raise RuntimeError(f"R47 focused dry run failed: {result['checks']}")
        print(f"R47 focused dry run valid: {output}", flush=True)
        return
    result = analyze_formal(worker, arrays)
    output = run_root / "result" / "r47_nsopm.json"
    write_json(output, result)
    print(f"R47 analysis completed status={result['status']} output={output}", flush=True)


if __name__ == "__main__":
    main()
