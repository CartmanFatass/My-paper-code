from __future__ import annotations

from dataclasses import fields, replace
import copy
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    artifacts,
    contracts,
    foundation,
    host_bridge,
    runner,
    source_manifest,
)


def _bind_canonical(monkeypatch, root):
    monkeypatch.setattr(runner, "CANONICAL_RESULT_ROOT", root)


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
    assert contracts.MANIFEST_SCHEMA == "SCDMP_FCEOV_MANIFEST_V3"
    assert artifacts.CHECKPOINT_SCHEMA == "SCDMP_FCEOV_CHECKPOINT_V3"
    assert contracts.CHECKPOINT_UPDATE == 160
    assert artifacts.FOUNDATION_GATE_SCHEMA == "SCDMP_FCEOV_FOUNDATION_GATE_V3"
    assert artifacts.PANEL_SCHEMA == "SCDMP_FCEOV_COMPLETE_2X3_RESULT_V3"
    assert artifacts.TERMINAL_FACT_SCHEMA == "SCDMP_FCEOV_TERMINAL_V3"

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


def test_preflight_is_result_blind_ready_and_rejects_existing_result_root(
    tmp_path, monkeypatch
):
    manifest = tmp_path / "manifest.json"
    source_manifest.write_source_manifest(manifest)
    monkeypatch.setattr(runner, "verify_public_alias", lambda: (b"same", b"same"))
    monkeypatch.setattr(
        runner,
        "headroom_conformance",
        lambda: host_bridge.HeadroomConformance(
            host_bridge.HeadroomWitness(0.84, 0.94, 0.66), True, 0.06, True
        ),
    )

    result_root = tmp_path / "prospective-results"
    _bind_canonical(monkeypatch, result_root)
    report = runner.run_preflight(manifest=manifest, result_root=result_root)
    assert report["production_pipeline_implemented"] is True
    assert report["production_result_path_implemented"] is True
    assert report["result_command_status"] == "READY"
    assert report["scientific_inference_hold"] is False
    assert report["resolved_result_root"] == str(result_root.resolve())
    assert report["training_episodes"] == 1_920
    assert report["panel_width"] == report["reset_width"] == 3_372
    assert report["native_session_widths"] == (144,) * 23 + (60,)
    assert result_root.exists() is False

    result_root.mkdir()
    with pytest.raises(runner.PreflightError, match="exist"):
        runner.run_preflight(manifest=manifest, result_root=result_root)


def test_cli_accepts_preflight_and_only_the_exact_frozen_result_phase(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "manifest.json"
    source_manifest.write_source_manifest(manifest)
    result_root = tmp_path / "never-created"
    monkeypatch.setattr(
        runner,
        "run_preflight",
        lambda **kwargs: {"production_result_path_implemented": True},
    )
    terminal = contracts.TerminalFact(
        artifacts.TERMINAL_FACT_SCHEMA,
        contracts.Disposition.FOUNDATION_NONPASS.value,
        foundation.analyze_competence(tuple(
            foundation.CompetenceRecord(row.mission, row.graph, True, False)
            for row in foundation.competence_inventory()
        )),
        False,
    )

    assert runner.main(
        ["--preflight-only", "--manifest", str(manifest), "--result-root", str(result_root)]
    ) == 0
    preflight_stdout = capsys.readouterr().out
    assert preflight_stdout == '{"production_result_path_implemented":true}\n'
    assert json.loads(preflight_stdout) == {"production_result_path_implemented": True}
    assert not result_root.exists()

    monkeypatch.setattr(runner, "run_result", lambda **kwargs: terminal)
    assert runner.main([
        "--phase", "FOUNDATION_AND_2X3", "--manifest", str(manifest),
        "--result-root", str(result_root),
    ]) == 0
    assert terminal.disposition in capsys.readouterr().out
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


def test_result_orchestration_uses_one_final_checkpoint_restore_and_stops_before_panel_on_nonpass(
    tmp_path, monkeypatch
):
    updates = []
    preflight_calls = []
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: preflight_calls.append(kwargs) or {
            "resources": dict(contracts.RESOURCE_MAXIMA), "production_result_path_implemented": True,
            "resource_envelope": dict(contracts.RESOURCE_ENVELOPE),
        },
    )
    admissions = []
    monkeypatch.setattr(runner, "admit_memory", lambda path: admissions.append(path) or {"passed": True})
    monkeypatch.setattr(runner, "fresh_master", lambda: bytes(range(32)))

    def cheap_update(model, optimizer, source, *, update):
        optimizer.step_index = update * 12
        updates.append(update)
        return SimpleNamespace(update=update, episodes_complete=12)

    monkeypatch.setattr(runner, "train_one_update", cheap_update)
    records = tuple(
        foundation.CompetenceRecord(row.mission, row.graph, True, False)
        for row in foundation.competence_inventory()
    )
    monkeypatch.setattr(runner, "execute_native_competence", lambda frozen, source: records)
    monkeypatch.setattr(
        runner, "execute_native_panel_slice",
        lambda *args: pytest.fail("panel must not execute after a competence nonpass"),
    )
    root = tmp_path / "fresh-result"
    _bind_canonical(monkeypatch, root)
    manifest = tmp_path / "manifest.json"
    source_manifest.write_source_manifest(manifest)
    def passing_direction_resources(**kwargs):
        scratch_root = kwargs.get("scratch_root")
        scratch_bytes = (
            scratch_root.stat().st_size
            if scratch_root is not None and scratch_root.is_file()
            else 0
        )
        value = {
            "schema": runner._DIRECTION_RESOURCE_SCHEMA,
            "stage": kwargs["stage"],
            "passed": True,
            "failure_reasons": [],
            "scratch_bytes": scratch_bytes,
        }
        receipt = kwargs.get("receipt")
        if receipt is not None:
            receipt.write_text(json.dumps(value), encoding="utf-8")
        return value

    monkeypatch.setattr(runner, "_enforce_direction_resources", passing_direction_resources)
    fact = runner._execute_result_pipeline(manifest=manifest, result_root=root)
    assert preflight_calls == [{"manifest": manifest, "result_root": root}]
    assert len(admissions) == 1
    assert updates == list(range(1, 161))
    assert fact.disposition == contracts.Disposition.FOUNDATION_NONPASS.value
    assert (root / "rng-master.bin").stat().st_size == 32
    witness = json.loads((root / "resume-witness.json").read_text())
    assert witness["checkpoint_update"] == 160 and witness["optimizer_step"] == 1920
    assert witness["continuation_stage"] == "COMPETENCE"
    assert len(list(root.glob("*.checkpoint.pt"))) == 1
    runtime = json.loads((root / "run-record.json").read_text())["runtime"]
    assert runtime["device"] == "cpu"
    assert runtime["torch_threads"] == 1
    assert runtime["torch_interop_threads"] == 1
    assert runtime["deterministic_algorithms"] is True
    assert not (root / "complete-2x3-panel.json").exists()

    monkeypatch.setattr(
        runner, "materialize_foundation",
        lambda *args, **kwargs: pytest.fail("terminal reentry must not materialize a model"),
    )
    monkeypatch.setattr(
        runner, "load_checkpoint",
        lambda *args, **kwargs: pytest.fail("terminal reentry must not load a checkpoint"),
    )
    monkeypatch.setattr(
        runner, "load_contiguous_panel_slices",
        lambda *args, **kwargs: pytest.fail("terminal reentry must not load panel cells"),
    )
    monkeypatch.setattr(
        runner, "fresh_master",
        lambda: pytest.fail("terminal reentry must not generate a master"),
    )
    assert runner.run_result(manifest=manifest, result_root=root) == fact

    terminal_path = root / "terminal-fact.json"
    tampered = json.loads(terminal_path.read_text(encoding="utf-8"))
    tampered["disposition"] = contracts.Disposition.CLOSED.value
    terminal_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(artifacts.ArtifactContractError):
        runner.run_result(manifest=manifest, result_root=root)


def test_resource_refusal_precedes_root_master_training_or_artifact(
    tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: calls.append("preflight") or {
            "resources": dict(contracts.RESOURCE_MAXIMA),
            "resource_envelope": dict(contracts.RESOURCE_ENVELOPE),
        },
    )
    monkeypatch.setattr(
        runner, "admit_memory",
        lambda path: (_ for _ in ()).throw(runner.ResourceAdmissionError("refused")),
    )
    monkeypatch.setattr(runner, "fresh_master", lambda: pytest.fail("master must not be generated"))
    monkeypatch.setattr(runner, "train_one_update", lambda *args, **kwargs: pytest.fail("training must not start"))
    root = tmp_path / "held-result"
    _bind_canonical(monkeypatch, root)
    with pytest.raises(runner.ResourceAdmissionError, match="refused"):
        runner.run_result(manifest=tmp_path / "manifest.json", result_root=root)
    assert calls == ["preflight"]
    assert not root.exists()


def test_passing_route_publishes_only_after_all_slices_and_resume_reuses_master(
    tmp_path, monkeypatch
):
    updates = []
    preflight_calls = []
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: preflight_calls.append(kwargs) or {
            "resources": dict(contracts.RESOURCE_MAXIMA),
            "resource_envelope": dict(contracts.RESOURCE_ENVELOPE),
        },
    )
    master_calls = []
    monkeypatch.setattr(
        runner, "fresh_master", lambda: master_calls.append("master") or bytes(range(32)),
    )
    monkeypatch.setattr(runner, "admit_memory", lambda path: {"passed": True})

    def cheap_update(model, optimizer, source, *, update):
        optimizer.step_index = update * 12
        updates.append(update)
        return SimpleNamespace(update=update, episodes_complete=12)

    monkeypatch.setattr(runner, "train_one_update", cheap_update)
    records = tuple(
        foundation.CompetenceRecord(row.mission, row.graph, True, True)
        for row in foundation.competence_inventory()
    )
    monkeypatch.setattr(runner, "execute_native_competence", lambda frozen, source: records)
    monkeypatch.setattr(
        runner, "materialize_disturbance_tapes",
        lambda source, *, start_tape, tape_count: (start_tape, tape_count),
    )
    panel_calls = []

    def cells_for_slice(frozen, tapes, panel_slice):
        panel_calls.append(panel_slice.index)
        if panel_slice.index == 1 and panel_calls.count(1) == 1:
            raise RuntimeError("technical interruption")
        return tuple(
            contracts.PanelCell(
                lane.tape, lane.graph, lane.action_name, lane.action_index,
                True, False, None,
            )
            for lane in panel_slice.lanes
        )

    monkeypatch.setattr(
        runner, "execute_native_panel_slice", cells_for_slice,
    )
    root = tmp_path / "passing-wiring"
    _bind_canonical(monkeypatch, root)
    manifest = tmp_path / "manifest.json"
    source_manifest.write_source_manifest(manifest)

    def passing_direction_resources(**kwargs):
        scratch_root = kwargs.get("scratch_root")
        scratch_bytes = (
            scratch_root.stat().st_size
            if scratch_root is not None and scratch_root.is_file()
            else 0
        )
        value = {
            "schema": runner._DIRECTION_RESOURCE_SCHEMA,
            "stage": kwargs["stage"],
            "passed": True,
            "failure_reasons": [],
            "scratch_bytes": scratch_bytes,
        }
        receipt = kwargs.get("receipt")
        if receipt is not None:
            receipt.write_text(json.dumps(value), encoding="utf-8")
        return value

    monkeypatch.setattr(runner, "_enforce_direction_resources", passing_direction_resources)
    with pytest.raises(RuntimeError, match="technical interruption"):
        runner._execute_result_pipeline(manifest=manifest, result_root=root)
    assert preflight_calls == [{"manifest": manifest, "result_root": root}]
    assert updates == list(range(1, 161))
    assert panel_calls == [0, 1]
    assert json.loads((root / "panel-frontier.json").read_text())["completed_slices"] == 1
    assert len(list(root.glob("panel-slice-*.json"))) == 1
    assert not (root / "final-bundle.json").exists()
    assert not (root / "terminal-fact.json").exists()

    monkeypatch.setattr(
        runner, "admit_memory",
        lambda path: (_ for _ in ()).throw(runner.ResourceAdmissionError("resume refused")),
    )
    with pytest.raises(runner.ResourceAdmissionError, match="resume refused"):
        runner.run_result(manifest=manifest, result_root=root)
    assert json.loads((root / "panel-frontier.json").read_text())["completed_slices"] == 1
    assert len(list(root.glob("panel-slice-*.json"))) == 1

    monkeypatch.setattr(runner, "admit_memory", lambda path: {"passed": True})
    fact = runner.run_result(manifest=manifest, result_root=root)
    assert fact.disposition == contracts.Disposition.CLOSED.value
    assert master_calls == ["master"]
    assert panel_calls.count(0) == 1
    assert panel_calls.count(1) == 2
    assert len(list(root.glob("panel-slice-*.json"))) == contracts.PANEL_SLICE_COUNT
    assert json.loads((root / "panel-frontier.json").read_text())["completed_slices"] == 24
    assert (root / "final-bundle.json").exists()

    monkeypatch.setattr(runner, "fresh_master", lambda: pytest.fail("complete load cannot create a master"))
    assert runner.run_result(manifest=manifest, result_root=root) == fact


def test_internal_execution_reruns_direct_preflight_and_rejects_resource_drift(tmp_path, monkeypatch):
    root = tmp_path / "bound-root"
    _bind_canonical(monkeypatch, root)
    manifest = tmp_path / "manifest.json"
    calls = []
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: calls.append(kwargs) or {"resources": {}},
    )
    monkeypatch.setattr(runner, "fresh_master", lambda: pytest.fail("master must follow valid preflight"))
    with pytest.raises(runner.PreflightError, match="resource report differs"):
        runner._execute_result_pipeline(manifest=manifest, result_root=root)
    assert calls == [{"manifest": manifest, "result_root": root}]
    assert not root.exists()


@pytest.mark.parametrize("existing_shape", ("absent", "partial", "complete", "resource-fail"))
def test_noncanonical_root_is_rejected_before_any_content_or_resource_access(
    tmp_path, monkeypatch, existing_shape
):
    canonical = tmp_path / "canonical"
    noncanonical = tmp_path / f"other-{existing_shape}"
    _bind_canonical(monkeypatch, canonical)
    if existing_shape != "absent":
        noncanonical.mkdir()
        if existing_shape == "complete":
            (noncanonical / "final-bundle.json").write_text("{}", encoding="utf-8")
        elif existing_shape == "resource-fail":
            (noncanonical / "invalid-evidence.json").write_text("{}", encoding="utf-8")
        else:
            (noncanonical / "rng-master.bin").write_bytes(b"partial")
    monkeypatch.setattr(
        runner, "run_preflight",
        lambda **kwargs: pytest.fail("noncanonical root must precede preflight"),
    )
    monkeypatch.setattr(
        runner, "admit_memory",
        lambda *args, **kwargs: pytest.fail("noncanonical root must precede resources"),
    )
    monkeypatch.setattr(
        runner, "fresh_master",
        lambda: pytest.fail("noncanonical root must precede master generation"),
    )
    with pytest.raises(runner.PreflightError, match="sole canonical"):
        runner.run_result(manifest=tmp_path / "manifest.json", result_root=noncanonical)


def test_existing_root_without_direct_snapshot_rejects_before_master_checkpoint_or_cells(
    tmp_path, monkeypatch
):
    root = tmp_path / "canonical-old-shape"
    _bind_canonical(monkeypatch, root)
    root.mkdir()
    for name in ("source-manifest.json", "rng-master.bin", "run-record.json"):
        (root / name).write_bytes(b"legacy")
    monkeypatch.setattr(
        runner, "load_rng_master",
        lambda *args, **kwargs: pytest.fail("old shape must precede master read"),
    )
    monkeypatch.setattr(
        runner, "load_checkpoint",
        lambda *args, **kwargs: pytest.fail("old shape must precede checkpoint read"),
    )
    monkeypatch.setattr(
        runner, "load_contiguous_panel_slices",
        lambda *args, **kwargs: pytest.fail("old shape must precede cell read"),
    )
    with pytest.raises(runner.PreflightError, match="direct V3 shape"):
        runner.run_result(manifest=tmp_path / "manifest.json", result_root=root)


@pytest.mark.parametrize(
    "failed_seam",
    ("rng-master", "source-manifest", "source-native-snapshot", "run-record", "resource-assessment"),
)
def test_fresh_staging_init_recovers_every_post_master_seam_with_same_master(
    tmp_path, monkeypatch, failed_seam
):
    root = tmp_path / f"canonical-{failed_seam}"
    _bind_canonical(monkeypatch, root)
    manifest = tmp_path / "manifest.json"
    source_manifest.write_source_manifest(manifest)
    runner._configure_numerical_runtime()
    calls = []
    expected_master = bytes(range(32))
    monkeypatch.setattr(
        runner, "fresh_master", lambda: calls.append("fresh") or expected_master,
    )
    monkeypatch.setattr(
        runner, "_enforce_direction_resources", lambda **kwargs: {"passed": True},
    )
    failed = {"value": False}

    def fail_once(name):
        if name == failed_seam and not failed["value"]:
            failed["value"] = True
            raise RuntimeError(f"init seam {name}")

    monkeypatch.setattr(runner, "_init_seam", fail_once)
    with pytest.raises(RuntimeError, match="init seam"):
        runner._initialize_fresh_root(
            manifest=manifest, root=root, started_at=runner.time.perf_counter(),
        )
    staging = runner._staging_root(root)
    assert not root.exists()
    assert (staging / "rng-master.bin").read_bytes() == expected_master

    monkeypatch.setattr(runner, "_init_seam", lambda name: None)
    master, _, _ = runner._initialize_fresh_root(
        manifest=manifest, root=root, started_at=runner.time.perf_counter(),
    )
    assert master == expected_master
    assert calls == ["fresh"]
    assert root.is_dir() and not staging.exists()


def test_staged_final_resource_overrun_writes_invalid_fact_before_canonical_publication(
    tmp_path, monkeypatch
):
    root = tmp_path / "canonical-resource-overrun"
    root.mkdir()
    encoded_size = 65 * 1024**2
    prepared = SimpleNamespace(encoded_size=encoded_size, encoded=b"staged-final")
    monkeypatch.setattr(runner, "prepare_final_bundle", lambda **kwargs: prepared)
    observed = []

    def assessment(**kwargs):
        observed.append(kwargs)
        failed = kwargs["scratch_root"] == root / "final-bundle.pending.json"
        return {
            "schema": runner._DIRECTION_RESOURCE_SCHEMA,
            "passed": not failed,
            "failure_reasons": ["durable_bytes_exceeded"] if failed else [],
        }

    monkeypatch.setattr(runner, "_direction_resource_assessment", assessment)
    staged = []

    def write_staged(path, value):
        assert value is prepared
        assert path == root / "final-bundle.pending.json"
        path.write_bytes(value.encoded)
        staged.append(path)

    monkeypatch.setattr(runner, "write_prepared_final_bundle", write_staged)
    with pytest.raises(runner.ResourceAdmissionError, match="pre-final-publication"):
        runner._prepare_and_publish_final(
            root=root, master=bytes(range(32)), run_record_bytes=b"record",
            source_snapshot=object(), records=(), cells=(), panel_analysis=object(),
            started_at=runner.time.perf_counter(),
        )
    assert staged == [root / "final-bundle.pending.json"]
    assert observed[-1]["scratch_root"] == root / "final-bundle.pending.json"
    assert (root / "final-bundle.pending.json").read_bytes() == prepared.encoded
    assert not (root / "final-bundle.json").exists()
    invalid = json.loads((root / "invalid-evidence.json").read_text(encoding="utf-8"))
    assert invalid["disposition"] == "INVALID_EVIDENCE"
    assert invalid["scientific_polarity"] is False
    assert not runner._contains_forbidden_receipt_key(invalid)


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
        runner.PreflightError, match="terminal invalid evidence forbids resume or final publication"
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
