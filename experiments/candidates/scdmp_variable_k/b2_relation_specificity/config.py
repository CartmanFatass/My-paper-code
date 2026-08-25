from __future__ import annotations

from dataclasses import dataclass

CANDIDATE = "SCDMP-B2-RELATION-SPECIFICITY"
REVISION = "SCDMP-B2-SCIENCE-20260813-02"
ARMS = ("FREE-DIRECT", "SCDMP-CORRECT", "SCDMP-ORDER-SHUFFLE")
ALGORITHM_SEEDS = tuple(range(100, 108))
NUMPY_VERSION = "1.26.3"
TORCH_VERSION = "2.7.0+cpu"
N_AGENTS = 4
TRAIN_DURATIONS = (2, 4, 8)
TARGET_DURATIONS = (6, 12)
TRAIN_EPISODES_PER_DURATION = 64
FIT_EPISODES_PER_DURATION = 48
TRAIN_HORIZON = 64
OPTIMIZER_UPDATES = 1_000
MODEL_PARAMETER_COUNT = 26_148
SCALE_FLOOR = 1.0e-3
SCALER_ATOMS_PER_OUTPUT = 10_752
BATCH_ROWS_PER_STRATUM = 8
BANK_ORDER = ("E_2", "E_4", "E_8", "C_22", "C_44")
STRATUM_ORDER = tuple((c, w) for c in ("REAL", "SHAM") for w in range(4))
SCORED_REGIMES = (
    "fixed_4", "fixed_8", "fixed_6", "fixed_12", "switch_6_to_12", "switch_12_to_6",
)
COMPOSITION_SPLITS = {6: ((2, 4), (4, 2)), 12: ((4, 8), (8, 4))}
ADAM = {"lr": 1e-3, "betas": (0.9, 0.999), "eps": 1e-8, "weight_decay": 1e-5}
ORDERED_PARAMETER_NAMES = (
    "node_1.weight", "node_1.bias", "node_2.weight", "node_2.bias",
    "action_embedding.weight", "action_embedding.bias",
    "word_gru.weight_ih", "word_gru.weight_hh", "word_gru.bias_ih", "word_gru.bias_hh",
    "f_1.weight", "f_1.bias", "f_2.weight", "f_2.bias", "f_3.weight", "f_3.bias",
    "gn_1.weight", "gn_1.bias", "gn_2.weight", "gn_2.bias",
    "ge_1.weight", "ge_1.bias", "ge_2.weight", "ge_2.bias",
)
MICROSTEP_LEDGER = {
    "common_training_corpus": 98_304,
    "three_arm_scored": 1_105_920,
    "common_audit_warmup": 24_576,
    "audit_target_words": 373_248,
    "audit_reverse_twins": 373_248,
}
MICROSTEP_TOTAL = 1_975_296
PHYSICAL_FULL_JOINT_TOTAL = 1_228_800
FACTOR_TRANSITIONS_PER_PANEL_KIND = 55_296
TRAINING_FORWARD_TOTAL = 216_024
DHOM_FORWARD_TOTAL = 144


@dataclass(frozen=True)
class ResourceEnvelope:
    cpu_workers: int = 1
    gpu_allowed: bool = False
    wall_seconds: int = 90 * 60
    rss_bytes: int = 2 * 1024**3


RESOURCES = ResourceEnvelope()
