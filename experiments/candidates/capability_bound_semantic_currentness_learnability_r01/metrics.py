"""Exact regret reductions, toggle gates, and CBSC-LR01 estimands."""

from __future__ import annotations

from fractions import Fraction
from typing import Final, Mapping, Sequence

from .codecs import CodecArm
from .host import Cell, Context
from .training import BlockTrainingResult, Evaluation


AUC_WEIGHTS: Final = (1.0 / 16.0, 1.0 / 8.0, 3.0 / 16.0, 3.0 / 8.0, 1.0 / 4.0)

_TOGGLE_CELL_PAIRS: Final = (
    ("neutral_active", 3, 5),
    ("persist_refresh", 3, 15),
    ("correct_swapped", 3, 4),
    ("open_gated", 6, 9),
    ("owner_live_broken", 3, 27),
    ("authentic_reassociated", 3, 9),
)


def normalized_auc(curve: Sequence[float]) -> float:
    if len(curve) != 5:
        raise ValueError("CBSC-LR01 AUC requires checkpoints 0,8,16,32,64")
    return float(sum(weight * float(value) for weight, value in zip(AUC_WEIGHTS, curve)))


def block_auc(result: BlockTrainingResult, surface: str = "E") -> float:
    if tuple(item.update for item in result.checkpoints) != (0, 8, 16, 32, 64):
        raise ValueError("main block lacks the exact checkpoint ladder")
    attribute = {"E": "mean_regret", "GATED": "gated_regret", "OPEN": "open_regret"}.get(surface)
    if attribute is None:
        raise ValueError("unknown regret surface")
    return normalized_auc([getattr(item, attribute) for item in result.checkpoints])


def paired_estimands(results: Mapping[CodecArm, BlockTrainingResult]) -> tuple[float, float, float]:
    if set(results) != set(CodecArm):
        raise ValueError("paired estimands require STRUCT, SHAM, and RAW")
    struct = results[CodecArm.STRUCT]
    sham = results[CodecArm.SHAM]
    raw = results[CodecArm.RAW]
    d_sr = block_auc(raw, "E") - block_auc(struct, "E")
    d_ss = block_auc(sham, "E") - block_auc(struct, "E")
    psi = (
        block_auc(sham, "GATED") - block_auc(struct, "GATED")
        - block_auc(sham, "OPEN") + block_auc(struct, "OPEN")
    )
    return d_sr, d_ss, psi


def competence_passes(result: BlockTrainingResult) -> bool:
    if result.purpose.value != "COMPETENCE" or result.arm is not CodecArm.RAW:
        return False
    final = result.checkpoints[-1]
    return (
        result.updates == 512
        and result.finite_losses
        and final.finite
        and final.state_unchanged
        and all(final.strict)
        and all(final.correct)
        and all(regret == 0 for regret in final.regrets)
    )


def toggle_counts(final: Evaluation, contexts: Sequence[Context]) -> dict[str, tuple[int, int]]:
    if len(contexts) != 768 or len(final.correct) != 768:
        raise ValueError("toggle counts require the complete heldout census")
    result: dict[str, tuple[int, int]] = {}
    for name, left_cell, right_cell in _TOGGLE_CELL_PAIRS:
        counts = []
        for cell in (left_cell, right_cell):
            selected = [
                correct for row, correct in zip(contexts, final.correct) if row.address.cell == cell
            ]
            if len(selected) != 16:
                raise RuntimeError("toggle cell does not contain exactly 16 EVAL slots")
            counts.append(sum(selected))
        result[name] = (counts[0], counts[1])
    return result


def struct_endpoint_gate(result: BlockTrainingResult, contexts: Sequence[Context]) -> bool:
    if result.arm is not CodecArm.STRUCT or tuple(item.update for item in result.checkpoints) != (0, 8, 16, 32, 64):
        return False
    initial, final = result.checkpoints[0], result.checkpoints[-1]
    return (
        final.finite
        and final.state_unchanged
        and final.mean_regret < initial.mean_regret
        and all(count >= 15 for pair in toggle_counts(final, contexts).values() for count in pair)
    )


__all__ = [
    "AUC_WEIGHTS", "block_auc", "competence_passes", "normalized_auc", "paired_estimands",
    "struct_endpoint_gate", "toggle_counts",
]
