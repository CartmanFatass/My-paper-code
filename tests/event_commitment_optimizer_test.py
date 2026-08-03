from __future__ import annotations

import ast
from pathlib import Path

from ha_ctse_process import event_commitment_optimizer
from ha_ctse_process import event_held_commitment_link
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner


MOVED_FUNCTIONS = {
    "_pack_trajectory_once",
    "compute_gae",
    "optimizer_ownership_manifest",
    "_gradient_summaries",
    "_optimizer_pass_record",
    "optimize_update",
}


def test_optimizer_has_unique_direct_owner_and_acyclic_dependencies() -> None:
    for name in MOVED_FUNCTIONS:
        owner = getattr(event_commitment_optimizer, name)
        assert owner.__module__ == "ha_ctse_process.event_commitment_optimizer"
        assert getattr(event_held_commitment_link, name) is owner

    assert benchmark_runner.optimize_update is event_commitment_optimizer.optimize_update
    assert (
        benchmark_runner.optimizer_ownership_manifest
        is event_commitment_optimizer.optimizer_ownership_manifest
    )
    assert (
        benchmark_runner.EVENT_ENTROPY_COEFFICIENT
        == event_commitment_optimizer.EVENT_ENTROPY_COEFFICIENT
    )

    parent_tree = ast.parse(
        Path(event_held_commitment_link.__file__).read_text(encoding="utf-8")
    )
    parent_definitions = {
        node.name for node in parent_tree.body if isinstance(node, ast.FunctionDef)
    }
    assert MOVED_FUNCTIONS.isdisjoint(parent_definitions)
    parent_assignments = {
        target.id
        for node in parent_tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert "EVENT_ENTROPY_COEFFICIENT" not in parent_assignments

    optimizer_tree = ast.parse(
        Path(event_commitment_optimizer.__file__).read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in optimizer_tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "ha_ctse_process.event_held_commitment_link" not in imported_modules
    assert "ha_ctse_process.event_commitment_checkpoint" not in imported_modules
    assert "ha_ctse_process.event_commitment_audit" not in imported_modules
    assert all(not module.startswith("scripts") for module in imported_modules)
