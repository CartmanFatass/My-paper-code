"""Machine-readable preactivity conformance certificate construction."""

from __future__ import annotations

import inspect

import numpy as np

from .checks import collision_fixtures, scaling_projection, work_replay_projection
from .config import (
    ACTIONS,
    COARSE_GRID,
    EVAL_K,
    EVAL_N,
    FINE_GRID,
    HORIZON,
    J_SHUFFLE_CLASSES,
    MAX_OPTIMIZER_UPDATES,
    MAX_PRIMITIVE_TICKS,
    MAX_RSS_BYTES,
    MAX_THREADS,
    MAX_WALL_MINUTES,
    MU,
    PACKET_METADATA_BITS,
    PACKET_REAL_SYMBOLS,
    REGIMES,
    REVISION,
    ROLLOUT_ARMS,
    ROLLOUT_TICK_BOUND,
    SEED_BLOCKS,
    SNAPSHOT_DRAW_BOUND,
    STREAMS,
    TIE_PRIORITY,
    TRAIN_K,
    TRAIN_N,
    analytic_information,
    shuffled_class,
)
from .models import CCICModel
from .reference import NumericalReference, compare_references, eligible_activity_states, reference_gap


def _replication_identity() -> dict:
    maximum_error = 0.0
    cases = 0
    for n, groups in ((2, (0, 0)), (5, (0, 1, 1, 2, 2)), (8, (0, 0, 1, 1, 2, 2, 3, 3))):
        m = max(groups) + 1
        replication = np.zeros((n, m), dtype=np.float64)
        for row, column in enumerate(groups):
            replication[row, column] = 1.0
        base = 0.5 * np.eye(m, dtype=np.float64) + 0.5 * np.ones((m, m), dtype=np.float64)
        left = replication.T @ np.linalg.pinv(replication @ base @ replication.T) @ replication
        error = float(np.max(np.abs(left - np.linalg.inv(base))))
        maximum_error = max(maximum_error, error)
        cases += 1
    return {
        "full_column_rank_support_cases": cases,
        "maximum_abs_error": maximum_error,
        "off_support_nugget_used": False,
        "passed": maximum_error <= 1e-10,
    }


def build_preactivity_certificate(fine: NumericalReference, coarse: NumericalReference) -> dict:
    information_table = {
        str(n): {regime: analytic_information(n, regime) for regime in REGIMES}
        for n in EVAL_N
    }
    reference_comparison = compare_references(fine, coarse)
    fine_gap = reference_gap(fine)
    coarse_gap = reference_gap(coarse)
    eligible = eligible_activity_states(fine)
    covariance_signature = tuple(inspect.signature(CCICModel.row_parameters).parameters)
    covariance_source = inspect.getsource(CCICModel.row_parameters)
    feature_trace = {
        "method_parameters": covariance_signature,
        "allowed_inputs": CCICModel.allowed_inputs,
        "forbidden_inputs": CCICModel.forbidden_inputs,
        "forbidden_intersection": sorted(set(covariance_signature) & set(CCICModel.forbidden_inputs)),
    }
    shuffle_map = {
        f"{n}:{regime}": f"{shuffled_class(n, regime)[0]}:{shuffled_class(n, regime)[1]}"
        for n, regime in J_SHUFFLE_CLASSES
    }
    resources = {
        "wall_minutes_ceiling": MAX_WALL_MINUTES,
        "peak_rss_bytes_ceiling": MAX_RSS_BYTES,
        "cpu_threads_ceiling": MAX_THREADS,
        "learned_optimizer_updates": MAX_OPTIMIZER_UPDATES,
        "primitive_tick_ceiling": MAX_PRIMITIVE_TICKS,
        "eight_arm_evaluation_tick_bound": ROLLOUT_TICK_BOUND,
        "snapshot_draw_bound": SNAPSHOT_DRAW_BOUND,
        "eight_full_rollout_arms": list(ROLLOUT_ARMS),
        "shadow_only": ["RECEIVED-COUNT", "MEAN-RI"],
    }
    work_projection = work_replay_projection()
    checks = {
        "revision": REVISION == "CCIC-B1-SCIENCE-20260813-06",
        "dgp": HORIZON == 30 and MU == 0.75 and TRAIN_N == (2, 5) and TRAIN_K == (1, 3),
        "axes": EVAL_N == (2, 5, 8) and EVAL_K == (1, 3, 5) and REGIMES == ("DUP", "CORR", "IND"),
        "seeds_and_counts": SEED_BLOCKS == 32,
        "packet_schema": PACKET_REAL_SYMBOLS == 1 and PACKET_METADATA_BITS == 64,
        "tie_priority": TIE_PRIORITY == ("SENSE", "RELAY", "COMMIT_PLUS", "COMMIT_MINUS"),
        "analytic_information": information_table == {
            "2": {"DUP": 0.5625, "CORR": 0.75, "IND": 1.125},
            "5": {"DUP": 0.5625, "CORR": 0.9375, "IND": 2.8125},
            "8": {"DUP": 0.5625, "CORR": 1.0, "IND": 4.5},
        },
        "replication_identity": _replication_identity()["passed"],
        "latin_u_literal": "u = softplus(b)" in covariance_source and "nu_i" not in covariance_source,
        "forbidden_input_trace": not feature_trace["forbidden_intersection"],
        "collision_fixtures": collision_fixtures()["passed"],
        "reference_stability": reference_comparison["passed"],
        "reference_gap": fine_gap >= 0.01 and coarse_gap >= 0.01,
        "eligible_activity_states": len(eligible) >= 24,
        "shuffle_successor_permutation": len(set(shuffle_map.values())) == 9,
        "resource_projection": (
            MAX_OPTIMIZER_UPDATES == 240_000
            and ROLLOUT_TICK_BOUND == 53_084_160
            and SNAPSHOT_DRAW_BOUND == 294_912
            and ROLLOUT_TICK_BOUND + SNAPSHOT_DRAW_BOUND < MAX_PRIMITIVE_TICKS
        ),
        "work_projection_passed": (
            len(work_projection["cells"]) == 27
            and work_projection["all_27_cells_passed"]
            and work_projection["passed"]
            and all(cell["formula_replay_agreement"] and cell["passed"] for cell in work_projection["cells"].values())
        ),
        "complexity_policy": scaling_projection()["hypothetical_environment_transitions"] == 0,
    }
    return {
        "revision": REVISION,
        "certificate_kind": "preactivity_conformance",
        "scientific_activity_started": False,
        "ideal_real_channel": {
            "real_symbols_per_row": 1,
            "metadata_bits_per_row": 64,
            "finite_word_gaussian_likelihood_claim": False,
        },
        "information_table": information_table,
        "replication_identity": _replication_identity(),
        "covariance_feature_trace": feature_trace,
        "latin_loading": "u_i := softplus(b_i)",
        "collision_fixtures": collision_fixtures(),
        "reference_stability": reference_comparison,
        "reference_gaps": {"fine": fine_gap, "coarse": coarse_gap, "minimum": 0.01},
        "activity_base_states": 96,
        "activity_actor_evaluations_per_seed": 288,
        "eligible_activity_state_count": len(eligible),
        "philox_streams": STREAMS,
        "j_shuffle_successor_map": shuffle_map,
        "exact_copy_pathwise_proof": {
            "DUP_quotient": "all N in {2,5,8} map to the same origin-zero single-row table",
            "nested_tapes": "latent, origin-zero idiosyncratic, and public-action addresses omit N",
            "canonical_post_quotient_order": "ascending (origin_id,capture_tick)",
            "same_actor_and_operation_order": True,
            "paired_runtime_check_required": True,
        },
        "work_replay_contract": work_projection,
        "answerability_paths": {
            "reference_and_actor_headroom_fail_closed": True,
            "all_lineage_regime_cells_reached_by_nested_tapes": True,
            "shuffle_and_clamp_use_shared_legal_actor": True,
            "RI_STRONG_v2_training_and_execution_are_functional": True,
            "all_cell_useful_work_required_before_activity": True,
            "partial_or_missing_seed_blocks_excluded_from_inference": True,
        },
        "scaling_projection": scaling_projection(),
        "resources": resources,
        "checks": checks,
        "passed": all(checks.values()),
    }
