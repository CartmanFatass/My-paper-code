"""Dedicated twelve-parameter RAW/WHITENED Bellman-complete scorers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .conditioning import ScoreEquivalence, TransformRecord, pair_initial_coefficients, transform_features
from .contract import ARM_IDS, ROOT_BASIS_DIM, TAIL_BASIS_DIM
from .rng import glorot_vector


def _torch():
    import torch
    return torch


def tail_basis(*, belief: float, period: int) -> tuple[float, ...]:
    normalized = period / 9.0
    return (1.0, belief, normalized, belief * normalized, normalized * normalized)


def root_basis(*, action_probe: bool, period: int, cost: float, linked: bool, reliability: float) -> tuple[float, ...]:
    probe = float(action_probe)
    normalized = period / 9.0
    return (1.0, (1.0 - probe) * normalized, (1.0 - probe) * normalized * normalized, probe, probe * cost, probe * float(linked), probe * float(linked) * reliability)


def basis_for_record(record: Any, *, stage: str, period: int, action_probe: bool = False):
    torch = _torch()
    values = tail_basis(belief=float(record.belief_short), period=period) if stage == "tail" else root_basis(action_probe=action_probe, period=period, cost=float(record.total_cost), linked=record.link == "LINKED", reliability=float(record.reliability))
    return torch.tensor(values, dtype=torch.float32)


class BCScorer:
    @staticmethod
    def build(stage: str, arm_id: str, initial_beta, transform: TransformRecord):
        torch = _torch()
        if stage not in {"tail", "root"} or arm_id not in ARM_IDS:
            raise ValueError("invalid scorer identity")
        dim = TAIL_BASIS_DIM if stage == "tail" else ROOT_BASIS_DIM
        if transform.stage != stage or transform.feature_dim != dim:
            raise ValueError("scorer transform stage mismatch")
        if initial_beta.dtype != torch.float32 or initial_beta.ndim != 1 or initial_beta.shape[0] != dim: raise ValueError("fixed-size initial coefficient mismatch")

        class Module(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.beta = torch.nn.Parameter(initial_beta.detach().clone())

            def forward(self, raw_features):
                if raw_features.dtype != torch.float32 or raw_features.ndim != 2 or raw_features.shape[1] != dim:
                    raise ValueError("scorer requires stage-sized FP32 raw features")
                coordinates = raw_features if arm_id == "FT-XF-BC-RAW" else transform_features(transform, raw_features)
                return coordinates @ self.beta

        return Module()


def raw_initialization(stage: str, seed_id: str, fold_id: int):
    torch = _torch()
    if stage not in {"tail", "root"} or fold_id not in (0, 1):
        raise ValueError("invalid initialization identity")
    dim = TAIL_BASIS_DIM if stage == "tail" else ROOT_BASIS_DIM
    return torch.tensor(glorot_vector(dim, seed_id, fold_id, stage), dtype=torch.float32)


def optimizer_for(scorer):
    torch = _torch()
    return torch.optim.AdamW(scorer.parameters(), lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0)


def validate_scorer(scorer, *, stage: str) -> None:
    torch = _torch()
    dim = TAIL_BASIS_DIM if stage == "tail" else ROOT_BASIS_DIM
    parameters = dict(scorer.named_parameters())
    if set(parameters) != {"beta"} or tuple(parameters["beta"].shape) != (dim,):
        raise ValueError("BC scorer trainable state drift")
    if parameters["beta"].dtype != torch.float32 or not torch.isfinite(parameters["beta"]).all().item():
        raise ValueError("BC scorer parameter precision/finiteness drift")


@dataclass(frozen=True)
class ArmBundle:
    root: Any
    tail: Any
    root_optimizer: Any
    tail_optimizer: Any


def initial_beta_for_arm(stage: str, arm_id: str, seed_id: str, fold_id: int, transform: TransformRecord):
    raw = raw_initialization(stage, seed_id, fold_id)
    return raw if arm_id == "FT-XF-BC-RAW" else transform.lower_matrix().T @ raw


def build_arm(arm_id: str, seed_id: str, fold_id: int, *, root_transform: TransformRecord, tail_transform: TransformRecord, root_initial=None, tail_initial=None) -> ArmBundle:
    root_initial = initial_beta_for_arm("root", arm_id, seed_id, fold_id, root_transform) if root_initial is None else root_initial
    tail_initial = initial_beta_for_arm("tail", arm_id, seed_id, fold_id, tail_transform) if tail_initial is None else tail_initial
    root = BCScorer.build("root", arm_id, root_initial, root_transform)
    tail = BCScorer.build("tail", arm_id, tail_initial, tail_transform)
    validate_scorer(root, stage="root"); validate_scorer(tail, stage="tail")
    root_optimizer, tail_optimizer = optimizer_for(root), optimizer_for(tail)
    if root_optimizer.state or tail_optimizer.state:
        raise ValueError("fresh AdamW state must be empty")
    return ArmBundle(root, tail, root_optimizer, tail_optimizer)
