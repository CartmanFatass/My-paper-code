from __future__ import annotations

import copy
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from experiments.candidates.vsp_03 import event_certified_boundary_confirmation as audit


ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / "scripts/run_vsp03_a1_event_certified_boundary_confirmation.py"
INDEX = ROOT / "docs/research/candidates/vsp_03/CODE_SCIENCE_INDEX.md"


def _replace_row(
    manifest: audit.AuditManifest,
    bits: str,
    *,
    exact: bool | None = None,
    bctt: bool | None = None,
) -> audit.AuditManifest:
    rows = list(manifest.lookup_rows)
    index = next(i for i, row in enumerate(rows) if row.inputs.bits == bits)
    old = rows[index]
    rows[index] = replace(
        old,
        outputs=replace(
            old.outputs,
            exact_boundary_debounce=old.outputs.exact_boundary_debounce if exact is None else exact,
            bctt_ec=old.outputs.bctt_ec if bctt is None else bctt,
        ),
    )
    return replace(manifest, lookup_rows=tuple(rows))


def test_unbound_source_fails_before_lookup_or_runtime_activity() -> None:
    result = audit.audit_manifest(audit.unbound_manifest()).to_dict()
    assert result["terminal_branch"] == "A1_INVALID_EVENT_CAUSALITY_OR_SCOPE"
    assert result["activity"]["lookup_evaluations"] == 0
    assert all(
        value == 0
        for name, value in result["activity"].items()
        if name != "registered_audits"
    )
    assert result["registered_source_status"] == "NO_GENUINE_TARGET_NEGATIVE_CAUSAL_DEPLOYMENT_EVENT_SEAM"
    assert result["source_receipt"] == {
        "status": "UNBOUND",
        "source_id": None,
        "authentication_id": None,
        "event_observations": [],
        "fabricated_event_latches": 0,
        "failures": ["NO_AUTHENTICATED_CAUSAL_SOURCE_BOUND"],
    }
    assert result["truth_table_audit"] == {"status": "NOT_EVALUATED", "rows": []}
    assert result["trace_audit"] == {"status": "NOT_EVALUATED", "traces": {}}


def test_frozen_future_source_truth_table_is_complete_and_exact() -> None:
    assert [f"{row.inputs.bits}->{row.outputs.bits}" for row in audit.FROZEN_TRUTH_TABLE] == [
        "000->00", "001->00", "010->00", "011->00",
        "100->00", "101->00", "110->11", "111->10",
    ]
    receipt = audit.audit_manifest(audit.unbound_manifest()).to_dict()["frozen_contract"]["truth_rows"]
    assert [row["a_y_e"] for row in receipt] == [f"{value:03b}" for value in range(8)]
    assert {row["a_y_e"] for row in receipt if row["causal_state"] == "INVALID_UNARMED_LATCH"} == {"001", "011"}


def test_complete_future_source_exercises_truth_table_traces_and_only_lookup_activity() -> None:
    result = audit.audit_manifest(audit.future_bound_manifest()).to_dict()
    assert result["terminal_branch"] == "A1_EVENT_CERTIFIED_BOUNDARY_DIVERGENCE_SUPPORTED"
    assert result["truth_table_audit"]["status"] == "EVALUATED"
    assert [row["actual"] for row in result["truth_table_audit"]["rows"]] == [
        "00", "00", "00", "00", "00", "00", "11", "10",
    ]
    assert result["activity"]["lookup_evaluations"] == 27
    assert all(result["activity"][name] == 0 for name in audit.ZERO_RUNTIME_FIELDS)
    traces = result["trace_audit"]["traces"]
    assert traces["INITIAL"] == {
        "decision": {"EXACT_BOUNDARY_DEBOUNCE": False, "BCTT_EC": False},
        "post_armed": {"EXACT_BOUNDARY_DEBOUNCE": True, "BCTT_EC": True},
    }
    assert traces["HOLD"] == {
        "decision": {"EXACT_BOUNDARY_DEBOUNCE": True, "BCTT_EC": True},
        "post_state": {
            "EXACT_BOUNDARY_DEBOUNCE": {"armed": False, "event_latched": False},
            "BCTT_EC": {"armed": False, "event_latched": False},
        },
    }
    assert traces["EXCURSION_REENTRY"] == {
        "decision": {"EXACT_BOUNDARY_DEBOUNCE": True, "BCTT_EC": False},
        "bctt_post_armed": True,
        "bctt_post_latch": False,
    }
    assert traces["CLEAN_TAU2"] == {"bctt_ec": True}
    assert traces["RESET_REARM"] == {
        "after_reset": {"armed": False, "event_latched": False},
        "first": False,
        "second": True,
    }
    assert traces["IDENTITY_CHANGE_REARM"] == {
        "after_identity_change": {"armed": False, "event_latched": False},
        "first": False,
        "second": True,
    }
    assert all(
        decisions == {"EXACT_BOUNDARY_DEBOUNCE": True, "BCTT_EC": True}
        for decisions in traces["BYPASS"].values()
    )


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("source_id", ""),
        ("authentication_id", ""),
        ("authentication_verified", False),
        ("primitive_event_name", ""),
        ("scope", audit.ScopeClass.FIRST_PASSAGE),
        ("prospectively_declared_before_trace", False),
        ("prospectively_declared_before_trace", 1),
        ("target_negative_is_primitive_event", False),
        ("target_causal_identity_bound", False),
        ("strictly_inside_open_boundary_interval", False),
        ("available_before_boundary_decision", False),
        ("boundaries_strictly_ordered", False),
        ("tied_events_forbidden", False),
    ],
)
def test_every_causal_source_or_scope_defect_dominates_without_lookup(field: str, bad: object) -> None:
    manifest = audit.future_bound_manifest()
    manifest = replace(manifest, source=replace(manifest.source, **{field: bad}))
    result = audit.audit_manifest(manifest).to_dict()
    assert result["terminal_branch"] == "A1_INVALID_EVENT_CAUSALITY_OR_SCOPE"
    assert result["activity"]["lookup_evaluations"] == 0
    assert result["source_receipt"]["event_observations"] == []
    assert result["source_receipt"]["fabricated_event_latches"] == 0


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("bit_identical_inputs", False),
        ("bit_identical_primitive_events", False),
        ("bit_identical_clocks", False),
        ("bit_identical_eligibility_classes", False),
        ("bit_identical_resets", False),
        ("bit_identical_termination_causes", False),
        ("bit_identical_credit_assignment", False),
        ("armed_bits_exact", 2),
        ("armed_bits_exact", True),
        ("armed_bits_bctt_ec", 0),
        ("event_latches_exact", 0),
        ("event_latches_bctt_ec", 2),
        ("lookup_width_exact", 2),
        ("lookup_width_bctt_ec", 4),
        ("event_latch_is_costed_in_both_arms", False),
    ],
)
def test_parity_cause_credit_and_cost_contract_is_fail_closed(field: str, bad: object) -> None:
    manifest = audit.future_bound_manifest()
    manifest = replace(manifest, parity=replace(manifest.parity, **{field: bad}))
    result = audit.audit_manifest(manifest).to_dict()
    assert result["terminal_branch"] == "A1_INVALID_PARITY_OR_CAUSE_CONTRACT"
    assert result["activity"]["lookup_evaluations"] == 0


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("exact", "A1_EXACT_DEBOUNCE_NOT_REPRODUCED"),
        ("hold", "A1_BCTT_EC_HOLD_REGRESSION"),
        ("collapse", "A1_BCTT_EC_REPAIR_COLLAPSES_TO_DEBOUNCE"),
        ("lifecycle", "A1_LATCH_RESET_OR_REARM_FAILED"),
    ],
)
def test_authoritative_branch_precedence_reaches_each_post_contract_failure(mutation: str, expected: str) -> None:
    manifest = audit.future_bound_manifest()
    if mutation == "exact":
        manifest = _replace_row(manifest, "110", exact=False)
    elif mutation == "hold":
        manifest = _replace_row(manifest, "110", bctt=False)
    elif mutation == "collapse":
        manifest = _replace_row(manifest, "111", bctt=True)
    else:
        manifest = replace(manifest, lifecycle=replace(manifest.lifecycle, evaluate_before_update=False))
    assert audit.audit_manifest(manifest).to_dict()["terminal_branch"] == expected


def test_untraced_valid_bctt_row_mismatch_cannot_reach_supported_branch() -> None:
    manifest = _replace_row(audit.future_bound_manifest(), "100", bctt=True)
    result = audit.audit_manifest(manifest).to_dict()
    row = next(item for item in result["truth_table_audit"]["rows"] if item["a_y_e"] == "100")
    assert row == {
        "a_y_e": "100",
        "actual": "01",
        "expected": "00",
        "causal_state": "VALID",
    }
    assert result["terminal_branch"] == "A1_BCTT_EC_HOLD_REGRESSION"
    assert {failure["kind"] for failure in result["contract_failures"]} == {"BCTT_EC_HOLD_REGRESSION"}


def test_branch_precedence_is_exact_and_earlier_failures_dominate() -> None:
    assert audit.BRANCH_PRECEDENCE == (
        "A1_INVALID_EVENT_CAUSALITY_OR_SCOPE",
        "A1_INVALID_PARITY_OR_CAUSE_CONTRACT",
        "A1_EXACT_DEBOUNCE_NOT_REPRODUCED",
        "A1_BCTT_EC_HOLD_REGRESSION",
        "A1_BCTT_EC_REPAIR_COLLAPSES_TO_DEBOUNCE",
        "A1_LATCH_RESET_OR_REARM_FAILED",
        "A1_EVENT_CERTIFIED_BOUNDARY_DIVERGENCE_SUPPORTED",
    )
    manifest = _replace_row(audit.future_bound_manifest(), "110", exact=False, bctt=False)
    manifest = replace(
        manifest,
        source=replace(manifest.source, target_causal_identity_bound=False),
        parity=replace(manifest.parity, bit_identical_credit_assignment=False),
        lifecycle=replace(manifest.lifecycle, reset_clears_armed_and_latch=False),
    )
    result = audit.audit_manifest(manifest).to_dict()
    assert result["terminal_branch"] == audit.BRANCH_PRECEDENCE[0]
    assert result["branch_precedence_applied"] == list(audit.BRANCH_PRECEDENCE)


@pytest.mark.parametrize(
    "field",
    [
        "evaluate_before_update",
        "continuing_sets_armed_to_current_positive",
        "continuing_clears_event_latch",
        "first_negative_while_armed_sets_latch",
        "latch_sticky_through_reentry",
        "termination_clears_armed_and_latch",
        "reset_clears_armed_and_latch",
        "identity_change_clears_armed_and_latch",
        "bypass_completes_on_first_positive",
    ],
)
def test_each_lifecycle_clause_is_observable_in_frozen_traces(field: str) -> None:
    manifest = audit.future_bound_manifest()
    manifest = replace(manifest, lifecycle=replace(manifest.lifecycle, **{field: False}))
    assert audit.audit_manifest(manifest).to_dict()["terminal_branch"] == "A1_LATCH_RESET_OR_REARM_FAILED"


def test_lifecycle_boolean_types_are_not_coerced() -> None:
    manifest = audit.future_bound_manifest()
    manifest = replace(manifest, lifecycle=replace(manifest.lifecycle, evaluate_before_update=1))
    result = audit.audit_manifest(manifest).to_dict()
    assert result["terminal_branch"] == "A1_LATCH_RESET_OR_REARM_FAILED"
    assert result["lifecycle_contract_receipt"]["failures"] == ["EVALUATE_BEFORE_UPDATE"]


def test_incomplete_or_duplicate_lookup_manifest_fails_at_exact_debounce_branch() -> None:
    manifest = audit.future_bound_manifest()
    for rows in (manifest.lookup_rows[:-1], manifest.lookup_rows[:-1] + (manifest.lookup_rows[0],)):
        result = audit.audit_manifest(replace(manifest, lookup_rows=rows)).to_dict()
        assert result["terminal_branch"] == "A1_EXACT_DEBOUNCE_NOT_REPRODUCED"
        assert result["trace_audit"] == {"status": "NOT_EVALUATED", "traces": {}}


def test_sticky_latch_ignores_unarmed_negative_and_survives_reentry_until_boundary_update() -> None:
    lifecycle = audit.LifecycleContract()
    state = audit.BoundaryState()
    audit.observe_negative_event(state, lifecycle)
    assert state == audit.BoundaryState(False, False)
    state.armed = True
    audit.observe_negative_event(state, lifecycle)
    audit.observe_negative_event(state, lifecycle)
    audit.observe_reentry(state, lifecycle)
    assert state == audit.BoundaryState(True, True)
    activity = audit.Activity()
    complete = audit.evaluate_boundary(
        rows=audit.FROZEN_TRUTH_MAP,
        arm=audit.Arm.BCTT_EC,
        state=state,
        positive=True,
        scope=audit.ScopeClass.PERSISTENT_OCCUPANCY,
        lifecycle=lifecycle,
        activity=activity,
    )
    assert complete is False
    assert state == audit.BoundaryState(True, False)


def test_validator_rejects_identity_branch_activity_trace_and_source_tampering() -> None:
    manifest = audit.unbound_manifest()
    original = audit.audit_manifest(manifest).to_dict()
    mutations = []
    for path, value in (
        (("candidate_id",), "other"),
        (("terminal_branch",), audit.BRANCH_PRECEDENCE[-1]),
        (("activity", "environment_calls"), 1),
        (("activity", "lookup_evaluations"), 1),
        (("source_receipt", "fabricated_event_latches"), 1),
        (("truth_table_audit", "status"), "EVALUATED"),
    ):
        changed = copy.deepcopy(original)
        target = changed
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        mutations.append(changed)
    for changed in mutations:
        with pytest.raises(audit.ContractViolation, match="recomputation"):
            audit.validate_audit_result(changed, manifest)


def test_one_shot_claim_is_reserved_before_audit_and_never_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "a1.json"
    original = audit.audit_manifest
    observed = {"reserved": False}

    def probe(manifest: audit.AuditManifest) -> audit.AuditResult:
        observed["reserved"] = output.exists() and output.stat().st_size == 0
        return original(manifest)

    monkeypatch.setattr(audit, "audit_manifest", probe)
    result = audit.publish_registered_audit_once(output)
    assert observed["reserved"] is True
    assert json.loads(output.read_text(encoding="utf-8")) == result.to_dict()
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        audit.publish_registered_audit_once(output)


def test_runner_help_and_one_shot_source_free_artifact(tmp_path: Path) -> None:
    import sys

    help_run = subprocess.run([sys.executable, str(RUNNER), "--help"], cwd=ROOT, check=True, capture_output=True, text=True)
    assert "--output" in help_run.stdout
    output = tmp_path / "registered.json"
    completed = subprocess.run([sys.executable, "-B", str(RUNNER), "--output", str(output)], cwd=ROOT, check=True, capture_output=True, text=True)
    summary = json.loads(completed.stdout)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert summary["terminal_branch"] == payload["terminal_branch"] == audit.BRANCH_PRECEDENCE[0]
    assert summary["lookup_evaluations"] == payload["activity"]["lookup_evaluations"] == 0
    refused = subprocess.run([sys.executable, "-B", str(RUNNER), "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
    assert refused.returncode != 0 and "refusing to overwrite" in refused.stderr


def test_code_science_index_binds_observable_and_nonclaims() -> None:
    text = INDEX.read_text(encoding="utf-8")
    for literal in (
        "A1_INVALID_EVENT_CAUSALITY_OR_SCOPE",
        "NO_GENUINE_TARGET_NEGATIVE_CAUSAL_DEPLOYMENT_EVENT_SEAM",
        "evaluate-before-update",
        "sticky through reentry",
        "reset/rearm",
        "first-passage, absorbing, and safety-handoff bypass",
        "bit-identical",
        "termination cause and credit assignment",
        "no natural value, novelty, return, or deployment claim",
    ):
        assert literal in text
    assert "`test_unbound_source_fails_before_lookup_or_runtime_activity`" in text
