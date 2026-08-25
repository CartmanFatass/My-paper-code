from __future__ import annotations

import ast
from dataclasses import dataclass
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

from ha_ctse_process import standalone_event_support as event_support


EVENT_SUPPORT_NAMES = {
    "enforce_variable_roster_event_resume_boundary",
    "_write_event_json",
    "_replace_event_file",
    "_write_event_arm_status",
    "_write_event_csv_rows",
    "_event_live_checkpoint_paths",
    "_event_identity_normalizers",
    "_nested_state_maximum_difference",
    "_event_state_dict_finite",
    "_make_event_model_owner",
    "_make_event_runtime",
    "_paired_mean_ci",
    "_event_prefix_rows",
    "_summarize_event_prefix_rows",
    "_event_semantic_primitive_probabilities",
    "_project_event_semantic_natural_row",
    "_capture_event_semantic_source",
    "_project_event_semantic_forced_source",
    "_forced_event_snapshot_effects",
    "_summarize_forced_audit",
    "_evaluate_event_model",
}


def _top_level_definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_event_support_cluster_has_one_concrete_owner() -> None:
    root = Path(__file__).parents[3]
    support_path = root / "ha_ctse_process" / "standalone_event_support.py"
    train_path = root / "ha_ctse_process" / "train.py"

    assert EVENT_SUPPORT_NAMES <= _top_level_definitions(support_path)
    assert EVENT_SUPPORT_NAMES.isdisjoint(_top_level_definitions(train_path))
    support_tree = ast.parse(support_path.read_text(encoding="utf-8"))
    imported_modules = {
        alias.name
        for node in ast.walk(support_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        str(node.module)
        for node in ast.walk(support_tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "ha_ctse_process.train" not in imported_modules
    forced_snapshot_effects = next(
        node
        for node in support_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_forced_event_snapshot_effects"
    )
    forced_snapshot_imports = {
        str(node.module)
        for node in ast.walk(forced_snapshot_effects)
        if isinstance(node, ast.ImportFrom)
    }
    assert "ha_ctse_process.variable_roster_event" not in forced_snapshot_imports
    assert "ha_ctse_process.variable_roster_event_support" in forced_snapshot_imports


@dataclass(frozen=True)
class _NestedState:
    tensor: torch.Tensor
    values: tuple[np.ndarray, ...]


def test_projection_and_nested_finite_state_semantics_are_preserved() -> None:
    row = SimpleNamespace(
        action=np.asarray([2], dtype=np.int64),
        physical_time=7,
        lifecycle_key="agent:3",
        membership_epoch=4,
        observation=np.asarray([1.0, 2.0], dtype=np.float32),
        actor_hidden_before=np.asarray([0.25, -0.5], dtype=np.float32),
        skill=1,
        old_log_probability=-0.7,
    )
    projected = event_support._project_event_semantic_natural_row(
        row,
        arm="f1",
        episode_id=9,
        active_set_size=3,
        primitive_probabilities=[0.1, 0.2, 0.7],
    )
    assert projected["natural_action"] == 2
    assert projected["primitive_legal_support"] == [0, 1, 2]
    assert projected["primitive_probabilities"] == [0.1, 0.2, 0.7]
    assert projected["task_master_seed"] == 97_057

    left = {"state": _NestedState(torch.tensor([1.0]), (np.asarray([2.0]),))}
    right = {"state": _NestedState(torch.tensor([1.0]), (np.asarray([2.0]),))}
    changed = {"state": _NestedState(torch.tensor([1.0]), (np.asarray([3.0]),))}
    assert event_support._nested_state_maximum_difference(left, right) == 0.0
    assert event_support._nested_state_maximum_difference(left, changed) == 1.0

    modules = [torch.nn.Linear(1, 1, bias=False) for _ in range(4)]
    core = SimpleNamespace(
        commitment_model=modules[0],
        event_critic=modules[1],
        low_actor=modules[2],
        low_critic=modules[3],
    )
    assert event_support._event_state_dict_finite(core)
    with torch.no_grad():
        modules[2].weight.fill_(float("nan"))
    assert not event_support._event_state_dict_finite(core)


def test_event_json_write_replaces_atomically_and_cleans_temporary(tmp_path) -> None:
    path = tmp_path / "nested" / "event.json"
    event_support._write_event_json(
        path,
        {"array": np.asarray([1, 2]), "flag": np.bool_(True)},
    )

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "array": [1, 2],
        "flag": True,
    }
    assert not path.with_suffix(".json.tmp").exists()


def test_event_replace_keeps_bounded_windows_fallback(monkeypatch, tmp_path) -> None:
    destination = tmp_path / "event.json"
    destination.write_text("old", encoding="utf-8")
    temporary = tmp_path / "event.json.tmp"
    temporary.write_text("new", encoding="utf-8")
    attempts = 0

    def denied(_self: Path, _target: Path) -> None:
        nonlocal attempts
        attempts += 1
        raise PermissionError("busy")

    monkeypatch.setattr(Path, "replace", denied)
    monkeypatch.setattr(event_support.time, "sleep", lambda _seconds: None)
    event_support._replace_event_file(temporary, destination)

    assert attempts == 10
    assert destination.read_text(encoding="utf-8") == "new"
    assert not temporary.exists()
