"""Fresh, result-blind contract for DISH-PROMOTION-SOURCE-FORK-R01."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final, Iterator, Mapping


OBJECT_ID: Final = "DISH-PROMOTION-SOURCE-FORK-R01"
SOURCE_FACTORED_NAMESPACE: Final = "TEST/DISH/PROMOTION-SOURCE-FORK/R01"
RUN_MODE: Final = "TEST_ONLY"
PACKAGES: Final = ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
CLAIM_SCHEDULES: Final = ("K8", "K4_TO_K12", "K12_TO_K4")
SPEEDS: Final = (4, 6, 8)
TRANSACTION_BRANCHES: Final = ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
POLICY_STATE_MODES: Final = ("RETAIN", "COPY", "SHADOW")
MODES: Final = TRANSACTION_BRANCHES
ENDPOINTS: Final = ("MEAN", "TAIL", "DEFICIT", "DELAY")
BLOCKS: Final = 24
SLOTS: Final = 16
FUTURE_TICKS: Final = 100
TRAINING_JOBS: Final = 24
CLAIM_ROWS: Final = BLOCKS * len(PACKAGES) * len(CLAIM_SCHEDULES) * len(SPEEDS) * SLOTS


class SourceFactoredContractError(RuntimeError):
    pass


@dataclass(frozen=True, order=True)
class ClaimCoordinate:
    block: int
    package: str
    schedule: str
    speed: int
    slot: int

    def __post_init__(self) -> None:
        if not (0 <= self.block < BLOCKS and self.package in PACKAGES and
                self.schedule in CLAIM_SCHEDULES and self.speed in SPEEDS and
                0 <= self.slot < SLOTS):
            raise SourceFactoredContractError("source-factored coordinate differs")

    def key(self) -> str:
        return f"{OBJECT_ID}/{self.block:02d}/{self.package}/{self.schedule}/SPEED_{self.speed}/{self.slot:02d}"


def iter_claim_coordinates() -> Iterator[ClaimCoordinate]:
    for block in range(BLOCKS):
        for package in PACKAGES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEEDS:
                    for slot in range(SLOTS):
                        yield ClaimCoordinate(block, package, schedule, speed, slot)


def complete_claim_inventory() -> tuple[ClaimCoordinate, ...]:
    rows = tuple(iter_claim_coordinates())
    if len(rows) != 6_912 or len({row.key() for row in rows}) != 6_912:
        raise SourceFactoredContractError("6,912-row source-factored inventory differs")
    return rows


@dataclass(frozen=True)
class ResourceCeilings:
    workers: int = 8
    cpu_cores: int = 8
    torch_threads: int = 1
    gpu: int = 0
    cpu_hours: float = 40.0
    wall_hours: float = 10.0
    rss_gib: float = 6.61
    scratch_gib: float = 1.66
    durable_gib: float = 0.83
    io_gib: float = 68.14


def complete_contract() -> Mapping[str, object]:
    resources = ResourceCeilings()
    return {
        "schema": "DISH_PROMOTION_SOURCE_FORK_R01_CONTRACT_V1",
        "object_id": OBJECT_ID, "namespace": SOURCE_FACTORED_NAMESPACE,
        "run_mode": RUN_MODE, "abi_version": 1,
        "transaction_branches": list(TRANSACTION_BRANCHES),
        "policy_state_modes": list(POLICY_STATE_MODES),
        "claim_rows": CLAIM_ROWS, "training_jobs": TRAINING_JOBS,
        "training_arm": "STRUCTURED", "future_ticks": FUTURE_TICKS,
        "optimizer_updates_per_fork": 0, "preserve_no_trigger_rows": True,
        "legacy_estimands_reused": False,
        "resource_ceilings": asdict(resources), "question_relevant_output": False,
    }


def validate_contract(value: Mapping[str, object]) -> None:
    if dict(value) != dict(complete_contract()):
        raise SourceFactoredContractError("source-factored contract differs")


__all__ = [
    "BLOCKS", "CLAIM_ROWS", "CLAIM_SCHEDULES", "ClaimCoordinate",
    "ENDPOINTS", "FUTURE_TICKS", "MODES", "OBJECT_ID", "PACKAGES", "POLICY_STATE_MODES",
    "SLOTS", "SOURCE_FACTORED_NAMESPACE", "SPEEDS", "SourceFactoredContractError",
    "RUN_MODE", "TRAINING_JOBS", "TRANSACTION_BRANCHES", "complete_claim_inventory", "complete_contract",
    "iter_claim_coordinates", "validate_contract",
]
