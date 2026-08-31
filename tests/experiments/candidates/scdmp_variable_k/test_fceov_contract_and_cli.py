from __future__ import annotations

from dataclasses import fields, replace
import copy
from types import SimpleNamespace

import pytest

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    artifacts,
    contracts,
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


def test_structural_schema_names_and_direct_manifest_are_exact(tmp_path):
    assert contracts.MANIFEST_SCHEMA == "SCDMP_FCEOV_MANIFEST_V1"
    assert artifacts.CHECKPOINT_SCHEMA == "SCDMP_FCEOV_CHECKPOINT_V1"
    assert artifacts.FOUNDATION_GATE_SCHEMA == "SCDMP_FCEOV_FOUNDATION_GATE_V1"
    assert artifacts.PANEL_SCHEMA == "SCDMP_FCEOV_COMPLETE_2X3_RESULT_V1"
    assert artifacts.TERMINAL_FACT_SCHEMA == "SCDMP_FCEOV_TERMINAL_V1"

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
    assert report["production_result_path_implemented"] is False
    assert report["training_episodes"] == 1_920
    assert report["panel_width"] == report["reset_width"] == 144
    assert result_root.exists() is False

    result_root.mkdir()
    with pytest.raises(runner.PreflightError, match="exist"):
        runner.run_preflight(manifest=manifest, result_root=result_root)


def test_cli_accepts_only_preflight_and_explicitly_refuses_every_phase(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "manifest.json"
    source_manifest.write_source_manifest(manifest)
    result_root = tmp_path / "never-created"
    monkeypatch.setattr(
        runner,
        "run_preflight",
        lambda **kwargs: {"production_result_path_implemented": False},
    )

    assert runner.main(
        ["--preflight-only", "--manifest", str(manifest), "--result-root", str(result_root)]
    ) == 0
    assert "result-blind preflight passed" in capsys.readouterr().out
    assert not result_root.exists()

    for phase in ("FOUNDATION_AND_2X3", "FOUNDATION", "ASSAY", "anything"):
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
    assert "--phase" not in help_text
