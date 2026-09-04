from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import datetime as datetime_module
import copy
import hashlib
import math

import pytest
import torch

from experiments.candidates.ucope.conditioning_discriminator_r01.checkpoint import load_checkpoint, load_evaluation_projection
from experiments.candidates.ucope.conditioning_discriminator_r01.contract import (
    ARM_IDS, CONTEXTS, K_EVAL, K_TRAIN, WorkloadConfig, expected_counts,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.evaluation import (
    CheckpointEvaluation, SupportEvaluation, evaluate_checkpoint,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.firewall import (
    validate_import_firewall, validate_runtime_path, zero_effect_ledger,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.host import (
    behavior_stratum, generate_population, group_fold, ordered_rows, validate_population,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.model import build_arm
from experiments.candidates.ucope.conditioning_discriminator_r01.oracle import build_oracle, validate_host
from experiments.candidates.ucope.conditioning_discriminator_r01.publication import (
    atomic_create_json, build_assessment, build_complete_result, build_manifest,
    stage_checkpoints, validate_admission, validate_assessment, validate_complete_result,
    validate_manifest,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.reducer import (
    materially_dominates, reduce_results,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.resources import ResourceMonitor
from experiments.candidates.ucope.conditioning_discriminator_r01.training import (
    build_fold_transforms, feature_matrix, load_checkpoint_models_read_only, prepare_arm_initialization, prepare_fold_data, train_policy,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.workflow import run_workload
from experiments.candidates.ucope.conditioning_discriminator_r01.assessment_v2 import MEASURE_FIELDS, TIMER_SPECS


def _load_runner():
    path = Path("scripts/run_ucope_bc_conditioning_discriminator_r01.py").resolve()
    spec = importlib.util.spec_from_file_location("ucope_conditioning_runner_test", path)
    module = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
    return module


def test_fresh_population_schedule_folds_counts_and_public_host_are_exact():
    config = WorkloadConfig.test(); seed = config.seed_ids[0]
    population = generate_population(config, seed); audit = validate_population(config, seed, population)
    assert audit == {"episodes": 320, "transitions": 1600, "root_rows": 320, "tail_rows": 160}
    assert [behavior_stratum(index) for index in range(10)] == [("PROBE", k) for k in K_TRAIN] + [("IMMEDIATE", k) for k in K_TRAIN]
    assert [group_fold(index) for index in (0, 9, 10, 19, 20)] == [0, 0, 1, 1, 0]
    assert all(len({row.fold_id for row in population if row.episode_index == index}) == 1 for index in range(40))
    assert (len(ordered_rows(population, fold_id=0, stage="tail")), len(ordered_rows(population, fold_id=0, stage="root"))) == (80, 160)
    assert validate_host()["positive_context"] == "LINKED-p17_20-c9_100"
    assert all(row["unique"] for support in (K_TRAIN, K_EVAL) for row in build_oracle(support).values())
    assert expected_counts(WorkloadConfig.science()) == {
        "environment_episodes": 122_880, "environment_transitions": 614_400,
        "root_rows": 122_880, "tail_rows": 61_440, "policies": 12, "checkpoints": 48,
        "tail_optimizer_updates": 1_920, "root_optimizer_updates": 3_840,
        "tail_example_exposures": 491_520, "root_example_exposures": 983_040,
        "target_materialization_events": 12, "target_materialization_rows": 245_760,
        "exact_support_evaluations": 96, "sampled_evaluation_episodes": 24_576,
    }


def test_shared_transforms_twelve_parameters_zero_optimizer_state_and_score_parity():
    config = WorkloadConfig.test(); seed = config.seed_ids[0]; population = generate_population(config, seed)
    prepared = prepare_fold_data(config, population, seed_id=seed, fold_id=0); transforms = prepared.transforms
    initializations = [prepare_arm_initialization(prepared, arm) for arm in ARM_IDS]
    bundles = [build_arm(arm, seed, 0, root_transform=transforms["root"], tail_transform=transforms["tail"], root_initial=initial.root_initial, tail_initial=initial.tail_initial) for arm, initial in zip(ARM_IDS, initializations)]
    assert all(sum(parameter.numel() for model in (bundle.root, bundle.tail) for parameter in model.parameters()) == 12 for bundle in bundles)
    assert all(set(dict(model.named_parameters())) == {"beta"} for bundle in bundles for model in (bundle.root, bundle.tail))
    assert all(not bundle.root_optimizer.state and not bundle.tail_optimizer.state for bundle in bundles)
    assert initializations[0].parity == initializations[1].parity
    assert torch.allclose(bundles[0].root(prepared.root_features), bundles[1].root(prepared.root_features), rtol=4e-6, atol=4e-6)


def test_non_pd_transform_stops_before_any_optimizer_construction(monkeypatch):
    import experiments.candidates.ucope.conditioning_discriminator_r01.training as training
    calls = []
    monkeypatch.setattr(training, "feature_matrix", lambda rows, *, stage: torch.ones((len(tuple(rows)), 5 if stage == "tail" else 7), dtype=torch.float32))
    import experiments.candidates.ucope.conditioning_discriminator_r01.model as model
    monkeypatch.setattr(model, "optimizer_for", lambda scorer: calls.append(scorer))
    config = WorkloadConfig.test(); seed = config.seed_ids[0]; population = generate_population(config, seed)
    with pytest.raises(ValueError, match="not positive definite"):
        build_fold_transforms(config, population, seed_id=seed, fold_id=0)
    assert calls == []


def test_tail_first_target_materialization_exact_counts_and_cold_resume_bit_identity(tmp_path):
    config = WorkloadConfig.test(); seed = config.seed_ids[0]; population = generate_population(config, seed)
    transforms = build_fold_transforms(config, population, seed_id=seed, fold_id=0); binding = "a" * 64
    interrupted = train_policy(config, population, arm_id=ARM_IDS[1], seed_id=seed, fold_id=0, transforms=transforms, binding=binding, checkpoint_root=tmp_path / "resume", stop_after_root_update=2)
    assert interrupted.activity["tail_optimizer_updates"] == 2 and interrupted.activity["root_optimizer_updates"] == 2
    resumed = train_policy(config, population, arm_id=ARM_IDS[1], seed_id=seed, fold_id=0, transforms=transforms, binding=binding, checkpoint_root=tmp_path / "resume")
    uninterrupted = train_policy(config, population, arm_id=ARM_IDS[1], seed_id=seed, fold_id=0, transforms=transforms, binding=binding, checkpoint_root=tmp_path / "full")
    assert resumed.activity == uninterrupted.activity
    assert resumed.activity["target_materialization_events"] == 1
    left, right = load_checkpoint(tmp_path / "resume/root-0004.full.pt"), load_checkpoint(tmp_path / "full/root-0004.full.pt")
    assert torch.equal(left["root_state"]["beta"], right["root_state"]["beta"])
    assert torch.equal(left["tail_state"]["beta"], right["tail_state"]["beta"])
    assert left["activity"] == right["activity"]
    with pytest.raises(FileExistsError, match="create-once"):
        from experiments.candidates.ucope.conditioning_discriminator_r01.checkpoint import save_checkpoint
        save_checkpoint(tmp_path / "resume/root-0004.full.pt", left)
    with pytest.raises(ValueError, match="only .eval.pt"):
        load_checkpoint_models_read_only(tmp_path / "resume/root-0004.full.pt")
    projection = load_evaluation_projection(tmp_path / "resume/root-0004.eval.pt")
    assert left["evaluation_projection_sha256"] == hashlib.sha256((tmp_path / "resume/root-0004.eval.pt").read_bytes()).hexdigest()
    assert torch.equal(left["root_state"]["beta"], projection["root_state"]["beta"]) and torch.equal(left["tail_state"]["beta"], projection["tail_state"]["beta"])
    assert left["transforms"] == projection["transforms"]
    from experiments.candidates.ucope.conditioning_discriminator_r01.checkpoint import validate_checkpoint
    bad_hyper = dict(left); bad_hyper["root_optimizer"] = __import__("copy").deepcopy(left["root_optimizer"]); bad_hyper["root_optimizer"]["param_groups"][0]["lr"] = 1e-2
    with pytest.raises(ValueError, match="hyperparameter"): validate_checkpoint(bad_hyper)
    bad_target = dict(left); bad_target["frozen_root_targets"] = left["frozen_root_targets"].clone(); bad_target["frozen_root_targets"][0] = float("nan")
    with pytest.raises(ValueError, match="root-target"): validate_checkpoint(bad_target)
    bad_activity = dict(left); bad_activity["activity"] = dict(left["activity"], root_example_exposures=0)
    with pytest.raises(ValueError, match="frontier"): validate_checkpoint(bad_activity)


def test_reduced_workflow_reuses_two_prepared_folds_and_constant_shape_checkpoint_reload(tmp_path, monkeypatch):
    import experiments.candidates.ucope.conditioning_discriminator_r01.workflow as workflow_module
    prepare_calls, reload_calls = [], []
    original_prepare, original_reload = workflow_module.prepare_fold_data, workflow_module.load_checkpoint_models_read_only
    def observed_prepare(*args, **kwargs):
        value = original_prepare(*args, **kwargs); prepare_calls.append((value.fold_id, len(value.root_rows), len(value.tail_rows))); return value
    def observed_reload(path):
        reload_calls.append(Path(path)); return original_reload(path)
    monkeypatch.setattr(workflow_module, "prepare_fold_data", observed_prepare); monkeypatch.setattr(workflow_module, "load_checkpoint_models_read_only", observed_reload)
    result = workflow_module.run_workload(WorkloadConfig.test(), binding="b" * 64, scratch_root=tmp_path / "work")
    expected = expected_counts(WorkloadConfig.test())
    for key, value in expected.items(): assert result.activity[key] == value
    assert result.activity["environment_transitions"] > 0 and result.activity["root_optimizer_updates"] > 0
    assert len(result.transform_evidence) == 4 and len(result.initialization_parity) == 8
    assert all(row["positive_diagonal"] and row["target_fields_read"] == row["outcome_fields_read"] == 0 for row in result.transform_evidence)
    assert len(result.evaluations) == 8 and all(item.sampled["episodes"] > 0 for item in result.evaluations)
    assert all(value == 0 for value in result.zero_effects.values())
    assert prepare_calls == [(0, 160, 80), (1, 160, 80)]
    assert len(reload_calls) == 8
    assert result.runtime["execution_topology"]["deterministic_algorithms"] is True
    assert result.runtime["execution_topology"]["intraop_threads"] == 1


def test_assessment_v2_static_workload_and_timer_contract_are_exact():
    import inspect
    from experiments.candidates.ucope.conditioning_discriminator_r01.assessment_v2 import run_assessment_workload
    assert list(TIMER_SPECS) == ["entry_fixed", "environment_rows", "feature_row_assembly", "gram_design_binding_rows", "cholesky_factorization", "learner_optimizer_setup", "initialization_parity_training_rows", "initialization_parity_candidate_rows", "tail_update_steps", "root_target_rows", "root_update_steps", "snapshot_full_binding_rows", "evaluation_projection_reload", "candidate_evaluation", "sampled_episode_work", "sanitized_assembly"]
    assert TIMER_SPECS["candidate_evaluation"] == (4736, 28416, 6)
    assert TIMER_SPECS["sampled_episode_work"] == (128, 24576, 192)
    assert TIMER_SPECS["snapshot_full_binding_rows"] == (1280, 983040, 768)
    assert WorkloadConfig.assess().run_id == "ucope-bc-conditioning-r01-assessment-03"
    source = inspect.getsource(run_assessment_workload)
    assert "evaluate_checkpoint" not in source and "reduce_results" not in source and "build_oracle" not in source


def test_assessment_v2_snapshot_reload_is_exactly_one_physical_load_per_snapshot(tmp_path, monkeypatch):
    import experiments.candidates.ucope.conditioning_discriminator_r01.assessment_v2 as assessment_module
    calls = []
    def fake_load(path):
        calls.append(Path(path)); return {"fold_id": int(Path(path).parent.name.split("-")[-1])}, object()
    monkeypatch.setattr(assessment_module, "load_checkpoint_models_read_only", lambda path: (fake_load(path)[0], object(), object()))
    paths = []
    for index in range(8):
        path = tmp_path / f"fold-{index % 2}" / f"root-{index:04d}.pt"; path.parent.mkdir(exist_ok=True); paths.append(path)
    loaded = assessment_module.reload_snapshots_once(paths)
    assert len(loaded) == 8 and calls == paths


def _support(arm, seed, fold, update, *, hamming, regret, agreement, competent=False, near=False, support="even"):
    periods = K_EVAL if support == "even" else K_TRAIN
    return SupportEvaluation(arm, seed, fold, update, support, periods, {}, {}, {}, {}, True, True, {}, {}, hamming, {"numerator": regret.numerator, "denominator": regret.denominator}, {"numerator": agreement.numerator, "denominator": agreement.denominator}, competent, near)


def _panel(*, separated: bool):
    values = []
    for update in (160, 320):
        for arm in ARM_IDS:
            for seed_index in range(3):
                seed = f"s{seed_index}"
                for fold in (0, 1):
                    white = arm == ARM_IDS[1]
                    good = separated and white
                    even = _support(arm, seed, fold, update, hamming=0 if good else 2, regret=Fraction(0) if good else Fraction(1, 10), agreement=Fraction(1) if good else Fraction(4, 5), competent=good)
                    odd = _support(arm, seed, fold, update, hamming=2, regret=Fraction(1, 10), agreement=Fraction(4, 5), support="odd")
                    values.append(CheckpointEvaluation(arm, seed, fold, update, odd, even, {}))
    return values


def test_exact_dominance_stable_positive_falsifier_and_contrary_predicates():
    positive = reduce_results(_panel(separated=True), seed_ids=("s0", "s1", "s2"), final_update=320)
    assert positive["conditioning_positive"] and positive["stable_clear_advantage_160_320"]
    assert not positive["falsifier"] and not positive["contrary_park_observation"]
    null = reduce_results(_panel(separated=False), seed_ids=("s0", "s1", "s2"), final_update=320)
    assert null["falsifier"] and null["contrary_park_observation"] and not null["conditioning_positive"]


def _classified_timer_rows():
    rows = []
    for key, (assessment_units, science_units, multiplier) in TIMER_SPECS.items():
        if key == "entry_fixed": continue
        rows.append({"timer_key": key, "wall_seconds": 0.01, "cpu_seconds": 0.01, "io_read_bytes": 1, "io_write_bytes": 1, "scratch_bytes_created": 1, "durable_bytes_created": 1, "assessment_work_units": assessment_units, "science_work_units": science_units, "multiplier": multiplier})
    return rows


def test_assessment_v2_projection_manifest_admission_and_tamper_fences(tmp_path):
    telemetry = {"wall_seconds": 0.01, "process_tree_peak_rss_bytes": 10_000_000, "scratch_high_water_bytes": 1000, "durable_high_water_bytes": 1000, "io_read_bytes": 100, "io_write_bytes": 100, "aggregate_io_bytes": 200, "thread_count_peak": 1, "process_count_peak": 1, "root_process_count": 1, "child_process_count_peak": 0, "cpu_seconds": 0.01, "cpu_core_equivalents": 1.0, "logical_cpu_count": 8, "host_cpu_occupancy": 0.125, "samples": 2}
    classified = _classified_timer_rows(); total_value = len(classified) + 2; totals = {"wall_seconds": len(classified) * 0.01 + 0.02, "cpu_seconds": len(classified) * 0.01 + 0.02, "io_read_bytes": total_value, "io_write_bytes": total_value, "scratch_bytes_created": total_value, "durable_bytes_created": total_value}
    telemetry["wall_seconds"] = totals["wall_seconds"]; telemetry["cpu_seconds"] = totals["cpu_seconds"]; telemetry["io_read_bytes"] = total_value; telemetry["io_write_bytes"] = total_value; telemetry["aggregate_io_bytes"] = 2 * total_value
    topology = {"deterministic_algorithms": True, "intraop_threads": 1, "interop_threads": 1, "interop_supported": True, "configured_once": True, "static_no_spawn": {"files_checked": 3, "spawn_imports": 0, "topology": "single_inline_root_process"}}
    assessment = build_assessment(classified_timer_rows=classified, invocation_telemetry=telemetry, topology_record=topology, observed_snapshot_count=8, source_aggregate="c" * 64, admission_binding={"path": "assessment-03.json", "sha256": "a" * 64, "size_bytes": 1, "captured_at": "2026-09-01T00:00:00Z", "assessed_at": "2026-09-01T00:00:01Z"}, scratch_bytes_created=total_value, durable_bytes_created=total_value)
    assert validate_assessment(assessment)["disposition"] == "PERFORMANCE_READY"
    assert assessment["snapshot_count_check"] == {"assessment": 8, "science": 48, "pass": True}
    assert not any(token in json.dumps(assessment).lower() for token in ("competence", "regret", "oracle", "checkpoint"))
    multiplier_sum = sum(spec[2] for key, spec in TIMER_SPECS.items() if key != "entry_fixed")
    assert assessment["projection"]["central_wall_seconds"] == pytest.approx(0.02 + 0.01 * multiplier_sum)
    assert assessment["projection"]["guarded_wall_seconds"] == pytest.approx(60 + 1.25 * (0.02 + 0.01 * multiplier_sum))
    assert assessment["projection"]["rss_cap_bytes"] == 322_667_520
    assert assessment["projection"]["read_cap_bytes"] == 33_554_432 + math.ceil(1.25 * (2 + multiplier_sum))
    assert assessment["projection"]["scratch_cap_bytes"] % 1_048_576 == 0
    forbidden = ("loss", "coefficient", "policy", "checkpoint", "oracle", "regret", "agreement", "competence", "separation", "acquisition", "score", "root_vector", "branch", "prediction", "selection", "action", "return", "metric", "model", "tensor", "optimizer", "snapshot", "payload")
    for token in forbidden:
        bad = copy.deepcopy(assessment); bad["telemetry"][f"{token}_field"] = 1
        with pytest.raises(ValueError, match="forbidden"): validate_assessment(bad)
    for field in ("telemetry", "invocation_totals", "admission_binding", "projection", "retained_assessment_01", "retained_assessment_02"):
        bad = copy.deepcopy(assessment); bad[field]["benign_extra"] = 1
        with pytest.raises(ValueError, match="inventory|binding|ledger|arithmetic"): validate_assessment(bad)
    for interop_value in (False, None):
        bad = copy.deepcopy(assessment); bad["topology"]["interop_supported"] = interop_value
        with pytest.raises(ValueError, match="exact execution topology"): validate_assessment(bad)
    bad_reconcile = copy.deepcopy(assessment); bad_reconcile["timer_rows"][1]["wall_seconds"] += 1
    with pytest.raises(ValueError, match="reconciliation"): validate_assessment(bad_reconcile)
    bad_units = copy.deepcopy(assessment); bad_units["timer_rows"][10]["assessment_work_units"] = 4735
    with pytest.raises(ValueError, match="work/multiplier"): validate_assessment(bad_units)
    for bad_snapshot_check in ({"assessment": 7, "science": 48, "pass": False}, {"assessment": 8, "science": 47, "pass": True}):
        bad = copy.deepcopy(assessment); bad["snapshot_count_check"] = bad_snapshot_check
        with pytest.raises(ValueError, match="snapshot count"): validate_assessment(bad)
    manifest = build_manifest(assessment=assessment, source_revision="d" * 40, source_inventory=[{"path": "x.py", "size_bytes": 1, "sha256": "e" * 64}], output_root="frozen", assessment_sha256="f" * 64, assessment_size_bytes=123)
    validate_manifest(manifest)
    assert manifest["performance_assessment"]["assessment_id"] == "ucope-bc-conditioning-r01-assessment-03"
    assert manifest["performance_assessment"]["snapshot_count_check"] == {"assessment": 8, "science": 48, "pass": True}
    assert manifest["resource_caps"]["aggregate_io_bytes"] == assessment["projection"]["aggregate_io_cap"]
    bad_manifest_count = copy.deepcopy(manifest); bad_manifest_count["performance_assessment"]["snapshot_count_check"]["science"] = 47
    with pytest.raises(ValueError, match="assessment-03 binding"): validate_manifest(bad_manifest_count)
    for interop_value in (False, None):
        bad = copy.deepcopy(manifest); bad["execution_topology"]["interop_supported"] = interop_value
        with pytest.raises(ValueError, match="exact execution topology"): validate_manifest(bad)
    tampered = dict(manifest, output_root="changed")
    with pytest.raises(ValueError, match="binding"):
        validate_manifest(tampered)
    now = datetime_module.datetime.now(datetime_module.timezone.utc)
    receipt = {"schema_version": 1, "captured_at": (now - datetime_module.timedelta(seconds=2)).isoformat().replace("+00:00", "Z"), "assessed_at": (now - datetime_module.timedelta(seconds=1)).isoformat().replace("+00:00", "Z"), "measurement_source": "fixture", "minimum_available_bytes": 4 * 1024**3, "available_physical_bytes": 4 * 1024**3, "cgroup_memory_max_bytes": None, "cgroup_memory_current_bytes": None, "cgroup_headroom_bytes": None, "effective_available_bytes": 4 * 1024**3, "physical_floor_pass": True, "effective_floor_pass": True, "passed": True, "failure_reasons": []}
    validate_admission(receipt, now=now)
    with pytest.raises(ValueError, match="below"):
        validate_admission(dict(receipt, effective_available_bytes=4 * 1024**3 - 1), now=now)
    with pytest.raises(ValueError, match="stale"):
        validate_admission(receipt, now=now + datetime_module.timedelta(minutes=10))
    destination = tmp_path / "once.json"; atomic_create_json(destination, {"a": 1})
    with pytest.raises(FileExistsError): atomic_create_json(destination, {"a": 1})


def test_retained_assessment_01_bytes_and_prepare_path_are_immutable():
    retained = Path("temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-01.json")
    assert hashlib.sha256(retained.read_bytes()).hexdigest() == "1dea9ee1762c1198b4cb71a10ac2450b8a6eadfd28edf3251f30151ffd9fb452"
    runner = _load_runner()
    with pytest.raises(runner.RunnerRefusal, match="frozen path"):
        runner._exact_path(retained, runner.ASSESSMENT_PATH, "assessment")
    retained_02 = Path("temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-02.json")
    assert hashlib.sha256(retained_02.read_bytes()).hexdigest() == "1456280de0bde1be6d8bb73448b5918d3ad5be963a1f1f6d5bf9862c32878a20"
    with pytest.raises(runner.RunnerRefusal, match="frozen path"): runner._exact_path(retained_02, runner.ASSESSMENT_PATH, "assessment")


def test_assessment_v2_scratch_and_durable_roots_are_disjoint(tmp_path):
    runner = _load_runner(); scratch, durable = runner.ASSESSMENT_SCRATCH_PATH.resolve(), runner.ASSESSMENT_PATH.parent.resolve()
    assert scratch != durable and scratch not in durable.parents and durable not in scratch.parents
    local_scratch, local_durable = tmp_path / "scratch", tmp_path / "durable"; local_scratch.mkdir(); local_durable.mkdir()
    (local_scratch / "s.bin").write_bytes(b"s" * 7); (local_durable / "d.bin").write_bytes(b"d" * 11)
    from experiments.candidates.ucope.conditioning_discriminator_r01.resources import directory_bytes
    assert directory_bytes(local_scratch) == 7 and directory_bytes(local_durable) == 11


def test_complete_result_reducer_and_checkpoint_tamper_detection(tmp_path, monkeypatch):
    workload = run_workload(WorkloadConfig.test(), binding="1" * 64, scratch_root=tmp_path / "work")
    assessment = {"dummy": True}; manifest = {"dummy": True}
    inventory = stage_checkpoints(workload.checkpoints, staging_root=tmp_path / "complete")
    result = build_complete_result(workload, manifest=manifest, admission_record={"sha256": "2" * 64}, resource_ledger={}, checkpoint_inventory=inventory)
    validate_complete_result(result, complete_root=tmp_path / "complete", allow_test=True)
    runner = _load_runner()
    import experiments.candidates.ucope.conditioning_discriminator_r01.host as host_module
    monkeypatch.setattr(host_module, "generate_population", lambda *a, **k: (_ for _ in ()).throw(AssertionError("validate generated episodes")))
    monkeypatch.setattr(host_module, "execute_episode", lambda *a, **k: (_ for _ in ()).throw(AssertionError("validate replayed episodes")))
    recomputed = runner.independent_recompute(tmp_path / "complete", result, WorkloadConfig.test())
    assert recomputed["evaluations"] == result["evaluations"] and recomputed["reducer"] == result["reducer"]
    duplicate = copy.deepcopy(result); duplicate["evaluations"].append(copy.deepcopy(duplicate["evaluations"][0]))
    with pytest.raises(ValueError, match="evaluation inventory"): validate_complete_result(duplicate, complete_root=tmp_path / "complete", allow_test=True)
    outer = copy.deepcopy(result); outer["evaluations"][0]["seed_id"] = "outer-drift"
    with pytest.raises(ValueError, match="outer/support identity"): validate_complete_result(outer, complete_root=tmp_path / "complete", allow_test=True)
    sampled = copy.deepcopy(result); sampled["evaluations"][0]["sampled"]["episodes"] -= 1
    with pytest.raises(ValueError, match="sampled inventory"): validate_complete_result(sampled, complete_root=tmp_path / "complete", allow_test=True)
    missing_activity = copy.deepcopy(result); del missing_activity["activity"]["root_rows"]
    with pytest.raises(ValueError, match="activity inventory"): validate_complete_result(missing_activity, complete_root=tmp_path / "complete", allow_test=True)
    extra_activity = copy.deepcopy(result); extra_activity["activity"]["unexpected"] = 0
    with pytest.raises(ValueError, match="activity inventory"): validate_complete_result(extra_activity, complete_root=tmp_path / "complete", allow_test=True)
    transition_activity = copy.deepcopy(result); transition_activity["activity"]["sampled_evaluation_transitions"] += 1
    with pytest.raises(ValueError, match="sampled transition activity"): validate_complete_result(transition_activity, complete_root=tmp_path / "complete", allow_test=True)
    for interop_value in (False, None):
        bad = copy.deepcopy(result); bad["runtime"]["execution_topology"]["interop_supported"] = interop_value
        with pytest.raises(ValueError, match="exact execution topology"): validate_complete_result(bad, complete_root=tmp_path / "complete", allow_test=True)
    changed = dict(result); changed["reducer"] = dict(changed["reducer"], falsifier=not changed["reducer"]["falsifier"])
    with pytest.raises(ValueError, match="reducer"):
        validate_complete_result(changed, complete_root=tmp_path / "complete", allow_test=True)
    path = tmp_path / "complete" / inventory[0]["projection_locator"]; path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="tamper"):
        validate_complete_result(result, complete_root=tmp_path / "complete", allow_test=True)


def test_static_and_runtime_firewalls_and_cli_exact_effect_surface(tmp_path):
    package = Path("experiments/candidates/ucope/conditioning_discriminator_r01")
    assert validate_import_firewall(tuple(package.glob("*.py")))["historical_imports"] == 0
    with pytest.raises(ValueError, match="historical"):
        validate_runtime_path(tmp_path / "ucope-scout-r01-b1-forbidden")
    assert all(value == 0 for value in zero_effect_ledger().values())
    runner = _load_runner(); parser = runner._parser()
    assert set(parser._subparsers._group_actions[0].choices) == {"assess-run", "prepare-run", "run", "validate"}
    with pytest.raises(SystemExit): parser.parse_args(["run", "--seed", "forbidden"])
    with pytest.raises(runner.RunnerRefusal, match="frozen path"):
        runner._exact_path(tmp_path / "alternate", runner.OUTPUT_ROOT, "output root")
    assert not runner.CONTROL_ROOT.exists() or runner.CONTROL_ROOT.is_dir()


def test_checkpoint_staging_is_copy_only_and_complete_exposure_removes_work(tmp_path):
    sources = {}
    for name in ("full", "projection", "binding"):
        source = tmp_path / f"source-{name}"; source.write_bytes(f"immutable-{name}".encode()); sources[name] = source
    record = {"arm_id": ARM_IDS[0], "seed_id": "technical", "fold_id": 0, "root_update": 2, **{name: {"path": str(path), "size_bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in sources.items()}}
    staged = stage_checkpoints([record], staging_root=tmp_path / "staging"); destination = tmp_path / "staging" / staged[0]["projection_locator"]; source = sources["projection"]
    original_destination = destination.read_bytes(); source.write_bytes(b"mutated-source")
    assert destination.read_bytes() == original_destination
    if hasattr(destination.stat(), "st_ino") and destination.stat().st_ino:
        assert destination.stat().st_ino != source.stat().st_ino
    runner = _load_runner(); output = tmp_path / "output"; work = output / "work"; hidden = output / ".complete-staging-test"; work.mkdir(parents=True); hidden.mkdir(); (work / "scratch").write_text("x"); (hidden / "result.json").write_text("{}")
    complete = runner._expose_complete(output, work, hidden)
    assert complete.is_dir() and not work.exists() and not hidden.exists()


def test_monitor_start_failure_quarantines_created_exact_identity(tmp_path, monkeypatch):
    runner = _load_runner(); manifest_path = tmp_path / "manifest.json"; admission_path = tmp_path / "admission.json"; output = tmp_path / "output"
    manifest_path.write_text("{}"); admission_path.write_text("{}")
    monkeypatch.setattr(runner, "MANIFEST_PATH", manifest_path); monkeypatch.setattr(runner, "ADMISSION_PATH", admission_path); monkeypatch.setattr(runner, "OUTPUT_ROOT", output)
    monkeypatch.setattr(runner, "validate_manifest", lambda value: {"output_root": str(output)})
    monkeypatch.setattr(runner, "validate_admission", lambda value: value)
    monkeypatch.setattr(runner, "_validate_bound_source", lambda manifest: None); monkeypatch.setattr(runner, "_validate_bound_assessment", lambda manifest: None)
    class FailingMonitor:
        def __init__(self, *args, **kwargs): pass
        def start(self): raise RuntimeError("monitor-start-failure")
    monkeypatch.setattr(runner, "ResourceMonitor", FailingMonitor)
    with pytest.raises(RuntimeError, match="monitor-start-failure"):
        runner.run_result(manifest_path, admission_path, output)
    assert not (output / "work").exists() and not any(path.name.startswith(".complete-staging") for path in output.iterdir())
    quarantines = list(output.glob("quarantine-*")); assert len(quarantines) == 1
    assert (quarantines[0] / "work").is_dir() and (quarantines[0] / "staging").is_dir() and (quarantines[0] / "failure.json").is_file()


def test_resource_monitor_reports_real_process_tree_fs_and_io(tmp_path):
    scratch, durable = tmp_path / "scratch", tmp_path / "durable"; scratch.mkdir(); durable.mkdir()
    monitor = ResourceMonitor(scratch, durable, interval=0.01).start()
    (scratch / "bytes.bin").write_bytes(b"x" * 1024)
    result = monitor.finish()
    assert result["wall_seconds"] >= 0 and result["process_tree_peak_rss_bytes"] > 0
    assert result["process_count_peak"] == 1 and result["root_process_count"] == 1 and result["child_process_count_peak"] == 0
    assert result["scratch_high_water_bytes"] >= 1024 and result["samples"] >= 2
    assert result["aggregate_io_bytes"] == result["io_read_bytes"] + result["io_write_bytes"]
    assert result["logical_cpu_count"] > 0 and result["cpu_core_equivalents"] >= 0 and result["host_cpu_occupancy"] >= 0
