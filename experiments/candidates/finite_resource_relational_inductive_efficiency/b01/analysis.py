"""Deterministic descriptive reductions only; no B01 branch interpretation."""

from __future__ import annotations

import math
import statistics
from typing import Any, Mapping, Sequence

from .constants import (
    ANALYSIS_SCHEMA, CANDIDATE_QUANTITY_SCHEMA, CHECKPOINTS, EVALUATION_ROSTERS,
    HELDOUT_ROSTERS, INTERVENTIONS, LEARNED_ARMS, QUANTITY_MARGINS,
    QUANTITY_ORDER, TRAIN_ROSTERS,
)
from .contract import B01ContractError


_CELL_FIELDS = {
    "seed_label", "checkpoint", "arm", "roster", "intervention",
    "native_return", "basin_west", "basin_east", "legal_tv", "tv_sup",
}


def _finite(value: Any, name: str, *, unit: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise B01ContractError(f"candidate {name} must be a finite real")
    result = float(value)
    if not math.isfinite(result) or (unit and not 0.0 <= result <= 1.0):
        raise B01ContractError(f"candidate {name} is outside its direct finite support")
    return result


def _candidate_cell_order(seed_label: str, checkpoint: int) -> list[tuple[Any, ...]]:
    return [
        (seed_label, checkpoint, arm, roster, intervention)
        for arm in LEARNED_ARMS
        for roster in EVALUATION_ROSTERS
        for intervention in INTERVENTIONS
    ] + [
        (seed_label, None, "UNIFORM_LEGAL", roster, "INTACT")
        for roster in TRAIN_ROSTERS
    ]


def candidate_test_quantity_values(
    cells: Sequence[Mapping[str, Any]], *, seed_label: str, checkpoint: int,
) -> dict[str, float]:
    """Reduce already-direct episode/cell facts to the canonical 28 values.

    This TEST/candidate surface accepts caller cell summaries and therefore
    is never production-complete evidence.  It performs no branch, CI, or polarity
    interpretation.  A production panel may call it only after its streamed
    direct cell validators have completed.
    """

    if not isinstance(seed_label, str) or not seed_label or checkpoint not in CHECKPOINTS:
        raise B01ContractError("candidate seed/checkpoint coordinate differs")
    expected = _candidate_cell_order(seed_label, checkpoint)
    if not isinstance(cells, Sequence) or len(cells) != len(expected):
        raise B01ContractError("candidate cell inventory is incomplete")
    by_key: dict[tuple[str, int, str], dict[str, float]] = {}
    for index, (raw, coordinate) in enumerate(zip(cells, expected)):
        if not isinstance(raw, Mapping) or set(raw) != _CELL_FIELDS:
            raise B01ContractError("candidate cell fields differ")
        key = (
            raw["seed_label"], raw["checkpoint"], raw["arm"],
            raw["roster"], raw["intervention"],
        )
        if key != coordinate:
            raise B01ContractError(f"candidate cell order differs at index {index}")
        native_return = _finite(raw["native_return"], "native_return", unit=True)
        west = _finite(raw["basin_west"], "basin_west", unit=True)
        east = _finite(raw["basin_east"], "basin_east", unit=True)
        needs_tv = (
            raw["arm"] == "PHY_TRUST" and raw["intervention"] == "INTACT"
            and raw["roster"] in HELDOUT_ROSTERS
        )
        if needs_tv:
            legal_tv = _finite(raw["legal_tv"], "legal_tv", unit=True)
            tv_sup = _finite(raw["tv_sup"], "tv_sup", unit=True)
        else:
            if raw["legal_tv"] is not None or raw["tv_sup"] is not None:
                raise B01ContractError("shadow quantities may occur only in PHY/intact heldout cells")
            legal_tv = tv_sup = math.nan
        by_key[(raw["arm"], raw["roster"], raw["intervention"])] = {
            "native_return": native_return, "basin_west": west, "basin_east": east,
            "legal_tv": legal_tv, "tv_sup": tv_sup,
        }

    def cell(arm: str, roster: int, intervention: str = "INTACT") -> Mapping[str, float]:
        return by_key[(arm, roster, intervention)]

    def h(value: float, margin: float) -> float:
        return min(value, 1.0 - value) - margin

    direct = {
        roster: cell("PHY_TRUST", roster)["native_return"]
        - cell("EDGE_FLEX", roster)["native_return"]
        for roster in EVALUATION_ROSTERS
    }
    seen = 0.5 * (direct[9] + direct[15])
    values: dict[str, float] = {
        f"d_N{roster}": direct[roster] for roster in EVALUATION_ROSTERS
    }
    values.update({
        f"e_N{roster}": cell("EDGE_FLEX", roster)["native_return"]
        - cell("UNIFORM_LEGAL", roster)["native_return"]
        for roster in TRAIN_ROSTERS
    })
    for roster in HELDOUT_ROSTERS:
        phy = cell("PHY_TRUST", roster)
        edge = cell("EDGE_FLEX", roster)
        phy_rotate = cell("PHY_TRUST", roster, "SEMANTIC_COLUMN_ROTATE")
        edge_rotate = cell("EDGE_FLEX", roster, "SEMANTIC_COLUMN_ROTATE")
        values[f"c_N{roster}"] = direct[roster] - seen
        values[f"z_N{roster}"] = min(phy["basin_west"], phy["basin_east"]) - min(
            edge["basin_west"], edge["basin_east"]
        )
        values[f"C_PHY_N{roster}"] = phy["native_return"] - phy_rotate["native_return"]
        values[f"V_N{roster}"] = phy["legal_tv"]
        values[f"I_N{roster}"] = values[f"C_PHY_N{roster}"] - (
            edge["native_return"] - edge_rotate["native_return"]
        )
        values[f"A_cut_N{roster}"] = min(
            h(cell("PHY_TRUST", roster, cut)["native_return"], QUANTITY_MARGINS["delta_cutR"])
            for cut in INTERVENTIONS
        )
        values[f"A_atten_N{roster}"] = min(
            h(cell(arm, roster, cut)["native_return"], QUANTITY_MARGINS["delta_I"])
            for arm in LEARNED_ARMS for cut in INTERVENTIONS
        )
        values[f"A_TV_N{roster}"] = phy["tv_sup"] - QUANTITY_MARGINS["delta_TV"]
        values[f"A_dir_N{roster}"] = min(
            h(cell(arm, roster)["native_return"], QUANTITY_MARGINS["delta_R"])
            for arm in LEARNED_ARMS
        )
        values[f"A_interaction_N{roster}"] = min(
            h(cell(arm, other)["native_return"], QUANTITY_MARGINS["delta_C"])
            for arm in LEARNED_ARMS for other in (roster, *TRAIN_ROSTERS)
        )
        values[f"A_zone_N{roster}"] = min(
            h(cell(arm, roster)[basin], QUANTITY_MARGINS["delta_Z"])
            for arm in LEARNED_ARMS for basin in ("basin_west", "basin_east")
        )
    if set(values) != set(QUANTITY_ORDER) or any(not math.isfinite(value) for value in values.values()):
        raise B01ContractError("candidate 28-value family is incomplete or nonfinite")
    return {name: values[name] for name in QUANTITY_ORDER}


def quantity_values_from_validated_cells(value: Any) -> dict[str, float]:
    """Production reducer seam; caller summaries and partial support are refused."""

    from .panel import ValidatedCellSet
    if type(value) is not ValidatedCellSet or value.source_surface != "STREAMED_DIRECT_SHARDS_ONLY":
        raise B01ContractError("production quantities require streamed direct-shard validated cells")
    if not all(value.support_by_cell):
        raise B01ContractError(
            "NONIDENTIFICATION_DIRECT_CELL_SUPPORT: complete-case reduction is forbidden"
        )
    return candidate_test_quantity_values(
        value.cells, seed_label=value.seed_label, checkpoint=value.checkpoint,
    )


def summarize_candidate_quantities(
    rows: Sequence[Mapping[str, Any]], *, seed_labels: Sequence[str],
) -> dict[str, Any]:
    """Manifest-seed-order individual/mean/median/min/max descriptions only."""

    labels = tuple(seed_labels)
    if not labels or len(set(labels)) != len(labels):
        raise B01ContractError("candidate summary seed order differs")
    expected = [
        (seed, checkpoint, quantity)
        for seed in labels for checkpoint in CHECKPOINTS for quantity in QUANTITY_ORDER
    ]
    if not isinstance(rows, Sequence) or len(rows) != len(expected):
        raise B01ContractError("candidate quantity inventory cardinality differs")
    values: dict[tuple[str, int, str], float] = {}
    for index, (row, coordinate) in enumerate(zip(rows, expected)):
        if not isinstance(row, Mapping) or set(row) != {
            "seed_label", "checkpoint", "quantity", "value",
        }:
            raise B01ContractError("candidate quantity row fields differ")
        if (row["seed_label"], row["checkpoint"], row["quantity"]) != coordinate:
            raise B01ContractError(f"candidate quantity coordinate order differs at {index}")
        values[coordinate] = _finite(row["value"], "quantity value")
    summaries = []
    for checkpoint in CHECKPOINTS:
        for quantity in QUANTITY_ORDER:
            individual = [values[(seed, checkpoint, quantity)] for seed in labels]
            summaries.append({
                "checkpoint": checkpoint, "quantity": quantity,
                "individual": [
                    {"seed_label": seed, "value": value}
                    for seed, value in zip(labels, individual)
                ],
                "mean": math.fsum(individual) / len(individual),
                "median": statistics.median(individual),
                "min": min(individual), "max": max(individual),
            })
    return {
        "schema": CANDIDATE_QUANTITY_SCHEMA, "complete": True,
        "quantity_order": list(QUANTITY_ORDER), "seed_order": list(labels),
        "reduction_order": ["SEED_CHECKPOINT", "MANIFEST_SEED_ORDER"],
        "branch_interpretation": None, "confidence_intervals": None, "polarity": None,
        "summaries": summaries,
    }


def summarize_between_arm_tv(
    components: Sequence[Mapping[str, Any]], *, seed_labels: Sequence[str],
    checkpoint: int, roster: int, intervention: str,
) -> dict[str, Any]:
    """One-cell diagnostic summary; never pools checkpoints/rosters/cuts."""

    labels = tuple(seed_labels)
    if (
        not labels or len(set(labels)) != len(labels) or checkpoint not in CHECKPOINTS
        or roster not in EVALUATION_ROSTERS or intervention not in INTERVENTIONS
        or len(components) != len(labels)
    ):
        raise B01ContractError("between-arm diagnostic summary coordinate differs")
    available = []
    defects = []
    contact_seed_ids = []
    for seed, component in zip(labels, components):
        if not isinstance(component, Mapping) or component.get("seed_label") != seed or (
            component.get("checkpoint"), component.get("roster"), component.get("intervention")
        ) != (checkpoint, roster, intervention):
            raise B01ContractError("between-arm component manifest order differs")
        status = component.get("status")
        if status == "AVAILABLE":
            contact_seed_ids.append(seed)
            value = component.get("individual_cell_mean")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                defects.append({"seed_label": seed, "status": "UNAVAILABLE_MEASUREMENT_DEFECT"})
            else:
                available.append({"seed_label": seed, "value": float(value)})
        elif status == "UNAVAILABLE_MEASUREMENT_DEFECT":
            contact_seed_ids.append(seed)
            defects.append({"seed_label": seed, "status": status})
        elif status not in {"PRE_TIGHT_CONTACT", "NO_TIGHT_CONTACT_BY_512"}:
            raise B01ContractError("between-arm diagnostic component status differs")
    values = [row["value"] for row in available]
    status = (
        "DESCRIPTIVE_AVAILABLE" if values else
        "UNAVAILABLE_MEASUREMENT_DEFECT" if defects else
        "NO_POST_CONTACT_SEEDS"
    )
    return {
        "schema": "FRRIE_B01_BETWEEN_ARM_TV_SUMMARY_V1",
        "role": "MANDATORY_DESCRIPTIVE_NON_GATE", "selected_anchor": "SYMMETRIC",
        "included_in_ordered_28": False,
        "checkpoint": checkpoint, "roster": roster, "intervention": intervention,
        "contact_seed_ids": contact_seed_ids, "contact_count": len(contact_seed_ids),
        "valid_value_seed_ids": [row["seed_label"] for row in available],
        "valid_value_count": len(available), "individual": available,
        "mean": None if not values else math.fsum(values) / len(values),
        "median": None if not values else statistics.median(values),
        "min": None if not values else min(values),
        "max": None if not values else max(values),
        "status": status,
        "unavailable_reason": (
            "NO_VALID_DIAGNOSTIC_VALUES" if status == "UNAVAILABLE_MEASUREMENT_DEFECT" else None
        ),
        "measurement_defects": defects,
        "branch_interpretation": None, "confidence_intervals": None, "polarity": None,
    }


def summarize_parameter_distance_checkpoints(
    indexes_by_seed: Mapping[str, Any], *, seed_order: Sequence[str],
) -> dict[str, Any]:
    """Display the Pro-frozen parameter L-infinity decomposition at checkpoints."""

    import math
    import struct
    from .constants import CHECKPOINTS, UPDATES

    labels = tuple(seed_order)
    if not labels or len(set(labels)) != len(labels) or set(indexes_by_seed) != set(labels):
        raise B01ContractError("parameter-distance summary seed inventory/order differs")

    def from_bits(bits: Any) -> float:
        if type(bits) is not int or not 0 <= bits < 2**64:
            raise B01ContractError("parameter-distance binary64 bits are invalid")
        value = struct.unpack("<d", struct.pack("<Q", bits))[0]
        if not math.isfinite(value) or value < 0.0:
            raise B01ContractError("parameter-distance scalar is nonfinite or negative")
        return value

    def bits(value: float) -> int:
        return struct.unpack("<Q", struct.pack("<d", float(value)))[0]

    normalized = {}
    for seed in labels:
        index = indexes_by_seed[seed]
        if (
            not isinstance(index, Mapping)
            or index.get("schema") != "FRRIE_B01_PARAMETER_DISTANCE_AVAILABILITY_INDEX_V1"
            or index.get("seed_block") != seed
            or not isinstance(index.get("records"), list)
            or len(index["records"]) != UPDATES
            or index.get("temporal_reducer") is not None
            or index.get("included_in_ordered_28") is not False
            or index.get("production_gate") is not False
        ):
            raise B01ContractError("parameter-distance validated index contract differs")
        normalized[seed] = index
    component_fields = {
        "LINF_FULL": "linf_full_binary64_bits_u64",
        "LINF_BETA": "linf_beta_binary64_bits_u64",
        "LINF_NONBETA": "linf_nonbeta_binary64_bits_u64",
    }
    checkpoint_rows = []
    for checkpoint in CHECKPOINTS:
        available_rows = []
        defects = []
        contact_seed_ids = []
        for seed in labels:
            kappa = normalized[seed]["first_tight_contact_update"]
            if kappa is not None and kappa <= checkpoint:
                contact_seed_ids.append(seed)
            if checkpoint == 0:
                continue
            record = normalized[seed]["records"][checkpoint - 1]
            if record.get("available") is True:
                derived = record.get("derived")
                if not isinstance(derived, Mapping):
                    raise B01ContractError("available parameter-distance record lacks direct derived bits")
                available_rows.append((seed, derived))
            elif record.get("availability_reason") in {
                "PARAMETER_DISTANCE_MEASUREMENT_DEFECT",
                "PARAMETER_DISTANCE_NONFINITE_RECORD",
            }:
                defects.append({
                    "seed_block": seed,
                    "availability_reason": record["availability_reason"],
                    "diagnostic_error": record.get("diagnostic_error"),
                })
        components = {}
        for name, field in component_fields.items():
            individual = [
                {
                    "seed_block": seed, "binary64_bits_u64": derived[field],
                    "display_value": from_bits(derived[field]),
                }
                for seed, derived in available_rows
            ]
            values = [row["display_value"] for row in individual]
            if values:
                ordered = sorted(values)
                count = len(ordered)
                median = (
                    ordered[count // 2] if count % 2
                    else math.fsum((ordered[count // 2 - 1], ordered[count // 2])) / 2.0
                )
                summary = {
                    "individual": individual,
                    "mean_binary64_bits_u64": bits(math.fsum(values) / count),
                    "median_binary64_bits_u64": bits(median),
                    "minimum_binary64_bits_u64": bits(ordered[0]),
                    "maximum_binary64_bits_u64": bits(ordered[-1]),
                }
            else:
                summary = {
                    "individual": [], "mean_binary64_bits_u64": None,
                    "median_binary64_bits_u64": None, "minimum_binary64_bits_u64": None,
                    "maximum_binary64_bits_u64": None,
                }
            components[name] = summary
        if available_rows:
            status = "DESCRIPTIVE_AVAILABLE"
        elif defects:
            status = "UNAVAILABLE_MEASUREMENT_DEFECT"
        else:
            status = "NO_POSTCONTACT_SEEDS"
        checkpoint_rows.append({
            "checkpoint": checkpoint, "status": status,
            "contact_seed_ids": contact_seed_ids, "contact_seed_count": len(contact_seed_ids),
            "available_seed_ids": [row[0] for row in available_rows],
            "available_seed_count": len(available_rows), "defects": defects,
            "components": components,
        })
    return {
        "schema": "FRRIE_B01_PARAMETER_DISTANCE_CHECKPOINT_SUMMARY_V1",
        "seed_order": list(labels), "checkpoints": checkpoint_rows,
        "state_stage": "POSTPROJECTION",
        "measurement_role": "MANDATORY_DESCRIPTIVE_NON_GATE",
        "temporal_reducer": None, "confidence_intervals": False,
        "cross_checkpoint_pooling": False, "included_in_ordered_28": False,
        "branch_or_gate": False,
    }


def descriptive_analysis(panel: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    raise B01ContractError(
        "PRODUCTION_ANALYSIS_UNAVAILABLE/REPAIR_REQUIRED: exact complete panel and 28-quantity reduction are not implemented"
    )
