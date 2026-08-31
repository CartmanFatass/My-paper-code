"""Result-blind complete static preflight for CBSC-LR01."""

from __future__ import annotations

import ast
import random
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .codecs import CODEC_SCHEDULES, CodecArm, decode_bits, encode_bits
from .contract import (
    ACTIVE_PARAMETERS,
    FIELD_LAYOUT,
    PRODUCTION_BLOCKER,
    READY_FOR_PRODUCTION,
    SHEAR_OPERATIONS,
)
from .host import Context, panel
from .oracle import assert_static_raw_oracle, compile_raw_oracle
from .resource import peak_rss_bytes
from .support import Purpose, Split


FORBIDDEN_CALLS = {"enumerate_worlds", "evaluate_registered", "write_complete_result"}
FORBIDDEN_MODULES = {
    "experiments.candidates.capability_bound_semantic_currentness.run",
    "experiments.candidates.capability_bound_semantic_currentness.artifact",
}


def _numpy_state_equal(left: tuple[Any, ...], right: tuple[Any, ...]) -> bool:
    return (
        left[0] == right[0] and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def _dependency_firewall() -> bool:
    root = Path(__file__).parent
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name in FORBIDDEN_MODULES for alias in node.names):
                    return False
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module in FORBIDDEN_MODULES:
                    return False
                if any(alias.name in FORBIDDEN_CALLS for alias in node.names):
                    return False
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    return False
    return True


def _local_q(row: Context) -> tuple[Fraction, Fraction, Fraction]:
    fields = row.fields
    active = bool(fields["focal_need_active"])
    neutral = bool(fields["body_native_neutral"])
    gated = bool(fields["access_binding_gated"])
    owner_equal = fields["owner_predecessor"] == fields["owner_current"]
    association_equal = fields["associated_carrier_issued_to"] == fields["physical_receiver"]
    address_equal = fields["body_addressed_receiver"] == fields["physical_receiver"]
    epoch_equal = fields["body_epoch"] == fields["current_epoch"]
    source_equal = fields["payload_source_receiver"] == fields["physical_receiver"]
    content_equal = fields["body_content_bit"] == fields["focal_need_bit"]
    permitted = active and not neutral and (
        not gated or (owner_equal and association_equal and address_equal)
    )
    correct = permitted and epoch_equal and address_equal and source_equal and content_equal
    serve = Fraction(3, 4) if correct else Fraction(-5, 4) if permitted else Fraction(-3, 4)
    refresh = Fraction(1, 8) if active else Fraction(-7, 8)
    return serve, refresh, Fraction(-1, 4)


def run_preflight() -> dict[str, object]:
    """Audit complete legal support without training or exposing learned results."""

    started = time.monotonic()
    baseline_peak_rss = peak_rss_bytes()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    torch_before = torch.random.get_rng_state().clone()
    inverse_ok = True
    target_ok = True
    support_ok = True
    twin_ok = True
    token_ok = True
    tuple_disjoint = True
    witness_ok = True
    legal_inputs = 0
    raw_witness = compile_raw_oracle()
    for purpose, blocks in ((Purpose.MAIN, range(24)), (Purpose.COMPETENCE, range(4))):
        for block in blocks:
            train = panel(purpose, block, Split.TRAIN)
            evaluation = panel(purpose, block, Split.EVAL)
            legal_inputs += len(train) + len(evaluation)
            train_tuples = {tuple(row.fields.values()) for row in train}
            eval_tuples = {tuple(row.fields.values()) for row in evaluation}
            tuple_disjoint = tuple_disjoint and train_tuples.isdisjoint(eval_tuples)
            for field in row_field_names():
                token_ok = token_ok and {row.fields[field] for row in train} == {
                    row.fields[field] for row in evaluation
                }
            for contexts in (train, evaluation):
                target_ok = target_ok and all(row.target_q == _local_q(row) for row in contexts)
                lookup = {(row.address.cell, row.address.slot): row for row in contexts}
                twin_ok = twin_ok and all(
                    row.target_q == lookup[(row.address.cell, row.address.slot ^ 1)].target_q
                    and row.target_q == lookup[(row.address.cell, row.address.slot ^ 2)].target_q
                    for row in contexts
                )
                raw_encoded: list[tuple[int, ...]] = []
                for row in contexts:
                    for arm in CodecArm:
                        encoded = encode_bits(row.canonical, arm)
                        inverse_ok = inverse_ok and decode_bits(encoded, arm) == row.canonical
                    raw_encoded.append(encode_bits(row.canonical, CodecArm.RAW))
                with torch.no_grad():
                    outputs = raw_witness(torch.tensor(raw_encoded, dtype=torch.float32))
                try:
                    assert_static_raw_oracle(outputs)
                    expected = torch.tensor([row.oracle_action for row in contexts], dtype=torch.int64)
                    witness_ok = witness_ok and torch.equal(outputs.argmax(dim=1), expected)
                except ValueError:
                    witness_ok = False
            support_ok = support_ok and len(train) == len(evaluation) == 768

    parameter_ok = sum(parameter.numel() for parameter in raw_witness.parameters()) == ACTIVE_PARAMETERS
    macs_ok = sum(layer.in_features * layer.out_features for layer in raw_witness.layers) == 43_056
    expected_struct = tuple(
        (target + bit, source + bit)
        for bit in range(8)
        for target, source in ((16, 8), (32, 24), (40, 0), (48, 0), (56, 0), (64, 0))
    ) + ((107, 108),)
    expected_sham = tuple(
        (target + bit, source + bit)
        for bit in range(8)
        for target, source in ((16, 24), (32, 0), (40, 8), (48, 24), (56, 8), (64, 24))
    ) + ((107, 109),)
    expected_raw = tuple(
        (offset + target, offset + source)
        for offset in range(0, 104, 8)
        for target, source in ((1, 0), (3, 2), (5, 4), (7, 6))
    )[:49]
    schedules_ok = (
        CODEC_SCHEDULES[CodecArm.STRUCT] == expected_struct
        and CODEC_SCHEDULES[CodecArm.SHAM] == expected_sham
        and CODEC_SCHEDULES[CodecArm.RAW] == expected_raw
        and all(len(schedule) == SHEAR_OPERATIONS for schedule in CODEC_SCHEDULES.values())
    )
    main_steps = 24 * 3 * 64
    competence_steps = 4 * 512
    durable_output_upper_bound = 1024**2 + 24 * 3 * (5 * 512 + 4096) + 4 * 4096
    measured_preflight_peak_rss = peak_rss_bytes()
    explicit_live_training_allowance = 64 * 1024**2
    estimated_production_peak_rss = measured_preflight_peak_rss + explicit_live_training_allowance
    measured_preflight_wall = time.monotonic() - started
    per_adam_step_planning_allowance_seconds = 0.2
    estimated_production_wall = (
        measured_preflight_wall
        + (main_steps + competence_steps) * per_adam_step_planning_allowance_seconds
    )
    rng_ok = (
        random.getstate() == python_before
        and _numpy_state_equal(np.random.get_state(), numpy_before)
        and torch.equal(torch.random.get_rng_state(), torch_before)
    )
    checks = {
        "dependency_firewall": _dependency_firewall(),
        "exact_field_layout": len(FIELD_LAYOUT) == 21 and FIELD_LAYOUT[-1] == ("presentation_flip", 111, 1),
        "codec_schedules_49": schedules_ok,
        "codec_inverse_every_legal_input": inverse_ok,
        "exact_target_ledger_adapter": target_ok,
        "complete_panel_support": support_ok and legal_inputs == (24 + 4) * 2 * 768,
        "train_eval_primitive_tuple_disjoint": tuple_disjoint,
        "train_eval_token_support_equal": token_ok,
        "receiver_presentation_twins": twin_ok,
        "raw_capacity_witness_every_legal_input": witness_ok,
        "active_parameters": parameter_ok,
        "dense_macs": macs_ok,
        "ambient_rng_unchanged": rng_ok,
        "work_counts": main_steps == 4_608 and competence_steps == 2_048,
        "resource_plan": (
            durable_output_upper_bound < 128 * 1024**2
            and estimated_production_peak_rss < 4 * 1024**3
            and estimated_production_wall < 1800
        ),
    }
    return {
        "protocol_id": "CBSC-LR01",
        "mode": "RESULT_BLIND_PREFLIGHT",
        "result_activity": "ZERO",
        "valid": all(checks.values()),
        "ready_for_production": READY_FOR_PRODUCTION,
        "production_blocker": PRODUCTION_BLOCKER,
        "codec_schedules": {
            arm.value: [list(pair) for pair in CODEC_SCHEDULES[arm]] for arm in CodecArm
        },
        "checks": checks,
        "counts": {
            "legal_inputs_audited": legal_inputs,
            "codec_round_trips": legal_inputs * 3,
            "main_adam_steps": 4_608,
            "competence_adam_steps": 2_048,
            "main_training_context_passes": 4_608 * 96,
            "main_scalar_target_exposures": 4_608 * 96 * 3,
            "durable_output_upper_bound_bytes": durable_output_upper_bound,
            "preflight_baseline_peak_rss_bytes": baseline_peak_rss,
            "measured_preflight_peak_rss_bytes": measured_preflight_peak_rss,
            "explicit_live_training_allowance_bytes": explicit_live_training_allowance,
            "estimated_production_peak_rss_bytes": estimated_production_peak_rss,
            "peak_rss_estimate_basis": "MEASURED_PREFLIGHT_LIFETIME_PEAK_PLUS_64MIB_MODEL_OPTIMIZER_TENSOR_AND_NATIVE_WORKSPACE_ALLOWANCE",
            "measured_preflight_wall_seconds": measured_preflight_wall,
            "per_adam_step_planning_allowance_seconds": per_adam_step_planning_allowance_seconds,
            "estimated_production_wall_seconds": estimated_production_wall,
            "wall_estimate_basis": "MEASURED_COMPLETE_PREFLIGHT_PLUS_6656_REGISTERED_ADAM_STEPS_AT_0.2_SECONDS_PER_STEP_PLANNING_ALLOWANCE",
            "worker_threads": 1,
            "wall_seconds_cap": 1800,
            "peak_memory_cap_bytes": 4 * 1024**3,
            "durable_output_cap_bytes": 128 * 1024**2,
        },
        "result_fields": [],
    }


def row_field_names() -> tuple[str, ...]:
    return tuple(name for name, _offset, _width in FIELD_LAYOUT)


__all__ = ["run_preflight"]
