"""Section 11 recast of SCDMP-MF-RS-MK-ORDER-VALUE-B01 (2026-09-02).

Provenance: `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`
A.4 decisions 1 and 7;
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`;
`docs/research/candidates/semigroup_consistent_duration_model_policy/
SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md`.

The three behaviours pinned here are:

i.   a missing, unreadable or `REVIEW_REQUIRED` performance assessment is
     recorded and does not refuse the launch (the `runner.py:606-611`
     `ResultExecutionDisabled` raise is gone);
ii.  missing resource telemetry publishes with `resources_unmeasured: true` and
     its reason and quarantines nothing, while a *measured* cap exceedance
     still invalidates;
iii. learner-side instrumentation failure still quarantines under spec §6.2.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    contracts, orchestration, runner,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.orchestration import (
    AttemptError,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.preflight import (
    PreflightReceipt,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.production import (
    PipelineOutcome,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.quarantine import (
    validate_quarantine_lock,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.resources import (
    ResourceTelemetry, UNMEASURED_TELEMETRY_REASONS, partition_failure_reasons,
)


FOUR_GIB = 4 * 1024**3
MASTER = b"scdmp-b01-recast-test-master!!!!"


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


def _a_r2_assessment(path: Path) -> Path:
    """The shape of `temp/scdmp-b01/A-R2/assessment.json` actually on disk."""

    path.write_text(json.dumps({
        "schema": "SCDMP_MF_RS_MK_B01_A_R2_V1",
        "assessment_id": "SCDMP-MF-RS-MK-ORDER-VALUE-B01-A-R2",
        "status": "PERFORMANCE_OBSERVATION_COMPLETE",
        "performance_readiness": "REVIEW_REQUIRED",
        "projection": {
            "conservative_projected_total_seconds": 350.1191929995366,
            "margin_to_1800_seconds": 1449.8808070004634,
            "projected_work_seconds": 290.1191929995366,
            "fixed_overhead_seconds": 60.0,
            "formula": "synthetic-test",
        },
        "scientific_polarity": None,
        "ordered_branch": None,
    }), encoding="utf-8")
    return path


def _unmeasured_telemetry(reasons=("telemetry_missing",)) -> ResourceTelemetry:
    return ResourceTelemetry(
        False, tuple(reasons), 0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0, None, None, 0,
    )


def _measured_telemetry() -> ResourceTelemetry:
    return ResourceTelemetry(
        True, (), 5, 1024, 2048, 4096, 10.0, 5.0, 0.5, 1, 2,
        FOUR_GIB + 1, FOUR_GIB + 1, 0,
    )


def _over_cap_telemetry() -> ResourceTelemetry:
    return ResourceTelemetry(
        False, ("process_tree_peak_rss_exceeded",), 3, 4 * 1024**3, 0, 0,
        10.0, 5.0, 0.5, 1, 1, FOUR_GIB, FOUR_GIB, 0,
    )


class _StubMonitor:
    """Live-telemetry stand-in whose finalized measurement the test chooses."""

    def __init__(self, telemetry: ResourceTelemetry, *, initial_raises: bool = False, **kwargs):
        self._telemetry = telemetry
        self._initial_raises = initial_raises
        self.events: list[str] = []

    def sample_now(self) -> None:
        self.events.append("sample")

    def require_valid_initial_observation(self) -> None:
        if self._initial_raises:
            raise RuntimeError("live resource telemetry lacks a valid initial observation")

    def start(self) -> None:
        self.events.append("start")

    def stop(self) -> None:
        self.events.append("stop")

    def observe_scratch_path(self, path) -> None:
        self.events.append("scratch")

    def finalize(self, *, exit_status: int) -> ResourceTelemetry:
        self.events.append(f"finalize:{exit_status}")
        return self._telemetry


class _Ledger:
    rows = ()

    def reconcile_for_branch(self, **kwargs):
        return {"declared_missions": 0, "actual_missions": 0}


def _outcome() -> PipelineOutcome:
    return PipelineOutcome(
        "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL", _Ledger(), 6, 320, None, True,
    )


def _bind_effectless_source_gate(monkeypatch) -> None:
    monkeypatch.setattr(
        orchestration, "write_source_identity_gate",
        lambda path: Path(path).write_bytes(b"source-gate"),
    )
    monkeypatch.setattr(orchestration, "compute_source_identity_bytes", lambda: b"source-gate")
    monkeypatch.setattr(
        orchestration, "validate_source_identity_bytes",
        lambda persisted, current: None if persisted == current
        else (_ for _ in ()).throw(AttemptError("source gate differs")),
    )


def _drive_run_result(
    tmp_path, monkeypatch, *, telemetry: ResourceTelemetry, pipeline,
    performance_assessment=None, performance_readiness=None,
):
    """Run `run_result` with an effectless source gate, admission and monitor."""

    root = tmp_path / contracts.ATTEMPT_ID
    receipt = tmp_path / "admission.json"
    _bind_effectless_source_gate(monkeypatch)
    monkeypatch.setattr(
        runner, "preflight_run",
        lambda path, *, command_runner: _admission(Path(path)),
    )
    monkeypatch.setattr(runner, "execute_full_pipeline", pipeline)
    monkeypatch.setattr(runner, "_artifact_inventory", lambda *args, **kwargs: [])
    captured: dict[str, object] = {}

    def build_tail_plan(**kwargs):
        captured.update(kwargs)
        return "tail-plan"

    def publish_tail(plan, *, attempt, scratch):
        assert plan == "tail-plan"
        return attempt.root / "published-result.json"

    monkeypatch.setattr(runner, "_build_tail_plan", build_tail_plan)
    monkeypatch.setattr(runner, "_stage_and_publish_tail", publish_tail)
    monitor = _StubMonitor(telemetry)
    result = runner.run_result(
        result_root=root, admission_receipt=receipt,
        confirmation=contracts.NAMED_RUN_ID,
        argv=("python", "runner.py", "--run-01"), cwd=tmp_path,
        command_runner=lambda *_a, **_k: None,
        monitor_factory=lambda **kwargs: monitor,
        performance_readiness=performance_readiness,
        performance_assessment=performance_assessment,
    )
    return root, result, captured


# --- (i) the demoted performance-readiness receipt -------------------------


def test_review_required_assessment_is_recorded_and_never_raises(tmp_path) -> None:
    path = _a_r2_assessment(tmp_path / "assessment.json")
    record = runner.performance_assessment_record(
        performance_readiness=None, performance_assessment=path,
    )
    assert record["schema"] == runner.PERFORMANCE_ASSESSMENT_SCHEMA
    assert record["gating"] is False
    assert record["assessment_performance_readiness"] == "REVIEW_REQUIRED"
    assert record["assessment_id"] == "SCDMP-MF-RS-MK-ORDER-VALUE-B01-A-R2"
    assert record["assessment_status"] == "PERFORMANCE_OBSERVATION_COMPLETE"
    assert record["assessment_note"] is None
    assert record["readiness_receipt_note"] == "not_supplied"
    assert record["scientific_polarity"] is None
    assert record["ordered_branch"] is None
    assert record["section11_recast_record"].endswith(
        "SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md"
    )


@pytest.mark.parametrize("supplied", ("absent", "missing_file", "not_json"))
def test_absent_or_broken_assessment_is_recorded_not_raised(tmp_path, supplied) -> None:
    if supplied == "absent":
        path = None
    elif supplied == "missing_file":
        path = tmp_path / "nowhere.json"
    else:
        path = tmp_path / "broken.json"
        path.write_bytes(b"[]")
    record = runner.performance_assessment_record(
        performance_readiness=None, performance_assessment=path,
    )
    assert record["gating"] is False
    assert record["assessment_performance_readiness"] is None
    assert record["assessment_note"] is not None


def test_run_result_reaches_the_attempt_with_a_review_required_assessment(
    tmp_path, monkeypatch,
) -> None:
    """No `ResultExecutionDisabled` on the receipt; the run reaches the attempt."""

    assessment_path = _a_r2_assessment(tmp_path / "assessment.json")
    root = tmp_path / contracts.ATTEMPT_ID
    monkeypatch.setattr(
        runner, "preflight_run",
        lambda path, *, command_runner: _admission(Path(path)),
    )
    reached: list[str] = []

    def stop_at_attempt(**kwargs):
        reached.append("attempt")
        raise RuntimeError("stop-before-root")

    monkeypatch.setattr(runner, "_initialize_or_resume_attempt", stop_at_attempt)
    with pytest.raises(RuntimeError, match="stop-before-root"):
        runner.run_result(
            result_root=root, admission_receipt=tmp_path / "admission.json",
            confirmation=contracts.NAMED_RUN_ID,
            argv=("python", "runner.py", "--run-01"), cwd=tmp_path,
            command_runner=lambda *_a, **_k: None,
            monitor_factory=lambda **kwargs: _StubMonitor(_measured_telemetry()),
            performance_readiness=None, performance_assessment=assessment_path,
        )
    assert reached == ["attempt"]
    assert not root.exists()


def test_recorded_assessment_is_a_create_once_attempt_artifact(tmp_path, monkeypatch) -> None:
    _bind_effectless_source_gate(monkeypatch)
    receipt = tmp_path / "admission.json"
    admission = _admission(receipt)
    attempt = orchestration._initialize_or_resume_attempt(
        result_root=tmp_path / contracts.ATTEMPT_ID, admission_receipt=receipt,
        admission=admission, master_source=lambda: MASTER,
        argv=("python", "runner.py", "--run-01"), cwd=tmp_path, resume=False,
        telemetry_witness=orchestration._issue_initial_telemetry_witness(
            _StubMonitor(_measured_telemetry())
        ),
    )
    record = runner.performance_assessment_record(
        performance_readiness=None,
        performance_assessment=_a_r2_assessment(tmp_path / "assessment.json"),
    )
    path = runner._record_performance_assessment(attempt.root, record)
    assert path.name == runner.PERFORMANCE_ASSESSMENT_FILE
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["assessment_performance_readiness"] == "REVIEW_REQUIRED"
    # Create-once: a second call neither raises nor rewrites the artifact.
    direct = path.read_bytes()
    runner._record_performance_assessment(attempt.root, record)
    assert path.read_bytes() == direct


def test_failed_initial_telemetry_observation_is_recorded_on_the_witness() -> None:
    witness = orchestration._issue_initial_telemetry_witness(
        _StubMonitor(_unmeasured_telemetry(), initial_raises=True)
    )
    assert witness.nonce is orchestration._TELEMETRY_WITNESS_NONCE
    assert witness.unmeasured_reason == "initial_observation_unavailable:RuntimeError"
    clean = orchestration._issue_initial_telemetry_witness(_StubMonitor(_measured_telemetry()))
    assert clean.unmeasured_reason is None


def test_a_monitor_without_a_validator_is_still_a_programming_error() -> None:
    with pytest.raises(AttemptError, match="cannot validate"):
        orchestration._issue_initial_telemetry_witness(object())


# --- (ii) telemetry recorded, not an invalidator ---------------------------


def test_failure_reason_partition_matches_the_recast_vocabulary() -> None:
    assert UNMEASURED_TELEMETRY_REASONS == frozenset({
        "telemetry_missing", "telemetry_measurement_failed", "telemetry_zero_work",
    })
    unmeasured, invalidating = partition_failure_reasons((
        "telemetry_missing", "telemetry_measurement_failed", "telemetry_zero_work",
        "process_tree_peak_rss_exceeded", "scratch_high_water_exceeded",
        "durable_output_exceeded", "wall_time_exceeded", "result_process_nonzero_exit",
    ))
    assert unmeasured == (
        "telemetry_missing", "telemetry_measurement_failed", "telemetry_zero_work",
    )
    assert invalidating == (
        "process_tree_peak_rss_exceeded", "scratch_high_water_exceeded",
        "durable_output_exceeded", "wall_time_exceeded", "result_process_nonzero_exit",
    )


def test_aggregate_records_unmeasured_telemetry_and_still_fails_a_measured_cap() -> None:
    unmeasured = runner._aggregate_telemetry((
        _unmeasured_telemetry(("telemetry_missing", "telemetry_measurement_failed")),
    ))
    assert unmeasured["passed"] is True
    assert unmeasured["failure_reasons"] == []
    assert unmeasured["resources_unmeasured"] is True
    assert unmeasured["resources_unmeasured_reasons"] == [
        "telemetry_missing", "telemetry_measurement_failed",
    ]

    over_cap = runner._aggregate_telemetry((_over_cap_telemetry(),))
    assert over_cap["passed"] is False
    assert "process_tree_peak_rss_exceeded" in over_cap["failure_reasons"]
    assert over_cap["resources_unmeasured"] is False

    measured = runner._aggregate_telemetry((_measured_telemetry(),))
    assert measured["passed"] is True
    assert measured["resources_unmeasured"] is False
    assert measured["resources_unmeasured_reasons"] == []


def test_prior_invocation_telemetry_tolerates_unmeasured_but_not_a_cap(tmp_path) -> None:
    unmeasured = tmp_path / "unmeasured.json"
    unmeasured.write_text(
        json.dumps({"invocation_telemetry": asdict(_unmeasured_telemetry())}), encoding="utf-8",
    )
    assert runner._load_telemetry(unmeasured).failure_reasons == ("telemetry_missing",)

    over_cap = tmp_path / "over-cap.json"
    over_cap.write_text(
        json.dumps({"invocation_telemetry": asdict(_over_cap_telemetry())}), encoding="utf-8",
    )
    with pytest.raises(AttemptError, match="did not pass"):
        runner._load_telemetry(over_cap)


def test_missing_telemetry_publishes_resources_unmeasured_and_quarantines_nothing(
    tmp_path, monkeypatch,
) -> None:
    root, result, captured = _drive_run_result(
        tmp_path, monkeypatch,
        telemetry=_unmeasured_telemetry(("telemetry_missing", "telemetry_measurement_failed")),
        pipeline=lambda attempt, **kwargs: _outcome(),
        performance_assessment=_a_r2_assessment(tmp_path / "assessment.json"),
    )
    assert result.name == "published-result.json"
    aggregate = captured["aggregate"]
    assert aggregate["passed"] is True
    assert aggregate["resources_unmeasured"] is True
    assert aggregate["resources_unmeasured_reasons"] == [
        "telemetry_missing", "telemetry_measurement_failed",
    ]
    # Decision 7: a missing measurement neither quarantines nor terminates.
    assert validate_quarantine_lock(root, mode="RUN-01") is False
    assert not (root / "terminal-no-polarity.json").exists()
    # The demoted receipt evidence is on disk as a recorded field.
    recorded = json.loads(
        (root / runner.PERFORMANCE_ASSESSMENT_FILE).read_text(encoding="utf-8")
    )
    assert recorded["gating"] is False
    assert recorded["assessment_performance_readiness"] == "REVIEW_REQUIRED"
    assert recorded["initial_telemetry_unmeasured_reason"] is None


def test_measured_cap_exceedance_still_fails_the_resource_contract(tmp_path, monkeypatch) -> None:
    with pytest.raises(AttemptError, match="measured resource contract"):
        _drive_run_result(
            tmp_path, monkeypatch, telemetry=_over_cap_telemetry(),
            pipeline=lambda attempt, **kwargs: _outcome(),
        )
    root = tmp_path / contracts.ATTEMPT_ID
    assert validate_quarantine_lock(root, mode="RUN-01") is True


def test_publication_values_carry_the_recorded_resource_fields(tmp_path, monkeypatch) -> None:
    _root, _result, captured = _drive_run_result(
        tmp_path, monkeypatch, telemetry=_unmeasured_telemetry(),
        pipeline=lambda attempt, **kwargs: _outcome(),
    )
    _ledger, _branch, published = runner._publication_values(
        captured["attempt"], captured["outcome"], captured["aggregate"], [],
        sealed_identity=(),
    )
    assert published["resources_unmeasured"] is True
    assert published["resources_unmeasured_reasons"] == ["telemetry_missing"]
    assert published["performance_assessment_file"] == runner.PERFORMANCE_ASSESSMENT_FILE
    assert published["section11_recast_record"].endswith(
        "SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md"
    )


# --- (iii) learner-side instrumentation still quarantines ------------------


@pytest.mark.parametrize("failure", (
    "foundation checkpoint artifact is missing",
    "required publication artifact is invalid: competence.json",
    "cold checkpoint frontier validation differs",
))
def test_learner_side_instrumentation_failure_still_quarantines(
    tmp_path, monkeypatch, failure,
) -> None:
    """Spec §6.2 is unchanged by the recast (compliance note A.4 decision 7)."""

    def broken_pipeline(attempt, **kwargs):
        raise AttemptError(failure)

    with pytest.raises(AttemptError, match="missing|invalid|differs"):
        _drive_run_result(
            tmp_path, monkeypatch, telemetry=_measured_telemetry(), pipeline=broken_pipeline,
        )
    root = tmp_path / contracts.ATTEMPT_ID
    assert validate_quarantine_lock(root, mode="RUN-01") is True
    terminal = json.loads((root / "terminal-no-polarity.json").read_text(encoding="utf-8"))
    assert terminal["scientific_polarity"] is None
