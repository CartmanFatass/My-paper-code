from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import subprocess

import pytest

from experiments.candidates.ec4g_r1 import portable_source_bound_two_phase_execution_census as census
from experiments.candidates.ec4g_r1 import two_phase_execution_materialization_census as a4


WORKTREE_ROOT = Path(census.__file__).resolve().parents[3]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def _make_source_repo(tmp_path: Path, monkeypatch) -> tuple[Path, Path, str, census.SourceEntryAdmission]:
    root = tmp_path / "registered"
    main = tmp_path / "main"
    main.mkdir()
    for relative in (census.RUNNER_PATH, census.SOURCE_PATH, census.PURE_ALGORITHM_DEPENDENCY_PATH):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((WORKTREE_ROOT / relative).read_bytes())
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    _git(root, "config", "user.email", "unit@example.invalid")
    _git(root, "config", "user.name", "EC4G unit fixture")
    _git(root, "config", "core.autocrlf", "true")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "source fixture")
    revision = _git(root, "rev-parse", "HEAD")
    monkeypatch.chdir(root)
    entry = census.admit_source_entry(
        source_revision=revision,
        registered_worktree_root=root,
        main_checkout_root=main,
        runner_file=root / census.RUNNER_PATH,
        runtime_module_file=root / census.SOURCE_PATH,
        pure_algorithm_dependency_file=root / census.PURE_ALGORITHM_DEPENDENCY_PATH,
    )
    return root, main, revision, entry


@pytest.fixture
def source_repo(tmp_path: Path, monkeypatch):
    return _make_source_repo(tmp_path, monkeypatch)


@pytest.fixture
def immutable_inputs() -> tuple[bytes, bytes]:
    return (
        subprocess.run(
            ["git", "-C", str(WORKTREE_ROOT), "cat-file", "blob", f"{census.C0_COMMIT}:{census.CONTRACT_PATH}"],
            check=True,
            capture_output=True,
        ).stdout,
        subprocess.run(
            ["git", "-C", str(WORKTREE_ROOT), "cat-file", "blob", f"{census.C1_COMMIT}:{census.BINDING_PATH}"],
            check=True,
            capture_output=True,
        ).stdout,
    )


def test_source_entry_accepts_exact_registered_commit_and_records_all_dependencies(source_repo) -> None:
    root, main, revision, entry = source_repo
    assert entry.accepted is True
    assert entry.first_failure is None
    assert Path(entry.registered_worktree_root) == root.resolve()
    assert Path(entry.canonical_cwd) == root.resolve()
    assert Path(entry.main_checkout_root) == main.resolve()
    assert entry.git_head == revision
    assert [item.role for item in entry.files] == [
        "runner",
        "runtime_core_module",
        "pure_algorithm_dependency",
    ]
    assert [item.relative_path for item in entry.files] == [
        census.RUNNER_PATH,
        census.SOURCE_PATH,
        census.PURE_ALGORITHM_DEPENDENCY_PATH,
    ]
    assert all(
        len(item.sha256) == len(item.committed_blob_sha256) == 64
        and len(item.git_blob_oid) in {40, 64}
        and item.worktree_filtered_blob_oid == item.git_blob_oid
        and item.match_mode in {"raw_bytes", "git_clean_filter_blob"}
        for item in entry.files
    )


def test_main_checkout_or_wrong_cwd_is_rejected_before_source_blobs(source_repo, monkeypatch) -> None:
    root, main, revision, _entry = source_repo
    monkeypatch.chdir(main)
    entry = census.admit_source_entry(
        source_revision=revision,
        registered_worktree_root=root,
        main_checkout_root=main,
        runner_file=root / census.RUNNER_PATH,
        runtime_module_file=root / census.SOURCE_PATH,
        pure_algorithm_dependency_file=root / census.PURE_ALGORITHM_DEPENDENCY_PATH,
    )
    assert entry.accepted is False
    assert "cwd" in entry.first_failure["detail"]

    monkeypatch.chdir(root)
    main_entry = census.admit_source_entry(
        source_revision=revision,
        registered_worktree_root=root,
        main_checkout_root=root,
        runner_file=root / census.RUNNER_PATH,
        runtime_module_file=root / census.SOURCE_PATH,
        pure_algorithm_dependency_file=root / census.PURE_ALGORITHM_DEPENDENCY_PATH,
    )
    assert main_entry.accepted is False
    assert "main checkout" in main_entry.first_failure["detail"]


@pytest.mark.parametrize("relative", [census.RUNNER_PATH, census.SOURCE_PATH, census.PURE_ALGORITHM_DEPENDENCY_PATH])
def test_runner_core_or_dependency_blob_tamper_is_rejected(source_repo, relative: str) -> None:
    root, main, revision, _entry = source_repo
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n# tampered\n")
    entry = census.admit_source_entry(
        source_revision=revision,
        registered_worktree_root=root,
        main_checkout_root=main,
        runner_file=root / census.RUNNER_PATH,
        runtime_module_file=root / census.SOURCE_PATH,
        pure_algorithm_dependency_file=root / census.PURE_ALGORITHM_DEPENDENCY_PATH,
    )
    assert entry.accepted is False
    assert "live bytes/filtered Git blob differ" in entry.first_failure["detail"]


def test_other_root_runtime_import_is_rejected(source_repo, tmp_path: Path) -> None:
    root, main, revision, _entry = source_repo
    other = tmp_path / "other" / "core.py"
    other.parent.mkdir()
    other.write_bytes((root / census.SOURCE_PATH).read_bytes())
    entry = census.admit_source_entry(
        source_revision=revision,
        registered_worktree_root=root,
        main_checkout_root=main,
        runner_file=root / census.RUNNER_PATH,
        runtime_module_file=other,
        pure_algorithm_dependency_file=root / census.PURE_ALGORITHM_DEPENDENCY_PATH,
    )
    assert entry.accepted is False
    assert "runtime_core_module" in entry.first_failure["detail"]


def test_symlink_escape_is_rejected(source_repo, tmp_path: Path) -> None:
    root, main, revision, _entry = source_repo
    core = root / census.SOURCE_PATH
    outside = tmp_path / "outside-core.py"
    outside.write_bytes(core.read_bytes())
    core.unlink()
    try:
        core.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    entry = census.admit_source_entry(
        source_revision=revision,
        registered_worktree_root=root,
        main_checkout_root=main,
        runner_file=root / census.RUNNER_PATH,
        runtime_module_file=core,
        pure_algorithm_dependency_file=root / census.PURE_ALGORITHM_DEPENDENCY_PATH,
    )
    assert entry.accepted is False
    assert "runtime_core_module" in entry.first_failure["detail"]


def test_symlink_component_guard_fails_closed_when_platform_probe_reports_link(source_repo, monkeypatch) -> None:
    root, main, revision, _entry = source_repo
    original = census._has_symlink_component

    def probe(registered_root: Path, relative_path: str) -> bool:
        return relative_path == census.SOURCE_PATH or original(registered_root, relative_path)

    monkeypatch.setattr(census, "_has_symlink_component", probe)
    entry = census.admit_source_entry(
        source_revision=revision,
        registered_worktree_root=root,
        main_checkout_root=main,
        runner_file=root / census.RUNNER_PATH,
        runtime_module_file=root / census.SOURCE_PATH,
        pure_algorithm_dependency_file=root / census.PURE_ALGORITHM_DEPENDENCY_PATH,
    )
    assert entry.accepted is False
    assert entry.first_failure["detail"] == "runtime_core_module has a symlink component"


def test_source_binding_failure_returns_first_branch_with_all_science_zero(tmp_path: Path) -> None:
    entry = census.SourceEntryAdmission(
        False,
        "0" * 40,
        str(tmp_path / "registered"),
        str(tmp_path / "main"),
        str(tmp_path / "main"),
        "runner",
        "core",
        "dependency",
        None,
        (),
        {"code": "SOURCE_ENTRY_BINDING_INVALID", "detail": "unit fixture"},
    )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("source failure must precede all science")

    result = census.run_portable_two_phase_census(
        None,
        None,
        entry_admission=entry,
        artifact_root=tmp_path / "must-not-exist",
        run_id="source-invalid",
        components=a4.ExecutionComponents(forbidden, forbidden, forbidden),
    )
    assert result.terminal_branch is census.PortableCensusBranch.SOURCE_ENTRY_BINDING_INVALID
    assert result.activity_counts["runs"] == result.activity_counts["entry_records"] == 1
    assert all(
        value == 0
        for key, value in result.activity_counts.items()
        if key not in {"runs", "entry_records"}
    )
    assert not (tmp_path / "must-not-exist").exists()
    assert result.design_freeze is None and result.payload()["D_RER3"] is None


def test_complete_fixture_is_fresh_exact_two_phase_census(
    tmp_path: Path, source_repo, immutable_inputs
) -> None:
    _root, _main, _revision, entry = source_repo
    result = census.run_portable_two_phase_census(
        *immutable_inputs,
        entry_admission=entry,
        artifact_root=tmp_path / "fresh-a5",
        run_id="unit-complete",
    )
    assert result.terminal_branch is census.PortableCensusBranch.COMPLETE_PORTABLE_TWO_PHASE_EXECUTION_CENSUS
    assert result.activity_counts == {
        "runs": 1,
        "entry_records": 1,
        "snapshots": 1,
        "map_calls": 6,
        "compiler_calls": 6,
        "objects": 6,
        "comparisons": 3,
        "pair_witnesses": 3,
        "D": 1,
        "prediction_uses": 0,
        "post_seal_writes": 0,
        "human_decisions_between_phases": 0,
        "all_environment_policy_learning_training_optimizer_evaluation_model_fit_stochastic_calls": 0,
        "retries_repairs_corrected_invocations_rescans_reconstructions": 0,
    }
    assert result.equality_vector == {"join": True, "leave": False, "rejoin": True}
    assert result.d_fraction == Fraction(1, 4) and result.d_decimal == Decimal("0.25")
    assert [item.pair for item in result.pair_witnesses] == ["join", "leave", "rejoin"]
    assert result.payload()["fresh_identity"] == {
        "a4_runtime_artifacts_read": 0,
        "a4_inferred_objects_reused": 0,
        "a4_equality_or_D_reused": 0,
        "fresh_phase_1_required": True,
    }
    assert b"predicted_D_RER3" not in result.to_bytes()
    assert result.payload()["result_id"] == "ec4g-a5-unit-complete"


def test_phase2_is_map_and_compiler_free(tmp_path: Path, source_repo, immutable_inputs, monkeypatch) -> None:
    _root, _main, _revision, entry = source_repo

    def close_construction(_seal) -> None:
        def forbidden(*_args, **_kwargs):
            raise AssertionError("Phase 2 must not call maps or compiler")

        monkeypatch.setattr(a4, "map_ec4g", forbidden)
        monkeypatch.setattr(a4, "map_direct_tau", forbidden)
        monkeypatch.setattr(a4, "compile_gamma", forbidden)

    result = census.run_portable_two_phase_census(
        *immutable_inputs,
        entry_admission=entry,
        artifact_root=tmp_path / "map-free-phase2",
        run_id="map-free",
        after_seal=close_construction,
    )
    assert result.terminal_branch is census.PortableCensusBranch.COMPLETE_PORTABLE_TWO_PHASE_EXECUTION_CENSUS
    assert result.activity_counts["map_calls"] == result.activity_counts["compiler_calls"] == 6
    assert result.activity_counts["comparisons"] == 3 and result.activity_counts["D"] == 1


def test_post_seal_change_prevents_all_comparison_and_D(tmp_path: Path, source_repo, immutable_inputs) -> None:
    _root, _main, _revision, entry = source_repo

    def mutate(seal: a4.Phase1Seal) -> None:
        object_path = seal.artifact_root / "00_k_join_M_E.object.json"
        document = json.loads(object_path.read_bytes())
        document["primitive_actions"] = ["post-seal-change"]
        object_path.write_bytes(census.canonical_json_bytes(document) + b"\n")

    result = census.run_portable_two_phase_census(
        *immutable_inputs,
        entry_admission=entry,
        artifact_root=tmp_path / "changed",
        run_id="changed",
        after_seal=mutate,
    )
    assert result.terminal_branch is census.PortableCensusBranch.PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID
    assert result.activity_counts["post_seal_writes"] == 1
    assert result.activity_counts["comparisons"] == 0
    assert result.activity_counts["pair_witnesses"] == 0
    assert result.activity_counts["D"] == 0
    assert result.equality_vector is None and result.payload()["D_RER3"] is None


def test_forbidden_prediction_flow_precedes_materialization(tmp_path: Path, source_repo, immutable_inputs) -> None:
    _root, _main, _revision, entry = source_repo
    result = census.run_portable_two_phase_census(
        *immutable_inputs,
        entry_admission=entry,
        artifact_root=tmp_path / "forbidden",
        run_id="forbidden",
        information_flow_events=({"code": "PREDICTION_FIELD_USE", "detail": "unit sentinel"},),
    )
    assert result.terminal_branch is census.PortableCensusBranch.FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE
    assert result.activity_counts["prediction_uses"] == 1
    assert result.activity_counts["map_calls"] == result.activity_counts["compiler_calls"] == 0
    assert not (tmp_path / "forbidden").exists()


def test_c0_c1_read_failure_is_exact_input_branch_before_science(tmp_path: Path, source_repo) -> None:
    _root, _main, _revision, entry = source_repo
    result = census.run_portable_two_phase_census(
        None,
        None,
        entry_admission=entry,
        artifact_root=tmp_path / "unread",
        run_id="unread",
        input_read_failure="registered C0 blob unavailable",
    )
    assert result.terminal_branch is census.PortableCensusBranch.INPUT_OR_DESIGN_FREEZE_INVALID
    assert result.first_failure == {
        "code": "C0_C1_SNAPSHOT_READ_FAILED",
        "detail": "registered C0 blob unavailable",
    }
    assert result.activity_counts["map_calls"] == result.activity_counts["compiler_calls"] == 0
    assert result.activity_counts["objects"] == result.activity_counts["comparisons"] == result.activity_counts["D"] == 0
    assert not (tmp_path / "unread").exists()


def test_extra_compiler_field_fails_phase1_without_comparison_or_D(
    tmp_path: Path, source_repo, immutable_inputs
) -> None:
    _root, _main, _revision, entry = source_repo

    def extra(contract, cell, action, map_identity):
        value = dict(census.compile_gamma(contract, cell, action, map_identity))
        value["unexpected"] = "forbidden"
        return value

    result = census.run_portable_two_phase_census(
        *immutable_inputs,
        entry_admission=entry,
        artifact_root=tmp_path / "extra",
        run_id="extra",
        components=a4.ExecutionComponents(census.map_ec4g, census.map_direct_tau, extra),
    )
    assert result.terminal_branch is census.PortableCensusBranch.MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS
    assert result.activity_counts["map_calls"] == 1
    assert result.activity_counts["compiler_calls"] == 1
    assert result.activity_counts["objects"] == 0
    assert result.activity_counts["comparisons"] == result.activity_counts["D"] == 0


def test_result_schema_uses_only_a5_branches_and_exact_source_entry_record(
    tmp_path: Path, source_repo, immutable_inputs
) -> None:
    _root, _main, _revision, entry = source_repo
    result = census.run_portable_two_phase_census(
        *immutable_inputs,
        entry_admission=entry,
        artifact_root=tmp_path / "schema",
        run_id="schema",
    )
    payload = result.payload()
    assert payload["treatment_id"] == census.TREATMENT_ID
    assert payload["terminal_branch"] in census.ORDERED_BRANCHES
    assert payload["design_freeze"]["ordered_branches"] == list(census.ORDERED_BRANCHES)
    assert payload["design_freeze"]["hard_caps"] == census.HARD_CAPS
    assert payload["source_entry_admission"] == entry.payload()
    assert payload["operator_receipt"]["status"] == "not_invoked_by_source"
    assert payload["technical_acceptance"]["owner"] == "code_project_manager"
    assert b"EC4G-A4-TWO-PHASE" not in result.to_bytes()
