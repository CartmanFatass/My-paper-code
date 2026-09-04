from __future__ import annotations

from dataclasses import asdict, dataclass

DIRECTION = "roster_consistent_latent_exploration"
REVISION = "RCLE-CPC-SCIENCE-20260815-04"
SCHEMA = "rcle-cpc-r04-atomic-seed-v1"
RNG_BINDING = "rcle-cpc-r04-blake2b-pcg64-v1"
SCIENCE_CARD_SHA256 = "7D10160836827A4AC036F01D0279BE5BF0E587C3A134785A7E470900FA1190EC"
PRO_CLOSED_INTAKE_SHA256 = "9C8673ADC14828DDD11D14548FE521038CF34E06BF08780D590ECB9B1B3F4050"

ARMS = ("COARSE-PERSISTENT", "FLEXIBLE-PERSISTENT", "CONTEXT-SHUFFLED-COARSE")
TRAIN_SIZES = (5, 7)
EVAL_SIZES = (5, 7, 9)
HANDOFF_STATES = (False, True)
SEEDS = (4109, 4217, 4337, 4441, 4561, 4673, 4787, 4903,
         5021, 5147, 5261, 5381, 5503, 5623, 5741, 5861)


@dataclass(frozen=True)
class RegisteredConfig:
    dtype: str = "float64"
    manager_element_input: int = 3
    manager_hidden: int = 32
    actor_input: int = 16
    actor_hidden: int = 64
    latent_dim: int = 8
    macro_states: int = 2
    refinements_per_macro: int = 4
    manager_parameters: int = 1524
    embedding_parameters: int = 80
    actor_parameters: int = 5443
    parameters_per_arm: int = 7047
    train_updates: int = 1000
    train_episodes_per_cell: int = 16
    eval_episodes_per_cell: int = 2048
    baseline_decay: float = 0.95
    gradient_direction_scale: float = 0.10
    learning_rate: float = 0.01
    nonzero_update_norm: float = 0.001
    clue_accuracy: float = 0.70
    value_mission_weight: float = 0.65
    value_pre_accuracy_weight: float = 0.15
    value_post_accuracy_weight: float = 0.15
    value_pre_validity_weight: float = 0.025
    value_post_validity_weight: float = 0.025
    primary_gamma: float = 0.9875
    mechanism_gamma: float = 1.0 - 0.05 / 6.0
    max_episodes: int = 4_000_000
    max_workers: int = 1
    max_memory_mib: int = 2048
    max_wall_minutes: int = 45

    def manifest(self) -> dict[str, object]:
        out: dict[str, object] = asdict(self)
        out.update(
            direction=DIRECTION,
            revision=REVISION,
            schema=SCHEMA,
            rng_binding=RNG_BINDING,
            science_card_sha256=SCIENCE_CARD_SHA256,
            pro_closed_intake_sha256=PRO_CLOSED_INTAKE_SHA256,
            arms=list(ARMS),
            train_sizes=list(TRAIN_SIZES),
            eval_sizes=list(EVAL_SIZES),
            handoff_states=list(HANDOFF_STATES),
            seeds=list(SEEDS),
            manager="set-mean(Linear(3,32)-tanh-Linear(32,32)-tanh)+N/9; heads 2 and 8",
            actor="Linear(16,64)-tanh-Linear(64,64)-tanh-Linear(64,3)",
            optimizer="joint plain SGD; raw complete-tensor direction norm; nonzero update norm 0.001",
            only_evaluable_checkpoint="immediately after update 1000",
        )
        return out


REGISTERED = RegisteredConfig()
