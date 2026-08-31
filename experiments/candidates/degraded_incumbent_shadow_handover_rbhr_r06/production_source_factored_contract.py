"""Fresh, result-blind contract for DISH-BLOCK-CERTIFICATE-PREVALENCE-R02."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Final, Iterator, Mapping


OBJECT_ID: Final = "DISH-BLOCK-CERTIFICATE-PREVALENCE-R02"
TRANSACTION_SUBSTRATE_ID: Final = "DISH-PROMOTION-SOURCE-FORK-R01"
SOURCE_FACTORED_NAMESPACE: Final = "TEST/DISH/BLOCK-CERTIFICATE-PREVALENCE/R02"
RUN_MODE: Final = "TEST_ONLY"
PACKAGES: Final = ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
CLAIM_SCHEDULES: Final = ("K8", "K4_TO_K12", "K12_TO_K4")
SPEEDS: Final = (4, 6, 8)
TRANSACTION_BRANCHES: Final = ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
POLICY_STATE_MODES: Final = ("RETAIN", "COPY", "SHADOW")
MODES: Final = TRANSACTION_BRANCHES
_ESTIMAND_SPECS: Final = (
    ("COPY-RETAIN", "TRANSFER_COPY", "RETAIN"),
    ("SHADOW-COPY", "TRANSFER_SHADOW", "TRANSFER_COPY"),
)
LEGACY_24_BLOCK_BOOTSTRAP_ALLOWED: Final = False
PRODUCTION_RESULT_ENTRY_IMPLEMENTED: Final = False
ENDPOINTS: Final = ("MEAN", "TAIL", "DEFICIT", "DELAY")
BLOCKS: Final = 24
ROOT_COUNT: Final = 24
ROOT_BYTES: Final = 32
PREVALENCE_REJECTION_THRESHOLD: Final = 18
SLOTS: Final = 16
FUTURE_TICKS: Final = 100
TRAINING_JOBS: Final = 24
CLAIM_ROWS: Final = BLOCKS * len(PACKAGES) * len(CLAIM_SCHEDULES) * len(SPEEDS) * SLOTS

# Additive production-readiness facts.  These do not modify the accepted
# TEST_ONLY contract returned by complete_contract().
PRODUCTION_NAMESPACE: Final = "DISH/BLOCK-CERTIFICATE-PREVALENCE/R02"
PRODUCTION_STATUS: Final = "PRODUCTION_NOT_READY"
PRODUCTION_REQUEST_SCHEMA: Final = "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_REQUEST_V2"
RUNNER_MASTER_POLICY: Final = "RUNNER_GENERATE_ONCE_IID_UNIFORM_256_BIT_ROOT_PANEL_24"
REPLAY_CERTIFICATE: Final = "TRANSFER_REPLAY"
TOTAL_UPDATES: Final = 24 * 1_024
TOTAL_TRAINING_TRANSITIONS: Final = TOTAL_UPDATES * 4_096
MAX_PREFIX_TICKS: Final = CLAIM_ROWS * 1_200
MAX_FORK_TICKS: Final = CLAIM_ROWS * 3 * FUTURE_TICKS
PRODUCTION_READINESS_GAPS: Final = (
    "PRODUCTION_SOURCE_FACTORED_NORMAL_TICK_AND_GENERATOR_PATH_ABSENT",
    "PRODUCTION_CHECKPOINT_SNAPSHOT_BRIDGE_AND_HANDOFF_INTEGRATION_ABSENT",
    "PRODUCTION_CAUSAL_VECTOR_AND_ROLE_INDEXED_POLICY_INTEGRATION_ABSENT",
    "PRODUCTION_ROLE_INDEXED_LIVE_POLICY_SNAPSHOT_AND_PPO_REPLAY_ABSENT",
    "PRODUCTION_SOURCE_SPECIFIC_MASKED_PER_DIMENSION_WELFORD_INTEGRATION_ABSENT",
    "FRESH_PREFIX_ALL_PRODUCERS_AND_ADDRESSED_MINIBATCH_FRONTIER_ABSENT",
    "EXACT_UNINTERRUPTED_VERSUS_RESUME_CHECKPOINT_PARITY_ABSENT",
    "FULL_TYPED_CAUSAL_REPLAY_CONTAINMENT_AND_DIRECT_DEADLINE_ABSENT",
    "SHARED_BLOCK_CHECKPOINT_AND_TYPED_NO_TRIGGER_DATA_PLANE_ABSENT",
    "DIRECT_PROCESS_TREE_AND_FILESYSTEM_RESOURCE_PREFLIGHT_ABSENT",
)
TEST_CONFORMANCE_CLOSED: Final = (
    "TEST_PHASED_SIDECAR_ABI_V1",
    "TEST_VALIDATED_RECURRENT_HANDOFF_V1",
    "TEST_TWO_OWNER_ONE_TICK_NATIVE_CAUSAL_54_58_ORACLE",
    "TEST_SOURCE_SPECIFIC_MASKED_PER_DIMENSION_WELFORD",
    "TEST_TYPED_OWNER_HISTORY_LIVE_REPLAY_RATIO_ONE",
)
class SourceFactoredContractError(RuntimeError):
    pass


class SourceFactoredNotReady(SourceFactoredContractError):
    pass


def estimand_definitions() -> dict[str, dict[str, str]]:
    """Return fresh nested dictionaries for the two independent axes."""

    return {
        name: {"treatment": treatment, "comparator": comparator}
        for name, treatment, comparator in _ESTIMAND_SPECS
    }


def prevalence_inference_contract() -> Mapping[str, object]:
    alpha = {"numerator": 1, "denominator": 80}
    tests = [
        {
            "id": f"{axis}/{claim}", "null": "p<=1/2",
            "alpha": dict(alpha), "reject_when_count_at_least": PREVALENCE_REJECTION_THRESHOLD,
        }
        for axis in ("COPY-RETAIN", "SHADOW-COPY")
        for claim in ("VALUE", "NO_MATERIAL")
    ]
    return {
        "root_law": {
            "count": ROOT_COUNT, "root_bytes": ROOT_BYTES,
            "distribution": "IID_UNIFORM_256_BIT", "duplicates_retained": True,
            "canonical_local_address_map": "F(U_b)",
            "global_block_index_role": "STORAGE_AND_ORDER_ONLY",
            "global_block_index_in_rng_address": False,
        },
        "within_root_census": {
            "packages": len(PACKAGES), "schedules": len(CLAIM_SCHEDULES),
            "speeds": len(SPEEDS), "slots": SLOTS,
            "rows": len(PACKAGES) * len(CLAIM_SCHEDULES) * len(SPEEDS) * SLOTS,
            "rows_are_independent_samples": False,
        },
        "tests": tests,
        "legacy_24_block_bootstrap_allowed": False,
        "no_alpha_recycling": True,
        "endpoint_anchor_scope": "ROOT_LOCAL_EXISTENTIAL_MAY_VARY",
        "fixed_endpoint_anchor_prevalence_authority": False,
        "indicator_rule_precommitted": True,
        "classification_selection_after_counts_allowed": False,
        "future_stochastic_address_law": {
            "physical_exogenous_evaluation_tape_shared_across_branches": True,
            "counter_frontier_shared_across_branches": True,
            "branch_id_in_scientific_rng_address": False,
            "branch_label_non_rng_roles": [
                "TRANSACTION", "OUTPUT_METADATA", "DETERMINISTIC_INTERVENTION_STATE",
            ],
        },
        "panel_retry_law": {
            "create_only_root_panel": True,
            "failure_before_panel_creation": "FRESH_PANEL_ALLOWED",
            "technical_failure_after_panel_creation": "REUSE_SAME_24_ROOTS_OUTCOME_BLIND_FROM_START",
            "redraw_after_panel_creation": False,
            "predefined_runtime_or_hard_event": "SCIENTIFIC_ZERO_OR_HARM_NOT_TECHNICAL_INCOMPLETE",
        },
        "claim_authority": {
            "algorithmic_root_certificate_prevalence": True,
            "expected_or_mean_return": False, "natural_prevalence": False,
            "generic_transfer": False, "unique_information_or_necessity": False,
            "safety_deployment_or_flight": False,
        },
    }


def production_readiness_gap_inventory() -> Mapping[str, object]:
    ceilings = ResourceCeilings()
    return {
        "schema": "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_READINESS_GAPS_V2",
        "object_id": OBJECT_ID, "namespace": PRODUCTION_NAMESPACE,
        "scientific_inference_object": OBJECT_ID,
        "status": PRODUCTION_STATUS, "ready": False,
        "transfer_replay": {"name": REPLAY_CERTIFICATE, "certificate_only": True,
                            "population_arm": False, "confirmatory_test_member": False},
        "fresh_master_allowed": False, "checkpoint_generation_allowed": False,
        "result_generation_allowed": False, "legacy_real_sham_substitute_allowed": False,
        "estimands": estimand_definitions(),
        "legacy_24_block_bootstrap_allowed": LEGACY_24_BLOCK_BOOTSTRAP_ALLOWED,
        "production_result_entry_implemented": PRODUCTION_RESULT_ENTRY_IMPLEMENTED,
        "resource_ceilings": {
            "workers_max": ceilings.workers, "cpu_cores_max": ceilings.cpu_cores,
            "torch_threads_per_worker": ceilings.torch_threads,
            "gpu_count": 0, "device": "cpu", "cpu_hours": ceilings.cpu_hours,
            "wall_hours": ceilings.wall_hours, "rss_gib": ceilings.rss_gib,
            "scratch_gib": ceilings.scratch_gib, "durable_gib": ceilings.durable_gib,
            "io_gib": ceilings.io_gib,
        },
        "question_relevant_output": False,
        "test_conformance_closed": list(TEST_CONFORMANCE_CLOSED),
        "scientific_holds": [],
        "gaps": list(PRODUCTION_READINESS_GAPS),
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
        "schema": "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_CONTRACT_V2",
        "object_id": OBJECT_ID, "scientific_object_id": OBJECT_ID,
        "transaction_substrate_id": TRANSACTION_SUBSTRATE_ID,
        "namespace": SOURCE_FACTORED_NAMESPACE,
        "run_mode": RUN_MODE, "abi_version": 1,
        "transaction_branches": list(TRANSACTION_BRANCHES),
        "policy_state_modes": list(POLICY_STATE_MODES),
        "estimands": estimand_definitions(),
        "estimands_independent": True,
        "legacy_24_block_bootstrap_allowed": LEGACY_24_BLOCK_BOOTSTRAP_ALLOWED,
        "legacy_single_branch_authority": False,
        "production_result_entry_implemented": PRODUCTION_RESULT_ENTRY_IMPLEMENTED,
        "prevalence_inference": prevalence_inference_contract(),
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
    "ENDPOINTS", "FUTURE_TICKS",
    "LEGACY_24_BLOCK_BOOTSTRAP_ALLOWED", "MODES", "OBJECT_ID", "PACKAGES", "POLICY_STATE_MODES",
    "PREVALENCE_REJECTION_THRESHOLD", "ROOT_BYTES", "ROOT_COUNT", "SLOTS",
    "SOURCE_FACTORED_NAMESPACE", "SPEEDS", "SourceFactoredContractError",
    "MAX_FORK_TICKS", "MAX_PREFIX_TICKS", "PRODUCTION_NAMESPACE",
    "PRODUCTION_READINESS_GAPS", "PRODUCTION_REQUEST_SCHEMA", "PRODUCTION_RESULT_ENTRY_IMPLEMENTED",
    "PRODUCTION_STATUS",
    "TEST_CONFORMANCE_CLOSED", "TRANSACTION_SUBSTRATE_ID",
    "REPLAY_CERTIFICATE", "RUN_MODE", "RUNNER_MASTER_POLICY", "SourceFactoredNotReady", "TOTAL_TRAINING_TRANSITIONS",
    "TOTAL_UPDATES", "TRAINING_JOBS", "TRANSACTION_BRANCHES", "canonical_json_bytes",
    "complete_claim_inventory", "complete_contract", "estimand_definitions", "iter_claim_coordinates",
    "prevalence_inference_contract", "production_readiness_gap_inventory", "validate_contract",
]
