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
    HORIZON, OBJECT, array_digest, equal, expected_counts, identity, jobs,
    source_binding, sum_counts, telemetry, write_json,
)
from .controller import MemoryController, TRACK_DTYPE
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
    return dict(native_transitions_checked=n, native_agent_motion_ticks=n * 8,
                terminal_padding_rows=int((~nonpadding).sum()), full_rf_resimulation=False,
                new_native_steps=0, extra_model_queries=0, extra_allocator_queries=0)


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
        self.forecast_error = []
        self.held_error = []
        self.forecast_rows = []

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
        if plan_index is None or arm != "V":
            return
        for index, track in enumerate(tracks):
            counts["forecast_origins"] += 1
            candidates = bindings[int(track["birth"])]
            if len(candidates) != 1:
                counts["forecast_ambiguous" if candidates else "forecast_unbound"] += 1
                continue
            counts["forecast_bound"] += 1
            if tick + 15 >= len(raw["truth_user_xyz"]):
                counts["forecast_future_censored"] += 1
                continue
            user = next(iter(candidates))
            truth = raw["truth_user_xyz"][tick + 15, user, :2]
            projected = raw["plan_users"][plan_index, index]
            error = float(np.linalg.norm(projected - truth))
            held = float(np.linalg.norm(track["last_xy"] - truth))
            counts["forecast_evaluated"] += 1
            counts["forecast_nonzero_velocity"] += int(np.any(track["v"] != 0.))
            counts["forecast_remembered"] += int(not track["current"])
            self.forecast_error.append(error)
            self.held_error.append(held)
            self.forecast_rows.append(dict(t=tick, user=user, birth=int(track["birth"]), age=tick-int(track["last_seen"]),
                                           forecast_error_m=error, held_error_m=held,
                                           last_xy=track["last_xy"].tolist(), forecast_xy=projected.tolist(),
                                           truth_xy=truth.tolist()))

    def result(self):
        result = dict(counts=self.counts, binding="contemporaneous stable native slot order and actual merge provenance")
        if self.forecast_error:
            error, held = np.asarray(self.forecast_error), np.asarray(self.held_error)
            result.update(forecast_mean_error_m=float(error.mean()), held_mean_error_m=float(held.mean()),
                          forecast_rmse_m=float(np.sqrt(np.mean(error ** 2))), held_rmse_m=float(np.sqrt(np.mean(held ** 2))),
                          forecast_better=int(np.count_nonzero(error < held)), forecast_worse=int(np.count_nonzero(error > held)),
                          forecast_equal=int(np.count_nonzero(error == held)),
                          worst_forecast_rows=sorted(self.forecast_rows, key=lambda r: r["forecast_error_m"], reverse=True)[:5])
        return result


def replay_episode(raw, row, phase, progress=None):
    arm, n = row["arm"], row["actual_length"]
    controller = StationPriorController() if arm == "REFERENCE" else MemoryController(arm)
    controller.reset()
    modes, previous_done = np.zeros(8, dtype=bool), np.ones(1, dtype=bool)
    binding = IdentityReading()
    plan_index = 0
    verified = 0
    try:
        for tick in range(n):
            obs = raw["observations"][tick]
            proposal = controller.propose(obs, UnavailableTruth(), tick, previous_done, modes.copy())
            equal(proposal, raw["proposed"][tick], "actual-path proposed commands")
            equal(controller.targets_xy, raw["target_xy"][tick], "actual held targets")
            decision = apply_feedback_params(obs, proposal, modes, PRODUCTION_PARAMS)
            for name, value in dict(submitted=decision.submitted_actions, mode=decision.modes,
                                    entered=decision.entered, exited=decision.exited,
                                    return_margin=decision.margins, nearest_station=decision.selected_stations,
                                    nearest_station_distance_m=decision.station_distances_m).items():
                equal(raw[name][tick], value, "actual feedback: " + name)
            equal(raw["own_xyz"][tick], own_positions(obs), "decoded decision position")
            held = own_energy(obs)
            equal(raw["station_occupancy"][tick], station_counts(decision.selected_stations, held["charging"]),
                  "decision-time occupancy decode")
            equal(raw["station_queue"][tick], station_counts(decision.selected_stations, held["waiting_steps"] > 0),
                  "decision-time queue decode")
            post = own_energy(raw["observations"][tick + 1])
            for name in ("charging", "waiting_steps", "battery"):
                equal(raw[name][tick], post[name], "post-step energy decode: " + name)
            equal(raw["dock_bit"][tick], decision.submitted_actions[:, 3] > .5, "dock command")
            current_plan = plan_index if tick % 30 == 0 else None
            if current_plan is not None:
                for name, value in plan_record(controller, tick).items():
                    equal(raw[name][plan_index], value, "actual plan: " + name)
                plan_index += 1
            slots, silent = bind_slots(raw, tick)
            binding.counts["slot_records"] += int(np.count_nonzero(slots >= 0))
            binding.counts["silent_true_slots"] += silent
            if arm in ("M", "V"):
                trace = controller.last_trace
                for name, value in memory_record(trace).items():
                    equal(raw[name][tick], value, "actual primitive memory: " + name)
                binding.step(raw, tick, trace, slots, current_plan, arm)
            modes = decision.modes
            previous_done[:] = raw["ends"][tick].any()
            verified += 1
            if progress is not None and verified % 100 == 0:
                progress(dict(verified=verified, policy_counts=expected_counts(arm, verified)))
    finally:
        if progress is not None:
            progress(dict(verified=verified, attempted_calls=controller.heuristic.calls,
                          policy_counts=getattr(controller, "counters", expected_counts(arm, verified)),
                          failed_call_count_scope="one interrupted inherited call may be additional"))
    equal(plan_index, len(raw["plan_step"]), "all and only actual plans")
    counts = expected_counts(arm, n)
    if arm != "REFERENCE" and controller.counters != counts:
        raise AssertionError("replay primitive accounting")
    if row["policy_counts"] != counts:
        raise AssertionError("deployment/replay count mismatch")
    original = world_row(row["seed"], raw["reward"], raw["metrics"], raw["ends"], raw, time_step_s=1.)
    original.update(mechanism_row(raw, absolute_station_xy(raw["observations"][0])))
    original.update(position_diagnostics(raw["metrics"], raw, area_size_m=8000., floor_m=50.))
    numeric_row_equal(row, original, "original evaluator reductions")
    numeric_row_equal(row, episode_metrics(raw), "independent complete-mission reductions")
    return dict(policy_counts=counts, identity_reading=binding.result(), verified_actual_proposals=n,
                verified_feedback_calls=n, new_native_steps=0)


def first_difference(left, right):
    different = np.any(left != right, axis=tuple(range(1, left.ndim)))
    indices = np.flatnonzero(different)
    return int(indices[0]) if len(indices) else None


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
            path = (out / row["raw"]["path"]).resolve()
            if not path.is_relative_to((out / "raw").resolve()):
                raise AssertionError("raw source escaped canonical output")
            binding = identity(path)
            if any(binding[key] != row["raw"][key] for key in ("sha256", "bytes")):
                raise AssertionError("raw source identity differs")
            with np.load(path, allow_pickle=False) as archive:
                raw = {key: archive[key] for key in archive.files}
            native = check_native(raw, row, phase)
            replay = replay_episode(raw, row, phase, progress)
            checked.append(dict(arm=row["arm"], seed=row["seed"], native=native, replay=replay))
            fingerprints[row["arm"]] = {key: array_digest(value) for key, value in raw.items()}
            trajectories[row["arm"]] = {key: raw[key].copy() for key in
                                       ("truth_user_xyz", "truth_uav_xyz", "truth_bs_xyz", "truth_station_xyz",
                                        "submitted", "proposed", "observations") if key != "observations"}
            trajectories[row["arm"]]["initial_observations"] = raw["observations"][0].copy()
            del raw
        pairs = []
        for left, right in (("M", "C"), ("V", "M"), ("V", "C")):
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
                              user_path_sha256=array_digest(a["truth_user_xyz"][:prefix])))
        reference_equal = None
        if phase == "engineering":
            reference_equal = fingerprints["REFERENCE"] == fingerprints["C"]
            if not reference_equal:
                differences = sorted(set(fingerprints["REFERENCE"]) ^ set(fingerprints["C"]))
                differences += [key for key in fingerprints["C"] if key in fingerprints["REFERENCE"]
                                and fingerprints["C"][key] != fingerprints["REFERENCE"][key]]
                raise AssertionError("frozen P_BS / C native identity differs: " + repr(differences))
        result = dict(**job, status="completed", episodes=checked, common_prefix_pairs=pairs,
                      exact_native_reference_C=reference_equal,
                      **{"reader_worker_"+key: value for key, value in telemetry(wall, cpu).items()})
        write_json(progress_path, dict(**job, status="completed", episodes=len(checked)))
        return result
    except BaseException as error:
        result = dict(**job, status="failed", error=repr(error), traceback=traceback.format_exc(),
                      completed_episodes=checked, inflight=state,
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
    if summary["status"] != "complete" or config["object"] != OBJECT or config["jobs"] != jobs(phase):
        raise AssertionError("incomplete or unfrozen panel")
    if config["source_binding"] != source_binding():
        raise AssertionError("reader source differs from native input binding")
    equal([{key: r[key] for key in ("job_key", "seed", "arm", "limit")} for r in rows], jobs(phase),
          "logical world/arm order")
    manifest = json.loads((out / "manifest.json").read_text())
    for name, expected in manifest["artifacts"].items():
        actual = identity(out / name)
        if any(actual[key] != expected[key] for key in ("sha256", "bytes")):
            raise AssertionError("compact native artifact changed")
    raw_files = {str(path.relative_to(out)) for path in (out / "raw").iterdir()}
    if raw_files != set(manifest["raw"]):
        raise AssertionError("unexpected or missing native raw artifact")
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
    complete = len(results) == len(worlds) and all(result["status"] == "completed" for result in results) and not errors
    result = dict(object=OBJECT, phase=phase, launch_sha=config["launch_sha"], status="VERIFIED" if complete else "FAILED",
                  source_binding=config["source_binding"], worlds=len(worlds), episodes=len(rows),
                  reader_workers=workers, submitted_worlds=submitted, errors=errors,
                  reader_worker_cpu_seconds_sum=sum(r.get("reader_worker_cpu_seconds", 0.) for r in results),
                  reader_worker_wall_seconds_sum=sum(r.get("reader_worker_wall_seconds", 0.) for r in results),
                  reader_worker_peak_rss_kib_max=max((r.get("reader_worker_peak_rss_kib", 0) for r in results), default=None),
                  reaped_reader_cpu_seconds=children_cpu()-child_cpu,
                  **{"reader_parent_"+key: value for key, value in telemetry(wall, cpu).items()},
                  new_native_steps=0, new_fits=0, new_labels=0, optimizer_updates=0)
    if complete:
        episodes = [e for r in results for e in r["episodes"]]
        counts = sum_counts(e["replay"]["policy_counts"] for e in episodes)
        if counts != summary["policy_counts"]:
            raise AssertionError("whole-reader call counts differ from deployment")
        result["replay_counts"] = counts | {"shield_calls": sum(r["actual_length"] for r in rows)}
        result["native_transitions_checked"] = sum(e["native"]["native_transitions_checked"] for e in episodes)
        if phase == "scientific":
            result["paired"] = comparisons(rows)
            if result["paired"] != summary["paired"]:
                raise AssertionError("paired complete-world reductions differ")
        else:
            result["exact_native_reference_C"] = all(r["exact_native_reference_C"] for r in results)
        result["identity_totals"] = {
            arm: sum_counts(e["replay"]["identity_reading"]["counts"] for e in episodes if e["arm"] == arm)
            for arm in ("C", "M", "V")}
    write_json(out / "reading.json", result)
    if not complete:
        raise RuntimeError("full actual-policy reader failed; completed native collection preserved")
    return result
