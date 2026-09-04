"""Identity-free contract for the prospective TBCC revision-02 panel.

This module describes the frozen address space, work inventory, and stage
barriers.  It deliberately contains no entropy source and creates no empirical
object when imported or when :func:`coordinate_proposal` is called.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Final


EMPIRICAL_STAGE: Final[str] = "SCDMP-TBCC-R02-FULL-EMPIRICAL-PANEL"
CARD_REVISION: Final[str] = "SCDMP-TBCC-ORDER-VALUE-SCIENCE-20260821-02"
CARD_SHA256: Final[str] = (
    "f7a6363caf4333e7afcf4cd8df8043ae3b3088a57cb42a34eaf7fa432cb38481"
)
REPLICATE_NAMESPACE: Final[str] = (
    "SCDMP-TBCC-ORDER-VALUE-r01/replicate/<uint32_be(s)>"
)
REPLICATES: Final[tuple[int, ...]] = tuple(range(24))
CONTROLLERS: Final[tuple[str, ...]] = (
    "FOUNDATION", "TREAT", "FREE", "REVERSED", "SET"
)
REGIMES: Final[tuple[str, ...]] = (
    "fixed-5", "fixed-11", "fixed-7", "fixed-13", "7-to-13", "13-to-7"
)

# Domain labels are purpose-specific, mutually distinct ASCII values.  The
# address field list following each label is part of the frozen serialization
# contract and prevents an address from one stage being reused in another.
DOMAIN_ADDRESS_SCHEMAS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("foundation-initialization", ("tensor_group", "flat_index")),
    ("foundation-training-state", ("update", "episode", "component")),
    ("foundation-competence-state", ("regime", "episode", "component")),
    ("opportunity-state", ("k", "state", "component")),
    ("opportunity-forced-action", ("k", "state", "action")),
    ("opportunity-disturbance-tape", ("k", "state", "tape", "tick", "component")),
    ("adapter-initialization", ("arm", "tensor_group", "flat_index")),
    ("adapter-training-state", ("arm", "update", "episode", "component")),
    ("final-evaluation-state", ("controller", "regime", "episode", "component")),
    ("setup-order", ("stage", "arm", "regime", "episode")),
    ("switch-time", ("stage", "arm", "regime", "episode")),
    ("disturbances", ("stage", "arm", "regime", "episode", "tick", "component")),
    ("categorical-uniforms", ("stage", "arm", "update", "episode", "renewal")),
    ("minibatch-permutations", ("stage", "arm", "update", "epoch")),
)
DOMAIN_LABELS: Final[tuple[str, ...]] = tuple(row[0] for row in DOMAIN_ADDRESS_SCHEMAS)

PANEL_COUNTS: Final[dict[str, int]] = {
    "replicates": 24,
    "foundation_updates_per_replicate": 160,
    "foundation_training_episodes": 46_080,
    "foundation_training_allocated_slots": 16_773_120,
    "foundation_training_max_policy_queries": 2_465_280,
    "foundation_adamw_steps": 46_080,
    "foundation_final_checkpoints": 24,
    "foundation_competence_episodes": 17_280,
    "foundation_competence_allocated_slots": 6_289_920,
    "foundation_competence_max_policy_queries": 768_960,
    "opportunity_states_per_k": 16,
    "opportunity_fixed_k_count": 2,
    "opportunity_graphs": 2,
    "opportunity_actions": 18,
    "opportunity_tapes": 4,
    "opportunity_rollouts": 110_592,
    "opportunity_allocated_slots": 40_255_488,
    "opportunity_max_policy_queries": 4_313_088,
    "opportunity_forced_interventions": 110_592,
    "order_stage_arms": 3,
    "order_stage_updates_per_arm": 96,
    "order_stage_training_episodes": 82_944,
    "order_stage_allocated_slots": 30_191_616,
    "order_stage_max_policy_queries": 4_437_504,
    "order_stage_adamw_steps": 82_944,
    "order_stage_final_checkpoints": 72,
    "final_evaluation_controllers": 5,
    "final_evaluation_episodes": 86_400,
    "final_evaluation_allocated_slots": 31_449_600,
    "final_evaluation_max_policy_queries": 3_844_800,
    "complete_episodes_or_rollouts": 343_296,
    "complete_allocated_slots": 124_959_744,
    "complete_max_policy_queries": 15_829_632,
    "complete_adamw_steps": 129_024,
    "complete_final_checkpoints": 96,
}

STAGE_BARRIERS: Final[dict[str, object]] = {
    "foundation_finals_before_competence": 24,
    "foundation_competence_atomic": True,
    "foundation_competence_pass_before_opportunity": True,
    "opportunity_atomic_replicates": 24,
    "opportunity_pass_before_order_materialization": True,
    "order_final_checkpoints_before_final_evaluation": 72,
    "foundation_final_checkpoints_before_final_evaluation": 24,
    "final_evaluation_atomic": True,
    "valid_prerequisite_nonpass_makes_downstream_inapplicable": True,
    "partial_publication_or_interpretation": False,
    "same_blinded_frontier_resume": True,
}
NATIVE_REWARD_TRACE_CONTRACT: Final[dict[str, object]] = {
    "abi_version": 2,
    "capacity": 13,
    "count_field": "last_hold_reward_count",
    "values_field": "last_hold_rewards",
    "count_equals_ticks_advanced": True,
    "inactive_tail": "canonical_zero",
}


class EmpiricalContractError(ValueError):
    """The prospective identity-free contract differs from the frozen card."""


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 64:
        raise EmpiricalContractError("source manifest SHA-256 must contain 64 hex characters")
    try:
        int(value, 16)
    except ValueError as error:
        raise EmpiricalContractError("source manifest SHA-256 is not hexadecimal") from error
    return value.lower()


def coordinate_proposal(source_manifest_sha256: str | None = None) -> dict[str, object]:
    """Return the exact unmaterialized proposal; never draw or persist anything."""

    manifest_sha = _sha_or_none(source_manifest_sha256)
    return {
        "schema": "SCDMP_TBCC_R02_COORDINATE_PROPOSAL_V1",
        "stage": EMPIRICAL_STAGE,
        "card_revision": CARD_REVISION,
        "card_sha256": CARD_SHA256,
        "materialized": False,
        "replicate_namespace": REPLICATE_NAMESPACE,
        "replicates": list(REPLICATES),
        "rng": {
            "derivation": "HMAC-SHA256",
            "master_bytes": 32,
            "master": None,
            "master_digest": None,
            "replicate_key_digests": [],
            "domain_key_digests": [],
            "sampled_values": [],
            "domain_address_schemas": [
                {"domain": domain, "fields": list(fields)}
                for domain, fields in DOMAIN_ADDRESS_SCHEMAS
            ],
        },
        "counts": dict(PANEL_COUNTS),
        "barriers": dict(STAGE_BARRIERS),
        "native_reward_trace": dict(NATIVE_REWARD_TRACE_CONTRACT),
        "source_manifest_sha256": manifest_sha,
        "empirical_objects_present": False,
    }


def validate_coordinate_proposal(
    value: Mapping[str, object], *, source_manifest_sha256: str | None = None
) -> dict[str, object]:
    expected = coordinate_proposal(source_manifest_sha256)
    if not isinstance(value, Mapping) or dict(value) != expected:
        raise EmpiricalContractError("coordinate proposal differs from the frozen identity-free contract")
    return expected


def coordinate_proposal_digest(source_manifest_sha256: str | None = None) -> str:
    return canonical_digest(coordinate_proposal(source_manifest_sha256))
