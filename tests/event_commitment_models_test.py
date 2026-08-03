from __future__ import annotations

import ast
import inspect

import torch

from ha_ctse_process import event_commitment_models
from ha_ctse_process.event_commitment_types import CommitmentArm
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner


def test_initialize_arms_has_one_true_owner_and_direct_callers() -> None:
    initialize_arms = event_commitment_models.initialize_arms
    assert initialize_arms.__module__ == "ha_ctse_process.event_commitment_models"
    assert benchmark_runner.initialize_arms is initialize_arms
    assert (
        benchmark_runner.parameter_and_optimizer_counts
        is event_commitment_models.parameter_and_optimizer_counts
    )


def test_model_owner_import_dag_does_not_reach_monolith_or_higher_layers() -> None:
    tree = ast.parse(inspect.getsource(event_commitment_models))
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "ha_ctse_process.event_held_commitment_link" not in imported
    assert "scripts.run_noncalendar_commitment_benchmark_g0" not in imported


def test_parameter_and_optimizer_counts_preserve_exact_exposure() -> None:
    arm = CommitmentArm("DUM")
    base_optimizer = torch.optim.Adam(arm.base_optimizer_parameters())
    event_optimizer = torch.optim.Adam(arm.event_parameters())

    assert event_commitment_models.parameter_and_optimizer_counts(
        arm, base_optimizer, event_optimizer
    ) == {
        "base_model": 14_980,
        "added_model": 1_608,
        "base_optimizer": 15_004,
        "event_optimizer": 1_584,
    }
    assert event_commitment_models.parameter_and_optimizer_counts(
        arm, base_optimizer, None
    )["event_optimizer"] == 0
