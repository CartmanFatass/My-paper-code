"""Immutable B20 block and panel addresses; safe to import before admission."""
from __future__ import annotations

from dataclasses import dataclass


OBJECT_ID = "s1_ordered_roster_confirmation_b20"
FINAL_ROLLOUT = 45
EVALUATION_ORDER = (5, 7, 6)
WORLD_SEED_BASES = {5: 2_446_500, 7: 2_446_700, 6: 2_446_600}
SCHEDULES = {"F": (6,) * 45, "M": (4, 6, 8) * 15}
PRODUCTION_SPEC_VALUES = {
    "train_n": 6, "test_ns": [5, 7, 6], "horizon": 500,
    "train_lanes": 16, "eval_lanes": 32, "rollouts": 45,
    "panels": [0, 45], "hidden_size": 256, "n_heads": 8,
    "n_layers": 2, "ppo_epochs": 15, "sequence_batch_size": 32,
    "coordinator_batch_size": 1280, "torch_threads": 4,
}


@dataclass(frozen=True)
class Block:
    number: int
    seed: int
    training_world_base: int

    @property
    def tag(self) -> str:
        return f"{OBJECT_ID}_b{self.number}_s{self.seed}"


BLOCKS = {
    1: Block(1, 1_016_101, 3_246_100),
    2: Block(2, 1_017_101, 3_346_100),
    3: Block(3, 1_018_101, 3_446_100),
}

SOURCE_RELATIVE_PATHS = (
    "experiments/candidates/agent_count_generalization/ordered_roster_confirmation_b20/runner.py",
    "experiments/candidates/agent_count_generalization/ordered_roster_confirmation_b20/__init__.py",
    "experiments/candidates/agent_count_generalization/ordered_roster_confirmation_b20/bindings.py",
    "experiments/candidates/agent_count_generalization/ordered_roster_confirmation_b20/reducer.py",
    "scripts/run_agent_count_ordered_roster_confirmation_b20.py",
    "experiments/candidates/agent_count_generalization/local_ordinary_b16/runner.py",
    "experiments/candidates/agent_count_generalization/bounded_confirmation_b15/runner.py",
    "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
    "experiments/candidates/agent_count_generalization/training_condition_b11/runner.py",
    "experiments/candidates/agent_count_generalization/configuration.py",
    "experiments/candidates/agent_count_generalization/runner.py",
    "experiments/candidates/agent_count_generalization/models.py",
    "experiments/candidates/agent_count_generalization/adapter.py",
    "hmasd/agent.py", "hmasd/utils.py",
)
