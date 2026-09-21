"""A bounded gate update for the prepared paired-branch experiment.

The prospective native reference uses B08's FULL factual-data PPO learner.
The focal-only factual surrogate in credit.py is an algebraic test reference,
not a proposed handicapped native comparator.
"""

from __future__ import annotations

from typing import Any, Callable, MutableMapping, Sequence

import torch

from .credit import paired_surrogate


def update_pairs(
    gate: torch.nn.Module,
    optimizer: Any,
    pairs: Sequence[dict[str, Any]],
    *,
    horizon: int,
    check: Callable[[], None],
    counts: MutableMapping[str, int],
) -> list[dict[str, float]]:
    """Four full-batch epochs; caller collects 16 frozen-policy pairs per round.

    Each pair samples one of 5*(H-1) nonreset agent/tick coordinates uniformly.
    Targets are native-J suffixes, so multiply by that coordinate count. There
    is no sample-dependent advantage normalization or borrowed future state.
    Smaller batches are supported for pure correctness fixtures only; the
    prospective declaration controls a result-bearing invocation.
    """
    if type(horizon) is not int or horizon < 2 or not pairs:
        raise ValueError("a nonempty pair batch and horizon >= 2 are required")
    if any(pair["mode"] != "paired" for pair in pairs):
        raise ValueError("this update accepts actual KEEP/END pairs only")
    for pair in pairs:
        pair["case"].validate(horizon)
        expected = [True, False] if pair["eligible"] else [False, False]
        if pair["sampled_keep"].tolist() != expected:
            raise ValueError("branch identities disagree with eligibility")
        if pair["suffix_returns"].shape != (2,) or pair["suffix_returns"].dtype != torch.float64:
            raise ValueError("two FP64 suffix returns are required per pair")
    context = torch.stack([pair["context"] for pair in pairs]).detach()
    agents = torch.tensor([pair["case"].agent for pair in pairs], dtype=torch.int64)
    rows = torch.arange(len(pairs))
    old = torch.stack([pair["old_logits"][pair["case"].agent] for pair in pairs]).detach()
    # Subtract the raw FP64 outcome readings BEFORE casting the learning target.
    delta = torch.stack([pair["suffix_returns"][0] - pair["suffix_returns"][1]
                         for pair in pairs]).to(dtype=torch.float32).detach()
    active = torch.tensor([pair["eligible"] for pair in pairs], dtype=torch.bool)
    multiplier = float(5 * (horizon - 1))
    metrics = []
    for _epoch in range(4):
        check()
        logits = gate(context)[rows, agents]
        loss = -paired_surrogate(logits, old, delta, active, multiplier=multiplier)
        if not bool(torch.isfinite(loss)):
            raise FloatingPointError("nonfinite paired gate loss")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(gate.parameters(), 0.5)
        if not bool(torch.isfinite(norm)):
            raise FloatingPointError("nonfinite paired gate gradient")
        optimizer.step()
        counts["gate_optimizer_steps"] = counts.get("gate_optimizer_steps", 0) + 1
        metrics.append({"loss": float(loss.detach()), "gradient_norm": float(norm)})
        check()
    return metrics
