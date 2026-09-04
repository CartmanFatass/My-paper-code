"""Frozen production inventory and preactivity fences for DISH RBHR r05.

This module contains no activity identity, master, coordinate, lease, model, or
result.  It is safe to import during construction and TEST-only measurement.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping


SCIENCE_REVISION: Final = "DISH-RBHR-SCIENCE-20260821-05"
HOST_ID: Final = "RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3"
COMPONENT: Final = "dish.rbhr.r05.full_host"
PREACTIVITY_NAMESPACE: Final = "TEST/DISH-RBHR-R05/PRODUCTION-PREACTIVITY/V1"

ARMS: Final = ("STRUCTURED", "FLEX", "NEVER", "IMMEDIATE", "HYSTERESIS")
PACKAGES: Final = ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
TRAIN_SCHEDULES: Final = ("K4", "K12", "K4_TO_K12", "K12_TO_K4")
EVALUATION_SCHEDULES: Final = ("K4", "K8", "K12", "K4_TO_K12", "K12_TO_K4")
CLAIM_SCHEDULES: Final = ("K8", "K4_TO_K12", "K12_TO_K4")
STRATA: Final = ("POSITIVE", "NEAR_ZERO", "NEGATIVE")
MASK_VIEWS: Final = ("DEGRADED", "MASK_OFF")
ENDPOINTS: Final = ("MEAN", "TAIL", "DEFICIT", "DELAY")
FULL_CONTRASTS: Final = ("S-N", "F-S", "F-N", "I-N", "I-S", "H-N", "H-S")
FORK_CONTRASTS: Final = ("REAL-SHAM",)

BLOCKS: Final = 24
UPDATES: Final = 1_024
TRANSITIONS_PER_UPDATE: Final = 4_096
TRAIN_LANES: Final = 32
TICKS_PER_EPISODE: Final = 1_200
TAPES_PER_STRATUM: Final = 16
BOOTSTRAP_RESAMPLES: Final = 99_999
BRANCHES: Final = 15
SOLE_EVALUATION_CHECKPOINT: Final = 1_024

SCIENCE_FILES: Final[tuple[str, ...]] = (
    "DISH_RBHR_R05_SCIENCE_CARD_20260821.md",
    "DISH_RBHR_R05_HOST_GENERATOR_AND_RNG_MANIFEST_20260821.md",
    "DISH_RBHR_R05_TOTAL_RNG_ALLOCATION_TABLE_20260821.md",
    "DISH_RBHR_R05_PAYLOAD_SERVICE_TICK_AND_COST_RECURRENCE_20260821.md",
    "DISH_RBHR_R05_CONTROLLER_TREATMENT_COMPARATORS_AND_CERTIFICATE_20260821.md",
    "DISH_RBHR_R05_TRAINING_AND_POPULATION_MANIFEST_20260821.md",
    "DISH_RBHR_R05_OPPORTUNITY_FORK_ENDPOINT_INFERENCE_AND_BRANCH_MANIFEST_20260821.md",
)


class ProductionContractError(RuntimeError):
    pass


def complete_inventory() -> dict[str, object]:
    accepted_tapes = BLOCKS * len(PACKAGES) * len(EVALUATION_SCHEDULES) * len(STRATA) * TAPES_PER_STRATUM
    training_jobs = BLOCKS * len(ARMS)
    training_transitions = training_jobs * UPDATES * TRANSITIONS_PER_UPDATE
    evaluation_episodes = accepted_tapes * len(MASK_VIEWS) * len(ARMS)
    evaluation_ticks = evaluation_episodes * TICKS_PER_EPISODE
    claim_cells = BLOCKS * len(PACKAGES) * len(CLAIM_SCHEDULES) * len(STRATA)
    claim_tapes = claim_cells * TAPES_PER_STRATUM
    candidate_slots = accepted_tapes
    accepted_advantage_branch_ticks = candidate_slots * 2 * 50
    recovery_witness_episodes = claim_tapes * len(MASK_VIEWS) * 2
    recovery_witness_ticks = recovery_witness_episodes * TICKS_PER_EPISODE
    fork_pairs_max = claim_tapes
    return {
        "schema": "DISH_RBHR_R05_COMPLETE_PRODUCTION_INVENTORY_V1",
        "science_revision": SCIENCE_REVISION,
        "blocks": BLOCKS,
        "arms": list(ARMS),
        "packages": list(PACKAGES),
        "training_schedules": list(TRAIN_SCHEDULES),
        "evaluation_schedules": list(EVALUATION_SCHEDULES),
        "claim_schedules": list(CLAIM_SCHEDULES),
        "strata": list(STRATA),
        "mask_views": list(MASK_VIEWS),
        "training_jobs": training_jobs,
        "updates_per_job": UPDATES,
        "transitions_per_update": TRANSITIONS_PER_UPDATE,
        "training_transitions": training_transitions,
        "accepted_tapes": accepted_tapes,
        "candidate_slots": candidate_slots,
        "candidate_attempt_cap_per_slot": 100_000,
        "candidate_attempts_max": candidate_slots * 100_000,
        "candidate_rejected_attempt_count": "UNKNOWN_BEFORE_VALUE_BLIND_MASTER",
        "accepted_advantage_branch_ticks": accepted_advantage_branch_ticks,
        "recovery_witness_episodes": recovery_witness_episodes,
        "recovery_witness_ticks": recovery_witness_ticks,
        "evaluation_episodes": evaluation_episodes,
        "evaluation_ticks": evaluation_ticks,
        "claim_branch_cells": claim_cells,
        "atomic_supercells": len(PACKAGES) * len(CLAIM_SCHEDULES),
        "fork_pairs_max": fork_pairs_max,
        "fork_ticks_max": fork_pairs_max * 2 * 100,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "branch_count": BRANCHES,
        "checkpoint_updates": [SOLE_EVALUATION_CHECKPOINT],
        "partial_interpretation_permitted": False,
    }


def validate_inventory(value: Mapping[str, object]) -> None:
    expected = complete_inventory()
    if dict(value) != expected:
        raise ProductionContractError("production inventory differs from the frozen complete panel")


def science_root(repository_root: Path) -> Path:
    return repository_root / "docs" / "research" / "candidates" / "degraded_incumbent_shadow_handover"


@dataclass(frozen=True)
class PreactivityAuthority:
    """A non-activity capability used only for TEST construction measurement."""

    namespace: str = PREACTIVITY_NAMESPACE
    scientific_master: bool = False
    coordinate: bool = False
    lease: bool = False
    production_activity: bool = False

    def require_test_only(self) -> None:
        if self.namespace != PREACTIVITY_NAMESPACE:
            raise ProductionContractError("preactivity namespace differs")
        if self.scientific_master or self.coordinate or self.lease or self.production_activity:
            raise ProductionContractError("preactivity authority was promoted to scientific activity")


def refuse_without_root_lease(authority: object | None) -> None:
    """Fail closed for every future production/master/coordinate entry point."""

    if authority is None:
        raise ProductionContractError("an explicit later Operational-Root lease binding is required")
    require = getattr(authority, "require_active", None)
    if not callable(require):
        raise ProductionContractError("authority is not a Root lease binding")
    require()
