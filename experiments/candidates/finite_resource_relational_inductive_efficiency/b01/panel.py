"""Exact primitive-only B01 complete-panel validators."""

from __future__ import annotations

import math
from typing import Any, Mapping

from ..host import native_endpoint
from .constants import (
    CHECKPOINTS, EVALUATION_EPISODES, EVALUATION_ROSTERS, INTERVENTIONS,
    LEARNED_ARMS, PANEL_SCHEMA, TEST_MANIFEST_SCHEMA,
)
from .contract import (
    B01ContractError, validate_invocation_binding, validate_manifest,
    validate_test_manifest,
)
from .native_batch import performance_readiness

_ROW_FIELDS = {
    "seed_label", "arm", "checkpoint", "roster", "intervention", "episode",
    "tape_binding", "J", "D_W", "D_E", "WASTE", "role_action_counts",
    "successful_scan", "successful_uplink", "successful_receive",
    "successful_delivery", "expired", "duplicate", "collision", "empty_radio",
}


def validate_primitive_row(value: Any, *, seed_labels: set[str], test_only: bool) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _ROW_FIELDS:
        raise B01ContractError("B01 primitive row fields differ")
    row = dict(value)
    if row["seed_label"] not in seed_labels:
        raise B01ContractError("primitive row seed label differs")
    if row["arm"] not in (*LEARNED_ARMS, "UNIFORM_LEGAL"):
        raise B01ContractError("primitive row arm differs")
    if row["roster"] not in EVALUATION_ROSTERS or row["intervention"] not in INTERVENTIONS:
        raise B01ContractError("primitive row cell differs")
    if type(row["episode"]) is not int or not 0 <= row["episode"] < EVALUATION_EPISODES:
        raise B01ContractError("primitive row episode differs")
    if row["arm"] == "UNIFORM_LEGAL":
        if row["checkpoint"] is not None or row["roster"] not in (9, 15) or row["intervention"] != "INTACT":
            raise B01ContractError("UNIFORM_LEGAL must be once per seed at intact N9/N15")
    elif row["checkpoint"] not in CHECKPOINTS:
        raise B01ContractError("learned primitive checkpoint differs")
    tape = row["tape_binding"]
    metadata_checkpoint = 0 if row["checkpoint"] is None else row["checkpoint"]
    if not isinstance(tape, Mapping) or tape != {
        "schema": "FRRIE_B01_EVALUATION_TAPE_V1",
        "seed_label": row["seed_label"], "roster": row["roster"],
        "episode": row["episode"], "checkpoint": metadata_checkpoint,
        "checkpoint_role": "METADATA_ONLY",
        "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
        "arm_independent": True, "intervention_independent": True,
        "checkpoint_independent": True, "uniform_mapping": "TOP24 / 2**24",
    }:
        raise B01ContractError("primitive row tape binding is not common/addressed")
    for field in ("J", "WASTE"):
        if isinstance(row[field], bool) or not isinstance(row[field], (int, float)) or not math.isfinite(row[field]):
            raise B01ContractError(f"primitive row {field} is nonfinite")
        if not 0.0 <= float(row[field]) <= 1.0:
            raise B01ContractError(f"primitive row {field} is outside [0,1]")
    if (
        type(row["D_W"]) is not int or type(row["D_E"]) is not int
        or not 0 <= row["D_W"] <= 3 or not 0 <= row["D_E"] <= 3
    ):
        raise B01ContractError("primitive delivery counts must be integers")
    expected_j = native_endpoint(row["D_W"], row["D_E"], row["WASTE"])
    if float(row["J"]).hex() != float(expected_j).hex():
        raise B01ContractError("primitive J differs from terminal primitives")
    counts = row["role_action_counts"]
    if (
        not isinstance(counts, list) or len(counts) != 3
        or any(not isinstance(role, list) or len(role) != 6 for role in counts)
        or any(type(item) is not int or item < 0 for role in counts for item in role)
    ):
        raise B01ContractError("role action counts are incomplete")
    role_total = 12 * (row["roster"] // 3)
    legal_by_role = ({0, 1, 5}, {0, 1, 5}, {2, 3, 4, 5})
    for role in range(3):
        if sum(counts[role]) != role_total or any(
            counts[role][action] != 0 for action in range(6) if action not in legal_by_role[role]
        ):
            raise B01ContractError("role action counts violate exact role opportunities")
    for field in (
        "successful_scan", "successful_uplink", "successful_receive",
        "successful_delivery", "expired", "duplicate", "collision", "empty_radio",
    ):
        if type(row[field]) is not int or row[field] < 0:
            raise B01ContractError(f"primitive {field} must be nonnegative integer")
    scan_opportunities = counts[0][0] + counts[1][0]
    uplink_opportunities = counts[0][1] + counts[1][1]
    receive_opportunities = counts[2][2] + counts[2][3]
    radio_opportunities = uplink_opportunities + receive_opportunities + counts[2][4]
    if (
        row["successful_scan"] > scan_opportunities
        or row["successful_uplink"] > uplink_opportunities
        or row["successful_receive"] > receive_opportunities
        or row["successful_delivery"] != row["D_W"] + row["D_E"]
        or row["empty_radio"] > radio_opportunities
    ):
        raise B01ContractError("primitive success/empty counts exceed direct action opportunities")
    return row


def validate_complete_panel(panel: Any, manifest: Mapping[str, Any]) -> dict[str, Any]:
    manifest0 = validate_manifest(manifest)
    fields = {
        "schema", "manifest_contract", "invocation_binding", "performance_evidence",
        "rows", "training_primitives", "checkpoint_restore_receipts",
        "action_probability_rows", "raw_control_receipt", "complete",
    }
    if not isinstance(panel, Mapping) or set(panel) != fields:
        raise B01ContractError("complete production panel fields differ")
    value = dict(panel)
    if value["schema"] != PANEL_SCHEMA or value["manifest_contract"] != manifest0 or value["complete"] is not True:
        raise B01ContractError("complete production panel identity differs")
    validate_invocation_binding(value["invocation_binding"], require_test_only=False)
    raise B01ContractError(
        "PRODUCTION_PANEL_VALIDATION_UNAVAILABLE/REPAIR_REQUIRED: exact training, "
        "checkpoint-restore, action-probability, support, and 28-quantity inventories are not implemented"
    )


def validate_test_panel(panel: Any, manifest: Mapping[str, Any]) -> dict[str, Any]:
    manifest0 = validate_test_manifest(manifest)
    fields = {"schema", "manifest_contract", "invocation_binding", "rows", "complete"}
    if not isinstance(panel, Mapping) or set(panel) != fields:
        raise B01ContractError("TEST panel fields differ")
    value = dict(panel)
    if value["schema"] != "FRRIE_B01_TEST_ONLY_PANEL_V1" or value["manifest_contract"] != manifest0 or value["complete"] is not True:
        raise B01ContractError("TEST panel identity differs")
    validate_invocation_binding(value["invocation_binding"], require_test_only=True)
    if not isinstance(value["rows"], list) or not value["rows"]:
        raise B01ContractError("TEST panel needs direct primitive rows")
    for row in value["rows"]:
        validate_primitive_row(row, seed_labels={manifest0["seed_label"]}, test_only=True)
    return value
