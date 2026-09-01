from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timezone
import inspect
import hashlib
import json
from pathlib import Path

import pytest
import torch

import scripts.run_vnfc_bpcr_b_explore as subject


NOW = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


class Sink:
    schema = subject.TELEMETRY_SCHEMA
    fields = tuple(subject.REQUIRED_TELEMETRY_FIELDS)

    def emit(self, payload: object) -> None:
        self.payload = payload


def receipt(**updates: object) -> dict[str, object]:
    value = {
        "schema_version": 1,
        "captured_at": "2026-09-01T11:59:00Z",
        "assessed_at": "2026-09-01T11:59:01Z",
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 6 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
    }
    value.update(updates)
    return value


def telemetry(**updates: object) -> dict[str, object]:
    value = {field: 1 for field in subject.REQUIRED_TELEMETRY_FIELDS}
    value.update({
        "telemetry_schema": subject.TELEMETRY_SCHEMA, "telemetry_terminal": True,
        "stage_wall_seconds": {stage: 1.0 for stage in ("source_binding", "training", "evaluation", "serialization")},
        "stage_cpu_seconds": {stage: 1.0 for stage in ("source_binding", "training", "evaluation", "serialization")},
        "available_physical_bytes": 6 * 1024**3, "effective_available_bytes": 5 * 1024**3,
        "parameter_count_by_arm": {arm: 1 for arm in subject.ARMS},
        "forward_calls_by_arm": {arm: 1 for arm in subject.ARMS},
        "backward_calls_by_arm": {arm: 1 for arm in subject.ARMS},
        "flop_exposure_by_arm": {arm: 1 for arm in subject.ARMS},
        "primary_host_calls": 1, "shadow_host_calls": 1, "total_host_call_multiplier": 2.0,
    })
    value.update(updates)
    return value


def bound_telemetry(terminal: dict[str, object], **updates: object) -> dict[str, object]:
    exposure = terminal["exposure"]; training = terminal["training"]
    value = telemetry(
        parameter_count_by_arm={arm: training[arm]["parameter_count"] for arm in subject.ARMS},
        forward_calls_by_arm={arm: exposure["training"][arm]["action_selection_forward_calls"] + exposure["training"][arm]["optimizer_forward_calls"] + exposure["evaluation"][arm]["policy_forward_calls"] + exposure["evaluation"][arm]["diagnostic_forward_calls"] for arm in subject.ARMS},
        backward_calls_by_arm={arm: exposure["training"][arm]["backward_calls"] for arm in subject.ARMS},
    )
    value.update(updates); return value


def shadow_receipt(batch_id: str) -> dict[str, object]:
    digest = lambda label: hashlib.sha256(label.encode()).hexdigest()
    source = {"included_source_identity": {"source": digest("source")}, "shadow_build_key": digest("build"), "shadow_embedded_build_key": digest("build"), "shadow_artifact_path": "shadow.dll", "shadow_artifact_sha256": digest("shadow"), "primary_artifact_path": "primary.dll", "primary_artifact_sha256": digest("primary"), "primary_registered_build_key": digest("primary-build")}
    boundaries = tuple({"boundary_index": index, "command_digest": digest(f"command-{index}"), "cumulative_action_digest": digest(f"cumulative-{index}"), "primary_full_output_digest": digest(f"output-{index}"), "shadow_full_output_digest": digest(f"output-{index}"), "exact": True, "primary_integrated_ticks": tuple([140 + 20 * index] * 8), "shadow_integrated_ticks": tuple([140 + 20 * index] * 8), "shadow_ticks_per_session": (20,) * 8, "shadow_tick_rows_digest": digest(f"ticks-{index}"), "source_exact_pre_post": True} for index in range(6))
    paired = {"schema": "VNFC-BEXP-PAIRED-PRIMARY-SHADOW-RECEIPT-v1", "input_digest": digest("input"), "action_digest": boundaries[-1]["cumulative_action_digest"], "width": 8, "main_return_source": "registered_r09_native_interactive_primary", "shadow_role": "telemetry_only_no_action_or_return_authority", "initial": {"primary_full_output_digest": digest("initial"), "shadow_full_output_digest": digest("initial"), "exact": True}, "source_pre": source, "source_post": dict(source), "boundaries": boundaries}
    raw_ticks = tuple({"integrated_ticks": index + 1} for index in range(120))
    recovery = {"observation_scope": "fresh_b_shadow_direct", "primary_rollout_applicability": "inference_only_after_exact_same-input/action boundary equivalence", "first_failed_zone_service_time_seconds": 0, "failed_zone_executor_reacquisition_time_seconds": 1, "failed_zone_zero_service_seconds_0_60": 2, "observed_failed_zone_seconds_0_60": 60, "complete_0_60": True, "raw_tick_rows": raw_ticks}
    final_shadow = tuple({"interactive": {"terminal": True}, "tick_rows": tuple({"integrated_ticks": 101 + index} for index in range(20)), "receipt": dict(recovery)} for _ in range(8))
    return subject.build_shadow_receipt(batch_id, paired, final_shadow)


def configs() -> tuple[subject.BExploreRunConfig, ...]:
    return (
        subject.BExploreRunConfig(subject.DEBUG_STAGE, subject.DEBUG_SEED, 8),
        *(subject.BExploreRunConfig(subject.PRIMARY_STAGE, seed, 64) for seed in subject.PRIMARY_SEEDS),
        subject.BExploreRunConfig(subject.OPTIONAL_STAGE, subject.OPTIONAL_SEEDS[0], 64, "training_variance", "N3_N5_TRAINING_ONLY"),
        subject.BExploreRunConfig(subject.OPTIONAL_STAGE, subject.OPTIONAL_SEEDS[1], 64, "technical_issue", "TECHNICAL_PRE_N7"),
    )


def checkpoint_artifact(config: subject.BExploreRunConfig) -> dict[str, object]:
    digest = "c" * 64
    return {"schema": "VNFC_BPCR_BEXP_R01_CHECKPOINT_MANIFEST_V1", "namespace": config.namespace, "bundle_filename": "CHECKPOINTS.bin", "bundle_sha256": digest, "bundle_size": 1, "checkpoint_identities": {arm: {label: digest for label in subject.CHECKPOINTS} for arm in subject.ARMS}, "contents": [{"arm": "MAPR", "checkpoint": "initial", "name": "p", "dtype": "float64", "shape": [1], "bytes": 8, "sha256": digest}], "manifest_filename": "CHECKPOINTS_MANIFEST.json", "manifest_sha256": digest}


def durable_checkpoint_artifact(root: Path, config: subject.BExploreRunConfig) -> dict[str, object]:
    checkpoints = {}
    for arm_index, arm in enumerate(subject.ARMS):
        checkpoints[arm] = {}
        for label_index, label in enumerate(subject.CHECKPOINTS):
            model = torch.nn.Linear(2, 1, dtype=torch.float64)
            with torch.no_grad(): model.weight.fill_(arm_index + label_index + 1); model.bias.fill_(label_index)
            checkpoints[arm][label] = subject.clone_checkpoint(model, label)
    return subject._serialize_checkpoint_bundle_once(root, config, checkpoints)


def runtime_terminal(config: subject.BExploreRunConfig, artifact: dict[str, object] | None = None) -> dict[str, object]:
    counts = subject.expected_counts(config)
    receipt_index = 0
    def next_receipt() -> dict[str, object]:
        nonlocal receipt_index
        value = shadow_receipt(f"batch-{receipt_index}"); receipt_index += 1; return value
    loss = {"actor_loss": 0.0, "critic_loss": 0.0, "entropy_loss": 0.0, "total_loss": 0.0, "preclip_gradient_norm": 0.0, "policy_entropy": 0.0}
    training = {}
    for arm in subject.ARMS:
        updates = tuple({"episodes": 16, "joint_transitions": 96, "optimizer_steps": 16, "training_action_forward_calls": 12, "optimizer_forward_calls": 384, "backward_calls": 16, "finite_values": True, "training_J_ext": (0.5,) * 16, "return_variance": 0.0, "advantage_variance": 0.0, "loss_rows": tuple(dict(loss) for _ in range(16)), "shadow_receipts": (next_receipt(), next_receipt()), "nonfinite_update_count": 0} for _ in range(config.updates))
        training[arm] = {"updates": config.updates, "episodes": counts["training_episodes_per_arm"], "joint_transitions": counts["joint_transitions_per_arm"], "optimizer_steps": counts["optimizer_steps_per_arm"], "parameter_count": 1, "training_action_forward_calls": 12 * config.updates, "optimizer_forward_calls": 384 * config.updates, "backward_calls": 16 * config.updates, "finite_values": True, "nonfinite_update_count": 0, "updates_telemetry": updates}
    learned = []
    checkpoints = ("final",) if config.stage == subject.DEBUG_STAGE else subject.CHECKPOINTS
    endpoint = {"fail_endpoint": (1, 2), "total_endpoint": (3, 4), "intact_endpoint": (2, 3)}
    for n in subject.ROSTERS:
        for zone in subject.ZONES:
            for label in checkpoints:
                for arm in subject.ARMS:
                    n7 = n == 7; direct = arm == "DIRECT"
                    learned.append({"arm": arm, "checkpoint": label, "cell": f"N{n}z{zone}", "rollouts": 8, "relabel_mismatch_count": 0, "hard_valid": True, "finite_values": True, "evaluation_policy_forward_calls": 6, "diagnostic_forward_calls": 60 if direct else 48, "action_sensitivity": tuple({"world": row} for row in range(8)) if n7 else (), "action_sensitivity_status": "OBSERVED_TREATMENT_BLIND_N7" if n7 else "NOT_APPLICABLE_TRAIN_SUPPORT_CELL", "direct_residual_activity": tuple({"boundary": row // 8, "world_row": row % 8, "total_variation": 0.0, "physical_command_change": False} for row in range(48)) if direct else (), "endpoints": tuple(dict(endpoint) for _ in range(8)), "shadow_receipts": (next_receipt(),)})
    bcrh = tuple({"arm": "BCRH", "cell": f"N7z{zone}", "rollouts": 8, "comparison_status": "IDENTIFIED", "hard_valid": True, "finite_values": True, "evaluation_policy_forward_calls": 0, "diagnostic_forward_calls": 0, "checker_rows": tuple({"candidate_count": 1} for _ in range(48)), "endpoints": tuple(dict(endpoint) for _ in range(8)), "shadow_receipts": (next_receipt(),)} for zone in subject.ZONES)
    evaluation = {"learned": tuple(learned), "bcrh": bcrh, "rollouts": counts["evaluation_rollouts_total"], "relabel_mismatch_count": {"MAPR": 0, "DIRECT": 0}}
    receipts = tuple(receipt for arm in subject.ARMS for update in training[arm]["updates_telemetry"] for receipt in update["shadow_receipts"]) + tuple(receipt for row in (*evaluation["learned"], *evaluation["bcrh"]) for receipt in row["shadow_receipts"])
    groups = 6 if config.stage == subject.DEBUG_STAGE else 12
    exposure = {"training": {arm: {"action_selection_forward_calls": 12 * config.updates, "optimizer_forward_calls": 384 * config.updates, "backward_calls": 16 * config.updates} for arm in subject.ARMS}, "evaluation": {"MAPR": {"policy_forward_calls": 6 * groups, "diagnostic_forward_calls": 48 * groups}, "DIRECT": {"policy_forward_calls": 6 * groups, "diagnostic_forward_calls": 60 * groups}, "BCRH": {"policy_forward_calls": 0, "diagnostic_forward_calls": 0}}}
    return {
        "schema": "VNFC_BPCR_BEXP_R01_RUNTIME_TERMINAL_V1", "namespace": config.namespace,
        "counts": counts, "ps_b0_passed": True,
        "learned_relabel_mismatch_count": {"MAPR": 0, "DIRECT": 0},
        "common_host_hard_valid": True, "finite_values": True,
        "initial_final_checkpoints_retained": True, "n7_controls_frozen_before_open": True,
        "source_pre_digest": "a" * 64, "source_post_digest": "a" * 64,
        "shadow_boundary_exact": True, "shadow_source_stable": True,
        "shadow_influenced_actions": False, "observations_complete": True,
        "training_observation_rows": counts["training_episodes_total"],
        "individual_world_seed_rows": counts["evaluation_rollouts_total"],
        "optimization_rows": counts["optimizer_steps_total"],
        "bcrh_comparison_status": "IDENTIFIED",
        "shadow_receipts": receipts, "training": training, "evaluation": evaluation,
        "exploratory_readout": subject._exploratory_readout(config, evaluation),
        "exposure": exposure,
        "ps_b0_result": {"passed": True, "mismatch_by_arm": {"MAPR": 0, "DIRECT": 0}}, "bcrh_precheck_result": {"common_host_valid": True}, "checkpoint_artifact": checkpoint_artifact(config) if artifact is None else artifact,
    }


def test_exact_stage_seed_budget_and_master_derivation() -> None:
    for config in configs():
        config.validate()
        first = subject.derive_seed_master(config); second = subject.derive_seed_master(config)
        assert first == second and len(first["master"]) == 32
        assert first["external_master_override"] is False
        assert config.namespace == f"{subject.RUN_REVISION}/{config.stage}/{config.seed}"
    invalid = (
        replace(configs()[0], seed=2026090102), replace(configs()[0], updates=7),
        subject.BExploreRunConfig(subject.PRIMARY_STAGE, subject.OPTIONAL_SEEDS[0], 64),
        subject.BExploreRunConfig(subject.OPTIONAL_STAGE, subject.OPTIONAL_SEEDS[0], 64),
        subject.BExploreRunConfig(subject.OPTIONAL_STAGE, subject.OPTIONAL_SEEDS[0], 64, "training_variance", "N7_ENDPOINT"),
    )
    for config in invalid:
        with pytest.raises(subject.BExploreContractError):
            config.validate()
    assert "external_master" not in inspect.signature(subject.run_b_explore_runtime).parameters
    assert len({config.namespace for config in configs()}) == 6


def test_exact_counts_and_evaluation_allocations() -> None:
    debug = subject.expected_counts(configs()[0]); primary = subject.expected_counts(configs()[1])
    assert (debug["training_episodes_total"], debug["joint_transitions_total"], debug["optimizer_steps_total"], debug["evaluation_rollouts_total"]) == (256, 1536, 256, 112)
    assert (primary["training_episodes_total"], primary["joint_transitions_total"], primary["optimizer_steps_total"], primary["evaluation_rollouts_total"]) == (2048, 12288, 2048, 208)
    assert subject.sequence_counts()["maximum"] == {
        "training_episodes_total": 10496, "joint_transitions_total": 62976,
        "optimizer_steps_total": 10496, "evaluation_rollouts_total": 1152,
    }
    for config in configs():
        plan = subject.evaluation_plan(config)
        assert len(plan["learned"]) + len(plan["bcrh"]) == subject.expected_counts(config)["evaluation_rollouts_total"]
        assert all(row["include_candidate_records"] is False for row in plan["bcrh"])
        assert plan["n7_namespace_disjoint_from_training"] is True
        assert plan["required_relabel_mismatch_count"] == {"MAPR": 0, "DIRECT": 0}
    assert debug["ps_b0_state_comparisons_not_rollouts"] == 288


def valid_ps_b0() -> tuple[subject.PSB0Comparison, ...]:
    rows = []
    for n, zone, kind, presentation, checkpoint, arm in sorted(subject.ps_b0_expected_addresses(), key=str):
        rows.append(subject.PSB0Comparison(
            n, zone, kind, presentation, checkpoint, arm, True, True, True, True, True,
            (1, None, 3, None), (1, None, 3, None),
            kind == "diagnostic_null_tie", kind == "later_fixed_or_acquiring",
            kind == "diagnostic_null_tie", 2 if kind == "diagnostic_null_tie" else 0,
            kind == "diagnostic_null_tie",
        ))
    return tuple(rows)


def test_ps_b0_exact_cardinality_structure_and_relabel() -> None:
    assert len(subject.ps_b0_state_descriptors()) == 18
    assert len(subject.ps_b0_expected_addresses()) == 288
    result = subject.validate_ps_b0(valid_ps_b0())
    assert result == {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_V1", "descriptors": 18, "presentations": 4, "comparisons": 288, "mismatch_by_arm": {"MAPR": 0, "DIRECT": 0}, "passed": True}
    bad = list(valid_ps_b0()); bad[0] = replace(bad[0], inverse_mapped_physical_command=(None, None, None, None))
    with pytest.raises(subject.BExploreContractError, match="inverse physical-command mismatch"):
        subject.validate_ps_b0(bad)


def bcrh_rows(valid: bool = True) -> tuple[subject.BCRHPrecheckRow, ...]:
    return tuple(subject.BCRHPrecheckRow(zone, obstruction, relay, True, True, valid, True, True, 10, False) for zone in subject.ZONES for obstruction in (False, True) for relay in (False, True))


def test_bcrh_corner_precheck_is_no_records_and_comparator_local() -> None:
    assert subject.validate_bcrh_precheck(bcrh_rows())["comparison_status"] == "IDENTIFIED"
    assert subject.validate_bcrh_precheck(bcrh_rows(False)) == {"comparison_status": "NONIDENTIFIED", "common_host_valid": True, "bcrh_identified": False}
    with pytest.raises(subject.BExploreContractError, match="no candidate records"):
        subject.validate_bcrh_precheck(tuple(replace(row, include_candidate_records=True) for row in bcrh_rows()))


def test_pretraining_readiness_is_hard_fenced_before_native_for_debug_and_primary(tmp_path: Path) -> None:
    calls = []
    def native(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs); return {"schema": "injected-native"}
    for config in (configs()[0], configs()[1]):
        with pytest.raises(subject.BExploreContractError, match="REPAIR_REQUIRED"):
            subject.assess_pretraining_readiness(config, preflight_receipt=receipt(), telemetry_sink=Sink(), now=NOW, source_identity_digest="a" * 64, native_admission=native, archived_debug_result_path=tmp_path / "must-not-read.json")
    assert calls == [] and list(tmp_path.iterdir()) == []
    plan = subject._exact_readiness_plan(configs()[0])
    assert subject.IMPLEMENTATION_READY is False and plan["implementation_ready"] is False
    assert plan["repair_required"]["missing_adapter"] == "DiagnosticStateAdapter.build_support_path_state(cell, seed)"
    assert "no equal-logit state is claimed" in plan["repair_required"]["required_semantics"]
    assert plan["shadow_telemetry"]["delayed_import_module"] == "experiments.candidates.variable_n_fleet_churn_b_explore"
    assert plan["shadow_telemetry"]["apis"] == ("PairedPrimaryShadowBatch", "BNativeTelemetryBatch", "require_boundary_equivalence", "derive_recovery_telemetry")
    assert plan["shadow_telemetry"]["execution_seam"].startswith("PairedPrimaryShadowBatch only")
    assert "2x" in plan["shadow_telemetry"]["host_call_cost"]


def test_preflight_telemetry_and_shadow_fail_closed() -> None:
    with pytest.raises(subject.BExploreContractError, match="below 4 GiB"):
        subject.validate_preflight_receipt(receipt(effective_available_bytes=3 * 1024**3), now=NOW)
    with pytest.raises(subject.BExploreContractError, match="not fresh"):
        subject.validate_preflight_receipt(receipt(captured_at="2026-09-01T11:00:00Z"), now=NOW)
    sink = Sink(); sink.fields = tuple(set(sink.fields) - {"process_tree_peak_rss_bytes"})
    with pytest.raises(subject.BExploreContractError, match="lacks required"):
        subject.validate_telemetry_sink(sink)
    with pytest.raises(subject.BExploreContractError, match="unmeasured"):
        subject.validate_telemetry_payload(telemetry(process_tree_peak_rss_bytes=None))
    shadow = shadow_receipt("test-episode")
    assert subject.validate_shadow_receipt(shadow)["status"] == "EQUIVALENT_PAIRED_BATCH_OBSERVED"
    drifted_pair = {**shadow["paired_receipt"], "source_post": {"drift": True}}
    with pytest.raises(subject.BExploreContractError, match="authority"):
        subject.validate_shadow_receipt({**shadow, "paired_receipt": drifted_pair})
    with pytest.raises(subject.BExploreContractError, match="authority"):
        subject.validate_shadow_receipt({**shadow, "shadow_influenced_actions": True})
    bad_boundary = list(shadow["paired_receipt"]["boundaries"]); bad_boundary[2] = {**bad_boundary[2], "shadow_full_output_digest": "0" * 64}
    with pytest.raises(subject.BExploreContractError, match="equivalence differs"):
        subject.validate_shadow_receipt({**shadow, "paired_receipt": {**shadow["paired_receipt"], "boundaries": tuple(bad_boundary)}})


def test_named_output_internal_contract_is_create_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", True)
    debug = configs()[0]
    source = {"mode": "current_checkout_actual_bytes", "digest": "a" * 64}
    plan = subject.serialize_readiness_plan_once(tmp_path, debug, preflight_receipt=receipt(), now=NOW, source_identity_provider=lambda: source)
    assert plan.name == "PLAN.json" and json.loads(plan.read_text("ascii"))["namespace"] == debug.namespace
    assert json.loads(plan.read_text("ascii"))["source_identity"] == source
    with pytest.raises(subject.BExploreContractError, match="already exists"):
        subject.serialize_readiness_plan_once(tmp_path, debug, preflight_receipt=receipt(), now=NOW, source_identity_provider=lambda: source)
    incomplete = subject.serialize_named_outcome_once(tmp_path, debug, raw_output={"counts": "raw"}, preflight_receipt=receipt(), telemetry_payload=None, now=NOW)
    invalid = json.loads(incomplete.read_text("ascii"))
    assert incomplete.name == "INCOMPLETE.json" and invalid["status"] == "INCOMPLETE"
    assert invalid["scientific_result"] is False and invalid["result"] is None
    assert invalid["raw_output_uninterpreted"] == {"counts": "raw"}
    with pytest.raises(subject.BExploreContractError, match="already exists"):
        subject.serialize_named_outcome_once(tmp_path, debug, raw_output={}, preflight_receipt=receipt(), telemetry_payload=None, now=NOW)
    valid_root = tmp_path / "valid"; artifact = durable_checkpoint_artifact(valid_root, debug)
    terminal = runtime_terminal(debug, artifact)
    result = subject.serialize_named_outcome_once(valid_root, debug, raw_output=terminal, preflight_receipt=receipt(), telemetry_payload=bound_telemetry(terminal), now=NOW)
    valid = json.loads(result.read_text("ascii"))
    assert result.name == "RESULT.json" and valid["status"] == "VALID_B_EXPLORE_RESULT"
    assert valid["scientific_result"] is True and valid["raw_output_uninterpreted"] is None
    assert (result.parent / "CHECKPOINTS.bin").is_file() and (result.parent / "CHECKPOINTS_MANIFEST.json").is_file()


def test_debug_gate_internal_validator_rejects_shallow_or_drifted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", True)
    debug = configs()[0]; artifact = durable_checkpoint_artifact(tmp_path, debug); terminal = runtime_terminal(debug, artifact)
    shallow = dict(terminal); shallow["training"] = {}
    with pytest.raises(subject.BExploreContractError, match="training arm payload"):
        subject.validate_runtime_terminal(debug, shallow)
    result = subject.serialize_named_outcome_once(tmp_path, debug, raw_output=terminal, preflight_receipt=receipt(), telemetry_payload=bound_telemetry(terminal), now=NOW)
    (result.parent / "CHECKPOINTS.bin").write_bytes(b"drift")
    with pytest.raises(subject.BExploreContractError, match="checkpoint bundle"):
        subject.build_debug_gate_receipt(result, source_identity_digest="a" * 64, preflight_receipt=receipt(), now=NOW)


def test_no_n7_tuning_no_c_imports_exact_sources_and_raw_lf() -> None:
    signature = set(inspect.signature(subject.run_b_explore_runtime).parameters)
    assert not signature.intersection(subject.FORBIDDEN_N7_CONTROL_SURFACES)
    assert not hasattr(subject, "exact_readiness_plan")
    assert not {"derive_seed_master", "_exact_readiness_plan", "build_shadow_receipt", "assess_posttraining_debug_gate", "validate_runtime_terminal", "_run_after_pretraining_readiness", "_serialize_checkpoint_bundle_once"}.intersection(subject.__all__)
    path = Path(subject.__file__); source = path.read_text("utf-8"); tree = ast.parse(source)
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not any(token in name for name in imports for token in ("evaluation", "frontier", "inference", "branch_reducer"))
    forbidden = ("full_panel_plan", "execute_plan", "ExactPanelReducer", "run_cut_batch", "AtomicFrontier", "seal_complete")
    assert not any(name in source for name in forbidden)
    assert "NativeInteractiveBatch(" not in source and "BNativeTelemetryBatch(" not in source
    assert source.count("PairedPrimaryShadowBatch(") == 3
    assert "HELDOUT-N7-UNOPENED" in source and "fresh_relabel_each_learned_decision" in source
    assert set(subject._ACTUAL_SOURCE_PATHS) == {
        "scripts/run_vnfc_bpcr_b_explore.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/contracts.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/empirical_contract.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/empirical_training.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/fixtures.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/models.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native_backend.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/numeric.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/production.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/rng.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/services.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/torch_models.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/training.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_backend.cpp",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_checker.hpp",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp",
        "experiments/candidates/variable_n_fleet_churn_b_explore/__init__.py",
        "experiments/candidates/variable_n_fleet_churn_b_explore/native_backend.py",
        "experiments/candidates/variable_n_fleet_churn_b_explore/native/telemetry_backend.cpp",
        "docs/research/candidates/variable_n_fleet_churn/VNFC_UAV_BOUNDED_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
        "docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
    }
    for raw_path in (path, Path(__file__)):
        assert b"\r\n" not in raw_path.read_bytes()


def test_public_runtime_validates_preflight_then_fences_before_all_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    samples = iter(({"files": (1,), "native": 1}, {"files": (2,), "native": 1}))
    monkeypatch.setattr(subject, "_source_identity", lambda: next(samples))
    fence = subject._SourceFence.capture()
    with pytest.raises(subject.BExploreContractError, match="identity drifted"):
        fence.close()
    events = []; original = subject.validate_preflight_receipt
    def checked(value: dict[str, object], *, now: datetime) -> dict[str, object]:
        events.append("preflight"); return original(value, now=now)
    monkeypatch.setattr(subject, "validate_preflight_receipt", checked)
    monkeypatch.setattr(subject.torch, "get_num_threads", lambda: events.append("threads") or 7)
    monkeypatch.setattr(subject, "_SourceFence", type("Fence", (), {"capture": classmethod(lambda cls: events.append("source"))}))
    def native(**kwargs: object) -> dict[str, object]: events.append("native"); return {}
    for config in (configs()[0], configs()[1]):
        with pytest.raises(subject.BExploreContractError, match="REPAIR_REQUIRED"):
            subject.run_b_explore_runtime(config, preflight_receipt=receipt(), telemetry_sink=Sink(), now=NOW, output_root=tmp_path, native_admission=native, archived_debug_result_path=tmp_path / "must-not-read")
    assert events == ["preflight", "preflight"] and list(tmp_path.iterdir()) == []


def test_debug_runtime_wiring_trains_before_gate_and_freezes_before_any_evaluation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    events = []
    class Fence:
        identity = {"source": "fixed"}
        @classmethod
        def capture(cls) -> "Fence":
            events.append("source-pre"); return cls()
        def close(self) -> None:
            events.append("source-post")
    monkeypatch.setattr(subject, "_SourceFence", Fence)
    learners = {"models": {"MAPR": object(), "DIRECT": object()}, "optimizers": {"MAPR": object(), "DIRECT": object()}}
    monkeypatch.setattr(subject, "_initialize_learners", lambda *args, **kwargs: events.append("initialize") or learners)
    training = {arm: {"updates": 8, "episodes": 128, "joint_transitions": 768, "optimizer_steps": 128, "updates_telemetry": ()} for arm in subject.ARMS}
    monkeypatch.setattr(subject, "_train_learners", lambda *args, **kwargs: events.append("train-N3-N5") or training)
    monkeypatch.setattr(subject, "clone_checkpoint", lambda model, label: events.append(f"checkpoint-{label}") or {"label": label, "state": {"p": torch.zeros(1)}, "sha256": label, "storage_disjoint": True})
    monkeypatch.setattr(subject, "validate_checkpoint_pair", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_serialize_checkpoint_bundle_once", lambda *args, **kwargs: events.append("persist-checkpoints") or checkpoint_artifact(configs()[0]))
    gate = {"runtime_ready": True, "ps_b0_result": {"passed": True}, "bcrh_result": {"common_host_valid": True}}
    monkeypatch.setattr(subject, "assess_posttraining_debug_gate", lambda *args, **kwargs: events.append("posttrain-PS-B0-BCRH") or gate)
    token = subject._HeldoutFreezeToken(configs()[0].namespace, "frozen")
    monkeypatch.setattr(subject, "_freeze_before_n7", lambda *args, **kwargs: events.append("freeze-before-N7") or token)
    evaluation = {"learned": (), "bcrh": (), "rollouts": 112, "relabel_mismatch_count": {"MAPR": 0, "DIRECT": 0}}
    monkeypatch.setattr(subject, "_execute_evaluation", lambda *args, **kwargs: events.append("evaluate-including-N7") or evaluation)
    monkeypatch.setattr(subject, "_runtime_terminal", lambda *args, **kwargs: events.append("terminal") or {"schema": "fake-terminal"})
    fence = Fence.capture()
    result = subject._run_after_pretraining_readiness(configs()[0], now=NOW, fence=fence, source_digest="a" * 64, diagnostic_state_adapter=object(), archived_debug_gate_receipt=None, output_root=tmp_path)
    assert result == {"schema": "fake-terminal"}
    assert events.index("train-N3-N5") < events.index("posttrain-PS-B0-BCRH") < events.index("freeze-before-N7") < events.index("evaluate-including-N7")


def test_public_serializers_and_debug_gate_hard_fence_before_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    creates = []
    monkeypatch.setattr(subject, "_create_once_json", lambda *args, **kwargs: creates.append(args) or tmp_path / "forbidden")
    debug = configs()[0]
    calls = (
        lambda: subject.serialize_readiness_plan_once(tmp_path, debug, preflight_receipt=receipt(), now=NOW),
        lambda: subject.serialize_named_outcome_once(tmp_path, debug, raw_output={}, preflight_receipt=receipt(), telemetry_payload=None, now=NOW),
        lambda: subject.build_debug_gate_receipt(tmp_path / "must-not-be-read.json", source_identity_digest="a" * 64, preflight_receipt=receipt(), now=NOW),
    )
    for call in calls:
        with pytest.raises(subject.BExploreContractError, match="REPAIR_REQUIRED"):
            call()
    assert creates == [] and list(tmp_path.iterdir()) == []
    with pytest.raises(subject.BExploreContractError, match="preflight receipt is absent"):
        subject.serialize_named_outcome_once(tmp_path, debug, raw_output={}, preflight_receipt=None, telemetry_payload=None, now=NOW)


def test_checkpoint_snapshots_are_separate() -> None:
    model = torch.nn.Linear(2, 1, dtype=torch.float64)
    initial = subject.clone_checkpoint(model, "initial")
    with torch.no_grad():
        model.weight.add_(1)
    final = subject.clone_checkpoint(model, "final")
    subject.validate_checkpoint_pair(initial, final)
    assert initial["sha256"] != final["sha256"]


def test_learned_output_finiteness_and_probability_validator() -> None:
    valid = {"command": torch.zeros((2, 4), dtype=torch.int64), "log_probability": torch.zeros(2, dtype=torch.float64), "token_entropies": torch.zeros((2, 4), dtype=torch.float64), "value": torch.zeros(2, dtype=torch.float64), "token_probabilities": torch.full((2, 4, 3), 1 / 3, dtype=torch.float64)}
    subject._validate_model_output(valid, context="test")
    for field in ("log_probability", "token_entropies", "value", "token_probabilities"):
        bad = {name: value.clone() for name, value in valid.items()}; bad[field].view(-1)[0] = float("nan")
        with pytest.raises(subject.BExploreContractError, match="nonfinite"):
            subject._validate_model_output(bad, context="test")
    negative = {name: value.clone() for name, value in valid.items()}; negative["token_probabilities"][0, 0, 0] = -0.1
    with pytest.raises(subject.BExploreContractError, match="outside"):
        subject._validate_model_output(negative, context="test")
    mass = {name: value.clone() for name, value in valid.items()}; mass["token_probabilities"][0, 0] *= .5
    with pytest.raises(subject.BExploreContractError, match="mass"):
        subject._validate_model_output(mass, context="test")
