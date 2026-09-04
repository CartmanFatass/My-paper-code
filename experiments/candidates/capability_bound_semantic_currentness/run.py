"""CBSC configuration inspection and sole future registered entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .artifact import write_complete_result
from .registered import RESULT_SCHEMA, SPEC_SCHEMA, evaluate_registered, registered_spec, validate_registered_spec
from .schema import rational_json


def configuration_payload() -> dict[str, object]:
    """Return identity/configuration only, with no question-relevant result fields."""

    spec = registered_spec()
    audit = validate_registered_spec(spec)
    return {
        "direction_id": spec.direction_id,
        "protocol_id": spec.protocol_id,
        "implementation_status": "READY_FOR_RESULT_BLIND_IMPLEMENTATION",
        "registered_spec_valid": audit.valid,
        "mode": "CONFIGURATION_ONLY",
        "result_activity": "ZERO",
        "host_schema": SPEC_SCHEMA,
        "result_schema": RESULT_SCHEMA,
        "factors": {
            "OWNER": [level.value for level in spec.owner_levels],
            "SEMANTIC": [level.value for level in spec.semantic_levels],
            "BINDING": [level.value for level in spec.binding_levels],
            "ACCESS": [level.value for level in spec.access_levels],
            "PAYLOAD": [level.value for level in spec.payload_levels],
        },
        "actions": [action.value for action in spec.actions],
        "arms": [arm.value for arm in spec.policies],
        "cardinalities": {
            "scientific_cells": spec.scientific_cell_count,
            "nuisance_per_cell": spec.nuisance_count,
            "worlds_per_arm": spec.world_count,
        },
        "cost_law": {name: rational_json(value) for name, value in spec.costs},
        "clocks": {
            "serve_terminal": 0,
            "safe_fallback_terminal": 0,
            "refresh_terminal": 1,
        },
        "material_margin": rational_json(spec.material_margin),
        "determinism": {
            "nuisance_version": spec.nuisance_version,
            "scientific_rng": 0,
            "optimizer_updates": 0,
            "seeds": 0,
            "checkpoints": 0,
            "canonical_row_sort": True,
        },
        "publication": {
            "atomic": True,
            "create_only": True,
            "complete_only": True,
            "preexisting_target_rejected": True,
        },
        "protocol_laws": {
            "order": list(spec.protocol_order),
            "all_payload_issuance": spec.all_payload_issuance_law,
            "phase_currentness": spec.phase_currentness_law,
            "reassociation": spec.reassociation_law,
            "authorization_information": spec.authorization_information_law,
            "action_clocks": [[name, clock] for name, clock in spec.action_clock_law],
            "determinism": list(spec.determinism_law),
            "publication": list(spec.publication_law),
            "branch_order": list(spec.branch_order),
            "cbsc_fixed_rule": [[condition, action] for condition, action in spec.cbsc_fixed_rule],
            "owner_blind": list(spec.owner_blind_law),
            "reset": list(spec.reset_law),
            "hard_open": list(spec.hard_open_law),
            "policy_capability": [[policy, law] for policy, law in spec.policy_capability_law],
            "action_ledger_incidence": [[action, list(entries)] for action, entries in spec.action_ledger_incidence],
            "contrast_formulas": [[name, formula] for name, formula in spec.contrast_laws],
            "delta_comparator": spec.delta_comparator,
            "branch_witness": spec.branch_witness_law,
        },
        "result_fields": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="capability_bound_semantic_currentness")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("configuration", help="emit result-blind registered configuration identity")
    registered = commands.add_parser("registered", help="run the future exact registered evaluation")
    registered.add_argument("--manifest", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "configuration":
        print(json.dumps(configuration_payload(), sort_keys=True, separators=(",", ":")))
        return 0
    spec = registered_spec()
    result = evaluate_registered(spec)
    published = write_complete_result(args.manifest, result)
    print(str(published))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["build_parser", "configuration_payload", "main"]
