"""B04 preserves B01 preparation and arithmetic with new snapshots and wall bounds."""

from __future__ import annotations

import time

from experiments.candidates.commitment_residual_triggered_options.raw_cycle_readout_b02 import experiment as raw
from experiments.candidates.commitment_residual_triggered_options.balanced_residual_b01_r1 import experiment as b01

base, np, torch = raw.base, raw.np, raw.torch
OBJECT_ID = "CRTO-RESIDUAL-CYCLE-ENDPOINTS-B04"
ARMS = tuple(rep.value for rep in b01.Representation)
ENDPOINTS = {"SHORT": 33, "LONG": 258}
ARM_CAP, SHARED_CAP = 1200.0, 1500.0


def project_cost(seed=0):
    stages = dict(zip(ARMS, (42.2828106, 62.5834969, 33.7267008)))
    shared_preparation = 434.7066687 - sum(stages.values())
    arms = {arm: 3 * (shared_preparation + stage * 258 / 256) for arm, stage in stages.items()}
    shared = 3 * (shared_preparation + sum(stages.values()) * 258 / 256)
    return {"object_id": OBJECT_ID, "result_bearing": False, "measured_source": "accepted B01 Windows stages",
            "law": "arm_j=3*(S+stage_j*258/256); shared=3*(S+sum(stages)*258/256)",
            "stage_seconds": stages, "shared_preparation_seconds": shared_preparation,
            "projected_arm_seconds": arms, "projected_shared_seconds": shared,
            "arm_cap_seconds": ARM_CAP, "shared_cap_seconds": SHARED_CAP,
            "projection_within_cap": max(arms.values()) <= ARM_CAP and shared <= SHARED_CAP,
            "prospective_work_counts": {"predictor_tapes": 128, "predictor_updates": 100,
                "predictor_processed_examples": 12800, "calibration_tapes": 64,
                "calibration_examples_expected": 16128, "gate_updates": 774,
                "processed_examples": 24768, "network_forward_rows": 96, "scored_decisions": 96},
            "planning_exposure": [{"representation": arm, "update": update,
                "processed_examples": 32 * update, "recipient_and_donor_occurrences": 32 * update // 48,
                "adam_lr": .001, "nominal_lr_exposure": .001 * update, **base.INITIAL_ANCHOR,
                "prior_B01_long_displacement_l2_over_initial_l2": prior}
                for arm, prior in zip(ARMS, (.1359536930, .1007137230, .1080224632))
                for update in ENDPOINTS.values()]}


def check_wall(started, arm_seconds=0.0):
    if time.perf_counter() - started > SHARED_CAP:
        raise TimeoutError("B04 exceeded its 1500-second shared cap")
    if arm_seconds > ARM_CAP:
        raise TimeoutError("B04 exceeded its 1200-second training-plus-evaluation cap")


# B02 arithmetic; only arm timing, LONG movement acceptance, and representation labels differ.
def train_path(rows: tuple[base.PanelRow, ...], packets: base.PacketDataset, *, seed: int,
           final_update: int, trace_updates: base.Sequence[int], batch_size: int,
           started: float, representation: str) -> tuple[
               dict[int, base.CommonHistoryGate], list[dict[str, object]], float, dict[str, float]]:
    arm_started = time.perf_counter()
    order = np.resize(np.arange(len(rows), dtype=np.int64), final_update * batch_size)
    model = base.CommonHistoryGate(base.counter_rng_for_namespace(
        base.LEARNER_NAMESPACE, "gate_initialization", seed,
    ))
    initial = base._parameter_tensors(model)
    scales = base._parameter_scales(initial)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=base.ADAM_LR, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0,
    )
    snapshots: dict[int, base.CommonHistoryGate] = {}
    exposures = []
    for update in range(1, final_update + 1):
        check_wall(started, time.perf_counter() - arm_started)
        begin = (update - 1) * batch_size
        histories, lengths, packet, legal, target = base._collate(
            rows, packets.values, order[begin:begin + batch_size],
        )
        prediction = model(histories, lengths, packet)
        loss = base.legal_masked_mse(prediction, target, legal)
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("RAW gate loss became nonfinite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if any(parameter.grad is not None and not bool(torch.all(torch.isfinite(parameter.grad)))
               for parameter in model.parameters()):
            raise RuntimeError("RAW gate gradient became nonfinite")
        torch.nn.utils.clip_grad_norm_(model.parameters(), base.GRADIENT_CLIP)
        optimizer.step()
        if any(not bool(torch.all(torch.isfinite(parameter))) for parameter in model.parameters()):
            raise RuntimeError("RAW gate parameter became nonfinite")
        if update in trace_updates:
            snapshot = base.deepcopy(model).eval()
            snapshots[update] = snapshot
            movement = base._movement(initial, snapshot)
            if (not all(base.math.isfinite(value) for value in movement.values())
                    or (update == final_update and any(value <= 0.0 for value in movement.values()))):
                raise RuntimeError("RAW gate movement is zero or nonfinite")
            exposures.append(base._exposure_line(
                update, scales, movement, batch_size=batch_size, row_count=len(rows),
            ))
    for line in exposures:
        line["representation"] = representation
    check_wall(started, time.perf_counter() - arm_started)
    return snapshots, exposures, time.perf_counter() - arm_started, scales


def prepare(seed, monitor, toy):
    if toy:
        train, evaluation, calibration, metadata = b01._toy_population()
        return train, evaluation, calibration, metadata, {
            "tapes": 0, "examples": 0, "updates": 0, "processed_examples": 0}, {
            "tapes": 0, "example_count": 16, "engineering_only": "synthetic calibration support"}
    tapes = tuple(t for regime, first in (("K4", 0), ("K8", 64))
                  for t in b01.build_balanced_tapes(replicate=0, split=b01.Split.PREDICTOR_FIT,
                      regime=regime, count=64, first_episode_index=first, rng_namespace=b01.LEARNER_NAMESPACE))
    examples = b01._predictor_examples(tapes, monitor=monitor)
    predictor, audit = b01.fit_fresh_predictor(examples, replicate=seed, updates=100, batch_size=128,
        rng_namespace=b01.LEARNER_NAMESPACE, resource_monitor=monitor)
    calibration_tapes = tuple(t for regime in ("K4", "K8") for t in b01.canonical_calibration_tapes(
        replicate=0, regime=regime, rng_namespace=b01.LEARNER_NAMESPACE))
    calibration_examples = b01._predictor_examples(calibration_tapes, monitor=monitor)
    def forecast(*args):
        monitor()
        return predictor.packet_forecast(*args)
    calibration, report = b01.fit_calibration_from_examples(calibration_examples, forecast)
    report = {k: v for k, v in report.items() if k != "table_record"}
    report["tapes"] = len(calibration_tapes)
    train, evaluation, metadata = b01._selected_rows(predictor, monitor=monitor)
    return train, evaluation, calibration, metadata, {
        "tapes": len(tapes), "examples": audit.examples, "updates": audit.updates,
        "processed_examples": audit.processed_examples, "rng_namespace": b01.LEARNER_NAMESPACE}, report


def packet_sets(train, evaluation, calibration, seed):
    packets, maps = {}, {}
    for ordinal, (split, rows) in enumerate((("TRAIN", train), ("EVALUATION", evaluation))):
        views = b01.construct_packet_views(rows, calibration)
        deranged, mapping = b01.derange_packets(rows, views.true_residual_dataset, seed=seed, split_ordinal=ordinal)
        packets[split] = dict(zip(ARMS, (views.raw_dataset, views.true_residual_dataset, deranged)))
        maps[split] = mapping
    return packets, maps


def exposure_counts(train, donor_map, endpoints, batch_size):
    result = {}
    donor_by_recipient = {m["recipient"]: m["donor"] for m in donor_map}
    for budget, update in endpoints.items():
        order = np.resize(np.arange(len(train)), update * batch_size)
        counts = np.bincount(order, minlength=len(train))
        recipients = {row.key.text: int(n) for row, n in zip(train, counts)}
        donors = {row.key.text: 0 for row in train}
        for recipient, count in recipients.items():
            donors[donor_by_recipient[recipient]] += count
        result[budget] = {"update": update, "recipient_counts_all_arms": recipients,
                          "calibrated_derangement_donor_counts": donors}
    return result


def score_summary(labels, predictions, exposures, endpoints, monitor=lambda arm, seconds: None):
    metrics, scoring_times = {}, {}
    for arm in ARMS:
        scoring_started = time.perf_counter()
        lines = {line["update"]: line for line in exposures[arm]}
        metrics[arm] = {}
        for budget, update in endpoints.items():
            values = predictions[arm][update]
            if values.shape != (len(labels), 8) or values.dtype != np.float32:
                raise ValueError("each snapshot requires one FP32 prediction vector per row")
            metrics[arm][budget] = {**raw.score_readout(labels, values), "exposure": lines[update]}
        scoring_times[arm] = time.perf_counter() - scoring_started
        monitor(arm, scoring_times[arm])
    return {"representations": metrics, "contrasts": b01._contrasts(metrics),
            "result_branch": b01.apply_result_rule(metrics), "scoring_seconds_by_arm": scoring_times}


def run_experiment(output_dir, *, argv, execution_node, seed=0, toy=False):
    started = time.perf_counter()
    train, evaluation, calibration, metadata, predictor_report, calibration_report = prepare(seed, lambda: check_wall(started), toy)
    packets, donor_maps = packet_sets(train, evaluation, calibration, seed)
    endpoints, batch_size = ({"SHORT": 3, "LONG": 6}, 4) if toy else (ENDPOINTS, 32)
    snapshots, exposures, training_wall, scales = {}, {}, {}, {}
    preparation_wall = time.perf_counter() - started
    for arm in ARMS:
        packets["TRAIN"][arm].require_rows(train)
        snapshots[arm], exposures[arm], training_wall[arm], scales[arm] = train_path(
            train, packets["TRAIN"][arm], seed=seed, final_update=endpoints["LONG"],
            trace_updates=tuple(endpoints.values()), batch_size=batch_size, started=started, representation=arm)
    predictions, evaluation_wall = {}, {}
    for arm in ARMS:
        evaluation_started = time.perf_counter()
        arm_monitor = lambda: check_wall(started, training_wall[arm] + time.perf_counter() - evaluation_started)
        packets["EVALUATION"][arm].require_rows(evaluation)
        predictions[arm] = raw.forward_snapshots(snapshots[arm], evaluation, packets["EVALUATION"][arm], arm_monitor)
        evaluation_wall[arm] = time.perf_counter() - evaluation_started
        arm_monitor()
    summary = score_summary(raw.panel_labels(evaluation, metadata), predictions, exposures, endpoints,
        monitor=lambda arm, seconds: check_wall(started, training_wall[arm] + evaluation_wall[arm] + seconds))
    peak = base._peak_rss_bytes()
    summary.update({"object_id": OBJECT_ID, "seed": seed, "toy": toy,
        "launch_sha": base.current_launch_sha(), "exact_argv": list(argv), "execution_node": execution_node,
        "thread_contract": base.thread_contract(),
        "source_namespace": b01.SOURCE_NAMESPACE, "initial_parameter_scales": scales,
        "training_order": [{"row_key": r.key.text, "address": metadata[r.key.text]} for r in train],
        "derangement_donor_maps": donor_maps, "endpoint_occurrences": exposure_counts(train, donor_maps["TRAIN"], endpoints, batch_size),
        "predictor": predictor_report, "calibration": calibration_report,
        "work_counts": {"gate_updates": 3 * endpoints["LONG"], "processed_examples": 3 * endpoints["LONG"] * batch_size,
            "network_forward_rows": 6 * len(evaluation), "scored_decisions": 6 * len(evaluation), "unique_eval_rows": len(evaluation),
            "environment_transitions": 0 if toy else 192 * 256 + sum(r.key.primitive_time for r in (*train, *evaluation)),
            "common_future_branch_steps": 0 if toy else sum(int(np.count_nonzero(r.legal_mask)) * 16 for r in (*train, *evaluation))},
        "cost_law": {**project_cost(seed), "measured_preparation_seconds": preparation_wall,
            "measured_training_seconds_by_arm": training_wall, "measured_forward_seconds_by_arm": evaluation_wall,
            "measured_seconds_per_update_by_arm": {a: t / endpoints["LONG"] for a, t in training_wall.items()},
            "measured_scoring_seconds": sum(summary["scoring_seconds_by_arm"].values())},
        "resources": {"wall_seconds": time.perf_counter() - started, "peak_rss_bytes": peak,
                      "status": "measured" if peak is not None else "resources_unmeasured"}})
    if toy:
        summary["result_branch"] = None
        summary["engineering_only"] = "TOY_SMOKE_NOT_A_SCIENTIFIC_POPULATION"
    raw.publish_summary(output_dir, summary)
    check_wall(started)
    return summary
