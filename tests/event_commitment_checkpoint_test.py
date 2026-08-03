from __future__ import annotations

import ast
from pathlib import Path

from ha_ctse_process import event_commitment_checkpoint
from ha_ctse_process import event_held_commitment_link
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner


OWNED_NAMES = (
    "runtime_rng_snapshot",
    "runtime_rng_equal",
    "save_checkpoint",
    "load_checkpoint",
    "compare_continuations",
)


def _module_tree(module: object) -> ast.Module:
    return ast.parse(Path(module.__file__).read_text(encoding="utf-8"))


def test_checkpoint_owner_import_identity_and_dag() -> None:
    owner_tree = _module_tree(event_commitment_checkpoint)
    parent_tree = _module_tree(event_held_commitment_link)
    owner_definitions = {
        node.name for node in owner_tree.body if isinstance(node, ast.FunctionDef)
    }
    parent_definitions = {
        node.name for node in parent_tree.body if isinstance(node, ast.FunctionDef)
    }
    assert set(OWNED_NAMES) <= owner_definitions
    assert set(OWNED_NAMES).isdisjoint(parent_definitions)

    owner_imports = {
        (node.module, alias.name)
        for node in owner_tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert (
        "ha_ctse_process.event_commitment_models",
        "initialize_arms",
    ) in owner_imports
    assert all(
        node.module != "ha_ctse_process.event_held_commitment_link"
        for node in owner_tree.body
        if isinstance(node, ast.ImportFrom)
    )

    for name in (
        "runtime_rng_snapshot",
        "save_checkpoint",
        "load_checkpoint",
        "compare_continuations",
    ):
        owner = getattr(event_commitment_checkpoint, name)
        assert owner.__module__ == "ha_ctse_process.event_commitment_checkpoint"
        assert getattr(benchmark_runner, name) is owner
