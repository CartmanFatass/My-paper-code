from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from ha_ctse_process.standalone_contracts import (
    enforce_aem_contract,
    enforce_iteration5_process_semantics_contract,
    enforce_r28_g1_contract,
    enforce_r29_action_info_contract,
    enforce_r30_contract,
    enforce_r30_pair_gate,
    enforce_r31_contract,
    enforce_r37_identity_contract,
    enforce_variable_roster_event_contract,
    is_iteration5_process_semantics,
    is_variable_roster_event,
)


CONTRACT_SYMBOLS = {
    "enforce_r28_g1_contract",
    "enforce_r29_action_info_contract",
    "is_variable_roster_event",
    "is_iteration5_process_semantics",
    "enforce_iteration5_process_semantics_contract",
    "enforce_variable_roster_event_contract",
    "dispatch_variable_roster_event_boundary",
    "enforce_r30_contract",
    "enforce_r31_contract",
    "enforce_aem_contract",
    "enforce_r37_identity_contract",
    "enforce_r30_pair_gate",
}


def _top_level_function_names(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _args(**overrides):
    values = {
        "r28_g1_arm": "off",
        "r29_action_info_mode": "off",
        "r31_effect_mode": "off",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_contract_symbols_have_one_true_owner() -> None:
    project_root = Path(__file__).resolve().parents[1]
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
    with pytest.raises(ValueError, match="unsupported R28-G1 arm"):
        enforce_r28_g1_contract(SimpleNamespace(), _args(r28_g1_arm="invalid"), None)
    with pytest.raises(ValueError, match="online reward is retired"):
        enforce_r29_action_info_contract(
            SimpleNamespace(skill_lifetime_candidates=(1, 2, 3, 4)),
            _args(r29_action_info_mode="real_reward"),
        )
    with pytest.raises(ValueError, match="unsupported high_controller"):
        enforce_r30_contract(SimpleNamespace(high_controller="invalid"), _args())
    with pytest.raises(ValueError, match="diagnostic-only"):
        enforce_r31_contract(
            SimpleNamespace(r31_effect_mode="real_reward"),
            _args(),
            None,
        )
    with pytest.raises(ValueError, match="restricted to the sparse Alice--Bob"):
        enforce_aem_contract(
            SimpleNamespace(aem_joint_novelty_enabled=True),
            _args(),
            None,
        )
    with pytest.raises(ValueError, match="masked or visible identity slots"):
        enforce_r37_identity_contract(
            SimpleNamespace(
                r37_identity_gate_enabled=True,
                alice_bob_actor_identity_mode="invalid",
            ),
            _args(),
            None,
        )
    with pytest.raises(ValueError, match="registered pre-R30 checkpoint"):
        enforce_r30_pair_gate(
            SimpleNamespace(high_controller="legacy_duration"),
            _args(r30_pair_gate=True),
            None,
        )
