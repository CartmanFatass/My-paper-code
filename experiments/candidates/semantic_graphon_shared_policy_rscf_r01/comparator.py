"""Literal PHY-TRUST within EDGE-FLEX comparator contract and audits."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from typing import Mapping

import torch
from torch import Tensor

from .policy import ACTOR_PARAMETER_SHAPES, CRITIC_PARAMETER_SHAPES
from .training import (
    ADAM_BETAS,
    ADAM_EPSILON,
    ADAM_LEARNING_RATE,
    EDGE_FLEX_BOUND,
    GLOBAL_GRADIENT_NORM_CLIP,
    PHY_TRUST_BOUND,
)


@dataclass(frozen=True)
class ArmContract:
    """Value-free construction/opportunity contract for one learned arm."""

    arm_name: str
    projection_box: tuple[float, float]
    observation_width: int = 22
    message_width: int = 32
    actor_input_width: int = 55
    hidden_width: int = 64
    union_action_width: int = 6
    public_roles: tuple[str, ...] = (
        "WEST-SURVEYOR",
        "EAST-SURVEYOR",
        "RIDGE-RELAY",
    )
    legal_action_indices: tuple[tuple[int, ...], ...] = (
        (0, 1, 5),
        (0, 1, 5),
        (2, 3, 4, 5),
    )
    legal_uniform_floor_mass: float = 0.04
    beta_shape: tuple[int, ...] = (3, 3, 2)
    registered_rosters: tuple[int, ...] = (9, 15, 6, 21)
    training_rosters: tuple[int, ...] = (9, 15)
    episodes_per_update: int = 64
    episodes_per_training_roster: int = 32
    selected_origins_per_role_per_episode: int = 1
    selected_roles_per_episode: int = 3
    legal_q_entries_by_role: tuple[int, ...] = (3, 3, 4)
    alternative_branches_by_role: tuple[int, ...] = (2, 2, 3)
    selector_is_arm_independent: bool = True
    selector_is_state_action_outcome_independent: bool = True
    antithetic_slot_pairing: bool = True
    common_future_tape: bool = True
    focal_only_current_action_replacement: bool = True
    teammate_current_actions_factual: bool = True
    closed_loop_future_policy: bool = True
    factual_branch_identity_required: bool = True
    branch_targets_stopped: bool = True
    branch_objects_in_execution_inputs: bool = False
    branch_objects_in_critic: bool = False
    branch_objects_in_checkpoint: bool = False
    adam_learning_rate: float = ADAM_LEARNING_RATE
    adam_betas: tuple[float, float] = ADAM_BETAS
    adam_epsilon: float = ADAM_EPSILON
    adam_weight_decay: float = 0.0
    global_gradient_norm_clip: float = GLOBAL_GRADIENT_NORM_CLIP
    backward_calls_per_update: int = 1
    optimizer_steps_per_update: int = 1
    training_updates: int = 512
    evaluable_checkpoints: tuple[int, ...] = (512,)


@dataclass(frozen=True)
class ComparatorAudit:
    passed: bool
    initialization_digest: str
    parameter_schema_digest: str
    common_contract_digest: str
    only_algorithmic_difference: str
    phy_projection_box: tuple[float, float]
    edge_projection_box: tuple[float, float]
    literal_containment: bool
    strict_capacity_witness_beta: float
    identical_information: bool
    identical_parameters_and_initialization: bool
    identical_selector_opportunity: bool
    identical_branch_opportunity: bool
    identical_optimizer_and_checkpoint: bool


def phy_trust_contract() -> ArmContract:
    return ArmContract(
        arm_name="PHY-TRUST",
        projection_box=(-PHY_TRUST_BOUND, PHY_TRUST_BOUND),
    )


def edge_flex_contract() -> ArmContract:
    return ArmContract(
        arm_name="EDGE-FLEX",
        projection_box=(-EDGE_FLEX_BOUND, EDGE_FLEX_BOUND),
    )


def parameter_initialization_digest(parameters: Mapping[str, Tensor]) -> str:
    """Hash an externally supplied initialization without creating one."""

    expected = {**ACTOR_PARAMETER_SHAPES, **CRITIC_PARAMETER_SHAPES}
    missing = sorted(set(expected) - set(parameters))
    extra = sorted(set(parameters) - set(expected))
    if missing or extra:
        raise ValueError(f"initialization schema mismatch: missing={missing}, extra={extra}")
    digest = hashlib.sha256()
    for name in sorted(expected):
        tensor = parameters[name]
        if not isinstance(tensor, Tensor):
            raise TypeError(f"initialization {name} must be a tensor")
        if tuple(tensor.shape) != expected[name]:
            raise ValueError(
                f"initialization {name} shape {tuple(tensor.shape)} != {expected[name]}"
            )
        if tensor.dtype is not torch.float32:
            raise TypeError(f"initialization {name} must be float32")
        value = tensor.detach().contiguous().cpu()
        if not bool(torch.isfinite(value).all().item()):
            raise ValueError(f"initialization {name} contains a nonfinite value")
        name_bytes = name.encode("utf-8")
        digest.update(len(name_bytes).to_bytes(4, "little"))
        digest.update(name_bytes)
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(value.view(torch.uint8).numpy().tobytes(order="C"))
    return digest.hexdigest()


def audit_literal_comparator(
    *,
    phy_initialization: Mapping[str, Tensor],
    edge_initialization: Mapping[str, Tensor],
    phy_contract: ArmContract | None = None,
    edge_contract: ArmContract | None = None,
) -> ComparatorAudit:
    """Fail closed unless projection box is the sole algorithmic difference."""

    phy = phy_contract if phy_contract is not None else phy_trust_contract()
    edge = edge_contract if edge_contract is not None else edge_flex_contract()
    if phy.arm_name != "PHY-TRUST" or edge.arm_name != "EDGE-FLEX":
        raise ValueError("arm identities must be PHY-TRUST and EDGE-FLEX")
    if phy.projection_box != (-0.15, 0.15):
        raise ValueError("PHY-TRUST projection must be exactly [-0.15,+0.15]")
    if edge.projection_box != (-1.50, 1.50):
        raise ValueError("EDGE-FLEX projection must be exactly [-1.50,+1.50]")

    phy_common = asdict(replace(phy, arm_name="COMMON", projection_box=(0.0, 0.0)))
    edge_common = asdict(replace(edge, arm_name="COMMON", projection_box=(0.0, 0.0)))
    if phy_common != edge_common:
        differences = sorted(
            key for key in phy_common if phy_common[key] != edge_common.get(key)
        )
        raise ValueError(f"arm contract differs outside projection box: {differences}")

    phy_init_digest = parameter_initialization_digest(phy_initialization)
    edge_init_digest = parameter_initialization_digest(edge_initialization)
    if phy_init_digest != edge_init_digest:
        raise ValueError("arm initializations are not bitwise identical")

    expected_schema = {**ACTOR_PARAMETER_SHAPES, **CRITIC_PARAMETER_SHAPES}
    schema_digest = _json_digest(
        {name: list(shape) for name, shape in sorted(expected_schema.items())}
    )
    common_digest = _json_digest(phy_common)
    nested = (
        edge.projection_box[0] <= phy.projection_box[0]
        and phy.projection_box[1] <= edge.projection_box[1]
    )
    strict_witness = 0.60
    strict = (
        edge.projection_box[0] <= strict_witness <= edge.projection_box[1]
        and not (phy.projection_box[0] <= strict_witness <= phy.projection_box[1])
    )
    if not nested or not strict:
        raise ValueError("projection boxes do not establish strict literal containment")

    return ComparatorAudit(
        passed=True,
        initialization_digest=phy_init_digest,
        parameter_schema_digest=schema_digest,
        common_contract_digest=common_digest,
        only_algorithmic_difference="projection_box",
        phy_projection_box=phy.projection_box,
        edge_projection_box=edge.projection_box,
        literal_containment=True,
        strict_capacity_witness_beta=strict_witness,
        identical_information=True,
        identical_parameters_and_initialization=True,
        identical_selector_opportunity=True,
        identical_branch_opportunity=True,
        identical_optimizer_and_checkpoint=True,
    )


def comparator_contract_audit() -> dict[str, object]:
    """Return the deterministic contract portion without parameter values."""

    phy = phy_trust_contract()
    edge = edge_flex_contract()
    common_phy = asdict(replace(phy, arm_name="COMMON", projection_box=(0.0, 0.0)))
    common_edge = asdict(replace(edge, arm_name="COMMON", projection_box=(0.0, 0.0)))
    return {
        "common_contract_equal": common_phy == common_edge,
        "only_algorithmic_difference": "projection_box",
        "phy_projection_box": phy.projection_box,
        "edge_projection_box": edge.projection_box,
        "literal_containment": (
            edge.projection_box[0] <= phy.projection_box[0]
            and phy.projection_box[1] <= edge.projection_box[1]
        ),
        "strict_capacity_witness_beta": 0.60,
        "identical_information": True,
        "identical_parameter_schema": True,
        "identical_selector_and_branch_opportunity": True,
        "identical_optimizer_backward_and_checkpoint_schedule": True,
        "factual_episodes_per_update": phy.episodes_per_update,
        "legal_q_entries_by_role": phy.legal_q_entries_by_role,
        "alternative_branches_by_role": phy.alternative_branches_by_role,
        "only_evaluable_checkpoint": phy.evaluable_checkpoints,
    }


def _json_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
