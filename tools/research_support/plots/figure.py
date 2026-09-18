"""The figure contract: a scientific figure is a bundle, never a bare image.

A PNG on its own cannot be audited. Six months later nobody can tell which runs it
summarised, whether the band is fit variability or episode variability, how many fits
failed before the plot was drawn, or whether the curve was smoothed with a window that
peeked into the future. This module therefore defines what every figure in the suite
ships with:

* :class:`FigureSpec` - machine-readable provenance written next to the image. It names
  the research question, the metric definition, the selection and checkpoint rules, the
  independent statistical unit, the sample counts, the missing/failed counts, the
  smoothing and alignment operations, the uncertainty method and the software versions.
* :class:`FigureResult` - the spec plus *the exact points that were drawn*. The table is
  not a convenience export: a drawn artist that is absent from the table is a figure the
  reader cannot check, so every chart in the suite adds a row for everything it draws,
  including intervals and reference lines.
* :func:`missing_panel` - the honest hole. When an input contract is unsatisfied the
  suite draws a labelled panel that names the absent record. It never substitutes a
  different metric, and it never silently drops the panel from the report.

Backend policy: this is the rendering module, so it selects the non-interactive ``Agg``
backend here and nowhere else. A shared training import must never choose a backend for
the process that imports it. Figures are built from :class:`matplotlib.figure.Figure`
directly rather than through ``pyplot``, so no global figure registry, no GUI event loop
and no ``show()`` is involved, and an exporting worker cannot leak windows.
"""

from __future__ import annotations

import csv
import importlib
import math
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib
import numpy as np

# --------------------------------------------------------------------------------------
# Backend selection (rendering module only)
# --------------------------------------------------------------------------------------

#: Backends that render to a file without a window manager or an event loop.
_NON_INTERACTIVE_BACKENDS = frozenset({"agg", "pdf", "svg", "ps", "pgf", "cairo", "template"})


def ensure_agg_backend() -> str:
    """Select ``Agg`` unless a non-interactive backend was already chosen.

    The guard matters in two directions. A process that already selected ``pdf`` or
    ``svg`` (for example a document build) keeps its choice, because re-selecting would
    discard an equivalent, deliberately configured backend. A process that merely
    inherited the interactive default (``TkAgg`` on this host) is switched, because a
    report worker or a test must not open a GUI toolkit.
    """

    current = matplotlib.get_backend()
    if current.strip().lower() in _NON_INTERACTIVE_BACKENDS:
        return current
    matplotlib.use("Agg", force=True)
    return matplotlib.get_backend()


ensure_agg_backend()

from matplotlib.axes import Axes  # noqa: E402  (import after backend selection)
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from .. import records  # noqa: E402
from ..records import Measured, Validity  # noqa: E402

# --------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------

#: Stamped on every figure drawn from constructed fixture data. The exact string is part
#: of the contract: a reader scanning a report must be able to grep for it.
DEFAULT_SYNTHETIC_BANNER = "SYNTHETIC ENGINEERING FIXTURE - NOT AN ALGORITHM RESULT"

#: Prefix of the text drawn on a missing panel and of :attr:`FigureResult.missing_reason`.
MISSING_PREFIX = "NOT RECORDED: "

#: Minimum readable size at the default figure size, per the figure contract.
TICK_FONT_SIZE = 9.0
LABEL_FONT_SIZE = 10.0
TITLE_FONT_SIZE = 12.0
LEGEND_FONT_SIZE = 9.0
ANNOTATION_FONT_SIZE = 9.0

DEFAULT_FIGSIZE = (9.0, 5.5)
DEFAULT_DPI = 160

#: Okabe-Ito colour-blind safe palette. Red and green never carry meaning on their own:
#: every series also gets a distinct marker and a distinct dash pattern.
METHOD_COLORS: tuple[str, ...] = (
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#D55E00",  # vermillion
    "#8C8C8C",  # grey
    "#000000",  # black
)
METHOD_MARKERS: tuple[str, ...] = ("o", "s", "^", "D", "v", "P", "X", "*")
METHOD_LINESTYLES: tuple[Any, ...] = (
    "-",
    (0, (6, 2)),
    (0, (2, 2)),
    (0, (6, 2, 1, 2)),
    (0, (1, 1.6)),
    (0, (8, 2, 1, 2, 1, 2)),
    (0, (4, 1, 4, 3)),
    (0, (10, 3)),
)
#: High-contrast variant: greyscale-safe, heavier strokes, same marker/dash separation.
HIGH_CONTRAST_COLORS: tuple[str, ...] = (
    "#000000",
    "#4D4D4D",
    "#767676",
    "#1B1B1B",
    "#5A5A5A",
    "#2E2E2E",
    "#8A8A8A",
    "#000000",
)


# --------------------------------------------------------------------------------------
# Software versions and provenance
# --------------------------------------------------------------------------------------


def software_versions() -> dict[str, str]:
    """Versions actually importable in this interpreter, not a requirements pin.

    A figure specification that repeats a pinned requirement file can be wrong; this
    reports what the process really used, and says ``not installed`` for a package that
    is absent rather than omitting the key.
    """

    versions: dict[str, str] = {
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()}",
    }
    for name in ("numpy", "matplotlib", "scipy", "pandas"):
        try:
            module = importlib.import_module(name)
        except Exception:  # pragma: no cover - depends on the environment
            versions[name] = "not installed"
            continue
        versions[name] = str(getattr(module, "__version__", "unknown"))
    versions["matplotlib_backend"] = matplotlib.get_backend()
    versions["records_schema"] = records.METRIC_SCHEMA
    return versions


def provenance_entry(
    source_path: str | Path | None,
    payload: Any = None,
    *,
    kind: str = "record_set",
    n_rows: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """One row of :attr:`FigureSpec.data_provenance`: where it came from and its hash."""

    entry: dict[str, Any] = {
        "kind": kind,
        "source_path": None if source_path is None else str(source_path),
    }
    if payload is not None:
        try:
            entry["content_hash"] = records.content_hash(payload)
        except Exception as error:  # pragma: no cover - defensive
            entry["content_hash"] = None
            entry["hash_error"] = f"{type(error).__name__}: {error}"
    else:
        entry["content_hash"] = None
    if n_rows is not None:
        entry["n_rows"] = int(n_rows)
    if note:
        entry["note"] = note
    return entry


# --------------------------------------------------------------------------------------
# Figure specification and result
# --------------------------------------------------------------------------------------


@dataclass
class FigureSpec:
    """Machine-readable provenance of one figure. Written next to the image.

    Defaults exist only so a chart does not have to repeat inapplicable fields; every
    default is the *honest* value (nothing recorded, no smoothing, no interval), never a
    flattering one.
    """

    figure_id: str
    title: str
    question: str
    x_label: str
    y_label: str
    metric_definition: str
    data_provenance: list[dict[str, Any]] = field(default_factory=list)
    selection_rule: str = "not recorded"
    checkpoint_rule: str = "not recorded"
    statistical_unit: str = "not applicable"
    n_fits: int | None = None
    n_evaluation_episodes: int | None = None
    n_missing: int = 0
    n_failed: int = 0
    smoothing: dict[str, Any] | None = None
    alignment_rule: str | None = None
    uncertainty_method: str = "none drawn"
    random_seed: int | None = None
    software_versions: dict[str, str] = field(default_factory=software_versions)
    caption: str = ""
    synthetic_banner: str | None = None
    warnings: list[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def to_json(self) -> dict[str, Any]:
        return {
            "figure_id": self.figure_id,
            "title": self.title,
            "question": self.question,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "metric_definition": self.metric_definition,
            "data_provenance": [dict(entry) for entry in self.data_provenance],
            "selection_rule": self.selection_rule,
            "checkpoint_rule": self.checkpoint_rule,
            "statistical_unit": self.statistical_unit,
            "n_fits": None if self.n_fits is None else int(self.n_fits),
            "n_evaluation_episodes": (
                None if self.n_evaluation_episodes is None else int(self.n_evaluation_episodes)
            ),
            "n_missing": int(self.n_missing),
            "n_failed": int(self.n_failed),
            "smoothing": None if self.smoothing is None else dict(self.smoothing),
            "alignment_rule": self.alignment_rule,
            "uncertainty_method": self.uncertainty_method,
            "random_seed": None if self.random_seed is None else int(self.random_seed),
            "software_versions": dict(self.software_versions),
            "caption": self.caption,
            "synthetic_banner": self.synthetic_banner,
            "warnings": list(self.warnings),
        }


@dataclass
class FigureResult:
    """A figure plus the exact data behind it.

    ``table`` holds one row per drawn datum - including interval endpoints, reference
    lines and censoring markers - so a reader can reproduce the image from the CSV. A
    panel that could not be drawn carries ``rendered=False`` and a ``missing_reason``
    that names the absent record.
    """

    spec: FigureSpec
    table: list[dict[str, Any]]
    png_path: Path | None = None
    svg_path: Path | None = None
    pdf_path: Path | None = None
    spec_path: Path | None = None
    table_path: Path | None = None
    rendered: bool = True
    missing_reason: str | None = None
    #: Live figure, retained only when the caller asked to inspect it. Never serialised.
    figure: Any = field(default=None, repr=False, compare=False)

    @property
    def figure_id(self) -> str:
        return self.spec.figure_id

    def to_json(self) -> dict[str, Any]:
        return {
            "figure_id": self.spec.figure_id,
            "spec": self.spec.to_json(),
            "table": [dict(row) for row in self.table],
            "png_path": None if self.png_path is None else str(self.png_path),
            "svg_path": None if self.svg_path is None else str(self.svg_path),
            "pdf_path": None if self.pdf_path is None else str(self.pdf_path),
            "spec_path": None if self.spec_path is None else str(self.spec_path),
            "table_path": None if self.table_path is None else str(self.table_path),
            "rendered": bool(self.rendered),
            "missing_reason": self.missing_reason,
        }


# --------------------------------------------------------------------------------------
# Figure construction helpers
# --------------------------------------------------------------------------------------


def new_figure(
    *,
    figsize: tuple[float, float] = DEFAULT_FIGSIZE,
    dpi: int = DEFAULT_DPI,
    nrows: int = 1,
    ncols: int = 1,
    sharex: bool = False,
    height_ratios: Sequence[float] | None = None,
    width_ratios: Sequence[float] | None = None,
) -> tuple[Figure, Any]:
    """Create an independent Agg-backed figure without touching ``pyplot``'s registry.

    Returns the figure and either one :class:`~matplotlib.axes.Axes` or an array of them,
    matching ``pyplot.subplots`` closely enough to keep chart code ordinary.
    """

    figure = Figure(figsize=figsize, dpi=dpi, layout="constrained")
    FigureCanvasAgg(figure)
    gridspec_kw: dict[str, Any] = {}
    if height_ratios is not None:
        gridspec_kw["height_ratios"] = list(height_ratios)
    if width_ratios is not None:
        gridspec_kw["width_ratios"] = list(width_ratios)
    axes = figure.subplots(nrows=nrows, ncols=ncols, sharex=sharex, gridspec_kw=gridspec_kw)
    for ax in np.atleast_1d(np.asarray(axes, dtype=object)).ravel().tolist():
        ax.tick_params(labelsize=TICK_FONT_SIZE)
    return figure, axes


def finish_axes(
    ax: Axes,
    *,
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    legend: bool | None = None,
    legend_loc: str = "best",
    grid: bool = True,
) -> None:
    """Apply the readability part of the figure contract to one panel.

    ``legend=None`` means "draw a legend when more than one labelled series is present",
    which is the contract's rule; pass ``True`` to force one for a single annotated
    series (a reference line, for instance).
    """

    if title is not None:
        ax.set_title(title, fontsize=TITLE_FONT_SIZE)
    if x_label is not None:
        ax.set_xlabel(x_label, fontsize=LABEL_FONT_SIZE)
    if y_label is not None:
        ax.set_ylabel(y_label, fontsize=LABEL_FONT_SIZE)
    ax.tick_params(labelsize=TICK_FONT_SIZE)
    if grid:
        ax.grid(True, alpha=0.3, linewidth=0.6)
    handles, labels = ax.get_legend_handles_labels()
    if labels and (legend is True or (legend is None and len(labels) > 1)):
        ax.legend(fontsize=LEGEND_FONT_SIZE, loc=legend_loc, framealpha=0.9)


def close_figure(figure: Figure | None) -> None:
    """Release a figure.

    Figures are created directly, so there is no ``pyplot`` window to destroy; clearing
    drops the artists and the renderer cache. A figure that *was* created through
    ``pyplot`` by a caller is closed through ``pyplot`` so its registry entry goes too.
    """

    if figure is None:
        return
    number = getattr(figure, "number", None)
    if number is not None and "matplotlib.pyplot" in sys.modules:  # pragma: no cover
        try:
            sys.modules["matplotlib.pyplot"].close(figure)
        except Exception:
            pass
    try:
        figure.clear()
    except Exception:  # pragma: no cover - defensive
        pass


def apply_method_style(
    ax: Axes | None,
    methods: Sequence[str],
    *,
    high_contrast: bool = False,
) -> dict[str, dict[str, Any]]:
    """Assign each method a colour **and** a marker **and** a dash pattern.

    Colour alone fails for a colour-blind reader, a greyscale print and a projector, and
    a red/green "bad/good" encoding fails twice over. The returned mapping is what chart
    code passes to ``plot``/``scatter``; the axes prop cycle is set to the same sequence
    so an unstyled call cannot silently reuse another method's appearance.
    """

    colors = HIGH_CONTRAST_COLORS if high_contrast else METHOD_COLORS
    styles: dict[str, dict[str, Any]] = {}
    for index, method in enumerate(methods):
        slot = index % len(METHOD_MARKERS)
        styles[str(method)] = {
            "color": colors[index % len(colors)],
            "marker": METHOD_MARKERS[slot],
            "linestyle": METHOD_LINESTYLES[slot],
            "linewidth": 2.0 if high_contrast else 1.6,
            "markersize": 6.5 if high_contrast else 5.5,
            "markerfacecolor": "none" if high_contrast else colors[index % len(colors)],
            "markeredgewidth": 1.4,
        }
    if ax is not None and styles:
        try:
            from cycler import cycler

            ax.set_prop_cycle(
                cycler(color=[s["color"] for s in styles.values()])
                + cycler(marker=[s["marker"] for s in styles.values()])
                + cycler(linestyle=[s["linestyle"] for s in styles.values()])
            )
        except Exception:  # pragma: no cover - cycler ships with matplotlib
            pass
    return styles


def render_rgb_array(fig: Figure) -> "np.ndarray":
    """Render to an ``(H, W, 3)`` ``uint8`` array through the Agg canvas.

    Used by the export path and by any consumer that wants pixels without a file. The
    alpha channel is dropped deliberately: consumers of this suite (video writers, image
    diffs, browser payloads) expect three channels, and a silent four-channel array is a
    shape bug that surfaces far from here.
    """

    canvas = fig.canvas
    if not isinstance(canvas, FigureCanvasAgg):
        canvas = FigureCanvasAgg(fig)
    canvas.draw()
    rgba = np.asarray(canvas.buffer_rgba(), dtype=np.uint8)
    rgb = np.ascontiguousarray(rgba[..., :3])
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:  # pragma: no cover
        raise RuntimeError(f"unexpected render shape {rgb.shape} dtype {rgb.dtype}")
    return rgb


def stamp_banner(fig: Figure, banner: str) -> None:
    """Draw the provenance banner on the image itself, once.

    A banner only in the HTML is lost the moment somebody pastes the PNG into a slide,
    which is exactly when a fixture figure is most likely to be mistaken for a result.
    """

    if getattr(fig, "_research_support_banner", None) == banner:
        return
    fig.text(
        0.5,
        0.995,
        banner,
        ha="center",
        va="top",
        fontsize=ANNOTATION_FONT_SIZE + 1,
        fontweight="bold",
        color="#7A0000",
        bbox={"facecolor": "#FFE9B0", "edgecolor": "#7A0000", "boxstyle": "round,pad=0.25"},
    )
    fig._research_support_banner = banner  # type: ignore[attr-defined]


def trailing_mean(values: Sequence[float | None], window: int) -> list[float | None]:
    """Causal moving average: point ``i`` uses ``i-window+1 .. i`` only.

    Online monitoring must not display a curve that used samples the run had not produced
    yet, and a centred window does exactly that. Missing entries stay missing rather than
    being filled with a repeated last value.
    """

    if window <= 1:
        return [None if v is None else float(v) for v in values]
    out: list[float | None] = []
    for index in range(len(values)):
        window_values = [
            float(v) for v in values[max(0, index - window + 1) : index + 1] if v is not None
        ]
        out.append(float(np.mean(window_values)) if window_values else None)
    return out


def synthetic_banner_for(
    inputs: Mapping[str, Any] | None = None,
    options: Mapping[str, Any] | None = None,
) -> str | None:
    """Decide whether this figure must carry the fixture banner.

    Explicit ``synthetic_banner`` wins; otherwise a ``synthetic`` flag or a declared
    ``source_kind`` of ``synthetic_fixture`` selects the standard banner text.
    """

    for source in (options or {}, inputs or {}):
        if "synthetic_banner" in source:
            value = source["synthetic_banner"]
            return None if value is None else str(value)
    for source in (options or {}, inputs or {}):
        if source.get("synthetic"):
            return DEFAULT_SYNTHETIC_BANNER
        source_kind = source.get("source_kind")
        if source_kind is None:
            continue
        value = getattr(source_kind, "value", source_kind)
        if str(value) == records.SourceKind.SYNTHETIC_FIXTURE.value:
            return DEFAULT_SYNTHETIC_BANNER
    return None


# --------------------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------------------


def _csv_cell(value: Any) -> str:
    """Format one table cell so a reader can recover the plotted number exactly.

    ``repr`` of a float round-trips in Python, so ``float(cell) == drawn_value`` holds
    bit for bit; that identity is what the figure-fidelity test checks. An absent value
    is an empty cell, never a zero.
    """

    if value is None:
        return ""
    if isinstance(value, Measured):
        return "" if value.validity is not Validity.OK else _csv_cell(value.value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return "" if not math.isfinite(number) else repr(number)
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    if isinstance(value, (list, tuple)):
        return "|".join(_csv_cell(item) for item in value)
    return str(value)


def _table_fieldnames(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    names: list[str] = []
    for row in rows:
        for key in row:
            if key not in names:
                names.append(str(key))
    return names


def _unit_warnings(spec: FigureSpec) -> None:
    text = f"{spec.x_label} {spec.y_label} {spec.title}"
    if "(" not in text and "[" not in text:
        spec.add_warning("axis labels carry no unit marker; confirm the quantity is dimensionless")


def export_figure(
    fig: Figure,
    result: FigureResult,
    output_dir: Path | str,
    *,
    formats: Sequence[str] = ("png", "svg", "pdf"),
    dpi: int = DEFAULT_DPI,
    close: bool = True,
) -> FigureResult:
    """Write the whole bundle: images, specification JSON and the drawn-point table.

    PNG, SVG and PDF come from the *same* figure object that the tests exercised, through
    matplotlib's own writers - no document-generation framework is involved, so the PDF
    cannot drift from the tested image. The result is mutated in place and returned.
    """

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    figure_id = result.spec.figure_id

    if result.spec.synthetic_banner:
        stamp_banner(fig, result.spec.synthetic_banner)
    _unit_warnings(result.spec)

    for fmt in formats:
        target = directory / f"{figure_id}.{fmt}"
        fig.savefig(target, format=fmt, dpi=dpi, facecolor="white")
        setattr(result, f"{fmt}_path", target)

    spec_path = directory / f"{figure_id}_spec.json"
    spec_path.write_text(records.dumps(result.spec.to_json(), indent=2), encoding="utf-8")
    result.spec_path = spec_path

    table_csv = directory / f"{figure_id}_table.csv"
    fieldnames = _table_fieldnames(result.table)
    with table_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or ["note"], restval="")
        writer.writeheader()
        for row in result.table:
            writer.writerow({key: _csv_cell(row.get(key)) for key in fieldnames})
    result.table_path = table_csv

    table_json = directory / f"{figure_id}_table.json"
    table_json.write_text(records.dumps(result.table, indent=2), encoding="utf-8")

    if close:
        close_figure(fig)
        result.figure = None
    else:
        result.figure = fig
    return result


def read_table_csv(path: Path | str) -> list[dict[str, str]]:
    """Read back a ``_table.csv`` exactly as written (helper for round-trip checks)."""

    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


# --------------------------------------------------------------------------------------
# Missing panel
# --------------------------------------------------------------------------------------


def build_missing_figure(
    figure_id: str,
    title: str,
    missing_record: str,
    *,
    question: str = "",
    detail: str = "",
) -> tuple[Figure, FigureSpec]:
    """Build the labelled hole: a real figure that names the record that is absent."""

    fig, ax = new_figure(figsize=(7.5, 4.2))
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_linestyle((0, (4, 3)))
        spine.set_linewidth(1.6)
        spine.set_color("#7A0000")
    ax.set_title(f"{figure_id} - {title}", fontsize=TITLE_FONT_SIZE)
    ax.text(
        0.5,
        0.60,
        f"{MISSING_PREFIX}{missing_record}",
        ha="center",
        va="center",
        fontsize=13.0,
        fontweight="bold",
        color="#7A0000",
        wrap=True,
    )
    ax.text(
        0.5,
        0.36,
        detail
        or "This panel is intentionally empty. No substitute metric is shown,\n"
        "because a different quantity would not answer this question.",
        ha="center",
        va="center",
        fontsize=ANNOTATION_FONT_SIZE,
        color="#333333",
    )
    if question:
        ax.text(
            0.5,
            0.15,
            f"Question: {question}",
            ha="center",
            va="center",
            fontsize=ANNOTATION_FONT_SIZE,
            style="italic",
            color="#333333",
        )
    spec = FigureSpec(
        figure_id=figure_id,
        title=title,
        question=question,
        x_label="not applicable (missing panel)",
        y_label="not applicable (missing panel)",
        metric_definition=f"unavailable: {missing_record} was not recorded",
        selection_rule="no rows selected; the required record is absent",
        checkpoint_rule="not applicable",
        statistical_unit="not applicable",
        n_missing=1,
        uncertainty_method="unavailable (no data)",
        caption=(
            f"Panel not drawn. The required record '{missing_record}' is absent from the "
            "supplied inputs. This demonstrates nothing about the algorithm; it records "
            "that the evidence was not captured."
        ),
        warnings=[f"{MISSING_PREFIX}{missing_record}"],
    )
    return fig, spec


def missing_panel(
    figure_id: str,
    title: str,
    missing_record: str,
    *,
    question: str = "",
    detail: str = "",
    output_dir: Path | str | None = None,
    synthetic_banner: str | None = None,
    keep_figure: bool = False,
) -> FigureResult:
    """The honest hole for an unsatisfied input contract.

    A real figure is drawn carrying ``NOT RECORDED: <missing_record>`` so the report shows
    a labelled gap rather than a blank box or, worse, a plausible-looking chart of some
    other quantity. ``output_dir`` exports it immediately; without one the figure is built
    (and closed unless ``keep_figure``) and the caller gets the specification only.
    """

    fig, spec = build_missing_figure(
        figure_id, title, missing_record, question=question, detail=detail
    )
    spec.synthetic_banner = synthetic_banner
    result = FigureResult(
        spec=spec,
        table=[
            {
                "role": "missing_panel",
                "figure_id": figure_id,
                "missing_record": missing_record,
                "status": "not_recorded",
            }
        ],
        rendered=False,
        missing_reason=f"{MISSING_PREFIX}{missing_record}",
    )
    if output_dir is not None:
        return export_figure(fig, result, output_dir, close=not keep_figure)
    if keep_figure:
        result.figure = fig
    else:
        close_figure(fig)
    return result


def measured_value(value: Any) -> float | None:
    """Unwrap a :class:`Measured` for plotting; a non-OK status yields ``None``.

    Chart code must never coerce an absent value to zero, so this returns ``None`` and the
    caller decides whether the point is dropped, marked or counted as missing.
    """

    if value is None:
        return None
    if isinstance(value, Measured):
        if value.validity is not Validity.OK:
            return None
        try:
            return float(value.value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def measured_status(value: Any) -> str:
    """Report the validity label behind a value, for a table ``status`` column."""

    if value is None:
        return "absent"
    if isinstance(value, Measured):
        if value.validity is Validity.OK:
            return value.validity.value
        return f"{value.validity.value}:{value.reason}" if value.reason else value.validity.value
    return "ok"


__all__ = [
    "DEFAULT_SYNTHETIC_BANNER",
    "MISSING_PREFIX",
    "METHOD_COLORS",
    "METHOD_MARKERS",
    "METHOD_LINESTYLES",
    "FigureSpec",
    "FigureResult",
    "apply_method_style",
    "build_missing_figure",
    "close_figure",
    "ensure_agg_backend",
    "export_figure",
    "finish_axes",
    "measured_status",
    "measured_value",
    "missing_panel",
    "new_figure",
    "provenance_entry",
    "read_table_csv",
    "render_rgb_array",
    "software_versions",
    "stamp_banner",
    "synthetic_banner_for",
    "trailing_mean",
]
