"""Portable HTML report: an index over figure bundles, with the provenance kept attached.

The report is a directory, not a document. Each figure keeps its own PNG/SVG/PDF, its
specification JSON and the table of the exact points it drew; ``index.html`` links to them
so a reader can go from a claim to the numbers in one click, offline.

Three properties are load-bearing:

* **Separation of fixture from artifact.** Synthetic engineering fixtures live in their own
  section, under the same banner that is stamped on the images. A figure built from
  constructed data can then never be quoted as an algorithm result by accident.
* **Holes stay visible.** A chart whose input contract was unsatisfied appears in the index
  as a labelled hole naming the absent record, and its identifier is listed in
  :attr:`ReportResult.missing_panels`. It is never dropped, and it is never filled by
  swapping in another data source.
* **Nothing is fetched.** The HTML is self-contained: no CDN, no remote font, no script
  logic. Everything inserted into the page is escaped with :func:`html.escape`, and the
  machine-readable payload is encoded with :func:`tools.research_support.records.dumps`,
  which already escapes ``<``, ``>`` and ``&``.

The report states no winner and tells no causal story; that is the reader's job, and the
figures carry the captions that say what they do and do not demonstrate.
"""

from __future__ import annotations

import html
import os
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import records
from .plots.figure import DEFAULT_SYNTHETIC_BANNER, FigureResult, software_versions

_STYLE = """
:root { color-scheme: light; }
body { font-family: "Segoe UI", Arial, Helvetica, sans-serif; margin: 0 auto; max-width: 1180px;
       padding: 24px; color: #1b1b1b; background: #ffffff; line-height: 1.45; }
h1 { font-size: 1.6rem; margin-bottom: 0.2rem; }
h2 { font-size: 1.25rem; margin-top: 2rem; border-bottom: 2px solid #1b1b1b; padding-bottom: 4px; }
h3 { font-size: 1.05rem; margin-bottom: 0.2rem; }
.banner { background: #ffe9b0; border: 2px solid #7a0000; color: #7a0000; font-weight: 700;
          padding: 10px 14px; margin: 14px 0; letter-spacing: 0.04em; }
.warnings { background: #f4f4f4; border-left: 5px solid #8c8c8c; padding: 10px 14px; margin: 14px 0; }
.warnings ul { margin: 6px 0 0 18px; padding: 0; }
.figure { border: 1px solid #cccccc; padding: 14px; margin: 18px 0; }
.figure.missing { border: 2px dashed #7a0000; background: #fff7f7; }
.figure img { max-width: 100%; height: auto; border: 1px solid #e0e0e0; }
.meta { font-size: 0.86rem; color: #333333; }
.meta table { border-collapse: collapse; margin-top: 8px; }
.meta td, .meta th { border: 1px solid #dddddd; padding: 3px 8px; text-align: left;
                     vertical-align: top; font-size: 0.84rem; }
.caption { margin: 8px 0; font-size: 0.92rem; }
.links a { margin-right: 12px; font-size: 0.86rem; }
.hole { color: #7a0000; font-weight: 700; }
footer { margin-top: 32px; font-size: 0.8rem; color: #555555; border-top: 1px solid #cccccc;
         padding-top: 10px; }
"""


@dataclass
class ReportRequest:
    """What to build and from what. ``charts`` empty means the whole capability suite."""

    output_dir: Path
    inputs: dict[str, Any]
    charts: Sequence[str] = ()
    title: str = "Algorithm capability report"
    provenance_label: str = ""
    warnings: Sequence[str] = ()


@dataclass
class ReportResult:
    output_dir: Path
    index_path: Path
    figures: list[FigureResult]
    missing_panels: list[str]
    warnings: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "output_dir": str(self.output_dir),
            "index_path": str(self.index_path),
            "figures": [figure.to_json() for figure in self.figures],
            "missing_panels": list(self.missing_panels),
            "warnings": list(self.warnings),
            "software_versions": software_versions(),
        }


def _prepare_output_dir(output_dir: Path) -> Path:
    """Create a fresh report directory, refusing to write into a populated one.

    A report directory is evidence. Overwriting one by default would silently destroy the
    figures a previous run was cited from, so an existing non-empty directory is an error
    the caller has to resolve deliberately.
    """

    directory = Path(output_dir)
    if directory.exists():
        if not directory.is_dir():
            raise FileExistsError(f"report output path exists and is not a directory: {directory}")
        if any(directory.iterdir()):
            raise FileExistsError(
                f"report output directory is not empty: {directory}. Refusing to overwrite a "
                "historical report; choose a new directory."
            )
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _chart_options(inputs: Mapping[str, Any], chart_id: str) -> dict[str, Any]:
    options = dict(inputs.get("chart_options") or {})
    per_chart = (inputs.get("chart_options_by_id") or {}).get(chart_id) or {}
    options.update(dict(per_chart))
    options.setdefault("keep_figure", False)
    return options


def build_report(request: ReportRequest) -> ReportResult:
    """Render the requested charts into a new directory and index them in ``index.html``.

    Every chart is called with the same ``inputs`` mapping; each one decides for itself
    whether its contract is satisfied. A chart that raises is reported as a failed panel
    with its exception text rather than being silently skipped, and a chart whose inputs
    are absent produces its own named missing panel - the report never substitutes a
    different data source to fill a slot.
    """

    from .plots.capability import CHART_REGISTRY, suite_chart_ids

    output_dir = _prepare_output_dir(Path(request.output_dir))
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    chart_ids = list(request.charts) or list(suite_chart_ids("capability"))
    warnings: list[str] = list(request.warnings)
    figures: list[FigureResult] = []
    missing_panels: list[str] = []

    for chart_id in chart_ids:
        entry = CHART_REGISTRY.get(chart_id)
        if entry is None:
            warnings.append(f"unknown chart id requested and skipped: {chart_id}")
            continue
        options = _chart_options(request.inputs, chart_id)
        try:
            result = entry.function(request.inputs, figures_dir, options=options)
        except Exception as error:  # pragma: no cover - exercised by the failure test
            detail = f"{type(error).__name__}: {error}"
            warnings.append(f"{chart_id} failed to render: {detail}")
            from .plots.figure import missing_panel

            result = missing_panel(
                chart_id,
                entry.title or chart_id,
                f"{chart_id} output (chart raised {detail})",
                question=entry.question,
                detail="The chart raised while drawing. Traceback is in the report JSON.",
                output_dir=figures_dir,
            )
            result.spec.add_warning(traceback.format_exc(limit=3))
        figures.append(result)
        if not result.rendered:
            missing_panels.append(result.spec.figure_id)
        for message in result.spec.warnings:
            warnings.append(f"{result.spec.figure_id}: {message}")

    index_path = output_dir / "index.html"
    result = ReportResult(
        output_dir=output_dir,
        index_path=index_path,
        figures=figures,
        missing_panels=missing_panels,
        warnings=warnings,
    )
    index_path.write_text(_render_index(request, result), encoding="utf-8")
    (output_dir / "report.json").write_text(records.dumps(result.to_json(), indent=2), encoding="utf-8")
    return result


def _relative(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return os.path.relpath(path, root).replace("\\", "/")
    except ValueError:  # pragma: no cover - different drive
        return str(path)


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _figure_block(figure: FigureResult, root: Path) -> str:
    spec = figure.spec
    png = _relative(figure.png_path, root)
    classes = "figure missing" if not figure.rendered else "figure"
    parts: list[str] = [f'<section class="{classes}" id="{_escape(spec.figure_id)}">']
    parts.append(f"<h3>{_escape(spec.figure_id)} - {_escape(spec.title)}</h3>")
    parts.append(f'<p class="meta"><strong>Question:</strong> {_escape(spec.question)}</p>')
    if not figure.rendered:
        parts.append(
            f'<p class="hole">MISSING PANEL - {_escape(figure.missing_reason or "record not recorded")}'
            "</p>"
        )
    if png:
        parts.append(
            f'<img src="{_escape(png)}" alt="{_escape(spec.figure_id)}: {_escape(spec.title)}">'
        )
    if spec.synthetic_banner:
        parts.append(f'<p class="banner">{_escape(spec.synthetic_banner)}</p>')
    parts.append(f'<p class="caption">{_escape(spec.caption)}</p>')

    rows: list[tuple[str, str]] = [
        ("statistical unit", spec.statistical_unit),
        ("metric definition", spec.metric_definition),
        ("x axis", spec.x_label),
        ("y axis", spec.y_label),
        ("selection rule", spec.selection_rule),
        ("checkpoint rule", spec.checkpoint_rule),
        ("uncertainty method", spec.uncertainty_method),
        ("training fits (n)", "not applicable" if spec.n_fits is None else str(spec.n_fits)),
        (
            "evaluation episodes (n)",
            "not recorded" if spec.n_evaluation_episodes is None else str(spec.n_evaluation_episodes),
        ),
        ("missing values (n)", str(spec.n_missing)),
        ("failed rows (n)", str(spec.n_failed)),
        ("smoothing", "none (raw)" if spec.smoothing is None else records.dumps(spec.smoothing)),
        ("alignment rule", spec.alignment_rule or "not applicable"),
        ("random seed", "not applicable" if spec.random_seed is None else str(spec.random_seed)),
    ]
    parts.append('<div class="meta"><table>')
    for name, value in rows:
        parts.append(f"<tr><th>{_escape(name)}</th><td>{_escape(value)}</td></tr>")
    for index, entry in enumerate(spec.data_provenance):
        source = entry.get("source_path") or "in-memory records"
        digest = entry.get("content_hash") or "not hashed"
        parts.append(
            f"<tr><th>source {index + 1}</th><td>{_escape(source)}<br>{_escape(digest)}</td></tr>"
        )
    parts.append("</table></div>")

    if spec.warnings:
        parts.append('<div class="warnings"><strong>Figure warnings</strong><ul>')
        for message in spec.warnings:
            parts.append(f"<li>{_escape(message)}</li>")
        parts.append("</ul></div>")

    links = [
        ("table (CSV)", _relative(figure.table_path, root)),
        (
            "table (JSON)",
            _relative(
                figure.table_path.with_name(f"{spec.figure_id}_table.json")
                if figure.table_path
                else None,
                root,
            ),
        ),
        ("figure specification (JSON)", _relative(figure.spec_path, root)),
        ("SVG", _relative(figure.svg_path, root)),
        ("PDF", _relative(figure.pdf_path, root)),
    ]
    parts.append('<p class="links">')
    for label, target in links:
        if target:
            parts.append(f'<a href="{_escape(target)}">{_escape(label)}</a>')
    parts.append("</p></section>")
    return "\n".join(parts)


def _render_index(request: ReportRequest, result: ReportResult) -> str:
    root = result.output_dir
    synthetic = [f for f in result.figures if f.spec.synthetic_banner]
    recorded = [f for f in result.figures if not f.spec.synthetic_banner]

    head = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_escape(request.title)}</title>",
        f"<style>{_STYLE}</style>",
        "</head>",
        "<body>",
        f"<h1>{_escape(request.title)}</h1>",
        f'<p class="meta">Provenance label: {_escape(request.provenance_label or "not stated")}</p>',
    ]

    compatibility: list[str] = [
        "This report ranks nothing and asserts no cause: each figure states what it does "
        "and does not demonstrate.",
        "Figures are grouped by provenance. A synthetic engineering fixture is not an "
        "algorithm result.",
    ]
    if result.missing_panels:
        compatibility.append(
            "Missing panels (the named record was not recorded): "
            + ", ".join(result.missing_panels)
        )
    body = list(head)
    body.append('<div class="warnings"><strong>Compatibility and provenance</strong><ul>')
    for message in compatibility + list(result.warnings):
        body.append(f"<li>{_escape(message)}</li>")
    body.append("</ul></div>")

    body.append("<h2>Synthetic engineering fixtures</h2>")
    if synthetic:
        body.append(f'<p class="banner">{_escape(DEFAULT_SYNTHETIC_BANNER)}</p>')
        body.append(
            '<p class="meta">Every figure in this section was drawn from constructed fixture '
            "data. It exercises the reader and the plotting code; it demonstrates nothing "
            "about any algorithm.</p>"
        )
        body.extend(_figure_block(figure, root) for figure in synthetic)
    else:
        body.append('<p class="meta">No synthetic fixture figures in this report.</p>')

    body.append("<h2>Recorded artifacts</h2>")
    if recorded:
        body.append(
            '<p class="meta">Figures drawn from recorded run artifacts. Each figure states its '
            "own selection and checkpoint rules.</p>"
        )
        body.extend(_figure_block(figure, root) for figure in recorded)
    else:
        body.append('<p class="meta">No recorded-artifact figures in this report.</p>')

    if result.missing_panels:
        body.append("<h2>Missing panels</h2>")
        body.append('<ul class="meta">')
        for figure in result.figures:
            if figure.rendered:
                continue
            body.append(
                f'<li><span class="hole">{_escape(figure.spec.figure_id)}</span>: '
                f"{_escape(figure.missing_reason)}</li>"
            )
        body.append("</ul>")

    body.append("<h2>Machine-readable summary</h2>")
    body.append('<script type="application/json" id="report-data">')
    body.append(records.dumps(result.to_json(), indent=2))
    body.append("</script>")
    body.append(
        '<p class="meta">The block above is data, not executable logic: this page contains no '
        "script logic, no remote resource and no external font.</p>"
    )

    versions = software_versions()
    body.append("<footer>")
    body.append(
        _escape(
            "Software versions: "
            + ", ".join(f"{name} {value}" for name, value in sorted(versions.items()))
        )
    )
    body.append("</footer></body></html>")
    return "\n".join(body)


__all__ = ["ReportRequest", "ReportResult", "build_report"]
