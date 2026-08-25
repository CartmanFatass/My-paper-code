from __future__ import annotations

import ast
import inspect
from types import SimpleNamespace

import pytest

from ha_ctse_process import standalone_variable_roster_runner
from ha_ctse_process import standalone_train_runner
from ha_ctse_process import train


def test_variable_roster_runner_has_one_owner_and_direct_dispatch() -> None:
    runner_source = inspect.getsource(standalone_variable_roster_runner)
    train_runner_source = inspect.getsource(standalone_train_runner)
    train_source = inspect.getsource(train)

    assert "ha_ctse_process.train" not in runner_source
    assert "def run_variable_roster_event_branch(" in runner_source
    assert "def _run_variable_roster_event_branch(" not in train_source
    assert "def run_variable_roster_event_branch(" not in train_source
    assert (
        "standalone_variable_roster_runner.run_variable_roster_event_branch("
        in inspect.getsource(standalone_train_runner.train_loop)
    )
    assert "ha_ctse_process.train" not in train_runner_source


def test_variable_roster_runner_import_dag_has_no_train_edge() -> None:
    module = ast.parse(inspect.getsource(standalone_variable_roster_runner))
    imported = {
        node.module
        for node in ast.walk(module)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported.update(
        alias.name
        for node in ast.walk(module)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert "ha_ctse_process.train" not in imported
    assert "ha_ctse_process.standalone_cli" in imported
    assert "ha_ctse_process.standalone_event_support" in imported
    assert "ha_ctse_process.standalone_metrics" in imported


def test_variable_roster_runner_contract_preflight_stops_before_runtime(
    tmp_path, monkeypatch
) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("contract preflight crossed the collector boundary")

    monkeypatch.setattr(
        standalone_variable_roster_runner, "create_collector", forbidden
    )
    config = SimpleNamespace(
        high_controller="variable_roster_event",
        scenario="generic_short_dynamic_roster",
        event_architecture_schema_version=1,
    )
    args = SimpleNamespace(
        num_envs=15,
        rollout_length=80,
        total_timesteps=320_000,
        resume_from="",
        log_dir=str(tmp_path / "arm"),
    )

    with pytest.raises(ValueError, match="Stage C requires num_envs=16"):
        standalone_variable_roster_runner.run_variable_roster_event_branch(
            config, args, None
        )
    assert not (tmp_path / "arm").exists()


def test_variable_roster_runner_profiles_direct_phase_boundaries_only() -> None:
    source = inspect.getsource(standalone_variable_roster_runner)
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "profiler"
    ]
    names = [node.func.attr for node in calls]
    assert names.count("start") == 9
    assert names.count("stop") == 9
    assert names.count("finish_update") == 2
    assert source.index("profiler.start(\"inference\"") < source.index("collector.step_event_runtime")
    assert source.index("collector.step_event_runtime") < source.index("profiler.start(\"transition_ledger_pack\"")
    assert source.count("collector.step_event_runtime(") == 1
    assert source.count("pack_event_ppo_data(") == 1
    assert source.count("apply_event_ppo_update(") == 1


def test_variable_writer_metrics_phase_has_one_start_and_one_stop() -> None:
    source = inspect.getsource(standalone_variable_roster_runner)
    metrics_start = source.index('profiler.start("metrics")', source.index("checkpoint_path=str(latest_checkpoint_path)"))
    writer_block = source.index("if writer is not None:", metrics_start)
    emit_call = source.index("emit(\n", writer_block)
    metrics_stop = source.index("profiler.stop()", emit_call)
    finish = source.index("profiler.finish_update", metrics_stop)
    assert metrics_start < writer_block < emit_call < metrics_stop < finish
    assert "elif profiler is not None" not in source[metrics_start:finish]


def test_variable_runner_constructs_profiler_only_in_the_positive_interval_branch() -> None:
    source = inspect.getsource(standalone_variable_roster_runner)
    assert source.count("InfrastructureProfiler(") == 1
    interval = 'profile_interval = int(getattr(args, "infrastructure_profile_interval", 0))'
    assert interval in source
    assert source.index("if profile_interval > 0:") < source.index("InfrastructureProfiler(")
    assert source.index("InfrastructureProfiler(\n            args.log_dir,") >= 0
