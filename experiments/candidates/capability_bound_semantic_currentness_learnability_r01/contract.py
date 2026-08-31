"""Result-blind immutable contract constants for CBSC-LR01."""

from __future__ import annotations

from typing import Final


PROTOCOL_ID: Final = "CBSC-LR01"
SCHEMA_ID: Final = "cbsc_lr01_complete_result_v1"
READY_FOR_PRODUCTION: Final = True
PRODUCTION_BLOCKER: Final = None
ARMS: Final = ("STRUCTURED_CBSC", "STRUCTURED_SHAM", "RAW_FLEX")
PURPOSES: Final = ("MAIN", "COMPETENCE")
SPLITS: Final = ("TRAIN", "EVAL")

INPUT_BITS: Final = 112
HIDDEN_WIDTHS: Final = (160, 128, 32, 16)
OUTPUTS: Final = 3
ACTIVE_PARAMETERS: Final = 43_395
SHEAR_OPERATIONS: Final = 49

CELLS: Final = 48
SLOTS: Final = 16
PANEL_CONTEXTS: Final = CELLS * SLOTS
BATCH_SIZE: Final = 96
BATCHES_PER_EPOCH: Final = 8
MAIN_BLOCKS: Final = 24
COMPETENCE_BLOCKS: Final = 4
MAIN_UPDATES: Final = 64
COMPETENCE_UPDATES: Final = 512
CHECKPOINTS: Final = (0, 8, 16, 32, 64)

OPTIMIZER: Final = {
    "name": "Adam",
    "learning_rate": 1e-3,
    "betas": [0.9, 0.999],
    "epsilon": 1e-8,
    "weight_decay": 0.0,
    "global_gradient_norm_clip": 1.0,
}
LOSS: Final = {
    "name": "mean_squared_error",
    "dtype": "float32",
    "shape": [BATCH_SIZE, OUTPUTS],
    "reduction": "mean_over_all_288_components",
    "weighting": None,
    "normalization": None,
    "discount": None,
    "auxiliary": None,
    "value_clip": None,
}
RESOURCE_CAPS: Final = {
    "threads": 1,
    "wall_seconds": 1800,
    "rss_bytes": 4 * 1024**3,
    "artifact_bytes": 128 * 1024**2,
}

FIELD_LAYOUT: Final = (
    ("physical_receiver", 0, 8),
    ("owner_predecessor", 8, 8),
    ("owner_current", 16, 8),
    ("body_epoch", 24, 8),
    ("current_epoch", 32, 8),
    ("associated_carrier_issued_to", 40, 8),
    ("execution_carrier_issued_to", 48, 8),
    ("body_addressed_receiver", 56, 8),
    ("payload_source_receiver", 64, 8),
    ("carrier_nonce", 72, 8),
    ("body_nonce", 80, 8),
    ("presentation_slot", 88, 8),
    ("public_phase", 96, 8),
    ("focal_need_active", 104, 1),
    ("access_binding_gated", 105, 1),
    ("body_native_neutral", 106, 1),
    ("body_content_bit", 107, 1),
    ("focal_need_bit", 108, 1),
    ("public_z0", 109, 1),
    ("public_z1", 110, 1),
    ("presentation_flip", 111, 1),
)


def describe() -> dict[str, object]:
    """Return configuration identity without reading or producing results."""

    from .codecs import CODEC_SCHEDULES, CodecArm

    return {
        "protocol_id": PROTOCOL_ID,
        "schema": SCHEMA_ID,
        "mode": "RESULT_BLIND_DESCRIBE",
        "result_activity": "ZERO",
        "ready_for_production": READY_FOR_PRODUCTION,
        "production_blocker": PRODUCTION_BLOCKER,
        "arms": list(ARMS),
        "representation": {
            "canonical_bits": INPUT_BITS,
            "bit_order": "LSB_FIRST_WITHIN_EACH_UINT8",
            "field_layout": [list(field) for field in FIELD_LAYOUT],
            "codec": "LOSSLESS_XOR_SHEAR",
            "operations_per_arm": SHEAR_OPERATIONS,
            "ordered_schedules": {
                arm.value: [list(pair) for pair in CODEC_SCHEDULES[arm]]
                for arm in CodecArm
            },
        },
        "network": {
            "widths": [INPUT_BITS, *HIDDEN_WIDTHS, OUTPUTS],
            "hidden_activation": "ReLU",
            "dtype": "float32",
            "active_parameters": ACTIVE_PARAMETERS,
            "dense_macs_per_context": 43_056,
            "hidden_initialization": "IDENTICAL_ADDRESSED",
            "output_head_initialization": "ZERO_WEIGHT_AND_BIAS",
        },
        "optimizer": dict(OPTIMIZER),
        "loss": dict(LOSS),
        "support": {
            "cells": CELLS,
            "slots": SLOTS,
            "contexts_per_panel": PANEL_CONTEXTS,
            "batch_size": BATCH_SIZE,
            "batches_per_epoch": BATCHES_PER_EPOCH,
            "main_blocks": MAIN_BLOCKS,
            "competence_blocks": COMPETENCE_BLOCKS,
            "main_updates": MAIN_UPDATES,
            "competence_updates": COMPETENCE_UPDATES,
            "checkpoints": list(CHECKPOINTS),
        },
        "resource_caps": dict(RESOURCE_CAPS),
        "publication": {
            "atomic": True,
            "create_only": True,
            "complete_only": True,
            "durable_model_or_optimizer_state": False,
            "resume": False,
        },
        "dependency_firewall": {
            "old_exact_runner": False,
            "old_exact_enumerator": False,
            "old_exact_artifact": False,
        },
        "result_fields": [],
    }


__all__ = [
    "ACTIVE_PARAMETERS", "ARMS", "BATCHES_PER_EPOCH", "BATCH_SIZE", "CELLS",
    "CHECKPOINTS", "COMPETENCE_BLOCKS", "COMPETENCE_UPDATES", "FIELD_LAYOUT",
    "HIDDEN_WIDTHS", "INPUT_BITS", "LOSS", "MAIN_BLOCKS", "MAIN_UPDATES",
    "OPTIMIZER", "OUTPUTS", "PANEL_CONTEXTS", "PROTOCOL_ID", "PURPOSES",
    "PRODUCTION_BLOCKER", "READY_FOR_PRODUCTION", "RESOURCE_CAPS", "SCHEMA_ID",
    "SHEAR_OPERATIONS", "SLOTS", "SPLITS",
    "describe",
]
