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
    assert recovered["correct_at_every_state"]
    assert recovered["incorrect_states"] == ()
    assert recovered["states_checked"] == 2

    missed = cs.classify_switching_rule(
        {"a": _row(0.51, 0.25), "b": _row(0.68, 0.75)}
    )
    assert not missed["correct_at_every_state"]
    assert missed["incorrect_states"] == ("a",)


def test_the_deviation_is_descriptive_and_does_not_drive_the_verdict():
    """A large deviation on the correct side must not be called a failure."""
    result = cs.classify_switching_rule({"a": _row(0.49, 0.25)})
    assert result["correct_at_every_state"]
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
