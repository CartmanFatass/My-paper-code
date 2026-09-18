"""Tests for the portable HTML report.

The properties under test are the ones that make the report safe to hand to somebody else:
it refuses to overwrite a historical run, it separates constructed fixtures from recorded
artifacts under the exact banner string, it shows a missing panel as a labelled hole naming
the absent record instead of quietly substituting another data source, and the page is
self-contained and escaped so no label can inject markup and no element can phone home.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tools.research_support import records
from tools.research_support.plots.figure import DEFAULT_SYNTHETIC_BANNER
from tools.research_support.records import (
    AggregationLevel,
    EntityId,
    EntityKind,
    GroundEntityState,
    Measured,
    MetricRecord,
    Phase,
    SourceKind,
    XKind,
)
from tools.research_support.reports import ReportRequest, ReportResult, build_report

PNG_ONLY: dict[str, Any] = {"formats": ("png",)}


def endpoint(fit: str, value: float) -> MetricRecord:
    return MetricRecord(
        run_id="run_fixture",
        method_id="hmasd",
        metric_name="service_ratio",
        value=Measured.ok(value, unit="dimensionless"),
        x_kind=XKind.CHECKPOINT_STEP,
        x_value=200,
        phase=Phase.EVALUATION,
        aggregation_level=AggregationLevel.REPLICATE,
        training_replicate_id=fit,
        unit="dimensionless",
        source_path="fixtures/metrics.jsonl",
    )


def ground_entities() -> list[GroundEntityState]:
    return [
        GroundEntityState(
            entity=EntityId(EntityKind.AGGREGATE_DEMAND_POINT, 0),
            position_m=(100.0, 100.0, 0.0),
            offered_mbps=Measured.ok(4.0, unit="Mbps"),
            delivered_mbps=Measured.ok(3.0, unit="Mbps"),
            represents_count=25,
        ),
        GroundEntityState(
            entity=EntityId(EntityKind.INDIVIDUAL_UE, 1),
            position_m=(250.0, 180.0, 0.0),
            offered_mbps=Measured.unknown("not_observed", unit="Mbps"),
            delivered_mbps=Measured.unknown("not_observed", unit="Mbps"),
            observed=False,
        ),
    ]


def base_inputs(**extra: Any) -> dict[str, Any]:
    inputs: dict[str, Any] = {
        "source_kind": SourceKind.SYNTHETIC_FIXTURE,
        "fit_endpoints": [endpoint("fit_a", 0.61), endpoint("fit_b", 0.66)],
        "ground_entities": ground_entities(),
        "chart_options": dict(PNG_ONLY),
    }
    inputs.update(extra)
    return inputs


def build(tmp_path: Path, **kwargs: Any) -> ReportResult:
    request = ReportRequest(
        output_dir=tmp_path / "report",
        inputs=kwargs.pop("inputs", base_inputs()),
        charts=kwargs.pop("charts", ("C02", "C06", "C10")),
        **kwargs,
    )
    return build_report(request)


def test_build_report_writes_a_self_contained_index(tmp_path: Path) -> None:
    result = build(tmp_path, provenance_label="synthetic engineering fixture")
    assert result.index_path.exists()
    assert (result.output_dir / "report.json").exists()
    assert [figure.spec.figure_id for figure in result.figures] == ["C02", "C06", "C10"]

    html = result.index_path.read_text(encoding="utf-8")
    assert "http://" not in html
    assert "https://" not in html
    assert "<img src=\"figures/C02.png\"" in html
    assert (result.output_dir / "figures" / "C02.png").exists()
    assert (result.output_dir / "figures" / "C02_table.csv").exists()
    assert "figures/C02_table.csv" in html
    assert "figures/C02_spec.json" in html
    # Sample counts and the statistical unit are printed next to the figure.
    assert "statistical unit" in html
    assert "independent training replicate (fit)" in html
    assert "training fits (n)" in html
    # No automatic winner or causal story.
    assert "ranks nothing and asserts no cause" in html


def test_build_report_refuses_a_non_empty_existing_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "report"
    output_dir.mkdir()
    (output_dir / "previous_index.html").write_text("earlier evidence", encoding="utf-8")
    request = ReportRequest(output_dir=output_dir, inputs=base_inputs(), charts=("C02",))
    with pytest.raises(FileExistsError) as error:
        build_report(request)
    assert "not empty" in str(error.value)
    assert (output_dir / "previous_index.html").read_text(encoding="utf-8") == "earlier evidence"


def test_build_report_accepts_an_empty_existing_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "report"
    output_dir.mkdir()
    request = ReportRequest(output_dir=output_dir, inputs=base_inputs(), charts=("C02",))
    result = build_report(request)
    assert result.index_path.exists()


def test_missing_panel_is_a_labelled_hole_naming_the_record(tmp_path: Path) -> None:
    result = build(tmp_path)
    assert result.missing_panels == ["C10"]
    hole = [figure for figure in result.figures if figure.spec.figure_id == "C10"][0]
    assert hole.rendered is False
    assert "sweep_records" in hole.missing_reason

    html = result.index_path.read_text(encoding="utf-8")
    assert "MISSING PANEL" in html
    assert "sweep_records" in html
    assert "figures/C10.png" in html  # the hole is drawn, not a blank box
    # The panel is not filled from another data source that happens to be present.
    assert hole.table[0]["missing_record"].startswith("sweep_records")
    assert all(row.get("role") == "missing_panel" for row in hole.table)


def test_synthetic_banner_appears_in_the_html_and_in_the_figure_spec(tmp_path: Path) -> None:
    result = build(tmp_path, provenance_label="constructed fixture")
    html = result.index_path.read_text(encoding="utf-8")
    assert DEFAULT_SYNTHETIC_BANNER in html
    assert "Synthetic engineering fixtures" in html
    assert "Recorded artifacts" in html
    drawn = [figure for figure in result.figures if figure.spec.figure_id == "C02"][0]
    assert drawn.spec.synthetic_banner == DEFAULT_SYNTHETIC_BANNER
    assert DEFAULT_SYNTHETIC_BANNER in drawn.spec_path.read_text(encoding="utf-8")


def test_recorded_and_synthetic_figures_land_in_different_sections(tmp_path: Path) -> None:
    inputs = base_inputs()
    inputs.pop("source_kind")
    inputs["chart_options_by_id"] = {"C02": {**PNG_ONLY, "synthetic_banner": None}}
    result = build(tmp_path, inputs=inputs, charts=("C02",))
    html = result.index_path.read_text(encoding="utf-8")
    synthetic_index = html.index("Synthetic engineering fixtures")
    recorded_index = html.index("Recorded artifacts")
    c02_index = html.index('id="C02"')
    assert synthetic_index < recorded_index < c02_index
    assert "No synthetic fixture figures in this report." in html


def test_labels_are_escaped_before_reaching_the_page(tmp_path: Path) -> None:
    label = '<script>alert("x")</script> & "quoted"'
    result = build(tmp_path, charts=("C02",), provenance_label=label)
    html = result.index_path.read_text(encoding="utf-8")
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert "&amp; &quot;quoted&quot;" in html
    assert '<script type="application/json" id="report-data">' in html


def test_embedded_json_is_encoded_by_the_records_encoder(tmp_path: Path) -> None:
    """A warning carrying markup must be neutralised by ``records.dumps``, not by luck."""

    result = build(tmp_path, charts=("C02",), warnings=("<b>compatibility</b> & caution",))
    html = result.index_path.read_text(encoding="utf-8")
    assert "<b>compatibility</b>" not in html
    assert "&lt;b&gt;compatibility&lt;/b&gt;" in html  # escaped for the visible list
    assert "\\u003cb\\u003ecompatibility" in html  # escaped inside the JSON payload


def test_report_json_round_trips_through_the_records_encoder(tmp_path: Path) -> None:
    result = build(tmp_path, charts=("C02", "C10"))
    payload = records.loads((result.output_dir / "report.json").read_text(encoding="utf-8"))
    assert payload["missing_panels"] == ["C10"]
    assert {figure["figure_id"] for figure in payload["figures"]} == {"C02", "C10"}
    c02 = [figure for figure in payload["figures"] if figure["figure_id"] == "C02"][0]
    assert c02["spec"]["statistical_unit"] == "independent training replicate (fit)"
    assert c02["rendered"] is True
    assert payload["software_versions"]["matplotlib_backend"].lower() == "agg"


def test_unknown_chart_id_is_reported_rather_than_silently_dropped(tmp_path: Path) -> None:
    result = build(tmp_path, charts=("C02", "C99"))
    assert [figure.spec.figure_id for figure in result.figures] == ["C02"]
    assert any("C99" in warning for warning in result.warnings)
    assert "C99" in result.index_path.read_text(encoding="utf-8")


def test_a_chart_that_raises_becomes_a_reported_failure_not_a_gap(tmp_path: Path) -> None:
    inputs = base_inputs()
    inputs["chart_options_by_id"] = {"C02": {"formats": ("not_a_real_format",)}}
    result = build(tmp_path, inputs=inputs, charts=("C02",))
    assert result.missing_panels == ["C02"]
    assert any("C02 failed to render" in warning for warning in result.warnings)
    assert "MISSING PANEL" in result.index_path.read_text(encoding="utf-8")


def test_malformed_input_produces_a_named_hole_not_a_substitute(tmp_path: Path) -> None:
    inputs = base_inputs()
    inputs["fit_endpoints"] = object()  # present, but not a record sequence
    result = build(tmp_path, inputs=inputs, charts=("C02",))
    hole = result.figures[0]
    assert hole.rendered is False
    assert "fit_endpoints" in hole.missing_reason
    assert result.missing_panels == ["C02"]


def test_default_request_covers_the_whole_capability_suite(tmp_path: Path) -> None:
    result = build(tmp_path, charts=())
    assert [figure.spec.figure_id for figure in result.figures] == [
        f"C{index:02d}" for index in range(1, 15)
    ]
    rendered = {figure.spec.figure_id for figure in result.figures if figure.rendered}
    assert rendered == {"C02", "C06"}
    assert set(result.missing_panels) == {
        f"C{index:02d}" for index in range(1, 15)
    } - rendered
    html = result.index_path.read_text(encoding="utf-8")
    for index in range(1, 15):
        assert f'id="C{index:02d}"' in html


def test_figure_warnings_are_surfaced_in_the_index(tmp_path: Path) -> None:
    result = build(tmp_path, charts=("C06",))
    html = result.index_path.read_text(encoding="utf-8")
    assert "Figure warnings" in html
    assert "hatched square" in html
    assert any(warning.startswith("C06:") for warning in result.warnings)
