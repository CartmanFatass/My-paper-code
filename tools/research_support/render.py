"""Offscreen scene rendering for exports and programmatic tests.

Matplotlib with the ``Agg`` backend, selected **here** and nowhere else: a shared training
module must never import a backend, and this module is reached only from an export or a
test. There is no GUI event loop, no ``pyplot.show`` and no figure left open.

The renderer draws the same frame data the browser draws and applies the same three rules:
a missing value renders as missing, an available link is visually distinct from a carrying
one, and every status pairs a colour with a marker shape.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

_BACKEND_READY = False


def _ensure_backend() -> None:
    """Select Agg once, without fighting a backend the caller already chose."""

    global _BACKEND_READY
    if _BACKEND_READY:
        return
    import matplotlib

    current = matplotlib.get_backend().lower()
    if current not in ("agg", "module://matplotlib_inline.backend_inline"):
        matplotlib.use("Agg", force=True)
    _BACKEND_READY = True


#: Status -> (colour, matplotlib marker, filled). Colour is never the only difference.
STATUS_MARKERS: dict[str, tuple[str, str, bool]] = {
    "served": ("#1a7f5a", "o", True),
    "partially_served": ("#b07400", "D", False),
    "unserved": ("#b3261e", "X", True),
    "zero_demand": ("#9aa2b1", ".", True),
    "unknown_demand": ("#6d4c9f", "s", False),
    "unknown_service": ("#6d4c9f", "s", False),
    "associated_no_backhaul": ("#8a5a00", "P", False),
}

LINK_COLOURS = {
    "uav_access": "#2f8f6f",
    "site_access": "#2f8f6f",
    "uav_uav_backhaul": "#7a4fb5",
    "site_uav_backhaul": "#7a4fb5",
    "wired_core": "#444b58",
}


def _mval(measured: Mapping[str, Any] | None) -> float | None:
    if not measured or measured.get("validity") != "ok":
        return None
    value = measured.get("value")
    return None if value is None else float(value)


#: Candidate label offsets in points, tried in order. The first that does not collide with an
#: already-placed label wins; if all collide the label is placed at the first candidate anyway
#: (a slightly crowded label is better than a silently dropped one).
_LABEL_OFFSETS = (
    (10, 6), (10, -12), (-10, 6), (-10, -12),
    (10, 18), (10, -24), (-10, 18), (-10, -24),
)


class _LabelPlacer:
    """Greedy non-overlapping annotation placement in display (point) space.

    Dense scenes put six UAVs inside a few hundred metres, and fixed offsets made their
    labels overprint each other. Boxes are approximated from the character count and the
    font size, which is enough to separate labels without a draw-measure-redraw round trip.
    """

    def __init__(self, axes, figure) -> None:
        self._axes = axes
        self._figure = figure
        self._boxes: list[tuple[float, float, float, float]] = []

    def _point_of(self, x: float, y: float) -> tuple[float, float]:
        display = self._axes.transData.transform((x, y))
        scale = 72.0 / self._figure.dpi
        return display[0] * scale, display[1] * scale

    def place(self, x: float, y: float, text: str, *, fontsize: float, color: str,
              ha: str = "left") -> None:
        px, py = self._point_of(x, y)
        width = 0.58 * fontsize * len(text)
        height = 1.25 * fontsize
        chosen = _LABEL_OFFSETS[0]
        for dx, dy in _LABEL_OFFSETS:
            left = px + dx if dx >= 0 else px + dx - width
            box = (left, py + dy - height * 0.25, left + width, py + dy + height * 0.75)
            if not any(
                box[0] < other[2] and other[0] < box[2]
                and box[1] < other[3] and other[1] < box[3]
                for other in self._boxes
            ):
                chosen = (dx, dy)
                self._boxes.append(box)
                break
        else:
            left = px + chosen[0]
            self._boxes.append(
                (left, py + chosen[1] - height * 0.25, left + width, py + chosen[1] + height * 0.75)
            )
        # A translucent halo keeps a label readable where it lands on a marker or a link.
        self._axes.annotate(
            text, (x, y), textcoords="offset points", xytext=chosen,
            ha="right" if chosen[0] < 0 else ha, fontsize=fontsize, color=color, zorder=9,
            bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "alpha": 0.72,
                  "edgecolor": "none"},
        )


def render_scene_figure(frame: Mapping[str, Any], *, figsize=(9.0, 7.2), dpi: int = 110):
    """Build a Matplotlib figure for one scene frame. The caller closes it."""

    _ensure_backend()
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=figsize, dpi=dpi)
    axes = figure.add_subplot(111)
    geometry = frame.get("geometry") or {}
    bounds = geometry.get("bounds_m") or [0, 0, 1000, 1000]
    axes.set_xlim(bounds[0], bounds[2])
    axes.set_ylim(bounds[1], bounds[3])
    # Equal metric aspect is mandatory: a metre right must equal a metre up.
    axes.set_aspect("equal", adjustable="box")
    axes.set_xlabel("x (m)")
    axes.set_ylabel("y (m)")
    axes.grid(True, linewidth=0.4, alpha=0.35)

    positions: dict[str, tuple[float, float]] = {}
    for section in ("uavs", "ground_entities", "sites"):
        for item in frame.get(section) or ():
            positions[item["entity"]["key"]] = (
                float(item["position_m"][0]),
                float(item["position_m"][1]),
            )

    # Links: dotted thin for available, solid and utilization-scaled for carrying.
    for link in frame.get("links") or ():
        source = positions.get(link["source"])
        target = positions.get(link["target"])
        if source is None or target is None:
            continue
        active = link.get("activity") == "active"
        colour = LINK_COLOURS.get(link.get("link_class"), "#737b8c")
        if active:
            utilization = _mval(link.get("utilization"))
            width = 1.0 + 3.0 * (0.0 if utilization is None else min(1.0, max(0.0, utilization)))
            axes.plot(
                [source[0], target[0]], [source[1], target[1]],
                color=colour, linewidth=width, alpha=0.9, solid_capstyle="round", zorder=2,
            )
        else:
            axes.plot(
                [source[0], target[0]], [source[1], target[1]],
                color="#9aa2b1", linewidth=0.7, alpha=0.4, linestyle=(0, (1, 4)), zorder=1,
            )

    # Ground entities. Marker AREA is proportional to offered demand.
    offered_values = [
        _mval(g.get("offered_mbps")) for g in frame.get("ground_entities") or ()
    ]
    finite = [v for v in offered_values if v is not None]
    max_offered = max(finite) if finite else 0.0
    for entity in frame.get("ground_entities") or ():
        x, y = positions[entity["entity"]["key"]]
        offered = _mval(entity.get("offered_mbps"))
        colour, marker, filled = STATUS_MARKERS.get(
            entity.get("service_status"), ("#737b8c", "o", False)
        )
        if offered is None or max_offered <= 0:
            area = 45.0
        else:
            area = 30.0 + 420.0 * (offered / max_offered)
        axes.scatter(
            [x], [y], s=area, marker=marker,
            facecolors=colour if filled else "none", edgecolors=colour,
            linewidths=1.3, zorder=4,
        )

    placer = _LabelPlacer(axes, figure)
    for site in frame.get("sites") or ():
        x, y = positions[site["entity"]["key"]]
        down = site.get("radio_up") is False or site.get("core_link_up") is False
        axes.scatter(
            [x], [y], s=190, marker="s",
            facecolors="none" if down else "#444b58",
            edgecolors="#b3261e" if down else "#444b58",
            linewidths=2.0 if down else 1.0, zorder=5,
        )
        if down:
            axes.scatter([x], [y], s=190, marker="x", color="#b3261e", linewidths=2.0, zorder=6)
        placer.place(
            x, y, site["entity"].get("label") or site["entity"]["key"],
            fontsize=8, color="#4a5160",
        )

    uavs = list(frame.get("uavs") or ())
    altitudes = [round(float(u["position_m"][2]), 1) for u in uavs]
    # A shared altitude belongs in the footer once, not beside every marker; repeating it in a
    # dense cluster is what pushed the labels into each other.
    common_altitude = altitudes[0] if altitudes and len(set(altitudes)) == 1 else None
    for uav in uavs:
        x, y = positions[uav["entity"]["key"]]
        axes.scatter([x], [y], s=150, marker="^", color="#1f5f9e", zorder=7)
        label = uav["entity"].get("label") or uav["entity"]["key"]
        if common_altitude is None:
            label = f"{label}  {float(uav['position_m'][2]):.0f} m"
        placer.place(x, y, label, fontsize=8, color="#16181d")

    clock = frame.get("clock") or {}
    provenance = frame.get("provenance") or {}
    identity = frame.get("identity") or {}
    axes.set_title(
        f"{provenance.get('environment_id', 'scene')}  |  "
        f"sim t={clock.get('simulation_time_s')} s  geometry t={clock.get('geometry_time_s')} s",
        fontsize=10,
    )
    subtitle = (
        f"run {identity.get('run_id')} | episode {identity.get('episode_id')} | "
        f"lane {identity.get('lane_id')} | seq {identity.get('sequence')} | "
        f"{provenance.get('source_kind')} / {provenance.get('policy_kind')}"
    )
    # Each footer line gets its own height. Joining them onto one line overprinted the
    # provenance string and ran the demand-point caption off the right edge.
    legend_line = "solid = carrying traffic    dotted = available, no traffic"
    if common_altitude is not None:
        legend_line += f"    |    all UAVs at {common_altitude:g} m altitude"
    footer = [subtitle, legend_line]
    capability = frame.get("capability") or {}
    if capability.get("has_aggregate_demand"):
        footer.append(
            "ground markers are AGGREGATE DEMAND POINTS (one per source grid cell), not "
            "people; marker AREA is proportional to offered demand"
        )
    elif capability.get("has_individual_ues"):
        footer.append(
            "ground markers are individual simulated UEs; this route carries no modelled "
            "traffic demand, so no per-UE rate is shown"
        )
    line_height = 0.019
    top = 0.012 + line_height * (len(footer) - 1)
    for index, line in enumerate(footer):
        figure.text(
            0.01, top - index * line_height, line,
            fontsize=7.5, color="#737b8c" if index == 0 else "#4a5160",
        )
    if not provenance.get("is_real_activity_data", False):
        figure.text(
            0.5, 0.972,
            "SYNTHETIC ENGINEERING FIXTURE - NOT AN ALGORITHM RESULT",
            ha="center", fontsize=9.5, color="#b3261e", weight="bold",
        )
    figure.tight_layout(rect=(0, 0.024 + line_height * len(footer), 1, 0.955))
    return figure


def render_scene_rgb(frame: Mapping[str, Any], *, figsize=(9.0, 7.2), dpi: int = 110) -> np.ndarray:
    """Render one frame to an ``(H, W, 3)`` ``uint8`` array.

    This is the programmatic path a test or an exporter uses; it advertises exactly the
    shape and dtype a ``render_mode='rgb_array'`` consumer expects.
    """

    _ensure_backend()
    import matplotlib.pyplot as plt

    figure = render_scene_figure(frame, figsize=figsize, dpi=dpi)
    try:
        canvas = figure.canvas
        canvas.draw()
        buffer = np.asarray(canvas.buffer_rgba(), dtype=np.uint8)
        return np.ascontiguousarray(buffer[:, :, :3])
    finally:
        plt.close(figure)
