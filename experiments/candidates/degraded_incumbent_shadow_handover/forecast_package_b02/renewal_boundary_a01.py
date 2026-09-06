"""DISH-RENEWAL-BOUNDARY-A01: ordinary policy-to-native renewal measurement."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.study import (
    HARD_EVENTS, HOST, OBJECT as B02_OBJECT, backend, load_host, native_state, terminal_facts,
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


OBJECT = "DISH-RENEWAL-BOUNDARY-A01"
EXPECTED_CHECKPOINT_SHA256 = "504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66"
FORMAL_HORIZON = 32
CHECK_HORIZON = 4
CAP_SECONDS = 120
WINDOWS = (
    {"window": 1, "regime": "TARGET_VISUAL_MASK", "schedule": "K8",
     "speed": "SPEED_4", "slot": 0, "block": 0, "expected_reset_phase": 4},
    {"window": 2, "regime": "TARGET_VISUAL_MASK", "schedule": "K4_TO_K12",
     "speed": "SPEED_4", "slot": 0, "block": 0, "expected_reset_phase": 2},
)
ROW_KEYS = (
    "window", "t", "policy_renew", "observation_tick",
    "pre_tick", "pre_countdown", "pre_k_active", "pre_k_epoch",
    "pre_owner", "pre_actuator_owner", "pre_cas_applied", "pre_a",
    "native_admission", "raw_action", "prepare", "commit",
    "post_countdown", "post_a", "returned_renew", "service", "energy_increment",
    "cas_applied", "hard_events", "hard_event_increments", "terminal",
    "held_changed", "held_minus_raw", "projected_raw", "held_minus_projected",
)


def planned_cost(profile):
    ticks = CHECK_HORIZON if profile == "check" else FORMAL_HORIZON * len(WINDOWS)
    return {
        "law": "1 A03 native build + C checkpoint loads + C resets + W native steps + W recurrent forwards + reduction/publication",
        "profile": profile, "W": ticks, "C": 1 if profile == "check" else 2,
        "cap_seconds": CAP_SECONDS,
        "projection_status": "composed from B02 measured terms in the CM record; runner does not invent a unit time",
    }


def native_admission(countdown):
    return int(countdown) == 0


def _clip_vec(x, y, cap):
    n = math.hypot(x, y)
    if n <= cap or n <= 1e-12:
        return x, y
    q = cap / n
    return x * q, y * q


def project_command(previous, raw):
    """Python copy of native project at cpp:261-263, for reporting only."""
    previous = [float(v) for v in previous]
    raw = [float(v) for v in raw]
    out = []
    for i in range(2):
        px, py = previous[2 * i], previous[2 * i + 1]
        rx, ry = _clip_vec(raw[2 * i], raw[2 * i + 1], 3.0)
        dx, dy = _clip_vec(rx - px, ry - py, 1.5)
        ax, ay = _clip_vec(px + dx, py + dy, 3.0)
        out.extend((ax, ay))
    return out


def _vec(value):
    return [float(v) for v in np.asarray(value).reshape(-1)]


def _flag(value):
    return bool(np.asarray(value).reshape(-1)[0])


def _scalar(value):
    return np.asarray(value).reshape(-1)[0]


def json_ready(value):
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


def make_row(*, window, t, observation, pre, step_rows, post, observation_after):
    pre0, post0 = pre[0], post[0]
    pre_a, post_a = _vec(pre0["a"]), _vec(post0["a"])
    raw = _vec(step_rows["raw_action"][0])
    projected = project_command(pre_a, raw)
    held_changed = any(a != b for a, b in zip(pre_a, post_a))
    hard = {name: int(_scalar(observation_after[name])) for name in HARD_EVENTS}
    hard_inc = {name: int(post0[name]) - int(pre0[name]) for name in HARD_EVENTS}
    return {
        "window": int(window), "t": int(t),
        "policy_renew": _flag(observation["renew"]),
        "observation_tick": int(_scalar(observation["tick"])),
        "pre_tick": int(pre0["tick"]), "pre_countdown": int(pre0["countdown"]),
        "pre_k_active": int(pre0["k_active"]), "pre_k_epoch": int(pre0["k_epoch"]),
        "pre_owner": int(pre0["owner"]), "pre_actuator_owner": int(pre0["actuator_owner"]),
        "pre_cas_applied": int(pre0["cas_applied"]), "pre_a": pre_a,
        "native_admission": native_admission(pre0["countdown"]),
        "raw_action": raw,
        "prepare": [int(v) for v in np.asarray(step_rows["prepare"][0]).reshape(-1)],
        "commit": [int(v) for v in np.asarray(step_rows["commit"][0]).reshape(-1)],
        "post_countdown": int(post0["countdown"]), "post_a": post_a,
        "returned_renew": _flag(observation_after["renew"]),
        "service": int(_scalar(observation_after["service"])),
        "energy_increment": float(post0["total_energy"]) - float(pre0["total_energy"]),
        "cas_applied": int(_scalar(observation_after["cas_applied"])),
        "hard_events": hard, "hard_event_increments": hard_inc,
        "terminal": _flag(observation_after["terminal"]),
        "held_changed": held_changed,
        "held_minus_raw": [a - b for a, b in zip(post_a, raw)] if held_changed else None,
        "projected_raw": projected,
        "held_minus_projected": [a - b for a, b in zip(post_a, projected)] if held_changed else None,
    }


def reduce_rows(rows):
    def counts(subset):
        native_true_policy_false = policy_true_native_false = both_true = both_false = 0
        held = 0
        admissions = []
        for index, row in enumerate(subset):
            native, policy = bool(row["native_admission"]), bool(row["policy_renew"])
            if native and not policy:
                native_true_policy_false += 1
            elif policy and not native:
                policy_true_native_false += 1
            elif native and policy:
                both_true += 1
            else:
                both_false += 1
            if row["held_changed"]:
                held += 1
            if native:
                previous = subset[index - 1]["raw_action"] if index else None
                admissions.append({
                    "window": row["window"], "t": row["t"],
                    "emitted_this": row["raw_action"],
                    "emitted_previous": previous,
                    "new_held": row["post_a"],
                })
        return {
            "native_true_policy_false": native_true_policy_false,
            "policy_true_native_false": policy_true_native_false,
            "both_true": both_true, "both_false": both_false,
            "held_changed_ticks": held,
            "admission_command_pairs": admissions,
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
        if _flag(observation["terminal"]):
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


def parameter_norm(policy):
    total = 0.0
    with torch.no_grad():
        for value in policy.model.state_dict().values():
            total += float(value.detach().double().square().sum())
    return math.sqrt(total)


def b02_master():
    return hashlib.sha256(f"{B02_OBJECT}/seed/61".encode("ascii")).digest()


def verify_checkpoint(path, expected_sha256=EXPECTED_CHECKPOINT_SHA256):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"checkpoint not found: {path}")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"checkpoint sha256 {digest} differs from {expected_sha256}")
    return digest, payload


def window_plan(profile):
    if profile == "check":
        return (WINDOWS[0],), CHECK_HORIZON
    if profile == "formal":
        return WINDOWS, FORMAL_HORIZON
    raise ValueError(f"profile differs: {profile}")


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


