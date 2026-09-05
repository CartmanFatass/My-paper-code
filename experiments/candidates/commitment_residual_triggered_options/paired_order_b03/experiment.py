"""Two fresh RAW paths sharing preparation, differing only in TRAIN order."""

from pathlib import Path
import time

from experiments.candidates.commitment_residual_triggered_options.raw_cycle_readout_b02 import experiment as raw

base, np = raw.base, raw.np
OBJECT_ID = "CRTO-PAIRED-ORDER-B03"
ENDPOINTS = (252, 255, 258)
ARMS = ("CANONICAL", "PAIRED")
DELTA = .0025


def project_cost(seed=0):
    if seed != 0:
        raise ValueError("B03 has fixed seed 0")
    preparation = 86.52683217800222 - 14.290888625997468 - .015708084996731486 - .0031209949956974015
    update = 14.290888625997468 / 257
    forward = .015708084996731486 / 5
    readout = .0031209949956974015
    per_arm = 3 * (preparation + 258 * update + 3 * forward + readout)
    shared = 3 * (preparation + 2 * 258 * update + 6 * forward + readout)
    return {"object_id": OBJECT_ID, "result_bearing": False,
            "law": "3*(B + arms*U*t + snapshots*f + r)", "measured_source": "B02 stages",
            "B": preparation, "t": update, "f": forward, "r": readout,
            "U": 258, "projected_arm_seconds": per_arm, "projected_shared_seconds": shared,
            "cap_seconds": raw.CAP_SECONDS, "projection_within_cap": max(per_arm, shared) <= raw.CAP_SECONDS,
            "prospective_work_counts": {"predictor_tapes": 128, "predictor_updates": 100,
                                        "predictor_processed_examples": 12800, "raw_gate_updates": 516,
                                        "raw_processed_examples": 16512, "network_forward_rows": 96,
                                        "scored_decisions": 96, "unique_eval_rows": 16},
            "prior_measured_exposure": base._exposure_line(258, base.INITIAL_ANCHOR, {
                "parameter_displacement_l2_over_initial_l2": .136922756396,
                "parameter_displacement_linf_over_initial_linf": .915735779253})}


def training_orders(rows, packets, metadata, declarations=base.SELECTED_ROWS):
    """Bind original declaration pairs to canonical rows, never regroup by event/onset."""
    packets.require_rows(rows)
    canonical_indices = {(metadata[r.key.text]["source_slot"], metadata[r.key.text]["episode_index"]): i
                         for i, r in enumerate(rows)}
    paired_indices, pair_membership = [], {}
    for offset in range(0, len(declarations), 2):
        keep, replan = declarations[offset:offset + 2]
        if keep.split != "TRAIN":
            continue
        pair = {"original_pair_index": offset // 2,
                "KEEP_address": keep.__dict__.copy(), "REPLAN_address": replan.__dict__.copy()}
        for address in (keep, replan):
            index = canonical_indices[(address.source_slot, address.episode_index)]
            paired_indices.append(index)
            pair_membership[index] = pair
    if sorted(paired_indices) != list(range(len(rows))):
        raise ValueError("original TRAIN pairs must permute the whole canonical population")
    orders, sequences = {}, {}
    for arm, indices in (("CANONICAL", list(range(len(rows)))), ("PAIRED", paired_indices)):
        ordered_rows = tuple(rows[i] for i in indices)
        ordered_packets = base.PacketDataset(tuple(packets.row_keys[i] for i in indices), packets.values[indices].copy())
        ordered_packets.require_rows(ordered_rows)
        orders[arm] = (ordered_rows, ordered_packets)
        sequences[arm] = [{"row_key": rows[i].key.text, "canonical_index": i,
                           "address": metadata[rows[i].key.text], **pair_membership[i]} for i in indices]
    return orders, sequences


def occurrence_counts(rows, update, batch_size):
    indices = np.resize(np.arange(len(rows)), update * batch_size)
    counts = np.bincount(indices, minlength=len(rows))
    return {row.key.text: int(count) for row, count in zip(rows, counts)}


def apply_result_rule(differences, canonical_competent, paired_competent):
    if not all(np.isfinite(v) for v in differences.values()):
        raise ValueError("nonfinite difference has no scientific branch")
    if not canonical_competent:
        return "B03-COMPARATOR-WEAK"
    if any(v < -DELTA for v in differences.values()):
        return "B03-MATERIAL-REGRET-LOSS"
    if paired_competent:
        if differences[max(differences)] > DELTA:
            return "B03-PAIRED-ORDER-SIGNAL"
        return "B03-PAIRED-ORDER-NO-MATERIAL-GAIN"
    return "B03-PAIRED-ORDER-INCOMPETENT"


def comparison_summary(labels, predictions, exposures, orders, batch_size=32, endpoints=ENDPOINTS):
    arms = {}
    for arm in ARMS:
        lines = {line["update"]: line for line in exposures[arm]}
        points = {}
        for update in endpoints:
            values = predictions[arm][update]
            if values.shape != (len(labels), 8) or values.dtype != np.float32:
                raise ValueError("snapshot forward must provide one FP32 vector per row")
            points[str(update)] = {**raw.score_readout(labels, values), "exposure": lines[update],
                                  "per_row_occurrences": occurrence_counts(orders[arm][0], update, batch_size)}
        arms[arm] = {"endpoints": points}
    differences = {}
    for update in endpoints:
        canonical, paired = (arms[a]["endpoints"][str(update)] for a in ARMS)
        if canonical["per_row_occurrences"] != paired["per_row_occurrences"]:
            raise ValueError("declared endpoint TRAIN multisets differ")
        differences[update] = canonical["equal_side_regret"] - paired["equal_side_regret"]
    primary = endpoints[-1]
    return {"arms": arms, "paired_differences": {str(u): d for u, d in differences.items()},
            "primary_update": primary, "primary_D": differences[primary],
            "result_branch": apply_result_rule(differences,
                arms["CANONICAL"]["endpoints"][str(primary)]["competent"],
                arms["PAIRED"]["endpoints"][str(primary)]["competent"])}


def toy_preparation():
    train, evaluation, metadata = base._toy_population()
    declarations = []
    for row in train:
        side = metadata[row.key.text]["side"]
        address = base.SelectedAddress("TRAIN", "TOY", 0, side, 0, row.key.episode_index, 0.0)
        metadata[row.key.text].update(address.__dict__)
        declarations.append(address)
    return train, evaluation, metadata, tuple(declarations)


def run_experiment(output_dir, *, argv, execution_node, seed=0, toy=False):
    started = time.perf_counter()
    monitor = lambda: raw.check_wall(started)
    cost = project_cost(seed)
    if not cost["projection_within_cap"]:
        raise ValueError("B03 projection exceeds shared or arm cap")
    threads = base.thread_contract()
    if toy:
        train, evaluation, metadata, declarations = toy_preparation()
        predictor_report = {"tapes": 0, "examples": 0, "updates": 0, "processed_examples": 0}
        endpoints, batch_size = (3, 6, 9), 4
    else:
        tapes = tuple(t for regime, first in (("K4", 0), ("K8", 64))
                      for t in base.build_balanced_tapes(replicate=0, split=base.Split.PREDICTOR_FIT,
                          regime=regime, count=64, first_episode_index=first, rng_namespace=base.LEARNER_NAMESPACE))
        examples = base._predictor_examples(tapes, monitor=monitor)
        predictor, audit = base.fit_fresh_predictor(examples, replicate=seed, updates=100,
            batch_size=128, rng_namespace=base.LEARNER_NAMESPACE, resource_monitor=monitor)
        train, evaluation, metadata = base._selected_rows(predictor, monitor=monitor)
        predictor_report = {"tapes": len(tapes), "examples": audit.examples, "updates": audit.updates,
                            "processed_examples": audit.processed_examples, "rng_namespace": base.LEARNER_NAMESPACE}
        endpoints, batch_size, declarations = ENDPOINTS, 32, base.SELECTED_ROWS
    orders, sequences = training_orders(train, base._raw_dataset(train), metadata, declarations)
    evaluation_packets = base._raw_dataset(evaluation)
    snapshots, exposures, initial_scales, training_wall = {}, {}, {}, {}
    for arm in ARMS:
        rows, packets = orders[arm]
        packets.require_rows(rows)
        snapshots[arm], exposures[arm], training_wall[arm], initial_scales[arm] = raw.train_raw(
            rows, packets, seed=seed, final_update=endpoints[-1], trace_updates=endpoints,
            batch_size=batch_size, started=started)
    forward_started = time.perf_counter()
    predictions = {arm: raw.forward_snapshots(snapshots[arm], evaluation, evaluation_packets, monitor)
                   for arm in ARMS}
    forward_wall = time.perf_counter() - forward_started
    readout_started = time.perf_counter()
    comparison = comparison_summary(raw.panel_labels(evaluation, metadata), predictions, exposures,
                                    orders, batch_size, endpoints)
    readout_wall = time.perf_counter() - readout_started
    counts = {"predictor_tapes": predictor_report["tapes"], "predictor_examples": predictor_report["examples"],
              "predictor_updates": predictor_report["updates"], "predictor_processed_examples": predictor_report["processed_examples"],
              "environment_transitions": 0 if toy else 128 * 256 + sum(r.key.primitive_time for r in (*train, *evaluation)),
              "common_future_branch_steps": 0 if toy else sum(int(np.count_nonzero(r.legal_mask)) * 16 for r in (*train, *evaluation)),
              "raw_gate_updates": 2 * endpoints[-1], "raw_processed_examples": 2 * endpoints[-1] * batch_size,
              "network_forward_rows": 2 * len(endpoints) * len(evaluation),
              "scored_decisions": 2 * len(endpoints) * len(evaluation), "unique_eval_rows": len(evaluation),
              "true_residual_gate_updates": 0, "true_residual_evaluation_rows": 0,
              "calibrated_derangement_gate_updates": 0, "calibrated_derangement_evaluation_rows": 0}
    peak = base._peak_rss_bytes()
    summary = {"object_id": OBJECT_ID, "seed": seed, "toy": toy, **comparison,
               "launch_sha": base.current_launch_sha(), "exact_argv": list(argv), "execution_node": execution_node,
               "result_root": str(Path(output_dir).resolve()), "thread_contract": threads,
               "train_orders": sequences, "initial_parameter_scales": initial_scales,
               "predictor": predictor_report, "source_namespace": base.SOURCE_NAMESPACE,
               "information_boundary": base.information_boundary_report(), "work_counts": counts,
               "cost_law": {**cost, "measured_training_seconds_by_arm": training_wall,
                            "measured_seconds_per_update_by_arm": {a: t / endpoints[-1] for a, t in training_wall.items()},
                            "measured_forward_seconds": forward_wall,
                            "measured_seconds_per_snapshot": forward_wall / (2 * len(endpoints)),
                            "measured_readout_seconds": readout_wall},
               "resources": {"wall_seconds": time.perf_counter() - started, "peak_rss_bytes": peak,
                             "status": "measured" if peak is not None else "resources_unmeasured"}}
    if toy:
        summary["result_branch"] = None
        summary["engineering_only"] = "TOY_SMOKE_NOT_A_SCIENTIFIC_POPULATION"
    monitor()
    raw.publish_summary(output_dir, summary)
    monitor()
    return summary
