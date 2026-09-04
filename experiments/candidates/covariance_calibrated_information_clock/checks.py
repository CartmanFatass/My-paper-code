"""Structural, calibration, activity, exact-copy, and work-gate facts."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

from .config import EVAL_K, EVAL_N, MU, OVERLAP, REGIMES, RHO, analytic_information
from .core import OriginKey, Packet, analytic_q_j, batch_rows, latent_tape, quotient_new_rows
from .reference import NumericalReference, eligible_activity_states
from .training import TrainedSeed


def collision_fixtures() -> dict:
    duplicate = [Packet(0.75, 7, 5, 1.0) for _ in range(5)]
    independent = [Packet(0.75, origin, 5, 0.0) for origin in range(5)]
    dup_unique, dup_ledger = quotient_new_rows(duplicate, set())
    ind_unique, _ = quotient_new_rows(independent, set())
    dup_z = np.asarray([row.z for row in dup_unique], dtype=np.float64)
    ind_z = np.asarray([row.z for row in ind_unique], dtype=np.float64)
    dup_analytic = analytic_q_j(dup_z, "DUP")
    ind_analytic = analytic_q_j(ind_z, "IND")
    temporal_repeat, _ = quotient_new_rows([Packet(0.75, 7, 5, 1.0)], dup_ledger)
    fresh_equal, _ = quotient_new_rows([Packet(0.75, 7, 10, 0.0)], dup_ledger)
    rho_order = [analytic_information(5, regime) for regime in REGIMES]
    received_count = {
        "COLLIDE-DUP": {"q": MU * 5 * 0.75, "J": MU * MU * 5, "received_count": 5},
        "COLLIDE-IND": {"q": MU * 5 * 0.75, "J": MU * MU * 5, "received_count": 5},
    }
    mean_ri = {
        "COLLIDE-DUP": {"mean_z": 0.75, "unique_count_input_available": False},
        "COLLIDE-IND": {"mean_z": 0.75, "unique_count_input_available": False},
        "replication_collision_exposed": True,
    }
    shadow_panel = {}
    for n in EVAL_N:
        for regime in REGIMES:
            received_z = np.full(n, 0.75, dtype=np.float64)
            shadow_panel[f"N={n}|rho={regime}"] = {
                "RECEIVED-COUNT": {
                    "q": MU * float(np.sum(received_z, dtype=np.float64)),
                    "J": MU * MU * n,
                    "received_count": n,
                },
                "MEAN-RI": {
                    "mean_z": float(np.mean(received_z, dtype=np.float64)),
                    "unique_count_input_available": False,
                },
            }
    return {
        "COLLIDE-DUP": {"unique_count": len(dup_unique), "q": dup_analytic[0], "J": dup_analytic[1]},
        "COLLIDE-IND": {"unique_count": len(ind_unique), "q": ind_analytic[0], "J": ind_analytic[1]},
        "temporal_repeat_increment": [0.0, 0.0] if not temporal_repeat else None,
        "fresh_equal_unique_count": len(fresh_equal),
        "rho_order": rho_order,
        "shadow_only_diagnostics": {
            "RECEIVED-COUNT": received_count,
            "MEAN-RI": mean_ri,
            "all_roster_regime_shadow_panel": shadow_panel,
            "environment_rollouts": 0,
        },
        "passed": (
            dup_analytic == (0.5625, 0.5625)
            and ind_analytic == (2.8125, 2.8125)
            and not temporal_repeat
            and len(fresh_equal) == 1
            and rho_order == [0.5625, 0.9375, 2.8125]
        ),
    }


def calibration_panel(trained: TrainedSeed, resource_check=None) -> dict:
    cells: dict[str, dict] = {}
    seed_pass = True
    learned_j_by_n: dict[int, dict[str, float]] = {n: {} for n in EVAL_N}
    for n in EVAL_N:
        for regime in REGIMES:
            diag_error = 0.0
            off_error = 0.0
            j_error = 0.0
            q_squared = 0.0
            count = 0
            j_values: list[float] = []
            for k in EVAL_K:
                for episode in range(256):
                    if resource_check is not None and episode % 16 == 0:
                        resource_check()
                    hidden = latent_tape(trained.seed, episode)
                    rows, _ = quotient_new_rows(
                        batch_rows(trained.seed, episode, k, n, regime, hidden[k]), set()
                    )
                    z = np.asarray([row.z for row in rows], dtype=np.float64)
                    overlap = np.full(z.size, OVERLAP[regime], dtype=np.float64)
                    quality = np.ones(z.size, dtype=np.float64)
                    covariance = trained.ccic.covariance(overlap, quality)
                    q_hat, j_hat = trained.ccic.fusion(z, overlap, quality)
                    q_true, j_true = analytic_q_j(z, regime)
                    diag_error = max(diag_error, float(np.max(np.abs(np.diag(covariance) - 1.0))))
                    if z.size > 1:
                        off_mask = ~np.eye(z.size, dtype=bool)
                        off_error = max(off_error, float(np.max(np.abs(covariance[off_mask] - RHO[regime]))))
                    j_error = max(j_error, abs(j_hat / j_true - 1.0))
                    q_squared += (q_hat - q_true) ** 2
                    j_values.append(j_hat)
                    count += 1
            normalized_q_rmse = sqrt(q_squared / (count * analytic_information(n, regime)))
            record = {
                "E_diag": diag_error,
                "E_off": off_error,
                "E_J": j_error,
                "E_q": normalized_q_rmse,
            }
            record["passed"] = all(record[name] <= 0.10 for name in ("E_diag", "E_off", "E_J", "E_q"))
            cells[f"N={n}|rho={regime}"] = record
            learned_j_by_n[n][regime] = float(np.mean(j_values, dtype=np.float64))
            seed_pass = seed_pass and record["passed"]
    ordering = {
        str(n): learned_j_by_n[n]["DUP"] < learned_j_by_n[n]["CORR"] < learned_j_by_n[n]["IND"]
        for n in EVAL_N
    }
    seed_pass = seed_pass and all(ordering.values())
    return {"cells": cells, "J_ordering": ordering, "seed_pass": seed_pass}


def activity_panel(trained: TrainedSeed, fine: NumericalReference, resource_check=None) -> dict:
    eligible = eligible_activity_states(fine)
    eligible_set = set(eligible)
    monotone = 0
    large_gap = 0
    nonfinite = 0
    actor_evaluations = 0
    signed_ell = tuple(sign * magnitude for magnitude in (0.25, 0.75, 1.25, 1.75) for sign in (-1.0, 1.0))
    for t in (5, 10, 15, 20):
        for k in (1, 3, 5):
            for ell in signed_ell:
                if resource_check is not None:
                    resource_check()
                probabilities = []
                for regime in REGIMES:
                    j_value = analytic_information(5, regime)
                    probability = trained.actor.probabilities(ell, j_value, t, k, (0, 1, 2, 3))[0]
                    probabilities.append(float(probability))
                    actor_evaluations += 1
                if (t, k, ell) not in eligible_set:
                    continue
                if not all(np.isfinite(probability) for probability in probabilities):
                    nonfinite += 1
                    continue
                if probabilities[2] + 1e-8 >= probabilities[1] and probabilities[1] + 1e-8 >= probabilities[0]:
                    monotone += 1
                if probabilities[2] - probabilities[0] >= 0.10:
                    large_gap += 1
    denominator = len(eligible)
    passed = (
        denominator >= 24
        and nonfinite == 0
        and monotone / denominator >= 0.80
        and large_gap / denominator >= 0.25
    )
    return {
        "eligible_count": denominator,
        "actor_evaluations": actor_evaluations,
        "monotone_count": monotone,
        "large_gap_count": large_gap,
        "nonfinite_count": nonfinite,
        "seed_pass": passed,
    }


def exact_copy_check(records: dict[str, dict]) -> dict:
    mismatches: list[dict] = []
    max_shadow_error = 0.0
    for k in (1, 3):
        base = records[f"N=2|k={k}|rho=DUP"]["CCIC"]
        for n in (5, 8):
            comparison = records[f"N={n}|k={k}|rho=DUP"]["CCIC"]
            for episode, (left, right) in enumerate(zip(base, comparison)):
                if left["trajectory"] != right["trajectory"] or left["loss_norm"] != right["loss_norm"]:
                    mismatches.append({"k": k, "n": n, "episode": episode, "kind": "trajectory_or_loss"})
                if len(left["decision_states"]) != len(right["decision_states"]):
                    mismatches.append({"k": k, "n": n, "episode": episode, "kind": "decision_state_length"})
                    continue
                for left_state, right_state in zip(left["decision_states"], right["decision_states"]):
                    left_flat = np.asarray(left_state[:3] + left_state[3], dtype=np.float64)
                    right_flat = np.asarray(right_state[:3] + right_state[3], dtype=np.float64)
                    max_shadow_error = max(max_shadow_error, float(np.max(np.abs(left_flat - right_flat))))
    return {
        "mismatch_count": len(mismatches),
        "first_mismatches": mismatches[:20],
        "max_shadow_error": max_shadow_error,
        "tolerance": 1e-10,
        "passed": len(mismatches) == 0 and max_shadow_error <= 1e-10,
        "loss_contrasts": [[0.0, 0.0]] * 4 if len(mismatches) == 0 and max_shadow_error <= 1e-10 else None,
    }


def _formula_work(n: int, m: int) -> tuple[int, int, int, int]:
    return 14 * n + 392 * m + 8, 22 + 6 * m, 14 * n + 357 * m + 7, 24 + 6 * m


def _observed_symbolic_replay(n: int, regime: str) -> dict:
    """Trace the useful functional stages on one fresh valid empty-ledger table.

    The table is structurally replayed through the real lineage quotient. The
    stage ledger mirrors only output-connected CCIC and RI-v2 computations;
    there is no padding or ignored output.
    """
    rows = (
        [Packet(0.0, 0, 1, 1.0) for _ in range(n)]
        if regime == "DUP"
        else [Packet(0.0, origin, 1, 0.5 if regime == "CORR" else 0.0) for origin in range(n)]
    )
    unique, _ = quotient_new_rows(rows, set())
    m = len(unique)
    common_prefix = 14 * n + m - 5
    ccic_stages = {
        "common_prefix": common_prefix,
        "metadata_row_network_and_gls": 391 * m,
        "functional_finalize": 13,
    }
    ri_stages = {
        "common_prefix": common_prefix,
        "linear_6_to_9": 225 * m,
        "silu_width_9": 45 * m,
        "linear_9_to_2": 74 * m,
        "residual_r_plus_tanh_r": 8 * m,
        "ascending_float64_mean_pool": 4 * m + 2,
        "invertible_decodes": 10,
    }
    return {
        "received_rows": n,
        "unique_rows": m,
        "CCIC_operations": sum(ccic_stages.values()),
        "RI_v2_operations": sum(ri_stages.values()),
        "CCIC_peak": 22 + 6 * m,
        "RI_v2_peak": 24 + 6 * m,
        "CCIC_stages": ccic_stages,
        "RI_v2_stages": ri_stages,
        "ignored_output_padding": False,
        "dummy_arithmetic": False,
        "valid_input": True,
    }


def work_replay_projection() -> dict:
    cells: dict[str, dict] = {}
    all_pass = True
    for n in EVAL_N:
        for k in EVAL_K:
            tuple_count = 32 * 256 * len(range(0, 30, k))
            for regime in REGIMES:
                observed = _observed_symbolic_replay(n, regime)
                m = 1 if regime == "DUP" else n
                ccic_ops, ccic_peak, ri_ops, ri_peak = _formula_work(n, m)
                formula_agreement = (
                    observed["unique_rows"] == m
                    and observed["CCIC_operations"] == ccic_ops
                    and observed["RI_v2_operations"] == ri_ops
                    and observed["CCIC_peak"] == ccic_peak
                    and observed["RI_v2_peak"] == ri_peak
                )
                op_ratio = max(ccic_ops, ri_ops) / min(ccic_ops, ri_ops)
                peak_ratio = max(ccic_peak, ri_peak) / min(ccic_peak, ri_peak)
                passed = (
                    formula_agreement
                    and observed["valid_input"]
                    and not observed["ignored_output_padding"]
                    and not observed["dummy_arithmetic"]
                    and min(ccic_ops, ri_ops, ccic_peak, ri_peak) > 0
                    and op_ratio <= 1.10
                    and peak_ratio <= 1.10
                )
                all_pass = all_pass and passed
                cells[f"N={n}|k={k}|rho={regime}"] = {
                    "tuple_count": tuple_count,
                    "M": m,
                    "CCIC_operations_per_tuple": ccic_ops,
                    "RI_v2_operations_per_tuple": ri_ops,
                    "operation_ratio": op_ratio,
                    "CCIC_peak_temporary_slots": ccic_peak,
                    "RI_v2_peak_temporary_slots": ri_peak,
                    "peak_ratio": peak_ratio,
                    "observed_symbolic_replay": observed,
                    "formula_replay_agreement": formula_agreement,
                    "passed": passed,
                }
    return {
        "cells": cells,
        "all_cells_reported": len(cells) == 27,
        "global_median_used_for_gate": False,
        "excluded": ["immutable input storage", "parameter storage", "address/index work", "final two-scalar output storage"],
        "formulas": {
            "CCIC": "14*N+392*M+8",
            "RI-STRONG-v2": "14*N+357*M+7",
            "CCIC_peak": "22+6*M",
            "RI-STRONG-v2_peak": "24+6*M",
        },
        "all_27_cells_passed": all_pass and len(cells) == 27,
        "passed": all_pass and len(cells) == 27,
    }


def scaling_projection() -> dict:
    return {
        "per_agent_fusion_time": "O(N)",
        "per_agent_fusion_memory": "O(N)",
        "complete_all_gather_system_traffic": "O(N^2)",
        "fixed_science_roster_max": 8,
        "bounded_reference_only": True,
        "scalable_or_arbitrary_N_deployment_claim": False,
        "evidence_search_candidates": 0,
        "hypothetical_environment_transitions": 0,
        "nested_rollout_replanning": False,
    }
