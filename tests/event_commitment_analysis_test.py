from __future__ import annotations

import ast
import inspect
from types import SimpleNamespace

import pytest
import torch

from ha_ctse_process import event_commitment_analysis
from ha_ctse_process.event_commitment_collector import CREATE, KEEP, RENEW
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner


OWNED_NAMES = {
    "action_distribution_tv",
    "batched_natural_and_permuted_action_tv",
    "factor_counts",
}


def test_analysis_has_one_direct_owner_and_acyclic_dependencies() -> None:
    for name in OWNED_NAMES:
        owner = getattr(event_commitment_analysis, name)
        assert owner.__module__ == "ha_ctse_process.event_commitment_analysis"
    assert (
        benchmark_runner.batched_natural_and_permuted_action_tv
        is event_commitment_analysis.batched_natural_and_permuted_action_tv
    )
    assert benchmark_runner.factor_counts is event_commitment_analysis.factor_counts

    tree = ast.parse(inspect.getsource(event_commitment_analysis))
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "ha_ctse_process.event_held_commitment_link" not in imported
    assert "scripts.run_noncalendar_commitment_benchmark_g0" not in imported

    batched = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "batched_natural_and_permuted_action_tv"
    )
    loops = [
        node for node in ast.walk(batched) if isinstance(node, (ast.For, ast.While))
    ]
    assert len(loops) == 1
    assert isinstance(loops[0], ast.For)
    assert ast.unparse(loops[0].target) == "position"
    assert all(
        not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"item", "numpy", "cpu"}
        )
        for node in ast.walk(batched)
    )


def test_action_tv_shift_range_and_factor_counts_are_exact() -> None:
    natural = torch.tensor(
        [[0.7, -1.3, 2.1], [0.1, 0.2, 0.3]], dtype=torch.float32
    )
    shifts = torch.tensor([[4.25], [-9.0]], dtype=torch.float32)
    shifted = event_commitment_analysis.action_distribution_tv(
        natural, natural + shifts
    )
    assert torch.allclose(shifted, torch.zeros_like(shifted), atol=1e-6)

    tv = event_commitment_analysis.action_distribution_tv(
        torch.tensor([[80.0, -80.0, -80.0], [0.0, 0.0, 0.0]]),
        torch.tensor([[-80.0, 80.0, -80.0], [0.0, 0.0, 0.0]]),
    )
    assert tv[0].item() == pytest.approx(1.0)
    assert tv[1].item() == pytest.approx(0.0)
    assert bool((tv >= 0.0).all()) and bool((tv <= 1.0).all())

    trajectory = SimpleNamespace(
        event_kind=torch.tensor([CREATE, KEEP, KEEP, RENEW, RENEW, RENEW]),
        event_cat_mask=torch.tensor([False, True, True, False, False, False]),
        event_mark_mask=torch.tensor([False, False, False, True, True, True]),
    )
    assert event_commitment_analysis.factor_counts(trajectory) == {
        "create": 1,
        "keep": 2,
        "renew": 3,
        "categorical": 2,
        "mark": 3,
    }
