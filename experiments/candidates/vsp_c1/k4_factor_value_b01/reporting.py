"""Small, model-free readers for the B01 primary observations."""
import json
from pathlib import Path


def curve_metrics(curve):
    """Nine fixed checkpoints; no best-checkpoint selection."""
    values = [row["mean_return"] for row in curve]
    return {
        "initial_return": values[0],
        "final_return": values[-1],
        "learning_gain": values[-1] - values[0],
        "normalized_auc": (0.5 * values[0] + sum(values[1:-1])
                           + 0.5 * values[-1]) / 8,
    }


def write_read(path, summary):
    """Exercise the actual primary JSON path, without a schema framework."""
    path = Path(path)
    path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    readback = json.loads(path.read_text(encoding="utf-8"))
    if readback != summary:
        raise ValueError("Primary result write/read mismatch")
    return readback


def budget512_metrics(curve):
    """Thirty-three fixed checkpoints; three AUC windows; no best-checkpoint selection."""
    values = [row["mean_return"] for row in curve]
    prefix = values[:9]
    late = values[8:]
    return {
        "initial_return": values[0],
        "return_128": values[8],
        "return_512": values[-1],
        "learning_gain_0_512": values[-1] - values[0],
        "learning_gain_128_512": values[-1] - values[8],
        "auc_0_128": (0.5 * prefix[0] + sum(prefix[1:-1]) + 0.5 * prefix[-1]) / 8,
        "auc_0_512": (0.5 * values[0] + sum(values[1:-1]) + 0.5 * values[-1]) / 32,
        "auc_128_512": (0.5 * late[0] + sum(late[1:-1]) + 0.5 * late[-1]) / 24,
    }
