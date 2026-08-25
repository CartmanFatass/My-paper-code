from __future__ import annotations

from .config import CANDIDATE, MICROSTEP_LEDGER, MICROSTEP_MAXIMUM, REVISION
from .lifecycle import Lifecycle


def incomplete_result(
    lifecycle: Lifecycle,
    *,
    reason: str,
    static_conformance: dict[str, object],
    partial: dict[str, object] | None = None,
    resource_actuals: dict[str, object] | None = None,
    activity_sidecar: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "artifact_kind": "SCDMP_B1_V5_LIFECYCLE_RESULT",
        "candidate": CANDIDATE,
        "revision": REVISION,
        "status": "incomplete",
        "reason": reason,
        "lifecycle": lifecycle.facts(),
        "question_relevant_output_exists": False,
        "scientific_interpretation_permitted": False,
        "cm_technical_acceptance_required": True,
        "static_conformance": static_conformance,
        "partial_output": partial,
        "seed_regime_effects": None,
        "model_actor_first_stages": None,
        "oracle_headroom_regret": None,
        "real_sham_order_checks": None,
        "adverse_bound_family": None,
        "resource_actuals": resource_actuals,
        "activity_sidecar": activity_sidecar,
        "anomalies": [reason],
    }


def complete_result_packet(
    lifecycle: Lifecycle,
    *,
    static_conformance: dict[str, object],
    seeds: list[dict[str, object]],
    inference: dict[str, object],
    resource_actuals: dict[str, object],
    microsteps: dict[str, int],
    activity_sidecar: dict[str, object],
) -> dict[str, object]:
    if [int(item["algorithm_seed"]) for item in seeds] != list(range(8)):
        raise RuntimeError("complete packet requires all eight seed payloads in order")
    if microsteps != MICROSTEP_LEDGER or sum(microsteps.values()) != MICROSTEP_MAXIMUM:
        raise RuntimeError("complete packet requires the exact immutable microstep ledger")
    if int(inference["adverse_family"]["count"]) != 12:
        raise RuntimeError("complete packet requires the exact twelve-member adverse family")
    if "gate_facts" not in inference or "main_estimands" not in inference:
        raise RuntimeError("complete packet requires all registered gate facts and bounds")
    physical_factor_steps = {
        category: sum(
            int(seed["audit"]["true_panel_evaluation"]["physical_factor_steps"][category])
            for seed in seeds
        )
        for category in ("audit_target_words", "audit_reverse_twins")
    }
    lifecycle.complete_result(completed_seeds=list(range(8)))
    return {
        "artifact_kind": "SCDMP_B1_V5_COMPLETE_RESULT",
        "candidate": CANDIDATE,
        "revision": REVISION,
        "status": "complete_question_relevant_output_pending_cm_acceptance",
        "lifecycle": lifecycle.facts(),
        "question_relevant_output_exists": True,
        "scientific_interpretation_permitted": False,
        "cm_technical_acceptance_required": True,
        "static_conformance": static_conformance,
        "per_seed": seeds,
        "seed_regime_effects": inference["scored"],
        "model_actor_first_stages": inference["audit_seed_vectors"],
        "oracle_headroom_regret": {
            "per_seed": [item["audit"]["arms"] for item in seeds],
            "seed_vectors": inference["audit_seed_vectors"]["headroom_regret"],
        },
        "real_sham_order_checks": [
            item["audit"]["physical_order_and_sham_identity"] for item in seeds
        ],
        "inference": inference,
        "adverse_bound_family": inference["adverse_family"],
        "resource_actuals": resource_actuals,
        "activity_sidecar": activity_sidecar,
        "registered_analytic_panel_microstep_ledger": microsteps,
        "physical_execution_accounting": {
            "full_joint_environment_steps": {
                "common_training_corpus": MICROSTEP_LEDGER["common_training_corpus"],
                "scored_evaluation": MICROSTEP_LEDGER["scored_evaluation"],
                "common_audit_warmup": MICROSTEP_LEDGER["common_audit_warmup"],
                "audit_target_words": 0,
                "audit_reverse_twins": 0,
            },
            "audit_scalar_agent_factor_transitions": physical_factor_steps,
            "note": (
                "The frozen 81-action audit denominators and ledger are evaluated exactly by "
                "analytic node/edge factors. Audit panel construction advances scalar-agent "
                "factor trajectories, not 81 full joint environments."
            ),
        },
        "anomalies": [],
        "interpretation": None,
        "interpretation_owner": "EM_semigroup_consistent_duration_model_policy_after_CM_acceptance",
    }
