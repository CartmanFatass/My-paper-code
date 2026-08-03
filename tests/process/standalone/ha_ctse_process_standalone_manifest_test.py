"""Focused ownership and behavior checks for standalone manifest extraction."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from ha_ctse_process import standalone_manifest
from ha_ctse_process import standalone_eval_runner
from ha_ctse_process import standalone_train_runner
from ha_ctse_process import train


MANIFEST_CONSTANTS = {
    "ALGORITHM_MANIFEST_FIELDS",
    "TRAINING_MANIFEST_FIELDS",
    "MODEL_MANIFEST_FIELDS",
    "PHYSICAL_MANIFEST_FIELDS",
}
MANIFEST_FUNCTIONS = {"jsonable", "pick_attrs", "export_run_manifest"}


def _top_level_names(path: Path, node_type: type[ast.AST]) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, node_type) and hasattr(node, "name")
    }


def _assigned_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }


def test_standalone_manifest_is_true_owner_and_train_uses_module_qualified_calls():
    manifest_path = Path(standalone_manifest.__file__)
    eval_runner_path = Path(standalone_eval_runner.__file__)
    train_runner_path = Path(standalone_train_runner.__file__)
    train_path = Path(train.__file__)
    manifest_tree = ast.parse(manifest_path.read_text(encoding="utf-8"))
    eval_runner_tree = ast.parse(eval_runner_path.read_text(encoding="utf-8"))
    train_runner_tree = ast.parse(train_runner_path.read_text(encoding="utf-8"))
    train_tree = ast.parse(train_path.read_text(encoding="utf-8"))

    assert MANIFEST_CONSTANTS <= _assigned_names(manifest_path)
    assert MANIFEST_CONSTANTS.isdisjoint(_assigned_names(train_path))
    assert MANIFEST_FUNCTIONS <= _top_level_names(manifest_path, ast.FunctionDef)
    assert MANIFEST_FUNCTIONS.isdisjoint(_top_level_names(train_path, ast.FunctionDef))
    assert _top_level_names(train_path, ast.FunctionDef) == {"run_env_dry_check", "main"}
    assert {"empty_r30_no_high_metrics", "train_loop"} <= _top_level_names(
        train_runner_path, ast.FunctionDef
    )
    assert {"eval_loop"} == _top_level_names(eval_runner_path, ast.FunctionDef)

    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "ha_ctse_process"
        and any(alias.name == "standalone_manifest" for alias in node.names)
        for tree in (eval_runner_tree, train_runner_tree)
        for node in tree.body
    )
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module == "ha_ctse_process.standalone_manifest"
        for tree in (train_tree, eval_runner_tree, train_runner_tree)
        for node in tree.body
    )
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module == "ha_ctse_process"
        and any(alias.name == "standalone_manifest" for alias in node.names)
        for node in train_tree.body
    )
    owner_trees = (eval_runner_tree, train_runner_tree)
    qualified_calls = [
        node
        for tree in owner_trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "standalone_manifest"
        and node.func.attr == "export_run_manifest"
    ]
    assert len(qualified_calls) == 3
    assert not any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "export_run_manifest")
            or (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "standalone_manifest"
                and node.func.attr == "export_run_manifest"
            )
        )
        for node in ast.walk(train_tree)
    )

    imported_modules = {
        alias.name
        for node in ast.walk(manifest_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        str(node.module)
        for node in ast.walk(manifest_tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "ha_ctse_process.train" not in imported_modules
    assert not hasattr(train, "export_run_manifest")


def test_jsonable_and_pick_attrs_preserve_conversion_and_field_order(tmp_path):
    opaque = object()
    value = {
        7: np.asarray([np.int64(2), np.int64(3)]),
        "float": np.float32(1.25),
        "flag": np.bool_(True),
        "tuple": (Path(tmp_path / "item"), opaque),
    }

    converted = standalone_manifest.jsonable(value)

    assert converted == {
        "7": [2, 3],
        "float": 1.25,
        "flag": True,
        "tuple": [str(tmp_path / "item"), str(opaque)],
    }
    assert json.loads(json.dumps(converted)) == converted

    source = SimpleNamespace(second=np.int64(2), first=Path("artifact"), ignored=9)
    picked = standalone_manifest.pick_attrs(
        source, ("first", "missing", "second")
    )
    assert list(picked) == ["first", "second"]
    assert picked == {"first": "artifact", "second": 2}


def test_retired_p3_fields_are_absent_from_manifest_schema():
    retired = ("skill_" + "effect", "skill_" + "force", "skill_" + "forcing")
    fields = (
        standalone_manifest.ALGORITHM_MANIFEST_FIELDS
        + standalone_manifest.TRAINING_MANIFEST_FIELDS
        + standalone_manifest.MODEL_MANIFEST_FIELDS
        + standalone_manifest.PHYSICAL_MANIFEST_FIELDS
    )

    assert all(not any(token in field for token in retired) for field in fields)


class _FakeEnv:
    obs_dim = np.int64(7)
    state_dim = np.int64(11)
    action_dim = np.int64(3)
    n_uavs = np.int64(2)
    n_agents = np.int64(2)
    n_users = np.int64(5)

    def get_current_state(self):
        return {
            "area_size": np.asarray([100.0, 80.0], dtype=np.float32),
            "max_steps": np.int64(25),
            "battery_enabled": np.bool_(True),
            "energy_stage": np.int64(3),
        }


class _FakeAgent:
    obs_dim = 7
    action_dim = 3
    n_agents = 2
    n_skills = 4
    duration_candidates = (2, np.int64(5))
    action_space_type = "discrete"
    device = "cpu"
    use_recurrent_low_level = True
    low_level_architecture = "gru"
    low_rnn_hidden_size = 16

    def parameter_counts(self):
        return {"actor": np.int64(13), "heads": np.asarray([2, 3])}


def test_export_run_manifest_writes_exact_schema_runtime_and_path(tmp_path):
    log_dir = tmp_path / "nested" / "run"
    args = SimpleNamespace(
        log_dir=str(log_dir),
        seed=np.int64(17),
        output_hint=Path("relative/output"),
    )
    config = SimpleNamespace(
        algorithm="ha_ctse_process",
        gamma=np.float32(0.99),
        hidden_size=np.int64(64),
        scenario="scenario7",
        unregistered_value=object(),
    )
    env = _FakeEnv()
    agent = _FakeAgent()

    standalone_manifest.export_run_manifest(
        args,
        config,
        env=env,
        agent=agent,
        total_steps=12,
        update_idx=2,
        mode="train",
    )
    manifest_path = log_dir / "metadata" / "run_manifest.json"
    assert manifest_path.is_file()
    assert not (log_dir / "run_manifest.json").exists()

    standalone_manifest.export_run_manifest(
        args,
        config,
        env=env,
        agent=agent,
        total_steps=18,
        update_idx=3,
        mode="eval",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert list(manifest) == [
        "mode",
        "total_steps",
        "update_idx",
        "args",
        "algorithm_config",
        "training_config",
        "model_config",
        "physical_env_config",
        "env_runtime_spec",
        "agent_runtime_spec",
    ]
    assert manifest["mode"] == "eval"
    assert manifest["total_steps"] == 18
    assert manifest["update_idx"] == 3
    assert manifest["args"]["seed"] == 17
    assert manifest["args"]["output_hint"] == "relative\\output"
    assert manifest["algorithm_config"] == {"algorithm": "ha_ctse_process"}
    assert manifest["training_config"] == {"gamma": np.float32(0.99)}
    assert manifest["model_config"] == {"hidden_size": 64}
    assert manifest["physical_env_config"] == {"scenario": "scenario7"}
    assert manifest["env_runtime_spec"] == {
        "obs_dim": 7,
        "state_dim": 11,
        "action_dim": 3,
        "n_uavs": 2,
        "n_agents": 2,
        "n_users": 5,
        "area_size": [100.0, 80.0],
        "max_steps": 25,
        "battery_enabled": True,
        "energy_stage": 3,
    }
    assert manifest["agent_runtime_spec"]["duration_candidates"] == [2, 5]
    assert manifest["agent_runtime_spec"]["high_controller"] == "legacy_duration"
    assert manifest["agent_runtime_spec"]["k0"] == 10
    assert manifest["agent_runtime_spec"]["fixed_skill_action_table"] is None
    assert manifest["agent_runtime_spec"]["parameter_counts"] == {
        "actor": 13,
        "heads": [2, 3],
    }
    json.dumps(manifest)
