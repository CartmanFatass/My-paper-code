"""CRTO balanced residual finite-population learner.

This attempt deliberately reuses the current CRTO host, predictor, packet, and
gate primitives.  It owns only the new selected population, matched 32/256
update trajectories, observables, and frozen result rule.
"""

from __future__ import annotations

from copy import deepcopy
import ctypes
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Mapping, Sequence

import numpy as np
import torch

from experiments.candidates.commitment_residual_triggered_options.host import (
    EventClass, HORIZON, Lane, Location, Option, Regime, ScenarioSpec, ScenarioTape,
    ServiceRelayHost,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.calibration import (
    fit_calibration_from_examples,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import (
    counter_rng_for_namespace,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    ACTION_ORDER, Budget, PanelRow, Representation, RowKey, Split,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.evaluation import (
    native_regret, select_printed_action,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.host_bridge import (
    build_balanced_tapes, canonical_calibration_tapes, materialize_common_history_row,
    materialize_predictor_examples, scan_common_history_boundary, scripted_decisions,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.models import (
    CommonHistoryGate, canonical_state,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.packets import (
    CalibrationTable, PacketDataset, construct_packet_views,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.training import (
    fit_fresh_predictor, legal_masked_mse,
)


OBJECT_ID = "CRTO-B-EXPLORE-BALANCED-RESIDUAL-R01-R1"
SOURCE_NAMESPACE = 2_026_083_192
LEARNER_NAMESPACE = 2_026_090_401
SEED = 0
BATCH_SIZE = 32
SHORT_UPDATES = 32
LONG_UPDATES = 256
ADAM_LR = 1e-3
GRADIENT_CLIP = 1.0
DELTA = 0.0025
ARM_CAP_SECONDS = 900.0
INVOCATION_CAP_SECONDS = 2_700.0
MINIMUM_MEMORY_BYTES = 4 * 1024**3
RECEIPT_MAX_AGE_SECONDS = 15 * 60


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
    return (
        SelectedAddress(split, event, onset, "KEEP", *keep),
        SelectedAddress(split, event, onset, "REPLAN", *replan),
    )


SELECTED_ROWS = tuple(row for pair in (
    _pair("EVAL", "COMMON-SENSOR", 50, (0, 867, -0.015972133800688196), (1, 887, +0.026129514381799113)),
    _pair("TRAIN", "COMMON-SENSOR", 66, (1, 861, -0.015900201131431313), (5, 852, +0.022324806761117533)),
    _pair("TRAIN", "COMMON-SENSOR", 82, (3, 868, -0.015430707003534716), (1, 867, +0.018707424451448768)),
    _pair("TRAIN", "COMMON-SENSOR", 98, (2, 858, -0.015491697940307608), (7, 864, +0.014432589133648643)),
    _pair("EVAL", "COMMON-SENSOR", 146, (3, 846, -0.015191471236038062), (1, 858, +0.011318814025678692)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 50, (2, 845, -0.015844100664009333), (5, 860, +0.028264546483069253)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 82, (5, 886, -0.015868014489464870), (3, 882, +0.033699291524739580)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 178, (6, 892, -0.011855323258242345), (4, 856, +0.011433789344832357)),
    _pair("EVAL", "NONE", 50, (5, 833, -0.015924670360319540), (7, 866, +0.022368155900459570)),
    _pair("TRAIN", "NONE", 66, (2, 883, -0.016199788285241960), (5, 871, +0.015043231765637488)),
    _pair("TRAIN", "NONE", 82, (0, 852, -0.015553172932134207), (6, 834, +0.023025781723483685)),
    _pair("TRAIN", "NONE", 98, (3, 832, -0.015553172932134207), (5, 842, +0.016646480061737690)),
    _pair("EVAL", "NONE", 146, (4, 838, -0.016162472490300284), (0, 850, +0.011387685355538746)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (4, 852, -0.016081392315262316), (0, 832, +0.051030566954046590)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 66, (1, 893, -0.015592695627609620), (6, 835, +0.055126609288734420)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 82, (1, 844, -0.015074613764991612), (4, 867, +0.020884116601865010)),
    _pair("EVAL", "UNANNOUNCED-DIFFERENTIAL", 98, (0, 870, -0.012232430956317680), (7, 879, +0.011364772507740845)),
    _pair("TRAIN", "COMMON-SENSOR", 50, (4, 832, -0.015969266939506052), (7, 853, +0.023850104117467240)),
    _pair("TRAIN", "COMMON-SENSOR", 66, (3, 890, -0.015615137764533160), (0, 849, +0.012661476509681191)),
    _pair("TRAIN", "COMMON-SENSOR", 82, (2, 836, -0.015370194427050315), (7, 839, +0.011328600211173268)),
    _pair("EVAL", "COMMON-SENSOR", 98, (6, 838, -0.015461142323068305), (1, 869, +0.012340280707167195)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 50, (6, 848, -0.015530033664156173), (0, 841, +0.028042269071415313)),
    _pair("TRAIN", "CUED-DIFFERENTIAL", 82, (6, 833, -0.015132816906941404), (1, 881, +0.017112418585218114)),
    _pair("TRAIN", "NONE", 50, (0, 875, -0.015740560557822580), (2, 834, +0.020523669369086340)),
    _pair("EVAL", "NONE", 66, (6, 888, -0.014846210526128112), (4, 846, +0.011921798141253603)),
    _pair("TRAIN", "NONE", 82, (4, 887, -0.015220969238438131), (1, 888, +0.015691913217543818)),
    _pair("TRAIN", "NONE", 98, (0, 877, -0.015522374569892361), (7, 888, +0.015956990983789250)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (2, 866, -0.015284980505363602), (6, 854, +0.041645193096735730)),
    _pair("EVAL", "UNANNOUNCED-DIFFERENTIAL", 66, (2, 888, -0.015491697940307553), (4, 868, +0.044192105128588870)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 82, (0, 839, -0.015045679765442688), (6, 884, +0.014180766863995609)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (5, 840, -0.014999596081699235), (3, 847, +0.038038314451649460)),
    _pair("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 66, (5, 841, -0.015400391272683014), (3, 872, +0.038494234843152650)),
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


def _movement(initial: Mapping[str, torch.Tensor], model: CommonHistoryGate) -> dict[str, float]:
    start = torch.cat([initial[name].reshape(-1).to(torch.float64) for name in initial])
    end = torch.cat([dict(model.named_parameters())[name].detach().cpu().reshape(-1).to(torch.float64)
                     for name in initial])
    delta = end - start
    if not (bool(torch.all(torch.isfinite(start))) and bool(torch.all(torch.isfinite(end)))
            and bool(torch.all(torch.isfinite(delta)))):
        raise RuntimeError("gate parameters or movement became nonfinite")
    initial_l2 = float(torch.linalg.vector_norm(start))
    initial_linf = float(torch.max(torch.abs(start)))
    return {
        "parameter_displacement_l2_over_initial_l2": (
            float(torch.linalg.vector_norm(delta)) / initial_l2),
        "parameter_displacement_linf_over_initial_linf": (
            float(torch.max(torch.abs(delta))) / max(initial_linf, 1e-12)),
    }


def _check_invocation(started: float, phase: str) -> None:
    if time.perf_counter() - started > INVOCATION_CAP_SECONDS:
        raise TimeoutError(f"three-path invocation exceeded its 2700-second cap during {phase}")


def current_launch_sha() -> str:
    """Observe the checked-out commit without turning it into a run guard."""
    repo = Path(__file__).resolve().parents[4]
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True,
    ).strip()


def _exposure_line(representation: str, checkpoint: str, updates: int,
                   scales: Mapping[str, float], movement: Mapping[str, float] | None,
                   *, batch_size: int = BATCH_SIZE) -> dict[str, object]:
    return {
        "representation": representation, "checkpoint": checkpoint,
        "updates": updates, "batch_size": batch_size,
        "processed_examples": updates * batch_size, "adam_lr": ADAM_LR,
        "nominal_lr_exposure": updates * ADAM_LR, **scales,
        "parameter_displacement_l2_over_initial_l2": (
            None if movement is None else movement["parameter_displacement_l2_over_initial_l2"]),
        "parameter_displacement_linf_over_initial_linf": (
            None if movement is None else movement["parameter_displacement_linf_over_initial_linf"]),
    }


def projected_arm_seconds() -> float:
    return 3.0 * 736.922 * max(73_728 / 484_096, 12_800 / 204_800, 8_192 / 131_072)


def project_cost(seed: int = SEED) -> dict[str, object]:
    model = CommonHistoryGate(counter_rng_for_namespace(
        LEARNER_NAMESPACE, "gate_initialization", seed,
    ))
    scales = _parameter_scales(_parameter_tensors(model))
    lines = [
        _exposure_line(rep.value, budget.value, updates, scales, None)
        for rep in Representation
        for budget, updates in ((Budget.SHORT, SHORT_UPDATES), (Budget.LONG, LONG_UPDATES))
    ]
    return {
        "object_id": OBJECT_ID, "result_bearing": False,
        "fixed_planning_law": (
            "3 * 736.922 * max(shared_host_steps/484096, "
            "predictor_processed_examples/204800, arm_gate_processed_examples/131072)"),
        "shared_host_steps": 73_728, "predictor_processed_examples": 12_800,
        "arm_gate_processed_examples": 8_192,
        "projected_arm_seconds": projected_arm_seconds(),
        "per_representation_cap_seconds": ARM_CAP_SECONDS,
        "invocation_cap_seconds": INVOCATION_CAP_SECONDS,
        "prospective_exposure_lines": lines,
    }


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


def _sattolo(size: int, rng: np.random.Generator) -> np.ndarray:
    if size < 2:
        raise ValueError("derangement cell needs at least two rows")
    donors = np.arange(size, dtype=np.int64)
    for index in range(size - 1, 0, -1):
        other = int(rng.integers(0, index))
        donors[index], donors[other] = donors[other], donors[index]
    return donors


def derange_packets(rows: tuple[PanelRow, ...], source: PacketDataset, *, seed: int,
                    split_ordinal: int) -> tuple[PacketDataset, list[dict[str, str]]]:
    source.require_rows(rows)
    groups: dict[tuple[str, str, int, float], list[int]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(row.derangement_cell, []).append(index)
    donors = np.empty(len(rows), dtype=np.int64)
    rng = counter_rng_for_namespace(LEARNER_NAMESPACE, "derangement", seed, split_ordinal)
    for indices in groups.values():
        local = _sattolo(len(indices), rng)
        for recipient, donor in enumerate(local):
            donors[indices[recipient]] = indices[int(donor)]
    values = source.values[donors]
    mapping = [
        {"recipient": rows[index].key.text, "donor": rows[int(donor)].key.text}
        for index, donor in enumerate(donors)
    ]
    return PacketDataset(tuple(row.key.text for row in rows), values), mapping


def _advantage(row: PanelRow) -> float:
    replacements = row.g16[1:][row.legal_mask[1:]]
    return float(np.max(replacements) - row.g16[0])


def _source_tape_map() -> dict[int, dict[int, ScenarioTape]]:
    tapes: dict[int, dict[int, ScenarioTape]] = {}
    for slot in range(8):
        batch = build_balanced_tapes(
            replicate=slot, split=Split.EVALUATION, regime="K8", count=64,
            first_episode_index=832, rng_namespace=SOURCE_NAMESPACE,
        )
        tapes[slot] = {tape.spec.episode_index: tape for tape in batch}
    return tapes


def selected_source_manifest() -> list[dict[str, object]]:
    tapes = _source_tape_map()
    return [{
        **address.__dict__,
        "observed_event": tapes[address.source_slot][address.episode_index].spec.event.value,
        "observed_onset": tapes[address.source_slot][address.episode_index].spec.event_onset,
        "observed_cost": tapes[address.source_slot][address.episode_index].spec.replanning_cost,
        "observed_regime": tapes[address.source_slot][address.episode_index].spec.regime.value,
    } for address in SELECTED_ROWS]


def _selected_rows(predictor, *, monitor=lambda: None) -> tuple[
    tuple[PanelRow, ...], tuple[PanelRow, ...], dict[str, dict[str, object]]
]:
    tapes = _source_tape_map()
    monitor()
    train: list[PanelRow] = []
    evaluation: list[PanelRow] = []
    metadata: dict[str, dict[str, object]] = {}
    for address in SELECTED_ROWS:
        monitor()
        tape = tapes[address.source_slot][address.episode_index]
        split = Split.TRAIN if address.split == "TRAIN" else Split.EVALUATION
        row = materialize_common_history_row(
            tape, replicate=address.source_slot, split=split,
            forecast=predictor.packet_forecast,
        )
        if row is None:
            raise RuntimeError(f"selected source row is missing: {address}")
        direct = _advantage(row)
        expected_sign = direct <= -0.01 if address.side == "KEEP" else direct >= 0.01
        if not (tape.spec.event.value == address.event
                and tape.spec.event_onset == address.onset
                and tape.spec.replanning_cost == 4.0
                and row.key.regime == "K8" and row.elapsed_horizon == 4 and expected_sign):
            raise RuntimeError(f"selected source row changed its frozen population fields: {address}")
        target = train if split is Split.TRAIN else evaluation
        target.append(row)
        metadata[row.key.text] = {
            **address.__dict__, "source_split_coordinate": "EVALUATION",
            "direct_advantage": direct, "primitive_time": row.key.primitive_time,
            "agent": row.key.agent, "elapsed_horizon": row.elapsed_horizon,
            "observed_regime": row.key.regime, "observed_cost": float(row.cost),
            "denominator": tape.total_physical_arrivals(),
        }
    train.sort(key=lambda item: item.key.canonical)
    evaluation.sort(key=lambda item: item.key.canonical)
    if len(train) != 48 or len(evaluation) != 16:
        raise RuntimeError("selected population is not exactly 48 TRAIN and 16 EVAL rows")
    return tuple(train), tuple(evaluation), metadata


def _predictor_examples(tapes: Sequence[ScenarioTape], *, monitor) -> tuple:
    examples = []
    for tape in tapes:
        monitor()
        examples.extend(materialize_predictor_examples((tape,)))
    monitor()
    return tuple(sorted(examples, key=lambda item: item.canonical_key))


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


def _train_paths(rows: tuple[PanelRow, ...], packets: Mapping[Representation, PacketDataset],
                 *, seed: int, short_updates: int, long_updates: int,
                 batch_size: int, invocation_started: float) -> tuple[
                     dict[Representation, dict[str, object]], list[dict[str, object]]
                 ]:
    order = np.resize(np.arange(len(rows), dtype=np.int64), long_updates * batch_size)
    outputs: dict[Representation, dict[str, object]] = {}
    exposure: list[dict[str, object]] = []
    initial_reference = None
    for representation in Representation:
        started = time.perf_counter()
        model = CommonHistoryGate(counter_rng_for_namespace(
            LEARNER_NAMESPACE, "gate_initialization", seed,
        ))
        initial_state = canonical_state(model)
        if initial_reference is None:
            initial_reference = initial_state
        elif initial_state != initial_reference:
            raise RuntimeError("representation gate initializations are not byte-identical")
        initial = _parameter_tensors(model)
        scales = _parameter_scales(initial)
        optimizer = torch.optim.Adam(
            model.parameters(), lr=ADAM_LR, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0,
        )
        checkpoints: dict[Budget, CommonHistoryGate] = {}
        for update in range(1, long_updates + 1):
            _check_invocation(invocation_started, f"{representation.value} training")
            begin = (update - 1) * batch_size
            batch = order[begin:begin + batch_size]
            histories, lengths, packet, legal, target = _collate(
                rows, packets[representation].values, batch,
            )
            prediction = model(histories, lengths, packet)
            loss = legal_masked_mse(prediction, target, legal)
            if not bool(torch.isfinite(loss)):
                raise RuntimeError("gate loss became nonfinite")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if any(parameter.grad is not None and not bool(torch.all(torch.isfinite(parameter.grad)))
                   for parameter in model.parameters()):
                raise RuntimeError("gate gradient became nonfinite")
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
            optimizer.step()
            if any(not bool(torch.all(torch.isfinite(parameter))) for parameter in model.parameters()):
                raise RuntimeError("gate parameter became nonfinite")
            if update in (short_updates, long_updates):
                checkpoint = Budget.SHORT if update == short_updates else Budget.LONG
                snapshot = deepcopy(model).eval()
                checkpoints[checkpoint] = snapshot
                movement = _movement(initial, snapshot)
                if checkpoint is Budget.LONG and (
                    not all(math.isfinite(value) for value in movement.values())
                    or any(value <= 0.0 for value in movement.values())
                ):
                    raise RuntimeError("LONG gate movement is zero or nonfinite")
                exposure.append(_exposure_line(
                    representation.value, checkpoint.value, update, scales,
                    movement, batch_size=batch_size,
                ))
            if time.perf_counter() - started > ARM_CAP_SECONDS:
                raise TimeoutError(f"{representation.value} exceeded its 900-second path cap")
        outputs[representation] = {
            "checkpoints": checkpoints, "wall_seconds": time.perf_counter() - started,
            "cyclic_order": order.tolist(),
        }
    return outputs, exposure


def _evaluate(model: CommonHistoryGate, rows: tuple[PanelRow, ...], packets: PacketDataset,
              metadata: Mapping[str, Mapping[str, object]], *, monitor=lambda: None) -> dict[str, object]:
    monitor()
    packets.require_rows(rows)
    lengths = torch.tensor([row.history.shape[0] for row in rows], dtype=torch.int64)
    histories = torch.zeros((len(rows), int(lengths.max()), 42), dtype=torch.float32)
    for index, row in enumerate(rows):
        histories[index, :row.history.shape[0]] = torch.from_numpy(np.array(row.history, copy=True))
    with torch.no_grad():
        predicted = model(histories, lengths, torch.from_numpy(packets.values.copy())).cpu().numpy()
    monitor()
    if not np.all(np.isfinite(predicted)):
        raise RuntimeError("gate evaluation became nonfinite")
    details = []
    by_side = {"KEEP": [], "REPLAN": []}
    exact = {"KEEP": 0, "REPLAN": 0}
    for row, values in zip(rows, predicted):
        monitor()
        selected = select_printed_action(values, row.legal_mask)
        oracle = select_printed_action(row.g16, row.legal_mask)
        regret = native_regret(row.g16, row.legal_mask, selected)
        side = str(metadata[row.key.text]["side"])
        by_side[side].append(regret)
        exact[side] += int(selected == oracle)
        charges = [None if not legal else (0.0 if index == 0 else 0.05 + row.cost)
                   for index, legal in enumerate(row.legal_mask)]
        details.append({
            "row_key": row.key.text, "material_side": side,
            "selected_action": ACTION_ORDER[selected], "selected_action_index": selected,
            "legal_mask": row.legal_mask.tolist(),
            "legal_action_order": [ACTION_ORDER[i] for i in np.flatnonzero(row.legal_mask)],
            "g16": [None if not np.isfinite(value) else float(value) for value in row.g16],
            "first_step_target_charges": charges,
            "common_future_denominator": int(metadata[row.key.text]["denominator"]),
            "oracle_action": ACTION_ORDER[oracle], "oracle_action_index": oracle,
            "native_regret": regret, "exact_action_correct": selected == oracle,
        })
    sides = {
        side: {"row_count": len(by_side[side]), "mean_regret": float(np.mean(by_side[side])),
               "exact_action_count": exact[side]}
        for side in ("KEEP", "REPLAN")
    }
    return {
        "rows": details, "sides": sides,
        "equal_side_regret": 0.5 * (sides["KEEP"]["mean_regret"] + sides["REPLAN"]["mean_regret"]),
    }


def _contrasts(metrics: Mapping[str, Mapping[str, Mapping[str, object]]]) -> dict[str, dict[str, float]]:
    out = {}
    for budget in ("SHORT", "LONG"):
        raw = float(metrics["RAW"][budget]["equal_side_regret"])
        true = float(metrics["TRUE_RESIDUAL"][budget]["equal_side_regret"])
        deranged = float(metrics["CALIBRATED_DERANGEMENT"][budget]["equal_side_regret"])
        out[budget] = {"d_RT": raw - true, "d_DT": deranged - true, "d_RD": raw - deranged}
    return out


def apply_result_rule(metrics: Mapping[str, Mapping[str, Mapping[str, object]]],
                      validity_issues: Sequence[str] = ()) -> str:
    if validity_issues:
        return "INVALID_INCOMPLETE_NO_SCIENTIFIC_BRANCH"
    raw_long = metrics["RAW"]["LONG"]["sides"]
    competent = all(
        int(raw_long[side]["row_count"]) == 8
        and int(raw_long[side]["exact_action_count"]) >= 6
        and float(raw_long[side]["mean_regret"]) <= 0.005
        for side in ("KEEP", "REPLAN")
    )
    c = _contrasts(metrics)
    r = lambda path, budget: float(metrics[path][budget]["equal_side_regret"])
    long_pairwise = (abs(c["LONG"]["d_RT"]), abs(c["LONG"]["d_DT"]), abs(c["LONG"]["d_RD"]))
    if (competent and c["SHORT"]["d_RT"] > DELTA and c["SHORT"]["d_DT"] > DELTA
            and all(value <= DELTA for value in long_pairwise)
            and r("RAW", "SHORT") - r("RAW", "LONG") > DELTA
            and r("TRUE_RESIDUAL", "LONG") - r("TRUE_RESIDUAL", "SHORT") <= DELTA):
        return "BR-A — ALIGNED_SHORT_ONLY"
    if (competent and all(c[budget][name] > DELTA
                          for budget in ("SHORT", "LONG") for name in ("d_RT", "d_DT"))):
        return "BR-B — PERSISTENT_ALIGNED_SIGNAL"
    if (competent and c["SHORT"]["d_RT"] > DELTA and c["SHORT"]["d_RD"] > DELTA
            and abs(c["SHORT"]["d_DT"]) <= DELTA):
        return "BR-C — GENERIC_PREPROCESSING"
    if competent and c["SHORT"]["d_RT"] <= DELTA and c["LONG"]["d_RT"] <= DELTA:
        return "BR-D — NO_TRUE_GAIN"
    if not competent:
        return "BR-E — COMPARATOR_WEAK"
    return "BR-F — MIXED_OR_UNRESOLVED"


def _peak_rss_bytes() -> int | None:
    if not hasattr(ctypes, "windll"):
        return None
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong),
            ("peak_working_set", ctypes.c_size_t), ("working_set", ctypes.c_size_t),
            ("quota_peak_paged", ctypes.c_size_t), ("quota_paged", ctypes.c_size_t),
            ("quota_peak_nonpaged", ctypes.c_size_t), ("quota_nonpaged", ctypes.c_size_t),
            ("pagefile", ctypes.c_size_t), ("peak_pagefile", ctypes.c_size_t),
        ]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        return None
    return int(counters.peak_working_set)


def _toy_population() -> tuple[tuple[PanelRow, ...], tuple[PanelRow, ...], CalibrationTable,
                               dict[str, dict[str, object]]]:
    metadata: dict[str, dict[str, object]] = {}
    panels = []
    for split in (Split.TRAIN, Split.EVALUATION):
        rows = []
        count = 6
        for index in range(count):
            side = "KEEP" if index % 2 == 0 else "REPLAN"
            key = RowKey(0, split, "K8", index + (0 if split is Split.TRAIN else 100), 60, 0)
            g16 = np.full(8, np.nan, dtype=np.float64)
            g16[:2] = (0.02, 0.0) if side == "KEEP" else (0.0, 0.02)
            row = PanelRow(
                key=key, cost=4.0, elapsed_horizon=4,
                history=np.full((3, 42), index / 10.0, dtype=np.float32),
                target=np.full(8, 0.1 * index, dtype=np.float32),
                mean=np.zeros(8, dtype=np.float32), cholesky=np.eye(8, dtype=np.float32),
                legal_mask=np.asarray((True, True, False, False, False, False, False, False)),
                g16=g16, logged_action=0, tape_record=("toy", split.value, index),
            )
            rows.append(row)
            metadata[key.text] = {"side": side, "denominator": 1}
        panels.append(tuple(rows))
    support = np.tile(np.linspace(-2.0, 2.0, 16, dtype=np.float32), (8, 1))
    return panels[0], panels[1], CalibrationTable(support), metadata


def run_experiment(output_dir: str | Path, *, admission_receipt: str | Path,
                   argv: Sequence[str], seed: int = SEED,
                   toy: bool = False) -> dict[str, object]:
    if seed != SEED:
        raise ValueError("this object has fixed learner seed 0")
    admission = validate_admission_receipt(admission_receipt)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    launch_sha = current_launch_sha()
    monitor = lambda: _check_invocation(started, "active stage")
    if toy:
        train_rows, eval_rows, calibration, metadata = _toy_population()
        predictor_report = {"tapes": 0, "examples": 0, "updates": 0, "processed_examples": 0}
        calibration_report = {"tapes": 0, "example_count": 0}
        short_updates, long_updates, batch_size = 1, 2, 4
        selected_reproduction = []
    else:
        monitor()
        predictor_tapes = (
            build_balanced_tapes(replicate=0, split=Split.PREDICTOR_FIT, regime="K4", count=64,
                                 first_episode_index=0, rng_namespace=LEARNER_NAMESPACE)
            + build_balanced_tapes(replicate=0, split=Split.PREDICTOR_FIT, regime="K8", count=64,
                                   first_episode_index=64, rng_namespace=LEARNER_NAMESPACE)
        )
        predictor_examples = _predictor_examples(predictor_tapes, monitor=monitor)
        monitor()
        predictor, predictor_audit = fit_fresh_predictor(
            predictor_examples, replicate=seed, updates=100, batch_size=128,
            rng_namespace=LEARNER_NAMESPACE, resource_monitor=monitor,
        )
        monitor()
        calibration_tapes = (
            canonical_calibration_tapes(replicate=0, regime="K4", rng_namespace=LEARNER_NAMESPACE)
            + canonical_calibration_tapes(replicate=0, regime="K8", rng_namespace=LEARNER_NAMESPACE)
        )
        calibration_examples = _predictor_examples(calibration_tapes, monitor=monitor)
        monitor()
        def calibration_forecast(*args):
            monitor()
            return predictor.packet_forecast(*args)
        calibration, calibration_report = fit_calibration_from_examples(
            calibration_examples, calibration_forecast,
        )
        monitor()
        calibration_report = {
            key: value for key, value in calibration_report.items() if key != "table_record"
        }
        calibration_report["tapes"] = 64
        predictor_report = {
            "tapes": 128, "examples": predictor_audit.examples,
            "updates": predictor_audit.updates,
            "processed_examples": predictor_audit.processed_examples,
            "K4_episode_indices": [0, 63], "K8_episode_indices": [64, 127],
        }
        train_rows, eval_rows, metadata = _selected_rows(predictor, monitor=monitor)
        short_updates, long_updates, batch_size = SHORT_UPDATES, LONG_UPDATES, BATCH_SIZE
        selected_reproduction = [metadata[row.key.text] for row in (*train_rows, *eval_rows)]
    train_views = construct_packet_views(train_rows, calibration)
    eval_views = construct_packet_views(eval_rows, calibration)
    train_deranged, train_map = derange_packets(
        train_rows, train_views.true_residual_dataset, seed=seed, split_ordinal=0,
    )
    eval_deranged, eval_map = derange_packets(
        eval_rows, eval_views.true_residual_dataset, seed=seed, split_ordinal=1,
    )
    train_packets = {
        Representation.RAW: train_views.raw_dataset,
        Representation.TRUE_RESIDUAL: train_views.true_residual_dataset,
        Representation.CALIBRATED_DERANGEMENT: train_deranged,
    }
    eval_packets = {
        Representation.RAW: eval_views.raw_dataset,
        Representation.TRUE_RESIDUAL: eval_views.true_residual_dataset,
        Representation.CALIBRATED_DERANGEMENT: eval_deranged,
    }
    trained, exposure = _train_paths(
        train_rows, train_packets, seed=seed, short_updates=short_updates,
        long_updates=long_updates, batch_size=batch_size, invocation_started=started,
    )
    metrics: dict[str, dict[str, object]] = {}
    for representation in Representation:
        metrics[representation.value] = {}
        checkpoints = trained[representation]["checkpoints"]
        evaluation_started = time.perf_counter()
        for budget in Budget:
            metrics[representation.value][budget.value] = _evaluate(
                checkpoints[budget], eval_rows, eval_packets[representation], metadata,
                monitor=monitor,
            )
            trajectory_wall = (
                float(trained[representation]["wall_seconds"])
                + time.perf_counter() - evaluation_started
            )
            if trajectory_wall > ARM_CAP_SECONDS:
                raise TimeoutError(
                    f"{representation.value} exceeded its 900-second training-plus-evaluation cap"
                )
        trained[representation]["evaluation_wall_seconds"] = (
            time.perf_counter() - evaluation_started
        )
    validity_issues = [] if not toy else ["TOY_SMOKE_NOT_A_SCIENTIFIC_POPULATION"]
    result_branch = apply_result_rule(metrics, validity_issues)
    peak = _peak_rss_bytes()
    prospective_cost = project_cost(seed)
    cost_law = {
        **prospective_cost,
        "measured_invocation_wall_seconds": 0.0,
        "measured_wall_seconds_per_gate_update": {
            representation.value: float(trained[representation]["wall_seconds"]) / long_updates
            for representation in Representation
        },
        "measured_representation_wall_seconds": {
            representation.value: (
                float(trained[representation]["wall_seconds"])
                + float(trained[representation]["evaluation_wall_seconds"])
            )
            for representation in Representation
        },
    }
    resources = {
        "admission": admission, "wall_seconds": 0.0, "peak_rss_bytes": peak,
        "status": "measured" if peak is not None else "resources_unmeasured",
    }
    summary = {
        "object_id": OBJECT_ID, "seed": seed, "toy": toy, "result_branch": result_branch,
        "validity_issues": validity_issues, "launch_sha": launch_sha, "exact_argv": list(argv),
        "source_law": {
            "rng_namespace": SOURCE_NAMESPACE, "source_split_coordinate": "EVALUATION",
            "regime": "K8", "source_slots": list(range(8)), "count_per_source_slot": 64,
            "first_episode_index": 832, "old_result_json_read": False,
            "legacy_confirmation_namespace_read_or_instantiated": False,
        },
        "selected_population": {"train_rows": len(train_rows), "evaluation_rows": len(eval_rows),
                                "reproduction": selected_reproduction},
        "predictor": predictor_report, "calibration": calibration_report,
        "derangement_donor_maps": {"TRAIN": train_map, "EVALUATION": eval_map},
        "action_order": list(ACTION_ORDER), "representations": metrics,
        "contrasts": _contrasts(metrics), "exposure_lines": exposure,
        "work_counts": {
            "environment_transitions": (0 if toy else 128 * 256 + 64 * 256
                                         + sum(row.key.primitive_time for row in (*train_rows, *eval_rows))),
            "common_future_branch_steps": (0 if toy else sum(
                int(np.count_nonzero(row.legal_mask)) * 16 for row in (*train_rows, *eval_rows))),
            "gate_updates_per_representation": long_updates,
            "processed_examples_per_representation": long_updates * batch_size,
            "evaluation_rows_per_representation": 2 * len(eval_rows),
        },
        "cost_law": cost_law,
        "resources": resources,
    }
    json.dumps(summary, indent=2, ensure_ascii=False)
    wall = time.perf_counter() - started
    _check_invocation(started, "final summary")
    cost_law["measured_invocation_wall_seconds"] = wall
    resources["wall_seconds"] = wall
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    return summary


def build_lower_domain_tape() -> ScenarioTape:
    hot = np.zeros(HORIZON, dtype=np.int8)
    hot[45] = 1
    return ScenarioTape(
        spec=ScenarioSpec(0, 0, Regime.K8, EventClass.NONE, 50, 4.0),
        initial_locations=np.asarray((Location.L, Location.R, Location.BASE, Location.BASE)),
        initial_hot_lane=Lane.L, arrival_hot_coin=hot,
        arrival_cold_coin=np.zeros(HORIZON, dtype=np.int8),
        relay_capacity_coin=np.zeros((HORIZON, 2), dtype=np.int8),
        option_uniform=np.full((HORIZON, 4), 0.5, dtype=np.float64),
        rate_control_uniform=np.full((HORIZON, 4), 0.5, dtype=np.float64),
    )


def observe_lower_domain() -> dict[str, object]:
    tape = build_lower_domain_tape()
    scan = scan_common_history_boundary(tape, replicate=0, split=Split.EVALUATION)
    row = materialize_common_history_row(
        tape, replicate=0, split=Split.EVALUATION,
        forecast=lambda *_: (np.zeros(8, dtype=np.float32), np.eye(8, dtype=np.float32)),
    )
    if row is None or scan.primitive_time is None or scan.agent is None:
        raise RuntimeError("lower-domain tape produced no retained boundary")
    host = ServiceRelayHost(tape)
    for _ in range(scan.primitive_time):
        host.advance(scripted_decisions(host))
    previous = Option(int(host.state.options[scan.agent]))
    return {
        "result_bearing": False, "event": tape.spec.event.value, "onset": tape.spec.event_onset,
        "cost": tape.spec.replanning_cost, "initial_locations": [Location(int(v)).name for v in tape.initial_locations],
        "initial_hot_lane": tape.initial_hot_lane.name, "sole_hot_coin_one_time": 45,
        "all_other_arrivals_and_capacity_zero": True, "uniforms": 0.5,
        "boundary_time": scan.primitive_time, "agent": scan.agent,
        "previous_option": previous.label, "target": row.target.tolist(),
        "target_energy": float(host.state.energies[scan.agent]),
        "target_energy_normalized": float(row.target[6]),
        "legal_actions": [ACTION_ORDER[i] for i in np.flatnonzero(row.legal_mask)],
        "g16": [None if not np.isfinite(value) else float(value) for value in row.g16],
        "advantage": _advantage(row), "denominator": tape.total_physical_arrivals(),
    }
