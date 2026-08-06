"""Tests for the MSSR support-native P reachability proof.

After the loop-1 build (2026-08-06) the three objects this proof maps EXIST, so
the proof reports ``MSSR_P_SUPPORT_NATIVE_PRESENT`` by genuine construction.
These tests pin the PRESENT state and keep the load-bearing safety facts: the
default production action path is still post-recurrence (FOLR-safe), and the
checks accept the real objects (not a decoy) while the interface still licenses
no scientific claim.
"""

from __future__ import annotations

import re

from experiments.candidates.vsp_06_mssr import support_native_p_reachability as pr


def test_ordering_check_accepts_the_mssr_first_action_head():
    """Check 3 passes: an MSSR-enabled policy exposes a pre-recurrence action."""
    result = pr.preaction_ordering()
    assert result.passed, result.detail


def test_default_logits_still_reads_post_recurrence():
    """FOLR safety: the default action path is unchanged and post-recurrence.

    Check 3 verifies both facts; its detail must report the default path reading
    the post-recurrence hidden value, or the check would be passing by degrading
    the default rather than by adding a genuine pre-recurrence head.
    """
    result = pr.preaction_ordering()
    assert "baseline=True" in result.detail


def test_partner_vocabulary_uses_word_boundaries():
    """Unbounded matching reports ~100 hits here, all inside exception names."""
    noise = "raise TypeError; except BrokenPipeError: pass  # KeyError"
    for token in pr.PARTNER_VOCABULARY:
        assert not re.findall(rf"\b{token}", noise, flags=re.IGNORECASE), token
    assert re.findall(r"\bpartner", "partner_interaction_cell", flags=re.IGNORECASE)


def test_owner_private_state_has_partner_field():
    result = pr.owner_private_state_inventory()
    assert result.passed, result.detail
    assert "partner_interaction_history" in result.detail


def test_host_runtime_has_partner_transition():
    result = pr.registered_partner_transition()
    assert result.passed, result.detail


def test_host_runtime_files_all_exist():
    """If a host file were renamed the scan would silently find nothing."""
    result = pr.registered_partner_transition()
    assert result.detail  # raises FileNotFoundError inside if a file is missing


def test_terminal_is_present_with_all_three_checks_passing():
    report = pr.proof()
    assert report["terminal"] == "MSSR_P_SUPPORT_NATIVE_PRESENT"
    assert all(check["passed"] for check in report["checks"].values())
    # Existence only: the interface still licenses no scientific claim.
    assert "licenses no scientific claim" in report["scope"]
