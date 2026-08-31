from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path

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


def _model_and_optimizer(*, final: bool = True):
    model = foundation.FoundationActorCritic(MidpointUniforms())
    optimizer = training.ExactAdamW(tuple(model.named_parameters()))
    if final:
        optimizer.step_index = 1_920
    return model, optimizer


MASTER = bytes(range(32))


def _snapshot(tmp_path: Path, *, changed_index: int | None = None):
    manifest = contracts.Manifest()
    keys = (
        tuple(("owned_python", name) for name in manifest.source_modules)
        + tuple(
            ("dependency_python", reference.split(":", 1)[0])
            for reference in manifest.allowed_dependencies
        )
        + (("native_source", "tbcc_backend.cpp"), ("native_binary", "loaded_tbcc_backend"))
    )
    entries = tuple(
        artifacts.SourceNativeEntry(
            kind,
            name,
            str((tmp_path / f"entry-{index}").resolve()),
            (f"direct-{index}".encode() + (b"!" if index == changed_index else b"")),
        )
        for index, (kind, name) in enumerate(keys)
    )
    return artifacts.SourceNativeSnapshot(artifacts.SOURCE_NATIVE_SNAPSHOT_SCHEMA, entries)


def _bundle_bindings(tmp_path: Path):
    return {
        "resolved_result_root": str(tmp_path.resolve()),
        "rng_master": MASTER,
        "run_record_bytes": b'{"direct":"run-record"}\n',
        "source_native_snapshot": _snapshot(tmp_path),
    }


def _gate(*, complete: bool = True, passed: bool = True) -> contracts.FoundationGate:
    if not complete:
        return contracts.FoundationGate(False, False, (), float("nan"), ())
    return foundation.analyze_competence(_records(safe=passed))


def _records(*, safe: bool = True):
    return tuple(
        foundation.CompetenceRecord(row.mission, row.graph, True, safe)
        for row in foundation.competence_inventory()
    )


def _complete_cells() -> tuple[contracts.PanelCell, ...]:
    indices = {"COMMON": 0, "A_HR": 10, "A_RH": 12}
    return tuple(
        contracts.PanelCell(tape, graph, action, indices[action], True, True, 182)
        for tape in range(contracts.TAPE_COUNT)
        for graph in ("HR", "RH")
        for action in ("COMMON", "A_HR", "A_RH")
    )


def test_checkpoint_restore_has_direct_tensor_and_optimizer_equality(tmp_path):
    model, optimizer = _model_and_optimizer()
    path = tmp_path / "foundation.checkpoint.pt"
    artifacts.write_checkpoint(path, model, optimizer, completed_updates=160, rng_master=MASTER)
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
    artifacts.write_checkpoint(path, model, optimizer, completed_updates=160, rng_master=MASTER)
    with pytest.raises(artifacts.ArtifactContractError, match="create-only"):
        artifacts.write_checkpoint(path, model, optimizer, completed_updates=160, rng_master=MASTER)
    assert [item.name for item in tmp_path.iterdir()] == ["foundation.checkpoint.pt"]

    legacy = tmp_path / "legacy.pt"
    torch.save({"schema": "SCDMP-TBCC-CHECKPOINT", "weights": {}}, legacy)
    with pytest.raises(artifacts.ArtifactContractError, match="legacy|fields"):
        artifacts.load_checkpoint(legacy, model, optimizer)


def test_foundation_panel_and_terminal_artifacts_are_atomic_and_complete_only(tmp_path):
    with pytest.raises(artifacts.ArtifactContractError, match="incomplete foundation"):
        artifacts.write_foundation_gate(
            tmp_path / "gate.json", _gate(complete=False, passed=False), ()
        )

    cells = _complete_cells()
    panel_analysis = analysis.analyze_complete_panel(cells)
    with pytest.raises(artifacts.ArtifactContractError, match="3372 terminal"):
        artifacts._test_only_write_final_bundle(
            tmp_path / "panel.json", competence_records=_records(), panel_cells=cells[:-1],
            **_bundle_bindings(tmp_path),
        )

    panel_path = tmp_path / "final-bundle.json"
    bundled_fact = artifacts._test_only_write_final_bundle(
        panel_path, competence_records=_records(), panel_cells=cells,
        **_bundle_bindings(tmp_path),
    )
    payload = json.loads(panel_path.read_text(encoding="utf-8"))
    assert payload["schema"] == artifacts.FINAL_BUNDLE_SCHEMA
    assert len(payload["panel_cells"]) == contracts.PANEL_WIDTH
    assert len(payload["competence_records"]) == 120
    assert payload["terminal_fact"]["disposition"] == bundled_fact.disposition
    assert payload["terminal_fact"]["l_theta"] == bundled_fact.l_theta
    assert "joint_effect_lower_bound" not in payload["terminal_fact"]
    assert "minimum_raw_gap_mean" not in payload["panel_analysis"]
    assert "joint_value_raw_lower" not in payload["panel_analysis"]
    assert all(
        "audit_marginal_raw_lower" not in gap
        for gap in payload["panel_analysis"]["gaps"]
    )
    assert len(payload["terminal_fact"]["gap_integer_sums"]) == 3
    assert len(payload["terminal_fact"]["component_p_values"]) == 3
    assert not list(tmp_path.glob("*.tmp"))
    with pytest.raises(artifacts.ArtifactContractError, match="create-only"):
        artifacts._test_only_write_final_bundle(
            panel_path, competence_records=_records(), panel_cells=cells,
            **_bundle_bindings(tmp_path),
        )

    fact = contracts.TerminalFact(
        schema=artifacts.TERMINAL_FACT_SCHEMA,
        disposition=contracts.Disposition.ESTABLISHED.value,
        foundation_gate=_gate(),
        panel_complete=False,
    )
    with pytest.raises(artifacts.ArtifactContractError, match="atomic final bundle"):
        artifacts.write_terminal_fact(
            tmp_path / "fact.json", fact, competence_records=_records()
        )

    closed_fact = contracts.TerminalFact(
        schema=artifacts.TERMINAL_FACT_SCHEMA,
        disposition=panel_analysis.disposition,
        foundation_gate=_gate(),
        panel_complete=True,
        gap_integer_sums=tuple(
            (gap.name, gap.raw_utility_numerator_sum) for gap in panel_analysis.gaps
        ),
        component_p_values=tuple((gap.name, gap.p_value_upper) for gap in panel_analysis.gaps),
        joint_p_value=panel_analysis.p_iut,
        l_theta=panel_analysis.l_theta,
    )
    with pytest.raises(artifacts.ArtifactContractError, match="atomic final bundle"):
        artifacts.write_terminal_fact(
            tmp_path / "closed-fact.json", closed_fact,
            competence_records=_records(), panel_cells=cells
        )
    with pytest.raises(artifacts.ArtifactContractError, match="atomic final bundle"):
        artifacts.write_terminal_fact(
            tmp_path / "bool-fact.json", replace(closed_fact, panel_complete=1),
            competence_records=_records(), panel_cells=cells  # type: ignore[arg-type]
        )


def test_complete_foundation_nonpass_can_end_without_creating_assay_artifact(tmp_path):
    gate = _gate(passed=False)
    gate_path = tmp_path / "foundation-gate.json"
    fact_path = tmp_path / "terminal-fact.json"
    records = _records(safe=False)
    artifacts.write_foundation_gate(gate_path, gate, records)
    artifacts.write_terminal_fact(
        fact_path,
        contracts.TerminalFact(
            schema=artifacts.TERMINAL_FACT_SCHEMA,
            disposition=contracts.Disposition.FOUNDATION_NONPASS.value,
            foundation_gate=gate,
            panel_complete=False,
        ),
        competence_records=records,
    )
    assert {item.name for item in tmp_path.iterdir()} == {
        "foundation-gate.json",
        "terminal-fact.json",
    }


def test_checkpoint_tampering_rejects_float_step_truncated_or_nonfinite_moments_without_mutation():
    model, optimizer = _model_and_optimizer()
    checkpoint = artifacts.make_checkpoint(model, optimizer, completed_updates=160, rng_master=MASTER)
    baseline = artifacts.make_checkpoint(model, optimizer, completed_updates=160, rng_master=MASTER)

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


def test_final_checkpoint_binds_persisted_master_and_observes_direct_resume_equality(tmp_path):
    master_path = tmp_path / "rng-master.bin"
    artifacts.write_rng_master(master_path, MASTER)
    assert artifacts.load_rng_master(master_path) == MASTER
    with pytest.raises(artifacts.ArtifactContractError, match="create-only"):
        artifacts.write_rng_master(master_path, MASTER)

    uninterrupted_model, uninterrupted_optimizer = _model_and_optimizer()
    checkpoint = artifacts.make_checkpoint(
        uninterrupted_model, uninterrupted_optimizer, completed_updates=160, rng_master=MASTER
    )
    restored_model, restored_optimizer = _model_and_optimizer(final=False)
    assert restored_optimizer.step_index == 0
    artifacts.restore_checkpoint(checkpoint, restored_model, restored_optimizer)
    assert restored_optimizer.step_index == 1_920
    assert artifacts.direct_resume_equal(checkpoint, restored_model, restored_optimizer)
    witness = artifacts.observe_resume_equality(
        checkpoint,
        uninterrupted_model,
        uninterrupted_optimizer,
        restored_model,
        restored_optimizer,
        persisted_master=artifacts.load_rng_master(master_path),
    )
    assert witness.checkpoint_update == 160
    assert witness.optimizer_step == 1_920
    assert witness.continuation_stage == "COMPETENCE"
    assert witness.model_tensors_equal and witness.optimizer_tensors_equal
    assert witness.counters_equal and witness.addressed_inputs_equal


def test_artifacts_reject_analysis_gate_and_terminal_semantic_tampering(tmp_path):
    cells = _complete_cells()
    duplicate = list(cells)
    duplicate[1] = duplicate[0]
    with pytest.raises(artifacts.ArtifactContractError, match="panel semantics"):
        artifacts._test_only_write_final_bundle(
            tmp_path / "mismatch.json", competence_records=_records(), panel_cells=duplicate,
            **_bundle_bindings(tmp_path),
        )

    with pytest.raises(artifacts.ArtifactContractError, match="120 raw"):
        artifacts.write_foundation_gate(
            tmp_path / "bad-gate.json",
            contracts.FoundationGate(
                True,
                True,
                (("HR", 0.72), ("RH", 0.9)),
                0.9,
                tuple((name, 0.01) for name in contracts.FAILURE_LABELS),
            ),
            _records(),
        )

    with pytest.raises(artifacts.ArtifactContractError, match="atomic final bundle"):
        artifacts.write_terminal_fact(
            tmp_path / "bad-fact.json",
            contracts.TerminalFact(
                artifacts.TERMINAL_FACT_SCHEMA,
                contracts.Disposition.ESTABLISHED.value,
                _gate(),
                True,
                (("d_0m", 0.1),),
            ),
            competence_records=_records(),
            panel_cells=cells,
        )


def test_typed_run_record_recomputes_exact_fixed_fields_and_rejects_tampering(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    monkeypatch.setattr(artifacts.torch, "get_num_interop_threads", lambda: 1)
    record = artifacts.build_run_record()
    path = tmp_path / "run-record.json"
    artifacts.write_run_record(path, record)
    payload = json.loads(path.read_text())
    assert payload["actions"] == [0, 10, 12]
    assert payload["resources"] == dict(contracts.RESOURCE_MAXIMA)
    assert payload["runtime"]["native_batch_widths"] == {
        "training": 12, "competence": 120, "panel_full": 144, "panel_final": 60,
    }
    assert payload["runtime"]["torch_threads"] == 1
    assert payload["runtime"]["deterministic_algorithms"] is True
    with pytest.raises(artifacts.ArtifactContractError, match="frozen execution"):
        artifacts.write_run_record(
            tmp_path / "tampered.json", replace(record, panel_width=143)
        )
    with pytest.raises(artifacts.ArtifactContractError, match="version strings"):
        artifacts.write_run_record(
            tmp_path / "bad-version.json",
            replace(record, runtime=replace(record.runtime, torch="")),
        )
    torch.use_deterministic_algorithms(False)
    try:
        with pytest.raises(artifacts.ArtifactContractError, match="runtime"):
            artifacts.write_run_record(tmp_path / "runtime-drift.json", record)
    finally:
        torch.use_deterministic_algorithms(True)


def test_production_bundle_publisher_is_distinct_from_the_private_fixture():
    assert hasattr(artifacts, "write_final_bundle")
    assert "write_final_bundle" in artifacts.__all__
    assert "_test_only_write_final_bundle" not in artifacts.__all__


def test_direct_source_native_snapshot_has_exact_inventory_lengths_and_rejects_byte_drift(
    tmp_path, monkeypatch,
):
    fixture_root = tmp_path / "live"
    fixture_root.mkdir()
    template = _snapshot(fixture_root)
    material = []
    for index, entry in enumerate(template.entries):
        path = fixture_root / f"material-{index}"
        path.write_bytes(entry.direct_bytes)
        material.append((entry.kind, entry.name, path))
    monkeypatch.setattr(artifacts, "_live_source_native_material", lambda: tuple(material))

    captured = artifacts.capture_source_native_snapshot()
    assert len(captured.entries) == 19
    assert [entry.kind for entry in captured.entries].count("owned_python") == 14
    assert [entry.kind for entry in captured.entries].count("dependency_python") == 3
    assert [entry.kind for entry in captured.entries].count("native_source") == 1
    assert [entry.kind for entry in captured.entries].count("native_binary") == 1
    encoded = artifacts.encode_source_native_snapshot(captured)
    payload = json.loads(encoded)
    assert all(row["length_bytes"] == len(entry.direct_bytes) for row, entry in zip(payload["entries"], captured.entries))
    assert all("hash" not in key.lower() for row in payload["entries"] for key in row)

    path = tmp_path / "source-native-snapshot.json"
    artifacts.write_source_native_snapshot(path, captured)
    loaded = artifacts.load_source_native_snapshot(path)
    artifacts.compare_source_native_snapshot(loaded, captured)
    with pytest.raises(artifacts.ArtifactContractError, match="create-only"):
        artifacts.write_source_native_snapshot(path, captured)

    material[7][2].write_bytes(material[7][2].read_bytes() + b"one-byte")
    changed = artifacts.capture_source_native_snapshot()
    with pytest.raises(artifacts.ArtifactContractError, match="direct bytes"):
        artifacts.compare_source_native_snapshot(loaded, changed)

    tampered = json.loads(encoded)
    tampered["entries"][0]["length_bytes"] += 1
    tampered_path = tmp_path / "length-tampered.json"
    tampered_path.write_text(json.dumps(tampered, sort_keys=True, separators=(",", ":")) + "\n")
    with pytest.raises(artifacts.ArtifactContractError, match="length"):
        artifacts.load_source_native_snapshot(tampered_path)


def test_v5_final_bundle_preencoding_binds_root_master_record_and_snapshot(tmp_path):
    cells = _complete_cells()
    bindings = _bundle_bindings(tmp_path)
    prepared = artifacts.prepare_final_bundle(
        competence_records=_records(),
        panel_cells=cells,
        panel_analysis=analysis.analyze_complete_panel(cells),
        **bindings,
    )
    assert artifacts.final_bundle_encoded_size(prepared) == len(prepared.encoded)
    assert artifacts.final_bundle_encoded_size(prepared) < 64 * 1024 * 1024
    payload = json.loads(prepared.encoded)
    assert payload["resolved_result_root"] == str(tmp_path.resolve())
    assert payload["schema"] == "SCDMP_FCEOV_FINAL_BUNDLE_V5"
    assert "hash" not in json.dumps(payload["source_native_snapshot"]).lower()

    bundle = tmp_path / "final-bundle.json"
    fact = artifacts.write_prepared_final_bundle(bundle, prepared)
    assert artifacts.load_final_bundle(
        bundle,
        expected_result_root=bindings["resolved_result_root"],
        expected_rng_master=MASTER,
        expected_run_record_bytes=bindings["run_record_bytes"],
        expected_source_native_snapshot=bindings["source_native_snapshot"],
    ) == fact

    legacy_payload = dict(payload)
    legacy_payload["schema"] = "SCDMP_FCEOV_FINAL_BUNDLE_V4"
    legacy_bundle = tmp_path / "legacy-v4-final-bundle.json"
    legacy_bundle.write_text(
        json.dumps(legacy_payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(artifacts.ArtifactContractError, match="schema"):
        artifacts.load_final_bundle(
            legacy_bundle,
            expected_result_root=bindings["resolved_result_root"],
            expected_rng_master=MASTER,
            expected_run_record_bytes=bindings["run_record_bytes"],
            expected_source_native_snapshot=bindings["source_native_snapshot"],
        )
    for changed in (
        {"expected_result_root": str((tmp_path / "other-root").resolve())},
        {"expected_rng_master": b"x" * 32},
        {"expected_run_record_bytes": b"other-record"},
        {"expected_source_native_snapshot": _snapshot(tmp_path, changed_index=0)},
    ):
        expected = {
            "expected_result_root": bindings["resolved_result_root"],
            "expected_rng_master": MASTER,
            "expected_run_record_bytes": bindings["run_record_bytes"],
            "expected_source_native_snapshot": bindings["source_native_snapshot"],
        }
        expected.update(changed)
        with pytest.raises(artifacts.ArtifactContractError, match="binding"):
            artifacts.load_final_bundle(bundle, **expected)


def test_foundation_nonpass_terminal_loader_recomputes_and_rejects_tampering(tmp_path):
    records = _records(safe=False)
    gate = foundation.analyze_competence(records)
    path = tmp_path / "terminal-fact.json"
    artifacts.write_terminal_fact(
        path,
        contracts.TerminalFact(
            artifacts.TERMINAL_FACT_SCHEMA,
            contracts.Disposition.FOUNDATION_NONPASS.value,
            gate,
            False,
        ),
        competence_records=records,
    )
    first = artifacts.load_foundation_nonpass_terminal(path)
    second = artifacts.load_foundation_nonpass_terminal(path)
    assert first == second
    assert first[0].disposition == contracts.Disposition.FOUNDATION_NONPASS.value
    assert len(first[1]) == 120

    payload = json.loads(path.read_text())
    payload["competence_records"][0]["safe_dock"] = True
    tampered = tmp_path / "tampered-terminal.json"
    tampered.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    with pytest.raises(artifacts.ArtifactContractError, match="120 raw|differs"):
        artifacts.load_foundation_nonpass_terminal(tampered)


def test_foundation_artifact_retains_all_raw_records_counts_and_rejects_partial_or_tampered(tmp_path):
    records = _records()
    gate = foundation.analyze_competence(records)
    path = tmp_path / "gate.json"
    artifacts.write_foundation_gate(path, gate, records)
    payload = json.loads(path.read_text())
    assert len(payload["competence_records"]) == 120
    assert payload["counts"] == {
        "missions": 120,
        "safe_by_graph": {"HR": 60, "RH": 60},
        "pooled_safe": 120,
        "failures": {name: 0 for name in contracts.FAILURE_LABELS},
    }
    with pytest.raises(artifacts.ArtifactContractError, match="120 raw"):
        artifacts.write_foundation_gate(tmp_path / "partial.json", gate, records[:-1])
    tampered = list(records)
    tampered[0] = replace(tampered[0], safe_dock=False)
    with pytest.raises(artifacts.ArtifactContractError, match="120 raw"):
        artifacts.write_foundation_gate(tmp_path / "tampered.json", gate, tampered)


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
