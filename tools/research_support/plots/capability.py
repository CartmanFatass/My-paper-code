"""Capability charts C01-C14: one standalone function per research question.

Each function answers a question a researcher can inspect, rather than producing a
picture that makes training look active. Three rules shape every function here.

1. **The input contract is checked first.** When the record a chart needs is absent the
   function returns :func:`~tools.research_support.plots.figure.missing_panel`, which
   names the missing record. No chart substitutes a different metric, rescales a proxy,
   or quietly drops itself from the report.
2. **Everything drawn is in the table.** Interval endpoints, reference lines, censoring
   markers and event markers all get rows, because a reader must be able to reconstruct
   the image from the CSV.
3. **The statistics live elsewhere.** Aggregation, intervals, pairing verification and
   recovery summaries come from ``tools.research_support.statistics``, imported lazily so
   this module is importable on its own and testable against a stand-in. When that module
   is unavailable the charts still draw the raw per-unit points and say in a warning that
   no aggregate or interval could be computed - they never fall back to a hand-rolled
   reduction whose rules nobody declared.

Restrictions from the plan's chart table are enforced in code, not only in prose: see the
per-function docstrings for the specific restriction each one carries.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

from ..records import (
    AggregationLevel,
    EntityId,
    Measured,
    MetricRecord,
    Phase,
    Validity,
)
from .figure import (
    ANNOTATION_FONT_SIZE,
    FigureResult,
    FigureSpec,
    LEGEND_FONT_SIZE,
    apply_method_style,
    export_figure,
    finish_axes,
    measured_status,
    measured_value,
    missing_panel,
    new_figure,
    provenance_entry,
    synthetic_banner_for,
    trailing_mean,
)

# --------------------------------------------------------------------------------------
# Lazy access to the concurrently developed statistics and catalog modules
# --------------------------------------------------------------------------------------


def _load_statistics(options: Mapping[str, Any] | None) -> Any | None:
    """Import the statistics module lazily, or accept an injected stand-in.

    Lazy because this module must import cleanly before ``statistics.py`` exists, and
    injectable because the chart tests exercise the statistical branches against a
    duck-typed object rather than the real reducer.
    """

    if options and "statistics_module" in options:
        # Present-but-None is a deliberate "pretend it is unavailable", which is how the
        # degraded branch is exercised without uninstalling anything.
        return options["statistics_module"] or None
    try:
        from .. import statistics as statistics_module  # type: ignore[attr-defined]
    except ImportError:
        return None
    return statistics_module


def _load_catalog(options: Mapping[str, Any] | None) -> Any | None:
    """Import the metric catalog lazily, or accept an injected stand-in."""

    if options and "catalog_module" in options:
        return options["catalog_module"] or None
    try:
        from .. import catalog as catalog_module  # type: ignore[attr-defined]
    except ImportError:
        return None
    return catalog_module


def _metric_definition(
    metric_name: str, options: Mapping[str, Any] | None, fallback: str
) -> tuple[str, str | None]:
    """Return ``(definition text, unit)`` from the catalog when it can answer.

    The fallback text describes what this chart drew; it never invents a unit.
    """

    catalog = _load_catalog(options)
    if catalog is not None:
        try:
            definition = catalog.try_metric_definition(metric_name)
        except Exception:
            definition = None
        if definition is not None:
            text = getattr(definition, "description", None) or getattr(
                definition, "definition_id", ""
            )
            unit = getattr(definition, "unit", None)
            direction = getattr(definition, "direction", None)
            pieces = [p for p in (str(text), f"direction: {direction}" if direction else "") if p]
            return "; ".join(pieces) or fallback, unit
    return fallback, None


def _statistics_unavailable_note(stats: Any | None) -> list[str]:
    if stats is None:
        return [
            "statistics module unavailable: per-unit points are drawn raw and no "
            "aggregate, interval or pairing verdict is shown"
        ]
    return []


def _reduce_units(
    stats: Any | None,
    rows: Sequence[MetricRecord],
    *,
    metric_name: str,
    unit_field: str = "training_replicate_id",
    weights: Any = None,
    ci_method: str = "student_t",
    ci_level: float = 0.95,
    rng_seed: int | None = None,
) -> tuple[Any | None, Any | None, list[str]]:
    """Aggregate episodes to units and reduce, returning ``(aggregation, reduction, notes)``.

    Every failure mode - module absent, signature drift, degenerate input - is reported as
    a note and yields ``None``, so a chart degrades to raw points instead of crashing a
    whole report.
    """

    notes = _statistics_unavailable_note(stats)
    if stats is None:
        return None, None, notes
    try:
        aggregation = stats.aggregate_episodes_to_units(
            list(rows), metric_name=metric_name, unit_field=unit_field, weights=weights
        )
    except Exception as error:
        return None, None, [f"aggregate_episodes_to_units failed: {type(error).__name__}: {error}"]
    try:
        reduction = stats.reduce_units(
            aggregation, ci_method=ci_method, ci_level=ci_level, rng_seed=rng_seed
        )
    except Exception as error:
        return aggregation, None, [f"reduce_units failed: {type(error).__name__}: {error}"]
    return aggregation, reduction, notes


def _interval_is_drawable(reduction: Any | None, n_units: int) -> bool:
    """A cross-unit interval is drawn only when it exists and covers at least two units.

    One fit has no cross-fit interval. Drawing a zero-width bar there would assert
    certainty the data cannot support, which is exactly the failure the plan forbids.
    """

    if reduction is None or n_units < 2:
        return False
    method = str(getattr(reduction, "ci_method", "unavailable") or "unavailable")
    if method.lower().startswith("unavail"):
        return False
    low = measured_value(getattr(reduction, "ci_low", None))
    high = measured_value(getattr(reduction, "ci_high", None))
    return low is not None and high is not None


def _uncertainty_label(reduction: Any | None, n_units: int, *, unit_kind: str) -> str:
    if n_units <= 1:
        return (
            f"unavailable (n_{unit_kind}=1; a cross-{unit_kind} interval is undefined for one "
            "unit and a point estimate is not a zero-width interval)"
        )
    if reduction is None:
        return "unavailable (no reducer available; raw per-unit points only)"
    method = str(getattr(reduction, "ci_method", "unavailable") or "unavailable")
    level = getattr(reduction, "ci_level", None)
    degenerate = bool(getattr(reduction, "degenerate_variance", False))
    text = f"{method} interval over {unit_kind} values"
    if level is not None:
        text += f" at level {float(level):.2f}"
    text += f" (n={int(n_units)})"
    if degenerate:
        text += "; empirical variance is degenerate (reported as degenerate, not as certainty)"
    return text


def _summary_annotation_lines(summary: Any) -> list[str]:
    """Format a statistics summary object without assuming its exact field names.

    The recovery summary is produced by a module written in parallel with this one. Rather
    than guessing attribute names, every scalar-valued public attribute is printed with
    its own name, so the annotation stays truthful if the field set differs.
    """

    lines: list[str] = []
    for name in sorted(dir(summary)):
        if name.startswith("_"):
            continue
        try:
            value = getattr(summary, name)
        except Exception:
            continue
        if callable(value):
            continue
        if isinstance(value, Measured):
            if value.validity is Validity.OK:
                lines.append(f"{name}: {value.value}{(' ' + value.unit) if value.unit else ''}")
            else:
                lines.append(f"{name}: unavailable ({value.validity.value}: {value.reason})")
        elif isinstance(value, bool):
            lines.append(f"{name}: {'yes' if value else 'no'}")
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            lines.append(f"{name}: {value}")
        elif isinstance(value, Mapping) and value:
            lines.append(f"{name}: " + ", ".join(f"{k}={v}" for k, v in sorted(value.items())))
    return lines


# --------------------------------------------------------------------------------------
# Small record helpers
# --------------------------------------------------------------------------------------


def _as_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, (str, bytes)):
        return []
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _first_missing(inputs: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    """Name the first required key that is absent or empty."""

    for key in keys:
        value = inputs.get(key)
        if value is None:
            return key
        if isinstance(value, (list, tuple, dict, set)) and len(value) == 0:
            return key
    return None


def _metric_rows(
    rows: Sequence[Any],
    *,
    metric_name: str | None = None,
    phase: Phase | None = None,
    aggregation_level: AggregationLevel | None = None,
    method_id: str | None = None,
) -> list[Any]:
    out: list[Any] = []
    for row in rows:
        if metric_name is not None and getattr(row, "metric_name", None) != metric_name:
            continue
        if phase is not None and getattr(row, "phase", None) is not phase:
            continue
        if aggregation_level is not None and getattr(row, "aggregation_level", None) is not (
            aggregation_level
        ):
            continue
        if method_id is not None and getattr(row, "method_id", None) != method_id:
            continue
        out.append(row)
    return out


def _distinct(values: Iterable[Any]) -> list[Any]:
    seen: list[Any] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


def _validity_counts(rows: Sequence[Any]) -> tuple[int, int]:
    """Return ``(n_missing, n_failed)`` over metric rows without discarding anything.

    ``INVALID`` is a technical failure of a row that was supposed to exist; the other
    non-OK statuses mean the measurement was never recorded. Both are reported.
    """

    n_missing = 0
    n_failed = 0
    for row in rows:
        value = getattr(row, "value", None)
        if not isinstance(value, Measured):
            continue
        if value.validity is Validity.OK:
            continue
        if value.validity is Validity.INVALID:
            n_failed += 1
        else:
            n_missing += 1
    return n_missing, n_failed


def _provenance_for(rows: Sequence[Any], *, kind: str, note: str | None = None) -> list[dict]:
    """One provenance entry per distinct source path, hashed over its own rows."""

    groups: dict[str | None, list[Any]] = {}
    for row in rows:
        groups.setdefault(getattr(row, "source_path", None), []).append(row)
    entries: list[dict] = []
    for source_path, group in groups.items():
        payload = [row.to_json() if hasattr(row, "to_json") else row for row in group]
        entries.append(
            provenance_entry(source_path, payload, kind=kind, n_rows=len(group), note=note)
        )
    return entries


def _record_unit(rows: Sequence[Any], fallback: str = "unit not recorded") -> str:
    units = _distinct(
        [getattr(row, "unit", None) or getattr(getattr(row, "value", None), "unit", None) for row in rows]
    )
    units = [u for u in units if u]
    if len(units) == 1:
        return str(units[0])
    if not units:
        return fallback
    return "MIXED UNITS: " + ", ".join(str(u) for u in units)


def _axis_label(name: str, unit: str | None) -> str:
    return f"{name} ({unit})" if unit else f"{name} (unit not recorded)"


def _text_panel(
    ax: Any, title: str, lines: Sequence[str], *, color: str = "#333333", wrap_at: int = 62
) -> None:
    """Render an explanatory or "not recorded" panel instead of an empty frame.

    Lines are hard-wrapped and the block is clipped to the axes: an over-wide text artist
    enlarges the axes tight bounding box, which makes the constrained layout collapse the
    neighbouring panel to zero width.
    """

    ax.axis("off")
    ax.set_title(title, fontsize=11.0)
    wrapped: list[str] = []
    for line in lines or ["(nothing to report)"]:
        text = str(line)
        if not text:
            wrapped.append("")
            continue
        while len(text) > wrap_at:
            wrapped.append(text[:wrap_at])
            text = "    " + text[wrap_at:]
        wrapped.append(text)
    artist = ax.text(
        0.02,
        0.95,
        "\n".join(wrapped),
        ha="left",
        va="top",
        fontsize=ANNOTATION_FONT_SIZE,
        color=color,
        transform=ax.transAxes,
        family="monospace",
    )
    artist.set_clip_on(True)


def _table_panel(
    ax: Any, title: str, col_labels: Sequence[str], rows: Sequence[Sequence[str]]
) -> None:
    ax.axis("off")
    ax.set_title(title, fontsize=11.0)
    if not rows:
        ax.text(0.02, 0.9, "(no rows)", transform=ax.transAxes, fontsize=ANNOTATION_FONT_SIZE)
        return
    table = ax.table(
        cellText=[[str(cell) for cell in row] for row in rows],
        colLabels=[str(c) for c in col_labels],
        loc="upper center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(ANNOTATION_FONT_SIZE)
    table.scale(1.0, 1.25)


def _add_metre_scale_bar(ax: Any) -> float:
    """Draw a metre scale bar and return its length. Mandatory on every spatial map."""

    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    span = float(x_max - x_min)
    if span <= 0:
        return 0.0
    target = span / 4.0
    decade = 10.0 ** math.floor(math.log10(target)) if target > 0 else 1.0
    length = decade
    for factor in (1.0, 2.0, 5.0, 10.0):
        if decade * factor <= target:
            length = decade * factor
    bar_x = x_min + 0.06 * span
    bar_y = y_min + 0.06 * float(y_max - y_min)
    ax.plot(
        [bar_x, bar_x + length],
        [bar_y, bar_y],
        color="black",
        linewidth=3.0,
        solid_capstyle="butt",
        zorder=6,
    )
    ax.text(
        bar_x + length / 2.0,
        bar_y + 0.02 * float(y_max - y_min),
        f"{length:g} m",
        ha="center",
        va="bottom",
        fontsize=ANNOTATION_FONT_SIZE,
        zorder=6,
    )
    return float(length)


def _short_label(text: Any, limit: int = 28) -> str:
    """Shorten a categorical tick label, keeping both ends.

    A recorded world identity can be a 150-character hash-and-scenario string. Used as a
    tick label it does not merely look bad: the axes tight bounding box grows until the
    constrained layout collapses the neighbouring panel to zero width. The full identity
    stays in the exported table, so nothing is lost by shortening the tick.
    """

    value = str(text)
    if len(value) <= limit:
        return value
    head = (limit - 3) // 2
    tail = limit - 3 - head
    return f"{value[:head]}...{value[-tail:]}"


def _entity_key(entity: Any) -> str:
    if isinstance(entity, EntityId):
        return entity.key
    if isinstance(entity, Mapping):
        return str(entity.get("key") or entity.get("entity") or entity)
    return str(entity)


def _finalize(
    fig: Any,
    spec: FigureSpec,
    table: list[dict[str, Any]],
    output_dir: Path | str,
    options: Mapping[str, Any] | None,
) -> FigureResult:
    """Export the bundle, retaining the live figure only when asked to."""

    opts = options or {}
    keep = bool(opts.get("keep_figure"))
    formats = tuple(opts.get("formats", ("png", "svg", "pdf")))
    result = FigureResult(spec=spec, table=table)
    return export_figure(fig, result, output_dir, formats=formats, close=not keep)


def _missing(
    figure_id: str,
    title: str,
    missing_record: str,
    *,
    question: str,
    output_dir: Path | str,
    options: Mapping[str, Any] | None,
    inputs: Mapping[str, Any] | None = None,
    detail: str = "",
) -> FigureResult:
    opts = options or {}
    return missing_panel(
        figure_id,
        title,
        missing_record,
        question=question,
        detail=detail,
        output_dir=output_dir,
        synthetic_banner=synthetic_banner_for(inputs, opts),
        keep_figure=bool(opts.get("keep_figure")),
    )


# --------------------------------------------------------------------------------------
# C01 - Does learning improve the declared objective?
# --------------------------------------------------------------------------------------

C01_QUESTION = "Does learning improve the declared objective?"


def c01_learning_curves(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Evaluation learning curves with faint per-replicate lines and a declared aggregate.

    Restrictions enforced here: the shaded interval is computed over *fit* units by the
    statistics module and is drawn only for two or more fits, so an episode-level band can
    never masquerade as fit variability; training reward is drawn on a separate panel with
    its own x axis because it lives on a different x kind; nothing is interpolated, and a
    short run is never extended to the longest run's budget.
    """

    opts = dict(options or {})
    title = "C01 Evaluation learning curves"
    missing_key = _first_missing(inputs, ("evaluation_curve",))
    if missing_key is not None:
        return _missing(
            "C01",
            title,
            "evaluation_curve (evaluation MetricRecord rows)",
            question=C01_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    curve_rows = _as_sequence(inputs["evaluation_curve"])
    metric_name = str(
        opts.get("metric_name")
        or (_distinct(getattr(r, "metric_name", None) for r in curve_rows) or ["unknown"])[0]
    )
    curve_rows = _metric_rows(curve_rows, metric_name=metric_name)
    if not curve_rows:
        return _missing(
            "C01",
            title,
            f"evaluation_curve rows for metric '{metric_name}'",
            question=C01_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    training_rows = _metric_rows(
        _as_sequence(inputs.get("training_reward")), phase=Phase.TRAINING
    ) or _as_sequence(inputs.get("training_reward"))
    stats = _load_statistics(opts)
    unit = _record_unit(curve_rows)
    definition, catalog_unit = _metric_definition(
        metric_name,
        opts,
        f"{metric_name} as recorded in the supplied evaluation rows; no transformation applied",
    )
    unit = catalog_unit or unit
    smoothing_window = int(opts.get("smoothing_window", 0) or 0)

    fig, axes = new_figure(figsize=(9.5, 8.0), nrows=3, height_ratios=(3.0, 1.0, 2.0))
    ax_curve, ax_count, ax_train = axes.tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    replicates = sorted(
        {str(getattr(r, "training_replicate_id", None) or "unlabelled") for r in curve_rows}
    )
    styles = apply_method_style(None, replicates, high_contrast=bool(opts.get("high_contrast")))

    # Faint per-replicate lines: the individual fits stay visible, never only a summary.
    for replicate in replicates:
        rows = [
            r
            for r in curve_rows
            if str(getattr(r, "training_replicate_id", None) or "unlabelled") == replicate
        ]
        points = sorted(
            (
                (float(getattr(r, "x_value", 0.0) or 0.0), measured_value(getattr(r, "value", None)), r)
                for r in rows
                if getattr(r, "x_value", None) is not None
            ),
            key=lambda item: item[0],
        )
        xs = [p[0] for p in points if p[1] is not None]
        ys = [p[1] for p in points if p[1] is not None]
        style = styles[replicate]
        if xs:
            ax_curve.plot(
                xs,
                ys,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=1.0,
                alpha=0.38,
                marker=style["marker"],
                markersize=3.5,
                label=f"fit {replicate} (raw)",
            )
        for x_value, y_value, row in points:
            table.append(
                {
                    "role": "replicate_curve_point",
                    "training_replicate_id": replicate,
                    "x_kind": getattr(getattr(row, "x_kind", None), "value", ""),
                    "x_value": x_value,
                    "metric_name": metric_name,
                    "value": y_value,
                    "unit": unit,
                    "status": measured_status(getattr(row, "value", None)),
                    "episode_id": getattr(row, "episode_id", None),
                    "source_path": getattr(row, "source_path", None),
                }
            )
        if smoothing_window > 1 and xs:
            smoothed = trailing_mean(ys, smoothing_window)
            ax_curve.plot(
                xs,
                smoothed,
                color=style["color"],
                linestyle="-",
                linewidth=1.2,
                alpha=0.55,
                label=f"fit {replicate} (trailing mean, window {smoothing_window})",
            )
            for x_value, y_value in zip(xs, smoothed):
                table.append(
                    {
                        "role": "replicate_curve_smoothed",
                        "training_replicate_id": replicate,
                        "x_value": x_value,
                        "value": y_value,
                        "unit": unit,
                        "status": "derived_presentation_only",
                    }
                )

    # Declared aggregate over fit units, one reduction per recorded x value.
    x_values = sorted(
        {
            float(getattr(r, "x_value", 0.0) or 0.0)
            for r in curve_rows
            if getattr(r, "x_value", None) is not None
        }
    )
    aggregate_x: list[float] = []
    aggregate_y: list[float] = []
    band_low: list[float] = []
    band_high: list[float] = []
    band_x: list[float] = []
    n_units_per_x: list[int] = []
    uncertainty = "unavailable (no aggregate drawn)"
    for x_value in x_values:
        rows_at_x = [r for r in curve_rows if float(getattr(r, "x_value", 0.0) or 0.0) == x_value]
        units_at_x = len(
            {str(getattr(r, "training_replicate_id", None) or "unlabelled") for r in rows_at_x}
        )
        n_units_per_x.append(units_at_x)
        aggregation, reduction, notes = _reduce_units(
            stats,
            rows_at_x,
            metric_name=metric_name,
            ci_method=str(opts.get("ci_method", "student_t")),
            rng_seed=opts.get("rng_seed"),
        )
        for note in notes:
            if note not in warnings:
                warnings.append(note)
        point = measured_value(getattr(reduction, "point", None)) if reduction else None
        if point is not None:
            aggregate_x.append(x_value)
            aggregate_y.append(point)
            table.append(
                {
                    "role": "aggregate_point",
                    "x_value": x_value,
                    "metric_name": metric_name,
                    "value": point,
                    "unit": unit,
                    "n_units": int(getattr(reduction, "n_units", units_at_x) or units_at_x),
                    "status": "aggregate_over_fits",
                }
            )
        if _interval_is_drawable(reduction, units_at_x):
            low = measured_value(getattr(reduction, "ci_low", None))
            high = measured_value(getattr(reduction, "ci_high", None))
            band_x.append(x_value)
            band_low.append(float(low))
            band_high.append(float(high))
            uncertainty = _uncertainty_label(reduction, units_at_x, unit_kind="fit")
            table.append(
                {
                    "role": "aggregate_interval",
                    "x_value": x_value,
                    "ci_low": low,
                    "ci_high": high,
                    "ci_method": str(getattr(reduction, "ci_method", "")),
                    "n_units": units_at_x,
                    "unit": unit,
                    "status": "pointwise_interval",
                }
            )
        elif reduction is not None:
            uncertainty = _uncertainty_label(reduction, units_at_x, unit_kind="fit")

    if aggregate_x:
        ax_curve.plot(
            aggregate_x,
            aggregate_y,
            color="#000000",
            linestyle="-",
            linewidth=2.2,
            marker="o",
            markersize=5.0,
            label=f"declared aggregate over fits (n={max(n_units_per_x or [0])})",
            zorder=5,
        )
    if band_x:
        ax_curve.fill_between(
            band_x,
            band_low,
            band_high,
            color="#000000",
            alpha=0.14,
            linewidth=0.0,
            label="pointwise interval over fit values (not simultaneous coverage)",
        )
    if len(replicates) < 2:
        warnings.append(
            "only one fit is present; no cross-fit interval is drawn and episode "
            "variability must not be read as fit variability"
        )

    x_kinds = _distinct(getattr(getattr(r, "x_kind", None), "value", "") for r in curve_rows)
    x_label = _axis_label("evaluation x axis: " + "/".join(str(k) for k in x_kinds), None)
    if len(x_kinds) > 1:
        warnings.append(
            "evaluation rows mix x kinds " + ", ".join(str(k) for k in x_kinds) + "; they are "
            "plotted on their recorded values without conversion"
        )
    finish_axes(
        ax_curve,
        title=f"Evaluation: {metric_name} ({unit})",
        y_label=_axis_label(metric_name, unit),
        legend=None,
    )

    # Sample counts change along x; the plan requires that to be visible.
    if x_values:
        ax_count.step(x_values, n_units_per_x, where="mid", color="#0072B2", linewidth=1.4)
        ax_count.set_ylim(0, max(n_units_per_x) + 1)
        for x_value, count in zip(x_values, n_units_per_x):
            table.append(
                {
                    "role": "contributing_fit_count",
                    "x_value": x_value,
                    "n_fits": int(count),
                    "status": "count",
                }
            )
    finish_axes(
        ax_count,
        title="Contributing fits per x position (count)",
        x_label=x_label,
        y_label="fits (count)",
    )

    # Training reward is a different quantity on a different x axis: separate panel.
    if training_rows:
        train_metric = str(
            opts.get("training_metric_name")
            or (_distinct(getattr(r, "metric_name", None) for r in training_rows) or ["unknown"])[0]
        )
        train_unit = _record_unit(training_rows)
        train_replicates = sorted(
            {str(getattr(r, "training_replicate_id", None) or "unlabelled") for r in training_rows}
        )
        train_styles = apply_method_style(None, train_replicates)
        for replicate in train_replicates:
            rows = [
                r
                for r in training_rows
                if str(getattr(r, "training_replicate_id", None) or "unlabelled") == replicate
            ]
            points = sorted(
                (
                    (float(getattr(r, "x_value", 0.0) or 0.0), measured_value(getattr(r, "value", None)))
                    for r in rows
                    if getattr(r, "x_value", None) is not None
                ),
                key=lambda item: item[0],
            )
            xs = [p[0] for p in points if p[1] is not None]
            ys = [p[1] for p in points if p[1] is not None]
            style = train_styles[replicate]
            if xs:
                ax_train.plot(
                    xs,
                    ys,
                    color=style["color"],
                    linestyle=style["linestyle"],
                    linewidth=1.2,
                    alpha=0.8,
                    label=f"fit {replicate}",
                )
            for x_value, y_value in points:
                table.append(
                    {
                        "role": "training_reward_point",
                        "training_replicate_id": replicate,
                        "x_value": x_value,
                        "metric_name": train_metric,
                        "value": y_value,
                        "unit": train_unit,
                        "status": "training_phase",
                    }
                )
        train_x_kinds = _distinct(
            getattr(getattr(r, "x_kind", None), "value", "") for r in training_rows
        )
        finish_axes(
            ax_train,
            title=f"Training reward, separate axis: {train_metric} ({train_unit})",
            x_label="training x axis: " + "/".join(str(k) for k in train_x_kinds),
            y_label=_axis_label(train_metric, train_unit),
        )
    else:
        _text_panel(
            ax_train,
            "Training reward (separate panel)",
            [
                "NOT RECORDED: training_reward",
                "The training-phase reward was not supplied, so no training curve is",
                "drawn. The evaluation panel above is not a substitute for it.",
            ],
            color="#7A0000",
        )
        warnings.append("NOT RECORDED: training_reward (optional panel left empty)")

    n_missing, n_failed = _validity_counts(curve_rows)
    episodes = {
        getattr(r, "episode_id", None) for r in curve_rows if getattr(r, "episode_id", None)
    }
    spec = FigureSpec(
        figure_id="C01",
        title="Evaluation learning curves with per-fit detail",
        question=C01_QUESTION,
        x_label=x_label,
        y_label=_axis_label(metric_name, unit),
        metric_definition=definition,
        data_provenance=_provenance_for(curve_rows, kind="evaluation_metric_rows")
        + _provenance_for(training_rows, kind="training_metric_rows"),
        selection_rule=(
            "all supplied evaluation rows for the selected metric; no best-checkpoint or "
            "best-seed selection, no row dropped"
        ),
        checkpoint_rule=str(
            opts.get("checkpoint_rule", "as recorded in the rows (checkpoint_id preserved)")
        ),
        statistical_unit="independent training replicate (fit)",
        n_fits=len(replicates),
        n_evaluation_episodes=len(episodes) or None,
        n_missing=n_missing,
        n_failed=n_failed,
        smoothing=(
            None
            if smoothing_window <= 1
            else {
                "method": "trailing_mean",
                "window": smoothing_window,
                "future_aware": False,
                "affects": "presentation only; raw curves remain drawn",
            }
        ),
        alignment_rule=(
            "rows are drawn at their recorded x values; no interpolation, no repeated last "
            "value for a missing tail checkpoint, no extension of a short run"
        ),
        uncertainty_method=uncertainty,
        random_seed=opts.get("rng_seed"),
        caption=(
            "Shows the recorded evaluation metric per fit and the declared aggregate across "
            "fits. Any interval is pointwise over fit values and is not a simultaneous "
            "coverage statement; episode-to-episode variability within one fit is a "
            "different quantity and is not drawn as a fit band. Training reward appears in "
            "its own panel because it is measured on a different x axis. Does not "
            "demonstrate that an improvement generalises beyond the evaluated worlds, and "
            "does not establish a cause for the shape of any curve."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C02 - Is the improvement consistent across fits?
# --------------------------------------------------------------------------------------

C02_QUESTION = "Is the improvement consistent across fits?"


def c02_per_fit_consistency(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Per-fit endpoint dots, a paired-difference panel only when pairing is verified.

    Restrictions enforced here: no bar-only summary (the fits are always drawn as
    individual dots); every fit appears in the raw table including technical failures; no
    best-seed selection (the selection rule is "all supplied fits"); and a single fit never
    receives an interval, zero width or otherwise.
    """

    opts = dict(options or {})
    title = "C02 Per-fit endpoint consistency"
    missing_key = _first_missing(inputs, ("fit_endpoints",))
    if missing_key is not None:
        return _missing(
            "C02",
            title,
            "fit_endpoints (per-fit endpoint MetricRecord rows)",
            question=C02_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    primary_rows = _as_sequence(inputs["fit_endpoints"])
    baseline_rows = _as_sequence(inputs.get("baseline_fit_endpoints"))
    metric_name = str(
        opts.get("metric_name")
        or (_distinct(getattr(r, "metric_name", None) for r in primary_rows) or ["unknown"])[0]
    )
    primary_rows = _metric_rows(primary_rows, metric_name=metric_name)
    baseline_rows = _metric_rows(baseline_rows, metric_name=metric_name)
    if not primary_rows:
        return _missing(
            "C02",
            title,
            f"fit_endpoints rows for metric '{metric_name}'",
            question=C02_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    stats = _load_statistics(opts)
    unit = _record_unit(primary_rows)
    definition, catalog_unit = _metric_definition(
        metric_name,
        opts,
        f"{metric_name} at the recorded fit endpoint, exactly as supplied",
    )
    unit = catalog_unit or unit
    fit_status: Mapping[str, str] = dict(inputs.get("fit_status") or {})

    groups: list[tuple[str, list[Any]]] = [
        (str(opts.get("method_label", "method under test")), primary_rows)
    ]
    if baseline_rows:
        groups.append((str(opts.get("baseline_label", "baseline")), baseline_rows))

    draw_paired = bool(baseline_rows)
    fig, axes = new_figure(
        figsize=(11.0, 6.0) if draw_paired else (9.0, 5.6),
        ncols=2 if draw_paired else 1,
        width_ratios=(3.0, 2.0) if draw_paired else None,
    )
    ax_dots, ax_paired = (axes.tolist() if draw_paired else (axes, None))

    table: list[dict[str, Any]] = []
    warnings: list[str] = []
    styles = apply_method_style(
        None, [name for name, _ in groups], high_contrast=bool(opts.get("high_contrast"))
    )
    interval_drawn = False
    uncertainty = "unavailable (no interval drawn)"
    aggregations: dict[str, Any] = {}
    n_fits_primary = 0

    # Axis order covers every fit that exists in any supplied group *and* every fit named
    # in fit_status, so a technical failure with no endpoint row still gets a position, a
    # tick label and a table row instead of vanishing from the comparison.
    axis_order = sorted(
        {str(getattr(r, "training_replicate_id", None) or "unlabelled") for _, rows in groups for r in rows}
        | {str(fit_id) for fit_id in fit_status}
    )
    for group_index, (label, rows) in enumerate(groups):
        group_fits = {str(getattr(r, "training_replicate_id", None) or "unlabelled") for r in rows}
        fit_ids = [
            fit_id
            for fit_id in axis_order
            if fit_id in group_fits or (group_index == 0 and fit_id in fit_status)
        ]
        style = styles[label]
        x_positions: list[float] = []
        y_values: list[float] = []
        for fit_id in fit_ids:
            fit_index = axis_order.index(fit_id)
            fit_rows = [
                r
                for r in rows
                if str(getattr(r, "training_replicate_id", None) or "unlabelled") == fit_id
            ]
            status = str(fit_status.get(fit_id, "")) or None
            values = [measured_value(getattr(r, "value", None)) for r in fit_rows]
            usable = [v for v in values if v is not None]
            row_status = measured_status(getattr(fit_rows[0], "value", None)) if fit_rows else "absent"
            is_failure = bool(status and status not in ("completed", "ok", "finished"))
            if usable and not is_failure:
                # Several rows per fit means this is not yet a fit-level endpoint: the
                # statistics module owns that aggregation, so raw rows are drawn instead.
                if len(usable) > 1:
                    warnings.append(
                        f"fit {fit_id} supplied {len(usable)} rows; each recorded row is drawn "
                        "separately because fit-level aggregation belongs to the statistics "
                        "module, not to this chart"
                    )
                for value in usable:
                    x_positions.append(fit_index + (group_index - (len(groups) - 1) / 2) * 0.18)
                    y_values.append(value)
            for record_index, (row, value) in enumerate(zip(fit_rows, values)):
                table.append(
                    {
                        "role": "fit_endpoint",
                        "group": label,
                        "training_replicate_id": fit_id,
                        "row_index": record_index,
                        "metric_name": metric_name,
                        "value": None if is_failure else value,
                        "unit": unit,
                        "validity": measured_status(getattr(row, "value", None)),
                        "fit_status": status or "not recorded",
                        "excluded_from_plot": bool(is_failure or value is None),
                        "checkpoint_id": getattr(row, "checkpoint_id", None),
                        "n_episodes_behind_row": getattr(row, "episode_id", None),
                        "source_path": getattr(row, "source_path", None),
                    }
                )
            if not fit_rows:
                table.append(
                    {
                        "role": "fit_endpoint",
                        "group": label,
                        "training_replicate_id": fit_id,
                        "value": None,
                        "unit": unit,
                        "validity": row_status,
                        "fit_status": status or "not recorded",
                        "excluded_from_plot": True,
                    }
                )
        if x_positions:
            ax_dots.plot(
                x_positions,
                y_values,
                linestyle="none",
                marker=style["marker"],
                markersize=8.0,
                markerfacecolor=style["color"],
                markeredgecolor="black",
                markeredgewidth=0.8,
                label=f"{label}: per-fit endpoint",
            )
        n_units = len(
            {
                str(getattr(r, "training_replicate_id", None) or "unlabelled")
                for r in rows
                if measured_value(getattr(r, "value", None)) is not None
                and not (
                    str(fit_status.get(str(getattr(r, "training_replicate_id", None)), ""))
                    not in ("", "completed", "ok", "finished")
                )
            }
        )
        if group_index == 0:
            n_fits_primary = n_units
        aggregation, reduction, notes = _reduce_units(
            stats,
            rows,
            metric_name=metric_name,
            ci_method=str(opts.get("ci_method", "student_t")),
            rng_seed=opts.get("rng_seed"),
        )
        aggregations[label] = aggregation
        for note in notes:
            if note not in warnings:
                warnings.append(note)
        centre = (group_index - (len(groups) - 1) / 2) * 0.18 + len(axis_order) + 0.7
        point = measured_value(getattr(reduction, "point", None)) if reduction else None
        if point is not None:
            ax_dots.plot(
                [centre],
                [point],
                linestyle="none",
                marker="_",
                markersize=22.0,
                markeredgewidth=2.4,
                color=style["color"],
                label=f"{label}: aggregate over fits",
            )
            table.append(
                {
                    "role": "aggregate_point",
                    "group": label,
                    "x_position": centre,
                    "value": point,
                    "unit": unit,
                    "n_units": int(getattr(reduction, "n_units", n_units) or n_units),
                    "validity": "aggregate_over_fits",
                }
            )
        if _interval_is_drawable(reduction, n_units):
            low = float(measured_value(getattr(reduction, "ci_low", None)))
            high = float(measured_value(getattr(reduction, "ci_high", None)))
            ax_dots.plot(
                [centre, centre],
                [low, high],
                color=style["color"],
                linewidth=2.0,
                solid_capstyle="butt",
                label=f"{label}: {getattr(reduction, 'ci_method', 'interval')} interval",
            )
            interval_drawn = True
            uncertainty = _uncertainty_label(reduction, n_units, unit_kind="fit")
            table.append(
                {
                    "role": "aggregate_interval",
                    "group": label,
                    "x_position": centre,
                    "ci_low": low,
                    "ci_high": high,
                    "ci_method": str(getattr(reduction, "ci_method", "")),
                    "n_units": n_units,
                    "unit": unit,
                }
            )
        else:
            uncertainty = _uncertainty_label(reduction, n_units, unit_kind="fit")

    failures = sorted(
        fit_id
        for fit_id, status in fit_status.items()
        if str(status) not in ("completed", "ok", "finished")
    )
    invalid_rows = [
        str(getattr(r, "training_replicate_id", None) or "unlabelled")
        for r in primary_rows
        if measured_value(getattr(r, "value", None)) is None
    ]
    note_lines = []
    if failures:
        note_lines.append(
            "technical failures (no value drawn): "
            + ", ".join(f"{fit_id}={fit_status[fit_id]}" for fit_id in failures)
        )
    if invalid_rows:
        note_lines.append("rows without a usable value: " + ", ".join(sorted(set(invalid_rows))))
    if note_lines:
        ax_dots.text(
            0.01,
            -0.16,
            "\n".join(note_lines),
            transform=ax_dots.transAxes,
            fontsize=ANNOTATION_FONT_SIZE,
            va="top",
            color="#7A0000",
        )
    ax_dots.set_xticks(range(len(axis_order)))
    ax_dots.set_xticklabels(
        [_short_label(fit_id) for fit_id in axis_order],
        rotation=30,
        ha="right",
        fontsize=ANNOTATION_FONT_SIZE,
    )
    finish_axes(
        ax_dots,
        title=f"Per-fit endpoint: {metric_name} ({unit})",
        x_label="training replicate (fit identity, categorical)",
        y_label=_axis_label(metric_name, unit),
        legend=True,
    )

    # Paired difference: drawn only when the statistics module verifies the pairing.
    pairing_status = "not attempted"
    if draw_paired:
        pairing_evidence = inputs.get("pairing_evidence")
        paired = None
        if pairing_evidence is None:
            lines = [
                "Paired-difference panel omitted.",
                "No pairing_evidence was supplied. Matching seed numbers or",
                "episode numbers is not evidence of a paired design, so an",
                "unpaired comparison would be the only honest summary here.",
            ]
            pairing_status = "omitted: no pairing evidence supplied"
        elif stats is None:
            lines = [
                "Paired-difference panel omitted.",
                "Pairing must be verified by the statistics module, which is not",
                "importable in this process. No pairing is assumed.",
            ]
            pairing_status = "omitted: verifier unavailable"
        else:
            try:
                paired = stats.paired_difference(
                    aggregations.get(groups[0][0]),
                    aggregations.get(groups[1][0]),
                    pairing_evidence=pairing_evidence,
                    ci_method=str(opts.get("ci_method", "student_t")),
                    ci_level=float(opts.get("ci_level", 0.95)),
                    rng_seed=opts.get("rng_seed"),
                )
            except Exception as error:
                paired = None
                pairing_status = f"omitted: paired_difference failed ({type(error).__name__})"
                warnings.append(f"paired_difference failed: {type(error).__name__}: {error}")
            lines = []
        if paired is not None:
            status_text = str(getattr(paired, "pairing_status", "unknown"))
            n_pairs = int(getattr(paired, "n_pairs", 0) or 0)
            verified = status_text.lower().startswith(("paired", "verified")) and n_pairs >= 1
            pairing_status = status_text
            if verified:
                pair_values = _paired_unit_differences(
                    aggregations.get(groups[0][0]), aggregations.get(groups[1][0])
                )
                for index, (unit_id, difference) in enumerate(pair_values):
                    ax_paired.plot(
                        [index],
                        [difference],
                        linestyle="none",
                        marker="o",
                        markersize=8.0,
                        markerfacecolor="#0072B2",
                        markeredgecolor="black",
                        label="per-pair difference" if index == 0 else None,
                    )
                    table.append(
                        {
                            "role": "pair_difference",
                            "pair_unit_id": unit_id,
                            "value": difference,
                            "unit": unit,
                            "pairing_status": status_text,
                        }
                    )
                point = measured_value(getattr(paired, "point", None))
                centre = len(pair_values) + 0.6
                if point is not None:
                    ax_paired.plot(
                        [centre],
                        [point],
                        linestyle="none",
                        marker="_",
                        markersize=22.0,
                        markeredgewidth=2.4,
                        color="#000000",
                        label="paired mean difference",
                    )
                    table.append(
                        {
                            "role": "paired_point",
                            "value": point,
                            "unit": unit,
                            "n_pairs": n_pairs,
                            "pairing_status": status_text,
                        }
                    )
                if _interval_is_drawable(paired, n_pairs):
                    low = float(measured_value(getattr(paired, "ci_low", None)))
                    high = float(measured_value(getattr(paired, "ci_high", None)))
                    ax_paired.plot(
                        [centre, centre],
                        [low, high],
                        color="#000000",
                        linewidth=2.0,
                        label=f"{getattr(paired, 'ci_method', 'interval')} paired interval",
                    )
                    interval_drawn = True
                    table.append(
                        {
                            "role": "paired_interval",
                            "ci_low": low,
                            "ci_high": high,
                            "ci_method": str(getattr(paired, "ci_method", "")),
                            "n_pairs": n_pairs,
                            "unit": unit,
                        }
                    )
                ax_paired.axhline(0.0, color="#555555", linestyle=(0, (4, 3)), linewidth=1.0)
                table.append({"role": "reference_line", "value": 0.0, "unit": unit, "label": "no difference"})
                unmatched_a = list(getattr(paired, "unmatched_a", ()) or ())
                unmatched_b = list(getattr(paired, "unmatched_b", ()) or ())
                incomplete = int(getattr(paired, "incomplete_pairs", 0) or 0)
                if unmatched_a or unmatched_b or incomplete:
                    ax_paired.text(
                        0.02,
                        0.02,
                        "unmatched A: "
                        + (", ".join(map(str, unmatched_a)) or "none")
                        + "\nunmatched B: "
                        + (", ".join(map(str, unmatched_b)) or "none")
                        + f"\nincomplete pairs: {incomplete}",
                        transform=ax_paired.transAxes,
                        fontsize=ANNOTATION_FONT_SIZE,
                        color="#7A0000",
                    )
                for unit_id in unmatched_a:
                    table.append({"role": "unmatched_unit", "group": groups[0][0], "pair_unit_id": unit_id})
                for unit_id in unmatched_b:
                    table.append({"role": "unmatched_unit", "group": groups[1][0], "pair_unit_id": unit_id})
                finish_axes(
                    ax_paired,
                    title=f"Paired difference ({groups[0][0]} minus {groups[1][0]}) ({unit})",
                    x_label="verified pair (categorical)",
                    y_label=_axis_label("difference", unit),
                    legend=True,
                )
            else:
                lines = [
                    "Paired-difference panel omitted.",
                    f"pairing_status reported by the verifier: {status_text}",
                    "An unpaired summary is the documented alternative; pairs are",
                    "not invented here.",
                ]
                fallback = getattr(paired, "fallback_unpaired", None)
                if fallback is not None:
                    lines.append("fallback unpaired summary is available in the statistics output.")
        if paired is None or not str(pairing_status).lower().startswith(("paired", "verified")):
            _text_panel(ax_paired, "Paired difference (not drawn)", lines, color="#7A0000")
            warnings.append(f"paired-difference panel not drawn: {pairing_status}")
    elif ax_paired is not None:  # pragma: no cover - defensive
        _text_panel(ax_paired, "Paired difference (not drawn)", ["no baseline group supplied"])

    if n_fits_primary <= 1:
        warnings.append(
            "single fit: no cross-fit interval is defined, so none is drawn; the dot is a "
            "point estimate, not an interval of width zero"
        )
    n_missing, n_failed = _validity_counts(primary_rows + baseline_rows)
    spec = FigureSpec(
        figure_id="C02",
        title="Per-fit endpoint consistency",
        question=C02_QUESTION,
        x_label="training replicate (fit identity, categorical)",
        y_label=_axis_label(metric_name, unit),
        metric_definition=definition,
        data_provenance=_provenance_for(primary_rows, kind="fit_endpoint_rows")
        + _provenance_for(baseline_rows, kind="baseline_fit_endpoint_rows"),
        selection_rule=(
            "every supplied fit is listed in the raw table, including technical failures; "
            "no best-seed selection and no exclusion of an inconvenient fit"
        ),
        checkpoint_rule=str(
            opts.get("checkpoint_rule", "fixed recorded endpoint per fit (checkpoint_id preserved)")
        ),
        statistical_unit="independent training replicate (fit)",
        n_fits=n_fits_primary,
        n_evaluation_episodes=(
            len({getattr(r, "episode_id", None) for r in primary_rows if getattr(r, "episode_id", None)})
            or None
        ),
        n_missing=n_missing,
        n_failed=n_failed + len(failures),
        uncertainty_method=uncertainty,
        random_seed=opts.get("rng_seed"),
        caption=(
            "Each dot is one fit's recorded endpoint; no bar summary replaces the fits. "
            f"Interval drawn: {'yes' if interval_drawn else 'no'}. Technical failures and "
            "rows without a usable value are listed in the table rather than dropped. "
            "Does not demonstrate which method is better overall, does not establish a "
            "cause for any gap, and a paired difference appears only when the pairing was "
            f"verified (status: {pairing_status})."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


def _paired_unit_differences(
    aggregation_a: Any, aggregation_b: Any
) -> list[tuple[str, float]]:
    """Differences of matched unit values, computed only after pairing was verified.

    This is elementary subtraction of two points that the verifier has already declared
    matched; it is not an independent pairing rule.
    """

    def _values(aggregation: Any) -> dict[str, float]:
        out: dict[str, float] = {}
        for unit in getattr(aggregation, "units", ()) or ():
            value = measured_value(getattr(unit, "value", None))
            if value is not None:
                out[str(getattr(unit, "unit_id", ""))] = value
        return out

    values_a = _values(aggregation_a)
    values_b = _values(aggregation_b)
    return [
        (unit_id, values_a[unit_id] - values_b[unit_id])
        for unit_id in sorted(set(values_a) & set(values_b))
    ]


# --------------------------------------------------------------------------------------
# C03 - Does service improve after an outage?
# --------------------------------------------------------------------------------------

C03_QUESTION = "Does service improve after an outage?"

#: Event types recognised for marker styling. Anything else is drawn as a generic event.
_EVENT_STYLES: dict[str, dict[str, Any]] = {
    "alarm": {"color": "#E69F00", "linestyle": (0, (2, 2))},
    "failure": {"color": "#7A0000", "linestyle": "-"},
    "repair": {"color": "#0072B2", "linestyle": (0, (6, 2))},
}


def c03_event_aligned_service(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Offered, delivered and unmet service aligned to the recorded event times.

    Restrictions enforced here: event markers use the times carried by the event records
    themselves, never a nominal schedule; the healthy and failed-ground reference lines are
    drawn only when they were recorded; and the caption states that an exogenous repair is
    not UAV-caused recovery.
    """

    opts = dict(options or {})
    title = "C03 Event-aligned service"
    missing_key = _first_missing(inputs, ("service_timeseries",))
    if missing_key is not None:
        return _missing(
            "C03",
            title,
            "service_timeseries (offered/delivered/unmet MetricRecord rows on simulated time)",
            question=C03_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    rows = _as_sequence(inputs["service_timeseries"])
    events = _as_sequence(inputs.get("world_events"))
    metric_names = [
        name
        for name in _distinct(getattr(r, "metric_name", None) for r in rows)
        if name is not None
    ]
    if not metric_names:
        return _missing(
            "C03",
            title,
            "service_timeseries rows carrying a metric_name",
            question=C03_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    unit = _record_unit(rows)
    fig, ax = new_figure(figsize=(10.0, 5.8))
    table: list[dict[str, Any]] = []
    warnings: list[str] = []
    styles = apply_method_style(None, metric_names, high_contrast=bool(opts.get("high_contrast")))

    for name in metric_names:
        series = sorted(
            (
                (float(getattr(r, "x_value", 0.0) or 0.0), measured_value(getattr(r, "value", None)), r)
                for r in _metric_rows(rows, metric_name=name)
                if getattr(r, "x_value", None) is not None
            ),
            key=lambda item: item[0],
        )
        xs = [p[0] for p in series if p[1] is not None]
        ys = [p[1] for p in series if p[1] is not None]
        style = styles[name]
        if xs:
            ax.plot(
                xs,
                ys,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=1.8,
                marker=style["marker"],
                markersize=4.0,
                label=f"{name} ({unit})",
            )
        gaps = [p[0] for p in series if p[1] is None]
        if gaps:
            warnings.append(
                f"{name}: {len(gaps)} sample(s) carry a non-OK validity and are left as gaps, "
                "not interpolated and not set to zero"
            )
        for x_value, y_value, row in series:
            table.append(
                {
                    "role": "service_point",
                    "metric_name": name,
                    "time_s": x_value,
                    "value": y_value,
                    "unit": unit,
                    "status": measured_status(getattr(row, "value", None)),
                    "x_kind": getattr(getattr(row, "x_kind", None), "value", ""),
                    "interval_start_s": getattr(row, "interval_start_s", None),
                    "interval_end_s": getattr(row, "interval_end_s", None),
                    "source_path": getattr(row, "source_path", None),
                }
            )

    seen_event_labels: set[str] = set()
    for event in events:
        time_s = getattr(event, "time_s", None)
        if time_s is None and isinstance(event, Mapping):
            time_s = event.get("time_s")
        if time_s is None:
            warnings.append("an event record carries no time and is not drawn")
            continue
        event_type = str(
            getattr(event, "event_type", None)
            or (event.get("event_type") if isinstance(event, Mapping) else "")
            or "event"
        )
        availability = str(getattr(event, "availability", "recorded") or "recorded")
        key = next((k for k in _EVENT_STYLES if k in event_type.lower()), None)
        style = _EVENT_STYLES.get(key or "", {"color": "#444444", "linestyle": (0, (1, 2))})
        label = f"{event_type} (recorded time)"
        ax.axvline(
            float(time_s),
            color=style["color"],
            linestyle=style["linestyle"],
            linewidth=1.6,
            alpha=0.9,
            label=None if label in seen_event_labels else label,
        )
        seen_event_labels.add(label)
        ax.annotate(
            event_type,
            xy=(float(time_s), 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(2, -10),
            textcoords="offset points",
            fontsize=ANNOTATION_FONT_SIZE,
            rotation=90,
            va="top",
            color=style["color"],
        )
        table.append(
            {
                "role": "event_marker",
                "time_s": float(time_s),
                "event_type": event_type,
                "description": str(getattr(event, "description", "") or ""),
                "entity": getattr(event, "entity", None),
                "availability": availability,
            }
        )
    if not events:
        warnings.append(
            "NOT RECORDED: world_events - the curves are drawn on raw simulated time with no "
            "alarm/failure/repair markers"
        )

    for reference_key, label in (
        ("healthy_reference", "healthy reference (recorded)"),
        ("failed_ground_reference", "failed-ground reference (recorded)"),
    ):
        reference = inputs.get(reference_key)
        value = measured_value(reference)
        if value is None:
            warnings.append(f"NOT RECORDED: {reference_key} - no reference line drawn")
            continue
        ax.axhline(
            value,
            color="#000000" if "healthy" in reference_key else "#8C8C8C",
            linestyle=(0, (5, 2)) if "healthy" in reference_key else (0, (1, 1.6)),
            linewidth=1.4,
            label=label,
        )
        table.append(
            {
                "role": "reference_line",
                "metric_name": reference_key,
                "value": value,
                "unit": unit,
                "status": measured_status(reference),
            }
        )

    finish_axes(
        ax,
        title=f"Service around recorded events ({unit})",
        x_label="simulated time (s)",
        y_label=_axis_label("rate", unit),
        legend=True,
    )

    n_missing, n_failed = _validity_counts(rows)
    spec = FigureSpec(
        figure_id="C03",
        title="Event-aligned offered, delivered and unmet service",
        question=C03_QUESTION,
        x_label="simulated time (s)",
        y_label=_axis_label("rate", unit),
        metric_definition=_metric_definition(
            metric_names[0],
            opts,
            "offered, delivered and unmet service rates as recorded per interval; unmet is "
            "taken from the record, not recomputed here",
        )[0],
        data_provenance=_provenance_for(rows, kind="service_timeseries_rows")
        + [
            provenance_entry(
                None,
                [e.to_json() if hasattr(e, "to_json") else e for e in events],
                kind="world_events",
                n_rows=len(events),
            )
        ],
        selection_rule="one episode of one recorded world; no pooling across worlds",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded for the rollout")),
        statistical_unit="one recorded episode (single trace; not a cross-fit summary)",
        n_evaluation_episodes=1,
        n_missing=n_missing,
        n_failed=n_failed,
        alignment_rule="samples are drawn at their recorded simulated times; events use their own recorded times",
        uncertainty_method="none: a single recorded trace is shown, not a summary",
        caption=(
            "Shows what the recorded trace did around the recorded events. An improvement "
            "after a repair marker is not evidence that the UAVs caused it: repair is an "
            "exogenous world event on its own schedule. Reference lines appear only where "
            "they were recorded, and a sample with a non-OK validity is a gap, not a zero. "
            "Does not demonstrate a causal contribution of the controller."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C04 - How quickly and reliably does service recover?
# --------------------------------------------------------------------------------------

C04_QUESTION = "How quickly and reliably does service recover?"

#: Outcome labels treated as a completed recovery. Everything else is censored or failed.
_RECOVERED_OUTCOMES = frozenset({"recovered", "recovery", "restored"})


def c04_recovery_times(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Per-episode time-to-recovery dots with explicit censoring.

    Restrictions enforced here: an unrecovered episode is never plotted at zero - it is
    drawn at its observation limit with a distinct caret marker meaning "at least this
    long" - the censoring reasons are counted in the table, and any mean is labelled
    conditional on recovery and is taken from the statistics module rather than computed
    here.
    """

    opts = dict(options or {})
    title = "C04 Time to recovery"
    outcomes = _as_sequence(inputs.get("recovery_outcomes"))
    if not outcomes:
        return _missing(
            "C04",
            title,
            "recovery_outcomes (per-episode recovery outcome records)",
            question=C04_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )
    deadline = inputs.get("recovery_deadline_s", opts.get("recovery_deadline_s"))
    deadline_value = measured_value(deadline)

    def _attr(item: Any, name: str, default: Any = None) -> Any:
        if isinstance(item, Mapping):
            return item.get(name, default)
        return getattr(item, name, default)

    fig, axes = new_figure(figsize=(11.0, 5.8), ncols=2, width_ratios=(3.0, 2.0))
    ax_dots, ax_reasons = axes.tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    observation_fallback = deadline_value
    recovered_x: list[float] = []
    recovered_y: list[float] = []
    censored_x: list[float] = []
    censored_y: list[float] = []
    reason_counts: dict[str, int] = {}
    episode_labels: list[str] = []

    for index, outcome in enumerate(outcomes):
        episode_id = str(_attr(outcome, "episode_id", f"episode_{index}"))
        episode_labels.append(episode_id)
        label = str(_attr(outcome, "outcome", "unknown"))
        time_value = measured_value(_attr(outcome, "time_to_recovery_s"))
        reason = str(_attr(outcome, "reason", "") or "not recorded")
        limit = measured_value(_attr(outcome, "observation_limit_s"))
        is_recovered = label.lower() in _RECOVERED_OUTCOMES and time_value is not None
        if is_recovered:
            recovered_x.append(float(index))
            recovered_y.append(float(time_value))
            plotted = float(time_value)
            meaning = "time_to_recovery_s"
        else:
            bound = limit if limit is not None else observation_fallback
            if bound is None:
                warnings.append(
                    f"episode {episode_id}: censored with no observation limit and no declared "
                    "deadline; it is listed in the table but cannot be positioned on the axis"
                )
                reason_counts[f"{label}:{reason}"] = reason_counts.get(f"{label}:{reason}", 0) + 1
                table.append(
                    {
                        "role": "recovery_episode",
                        "episode_id": episode_id,
                        "outcome": label,
                        "time_to_recovery_s": None,
                        "plotted_y_s": None,
                        "plotted_y_meaning": "not plotted (no observation limit)",
                        "censored": True,
                        "censoring_reason": reason,
                    }
                )
                continue
            censored_x.append(float(index))
            censored_y.append(float(bound))
            plotted = float(bound)
            meaning = "observation limit; true time is at least this value"
            reason_counts[f"{label}:{reason}"] = reason_counts.get(f"{label}:{reason}", 0) + 1
        table.append(
            {
                "role": "recovery_episode",
                "episode_id": episode_id,
                "outcome": label,
                "time_to_recovery_s": float(time_value) if is_recovered else None,
                "plotted_y_s": plotted,
                "plotted_y_meaning": meaning,
                "censored": not is_recovered,
                "censoring_reason": "" if is_recovered else reason,
                "status": measured_status(_attr(outcome, "time_to_recovery_s")),
            }
        )

    if recovered_x:
        ax_dots.plot(
            recovered_x,
            recovered_y,
            linestyle="none",
            marker="o",
            markersize=8.0,
            markerfacecolor="#0072B2",
            markeredgecolor="black",
            label="recovered: observed time to recovery",
        )
    if censored_x:
        # A caret pointing up reads as "at least this long"; it is a different shape, not a
        # different colour, so the distinction survives greyscale printing.
        ax_dots.plot(
            censored_x,
            censored_y,
            linestyle="none",
            marker="^",
            markersize=10.0,
            markerfacecolor="none",
            markeredgecolor="#7A0000",
            markeredgewidth=1.8,
            label="censored: not recovered by the observation limit",
        )
        for x_value, y_value in zip(censored_x, censored_y):
            ax_dots.annotate(
                "",
                xy=(x_value, y_value * 1.08 if y_value else 1.0),
                xytext=(x_value, y_value),
                arrowprops={"arrowstyle": "-|>", "color": "#7A0000", "linewidth": 1.2},
            )
    if deadline_value is not None:
        ax_dots.axhline(
            deadline_value,
            color="#000000",
            linestyle=(0, (5, 2)),
            linewidth=1.4,
            label=f"declared deadline ({deadline_value:g} s)",
        )
        table.append(
            {
                "role": "reference_line",
                "episode_id": "",
                "plotted_y_s": float(deadline_value),
                "plotted_y_meaning": "declared recovery deadline (s)",
            }
        )
    else:
        warnings.append("NOT RECORDED: recovery_deadline_s - no deadline line and no recovery fraction")

    ax_dots.set_xticks(range(len(episode_labels)))
    ax_dots.set_xticklabels(
        [_short_label(label) for label in episode_labels],
        rotation=35,
        ha="right",
        fontsize=ANNOTATION_FONT_SIZE,
    )
    bottom = 0.0
    top = max(recovered_y + censored_y + ([deadline_value] if deadline_value else []) + [1.0])
    ax_dots.set_ylim(bottom - 0.05 * top, top * 1.2)
    finish_axes(
        ax_dots,
        title="Time to recovery per episode (s)",
        x_label="episode identity (categorical)",
        y_label="time to recovery (s)",
        legend=True,
    )

    stats = _load_statistics(opts)
    summary_lines: list[str] = []
    if stats is not None and deadline_value is not None:
        try:
            summary = stats.recovery_summary(list(outcomes), deadline_s=float(deadline_value))
        except Exception as error:
            summary = None
            warnings.append(f"recovery_summary failed: {type(error).__name__}: {error}")
        if summary is not None:
            summary_lines = _summary_annotation_lines(summary)
            for line in summary_lines:
                table.append({"role": "recovery_summary", "summary_field": line})
    else:
        warnings.append(
            "recovery fraction and conditional mean not shown: they are produced by the "
            "statistics module, which is unavailable or has no declared deadline here"
        )

    for reason, count in sorted(reason_counts.items()):
        table.append({"role": "censoring_reason_count", "censoring_reason": reason, "count": count})
    lines = [
        f"episodes: {len(outcomes)}",
        f"recovered: {len(recovered_x)}",
        f"censored / competing outcome: {len(censored_x)}",
        "",
        "censoring reasons (outcome:reason -> episodes):",
    ]
    if reason_counts:
        lines.extend(f"  {reason} -> {count}" for reason, count in sorted(reason_counts.items()))
    else:
        lines.append("  (none)")
    if summary_lines:
        lines.append("")
        lines.append("statistics module summary (any mean below is")
        lines.append("conditional on recovery):")
        lines.extend(summary_lines)
    _text_panel(ax_reasons, "Outcome and censoring-reason counts", lines)

    spec = FigureSpec(
        figure_id="C04",
        title="Per-episode time to recovery with censoring",
        question=C04_QUESTION,
        x_label="episode identity (categorical)",
        y_label="time to recovery (s)",
        metric_definition=_metric_definition(
            "time_to_recovery_s",
            opts,
            "time from the recorded outage onset to the recorded restoration criterion, in "
            "seconds; an episode that never met the criterion has no value and is censored "
            "at its observation limit",
        )[0],
        data_provenance=[
            provenance_entry(
                inputs.get("recovery_source_path"),
                [o if isinstance(o, Mapping) else _summary_annotation_lines(o) for o in outcomes],
                kind="recovery_outcomes",
                n_rows=len(outcomes),
            )
        ],
        selection_rule="every supplied episode is shown; no episode is dropped for being unrecovered",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded for the evaluated policy")),
        statistical_unit="one evaluation episode (episode variability, not fit variability)",
        n_evaluation_episodes=len(outcomes),
        n_missing=sum(1 for row in table if row.get("role") == "recovery_episode" and row.get("censored")),
        n_failed=sum(
            1
            for outcome in outcomes
            if "fail" in str(_attr(outcome, "outcome", "")).lower()
        ),
        uncertainty_method=(
            "raw episode records; any summary shown comes from the statistics module and any "
            "mean is conditional on recovery"
        ),
        caption=(
            "Each dot is one episode. Filled circles are observed recovery times; open "
            "carets are censored episodes drawn at their observation limit, meaning the true "
            "time is at least that long - they are never placed at zero. Automatic repair, "
            "episode end and technical failure are separate outcomes and are counted "
            "separately. Any mean shown is conditional on recovery and is not the expected "
            "recovery time of the population. Does not demonstrate a recovery cause."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C05 - Is access or backhaul limiting service?
# --------------------------------------------------------------------------------------

C05_QUESTION = "Is access or backhaul limiting service?"


def c05_capacity_bottleneck(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Link and resource-domain utilization over time with integrated unmet traffic.

    Restrictions enforced here: the utilization axis is labelled as a fraction of
    *isolated link* capacity, the shared-resource-domain panel is what shows schedulable
    contention, and the caption refuses to convert saturation into a causal claim about
    which element is responsible for unmet demand.
    """

    opts = dict(options or {})
    title = "C05 Capacity and bottleneck"
    frames = _as_sequence(inputs.get("link_frames"))
    if not frames:
        return _missing(
            "C05",
            title,
            "link_frames (per-time link utilization records)",
            question=C05_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    threshold = float(opts.get("saturation_threshold", 0.95))
    fig, axes = new_figure(figsize=(10.0, 8.5), nrows=3, sharex=True)
    ax_links, ax_domains, ax_unmet = axes.tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    link_series: dict[str, list[tuple[float, float | None, str]]] = {}
    domain_series: dict[str, list[tuple[float, float | None, str]]] = {}
    for frame in frames:
        time_s = float(frame.get("time_s", 0.0)) if isinstance(frame, Mapping) else 0.0
        for link in _as_sequence(frame.get("links") if isinstance(frame, Mapping) else None):
            key = str(getattr(link, "link_key", None) or _entity_key(link))
            value = measured_value(getattr(link, "utilization", None))
            link_series.setdefault(key, []).append(
                (time_s, value, measured_status(getattr(link, "utilization", None)))
            )
            table.append(
                {
                    "role": "link_utilization",
                    "time_s": time_s,
                    "link_key": key,
                    "link_class": str(getattr(link, "link_class", "")),
                    "resource_domain": getattr(link, "resource_domain", None),
                    "utilization": value,
                    "capacity_mbps": measured_value(getattr(link, "capacity_mbps", None)),
                    "flow_mbps": measured_value(getattr(link, "flow_mbps", None)),
                    "status": measured_status(getattr(link, "utilization", None)),
                }
            )
        for domain in _as_sequence(
            frame.get("resource_domains") if isinstance(frame, Mapping) else None
        ):
            key = str(getattr(domain, "domain_id", None) or _entity_key(domain))
            value = measured_value(getattr(domain, "utilization", None))
            domain_series.setdefault(key, []).append(
                (time_s, value, measured_status(getattr(domain, "utilization", None)))
            )
            table.append(
                {
                    "role": "resource_domain_utilization",
                    "time_s": time_s,
                    "domain_id": key,
                    "utilization": value,
                    "status": measured_status(getattr(domain, "utilization", None)),
                }
            )

    styles = apply_method_style(None, sorted(link_series), high_contrast=bool(opts.get("high_contrast")))
    # A real service-restoration frame carries tens of links. Every one is drawn and every
    # one is in the table; only the *legend* is capped, because a 40-entry legend hides the
    # plot it is meant to explain. The cap is a presentation choice and is recorded.
    legend_limit = int(opts.get("link_legend_limit", 12))
    for position, key in enumerate(sorted(link_series)):
        points = sorted(link_series[key], key=lambda item: item[0])
        xs = [p[0] for p in points if p[1] is not None]
        ys = [p[1] for p in points if p[1] is not None]
        style = styles[key]
        if xs:
            ax_links.plot(
                xs,
                ys,
                color=style["color"],
                linestyle=style["linestyle"],
                marker=style["marker"],
                markersize=3.5,
                linewidth=1.4,
                label=key if position < legend_limit else None,
            )
    if len(link_series) > legend_limit:
        warnings.append(
            f"{len(link_series)} links are drawn and tabulated; the legend lists the first "
            f"{legend_limit} by link key. No link is omitted from the figure or the table."
        )
    ax_links.axhline(
        threshold,
        color="#000000",
        linestyle=(0, (4, 3)),
        linewidth=1.2,
        label=f"declared saturation threshold ({threshold:g})",
    )
    table.append(
        {
            "role": "reference_line",
            "utilization": threshold,
            "status": "declared_saturation_threshold",
        }
    )
    finish_axes(
        ax_links,
        title="Per-link utilization (fraction of isolated link capacity)",
        y_label="utilization (fraction of isolated capacity)",
        legend=True,
    )

    if domain_series:
        domain_styles = apply_method_style(None, sorted(domain_series))
        for key in sorted(domain_series):
            points = sorted(domain_series[key], key=lambda item: item[0])
            xs = [p[0] for p in points if p[1] is not None]
            ys = [p[1] for p in points if p[1] is not None]
            style = domain_styles[key]
            if xs:
                ax_domains.plot(
                    xs,
                    ys,
                    color=style["color"],
                    linestyle=style["linestyle"],
                    marker=style["marker"],
                    markersize=3.5,
                    linewidth=1.6,
                    label=f"domain {key}",
                )
                saturated = [x for x, y in zip(xs, ys) if y >= threshold]
                for x_value in saturated:
                    ax_domains.axvspan(
                        x_value - 0.001, x_value + 0.001, color="#E69F00", alpha=0.25, linewidth=0
                    )
                    table.append(
                        {
                            "role": "domain_saturated_sample",
                            "time_s": x_value,
                            "domain_id": key,
                            "status": "at_or_above_threshold",
                        }
                    )
        ax_domains.axhline(threshold, color="#000000", linestyle=(0, (4, 3)), linewidth=1.2)
        finish_axes(
            ax_domains,
            title="Shared resource-domain utilization (schedulable contention)",
            y_label="utilization (fraction of domain capacity)",
            legend=True,
        )
    else:
        _text_panel(
            ax_domains,
            "Shared resource-domain utilization",
            [
                "NOT RECORDED: resource_domains",
                "Per-link utilization above is isolated-link capacity only. Without the",
                "resource-domain records, schedulable contention cannot be shown, and",
                "per-link headroom must not be read as spare schedulable capacity.",
            ],
            color="#7A0000",
        )
        warnings.append("NOT RECORDED: resource_domains in link_frames")

    unmet_rows = _as_sequence(inputs.get("unmet_traffic"))
    if unmet_rows:
        unmet_unit = _record_unit(unmet_rows)
        points = sorted(
            (
                (
                    float(getattr(r, "x_value", 0.0) or 0.0),
                    measured_value(getattr(r, "value", None)),
                    getattr(r, "interval_start_s", None),
                    getattr(r, "interval_end_s", None),
                    r,
                )
                for r in unmet_rows
            ),
            key=lambda item: item[0],
        )
        cumulative = 0.0
        xs: list[float] = []
        ys: list[float] = []
        for x_value, value, start_s, end_s, row in points:
            if value is None:
                warnings.append(
                    "an unmet-traffic sample has a non-OK validity; the integral is not "
                    "continued across it and the gap is recorded in the table"
                )
                table.append(
                    {
                        "role": "unmet_sample",
                        "time_s": x_value,
                        "unmet_rate": None,
                        "status": measured_status(getattr(row, "value", None)),
                    }
                )
                continue
            width = (
                float(end_s) - float(start_s)
                if start_s is not None and end_s is not None
                else float(opts.get("interval_width_s", 1.0))
            )
            cumulative += value * width
            xs.append(x_value)
            ys.append(cumulative)
            table.append(
                {
                    "role": "unmet_integral_point",
                    "time_s": x_value,
                    "unmet_rate": value,
                    "interval_width_s": width,
                    "cumulative_unmet": cumulative,
                    "unit": f"{unmet_unit} x s",
                    "status": "ok",
                }
            )
        if xs:
            ax_unmet.plot(xs, ys, color="#7A0000", linestyle="-", linewidth=1.8, marker="o", markersize=3.5)
        finish_axes(
            ax_unmet,
            title=f"Integrated unmet traffic (cumulative, {unmet_unit} x s)",
            x_label="simulated time (s)",
            y_label=f"cumulative unmet ({unmet_unit} x s)",
        )
    else:
        _text_panel(
            ax_unmet,
            "Integrated unmet traffic",
            [
                "NOT RECORDED: unmet_traffic",
                "No unmet-demand record was supplied, so the integral is not shown.",
                "Utilization alone does not stand in for unmet demand.",
            ],
            color="#7A0000",
        )
        ax_unmet.set_xlabel("simulated time (s)")
        warnings.append("NOT RECORDED: unmet_traffic")

    spec = FigureSpec(
        figure_id="C05",
        title="Link and resource-domain utilization with unmet traffic",
        question=C05_QUESTION,
        x_label="simulated time (s)",
        y_label="utilization (fraction) and cumulative unmet (rate x s)",
        metric_definition=(
            "link utilization is recorded flow divided by that link's isolated capacity; "
            "resource-domain utilization is the recorded occupancy of a shared radio "
            "resource; integrated unmet traffic is the recorded unmet rate multiplied by "
            "each record's own interval width and accumulated"
        ),
        data_provenance=[
            provenance_entry(
                inputs.get("link_source_path"),
                [
                    {
                        "time_s": frame.get("time_s") if isinstance(frame, Mapping) else None,
                        "links": [
                            link.to_json() if hasattr(link, "to_json") else str(link)
                            for link in _as_sequence(
                                frame.get("links") if isinstance(frame, Mapping) else None
                            )
                        ],
                    }
                    for frame in frames
                ],
                kind="link_frames",
                n_rows=len(frames),
            )
        ]
        + _provenance_for(unmet_rows, kind="unmet_traffic_rows"),
        selection_rule="all supplied frames of one recorded episode, in recorded time order",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded for the rollout")),
        statistical_unit="one recorded episode (single trace)",
        n_evaluation_episodes=1,
        n_missing=sum(1 for row in table if row.get("status", "").startswith(("unknown", "not_recorded"))),
        uncertainty_method="none: recorded per-sample values are drawn as recorded",
        caption=(
            "Per-link utilization is measured against each link's isolated capacity; it is "
            "not the schedulable flow, which depends on the shared resource domain shown in "
            "the middle panel. A saturated link or domain coinciding with unmet demand does "
            "not establish which element is responsible: the schedule, the demand pattern "
            "and the topology all participate. Does not demonstrate a bottleneck cause."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C06 - Where are users or demand underserved?
# --------------------------------------------------------------------------------------

C06_QUESTION = "Where are users or demand underserved?"

#: Three states that must never collapse into one another, plus the served gradations.
#: Each carries its own marker shape *and* fill *and* (for the unknown states) a hatch, so
#: the distinction survives greyscale printing and colour-blind vision.
_DEMAND_STATE_STYLE: dict[str, dict[str, Any]] = {
    "served": {
        "marker": "o",
        "facecolor": "#0072B2",
        "edgecolor": "#00304D",
        "hatch": None,
        "label": "served (delivered >= offered)",
    },
    "partially_served": {
        "marker": "D",
        "facecolor": "#56B4E9",
        "edgecolor": "#00304D",
        "hatch": None,
        "label": "partially served (0 < delivered < offered)",
    },
    "unserved": {
        "marker": "v",
        "facecolor": "#CC79A7",
        "edgecolor": "#000000",
        "hatch": None,
        "label": "unserved (offered > 0, delivered = 0)",
    },
    "zero_demand": {
        "marker": "o",
        "facecolor": "none",
        "edgecolor": "#000000",
        "hatch": None,
        "label": "zero demand (measured 0, not missing)",
    },
    "demand_unknown": {
        "marker": "s",
        "facecolor": "#FFFFFF",
        "edgecolor": "#8C8C8C",
        "hatch": "xxx",
        "label": "demand unknown (not observed)",
    },
    "demand_not_applicable": {
        "marker": "X",
        "facecolor": "#FFFFFF",
        "edgecolor": "#444444",
        "hatch": "..",
        "label": "demand not applicable (environment models no traffic demand)",
    },
    "delivery_unknown": {
        "marker": "P",
        "facecolor": "#FFFFFF",
        "edgecolor": "#444444",
        "hatch": "///",
        "label": "delivery unknown (demand observed)",
    },
}

#: Marker AREA is proportional to weight, because perceived quantity follows area, not
#: radius. ``scatter`` takes ``s`` in points squared, so the weight is passed straight in.
DEFAULT_AREA_PER_UNIT = 60.0
MIN_MARKER_AREA = 18.0


def _demand_state(offered: Any, delivered: Any) -> str:
    offered_value = measured_value(offered)
    delivered_value = measured_value(delivered)
    if offered_value is None:
        # "This environment has no traffic-demand model" is a different fact from "this
        # entity was not observed"; the legacy relay route reports the former for every
        # ground marker, and collapsing the two would invent an observation problem.
        if getattr(offered, "validity", None) is Validity.NOT_APPLICABLE:
            return "demand_not_applicable"
        return "demand_unknown"
    if offered_value == 0.0:
        return "zero_demand"
    if delivered_value is None:
        return "delivery_unknown"
    if delivered_value <= 0.0:
        return "unserved"
    if delivered_value < offered_value:
        return "partially_served"
    return "served"


def c06_spatial_service(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Spatial maps of offered, delivered and unmet demand with honest missing states.

    Restrictions enforced here: zero demand, unknown demand and unserved demand get three
    different marker shapes (and a hatch for the unknown states), so they can never be read
    as one another; marker *area* is proportional to the weight with a visible size-scale
    legend; the aspect ratio is equal and a metre scale bar is drawn; and an aggregate
    demand point is labelled as an aggregate, never as a person.
    """

    opts = dict(options or {})
    title = "C06 Spatial service"
    entities = _as_sequence(inputs.get("ground_entities"))
    if not entities:
        return _missing(
            "C06",
            title,
            "ground_entities (per-entity offered/delivered demand with positions)",
            question=C06_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    area_per_unit = float(opts.get("area_per_unit", DEFAULT_AREA_PER_UNIT))
    geometry = inputs.get("geometry")
    bounds = getattr(geometry, "bounds_m", None) if geometry is not None else None

    fig, axes = new_figure(figsize=(12.0, 9.0), nrows=2, ncols=2)
    ax_offered, ax_delivered, ax_unmet, ax_ratio = axes.ravel().tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    rows: list[dict[str, Any]] = []
    has_aggregate = False
    for entity in entities:
        entity_id = getattr(entity, "entity", None)
        key = _entity_key(entity_id)
        kind = getattr(getattr(entity_id, "kind", None), "value", "unknown")
        is_aggregate = bool(getattr(getattr(entity_id, "kind", None), "is_aggregate", False))
        has_aggregate = has_aggregate or is_aggregate
        position = getattr(entity, "position_m", (0.0, 0.0, 0.0))
        offered = getattr(entity, "offered_mbps", None)
        delivered = getattr(entity, "delivered_mbps", None)
        offered_value = measured_value(offered)
        delivered_value = measured_value(delivered)
        unmet_value = (
            None
            if offered_value is None or delivered_value is None
            else max(0.0, offered_value - delivered_value)
        )
        state = _demand_state(offered, delivered)
        ratio = (
            None
            if offered_value is None or delivered_value is None or offered_value <= 0.0
            else delivered_value / offered_value
        )
        rows.append(
            {
                "entity_key": key,
                "entity_kind": kind,
                "is_aggregate": is_aggregate,
                "represents_count": int(getattr(entity, "represents_count", 1) or 1),
                "x_m": float(position[0]),
                "y_m": float(position[1]),
                "offered_mbps": offered_value,
                "offered_status": measured_status(offered),
                "delivered_mbps": delivered_value,
                "delivered_status": measured_status(delivered),
                "unmet_mbps": unmet_value,
                "service_ratio": ratio,
                "status": state,
                "observed": bool(getattr(entity, "observed", True)),
            }
        )

    def _draw_map(ax: Any, value_key: str, panel_title: str) -> None:
        for state, style in _DEMAND_STATE_STYLE.items():
            group = [row for row in rows if row["status"] == state]
            if not group:
                continue
            weights = [row.get(value_key) for row in group]
            sizes = [
                MIN_MARKER_AREA if (w is None or w <= 0.0) else max(MIN_MARKER_AREA, area_per_unit * w)
                for w in weights
            ]
            label = style["label"]
            if any(row["is_aggregate"] for row in group):
                label += " [aggregate demand point, not a person]"
            ax.scatter(
                [row["x_m"] for row in group],
                [row["y_m"] for row in group],
                s=sizes,
                marker=style["marker"],
                facecolors=style["facecolor"],
                edgecolors=style["edgecolor"],
                hatch=style["hatch"],
                linewidths=1.2,
                label=label,
                zorder=3,
            )
            for row, size, weight in zip(group, sizes, weights):
                table.append(
                    {
                        "role": f"map_marker_{value_key}",
                        "panel": panel_title,
                        "entity_key": row["entity_key"],
                        "entity_kind": row["entity_kind"],
                        "is_aggregate": row["is_aggregate"],
                        "represents_count": row["represents_count"],
                        "x_m": row["x_m"],
                        "y_m": row["y_m"],
                        "weight": weight,
                        "marker_area_points2": float(size),
                        "marker_shape": style["marker"],
                        "marker_hatch": style["hatch"] or "",
                        "status": row["status"],
                        "offered_status": row["offered_status"],
                        "delivered_status": row["delivered_status"],
                    }
                )
        if bounds is not None:
            ax.set_xlim(float(bounds[0]), float(bounds[2]))
            ax.set_ylim(float(bounds[1]), float(bounds[3]))
        ax.set_aspect("equal", adjustable="box")
        finish_axes(
            ax,
            title=panel_title,
            x_label="east (m)",
            y_label="north (m)",
            legend=True,
            grid=True,
        )
        length = _add_metre_scale_bar(ax)
        table.append(
            {
                "role": "scale_bar",
                "panel": panel_title,
                "weight": length,
                "status": "scale_bar_length_m",
            }
        )

    _draw_map(ax_offered, "offered_mbps", "Offered demand (Mbps), marker area proportional to rate")
    _draw_map(ax_delivered, "delivered_mbps", "Delivered rate (Mbps), marker area proportional to rate")
    _draw_map(ax_unmet, "unmet_mbps", "Unmet demand (Mbps), marker area proportional to rate")

    # Size-scale legend: without it an area encoding cannot be read quantitatively.
    from matplotlib.lines import Line2D

    reference_weights = [w for w in (1.0, 5.0, 10.0) if w is not None]
    handles = [
        Line2D(
            [],
            [],
            linestyle="none",
            marker="o",
            markerfacecolor="#0072B2",
            markeredgecolor="#00304D",
            markersize=math.sqrt(max(MIN_MARKER_AREA, area_per_unit * weight)),
            label=f"{weight:g} Mbps",
        )
        for weight in reference_weights
    ]
    size_legend = ax_offered.legend(
        handles=handles,
        title="marker AREA proportional to rate",
        loc="lower right",
        fontsize=LEGEND_FONT_SIZE,
        labelspacing=1.4,
        borderpad=0.9,
    )
    size_legend.get_title().set_fontsize(LEGEND_FONT_SIZE)
    ax_offered.add_artist(size_legend)
    for weight in reference_weights:
        table.append(
            {
                "role": "size_scale_reference",
                "weight": float(weight),
                "marker_area_points2": float(max(MIN_MARKER_AREA, area_per_unit * weight)),
                "status": "legend_reference",
            }
        )

    ratios = [row["service_ratio"] for row in rows if row["service_ratio"] is not None]
    if ratios:
        counts, edges, _ = ax_ratio.hist(
            ratios, bins=min(10, max(3, len(ratios))), color="#0072B2", edgecolor="black"
        )
        for index, count in enumerate(np.atleast_1d(counts).tolist()):
            table.append(
                {
                    "role": "service_ratio_bin",
                    "bin_low": float(edges[index]),
                    "bin_high": float(edges[index + 1]),
                    "count": int(count),
                    "status": "per_entity_ratio",
                }
            )
    unknown_ratio = sum(1 for row in rows if row["service_ratio"] is None)
    ax_ratio.text(
        0.02,
        0.92,
        f"entities without a defined ratio: {unknown_ratio}\n"
        "(zero demand or an unknown value; not counted as 0.0)",
        transform=ax_ratio.transAxes,
        fontsize=ANNOTATION_FONT_SIZE,
        color="#7A0000",
        va="top",
    )
    finish_axes(
        ax_ratio,
        title="Per-entity service ratio (delivered / offered, dimensionless)",
        x_label="service ratio (delivered / offered)",
        y_label="entities (count)",
    )

    state_counts: dict[str, int] = {}
    for row in rows:
        state_counts[row["status"]] = state_counts.get(row["status"], 0) + 1
    for state, count in sorted(state_counts.items()):
        table.append({"role": "state_count", "status": state, "count": count})
    if has_aggregate:
        warnings.append(
            "some markers are aggregate demand points for a source grid cell; they are "
            "labelled as aggregates and must not be read as individual people"
        )
    if state_counts.get("demand_unknown"):
        warnings.append(
            f"{state_counts['demand_unknown']} entity/entities have unknown demand; they are "
            "drawn with a hatched square, never as zero demand"
        )
    if state_counts.get("demand_not_applicable"):
        warnings.append(
            f"{state_counts['demand_not_applicable']} entity/entities report demand as not "
            "applicable: this environment models no traffic demand, so offered and "
            "delivered rates do not exist for them and none is displayed"
        )

    spec = FigureSpec(
        figure_id="C06",
        title="Spatial offered, delivered and unmet demand",
        question=C06_QUESTION,
        x_label="east (m)",
        y_label="north (m)",
        metric_definition=(
            "offered and delivered rates as recorded per entity (Mbps); unmet is offered "
            "minus delivered, floored at zero, computed only where both were recorded; "
            "service ratio is delivered/offered and is undefined for zero or unknown demand"
        ),
        data_provenance=[
            provenance_entry(
                inputs.get("scene_source_path"),
                [e.to_json() if hasattr(e, "to_json") else str(e) for e in entities],
                kind="ground_entities",
                n_rows=len(entities),
            )
        ],
        selection_rule="every supplied entity is drawn, including unobserved ones",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded for the frame shown")),
        statistical_unit="one recorded frame (spatial snapshot, not a summary over episodes)",
        n_missing=state_counts.get("demand_unknown", 0) + state_counts.get("delivery_unknown", 0),
        uncertainty_method="none: a recorded snapshot is drawn as recorded",
        caption=(
            "Marker area - not radius - is proportional to the recorded rate, and the "
            "size-scale legend gives the mapping. Zero demand, unknown demand and unserved "
            "demand are three different markers, because a measured zero and a missing "
            "observation are different facts. Aggregate demand points represent a source "
            "grid cell, not a person, and no per-person demand is fabricated. The axes are "
            "equal-aspect with a metre scale bar. Does not demonstrate why a location is "
            "underserved."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C07 - What does the controller actually do?
# --------------------------------------------------------------------------------------

C07_QUESTION = "What does the controller actually do?"


def c07_controller_behaviour(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """UAV trajectories, altitude, speed, requested versus executed action and effort.

    Restrictions enforced here: the effort axis is "motion effort (s)", an explicitly
    defined speed-weighted active time, and the module never converts it to joules or
    invents a battery value. Recorded energy, if present, is reported in the table under
    its recorded unit rather than being rescaled.
    """

    opts = dict(options or {})
    title = "C07 Controller behaviour"
    frames = _as_sequence(inputs.get("uav_frames"))
    if not frames:
        return _missing(
            "C07",
            title,
            "uav_frames (per-time UAV state records with positions)",
            question=C07_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    tracks: dict[str, list[tuple[float, Any]]] = {}
    for frame in frames:
        if not isinstance(frame, Mapping):
            continue
        time_s = float(frame.get("time_s", 0.0))
        for uav in _as_sequence(frame.get("uavs")):
            tracks.setdefault(_entity_key(getattr(uav, "entity", uav)), []).append((time_s, uav))
    if not tracks:
        return _missing(
            "C07",
            title,
            "uav_frames[*].uavs (UAV state records inside the frames)",
            question=C07_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    fig, axes = new_figure(figsize=(13.0, 8.0), nrows=2, ncols=3)
    ax_traj, ax_alt, ax_speed, ax_distance, ax_action, ax_effort = axes.ravel().tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []
    styles = apply_method_style(None, sorted(tracks), high_contrast=bool(opts.get("high_contrast")))

    speeds_all: list[float] = []
    for key in sorted(tracks):
        for _, uav in tracks[key]:
            velocity = getattr(uav, "executed_velocity_mps", None)
            if velocity is not None:
                speeds_all.append(float(np.linalg.norm(np.asarray(velocity, dtype=float))))
    reference_speed = float(
        opts.get("reference_speed_mps", max(speeds_all) if speeds_all else 0.0) or 0.0
    )
    if reference_speed <= 0.0:
        warnings.append(
            "no positive reference speed is available; motion effort is reported as "
            "unweighted active time (s)"
        )

    effort_labels: list[str] = []
    effort_values: list[float] = []
    for key in sorted(tracks):
        series = sorted(tracks[key], key=lambda item: item[0])
        style = styles[key]
        times = [float(t) for t, _ in series]
        xs = [float(getattr(u, "position_m", (0, 0, 0))[0]) for _, u in series]
        ys = [float(getattr(u, "position_m", (0, 0, 0))[1]) for _, u in series]
        zs = [float(getattr(u, "position_m", (0, 0, 0))[2]) for _, u in series]
        ax_traj.plot(
            xs,
            ys,
            color=style["color"],
            linestyle=style["linestyle"],
            linewidth=1.6,
            marker=style["marker"],
            markersize=3.5,
            label=key,
        )
        ax_traj.plot([xs[0]], [ys[0]], marker="s", markersize=9.0, markerfacecolor="none",
                     markeredgecolor=style["color"], linestyle="none")
        ax_traj.plot([xs[-1]], [ys[-1]], marker="*", markersize=12.0, color=style["color"],
                     linestyle="none")
        ax_alt.plot(times, zs, color=style["color"], linestyle=style["linestyle"], linewidth=1.6,
                    label=key)

        speeds: list[float | None] = []
        for _, uav in series:
            velocity = getattr(uav, "executed_velocity_mps", None)
            speeds.append(
                None
                if velocity is None
                else float(np.linalg.norm(np.asarray(velocity, dtype=float)))
            )
        speed_times = [t for t, s in zip(times, speeds) if s is not None]
        speed_values = [s for s in speeds if s is not None]
        if speed_values:
            ax_speed.plot(
                speed_times,
                speed_values,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=1.6,
                label=key,
            )
        else:
            warnings.append(f"NOT RECORDED: executed_velocity_mps for {key}")

        cumulative = [0.0]
        for index in range(1, len(series)):
            step = math.dist((xs[index - 1], ys[index - 1], zs[index - 1]), (xs[index], ys[index], zs[index]))
            cumulative.append(cumulative[-1] + step)
        ax_distance.plot(
            times, cumulative, color=style["color"], linestyle=style["linestyle"], linewidth=1.6, label=key
        )

        effort = 0.0
        contributions = 0
        for index in range(1, len(times)):
            dt = times[index] - times[index - 1]
            speed = speeds[index] if speeds[index] is not None else None
            if speed is None or dt <= 0:
                continue
            effort += dt * (speed / reference_speed if reference_speed > 0 else 1.0)
            contributions += 1
        effort_labels.append(key)
        # No usable speed sample means the effort is *unrecorded*, not zero. A trace that
        # records positions but no executed velocity would otherwise publish "0 s of
        # motion effort" for a UAV that visibly moved.
        effort_values.append(effort if contributions else None)
        if not contributions:
            warnings.append(
                f"motion effort for {key} is not computable: no recorded speed sample; it is "
                "reported as absent, not as zero"
            )

        requested: list[float] = []
        executed: list[float] = []
        for _, uav in series:
            request = getattr(uav, "requested_velocity_mps", None)
            execute = getattr(uav, "executed_velocity_mps", None)
            if request is None or execute is None:
                continue
            requested.append(float(np.linalg.norm(np.asarray(request, dtype=float))))
            executed.append(float(np.linalg.norm(np.asarray(execute, dtype=float))))
        if requested:
            ax_action.plot(
                requested,
                executed,
                linestyle="none",
                marker=style["marker"],
                markersize=6.0,
                markerfacecolor=style["color"],
                markeredgecolor="black",
                label=key,
            )
        else:
            # Name the side that is actually absent: a comparison needs both, and blaming
            # the recorded one would send a reader looking for the wrong gap.
            absent_sides = [
                name
                for name, present in (
                    (
                        "requested_velocity_mps",
                        any(getattr(u, "requested_velocity_mps", None) is not None for _, u in series),
                    ),
                    (
                        "executed_velocity_mps",
                        any(getattr(u, "executed_velocity_mps", None) is not None for _, u in series),
                    ),
                )
                if not present
            ]
            warnings.append(
                f"requested-versus-executed action for {key} needs both velocities; "
                + (
                    "NOT RECORDED: " + ", ".join(absent_sides)
                    if absent_sides
                    else "no sample carries both"
                )
            )

        for index, (time_s, uav) in enumerate(series):
            energy = getattr(uav, "energy", None)
            table.append(
                {
                    "role": "uav_sample",
                    "uav_key": key,
                    "time_s": float(time_s),
                    "x_m": xs[index],
                    "y_m": ys[index],
                    "altitude_m": zs[index],
                    "speed_mps": speeds[index],
                    "cumulative_distance_m": cumulative[index],
                    "requested_speed_mps": (
                        None
                        if getattr(uav, "requested_velocity_mps", None) is None
                        else float(
                            np.linalg.norm(
                                np.asarray(getattr(uav, "requested_velocity_mps"), dtype=float)
                            )
                        )
                    ),
                    "recorded_energy_value": measured_value(energy),
                    "recorded_energy_unit": getattr(energy, "unit", None) if energy is not None else None,
                    "recorded_energy_status": measured_status(energy),
                    "active": bool(getattr(uav, "active", True)),
                }
            )
        table.append(
            {
                "role": "uav_summary",
                "uav_key": key,
                "flight_distance_m": cumulative[-1],
                "motion_effort_s": effort,
                "reference_speed_mps": reference_speed or None,
                "n_samples": len(series),
            }
        )

    if requested_limits := [
        value
        for ax in (ax_action,)
        for line in ax.get_lines()
        for value in list(line.get_xdata()) + list(line.get_ydata())
    ]:
        low = float(min(requested_limits))
        high = float(max(requested_limits))
        ax_action.plot(
            [low, high],
            [low, high],
            color="#000000",
            linestyle=(0, (4, 3)),
            linewidth=1.2,
            label="executed = requested",
        )
        table.append(
            {
                "role": "reference_line",
                "uav_key": "",
                "requested_speed_mps": low,
                "speed_mps": low,
                "flight_distance_m": None,
            }
        )

    drawable_effort = [
        (index, label, value)
        for index, (label, value) in enumerate(zip(effort_labels, effort_values))
        if value is not None
    ]
    if drawable_effort:
        ax_effort.bar(
            [index for index, _, _ in drawable_effort],
            [value for _, _, value in drawable_effort],
            color="#0072B2",
            edgecolor="black",
            hatch="//",
        )
    if effort_labels:
        ax_effort.set_xticks(range(len(effort_labels)))
        ax_effort.set_xticklabels(effort_labels, rotation=30, ha="right", fontsize=ANNOTATION_FONT_SIZE)
    if not drawable_effort:
        ax_effort.text(
            0.5,
            0.5,
            "NOT RECORDED: executed speed\nmotion effort cannot be computed and is not shown as zero",
            ha="center",
            va="center",
            transform=ax_effort.transAxes,
            fontsize=ANNOTATION_FONT_SIZE,
            color="#7A0000",
        )

    ax_traj.set_aspect("equal", adjustable="datalim")
    finish_axes(ax_traj, title="Trajectory (m), square = start, star = end", x_label="east (m)",
                y_label="north (m)", legend=True)
    finish_axes(ax_alt, title="Altitude (m above ground)", x_label="time (s)", y_label="altitude (m)")
    finish_axes(ax_speed, title="Executed speed (m/s)", x_label="time (s)", y_label="speed (m/s)")
    finish_axes(ax_distance, title="Cumulative flight distance (m)", x_label="time (s)",
                y_label="distance (m)")
    finish_axes(ax_action, title="Requested versus executed speed (m/s)",
                x_label="requested speed (m/s)", y_label="executed speed (m/s)", legend=True)
    finish_axes(
        ax_effort,
        title="Motion effort (s), speed-weighted active time",
        x_label="UAV lifetime identity (categorical)",
        y_label="motion effort (s)",
    )

    spec = FigureSpec(
        figure_id="C07",
        title="Controller behaviour: trajectories, kinematics and executed action",
        question=C07_QUESTION,
        x_label="time (s) and east (m), per panel",
        y_label=(
            "position (m), altitude (m), speed (m/s), distance (m), motion effort (s)"
        ),
        metric_definition=(
            "motion effort (s) is the sum over recorded steps of the step duration times the "
            "recorded speed divided by the declared reference speed; it is a "
            "speed-weighted active time in seconds and is NOT energy. No joule, watt or "
            "battery value is computed anywhere in this chart. Flight distance is the "
            "recorded three-dimensional path length in metres."
        ),
        data_provenance=[
            provenance_entry(
                inputs.get("uav_source_path"),
                [
                    {
                        "time_s": frame.get("time_s"),
                        "uavs": [
                            u.to_json() if hasattr(u, "to_json") else str(u)
                            for u in _as_sequence(frame.get("uavs"))
                        ],
                    }
                    for frame in frames
                    if isinstance(frame, Mapping)
                ],
                kind="uav_frames",
                n_rows=len(frames),
            )
        ],
        selection_rule="every UAV lifetime present in the supplied frames",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded for the rollout")),
        statistical_unit="one recorded episode (single trace)",
        n_evaluation_episodes=1,
        uncertainty_method="none: recorded per-step values are drawn as recorded",
        caption=(
            "Shows what the controller did in the recorded episode: path, altitude, speed, "
            "how far the executed velocity followed the requested one, and a speed-weighted "
            "motion effort in seconds. Motion effort is not energy and no battery model "
            "exists in these records, so no joule value is shown. Does not demonstrate that "
            "the behaviour is optimal or that it caused any service outcome."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C08 - What temporal organization does a hierarchy use?
# --------------------------------------------------------------------------------------

C08_QUESTION = "What temporal organization does a hierarchy use?"

#: Colour plus hatch per skill identifier, so the raster is readable in greyscale and the
#: encoding never implies an ordering between two categorical identifiers.
_SKILL_HATCHES: tuple[str, ...] = ("", "///", "...", "xxx", "\\\\\\", "+++", "ooo", "**")


def c08_skill_organization(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Team and per-UAV skill raster, duration distribution in seconds, renewal events.

    Restrictions enforced here: skill identifiers are treated as categorical strings
    everywhere, including in the exported table, and nothing in this chart averages,
    orders or interpolates them. The caption states that label permutation across
    independently trained fits prevents naive pooling of "skill 3" between fits.
    """

    opts = dict(options or {})
    title = "C08 Skill organization"
    segments = _as_sequence(inputs.get("skill_segments"))
    if not segments:
        return _missing(
            "C08",
            title,
            "skill_segments (recorded skill assignment intervals per unit)",
            question=C08_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    def _field(item: Any, name: str, default: Any = None) -> Any:
        if isinstance(item, Mapping):
            return item.get(name, default)
        return getattr(item, name, default)

    fig, axes = new_figure(figsize=(11.5, 8.5), nrows=3, height_ratios=(3.0, 2.0, 1.4))
    ax_raster, ax_duration, ax_events = axes.tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    units = _distinct(str(_field(segment, "unit", "unknown")) for segment in segments)
    units = sorted(units, key=lambda name: (name != "team", name))
    skill_ids = _distinct(str(_field(segment, "skill_id", "unknown")) for segment in segments)
    skill_ids = sorted(skill_ids)
    skill_styles = {
        skill_id: {
            "color": ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#8C8C8C", "#000000"][
                index % 8
            ],
            "hatch": _SKILL_HATCHES[index % len(_SKILL_HATCHES)],
        }
        for index, skill_id in enumerate(skill_ids)
    }

    durations_by_skill: dict[str, list[float]] = {}
    drawn_labels: set[str] = set()
    for segment in segments:
        unit = str(_field(segment, "unit", "unknown"))
        skill_id = str(_field(segment, "skill_id", "unknown"))
        start = _field(segment, "start_s")
        end = _field(segment, "end_s")
        start_value = measured_value(start)
        end_value = measured_value(end)
        if start_value is None or end_value is None:
            warnings.append(
                f"skill segment for unit {unit} skill {skill_id} has an unrecorded boundary "
                "and is listed in the table but not drawn"
            )
            table.append(
                {
                    "role": "skill_segment",
                    "unit": unit,
                    "skill_id": skill_id,
                    "start_s": start_value,
                    "end_s": end_value,
                    "duration_s": None,
                    "renewed": _field(segment, "renewed"),
                    "status": "boundary_not_recorded",
                }
            )
            continue
        duration = float(end_value) - float(start_value)
        durations_by_skill.setdefault(skill_id, []).append(duration)
        row_index = units.index(unit)
        style = skill_styles[skill_id]
        ax_raster.broken_barh(
            [(float(start_value), duration)],
            (row_index - 0.38, 0.76),
            facecolors=style["color"],
            edgecolor="black",
            hatch=style["hatch"],
            linewidth=0.8,
            label=(f"skill {skill_id}" if f"skill {skill_id}" not in drawn_labels else None),
        )
        drawn_labels.add(f"skill {skill_id}")
        renewed = _field(segment, "renewed")
        table.append(
            {
                "role": "skill_segment",
                "unit": unit,
                "skill_id": skill_id,
                "start_s": float(start_value),
                "end_s": float(end_value),
                "duration_s": duration,
                "renewed": None if renewed is None else bool(renewed),
                "status": "recorded",
            }
        )
        if renewed is not None:
            marker = "o" if bool(renewed) else "x"
            ax_events.plot(
                [float(start_value)],
                [row_index],
                linestyle="none",
                marker=marker,
                markersize=8.0,
                markerfacecolor="none" if marker == "o" else None,
                markeredgecolor="#7A0000" if bool(renewed) else "#0072B2",
                color="#0072B2",
                label=None,
            )
            table.append(
                {
                    "role": "skill_boundary_event",
                    "unit": unit,
                    "skill_id": skill_id,
                    "start_s": float(start_value),
                    "renewed": bool(renewed),
                    "status": "renewal" if bool(renewed) else "keep",
                }
            )

    for event in _as_sequence(inputs.get("skill_events")):
        time_s = _field(event, "time_s")
        if time_s is None:
            continue
        renew = _field(event, "renew")
        entity = _field(event, "entity")
        row_index = units.index(str(entity)) if str(entity) in units else -1
        ax_events.plot(
            [float(time_s)],
            [row_index],
            linestyle="none",
            marker="^" if renew else "v",
            markersize=8.0,
            color="#000000",
        )
        team_skill = _field(event, "team_skill_id")
        individual = _field(event, "individual_skill_ids")
        table.append(
            {
                "role": "skill_event",
                "unit": str(entity) if entity is not None else "",
                "skill_id": "" if team_skill is None else str(team_skill),
                "start_s": float(time_s),
                "renewed": None if renew is None else bool(renew),
                "individual_skill_ids": (
                    "" if individual is None else "|".join(str(v) for v in individual)
                ),
                "status": str(_field(event, "availability", "recorded")),
            }
        )

    ax_raster.set_yticks(range(len(units)))
    ax_raster.set_yticklabels(units, fontsize=ANNOTATION_FONT_SIZE)
    ax_raster.set_ylim(-0.6, len(units) - 0.4)
    finish_axes(
        ax_raster,
        title="Skill assignment raster (categorical skill identifier over simulated time)",
        y_label="unit (team / UAV lifetime)",
        legend=True,
    )

    all_durations = [d for values in durations_by_skill.values() for d in values]
    if all_durations:
        counts, edges, _ = ax_duration.hist(
            all_durations,
            bins=min(12, max(3, len(all_durations))),
            color="#8C8C8C",
            edgecolor="black",
        )
        for index, count in enumerate(np.atleast_1d(counts).tolist()):
            table.append(
                {
                    "role": "duration_bin",
                    "skill_id": "all skills pooled within this fit",
                    "start_s": float(edges[index]),
                    "end_s": float(edges[index + 1]),
                    "count": int(count),
                    "status": "duration_histogram_bin",
                }
            )
        offset = 0.0
        for skill_id in skill_ids:
            values = durations_by_skill.get(skill_id, [])
            if not values:
                continue
            ax_duration.plot(
                values,
                np.full(len(values), -0.6 - offset),
                linestyle="none",
                marker="|",
                markersize=10.0,
                color=skill_styles[skill_id]["color"],
                label=f"skill {skill_id} durations",
            )
            offset += 0.5
    finish_axes(
        ax_duration,
        title="Empirical skill duration distribution (s)",
        x_label="skill segment duration (s)",
        y_label="segments (count)",
        legend=True,
    )

    ax_events.set_yticks(range(len(units)))
    ax_events.set_yticklabels(units, fontsize=ANNOTATION_FONT_SIZE)
    ax_events.set_ylim(-1.2, len(units) - 0.4)
    finish_axes(
        ax_events,
        title="Renewal (circle/up) and keep (cross/down) events at recorded times",
        x_label="simulated time (s)",
        y_label="unit",
    )

    for skill_id in skill_ids:
        values = durations_by_skill.get(skill_id, [])
        table.append(
            {
                "role": "skill_id_inventory",
                "skill_id": skill_id,
                "count": len(values),
                "duration_s": float(sum(values)) if values else None,
                "status": "categorical identifier; never averaged or ordered",
            }
        )

    spec = FigureSpec(
        figure_id="C08",
        title="Temporal organization of the skill hierarchy",
        question=C08_QUESTION,
        x_label="simulated time (s)",
        y_label="unit (categorical) and segment count",
        metric_definition=(
            "a skill segment is a recorded interval during which one unit carried one "
            "categorical skill identifier; duration is the recorded end minus the recorded "
            "start, in seconds. Skill identifiers are labels: they are never averaged, "
            "ordered or interpolated."
        ),
        data_provenance=[
            provenance_entry(
                inputs.get("skill_source_path"),
                [s if isinstance(s, Mapping) else str(s) for s in segments],
                kind="skill_segments",
                n_rows=len(segments),
            )
        ],
        selection_rule="every supplied segment of this single recorded rollout",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded for the rollout")),
        statistical_unit="one recorded rollout of one fit (labels are fit-local)",
        n_missing=sum(1 for row in table if row.get("status") == "boundary_not_recorded"),
        uncertainty_method="none: recorded segments are drawn as recorded",
        caption=(
            "Shows when each unit held which skill identifier and how long the segments "
            "lasted. A skill identifier is a label, not a named behaviour: nothing here "
            "averages identifiers, and 'skill 3' in one independently trained fit is not "
            "the same behaviour as 'skill 3' in another, because the labels can permute "
            "between fits. Pooling identifiers across fits is therefore invalid without a "
            "separately verified operational definition. Does not demonstrate that any "
            "segment corresponds to a meaningful role."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C09 - Does roster change affect continuing agents?
# --------------------------------------------------------------------------------------

C09_QUESTION = "Does roster change affect continuing agents?"


def c09_roster_changes(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Membership and lifetime timeline plus episode-aligned performance around changes.

    Restriction enforced here: a row of the timeline is one *lifetime*, identified by
    kind/slot/generation, so a slot that is vacated and later reused produces two separate
    rows and cannot inherit the earlier member's history.
    """

    opts = dict(options or {})
    title = "C09 Roster change"
    intervals = _as_sequence(inputs.get("membership_intervals"))
    if not intervals:
        return _missing(
            "C09",
            title,
            "membership_intervals (per-lifetime join/leave records)",
            question=C09_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    def _field(item: Any, name: str, default: Any = None) -> Any:
        if isinstance(item, Mapping):
            return item.get(name, default)
        return getattr(item, name, default)

    performance_rows = _as_sequence(inputs.get("episode_performance"))
    fig, axes = new_figure(figsize=(11.0, 7.5), nrows=2, height_ratios=(2.2, 2.0))
    ax_timeline, ax_performance = axes.tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    entries: list[dict[str, Any]] = []
    for interval in intervals:
        entity = _field(interval, "entity")
        lifetime_key = _entity_key(entity)
        slot = getattr(entity, "slot", None) if isinstance(entity, EntityId) else _field(interval, "slot")
        generation = (
            getattr(entity, "generation", None)
            if isinstance(entity, EntityId)
            else _field(interval, "generation")
        )
        join_s = measured_value(_field(interval, "join_s"))
        leave_s = measured_value(_field(interval, "leave_s"))
        entries.append(
            {
                "lifetime_key": lifetime_key,
                "slot": slot,
                "generation": generation,
                "join_s": join_s,
                "leave_s": leave_s,
                "join_episode": _field(interval, "join_episode"),
                "leave_episode": _field(interval, "leave_episode"),
            }
        )
    entries.sort(key=lambda row: (str(row["lifetime_key"])))

    horizon = float(
        opts.get(
            "horizon_s",
            max(
                [row["leave_s"] or 0.0 for row in entries]
                + [row["join_s"] or 0.0 for row in entries]
                + [1.0]
            ),
        )
    )
    for index, row in enumerate(entries):
        join_s = row["join_s"]
        leave_s = row["leave_s"]
        if join_s is None:
            warnings.append(f"{row['lifetime_key']}: join time not recorded; bar not drawn")
        else:
            end = horizon if leave_s is None else leave_s
            ax_timeline.broken_barh(
                [(float(join_s), float(end) - float(join_s))],
                (index - 0.36, 0.72),
                facecolors="#56B4E9" if leave_s is None else "#0072B2",
                edgecolor="black",
                hatch="//" if leave_s is None else "",
                linewidth=0.8,
            )
            ax_timeline.plot([float(join_s)], [index], marker=">", color="#000000", markersize=7.0,
                             linestyle="none")
            if leave_s is not None:
                ax_timeline.plot([float(leave_s)], [index], marker="s", color="#7A0000",
                                 markersize=7.0, linestyle="none")
        table.append(
            {
                "role": "membership_interval",
                "lifetime_key": row["lifetime_key"],
                "slot": row["slot"],
                "generation": row["generation"],
                "join_s": join_s,
                "leave_s": leave_s,
                "drawn_end_s": horizon if leave_s is None else leave_s,
                "status": "continuing at horizon" if leave_s is None else "left",
            }
        )

    ax_timeline.set_yticks(range(len(entries)))
    ax_timeline.set_yticklabels([row["lifetime_key"] for row in entries], fontsize=ANNOTATION_FONT_SIZE)
    ax_timeline.set_ylim(-0.7, len(entries) - 0.3)
    finish_axes(
        ax_timeline,
        title="Membership by lifetime identity (kind:slot:generation), hatched bar = still present",
        x_label="simulated time (s)",
        y_label="lifetime identity (categorical)",
    )

    slots_reused = [
        slot
        for slot in {row["slot"] for row in entries if row["slot"] is not None}
        if len([row for row in entries if row["slot"] == slot]) > 1
    ]
    if slots_reused:
        warnings.append(
            "array slot(s) "
            + ", ".join(str(s) for s in sorted(slots_reused, key=str))
            + " carry more than one lifetime; each lifetime is a separate row and no "
            "history is inherited across the reuse"
        )

    if performance_rows:
        metric_name = str(
            opts.get("metric_name")
            or (_distinct(getattr(r, "metric_name", None) for r in performance_rows) or ["unknown"])[0]
        )
        unit = _record_unit(performance_rows)
        points = sorted(
            (
                (float(getattr(r, "x_value", 0.0) or 0.0), measured_value(getattr(r, "value", None)), r)
                for r in _metric_rows(performance_rows, metric_name=metric_name)
                if getattr(r, "x_value", None) is not None
            ),
            key=lambda item: item[0],
        )
        xs = [p[0] for p in points if p[1] is not None]
        ys = [p[1] for p in points if p[1] is not None]
        ax_performance.plot(xs, ys, color="#0072B2", marker="o", markersize=4.5, linewidth=1.5,
                            label=f"{metric_name} ({unit})")
        for x_value, y_value, row in points:
            table.append(
                {
                    "role": "episode_performance",
                    "lifetime_key": "",
                    "episode_index": x_value,
                    "value": y_value,
                    "unit": unit,
                    "status": measured_status(getattr(row, "value", None)),
                }
            )
        marked = False
        for row in entries:
            for key, label, style in (
                ("join_episode", "join", (0, (5, 2))),
                ("leave_episode", "leave", (0, (1, 1.6))),
            ):
                episode = row.get(key)
                if episode is None:
                    continue
                ax_performance.axvline(
                    float(episode),
                    color="#7A0000",
                    linestyle=style,
                    linewidth=1.3,
                    label=f"roster {label}" if not marked else None,
                )
                marked = True
                table.append(
                    {
                        "role": "roster_change_marker",
                        "lifetime_key": row["lifetime_key"],
                        "episode_index": float(episode),
                        "status": label,
                    }
                )
        if not marked:
            warnings.append(
                "NOT RECORDED: join_episode / leave_episode - performance is drawn without "
                "roster-change alignment markers"
            )
        finish_axes(
            ax_performance,
            title=f"Episode-aligned performance: {metric_name} ({unit})",
            x_label="episode index",
            y_label=_axis_label(metric_name, unit),
            legend=True,
        )
    else:
        _text_panel(
            ax_performance,
            "Episode-aligned performance around joins and leaves",
            [
                "NOT RECORDED: episode_performance",
                "The membership timeline above is drawn, but without per-episode",
                "performance rows there is nothing to align to a join or a leave.",
            ],
            color="#7A0000",
        )
        warnings.append("NOT RECORDED: episode_performance")

    mask_diagnostics = inputs.get("mask_diagnostics")
    if mask_diagnostics:
        for key, value in dict(mask_diagnostics).items():
            table.append({"role": "mask_diagnostic", "lifetime_key": str(key), "status": str(value)})
    else:
        warnings.append("NOT RECORDED: mask_diagnostics (history-age and mask legality not shown)")

    spec = FigureSpec(
        figure_id="C09",
        title="Roster membership and continuing-agent performance",
        question=C09_QUESTION,
        x_label="simulated time (s) and episode index",
        y_label="lifetime identity (categorical) and recorded metric",
        metric_definition=(
            "a membership interval is the recorded join and leave time of one lifetime, "
            "identified by kind:slot:generation. A vacated array slot that is later reused "
            "starts a new lifetime with a new generation and a separate row."
        ),
        data_provenance=[
            provenance_entry(
                inputs.get("roster_source_path"),
                [i if isinstance(i, Mapping) else str(i) for i in intervals],
                kind="membership_intervals",
                n_rows=len(intervals),
            )
        ]
        + _provenance_for(performance_rows, kind="episode_performance_rows"),
        selection_rule="every supplied lifetime; no lifetime merged into another by slot",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded")),
        statistical_unit="one recorded run; episodes are the x axis of the lower panel",
        n_evaluation_episodes=(
            len({getattr(r, "episode_id", None) for r in performance_rows if getattr(r, "episode_id", None)})
            or None
        ),
        uncertainty_method="none: recorded values are drawn as recorded",
        caption=(
            "Each timeline row is one lifetime, not one array slot, so a reused slot appears "
            "twice and cannot inherit an earlier member's trail or history. Performance "
            "around a roster change is shown for alignment only: a change in the curve near "
            "a marker is not evidence that the join or leave caused it. Does not demonstrate "
            "a causal effect of roster change."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C10 - How robust is the observed performance?
# --------------------------------------------------------------------------------------

C10_QUESTION = "How robust is the observed performance?"


def c10_robustness_sweep(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Recorded metric against a predeclared sweep factor.

    Restriction enforced here: this function reads existing sweep rows only. It never
    launches a run, never interpolates between measured factor levels and never
    extrapolates beyond the measured range.
    """

    opts = dict(options or {})
    title = "C10 Robustness sweep"
    rows = _as_sequence(inputs.get("sweep_records"))
    if not rows:
        return _missing(
            "C10",
            title,
            "sweep_records (recorded metric rows across a predeclared factor)",
            question=C10_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
            detail=(
                "No robustness study is launched to fill this panel. The sweep must already\n"
                "exist in recorded artifacts before this chart can draw anything."
            ),
        )

    factor_name = str(inputs.get("factor_name", opts.get("factor_name", "declared sweep factor")))
    factor_unit = str(inputs.get("factor_unit", opts.get("factor_unit", "")) or "")
    metric_name = str(
        opts.get("metric_name")
        or (_distinct(getattr(r, "metric_name", None) for r in rows) or ["unknown"])[0]
    )
    rows = _metric_rows(rows, metric_name=metric_name)
    unit = _record_unit(rows)
    stats = _load_statistics(opts)

    fig, ax = new_figure(figsize=(9.5, 5.8))
    table: list[dict[str, Any]] = []
    warnings: list[str] = []
    methods = sorted({str(getattr(r, "method_id", "unknown")) for r in rows})
    styles = apply_method_style(None, methods, high_contrast=bool(opts.get("high_contrast")))
    uncertainty = "unavailable (no interval drawn)"

    for method in methods:
        method_rows = _metric_rows(rows, method_id=method)
        levels = sorted(
            {float(getattr(r, "x_value", 0.0) or 0.0) for r in method_rows if getattr(r, "x_value", None) is not None}
        )
        style = styles[method]
        point_x: list[float] = []
        point_y: list[float] = []
        for level in levels:
            level_rows = [r for r in method_rows if float(getattr(r, "x_value", 0.0) or 0.0) == level]
            for row in level_rows:
                value = measured_value(getattr(row, "value", None))
                if value is not None:
                    ax.plot(
                        [level],
                        [value],
                        linestyle="none",
                        marker=style["marker"],
                        markersize=5.0,
                        markerfacecolor="none",
                        markeredgecolor=style["color"],
                        alpha=0.7,
                    )
                table.append(
                    {
                        "role": "sweep_observation",
                        "method_id": method,
                        "factor_level": level,
                        "factor_name": factor_name,
                        "training_replicate_id": getattr(row, "training_replicate_id", None),
                        "value": value,
                        "unit": unit,
                        "status": measured_status(getattr(row, "value", None)),
                        "source_path": getattr(row, "source_path", None),
                    }
                )
            n_units = len(
                {str(getattr(r, "training_replicate_id", None) or "unlabelled") for r in level_rows}
            )
            _, reduction, notes = _reduce_units(
                stats, level_rows, metric_name=metric_name, rng_seed=opts.get("rng_seed")
            )
            for note in notes:
                if note not in warnings:
                    warnings.append(note)
            point = measured_value(getattr(reduction, "point", None)) if reduction else None
            if point is not None:
                point_x.append(level)
                point_y.append(point)
                table.append(
                    {
                        "role": "sweep_aggregate",
                        "method_id": method,
                        "factor_level": level,
                        "value": point,
                        "unit": unit,
                        "n_units": n_units,
                        "status": "aggregate_over_fits",
                    }
                )
            if _interval_is_drawable(reduction, n_units):
                low = float(measured_value(getattr(reduction, "ci_low", None)))
                high = float(measured_value(getattr(reduction, "ci_high", None)))
                ax.plot([level, level], [low, high], color=style["color"], linewidth=1.8)
                uncertainty = _uncertainty_label(reduction, n_units, unit_kind="fit")
                table.append(
                    {
                        "role": "sweep_interval",
                        "method_id": method,
                        "factor_level": level,
                        "ci_low": low,
                        "ci_high": high,
                        "ci_method": str(getattr(reduction, "ci_method", "")),
                        "n_units": n_units,
                    }
                )
        if point_x:
            ax.plot(
                point_x,
                point_y,
                color=style["color"],
                linestyle=style["linestyle"],
                marker=style["marker"],
                markersize=6.0,
                linewidth=1.6,
                label=f"{method} (aggregate over fits)",
            )
        elif levels:
            ax.plot([], [], color=style["color"], marker=style["marker"], linestyle="none",
                    label=f"{method} (per-fit observations only)")

    finish_axes(
        ax,
        title=f"{metric_name} ({unit}) versus {factor_name}"
        + (f" ({factor_unit})" if factor_unit else ""),
        x_label=f"{factor_name} ({factor_unit})" if factor_unit else f"{factor_name} (recorded levels)",
        y_label=_axis_label(metric_name, unit),
        legend=True,
    )

    n_missing, n_failed = _validity_counts(rows)
    spec = FigureSpec(
        figure_id="C10",
        title="Robustness across a predeclared factor",
        question=C10_QUESTION,
        x_label=f"{factor_name} ({factor_unit})" if factor_unit else f"{factor_name} (recorded levels)",
        y_label=_axis_label(metric_name, unit),
        metric_definition=_metric_definition(
            metric_name, opts, f"{metric_name} as recorded at each measured factor level"
        )[0],
        data_provenance=_provenance_for(rows, kind="sweep_records"),
        selection_rule="only factor levels that were actually measured; nothing is interpolated",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded per sweep row")),
        statistical_unit="independent training replicate (fit) at each factor level",
        n_fits=len({str(getattr(r, "training_replicate_id", None) or "unlabelled") for r in rows}),
        n_missing=n_missing,
        n_failed=n_failed,
        uncertainty_method=uncertainty,
        caption=(
            "Reads an existing sweep only: no robustness study was launched to produce this "
            "panel, and no value is drawn between or beyond the measured levels. Faint open "
            "markers are individual recorded rows; a connected line appears only where an "
            "aggregate over fits was computed. Does not demonstrate behaviour at an "
            "unmeasured factor level."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C11 - Are comparisons computationally transparent?
# --------------------------------------------------------------------------------------

C11_QUESTION = "Are comparisons computationally transparent?"


def c11_computational_transparency(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Quality against training exposure, plus measured wall time where it was recorded.

    Restriction enforced here: no speedup is stated. Wall time is drawn only from recorded
    rows, hardware and configuration differences are declared as uncontrolled, and an
    absent wall-time record leaves a labelled hole instead of an inferred ratio.
    """

    opts = dict(options or {})
    title = "C11 Computational transparency"
    rows = _as_sequence(inputs.get("cost_records"))
    if not rows:
        return _missing(
            "C11",
            title,
            "cost_records (quality-versus-exposure and measured wall-time rows)",
            question=C11_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    quality_metric = str(opts.get("quality_metric", inputs.get("quality_metric", "")) or "")
    wall_metric = str(opts.get("wall_time_metric", inputs.get("wall_time_metric", "wall_time_s")))
    if not quality_metric:
        candidates = [
            name
            for name in _distinct(getattr(r, "metric_name", None) for r in rows)
            if name and name != wall_metric
        ]
        quality_metric = str(candidates[0]) if candidates else ""
    quality_rows = _metric_rows(rows, metric_name=quality_metric) if quality_metric else []
    wall_rows = _metric_rows(rows, metric_name=wall_metric)

    fig, axes = new_figure(figsize=(11.0, 5.6), ncols=2)
    ax_quality, ax_wall = axes.tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    if quality_rows:
        unit = _record_unit(quality_rows)
        methods = sorted({str(getattr(r, "method_id", "unknown")) for r in quality_rows})
        styles = apply_method_style(None, methods)
        for method in methods:
            points = sorted(
                (
                    (float(getattr(r, "x_value", 0.0) or 0.0), measured_value(getattr(r, "value", None)), r)
                    for r in _metric_rows(quality_rows, method_id=method)
                    if getattr(r, "x_value", None) is not None
                ),
                key=lambda item: item[0],
            )
            style = styles[method]
            xs = [p[0] for p in points if p[1] is not None]
            ys = [p[1] for p in points if p[1] is not None]
            if xs:
                ax_quality.plot(
                    xs, ys, color=style["color"], linestyle=style["linestyle"], marker=style["marker"],
                    markersize=4.5, linewidth=1.5, label=method
                )
            for x_value, y_value, row in points:
                table.append(
                    {
                        "role": "quality_vs_exposure",
                        "method_id": method,
                        "training_exposure": x_value,
                        "x_kind": getattr(getattr(row, "x_kind", None), "value", ""),
                        "value": y_value,
                        "unit": unit,
                        "training_replicate_id": getattr(row, "training_replicate_id", None),
                        "status": measured_status(getattr(row, "value", None)),
                    }
                )
        finish_axes(
            ax_quality,
            title=f"Quality versus training exposure: {quality_metric} ({unit})",
            x_label="training exposure (recorded x kind)",
            y_label=_axis_label(quality_metric, unit),
            legend=True,
        )
    else:
        _text_panel(
            ax_quality,
            "Quality versus training exposure",
            ["NOT RECORDED: quality metric rows in cost_records"],
            color="#7A0000",
        )
        warnings.append("NOT RECORDED: quality metric rows in cost_records")

    if wall_rows:
        unit = _record_unit(wall_rows, fallback="s")
        methods = sorted({str(getattr(r, "method_id", "unknown")) for r in wall_rows})
        for index, method in enumerate(methods):
            values = [
                (str(getattr(r, "training_replicate_id", None) or "unlabelled"), measured_value(getattr(r, "value", None)), r)
                for r in _metric_rows(wall_rows, method_id=method)
            ]
            drawn = [(fit, value) for fit, value, _ in values if value is not None]
            if drawn:
                ax_wall.plot(
                    [index] * len(drawn),
                    [value for _, value in drawn],
                    linestyle="none",
                    marker="o",
                    markersize=8.0,
                    markerfacecolor="#0072B2",
                    markeredgecolor="black",
                    label="measured wall time per fit" if index == 0 else None,
                )
            for fit, value, row in values:
                table.append(
                    {
                        "role": "measured_wall_time",
                        "method_id": method,
                        "training_replicate_id": fit,
                        "value": value,
                        "unit": unit,
                        "hardware_note": str(inputs.get("hardware_note", "not recorded")),
                        "status": measured_status(getattr(row, "value", None)),
                    }
                )
        ax_wall.set_xticks(range(len(methods)))
        ax_wall.set_xticklabels(methods, rotation=20, ha="right", fontsize=ANNOTATION_FONT_SIZE)
        finish_axes(
            ax_wall,
            title=f"Measured wall time per fit ({unit})",
            x_label="method (categorical)",
            y_label=_axis_label("wall time", unit),
            legend=True,
        )
    else:
        _text_panel(
            ax_wall,
            "Measured wall time",
            [
                f"NOT RECORDED: {wall_metric}",
                "No wall-time measurement was supplied. No speedup, throughput or",
                "cost ratio is inferred from the quality panel alone.",
            ],
            color="#7A0000",
        )
        warnings.append(f"NOT RECORDED: {wall_metric} (no speedup may be stated)")

    n_missing, n_failed = _validity_counts(rows)
    spec = FigureSpec(
        figure_id="C11",
        title="Quality versus training exposure and measured cost",
        question=C11_QUESTION,
        x_label="training exposure (recorded x kind) and method (categorical)",
        y_label="recorded quality metric and measured wall time (s)",
        metric_definition=(
            "quality is the recorded evaluation metric at a recorded training exposure; "
            "wall time is a recorded measurement, never derived from step counts"
        ),
        data_provenance=_provenance_for(rows, kind="cost_records"),
        selection_rule="all supplied cost rows; no run excluded for being slow",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded per row")),
        statistical_unit="independent training replicate (fit)",
        n_fits=len({str(getattr(r, "training_replicate_id", None) or "unlabelled") for r in rows}),
        n_missing=n_missing,
        n_failed=n_failed,
        uncertainty_method="none: measured values are drawn per fit without a summary interval",
        caption=(
            "Shows recorded quality against recorded training exposure and, where it was "
            "measured, wall time per fit. Hardware, configuration and contention are not "
            "controlled here and are not recorded per row unless the hardware note says so, "
            "so no speedup or efficiency ratio is stated. Does not demonstrate that one "
            "method is cheaper to train."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C12 - Are training mechanics behaving as expected?
# --------------------------------------------------------------------------------------

C12_QUESTION = "Are training mechanics behaving as expected?"


def c12_training_mechanics(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Small multiples of the recorded training diagnostics, with invalid-sample markers.

    Restriction enforced here: only recorded diagnostic rows are drawn. Nothing is
    recomputed, no extra forward pass is run, and an invalid or non-finite sample is drawn
    as a marker at the panel floor whose y position is explicitly declared not to be a
    value.
    """

    opts = dict(options or {})
    title = "C12 Training mechanics"
    rows = _as_sequence(inputs.get("training_diagnostics"))
    if not rows:
        return _missing(
            "C12",
            title,
            "training_diagnostics (recorded loss/entropy/KL/clip/value-error rows)",
            question=C12_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
            detail=(
                "Diagnostics are plotted only from what training recorded. This panel does\n"
                "not run extra forward passes or recompute a loss to fill itself.",
            )[0],
        )

    metric_names = sorted(
        {str(getattr(r, "metric_name", "unknown")) for r in rows if getattr(r, "metric_name", None)}
    )
    flag_names = [
        name
        for name in metric_names
        if name.endswith("_flag") or name in set(opts.get("flag_metrics", ()))
    ]
    curve_names = [name for name in metric_names if name not in flag_names]
    panels = curve_names + flag_names
    n_panels = max(1, min(len(panels), int(opts.get("max_panels", 9))))
    n_cols = 3 if n_panels > 2 else n_panels
    n_rows_grid = int(math.ceil(n_panels / n_cols))
    fig, axes = new_figure(
        figsize=(4.2 * n_cols, 3.0 * n_rows_grid + 0.6), nrows=n_rows_grid, ncols=n_cols
    )
    axes_list = np.atleast_1d(np.asarray(axes, dtype=object)).ravel().tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []
    if len(panels) > n_panels:
        warnings.append(
            f"{len(panels) - n_panels} recorded diagnostic(s) are not drawn because the panel "
            "limit was reached: " + ", ".join(panels[n_panels:])
        )

    for index, name in enumerate(panels[:n_panels]):
        ax = axes_list[index]
        metric_rows = _metric_rows(rows, metric_name=name)
        unit = _record_unit(metric_rows, fallback="dimensionless")
        points = sorted(
            (
                (float(getattr(r, "x_value", 0.0) or 0.0), measured_value(getattr(r, "value", None)), r)
                for r in metric_rows
                if getattr(r, "x_value", None) is not None
            ),
            key=lambda item: item[0],
        )
        xs = [p[0] for p in points if p[1] is not None]
        ys = [p[1] for p in points if p[1] is not None]
        if name in flag_names:
            ax.plot(xs, ys, linestyle="none", marker="|", markersize=12.0, color="#7A0000")
        elif xs:
            ax.plot(xs, ys, color="#0072B2", linewidth=1.5, marker="o", markersize=3.0)
        for x_value, y_value, row in points:
            table.append(
                {
                    "role": "diagnostic_sample",
                    "metric_name": name,
                    "x_value": x_value,
                    "x_kind": getattr(getattr(row, "x_kind", None), "value", ""),
                    "value": y_value,
                    "unit": unit,
                    "status": measured_status(getattr(row, "value", None)),
                    "training_replicate_id": getattr(row, "training_replicate_id", None),
                }
            )
        invalid_x = [p[0] for p in points if p[1] is None]
        if invalid_x:
            floor = ax.get_ylim()[0] if ys else 0.0
            ax.plot(
                invalid_x,
                np.full(len(invalid_x), floor),
                linestyle="none",
                marker="x",
                markersize=8.0,
                color="#7A0000",
                label="invalid / NaN (marker position is not a value)",
            )
            for x_value in invalid_x:
                table.append(
                    {
                        "role": "invalid_marker",
                        "metric_name": name,
                        "x_value": x_value,
                        "value": None,
                        "plotted_y": float(floor),
                        "status": "marker position is not a measurement",
                    }
                )
            warnings.append(f"{name}: {len(invalid_x)} invalid or non-finite sample(s) marked")
        finish_axes(
            ax,
            title=f"{name} ({unit})",
            x_label="recorded training x value",
            y_label=_axis_label(name, unit),
            legend=bool(invalid_x),
        )
    for ax in axes_list[n_panels:]:
        ax.axis("off")

    n_missing, n_failed = _validity_counts(rows)
    spec = FigureSpec(
        figure_id="C12",
        title="Recorded training diagnostics",
        question=C12_QUESTION,
        x_label="recorded training x value (per panel)",
        y_label="recorded diagnostic value (per panel unit)",
        metric_definition=(
            "each panel is one diagnostic exactly as the training process recorded it; no "
            "loss, gradient or entropy is recomputed here and no additional forward pass is "
            "performed"
        ),
        data_provenance=_provenance_for(rows, kind="training_diagnostics"),
        selection_rule="all supplied diagnostic rows, in recorded x order",
        checkpoint_rule="not applicable: these are training-time records, not checkpoints",
        statistical_unit="one training process (diagnostics are within-run, not cross-fit evidence)",
        n_fits=len({str(getattr(r, "training_replicate_id", None) or "unlabelled") for r in rows}),
        n_missing=n_missing,
        n_failed=n_failed,
        uncertainty_method="none: raw recorded diagnostics",
        caption=(
            "Shows what the training process recorded about its own mechanics. These are "
            "within-run diagnostics: a well-behaved loss curve is not evidence of a better "
            "policy, and a marker for an invalid sample sits at the panel floor purely to be "
            "visible - its height is not a measurement. Does not demonstrate learning "
            "quality or generalisation."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C13 - Are policies using comparable information?
# --------------------------------------------------------------------------------------

C13_QUESTION = "Are policies using comparable information?"


def c13_information_comparability(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Recorded information-age and missingness curves with a condition table.

    Restriction enforced here: the information condition is read from the recorded
    condition table; equal observation dimensionality is never treated as evidence of
    equal information rights, and the caption says so.
    """

    opts = dict(options or {})
    title = "C13 Information comparability"
    rows = _as_sequence(inputs.get("information_records"))
    conditions = inputs.get("information_conditions") or {}
    if not rows and not conditions:
        return _missing(
            "C13",
            title,
            "information_records and information_conditions (age/missingness and declared conditions)",
            question=C13_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    fig, axes = new_figure(figsize=(11.5, 5.8), ncols=2)
    ax_curves, ax_table = axes.tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    if rows:
        metric_names = sorted({str(getattr(r, "metric_name", "unknown")) for r in rows})
        series_labels = [
            f"{getattr(r, 'method_id', 'unknown')} / {getattr(r, 'metric_name', 'unknown')}"
            for r in rows
        ]
        styles = apply_method_style(None, sorted(set(series_labels)))
        for label in sorted(set(series_labels)):
            method_id, metric_name = label.split(" / ", 1)
            points = sorted(
                (
                    (float(getattr(r, "x_value", 0.0) or 0.0), measured_value(getattr(r, "value", None)), r)
                    for r in rows
                    if str(getattr(r, "method_id", "unknown")) == method_id
                    and str(getattr(r, "metric_name", "unknown")) == metric_name
                    and getattr(r, "x_value", None) is not None
                ),
                key=lambda item: item[0],
            )
            style = styles[label]
            xs = [p[0] for p in points if p[1] is not None]
            ys = [p[1] for p in points if p[1] is not None]
            unit = _record_unit([p[2] for p in points], fallback="s or fraction")
            if xs:
                ax_curves.plot(
                    xs, ys, color=style["color"], linestyle=style["linestyle"], marker=style["marker"],
                    markersize=4.0, linewidth=1.5, label=f"{label} ({unit})"
                )
            for x_value, y_value, row in points:
                table.append(
                    {
                        "role": "information_sample",
                        "method_id": method_id,
                        "metric_name": metric_name,
                        "x_value": x_value,
                        "value": y_value,
                        "unit": unit,
                        "status": measured_status(getattr(row, "value", None)),
                    }
                )
        finish_axes(
            ax_curves,
            title="Recorded observation age (s) and missingness (fraction)",
            x_label="recorded x value (time or step)",
            y_label="age (s) / missing fraction (dimensionless)",
            legend=True,
        )
    else:
        _text_panel(
            ax_curves,
            "Information age and missingness",
            [
                "NOT RECORDED: information_records",
                "Only the declared condition table is available; no age or missingness",
                "curve is drawn, and none is inferred from observation shapes.",
            ],
            color="#7A0000",
        )
        warnings.append("NOT RECORDED: information_records")

    if conditions:
        condition_rows: list[list[str]] = []
        for method, condition in dict(conditions).items():
            if isinstance(condition, Mapping):
                for key, value in condition.items():
                    condition_rows.append([str(method), str(key), str(value)])
                    table.append(
                        {
                            "role": "information_condition",
                            "method_id": str(method),
                            "metric_name": str(key),
                            "condition_value": str(value),
                        }
                    )
            else:
                condition_rows.append([str(method), "condition", str(condition)])
                table.append(
                    {
                        "role": "information_condition",
                        "method_id": str(method),
                        "metric_name": "condition",
                        "condition_value": str(condition),
                    }
                )
        _table_panel(ax_table, "Declared information conditions", ["method", "field", "value"], condition_rows)
    else:
        _text_panel(
            ax_table,
            "Declared information conditions",
            [
                "NOT RECORDED: information_conditions",
                "Without a declared condition table, comparability cannot be asserted.",
            ],
            color="#7A0000",
        )
        warnings.append("NOT RECORDED: information_conditions")

    n_missing, n_failed = _validity_counts(rows)
    spec = FigureSpec(
        figure_id="C13",
        title="Information age, missingness and declared conditions",
        question=C13_QUESTION,
        x_label="recorded x value (time or step)",
        y_label="age (s) / missing fraction (dimensionless)",
        metric_definition=(
            "observation age is the recorded delay between a measurement and the decision "
            "that used it; missingness is the recorded fraction of masked fields. Both come "
            "from the policy-facing store, not from privileged truth."
        ),
        data_provenance=_provenance_for(rows, kind="information_records")
        + [provenance_entry(None, dict(conditions), kind="information_conditions")],
        selection_rule="all supplied information rows and declared conditions",
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded")),
        statistical_unit="one recorded run per method",
        n_missing=n_missing,
        n_failed=n_failed,
        uncertainty_method="none: recorded values are drawn as recorded",
        caption=(
            "Shows the recorded information age and missingness alongside each method's "
            "declared information condition. Two policies with equal observation dimensions "
            "can still have different information rights, so the declared condition table - "
            "not the vector shape - is the evidence here. Does not demonstrate that a "
            "comparison is fair; it shows what would have to be argued."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# C14 - Where does one policy outperform another?
# --------------------------------------------------------------------------------------

C14_QUESTION = "Where does one policy outperform another?"


def c14_shared_world_difference(
    inputs: Mapping[str, Any],
    output_dir: Path,
    *,
    options: Mapping[str, Any] | None = None,
) -> FigureResult:
    """Per-world differences on shared worlds, with unmatched and non-comparable rows shown.

    Restrictions enforced here: a world present for only one method is listed as unmatched
    and is never drawn as a zero difference; a metric whose two sides carry different units
    is declared non-comparable and no difference is computed for it; and the caption
    declares no winner.
    """

    opts = dict(options or {})
    title = "C14 Shared-world difference"
    rows = _as_sequence(inputs.get("world_differences"))
    if not rows:
        return _missing(
            "C14",
            title,
            "world_differences (per-world metric rows for two methods on shared worlds)",
            question=C14_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    methods = _distinct(str(getattr(r, "method_id", "unknown")) for r in rows)
    method_a = str(opts.get("method_a", inputs.get("method_a", methods[0] if methods else "")))
    method_b = str(
        opts.get(
            "method_b",
            inputs.get("method_b", methods[1] if len(methods) > 1 else ""),
        )
    )
    if not method_a or not method_b or method_a == method_b:
        return _missing(
            "C14",
            title,
            "world_differences rows for two distinct method_id values",
            question=C14_QUESTION,
            output_dir=output_dir,
            options=opts,
            inputs=inputs,
        )

    metric_name = str(
        opts.get("metric_name")
        or (_distinct(getattr(r, "metric_name", None) for r in rows) or ["unknown"])[0]
    )
    rows = _metric_rows(rows, metric_name=metric_name)
    rows_a = _metric_rows(rows, method_id=method_a)
    rows_b = _metric_rows(rows, method_id=method_b)
    unit_a = _record_unit(rows_a)
    unit_b = _record_unit(rows_b)
    comparable = unit_a == unit_b and not unit_a.startswith("MIXED")

    fig, axes = new_figure(figsize=(12.0, 6.0), ncols=2, width_ratios=(3.0, 2.2))
    ax_diff, ax_table = axes.tolist()
    table: list[dict[str, Any]] = []
    warnings: list[str] = []

    def _by_world(method_rows: Sequence[Any]) -> dict[str, list[Any]]:
        out: dict[str, list[Any]] = {}
        for row in method_rows:
            out.setdefault(str(getattr(row, "world_id", None) or "unlabelled"), []).append(row)
        return out

    worlds_a = _by_world(rows_a)
    worlds_b = _by_world(rows_b)
    matched = sorted(set(worlds_a) & set(worlds_b))
    unmatched_a = sorted(set(worlds_a) - set(worlds_b))
    unmatched_b = sorted(set(worlds_b) - set(worlds_a))
    incomplete = 0

    if not comparable:
        warnings.append(
            f"non-comparable metric units: {method_a} reports '{unit_a}' and {method_b} "
            f"reports '{unit_b}'; no difference is computed"
        )
        _text_panel(
            ax_diff,
            f"Per-world difference: {metric_name}",
            [
                "NOT COMPARABLE: the two methods report different units for this metric.",
                f"  {method_a}: {unit_a}",
                f"  {method_b}: {unit_b}",
                "A difference between different units would be meaningless, so none is drawn.",
            ],
            color="#7A0000",
        )
    else:
        drawn_x: list[int] = []
        for index, world in enumerate(matched):
            value_a = next(
                (measured_value(getattr(r, "value", None)) for r in worlds_a[world]), None
            )
            value_b = next(
                (measured_value(getattr(r, "value", None)) for r in worlds_b[world]), None
            )
            if value_a is None or value_b is None:
                incomplete += 1
                table.append(
                    {
                        "role": "world_difference",
                        "world_id": world,
                        "value_a": value_a,
                        "value_b": value_b,
                        "difference": None,
                        "unit": unit_a,
                        "status": "incomplete_pair",
                    }
                )
                ax_diff.plot(
                    [index],
                    [0.0],
                    linestyle="none",
                    marker="x",
                    markersize=9.0,
                    color="#7A0000",
                    label="incomplete pair (no difference; marker is not a value)"
                    if incomplete == 1
                    else None,
                )
                continue
            difference = value_a - value_b
            drawn_x.append(index)
            ax_diff.plot(
                [index],
                [difference],
                linestyle="none",
                marker="o",
                markersize=8.0,
                markerfacecolor="#0072B2",
                markeredgecolor="black",
                label=f"{method_a} minus {method_b}" if index == matched.index(matched[0]) else None,
            )
            table.append(
                {
                    "role": "world_difference",
                    "world_id": world,
                    "value_a": value_a,
                    "value_b": value_b,
                    "difference": difference,
                    "unit": unit_a,
                    "status": "matched",
                }
            )
        ax_diff.axhline(0.0, color="#555555", linestyle=(0, (4, 3)), linewidth=1.2)
        table.append({"role": "reference_line", "world_id": "", "difference": 0.0, "unit": unit_a,
                      "status": "no difference"})
        ax_diff.set_xticks(range(len(matched)))
        ax_diff.set_xticklabels(
            [_short_label(world) for world in matched],
            rotation=30,
            ha="right",
            fontsize=ANNOTATION_FONT_SIZE,
        )
        if any(len(str(world)) > 28 for world in matched):
            warnings.append(
                "world identities are shortened in the tick labels for readability; the "
                "full recorded identity of every point is in the exported table"
            )
        if unmatched_a or unmatched_b:
            ax_diff.text(
                0.02,
                0.02,
                f"unmatched worlds ({method_a}): " + (", ".join(unmatched_a) or "none") + "\n"
                f"unmatched worlds ({method_b}): " + (", ".join(unmatched_b) or "none") + "\n"
                "(listed, never drawn as a zero difference)",
                transform=ax_diff.transAxes,
                fontsize=ANNOTATION_FONT_SIZE,
                color="#7A0000",
            )
        finish_axes(
            ax_diff,
            title=f"Per-world difference on shared worlds: {metric_name} ({unit_a})",
            x_label="shared world identity (categorical)",
            y_label=_axis_label(f"{method_a} minus {method_b}", unit_a),
            legend=True,
        )

    for world in unmatched_a:
        table.append({"role": "unmatched_world", "world_id": world, "status": f"only in {method_a}"})
    for world in unmatched_b:
        table.append({"role": "unmatched_world", "world_id": world, "status": f"only in {method_b}"})
    for name in _as_sequence(inputs.get("non_comparable_metrics")):
        table.append({"role": "non_comparable_metric", "world_id": "", "status": str(name)})

    stats = _load_statistics(opts)
    pairing_evidence = inputs.get("pairing_evidence")
    effect_rows: list[list[str]] = [
        ["metric", metric_name],
        ["unit (A)", unit_a],
        ["unit (B)", unit_b],
        ["matched worlds", str(len(matched))],
        ["incomplete pairs", str(incomplete)],
        [f"unmatched ({method_a})", str(len(unmatched_a))],
        [f"unmatched ({method_b})", str(len(unmatched_b))],
    ]
    uncertainty = "unavailable (no paired interval computed)"
    if comparable and stats is not None and pairing_evidence is not None:
        aggregation_a, _, notes_a = _reduce_units(
            stats, rows_a, metric_name=metric_name, unit_field=str(opts.get("unit_field", "world_id"))
        )
        aggregation_b, _, notes_b = _reduce_units(
            stats, rows_b, metric_name=metric_name, unit_field=str(opts.get("unit_field", "world_id"))
        )
        for note in notes_a + notes_b:
            if note not in warnings:
                warnings.append(note)
        try:
            paired = stats.paired_difference(
                aggregation_a,
                aggregation_b,
                pairing_evidence=pairing_evidence,
                ci_method=str(opts.get("ci_method", "student_t")),
                ci_level=float(opts.get("ci_level", 0.95)),
                rng_seed=opts.get("rng_seed"),
            )
        except Exception as error:
            paired = None
            warnings.append(f"paired_difference failed: {type(error).__name__}: {error}")
        if paired is not None:
            point = measured_value(getattr(paired, "point", None))
            effect_rows.append(["pairing status", str(getattr(paired, "pairing_status", "unknown"))])
            effect_rows.append(["paired n", str(getattr(paired, "n_pairs", "unknown"))])
            effect_rows.append(
                ["paired difference", "unavailable" if point is None else f"{point:.6g} {unit_a}"]
            )
            low = measured_value(getattr(paired, "ci_low", None))
            high = measured_value(getattr(paired, "ci_high", None))
            if _interval_is_drawable(paired, int(getattr(paired, "n_pairs", 0) or 0)):
                effect_rows.append(
                    ["paired interval", f"[{low:.6g}, {high:.6g}] {unit_a}"]
                )
                uncertainty = _uncertainty_label(
                    paired, int(getattr(paired, "n_pairs", 0) or 0), unit_kind="pair"
                )
            else:
                effect_rows.append(["paired interval", "unavailable (not a zero-width interval)"])
            table.append(
                {
                    "role": "paired_effect",
                    "world_id": "",
                    "difference": point,
                    "unit": unit_a,
                    "status": str(getattr(paired, "pairing_status", "unknown")),
                }
            )
    elif comparable:
        effect_rows.append(
            ["paired effect", "not computed (pairing evidence or statistics module absent)"]
        )
        warnings.append(
            "no paired effect is reported: pairing must be verified by the statistics module"
        )
    _table_panel(ax_table, "Effect and comparability table", ["field", "value"], effect_rows)

    n_missing, n_failed = _validity_counts(rows)
    spec = FigureSpec(
        figure_id="C14",
        title="Shared-world difference between two methods",
        question=C14_QUESTION,
        x_label="shared world identity (categorical)",
        y_label=_axis_label(f"{method_a} minus {method_b}", unit_a),
        metric_definition=(
            f"per-world difference of {metric_name} between {method_a} and {method_b} on the "
            "same recorded world identity, retaining the original sign and unit; no "
            "improvement-oriented transformation is applied"
        ),
        data_provenance=_provenance_for(rows, kind="world_difference_rows"),
        selection_rule=(
            "worlds present for both methods are differenced; worlds present for only one "
            "method are listed as unmatched and never drawn as zero"
        ),
        checkpoint_rule=str(opts.get("checkpoint_rule", "as recorded per row")),
        statistical_unit=str(opts.get("statistical_unit", "shared world (matched block)")),
        n_missing=n_missing + incomplete,
        n_failed=n_failed,
        uncertainty_method=uncertainty,
        caption=(
            "Each dot is one shared world's difference, with its original sign and unit. "
            "Unmatched worlds and incomplete pairs are listed rather than imputed, and a "
            "metric whose two sides use different units is refused rather than differenced. "
            "No winner is declared here: a positive mean difference on these worlds is not a "
            "general ranking, and this figure does not establish a cause for any gap."
        ),
        synthetic_banner=synthetic_banner_for(inputs, opts),
        warnings=warnings,
    )
    return _finalize(fig, spec, table, output_dir, opts)


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ChartEntry:
    """One chart's identity, question and input contract.

    ``required_inputs`` is documentation and report bookkeeping, not the gate: each chart
    re-checks its own contract and returns a named missing panel, so a chart called
    directly behaves the same way as one called through the report.
    """

    figure_id: str
    function: Callable[..., FigureResult]
    question: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()
    suite: str = "capability"
    title: str = ""


CHART_REGISTRY: dict[str, ChartEntry] = {
    entry.figure_id: entry
    for entry in (
        ChartEntry(
            figure_id="C01",
            function=c01_learning_curves,
            question=C01_QUESTION,
            required_inputs=("evaluation_curve",),
            optional_inputs=("training_reward",),
            title="Evaluation learning curves with per-fit detail",
        ),
        ChartEntry(
            figure_id="C02",
            function=c02_per_fit_consistency,
            question=C02_QUESTION,
            required_inputs=("fit_endpoints",),
            optional_inputs=("baseline_fit_endpoints", "pairing_evidence", "fit_status"),
            title="Per-fit endpoint consistency",
        ),
        ChartEntry(
            figure_id="C03",
            function=c03_event_aligned_service,
            question=C03_QUESTION,
            required_inputs=("service_timeseries",),
            optional_inputs=("world_events", "healthy_reference", "failed_ground_reference"),
            title="Event-aligned offered, delivered and unmet service",
        ),
        ChartEntry(
            figure_id="C04",
            function=c04_recovery_times,
            question=C04_QUESTION,
            required_inputs=("recovery_outcomes",),
            optional_inputs=("recovery_deadline_s",),
            title="Per-episode time to recovery with censoring",
        ),
        ChartEntry(
            figure_id="C05",
            function=c05_capacity_bottleneck,
            question=C05_QUESTION,
            required_inputs=("link_frames",),
            optional_inputs=("unmet_traffic",),
            title="Link and resource-domain utilization with unmet traffic",
        ),
        ChartEntry(
            figure_id="C06",
            function=c06_spatial_service,
            question=C06_QUESTION,
            required_inputs=("ground_entities",),
            optional_inputs=("geometry",),
            title="Spatial offered, delivered and unmet demand",
        ),
        ChartEntry(
            figure_id="C07",
            function=c07_controller_behaviour,
            question=C07_QUESTION,
            required_inputs=("uav_frames",),
            optional_inputs=(),
            title="Controller behaviour: trajectories, kinematics and executed action",
        ),
        ChartEntry(
            figure_id="C08",
            function=c08_skill_organization,
            question=C08_QUESTION,
            required_inputs=("skill_segments",),
            optional_inputs=("skill_events",),
            title="Temporal organization of the skill hierarchy",
        ),
        ChartEntry(
            figure_id="C09",
            function=c09_roster_changes,
            question=C09_QUESTION,
            required_inputs=("membership_intervals",),
            optional_inputs=("episode_performance", "mask_diagnostics"),
            title="Roster membership and continuing-agent performance",
        ),
        ChartEntry(
            figure_id="C10",
            function=c10_robustness_sweep,
            question=C10_QUESTION,
            required_inputs=("sweep_records",),
            optional_inputs=("factor_name", "factor_unit"),
            title="Robustness across a predeclared factor",
        ),
        ChartEntry(
            figure_id="C11",
            function=c11_computational_transparency,
            question=C11_QUESTION,
            required_inputs=("cost_records",),
            optional_inputs=("quality_metric", "wall_time_metric", "hardware_note"),
            title="Quality versus training exposure and measured cost",
        ),
        ChartEntry(
            figure_id="C12",
            function=c12_training_mechanics,
            question=C12_QUESTION,
            required_inputs=("training_diagnostics",),
            optional_inputs=(),
            title="Recorded training diagnostics",
        ),
        ChartEntry(
            figure_id="C13",
            function=c13_information_comparability,
            question=C13_QUESTION,
            required_inputs=("information_records",),
            optional_inputs=("information_conditions",),
            title="Information age, missingness and declared conditions",
        ),
        ChartEntry(
            figure_id="C14",
            function=c14_shared_world_difference,
            question=C14_QUESTION,
            required_inputs=("world_differences",),
            optional_inputs=("pairing_evidence", "method_a", "method_b", "non_comparable_metrics"),
            title="Shared-world difference between two methods",
        ),
    )
}


#: Charts required by the plan's mandatory first working report (Section 7.1).
FIRST_REPORT_CHARTS: tuple[str, ...] = ("C02", "C03", "C04", "C05", "C06", "C07", "C14")


def suite_chart_ids(suite: str = "capability") -> tuple[str, ...]:
    """Chart identifiers of one suite, in identifier order."""

    return tuple(
        sorted(entry.figure_id for entry in CHART_REGISTRY.values() if entry.suite == suite)
    )


__all__ = [
    "CHART_REGISTRY",
    "FIRST_REPORT_CHARTS",
    "ChartEntry",
    "c01_learning_curves",
    "c02_per_fit_consistency",
    "c03_event_aligned_service",
    "c04_recovery_times",
    "c05_capacity_bottleneck",
    "c06_spatial_service",
    "c07_controller_behaviour",
    "c08_skill_organization",
    "c09_roster_changes",
    "c10_robustness_sweep",
    "c11_computational_transparency",
    "c12_training_mechanics",
    "c13_information_comparability",
    "c14_shared_world_difference",
    "suite_chart_ids",
]
