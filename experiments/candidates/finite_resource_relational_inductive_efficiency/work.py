"""Deterministic FRRIE v2 planned and cumulative work accounting.

``flops`` below is a transparent, conventional static operation count.  It is
not a measurement of a processor, elapsed time, vector instructions, or the
data-dependent native simulator.  Native simulator exposure is instead
reported exactly in environment slots.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


LEARNED_ARMS = ("PHY_TRUST", "EDGE_FLEX")
SEED_BLOCK_COUNT = 24
UPDATES = 512
PARAMETER_COUNT = 35_513
PARAMETER_BYTES = PARAMETER_COUNT * 4

FLOP_ESTIMATOR_VERSION = "FRRIE_STATIC_FLOP_ESTIMATOR_V2"
FLOP_ESTIMATOR_FORMULA = "MODEL_AND_NATIVE_OPERATION_COUNT_NO_WALL_CLOCK_PROXY"
CUMULATIVE_CHECKPOINT_SCHEMA = "FRRIE_CUMULATIVE_CHECKPOINT_WORK_V2"
FINAL_CUMULATIVE_SCHEMA = "FRRIE_FINAL_CUMULATIVE_WORK_V2"
AGGREGATED_WORK_SCHEMA = "FRRIE_24_BLOCK_AGGREGATED_WORK_V2"

# Exact logical opportunity counts, per learned arm and per whole seed block.
FACTUAL_TRAIN_ENVIRONMENT_SLOTS = 512 * 64 * 12
FACTUAL_AUDITS_PER_EPISODE = 3
COUNTERFACTUAL_ALTERNATIVES_PER_EPISODE = 7
COUNTERFACTUAL_ALTERNATIVE_ENVIRONMENT_SLOTS = 1_490_944
FACTUAL_AUDIT_ENVIRONMENT_SLOTS = 638_976
ALTERNATIVE_SUFFIX_ENVIRONMENT_SLOTS = (
    COUNTERFACTUAL_ALTERNATIVE_ENVIRONMENT_SLOTS
    + FACTUAL_AUDIT_ENVIRONMENT_SLOTS
)
LEARNED_EVAL_ENVIRONMENT_SLOTS = 4 * 2 * 256 * 12
# The semantic rotation audit reuses an intact observation/incoming-hidden
# history. It invokes no native step and therefore consumes zero environment
# slots. Its batched policy calls remain real model work and are tracked under
# a deliberately different unit.
SHADOW_AUDIT_ENVIRONMENT_SLOTS = 0
SHADOW_AUDIT_ACTOR_STEPS = 2 * 256 * 12
ENVIRONMENT_SLOTS = (
    FACTUAL_TRAIN_ENVIRONMENT_SLOTS
    + ALTERNATIVE_SUFFIX_ENVIRONMENT_SLOTS
    + LEARNED_EVAL_ENVIRONMENT_SLOTS
)

BASE_POLICY_DECISIONS = 512 * 12 * (32 * 9 + 32 * 15)
COUNTERFACTUAL_ALTERNATIVE_FUTURE_ACTOR_STEPS = 512 * 64 * 7 * 11 // 2
COUNTERFACTUAL_ALTERNATIVE_FUTURE_POLICY_DECISIONS = 15_138_816
FACTUAL_AUDIT_FUTURE_ACTOR_STEPS = 540_672
FACTUAL_AUDIT_FUTURE_POLICY_DECISIONS = 6_488_064
SUFFIX_FUTURE_ACTOR_STEPS = (
    COUNTERFACTUAL_ALTERNATIVE_FUTURE_ACTOR_STEPS
    + FACTUAL_AUDIT_FUTURE_ACTOR_STEPS
)
SUFFIX_FUTURE_POLICY_DECISIONS = (
    COUNTERFACTUAL_ALTERNATIVE_FUTURE_POLICY_DECISIONS
    + FACTUAL_AUDIT_FUTURE_POLICY_DECISIONS
)
LEARNED_EVAL_POLICY_DECISIONS = 256 * 12 * 2 * (9 + 15 + 6 + 21)
SHADOW_AUDIT_POLICY_DECISIONS = 256 * 12 * (6 + 21)
LEARNED_DECISIONS = (
    BASE_POLICY_DECISIONS
    + SUFFIX_FUTURE_POLICY_DECISIONS
    + LEARNED_EVAL_POLICY_DECISIONS
    + SHADOW_AUDIT_POLICY_DECISIONS
)
EVALUATION_OPPORTUNITIES = 4 * 2 * 256


def _sum_operations(inventory: Mapping[str, int]) -> int:
    return sum(inventory.values())


# One row of the batched actor. Dot-product additions and explicit bias
# additions are deliberately distinct. A scalar exp/log/tanh/sigmoid/sqrt is
# one conventional nonlinearity; a scalar division is one conventional op.
_ACTOR_PER_DECISION = {
    # message encoder, GRU, action head, and the legal-uniform mixture
    "multiplications": 26_892,
    "additions": 26_533,
    "bias_additions": 294,
    "nonlinearities": 294,
    "divisions": 7,
}

# Fixed work in one batched relational aggregation. Role accumulation adds 32
# message elements per decision and is kept separate because batch N varies.
_AGGREGATION_PER_ACTOR_STEP = {
    "multiplications": 318,
    "additions": 243,
    "nonlinearities": 39,
    "divisions": 108,
}
_ROLE_ACCUMULATION_ADDITIONS_PER_DECISION = 32

# The critic MLP maps 66 -> 64 -> 64 -> 1. Role aggregation is expressed from
# the factual decision and slot counts below, rather than hiding roster N in a
# rounded per-slot average.
_CRITIC_MLP_PER_FACTUAL_SLOT = {
    "multiplications": 8_384,
    "additions": 8_255,
    "bias_additions": 129,
    "nonlinearities": 128,
}


def _actor_forward(decisions: int, actor_steps: int) -> int:
    return (
        decisions * _sum_operations(_ACTOR_PER_DECISION)
        + decisions * _ROLE_ACCUMULATION_ADDITIONS_PER_DECISION
        + actor_steps * _sum_operations(_AGGREGATION_PER_ACTOR_STEP)
    )


def _critic_forward() -> int:
    # For each role the implementation masks all N rows, reduces all N rows,
    # and divides its 22-element sum by the role count: 3 * 22 operations.
    role_aggregation = {
        "multiplications": 3 * 22 * BASE_POLICY_DECISIONS,
        "additions": 3 * 22 * (
            BASE_POLICY_DECISIONS - FACTUAL_TRAIN_ENVIRONMENT_SLOTS
        ),
        "divisions": 3 * 22 * FACTUAL_TRAIN_ENVIRONMENT_SLOTS,
    }
    return (
        _sum_operations(role_aggregation)
        + FACTUAL_TRAIN_ENVIRONMENT_SLOTS
        * _sum_operations(_CRITIC_MLP_PER_FACTUAL_SLOT)
    )


_FACTUAL_ACTOR_FORWARD = _actor_forward(
    BASE_POLICY_DECISIONS, FACTUAL_TRAIN_ENVIRONMENT_SLOTS
)
_FACTUAL_CRITIC_FORWARD = _critic_forward()
_FACTUAL_FORWARD = _FACTUAL_ACTOR_FORWARD + _FACTUAL_CRITIC_FORWARD
_BACKWARD_MULTIPLIER = 2
_FACTUAL_AUTOGRAD_BACKWARD = _BACKWARD_MULTIPLIER * _FACTUAL_FORWARD

_COUNTERFACTUAL_ALTERNATIVE_ACTOR_FORWARD = _actor_forward(
    COUNTERFACTUAL_ALTERNATIVE_FUTURE_POLICY_DECISIONS,
    COUNTERFACTUAL_ALTERNATIVE_FUTURE_ACTOR_STEPS,
)
_FACTUAL_AUDIT_ACTOR_FORWARD = _actor_forward(
    FACTUAL_AUDIT_FUTURE_POLICY_DECISIONS,
    FACTUAL_AUDIT_FUTURE_ACTOR_STEPS,
)
_EVAL_ACTOR_FORWARD = _actor_forward(
    LEARNED_EVAL_POLICY_DECISIONS, LEARNED_EVAL_ENVIRONMENT_SLOTS
)
_SHADOW_ACTOR_FORWARD = _actor_forward(
    SHADOW_AUDIT_POLICY_DECISIONS, SHADOW_AUDIT_ACTOR_STEPS
)

# Per update, global-norm work is P squares, P-1 reduction additions, one
# sqrt, epsilon addition and division, then P gradient scales.
_GRADIENT_NORM_AND_CLIP_PER_UPDATE = (
    2 * PARAMETER_COUNT + (PARAMETER_COUNT - 1) + 1 + 1 + 1
)
# Per update Adam uses, per parameter: six multiplies, four additions, three
# divisions, and one sqrt. The two bias-correction subtractions and two scalar
# powers are counted once per update.
_ADAM_PER_UPDATE = (
    6 * PARAMETER_COUNT
    + 4 * PARAMETER_COUNT
    + 3 * PARAMETER_COUNT
    + PARAMETER_COUNT
    + 2
    + 2
)
# Projection checks both bounds for each of the 18 beta values. Comparisons are
# conventional scalar operations here, not claimed IEEE floating additions.
_BETA_PROJECTION_PER_UPDATE = 2 * 18

_FLOP_COMPONENTS = {
    "factual_actor_forward": _FACTUAL_ACTOR_FORWARD,
    "factual_critic_forward": _FACTUAL_CRITIC_FORWARD,
    "factual_autograd_backward_convention": _FACTUAL_AUTOGRAD_BACKWARD,
    "counterfactual_alternative_actor_forward": _COUNTERFACTUAL_ALTERNATIVE_ACTOR_FORWARD,
    "factual_audit_actor_forward": _FACTUAL_AUDIT_ACTOR_FORWARD,
    "learned_evaluation_actor_forward": _EVAL_ACTOR_FORWARD,
    "shadow_audit_actor_forward": _SHADOW_ACTOR_FORWARD,
    "gradient_norm_and_clip": UPDATES * _GRADIENT_NORM_AND_CLIP_PER_UPDATE,
    "adam": UPDATES * _ADAM_PER_UPDATE,
    "beta_projection_bound_comparisons": UPDATES * _BETA_PROJECTION_PER_UPDATE,
}
_CHECKPOINT_COMPONENT_NAMES = (
    "factual_actor_forward",
    "factual_critic_forward",
    "factual_autograd_backward_convention",
    "counterfactual_alternative_actor_forward",
    "factual_audit_actor_forward",
    "gradient_norm_and_clip",
    "adam",
    "beta_projection_bound_comparisons",
)
CHECKPOINT_CONVENTIONAL_FLOPS = sum(
    _FLOP_COMPONENTS[name] for name in _CHECKPOINT_COMPONENT_NAMES
)
FINAL_CONVENTIONAL_FLOPS = sum(_FLOP_COMPONENTS.values())


FRRIE_STATIC_FLOP_ESTIMATOR_V2: dict[str, Any] = {
    "schema": FLOP_ESTIMATOR_VERSION,
    "kind": "DETERMINISTIC_CONVENTIONAL_OPERATION_COUNT_NOT_MEASURED_HARDWARE_FLOPS",
    "formula": FLOP_ESTIMATOR_FORMULA,
    "tensor_shapes": {
        "message_encoder": [[22, 64], [64, 32]],
        "gru_input": [55, 192],
        "gru_hidden_gates": [64, 64, 3],
        "action_head": [64, 6],
        "relational_roles": 3,
        "message_width": 32,
        "critic": [[66, 64], [64, 64], [64, 1]],
        "beta": [3, 3, 2],
        "parameter_count": PARAMETER_COUNT,
    },
    "primitive_convention": {
        "multiply": 1,
        "add_or_subtract": 1,
        "bias_add": 1,
        "divide": 1,
        "scalar_exp_log_tanh_sigmoid_or_sqrt": 1,
        "softmax_width": 6,
        "softmax_inventory": {"exp": 6, "reduction_add": 5, "divide": 6},
        "backward_multiplier_of_factual_actor_plus_critic_forward": _BACKWARD_MULTIPLIER,
        "projection_bound_comparison": 1,
    },
    "actor_per_decision": deepcopy(_ACTOR_PER_DECISION),
    "aggregation_per_actor_step": deepcopy(_AGGREGATION_PER_ACTOR_STEP),
    "role_accumulation_additions_per_decision": _ROLE_ACCUMULATION_ADDITIONS_PER_DECISION,
    "critic_mlp_per_factual_slot": deepcopy(_CRITIC_MLP_PER_FACTUAL_SLOT),
    "optimizer_per_update": {
        "gradient_norm_and_clip": _GRADIENT_NORM_AND_CLIP_PER_UPDATE,
        "adam": _ADAM_PER_UPDATE,
        "beta_projection_bound_comparisons": _BETA_PROJECTION_PER_UPDATE,
    },
    "suffix_inventory": {
        "factual_audits_per_episode": FACTUAL_AUDITS_PER_EPISODE,
        "counterfactual_alternatives_per_episode": COUNTERFACTUAL_ALTERNATIVES_PER_EPISODE,
        "counterfactual_alternative_environment_slots": COUNTERFACTUAL_ALTERNATIVE_ENVIRONMENT_SLOTS,
        "counterfactual_alternative_future_actor_steps": COUNTERFACTUAL_ALTERNATIVE_FUTURE_ACTOR_STEPS,
        "counterfactual_alternative_future_policy_decisions": COUNTERFACTUAL_ALTERNATIVE_FUTURE_POLICY_DECISIONS,
        "factual_audit_environment_slots": FACTUAL_AUDIT_ENVIRONMENT_SLOTS,
        "factual_audit_future_actor_steps": FACTUAL_AUDIT_FUTURE_ACTOR_STEPS,
        "factual_audit_future_policy_decisions": FACTUAL_AUDIT_FUTURE_POLICY_DECISIONS,
        "all_suffix_future_actor_steps": SUFFIX_FUTURE_ACTOR_STEPS,
        "all_suffix_future_policy_decisions": SUFFIX_FUTURE_POLICY_DECISIONS,
    },
    "per_arm_per_seed_block_components": deepcopy(_FLOP_COMPONENTS),
    "checkpoint_total_conventional_flops": CHECKPOINT_CONVENTIONAL_FLOPS,
    "final_total_conventional_flops": FINAL_CONVENTIONAL_FLOPS,
    "scope": {
        "counted": "MODEL_FORWARD_FACTUAL_AUTOGRAD_CONVENTION_OPTIMIZER_AND_PROJECTION",
        "native_environment": "EXACT_ENVIRONMENT_SLOTS_REPORTED_SEPARATELY",
        "excluded": "DATA_DEPENDENT_NATIVE_BRANCH_ARITHMETIC_MEMORY_IO_VECTOR_WIDTH_AND_WALL_CLOCK",
    },
}


_WORK_FIELDS = (
    "accounting_basis",
    "seed_block_count",
    "factual_train_environment_slots",
    "factual_audits_per_episode",
    "counterfactual_alternatives_per_episode",
    "counterfactual_alternative_environment_slots",
    "factual_audit_environment_slots",
    "alternative_suffix_environment_slots",
    "learned_eval_environment_slots",
    "environment_slots",
    "base_policy_decisions",
    "counterfactual_alternative_future_actor_steps",
    "counterfactual_alternative_future_policy_decisions",
    "factual_audit_future_actor_steps",
    "factual_audit_future_policy_decisions",
    "suffix_future_actor_steps",
    "suffix_future_policy_decisions",
    "learned_eval_policy_decisions",
    "shadow_audit_policy_decisions",
    "learned_decisions",
    "backward_calls",
    "adam_steps",
    "parameter_bytes",
    "flops",
    "flop_estimator_version",
    "flop_estimator_formula",
    "workers",
    "threads",
    "native_width",
    "dtype",
    "checkpoint_io",
    "evaluation_opportunities",
)


def _compute_bindings(compute: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(compute, Mapping):
        raise ValueError("compute must be a mapping")
    required = ("workers", "threads", "native_width", "model_dtype")
    if any(field not in compute for field in required):
        raise ValueError("compute lacks a work-accounting binding")
    for field in ("workers", "threads", "native_width"):
        if type(compute[field]) is not int or compute[field] <= 0:
            raise ValueError(f"compute.{field} must be a positive literal integer")
    if compute["model_dtype"] != "float32":
        raise ValueError("FRRIE work accounting requires compute.model_dtype float32")
    return {
        "workers": compute["workers"],
        "threads": compute["threads"],
        "native_width": compute["native_width"],
        "dtype": compute["model_dtype"],
    }


def _work_row(compute: Mapping[str, Any], *, final: bool) -> dict[str, Any]:
    bindings = _compute_bindings(compute)
    learned_eval_slots = LEARNED_EVAL_ENVIRONMENT_SLOTS if final else 0
    learned_eval_decisions = LEARNED_EVAL_POLICY_DECISIONS if final else 0
    shadow_decisions = SHADOW_AUDIT_POLICY_DECISIONS if final else 0
    return {
        "accounting_basis": "PER_LEARNED_ARM_PER_SEED_BLOCK",
        # This declares the prospective panel cardinality. It does not multiply
        # this per-block row; aggregate_seed_blocks is the sole multiplier.
        "seed_block_count": SEED_BLOCK_COUNT,
        "factual_train_environment_slots": FACTUAL_TRAIN_ENVIRONMENT_SLOTS,
        "factual_audits_per_episode": FACTUAL_AUDITS_PER_EPISODE,
        "counterfactual_alternatives_per_episode": COUNTERFACTUAL_ALTERNATIVES_PER_EPISODE,
        "counterfactual_alternative_environment_slots": COUNTERFACTUAL_ALTERNATIVE_ENVIRONMENT_SLOTS,
        "factual_audit_environment_slots": FACTUAL_AUDIT_ENVIRONMENT_SLOTS,
        "alternative_suffix_environment_slots": ALTERNATIVE_SUFFIX_ENVIRONMENT_SLOTS,
        "learned_eval_environment_slots": learned_eval_slots,
        "environment_slots": (
            FACTUAL_TRAIN_ENVIRONMENT_SLOTS
            + ALTERNATIVE_SUFFIX_ENVIRONMENT_SLOTS
            + learned_eval_slots
        ),
        "base_policy_decisions": BASE_POLICY_DECISIONS,
        "counterfactual_alternative_future_actor_steps": COUNTERFACTUAL_ALTERNATIVE_FUTURE_ACTOR_STEPS,
        "counterfactual_alternative_future_policy_decisions": COUNTERFACTUAL_ALTERNATIVE_FUTURE_POLICY_DECISIONS,
        "factual_audit_future_actor_steps": FACTUAL_AUDIT_FUTURE_ACTOR_STEPS,
        "factual_audit_future_policy_decisions": FACTUAL_AUDIT_FUTURE_POLICY_DECISIONS,
        "suffix_future_actor_steps": SUFFIX_FUTURE_ACTOR_STEPS,
        "suffix_future_policy_decisions": SUFFIX_FUTURE_POLICY_DECISIONS,
        "learned_eval_policy_decisions": learned_eval_decisions,
        "shadow_audit_policy_decisions": shadow_decisions,
        "learned_decisions": (
            BASE_POLICY_DECISIONS
            + SUFFIX_FUTURE_POLICY_DECISIONS
            + learned_eval_decisions
            + shadow_decisions
        ),
        "backward_calls": UPDATES,
        "adam_steps": UPDATES,
        "parameter_bytes": PARAMETER_BYTES,
        "flops": FINAL_CONVENTIONAL_FLOPS if final else CHECKPOINT_CONVENTIONAL_FLOPS,
        "flop_estimator_version": FLOP_ESTIMATOR_VERSION,
        "flop_estimator_formula": FLOP_ESTIMATOR_FORMULA,
        **bindings,
        "checkpoint_io": 1,
        "evaluation_opportunities": EVALUATION_OPPORTUNITIES if final else 0,
    }


def planned_work(compute: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Return exact full-panel work per learned arm and whole seed block."""

    row = _work_row(compute, final=True)
    return {arm: deepcopy(row) for arm in LEARNED_ARMS}


def checkpoint_cumulative_work(compute: Mapping[str, Any]) -> dict[str, Any]:
    """Return the sole post-update-512, pre-evaluation cumulative boundary."""

    row = _work_row(compute, final=False)
    return {
        "schema": CUMULATIVE_CHECKPOINT_SCHEMA,
        "boundary": "POST_UPDATE_512_PRE_EVALUATION",
        "training_update": UPDATES,
        "evaluation_checkpoint_cursor": 0,
        "arms": {arm: deepcopy(row) for arm in LEARNED_ARMS},
        "flop_components": {
            name: _FLOP_COMPONENTS[name] for name in _CHECKPOINT_COMPONENT_NAMES
        },
    }


def validate_cumulative_checkpoint_work(
    value: Mapping[str, Any], compute: Mapping[str, Any]
) -> dict[str, Any]:
    """Reject any mutation of the sole cumulative checkpoint work object."""

    if not isinstance(value, Mapping):
        raise ValueError("cumulative checkpoint work must be a mapping")
    expected = checkpoint_cumulative_work(compute)
    if dict(value) != expected:
        raise ValueError("cumulative checkpoint work differs from the exact v2 boundary")
    return deepcopy(expected)


def final_cumulative_work(compute: Mapping[str, Any]) -> dict[str, Any]:
    """Return cumulative work only after atomic complete-panel publication."""

    row = _work_row(compute, final=True)
    return {
        "schema": FINAL_CUMULATIVE_SCHEMA,
        "boundary": "COMPLETE_PANEL_PUBLISHED",
        "training_update": UPDATES,
        "evaluation_checkpoint_cursor": 1,
        "arms": {arm: deepcopy(row) for arm in LEARNED_ARMS},
        "flop_components": deepcopy(_FLOP_COMPONENTS),
    }


_BLOCK_ADDITIVE_FIELDS = (
    "factual_train_environment_slots",
    "counterfactual_alternative_environment_slots",
    "factual_audit_environment_slots",
    "alternative_suffix_environment_slots",
    "learned_eval_environment_slots",
    "environment_slots",
    "base_policy_decisions",
    "counterfactual_alternative_future_actor_steps",
    "counterfactual_alternative_future_policy_decisions",
    "factual_audit_future_actor_steps",
    "factual_audit_future_policy_decisions",
    "suffix_future_actor_steps",
    "suffix_future_policy_decisions",
    "learned_eval_policy_decisions",
    "shadow_audit_policy_decisions",
    "learned_decisions",
    "backward_calls",
    "adam_steps",
    "parameter_bytes",
    "flops",
    "checkpoint_io",
    "evaluation_opportunities",
)

# Exact additive resource totals for one learned arm over the entire registered
# panel.  These are intentionally separate from planned_work(): the latter is
# still one whole seed-block vector even though it declares that 24 blocks are
# prospectively required.
FRRIE_ALL_24_BLOCK_TOTALS_V2 = {
    "factual_train_environment_slots": FACTUAL_TRAIN_ENVIRONMENT_SLOTS * SEED_BLOCK_COUNT,
    "counterfactual_alternative_environment_slots": COUNTERFACTUAL_ALTERNATIVE_ENVIRONMENT_SLOTS * SEED_BLOCK_COUNT,
    "factual_audit_environment_slots": FACTUAL_AUDIT_ENVIRONMENT_SLOTS * SEED_BLOCK_COUNT,
    "alternative_suffix_environment_slots": ALTERNATIVE_SUFFIX_ENVIRONMENT_SLOTS * SEED_BLOCK_COUNT,
    "learned_eval_environment_slots": LEARNED_EVAL_ENVIRONMENT_SLOTS * SEED_BLOCK_COUNT,
    "environment_slots": ENVIRONMENT_SLOTS * SEED_BLOCK_COUNT,
    "base_policy_decisions": BASE_POLICY_DECISIONS * SEED_BLOCK_COUNT,
    "counterfactual_alternative_future_actor_steps": COUNTERFACTUAL_ALTERNATIVE_FUTURE_ACTOR_STEPS * SEED_BLOCK_COUNT,
    "counterfactual_alternative_future_policy_decisions": COUNTERFACTUAL_ALTERNATIVE_FUTURE_POLICY_DECISIONS * SEED_BLOCK_COUNT,
    "factual_audit_future_actor_steps": FACTUAL_AUDIT_FUTURE_ACTOR_STEPS * SEED_BLOCK_COUNT,
    "factual_audit_future_policy_decisions": FACTUAL_AUDIT_FUTURE_POLICY_DECISIONS * SEED_BLOCK_COUNT,
    "suffix_future_actor_steps": SUFFIX_FUTURE_ACTOR_STEPS * SEED_BLOCK_COUNT,
    "suffix_future_policy_decisions": SUFFIX_FUTURE_POLICY_DECISIONS * SEED_BLOCK_COUNT,
    "learned_eval_policy_decisions": LEARNED_EVAL_POLICY_DECISIONS * SEED_BLOCK_COUNT,
    "shadow_audit_policy_decisions": SHADOW_AUDIT_POLICY_DECISIONS * SEED_BLOCK_COUNT,
    "learned_decisions": LEARNED_DECISIONS * SEED_BLOCK_COUNT,
    "backward_calls": UPDATES * SEED_BLOCK_COUNT,
    "adam_steps": UPDATES * SEED_BLOCK_COUNT,
    "parameter_bytes": PARAMETER_BYTES * SEED_BLOCK_COUNT,
    "flops": FINAL_CONVENTIONAL_FLOPS * SEED_BLOCK_COUNT,
    "checkpoint_io": SEED_BLOCK_COUNT,
    "evaluation_opportunities": EVALUATION_OPPORTUNITIES * SEED_BLOCK_COUNT,
}


def aggregate_seed_blocks(
    per_block_work: Mapping[str, Mapping[str, Any]],
    block_count: int = SEED_BLOCK_COUNT,
) -> dict[str, Any]:
    """Explicitly aggregate the per-block arm vectors over exactly 24 blocks."""

    if type(block_count) is not int or block_count != SEED_BLOCK_COUNT:
        raise ValueError("FRRIE v2 aggregation requires exactly 24 seed blocks")
    if not isinstance(per_block_work, Mapping) or set(per_block_work) != set(LEARNED_ARMS):
        raise ValueError("per-block work must bind exactly both learned arms")
    if dict(per_block_work[LEARNED_ARMS[0]]) != dict(per_block_work[LEARNED_ARMS[1]]):
        raise ValueError("learned-arm work must remain exactly symmetric")
    rows: dict[str, dict[str, Any]] = {}
    for arm in LEARNED_ARMS:
        source = per_block_work[arm]
        if not isinstance(source, Mapping) or set(source) != set(_WORK_FIELDS):
            raise ValueError("per-block work fields differ from the exact v2 vector")
        if source["accounting_basis"] != "PER_LEARNED_ARM_PER_SEED_BLOCK":
            raise ValueError("only per-learned-arm/per-seed-block work may be aggregated")
        row = deepcopy(dict(source))
        row["accounting_basis"] = "PER_LEARNED_ARM_ALL_24_SEED_BLOCKS"
        row["seed_block_count"] = SEED_BLOCK_COUNT
        for field in _BLOCK_ADDITIVE_FIELDS:
            if type(source[field]) is not int or source[field] < 0:
                raise ValueError(f"per-block work.{field} must be a nonnegative integer")
            row[field] = source[field] * SEED_BLOCK_COUNT
            if row[field] != FRRIE_ALL_24_BLOCK_TOTALS_V2[field]:
                raise ValueError(
                    "per-block work is not the exact registered vector for 24-block aggregation"
                )
        rows[arm] = row
    if rows[LEARNED_ARMS[0]] != rows[LEARNED_ARMS[1]]:
        raise ValueError("learned-arm work must remain exactly symmetric")
    return {
        "schema": AGGREGATED_WORK_SCHEMA,
        "seed_block_count": SEED_BLOCK_COUNT,
        "arms": rows,
    }
