"""Preserve complete paired rollouts before any learning consumes their credit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from ..frozen_mean_gate_b08.study import file_identity


def save_pair(path: Path, pair: dict[str, Any]) -> dict[str, Any]:
    """Write all recorded branch tensors, not just the chosen credit difference.

    The caller records world/coin addresses and the behavior-policy digest in
    its JSONL row. This file preserves exact input tensors for the gate update,
    all rewards/commands and all agents' predecision contexts for prefix review.
    No pickle, object arrays, forward calls, optimization or implicit overwrite.
    """
    path = Path(path)
    if pair["mode"] != "paired":
        raise ValueError("B10 raw artifacts require actual KEEP/END pairs")
    path.parent.mkdir(parents=True, exist_ok=True)
    left, right = pair["episodes"]
    arrays = {name: torch.stack((left[name], right[name])).numpy() for name in left}
    arrays.update(
        focal_tick=np.asarray(pair["case"].tick, dtype=np.int64),
        focal_agent=np.asarray(pair["case"].agent, dtype=np.int64),
        focal_eligible=np.asarray(pair["eligible"], dtype=bool),
        suffix_returns=pair["suffix_returns"].numpy(),
        common_uniforms=pair["common_uniforms"].numpy(),
        focal_uniforms=pair["focal_uniforms"].numpy(),
    )
    # Exclusive creation preserves partial evidence after a write failure.
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    return file_identity(path)


def inspect_pair(path: Path) -> dict[str, Any]:
    """Reconstruct a persisted pair's credit independently with NumPy FP64.

    Summation may differ from Torch by ordinary FP64 reduction order. The
    absolute tolerance is 1e-13 in normalized-return units; prefix equality and
    command/eligibility identities stay exact. This does no policy evaluation.
    """
    with np.load(path, allow_pickle=False) as stored:
        arrays = {name: stored[name] for name in stored.files}
    reward = arrays["reward"]
    if reward.ndim != 2 or reward.shape[0] != 2 or reward.dtype != np.float64:
        raise ValueError("pair rewards must be two complete FP64 sequences")
    horizon = reward.shape[1]
    tick, agent = int(arrays["focal_tick"]), int(arrays["focal_agent"])
    if not (1 <= tick < horizon and 0 <= agent < 5):
        raise ValueError("invalid persisted focal coordinate")
    for name, tail in (("context", (5, 175)), ("critic", (136,)),
                       ("logits", (5,)), ("value", ()),
                       ("eligible", (5,)), ("keep", (5,)), ("commands", (5, 3))):
        if arrays[name].shape != (2, horizon) + tail:
            raise ValueError(f"invalid persisted {name} shape")
        length = tick if name in ("keep", "commands") else tick + 1
        if not np.array_equal(arrays[name][0, :length], arrays[name][1, :length]):
            raise ValueError(f"persisted prefix mismatch in {name}")
    if not np.array_equal(reward[0, :tick], reward[1, :tick]):
        raise ValueError("persisted prefix mismatch in reward")
    if any(not np.isfinite(value).all() for value in arrays.values()):
        raise ValueError("persisted pair contains nonfinite data")
    eligible, keep = arrays["eligible"], arrays["keep"]
    if eligible.dtype != bool or keep.dtype != bool:
        raise ValueError("persisted masks must be boolean")
    if eligible[:, 0].any() or (keep & ~eligible).any():
        raise ValueError("persisted pair executed an illegal KEEP")
    if not np.array_equal(eligible[:, 1:], ~keep[:, :-1]):
        raise ValueError("persisted pair lost KEEP's forced-fresh successor")
    active = bool(eligible[0, tick, agent])
    if active != bool(arrays["focal_eligible"]):
        raise ValueError("persisted focal eligibility disagrees with the trajectory")
    if keep[:, tick, agent].tolist() != ([True, False] if active else [False, False]):
        raise ValueError("persisted branch identities disagree with eligibility")
    if not active and any(not np.array_equal(arrays[name][0], arrays[name][1]) for name in
                          ("reward", "context", "critic", "logits", "value", "eligible", "keep", "commands")):
        raise ValueError("persisted inactive pair diverged")
    previous = arrays["context"][..., 104:107]
    fresh = arrays["context"][..., 107:110]
    if not np.array_equal(arrays["commands"], np.where(keep[..., None], previous, fresh)):
        raise ValueError("persisted command is inconsistent with KEEP/END")
    suffix = reward[:, tick:].sum(axis=1, dtype=np.float64) / horizon
    if arrays["suffix_returns"].shape != (2,) or not np.allclose(
            suffix, arrays["suffix_returns"], rtol=0, atol=1e-13):
        raise ValueError("persisted suffix credit disagrees with raw rewards")
    return {"horizon": horizon, "tick": tick, "agent": agent, "eligible": active,
            "suffix_returns": suffix.tolist(), "delta": float(suffix[0] - suffix[1]),
            "branch_J": (reward.sum(axis=1, dtype=np.float64) / horizon).tolist(),
            "team_steps": int(reward.size)}
