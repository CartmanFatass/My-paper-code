"""Frozen predictive auxiliary A01 bindings and per-arm panel summary."""

import math


OBJECT = "FOLR_PREDICTIVE_AUX_A01_783101"
TRAINING_SEED = 783101
EVALUATION_SEED = 1783101
PROBE_SEED = 2783101
TRAIN_EPISODES = 5000
TRAIN_TRANSITIONS = 100000
OPTIMIZER_STEPS = 4969
PANEL_EPISODES = 128
PANEL_TRANSITIONS = 2560


def arm_result(values):
    if len(values) != PANEL_EPISODES or any(not math.isfinite(value) for value in values):
        raise ValueError("native panel must contain 128 finite returns")
    mean = sum(values) / len(values)
    return {
        "mean": mean,
        "minimum": min(values),
        "maximum": max(values),
        "negative_count": sum(value < 0 for value in values),
        "episodes": len(values),
    }


