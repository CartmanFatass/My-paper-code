"""Frozen constants, projection boundary, cost law, and branch rule for R02."""

from __future__ import annotations

import hashlib
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..arms import initialize_paired_arms
from ..b01.constants import LEARNED_ARMS
from ..policy import FRRIEActorCritic
from ..rng import AddressedRNG
from ..state_codec import encode_optimizer_state
from ..training import make_optimizer

OBJECT_ID = "FRRIE-B01-CONTACT-ACTIVE-R128-R02-20260904"
SEED = 1
SEED_LABEL = "FRRIE-B02-CONTACT-BLOCK-001"
ROOT_HEX = "2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807"
TEST_SEED_LABEL = "FRRIE-B02-CONTACT-TEST-001"
TEST_ROOT_HEX = "98c9faafac89c94a47fc5cf61e715e2f652e9451096ba113d28524f756fc9bc0"
PRODUCTION_UPDATES = 128
PRODUCTION_CHECKPOINTS = (0, 32, 64, 128)
PRODUCTION_EVAL_EPISODES = 256
ROSTERS = (9, 15)
HORIZON = 12
TIGHT_BOX = (-0.04, 0.04)
WIDE_BOX = (-1.50, 1.50)
MEI = 0.005
PUBLIC_ARM = {"PHY_TRUST": "PHY_TRUST_004", "EDGE_FLEX": "EDGE_FLEX_150"}


class ContactActorCritic(FRRIEActorCritic):
    """The unchanged actor/critic with the frozen R02 projection boxes."""

    @property
    def projection_box(self) -> tuple[float, float]:
        return TIGHT_BOX if self.arm_id == "PHY_TRUST" else WIDE_BOX

    def project_beta(self) -> None:
        import torch

        with torch.no_grad():
            self.beta.clamp_(*self.projection_box)


def exposure_record(
    updates: int, changed_coordinates: int = 5, *, adam_lr: float = 0.0003,
) -> dict[str, Any]:
    nominal = round(updates * adam_lr, 10)
    ratio = round(nominal / 0.05, 10)
    return {
        "updates": updates,
        "adam_lr": adam_lr,
        "nominal_lr_exposure": nominal,
        "init_half_range": 0.05,
        "nominal_exposure_over_init_half_range": ratio,
        "tight_box_half_width": 0.04,
        "initial_projection_changed_coordinates": changed_coordinates,
        "line": (
            f"updates={updates}; adam_lr={adam_lr:g}; nominal_lr_exposure={nominal:g}; "
            f"init_half_range=0.05; nominal_exposure_over_init_half_range={ratio:g}; "
            f"tight_box_half_width=0.04; "
            f"initial_projection_changed_coordinates={changed_coordinates}"
        ),
    }


def cost_config(
    updates: int, checkpoints: Sequence[int], episodes: int,
) -> dict[str, Any]:
    training = 4_928 * updates
    evaluation = len(checkpoints) * len(ROSTERS) * episodes * HORIZON
    uniform = len(ROSTERS) * episodes * HORIZON
    return {
        "updates": updates,
        "checkpoints": list(checkpoints),
        "evaluation_episodes_per_cell": episodes,
        "learned_training_per_arm": training,
        "learned_evaluation_per_arm": evaluation,
        "learned_total_per_arm": training + evaluation,
        "shared_uniform": uniform,
        "invocation": 2 * (training + evaluation) + uniform,
        "optimizer_steps_per_arm": updates,
        "cells": len(ROSTERS) + 2 * len(checkpoints) * len(ROSTERS),
        "evaluation_episodes_total": (
            len(ROSTERS) * episodes
            + 2 * len(checkpoints) * len(ROSTERS) * episodes
        ),
        "factual_learner_transitions_per_arm": 64 * updates * HORIZON,
        "factual_learner_transitions_total": 128 * updates * HORIZON,
    }


def _finite_descriptors(rule_inputs: Mapping[str, Any]) -> dict[int, tuple[float, float]] | None:
    rows = rule_inputs.get("update_128_descriptors")
    if not isinstance(rows, list) or len(rows) != 2:
        return None
    parsed: dict[int, tuple[float, float]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"roster", "d_128", "e_128"}:
            return None
        roster, d_value, e_value = row["roster"], row["d_128"], row["e_128"]
        if roster not in ROSTERS or any(
            type(value) not in (int, float) or not math.isfinite(float(value))
            for value in (d_value, e_value)
        ):
            return None
        parsed[int(roster)] = (float(d_value), float(e_value))
    return parsed if set(parsed) == set(ROSTERS) else None


def classify_r02(
    rule_inputs: Mapping[str, Any], *, test_only: bool = False, branch_prefix: str = "R02",
) -> str:
    if test_only:
        return "TEST_ONLY_NON_RESULT"
    required_true = (
        "complete", "admission_valid", "exposure_present",
        "raw_paired_initialization_equal", "initial_tight_clip_changed_exactly_five",
        "optimizer_moments_unchanged_by_projection", "paired_information_work_equal",
        "evaluation_preserved_model_bytes", "same_evaluation_tapes",
        "required_curves_and_counts_present",
    )
    if branch_prefix == "R06" and any(
        rule_inputs.get(name) != {public: [0.003] for public in PUBLIC_ARM.values()}
        for name in ("initial_optimizer_group_lr", "final_optimizer_group_lr")
    ):
        return f"{branch_prefix}_INVALID_INCOMPLETE"
    required_positive = (
        "learner_transitions", "training_episodes", "backward_calls", "adam_steps",
        "evaluation_episodes",
    )
    descriptors = _finite_descriptors(rule_inputs)
    if (
        any(rule_inputs.get(name) is not True for name in required_true)
        or any(
            type(rule_inputs.get(name)) is not int or rule_inputs[name] <= 0
            for name in required_positive
        )
        or rule_inputs.get("first_tight_contact_update") != 0
        or descriptors is None
    ):
        return f"{branch_prefix}_INVALID_INCOMPLETE"
    if any(e_value < 0.0 for _, e_value in descriptors.values()):
        return f"{branch_prefix}_EDGE_BELOW_UNIFORM"
    if all(d_value >= MEI for d_value, _ in descriptors.values()):
        return f"{branch_prefix}_FAVORABLE_BOTH"
    if any(d_value <= -MEI for d_value, _ in descriptors.values()):
        return f"{branch_prefix}_ADVERSE_OR_MIXED"
    return f"{branch_prefix}_SMALL_OR_ROSTER_MIXED"


def _initialize_contact_pair(root_hex: str, seed_label: str, *, adam_lr: float = 0.0003) -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, bytes]
]:
    """Construct the raw pair, observe it, then apply the checkpoint-0 boxes."""

    root = bytes.fromhex(root_hex)
    phy_arm, edge_arm = initialize_paired_arms(AddressedRNG(root), seed_label)
    raw_arm_bytes = {
        "PHY_TRUST": phy_arm.parameter_bytes(),
        "EDGE_FLEX": edge_arm.parameter_bytes(),
    }
    models = {
        "PHY_TRUST": ContactActorCritic(phy_arm),
        "EDGE_FLEX": ContactActorCritic(edge_arm),
    }
    raw_model_bytes = {arm: models[arm].parameter_bytes() for arm in LEARNED_ARMS}
    optimizers = {arm: make_optimizer(models[arm]) for arm in LEARNED_ARMS}
    for optimizer in optimizers.values():
        for group in optimizer.param_groups:
            group["lr"] = adam_lr
    initial_group_lr = {
        PUBLIC_ARM[arm]: [group["lr"] for group in optimizers[arm].param_groups]
        for arm in LEARNED_ARMS
    }
    optimizer_before = {
        arm: encode_optimizer_state(models[arm], optimizers[arm]) for arm in LEARNED_ARMS
    }
    raw_beta = models["PHY_TRUST"].beta.detach().clone()
    edge_beta = models["EDGE_FLEX"].beta.detach().clone()
    projected = raw_beta.clamp(*TIGHT_BOX)
    changed_mask = (projected != raw_beta).reshape(-1)
    changed_indices = tuple(
        int(value) for value in np.flatnonzero(changed_mask.detach().numpy()).tolist()
    )
    overshoot = float((projected - raw_beta).abs().max().item())
    displacement = float((projected - raw_beta).abs().sum().item())
    models["PHY_TRUST"].project_beta()
    models["EDGE_FLEX"].project_beta()
    optimizer_after = {
        arm: encode_optimizer_state(models[arm], optimizers[arm]) for arm in LEARNED_ARMS
    }
    audit = {
        "initial_optimizer_group_lr": initial_group_lr,
        "raw_paired_arm_bytes_equal": raw_arm_bytes["PHY_TRUST"] == raw_arm_bytes["EDGE_FLEX"],
        "raw_paired_model_bytes_equal": raw_model_bytes["PHY_TRUST"] == raw_model_bytes["EDGE_FLEX"],
        "raw_parameter_sha256": hashlib.sha256(raw_model_bytes["PHY_TRUST"]).hexdigest(),
        "raw_beta_min": float(raw_beta.min().item()),
        "raw_beta_max": float(raw_beta.max().item()),
        "tight_box": list(TIGHT_BOX),
        "wide_box": list(WIDE_BOX),
        "tight_changed_coordinates": len(changed_indices),
        "tight_changed_coordinate_indices": list(changed_indices),
        "tight_maximum_overshoot": overshoot,
        "tight_projection_displacement": displacement,
        "tight_projection_matches_direct_clip": bool(models["PHY_TRUST"].beta.detach().equal(projected)),
        "wide_initial_projection_identity": bool(models["EDGE_FLEX"].beta.detach().equal(edge_beta)),
        "optimizer_state_pair_equal_before_projection": optimizer_before["PHY_TRUST"] == optimizer_before["EDGE_FLEX"],
        "optimizer_state_pair_equal_after_projection": optimizer_after["PHY_TRUST"] == optimizer_after["EDGE_FLEX"],
        "optimizer_state_unchanged_by_initial_projection": all(
            optimizer_before[arm] == optimizer_after[arm] for arm in LEARNED_ARMS
        ),
        "optimizer_sha256_before_projection": {
            PUBLIC_ARM[arm]: hashlib.sha256(optimizer_before[arm]).hexdigest()
            for arm in LEARNED_ARMS
        },
        "optimizer_sha256_after_projection": {
            PUBLIC_ARM[arm]: hashlib.sha256(optimizer_after[arm]).hexdigest()
            for arm in LEARNED_ARMS
        },
        "first_tight_contact_update": 0,
    }
    return models, optimizers, audit, raw_model_bytes


def initialize_contact_pair() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, bytes]
]:
    return _initialize_contact_pair(ROOT_HEX, SEED_LABEL)


def initialize_test_contact_pair() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, bytes]
]:
    return _initialize_contact_pair(TEST_ROOT_HEX, TEST_SEED_LABEL)
