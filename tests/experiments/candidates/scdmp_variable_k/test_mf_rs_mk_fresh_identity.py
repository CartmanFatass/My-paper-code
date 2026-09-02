from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import os
import subprocess
import sys

import pytest

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    assessment, contracts, orchestration, runner,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    frontier as frontier_module,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.preflight import (
    PreflightReceipt,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.rng import (
    heldout_tape_address,
)


MASTER = b"scdmp-b01-test-master-32-bytes!!"
FOUR_GIB = 4 * 1024**3


def _admission(path: Path) -> PreflightReceipt:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "minimum_available_bytes": FOUR_GIB,
        "available_physical_bytes": FOUR_GIB + 1,
        "effective_available_bytes": FOUR_GIB + 2,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
    }), encoding="utf-8")
    return PreflightReceipt(path.resolve(), FOUR_GIB + 1, FOUR_GIB + 2, True)


def _telemetry_witness():
    return orchestration._issue_initial_telemetry_witness(type("Monitor", (), {
        "require_valid_initial_observation": lambda self: None,
    })())


def test_canonical_replacement_identities_q_address_and_expansion_binding() -> None:
    assert contracts.STUDY_ID == "SCDMP-MF-RS-MK-ORDER-VALUE-B01"
    assert contracts.QUARANTINED_NAMED_RUN_ID == f"{contracts.STUDY_ID}-RUN-01"
    assert contracts.NAMED_RUN_ID == f"{contracts.STUDY_ID}-RUN-01-REPLACEMENT-01"
    assert contracts.ATTEMPT_ID == f"{contracts.NAMED_RUN_ID}-ATTEMPT-01"
    assert contracts.Q_COUNTER_ADDRESS == (
        contracts.STUDY_ID, "RUN-01-REPLACEMENT-01", "PRE_EVENT_Q_PATTERN", 0,
    )
    assert contracts.Q_PATTERNS == (
        (0, 0, 1, 1, 1, 0), (0, 1, 1, 1, 0, 0),
        (1, 0, 0, 0, 1, 1), (1, 1, 0, 0, 0, 1),
    )
    manifest = contracts.Manifest()
    manifest.validate()
    value = manifest.to_dict()
    assert value["named_run_id"] == contracts.NAMED_RUN_ID
    assert value["attempt_id"] == contracts.ATTEMPT_ID
    assert value["expansion_run_02a_id"] == f"{contracts.STUDY_ID}-RUN-02A"
    assert value["expansion_run_02b_id"] == f"{contracts.STUDY_ID}-RUN-02B"
    assert value["expansion_base_candidate"] == contracts.NAMED_RUN_ID
    assert value["expansion_binding_rule"] == (
        "first_valid_base_run_reuse_state_panel_and_q_without_redraw"
    )
    with pytest.raises(contracts.ContractError):
        replace(manifest, named_run_id=contracts.QUARANTINED_NAMED_RUN_ID).validate()


def test_quarantined_coordinate_is_refused_before_resolve_or_content_probe(
    tmp_path, monkeypatch,
) -> None:
    forbidden = tmp_path / contracts.QUARANTINED_NAMED_RUN_ID

    def forbidden_resolve(*_args, **_kwargs):
        raise AssertionError("filesystem resolve must not run for a forbidden identity")

    monkeypatch.setattr(Path, "resolve", forbidden_resolve)
    with pytest.raises(orchestration.AttemptError, match="canonical evidence attempt"):
        orchestration.canonical_result_root(forbidden)


def _directory_symlink_or_skip(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except OSError:
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True, text=True,
        )
        if completed.returncode != 0:
            pytest.skip("directory symlinks and junctions are unavailable")


def test_canonical_leaf_link_to_synthetic_quarantined_name_is_refused(tmp_path) -> None:
    synthetic = tmp_path / contracts.QUARANTINED_NAMED_RUN_ID
    synthetic.mkdir()
    leaf = tmp_path / contracts.ATTEMPT_ID
    _directory_symlink_or_skip(leaf, synthetic)
    with pytest.raises(orchestration.AttemptError, match="symlink|junction|reparse"):
        orchestration.canonical_result_root(leaf)


def test_canonical_parent_link_to_synthetic_quarantined_name_is_refused(tmp_path) -> None:
    synthetic = tmp_path / contracts.QUARANTINED_NAMED_RUN_ID
    synthetic.mkdir()
    alias = tmp_path / "aliased-parent"
    _directory_symlink_or_skip(alias, synthetic)
    with pytest.raises(orchestration.AttemptError, match="symlink|junction|reparse"):
        orchestration.canonical_result_root(alias / contracts.ATTEMPT_ID)


def test_atomic_handle_reader_never_calls_path_read(tmp_path, monkeypatch) -> None:
    path = tmp_path / "direct.bin"
    path.write_bytes(b"direct-handle-bytes")
    monkeypatch.setattr(
        Path, "read_bytes", lambda _self: (_ for _ in ()).throw(AssertionError("path read raced")),
    )
    monkeypatch.setattr(
        Path, "read_text", lambda _self, **_kwargs: (_ for _ in ()).throw(AssertionError("path read raced")),
    )
    assert orchestration._read_regular_bytes(path, label="race test") == b"direct-handle-bytes"


def test_fresh_root_header_master_q_and_resume_are_one_sealed_identity(
    tmp_path, monkeypatch,
) -> None:
    root = tmp_path / contracts.ATTEMPT_ID
    first_receipt = tmp_path / "fresh-admission.json"
    first_admission = _admission(first_receipt)
    calls: list[str] = []

    def write_gate(path: Path) -> None:
        Path(path).write_bytes(b"source-gate")

    def validate_gate(path: Path) -> None:
        assert Path(path).read_bytes() == b"source-gate"

    monkeypatch.setattr(orchestration, "write_source_identity_gate", write_gate)
    monkeypatch.setattr(orchestration, "compute_source_identity_bytes", lambda: b"source-gate")
    monkeypatch.setattr(
        orchestration, "validate_source_identity_bytes",
        lambda persisted, current: validate_gate(root / "source-identity.json")
        if persisted == current else (_ for _ in ()).throw(orchestration.AttemptError("source gate differs")),
    )

    def master_source() -> bytes:
        calls.append("master")
        assert root.is_dir()
        header = json.loads((root / "attempt-header.json").read_text(encoding="utf-8"))
        assert header["named_run_id"] == contracts.NAMED_RUN_ID
        assert header["attempt_id"] == contracts.ATTEMPT_ID
        assert (root / "source-identity.json").read_bytes() == b"source-gate"
        assert not (root / "run-master.bin").exists()
        assert not (root / "manifest.json").exists()
        return MASTER

    fresh = orchestration._initialize_or_resume_attempt(
        result_root=root, admission_receipt=first_receipt, admission=first_admission,
        master_source=master_source,
        argv=("python", "runner.py", "--run-01"), cwd=tmp_path, resume=False,
        telemetry_witness=_telemetry_witness(),
    )
    q_audit = json.loads((root / "realized-q-audit.json").read_text(encoding="utf-8"))
    persisted = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert calls == ["master"]
    assert q_audit["counter_address"] == list(contracts.Q_COUNTER_ADDRESS)
    assert q_audit["draw_count"] == 1 and q_audit["redraw_allowed"] is False
    assert persisted["study_id"] == contracts.STUDY_ID
    assert persisted["named_run_id"] == contracts.NAMED_RUN_ID
    assert persisted["attempt_id"] == contracts.ATTEMPT_ID

    next_receipt = root / "admissions" / "invocation-000001.json"
    next_admission = _admission(next_receipt)
    resumed = orchestration._initialize_or_resume_attempt(
        result_root=root, admission_receipt=next_receipt, admission=next_admission,
        master_source=lambda: (_ for _ in ()).throw(AssertionError("resume redrew master")),
        argv=("python", "runner.py", "--run-01", "--resume"), cwd=tmp_path, resume=True,
        telemetry_witness=_telemetry_witness(),
    )
    assert resumed.fresh is False
    assert resumed.root == fresh.root
    assert resumed.run_manifest == fresh.run_manifest
    assert (root / "run-master.bin").read_bytes() == MASTER

    duplicate_receipt = tmp_path / "duplicate-admission.json"
    with pytest.raises(orchestration.AttemptError, match="resume"):
        orchestration._initialize_or_resume_attempt(
            result_root=root, admission_receipt=duplicate_receipt,
            admission=_admission(duplicate_receipt), master_source=lambda: MASTER,
            argv=("python", "runner.py", "--run-01"), cwd=tmp_path, resume=False,
            telemetry_witness=_telemetry_witness(),
        )


def test_heldout_token_and_cli_confirmation_derive_from_replacement_identity(tmp_path) -> None:
    assert contracts.HELDOUT_NAMESPACE_TOKEN.endswith("/RUN-01-REPLACEMENT-01")
    address = heldout_tape_address(contracts.HELDOUT_NAMESPACE_TOKEN, "k7-early", 0)
    assert address.tape_id == f"{contracts.HELDOUT_NAMESPACE_TOKEN}/k7-early/0"
    assert runner.RUN_CONFIRMATION == contracts.NAMED_RUN_ID
    assert assessment.ASSESS_ID == "SCDMP-MF-RS-MK-ORDER-VALUE-B01-A-R2"
    assert assessment.ASSESS_SCHEMA == "SCDMP_MF_RS_MK_B01_A_R2_V1"
    completed = subprocess.run(
        [
            sys.executable, "scripts/run_scdmp_mf_rs_mk_b01.py", "--run-01",
            "--receipt", str(tmp_path / "admit.json"),
            "--result-root", str(tmp_path / contracts.ATTEMPT_ID),
            "--confirm-run-id", contracts.QUARANTINED_NAMED_RUN_ID,
        ],
        cwd=Path.cwd(), capture_output=True, text=True,
    )
    assert completed.returncode == 2
    assert f"--confirm-run-id {contracts.NAMED_RUN_ID}" in completed.stderr


def test_runner_orders_admission_initial_telemetry_before_attempt_access(
    tmp_path, monkeypatch,
) -> None:
    root = tmp_path / contracts.ATTEMPT_ID
    receipt = tmp_path / "admission.json"
    events: list[str] = []

    monkeypatch.setattr(runner, "validate_performance_readiness_receipt", lambda _path: {})

    def admit(path, *, command_runner):
        del command_runner
        events.append("admission")
        return _admission(Path(path))

    monkeypatch.setattr(runner, "preflight_run", admit)

    class Monitor:
        def __init__(self, **kwargs):
            assert kwargs["autostart"] is False
            events.append("monitor-constructed")

        def sample_now(self):
            events.append("initial-sample")

        def require_valid_initial_observation(self):
            events.append("initial-valid")

        def start(self):
            events.append("monitor-started")

        def stop(self):
            events.append("monitor-stopped")

        def finalize(self, *, exit_status):
            assert exit_status == 1
            events.append("monitor-finalized")
            return object()

    def stop_at_attempt(**kwargs):
        assert kwargs["admission"].passed
        assert kwargs["telemetry_witness"].nonce is not None
        events.append("attempt-access")
        raise RuntimeError("stop-before-root")

    monkeypatch.setattr(runner, "_initialize_or_resume_attempt", stop_at_attempt)
    with pytest.raises(RuntimeError, match="stop-before-root"):
        runner.run_result(
            result_root=root, admission_receipt=receipt,
            confirmation=contracts.NAMED_RUN_ID, argv=("python", "runner.py", "--run-01"),
            cwd=tmp_path, command_runner=lambda *_a, **_k: None,
            monitor_factory=Monitor, performance_readiness=tmp_path / "ready.json",
        )
    assert events[:6] == [
        "admission", "monitor-constructed", "initial-sample", "initial-valid",
        "monitor-started", "attempt-access",
    ]
    assert not root.exists()


def test_scientific_size_source_allows_only_precreation_zero(tmp_path) -> None:
    scratch = tmp_path / "scratch"
    durable = tmp_path / contracts.ATTEMPT_ID
    scratch.mkdir()
    measure = runner._new_scientific_size_source()
    assert measure(scratch, durable) == (0, 0)
    durable.mkdir()
    (durable / "header").write_bytes(b"x")
    assert measure(scratch, durable) == (0, 1)
    (durable / "header").unlink()
    durable.rmdir()
    with pytest.raises(OSError, match="disappeared"):
        measure(scratch, durable)


def _make_sealed_attempt(tmp_path, monkeypatch):
    root = tmp_path / contracts.ATTEMPT_ID
    receipt = tmp_path / "admission.json"
    admission = _admission(receipt)

    def write_gate(path: Path) -> None:
        Path(path).write_bytes(b"source-gate")

    def validate_gate(path: Path) -> None:
        if Path(path).read_bytes() != b"source-gate":
            raise orchestration.AttemptError("source gate differs")

    monkeypatch.setattr(orchestration, "write_source_identity_gate", write_gate)
    monkeypatch.setattr(orchestration, "compute_source_identity_bytes", lambda: b"source-gate")
    monkeypatch.setattr(
        orchestration, "validate_source_identity_bytes",
        lambda persisted, current: validate_gate(root / "source-identity.json")
        if persisted == current else (_ for _ in ()).throw(orchestration.AttemptError("source gate differs")),
    )
    attempt = orchestration._initialize_or_resume_attempt(
        result_root=root, admission_receipt=receipt, admission=admission,
        master_source=lambda: MASTER, argv=("python", "runner.py", "--run-01"),
        cwd=tmp_path, resume=False, telemetry_witness=_telemetry_witness(),
    )
    return attempt


def _synthetic_quarantine_target(tmp_path: Path, name: str) -> Path:
    target = tmp_path / "synthetic-targets" / contracts.QUARANTINED_NAMED_RUN_ID / name
    target.mkdir(parents=True)
    (target / "sentinel.txt").write_text("must-not-read", encoding="utf-8")
    return target


def test_linked_run_master_synthetic_quarantine_target_is_never_read(tmp_path, monkeypatch) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    master = attempt.root / "run-master.bin"
    master.unlink()
    _directory_symlink_or_skip(master, _synthetic_quarantine_target(tmp_path, "master"))
    monkeypatch.setattr(
        orchestration, "_read_fd_all",
        lambda _descriptor: (_ for _ in ()).throw(AssertionError("linked target content reached")),
    )
    with pytest.raises(orchestration.AttemptError, match="reparse|directory|regular|unavailable"):
        orchestration.validate_sealed_identity(attempt)


def test_linked_prior_resource_synthetic_quarantine_target_is_never_read(tmp_path, monkeypatch) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    resources = attempt.root / "resources"
    _directory_symlink_or_skip(resources, _synthetic_quarantine_target(tmp_path, "resources"))
    monkeypatch.setattr(
        orchestration, "_read_fd_all",
        lambda _descriptor: (_ for _ in ()).throw(AssertionError("linked target content reached")),
    )
    with pytest.raises(orchestration.AttemptError, match="reparse|symlink|junction"):
        runner._prior_telemetry(attempt)


def test_linked_frontier_synthetic_quarantine_target_is_never_read(tmp_path, monkeypatch) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    frontier = attempt.root / "technical-frontier.json"
    _directory_symlink_or_skip(frontier, _synthetic_quarantine_target(tmp_path, "frontier"))
    monkeypatch.setattr(
        orchestration, "_read_fd_all",
        lambda _descriptor: (_ for _ in ()).throw(AssertionError("linked target content reached")),
    )
    with pytest.raises(orchestration.AttemptError, match="reparse|directory|regular|unavailable"):
        frontier_module.load_technical_frontier(attempt)


def test_linked_current_tail_resource_target_is_never_read(tmp_path, monkeypatch) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    resources = attempt.root / "resources"
    resources.mkdir()
    linked = resources / "invocation-000000.json"
    _directory_symlink_or_skip(linked, _synthetic_quarantine_target(tmp_path, "tail-resource"))
    monkeypatch.setattr(
        orchestration, "_read_fd_all",
        lambda _descriptor: (_ for _ in ()).throw(AssertionError("linked target content reached")),
    )
    payloads = (
        ("resources/invocation-000000.json", b"resource"),
        ("work-ledger.json", b"ledger"),
        ("ordered-branch.json", b"branch"),
        ("published-result.json", b"published"),
    )
    plan = runner.PublicationTailPlan(
        payloads, 0, sum(len(row[1]) for row in payloads),
        sum(len(row[1]) for row in payloads), sum(len(row[1]) for row in payloads),
        0, 0, (),
    )
    scratch = tmp_path / "linked-tail-scratch"
    scratch.mkdir()
    with pytest.raises(orchestration.AttemptError, match="symlink|junction|reparse|nonregular"):
        runner._stage_and_publish_tail(plan, attempt=attempt, scratch=scratch)
    assert not (attempt.root / "published-result.json").exists()


def _assert_final_commit_refused(attempt, tmp_path, expected_inventory) -> None:
    payloads = (
        ("resources/invocation-000000.json", b"resource"),
        ("work-ledger.json", b"ledger"),
        ("ordered-branch.json", b"branch"),
        ("published-result.json", b"published"),
    )
    prepublication = runner._tree_bytes(attempt.root)
    exact = sum(len(payload) for _name, payload in payloads)
    plan = runner.PublicationTailPlan(
        payloads, prepublication, exact, exact, prepublication + exact, 0, 0,
        expected_inventory,
    )
    scratch = tmp_path / "tail-scratch"
    scratch.mkdir()
    with pytest.raises((orchestration.AttemptError, json.JSONDecodeError, UnicodeError)):
        runner._stage_and_publish_tail(plan, attempt=attempt, scratch=scratch)
    assert not (attempt.root / "published-result.json").exists()


@pytest.mark.parametrize(
    "relative",
    (
        "attempt-header.json", "manifest.json", "run-master.bin",
        "realized-q-audit.json", "source-identity.json",
    ),
)
@pytest.mark.parametrize("mutation", ("delete", "tamper"))
def test_every_sealed_identity_artifact_blocks_final_commit_when_changed(
    tmp_path, monkeypatch, relative, mutation,
) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    expected_inventory = orchestration.validate_sealed_identity(attempt)
    path = attempt.root / relative
    if mutation == "delete":
        path.unlink()
    else:
        direct = path.read_bytes()
        path.write_bytes((b"x" * len(direct)) if relative == "run-master.bin" else direct + b"x")
    _assert_final_commit_refused(attempt, tmp_path, expected_inventory)


@pytest.mark.parametrize("mutation", ("missing", "sparse", "extra", "field"))
def test_resume_history_corruption_blocks_final_commit(tmp_path, monkeypatch, mutation) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    expected_inventory = orchestration.validate_sealed_identity(attempt)
    admission = attempt.root / "admissions" / "invocation-000000.json"
    invocation = attempt.root / "invocations" / "invocation-000000.json"
    if mutation == "missing":
        admission.unlink()
    elif mutation == "sparse":
        invocation.rename(invocation.with_name("invocation-000001.json"))
    elif mutation == "extra":
        invocation.with_name("invocation-000001.json").write_bytes(invocation.read_bytes())
    else:
        value = json.loads(invocation.read_text(encoding="utf-8"))
        value["attempt_id"] = contracts.QUARANTINED_NAMED_RUN_ID
        invocation.write_bytes((json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ) + "\n").encode())
    _assert_final_commit_refused(attempt, tmp_path, expected_inventory)


def test_structurally_valid_history_hash_change_after_plan_blocks_commit(tmp_path, monkeypatch) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    next_receipt = attempt.root / "admissions" / "invocation-000001.json"
    attempt = orchestration._initialize_or_resume_attempt(
        result_root=attempt.root, admission_receipt=next_receipt,
        admission=_admission(next_receipt),
        master_source=lambda: (_ for _ in ()).throw(AssertionError("resume redrew master")),
        argv=("python", "runner.py", "--run-01", "--resume"), cwd=tmp_path, resume=True,
        telemetry_witness=_telemetry_witness(),
    )
    expected_inventory = orchestration.validate_sealed_identity(attempt)
    payloads = (
        ("resources/invocation-000000.json", b"resource"),
        ("work-ledger.json", b"ledger"),
        ("ordered-branch.json", b"branch"),
        ("published-result.json", b"published"),
    )
    prepublication = runner._tree_bytes(attempt.root)
    exact = sum(len(payload) for _name, payload in payloads)
    plan = runner.PublicationTailPlan(
        payloads, prepublication, exact, exact, prepublication + exact, 0, 0,
        expected_inventory,
    )
    invocation = attempt.root / "invocations" / "invocation-000001.json"
    value = json.loads(invocation.read_text(encoding="utf-8"))
    value["exact_argv"][0] = "pyth0n"
    changed = (json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ) + "\n").encode()
    assert len(changed) == invocation.stat().st_size
    invocation.write_bytes(changed)
    scratch = tmp_path / "post-plan-tail-scratch"
    scratch.mkdir()
    with pytest.raises(orchestration.AttemptError, match="immutable attempt baseline|changed after publication"):
        runner._stage_and_publish_tail(plan, attempt=attempt, scratch=scratch)
    assert not (attempt.root / "published-result.json").exists()


def test_history_argv_mutation_immediately_after_sealing_blocks_technical_builder(
    tmp_path, monkeypatch,
) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    assert attempt.sealed_identity_baseline
    invocation = attempt.root / "invocations" / "invocation-000000.json"
    value = json.loads(invocation.read_text(encoding="utf-8"))
    value["exact_argv"][0] = "pyth0n"
    invocation.write_bytes((json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ) + "\n").encode())
    with pytest.raises(orchestration.AttemptError):
        runner._build_technical_slice_tail_plan(
            attempt=attempt,
            stopped=frontier_module.TechnicalSliceStop(
                frontier_module.TECHNICAL_FRONTIER_IDS[0], 0,
            ),
            telemetry=runner.ResourceTelemetry(
                True, (), 1, 1, 1, 1, 1.0, 1.0, 1.0, 1, 1,
                FOUR_GIB, FOUR_GIB, 0,
            ),
            prepublication_durable_bytes=runner._tree_bytes(attempt.root),
        )


def test_coordinated_header_manifest_argv_cwd_mutation_blocks_final_builder(
    tmp_path, monkeypatch,
) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    for name in ("attempt-header.json", "manifest.json"):
        path = attempt.root / name
        value = json.loads(path.read_text(encoding="utf-8"))
        value["frozen_argv"][0] = "pyth0n"
        cwd = value["frozen_cwd"]
        value["frozen_cwd"] = cwd[:-1] + ("x" if cwd[-1:] != "x" else "y")
        path.write_bytes((json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ) + "\n").encode())
    with pytest.raises(orchestration.AttemptError):
        runner._build_tail_plan(
            attempt=attempt, outcome=None, telemetry=None, aggregate={}, inventory=[],
            prepublication_durable_bytes=runner._tree_bytes(attempt.root),
            preview_io_read_bytes=0, preview_io_write_bytes=0,
            active_gate_binding={},
        )


@pytest.mark.parametrize("mutation", ("missing", "sparse", "extra", "field"))
def test_corrupt_resume_history_refuses_before_new_admission(
    tmp_path, monkeypatch, mutation,
) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    admission = attempt.root / "admissions" / "invocation-000000.json"
    invocation = attempt.root / "invocations" / "invocation-000000.json"
    if mutation == "missing":
        admission.unlink()
    elif mutation == "sparse":
        invocation.rename(invocation.with_name("invocation-000001.json"))
    elif mutation == "extra":
        invocation.with_name("invocation-000001.json").write_bytes(invocation.read_bytes())
    else:
        value = json.loads(invocation.read_text(encoding="utf-8"))
        value["invocation_index"] = 1
        invocation.write_bytes((json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ) + "\n").encode())
    monkeypatch.setattr(runner, "validate_performance_readiness_receipt", lambda _path: {})
    admission_calls = []
    with pytest.raises(orchestration.AttemptError):
        runner.run_result(
            result_root=attempt.root,
            admission_receipt=attempt.root / "admissions" / "invocation-000001.json",
            confirmation=contracts.NAMED_RUN_ID, resume=True,
            argv=("python", "runner.py", "--run-01", "--resume"), cwd=tmp_path,
            command_runner=lambda *args, **kwargs: admission_calls.append((args, kwargs)),
            performance_readiness=tmp_path / "ready.json",
        )
    assert admission_calls == []


def test_sealed_identity_tamper_blocks_technical_frontier_commit(tmp_path, monkeypatch) -> None:
    attempt = _make_sealed_attempt(tmp_path, monkeypatch)
    expected_inventory = orchestration.validate_sealed_identity(attempt)
    header = attempt.root / "attempt-header.json"
    header.write_bytes(header.read_bytes() + b"tamper")
    resource = b"resource"
    frontier = b"frontier"
    prepublication = runner._tree_bytes(attempt.root)
    plan = runner.TechnicalSliceTailPlan(
        "resources/invocation-000000.json", resource, frontier,
        prepublication, prepublication + len(resource) + len(frontier), expected_inventory,
    )
    scratch = tmp_path / "technical-scratch"
    scratch.mkdir()
    gate = runner.ActiveInvocationGate(attempt.root, mode="RUN-01")
    gate.acquire()
    try:
        with pytest.raises(orchestration.AttemptError):
            runner._stage_and_commit_technical_slice_tail(
                plan, attempt=attempt, scratch=scratch, active_gate=gate,
            )
    finally:
        gate.release()
    assert not (attempt.root / "technical-frontier.json").exists()
