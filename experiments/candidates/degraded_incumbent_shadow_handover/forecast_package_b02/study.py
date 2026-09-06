"""One paired seed, real recurrent learners and ordinary whole-episode service."""

from io import BytesIO
import hashlib
import math
import time

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_backend as backend
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_population import EvaluationCoordinate
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, RecurrentRolloutState, NativePersistentTrainingFlow,
    MasterAddressedTrainResetFactory, build_master_addressed_initial_state,
)
from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01.native_a03 import load_host
from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01.study import _reset_row

OBJECT = "DISH-FORECAST-PACKAGE-B02"
HOST = "GROUND-TERMINAL-LINEAR-CLEARANCE-A03"
ARMS = ("CONTROL", "FORECAST_PACKAGE")
HARD_EVENTS = ("invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear",
               "command_slew_breach", "separation_breach")


def planned_cost():
    return {"law": "N ordinary + L next-label + 2E delay + H consequence; H <= 20E",
            "N": 65536, "L": 65536, "E_upper": 65536, "H_upper": 1310720,
            "native_training_calls_upper": 1572864, "evaluation_ticks_upper": 4800,
            "optimizer_steps": 512, "projected_wall_seconds": None,
            "projection_status": "unmeasured on this host; not inferred from native work bound",
            "whole_arm_cap_seconds": 1800, "shared_preparation_allocation": "measured shared wall / 2"}


def new_progress():
    return {"ordinary_training_transitions": 0, "next_label_steps": 0,
            "service_label_eligible": 0, "next_mask_count": 0,
            "completed_updates": 0, "optimizer_steps": 0,
            "training_service": 0, "training_energy": 0.0,
            "training_legal_transfers": 0, "training_terminals": 0,
            "training_hard_events": dict.fromkeys(HARD_EVENTS, 0),
            "evaluation_ticks": 0, "curves": [], "evaluation_rows": []}


def check_time(deadline):
    if time.perf_counter() >= deadline:
        raise TimeoutError("B02 complete-arm wall allowance exhausted")


def native_state(batch):
    return np.frombuffer(batch._states, dtype=np.dtype(backend._State), count=batch.width)


class TrainingMeasurements:
    """Count the actual ordinary and passive calls without changing either native path."""

    def __init__(self, native, progress, deadline):
        self.native, self.progress, self.deadline = native, progress, deadline
        self.width = native.width

    def passive_labels(self, rows):
        check_time(self.deadline)
        labels = self.native.passive_labels(rows)
        self.progress["next_label_steps"] += self.width
        self.progress["service_label_eligible"] += int(labels["q_mask"].sum())
        self.progress["next_mask_count"] += int(labels["next_mask"].sum())
        return labels

    def step(self, rows):
        check_time(self.deadline)
        before = native_state(self.native).copy()
        outcome = self.native.step(rows)
        after = native_state(self.native)
        p = self.progress
        p["ordinary_training_transitions"] += self.width
        p["training_service"] += int(outcome["service"].sum())
        p["training_energy"] += float((after["total_energy"] - before["total_energy"]).sum())
        p["training_legal_transfers"] += int(outcome["cas_applied"].sum())
        p["training_terminals"] += int(outcome["terminal"].sum())
        for name in HARD_EVENTS:
            p["training_hard_events"][name] += int((after[name] - before[name]).sum())
        return outcome

    def reset_selected(self, mask, rows):
        return self.native.reset_selected(mask, rows)


def parameter_movement(initial, final):
    before = torch.load(BytesIO(initial), map_location="cpu", weights_only=False)["model"]
    after = torch.load(BytesIO(final), map_location="cpu", weights_only=False)["model"]
    initial_sq = final_sq = displacement_sq = absolute = 0.0
    for name, value in before.items():
        first = value.double()
        last = after[name].double()
        difference = last - first
        initial_sq += float(first.square().sum())
        final_sq += float(last.square().sum())
        displacement_sq += float(difference.square().sum())
        absolute += float(difference.abs().sum())
    return {"initial_norm": math.sqrt(initial_sq), "final_norm": math.sqrt(final_sq),
            "absolute_l1_displacement": absolute, "l2_displacement": math.sqrt(displacement_sq),
            "relative_l2_displacement": math.sqrt(displacement_sq / initial_sq)}


def terminal_facts(native, completed_ticks):
    state = native_state(native)[0]
    separation = float(np.linalg.norm(state["p"][:2] - state["p"][2:]))
    causes = []
    if np.any(state["battery"] <= 0):
        causes.append("battery_exhausted")
    if separation < 15:
        causes.append("separation_below_15")
    if int(state["tick"]) >= 1200:
        causes.append("fixed_horizon")
    if bool(state["terminal"]) and not causes:
        causes.append("native_terminal_other")
    return {"native_terminal": bool(state["terminal"]), "causes": causes,
            "native_tick": int(state["tick"]), "actual_completed_ticks": completed_ticks,
            "battery": state["battery"].tolist(), "separation": separation,
            "owner": int(state["owner"]), "actuator_owner": int(state["actuator_owner"])}


def evaluate_episode(native, policy, deadline, progress, record, horizon=1200):
    """Ordinary stepping only; unstepped terminal remainder contributes zero service."""
    observation = native.observe()
    record.update(service_ticks=0, completed_ticks=0, legal_transfers=0,
                  service_before_transfer=0, service_at_or_after_transfer=0,
                  energy=0.0, hard_events=dict.fromkeys(HARD_EVENTS, 0))
    transferred = False
    for tick in range(horizon):
        check_time(deadline)
        if bool(observation["terminal"][0]):
            break
        owner_before = np.asarray(observation["owner"], dtype=np.int64)
        rows = policy.step_rows(observation, sampler=None, global_tick=tick, deterministic=True)
        observation = native.step(rows)
        progress["evaluation_ticks"] += 1
        record["completed_ticks"] += 1
        policy.apply_native_promotion(owner_before=owner_before, step_rows=rows, observation_after=observation)
        transfers = int(observation["cas_applied"][0])
        record["legal_transfers"] += transfers
        transferred = transferred or bool(transfers)
        service = int(observation["service"][0])
        record["service_ticks"] += service
        record["service_at_or_after_transfer" if transferred else "service_before_transfer"] += service
        state = native_state(native)[0]
        record["energy"] = float(state["total_energy"])
        record["hard_events"] = {name: int(state[name]) for name in HARD_EVENTS}
        record["terminal"] = terminal_facts(native, record["completed_ticks"])
    record["unstepped_zero_service_ticks"] = horizon - record["completed_ticks"]
    record["fixed_horizon"] = horizon
    record["post_transfer_service_attribution"] = "temporal only; packet source unestimated"
    record["complete"] = record["completed_ticks"] == horizon or bool(observation["terminal"][0])
    return record


def run_arm(arm, output, deadline, progress):
    package = arm == "FORECAST_PACKAGE"
    master = hashlib.sha256(f"{OBJECT}/seed/61".encode("ascii")).digest()
    torch.set_num_threads(1)
    library = load_host(HOST)
    check_time(deadline)
    initial = build_master_addressed_initial_state(master=master, block=0, arm="STRUCTURED")
    initial_parameters = torch.load(BytesIO(initial), map_location="cpu", weights_only=False)["model"]
    progress["initial_model_norm"] = math.sqrt(sum(float(value.double().square().sum()) for value in initial_parameters.values()))
    progress["configuration"] = {
        "seed": 61, "master_hex": master.hex(), "underlying_arm": "STRUCTURED", "block": 0,
        "host": HOST, "forecast_package": package, "torch_threads": torch.get_num_threads(),
        "training_dtype": "float32", "native_dtype": "float64", "lanes": 32, "ticks_per_update": 128,
        "updates": 16, "epochs": 4, "minibatches_per_epoch": 8, "optimizer": "AdamW",
        "learning_rate": 3e-4, "forecast_coefficient": 0.025,
        "pairing": "same master-addressed STRUCTURED initialization and semantic-address exogenous streams",
        "host_headroom": "no tuned same-host reference", "evaluation_selection": "update16 only",
    }
    reset = MasterAddressedTrainResetFactory(master=master, block=0, arm="STRUCTURED")
    native = backend.native_batch_from_rows(reset.rows(np.zeros(32, dtype=np.int64)), library=library)
    measured = TrainingMeasurements(native, progress, deadline)
    flow = NativePersistentTrainingFlow(native=measured, arm="STRUCTURED", master=master, block=0,
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
            row = _reset_row(master, coordinate)
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


def exposure(progress):
    n, labels, eligible = (progress[name] for name in
                           ("ordinary_training_transitions", "next_label_steps", "service_label_eligible"))
    return {"ordinary_training_transitions": n, "next_label_steps": labels,
            "service_label_eligible": eligible, "next_mask_count": progress["next_mask_count"],
            "delay_steps": 2 * eligible, "consequence_steps": None,
            "consequence_steps_upper": 20 * eligible,
            "consequence_scope": "unmeasured; zero service does not reveal skipped native calls",
            "native_training_calls_lower": n + labels + 2 * eligible,
            "native_training_calls_upper": n + labels + 22 * eligible,
            "optimizer_steps": progress["optimizer_steps"], "completed_updates": progress["completed_updates"],
            "ordinary_evaluation_ticks": progress["evaluation_ticks"], "paired_training_replicates": 1}


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
