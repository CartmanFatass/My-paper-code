"""Complete-result validation and atomic create-only publication."""

from __future__ import annotations

import os
import json
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product
from pathlib import Path

from .factorial import construct_world, nuisance_coordinates, world_inventory_record
from .registered import PROTOCOL_ID, RESULT_SCHEMA, _build_complete_result, registered_spec
from .rng import canonical_bytes
from .schema import (
    AccessState,
    BindingState,
    CompleteResult,
    NuisanceCoordinate,
    OwnerState,
    PayloadState,
    PolicyArm,
    SemanticState,
    to_jsonable,
)


_BRANCHES = {
    "VALID_NARROW_PROTOCOL_VALUE",
    "INDEX_ABSORBS",
    "RAW_MISMATCH_OR_TIE",
    "NO_CAPABILITY_EDGE",
    "NO_CONTENT_EDGE",
    "INVALID",
}


def validate_complete_result(result: CompleteResult) -> None:
    """Reject any partial, inconsistent, noncanonical, or identity-shifted result."""

    errors: list[str] = []
    if not isinstance(result, CompleteResult):
        raise TypeError("result must be a CompleteResult")
    if result.schema != RESULT_SCHEMA:
        errors.append("result schema identity")
    if result.complete is not True:
        errors.append("complete barrier")
    spec = registered_spec()
    if set(result.identity) != {"direction_id", "protocol_id", "nuisance_version"}:
        errors.append("exact identity key set")
    if result.identity.get("direction_id") != spec.direction_id:
        errors.append("direction identity")
    if result.identity.get("protocol_id") != PROTOCOL_ID:
        errors.append("protocol identity")
    if result.branch not in _BRANCHES:
        errors.append("registered result branch")
    if not result.interpretation_boundary:
        errors.append("interpretation boundary")
    expected_support = {
        "scientific_cell_count": 48,
        "nuisance_count_per_cell": 128,
        "world_count_per_arm": 6144,
        "policy_count": 6,
        "row_count": 36864,
    }
    if result.support != expected_support:
        errors.append("registered exact support")
    expected_rows = result.support.get("row_count")
    if type(expected_rows) is not int or expected_rows != len(result.rows):
        errors.append("support row count")
    expected_worlds = result.support.get("world_count_per_arm")
    expected_policies = result.support.get("policy_count")
    if type(expected_worlds) is not int or expected_worlds <= 0:
        errors.append("support world count")
    if type(expected_policies) is not int or expected_policies <= 0:
        errors.append("support policy count")
    if (
        type(expected_worlds) is int
        and type(expected_policies) is int
        and expected_rows != expected_worlds * expected_policies
    ):
        errors.append("rectangular support")
    seen: set[tuple[str, PolicyArm]] = set()
    previous: tuple[str, str] | None = None
    worlds: set[str] = set()
    policies: set[PolicyArm] = set()
    world_policies: dict[str, set[PolicyArm]] = defaultdict(set)
    world_nuisance: dict[str, str] = {}
    for row in result.rows:
        key = (row.world_id, row.policy)
        sort_key = (row.world_id, row.policy.value)
        if key in seen:
            errors.append("duplicate world-policy row")
            break
        if previous is not None and sort_key < previous:
            errors.append("noncanonical row order")
            break
        previous = sort_key
        seen.add(key)
        worlds.add(row.world_id)
        policies.add(row.policy)
        world_policies[row.world_id].add(row.policy)
        prior_nuisance = world_nuisance.setdefault(row.world_id, row.nuisance_id)
        if prior_nuisance != row.nuisance_id:
            errors.append("world nuisance identity mismatch")
            break
        if row.ledger.action is not row.decision:
            errors.append("decision-ledger action mismatch")
            break
        if row.ledger.net_return != row.action_values.for_action(row.decision):
            errors.append("decision-ledger value mismatch")
            break
        if any("authorization_result" in name for name, _ in row.observation.primitives):
            errors.append("pre-action authorization-result leak")
            break
    if type(expected_worlds) is int and len(worlds) != expected_worlds:
        errors.append("distinct world support")
    if type(expected_policies) is int and len(policies) != expected_policies:
        errors.append("distinct policy support")
    if any(policy_set != set(PolicyArm) for policy_set in world_policies.values()):
        errors.append("six-arm rectangular support")
    nuisance_world_counts = Counter(world_nuisance.values())
    expected_pairing = {
        "nuisance_version": "CBSC-F0-V1",
        "distinct_nuisance_ids": 128,
        "worlds_per_nuisance_id": 48,
        "controller_or_action_in_address": False,
    }
    if result.pairing != expected_pairing:
        errors.append("registered exact pairing")
    if len(nuisance_world_counts) != 128 or set(nuisance_world_counts.values()) != {48}:
        errors.append("nuisance pairing multiplicity")
    expected_row_order = {
        "law": "LEXICOGRAPHIC_WORLD_ID_THEN_POLICY",
        "row_count": len(result.rows),
        "first_key": [result.rows[0].world_id, result.rows[0].policy.value] if result.rows else None,
        "last_key": [result.rows[-1].world_id, result.rows[-1].policy.value] if result.rows else None,
    }
    expected_inventory = {
        "policies": [arm.value for arm in spec.policies],
        "actions": [action.value for action in spec.actions],
        "terminal_clocks": [0, 1],
        "ledger_components": [
            "common_validation_read",
            "padded_terminal_service_actuation",
            "refresh_scan",
            "refresh_delay",
            "new_content_ingestion",
            "gross_correct_service",
            "gross_wrong_service",
            "gross_unauthorized_attempt",
            "gross_safe_fallback",
        ],
    }
    if set(result.manifests) != {"registered_spec", "row_order", "inventory", "world_inventory"}:
        errors.append("exact manifest key set")
    if result.manifests.get("registered_spec") != to_jsonable(spec):
        errors.append("direct registered-spec manifest")
    if result.manifests.get("row_order") != expected_row_order:
        errors.append("direct row-order manifest")
    if result.manifests.get("inventory") != expected_inventory:
        errors.append("direct action/policy/ledger inventory")
    structural_inventory = result.manifests.get("world_inventory")
    observed_coordinates: set[tuple[object, ...]] = set()
    inventory_world_ids: list[str] = []
    reconstructed_worlds = []
    if not isinstance(structural_inventory, list) or len(structural_inventory) != 6144:
        errors.append("complete structural world inventory")
    else:
        inventory_keys = {
            "world_id", "nuisance_id", "owner", "semantic", "binding", "access", "payload",
            "nuisance", "focal_need_active", "issued_inventory", "carrier_assignment", "presentation",
        }
        for entry in structural_inventory:
            try:
                if not isinstance(entry, dict) or set(entry) != inventory_keys:
                    raise ValueError("inventory key set")
                nuisance_payload = entry["nuisance"]
                nuisance_field_names = tuple(spec.nuisance_fields)
                if not isinstance(nuisance_payload, dict) or tuple(nuisance_payload) != nuisance_field_names:
                    raise ValueError("nuisance fields")
                coordinate = NuisanceCoordinate(*(nuisance_payload[name] for name in nuisance_field_names))
                owner = OwnerState(entry["owner"])
                semantic = SemanticState(entry["semantic"])
                binding = BindingState(entry["binding"])
                access = AccessState(entry["access"])
                payload = PayloadState(entry["payload"])
                world = construct_world(owner, semantic, binding, access, payload, coordinate)
                if entry != world_inventory_record(world):
                    raise ValueError("world structural record")
                observed_coordinates.add((owner, semantic, binding, access, payload, coordinate.address()))
                inventory_world_ids.append(world.world_id)
                reconstructed_worlds.append(world)
            except (KeyError, TypeError, ValueError) as error:
                errors.append(f"invalid structural world inventory: {error}")
                break
        expected_coordinates = {
            (owner, semantic, binding, access, payload, coordinate.address())
            for owner, semantic, binding, access, payload in product(
                spec.owner_levels,
                spec.semantic_levels,
                spec.binding_levels,
                spec.access_levels,
                spec.payload_levels,
            )
            for coordinate in nuisance_coordinates()
        }
        if observed_coordinates != expected_coordinates:
            errors.append("exact factorial coordinate inventory")
        if inventory_world_ids != sorted(inventory_world_ids) or len(set(inventory_world_ids)) != 6144:
            errors.append("canonical transparent world inventory order")
        expected_row_keys = sorted(
            (world_id, policy.value) for world_id in inventory_world_ids for policy in spec.policies
        )
        actual_row_keys = [(row.world_id, row.policy.value) for row in result.rows]
        if actual_row_keys != expected_row_keys:
            errors.append("complete canonical world-policy cross product")
    required_contrasts = {
        "capability_difference_in_differences",
        "owner_information_value_usable_cell",
        "retained_content_value_usable_cell",
        "correct_current_value",
        "swapped_current_value",
        "currentness_persist_minus_refresh",
        "receiver_correct_minus_swapped",
        "cbsc_min_selected_margin",
        "optimized_min_selected_margin_excluding_fixed_arms",
    }
    if not isinstance(result.audits, dict) or not result.audits:
        errors.append("invariant audits")
    if not isinstance(result.contrasts, dict):
        errors.append("exact contrasts")
    else:
        if set(result.contrasts) != required_contrasts:
            errors.append("complete exact contrasts")
        elif any(not isinstance(value, Fraction) for value in result.contrasts.values()):
            errors.append("exact Fraction contrasts")
    audit_order = (
        "raw_rowwise_identity",
        "cbsc_selected_is_unique_optimum",
        "cbsc_selected_margin_positive",
        "optimized_policy_decisions_unique_excluding_fixed_arms",
        "optimized_selected_margin_positive_excluding_fixed_arms",
        "hard_open_is_fixed_diagnostic",
        "open_predictive_index_equivalence",
        "open_zero_binding_action_value_effect",
        "currentness_clears_material_margin",
        "correct_swapped_clears_material_margin",
        "neutral_payload_never_direct",
        "capability_did_clears_material_margin",
        "owner_information_clears_material_margin",
        "retained_content_clears_material_margin",
        "no_preaction_authorization_result",
    )
    required_audits = set(audit_order)
    if set(result.audits) != required_audits:
        errors.append("complete invariant audits")
    elif any(type(value) is not bool for value in result.audits.values()):
        errors.append("boolean invariant audits")
    if result.interpretation_boundary != spec.interpretation_boundary:
        errors.append("registered interpretation boundary")
    if not errors and len(reconstructed_worlds) == spec.world_count:
        expected_result = _build_complete_result(spec, tuple(reconstructed_worlds))
        if result.rows != expected_result.rows:
            mismatch = next(
                (
                    (supplied.world_id, supplied.policy.value)
                    for supplied, expected in zip(result.rows, expected_result.rows)
                    if supplied != expected
                ),
                ("ROW_COUNT", "MISMATCH"),
            )
            errors.append(f"semantic row mismatch at world={mismatch[0]} policy={mismatch[1]}")
        if result != expected_result:
            errors.append("complete result differs from independently reconstructed exact semantics")
    try:
        import jsonschema

        schema_path = Path(__file__).with_name("schemas") / "cbsc_exact_factorial_result_v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(to_jsonable(result))
    except Exception as error:
        errors.append(f"Draft 2020-12 result schema: {type(error).__name__}")
    if errors:
        raise ValueError("invalid complete CBSC result: " + "; ".join(dict.fromkeys(errors)))


def _atomic_create_only_bytes(target: Path, payload: bytes) -> Path:
    """Atomic byte mechanic isolated from the complete-result validation gate."""

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"CBSC result publication is create-only: {target}")
    temporary: Path | None = None
    for counter in range(1024):
        candidate = target.with_name(f".{target.name}.cbsc-tmp-{os.getpid()}-{counter}")
        try:
            descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        temporary = candidate
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            candidate.unlink(missing_ok=True)
            raise
        break
    if temporary is None:
        raise FileExistsError("could not allocate bounded CBSC publication temporary")
    try:
        # A hard link is an atomic create operation and cannot replace a racer.
        os.link(temporary, target)
    except FileExistsError as error:
        raise FileExistsError(f"CBSC result publication is create-only: {target}") from error
    finally:
        temporary.unlink(missing_ok=True)
    return target


def write_complete_result(manifest_path: str | os.PathLike[str], result: CompleteResult) -> Path:
    """Publish canonical complete bytes atomically without replacing any target."""

    validate_complete_result(result)
    return _atomic_create_only_bytes(Path(manifest_path), canonical_bytes(result) + b"\n")


__all__ = ["validate_complete_result", "write_complete_result"]
