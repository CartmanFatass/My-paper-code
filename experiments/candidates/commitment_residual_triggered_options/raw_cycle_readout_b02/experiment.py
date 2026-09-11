"""One RAW trajectory, endpoint and three-snapshot score means (B02)."""

from __future__ import annotations

import json
from pathlib import Path
import time

from experiments.candidates.commitment_residual_triggered_options.raw_phase_trace_a01 import experiment as base

np, torch = base.np, base.torch
OBJECT_ID = "CRTO-RAW-CYCLE-READOUT-B02"
SNAPSHOTS = tuple(range(253, 258))
ENDINGS = (255, 256, 257)
CAP_SECONDS = 600.0
DELTA = 0.0025


def project_cost(seed=0):
    if seed != 0:
        raise ValueError("B02 has fixed seed 0")
    fixed = 80.505860614001 - 14.019378483993933 - 0.05376777199853677
    per_update = 14.019378483993933 / 264
    per_snapshot = 0.05376777199853677 / 13
    projected = 3 * (fixed + 257 * per_update + 5 * per_snapshot)
    return {
        "object_id": OBJECT_ID, "result_bearing": False,
        "law": "3 * (base + U * seconds_per_update + S * seconds_per_snapshot)",
        "measured_source": "A02 RAW stages; planning multiplier 3",
        "base_seconds": fixed, "seconds_per_update": per_update,
        "seconds_per_snapshot": per_snapshot, "U": 257, "S": 5,
        "projected_arm_seconds": projected, "invocation_cap_seconds": CAP_SECONDS,
        "projection_within_cap": projected <= CAP_SECONDS,
        "shared_invocations": 1, "machine_time_charged_once": True,
        "prospective_work_counts": {
            "predictor_tapes": 128, "predictor_updates": 100,
            "predictor_processed_examples": 12800, "raw_gate_updates": 257,
            "raw_processed_examples": 8224, "network_forward_rows": 80,
            "scored_decisions": 96, "unique_eval_rows": 16,
        },
        "prior_measured_exposure": base._exposure_line(257, base.INITIAL_ANCHOR, {
            "parameter_displacement_l2_over_initial_l2": 0.136428218836,
            "parameter_displacement_linf_over_initial_linf": 0.913744698074,
        }),
    }


def check_wall(started):
    if time.perf_counter() - started > CAP_SECONDS:
        raise TimeoutError("B02 invocation exceeded its 600-second wall cap")


# A01 numerical loop copied verbatim except qualified helpers and B02 wall monitor.
def train_raw(rows: tuple[base.PanelRow, ...], packets: base.PacketDataset, *, seed: int,
           final_update: int, trace_updates: base.Sequence[int], batch_size: int,
           started: float) -> tuple[
               dict[int, base.CommonHistoryGate], list[dict[str, object]], float, dict[str, float]]:
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
    training_started = time.perf_counter()
    for update in range(1, final_update + 1):
        check_wall(started)
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
            if not all(base.math.isfinite(value) and value > 0.0 for value in movement.values()):
                raise RuntimeError("RAW gate movement is zero or nonfinite")
            exposures.append(base._exposure_line(
                update, scales, movement, batch_size=batch_size, row_count=len(rows),
            ))
    return snapshots, exposures, time.perf_counter() - training_started, scales


def cycle_mean(predictions, ending):
    """Explicit left-associated FP64 sum in ascending update order."""
    first, second, third = (np.asarray(predictions[u], dtype=np.float64)
                            for u in range(ending - 2, ending + 1))
    return ((first + second) + third) / 3.0


def panel_labels(rows, metadata):
    return [{"row_key": row.key.text, "material_side": metadata[row.key.text]["side"],
             "legal_mask": row.legal_mask.tolist(),
             "g16": [float(v) if legal else None for v, legal in zip(row.g16, row.legal_mask)]}
            for row in rows]


def legal_vector(values, mask):
    return {base.ACTION_ORDER[i]: float(values[i]) for i in np.flatnonzero(mask)}


def score_readout(labels, predictions):
    details = []
    for row, values in zip(labels, predictions):
        legal = np.asarray(row["legal_mask"], dtype=bool)
        native = np.asarray(row["g16"], dtype=np.float64)
        selected = base.select_printed_action(values, legal)
        oracle = base.select_printed_action(native, legal)
        regret = base.native_regret(native, legal, selected)
        if not np.isfinite(regret) or regret < 0:
            raise ValueError("native regret must be finite nonnegative")
        details.append({**row, "legal_action_order": [base.ACTION_ORDER[i] for i in np.flatnonzero(legal)],
                        "legal_g16": legal_vector(native, legal),
                        "legal_prediction": legal_vector(values, legal),
                        "selected_action": base.ACTION_ORDER[selected], "selected_action_index": selected,
                        "oracle_action": base.ACTION_ORDER[oracle], "oracle_action_index": oracle,
                        "selected_g16": float(native[selected]), "oracle_g16": float(native[oracle]),
                        "native_regret": regret, "exact_action_correct": selected == oracle})
    sides = {}
    for side in ("KEEP", "REPLAN"):
        members = [r for r in details if r["material_side"] == side]
        sides[side] = {"row_count": len(members),
                       "exact_action_count": sum(r["exact_action_correct"] for r in members),
                       "mean_regret": float(np.mean([r["native_regret"] for r in members]))}
    return {"rows": details, "sides": sides,
            "equal_side_regret": sum(s["mean_regret"] for s in sides.values()) / 2,
            "competent": all(s["row_count"] == 8 and s["exact_action_count"] >= 6
                             and s["mean_regret"] <= 0.005 for s in sides.values())}


def apply_result_rule(differences, cycle_competent, endpoint_competent):
    if not all(np.isfinite(d) for d in differences):
        raise ValueError("nonfinite paired difference has no scientific branch")
    if any(d < -DELTA for d in differences):
        return "B02-MATERIAL-REGRET-LOSS"
    if cycle_competent and not endpoint_competent:
        return "B02-CYCLE-COMPETENCE-STABILIZED"
    if cycle_competent and endpoint_competent:
        return "B02-BOTH-READOUTS-COMPETENT"
    return "B02-CYCLE-COMPETENCE-NOT-STABILIZED"


def readout_summary(labels, predictions, exposures, endings=ENDINGS):
    """The same publication computation serves formal execution and offline fixtures."""
    exposure_by_update = {line["update"]: line for line in exposures}
    snapshots = {}
    for update, values in predictions.items():
        if values.shape != (len(labels), 8) or values.dtype != np.float32:
            raise ValueError("snapshot forward must provide one FP32 vector per row")
        for row, vector in zip(labels, values):
            if not np.all(np.isfinite(vector[np.asarray(row["legal_mask"], dtype=bool)])):
                raise ValueError("snapshot legal predictions must be finite")
        snapshots[str(update)] = {
            "exposure": exposure_by_update[update],
            "rows": [{"row_key": r["row_key"], "legal_prediction": legal_vector(v, r["legal_mask"])}
                     for r, v in zip(labels, values)],
        }
    paired = {}
    for update in endings:
        endpoint = score_readout(labels, predictions[update])
        cycle = score_readout(labels, cycle_mean(predictions, update))
        paired[str(update)] = {
            "exposure": exposure_by_update[update], "window_updates": list(range(update - 2, update + 1)),
            "ENDPOINT": endpoint, "CYCLE": cycle,
            "D": endpoint["equal_side_regret"] - cycle["equal_side_regret"],
        }
    differences = [p["D"] for p in paired.values()]
    cycle_all = all(p["CYCLE"]["competent"] for p in paired.values())
    endpoint_all = all(p["ENDPOINT"]["competent"] for p in paired.values())
    mean = float(np.mean(differences))
    return {"snapshots": snapshots, "endings": paired,
            "aggregate": {"S_CYCLE": cycle_all, "S_ENDPOINT": endpoint_all, "D_bar": mean,
                          "D_bar_vs_MEI": "above" if mean > DELTA else "below" if mean < -DELTA else "inside"},
            "result_branch": apply_result_rule(differences, cycle_all, endpoint_all)}


def publish_summary(output, summary):
    Path(output).mkdir(parents=True, exist_ok=True)
    (Path(output) / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def forward_snapshots(snapshots, rows, packets, monitor):
    histories, lengths, packet, _, _ = base._collate(rows, packets.values, np.arange(len(rows)))
    predictions = {}
    for update, model in snapshots.items():
        monitor()
        with torch.no_grad():
            predictions[update] = model(histories, lengths, packet).cpu().numpy()
    return predictions


def run_experiment(output_dir, *, argv, execution_node, seed=0, toy=False):
    started = time.perf_counter()
    monitor = lambda: check_wall(started)
    cost = project_cost(seed)
    if not cost["projection_within_cap"]:
        raise ValueError("B02 projection exceeds cap")
    threads = base.thread_contract()
    if toy:
        train_rows, eval_rows, metadata = base._toy_population()
        predictor_report = {"tapes": 0, "examples": 0, "updates": 0, "processed_examples": 0}
        final_update, batch_size, trace_updates, endings = 5, 4, (1, 2, 3, 4, 5), (3, 4, 5)
    else:
        tapes = tuple(tape for regime, first in (("K4", 0), ("K8", 64))
                      for tape in base.build_balanced_tapes(
                          replicate=0, split=base.Split.PREDICTOR_FIT, regime=regime, count=64,
                          first_episode_index=first, rng_namespace=base.LEARNER_NAMESPACE))
        examples = base._predictor_examples(tapes, monitor=monitor)
        predictor, audit = base.fit_fresh_predictor(
            examples, replicate=seed, updates=100, batch_size=128,
            rng_namespace=base.LEARNER_NAMESPACE, resource_monitor=monitor)
        train_rows, eval_rows, metadata = base._selected_rows(predictor, monitor=monitor)
        predictor_report = {"rng_namespace": base.LEARNER_NAMESPACE, "tapes": len(tapes),
                            "examples": audit.examples, "updates": audit.updates,
                            "batch_size": 128, "processed_examples": audit.processed_examples}
        final_update, batch_size, trace_updates, endings = 257, 32, SNAPSHOTS, ENDINGS
    train_packets, eval_packets = base._raw_dataset(train_rows), base._raw_dataset(eval_rows)
    snapshots, exposures, training_wall, scales = train_raw(
        train_rows, train_packets, seed=seed, final_update=final_update,
        trace_updates=trace_updates, batch_size=batch_size, started=started)
    evaluation_started = time.perf_counter()
    predictions = forward_snapshots(snapshots, eval_rows, eval_packets, monitor)
    forward_wall = time.perf_counter() - evaluation_started
    readout_started = time.perf_counter()
    comparison = readout_summary(panel_labels(eval_rows, metadata), predictions, exposures, endings)
    readout_wall = time.perf_counter() - readout_started
    counts = {"predictor_tapes": predictor_report["tapes"], "predictor_examples": predictor_report["examples"],
              "predictor_updates": predictor_report["updates"],
              "predictor_processed_examples": predictor_report["processed_examples"],
              "environment_transitions": 0 if toy else 128 * 256 + sum(
                  row.key.primitive_time for row in (*train_rows, *eval_rows)),
              "common_future_branch_steps": 0 if toy else sum(
                  int(np.count_nonzero(row.legal_mask)) * 16 for row in (*train_rows, *eval_rows)),
              "raw_gate_updates": final_update, "raw_processed_examples": final_update * batch_size,
              "snapshot_count": len(snapshots), "network_forward_rows": len(snapshots) * len(eval_rows),
              "scored_decisions": 2 * len(endings) * len(eval_rows), "unique_eval_rows": len(eval_rows),
              "true_residual_gate_updates": 0, "true_residual_evaluation_rows": 0,
              "calibrated_derangement_gate_updates": 0, "calibrated_derangement_evaluation_rows": 0}
    peak = base._peak_rss_bytes()
    summary = {"object_id": OBJECT_ID, "seed": seed, "toy": toy, **comparison,
               "launch_sha": base.current_launch_sha(), "exact_argv": list(argv),
               "execution_node": execution_node, "result_root": str(Path(output_dir).resolve()),
               "thread_contract": threads, "action_order": list(base.ACTION_ORDER),
               "initial_parameter_scales": scales, "predictor": predictor_report,
               "source_namespace": base.SOURCE_NAMESPACE,
               "selected_population": {"train_rows": len(train_rows), "evaluation_rows": len(eval_rows),
                                       "reproduction": [metadata[r.key.text] for r in (*train_rows, *eval_rows)]},
               "information_boundary": base.information_boundary_report(), "work_counts": counts,
               "historical_checks_descriptive_only": {
                   "initialization": base._anchor_from_scales(scales),
                   "update_256_matches": None if toy else base.update_256_anchor_matches(
                       comparison["endings"]["256"]["ENDPOINT"])},
               "cost_law": {**cost, "measured_raw_training_wall_seconds": training_wall,
                            "measured_seconds_per_update": training_wall / final_update,
                            "measured_forward_wall_seconds": forward_wall,
                            "measured_seconds_per_snapshot": forward_wall / len(snapshots),
                            "measured_readout_wall_seconds": readout_wall},
               "resources": {"peak_rss_bytes": peak, "wall_seconds": time.perf_counter() - started,
                             "status": "measured" if peak is not None else "resources_unmeasured"}}
    if toy:
        summary["result_branch"] = None
        summary["engineering_only"] = "TOY_SMOKE_NOT_A_SCIENTIFIC_POPULATION"
    monitor()
    publish_summary(output_dir, summary)
    monitor()
    return summary
