"""Exact state recurrence for the frozen B03 complete ordinary continuation.

Only ticks strictly after the final event are eligible. The ordinary transition
depends on time modulo lcm(8,10)=40; decoded reports ignore their absolute time
coordinate. Full byte keys certify equality, while hashes are only evidence.
"""

from copy import deepcopy
import hashlib
import struct

import numpy as np

from experiments.candidates.uav_fleet_transmission.b02.controller import (
    Program, COUNT_KEYS, empty_counts, trace_counts,
)
from experiments.candidates.uav_fleet_transmission.control import (
    _Scores, decode_public_state, predict_next,
)
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.b03.surrogate import (
    REWARD_COMPONENTS, _integer, _report, _copy_history, _copy_plan, encode_model_report,
)

KEY_LAYOUT = "<i8 phase40,mask; <f8 physical[8,3],estimated[8,3]; <f4 issued[8,3],public_users[50,2]"


def recurrence_key(t, positions, history, old_mask, original_report):
    """Fixed-layout actual bytes, including signed zeros and every FP bit."""
    parts = []
    for value, shape, dtype in ((positions, (8, 3), np.float64),
                                (history.positions, (8, 3), np.float64),
                                (history.commands, (8, 3), np.float32),
                                (original_report[32:132], (100,), np.float32)):
        array = np.asarray(value)
        if array.shape != shape or array.dtype != np.dtype(dtype) or not np.isfinite(array).all():
            raise ValueError("recurrence key requires the original finite FP64/FP32 state bits")
        parts.append(array.astype(np.dtype(dtype).newbyteorder("<"), copy=False).tobytes(order="C"))
    return struct.pack("<qq", int(t) % 40, int(old_mask)) + b"".join(parts)


def _requests(controller_counts):
    return sum(counts["requested_candidates"] for counts in controller_counts.values())


def simulate_continuation(controller, public_state, old_mask, plan=None, horizon=500):
    """Return frozen logical outputs plus independently accounted exact reuse."""
    horizon = _integer(horizon, "horizon")
    if not 41 <= horizon <= 500:
        raise ValueError("requires H500 or a shortened correctness tail of at least H41")
    history = _copy_history(controller)
    initial_report = _report(public_state)
    positions, users = decode_public_state(initial_report, 8)
    mask_bits(old_mask, 8)
    old_mask = int(old_mask)
    copied_plan = _copy_plan(plan, old_mask)
    barrier = copied_plan["arrival_t"] if copied_plan is not None and copied_plan["initiated"] else 40
    program = Program("C", horizon=horizon)
    program.controller = history
    program.plan, program.option_old_mask = copied_plan, old_mask
    count = horizon - 40
    arrays = dict(positions=np.empty((count + 1, 8, 3), dtype=np.float64),
                  actions=np.empty((count, 8, 3), dtype=np.float32),
                  masks=np.empty(count, dtype=np.int64),
                  reward_components=np.empty((count, 4), dtype=np.float64),
                  controller_estimates=np.empty((count + 1, 8, 3), dtype=np.float64))
    arrays["positions"][0] = positions
    arrays["controller_estimates"][0] = history.positions
    reports, report_times, decisions = [], [], []
    controller_counts, actual_controller_counts = empty_counts(), empty_counts()
    reward_counts = {key: 0 for key in COUNT_KEYS}
    actual_reward_counts = {key: 0 for key in COUNT_KEYS}
    total_J, total_served, total_quality, total_height, total_path = 0., 0, 0., 0., 0.
    predictions, actual_predictions, computed = 0, 0, 0
    cache, source_times, first_repeat = {}, [], None
    for index, t in enumerate(range(40, horizon)):
        state = None
        if t % 10 == 0:
            state = initial_report.copy() if t == 40 else encode_model_report(
                positions, initial_report, t, horizon)
            reports.append(state.copy())
            report_times.append(t)
        key = recurrence_key(t, positions, history, old_mask, initial_report) if t > barrier else None
        cached = cache.get(key) if key is not None else None
        if cached is None:
            command, old_mask, decision = program.select(t, state, old_mask)
            command = np.asarray(command, dtype=np.float32)
            next_positions = predict_next(positions, command)
            scorer = _Scores(users)
            score = scorer.score(next_positions, [old_mask])[0]
            tick_reward_counts = dict(scorer.counts)
            trace_counts(decision, actual_controller_counts)
            for name in COUNT_KEYS:
                actual_reward_counts[name] += int(tick_reward_counts[name])
            actual_predictions += int(decision.get("motion", {}).get("requested_candidates", 0))
            computed += 1
            source_t = t
            if key is not None:
                cache[key] = dict(source_t=t, command=command.copy(), old_mask=int(old_mask),
                                  decision=deepcopy(decision), next_positions=next_positions.copy(),
                                  next_estimate=history.positions.copy(), next_commands=history.commands.copy(),
                                  score=dict(score), reward_counts=tick_reward_counts)
        else:
            source_t = cached["source_t"]
            if first_repeat is None:
                first_repeat = dict(source_t=source_t, repeat_t=t, period=t - source_t,
                                    phase=t % 40, entering_mask=old_mask,
                                    key_sha256=hashlib.sha256(key).hexdigest())
            command, old_mask = cached["command"].copy(), cached["old_mask"]
            next_positions = cached["next_positions"].copy()
            decision = deepcopy(cached["decision"])
            decision["t"] = t
            score, tick_reward_counts = cached["score"], cached["reward_counts"]
            history.positions = cached["next_estimate"].copy()
            history.commands = cached["next_commands"].copy()
            # Absolute clocks and reports advance despite transition reuse.
            history.next_t = t + 1
            if state is not None:
                _, history.users = decode_public_state(state, 8)
        source_times.append(source_t)
        for name in COUNT_KEYS:
            reward_counts[name] += int(tick_reward_counts[name])
        trace_counts(decision, controller_counts)
        if "motion" in decision:
            predictions += int(decision["motion"]["requested_candidates"])
        # Preserve each FP addition and each path norm in original tick order.
        total_J += float(score["J"])
        total_served += int(score["served"])
        total_quality += float(score["quality"])
        total_height += float(score["energy_penalty"])
        total_path += float(np.linalg.norm(next_positions - positions, axis=1).sum())
        arrays["positions"][index + 1] = next_positions
        arrays["actions"][index] = command
        arrays["masks"][index] = old_mask
        arrays["reward_components"][index] = [score[name] for name in REWARD_COMPONENTS]
        arrays["controller_estimates"][index + 1] = history.positions
        decisions.append(deepcopy(decision))
        positions = next_positions
    arrays["report_times"] = np.asarray(report_times, dtype=np.int64)
    arrays["reports"] = np.asarray(reports, dtype=np.float32)
    summary = dict(start_t=40, horizon=horizon, model_transitions=count,
                   total_J=total_J, total_served=total_served, total_quality=total_quality,
                   total_energy_penalty=total_height, total_path=total_path,
                   controller_counts=controller_counts, reward_counts=reward_counts,
                   ordinary_candidate_position_predictions=predictions,
                   reward_component_columns=REWARD_COMPONENTS.copy(),
                   initial_old_mask=int(decisions[0]["old_mask"]),
                   plan_initiated=bool(copied_plan is not None and copied_plan["initiated"]))
    reuse = dict(schema="exact_ordinary_recurrence.v1", key_layout=KEY_LAYOUT,
                 eligibility_after_t=int(barrier), computed_ticks=computed, reused_ticks=count - computed,
                 logical_controller_calls=count, actual_controller_calls=computed,
                 logical_reward_calls=count, actual_reward_calls=computed,
                 logical_controller_counts=deepcopy(controller_counts), actual_controller_counts=actual_controller_counts,
                 logical_reward_counts=dict(reward_counts), actual_reward_counts=actual_reward_counts,
                 logical_controller_requests=_requests(controller_counts),
                 actual_controller_requests=_requests(actual_controller_counts),
                 logical_reward_requests=reward_counts["requested_candidates"],
                 actual_reward_requests=actual_reward_counts["requested_candidates"],
                 logical_requested_candidates=_requests(controller_counts) + reward_counts["requested_candidates"],
                 actual_requested_candidates=_requests(actual_controller_counts) + actual_reward_counts["requested_candidates"],
                 logical_candidate_position_predictions=predictions, actual_candidate_position_predictions=actual_predictions,
                 first_repeat=first_repeat, source_times=source_times)
    return dict(arrays=arrays, decisions=decisions, summary=summary, reuse=reuse)
