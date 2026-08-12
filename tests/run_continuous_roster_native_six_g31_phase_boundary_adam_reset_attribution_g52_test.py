from __future__ import annotations

import copy
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_common_fast_anchor_attribution_g50 as g50,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51
    as g51,
)
from scripts import (
    run_continuous_roster_native_six_g31_phase_boundary_adam_reset_attribution_g52
    as runner,
)


source = runner.source


def test_runner_exact_configuration_sources_seeds_backend_and_threads() -> None:
    nonformal = runner._configuration(formal=False, cpu_budget=2, process_workers=2)
    formal = runner._configuration(formal=True, cpu_budget=2, process_workers=2)
    assert nonformal["phase_A_updates"] == 10
    assert nonformal["phase_B_updates_per_arm"] == 10
    assert nonformal["training_real_transitions"] == 11_520
    assert nonformal["evaluation_real_transitions"] == 6_912
    assert nonformal["total_real_transitions"] == 18_432
    assert nonformal["optimizer_steps"] == 60
    assert nonformal["bootstrap_resamples"] == 250
    assert nonformal["wall_clock_cap_seconds"] == 1_200
    assert formal["phase_A_updates"] == 100
    assert formal["phase_B_updates_per_arm"] == 100
    assert formal["training_real_transitions"] == 345_600
    assert formal["evaluation_real_transitions"] == 165_888
    assert formal["total_real_transitions"] == 511_488
    assert formal["optimizer_steps"] == 1_800
    assert formal["bootstrap_resamples"] == 10_000
    assert formal["wall_clock_cap_seconds"] == 28_800
    assert formal["replicates"] == 3
    assert formal["common_phase_A_ancestor_count"] == 3
    assert formal["training_parallel_unit"] == "independent_common_ancestor_root"
    assert formal["process_isolation"] == "one_preassigned_replicate_per_task"
    assert formal["deterministic_merge"] == "preassigned_index_not_completion_order"
    assert formal["worker_start_method"] == "spawn"
    assert formal["worker_thread_controls"] == {
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    }
    assert formal["environment_backend"] == "ContinuousRosterToyBatch_CPU_CPP_required"
    assert formal["python_fallback"] is False
    assert formal["H"] == 48 and formal["K_search"] == 0
    assert formal["hypothetical_transitions"] == 0

    controls = runner.source_controls()
    assert controls["fresh_end_to_end_lifecycle"] is True
    assert controls["predecessor_checkpoint_initialization"] is False
    assert controls["predecessor_optimizer_initialization"] is False
    assert controls["predecessor_trajectory_initialization"] is False
    assert controls["predecessor_manifest_or_run_root_initialization"] is False
    assert controls["phase_A_model_class"] == "G51NoBaselinePhaseAProjection"
    assert controls["phase_A_credit_baselines_package"] is False
    assert controls["retained_actor_parameter_count"] == 17
    assert controls["forced_common_post_first_step_trajectories"] is False
    assert source.seed_block(0, formal=False)["initialization"] == 11_421_000
    assert source.seed_block(0, formal=True)["initialization"] == 10_521_000
    with pytest.raises(ValueError, match="outside frozen support"):
        source.seed_block(3, formal=True)
    with pytest.raises(ValueError, match="exceed"):
        runner._resolve_cpu_execution(1, 2)


def test_exact_first_match_order_estimand_margin_and_claims() -> None:
    assert runner.FIRST_MATCH_ORDER == (
        runner.INVALID_BRANCH,
        runner.SOURCE_FAILURE_BRANCH,
        runner.NULL_SUFFICIENT_BRANCH,
        runner.REFERENCE_ADVANTAGE_BRANCH,
        runner.UNDERPOWERED_BRANCH,
    )
    assert runner._synthetic_branch_witnesses() == {
        "invalid": runner.INVALID_BRANCH,
        "source_failure": runner.SOURCE_FAILURE_BRANCH,
        "persistent_sufficient": runner.NULL_SUFFICIENT_BRANCH,
        "reset_advantage": runner.REFERENCE_ADVANTAGE_BRANCH,
        "underpowered": runner.UNDERPOWERED_BRANCH,
    }
    base = {
        "operational_valid": True,
        "treatment_activation_valid": True,
        "source_valid": True,
        "RESET_access_pass": True,
        "CARRY_access_pass": True,
        "CARRY_access_confident_fail": False,
        "persistent_Adam_noninferior": True,
        "material_reset_advantage": True,
    }
    assert runner.select_g52_result_branch({**base, "treatment_activation_valid": False}) == runner.INVALID_BRANCH
    assert runner.select_g52_result_branch({**base, "source_valid": False}) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g52_result_branch(base) == runner.NULL_SUFFICIENT_BRANCH
    assert runner.select_g52_result_branch(
        {**base, "persistent_Adam_noninferior": False, "CARRY_access_pass": False, "CARRY_access_confident_fail": True}
    ) == runner.REFERENCE_ADVANTAGE_BRANCH
    assert runner.MATERIALITY_MARGIN == 0.05
    analyze_source = inspect.getsource(runner.analyze)
    assert "Delta_reset=U_RESET-U_CARRY" in analyze_source
    assert "favors_RESET" in analyze_source
    assert "terminal_for_registered_treatment_if_formal" in analyze_source
    assert "retry_rescue_more_roots_seed_search_or_ablation_authorized" in analyze_source


def _activation_certificate(
    models: dict[str, object], optimizers: dict[str, torch.optim.Adam],
    boundary: dict[str, object], *, active: bool = True,
) -> dict[str, object]:
    source.make_synthetic_boundary_state_for_readiness(
        models[source.RESET_ARM], optimizers[source.RESET_ARM], step=1  # type: ignore[arg-type]
    )
    for parameter in source.actor_parameters(models[source.CARRY_ARM]):  # type: ignore[arg-type]
        optimizers[source.CARRY_ARM].state[parameter]["step"].fill_(21.0)
    evidence = {
        source.RESET_ARM: source.inspect_post_step_adam_state(
            arm=source.RESET_ARM, model=models[source.RESET_ARM],  # type: ignore[arg-type]
            optimizer=optimizers[source.RESET_ARM], expected_step=1,
        ),
        source.CARRY_ARM: source.inspect_post_step_adam_state(
            arm=source.CARRY_ARM, model=models[source.CARRY_ARM],  # type: ignore[arg-type]
            optimizer=optimizers[source.CARRY_ARM], expected_step=21,
        ),
    }
    pre = source._actor_rows(models[source.RESET_ARM])  # type: ignore[arg-type]
    reset = tuple(row + (1e-4 if active else 0.0) for row in pre)
    carry = tuple(row + (5e-5 if active else 0.0) for row in pre)
    return source.build_boundary_activation_certificate(
        pre_step_rows=pre,
        post_step_rows={source.RESET_ARM: reset, source.CARRY_ARM: carry},
        batch_digest="1" * 64,
        target_digest="2" * 64,
        normalized_target_digest="3" * 64,
        assigned_gradient_digests={arm: "4" * 64 for arm in source.ARMS},
        reset_empty_state=True,
        carry_state_digest=boundary["CARRY_install"]["installed_state_digest"],  # type: ignore[index]
        carried_state_finite_nonzero=True,
        post_step_optimizer_state=evidence,
        post_step_optimizer_storage_disjoint=True,
        carry_boundary_step=20,
    )


def test_final_only_checkpoint_reload_and_tamper_rejection() -> None:
    ancestor, ancestor_optimizer = source.make_fresh_phase_A_ancestor(
        member_capacity=8, initialization_seed=10_521_000
    )
    source.make_synthetic_boundary_state_for_readiness(ancestor, ancestor_optimizer, step=20)
    models, optimizers, boundary = source.project_phase_B_arms(
        ancestor,
        ancestor_optimizer,
        completed_phase_A_updates=10,
        expected_step=20,
    )
    certificate = _activation_certificate(models, optimizers, boundary)
    for parameter in source.actor_parameters(models[source.RESET_ARM]):
        optimizers[source.RESET_ARM].state[parameter]["step"].fill_(20.0)
    for parameter in source.actor_parameters(models[source.CARRY_ARM]):
        optimizers[source.CARRY_ARM].state[parameter]["step"].fill_(40.0)
    configuration = runner._configuration(formal=False)
    checkpoints = {
        arm: source.build_final_checkpoint(
            model=models[arm],
            optimizer=optimizers[arm],
            source_commit="a" * 40,
            formal=False,
            replicate=0,
            arm=arm,
            completed_phase_A_updates=10,
            completed_phase_B_updates=10,
            configuration=configuration,
            seeds=source.seed_block(0, formal=False),
            boundary_evidence=boundary,
            activation_certificate=certificate,
        )
        for arm in source.ARMS
    }
    for arm, checkpoint in checkpoints.items():
        assert source.validate_final_checkpoint(checkpoint)
        reloaded = source.load_phase_B_checkpoint_model(checkpoint, member_capacity=8)
        assert source._actor_digest(reloaded) == source._actor_digest(models[arm])
        assert checkpoint["kind"] == "final_only"
        assert checkpoint["checkpoint_selection"] == "final_only"
        tampered = copy.deepcopy(checkpoint)
        tampered["completed_phase_B_updates"] = 9
        assert not source.validate_final_checkpoint(tampered)
        tampered = copy.deepcopy(checkpoint)
        tampered["activation_certificate"]["active"] = False
        assert not source.validate_final_checkpoint(tampered)
        tampered = copy.deepcopy(checkpoint)
        tampered["actor_state"]["extra"] = torch.zeros(1)
        assert not source.validate_final_checkpoint(tampered)


def test_formal_admission_and_nonformal_authority_fail_closed(tmp_path: Path) -> None:
    admission = runner.validate_formal_admission(
        source_commit="a" * 40,
        authorization_token=runner.AUTHORIZATION_TOKEN,
        alignment_disposition="ALIGNED",
        aligned_source_commit="a" * 40,
        alignment_stage_commit="b" * 40,
        implementation_handoff_sha256=runner.IMPLEMENTATION_HANDOFF_SHA256,
        preflight_root=tmp_path / "missing",
        cpu_budget=2,
        process_workers=2,
    )
    assert admission["admitted"] is False
    assert "aligned_implementation_commit" in admission["errors"]
    assert "alignment_stage_commit" in admission["errors"]
    assert "same_source_nonformal_preflight" in admission["errors"]

    with pytest.raises(ValueError, match="nonformal train cannot carry formal authority"):
        runner.train(
            run_root=tmp_path / "nonformal",
            source_commit="a" * 40,
            formal=False,
            authorization_token=runner.AUTHORIZATION_TOKEN,
        )
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "existing").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="not fresh"):
        runner.train(
            run_root=occupied,
            source_commit="a" * 40,
            formal=False,
        )


def _proof_episode(process: dict[str, object], *, random: bool) -> dict[str, object]:
    rewards = [1.0] * 48
    event_order = list(process["event_order"])
    return {
        "local_episode_id": process["local_episode_id"],
        "episode_id": process["episode_id"],
        "signature": process["signature"],
        "event_times": list(process["event_times"]),
        "event_order": event_order,
        "roster_sizes_valid": True,
        "reward_trace": rewards,
        "roster_size_trace": list(process["random_expected_roster_sizes"] if random else process["fixed_expected_roster_sizes"]),
        "utility": 1.0,
        "minimum_step_utility": 1.0,
        "minimum_event_window_utility": 1.0,
        "minimum_process_segment_utility": 1.0,
        "event_window_utility": {name: 1.0 for name in event_order},
        "process_segment_utility": [1.0] * 5,
    }


def _build_complete_artifact_fixture(root: Path, *, active: bool) -> tuple[dict[str, object], dict[str, object]]:
    configuration = runner._configuration(formal=False, cpu_budget=2, process_workers=2)
    assert configuration["replicates"] == 1
    root.mkdir(parents=True, exist_ok=True)
    (root / runner.CHECKPOINT_DIRECTORY).mkdir()
    ancestor, ancestor_optimizer = source.make_fresh_phase_A_ancestor(
        member_capacity=8, initialization_seed=10_521_333
    )
    initial_digest = source._actor_digest(ancestor)
    source.make_synthetic_boundary_state_for_readiness(ancestor, ancestor_optimizer, step=20)
    models, optimizers, boundary = source.project_phase_B_arms(
        ancestor, ancestor_optimizer, completed_phase_A_updates=10, expected_step=20
    )
    certificate = _activation_certificate(models, optimizers, boundary, active=active)
    for parameter in source.actor_parameters(models[source.RESET_ARM]):
        optimizers[source.RESET_ARM].state[parameter]["step"].fill_(20.0)
    for parameter in source.actor_parameters(models[source.CARRY_ARM]):
        optimizers[source.CARRY_ARM].state[parameter]["step"].fill_(40.0)
    checkpoints = {
        arm: source.build_final_checkpoint(
            model=models[arm], optimizer=optimizers[arm], source_commit="a" * 40,
            formal=False, replicate=0, arm=arm, completed_phase_A_updates=10,
            completed_phase_B_updates=10, configuration=configuration,
            seeds=source.seed_block(0, formal=False), boundary_evidence=boundary,
            activation_certificate=certificate,
        )
        for arm in source.ARMS
    }
    arm_rows: dict[str, object] = {}
    for arm in source.ARMS:
        reference = runner._checkpoint_reference(0, arm)
        path = root / reference
        torch.save(checkpoints[arm], path)
        arm_rows[arm] = {
            "final_checkpoint": reference,
            "final_checkpoint_sha256": runner._artifact_digest(path),
            "final_model_state_digest": runner._checkpoint_model_state_digest(checkpoints[arm]),
            "completed_phase_A_updates": 10,
            "completed_phase_B_updates": 10,
        }
    phase_a = [
        {
            "update_index": index, "PPO_passes": 2, "optimizer_steps": 2,
            "records": [
                {"pass_index": pass_index, "target_digest": "1" * 64,
                 "normalized_target_digest": "2" * 64,
                 "assigned_gradient_digest": "3" * 64,
                 "optimizer_step": index * 2 + pass_index + 1}
                for pass_index in range(2)
            ],
            "passed": True,
        }
        for index in range(10)
    ]
    phase_b = [{
        "update_index": 0, "first_step_certificate": certificate,
        "PPO_passes_per_arm": 2, "optimizer_steps_per_arm": 2,
        "certificate_structurally_valid": True,
        "first_batch_materialized_before_either_step": True,
        "both_first_step_plans_materialized_before_either_step": True,
        "first_step_actor_batch_target_gradient_equal": True,
        "boundary_operationally_valid": True,
        "treatment_active": active, "passed": True,
    }] + [
        {
            "update_index": index, "optimizer_steps_per_arm": 2,
            "PPO_passes_per_arm": 2,
            "separate_on_policy_collection": True,
            "paired_exogenous_assignments_only": True,
            "forced_common_actions_or_trajectories": False,
            "records": [
                {"pass_index": pass_index, "plans_materialized_before_either_step": True,
                 "arm_specific_trajectory_digests": {arm: "4" * 64 for arm in source.ARMS},
                 "arm_specific_target_digests": {arm: "5" * 64 for arm in source.ARMS}}
                for pass_index in range(2)
            ],
            "passed": True,
        }
        for index in range(1, 10)
    ]
    conclusion = {
        "certificate_kind": "G52_FORMAL_ROOT_ACTIVATION_INVENTORY_V1",
        "root_count": 1,
        "q_r": [certificate["norms"]["q_r"]],
        "every_root_certificate_structurally_valid": True,
        "every_root_boundary_operationally_valid": True,
        "every_root_active": active,
        "every_root_scientifically_valid": active,
    }
    cpu = {
        **runner._resolve_cpu_execution(2, 2),
        "hardware_logical_cpu_count": int(os.cpu_count() or 1),
        "effective_parent_torch_intraop_threads": 1,
    }
    native = {
        "kind": "ContinuousRosterToyBatch_CPU_CPP", "required": True,
        "python_fallback": False, "module": "proof_fixture_native_backend",
        "build_identity": "f" * 64,
    }
    training: dict[str, object] = {
        "schema_version": runner.SCHEMA_VERSION, "algorithm_id": runner.ALGORITHM_ID,
        "source_id": runner.SOURCE_ID, "stage": "train", "status": "COMPLETE",
        "formal": False, "formal_statistical_run": False, "scientific_iteration_cost": 0,
        "source_commit": "a" * 40, "authorization_token": None,
        "alignment_audit_id": None, "alignment_disposition": None,
        "aligned_source_commit": None, "alignment_stage_commit": None,
        "implementation_handoff_sha256": runner.IMPLEMENTATION_HANDOFF_SHA256,
        "preflight_root": None, "preflight_artifact_digests": None,
        "accepted_anchor_artifact_digests": None, "configuration": configuration,
        "source_controls": runner.source_controls(), "native_backend": native,
        "cpu_execution": cpu, "conclusion_evidence": conclusion,
        "replicate_results": [{
            "replicate": 0, "seeds": source.seed_block(0, formal=False),
            "fresh_initialization_count": 1, "common_phase_A_ancestor_count": 1,
            "phase_A_initial_actor_digest": initial_digest,
            "phase_A_final_actor_digest": boundary["ancestor_actor_digest"],
            "phase_A_update_records": phase_a, "phase_boundary_evidence": boundary,
            "first_phase_B_activation_certificate": certificate,
            "phase_B_update_records": phase_b,
            "later_arm_specific_on_policy_collection": True,
            "paired_exogenous_assignments": True,
            "forced_common_post_first_step_trajectories": False,
            "proof_activity": {"diagnostic_real_transitions": 0, "diagnostic_optimizer_steps": 0, "bootstrap_resamples": 0},
            "arms": arm_rows,
            "worker_execution": {
                "preassigned_index": 0, "pid": 4242, "output_digest": "e" * 64,
                "wall_time_seconds": 1.0, "thread_environment": dict(runner.WORKER_THREAD_ENV),
                "torch_intraop_threads": 1,
            },
        }],
        "checkpoint_selection": "final_only",
        "work_accounting": {
            "scientific_real_transitions": configuration["training_real_transitions"],
            "scientific_optimizer_steps": configuration["optimizer_steps"],
            "proof_real_transitions": 0, "proof_optimizer_steps": 0, "bootstrap_resamples": 0,
        },
        "stage_wall_time_seconds": 1.0,
    }
    runner._write_json(root / runner.TRAIN_MANIFEST, training)
    inventories = [
        runner._source_inventory(replicate=0, capacity=capacity, episode_count=6, formal=False)[1]
        for capacity in runner.g34.CAPACITIES
    ]
    inventory_map = {int(row["capacity"]): row["processes"] for row in inventories}
    cells: list[dict[str, object]] = []
    for capacity in runner.g34.CAPACITIES:
        for arm in source.ARMS:
            for name in runner.MODEL_CELLS:
                contract = runner._cell_contract(name)
                cells.append({
                    "replicate": 0, "capacity": capacity, "arm": arm, "cell": name,
                    **contract, "optimizer_steps": 0,
                    "state_before": arm_rows[arm]["final_model_state_digest"],  # type: ignore[index]
                    "state_after": arm_rows[arm]["final_model_state_digest"],  # type: ignore[index]
                    "lifecycle_valid": True, "realized_successor_actor_credit_read_count": 0,
                    "baseline_evaluation_read_count": 0,
                    "episodes": [_proof_episode(row, random=contract["process"] == "random") for row in inventory_map[capacity]],
                })
    workers = []
    for index, (capacity, name) in enumerate((capacity, name) for capacity in runner.g34.CAPACITIES for name in runner.MODEL_CELLS):
        workers.append({
            "index": index, "task_identity": {"replicate": 0, "capacity": capacity, "cell": name},
            "configured_process_workers": 2, "output_path": f"proof/task_{index}/result.json",
            "output_digest": f"{index + 1:064x}", "output_transport_consumed": True,
            "runtime": {"pid": 5000 + index, "wall_time_seconds": 0.1,
                        "process_cpu_seconds": 0.1, "python_peak_traced_bytes": 1,
                        "torch_intraop_threads": 1, "thread_environment": dict(runner.WORKER_THREAD_ENV)},
        })
    evaluation: dict[str, object] = {
        "schema_version": runner.SCHEMA_VERSION, "algorithm": runner.ALGORITHM_ID,
        "source_id": runner.SOURCE_ID, "stage": "evaluate", "status": "COMPLETE",
        "formal": False, "source_commit": "a" * 40, "authorization_token": None,
        "alignment_audit_id": None, "alignment_disposition": None,
        "aligned_source_commit": None, "alignment_stage_commit": None,
        "preflight_artifact_digests": None, "accepted_anchor_artifact_digests": None,
        "runtime": {"python": "proof", "torch": "proof", "numpy": "proof", "platform": "proof"},
        "cpu_execution": cpu, "native_backend": native, "configuration": configuration,
        "source_controls": runner.source_controls(), "conclusion_evidence": conclusion,
        "training_manifest_digest": runner._artifact_digest(root / runner.TRAIN_MANIFEST),
        "stage_wall_time_seconds": 1.0, "direct_source_validation": True,
        "source_inventory": inventories, "worker_execution": workers, "cells": cells,
        "work_accounting": {"scientific_real_transitions": configuration["evaluation_real_transitions"],
                            "scientific_optimizer_steps": 0, "proof_real_transitions": 0,
                            "proof_optimizer_steps": 0, "bootstrap_resamples": 0},
    }
    runner._write_json(root / runner.EVALUATION_MANIFEST, evaluation)
    return training, evaluation


def test_same_source_preflight_rejects_incomplete_and_accepts_complete_fixture(tmp_path: Path) -> None:
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    configuration = runner._configuration(formal=False, cpu_budget=2, process_workers=2)
    for name, value in (
        (runner.TRAIN_MANIFEST, {"formal": False, "source_commit": "a" * 40, "configuration": configuration, "stage_wall_time_seconds": 1.0}),
        (runner.EVALUATION_MANIFEST, {"formal": False, "source_commit": "a" * 40, "configuration": configuration, "stage_wall_time_seconds": 1.0}),
        (runner.ANALYSIS_RESULT, {"formal": False, "source_commit": "a" * 40, "result_branch": runner.NONFORMAL_BRANCH, "operational_valid": True, "scientific_branch_selected": False, "stage_wall_time_seconds": 1.0}),
    ):
        runner._write_json(incomplete / name, value)
    with pytest.raises(ValueError, match="complete-artifact"):
        runner._valid_nonformal_preflight(incomplete, source_commit="a" * 40)

    complete = tmp_path / "complete"
    training, evaluation = _build_complete_artifact_fixture(complete, active=True)
    analysis = {
        "schema_version": runner.SCHEMA_VERSION, "algorithm_id": runner.ALGORITHM_ID,
        "source_id": runner.SOURCE_ID, "stage": "analyze", "status": "COMPLETE",
        "formal": False, "source_commit": "a" * 40, "operational_valid": True,
        "operational_errors": [], "metrics": {"operational_valid": True, "treatment_activation_valid": True},
        "primary_estimand": "Delta_reset=U_RESET-U_CARRY", "positive_direction": "favors_RESET",
        "materiality_and_noninferiority_margin": 0.05,
        "threshold_record": {
            "utility_floor": runner.UTILITY_FLOOR,
            "stochastic_floor": runner.STOCHASTIC_FLOOR,
            "event_floor": runner.EVENT_FLOOR,
            "segment_floor": runner.SEGMENT_FLOOR,
            "random_minus_fixed_floor": runner.PROCESS_MARGIN,
            "minimum_replicate_floor": runner.MINIMUM_REPLICATE_FLOOR,
            "materiality_noninferiority_margin": runner.MATERIALITY_MARGIN,
        }, "first_match_priority": list(runner.FIRST_MATCH_ORDER),
        "result_branch": runner.NONFORMAL_BRANCH, "scientific_branch_selected": False,
        "claim_ceiling": source.CLAIM_CEILINGS["otherwise"],
        "terminal_for_registered_treatment_if_formal": False,
        "retry_rescue_more_roots_seed_search_or_ablation_authorized": False,
        "training_manifest_digest": runner._artifact_digest(complete / runner.TRAIN_MANIFEST),
        "evaluation_manifest_digest": runner._artifact_digest(complete / runner.EVALUATION_MANIFEST),
        "work_accounting": {"scientific_real_transitions": 0, "scientific_optimizer_steps": 0,
                            "proof_real_transitions": 0, "proof_optimizer_steps": 0,
                            "bootstrap_resamples": configuration["bootstrap_resamples"]},
        "stage_wall_time_seconds": 1.0,
    }
    runner._write_json(complete / runner.ANALYSIS_RESULT, analysis)
    digests = runner._valid_nonformal_preflight(complete, source_commit="a" * 40)
    assert set(digests) == {"training", "evaluation", "analysis"}
    analysis["evaluation_manifest_digest"] = "0" * 64
    runner._write_json(complete / runner.ANALYSIS_RESULT, analysis)
    with pytest.raises(ValueError, match="complete-artifact"):
        runner._valid_nonformal_preflight(complete, source_commit="a" * 40)


def test_sealed_q_zero_reaches_exact_invalid_branch_without_generic_error(tmp_path: Path) -> None:
    training, evaluation = _build_complete_artifact_fixture(tmp_path, active=False)
    assert runner._training_errors(tmp_path, training) == []
    assert runner._evaluation_errors(tmp_path, training, evaluation) == []
    result = runner.analyze(run_root=tmp_path)
    assert result["status"] == "COMPLETE"
    assert result["operational_valid"] is True
    assert result["metrics"]["treatment_activation_valid"] is False
    assert result["result_branch"] == runner.INVALID_BRANCH
    assert result["work_accounting"]["bootstrap_resamples"] == 0
    assert runner._analysis_errors(tmp_path, training, evaluation, result) == []


def test_evaluation_validation_rejects_route_source_state_worker_pairing_and_backend_tamper(tmp_path: Path) -> None:
    training, evaluation = _build_complete_artifact_fixture(tmp_path, active=True)
    assert runner._evaluation_errors(tmp_path, training, evaluation) == []

    witnesses: list[dict[str, object]] = []
    duplicate = copy.deepcopy(evaluation)
    duplicate["cells"][1] = copy.deepcopy(duplicate["cells"][0])
    witnesses.append(duplicate)
    extra_key = copy.deepcopy(evaluation)
    extra_key["cells"][0]["anonymous"] = True
    witnesses.append(extra_key)
    state = copy.deepcopy(evaluation)
    state["cells"][0]["state_after"] = "0" * 64
    witnesses.append(state)
    lifecycle = copy.deepcopy(evaluation)
    lifecycle["cells"][0]["lifecycle_valid"] = False
    witnesses.append(lifecycle)
    source_inventory = copy.deepcopy(evaluation)
    source_inventory["source_inventory"][0]["processes"][0]["signature"] = "tampered"
    witnesses.append(source_inventory)
    worker = copy.deepcopy(evaluation)
    worker["worker_execution"][0]["runtime"]["torch_intraop_threads"] = 2
    witnesses.append(worker)
    pairing = copy.deepcopy(evaluation)
    pairing["cells"][0]["episodes"][0]["episode_id"] += 1
    witnesses.append(pairing)
    backend = copy.deepcopy(evaluation)
    backend["native_backend"]["python_fallback"] = True
    witnesses.append(backend)
    order = copy.deepcopy(evaluation)
    order["cells"][0], order["cells"][1] = order["cells"][1], order["cells"][0]
    witnesses.append(order)
    assert all(runner._evaluation_errors(tmp_path, training, witness) for witness in witnesses)


def test_g52_import_and_adapter_use_do_not_mutate_g50_or_g48_backends() -> None:
    code = r'''
from scripts import run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50 as g50
base, backend = g50._base, g50._backend
before = (
    id(base.source), id(backend.source), id(base._evaluate_cell),
    id(backend._metric_arrays), base.ALGORITHM_ID, backend.ALGORITHM_ID,
    id(g50.source), g50.ALGORITHM_ID,
)
from scripts import run_continuous_roster_native_six_g31_phase_boundary_adam_reset_attribution_g52 as g52
g52._configuration(formal=False, cpu_budget=2, process_workers=2)
g52._bootstrap_plan(formal=False, replicates=1, episodes=6, repetitions=2)
g52._source_inventory(replicate=0, capacity=6, episode_count=6, formal=False)
after = (
    id(base.source), id(backend.source), id(base._evaluate_cell),
    id(backend._metric_arrays), base.ALGORITHM_ID, backend.ALGORITHM_ID,
    id(g50.source), g50.ALGORITHM_ID,
)
assert before == after
assert g50.source is not g52.source
'''
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=runner.PROJECT_ROOT,
        text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_readiness_interface_and_artifact_boundary_without_running_readiness(tmp_path: Path) -> None:
    smoke = runner.readiness_interface_smoke(source_commit="a" * 40)
    assert smoke["formal"] is False
    assert smoke["execution_readiness_proof_only"] is True
    assert smoke["registered_scientific_roots"] == 0
    assert smoke["scientific_iteration_cost"] == 0
    assert smoke["scientific_real_transitions"] == 0
    assert smoke["scientific_optimizer_steps"] == 0
    assert smoke["bootstrap_resamples"] == 0
    assert smoke["scientific_branch_selected"] is False
    assert smoke["interfaces"][-6:] == [
        "readiness-smoke",
        "readiness-train",
        "readiness-validate",
        "readiness-reload",
        "readiness-evaluate",
        "readiness-analyze",
    ]
    with pytest.raises(ValueError, match="integrated source commit"):
        runner.readiness_interface_smoke(source_commit="dirty")

    for name in runner.READINESS_ARTIFACTS:
        path = tmp_path / name
        if path.suffix == ".json":
            path.write_text("{}", encoding="utf-8")
        else:
            path.write_bytes(b"proof")
    analysis = {
        "passed": True,
        "formal": False,
        "registered_scientific_roots": 0,
        "bootstrap_inference": False,
        "scientific_branch_selected": False,
        "result_branch": None,
    }
    runner._write_json(tmp_path / runner.READINESS_ANALYSIS, analysis)
    assert runner.validate_readiness_artifacts(tmp_path) == []
    analysis["result_branch"] = runner.INVALID_BRANCH
    runner._write_json(tmp_path / runner.READINESS_ANALYSIS, analysis)
    assert runner.validate_readiness_artifacts(tmp_path) == [
        "readiness_analysis_boundary_invalid"
    ]


def test_first_batch_then_later_collection_and_proof_science_accounting_are_explicit() -> None:
    training_source = inspect.getsource(runner._train_replicate)
    assert "first_batch = _collect_phase_B" in training_source
    assert "execute_first_phase_B_update" in training_source
    assert "for update_index in range(1, phase_B_updates)" in training_source
    assert "trajectories =" in training_source and "for arm in source.ARMS" in training_source
    assert "forced_common_post_first_step_trajectories" in training_source
    readiness_source = inspect.getsource(runner.readiness_train)
    assert "make_synthetic_boundary_state_for_readiness" in readiness_source
    assert "registered_scientific_roots" in readiness_source
    assert "proof_activity" in readiness_source
    assert "bootstrap_resamples" in readiness_source
    assert "scientific_branch_selected" in readiness_source


def test_predecessor_identities_remain_immutable_authorities() -> None:
    assert g50.ALGORITHM_ID == "CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50"
    assert g50.SOURCE_ID.endswith("_G50_P0")
    assert g51.ALGORITHM_ID == "CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51"
    assert g51.SOURCE_ID.endswith("_G51_P0")
    assert source.ACCEPTED_ANCESTRY[1] == "G50_P0@b8290699f5c10c593bbc21a6666c17950fae84d3"
    assert source.ACCEPTED_ANCESTRY[2] == "G51_P0@ce6ed8659c480ca2779155b2871dc82b89fa0e95"
    assert "predecessor_artifact_initialization" in inspect.getsource(source.build_final_checkpoint)
