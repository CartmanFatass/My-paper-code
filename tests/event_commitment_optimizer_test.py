from __future__ import annotations

import ast
from pathlib import Path

from ha_ctse_process import event_commitment_optimizer
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner


MOVED_FUNCTIONS = {
    "_pack_trajectory_once",
    "compute_gae",
    "optimizer_ownership_manifest",
    "_expected_parameter_counts",
    "_expected_optimizer_manifest",
    "_optimizer_pass_valid",
    "_gradient_summaries",
    "_optimizer_pass_record",
    "optimize_update",
}


def test_optimizer_has_unique_direct_owner_and_acyclic_dependencies() -> None:
    for name in MOVED_FUNCTIONS:
        owner = getattr(event_commitment_optimizer, name)
        assert owner.__module__ == "ha_ctse_process.event_commitment_optimizer"

    for name in (
        "optimize_update",
        "optimizer_ownership_manifest",
        "_expected_parameter_counts",
        "_expected_optimizer_manifest",
        "_optimizer_pass_valid",
        "EVENT_ENTROPY_COEFFICIENT",
    ):
        assert not hasattr(benchmark_runner, name)

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

    runner_tree = ast.parse(
        Path(benchmark_runner.__file__).read_text(encoding="utf-8")
    )
    runner_functions = {
        node.name for node in runner_tree.body if isinstance(node, ast.FunctionDef)
    }
    assert not runner_functions.intersection({
        "_expected_parameter_counts",
        "_expected_optimizer_manifest",
        "_optimizer_pass_valid",
    })
