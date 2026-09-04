from __future__ import annotations

from dataclasses import asdict, dataclass

DIRECTION = "roster_consistent_latent_exploration"
REVISION = "RCLE-B2-SCIENCE-20260814-02"
SCHEMA = "rcle-b2-rev02-atomic-seed-v1"

ARMS = ("RCLE", "VALIDITY-ONLY")
COMMON_ARMS = ARMS
TRAIN_SIZES = (4, 8)
EVAL_SIZES = (4, 8, 12)
LATENTS = (0, 1, 2, 3)
LOCKS = (0, 1, 2, 3)
SEEDS = (2371, 2473, 2591, 2683, 2791, 2903, 3011, 3121, 3251, 3371, 3491, 3613)


@dataclass(frozen=True)
class RegisteredConfig:
    dtype: str = "float64"
    actor_input: int = 11
    actor_hidden: int = 32
    actor_parameters: int = 1506
    posterior_parameters: int = 16
    train_updates: int = 2000
    train_episodes_per_size_update: int = 16
    eval_campaigns_per_size: int = 2048
    eval_campaigns_per_lock: int = 512
    anchor_campaigns_per_lock: int = 256
    actor_learning_rate: float = 1e-3
    posterior_learning_rate: float = 1e-2
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8
    gradient_clip_norm: float = 1.0
    baseline_decay: float = 0.95
    beta: float = 0.10
    max_roster_proposals: int = 4096
    positive_margin: float = 0.10
    no_material_margin: float = 0.05
    fidelity_margin: float = 0.70
    private_cut_margin: float = 0.10
    temporal_cut_margin: float = 0.05
    max_episodes: int = 8_000_000
    max_workers: int = 1
    max_memory_mib: int = 2048
    max_wall_minutes: int = 45

    def manifest(self) -> dict[str, object]:
        out: dict[str, object] = asdict(self)
        out.update(
            direction=DIRECTION,
            revision=REVISION,
            schema=SCHEMA,
            arms=list(ARMS),
            train_sizes=list(TRAIN_SIZES),
            eval_sizes=list(EVAL_SIZES),
            seeds=list(SEEDS),
            xi_law="Uniform[0.3,0.7] retained across X proposals",
            x_law="Beta(8*Xi,8*(1-Xi)) iid candidate conditioned on A_N",
            actor="Linear(11,32)-tanh-Linear(32,32)-tanh-Linear(32,2)",
            rng="BLAKE2b-addressed NumPy PCG64 namespaces",
            only_evaluable_checkpoint="immediately after update 2000",
        )
        return out


REGISTERED = RegisteredConfig()
