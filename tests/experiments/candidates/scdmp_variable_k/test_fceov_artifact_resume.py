from __future__ import annotations

import copy
from dataclasses import replace
import json

import pytest
import torch

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    analysis,
    artifacts,
    contracts,
    foundation,
    lifecycle,
    training,
)


class MidpointUniforms:
    def initialization_uniforms(self, *, replicate, arm, tensor_name, count):
        return (0.5,) * count


def _model_and_optimizer():
    model = foundation.FoundationActorCritic(MidpointUniforms())
    optimizer = training.ExactAdamW(tuple(model.named_parameters()))
    return model, optimizer


def _gate(*, complete: bool = True, passed: bool = True) -> contracts.FoundationGate:
    graph_bound = 0.9 if passed else 0.72
    return contracts.FoundationGate(
        complete,
        passed,
        (("HR", graph_bound), ("RH", 0.9)) if complete else (),
        0.9 if complete else float("nan"),
        tuple((name, 0.01) for name in contracts.FAILURE_LABELS) if complete else (),
    )


def _complete_cells() -> tuple[contracts.PanelCell, ...]:
    indices = {"COMMON": 0, "A_HR": 10, "A_RH": 12}
    return tuple(
        contracts.PanelCell(tape, graph, action, indices[action], True, True, 182)
        for tape in range(24)
        for graph in ("HR", "RH")
        for action in ("COMMON", "A_HR", "A_RH")
    )


def test_checkpoint_restore_has_direct_tensor_and_optimizer_equality(tmp_path):
    model, optimizer = _model_and_optimizer()
    path = tmp_path / "foundation.checkpoint.pt"
    artifacts.write_checkpoint(path, model, optimizer, completed_updates=0)
    loaded = artifacts.load_checkpoint(path, model, optimizer)
    assert artifacts.direct_resume_equal(loaded, model, optimizer)

    with torch.no_grad():
        for parameter in model.parameters():
            parameter.add_(3.0)
    assert not artifacts.direct_resume_equal(loaded, model, optimizer)

    artifacts.restore_checkpoint(loaded, model, optimizer)
    assert artifacts.direct_resume_equal(loaded, model, optimizer)


def test_registered_checkpoint_path_is_create_only_and_legacy_schema_is_rejected(tmp_path):
    model, optimizer = _model_and_optimizer()
    path = tmp_path / "foundation.checkpoint.pt"
    artifacts.write_checkpoint(path, model, optimizer, completed_updates=0)
    with pytest.raises(artifacts.ArtifactContractError, match="create-only"):
        artifacts.write_checkpoint(path, model, optimizer, completed_updates=0)
    assert [item.name for item in tmp_path.iterdir()] == ["foundation.checkpoint.pt"]

    legacy = tmp_path / "legacy.pt"
    torch.save({"schema": "SCDMP-TBCC-CHECKPOINT", "weights": {}}, legacy)
    with pytest.raises(artifacts.ArtifactContractError, match="legacy|fields"):
        artifacts.load_checkpoint(legacy, model, optimizer)


def test_foundation_panel_and_terminal_artifacts_are_atomic_and_complete_only(tmp_path):
    with pytest.raises(artifacts.ArtifactContractError, match="incomplete foundation"):
        artifacts.write_foundation_gate(tmp_path / "gate.json", _gate(complete=False, passed=False))

    cells = _complete_cells()
    panel_analysis = analysis.analyze_complete_panel(cells)
    with pytest.raises(artifacts.ArtifactContractError, match="partial panel"):
        artifacts.write_complete_panel(tmp_path / "panel.json", cells[:-1], panel_analysis)

    panel_path = tmp_path / "panel.json"
    artifacts.write_complete_panel(panel_path, cells, panel_analysis)
    payload = json.loads(panel_path.read_text(encoding="utf-8"))
    assert payload["schema"] == artifacts.PANEL_SCHEMA
    assert len(payload["cells"]) == 144
    assert not list(tmp_path.glob("*.tmp"))

    fact = contracts.TerminalFact(
        schema=artifacts.TERMINAL_FACT_SCHEMA,
        disposition=contracts.Disposition.ESTABLISHED.value,
        foundation_gate=_gate(),
        panel_complete=False,
    )
    with pytest.raises(artifacts.ArtifactContractError, match="complete panel"):
        artifacts.write_terminal_fact(tmp_path / "fact.json", fact)

    bounds = tuple((bound.name, bound.lower) for bound in panel_analysis.bounds)
    closed_fact = contracts.TerminalFact(
        schema=artifacts.TERMINAL_FACT_SCHEMA,
        disposition=panel_analysis.disposition,
        foundation_gate=_gate(),
        panel_complete=True,
        adjusted_lower_bounds=bounds,
    )
    artifacts.write_terminal_fact(
        tmp_path / "closed-fact.json", closed_fact, panel_cells=cells
    )
    assert json.loads((tmp_path / "closed-fact.json").read_text())["disposition"] == (
        contracts.Disposition.CLOSED.value
    )

    spoofed = replace(
        closed_fact,
        disposition=contracts.Disposition.ESTABLISHED.value,
        adjusted_lower_bounds=tuple((name, 0.1) for name, _ in bounds),
    )
    with pytest.raises(artifacts.ArtifactContractError, match="panel analysis"):
        artifacts.write_terminal_fact(
            tmp_path / "spoofed-fact.json", spoofed, panel_cells=cells
        )
    with pytest.raises(artifacts.ArtifactContractError, match="complete panel"):
        artifacts.write_terminal_fact(
            tmp_path / "bool-fact.json", replace(closed_fact, panel_complete=1), panel_cells=cells  # type: ignore[arg-type]
        )


def test_complete_foundation_nonpass_can_end_without_creating_assay_artifact(tmp_path):
    gate = _gate(passed=False)
    gate_path = tmp_path / "foundation-gate.json"
    fact_path = tmp_path / "terminal-fact.json"
    artifacts.write_foundation_gate(gate_path, gate)
    artifacts.write_terminal_fact(
        fact_path,
        contracts.TerminalFact(
            schema=artifacts.TERMINAL_FACT_SCHEMA,
            disposition=contracts.Disposition.FOUNDATION_NONPASS.value,
            foundation_gate=gate,
            panel_complete=False,
        ),
    )
    assert {item.name for item in tmp_path.iterdir()} == {
        "foundation-gate.json",
        "terminal-fact.json",
    }


def test_checkpoint_tampering_rejects_float_step_truncated_or_nonfinite_moments_without_mutation():
    model, optimizer = _model_and_optimizer()
    checkpoint = artifacts.make_checkpoint(model, optimizer, completed_updates=0)
    baseline = artifacts.make_checkpoint(model, optimizer, completed_updates=0)

    mutations = []
    float_step = copy.deepcopy(checkpoint)
    float_step["optimizer"]["step"] = 0.0
    mutations.append(float_step)
    bool_step = copy.deepcopy(checkpoint)
    bool_step["optimizer"]["step"] = False
    mutations.append(bool_step)
    truncated = copy.deepcopy(checkpoint)
    truncated["optimizer"]["first"] = truncated["optimizer"]["first"][:-1]
    mutations.append(truncated)
    nonfinite = copy.deepcopy(checkpoint)
    nonfinite["optimizer"]["second"][-1].view(-1)[0] = float("nan")
    mutations.append(nonfinite)
    negative_second = copy.deepcopy(checkpoint)
    negative_second["optimizer"]["second"][-1].view(-1)[0] = -1.0
    mutations.append(negative_second)
    aliased = copy.deepcopy(checkpoint)
    shared = aliased["optimizer"]["first"][0]
    aliased["optimizer"]["first"] = tuple(
        shared for _ in aliased["optimizer"]["first"]
    )
    first_model_name = next(iter(aliased["model_state"]))
    aliased["model_state"][first_model_name] = (
        aliased["model_state"][first_model_name] + 1.0
    )
    mutations.append(aliased)

    for value in mutations:
        with pytest.raises(artifacts.ArtifactContractError):
            artifacts.restore_checkpoint(value, model, optimizer)
        assert artifacts.direct_resume_equal(baseline, model, optimizer)


def test_artifacts_reject_analysis_gate_and_terminal_semantic_tampering(tmp_path):
    cells = _complete_cells()
    observed = analysis.analyze_complete_panel(cells)
    with pytest.raises(artifacts.ArtifactContractError, match="recomputation"):
        artifacts.write_complete_panel(
            tmp_path / "mismatch.json",
            cells,
            replace(observed, interaction=observed.interaction + 0.1),
        )

    with pytest.raises(artifacts.ArtifactContractError, match="pass flag"):
        artifacts.write_foundation_gate(
            tmp_path / "bad-gate.json",
            contracts.FoundationGate(
                True,
                True,
                (("HR", 0.72), ("RH", 0.9)),
                0.9,
                tuple((name, 0.01) for name in contracts.FAILURE_LABELS),
            ),
        )

    with pytest.raises(artifacts.ArtifactContractError, match="exact four"):
        artifacts.write_terminal_fact(
            tmp_path / "bad-fact.json",
            contracts.TerminalFact(
                artifacts.TERMINAL_FACT_SCHEMA,
                contracts.Disposition.ESTABLISHED.value,
                _gate(),
                True,
                (("d_0m", 0.1),),
            ),
            panel_cells=cells,
        )


def test_lifecycle_is_fail_closed_and_contains_no_authorization_stage():
    foundation_stage = lifecycle.preflight_complete()
    assert foundation_stage.stage is lifecycle.Stage.FOUNDATION
    assert {stage.name for stage in lifecycle.Stage} == {
        "PREFLIGHT",
        "FOUNDATION",
        "ASSAY",
        "TERMINAL",
    }

    nonpass = foundation_stage.advance_foundation(_gate(passed=False))
    assert nonpass.stage is lifecycle.Stage.TERMINAL and nonpass.panel_complete is False
    assay = foundation_stage.advance_foundation(_gate())
    assert assay.stage is lifecycle.Stage.ASSAY
    assert assay.advance_panel(complete=True).stage is lifecycle.Stage.TERMINAL

    with pytest.raises(ValueError):
        foundation_stage.advance_foundation(_gate(complete=False, passed=False))
    for invalid in (False, 1, "true", None):
        with pytest.raises((TypeError, ValueError)):
            assay.advance_panel(complete=invalid)  # type: ignore[arg-type]
