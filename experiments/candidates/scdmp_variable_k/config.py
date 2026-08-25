from __future__ import annotations

from dataclasses import dataclass

CANDIDATE = "SCDMP-B1"
REVISION = "SCDMP-B1-SCIENCE-20260812-05"
ARMS = ("SCDMP", "SCDMP-NOCOMP")
ALGORITHM_SEEDS = tuple(range(8))

NUMPY_VERSION = "1.26.3"
N_AGENTS = 4
ACTIONS = (-1, 0, 1)
ACTION_NAMES = ("LEFT", "COAST", "RIGHT")
EPISODE_HORIZON = 240
TRAIN_HORIZON = 64
TRAIN_DURATIONS = (2, 4, 8)
TARGET_DURATIONS = (6, 12)
TRAIN_EPISODES_PER_DURATION = 64
FIT_EPISODES_PER_DURATION = 48
PROBE_EPISODES_PER_DURATION = 16
EVAL_EPISODES_PER_REGIME = 32
AUDIT_STATES_PER_DURATION = 32
AUDIT_WARMUP_STEPS = 48
AUDIT_ACTION_COUNT = 81

V_STAR = 0.20
E_BOUND = 1.5
V_BOUND = 0.6
POSITION_STEP = 0.10
ACTION_ACCELERATION = 0.12
WIND_ACCELERATION = 0.06
GAP_FAILURE = 0.25

TOKEN_COEFFICIENTS = {
    "A_REAL": (0.98, 1.0),
    "B_REAL": (0.82, -1.0),
    "A_SHAM": (0.90, 0.0),
    "B_SHAM": (0.90, 0.0),
}
TOKEN_INDEX = {"A_REAL": 0, "B_REAL": 1, "A_SHAM": 2, "B_SHAM": 3}

TRAIN_WORD_PATTERNS = {
    2: ("AA", "BB", "AB", "BA"),
    4: ("AAAA", "BBBB", "AABB", "BBAA"),
    8: ("AAAAAAAA", "BBBBBBBB", "AAAABBBB", "BBBBAAAA"),
}
TARGET_WORD_PATTERNS = {
    6: ("AABBBB", "BBBBAA", "AAAABB", "BBAAAA"),
    12: (
        "AAAABBBBBBBB", "BBBBBBBBAAAA", "AAAAAAAABBBB", "BBBBAAAAAAAA",
    ),
}
COMPOSITION_SPLITS = {6: ((2, 4), (4, 2)), 12: ((4, 8), (8, 4))}
SCORED_REGIMES = (
    "fixed_4", "fixed_8", "fixed_6", "fixed_12", "switch_6_to_12", "switch_12_to_6",
)
TARGET_REGIMES = SCORED_REGIMES[2:]

MODEL_PARAMETER_COUNT = 26_148
MODEL_PARAMETER_BREAKDOWN = {
    "node_encoder": 1_184,
    "action_embedding": 32,
    "word_gru": 3_744,
    "F": 9_026,
    "G_node": 4_801,
    "G_edge": 7_361,
}
MODEL_PARAMETER_ABORT_CEILING = 75_000
OPTIMIZER_UPDATES = 1_000
ADAM = {
    "lr": 1.0e-3,
    "betas": (0.9, 0.999),
    "eps": 1.0e-8,
    "weight_decay": 1.0e-5,
    "gradient_norm_clip": 1.0,
}
COMPOSITION_WEIGHT = {"SCDMP": 0.5, "SCDMP-NOCOMP": 0.0}
SCALE_FLOOR = 1.0e-3
SCALER_DDOF = 0
SCALER_ATOMS_PER_OUTPUT = 10_752
SCALER_NUMPY_CALL = "numpy.std(x64,axis=None,dtype=numpy.float64,ddof=0)"
BATCH_ROWS_PER_STRATUM = 8
BANK_ORDER = ("E_2", "E_4", "E_8", "C_22", "C_44")
STRATUM_ORDER = tuple(
    (dynamics_class, word_row)
    for dynamics_class in ("REAL", "SHAM")
    for word_row in range(4)
)

CPU_WORKERS = 1
GPU_ALLOWED = False
RSS_LIMIT_BYTES = 2 * 1024**3
WALL_LIMIT_SECONDS = 90 * 60
MICROSTEP_LEDGER = {
    "common_training_corpus": 98_304,
    "scored_evaluation": 737_280,
    "common_audit_warmup": 24_576,
    "audit_target_words": 373_248,
    "audit_reverse_twins": 373_248,
}
MICROSTEP_MAXIMUM = 1_606_656


def word(pattern: str, dynamics_class: str) -> tuple[str, ...]:
    if dynamics_class not in ("REAL", "SHAM"):
        raise ValueError(f"unknown dynamics class: {dynamics_class}")
    return tuple(f"{letter}_{dynamics_class}" for letter in pattern)


def word_table(duration: int, dynamics_class: str, *, target: bool = False) -> tuple[tuple[str, ...], ...]:
    patterns = TARGET_WORD_PATTERNS if target else TRAIN_WORD_PATTERNS
    return tuple(word(pattern, dynamics_class) for pattern in patterns[duration])


def target_decomposition_certificate() -> dict[str, object]:
    checks: dict[str, bool] = {}
    for duration, patterns in TARGET_WORD_PATTERNS.items():
        for row, pattern in enumerate(patterns):
            for prefix, suffix in COMPOSITION_SPLITS[duration]:
                checks[f"k{duration}_row{row}_{prefix}+{suffix}"] = (
                    pattern[:prefix] in TRAIN_WORD_PATTERNS[prefix]
                    and pattern[prefix:] in TRAIN_WORD_PATTERNS[suffix]
                )
    return {"checks": checks, "conforming": all(checks.values())}


@dataclass(frozen=True)
class ResourceEnvelope:
    cpu_workers: int = CPU_WORKERS
    gpu_allowed: bool = GPU_ALLOWED
    rss_limit_bytes: int = RSS_LIMIT_BYTES
    wall_limit_seconds: int = WALL_LIMIT_SECONDS
    microstep_maximum: int = MICROSTEP_MAXIMUM
    optimizer_updates_per_arm_seed: int = OPTIMIZER_UPDATES


REGISTERED_RESOURCES = ResourceEnvelope()
