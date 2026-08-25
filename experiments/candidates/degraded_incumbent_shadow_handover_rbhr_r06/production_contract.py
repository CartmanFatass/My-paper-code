"""Frozen r06 engineering inventory and preactivity authority boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping


SCIENCE_REVISION: Final = "DISH-RBHR-SCIENCE-20260822-06"
HOST_ID: Final = "RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3"
COMPONENT: Final = "dish.rbhr.r06.full_host"
TEST_NAMESPACE: Final = "TEST/DISH-RBHR-R06/ENGINEERING-CONFORMANCE/V1"
RNG_PREFIX: Final = "DISH/RBHR/R06"

ARMS: Final = ("STRUCTURED", "FLEX", "NEVER", "IMMEDIATE", "HYSTERESIS")
REGIMES: Final = ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
TRAIN_SCHEDULES: Final = ("K4", "K12", "K4_TO_K12", "K12_TO_K4")
EVALUATION_SCHEDULES: Final = ("K4", "K8", "K12", "K4_TO_K12", "K12_TO_K4")
CLAIM_SCHEDULES: Final = ("K8", "K4_TO_K12", "K12_TO_K4")
SPEED_STRATA: Final = ("SPEED_4", "SPEED_6", "SPEED_8")
SPEEDS: Final = (4, 6, 8)
MASK_VIEWS: Final = ("DEGRADED", "MASK_OFF")
ENDPOINTS: Final = ("MEAN", "TAIL", "DEFICIT", "DELAY")
BRANCHES: Final = (
    "INVALID_PROTOCOL_OR_MEASUREMENT",
    "LEARNED_ARM_COMPETENCE_NOT_ESTABLISHED",
    "NO_REGISTERED_RECOVERY_WITNESS",
    "NONANSWERABLE_OR_NO_HEADROOM",
    "EFFECTIVE_HANDOVER_SUPPORT_NOT_ESTABLISHED",
    "TARGET_SPECIFIC_HARM",
    "NONACTUATION_PACKAGE_EFFECT",
    "SHADOW_ACTUATION_NONPASS",
    "SIMPLE_RULE_SUFFICIENT[IMMEDIATE]",
    "SIMPLE_RULE_SUFFICIENT[HYSTERESIS]",
    "FLEXIBLE_CONTAINER_SUPERIOR",
    "FLEX_RELATIVE_NONRETENTION",
    "STRUCTURED_ATOMIC_VALUE",
    "TARGET_SPECIFIC_NO_MATERIAL",
    "UNRESOLVED",
)

BLOCKS: Final = 24
SLOTS_PER_SPEED: Final = 16
EVALUATION_SLOTS_PER_CELL: Final = 48
UPDATES: Final = 1_024
TRANSITIONS_PER_UPDATE: Final = 4_096
TRAIN_LANES: Final = 32
TICKS_PER_EPISODE: Final = 1_200
BOOTSTRAP_RESAMPLES: Final = 99_999

SCIENCE_FILES: Final[tuple[tuple[str, str], ...]] = (
    ("DISH_RBHR_R06_SCIENCE_COMPOSITE_20260822.md", "cba40d437b52a6e2cb47c5cfe71aba3bb8d9f85b3ef1bf89620838d66402cb8a"),
    ("DISH_RBHR_POPULATION_INSTANTIABILITY_SUPPORT_ANALYSIS_20260822.md", "b129440671367cf90b40ca56564a9671be96f0adf24ae4c64c4d083a0b44f20d"),
    ("DISH_RBHR_R05_HOST_GENERATOR_AND_RNG_MANIFEST_20260821.md", "b4b3f9f0479c3e84489ca8b09c9193b4cce26db067a0a604c322784991ef729d"),
    ("DISH_RBHR_R05_TOTAL_RNG_ALLOCATION_TABLE_20260821.md", "3f0f3438f9913f57e997d60c850ddd2563da958d8bd0df99490b80d96f69bbb5"),
    ("DISH_RBHR_R05_PAYLOAD_SERVICE_TICK_AND_COST_RECURRENCE_20260821.md", "5e10d62d74500a1bfad3f81df8236c6b63615cd2abd198be9eb29d79957dd871"),
    ("DISH_RBHR_R05_CONTROLLER_TREATMENT_COMPARATORS_AND_CERTIFICATE_20260821.md", "3b69088ce5829261db6f4453c980548727e377b53d9403d439bb7cca66a35b30"),
    ("DISH_RBHR_R05_TRAINING_AND_POPULATION_MANIFEST_20260821.md", "bb451c4c9f13a972c79169692d87592687b9113eb65caa0ec97b4d12dd0b1a3b"),
    ("DISH_RBHR_R05_OPPORTUNITY_FORK_ENDPOINT_INFERENCE_AND_BRANCH_MANIFEST_20260821.md", "a20401b355763ce60791d3c1a75b98f0f5c07c88119fc982ea98b85b52141cad"),
)


class R06ContractError(RuntimeError):
    pass


def complete_inventory() -> dict[str, object]:
    evaluation_tapes = BLOCKS * len(REGIMES) * len(EVALUATION_SCHEDULES) * len(SPEED_STRATA) * SLOTS_PER_SPEED
    training_jobs = BLOCKS * len(ARMS)
    claim_tapes = BLOCKS * len(REGIMES) * len(CLAIM_SCHEDULES) * len(SPEED_STRATA) * SLOTS_PER_SPEED
    return {
        "schema": "DISH_RBHR_R06_COMPLETE_INVENTORY_V1",
        "science_revision": SCIENCE_REVISION,
        "blocks": BLOCKS,
        "arms": list(ARMS),
        "regimes": list(REGIMES),
        "evaluation_schedules": list(EVALUATION_SCHEDULES),
        "claim_schedules": list(CLAIM_SCHEDULES),
        "speed_strata": list(SPEED_STRATA),
        "slots_per_speed": SLOTS_PER_SPEED,
        "evaluation_tapes": evaluation_tapes,
        "mask_views": list(MASK_VIEWS),
        "evaluation_episodes": evaluation_tapes * len(MASK_VIEWS) * len(ARMS),
        "evaluation_ticks": evaluation_tapes * len(MASK_VIEWS) * len(ARMS) * TICKS_PER_EPISODE,
        "claim_tapes": claim_tapes,
        "training_jobs": training_jobs,
        "updates_per_job": UPDATES,
        "transitions_per_update": TRANSITIONS_PER_UPDATE,
        "training_transitions": training_jobs * UPDATES * TRANSITIONS_PER_UPDATE,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "branch_count": len(BRANCHES),
        "candidate_attempt_coordinate": False,
        "rejection_loop": False,
        "scientific_admission_failure_probability": 0.0,
        "partial_interpretation_permitted": False,
    }


def validate_inventory(value: Mapping[str, object]) -> None:
    if dict(value) != complete_inventory():
        raise R06ContractError("r06 complete inventory differs")


@dataclass(frozen=True)
class TestAuthority:
    namespace: str = TEST_NAMESPACE
    scientific_master: bool = False
    identity: bool = False
    coordinate: bool = False
    tape: bool = False
    model: bool = False
    activity: bool = False

    def require_test_only(self) -> None:
        if self.namespace != TEST_NAMESPACE or any((
            self.scientific_master, self.identity, self.coordinate, self.tape, self.model, self.activity,
        )):
            raise R06ContractError("r06 TEST authority was promoted to activity")


def science_root(repository_root: Path) -> Path:
    return repository_root / "docs" / "research" / "candidates" / "degraded_incumbent_shadow_handover"


def refuse_activity(authority: object | None = None) -> None:
    raise R06ContractError("r06 empirical identity/activity requires a later Portfolio decision and Root lease")


__all__ = [name for name in globals() if name.isupper()] + [
    "R06ContractError", "TestAuthority", "complete_inventory", "refuse_activity",
    "science_root", "validate_inventory",
]
