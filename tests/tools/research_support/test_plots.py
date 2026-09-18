"""Tests for the figure contract and the C01-C14 capability charts.

These tests are written against the properties that make a figure auditable rather than
against pixel output: the exported table must reproduce the drawn numbers exactly, a
single fit must not receive an interval, an unrecovered episode must not be drawn at zero,
three demand states must stay visually distinct, categorical skill identifiers must never
be averaged, and an unsatisfied input contract must produce a named hole.

The statistics and catalog modules are developed separately, so every statistical branch
here is exercised through a duck-typed stand-in defined in this file. That keeps the chart
behaviour under test independent of the reducer's internals, and it lets the "statistics
unavailable" branch be checked without uninstalling anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pytest

from tools.research_support.plots import capability
from tools.research_support.plots.figure import (
    DEFAULT_SYNTHETIC_BANNER,
    FigureResult,
    FigureSpec,
    apply_method_style,
    close_figure,
    export_figure,
    missing_panel,
    new_figure,
    read_table_csv,
    render_rgb_array,
    software_versions,
)
from tools.research_support.records import (
    AggregationLevel,
    DecisionEvent,
    EntityId,
    EntityKind,
    GroundEntityState,
    LinkActivity,
    LinkRecord,
    Measured,
    MetricRecord,
    Phase,
    ResourceDomainRecord,
    SceneGeometry,
    SourceKind,
    UavState,
    Validity,
    XKind,
)

PNG_ONLY: dict[str, Any] = {"formats": ("png",)}


# --------------------------------------------------------------------------------------
# Duck-typed stand-ins for the concurrently developed statistics module
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FakeUnitValue:
    unit_id: str
    value: Measured
    n_episodes: int = 1
    n_invalid_episodes: int = 0
    weights_note: str | None = None


@dataclass(frozen=True)
class FakeUnitAggregation:
    metric_name: str
    unit_kind: str
    units: tuple[FakeUnitValue, ...]
    excluded: dict[str, int] = field(default_factory=dict)
    n_source_rows: int = 0
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FakeReduction:
    metric_name: str
    unit_kind: str
    n_units: int
    point: Measured
    sd: Measured
    se: Measured
    ci_low: Measured
    ci_high: Measured
    ci_method: str
    ci_level: float
    degenerate_variance: bool = False
    excluded: dict[str, int] = field(default_factory=dict)
    per_unit: tuple[FakeUnitValue, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FakePairedReduction:
    metric_name: str
    n_pairs: int
    pairing_status: str
    point: Measured
    sd: Measured
    se: Measured
    ci_low: Measured
    ci_high: Measured
    ci_method: str
    ci_level: float
    unmatched_a: tuple[str, ...] = ()
    unmatched_b: tuple[str, ...] = ()
    incomplete_pairs: int = 0
    degenerate_variance: bool = False
    notes: tuple[str, ...] = ()
    fallback_unpaired: FakeReduction | None = None


@dataclass(frozen=True)
class FakeRecoverySummary:
    n_episodes: int
    recovery_fraction_at_deadline: Measured
    conditional_mean_recovered_s: Measured
    deadline_s: float


class FakeStatistics:
    """Minimal stand-in honouring the declared statistics interface."""

    def __init__(self, *, pairing_status: str = "paired") -> None:
        self.pairing_status = pairing_status

    def aggregate_episodes_to_units(
        self,
        records: Sequence[Any],
        *,
        metric_name: str,
        unit_field: str = "training_replicate_id",
        weights: Any = None,
        catalog_lookup: Any = None,
    ) -> FakeUnitAggregation:
        buckets: dict[str, list[float]] = {}
        for record in records:
            if record.metric_name != metric_name:
                continue
            if record.value.validity is not Validity.OK:
                continue
            unit_id = str(getattr(record, unit_field, None) or "unlabelled")
            buckets.setdefault(unit_id, []).append(float(record.value.value))
        units = tuple(
            FakeUnitValue(
                unit_id=unit_id,
                value=Measured.ok(float(np.mean(values))),
                n_episodes=len(values),
            )
            for unit_id, values in sorted(buckets.items())
        )
        return FakeUnitAggregation(
            metric_name=metric_name,
            unit_kind=unit_field,
            units=units,
            n_source_rows=len(records),
        )

    def reduce_units(
        self,
        aggregation: FakeUnitAggregation,
        *,
        ci_method: str = "student_t",
        ci_level: float = 0.95,
        rng_seed: int | None = None,
        n_resamples: int = 9999,
    ) -> FakeReduction:
        values = [float(unit.value.value) for unit in aggregation.units]
        point = Measured.ok(float(np.mean(values))) if values else Measured.unknown("no_units")
        if len(values) < 2:
            absent = Measured.unknown("single_unit_has_no_cross_unit_spread")
            return FakeReduction(
                metric_name=aggregation.metric_name,
                unit_kind=aggregation.unit_kind,
                n_units=len(values),
                point=point,
                sd=absent,
                se=absent,
                ci_low=absent,
                ci_high=absent,
                ci_method="unavailable",
                ci_level=ci_level,
                per_unit=aggregation.units,
            )
        sd = float(np.std(values, ddof=1))
        mean = float(np.mean(values))
        return FakeReduction(
            metric_name=aggregation.metric_name,
            unit_kind=aggregation.unit_kind,
            n_units=len(values),
            point=point,
            sd=Measured.ok(sd),
            se=Measured.ok(sd / np.sqrt(len(values))),
            ci_low=Measured.ok(mean - sd),
            ci_high=Measured.ok(mean + sd),
            ci_method=ci_method,
            ci_level=ci_level,
            degenerate_variance=sd == 0.0,
            per_unit=aggregation.units,
        )

    def paired_difference(
        self,
        a: FakeUnitAggregation,
        b: FakeUnitAggregation,
        *,
        pairing_evidence: Any,
        ci_method: str = "student_t",
        ci_level: float = 0.95,
        rng_seed: int | None = None,
        n_resamples: int = 9999,
    ) -> FakePairedReduction:
        values_a = {unit.unit_id: float(unit.value.value) for unit in a.units}
        values_b = {unit.unit_id: float(unit.value.value) for unit in b.units}
        shared = sorted(set(values_a) & set(values_b))
        differences = [values_a[key] - values_b[key] for key in shared]
        if self.pairing_status != "paired" or not differences:
            absent = Measured.unknown("pairing_not_verified")
            return FakePairedReduction(
                metric_name=a.metric_name,
                n_pairs=len(differences),
                pairing_status=self.pairing_status,
                point=absent,
                sd=absent,
                se=absent,
                ci_low=absent,
                ci_high=absent,
                ci_method="unavailable",
                ci_level=ci_level,
                unmatched_a=tuple(sorted(set(values_a) - set(values_b))),
                unmatched_b=tuple(sorted(set(values_b) - set(values_a))),
            )
        mean = float(np.mean(differences))
        sd = float(np.std(differences, ddof=1)) if len(differences) > 1 else 0.0
        return FakePairedReduction(
            metric_name=a.metric_name,
            n_pairs=len(differences),
            pairing_status="paired",
            point=Measured.ok(mean),
            sd=Measured.ok(sd),
            se=Measured.ok(sd / np.sqrt(len(differences))) if differences else Measured.unknown("n"),
            ci_low=Measured.ok(mean - sd),
            ci_high=Measured.ok(mean + sd),
            ci_method=ci_method,
            ci_level=ci_level,
            unmatched_a=tuple(sorted(set(values_a) - set(values_b))),
            unmatched_b=tuple(sorted(set(values_b) - set(values_a))),
        )

    def recovery_summary(self, outcomes: Sequence[Any], *, deadline_s: float) -> FakeRecoverySummary:
        recovered = [
            float(o.time_to_recovery_s.value)
            for o in outcomes
            if o.time_to_recovery_s.validity is Validity.OK
        ]
        by_deadline = [t for t in recovered if t <= deadline_s]
        return FakeRecoverySummary(
            n_episodes=len(outcomes),
            recovery_fraction_at_deadline=Measured.ok(len(by_deadline) / max(1, len(outcomes))),
            conditional_mean_recovered_s=(
                Measured.ok(float(np.mean(recovered)), unit="s")
                if recovered
                else Measured.unknown("no_recovered_episode")
            ),
            deadline_s=float(deadline_s),
        )


@dataclass
class FakeOutcome:
    """Duck-typed :class:`RecoveryOutcome` used by the C04 tests."""

    episode_id: str
    outcome: str
    time_to_recovery_s: Measured
    reason: str = ""
    observation_limit_s: Measured | None = None


def fake_options(**extra: Any) -> dict[str, Any]:
    options: dict[str, Any] = dict(PNG_ONLY)
    options["statistics_module"] = FakeStatistics()
    options.update(extra)
    return options


# --------------------------------------------------------------------------------------
# Record helpers
# --------------------------------------------------------------------------------------


def metric_record(
    name: str,
    value: float | None,
    x_value: float | int | None,
    *,
    method: str = "hmasd",
    fit: str = "fit_a",
    unit: str = "dimensionless",
    phase: Phase = Phase.EVALUATION,
    level: AggregationLevel = AggregationLevel.REPLICATE,
    x_kind: XKind = XKind.CHECKPOINT_STEP,
    world: str | None = None,
    episode: str | None = None,
    validity: Validity | None = None,
    source_path: str = "fixtures/metrics.jsonl",
) -> MetricRecord:
    measured = (
        Measured.ok(value, unit=unit)
        if validity is None
        else Measured.absent(validity, "fixture_absent", unit=unit)
    )
    return MetricRecord(
        run_id="run_fixture",
        method_id=method,
        metric_name=name,
        value=measured,
        x_kind=x_kind,
        x_value=x_value,
        phase=phase,
        aggregation_level=level,
        training_replicate_id=fit,
        world_id=world,
        episode_id=episode,
        unit=unit,
        source_path=source_path,
    )


def vertical_segments(ax: Any) -> list[tuple[float, float, float]]:
    """Two-point line artists with a constant x: the shape an interval bar is drawn with."""

    found: list[tuple[float, float, float]] = []
    for line in ax.get_lines():
        xs = list(np.atleast_1d(line.get_xdata()))
        ys = list(np.atleast_1d(line.get_ydata()))
        if len(xs) == 2 and len(ys) == 2 and xs[0] == xs[1]:
            found.append((float(xs[0]), float(ys[0]), float(ys[1])))
    return found


def rows_with_role(result: FigureResult, role: str) -> list[dict[str, Any]]:
    return [row for row in result.table if str(row.get("role", "")) == role]


def release(result: FigureResult) -> None:
    close_figure(result.figure)
    result.figure = None


# --------------------------------------------------------------------------------------
# Figure contract
# --------------------------------------------------------------------------------------


def test_software_versions_reports_the_running_interpreter() -> None:
    versions = software_versions()
    assert versions["python"].startswith("3.")
    assert versions["numpy"] == np.__version__
    assert versions["matplotlib_backend"].lower() == "agg"


def test_render_rgb_array_is_three_channel_uint8() -> None:
    fig, ax = new_figure(figsize=(3.0, 2.0), dpi=100)
    ax.plot([0.0, 1.0], [0.0, 1.0])
    array = render_rgb_array(fig)
    assert array.ndim == 3
    assert array.shape[2] == 3
    assert array.dtype == np.uint8
    assert array.shape[:2] == (200, 300)
    close_figure(fig)


def test_apply_method_style_separates_methods_by_more_than_colour() -> None:
    styles = apply_method_style(None, ["a", "b", "c"])
    assert len({style["color"] for style in styles.values()}) == 3
    assert len({style["marker"] for style in styles.values()}) == 3
    assert len({str(style["linestyle"]) for style in styles.values()}) == 3
    high = apply_method_style(None, ["a", "b", "c"], high_contrast=True)
    assert {style["color"] for style in high.values()} != {style["color"] for style in styles.values()}
    assert len({style["marker"] for style in high.values()}) == 3


def test_export_figure_table_reproduces_the_drawn_points_exactly(tmp_path: Path) -> None:
    xs = [0.0, 1.0, 2.0]
    ys = [0.1 + 0.2, 1.0 / 3.0, -2.5e-7]
    fig, ax = new_figure(figsize=(4.0, 3.0), dpi=100)
    line = ax.plot(xs, ys, marker="o", label="series (Mbps)")[0]
    drawn_y = [float(value) for value in line.get_ydata()]
    spec = FigureSpec(
        figure_id="TEST",
        title="Round trip (Mbps)",
        question="Does the table reproduce the drawn points?",
        x_label="x (s)",
        y_label="y (Mbps)",
        metric_definition="fixture series",
    )
    result = FigureResult(
        spec=spec,
        table=[
            {"role": "series_point", "x_value": x, "value": y, "unit": "Mbps"}
            for x, y in zip(xs, ys)
        ],
    )
    result = export_figure(fig, result, tmp_path, formats=("png", "svg", "pdf"))

    assert result.png_path and result.png_path.exists()
    assert result.svg_path and result.svg_path.exists()
    assert result.pdf_path and result.pdf_path.exists()
    assert result.spec_path and result.spec_path.exists()
    assert (tmp_path / "TEST_table.json").exists()

    written = read_table_csv(result.table_path)
    assert [float(row["x_value"]) for row in written] == xs
    assert [float(row["value"]) for row in written] == ys  # exact, not approximate
    assert drawn_y == [float(row["value"]) for row in written]


def test_export_figure_stamps_the_synthetic_banner(tmp_path: Path) -> None:
    fig, ax = new_figure(figsize=(4.0, 3.0), dpi=100)
    ax.plot([0.0, 1.0], [0.0, 1.0])
    spec = FigureSpec(
        figure_id="BANNER",
        title="Fixture (Mbps)",
        question="q",
        x_label="x (s)",
        y_label="y (Mbps)",
        metric_definition="fixture",
        synthetic_banner=DEFAULT_SYNTHETIC_BANNER,
    )
    result = export_figure(
        fig, FigureResult(spec=spec, table=[]), tmp_path, formats=("png",), close=False
    )
    texts = [text.get_text() for text in result.figure.texts]
    assert DEFAULT_SYNTHETIC_BANNER in texts
    assert DEFAULT_SYNTHETIC_BANNER in result.spec_path.read_text(encoding="utf-8")
    # Re-exporting must not stack a second banner on the same figure.
    export_figure(result.figure, result, tmp_path, formats=("png",), close=False)
    assert [t.get_text() for t in result.figure.texts].count(DEFAULT_SYNTHETIC_BANNER) == 1
    release(result)


def test_missing_panel_names_the_record_and_draws_it(tmp_path: Path) -> None:
    result = missing_panel(
        "C10",
        "Robustness",
        "sweep_records",
        question="How robust is the observed performance?",
        output_dir=tmp_path,
        keep_figure=True,
    )
    assert result.rendered is False
    assert result.missing_reason == "NOT RECORDED: sweep_records"
    assert result.png_path.exists()
    drawn = [text.get_text() for ax in result.figure.axes for text in ax.texts]
    assert any("NOT RECORDED: sweep_records" in text for text in drawn)
    release(result)


# --------------------------------------------------------------------------------------
# C01
# --------------------------------------------------------------------------------------


def test_c01_draws_per_fit_lines_and_a_cross_fit_aggregate(tmp_path: Path) -> None:
    rows = [
        metric_record("service_ratio", 0.40 + 0.05 * index + step / 1000.0, step, fit=fit)
        for index, fit in enumerate(("fit_a", "fit_b", "fit_c"))
        for step in (0, 100, 200)
    ]
    training = [
        metric_record(
            "team_reward",
            1.0 + step / 100.0,
            step,
            fit="fit_a",
            phase=Phase.TRAINING,
            unit="reward",
            x_kind=XKind.TRAINING_TEAM_STEP,
        )
        for step in (0, 50, 100)
    ]
    result = capability.c01_learning_curves(
        {"evaluation_curve": rows, "training_reward": training},
        tmp_path,
        options=fake_options(keep_figure=True),
    )
    assert result.rendered
    assert result.spec.n_fits == 3
    assert rows_with_role(result, "aggregate_point")
    assert rows_with_role(result, "aggregate_interval")
    assert rows_with_role(result, "training_reward_point")
    # Training reward lives on its own panel: it is a different quantity on a different x.
    assert len(result.figure.axes) == 3
    assert "fit" in result.spec.statistical_unit

    written = read_table_csv(result.table_path)
    drawn = {
        (row["training_replicate_id"], float(row["x_value"])): float(row["value"])
        for row in written
        if row["role"] == "replicate_curve_point"
    }
    for record in rows:
        assert drawn[(record.training_replicate_id, float(record.x_value))] == record.value.value
    release(result)


def test_c01_with_one_fit_draws_no_band(tmp_path: Path) -> None:
    rows = [metric_record("service_ratio", 0.4 + step / 1000.0, step) for step in (0, 100)]
    result = capability.c01_learning_curves(
        {"evaluation_curve": rows}, tmp_path, options=fake_options(keep_figure=True)
    )
    assert result.spec.n_fits == 1
    assert rows_with_role(result, "aggregate_interval") == []
    assert len(result.figure.axes[0].collections) == 0  # a band would add a collection
    assert any("only one fit" in message for message in result.spec.warnings)
    release(result)


def test_c01_missing_evaluation_curve_names_the_record(tmp_path: Path) -> None:
    result = capability.c01_learning_curves({}, tmp_path, options=PNG_ONLY)
    assert result.rendered is False
    assert "evaluation_curve" in result.missing_reason


# --------------------------------------------------------------------------------------
# C02
# --------------------------------------------------------------------------------------


def test_c02_single_fit_draws_no_interval_and_reports_it_unavailable(tmp_path: Path) -> None:
    rows = [metric_record("service_ratio", 0.61, 200, fit="fit_only")]
    result = capability.c02_per_fit_consistency(
        {"fit_endpoints": rows}, tmp_path, options=fake_options(keep_figure=True)
    )
    assert result.spec.n_fits == 1
    assert result.spec.uncertainty_method.startswith("unavailable")
    assert rows_with_role(result, "aggregate_interval") == []
    # A zero-width bar would appear as a two-point vertical line artist.
    assert vertical_segments(result.figure.axes[0]) == []
    assert any("not an interval of width zero" in w for w in result.spec.warnings)
    release(result)


def test_c02_multiple_fits_draw_one_interval_and_keep_every_fit_in_the_table(
    tmp_path: Path,
) -> None:
    rows = [
        metric_record("service_ratio", value, 200, fit=fit)
        for fit, value in (("fit_a", 0.61), ("fit_b", 0.66), ("fit_c", 0.58))
    ]
    result = capability.c02_per_fit_consistency(
        {
            "fit_endpoints": rows,
            "fit_status": {
                "fit_a": "completed",
                "fit_b": "completed",
                "fit_c": "completed",
                "fit_d": "technical_failure:nan_loss",
            },
        },
        tmp_path,
        options=fake_options(keep_figure=True),
    )
    assert result.spec.n_fits == 3
    intervals = rows_with_role(result, "aggregate_interval")
    assert len(intervals) == 1
    assert intervals[0]["ci_low"] < intervals[0]["ci_high"]
    segments = vertical_segments(result.figure.axes[0])
    assert len(segments) == 1

    endpoints = rows_with_role(result, "fit_endpoint")
    listed = {row["training_replicate_id"] for row in endpoints}
    assert listed == {"fit_a", "fit_b", "fit_c", "fit_d"}
    failed = [row for row in endpoints if row["training_replicate_id"] == "fit_d"][0]
    assert failed["value"] is None
    assert failed["fit_status"] == "technical_failure:nan_loss"
    assert result.spec.n_failed >= 1
    # No bar-only summary: the per-fit dots are real marker artists.
    assert any(line.get_marker() not in ("", "None", None) for line in result.figure.axes[0].get_lines())
    release(result)


def test_c02_paired_panel_requires_verified_pairing(tmp_path: Path) -> None:
    primary = [
        metric_record("service_ratio", value, 200, fit=fit)
        for fit, value in (("fit_a", 0.61), ("fit_b", 0.66))
    ]
    baseline = [
        metric_record("service_ratio", value, 200, method="baseline", fit=fit)
        for fit, value in (("fit_a", 0.55), ("fit_b", 0.60))
    ]
    inputs = {
        "fit_endpoints": primary,
        "baseline_fit_endpoints": baseline,
        "pairing_evidence": {"design": "shared world block"},
    }
    unpaired = capability.c02_per_fit_consistency(
        inputs,
        tmp_path / "unpaired",
        options=fake_options(statistics_module=FakeStatistics(pairing_status="unpaired")),
    )
    assert rows_with_role(unpaired, "pair_difference") == []
    assert any("paired-difference panel not drawn" in w for w in unpaired.spec.warnings)

    paired = capability.c02_per_fit_consistency(
        inputs, tmp_path / "paired", options=fake_options()
    )
    differences = rows_with_role(paired, "pair_difference")
    assert {row["pair_unit_id"] for row in differences} == {"fit_a", "fit_b"}
    assert differences[0]["value"] == pytest.approx(0.61 - 0.55)
    assert rows_with_role(paired, "paired_interval")

    no_evidence = capability.c02_per_fit_consistency(
        {"fit_endpoints": primary, "baseline_fit_endpoints": baseline},
        tmp_path / "no_evidence",
        options=fake_options(),
    )
    assert rows_with_role(no_evidence, "pair_difference") == []


def test_c02_without_a_statistics_module_still_draws_the_fits(tmp_path: Path) -> None:
    rows = [
        metric_record("service_ratio", value, 200, fit=fit)
        for fit, value in (("fit_a", 0.61), ("fit_b", 0.66))
    ]
    result = capability.c02_per_fit_consistency(
        {"fit_endpoints": rows},
        tmp_path,
        options={**PNG_ONLY, "statistics_module": None},
    )
    assert len(rows_with_role(result, "fit_endpoint")) == 2
    assert rows_with_role(result, "aggregate_interval") == []
    assert any("statistics module unavailable" in w for w in result.spec.warnings)


# --------------------------------------------------------------------------------------
# C03
# --------------------------------------------------------------------------------------


def test_c03_uses_recorded_event_times_and_omits_unrecorded_references(tmp_path: Path) -> None:
    series = [
        metric_record(name, value, t, unit="Mbps", x_kind=XKind.SIMULATED_SECOND)
        for t in (0.0, 10.0, 20.0, 30.0)
        for name, value in (("offered_mbps", 10.0), ("delivered_mbps", 10.0 if t < 20 else 4.0))
    ]
    events = [
        DecisionEvent(time_s=17.5, event_type="site_failure", description="radio down"),
        DecisionEvent(time_s=28.25, event_type="repair", description="exogenous repair"),
    ]
    result = capability.c03_event_aligned_service(
        {
            "service_timeseries": series,
            "world_events": events,
            "healthy_reference": Measured.ok(10.0, unit="Mbps"),
            "failed_ground_reference": Measured.not_recorded("no_failed_ground_run", unit="Mbps"),
        },
        tmp_path,
        options=fake_options(),
    )
    markers = rows_with_role(result, "event_marker")
    assert [row["time_s"] for row in markers] == [17.5, 28.25]
    references = rows_with_role(result, "reference_line")
    assert [row["metric_name"] for row in references] == ["healthy_reference"]
    assert any("failed_ground_reference" in w for w in result.spec.warnings)
    assert "repair" in result.spec.caption and "exogenous" in result.spec.caption


# --------------------------------------------------------------------------------------
# C04
# --------------------------------------------------------------------------------------


def test_c04_censored_episode_is_not_at_zero_and_is_counted(tmp_path: Path) -> None:
    outcomes = [
        FakeOutcome("ep0", "recovered", Measured.ok(12.0, unit="s")),
        FakeOutcome("ep1", "recovered", Measured.ok(25.0, unit="s")),
        FakeOutcome(
            "ep2",
            "automatic_repair",
            Measured.not_recorded("never_met_criterion", unit="s"),
            reason="exogenous_repair",
            observation_limit_s=Measured.ok(40.0, unit="s"),
        ),
    ]
    result = capability.c04_recovery_times(
        {"recovery_outcomes": outcomes, "recovery_deadline_s": 30.0},
        tmp_path,
        options=fake_options(keep_figure=True),
    )
    episodes = {row["episode_id"]: row for row in rows_with_role(result, "recovery_episode")}
    assert set(episodes) == {"ep0", "ep1", "ep2"}
    censored = episodes["ep2"]
    assert censored["censored"] is True
    assert censored["time_to_recovery_s"] is None
    assert censored["plotted_y_s"] == 40.0  # its observation limit, never 0
    assert censored["plotted_y_s"] != 0.0
    assert "at least" in censored["plotted_y_meaning"]

    counts = {row["censoring_reason"]: row["count"] for row in rows_with_role(result, "censoring_reason_count")}
    assert counts == {"automatic_repair:exogenous_repair": 1}

    ax = result.figure.axes[0]
    censored_artists = [
        line for line in ax.get_lines() if "censored" in str(line.get_label())
    ]
    assert len(censored_artists) == 1
    assert censored_artists[0].get_marker() == "^"
    recovered_artists = [line for line in ax.get_lines() if "recovered:" in str(line.get_label())]
    assert recovered_artists[0].get_marker() == "o"
    assert set(np.atleast_1d(censored_artists[0].get_ydata())) == {40.0}
    assert "conditional on recovery" in result.spec.caption
    release(result)


def test_c04_without_statistics_reports_no_mean(tmp_path: Path) -> None:
    outcomes = [FakeOutcome("ep0", "recovered", Measured.ok(12.0, unit="s"))]
    result = capability.c04_recovery_times(
        {"recovery_outcomes": outcomes, "recovery_deadline_s": 30.0},
        tmp_path,
        options={**PNG_ONLY, "statistics_module": None},
    )
    assert rows_with_role(result, "recovery_summary") == []
    assert any("statistics module" in w for w in result.spec.warnings)


# --------------------------------------------------------------------------------------
# C05
# --------------------------------------------------------------------------------------


def link_frame(time_s: float, utilization: float) -> dict[str, Any]:
    uav = EntityId(EntityKind.UAV, 0)
    site = EntityId(EntityKind.SITE, 0)
    return {
        "time_s": time_s,
        "links": [
            LinkRecord(
                link_key="access_0",
                source=uav,
                target=site,
                link_class="access",
                activity=LinkActivity.ACTIVE,
                capacity_mbps=Measured.ok(20.0, unit="Mbps"),
                flow_mbps=Measured.ok(20.0 * utilization, unit="Mbps"),
                utilization=Measured.ok(utilization),
                resource_domain="domain_a",
            )
        ],
        "resource_domains": [
            ResourceDomainRecord(
                domain_id="domain_a",
                description="shared access",
                link_keys=("access_0",),
                utilization=Measured.ok(min(1.0, utilization + 0.1)),
            )
        ],
    }


def test_c05_integrates_unmet_traffic_over_recorded_intervals(tmp_path: Path) -> None:
    frames = [link_frame(float(t), 0.5 + 0.1 * index) for index, t in enumerate((0, 5, 10))]
    unmet = [
        MetricRecord(
            run_id="run_fixture",
            method_id="hmasd",
            metric_name="unmet_mbps",
            value=Measured.ok(2.0, unit="Mbps"),
            x_kind=XKind.SIMULATED_SECOND,
            x_value=float(t),
            phase=Phase.EVALUATION,
            aggregation_level=AggregationLevel.SUBINTERVAL,
            interval_start_s=float(t),
            interval_end_s=float(t) + 5.0,
            unit="Mbps",
        )
        for t in (0, 5, 10)
    ]
    result = capability.c05_capacity_bottleneck(
        {"link_frames": frames, "unmet_traffic": unmet}, tmp_path, options=fake_options()
    )
    integral = rows_with_role(result, "unmet_integral_point")
    assert [row["cumulative_unmet"] for row in integral] == [10.0, 20.0, 30.0]
    assert rows_with_role(result, "resource_domain_utilization")
    assert "isolated" in result.spec.caption and "not establish" in result.spec.caption
    assert "isolated capacity" in result.spec.metric_definition
    assert "schedulable" in result.spec.caption


def test_c05_missing_unmet_traffic_leaves_a_named_hole(tmp_path: Path) -> None:
    result = capability.c05_capacity_bottleneck(
        {"link_frames": [link_frame(0.0, 0.5)]}, tmp_path, options=fake_options()
    )
    assert result.rendered
    assert any("NOT RECORDED: unmet_traffic" in w for w in result.spec.warnings)
    assert rows_with_role(result, "unmet_integral_point") == []


# --------------------------------------------------------------------------------------
# C06
# --------------------------------------------------------------------------------------


def ground_entity(
    slot: int,
    x: float,
    offered: Measured | None,
    delivered: Measured | None,
    *,
    kind: EntityKind = EntityKind.INDIVIDUAL_UE,
    represents: int = 1,
) -> GroundEntityState:
    return GroundEntityState(
        entity=EntityId(kind, slot),
        position_m=(x, 100.0, 0.0),
        offered_mbps=offered,
        delivered_mbps=delivered,
        represents_count=represents,
        observed=offered is not None and offered.validity is Validity.OK,
    )


def test_c06_keeps_zero_unknown_and_unserved_visually_distinct(tmp_path: Path) -> None:
    entities = [
        ground_entity(0, 100.0, Measured.ok(0.0, unit="Mbps"), Measured.ok(0.0, unit="Mbps")),
        ground_entity(1, 200.0, Measured.unknown("not_observed", unit="Mbps"), None),
        ground_entity(2, 300.0, Measured.ok(3.0, unit="Mbps"), Measured.ok(0.0, unit="Mbps")),
    ]
    result = capability.c06_spatial_service(
        {"ground_entities": entities, "geometry": SceneGeometry(bounds_m=(0.0, 0.0, 400.0, 200.0))},
        tmp_path,
        options=fake_options(keep_figure=True),
    )
    statuses = {row["entity_key"]: row["status"] for row in rows_with_role(result, "map_marker_offered_mbps")}
    assert statuses == {
        "individual_ue:0:0": "zero_demand",
        "individual_ue:1:0": "demand_unknown",
        "individual_ue:2:0": "unserved",
    }

    ax = result.figure.axes[0]
    by_state = {}
    for collection in ax.collections:
        label = str(collection.get_label())
        for state, style in capability._DEMAND_STATE_STYLE.items():
            if style["label"].split(" (")[0] in label:
                by_state[state] = collection
    assert {"zero_demand", "demand_unknown", "unserved"} <= set(by_state)
    shapes = {
        state: by_state[state].get_paths()[0].vertices.tobytes()
        for state in ("zero_demand", "demand_unknown", "unserved")
    }
    assert len(set(shapes.values())) == 3  # three different marker shapes
    assert by_state["demand_unknown"].get_hatch() == "xxx"
    assert by_state["zero_demand"].get_hatch() in (None, "")
    zero_face = by_state["zero_demand"].get_facecolor()
    unserved_face = by_state["unserved"].get_facecolor()
    assert zero_face.shape[0] == 0 or zero_face[0][3] == 0.0  # unfilled
    assert unserved_face[0][3] > 0.0  # filled
    release(result)


def test_c06_marker_size_scales_with_area_not_radius(tmp_path: Path) -> None:
    entities = [
        ground_entity(0, 100.0, Measured.ok(1.0, unit="Mbps"), Measured.ok(1.0, unit="Mbps")),
        ground_entity(1, 200.0, Measured.ok(4.0, unit="Mbps"), Measured.ok(4.0, unit="Mbps")),
    ]
    result = capability.c06_spatial_service(
        {"ground_entities": entities}, tmp_path, options=fake_options(keep_figure=True)
    )
    served = [
        row
        for row in rows_with_role(result, "map_marker_offered_mbps")
        if row["status"] == "served"
    ]
    areas = {row["weight"]: row["marker_area_points2"] for row in served}
    assert areas[4.0] / areas[1.0] == pytest.approx(4.0)  # area ratio, not sqrt(4) = 2
    ax = result.figure.axes[0]
    sizes = sorted(float(size) for collection in ax.collections for size in collection.get_sizes())
    assert sizes[-1] / sizes[-2] == pytest.approx(4.0)
    assert rows_with_role(result, "size_scale_reference")
    assert rows_with_role(result, "scale_bar")
    assert ax.get_aspect() == 1.0
    release(result)


def test_c06_labels_aggregate_points_as_aggregates(tmp_path: Path) -> None:
    entities = [
        ground_entity(
            0,
            100.0,
            Measured.ok(4.0, unit="Mbps"),
            Measured.ok(4.0, unit="Mbps"),
            kind=EntityKind.AGGREGATE_DEMAND_POINT,
            represents=25,
        )
    ]
    result = capability.c06_spatial_service(
        {"ground_entities": entities}, tmp_path, options=fake_options(keep_figure=True)
    )
    labels = [str(collection.get_label()) for collection in result.figure.axes[0].collections]
    assert any("aggregate demand point, not a person" in label for label in labels)
    assert any("aggregate demand point" in w for w in result.spec.warnings)
    assert "no per-person demand is fabricated" in result.spec.caption
    release(result)


# --------------------------------------------------------------------------------------
# C07
# --------------------------------------------------------------------------------------


def test_c07_reports_motion_effort_in_seconds_and_no_energy_claim(tmp_path: Path) -> None:
    uav = EntityId(EntityKind.UAV, 0)
    frames = [
        {
            "time_s": float(t),
            "uavs": [
                UavState(
                    entity=uav,
                    position_m=(100.0 + 10.0 * index, 100.0, 80.0),
                    executed_velocity_mps=(2.0, 0.0, 0.0),
                    requested_velocity_mps=(2.5, 0.0, 0.0),
                )
            ],
        }
        for index, t in enumerate((0.0, 5.0, 10.0))
    ]
    result = capability.c07_controller_behaviour(
        {"uav_frames": frames}, tmp_path, options=fake_options(reference_speed_mps=4.0)
    )
    summary = rows_with_role(result, "uav_summary")[0]
    assert summary["flight_distance_m"] == pytest.approx(20.0)
    assert summary["motion_effort_s"] == pytest.approx(10.0 * (2.0 / 4.0))
    assert "motion effort (s)" in result.spec.y_label
    blob = (result.spec.metric_definition + result.spec.caption).lower()
    assert "joule" in blob and "not energy" in blob
    assert "battery" in blob
    samples = rows_with_role(result, "uav_sample")
    assert all(row["recorded_energy_value"] is None for row in samples)


# --------------------------------------------------------------------------------------
# C08
# --------------------------------------------------------------------------------------


def test_c08_treats_skill_ids_as_categorical_and_never_averages_them(tmp_path: Path) -> None:
    segments = [
        {"unit": "team", "skill_id": 1, "start_s": 0.0, "end_s": 10.0, "renewed": False},
        {"unit": "team", "skill_id": 2, "start_s": 10.0, "end_s": 25.0, "renewed": True},
        {"unit": "uav:0:0", "skill_id": 0, "start_s": 0.0, "end_s": 12.0, "renewed": False},
    ]
    result = capability.c08_skill_organization(
        {"skill_segments": segments}, tmp_path, options=fake_options()
    )
    skill_rows = rows_with_role(result, "skill_segment")
    assert all(isinstance(row["skill_id"], str) for row in skill_rows)
    assert {row["skill_id"] for row in skill_rows} == {"0", "1", "2"}
    assert [row["duration_s"] for row in skill_rows] == [10.0, 15.0, 12.0]

    columns = {key for row in result.table for key in row}
    assert not any(
        "skill" in column and any(token in column for token in ("mean", "avg", "average"))
        for column in columns
    )
    written = read_table_csv(result.table_path)
    for row in written:
        if row.get("role") == "skill_id_inventory":
            assert row["skill_id"] in {"0", "1", "2"}
    assert "permut" in result.spec.caption
    assert rows_with_role(result, "duration_bin")


# --------------------------------------------------------------------------------------
# C09
# --------------------------------------------------------------------------------------


def test_c09_separates_two_lifetimes_that_share_an_array_slot(tmp_path: Path) -> None:
    intervals = [
        {"entity": EntityId(EntityKind.UAV, 3, 0), "join_s": 0.0, "leave_s": 40.0},
        {"entity": EntityId(EntityKind.UAV, 3, 1), "join_s": 90.0, "leave_s": None},
    ]
    result = capability.c09_roster_changes(
        {"membership_intervals": intervals}, tmp_path, options=fake_options()
    )
    rows = rows_with_role(result, "membership_interval")
    assert [row["lifetime_key"] for row in rows] == ["uav:3:0", "uav:3:1"]
    assert {row["generation"] for row in rows} == {0, 1}
    assert rows[1]["leave_s"] is None
    assert rows[1]["status"].startswith("continuing")
    assert any("more than one lifetime" in w for w in result.spec.warnings)


# --------------------------------------------------------------------------------------
# C10 - C14 and the registry
# --------------------------------------------------------------------------------------


def test_c10_reads_recorded_levels_only(tmp_path: Path) -> None:
    rows = [
        metric_record("service_ratio", 0.7 - 0.05 * level, level, fit=fit, x_kind=XKind.NONE)
        for level in (1, 2)
        for fit in ("fit_a", "fit_b")
    ]
    result = capability.c10_robustness_sweep(
        {"sweep_records": rows, "factor_name": "demand intensity", "factor_unit": "x nominal"},
        tmp_path,
        options=fake_options(),
    )
    levels = sorted({row["factor_level"] for row in rows_with_role(result, "sweep_observation")})
    assert levels == [1.0, 2.0]
    assert "no robustness study was launched" in result.spec.caption


def test_c12_marks_invalid_samples_without_giving_them_a_value(tmp_path: Path) -> None:
    rows = [
        metric_record("actor_loss", 0.5, 0, x_kind=XKind.UPDATE_INDEX),
        metric_record("actor_loss", 0.4, 1, x_kind=XKind.UPDATE_INDEX),
        metric_record("actor_loss", None, 2, x_kind=XKind.UPDATE_INDEX, validity=Validity.INVALID),
    ]
    result = capability.c12_training_mechanics(
        {"training_diagnostics": rows}, tmp_path, options=fake_options()
    )
    markers = rows_with_role(result, "invalid_marker")
    assert len(markers) == 1
    assert markers[0]["value"] is None
    assert "not a measurement" in markers[0]["status"]
    assert "recomputed here" in result.spec.metric_definition
    assert "forward pass" in result.spec.metric_definition


def test_c14_lists_unmatched_worlds_instead_of_drawing_them_as_zero(tmp_path: Path) -> None:
    rows = [
        metric_record("service_ratio", value, None, method=method, world=world, fit=f"fit_{world}")
        for method, values in (("hmasd", (0.62, 0.66)), ("baseline", (0.58, 0.60)))
        for world, value in zip(("w1", "w2"), values)
    ]
    rows.append(metric_record("service_ratio", 0.5, None, method="hmasd", world="w9", fit="fit_w9"))
    result = capability.c14_shared_world_difference(
        {"world_differences": rows, "method_a": "hmasd", "method_b": "baseline"},
        tmp_path,
        options=fake_options(),
    )
    differences = {row["world_id"]: row["difference"] for row in rows_with_role(result, "world_difference")}
    assert differences["w1"] == pytest.approx(0.04)
    assert "w9" not in differences
    unmatched = rows_with_role(result, "unmatched_world")
    assert [row["world_id"] for row in unmatched] == ["w9"]
    assert "No winner is declared" in result.spec.caption


def test_c14_refuses_to_difference_mismatched_units(tmp_path: Path) -> None:
    rows = [
        metric_record("throughput", 5.0, None, method="hmasd", world="w1", unit="Mbps"),
        metric_record("throughput", 5.0, None, method="baseline", world="w1", unit="kbps"),
    ]
    result = capability.c14_shared_world_difference(
        {"world_differences": rows, "method_a": "hmasd", "method_b": "baseline"},
        tmp_path,
        options=fake_options(),
    )
    assert rows_with_role(result, "world_difference") == []
    assert any("non-comparable metric units" in w for w in result.spec.warnings)


@pytest.mark.parametrize("chart_id", sorted(capability.CHART_REGISTRY))
def test_every_chart_reports_a_named_missing_panel_for_empty_inputs(
    chart_id: str, tmp_path: Path
) -> None:
    entry = capability.CHART_REGISTRY[chart_id]
    result = entry.function({}, tmp_path / chart_id, options=PNG_ONLY)
    assert result.rendered is False
    assert result.missing_reason.startswith("NOT RECORDED: ")
    assert any(
        required.split(" ")[0] in result.missing_reason for required in entry.required_inputs
    )
    assert result.png_path.exists()
    assert entry.suite == "capability"
    assert entry.question


def test_registry_covers_c01_to_c14_and_the_first_report_set() -> None:
    assert sorted(capability.CHART_REGISTRY) == [f"C{index:02d}" for index in range(1, 15)]
    assert set(capability.FIRST_REPORT_CHARTS) <= set(capability.CHART_REGISTRY)
    assert set(capability.FIRST_REPORT_CHARTS) == {"C02", "C03", "C04", "C05", "C06", "C07", "C14"}


def test_charts_mark_fixture_inputs_with_the_synthetic_banner(tmp_path: Path) -> None:
    rows = [metric_record("service_ratio", 0.5, 100)]
    result = capability.c01_learning_curves(
        {"evaluation_curve": rows, "source_kind": SourceKind.SYNTHETIC_FIXTURE},
        tmp_path,
        options=fake_options(),
    )
    assert result.spec.synthetic_banner == DEFAULT_SYNTHETIC_BANNER
    assert DEFAULT_SYNTHETIC_BANNER in result.spec_path.read_text(encoding="utf-8")
