"""Retained final/probe panels and descriptive A01 diagnostics."""

import hashlib
from pathlib import Path

import numpy as np
import torch

from .learner import PREDICTION_STEPS, prediction_targets


PREDICTION_KEY = "predictor_predictions"


def array_digest(arrays, *, exclude=()):
    """Hash semantic array content without depending on npz container timestamps."""
    digest = hashlib.sha256()
    excluded = set(exclude)
    for name in sorted(arrays):
        if name in excluded:
            continue
        value = np.ascontiguousarray(arrays[name])
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(value.dtype.str.encode("ascii") + b"\0")
        digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def _moments(predictions, targets, eligible):
    selected_predictions = predictions[eligible].astype(np.float64)
    selected_targets = targets[eligible].astype(np.float64)
    errors = selected_predictions - selected_targets
    count = int(selected_predictions.size)
    if count == 0:
        raise ValueError("panel contains no eligible prediction labels")
    return {
        "count": count,
        "prediction_mean": float(selected_predictions.mean()),
        "prediction_second_moment": float(np.square(selected_predictions).mean()),
        "target_mean": float(selected_targets.mean()),
        "target_second_moment": float(np.square(selected_targets).mean()),
        "error_mean": float(errors.mean()),
        "mse": float(np.square(errors).mean()),
    }


def _post_event_windows(events, rewards):
    sums, counts = [], []
    for episode_events, episode_rewards in zip(events, rewards):
        selected = np.zeros(episode_rewards.shape[0], dtype=bool)
        for action_time in np.flatnonzero(episode_events):
            if 0 < action_time < episode_rewards.shape[0]:
                selected[action_time:min(action_time + 3, episode_rewards.shape[0])] = True
        sums.append(float(episode_rewards[selected].astype(np.float64).sum()))
        counts.append(int(selected.sum()))
    total_count = sum(counts)
    total_sum = float(sum(sums))
    return {
        "episode_reward_sums": sums,
        "episode_tick_counts": counts,
        "reward_sum": total_sum,
        "tick_count": total_count,
        "reward_mean_per_tick": total_sum / total_count if total_count else None,
        "rule": "union of first 3 action times after each noninitial event",
    }


@torch.no_grad()
def build_panel_arrays(episodes, actor, predictor):
    if not episodes:
        raise ValueError("cannot publish an empty panel")
    raw = {
        key: np.stack([episode[key] for episode in episodes])
        for key in episodes[0]
    }
    batch = {key: torch.as_tensor(value) for key, value in raw.items()}
    actor.eval()
    predictor.eval()
    _, hidden = actor(batch)
    predictions = predictor(hidden[:, :PREDICTION_STEPS]).squeeze(-1)
    targets, eligible = prediction_targets(batch)
    arrays = dict(raw)
    arrays[PREDICTION_KEY] = predictions.cpu().numpy()
    arrays["predictor_targets"] = targets.cpu().numpy()
    arrays["predictor_eligible"] = eligible.cpu().numpy()
    return arrays


def write_panel(path, episodes, actor, predictor):
    arrays = build_panel_arrays(episodes, actor, predictor)
    path = Path(path)
    np.savez_compressed(path, **arrays)
    artifact_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "path": str(path),
        "artifact_sha256": artifact_sha256,
        "input_sha256": array_digest(arrays, exclude=(PREDICTION_KEY,)),
        "panel_sha256": array_digest(arrays),
        "prediction": _moments(
            arrays[PREDICTION_KEY], arrays["predictor_targets"], arrays["predictor_eligible"]
        ),
        "post_event_window": _post_event_windows(arrays["event"], arrays["reward"]),
        "episodes": len(episodes),
        "transitions": int(arrays["reward"].shape[0] * arrays["reward"].shape[1]),
    }


def aggregate_update_moments(rows):
    count = sum(row["prediction_count"] for row in rows)
    if count == 0:
        raise ValueError("no predictor optimizer observations")
    total = lambda key: sum(row[key] for row in rows)
    return {
        "count": count,
        "optimizer_steps": len(rows),
        "prediction_mean": total("prediction_sum") / count,
        "prediction_second_moment": total("prediction_square_sum") / count,
        "target_mean": total("target_sum") / count,
        "target_second_moment": total("target_square_sum") / count,
        "error_mean": total("error_sum") / count,
        "mse": total("error_square_sum") / count,
    }

