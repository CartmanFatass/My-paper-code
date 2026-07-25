"""Focused checks on the D7.2B audit's decision logic.

The rollout machinery is exercised by running it; these pin the parts where a
silent error would produce a confident wrong conclusion instead of a crash:
urgency identification, clustering, the split-sample estimator, and the
first-match order of the branch table.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "d7_2b_audit", PROJECT_ROOT / "scripts" / "audit_d7_2b_toy_positive_control.py"
)
audit = importlib.util.module_from_spec(_SPEC)
# Registered before exec: `@dataclass` resolves annotations through
# sys.modules[cls.__module__], which is None for an unregistered module.
sys.modules[_SPEC.name] = audit
_SPEC.loader.exec_module(audit)

INVALID = audit.INVALID_SKILL


def test_urgency_is_read_from_the_incumbent_axis():
    # x-axis skills serve the slow duty, whose target holds for six checks.
    assert audit.regime_of(0, True) == "stable"
    assert audit.regime_of(1, True) == "stable"
    # y-axis skills serve the fast duty, which flips at every check.
    assert audit.regime_of(2, True) == "flex"
    assert audit.regime_of(3, True) == "flex"
    # No incumbent means no regime -- there is nothing to keep (D0 section 2).
    assert audit.regime_of(0, False) == "undefined"
    assert audit.regime_of(INVALID, True) == "undefined"


def test_target_skills_follow_the_state_signs():
    assert audit.target_skills_from_state([1.0, 0.0, 0.0, 1.0, 0.0, 0.0]) == (0, 2)
    assert audit.target_skills_from_state([-1.0, 0.0, 0.0, 1.0, 0.0, 0.0]) == (1, 2)
    assert audit.target_skills_from_state([1.0, 0.0, 0.0, -1.0, 0.0, 0.0]) == (0, 3)
    assert audit.target_skills_from_state([-1.0, 0.0, 0.0, -1.0, 0.0, 0.0]) == (1, 3)
    with pytest.raises(RuntimeError):
        audit.target_skills_from_state([1.0, 0.0])


def test_ci_clusters_by_episode_rather_than_by_check():
    """Checks inside one episode share the seeded target signs, so treating them
    as independent would understate the interval. Same points, different
    clustering, must give a wider interval when they collapse into one cluster."""
    spread = [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0], [0.0, 1.0]]
    many = audit.clustered_mean_ci(spread)
    assert many["clusters"] == 4
    assert many["points"] == 8
    # Four identical cluster means -> zero between-cluster variance.
    assert many["mean"] == pytest.approx(0.5)
    assert many["lcb95"] == pytest.approx(0.5)

    varied = audit.clustered_mean_ci([[0.0], [1.0], [0.0], [1.0]])
    assert varied["mean"] == pytest.approx(0.5)
    assert varied["lcb95"] < 0.5 < varied["ucb95"]


def test_ci_refuses_to_bound_a_single_cluster():
    """One episode cannot support an interval, and reporting a tight one would let
    a threshold pass on a single seed."""
    single = audit.clustered_mean_ci([[1.0, 1.0, 1.0]])
    assert single["clusters"] == 1
    assert single["lcb95"] == float("-inf")
    assert single["ucb95"] == float("inf")

    empty = audit.clustered_mean_ci([[], []])
    assert empty["clusters"] == 0
    assert empty["mean"] != empty["mean"]  # NaN


def test_split_sample_u_opp_does_not_value_on_its_selection_half():
    """D0 section 3: maximizing and valuing on one sample manufactures an
    optimistic source effect, because the selection is itself an estimate. Skill 1
    looks best on the first half by noise alone and is worthless on the second, so
    a same-sample maximizer would report 10.0 where the honest estimate is 0.0.
    """
    opp = {
        1: [10.0, 10.0, 0.0, 0.0],   # selected on the first half, worthless after
        2: [1.0, 1.0, 1.0, 1.0],     # unremarkable but honest
    }
    value = audit._split_sample_u_opp(opp, keep_mean=0.0, b_value=1.0)
    assert value == pytest.approx(0.0)
    naive_same_sample = max(sum(v) / len(v) for v in opp.values())
    assert value < naive_same_sample

    assert audit._split_sample_u_opp({1: [1.0]}, keep_mean=0.0, b_value=1.0) is None


def test_window_return_truncates_at_the_episode_end():
    trace = audit.EpisodeTrace(episode_id=0)
    trace.step_rewards = [1.0, 1.0, 1.0]
    assert audit.window_return(trace, 0, 3) == pytest.approx(3.0)
    assert audit.window_return(trace, 1, 30) == pytest.approx(2.0)
    assert audit.window_return(trace, 3, 5) != audit.window_return(trace, 0, 1)


def _cond(passed):
    return {"passed": bool(passed)}


def test_branch_table_puts_access_before_behaviour():
    """First match, and the order is the point: an access or headroom failure must
    never be reported as a renewal result."""
    b_h_live = {"30": {"b_h": 10.0}}
    b_h_dead = {"30": {"b_h": 0.0}}

    # No headroom wins even when everything else would pass.
    branch, _ = audit.verdict(_cond(True), _cond(True), _cond(True), b_h_dead, 30)
    assert branch == "NO_RENEWAL_HEADROOM_D7_TOY_SOURCE"

    # An A failure outranks B and C, and says nothing about renewal capacity.
    branch, reason = audit.verdict(
        _cond(False), _cond(True), _cond(True), b_h_live, 30
    )
    assert branch == "NO_ACCESS_D7_TOY_POSITIVE_CONTROL"
    assert "does not update R30 renewal capacity" in reason

    branch, _ = audit.verdict(_cond(True), _cond(False), _cond(True), b_h_live, 30)
    assert branch == "NONFORMAL_NO_URGENCY_SEPARATION_D7_2B"

    # B passing while C fails is the capability-without-alignment reading.
    branch, _ = audit.verdict(_cond(True), _cond(True), _cond(False), b_h_live, 30)
    assert branch == "NONFORMAL_CAPABILITY_WITHOUT_ALIGNMENT_D7_2B"

    branch, reason = audit.verdict(
        _cond(True), _cond(True), _cond(True), b_h_live, 30
    )
    assert branch == "NONFORMAL_CARRIER_EXPRESSES_URGENCY_D7_2B"
    assert "Not a claim about variable k" in reason


def test_thresholds_match_the_frozen_contract():
    """These are read from D7's pass conditions and may not be renegotiated after
    seeing output. Pinning them means a later edit has to be deliberate."""
    assert audit.A_MATCH_FLOOR == 0.75
    assert audit.B_DIFF_FLOOR == 0.20
    assert audit.B_FLEX_FLOOR == 0.10
    assert audit.B_STABLE_CEIL == 0.05
    assert audit.C_SET_GAP_FLOOR == 0.50
    assert audit.C_SET_FLEX_FLOOR == 0.75
    assert audit.C_KEEP_STABLE_FLOOR == 0.75
    assert audit.C_FULL_SYNC_CEIL == 0.25
