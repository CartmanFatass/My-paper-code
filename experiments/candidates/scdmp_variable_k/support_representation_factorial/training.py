from __future__ import annotations

from collections.abc import Callable

import numpy as np
import torch

from .config import (
    ADAMW,
    BATCHES_PER_EPOCH,
    LOGICAL_BATCH_ROWS,
    LOGICAL_STEPS,
    PERMUTATION_EPOCHS,
    TRAIN_ROWS,
)
from .corpus import Row, SegmentExamples, segment_examples
from .model import SegmentModel
from .rng import HMACStream


class MinibatchPlan:
    """Continued-substream permutations serving one-based steps 1,...,600."""

    def __init__(self, stream: HMACStream, row_count: int = TRAIN_ROWS) -> None:
        if row_count != TRAIN_ROWS:
            raise ValueError("SRF training support contains exactly 4,096 rows")
        self.permutations: list[np.ndarray] = []
        for _epoch in range(PERMUTATION_EPOCHS):
            values = list(range(row_count))
            stream.shuffle(values)
            self.permutations.append(np.asarray(values, dtype=np.int64))
        self.draw_count = stream.draw_count

    def rows_for_step(self, n: int) -> np.ndarray:
        if not 1 <= n <= LOGICAL_STEPS:
            raise ValueError("optimizer step must be one-based in 1,...,600")
        batch = n - 1
        epoch, batch_index = divmod(batch, BATCHES_PER_EPOCH)
        start = batch_index * LOGICAL_BATCH_ROWS
        return self.permutations[epoch][start:start + LOGICAL_BATCH_ROWS].copy()


class SegmentStore:
    """One deterministic direct-truth materialization selected in whole rows."""

    def __init__(self, rows: tuple[Row, ...]) -> None:
        self.rows = rows
        self.examples = segment_examples(rows, row_equal=False)
        counts = np.asarray(
            [row.k * (row.k + 1) // 2 for row in rows], dtype=np.int64,
        )
        self.offsets = np.concatenate((np.asarray([0], dtype=np.int64), np.cumsum(counts)))

    def logical_batch(self, row_indices: np.ndarray) -> SegmentExamples:
        if len(row_indices) != LOGICAL_BATCH_ROWS \
                or len(set(map(int, row_indices))) != LOGICAL_BATCH_ROWS:
            raise ValueError("logical checkpoint batch needs 256 distinct rows")
        atom_indices: list[np.ndarray] = []
        weights: list[np.ndarray] = []
        for raw in row_indices:
            row = int(raw)
            start, stop = int(self.offsets[row]), int(self.offsets[row + 1])
            atom_indices.append(np.arange(start, stop, dtype=np.int64))
            weights.append(np.full(
                stop - start,
                1.0 / LOGICAL_BATCH_ROWS / (stop - start),
                dtype=np.float64,
            ))
        selected = np.concatenate(atom_indices)
        source = self.examples
        return SegmentExamples(
            source.states[selected], source.actions[selected], source.words[selected],
            source.lengths[selected], source.terminal[selected], source.reward[selected],
            np.concatenate(weights),
        )


class ExactAdamW:
    """Unfused float32 one-based AdamW implementation for the frozen checkpoint law."""

    def __init__(self, model: SegmentModel) -> None:
        self.representation = model.representation
        self.parameters = model.ordered_parameters()
        self.m = [torch.zeros_like(parameter) for parameter in self.parameters]
        self.v = [torch.zeros_like(parameter) for parameter in self.parameters]
        self.step_number = 0

    def zero_grad(self) -> None:
        for parameter in self.parameters:
            parameter.grad = None

    @torch.no_grad()
    def step(self, n: int) -> float:
        if n != self.step_number + 1 or not 1 <= n <= LOGICAL_STEPS:
            raise ValueError("AdamW steps must be consecutive and one-based")
        squared = torch.zeros((), dtype=torch.float32)
        for parameter in self.parameters:
            if parameter.grad is None:
                raise RuntimeError("every trainable parameter must receive a direct-loss gradient")
            squared.add_(torch.sum(parameter.grad.detach().to(torch.float32) ** 2))
        norm = torch.sqrt(squared)
        if not bool(torch.isfinite(norm)):
            raise FloatingPointError("nonfinite complete logical-batch gradient norm")
        norm_value = float(norm.item())
        scale = 1.0 if norm_value == 0.0 else min(1.0, ADAMW.max_grad_norm / norm_value)
        beta1_n = ADAMW.beta1 ** n
        beta2_n = ADAMW.beta2 ** n
        for index, parameter in enumerate(self.parameters):
            gradient = parameter.grad.detach().to(torch.float32) * scale
            self.m[index].mul_(ADAMW.beta1).add_(gradient, alpha=1.0 - ADAMW.beta1)
            self.v[index].mul_(ADAMW.beta2).addcmul_(
                gradient, gradient, value=1.0 - ADAMW.beta2,
            )
            mhat = self.m[index] / (1.0 - beta1_n)
            vhat = self.v[index] / (1.0 - beta2_n)
            parameter.mul_(1.0 - ADAMW.learning_rate * ADAMW.weight_decay)
            parameter.addcdiv_(
                mhat,
                torch.sqrt(vhat).add_(ADAMW.epsilon),
                value=-ADAMW.learning_rate,
            )
        self.step_number = n
        return norm_value

    def state_dict(self) -> dict[str, object]:
        return {
            "representation": self.representation,
            "step_number": self.step_number,
            "m": [value.detach().cpu().clone() for value in self.m],
            "v": [value.detach().cpu().clone() for value in self.v],
        }

    def load_state_dict(self, state: dict[str, object]) -> None:
        if state.get("representation") != self.representation:
            raise RuntimeError("optimizer representation identity mismatch")
        raw_m, raw_v = state.get("m"), state.get("v")
        if not isinstance(raw_m, list) or not isinstance(raw_v, list) \
                or len(raw_m) != len(self.m) or len(raw_v) != len(self.v):
            raise RuntimeError("optimizer frontier shape mismatch")
        self.step_number = int(state["step_number"])
        for target, source in zip(self.m, raw_m):
            target.copy_(source)
        for target, source in zip(self.v, raw_v):
            target.copy_(source)


def direct_loss(
    model: SegmentModel,
    examples: SegmentExamples,
    scale_f: np.ndarray,
    scale_g: np.float32,
    *,
    microbatch_examples: int = 2_048,
) -> float:
    states, actions, words, lengths, true_f, true_g, weights = examples.tensors()
    scale_f_tensor = torch.as_tensor(scale_f, dtype=torch.float32)
    scale_g_tensor = torch.as_tensor(scale_g, dtype=torch.float32)
    total = 0.0
    for start in range(0, len(lengths), microbatch_examples):
        stop = min(start + microbatch_examples, len(lengths))
        predicted_f, predicted_g = model(
            states[start:stop], actions[start:stop], words[start:stop], lengths[start:stop],
        )
        state_error = torch.mean(
            ((predicted_f - true_f[start:stop]) / scale_f_tensor) ** 2, dim=1,
        )
        reward_error = ((predicted_g - true_g[start:stop]) / scale_g_tensor) ** 2
        loss = torch.sum(weights[start:stop] * 0.5 * (state_error + reward_error))
        loss.backward()
        total += float(loss.detach().item())
    return total


def train_checkpoint(
    model: SegmentModel,
    optimizer: ExactAdamW,
    plan: MinibatchPlan,
    store: SegmentStore,
    scale_f: np.ndarray,
    scale_g: np.float32,
    *,
    first_step: int = 1,
    initial_direct_examples: int = 0,
    before_step: Callable[[int], None] | None = None,
    on_step: Callable[[int, SegmentModel, ExactAdamW, float, float, int], None] | None = None,
    microbatch_examples: int = 2_048,
) -> tuple[list[dict[str, float | int]], int]:
    if first_step != optimizer.step_number + 1:
        raise ValueError("frontier optimizer boundary and requested first step disagree")
    trace: list[dict[str, float | int]] = []
    executed = int(initial_direct_examples)
    for n in range(first_step, LOGICAL_STEPS + 1):
        if before_step is not None:
            before_step(n)
        optimizer.zero_grad()
        batch = store.logical_batch(plan.rows_for_step(n))
        loss = direct_loss(
            model, batch, scale_f, scale_g,
            microbatch_examples=microbatch_examples,
        )
        norm = optimizer.step(n)
        executed += len(batch.lengths)
        row: dict[str, float | int] = {
            "n": n,
            "loss": loss,
            "preclip_gradient_norm": norm,
            "direct_model_examples": len(batch.lengths),
        }
        trace.append(row)
        if on_step is not None:
            on_step(n, model, optimizer, loss, norm, executed)
    return trace, executed
