from __future__ import annotations

import ast
import inspect

from ha_ctse_process import event_commitment_models, event_held_commitment_link
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner


def test_initialize_arms_has_one_true_owner_and_direct_callers() -> None:
    initialize_arms = event_commitment_models.initialize_arms
    assert initialize_arms.__module__ == "ha_ctse_process.event_commitment_models"
    assert benchmark_runner.initialize_arms is initialize_arms
    assert not hasattr(event_held_commitment_link, "initialize_arms")


def test_model_owner_import_dag_does_not_reach_monolith_or_higher_layers() -> None:
    tree = ast.parse(inspect.getsource(event_commitment_models))
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "ha_ctse_process.event_held_commitment_link" not in imported
    assert "scripts.run_noncalendar_commitment_benchmark_g0" not in imported
