"""Exact seed-0 RAW learner trace over B01 updates 252 through 264."""

from __future__ import annotations

from copy import deepcopy
import ctypes
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import time
from typing import Mapping, Sequence

THREAD_ENVIRONMENT = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")
for _thread_variable in THREAD_ENVIRONMENT:
    os.environ[_thread_variable] = "1"

import numpy as np
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

from experiments.candidates.commitment_residual_triggered_options.host import ScenarioTape
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import (
    counter_rng_for_namespace,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    ACTION_ORDER, PanelRow, RowKey, Split,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.evaluation import (
    native_regret, select_printed_action,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.host_bridge import (
    build_balanced_tapes, materialize_common_history_row, materialize_predictor_examples,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.models import (
    CommonHistoryGate,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.packets import (
    PacketDataset, raw_packet,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.training import (
    fit_fresh_predictor, legal_masked_mse,
)


OBJECT_ID = "CRTO-RAW-PHASE-TRACE-A-RECON-R01"
SOURCE_NAMESPACE = 2_026_083_192
LEARNER_NAMESPACE = 2_026_090_401
SEED = 0
BATCH_SIZE = 32
TRACE_UPDATES = tuple(range(252, 265))
FINAL_UPDATE = 264
ADAM_LR = 1e-3
GRADIENT_CLIP = 1.0
INVOCATION_CAP_SECONDS = 1_800.0
PRIOR_INVOCATION_SECONDS = 434.7066687
PROJECTED_ARM_SECONDS = 1_304.1200061
MINIMUM_MEMORY_BYTES = 4 * 1024**3
RECEIPT_MAX_AGE_SECONDS = 15 * 60
INITIAL_ANCHOR = {
    "initial_parameter_l2": 18.87916908516977,
    "initial_parameter_rms": 0.10402732933491829,
    "initial_parameter_linf": 0.28862619400024414,
}
UPDATE_256_ANCHOR = {
    "KEEP": {"exact_action_count": 8, "mean_regret": 0.0},
    "REPLAN": {"exact_action_count": 4, "mean_regret": 0.0066464623737892345},
    "equal_side_regret": 0.0033232311868946172,
}


def thread_contract() -> dict[str, object]:
    observed = {
        "torch_intraop_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
    }
    if any(os.environ[name] != "1" for name in THREAD_ENVIRONMENT) or any(
            count != 1 for count in observed.values()):
        raise RuntimeError("RAW trace requires one computational thread")
    return {
        "required_computational_threads": 1,
        "native_thread_environment": {name: os.environ[name] for name in THREAD_ENVIRONMENT},
        **observed, "matches": True,
    }


@dataclass(frozen=True)
class SelectedAddress:
    split: str
    event: str
    onset: int
    side: str
    source_slot: int
    episode_index: int
    prior_advantage: float


def _pair(split: str, event: str, onset: int, keep: tuple[int, int, float],
          replan: tuple[int, int, float]) -> tuple[SelectedAddress, SelectedAddress]:
    return (SelectedAddress(split, event, onset, "KEEP", *keep),
            SelectedAddress(split, event, onset, "REPLAN", *replan))


SELECTED_ROWS = tuple(row for pair in (
    _pair("EVAL", "COMMON-SENSOR", 50, (0, 867, -.015972133800688196), (1, 887, +.026129514381799113)),
    _pair("TRAIN", "COMMON-SENSOR", 66, (1, 861, -.015900201131431313), (5, 852, +.022324806761117533)),
    _pair("TRAIN", "COMMON-SENSOR", 82, (3, 868, -.015430707003534716), (1, 867, +.018707424451448768)),
    _pair("TRAIN", "COMMON-SENSOR", 98, (2, 858, -.015491697940307608), (7, 864, +.014432589133648643)),
    _pair("EVAL", "COMMON-SENSOR", 146, (3, 846, -.015191471236038062), (1, 858, +.011318814025678692)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 50, (2, 845, -.015844100664009333), (5, 860, +.028264546483069253)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 82, (5, 886, -.015868014489464870), (3, 882, +.033699291524739580)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 178, (6, 892, -.011855323258242345), (4, 856, +.011433789344832357)),
    _pair("EVAL", "NONE", 50, (5, 833, -.015924670360319540), (7, 866, +.022368155900459570)),
    _pair("TRAIN", "NONE", 66, (2, 883, -.016199788285241960), (5, 871, +.015043231765637488)),
    _pair("TRAIN", "NONE", 82, (0, 852, -.015553172932134207), (6, 834, +.023025781723483685)),
    _pair("TRAIN", "NONE", 98, (3, 832, -.015553172932134207), (5, 842, +.016646480061737690)),
    _pair("EVAL", "NONE", 146, (4, 838, -.016162472490300284), (0, 850, +.011387685355538746)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (4, 852, -.016081392315262316), (0, 832, +.051030566954046590)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 66, (1, 893, -.015592695627609620), (6, 835, +.055126609288734420)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 82, (1, 844, -.015074613764991612), (4, 867, +.020884116601865010)),
    _pair("EVAL", "UNANNOUNCED-DIFFERENTIAL", 98, (0, 870, -.012232430956317680), (7, 879, +.011364772507740845)),
    _pair("TRAIN", "COMMON-SENSOR", 50, (4, 832, -.015969266939506052), (7, 853, +.023850104117467240)),
    _pair("TRAIN", "COMMON-SENSOR", 66, (3, 890, -.015615137764533160), (0, 849, +.012661476509681191)),
    _pair("TRAIN", "COMMON-SENSOR", 82, (2, 836, -.015370194427050315), (7, 839, +.011328600211173268)),
    _pair("EVAL", "COMMON-SENSOR", 98, (6, 838, -.015461142323068305), (1, 869, +.012340280707167195)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 50, (6, 848, -.015530033664156173), (0, 841, +.028042269071415313)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 82, (6, 833, -.015132816906941404), (1, 881, +.017112418585218114)),
    _pair("TRAIN", "NONE", 50, (0, 875, -.015740560557822580), (2, 834, +.020523669369086340)),
    _pair("EVAL", "NONE", 66, (6, 888, -.014846210526128112), (4, 846, +.011921798141253603)),
    _pair("TRAIN", "NONE", 82, (4, 887, -.015220969238438131), (1, 888, +.015691913217543818)),
    _pair("TRAIN", "NONE", 98, (0, 877, -.015522374569892361), (7, 888, +.015956990983789250)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (2, 866, -.015284980505363602), (6, 854, +.041645193096735730)),
    _pair("EVAL", "UNANNOUNCED-DIFFERENTIAL", 66, (2, 888, -.015491697940307553), (4, 868, +.044192105128588870)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 82, (0, 839, -.015045679765442688), (6, 884, +.014180766863995609)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (5, 840, -.014999596081699235), (3, 847, +.038038314451649460)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 66, (5, 841, -.015400391272683014), (3, 872, +.038494234843152650)),
) for row in pair)


def selected_population_spec() -> list[dict[str, object]]:
    return [address.__dict__.copy() for address in SELECTED_ROWS]


def _parameter_tensors(model: CommonHistoryGate) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in model.named_parameters()}


def _parameter_scales(values: Mapping[str, torch.Tensor]) -> dict[str, float]:
    flat = torch.cat([value.reshape(-1).to(torch.float64) for value in values.values()])
    return {
        "initial_parameter_l2": float(torch.linalg.vector_norm(flat)),
        "initial_parameter_rms": float(torch.sqrt(torch.mean(flat.square()))),
        "initial_parameter_linf": float(torch.max(torch.abs(flat))),
    }


def _anchor_from_scales(observed: Mapping[str, float]) -> dict[str, object]:
    return {"observed": observed, "expected": INITIAL_ANCHOR.copy(), "matches": all(
        math.isclose(observed[name], expected, rel_tol=1e-7, abs_tol=0.0)
        for name, expected in INITIAL_ANCHOR.items()
    )}


def initialization_anchor(seed: int = SEED) -> dict[str, object]:
    model = CommonHistoryGate(counter_rng_for_namespace(
        LEARNER_NAMESPACE, "gate_initialization", seed,
    ))
    return _anchor_from_scales(_parameter_scales(_parameter_tensors(model)))


def _movement(initial: Mapping[str, torch.Tensor], model: CommonHistoryGate) -> dict[str, float]:
    start = torch.cat([initial[name].reshape(-1).to(torch.float64) for name in initial])
    end_parameters = dict(model.named_parameters())
    end = torch.cat([end_parameters[name].detach().cpu().reshape(-1).to(torch.float64)
                     for name in initial])
    delta = end - start
    return {
        "parameter_displacement_l2_over_initial_l2": (
            float(torch.linalg.vector_norm(delta)) / float(torch.linalg.vector_norm(start))),
        "parameter_displacement_linf_over_initial_linf": (
            float(torch.max(torch.abs(delta))) / max(float(torch.max(torch.abs(start))), 1e-12)),
    }


def _exposure_line(update: int, scales: Mapping[str, float],
                   movement: Mapping[str, float] | None, *, batch_size: int = BATCH_SIZE,
                   row_count: int = 48) -> dict[str, object]:
    return {
        "representation": "RAW", "update": update, "update_mod_3": update % 3,
        "post_update_cyclic_cursor": (batch_size * update) % row_count,
        "batch_size": batch_size, "processed_examples": batch_size * update,
        "adam_lr": ADAM_LR, "nominal_lr_exposure": ADAM_LR * update, **scales,
        "parameter_displacement_l2_over_initial_l2": None if movement is None else (
            movement["parameter_displacement_l2_over_initial_l2"]),
        "parameter_displacement_linf_over_initial_linf": None if movement is None else (
            movement["parameter_displacement_linf_over_initial_linf"]),
    }


def _cost_payload(anchor: Mapping[str, object]) -> dict[str, object]:
    lines = [_exposure_line(update, anchor["observed"], None) for update in TRACE_UPDATES]
    return {
        "object_id": OBJECT_ID, "result_bearing": False,
        "fixed_planning_law": "3 * 434.7066687 = 1304.1200061 seconds",
        "prior_complete_b01_invocation_seconds": PRIOR_INVOCATION_SECONDS,
        "planning_multiplier": 3, "projected_raw_trace_arm_seconds": PROJECTED_ARM_SECONDS,
        "per_arm_and_invocation_wall_cap_seconds": INVOCATION_CAP_SECONDS,
        "projection_within_cap": PROJECTED_ARM_SECONDS < INVOCATION_CAP_SECONDS,
        "thread_contract": thread_contract(),
        "prospective_work_counts": {
            "predictor_tapes": 128, "predictor_updates": 100,
            "predictor_batch_size": 128, "predictor_processed_examples": 12_800,
            "raw_gate_updates": FINAL_UPDATE, "raw_gate_batch_size": BATCH_SIZE,
            "raw_gate_processed_examples": FINAL_UPDATE * BATCH_SIZE,
            "checkpoint_count": len(TRACE_UPDATES),
            "checkpoint_evaluation_rows": len(TRACE_UPDATES) * 16,
            "true_residual_updates": 0, "true_residual_evaluation_rows": 0,
            "calibrated_derangement_updates": 0,
            "calibrated_derangement_evaluation_rows": 0,
        },
        "initialization_anchor": anchor, "prospective_exposure_lines": lines,
    }


def project_cost(seed: int = SEED) -> dict[str, object]:
    thread_contract()
    return _cost_payload(initialization_anchor(seed))


def validate_admission_receipt(path: str | Path, *, now: datetime | None = None) -> dict[str, object]:
    source = Path(path).resolve()
    value = json.loads(source.read_text(encoding="utf-8"))
    if not (value.get("passed") is True and value.get("physical_floor_pass") is True
            and value.get("effective_floor_pass") is True
            and int(value.get("available_physical_bytes", 0)) >= MINIMUM_MEMORY_BYTES
            and int(value.get("effective_available_bytes", 0)) >= MINIMUM_MEMORY_BYTES):
        raise ValueError("memory admission receipt does not establish both 4 GiB floors")
    stamp = str(value.get("assessed_at") or value.get("captured_at") or "")
    assessed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    current = now or datetime.now(timezone.utc)
    age = (current - assessed.astimezone(timezone.utc)).total_seconds()
    if not 0.0 <= age <= RECEIPT_MAX_AGE_SECONDS:
        raise ValueError("memory admission receipt is not fresh for this invocation")
    return {
        "path": str(source), "assessed_at": stamp, "age_seconds": age,
        "available_physical_bytes": int(value["available_physical_bytes"]),
        "effective_available_bytes": int(value["effective_available_bytes"]),
    }


def current_launch_sha() -> str:
    repo = Path(__file__).resolve().parents[4]
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def _check_wall(started: float) -> None:
    if time.perf_counter() - started > INVOCATION_CAP_SECONDS:
        raise TimeoutError("RAW trace invocation exceeded its 1800-second wall cap")


def _source_tape_map() -> dict[int, dict[int, ScenarioTape]]:
    return {slot: {tape.spec.episode_index: tape for tape in build_balanced_tapes(
        replicate=slot, split=Split.EVALUATION, regime="K8", count=64,
        first_episode_index=832, rng_namespace=SOURCE_NAMESPACE,
    )} for slot in range(8)}


def selected_source_manifest() -> list[dict[str, object]]:
    tapes = _source_tape_map()
    return [{**address.__dict__,
             "observed_event": tapes[address.source_slot][address.episode_index].spec.event.value,
             "observed_onset": tapes[address.source_slot][address.episode_index].spec.event_onset,
             "observed_cost": tapes[address.source_slot][address.episode_index].spec.replanning_cost,
             "observed_regime": tapes[address.source_slot][address.episode_index].spec.regime.value}
            for address in SELECTED_ROWS]


def _advantage(row: PanelRow) -> float:
    return float(np.max(row.g16[1:][row.legal_mask[1:]]) - row.g16[0])


def _selected_rows(predictor, *, monitor) -> tuple[
        tuple[PanelRow, ...], tuple[PanelRow, ...], dict[str, dict[str, object]]]:
    tapes = _source_tape_map()
    train, evaluation = [], []
    metadata: dict[str, dict[str, object]] = {}
    for address in SELECTED_ROWS:
        monitor()
        tape = tapes[address.source_slot][address.episode_index]
        split = Split.TRAIN if address.split == "TRAIN" else Split.EVALUATION
        row = materialize_common_history_row(
            tape, replicate=address.source_slot, split=split, forecast=predictor.packet_forecast,
        )
        if row is None:
            raise RuntimeError(f"selected source row is missing: {address}")
        direct = _advantage(row)
        expected_side = direct <= -0.01 if address.side == "KEEP" else direct >= 0.01
        if not (tape.spec.event.value == address.event and tape.spec.event_onset == address.onset
                and tape.spec.replanning_cost == 4.0 and row.key.regime == "K8"
                and row.elapsed_horizon == 4 and expected_side):
            raise RuntimeError(f"selected source row changed: {address}")
        (train if split is Split.TRAIN else evaluation).append(row)
        metadata[row.key.text] = {
            **address.__dict__, "source_split_coordinate": "EVALUATION",
            "direct_advantage": direct, "primitive_time": row.key.primitive_time,
            "agent": row.key.agent, "elapsed_horizon": row.elapsed_horizon,
            "observed_regime": row.key.regime, "observed_cost": float(row.cost),
            "denominator": tape.total_physical_arrivals(),
        }
    train.sort(key=lambda row: row.key.canonical)
    evaluation.sort(key=lambda row: row.key.canonical)
    if len(train) != 48 or len(evaluation) != 16:
        raise RuntimeError("selected population is not exactly 48 TRAIN and 16 EVAL rows")
    return tuple(train), tuple(evaluation), metadata


def _predictor_examples(tapes: Sequence[ScenarioTape], *, monitor) -> tuple:
    examples = []
    for tape in tapes:
        monitor()
        examples.extend(materialize_predictor_examples((tape,)))
    return tuple(sorted(examples, key=lambda example: example.canonical_key))


def _raw_dataset(rows: tuple[PanelRow, ...]) -> PacketDataset:
    return PacketDataset(tuple(row.key.text for row in rows), np.stack([
        raw_packet(row.target, row.mean, row.cholesky) for row in rows
    ]))


def _collate(rows: Sequence[PanelRow], packets: np.ndarray, indices: np.ndarray):
    selected = [rows[int(index)] for index in indices]
    lengths = torch.tensor([row.history.shape[0] for row in selected], dtype=torch.int64)
    histories = torch.zeros((len(selected), int(lengths.max()), 42), dtype=torch.float32)
    for index, row in enumerate(selected):
        histories[index, :row.history.shape[0]] = torch.from_numpy(np.array(row.history, copy=True))
    packet = torch.from_numpy(np.asarray(packets[indices], dtype=np.float32).copy())
    legal = torch.from_numpy(np.stack([row.legal_mask for row in selected]).copy())
    target = torch.nan_to_num(torch.from_numpy(
        np.stack([row.g16 for row in selected]).astype(np.float32)), nan=0.0)
    return histories, lengths, packet, legal, target


def _train(rows: tuple[PanelRow, ...], packets: PacketDataset, *, seed: int,
           final_update: int, trace_updates: Sequence[int], batch_size: int,
           started: float) -> tuple[
               dict[int, CommonHistoryGate], list[dict[str, object]], float, dict[str, float]]:
    order = np.resize(np.arange(len(rows), dtype=np.int64), final_update * batch_size)
    model = CommonHistoryGate(counter_rng_for_namespace(
        LEARNER_NAMESPACE, "gate_initialization", seed,
    ))
    initial = _parameter_tensors(model)
    scales = _parameter_scales(initial)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=ADAM_LR, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0,
    )
    snapshots: dict[int, CommonHistoryGate] = {}
    exposures = []
    training_started = time.perf_counter()
    for update in range(1, final_update + 1):
        _check_wall(started)
        begin = (update - 1) * batch_size
        histories, lengths, packet, legal, target = _collate(
            rows, packets.values, order[begin:begin + batch_size],
        )
        prediction = model(histories, lengths, packet)
        loss = legal_masked_mse(prediction, target, legal)
        if not bool(torch.isfinite(loss)):
            raise RuntimeError("RAW gate loss became nonfinite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if any(parameter.grad is not None and not bool(torch.all(torch.isfinite(parameter.grad)))
               for parameter in model.parameters()):
            raise RuntimeError("RAW gate gradient became nonfinite")
        torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
        optimizer.step()
        if any(not bool(torch.all(torch.isfinite(parameter))) for parameter in model.parameters()):
            raise RuntimeError("RAW gate parameter became nonfinite")
        if update in trace_updates:
            snapshot = deepcopy(model).eval()
            snapshots[update] = snapshot
            movement = _movement(initial, snapshot)
            if not all(math.isfinite(value) and value > 0.0 for value in movement.values()):
                raise RuntimeError("RAW gate movement is zero or nonfinite")
            exposures.append(_exposure_line(
                update, scales, movement, batch_size=batch_size, row_count=len(rows),
            ))
    return snapshots, exposures, time.perf_counter() - training_started, scales


def _evaluate(model: CommonHistoryGate, rows: tuple[PanelRow, ...], packets: PacketDataset,
              metadata: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    packets.require_rows(rows)
    lengths = torch.tensor([row.history.shape[0] for row in rows], dtype=torch.int64)
    histories = torch.zeros((len(rows), int(lengths.max()), 42), dtype=torch.float32)
    for index, row in enumerate(rows):
        histories[index, :row.history.shape[0]] = torch.from_numpy(np.array(row.history, copy=True))
    with torch.no_grad():
        predicted = model(histories, lengths, torch.from_numpy(packets.values.copy())).cpu().numpy()
    by_side = {"KEEP": [], "REPLAN": []}
    exact = {"KEEP": 0, "REPLAN": 0}
    details = []
    for row, values in zip(rows, predicted):
        selected = select_printed_action(values, row.legal_mask)
        oracle = select_printed_action(row.g16, row.legal_mask)
        regret = native_regret(row.g16, row.legal_mask, selected)
        side = str(metadata[row.key.text]["side"])
        by_side[side].append(regret)
        exact[side] += int(selected == oracle)
        details.append({
            "row_key": row.key.text, "material_side": side,
            "legal_mask": row.legal_mask.tolist(),
            "legal_action_order": [ACTION_ORDER[i] for i in np.flatnonzero(row.legal_mask)],
            "g16": [None if not np.isfinite(value) else float(value) for value in row.g16],
            "legal_g16": {ACTION_ORDER[i]: float(row.g16[i]) for i in np.flatnonzero(row.legal_mask)},
            "oracle_action": ACTION_ORDER[oracle], "oracle_action_index": oracle,
            "oracle_g16": float(row.g16[oracle]), "raw_selected_action": ACTION_ORDER[selected],
            "raw_selected_action_index": selected, "raw_selected_g16": float(row.g16[selected]),
            "native_regret": regret, "exact_action_correct": selected == oracle,
        })
    sides = {side: {"row_count": len(values), "exact_action_count": exact[side],
                    "mean_regret": float(np.mean(values))}
             for side, values in by_side.items()}
    return {"rows": details, "sides": sides, "equal_side_regret":
            0.5 * (sides["KEEP"]["mean_regret"] + sides["REPLAN"]["mean_regret"]),
            "competent": all(sides[side]["exact_action_count"] >= 6
                             and sides[side]["mean_regret"] <= 0.005
                             for side in ("KEEP", "REPLAN"))}


def information_boundary_report(*, evaluations_after_training: bool = True) -> dict[str, object]:
    return {
        "eval_affects_predictor_fit": False, "eval_affects_raw_training": False,
        "eval_affects_example_order": False, "eval_affects_stopping": False,
        "eval_affects_checkpoint_creation": False, "eval_affects_checkpoint_selection": False,
        "old_result_supplies_learner_state": False,
        "true_residual_gate_updates": 0, "true_residual_evaluation_rows": 0,
        "calibrated_derangement_gate_updates": 0,
        "calibrated_derangement_evaluation_rows": 0,
        "confirmation_namespace_read_or_instantiated": False,
        "evaluations_started_after_all_snapshots_created": evaluations_after_training,
    }


def information_boundary_is_valid(report: Mapping[str, object]) -> bool:
    forbidden_true = (
        "eval_affects_predictor_fit", "eval_affects_raw_training", "eval_affects_example_order",
        "eval_affects_stopping", "eval_affects_checkpoint_creation",
        "eval_affects_checkpoint_selection", "old_result_supplies_learner_state",
        "confirmation_namespace_read_or_instantiated",
    )
    return (not any(bool(report[name]) for name in forbidden_true)
            and int(report["true_residual_gate_updates"]) == 0
            and int(report["true_residual_evaluation_rows"]) == 0
            and int(report["calibrated_derangement_gate_updates"]) == 0
            and int(report["calibrated_derangement_evaluation_rows"]) == 0
            and bool(report["evaluations_started_after_all_snapshots_created"]))


def update_256_anchor_matches(metrics: Mapping[str, object]) -> bool:
    sides = metrics["sides"]
    return (all(int(sides[side]["exact_action_count"]) == expected["exact_action_count"]
                and math.isclose(float(sides[side]["mean_regret"]), expected["mean_regret"],
                                 rel_tol=0.0, abs_tol=1e-12)
                for side, expected in (("KEEP", UPDATE_256_ANCHOR["KEEP"]),
                                       ("REPLAN", UPDATE_256_ANCHOR["REPLAN"])))
            and math.isclose(float(metrics["equal_side_regret"]),
                             UPDATE_256_ANCHOR["equal_side_regret"],
                             rel_tol=0.0, abs_tol=1e-12))


def trace_measurement_issues(metrics: Mapping[str, Mapping[str, object]],
                             exposures: Sequence[Mapping[str, object]]) -> list[str]:
    issues = []
    if tuple(int(update) for update in metrics) != TRACE_UPDATES:
        issues.append("TRACE_UPDATE_SET_OR_ORDER_MISMATCH")
    if len(exposures) != len(TRACE_UPDATES):
        issues.append("TRACE_EXPOSURE_COUNT_MISMATCH")
    for update, checkpoint in metrics.items():
        rows = checkpoint["rows"]
        sides = checkpoint["sides"]
        if len(rows) != 16 or any(int(sides[side]["row_count"]) != 8
                                  for side in ("KEEP", "REPLAN")):
            issues.append(f"UPDATE_{update}_EVALUATION_COUNT_MISMATCH")
        for row in rows:
            legal = row["legal_mask"]
            selected = int(row["raw_selected_action_index"])
            legal_g16 = tuple(float(value) for value in row["legal_g16"].values())
            regret = float(row["native_regret"])
            if (not legal[selected] or not legal_g16
                    or not all(math.isfinite(value) and value >= 0.0 for value in legal_g16)
                    or not math.isfinite(regret) or regret < 0.0):
                issues.append(f"UPDATE_{update}_ILLEGAL_OR_NONFINITE_ROW_MEASUREMENT")
                break
    for line in exposures:
        movement = (line["parameter_displacement_l2_over_initial_l2"],
                    line["parameter_displacement_linf_over_initial_linf"])
        if not all(value is not None and math.isfinite(float(value)) and float(value) > 0.0
                   for value in movement):
            issues.append(f"UPDATE_{line['update']}_MOVEMENT_MISSING_OR_NONFINITE")
    return issues


def apply_result_rule(*, information_boundary_valid: bool, completeness_issues: Sequence[str]) -> str:
    if not information_boundary_valid:
        return "A01-RAW-PHASE-INFORMATION-BOUNDARY-INVALID"
    if completeness_issues:
        return "A01-RAW-PHASE-INCOMPLETE"
    return "A01-RAW-PHASE-TRACE-MEASURED"


def _peak_rss_bytes() -> int | None:
    if hasattr(ctypes, "windll"):
        class Counters(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong),
                        ("peak_working_set", ctypes.c_size_t), ("working_set", ctypes.c_size_t),
                        ("quota_peak_paged", ctypes.c_size_t), ("quota_paged", ctypes.c_size_t),
                        ("quota_peak_nonpaged", ctypes.c_size_t), ("quota_nonpaged", ctypes.c_size_t),
                        ("pagefile", ctypes.c_size_t), ("peak_pagefile", ctypes.c_size_t)]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if ctypes.windll.psapi.GetProcessMemoryInfo(
                ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return int(counters.peak_working_set)
        return None
    try:
        import resource
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return peak if resource.getpagesize() == 1 else peak * 1024
    except (ImportError, AttributeError):
        return None


def _toy_population() -> tuple[tuple[PanelRow, ...], tuple[PanelRow, ...], dict[str, dict[str, object]]]:
    panels = []
    metadata: dict[str, dict[str, object]] = {}
    for split in (Split.TRAIN, Split.EVALUATION):
        rows = []
        for index in range(6):
            side = "KEEP" if index % 2 == 0 else "REPLAN"
            key = RowKey(0, split, "K8", index + (0 if split is Split.TRAIN else 100), 60, 0)
            g16 = np.full(8, np.nan, dtype=np.float64)
            g16[:2] = (0.02, 0.0) if side == "KEEP" else (0.0, 0.02)
            rows.append(PanelRow(
                key=key, cost=4.0, elapsed_horizon=4,
                history=np.full((3, 42), index / 10.0, dtype=np.float32),
                target=np.full(8, 0.1 * index, dtype=np.float32),
                mean=np.zeros(8, dtype=np.float32), cholesky=np.eye(8, dtype=np.float32),
                legal_mask=np.asarray((True, True, False, False, False, False, False, False)),
                g16=g16, logged_action=0, tape_record=("toy", split.value, index),
            ))
            metadata[key.text] = {"side": side, "denominator": 1}
        panels.append(tuple(rows))
    return panels[0], panels[1], metadata


def run_experiment(output_dir: str | Path, *, admission_receipt: str | Path,
                   argv: Sequence[str], execution_node: str, seed: int = SEED,
                   toy: bool = False) -> dict[str, object]:
    if seed != SEED:
        raise ValueError("this object has fixed learner seed 0")
    threads = thread_contract()
    admission = validate_admission_receipt(admission_receipt)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if toy:
        train_rows, eval_rows, metadata = _toy_population()
        predictor_report = {"tapes": 0, "examples": 0, "updates": 0, "processed_examples": 0}
        selected_reproduction = []
        final_update, batch_size, trace_updates = 3, 4, (1, 2, 3)
    else:
        predictor_tapes = (
            build_balanced_tapes(replicate=0, split=Split.PREDICTOR_FIT, regime="K4", count=64,
                                 first_episode_index=0, rng_namespace=LEARNER_NAMESPACE)
            + build_balanced_tapes(replicate=0, split=Split.PREDICTOR_FIT, regime="K8", count=64,
                                   first_episode_index=64, rng_namespace=LEARNER_NAMESPACE)
        )
        examples = _predictor_examples(predictor_tapes, monitor=lambda: _check_wall(started))
        predictor, audit = fit_fresh_predictor(
            examples, replicate=seed, updates=100, batch_size=128,
            rng_namespace=LEARNER_NAMESPACE, resource_monitor=lambda: _check_wall(started),
        )
        train_rows, eval_rows, metadata = _selected_rows(
            predictor, monitor=lambda: _check_wall(started),
        )
        predictor_report = {
            "rng_namespace": LEARNER_NAMESPACE, "split": "PREDICTOR_FIT",
            "tapes": 128, "examples": audit.examples, "updates": audit.updates,
            "batch_size": 128, "processed_examples": audit.processed_examples,
            "K4_episode_indices": [0, 63], "K8_episode_indices": [64, 127],
        }
        selected_reproduction = [metadata[row.key.text] for row in (*train_rows, *eval_rows)]
        final_update, batch_size, trace_updates = FINAL_UPDATE, BATCH_SIZE, TRACE_UPDATES
    train_packets, eval_packets = _raw_dataset(train_rows), _raw_dataset(eval_rows)
    snapshots, exposures, training_wall, initial_scales = _train(
        train_rows, train_packets, seed=seed, final_update=final_update,
        trace_updates=trace_updates, batch_size=batch_size, started=started,
    )
    anchor = _anchor_from_scales(initial_scales)
    evaluation_started = time.perf_counter()
    metrics = {str(update): _evaluate(snapshots[update], eval_rows, eval_packets, metadata)
               for update in trace_updates}
    evaluation_wall = time.perf_counter() - evaluation_started
    boundary = information_boundary_report(evaluations_after_training=True)
    issues = []
    if toy:
        issues.append("TOY_SMOKE_NOT_A_SCIENTIFIC_POPULATION")
    else:
        if not anchor["matches"]:
            issues.append("SEED_0_INITIALIZATION_ANCHOR_MISMATCH")
        if not update_256_anchor_matches(metrics["256"]):
            issues.append("UPDATE_256_B01_ANCHOR_MISMATCH")
        if (predictor_report["tapes"], predictor_report["updates"],
                predictor_report["examples"], predictor_report["processed_examples"]) != (
                    128, 100, 32_256, 12_800):
            issues.append("PREDICTOR_COUNT_MISMATCH")
        if len(selected_reproduction) != 64 or len(train_rows) != 48 or len(eval_rows) != 16:
            issues.append("SELECTED_POPULATION_COUNT_MISMATCH")
        issues.extend(trace_measurement_issues(metrics, exposures))
    anchor_regret = float(metrics[str(256 if not toy else 2)]["equal_side_regret"])
    for update, value in metrics.items():
        value["update"] = int(update)
        value["update_mod_3"] = int(update) % 3
        value["post_update_cyclic_cursor"] = (batch_size * int(update)) % len(train_rows)
        value["processed_examples"] = batch_size * int(update)
        value["nominal_lr_exposure"] = ADAM_LR * int(update)
        value["signed_local_difference_D_u"] = anchor_regret - float(value["equal_side_regret"])
    best = min(metrics.values(), key=lambda value: (value["equal_side_regret"], value["update"]))
    worst = min(metrics.values(), key=lambda value: (-value["equal_side_regret"], value["update"]))
    wall = time.perf_counter() - started
    _check_wall(started)
    peak = _peak_rss_bytes()
    branch = apply_result_rule(
        information_boundary_valid=information_boundary_is_valid(boundary),
        completeness_issues=issues,
    )
    summary = {
        "object_id": OBJECT_ID, "seed": seed, "toy": toy, "result_branch": branch,
        "completeness_issues": issues, "launch_sha": current_launch_sha(),
        "exact_argv": list(argv), "execution_node": execution_node,
        "thread_contract": threads,
        "result_root": str(output), "source_law": {
            "rng_namespace": SOURCE_NAMESPACE, "source_split_coordinate": "EVALUATION",
            "regime": "K8", "source_slots": list(range(8)), "count_per_source_slot": 64,
            "first_episode_index": 832, "old_result_json_read": False,
            "legacy_confirmation_namespace_read_or_instantiated": False,
        },
        "selected_population": {"train_rows": len(train_rows), "evaluation_rows": len(eval_rows),
                                "reproduction": selected_reproduction},
        "predictor": predictor_report, "representation": "RAW",
        "absent_representations": ["TRUE_RESIDUAL", "CALIBRATED_DERANGEMENT"],
        "action_order": list(ACTION_ORDER), "initialization_anchor": anchor,
        "update_256_anchor": {"expected": UPDATE_256_ANCHOR,
                              "matches": False if toy else update_256_anchor_matches(metrics["256"])},
        "trace": metrics, "trace_aggregate": {
            "anchor_update": 256, "best_update_smallest_tie_break": best["update"],
            "worst_update_smallest_tie_break": worst["update"],
            "best_equal_side_regret": best["equal_side_regret"],
            "worst_equal_side_regret": worst["equal_side_regret"],
        },
        "exposure_lines": exposures, "information_boundary": boundary,
        "work_counts": {
            "predictor_tapes": predictor_report["tapes"],
            "predictor_examples": predictor_report["examples"],
            "predictor_updates": predictor_report["updates"],
            "predictor_processed_examples": predictor_report["processed_examples"],
            "environment_transitions": (0 if toy else 128 * 256 + sum(
                row.key.primitive_time for row in (*train_rows, *eval_rows))),
            "common_future_branch_steps": (0 if toy else sum(
                int(np.count_nonzero(row.legal_mask)) * 16 for row in (*train_rows, *eval_rows))),
            "raw_gate_updates": final_update, "raw_processed_examples": final_update * batch_size,
            "checkpoint_count": len(trace_updates),
            "checkpoint_evaluation_rows": len(trace_updates) * len(eval_rows),
            "true_residual_gate_updates": 0, "true_residual_evaluation_rows": 0,
            "calibrated_derangement_gate_updates": 0,
            "calibrated_derangement_evaluation_rows": 0,
        },
        "cost_law": {**_cost_payload(anchor),
                     "measured_raw_training_wall_seconds": training_wall,
                     "measured_wall_seconds_per_raw_gate_update": training_wall / final_update,
                     "measured_checkpoint_evaluation_wall_seconds": evaluation_wall,
                     "measured_wall_seconds_per_checkpoint_evaluation": evaluation_wall / len(trace_updates),
                     "measured_invocation_wall_seconds": wall},
        "resources": {"admission": admission, "wall_seconds": wall, "peak_rss_bytes": peak,
                      "status": "measured" if peak is not None else "resources_unmeasured"},
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    return summary
