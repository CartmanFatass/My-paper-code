"""Rolling-clock model segments; original B08 key and local certificates."""

from copy import deepcopy
import hashlib

import numpy as np

from experiments.candidates.uav_fleet_transmission.b02.controller import COUNT_KEYS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b03 import surrogate as b03
from experiments.candidates.uav_fleet_transmission.b04 import surrogate as b04
from experiments.candidates.uav_fleet_transmission.control import decode_public_state
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.segment import (
    SegmentDependencies, DEFAULT_DEPENDENCIES, recurrence_key, validate_entry, certify, full_work,
)
from .option import STARTS


def simulate_segment(controller, public_state, old_mask, plan=None, *, start_t=40, end_t=500,
                     report_horizon=500, physical_positions=None, reuse=True, dependencies=DEFAULT_DEPENDENCIES):
    start_t, end_t = b03._integer(start_t, "start_t"), b03._integer(end_t, "end_t")
    if report_horizon != 500 or start_t not in STARTS or not start_t < end_t <= 500:
        raise ValueError("lawful rolling segment under fixed report denominator500 required")
    original = validate_entry(controller, public_state, old_mask, start_t)
    entering_mask = int(old_mask)
    decoded, users = decode_public_state(original, 8)
    positions = decoded if physical_positions is None else np.asarray(physical_positions, np.float64).copy()
    if positions.shape != (8, 3) or not np.isfinite(positions).all():
        raise ValueError("outer physical state must be finite N8 positions")
    program = dependencies.program("C", report_horizon)
    program.controller = deepcopy(controller)
    program.plan, program.option_old_mask = b04.validate_plan(plan, old_mask, start_t), entering_mask
    history = program.controller
    barrier = program.plan["arrival_t"] if program.plan is not None and program.plan["initiated"] else start_t
    count = end_t - start_t
    arrays = dict(positions=np.empty((count + 1, 8, 3), np.float64), actions=np.empty((count, 8, 3), np.float32),
                  masks=np.empty(count, np.int64), reward_components=np.empty((count, 4), np.float64),
                  controller_estimates=np.empty((count + 1, 8, 3), np.float64))
    arrays["positions"][0], arrays["controller_estimates"][0] = positions, history.positions
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
        key = recurrence_key(t, positions, history, old_mask, original) if reuse and t > barrier else None
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
            source_t, computed = t, computed + 1
            if key is not None:
                cache[key] = dict(source_t=t, command=command.copy(), mask=int(old_mask), decision=deepcopy(decision),
                                  physical=moved.copy(), positions=history.positions.copy(), commands=history.commands.copy(),
                                  users=history.users.copy(), score=deepcopy(score), reward_counts=reward_counts)
        else:
            source_t = cached["source_t"]
            if first_repeat is None:
                first_repeat = dict(source_t=source_t, repeat_t=t, period=t - source_t, phase=t % 40,
                                    entering_mask=int(old_mask), key_sha256=hashlib.sha256(key).hexdigest())
            command, old_mask, moved = cached["command"].copy(), cached["mask"], cached["physical"].copy()
            decision, score, reward_counts = deepcopy(cached["decision"]), cached["score"], cached["reward_counts"]
            decision["t"] = t
            history.positions, history.commands, history.users = cached["positions"].copy(), cached["commands"].copy(), cached["users"].copy()
            history.next_t = t + 1
        sources.append(source_t)
        trace_counts(decision, cc)
        for k in COUNT_KEYS:
            rc[k] += int(reward_counts[k])
        arrays["positions"][i + 1], arrays["actions"][i], arrays["masks"][i] = moved, command, old_mask
        arrays["reward_components"][i] = [score[k] for k in b03.REWARD_COMPONENTS]
        arrays["controller_estimates"][i + 1] = history.positions
        decisions.append(deepcopy(decision))
        positions = moved
    arrays.update(report_times=np.asarray(times, np.int64), reports=np.asarray(reports, np.float32))
    result = dict(arrays=arrays, decisions=decisions, summary=b04.summarize(arrays, start_t, end_t, cc, rc),
                  terminal_controller=deepcopy(history), terminal_mask=int(old_mask))
    work = full_work(result, start_t, end_t, barrier)
    work.update(computed_ticks=computed, reused_ticks=count - computed, actual_controller_calls=computed,
                actual_reward_calls=computed, actual_controller_counts=actual_cc, actual_reward_counts=actual_rc,
                actual_controller_requests=sum(v["requested_candidates"] for v in actual_cc.values()),
                actual_reward_requests=actual_rc["requested_candidates"],
                actual_requested_candidates=sum(v["requested_candidates"] for v in actual_cc.values()) + actual_rc["requested_candidates"],
                actual_candidate_position_predictions=actual_cc["motion"]["requested_candidates"],
                first_repeat=first_repeat, source_times=sources)
    return certify(result, controller, original, entering_mask, plan, start_t, end_t,
                   physical_positions=physical_positions, reuse=work)
