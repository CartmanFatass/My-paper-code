from __future__ import annotations

from dataclasses import asdict, dataclass

TREATMENT_ID = "VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1"
REVISION = "SP-RDA-MATH-CLOSURE-20260812-06"
SEEDS = (1601, 1621, 1657, 1669, 1693, 1721, 1747, 1783)
TRAIN_SCHEDULES = ((6, 9), (9, 6), (9, 12), (12, 9))
EVAL_SCHEDULES = ((9, 12), (15, 12), (12, 15), (18, 15))
MASSES = ("FIXED_MASS", "REAL_MASS")
GEOMETRIES = ("SEPARABLE", "COUPLED")
CHURNS = ("KEEP_OPTIMAL", "SWITCH_REQUIRED")
ROW_ORDERS = ("STABLE", "REVERSE", "RANDOM_0", "RANDOM_1")
EXECUTABLE_ARMS = ("ZERO-RDA", "FROZEN-RDA", "HANDOFF-RDA", "G-RELEASE", "G-PERMUTE")
AUDIT_SIZES = (15, 30, 60, 120)


@dataclass(frozen=True)
class RegisteredConfig:
    updates: int = 32
    trials_per_cell_update: int = 4
    ppo_epochs: int = 8
    minibatch_trials: int = 8
    learning_rate: float = 3e-4
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_eps: float = 1e-8
    ppo_clip: float = 0.20
    value_coefficient: float = 0.5
    entropy_coefficient: float = 0.01
    gradient_clip: float = 0.5
    bid_sigma: float = 0.20
    eval_worlds_per_cell: int = 24
    audit_repeats: int = 256
    training_raw_cap: int = 96
    training_successes: int = 32
    conclusion_raw_cap: int = 64
    conclusion_successes: int = 24
    certificate_calls_per_raw: int = 24
    audit_warmups: int = 64
    result_schema: str = "vnfc-b3-stage1-result-v1"

    @property
    def train_cells(self) -> int:
        return len(TRAIN_SCHEDULES) * len(MASSES) * len(GEOMETRIES) * len(CHURNS)

    @property
    def trials_per_update(self) -> int:
        return self.train_cells * self.trials_per_cell_update

    @property
    def trials_per_seed(self) -> int:
        return self.updates * self.trials_per_update

    @property
    def optimizer_steps_per_seed(self) -> int:
        return self.updates * self.ppo_epochs * (self.trials_per_update // self.minibatch_trials)

    @property
    def eval_worlds_per_seed(self) -> int:
        return len(EVAL_SCHEDULES) * len(MASSES) * len(GEOMETRIES) * len(CHURNS) * self.eval_worlds_per_cell

    def manifest(self) -> dict:
        out = asdict(self)
        out.update(
            treatment_id=TREATMENT_ID,
            revision=REVISION,
            seeds=list(SEEDS),
            train_schedules=[list(x) for x in TRAIN_SCHEDULES],
            evaluation_schedules=[list(x) for x in EVAL_SCHEDULES],
            executable_stage1_arms=list(EXECUTABLE_ARMS),
            train_cells=self.train_cells,
            trials_per_update=self.trials_per_update,
            trials_per_seed=self.trials_per_seed,
            stage1_trials_total=self.trials_per_seed * len(SEEDS),
            optimizer_steps_per_seed=self.optimizer_steps_per_seed,
            optimizer_steps_total=self.optimizer_steps_per_seed * len(SEEDS),
            eval_worlds_per_seed=self.eval_worlds_per_seed,
            raw_base_cap_total=(self.training_raw_cap + self.conclusion_raw_cap) * 4 * len(SEEDS),
            derived_variant_cap_total=(self.training_raw_cap + self.conclusion_raw_cap) * 4 * len(SEEDS) * 4,
            certificate_solver_call_cap=(self.training_raw_cap + self.conclusion_raw_cap) * 4 * len(SEEDS) * self.certificate_calls_per_raw,
            tagged_conclusion_ceilings_total=self.eval_worlds_per_seed * len(SEEDS),
            row_replicas_per_arm_seed=self.eval_worlds_per_seed * len(ROW_ORDERS),
        )
        return out


REGISTERED = RegisteredConfig()
