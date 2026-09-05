"""B06 RAW-only preparation and paired endpoint reading; accepted learner unchanged."""

import time

from experiments.candidates.commitment_residual_triggered_options.residual_cycle_endpoints_b04 import experiment as b04

raw, base, b01, np = b04.raw, b04.base, b04.b01, b04.np
OBJECT_ID = "CRTO-RAW-EXPOSURE-B06"
ENDPOINTS = (258, 516)
MEI = .000625
HISTORICAL = {
    1: {"seconds_per_update": .0600742854535207, "readout_seconds": .008204734011087567,
        "scales": (18.92643228704128, .10428775735716496, .287416011095047),
        "movement": (.15185621905905447, 1.1030603123304337)},
    2: {"seconds_per_update": .057716591918605016, "readout_seconds": .012151057992014103,
        "scales": (18.844772502567565, .10383779850280324, .2884293794631958),
        "movement": (.1765496051797392, .9841327580955074)},
}


def project_cost(seed):
    prior = HISTORICAL[seed]
    scales = dict(zip(("initial_parameter_l2", "initial_parameter_rms", "initial_parameter_linf"), prior["scales"]))
    return {"seed": seed, "result_bearing": False, "law": "3*(P + u*t_s + E_s)",
            "P": 125.72588114999235, "t_s": prior["seconds_per_update"], "E_s": prior["readout_seconds"],
            "projected_seconds_by_update": {str(u): 3 * (125.72588114999235 + u * prior["seconds_per_update"]
                                                       + prior["readout_seconds"]) for u in ENDPOINTS},
            "arm_cap_seconds": b04.ARM_CAP, "invocation_cap_seconds": b04.SHARED_CAP,
            "prior_B05_update_258_measurement": base._exposure_line(258, scales, dict(zip((
                "parameter_displacement_l2_over_initial_l2", "parameter_displacement_linf_over_initial_linf"), prior["movement"]))),
            "exposure_plan": [{"update": u, "processed_examples": 32 * u, "recipient_occurrences": 32 * u // 48,
                               "batch_size": 32, "adam_lr": .001, "nominal_lr_exposure": .001 * u} for u in ENDPOINTS],
            "work_plan": {"predictor_tapes": 128, "predictor_updates": 100, "predictor_processed_examples": 12800,
                          "gate_updates": 516, "processed_examples": 16512, "network_forward_rows": 32,
                          "scored_decisions": 32, "unique_eval_rows": 16, "calibration_tapes": 0,
                          "calibration_examples": 0, "derangement_packets": 0}}


def result_rule(difference, baseline_competent, endpoint_competent):
    if not np.isfinite(difference):
        raise ValueError("nonfinite paired difference has no scientific branch")
    if difference < -MEI:
        return "B06-MATERIAL-REGRET-COST"
    if not endpoint_competent:
        return "B06-COMPARATOR-STILL-WEAK"
    if baseline_competent:
        return "B06-COMPETENCE-ALREADY-PRESENT"
    if difference > MEI:
        return "B06-COMPETENCE-RECOVERED-WITH-GAIN"
    return "B06-COMPETENCE-RECOVERED-WITHIN-MEI"


def aggregate_rule(branches):
    """DM may apply this after both seeds; a partial object has no aggregate."""
    if set(branches) != {1, 2} or any(v is None for v in branches.values()):
        return None
    if "B06-MATERIAL-REGRET-COST" in branches.values():
        return "B06-COST-PRESENT"
    if "B06-COMPARATOR-STILL-WEAK" in branches.values():
        return "B06-COMPARATOR-LIMITED"
    if all(v in ("B06-COMPETENCE-RECOVERED-WITH-GAIN", "B06-COMPETENCE-RECOVERED-WITHIN-MEI") for v in branches.values()):
        return "B06-COMPETENCE-RECOVERED-BOTH"
    return "B06-ALREADY-PRESENT-OR-MIXED"


def paired_readout(labels, predictions, exposures, train, batch_size=32):
    points = {}
    for line in exposures:
        update = line["update"]
        values = predictions[update]
        if values.shape != (len(labels), 8) or values.dtype != np.float32:
            raise ValueError("each snapshot requires one FP32 prediction vector per row")
        if not all(np.isfinite(line[k]) and line[k] > 0 for k in (
                "parameter_displacement_l2_over_initial_l2", "parameter_displacement_linf_over_initial_linf")):
            raise ValueError("B06 requires finite positive movement at both endpoints")
        visits = np.bincount(np.resize(np.arange(len(train)), update * batch_size), minlength=len(train))
        points[str(update)] = {**raw.score_readout(labels, values), "exposure": line,
                              "recipient_counts": {r.key.text: int(n) for r, n in zip(train, visits)}}
    baseline, endpoint = points.values()
    difference = baseline["equal_side_regret"] - endpoint["equal_side_regret"]
    changed = [{"row_key": before["row_key"], "material_side": before["material_side"],
                "baseline_action": before["selected_action"], "endpoint_action": after["selected_action"],
                "baseline_regret": before["native_regret"], "endpoint_regret": after["native_regret"],
                "paired_regret_difference": before["native_regret"] - after["native_regret"]}
               for before, after in zip(baseline["rows"], endpoint["rows"])
               if before["selected_action_index"] != after["selected_action_index"]]
    return {"endpoints": points, "D": difference, "MEI": MEI, "changed_actions": changed,
            "C_baseline": baseline["competent"], "C_endpoint": endpoint["competent"],
            "result_branch": result_rule(difference, baseline["competent"], endpoint["competent"])}


def prepare(seed, monitor, toy):
    if toy:
        train, evaluation, metadata = base._toy_population()
        return train, evaluation, metadata, {"tapes": 0, "examples": 0, "updates": 0, "processed_examples": 0}
    tapes = tuple(t for regime, first in (("K4", 0), ("K8", 64))
                  for t in b01.build_balanced_tapes(replicate=0, split=b01.Split.PREDICTOR_FIT,
                      regime=regime, count=64, first_episode_index=first, rng_namespace=b01.LEARNER_NAMESPACE))
    examples = b01._predictor_examples(tapes, monitor=monitor)
    predictor, audit = b01.fit_fresh_predictor(examples, replicate=seed, updates=100, batch_size=128,
        rng_namespace=b01.LEARNER_NAMESPACE, resource_monitor=monitor)
    train, evaluation, metadata = b01._selected_rows(predictor, monitor=monitor)
    return train, evaluation, metadata, {"tapes": len(tapes), "examples": audit.examples,
        "updates": audit.updates, "processed_examples": audit.processed_examples, "rng_namespace": b01.LEARNER_NAMESPACE}


def run_experiment(output_dir, *, seed, argv, execution_node, toy=False):
    started = time.perf_counter()
    train, evaluation, metadata, predictor = prepare(seed, lambda: b04.check_wall(started), toy)
    training_packets, evaluation_packets = base._raw_dataset(train), base._raw_dataset(evaluation)
    endpoints, batch_size = ((3, 6), 4) if toy else (ENDPOINTS, 32)
    preparation_seconds = time.perf_counter() - started
    snapshots, exposures, training_seconds, scales = b04.train_path(train, training_packets, seed=seed,
        final_update=endpoints[-1], trace_updates=endpoints, batch_size=batch_size, started=started, representation="RAW")
    evaluation_started = time.perf_counter()
    predictions = raw.forward_snapshots(snapshots, evaluation, evaluation_packets,
        lambda: b04.check_wall(started, training_seconds + time.perf_counter() - evaluation_started))
    forward_seconds = time.perf_counter() - evaluation_started
    summary = paired_readout(raw.panel_labels(evaluation, metadata), predictions, exposures, train, batch_size)
    evaluation_seconds = time.perf_counter() - evaluation_started
    b04.check_wall(started, training_seconds + evaluation_seconds)
    peak = base._peak_rss_bytes()
    summary.update({"object_id": OBJECT_ID, "seed": seed, "toy": toy, "launch_sha": base.current_launch_sha(),
        "exact_argv": list(argv), "execution_node": execution_node, "thread_contract": base.thread_contract(),
        "source_namespace": b01.SOURCE_NAMESPACE, "initial_parameter_scales": scales, "predictor": predictor,
        "selected_population": {"train_rows": len(train), "evaluation_rows": len(evaluation),
            "canonical_order": [r.key.text for r in train],
            "metadata": [{"row_key": r.key.text, **metadata[r.key.text]} for r in (*train, *evaluation)]},
        "work_counts": {"gate_updates": endpoints[-1], "processed_examples": endpoints[-1] * batch_size,
            "network_forward_rows": len(endpoints) * len(evaluation), "scored_decisions": len(endpoints) * len(evaluation),
            "unique_eval_rows": len(evaluation), "calibration_tapes": 0, "calibration_examples": 0, "derangement_packets": 0,
            "environment_transitions": 0 if toy else 128 * 256 + sum(r.key.primitive_time for r in (*train, *evaluation)),
            "common_future_branch_steps": 0 if toy else sum(int(np.count_nonzero(r.legal_mask)) * 16 for r in (*train, *evaluation))},
        "cost_law": {**project_cost(seed), "measured_preparation_seconds": preparation_seconds,
            "measured_training_seconds": training_seconds, "measured_seconds_per_update": training_seconds / endpoints[-1],
            "measured_forward_seconds": forward_seconds, "measured_scoring_seconds": evaluation_seconds - forward_seconds},
        "resources": {"wall_seconds": time.perf_counter() - started, "peak_rss_bytes": peak,
                      "status": "measured" if peak is not None else "resources_unmeasured"}})
    if toy:
        summary["result_branch"] = None
        summary["engineering_only"] = "TOY_SMOKE_NOT_A_SCIENTIFIC_POPULATION"
    raw.publish_summary(output_dir, summary)
    b04.check_wall(started)
    return summary
