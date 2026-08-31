"""Create-only atomic FCEOV artifacts with direct structural resume equality."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
import json
import os
import pickle
import platform
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

import torch
from torch import Tensor, nn

from .analysis import PanelAnalysis, analyze_complete_panel
from .contracts import (
    CHECKPOINT_UPDATE, Disposition, FAILURE_LABELS, FOUNDATION_UPDATES, FoundationGate, GRAPHS,
    PANEL_WIDTH, RESOURCE_MAXIMA, PanelCell, TerminalFact,
)
from .training import ExactAdamW, OptimizerSnapshot, TrainingContractError
from .foundation import CompetenceRecord, FoundationActorCritic, analyze_competence
from .rng import AddressRNG


CHECKPOINT_SCHEMA = "SCDMP_FCEOV_CHECKPOINT_V2"
FOUNDATION_GATE_SCHEMA = "SCDMP_FCEOV_FOUNDATION_GATE_V2"
PANEL_SCHEMA = "SCDMP_FCEOV_COMPLETE_2X3_RESULT_V1"
TERMINAL_FACT_SCHEMA = "SCDMP_FCEOV_TERMINAL_V2"
RUN_RECORD_SCHEMA = "SCDMP_FCEOV_RUN_RECORD_V1"
RESUME_WITNESS_SCHEMA = "SCDMP_FCEOV_RESUME_WITNESS_V1"
FINAL_BUNDLE_SCHEMA = "SCDMP_FCEOV_FINAL_BUNDLE_V1"


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
    model: nn.Module, optimizer: ExactAdamW, *, completed_updates: int, rng_master: bytes
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
    value: dict[str, object] = {
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
    if not isinstance(rng_master, bytes) or len(rng_master) != 32:
        raise ArtifactContractError("production checkpoint RNG master differs")
    if completed_updates != CHECKPOINT_UPDATE:
        raise ArtifactContractError("production checkpoint frontier must be update 160")
    value["rng_master"] = rng_master
    return value


def _validate_checkpoint(value: object, model: nn.Module, optimizer: ExactAdamW) -> dict[str, object]:
    _validate_foundation_binding(model, optimizer)
    required_fields = {"schema", "completed_updates", "model_state", "optimizer", "rng_master"}
    if not isinstance(value, dict) or set(value) != required_fields:
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
    master = value["rng_master"]
    if not isinstance(master, bytes) or len(master) != 32 or completed != CHECKPOINT_UPDATE:
        raise ArtifactContractError("production checkpoint master/frontier differs")
    return value


def write_checkpoint(
    path: str | Path,
    model: nn.Module,
    optimizer: ExactAdamW,
    *,
    completed_updates: int,
    rng_master: bytes,
) -> None:
    stream = BytesIO()
    torch.save(make_checkpoint(model, optimizer, completed_updates=completed_updates, rng_master=rng_master), stream)
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


def write_rng_master(path: str | Path, master: bytes) -> None:
    if not isinstance(master, bytes) or len(master) != 32:
        raise ArtifactContractError("run RNG master must contain exactly 32 bytes")
    _atomic_create(Path(path), master)


def load_rng_master(path: str | Path) -> bytes:
    try:
        value = Path(path).read_bytes()
    except OSError as error:
        raise ArtifactContractError("run RNG master cannot be loaded") from error
    if len(value) != 32:
        raise ArtifactContractError("persisted run RNG master differs")
    return value


@dataclass(frozen=True, slots=True)
class ResumeWitness:
    schema: str
    checkpoint_update: int
    optimizer_step: int
    model_tensors_equal: bool
    optimizer_tensors_equal: bool
    counters_equal: bool
    addressed_inputs_equal: bool
    continuation_stage: str
    probe_initial_state: tuple[float, float, float]
    probe_disturbance: tuple[float, float, float]


def observe_resume_equality(
    checkpoint: Mapping[str, object],
    uninterrupted_model: FoundationActorCritic,
    uninterrupted_optimizer: ExactAdamW,
    restored_model: FoundationActorCritic,
    restored_optimizer: ExactAdamW,
    *,
    persisted_master: bytes,
) -> ResumeWitness:
    """Directly compare the final-training resume state and competence RNG inputs."""

    from .foundation import competence_disturbance, competence_initial_draws, competence_inventory

    if (
        not isinstance(persisted_master, bytes)
        or len(persisted_master) != 32
        or checkpoint.get("schema") != CHECKPOINT_SCHEMA
        or checkpoint.get("completed_updates") != CHECKPOINT_UPDATE
        or checkpoint.get("rng_master") != persisted_master
        or not direct_resume_equal(checkpoint, restored_model, restored_optimizer)
    ):
        raise ArtifactContractError("checkpoint and persisted RNG masters differ")
    model_equal = all(
        torch.equal(left, right)
        for left, right in zip(uninterrupted_model.state_dict().values(), restored_model.state_dict().values())
    )
    left_state = uninterrupted_optimizer.snapshot()
    right_state = restored_optimizer.snapshot()
    optimizer_equal = (
        left_state.names == right_state.names
        and all(torch.equal(left, right) for left, right in zip(left_state.first, right_state.first))
        and all(torch.equal(left, right) for left, right in zip(left_state.second, right_state.second))
    )
    counters_equal = left_state.step == right_state.step == CHECKPOINT_UPDATE * 12
    mission = competence_inventory()[0]
    left_rng = AddressRNG(persisted_master)
    right_rng = AddressRNG(bytes(persisted_master))
    left_probe = (
        competence_initial_draws(left_rng, mission),
        tuple(competence_disturbance(left_rng, mission, tick=0, component=name) for name in ("eta_v", "eta_y", "eta_omega")),
    )
    right_probe = (
        competence_initial_draws(right_rng, mission),
        tuple(competence_disturbance(right_rng, mission, tick=0, component=name) for name in ("eta_v", "eta_y", "eta_omega")),
    )
    addressed_equal = left_probe == right_probe
    if not (model_equal and optimizer_equal and counters_equal and addressed_equal):
        raise ArtifactContractError("nonzero checkpoint/resume continuation equality failed")
    return ResumeWitness(
        RESUME_WITNESS_SCHEMA, CHECKPOINT_UPDATE, left_state.step, model_equal, optimizer_equal,
        counters_equal, addressed_equal, "COMPETENCE", left_probe[0], left_probe[1],
    )


def write_resume_witness(path: str | Path, witness: ResumeWitness) -> None:
    if not isinstance(witness, ResumeWitness) or witness.schema != RESUME_WITNESS_SCHEMA:
        raise ArtifactContractError("resume witness differs")
    if not all((witness.model_tensors_equal, witness.optimizer_tensors_equal, witness.counters_equal, witness.addressed_inputs_equal)):
        raise ArtifactContractError("resume witness is not a direct equality observation")
    _atomic_json(Path(path), asdict(witness))


@dataclass(frozen=True, slots=True)
class RunRuntime:
    python: str
    torch: str
    device: str = "cpu"
    torch_threads: int = 1
    torch_interop_threads: int = 1
    deterministic_algorithms: bool = True
    native_batch_widths: tuple[tuple[str, int], ...] = (
        ("training", 12), ("competence", 120), ("panel", 144),
    )


@dataclass(frozen=True, slots=True)
class RunRecord:
    schema: str
    phase: str
    checkpoint_update: int
    foundation_updates: int
    episodes_per_update: int
    competence_missions: int
    panel_width: int
    actions: tuple[int, int, int]
    resources: tuple[tuple[str, int], ...]
    runtime: RunRuntime


def build_run_record() -> RunRecord:
    return RunRecord(
        RUN_RECORD_SCHEMA, "FOUNDATION_AND_2X3", CHECKPOINT_UPDATE, FOUNDATION_UPDATES,
        12, 120, PANEL_WIDTH, (0, 10, 12), tuple(RESOURCE_MAXIMA.items()),
        RunRuntime(
            platform.python_version(), str(torch.__version__), "cpu", torch.get_num_threads(),
            torch.get_num_interop_threads(), torch.are_deterministic_algorithms_enabled(),
        ),
    )


def write_run_record(path: str | Path, value: RunRecord) -> None:
    if not isinstance(value, RunRecord) or not isinstance(value.runtime, RunRuntime):
        raise ArtifactContractError("run record must use the exact typed schema")
    if any(
        not isinstance(version, str)
        or not version.strip()
        or any(ord(character) < 32 for character in version)
        for version in (value.runtime.python, value.runtime.torch)
    ):
        raise ArtifactContractError("runtime version strings must be nonempty printable text")
    if (
        value.runtime.device != "cpu"
        or value.runtime.torch_threads != 1
        or value.runtime.torch_interop_threads != 1
        or value.runtime.deterministic_algorithms is not True
    ):
        raise ArtifactContractError("run record numerical runtime controls differ")
    expected = build_run_record()
    if value != expected:
        raise ArtifactContractError("run record fields/runtime differ from the frozen execution contract")
    payload = asdict(value)
    payload["resources"] = dict(value.resources)
    payload["runtime"]["native_batch_widths"] = dict(value.runtime.native_batch_widths)
    _atomic_json(Path(path), payload)


def _competence_evidence(
    gate: FoundationGate, records: Sequence[CompetenceRecord]
) -> tuple[tuple[CompetenceRecord, ...], dict[str, object]]:
    rows = tuple(records)
    try:
        recomputed = analyze_competence(rows)
    except ValueError as error:
        raise ArtifactContractError("competence evidence is invalid") from error
    if not recomputed.complete or recomputed != gate:
        raise ArtifactContractError("foundation gate differs from 120 raw competence records")
    _validate_complete_gate(gate)
    counts: dict[str, object] = {
        "missions": len(rows),
        "safe_by_graph": {
            graph: sum(row.safe_dock for row in rows if row.graph == graph) for graph in GRAPHS
        },
        "pooled_safe": sum(row.safe_dock for row in rows),
        "failures": {
            label: sum(label in row.failures for row in rows) for label in FAILURE_LABELS
        },
    }
    return rows, counts


def write_foundation_gate(
    path: str | Path, gate: FoundationGate, records: Sequence[CompetenceRecord]
) -> None:
    if not gate.complete:
        raise ArtifactContractError("incomplete foundation gate cannot be published")
    rows, counts = _competence_evidence(gate, records)
    _atomic_json(Path(path), {
        "schema": FOUNDATION_GATE_SCHEMA,
        "gate": asdict(gate),
        "competence_records": [asdict(row) for row in rows],
        "counts": counts,
    })


def _write_complete_panel_fixture(path: str | Path, cells: Sequence[PanelCell], analysis: PanelAnalysis) -> None:
    """Historical fixture writer; production passing publication uses one final bundle."""
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


def _test_only_write_final_bundle(
    path: str | Path,
    *,
    competence_records: Sequence[CompetenceRecord],
    panel_cells: Sequence[PanelCell],
) -> TerminalFact:
    """TEST_ONLY atomic historical inference fixture; unavailable to result execution."""

    rows = tuple(competence_records)
    gate = analyze_competence(rows)
    evidence_rows, counts = _competence_evidence(gate, rows)
    if gate.passed is not True:
        raise ArtifactContractError("atomic final bundle requires a passing raw competence gate")
    cells = tuple(panel_cells)
    if len(cells) != PANEL_WIDTH or any(not cell.terminal for cell in cells):
        raise ArtifactContractError("atomic final bundle requires 144 terminal panel cells")
    try:
        panel_analysis = analyze_complete_panel(cells)
    except ValueError as error:
        raise ArtifactContractError("atomic final bundle panel semantics are invalid") from error
    bounds = tuple((bound.name, bound.lower) for bound in panel_analysis.bounds)
    fact = TerminalFact(
        TERMINAL_FACT_SCHEMA, panel_analysis.disposition, gate, True, bounds,
    )
    _atomic_json(Path(path), {
        "schema": FINAL_BUNDLE_SCHEMA,
        "foundation_gate": asdict(gate),
        "competence_records": [asdict(row) for row in evidence_rows],
        "competence_counts": counts,
        "panel_cells": [asdict(cell) for cell in cells],
        "panel_analysis": asdict(panel_analysis),
        "terminal_fact": asdict(fact),
    })
    return fact


def write_terminal_fact(
    path: str | Path,
    fact: TerminalFact,
    *,
    competence_records: Sequence[CompetenceRecord],
    panel_cells: Sequence[PanelCell] | None = None,
) -> None:
    if fact.schema != TERMINAL_FACT_SCHEMA or not fact.foundation_gate.complete:
        raise ArtifactContractError("terminal fact is incomplete or has a legacy schema")
    rows, counts = _competence_evidence(fact.foundation_gate, competence_records)
    if fact.foundation_gate.passed:
        raise ArtifactContractError("passing panel requires atomic final bundle")
    if (
        fact.panel_complete is not False
        or panel_cells is not None
        or fact.adjusted_lower_bounds
        or fact.disposition != Disposition.FOUNDATION_NONPASS.value
    ):
        raise ArtifactContractError("foundation nonpass terminal branch differs")
    value = asdict(fact)
    value["competence_records"] = [asdict(row) for row in rows]
    value["competence_counts"] = counts
    _atomic_json(Path(path), value)


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
    "ArtifactContractError", "CHECKPOINT_SCHEMA", "FINAL_BUNDLE_SCHEMA", "FOUNDATION_GATE_SCHEMA", "PANEL_SCHEMA",
    "RESUME_WITNESS_SCHEMA", "RUN_RECORD_SCHEMA", "ResumeWitness", "RunRecord", "RunRuntime",
    "TERMINAL_FACT_SCHEMA", "direct_resume_equal", "load_checkpoint", "make_checkpoint",
    "build_run_record", "load_rng_master", "observe_resume_equality", "restore_checkpoint", "write_checkpoint",
    "write_foundation_gate", "write_resume_witness", "write_rng_master",
    "write_run_record", "write_terminal_fact",
]
