"""B08: one expected native-cost objective, three representations, two endpoints."""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import time

from experiments.candidates.commitment_residual_triggered_options.residual_cycle_endpoints_b04 import experiment as b04

raw, b01, base, np, torch = b04.raw, b04.b01, b04.base, b04.np, b04.torch
OBJECT_ID = "CRTO-NATIVE-COST-B08"
ARMS, ENDPOINTS = b04.ARMS, b04.ENDPOINTS
RAW, TRUE, DERANGED = ARMS
ARM_CAP, SHARED_CAP = 1200.0, 1500.0
MEI = .0025
HISTORICAL_INPUT_COMMIT = "c9690db8ef340ac8201043183a864454f08c0431"
HISTORICAL_LAUNCH_SHA = "c53f3bb19c91d01ef87cb2c4b9737811eb10d795"


def expected_native_cost_loss(logits, target, legal):
    """Equal row weights; illegal actions have zero probability and gradient."""
    labels = target.detach()
    best = labels.masked_fill(~legal, -torch.inf).amax(dim=-1, keepdim=True)
    costs = torch.where(legal, (best - labels) / .01, 0.0)
    probability = torch.softmax(logits.masked_fill(~legal, -torch.inf), dim=-1)
    return (probability * costs).sum(dim=-1).mean()


def project_cost():
    preparation, scoring = 120.60043037099967, .00270985699899029
    per_update = dict(zip(ARMS, (.06733760550387935, .06475017771316384, .06617708206977113)))
    forward = dict(zip(ARMS, (.014060344998142682, .011793982004746795, .012702049003564753)))
    arm_work = {a: 258 * per_update[a] + forward[a] for a in ARMS}
    return {"result_bearing": False, "measured_source": "B04 stages, P68 arithmetic",
        "arm_law": "3*(S+258*t_j+E_j+Q)", "shared_law": "3*(S+sum_j(258*t_j+E_j)+Q)",
        "S": preparation, "t": per_update, "E": forward, "Q": scoring,
        "projected_arm_seconds": {a: 3*(preparation+arm_work[a]+scoring) for a in ARMS},
        "projected_shared_seconds": 3*(preparation+sum(arm_work.values())+scoring),
        "arm_cap_seconds": ARM_CAP, "shared_cap_seconds": SHARED_CAP,
        "unmeasured": ["new loss overhead", "setup/check/publication overhead", "current node load"],
        "gate_updates": 774, "gate_processed_examples": 24768,
        "predictor_updates": 100, "predictor_processed_examples": 12800,
        "evaluation_decisions": 96, "unique_eval_identities": 16}


def complete_accounting(complete_seconds, arm_seconds):
    """Outer command elapsed includes imports, preparation and output publication.

    Per-arm charges are conservative counterfactual costs, never summed as machine time.
    """
    shared = complete_seconds - sum(arm_seconds.values())
    charges = {a: shared + arm_seconds[a] for a in ARMS}
    return {"complete_shared_wall_seconds": complete_seconds, "shared_overhead_seconds": shared,
        "arm_training_evaluation_scoring_seconds": dict(arm_seconds),
        "charged_seconds_by_arm": charges,
        "arm_cap_breaches": [a for a in ARMS if charges[a] > ARM_CAP],
        "shared_cap_breached": complete_seconds > SHARED_CAP,
        "study_elapsed_critical_path_seconds": complete_seconds,
        "summed_invocation_wall_seconds": complete_seconds,
        "aggregate_cpu_seconds": None,
        "aggregate_cpu_status": "unmeasured; wall is not CPU work"}


class WallBudget:
    """Existing elapsed-wall pattern, charging all common time to every arm."""
    def __init__(self, started):
        self.started = started
        self.arm_seconds = dict.fromkeys(ARMS, 0.0)
        self.active = None
        self.phase_started = None

    def check(self):
        now = time.perf_counter()
        measured = dict(self.arm_seconds)
        if self.active is not None:
            measured[self.active] += now - self.phase_started
        accounting = complete_accounting(now - self.started, measured)
        if accounting["shared_cap_breached"] or accounting["arm_cap_breaches"]:
            raise TimeoutError("B08 accrued complete-wall budget exceeded: " + json.dumps(accounting))

    @contextmanager
    def arm(self, name):
        self.check()
        self.active, self.phase_started = name, time.perf_counter()
        try:
            yield
        finally:
            self.arm_seconds[name] += time.perf_counter() - self.phase_started
            self.active, self.phase_started = None, None
        self.check()


# B04 initialization, cyclic batches, Adam, clipping and in-memory snapshots preserved.
def train_path(rows: tuple[base.PanelRow, ...], packets: base.PacketDataset, *, seed: int,
           final_update: int, trace_updates: base.Sequence[int], batch_size: int,
           monitor, representation: str) -> tuple[
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
        monitor()
        begin = (update - 1) * batch_size
        histories, lengths, packet, legal, target = base._collate(
            rows, packets.values, order[begin:begin + batch_size],
        )
        prediction = model(histories, lengths, packet)
        loss = expected_native_cost_loss(prediction, target, legal)
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("B08 gate loss became nonfinite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if any(parameter.grad is not None and not bool(torch.all(torch.isfinite(parameter.grad)))
               for parameter in model.parameters()):
            raise RuntimeError("B08 gate gradient became nonfinite")
        torch.nn.utils.clip_grad_norm_(model.parameters(), base.GRADIENT_CLIP)
        optimizer.step()
        if any(not bool(torch.all(torch.isfinite(parameter))) for parameter in model.parameters()):
            raise RuntimeError("B08 gate parameter became nonfinite")
        if update in trace_updates:
            snapshot = base.deepcopy(model).eval()
            snapshots[update] = snapshot
            movement = base._movement(initial, snapshot)
            if (not all(base.math.isfinite(value) for value in movement.values())
                    or (update == final_update and any(value <= 0.0 for value in movement.values()))):
                raise RuntimeError("B08 gate movement is zero or nonfinite")
            exposures.append(base._exposure_line(
                update, scales, movement, batch_size=batch_size, row_count=len(rows),
            ))
            exposures[-1]["last_batch_expected_native_cost_loss"] = float(loss.detach())
    for line in exposures:
        line["representation"] = representation
    monitor()
    return snapshots, exposures, time.perf_counter() - arm_started, scales



def paired_contrast(reference, treatment):
    """Preserve all signed native gains, including actions that got worse."""
    before = {r["row_key"]: r for r in reference["rows"]}
    if (len(before) != 16 or len(treatment["rows"]) != 16
            or set(before) != {r["row_key"] for r in treatment["rows"]}):
        raise ValueError("primary contrast needs the same 16 distinct EVAL identities")
    rows = []
    for after in treatment["rows"]:
        prior = before[after["row_key"]]
        if prior["material_side"] != after["material_side"] or prior["legal_mask"] != after["legal_mask"]:
            raise ValueError("primary comparison side or legal support differs")
        legal = np.asarray(after["legal_mask"], dtype=bool)
        old_labels = np.asarray(prior["g16"], dtype=np.float64)
        new_labels = np.asarray(after["g16"], dtype=np.float64)
        old_action, new_action = prior["selected_action_index"], after["selected_action_index"]
        rows.append({"row_key": after["row_key"], "material_side": after["material_side"],
            "reference_action_index": old_action, "true_action_index": new_action,
            "reference_selected_g16": prior["selected_g16"], "true_selected_g16": after["selected_g16"],
            "signed_native_gain": after["selected_g16"] - prior["selected_g16"],
            "same_new_labels_signed_gain": float(new_labels[new_action] - new_labels[old_action]),
            "max_abs_native_label_difference": float(np.max(np.abs(new_labels[legal]-old_labels[legal])))})
    delta = reference["equal_side_regret"] - treatment["equal_side_regret"]
    paired = float(np.mean([r["signed_native_gain"] for r in rows]))
    rescored = float(np.mean([r["same_new_labels_signed_gain"] for r in rows]))
    max_difference = max(r["max_abs_native_label_difference"] for r in rows)
    # Native labels are FP64. This tolerance is far below the .01 action / .0025 mean scale;
    # even a smaller discrepancy cannot be ignored if it changes a reported margin/sign.
    boundaries = (-MEI, -.000625, 0., .000625, MEI)
    same_reading = all((delta > b) == (paired > b) == (rescored > b)
                       and (delta < b) == (paired < b) == (rescored < b) for b in boundaries)
    return {"delta_regret": delta, "paired_native_gain_mean": paired,
        "paired_native_gain_sum": sum(r["signed_native_gain"] for r in rows),
        "new_label_rescored_gain_mean": rescored,
        "max_abs_native_label_difference": max_difference,
        "comparison_trustworthy": max_difference <= 1e-7 and (max_difference == 0.0 or same_reading),
        "native_label_tolerance": 1e-7,
        "rows": rows, "gain_rows": sum(r["signed_native_gain"] > 0 for r in rows),
        "loss_rows": sum(r["signed_native_gain"] < 0 for r in rows)}


def result_reading(contrasts, raw_long_competent):
    trustworthy = {b: all(c["comparison_trustworthy"] for c in point.values())
                   for b, point in contrasts.items()}
    complete = all(trustworthy.values())
    signals = {b: (raw_long_competent and all(c["delta_regret"] > MEI for c in point.values()))
               if trustworthy[b] and raw_long_competent is not None else None for b, point in contrasts.items()}
    losses = [{"endpoint": b, "reference": name, "delta": c["delta_regret"],
               "material": c["delta_regret"] < -MEI}
              for b, point in contrasts.items() for name, c in point.items() if c["delta_regret"] < 0]
    qualifying = [b for b, flag in signals.items() if flag]
    if not complete or raw_long_competent is None:
        description = "PRIMARY_COMPARISON_LIMITED"
    elif not raw_long_competent:
        description = "WEAK_NEW_RAW_LONG_DIAGNOSTICS_ONLY"
    elif len(qualifying) == 2:
        description = "ALIGNMENT_AT_BOTH_OBSERVED_BUDGETS"
    elif qualifying:
        description = "ALIGNMENT_AT_" + qualifying[0]
    else:
        description = "NO_SPECIFIED_ALIGNMENT_SIGNAL"
    return {"new_raw_long_competent": raw_long_competent, "primary_comparisons_trustworthy": complete,
        "primary_comparisons_trustworthy_by_endpoint": trustworthy,
        "alignment_by_endpoint": signals, "qualifying_endpoints": qualifying,
        "reading": description, "opposite_sign_or_adverse_contrasts": losses,
        "mixed_budget": bool(qualifying and any(r["endpoint"] not in qualifying for r in losses)),
        "short_signal_lost_at_long": signals["SHORT"] is True and signals["LONG"] is False,
        "MEI": MEI, "diagnostic_margin": .000625,
        "ceiling": "selected seed-0 panel and two observed budgets; no best checkpoint selected"}


def score_summary(labels, predictions, exposures, historical, budget):
    metrics = {}
    for arm in ARMS:
        with budget.arm(arm):
            lines = {line["update"]: line for line in exposures[arm]}
            metrics[arm] = {}
            for endpoint, update in ENDPOINTS.items():
                values = predictions[arm][update]
                if values.shape != (16, 8) or values.dtype != np.float32:
                    raise ValueError("each snapshot requires 16 FP32 logit vectors")
                point = raw.score_readout(labels, values)
                for row, vector in zip(point["rows"], values):
                    row["logits"] = vector.tolist()
                    row["legal_logits"] = row.pop("legal_prediction")
                metrics[arm][endpoint] = {**point, "exposure": lines[update]}
    contrasts, descriptive = {}, {}
    for endpoint in ENDPOINTS:
        true = metrics[TRUE][endpoint]
        contrasts[endpoint] = {
            "new_RAW": paired_contrast(metrics[RAW][endpoint], true),
            "new_DERANGED": paired_contrast(metrics[DERANGED][endpoint], true),
            "historical_B04_RAW": paired_contrast(historical["representations"][RAW][endpoint], true)}
        descriptive[endpoint] = {
            "new_RAW_minus_new_DERANGED_regret": metrics[RAW][endpoint]["equal_side_regret"] - metrics[DERANGED][endpoint]["equal_side_regret"],
            "historical_minus_new_regret_by_arm": {a: historical["representations"][a][endpoint]["equal_side_regret"] - metrics[a][endpoint]["equal_side_regret"] for a in ARMS},
            "failed_primary_contrasts": [name for name, c in contrasts[endpoint].items() if c["delta_regret"] <= MEI]}
    return {"representations": metrics, "contrasts": contrasts, "descriptive": descriptive,
        "historical_representations": historical["representations"],
        "result_reading": result_reading(contrasts, metrics[RAW]["LONG"]["competent"])}


def run_experiment(output_dir, *, historical_summary, argv, execution_node, started, seed=0):
    budget = WallBudget(started)
    historical = json.loads(Path(historical_summary).read_text(encoding="utf-8"))
    budget.check()
    train, evaluation, calibration, metadata, predictor_report, calibration_report = b04.prepare(seed, budget.check, False)
    packets, donor_maps = b04.packet_sets(train, evaluation, calibration, seed)
    preparation_wall = time.perf_counter() - started
    snapshots, exposures, training_wall, scales = {}, {}, {}, {}
    for arm in ARMS:
        with budget.arm(arm):
            packets["TRAIN"][arm].require_rows(train)
            snapshots[arm], exposures[arm], training_wall[arm], scales[arm] = train_path(
                train, packets["TRAIN"][arm], seed=seed, final_update=258,
                trace_updates=tuple(ENDPOINTS.values()), batch_size=32,
                monitor=budget.check, representation=arm)
    predictions, evaluation_wall = {}, {}
    for arm in ARMS:
        with budget.arm(arm):
            evaluation_started = time.perf_counter()
            packets["EVALUATION"][arm].require_rows(evaluation)
            predictions[arm] = raw.forward_snapshots(snapshots[arm], evaluation, packets["EVALUATION"][arm], budget.check)
            evaluation_wall[arm] = time.perf_counter() - evaluation_started
    summary = score_summary(raw.panel_labels(evaluation, metadata), predictions, exposures, historical, budget)
    peak = base._peak_rss_bytes()
    summary.update({"object_id": OBJECT_ID, "seed": seed, "launch_sha": base.current_launch_sha(),
        "exact_argv": list(argv), "execution_node": execution_node,
        "historical_input": {"path": str(historical_summary), "input_commit": HISTORICAL_INPUT_COMMIT,
            "launch_sha": HISTORICAL_LAUNCH_SHA},
        "thread_contract": base.thread_contract(), "source_namespace": b01.SOURCE_NAMESPACE,
        "objective": "mean row expected native cost; temperature1; scale .01; logits",
        "initial_parameter_scales": scales,
        "training_order": [{"row_key": r.key.text, "address": metadata[r.key.text]} for r in train],
        "derangement_donor_maps": donor_maps,
        "endpoint_occurrences": b04.exposure_counts(train, donor_maps["TRAIN"], ENDPOINTS, 32),
        "predictor": predictor_report, "calibration": calibration_report,
        "work_counts": {"gate_updates": 774, "processed_examples": 24768,
            "network_forward_rows": 6 * len(evaluation), "scored_decisions": 6 * len(evaluation),
            "unique_eval_rows": len(evaluation), "historical_decisions_read": 6 * len(evaluation),
            "environment_transitions": 192 * 256 + sum(r.key.primitive_time for r in (*train, *evaluation)),
            "common_future_branch_steps": sum(int(np.count_nonzero(r.legal_mask)) * 16 for r in (*train, *evaluation))},
        "cost_law": {**project_cost(), "measured_preparation_seconds": preparation_wall,
            "measured_training_seconds_by_arm": training_wall, "measured_forward_seconds_by_arm": evaluation_wall,
            "arm_training_evaluation_scoring_seconds": budget.arm_seconds},
        "resources": {"inner_prepublication_wall_seconds": time.perf_counter() - started,
            "complete_accounting": "pending terminal supervisor elapsed; use account command after collection",
            "peak_rss_bytes": peak, "status": "measured" if peak is not None else "resources_unmeasured"}})
    budget.check()
    raw.publish_summary(output_dir, summary)
    budget.check()
    return summary


def publish_complete_accounting(output_dir, complete_wall_seconds):
    """Collection-time reduction of terminal outer elapsed; does not rerun science.

    The terminal supervisor measured the required run command through summary publication
    and process shutdown. This separate collection record is not a second learner invocation.
    """
    summary = json.loads((Path(output_dir) / "summary.json").read_text(encoding="utf-8"))
    result = complete_accounting(complete_wall_seconds,
        summary["cost_law"]["arm_training_evaluation_scoring_seconds"])
    result["timing_source"] = "terminal agent-task elapsed of the complete run command"
    result["scope"] = "run command including startup/preparation/checks/summary publication/shutdown; excludes collection reduction"
    (Path(output_dir) / "complete_accounting.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result
