from __future__ import annotations

import ast
import inspect
from pathlib import Path
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest

from ha_ctse_process import standalone_eval_runner
from ha_ctse_process import train


BASE_COMMIT = "83affae674caa08f4774fb324e02b7f32ab4008b"


def _function_node(source: str, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_eval_loop_has_one_true_owner_and_no_reverse_import_edge() -> None:
    runner_tree = ast.parse(inspect.getsource(standalone_eval_runner))
    train_tree = ast.parse(inspect.getsource(train))
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

    assert runner_definitions == {"eval_loop"}
    assert "eval_loop" not in train_definitions
    assert "ha_ctse_process.train" not in imported_modules
    assert not hasattr(train, "eval_loop")


def test_moved_eval_loop_matches_the_ticket_base_ast() -> None:
    repository = Path(__file__).resolve().parents[3]
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

    expected = _function_node(base_source, "eval_loop")
    actual = _function_node(inspect.getsource(standalone_eval_runner), "eval_loop")
    assert ast.dump(actual, include_attributes=False) == ast.dump(
        expected, include_attributes=False
    )


def test_main_uses_only_module_qualified_eval_dispatch() -> None:
    main_node = _function_node(inspect.getsource(train), "main")
    qualified_calls = [
        node
        for node in ast.walk(main_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "standalone_eval_runner"
        and node.func.attr == "eval_loop"
    ]
    bare_calls = [
        node
        for node in ast.walk(main_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "eval_loop"
    ]

    assert len(qualified_calls) == 1
    assert not bare_calls
    assert train.standalone_eval_runner is standalone_eval_runner


def test_eval_preflight_fails_closed_before_environment_creation(monkeypatch) -> None:
    def forbidden_env(*_args, **_kwargs):
        raise AssertionError("eval preflight crossed the environment boundary")

    monkeypatch.setattr(standalone_eval_runner, "create_env", forbidden_env)
    args = SimpleNamespace(resume_from="")
    config = SimpleNamespace(high_controller="legacy_duration")
    with pytest.raises(ValueError, match="--mode eval requires --resume_from"):
        standalone_eval_runner.eval_loop(config, args, None)

    def fail_event_boundary(_config):
        raise ValueError("event evaluation remains runner-owned")

    monkeypatch.setattr(
        standalone_eval_runner,
        "dispatch_variable_roster_event_boundary",
        fail_event_boundary,
    )
    args.resume_from = "checkpoint.pt"
    config.high_controller = "variable_roster_event"
    with pytest.raises(ValueError, match="event evaluation remains runner-owned"):
        standalone_eval_runner.eval_loop(config, args, None)


def test_eval_loop_preserves_lifecycle_checkpoint_manifest_and_metric_order(
    monkeypatch,
) -> None:
    calls: list[object] = []
    agent = object()
    metrics = {"episode_reward_mean": 3.5}
    writer = object()

    class FakeEnv:
        def reset(self, *, seed):
            calls.append(("reset", seed))
            return object(), {"state": np.asarray([[1.0, 2.0], [3.0, 4.0]])}

        def close(self):
            calls.append("close")

    env = FakeEnv()

    def fake_create_env(config, scenario, seed, *, rank, scale_mode):
        calls.append(("create_env", config, scenario, seed, rank, scale_mode))
        return env

    def fake_create_agent(config, args, actual_env, *, num_envs, state_dim):
        calls.append(
            ("create_agent", config, args, actual_env, num_envs, state_dim)
        )
        return agent

    def fake_load_checkpoint(path, actual_agent, *, load_optimizers):
        calls.append(("load_checkpoint", path, actual_agent, load_optimizers))
        return 41, 7

    def fake_export_manifest(args, config, **kwargs):
        calls.append(("manifest", args, config, kwargs))

    def fake_emit(args, message):
        assert not hasattr(args, "eval_checkpoint_name")
        calls.append(("emit", args, message))

    def fake_evaluate(actual_agent, config, args, *, episodes, total_steps):
        assert args.eval_checkpoint_name == "checkpoint.pt"
        calls.append(
            ("evaluate", actual_agent, config, args, episodes, total_steps)
        )
        return metrics

    def fake_log_eval_metrics(actual_writer, total_steps, actual_metrics):
        calls.append(("log", actual_writer, total_steps, actual_metrics))

    monkeypatch.setattr(standalone_eval_runner, "create_env", fake_create_env)
    monkeypatch.setattr(standalone_eval_runner, "create_agent", fake_create_agent)
    monkeypatch.setattr(
        standalone_eval_runner, "load_checkpoint", fake_load_checkpoint
    )
    monkeypatch.setattr(
        standalone_eval_runner.standalone_manifest,
        "export_run_manifest",
        fake_export_manifest,
    )
    monkeypatch.setattr(standalone_eval_runner, "emit", fake_emit)
    monkeypatch.setattr(standalone_eval_runner, "evaluate", fake_evaluate)
    monkeypatch.setattr(
        standalone_eval_runner, "log_eval_metrics", fake_log_eval_metrics
    )

    config = SimpleNamespace(
        high_controller="legacy_duration",
        scenario="scenario7",
        skill_lifetime_candidates=(2, 5),
    )
    args = SimpleNamespace(
        resume_from="artifacts/checkpoint.pt",
        seed=17,
        eval_episodes=3,
        eval_action_mode="deterministic",
    )

    assert standalone_eval_runner.eval_loop(config, args, writer) is None
    assert [call if isinstance(call, str) else call[0] for call in calls] == [
        "create_env",
        "reset",
        "create_agent",
        "close",
        "load_checkpoint",
        "manifest",
        "emit",
        "evaluate",
        "log",
    ]
    assert calls[0] == ("create_env", config, "scenario7", 17, 0, "eval")
    assert calls[2] == ("create_agent", config, args, env, 1, 4)
    assert calls[4] == (
        "load_checkpoint",
        "artifacts/checkpoint.pt",
        agent,
        False,
    )
    assert calls[5][3] == {
        "env": env,
        "agent": agent,
        "total_steps": 41,
        "update_idx": 7,
        "mode": "eval",
    }
    assert "total_steps=41 update_idx=7" in calls[6][2]
    assert calls[7] == ("evaluate", agent, config, args, 3, 41)
    assert calls[8] == ("log", writer, 41, metrics)
