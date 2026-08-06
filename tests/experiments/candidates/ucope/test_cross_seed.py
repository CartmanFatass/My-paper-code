"""Tests for the cross-seed replication.

The load-bearing tests are the two that guard against the specific ways this
analysis could lie: using the wrong unit of analysis (ledgers instead of seeds),
and letting two replications share an episode stream so that "independent
replications" are not independent.
"""

from __future__ import annotations

import math

import pytest

from experiments.candidates.ucope import cross_seed as cs
from experiments.candidates.ucope import crossed_evaluation as ce
from experiments.candidates.ucope import paired_training as pt


def _row(played: float, bayes: float) -> dict[str, float]:
    return {"mean_effort": played, "steps": 10, "bayes_optimal_effort": bayes}


def test_the_switching_rule_classification_needs_no_invented_tolerance():
    """Correctness is 'same side of the switch', not 'within epsilon'.

    A policy playing 0.30 where Bayes says 0.25 has recovered the rule; one
    playing 0.51 there has not, even though 0.51 is closer to 0.75 than 0.30 is
    far from 0.25.  That is the whole point of classifying by side.
    """
    recovered = cs.classify_switching_rule(
        {"a": _row(0.30, 0.25), "b": _row(0.68, 0.75)}
    )
    assert recovered["state_conditional_mean_correct_at_every_state"]
    assert recovered["incorrect_states"] == ()
    assert recovered["states_checked"] == 2

    missed = cs.classify_switching_rule(
        {"a": _row(0.51, 0.25), "b": _row(0.68, 0.75)}
    )
    assert not missed["state_conditional_mean_correct_at_every_state"]
    assert missed["incorrect_states"] == ("a",)


def test_the_deviation_is_descriptive_and_does_not_drive_the_verdict():
    """A large deviation on the correct side must not be called a failure."""
    result = cs.classify_switching_rule({"a": _row(0.49, 0.25)})
    assert result["state_conditional_mean_correct_at_every_state"]
    assert result["maximum_absolute_deviation_from_bayes"] == pytest.approx(0.24)


def test_the_unit_of_analysis_is_the_seed_with_small_sample_critical_values():
    """n is the number of seeds and the interval uses t, not 1.96.

    Reporting the within-run per-ledger standard error as though it bounded
    across-seed variability is exactly the error this module exists to avoid,
    so the summary must count seeds and must widen for small df.
    """
    values = [4.1, 4.6, 4.3, 4.9, 4.0, 4.4, 4.7, 4.2]
    summary = cs.across_seed_summary(values)
    assert summary["seeds"] == 8
    assert summary["degrees_of_freedom"] == 7
    assert summary["t_critical_975"] == 2.365
    assert summary["t_critical_975"] > 1.96
    assert summary["half_width_95"] == pytest.approx(
        2.365 * summary["standard_error"]
    )
    assert summary["minimum"] == 4.0 and summary["maximum"] == 4.9


def test_a_single_seed_reports_no_across_seed_uncertainty():
    """One seed cannot support an interval, and must not pretend to."""
    summary = cs.across_seed_summary([4.47])
    assert summary["seeds"] == 1
    assert summary["degrees_of_freedom"] == 0
    assert math.isnan(summary["standard_error"])
    assert math.isnan(summary["half_width_95"])


def test_seeds_that_would_share_a_stream_are_refused():
    """run_arm consumes seed+1..seed+3, so near-adjacent seeds collide.

    With seeds 100 and 102, replication A's evidence seed (103) and replication
    B's torch seed (103) are the same number -- the replications would not be
    independent, and the across-seed spread would be understated.
    """
    with pytest.raises(ValueError, match="derived-seed span"):
        cs.run_replication(seeds=(100, 102))
    with pytest.raises(ValueError, match="distinct"):
        cs.run_replication(seeds=(100, 100))


def test_the_registered_seeds_are_mutually_safe_and_start_from_the_archive():
    """The archived single-seed artifact must be one of the replications."""
    seeds = cs.REPLICATION_SEEDS
    assert seeds[0] == 20_260_806, "the archived v3 run is replication one"
    assert len(set(seeds)) == len(seeds)
    for left in seeds:
        for right in seeds:
            if left != right:
                assert abs(left - right) > 3


def test_provenance_covers_this_module_including_its_dirtiness():
    """Inheriting the flag unchanged would exempt this file from the check."""
    record = cs.provenance(run_arguments={"seeds": [1]})
    assert cs._SELF_SOURCE in record["source_digests"]
    assert len(record["source_digests"][cs._SELF_SOURCE]) == 64
    # Every single-seed source is still covered.
    for relative in cs.ce._PROVENANCE_SOURCES:
        assert relative in record["source_digests"]
    assert record["commit_authenticates_the_run"] is (
        record["source_commit"] != "UNAVAILABLE"
        and record["source_tree_dirty"] is False
    )


def test_a_replication_trains_to_the_registered_budget():
    """The defect this test exists for was real and silent.

    The archived single-seed artifact was launched with ``iterations=300``
    while ``run_arm``'s own default is 120, so the first cross-seed replication
    trained every arm to 40% of the registered budget. Nothing failed: it
    produced eight plausible-looking numbers whose spread described the short
    budget rather than the seed (regrets ~5.4 against the registered 0.58).

    A budget supplied only by the caller is a budget two callers can disagree
    about, so it now lives in one place and both paths default to it.
    """
    assert ce.REGISTERED_TRAINING["iterations"] == 300
    resolved = {**ce.REGISTERED_TRAINING}
    for key in ("iterations", "episodes_per_iteration", "evaluation_episodes"):
        assert key in resolved
        # The registered budget must not silently equal run_arm's default in
        # the one field where they differed.
    assert ce.REGISTERED_TRAINING["iterations"] != 120

    summary = cs.run_replication(
        seeds=(41_000,),
        evaluation_ledgers=1,
        iterations=1,
        episodes_per_iteration=2,
        evaluation_episodes=2,
    )
    recorded = summary["provenance"]["run_arguments"]
    # An explicit override wins, and the artifact records what actually ran...
    assert recorded["iterations"] == 1
    # ...including the fields that fell through to the registered budget.
    assert recorded["episodes_per_iteration"] == 2
    assert set(ce.REGISTERED_TRAINING) <= set(recorded)


def test_a_two_seed_replication_produces_distinct_checkpoints():
    """Cheap end-to-end: two seeds must not train to the same weights.

    If the seed did not actually reach the policy initialization, every
    replication would return the same checkpoint and the across-seed spread
    would be identically zero -- a result that would look like exceptional
    stability rather than a broken design.
    """
    summary = cs.run_replication(
        seeds=(31_000, 32_000),
        evaluation_ledgers=2,
        iterations=1,
        episodes_per_iteration=2,
        evaluation_episodes=2,
    )
    assert summary["terminal"] in {"CROSS_SEED_MEASURED", "CROSS_SEED_PARTIAL"}
    assert len(summary["per_seed"]) == 2
    assert summary["distinct_informed_checkpoints"] == 2
    assert summary["between_arm_contrast_across_seeds"]["seeds"] == 2
    assert summary["raw_output_binding"] == "ucope.cross_seed.v1"
    # The per-seed reports travel with the summary, minus the weight tensors.
    for report in summary["per_seed_reports"].values():
        assert "checkpoints" not in report
        assert report["raw_output_binding"] == "ucope.crossed_evaluation.v1"
    # The determinism checksum must still hold inside every replication.
    assert summary["all_seeds_severed_bit_identical_to_blind"]
    for row in summary["per_seed"]:
        assert set(row["checkpoint_digests"]) == set(pt.ARMS)


def test_the_classification_says_what_it_measures():
    """Pro's wording correction: it is the state-conditional MEAN, not coverage.

        The implementation first averages all played efforts associated with a
        count state and then classifies that state-conditional mean relative to
        the action midpoint. It does not check that every individual
        ledger/time/context realization remained on the correct side.

    The key is named for the mean and the row says so, because "recovering the
    switching rule everywhere" was read as per-instance coverage and is not.
    """
    result = cs.classify_switching_rule({"a": _row(0.30, 0.25)})
    assert "state_conditional_mean_correct_at_every_state" in result
    assert "correct_at_every_state" not in result
    assert "not per-instance coverage" in result["measures"]


def test_the_registered_evaluation_support_is_not_held_out_for_the_first_seed():
    """The defect Pro found, pinned so it cannot be silently reintroduced.

        The first replication seed is 20260806, while the fixed evaluation
        ledger seed is 20260808. run_arm derives regime_seed = seed + 2 and uses
        that same value as the training ledger's master_seed [...] Thus, for the
        first replication, evaluation ledgers 0,...,63 are the same ledger
        contexts encountered during its first 64 training episodes.

    This asserts the collision on the constants the archived v2 artifact
    actually ran under.  It is a record of a known limitation, not a target to
    make pass by editing the constants -- the artifact must stay reproducible.
    """
    report = ce.evaluation_support_disjointness(
        seeds=cs.REPLICATION_SEEDS,
        ledger_seed=20_260_808,
        evaluation_ledgers=64,
        iterations=300,
        episodes_per_iteration=16,
    )
    assert report["ledger_seed_collides_with_a_training_root"]
    assert report["colliding_training_seeds"] == [20_260_806]
    assert report["overlapping_ledger_ids"] == list(range(64))
    assert not report["evaluation_support_is_held_out_for_every_seed"]


def test_shifting_the_ledger_base_clears_the_overlap_for_every_seed():
    """Pro named two remedies; this is the one robust to any seed choice.

        A future evaluation seed should be outside every training-derived seed
        root, or evaluation ledger IDs should be outside the training episode-ID
        range.

    The seed-side remedy fixes one seed at a time; shifting the ids fixes all of
    them, because a ledger is (id, master_seed, profile) and disagreeing on the
    id is enough.
    """
    clean = ce.evaluation_support_disjointness(
        seeds=cs.REPLICATION_SEEDS,
        ledger_seed=20_260_808,
        evaluation_ledgers=64,
        iterations=300,
        episodes_per_iteration=16,
        ledger_base=ce.CLEAN_LEDGER_BASE,
    )
    # The seed collision is untouched -- and that is fine, because the ids no
    # longer meet.
    assert clean["ledger_seed_collides_with_a_training_root"]
    assert clean["overlapping_ledger_ids"] == []
    assert clean["evaluation_support_is_held_out_for_every_seed"]

    # ...and the seed-side remedy works on its own too.
    other = ce.evaluation_support_disjointness(
        seeds=cs.REPLICATION_SEEDS,
        ledger_seed=77_777_777,
        evaluation_ledgers=64,
        iterations=300,
        episodes_per_iteration=16,
    )
    assert not other["ledger_seed_collides_with_a_training_root"]
    assert other["evaluation_support_is_held_out_for_every_seed"]


def test_the_ledger_base_actually_changes_the_evaluation_ledgers():
    """A shift that produced the same ledger would fix nothing.

    The ledger's identity IS its ``episode_id``: it is what ``make_ledger``
    keys the draw on and what a training episode would have to match for the
    two contexts to coincide.  Compared field-wise because the dataclass holds
    numpy arrays and ``==`` on it is ambiguous.
    """
    default = ce.evaluation_ledger(0, ledger_seed=20_260_808)
    shifted = ce.evaluation_ledger(
        0, ledger_seed=20_260_808, ledger_base=ce.CLEAN_LEDGER_BASE
    )
    assert default.episode_id == 0
    assert shifted.episode_id == ce.CLEAN_LEDGER_BASE
    # The archived behaviour is the ledger_base=0 path, unchanged.
    assert ce.evaluation_ledger(
        7, ledger_seed=20_260_808, ledger_base=0
    ).episode_id == 7
    # ...and the shift is what puts it clear of every training episode id.
    assert shifted.episode_id >= 300 * 16
