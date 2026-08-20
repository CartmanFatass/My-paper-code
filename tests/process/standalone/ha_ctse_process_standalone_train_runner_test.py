from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from ha_ctse_process import event_process_runner
from ha_ctse_process import standalone_train_runner
from ha_ctse_process import standalone_variable_roster_runner
from ha_ctse_process import train


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


def test_train_loop_profiles_existing_direct_phase_boundaries_only() -> None:
    runner_source = inspect.getsource(standalone_train_runner)
    loop = _function_node(runner_source, "train_loop")
    calls = [
        node for node in ast.walk(loop) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "profiler"
    ]
    names = [node.func.attr for node in calls]
    assert names.count("start") == 7
    assert names.count("stop") == 7
    assert names.count("finish_update") == 1
    assert runner_source.index("profiler.start(\"inference\"") < runner_source.index("collector.step(pre_actions)")
    assert runner_source.index("collector.step(pre_actions)") < runner_source.index("profiler.start(\"transition_ledger_pack\"")
    assert runner_source.index("profiler.stop(torch_phase=True)") < runner_source.index("profiler.start(\"metrics\"")
    assert runner_source.index("profiler.start(\"metrics\"") < runner_source.index("env_reward_mean")
    assert runner_source.count("collector.step(pre_actions)") == 1
    assert runner_source.count("agent.process_update(") == 1
    assert runner_source.count("agent.update_low(") == 1


def test_periodic_checkpoint_follows_due_evaluation_frontier() -> None:
    runner_source = inspect.getsource(standalone_train_runner.train_loop)

    eval_guard = "if int(args.eval_interval) > 0"
    save_guard = "if int(args.save_interval) > 0"
    assert runner_source.count(eval_guard) == 1
    assert runner_source.count(save_guard) == 1
    assert runner_source.index(eval_guard) < runner_source.index(save_guard)
    assert runner_source.index("last_eval_step = int(total_steps)") < runner_source.index(
        save_guard
    )


def test_train_loop_constructs_profiler_only_in_the_positive_interval_branch() -> None:
    source = inspect.getsource(standalone_train_runner)
    assert source.count("InfrastructureProfiler(") == 1
    interval = 'profile_interval = int(getattr(args, "infrastructure_profile_interval", 0))'
    assert interval in source
    assert source.index("if profile_interval > 0:") < source.index("InfrastructureProfiler(")


def test_retired_p3_runner_surface_is_absent() -> None:
    source = inspect.getsource(standalone_train_runner)
    retired = ("skill_" + "effect", "skill_" + "force", "skill_" + "forcing")

    assert all(token not in source for token in retired)


def test_standard_profile_cuda_sync_binds_the_configured_agent_device(monkeypatch) -> None:
    received = []
    monkeypatch.setattr(
        standalone_train_runner.torch.cuda,
        "synchronize",
        lambda device: received.append(device),
    )

    callback = standalone_train_runner._cuda_synchronize_callback(
        SimpleNamespace(device="cuda:1")
    )
    callback()

    assert received == [standalone_train_runner.torch.device("cuda:1")]


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
    args = SimpleNamespace()
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
