"""One fresh final-only learning pair for the fixed arrival-bridge rule."""
import json
import time

from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b04 import study as b04

OBJECT = "DISH-ARRIVAL-BRIDGE-RETENTION-B08"
SEED = 137
ARMS = ("REPLACE", "HALF_RETAIN")
EXCLUSIVE_CAP = 900.0
SHARED_CAP = 300.0
EXTERNAL_RESERVE = 90.0


def planned_cost():
    return {"per_arm": {**b04.planned_cost(), "evaluation_ticks_upper": 4800,
                        "whole_arm_cap_seconds": 1050,
                        "initial_evaluation_episodes": 0, "final_evaluation_episodes": 4},
            "exclusive_cap_seconds": EXCLUSIVE_CAP, "shared_cap_seconds": SHARED_CAP,
            "charged_arm_cap_seconds": 1050, "pair_cap_seconds": 2100,
            "shared_allocation": "S once, S/2 per arm", "external_reserve_seconds": EXTERNAL_RESERVE}


def exposure(arms):
    return {mode: {**b04.exposure(arm), "initial_evaluation_episodes": 0,
                   "final_evaluation_rows": len(arm.get("evaluation_rows", [])),
                   "TRAIN_denominator_ordinary_transitions": arm["ordinary_training_transitions"],
                   "EVAL_denominator_actual_ticks": arm["evaluation_ticks"], "H_measured": False}
            for mode, arm in arms.items()}


def reduce_pair(arms):
    result = {"status": "INCOMPLETE", "Delta_bridge": None, "means": {}, "paired_rows": [],
              "training_pairs": 1, "MEI_service_ticks": 24,
              "uncertainty": "one matched training pair; no training-population interval",
              "post_CAS_source_value": "unestimated"}
    keys = [c.canonical_key() for c in b04.coordinates()]
    panels = {}
    for mode in ARMS:
        arm = arms.get(mode, {})
        rows = arm.get("evaluation_rows", [])
        panel = {r["coordinate"]: r for r in rows if r.get("complete")}
        complete = len(rows) == 4 and set(panel) == set(keys)
        panels[mode] = panel if complete else None
        result["means"][mode] = sum(panel[k]["service_ticks"] for k in keys) / 4 if complete else None
    learners = all(arms.get(m, {}).get("completed_updates") == 16
                   and arms[m].get("ordinary_training_transitions") == 65536
                   and arms[m].get("optimizer_steps") == 512 for m in ARMS)
    if learners and all(panels[m] is not None for m in ARMS):
        result["paired_rows"] = [{"coordinate": k, "REPLACE": panels[ARMS[0]][k],
                                  "HALF_RETAIN": panels[ARMS[1]][k],
                                  "difference": panels[ARMS[1]][k]["service_ticks"]
                                  - panels[ARMS[0]][k]["service_ticks"]} for k in keys]
        result["Delta_bridge"] = sum(r["difference"] for r in result["paired_rows"]) / 4
        result["status"] = "COMPLETE"
    delta = result["Delta_bridge"]
    result["branch_facts"] = {
        "at_least_plus24": None if delta is None else delta >= 24,
        "open_band": None if delta is None else -24 < delta < 24,
        "at_most_minus24": None if delta is None else delta <= -24,
        "ordinary_EVAL_transfers": {m: sum(r.get("legal_transfers", 0)
                                              for r in arms.get(m, {}).get("evaluation_rows", []))
                                    for m in ARMS},
        "native_tradeoff_disposition": "DM reads all native rows; no automated gate"}
    return result


def allocate_cost(result, started, prior_shared_seconds, now=None):
    elapsed = (time.perf_counter() if now is None else now) - started
    exclusive = {m: result.get("arms", {}).get(m, {}).get("exclusive_wall_seconds", 0.0) for m in ARMS}
    shared = prior_shared_seconds + elapsed - sum(exclusive.values())
    charged = {m: exclusive[m] + shared / 2 for m in ARMS}
    result["cost"] = {"prior_shared_seconds": prior_shared_seconds, "shared_seconds": shared,
                      "exclusive_arm_seconds": exclusive, "charged_arm_seconds": charged,
                      "in_run_wall_seconds": elapsed, "charged_pair_seconds": prior_shared_seconds + elapsed,
                      "remaining_shared_seconds": SHARED_CAP - shared,
                      "remaining_exclusive_seconds": {m: EXCLUSIVE_CAP - exclusive[m] for m in ARMS}}
    if shared > SHARED_CAP or any(v > EXCLUSIVE_CAP for v in exclusive.values()):
        result["status"] = "INCOMPLETE"
        result["budget_exhausted"] = True
    return result["cost"]


def shared_deadline(result, started, prior_shared_seconds, *, reserve=EXTERNAL_RESERVE, now=None):
    now = time.perf_counter() if now is None else now
    cost = allocate_cost(result, started, prior_shared_seconds, now)
    return now + cost["remaining_shared_seconds"] - reserve


def run_study(output, started, prior_shared_seconds, result, *, set_deadline=lambda deadline: None):
    shared = output / "shared"
    shared.mkdir()
    result["shared"] = b04.new_progress()
    result["arms"] = {}
    deadline = shared_deadline(result, started, prior_shared_seconds)
    set_deadline(deadline)
    b04.prepare_shared(shared, deadline, result["shared"], seed=SEED,
                       object_name=OBJECT, master_family=OBJECT, evaluate_initial=False)
    result["master_hex"] = result["shared"]["master_hex"]
    result["resets"] = json.loads((shared / "resets.json").read_text(encoding="utf8"))
    for mode in ARMS:
        b04.check_time(shared_deadline(result, started, prior_shared_seconds))
        arm = result["arms"][mode] = b04.new_progress()
        arm.update(arm=mode, status="INCOMPLETE")
        destination = output / mode.lower()
        destination.mkdir()
        arm_started = time.perf_counter()
        deadline = arm_started + EXCLUSIVE_CAP - 2.0
        set_deadline(deadline)
        try:
            def evaluate(native, policy, deadline, progress, record):
                record.update(arm=mode, phase="final", arrival_bridge_mode=policy.model.arrival_bridge_mode)
                return b04.evaluate_episode(native, policy, deadline, progress, record,
                                            record_first_transfer=True)
            b04.run_arm("LOW_LR", destination, deadline, arm, shared, seed=SEED,
                        object_name=OBJECT, master_family=OBJECT, episode_evaluator=evaluate,
                        mean_mode="DIRECT_MEAN", arrival_bridge_mode=mode)
            arm["configuration"].update(arm=mode, arrival_bridge_mode=mode)
        finally:
            arm["exclusive_wall_seconds"] = time.perf_counter() - arm_started
        set_deadline(shared_deadline(result, started, prior_shared_seconds))
    result["primary"] = reduce_pair(result["arms"])
    result["status"] = result["primary"]["status"]
