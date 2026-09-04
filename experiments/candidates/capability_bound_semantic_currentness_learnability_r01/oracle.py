"""Deterministic sparse RAW competence witness in the common dense shapes.

The compiler is never used to initialize or tune a learned arm.  It is a static
active-parameter witness that the common RAW representation can express the
frozen CBSC decision rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import torch

from .codecs import CodecArm
from .model import DenseLearner


BYTE_OFFSETS: Final = {
    "physical": 0,
    "owner_predecessor": 8,
    "owner_current": 16,
    "body_epoch": 24,
    "current_epoch": 32,
    "association": 40,
    "execution": 48,
    "address": 56,
    "source": 64,
    "carrier_nonce": 72,
    "body_nonce": 80,
    "presentation_slot": 88,
    "public_phase": 96,
}
FLAG_BITS: Final = {
    "need_active": 104,
    "gated": 105,
    "neutral": 106,
    "content": 107,
    "need": 108,
}


@dataclass(frozen=True)
class _RecoveredByte:
    bits: tuple[tuple[int, ...], ...]


def _clear(model: DenseLearner) -> None:
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.zero_()


def compile_raw_oracle() -> DenseLearner:
    """Compile the exact equality/AND decision circuit into the common MLP."""

    with torch.random.fork_rng(devices=[], enabled=True):
        model = DenseLearner()
        _clear(model)
    l1, l2, l3, l4, output = model.layers

    # L1 reverses the RAW (odd target ^= preceding even source) shears for
    # oracle-relevant bytes.  An odd original bit is abs(encoded odd-even),
    # represented by two ReLUs; an even source bit and flags are carried.
    recovered: dict[str, _RecoveredByte] = {}
    inverse_targets: list[tuple[int, tuple[int, ...]]] = []
    cursor = 0
    with torch.no_grad():
        for name, offset in BYTE_OFFSETS.items():
            bit_units: list[tuple[int, ...]] = []
            bit_count = 2 if name == "public_phase" else 8
            for bit in range(bit_count):
                index = offset + bit
                if bit % 2 == 0:
                    l1.weight[cursor, index] = 1.0
                    bit_units.append((cursor,))
                    cursor += 1
                else:
                    source = index - 1
                    l1.weight[cursor, index] = 1.0
                    l1.weight[cursor, source] = -1.0
                    positive = cursor
                    cursor += 1
                    l1.weight[cursor, source] = 1.0
                    l1.weight[cursor, index] = -1.0
                    negative = cursor
                    cursor += 1
                    bit_units.append((positive, negative))
                    inverse_targets.append((index, (positive, negative)))
            recovered[name] = _RecoveredByte(tuple(bit_units))

        flag_l1: dict[str, int] = {}
        for name, index in FLAG_BITS.items():
            l1.weight[cursor, index] = 1.0
            flag_l1[name] = cursor
            cursor += 1
    if cursor != 152 or len(inverse_targets) != 49 or cursor > l1.out_features:
        raise RuntimeError("CBSC-LR01 RAW oracle L1 routing changed")
    model._raw_inverse_target_units = tuple(inverse_targets)  # type: ignore[attr-defined]

    comparisons = (
        ("owner", "owner_predecessor", "owner_current"),
        ("epoch", "body_epoch", "current_epoch"),
        ("association", "association", "physical"),
        ("execution", "execution", "physical"),
        ("address", "address", "physical"),
        ("source", "source", "physical"),
    )
    mismatch_units: dict[str, list[int]] = {}
    cursor = 0
    with torch.no_grad():
        for equality, left, right in comparisons:
            mismatch_units[equality] = []
            for bit in range(8):
                left_units = recovered[left].bits[bit]
                right_units = recovered[right].bits[bit]
                for sign in (1.0, -1.0):
                    for unit in left_units:
                        l2.weight[cursor, unit] += sign
                    for unit in right_units:
                        l2.weight[cursor, unit] -= sign
                    mismatch_units[equality].append(cursor)
                    cursor += 1
        mismatch_units["content"] = []
        for sign in (1.0, -1.0):
            l2.weight[cursor, flag_l1["content"]] = sign
            l2.weight[cursor, flag_l1["need"]] = -sign
            mismatch_units["content"].append(cursor)
            cursor += 1
        carried_l2: dict[str, int] = {}
        for name in ("need_active", "gated", "neutral"):
            l2.weight[cursor, flag_l1[name]] = 1.0
            carried_l2[name] = cursor
            cursor += 1
    if cursor != 101 or cursor > l2.out_features:
        raise RuntimeError("CBSC-LR01 RAW oracle L2 routing changed")

    equality_l3: dict[str, int] = {}
    cursor = 0
    with torch.no_grad():
        for name in ("owner", "epoch", "association", "execution", "address", "source", "content"):
            l3.bias[cursor] = 1.0
            for unit in mismatch_units[name]:
                l3.weight[cursor, unit] = -1.0
            equality_l3[name] = cursor
            cursor += 1
        carried_l3: dict[str, int] = {}
        for name in ("need_active", "gated", "neutral"):
            l3.weight[cursor, carried_l2[name]] = 1.0
            carried_l3[name] = cursor
            cursor += 1
    if cursor != 10 or cursor > l3.out_features:
        raise RuntimeError("CBSC-LR01 RAW oracle L3 routing changed")

    # The execution equality is deliberately computed and audited by the
    # compiler but does not enter the registered serve predicates.
    with torch.no_grad():
        # execution equality is redundant on legal OPEN contexts, but routing
        # it keeps every compiled equality on an output-connected path.
        # serve_open = AND(N,!neutral,!G,epoch,execution,address,source,content)
        l4.bias[0] = -5.0
        l4.weight[0, carried_l3["need_active"]] = 1.0
        l4.weight[0, carried_l3["neutral"]] = -1.0
        l4.weight[0, carried_l3["gated"]] = -1.0
        for name in ("epoch", "execution", "address", "source", "content"):
            l4.weight[0, equality_l3[name]] = 1.0

        # serve_gated includes the likewise redundant-on-legal-support
        # execution equality so the capacity witness contains no dead clause.
        l4.bias[1] = -8.0
        l4.weight[1, carried_l3["need_active"]] = 1.0
        l4.weight[1, carried_l3["neutral"]] = -1.0
        l4.weight[1, carried_l3["gated"]] = 1.0
        for name in ("owner", "association", "epoch", "execution", "address", "source", "content"):
            l4.weight[1, equality_l3[name]] = 1.0

        # fallback = 1-N; carry N for REFRESH=N-serve_open-serve_gated.
        l4.bias[2] = 1.0
        l4.weight[2, carried_l3["need_active"]] = -1.0
        l4.weight[3, carried_l3["need_active"]] = 1.0

        # Output order is SERVE, REFRESH, SAFE_FALLBACK.
        output.weight[0, 0] = 1.0
        output.weight[0, 1] = 1.0
        output.weight[1, 3] = 1.0
        output.weight[1, 0] = -1.0
        output.weight[1, 1] = -1.0
        output.weight[2, 2] = 1.0

    model.requires_grad_(False)
    return model


def raw_oracle_action(encoded_raw_bits: torch.Tensor) -> torch.Tensor:
    """Return one-hot action witnesses; this never participates in learning."""

    model = compile_raw_oracle()
    with torch.no_grad():
        return model(encoded_raw_bits.to(dtype=torch.float32))


def assert_static_raw_oracle(outputs: torch.Tensor) -> None:
    if outputs.ndim != 2 or outputs.shape[1] != 3:
        raise ValueError("RAW oracle outputs must have shape [contexts,3]")
    if not torch.isfinite(outputs).all():
        raise ValueError("RAW oracle outputs must be finite")
    if not torch.equal(outputs, torch.nn.functional.one_hot(outputs.argmax(dim=1), 3).to(torch.float32)):
        raise ValueError("RAW oracle must be exactly one-hot with a unique argmax")


def raw_inverted_shear_targets(model: DenseLearner, encoded_raw_bits: torch.Tensor) -> torch.Tensor:
    """Expose the 49 compiled L1 inverse targets for structural verification."""

    mapping = getattr(model, "_raw_inverse_target_units", None)
    if mapping is None or len(mapping) != 49:
        raise ValueError("model is not a compiled CBSC-LR01 RAW oracle")
    with torch.no_grad():
        layer1 = torch.relu(model.layers[0](encoded_raw_bits.to(torch.float32)))
        return torch.stack(
            [sum((layer1[:, unit] for unit in units), torch.zeros_like(layer1[:, 0])) for _target, units in mapping],
            dim=1,
        )


__all__ = [
    "assert_static_raw_oracle", "compile_raw_oracle", "raw_inverted_shear_targets",
    "raw_oracle_action",
]
