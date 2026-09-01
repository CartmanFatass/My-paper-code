import argparse
import ast
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import threading

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[5]
MODULE_PATH = PROJECT_ROOT / "experiments/candidates/ucope/contextual_paid_acquisition_r01/structural_competence.py"
RUNNER_PATH = PROJECT_ROOT / "scripts/run_ucope_structural_competence_certificate.py"
STRUCTURAL_REPLAY_PATH = (
    PROJECT_ROOT
    / "experiments/candidates/ucope/contextual_paid_acquisition_r01/structural_replay.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def structural():
    module = _load(MODULE_PATH, "_test_ucope_structural_competence")
    prefix = "experiments.candidates.ucope.contextual_paid_acquisition_r01"
    contract = importlib.import_module(f"{prefix}.contract")
    oracle = importlib.import_module(f"{prefix}.oracle")
    module.configure_postseal_runtime({
        "K_TEST": contract.K_TEST,
        "as_fraction": contract.as_fraction,
        "context_id": contract.context_id,
        "contexts": contract.contexts,
        "direct_probe_value": oracle.direct_probe_value,
        "expected_tail_value": oracle.expected_tail_value,
        "informed_value": oracle.informed_value,
        "joint_count_probability": oracle.joint_count_probability,
        "optimal_tail": oracle.optimal_tail,
        "posterior_short": oracle.posterior_short,
    })
    return module


@pytest.fixture(scope="module")
def runner():
    return _load(RUNNER_PATH, "_test_ucope_structural_runner")


@pytest.fixture(scope="module")
def structural_replay():
    return _load(STRUCTURAL_REPLAY_PATH, "_test_ucope_structural_replay")


def _subcommands(parser):
    actions = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
    assert len(actions) == 1
    return actions[0].choices


CONTEXT_IDS = (
    "LINKED-p13_20-c9_100", "LINKED-p13_20-c7_50",
    "LINKED-p17_20-c9_100", "LINKED-p17_20-c7_50",
    "SEVERED-p13_20-c9_100", "SEVERED-p13_20-c7_50",
    "SEVERED-p17_20-c9_100", "SEVERED-p17_20-c7_50",
)


def _fit_record(structural, coefficients, row_count):
    width = len(coefficients)
    return {
        "solver": structural.EXACT_SOLVER_LAW,
        "expected_rank": width,
        "rank": width,
        "rank_status": "FULL_RANK",
        "row_count": row_count,
        "normal_matrix": [
            [Fraction(int(row == column)) for column in range(width)]
            for row in range(width)
        ],
        "normal_rhs": list(coefficients),
        "coefficients": tuple(coefficients),
    }


def _rank_stop_record(structural, width, row_count):
    return {
        "solver": structural.EXACT_SOLVER_LAW,
        "expected_rank": width,
        "rank": 0,
        "rank_status": "RANK_DEFICIENT_STOP",
        "row_count": row_count,
        "normal_matrix": [[Fraction(0) for _ in range(width)] for _ in range(width)],
        "normal_rhs": [Fraction(0) for _ in range(width)],
        "coefficients": None,
    }


def _support(root):
    if root:
        return {
            "rows": 81_920,
            "groups": 10_240,
            "contexts": {cell: 10_240 for cell in CONTEXT_IDS},
            "strata": {
                f"{action}:{period}": 8_192
                for action in ("PROBE", "IMMEDIATE")
                for period in (1, 3, 5, 7, 9)
            },
        }
    return {
        "rows": 40_960,
        "groups": 5_120,
        "contexts": {cell: 5_120 for cell in CONTEXT_IDS},
        "strata": {f"PROBE:{period}": 8_192 for period in (1, 3, 5, 7, 9)},
    }


def _fit_document(structural, root_record, tail_record, receipt):
    policies = [
        {
            "policy_fold": fold,
            "root_source_fold": fold,
            "tail_source_fold": 1 - fold,
            "root": deepcopy(root_record),
            "tail": deepcopy(tail_record),
            "root_support": _support(True),
            "tail_support": _support(False),
        }
        for fold in (0, 1)
    ]
    full_rank = root_record["rank"] == 7 and tail_record["rank"] == 5
    return {
        "format": structural.FIT_FORMAT,
        "complete": True,
        "sealed": True,
        "binding_receipt": dict(receipt),
        "fold_law": {
            "group_key": "(seed_slot,index)",
            "fold_id": "(index//10)%2",
            "dependence_claim": structural.FOLD_DEPENDENCE_CLAIM,
            "source_assignment": "GLOBAL_BALANCED_RANK_WITH_CROSS_FOLD_DEPENDENCE",
            "behavior_strata": "ACTION_PERIOD_GROUP_COUNTS_EXACTLY_EQUAL_WITHIN_EACH_HALF",
            "combination": "BOTH_FOLD_POLICIES_MUST_PASS",
        },
        "tail_basis": list(structural.TAIL_BASIS),
        "root_basis": list(structural.ROOT_BASIS),
        "solver": structural.EXACT_SOLVER_LAW,
        "arithmetic": structural.EXACT_ARITHMETIC_LAW,
        "expected_ranks": {"tail": 5, "root": 7},
        "activity": dict(structural.FIT_ACTIVITY),
        "process_boundary_claim": structural.FIT_DATA_DEPENDENCY_CLAIM,
        "full_rank": full_rank,
        "seeds": [
            {"seed_slot": seed, "policies": deepcopy(policies)}
            for seed in structural.SEED_SLOTS
        ],
    }


def _resource_ledger(runner, entry="run", *, passed=True):
    observed = {
        "workers": 1,
        "wall_seconds": 0 if passed else runner.RESOURCE_CEILINGS["wall_seconds"],
        "cpu_seconds": 0,
        "peak_process_threads": 1,
        "peak_rss_bytes": 1,
        "scientific_child_processes": 0,
        "scratch_high_water_bytes": 0,
        "durable_high_water_bytes": 0,
        "read_bytes": 0,
        "write_bytes": 0,
        "aggregate_io_bytes": 0,
    }
    return {
        "format": "UCOPE_STRUCTURAL_RESOURCE_LEDGER_V1",
        "entry": entry,
        "ceilings": dict(runner.RESOURCE_CEILINGS),
        "measurement_scope": runner.RESOURCE_MEASUREMENT_SCOPE,
        "sample_interval_seconds": runner.RESOURCE_SAMPLE_SECONDS,
        "publication_headroom": dict(runner.PUBLICATION_HEADROOM),
        "observed": observed,
        "passed": passed,
    }


def _monitor_type(runner, *, passed=True):
    class FixedMonitor:
        def __init__(self, entry, **_kwargs):
            self.entry = entry

        def start(self):
            return self

        def set_paths(self, **_kwargs):
            return None

        def finish(self):
            return _resource_ledger(runner, self.entry, passed=passed)

    return FixedMonitor


def _sandbox_admission(tmp_path, runner, monkeypatch, entry="run"):
    project = tmp_path / "control-project"
    controls = project / "controls"
    monkeypatch.setattr(runner, "PROJECT_ROOT", project)
    monkeypatch.setattr(runner, "CONTROL_ROOT", controls)
    monkeypatch.setattr(runner, "ASSESSMENT_ROOT", controls / "assessments")
    monkeypatch.setattr(runner, "require_frozen_execution_environment", lambda: None)
    relative = f"controls/resource-receipts/{entry}-{'0' * 32}.json"
    payload = {
        "schema_version": 1,
        "captured_at": "2026-08-31T00:00:00.000000Z",
        "assessed_at": "2026-08-31T00:00:00.000001Z",
        "measurement_source": "synthetic-test",
        "minimum_available_bytes": 4 * 1024**3,
        "passed": True,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "available_physical_bytes": 8 * 1024**3,
        "cgroup_memory_max_bytes": None,
        "cgroup_memory_current_bytes": None,
        "cgroup_headroom_bytes": None,
        "effective_available_bytes": 8 * 1024**3,
        "failure_reasons": [],
    }
    path = project / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "entry": entry,
        "preflight_receipt_relative_path": relative,
        **payload,
    }


def _store_control_ledger(runner, ledger, name):
    relative = f"controls/resource-receipts/{name}.json"
    runner.atomic_create_json(runner.PROJECT_ROOT / relative, ledger)
    return relative


def _fixed_assessment_work():
    return {
        "prefit_members_compared": 90,
        "canonical_rows_replayed": 1_638_400,
        "exact_in_memory_solve_passes": 2,
        "independent_prefit_modules": 2,
        "exact_row_decodes": 9_830_400,
        "exact_root_normal_accumulations": 3_276_800,
        "postfit_members_opened": 0,
        "serialized_solve_documents": 0,
        "scientific_outputs_created": 0,
    }


def _materialize_valid_assessment(tmp_path, runner, monkeypatch):
    admission = _sandbox_admission(
        tmp_path, runner, monkeypatch, entry="assess-run"
    )
    ledger_relative = (
        "controls/resource-receipts/"
        f"assess-run-ledger-{'1' * 32}.json"
    )
    runner.atomic_create_json(
        runner.PROJECT_ROOT / ledger_relative,
        _resource_ledger(runner, entry="assess-run"),
    )
    root = runner.ASSESSMENT_ROOT / f"assess-run-{'2' * 32}"
    receipt = root / runner.ASSESSMENT_RECEIPT_FILENAME
    runner.atomic_create_json(
        receipt,
        {
            "format": runner.ASSESSMENT_FORMAT,
            "entry": "assess-run",
            "complete": True,
            "performance_disposition": "PERFORMANCE_READY",
            "scope": "RESOURCE_AND_TECHNICAL_ONLY",
            "exact_refit_equal": True,
            "work": _fixed_assessment_work(),
            "resource_admission_relative_path": admission[
                "preflight_receipt_relative_path"
            ],
            "resource_ledger_relative_path": ledger_relative,
        },
    )
    return receipt, admission, runner.PROJECT_ROOT / ledger_relative


def _freeze_synthetic_result(output, runner, monkeypatch):
    root = Path(output)
    raw = str(root)
    monkeypatch.setattr(runner, "FROZEN_RESULT_ROOT", root, raising=False)
    monkeypatch.setattr(runner, "FROZEN_RESULT_ROOT_ARG", raw, raising=False)
    return raw


def test_runner_surface_has_fixed_inputs_and_no_scientific_overrides(runner):
    commands = _subcommands(runner.build_parser())
    assert set(commands) == {
        "freeze-reference-bundle", "check-binding", "assess-run", "run", "validate",
    }
    for name in ("freeze-reference-bundle", "check-binding", "assess-run"):
        assert {action.dest for action in commands[name]._actions if action.dest != "help"} == set()
    for name in ("run", "validate"):
        actions = [action for action in commands[name]._actions if action.dest != "help"]
        assert [(action.dest, action.required) for action in actions] == [("output_root", True)]
    rendered = RUNNER_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "--manifest", "--support", "--belief-result", "--bundle-root", "--seed", "--fold", "--k-test",
        "--k-train", "--threshold", "--retry", "--append", "--resample",
    ):
        assert forbidden not in rendered


def test_runner_freezes_absolute_execution_environment(runner):
    assert runner.FROZEN_PROJECT_ROOT == Path("C:/Projects/HMASD")
    assert runner.FROZEN_PYTHON_EXECUTABLE == Path(
        "C:/Users/fires/AppData/Local/Programs/Python/Python311/python.exe"
    )
    assert runner.FROZEN_PYTHON_VERSION == (3, 11, 9)
    assert runner.FROZEN_PYTHON_IMPLEMENTATION == "CPython"
    assert runner.FROZEN_RESULT_ROOT == Path(
        "C:/Projects/HMASD/temp/directions/ucope/exp/"
        "ucope-structural-competence-r01"
    )
    assert runner.FROZEN_RESULT_ROOT_ARG == (
        "temp/directions/ucope/exp/ucope-structural-competence-r01"
    )


def test_v2_qualification_namespace_and_formats_are_exact(runner):
    qualification_parent = runner.FROZEN_PROJECT_ROOT / "temp/directions/ucope/exp"
    assert runner.FIXED_BUNDLE_ROOT == (
        qualification_parent
        / "ucope-structural-competence-reference-bundle-v2"
    )
    assert runner.CONTROL_ROOT == (
        qualification_parent / "ucope-structural-competence-controls-v2"
    )
    assert runner.ASSESSMENT_ROOT == runner.CONTROL_ROOT / "assessments"
    assert runner.REFERENCE_BUNDLE_FORMAT == (
        "UCOPE_STRUCTURAL_REFERENCE_BUNDLE_V2"
    )
    assert runner.CONTROL_RECEIPT_FORMAT == "UCOPE_STRUCTURAL_CONTROL_STOP_V2"
    assert runner.ASSESSMENT_FORMAT == (
        "UCOPE_STRUCTURAL_OUTCOME_BLIND_ASSESSMENT_V2"
    )
    assert runner.FIXED_BUNDLE_ROOT != (
        qualification_parent / "ucope-structural-competence-reference-bundle"
    )
    assert runner.CONTROL_ROOT != (
        qualification_parent / "ucope-structural-competence-controls"
    )
    assert runner.CONTROL_ROOT == (
        Path("C:/Projects/HMASD/temp/directions/ucope/exp/")
        / "ucope-structural-competence-controls-v2"
    )
    assert "EXECUTION_ENVIRONMENT" in runner.CONTROL_STAGES
    assert runner.CONTROL_STAGES == frozenset().union(
        *runner.CONTROL_STAGES_BY_ENTRY.values()
    )


def test_v1_bundle_and_ready_evidence_cannot_qualify_v2_and_remain_untouched(
    tmp_path, runner, monkeypatch,
):
    old_bundle = tmp_path / "ucope-structural-competence-reference-bundle"
    old_bundle.mkdir()
    old_manifest = runner._bundle_manifest()
    old_manifest["format"] = "UCOPE_STRUCTURAL_REFERENCE_BUNDLE_V1"
    old_manifest_path = old_bundle / "manifest.json"
    old_manifest_path.write_bytes(runner._plain_canonical_bytes(old_manifest))
    before_manifest = old_manifest_path.read_bytes()
    with pytest.raises(runner.DataBindingMismatch, match="envelope"):
        runner._validate_manifest_shape(old_manifest)

    old_assessment = (
        tmp_path / "ucope-structural-competence-controls" / "assessments"
        / f"assess-run-{'1' * 32}" / runner.ASSESSMENT_RECEIPT_FILENAME
    )
    old_assessment.parent.mkdir(parents=True)
    old_assessment.write_bytes(
        runner._plain_canonical_bytes({
            "format": "UCOPE_STRUCTURAL_OUTCOME_BLIND_ASSESSMENT_V1",
            "entry": "assess-run",
            "complete": True,
            "performance_disposition": "PERFORMANCE_READY",
            "scope": "RESOURCE_AND_TECHNICAL_ONLY",
            "exact_refit_equal": True,
            "work": _fixed_assessment_work(),
            "resource_admission_relative_path": (
                "ucope-structural-competence-controls/resource-receipts/"
                f"assess-run-{'2' * 32}.json"
            ),
            "resource_ledger_relative_path": (
                "ucope-structural-competence-controls/resource-receipts/"
                f"assess-run-ledger-{'3' * 32}.json"
            ),
        })
    )
    before_ready = old_assessment.read_bytes()
    monkeypatch.setattr(runner, "ASSESSMENT_ROOT", old_assessment.parents[1])
    with pytest.raises(
        runner.AssessmentQualificationError,
        match="not complete PERFORMANCE_READY",
    ):
        runner.validate_performance_assessment()
    monkeypatch.setattr(
        runner, "ASSESSMENT_ROOT",
        tmp_path / "ucope-structural-competence-controls-v2" / "assessments",
    )
    with pytest.raises(runner.AssessmentQualificationError, match="absent"):
        runner.validate_performance_assessment()
    assert old_manifest_path.read_bytes() == before_manifest
    assert old_assessment.read_bytes() == before_ready


def test_execution_environment_guard_rejects_cwd_interpreter_and_version_drift(
    tmp_path, runner, monkeypatch,
):
    runner.require_frozen_execution_environment()

    monkeypatch.chdir(tmp_path)
    with pytest.raises(runner.ExecutionEnvironmentMismatch, match="working directory"):
        runner.require_frozen_execution_environment()
    monkeypatch.chdir(runner.FROZEN_PROJECT_ROOT)

    monkeypatch.setattr(runner, "PROJECT_ROOT", tmp_path)
    with pytest.raises(runner.ExecutionEnvironmentMismatch, match="project root"):
        runner.require_frozen_execution_environment()
    monkeypatch.setattr(runner, "PROJECT_ROOT", runner.FROZEN_PROJECT_ROOT)

    monkeypatch.setattr(runner.sys, "executable", str(tmp_path / "python.exe"))
    with pytest.raises(runner.ExecutionEnvironmentMismatch, match="interpreter executable"):
        runner.require_frozen_execution_environment()
    monkeypatch.setattr(runner.sys, "executable", str(runner.FROZEN_PYTHON_EXECUTABLE))

    monkeypatch.setattr(runner.sys, "version_info", (3, 11, 10, "final", 0))
    with pytest.raises(runner.ExecutionEnvironmentMismatch, match="interpreter version"):
        runner.require_frozen_execution_environment()


def test_four_public_entries_publish_unique_v2_environment_controls_before_state(
    tmp_path, runner, monkeypatch,
):
    controls = tmp_path / "ucope-structural-competence-controls-v2"
    bundle = tmp_path / "ucope-structural-competence-reference-bundle-v2"
    result = tmp_path / "ucope-structural-competence-r01"
    raw_result = _freeze_synthetic_result(result, runner, monkeypatch)
    monkeypatch.setattr(runner, "CONTROL_ROOT", controls)
    monkeypatch.setattr(runner, "ASSESSMENT_ROOT", controls / "assessments")
    monkeypatch.setattr(runner, "FIXED_BUNDLE_ROOT", bundle)

    entries = []

    def reject_environment():
        entries.append("environment")
        raise runner.ExecutionEnvironmentMismatch("synthetic environment drift")

    monkeypatch.setattr(
        runner, "require_frozen_execution_environment", reject_environment
    )
    monkeypatch.setattr(
        runner, "_admit_memory",
        lambda _entry: pytest.fail("memory reached after environment drift"),
    )
    monkeypatch.setattr(
        runner, "_persist_entry_admission",
        lambda *_args, **_kwargs: pytest.fail(
            "admission persistence reached after environment drift"
        ),
    )
    monkeypatch.setattr(
        runner, "verify_data_binding",
        lambda: pytest.fail("binding reached after environment drift"),
    )
    monkeypatch.setattr(
        runner, "ResourceMonitor",
        lambda *_args, **_kwargs: pytest.fail(
            "resource sampler reached after environment drift"
        ),
    )
    monkeypatch.setattr(
        runner.STRUCTURAL, "fit_structural_artifact",
        lambda *_args, **_kwargs: pytest.fail("fit reached after environment drift"),
    )
    monkeypatch.setattr(
        runner.STRUCTURAL, "evaluate_sealed_fit",
        lambda *_args, **_kwargs: pytest.fail(
            "evaluation reached after environment drift"
        ),
    )

    receipts = []
    expected_entries = []
    validate_raises = 0
    for _attempt in range(2):
        receipts.append(runner.freeze_reference_bundle(bundle))
        expected_entries.append("freeze-reference-bundle")
        receipts.append(runner.check_binding())
        expected_entries.append("check-binding")
        receipts.append(runner.run_certificate(raw_result))
        expected_entries.append("run")

        before = set(controls.glob("*.json")) if controls.exists() else set()
        with pytest.raises(
            runner.ExecutionEnvironmentMismatch,
            match="synthetic environment drift",
        ):
            runner.validate_run(raw_result)
        validate_raises += 1
        after = set(controls.glob("*.json"))
        created = after - before
        assert len(created) == 1
        receipts.extend(created)
        expected_entries.append("validate")

    assert validate_raises == 2
    assert entries == ["environment"] * 8
    assert len(receipts) == len(set(receipts)) == 8
    assert set(controls.iterdir()) == set(receipts)
    expected_keys = {
        "format", "complete", "disposition", "actual_stage",
        "fit_entered", "evaluation_entered", "fit_published",
        "evaluation_published", "scientific_certificate_published",
        "resource_admission_relative_path", "resource_ledger_relative_path",
    }
    for path, entry in zip(receipts, expected_entries):
        value = json.loads(path.read_text(encoding="utf-8"))
        assert set(value) == expected_keys
        assert value == {
            "format": runner.CONTROL_RECEIPT_FORMAT,
            "complete": False,
            "disposition": "INCOMPLETE_TECHNICAL_PUBLICATION",
            "actual_stage": "EXECUTION_ENVIRONMENT",
            "fit_entered": False,
            "evaluation_entered": False,
            "fit_published": False,
            "evaluation_published": False,
            "scientific_certificate_published": False,
            "resource_admission_relative_path": None,
            "resource_ledger_relative_path": None,
        }
        assert path.name.startswith(f"{entry}-technical-control-")
        assert path.parent == controls
    assert not bundle.exists()
    assert not result.exists()
    assert not (controls / "resource-receipts").exists()


def test_control_publisher_rejects_unfrozen_or_late_environment_stage(
    tmp_path, runner, monkeypatch,
):
    controls = tmp_path / "controls-v2"
    monkeypatch.setattr(runner, "CONTROL_ROOT", controls)
    with pytest.raises(ValueError, match="entry/stage"):
        runner.publish_technical_stop("run", actual_stage="UNKNOWN_STAGE")
    with pytest.raises(ValueError, match="later activity"):
        runner.publish_technical_stop(
            "run", actual_stage="EXECUTION_ENVIRONMENT",
            fit_entered=True,
        )
    assert not controls.exists()


def test_memory_admission_launches_the_frozen_absolute_interpreter(
    tmp_path, runner, monkeypatch,
):
    monkeypatch.setattr(runner, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(runner, "CONTROL_ROOT", tmp_path / "controls")
    observed = []

    def complete(argv, *, cwd, capture_output, text, check):
        observed.append((argv, cwd, capture_output, text, check))
        Path(argv[-1]).write_text(
            json.dumps(
                {
                    "passed": True,
                    "physical_floor_pass": True,
                    "effective_floor_pass": True,
                    "available_physical_bytes": 8 * 1024**3,
                    "effective_available_bytes": 8 * 1024**3,
                }
            ),
            encoding="utf-8",
        )
        return type("Completed", (), {"returncode": 0})()

    monkeypatch.setattr(runner.subprocess, "run", complete)
    receipt = runner._admit_memory("assess-run")
    assert receipt["entry"] == "assess-run"
    assert len(observed) == 1
    argv, cwd, capture_output, text, check = observed[0]
    assert argv[:3] == [
        str(runner.FROZEN_PYTHON_EXECUTABLE),
        str(tmp_path / "scripts/hmasd_resource_preflight.py"),
        "admit-memory",
    ]
    assert cwd == tmp_path
    assert (capture_output, text, check) == (True, True, False)


def test_assess_run_cli_has_no_override_and_prints_its_unique_receipt(
    tmp_path, runner, monkeypatch, capsys,
):
    receipt = tmp_path / "assessment" / "assessment-receipt.json"
    monkeypatch.setattr(runner, "assess_run", lambda: receipt)
    assert runner.main(["assess-run"]) == 0
    assert capsys.readouterr().out.strip() == str(receipt)


def test_result_root_guard_rejects_every_equivalent_or_alternate_spelling(runner):
    exact = runner.FROZEN_RESULT_ROOT_ARG
    runner.require_frozen_result_argument(exact)
    variants = (
        runner.FROZEN_RESULT_ROOT,
        str(runner.FROZEN_RESULT_ROOT),
        f"./{exact}",
        exact.replace("/", "\\"),
        "temp/directions/ucope/exp/../exp/ucope-structural-competence-r01",
        f"{exact}/.",
        exact.upper(),
    )
    for variant in variants:
        with pytest.raises(
            runner.ExecutionEnvironmentMismatch, match="result root argument"
        ):
            runner.require_frozen_result_argument(variant)


def test_result_cli_requires_exact_raw_argv_and_disables_abbreviation(
    tmp_path, runner, monkeypatch, capsys,
):
    exact = runner.FROZEN_RESULT_ROOT_ARG
    parser = runner.build_parser()
    for command in ("run", "validate"):
        with pytest.raises(SystemExit):
            parser.parse_args([command, "--output", exact])
        with pytest.raises(SystemExit):
            parser.parse_args([command, "--output-r", exact])

    run_receipt = tmp_path / "run-receipt.json"
    monkeypatch.setattr(
        runner,
        "run_certificate",
        lambda value: run_receipt if value == exact else pytest.fail("argv drift"),
    )
    assert runner.main(["run", "--output-root", exact]) == 0
    assert capsys.readouterr().out.strip() == str(run_receipt)

    monkeypatch.setattr(
        runner,
        "validate_run",
        lambda value: {"validated": value == exact},
    )
    assert runner.main(["validate", "--output-root", exact]) == 0
    assert json.loads(capsys.readouterr().out)["validated"] is True

    for raw in (
        ["run", f"--output-root={exact}"],
        ["validate", f"--output-root={exact}"],
        ["run", "--output-root", str(runner.FROZEN_RESULT_ROOT)],
        ["validate", "--output-root", f"./{exact}"],
    ):
        with pytest.raises(
            runner.ExecutionEnvironmentMismatch, match="exact frozen argv"
        ):
            runner.main(raw)


def test_run_and_validate_guard_result_identity_before_memory_or_data(
    runner, monkeypatch,
):
    monkeypatch.setattr(
        runner,
        "_admit_memory",
        lambda _entry: pytest.fail("memory reached after result identity drift"),
    )
    for function in (runner.run_certificate, runner.validate_run):
        with pytest.raises(
            runner.ExecutionEnvironmentMismatch, match="result root argument"
        ):
            function(str(runner.FROZEN_RESULT_ROOT))
        source = inspect.getsource(function)
        assert source.index("require_frozen_result_argument") < source.index(
            "_admit_memory"
        )


def test_assess_run_is_unique_outcome_blind_in_memory_exact_refit(
    tmp_path, runner, structural, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch, entry="assess-run")
    assessments = runner.CONTROL_ROOT / "assessments"
    monkeypatch.setattr(runner, "ASSESSMENT_ROOT", assessments, raising=False)
    monkeypatch.setattr(runner, "require_frozen_execution_environment", lambda: None)
    admitted = []
    monkeypatch.setattr(
        runner,
        "_admit_memory",
        lambda entry: admitted.append(entry) or admission,
    )
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner))
    prefit_bytes = tuple(b"captured" for _ in range(90))
    capture = runner.BindingCapture(
        {
            "status": "MATCH",
            "bundle_format": runner.REFERENCE_BUNDLE_FORMAT,
            "member_count": 91,
            "prefit_member_count": 90,
            "postfit_member_count": 1,
            "raw_members_compared": 90,
            "gzip_members_opened": 80,
            "json_rows_parsed": 1_638_400,
            "canonical_rows_compared": 1_638_400,
            "decoder_rows_replayed": 1_638_400,
        },
        manifest_bytes=b"manifest",
        frozen_binding_bytes=b"binding",
        bundle_admission_bytes=b"bundle-admission",
        bundle_ledger_bytes=b"bundle-ledger",
        prefit_bytes=prefit_bytes,
    )
    monkeypatch.setattr(runner, "verify_data_binding", lambda: capture)
    monkeypatch.setattr(
        runner, "_assessment_final_prefit_sweep", lambda _capture: None,
        raising=False,
    )
    calls = []

    class InMemoryStructural:
        def __init__(self, identity):
            self.identity = identity

        def _assessment_fit_document(self, binding_receipt, tape_bytes):
            calls.append(self.identity)
            assert binding_receipt is capture
            assert tape_bytes is capture.tape_bytes
            return {
                "full_rank": False,
                "normal_matrix": [[Fraction(0)]],
                "coefficients": None,
            }

    modules = iter(
        [InMemoryStructural(1), InMemoryStructural(2),
         InMemoryStructural(3), InMemoryStructural(4)]
    )
    monkeypatch.setattr(runner, "_compile_structural", lambda _raw: next(modules))

    first = runner.assess_run()
    assert runner.validate_performance_assessment()["receipt_path"] == first
    second = runner.assess_run()
    with pytest.raises(runner.AssessmentQualificationError, match="exactly one"):
        runner.validate_performance_assessment()
    assert first != second
    assert first.parent != second.parent
    assert first.name == second.name == runner.ASSESSMENT_RECEIPT_FILENAME
    assert admitted == ["assess-run", "assess-run"]
    assert calls == [1, 2, 3, 4]

    receipt = json.loads(first.read_text(encoding="utf-8"))
    assert receipt == {
        "format": runner.ASSESSMENT_FORMAT,
        "entry": "assess-run",
        "complete": True,
        "performance_disposition": "PERFORMANCE_READY",
        "scope": "RESOURCE_AND_TECHNICAL_ONLY",
        "exact_refit_equal": True,
        "work": {
            "prefit_members_compared": 90,
            "canonical_rows_replayed": 1_638_400,
            "exact_in_memory_solve_passes": 2,
            "independent_prefit_modules": 2,
            "exact_row_decodes": 9_830_400,
            "exact_root_normal_accumulations": 3_276_800,
            "postfit_members_opened": 0,
            "serialized_solve_documents": 0,
            "scientific_outputs_created": 0,
        },
        "resource_admission_relative_path": admission[
            "preflight_receipt_relative_path"
        ],
        "resource_ledger_relative_path": receipt[
            "resource_ledger_relative_path"
        ],
    }
    assert list(first.parent.iterdir()) == [first]
    rendered = first.read_text(encoding="utf-8").lower()
    for forbidden in ("normal_matrix", "rank", "coefficient", "policy", "competence"):
        assert forbidden not in rendered
    assert not list(tmp_path.rglob(runner.FIT_FILENAME))
    assert not list(tmp_path.rglob(runner.FIT_REFERENCE_FILENAME))

    assess_closure = inspect.getsource(runner.assess_run) + inspect.getsource(
        runner._compare_independent_in_memory_fits
    )
    structural_assess_closure = "\n".join(
        inspect.getsource(function)
        for function in (
            structural._assessment_fit_document,
            structural._assessment_fit_seed,
            structural._assessment_empty_root_fit,
        )
    )
    for forbidden in (
        "canonical_bytes", "_create_once", "fit_structural_artifact",
        "FIT_FILENAME", "FIT_REFERENCE_FILENAME", "CERTIFICATE_FILENAME",
        "_verify_postfit_binding", "evaluate_sealed_fit",
    ):
        assert forbidden not in assess_closure
        assert forbidden not in structural_assess_closure
    assert "first_module._fit_document" not in assess_closure
    assert "second_module._fit_document" not in assess_closure


def test_assess_run_fails_closed_before_data_for_environment_or_memory(
    tmp_path, runner, monkeypatch,
):
    monkeypatch.setattr(runner, "ASSESSMENT_ROOT", tmp_path / "assessments")
    data_entered = []
    monkeypatch.setattr(
        runner, "verify_data_binding", lambda: data_entered.append(True)
    )
    monkeypatch.setattr(
        runner,
        "require_frozen_execution_environment",
        lambda: (_ for _ in ()).throw(
            runner.ExecutionEnvironmentMismatch("wrong interpreter")
        ),
    )
    monkeypatch.setattr(
        runner, "_admit_memory",
        lambda _entry: pytest.fail("memory admission reached after environment drift"),
    )
    environment_path = runner.assess_run()
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    assert environment["performance_disposition"] == "REPAIR_REQUIRED"
    assert environment["disposition"] == "INCOMPLETE_TECHNICAL_ASSESSMENT"
    assert environment["actual_stage"] == "EXECUTION_ENVIRONMENT"
    assert environment["resource_admission_relative_path"] is None
    assert environment["resource_ledger_relative_path"] is None
    assert data_entered == []

    monkeypatch.setattr(runner, "require_frozen_execution_environment", lambda: None)
    monkeypatch.setattr(
        runner,
        "_admit_memory",
        lambda _entry: (_ for _ in ()).throw(
            runner.ResourceAdmissionRefusal("below 4 GiB")
        ),
    )
    memory_path = runner.assess_run()
    memory = json.loads(memory_path.read_text(encoding="utf-8"))
    assert memory_path.parent != environment_path.parent
    assert memory["performance_disposition"] == "REPAIR_REQUIRED"
    assert memory["disposition"] == "RESOURCE_REFUSAL_NO_SCIENCE_STATE"
    assert memory["actual_stage"] == "MEMORY_ADMISSION"
    assert memory["resource_admission_relative_path"] is None
    assert memory["resource_ledger_relative_path"] is None
    assert data_entered == []

    ready, _admission, _ledger = _materialize_valid_assessment(
        tmp_path, runner, monkeypatch
    )
    assert runner.validate_performance_assessment()["receipt_path"] == ready


def test_assess_run_resource_overrun_precedes_technical_failure(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch, entry="assess-run")
    monkeypatch.setattr(runner, "ASSESSMENT_ROOT", runner.CONTROL_ROOT / "assessments")
    monkeypatch.setattr(runner, "require_frozen_execution_environment", lambda: None)
    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: admission)
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner, passed=False))
    monkeypatch.setattr(
        runner,
        "verify_data_binding",
        lambda: (_ for _ in ()).throw(runner.DataBindingMismatch("synthetic drift")),
    )

    path = runner.assess_run()
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["performance_disposition"] == "REPAIR_REQUIRED"
    assert receipt["disposition"] == "INCOMPLETE_RESOURCE_CEILING"
    assert receipt["actual_stage"] == "PREFIT_BINDING"
    assert receipt["resource_admission_relative_path"] == admission[
        "preflight_receipt_relative_path"
    ]
    assert receipt["resource_ledger_relative_path"].endswith(".json")
    ledger = json.loads(
        (runner.PROJECT_ROOT / receipt["resource_ledger_relative_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert ledger["passed"] is False
    assert not list(tmp_path.rglob(runner.FIT_FILENAME))
    ready, _admission, _ledger = _materialize_valid_assessment(
        tmp_path, runner, monkeypatch
    )
    assert runner.validate_performance_assessment()["receipt_path"] == ready


def test_assess_run_refit_mismatch_is_technical_and_never_publishes_documents(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch, entry="assess-run")
    monkeypatch.setattr(runner, "ASSESSMENT_ROOT", runner.CONTROL_ROOT / "assessments")
    monkeypatch.setattr(runner, "require_frozen_execution_environment", lambda: None)
    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: admission)
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner))
    prefit_bytes = tuple(b"captured" for _ in range(90))
    capture = runner.BindingCapture(
        {
            "prefit_member_count": 90,
            "raw_members_compared": 90,
            "decoder_rows_replayed": 1_638_400,
            "canonical_rows_compared": 1_638_400,
        },
        manifest_bytes=b"manifest",
        frozen_binding_bytes=b"binding",
        bundle_admission_bytes=b"bundle-admission",
        bundle_ledger_bytes=b"bundle-ledger",
        prefit_bytes=prefit_bytes,
    )
    monkeypatch.setattr(runner, "verify_data_binding", lambda: capture)

    class DifferentDocument:
        def __init__(self, value):
            self.value = value

        def _assessment_fit_document(self, _binding, _tapes):
            return {"technical_fixture": self.value}

    modules = iter((DifferentDocument(1), DifferentDocument(2)))
    monkeypatch.setattr(runner, "_compile_structural", lambda _raw: next(modules))

    path = runner.assess_run()
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["performance_disposition"] == "REPAIR_REQUIRED"
    assert receipt["disposition"] == "INCOMPLETE_TECHNICAL_ASSESSMENT"
    assert receipt["actual_stage"] == "EXACT_REFIT"
    assert receipt["exact_refit_equal"] is False
    assert receipt["work"]["exact_in_memory_solve_passes"] == 2
    assert receipt["resource_ledger_relative_path"].endswith(".json")
    assert not list(tmp_path.rglob(runner.FIT_FILENAME))
    assert not list(tmp_path.rglob(runner.FIT_REFERENCE_FILENAME))
    ready, _admission, _ledger = _materialize_valid_assessment(
        tmp_path, runner, monkeypatch
    )
    assert runner.validate_performance_assessment()["receipt_path"] == ready


def test_rank_deficiency_does_not_curtail_either_fold_sweep(
    structural, monkeypatch,
):
    seed = structural.SEED_SLOTS[0]
    rows = (
        {
            "seed_slot": seed,
            "index": 0,
            "context_id": CONTEXT_IDS[0],
            "root_action": "PROBE",
            "period": 1,
            "link": "SEVERED",
            "tail_return": 0,
        },
        {
            "seed_slot": seed,
            "index": 10,
            "context_id": CONTEXT_IDS[0],
            "root_action": "PROBE",
            "period": 1,
            "link": "SEVERED",
            "tail_return": 0,
        },
    )
    sweeps = []

    def fixed_rows(observed_seed, _tape_bytes):
        assert observed_seed == seed
        sweeps.append(observed_seed)
        yield from rows

    monkeypatch.setattr(structural, "_iter_seed_rows", fixed_rows)
    result = structural._fit_seed(seed, tuple(b"fixture" for _ in range(80)))
    assert sweeps == [seed, seed, seed]
    assert len(result["policies"]) == 2
    for policy in result["policies"]:
        assert policy["tail"]["rank_status"] == "RANK_DEFICIENT_STOP"
        assert policy["root"]["rank_status"] == "RANK_DEFICIENT_STOP"
        assert policy["root_support"]["rows"] == 1


def test_assessment_padding_equalizes_full_rank_and_rank_deficient_root_work(
    structural, monkeypatch,
):
    seed = structural.SEED_SLOTS[0]
    rows = (
        {
            "seed_slot": seed, "index": 0, "context_id": CONTEXT_IDS[0],
            "root_action": "PROBE", "period": 1, "link": "SEVERED",
            "reliability": Fraction(1, 2), "total_cost": 0, "tail_return": 0,
            "primitive_ledger": {
                "probe_service": 0, "probe_time": 0, "probe_energy": 0,
            },
        },
        {
            "seed_slot": seed, "index": 1, "context_id": CONTEXT_IDS[0],
            "root_action": "IMMEDIATE", "period": 1, "link": "SEVERED",
            "reliability": Fraction(1, 2), "total_cost": 0, "tail_return": 0,
        },
        {
            "seed_slot": seed, "index": 10, "context_id": CONTEXT_IDS[0],
            "root_action": "PROBE", "period": 1, "link": "SEVERED",
            "reliability": Fraction(1, 2), "total_cost": 0, "tail_return": 0,
            "primitive_ledger": {
                "probe_service": 0, "probe_time": 0, "probe_energy": 0,
            },
        },
        {
            "seed_slot": seed, "index": 11, "context_id": CONTEXT_IDS[0],
            "root_action": "IMMEDIATE", "period": 1, "link": "SEVERED",
            "reliability": Fraction(1, 2), "total_cost": 0, "tail_return": 0,
        },
    )
    original_root_basis = structural.root_basis
    original_probe_target = structural.probe_root_target
    original_accumulate = structural._accumulate_normal
    counts_by_mode = {}
    results = {}

    for mode in ("full", "deficient"):
        counts = {
            "iter_calls": 0, "rows_decoded": 0, "root_basis": 0,
            "probe_target": 0, "normal_accumulations": 0, "solves": 0,
        }

        def fixed_rows(observed_seed, _tape_bytes):
            assert observed_seed == seed
            counts["iter_calls"] += 1
            for row in rows:
                counts["rows_decoded"] += 1
                yield row

        def counted_root_basis(*args, **kwargs):
            counts["root_basis"] += 1
            return original_root_basis(*args, **kwargs)

        def counted_probe_target(*args, **kwargs):
            counts["probe_target"] += 1
            return original_probe_target(*args, **kwargs)

        def counted_accumulate(*args, **kwargs):
            counts["normal_accumulations"] += 1
            return original_accumulate(*args, **kwargs)

        def fixed_solve(matrix, rhs, *, expected_rank, row_count):
            counts["solves"] += 1
            deficient_tail = expected_rank == 5 and mode == "deficient"
            coefficients = (
                None if deficient_tail
                else tuple(Fraction(0) for _ in range(expected_rank))
            )
            return {
                "solver": structural.EXACT_SOLVER_LAW,
                "expected_rank": expected_rank,
                "rank": 0 if deficient_tail else expected_rank,
                "rank_status": (
                    "RANK_DEFICIENT_STOP" if deficient_tail else "FULL_RANK"
                ),
                "row_count": row_count,
                "normal_matrix": tuple(tuple(value for value in row) for row in matrix),
                "normal_rhs": tuple(rhs),
                "coefficients": coefficients,
            }

        monkeypatch.setattr(structural, "_iter_seed_rows", fixed_rows)
        monkeypatch.setattr(structural, "root_basis", counted_root_basis)
        monkeypatch.setattr(structural, "probe_root_target", counted_probe_target)
        monkeypatch.setattr(structural, "_accumulate_normal", counted_accumulate)
        monkeypatch.setattr(structural, "_fit_from_normal", fixed_solve)
        results[mode] = structural._assessment_fit_seed(
            seed, tuple(b"fixture" for _ in range(80))
        )
        counts_by_mode[mode] = counts

    assert counts_by_mode["full"] == counts_by_mode["deficient"] == {
        "iter_calls": 3,
        "rows_decoded": 12,
        "root_basis": 4,
        "probe_target": 2,
        "normal_accumulations": 6,
        "solves": 4,
    }
    assert all(
        policy["root"]["rank_status"] == "FULL_RANK"
        for policy in results["full"]["policies"]
    )
    assert all(
        policy["root"]["rank_status"] == "RANK_DEFICIENT_STOP"
        for policy in results["deficient"]["policies"]
    )
    assert structural.ASSESSMENT_PADDING_LAW == (
        "TECHNICAL_ONLY_ZERO_TAIL_VECTOR_FIXED_ROOT_WORK_V1"
    )


def test_assessment_full_rank_document_preserves_scientific_fit_semantics(
    structural, monkeypatch,
):
    seed = structural.SEED_SLOTS[0]
    base_rows = (
        {
            "seed_slot": seed, "index": 0, "context_id": CONTEXT_IDS[0],
            "root_action": "PROBE", "period": 1, "link": "SEVERED",
            "reliability": Fraction(1, 2), "total_cost": 0, "tail_return": 0,
            "primitive_ledger": {
                "probe_service": 0, "probe_time": 0, "probe_energy": 0,
            },
        },
        {
            "seed_slot": seed, "index": 10, "context_id": CONTEXT_IDS[0],
            "root_action": "PROBE", "period": 1, "link": "SEVERED",
            "reliability": Fraction(1, 2), "total_cost": 0, "tail_return": 0,
            "primitive_ledger": {
                "probe_service": 0, "probe_time": 0, "probe_energy": 0,
            },
        },
    )
    rows = base_rows + base_rows

    def fixed_rows(observed_seed, _tape_bytes):
        assert observed_seed == seed
        yield from rows

    def full_rank_solve(matrix, rhs, *, expected_rank, row_count):
        return {
            "solver": structural.EXACT_SOLVER_LAW,
            "expected_rank": expected_rank,
            "rank": expected_rank,
            "rank_status": "FULL_RANK",
            "row_count": row_count,
            "normal_matrix": tuple(tuple(value for value in row) for row in matrix),
            "normal_rhs": tuple(rhs),
            "coefficients": tuple(Fraction(0) for _ in range(expected_rank)),
        }

    monkeypatch.setattr(structural, "_iter_seed_rows", fixed_rows)
    monkeypatch.setattr(structural, "_fit_from_normal", full_rank_solve)
    tapes = tuple(b"fixture" for _ in range(80))
    assert structural._assessment_fit_seed(seed, tapes) == structural._fit_seed(
        seed, tapes
    )


def test_assessment_structural_call_graph_is_prefit_only_and_nonserializing():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    reachable = set()
    pending = ["_assessment_fit_document"]
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        for call in (
            node for node in ast.walk(functions[name]) if isinstance(node, ast.Call)
        ):
            if isinstance(call.func, ast.Name) and call.func.id in functions:
                pending.append(call.func.id)
    assert {
        "_assessment_fit_document", "_assessment_fit_seed",
        "_assessment_empty_root_fit", "_iter_seed_rows", "_fit_from_normal",
    } <= reachable
    assert reachable.isdisjoint(
        {
            "canonical_bytes", "_create_once", "fit_structural_artifact",
            "configure_postseal_runtime", "_postseal_contexts", "_assess_policy",
            "_certificate_document", "evaluate_sealed_fit", "validate_certificate",
        }
    )


def test_strict_assessment_validator_accepts_one_canonical_ready_receipt(
    tmp_path, runner, monkeypatch,
):
    receipt_path, admission, ledger_path = _materialize_valid_assessment(
        tmp_path, runner, monkeypatch
    )
    before = {
        path: path.read_bytes()
        for path in (
            receipt_path,
            runner.PROJECT_ROOT / admission["preflight_receipt_relative_path"],
            ledger_path,
        )
    }
    observed = runner.validate_performance_assessment()
    assert observed["receipt_path"] == receipt_path
    assert observed["receipt"]["entry"] == "assess-run"
    assert observed["receipt"]["work"] == _fixed_assessment_work()
    assert observed["admission"]["available_physical_bytes"] == 8 * 1024**3
    assert observed["ledger"]["passed"] is True
    assert ledger_path.is_file()
    assert admission["preflight_receipt_relative_path"].endswith(".json")
    assert {path: path.read_bytes() for path in before} == before


def test_assessment_validator_call_graph_is_read_only_and_data_blind():
    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"), filename=str(RUNNER_PATH))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    reachable = set()
    pending = ["validate_performance_assessment"]
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        for call in (
            node for node in ast.walk(functions[name]) if isinstance(node, ast.Call)
        ):
            if isinstance(call.func, ast.Name) and call.func.id in functions:
                pending.append(call.func.id)
    assert reachable.isdisjoint(
        {
            "atomic_create_bytes", "atomic_create_json", "_publish_assessment_receipt",
            "capture_prefit_binding", "verify_data_binding", "_compile_structural",
            "_bound_structural", "_verify_postfit_binding", "_run_certificate_admitted",
            "fit_structural_artifact", "evaluate_sealed_fit",
        }
    )


def test_strict_assessment_validator_rejects_absent_and_orphaned_receipts(
    tmp_path, runner, monkeypatch,
):
    _sandbox_admission(tmp_path, runner, monkeypatch, entry="assess-run")
    with pytest.raises(runner.AssessmentQualificationError, match="absent"):
        runner.validate_performance_assessment()

    (runner.ASSESSMENT_ROOT / "orphan").mkdir(parents=True)
    with pytest.raises(runner.AssessmentQualificationError, match="inventory"):
        runner.validate_performance_assessment()


def test_strict_assessment_validator_rejects_noncanonical_extra_and_bad_work(
    tmp_path, runner, monkeypatch,
):
    receipt_path, _admission, _ledger = _materialize_valid_assessment(
        tmp_path, runner, monkeypatch
    )
    value = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt_path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(runner.AssessmentQualificationError, match="canonical"):
        runner.validate_performance_assessment()

    value["extra"] = False
    receipt_path.write_bytes(runner._plain_canonical_bytes(value))
    with pytest.raises(runner.AssessmentQualificationError, match="field inventory"):
        runner.validate_performance_assessment()

    value.pop("extra")
    value["work"]["exact_row_decodes"] -= 1
    receipt_path.write_bytes(runner._plain_canonical_bytes(value))
    with pytest.raises(runner.AssessmentQualificationError, match="work"):
        runner.validate_performance_assessment()


def test_strict_assessment_validator_rejects_multiple_and_failing_receipts(
    tmp_path, runner, monkeypatch,
):
    receipt_path, _admission, _ledger = _materialize_valid_assessment(
        tmp_path, runner, monkeypatch
    )
    duplicate = (
        runner.ASSESSMENT_ROOT / f"assess-run-{'3' * 32}"
        / runner.ASSESSMENT_RECEIPT_FILENAME
    )
    duplicate.parent.mkdir(parents=True)
    duplicate.write_bytes(receipt_path.read_bytes())
    with pytest.raises(runner.AssessmentQualificationError, match="exactly one"):
        runner.validate_performance_assessment()

    duplicate.unlink()
    duplicate.parent.rmdir()
    failing = {
        "format": runner.ASSESSMENT_FORMAT,
        "entry": "assess-run",
        "complete": False,
        "performance_disposition": "REPAIR_REQUIRED",
        "disposition": "INCOMPLETE_TECHNICAL_ASSESSMENT",
        "actual_stage": "EXECUTION_ENVIRONMENT",
        "scope": "RESOURCE_AND_TECHNICAL_ONLY",
        "exact_refit_equal": None,
        "work": {name: 0 for name in _fixed_assessment_work()},
        "resource_admission_relative_path": None,
        "resource_ledger_relative_path": None,
    }
    receipt_path.write_bytes(runner._plain_canonical_bytes(failing))
    with pytest.raises(runner.AssessmentQualificationError, match="PERFORMANCE_READY"):
        runner.validate_performance_assessment()


def test_strict_assessment_validator_allows_valid_failure_then_one_ready(
    tmp_path, runner, monkeypatch,
):
    ready_path, _admission, _ledger = _materialize_valid_assessment(
        tmp_path, runner, monkeypatch
    )
    failed_path = (
        runner.ASSESSMENT_ROOT / f"assess-run-{'3' * 32}"
        / runner.ASSESSMENT_RECEIPT_FILENAME
    )
    runner.atomic_create_json(
        failed_path,
        {
            "format": runner.ASSESSMENT_FORMAT,
            "entry": "assess-run",
            "complete": False,
            "performance_disposition": "REPAIR_REQUIRED",
            "disposition": "INCOMPLETE_TECHNICAL_ASSESSMENT",
            "actual_stage": "EXECUTION_ENVIRONMENT",
            "scope": "RESOURCE_AND_TECHNICAL_ONLY",
            "exact_refit_equal": None,
            "work": {name: 0 for name in _fixed_assessment_work()},
            "resource_admission_relative_path": None,
            "resource_ledger_relative_path": None,
        },
    )
    observed = runner.validate_performance_assessment()
    assert observed["receipt_path"] == ready_path
    assert observed["receipt"]["performance_disposition"] == "PERFORMANCE_READY"


def test_strict_assessment_validator_rejects_orphaned_or_failing_resources(
    tmp_path, runner, monkeypatch,
):
    _receipt, _admission, ledger_path = _materialize_valid_assessment(
        tmp_path, runner, monkeypatch
    )
    ledger_path.unlink()
    with pytest.raises(runner.AssessmentQualificationError, match="ledger"):
        runner.validate_performance_assessment()

    _receipt, _admission, ledger_path = _materialize_valid_assessment(
        tmp_path / "second", runner, monkeypatch
    )
    ledger_path.write_bytes(
        runner._plain_canonical_bytes(
            _resource_ledger(runner, entry="assess-run", passed=False)
        )
    )
    with pytest.raises(runner.AssessmentQualificationError, match="resource"):
        runner.validate_performance_assessment()

    receipt_path, _admission, _ledger = _materialize_valid_assessment(
        tmp_path / "third", runner, monkeypatch
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    admission_path = (
        runner.PROJECT_ROOT / receipt["resource_admission_relative_path"]
    )
    failed_admission = json.loads(admission_path.read_text(encoding="utf-8"))
    failed_admission["available_physical_bytes"] = 4 * 1024**3 - 1
    failed_admission["effective_available_bytes"] = 4 * 1024**3 - 1
    failed_admission["physical_floor_pass"] = False
    failed_admission["effective_floor_pass"] = False
    failed_admission["passed"] = False
    failed_admission["failure_reasons"] = [
        "available physical memory is below 4 GiB"
    ]
    admission_path.write_text(
        json.dumps(
            failed_admission, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(runner.AssessmentQualificationError, match="admission"):
        runner.validate_performance_assessment()


def test_result_blind_reference_bundle_is_ordered_direct_bytes_and_create_once(
    tmp_path, runner, structural, monkeypatch,
):
    class PassingMonitor:
        def __init__(self, entry, **_kwargs):
            self.entry = entry
            self._thread = type("StoppedThread", (), {"is_alive": lambda self: False})()

        def start(self):
            return self

        def finish(self):
            return {
                "format": "UCOPE_STRUCTURAL_RESOURCE_LEDGER_V1",
                "entry": self.entry,
                "ceilings": dict(runner.RESOURCE_CEILINGS),
                "measurement_scope": runner.RESOURCE_MEASUREMENT_SCOPE,
                "sample_interval_seconds": runner.RESOURCE_SAMPLE_SECONDS,
                "publication_headroom": dict(runner.PUBLICATION_HEADROOM),
                "observed": {
                    "workers": 1,
                    "wall_seconds": 0,
                    "cpu_seconds": 0,
                    "peak_process_threads": 1,
                    "peak_rss_bytes": 1,
                    "scientific_child_processes": 0,
                    "scratch_high_water_bytes": 0,
                    "durable_high_water_bytes": 0,
                    "read_bytes": 0,
                    "write_bytes": 0,
                    "aggregate_io_bytes": 0,
                },
                "passed": True,
            }

    admissions = []
    monkeypatch.setattr(
        runner,
        "_admit_memory",
        lambda entry: admissions.append(entry) or {
            "entry": entry,
            "passed": True,
            "physical_floor_pass": True,
            "effective_floor_pass": True,
            "available_physical_bytes": 8 * 1024**3,
            "effective_available_bytes": 8 * 1024**3,
        },
        raising=False,
    )
    monkeypatch.setattr(runner, "_persist_entry_admission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "ResourceMonitor", PassingMonitor)
    monkeypatch.setattr(
        runner,
        "_validate_prefit_row_structure",
        lambda _captured: (80, 1_638_400, 1_638_400),
    )
    bundle = tmp_path / "reference-bundle"
    manifest_path = runner.freeze_reference_bundle(bundle)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_prefit = structural.expected_prefit_reference_bundle_members()
    expected_postfit = structural.expected_postfit_reference_bundle_members()
    assert manifest["format"] == runner.REFERENCE_BUNDLE_FORMAT
    assert manifest["format"] == "UCOPE_STRUCTURAL_REFERENCE_BUNDLE_V2"
    assert manifest["complete"] is True
    assert manifest["prefit_members"] == [
        {
            "ordinal": index,
            "source_relative_path": source,
            "bundle_relative_path": f"members/{index:03d}.bin",
            "length": (PROJECT_ROOT / source).stat().st_size,
            "schema_role": role,
            "phase_role": "PREFIT",
        }
        for index, (source, role) in enumerate(expected_prefit)
    ]
    assert manifest["postfit_members"] == [
        {
            "ordinal": index,
            "source_relative_path": source,
            "bundle_relative_path": f"members/{index:03d}.bin",
            "length": (PROJECT_ROOT / source).stat().st_size,
            "schema_role": role,
            "phase_role": "POSTFIT",
        }
        for index, (source, role) in enumerate(
            expected_postfit, start=len(expected_prefit)
        )
    ]
    expected = expected_prefit + expected_postfit
    records = manifest["prefit_members"] + manifest["postfit_members"]
    assert len(expected_prefit) == 90
    assert len(expected_postfit) == 1
    assert len(expected) == 91
    assert sum(
        record["length"] for record in records if record["schema_role"] == "retained_gzip_tape"
    ) == 29_793_881
    for record in records:
        assert (PROJECT_ROOT / record["source_relative_path"]).read_bytes() == (
            bundle / record["bundle_relative_path"]
        ).read_bytes()
    receipt = runner.verify_reference_binding(bundle, replay_rows=False)
    assert receipt == {
        "status": "MATCH",
            "bundle_format": runner.REFERENCE_BUNDLE_FORMAT,
        "member_count": 91,
        "prefit_member_count": 90,
        "postfit_member_count": 1,
        "raw_members_compared": 90,
        "gzip_members_opened": 0,
        "json_rows_parsed": 0,
        "canonical_rows_compared": 0,
        "decoder_rows_replayed": 0,
    }
    with pytest.raises(FileExistsError):
        runner.freeze_reference_bundle(bundle)
    assert admissions == ["freeze-reference-bundle", "freeze-reference-bundle"]


def test_common_ancestry_block_parity_is_context_invariant_and_stratum_complete(structural):
    seed = "cpa-r01-fresh-slot-00"
    assert [structural.fold_id(seed, index) for index in range(30)] == [0] * 10 + [1] * 10 + [0] * 10
    for index in range(20_480):
        expected = (index // 10) % 2
        assert structural.fold_id(seed, index) == expected
        assert structural.fold_group_key(seed, index) == (seed, index)
    for fold in (0, 1):
        assert {index % 10 for index in range(20_480) if structural.fold_id(seed, index) == fold} == set(range(10))
        counts = {
            stratum: sum(
                structural.fold_id(seed, index) == fold and index % 10 == stratum
                for index in range(20_480)
            )
            for stratum in range(10)
        }
        assert set(counts.values()) == {1024}
    assert structural.FOLD_DEPENDENCE_CLAIM == "COMPLEMENTARY_GROUP_DISJOINT_NO_CROSS_FOLD_INDEPENDENCE_CLAIM"


def test_exact_bases_solver_and_complementary_probe_target_are_frozen(structural):
    assert structural.TAIL_BASIS == ("1", "b", "k/9", "b*k/9", "(k/9)^2")
    assert structural.ROOT_BASIS == (
        "1", "(1-a)*k/9", "(1-a)*(k/9)^2", "a", "a*C", "a*L", "a*L*p",
    )
    coefficients = tuple(Fraction(value) for value in (3, -2, 5, 7, -11))
    rows = []
    targets = []
    for belief in (Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)):
        for period in (1, 3, 5, 7, 9):
            basis = structural.tail_basis(belief, period)
            rows.append(basis)
            targets.append(sum(c * x for c, x in zip(coefficients, basis)))
    fit = structural.exact_least_squares(rows, targets, expected_rank=5)
    assert fit["rank"] == 5
    assert fit["coefficients"] == coefficients
    assert fit["solver"] == structural.EXACT_SOLVER_LAW

    complement_tail = (Fraction(1), Fraction(0), Fraction(9, 10), Fraction(0), Fraction(-1, 10))
    expected = Fraction(-1, 20) + max(
        structural.score(complement_tail, structural.tail_basis(Fraction(1, 2), period))
        for period in structural.K_TRAIN
    )
    assert structural.probe_root_target(Fraction(-1, 20), Fraction(1, 2), complement_tail) == expected
    parsed = json.loads('{"value":0.1,"negative_zero":-0.0,"integer_zero":-0}')
    assert structural._fraction(parsed["value"]) == Fraction.from_float(0.1)
    assert structural._fraction(parsed["value"]) != Fraction(1, 10)
    assert structural._fraction(parsed["negative_zero"]) == 0
    assert structural._fraction(parsed["integer_zero"]) == 0
    assert structural._fraction(5e-324) == Fraction.from_float(5e-324)
    with pytest.raises(ValueError, match="binary64"):
        structural._fraction(Decimal("0.1"))
    with pytest.raises(ValueError, match="nonfinite"):
        structural._fraction(float("inf"))
    with pytest.raises(structural.StructuralCertificateError, match="nonfinite"):
        json.loads("NaN", parse_constant=structural._reject_json_constant)
    assert structural.EXACT_ARITHMETIC_LAW == (
        "JSON_BINARY64_RN_TIES_EVEN_TO_REDUCED_DYADIC_RATIONAL_V1"
    )


def test_known_exact_structural_policy_passes_postseal_competence(structural):
    tail = (
        Fraction(31, 100), Fraction(3, 5), Fraction(27, 20),
        Fraction(-27, 25), Fraction(-891, 1000),
    )
    root = (
        Fraction(61, 100), Fraction(81, 100), Fraction(-891, 1000),
        Fraction(43, 200), Fraction(-1),
        Fraction(-388036941, 3200000000), Fraction(38665803, 160000000),
    )
    policy = {
        "tail": _fit_record(structural, tail, 40_960),
        "root": _fit_record(structural, root, 81_920),
    }
    assessed = structural._assess_policy(policy)
    assert assessed["pass"] is True
    assert assessed["reason"] == "PASS"
    assert assessed["maximum_regret"] == 0
    assert assessed["minimum_forced_probe_tail_agreement"] == 1
    assert assessed["root_unique"] is assessed["tail_unique"] is True
    assert assessed["minimum_root_margin"] > 0
    assert assessed["minimum_tail_margin"] > 0


def test_rank_and_tie_are_valid_scientific_stops_not_technical_errors(structural):
    receipt = {"status": "MATCH"}
    rank_fit = _fit_document(
        structural,
        _rank_stop_record(structural, 7, 81_920),
        _rank_stop_record(structural, 5, 40_960),
        receipt,
    )
    rank_certificate = structural._certificate_document(rank_fit, receipt, receipt)
    assert rank_certificate["disposition"] == "STOP_FOLD_RANK"
    assert rank_certificate["admit"] is False
    assert rank_certificate["gate_counts"] == {
        "fold_policies": 20, "rank_pass": 0, "unique": 0, "competent": 0,
    }

    competent_root = (
        Fraction(61, 100), Fraction(81, 100), Fraction(-891, 1000),
        Fraction(43, 200), Fraction(-1),
        Fraction(-388036941, 3200000000), Fraction(38665803, 160000000),
    )
    tied_tail = (Fraction(0),) * 5
    tie_fit = _fit_document(
        structural,
        _fit_record(structural, competent_root, 81_920),
        _fit_record(structural, tied_tail, 40_960),
        receipt,
    )
    tie_certificate = structural._certificate_document(tie_fit, receipt, receipt)
    assert tie_certificate["disposition"] == "STOP_NONUNIQUE_POLICY"
    assert tie_certificate["admit"] is False
    assert {fold["reason"] for seed in tie_certificate["seeds"] for fold in seed["folds"]} == {
        "NONUNIQUE_POLICY_STOP"
    }


def test_structural_pass_requires_root_decision_and_never_auto_admits(structural):
    receipt = {"status": "MATCH"}
    tail = (
        Fraction(31, 100), Fraction(3, 5), Fraction(27, 20),
        Fraction(-27, 25), Fraction(-891, 1000),
    )
    root = (
        Fraction(61, 100), Fraction(81, 100), Fraction(-891, 1000),
        Fraction(43, 200), Fraction(-1),
        Fraction(-388036941, 3200000000), Fraction(38665803, 160000000),
    )
    fit = _fit_document(
        structural,
        _fit_record(structural, root, 81_920),
        _fit_record(structural, tail, 40_960),
        receipt,
    )
    certificate = structural._certificate_document(fit, receipt, receipt)
    assert certificate["disposition"] == "STRUCTURAL_PREREQUISITE_PASS"
    assert certificate["prerequisite_pass"] is True
    assert certificate["admit"] is False
    assert certificate["next_action"] == "ROOT_NEW_OBJECT_DECISION_REQUIRED"


def test_fit_activity_and_bundle_only_source_are_explicit(structural):
    assert structural.FIT_ACTIVITY == {
        "model_constructions": 0,
        "optimizer_constructions": 0,
        "optimizer_updates": 0,
        "checkpoint_reads": 0,
        "checkpoint_writes": 0,
        "heldout_outcome_rows_read": 0,
        "policy_evaluations_before_seal": 0,
    }
    source = inspect.getsource(structural._iter_seed_rows)
    assert "RETAINED_ROOT" not in source
    assert "materialized" not in source
    assert "reference_tape_member" in source
    assert structural.reference_tape_member("cpa-r01-fresh-slot-03", 5) == (
        structural.FIXED_BUNDLE_ROOT / "members/029.bin"
    )
    fit_signature = inspect.signature(structural.fit_structural_artifact)
    assert set(fit_signature.parameters) == {"binding_receipt", "tape_bytes", "output_path"}
    fit_source = inspect.getsource(structural.fit_structural_artifact).lower()
    assert "postfit" not in fit_source
    assert "oracle" not in fit_source


def test_fit_validator_rejects_support_and_row_count_drift(structural):
    receipt = {"status": "MATCH"}
    tail = _fit_record(structural, (Fraction(1),) * 5, 40_960)
    root = _fit_record(structural, (Fraction(1),) * 7, 81_920)
    fit = _fit_document(structural, root, tail, receipt)
    structural._validate_fit_structure(fit, receipt)

    row_drift = deepcopy(fit)
    row_drift["seeds"][0]["policies"][0]["root"]["row_count"] -= 1
    with pytest.raises(structural.StructuralCertificateError, match="row count"):
        structural._validate_fit_structure(row_drift, receipt)

    context_drift = deepcopy(fit)
    contexts = context_drift["seeds"][0]["policies"][0]["tail_support"]["contexts"]
    contexts["WRONG-CONTEXT"] = contexts.pop(CONTEXT_IDS[0])
    with pytest.raises(structural.StructuralCertificateError, match="support"):
        structural._validate_fit_structure(context_drift, receipt)


@pytest.mark.parametrize("bad", ["2/2", "1/-2"])
def test_noncanonical_rational_text_is_rejected_not_reinterpreted(tmp_path, structural, bad):
    path = tmp_path / "fit.json"
    path.write_bytes(structural.canonical_bytes({
        "format": structural.FIT_FORMAT,
        "complete": True,
        "sealed": True,
        "bad": bad,
    }))
    with pytest.raises(structural.StructuralCertificateError, match="canonical"):
        structural._load_sealed(path)


def test_nonfinite_sealed_json_is_rejected(tmp_path, structural):
    path = tmp_path / "fit.json"
    path.write_bytes(
        b'{"bad":NaN,"complete":true,"format":"UCOPE_STRUCTURAL_EXACT_FIT_V1","sealed":true}'
    )
    with pytest.raises(structural.StructuralCertificateError, match="canonical"):
        structural._load_sealed(path)


@pytest.mark.parametrize("bad", [1, 0.5, Decimal("0.5"), "1/2"])
def test_exact_system_rejects_nonfraction_numeric_storage(structural, bad):
    receipt = {"status": "MATCH"}
    fit = _fit_document(
        structural,
        _fit_record(structural, (Fraction(1),) * 7, 81_920),
        _fit_record(structural, (Fraction(1),) * 5, 40_960),
        receipt,
    )
    fit["seeds"][0]["policies"][0]["root"]["normal_matrix"][0][0] = bad
    with pytest.raises(structural.StructuralCertificateError, match="exact rational"):
        structural._validate_fit_structure(fit, receipt)


def test_fit_phase_source_cannot_load_heldout_evaluation_or_oracle(structural):
    assert {"fold_group_key", "fold_id", "reference_tape_member"} <= set(
        structural.FIT_PHASE_FUNCTIONS
    )
    fit_source = inspect.getsource(structural.fit_structural_artifact)
    helper_source = "\n".join(
        inspect.getsource(getattr(structural, name))
        for name in structural.FIT_PHASE_FUNCTIONS
    )
    lowered = (fit_source + helper_source).lower()
    for forbidden in ("k_test", "evaluation", "oracle", "audit_discrete_policy", "construct_flip_certificate"):
        assert forbidden not in lowered
    fit_seed_source = inspect.getsource(structural._fit_seed)
    assert 'row["tail_return"]' in fit_seed_source
    assert 'row["unshaped_return"]' not in fit_seed_source
    assert 'row["immediate_return"]' not in fit_seed_source
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    fit_closure = set(structural.FIT_PHASE_FUNCTIONS) | {"fit_structural_artifact"}
    for name in fit_closure:
        assert name in functions
        for call in (node for node in ast.walk(functions[name]) if isinstance(node, ast.Call)):
            if isinstance(call.func, ast.Name) and call.func.id in functions:
                assert call.func.id in fit_closure, (name, call.func.id)
    top_level_imports = [
        (node.module or "")
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    ]
    assert not any(name.endswith(("evaluation", "oracle", "artifact", "model", "training", "checkpoint")) for name in top_level_imports)
    assert structural.FIT_DATA_DEPENDENCY_CLAIM == (
        "AUDITABLE_FIT_DATA_DEPENDENCY_NO_PROCESS_ISOLATION_CLAIM"
    )


def test_every_production_entry_starts_with_fresh_memory_admission(runner):
    for name in (
        "freeze_reference_bundle", "check_binding", "assess_run",
        "run_certificate", "validate_run",
    ):
        source = inspect.getsource(getattr(runner, name))
        assert "_admit_memory" in source, name
        assert source.index("require_frozen_execution_environment") < source.index(
            "_admit_memory"
        ), name
    admission_source = inspect.getsource(runner._admit_memory)
    assert "hmasd_resource_preflight.py" in admission_source
    assert "admit-memory" in admission_source
    assert "physical_floor_pass" in admission_source
    assert "effective_floor_pass" in admission_source


def test_bundle_separates_prefit_and_postfit_dependencies(runner, structural):
    manifest = runner._bundle_manifest()
    assert set(manifest) == {"format", "complete", "prefit_members", "postfit_members"}
    prefit_sources = {item["source_relative_path"] for item in manifest["prefit_members"]}
    postfit_sources = {item["source_relative_path"] for item in manifest["postfit_members"]}
    assert not any(path.endswith(("belief-result.json", "evaluation.py", "oracle.py")) for path in prefit_sources)
    assert any(path.endswith("rng.py") for path in prefit_sources)
    assert any(path.endswith("structural_replay.py") for path in prefit_sources)
    assert postfit_sources == {
        "experiments/candidates/ucope/contextual_paid_acquisition_r01/oracle.py"
    }
    assert len([item for item in manifest["prefit_members"] if item["schema_role"] == "retained_gzip_tape"]) == 80
    assert prefit_sources.isdisjoint(postfit_sources)
    claim = structural.FIT_DATA_DEPENDENCY_CLAIM
    assert claim == "AUDITABLE_FIT_DATA_DEPENDENCY_NO_PROCESS_ISOLATION_CLAIM"


def test_prefit_replay_has_no_heldout_import_and_matches_frozen_host(structural_replay):
    source = STRUCTURAL_REPLAY_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in ("k_test", "oracle", "evaluation", "belief-result"):
        assert forbidden not in lowered
    tree = ast.parse(source, filename=str(STRUCTURAL_REPLAY_PATH))
    assert all(
        not isinstance(node, ast.ImportFrom) or node.level == 0
        for node in ast.walk(tree)
    )

    prefix = "experiments.candidates.ucope.contextual_paid_acquisition_r01"
    contract = importlib.import_module(f"{prefix}.contract")
    host = importlib.import_module(f"{prefix}.host")
    rng = importlib.import_module(f"{prefix}.rng")
    schema = importlib.import_module(f"{prefix}.schema")
    strata = [
        (slot, "PROBE", period)
        for slot, period in enumerate(contract.K_TRAIN)
    ] + [
        (slot + 5, "IMMEDIATE", period)
        for slot, period in enumerate(contract.K_TRAIN)
    ]
    for seed_slot in ("cpa-r01-fresh-slot-00", "cpa-r01-fresh-slot-09"):
        for context in contract.contexts():
            for regime in ("SHORT", "LONG"):
                for index, action, period in strata:
                    display = regime if context["link"] == "LINKED" else (
                        "LONG" if regime == "SHORT" else "SHORT"
                    )
                    expected = structural_replay.expected_episode_row(
                        seed_slot=seed_slot,
                        context=context,
                        index=index,
                        root_action=action,
                        period=period,
                        regime=regime,
                        display_regime=display,
                        rng=rng,
                    )
                    observed = host.simulate_episode(
                        seed_slot,
                        context,
                        schema.PlanEntry(index=index, root_action=action, period=period),
                        regime,
                        display,
                    ).to_dict()
                    assert expected == observed


def test_full_deterministic_replay_is_inside_prefit_binding_before_fit(runner):
    capture_source = inspect.getsource(runner.capture_prefit_binding)
    structure_source = inspect.getsource(runner._validate_prefit_row_structure)
    compile_source = inspect.getsource(runner._compile_prefit_runtime).lower()
    constants_source = inspect.getsource(runner._training_rng_constants).lower()
    run_source = inspect.getsource(runner._run_certificate_admitted)
    assert "_validate_prefit_row_structure" in capture_source
    assert "_compile_prefit_runtime" in structure_source
    assert "expected_episode_row" in structure_source
    assert "_final_prefit_sweep" in capture_source
    assert capture_source.index("_validate_prefit_row_structure") < capture_source.index(
        "_final_prefit_sweep"
    )
    assert "oracle" not in compile_source + constants_source
    assert "k_test" not in compile_source + constants_source
    contract_id, rng_version = runner._training_rng_constants(
        (PROJECT_ROOT / "experiments/candidates/ucope/contextual_paid_acquisition_r01/contract.py").read_bytes()
    )
    assert contract_id == "UCOPE-CONTEXTUAL-PAID-ACQUISITION-R01-20260830"
    assert rng_version == "UCOPE_CPA_COUNTER_V1"
    assert run_source.index("verify_data_binding") < run_source.index("fit_structural_artifact")


def test_final_prefit_sweep_rejects_drift_after_replay(tmp_path, runner, monkeypatch):
    project = tmp_path / "project"
    bundle = tmp_path / "bundle"
    (project / "source").mkdir(parents=True)
    (bundle / "members").mkdir(parents=True)
    source = project / "source/member.bin"
    frozen = bundle / "members/000.bin"
    source.write_bytes(b"captured")
    frozen.write_bytes(b"captured")
    manifest = b"manifest"
    binding = b"binding"
    admission = b"admission"
    ledger = b"ledger"
    (bundle / "manifest.json").write_bytes(manifest)
    (bundle / runner.PREFIT_BINDING_RECEIPT_FILENAME).write_bytes(binding)
    (bundle / runner.RESOURCE_RECEIPT_FILENAME).write_bytes(admission)
    (bundle / runner.RESOURCE_LEDGER_FILENAME).write_bytes(ledger)
    runner_copy = project / "runner.py"
    runner_copy.write_bytes(b"runner")
    monkeypatch.setattr(runner, "PROJECT_ROOT", project)
    monkeypatch.setattr(runner, "RUNNER_PATH", runner_copy)
    monkeypatch.setattr(runner, "RUNNER_START_BYTES", b"runner")
    arguments = {
        "bundle_path": bundle,
        "manifest_bytes": manifest,
        "frozen_binding_bytes": binding,
        "admission_bytes": admission,
        "ledger_bytes": ledger,
        "records": [{
            "source_relative_path": "source/member.bin",
            "bundle_relative_path": "members/000.bin",
        }],
        "snapshots": (b"captured",),
    }
    runner._final_prefit_sweep(**arguments)
    source.write_bytes(b"drifted")
    with pytest.raises(runner.DataBindingMismatch, match="changed"):
        runner._final_prefit_sweep(**arguments)


def test_freeze_final_sweep_covers_control_bytes_before_atomic_publish(runner):
    source = inspect.getsource(runner.freeze_reference_bundle)
    manifest_write = source.index('atomic_create_bytes(staging / "manifest.json"')
    control_readback = source.index('(staging / "manifest.json").read_bytes()')
    finish = source.index("ledger = monitor.finish()")
    publish = source.index("os.replace(staging, target)")
    assert manifest_write < control_readback < finish < publish
    assert "source_bytes != captured_raw" in source
    assert "frozen.read_bytes() != captured_raw" in source


def test_nonrun_control_paths_are_unique_per_attempt(tmp_path, runner):
    first = runner._control_path("check-binding", None, kind="binding-control")
    second = runner._control_path("check-binding", None, kind="binding-control")
    assert first != second
    validation_a = runner._control_path("validate", tmp_path / "result", kind="binding-control")
    validation_b = runner._control_path("validate", tmp_path / "result", kind="binding-control")
    assert validation_a != validation_b


def test_result_inventory_is_exact_and_rejects_extra_files(tmp_path, runner):
    root = tmp_path / "result"
    root.mkdir()
    for name in (
        runner.FIT_FILENAME,
        runner.FIT_REFERENCE_FILENAME,
        runner.CERTIFICATE_FILENAME,
        runner.RESOURCE_RECEIPT_FILENAME,
        runner.RESOURCE_LEDGER_FILENAME,
    ):
        (root / name).write_bytes(b"fixture")
    runner._validate_result_inventory(root)
    (root / "extra.json").write_bytes(b"extra")
    with pytest.raises(runner.DataBindingMismatch, match="inventory"):
        runner._validate_result_inventory(root)


def test_validator_refits_from_prefit_snapshot_before_policy_recheck(structural):
    source = inspect.getsource(structural.validate_certificate)
    assert "_fit_document" in source
    assert "tape_bytes" in source
    assert "recomputed" in source


def test_run_requires_ready_assessment_before_any_prefit_or_fit(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch, entry="run")
    output = tmp_path / "fixed-result"
    raw_output = _freeze_synthetic_result(output, runner, monkeypatch)
    monkeypatch.setattr(runner, "require_frozen_execution_environment", lambda: None)
    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: admission)
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner))
    monkeypatch.setattr(
        runner,
        "verify_data_binding",
        lambda: pytest.fail("prefit binding reached without ready assessment"),
    )
    monkeypatch.setattr(
        runner.STRUCTURAL,
        "fit_structural_artifact",
        lambda *args, **kwargs: pytest.fail("fit reached without ready assessment"),
    )

    stop_path = runner.run_certificate(raw_output)
    assert stop_path.parent == runner.CONTROL_ROOT
    assert not output.exists()
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    assert stop["disposition"] == "INCOMPLETE_TECHNICAL_PUBLICATION"
    assert stop["actual_stage"] == "PERFORMANCE_QUALIFICATION"
    assert stop["fit_entered"] is stop["evaluation_entered"] is False
    assert stop["resource_admission_relative_path"] == admission[
        "preflight_receipt_relative_path"
    ]
    assert stop["resource_ledger_relative_path"].endswith(".json")


def test_run_assessment_failure_keeps_resource_first_precedence(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch, entry="run")
    output = tmp_path / "fixed-result"
    raw_output = _freeze_synthetic_result(output, runner, monkeypatch)
    monkeypatch.setattr(runner, "require_frozen_execution_environment", lambda: None)
    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: admission)
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner, passed=False))
    monkeypatch.setattr(
        runner,
        "verify_data_binding",
        lambda: pytest.fail("prefit binding reached without ready assessment"),
    )

    stop_path = runner.run_certificate(raw_output)
    assert stop_path.parent == runner.CONTROL_ROOT
    assert not output.exists()
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    assert stop["disposition"] == "INCOMPLETE_RESOURCE_CEILING"
    assert stop["actual_stage"] == "PERFORMANCE_QUALIFICATION"
    ledger = json.loads(
        (runner.PROJECT_ROOT / stop["resource_ledger_relative_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert ledger["passed"] is False


def test_run_validates_ready_assessment_before_prefit_binding(
    tmp_path, runner, monkeypatch,
):
    _materialize_valid_assessment(tmp_path, runner, monkeypatch)
    run_admission = _sandbox_admission(tmp_path, runner, monkeypatch, entry="run")
    output = tmp_path / "fixed-result"
    raw_output = _freeze_synthetic_result(output, runner, monkeypatch)
    monkeypatch.setattr(runner, "require_frozen_execution_environment", lambda: None)
    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: run_admission)
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner))
    events = []
    actual_validator = runner.validate_performance_assessment

    def qualify():
        events.append("assessment")
        return actual_validator()

    def stop_at_binding():
        events.append("prefit")
        raise runner.DataBindingMismatch("synthetic binding stop")

    monkeypatch.setattr(runner, "validate_performance_assessment", qualify)
    monkeypatch.setattr(runner, "verify_data_binding", stop_at_binding)
    stop_path = runner.run_certificate(raw_output)
    assert events == ["assessment", "prefit"]
    assert stop_path.parent == runner.CONTROL_ROOT
    assert not output.exists()
    assert json.loads(stop_path.read_text(encoding="utf-8"))["disposition"] == (
        "STOP_DATA_BINDING"
    )


def test_run_source_orders_assessment_gate_before_prefit_and_fit(runner):
    source = inspect.getsource(runner._run_certificate_admitted)
    assert source.index('ResourceMonitor("run").start()') < source.index(
        "validate_performance_assessment"
    ) < source.index("verify_data_binding") < source.index("fit_structural_artifact")


def test_incomplete_run_attempts_are_unique_controls_only_and_never_claim_result(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch, entry="run")
    result = tmp_path / "fixed-result"
    raw_result = _freeze_synthetic_result(result, runner, monkeypatch)
    receipts = []

    monkeypatch.setattr(
        runner, "_admit_memory",
        lambda _entry: (_ for _ in ()).throw(
            runner.ResourceAdmissionRefusal("synthetic memory refusal")
        ),
    )
    receipts.append(runner.run_certificate(raw_result))
    assert not result.exists()

    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: admission)
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner))
    monkeypatch.setattr(runner, "validate_performance_assessment", lambda: {})
    monkeypatch.setattr(
        runner, "verify_data_binding",
        lambda: (_ for _ in ()).throw(runner.DataBindingMismatch("synthetic drift")),
    )
    receipts.append(runner.run_certificate(raw_result))
    assert not result.exists()

    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner, passed=False))
    receipts.append(runner.run_certificate(raw_result))
    assert not result.exists()

    class StartFailure:
        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            raise RuntimeError("synthetic sampler failure")

        def finish(self):
            raise RuntimeError("synthetic sampler never started")

    monkeypatch.setattr(runner, "ResourceMonitor", StartFailure)
    receipts.append(runner.run_certificate(raw_result))
    assert not result.exists()

    assert len(set(receipts)) == 4
    assert all(path.parent == runner.CONTROL_ROOT and path.is_file() for path in receipts)
    dispositions = [
        json.loads(path.read_text(encoding="utf-8"))["disposition"]
        for path in receipts
    ]
    assert dispositions == [
        "RESOURCE_REFUSAL_NO_SCIENCE_STATE",
        "STOP_DATA_BINDING",
        "INCOMPLETE_RESOURCE_CEILING",
        "INCOMPLETE_TECHNICAL_PUBLICATION",
    ]


def test_atomic_publication_failure_is_repeatable_controls_only(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch, entry="run")
    result = tmp_path / "fixed-result"
    raw_result = _freeze_synthetic_result(result, runner, monkeypatch)
    prefit = {
        "status": "MATCH", "bundle_format": runner.REFERENCE_BUNDLE_FORMAT,
        "member_count": 91, "raw_members_compared": 90,
        "decoder_rows_replayed": 1_638_400,
    }
    postfit = {
        "status": "MATCH", "bundle_format": runner.REFERENCE_BUNDLE_FORMAT,
        "member_count": 91, "raw_members_compared": 91,
    }
    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: admission)
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner))
    monkeypatch.setattr(runner, "validate_performance_assessment", lambda: {})
    monkeypatch.setattr(runner, "verify_data_binding", lambda: prefit)
    monkeypatch.setattr(runner, "_verify_postfit_binding", lambda _prefit: postfit)

    def fit(*, binding_receipt, output_path):
        assert binding_receipt is prefit
        runner.atomic_create_json(output_path, {"format": "fit", "sealed": True})

    def evaluate(
        *, fit_path, fit_reference_path, binding_receipt,
        postfit_binding_receipt, output_path,
    ):
        assert Path(fit_path).read_bytes() == Path(fit_reference_path).read_bytes()
        assert binding_receipt is prefit
        assert postfit_binding_receipt is postfit
        runner.atomic_create_json(
            output_path, {"format": "certificate", "complete": True}
        )

    monkeypatch.setattr(runner.STRUCTURAL, "fit_structural_artifact", fit)
    monkeypatch.setattr(runner.STRUCTURAL, "evaluate_sealed_fit", evaluate)
    monkeypatch.setattr(
        runner.os, "replace",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("synthetic publication failure")
        ),
    )

    first = runner.run_certificate(raw_result)
    second = runner.run_certificate(raw_result)
    assert first != second
    assert all(path.parent == runner.CONTROL_ROOT for path in (first, second))
    assert all(path.is_file() for path in (first, second))
    assert all(
        json.loads(path.read_text(encoding="utf-8"))["disposition"]
        == "INCOMPLETE_TECHNICAL_PUBLICATION"
        for path in (first, second)
    )
    assert not result.exists()


def test_data_binding_refusal_precedes_output_or_fit(tmp_path, runner, monkeypatch):
    called = []
    admission = _sandbox_admission(tmp_path, runner, monkeypatch)

    monkeypatch.setattr(
        runner, "_admit_memory", lambda entry: called.append("memory") or admission,
        raising=False,
    )
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner))
    monkeypatch.setattr(runner, "validate_performance_assessment", lambda: {})

    def refuse():
        called.append("binding")
        raise runner.DataBindingMismatch("drift")

    monkeypatch.setattr(runner, "verify_data_binding", refuse)
    monkeypatch.setattr(
        runner.STRUCTURAL,
        "fit_structural_artifact",
        lambda *args, **kwargs: pytest.fail("fit reached after data binding drift"),
    )
    monkeypatch.setattr(
        runner.STRUCTURAL,
        "evaluate_sealed_fit",
        lambda *args, **kwargs: pytest.fail("evaluation reached after data binding drift"),
    )
    output = tmp_path / "result"
    raw_output = _freeze_synthetic_result(output, runner, monkeypatch)
    receipt_path = runner.run_certificate(raw_output)
    assert called == ["memory", "binding"]
    assert receipt_path.parent == runner.CONTROL_ROOT
    assert not output.exists()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["format"] == runner.CONTROL_RECEIPT_FORMAT
    assert receipt["complete"] is True
    assert receipt["disposition"] == "STOP_DATA_BINDING"
    assert receipt["actual_stage"] == "PREFIT_BINDING"
    assert receipt["fit_entered"] is receipt["evaluation_entered"] is False
    assert receipt["fit_published"] is receipt["evaluation_published"] is False
    assert receipt["scientific_certificate_published"] is False
    assert receipt["resource_admission_relative_path"] == admission[
        "preflight_receipt_relative_path"
    ]
    assert receipt["resource_ledger_relative_path"].endswith(".json")
    assert not output.exists()


def test_runtime_ceiling_precedes_data_binding_stop_and_persists_ledger(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch)
    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: admission)
    monkeypatch.setattr(runner, "ResourceMonitor", _monitor_type(runner, passed=False))
    monkeypatch.setattr(runner, "validate_performance_assessment", lambda: {})
    monkeypatch.setattr(
        runner, "verify_data_binding",
        lambda: (_ for _ in ()).throw(runner.DataBindingMismatch("late drift")),
    )
    output = tmp_path / "resource-first"
    raw_output = _freeze_synthetic_result(output, runner, monkeypatch)
    path = runner.run_certificate(raw_output)
    assert path.parent == runner.CONTROL_ROOT
    assert not output.exists()
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["disposition"] == "INCOMPLETE_RESOURCE_CEILING"
    assert receipt["complete"] is False
    assert receipt["fit_entered"] is receipt["evaluation_entered"] is False
    ledger = json.loads(
        (runner.PROJECT_ROOT / receipt["resource_ledger_relative_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert ledger["passed"] is False


def test_sampler_start_failure_is_incomplete_technical_with_no_live_ledger(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch)
    monkeypatch.setattr(runner, "_admit_memory", lambda _entry: admission)

    class StartFailure:
        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            raise RuntimeError("sampler unavailable")

        def finish(self):
            raise RuntimeError("sampler never started")

    monkeypatch.setattr(runner, "ResourceMonitor", StartFailure)
    output = tmp_path / "sampler-stop"
    raw_output = _freeze_synthetic_result(output, runner, monkeypatch)
    path = runner.run_certificate(raw_output)
    assert path.parent == runner.CONTROL_ROOT
    assert not output.exists()
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["disposition"] == "INCOMPLETE_TECHNICAL_PUBLICATION"
    assert receipt["actual_stage"] == "ENTRY_SETUP"
    assert receipt["resource_ledger_relative_path"] is None


def test_frozen_resource_ceilings_and_runtime_observation_surface(runner):
    assert runner.RESOURCE_BASELINE_PROCESS_THREAD_CEILING == 4
    assert runner.RESOURCE_SAMPLER_THREAD_ALLOWANCE == 1
    assert runner.RESOURCE_CEILINGS == {
        "workers": 1,
        "scientific_child_processes": 0,
        "wall_seconds": 3_600,
        "cpu_seconds": 3_600,
        "peak_process_threads": 5,
        "peak_rss_bytes": 2 * 1024**3,
        "scratch_high_water_bytes": 256 * 1024**2,
        "durable_high_water_bytes": 256 * 1024**2,
        "aggregate_io_bytes": 8 * 1024**3,
    }
    monitor_source = inspect.getsource(runner.ResourceMonitor)
    for observation in (
        "wall_seconds",
        "cpu_seconds",
        "peak_process_threads",
        "peak_rss_bytes",
        "scratch_high_water_bytes",
        "durable_high_water_bytes",
        "read_bytes",
        "write_bytes",
        "aggregate_io_bytes",
    ):
        assert observation in monitor_source
    assert "GetProcessMemoryInfo" in monitor_source
    assert "GetProcessIoCounters" in monitor_source
    assert "GetProcessTimes" in monitor_source
    assert "CreateToolhelp32Snapshot" in monitor_source
    assert runner.PUBLICATION_HEADROOM == {
        "wall_seconds": 10,
        "cpu_seconds": 10,
        "peak_rss_bytes": 16 * 1024**2,
        "scratch_high_water_bytes": 1024**2,
        "durable_high_water_bytes": 1024**2,
        "aggregate_io_bytes": 4 * 1024**2,
    }
    assert runner.RESOURCE_SAMPLE_SECONDS == 0.25


def test_resource_monitor_accounts_for_exactly_one_sampler_thread(
    runner, monkeypatch,
):
    monkeypatch.setattr(runner, "RESOURCE_SAMPLE_SECONDS", 0.001)
    sampler_observed = threading.Event()
    samples = []
    monitor = runner.ResourceMonitor("synthetic-thread-accounting")

    def synthetic_process_observation():
        sampler_alive = monitor._thread.is_alive()
        process_threads = (
            runner.RESOURCE_BASELINE_PROCESS_THREAD_CEILING
            + int(sampler_alive)
        )
        samples.append((sampler_alive, process_threads))
        if sampler_alive:
            sampler_observed.set()
        return 0.0, 0, process_threads, 0, 0, 0

    monkeypatch.setattr(monitor, "_process_observation", synthetic_process_observation)
    monitor.start()
    assert sampler_observed.wait(timeout=1.0)
    ledger = monitor.finish()

    assert samples[0] == (
        False, runner.RESOURCE_BASELINE_PROCESS_THREAD_CEILING,
    )
    assert (True, runner.RESOURCE_CEILINGS["peak_process_threads"]) in samples
    assert samples[-1] == (
        False, runner.RESOURCE_BASELINE_PROCESS_THREAD_CEILING,
    )
    assert runner.RESOURCE_CEILINGS["peak_process_threads"] == (
        runner.RESOURCE_BASELINE_PROCESS_THREAD_CEILING
        + runner.RESOURCE_SAMPLER_THREAD_ALLOWANCE
    )
    assert ledger["observed"]["peak_process_threads"] == 5
    assert ledger["observed"]["scientific_child_processes"] == 0
    assert ledger["passed"] is True


def test_sixth_process_thread_fails_ceiling_and_ledger_disposition(runner):
    observed = deepcopy(_resource_ledger(runner)["observed"])
    observed["peak_process_threads"] = (
        runner.RESOURCE_CEILINGS["peak_process_threads"] + 1
    )
    assert observed["peak_process_threads"] == 6
    assert runner._resource_observation_passes(observed) is False

    ledger = {
        "format": "UCOPE_STRUCTURAL_RESOURCE_LEDGER_V1",
        "entry": "run",
        "ceilings": dict(runner.RESOURCE_CEILINGS),
        "measurement_scope": runner.RESOURCE_MEASUREMENT_SCOPE,
        "sample_interval_seconds": runner.RESOURCE_SAMPLE_SECONDS,
        "publication_headroom": dict(runner.PUBLICATION_HEADROOM),
        "observed": observed,
        "passed": False,
    }
    runner._validate_runtime_ledger(ledger, entry="run", require_pass=False)

    ledger["passed"] = True
    with pytest.raises(
        runner.ResourceAdmissionRefusal,
        match="disposition differs from frozen predicate",
    ):
        runner._validate_runtime_ledger(ledger, entry="run", require_pass=False)


def test_resource_ledger_strictly_checks_workers_io_and_publication_headroom(runner):
    admission = {
        "entry": "run",
        "passed": True,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "available_physical_bytes": 8 * 1024**3,
        "effective_available_bytes": 8 * 1024**3,
    }
    observed = {
        "workers": 1,
        "wall_seconds": 1,
        "cpu_seconds": 1,
        "peak_process_threads": 2,
        "peak_rss_bytes": 1024,
        "scientific_child_processes": 0,
        "scratch_high_water_bytes": 0,
        "durable_high_water_bytes": 0,
        "read_bytes": 10,
        "write_bytes": 20,
        "aggregate_io_bytes": 30,
    }
    ledger = {
        "format": "UCOPE_STRUCTURAL_RESOURCE_LEDGER_V1",
        "entry": "run",
        "ceilings": dict(runner.RESOURCE_CEILINGS),
        "measurement_scope": runner.RESOURCE_MEASUREMENT_SCOPE,
        "sample_interval_seconds": runner.RESOURCE_SAMPLE_SECONDS,
        "publication_headroom": dict(runner.PUBLICATION_HEADROOM),
        "observed": observed,
        "passed": True,
    }
    runner._validate_resource_values(admission, ledger, entry="run")
    bad_workers = deepcopy(ledger)
    bad_workers["observed"]["workers"] = 0
    with pytest.raises(runner.ResourceAdmissionRefusal, match="worker"):
        runner._validate_resource_values(admission, bad_workers, entry="run")
    fractional_workers = deepcopy(ledger)
    fractional_workers["observed"]["workers"] = 1.0
    with pytest.raises(runner.ResourceAdmissionRefusal, match="malformed"):
        runner._validate_resource_values(admission, fractional_workers, entry="run")
    fractional_bytes = deepcopy(ledger)
    fractional_bytes["observed"]["read_bytes"] = 10.5
    fractional_bytes["observed"]["aggregate_io_bytes"] = 30.5
    with pytest.raises(runner.ResourceAdmissionRefusal, match="malformed"):
        runner._validate_resource_values(admission, fractional_bytes, entry="run")
    bad_io = deepcopy(ledger)
    bad_io["observed"]["aggregate_io_bytes"] = 31
    with pytest.raises(runner.ResourceAdmissionRefusal, match="aggregate I/O"):
        runner._validate_resource_values(admission, bad_io, entry="run")
    no_headroom = deepcopy(ledger)
    no_headroom["observed"]["wall_seconds"] = runner.RESOURCE_CEILINGS["wall_seconds"]
    with pytest.raises(runner.ResourceAdmissionRefusal, match="ceiling"):
        runner._validate_resource_values(admission, no_headroom, entry="run")


def test_control_validator_rejects_ledger_disposition_inversion(
    tmp_path, runner, monkeypatch,
):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch)
    root = tmp_path / "fixed-result"
    monitor = _monitor_type(runner, passed=False)("run").start()
    path = runner._publish_failed_entry(
        "run", kind="binding", output_root=root,
        actual_stage="PREFIT_BINDING", fit_entered=False,
        evaluation_entered=False,
        monitor=monitor, admission=admission,
    )
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["disposition"] == "INCOMPLETE_RESOURCE_CEILING"
    assert value["resource_ledger_relative_path"].endswith(".json")
    assert path.parent == runner.CONTROL_ROOT
    assert not root.exists()


def test_validator_resource_sidecars_are_attempt_unique(tmp_path, runner):
    root = tmp_path / "result"
    root.mkdir()
    admission = {"entry": "validate", "passed": True}
    ledger = _resource_ledger(runner, "validate")
    first = runner._publish_validation_resources(root, admission, ledger)
    second = runner._publish_validation_resources(root, admission, ledger)
    assert set(first).isdisjoint(second)
    assert all(path.is_file() for path in first + second)


def test_memory_preflight_receipt_is_durable_and_not_deleted(runner):
    source = inspect.getsource(runner._admit_memory)
    assert "resource-receipts" in source
    assert "preflight_receipt_relative_path" in source
    assert "mkdtemp" not in source
    assert "rmtree" not in source


def test_memory_preflight_process_start_failure_is_resource_refusal(
    tmp_path, runner, monkeypatch,
):
    monkeypatch.setattr(runner, "CONTROL_ROOT", tmp_path / "controls")
    monkeypatch.setattr(
        runner.subprocess, "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("cannot launch")),
    )
    with pytest.raises(runner.ResourceAdmissionRefusal, match="could not execute"):
        runner._admit_memory("run")


def test_manifest_phase_role_is_explicit_and_fail_closed(runner):
    manifest = runner._bundle_manifest()
    prefit, postfit = runner._validate_manifest_shape(manifest)
    assert {record["phase_role"] for record in prefit} == {"PREFIT"}
    assert {record["phase_role"] for record in postfit} == {"POSTFIT"}
    drift = deepcopy(manifest)
    drift["prefit_members"][0]["phase_role"] = "POSTFIT"
    with pytest.raises(runner.DataBindingMismatch, match="schema"):
        runner._validate_manifest_shape(drift)


def test_control_receipts_separate_activity_from_publication(tmp_path, runner, monkeypatch):
    admission = _sandbox_admission(tmp_path, runner, monkeypatch)
    admission_path = admission["preflight_receipt_relative_path"]
    passing_ledger_path = _store_control_ledger(
        runner, _resource_ledger(runner), "passing-ledger"
    )
    failing_ledger_path = _store_control_ledger(
        runner, _resource_ledger(runner, passed=False), "failing-ledger"
    )
    final_drift_root = tmp_path / "final-drift"
    path = runner.publish_binding_stop(
        "run", "drift", final_drift_root, actual_stage="FINAL_BINDING",
        fit_entered=True, evaluation_entered=True,
        resource_admission_relative_path=admission_path,
        resource_ledger_relative_path=passing_ledger_path,
    )
    value = json.loads(path.read_text(encoding="utf-8"))
    assert path.parent == runner.CONTROL_ROOT
    assert not final_drift_root.exists()
    assert value["disposition"] == "STOP_DATA_BINDING"
    assert value["actual_stage"] == "FINAL_BINDING"
    assert value["fit_entered"] is value["evaluation_entered"] is True
    assert value["fit_published"] is value["evaluation_published"] is False
    assert value["scientific_certificate_published"] is False

    refusal_root = tmp_path / "memory-refusal"
    refusal_path = runner.publish_resource_stop("run", refusal_root)
    refusal = json.loads(refusal_path.read_text(encoding="utf-8"))
    assert refusal_path.parent == runner.CONTROL_ROOT
    assert not refusal_root.exists()
    assert refusal["complete"] is True
    assert refusal["disposition"] == "RESOURCE_REFUSAL_NO_SCIENCE_STATE"
    assert refusal["actual_stage"] == "MEMORY_ADMISSION"
    assert refusal["fit_entered"] is refusal["evaluation_entered"] is False

    overrun_root = tmp_path / "resource-overrun"
    overrun_path = runner.publish_resource_stop(
        "run", overrun_root, runtime_ceiling=True, actual_stage="PREPUBLICATION_RESOURCE",
        fit_entered=True, evaluation_entered=True,
        resource_admission_relative_path=admission_path,
        resource_ledger_relative_path=failing_ledger_path,
    )
    overrun = json.loads(overrun_path.read_text(encoding="utf-8"))
    assert overrun_path.parent == runner.CONTROL_ROOT
    assert not overrun_root.exists()
    assert overrun["complete"] is False
    assert overrun["disposition"] == "INCOMPLETE_RESOURCE_CEILING"
    assert overrun["fit_entered"] is overrun["evaluation_entered"] is True

    technical_root = tmp_path / "technical-publication"
    technical_path = runner.publish_technical_stop(
        "run", technical_root, actual_stage="ENTRY_SETUP",
        resource_admission_relative_path=admission_path,
    )
    technical = json.loads(technical_path.read_text(encoding="utf-8"))
    assert technical_path.parent == runner.CONTROL_ROOT
    assert not technical_root.exists()
    assert technical["complete"] is False
    assert technical["disposition"] == "INCOMPLETE_TECHNICAL_PUBLICATION"


def test_missing_bundle_is_one_data_binding_stop(tmp_path, runner, monkeypatch):
    monkeypatch.setattr(runner, "_admit_memory", lambda entry: {"passed": True}, raising=False)
    with pytest.raises(runner.DataBindingMismatch):
        runner.verify_reference_binding(tmp_path / "absent", replay_rows=False)


def test_runner_seals_fit_before_evaluation_and_is_create_once(tmp_path, runner, monkeypatch):
    events = []
    receipt = {
        "status": "MATCH", "bundle_format": "fixed", "member_count": 91,
        "raw_members_compared": 90, "decoder_rows_replayed": 1_638_400,
    }

    def bind():
        events.append("binding")
        return receipt

    postfit_receipt = {
        "status": "MATCH", "bundle_format": "fixed", "member_count": 91,
        "raw_members_compared": 91,
    }

    def postfit(prefit):
        events.append("postfit-binding")
        assert prefit is receipt
        return postfit_receipt

    monkeypatch.setattr(runner, "verify_data_binding", bind)
    monkeypatch.setattr(runner, "_verify_postfit_binding", postfit)
    monkeypatch.setattr(
        runner, "_admit_memory", lambda entry: events.append("memory") or {"passed": True},
        raising=False,
    )

    class PassingMonitor:
        def __init__(self, entry, **_kwargs):
            self.entry = entry
            self._thread = type("StoppedThread", (), {"is_alive": lambda self: False})()

        def start(self):
            return self

        def set_paths(self, **_kwargs):
            return None

        def finish(self):
            return {"entry": self.entry, "passed": True}

    monkeypatch.setattr(runner, "ResourceMonitor", PassingMonitor)
    monkeypatch.setattr(runner, "validate_performance_assessment", lambda: {})

    def fit(*, binding_receipt, output_path):
        events.append("fit")
        assert binding_receipt is receipt
        runner.atomic_create_json(output_path, {"format": "fit", "sealed": True})
        return Path(output_path)

    def evaluate(
        *, fit_path, fit_reference_path, binding_receipt,
        postfit_binding_receipt, output_path,
    ):
        events.append("evaluate")
        assert json.loads(Path(fit_path).read_text(encoding="utf-8"))["sealed"] is True
        assert Path(fit_path).read_bytes() == Path(fit_reference_path).read_bytes()
        assert binding_receipt is receipt
        assert postfit_binding_receipt is postfit_receipt
        runner.atomic_create_json(output_path, {"format": "certificate", "complete": True})
        return Path(output_path)

    monkeypatch.setattr(runner.STRUCTURAL, "fit_structural_artifact", fit)
    monkeypatch.setattr(runner.STRUCTURAL, "evaluate_sealed_fit", evaluate)
    output = tmp_path / "result"
    raw_output = _freeze_synthetic_result(output, runner, monkeypatch)
    certificate = runner.run_certificate(raw_output)
    assert certificate == output / runner.CERTIFICATE_FILENAME
    assert events == ["memory", "binding", "fit", "postfit-binding", "evaluate"]
    original = certificate.read_bytes()
    with pytest.raises(FileExistsError):
        runner.run_certificate(raw_output)
    assert certificate.read_bytes() == original
