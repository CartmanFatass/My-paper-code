"""Tests for ``tools/research_support/render.py``.

The renderer is the one place where a reading mistake becomes invisible, so the tests are
about honesty of the encoding rather than about pixels:

* a missing measurement renders as missing, with the entity still drawn;
* an available link and a carrying link are different artists, not the same "connected"
  style;
* every service status pairs a colour with a marker, so colour is never the only
  difference;
* metric aspect is equal and marker **area** (not radius) carries offered demand;
* a synthetic fixture says so, and the footer lines do not overprint each other.
"""

from __future__ import annotations

import itertools
import pathlib
import sys
from typing import Any, Iterator

import numpy as np
import pytest

_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import matplotlib  # noqa: E402

matplotlib.use("Agg", force=True)  # the renderer selects Agg too; be explicit for the test

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import to_rgba  # noqa: E402

from tools.research_support import records as R  # noqa: E402
from tools.research_support.render import (  # noqa: E402
    LINK_COLOURS,
    STATUS_MARKERS,
    render_scene_figure,
    render_scene_rgb,
)

_BANNER = "SYNTHETIC ENGINEERING FIXTURE - NOT AN ALGORITHM RESULT"


@pytest.fixture(autouse=True)
def _no_leaked_figures() -> Iterator[None]:
    plt.close("all")
    yield
    plt.close("all")
    assert plt.get_fignums() == []


# --------------------------------------------------------------------------------------
# Frame fixtures
# --------------------------------------------------------------------------------------


def _uav(slot: int, position: tuple[float, float, float]) -> R.UavState:
    return R.UavState(
        entity=R.EntityId(kind=R.EntityKind.UAV, slot=slot, label=f"uav-{slot}"),
        position_m=position,
    )


def _ground(
    slot: int,
    position: tuple[float, float, float],
    offered: R.Measured | None,
    status: str,
) -> R.GroundEntityState:
    return R.GroundEntityState(
        entity=R.EntityId(
            kind=R.EntityKind.AGGREGATE_DEMAND_POINT, slot=slot, label=f"cell-{slot}"
        ),
        position_m=position,
        offered_mbps=offered,
        service_status=status,
    )


def _scene(
    *,
    uavs: tuple[R.UavState, ...] = (),
    ground: tuple[R.GroundEntityState, ...] = (),
    sites: tuple[R.SiteStateRecord, ...] = (),
    links: tuple[R.LinkRecord, ...] = (),
    is_real: bool = False,
    capability: R.SceneCapability | None = None,
) -> dict[str, Any]:
    frame = R.SceneFrame(
        identity=R.SceneIdentity(
            run_id="run-1", trace_id="trace-1", episode_id="ep-1", world_id="w-1",
            lane_id=0, sequence=3,
        ),
        clock=R.SceneClock(
            simulation_time_s=12.5, geometry_time_s=12.0, decision_step=5,
            capture_wall_time_utc="2026-09-18T00:00:00Z", producer_monotonic_s=1.0,
            measurement_start_s=12.0, measurement_end_s=12.5,
        ),
        provenance=R.SceneProvenance(
            route="unit_test", environment_id="uav_service_restoration",
            source_kind=(
                R.SourceKind.RULE_CONTROLLER_ROLLOUT if is_real else R.SourceKind.SYNTHETIC_FIXTURE
            ),
            policy_kind=R.PolicyKind.RULE_CONTROLLER,
            information_condition="privileged_truth", frame_kind=R.FrameKind.TRANSITION,
            capture_resolution="decision_boundary", is_real_activity_data=is_real,
        ),
        geometry=R.SceneGeometry(bounds_m=(0.0, 0.0, 1000.0, 1000.0)),
        capability=capability
        or R.SceneCapability(
            has_uav_positions=True, has_aggregate_demand=True, has_links=True,
            has_demand_rates=True,
        ),
        uavs=uavs,
        ground_entities=ground,
        sites=sites,
        links=links,
    )
    payload = frame.to_json()
    assert R.validate_scene_json(payload) == []
    return payload


def _mixed_frame(**kwargs: Any) -> dict[str, Any]:
    """Two measured demands 4x apart, one missing demand, one active and one idle link."""

    uav_a = _uav(0, (200.0, 200.0, 120.0))
    uav_b = _uav(1, (400.0, 300.0, 120.0))
    low = _ground(0, (300.0, 300.0, 0.0), R.Measured.ok(1.0, unit="Mbps"), "served")
    high = _ground(1, (700.0, 400.0, 0.0), R.Measured.ok(4.0, unit="Mbps"), "partially_served")
    missing = _ground(2, (800.0, 800.0, 0.0), R.Measured.unknown("not_observed"), "unknown_demand")
    site_up = R.SiteStateRecord(
        entity=R.EntityId(kind=R.EntityKind.SITE, slot=0, label="site-0"),
        position_m=(500.0, 500.0, 25.0), radio_up=True, core_link_up=True,
    )
    site_down = R.SiteStateRecord(
        entity=R.EntityId(kind=R.EntityKind.SITE, slot=1, label="site-1"),
        position_m=(600.0, 100.0, 25.0), radio_up=False, core_link_up=True, degraded=True,
    )
    active = R.LinkRecord(
        link_key=R.canonical_link_key(uav_a.entity, low.entity, "uav_access"),
        source=uav_a.entity, target=low.entity, link_class="uav_access",
        activity=R.LinkActivity.ACTIVE,
        flow_mbps=R.Measured.ok(1.0), utilization=R.Measured.ok(0.5),
    )
    available = R.LinkRecord(
        link_key=R.canonical_link_key(uav_b.entity, high.entity, "uav_access"),
        source=uav_b.entity, target=high.entity, link_class="uav_access",
        activity=R.LinkActivity.AVAILABLE,
        flow_mbps=R.Measured.ok(0.0), utilization=R.Measured.ok(0.0),
    )
    return _scene(
        uavs=(uav_a, uav_b),
        ground=(low, high, missing),
        sites=(site_up, site_down),
        links=(active, available),
        **kwargs,
    )


def _sizes_by_position(axes) -> dict[tuple[float, float], list[float]]:
    out: dict[tuple[float, float], list[float]] = {}
    for collection in axes.collections:
        offsets = np.asarray(collection.get_offsets(), dtype=float)
        sizes = np.asarray(collection.get_sizes(), dtype=float)
        for index, (x, y) in enumerate(offsets):
            size = float(sizes[index % len(sizes)])
            out.setdefault((round(float(x), 3), round(float(y), 3)), []).append(size)
    return out


# --------------------------------------------------------------------------------------
# rgb_array contract
# --------------------------------------------------------------------------------------


def test_render_scene_rgb_returns_an_hw3_uint8_array() -> None:
    array = render_scene_rgb(_mixed_frame(), figsize=(4.0, 3.0), dpi=60)
    assert array.ndim == 3
    assert array.shape == (180, 240, 3)
    assert array.dtype == np.uint8
    assert array.flags["C_CONTIGUOUS"]
    assert array.min() >= 0 and array.max() <= 255
    assert array.max() > array.min(), "the frame rendered as a single flat colour"
    # The renderer closes its own figure on this path.
    assert plt.get_fignums() == []


# --------------------------------------------------------------------------------------
# Missing values
# --------------------------------------------------------------------------------------


def test_a_missing_measurement_renders_without_inventing_a_value() -> None:
    frame = _mixed_frame()
    figure = render_scene_figure(frame, figsize=(6.0, 5.0), dpi=80)
    try:
        axes = figure.axes[0]
        sizes = _sizes_by_position(axes)
        # Three ground markers, two site markers (+1 overstrike for the down site), two UAVs.
        assert len(axes.collections) == 3 + 3 + 2

        missing_position = (800.0, 800.0)
        assert missing_position in sizes, "the entity with a missing demand was not drawn"
        assert sizes[missing_position] == [45.0], "a missing demand uses the neutral size"

        # Its colour/marker come from its declared status, not from a substituted number.
        colour, marker, filled = STATUS_MARKERS["unknown_demand"]
        collection = axes.collections[2]
        assert tuple(np.asarray(collection.get_offsets(), dtype=float)[0]) == missing_position
        assert np.allclose(collection.get_edgecolor()[0], to_rgba(colour))
        assert filled is False
        assert collection.get_facecolor().size == 0 or np.allclose(
            collection.get_facecolor()[0][3], 0.0
        )
    finally:
        plt.close(figure)


def test_a_frame_with_no_measurement_at_all_still_draws_every_entity() -> None:
    ground = tuple(
        _ground(slot, (100.0 * (slot + 1), 200.0, 0.0), R.Measured.unknown("no traffic model"),
                "unknown_demand")
        for slot in range(3)
    )
    figure = render_scene_figure(
        _scene(
            uavs=(_uav(0, (50.0, 50.0, 100.0)),),
            ground=ground,
            capability=R.SceneCapability(has_individual_ues=True, has_uav_positions=True),
        ),
        figsize=(5.0, 4.0),
        dpi=70,
    )
    try:
        axes = figure.axes[0]
        sizes = _sizes_by_position(axes)
        assert all(sizes[(100.0 * (slot + 1), 200.0)] == [45.0] for slot in range(3))
        footer = [text.get_text() for text in figure.texts]
        assert any("individual simulated UEs" in line for line in footer)
        assert not any("AGGREGATE DEMAND POINTS" in line for line in footer)
    finally:
        plt.close(figure)


# --------------------------------------------------------------------------------------
# Links
# --------------------------------------------------------------------------------------


def test_available_and_active_links_are_visibly_different_artists() -> None:
    figure = render_scene_figure(_mixed_frame(), figsize=(6.0, 5.0), dpi=80)
    try:
        axes = figure.axes[0]
        lines = axes.get_lines()
        assert len(lines) == 2, "one artist per link"
        active, available = lines[0], lines[1]

        assert active.get_linestyle() != available.get_linestyle()
        assert active.is_dashed() is False
        assert available.is_dashed() is True
        assert active.get_linewidth() > available.get_linewidth()
        assert active.get_linewidth() == pytest.approx(1.0 + 3.0 * 0.5)
        assert available.get_linewidth() == pytest.approx(0.7)
        assert to_rgba(active.get_color()) != to_rgba(available.get_color())
        assert to_rgba(active.get_color()) == to_rgba(LINK_COLOURS["uav_access"])
        assert active.get_alpha() != available.get_alpha()
        assert active.get_zorder() > available.get_zorder()
    finally:
        plt.close(figure)


def test_link_width_tracks_utilization_and_survives_a_missing_one() -> None:
    uav = _uav(0, (100.0, 100.0, 120.0))
    cells = tuple(
        _ground(slot, (200.0 + 100.0 * slot, 300.0, 0.0), R.Measured.ok(1.0), "served")
        for slot in range(3)
    )
    utilizations = (R.Measured.ok(0.0), R.Measured.ok(1.0), R.Measured.unknown("not_recorded"))
    links = tuple(
        R.LinkRecord(
            link_key=R.canonical_link_key(uav.entity, cell.entity, "uav_access"),
            source=uav.entity, target=cell.entity, link_class="uav_access",
            activity=R.LinkActivity.ACTIVE, utilization=utilization,
        )
        for cell, utilization in zip(cells, utilizations)
    )
    figure = render_scene_figure(
        _scene(uavs=(uav,), ground=cells, links=links), figsize=(5.0, 4.0), dpi=70
    )
    try:
        widths = [line.get_linewidth() for line in figure.axes[0].get_lines()]
        assert widths[0] == pytest.approx(1.0)
        assert widths[1] == pytest.approx(4.0)
        # An unknown utilization falls back to the unscaled width, it does not guess 1.0.
        assert widths[2] == pytest.approx(1.0)
    finally:
        plt.close(figure)


def test_a_link_to_an_absent_endpoint_is_skipped_rather_than_raising() -> None:
    uav = _uav(0, (100.0, 100.0, 120.0))
    ghost = R.EntityId(kind=R.EntityKind.AGGREGATE_DEMAND_POINT, slot=99)
    link = R.LinkRecord(
        link_key=R.canonical_link_key(uav.entity, ghost, "uav_access"),
        source=uav.entity, target=ghost, link_class="uav_access",
        activity=R.LinkActivity.ACTIVE,
    )
    figure = render_scene_figure(_scene(uavs=(uav,), links=(link,)), figsize=(4.0, 3.0), dpi=60)
    try:
        assert figure.axes[0].get_lines() == []
    finally:
        plt.close(figure)


# --------------------------------------------------------------------------------------
# Status encoding
# --------------------------------------------------------------------------------------


def test_status_markers_never_differ_by_colour_alone() -> None:
    pairs = {name: (colour, marker) for name, (colour, marker, _f) in STATUS_MARKERS.items()}
    for first, second in itertools.combinations(pairs, 2):
        colour_a, marker_a = pairs[first]
        colour_b, marker_b = pairs[second]
        if (colour_a, marker_a) == (colour_b, marker_b):
            continue  # a deliberate alias, not two statuses that look alike
        assert marker_a != marker_b, f"{first} and {second} differ only by colour"

    # ``unknown_demand`` and ``unknown_service`` are the one intentional alias pair.
    assert pairs["unknown_demand"] == pairs["unknown_service"]
    distinct = set(pairs.values())
    assert len(distinct) == len(STATUS_MARKERS) - 1
    assert len({colour for colour, _m in distinct}) == len(distinct)
    assert len({marker for _c, marker in distinct}) == len(distinct)
    # The fill flag is a property of the pair, not a third independent channel.
    by_pair: dict[tuple[str, str], set[bool]] = {}
    for colour, marker, filled in STATUS_MARKERS.values():
        by_pair.setdefault((colour, marker), set()).add(filled)
    assert all(len(flags) == 1 for flags in by_pair.values())


def test_each_status_draws_a_distinguishable_marker() -> None:
    statuses = sorted(
        {(colour, marker, filled): name for name, (colour, marker, filled) in STATUS_MARKERS.items()}.values()
    )
    ground = tuple(
        _ground(slot, (100.0 * (slot + 1), 500.0, 0.0), R.Measured.ok(1.0), status)
        for slot, status in enumerate(statuses)
    )
    figure = render_scene_figure(_scene(ground=ground), figsize=(7.0, 5.0), dpi=80)
    try:
        axes = figure.axes[0]
        assert len(axes.collections) == len(statuses)
        signatures = set()
        for collection in axes.collections:
            path = collection.get_paths()[0]
            signatures.add(
                (
                    path.vertices.shape,
                    np.round(path.vertices, 4).tobytes(),
                    np.round(collection.get_edgecolor(), 4).tobytes(),
                    collection.get_facecolor().size > 0,
                )
            )
        assert len(signatures) == len(statuses), "two statuses render the same marker"
    finally:
        plt.close(figure)


def test_an_unknown_status_string_gets_a_neutral_marker_not_a_served_one() -> None:
    ground = (_ground(0, (100.0, 100.0, 0.0), R.Measured.ok(1.0), "something_new"),)
    figure = render_scene_figure(_scene(ground=ground), figsize=(4.0, 3.0), dpi=60)
    try:
        collection = figure.axes[0].collections[0]
        served_colour = to_rgba(STATUS_MARKERS["served"][0])
        assert not np.allclose(collection.get_edgecolor()[0], served_colour)
    finally:
        plt.close(figure)


# --------------------------------------------------------------------------------------
# Geometry and scaling
# --------------------------------------------------------------------------------------


def test_axes_aspect_is_equal_and_bounds_come_from_the_frame() -> None:
    figure = render_scene_figure(_mixed_frame(), figsize=(6.0, 5.0), dpi=80)
    try:
        axes = figure.axes[0]
        assert axes.get_aspect() in (1.0, "equal")
        assert axes.get_xlim() == (0.0, 1000.0)
        assert axes.get_ylim() == (0.0, 1000.0)
        assert axes.get_xlabel() == "x (m)" and axes.get_ylabel() == "y (m)"
    finally:
        plt.close(figure)


def test_marker_area_not_radius_is_proportional_to_offered_demand() -> None:
    """Matplotlib's ``s`` is an area in points^2, so a 4x demand must be a 4x ``s``."""

    figure = render_scene_figure(_mixed_frame(), figsize=(6.0, 5.0), dpi=80)
    try:
        sizes = _sizes_by_position(figure.axes[0])
        low = sizes[(300.0, 300.0)][0]
        high = sizes[(700.0, 400.0)][0]
        offset = 30.0
        assert (high - offset) / (low - offset) == pytest.approx(4.0)
        # The raw ratio is not 4x, which is exactly why the offset must be removed first.
        assert high / low == pytest.approx(450.0 / 135.0)
        assert low == pytest.approx(135.0) and high == pytest.approx(450.0)
    finally:
        plt.close(figure)


def test_a_down_site_is_marked_twice_and_an_up_site_once() -> None:
    figure = render_scene_figure(_mixed_frame(), figsize=(6.0, 5.0), dpi=80)
    try:
        sizes = _sizes_by_position(figure.axes[0])
        assert sizes[(500.0, 500.0)] == [190.0]  # healthy site: one marker
        assert sizes[(600.0, 100.0)] == [190.0, 190.0]  # down site: square plus overstrike
    finally:
        plt.close(figure)


# --------------------------------------------------------------------------------------
# Provenance and text layout
# --------------------------------------------------------------------------------------


def test_the_synthetic_fixture_banner_appears_only_for_synthetic_data() -> None:
    synthetic = render_scene_figure(_mixed_frame(is_real=False), figsize=(6.0, 5.0), dpi=80)
    try:
        texts = [text.get_text() for text in synthetic.texts]
        assert _BANNER in texts
    finally:
        plt.close(synthetic)

    real = render_scene_figure(_mixed_frame(is_real=True), figsize=(6.0, 5.0), dpi=80)
    try:
        texts = [text.get_text() for text in real.texts]
        assert _BANNER not in texts
        assert not any("SYNTHETIC" in text for text in texts)
    finally:
        plt.close(real)


@pytest.mark.parametrize("is_real", [False, True])
def test_no_two_figure_level_texts_share_the_same_y(is_real: bool) -> None:
    figure = render_scene_figure(_mixed_frame(is_real=is_real), figsize=(6.0, 5.0), dpi=80)
    try:
        positions = [round(text.get_position()[1], 6) for text in figure.texts]
        assert len(positions) >= 3
        assert len(set(positions)) == len(positions), f"overprinted footer lines at {positions}"
    finally:
        plt.close(figure)


def test_the_footer_states_what_the_ground_markers_are() -> None:
    figure = render_scene_figure(_mixed_frame(), figsize=(6.0, 5.0), dpi=80)
    try:
        footer = [text.get_text() for text in figure.texts]
        assert any("AGGREGATE DEMAND POINTS" in line for line in footer)
        assert any("not people" in line for line in footer)
        assert any("marker AREA is proportional to offered demand" in line for line in footer)
        assert any("solid = carrying traffic" in line for line in footer)
        assert any("dotted = available, no traffic" in line for line in footer)
    finally:
        plt.close(figure)


def test_the_title_distinguishes_simulated_from_geometry_time() -> None:
    figure = render_scene_figure(_mixed_frame(), figsize=(6.0, 5.0), dpi=80)
    try:
        title = figure.axes[0].get_title()
        assert "sim t=12.5 s" in title
        assert "geometry t=12.0 s" in title
        assert "uav_service_restoration" in title
    finally:
        plt.close(figure)


def test_a_shared_altitude_is_stated_once_in_the_footer_not_per_marker() -> None:
    uavs = tuple(_uav(slot, (100.0 + 10.0 * slot, 100.0, 120.0)) for slot in range(4))
    figure = render_scene_figure(_scene(uavs=uavs), figsize=(6.0, 5.0), dpi=80)
    try:
        footer = " ".join(text.get_text() for text in figure.texts)
        assert "all UAVs at 120 m altitude" in footer
        labels = [annotation.get_text() for annotation in figure.axes[0].texts]
        assert labels == ["uav-0", "uav-1", "uav-2", "uav-3"]
        assert not any("120 m" in label for label in labels)
    finally:
        plt.close(figure)


def test_differing_altitudes_are_shown_per_marker() -> None:
    uavs = (
        _uav(0, (100.0, 100.0, 120.0)),
        _uav(1, (300.0, 300.0, 80.0)),
    )
    figure = render_scene_figure(_scene(uavs=uavs), figsize=(6.0, 5.0), dpi=80)
    try:
        labels = [annotation.get_text() for annotation in figure.axes[0].texts]
        assert labels == ["uav-0  120 m", "uav-1  80 m"]
        footer = " ".join(text.get_text() for text in figure.texts)
        assert "all UAVs at" not in footer
    finally:
        plt.close(figure)


def test_labels_in_a_dense_cluster_do_not_all_take_the_same_offset() -> None:
    """The greedy placer must separate labels that share an anchor region."""

    uavs = tuple(_uav(slot, (500.0 + 2.0 * slot, 500.0 + 2.0 * slot, 120.0)) for slot in range(6))
    figure = render_scene_figure(_scene(uavs=uavs), figsize=(6.0, 5.0), dpi=80)
    try:
        annotations = figure.axes[0].texts
        assert len(annotations) == 6
        offsets = {tuple(annotation.xyann) for annotation in annotations}
        assert len(offsets) > 1, "every label took the first candidate offset"
    finally:
        plt.close(figure)
