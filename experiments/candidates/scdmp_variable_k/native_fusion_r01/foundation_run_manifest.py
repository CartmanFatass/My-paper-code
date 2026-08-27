"""Unissued prospective foundation-activity manifest schema for CLOSED R01."""

from __future__ import annotations

import hashlib
import json
from typing import Final, Mapping

from .foundation_activity_contract import prospective_counts


S3_SLICE: Final[str] = (
    "SCDMP-NATIVE-FUSION-R01-S3-FOUNDATION-ACTIVITY-GATE-CONSTRUCTION-V1"
)
S4_SLICE: Final[str] = (
    "SCDMP-NATIVE-FUSION-R01-S4-FOUNDATION-ACTIVITY-PRELAUNCH-V1"
)
PYTHON_EXECUTABLE: Final[str] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
)
PRODUCTION_MODULE: Final[str] = (
    "experiments.candidates.scdmp_variable_k.native_fusion_r01."
    "foundation_activity_production"
)
NAMESPACE_PREFIX: Final[str] = "SCDMP-NATIVE-FUSION-R01/replicate"
PROSPECTIVE_OUTPUT_ROOT: Final[str] = (
    "temp/directions/semigroup_consistent_duration_model_policy/exp/"
    "native_fusion_r01/foundation"
)
S4_RUN_MANIFEST_PATH: Final[str] = (
    "temp/directions/semigroup_consistent_duration_model_policy/exp/"
    "native_fusion_r01/foundation-run-manifest.json"
)
HMAC_DOMAINS: Final[tuple[str, ...]] = (
    "foundation/initialization",
    "foundation/training",
    "foundation/competence",
    "opportunity/states",
    "opportunity/actions",
    "opportunity/tapes",
    "adapter/initialization",
    "adapter/training",
    "final/evaluation",
    "event/order",
    "switch/time",
    "disturbances",
    "action/uniforms",
    "minibatch/permutations",
)


def _valid_sha(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def manifest_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_prospective_activity_manifest(*, code_sha256: str) -> dict[str, object]:
    if not _valid_sha(code_sha256):
        raise ValueError("code_sha256 must be a SHA-256")
    counts = prospective_counts()
    replicate_roster = []
    terminal_slots = []
    for index in range(counts.replicates):
        uint32_be_hex = index.to_bytes(4, byteorder="big", signed=False).hex()
        replicate_roster.append(
            {
                "replicate_index": index,
                "uint32_be_hex": uint32_be_hex,
                "prospective_namespace": f"{NAMESPACE_PREFIX}/{uint32_be_hex}",
                "registered": False,
                "address_materialized": False,
            }
        )
        terminal_slots.append(
            {
                "replicate_index": index,
                "update_index": 192,
                "persistent_step_index": 3_072,
                "materialized": False,
                "eligible": False,
                "technically_accepted": False,
            }
        )
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_PROSPECTIVE_FOUNDATION_ACTIVITY_MANIFEST_V1",
        "slice": S3_SLICE,
        "status": "PROSPECTIVE_CREATE_ONLY_UNISSUED",
        "create_only": True,
        "code_sha256": code_sha256.lower(),
        "namespace_template": f"{NAMESPACE_PREFIX}/<uint32_be(s)>",
        "hmac_sha256_domains": list(HMAC_DOMAINS),
        "replicate_roster": replicate_roster,
        "counts": {
            "replicates": counts.replicates,
            "updates_per_foundation": counts.updates_per_foundation,
            "episodes_per_update": counts.episodes_per_update,
            "structural_steps_per_update": counts.structural_steps_per_update,
            "episodes_per_foundation": counts.episodes_per_foundation,
            "steps_per_foundation": counts.steps_per_foundation,
            "total_foundation_episodes": counts.total_foundation_episodes,
            "total_foundation_steps": counts.total_foundation_steps,
            "terminal_slots": len(terminal_slots),
        },
        "terminal_slots": terminal_slots,
        "output_root_contract": {
            "path": PROSPECTIVE_OUTPUT_ROOT,
            "create_only": True,
            "must_not_exist_before_launch": True,
        },
        "master_present": False,
        "registered_identity_present": False,
        "registered_address_present": False,
        "model_present": False,
        "optimizer_present": False,
        "checkpoint_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }


def build_production_argv(*, code_sha256: str) -> tuple[str, ...]:
    if not _valid_sha(code_sha256):
        raise ValueError("code_sha256 must be a SHA-256")
    return (
        PYTHON_EXECUTABLE,
        "-m",
        PRODUCTION_MODULE,
        "--run-manifest",
        S4_RUN_MANIFEST_PATH,
        "--code-sha256",
        code_sha256.lower(),
        "--output-root",
        PROSPECTIVE_OUTPUT_ROOT,
    )


def build_prelaunch_manifest(
    *, code_sha256: str, activity_estimate_sha256: str
) -> dict[str, object]:
    """Build an unissued S4 contract; it cannot authorize foundation activity."""

    if not _valid_sha(code_sha256) or not _valid_sha(activity_estimate_sha256):
        raise ValueError("prelaunch references must be SHA-256 values")
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S4_FOUNDATION_ACTIVITY_PRELAUNCH_V1",
        "slice": S4_SLICE,
        "status": "PRELAUNCH_TECHNICALLY_BOUND_UNISSUED",
        "canonical_parameters": {
            "replicates": 24,
            "updates_per_foundation": 192,
            "episodes_per_update": 16,
            "adamw_steps_per_update": 16,
            "episodes_per_foundation": 3_072,
            "adamw_steps_per_foundation": 3_072,
            "total_episodes": 73_728,
            "total_allocated_primitive_slots": 30_965_760,
            "total_maximum_policy_queries": 5_419_008,
            "total_adamw_steps": 73_728,
            "final_checkpoint_slots": 24,
            "k_balance_per_update": {"4": 8, "10": 8},
            "order_balance_per_k_update": {"GR": 4, "RG": 4},
        },
        "hmac_sha256_domains": list(HMAC_DOMAINS),
        "code_sha256": code_sha256.lower(),
        "activity_estimate_sha256": activity_estimate_sha256.lower(),
        "payload_argv": list(build_production_argv(code_sha256=code_sha256)),
        "output_effect_template": {
            "kind": "LOCAL_RESULT_ROOT",
            "resource_id": PROSPECTIVE_OUTPUT_ROOT,
            "operation": "CREATE_ONLY",
        },
        "run_manifest_contract": {
            "path": S4_RUN_MANIFEST_PATH,
            "strict_canonical_utf8_json": True,
            "immutable": True,
            "required_status": "AUTHORIZED_IMMUTABLE",
            "required_code_sha256": code_sha256.lower(),
            "required_output_root": PROSPECTIVE_OUTPUT_ROOT,
            "required_effect_count": 1,
            "required_activity_authorized": True,
            "required_operator_now": True,
            "draw_master_only_inside_operator_process": True,
            "immutable_old_state_per_update": True,
            "complete_only_publication": True,
            "rerun_permitted": False,
        },
        "result_responsive_options": [],
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }
