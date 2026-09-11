"""One paired seed, real recurrent learners and ordinary whole-episode service."""

from io import BytesIO
import hashlib
import math
import time

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.study import (
    HOST, ARMS, HARD_EVENTS, planned_cost, new_progress, check_time,
    TrainingMeasurements, parameter_movement, evaluate_episode, exposure,
    backend, EvaluationCoordinate, BatchedRecurrentPolicy, RecurrentRolloutState,
    NativePersistentTrainingFlow, MasterAddressedTrainResetFactory,
    build_master_addressed_initial_state, load_host, _reset_row,
)

OBJECT = "DISH-FORECAST-PACKAGE-B03"
SEED = 73


def master():
    return hashlib.sha256(f"{OBJECT}/seed/{SEED}".encode("ascii")).digest()


def configuration(arm):
    return {
        "seed": 73, "master_hex": master().hex(), "object": OBJECT,
        "underlying_arm": "STRUCTURED", "block": 0,
        "host": HOST, "forecast_package": arm == "FORECAST_PACKAGE",
        "torch_threads": torch.get_num_threads(),
        "training_dtype": "float32", "native_dtype": "float64", "lanes": 32, "ticks_per_update": 128,
        "updates": 16, "epochs": 4, "minibatches_per_epoch": 8, "optimizer": "AdamW",
        "learning_rate": 3e-4, "forecast_coefficient": 0.025,
        "pairing": "same master-addressed STRUCTURED initialization and semantic-address exogenous streams",
        "host_headroom": "no tuned same-host reference", "evaluation_selection": "update16 only",
        "renewal_boundary": "corrected: observation['renew'] = countdown == 0 (3f4d447f6); raw flag renew_completed",
    }


def run_arm(arm, output, deadline, progress):
    package = arm == "FORECAST_PACKAGE"
    master_digest = master()
    torch.set_num_threads(1)
    library = load_host(HOST)
    check_time(deadline)
    initial = build_master_addressed_initial_state(master=master_digest, block=0, arm="STRUCTURED")
    initial_parameters = torch.load(BytesIO(initial), map_location="cpu", weights_only=False)["model"]
    progress["initial_model_norm"] = math.sqrt(sum(float(value.double().square().sum()) for value in initial_parameters.values()))
    progress["configuration"] = configuration(arm)
    reset = MasterAddressedTrainResetFactory(master=master_digest, block=0, arm="STRUCTURED")
    native = backend.native_batch_from_rows(reset.rows(np.zeros(32, dtype=np.int64)), library=library)
    measured = TrainingMeasurements(native, progress, deadline)
    flow = NativePersistentTrainingFlow(native=measured, arm="STRUCTURED", master=master_digest, block=0,
                                        checkpoint_bytes=initial, forecast_package=package,
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
        progress["curves"].append({"update": update, "service_ticks": progress["training_service"] - previous_service,
                                   "next_mask_count": progress["next_mask_count"] - previous_next,
                                   "service_label_eligible": progress["service_label_eligible"] - previous_q,
                                   "optimizer_steps": receipt["optimizer_steps"],
                                   "mean_loss": receipt["mean_loss"], "mean_gradient_norm": receipt["mean_gradient_norm"],
                                   "losses_finite": receipt["losses_finite"], "gradient_norms_finite": receipt["gradient_norms_finite"],
                                   "wall_seconds": time.perf_counter() - started})
        if not receipt["losses_finite"] or not receipt["gradient_norms_finite"]:
            raise FloatingPointError("B02 nonfinite learner update")
    final = flow.trainer.checkpoint_bytes
    progress["parameter_movement"] = parameter_movement(initial, final)
    check_time(deadline)
    (output / "checkpoint_update16.pt").write_bytes(final)
    for regime in ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK"):
        for schedule in ("K8", "K4_TO_K12"):
            check_time(deadline)
            coordinate = EvaluationCoordinate(0, regime, schedule, "SPEED_4", 0)
            row = _reset_row(master_digest, coordinate)
            evaluation = backend.native_batch_from_rows((row,), library=library)
            state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
            policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=final, state=state,
                                            forecast_package=package)
            record = {"regime": regime, "schedule": schedule, "speed": 4, "slot": 0, "block": 0,
                      "coordinate": coordinate.canonical_key(), "reset": row}
            progress["evaluation_rows"].append(record)
            evaluate_episode(evaluation, policy, deadline, progress, record)
    progress["mean_service_ticks"] = sum(row["service_ticks"] for row in progress["evaluation_rows"]) / 4
    progress["status"] = "COMPLETE"


def paired_result(control, package):
    result = {"object": OBJECT, "status": "INCOMPLETE_PAIR", "training_seeds": 1,
              "MEI_service_ticks": 24, "uncertainty": "one training replicate; no population interval",
              "control_status": control["status"], "package_status": package["status"]}
    if control["status"] != "COMPLETE" or package["status"] != "COMPLETE":
        return result
    control_rows = {row["coordinate"]: row for row in control["evaluation_rows"]}
    package_rows = {row["coordinate"]: row for row in package["evaluation_rows"]}
    if len(control_rows) != 4 or control_rows.keys() != package_rows.keys():
        return result
    rows = []
    for key, left in control_rows.items():
        right = package_rows[key]
        rows.append({"coordinate": key, "control_service": left["service_ticks"],
                     "package_service": right["service_ticks"],
                     "difference": right["service_ticks"] - left["service_ticks"],
                     "control_energy": left["energy"], "package_energy": right["energy"],
                     "control_hard_events": left["hard_events"], "package_hard_events": right["hard_events"],
                     "control_terminal": left["terminal"], "package_terminal": right["terminal"],
                     "control_legal_transfers": left["legal_transfers"], "package_legal_transfers": right["legal_transfers"]})
    result.update(status="COMPLETE", paired_rows=rows,
                  control_mean=sum(row["control_service"] for row in rows) / 4,
                  package_mean=sum(row["package_service"] for row in rows) / 4,
                  delta_package=sum(row["difference"] for row in rows) / 4,
                  temporal_source_contrast="unestimated", component_attribution="unestimated")
    return result
