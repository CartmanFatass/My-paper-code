"""Fixed B06 seed/spec adapter over the unchanged B04 training engine."""
from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
import traceback
from typing import Any

import torch

from experiments.candidates.complementary_skill_learning.b04 import runner as b04


FIXED_SEED = 260923961
DEFAULT_SPEC = replace(
    b04.DEFAULT_SPEC,
    init_seed=260923961,
    head_seed=260923962,
    train_rng_seed=260923963,
    aux_seed=260923964,
    low_action_seed=260923965,
    high_collection_seed=260923966,
    high_update_seed=260923967,
    train_world_base=2200000,
)

_FIXED_ADDRESSES = {
    name: getattr(DEFAULT_SPEC, name)
    for name in (
        "init_seed",
        "head_seed",
        "train_rng_seed",
        "aux_seed",
        "low_action_seed",
        "high_collection_seed",
        "high_update_seed",
        "eval_rng_seed",
        "train_world_base",
        "eval_world_base",
    )
}


def _validate_before_work(spec: b04.Spec) -> None:
    """Refuse drift before B04 creates an output directory or native object."""

    actual_addresses = {name: getattr(spec, name) for name in _FIXED_ADDRESSES}
    if actual_addresses != _FIXED_ADDRESSES:
        raise ValueError(f"B06 fixed RNG/world addresses differ: {actual_addresses}")
    if not spec.small_model and spec != DEFAULT_SPEC:
        raise ValueError("B06 production Spec differs from the fixed protocol")
    if (
        b04._uniform_stream_digest(DEFAULT_SPEC)
        != b04.EXPECTED_UNIFORM_LABEL_STREAM_SHA256
    ):
        raise ValueError("B06 prescribed uniform evaluation stream digest differs")


def _validate_completed_adapter(
    summary: dict[str, Any], spec: b04.Spec, arm: str
) -> None:
    if summary.get("status") != "complete":
        raise ValueError("B06 reused engine did not return a complete fit")
    if summary.get("object_id") != b04.OBJECT:
        raise ValueError("B06 raw output lost the reused B04 engine identity")
    if summary.get("arm") != arm or summary.get("spec") != asdict(spec):
        raise ValueError("B06 raw output does not carry its actual arm and Spec")

    expected_panels = (
        {"initial_own", "initial_uniform", "final_own", "final_uniform"}
        if arm == "M"
        else {"initial_uniform", "final_uniform"}
    )
    panels = summary.get("panels", {})
    if set(panels) != expected_panels:
        raise ValueError("B06 completed arm has the wrong evaluation panel set")

    expected_uniform_digest = b04._uniform_stream_digest(spec)
    for name in ("initial_uniform", "final_uniform"):
        if panels[name].get("selected_label_stream_sha256") != expected_uniform_digest:
            raise ValueError(f"B06 {name} did not use the prescribed uniform factors")
    if not spec.small_model and any(
        not panels[name].get("frozen_b01_uniform_stream_match", False)
        for name in ("initial_uniform", "final_uniform")
    ):
        raise ValueError("B06 production uniform panels lost the frozen stream identity")


def run_fit(
    arm: str,
    out: Path | str,
    launch_sha: str,
    *,
    spec: b04.Spec = DEFAULT_SPEC,
    device: str | torch.device = "cuda",
    admission: dict[str, Any] | None = None,
):
    """Run one admitted B06 arm through B04 and validate adapter-owned identity."""

    arm = str(arm).upper()
    if arm not in {"M", "U"}:
        raise ValueError(arm)
    _validate_before_work(spec)
    summary = b04.run_fit(
        arm,
        out,
        launch_sha,
        spec=spec,
        device=device,
        admission=admission,
    )
    try:
        _validate_completed_adapter(summary, spec, arm)
    except BaseException as exc:
        summary["status"] = "failed"
        summary["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "stage": "b06_adapter_completed_contract",
        }
        b04.write_json(Path(out) / "summary.json", summary)
        raise
    return summary


__all__ = ["DEFAULT_SPEC", "FIXED_SEED", "run_fit"]

