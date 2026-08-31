"""Fresh, result-blind contract for DISH-PROMOTION-SOURCE-FORK-R01."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
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

# Additive production-readiness facts.  These do not modify the accepted
# TEST_ONLY contract returned by complete_contract().
PRODUCTION_NAMESPACE: Final = "DISH/PROMOTION-SOURCE-FORK/R01"
PRODUCTION_STATUS: Final = "PRODUCTION_NOT_READY"
PRODUCTION_REQUEST_SCHEMA: Final = "DISH_PROMOTION_SOURCE_FORK_R01_REQUEST_V1"
RUNNER_MASTER_POLICY: Final = "RUNNER_GENERATE_ONCE_OS_CSPRNG_256"
REPLAY_CERTIFICATE: Final = "TRANSFER_REPLAY"
TOTAL_UPDATES: Final = 24 * 1_024
TOTAL_TRAINING_TRANSITIONS: Final = TOTAL_UPDATES * 4_096
MAX_PREFIX_TICKS: Final = CLAIM_ROWS * 1_200
MAX_FORK_TICKS: Final = CLAIM_ROWS * 3 * FUTURE_TICKS
INFERENCE_RESAMPLES: Final = 99_999
PRODUCTION_READINESS_GAPS: Final = (
    "SOURCE_FACTORED_PHASED_SIDECAR_ABI_AND_BEGIN_TICK_TOKEN_ABSENT",
    "TSTAR_SNAPSHOT_ASSIMILATION_AND_VALIDATED_RECURRENT_HANDOFF_ABSENT",
    "SOURCE_MODE_NATIVE_ACTOR_54_VECTOR_AND_DELIVERED_PARTNER_STATE_ABSENT",
    "SOURCE_MODE_NATIVE_CRITIC_BASE_ERROR_ABSENT",
    "ROLE_INDEXED_LIVE_POLICY_SNAPSHOT_AND_PPO_REPLAY_ABSENT",
    "MASKED_PER_DIMENSION_ACTOR_SNAPSHOT_CRITIC_WELFORD_ABSENT",
    "FRESH_PREFIX_ALL_PRODUCERS_AND_ADDRESSED_MINIBATCH_FRONTIER_ABSENT",
    "EXACT_UNINTERRUPTED_VERSUS_RESUME_CHECKPOINT_PARITY_ABSENT",
    "TYPED_CAUSAL_REPLAY_CONTAINMENT_AND_DIRECT_DEADLINE_ABSENT",
    "SHARED_BLOCK_CHECKPOINT_AND_TYPED_NO_TRIGGER_DATA_PLANE_ABSENT",
    "PAIRED_99999_BLOCK_MAX_T_REDUCER_ABSENT",
    "DIRECT_PROCESS_TREE_AND_FILESYSTEM_RESOURCE_PREFLIGHT_ABSENT",
)


class SourceFactoredContractError(RuntimeError):
    pass


class SourceFactoredNotReady(SourceFactoredContractError):
    pass


def production_readiness_gap_inventory() -> Mapping[str, object]:
    ceilings = ResourceCeilings()
    return {
        "schema": "DISH_PROMOTION_SOURCE_FORK_R01_READINESS_GAPS_V1",
        "object_id": OBJECT_ID, "namespace": PRODUCTION_NAMESPACE,
        "status": PRODUCTION_STATUS, "ready": False,
        "transfer_replay": {"name": REPLAY_CERTIFICATE, "certificate_only": True,
                            "population_arm": False, "max_t_member": False},
        "fresh_master_allowed": False, "checkpoint_generation_allowed": False,
        "result_generation_allowed": False, "legacy_real_sham_substitute_allowed": False,
        "resource_ceilings": {
            "workers_max": ceilings.workers, "cpu_cores_max": ceilings.cpu_cores,
            "torch_threads_per_worker": ceilings.torch_threads,
            "gpu_count": 0, "device": "cpu", "cpu_hours": ceilings.cpu_hours,
            "wall_hours": ceilings.wall_hours, "rss_gib": ceilings.rss_gib,
            "scratch_gib": ceilings.scratch_gib, "durable_gib": ceilings.durable_gib,
            "io_gib": ceilings.io_gib,
        },
        "question_relevant_output": False, "gaps": list(PRODUCTION_READINESS_GAPS),
    }


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise SourceFactoredContractError("canonical ASCII JSON differs") from error


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
    "INFERENCE_RESAMPLES", "MAX_FORK_TICKS", "MAX_PREFIX_TICKS", "PRODUCTION_NAMESPACE",
    "PRODUCTION_READINESS_GAPS", "PRODUCTION_REQUEST_SCHEMA", "PRODUCTION_STATUS",
    "REPLAY_CERTIFICATE", "RUN_MODE", "RUNNER_MASTER_POLICY", "SourceFactoredNotReady", "TOTAL_TRAINING_TRANSITIONS",
    "TOTAL_UPDATES", "TRAINING_JOBS", "TRANSACTION_BRANCHES", "canonical_json_bytes",
    "complete_claim_inventory", "complete_contract", "iter_claim_coordinates",
    "production_readiness_gap_inventory", "validate_contract",
]
