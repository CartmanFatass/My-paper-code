"""Exact, branch-local recurrence for B04's fixed 40/120 model segments.

Certificates are separate from the frozen scientific summaries. Array envelopes
retain every bit, including issued negative zero and unrounded outer positions.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import struct

import numpy as np

from experiments.candidates.uav_fleet_transmission.b02.controller import COUNT_KEYS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b03 import surrogate as b03
from experiments.candidates.uav_fleet_transmission.b04 import surrogate as b04
from experiments.candidates.uav_fleet_transmission.control import OrdinaryController, _Scores, decode_public_state, predict_next
from experiments.candidates.uav_fleet_transmission.host import mask_bits

KEY_LAYOUT = "<i8 phase40,mask,n_uavs; <f8 physical[8,3],estimated[8,3],users[50,2]; <f4 issued[8,3],public_users[100]"


@dataclass(frozen=True)
class SegmentDependencies:
    """Explicit transition/scorer binding; synthetic tests replace these only."""
    program: object = b04.OptionProgram
    predict: object = predict_next
    scorer: object = _Scores


DEFAULT_DEPENDENCIES = SegmentDependencies()


def encode_array(value):
    value = np.asarray(value)
    dtype = value.dtype.newbyteorder("<")
    value = value.astype(dtype, copy=False)
    return dict(dtype=dtype.str, shape=list(value.shape), hex=value.tobytes(order="C").hex())


def boundary(history, physical, mask):
    return dict(next_t=int(history.next_t), n_uavs=int(history.n_uavs), mask=int(mask),
                physical=encode_array(physical), positions=encode_array(history.positions),
                users=encode_array(history.users), commands=encode_array(history.commands))


def validate_entry(controller, report, old_mask, start_t):
    if not isinstance(controller, OrdinaryController) or controller.n_uavs != 8 or controller.next_t != start_t:
        raise ValueError("segment requires the actual scheduled N8 history")
    for value, shape, dtype in ((controller.positions, (8, 3), np.float64),
                                (controller.users, (50, 2), np.float64),
                                (controller.commands, (8, 3), np.float32)):
        value = np.asarray(value)
        if value.shape != shape or value.dtype != np.dtype(dtype) or not np.isfinite(value).all():
            raise ValueError("history must preserve its finite FP64/FP32 bits")
    if not np.isin(controller.commands, [-1., 0., 1.]).all():
        raise ValueError("history must preserve float32 ternary issued commands")
    report = b03._report(report)
    _, users = decode_public_state(report, 8)
    if users.tobytes() != controller.users.tobytes():
        raise ValueError("static public users disagree with the entering history")
    mask_bits(old_mask, 8)
    return report


def recurrence_key(t, positions, history, old_mask, original_report):
    parts = []
    for value, shape, dtype in ((positions, (8, 3), np.float64),
                                (history.positions, (8, 3), np.float64),
                                (history.users, (50, 2), np.float64),
                                (history.commands, (8, 3), np.float32),
                                (original_report[32:132], (100,), np.float32)):
        value = np.asarray(value)
        if value.shape != shape or value.dtype != np.dtype(dtype) or not np.isfinite(value).all():
            raise ValueError("recurrence requires the original finite FP64/FP32 state bits")
        parts.append(value.astype(np.dtype(dtype).newbyteorder("<"), copy=False).tobytes(order="C"))
    return struct.pack("<qqq", int(t) % 40, int(old_mask), int(history.n_uavs)) + b"".join(parts)


def _requests(counts):
    return sum(kind["requested_candidates"] for kind in counts.values())


def full_work(result, start_t, end_t, barrier):
    """Original work accounting, without a transition/scorer query."""
    cc, rc = result["summary"]["controller_counts"], result["summary"]["reward_counts"]
    count = end_t - start_t
    predictions = result["summary"]["ordinary_candidate_position_predictions"]
    return dict(schema="b08_exact_recurrence.v1", key_layout=KEY_LAYOUT,
        eligibility_after_t=int(barrier), computed_ticks=count, reused_ticks=0,
        logical_controller_calls=count, actual_controller_calls=count,
        logical_reward_calls=count, actual_reward_calls=count,
        logical_controller_counts=deepcopy(cc), actual_controller_counts=deepcopy(cc),
        logical_reward_counts=deepcopy(rc), actual_reward_counts=deepcopy(rc),
        logical_controller_requests=_requests(cc), actual_controller_requests=_requests(cc),
        logical_reward_requests=rc["requested_candidates"], actual_reward_requests=rc["requested_candidates"],
        logical_requested_candidates=_requests(cc)+rc["requested_candidates"],
        actual_requested_candidates=_requests(cc)+rc["requested_candidates"],
        logical_candidate_position_predictions=predictions, actual_candidate_position_predictions=predictions,
        first_repeat=None, source_times=list(range(start_t, end_t)))


def reconstruct_terminal(controller, result, end_t):
    """B03/B06 omit terminal history; recover it from their complete outputs."""
    history = deepcopy(controller)
    arrays = result["arrays"]
    history.positions = arrays["controller_estimates"][-1].copy()
    history.commands = arrays["actions"][-1].copy()
    _, history.users = decode_public_state(arrays["reports"][-1], 8)
    history.next_t = end_t
    return history, int(arrays["masks"][-1])


def certify(result, controller, report, mask, plan, start_t, end_t, *, physical_positions=None, reuse=None):
    """Attach a copied boundary/reuse certificate; scientific fields stay intact."""
    report = validate_entry(controller, report, mask, start_t)
    physical = decode_public_state(report, 8)[0] if physical_positions is None else np.asarray(physical_positions, np.float64).copy()
    barrier = plan["arrival_t"] if plan is not None and plan["initiated"] else start_t
    history, terminal_mask = (result["terminal_controller"], result["terminal_mask"]) if "terminal_controller" in result else reconstruct_terminal(controller, result, end_t)
    work = deepcopy(reuse) if reuse is not None else full_work(result, start_t, end_t, barrier)
    reports = len(result["arrays"]["report_times"])
    work.update(logical_report_calls=reports, actual_report_calls=reports)
    result["certificate"] = dict(schema="b08_exact_segment.v1", start_t=start_t, end_t=end_t,
        report_horizon=500, plan=deepcopy(plan), entry_report=encode_array(report),
        entry=boundary(controller, physical, mask),
        terminal=boundary(history, result["arrays"]["positions"][-1], terminal_mask), reuse=work)
    return result


def simulate_segment(controller, public_state, old_mask, plan=None, *, start_t=40,
                     end_t=500, report_horizon=500, physical_positions=None, reuse=False,
                     dependencies=DEFAULT_DEPENDENCIES):
    """Original binding or exact local reuse with fixed report denominator500."""
    start_t, end_t = b03._integer(start_t, "start_t"), b03._integer(end_t, "end_t")
    if report_horizon != 500 or start_t not in (40, 120) or not start_t < end_t <= 500:
        raise ValueError("fixed report horizon and lawful nonempty 40/120 segment required")
    if start_t == 40 and end_t > 120:
        raise ValueError("B04 prefix cannot cross its t120 decision boundary")
    original = validate_entry(controller, public_state, old_mask, start_t)
    if not reuse:
        result = b04.simulate_segment(controller, public_state, old_mask, plan, start_t=start_t,
            end_t=end_t, report_horizon=report_horizon, physical_positions=physical_positions)
        return certify(result, controller, public_state, old_mask, plan, start_t, end_t,
                       physical_positions=physical_positions)
    decoded, users = decode_public_state(original, 8)
    positions = decoded if physical_positions is None else np.asarray(physical_positions, np.float64).copy()
    if positions.shape != (8, 3) or not np.isfinite(positions).all():
        raise ValueError("outer physical state must be finite N8 positions")
    mask_bits(old_mask, 8)
    entering_mask = int(old_mask)
    program = dependencies.program("C", report_horizon)
    program.controller = deepcopy(controller)
    program.plan, program.option_old_mask = b04.validate_plan(plan, old_mask, start_t), int(old_mask)
    history = program.controller
    barrier = program.plan["arrival_t"] if program.plan is not None and program.plan["initiated"] else start_t
    count = end_t-start_t
    arrays = dict(positions=np.empty((count+1, 8, 3), np.float64), actions=np.empty((count, 8, 3), np.float32),
        masks=np.empty(count, np.int64), reward_components=np.empty((count, 4), np.float64),
        controller_estimates=np.empty((count+1, 8, 3), np.float64))
    arrays["positions"][0], arrays["controller_estimates"][0] = positions, controller.positions
    reports, times, decisions, sources = [], [], [], []
    cc, actual_cc = empty_counts(), empty_counts()
    rc, actual_rc = {k: 0 for k in COUNT_KEYS}, {k: 0 for k in COUNT_KEYS}
    computed, cache, first_repeat = 0, {}, None
    for i, t in enumerate(range(start_t, end_t)):
        state = None
        if t % 10 == 0:
            state = original.copy() if t == start_t else b03.encode_model_report(positions, original, t, report_horizon)
            reports.append(state.copy())
            times.append(t)
        key = recurrence_key(t, positions, history, old_mask, original) if t > barrier else None
        cached = cache.get(key) if key is not None else None
        if cached is None:
            command, old_mask, decision = program.select(t, state, old_mask)
            command = np.asarray(command, np.float32)
            moved = dependencies.predict(positions, command)
            scorer = dependencies.scorer(users)
            score = scorer.score(moved, [old_mask])[0]
            reward_counts = dict(scorer.counts)
            trace_counts(decision, actual_cc)
            for k in COUNT_KEYS:
                actual_rc[k] += int(reward_counts[k])
            source_t, computed = t, computed+1
            if key is not None:
                cache[key] = dict(source_t=t, command=command.copy(), mask=int(old_mask), decision=deepcopy(decision),
                    physical=moved.copy(), positions=history.positions.copy(), commands=history.commands.copy(),
                    users=history.users.copy(), score=deepcopy(score), reward_counts=reward_counts)
        else:
            source_t = cached["source_t"]
            if first_repeat is None:
                first_repeat = dict(source_t=source_t, repeat_t=t, period=t-source_t, phase=t % 40,
                    entering_mask=int(old_mask), key_sha256=hashlib.sha256(key).hexdigest())
            command, old_mask, moved = cached["command"].copy(), cached["mask"], cached["physical"].copy()
            decision, score, reward_counts = deepcopy(cached["decision"]), cached["score"], cached["reward_counts"]
            decision["t"] = t
            history.positions, history.commands, history.users = cached["positions"].copy(), cached["commands"].copy(), cached["users"].copy()
            history.next_t = t+1
        sources.append(source_t)
        trace_counts(decision, cc)
        for k in COUNT_KEYS:
            rc[k] += int(reward_counts[k])
        arrays["positions"][i+1], arrays["actions"][i], arrays["masks"][i] = moved, command, old_mask
        arrays["reward_components"][i] = [score[k] for k in b03.REWARD_COMPONENTS]
        arrays["controller_estimates"][i+1] = history.positions
        decisions.append(deepcopy(decision))
        positions = moved
    arrays.update(report_times=np.asarray(times, np.int64), reports=np.asarray(reports, np.float32))
    result = dict(arrays=arrays, decisions=decisions, summary=b04.summarize(arrays, start_t, end_t, cc, rc),
        terminal_controller=deepcopy(history), terminal_mask=int(old_mask))
    work = full_work(result, start_t, end_t, barrier)
    work.update(computed_ticks=computed, reused_ticks=count-computed, actual_controller_calls=computed,
        actual_reward_calls=computed, actual_controller_counts=actual_cc, actual_reward_counts=actual_rc,
        actual_controller_requests=_requests(actual_cc), actual_reward_requests=actual_rc["requested_candidates"],
        actual_requested_candidates=_requests(actual_cc)+actual_rc["requested_candidates"],
        actual_candidate_position_predictions=actual_cc["motion"]["requested_candidates"],
        first_repeat=first_repeat, source_times=sources)
    return certify(result, controller, original, entering_mask, plan, start_t, end_t,
                   physical_positions=physical_positions, reuse=work)
