from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.capability_bound_semantic_currentness.artifact import _atomic_create_only_bytes, validate_complete_result, write_complete_result
from experiments.candidates.capability_bound_semantic_currentness.factorial import construct_world
from experiments.candidates.capability_bound_semantic_currentness.policies import action_ledger, action_vector, controller_view
from experiments.candidates.capability_bound_semantic_currentness.registered import registered_spec
from experiments.candidates.capability_bound_semantic_currentness.schema import (
    AccessState,
    Action,
    BindingState,
    CompleteResult,
    NuisanceCoordinate,
    OwnerState,
    PayloadState,
    PolicyArm,
    ResultRow,
    SemanticState,
    to_jsonable,
)


def _synthetic_complete() -> CompleteResult:
    world = construct_world(OwnerState.LIVE, SemanticState.PERSIST, BindingState.AUTHENTIC, AccessState.OPEN, PayloadState.NATIVE_NEUTRAL, NuisanceCoordinate(0, 0, 1, 1, 0, 0, 0))
    rows = []
    for policy in PolicyArm:
        rows.append(ResultRow(
            world.world_id,
            world.nuisance_id,
            policy,
            controller_view(world, policy),
            action_vector(world, policy),
            Action.SAFE_FALLBACK,
            action_ledger(world, policy, Action.SAFE_FALLBACK),
        ))
    rows.sort(key=lambda row: (row.world_id, row.policy.value))
    spec = registered_spec()
    return CompleteResult(
        "cbsc_exact_factorial_result_v1", True,
        {"direction_id": "capability_bound_semantic_currentness", "protocol_id": "CBSC-EXACT-FACTORIAL-V1", "nuisance_version": "CBSC-F0-V1"},
        {
            "registered_spec": to_jsonable(spec),
            "row_order": {
                "law": "LEXICOGRAPHIC_WORLD_ID_THEN_POLICY", "row_count": 6,
                "first_key": [rows[0].world_id, rows[0].policy.value],
                "last_key": [rows[-1].world_id, rows[-1].policy.value],
            },
            "inventory": {
                "policies": [arm.value for arm in spec.policies],
                "actions": [action.value for action in spec.actions],
                "terminal_clocks": [0, 1],
                "ledger_components": [
                    "common_validation_read", "padded_terminal_service_actuation", "refresh_scan",
                    "refresh_delay", "new_content_ingestion", "gross_correct_service",
                    "gross_wrong_service", "gross_unauthorized_attempt", "gross_safe_fallback",
                ],
            },
        },
        {"world_count_per_arm": 1, "policy_count": 6, "row_count": 6},
        {"nuisance_version": "CBSC-F0-V1"},
        tuple(rows), {"synthetic": Fraction(0)}, {"synthetic_complete": True},
        "Synthetic structure-only fixture; no scientific interpretation.", "INVALID", "synthetic_fixture",
    )


def test_partial_rectangle_rejected_and_atomic_create_only_mechanics_isolated(tmp_path):
    result = _synthetic_complete()
    with pytest.raises(ValueError, match="registered exact support"):
        validate_complete_result(result)
    target = tmp_path / "result" / "manifest.json"
    assert _atomic_create_only_bytes(target, b"structural-test-bytes\n") == target
    assert target.read_bytes() == b"structural-test-bytes\n"
    with pytest.raises(FileExistsError, match="create-only"):
        _atomic_create_only_bytes(target, b"replacement")
    partial = tmp_path / "partial.json"
    with pytest.raises(ValueError, match="complete barrier"):
        write_complete_result(partial, replace(result, complete=False))
    assert not partial.exists()


def test_configuration_cli_has_zero_result_fields_and_no_forbidden_flags():
    command = [sys.executable, "-m", "experiments.candidates.capability_bound_semantic_currentness.run", "configuration"]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(completed.stdout)
    assert payload["result_fields"] == []
    assert payload["mode"] == "CONFIGURATION_ONLY"
    assert payload["result_activity"] == "ZERO"
    assert not any("authoriz" in key.lower() for key in payload)
    forbidden = {"seed", "arm", "payoff", "threshold", "smoke", "full", "retry", "resume", "checkpoint", "branch", "contrast", "return"}
    assert forbidden.isdisjoint(payload)


def test_result_schema_rejects_partial_tamper():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(Path("experiments/candidates/capability_bound_semantic_currentness/schemas/cbsc_exact_factorial_result_v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    payload = json.loads(__import__("experiments.candidates.capability_bound_semantic_currentness.rng", fromlist=["canonical_dumps"]).canonical_dumps(_synthetic_complete()))
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)
    payload["complete"] = False
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)
