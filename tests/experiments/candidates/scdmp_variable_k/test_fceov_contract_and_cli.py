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
        "episodes_rollouts": 2_184,
        "primitive_slots": 794_976,
        "adamw_steps": 1_920,
        "checkpoints": 1,
        "forced_actions": 144,
        "foundation_queries": 61_008,
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
    assert contracts.MANIFEST_SCHEMA == "SCDMP_FCEOV_MANIFEST_V2"
    assert artifacts.CHECKPOINT_SCHEMA == "SCDMP_FCEOV_CHECKPOINT_V2"
    assert contracts.CHECKPOINT_UPDATE == 160
    assert artifacts.FOUNDATION_GATE_SCHEMA == "SCDMP_FCEOV_FOUNDATION_GATE_V2"
    assert artifacts.PANEL_SCHEMA == "SCDMP_FCEOV_COMPLETE_2X3_RESULT_V1"
    assert artifacts.TERMINAL_FACT_SCHEMA == "SCDMP_FCEOV_TERMINAL_V2"

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


def test_preflight_has_no_result_route_or_files_and_rejects_existing_result_root(
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
    report = runner.run_preflight(manifest=manifest, result_root=result_root)
    assert report["production_pipeline_implemented"] is True
    assert report["production_result_path_implemented"] is False
    assert report["result_command_status"] == "SCIENTIFIC_INFERENCE_HOLD"
    assert report["scientific_inference_hold"] is True
    assert report["resolved_result_root"] == str(result_root.resolve())
    assert report["training_episodes"] == 1_920
    assert report["panel_width"] == report["reset_width"] == 144
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

    assert runner.main(
        ["--preflight-only", "--manifest", str(manifest), "--result-root", str(result_root)]
    ) == 0
    preflight_stdout = capsys.readouterr().out
    assert preflight_stdout == '{"production_result_path_implemented":true}\n'
    assert json.loads(preflight_stdout) == {"production_result_path_implemented": True}
    assert not result_root.exists()

    assert runner.main([
        "--phase", "FOUNDATION_AND_2X3", "--manifest", str(manifest),
        "--result-root", str(result_root),
    ]) == 1
    assert "SCIENTIFIC_INFERENCE_HOLD" in capsys.readouterr().err
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
        },
    )
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
        runner, "execute_native_panel",
        lambda *args: pytest.fail("panel must not execute after a competence nonpass"),
    )
    root = tmp_path / "fresh-result"
    manifest = tmp_path / "manifest.json"
    fact = runner._execute_result_pipeline(manifest=manifest, result_root=root)
    assert preflight_calls == [{"manifest": manifest, "result_root": root}]
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


def test_public_result_phase_holds_after_preflight_before_root_master_training_or_artifact(
    tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: calls.append("preflight") or {
            "resources": dict(contracts.RESOURCE_MAXIMA)
        },
    )
    monkeypatch.setattr(runner, "fresh_master", lambda: pytest.fail("master must not be generated"))
    monkeypatch.setattr(runner, "train_one_update", lambda *args, **kwargs: pytest.fail("training must not start"))
    root = tmp_path / "held-result"
    with pytest.raises(runner.ScientificInferenceHold, match="SCIENTIFIC_INFERENCE_HOLD"):
        runner.run_result(manifest=tmp_path / "manifest.json", result_root=root)
    assert calls == ["preflight"]
    assert not root.exists()


def test_internal_passing_route_stops_after_raw_panel_before_analysis_or_publication(
    tmp_path, monkeypatch
):
    assert not hasattr(runner, "analyze_complete_panel")
    assert not hasattr(runner, "write_complete_panel")
    updates = []
    preflight_calls = []
    monkeypatch.setattr(
        runner, "run_preflight", lambda **kwargs: preflight_calls.append(kwargs) or {
            "resources": dict(contracts.RESOURCE_MAXIMA)
        },
    )
    monkeypatch.setattr(runner, "fresh_master", lambda: bytes(range(32)))

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
    monkeypatch.setattr(runner, "materialize_disturbance_tapes", lambda source: ("raw-tapes",))
    raw_cells = tuple(
        contracts.PanelCell(
            tape, graph, action, {"COMMON": 0, "A_HR": 10, "A_RH": 12}[action],
            True, False, None,
        )
        for tape in range(24)
        for graph in contracts.GRAPHS
        for action in contracts.CANDIDATE_ACTIONS
    )
    panel_calls = []
    monkeypatch.setattr(
        runner,
        "execute_native_panel",
        lambda frozen, tapes: panel_calls.append(tapes) or raw_cells,
    )
    terminal_calls = []
    monkeypatch.setattr(
        runner,
        "write_terminal_fact",
        lambda *args, **kwargs: terminal_calls.append((args, kwargs)),
    )
    root = tmp_path / "passing-wiring"
    manifest = tmp_path / "manifest.json"
    with pytest.raises(runner.ScientificInferenceHold, match="raw 144-cell panel completed"):
        runner._execute_result_pipeline(manifest=manifest, result_root=root)
    assert preflight_calls == [{"manifest": manifest, "result_root": root}]
    assert updates == list(range(1, 161))
    assert panel_calls == [("raw-tapes",)]
    assert terminal_calls == []
    assert not (root / "complete-2x3-panel.json").exists()
    assert not (root / "terminal-fact.json").exists()


def test_internal_execution_reruns_direct_preflight_and_rejects_resource_drift(tmp_path, monkeypatch):
    root = tmp_path / "bound-root"
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
