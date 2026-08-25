"""Frozen, coordinate-free contracts for the ONLGR TBVUUS r03 panel.

This module deliberately contains no coordinate encoder, random generator,
host binding, or production runner.  It is the one small source of truth for
the immutable identities, finite-package counts, schemas, and controller-free
tape law that later native construction must satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping


DIRECTION_ID = "opportunity_normalized_lease_gated_rebinding"
SCIENCE_REVISION = "ONLGR-TBVUUS-SCIENCE-20260821-03"
STAGE = "ONLGR-TBVUUS-R03-FULL-PANEL"
HOST_ID = "HEADLAND-90-ROAD-TRACK-PATCH-UTILITY-v1"
PRODUCTION_NAMESPACE = "ONLGR-TBVUUS-HEADLAND90-20260821-v1"

NEVER_UPDATE = "NEVER-UPDATE"
OVERHEAD_SHAM = "OVERHEAD-SHAM"
RAW_ESTIMATE_PATCH = "RAW-ESTIMATE-PATCH"
ROAD_TRACK_ESTIMATE_PATCH = "ROAD-TRACK-ESTIMATE-PATCH"
ARMS = (
    NEVER_UPDATE,
    OVERHEAD_SHAM,
    RAW_ESTIMATE_PATCH,
    ROAD_TRACK_ESTIMATE_PATCH,
)
ROUTE_CLASSES = ("SHORT", "LONG")

REPLICATES = 128
BLOCKS_PER_CONTROLLER_REPLICATE = 20
ENCOUNTERS_PER_BLOCK = 2
SHORT_PHYSICAL_TICKS = 48
LONG_PHYSICAL_TICKS = 144
SHORT_SCORED_TICKS = 32
LONG_SCORED_TICKS = 128
CONTROLLER_REPLICATES = len(ARMS) * REPLICATES
ENCOUNTERS_PER_CONTROLLER_REPLICATE = (
    BLOCKS_PER_CONTROLLER_REPLICATE * ENCOUNTERS_PER_BLOCK
)
PHYSICAL_TICKS_PER_CONTROLLER_REPLICATE = BLOCKS_PER_CONTROLLER_REPLICATE * (
    SHORT_PHYSICAL_TICKS + LONG_PHYSICAL_TICKS
)
SCORED_TICKS_PER_CONTROLLER_REPLICATE = BLOCKS_PER_CONTROLLER_REPLICATE * (
    SHORT_SCORED_TICKS + LONG_SCORED_TICKS
)
TOTAL_ARM_ENCOUNTERS = CONTROLLER_REPLICATES * ENCOUNTERS_PER_CONTROLLER_REPLICATE
TOTAL_PHYSICAL_TICKS = CONTROLLER_REPLICATES * PHYSICAL_TICKS_PER_CONTROLLER_REPLICATE
SCHEDULED_T0_DECISIONS_PER_ARM = REPLICATES * ENCOUNTERS_PER_CONTROLLER_REPLICATE

ACTION_WORD_DOMAIN = None
DISTURBANCE_STREAMS = (
    "target_lateral",
    "wind_T",
    "wind_R",
    "sensor_x",
    "sensor_y",
    "shadow_TR",
    "shadow_RB",
    "link_TR",
    "link_RB",
)

COORDINATE_PROPOSAL_SCHEMA = "ONLGR-TBVUUS-R03-COORDINATE-PROPOSAL-v1"
PREACTIVITY_SCHEMA = "ONLGR-TBVUUS-R03-PREACTIVITY-IDENTITY-v1"
CELL_SCHEMA = "ONLGR-TBVUUS-R03-BLINDED-CELL-v1"
CELL_COMMIT_SCHEMA = "ONLGR-TBVUUS-R03-CELL-COMMIT-v1"
PANEL_COMMIT_SCHEMA = "ONLGR-TBVUUS-R03-PANEL-COMMIT-v1"
COMPLETE_SCHEMA = "ONLGR-TBVUUS-R03-COMPLETE-v1"
CM_ACCEPTANCE_SCHEMA = "ONLGR-TBVUUS-R03-CM-TECHNICAL-ACCEPTANCE-v1"
RESULT_RELEASE_AUTHORIZATION_SCHEMA = "ONLGR-TBVUUS-R03-ROOT-RESULT-RELEASE-AUTHORIZATION-v2"
RESULT_RELEASE_ID_SCHEMA = "ONLGR-TBVUUS-R03-RESULT-RELEASE-ID-v1"
RESULT_RELEASE_RECEIPT_SCHEMA = "ONLGR-TBVUUS-R03-RESULT-RELEASE-RECEIPT-v2"
PORTFOLIO_EM_SEQUENCING_RECEIPT_SCHEMA = (
    "ONLGR-TBVUUS-R03-PORTFOLIO-EM-RESULT-INTAKE-SEQUENCING-RECEIPT-v1"
)
RESULT_SCHEMA = "ONLGR-TBVUUS-R03-RESULT-v2"
SOURCE_MANIFEST_SCHEMA = "ONLGR-TBVUUS-R03-SOURCE-MANIFEST-v1"
ACCEPTED_FREEZE_SCHEMA = "ONLGR-TBVUUS-R03-ACCEPTED-PREACTIVITY-FREEZE-v1"
COORDINATE_BINDING_SCHEMA = "ONLGR-TBVUUS-R03-ROOT-COORDINATE-BINDING-v1"
DIRECTION_LEASE_SCHEMA = "ONLGR-TBVUUS-R03-DIRECTION-LEASE-v1"
PRIVATE_PANEL_SCHEMA = "ONLGR-TBVUUS-R03-PRIVATE-PANEL-v1"
ACTIVITY_INTENT_SCHEMA = "ONLGR-TBVUUS-R03-ACTIVITY-INTENT-v1"
ACTIVITY_STARTED_SCHEMA = "ONLGR-TBVUUS-R03-ACTIVITY-STARTED-v1"
SERIALIZER_ID = "UTF8-CANONICAL-JSON-SORTED-COMPACT-LF-v1"

SIDECAR_SCHEMAS = {
    "tick_audit": ("ONLGR-TBVUUS-R03-TICK-AUDIT-v1", PHYSICAL_TICKS_PER_CONTROLLER_REPLICATE),
    "road_fit_audit": (
        "ONLGR-TBVUUS-R03-ROAD-FIT-AUDIT-v1",
        ENCOUNTERS_PER_CONTROLLER_REPLICATE,
    ),
    "arm_transition_audit": (
        "ONLGR-TBVUUS-R03-ARM-TRANSITION-AUDIT-v1",
        ENCOUNTERS_PER_CONTROLLER_REPLICATE,
    ),
    "endpoint_audit": (
        "ONLGR-TBVUUS-R03-ENDPOINT-AUDIT-v1",
        BLOCKS_PER_CONTROLLER_REPLICATE,
    ),
}

BINDING_KEYS = (
    "preactivity_freeze_sha256",
    "coordinate_binding_sha256",
    "lease_scope_sha256",
    "source_set_sha256",
    "config_sha256",
    "schema_sha256",
    "native_artifact_sha256",
)

HARD_FAILURE_KEYS = (
    "terrain_penetrations",
    "geofence_exits",
    "separation_breaches",
    "no_safe_control",
    "no_planner_solution",
    "battery_exhaustions",
    "numerical_faults",
)


class ContractError(ValueError):
    """A proposed object differs from the immutable r03 contract."""


def canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("contract value is not finite canonical JSON") from exc


def document_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class PanelShape:
    arms: int = len(ARMS)
    replicates: int = REPLICATES
    blocks_per_controller_replicate: int = BLOCKS_PER_CONTROLLER_REPLICATE
    encounters_per_block: int = ENCOUNTERS_PER_BLOCK
    controller_replicates: int = CONTROLLER_REPLICATES
    arm_encounters: int = TOTAL_ARM_ENCOUNTERS
    physical_ticks_per_controller_replicate: int = PHYSICAL_TICKS_PER_CONTROLLER_REPLICATE
    total_physical_ticks: int = TOTAL_PHYSICAL_TICKS

    def validate(self) -> None:
        expected = PanelShape()
        if self != expected:
            raise ContractError("panel shape differs from the exact 4x128 r03 package")
        if self.controller_replicates != self.arms * self.replicates:
            raise ContractError("controller-replicate count is inconsistent")
        if self.arm_encounters != (
            self.controller_replicates
            * self.blocks_per_controller_replicate
            * self.encounters_per_block
        ):
            raise ContractError("arm-encounter count is inconsistent")
        if self.total_physical_ticks != (
            self.controller_replicates * self.physical_ticks_per_controller_replicate
        ):
            raise ContractError("physical-tick count is inconsistent")

    def as_dict(self) -> dict[str, int]:
        self.validate()
        return {
            "arms": self.arms,
            "replicates": self.replicates,
            "blocks_per_controller_replicate": self.blocks_per_controller_replicate,
            "encounters_per_block": self.encounters_per_block,
            "controller_replicates": self.controller_replicates,
            "arm_encounters": self.arm_encounters,
            "physical_ticks_per_controller_replicate": self.physical_ticks_per_controller_replicate,
            "total_physical_ticks": self.total_physical_ticks,
        }


def coordinate_proposal() -> dict[str, object]:
    """Return the unbound schema/count proposal, never coordinate rows or words."""

    proposal: dict[str, object] = {
        "schema": COORDINATE_PROPOSAL_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "bound": False,
        "coordinate_rows_present": False,
        "production_words_present": False,
        "split": "HOLD",
        "replicates": REPLICATES,
        "arms": list(ARMS),
        "panel_shape": PanelShape().as_dict(),
        "coordinate_schema": {
            "fields": [
                "namespace", "split", "replicate", "block", "class",
                "template", "tick", "stream", "lane",
            ],
            "split_domain": ["HOLD"],
            "replicate_domain": "0,...,127",
            "block_domain": "0,...,19",
            "class_domain": list(ROUTE_CLASSES),
            "template_law": "(replicate+3*block) mod 4",
            "stream_domain": list(DISTURBANCE_STREAMS),
            "controller_identity_in_disturbance_key": False,
            "arm_identity_in_disturbance_key": False,
        },
        "controller_free_tape_law": {
            "streams": list(DISTURBANCE_STREAMS),
            "action_stream_present": False,
            "action_word_generated": False,
            "action_word_consumed": False,
            "shared_across_arms_within_replicate": True,
            "counter_law": (
                "SHA-256(length-prefixed UTF-8 tuple); uniform=(uint32be+0.5)/2^32; "
                "fixed Box-Muller lower-lane pairs"
            ),
            "future_binding": "Root-authored exact row-set digest; absent from this proposal",
        },
        "balance_laws": {
            "template": "(replicate+3*block) mod 4",
            "encounter_order": (
                "SHORT,LONG iff (replicate+block) is even; otherwise LONG,SHORT"
            ),
            "route_classes_diagnostic_only": True,
        },
    }
    proposal["proposal_sha256"] = document_sha256(proposal)
    return proposal


def validate_coordinate_proposal(value: Mapping[str, object]) -> dict[str, object]:
    expected = coordinate_proposal()
    if dict(value) != expected:
        raise ContractError("coordinate proposal differs or contains bound material")
    return expected


def prospective_schema_contract() -> dict[str, object]:
    """Describe the complete future storage surface without any observations."""

    value = {
        "serializer": SERIALIZER_ID,
        "schemas": {
            "preactivity": PREACTIVITY_SCHEMA,
            "cell": CELL_SCHEMA,
            "cell_commit": CELL_COMMIT_SCHEMA,
            "panel_commit": PANEL_COMMIT_SCHEMA,
            "complete": COMPLETE_SCHEMA,
            "cm_acceptance": CM_ACCEPTANCE_SCHEMA,
            "result_release_authorization": RESULT_RELEASE_AUTHORIZATION_SCHEMA,
            "result_release_receipt": RESULT_RELEASE_RECEIPT_SCHEMA,
            "portfolio_em_sequencing_receipt": PORTFOLIO_EM_SEQUENCING_RECEIPT_SCHEMA,
            "result": RESULT_SCHEMA,
            "sidecars": {key: schema for key, (schema, _) in SIDECAR_SCHEMAS.items()},
        },
        "required_sidecar_rows_per_cell": {
            key: rows for key, (_, rows) in SIDECAR_SCHEMAS.items()
        },
        "binding_keys": list(BINDING_KEYS),
        "write_once": True,
        "same_coordinate_resume_only": True,
        "atomic_complete_then_result": True,
        "partial_result_fields_forbidden": True,
    }
    return {**value, "schema_contract_sha256": document_sha256(value)}


def frozen_identity() -> dict[str, object]:
    value = {
        "direction_id": DIRECTION_ID,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "arms": list(ARMS),
        "panel_shape": PanelShape().as_dict(),
        "action_word_domain": ACTION_WORD_DOMAIN,
        "coordinate_proposal": coordinate_proposal(),
        "schema_contract": prospective_schema_contract(),
    }
    return {**value, "identity_sha256": document_sha256(value)}
