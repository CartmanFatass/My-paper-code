"""One complete saved-observation replay; no native steps or retry path.

The owner supplies the correctly sequenced learner/checkpoint and accounts for
the repeated purchased H queries and Adam updates. Native RF is not resimulated;
the retained B10 checker reconstructs arithmetic over recorded native outputs.
"""
from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING, Callable

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    absolute_station_xy, mechanism_row, position_diagnostics, station_counts, world_row,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    PRODUCTION_PARAMS, apply_feedback_params,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import own_energy, own_positions
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.capture import (
    memory_record, plan_record,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.contract import (
    array_digest, equal,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.controller import (
    validate_candidate_record,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.metrics import episode_metrics
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.reader import (
    UnavailableTruth, check_native, compare_candidate_prefix, compare_records,
    numeric_row_equal, validate_candidate_records,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.trace import CANDIDATE_DTYPE

from .contract import diagnostic_bytes, expected_counts
from .controller import CHOICE_DTYPE, make_controller

if TYPE_CHECKING:
    from .learner import Learner


_PROGRAMS = {"C", "H_T", "T", "SELECTOR", "forced_C", "forced_H_T", "alternating"}
_MIXED = _PROGRAMS - {"C", "H_T"}


def _same_array(actual, recorded, label):
    if np.asarray(actual).dtype != np.asarray(recorded).dtype:
        raise AssertionError(label + ": dtype mismatch")
    equal(actual, recorded, label)


def _compare_typed_records(raw, values, index, label):
    compare_records(raw, values, index, label)
    for key, value in values.items():
        if np.asarray(value).dtype != raw[key][index].dtype:
            raise AssertionError(label + "/" + key + ": dtype mismatch")


def _check_choices(raw, program, n):
    choices = raw.get("choice_records", np.empty(0, CHOICE_DTYPE))
    if choices.dtype != CHOICE_DTYPE or choices.ndim != 1:
        raise AssertionError("choice structured dtype/shape")
    if program not in _MIXED:
        if len(choices):
            raise AssertionError("canonical endpoint has mixed choice records")
        return choices
    equal(choices["step"], np.arange(0, n, 30), "all and only real choice boundaries")
    if not choices["completed"].all():
        raise AssertionError("incomplete choice in complete mission")
    equal(choices["features_available"], np.full(len(choices), program != "T"),
          "learned/scripted feature packing; ordinary threshold omits encoding")
    if not np.isfinite(choices["features"]).all():
        raise AssertionError("nonfinite selector features")
    for index, choice in enumerate(choices):
        action = int(choice["requested_action"])
        if action not in (0, 1) or (action and not choice["h_eligible"]):
            raise AssertionError("invalid masked choice")
        equal([choice["masked_action"], choice["executed_action"]], [action, action],
              "requested/masked/controller-executed choice")
        equal(choice["h_search"], bool(action), "H work iff requested H")
        previous = np.full((8, 2), np.nan) if index == 0 else raw["plan_targets"][index - 1]
        equal(choice["previous_targets"], previous, "one actual previous committed target history")
        equal(choice["has_previous_choice"], index > 0, "choice reset flag")
        prior_action = -1 if index == 0 else int(choices[index - 1]["requested_action"])
        equal(choice["previous_requested_action"], prior_action, "choice history")
        streak = 0
        for prior in reversed(choices[:index]):
            if int(prior["requested_action"]) != prior_action:
                break
            streak += 1
        equal(choice["previous_same_choice_count"], streak, "choice streak")
    return choices


def _check_assignment_menu(raw, program, choices):
    """Independent recorded-input assertions, with literal H_T tie arithmetic.

    B10's schema validator is reusable; its H_A base-first argmax assignment
    checker is not. No controller tie helper or new private query is used here.
    """
    records = raw["candidate_records"]
    consumed = 0
    for index, tick_value in enumerate(raw["plan_step"]):
        tick = int(tick_value)
        role = raw["plan_assignment_role"][index]
        call = raw["plan_assignment_call"][index]
        column = raw["plan_assignment_column"][index]
        ordinary = raw["plan_ordinary_targets"][index]
        prior = np.zeros(8, bool) if tick == 0 else raw["mode"][tick - 1]
        eligible = (role == 2) & ~prior & np.isfinite(ordinary).all(axis=1)
        members = np.flatnonzero(eligible)
        if len(members) > 6:
            raise AssertionError("more than six eligible service members")
        equal(raw["plan_eligible"][index], eligible, "actual service eligibility")
        for member in range(8):
            source_call, col = int(call[member]), int(column[member])
            if source_call == 0:
                if role[member] != 0 or col != -1 or not np.isnan(ordinary[member]).all():
                    raise AssertionError("missing assignment provenance")
            elif source_call in (1, 2):
                key = "plan_priority" if source_call == 1 else "plan_ring"
                count = int(raw[key + "_count"][index])
                if source_call == 1:
                    count = min(count, int((~prior).sum()))
                if not 0 <= col < count or prior[member]:
                    raise AssertionError("assignment source/return eligibility")
                equal(ordinary[member], raw[key][index, col], "original solver column target")
                expected_role = 3 if source_call == 2 else 1 if col < raw["plan_relay_count"][index] else 2
                equal(role[member], expected_role, "original assignment role")
            else:
                raise AssertionError("unknown assignment call")
        for source_call in (1, 2):
            cols = column[call == source_call]
            if len(set(map(int, cols))) != len(cols):
                raise AssertionError("solver column assigned twice")
        group = records[records["step"] == tick]
        equal(raw["plan_candidate_first"][index], consumed, "candidate menu offset")
        consumed += len(group)
        h_eligible = len(members) >= 2 and np.isfinite(raw["plan_bs"][index]).all()
        fallback = 2 if not np.isfinite(raw["plan_bs"][index]).all() else 1 if len(members) < 2 else 0
        action = int(choices[index]["requested_action"]) if program in _MIXED else int(program == "H_T" and h_eligible)
        equal(raw["plan_fallback"][index], fallback, "lawful fallback reason")
        if program in _MIXED:
            choice = choices[index]
            equal(choice["eligible"], eligible, "choice eligible members")
            equal(choice["m"], len(members), "choice eligible count")
            equal(choice["h_eligible"], h_eligible, "choice eligibility")
            equal(choice["forced_reason"], fallback, "choice forced reason")
            equal(choice["ordinary_targets"], ordinary, "choice ordinary targets")
            equal(choice["committed_targets"], raw["plan_targets"][index], "choice committed targets")
            equal(choice["candidate_first"], consumed - len(group), "choice menu offset")
            equal(choice["candidate_count"], len(group), "choice menu length")
        if program != "C":
            equal(raw["plan_user_count"][index], raw["trace_current_count"][tick], "static current-user count")
            equal(raw["plan_users"][index], raw["trace_canonical"][tick], "original C canonical current map")
        if not action:
            if len(group) or raw["plan_candidate_count"][index] != 0:
                raise AssertionError("private query work on C-selected/ineligible interval")
            equal(raw["plan_targets"][index], ordinary, "C leaves ordinary targets committed")
            equal(raw["plan_selected_candidate"][index], -1, "no H selection on C")
            continue
        pairs = [(-1, -1)] + list(combinations(members.tolist(), 2))
        equal(len(group), len(pairs), "all and only lexicographic pair candidates")
        equal(raw["plan_candidate_count"][index], len(pairs), "plan menu length")
        for candidate_index, (record, pair) in enumerate(zip(group, pairs)):
            equal([record["pair_left"], record["pair_right"]], pair, "lexicographic unordered service pair")
            candidate = ordinary.copy()
            if candidate_index:
                candidate[list(pair)] = candidate[list(pair[::-1])]
            equal(record["targets"][:, :2], candidate, "target-multiset preserving swap")
            equal(record["q"], raw["plan_user_count"][index], "current-user query count")
            equal(record["score"], 10. * np.sum(record["qos"] - 2. * record["return_cost"]),
                  "literal native proxy score")
            equal(record["alias_base"], bool(candidate_index and np.array_equal(candidate, ordinary, equal_nan=True)),
                  "coordinate alias of base")
        scores, travel = group["score"], group["forecast_travel"]
        if not np.isfinite(travel).all():
            raise AssertionError("nonfinite candidate travel")
        accepted = np.zeros(len(group), bool)
        incumbent = -np.inf
        for candidate_index, score in enumerate(scores):
            if score > incumbent:
                accepted[candidate_index] = True
                incumbent = score
        equal(group["accepted"], accepted, "literal provisional running-score acceptances")
        top = np.flatnonzero(scores == np.max(scores))
        # Base dominates all travel ties only when its score is an exact maximum.
        winner = 0 if scores[0] == np.max(scores) else min(map(int, top), key=lambda k: (float(travel[k]), k))
        equal(raw["plan_selected_candidate"][index], winner, "literal H_T score/travel/index selection")
        equal(raw["plan_selected_pair"][index], pairs[winner], "selected pair provenance")
        equal(np.flatnonzero(group["selected"]), [winner], "one selected H_T candidate")
        equal(raw["plan_targets"][index], group[winner]["targets"][:, :2], "actual selected commit")
        q = int(raw["plan_user_count"][index])
        equal(raw["plan_prediction_xy"][index, :, :q], np.repeat(raw["plan_users"][index, None, :q], 3, axis=0),
              "H static current anonymous users")
        if program in _MIXED:
            equal(choice["selected"], winner, "choice selected candidate")
            equal(choice["h_selected"], int(top[0]), "old H incumbent")
            equal(choice["tie_changed"], winner != int(top[0]), "travel tie changed incumbent")
            equal(choice["h_selected_base"], winner == 0, "H-selected base diagnostic")
            equal(choice["selected_pair_alias"], group[winner]["alias_base"], "H-selected pair alias")
    equal(consumed, len(records), "no orphan candidate menus")


def replay_episode(raw: dict, row: dict, *, learner: Learner | None = None,
                   stop_check: Callable | None = None) -> dict:
    """Verify one completed mission; the first failure propagates without retry.

    stop_check is a zero-argument budget callback. Raw identity, job selection,
    checkpoint cadence and cross-mission sequencing remain the caller's work.
    """
    def stop():
        if stop_check is not None:
            stop_check()

    stop()
    if row.get("status", "completed") != "completed":
        raise AssertionError("complete-mission reader refuses failed/partial prefixes")
    program, phase = row["program"], row["phase"]
    if program not in _PROGRAMS or phase not in ("audit", "train", "calibration", "final"):
        raise ValueError("unknown B01 program/phase")
    if (program == "SELECTOR") != (learner is not None):
        raise ValueError("SELECTOR requires its persistent learner; ordinary programs forbid one")
    if (phase == "train" and program != "SELECTOR") or (program == "SELECTOR" and phase not in ("train", "final")):
        raise ValueError("learning occurs only in SELECTOR training missions")
    n = row["actual_length"]
    if type(n) is not int or not 1 <= n <= 3000 or row["limit"] != 3000:
        raise AssertionError("complete native finite-mission length/limit")
    equal(raw["plan_step"], np.arange(0, n, 30), "all and only true plan boundaries")
    # H_A is ONLY the retained modeled-record schema label, not its selection rule.
    records = validate_candidate_records(raw, "C" if program == "C" else "H_A", True)
    for record in records:
        validate_candidate_record(record)
    choices = _check_choices(raw, program, n)
    _check_assignment_menu(raw, program, choices)
    stop()
    native = check_native(raw, row, phase)
    stop()
    # Reconstruct endpoints from recorded native/feedback evidence, independently
    # of private candidate values and learner answers.
    original = world_row(row["seed"], raw["reward"], raw["metrics"], raw["ends"], raw, time_step_s=1.)
    original.update(mechanism_row(raw, absolute_station_xy(raw["observations"][0])))
    original.update(position_diagnostics(raw["metrics"], raw, area_size_m=8000., floor_m=50.))
    numeric_row_equal(row, original, "original evaluator reductions")
    numeric_row_equal(row, episode_metrics(raw), "independent complete-mission reductions")
    stop()
    learning_before = learner.counts() if learner is not None else None
    if learner is not None:
        learner.start_episode(row["episode_index"], training=phase == "train")
    controller = make_controller(program, chooser=learner.decide if learner is not None else None,
                                 theta=row.get("theta"), initial_parity=row.get("initial_parity", 0))
    active_error = False
    try:
        controller.reset()
        # A bounded prefix blocks any query beyond the actually purchased menu.
        controller.replay_prefix = records
        if program in _MIXED:
            controller.replay_choice_prefix = choices
        modes, previous_done = np.zeros(8, bool), np.ones(1, bool)
        plan_index = 0
        plan_keys, memory_keys, decision_keys = set(), set(), {
            "proposed", "target_xy", "decision_targets_xyz"}
        for tick in range(n):
            if tick % 30 == 0:
                stop()  # Before expensive private search or boundary Adam update.
            obs = raw["observations"][tick]
            proposal = controller.propose(obs, UnavailableTruth(), tick, previous_done, modes.copy())
            equal(proposal, raw["proposed"][tick], "actual-path proposed commands")
            equal(controller.heuristic.calls, tick + 1, "one actual inherited act per primitive tick")
            equal(controller.targets_xy, raw["target_xy"][tick], "actual held xy targets")
            targets_xyz = getattr(controller, "targets_xyz", None)
            if targets_xyz is None:
                targets_xyz = np.column_stack((controller.heuristic.targets_xy, np.full(8, 100.)))
            equal(targets_xyz, raw["decision_targets_xyz"][tick], "actual held xyz targets")
            decision = apply_feedback_params(obs, proposal, modes, PRODUCTION_PARAMS)
            values = dict(submitted=decision.submitted_actions, mode=decision.modes,
                          entered=decision.entered, exited=decision.exited,
                          return_margin=decision.margins, nearest_station=decision.selected_stations,
                          nearest_station_distance_m=decision.station_distances_m,
                          own_xyz=own_positions(obs), dock_bit=decision.submitted_actions[:, 3] > .5)
            held = own_energy(obs)
            values.update(station_occupancy=station_counts(decision.selected_stations, held["charging"]),
                          station_queue=station_counts(decision.selected_stations, held["waiting_steps"] > 0))
            post = own_energy(raw["observations"][tick + 1])
            values.update({name: post[name] for name in ("charging", "waiting_steps", "battery")})
            decision_keys.update(values)
            _compare_typed_records(raw, values, tick, "actual feedback/decision decode")
            if tick % 30 == 0:
                plan = plan_record(controller, tick)
                plan_keys.update(plan)
                _compare_typed_records(raw, plan, plan_index, "actual plan")
                plan_index += 1
            if program != "C":
                trace = controller.last_trace
                equal([trace["step"], trace["replanned"]], [tick, tick % 30 == 0], "actual tracker clock")
                memory = memory_record(trace)
                memory_keys.update(memory)
                _compare_typed_records(raw, memory, tick, "actual primitive memory")
            terminal = bool(raw["native_ends"][tick].any())
            if learner is not None:
                if terminal:
                    stop()  # Before the final (possibly partial) block update.
                learner.observe_reward(float(raw["native_reward"][tick]), terminal)
            modes = decision.modes
            previous_done[:] = terminal
            if (tick + 1) % 100 == 0:
                stop()
        stop()
        for key in decision_keys:
            equal(len(raw[key]), n, "complete primitive decision-array count/" + key)
        for key in plan_keys:
            equal(len(raw[key]), plan_index, "complete plan-array count/" + key)
        for key in memory_keys:
            equal(len(raw[key]), n, "complete memory-array count/" + key)
        # Reject unrecognized saved policy/learner arrays instead of silently
        # excluding them from a purported complete replay.
        recorded_plan_keys = {key for key in raw if key.startswith("plan_")}
        recorded_memory_keys = {key for key in raw if key.startswith(("trace_", "event_"))}
        if recorded_plan_keys != plan_keys or recorded_memory_keys != memory_keys:
            raise AssertionError("saved plan/memory schema differs from reconstructed schema")
        audit = controller.audit_arrays() if hasattr(controller, "audit_arrays") else {
            "candidate_records": np.empty(0, CANDIDATE_DTYPE)}
        compare_candidate_prefix(audit["candidate_records"], records)
        for key, value in audit.items():
            if key not in raw:
                raise AssertionError("missing controller audit/" + key)
            _same_array(value, raw[key], "actual controller audit/" + key)
        diagnostics = diagnostic_bytes(getattr(controller, "choice_diagnostics", []))
        _same_array(diagnostics, raw["choice_diagnostics_json"], "all choice diagnostics")
        counts = dict(controller.counters)
        if counts != row["policy_counts"]:
            raise AssertionError("deployment/replay actual-work count mismatch")
        for key, value in expected_counts(program, n).items():
            equal(counts.get(key, 0), value, "fixed primitive accounting/" + key)
        for key, value in dict(candidate_forecasts=len(records), candidate_forecasts_completed=len(records),
                               joint_forecast_ticks=30 * len(records), joint_forecast_ticks_completed=30 * len(records),
                               model_score_calls=3 * len(records), model_score_calls_completed=3 * len(records)).items():
            equal(counts.get(key, 0), value, "complete paid-query accounting/" + key)
        learn = {} if learner is None else {"learn_" + key: value for key, value in learner.episode_arrays().items()}
        if {key for key in raw if key.startswith("learn_")} != set(learn):
            raise AssertionError("saved learner schema differs from reconstructed schema")
        for key, value in learn.items():
            _same_array(value, raw[key], "actual learner/" + key)
        learner_counts = learner.counts() if learner is not None else None
        learner_digests = learner.digests() if learner is not None else None
        if learner is not None:
            if learner_counts != row["learner_counts"] or learner_digests != row["learner_digests"]:
                raise AssertionError("mission learner clocks/parameter/target/optimizer digest mismatch")
        updates = 0 if learner is None else learner_counts["updates"] - learning_before["updates"]
        if phase != "train" and updates:
            raise AssertionError("optimizer update during inference")
        stop()
        reproduced = audit | learn | {"choice_diagnostics_json": diagnostics}
        return dict(status="verified", success=True, job_key=row["job_key"],
                    policy_counts=counts, verified_actual_proposals=n, verified_feedback_calls=n,
                    plans_checked=plan_index, choices_checked=len(choices), candidate_records_checked=len(records),
                    repeated_candidate_forecasts=counts.get("candidate_forecasts", 0),
                    repeated_nominal_ticks=counts.get("joint_forecast_ticks_completed", 0),
                    repeated_model_score_queries=counts.get("model_score_calls_completed", 0),
                    repeated_model_rf_queries=counts.get("model_rf_calls_completed", 0),
                    verification_optimizer_updates=updates, replay_presentations=updates * 64,
                    learner_counts=learner_counts, learner_digests=learner_digests,
                    native_arithmetic=native, full_native_rf_resimulation=False, new_native_steps=0,
                    raw_array_checksums={key: array_digest(value) for key, value in sorted(raw.items())},
                    reproduced_array_checksums={key: array_digest(value) for key, value in sorted(reproduced.items())})
    except BaseException:
        active_error = True
        raise
    finally:
        close = getattr(controller, "close", None)
        if close is not None:
            if active_error:
                # Resource-close failure must not replace the first read failure.
                try:
                    close()
                except Exception:
                    pass
            else:
                close()
