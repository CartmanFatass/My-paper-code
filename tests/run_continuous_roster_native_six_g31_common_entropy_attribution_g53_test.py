from __future__ import annotations

import importlib.util
import copy
import ast
import json
import inspect
from pathlib import Path
import sys

import pytest
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/run_continuous_roster_native_six_g31_common_entropy_attribution_g53.py"
SPEC = importlib.util.spec_from_file_location("g53_runner_test_module", PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def test_runner_phase_inventory_configuration_and_source_controls() -> None:
    assert runner.PHASES == (
        "train", "evaluate", "analyze", "exercise", "readiness-smoke",
        "readiness-train", "readiness-validate", "readiness-reload",
        "readiness-evaluate", "readiness-analyze",
    )
    config = runner.configuration(formal=False)
    assert config["cpu_budget"] == config["process_workers"] == 2
    assert config["worker_start_method"] == "spawn"
    assert config["worker_thread_controls"] == {
        "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
    }
    assert config["aggregate_RSS_cap_bytes"] == 2_147_483_648
    assert config["wall_clock_cap_seconds"] == 1_200.0
    assert config["physical_training_collection_count"] == 39
    assert config["post_treatment_arm_local_physical_collections_per_root"] == 38
    assert config["arm_update_exposures"] == 40
    controls = runner.source_controls()
    assert controls["predecessor_artifact_initialization_count"] == 0
    assert controls["G52_dependency_state_artifact_result_count"] == 0
    assert controls["post_treatment_trajectory_sharing"] is False


def test_formal_runtime_and_cli_authority_fail_closed() -> None:
    with pytest.raises(ValueError, match="formal runtime"):
        runner.configuration(formal=True)
    with pytest.raises(ValueError, match="formal CLI"):
        runner.train(
            run_root=Path("unused"), source_commit="a" * 40, formal=True
        )
    with pytest.raises(SystemExit, match="fails closed"):
        runner._reject_formal(type("Args", (), {
            "formal": True, "authorization_token": None, "preflight_root": None,
            "alignment_disposition": None, "aligned_source_commit": None,
            "alignment_stage_commit": None,
        })())


def test_readiness_is_proof_only_and_cannot_initialize_nonformal(tmp_path: Path) -> None:
    smoke = runner.readiness_interface_smoke(source_commit="a" * 40)
    assert smoke["passed"] is True
    assert (smoke["scientific_roots"], smoke["scientific_transitions"], smoke["optimizer_steps"], smoke["bootstrap_resamples"]) == (0, 0, 0, 0)
    assert smoke["initializes_nonformal"] is False
    root = tmp_path / "readiness"
    train = runner.readiness_train(run_root=root, source_commit="a" * 40)
    assert train["proof_only"] is True
    assert not (root / runner.TRAIN_MANIFEST).exists()
    assert runner.readiness_validate(run_root=root)["scientific_transitions"] == 0
    assert runner.readiness_reload(run_root=root)["optimizer_steps"] == 0
    assert runner.readiness_evaluate(run_root=root)["evaluation_cells"] == 0
    assert runner.readiness_analyze(run_root=root)["scientific_branch_selected"] is False
    record = json.loads((root / "readiness_train.json").read_text(encoding="utf-8"))
    record["phase"] = "readiness-evaluate"
    (root / "readiness_train.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="strict validation"):
        runner.readiness_reload(run_root=root)


def test_readiness_rejects_invalid_commit_and_digest_changes(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="valid source commit"):
        runner.readiness_train(run_root=tmp_path / "bad", source_commit="bad")
    root = tmp_path / "ready"
    runner.readiness_train(run_root=root, source_commit="b" * 40)
    reloaded = runner.readiness_reload(run_root=root)
    assert reloaded["reload_digest_verified"] is True
    assert reloaded["readiness_train_sha256"] == runner._digest(root / "readiness_train.json")
    record = json.loads((root / "readiness_train.json").read_text(encoding="utf-8"))
    record["source_commit"] = "c" * 39
    (root / "readiness_train.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="strict validation"):
        runner.readiness_validate(run_root=root)


def test_readiness_train_admits_wrapper_log_root_and_rejects_foreign_or_replay(
    tmp_path: Path,
) -> None:
    root = tmp_path / "wrapper"
    logs = root / ".hmasd-readiness-logs"
    logs.mkdir(parents=True)
    expected_logs = {
        "interface_smoke.stdout": "smoke output",
        "interface_smoke.stderr": "",
        "bounded_exercise.stdout": "",
        "bounded_exercise.stderr": "",
    }
    for name, content in expected_logs.items():
        (logs / name).write_text(content, encoding="utf-8")
    runner.readiness_train(run_root=root, source_commit="e" * 40)
    assert {entry.name for entry in root.iterdir()} == {
        ".hmasd-readiness-logs", "readiness_train.json"
    }
    assert {
        entry.name: entry.read_text(encoding="utf-8") for entry in logs.iterdir()
    } == expected_logs
    with pytest.raises(ValueError, match="replay"):
        runner.readiness_train(run_root=root, source_commit="e" * 40)

    foreign = tmp_path / "foreign"; foreign.mkdir()
    (foreign / ".hmasd-readiness-logs").mkdir()
    (foreign / "unexpected.txt").write_text("foreign", encoding="utf-8")
    with pytest.raises(ValueError, match="foreign"):
        runner.readiness_train(run_root=foreign, source_commit="e" * 40)

    bad_log = tmp_path / "bad-log"; bad_log.mkdir()
    (bad_log / ".hmasd-readiness-logs").write_text("not a directory", encoding="utf-8")
    with pytest.raises(ValueError, match="not a real directory"):
        runner.readiness_train(run_root=bad_log, source_commit="e" * 40)

    bad_content = tmp_path / "bad-content"
    bad_content_logs = bad_content / ".hmasd-readiness-logs"
    bad_content_logs.mkdir(parents=True)
    (bad_content_logs / "artifact_validation.stdout").write_text("future", encoding="utf-8")
    with pytest.raises(ValueError, match="lifecycle"):
        runner.readiness_train(run_root=bad_content, source_commit="e" * 40)


def test_scientific_fresh_root_still_rejects_wrapper_log_directory(tmp_path: Path) -> None:
    root = tmp_path / "scientific"
    (root / ".hmasd-readiness-logs").mkdir(parents=True)
    with pytest.raises(ValueError, match="fresh"):
        runner._fresh_root(root)


def test_branch_precedence_and_claim_ceiling() -> None:
    complete = {
        "operational_valid": True, "source_valid": True, "pairing_valid": True,
        "G52_isolation_valid": True, "activation_valid": True, "exact_completion": True,
    }
    assert runner.select_result_branch(complete) == runner.NONFORMAL_BRANCH
    for key in complete:
        invalid = dict(complete); invalid[key] = False
        assert runner.select_result_branch(invalid) == runner.INVALID_BRANCH


def test_fresh_root_rejects_preexisting_contents(tmp_path: Path) -> None:
    root = tmp_path / "occupied"; root.mkdir(); (root / "foreign.txt").write_text("x")
    with pytest.raises(ValueError, match="fresh"):
        runner._fresh_root(root)


def _activation() -> dict[str, object]:
    return {
        "same_stored_trajectory_object": True,
        "model_mask_RNG_actor_metadata_Adam_equal": True,
        "stored_trajectory_digest": {name: "a" * 64 for name in (
            "observations", "active_mask", "rewards", "hidden_before",
            "terminal_hidden_reset_mask", "pre_tanh_actions", "actions", "old_log_probs",
        )},
        "replay_old_logprob_target_centered_normalized_policy_gradient_equal": True,
        "raw_entropy_scalar_equal_finite": True,
        "raw_entropy_gradient_equal_finite": True,
        "raw_entropy_gradient_support": ["policy.log_std"],
        "null_scaled_gradient_finite_bytewise_zero": True,
        "reference_scaled_gradient_support": ["policy.log_std"],
        "reference_scaled_gradient_positive_norm": True,
        "coefficient_is_sole_graph_delta": True,
        "post_step_actor_or_Adam_state_differs": True,
        "activation": {
            "reference_scaled_entropy_gradient_norm64": 1.0,
            "null_scaled_entropy_gradient_norm64": 0.0,
            "difference_norm64": 1.0, "q_H": 1.0,
            "active_iff_q_H_gt_0": True,
        },
    }


def _training_row() -> dict[str, object]:
    actor_names = runner.source.reconstruct_static_certificate()["actor_parameter_names"]
    phase_A = {
        "fresh_G50_null_source_count": 1, "G51_NoBaselinePhaseAProjection_count": 1,
        "G51_make_phase_A_models_call_count": 0,
        "baseline_free_before_trajectory_or_optimizer": True,
        "model_state_bytes_equal": True, "actor_parameter_names": actor_names,
        "actor_parameter_order_equal": True, "optimizer_parameter_order_equal": True,
        "Adam_states_empty": True, "slow_critic_state_bytes_equal_and_unexposed": True,
        "shared_storage_count": 0, "projection_RNG_consumption": 0,
        "G52_CARRY_state_count": 0, "passed": True,
    }
    boundary = {
        "completed_phase_A_updates": 10,
        "retained_actor_and_log_std_bytes_equal": True,
        "slow_critic_deleted_at_common_boundary": True, "baseline_absent": True,
        "forbidden_state_keys": [], "phase_A_optimizer_disposed": True,
        "projection_optimizer_steps": 0, "projection_RNG_consumption": 0,
        "passed": True,
    }
    updates = []
    activation = _activation()
    for ordinal in range(20):
        phase = "A" if ordinal < 10 else "B"
        index = ordinal if ordinal < 10 else ordinal - 10
        shared = ordinal == 0
        passes = []
        for pass_index in range(2):
            passes.append({
                "pass_index": pass_index,
                "plans_prepared_before_either_step": True,
                "reverse_preparation_preserved_model_optimizer_gradient_and_RNG": True,
                "coefficient_read_audit": [[phase, arm] for arm in runner.source.ARMS],
                "coefficient_call_count_per_arm": {arm: 1 for arm in runner.source.ARMS},
                "coefficient_hex": {arm: runner.source.ENTROPY_COEFFICIENTS[arm].hex() for arm in runner.source.ARMS},
                "raw_entropy_gradient_digest": {arm: "b" * 64 for arm in runner.source.ARMS},
                "scaled_entropy_gradient_digest": {arm: "c" * 64 for arm in runner.source.ARMS},
                "normalization_rows": 384,
                "physical_normalization_instances": 1 if shared else 2,
                "normalization_exposures": 2, "optimizer_steps_per_arm": 1,
            })
        updates.append({
            "phase": phase, "update_index": index,
            "shared_pretreatment_physical_collection_count": 1 if shared else 0,
            "arm_exposures": 2, "paired_episode_IDs": True,
            "post_treatment_arm_local_on_policy": not shared,
            "pass_records": passes,
            "first_batch_activation_certificate": activation if shared else None,
            "optimizer_steps_per_arm": 2, "passed": True,
        })
    return {
        "replicate": 0, "seeds": runner.source.seed_block(0, formal=False),
        "phase_A_boundary": phase_A,
        "phase_B_boundary": {arm: copy.deepcopy(boundary) for arm in runner.source.ARMS},
        "phase_B_fresh_empty_Adam": True, "update_records": updates,
        "first_batch_activation_certificate": activation,
        "physical_collection_count": 39, "shared_pretreatment_batch_count": 1,
        "post_treatment_arm_local_physical_collections_per_root": 38,
        "arm_update_exposures": 40, "optimizer_step_count": 80,
        "checkpoints": {arm: {} for arm in runner.source.ARMS}, "worker": {},
    }


def test_strict_nested_training_pairing_and_coefficient_evidence_rejects_tampering() -> None:
    row = _training_row()
    assert runner._strict_training_row(row)
    mutations = []
    item = copy.deepcopy(row); item["post_treatment_arm_local_physical_collections_per_root"] = 39; mutations.append(item)
    item = copy.deepcopy(row); item["update_records"][10]["phase"] = "A"; mutations.append(item)
    item = copy.deepcopy(row); item["update_records"][1]["paired_episode_IDs"] = False; mutations.append(item)
    item = copy.deepcopy(row); item["update_records"][1]["shared_pretreatment_physical_collection_count"] = 1; mutations.append(item)
    item = copy.deepcopy(row); item["update_records"][0]["pass_records"][0]["coefficient_call_count_per_arm"][runner.source.NULL_ARM] = 0; mutations.append(item)
    item = copy.deepcopy(row); item["update_records"][0]["first_batch_activation_certificate"]["activation"]["q_H"] = 0.0; mutations.append(item)
    item = copy.deepcopy(row); item["phase_B_boundary"][runner.source.NULL_ARM]["baseline_absent"] = False; mutations.append(item)
    assert all(not runner._strict_training_row(item) for item in mutations)


def _episode(local: int, capacity: int = 8) -> dict[str, object]:
    return {
        "local_episode_id": local,
        "episode_id": runner.g34.episode_address(capacity, local), "profile": "fixture",
        "event_times": [8, 16, 24, 32], "event_order": ["L", "R", "J", "T"],
        "count_trajectory": [8] * 48, "signature": f"sig-{local}",
        "utility": 0.5, "minimum_step_utility": 0.1,
        "minimum_event_window_utility": 0.2, "minimum_process_segment_utility": 0.3,
        "event_window_utility": {name: 0.2 for name in ("L", "R", "J", "T")},
        "process_segment_utility": [0.3] * 5,
        "reward_trace": [0.5] * 48, "roster_size_trace": [8] * 48,
        "roster_sizes_valid": True,
    }


def _artifact_fixture(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, object], dict[str, object]]:
    root.mkdir()
    training = {
        "source_commit": "d" * 40, "configuration": runner.configuration(formal=False),
        "replicate_results": [_training_row()],
        "source_controls": runner.source_controls(),
        "static_certificate": runner.source.reconstruct_static_certificate(),
        "stage_wall_time_seconds": 1.0,
    }
    runner._write_json(root / runner.TRAIN_MANIFEST, training)
    cells = []
    index = 0
    for arm in runner.source.ARMS:
        for capacity in runner.source.EVALUATION_CAPACITIES:
            for cell in runner.MODEL_CELLS:
                process = "fixed" if "fixed" in cell else "random"
                cells.append({
                    "index": index, "arm": arm, "capacity": capacity, "cell": cell,
                    "process": process, "deterministic": cell.endswith("deterministic"),
                    "process_schedule_source": "base.fixed_expected_roster_sizes" if process == "fixed" else "G34.random_expected_roster_sizes",
                    "lifecycle_valid": True, "optimizer_steps": 0,
                    "baseline_actor_read_count": 0, "coefficient_read_count": 0,
                    "episodes": [_episode(row, capacity) for row in range(6)],
                    "worker_pid": 1000 + index, "thread_environment": runner.WORKER_THREAD_ENV,
                    "torch_intraop_threads": 1, "peak_RSS_bytes": 1_000_000,
                }); index += 1
    evaluation = {
        "schema_version": runner.SCHEMA_VERSION, "algorithm_id": runner.ALGORITHM_ID,
        "source_id": runner.source.SOURCE_ID, "stage": "evaluate", "status": "COMPLETE",
        "formal": False, "source_commit": training["source_commit"],
        "configuration": training["configuration"],
        "training_manifest_sha256": runner._digest(root / runner.TRAIN_MANIFEST),
        "cells": cells, "evaluation_transition_count": 6912, "optimizer_steps": 0,
        "distinct_worker_pid_count": 24, "transient_worker_payloads_removed": True,
        "stage_wall_time_seconds": 1.0,
    }
    runner._write_json(root / runner.EVALUATION_MANIFEST, evaluation)
    monkeypatch.setattr(runner, "validate_training_artifacts", lambda _: {"valid": True, "errors": []})
    return training, evaluation


def test_strict_evaluation_inventory_order_lifecycle_and_fixed_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "artifacts"
    _, evaluation = _artifact_fixture(root, monkeypatch)
    assert runner.validate_evaluation_artifacts(root)["valid"] is True
    for mutation in (
        lambda rows: rows.__setitem__(0, rows[1]),
        lambda rows: rows[0].__setitem__("lifecycle_valid", False),
        lambda rows: rows[0].__setitem__("process_schedule_source", "G34.random_expected_roster_sizes"),
        lambda rows: rows[0].__setitem__("coefficient_read_count", 1),
    ):
        changed = copy.deepcopy(evaluation); mutation(changed["cells"])
        runner._write_json(root / runner.EVALUATION_MANIFEST, changed)
        assert runner.validate_evaluation_artifacts(root)["valid"] is False
    runner._write_json(root / runner.EVALUATION_MANIFEST, evaluation)


def test_evaluation_worker_dispatches_fixed_and_random_process_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, bool]] = []
    class Model:
        pass
    monkeypatch.setattr(runner.torch, "load", lambda *args, **kwargs: {})
    monkeypatch.setattr(runner.source, "load_final_checkpoint_model", lambda *args, **kwargs: Model())
    monkeypatch.setattr(runner, "_processes", lambda **kwargs: ())
    monkeypatch.setattr(runner, "_peak_rss_bytes", lambda: 1)
    monkeypatch.setattr(runner, "_activate_worker", lambda: None)
    def evaluate_model(*args: object, **kwargs: object) -> tuple[tuple[dict[str, object], ...], bool]:
        calls.append((str(kwargs["process_kind"]), bool(kwargs["deterministic"])))
        return tuple(_episode(index, 8) for index in range(6)), True
    monkeypatch.setattr(runner.source.g40, "evaluate_model", evaluate_model)
    common = {
        "arm": runner.source.REFERENCE_ARM, "capacity": 8,
        "checkpoint": str(tmp_path / "unused.pt"), "seeds": {},
        "action_seed": 1,
    }
    for index, cell in enumerate(("final_fixed_deterministic", "final_random_stochastic")):
        runner._evaluate_task({
            **common, "index": index, "cell": cell,
            "output_path": str(tmp_path / f"cell-{index}.pt"),
        })
    assert calls == [("fixed", True), ("random", False)]
    assert "process_kind=process_kind" in inspect.getsource(runner._evaluate_task)
    assert "base.fixed_expected_roster_sizes" in inspect.getsource(runner._evaluate_task)


def test_analysis_recomputes_branch_and_rejects_forbidden_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "analysis"
    training, evaluation = _artifact_fixture(root, monkeypatch)
    monkeypatch.setattr(runner, "validate_evaluation_artifacts", lambda _: {"valid": True, "errors": []})
    metrics = runner._expected_analysis_metrics(training, evaluation, operational_valid=True)
    result = {
        "schema_version": runner.SCHEMA_VERSION, "algorithm_id": runner.ALGORITHM_ID,
        "source_id": runner.source.SOURCE_ID, "stage": "analyze", "status": "COMPLETE",
        "formal": False, "source_commit": training["source_commit"],
        "configuration": training["configuration"],
        "train_manifest_sha256": runner._digest(root / runner.TRAIN_MANIFEST),
        "evaluation_manifest_sha256": runner._digest(root / runner.EVALUATION_MANIFEST),
        "metrics": metrics, "validation_errors": [],
        "result_branch": runner.select_result_branch(metrics),
        "scientific_branch_selected": False,
        "terminal_for_registered_treatment_if_formal": False,
        "arm_ranking_authorized": False, "retry_rescue_authorized": False,
        "future_claim_branches_selected": [],
        "claim_ceiling": "one_root_conditional_nonformal_exercise_only",
        "stage_wall_time_seconds": 1.0, "cumulative_wall_time_seconds": 3.0,
    }
    runner._write_json(root / runner.ANALYSIS_RESULT, result)
    assert runner.validate_analysis_artifacts(root)["valid"] is True
    changed = copy.deepcopy(result); changed["scientific_branch_selected"] = True
    runner._write_json(root / runner.ANALYSIS_RESULT, changed)
    assert runner.validate_analysis_artifacts(root)["valid"] is False
    changed = copy.deepcopy(result); changed["result_branch"] = runner.INVALID_BRANCH
    runner._write_json(root / runner.ANALYSIS_RESULT, changed)
    assert runner.validate_analysis_artifacts(root)["valid"] is False


def test_runner_coefficient_isolation_and_no_g52_import(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runner.source, "entropy_coefficient",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected read")),
    )
    assert runner.configuration(formal=False)["formal"] is False
    assert runner.source_controls()["G52_dependency_state_artifact_result_count"] == 0
    assert runner.select_result_branch({}) == runner.INVALID_BRANCH
    tree = ast.parse(PATH.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom): imports.append(node.module or "")
    assert not [name for name in imports if "g52" in name.lower()]
