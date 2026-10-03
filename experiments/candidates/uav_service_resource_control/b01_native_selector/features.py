"""B01 lawful pre-search context: fixed scales, FP64 edges, FP32 network input."""
from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_positions, energy_uav_records, station_records,
    E_BATTERY, E_MARGIN, E_CHARGING, E_AVAILABLE, E_RETURNING, E_DOCK, E_WAITING,
)
from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.energy import (
    bump, flight_edge, target_return,
)

FEATURE_COUNT = FEATURE_DIM = 327
FEATURE_SLICES = dict(uavs=slice(0, 208), stations=slice(208, 222),
                      bs=slice(222, 229), users=slice(229, 319), global_=slice(319, 327))
UAV_FIELDS = (
    "x", "y", "z", "battery", "return_margin", "previous_F", "charging",
    "available", "returning", "dock", "waiting", "role_missing", "role_relay",
    "role_service", "role_ring", "target_valid", "target_x", "target_y",
    "previous_target_valid", "previous_target_x", "previous_target_y",
    "edge_valid", "arrival_ticks", "flight_wh", "return_wh", "slack",
)
BS_SOURCES = ("observed-current", "observed-memory", "inferred", "absent")
FEATURE_SPEC = dict(dim=327, dtype="float32", horizon=3000,
    uav_fields=UAV_FIELDS, bs_sources=BS_SOURCES,
    fields=[dict(name=k, start=v.start, stop=v.stop) for k, v in FEATURE_SLICES.items()])


def _finite(value, shape, label):
    value = np.asarray(value, dtype=np.float64)
    if value.shape != shape or not np.isfinite(value).all():
        raise ValueError(label + " must be finite with shape " + str(shape))
    return value


def target_payload(value):
    """Only an all-NaN XY row is missing; partial NaNs/infinities are errors."""
    value = np.asarray(value, dtype=np.float64)
    if value.shape != (8, 2):
        raise ValueError("targets must have shape (8,2)")
    valid = np.isfinite(value).all(axis=1)
    if not np.all(valid | np.isnan(value).all(axis=1)):
        raise ValueError("malformed missing target")
    return valid, np.where(valid[:, None], value, 0.)


def lawful_context(observations, layout, *, ordinary_targets, previous_targets,
                   roles, modes, users, bs_xy, bs_source, law, counters=None):
    """Decode legal fields and evaluate only each eligible member's owned edge.

    This function has no candidate, tracker, native-state or model argument.
    The returned FP64 edge values also supply literal ordinary-rule comparisons.
    """
    observations = _finite(observations, (8, layout.dim), "legal observations")
    bump(counters, "feature_own_position_decodes")
    xyz = _finite(own_positions(observations, layout), (8, 3), "own positions")
    bump(counters, "feature_energy_decodes")
    records = energy_uav_records(observations, layout)[np.arange(8), np.arange(8)]
    energy = _finite(records, (8, 13), "own energy records")
    for field in (E_CHARGING, E_AVAILABLE, E_RETURNING, E_DOCK):
        if not np.isin(energy[:, field], (0., 1.)).all():
            raise ValueError("malformed own energy bit")
    modes = np.asarray(modes)
    roles = np.asarray(roles)
    if modes.shape != (8,) or modes.dtype != np.dtype(bool):
        raise ValueError("previous F must be eight boolean bits")
    if roles.shape != (8,) or roles.dtype.kind not in "iu" or not np.isin(roles, range(4)).all():
        raise ValueError("invalid assignment roles")
    valid, targets = target_payload(ordinary_targets)
    previous_valid, previous = target_payload(previous_targets)
    eligible = ~modes & (roles == 2) & valid
    m = int(eligible.sum())
    if m > 6:
        raise ValueError("ordinary C assigned more than six service members")
    users = np.asarray(users, dtype=np.float64)
    if users.ndim != 2 or users.shape[1:] != (2,) or len(users) > 30 or not np.isfinite(users).all():
        raise ValueError("canonical users must contain at most30finite XY rows")
    if bs_source not in BS_SOURCES or ((bs_xy is None) != (bs_source == "absent")):
        raise ValueError("inconsistent lawful BS provenance")
    bs = np.zeros(2) if bs_xy is None else _finite(bs_xy, (2,), "lawful BS")
    bump(counters, "feature_station_decodes")
    station = station_records(observations, layout)
    station_xyz = _finite(station["xyz_m"][0], (2, 3), "observer0 stations")
    if not np.all(station["valid"][0]):
        raise ValueError("both observer0 stations must be valid")
    capacity = _finite(station["capacity_ratio"][0], (2,), "station capacity")
    if not np.array_equal(capacity, np.full(2, 1. / 8.)):
        raise ValueError("B01 station capacity must be [1,1]")
    station_payload = np.column_stack((station_xyz / [8000., 8000., 200.], capacity,
        _finite(station["available_ratio"][0], (2,), "station availability"),
        _finite(station["queue_ratio"][0], (2,), "station queue"), np.ones(2)))
    edges = np.zeros((8, 5), dtype=np.float64)
    return_station = np.full(8, -1, dtype=np.int8)
    for member in np.flatnonzero(eligible):
        target = np.r_[targets[member], 100.]
        station_id, wh = target_return(target, station_xyz, law, counters=counters)
        ticks, fly_wh, slack = flight_edge(xyz[member], target, energy[member, E_BATTERY],
                                         wh, law, counters=counters)
        edges[member] = 1., ticks, fly_wh, wh, slack
        return_station[member] = station_id
    minimum = float(np.min(edges[eligible, 4])) if m else 0.
    return dict(xyz=xyz, energy=energy.copy(), modes=modes.copy(), roles=roles.copy(),
        targets=targets, target_valid=valid, previous_targets=previous,
        previous_target_valid=previous_valid, eligible=eligible, m=m,
        h_eligible=bool(m >= 2 and bs_xy is not None), edges=edges,
        return_station=return_station, min_slack=minimum, min_slack_valid=bool(m),
        stations=station_payload, bs_xy=bs, bs_valid=bs_xy is not None,
        bs_source=bs_source, users=users.copy())


def pack_features(context, *, step, previous_action=None, same_choice_count=0):
    """Network layout exactly matches the B01 source contract's six blocks."""
    if (isinstance(step, (bool, np.bool_)) or not isinstance(step, (int, np.integer))
            or step not in range(0, 3000, 30)):
        raise ValueError("pre-search step must be a mission planning boundary")
    if previous_action not in (None, 0, 1) or same_choice_count < 0:
        raise ValueError("invalid previous-choice history")
    if (previous_action is None) != (same_choice_count == 0):
        raise ValueError("previous choice and streak differ")
    c, e = context, context["energy"]
    own = np.column_stack((c["xyz"][:, :2] / 8000., (c["xyz"][:, 2] - 50.) / 150.,
        e[:, E_BATTERY], e[:, E_MARGIN], c["modes"], e[:, E_CHARGING],
        e[:, E_AVAILABLE], e[:, E_RETURNING], e[:, E_DOCK],
        np.rint(e[:, E_WAITING] * 3000.) / 3000., np.eye(4)[c["roles"]],
        c["target_valid"], c["targets"] / 8000., c["previous_target_valid"],
        c["previous_targets"] / 8000.,
        c["edges"] / np.array([1., 3000., 160., 160., 1.])))
    users = np.zeros((30, 3), dtype=np.float64)
    users[:len(c["users"]), :2] = c["users"] / 8000.
    users[:len(c["users"]), 2] = 1.
    bs = np.r_[c["bs_xy"] / 8000., c["bs_valid"],
               np.eye(4)[BS_SOURCES.index(c["bs_source"])]]
    global_values = [step / 3000., previous_action is not None,
        0 if previous_action is None else previous_action, same_choice_count / 100.,
        c["m"] / 6., c["h_eligible"], c["min_slack"], c["min_slack_valid"]]
    result = np.concatenate((own.ravel(), c["stations"].ravel(), bs,
                             users.ravel(), global_values)).astype(np.float32)
    if result.shape != (327,) or not np.isfinite(result).all():
        raise ValueError("nonfinite or malformed327 context")
    return result
