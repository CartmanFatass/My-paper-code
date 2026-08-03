"""Standalone episodic joint-position novelty accounting."""

from __future__ import annotations

import numpy as np

from ha_ctse_process.plotting import AEM_METRIC_FIELDS


def empty_aem_metrics(active: bool = False) -> dict[str, float]:
    metrics = {field: 0.0 for field in AEM_METRIC_FIELDS}
    metrics["aem_active"] = float(bool(active))
    return metrics


class EpisodicJointPositionNovelty:
    """Per-vector-env direct-table counts for the registered R36 bonus."""

    def __init__(self, num_envs: int, grid_size: int, episode_horizon: int):
        self.num_envs = int(num_envs)
        self.grid_size = int(grid_size)
        self.episode_horizon = int(episode_horizon)
        self.table_size = int(self.grid_size**4)
        self.counts = np.zeros((self.num_envs, self.table_size), dtype=np.int32)
        self._metrics = empty_aem_metrics(active=True)
        self._bonus_min = float("inf")

    def _cell_index(self, normalized_positions: np.ndarray) -> int:
        positions = np.asarray(normalized_positions, dtype=np.float32).reshape(-1)
        if positions.shape != (4,) or not np.all(np.isfinite(positions)):
            raise ValueError("R36 AEM requires exactly four finite normalized position values")
        bins = np.floor(np.clip(positions, 0.0, 1.0) * self.grid_size).astype(
            np.int64
        )
        bins = np.minimum(bins, self.grid_size - 1)
        cell = int(bins[0])
        for value in bins[1:]:
            cell = cell * self.grid_size + int(value)
        if not 0 <= cell < self.table_size:
            raise RuntimeError("R36 AEM direct joint-position index is out of range")
        return cell

    def observe(self, env_id: int, normalized_positions: np.ndarray) -> float:
        env_id = int(env_id)
        cell = self._cell_index(normalized_positions)
        count_before = int(self.counts[env_id, cell])
        expected = 1.0 / (
            float(self.episode_horizon) * float(np.sqrt(count_before + 1.0))
        )
        bonus = float(expected)
        self.counts[env_id, cell] = count_before + 1

        self._metrics["aem_bonus_applied_steps"] += 1.0
        self._metrics["aem_bonus_sum"] += bonus
        self._metrics["aem_bonus_max"] = max(
            self._metrics["aem_bonus_max"], bonus
        )
        self._bonus_min = min(self._bonus_min, bonus)
        self._metrics["aem_preincrement_count_max"] = max(
            self._metrics["aem_preincrement_count_max"], float(count_before)
        )
        self._metrics["aem_formula_max_abs_error"] = max(
            self._metrics["aem_formula_max_abs_error"], abs(bonus - expected)
        )
        return bonus

    def reset_env(self, env_id: int) -> None:
        self.counts[int(env_id)].fill(0)
        self._metrics["aem_count_resets"] += 1.0

    def pop_update_metrics(self) -> dict[str, float]:
        metrics = dict(self._metrics)
        steps = metrics["aem_bonus_applied_steps"]
        metrics["aem_bonus_mean"] = (
            metrics["aem_bonus_sum"] / steps if steps > 0.0 else 0.0
        )
        metrics["aem_bonus_min"] = self._bonus_min if steps > 0.0 else 0.0
        self._metrics = empty_aem_metrics(active=True)
        self._bonus_min = float("inf")
        return metrics
