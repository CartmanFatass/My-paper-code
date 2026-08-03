from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from ha_ctse_process.standalone_novelty import (
    EpisodicJointPositionNovelty,
    empty_aem_metrics,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
STANDALONE_TRAIN_RUNNER_PATH = (
    REPOSITORY_ROOT / "ha_ctse_process" / "standalone_train_runner.py"
)
NOVELTY_PATH = REPOSITORY_ROOT / "ha_ctse_process" / "standalone_novelty.py"


def _top_level_definitions(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in module.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_standalone_novelty_is_true_owner_and_runner_uses_module_qualified_import():
    train_runner_module = ast.parse(
        STANDALONE_TRAIN_RUNNER_PATH.read_text(encoding="utf-8")
    )

    assert {
        "empty_aem_metrics",
        "EpisodicJointPositionNovelty",
    }.issubset(_top_level_definitions(NOVELTY_PATH))
    assert {
        "empty_aem_metrics",
        "EpisodicJointPositionNovelty",
    }.isdisjoint(_top_level_definitions(STANDALONE_TRAIN_RUNNER_PATH))
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "ha_ctse_process"
        and any(alias.name == "standalone_novelty" for alias in node.names)
        for node in train_runner_module.body
    )
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.module == "ha_ctse_process.standalone_novelty"
        for node in train_runner_module.body
    )
    qualified_calls = {
        node.func.attr
        for node in ast.walk(train_runner_module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "standalone_novelty"
    }
    assert {
        "empty_aem_metrics",
        "EpisodicJointPositionNovelty",
    }.issubset(qualified_calls)


def test_first_and_repeated_bonus_use_preincrement_count():
    novelty = EpisodicJointPositionNovelty(
        num_envs=1,
        grid_size=3,
        episode_horizon=8,
    )
    position = np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

    assert novelty.observe(0, position) == pytest.approx(1.0 / 8.0)
    assert novelty.observe(0, position) == pytest.approx(1.0 / (8.0 * np.sqrt(2.0)))
    assert novelty.counts[0, novelty._cell_index(position)] == 2


def test_boundary_positions_are_clipped_and_use_row_major_grid_index():
    novelty = EpisodicJointPositionNovelty(
        num_envs=1,
        grid_size=3,
        episode_horizon=8,
    )

    assert novelty._cell_index(np.asarray([-0.2, 0.34, 0.67, 1.2])) == 17
    with pytest.raises(ValueError, match="exactly four finite"):
        novelty._cell_index(np.asarray([0.0, 0.0, 0.0, np.inf]))


def test_reset_env_only_clears_the_selected_environment():
    novelty = EpisodicJointPositionNovelty(
        num_envs=2,
        grid_size=2,
        episode_horizon=4,
    )
    position = np.asarray([0.25, 0.25, 0.25, 0.25], dtype=np.float32)
    for env_id in (0, 1):
        novelty.observe(env_id, position)
        novelty.observe(env_id, position)

    novelty.reset_env(0)

    assert novelty.observe(0, position) == pytest.approx(1.0 / 4.0)
    assert novelty.observe(1, position) == pytest.approx(1.0 / (4.0 * np.sqrt(3.0)))


def test_pop_update_metrics_returns_and_resets_the_registered_schema():
    novelty = EpisodicJointPositionNovelty(
        num_envs=2,
        grid_size=2,
        episode_horizon=4,
    )
    position = np.zeros(4, dtype=np.float32)
    first_bonus = novelty.observe(0, position)
    second_bonus = novelty.observe(0, position)
    novelty.reset_env(1)

    metrics = novelty.pop_update_metrics()

    assert set(metrics) == set(empty_aem_metrics(active=True))
    assert metrics["aem_active"] == 1.0
    assert metrics["aem_bonus_applied_steps"] == 2.0
    assert metrics["aem_bonus_sum"] == pytest.approx(first_bonus + second_bonus)
    assert metrics["aem_bonus_mean"] == pytest.approx((first_bonus + second_bonus) / 2.0)
    assert metrics["aem_bonus_min"] == pytest.approx(second_bonus)
    assert metrics["aem_bonus_max"] == pytest.approx(first_bonus)
    assert metrics["aem_count_resets"] == 1.0
    assert metrics["aem_preincrement_count_max"] == 1.0
    assert metrics["aem_formula_max_abs_error"] == 0.0
    assert metrics["aem_forbidden_field_reads"] == 0.0
    assert novelty.pop_update_metrics() == empty_aem_metrics(active=True)
