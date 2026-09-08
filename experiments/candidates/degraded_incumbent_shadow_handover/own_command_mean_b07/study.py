"""One matched pair of raw-own-command and direct means on the retained B04 path."""
import json
import time

from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b04 import study as b04

OBJECT = "DISH-OWN-COMMAND-MEAN-B07"
SEED = 127
ARMS = ("DIRECT_MEAN", "OWN_COMMAND_MEAN")
EXTERNAL_AND_CLOSURE_RESERVE_SECONDS = 10.0


def evaluate_episode(native, policy, deadline, progress, record):
    record["mean_mode"] = policy.mean_mode
    return b04.evaluate_episode(native, policy, deadline, progress, record,
                                record_first_transfer=True)


def exposure(arms):
    return {mode: {**b04.exposure(arm),
                   "initial_evaluation_rows": len(arm.get("initial_rows", [])),
                   "final_evaluation_rows": len(arm.get("evaluation_rows", [])),
                   "TRAIN_denominator_ordinary_transitions": arm["ordinary_training_transitions"],
                   "EVAL_denominator_actual_ticks": arm["evaluation_ticks"],
                   "H_measured": False}
            for mode, arm in arms.items()}


def planned_cost():
    return {"per_arm": {**b04.planned_cost(), "evaluation_ticks_upper": 9600,
                        "initial_evaluation_episodes": 4, "final_evaluation_episodes": 4},
            "pair_cap_seconds": 3600, "shared_allocation": "S once, S/2 per arm"}


def initial_rows(mode, shared, deadline, progress):
    library = b04.load_host(b04.HOST)
    initial = (shared / "initial_state.pt").read_bytes()
    resets = json.loads((shared / "resets.json").read_text(encoding="utf8"))
    progress["initial_rows"] = []
    for coordinate in b04.coordinates():
        b04.check_time(deadline)
        reset = resets[coordinate.canonical_key()]
        native = b04.backend.native_batch_from_rows((reset,), library=library)
        state = b04.RecurrentRolloutState.fresh("STRUCTURED", width=1)
        policy = b04.BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=initial,
                                          state=state, forecast_package=False, mean_mode=mode)
        record = {"coordinate": coordinate.canonical_key(), "reset": reset,
                  "regime": coordinate.regime, "schedule": coordinate.schedule,
                  "speed": 4, "slot": 0, "block": 0, "arm": mode,
                  "phase": "initial", "source": f"new:{mode}:zero_update:raw"}
        progress["initial_rows"].append(record)
        evaluate_episode(native, policy, deadline, progress, record)


def reduce_pair(arms):
    """Retain final observations independently of missing initial references."""
    result = {"status": "INCOMPLETE", "final_differences": [], "means": {},
              "Delta_mean": None, "D_OWN": None, "D_DIRECT": None}
    keys = [c.canonical_key() for c in b04.coordinates()]
    panels = {}
    for mode in ARMS:
        arm = arms.get(mode, {})
        panels[mode] = {}
        result["means"][mode] = {}
        for phase, field in (("initial", "initial_rows"), ("final", "evaluation_rows")):
            rows = arm.get(field, [])
            panel = {r["coordinate"]: r for r in rows if r.get("complete")}
            complete = len(rows) == 4 and set(panel) == set(keys)
            panels[mode][phase] = panel if complete else None
            result["means"][mode][phase] = (
                sum(panel[k]["service_ticks"] for k in keys) / 4 if complete else None)
    learners = all(arms.get(mode, {}).get("completed_updates") == 16
                   and arms[mode].get("ordinary_training_transitions") == 65536
                   and arms[mode].get("optimizer_steps") == 512 for mode in ARMS)
    if learners and all(panels[m]["final"] is not None for m in ARMS):
        result["final_differences"] = [
            {"coordinate": k, "own_minus_direct": panels[ARMS[1]]["final"][k]["service_ticks"]
             - panels[ARMS[0]]["final"][k]["service_ticks"]} for k in keys]
        result["Delta_mean"] = sum(r["own_minus_direct"] for r in result["final_differences"]) / 4
        result["status"] = "FINAL_PRIMARY_COMPLETE"
    for mode, field in ((ARMS[0], "D_DIRECT"), (ARMS[1], "D_OWN")):
        means = result["means"][mode]
        if arms.get(mode, {}).get("completed_updates") == 16 and all(v is not None for v in means.values()):
            result[field] = means["final"] - means["initial"]
    if result["Delta_mean"] is not None and all(result[f] is not None for f in ("D_DIRECT", "D_OWN")):
        result["status"] = "COMPLETE"
    delta, own = result["Delta_mean"], result["D_OWN"]
    rows = [r for arm in arms.values() for field in ("initial_rows", "evaluation_rows")
            for r in arm.get(field, [])]
    transfers = sum(r.get("legal_transfers", 0) for r in rows)
    result["branch_facts"] = {
        "at_least_plus24": None if delta is None else delta >= 24,
        "increment_with_own_initial_loss": None if delta is None or own is None else delta > 0 and own <= -24,
        "open_band": None if delta is None else -24 < delta < 24,
        "at_most_minus24": None if delta is None else delta <= -24,
        "ordinary_legal_transfers_observed": transfers,
        "no_ordinary_legal_transfer_in_complete_panel": result["status"] == "COMPLETE" and transfers == 0,
        "input_learner_or_primary_incomplete": result["status"] != "COMPLETE",
        "native_tradeoff_disposition": "DM judgment from all native rows; no automated gate",
    }
    return result


def allocate_cost(result, started, prior_shared_seconds, now=None):
    now = time.perf_counter() if now is None else now
    elapsed = now - started
    exclusive = {m: result.get("arms", {}).get(m, {}).get("exclusive_wall_seconds", 0.0) for m in ARMS}
    shared = prior_shared_seconds + elapsed - sum(exclusive.values())
    charged = {m: exclusive[m] + shared / 2 for m in ARMS}
    result["cost"] = {"prior_shared_seconds": prior_shared_seconds, "shared_seconds": shared,
                      "exclusive_arm_seconds": exclusive, "charged_arm_seconds": charged,
                      "in_run_wall_seconds": elapsed, "charged_pair_seconds": prior_shared_seconds + elapsed,
                      "remaining_arm_seconds": {m: 1800 - charged[m] for m in ARMS},
                      "remaining_pair_seconds": 3600 - prior_shared_seconds - elapsed}
    if any(v >= 1800 for v in charged.values()) or elapsed + prior_shared_seconds >= 3600:
        result["status"] = "INCOMPLETE"
        result["budget_exhausted"] = True
    return result["cost"]


def run_study(output, started, prior_shared_seconds, result, *, set_deadline=lambda deadline: None):
    shared = output / "shared"
    shared.mkdir()
    result["shared"] = b04.new_progress()
    result["arms"] = {}
    result["external_and_closure_reserve_seconds"] = EXTERNAL_AND_CLOSURE_RESERVE_SECONDS
    pair_deadline = started + 3600 - prior_shared_seconds - EXTERNAL_AND_CLOSURE_RESERVE_SECONDS
    set_deadline(pair_deadline)
    b04.prepare_shared(shared, pair_deadline, result["shared"], seed=SEED,
                       object_name=OBJECT, master_family=OBJECT, evaluate_initial=False)
    result["master_hex"] = result["shared"]["master_hex"]
    result["resets"] = json.loads((shared / "resets.json").read_text(encoding="utf8"))
    for mode in ARMS:
        arm = result["arms"][mode] = b04.new_progress()
        arm.update(arm=mode, mean_mode=mode, status="INCOMPLETE")
        destination = output / mode.lower()
        destination.mkdir()
        cost = allocate_cost(result, started, prior_shared_seconds)
        arm_started = time.perf_counter()
        deadline = min(pair_deadline, arm_started + 1800 - (cost["shared_seconds"] + EXTERNAL_AND_CLOSURE_RESERVE_SECONDS) / 2)
        set_deadline(deadline)
        try:
            initial_rows(mode, shared, deadline, arm)
            def evaluate(native, policy, deadline, progress, record):
                record.update(arm=mode, phase="final")
                return evaluate_episode(native, policy, deadline, progress, record)
            b04.run_arm("LOW_LR", destination, deadline, arm, shared, seed=SEED,
                        object_name=OBJECT, master_family=OBJECT,
                        episode_evaluator=evaluate, mean_mode=mode)
            arm["configuration"]["arm"] = mode
        finally:
            arm["exclusive_wall_seconds"] = time.perf_counter() - arm_started
    set_deadline(pair_deadline)
    result["primary"] = reduce_pair(result["arms"])
    result["status"] = result["primary"]["status"]
