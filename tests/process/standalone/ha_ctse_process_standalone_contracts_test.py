from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from ha_ctse_process import standalone_contracts
from ha_ctse_process.standalone_contracts import (
    enforce_iteration5_process_semantics_contract,
    enforce_r30_contract,
    enforce_r30_pair_gate,
    enforce_variable_roster_event_contract,
    is_iteration5_process_semantics,
    is_variable_roster_event,
)


CONTRACT_SYMBOLS = {
    "is_variable_roster_event",
    "is_iteration5_process_semantics",
    "enforce_iteration5_process_semantics_contract",
    "enforce_variable_roster_event_contract",
    "dispatch_variable_roster_event_boundary",
    "enforce_r30_contract",
    "enforce_r30_pair_gate",
}

RETIRED_CONTRACT_SYMBOLS = {
    "enforce_r28_g1_contract",
    "enforce_r29_action_info_contract",
    "enforce_r31_contract",
    "enforce_aem_contract",
    "enforce_r37_identity_contract",
}


def _top_level_function_names(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _args(**overrides):
    return SimpleNamespace(**overrides)


def test_contract_symbols_have_one_true_owner() -> None:
    project_root = Path(__file__).resolve().parents[3]
    owner = _top_level_function_names(
        project_root / "ha_ctse_process" / "standalone_contracts.py"
    )
    train = _top_level_function_names(project_root / "ha_ctse_process" / "train.py")

    assert CONTRACT_SYMBOLS <= owner
    assert not CONTRACT_SYMBOLS & train


def test_contract_predicates_and_fail_closed_errors() -> None:
    assert is_variable_roster_event(
        SimpleNamespace(high_controller="variable_roster_event")
    )
    assert not is_variable_roster_event(SimpleNamespace(high_controller="legacy_duration"))
    assert is_iteration5_process_semantics(
        SimpleNamespace(iteration5_process_semantics_arm="c1_semantic_on")
    )

    with pytest.raises(ValueError, match="exact F0"):
        enforce_iteration5_process_semantics_contract(
            SimpleNamespace(
                high_controller="variable_roster_event",
                iteration5_process_semantics_arm="c1_semantic_on",
                event_architecture_mode="f1",
            ),
            _args(),
        )
    with pytest.raises(ValueError, match="architecture schema version 1"):
        enforce_variable_roster_event_contract(
            SimpleNamespace(
                high_controller="variable_roster_event",
                event_architecture_mode="f0",
                event_architecture_schema_version=0,
                event_opportunity_schedule="uniform_active_gap_v1",
            ),
            _args(),
            None,
        )
    with pytest.raises(ValueError, match="unsupported high_controller"):
        enforce_r30_contract(SimpleNamespace(high_controller="invalid"), _args())
    with pytest.raises(ValueError, match="registered pre-R30 checkpoint"):
        enforce_r30_pair_gate(
            SimpleNamespace(high_controller="legacy_duration"),
            _args(r30_pair_gate=True),
            None,
        )


def test_retired_contract_surfaces_are_absent() -> None:
    source = inspect.getsource(standalone_contracts)
    retired = tuple(RETIRED_CONTRACT_SYMBOLS) + (
        "r28_g1_",
        "r29_action_info_",
        "r31_effect_",
        "aem_",
        "r37_identity_",
    )

    assert all(token not in source for token in retired)
