"""Tests for the MSSR support-native P runtime objects (Seq 12 build).

Object 1: ``LifecycleRecord.partner_interaction_history`` (owner-private P field).
Object 3: ``EventCommitmentPolicy.first_logits`` (pre-recurrence action head).

Two load-bearing properties are pinned here:

* the objects are REAL -- a genuine pre-recurrence head that reads historical P,
  and a frozen provenance-bound owner-private field with no public setter; and
* building them leaves a DISABLED policy byte-identical to the shipped one, so
  the existing FOLR / continuous-roster runs are unperturbed.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
import torch

from ha_ctse_process import variable_roster_event_types as vt
from ha_ctse_process.variable_roster_event import VariableRosterEventCore
from ha_ctse_process.variable_roster_event_models import EventCommitmentPolicy


def _policy(partner_first_action: bool) -> EventCommitmentPolicy:
    torch.manual_seed(17)
    return EventCommitmentPolicy(
        obs_dim=6,
        n_skills=4,
        member_hidden_dim=12,
        high_hidden_dim=10,
        skill_embedding_dim=5,
        partner_first_action=partner_first_action,
    )


# --- Object 1: owner-private, provenance-bound P field -----------------------


def test_lifecycle_record_has_owner_private_partner_field():
    names = {f.name for f in dataclasses.fields(vt.LifecycleRecord)}
    assert "partner_interaction_history" in names


def test_partner_field_defaults_to_none():
    # Every existing constructor omits the field, so P is absent unless the
    # registered transition writes it.
    record = vt.LifecycleRecord(
        lifecycle_key="k",
        status="ACTIVE",
        membership_epoch=0,
        low_actor_hidden=np.zeros(1, np.float32),
        low_critic_hidden=np.zeros(1, np.float32),
        high_hidden=np.zeros(1, np.float32),
        active_skill=None,
        skill_active_age=0,
        active_gap_remaining=None,
        last_policy_event_time=None,
        open_event_trace=None,
        policy_version=0,
    )
    assert record.partner_interaction_history is None


def test_partner_history_is_frozen_and_provenance_bound():
    row = vt.PartnerInteractionRow(
        episode_id=7,
        owner_lifecycle_key="a",
        membership_epoch=2,
        partner_lifecycle_key="b",
        event_index=3,
        prior_p=0.0,
        payload=0.5,
        next_p=0.5,
        writer_policy_version=1,
    )
    history = vt.PartnerInteractionHistory(current_p=0.5, rows=(row,))
    # No public setter: the value cannot be injected by assignment.
    with pytest.raises(dataclasses.FrozenInstanceError):
        history.current_p = 1.0  # type: ignore[misc]
    # Every write carries its full provenance tuple.
    assert history.rows[0].partner_lifecycle_key == "b"
    assert history.rows[0].episode_id == 7
    assert history.rows[0].writer_policy_version == 1


# --- Object 3: pre-recurrence action head ------------------------------------


def test_disabled_policy_is_byte_identical_to_shipped():
    # Building with partner_first_action=False must add no parameters and must
    # not perturb initialization: it equals a policy built with no kwarg at all.
    torch.manual_seed(17)
    baseline = EventCommitmentPolicy(
        obs_dim=6,
        n_skills=4,
        member_hidden_dim=12,
        high_hidden_dim=10,
        skill_embedding_dim=5,
    )
    disabled = _policy(False)
    baseline_state, disabled_state = baseline.state_dict(), disabled.state_dict()
    assert set(baseline_state) == set(disabled_state)  # no new parameters
    for key in baseline_state:
        assert torch.equal(baseline_state[key], disabled_state[key]), key


def test_enabled_policy_adds_only_the_first_action_head():
    disabled, enabled = _policy(False), _policy(True)
    extra = set(enabled.state_dict()) - set(disabled.state_dict())
    assert extra == {
        "first_decoder.0.weight",
        "first_decoder.0.bias",
        "first_head.weight",
        "first_head.bias",
    }


def test_first_logits_is_genuinely_pre_recurrence():
    # The honest check-3 property: first_logits are NOT reproducible from the
    # post-recurrence hidden value, so they do not depend on the GRU update.
    model = _policy(True)
    torch.manual_seed(23)
    member = torch.randn(model.member_hidden_dim)
    summary = torch.randn(model.summary_dim)
    pre_hidden = torch.randn(model.high_hidden_dim)
    with torch.no_grad():
        logits, new_hidden = model.first_logits(member, summary, pre_hidden)
        reconstructed = model.skill_head(
            model.decoder_hidden(
                torch.cat(
                    (new_hidden.reshape(1, -1), summary.reshape(1, -1)), dim=-1
                )
            )
        ).squeeze(0)
    assert not torch.equal(logits, reconstructed)


def test_first_logits_reads_historical_p():
    # P genuinely enters the action: a different historical P changes the logits.
    model = _policy(True)
    torch.manual_seed(23)
    member = torch.randn(model.member_hidden_dim)
    summary = torch.randn(model.summary_dim)
    pre_hidden = torch.randn(model.high_hidden_dim)
    with torch.no_grad():
        low, _ = model.first_logits(member, summary, pre_hidden, partner_p=0.0)
        high, _ = model.first_logits(member, summary, pre_hidden, partner_p=1.0)
    assert not torch.equal(low, high)


def test_first_logits_requires_the_flag():
    model = _policy(False)
    with pytest.raises(RuntimeError):
        model.first_logits(
            torch.zeros(model.member_hidden_dim),
            torch.zeros(model.summary_dim),
            torch.zeros(model.high_hidden_dim),
        )


# --- Object 2: registered partner-interaction transition ---------------------


def _enabled_core() -> VariableRosterEventCore:
    core = VariableRosterEventCore(
        architecture_mode="f1",
        obs_dim=6,
        critic_member_dim=6,
        critic_global_dim=3,
        n_skills=4,
        action_dim=1,
        rng_episode_id=99,
        partner_interaction_enabled=True,
    )
    core.policy_version = 3
    return core


def _record(key: str) -> vt.LifecycleRecord:
    return vt.LifecycleRecord(
        lifecycle_key=key,
        status="ACTIVE",
        membership_epoch=1,
        low_actor_hidden=np.zeros(1, np.float32),
        low_critic_hidden=np.zeros(1, np.float32),
        high_hidden=np.zeros(4, np.float32),
        active_skill=0,
        skill_active_age=0,
        active_gap_remaining=None,
        last_policy_event_time=None,
        open_event_trace=None,
        policy_version=3,
    )


def test_partner_transition_writes_genuine_cross_member_p():
    core = _enabled_core()
    record = _record("i")
    active_keys = ["i", "j", "k"]
    active_observations = torch.tensor(
        [
            [1.0, 0.0, 0.0, 0.0],  # i -- self (owner_row), excluded
            [0.9, 0.1, 0.0, 0.0],  # j -- strongest observation alignment with i
            [-1.0, 0.0, 0.0, 0.0],  # k -- anti-aligned
        ]
    )
    core._write_partner_interaction(
        record=record,
        owner_key="i",
        owner_row=0,
        active_keys=active_keys,
        active_observations=active_observations,
        event_index=5,
    )
    history = record.partner_interaction_history
    assert history is not None
    row = history.rows[-1]
    # The partner is the genuine strongest interactor j -- not self, not k.
    assert row.partner_lifecycle_key == "j"
    # Every write is bound to its full provenance tuple.
    assert row.episode_id == 99
    assert row.owner_lifecycle_key == "i"
    assert row.membership_epoch == 1
    assert row.event_index == 5
    assert row.writer_policy_version == 3
    assert -1.0 <= history.current_p <= 1.0


def test_partner_p_depends_on_partner_observation():
    core = _enabled_core()
    owner_obs = torch.tensor([1.0, 0.0, 0.0, 0.0])

    def run(partner_obs: torch.Tensor) -> float:
        record = _record("i")
        core._write_partner_interaction(
            record=record,
            owner_key="i",
            owner_row=0,
            active_keys=["i", "j"],
            active_observations=torch.stack([owner_obs, partner_obs]),
            event_index=0,
        )
        return record.partner_interaction_history.current_p

    # A genuine i-depends-on-j signal: a different partner observation changes P.
    assert run(torch.tensor([1.0, 0.0, 0.0, 0.0])) != run(
        torch.tensor([-1.0, 0.0, 0.0, 0.0])
    )


def test_partner_transition_is_deterministic():
    core = _enabled_core()
    owner_obs = torch.tensor([0.5, 0.5, 0.0, 0.0])
    partner_obs = torch.tensor([0.3, 0.4, 0.1, 0.0])

    def run() -> float:
        record = _record("i")
        core._write_partner_interaction(
            record=record,
            owner_key="i",
            owner_row=0,
            active_keys=["i", "j"],
            active_observations=torch.stack([owner_obs, partner_obs]),
            event_index=0,
        )
        return record.partner_interaction_history.current_p

    assert run() == run()  # no RNG consumed


def test_solitary_owner_has_no_partner_write():
    core = _enabled_core()
    record = _record("i")
    core._write_partner_interaction(
        record=record,
        owner_key="i",
        owner_row=0,
        active_keys=["i"],
        active_observations=torch.zeros(1, 4),
        event_index=0,
    )
    assert record.partner_interaction_history is None


def test_partner_p_accumulates_as_a_provenance_ledger():
    core = _enabled_core()
    record = _record("i")
    owner_obs = torch.tensor([1.0, 0.0, 0.0, 0.0])
    partner_obs = torch.tensor([1.0, 0.0, 0.0, 0.0])
    observations = torch.stack([owner_obs, partner_obs])
    for event_index in range(3):
        core._write_partner_interaction(
            record=record,
            owner_key="i",
            owner_row=0,
            active_keys=["i", "j"],
            active_observations=observations,
            event_index=event_index,
        )
    history = record.partner_interaction_history
    assert len(history.rows) == 3
    # Each write's prior_p equals the previous write's next_p -- a real ledger.
    assert history.rows[1].prior_p == history.rows[0].next_p
    assert history.rows[2].prior_p == history.rows[1].next_p
    assert history.current_p == history.rows[2].next_p
