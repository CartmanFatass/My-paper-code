from __future__ import annotations

from dataclasses import dataclass

CANDIDATE = "SCDMP-TARGET-BOUND-ORDER-TO-VALUE"
REVISION = "SCDMP-TBOV-SCIENCE-20260815-07"
CARD_SHA256 = "fe3ab61aa438cecc4493eabed93efc9a5e962b1a21888781711b02dcbeedf9a0"
HMAC_SEED_NAMESPACE = b"SCDMP-TBOV-r06/STAGE-A/seed/"

EVENTS = ("C", "S+", "S-", "G+", "G-")
EVENT_TO_INDEX = {event: index for index, event in enumerate(EVENTS)}
ACTIONS = tuple(
    (fl, fr, rl, rr)
    for fl in (-1, 0, 1)
    for fr in (-1, 0, 1)
    for rl in (-1, 0, 1)
    for rr in (-1, 0, 1)
)
K_FIT = (4, 10)
K_TARGET = (6, 8, 12)
SEED_INDICES = tuple(range(10))
CHECKPOINT_FIT_ROWS = 4_096
FIT_SUPPORT_ROWS = 1_024
TARGET_BASE_ROWS = 256
LOGICAL_STEPS = 600
LOGICAL_BATCH_ROWS = 256
BATCHES_PER_EPOCH = 16
MODEL_PARAMETER_COUNT = 97_706
STATE_SCALE = (0.50, 0.30, 0.40, 0.24, 0.80, 0.40, 0.40, 0.40, 0.40)
STATE_BOUNDS = (
    (-0.25, 0.25), (-0.15, 0.15), (-0.20, 0.20),
    (-0.12, 0.12), (-0.40, 0.40),
    (-0.20, 0.20), (-0.20, 0.20), (-0.20, 0.20), (-0.20, 0.20),
)

DOMAIN_LABELS = (
    "checkpoint_fit/state", "checkpoint_fit/cells", "checkpoint_fit/action",
    "fit_support/state", "fit_support/cells", "fit_support/action",
    "target_k6/state", "target_k6/cells",
    "target_k8/state", "target_k8/cells",
    "target_k12/state", "target_k12/cells",
    "checkpoint_init", "checkpoint_minibatch",
)

PHYSICAL_NAMES = tuple(
    f"{metric}_k{k}" for metric in ("T", "R", "A") for k in K_TARGET
)
PHYSICAL_MARGINS = {
    **{f"T_k{k}": 0.12 for k in K_TARGET},
    **{f"R_k{k}": 0.06 for k in K_TARGET},
    **{f"A_k{k}": 1.0 for k in K_TARGET},
}
ASSAY_COMPONENTS = ("dF", "dR", "dQ")
ASSAY_MARGINS = {"dF": 0.20, "dR": 0.20, "dQ": 0.10}
BRANCHES = (
    "DELETE-FROM-OBJECT--PHYSICAL-OPPORTUNITY-EXCLUDED",
    "PHYSICAL-OPPORTUNITY-INDETERMINATE",
    "STAGE-A-ASSAY-DENOMINATOR-NONIDENTIFICATION",
    "MODIFY-CHECKPOINT",
    "ASSAY-ACTION-ADVERSE--DELETE-FROM-OBJECT",
    "SELECT-ORDER-TR",
    "MODIFY-TO-ORDER-Q",
    "ASSAY-NEGATIVE--DELETE-FROM-OBJECT",
    "ASSAY-INDETERMINATE",
)

PROSPECTIVE_COST = {
    "algorithm_seeds": 10,
    "adamw_steps": 6_000,
    "checkpoint_training_segment_examples": 49_920_000,
    "total_model_examples": 56_151_040,
    "lease_planning_hours": 12,
}


@dataclass(frozen=True)
class AdamWLaw:
    learning_rate: float = 3.0e-4
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1.0e-8
    weight_decay: float = 1.0e-5
    max_grad_norm: float = 1.0


ADAMW = AdamWLaw()


def static_contract() -> dict[str, object]:
    return {
        "candidate": CANDIDATE,
        "revision": REVISION,
        "card_sha256": CARD_SHA256,
        "stage": "STAGE_A_ONLY",
        "stage_b_implemented": False,
        "scientific_activity_started": False,
        "hmac_seed_namespace": HMAC_SEED_NAMESPACE.decode("ascii"),
        "seed_indices": list(SEED_INDICES),
        "fit_durations": list(K_FIT),
        "target_durations": list(K_TARGET),
        "row_counts": {
            "checkpoint_fit": CHECKPOINT_FIT_ROWS,
            "fit_support": FIT_SUPPORT_ROWS,
            "target_per_k": TARGET_BASE_ROWS,
        },
        "optimizer": {
            "steps": LOGICAL_STEPS,
            "batch_rows": LOGICAL_BATCH_ROWS,
            "batch_index": "b=n-1 for n=1,...,600",
            "checkpoint": "theta_600",
            **ADAMW.__dict__,
        },
        "model_parameter_count": MODEL_PARAMETER_COUNT,
        "branches": list(BRANCHES),
        "partial_selection_permitted": False,
        "prospective_cost": dict(PROSPECTIVE_COST),
    }
