"""Frozen Stage-1 configuration for VSP06-B2R2.

No policy, model, learner, optimizer, evaluator, environment, RNG, manifest, or
full-execution implementation is present in this Stage-1 module.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Mapping


DIRECTION_ID = "CAND-VSP-06-MSSR"
CANDIDATE_ID = "CAND-VSP-06-MSSR@adversarial-revision-v9"
TREATMENT_ID = (
    "VSP06-B2R2-AUTHENTICATED-PARTNER-RECALL-CREDIT-EFFICIENCY-"
    "SOURCE-BOUND-SYMMETRY-GUARANTEED-EXACT-FEASIBILITY"
)
SELECTOR_ID = "VSP06-B2R2-SB-SG-EF-CP-SAT-V1"
VERIFIER_ID = "VSP06-B2R2-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1"
SCIENTIFIC_PARENT = "898af9e848ce45f3510560a96ae454651a9f0736"
IMMEDIATE_PREDECESSOR_IMPLEMENTATION = "7d37be4ff33b2ba4984074383a719390e2cce6b0"

FORMAL = False
K_SEARCH = 0
HYPOTHETICAL_TRANSITIONS = 0
STAGE1_STATUS = "SYNTHETIC_STRUCTURAL_VALID_ONLY"
PRECLAIM_TECHNICAL_FAILURE = "B2R2_SELECTOR_INVALID_NO_RUN"
POST_ACTIVITY_FAILURE = "B2R2_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
SEALED_SELECTOR = "B2R2_SELECTOR_VERIFIED_MANIFEST_FIXED"

THRESHOLDS = {
    "candidate_minus_generic_keep_aulc": 0.08,
    "candidate_final_keep": 0.55,
    "selected_p_mediation": 0.20,
    "selected_p_cross_swap_follow": 0.80,
    "absolute_decoy_accuracy_change": 0.02,
    "decoy_kernel_tv_change": 0.02,
    "maximum_per_seed_current_arm_aulc_gap": 0.05,
    "mean_reset_stale_target_rate": 0.15,
}

CAPS = {
    "fits": 10,
    "trainer_invocations": 10,
    "episodes": 44_300,
    "transitions": 520_000,
    "production_policy_forwards": 540_000,
    "learner_updates": 1_100,
    "optimizer_steps": 1_100,
    "evaluator_calls": 75,
    "evaluation_episodes": 10_500,
    "sweeps": 0,
    "retries": 0,
    "rescues": 0,
    "extra_roots": 0,
}

PROSPECTIVE_ENVIRONMENT = {
    "python": "3.11",
    "ortools": "9.12.4544",
    "torch": "2.7.0",
    "torch_device": "cpu",
    "torch_deterministic_algorithms": True,
    "torch_intra_op_threads": 1,
    "torch_inter_op_threads": 1,
}

INVALID = "B2R2_INVALID_CONTRACT_ACTIVITY_CAP_OR_PROVENANCE"
NAVIGATION_FAIL = "B2R2_NAVIGATION_OR_CANDIDATE_FINAL_KEEP_GATE_FAILS"
MEDIATION_FAIL = "B2R2_SELECTED_P_MEDIATION_GATE_FAILS"
CROSS_SWAP_FAIL = "B2R2_SELECTED_P_CROSS_SWAP_GATE_FAILS"
DECOY_FAIL = "B2R2_DECOY_INVARIANCE_GATE_FAILS"
CURRENT_RESET_FAIL = "B2R2_CURRENT_OR_RESET_CONTROL_GATE_FAILS"
NOT_SUPPORTED = "B2R2_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_NOT_SUPPORTED"
SUPPORTED = "B2R2_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_SUPPORTED"
BRANCH_PRECEDENCE = (
    INVALID,
    NAVIGATION_FAIL,
    MEDIATION_FAIL,
    CROSS_SWAP_FAIL,
    DECOY_FAIL,
    CURRENT_RESET_FAIL,
    NOT_SUPPORTED,
    SUPPORTED,
)

ACTIVITY_FIELDS = (
    "canonical_rows_enumerated",
    "cp_sat_processes",
    "cp_sat_models",
    "canonical_selector_invocations",
    "canonical_verifier_invocations",
    "witnesses_created",
    "manifests_created",
    "model_loads",
    "environment_creations",
    "environment_episodes",
    "environment_transitions",
    "production_policy_forwards",
    "learner_updates",
    "optimizer_steps",
    "evaluator_calls",
    "evaluation_episodes",
    "rng_draws",
    "fits",
    "trainer_invocations",
    "registered_full_invocations",
    "result_outputs",
    "readiness_outputs",
)

FRESH_SOURCE_PATHS = (
    "experiments/candidates/vsp_06_mssr/vsp06_b2r2_source_bound_symmetry_guaranteed_exact_feasibility.py",
    "experiments/candidates/vsp_06_mssr/vsp06_b2r2_independent_exact_manifest_verifier.py",
    "experiments/candidates/vsp_06_mssr/vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py",
    "scripts/run_vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py",
    "tests/experiments/candidates/vsp_06_mssr/test_vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py",
    "docs/research/candidates/vsp_06_mssr/VSP06_B2R2_CONSTRAINT_TARGET_LEDGER_V1.json",
    "docs/research/candidates/vsp_06_mssr/VSP06_B2R2_CODE_SCIENCE_INDEX.md",
)

RESERVED_CANONICAL_PATHS = (
    "docs/research/candidates/vsp_06_mssr/VSP06_B2R2_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_RESULT.json",
    "temp/sessions/code_project_manager/vsp06_b2r2_authenticated_partner_recall_credit_efficiency",
    "temp/sessions/experiment_operator/vsp06_b2r2_authenticated_partner_recall_credit_efficiency/operator_receipt.json",
    "temp/sessions/code_project_manager/vsp06_b2r2_authenticated_partner_recall_credit_efficiency/canonical_catalog.json",
    "temp/sessions/code_project_manager/vsp06_b2r2_authenticated_partner_recall_credit_efficiency/selector/membership_witness.json",
    "temp/sessions/code_project_manager/vsp06_b2r2_authenticated_partner_recall_credit_efficiency/frozen_manifest.json",
    "temp/sessions/code_project_manager/vsp06_b2r2_authenticated_partner_recall_credit_efficiency/environment",
    "temp/sessions/code_project_manager/vsp06_b2r2_authenticated_partner_recall_credit_efficiency/readiness",
)


class Stage1ConfigurationError(RuntimeError):
    """The frozen Stage-1 contract or path provenance failed closed."""


def zero_activity_counts() -> dict[str, int]:
    return {name: 0 for name in ACTIVITY_FIELDS}


def validate_zero_activity(counts: Mapping[str, Any]) -> None:
    if not isinstance(counts, Mapping) or tuple(counts) != ACTIVITY_FIELDS:
        raise Stage1ConfigurationError("activity counter schema changed")
    if any(isinstance(value, bool) or not isinstance(value, int) or value != 0 for value in counts.values()):
        raise Stage1ConfigurationError("Stage 1 requires every activity counter to remain zero")


def guard_source_path(path: str) -> str:
    if not isinstance(path, str) or "\\" in path:
        raise Stage1ConfigurationError("source path must be a repository-relative POSIX path")
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts or path not in FRESH_SOURCE_PATHS:
        raise Stage1ConfigurationError("path is outside the fresh Stage-1 allowlist")
    return path


def guard_reserved_path(path: str) -> str:
    if not isinstance(path, str) or "\\" in path:
        raise Stage1ConfigurationError("reserved path must be repository-relative POSIX text")
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts or path not in RESERVED_CANONICAL_PATHS:
        raise Stage1ConfigurationError("path is outside the reserved canonical allowlist")
    return path


def validate_fresh_identities(values: Mapping[str, str]) -> None:
    expected = {
        "direction": DIRECTION_ID,
        "candidate": CANDIDATE_ID,
        "treatment": TREATMENT_ID,
        "selector": SELECTOR_ID,
        "verifier": VERIFIER_ID,
        "scientific_parent": SCIENTIFIC_PARENT,
        "immediate_predecessor_implementation": IMMEDIATE_PREDECESSOR_IMPLEMENTATION,
    }
    if values != expected:
        raise Stage1ConfigurationError("fresh identity binding mismatch")


def stage1_contract() -> dict[str, Any]:
    counts = zero_activity_counts()
    validate_zero_activity(counts)
    return {
        "status": STAGE1_STATUS,
        "direction": DIRECTION_ID,
        "candidate": CANDIDATE_ID,
        "treatment": TREATMENT_ID,
        "selector": SELECTOR_ID,
        "verifier": VERIFIER_ID,
        "scientific_parent": SCIENTIFIC_PARENT,
        "immediate_predecessor_implementation": IMMEDIATE_PREDECESSOR_IMPLEMENTATION,
        "formal": FORMAL,
        "K_search": K_SEARCH,
        "hypothetical_transitions": HYPOTHETICAL_TRANSITIONS,
        "thresholds": dict(THRESHOLDS),
        "caps": dict(CAPS),
        "prospective_environment": dict(PROSPECTIVE_ENVIRONMENT),
        "branch_precedence": BRANCH_PRECEDENCE,
        "activity_counts": counts,
        "fresh_source_paths": FRESH_SOURCE_PATHS,
        "reserved_canonical_paths": RESERVED_CANONICAL_PATHS,
        "canonical_readiness": False,
        "scientific_claim": None,
    }


__all__ = [
    "Stage1ConfigurationError", "THRESHOLDS", "CAPS", "BRANCH_PRECEDENCE",
    "FRESH_SOURCE_PATHS", "RESERVED_CANONICAL_PATHS", "zero_activity_counts",
    "validate_zero_activity", "guard_source_path", "guard_reserved_path",
    "validate_fresh_identities", "stage1_contract",
]
