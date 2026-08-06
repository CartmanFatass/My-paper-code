"""Tests for the VSP-02 duration-exposure interface proof.

The two interventions control each other. ``duration_is_owner_selected`` reports
a null -- the gap does not move when the action changes -- and that null is only
meaningful because ``duration_is_exogenous`` shows the same measurement *can*
move the gap when the RNG changes. ``test_the_null_is_not_a_dead_measurement``
pins that relationship explicitly, so the proof cannot silently degrade into a
checker that always reports "no effect".
"""

from __future__ import annotations

from experiments.candidates.vsp_02 import duration_exposure_mapping as dm


def test_the_null_is_not_a_dead_measurement():
    """The action null is only evidence because the RNG intervention moves it."""
    action_check = dm.duration_is_owner_selected()
    rng_check = dm.duration_is_exogenous()

    # The action intervention finds no effect...
    assert not action_check.passed
    assert "independent of" in action_check.detail
    # ...while the very same measurement responds to the RNG intervention.
    assert not rng_check.passed
    assert "drawn from the RNG" in rng_check.detail


def test_duration_does_not_respond_to_the_owner_action():
    result = dm.duration_is_owner_selected()
    assert not result.passed


def test_duration_is_driven_by_the_opportunity_rng():
    result = dm.duration_is_exogenous()
    assert not result.passed


def test_interventions_are_deterministic():
    """A proof that changes between runs is not a proof."""
    assert dm.duration_is_owner_selected().detail == (
        dm.duration_is_owner_selected().detail
    )
    assert dm.duration_is_exogenous().detail == dm.duration_is_exogenous().detail


def test_escrow_lifecycle_is_absent_and_names_what_is_missing():
    result = dm.escrow_lifecycle_present()
    assert not result.passed
    for required in ("CLAIM", "RELEASE", "TERMINAL_HORIZON"):
        assert required in result.detail


def test_runtime_boundary_vocabulary_is_actually_read():
    """Guard against the scan silently reading an empty vocabulary."""
    result = dm.escrow_lifecycle_present()
    assert "ordinary_opportunity" in result.detail
    assert "terminal_boundary" in result.detail


def test_terminal_is_absent():
    report = dm.proof()
    assert report["terminal"] == "VSP02_DURATION_EXPOSURE_ABSENT"
    assert not any(check["passed"] for check in report["checks"].values())
    assert "licenses no scientific claim" in report["scope"]
