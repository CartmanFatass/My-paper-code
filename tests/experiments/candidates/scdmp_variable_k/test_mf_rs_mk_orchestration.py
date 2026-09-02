from __future__ import annotations

import json
import copy
import base64
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import contracts
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.assessment import (
    ASSESS_COUNTS,
    finalize_assess_success,
    prepare_assess_attempt,
    raise_after_quarantine,
    write_no_polarity_terminal,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.foundation import (
    direct_tensor_state,
    materialize_foundation,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.orchestration import (
    AttemptError,
    WorkLedger,
    _initialize_or_resume_attempt,
    _issue_initial_telemetry_witness,
    load_foundation_checkpoint,
    write_foundation_checkpoint,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.preflight import (
    preflight_run,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.rng import (
    CounterRNG, materialize_disturbance_tape,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.resources import (
    ResourceTelemetry,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.training import (
    ExactAdamW,
    UpdateReceipt,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.workload import (
    execute_training_update,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.source_identity import (
    ASSIGNED_BASE_COMMIT,
    OWNED_PRODUCTION_PATHS,
    SourceIdentityError,
    compute_source_identity_bytes,
    validate_source_identity_bytes,
    validate_source_identity_gate,
    write_source_identity_gate,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import quarantine as quarantine_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.quarantine import (
    quarantine_lock_path,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import production as production_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import native_backend as native_backend_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import assessment as assessment_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.runner import (
    RUN_CONFIRMATION,
    run_result,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import runner as runner_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.active_gate import (
    ActiveGateError,
    ActiveInvocationGate,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.frontier import (
    TECHNICAL_FRONTIER_IDS,
    FrontierController,
    TechnicalSliceStop,
    load_technical_frontier,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import frontier as frontier_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.foundation import (
    ImmutableBatchedFoundationPolicy,
    freeze_foundation_actor,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_backend import (
    NativeSession, construct_reachable_twins,
)


FOUR_GIB = 4 * 1024**3
MASTER = b"scdmp-b01-test-master-32-bytes!!"


def _canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _admit(command, **_kwargs):
    destination = Path(command[-1])
    assert command[-2] == "--out"
    assert not destination.exists()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        "minimum_available_bytes": FOUR_GIB,
        "available_physical_bytes": FOUR_GIB + 17,
        "effective_available_bytes": FOUR_GIB + 11,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
    }), encoding="utf-8")
    return SimpleNamespace(returncode=0)


def initialize_or_resume_attempt(*, admission_receipt, command_runner, **kwargs):
    admission = preflight_run(admission_receipt, command_runner=command_runner)
    witness = _issue_initial_telemetry_witness(SimpleNamespace(
        require_valid_initial_observation=lambda: None,
    ))
    return _initialize_or_resume_attempt(
        admission_receipt=admission_receipt, admission=admission,
        telemetry_witness=witness, **kwargs,
    )


def test_fresh_attempt_admits_before_root_and_resume_reuses_sealed_identity(tmp_path) -> None:
    root = tmp_path / contracts.ATTEMPT_ID
    first_receipt = tmp_path / "admit-fresh.json"
    calls: list[str] = []

    def master_source() -> bytes:
        calls.append("master")
        assert first_receipt.is_file()
        assert root.is_dir()
        assert (root / "attempt-header.json").is_file()
        return MASTER

    fresh = initialize_or_resume_attempt(
        result_root=root,
        admission_receipt=first_receipt,
        command_runner=_admit,
        master_source=master_source,
        argv=("python", "scripts/run_scdmp_mf_rs_mk_b01.py", "--run-01"),
        cwd=tmp_path,
        resume=False,
    )

    expected = contracts.build_run_manifest(MASTER)
    assert fresh.fresh is True
    assert fresh.run_manifest == expected
    assert fresh.root == root.resolve()
    assert calls == ["master"]
    assert not first_receipt.exists()
    assert (root / "admissions" / "invocation-000000.json").is_file()
    assert (root / "run-master.bin").read_bytes() == MASTER
    persisted = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    q_audit = json.loads((root / "realized-q-audit.json").read_text(encoding="utf-8"))
    assert persisted["run_manifest"] == expected.to_dict()
    assert persisted["frozen_cwd"] == str(tmp_path.resolve())
    assert persisted["frozen_argv"][-1] == "--run-01"
    assert persisted["worker_topology"] == {
        "foreground_processes": 1,
        "telemetry_threads": 1,
        "torch_intraop_threads": 1,
        "native_training_batch_width": 12,
        "native_evaluator_batch_width": 32,
        "native_twin_batch_width": 2,
    }
    assert q_audit["draw_count"] == 1
    assert q_audit["redraw_allowed"] is False
    assert {row["cell"]: row["q_pre"] for row in q_audit["q_by_cell"]} == {
        state.cell: expected.q_by_cell[index]
        for index, state in enumerate(contracts.STATE_SPECS)
    }

    with pytest.raises(AttemptError, match="resume"):
        initialize_or_resume_attempt(
            result_root=root,
            admission_receipt=tmp_path / "admit-duplicate.json",
            command_runner=_admit,
            master_source=lambda: (_ for _ in ()).throw(AssertionError("must not draw")),
            argv=("python", "runner.py", "--run-01"),
            cwd=tmp_path,
            resume=False,
        )

    resumed = initialize_or_resume_attempt(
        result_root=root,
        admission_receipt=root / "admissions" / "invocation-000001.json",
        command_runner=_admit,
        master_source=lambda: (_ for _ in ()).throw(AssertionError("resume redrew master")),
        argv=("python", "scripts/run_scdmp_mf_rs_mk_b01.py", "--run-01", "--resume"),
        cwd=tmp_path,
        resume=True,
    )
    assert resumed.fresh is False
    assert resumed.run_manifest == fresh.run_manifest
    assert (root / "run-master.bin").read_bytes() == MASTER
    assert (root / "admissions" / "invocation-000001.json").is_file()
    write_no_polarity_terminal(
        root, mode="RUN-01", stage="native-failure", error_type="RuntimeError", telemetry=None,
    )
    with pytest.raises(AttemptError, match="quarantined"):
        initialize_or_resume_attempt(
            result_root=root,
            admission_receipt=root / "admissions" / "invocation-000002.json",
            command_runner=_admit,
            master_source=lambda: (_ for _ in ()).throw(AssertionError("must not draw")),
            argv=("python", "runner.py", "--run-01", "--resume"),
            cwd=tmp_path,
            resume=True,
        )
    # This direct test helper pre-admits before calling the resume gate; the
    # scientific CLI path refuses a locked attempt before writing this slot.
    assert (root / "admissions" / "invocation-000002.json").is_file()


def test_checkpoint_round_trip_preserves_full_float32_model_and_adamw_state(tmp_path) -> None:
    run_manifest = contracts.build_run_manifest(MASTER)
    model = materialize_foundation(CounterRNG(1709))
    optimizer = ExactAdamW(tuple(model.named_parameters()))
    with torch.no_grad():
        next(model.parameters()).add_(torch.tensor(0.125, dtype=torch.float32))
        optimizer.first[0].fill_(0.25)
        optimizer.second[0].fill_(0.5)
    optimizer.step_index = 24
    path = tmp_path / "foundation-1709-update-002.json"

    write_foundation_checkpoint(
        path, model=model, optimizer=optimizer, update=2, run_manifest=run_manifest,
        training_receipt=UpdateReceipt(2, 12, 24, 48, 24, 0.25),
    )
    restored, restored_optimizer = load_foundation_checkpoint(
        path, expected_seed=1709, run_manifest=run_manifest,
    )

    assert direct_tensor_state(restored) == direct_tensor_state(model)
    assert restored_optimizer.step_index == 24
    assert all(
        torch.equal(left, right)
        for left, right in zip(restored_optimizer.first, optimizer.first)
    )
    assert all(
        torch.equal(left, right)
        for left, right in zip(restored_optimizer.second, optimizer.second)
    )
    with pytest.raises(AttemptError, match="create-only"):
        write_foundation_checkpoint(
            path, model=model, optimizer=optimizer, update=2, run_manifest=run_manifest,
            training_receipt=UpdateReceipt(2, 12, 24, 48, 24, 0.25),
        )


def test_publication_ledger_reconciles_exact_declared_work_and_source_ceiling() -> None:
    ledger = WorkLedger()
    ledger.record("foundation_training", missions=3_840, allocated_slots=3_840 * 364,
                  transitions=1_000, policy_queries=500, optimizer_steps=3_840,
                  evaluator_calls=0)
    ledger.record("fixed_learning_curves", missions=576, allocated_slots=576 * 364,
                  transitions=100, policy_queries=50, optimizer_steps=0,
                  evaluator_calls=18)
    ledger.record("final_competence", missions=256, allocated_slots=256 * 364,
                  transitions=100, policy_queries=50, optimizer_steps=0,
                  evaluator_calls=8)
    ledger.record("reachable_state_source_scans", missions=11, allocated_slots=48 * 364,
                  transitions=100, policy_queries=50, optimizer_steps=0,
                  evaluator_calls=0)
    ledger.record("development", missions=3_456, allocated_slots=3_456 * 364,
                  transitions=100, policy_queries=50, optimizer_steps=0,
                  evaluator_calls=1_728)
    ledger.record("heldout", missions=1_152, allocated_slots=1_152 * 364,
                  transitions=100, policy_queries=50, optimizer_steps=0,
                  evaluator_calls=576)

    summary = ledger.reconcile_for_publication(source_states=6, ppo_updates=320)

    assert summary["declared_total_missions"] == 9_328
    assert summary["actual_executed_missions"] == 9_291
    assert summary["source_scan_ceiling_unexecuted"] == 37
    assert summary["allocated_primitive_slots"] == 3_395_392
    assert summary["optimizer_steps"] == 3_840

    incomplete = WorkLedger()
    incomplete.record("foundation_training", missions=3_839, allocated_slots=3_840 * 364,
                      transitions=0, policy_queries=0, optimizer_steps=3_840,
                      evaluator_calls=0)
    with pytest.raises(AttemptError, match="reconciliation"):
        incomplete.reconcile_for_publication(source_states=6, ppo_updates=320)


def test_early_branch_partial_ledger_is_complete_through_its_frozen_frontier() -> None:
    ledger = WorkLedger()
    ledger.record("foundation_training", missions=3_840, allocated_slots=3_840 * 364,
                  transitions=10, policy_queries=10, optimizer_steps=3_840, evaluator_calls=0)
    ledger.record("fixed_learning_curves", missions=576, allocated_slots=576 * 364,
                  transitions=10, policy_queries=10, optimizer_steps=0, evaluator_calls=18)
    ledger.record("final_competence", missions=256, allocated_slots=256 * 364,
                  transitions=10, policy_queries=10, optimizer_steps=0, evaluator_calls=2)
    summary = ledger.reconcile_for_branch(
        branch="FOUNDATION_COMPETENCE_NOT_ESTABLISHED", source_states=0, ppo_updates=320,
    )
    assert summary["actual_executed_missions"] == 4_672
    assert summary["declared_not_executed_missions"] == 4_656
    with pytest.raises(AttemptError, match="branch-specific"):
        ledger.reconcile_for_branch(
            branch="REACHABLE_STATE_PANEL_NOT_ESTABLISHED", source_states=0, ppo_updates=320,
        )


def test_one_production_training_update_uses_real_twelve_lane_native_ppo_path() -> None:
    source = CounterRNG(1709)
    model = materialize_foundation(source)
    optimizer = ExactAdamW(tuple(model.named_parameters()))
    before = direct_tensor_state(model)

    observed = execute_training_update(model, optimizer, source, update=1)

    assert observed.receipt.update == 1
    assert observed.receipt.optimizer_step == 12
    assert observed.receipt.episodes_complete == observed.missions == 12
    assert observed.allocated_slots == 12 * 364
    assert observed.transitions > 0
    assert observed.policy_queries == observed.receipt.records
    assert direct_tensor_state(model) != before


def _passing_telemetry() -> ResourceTelemetry:
    return ResourceTelemetry(
        passed=True,
        failure_reasons=(),
        sample_count=4,
        process_tree_peak_rss_bytes=128 * 1024**2,
        scratch_high_water_bytes=1024,
        durable_high_water_bytes=2048,
        wall_seconds=2.0,
        cpu_seconds=1.5,
        cpu_utilization_fraction=0.75,
        max_process_count=1,
        max_thread_count=3,
        start_available_memory_bytes=FOUR_GIB + 10,
        end_available_memory_bytes=FOUR_GIB + 5,
        exit_status=0,
    )


def _stage_observations():
    return {
        "foundation_training": {"measured_missions": 12, "wall_seconds": 1.0},
        "foundation_evaluator": {"measured_missions": 32, "wall_seconds": 1.0},
        "source_scan": {"measured_missions": 1, "wall_seconds": 0.1},
        "development": {"measured_missions": 36, "wall_seconds": 1.0},
        "heldout": {"measured_missions": 6, "wall_seconds": 0.2},
        "checkpoint_serialize": {"measured_missions": 322, "wall_seconds": 1.0,
                                 "io_read_bytes": 10, "io_write_bytes": 20},
        "checkpoint_cold_validate": {"measured_missions": 322, "wall_seconds": 1.0,
                                     "io_read_bytes": 20, "io_write_bytes": 0},
        "checkpoint_inventory": {"measured_missions": 322, "wall_seconds": 0.2,
                                 "io_read_bytes": 1, "io_write_bytes": 0},
        "publication_preview": {"measured_missions": 1, "wall_seconds": 0.1,
                                "io_read_bytes": 0, "io_write_bytes": 5},
    }


def test_a_recon_transaction_is_create_once_and_never_publishes_science(tmp_path) -> None:
    root = tmp_path / "a-recon"
    receipt = tmp_path / "a-recon-admit.json"
    attempt = prepare_assess_attempt(
        assess_root=root,
        admission_receipt=receipt,
        command_runner=_admit,
        argv=("python", "runner.py", "--assess-run", "A/RECON"),
        cwd=tmp_path,
    )
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert attempt.root == root.resolve()
    assert manifest["assessment_id"] == assessment_module.ASSESS_ID
    assert "run-master.bin" not in {row.name for row in root.iterdir()}
    assert manifest["science_exclusions"] == [
        "RUN-01 result root", "RUN-01 master", "RUN-01 q draw",
        "RUN-01 raw returns", "RUN-01 ordered branch",
    ]

    published = finalize_assess_success(
        root, telemetry=_passing_telemetry(), counts=ASSESS_COUNTS,
        stage_observations=_stage_observations(),
    )
    value = json.loads(published.read_text(encoding="utf-8"))
    assert value["scientific_polarity"] is None
    assert value["ordered_branch"] is None
    assert value["performance_readiness"] == "REVIEW_REQUIRED"
    assert value["projection"]["formula"].endswith("+ 60.0")
    with pytest.raises(AttemptError, match="create-only"):
        finalize_assess_success(
            root, telemetry=_passing_telemetry(), counts=ASSESS_COUNTS,
            stage_observations=_stage_observations(),
        )


def test_a_assessment_rename_has_no_post_commit_cleanup(tmp_path, monkeypatch) -> None:
    root = tmp_path / "a-final-commit"
    prepare_assess_attempt(
        assess_root=root, admission_receipt=tmp_path / "a-final-admit.json",
        command_runner=_admit, argv=("python", "runner.py", "--assess-run", "A/RECON"),
        cwd=tmp_path,
    )
    committed = False
    original_unlink = Path.unlink

    def commit(staged: Path, destination: Path) -> None:
        nonlocal committed
        staged.rename(destination)
        committed = True

    def guarded_unlink(path: Path, *args, **kwargs):
        if committed:
            raise AssertionError("A/RECON cleanup ran after assessment commit")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", guarded_unlink)
    result = finalize_assess_success(
        root, telemetry=_passing_telemetry(), counts=ASSESS_COUNTS,
        stage_observations=_stage_observations(), final_committer=commit,
    )
    assert committed and result == root / "assessment.json"


def test_failure_terminal_is_exact_no_polarity_and_blocks_assess_publication(tmp_path) -> None:
    root = tmp_path / "failed"
    terminal = write_no_polarity_terminal(
        root,
        mode="RUN-01",
        stage="foundation-training",
        error_type="NativeBackendError",
        telemetry=None,
    )
    value = json.loads(terminal.read_text(encoding="utf-8"))
    assert value["status"] == "QUARANTINED_INCOMPLETE_ATTEMPT"
    assert value["scientific_polarity"] is None
    assert value["ordered_branch"] is None
    with pytest.raises(AttemptError, match="quarantined"):
        finalize_assess_success(
            root, telemetry=_passing_telemetry(), counts=ASSESS_COUNTS,
            stage_observations=_stage_observations(),
        )


@pytest.mark.parametrize("preexisting", (True, False))
def test_quarantine_write_failure_or_collision_never_masks_primary_exception(tmp_path, preexisting) -> None:
    root = tmp_path / "quarantine"
    if preexisting:
        write_no_polarity_terminal(
            root, mode="RUN-01", stage="first", error_type="ValueError", telemetry=None,
        )
    else:
        root.write_text("not-a-directory", encoding="utf-8")
    primary = RuntimeError("primary-native-failure")
    with pytest.raises(RuntimeError, match="primary-native-failure") as observed:
        raise_after_quarantine(
            root, mode="RUN-01", stage="second", original=primary, telemetry=None,
        )
    assert observed.value is primary


def test_keyboard_interrupt_is_fail_closed_no_polarity_not_resumable(tmp_path) -> None:
    root = tmp_path / "interrupted-run"
    primary = KeyboardInterrupt("operator-stop")
    with pytest.raises(KeyboardInterrupt) as observed:
        raise_after_quarantine(
            root, mode="RUN-01", stage="foundation-checkpoint-frontier",
            original=primary, telemetry=None,
        )
    assert observed.value is primary
    terminal = json.loads((root / "terminal-no-polarity.json").read_text(encoding="utf-8"))
    assert terminal["status"] == "QUARANTINED_INCOMPLETE_ATTEMPT"
    assert terminal["scientific_polarity"] is None


def test_source_identity_binds_exact_owned_diff_runtime_native_and_abi(tmp_path) -> None:
    encoded = compute_source_identity_bytes()
    value = validate_source_identity_bytes(encoded, encoded)
    assert value["assigned_base_commit"] == ASSIGNED_BASE_COMMIT
    assert tuple(value["owned_production_paths"]) == OWNED_PRODUCTION_PATHS
    assert len(value["owned_source_inventory"]) == len(OWNED_PRODUCTION_PATHS)
    assert value["git_diff_command"][:4] == ["git", "diff", "--binary", ASSIGNED_BASE_COMMIT]
    assert len(value["git_diff_sha256"]) == 64
    assert value["python"]["resolved_executable"]
    assert value["torch_version"] == str(torch.__version__)
    assert value["native_abi_identity"]["abi_version"] == 3
    assert value["native_abi_identity"]["struct_sizes"] == value["native_abi_identity"]["python_struct_sizes"]
    assert value["compiled_native_library"]["sha256"]

    gate = tmp_path / "source-identity.json"
    write_source_identity_gate(gate)
    assert validate_source_identity_gate(gate)["assigned_base_commit"] == ASSIGNED_BASE_COMMIT
    with pytest.raises(SourceIdentityError, match="create-only"):
        write_source_identity_gate(gate)


@pytest.mark.parametrize("field", ("base", "path", "python", "native", "diff", "abi"))
def test_source_identity_tamper_is_rejected_by_direct_recomputation(field) -> None:
    actual = compute_source_identity_bytes()
    value = json.loads(actual)
    changed = copy.deepcopy(value)
    if field == "base":
        changed["assigned_base_commit"] = "0" * 40
    elif field == "path":
        changed["owned_production_paths"][0] = "experiments/not-owned.py"
    elif field == "python":
        changed["python"]["resolved_executable"] += ".tampered"
    elif field == "native":
        changed["compiled_native_library"]["sha256"] = "f" * 64
    elif field == "diff":
        changed["git_diff_sha256"] = "e" * 64
    else:
        changed["native_abi_identity"]["abi_version"] = 2
    with pytest.raises(SourceIdentityError, match="differs"):
        validate_source_identity_bytes(_canonical(changed), actual)


def test_resume_source_identity_mismatch_locks_original_run_root(tmp_path) -> None:
    root = tmp_path / "source-mismatch-run" / contracts.ATTEMPT_ID
    initialize_or_resume_attempt(
        result_root=root, admission_receipt=tmp_path / "source-mismatch-admit.json",
        command_runner=_admit, master_source=lambda: MASTER,
        argv=("python", "runner.py", "--run-01"), cwd=tmp_path, resume=False,
    )
    path = root / "source-identity.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["python"]["version"] += " tampered"
    path.write_bytes(_canonical(value))
    with pytest.raises(SourceIdentityError, match="differs"):
        initialize_or_resume_attempt(
            result_root=root,
            admission_receipt=root / "admissions" / "invocation-000001.json",
            command_runner=_admit, master_source=lambda: MASTER,
            argv=("python", "runner.py", "--run-01", "--resume"),
            cwd=tmp_path, resume=True,
        )
    assert (root / "terminal-no-polarity.json").is_file()
    assert quarantine_lock_path(root).is_file()


def test_legal_run_terminal_writer_failure_leaves_independent_nonresumable_lock(
    tmp_path, monkeypatch,
) -> None:
    root = tmp_path / "legal-run" / contracts.ATTEMPT_ID
    receipt = tmp_path / "legal-admit.json"
    initialize_or_resume_attempt(
        result_root=root, admission_receipt=receipt, command_runner=_admit,
        master_source=lambda: MASTER, argv=("python", "runner.py", "--run-01"),
        cwd=tmp_path, resume=False,
    )
    primary = RuntimeError("native-primary")
    monkeypatch.setattr(
        quarantine_module, "write_no_polarity_terminal",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("terminal-write-failed")),
    )
    with pytest.raises(RuntimeError, match="native-primary") as observed:
        quarantine_module.raise_after_quarantine(
            root, mode="RUN-01", stage="native", original=primary, telemetry=None,
        )
    assert observed.value is primary
    assert quarantine_lock_path(root).is_file()
    assert not (root / "terminal-no-polarity.json").exists()
    with pytest.raises(AttemptError, match="quarantine lock"):
        initialize_or_resume_attempt(
            result_root=root,
            admission_receipt=root / "admissions" / "invocation-000001.json",
            command_runner=_admit, master_source=lambda: MASTER,
            argv=("python", "runner.py", "--run-01", "--resume"),
            cwd=tmp_path, resume=True,
        )


def test_quarantine_lock_failure_preserves_exact_primary_and_attaches_incident(tmp_path) -> None:
    blocked = tmp_path / "blocked-parent"
    blocked.write_text("file", encoding="utf-8")
    primary = RuntimeError("primary")
    with pytest.raises(RuntimeError, match="primary") as observed:
        quarantine_module.raise_after_quarantine(
            blocked / "run", mode="RUN-01", stage="init", original=primary, telemetry=None,
        )
    assert observed.value is primary
    assert isinstance(primary.quarantine_lock_error, BaseException)


@pytest.mark.parametrize(
    "mutation",
    ("late_boundary", "receipt", "hidden_state", "public_cache", "persistent_flag", "spliced_post"),
)
def test_reachable_source_resume_deep_validates_witness_without_replaying_addresses(
    tmp_path, mutation,
) -> None:
    manifest = contracts.build_run_manifest(MASTER)
    spec = contracts.STATE_SPECS[0]
    model = materialize_foundation(CounterRNG(spec.source_seed))
    policy = ImmutableBatchedFoundationPolicy(freeze_foundation_actor(model))
    twins = construct_reachable_twins(
        run_manifest=manifest, state_spec=spec, prefix_policy=policy,
    )
    checkpoint_binding = {"relative_path": "final.json", "byte_size": 1, "sha256": "a" * 64}
    value = production_module._twins_value(
        twins, manifest, checkpoint_binding=checkpoint_binding,
    )
    if mutation == "late_boundary":
        baseline = tmp_path / "twins-baseline.json"
        baseline.write_bytes(_canonical(value))
        validation_counts = {
            "resume_validation_policy_forwards": 0,
            "resume_validation_transition_proofs": 0,
        }
        restored = production_module._load_twins(
            baseline, manifest, state_spec=spec, prefix_policy=policy,
            checkpoint_binding=checkpoint_binding, validation_counts=validation_counts,
        )
        assert restored.source_snapshot_bytes == twins.source_snapshot_bytes
        assert restored.hr.state_bytes == twins.hr.state_bytes
        assert restored.source_candidate_witnesses == twins.source_candidate_witnesses
        assert validation_counts == {
            "resume_validation_policy_forwards": restored.policy_queries,
            "resume_validation_transition_proofs": restored.policy_queries,
        }
    changed = copy.deepcopy(value)
    if mutation == "late_boundary":
        changed["boundary_tick"] += spec.k
    elif mutation == "receipt":
        changed["source_scan_receipts"][-1]["renewal_steps"] += 1
    elif mutation == "hidden_state":
        direct = bytearray(base64.b64decode(changed["hr_state_b64"]))
        direct[32] ^= 1
        changed["hr_state_b64"] = base64.b64encode(direct).decode("ascii")
    elif mutation == "public_cache":
        direct = bytearray(base64.b64decode(changed["hr_public_b64"]))
        direct[-1] ^= 1
        changed["hr_public_b64"] = base64.b64encode(direct).decode("ascii")
    elif mutation == "spliced_post":
        renewal = twins.source_candidate_witnesses[0].renewals[0]
        session = NativeSession.from_state_bytes((renewal.pre_state_bytes,))
        tape = materialize_disturbance_tape(twins.source_candidate_witnesses[0].address)
        session.step(((renewal.foundation_action + 1) % 18,), (tape[renewal.renewal_index],))
        wrong = session.state_bytes()[0]
        wrong_state = NativeSession.from_state_bytes((wrong,)).states()[0]
        right_state = NativeSession.from_state_bytes((renewal.post_state_bytes,)).states()[0]
        wrong_pod = native_backend_module._NativeState.from_buffer_copy(wrong)
        right_pod = native_backend_module._NativeState.from_buffer_copy(renewal.post_state_bytes)
        assert (wrong_state.output.tick, wrong_pod.current_k, wrong_state.latent_q) == (
            right_state.output.tick, right_pod.current_k, right_state.latent_q,
        )
        changed["source_candidate_witnesses"][0]["renewals"][0]["post_state_b64"] = (
            base64.b64encode(wrong).decode("ascii")
        )
    else:
        changed["persistent_twin_bytes_equal"] = False
    path = tmp_path / f"twins-{mutation}.json"
    path.write_bytes(_canonical(changed))
    with pytest.raises(AttemptError, match="source|reachable"):
        production_module._load_twins(
            path, manifest, state_spec=spec, prefix_policy=policy,
            checkpoint_binding=checkpoint_binding,
        )


def test_a_recon_source_gate_failure_after_admission_is_isolated_and_locked(
    tmp_path, monkeypatch,
) -> None:
    root = tmp_path / "a-source-failure"
    receipt = tmp_path / "a-source-admit.json"
    monkeypatch.setattr(
        assessment_module, "write_source_identity_gate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(SourceIdentityError("source-measurement")),
    )
    with pytest.raises(SourceIdentityError, match="source-measurement"):
        assessment_module.run_assess(
            assess_root=root, admission_receipt=receipt, command_runner=_admit,
            argv=("python", "runner.py", "--assess-run", "A/RECON"), cwd=tmp_path,
        )
    isolated = tmp_path / ".a-source-failure.initialization-failure"
    assert not root.exists()
    assert (isolated / "terminal-no-polarity.json").is_file()
    assert quarantine_lock_path(isolated).is_file()


def test_a_recon_staging_failure_is_locked_without_becoming_result_root(tmp_path, monkeypatch) -> None:
    root = tmp_path / "a-staging-failure"
    receipt = tmp_path / "a-staging-admit.json"
    monkeypatch.setattr(
        assessment_module, "atomic_create_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("staging-write")),
    )
    with pytest.raises(OSError, match="staging-write"):
        assessment_module.run_assess(
            assess_root=root, admission_receipt=receipt, command_runner=_admit,
            argv=("python", "runner.py", "--assess-run", "A/RECON"), cwd=tmp_path,
        )
    staging = tmp_path / ".a-staging-failure.initializing"
    assert not root.exists()
    assert (staging / "terminal-no-polarity.json").is_file()
    assert quarantine_lock_path(staging).is_file()


def test_a_recon_stale_scratch_and_monitor_ctor_failures_lock_legal_roots(tmp_path) -> None:
    for suffix, monitor_factory in (
        ("scratch", None),
        ("monitor", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("monitor-ctor"))),
    ):
        root = tmp_path / f"a-{suffix}"
        receipt = tmp_path / f"a-{suffix}-admit.json"
        scratch = tmp_path / f".a-{suffix}.scratch"
        if suffix == "scratch":
            scratch.mkdir()
        kwargs = {} if monitor_factory is None else {"monitor_factory": monitor_factory}
        expected = "already exists" if suffix == "scratch" else "monitor-ctor"
        with pytest.raises((FileExistsError, RuntimeError), match=expected):
            assessment_module.run_assess(
                assess_root=root, admission_receipt=receipt, command_runner=_admit,
                argv=("python", "runner.py", "--assess-run", "A/RECON"), cwd=tmp_path,
                **kwargs,
            )
        assert (root / "terminal-no-polarity.json").is_file()
        assert quarantine_lock_path(root).is_file()


def test_run01_resume_stale_scratch_and_monitor_ctor_failures_lock_original_root(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(runner_module, "validate_performance_readiness_receipt", lambda _path: {})
    for suffix, monitor_factory in (
        ("scratch", None),
        ("monitor", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("monitor-ctor"))),
    ):
        root = tmp_path / f"run-{suffix}" / contracts.ATTEMPT_ID
        initialize_or_resume_attempt(
            result_root=root, admission_receipt=tmp_path / f"run-{suffix}-admit.json",
            command_runner=_admit, master_source=lambda: MASTER,
            argv=("python", "runner.py", "--run-01"), cwd=tmp_path, resume=False,
        )
        receipt = root / "admissions" / "invocation-000001.json"
        scratch = root.with_name(f".{root.name}.scratch-{receipt.stem}")
        if suffix == "scratch":
            scratch.mkdir()
        kwargs = {} if monitor_factory is None else {"monitor_factory": monitor_factory}
        expected = "already exists" if suffix == "scratch" else "monitor-ctor"
        with pytest.raises((AttemptError, RuntimeError), match=expected):
            run_result(
                result_root=root, admission_receipt=receipt, confirmation=RUN_CONFIRMATION,
                resume=True, argv=("python", "runner.py", "--run-01", "--resume"),
                cwd=tmp_path, command_runner=_admit,
                performance_readiness=tmp_path / "ready.json", **kwargs,
            )
        assert (root / "terminal-no-polarity.json").is_file()
        assert quarantine_lock_path(root).is_file()


def test_duplicate_active_invocation_rejects_before_admission_without_polluting_root(tmp_path) -> None:
    root = tmp_path / "active-run"
    root.mkdir()
    first = ActiveInvocationGate(root, mode="RUN-01")
    second = ActiveInvocationGate(root, mode="RUN-01")
    first.acquire()
    with pytest.raises(ActiveGateError, match="already owns"):
        second.acquire()
    assert not (root / "terminal-no-polarity.json").exists()
    assert not quarantine_lock_path(root).exists()
    first.assert_owner()
    first.release()


def test_os_lease_releases_after_hard_process_death(tmp_path) -> None:
    root = tmp_path / "hard-kill-run"
    code = (
        "import sys,time;"
        "from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.active_gate "
        "import ActiveInvocationGate;"
        "g=ActiveInvocationGate(sys.argv[1],mode='RUN-01');g.acquire();"
        "print('READY',flush=True);time.sleep(60)"
    )
    child = subprocess.Popen(
        [sys.executable, "-c", code, str(root)], cwd=Path.cwd(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        assert child.stdout is not None and child.stdout.readline().strip() == "READY"
        contender = ActiveInvocationGate(root, mode="RUN-01")
        with pytest.raises(ActiveGateError, match="already owns"):
            contender.acquire()
        child.kill()
        child.wait(timeout=10)
        recovered = ActiveInvocationGate(root, mode="RUN-01")
        recovered.acquire()
        recovered.release()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


def test_stale_lease_without_complete_frontier_is_not_a_resume(tmp_path) -> None:
    root = tmp_path / "stale-no-frontier"
    root.mkdir()
    (root / "source-identity.json").write_bytes(b"identity\n")
    resumed = SimpleNamespace(
        root=root, run_manifest=contracts.build_run_manifest(MASTER), invocation_index=1,
    )
    with pytest.raises(AttemptError, match="lacks a sealed frontier"):
        FrontierController(resumed, stop_after=None)


def _commit_first_frontier(tmp_path, monkeypatch, *, final_committer=None):
    root = tmp_path / "frontier-run"
    root.mkdir()
    (root / "source-identity.json").write_bytes(b"sealed-source-identity\n")
    manifest = contracts.build_run_manifest(MASTER)
    for directory in ("admissions", "invocations"):
        path = root / directory
        path.mkdir()
        (path / "invocation-000000.json").write_bytes(b"{}\n")
    checkpoint = root / "foundations" / "1709" / "checkpoints" / "update-001.json"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(_canonical({"run_binding": manifest.to_dict(), "seed": 1709, "update": 1}))
    fresh = SimpleNamespace(root=root, run_manifest=manifest, invocation_index=0)
    monkeypatch.setattr(
        frontier_module, "compute_source_identity_bytes", lambda: b"sealed-source-identity\n",
    )
    monkeypatch.setattr(
        frontier_module, "validate_source_identity_bytes", lambda _persisted, _current: {},
    )
    sealed_rows = tuple({"test": index} for index in range(6))
    monkeypatch.setattr(runner_module, "validate_sealed_identity", lambda _attempt: sealed_rows)
    monkeypatch.setattr(frontier_module, "validate_sealed_identity", lambda _attempt: sealed_rows)
    stopped = TechnicalSliceStop(TECHNICAL_FRONTIER_IDS[0], 0)
    plan = runner_module._build_technical_slice_tail_plan(
        attempt=fresh, stopped=stopped, telemetry=_passing_telemetry(),
        prepublication_durable_bytes=runner_module._tree_bytes(root),
    )
    scratch = tmp_path / "frontier-scratch"
    scratch.mkdir()
    gate = ActiveInvocationGate(root, mode="RUN-01")
    gate.acquire()
    kwargs = {} if final_committer is None else {"final_committer": final_committer}
    result = runner_module._stage_and_commit_technical_slice_tail(
        plan, attempt=fresh, scratch=scratch, active_gate=gate, **kwargs,
    )
    for directory in ("admissions", "invocations"):
        (root / directory / "invocation-000001.json").write_bytes(b"{}\n")
    resumed = SimpleNamespace(root=root, run_manifest=manifest, invocation_index=1)
    return result, resumed


def test_result_blind_frontier_is_preregistered_ordered_and_resume_contiguous(
    tmp_path, monkeypatch,
) -> None:
    assert TECHNICAL_FRONTIER_IDS[0] == "training-1709-update-001"
    assert TECHNICAL_FRONTIER_IDS[-1] == "development-2903-k13-late"
    assert not any("heldout" in row for row in TECHNICAL_FRONTIER_IDS)
    result, resumed = _commit_first_frontier(tmp_path, monkeypatch)
    assert result.name == "technical-frontier.json"
    sealed = load_technical_frontier(resumed)
    assert sealed["scientific_polarity"] is None
    assert sealed["ordered_branch"] is None
    next_controller = FrontierController(resumed, stop_after=None)
    next_controller.unit(TECHNICAL_FRONTIER_IDS[0], created=False)
    next_controller.unit(TECHNICAL_FRONTIER_IDS[1], created=True)
    with pytest.raises(AttemptError, match="order"):
        next_controller.unit(TECHNICAL_FRONTIER_IDS[3], created=True)


@pytest.mark.parametrize("mutation", ("frontier_id", "extra_key", "resource_path", "resource_schema", "artifact"))
def test_frontier_tamper_and_resource_artifact_mismatch_are_rejected(
    tmp_path, monkeypatch, mutation,
) -> None:
    path, resumed = _commit_first_frontier(tmp_path, monkeypatch)
    root = resumed.root
    value = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "frontier_id":
        value["frontier_id"] = TECHNICAL_FRONTIER_IDS[1]
        path.write_bytes(_canonical(value))
    elif mutation == "extra_key":
        value["extra"] = 1
        path.write_bytes(_canonical(value))
    elif mutation == "resource_path":
        value["resource_telemetry_file"] = "resources/other.json"
        path.write_bytes(_canonical(value))
    elif mutation == "resource_schema":
        resource = root / "resources" / "invocation-000000.json"
        row = json.loads(resource.read_text(encoding="utf-8"))
        row["schema"] = "WRONG"
        resource.write_bytes(_canonical(row))
    else:
        (root / "foundations" / "1709" / "checkpoints" / "update-001.json").unlink()
    with pytest.raises(AttemptError, match="frontier|artifact|resource"):
        load_technical_frontier(resumed)


def test_technical_slice_tail_overcap_is_refused_before_staging(tmp_path, monkeypatch) -> None:
    root = tmp_path / "slice-overcap"
    root.mkdir()
    (root / "source-identity.json").write_bytes(b"identity\n")
    attempt = SimpleNamespace(
        root=root, run_manifest=contracts.build_run_manifest(MASTER), invocation_index=0,
    )
    monkeypatch.setattr(runner_module, "validate_sealed_identity", lambda _attempt: ())
    with pytest.raises(AttemptError, match="exceeds 256 MiB"):
        runner_module._build_technical_slice_tail_plan(
            attempt=attempt, stopped=TechnicalSliceStop(TECHNICAL_FRONTIER_IDS[0], 0),
            telemetry=_passing_telemetry(), prepublication_durable_bytes=256 * 1024**2,
        )


def test_technical_frontier_rename_has_no_post_commit_cleanup_or_release(
    tmp_path, monkeypatch,
) -> None:
    committed = False
    original_unlink = Path.unlink
    original_release = ActiveInvocationGate.release

    def commit(staged: Path, destination: Path) -> None:
        nonlocal committed
        staged.rename(destination)
        committed = True

    def guarded_unlink(path: Path, *args, **kwargs):
        if committed:
            raise AssertionError("frontier cleanup ran after commit")
        return original_unlink(path, *args, **kwargs)

    def guarded_release(gate):
        if committed:
            raise AssertionError("frontier lease released after commit")
        return original_release(gate)

    monkeypatch.setattr(Path, "unlink", guarded_unlink)
    monkeypatch.setattr(ActiveInvocationGate, "release", guarded_release)
    result, _resumed = _commit_first_frontier(
        tmp_path, monkeypatch, final_committer=commit,
    )
    assert committed and result.name == "technical-frontier.json"


def test_publication_tail_overcap_and_direct_mismatch_fail_before_polarity(tmp_path) -> None:
    with pytest.raises(AttemptError, match="exceeds 256 MiB"):
        runner_module._validate_tail_capacity(256 * 1024**2, 1)

    root = tmp_path / "tail-root"
    scratch = tmp_path / "tail-scratch"
    root.mkdir()
    scratch.mkdir()
    payloads = (
        ("resources/invocation-000000.json", b"resource"),
        ("work-ledger.json", b"ledger"),
        ("ordered-branch.json", b"branch-prepared-no-polarity"),
        ("published-result.json", b"published-polarity"),
    )
    total = sum(len(value) for _name, value in payloads)
    plan = runner_module.PublicationTailPlan(
        payloads, 0, total, total, total, 11, 17, (),
    )

    def corrupt(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload + b"corrupt")

    with pytest.raises(AttemptError, match="mismatch"):
        runner_module._stage_and_publish_tail(
            plan, attempt=SimpleNamespace(root=root), scratch=scratch, writer=corrupt,
        )
    assert not (root / "published-result.json").exists()
    assert plan.preview_io_read_bytes == 11
    assert plan.preview_io_write_bytes == 17


def test_published_result_create_is_irreversible_last_effect(tmp_path, monkeypatch) -> None:
    root = tmp_path / "commit-root"
    scratch = tmp_path / "commit-scratch"
    root.mkdir()
    scratch.mkdir()
    payloads = (
        ("resources/invocation-000000.json", b"resource"),
        ("work-ledger.json", b"ledger"),
        ("ordered-branch.json", b"prepared"),
        ("published-result.json", b"commit"),
    )
    total = sum(len(value) for _name, value in payloads)
    plan = runner_module.PublicationTailPlan(payloads, 0, total, total, total, 0, 0, ())
    committed = False
    original_tree_bytes = runner_module._tree_bytes
    original_unlink = Path.unlink

    def guarded_tree_bytes(path: Path) -> int:
        if committed:
            raise AssertionError("post-commit durable check executed")
        return original_tree_bytes(path)

    def writer(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(path)
        path.write_bytes(payload)

    def commit(staged: Path, published: Path) -> None:
        nonlocal committed
        staged.rename(published)
        committed = True

    def guarded_unlink(path: Path, *args, **kwargs):
        if committed:
            raise AssertionError("post-commit temporary cleanup executed")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(runner_module, "_tree_bytes", guarded_tree_bytes)
    monkeypatch.setattr(runner_module, "validate_sealed_identity", lambda _attempt: ())
    monkeypatch.setattr(Path, "unlink", guarded_unlink)
    result = runner_module._stage_and_publish_tail(
        plan, attempt=SimpleNamespace(root=root), scratch=scratch,
        writer=writer, final_committer=commit,
    )
    assert result == root / "published-result.json"
    assert committed
