"""Tests for the MSSR support-native P reachability proof.

The proof reports ABSENT on this repository.  A checker that can *only* report
ABSENT proves nothing, so the load-bearing test here is
``test_ordering_check_passes_on_a_genuine_preaction_model``: a positive control
with a model whose logits really are computed before recurrence, which the same
check must accept.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from experiments.candidates.vsp_06_mssr import support_native_p_reachability as pr


class _PreactionStub(nn.Module):
    """A model that satisfies first_logits_tick < recurrent_update_tick.

    The logits are produced from the PRE-recurrence hidden state; the recurrent
    update still happens and still returns a new hidden value, but the action
    distribution does not depend on it.
    """

    def __init__(self, *, member_hidden_dim=12, high_hidden_dim=10, n_skills=4):
        super().__init__()
        self.member_hidden_dim = member_hidden_dim
        self.high_hidden_dim = high_hidden_dim
        self.summary_dim = member_hidden_dim + 1
        self.n_skills = n_skills
        self.high_rnn = nn.GRUCell(
            member_hidden_dim + self.summary_dim, high_hidden_dim
        )
        self.decoder_hidden = nn.Sequential(
            nn.Linear(high_hidden_dim + self.summary_dim, high_hidden_dim),
            nn.GELU(),
        )
        self.skill_head = nn.Linear(high_hidden_dim, n_skills)

    def logits(self, member_embedding, selected_summary, pre_hidden):
        member_embedding = member_embedding.reshape(1, self.member_hidden_dim)
        selected_summary = selected_summary.reshape(1, self.summary_dim)
        pre_hidden = pre_hidden.reshape(1, self.high_hidden_dim)
        # Logits FIRST, from the pre-recurrence hidden state.
        logits = self.skill_head(
            self.decoder_hidden(torch.cat((pre_hidden, selected_summary), dim=-1))
        ).squeeze(0)
        # Recurrence afterwards.
        new_hidden = self.high_rnn(
            torch.cat((member_embedding, selected_summary), dim=-1), pre_hidden
        )
        return logits, new_hidden.squeeze(0)


def test_ordering_check_passes_on_a_genuine_preaction_model():
    """Positive control: the check must ACCEPT a real pre-recurrence path."""
    torch.manual_seed(5)
    result = pr.preaction_ordering(model=_PreactionStub())
    assert result.passed, result.detail


def test_ordering_check_fails_on_the_actual_runtime_policy():
    """And must REJECT the shipped policy, which reads post-recurrence hidden."""
    result = pr.preaction_ordering()
    assert not result.passed
    assert "post-recurrence" in result.detail


def test_partner_vocabulary_uses_word_boundaries():
    """Unbounded matching reports ~100 hits here, all inside exception names."""
    import re

    noise = "raise TypeError; except BrokenPipeError: pass  # KeyError"
    for token in pr.PARTNER_VOCABULARY:
        assert not re.findall(rf"\b{token}", noise, flags=re.IGNORECASE), token
    assert re.findall(r"\bpartner", "partner_interaction_cell", flags=re.IGNORECASE)


def test_owner_private_state_has_no_partner_field():
    result = pr.owner_private_state_inventory()
    assert not result.passed
    assert "high_hidden" in result.detail, "the inventory must be real, not empty"


def test_host_runtime_has_no_partner_transition():
    result = pr.registered_partner_transition()
    assert not result.passed


def test_host_runtime_files_all_exist():
    """If a host file were renamed the scan would silently find nothing."""
    result = pr.registered_partner_transition()
    assert result.detail  # raises FileNotFoundError inside if a file is missing


def test_terminal_is_absent_with_all_three_checks_failing():
    report = pr.proof()
    assert report["terminal"] == "MSSR_P_SUPPORT_NATIVE_ABSENT"
    assert not any(check["passed"] for check in report["checks"].values())
    assert "licenses no scientific claim" in report["scope"]
