from __future__ import annotations

from dataclasses import asdict, dataclass

DIRECTION = "semantic_graphon_shared_policy"
REVISION = "SGSP-B1-SCIENCE-20260813-05"
SCHEMA = "sgsp-b1-rev05-atomic-result-v1"

SCOUT = 0
RELAY = 1
ROLE_NAMES = ("SCOUT", "RELAY")
ROLE_COORDINATES = (0.25, 0.75)
GRAPHON = ((1.0, 0.2), (0.2, 1.0))
ALT_GRAPHON = ((0.2, 1.0), (1.0, 0.2))
SELF_EDGES_INCLUDED = True
POPULATION_NORMALIZATION = "1/N"
CANONICAL_ROW_ORDER = "lexicographic(role,within_role_slot)"
NOMINAL_HANDLE_RULE = "Handle(phase,seed,N,regime,episode,role,within_role_slot)"

TRAIN_SIZES = (8, 12)
HELDOUT_SIZES = (6, 16)
ALL_SIZES = (6, 8, 12, 16)
REGIMES = ("SAME", "OPPOSED")
TRAIN_CELLS_LEXICOGRAPHIC = tuple(
    (n, regime) for n in sorted(TRAIN_SIZES) for regime in sorted(REGIMES)
)
EVAL_CELLS = tuple((n, regime) for n in ALL_SIZES for regime in REGIMES)
HELDOUT_CELLS = tuple((n, regime) for n in HELDOUT_SIZES for regime in REGIMES)

ARMS = ("SGSP-W", "ALT-CENTER", "EDGE-PE", "ANON-MEAN")
EDGE_ARMS = ("SGSP-W", "ALT-CENTER", "EDGE-PE")
RESIDUAL_SCALES = {"SGSP-W": 0.25, "ALT-CENTER": 0.25, "EDGE-PE": 2.0}
ARM_CENTERS = {"SGSP-W": GRAPHON, "ALT-CENTER": ALT_GRAPHON, "EDGE-PE": GRAPHON}
ACTIONS = ("SERVE_NEG", "SERVE_POS")

SEEDS = (
    4103, 4127, 4153, 4177, 4201, 4229, 4253, 4273,
    4297, 4327, 4357, 4387, 4409, 4441, 4463, 4483,
)

# These labels and the algorithms in rng.py are prospective registered source
# semantics. Every world/action/permutation address includes N.
COUNTER_ROOT = f"{DIRECTION}|{REVISION}|blake2b-counter-v1"
COUNTER_ALGORITHM = {
    "digest": "BLAKE2b-128 over UTF-8 unit-separator-delimited address fields",
    "uniform01": "leading uint64 little-endian, top 53 bits, multiply 2^-53",
    "normal": "fixed Box-Muller from terminal gaussian/u1 and gaussian/u2",
    "bounded_integer": "uint64 rejection below 2^64-(2^64 mod bound)",
    "permutation": "Fisher-Yates with addressed shuffle_stop and rejection index",
    "forced_nonidentity": "outer attempt increments only for whole identity permutation",
}
COUNTER_TERMINALS = (
    "orientation",
    "gaussian",
    "action",
    "identity_replay_permutation",
    "initialization",
)


@dataclass(frozen=True)
class RegisteredConfig:
    dtype: str = "float64"
    encoder_hidden: int = 32
    message_width: int = 33
    actor_input: int = 36
    actor_hidden: int = 32
    action_count: int = 2
    train_updates: int = 480
    worlds_per_train_cell_update: int = 16
    train_batch_worlds: int = 64
    eval_worlds_per_cell: int = 256
    learning_rate: float = 4e-4
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8
    adam_amsgrad: bool = False
    weight_decay: float = 0.0
    gradient_clip_norm: float = 2.0
    entropy_coefficient: float = 0.01
    support_softmax_mass: float = 0.96
    support_floor: float = 0.02
    support_ceiling: float = 0.98
    summary_epsilon: float = 1e-12
    dense_tolerance: float = 1e-10
    permutation_tolerance: float = 1e-10
    material_return_margin: float = 0.025
    reassociation_return_threshold: float = 0.075
    reassociation_tv_threshold: float = 0.10
    attenuation_threshold: float = 0.015
    max_formal_wall_clock_hours: int = 8
    max_workers: int = 1

    @property
    def edge_arm_parameters(self) -> int:
        return 64 + 4 + 1184 + 66

    @property
    def anon_parameters(self) -> int:
        return 64 + 1184 + 66

    def manifest(self) -> dict[str, object]:
        out: dict[str, object] = asdict(self)
        out.update(
            direction=DIRECTION,
            revision=REVISION,
            schema=SCHEMA,
            seeds=list(SEEDS),
            train_sizes=list(TRAIN_SIZES),
            heldout_sizes=list(HELDOUT_SIZES),
            regimes=list(REGIMES),
            arms=list(ARMS),
            graphon=[list(row) for row in GRAPHON],
            alt_graphon=[list(row) for row in ALT_GRAPHON],
            residual_scales=dict(RESIDUAL_SCALES),
            self_edges_included=SELF_EDGES_INCLUDED,
            population_normalization=POPULATION_NORMALIZATION,
            canonical_row_order=CANONICAL_ROW_ORDER,
            nominal_handle_rule=NOMINAL_HANDLE_RULE,
            counter_root=COUNTER_ROOT,
            counter_algorithm=dict(COUNTER_ALGORITHM),
            counter_terminals=list(COUNTER_TERMINALS),
            edge_arm_parameters=self.edge_arm_parameters,
            anon_parameters=self.anon_parameters,
            training_episode_rule="16*(update-1)+local_e",
            evaluation_episode_rule="0..255 under evaluation phase",
        )
        return out


REGISTERED = RegisteredConfig()
