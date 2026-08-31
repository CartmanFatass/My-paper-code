"""Create-only atomic FCEOV artifacts with direct structural resume equality."""

from __future__ import annotations

from dataclasses import asdict
from io import BytesIO
import json
import os
import pickle
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

import torch
from torch import Tensor, nn

from .analysis import CONTRAST_NAMES, PanelAnalysis, analyze_complete_panel
from .contracts import (
    Disposition, FAILURE_LABELS, FoundationGate, GRAPHS, PANEL_WIDTH, PanelCell, TerminalFact,
)
from .training import ExactAdamW, OptimizerSnapshot, TrainingContractError
from .foundation import FoundationActorCritic


CHECKPOINT_SCHEMA = "SCDMP_FCEOV_CHECKPOINT_V1"
FOUNDATION_GATE_SCHEMA = "SCDMP_FCEOV_FOUNDATION_GATE_V1"
PANEL_SCHEMA = "SCDMP_FCEOV_COMPLETE_2X3_RESULT_V1"
TERMINAL_FACT_SCHEMA = "SCDMP_FCEOV_TERMINAL_V1"


class ArtifactContractError(RuntimeError):
    pass


def _atomic_create(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    except FileExistsError as error:
        raise ArtifactContractError("FCEOV artifacts are create-only") from error
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_json(path: Path, value: Mapping[str, object]) -> None:
    try:
        payload = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("artifact is not finite direct JSON") from error
    _atomic_create(path, payload)


def make_checkpoint(
    model: nn.Module, optimizer: ExactAdamW, *, completed_updates: int
) -> dict[str, object]:
    _validate_foundation_binding(model, optimizer)
    if (
        isinstance(completed_updates, bool)
        or not isinstance(completed_updates, int)
        or not 0 <= completed_updates <= 160
    ):
        raise ArtifactContractError("checkpoint update frontier differs")
    if optimizer.step_index != completed_updates * 12:
        raise ArtifactContractError("checkpoint optimizer frontier differs")
    state = optimizer.snapshot()
    return {
        "schema": CHECKPOINT_SCHEMA,
        "completed_updates": completed_updates,
        "model_state": {name: value.detach().clone() for name, value in model.state_dict().items()},
        "optimizer": {
            "step": state.step,
            "names": state.names,
            "first": state.first,
            "second": state.second,
        },
    }


def _validate_checkpoint(value: object, model: nn.Module, optimizer: ExactAdamW) -> dict[str, object]:
    _validate_foundation_binding(model, optimizer)
    if not isinstance(value, dict) or set(value) != {"schema", "completed_updates", "model_state", "optimizer"}:
        raise ArtifactContractError("checkpoint fields differ or legacy schema was supplied")
    if value["schema"] != CHECKPOINT_SCHEMA:
        raise ArtifactContractError("checkpoint schema differs or is legacy")
    completed = value["completed_updates"]
    if isinstance(completed, bool) or not isinstance(completed, int) or not 0 <= completed <= 160:
        raise ArtifactContractError("checkpoint completed-update frontier differs")
    expected = model.state_dict()
    observed = value["model_state"]
    if not isinstance(observed, dict) or set(observed) != set(expected):
        raise ArtifactContractError("checkpoint model tensor names differ")
    for name, reference in expected.items():
        item = observed[name]
        if not isinstance(item, Tensor) or item.dtype != reference.dtype or item.shape != reference.shape or not bool(torch.isfinite(item).all()):
            raise ArtifactContractError(f"checkpoint model tensor differs: {name}")
    model_tensors = tuple(observed[name] for name in expected)
    if len({id(value) for value in model_tensors}) != len(model_tensors):
        raise ArtifactContractError("checkpoint model tensors must be direct nonaliased state")
    row = value["optimizer"]
    required = {"step", "names", "first", "second"}
    if not isinstance(row, dict) or set(row) != required:
        raise ArtifactContractError("checkpoint optimizer structure differs")
    raw_step = row["step"]
    if isinstance(raw_step, bool) or not isinstance(raw_step, int):
        raise ArtifactContractError("checkpoint optimizer step must be an integer")
    try:
        snapshot = OptimizerSnapshot(raw_step, tuple(row["names"]), tuple(row["first"]), tuple(row["second"]))
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("checkpoint optimizer structure differs") from error
    if snapshot.step != completed * 12:
        raise ArtifactContractError("checkpoint optimizer/update frontiers differ")
    try:
        optimizer.validate_snapshot(snapshot)
    except TrainingContractError as error:
        raise ArtifactContractError("checkpoint optimizer state differs") from error
    return value


def write_checkpoint(
    path: str | Path, model: nn.Module, optimizer: ExactAdamW, *, completed_updates: int
) -> None:
    stream = BytesIO()
    torch.save(make_checkpoint(model, optimizer, completed_updates=completed_updates), stream)
    _atomic_create(Path(path), stream.getvalue())


def load_checkpoint(path: str | Path, model: nn.Module, optimizer: ExactAdamW) -> dict[str, object]:
    try:
        value = torch.load(BytesIO(Path(path).read_bytes()), map_location="cpu", weights_only=True)
    except (OSError, RuntimeError, EOFError, pickle.UnpicklingError) as error:
        raise ArtifactContractError("checkpoint cannot be loaded") from error
    return _validate_checkpoint(value, model, optimizer)


@torch.no_grad()
def restore_checkpoint(value: Mapping[str, object], model: nn.Module, optimizer: ExactAdamW) -> None:
    row = _validate_checkpoint(dict(value), model, optimizer)
    state = row["optimizer"]
    assert isinstance(state, dict)
    incoming_optimizer = OptimizerSnapshot(
        int(state["step"]), tuple(state["names"]), tuple(state["first"]), tuple(state["second"])
    )
    before_model = {name: value.detach().clone() for name, value in model.state_dict().items()}
    before_optimizer = optimizer.snapshot()
    try:
        model.load_state_dict(row["model_state"], strict=True)  # type: ignore[arg-type]
        optimizer.restore(incoming_optimizer)
        if not direct_resume_equal(row, model, optimizer):
            raise ArtifactContractError("direct checkpoint resume equality failed")
    except Exception:
        model.load_state_dict(before_model, strict=True)
        optimizer.restore(before_optimizer)
        raise


def direct_resume_equal(value: Mapping[str, object], model: nn.Module, optimizer: ExactAdamW) -> bool:
    observed = value.get("model_state")
    state = value.get("optimizer")
    if not isinstance(observed, Mapping) or not isinstance(state, Mapping):
        return False
    if set(observed) != set(model.state_dict()):
        return False
    if any(not torch.equal(observed[name], current) for name, current in model.state_dict().items()):
        return False
    current = optimizer.snapshot()
    return (
        state.get("step") == current.step
        and tuple(state.get("names", ())) == current.names
        and len(tuple(state.get("first", ()))) == len(current.first)
        and len(tuple(state.get("second", ()))) == len(current.second)
        and all(torch.equal(left, right) for left, right in zip(tuple(state.get("first", ())), current.first))
        and all(torch.equal(left, right) for left, right in zip(tuple(state.get("second", ())), current.second))
    )


def write_foundation_gate(path: str | Path, gate: FoundationGate) -> None:
    if not gate.complete:
        raise ArtifactContractError("incomplete foundation gate cannot be published")
    _validate_complete_gate(gate)
    _atomic_json(Path(path), {"schema": FOUNDATION_GATE_SCHEMA, "gate": asdict(gate)})


def write_complete_panel(path: str | Path, cells: Sequence[PanelCell], analysis: PanelAnalysis) -> None:
    rows = tuple(cells)
    if len(rows) != PANEL_WIDTH or any(not row.terminal for row in rows) or len(analysis.tape_contrasts) != 24:
        raise ArtifactContractError("partial panel cannot be published")
    try:
        recomputed = analyze_complete_panel(rows)
    except ValueError as error:
        raise ArtifactContractError("complete panel semantics are invalid") from error
    if recomputed != analysis:
        raise ArtifactContractError("panel analysis differs from direct recomputation")
    _atomic_json(Path(path), {
        "schema": PANEL_SCHEMA,
        "cells": [asdict(row) for row in rows],
        "analysis": asdict(analysis),
    })


def write_terminal_fact(
    path: str | Path,
    fact: TerminalFact,
    *,
    panel_cells: Sequence[PanelCell] | None = None,
) -> None:
    if fact.schema != TERMINAL_FACT_SCHEMA or not fact.foundation_gate.complete:
        raise ArtifactContractError("terminal fact is incomplete or has a legacy schema")
    _validate_complete_gate(fact.foundation_gate)
    if fact.foundation_gate.passed and fact.panel_complete is not True:
        raise ArtifactContractError("passing foundation requires a complete panel terminal fact")
    if fact.foundation_gate.passed:
        if panel_cells is None:
            raise ArtifactContractError("passing terminal fact requires the same complete panel cells")
        try:
            panel_analysis = analyze_complete_panel(tuple(panel_cells))
        except ValueError as error:
            raise ArtifactContractError("terminal fact panel semantics are invalid") from error
        if tuple(name for name, _ in fact.adjusted_lower_bounds) != CONTRAST_NAMES:
            raise ArtifactContractError("terminal fact must contain the exact four adjusted bounds")
        values = tuple(value for _, value in fact.adjusted_lower_bounds)
        if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not torch.isfinite(torch.tensor(value)) for value in values):
            raise ArtifactContractError("terminal fact adjusted bound is nonfinite")
        expected_bounds = tuple((bound.name, bound.lower) for bound in panel_analysis.bounds)
        if fact.adjusted_lower_bounds != expected_bounds:
            raise ArtifactContractError("terminal fact bounds differ from direct panel analysis")
        if fact.disposition != panel_analysis.disposition:
            raise ArtifactContractError("terminal fact disposition differs from direct panel analysis")
    else:
        if (
            fact.panel_complete is not False
            or panel_cells is not None
            or fact.adjusted_lower_bounds
            or fact.disposition != Disposition.FOUNDATION_NONPASS.value
        ):
            raise ArtifactContractError("foundation nonpass terminal branch differs")
    _atomic_json(Path(path), asdict(fact))


def _validate_complete_gate(gate: FoundationGate) -> None:
    if (
        not isinstance(gate, FoundationGate)
        or gate.complete is not True
        or not isinstance(gate.passed, bool)
    ):
        raise ArtifactContractError("foundation gate flags differ")
    if tuple(name for name, _ in gate.graph_lower_bounds) != GRAPHS:
        raise ArtifactContractError("foundation graph-bound inventory differs")
    if tuple(name for name, _ in gate.failure_upper_bounds) != FAILURE_LABELS:
        raise ArtifactContractError("foundation failure-bound inventory differs")
    values = tuple(value for _, value in gate.graph_lower_bounds) + (gate.pooled_lower_bound,) + tuple(
        value for _, value in gate.failure_upper_bounds
    )
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not bool(torch.isfinite(torch.tensor(value)))
        or not 0.0 <= value <= 1.0
        for value in values
    ):
        raise ArtifactContractError("foundation gate bound is invalid")
    expected = (
        all(value > 0.72 for _, value in gate.graph_lower_bounds)
        and gate.pooled_lower_bound > 0.84
        and all(value < 0.10 for _, value in gate.failure_upper_bounds)
    )
    if gate.passed != expected:
        raise ArtifactContractError("foundation gate pass flag differs from strict bounds")


def _validate_foundation_binding(model: nn.Module, optimizer: ExactAdamW) -> None:
    if not isinstance(model, FoundationActorCritic):
        raise ArtifactContractError("checkpoint requires the isolated FCEOV FoundationActorCritic")
    if sum(value.numel() for value in model.parameters()) != 24_115:
        raise ArtifactContractError("foundation checkpoint parameter schema differs")
    if not optimizer.matches_named_parameters(tuple(model.named_parameters())):
        raise ArtifactContractError("checkpoint optimizer is not bound to this foundation")


__all__ = [
    "ArtifactContractError", "CHECKPOINT_SCHEMA", "FOUNDATION_GATE_SCHEMA", "PANEL_SCHEMA",
    "TERMINAL_FACT_SCHEMA", "direct_resume_equal", "load_checkpoint", "make_checkpoint",
    "restore_checkpoint", "write_checkpoint", "write_complete_panel", "write_foundation_gate",
    "write_terminal_fact",
]
