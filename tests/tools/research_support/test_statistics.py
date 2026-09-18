"""Tests for the statistical reductions.

Each test targets one acceptance point of plan section 7.3 and of the section 18
"Statistical unit" / "Statistical math" / "Recovery" rows, and would fail if that point
broke:

* the independent unit is the training replicate, and episodes of one replicate are
  precision about that fit, not extra fits;
* a single fit has no cross-fit SD/SE/CI at all;
* invalid, missing, out-of-domain and wrongly united rows are counted before reduction;
* zero variance is degenerate rather than certain;
* a ratio comes from summed denominators, and a zero denominator is invalid, not 0.0;
* matching seed numbers do not buy a paired analysis;
* both interval methods run on the installed SciPy;
* recovery keeps repair, episode end and technical failure apart, retains unrecovered
  episodes, and labels the recovered-only mean as conditional.

Expected numbers are computed by hand inside the tests. Where a Student-t quantile is
needed, the test uses the closed form for that degrees of freedom (the ``df=1`` quantile is
the Cauchy quantile ``tan(pi * (p - 1/2))``) rather than calling SciPy again, so the check
is independent of the implementation.
"""

from __future__ import annotations

import math
import pathlib
import sys
from typing import Any

import pytest

# ``tests/tools/research_support/__init__.py`` makes this directory a package, so pytest puts
# ``tests/tools`` on ``sys.path``; the repository's own ``tools`` has no ``__init__.py`` and is
# therefore a namespace package whose portions are searched in ``sys.path`` order. Without the
# repository root first, ``tools.research_support`` would resolve to this *test* package. The
# reordering is local to the interpreter running the tests and touches no source file.
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)


from tools.research_support import statistics as st
from tools.research_support.records import (
    AggregationLevel,
    Measured,
    MetricRecord,
    Phase,
    Validity,
    XKind,
    dumps,
    loads,
)

# t quantile at 97.5 % for one degree of freedom, from the Cauchy closed form.
_T_975_DF1 = math.tan(math.pi * 0.475)
# t quantile at 97.5 % for two degrees of freedom: F(t) = (1 + t / sqrt(2 + t^2)) / 2.
_T_975_DF2 = 0.95 * math.sqrt(2.0 / (1.0 - 0.95**2))


def record(
    *,
    metric: str,
    value: Any,
    replicate: str | None = "f1",
    episode: str | None = "e1",
    world: str | None = None,
    unit: str | None = None,
    validity: Validity | None = None,
    reason: str | None = None,
) -> MetricRecord:
    """Build one long-form metric record; ``validity`` set means the value is absent."""

    if validity is None:
        measured = Measured.ok(value, unit=unit)
    else:
        measured = Measured.absent(validity, reason or "unspecified", unit=unit)
    return MetricRecord(
        run_id="run",
        method_id="method",
        metric_name=metric,
        value=measured,
        x_kind=XKind.EPISODE_INDEX,
        x_value=0,
        phase=Phase.EVALUATION,
        aggregation_level=AggregationLevel.EPISODE,
        training_replicate_id=replicate,
        world_id=world,
        episode_id=episode,
        unit=unit,
    )


def rate_rows(values: dict[str, list[float]]) -> list[MetricRecord]:
    """Per-replicate lists of ``mean_delivered_mbps`` episode values (a mean-reduced rate)."""

    rows: list[MetricRecord] = []
    for replicate, episode_values in values.items():
        for index, value in enumerate(episode_values):
            rows.append(
                record(
                    metric="mean_delivered_mbps",
                    value=float(value),
                    replicate=replicate,
                    episode=f"{replicate}_e{index}",
                )
            )
    return rows


def unit_value(aggregation: st.UnitAggregation, unit_id: str) -> st.UnitValue:
    return next(unit for unit in aggregation.units if unit.unit_id == unit_id)


# --------------------------------------------------------------------------------------
# Statistical unit
# --------------------------------------------------------------------------------------


def test_replicate_means_and_student_t_interval_are_hand_checked() -> None:
    # f1 episodes 10, 12, 14 -> mean 12. f2 episodes 20, 24 -> mean 22.
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [10.0, 12.0, 14.0], "f2": [20.0, 24.0]}),
        metric_name="mean_delivered_mbps",
    )
    assert aggregation.unit_kind == "training_replicate"
    assert aggregation.n_source_rows == 5
    assert aggregation.excluded == {}
    assert unit_value(aggregation, "f1").value.value == pytest.approx(12.0)
    assert unit_value(aggregation, "f1").n_episodes == 3
    assert unit_value(aggregation, "f2").value.value == pytest.approx(22.0)

    reduction = st.reduce_units(aggregation)
    # Mean over units: (12 + 22) / 2 = 17. Deviations -5 and +5 -> variance 50 (ddof=1),
    # sd = sqrt(50), se = sqrt(50) / sqrt(2) = 5 exactly.
    assert reduction.n_units == 2
    assert reduction.point.value == pytest.approx(17.0)
    assert reduction.sd.value == pytest.approx(math.sqrt(50.0))
    assert reduction.se.value == pytest.approx(5.0)
    assert reduction.ci_method == "student_t"
    assert reduction.ci_low.value == pytest.approx(17.0 - _T_975_DF1 * 5.0)
    assert reduction.ci_high.value == pytest.approx(17.0 + _T_975_DF1 * 5.0)
    assert reduction.degenerate_variance is False
    assert any(note.startswith("small_n: n_units=2") for note in reduction.notes)
    assert all(unit_measure.unit == "Mbps" for unit_measure in (reduction.point, reduction.sd))


def test_three_unit_student_t_interval_uses_ddof_one_and_df_two() -> None:
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [9.0, 11.0], "f2": [20.0], "f3": [26.0]}),
        metric_name="mean_delivered_mbps",
    )
    reduction = st.reduce_units(aggregation)
    # Unit values 10, 20, 26 -> mean 56/3. Deviations from the mean: -26/3, 4/3, 22/3.
    # Sum of squares = (676 + 16 + 484) / 9 = 1176 / 9; variance (ddof=1) = 1176 / 18 =
    # 196 / 3, so sd = 14 / sqrt(3) and se = sd / sqrt(3) = 14 / 3 exactly.
    mean = 56.0 / 3.0
    sd = 14.0 / math.sqrt(3.0)
    se = 14.0 / 3.0
    assert reduction.n_units == 3
    assert reduction.point.value == pytest.approx(mean)
    assert reduction.sd.value == pytest.approx(sd)
    assert reduction.se.value == pytest.approx(se)
    assert reduction.ci_low.value == pytest.approx(mean - _T_975_DF2 * se)
    assert reduction.ci_high.value == pytest.approx(mean + _T_975_DF2 * se)


def test_extra_episodes_on_one_replicate_do_not_create_independent_fits() -> None:
    rows = rate_rows({"f1": [10.0, 14.0], "f2": [20.0, 24.0]})
    before = st.reduce_units(st.aggregate_episodes_to_units(rows, metric_name="mean_delivered_mbps"))
    assert before.n_units == 2

    rows_plus = rows + [
        record(
            metric="mean_delivered_mbps",
            value=12.0,
            replicate="f1",
            episode=f"f1_extra{index}",
        )
        for index in range(100)
    ]
    aggregation = st.aggregate_episodes_to_units(rows_plus, metric_name="mean_delivered_mbps")
    after = st.reduce_units(aggregation)

    assert after.n_units == 2, "100 more evaluation episodes of one fit are not 100 fits"
    assert unit_value(aggregation, "f1").n_episodes == 102
    assert unit_value(aggregation, "f2").n_episodes == 2
    assert unit_value(aggregation, "f2").value.value == pytest.approx(22.0)
    # f1 mean: (10 + 14 + 100 * 12) / 102 = 1224 / 102 = 12.0
    assert unit_value(aggregation, "f1").value.value == pytest.approx(12.0)
    assert after.point.value == pytest.approx(17.0)


def test_single_fit_has_no_cross_fit_interval() -> None:
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [10.0, 12.0, 14.0, 16.0]}), metric_name="mean_delivered_mbps"
    )
    reduction = st.reduce_units(aggregation)

    assert reduction.n_units == 1
    assert reduction.point.validity is Validity.OK
    assert reduction.point.value == pytest.approx(13.0)
    for field in (reduction.sd, reduction.se, reduction.ci_low, reduction.ci_high):
        assert field.value is None
        assert field.validity is Validity.NOT_APPLICABLE
        assert field.reason == "single_independent_fit"
    assert reduction.ci_method == "unavailable"
    assert reduction.degenerate_variance is False
    assert any("single_independent_fit" in note for note in reduction.notes)


def test_episode_unit_kind_is_available_but_explicit() -> None:
    rows = rate_rows({"f1": [10.0, 20.0]})
    aggregation = st.aggregate_episodes_to_units(
        rows, metric_name="mean_delivered_mbps", unit_field="episode_id"
    )
    assert aggregation.unit_kind == "episode"
    assert [unit.unit_id for unit in aggregation.units] == ["f1_e0", "f1_e1"]
    with pytest.raises(ValueError):
        st.aggregate_episodes_to_units(
            rows, metric_name="mean_delivered_mbps", unit_field="method_id"
        )


# --------------------------------------------------------------------------------------
# Exclusions
# --------------------------------------------------------------------------------------


def test_every_unusable_row_is_counted_before_reduction() -> None:
    rows = [
        record(metric="mean_delivered_mbps", value=10.0, replicate="f1", episode="a"),
        record(
            metric="mean_delivered_mbps",
            value=None,
            replicate="f1",
            episode="b",
            validity=Validity.INVALID,
            reason="non_finite",
        ),
        record(
            metric="mean_delivered_mbps",
            value=None,
            replicate="f1",
            episode="c",
            validity=Validity.UNKNOWN,
            reason="absent_in_source",
        ),
        record(metric="mean_delivered_mbps", value=20.0, replicate="f2", episode="d"),
        record(metric="mean_delivered_mbps", value=-5.0, replicate="f2", episode="e"),
        record(
            metric="mean_delivered_mbps",
            value=7.0,
            replicate="f2",
            episode="f",
            unit="Mbit",
        ),
        record(metric="mean_delivered_mbps", value=99.0, replicate=None, episode="g"),
        record(metric="offered_mbit", value=500.0, replicate="f1", episode="a"),
    ]
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="mean_delivered_mbps")

    assert aggregation.n_source_rows == 7, "the offered_mbit row is not a source row here"
    assert aggregation.excluded == {
        "validity:invalid:non_finite": 1,
        "validity:unknown:absent_in_source": 1,
        "out_of_valid_domain": 1,
        "unit_mismatch": 1,
        "missing_unit_id": 1,
    }
    assert [unit.value.value for unit in aggregation.units] == [10.0, 20.0]
    assert unit_value(aggregation, "f1").n_invalid_episodes == 2
    assert unit_value(aggregation, "f2").n_invalid_episodes == 2
    assert unit_value(aggregation, "f1").n_episodes == 1

    reduction = st.reduce_units(aggregation)
    assert reduction.n_units == 2
    assert reduction.excluded == aggregation.excluded
    assert reduction.point.value == pytest.approx(15.0)


def test_absent_unit_values_are_excluded_from_the_reduction_not_zeroed() -> None:
    rows = [
        record(metric="mean_delivered_mbps", value=10.0, replicate="f1", episode="a"),
        record(metric="mean_delivered_mbps", value=20.0, replicate="f2", episode="b"),
        record(
            metric="mean_delivered_mbps",
            value=None,
            replicate="f3",
            episode="c",
            validity=Validity.MISSING_ARTIFACT,
            reason="episode_log_missing",
        ),
    ]
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="mean_delivered_mbps")
    reduction = st.reduce_units(aggregation)

    assert reduction.n_units == 2
    assert reduction.point.value == pytest.approx(15.0), "a missing fit is not a fit scoring 0"
    assert reduction.excluded["validity:missing_artifact:episode_log_missing"] == 1
    assert reduction.excluded["unit_value_absent:not_recorded:no_usable_rows_for_unit"] == 1
    f3 = next(unit for unit in reduction.per_unit if unit.unit_id == "f3")
    assert f3.value.value is None and f3.n_invalid_episodes == 1


def test_declared_weights_are_applied_and_recorded() -> None:
    rows = [
        record(metric="mean_delivered_mbps", value=10.0, replicate="f1", episode="a", world="w1"),
        record(metric="mean_delivered_mbps", value=20.0, replicate="f1", episode="b", world="w2"),
        record(metric="mean_delivered_mbps", value=99.0, replicate="f1", episode="c", world="w3"),
    ]
    aggregation = st.aggregate_episodes_to_units(
        rows, metric_name="mean_delivered_mbps", weights={"w1": 0.25, "w2": 0.75}
    )
    # 0.25 * 10 + 0.75 * 20 = 17.5, over the declared worlds only.
    f1 = unit_value(aggregation, "f1")
    assert f1.value.value == pytest.approx(17.5)
    assert aggregation.excluded == {"no_declared_weight": 1}
    assert "declared weights" in (f1.weights_note or "")

    equal = st.aggregate_episodes_to_units(rows, metric_name="mean_delivered_mbps")
    assert unit_value(equal, "f1").value.value == pytest.approx((10.0 + 20.0 + 99.0) / 3.0)
    assert "equal weights" in (unit_value(equal, "f1").weights_note or "")


# --------------------------------------------------------------------------------------
# Degenerate variance
# --------------------------------------------------------------------------------------


def test_zero_variance_is_degenerate_not_certainty() -> None:
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [7.0, 7.0], "f2": [7.0], "f3": [7.0]}),
        metric_name="mean_delivered_mbps",
    )
    reduction = st.reduce_units(aggregation)

    assert reduction.n_units == 3
    assert reduction.point.value == pytest.approx(7.0)
    assert reduction.sd.validity is Validity.OK and reduction.sd.value == 0.0
    assert reduction.degenerate_variance is True
    assert reduction.ci_low.value == pytest.approx(7.0)
    assert reduction.ci_high.value == pytest.approx(7.0)
    assert any("degenerate_variance" in note for note in reduction.notes)
    assert any("not evidence of certainty" in note for note in reduction.notes)


def test_zero_variance_bootstrap_stays_degenerate_rather_than_unavailable() -> None:
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [7.0], "f2": [7.0], "f3": [7.0]}),
        metric_name="mean_delivered_mbps",
    )
    reduction = st.reduce_units(
        aggregation, ci_method="replicate_bootstrap", rng_seed=5, n_resamples=199
    )
    assert reduction.degenerate_variance is True
    assert reduction.ci_low.value == pytest.approx(7.0)
    assert reduction.ci_high.value == pytest.approx(7.0)
    assert any("degenerate_variance" in note for note in reduction.notes)


# --------------------------------------------------------------------------------------
# Ratios
# --------------------------------------------------------------------------------------


def _ratio_rows(unit_id: str, pairs: list[tuple[float, float]]) -> list[MetricRecord]:
    rows: list[MetricRecord] = []
    for index, (delivered, offered) in enumerate(pairs):
        episode = f"{unit_id}_e{index}"
        rows.append(
            record(
                metric="delivered_mbit",
                value=delivered,
                replicate=unit_id,
                episode=episode,
                unit="Mbit",
            )
        )
        rows.append(
            record(
                metric="offered_mbit",
                value=offered,
                replicate=unit_id,
                episode=episode,
                unit="Mbit",
            )
        )
    return rows


def test_ratio_is_recomputed_from_summed_denominators() -> None:
    rows = _ratio_rows("f1", [(50.0, 100.0), (30.0, 300.0)])
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="satisfaction_ratio")
    f1 = unit_value(aggregation, "f1")

    # sum(delivered) / sum(offered) = 80 / 400 = 0.2, while the mean of the per-episode
    # ratios 0.5 and 0.1 would be 0.3. The two must not be confused.
    assert f1.value.value == pytest.approx(0.2)
    assert f1.value.value != pytest.approx(0.3)
    assert f1.n_episodes == 2
    assert aggregation.n_source_rows == 4
    assert any(note.startswith("ratio_recomputed_from_sums") for note in aggregation.notes)


def test_zero_denominator_ratio_is_invalid_not_zero() -> None:
    rows = _ratio_rows("f1", [(50.0, 100.0)]) + _ratio_rows("f2", [(0.0, 0.0)])
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="satisfaction_ratio")

    f2 = unit_value(aggregation, "f2")
    assert f2.value.value is None, "a zero-demand unit is not a unit scoring 0.0"
    assert f2.value.validity is Validity.INVALID
    assert f2.value.reason == "zero_denominator"

    reduction = st.reduce_units(aggregation)
    assert reduction.n_units == 1
    assert reduction.point.value == pytest.approx(0.5)
    assert reduction.excluded["unit_value_absent:invalid:zero_denominator"] == 1


def test_ratio_without_component_rows_says_it_averaged_ratios() -> None:
    rows = [
        record(metric="satisfaction_ratio", value=0.5, replicate="f1", episode="a", unit="ratio"),
        record(metric="satisfaction_ratio", value=0.1, replicate="f1", episode="b", unit="ratio"),
    ]
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="satisfaction_ratio")
    f1 = unit_value(aggregation, "f1")
    assert f1.value.value == pytest.approx(0.3)
    assert any(
        note.startswith("ratio_averaged_from_per_episode_values") for note in aggregation.notes
    )
    assert "components unavailable" in (f1.weights_note or "")


def test_ratio_components_out_of_domain_are_excluded_per_component() -> None:
    rows = _ratio_rows("f1", [(50.0, 100.0)])
    rows.append(
        record(
            metric="delivered_mbit",
            value=-1.0,
            replicate="f1",
            episode="f1_e1",
            unit="Mbit",
        )
    )
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="satisfaction_ratio")
    assert aggregation.excluded == {"numerator:out_of_valid_domain": 1}
    assert unit_value(aggregation, "f1").value.value == pytest.approx(0.5)


# --------------------------------------------------------------------------------------
# Categorical metrics
# --------------------------------------------------------------------------------------


def test_skill_identifiers_are_never_averaged() -> None:
    rows = [
        record(metric="team_skill_id", value=3, replicate="f1", episode="a"),
        record(metric="team_skill_id", value=3, replicate="f1", episode="b"),
        record(metric="team_skill_id", value=5, replicate="f2", episode="c"),
    ]
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="team_skill_id")
    assert [unit.value.value for unit in aggregation.units] == ["3", "5"]

    reduction = st.reduce_units(aggregation)
    assert reduction.point.value is None
    assert reduction.point.validity is Validity.NOT_APPLICABLE
    assert reduction.point.reason == "non_numeric_unit_values_not_averaged"
    assert reduction.ci_method == "unavailable"


def test_a_unit_with_disagreeing_labels_has_no_value() -> None:
    rows = [
        record(metric="team_skill_id", value=3, replicate="f1", episode="a"),
        record(metric="team_skill_id", value=4, replicate="f1", episode="b"),
    ]
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="team_skill_id")
    f1 = unit_value(aggregation, "f1")
    assert f1.value.value is None
    assert f1.value.reason == "categorical_metric_not_averaged"


def test_an_uncatalogued_metric_is_flagged() -> None:
    rows = [
        record(metric="mystery_metric", value=1.0, replicate="f1", episode="a"),
        record(metric="mystery_metric", value=3.0, replicate="f1", episode="b"),
    ]
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="mystery_metric")
    assert unit_value(aggregation, "f1").value.value == pytest.approx(2.0)
    assert any(note.startswith("metric_not_in_catalog") for note in aggregation.notes)


# --------------------------------------------------------------------------------------
# Reducers other than the mean
# --------------------------------------------------------------------------------------


def test_median_reducer_is_used_for_a_per_episode_extremum() -> None:
    rows = [
        record(metric="peak_unmet_mbps", value=value, replicate="f1", episode=f"e{index}")
        for index, value in enumerate([4.0, 10.0, 1.0])
    ]
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="peak_unmet_mbps")
    f1 = unit_value(aggregation, "f1")
    # Median of 1, 4, 10 is 4; the mean would be 5, and a mean of maxima is not a maximum.
    assert f1.value.value == pytest.approx(4.0)
    assert (f1.weights_note or "").startswith("median")


def test_median_says_when_it_ignores_declared_weights() -> None:
    rows = [
        record(
            metric="peak_unmet_mbps",
            value=value,
            replicate="f1",
            episode=f"e{index}",
            world=world,
        )
        for index, (value, world) in enumerate([(4.0, "w1"), (10.0, "w2"), (1.0, "w3")])
    ]
    aggregation = st.aggregate_episodes_to_units(
        rows, metric_name="peak_unmet_mbps", weights={"w1": 0.5, "w2": 0.25, "w3": 0.25}
    )
    assert unit_value(aggregation, "f1").value.value == pytest.approx(4.0)
    assert any("median_ignores_declared_weights" in note for note in aggregation.notes)


def test_sum_reducer_totals_and_warns_about_unequal_episode_counts() -> None:
    rows = [
        record(metric="delivered_mbit", value=10.0, replicate="f1", episode="a", unit="Mbit"),
        record(metric="delivered_mbit", value=20.0, replicate="f1", episode="b", unit="Mbit"),
        record(metric="delivered_mbit", value=5.0, replicate="f2", episode="c", unit="Mbit"),
    ]
    aggregation = st.aggregate_episodes_to_units(rows, metric_name="delivered_mbit")
    assert unit_value(aggregation, "f1").value.value == pytest.approx(30.0)
    assert unit_value(aggregation, "f2").value.value == pytest.approx(5.0)
    assert any(
        note.startswith("extensive_reducer_with_unequal_row_counts")
        for note in aggregation.notes
    )


def test_a_caller_supplied_catalog_lookup_overrides_the_default() -> None:
    from tools.research_support.catalog import MetricDefinition

    declared = MetricDefinition(
        name="mean_delivered_mbps",
        unit="Mbps",
        direction="higher_is_better",
        reducer="sum",
        definition_id="test.mean_delivered_mbps.v1",
        description="deliberately declared as extensive, to prove the lookup is honoured",
    )
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [10.0, 12.0]}),
        metric_name="mean_delivered_mbps",
        catalog_lookup=lambda name: declared if name == declared.name else None,
    )
    assert unit_value(aggregation, "f1").value.value == pytest.approx(22.0)


# --------------------------------------------------------------------------------------
# Paired differences
# --------------------------------------------------------------------------------------


def _aggregation_from(values: dict[str, float]) -> st.UnitAggregation:
    return st.aggregate_episodes_to_units(
        rate_rows({unit: [value] for unit, value in values.items()}),
        metric_name="mean_delivered_mbps",
    )


def test_paired_difference_is_hand_checked_and_keeps_its_sign() -> None:
    a = _aggregation_from({"f1": 12.0, "f2": 22.0, "f3": 30.0})
    b = _aggregation_from({"f1": 10.0, "f2": 25.0, "f3": 29.0})
    paired = st.paired_difference(a, b, pairing_evidence="verified_world_identity")

    # Differences a - b: +2, -3, +1 -> mean 0. Deviations 2, -3, 1 -> variance 14/2 = 7.
    assert paired.pairing_status == "verified"
    assert paired.n_pairs == 3
    assert paired.point.value == pytest.approx(0.0)
    assert paired.sd.value == pytest.approx(math.sqrt(7.0))
    assert paired.se.value == pytest.approx(math.sqrt(7.0 / 3.0))
    assert paired.ci_method == "student_t"
    assert paired.ci_low.value == pytest.approx(-_T_975_DF2 * math.sqrt(7.0 / 3.0))
    assert paired.ci_high.value == pytest.approx(_T_975_DF2 * math.sqrt(7.0 / 3.0))
    assert paired.fallback_unpaired is None

    worse = st.paired_difference(
        _aggregation_from({"f1": 10.0, "f2": 10.0}),
        _aggregation_from({"f1": 12.0, "f2": 14.0}),
        pairing_evidence="verified_design",
    )
    # Differences -2 and -4 -> mean -3, kept negative rather than oriented as improvement.
    assert worse.point.value == pytest.approx(-3.0)
    assert worse.sd.value == pytest.approx(math.sqrt(2.0))


@pytest.mark.parametrize(
    "evidence, expected_status",
    [("matching_seed_number_only", "pairing_unverified"), ("none", "unpaired")],
)
def test_unevidenced_pairing_is_refused_with_an_unpaired_fallback(
    evidence: str, expected_status: str
) -> None:
    a = _aggregation_from({"f1": 12.0, "f2": 22.0})
    b = _aggregation_from({"f1": 10.0, "f2": 25.0})
    paired = st.paired_difference(a, b, pairing_evidence=evidence)

    assert paired.pairing_status == expected_status
    assert paired.n_pairs == 0
    for field in (paired.point, paired.sd, paired.se, paired.ci_low, paired.ci_high):
        assert field.value is None
        assert field.validity is Validity.NOT_APPLICABLE
        assert field.reason == f"pairing_refused:{evidence}"
    assert paired.ci_method == "unavailable"

    fallback = paired.fallback_unpaired
    assert fallback is not None
    assert fallback.n_units == 2
    assert fallback.point.value == pytest.approx(17.0)  # (12 + 22) / 2
    assert fallback.ci_method == "student_t"
    assert any("pairing refused" in note for note in paired.notes)

    if evidence == "matching_seed_number_only":
        assert any("matching seed numbers are not" in note for note in paired.notes)

    with pytest.raises(ValueError):
        st.paired_difference(a, b, pairing_evidence="same_seed_probably_fine")


def test_unmatched_and_incomplete_pairs_are_reported() -> None:
    a = _aggregation_from({"f1": 12.0, "f2": 22.0, "f3": 30.0})
    b_rows = rate_rows({"f2": [25.0], "f4": [1.0]})
    b_rows.append(
        record(
            metric="mean_delivered_mbps",
            value=None,
            replicate="f3",
            episode="f3_e0",
            validity=Validity.MISSING_ARTIFACT,
            reason="episode_log_missing",
        )
    )
    b = st.aggregate_episodes_to_units(b_rows, metric_name="mean_delivered_mbps")

    paired = st.paired_difference(a, b, pairing_evidence="verified_design")
    assert paired.unmatched_a == ("f1",)
    assert paired.unmatched_b == ("f4",)
    assert paired.incomplete_pairs == 1
    assert paired.n_pairs == 1
    assert paired.point.value == pytest.approx(-3.0)  # 22 - 25
    for field in (paired.sd, paired.se, paired.ci_low, paired.ci_high):
        assert field.value is None and field.reason == "single_pair"
    assert any("not the full batch" in note for note in paired.notes)


def test_pairing_across_different_unit_kinds_is_refused() -> None:
    rows = rate_rows({"f1": [10.0, 20.0]})
    by_replicate = st.aggregate_episodes_to_units(rows, metric_name="mean_delivered_mbps")
    by_episode = st.aggregate_episodes_to_units(
        rows, metric_name="mean_delivered_mbps", unit_field="episode_id"
    )
    paired = st.paired_difference(
        by_replicate, by_episode, pairing_evidence="verified_world_identity"
    )
    assert paired.pairing_status == "unpaired"
    assert paired.fallback_unpaired is not None

    with pytest.raises(ValueError):
        st.paired_difference(
            by_replicate,
            st.aggregate_episodes_to_units(
                _ratio_rows("f1", [(1.0, 2.0)]), metric_name="satisfaction_ratio"
            ),
            pairing_evidence="verified_design",
        )


# --------------------------------------------------------------------------------------
# Interval methods on the installed SciPy
# --------------------------------------------------------------------------------------


def test_replicate_bootstrap_runs_on_the_installed_scipy_and_is_seed_reproducible() -> None:
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [10.0], "f2": [14.0], "f3": [20.0], "f4": [26.0], "f5": [30.0]}),
        metric_name="mean_delivered_mbps",
    )
    first = st.reduce_units(
        aggregation, ci_method="replicate_bootstrap", rng_seed=20260918, n_resamples=999
    )
    second = st.reduce_units(
        aggregation, ci_method="replicate_bootstrap", rng_seed=20260918, n_resamples=999
    )

    assert first.ci_method == "replicate_bootstrap"
    assert first.n_units == 5
    assert first.point.value == pytest.approx(20.0)  # (10 + 14 + 20 + 26 + 30) / 5
    assert first.sd.value == pytest.approx(math.sqrt(((-10) ** 2 + 36 + 0 + 36 + 100) / 4))
    assert first.ci_low.value is not None and first.ci_high.value is not None
    assert first.ci_low.value < first.point.value < first.ci_high.value
    assert first.ci_low.value == second.ci_low.value
    assert first.ci_high.value == second.ci_high.value
    assert any("scipy.stats.bootstrap" in note for note in first.notes)
    assert any(st.BOOTSTRAP_INTERVAL_TYPE in note for note in first.notes)
    assert not any("small_n" in note for note in first.notes)


def test_bootstrap_without_a_seed_says_it_is_not_reproducible() -> None:
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [10.0], "f2": [20.0], "f3": [30.0]}),
        metric_name="mean_delivered_mbps",
    )
    reduction = st.reduce_units(
        aggregation, ci_method="replicate_bootstrap", n_resamples=199
    )
    assert any("not reproducible" in note for note in reduction.notes)


def test_paired_bootstrap_resamples_matching_blocks_together() -> None:
    a = _aggregation_from({"f1": 12.0, "f2": 22.0, "f3": 30.0, "f4": 41.0})
    b = _aggregation_from({"f1": 10.0, "f2": 25.0, "f3": 29.0, "f4": 35.0})
    paired = st.paired_difference(
        a,
        b,
        pairing_evidence="verified_world_identity",
        ci_method="replicate_bootstrap",
        rng_seed=7,
        n_resamples=999,
    )
    # Differences +2, -3, +1, +6 -> mean 1.5.
    assert paired.point.value == pytest.approx(1.5)
    assert paired.ci_method == "replicate_bootstrap"
    assert paired.ci_low.value is not None and paired.ci_high.value is not None
    assert paired.ci_low.value <= paired.point.value <= paired.ci_high.value
    assert any("matched blocks are resampled together" in note for note in paired.notes)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ci_method": "wald"},
        {"ci_level": 0.0},
        {"ci_level": 1.0},
        {"n_resamples": 0},
    ],
)
def test_invalid_interval_arguments_are_refused(kwargs: dict) -> None:
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [10.0], "f2": [20.0]}), metric_name="mean_delivered_mbps"
    )
    with pytest.raises(ValueError):
        st.reduce_units(aggregation, **kwargs)


# --------------------------------------------------------------------------------------
# Recovery
# --------------------------------------------------------------------------------------


def _recovered(episode_id: str, time_s: float) -> st.RecoveryOutcome:
    return st.RecoveryOutcome(
        episode_id=episode_id,
        outcome="recovered",
        time_to_recovery_s=Measured.ok(time_s, unit="s"),
    )


def _unrecovered(episode_id: str, outcome: str, reason: str) -> st.RecoveryOutcome:
    return st.RecoveryOutcome(
        episode_id=episode_id,
        outcome=outcome,
        time_to_recovery_s=Measured.absent(Validity.NOT_APPLICABLE, reason, unit="s"),
        reason=reason,
    )


def test_recovery_summary_distinguishes_repair_episode_end_and_technical_failure() -> None:
    outcomes = [
        _recovered("e1", 12.0),
        _recovered("e2", 30.0),
        _unrecovered("e3", "censored_automatic_repair", "repaired_before_recovery_threshold_reached"),
        _unrecovered("e4", "censored_episode_end", "threshold_not_reached_within_episode"),
        _unrecovered("e5", "technical_failure", "worker_crashed"),
        _unrecovered("e6", "never_affected", "no capability loss in this episode"),
    ]
    summary = st.recovery_summary(outcomes, deadline_s=20.0)

    assert summary.n_episodes == 6
    assert summary.outcomes_by_kind == {
        "recovered": 2,
        "censored_episode_end": 1,
        "censored_automatic_repair": 1,
        "technical_failure": 1,
        "never_affected": 1,
    }
    # Determinable affected episodes: 2 recovered + 1 repair-censored + 1 end-censored = 4.
    # Recovered within 20 s: only e1 -> 1 / 4 = 0.25.
    assert summary.recovery_fraction_at_deadline.value == pytest.approx(0.25)
    # Conditional mean over recovered episodes only: (12 + 30) / 2 = 21.
    assert summary.conditional_mean_recovered_s.value == pytest.approx(21.0)
    assert any("CONDITIONAL on recovery" in note for note in summary.notes)
    assert any("competing event" in note for note in summary.notes)
    # Counting the technical failure as unrecovered would give 1 / 5 = 0.2; the note must
    # state the alternative rather than hide the choice.
    assert any("0.2" in note and "technical_failure" in note for note in summary.notes)

    # Only genuinely recovered episodes may enter the recovered bookkeeping: if a censored
    # outcome were pulled into it, this note would appear.
    assert not any("carry no time_to_recovery_s" in note for note in summary.notes)

    assert len(summary.per_episode) == 6, "unrecovered episodes are retained, not filtered"
    for outcome in summary.per_episode:
        if outcome.outcome != "recovered":
            assert outcome.time_to_recovery_s.value is None


def test_a_repair_censored_episode_does_not_count_as_recovery() -> None:
    repaired = st.recovery_summary(
        [
            _recovered("e1", 5.0),
            _unrecovered("e2", "censored_automatic_repair", "repaired_before_recovery_threshold_reached"),
        ],
        deadline_s=60.0,
    )
    assert repaired.recovery_fraction_at_deadline.value == pytest.approx(0.5)
    assert repaired.outcomes_by_kind["censored_automatic_repair"] == 1
    assert not any("kaplan" in note.lower() for note in repaired.notes if "no Kaplan" not in note)


def test_an_unrecovered_episode_cannot_carry_a_time() -> None:
    with pytest.raises(ValueError):
        st.RecoveryOutcome(
            episode_id="e1",
            outcome="censored_episode_end",
            time_to_recovery_s=Measured.ok(0.0, unit="s"),
        )
    with pytest.raises(ValueError):
        st.RecoveryOutcome(
            episode_id="e1",
            outcome="not_a_real_outcome",
            time_to_recovery_s=Measured.absent(Validity.NOT_APPLICABLE, "x", unit="s"),
        )


def test_recovery_edge_cases_are_absent_not_zero() -> None:
    never = st.recovery_summary(
        [_unrecovered("e1", "never_affected", "no capability loss in this episode")],
        deadline_s=30.0,
    )
    assert never.recovery_fraction_at_deadline.value is None
    assert never.recovery_fraction_at_deadline.validity is Validity.NOT_APPLICABLE
    assert never.conditional_mean_recovered_s.value is None

    none_recovered = st.recovery_summary(
        [_unrecovered("e1", "censored_episode_end", "threshold_not_reached_within_episode")],
        deadline_s=30.0,
    )
    assert none_recovered.recovery_fraction_at_deadline.value == pytest.approx(0.0)
    assert none_recovered.conditional_mean_recovered_s.value is None
    assert none_recovered.conditional_mean_recovered_s.validity is Validity.NOT_APPLICABLE

    with pytest.raises(ValueError):
        st.recovery_summary([_recovered("e1", 1.0)], deadline_s=0.0)


def test_recovery_outcome_from_report_uses_the_reference_definition() -> None:
    recovered = st.recovery_outcome_from_report(
        {
            "applicable": True,
            "censored": False,
            "recovery_time_s": 140.0,
            "time_to_recovery_s": 40.0,
            "censoring_reason": None,
        },
        episode_id="e1",
    )
    assert recovered.outcome == "recovered"
    assert recovered.time_to_recovery_s.value == pytest.approx(40.0)

    repaired = st.recovery_outcome_from_report(
        {
            "applicable": True,
            "censored": True,
            "recovery_time_s": None,
            "time_to_recovery_s": None,
            "censoring_reason": "repaired_before_recovery_threshold_reached",
        },
        episode_id="e2",
    )
    assert repaired.outcome == "censored_automatic_repair"
    assert repaired.time_to_recovery_s.value is None

    after_repair = st.recovery_outcome_from_report(
        {
            "applicable": True,
            "censored": True,
            "time_to_recovery_s": None,
            "censoring_reason": "threshold_first_met_after_automatic_repair",
        },
        episode_id="e3",
    )
    assert after_repair.outcome == "censored_automatic_repair"

    ended = st.recovery_outcome_from_report(
        {
            "applicable": True,
            "censored": True,
            "time_to_recovery_s": None,
            "censoring_reason": "threshold_not_reached_within_episode",
        },
        episode_id="e4",
    )
    assert ended.outcome == "censored_episode_end"

    unaffected = st.recovery_outcome_from_report(
        {
            "applicable": False,
            "reason": "the failure harmed no demand point in the healthy reference",
            "recovery_time_s": None,
            "censored": False,
            "censoring_reason": None,
        },
        episode_id="e5",
    )
    assert unaffected.outcome == "never_affected"
    assert unaffected.time_to_recovery_s.validity is Validity.NOT_APPLICABLE


# --------------------------------------------------------------------------------------
# Serialisation
# --------------------------------------------------------------------------------------


def test_results_serialise_to_strict_json(tmp_path) -> None:
    aggregation = st.aggregate_episodes_to_units(
        rate_rows({"f1": [10.0, 12.0], "f2": [20.0], "f3": [30.0]}),
        metric_name="mean_delivered_mbps",
    )
    reduction = st.reduce_units(aggregation)
    paired = st.paired_difference(
        aggregation, aggregation, pairing_evidence="matching_seed_number_only"
    )
    summary = st.recovery_summary(
        [
            _recovered("e1", 12.0),
            _unrecovered("e2", "censored_automatic_repair", "repaired_before_recovery_threshold_reached"),
        ],
        deadline_s=20.0,
    )

    for payload in (
        aggregation.to_json(),
        reduction.to_json(),
        paired.to_json(),
        summary.to_json(),
    ):
        text = dumps(payload)
        assert "NaN" not in text and "Infinity" not in text
        assert loads(text) is not None

    target = tmp_path / "reduction.json"
    target.write_text(dumps(reduction.to_json(), indent=2), encoding="utf-8")
    restored = loads(target.read_text(encoding="utf-8"))
    assert restored["n_units"] == 3
    assert restored["point"]["validity"] == "ok"
    assert restored["excluded"] == {}
    assert loads(dumps(aggregation.to_json()))["n_excluded_rows"] == 0
