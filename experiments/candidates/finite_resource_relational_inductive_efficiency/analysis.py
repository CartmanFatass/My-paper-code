"""Complete-panel-only FRRIE reduction with competence-first ordering.

Only deterministic block and gate inputs are computed. The frozen contract does not
freeze a simultaneous-bound procedure, so this module emits no polarity.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Sequence

from .contracts.core import (
    EVALUATIONS_PER_CELL,
    FRRIE_COMPLETE_PANEL_RESULT_V1,
    HELDOUT_ROSTERS,
    INTERVENTIONS,
    LEARNED_ARMS,
    TRAIN_ROSTERS,
    ContractError,
    validate_manifest,
)
from .host import HORIZON, LEGAL_ACTIONS_BY_ROLE, PUBLIC_ROLES, native_endpoint


class IncompletePanel(ContractError):
    pass


def _exact_keys(value: Mapping[str, Any], keys: set[str], field: str) -> None:
    if set(value) != keys:
        raise IncompletePanel(f"{field} fields must be exact")


def _mean(values: Iterable[float]) -> float:
    materialized = tuple(float(value) for value in values)
    if not materialized:
        raise IncompletePanel("required complete-panel reduction is empty")
    return math.fsum(materialized) / len(materialized)


def _validate_tapes(row: Mapping[str, Any]) -> None:
    tapes = row["tape_contracts"]
    if not isinstance(tapes, list) or len(tapes) != EVALUATIONS_PER_CELL:
        raise IncompletePanel("cell must carry every direct evaluation tape contract")
    for episode, tape in enumerate(tapes):
        expected = {
            "schema": "FRRIE_ADDRESSED_TAPE_V1",
            "seed_block": row["seed_block"],
            "purpose": "EVALUATE",
            "roster": row["roster"],
            "update": row["checkpoint"],
            "episode": episode,
        }
        if not isinstance(tape, Mapping) or dict(tape) != expected:
            raise IncompletePanel("cell tape contract does not bind its direct coordinates")


def _validate_action_counts(value: Any, roster: int) -> dict[str, tuple[int, ...]]:
    if not isinstance(value, Mapping) or set(value) != set(PUBLIC_ROLES):
        raise IncompletePanel("episode action counts must bind all three public roles")
    expected_per_role = HORIZON * (roster // 3)
    result: dict[str, tuple[int, ...]] = {}
    for role in PUBLIC_ROLES:
        counts = value[role]
        if (
            not isinstance(counts, list)
            or len(counts) != 6
            or any(type(count) is not int or count < 0 for count in counts)
            or sum(counts) != expected_per_role
        ):
            raise IncompletePanel("episode action counts have the wrong shape or total")
        legal = set(LEGAL_ACTIONS_BY_ROLE[role])
        if any(counts[action] for action in range(6) if action not in legal):
            raise IncompletePanel("episode contains an illegal role-masked action")
        result[role] = tuple(counts)
    return result


def _validate_episode(record: Mapping[str, Any], roster: int) -> dict[str, Any]:
    _exact_keys(record, {"dw", "de", "waste", "action_counts_by_role"}, "episode")
    if type(record["dw"]) is not int or type(record["de"]) is not int:
        raise IncompletePanel("episode delivery primitives must be integer counts")
    waste = record["waste"]
    if isinstance(waste, bool) or not isinstance(waste, (int, float)) or not math.isfinite(float(waste)):
        raise IncompletePanel("episode waste primitive must be finite")
    try:
        native_return = native_endpoint(record["dw"], record["de"], float(waste))
    except ContractError as exc:
        raise IncompletePanel("episode endpoint primitive is outside support") from exc
    return {
        "native_return": native_return,
        "basin_delivery": min(record["dw"], record["de"]) / 3.0,
        "action_counts_by_role": _validate_action_counts(record["action_counts_by_role"], roster),
    }


def validate_complete_panel(panel: Mapping[str, Any], manifest0: Mapping[str, Any]) -> list[dict[str, Any]]:
    manifest = validate_manifest(manifest0)
    _exact_keys(panel, {"schema", "manifest_contract", "complete", "cells"}, "panel")
    if panel["schema"] != FRRIE_COMPLETE_PANEL_RESULT_V1 or panel["complete"] is not True:
        raise IncompletePanel("panel is not a complete FRRIE result")
    if panel["manifest_contract"] != manifest:
        raise IncompletePanel("panel manifest contract differs from the validated contract")
    rows0 = panel["cells"]
    if not isinstance(rows0, list):
        raise IncompletePanel("panel cells must be a list")
    row_fields = {
        "seed_block", "arm", "checkpoint", "roster", "intervention", "episodes",
        "tape_contracts", "episode_records", "support_valid",
    }
    rows: list[dict[str, Any]] = []
    observed: set[tuple[Any, ...]] = set()
    for index, row0 in enumerate(rows0):
        if not isinstance(row0, Mapping):
            raise IncompletePanel(f"panel cell {index} must be an object")
        _exact_keys(row0, row_fields, f"panel cell {index}")
        key = (row0["seed_block"], row0["arm"], row0["checkpoint"], row0["roster"], row0["intervention"])
        if key in observed:
            raise IncompletePanel("duplicate panel cell")
        observed.add(key)
        if row0["episodes"] != EVALUATIONS_PER_CELL or type(row0["support_valid"]) is not bool:
            raise IncompletePanel("panel cell lacks exact episodes/support flag")
        _validate_tapes(row0)
        if not row0["support_valid"]:
            if row0["episode_records"] is not None:
                raise IncompletePanel("unsupported cell must not expose partial scientific values")
            rows.append(dict(row0))
            continue
        records0 = row0["episode_records"]
        if not isinstance(records0, list) or len(records0) != EVALUATIONS_PER_CELL:
            raise IncompletePanel("supported cell must contain all episode primitives")
        records = [_validate_episode(record, row0["roster"]) for record in records0]
        row = dict(row0)
        row["native_return"] = _mean(record["native_return"] for record in records)
        row["basin_delivery"] = _mean(record["basin_delivery"] for record in records)
        row["legal_action_rate"] = 1.0
        row["action_counts_by_role"] = {
            role: tuple(sum(record["action_counts_by_role"][role][action] for record in records) for action in range(6))
            for role in PUBLIC_ROLES
        }
        rows.append(row)
    required = {
        (block, arm, checkpoint, roster, intervention)
        for block in manifest["seed_blocks"]
        for arm in (*LEARNED_ARMS, "UNIFORM_LEGAL")
        for checkpoint in manifest["training"]["checkpoints"]
        for roster in (*TRAIN_ROSTERS, *HELDOUT_ROSTERS)
        for intervention in INTERVENTIONS
    }
    if observed != required:
        raise IncompletePanel("complete panel cell contract set mismatch")
    return rows


def _select(rows: Sequence[Mapping[str, Any]], *, arm: str, checkpoint: int, roster: int, intervention: str) -> list[Mapping[str, Any]]:
    selected = [row for row in rows if row["arm"] == arm and row["checkpoint"] == checkpoint and row["roster"] == roster and row["intervention"] == intervention]
    if not selected:
        raise IncompletePanel("registered cell reduction is absent")
    return selected


def _cell_mean(rows: Sequence[Mapping[str, Any]], metric: str, *, arm: str, checkpoint: int, roster: int, intervention: str) -> float:
    return _mean(row[metric] for row in _select(rows, arm=arm, checkpoint=checkpoint, roster=roster, intervention=intervention))


def _cell_action_tv(rows: Sequence[Mapping[str, Any]], *, checkpoint: int, roster: int, intervention: str) -> dict[str, float]:
    totals = {arm: {role: [0] * 6 for role in PUBLIC_ROLES} for arm in LEARNED_ARMS}
    for arm in LEARNED_ARMS:
        for row in _select(rows, arm=arm, checkpoint=checkpoint, roster=roster, intervention=intervention):
            for role in PUBLIC_ROLES:
                for action, count in enumerate(row["action_counts_by_role"][role]):
                    totals[arm][role][action] += count
    output = {}
    for role in PUBLIC_ROLES:
        distributions = {}
        for arm in LEARNED_ARMS:
            denominator = sum(totals[arm][role])
            distributions[arm] = [count / denominator for count in totals[arm][role]]
        output[role] = 0.5 * math.fsum(abs(left - right) for left, right in zip(distributions["PHY_TRUST"], distributions["EDGE_FLEX"]))
    return output


def generic_competence_passes(panel: Mapping[str, Any], manifest0: Mapping[str, Any]) -> bool:
    manifest = validate_manifest(manifest0)
    rows = validate_complete_panel(panel, manifest)
    edge = [row for row in rows if row["arm"] == "EDGE_FLEX" and row["checkpoint"] == 512 and row["intervention"] == "INTACT"]
    if any(not row["support_valid"] for row in edge):
        return False
    held = [row for row in edge if row["roster"] in HELDOUT_ROSTERS]
    seen = [row for row in edge if row["roster"] in TRAIN_ROSTERS]
    metrics = {
        "heldout_direct_return_lower": min(row["native_return"] for row in held),
        "seen_direct_return_lower": min(row["native_return"] for row in seen),
        "worst_basin_delivery_lower": min(row["basin_delivery"] for row in edge),
        "legal_action_validity_lower": min(row["legal_action_rate"] for row in edge),
    }
    return all(float(metrics[field]) >= float(bound) for field, bound in manifest["generic_competence"].items())


def _work_crossings(rows: Sequence[Mapping[str, Any]], manifest: Mapping[str, Any]) -> dict[str, dict[str, int | None]]:
    checkpoints = manifest["training"]["checkpoints"]
    thresholds = manifest["work_to_threshold"]["thresholds_by_roster"]
    output = {}
    for arm in LEARNED_ARMS:
        by_roster = {}
        for roster in (*TRAIN_ROSTERS, *HELDOUT_ROSTERS):
            threshold = float(thresholds[str(roster)])
            by_roster[str(roster)] = next((checkpoint for checkpoint in checkpoints if _cell_mean(rows, "native_return", arm=arm, checkpoint=checkpoint, roster=roster, intervention="INTACT") >= threshold), None)
        output[arm] = by_roster
    return output


def analyze_complete_panel(panel: Mapping[str, Any], manifest0: Mapping[str, Any]) -> dict[str, Any]:
    manifest = validate_manifest(manifest0)
    rows = validate_complete_panel(panel, manifest)
    base = {"schema": "FRRIE_COMPLETE_PANEL_ANALYSIS_V1", "complete": True, "manifest_contract": manifest}
    if any(not row["support_valid"] for row in rows):
        return {**base, "status": "NONIDENTIFICATION_ENDPOINT_SUPPORT", "treatment_contrasts_computed": False}
    if not generic_competence_passes(panel, manifest):
        return {**base, "status": "NONIDENTIFICATION_GENERIC_INCOMPETENCE", "treatment_contrasts_computed": False}
    cell_returns = {
        (roster, intervention, arm): _cell_mean(rows, "native_return", arm=arm, checkpoint=512, roster=roster, intervention=intervention)
        for roster in (*TRAIN_ROSTERS, *HELDOUT_ROSTERS) for intervention in INTERVENTIONS for arm in LEARNED_ARMS
    }
    contrasts = {
        f"N{roster}:{intervention}": cell_returns[(roster, intervention, "PHY_TRUST")] - cell_returns[(roster, intervention, "EDGE_FLEX")]
        for roster in (*TRAIN_ROSTERS, *HELDOUT_ROSTERS) for intervention in INTERVENTIONS
    }
    interaction_values = {
        f"heldout_N{heldout}-seen_N{seen}": contrasts[f"N{heldout}:INTACT"] - contrasts[f"N{seen}:INTACT"]
        for heldout in HELDOUT_ROSTERS for seen in TRAIN_ROSTERS
    }
    treatment_cut = {str(roster): cell_returns[(roster, "INTACT", "PHY_TRUST")] - cell_returns[(roster, "SEMANTIC_COLUMN_ROTATE", "PHY_TRUST")] for roster in HELDOUT_ROSTERS}
    edge_cut = {str(roster): cell_returns[(roster, "INTACT", "EDGE_FLEX")] - cell_returns[(roster, "SEMANTIC_COLUMN_ROTATE", "EDGE_FLEX")] for roster in HELDOUT_ROSTERS}
    basin = {
        str(roster): _cell_mean(rows, "basin_delivery", arm="PHY_TRUST", checkpoint=512, roster=roster, intervention="INTACT") - _cell_mean(rows, "basin_delivery", arm="EDGE_FLEX", checkpoint=512, roster=roster, intervention="INTACT")
        for roster in HELDOUT_ROSTERS
    }
    action_tv = {str(roster): _cell_action_tv(rows, checkpoint=512, roster=roster, intervention="INTACT") for roster in HELDOUT_ROSTERS}
    differential = {roster: treatment_cut[roster] - edge_cut[roster] for roster in treatment_cut}
    block_contrasts = {}
    for block in manifest["seed_blocks"]:
        block_rows = [row for row in rows if row["seed_block"] == block]
        block_contrasts[block] = {
            f"N{roster}:{intervention}": _cell_mean(block_rows, "native_return", arm="PHY_TRUST", checkpoint=512, roster=roster, intervention=intervention) - _cell_mean(block_rows, "native_return", arm="EDGE_FLEX", checkpoint=512, roster=roster, intervention=intervention)
            for roster in (*TRAIN_ROSTERS, *HELDOUT_ROSTERS) for intervention in INTERVENTIONS
        }
    deterministic_inputs = {
        "heldout_direct_return": min(contrasts[f"N{roster}:INTACT"] for roster in HELDOUT_ROSTERS),
        "heldout_minus_seen_interactions": interaction_values,
        "heldout_minus_seen_interaction_worst": min(interaction_values.values()),
        "worst_basin_delivery_by_roster": basin,
        "worst_basin_delivery": min(basin.values()),
        "treatment_cut_loss_by_roster": treatment_cut,
        "treatment_cut_loss": min(treatment_cut.values()),
        "legal_action_tv_by_roster_and_role": action_tv,
        "legal_action_tv": min(value for by_role in action_tv.values() for value in by_role.values()),
        "differential_cut_attenuation_by_roster": differential,
        "differential_cut_attenuation": min(differential.values()),
    }
    return {
        **base,
        "status": "UNRESOLVED_ANALYSIS_METHOD_UNFROZEN",
        "treatment_contrasts_computed": True,
        "scientific_polarity": None,
        "cell_contrasts": dict(sorted(contrasts.items())),
        "block_contrasts": block_contrasts,
        "deterministic_gate_inputs": deterministic_inputs,
        "point_work_to_threshold_crossings": _work_crossings(rows, manifest),
    }
