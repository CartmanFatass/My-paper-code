"""One replay per actual trajectory, plus independent recorded-state and endpoint checks."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import json
import math
import multiprocessing
from pathlib import Path
import resource
import time
import traceback

import numpy as np

from experiments.candidates.energy_relay_availability.runner import execute_bounded
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    TRACE_FIELDS, absolute_station_xy, mechanism_row, position_diagnostics,
    station_counts, world_row,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS, apply_feedback_params
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT, own_energy, own_positions
from experiments.candidates.uav_information_value.b02.controller import StationPriorController

from .capture import memory_record, plan_record
from .contract import (
    ARMS, HORIZON, OBJECT, SAMPLES, array_digest, equal, expected_counts, identity, jobs,
    source_binding, sum_counts, telemetry, write_json,
)
from .controller import ReplayBoundary, make_controller
from .trace import CANDIDATE_DTYPE
from .metrics import comparisons, episode_metrics


class UnavailableTruth:
    """The offline policy gets no central-state array, just as its source promises."""
    def __getattribute__(self, name):
        raise AssertionError("policy attempted central-state access: " + name)

    def __array__(self, *unused, **kwargs):
        raise AssertionError("policy attempted central-state conversion")


def numeric_row_equal(actual, expected, prefix):
    for key, value in expected.items():
        if isinstance(value, dict):
            numeric_row_equal(actual[key], value, prefix + "/" + key)
        elif value is None or isinstance(value, str):
            if actual[key] != value:
                raise AssertionError(prefix + "/" + key)
        else:
            equal(actual[key], value, prefix + "/" + key, 1e-9)


def power(v_xy, v_z, p):
    return (p["P0"] * (1 + p["k1"] * v_xy ** 2)
            + p["Pi"] * np.sqrt(np.maximum(0., np.sqrt(1 + v_xy ** 4 / (4 * p["v0"] ** 4))
                                                   - v_xy ** 2 * p["k2"]))
            + p["k3"] * v_xy ** 3 + p["P_z_coeff"] * np.abs(v_z))


def check_native(raw, row, phase):
    n = row["actual_length"]
    if n < 1 or n > row["limit"]:
        raise AssertionError("invalid native length")
    shapes = dict(observations=(n + 1, 8, 365), truth_user_xyz=(n + 1, 30, 3),
                  truth_uav_xyz=(n + 1, 8, 3), proposed=(n, 8, 4), submitted=(n, 8, 4),
                  native_battery=(n + 1, 8), reward=(n,), native_reward=(n,), ends=(n, 2),
                  native_ends=(n, 2), metrics=(n, len(TRACE_FIELDS)), native_connections=(n + 1, 8, 30),
                  native_peer_connections=(n + 1, 8, 8), native_bs_connections=(n + 1, 8, 1),
                  native_routes=(n + 1, 8, 9), native_demand_bps=(n + 1, 30),
                  native_delivered_bps=(n + 1, 30), native_access_bps=(n + 1, 8, 30))
    for key, shape in shapes.items():
        if raw[key].shape != shape or not np.isfinite(raw[key]).all():
            raise AssertionError("native shape/nonfinite: " + key)
    for key in ("observations", "proposed", "submitted"):
        if raw[key].dtype != np.float32:
            raise AssertionError("FP32 legal input/action contract")
    for key in ("truth_user_xyz", "truth_uav_xyz", "native_battery", "native_reward"):
        if raw[key].dtype != np.float64:
            raise AssertionError("FP64 native diagnostic contract")
    if any(value.dtype.kind == "O" for value in raw.values()):
        raise AssertionError("object arrays forbidden")
    equal(raw["recorded_native_steps"], n, "observed native steps")
    equal(raw["recorded_decision_steps"], n, "recorded actual decisions")
    equal(raw["metric_fields"], TRACE_FIELDS, "metric field order")
    equal(raw["reward"], raw["native_reward"], "adapter reward capture")
    if raw["native_ends"][:-1].any():
        raise AssertionError("native execution continued past termination")
    if phase == "scientific":
        equal(raw["ends"], raw["native_ends"], "native end flags")
        if not raw["native_ends"][-1].any():
            raise AssertionError("missing native terminal/truncation")
    else:
        equal(n, 61, "engineering native prefix")
        equal(raw["ends"][:-1], raw["native_ends"][:-1], "engineering pre-stop flags")
        equal(raw["ends"][-1], [raw["native_ends"][-1, 0], True], "explicit harness stop")
    p = row["native_parameters"]
    if p["time_step"] != 1. or p["max_steps"] != HORIZON or p["battery_capacity_wh"] != 160.:
        raise AssertionError("fixed native time/energy parameters")
    xyz = raw["truth_uav_xyz"]
    normalized = xyz.copy()
    normalized[..., :2] /= 8000.
    normalized[..., 2] = (normalized[..., 2] - 50.) / 150.
    equal(raw["observations"][:-1, :, :3], normalized[:-1].astype(np.float32), "lawful own position")
    # Terminal row padding is permitted by the original adapter, and is never acted on.
    nonpadding = np.any(raw["observations"][-1] != 0., axis=1)
    equal(raw["observations"][-1, nonpadding, :3], normalized[-1, nonpadding].astype(np.float32),
          "terminal own position or explicit adapter padding")
    equal(raw["observations"][:-1, :, S7S2_LAYOUT.step],
          np.broadcast_to((np.arange(n) / HORIZON).astype(np.float32)[:, None], (n, 8)), "native input clock")
    if (np.any(xyz[..., :2] < 0) or np.any(xyz[..., :2] > 8000) or np.any(xyz[..., 2] < 50.)
            or np.any(xyz[..., 2] > 200.) or raw["native_failed"].any()):
        raise AssertionError("arena or fault-free contract")
    equal(np.diff(xyz, axis=0), raw["native_velocity"][1:], "native actual motion", 1e-12)
    velocity = raw["native_velocity"][1:]
    energy = power(np.linalg.norm(velocity[..., :2], axis=-1), velocity[..., 2], p) / 3600.
    equal(raw["native_consumed_wh"][1:], energy, "native propulsion from actual motion", 1e-12)
    # Keep sequential subtract/add rounding rather than collapsing the update algebra.
    battery = raw["native_battery"][:-1] - raw["native_consumed_wh"][1:] / 160.
    battery += raw["native_charged_wh"][1:] / 160.
    equal(raw["native_battery"][1:], np.clip(battery, 0., 1.), "native battery recurrence", 1e-14)
    equal(raw["native_net_charged_wh"][1:],
          np.maximum(0., raw["native_charged_wh"][1:] - raw["native_consumed_wh"][1:]), "net charging", 1e-14)
    equal(raw["native_charging"][1:], raw["native_charged_wh"][1:] > 0., "actual charging flag")
    if np.any(raw["native_station_occupancy"] > np.asarray(p["station_capacity"])[None]):
        raise AssertionError("station capacity exceeded")
    equal(raw["native_demand_bps"], np.full((n + 1, 30), 1e6), "fixed offered demand")
    rates_bps = raw["native_user_rates_mbps"][1:] * 1e6
    delivered = raw["native_delivered_bps"][1:]
    equal(delivered, np.minimum(rates_bps, 1e6), "delivered traffic native rate/demand bound", 1e-7)
    if np.any(delivered < 0) or np.any(raw["native_access_bps"] < 0):
        raise AssertionError("negative native service/capacity")
    fields = {str(name): k for k, name in enumerate(raw["metric_fields"])}
    m = raw["metrics"]
    equal(m[:, fields["qos_satisfaction_ratio"]], np.mean(delivered / 1e6, axis=1), "native QoS reduction", 1e-14)
    equal(m[:, fields["delivered_end_to_end_throughput_mbps"]], delivered.sum(axis=1) / 1e6,
          "native delivered throughput", 1e-12)
    expected_j = (m[:, fields["qos_satisfaction_ratio"]] - 2. * m[:, fields["return_constraint_cost"]]
                  - m[:, fields["cutoff_event_penalty"]] - m[:, fields["depletion_event_penalty"]]
                  + m[:, fields["graph_potential_delta"]])
    equal(raw["reward"], expected_j, "native J decomposition", 1e-12)
    equal(m[:, fields["return_penalty_coefficient"]], np.full(n, 2.), "unreweighted return cost")
    scalar = {str(name): raw["reward_scalars"][:, k] for k, name in enumerate(raw["reward_scalar_fields"])}
    for field, column in fields.items():
        equal(m[:, column], scalar[field], "metric/scalar binding: " + field)
    next_potential = np.where(raw["native_ends"].any(axis=1), 0., scalar["graph_potential"])
    equal(scalar["graph_potential_delta"], p["reward_discount_gamma"] * next_potential
          - scalar["graph_potential_before"], "native potential and terminal handling", 1e-12)
    equal(scalar["step_propulsion_energy_wh"], raw["native_consumed_wh"][1:].sum(axis=1), "team propulsion", 1e-12)
    equal(scalar["step_charger_input_wh"], raw["native_charged_wh"][1:].sum(axis=1), "charger input", 1e-12)
    equal(scalar["battery_min_ratio"], raw["native_battery"][1:].min(axis=1), "minimum battery")
    check_routes(raw)
    check_individual_summaries(raw, row)
    return dict(native_transitions_checked=n, native_agent_motion_ticks=n * 8,
                terminal_padding_rows=int((~nonpadding).sum()), full_rf_resimulation=False,
                new_native_steps=0, extra_model_queries=0, extra_allocator_queries=0)



def longest_reference(flags):
    best = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        best = max(best, current)
    return best


def check_individual_summaries(raw, row):
    """Validate DM-owned summaries directly against already checked native data."""
    delivered = raw["native_delivered_bps"][1:]
    demand = raw["native_demand_bps"][1:]
    n = len(delivered)
    service = row["individual_service"]
    equal(service["native_user_index"], np.arange(30), "individual native user order")
    equal(service["observed_steps"], n, "individual observed horizon")
    equal(service["planned_horizon"], HORIZON, "individual planned horizon")
    equal(service["time_step_seconds"], 1., "individual elapsed step")
    if service["outage_scope"] != "observed native steps only; no imputed termination suffix":
        raise AssertionError("individual outage suffix scope")
    satisfaction = np.clip(delivered / demand, 0., 1.)
    qos = np.array([math.fsum(map(float, satisfaction[:, j])) for j in range(30)])
    zero = (delivered == 0).sum(axis=0)
    spells = np.array([longest_reference(delivered[:, j] == 0) for j in range(30)])
    equal(service["delivered_megabits"], [math.fsum(map(float, delivered[:, j])) / 1e6 for j in range(30)],
          "individual delivered megabits", 1e-9)
    for name, values in (("cumulative_qos_seconds", qos), ("qos_per_planned_step", qos/HORIZON),
                         ("qos_per_actual_step", qos/n), ("observed_zero_delivery_steps", zero),
                         ("longest_observed_zero_delivery_spell", spells)):
        equal(service[name], values, "individual service/" + name, 1e-9)
    for name, value in dict(user_cumulative_qos_minimum=qos.min(),
         user_cumulative_qos_p10=np.quantile(qos, .1), user_qos_per_planned_step_minimum=qos.min()/HORIZON,
         user_qos_per_planned_step_p10=np.quantile(qos, .1)/HORIZON,
         user_qos_per_actual_step_minimum=qos.min()/n, user_zero_delivery_steps=zero.sum(),
         user_longest_zero_delivery_spell=spells.max(), users_without_any_delivery=np.count_nonzero(qos == 0)).items():
        equal(row[name], value, "individual service tail/" + name, 1e-9)
    energy = row["individual_uav_energy"]
    equal(energy["native_uav_index"], np.arange(8), "individual native UAV order")
    battery = raw["native_battery"][1:]
    cutoff = battery <= .02
    charging = raw["native_charging"][1:]
    waits = raw["native_waiting"][1:]
    travel = np.linalg.norm(np.diff(raw["truth_uav_xyz"], axis=0), axis=2)
    for name, values in (("travel_m", travel.sum(axis=0)),
         ("consumed_wh", raw["native_consumed_wh"][1:].sum(axis=0)),
         ("charged_wh", raw["native_charged_wh"][1:].sum(axis=0)),
         ("net_charged_wh", raw["native_net_charged_wh"][1:].sum(axis=0)),
         ("minimum_battery_ratio", battery.min(axis=0)), ("final_battery_ratio", battery[-1]),
         ("post_step_reserve_steps", (battery <= .1).sum(axis=0)),
         ("post_step_cutoff_steps", cutoff.sum(axis=0)), ("charging_steps", charging.sum(axis=0)),
         ("maximum_waiting_steps", waits.max(axis=0)),
         ("longest_post_step_cutoff_spell", [longest_reference(cutoff[:, j]) for j in range(8)]),
         ("longest_charging_spell", [longest_reference(charging[:, j]) for j in range(8)])):
        equal(energy[name], values, "individual UAV/" + name, 1e-9)
    for name, value in dict(native_cutoff_uav_steps=cutoff.sum(),
         longest_post_step_cutoff_spell=max(longest_reference(cutoff[:, j]) for j in range(8)),
         maximum_charging_wait_steps=waits.max(),
         longest_charging_spell=max(longest_reference(charging[:, j]) for j in range(8))).items():
        equal(row[name], value, "individual UAV tail/" + name)

def check_routes(raw):
    # Native widest paths use positive directed capacities. The separately recorded
    # connection masks require both directions, so they cannot validate a route edge.
    # Routes also precede the energy update; do not impose post-update availability.
    # These are checks of recorded native outputs, not additional RF/model queries.
    for tick in range(len(raw["native_routes"])):
        for member, path in enumerate(raw["native_routes"][tick]):
            nodes = path[path >= 0]
            if len(nodes):
                if (nodes[0] != member or nodes[-1] != 8 or len(set(nodes)) != len(nodes)
                        or np.any(nodes > 8) or raw["native_route_capacity"][tick, member] <= 0):
                    raise AssertionError("native route topology")


def bind_slots(raw, tick):
    """Original contemporaneous radius/stable-distance order, independently of track predictions."""
    obs = raw["observations"][tick]
    own, users = raw["truth_uav_xyz"][tick], raw["truth_user_xyz"][tick]
    records = obs[:, S7S2_LAYOUT.users].reshape(8, 30, 6)
    ids = np.full((8, 30), -1, dtype=np.int16)
    silent = 0
    for member in range(8):
        # Match the source's per-pair norm and stable user-index tie order exactly.
        distances = np.asarray([np.linalg.norm(own[member] - point) for point in users])
        order = np.argsort(distances, kind="stable")
        visible = order[distances[order] <= 1500.]
        width = len(visible)
        if width:
            equal(records[member, :width, :2], ((users[visible, :2] - own[member, :2]) / 8000.).astype(np.float32),
                  "original user-slot relative position")
            equal(records[member, :width, 3], raw["native_connections"][tick, member, visible].astype(np.float32),
                  "original slot own-connection field")
            equal(records[member, :width, 4], raw["native_serviced"][tick, visible].astype(np.float32),
                  "original slot serviced field")
            equal(records[member, :width, 5], (raw["native_serving_set_count"][tick, visible] / 3.).astype(np.float32),
                  "original slot serving-set field")
            present = np.any(records[member, :width] != 0., axis=1)
            ids[member, :width] = np.where(present, visible, -1)
            silent += int((~present).sum())
        equal(records[member, width:], np.zeros_like(records[member, width:]), "original absent user slots")
    if np.any((records[..., 2] < 0) | (records[..., 2] > 1)):
        raise AssertionError("normalized legal SINR out of range")
    return ids, silent


class IdentityReading:
    def __init__(self):
        self.bindings = {}
        self.last_birth = np.full(30, -1, dtype=np.int64)
        self.counts = dict(slot_records=0, silent_true_slots=0, current_points=0, bound_current_points=0,
                           ambiguous_current_points=0, unbound_current_points=0, continuation_events=0,
                           singleton_continuations=0, identity_switches=0, births=0,
                           singleton_births=0, reidentified_births=0, duplicate_bound_track_times=0,
                           forecast_origins=0, forecast_bound=0, forecast_ambiguous=0, forecast_unbound=0,
                           forecast_future_censored=0, forecast_evaluated=0, forecast_nonzero_velocity=0,
                           forecast_remembered=0)
        self.forecasts = {str(tau): empty_forecast_stats() for tau in SAMPLES}

    def step(self, raw, tick, trace, slots, plan_index, arm):
        counts = self.counts
        current_count = int(raw["trace_current_count"][tick])
        tracks = trace["tracks"]
        mapping = trace["raw_to_canonical"]
        kept = trace["kept_flat_indices"]
        present = slots >= 0
        equal(mapping >= 0, present, "canonical raw-slot presence provenance")
        if np.any(mapping[present] >= current_count):
            raise AssertionError("invalid canonical provenance index")
        canonical = trace["canonical_xy"]
        if current_count:
            equal(mapping.reshape(-1)[kept], np.arange(current_count), "kept raw slots map to themselves")
            equal(tracks["last_xy"][:current_count], canonical, "current canonical prefix")
        continued = set(map(int, trace["events"]["continued"]))
        new = set(map(int, trace["events"]["new"]))
        bindings = {}
        for index, track in enumerate(tracks):
            birth = int(track["birth"])
            if index < current_count:
                native = frozenset(map(int, slots[mapping == index])) - {-1}
                counts["current_points"] += 1
                counts["bound_current_points" if len(native) == 1 else
                       "ambiguous_current_points" if len(native) > 1 else "unbound_current_points"] += 1
                old = self.bindings.get(birth, frozenset())
                if birth in continued:
                    counts["continuation_events"] += 1
                    if len(native) == len(old) == 1:
                        counts["singleton_continuations"] += 1
                        counts["identity_switches"] += int(native != old)
                if birth in new:
                    counts["births"] += 1
                    if len(native) == 1:
                        counts["singleton_births"] += 1
                        user = next(iter(native))
                        counts["reidentified_births"] += int(self.last_birth[user] >= 0 and self.last_birth[user] != birth)
                for user in native:
                    if len(native) == 1:
                        self.last_birth[user] = birth
            else:
                native = self.bindings[birth]
            bindings[birth] = native
        unique_users = [next(iter(ids)) for ids in bindings.values() if len(ids) == 1]
        counts["duplicate_bound_track_times"] += len(unique_users) - len(set(unique_users))
        self.bindings = bindings
        if plan_index is None or arm not in ("H", "F"):
            return
        for tau_index, tau in enumerate(SAMPLES):
            stats = self.forecasts[str(tau)]
            for index, track in enumerate(tracks):
                stats["origins"] += 1
                counts["forecast_origins"] += 1
                candidates = bindings[int(track["birth"])]
                if len(candidates) != 1:
                    name = "ambiguous" if candidates else "unbound"
                    stats[name] += 1
                    counts["forecast_" + name] += 1
                    continue
                stats["bound"] += 1
                counts["forecast_bound"] += 1
                if tick + tau >= len(raw["truth_user_xyz"]):
                    stats["censored"] += 1
                    counts["forecast_future_censored"] += 1
                    continue
                user = next(iter(candidates))
                truth = raw["truth_user_xyz"][tick + tau, user, :2]
                projected = raw["plan_prediction_xy"][plan_index, tau_index, index]
                current = raw["plan_users"][plan_index, index]
                if not np.isfinite(projected).all() or not np.isfinite(current).all():
                    raise AssertionError("nonfinite origin-bound forecast")
                error = float(np.linalg.norm(projected - truth))
                current_error = float(np.linalg.norm(current - truth))
                last_seen_error = float(np.linalg.norm(track["last_xy"] - truth))
                nonzero, remembered = bool(np.any(track["v"] != 0.)), not bool(track["current"])
                counts["forecast_evaluated"] += 1
                counts["forecast_nonzero_velocity"] += int(nonzero)
                counts["forecast_remembered"] += int(remembered)
                update_forecast_stats(stats, error, current_error, last_seen_error,
                    dict(t=tick, tau=tau, arm=arm, user=user, birth=int(track["birth"]),
                         age=tick-int(track["last_seen"]), nonzero_velocity=nonzero,
                         remembered=remembered, forecast_error_m=error,
                         current_error_m=current_error, last_seen_error_m=last_seen_error,
                         last_xy=track["last_xy"].tolist(), current_xy=current.tolist(),
                         forecast_xy=projected.tolist(), truth_xy=truth.tolist()))

    def result(self):
        return dict(counts=self.counts,
                    binding="origin birth; contemporaneous stable native slot order and actual merge provenance",
                    per_tau={key: finish_forecast_stats(value) for key, value in self.forecasts.items()},
                    combined=finish_forecast_stats(pool_forecast_stats(self.forecasts.values())))


def empty_forecast_stats():
    return dict(origins=0, bound=0, ambiguous=0, unbound=0, censored=0, evaluated=0,
                forecast_sum_m=0., forecast_sum_sq_m2=0., current_sum_m=0., current_sum_sq_m2=0.,
                last_seen_sum_m=0., last_seen_sum_sq_m2=0., better=0, worse=0, equal=0,
                nonzero_velocity=0, remembered=0, worst_rows=[])


def update_forecast_stats(stats, error, current_error, last_seen_error, row):
    stats["evaluated"] += 1
    for name, value in (("forecast", error), ("current", current_error), ("last_seen", last_seen_error)):
        stats[name + "_sum_m"] += value
        stats[name + "_sum_sq_m2"] += value * value
    stats["better" if error < current_error else "worse" if error > current_error else "equal"] += 1
    stats["nonzero_velocity"] += int(row["nonzero_velocity"])
    stats["remembered"] += int(row["remembered"])
    stats["worst_rows"] = sorted(stats["worst_rows"] + [row],
                                 key=lambda item: item["forecast_error_m"], reverse=True)[:5]


def pool_forecast_stats(items):
    result = empty_forecast_stats()
    worst = []
    for item in items:
        for key in result:
            if key != "worst_rows":
                result[key] += item[key]
        worst.extend(item["worst_rows"])
    result["worst_rows"] = sorted(worst, key=lambda row: row["forecast_error_m"], reverse=True)[:5]
    return result


def finish_forecast_stats(stats):
    result = dict(stats)
    n = stats["evaluated"]
    for name in ("forecast", "current", "last_seen"):
        result[name + "_mean_error_m"] = stats[name + "_sum_m"] / n if n else None
        result[name + "_rmse_m"] = math.sqrt(stats[name + "_sum_sq_m2"] / n) if n else None
    return result


def validate_candidate_records(raw, arm, complete):
    records = raw["candidate_records"]
    if records.ndim != 1 or records.dtype != CANDIDATE_DTYPE:
        raise AssertionError("candidate structured dtype/shape")
    if arm not in ("H", "F") and len(records):
        raise AssertionError("unmodeled arm has candidate records")
    if (np.any(records["q"] < 1) or np.any(records["q"] > 30)
            or np.any(records["ticks"] < 0) or np.any(records["ticks"] > 30)
            or np.any(records["rf_completed"] < 0) or np.any(records["rf_started"] > 3)
            or np.any(records["rf_started"] < records["rf_completed"])
            or np.any(records["rf_started"] - records["rf_completed"] > 1)):
        raise AssertionError("candidate execution bounds")
    incomplete = np.flatnonzero(~records["completed"])
    if complete and len(incomplete):
        raise AssertionError("incomplete candidate in complete episode")
    if len(incomplete) and (len(incomplete) != 1 or incomplete[0] != len(records) - 1):
        raise AssertionError("incomplete candidate is not final prefix record")
    if np.any(records["completed"] & ((records["ticks"] != 30) | (records["rf_completed"] != 3))):
        raise AssertionError("completed candidate missing nominal/RF work")
    if np.any((records["rf_started"] > 0) & (records["ticks"] != 30)):
        raise AssertionError("RF precedes completed nominal forecast")
    last_step, local = -1, 0
    for record in records:
        step = int(record["step"])
        if step < last_step or step % 30 or step < 0:
            raise AssertionError("candidate clock/order")
        local = local + 1 if step == last_step else 0
        if int(record["index"]) != local or local >= 100:
            raise AssertionError("candidate local index/order")
        if not np.isfinite(record["targets"]).all():
            raise AssertionError("candidate target nonfinite")
        last_step = step
    return records


def compare_candidate_prefix(actual, recorded, *, unverified_ranking_step=None):
    if actual.shape != recorded.shape or actual.dtype != CANDIDATE_DTYPE:
        raise AssertionError("candidate actual prefix count/schema")
    for index, (left, right) in enumerate(zip(actual, recorded)):
        for name in CANDIDATE_DTYPE.names:
            if name in ("accepted", "selected") and int(right["step"]) == unverified_ranking_step:
                # A fully scored final query may not yet have returned to the
                # search. Preserve flags without inventing a rejection/selection.
                continue
            if name == "rf_started" and not right["completed"]:
                # Failed RF attempt has no computed output to repay. Completed
                # calls are replayed; the omitted interrupted attempt is reported.
                equal(left[name], right["rf_completed"], f"candidate {index}/replayed RF attempts")
            else:
                equal(left[name], right[name], f"candidate {index}/{name}")


def compare_records(raw, values, index, label):
    for name, value in values.items():
        if name not in raw or index >= len(raw[name]):
            raise AssertionError(label + "/missing " + name)
        equal(raw[name][index], value, label + "/" + name)



def replay_episode(raw, row, phase, progress=None):
    complete = row.get("status", "completed") == "completed"
    arm = row["arm"]
    records = validate_candidate_records(raw, arm, complete)
    unverified_ranking_step = None
    if not complete and len(records):
        step = int(records[-1]["step"])
        in_step = records["step"] == step
        if step not in raw.get("plan_step", []) and not records["selected"][in_step].any():
            unverified_ranking_step = step
    n = int(row["actual_length"] if complete else np.asarray(raw["recorded_decision_steps"]).item())
    if n < 0 or len(raw["observations"]) <= n:
        raise AssertionError("decision prefix lacks lawful boundary observations")
    controller = make_controller(arm)
    controller.reset()
    if arm in ("H", "F"):
        controller.replay_prefix = records
    modes, previous_done = np.zeros(8, dtype=bool), np.ones(1, dtype=bool)
    binding = IdentityReading()
    plan_index = verified = attempts = reference_lloyd = shield_attempts = 0
    boundary = None
    actual_counts = {}
    missing = set()

    def saved(name, index, value, label):
        if name not in raw:
            if complete:
                raise AssertionError(label + "/missing " + name)
            missing.add(name)
            return
        if index >= len(raw[name]):
            raise AssertionError(label + "/short " + name)
        equal(raw[name][index], value, label)

    def counts():
        if arm == "REFERENCE":
            return expected_counts(arm, verified) | {"proposals": attempts, "lloyd_solves": reference_lloyd}
        return dict(controller.counters)

    try:
        for tick in range(n):
            obs = raw["observations"][tick]
            attempts += 1
            try:
                proposal = controller.propose(obs, UnavailableTruth(), tick, previous_done, modes.copy())
            except ReplayBoundary as error:
                raise AssertionError("boundary inside a recorded completed decision") from error
            equal(proposal, raw["proposed"][tick], "actual-path proposed commands")
            saved("target_xy", tick, controller.targets_xy, "actual held targets")
            targets_xyz = getattr(controller, "targets_xyz", None)
            if targets_xyz is None:
                targets_xyz = np.column_stack((controller.heuristic.targets_xy, np.full(8, 100.0)))
            saved("decision_targets_xyz", tick, targets_xyz, "actual held xyz targets")
            shield_attempts += 1
            decision = apply_feedback_params(obs, proposal, modes, PRODUCTION_PARAMS)
            for name, value in dict(submitted=decision.submitted_actions, mode=decision.modes,
                                    entered=decision.entered, exited=decision.exited,
                                    return_margin=decision.margins, nearest_station=decision.selected_stations,
                                    nearest_station_distance_m=decision.station_distances_m).items():
                saved(name, tick, value, "actual feedback: " + name)
            saved("own_xyz", tick, own_positions(obs), "decoded decision position")
            held = own_energy(obs)
            saved("station_occupancy", tick, station_counts(decision.selected_stations, held["charging"]),
                  "decision-time occupancy decode")
            saved("station_queue", tick, station_counts(decision.selected_stations, held["waiting_steps"] > 0),
                  "decision-time queue decode")
            post = own_energy(raw["observations"][tick + 1])
            for name in ("charging", "waiting_steps", "battery"):
                saved(name, tick, post[name], "post-step energy decode: " + name)
            saved("dock_bit", tick, decision.submitted_actions[:, 3] > .5, "dock command")
            current_plan = plan_index if tick % 30 == 0 else None
            if current_plan is not None:
                compare_records(raw, plan_record(controller, tick), plan_index, "actual plan")
                plan_index += 1
            slots, silent = bind_slots(raw, tick)
            binding.counts["slot_records"] += int(np.count_nonzero(slots >= 0))
            binding.counts["silent_true_slots"] += silent
            if arm in ("H", "F"):
                trace = controller.last_trace
                compare_records(raw, memory_record(trace), tick, "actual primitive memory")
                binding.step(raw, tick, trace, slots, current_plan, arm)
            modes = decision.modes
            previous_done[:] = raw.get("ends", raw["native_ends"])[tick].any()
            verified += 1
            if arm == "REFERENCE" and current_plan is not None:
                reference_lloyd += int(raw["plan_user_count"][current_plan] > 0)
            if progress is not None and verified % 100 == 0:
                progress(dict(verified=verified, policy_counts=counts()))
        # The recorder attaches decisions AFTER native transitions. An interrupted
        # replan can therefore exist at n without a saved decision/plan/track row.
        # Candidate records are the positive evidence permitting this single call.
        if not complete and len(records) and int(records[-1]["step"]) == n:
            attempts += 1
            try:
                proposal = controller.propose(raw["observations"][n], UnavailableTruth(), n,
                                              previous_done, modes.copy())
            except ReplayBoundary as error:
                boundary = str(error)
            else:
                # A full modeled search may have finished before capture/native
                # failed. Check its saved candidate outputs; do not invent an end.
                if len(raw.get("submitted", [])) > n:
                    shield_attempts += 1
                    decision = apply_feedback_params(raw["observations"][n], proposal, modes, PRODUCTION_PARAMS)
                    equal(decision.submitted_actions, raw["submitted"][n], "inflight actual submitted command")
        actual = controller.audit_arrays()["candidate_records"] if hasattr(controller, "audit_arrays") else np.empty(0, CANDIDATE_DTYPE)
        compare_candidate_prefix(actual, records, unverified_ranking_step=unverified_ranking_step)
        equal(plan_index, len(raw.get("plan_step", [])), "all and only captured actual plans")
        actual_counts = counts()
        if complete:
            fixed = expected_counts(arm, n)
            if any(actual_counts.get(key, 0) != value for key, value in fixed.items()):
                raise AssertionError("replay primitive accounting")
            if actual_counts != row["policy_counts"]:
                raise AssertionError("deployment/replay actual-work count mismatch")
            original = world_row(row["seed"], raw["reward"], raw["metrics"], raw["ends"], raw, time_step_s=1.)
            original.update(mechanism_row(raw, absolute_station_xy(raw["observations"][0])))
            original.update(position_diagnostics(raw["metrics"], raw, area_size_m=8000., floor_m=50.))
            numeric_row_equal(row, original, "original evaluator reductions")
            numeric_row_equal(row, episode_metrics(raw), "independent complete-mission reductions")
        deployment = row.get("policy_counts") or {}
        omitted = {key: int(value) - int(actual_counts.get(key, 0)) for key, value in deployment.items()
                   if int(value) != int(actual_counts.get(key, 0))}
        if not complete and any(value < 0 for value in omitted.values()):
            raise AssertionError("partial replay overran recorded attempted work")
        return dict(status="verified" if complete else "partial-prefix-verified",
                    policy_counts=actual_counts, deployment_attempted_counts=deployment,
                    unreplayed_attempted_or_uncertain_counts=omitted,
                    recorded_rf_attempts_without_output=int(np.sum(records["rf_started"] - records["rf_completed"])),
                    replay_boundary=boundary, candidate_records_checked=len(records),
                    unverified_candidate_ranking_step=unverified_ranking_step,
                    preserved_unverified_ranking_flags=[dict(index=int(record["index"]),
                        accepted=bool(record["accepted"]), selected=bool(record["selected"]))
                        for record in records if int(record["step"]) == unverified_ranking_step],
                    ranking_scope="exact on captured complete plans; interrupted final plan flags preserved, false does not prove rejection",
                    identity_reading=binding.result(), verified_actual_proposals=verified,
                    verified_feedback_calls=verified, shield_calls=shield_attempts,
                    inflight_proposals_replayed=attempts-verified,
                    missing_saved_decision_fields=sorted(missing),
                    new_native_steps=0, partial_native_scope="complete recorded decisions only; no missing output reconstructed")
    finally:
        if progress is not None:
            progress(dict(verified=verified, attempted_calls=attempts, policy_counts=counts(),
                          shield_calls=shield_attempts,
                          replay_boundary=boundary,
                          failed_call_count_scope="actual replay attempts; deployment interrupted suffix separately preserved"))
        close = getattr(controller, "close", None)
        if close is not None:
            close()


def same_values(left, right):
    same = np.equal(left, right)
    if np.asarray(left).dtype.kind in "fc" and np.asarray(right).dtype.kind in "fc":
        same |= np.isnan(left) & np.isnan(right)
    return same


def first_difference(left, right):
    different = np.any(~same_values(left, right), axis=tuple(range(1, left.ndim)))
    indices = np.flatnonzero(different)
    return int(indices[0]) if len(indices) else None


def change_reading(left, right):
    n = min(len(left), len(right))
    a, b = left[:n], right[:n]
    changed = np.any(~same_values(a, b), axis=tuple(range(1, a.ndim)))
    indices = np.flatnonzero(changed)
    later = indices[indices > 0]
    result = dict(common_rows=n, different_rows=int(changed.sum()),
                  first_difference=int(indices[0]) if len(indices) else None,
                  first_later_difference=int(later[0]) if len(later) else None,
                  different_later_rows=int(np.count_nonzero(changed[1:])))
    if a.dtype.kind in "fc":
        finite = np.isfinite(a).all(axis=-1) & np.isfinite(b).all(axis=-1)
        distance = np.linalg.norm(np.where(np.isfinite(a-b), a-b, 0), axis=-1)
        result.update(maximum_norm=float(distance[finite].max()) if finite.any() else None,
                      mean_norm=float(distance[finite].mean()) if finite.any() else None)
    return result


def check_partial_native(raw, row):
    """Preserved capture prefix, without claiming missing reward/end reductions."""
    n = int(np.asarray(raw["recorded_native_steps"]).item())
    d = int(np.asarray(raw["recorded_decision_steps"]).item())
    if not 0 <= d <= n <= row["limit"] or n - d > 1:
        raise AssertionError("partial native/decision chronology")
    if raw["observations"].shape != (n+1, 8, 365) or raw["observations"].dtype != np.float32:
        raise AssertionError("partial lawful boundary shape/dtype")
    if any(value.dtype.kind == "O" for value in raw.values()):
        raise AssertionError("object arrays forbidden")
    if raw["proposed"].shape != (d, 8, 4) or raw["submitted"].shape != (n, 8, 4):
        raise AssertionError("partial command capture shape")
    if row.get("observed_native_steps", n) != n:
        raise AssertionError("partial observed native count mismatch")
    # A failure in boundary capture itself can leave an incomplete tail. Do not
    # synthesize it or silently trim it into a complete native evidence record.
    checked_routes = False
    if "native_routes" in raw and "native_route_capacity" in raw:
        check_routes(raw)
        checked_routes = True
    return dict(native_transitions_checked=0, observed_native_steps=n,
                recorded_completed_decisions=d, recorded_route_topology_checked=checked_routes,
                native_reward_energy_endpoint_verification="unavailable for incomplete capture; retained outputs only",
                new_native_steps=0, full_rf_resimulation=False)


def read_world(payload):
    job, rows, out_string, phase = payload
    out = Path(out_string)
    wall, cpu = time.perf_counter(), time.process_time()
    checked, trajectories, fingerprints = [], {}, {}
    state = {}
    progress_path = out / "reading_raw" / (str(job["seed"]) + ".progress.json")

    def progress(value):
        state.update(value)
        write_json(progress_path, dict(**job, status="running", **state))

    try:
        import torch
        torch.set_num_threads(1)
        for row in rows:
            state = dict(arm=row["arm"], verified=0)
            complete = row.get("status") == "completed"
            artifact = row.get("raw") if complete else row.get("partial", row.get("incomplete_raw"))
            if artifact is None:
                checked.append(dict(arm=row["arm"], seed=row["seed"], native=None,
                    replay=dict(status="unverifiable-no-saved-input", policy_counts={},
                                deployment_attempted_counts=row.get("policy_counts") or {},
                                unreplayed_attempted_or_uncertain_counts=row.get("policy_counts") or {},
                                verified_actual_proposals=0, verified_feedback_calls=0,
                                identity_reading=IdentityReading().result(), new_native_steps=0)))
                continue
            path = (out / artifact["path"]).resolve()
            if not path.is_relative_to((out / "raw").resolve()):
                raise AssertionError("raw source escaped canonical output")
            binding = identity(path)
            if any(binding[key] != artifact[key] for key in ("sha256", "bytes")):
                raise AssertionError("raw source identity differs")
            with np.load(path, allow_pickle=False) as archive:
                raw = {key: archive[key] for key in archive.files}
            native = check_native(raw, row, phase) if complete else check_partial_native(raw, row)
            replay = replay_episode(raw, row, phase, progress)
            checked.append(dict(arm=row["arm"], seed=row["seed"], native=native, replay=replay))
            state = {}  # Episode now owns these counts; later pair failures are not inflight replay.
            if complete:
                fingerprints[row["arm"]] = {key: array_digest(value) for key, value in raw.items()}
                trajectories[row["arm"]] = {key: raw[key].copy() for key in
                    ("truth_user_xyz", "truth_uav_xyz", "truth_bs_xyz", "truth_station_xyz",
                     "submitted", "proposed", "decision_targets_xyz")}
                trajectories[row["arm"]]["initial_observations"] = raw["observations"][0].copy()
            del raw
        pairs = []
        for left, right in (("F", "H"), ("H", "C"), ("F", "C")):
            if left not in trajectories or right not in trajectories:
                continue
            a, b = trajectories[left], trajectories[right]
            prefix = min(len(a["truth_user_xyz"]), len(b["truth_user_xyz"]))
            equal(a["truth_user_xyz"][:prefix], b["truth_user_xyz"][:prefix], "actual common-prefix user path")
            for name in ("truth_uav_xyz", "truth_bs_xyz", "truth_station_xyz"):
                equal(a[name][0], b[name][0], "common reset: " + name)
            equal(a["initial_observations"], b["initial_observations"], "common reset lawful observations")
            pairs.append(dict(contrast=left+"-"+right, observed_common_boundaries=prefix,
                first_position_divergence_boundary=first_difference(a["truth_uav_xyz"][:prefix], b["truth_uav_xyz"][:prefix]),
                first_proposal_divergence_tick=first_difference(a["proposed"][:prefix-1], b["proposed"][:prefix-1]),
                first_submitted_divergence_tick=first_difference(a["submitted"][:prefix-1], b["submitted"][:prefix-1]),
                target_xyz_changes=change_reading(a["decision_targets_xyz"], b["decision_targets_xyz"]),
                proposed_changes=change_reading(a["proposed"], b["proposed"]),
                submitted_changes=change_reading(a["submitted"], b["submitted"]),
                physical_xyz_changes=change_reading(a["truth_uav_xyz"], b["truth_uav_xyz"]),
                user_path_sha256=array_digest(a["truth_user_xyz"][:prefix])))
        reference_equal = None
        if phase == "engineering" and {"REFERENCE", "C"} <= fingerprints.keys():
            reference_equal = fingerprints["REFERENCE"] == fingerprints["C"]
            if not reference_equal:
                differences = sorted(set(fingerprints["REFERENCE"]) ^ set(fingerprints["C"]))
                differences += [key for key in fingerprints["C"] if key in fingerprints["REFERENCE"]
                                and fingerprints["C"][key] != fingerprints["REFERENCE"][key]]
                raise AssertionError("frozen P_BS / C native identity differs: " + repr(differences))
        all_complete = all(row.get("status") == "completed" for row in rows)
        result = dict(**job, status="completed" if all_complete else "partial", episodes=checked,
                      common_prefix_pairs=pairs, exact_native_reference_C=reference_equal,
                      **{"reader_worker_"+key: value for key, value in telemetry(wall, cpu).items()})
        write_json(progress_path, dict(**job, status=result["status"], episodes=len(checked)))
        return result
    except BaseException as error:
        result = dict(**job, status="failed", error=repr(error), traceback=traceback.format_exc(),
                      episodes=checked, inflight=state,
                      **{"reader_worker_"+key: value for key, value in telemetry(wall, cpu).items()})
        write_json(progress_path, result)
        return result


def children_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def read_result(out, workers):
    out = Path(out)
    if workers not in (1, 2) or any((out / name).exists() for name in ("reading.json", "reading_worlds.json", "reading_raw")):
        raise ValueError("invalid worker count or a reader was already started; no automatic replay")
    wall, cpu, child_cpu = time.perf_counter(), time.process_time(), children_cpu()
    config = json.loads((out / "config.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    rows = json.loads((out / "perworld.json").read_text())
    phase = config["phase"]
    if config["object"] != OBJECT or summary["object"] != OBJECT or config["jobs"] != jobs(phase):
        raise AssertionError("unfrozen panel")
    if summary["status"] not in ("complete", "incomplete") or summary["launch_sha"] != config["launch_sha"]:
        raise AssertionError("native summary status/source binding")
    if config["source_binding"] != source_binding():
        raise AssertionError("reader source differs from native input binding")
    expected_jobs = jobs(phase)
    declared = {job["job_key"]: job for job in expected_jobs}
    keys = [row["job_key"] for row in rows]
    if len(set(keys)) != len(keys) or any(key not in declared for key in keys):
        raise AssertionError("undeclared or duplicate actual job")
    equal(keys, [job["job_key"] for job in expected_jobs if job["job_key"] in keys], "logical actual world/arm order")
    for row in rows:
        if {key: row[key] for key in ("job_key", "seed", "arm", "limit")} != declared[row["job_key"]]:
            raise AssertionError("native row differs from declared job")
        if row.get("status") not in ("completed", "failed"):
            raise AssertionError("unknown actual episode status")
    if summary["status"] == "complete" and (keys != [job["job_key"] for job in expected_jobs]
                                            or any(row["status"] != "completed" for row in rows)):
        raise AssertionError("incomplete reported complete panel")
    manifest = json.loads((out / "manifest.json").read_text())
    if manifest["object"] != OBJECT or manifest["launch_sha"] != config["launch_sha"]:
        raise AssertionError("manifest source/object identity differs")
    for name, expected in (manifest["artifacts"] | manifest["raw"]).items():
        path = (out / name).resolve()
        if not path.is_relative_to(out.resolve()):
            raise AssertionError("manifest path escaped output")
        actual = identity(path)
        if any(actual[key] != expected[key] for key in ("sha256", "bytes")):
            raise AssertionError("saved artifact changed: " + name)
    raw_files = {str(path.relative_to(out)) for path in (out / "raw").iterdir()}
    if raw_files != set(manifest["raw"]):
        raise AssertionError("unexpected or missing native raw artifact")
    unreported_evidence = []
    for job in expected_jobs:
        if job["job_key"] in keys:
            continue
        stem = job["job_key"].replace("/", "_")
        progress_path = out / "raw" / (stem + ".progress.json")
        item = dict(**job, replay_status="not-replayed-no-authoritative-episode-row",
                    raw_artifacts={name: value for name, value in manifest["raw"].items()
                                   if name in (f"raw/{stem}.npz", f"raw/{stem}.partial.npz")})
        if progress_path.exists():
            saved_progress = json.loads(progress_path.read_text())
            if any(saved_progress.get(key) != job[key] for key in ("job_key", "seed", "arm", "limit")):
                raise AssertionError("unreported progress job binding differs")
            item.update(last_preserved_progress=saved_progress,
                        known_attempted_count_lower_bound=saved_progress.get("policy_counts") or {},
                        count_scope="last preserved progress; later missing attempts remain unknown")
        else:
            item.update(known_attempted_count_lower_bound={}, count_scope="no attempt count evidence")
        unreported_evidence.append(item)
    (out / "reading_raw").mkdir()
    worlds = sorted({row["seed"] for row in rows})
    plan = [dict(job_key=str(seed), seed=seed) for seed in worlds]
    results, submitted = [], []

    def on_result(result):
        results.append(result)
        results.sort(key=lambda item: item["seed"])
        write_json(out / "reading_worlds.json", results)

    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        _, errors = execute_bounded(pool, plan, workers,
            lambda job: (job, [row for row in rows if row["seed"] == job["seed"]], str(out), phase),
            on_result, submitted, worker_fn=read_world)
    audit_ok = len(results) == len(worlds) and all(r["status"] in ("completed", "partial") for r in results) and not errors
    complete = audit_ok and summary["status"] == "complete"
    episodes = [episode for world in results for episode in world.get("episodes", [])]
    replay_counts = sum_counts(e["replay"]["policy_counts"] for e in episodes)
    failed_attempts = sum_counts(r.get("inflight", {}).get("policy_counts", {}) for r in results if r["status"] == "failed")
    attempted_counts = sum_counts((replay_counts, failed_attempts))
    result = dict(object=OBJECT, phase=phase, launch_sha=config["launch_sha"],
                  status="VERIFIED" if complete else "PARTIAL" if audit_ok else "FAILED",
                  source_binding=config["source_binding"], worlds=len(worlds), episodes=len(rows),
                  reader_workers=workers, submitted_worlds=submitted, errors=errors,
                  replay_counts=replay_counts, replay_attempted_counts=attempted_counts,
                  failed_replay_attempted_counts=failed_attempts,
                  deployment_reported_attempted_counts=sum_counts(row.get("policy_counts") or {} for row in rows),
                  preserved_unreplayed_attempted_or_uncertain_counts=sum_counts(
                      e["replay"].get("unreplayed_attempted_or_uncertain_counts", {}) for e in episodes),
                  verified_actual_proposals=sum(e["replay"]["verified_actual_proposals"] for e in episodes),
                  verified_feedback_calls=sum(e["replay"]["verified_feedback_calls"] for e in episodes),
                  reader_shield_calls=sum(e["replay"].get("shield_calls", 0) for e in episodes)
                      + sum(r.get("inflight", {}).get("shield_calls", 0) for r in results if r["status"] == "failed"),
                  native_transitions_checked=sum((e.get("native") or {}).get("native_transitions_checked", 0) for e in episodes),
                  unreported_jobs=[job for job in expected_jobs if job["job_key"] not in keys],
                  unreported_job_evidence=unreported_evidence,
                  unreported_attempted_count_lower_bound=sum_counts(
                      item["known_attempted_count_lower_bound"] for item in unreported_evidence),
                  deployment_unstarted_jobs=summary.get("unstarted_jobs", []),
                  reader_worker_cpu_seconds_sum=sum(r.get("reader_worker_cpu_seconds", 0.) for r in results),
                  reader_worker_wall_seconds_sum=sum(r.get("reader_worker_wall_seconds", 0.) for r in results),
                  reader_worker_peak_rss_kib_max=max((r.get("reader_worker_peak_rss_kib", 0) for r in results), default=None),
                  reaped_reader_cpu_seconds=children_cpu()-child_cpu,
                  **{"reader_parent_"+key: value for key, value in telemetry(wall, cpu).items()},
                  new_native_steps=0, model_resets=0, model_native_steps=0,
                  new_fits=0, new_labels=0, optimizer_updates=0,
                  model_vs_native="declared FP32 decoding/FP64 nominal and post-energy sample; omitted guard/intermediate association/PBRS/event penalties; no equality imposed")
    result["identity_totals"] = {
        arm: sum_counts(e["replay"]["identity_reading"]["counts"] for e in episodes if e["arm"] == arm)
        for arm in ARMS}
    result["forecast_by_world"] = [dict(seed=e["seed"], arm=e["arm"],
         replay_status=e["replay"]["status"], **e["replay"]["identity_reading"])
         for e in episodes if e["arm"] in ("H", "F")]
    result["forecast_totals"] = {}
    for arm in ("H", "F"):
        per_tau = {}
        for tau in SAMPLES:
            values = []
            for e in episodes:
                if e["arm"] != arm:
                    continue
                item = dict(e["replay"]["identity_reading"]["per_tau"][str(tau)])
                item["worst_rows"] = [dict(seed=e["seed"], **row) for row in item["worst_rows"]]
                values.append(item)
            per_tau[str(tau)] = finish_forecast_stats(pool_forecast_stats(values))
        result["forecast_totals"][arm] = dict(per_tau=per_tau,
             combined=finish_forecast_stats(pool_forecast_stats(per_tau.values())),
             scope="recorded origin identities on this arm's own path; partial censoring retained")
    if complete:
        completed_counts = sum_counts(e["replay"]["policy_counts"] for e in episodes)
        if completed_counts != summary["policy_counts"]:
            raise AssertionError("whole-reader actual-work call counts differ from deployment")
        if phase == "scientific":
            result["paired"] = comparisons(rows)
            if result["paired"] != summary["paired"]:
                raise AssertionError("paired complete-world reductions differ")
        else:
            result["exact_native_reference_C"] = all(r["exact_native_reference_C"] for r in results)
    write_json(out / "reading.json", result)
    if not audit_ok:
        raise RuntimeError("full actual-call reader audit failed; complete/partial native collection preserved")
    return result
