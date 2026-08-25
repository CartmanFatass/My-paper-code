from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.artifacts import (
    ADAPTER_ARMS,
    ArtifactContractError,
    AdapterFinalReceipt,
    EmpiricalBindings,
    FinalPanelReceipt,
    FoundationFinalReceipt,
    FoundationGate,
    GateOutcome,
    OpportunityReceipt,
    ResultCode,
    accepted_native_binding,
    accepted_native_binding_digest,
    final_panel_barrier_digest,
    foundation_barrier_digest,
    issue_adapter_execution_permit,
    issue_final_evaluation_permit,
    issue_stage1b_opportunity_execution_permit,
    load_foundation_gate,
    load_opportunity_receipt,
    preactivity_template,
    publish_complete_result,
    publish_foundation_gate,
    publish_opportunity_receipt,
    publish_preactivity_template,
    require_final_panel_barrier,
    require_foundation_checkpoint_barrier,
    seal_empirical_activity_permit,
    seal_empirical_bindings,
    test_only_bindings as make_test_bindings,
    validate_stage1b_opportunity_execution_permit,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.frontier import (
    FrontierContractError,
    FrontierGeneration,
    FrontierStage,
    FrontierState,
    adapter_receipt_from_final,
    create_frontier_generation,
    foundation_receipt_from_final,
    frontier_generation_digest,
    load_frontier_generation,
    load_resume_chain,
    validate_resume_chain,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.host_types import HostOutput
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.opportunity import (
    DisturbanceTape,
    OpportunityContractError,
    OpportunityState,
    run_complete_pair,
)


def fake(name: str) -> str:
    return "TEST_ONLY_FAKE_SHA256:" + hashlib.sha256(name.encode("ascii")).hexdigest()


def real_digest(name: str) -> str:
    return hashlib.sha256(f"OPAQUE_TEST_PRODUCTION_FORM:{name}".encode("ascii")).hexdigest()


def production_bindings(token: str) -> EmpiricalBindings:
    activity = seal_empirical_activity_permit(
        authorization_sha256=real_digest(f"{token}:authorization")
    )
    return seal_empirical_bindings(
        permit=activity,
        source_manifest_sha256=real_digest(f"{token}:source"),
        shared_receipt_sha256=real_digest(f"{token}:shared"),
        master_commitment_sha256=real_digest(f"{token}:master-commitment"),
        empirical_identity_sha256=real_digest(f"{token}:empirical-binding"),
        coordinate_manifest_sha256=real_digest(f"{token}:coordinate-binding"),
        origin_receipt_sha256=real_digest(f"{token}:origin"),
    )


def production_foundation_receipts(bindings: EmpiricalBindings):
    return tuple(
        FoundationFinalReceipt(
            replicate=replicate,
            coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
            checkpoint_sha256=real_digest(f"checkpoint:{replicate}"),
            optimizer_state_sha256=real_digest(f"optimizer:{replicate}"),
        )
        for replicate in range(24)
    )


class _ProductionPermitTestOnlySession:
    created = 0

    def __init__(self, resets):
        resets = tuple(resets)
        type(self).created += 1
        self.initial = tuple(_test_host_output(active=True, terminal=False, tick=0) for _ in resets)

    def renew(self, rows):
        return tuple(_test_host_output(active=False, terminal=True, tick=7) for _ in tuple(rows))

    def close(self):
        pass


def _test_host_output(*, active: bool, terminal: bool, tick: int) -> HostOutput:
    return HostOutput(
        advanced=tick > 0, active=active, terminal=terminal,
        ticks_advanced=tick, tick=tick, hold_k=7, next_k=7,
        observation=(0.0,) * 18, safe_dock=False, timeout=terminal,
        cable_overload=False, gantry_contact=False, attitude_loss=False,
        formation_loss=False, cumulative_reward=0.0, cumulative_energy=0.0,
        energy_ticks=tick, dock_tick=None,
    )


def _test_opportunity_tapes():
    signs = ((1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1))
    return tuple(
        DisturbanceTape(
            f"TEST_ONLY:production-permit-tape:{index}",
            (0.003 * x,) * 364,
            (0.002 * y,) * 364,
            (0.004 * z,) * 364,
        )
        for index, (x, y, z) in enumerate(signs)
    )


def foundation_final(replicate: int, bindings: EmpiricalBindings) -> FrontierGeneration:
    return FrontierGeneration(
        stage=FrontierStage.FOUNDATION,
        replicate=replicate,
        arm="FOUNDATION",
        lineage_digest=bindings.lineage_digest,
        coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
        generation=0,
        previous_generation_sha256=None,
        state=FrontierState.FINAL_CHECKPOINT,
        update_index=160,
        optimizer_step=1920,
        checkpoint_sha256=fake(f"foundation-checkpoint-{replicate}"),
        optimizer_state_sha256=fake(f"foundation-optimizer-{replicate}"),
    )


def adapter_final(replicate: int, arm: str, bindings: EmpiricalBindings) -> FrontierGeneration:
    return FrontierGeneration(
        stage=FrontierStage.ADAPTER,
        replicate=replicate,
        arm=arm,
        lineage_digest=bindings.lineage_digest,
        coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
        generation=0,
        previous_generation_sha256=None,
        state=FrontierState.FINAL_CHECKPOINT,
        update_index=96,
        optimizer_step=1152,
        checkpoint_sha256=fake(f"adapter-checkpoint-{replicate}-{arm}"),
        optimizer_state_sha256=fake(f"adapter-optimizer-{replicate}-{arm}"),
    )


def gates(root: Path, bindings: EmpiricalBindings, *, opportunity_pass: bool = True):
    foundation_receipts = tuple(
        foundation_receipt_from_final(foundation_final(i, bindings), bindings=bindings)
        for i in range(24)
    )
    barrier = require_foundation_checkpoint_barrier(foundation_receipts, bindings)
    foundation = FoundationGate(
        outcome=GateOutcome.PASS,
        complete_panel_sha256=fake("foundation-panel"),
        barrier_sha256=foundation_barrier_digest(barrier),
    )
    foundation_path = root / "foundation-gate.json"
    publish_foundation_gate(
        foundation_path, foundation, artifact_root=root, barrier=barrier, bindings=bindings
    )
    foundation = load_foundation_gate(
        foundation_path, artifact_root=root, barrier=barrier, bindings=bindings
    )
    foundation_sha = hashlib.sha256(foundation_path.read_bytes()).hexdigest()
    opportunity = OpportunityReceipt(
        outcome=GateOutcome.PASS if opportunity_pass else GateOutcome.NONPASS,
        complete_stage_sha256=fake("opportunity-stage"),
        foundation_gate_sha256=foundation_sha,
    )
    opportunity_path = root / "opportunity.json"
    publish_opportunity_receipt(
        opportunity_path,
        opportunity,
        artifact_root=root,
        foundation_gate_path=foundation_path,
        foundation_gate=foundation,
        bindings=bindings,
    )
    opportunity = load_opportunity_receipt(
        opportunity_path,
        artifact_root=root,
        foundation_gate_path=foundation_path,
        foundation_gate=foundation,
        bindings=bindings,
    )
    adapter_permit = None
    if opportunity.outcome is GateOutcome.PASS:
        adapter_permit = issue_adapter_execution_permit(
            foundation_gate_path=foundation_path,
            foundation_gate=foundation,
            opportunity_path=opportunity_path,
            opportunity=opportunity,
            artifact_root=root,
            bindings=bindings,
        )
    return barrier, foundation_path, foundation, opportunity_path, opportunity, adapter_permit


def test_preactivity_template_has_no_empirical_fields(tmp_path: Path) -> None:
    payload = preactivity_template(
        source_manifest_sha256="1" * 64, shared_receipt_sha256="2" * 64
    )
    forbidden = {"master_commitment_sha256", "empirical_identity_sha256", "coordinate_manifest_sha256", "origin_receipt_sha256"}
    assert forbidden.isdisjoint(payload)
    assert payload["scientific_activity_started"] is False
    assert payload["native_abi"] == 2
    assert payload["native_source_sha256"] == "ea2149b187ba65c9229f0ada9c3bd55bd0f424ec5a5830de1f454585b488de38"
    assert payload["native_build_key"] == "9a9801e94e1b02468df1e3d59e0c0055b85e2d02306c018bb275b69e0f718fe3"
    assert payload["native_artifact_sha256"] == "df1097603c3fd2e1f66875e5d3209fcc509609f870569a205efc83c607a7bb9d"
    assert payload["native_artifact_size"] == 177664
    assert payload["native_struct_sizes"]["host_output"] == 336
    assert payload["native_reward_trace"] == {
        "abi_version": 2,
        "capacity": 13,
        "count_field": "last_hold_reward_count",
        "values_field": "last_hold_rewards",
        "count_equals_ticks_advanced": True,
        "inactive_tail": "canonical_zero",
    }
    path = tmp_path / "preactivity.json"
    publish_preactivity_template(
        path,
        artifact_root=tmp_path,
        source_manifest_sha256="1" * 64,
        shared_receipt_sha256="2" * 64,
    )
    with pytest.raises(ArtifactContractError, match="create-only"):
        publish_preactivity_template(
            path,
            artifact_root=tmp_path,
            source_manifest_sha256="1" * 64,
            shared_receipt_sha256="2" * 64,
        )


def test_unsealed_and_non_fake_test_bindings_fail_closed() -> None:
    raw = EmpiricalBindings(*(["1" * 64] * 7), test_only=False)
    with pytest.raises(ArtifactContractError, match="sealed"):
        raw.validate()
    bad_test = replace(make_test_bindings(), source_manifest_sha256="1" * 64)
    with pytest.raises(ArtifactContractError, match="TEST_ONLY"):
        bad_test.validate()


def test_hash_linked_same_coordinate_resume_and_receipt(tmp_path: Path) -> None:
    bindings = make_test_bindings(token="resume")
    created = FrontierGeneration(
        stage=FrontierStage.FOUNDATION,
        replicate=3,
        arm="FOUNDATION",
        lineage_digest=bindings.lineage_digest,
        coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
        generation=0,
        previous_generation_sha256=None,
        state=FrontierState.CREATED,
        update_index=0,
        optimizer_step=0,
    )
    training = replace(
        created,
        generation=1,
        previous_generation_sha256=frontier_generation_digest(created, bindings),
        state=FrontierState.TRAINING,
        update_index=80,
        optimizer_step=960,
    )
    final = replace(
        training,
        generation=2,
        previous_generation_sha256=frontier_generation_digest(training, bindings),
        state=FrontierState.FINAL_CHECKPOINT,
        update_index=160,
        optimizer_step=1920,
        checkpoint_sha256=fake("resume-checkpoint"),
        optimizer_state_sha256=fake("resume-optimizer"),
    )
    paths = [tmp_path / f"g{i}.json" for i in range(3)]
    for path, row in zip(paths, (created, training, final), strict=True):
        create_frontier_generation(path, row, artifact_root=tmp_path, bindings=bindings)
    loaded = load_resume_chain(paths, artifact_root=tmp_path, bindings=bindings)
    assert loaded[-1] == final
    receipt = foundation_receipt_from_final(final, bindings=bindings)
    assert receipt.optimizer_state_sha256 == fake("resume-optimizer")
    with pytest.raises(FrontierContractError, match="create-only"):
        create_frontier_generation(paths[0], created, artifact_root=tmp_path, bindings=bindings)


def test_resume_rejects_cross_lineage_coordinate_gap_and_backward_progress() -> None:
    one = make_test_bindings(token="one")
    other = make_test_bindings(token="other")
    start = FrontierGeneration(
        FrontierStage.ADAPTER, 0, "TREAT", one.lineage_digest,
        one.coordinate_manifest_sha256, 0, None, FrontierState.CREATED, 0, 0
    )
    next_row = replace(
        start, generation=1, previous_generation_sha256=frontier_generation_digest(start, one),
        state=FrontierState.TRAINING, update_index=10, optimizer_step=120,
    )
    assert len(validate_resume_chain((start, next_row), bindings=one)) == 2
    with pytest.raises(FrontierContractError, match="lineage"):
        replace(next_row, lineage_digest=other.lineage_digest).validate(one)
    with pytest.raises(FrontierContractError, match="skipped"):
        validate_resume_chain((start, replace(next_row, generation=2)), bindings=one)
    backwards = replace(
        next_row,
        generation=2,
        previous_generation_sha256=frontier_generation_digest(next_row, one),
        update_index=9,
        optimizer_step=119,
    )
    with pytest.raises(FrontierContractError, match="backward"):
        validate_resume_chain((start, next_row, backwards), bindings=one)


def test_exact_foundation_barrier_rejects_incomplete_duplicate_and_tamper(tmp_path: Path) -> None:
    bindings = make_test_bindings(token="foundation")
    receipts = tuple(
        foundation_receipt_from_final(foundation_final(i, bindings), bindings=bindings)
        for i in range(24)
    )
    barrier = require_foundation_checkpoint_barrier(receipts, bindings)
    assert barrier.accepted_slots == 24
    with pytest.raises(ArtifactContractError, match="exactly 24"):
        require_foundation_checkpoint_barrier(receipts[:-1], bindings)
    with pytest.raises(ArtifactContractError, match="missing, duplicate"):
        require_foundation_checkpoint_barrier(receipts[:-1] + (receipts[0],), bindings)
    gate = FoundationGate(GateOutcome.PASS, fake("panel"), foundation_barrier_digest(barrier))
    path = tmp_path / "gate.json"
    publish_foundation_gate(path, gate, artifact_root=tmp_path, barrier=barrier, bindings=bindings)
    row = json.loads(path.read_text("ascii"))
    row["outcome"] = "UNKNOWN"
    path.write_text(json.dumps(row, sort_keys=True, separators=(",", ":")), "ascii")
    with pytest.raises(ArtifactContractError):
        load_foundation_gate(path, artifact_root=tmp_path, barrier=barrier, bindings=bindings)


def test_opportunity_is_conditional_and_exact(tmp_path: Path) -> None:
    bindings = make_test_bindings(token="opportunity")
    receipts = tuple(
        foundation_receipt_from_final(foundation_final(i, bindings), bindings=bindings)
        for i in range(24)
    )
    barrier = require_foundation_checkpoint_barrier(receipts, bindings)
    nonpass = FoundationGate(GateOutcome.NONPASS, fake("nonpass"), foundation_barrier_digest(barrier))
    foundation_path = tmp_path / "foundation.json"
    publish_foundation_gate(
        foundation_path, nonpass, artifact_root=tmp_path, barrier=barrier, bindings=bindings
    )
    receipt = OpportunityReceipt(GateOutcome.PASS, fake("opportunity"), hashlib.sha256(foundation_path.read_bytes()).hexdigest())
    with pytest.raises(ArtifactContractError, match="inapplicable"):
        publish_opportunity_receipt(
            tmp_path / "opportunity.json", receipt, artifact_root=tmp_path,
            foundation_gate_path=foundation_path, foundation_gate=nonpass, bindings=bindings,
        )


def test_production_stage1b_permit_bridges_exact_foundation_barrier_and_atomic_gate(tmp_path: Path) -> None:
    bindings = production_bindings("stage1b")
    receipts = production_foundation_receipts(bindings)
    barrier = require_foundation_checkpoint_barrier(receipts, bindings)
    gate = FoundationGate(
        GateOutcome.PASS,
        real_digest("foundation-complete-panel"),
        foundation_barrier_digest(barrier),
    )
    gate_path = tmp_path / "FOUNDATION_GATE.json"
    publish_foundation_gate(
        gate_path, gate, artifact_root=tmp_path, barrier=barrier, bindings=bindings
    )
    opportunity_path = tmp_path / "OPPORTUNITY_RECEIPT.json"
    final_path = tmp_path / "COMPLETE_ATOMIC_RESULT.json"
    adapter_paths = tuple(
        tmp_path / "frontiers" / f"ADAPTER_{replicate:02d}_{arm}.json"
        for replicate in range(24)
        for arm in ADAPTER_ARMS
    )
    permit = issue_stage1b_opportunity_execution_permit(
        receipts=receipts,
        foundation_barrier=barrier,
        foundation_gate_path=gate_path,
        foundation_gate=gate,
        artifact_root=tmp_path,
        bindings=bindings,
        opportunity_receipt_path=opportunity_path,
        adapter_frontier_paths=adapter_paths,
        final_result_path=final_path,
    )
    validate_stage1b_opportunity_execution_permit(permit, bindings=bindings)
    assert permit.accepted_foundation_slots == 24
    assert permit.adapter_target_count == 72
    assert permit.opportunity_unopened is permit.adapters_unopened is permit.final_evaluation_unopened is True
    assert permit.test_only is False
    assert all(
        not str(value).startswith("TEST_ONLY_FAKE_SHA256:")
        for value in (
            permit.lineage_digest,
            permit.coordinate_manifest_sha256,
            permit.receipt_inventory_sha256,
            permit.foundation_barrier_sha256,
            permit.foundation_gate_sha256,
            permit.complete_panel_sha256,
            permit.downstream_targets_sha256,
        )
    )
    _ProductionPermitTestOnlySession.created = 0
    metrics = run_complete_pair(
        OpportunityState(0, 7, 0, 0.01, 0.0, 0.0),
        _test_opportunity_tapes(),
        permit=permit,
        foundation=lambda observations: tuple((0.0,) * 18 for _ in observations),
        session_factory=_ProductionPermitTestOnlySession,
    )
    assert metrics.rollout_count == 144
    assert _ProductionPermitTestOnlySession.created == 1

    tampered_permit = replace(permit, lineage_digest=real_digest("tampered-lineage"))
    with pytest.raises(OpportunityContractError, match="passing-foundation permit"):
        run_complete_pair(
            OpportunityState(0, 7, 0, 0.01, 0.0, 0.0),
            _test_opportunity_tapes(),
            permit=tampered_permit,
            foundation=lambda observations: (),
            session_factory=_ProductionPermitTestOnlySession,
        )
    assert _ProductionPermitTestOnlySession.created == 1

    with pytest.raises(ArtifactContractError, match="exactly 24"):
        issue_stage1b_opportunity_execution_permit(
            receipts=receipts[:-1], foundation_barrier=barrier,
            foundation_gate_path=gate_path, foundation_gate=gate,
            artifact_root=tmp_path, bindings=bindings,
            opportunity_receipt_path=opportunity_path,
            adapter_frontier_paths=adapter_paths, final_result_path=final_path,
        )
    with pytest.raises(ArtifactContractError, match="update 160 / optimizer step 1920"):
        issue_stage1b_opportunity_execution_permit(
            receipts=(replace(receipts[0], optimizer_step=1919), *receipts[1:]),
            foundation_barrier=barrier,
            foundation_gate_path=gate_path, foundation_gate=gate,
            artifact_root=tmp_path, bindings=bindings,
            opportunity_receipt_path=opportunity_path,
            adapter_frontier_paths=adapter_paths, final_result_path=final_path,
        )
    with pytest.raises(ArtifactContractError, match="coordinate differs"):
        issue_stage1b_opportunity_execution_permit(
            receipts=receipts, foundation_barrier=barrier,
            foundation_gate_path=gate_path, foundation_gate=gate,
            artifact_root=tmp_path, bindings=production_bindings("cross-lineage"),
            opportunity_receipt_path=opportunity_path,
            adapter_frontier_paths=adapter_paths, final_result_path=final_path,
        )
    with pytest.raises(ArtifactContractError, match="sealed production"):
        validate_stage1b_opportunity_execution_permit(
            tampered_permit,
            bindings=bindings,
        )

    nonpass = FoundationGate(
        GateOutcome.NONPASS,
        real_digest("foundation-nonpass-panel"),
        foundation_barrier_digest(barrier),
    )
    nonpass_path = tmp_path / "FOUNDATION_NONPASS.json"
    publish_foundation_gate(
        nonpass_path, nonpass, artifact_root=tmp_path, barrier=barrier, bindings=bindings
    )
    with pytest.raises(ArtifactContractError, match="passing atomic"):
        issue_stage1b_opportunity_execution_permit(
            receipts=receipts, foundation_barrier=barrier,
            foundation_gate_path=nonpass_path, foundation_gate=nonpass,
            artifact_root=tmp_path, bindings=bindings,
            opportunity_receipt_path=opportunity_path,
            adapter_frontier_paths=adapter_paths, final_result_path=final_path,
        )

    adapter_paths[0].parent.mkdir(parents=True, exist_ok=True)
    adapter_paths[0].write_bytes(b"unopened-state-witness")
    with pytest.raises(OpportunityContractError, match="passing-foundation permit"):
        run_complete_pair(
            OpportunityState(0, 7, 0, 0.01, 0.0, 0.0),
            _test_opportunity_tapes(),
            permit=permit,
            foundation=lambda observations: (),
            session_factory=_ProductionPermitTestOnlySession,
        )
    assert _ProductionPermitTestOnlySession.created == 1
    with pytest.raises(ArtifactContractError, match="already open"):
        issue_stage1b_opportunity_execution_permit(
            receipts=receipts, foundation_barrier=barrier,
            foundation_gate_path=gate_path, foundation_gate=gate,
            artifact_root=tmp_path, bindings=bindings,
            opportunity_receipt_path=opportunity_path,
            adapter_frontier_paths=adapter_paths, final_result_path=final_path,
        )


def test_exact_72_final_receipts_and_five_controller_barrier(tmp_path: Path) -> None:
    bindings = make_test_bindings(token="final")
    foundation_barrier, foundation_path, foundation, opportunity_path, opportunity, adapter_permit = gates(tmp_path, bindings)
    assert adapter_permit is not None
    persisted_adapter = adapter_final(0, "TREAT", bindings)
    with pytest.raises(FrontierContractError, match="adapter permit"):
        create_frontier_generation(
            tmp_path / "adapter-no-permit.json", persisted_adapter,
            artifact_root=tmp_path, bindings=bindings,
        )
    create_frontier_generation(
        tmp_path / "adapter-with-permit.json", persisted_adapter,
        artifact_root=tmp_path, bindings=bindings, adapter_permit=adapter_permit,
    )
    adapters = tuple(
        adapter_receipt_from_final(
            adapter_final(replicate, arm, bindings), bindings=bindings,
            adapter_permit=adapter_permit,
        )
        for replicate in range(24) for arm in ADAPTER_ARMS
    )
    barrier = require_final_panel_barrier(
        adapters,
        foundation_barrier=foundation_barrier,
        foundation_gate_path=foundation_path,
        foundation_gate=foundation,
        opportunity_path=opportunity_path,
        opportunity=opportunity,
        artifact_root=tmp_path,
        bindings=bindings,
    )
    assert barrier.accepted_adapters == 72
    assert barrier.controllers == ("FOUNDATION", "TREAT", "FREE", "REVERSED", "SET")
    assert issue_final_evaluation_permit(barrier, bindings=bindings).controller_count == 5
    with pytest.raises(ArtifactContractError, match="exactly 72"):
        require_final_panel_barrier(
            adapters[:-1], foundation_barrier=foundation_barrier,
            foundation_gate_path=foundation_path, foundation_gate=foundation,
            opportunity_path=opportunity_path, opportunity=opportunity,
            artifact_root=tmp_path, bindings=bindings,
        )
    duplicate = adapters[:-1] + (adapters[0],)
    with pytest.raises(ArtifactContractError, match="missing, duplicate"):
        require_final_panel_barrier(
            duplicate, foundation_barrier=foundation_barrier,
            foundation_gate_path=foundation_path, foundation_gate=foundation,
            opportunity_path=opportunity_path, opportunity=opportunity,
            artifact_root=tmp_path, bindings=bindings,
        )


def test_complete_result_publisher_enforces_realized_path(tmp_path: Path) -> None:
    bindings = make_test_bindings(token="result")
    foundation_barrier, foundation_path, foundation, opportunity_path, opportunity, adapter_permit = gates(tmp_path, bindings)
    assert adapter_permit is not None
    adapters = tuple(
        adapter_receipt_from_final(
            adapter_final(r, arm, bindings), bindings=bindings,
            adapter_permit=adapter_permit,
        )
        for r in range(24) for arm in ADAPTER_ARMS
    )
    barrier = require_final_panel_barrier(
        adapters, foundation_barrier=foundation_barrier,
        foundation_gate_path=foundation_path, foundation_gate=foundation,
        opportunity_path=opportunity_path, opportunity=opportunity,
        artifact_root=tmp_path, bindings=bindings,
    )
    panel = FinalPanelReceipt(fake("final-panel"), final_panel_barrier_digest(barrier))
    result_path = tmp_path / "result.json"
    publish_complete_result(
        result_path,
        artifact_root=tmp_path,
        bindings=bindings,
        result_code=ResultCode.NONIDENTIFIED,
        complete_inference_sha256=fake("inference"),
        foundation_gate_path=foundation_path,
        foundation_gate=foundation,
        opportunity_path=opportunity_path,
        opportunity=opportunity,
        final_barrier=barrier,
        final_panel=panel,
    )
    row = json.loads(result_path.read_text("ascii"))
    assert row["realized_path"] == "FULL_FIVE_CONTROLLER_PANEL"
    assert row["partial_values_exposed"] is False
    assert row["interpretation_included"] is False
    with pytest.raises(ArtifactContractError, match="create-only"):
        publish_complete_result(
            result_path, artifact_root=tmp_path, bindings=bindings,
            result_code=ResultCode.NONIDENTIFIED, complete_inference_sha256=fake("inference"),
            foundation_gate_path=foundation_path, foundation_gate=foundation,
            opportunity_path=opportunity_path, opportunity=opportunity,
            final_barrier=barrier, final_panel=panel,
        )


def test_prerequisite_nonpass_result_has_no_downstream_values(tmp_path: Path) -> None:
    bindings = make_test_bindings(token="nonpass-result")
    receipts = tuple(
        foundation_receipt_from_final(foundation_final(i, bindings), bindings=bindings)
        for i in range(24)
    )
    barrier = require_foundation_checkpoint_barrier(receipts, bindings)
    gate = FoundationGate(GateOutcome.NONPASS, fake("foundation-nonpass-panel"), foundation_barrier_digest(barrier))
    gate_path = tmp_path / "foundation.json"
    publish_foundation_gate(gate_path, gate, artifact_root=tmp_path, barrier=barrier, bindings=bindings)
    path = tmp_path / "result.json"
    publish_complete_result(
        path, artifact_root=tmp_path, bindings=bindings,
        result_code=ResultCode.FOUNDATION_NOT_ESTABLISHED,
        complete_inference_sha256=fake("foundation-nonpass-inference"),
        foundation_gate_path=gate_path, foundation_gate=gate,
    )
    row = json.loads(path.read_text("ascii"))
    assert row["realized_path"] == "FOUNDATION_ONLY"
    assert "opportunity_receipt_sha256" not in row
    assert "final_panel_sha256" not in row


def test_path_escape_interrupted_tampered_and_cross_lineage_rejected(tmp_path: Path) -> None:
    bindings = make_test_bindings(token="safety")
    row = foundation_final(0, bindings)
    with pytest.raises(FrontierContractError, match="escapes"):
        create_frontier_generation(
            tmp_path.parent / "escape.json", row, artifact_root=tmp_path, bindings=bindings
        )
    interrupted = tmp_path / "interrupted.json"
    interrupted.write_bytes(b'{"schema":')
    with pytest.raises(FrontierContractError, match="interrupted"):
        load_frontier_generation(interrupted, artifact_root=tmp_path, bindings=bindings)
    valid = tmp_path / "valid.json"
    create_frontier_generation(valid, row, artifact_root=tmp_path, bindings=bindings)
    payload = json.loads(valid.read_text("ascii"))
    payload["optimizer_step"] = 1919
    valid.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), "ascii")
    with pytest.raises(FrontierContractError):
        load_frontier_generation(valid, artifact_root=tmp_path, bindings=bindings)
    with pytest.raises(FrontierContractError, match="lineage"):
        row.validate(make_test_bindings(token="different"))


def test_abi2_binding_is_in_lineage_and_stale_abi1_frontier_is_rejected(tmp_path: Path) -> None:
    bindings = make_test_bindings(token="abi2")
    native = accepted_native_binding()
    assert native["native_abi"] == 2
    assert bindings.payload()["native_struct_sizes"] == native["native_struct_sizes"]
    assert bindings.payload()["native_reward_trace"] == native["native_reward_trace"]
    assert accepted_native_binding_digest() == hashlib.sha256(
        json.dumps(native, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    final = foundation_final(0, bindings)
    path = tmp_path / "frontier.json"
    create_frontier_generation(path, final, artifact_root=tmp_path, bindings=bindings)
    payload = json.loads(path.read_text("ascii"))
    payload["native_binding_sha256"] = hashlib.sha256(b"STALE_ABI1").hexdigest()
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), "ascii")
    with pytest.raises(FrontierContractError, match="ABI2"):
        load_frontier_generation(path, artifact_root=tmp_path, bindings=bindings)
