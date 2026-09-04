"""Matched FP32 full-Q training and adaptation-free heldout evaluation."""

from __future__ import annotations

import hashlib
import copy
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterable, Mapping, Sequence

import torch
import numpy as np

from .addressing import block_id, ordered_batch_ids
from .codecs import CodecArm, encode_bits
from .contract import CHECKPOINTS
from .host import Context, panel
from .initialization import initialized_learner
from .support import Purpose, Split


@dataclass(frozen=True)
class Evaluation:
    update: int
    finite: bool
    choices: tuple[int, ...]
    strict: tuple[bool, ...]
    correct: tuple[bool, ...]
    regrets: tuple[Fraction, ...]
    mean_regret: float
    gated_regret: float
    open_regret: float
    state_unchanged: bool


@dataclass(frozen=True)
class BlockTrainingResult:
    purpose: Purpose
    block: int
    arm: CodecArm
    updates: int
    checkpoints: tuple[Evaluation, ...]
    optimizer_steps: int
    examples: int
    finite_losses: bool
    gradient_clip: float
    work_receipt: Mapping[str, object]


def _direct_state_snapshot(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
) -> tuple[dict[str, torch.Tensor], dict[str, object]]:
    model_state = {
        name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()
    }
    return model_state, copy.deepcopy(optimizer.state_dict())


def _direct_state_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
        return (
            isinstance(left, torch.Tensor)
            and isinstance(right, torch.Tensor)
            and torch.equal(left, right)
        )
    if isinstance(left, dict) or isinstance(right, dict):
        return (
            isinstance(left, dict)
            and isinstance(right, dict)
            and left.keys() == right.keys()
            and all(_direct_state_equal(left[key], right[key]) for key in left)
        )
    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        return (
            type(left) is type(right)
            and len(left) == len(right)
            and all(_direct_state_equal(a, b) for a, b in zip(left, right))
        )
    return type(left) is type(right) and left == right


def _array_digest(*tensors: torch.Tensor) -> str:
    digest = hashlib.sha256()
    for tensor in tensors:
        value = tensor.detach().cpu().contiguous()
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(value.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _model_digest(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes(order="C"))
    return digest.hexdigest()


def _materialize(contexts: Sequence[Context], arm: CodecArm) -> tuple[torch.Tensor, torch.Tensor]:
    inputs = torch.tensor([encode_bits(row.canonical, arm) for row in contexts], dtype=torch.float32)
    targets = torch.tensor(
        [[float(value) for value in row.target_q] for row in contexts],
        dtype=torch.float32,
    )
    return inputs, targets


def _mean(values: Iterable[Fraction]) -> float:
    material = tuple(values)
    if not material:
        raise ValueError("cannot average empty regret support")
    return float(np.asarray([float(value) for value in material], dtype=np.float64).mean(dtype=np.float64))


def evaluate_adaptation_free(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    contexts: Sequence[Context],
    inputs: torch.Tensor,
    *,
    update: int,
) -> Evaluation:
    """Evaluate without altering any model or optimizer tensor/scalar bytes."""

    before = _direct_state_snapshot(model, optimizer)
    was_training = model.training
    model.eval()
    with torch.no_grad():
        predictions = model(inputs)
    model.train(was_training)
    after = _direct_state_snapshot(model, optimizer)
    finite = bool(torch.isfinite(predictions).all().item())
    choices: list[int] = []
    strict: list[bool] = []
    correct: list[bool] = []
    regrets: list[Fraction] = []
    if finite:
        for row, scores in zip(contexts, predictions):
            choice = int(torch.argmax(scores).item())  # first maximum in action order
            maximum = scores[choice]
            unique = int(torch.count_nonzero(scores == maximum).item()) == 1
            best_q = max(row.target_q)
            choices.append(choice)
            strict.append(unique)
            correct.append(choice == row.oracle_action)
            regrets.append(best_q - row.target_q[choice])
    else:
        choices = [-1] * len(contexts)
        strict = [False] * len(contexts)
        correct = [False] * len(contexts)
        regrets = [Fraction(0)] * len(contexts)
    gated = [
        regret for row, regret in zip(contexts, regrets)
        if row.cell.payload.value == "RECEIVER_CORRECT"
        and row.cell.semantic.value == "PERSIST"
        and row.cell.access.value == "BINDING_GATED"
    ]
    opened = [
        regret for row, regret in zip(contexts, regrets)
        if row.cell.payload.value == "RECEIVER_CORRECT"
        and row.cell.semantic.value == "PERSIST"
        and row.cell.access.value == "OPEN"
    ]
    if len(gated) != 64 or len(opened) != 64:
        raise RuntimeError("CBSC-LR01 specificity census changed")
    return Evaluation(
        update=update,
        finite=finite,
        choices=tuple(choices),
        strict=tuple(strict),
        correct=tuple(correct),
        regrets=tuple(regrets),
        mean_regret=_mean(regrets),
        gated_regret=_mean(gated),
        open_regret=_mean(opened),
        state_unchanged=_direct_state_equal(before, after),
    )


def train_block(
    purpose: Purpose,
    block: int,
    arm: CodecArm,
    *,
    passes: int,
    checkpoint_updates: Sequence[int],
    resource_guard: Callable[[], None] | None = None,
) -> BlockTrainingResult:
    """Execute one frozen block; callers cannot alter optimizer or batching."""

    if passes <= 0 or any(type(value) is not int or value < 0 for value in checkpoint_updates):
        raise ValueError("invalid frozen training schedule")
    total_updates = passes * 8
    if tuple(sorted(set(checkpoint_updates))) != tuple(checkpoint_updates) or checkpoint_updates[-1] != total_updates:
        raise ValueError("checkpoints must be increasing, unique, and end at total updates")
    identity = block_id(purpose, block)
    train_contexts = panel(purpose, block, Split.TRAIN)
    eval_contexts = panel(purpose, block, Split.EVAL)
    train_inputs, train_targets = _materialize(train_contexts, arm)
    eval_inputs, eval_targets = _materialize(eval_contexts, arm)
    canonical_train = torch.tensor([row.canonical for row in train_contexts], dtype=torch.float32)
    canonical_eval = torch.tensor([row.canonical for row in eval_contexts], dtype=torch.float32)
    model = initialized_learner(purpose, block)
    initial_parameter_digest = _model_digest(model)
    with torch.no_grad():
        initial_logits_zero = bool(torch.count_nonzero(model(eval_inputs)).item() == 0)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0,
        foreach=False, fused=False,
    )
    evaluations: list[Evaluation] = []
    checkpoint_set = set(checkpoint_updates)
    if 0 in checkpoint_set:
        evaluations.append(evaluate_adaptation_free(model, optimizer, eval_contexts, eval_inputs, update=0))
    finite_losses = True
    update = 0
    order_material: list[int] = []
    for epoch in range(passes):
        for batch_id in ordered_batch_ids(purpose.value, identity, epoch):
            order_material.append(batch_id)
            indices = [cell * 16 + slot for cell in range(48) for slot in (2 * batch_id, 2 * batch_id + 1)]
            predictions = model(train_inputs[indices])
            loss = torch.nn.functional.mse_loss(predictions, train_targets[indices], reduction="mean")
            finite_losses = finite_losses and bool(torch.isfinite(loss).item())
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0, error_if_nonfinite=True)
            optimizer.step()
            update += 1
            if resource_guard is not None:
                resource_guard()
            if update in checkpoint_set:
                evaluations.append(evaluate_adaptation_free(
                    model, optimizer, eval_contexts, eval_inputs, update=update,
                ))
    if update != total_updates or tuple(item.update for item in evaluations) != tuple(checkpoint_updates):
        raise RuntimeError("CBSC-LR01 training/checkpoint schedule changed")
    return BlockTrainingResult(
        purpose=purpose,
        block=block,
        arm=arm,
        updates=update,
        checkpoints=tuple(evaluations),
        optimizer_steps=update,
        examples=update * 96,
        finite_losses=finite_losses,
        gradient_clip=1.0,
        work_receipt={
            "digest_role": "NON_AUTH_INFORMATIONAL_RECEIPT",
            "initial_parameter_digest": initial_parameter_digest,
            "canonical_context_digest": _array_digest(canonical_train, canonical_eval),
            "encoded_context_digest": _array_digest(train_inputs, eval_inputs),
            "target_digest": _array_digest(train_targets, eval_targets),
            "batch_order_digest": hashlib.sha256(bytes(order_material)).hexdigest(),
            "initial_logits_zero": initial_logits_zero,
            "codec_context_materializations": 1_536,
            "codec_xor_operations": 1_536 * 49,
            "active_parameters": 43_395,
            "parameter_bytes": 173_580,
            "dense_macs_per_context": 43_056,
            "training_forward_contexts": update * 96,
            "backward_calls": update,
            "adam_calls": update,
            "scalar_target_exposures": update * 96 * 3,
            "checkpoint_evaluations": len(evaluations),
            "evaluation_contexts": len(evaluations) * 768,
            "workers": 1,
            "threads": 1,
            "dtype": "float32",
        },
    )


def train_main_block(block: int, arm: CodecArm, resource_guard: Callable[[], None] | None = None) -> BlockTrainingResult:
    return train_block(Purpose.MAIN, block, arm, passes=8, checkpoint_updates=CHECKPOINTS, resource_guard=resource_guard)


def train_competence_block(block: int, resource_guard: Callable[[], None] | None = None) -> BlockTrainingResult:
    return train_block(Purpose.COMPETENCE, block, CodecArm.RAW, passes=64, checkpoint_updates=(512,), resource_guard=resource_guard)


__all__ = [
    "BlockTrainingResult", "Evaluation", "evaluate_adaptation_free", "train_block",
    "train_competence_block", "train_main_block",
]
