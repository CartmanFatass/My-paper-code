from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.analysis import (
    FAMILY_SIZE,
    QUANTITY_NAMES,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.audits import (
    AuditCertificate,
    AuditName,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.contracts import (
    FROZEN_LOGICAL_COUNTS,
    RESERVED_SCIENTIFIC_NAMESPACE,
    ContractError,
    TestIdentity as RSCFTestIdentity,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.evaluation import (
    expected_cell_keys,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.lifecycle import (
    LifecycleContractError,
    ResumeIdentity,
    WriteOnceConflictError,
    canonical_sha256,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.policy import (
    ACTOR_PARAMETER_SHAPES,
    CRITIC_PARAMETER_SHAPES,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.runner import (
    EVALUATION_ROSTERS,
    RSCFGateBRunner,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.snapshot import restore_snapshot


def _literal_parameters(shapes: dict[str, tuple[int, ...]], phase: int) -> dict[str, torch.Tensor]:
    result: dict[str, torch.Tensor] = {}
    cursor = phase * 101
    for name, shape in shapes.items():
        count = 1
        for size in shape:
            count *= size
        values = torch.arange(cursor, cursor + count, dtype=torch.float32)
        result[name] = (0.015 * torch.sin(values * 0.017 + phase)).reshape(shape).contiguous()
        cursor += count
    return result


@pytest.fixture(scope="module")
def runner_and_update():
    actor_parameters = _literal_parameters(ACTOR_PARAMETER_SHAPES, 1)
    critic_parameters = _literal_parameters(CRITIC_PARAMETER_SHAPES, 2)
    runner = RSCFGateBRunner(
        RSCFTestIdentity("CASE_RUNNER"),
        actor_parameters=actor_parameters,
        critic_parameters=critic_parameters,
        width=32,
    )
    update = runner.run_test_update(
        fixture_update_index=0,
        verify_reverse_order=True,
    )
    return runner, update, actor_parameters, critic_parameters


def test_runner_fails_closed_on_scientific_looking_identity_before_native_load() -> None:
    for label in ("SCIENTIFIC_RUNNER", "MODEL_CASE", "CHECKPOINT_CASE", "SEED_CASE"):
        with pytest.raises(ContractError):
            RSCFTestIdentity(label)
    with pytest.raises(ContractError):
        RSCFGateBRunner(
            RESERVED_SCIENTIFIC_NAMESPACE,  # type: ignore[arg-type]
            actor_parameters={},
            critic_parameters={},
        )


def test_full_chain_update_preserves_selector_snapshot_native_and_autograd_contracts(
    runner_and_update,
) -> None:
    runner, update, _actor_parameters, _critic_parameters = runner_and_update
    assert update.runner_identity_sha256 == runner.runner_identity_sha256
    assert update.comparator.passed
    assert update.comparator.only_algorithmic_difference == "projection_box"
    assert update.comparator.phy_projection_box == (-0.15, 0.15)
    assert update.comparator.edge_projection_box == (-1.50, 1.50)

    schedules = update.selector_schedules
    assert tuple(schedule.roster_size for schedule in schedules) == (9, 15)
    assert [schedule.counts.canonical_payload() for schedule in schedules] == [
        {
            "factual_test_episodes": 32,
            "selected_origins": 96,
            "q_entries": 320,
            "factual_reuses": 96,
            "alternative_continuations": 224,
        },
        {
            "factual_test_episodes": 32,
            "selected_origins": 96,
            "q_entries": 320,
            "factual_reuses": 96,
            "alternative_continuations": 224,
        },
    ]
    assert schedules[0].provenance_digest != schedules[1].provenance_digest
    with pytest.raises(ValueError, match="exactly 32 episodes"):
        runner.run_test_update(episodes_per_roster=1, verify_reverse_order=False)
    for schedule in schedules:
        by_pair_role: dict[tuple[int, int], dict[int, object]] = {}
        for origin in schedule.selections:
            by_pair_role.setdefault((origin.pair_index, origin.role_index), {})[origin.side] = origin
        assert all(
            sides[0].base_address_digest == sides[1].base_address_digest
            and sides[0].selected_slot + sides[1].selected_slot == 11
            for sides in by_pair_role.values()
        )

    assert update.same_snapshot_objects_for_both_arms
    assert len(update.shared_snapshot_digests) == 192
    assert all(len(digest) == 16 for digest in update.shared_snapshot_digests)
    assert len(update.factual_trace_digests) == 64
    assert len(set(update.factual_trace_digests)) == 64
    assert len(update.native_targets) == 64
    assert sum(target.q_entry_count for target in update.native_targets) == 640
    assert sum(target.factual_reuse_count for target in update.native_targets) == 192
    assert sum(target.alternative_count for target in update.native_targets) == 448
    for target in update.native_targets:
        assert target.roster_size in (9, 15)
        assert (target.q_entry_count, target.factual_reuse_count, target.alternative_count) == (10, 3, 7)
        assert target.focal_only_intervention
        assert target.factual_teammates_unchanged
        assert target.common_tape
        assert target.branch_order_independent
        assert target.factual_suffix_identity
        assert target.immutable_parameter_identity
        assert target.closed_loop_recurrence
        assert len(target.origin_snapshot_sha256) == 3
        assert len(set(target.origin_snapshot_sha256)) == 3
        assert not target.q_targets.requires_grad
        assert target.q_targets.grad_fn is None
        assert "q_targets" not in target.compact_payload()
        assert "factual_return" not in target.compact_payload()

    assert tuple(arm.arm_name for arm in update.arm_updates) == ("PHY-TRUST", "EDGE-FLEX")
    assert tuple(arm.projection_bound for arm in update.arm_updates) == (0.15, 1.50)
    for arm in update.arm_updates:
        assert arm.step.backward_calls == 1
        assert arm.step.optimizer_steps == 1
        assert arm.step.projection_after_step
        assert arm.batch_loss.episode_count == 64
        assert arm.batch_loss.equal_episode_weighting
        for graph in arm.factual_graphs:
            assert graph.roster_size in (9, 15)
            assert graph.selected_roles == (0, 1, 2)
            assert graph.factual_logprob_requires_grad
            assert graph.all_slot_entropy_requires_grad
            assert graph.critic_requires_grad
            assert not graph.q_target_requires_grad
            assert graph.no_private_target_in_actor_or_critic
            assert graph.distinct_factual_state_count == 12
            assert graph.torch_native_action_identity
            assert graph.torch_native_probability_max_abs_error < 2.0e-5
            assert graph.shared_trajectory_terminal_return
    assert update.audit_certificate.structural_valid
    assert update.audit_certificate.failed_names == ()
    counted = {entry.name: entry for entry in update.audit_certificate.evidence}
    assert counted[AuditName.Q_ENTRY_COUNT].observed_count == 640
    assert counted[AuditName.FACTUAL_REUSE_COUNT].observed_count == 192
    assert counted[AuditName.ALTERNATIVE_COUNT].observed_count == 448
    target_actor, _ = runner._fresh_arm()
    trace_batches = runner.factual_trace_batches(target_actor, schedules)
    origins = runner.selected_origin_inventory(trace_batches)
    assert len(origins) == 192
    for episode in range(64):
        episode_origins = [item for item in origins if item.episode_index == episode]
        assert len(episode_origins) == 3
        assert len({item.trajectory_digest for item in episode_origins}) == 1
        assert len({item.factual_terminal_return for item in episode_origins}) == 1
        record = trace_batches[episode // 32]
        lane = episode % 32
        for origin in episode_origins:
            role = origin.selection.role_index
            assert origin.selection.selected_slot == record.trajectory.origin_slot[lane, role]
            assert origin.selection.roster_agent_index == record.trajectory.origin_agent[lane, role]
            assert origin.snapshot_digest == record.trajectory.snapshot_digest[
                lane, origin.selection.selected_slot
            ]
    adapted = runner._trajectory_suffix_batch(trace_batches[0], role=0, intervention=None)
    for lane in range(32):
        assert adapted.origin_slot[lane] == trace_batches[0].trajectory.origin_slot[lane, 0]
        assert adapted.focal_agent[lane] == trace_batches[0].trajectory.origin_agent[lane, 0]
        assert adapted.post_gru_hidden[lane].tobytes() == trace_batches[0].trajectory.post_gru_hidden[
            lane, adapted.origin_slot[lane]
        ].tobytes()


def test_snapshot_restore_isolation_and_logical_count_metadata(runner_and_update) -> None:
    runner, update, _actor_parameters, _critic_parameters = runner_and_update
    # Rebuild one deterministic snapshot through the runner's public TEST identity.
    from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.fixtures import (
        make_test_pretransition_snapshot,
    )

    snapshot = make_test_pretransition_snapshot(runner.test_identity, roster_size=9, fixture_lane_index=3)
    before = snapshot.digest
    phy_restore = restore_snapshot(snapshot)
    edge_restore = restore_snapshot(snapshot)
    original_action = int(edge_restore["factual_joint_action"][0])
    phy_restore["factual_joint_action"][0] = 0 if original_action != 0 else 1
    assert edge_restore["factual_joint_action"][0] != phy_restore["factual_joint_action"][0]
    assert snapshot.digest == before
    assert update.logical_counts == FROZEN_LOGICAL_COUNTS.as_dict()
    assert update.logical_counts == {
        "factual_base_episodes": 1_572_864,
        "all_legal_q_entries": 15_728_640,
        "new_alternative_continuations": 11_010_048,
        "branch_environment_slot_transitions": 71_565_312,
        "base_training_environment_slots": 18_874_368,
        "evaluation_environment_slots": 1_032_192,
        "total_environment_slots": 91_471_872,
        "future_branch_learned_decisions": 726_663_168,
        "total_learned_decisions": 966_647_808,
        "full_batch_backward_calls": 24_576,
    }


def test_non_evaluable_frontier_resume_identity_and_write_once_complete_packet(
    runner_and_update, tmp_path
) -> None:
    runner, update, actor_parameters, critic_parameters = runner_and_update
    identity = runner.resume_identity(update.selector_schedules)
    origin_ids = [
        digest
        for target in update.native_targets
        for digest in target.origin_snapshot_sha256
    ]
    partial = runner.frontier(
        identity,
        expected_origin_count=192,
        completed_origin_ids=origin_ids[:96],
        audit_digest=update.audit_certificate.digest,
    )
    complete_frontier = runner.frontier(
        identity,
        expected_origin_count=192,
        completed_origin_ids=origin_ids,
        audit_digest=update.audit_certificate.digest,
    )
    assert not partial.evaluable
    assert not complete_frontier.evaluable
    complete_frontier.require_resume_successor_of(partial)
    with pytest.raises(ValueError, match="duplicate"):
        runner.frontier(
            identity,
            expected_origin_count=2,
            completed_origin_ids=("TEST_ORIGIN_A", "TEST_ORIGIN_A"),
        )
    different_identity = replace(identity, test_schedule_sha256="0" * 64)
    with pytest.raises(LifecycleContractError, match="identity mismatch"):
        complete_frontier.resume_identity.require_exact_match(different_identity)

    checkpoint = runner.checkpoint_ref(update=512)
    with pytest.raises(LifecycleContractError, match="update 512"):
        runner.checkpoint_ref(update=511)
    packet = runner.complete_packet(
        identity,
        completed_origin_ids=origin_ids,
        expected_origin_count=192,
        certificate=update.audit_certificate,
        checkpoint=checkpoint,
    )
    assert packet.evaluable
    mismatched_certificate = AuditCertificate(
        runner.test_identity.namespace,
        "TEST_DIFFERENT_SCHEDULE",
        update.audit_certificate.evidence,
    )
    with pytest.raises(ValueError, match="matching valid audit"):
        runner.complete_packet(
            identity,
            completed_origin_ids=origin_ids,
            expected_origin_count=192,
            certificate=mismatched_certificate,
            checkpoint=checkpoint,
        )
    store = runner.frontier_store(tmp_path / "TEST_FRONTIER")
    store.write_frontier("GEN0", partial)
    assert store.read_frontier("GEN0", identity) == partial
    store.write_complete_packet("PACKET0", packet)
    assert store.read_complete_packet("PACKET0", identity) == packet
    with pytest.raises(WriteOnceConflictError):
        store.write_complete_packet("PACKET0", packet)

    durable_path = tmp_path / "PROCESS_LOSS_TEST.pt"
    durable_sha = runner.save_test_checkpoint(
        durable_path,
        schedules=update.selector_schedules,
        completed_origin_ids=origin_ids,
        expected_origin_count=192,
        compact_accumulators={"completed_origins": 192, "factual_episodes": 64},
    )
    durable_bytes = durable_path.read_bytes()
    assert b"q_targets" not in durable_bytes
    assert b"factual_return" not in durable_bytes
    assert b"branch_private" not in durable_bytes
    with pytest.raises(WriteOnceConflictError):
        runner.save_test_checkpoint(
            durable_path,
            schedules=update.selector_schedules,
            completed_origin_ids=origin_ids,
            expected_origin_count=192,
            compact_accumulators={"completed_origins": 192},
        )
    restored_runner = RSCFGateBRunner(
        RSCFTestIdentity("CASE_RUNNER"),
        actor_parameters=actor_parameters,
        critic_parameters=critic_parameters,
        width=32,
        expected_native_identity=runner.native_identity,
    )
    restored = restored_runner.restore_test_checkpoint(
        durable_path, expected_identity=identity
    )
    assert restored.file_sha256 == durable_sha
    assert restored.state_sha256 == checkpoint.checkpoint_sha256
    assert restored.frontier.completed_origin_count == 192
    assert restored.compact_accumulators == {
        "completed_origins": 192,
        "factual_episodes": 64,
    }
    assert restored_runner.checkpoint_ref().checkpoint_sha256 == checkpoint.checkpoint_sha256
    assert list(tmp_path.glob("*.pending")) == []


def test_update512_evaluation_consumers_cover_all_registered_rosters(runner_and_update) -> None:
    runner, _update, _actor_parameters, _critic_parameters = runner_and_update
    checkpoint = runner.checkpoint_ref(update=512)
    for roster in EVALUATION_ROSTERS:
        audit = runner.evaluation_forward(
            checkpoint, arm_name="PHY-TRUST", roster_size=roster
        )
        assert audit.actor_probability_shape == (roster, 6)
        assert audit.critic_shape == ()
        assert audit.checkpoint_update == 512
        assert audit.no_private_target_input
        assert len(audit.compact_output_sha256) == 64
    bundle = runner._evaluation_trace_bundle(arm_name="PHY-TRUST", roster_size=6)
    assert np.array_equal(bundle.intact.active, bundle.full_rotated.active)
    for role in range(3):
        agents = np.flatnonzero(bundle.episode.roles[0, :6] == role)
        intact_support = bundle.intact.legal_probabilities[:, :, agents] > 0.0
        rotated_support = bundle.full_rotated.legal_probabilities[:, :, agents] > 0.0
        assert np.array_equal(intact_support, rotated_support)
    np.testing.assert_array_equal(
        bundle.shadow.legal_probabilities[:, 0],
        bundle.full_rotated.legal_probabilities[:, 0],
    )
    assert not np.array_equal(
        bundle.shadow.legal_probabilities[:, 1:],
        bundle.full_rotated.legal_probabilities[:, 1:],
    )
    assert not np.array_equal(
        bundle.shadow.legal_probabilities,
        bundle.intact.legal_probabilities,
    )


def test_complete_evaluation_and_exact_28_quantity_analyzer_plumbing(runner_and_update) -> None:
    runner, update, _actor_parameters, _critic_parameters = runner_and_update
    checkpoint = runner.checkpoint_ref(update=512)
    base_identity = runner.resume_identity(update.selector_schedules)
    origin_ids = tuple(
        digest
        for target in update.native_targets
        for digest in target.origin_snapshot_sha256
    )
    panels = []
    certificates = []
    for block in range(24):
        test_id = f"TEST_BLOCK_{block:02d}"
        certificate = AuditCertificate(
            runner.test_identity.namespace,
            test_id,
            update.audit_certificate.evidence,
        )
        identity = ResumeIdentity(
            namespace=base_identity.namespace,
            test_schedule_id=test_id,
            test_schedule_sha256=canonical_sha256({"base": base_identity.test_schedule_sha256, "block": block}),
            runner_identity_sha256=base_identity.runner_identity_sha256,
            selector_identity_sha256=base_identity.selector_identity_sha256,
        )
        packet = runner.complete_packet(
            identity,
            completed_origin_ids=origin_ids,
            expected_origin_count=len(origin_ids),
            certificate=certificate,
            checkpoint=checkpoint,
        )
        panel = runner.generate_test_evaluation_panel(packet, certificate)
        assert set(panel.by_key) == set(expected_cell_keys())
        assert all(cell.episode_count == 256 for cell in panel.cells)
        panels.append(panel)
        certificates.append(certificate)
    analysis = runner.analyze_test_panels(panels, certificates)
    assert len(analysis.intervals) == FAMILY_SIZE == 28
    assert set(analysis.intervals) == set(QUANTITY_NAMES)
    assert analysis.structural_failures == ()
    assert len(analysis.digest) == 64
