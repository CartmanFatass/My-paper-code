"""Tests for the trace-to-chart-input adapter.

Two layers. A constructed trace written with the real :class:`TraceWriter` pins the
contract that must hold on any machine: which keys are derivable, that the recorded
interval amount converts to a rate exactly and reversibly, that a standing condition
restated in every frame is one event at its own recorded time, that an interrupted
recording is reported as interrupted, and that every key a scene trace cannot support is
absent with a reason instead of being fabricated.

On top of that, the recorded traces in ``temp/research_support`` are exercised directly,
because the point of this adapter is that ``report --trace`` produces real panels from
them. Those tests skip when the traces are not present (``temp/`` is not committed), and
the constructed-trace layer still covers the contract in that case.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.research_support.capture.trace_store import STATUS_INCOMPLETE, TraceWriter
from tools.research_support.records import (
    DecisionEvent,
    EntityId,
    EntityKind,
    GroundEntityState,
    LinkActivity,
    LinkRecord,
    Measured,
    ResourceDomainRecord,
    SceneCapability,
    SceneClock,
    SceneFrame,
    SceneGeometry,
    SceneIdentity,
    SceneProvenance,
    SourceKind,
    PolicyKind,
    FrameKind,
    UavState,
    Validity,
)
from tools.research_support.report_inputs import (
    SCENE_DERIVABLE,
    inputs_from_trace,
    inputs_from_traces,
)
from tools.research_support.reports import ReportRequest, build_report

TRACE_ROOT = Path("temp/research_support")
SR_TRACE = TRACE_ROOT / "sr-trace"
SR_STATIC_TRACE = TRACE_ROOT / "sr-trace-static"
LEGACY_TRACE = TRACE_ROOT / "legacy-trace"

requires_sr = pytest.mark.skipif(not SR_TRACE.is_dir(), reason="recorded sr-trace not present")
requires_sr_pair = pytest.mark.skipif(
    not (SR_TRACE.is_dir() and SR_STATIC_TRACE.is_dir()),
    reason="recorded service-restoration trace pair not present",
)
requires_legacy = pytest.mark.skipif(
    not LEGACY_TRACE.is_dir(), reason="recorded legacy trace not present"
)

#: Keys the adapter must never invent from a scene trace.
UNSUPPORTED_KEYS = (
    "evaluation_curve",
    "fit_endpoints",
    "recovery_outcomes",
    "skill_segments",
    "membership_intervals",
    "sweep_records",
    "cost_records",
    "training_diagnostics",
    "information_records",
)


# --------------------------------------------------------------------------------------
# A constructed trace written through the real writer
# --------------------------------------------------------------------------------------


def _frame(
    sequence: int,
    *,
    world_id: str = "world-a",
    method_note: str = "rule",
    with_demand: bool = True,
    interval_s: float = 10.0,
    delivered_mbit: float = 30.0,
    offered_mbit: float = 40.0,
    event: bool = False,
) -> SceneFrame:
    start = float(sequence) * interval_s
    end = start + interval_s
    uav = EntityId(EntityKind.UAV, 0)
    site = EntityId(EntityKind.SITE, 0)
    cell = EntityId(EntityKind.AGGREGATE_DEMAND_POINT, 0)
    demand = (
        {
            "offered_mbps": Measured.ok(offered_mbit / interval_s, unit="Mbps"),
            "delivered_mbps": Measured.ok(delivered_mbit / interval_s, unit="Mbps"),
        }
        if with_demand
        else {
            "offered_mbps": Measured.not_applicable("environment models no traffic demand"),
            "delivered_mbps": Measured.not_applicable("environment models no traffic demand"),
        }
    )
    interval_metrics: dict[str, Measured] = {
        "reward_total": Measured.ok(0.5, unit="native_reward"),
        "interval_start_s": Measured.ok(start, unit="s"),
        "interval_end_s": Measured.ok(end, unit="s"),
    }
    if with_demand:
        interval_metrics.update(
            {
                "offered_mbit_interval": Measured.ok(offered_mbit, unit="Mbit"),
                "delivered_mbit_interval": Measured.ok(delivered_mbit, unit="Mbit"),
                "unmet_mbit_interval": Measured.ok(offered_mbit - delivered_mbit, unit="Mbit"),
            }
        )
    return SceneFrame(
        identity=SceneIdentity(
            run_id=f"run-{method_note}",
            trace_id=f"trace-{method_note}",
            episode_id="episode-0",
            world_id=world_id,
            lane_id=0,
            sequence=sequence,
        ),
        clock=SceneClock(
            simulation_time_s=end,
            geometry_time_s=start,
            decision_step=sequence,
            capture_wall_time_utc="2026-09-18T00:00:00+00:00",
            producer_monotonic_s=float(sequence),
            measurement_start_s=start,
            measurement_end_s=start + 1.0,
        ),
        provenance=SceneProvenance(
            route="service-restoration",
            environment_id="env_v0" if with_demand else "legacy_env_v0",
            source_kind=SourceKind.RULE_CONTROLLER_ROLLOUT,
            policy_kind=PolicyKind.RULE_CONTROLLER,
            information_condition="central_delayed_telemetry",
            frame_kind=FrameKind.TRANSITION,
            capture_resolution="one_frame_per_decision",
        ),
        geometry=SceneGeometry(bounds_m=(0.0, 0.0, 1000.0, 1000.0)),
        capability=SceneCapability(
            has_uav_positions=True,
            has_aggregate_demand=with_demand,
            has_demand_rates=with_demand,
            has_delivered_rates=with_demand,
            has_links=True,
            has_link_flows=with_demand,
            has_interval_metrics=True,
        ),
        uavs=(
            UavState(
                entity=uav,
                position_m=(10.0 * sequence, 20.0, 80.0),
                executed_velocity_mps=(1.0, 0.0, 0.0),
                requested_velocity_mps=(1.0, 0.0, 0.0),
            ),
        ),
        ground_entities=(
            GroundEntityState(
                entity=cell,
                position_m=(100.0, 200.0, 0.0),
                represents_count=12,
                service_status="served" if with_demand else None,
                **demand,
            ),
        ),
        links=(
            LinkRecord(
                link_key="site:0:0->aggregate_demand_point:0:0|site_access",
                source=site,
                target=cell,
                link_class="site_access",
                activity=LinkActivity.ACTIVE,
                capacity_mbps=Measured.ok(50.0, unit="Mbps"),
                flow_mbps=(
                    Measured.ok(delivered_mbit / interval_s, unit="Mbps")
                    if with_demand
                    else Measured.not_applicable("environment models no traffic flow")
                ),
                utilization=(
                    Measured.ok(delivered_mbit / interval_s / 50.0)
                    if with_demand
                    else Measured.not_applicable("environment models no traffic flow")
                ),
                resource_domain="access:site0",
            ),
        ),
        resource_domains=(
            ResourceDomainRecord(
                domain_id="access:site0",
                description="site 0 access airtime",
                link_keys=("site:0:0->aggregate_demand_point:0:0|site_access",),
                utilization=Measured.ok(0.4) if with_demand else None,
            ),
        ),
        events=(
            (
                DecisionEvent(
                    time_s=20.0,
                    event_type="full_site_failure",
                    description="full_site_failure on site index 1",
                ),
            )
            if event
            else ()
        ),
        interval_metrics=interval_metrics,
    )


def write_trace(
    directory: Path,
    *,
    n_frames: int = 4,
    world_id: str = "world-a",
    method_note: str = "rule",
    with_demand: bool = True,
    delivered_mbit: float = 30.0,
    controller: str = "greedy_rule",
    status: str | None = None,
    truncate_last_line: bool = False,
) -> Path:
    """Write a small trace with the real writer, optionally leaving it interrupted."""

    writer = TraceWriter(
        directory,
        trace_id=f"trace-{method_note}",
        manifest={
            "route": "service-restoration",
            "environment_id": "env_v0" if with_demand else "legacy_env_v0",
            "controller": controller,
            "controller_kind": "untuned_diagnostic_rule",
            "seed": 17,
            "source_kind": "rule_controller_rollout",
        },
    )
    for sequence in range(n_frames):
        frame = _frame(
            sequence,
            world_id=world_id,
            method_note=method_note,
            with_demand=with_demand,
            delivered_mbit=delivered_mbit,
            # The same standing condition is restated from its onset onwards, exactly as
            # the recorded service-restoration trace does.
            event=sequence >= 2,
        )
        writer.append(frame.to_bytes(), sequence=sequence, time_s=frame.clock.simulation_time_s)
    writer.close(status=status or "closed")
    if truncate_last_line:
        chunk = sorted((directory / "chunks").glob("chunk-*.jsonl"))[-1]
        raw = chunk.read_bytes()
        chunk.write_bytes(raw[: len(raw) - 40])
    return directory


def test_scene_trace_yields_only_the_four_supported_keys(tmp_path: Path) -> None:
    derived = inputs_from_trace(write_trace(tmp_path / "t"))
    assert derived["derived_inputs"] == list(SCENE_DERIVABLE)
    for key in SCENE_DERIVABLE:
        assert derived[key], f"{key} should be non-empty"
    for key in UNSUPPORTED_KEYS:
        assert key not in derived, f"{key} must not be fabricated from a scene trace"
        assert key in derived["absent_inputs"]
        assert derived["absent_inputs"][key]
    assert "world_differences" in derived["absent_inputs"]
    assert "two traces" in derived["absent_inputs"]["world_differences"]


def test_interval_amounts_become_rates_exactly_and_reversibly(tmp_path: Path) -> None:
    derived = inputs_from_trace(write_trace(tmp_path / "t", delivered_mbit=30.0))
    rows = [r for r in derived["service_timeseries"] if r.metric_name == "delivered_mbps"]
    assert len(rows) == 4
    for row in rows:
        width = row.interval_end_s - row.interval_start_s
        assert width == 10.0
        assert row.value.unit == "Mbps"
        assert row.value.value == pytest.approx(3.0)
        # Multiplying the plotted rate by the record's own width returns the recorded Mbit.
        assert row.value.value * width == pytest.approx(30.0)
        assert "divided by its own recorded interval width" in row.definition_id
        assert row.x_value == row.interval_end_s
    # The reward term is not dragged onto the service axis.
    assert {r.metric_name for r in derived["service_timeseries"]} == {
        "offered_mbps",
        "delivered_mbps",
        "unmet_mbps",
    }
    unmet = derived["unmet_traffic"]
    assert all(r.metric_name == "unmet_mbps" for r in unmet)


def test_a_standing_condition_is_one_event_at_its_recorded_time(tmp_path: Path) -> None:
    derived = inputs_from_trace(write_trace(tmp_path / "t", n_frames=6))
    events = derived["world_events"]
    assert len(events) == 1  # restated in four frames, recorded once
    assert events[0].time_s == 20.0
    assert events[0].event_type == "full_site_failure"


def test_geometry_sections_use_the_geometry_time(tmp_path: Path) -> None:
    derived = inputs_from_trace(write_trace(tmp_path / "t"))
    assert [frame["time_s"] for frame in derived["uav_frames"]] == [0.0, 10.0, 20.0, 30.0]
    assert [frame["time_s"] for frame in derived["link_frames"]] == [0.0, 10.0, 20.0, 30.0]
    link = derived["link_frames"][0]["links"][0]
    assert isinstance(link, LinkRecord)
    assert link.activity is LinkActivity.ACTIVE
    assert link.capacity_mbps.value == 50.0
    assert link.resource_domain == "access:site0"
    uav = derived["uav_frames"][0]["uavs"][0]
    assert isinstance(uav, UavState)
    assert uav.position_m[2] == 80.0
    assert uav.requested_velocity_mps == (1.0, 0.0, 0.0)


def test_spatial_frame_is_chosen_by_position_not_by_outcome(tmp_path: Path) -> None:
    derived = inputs_from_trace(write_trace(tmp_path / "t"), ground_frame_selector="last")
    assert isinstance(derived["geometry"], SceneGeometry)
    entity = derived["ground_entities"][0]
    assert entity.represents_count == 12
    assert entity.offered_mbps.validity is Validity.OK
    rule = derived["chart_options_by_id"]["C06"]["checkpoint_rule"]
    assert "chosen by position in the recording" in rule
    first = inputs_from_trace(write_trace(tmp_path / "u"), ground_frame_selector="first")
    assert "first recorded frame" in first["chart_options_by_id"]["C06"]["checkpoint_rule"]


def test_a_route_without_a_traffic_model_claims_no_demand(tmp_path: Path) -> None:
    derived = inputs_from_trace(write_trace(tmp_path / "t", with_demand=False))
    assert "service_timeseries" not in derived
    assert "no offered, delivered or unmet" in derived["absent_inputs"]["service_timeseries"]
    assert "models no traffic demand" in derived["absent_inputs"]["service_timeseries"]
    # Links exist but carry no flow: an empty capacity panel would imply a flat measurement.
    assert "link_frames" not in derived
    assert "no recorded flow or utilization" in derived["absent_inputs"]["link_frames"]
    entity = derived["ground_entities"][0]
    assert entity.offered_mbps.validity is Validity.NOT_APPLICABLE
    assert entity.delivered_mbps.validity is Validity.NOT_APPLICABLE
    assert entity.offered_mbps.value is None


def test_an_interrupted_trace_is_reported_as_interrupted(tmp_path: Path) -> None:
    derived = inputs_from_trace(
        write_trace(tmp_path / "t", status=STATUS_INCOMPLETE, truncate_last_line=True)
    )
    provenance = derived["trace_provenance"][0]
    assert provenance["complete"] is False
    assert provenance["status"] == STATUS_INCOMPLETE
    assert derived["read_status"][provenance["trace_id"]] == STATUS_INCOMPLETE
    assert any("not a cleanly closed recording" in note for note in derived["notes"])
    assert any("partial episode" in note for note in derived["notes"])


def test_provenance_carries_the_trace_identity(tmp_path: Path) -> None:
    provenance = inputs_from_trace(write_trace(tmp_path / "t"))["trace_provenance"][0]
    assert provenance["trace_id"] == "trace-rule"
    assert provenance["world_id"] == "world-a"
    assert provenance["episode_id"] == "episode-0"
    assert provenance["run_id"] == "run-rule"
    assert provenance["lane_id"] == 0
    assert provenance["source_kind"] == "rule_controller_rollout"
    assert provenance["policy_kind"] == "rule_controller"
    assert provenance["method_id"] == "greedy_rule"
    assert provenance["manifest"]["seed"] == 17


def test_two_traces_of_the_same_world_earn_a_comparison(tmp_path: Path) -> None:
    a = write_trace(tmp_path / "a", method_note="a", controller="greedy_rule", delivered_mbit=30.0)
    b = write_trace(tmp_path / "b", method_note="b", controller="static_uav", delivered_mbit=20.0)
    derived = inputs_from_traces([a, b])
    assert "world_differences" in derived["derived_inputs"]
    assert derived["method_a"] == "greedy_rule"
    assert derived["method_b"] == "static_uav"
    assert derived["pairing_evidence"] == "verified_world_identity"
    assert derived["chart_options_by_id"]["C14"]["metric_name"] == "delivered_mbit_episode_total"
    rows = [
        row
        for row in derived["world_differences"]
        if row.metric_name == "delivered_mbit_episode_total"
    ]
    assert {row.method_id: row.value.value for row in rows} == {
        "greedy_rule": pytest.approx(120.0),  # 4 intervals x 30 Mbit
        "static_uav": pytest.approx(80.0),
    }
    assert all(row.unit == "Mbit" for row in rows)
    # The scene panels stay with the first trace rather than being spliced together.
    assert len(derived["uav_frames"]) == 4
    assert len(derived["trace_provenance"]) == 2


def test_two_traces_of_different_worlds_are_not_differenced(tmp_path: Path) -> None:
    a = write_trace(tmp_path / "a", method_note="a", world_id="world-a", controller="greedy_rule")
    b = write_trace(tmp_path / "b", method_note="b", world_id="world-b", controller="static_uav")
    derived = inputs_from_traces([a, b])
    assert "world_differences" not in derived
    reason = derived["absent_inputs"]["world_differences"]
    assert "world identities differ" in reason
    assert "world-a" in reason and "world-b" in reason
    assert "pairing_evidence" not in derived


def test_two_traces_of_the_same_method_are_not_differenced(tmp_path: Path) -> None:
    a = write_trace(tmp_path / "a", method_note="a", controller="greedy_rule")
    b = write_trace(tmp_path / "b", method_note="b", controller="greedy_rule")
    derived = inputs_from_traces([a, b])
    assert "world_differences" not in derived
    assert "two distinguishable arms" in derived["absent_inputs"]["world_differences"]


def test_report_from_a_constructed_trace_draws_what_it_has(tmp_path: Path) -> None:
    derived = inputs_from_trace(write_trace(tmp_path / "t"))
    derived["chart_options"] = {"formats": ("png",)}
    result = build_report(
        ReportRequest(
            output_dir=tmp_path / "report",
            inputs=derived,
            title="Constructed trace",
            provenance_label="rule controller rollout",
        )
    )
    rendered = {figure.spec.figure_id for figure in result.figures if figure.rendered}
    assert rendered == {"C03", "C05", "C06", "C07"}
    assert set(result.missing_panels) == {
        "C01",
        "C02",
        "C04",
        "C08",
        "C09",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
    }
    html = result.index_path.read_text(encoding="utf-8")
    assert "Recorded artifacts" in html
    # A rule-controller rollout is a recorded artifact, not a synthetic fixture.
    for figure in result.figures:
        assert figure.spec.synthetic_banner is None


# --------------------------------------------------------------------------------------
# The recorded traces on disk
# --------------------------------------------------------------------------------------


@requires_sr
def test_recorded_service_restoration_trace_supports_four_panels() -> None:
    derived = inputs_from_trace(SR_TRACE)
    assert derived["derived_inputs"] == list(SCENE_DERIVABLE)
    assert len(derived["service_timeseries"]) == 180  # 60 recorded intervals x 3 quantities
    assert {row.metric_name for row in derived["service_timeseries"]} == {
        "offered_mbps",
        "delivered_mbps",
        "unmet_mbps",
    }
    events = derived["world_events"]
    assert [(event.time_s, event.event_type) for event in events] == [
        (120.0, "full_site_failure")
    ]
    assert len(derived["link_frames"]) == 60
    assert len(derived["uav_frames"]) == 61
    assert len(derived["ground_entities"]) == 9
    assert all(
        entity.entity.kind is EntityKind.AGGREGATE_DEMAND_POINT
        for entity in derived["ground_entities"]
    )
    for key in UNSUPPORTED_KEYS:
        assert key not in derived
        assert key in derived["absent_inputs"]
    provenance = derived["trace_provenance"][0]
    assert provenance["status"] == "closed"
    assert provenance["complete"] is True
    assert provenance["method_id"] == "backhaul_aware_greedy"
    assert provenance["environment_id"] == "uav_service_restoration_v0"


@requires_sr
def test_report_from_the_recorded_trace_renders_the_supported_charts(tmp_path: Path) -> None:
    derived = inputs_from_trace(SR_TRACE)
    derived["chart_options"] = {"formats": ("png",)}
    result = build_report(
        ReportRequest(
            output_dir=tmp_path / "report",
            inputs=derived,
            title="Service restoration capability",
            provenance_label="rule controller rollout, 1 episode, not a training result",
        )
    )
    rendered = {figure.spec.figure_id for figure in result.figures if figure.rendered}
    assert {"C03", "C05", "C06", "C07"} <= rendered
    assert {"C01", "C02", "C04", "C08", "C09", "C10", "C11", "C12", "C13"} <= set(
        result.missing_panels
    )
    c03 = [f for f in result.figures if f.spec.figure_id == "C03"][0]
    event_rows = [row for row in c03.table if row.get("role") == "event_marker"]
    assert [row["time_s"] for row in event_rows] == [120.0]
    assert "Mbps" in c03.spec.y_label
    c06 = [f for f in result.figures if f.spec.figure_id == "C06"][0]
    assert any("aggregate demand point" in warning for warning in c06.spec.warnings)
    html = result.index_path.read_text(encoding="utf-8")
    assert "http://" not in html and "https://" not in html


@requires_legacy
def test_recorded_legacy_trace_does_not_claim_demand_it_has_not_got(tmp_path: Path) -> None:
    derived = inputs_from_trace(LEGACY_TRACE)
    assert "service_timeseries" not in derived
    assert "link_frames" not in derived
    assert sorted(derived["derived_inputs"]) == ["ground_entities", "uav_frames"]
    entities = derived["ground_entities"]
    assert entities
    assert all(entity.entity.kind is EntityKind.INDIVIDUAL_UE for entity in entities)
    for entity in entities:
        assert entity.offered_mbps.validity is Validity.NOT_APPLICABLE
        assert entity.delivered_mbps.validity is Validity.NOT_APPLICABLE
        assert entity.offered_mbps.value is None  # never a zero standing in for "no model"

    derived["chart_options"] = {"formats": ("png",)}
    result = build_report(
        ReportRequest(output_dir=tmp_path / "report", inputs=derived, charts=("C06",))
    )
    figure = result.figures[0]
    statuses = {
        row["status"]
        for row in figure.table
        if str(row.get("role", "")).startswith("map_marker_offered")
    }
    assert statuses == {"demand_not_applicable"}
    assert any("models no traffic demand" in warning for warning in figure.spec.warnings)


@requires_sr_pair
def test_two_recorded_traces_of_the_same_world_populate_c14(tmp_path: Path) -> None:
    derived = inputs_from_traces([SR_TRACE, SR_STATIC_TRACE])
    assert "world_differences" in derived["derived_inputs"]
    assert derived["pairing_evidence"] == "verified_world_identity"
    assert derived["method_a"] == "backhaul_aware_greedy"
    assert derived["method_b"] == "static_uav"
    worlds = {row.world_id for row in derived["world_differences"]}
    assert len(worlds) == 1

    derived["chart_options"] = {"formats": ("png",)}
    result = build_report(
        ReportRequest(output_dir=tmp_path / "report", inputs=derived, charts=("C14",))
    )
    figure = result.figures[0]
    assert figure.rendered
    differences = [row for row in figure.table if row.get("role") == "world_difference"]
    assert len(differences) == 1
    assert differences[0]["status"] == "matched"
    assert differences[0]["unit"] == "Mbit"
    # One matched world gives a point, never an interval of width zero.
    assert "unavailable" in figure.spec.uncertainty_method
    assert [row for row in figure.table if row.get("role") == "world_interval"] == []


@requires_sr
@requires_legacy
def test_a_service_trace_and_a_legacy_trace_are_not_differenced() -> None:
    derived = inputs_from_traces([SR_TRACE, LEGACY_TRACE])
    assert "world_differences" not in derived
    reason = derived["absent_inputs"]["world_differences"]
    assert "different environments" in reason
    assert "uav_forced_relay_env_v0" in reason
    assert "pairing_evidence" not in derived
    # The scene panels still come from the first trace only.
    assert len(derived["uav_frames"]) == 61
