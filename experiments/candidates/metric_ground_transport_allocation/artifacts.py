"""Atomic typed-numeric artifact construction and completeness checks."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

import numpy as np

from .config import FINAL_SEEDS, REVISION


REQUIRED_SEED_FIELDS = {
    "arm", "binding", "phase", "training_seed", "tape_address", "N",
    "ordered_pair", "load_flag", "epoch", "agent_records", "task_records",
    "raw_supply", "raw_demand", "displayed_coordinates", "true_utility_table_key",
    "priority_ranks", "action_uniforms", "row_permutation", "task_permutation",
    "feature_vector", "edge_map_key", "raw_edge_scores", "expanded_Nx4_logits",
    "idle_logits", "step_masks", "categorical_probabilities", "sampled_step_actions",
    "coupling_X", "idle_iota", "unmet_mu", "feasibility_residuals", "reward",
    "normalized_endpoint", "oracle_panel_key", "parameter_count", "feature_ops",
    "map_ops", "edge_evaluations", "decoder_steps", "softmax_categories",
    "input_words", "output_words", "messages", "replay_row_permutation",
    "replay_task_permutation", "replay_sampled_actions", "replay_coupling_X",
    "replay_idle_iota", "replay_unmet_mu", "replay_feasibility_residuals",
    "replay_reward", "replay_normalized_endpoint", "checkpoint_parameters",
    "selected_hyperparameters", "alignment", "coupling_log_probability", "mean_entropy",
}


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def create_temp_root(final_root: Path) -> Path:
    if final_root.exists():
        raise FileExistsError(final_root)
    temp = final_root.with_name(final_root.name + ".tmp")
    if temp.exists():
        raise FileExistsError(temp)
    temp.mkdir(parents=True)
    return temp


def write_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    np.savez_compressed(path, **arrays)


def validate_seed_packet(path: Path, seed: int) -> None:
    with np.load(path, allow_pickle=False) as packet:
        missing = REQUIRED_SEED_FIELDS.difference(packet.files)
        if missing:
            raise RuntimeError(f"missing seed fields: {sorted(missing)}")
        rows = len(packet["N"])
        if rows != 49_152:
            raise RuntimeError(f"seed {seed} row count {rows}")
        if set(np.unique(packet["arm"])) != {0, 1} or set(np.unique(packet["binding"])) != {0, 1}:
            raise RuntimeError("incomplete arm/binding coverage")
        if set(np.unique(packet["N"])) != {4, 6, 8, 12}:
            raise RuntimeError("incomplete roster coverage")
        if np.any(packet["feasibility_residuals"]):
            raise RuntimeError("base feasibility failure")
        if np.any(packet["replay_feasibility_residuals"]):
            raise RuntimeError("replay feasibility failure")
        if not np.array_equal(packet["reward"], packet["replay_reward"]):
            raise RuntimeError("replay reward mismatch")
        if not np.array_equal(packet["normalized_endpoint"], packet["replay_normalized_endpoint"]):
            raise RuntimeError("replay endpoint mismatch")


def tree_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def validate_tree(root: Path) -> None:
    expected = {"manifest.json", "tables.npz", "summary.json", *(f"seed_{seed}.npz" for seed in FINAL_SEEDS)}
    actual = {path.name for path in root.iterdir() if path.is_file()}
    if actual != expected:
        raise RuntimeError(f"artifact file set mismatch: missing={expected-actual}, extra={actual-expected}")
    for seed in FINAL_SEEDS:
        validate_seed_packet(root / f"seed_{seed}.npz", seed)
    if tree_bytes(root) >= 8 * 1024**3:
        raise RuntimeError("artifact disk frontier exceeded")


def install(temp_root: Path, final_root: Path, *, prevalidated: bool = False) -> None:
    if not prevalidated:
        validate_tree(temp_root)
    os.replace(temp_root, final_root)
