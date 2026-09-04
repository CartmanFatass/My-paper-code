from __future__ import annotations

from dataclasses import fields, replace
import copy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    analysis,
    artifacts,
    contracts,
    foundation,
    host_bridge,
    runner,
    source_manifest,
)


_HISTORICAL_MASTER_CONTRACT = (
    "one OS-cryptographic 32-byte master after fresh preflight and resource admission",
    "create-only raw persistence; every resume reloads the same master",
    "no redraw, replacement, seed selection, threshold change, or tape-count change",
    "checkpoint V3 binds the same raw master at completed update 160",
)


def _historical_manifest() -> contracts.Manifest:
    return contracts.Manifest(
        production_status="READY_GUARDED_RESUMABLE_RESULT",
        master_contract=_HISTORICAL_MASTER_CONTRACT,
    )


def _bind_canonical(monkeypatch, root):
    monkeypatch.setattr(runner, "CANONICAL_RESULT_ROOT", root)


def _simulate_live_package_module_addition(monkeypatch):
    package_root = Path(source_manifest.__file__).resolve().parent
    original_glob = Path.glob

    def drifted_glob(path, pattern):
        rows = original_glob(path, pattern)
        if path.resolve() == package_root and pattern == "*.py":
            return iter((*rows, package_root / "future_live_module.py"))
        return rows

    monkeypatch.setattr(Path, "glob", drifted_glob)


def test_fixed_task_clock_horizon_k_state_and_hr_rh_public_alias():
    assert contracts.HOST == "QUAD-UAV-PALLET-GANTRY-24P5M-v1"
    assert contracts.TICK_SECONDS == 0.1
    assert contracts.HORIZON_TICKS == 364
    assert contracts.K_TARGET == 13

    state = contracts.fixed_claim_state()
    assert state == contracts.PublicClaimState(
        x=0.0,
        v=0.015,
        y=0.0,
        w=0.0,
        phi=0.0,
        omega=0.0,
        z=(0.0, 0.0, 0.0, 0.0),
        formation=0.0,
        prior_a=1,
        prior_load_share=(0, 0, 0, 0),
        tick=0,
        k=13,
    )
    assert len(state.observation()) == 18
    assert len(state.observation_bytes()) == 18 * 8
    assert contracts.validate_state_alias(state, state.observation_bytes()) is True
    with pytest.raises(contracts.ContractError, match="byte-identical"):
        contracts.validate_state_alias(state, replace(state, v=0.0150000000000001))
    with pytest.raises(contracts.ContractError, match="exactly 18"):
        contracts.validate_state_alias(b"same", b"same")
    public_fields = {field.name for field in fields(contracts.PublicClaimState)}
    assert "prior_load_share" in public_fields
    assert "prior_rewards" not in public_fields


def test_graph_maps_action_catalogue_and_resource_contract_are_exact_and_immutable():
    assert contracts.GRAPHS == ("HR", "RH")
    assert dict(contracts.GRAPH_Q) == {"HR": 1, "RH": 0}
    assert dict(contracts.GRAPH_ASSIGNMENT) == {
        "HR": (4, 2, 1, 3),
        "RH": (1, 4, 2, 3),
    }
    assert dict(contracts.GRAPH_EVENTS) == {
        "HR": ("HOOK_HANDOFF", "FORMATION_ROTATE"),
        "RH": ("FORMATION_ROTATE", "HOOK_HANDOFF"),
    }
    assert dict(contracts.CANDIDATE_ACTIONS) == {"COMMON": 0, "A_HR": 10, "A_RH": 12}
    assert contracts.ACTIONS[0] == (1, (0, 0, 0, 0))
    assert contracts.ACTIONS[10] == (2, (1, -1, 0, 0))
    assert contracts.ACTIONS[12] == (2, (0, 0, 1, -1))
    assert dict(contracts.RESOURCE_MAXIMA) == {
        "episodes_rollouts": 5_412,
        "primitive_slots": 1_969_968,
        "adamw_steps": 1_920,
        "checkpoints": 1,
        "forced_actions": 3_372,
        "foundation_queries": 148_164,
        "panel_slices": 24,
    }

    for value in (
        contracts.GRAPH_Q,
        contracts.GRAPH_ASSIGNMENT,
        contracts.GRAPH_EVENTS,
        contracts.CANDIDATE_ACTIONS,
        contracts.RESOURCE_MAXIMA,
    ):
        with pytest.raises(TypeError):
            value["mutation"] = 1  # type: ignore[index]


def test_native_local_headroom_witness_is_registered_exactly():
    hr_bytes, rh_bytes = host_bridge.verify_public_alias()
    assert hr_bytes == rh_bytes == contracts.fixed_claim_state().observation_bytes()
    observed = host_bridge.headroom_conformance()
    assert observed.analytic_witness == host_bridge.HeadroomWitness(
        matched_load=0.84,
        mismatched_load=0.94,
        common_maximum_load=0.66,
    )
    assert observed.native_matched_exposure_zero is True
    assert observed.native_mismatched_exposure == pytest.approx(0.06, abs=1e-15)
    assert observed.native_common_exposure_zero is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("advanced", True),
        ("hold_k", 13),
        ("next_k", 7),
        ("last_hold_reward_count", 1),
        ("last_hold_rewards", (1.0,) + (0.0,) * 12),
    ),
)
def test_shared_native_reset_validator_rejects_omitted_counter_mutations(field, value):
    reset = host_bridge.fixed_resets()[0]
    fields = {
        "advanced": False, "active": True, "terminal": False, "tick": 0,
        "ticks_advanced": 0, "hold_k": 0, "next_k": 13,
        "observation": contracts.fixed_claim_state().observation(),
        "cumulative_reward": 0.0, "cumulative_energy": 0.0, "energy_ticks": 0,
        "safe_dock": False, "timeout": False, "cable_overload": False,
        "gantry_contact": False, "attitude_loss": False, "formation_loss": False,
        "dock_tick": None, "last_hold_reward_count": 0,
        "last_hold_rewards": (0.0,) * 13,
    }
    fields[field] = value
    with pytest.raises(host_bridge.HostBridgeError, match="reset state/counters"):
        host_bridge.validate_native_reset_outputs(
            (reset,), (SimpleNamespace(**fields),), width=1, context="test"
        )


@pytest.mark.parametrize(("field", "value"), (("advanced", False), ("hold_k", 12)))
def test_shared_transition_rejects_active_advanced_or_hold_drift(field, value):
    before = SimpleNamespace(
        advanced=False, active=True, terminal=False, ticks_advanced=0, tick=0,
        hold_k=0, next_k=13, observation=(0.0,) * 18, safe_dock=False,
        timeout=False, cable_overload=False, gantry_contact=False, attitude_loss=False,
        formation_loss=False, cumulative_reward=0.0, cumulative_energy=0.0,
        energy_ticks=0, dock_tick=None, last_hold_reward_count=0,
        last_hold_rewards=(0.0,) * 13,
    )
    after = SimpleNamespace(**{
        **vars(before), "advanced": True, "ticks_advanced": 13, "tick": 13,
        "hold_k": 13, "last_hold_reward_count": 13,
    })
    setattr(after, field, value)
    with pytest.raises(host_bridge.HostBridgeError, match="frontier"):
        host_bridge.validate_native_transition((before,), (after,), width=1, context="test")


def test_shared_transition_requires_full_cached_absorbed_output_equality():
    before = SimpleNamespace(
        advanced=True, active=False, terminal=True, ticks_advanced=7, tick=7,
        hold_k=13, next_k=13, observation=(0.0,) * 18, safe_dock=False,
        timeout=False, cable_overload=True, gantry_contact=False, attitude_loss=False,
        formation_loss=False, cumulative_reward=-1.0, cumulative_energy=0.25,
        energy_ticks=7, dock_tick=None, last_hold_reward_count=7,
        last_hold_rewards=(-1.0,) + (0.0,) * 12,
    )
    after = SimpleNamespace(**{**vars(before), "last_hold_rewards": (-0.5,) + (0.0,) * 12})
    with pytest.raises(host_bridge.HostBridgeError, match="absorbed.*mutated"):
        host_bridge.validate_native_transition((before,), (after,), width=1, context="test")


def test_structural_schema_names_and_direct_manifest_are_exact(tmp_path):
    assert contracts.MANIFEST_SCHEMA == "SCDMP_FCEOV_MANIFEST_V4"
    assert artifacts.CHECKPOINT_SCHEMA == "SCDMP_FCEOV_CHECKPOINT_V4"
    assert contracts.CHECKPOINT_UPDATE == 160
    assert artifacts.FOUNDATION_GATE_SCHEMA == "SCDMP_FCEOV_FOUNDATION_GATE_V4"
    assert artifacts.PANEL_SCHEMA == "SCDMP_FCEOV_COMPLETE_2X3_RESULT_V4"
    assert artifacts.TERMINAL_FACT_SCHEMA == "SCDMP_FCEOV_TERMINAL_V4"
    assert artifacts.RUN_RECORD_SCHEMA == "SCDMP_FCEOV_RUN_RECORD_V4"
    assert artifacts.RESUME_WITNESS_SCHEMA == "SCDMP_FCEOV_RESUME_WITNESS_V4"
    assert artifacts.PANEL_SLICE_SCHEMA == "SCDMP_FCEOV_PANEL_SLICE_V4"
    assert artifacts.PANEL_FRONTIER_SCHEMA == "SCDMP_FCEOV_PANEL_FRONTIER_V4"
    assert artifacts.SOURCE_NATIVE_SNAPSHOT_SCHEMA == (
        "SCDMP_FCEOV_SOURCE_NATIVE_DIRECT_BYTES_V2"
    )
    assert artifacts.FINAL_BUNDLE_SCHEMA == "SCDMP_FCEOV_FINAL_BUNDLE_V5"
    assert contracts.LIFECYCLE_STATUS == "CLOSED_TERMINAL_OBJECT_CONSUMED"
    assert contracts.RESULT_COMMAND_STATUS == "DO_NOT_INVOKE"
    assert contracts.Manifest().production_status == "CLOSED_TERMINAL_OBJECT_CONSUMED"
    assert contracts.Manifest().master_contract == (
        "the completed .3 scientific object is valid and consumed",
        "no fresh, resume, reload, continuation, replacement, or result invocation",
        "preflight reports the terminal tombstone without admission or artifact access",
        "only explicit read-only validation of the consumed artifact is permitted",
    )

    value = source_manifest.build_source_manifest()
    assert not {"hash", "digest", "identity", "authorization", "approval", "lease"} & {
        key.lower() for key in value
    }
    path = tmp_path / "manifest.json"
    source_manifest.write_source_manifest(path)
    assert source_manifest.load_source_manifest(path) == contracts.Manifest()
    with pytest.raises(source_manifest.SourceManifestError):
        source_manifest.validate_source_manifest({**value, "schema": "legacy"})

    for family in (
        "product_initialization",
        "claim_state",
        "graph_contract",
        "candidate_actions",
        "competence_contract",
        "contrast_contract",
        "inference_contract",
        "resource_maxima",
        "source_modules",
        "allowed_dependencies",
    ):
        tampered = copy.deepcopy(value)
        tampered[family] = []
        with pytest.raises(source_manifest.SourceManifestError):
            source_manifest.validate_source_manifest(tampered)


def test_preflight_is_an_effect_free_terminal_tombstone(monkeypatch):
    class ExplodingPath:
        def __fspath__(self):
            raise AssertionError("tombstone preflight must not inspect paths")

    for name in (
        "load_source_manifest", "build_training_plan", "build_panel_inventory",
        "preflight_native_panel_widths", "verify_public_alias", "headroom_conformance",
    ):
        monkeypatch.setattr(
            runner, name,
            lambda *args, _name=name, **kwargs: pytest.fail(f"preflight called {_name}"),
        )
    report = runner.run_preflight(manifest=ExplodingPath(), result_root=ExplodingPath())
    assert report == {
        "lifecycle_status": "CLOSED_TERMINAL_OBJECT_CONSUMED",
        "result_command_status": "DO_NOT_INVOKE",
        "message": "FCEOV .3 consumed, no fresh/resume/reload/continuation",
    }


def test_cli_reports_tombstone_rejects_result_and_dispatches_read_only_validation(
    tmp_path, monkeypatch, capsys,
):
    manifest = tmp_path / "manifest.json"
    source_manifest.write_source_manifest(manifest)
    result_root = tmp_path / "never-created"
    assert runner.main(
        ["--preflight-only", "--manifest", str(manifest), "--result-root", str(result_root)]
    ) == 0
    preflight_stdout = capsys.readouterr().out
    assert json.loads(preflight_stdout) == {
        "lifecycle_status": "CLOSED_TERMINAL_OBJECT_CONSUMED",
        "result_command_status": "DO_NOT_INVOKE",
        "message": "FCEOV .3 consumed, no fresh/resume/reload/continuation",
    }
    assert not result_root.exists()

    validation = {
        "validated": True,
        "lifecycle_status": "CLOSED_TERMINAL_OBJECT_CONSUMED",
        "result_command_status": "DO_NOT_INVOKE",
        "artifact": str(result_root / "final-bundle.json"),
        "disposition": contracts.Disposition.CLOSED.value,
        "panel_complete": True,
    }
    monkeypatch.setattr(runner, "validate_consumed_artifact", lambda **kwargs: validation)
    assert runner.main([
        "--validate-consumed-artifact", str(result_root / "final-bundle.json"),
        "--result-root", str(result_root),
    ]) == 0
    assert json.loads(capsys.readouterr().out) == validation

    assert runner.main([
        "--phase", "FOUNDATION_AND_2X3", "--manifest", str(manifest),
        "--result-root", str(result_root),
    ]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert ".3 consumed, no fresh/resume/reload/continuation" in captured.err
    assert not result_root.exists()

    for phase in ("FOUNDATION", "ASSAY", "anything"):
        with pytest.raises(SystemExit) as error:
            runner.main(
                ["--phase", phase, "--manifest", str(manifest), "--result-root", str(result_root)]
            )
        assert error.value.code == 2
    with pytest.raises(SystemExit) as error:
        runner.main(["--manifest", str(manifest), "--result-root", str(result_root)])
    assert error.value.code == 2
    help_text = runner._parser().format_help()
    assert "--preflight-only" in help_text
    assert "--phase" in help_text
    assert "FOUNDATION_AND_2X3" in help_text
    assert "--validate-consumed-artifact" in help_text


def test_every_result_entry_rejects_before_path_or_scientific_effect(monkeypatch):
    class ExplodingPath:
        def __fspath__(self):
            raise AssertionError("closed result entry inspected a path")

    for name in (
        "set_atomic_scratch_observer", "load_source_manifest", "load_rng_master",
        "fresh_master", "materialize_foundation", "load_checkpoint",
    ):
        monkeypatch.setattr(
            runner, name,
            lambda *args, _name=name, **kwargs: pytest.fail(f"closed entry called {_name}"),
        )
    for entry in (
        runner.run_result,
        runner._execute_result_pipeline,
        runner._execute_result_pipeline_body,
    ):
        with pytest.raises(
            runner.PreflightError,
            match=r"\.3 consumed, no fresh/resume/reload/continuation",
        ):
            entry(manifest=ExplodingPath(), result_root=ExplodingPath())

    helper_calls = (
        lambda: runner._admit_memory_or_record(
            root=ExplodingPath(), receipt=ExplodingPath(), stage="closed",
        ),
        lambda: runner._publish_staging_root(ExplodingPath(), ExplodingPath()),
        lambda: runner._validate_persisted_contract(ExplodingPath(), ExplodingPath()),
        lambda: runner._initialize_fresh_root(
            manifest=ExplodingPath(), root=ExplodingPath(), started_at=0.0,
        ),
        lambda: runner._train_and_restore_foundation(ExplodingPath(), b""),
        lambda: runner._load_or_execute_foundation_gate(
            ExplodingPath(), object(), object(),
        ),
        lambda: runner._reconcile_frontier(ExplodingPath(), 0),
        lambda: runner._prepare_and_publish_final(
            root=ExplodingPath(), master=b"", run_record_bytes=b"",
            source_snapshot=object(), records=(), cells=(), panel_analysis=object(),
            started_at=0.0,
        ),
    )
    for call in helper_calls:
        with pytest.raises(
            runner.PreflightError,
            match=r"\.3 consumed, no fresh/resume/reload/continuation",
        ):
            call()


def test_consumed_artifact_missing_is_read_only_and_cannot_fall_back(
    tmp_path, monkeypatch
):
    root = tmp_path / "missing-consumed-root"
    _bind_canonical(monkeypatch, root)
    for name in (
        "load_consumed_source_manifest", "load_run_record", "load_source_native_snapshot",
        "load_rng_master", "load_final_bundle", "fresh_master", "materialize_foundation",
    ):
        monkeypatch.setattr(
            runner, name,
            lambda *args, _name=name, **kwargs: pytest.fail(f"missing validation called {_name}"),
        )
    with pytest.raises(runner.PreflightError, match=r"consumed \.3 final bundle is missing"):
        runner.validate_consumed_artifact(
            artifact=root / "final-bundle.json", result_root=root,
        )
    assert not root.exists()


def test_historical_consumed_manifest_status_has_a_dedicated_validator(
    tmp_path, monkeypatch,
):
    historical = _historical_manifest().to_dict()
    path = tmp_path / "historical-source-manifest.json"
    path.write_text(
        json.dumps(historical, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    _simulate_live_package_module_addition(monkeypatch)
    with pytest.raises(source_manifest.SourceManifestError, match="module inventory"):
        source_manifest.validate_source_manifest(source_manifest.build_source_manifest())
    assert source_manifest.load_consumed_source_manifest(path).production_status == (
        "READY_GUARDED_RESUMABLE_RESULT"
    )
    with pytest.raises(source_manifest.SourceManifestError):
        source_manifest.load_source_manifest(path)

    for field, value in (("tapes", 561), ("panel_width", 3_371)):
        tampered = dict(historical)
        tampered[field] = value
        path.write_text(
            json.dumps(tampered, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(source_manifest.SourceManifestError, match=r"historical \.3"):
            source_manifest.load_consumed_source_manifest(path)


def test_validate_consumed_artifact_recomputes_complete_history_without_writes_or_fallback(
    tmp_path, monkeypatch,
):
    root = tmp_path / "synthetic-consumed-dot3"
    root.mkdir()
    _bind_canonical(monkeypatch, root)

    historical = _historical_manifest()
    (root / "source-manifest.json").write_text(
        json.dumps(historical.to_dict(), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    run_record = {
        "schema": "SCDMP_FCEOV_RUN_RECORD_V4",
        "phase": runner.PHASE,
        "checkpoint_update": 160,
        "foundation_updates": 160,
        "episodes_per_update": 12,
        "competence_missions": 120,
        "panel_width": contracts.PANEL_WIDTH,
        "actions": [0, 10, 12],
        "resources": dict(contracts.RESOURCE_MAXIMA),
        "runtime": {
            "python": "historical-python",
            "torch": "historical-torch",
            "device": "cpu",
            "torch_threads": 1,
            "torch_interop_threads": 1,
            "deterministic_algorithms": True,
            "native_batch_widths": {
                "training": 12, "competence": 120, "panel_full": 144,
                "panel_final": 60,
            },
        },
    }
    run_record_bytes = (
        json.dumps(run_record, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    (root / "run-record.json").write_bytes(run_record_bytes)

    keys = (
        tuple(("owned_python", name) for name in historical.source_modules)
        + tuple(
            ("dependency_python", reference.split(":", 1)[0])
            for reference in historical.allowed_dependencies
        )
        + (("native_source", "tbcc_backend.cpp"),
           ("native_binary", "loaded_tbcc_backend"))
    )
    snapshot = artifacts.SourceNativeSnapshot(
        artifacts.SOURCE_NATIVE_SNAPSHOT_SCHEMA,
        tuple(
            artifacts.SourceNativeEntry(
                kind, name, str((root / f"snapshot-entry-{index}").resolve()),
                f"historical-direct-{index}".encode("ascii"),
            )
            for index, (kind, name) in enumerate(keys)
        ),
    )
    artifacts.write_source_native_snapshot(root / "source-native-snapshot.json", snapshot)
    master = bytes(range(32))
    artifacts.write_rng_master(root / "rng-master.bin", master)

    records = tuple(
        foundation.CompetenceRecord(row.mission, row.graph, True, True)
        for row in foundation.competence_inventory()
    )
    action_indices = {"COMMON": 0, "A_HR": 10, "A_RH": 12}
    cells = tuple(
        contracts.PanelCell(
            tape, graph, action_name, action_indices[action_name], True, True, 182,
        )
        for tape in range(contracts.TAPE_COUNT)
        for graph in contracts.GRAPHS
        for action_name in ("COMMON", "A_HR", "A_RH")
    )
    prepared = artifacts.prepare_final_bundle(
        competence_records=records,
        panel_cells=cells,
        panel_analysis=analysis.analyze_complete_panel(cells),
        resolved_result_root=str(root.resolve()),
        rng_master=master,
        run_record_bytes=run_record_bytes,
        source_native_snapshot=snapshot,
    )
    artifacts.write_prepared_final_bundle(root / "final-bundle.json", prepared)
    receipt_base = {
        "schema": runner._DIRECTION_RESOURCE_SCHEMA,
        "passed": True,
        "failure_reasons": [],
        "attempt_cumulative_scratch_peak_bytes": 0,
        "peak_rss_bytes": 1,
        "wall_seconds": 0.1,
        "durable_bytes": (root / "final-bundle.json").stat().st_size,
    }
    (root / "direction-resource-pre-final-publication-0000.json").write_text(
        json.dumps({
            **receipt_base,
            "stage": "pre-final-publication",
            "scratch_bytes": (root / "final-bundle.json").stat().st_size,
        }, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (root / "direction-resource-final-publication-0000.json").write_text(
        json.dumps({
            **receipt_base, "stage": "final-publication",
        }, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    before = tuple(
        (str(path.relative_to(root)), path.read_bytes())
        for path in sorted(root.rglob("*")) if path.is_file()
    )
    for name in (
        "fresh_master", "train_one_update", "execute_native_competence",
        "execute_native_panel_slice", "materialize_foundation", "load_checkpoint",
        "capture_source_native_snapshot", "compare_source_native_snapshot",
        "_prepare_and_publish_final",
    ):
        monkeypatch.setattr(
            runner, name,
            lambda *args, _name=name, **kwargs: pytest.fail(f"validation called {_name}"),
        )

    _simulate_live_package_module_addition(monkeypatch)
    report = runner.validate_consumed_artifact(
        artifact=root / "final-bundle.json", result_root=root,
    )
    after = tuple(
        (str(path.relative_to(root)), path.read_bytes())
        for path in sorted(root.rglob("*")) if path.is_file()
    )
    assert report == {
        "validated": True,
        "lifecycle_status": "CLOSED_TERMINAL_OBJECT_CONSUMED",
        "result_command_status": "DO_NOT_INVOKE",
        "artifact": str((root / "final-bundle.json").resolve()),
        "disposition": contracts.Disposition.CLOSED.value,
        "panel_complete": True,
    }
    assert after == before


def test_post_work_resource_measurement_failure_is_terminal_after_resources_recover(
    tmp_path, monkeypatch
):
    root = tmp_path / "canonical-post-work-measurement-failure"
    root.mkdir()
    for name in (
        "source-manifest.json", "source-native-snapshot.json", "rng-master.bin",
        "run-record.json",
    ):
        (root / name).write_bytes(b"present")
    _bind_canonical(monkeypatch, root)

    monkeypatch.setattr(
        runner, "_direction_resource_assessment",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("telemetry unavailable")),
    )
    with pytest.raises(runner.ResourceAdmissionError, match="slice-000-native"):
        runner._enforce_direction_resources(
            stage="slice-000-native", root=root, scratch_root=None,
            started_at=runner.time.perf_counter(), terminal_on_failure=True,
        )

    invalid_path = root / "invalid-evidence.json"
    invalid = json.loads(invalid_path.read_text(encoding="utf-8"))
    assert invalid["failure_reasons"] == ["resource_measurement_failed"]
    assert invalid["resource_assessment"]["failure_reasons"] == [
        "resource_measurement_failed"
    ]
    assert invalid["resource_assessment"]["passed"] is False
    assert not runner._contains_forbidden_receipt_key(invalid)

    healthy_calls = []
    monkeypatch.setattr(
        runner, "_direction_resource_assessment",
        lambda **kwargs: healthy_calls.append(kwargs) or {
            "schema": runner._DIRECTION_RESOURCE_SCHEMA,
            "passed": True,
            "failure_reasons": [],
        },
    )
    assert runner._enforce_direction_resources(
        stage="later-healthy-observation", root=root, scratch_root=None,
        started_at=runner.time.perf_counter(),
    )["passed"] is True
    with pytest.raises(
        runner.PreflightError, match=r"\.3 consumed, no fresh/resume/reload/continuation"
    ):
        runner._execute_result_pipeline(
            manifest=tmp_path / "unused-manifest.json", result_root=root,
        )
    assert len(healthy_calls) == 1
    assert not (root / "final-bundle.json").exists()


def test_pre_work_resource_measurement_failure_can_recover_at_same_frontier(
    tmp_path, monkeypatch
):
    root = tmp_path / "recoverable-pre-work-measurement-failure"
    root.mkdir()
    calls = []

    def fail_then_pass(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("telemetry unavailable")
        return {
            "schema": runner._DIRECTION_RESOURCE_SCHEMA,
            "passed": True,
            "failure_reasons": [],
        }

    monkeypatch.setattr(runner, "_direction_resource_assessment", fail_then_pass)
    with pytest.raises(runner.ResourceAdmissionError, match="slice-007-before"):
        runner._enforce_direction_resources(
            stage="slice-007-before", root=root, scratch_root=None,
            started_at=runner.time.perf_counter(), terminal_on_failure=False,
        )
    assert not (root / "invalid-evidence.json").exists()
    assert runner._enforce_direction_resources(
        stage="slice-007-before", root=root, scratch_root=None,
        started_at=runner.time.perf_counter(), terminal_on_failure=False,
    )["passed"] is True
    assert len(calls) == 2
    assert not (root / "invalid-evidence.json").exists()


def test_direction_launch_capacity_uses_shared_reserve_and_peak_formula(tmp_path, monkeypatch):
    root = tmp_path / "capacity"
    monkeypatch.setattr(runner, "_physical_total_memory_bytes", lambda: 16 * 1024**3)
    monkeypatch.setattr(runner, "_peak_working_set_bytes", lambda: 128 * 1024**2)
    unsafe = runner._direction_resource_assessment(
        root=root, scratch_root=None, started_at=runner.time.perf_counter(),
        memory_receipt={
            "effective_available_bytes": 5 * 1024**3,
            "cgroup_memory_max_bytes": None,
        },
    )
    assert unsafe["capacity"]["workers"] == 1
    assert unsafe["capacity"]["threads_per_worker"] == 1
    assert unsafe["capacity"]["adjusted_peak_bytes"] == 5 * 1024**3 // 4
    assert unsafe["passed"] is False
    assert "shared_reserve_and_peak_formula_failed" in unsafe["failure_reasons"]

    safe = runner._direction_resource_assessment(
        root=root, scratch_root=None, started_at=runner.time.perf_counter(),
        memory_receipt={
            "effective_available_bytes": 6 * 1024**3,
            "cgroup_memory_max_bytes": None,
        },
    )
    assert safe["capacity"]["memory_safe"] is True
    assert safe["passed"] is True


def test_clean_process_engages_single_thread_intra_interop_and_deterministic_torch():
    code = (
        "import json,torch;"
        "torch.set_num_threads(1);"
        "torch.set_num_interop_threads(1);"
        "torch.use_deterministic_algorithms(True);"
        "print(json.dumps([torch.get_num_threads(),torch.get_num_interop_threads(),"
        "torch.are_deterministic_algorithms_enabled()]))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=20
    )
    assert json.loads(completed.stdout) == [1, 1, True]


def test_all_historical_and_noncanonical_result_roots_share_the_tombstone(tmp_path, monkeypatch):
    quarantined_first = tmp_path / "2026-08-31.1-wave3-fceov-v3"
    quarantined_second = tmp_path / "2026-08-31.2-wave3-fceov-v3-replacement"
    replacement = tmp_path / "2026-08-31.3-wave3-fceov-v3-replacement"
    monkeypatch.setattr(runner, "QUARANTINED_RESULT_ROOT", quarantined_first)
    monkeypatch.setattr(
        runner, "QUARANTINED_REPLACEMENT_RESULT_ROOT", quarantined_second,
    )
    monkeypatch.setattr(runner, "CANONICAL_RESULT_ROOT", replacement)
    for path in (quarantined_first, quarantined_second, replacement, tmp_path / "other"):
        with pytest.raises(runner.PreflightError, match=r"\.3 consumed, no fresh/resume/reload/continuation"):
            runner.run_result(manifest=tmp_path / "unused.json", result_root=path)
    assert replacement not in (quarantined_first, quarantined_second)


def test_shared_assess_run_validates_exact_frozen_plan_and_floor(tmp_path, monkeypatch):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        out = Path(argv[argv.index("--out") + 1])
        out.write_text(json.dumps({
            "direction_id": runner._ASSESS_DIRECTION,
            "run_id": runner._ASSESS_RUN_ID,
            "workers": 1,
            "threads_per_worker": 1,
            "estimate": {
                "wall_seconds": 300,
                "peak_memory_gib": 1.0,
                "basis": "frozen SCDMP FCEOV replacement resource envelope",
            },
            "minimum_available_bytes": 4 * 1024**3,
            "physical_floor_pass": True,
            "effective_floor_pass": True,
            "memory_floor_pass": True,
            "memory_safe": True,
        }), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    receipt = tmp_path / "assess.json"
    assert runner.assess_run(receipt)["memory_safe"] is True
    argv = calls[0]
    assert argv[2] == "assess-run"
    assert argv[argv.index("--workers") + 1] == "1"
    assert argv[argv.index("--threads-per-worker") + 1] == "1"

    value = json.loads(receipt.read_text(encoding="utf-8"))
    value["effective_floor_pass"] = False
    receipt.unlink()

    def refused(argv, **kwargs):
        out = Path(argv[argv.index("--out") + 1])
        out.write_text(json.dumps(value), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runner.subprocess, "run", refused)
    with pytest.raises(runner.ResourceAdmissionError, match="refused"):
        runner.assess_run(receipt)


def test_all_atomic_writers_observe_flushed_temporary_bytes(tmp_path):
    observed = []
    artifacts.set_atomic_scratch_observer(
        lambda path: observed.append((path.name, path.stat().st_size)),
    )
    try:
        artifacts._atomic_create(tmp_path / "artifact.bin", b"abc")
        source_manifest.write_source_manifest(tmp_path / "manifest.json")
        runner._atomic_create_json(tmp_path / "receipt.json", {"complete": True})
    finally:
        artifacts.set_atomic_scratch_observer(None)
    assert len(observed) == 3
    assert observed[0][1] == 3
    assert all(size > 0 for _, size in observed)


def test_short_lived_over_ceiling_atomic_temp_is_retained_and_terminal_invalid(
    tmp_path, monkeypatch
):
    root = tmp_path / "replacement"
    root.mkdir()
    _bind_canonical(monkeypatch, root)
    tracker = runner._InvocationScratchTracker(root)
    tracker.scientific_state_started = True
    monkeypatch.setattr(runner, "_ACTIVE_SCRATCH_TRACKER", tracker)
    monkeypatch.setattr(runner, "_peak_working_set_bytes", lambda: 1)
    artifacts.set_atomic_scratch_observer(tracker.observe)
    transient = root / "short-lived.bin"
    try:
        artifacts._atomic_create(transient, b"x" * (64 * 1024**2 + 1))
        transient.unlink()
        with pytest.raises(runner.ResourceAdmissionError, match="scratch_bytes_exceeded"):
            runner._enforce_direction_resources(
                stage="post-work", root=root, scratch_root=None,
                started_at=runner.time.perf_counter(), terminal_on_failure=True,
            )
    finally:
        artifacts.set_atomic_scratch_observer(None)
        monkeypatch.setattr(runner, "_ACTIVE_SCRATCH_TRACKER", None)
    invalid = json.loads((root / "invalid-evidence.json").read_text(encoding="utf-8"))
    assert invalid["resource_assessment"]["attempt_cumulative_scratch_peak_bytes"] > 64 * 1024**2


def test_post_work_observer_failure_creates_sibling_invalid_and_refuses_reentry(
    tmp_path, monkeypatch
):
    root = tmp_path / "replacement"
    _bind_canonical(monkeypatch, root)
    tracker = runner._InvocationScratchTracker(root)
    tracker.scientific_state_started = True
    artifacts.set_atomic_scratch_observer(tracker.observe)
    try:
        with pytest.raises(runner.ResourceAdmissionError, match="observation failed"):
            tracker.observe(tmp_path / "missing.tmp")
    finally:
        artifacts.set_atomic_scratch_observer(None)
    sibling = root.parent / f".{root.name}.invalid-evidence.json"
    assert sibling.exists() and not root.exists()
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: pytest.fail("invalid sibling must precede preflight"),
    )
    with pytest.raises(runner.PreflightError, match=r"\.3 consumed, no fresh/resume/reload/continuation"):
        runner.run_result(manifest=tmp_path / "unused.json", result_root=root)
