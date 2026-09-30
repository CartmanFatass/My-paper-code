"""Pure complete C continuation from a copied lawful t40 history."""

from copy import deepcopy
from numbers import Integral

import numpy as np

from ..b02.controller import Program, COUNT_KEYS, empty_counts, trace_counts
from ..control import OrdinaryController, _Scores, decode_public_state, predict_next
from ..host import mask_bits

REWARD_COMPONENTS = ["J", "served", "quality", "energy_penalty"]


def _integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    return int(value)


def _report(public_state):
    state = np.asarray(public_state)
    if state.dtype != np.dtype(np.float32):
        raise ValueError("the original public report must retain its float32 bits")
    decode_public_state(state, 8)  # Includes shape, validity and finiteness.
    return state.copy()


def encode_model_report(positions, original_public_state, t, horizon=500):
    """CountAdapter's first-cast-FP32 codec with static user bits preserved."""
    t, horizon = _integer(t, "t"), _integer(horizon, "horizon")
    if horizon <= 0 or not 0 <= t <= horizon:
        raise ValueError("report time must be within its positive horizon")
    positions = np.asarray(positions)
    if positions.shape != (8, 3) or not np.isfinite(positions).all():
        raise ValueError("requires finite model-physical N8 positions")
    state = _report(original_public_state)
    # These operations deliberately retain CountAdapter's float32 rounding
    # before division/subtraction, rather than normalizing double coordinates.
    uavs = np.asarray(positions, dtype=np.float32)
    encoded = np.zeros((8, 3), dtype=np.float32)
    encoded[:, :2] = uavs[:, :2] / 1000.0
    encoded[:, 2] = (uavs[:, 2] - 50.0) / 100.0
    state[:24] = encoded.reshape(-1)
    state[-1] = np.float32(float(t) / float(horizon))
    return state


def _copy_history(controller):
    if not isinstance(controller, OrdinaryController) or controller.n_uavs != 8 or controller.next_t != 40:
        raise ValueError("requires the actual N8 ordinary controller at next_t40")
    commands = np.asarray(controller.commands)
    if (commands.dtype != np.dtype(np.float32) or commands.shape != (8, 3)
            or not np.isin(commands, [-1., 0., 1.]).all()):
        raise ValueError("issued history requires float32 ternary N8 commands")
    for value, shape in ((controller.positions, (8, 3)), (controller.users, (50, 2))):
        if value is None or np.asarray(value).shape != shape or not np.isfinite(value).all():
            raise ValueError("controller history must contain finite positions and users")
    return deepcopy(controller)


def _copy_plan(plan, old_mask):
    if plan is None:
        return None
    plan = deepcopy(plan)
    if not isinstance(plan, dict) or not isinstance(plan.get("initiated"), bool):
        raise ValueError("plan must record its initiation decision")
    if not plan["initiated"]:
        return plan
    duration = _integer(plan["duration"], "duration")
    arrival = _integer(plan["arrival_t"], "arrival_t")
    member = _integer(plan["member"], "member")
    if duration not in (10, 20, 30, 40) or arrival != 40 + duration or not 0 <= member < 8:
        raise ValueError("plan must retain the original aligned t40 commitment")
    if mask_bits(old_mask, 8)[member]:
        raise ValueError("the planned member must be silent under the entering mask")
    commands = np.asarray(plan["commands"], dtype=np.float32)
    destination = np.asarray(plan["predicted_destination"], dtype=np.float64)
    if (commands.shape != (duration, 8, 3) or not np.isin(commands, [-1., 0., 1.]).all()
            or np.any(np.delete(commands, member, axis=1))
            or destination.shape != (8, 3) or not np.isfinite(destination).all()):
        raise ValueError("plan must contain its fixed silent-member commands and destination")
    return plan


def simulate_continuation(controller, public_state, old_mask, plan=None, horizon=500):
    """Advance each model tick explicitly; never access a native environment.

    Physical positions start from decoded t40 coordinates. The copied C state
    keeps its entering estimate/issued history, then consumes the untouched
    original t40 report. Later reports encode physical positions only on legal
    boundaries. Every post-action reward uses a fresh, single-request scorer.
    """
    horizon = _integer(horizon, "horizon")
    if not 41 <= horizon <= 500:
        raise ValueError("requires H500 or a shortened correctness tail of at least H41")
    history = _copy_history(controller)
    initial_report = _report(public_state)
    positions, users = decode_public_state(initial_report, 8)
    mask_bits(old_mask, 8)
    old_mask = int(old_mask)
    copied_plan = _copy_plan(plan, old_mask)
    program = Program("C", horizon=horizon)
    program.controller = history
    program.plan, program.option_old_mask = copied_plan, old_mask
    count = horizon - 40
    arrays = dict(positions=np.empty((count+1, 8, 3), dtype=np.float64),
                  actions=np.empty((count, 8, 3), dtype=np.float32),
                  masks=np.empty(count, dtype=np.int64),
                  reward_components=np.empty((count, 4), dtype=np.float64),
                  controller_estimates=np.empty((count+1, 8, 3), dtype=np.float64))
    arrays["positions"][0] = positions
    arrays["controller_estimates"][0] = history.positions
    reports, report_times, decisions = [], [], []
    controller_counts = empty_counts()
    reward_counts = {key: 0 for key in COUNT_KEYS}
    total_J, total_served, total_quality, total_height, total_path = 0., 0, 0., 0., 0.
    predictions = 0
    for index, t in enumerate(range(40, horizon)):
        state = None
        if t % 10 == 0:
            state = initial_report.copy() if t == 40 else encode_model_report(
                positions, initial_report, t, horizon)
            reports.append(state.copy())
            report_times.append(t)
        command, old_mask, decision = program.select(t, state, old_mask)
        command = np.asarray(command, dtype=np.float32)
        next_positions = predict_next(positions, command)
        # Deliberately do not persist reward geometry or state/mask cache across
        # ticks or share it with the controller's within-decision searches.
        scorer = _Scores(users)
        score = scorer.score(next_positions, [old_mask])[0]
        for key in COUNT_KEYS:
            reward_counts[key] += int(scorer.counts[key])
        trace_counts(decision, controller_counts)
        if "motion" in decision:
            predictions += int(decision["motion"]["requested_candidates"])
        total_J += float(score["J"])
        total_served += int(score["served"])
        total_quality += float(score["quality"])
        total_height += float(score["energy_penalty"])
        total_path += float(np.linalg.norm(next_positions - positions, axis=1).sum())
        arrays["positions"][index+1] = next_positions
        arrays["actions"][index] = command
        arrays["masks"][index] = old_mask
        arrays["reward_components"][index] = [score[key] for key in REWARD_COMPONENTS]
        arrays["controller_estimates"][index+1] = history.positions
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
    return dict(arrays=arrays, decisions=decisions, summary=summary)
