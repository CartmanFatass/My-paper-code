"""FRRIE v2 complete-panel, block-level reduction and frozen inference."""

from __future__ import annotations

import math
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts.core import (
    EVALUATIONS_PER_CELL, FP32_PROBABILITY_TOLERANCE, FRRIE_CHECKPOINT_V2,
    FRRIE_COMPLETE_PANEL_ANALYSIS_V2, FRRIE_COMPLETE_PANEL_RESULT_V2,
    FRRIE_SEALED_SEED_PACKET_V2,
    HELDOUT_ROSTERS, INTERVENTIONS, LEARNED_ARMS, QUANTITY_ORDER,
    REQUIRED_SEED_BLOCKS, THRESHOLDS, TRAIN_ROSTERS, ContractError,
    expected_block_checkpoint_path, expected_native_contract_record, validate_manifest,
)
from .host import HORIZON, LEGAL_ACTIONS_BY_ROLE, PUBLIC_ROLES, native_endpoint
from .work import checkpoint_cumulative_work, final_cumulative_work

ANALYSIS_SCHEMA = FRRIE_COMPLETE_PANEL_ANALYSIS_V2
ALL_ARMS = (*LEARNED_ARMS, "UNIFORM_LEGAL")
ALL_ROSTERS = (*TRAIN_ROSTERS, *HELDOUT_ROSTERS)


class IncompletePanel(ContractError):
    pass


class CheckpointBytesUnvalidated(IncompletePanel):
    pass


def _seed_packet_binding(manifest: Mapping[str, Any], block: str, provenance: str) -> dict[str, Any]:
    index = manifest["seed_blocks"].index(block)
    return {
        "packet_path": manifest["sealed_seed_packet"]["path"],
        "schema": FRRIE_SEALED_SEED_PACKET_V2,
        "version": 2,
        "block_index": index,
        "block_label": block,
        "generation_provenance": provenance,
        "no_prior_use": True,
    }


def expected_checkpoint_inventory(
    manifest: Mapping[str, Any], *, generation_provenance: str,
    checkpoint_bytes_revalidated: bool,
) -> dict[str, Any]:
    """Construct the direct, digest-free block checkpoint inventory."""
    if not isinstance(generation_provenance, str) or not generation_provenance:
        raise IncompletePanel("checkpoint inventory requires direct seed generation provenance")
    if type(checkpoint_bytes_revalidated) is not bool:
        raise IncompletePanel("checkpoint byte revalidation state must be literal boolean")
    return {
        "schema": "FRRIE_PANEL_CHECKPOINT_INVENTORY_V2",
        "checkpoint_bytes_revalidated": checkpoint_bytes_revalidated,
        "blocks": [
            {
                "seed_block": block,
                "block_index": index,
                "update": 512,
                "checkpoint_path": str(expected_block_checkpoint_path(manifest, block)),
                "checkpoint_schema": FRRIE_CHECKPOINT_V2,
                "open_mode": "READ_ONLY",
                "seed_packet_binding": _seed_packet_binding(
                    manifest, block, generation_provenance,
                ),
            }
            for index, block in enumerate(manifest["seed_blocks"])
        ],
        "final_cumulative_receipt": final_cumulative_work(manifest["compute"]),
    }


def _cell_work(arm: str, roster: int, intervention: str) -> dict[str, Any]:
    learned = arm in LEARNED_ARMS
    decisions = EVALUATIONS_PER_CELL * HORIZON * roster if learned else 0
    shadow = (
        decisions if learned and roster in HELDOUT_ROSTERS and intervention == "INTACT"
        else 0
    )
    return {
        "schema": "FRRIE_CELL_WORK_V2",
        "environment_slots": EVALUATIONS_PER_CELL * HORIZON,
        "learned_policy_decisions": decisions,
        "shadow_audit_policy_decisions": shadow,
        "evaluation_opportunities": EVALUATIONS_PER_CELL,
    }


def expected_result_binding(
    manifest: Mapping[str, Any], inventory: Mapping[str, Any], *, block: str,
    arm: str, roster: int, intervention: str,
) -> dict[str, Any]:
    index = manifest["seed_blocks"].index(block)
    inventory_block = inventory["blocks"][index]
    if arm in LEARNED_ARMS:
        source = {
            "kind": "LEARNED_BLOCK_CHECKPOINT",
            "path": inventory_block["checkpoint_path"],
            "schema": FRRIE_CHECKPOINT_V2,
            "open_mode": "READ_ONLY",
            "checkpoint_bytes_revalidated": inventory["checkpoint_bytes_revalidated"],
        }
    else:
        source = {
            "kind": "UNIFORM_LEGAL_EVALUATION_ONLY",
            "path": None,
            "schema": None,
            "open_mode": "EVALUATION_ONLY_NO_CHECKPOINT",
            "checkpoint_bytes_revalidated": None,
        }
    return {
        "schema": "FRRIE_CELL_RESULT_BINDING_V2",
        "seed_block": block,
        "block_index": index,
        "arm": arm,
        "update": 512,
        "source": source,
        "seed_packet_binding": deepcopy(inventory_block["seed_packet_binding"]),
        "native_contract": expected_native_contract_record(manifest["compute"]),
        "package_source_relative_path": "native/frrie_ridgegate2z_external.cpp",
        "cell_work": _cell_work(arm, roster, intervention),
        "rng_tape_binding": {
            "mapping_schema": "FRRIE_ADDRESSED_FP32_UNIFORM_V1",
            "uniform_formula": "TOP24 / 2**24",
            "same_index_episode_tape": True,
            "arm_independent": True,
            "cut_independent": True,
            "branch_independent": True,
        },
    }


def _revalidate_checkpoint_files(
    manifest: Mapping[str, Any], inventory: Mapping[str, Any],
) -> None:
    """Independently restore exact checkpoint paths before value reduction."""
    from .checkpoint import restore_checkpoint

    packet_path = Path(manifest["sealed_seed_packet"]["path"])
    try:
        with packet_path.open("r", encoding="utf-8") as handle:
            packet = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckpointBytesUnvalidated(
            "current sealed seed packet is absent or unreadable during analysis"
        ) from exc
    if not isinstance(packet, Mapping):
        raise CheckpointBytesUnvalidated(
            "current sealed seed packet is not a direct object during analysis"
        )
    native_contract = expected_native_contract_record(manifest["compute"])
    try:
        for index, seed_block in enumerate(manifest["seed_blocks"]):
            expected_path = expected_block_checkpoint_path(manifest, seed_block)
            if inventory["blocks"][index]["checkpoint_path"] != str(expected_path):
                raise CheckpointBytesUnvalidated(
                    "checkpoint inventory path differs from exact manifest path"
                )
            with expected_path.open("rb") as handle:
                checkpoint_bytes = handle.read()
            restore_checkpoint(
                checkpoint_bytes,
                manifest_contract=manifest,
                native_contract=native_contract,
                seed_packet_contract=packet,
                expected_update=512,
                expected_seed_block=seed_block,
                seed_packet_path=manifest["sealed_seed_packet"]["path"],
            )
    except (OSError, ContractError, KeyError, IndexError, TypeError) as exc:
        if isinstance(exc, CheckpointBytesUnvalidated):
            raise
        raise CheckpointBytesUnvalidated(
            "exact block checkpoint files were not independently restored during analysis"
        ) from exc


def _exact_keys(value: Mapping[str, Any], keys: set[str], field: str) -> None:
    if set(value) != keys:
        raise IncompletePanel(f"{field} fields must be exact")


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IncompletePanel(f"{field} must be a finite real scalar")
    result = float(value)
    if not math.isfinite(result):
        raise IncompletePanel(f"{field} must be finite")
    return result


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise IncompletePanel("required complete-panel reduction is empty")
    return math.fsum(values) / len(values)


def _validate_receipts(value: Any, manifest: Mapping[str, Any]) -> tuple[bool, str | None]:
    if not isinstance(value, Mapping):
        raise IncompletePanel("panel receipts must be direct objects")
    _exact_keys(value, {"checkpoint", "work", "support"}, "receipts")
    expected = {
        "checkpoint": checkpoint_cumulative_work(manifest["compute"]),
        "work": final_cumulative_work(manifest["compute"]),
    }
    for name, wanted in expected.items():
        if not isinstance(value[name], Mapping) or dict(value[name]) != wanted:
            raise IncompletePanel(f"{name} receipt is absent, partial, or false")
    support = value["support"]
    if (not isinstance(support, Mapping)
            or set(support) != {"endpoint_support_complete", "complete", "reason"}
            or type(support["endpoint_support_complete"]) is not bool
            or support["complete"] is not True
            or (support["endpoint_support_complete"] and support["reason"] is not None)
            or (not support["endpoint_support_complete"] and not isinstance(support["reason"], str))
            or (isinstance(support["reason"], str) and not support["reason"])):
        raise IncompletePanel("support receipt is absent or partial")
    return support["endpoint_support_complete"], support["reason"]


def _validate_tapes(row: Mapping[str, Any]) -> None:
    tapes = row["tape_contracts"]
    if not isinstance(tapes, list) or len(tapes) != EVALUATIONS_PER_CELL:
        raise IncompletePanel("cell must carry all 256 addressed evaluation tapes")
    for episode, tape in enumerate(tapes):
        expected = {
            "schema": "FRRIE_ADDRESSED_TAPE_V1", "seed_block": row["seed_block"],
            "purpose": "EVALUATE", "roster": row["roster"], "update": 512,
            "episode": episode,
        }
        if not isinstance(tape, Mapping) or dict(tape) != expected:
            raise IncompletePanel("cell tape does not bind its direct coordinates")


def _probability_vector(value: Any, role: str, field: str) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != 6:
        raise IncompletePanel(f"{field} must be a six-action probability vector")
    vector = tuple(_finite(item, field) for item in value)
    legal = set(LEGAL_ACTIONS_BY_ROLE[role])
    if any(item < 0.0 or item > 1.0 for item in vector):
        raise IncompletePanel(f"{field} lies outside the probability simplex")
    if any(vector[action] != 0.0 for action in range(6) if action not in legal):
        raise IncompletePanel(f"{field} assigns probability to an illegal action")
    if not math.isclose(math.fsum(vector), 1.0, rel_tol=0.0, abs_tol=FP32_PROBABILITY_TOLERANCE):
        raise IncompletePanel(f"{field} does not sum to one")
    minimum = 0.04 / len(legal)
    if any(vector[action] + FP32_PROBABILITY_TOLERANCE < minimum for action in legal):
        raise IncompletePanel(f"{field} violates the frozen legal probability floor")
    return vector


def _decision_values(value: Any, roster: int) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != HORIZON * roster:
        raise IncompletePanel("intact PHY episode must carry every slot/entity probability pair")
    tv, tv_sup = [], []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise IncompletePanel("decision probability pair must be an object")
        _exact_keys(item, {"slot", "entity", "role", "intact", "shadow"}, "decision pair")
        slot, entity, role = item["slot"], item["entity"], item["role"]
        expected_role = PUBLIC_ROLES[min(entity // (roster // 3), 2)]
        if (slot != index // roster or entity != index % roster or role != expected_role):
            raise IncompletePanel("decision history is not in exact episode/slot/entity order")
        intact = _probability_vector(item["intact"], role, "intact probability")
        shadow = _probability_vector(item["shadow"], role, "shadow probability")
        legal = LEGAL_ACTIONS_BY_ROLE[role]
        tv.append(0.5 * math.fsum(abs(intact[a] - shadow[a]) for a in legal))
        m = len(legal)
        tv_sup.append(1.0 - (m - 1) * (0.04 / m) - min(intact[a] for a in legal))
    return _mean(tv), _mean(tv_sup)


def _validate_episode(
    record: Any, roster: int, needs_probabilities: bool, *, episode: int,
    tape_contract: Mapping[str, Any], decision_cache: dict[tuple[int, int], tuple[float, float]],
) -> dict[str, float]:
    if not isinstance(record, Mapping):
        raise IncompletePanel("episode primitive must be an object")
    _exact_keys(record, {"episode", "tape_contract", "dw", "de", "waste", "decision_probability_pairs"}, "episode")
    if record["episode"] != episode or record["tape_contract"] != tape_contract:
        raise IncompletePanel("episode primitive is not directly bound to its same-index tape")
    if type(record["dw"]) is not int or type(record["de"]) is not int:
        raise IncompletePanel("basin delivery primitives must be integer counts")
    waste = _finite(record["waste"], "episode waste")
    try:
        endpoint = native_endpoint(record["dw"], record["de"], waste)
    except ContractError as exc:
        raise IncompletePanel("episode endpoint primitive is outside support") from exc
    result = {"return": endpoint, "west": record["dw"] / 3.0, "east": record["de"] / 3.0}
    pairs = record["decision_probability_pairs"]
    if needs_probabilities:
        cache_key = (id(pairs), roster)
        if cache_key not in decision_cache:
            decision_cache[cache_key] = _decision_values(pairs, roster)
        result["tv"], result["tv_sup"] = decision_cache[cache_key]
    elif pairs is not None:
        raise IncompletePanel("only intact PHY episodes may carry shadow probability histories")
    return result


def validate_complete_panel(panel: Mapping[str, Any], manifest0: Mapping[str, Any]) -> list[dict[str, Any]]:
    manifest = validate_manifest(manifest0)
    if not isinstance(panel, Mapping):
        raise IncompletePanel("panel must be an object")
    _exact_keys(panel, {"schema", "manifest_contract", "complete", "receipts", "checkpoint_inventory", "cells"}, "panel")
    if panel["schema"] != FRRIE_COMPLETE_PANEL_RESULT_V2 or panel["complete"] is not True:
        raise IncompletePanel("panel is not a complete FRRIE result")
    if panel["manifest_contract"] != manifest:
        raise IncompletePanel("panel manifest contract differs from the validated contract")
    support_receipt, support_reason = _validate_receipts(panel["receipts"], manifest)
    inventory = panel["checkpoint_inventory"]
    try:
        provenance = inventory["blocks"][0]["seed_packet_binding"]["generation_provenance"]
        bytes_revalidated = inventory["checkpoint_bytes_revalidated"]
        expected_inventory = expected_checkpoint_inventory(
            manifest, generation_provenance=provenance,
            checkpoint_bytes_revalidated=bytes_revalidated,
        )
    except (KeyError, IndexError, TypeError, IncompletePanel) as exc:
        raise IncompletePanel("checkpoint inventory is absent or partial") from exc
    if inventory != expected_inventory or inventory["final_cumulative_receipt"] != panel["receipts"]["work"]:
        raise IncompletePanel("checkpoint inventory differs from the exact 24-block/final-work binding")
    if not bytes_revalidated:
        raise CheckpointBytesUnvalidated(
            "checkpoint inventory does not assert prior byte revalidation"
        )
    # The prior transaction receipt is necessary but never sufficient:
    # standalone analysis reopens and restores every exact file itself before
    # it can inspect any episode primitive or descriptive value.
    _revalidate_checkpoint_files(manifest, inventory)
    cells = panel["cells"]
    if not isinstance(cells, list):
        raise IncompletePanel("panel cells must be a list")
    expected_keys = [(block, arm, 512, roster, cut) for block in REQUIRED_SEED_BLOCKS
                     for arm in ALL_ARMS for roster in ALL_ROSTERS for cut in INTERVENTIONS]
    if len(cells) != len(expected_keys):
        raise IncompletePanel("complete panel cell contract set is partial")
    rows: list[dict[str, Any]] = []
    decision_cache: dict[tuple[int, int], tuple[float, float]] = {}
    fields = {"seed_block", "arm", "checkpoint", "roster", "intervention", "episodes", "tape_contracts", "episode_records", "support_valid", "support_reason", "result_binding"}
    for index, (row, wanted) in enumerate(zip(cells, expected_keys)):
        if not isinstance(row, Mapping):
            raise IncompletePanel(f"panel cell {index} must be an object")
        _exact_keys(row, fields, f"panel cell {index}")
        key = (row["seed_block"], row["arm"], row["checkpoint"], row["roster"], row["intervention"])
        if key != wanted:
            raise IncompletePanel("panel cells must follow manifest block and frozen cell order")
        if row["episodes"] != EVALUATIONS_PER_CELL or type(row["support_valid"]) is not bool:
            raise IncompletePanel("panel cell episode/support facts are invalid")
        expected_binding = expected_result_binding(
            manifest, inventory, block=row["seed_block"], arm=row["arm"],
            roster=row["roster"], intervention=row["intervention"],
        )
        if row["result_binding"] != expected_binding:
            raise IncompletePanel("cell result_binding differs from its direct V2 identity/work/RNG binding")
        if row["support_valid"] != support_receipt:
            raise IncompletePanel("cell and direct panel support receipts disagree")
        if row["support_valid"]:
            if row["support_reason"] is not None:
                raise IncompletePanel("supported cell must not carry a failure reason")
        elif not isinstance(row["support_reason"], str) or not row["support_reason"] or row["support_reason"] != support_reason:
            raise IncompletePanel("unsupported cell must carry the direct support reason")
        _validate_tapes(row)
        records = row["episode_records"]
        if not bytes_revalidated:
            if records is not None:
                raise IncompletePanel("unvalidated checkpoint bytes must expose no episode scientific values")
            rows.append(dict(row))
            continue
        if not row["support_valid"]:
            if records is not None:
                raise IncompletePanel("unsupported cell must expose no episode scientific values")
            rows.append(dict(row))
            continue
        if not isinstance(records, list) or len(records) != EVALUATIONS_PER_CELL:
            raise IncompletePanel("panel cell must carry every episode primitive without partial values")
        needs_probabilities = row["arm"] == "PHY_TRUST" and row["intervention"] == "INTACT"
        episodes = [
            _validate_episode(
                record, row["roster"], needs_probabilities, episode=episode,
                tape_contract=row["tape_contracts"][episode], decision_cache=decision_cache,
            )
            for episode, record in enumerate(records)
        ]
        reduced = dict(row)
        reduced.update({
            "native_return": _mean([episode["return"] for episode in episodes]),
            "basin_west": _mean([episode["west"] for episode in episodes]),
            "basin_east": _mean([episode["east"] for episode in episodes]),
            "support_valid": True,
        })
        if needs_probabilities:
            reduced["legal_tv"] = _mean([episode["tv"] for episode in episodes])
            reduced["tv_sup"] = _mean([episode["tv_sup"] for episode in episodes])
        rows.append(reduced)
    for arm in LEARNED_ARMS:
        final_row = inventory["final_cumulative_receipt"]["arms"][arm]
        for block in REQUIRED_SEED_BLOCKS:
            cell_work = [
                row["result_binding"]["cell_work"] for row in cells
                if row["arm"] == arm and row["seed_block"] == block
            ]
            totals = {
                "learned_eval_environment_slots": sum(row["environment_slots"] for row in cell_work),
                "learned_eval_policy_decisions": sum(row["learned_policy_decisions"] for row in cell_work),
                "shadow_audit_policy_decisions": sum(row["shadow_audit_policy_decisions"] for row in cell_work),
                "evaluation_opportunities": sum(row["evaluation_opportunities"] for row in cell_work),
            }
            if any(final_row[field] != value for field, value in totals.items()):
                raise IncompletePanel("cell work inventory does not sum to exact per-block work.py final counters")
    return rows


def _block_quantities(rows: Sequence[Mapping[str, Any]], block: str) -> dict[str, float]:
    by_key = {(row["arm"], row["roster"], row["intervention"]): row for row in rows if row["seed_block"] == block}
    def cell(arm: str, roster: int, cut: str = "INTACT") -> Mapping[str, Any]:
        return by_key[(arm, roster, cut)]
    def h(value: float, delta: float) -> float:
        return min(value, 1.0 - value) - delta
    direct = {n: cell("PHY_TRUST", n)["native_return"] - cell("EDGE_FLEX", n)["native_return"] for n in ALL_ROSTERS}
    seen = 0.5 * (direct[9] + direct[15])
    values: dict[str, float] = {f"d_N{n}": direct[n] for n in ALL_ROSTERS}
    values.update({f"e_N{n}": cell("EDGE_FLEX", n)["native_return"] - cell("UNIFORM_LEGAL", n)["native_return"] for n in TRAIN_ROSTERS})
    for n in HELDOUT_ROSTERS:
        pi, ei = cell("PHY_TRUST", n), cell("EDGE_FLEX", n)
        pr, er = cell("PHY_TRUST", n, "SEMANTIC_COLUMN_ROTATE"), cell("EDGE_FLEX", n, "SEMANTIC_COLUMN_ROTATE")
        values[f"c_N{n}"] = direct[n] - seen
        values[f"z_N{n}"] = min(pi["basin_west"], pi["basin_east"]) - min(ei["basin_west"], ei["basin_east"])
        values[f"C_PHY_N{n}"] = pi["native_return"] - pr["native_return"]
        values[f"V_N{n}"] = pi["legal_tv"]
        values[f"I_N{n}"] = values[f"C_PHY_N{n}"] - (ei["native_return"] - er["native_return"])
        values[f"A_cut_N{n}"] = min(h(cell("PHY_TRUST", n, cut)["native_return"], THRESHOLDS["delta_cutR"]) for cut in INTERVENTIONS)
        values[f"A_atten_N{n}"] = min(h(cell(arm, n, cut)["native_return"], THRESHOLDS["delta_I"]) for arm in LEARNED_ARMS for cut in INTERVENTIONS)
        values[f"A_TV_N{n}"] = pi["tv_sup"] - THRESHOLDS["delta_TV"]
        values[f"A_dir_N{n}"] = min(h(cell(arm, n)["native_return"], THRESHOLDS["delta_R"]) for arm in LEARNED_ARMS)
        values[f"A_interaction_N{n}"] = min(h(cell(arm, m)["native_return"], THRESHOLDS["delta_C"]) for arm in LEARNED_ARMS for m in (n, *TRAIN_ROSTERS))
        values[f"A_zone_N{n}"] = min(h(cell(arm, n)[basin], THRESHOLDS["delta_Z"]) for arm in LEARNED_ARMS for basin in ("basin_west", "basin_east"))
    if set(values) != set(QUANTITY_ORDER) or any(not math.isfinite(value) for value in values.values()):
        raise IncompletePanel("block quantity family is missing, reordered, or nonfinite")
    return {name: values[name] for name in QUANTITY_ORDER}


def _invalid(manifest: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {"schema": ANALYSIS_SCHEMA, "complete": False, "manifest_contract": dict(manifest),
            "status": "INVALID", "scientific_polarity": None,
            "invalid_reasons": [reason], "scientific_values_emitted": False}


def analyze_complete_panel(panel: Mapping[str, Any], manifest0: Mapping[str, Any]) -> dict[str, Any]:
    try:
        manifest = validate_manifest(manifest0)
    except ContractError as exc:
        return _invalid({}, str(exc))
    try:
        rows = validate_complete_panel(panel, manifest)
        if not all(row["support_valid"] for row in rows):
            return {
                "schema": ANALYSIS_SCHEMA, "complete": True, "manifest_contract": manifest,
                "status": "NONIDENTIFICATION_ENDPOINT_SUPPORT", "scientific_polarity": None,
                "scientific_values_emitted": False,
                "final_cumulative_receipt": dict(panel["receipts"]["work"]),
                "quantity_order": list(QUANTITY_ORDER), "intervals": None,
                "predicates": [], "predicate_flags": {"support_structural": False},
                "support_reason": panel["receipts"]["support"]["reason"],
            }
        block_values = {block: _block_quantities(rows, block) for block in REQUIRED_SEED_BLOCKS}
    except CheckpointBytesUnvalidated as exc:
        return {
            "schema": ANALYSIS_SCHEMA, "complete": False, "manifest_contract": manifest,
            "status": "TECHNICAL_FAILURE", "scientific_polarity": None,
            "scientific_values_emitted": False,
            "engineering_blockers": ["CHECKPOINT_BYTES_NOT_REVALIDATED"],
            "invalid_reasons": [str(exc)],
        }
    except (ContractError, KeyError, TypeError, ValueError) as exc:
        return _invalid(manifest, str(exc))
    support_structural = True
    status = "UNRESOLVED_ANALYSIS_METHOD_UNFROZEN"
    return {
        "schema": ANALYSIS_SCHEMA, "complete": True, "manifest_contract": manifest,
        "status": status, "scientific_polarity": None, "scientific_values_emitted": True,
        "final_cumulative_receipt": dict(panel["receipts"]["work"]),
        "quantity_order": list(QUANTITY_ORDER), "block_quantities": block_values,
        "inference": dict(manifest["inference"]), "intervals": None,
        "predicates": [], "predicate_flags": {"support_structural": support_structural},
    }


def generic_competence_passes(panel: Mapping[str, Any], manifest0: Mapping[str, Any]) -> bool:
    """Competence is not decidable until the distribution-free family is frozen."""
    analyze_complete_panel(panel, manifest0)
    return False
