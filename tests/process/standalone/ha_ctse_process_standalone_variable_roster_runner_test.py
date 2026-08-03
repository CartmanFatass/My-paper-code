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
