"""Primitive-time model segments with physical/report/controller separation."""
from copy import deepcopy

import numpy as np

from ..b02.controller import Program, COUNT_KEYS, empty_counts, trace_counts
from ..b02.option import arrival_mask
from ..b03.surrogate import encode_model_report, _integer, _report, REWARD_COMPONENTS
from ..control import OrdinaryController, _Scores, decode_public_state, predict_next
from ..host import mask_bits


def validate_plan(plan, old_mask, start_t):
    if plan is None:
        return None
    plan = deepcopy(plan)
    if not isinstance(plan, dict) or not isinstance(plan.get("initiated"), bool):
        raise ValueError("plan must explicitly record initiation")
    if _integer(plan.get("start_t", start_t), "plan start") != start_t:
        raise ValueError("expired or mismatched plan was not replaced")
    if not plan["initiated"]:
        return plan
    duration, arrival, member = (_integer(plan[key], key) for key in ("duration", "arrival_t", "member"))
    if duration not in (10, 20, 30, 40) or arrival != start_t+duration or not 0 <= member < 8:
        raise ValueError("plan must preserve its fixed aligned start/arrival/duration")
    if mask_bits(old_mask, 8)[member]:
        raise ValueError("option member is already transmitting")
    commands = np.asarray(plan["commands"], dtype=np.float32)
    destination = np.asarray(plan["predicted_destination"], dtype=np.float64)
    if (commands.shape != (duration, 8, 3) or not np.isin(commands, [-1., 0., 1.]).all()
            or np.any(np.delete(commands, member, axis=1))
            or destination.shape != (8, 3) or not np.isfinite(destination).all()):
        raise ValueError("fixed silent-member commands/destination are malformed")
    return plan


class OptionProgram(Program):
    """Only the option command index is parameterized; C/_forced stay frozen."""
    def select(self, t, state, old_mask):
        if t != self.controller.next_t or ((state is not None) != (t % 10 == 0)):
            raise ValueError("invalid clock or public snapshot cadence")
        if self.plan is None or not self.plan["initiated"] or t > self.plan["arrival_t"]:
            return super().select(t, state, old_mask)
        if old_mask != self.option_old_mask:
            raise ValueError("transit changed the old mask")
        start = self.plan.get("start_t", 40)
        if t < start:
            raise ValueError("option executed before its scheduled commitment")
        decision = dict(t=t, old_mask=int(old_mask), phase="transit")
        if t < self.plan["arrival_t"]:
            command = self._forced(t, state, self.plan["commands"][t-start])
        else:
            positions, users = decode_public_state(state, 8)
            command = self._forced(t, state, np.zeros((8, 3), dtype=np.float32))
            old_mask, trace = arrival_mask(users, positions, self.plan["member"])
            decision.update(arrival=trace, phase="arrival",
                arrival_prediction_error=(positions-np.asarray(self.plan["predicted_destination"])).tolist())
        decision["issued_mask"] = int(old_mask)
        return command, int(old_mask), decision


def simulate_segment(controller, public_state, old_mask, plan=None, *, start_t=40,
                     end_t=500, report_horizon=500, physical_positions=None):
    start_t, end_t = _integer(start_t, "start_t"), _integer(end_t, "end_t")
    if report_horizon != 500 or start_t not in (40, 120) or not start_t < end_t <= 500:
        raise ValueError("fixed report horizon and lawful nonempty 40/120 segment required")
    if not isinstance(controller, OrdinaryController) or controller.n_uavs != 8 or controller.next_t != start_t:
        raise ValueError("segment requires the actual scheduled N8 history")
    if (controller.commands.dtype != np.float32 or controller.commands.shape != (8, 3)
            or not np.isin(controller.commands, [-1., 0., 1.]).all()):
        raise ValueError("history must preserve float32 ternary issued commands")
    for value, shape in ((controller.positions, (8, 3)), (controller.users, (50, 2))):
        if np.asarray(value).shape != shape or not np.isfinite(value).all():
            raise ValueError("history must be finite")
    original = _report(public_state)
    decoded, users = decode_public_state(original, 8)
    positions = decoded if physical_positions is None else np.asarray(physical_positions, dtype=np.float64).copy()
    if positions.shape != (8, 3) or not np.isfinite(positions).all():
        raise ValueError("outer physical state must be finite N8 positions")
    mask_bits(old_mask, 8)
    program = OptionProgram("C", report_horizon)
    program.controller = deepcopy(controller)
    program.plan, program.option_old_mask = validate_plan(plan, old_mask, start_t), int(old_mask)
    count = end_t-start_t
    arrays = dict(positions=np.empty((count+1, 8, 3), np.float64), actions=np.empty((count, 8, 3), np.float32),
        masks=np.empty(count, np.int64), reward_components=np.empty((count, 4), np.float64),
        controller_estimates=np.empty((count+1, 8, 3), np.float64))
    arrays["positions"][0], arrays["controller_estimates"][0] = positions, controller.positions
    reports, times, decisions = [], [], []
    controller_counts, reward_counts = empty_counts(), {k: 0 for k in COUNT_KEYS}
    for i, t in enumerate(range(start_t, end_t)):
        state = None
        if t % 10 == 0:
            state = original.copy() if t == start_t else encode_model_report(positions, original, t, report_horizon)
            reports.append(state.copy())
            times.append(t)
        command, old_mask, decision = program.select(t, state, old_mask)
        moved = predict_next(positions, command)
        scorer = _Scores(users)
        score = scorer.score(moved, [old_mask])[0]
        for key in COUNT_KEYS:
            reward_counts[key] += int(scorer.counts[key])
        trace_counts(decision, controller_counts)
        arrays["positions"][i+1], arrays["actions"][i], arrays["masks"][i] = moved, command, old_mask
        arrays["reward_components"][i] = [score[k] for k in REWARD_COMPONENTS]
        arrays["controller_estimates"][i+1] = program.controller.positions
        decisions.append(deepcopy(decision))
        positions = moved
    arrays.update(report_times=np.asarray(times, np.int64), reports=np.asarray(reports, np.float32))
    result = dict(arrays=arrays, decisions=decisions,
        summary=summarize(arrays, start_t, end_t, controller_counts, reward_counts),
        terminal_controller=deepcopy(program.controller), terminal_mask=int(old_mask))
    return result


def summarize(arrays, start_t, end_t, controller_counts, reward_counts):
    totals = [0., 0, 0., 0.]
    path = 0.
    for i, reward in enumerate(arrays["reward_components"]):
        totals[0] += float(reward[0])
        totals[1] += int(reward[1])
        totals[2] += float(reward[2])
        totals[3] += float(reward[3])
        path += float(np.linalg.norm(arrays["positions"][i+1]-arrays["positions"][i], axis=1).sum())
    return dict(start_t=start_t, end_t=end_t, horizon=500, model_transitions=end_t-start_t,
        total_J=totals[0], total_served=totals[1], total_quality=totals[2], total_energy_penalty=totals[3],
        total_path=path, controller_counts=deepcopy(controller_counts), reward_counts=deepcopy(reward_counts),
        ordinary_candidate_position_predictions=int(controller_counts["motion"]["requested_candidates"]),
        reward_component_columns=REWARD_COMPONENTS.copy())


def concatenate(prefix, suffix):
    if prefix["summary"]["end_t"] != suffix["summary"]["start_t"]:
        raise ValueError("noncontiguous model segments")
    if not np.array_equal(prefix["arrays"]["positions"][-1], suffix["arrays"]["positions"][0]):
        raise ValueError("outer physical state replaced at the nested boundary")
    arrays = {}
    for key in prefix["arrays"]:
        right = suffix["arrays"][key]
        if key in ("positions", "controller_estimates"):
            right = right[1:]
        arrays[key] = np.concatenate((prefix["arrays"][key], right), axis=0)
    cc, rc = empty_counts(), {k: 0 for k in COUNT_KEYS}
    for result in (prefix, suffix):
        for kind in cc:
            for key in COUNT_KEYS:
                cc[kind][key] += result["summary"]["controller_counts"][kind][key]
        for key in COUNT_KEYS:
            rc[key] += result["summary"]["reward_counts"][key]
    summary = summarize(arrays, prefix["summary"]["start_t"], suffix["summary"]["end_t"], cc, rc)
    summary["segments"] = [deepcopy(prefix["summary"]), deepcopy(suffix["summary"])]
    return dict(arrays=arrays, decisions=deepcopy(prefix["decisions"]+suffix["decisions"]), summary=summary,
                terminal_controller=deepcopy(suffix["terminal_controller"]), terminal_mask=suffix["terminal_mask"])
