"""B07 centers prediction and target separately; evaluation stays uncentered."""

from __future__ import annotations

import json
from pathlib import Path
import time

from experiments.candidates.commitment_residual_triggered_options.raw_exposure_b06 import experiment as b06

b04, raw, base, np = b06.b04, b06.raw, b06.base, b06.np
torch, check_wall = base.torch, b04.check_wall
OBJECT_ID = "CRTO-RAW-CENTERED-LOSS-B07"
MEI = .000625


def centered_loss(prediction, target, legal):
    counts = legal.sum(dim=-1, keepdim=True).to(torch.float32)
    prediction_mean = torch.where(legal, prediction, 0.0).sum(dim=-1, keepdim=True) / counts
    target_mean = torch.where(legal, target, 0.0).sum(dim=-1, keepdim=True) / counts
    return base.legal_masked_mse(prediction - prediction_mean, target - target_mean, legal)


def project_cost(seed):
    per_update, readout, displacement = {
        1: (.05216934772284702, .007404837990179658, (.2442592158905306, 1.922981775039011)),
        2: (.047116037356571785, .007313847003388219, (.2792536742091679, 2.055482417800879)),
    }[seed]
    scales = dict(zip(("initial_parameter_l2", "initial_parameter_rms", "initial_parameter_linf"), b06.HISTORICAL[seed]["scales"]))
    return {"seed": seed, "result_bearing": False, "law": "3*(P + 516*t_s + E_s)",
        "P": 62.425374370999634, "t_s": per_update, "E_s": readout,
        "projected_arm_seconds": 3 * (62.425374370999634 + 516 * per_update + readout),
        "arm_cap_seconds": b04.ARM_CAP, "invocation_cap_seconds": b04.SHARED_CAP,
        "prior_B06_absolute_loss_516_measurement": base._exposure_line(516, scales, dict(zip((
            "parameter_displacement_l2_over_initial_l2", "parameter_displacement_linf_over_initial_linf"), displacement))),
        "exposure_plan": {"update": 516, "batch_size": 32, "processed_examples": 16512,
            "recipient_occurrences": 344, "adam_lr": .001, "nominal_lr_exposure": .516},
        "work_plan": {"predictor_tapes": 128, "predictor_updates": 100, "predictor_processed_examples": 12800,
            "gate_updates": 516, "processed_examples": 16512, "new_forward_rows": 16, "new_scored_decisions": 16,
            "historical_decisions_read": 16, "unique_eval_rows": 16, "calibration_examples": 0, "derangement_packets": 0}}


def result_rule(difference, competent):
    if not np.isfinite(difference):
        raise ValueError("nonfinite paired difference has no scientific branch")
    if difference < -MEI:
        return "B07-MATERIAL-NATIVE-COST"
    if not competent:
        return "B07-COMPARATOR-STILL-WEAK"
    if difference > MEI:
        return "B07-COMPETENCE-WITH-NATIVE-GAIN"
    return "B07-COMPETENCE-WITHIN-MEI"


def aggregate_rule(branches):
    if set(branches) != {1, 2} or any(v is None for v in branches.values()):
        return None
    if "B07-MATERIAL-NATIVE-COST" in branches.values():
        return "B07-COST-PRESENT"
    if "B07-COMPARATOR-STILL-WEAK" in branches.values():
        return "B07-COMPARATOR-LIMITED"
    return "B07-COMPETENT-BOTH"


def compare_readouts(baseline, treatment):
    prior_rows = {r["row_key"]: r for r in baseline["rows"]}
    if set(prior_rows) != {r["row_key"] for r in treatment["rows"]} or len(prior_rows) != len(treatment["rows"]):
        raise ValueError("baseline and treatment must contain the same distinct EVAL identities")
    alignment, changed = [], []
    for after in treatment["rows"]:
        before = prior_rows[after["row_key"]]
        identity_matches = before["material_side"] == after["material_side"] and before["legal_mask"] == after["legal_mask"]
        native_matches = before["legal_g16"] == after["legal_g16"]
        alignment.append({"row_key": after["row_key"], "identity_aligned": identity_matches, "native_labels_aligned": native_matches})
        if not identity_matches or not native_matches:
            raise ValueError("baseline and treatment native labels, side or legal mask differ")
        if before["selected_action_index"] != after["selected_action_index"]:
            changed.append({"row_key": after["row_key"], "material_side": after["material_side"],
                "baseline_action": before["selected_action"], "treatment_action": after["selected_action"],
                "baseline_regret": before["native_regret"], "treatment_regret": after["native_regret"],
                "paired_regret_difference": before["native_regret"] - after["native_regret"]})
    difference = baseline["equal_side_regret"] - treatment["equal_side_regret"]
    return {"baseline": baseline, "treatment": treatment, "native_alignment": alignment,
        "changed_actions": changed, "D": difference, "MEI": MEI,
        "C_baseline": baseline["competent"], "C_treatment": treatment["competent"],
        "result_branch": result_rule(difference, treatment["competent"])}


# Accepted B04 loop: only the loss call differs.
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
        loss = centered_loss(prediction, target, legal)
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


def run_experiment(output_dir, *, seed, baseline_summary, argv, execution_node, toy=False):
    started = time.perf_counter()
    prior = json.loads(Path(baseline_summary).read_text(encoding="utf-8"))
    if prior["seed"] != seed:
        raise ValueError("baseline seed must match the treatment seed")
    train, evaluation, metadata, predictor = b06.prepare(seed, lambda: check_wall(started), toy)
    train_packets, eval_packets = base._raw_dataset(train), base._raw_dataset(evaluation)
    final_update, batch_size = (6, 4) if toy else (516, 32)
    preparation_seconds = time.perf_counter() - started
    snapshots, exposures, training_seconds, scales = train_path(train, train_packets, seed=seed,
        final_update=final_update, trace_updates=(final_update,), batch_size=batch_size, started=started, representation="RAW")
    evaluation_started = time.perf_counter()
    predictions = raw.forward_snapshots(snapshots, evaluation, eval_packets,
        lambda: check_wall(started, training_seconds + time.perf_counter() - evaluation_started))
    forward_seconds = time.perf_counter() - evaluation_started
    treatment = raw.score_readout(raw.panel_labels(evaluation, metadata), predictions[final_update])
    visits = np.bincount(np.resize(np.arange(len(train)), final_update * batch_size), minlength=len(train))
    treatment.update(exposure=exposures[0], recipient_counts={r.key.text: int(n) for r, n in zip(train, visits)})
    summary = compare_readouts(prior["endpoints"]["516"], treatment)
    evaluation_seconds = time.perf_counter() - evaluation_started
    check_wall(started, training_seconds + evaluation_seconds)
    peak = base._peak_rss_bytes()
    summary.update({"object_id": OBJECT_ID, "seed": seed, "toy": toy, "launch_sha": base.current_launch_sha(),
        "exact_argv": list(argv), "execution_node": execution_node, "baseline_input_path": str(baseline_summary),
        "thread_contract": base.thread_contract(), "source_namespace": b06.b01.SOURCE_NAMESPACE,
        "initial_parameter_scales": scales, "predictor": predictor,
        "selected_population": {"train_rows": len(train), "evaluation_rows": len(evaluation),
            "canonical_order": [r.key.text for r in train],
            "metadata": [{"row_key": r.key.text, **metadata[r.key.text]} for r in (*train, *evaluation)]},
        "work_counts": {"gate_updates": final_update, "processed_examples": final_update * batch_size,
            "new_forward_rows": len(evaluation), "new_scored_decisions": len(evaluation),
            "historical_decisions_read": len(prior["endpoints"]["516"]["rows"]), "unique_eval_rows": len(evaluation),
            "calibration_tapes": 0, "calibration_examples": 0, "derangement_packets": 0,
            "environment_transitions": 0 if toy else 128 * 256 + sum(r.key.primitive_time for r in (*train, *evaluation)),
            "common_future_branch_steps": 0 if toy else sum(int(np.count_nonzero(r.legal_mask)) * 16 for r in (*train, *evaluation))},
        "cost_law": {**project_cost(seed), "measured_preparation_seconds": preparation_seconds,
            "measured_training_seconds": training_seconds, "measured_seconds_per_update": training_seconds / final_update,
            "measured_forward_seconds": forward_seconds, "measured_scoring_seconds": evaluation_seconds - forward_seconds},
        "resources": {"wall_seconds": time.perf_counter() - started, "peak_rss_bytes": peak,
                      "status": "measured" if peak is not None else "resources_unmeasured"}})
    if toy:
        summary["result_branch"] = None
        summary["engineering_only"] = "TOY_SMOKE_WITH_SYNTHETIC_BASELINE_NOT_A_SCIENTIFIC_POPULATION"
    raw.publish_summary(output_dir, summary)
    check_wall(started)
    return summary
