"""Focused wrong-implementation tests for VSP06-A1."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.vsp_06_mssr import joint_production_binding as mssr
from ha_ctse_process.variable_roster_event import (
    MSSR_JOINT_PRODUCTION_ACTION_PATH,
    ORDINARY_PRODUCTION_ACTION_PATH,
    PRODUCTION_ACTION_PATHS,
    VariableRosterEventCore,
    _pack_event_high_replay,
    _replay_packed_event_token,
)
from ha_ctse_process.variable_roster_event_models import EventCommitmentPolicy
from ha_ctse_process.variable_roster_event_types import (
    ClosedEventRow,
    LifecycleRecord,
    PartnerInteractionHistory,
    PartnerInteractionRow,
)


HAS_REGISTERED_FACTORIES = all(
    callable(item) for item in mssr._registered_factories()
)
requires_factories = pytest.mark.skipif(
    not HAS_REGISTERED_FACTORIES,
    reason="integrated registered MSSR production factories are not in this ticket",
)


def _ordinary_core(*, explicit: bool) -> VariableRosterEventCore:
    torch.manual_seed(177)
    kwargs = {}
    if explicit:
        kwargs["production_action_path"] = ORDINARY_PRODUCTION_ACTION_PATH
    return VariableRosterEventCore(
        architecture_mode="f1",
        obs_dim=3,
        critic_member_dim=3,
        critic_global_dim=2,
        n_skills=3,
        action_dim=1,
        member_hidden_dim=8,
        high_hidden_dim=6,
        skill_embedding_dim=4,
        runtime_mode="supplied_executor",
        **kwargs,
    )


def _lifecycle(key: str, *, epoch: int = 1) -> LifecycleRecord:
    return LifecycleRecord(
        lifecycle_key=key,
        status="ACTIVE",
        membership_epoch=epoch,
        low_actor_hidden=np.empty(0, dtype=np.float32),
        low_critic_hidden=np.empty(0, dtype=np.float32),
        high_hidden=np.zeros(6, dtype=np.float32),
        active_skill=0,
        skill_active_age=0,
        active_gap_remaining=1,
        last_policy_event_time=0,
        open_event_trace=None,
        policy_version=3,
    )


def _provenance_fixture() -> tuple[
    VariableRosterEventCore, LifecycleRecord, tuple[PartnerInteractionRow, ...]
]:
    core = VariableRosterEventCore(
        architecture_mode="f1",
        obs_dim=3,
        critic_member_dim=3,
        critic_global_dim=2,
        n_skills=3,
        action_dim=1,
        member_hidden_dim=8,
        high_hidden_dim=6,
        skill_embedding_dim=4,
        runtime_mode="supplied_executor",
        partner_interaction_enabled=True,
        rng_episode_id=7,
    )
    core.policy_version = 3
    owner = _lifecycle("owner")
    partner = _lifecycle("partner")
    first_next = float(np.clip(0.8 * 0.0 + 0.2 * 0.5, -1.0, 1.0))
    second_next = float(np.clip(0.8 * first_next + 0.2 * -0.5, -1.0, 1.0))
    rows = (
        PartnerInteractionRow(7, "owner", 0, "partner", 0, 0.0, 0.5, first_next, 1),
        PartnerInteractionRow(
            7, "owner", 1, "partner", 1, first_next, -0.5, second_next, 2
        ),
    )
    owner.partner_interaction_history = PartnerInteractionHistory(second_next, rows)
    core.records = {"owner": owner, "partner": partner}
    assert core._authenticated_partner_p(owner) == second_next
    return core, owner, rows


def _install_rows(
    owner: LifecycleRecord,
    rows: tuple[PartnerInteractionRow, ...],
    *,
    current_p: float | None = None,
) -> None:
    tail = rows[-1].next_p if current_p is None else current_p
    owner.partner_interaction_history = PartnerInteractionHistory(tail, rows)


def _complete_evidence() -> dict[str, bool]:
    return {name: True for name in mssr.RETAINED_EVIDENCE_FIELDS}


def _mssr_replay_fixture():
    evidence, _owner, core, _right = mssr._factory_triplet()
    assert evidence == {
        "factory_available": True,
        "factory_identity": True,
        "path_bound": True,
        "factory_error": None,
    }
    history = mssr._drive_history(core, mssr.POSITIVE_HISTORY_SOURCE_OBS)
    row = core.high_ledger[-1]
    assert row.owner_lifecycle_key == mssr.OWNER
    retained_p = float(history["historical_write"]["next_p"])
    assert row.authenticated_partner_p == retained_p
    closed = ClosedEventRow(
        lifecycle_key=row.owner_lifecycle_key,
        membership_epoch=row.membership_epoch,
        policy_version=row.policy_version,
        actor_valid=True,
        start_time=row.physical_event_time,
        end_time=row.physical_event_time + 1,
        elapsed_physical_time=1,
        discounted_reward=0.0,
        old_value=row.old_owner_value,
        bootstrap_value=0.0,
        bootstrap_discount=0.0,
        return_target=row.old_owner_value,
        old_log_probability=row.old_token_log_probability,
        token_ledger_index=len(core.high_ledger) - 1,
        boundary_kind="ORDINARY_BOUNDARY",
    )
    packed = _pack_event_high_replay(
        core,
        closed,
        row,
        normalized_advantage=0.0,
        raw_advantage=0.0,
    )
    return core, row, packed


def test_registered_probe_constructs_factories_but_executes_no_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    def forbidden(*args, **kwargs):
        raise AssertionError("registered probe executed a policy call")

    monkeypatch.setattr(EventCommitmentPolicy, "logits", forbidden)
    monkeypatch.setattr(EventCommitmentPolicy, "first_logits", forbidden)
    result = mssr.registered_probe()
    expected = mssr.NO_WITNESS if HAS_REGISTERED_FACTORIES else mssr.NO_SINGLE_PATH
    assert result["branch"] == expected
    assert set(result["activity_counts"].values()) == {0}
    assert result["focused_dynamic_witness"]["executed_by_registered_probe"] is False


def test_action_path_registry_has_no_hidden_second_mssr_route():
    assert PRODUCTION_ACTION_PATHS == (
        ORDINARY_PRODUCTION_ACTION_PATH,
        MSSR_JOINT_PRODUCTION_ACTION_PATH,
    )


def test_default_runtime_parameter_graph_and_architecture_state_are_unchanged():
    default = _ordinary_core(explicit=False)
    explicit = _ordinary_core(explicit=True)
    assert default.architecture_state() == explicit.architecture_state()
    assert "production_action_path" not in default.architecture_state()
    for key, tensor in default.commitment_model.state_dict().items():
        assert torch.equal(tensor, explicit.commitment_model.state_dict()[key]), key


@requires_factories
def test_factory_identity_and_joint_path_are_real_production_objects():
    evidence, owner, left, right = mssr._factory_triplet()
    assert evidence["factory_available"] is True
    assert evidence["factory_identity"] is True
    assert evidence["path_bound"] is True
    assert left.commitment_model is right.commitment_model is owner.commitment_model
    assert left.production_action_path == MSSR_JOINT_PRODUCTION_ACTION_PATH


def test_selective_partition_is_consumed_not_merely_labeled():
    torch.manual_seed(17)
    policy = EventCommitmentPolicy(
        obs_dim=3,
        n_skills=3,
        member_hidden_dim=3,
        high_hidden_dim=2,
        skill_embedding_dim=2,
        partner_first_action=True,
    )
    with torch.no_grad():
        linear = policy.first_decoder[0]
        linear.weight.zero_()
        linear.bias.fill_(1.0)
        linear.weight[0, 0] = 1.0
        linear.weight[1, policy.high_hidden_dim] = 1.0
        linear.weight[2, -1] = 1.0
        policy.first_head.weight.copy_(torch.eye(3))
        policy.first_head.bias.zero_()
    member = torch.zeros(policy.member_hidden_dim)
    summary = torch.zeros(policy.summary_dim)
    hidden = torch.zeros(policy.high_hidden_dim)

    def logits(*, s: float = 0.0, p: float = 0.0, f: float = 0.0):
        changed_summary = summary.clone()
        changed_summary[0] = s
        changed_hidden = hidden.clone()
        changed_hidden[0] = f
        partition = policy.selective_spf_partition(changed_summary, changed_hidden, p)
        return policy.first_logits(
            member, summary, hidden, partition=partition
        )[0]

    baseline = logits()
    assert not torch.equal(baseline, logits(s=1.0))
    assert not torch.equal(baseline, logits(p=1.0))
    assert not torch.equal(baseline, logits(f=1.0))


@requires_factories
def test_all_mssr_replay_paths_reuse_retained_p_and_first_action_head(
    monkeypatch: pytest.MonkeyPatch,
):
    core, row, packed = _mssr_replay_fixture()
    first_calls: list[float] = []
    original_first_logits = EventCommitmentPolicy.first_logits

    def tracked_first_logits(self, *args, **kwargs):
        partition = kwargs["partition"]
        first_calls.append(float(partition.partner_history.detach().cpu().item()))
        return original_first_logits(self, *args, **kwargs)

    def forbidden_ordinary_logits(*_args, **_kwargs):
        raise AssertionError("MSSR replay called the ordinary post-recurrence head")

    monkeypatch.setattr(EventCommitmentPolicy, "first_logits", tracked_first_logits)
    monkeypatch.setattr(EventCommitmentPolicy, "logits", forbidden_ordinary_logits)

    probabilities = core.replay_token_distribution(row, summary_source="working")
    replay_logp, _value, _entropy = core.replay_event_token(row)
    packed_logp, _packed_value, _packed_entropy = _replay_packed_event_token(packed)

    assert probabilities == pytest.approx(row.direct_probabilities, abs=1.0e-7)
    assert float(replay_logp.detach().cpu()) == pytest.approx(
        row.old_token_log_probability, abs=1.0e-7
    )
    assert float(packed_logp.detach().cpu()) == pytest.approx(
        row.old_token_log_probability, abs=1.0e-7
    )
    expected_tensor_p = float(np.float32(row.authenticated_partner_p))
    assert first_calls == [expected_tensor_p] * 3


@requires_factories
@pytest.mark.parametrize(
    "invalid_p",
    [None, np.nan, np.inf, -1.0001, 1.0001, True, "0.25"],
)
def test_mssr_replay_fails_closed_without_valid_retained_pre_token_p(invalid_p):
    core, row, _packed = _mssr_replay_fixture()
    invalid_row = replace(row, authenticated_partner_p=invalid_p)
    closed = ClosedEventRow(
        lifecycle_key=invalid_row.owner_lifecycle_key,
        membership_epoch=invalid_row.membership_epoch,
        policy_version=invalid_row.policy_version,
        actor_valid=True,
        start_time=invalid_row.physical_event_time,
        end_time=invalid_row.physical_event_time + 1,
        elapsed_physical_time=1,
        discounted_reward=0.0,
        old_value=invalid_row.old_owner_value,
        bootstrap_value=0.0,
        bootstrap_discount=0.0,
        return_target=invalid_row.old_owner_value,
        old_log_probability=invalid_row.old_token_log_probability,
        token_ledger_index=len(core.high_ledger) - 1,
        boundary_kind="ORDINARY_BOUNDARY",
    )
    invalid_packed = _pack_event_high_replay(
        core,
        closed,
        invalid_row,
        normalized_advantage=0.0,
        raw_advantage=0.0,
    )

    operations = (
        lambda: core.replay_token_distribution(
            invalid_row, summary_source="working"
        ),
        lambda: core.replay_event_token(invalid_row),
        lambda: _replay_packed_event_token(invalid_packed),
    )
    for operation in operations:
        with pytest.raises(ValueError, match="retained pre-token authenticated P"):
            operation()


@requires_factories
def test_legal_histories_use_deterministic_kernel_action_without_teacher_action():
    result = mssr.build_legal_matched_support_witness()
    assert result["branch"] == mssr.ESTABLISHED
    accepted = mssr.registered_probe(result)
    assert accepted["branch"] == mssr.ESTABLISHED
    assert set(accepted["activity_counts"].values()) == {0}
    assert result["evidence"]["current_non_p_context_byte_equal"] is True
    assert result["evidence"]["authenticated_p_byte_different"] is True
    for side in ("left", "right"):
        decision = result[side]["decision"]
        assert decision["teacher_action_used"] is False
        assert decision["selected_action"] == decision["kernel_argmax"]
        assert len(decision["full_masked_logits"]) == len(
            decision["full_probabilities"]
        )
        assert decision["action_from_full_kernel"] is True


def test_authoritative_five_branch_precedence_is_fail_closed():
    evidence = _complete_evidence()
    assert mssr.classify_retained_evidence(evidence) == mssr.ESTABLISHED
    assert mssr.classify_retained_evidence({}) == mssr.INVALID

    invalid = dict(evidence, package_valid=False)
    assert mssr.classify_retained_evidence(invalid) == mssr.INVALID
    no_factory = dict(evidence, factory_available=False)
    assert mssr.classify_retained_evidence(no_factory) == mssr.NO_SINGLE_PATH
    no_binding = dict(evidence, path_bound=False)
    assert mssr.classify_retained_evidence(no_binding) == mssr.NO_SINGLE_PATH
    no_support = dict(evidence, legal_histories=False)
    assert mssr.classify_retained_evidence(no_support) == mssr.NO_WITNESS
    same_p = dict(evidence, authenticated_p_byte_different=False)
    assert mssr.classify_retained_evidence(same_p) == mssr.NO_WITNESS
    bad_provenance = dict(evidence, provenance_authenticated=False)
    assert (
        mssr.classify_retained_evidence(bad_provenance)
        == mssr.PROVENANCE_OR_CONTEXT_FAILURE
    )
    bad_context = dict(evidence, current_non_p_context_byte_equal=False)
    assert (
        mssr.classify_retained_evidence(bad_context)
        == mssr.PROVENANCE_OR_CONTEXT_FAILURE
    )
    bad_action = dict(evidence, action_from_full_kernel=False)
    assert mssr.classify_retained_evidence(bad_action) == mssr.INVALID


def test_registered_probe_rejects_unbound_or_wrong_candidate_receipt():
    result = mssr.registered_probe(
        {
            "raw_output_binding": "wrong.binding",
            "candidate": mssr.CANDIDATE,
            "evidence": _complete_evidence(),
        }
    )
    assert result["branch"] == mssr.INVALID


def test_provenance_rejects_negative_and_unknown_identity_fields():
    core, owner, rows = _provenance_fixture()
    bad = replace(rows[0], membership_epoch=-1)
    _install_rows(owner, (bad, rows[1]))
    with pytest.raises(ValueError, match="identity"):
        core._authenticated_partner_p(owner)
    bad = replace(rows[0], event_index=-1)
    _install_rows(owner, (bad, rows[1]))
    with pytest.raises(ValueError, match="identity"):
        core._authenticated_partner_p(owner)
    bad = replace(rows[0], writer_policy_version=-1)
    _install_rows(owner, (bad, rows[1]))
    with pytest.raises(ValueError, match="identity"):
        core._authenticated_partner_p(owner)
    bad = replace(rows[0], partner_lifecycle_key="missing")
    _install_rows(owner, (bad, rows[1]))
    with pytest.raises(ValueError, match="identity"):
        core._authenticated_partner_p(owner)


def test_provenance_rejects_nonmonotonic_epoch_event_and_writer_order():
    core, owner, rows = _provenance_fixture()
    bad_first = replace(rows[0], membership_epoch=1)
    bad_second = replace(rows[1], membership_epoch=0)
    _install_rows(owner, (bad_first, bad_second))
    with pytest.raises(ValueError, match="identity"):
        core._authenticated_partner_p(owner)
    bad_second = replace(rows[1], event_index=0)
    _install_rows(owner, (rows[0], bad_second))
    with pytest.raises(ValueError, match="identity"):
        core._authenticated_partner_p(owner)
    bad_first = replace(rows[0], writer_policy_version=2)
    bad_second = replace(rows[1], writer_policy_version=1)
    _install_rows(owner, (bad_first, bad_second))
    with pytest.raises(ValueError, match="identity"):
        core._authenticated_partner_p(owner)


def test_provenance_rejects_payload_range_transition_equation_and_tail():
    core, owner, rows = _provenance_fixture()
    bad = replace(rows[0], payload=1.5)
    _install_rows(owner, (bad, rows[1]))
    with pytest.raises(ValueError, match="identity"):
        core._authenticated_partner_p(owner)
    bad = replace(rows[0], next_p=rows[0].next_p + 0.01)
    _install_rows(owner, (bad, rows[1]))
    with pytest.raises(ValueError, match="transition equation"):
        core._authenticated_partner_p(owner)
    _install_rows(owner, rows, current_p=rows[-1].next_p + 0.01)
    with pytest.raises(ValueError, match="provenance tail"):
        core._authenticated_partner_p(owner)


def test_checkpoint_codec_corruption_is_rejected_before_action_use():
    core, owner, rows = _provenance_fixture()
    state = core._record_to_state(owner)
    state["partner_interaction_history"] = PartnerInteractionHistory(
        current_p=rows[-1].next_p,
        rows=(rows[0], replace(rows[1], next_p=rows[1].next_p + 0.2)),
    )
    restored = core._record_from_state(state)
    core.records["owner"] = restored
    with pytest.raises(ValueError, match="transition equation"):
        core._authenticated_partner_p(restored)
