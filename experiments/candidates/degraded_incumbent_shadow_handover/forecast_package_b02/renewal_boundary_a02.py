"""DISH-RENEWAL-BOUNDARY-A02-CORRECTION: ordinary renew overlay measurement."""

from __future__ import annotations

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02 import (
    renewal_boundary_a01 as a01,
)
from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.study import (
    HOST, backend, load_host, native_state, terminal_facts,
)
from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01.study import (
    _reset_row,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_population import (
    EvaluationCoordinate,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, RecurrentRolloutState,
)


OBJECT = "DISH-RENEWAL-BOUNDARY-A02-CORRECTION"
EXPECTED_CHECKPOINT_SHA256 = a01.EXPECTED_CHECKPOINT_SHA256
FORMAL_HORIZON = a01.FORMAL_HORIZON
CHECK_HORIZON = a01.CHECK_HORIZON
CAP_SECONDS = a01.CAP_SECONDS
WINDOWS = a01.WINDOWS
INCORPORATION_TOLERANCE = 1e-9
ROW_KEYS = (
    "window", "t", "policy_renew", "renew_completed", "pre_countdown",
    "held_before", "emitted", "projected_expected", "held_after",
    "incorporated_as_projected", "value_equal_to_held", "prepare", "commit",
    "cas_applied", "owner", "service", "energy_increment", "hard_events",
    "hard_event_increments", "terminal", "native_admission",
    "observation_tick", "pre_tick", "held_changed",
)

project_command = a01.project_command
native_admission = a01.native_admission
b02_master = a01.b02_master
verify_checkpoint = a01.verify_checkpoint
window_plan = a01.window_plan
json_ready = a01.json_ready
parameter_norm = a01.parameter_norm


def planned_cost(profile):
    ticks = CHECK_HORIZON if profile == "check" else FORMAL_HORIZON * len(WINDOWS)
    return {
        "law": (
            "build/import/load + one focused regression + checkpoint + "
            "2 x (policy + reset) + <= 64 x (forward + native step) + publication"
        ),
        "profile": profile, "W": ticks, "C": 1 if profile == "check" else 2,
        "cap_seconds": CAP_SECONDS,
        "projection_status": (
            "composed from A01 measured terms in the CM record; "
            "runner does not invent a unit time"
        ),
    }


def _vec_close(left, right, tolerance=INCORPORATION_TOLERANCE):
    left = [float(v) for v in left]
    right = [float(v) for v in right]
    if len(left) != len(right):
        return False
    return all(abs(a - b) <= tolerance for a, b in zip(left, right))


def make_row(*, window, t, observation, pre, step_rows, post, observation_after):
    pre0, post0 = pre[0], post[0]
    held_before = a01._vec(pre0["a"])
    held_after = a01._vec(post0["a"])
    emitted = a01._vec(step_rows["raw_action"][0])
    projected = project_command(held_before, emitted)
    admitted = native_admission(pre0["countdown"])
    hard = {name: int(a01._scalar(observation_after[name])) for name in a01.HARD_EVENTS}
    hard_inc = {name: int(post0[name]) - int(pre0[name]) for name in a01.HARD_EVENTS}
    return {
        "window": int(window), "t": int(t),
        "policy_renew": a01._flag(observation["renew"]),
        "renew_completed": a01._flag(observation_after["renew_completed"]),
        "pre_countdown": int(pre0["countdown"]),
        "held_before": held_before, "emitted": emitted,
        "projected_expected": projected, "held_after": held_after,
        "incorporated_as_projected": bool(
            admitted and _vec_close(held_after, projected)
        ),
        "value_equal_to_held": _vec_close(emitted, held_before),
        "prepare": [int(v) for v in np.asarray(step_rows["prepare"][0]).reshape(-1)],
        "commit": [int(v) for v in np.asarray(step_rows["commit"][0]).reshape(-1)],
        "cas_applied": int(a01._scalar(observation_after["cas_applied"])),
        "owner": int(pre0["owner"]),
        "service": int(a01._scalar(observation_after["service"])),
        "energy_increment": float(post0["total_energy"]) - float(pre0["total_energy"]),
        "hard_events": hard, "hard_event_increments": hard_inc,
        "terminal": a01._flag(observation_after["terminal"]),
        "native_admission": admitted,
        "observation_tick": int(a01._scalar(observation["tick"])),
        "pre_tick": int(pre0["tick"]),
        "held_changed": any(a != b for a, b in zip(held_before, held_after)),
    }


def reduce_rows(rows):
    def counts(subset):
        matched_renewals = matched_non_renewals = 0
        native_true_policy_false = policy_true_native_false = 0
        native_out_renew_equals_policy_renew = 0
        native_out_true_policy_false = policy_true_native_out_false = 0
        held_changed_ticks = 0
        admissions = 0
        admissions_held_equals_projected = 0
        admissions_emitted_equals_held = 0
        for row in subset:
            native, policy = bool(row["native_admission"]), bool(row["policy_renew"])
            if native and policy:
                matched_renewals += 1
            elif (not native) and (not policy):
                matched_non_renewals += 1
            elif native and not policy:
                native_true_policy_false += 1
            else:
                policy_true_native_false += 1
            # Primary agreement: native out.renew (renew_completed) vs policy_renew.
            # native_admission vs policy_renew is a countdown-consistency check.
            native_out = bool(row["renew_completed"])
            if native_out == policy:
                native_out_renew_equals_policy_renew += 1
            elif native_out and not policy:
                native_out_true_policy_false += 1
            else:
                policy_true_native_out_false += 1
            if row["held_changed"]:
                held_changed_ticks += 1
            if native:
                admissions += 1
                if row["incorporated_as_projected"]:
                    admissions_held_equals_projected += 1
                if row["value_equal_to_held"]:
                    admissions_emitted_equals_held += 1
        return {
            "matched_renewals": matched_renewals,
            "matched_non_renewals": matched_non_renewals,
            "native_true_policy_false": native_true_policy_false,
            "policy_true_native_false": policy_true_native_false,
            "native_out_renew_equals_policy_renew": native_out_renew_equals_policy_renew,
            "native_out_true_policy_false": native_out_true_policy_false,
            "policy_true_native_out_false": policy_true_native_out_false,
            "admissions": admissions,
            "admissions_held_equals_projected": admissions_held_equals_projected,
            "admissions_emitted_equals_held": admissions_emitted_equals_held,
            "held_changed_ticks": held_changed_ticks,
            "live_ticks": len(subset),
        }

    windows = sorted({row["window"] for row in rows})
    return {
        "per_window": {str(window): counts([row for row in rows if row["window"] == window])
                       for window in windows},
        "overall": counts(rows),
    }


def run_window(native, policy, *, window, horizon):
    observation = native.observe()
    recorded = []
    for tick in range(horizon):
        if a01._flag(observation["terminal"]):
            break
        owner_before = np.asarray(observation["owner"], dtype=np.int64)
        consumed = observation
        step = policy.step_rows(consumed, sampler=None, global_tick=tick, deterministic=True)
        pre = native_state(native).copy()
        observation = native.step(step)
        policy.apply_native_promotion(
            owner_before=owner_before, step_rows=step, observation_after=observation,
        )
        post = native_state(native).copy()
        recorded.append(make_row(
            window=window, t=tick, observation=consumed, pre=pre,
            step_rows=step, post=post, observation_after=observation,
        ))
    early = None
    if len(recorded) < horizon:
        early = terminal_facts(native, len(recorded))
    return {"rows": recorded, "live_ticks": len(recorded), "horizon": horizon,
            "early_terminal": early}


def run_measurement(*, checkpoint_bytes, profile):
    torch.set_num_threads(1)
    specs, horizon = window_plan(profile)
    master = b02_master()
    library = load_host(HOST)
    rows = []
    meta = []
    for spec in specs:
        coordinate = EvaluationCoordinate(
            spec["block"], spec["regime"], spec["schedule"], spec["speed"], spec["slot"],
        )
        reset = _reset_row(master, coordinate)
        phase = int(reset["phase"])
        native = backend.native_batch_from_rows((reset,), library=library)
        state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
        policy = BatchedRecurrentPolicy(
            arm="STRUCTURED", checkpoint_bytes=checkpoint_bytes, state=state,
            forecast_package=True,
        )
        before = parameter_norm(policy)
        result = run_window(native, policy, window=spec["window"], horizon=horizon)
        after = parameter_norm(policy)
        meta.append({
            "window": spec["window"], "coordinate": coordinate.canonical_key(),
            "reset": json_ready(reset), "phase": phase,
            "expected_reset_phase": spec["expected_reset_phase"],
            "phase_matches_expected": phase == spec["expected_reset_phase"],
            "live_ticks": result["live_ticks"], "horizon": horizon,
            "early_terminal": result["early_terminal"],
            "parameter_norm_before": before, "parameter_norm_after": after,
        })
        rows.extend(result["rows"])
    return rows, meta
