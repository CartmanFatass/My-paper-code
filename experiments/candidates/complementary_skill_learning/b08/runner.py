"""Fixed B08 address recurrence over the unchanged B07 E/M/U engine."""
from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
import traceback
from typing import Any, Mapping

import torch

from experiments.candidates.complementary_skill_learning.b07 import runner as b07


OBJECT = "complementary_skill_b08"
FIXED_SEED = 260924041
DEFAULT_SPEC = replace(
    b07.DEFAULT_SPEC,
    init_seed=260924041,
    head_seed=260924042,
    train_rng_seed=260924043,
    aux_seed=260924044,
    low_action_seed=260924045,
    high_collection_seed=260924046,
    high_update_seed=260924047,
    train_world_base=2400000,
)
PROTOCOL = b07.ExpectedProtocol(
    protocol_id=OBJECT,
    default_spec=DEFAULT_SPEC,
    source_module=__name__,
)
ENGINE_RUN_FIT = b07.run_fit

S_SEEDS = {f"S{i}": 260924101 + i for i in range(4)}
R_SEEDS = {f"R{i}": 262625201 + i for i in range(4)}
NON_LABEL_SEED = 260924105
EVAL_WORLD_BASE = 1700200

_FIXED_ADDRESSES = {
    name: int(getattr(DEFAULT_SPEC, name))
    for name in (
        "init_seed",
        "head_seed",
        "train_rng_seed",
        "aux_seed",
        "low_action_seed",
        "high_collection_seed",
        "high_update_seed",
        "train_world_base",
        "eval_world_base",
    )
}


def _validate_before_work(spec: b07.Spec) -> None:
    """Refuse B08 production or evaluation-address drift before engine effects."""

    addresses = {name: int(getattr(spec, name)) for name in _FIXED_ADDRESSES}
    if addresses != _FIXED_ADDRESSES:
        raise ValueError(f"B08 fixed RNG/world addresses differ: {addresses}")
    if not spec.small_model and spec != DEFAULT_SPEC:
        raise ValueError("B08 production Spec differs from the fixed protocol")
    if spec.n_agents != 6 or spec.k != 10 or spec.horizon % spec.k:
        raise ValueError("B08 requires six agents and complete k10 renewals")
    if b07.S_SEEDS != S_SEEDS or b07.R_SEEDS != R_SEEDS:
        raise ValueError("B08 inherited evaluation label streams differ")
    if b07.NON_LABEL_SEED != NON_LABEL_SEED:
        raise ValueError("B08 inherited non-label evaluation seed differs")
    if spec.eval_world_base != EVAL_WORLD_BASE:
        raise ValueError("B08 inherited evaluation worlds differ")


def _expected_counts(spec: b07.Spec, arm: str) -> dict[str, int]:
    panel_count = 10 if arm in {"E", "M"} else 5
    s_panel_count = 5 if arm in {"E", "M"} else 0
    return {
        "training_transitions": spec.lanes * spec.horizon * spec.rollouts,
        "native_updates": spec.rollouts,
        "evaluation_transitions": panel_count * spec.eval_lanes * spec.horizon,
        "evaluation_episodes": panel_count * spec.eval_lanes,
        "S_transitions": s_panel_count * spec.eval_lanes * spec.horizon,
        "R_transitions": (panel_count - s_panel_count) * spec.eval_lanes * spec.horizon,
    }


def _validate_completed_adapter(
    summary: Mapping[str, Any], spec: b07.Spec, arm: str, launch_sha: str
) -> None:
    if summary.get("status") != "complete":
        raise ValueError("B08 reused engine did not return a complete fit")
    if summary.get("object_id") != b07.OBJECT:
        raise ValueError("B08 lost the reused B07 engine object identity")
    if summary.get("arm") != arm or summary.get("spec") != asdict(spec):
        raise ValueError("B08 output does not carry its actual arm and Spec")
    protocol = summary.get("adapter_protocol", {})
    if protocol != {
        "protocol_id": OBJECT,
        "source_module": __name__,
        "launch_sha": launch_sha,
        "spec": asdict(spec),
        "reused_engine": {
            "object_id": b07.OBJECT,
            "module": b07.__name__,
            "callable": f"{b07.run_fit.__module__}.{b07.run_fit.__qualname__}",
        },
    }:
        raise ValueError("B08 adapter protocol or reused-engine identity differs")
    counts = summary.get("counts", {})
    for name, value in _expected_counts(spec, arm).items():
        if counts.get(name) != value:
            raise ValueError(f"B08 {name} differs from the fixed protocol")
    intervention = summary.get("intervention", {})
    expected = {
        "E": (0.0, False),
        "M": (0.07, False),
        "U": (0.07, True),
    }[arm]
    if (
        intervention.get("lambda_h"),
        intervention.get("disable_high_level_training"),
    ) != expected:
        raise ValueError("B08 high-level intervention differs from the fixed protocol")
    if intervention.get("lambda_l") != 0.05:
        raise ValueError("B08 low-level entropy coefficient differs")
    if arm == "M":
        metadata = summary.get("M_final_S_reference", {}).get("metadata", {})
        if (
            metadata.get("adapter_protocol_id") != OBJECT
            or metadata.get("adapter_source_module") != __name__
            or metadata.get("spec") != asdict(spec)
            or metadata.get("source_launch_sha") != launch_sha
        ):
            raise ValueError("B08 M reference is not bound to this protocol and source")
    if arm == "E":
        source = summary.get("reference_binding", {}).get("source", {})
        if source.get("adapter_protocol_id") != OBJECT:
            raise ValueError("B08 E did not consume a B08 M reference")


def validate_reference(
    path: Path | str,
    expected_sha256: str,
    spec: b07.Spec,
    *,
    expected_source_launch_sha: str,
) -> dict[str, Any]:
    _validate_before_work(spec)
    return b07.validate_reference(
        path,
        expected_sha256,
        spec,
        expected_source_launch_sha=expected_source_launch_sha,
        expected_protocol=PROTOCOL,
    )


def run_fit(
    arm: str,
    out: Path | str,
    launch_sha: str,
    *,
    spec: b07.Spec = DEFAULT_SPEC,
    device: str | torch.device = "cuda",
    admission: dict[str, Any] | None = None,
    reference_path: Path | str | None = None,
    reference_sha256: str | None = None,
):
    """Run one B08 arm while retaining B07 as the executable engine identity."""

    arm = str(arm).upper()
    if arm not in b07.ARMS:
        raise ValueError(arm)
    _validate_before_work(spec)
    summary = ENGINE_RUN_FIT(
        arm,
        out,
        launch_sha,
        spec=spec,
        device=device,
        admission=admission,
        reference_path=reference_path,
        reference_sha256=reference_sha256,
        expected_protocol=PROTOCOL,
    )
    try:
        _validate_completed_adapter(summary, spec, arm, launch_sha)
    except BaseException as exc:
        summary["status"] = "failed"
        summary["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "stage": "b08_adapter_completed_contract",
        }
        b07.write_json(
            Path(out) / "summary.json",
            b07._compact_summary(summary, Path(out)),
        )
        raise
    return summary


aggregate_arm = b07.aggregate_arm
aggregate_batch = b07.aggregate_batch
make_config = b07.make_config
make_envs = b07.make_envs
seed_rng = b07.seed_rng
native_digest = b07.native_digest
frozen_digest = b07.frozen_digest
_build_agent = b07._build_agent

__all__ = [
    "DEFAULT_SPEC",
    "ENGINE_RUN_FIT",
    "EVAL_WORLD_BASE",
    "FIXED_SEED",
    "NON_LABEL_SEED",
    "OBJECT",
    "PROTOCOL",
    "R_SEEDS",
    "S_SEEDS",
    "aggregate_arm",
    "aggregate_batch",
    "run_fit",
    "validate_reference",
]
