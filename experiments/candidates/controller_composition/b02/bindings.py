"""Fixed B02 addresses and exposure; no production tuning switches."""
from __future__ import annotations

OBJECT = "controller_composition_b02"
TAG = "b02_partner_training_20260925"
SEED = 92_526_001
ASSIGNMENT_SEED = 92_526_002
RUNTIME_SEED = 92_526_051
BOOTSTRAP_SEED = 92_526_999
TRAIN_WORLD_BASE = 92_530_000
EVAL_WORLD_BASE = 92_540_000
TRAIN_LANES = 16
EVAL_LANES = 32
HORIZON = 500
ROLLOUTS = 45
EPOCHS = 15
BOOTSTRAP_DRAWS = 10_000
ARMS = ("F1", "F2", "M")
EVAL_LEARNERS = ("I", "F1", "F2", "M")
EVAL_CELLS = tuple((learner, partner) for learner in EVAL_LEARNERS for partner in (1, 2, 3)) + (("OLD3", 3),)
