"""Common two-phase transition executor and bounded ordinary joint search."""

from __future__ import annotations

import time

import numpy as np

from experiments.candidates.energy_relay_availability.b04.transit_hold import TransitHoldHeuristic
from experiments.candidates.energy_relay_benchmark.b01.evaluation import central_plan_inputs
from experiments.candidates.energy_relay_benchmark.b01.feedback import decode_legal_observations
from experiments.candidates.uav_radio_placement.b01.placement import PlacementController

from .motion import HORIZON, N_UAVS, forecast, legal_start, toward, waypoints


CLOCK = HORIZON
# Eligible[8]; own xyz[24]; battery/margin/available/charging/wait/F[48];
# R xyz[24]; station xyz[6], capacity[2]; users xy[60], BS xy[2];
# conditional own xyz/battery at 10/20/30 for four modes[384]; time[1].
FEATURE_DIM = 559
SCORE_TOL = 1e-8
TRAVEL_TOL_M = 1e-6


def _features(start, targets, inputs, eligible, prior_F, model_env):
    predictions = np.empty((N_UAVS, 4, 3, 4), dtype=np.float64)
    crossings = np.zeros((N_UAVS, 4, 3), dtype=bool)  # F, reserve, cutoff
    all_d = np.zeros(N_UAVS, dtype=np.int64)
    base = forecast(start, targets, all_d, prior_F, model_env)
    forecasts = 1
    for member in range(N_UAVS):
        predictions[member, 0, :, :3] = base.xyz[:, member]
        predictions[member, 0, :, 3] = base.battery[:, member]
        crossings[member, 0] = (base.crossed_F[member], base.crossed_reserve[member],
                                base.crossed_cutoff[member])
        for mode in (1, 2, 3):
            if eligible[member]:
                choice = all_d.copy()
                choice[member] = mode
                outcome = forecast(start, targets, choice, prior_F, model_env)
                forecasts += 1
            else:
                outcome = base
            predictions[member, mode, :, :3] = outcome.xyz[:, member]
            predictions[member, mode, :, 3] = outcome.battery[:, member]
            crossings[member, mode] = (outcome.crossed_F[member],
                                       outcome.crossed_reserve[member],
                                       outcome.crossed_cutoff[member])
    area = 8000.0
    predicted_scaled = predictions.copy()
    predicted_scaled[..., :3] /= area
    own = np.asarray(start["xyz"], dtype=np.float64)
    facts = np.column_stack((start["battery"], start["margin"],
                             start["available"], start["charging"],
                             start["waits"] / 3000.0, prior_F))
    features = np.concatenate((
        eligible.astype(float), (own / area).reshape(-1), facts.reshape(-1),
        (targets / area).reshape(-1), (start["stations"] / area).reshape(-1),
        start["capacity"] / N_UAVS,
        np.asarray(inputs["users_xy"], dtype=float).reshape(-1) / area,
        np.asarray(inputs["bs_xy"], dtype=float).reshape(-1) / area,
        predicted_scaled.reshape(-1),
        np.asarray([1.0]),  # overwritten by caller with normalized remaining horizon
    )).astype(np.float32)
    if features.shape != (FEATURE_DIM,) or not np.isfinite(features).all():
        raise ValueError("invalid transition feature vector")
    aliases = np.zeros(N_UAVS, dtype=np.int64)
    for member in range(N_UAVS):
        aliases[member] = sum(
            np.allclose(predictions[member, mode], predictions[member, 0], rtol=0, atol=1e-6)
            for mode in (1, 2, 3))
    return features, forecasts, aliases, crossings


class TransitionController:
    """A single real R stream; mode choices alter only its inter-clock proposals."""

    feature_dim = FEATURE_DIM

    def __init__(self, arm, env, model_env, chooser=None):
        if arm not in ("L", "O"):
            raise ValueError("arm must be L or O")
        if env is model_env or getattr(env, "env", env) is getattr(model_env, "env", model_env):
            raise ValueError("scoring model must be independently initialized")
        if arm == "O" and chooser is not None:
            raise ValueError("ordinary O chooses its own modes")
        self.arm, self.env, self.model_env, self.chooser = arm, env, model_env, chooser
        self.source = PlacementController("R", env, model_env)
        self.reset()

    def reset(self):
        self.source.reset()
        self.decision_records = []
        self.last_features = None
        self._prepared = None
        self._selected = None
        self._calls = 0
        self._cancelled = np.zeros(N_UAVS, dtype=bool)
        self._candidate_forecasts = 0
        self._prediction_team_ticks = 0
        self._transition_started = 0
        self._transition_completed = 0
        self._planner_cpu_seconds = 0.0
        self._planner_wall_seconds = 0.0

    @property
    def targets_xy(self):
        return self.source.targets_xy

    @property
    def snapshot_calls_started(self):
        return self.source.snapshot_calls_started + self._transition_started

    @property
    def snapshot_calls_completed(self):
        return self.source.snapshot_calls_completed + self._transition_completed

    def _forecast(self, start, targets, choice, prior_F):
        self._candidate_forecasts += 1
        self._prediction_team_ticks += HORIZON
        return forecast(start, targets, choice, prior_F, self.model_env)

    def _score(self, inputs, outcome):
        raw = getattr(self.model_env, "env", self.model_env)
        qos = []
        for positions, battery in zip(outcome.xyz, outcome.battery):
            self._transition_started += 1
            value = TransitHoldHeuristic._service_qos_at_snapshot(raw, inputs, positions, battery)
            self._transition_completed += 1
            if not np.isfinite(value):
                raise FloatingPointError("nonfinite transition radio score")
            qos.append(value)
        worst = np.maximum(0.0, -np.min(outcome.margin, axis=1))
        costs = worst / max(float(raw.return_margin_scale), 1e-8)
        if raw.return_cost_cap is not None:
            costs = np.minimum(costs, float(raw.return_cost_cap))
        score = 10.0 * float(np.sum(np.asarray(qos, dtype=np.float64) -
                                    float(raw.lambda_return) * costs, dtype=np.float64))
        return score

    def _ordinary(self, start, targets, inputs, eligible, prior_F, step):
        selected = np.zeros(N_UAVS, dtype=np.int64)
        history = []

        def examine(choice, label):
            outcome = self._forecast(start, targets, choice, prior_F)
            score = self._score(inputs, outcome)
            row = {"label": label, "modes": choice.copy(), "score": score,
                   "travel_m": outcome.travel_m,
                   "crossed_F": outcome.crossed_F.copy(),
                   "crossed_reserve": outcome.crossed_reserve.copy(),
                   "crossed_cutoff": outcome.crossed_cutoff.copy()}
            history.append(row)
            return row

        best = examine(selected, "all_D")

        def accept(candidate):
            nonlocal best, selected
            if (candidate["score"] > best["score"] + SCORE_TOL or
                    (abs(candidate["score"] - best["score"]) <= SCORE_TOL and
                     candidate["travel_m"] < best["travel_m"] - TRAVEL_TOL_M)):
                best = candidate
                selected = candidate["modes"].copy()
                candidate["accepted"] = True

        start_member = (step // CLOCK) % N_UAVS
        order = [(start_member + offset) % N_UAVS for offset in range(N_UAVS)]
        for sweep, members in enumerate((order, list(reversed(order)))):
            for member in members:
                if not eligible[member]:
                    continue
                incumbent = selected.copy()
                winner = None
                for mode in range(4):
                    if mode == incumbent[member]:
                        continue
                    candidate = incumbent.copy()
                    candidate[member] = mode
                    row = examine(candidate, f"sweep{sweep}_u{member}_m{mode}")
                    if winner is None or (row["score"] > winner["score"] + SCORE_TOL or
                            (abs(row["score"] - winner["score"]) <= SCORE_TOL and
                             row["travel_m"] < winner["travel_m"] - TRAVEL_TOL_M)):
                        winner = row
                if winner is not None:
                    accept(winner)
        for first in range(N_UAVS):
            if not eligible[first]:
                continue
            for second in range(first + 1, N_UAVS):
                if not eligible[second]:
                    continue
                incumbent = selected.copy()
                winner = None
                for a in (0, 1):
                    for b in (0, 1):
                        candidate = incumbent.copy()
                        candidate[first], candidate[second] = a, b
                        row = examine(candidate, f"pair{first}_{second}_{a}_{b}")
                        if winner is None or (row["score"] > winner["score"] + SCORE_TOL or
                                (abs(row["score"] - winner["score"]) <= SCORE_TOL and
                                 row["travel_m"] < winner["travel_m"] - TRAVEL_TOL_M)):
                            winner = row
                if winner is not None:
                    accept(winner)
        return selected, history

    def prepare_clock(self, observations, prior_F, step):
        step = int(step)
        if step != self._calls or step % CLOCK:
            raise ValueError("prepare_clock requires the next thirty-step boundary")
        if self._prepared is not None and self._prepared["step"] == step:
            return self.last_features.copy()
        wall, cpu = time.perf_counter(), time.process_time()
        prior_F = np.asarray(prior_F, dtype=bool)
        if prior_F.shape != (N_UAVS,):
            raise ValueError("prior F must have eight flags")
        base = self.source.propose(observations, None, step, None, prior_F)
        targets = self.source.targets_xyz.copy()
        start = legal_start(observations)
        inputs = central_plan_inputs(self.env)
        eligible = start["available"] & ~prior_F & np.isfinite(targets).all(axis=1)
        features, n_forecasts, aliases, crossings = _features(
            start, targets, inputs, eligible, prior_F, self.model_env)
        features[-1] = np.float32((3000 - step) / 3000.0)
        self._candidate_forecasts += n_forecasts
        self._prediction_team_ticks += n_forecasts * HORIZON
        record = {"step": step, "clock_index": step // CLOCK,
                  "eligible": eligible.copy(), "prior_F": prior_F.copy(),
                  "features": features.copy(),
                  "destination_record": self.source.decision_records[-1],
                  "requested_modes": None, "R_targets_xyz": targets.copy(),
                  "feature_forecasts": n_forecasts, "nominal_aliases": aliases,
                  "feature_predicted_crossings": crossings,
                  "candidate_scores": [], "candidate_count": 0,
                  "transition_snapshot_calls": 0,
                  "cancelled_members": np.zeros(N_UAVS, dtype=bool),
                  "cancelled_member_ticks": np.zeros(N_UAVS, dtype=np.int64)}
        self._prepared = {"step": step, "base": base.copy(), "targets": targets,
                          "start": start, "inputs": inputs, "eligible": eligible,
                          "prior_F": prior_F.copy(), "record": record,
                          "waypoints": waypoints(start["xyz"], targets)}
        self._selected = None
        self._cancelled[:] = False
        self.last_features = features.copy()
        if self.arm == "O":
            selected, scores = self._ordinary(start, targets, inputs, eligible, prior_F, step)
            self._selected = selected
            record["candidate_scores"] = scores
            record["candidate_count"] = len(scores)
            record["transition_snapshot_calls"] = 3 * len(scores)
        elif self.chooser is not None:
            self.set_modes(self.chooser(features.copy()))
        self._planner_wall_seconds += time.perf_counter() - wall
        self._planner_cpu_seconds += time.process_time() - cpu
        record["planner_wall_seconds"] = time.perf_counter() - wall
        record["planner_cpu_seconds"] = time.process_time() - cpu
        return features.copy()

    def set_modes(self, modes):
        if self._prepared is None:
            raise RuntimeError("prepare_clock before set_modes")
        if self._prepared["step"] != self._calls:
            raise RuntimeError("selected modes belong to an earlier clock")
        values = np.asarray(modes)
        if values.shape != (N_UAVS,) or not np.issubdtype(values.dtype, np.integer):
            raise ValueError("modes must be eight integer labels")
        if np.any((values < 0) | (values > 3)):
            raise ValueError("mode outside D/W/B+/B-")
        selected = values.astype(np.int64, copy=True)
        selected[~self._prepared["eligible"]] = 0
        self._selected = selected
        self._prepared["record"]["requested_modes"] = values.astype(np.int64, copy=True)
        self._prepared["record"]["selected_modes"] = selected.copy()

    def propose(self, observations, state, step, previous_done, modes):
        step = int(step)
        if step != self._calls:
            raise ValueError("transition controller requires sequential native steps")
        if step % CLOCK == 0:
            if self._prepared is None or self._prepared["step"] != step:
                self.prepare_clock(observations, modes, step)
            p = self._prepared
            base = p["base"].copy()
            if self._selected is None:
                self.set_modes(np.zeros(N_UAVS, dtype=np.int64))
            if p["record"]["requested_modes"] is None:
                p["record"]["requested_modes"] = self._selected.copy()
                p["record"]["selected_modes"] = self._selected.copy()
            self.decision_records.append(p["record"])
        else:
            base = self.source.propose(observations, state, step, previous_done, modes)
            p = self._prepared
        prior = np.asarray(modes, dtype=bool)
        margin = decode_legal_observations(observations)[0]
        entered = ~prior & (margin <= 0.0)
        self._cancelled |= entered
        record = p["record"]
        record["cancelled_members"] |= entered
        local_tick = step - p["step"]
        if local_tick < 15:
            record["cancelled_member_ticks"] += self._cancelled & (self._selected != 0)
        action = base.copy()
        if local_tick < 15:
            xyz = legal_start(observations)["xyz"]
            for member in range(N_UAVS):
                mode = self._selected[member]
                if mode == 0 or self._cancelled[member]:
                    continue
                target = p["start"]["xyz"][member] if mode == 1 else p["waypoints"][mode - 2, member]
                velocity = toward(xyz[member], target, dt=1.0)
                action[member] = np.asarray((velocity[0] / 30.0, velocity[1] / 30.0,
                                             velocity[2] / 5.0, 0.0), dtype=np.float32)
        self._calls += 1
        return action

    def work_counts(self):
        destination = self.source.snapshot_calls_started
        return {"service_snapshot_calls": destination + self._transition_started,
                "service_snapshot_calls_completed": self.source.snapshot_calls_completed + self._transition_completed,
                "destination_snapshot_calls": destination,
                "destination_snapshot_calls_completed": self.source.snapshot_calls_completed,
                "transition_snapshot_calls": self._transition_started,
                "transition_snapshot_calls_completed": self._transition_completed,
                "prediction_team_ticks": self._prediction_team_ticks,
                "candidate_forecasts": self._candidate_forecasts,
                "planner_cpu_seconds": self._planner_cpu_seconds,
                "planner_wall_seconds": self._planner_wall_seconds}
