from __future__ import annotations

import ast
import inspect
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from ha_ctse_process import event_process_runner
from ha_ctse_process import standalone_train_runner
from ha_ctse_process import standalone_variable_roster_runner
from ha_ctse_process import train


BASE_COMMIT = "d709767b26dec8cf8c987b74e7ea09e807dbb3ba"


def _function_node(source: str, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_train_loop_has_one_true_owner_and_no_reverse_import_edge() -> None:
    runner_source = inspect.getsource(standalone_train_runner)
    train_source = inspect.getsource(train)
    runner_tree = ast.parse(runner_source)
    train_tree = ast.parse(train_source)
    runner_definitions = {
        node.name for node in runner_tree.body if isinstance(node, ast.FunctionDef)
    }
    train_definitions = {
        node.name for node in train_tree.body if isinstance(node, ast.FunctionDef)
    }
    imported_modules = {
        node.module
        for node in ast.walk(runner_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(runner_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert {"empty_r30_no_high_metrics", "train_loop"} <= runner_definitions
    assert not {"empty_r30_no_high_metrics", "train_loop"} & train_definitions
    assert "ha_ctse_process.train" not in imported_modules
    assert not hasattr(train, "train_loop")


def test_moved_definitions_match_the_ticket_base_ast() -> None:
    repository = Path(__file__).resolve().parents[1]
    base_source = subprocess.run(
        [
            "git",
            "-c",
            "core.longpaths=true",
            "show",
            f"{BASE_COMMIT}:ha_ctse_process/train.py",
        ],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    runner_source = inspect.getsource(standalone_train_runner)

    for name in ("empty_r30_no_high_metrics", "train_loop"):
        expected = _function_node(base_source, name)
        actual = _function_node(runner_source, name)
        assert ast.dump(actual, include_attributes=False) == ast.dump(
            expected, include_attributes=False
        )


def test_main_uses_only_module_qualified_train_dispatch() -> None:
    main_node = _function_node(inspect.getsource(train), "main")
    qualified_calls = [
        node
        for node in ast.walk(main_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "standalone_train_runner"
        and node.func.attr == "train_loop"
    ]
    bare_calls = [
        node
        for node in ast.walk(main_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "train_loop"
    ]

    assert len(qualified_calls) == 2
    assert not bare_calls
    assert train.standalone_train_runner is standalone_train_runner


def test_early_preflight_and_dispatch_do_not_cross_collector_boundary(
    monkeypatch,
) -> None:
    calls: list[tuple[object, object, object]] = []
    sentinel = object()

    def forbidden_collector(*_args, **_kwargs):
        raise AssertionError("early train dispatch crossed the collector boundary")

    def branch(config, args, writer):
        calls.append((config, args, writer))
        return sentinel

    monkeypatch.setattr(standalone_train_runner, "create_collector", forbidden_collector)
    monkeypatch.setattr(
        standalone_train_runner, "_run_iteration5_process_semantics_branch", branch
    )
    args = SimpleNamespace(
        r28_g1_arm="off",
        r29_action_info_mode="off",
        r31_effect_mode="off",
    )
    bad_config = SimpleNamespace(
        high_controller="variable_roster_event",
        event_architecture_mode="f1",
        iteration5_process_semantics_arm="c1_semantic_on",
    )
    with pytest.raises(ValueError, match="exact F0"):
        standalone_train_runner.train_loop(bad_config, args, None)
    assert not calls

    config = SimpleNamespace(
        high_controller="variable_roster_event",
        event_architecture_mode="f0",
        iteration5_process_semantics_arm="c1_semantic_on",
    )
    assert standalone_train_runner.train_loop(config, args, None) is sentinel
    assert calls == [(config, args, None)]


def test_early_branch_callables_preserve_object_identity() -> None:
    assert (
        standalone_train_runner._run_iteration5_process_semantics_branch
        is event_process_runner._run_iteration5_process_semantics_branch
    )
    assert (
        standalone_train_runner.standalone_variable_roster_runner
        is standalone_variable_roster_runner
    )
    assert (
        standalone_train_runner.standalone_variable_roster_runner.run_variable_roster_event_branch
        is standalone_variable_roster_runner.run_variable_roster_event_branch
    )
