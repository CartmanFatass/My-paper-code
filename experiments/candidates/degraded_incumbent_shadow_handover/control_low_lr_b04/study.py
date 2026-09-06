"""CONTROL vs LOW_LR on one paired seed; initializer payload carries the AdamW rate."""

from io import BytesIO
import hashlib
import json
import math
import time

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.study import (
    HOST, HARD_EVENTS, planned_cost, new_progress, check_time,
    TrainingMeasurements, parameter_movement, evaluate_episode, exposure,
    backend, EvaluationCoordinate, load_host, _reset_row,
)
from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b03.study import (
    BatchedRecurrentPolicy, RecurrentRolloutState, NativePersistentTrainingFlow,
    MasterAddressedTrainResetFactory, build_master_addressed_initial_state,
)

OBJECT = "DISH-CONTROL-LOW-LR-B04"
SEED = 89
ARMS = ("CONTROL", "LOW_LR")
LEARNING_RATES = {"CONTROL": 3e-4, "LOW_LR": 3e-5}
SCALE_TICKS = 24
RENEWAL_BOUNDARY = (
    "corrected: observation['renew'] = countdown == 0 (3f4d447f6); raw flag renew_completed"
)
LEARNING_RATE_MECHANISM = (
    "initializer payload optimizer param_groups[*].lr rewritten before training; "
    "engine restores optimizer state at every update"
)


def master():
    return hashlib.sha256(f"{OBJECT}/seed/{SEED}".encode("ascii")).digest()


def model_norm(state_dict):
    return math.sqrt(sum(float(value.double().square().sum()) for value in state_dict.values()))


def set_learning_rate(payload, lr):
    loaded = torch.load(BytesIO(payload), map_location="cpu", weights_only=False)
    groups = loaded["optimizer"]["param_groups"]
    if len(groups) != 2:
        raise RuntimeError("B04 optimizer parameter group count differs")
    for group in groups:
        group["lr"] = lr
    stream = BytesIO()
    torch.save(loaded, stream)
    return stream.getvalue()


def learning_rates(checkpoint):
    loaded = torch.load(BytesIO(checkpoint), map_location="cpu", weights_only=False)
    return [float(group["lr"]) for group in loaded["optimizer"]["param_groups"]]


def coordinates():
    return tuple(
        EvaluationCoordinate(0, regime, schedule, "SPEED_4", 0)
        for regime in ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
        for schedule in ("K8", "K4_TO_K12")
    )


def recorded_resets(master_digest):
    return {coordinate.canonical_key(): dict(_reset_row(master_digest, coordinate))
            for coordinate in coordinates()}


def configuration(arm):
    return {
        "seed": SEED, "master_hex": master().hex(), "object": OBJECT, "arm": arm,
        "underlying_arm": "STRUCTURED", "block": 0, "host": HOST, "forecast_package": False,
        "torch_threads": torch.get_num_threads(), "training_dtype": "float32",
        "native_dtype": "float64", "lanes": 32, "ticks_per_update": 128, "updates": 16,
        "epochs": 4, "minibatches_per_epoch": 8, "optimizer": "AdamW",
        "learning_rate": LEARNING_RATES[arm], "learning_rate_mechanism": LEARNING_RATE_MECHANISM,
        "forecast_coefficient": 0.025,
        "pairing": "same master-addressed STRUCTURED initialization and semantic-address exogenous streams",
        "host_headroom": "no tuned same-host reference", "evaluation_selection": "update16 only",
        "renewal_boundary": RENEWAL_BOUNDARY, "scale_ticks": SCALE_TICKS,
    }


def prepare_shared(output, deadline, progress):
    torch.set_num_threads(1)
    library = load_host(HOST)
    check_time(deadline)
    initial = build_master_addressed_initial_state(master=master(), block=0, arm="STRUCTURED")
    (output / "initial_state.pt").write_bytes(initial)
    loaded = torch.load(BytesIO(initial), map_location="cpu", weights_only=False)
    progress["initializer_calls"] = 1
    progress["initial_model_norm"] = model_norm(loaded["model"])
    progress["welford_counts"] = {name: int(loaded["welford"][name].count)
                                  for name in ("actor", "snapshot", "critic")}
    if any(progress["welford_counts"][name] != 0 for name in progress["welford_counts"]):
        raise RuntimeError("B04 initializer Welford counts are not zero")
    rates = learning_rates(initial)
    if rates != [LEARNING_RATES["CONTROL"], LEARNING_RATES["CONTROL"]]:
        raise RuntimeError("B04 initializer learning rates differ")
    progress["initial_learning_rates"] = rates
    resets = recorded_resets(master())
    (output / "resets.json").write_text(json.dumps(resets, indent=2) + "\n", encoding="utf8")
    progress["reference_rows"] = []
    for coordinate in coordinates():
        check_time(deadline)
        row = resets[coordinate.canonical_key()]
        evaluation = backend.native_batch_from_rows((row,), library=library)
        state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
        policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=initial, state=state,
                                        forecast_package=False)
        record = {"regime": coordinate.regime, "schedule": coordinate.schedule, "speed": 4,
                  "slot": 0, "block": 0, "coordinate": coordinate.canonical_key(), "reset": row,
                  "source": "new:zero_update:raw",
                  "parameter_norm_before": progress["initial_model_norm"]}
        progress["reference_rows"].append(record)
        evaluate_episode(evaluation, policy, deadline, progress, record)
        after = model_norm(policy.model.state_dict())
        record["parameter_norm_after"] = after
        if abs(after - progress["initial_model_norm"]) > 1e-9:
            raise RuntimeError("B04 zero-update parameter norm moved")
    for name in ("ordinary_training_transitions", "optimizer_steps", "completed_updates",
                 "next_label_steps"):
        if progress.get(name, 0) != 0:
            raise RuntimeError("B04 zero-update training counter moved")
    progress["reference_mean_service_ticks"] = (
        sum(row["service_ticks"] for row in progress["reference_rows"]) / 4
    )
    progress["status"] = "COMPLETE"


def run_arm(arm, output, deadline, progress, shared):
    master_digest = master()
    torch.set_num_threads(1)
    library = load_host(HOST)
    check_time(deadline)
    shared_bytes = (shared / "initial_state.pt").read_bytes()
    shared_norm = model_norm(torch.load(BytesIO(shared_bytes), map_location="cpu",
                                        weights_only=False)["model"])
    initial = set_learning_rate(shared_bytes, LEARNING_RATES[arm])
    arm_norm = model_norm(torch.load(BytesIO(initial), map_location="cpu",
                                     weights_only=False)["model"])
    if arm_norm != shared_norm:
        raise RuntimeError("B04 initial model norm differs from shared initialization")
    progress["initial_model_norm"] = arm_norm
    progress["configuration"] = configuration(arm)
    reset = MasterAddressedTrainResetFactory(master=master_digest, block=0, arm="STRUCTURED")
    native = backend.native_batch_from_rows(reset.rows(np.zeros(32, dtype=np.int64)), library=library)
    measured = TrainingMeasurements(native, progress, deadline)
    flow = NativePersistentTrainingFlow(native=measured, arm="STRUCTURED", master=master_digest,
                                        block=0, checkpoint_bytes=initial, forecast_package=False,
                                        progress=progress, deadline=deadline)
    for update in range(1, 17):
        check_time(deadline)
        started = time.perf_counter()
        previous_service = progress["training_service"]
        previous_next = progress["next_mask_count"]
        previous_q = progress["service_label_eligible"]
        fragments = flow.collect_update(native.observe())
        receipt = flow.apply_update(fragments)
        progress["completed_updates"] = update
        rates = learning_rates(flow.trainer.checkpoint_bytes)
        if any(rate != LEARNING_RATES[arm] for rate in rates):
            raise RuntimeError("B04 learning rate drift")
        progress["curves"].append({
            "update": update, "service_ticks": progress["training_service"] - previous_service,
            "next_mask_count": progress["next_mask_count"] - previous_next,
            "service_label_eligible": progress["service_label_eligible"] - previous_q,
            "optimizer_steps": receipt["optimizer_steps"], "mean_loss": receipt["mean_loss"],
            "mean_gradient_norm": receipt["mean_gradient_norm"],
            "losses_finite": receipt["losses_finite"],
            "gradient_norms_finite": receipt["gradient_norms_finite"],
            "wall_seconds": time.perf_counter() - started, "learning_rates": rates,
        })
        if not receipt["losses_finite"] or not receipt["gradient_norms_finite"]:
            raise FloatingPointError("B02 nonfinite learner update")
    final = flow.trainer.checkpoint_bytes
    progress["parameter_movement"] = parameter_movement(initial, final)
    check_time(deadline)
    (output / "checkpoint_update16.pt").write_bytes(final)
    recorded = json.loads((shared / "resets.json").read_text(encoding="utf8"))
    for coordinate in coordinates():
        check_time(deadline)
        expected = dict(_reset_row(master_digest, coordinate))
        row = recorded[coordinate.canonical_key()]
        if row != expected:
            raise RuntimeError("B04 recorded reset differs from _reset_row")
        evaluation = backend.native_batch_from_rows((row,), library=library)
        state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
        policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=final, state=state,
                                        forecast_package=False)
        record = {"regime": coordinate.regime, "schedule": coordinate.schedule, "speed": 4,
                  "slot": 0, "block": 0, "coordinate": coordinate.canonical_key(), "reset": row,
                  "source": f"new:{arm}:update16"}
        progress["evaluation_rows"].append(record)
        evaluate_episode(evaluation, policy, deadline, progress, record)
    progress["mean_service_ticks"] = sum(row["service_ticks"] for row in progress["evaluation_rows"]) / 4
    progress["status"] = "COMPLETE"


def paired_result(control, low_lr, reference):
    if (control.get("status") != "COMPLETE" or low_lr.get("status") != "COMPLETE"
            or reference.get("status") != "COMPLETE"):
        raise ValueError("B04 paired input is not COMPLETE")
    control_rows = {row["coordinate"]: row for row in control["evaluation_rows"]}
    low_rows = {row["coordinate"]: row for row in low_lr["evaluation_rows"]}
    ref_rows = {row["coordinate"]: row for row in reference["reference_rows"]}
    rows = []
    for coordinate in coordinates():
        key = coordinate.canonical_key()
        if key not in control_rows or key not in low_rows or key not in ref_rows:
            raise ValueError("B04 paired coordinate missing")
        left, right, zero = control_rows[key], low_rows[key], ref_rows[key]
        rows.append({
            "coordinate": key,
            "reference_service": zero["service_ticks"],
            "control_service": left["service_ticks"],
            "low_lr_service": right["service_ticks"],
            "reference_source": zero.get("source", "new:zero_update:raw"),
            "control_source": left.get("source", "new:CONTROL:update16"),
            "low_lr_source": right.get("source", "new:LOW_LR:update16"),
            "low_lr_minus_control": right["service_ticks"] - left["service_ticks"],
            "control_minus_reference": left["service_ticks"] - zero["service_ticks"],
            "low_lr_minus_reference": right["service_ticks"] - zero["service_ticks"],
        })
    return {
        "object": OBJECT, "seed": SEED, "scale_ticks": SCALE_TICKS, "status": "COMPLETE",
        "reference_mean": sum(row["reference_service"] for row in rows) / 4,
        "control_mean": sum(row["control_service"] for row in rows) / 4,
        "low_lr_mean": sum(row["low_lr_service"] for row in rows) / 4,
        "delta_lr": sum(row["low_lr_minus_control"] for row in rows) / 4,
        "d_control_new": sum(row["control_minus_reference"] for row in rows) / 4,
        "d_low_lr_new": sum(row["low_lr_minus_reference"] for row in rows) / 4,
        "rows": rows,
    }
