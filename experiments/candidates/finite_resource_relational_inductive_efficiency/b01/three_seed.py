"""One-root invocation for the frozen FRRIE B01 three-seed panel."""

from __future__ import annotations

import argparse
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..arms import initialize_paired_arms
from ..policy import make_actor_critic
from ..rng import AddressedRNG
from ..state_codec import encode_optimizer_state
from ..training import make_optimizer
from .batch_collector import _collect_b01_arm_update
from .constants import LEARNED_ARMS, ROOT_LABELS, TEST_SEED_LABEL
from .contract import B01ContractError, canonical_json_bytes
from .native_batch import B01NativeBatchEnvironment
from .r128_smoke import (
    _TimedTrainer, _ToyPolicy, _build_adapter, _enforce_time_cap, _launch_sha,
    _load_admission, _peak_rss_bytes, _production_training_inputs, _uniform_actions,
)
from .seed_packet import read_production_seed_packet, read_test_seed_packet
from .tapes import evaluation_tape
from .trainer import PairedB01Trainer

OBJECT_ID = "FRRIE-B01-THREE-SEED-SECTION11-20260904"
PRODUCTION_UPDATES = 512
PRODUCTION_CHECKPOINTS = (0, 32, 64, 128, 256, 512)
PRODUCTION_ROSTERS = (6, 9, 15, 21)
PRODUCTION_EVAL_EPISODES = 256
INTERVENTIONS = ("INTACT", "SEMANTIC_COLUMN_ROTATE")
HORIZON = 12
NativeEnvironment = B01NativeBatchEnvironment
PRODUCTION_ROOT_HEX = {
    ROOT_LABELS[0]: "be5f067f01c0f5c75a52d125599b40dc1dcce3687bcf3f9d42fce550e2354916",
    ROOT_LABELS[1]: "4eb956af014e3c1e89b38e67e6bd46d53b7b9f41ac2698d3187cdee3b11c8e10",
    ROOT_LABELS[2]: "5aca87f3fd99d00191e73330d611092a30cbc4ba73ca0a032c12be990f00d428",
}


def exposure_record(updates: int) -> dict[str, Any]:
    nominal = round(updates * 0.0003, 10)
    ratio = round(nominal / 0.05, 10)
    return {
        "updates": updates, "adam_lr": 0.0003, "nominal_lr_exposure": nominal,
        "init_half_range": 0.05, "nominal_exposure_over_init_half_range": ratio,
        "line": (
            f"updates={updates}; adam_lr=0.0003; nominal_lr_exposure={nominal:.4f}; "
            f"init_half_range=0.05; nominal_exposure_over_init_half_range={ratio:.3f}"
        ),
    }


def cost_config(
    updates: int, checkpoints: Sequence[int], rosters: Sequence[int], episodes: int,
) -> dict[str, Any]:
    training = 4_928 * updates
    evaluation = len(checkpoints) * len(rosters) * len(INTERVENTIONS) * episodes * HORIZON
    uniform_cells = sum(roster in (9, 15) for roster in rosters)
    uniform = uniform_cells * episodes * HORIZON
    learned_cells = 2 * len(checkpoints) * len(rosters) * len(INTERVENTIONS)
    eval_episodes = learned_cells * episodes + uniform_cells * episodes
    return {
        "updates": updates, "checkpoints": list(checkpoints), "rosters": list(rosters),
        "interventions": list(INTERVENTIONS), "evaluation_episodes_per_cell": episodes,
        "learned_training_per_arm": training, "learned_evaluation_per_arm": evaluation,
        "learned_total_per_arm": training + evaluation, "shared_uniform": uniform,
        "factual_native_slots_per_arm": 768 * updates,
        "factual_suffix_audit_slots_per_arm": 1_248 * updates,
        "nonfactual_suffix_slots_per_arm": 2_912 * updates,
        "counterfactual_audit_slots_per_arm": 4_160 * updates,
        "invocation": 2 * (training + evaluation) + uniform,
        "optimizer_steps_per_arm": updates, "learned_cells": learned_cells,
        "uniform_cells": uniform_cells, "cells": learned_cells + uniform_cells,
        "evaluation_episodes_total": learned_cells * episodes + uniform_cells * episodes,
        "evaluation_transitions_total": eval_episodes * HORIZON,
        "factual_learner_transitions_per_arm": 64 * updates * HORIZON,
        "factual_learner_transitions_total": 128 * updates * HORIZON,
    }


def classify_seed(rule_inputs: Mapping[str, Any], *, test_only: bool = False) -> str:
    if test_only:
        return "TEST_ONLY_NON_RESULT"
    true_fields = (
        "complete", "admission_valid", "exposure_present", "paired_information_work_equal",
        "precontact_full_state_equal", "precontact_evaluation_equal",
        "evaluation_preserved_state", "same_evaluation_tapes",
    )
    positive_fields = (
        "learner_transitions", "training_episodes", "backward_calls", "adam_steps",
        "evaluation_episodes", "evaluation_transitions",
    )
    if any(rule_inputs.get(name) is not True for name in true_fields):
        return "B01_INVALID"
    if any(type(rule_inputs.get(name)) is not int or rule_inputs[name] <= 0
           for name in positive_fields):
        return "B01_INVALID"
    return "B01_SEED_VALID_DIRECT"


def _seed_root(path: Path, label: str, *, test_only: bool) -> tuple[bytes, dict[str, Any]]:
    if not path.is_absolute():
        raise B01ContractError("seed packet path must be absolute")
    if test_only:
        packet = read_test_seed_packet(path)
        if label != TEST_SEED_LABEL:
            raise B01ContractError("TEST run requires the canonical first TEST label")
    else:
        packet = read_production_seed_packet(path)
        if label not in ROOT_LABELS[:3]:
            raise B01ContractError("production seed label must be one of ordered roots 001..003")
    index = packet["labels"].index(label)
    root_hex = packet["roots_hex"][index]
    if not test_only and root_hex != PRODUCTION_ROOT_HEX[label]:
        raise B01ContractError("selected production root differs from the frozen literal bytes")
    return bytes.fromhex(root_hex), packet


def _actions(
    model: Any, observations: np.ndarray, roles: np.ndarray, uniforms: np.ndarray,
    hidden: Any, *, rotated: bool, shadow_tv: bool,
) -> tuple[np.ndarray, Any, float, int]:
    import torch
    observations_t = torch.from_numpy(np.ascontiguousarray(observations))
    roles_t = torch.from_numpy(np.ascontiguousarray(roles))
    actor = model.actor_step_batch(
        observations_t, roles_t, hidden, rotate_columns=rotated,
    )
    tv_sum = 0.0
    tv_count = 0
    if shadow_tv:
        shadow = model.actor_step_batch(
            observations_t, roles_t, hidden, rotate_columns=True,
        )
        tv_sum = float((0.5 * (actor.probabilities - shadow.probabilities).abs().sum(dim=2))
                       .to(torch.float64).sum().item())
        tv_count = int(actor.probabilities.shape[0] * actor.probabilities.shape[1])
    uniforms_t = torch.from_numpy(np.ascontiguousarray(uniforms, dtype=np.float32))
    actions = model.actions_from_uniforms_batch(actor.probabilities, uniforms_t)
    return actions.numpy(), actor.hidden, tv_sum, tv_count


def _evaluate_cell(
    adapter: Any, model: Any | None, *, tapes: tuple[Any, ...], intervention: str,
    measure_shadow_tv: bool = False,
) -> tuple[dict[str, Any], tuple[Any, ...]]:
    roster, episodes = tapes[0].roster, len(tapes)
    before = None if model is None else model.parameter_bytes()
    sums = {name: 0 for name in (
        "duplicate", "expired", "collision", "empty_radio", "radio_actions",
        "waste_actions", "successful_deliveries",
    )}
    action_counts = [0] * 6
    returns: list[float] = []
    dw: list[int] = []
    de: list[int] = []
    waste: list[float] = []
    action_trace: list[bytes] = []
    terminal_trace: list[Any] = []
    tv_sum, tv_count = 0.0, 0
    for start in range(0, episodes, 32):
        batch_tapes = tapes[start:min(start + 32, episodes)]
        environment = NativeEnvironment(adapter, roster=roster, lanes=len(batch_tapes))
        environment.reset(batch_tapes)
        hidden: Any = None
        real_model = model is not None and not hasattr(model, "select_actions")
        if real_model:
            import torch
            hidden = torch.zeros((len(batch_tapes), roster, 64), dtype=torch.float32)
            was_training = bool(model.training)
            model.eval()
        else:
            was_training = False
        terminal = None
        try:
            for slot in range(HORIZON):
                frame = environment.observe()
                uniforms = np.ascontiguousarray(
                    np.stack([tape.action_uniform[slot] for tape in batch_tapes]), dtype=np.float32,
                )
                if model is None:
                    actions = _uniform_actions(frame.legal_masks, uniforms)
                elif hasattr(model, "select_actions"):
                    actions, hidden = model.select_actions(frame.legal_masks, uniforms, hidden)
                else:
                    import torch
                    with torch.no_grad():
                        actions, hidden, added_tv, added_n = _actions(
                            model, frame.observations, frame.roles, uniforms, hidden,
                            rotated=intervention == "SEMANTIC_COLUMN_ROTATE",
                            shadow_tv=measure_shadow_tv,
                        )
                    tv_sum += added_tv
                    tv_count += added_n
                terminal = environment.step(actions)
                action_trace.append(np.asarray(actions, dtype=np.int64).tobytes(order="C"))
                counts = np.bincount(np.asarray(actions).reshape(-1), minlength=6)
                action_counts = [left + int(right) for left, right in zip(action_counts, counts)]
        finally:
            if real_model:
                model.train(was_training)
        if terminal is None or terminal.terminals != (True,) * len(batch_tapes):
            raise B01ContractError("evaluation did not terminate every native lane")
        terminal_trace.append(tuple(
            (float(value).hex(), tuple(asdict(primitive).items()))
            for value, primitive in zip(terminal.returns, terminal.primitives)
        ))
        returns.extend(map(float, terminal.returns))
        for primitive in terminal.primitives:
            direct = asdict(primitive)
            dw.append(int(direct["dw"]))
            de.append(int(direct["de"]))
            waste.append(float(direct["waste"]))
            for name in sums:
                sums[name] += int(direct[name])
    values = {
        "J": float(np.mean(returns)), "D_W": float(np.mean(dw)),
        "D_E": float(np.mean(de)), "min_D": float(np.mean(np.minimum(dw, de))),
        "WASTE": float(np.mean(waste)), "action_counts": action_counts,
        "native_event_counts": sums, "episodes": episodes,
        "transitions": episodes * HORIZON, "environment_slots": episodes * HORIZON,
        "model_bytes_preserved": model is None or model.parameter_bytes() == before,
        "V": tv_sum / tv_count if tv_count else None,
    }
    return values, (tuple(action_trace), tuple(terminal_trace))


def _cell(
    arm: str, checkpoint: int | None, roster: int, intervention: str,
    values: Mapping[str, Any],
) -> dict[str, Any]:
    return {"arm": arm, "checkpoint": checkpoint, "roster": roster,
            "intervention": intervention, **values}


def execute(
    *, output_root: Path, seed_packet: Path, admission_receipt: Path, seed_label: str,
    test_only: bool, updates: int, checkpoints: Sequence[int], rosters: Sequence[int],
    eval_episodes: int,
) -> dict[str, Any]:
    if not all(path.is_absolute() for path in (output_root, seed_packet, admission_receipt)):
        raise B01ContractError("output, seed packet, and admission paths must be absolute")
    admission = _load_admission(admission_receipt)
    started = time.perf_counter()
    torch_threads = None
    if not test_only:
        import torch
        torch.set_num_threads(1)
        torch_threads = torch.get_num_threads()
    root, packet = _seed_root(seed_packet, seed_label, test_only=test_only)
    evaluation_tapes = {
        roster: tuple(evaluation_tape(root, seed_label=seed_label, roster=roster, episode=i)
                      for i in range(eval_episodes))
        for roster in rosters
    }
    launch_sha = _launch_sha()
    output_root.mkdir(parents=True, exist_ok=True)
    adapter = _build_adapter()
    cells: list[dict[str, Any]] = []
    traces: dict[tuple[str, int, int, str], tuple[Any, ...]] = {}
    learned_wall = {arm: 0.0 for arm in LEARNED_ARMS}
    training_slots = {arm: 0 for arm in LEARNED_ARMS}
    factual_slots = {arm: 0 for arm in LEARNED_ARMS}
    suffix_audit_slots = {arm: 0 for arm in LEARNED_ARMS}
    nonfactual_slots = {arm: 0 for arm in LEARNED_ARMS}
    backward = {arm: 0 for arm in LEARNED_ARMS}
    adam = {arm: 0 for arm in LEARNED_ARMS}
    factual_episodes = {arm: 0 for arm in LEARNED_ARMS}
    optimizer_wall = {arm: 0.0 for arm in LEARNED_ARMS}
    paired_assertions = precontact_assertions = 0
    eval_preserved = precontact_eval_equal = True
    tape_uses = {roster: 0 for roster in rosters}
    uniform: dict[int, dict[str, Any]] = {}
    for roster in (9, 15):
        if roster in evaluation_tapes:
            uniform[roster], _ = _evaluate_cell(
                adapter, None, tapes=evaluation_tapes[roster], intervention="INTACT",
            )
            tape_uses[roster] += 1
            cells.append(_cell("UNIFORM_LEGAL", None, roster, "INTACT", uniform[roster]))
    _enforce_time_cap(started, learned_wall)

    if test_only:
        models = {arm: _ToyPolicy(arm) for arm in LEARNED_ARMS}
        initial = {arm: models[arm].parameter_bytes() for arm in LEARNED_ARMS}
        projection = {
            "first_tight_contact_update": None, "precontact_full_state_equal": True,
            "tight_projection_changed_coordinates": 0, "wide_boundary_contact": False,
            "maximum_tight_overshoot": 0.0, "cumulative_tight_displacement": 0.0,
        }
    else:
        phy, edge = initialize_paired_arms(AddressedRNG(root), seed_label)
        models = {"PHY_TRUST": make_actor_critic(phy), "EDGE_FLEX": make_actor_critic(edge)}
        optimizers = {arm: make_optimizer(models[arm]) for arm in LEARNED_ARMS}
        paired = PairedB01Trainer(models, optimizers)
        timed = {arm: _TimedTrainer(paired.trainers[arm]) for arm in LEARNED_ARMS}
        paired.trainers.update(timed)
        initial = {arm: models[arm].parameter_bytes() for arm in LEARNED_ARMS}

    for update in range(updates + 1):
        if update in set(checkpoints):
            for arm in LEARNED_ARMS:
                before_opt = None if test_only else encode_optimizer_state(models[arm], optimizers[arm])
                arm_started = time.perf_counter()
                for roster in rosters:
                    for intervention in INTERVENTIONS:
                        values, trace = _evaluate_cell(
                            adapter, models[arm], tapes=evaluation_tapes[roster],
                            intervention=intervention,
                            measure_shadow_tv=(arm == "PHY_TRUST" and roster in (6, 21)
                                               and intervention == "INTACT"),
                        )
                        tape_uses[roster] += 1
                        cells.append(_cell(arm, update, roster, intervention, values))
                        traces[(arm, update, roster, intervention)] = trace
                        eval_preserved = eval_preserved and values["model_bytes_preserved"]
                learned_wall[arm] += time.perf_counter() - arm_started
                if not test_only:
                    eval_preserved = eval_preserved and (
                        encode_optimizer_state(models[arm], optimizers[arm]) == before_opt)
            contact = None if test_only else paired.first_tight_contact_update
            if contact is None:
                equal = all(
                    traces[("PHY_TRUST", update, roster, intervention)]
                    == traces[("EDGE_FLEX", update, roster, intervention)]
                    for roster in rosters for intervention in INTERVENTIONS
                )
                precontact_eval_equal = precontact_eval_equal and equal
                if not equal:
                    raise B01ContractError("paired evaluation differed before tight contact")
            _enforce_time_cap(started, learned_wall)
        if update == updates:
            break
        number = update + 1
        if test_only:
            for arm in LEARNED_ARMS:
                models[arm].update()
                training_slots[arm] += 4_928
                factual_slots[arm] += 768
                suffix_audit_slots[arm] += 1_248
                nonfactual_slots[arm] += 2_912
                factual_episodes[arm] += 64
                backward[arm] += 1
                adam[arm] += 1
        else:
            training_tapes, origins = _production_training_inputs(root, seed_label, number)
            batches = {}
            for arm in LEARNED_ARMS:
                arm_started = time.perf_counter()
                collected = _collect_b01_arm_update(
                    model=models[arm], adapter=adapter, tapes=training_tapes, origins=origins,
                    update=number, allowed_seed_labels=(seed_label,),
                )
                learned_wall[arm] += time.perf_counter() - arm_started
                batches[arm] = collected.batch
                training_slots[arm] += collected.audit.total_environment_slots
                factual_slots[arm] += collected.audit.factual_slots
                suffix_audit_slots[arm] += collected.audit.factual_suffix_audit_slots
                nonfactual_slots[arm] += collected.audit.nonfactual_suffix_slots
                factual_episodes[arm] += collected.audit.factual_episodes
            was_precontact = paired.first_tight_contact_update is None
            before_wall = {arm: timed[arm].wall_seconds for arm in LEARNED_ARMS}
            receipts = paired.update(batches, update=number)
            paired_assertions += 1
            precontact_assertions += int(was_precontact)
            for arm in LEARNED_ARMS:
                elapsed = timed[arm].wall_seconds - before_wall[arm]
                learned_wall[arm] += elapsed
                optimizer_wall[arm] += elapsed
                backward[arm] += receipts[arm].backward_calls
                adam[arm] += receipts[arm].adam_steps
        _enforce_time_cap(started, learned_wall)

    if test_only:
        first_contact, precontact_state_equal = None, True
    else:
        projection = paired.projection_audit()
        first_contact = projection["first_tight_contact_update"]
        precontact_state_equal = projection["precontact_full_state_equal"]
    distances = {
        arm: (0.0 if test_only else float(np.max(np.abs(
            np.frombuffer(models[arm].parameter_bytes(), dtype="<f4")
            - np.frombuffer(initial[arm], dtype="<f4")
        ))) / 0.05)
        for arm in LEARNED_ARMS
    }
    descriptors = []
    for checkpoint in checkpoints:
        for roster in rosters:
            rows = {(row["arm"], row["intervention"]): row for row in cells
                    if row["checkpoint"] == checkpoint and row["roster"] == roster}
            d_intact = rows[("PHY_TRUST", "INTACT")]["J"] - rows[("EDGE_FLEX", "INTACT")]["J"]
            d_rotate = (rows[("PHY_TRUST", "SEMANTIC_COLUMN_ROTATE")]["J"]
                        - rows[("EDGE_FLEX", "SEMANTIC_COLUMN_ROTATE")]["J"])
            descriptors.append({
                "checkpoint": checkpoint, "roster": roster, "d_u": d_intact,
                "e_u": (rows[("EDGE_FLEX", "INTACT")]["J"] - uniform[roster]["J"]
                        if roster in uniform else None),
                "I_u": d_intact - d_rotate if roster in (6, 21) else None,
                "V_u": rows[("PHY_TRUST", "INTACT")]["V"] if roster in (6, 21) else None,
            })

    costs = cost_config(updates, checkpoints, rosters, eval_episodes)
    eval_episodes_total = sum(row["episodes"] for row in cells)
    eval_transitions_total = sum(row["transitions"] for row in cells)
    expected_uses = {roster: 2 * len(checkpoints) * len(INTERVENTIONS)
                     + int(roster in (9, 15)) for roster in rosters}
    same_tapes = tape_uses == expected_uses
    expected_precontact = updates if test_only or first_contact is None else first_contact
    paired_work = test_only or (
        paired_assertions == updates and precontact_assertions == expected_precontact
        and all(len(set(values.values())) == 1 for values in (
            training_slots, factual_slots, suffix_audit_slots, nonfactual_slots,
        ))
    )
    counterfactual_audit_slots = {
        arm: suffix_audit_slots[arm] + nonfactual_slots[arm] for arm in LEARNED_ARMS
    }
    observed = {
        "updates": updates if test_only else paired_assertions,
        "factual_episodes_per_arm": factual_episodes,
        "training_slots_per_arm": training_slots, "backward_per_arm": backward,
        "factual_native_slots_per_arm": factual_slots,
        "factual_suffix_audit_slots_per_arm": suffix_audit_slots,
        "nonfactual_suffix_slots_per_arm": nonfactual_slots,
        "counterfactual_audit_slots_per_arm": counterfactual_audit_slots,
        "adam_per_arm": adam, "cells": len(cells),
        "learned_cells": sum(row["arm"] in LEARNED_ARMS for row in cells),
        "uniform_cells": sum(row["arm"] == "UNIFORM_LEGAL" for row in cells),
        "evaluation_episodes": eval_episodes_total,
        "evaluation_transitions": eval_transitions_total, "descriptors": len(descriptors),
        "tape_uses": tape_uses, "cost_config": costs, "torch_threads": torch_threads,
        "evaluation_preserved": eval_preserved, "paired_information_work_equal": paired_work,
        "precontact_state_equal": precontact_state_equal,
        "precontact_evaluation_equal": precontact_eval_equal,
        "learner_transitions_per_arm": {
            arm: factual_episodes[arm] * HORIZON for arm in LEARNED_ARMS},
    }
    if test_only:
        complete = True
        completion = {"complete": True, "status": "TEST_ONLY_NON_RESULT", "observed": observed}
    else:
        expected = {
            "updates": 512,
            "factual_episodes_per_arm": {arm: 32_768 for arm in LEARNED_ARMS},
            "training_slots_per_arm": {arm: 2_523_136 for arm in LEARNED_ARMS},
            "factual_native_slots_per_arm": {arm: 393_216 for arm in LEARNED_ARMS},
            "factual_suffix_audit_slots_per_arm": {arm: 638_976 for arm in LEARNED_ARMS},
            "nonfactual_suffix_slots_per_arm": {arm: 1_490_944 for arm in LEARNED_ARMS},
            "counterfactual_audit_slots_per_arm": {arm: 2_129_920 for arm in LEARNED_ARMS},
            "backward_per_arm": {arm: 512 for arm in LEARNED_ARMS},
            "adam_per_arm": {arm: 512 for arm in LEARNED_ARMS}, "cells": 98,
            "learned_cells": 96, "uniform_cells": 2, "evaluation_episodes": 25_088,
            "evaluation_transitions": 301_056, "descriptors": 24,
            "tape_uses": {6: 24, 9: 25, 15: 25, 21: 24},
            "cost_config": cost_config(
                PRODUCTION_UPDATES, PRODUCTION_CHECKPOINTS, PRODUCTION_ROSTERS,
                PRODUCTION_EVAL_EPISODES,
            ),
            "torch_threads": 1, "evaluation_preserved": True,
            "paired_information_work_equal": True, "precontact_state_equal": True,
            "precontact_evaluation_equal": True,
            "learner_transitions_per_arm": {arm: 393_216 for arm in LEARNED_ARMS},
        }
        checks = {name: observed[name] == value for name, value in expected.items()}
        complete = all(checks.values())
        completion = {"complete": complete, "checks": checks,
                      "expected": expected, "observed": observed}
    rule_inputs = {
        "complete": complete, "admission_valid": True, "exposure_present": True,
        "paired_information_work_equal": paired_work,
        "precontact_full_state_equal": precontact_state_equal,
        "precontact_evaluation_equal": precontact_eval_equal,
        "evaluation_preserved_state": eval_preserved, "same_evaluation_tapes": same_tapes,
        "learner_transitions": sum(factual_episodes.values()) * HORIZON,
        "training_episodes": sum(factual_episodes.values()),
        "backward_calls": sum(backward.values()), "adam_steps": sum(adam.values()),
        "evaluation_episodes": eval_episodes_total,
        "evaluation_transitions": eval_transitions_total,
    }
    wall = time.perf_counter() - started
    peak = _peak_rss_bytes()
    summary = {
        "object_id": OBJECT_ID, "test_only": test_only,
        "seed_validity": classify_seed(rule_inputs, test_only=test_only),
        "aggregate_rule_status": "NOT_APPLIED_SINGLE_SEED_INVOCATION",
        "seed_label": seed_label, "seed_root_hex": root.hex(),
        "seed_packet_path": str(seed_packet), "seed_packet_schema": packet["schema"],
        "launch_sha": launch_sha,
        "admission": {"path": str(admission_receipt), "validated": True, "facts": admission},
        "exposure": exposure_record(updates), "deterministic_rule_inputs": rule_inputs,
        "runtime_configuration": {"torch_threads": torch_threads, "native_width": 32,
                                  "dtype": "CPU_FP32" if not test_only else "TEST_ONLY"},
        "completion_audit": completion,
        "evaluation_tape_reuse": {
            "rosters": list(rosters), "episodes_per_roster": eval_episodes,
            "expected_cell_uses_per_roster": {str(k): v for k, v in expected_uses.items()},
            "completed_cell_uses_per_roster": {str(k): v for k, v in tape_uses.items()},
            "same_tape_objects_reused": same_tapes,
        },
        "projection_audit": {
            **projection, "precontact_evaluation_equal": precontact_eval_equal,
            "changed_coordinate_inventory": sorted([] if test_only else paired.changed_coordinates),
        },
        "linf_theta_final_minus_initial_over_0_05": distances,
        "cells": cells, "descriptive_estimands": descriptors,
        "optional_measurement_gaps": [
            "raw sidecars", "between-arm action-probability TV/raw traces",
            "ordered-28 inventory/analyzer", "raw-value fixture",
            "checkpoint/resume files", "validator certificates", "formal support census/branch",
            "full parameter-distance sidecars",
        ],
        "work": {
            "expected_cost_law": costs, "observed_training_slots": training_slots,
            "backward_calls": backward, "adam_steps": adam,
            "direct_paired_checks": {
                "successful_paired_updates": paired_assertions,
                "successful_precontact_information_assertions": precontact_assertions,
                "expected_precontact_information_assertions": expected_precontact,
            },
            "per_arm": {arm: {
                "factual_training_episodes": factual_episodes[arm],
                "factual_learner_transitions": factual_episodes[arm] * HORIZON,
                "factual_native_slots": factual_slots[arm],
                "factual_suffix_audit_native_slots": suffix_audit_slots[arm],
                "nonfactual_suffix_native_slots": nonfactual_slots[arm],
                "counterfactual_audit_native_slots": counterfactual_audit_slots[arm],
                "total_training_environment_slots": training_slots[arm],
                "learned_evaluation_episodes": len(checkpoints) * len(rosters)
                                               * len(INTERVENTIONS) * eval_episodes,
                "learned_evaluation_transitions": len(checkpoints) * len(rosters)
                                                  * len(INTERVENTIONS) * eval_episodes * HORIZON,
                "backward_calls": backward[arm], "adam_steps": adam[arm],
                "optimizer_wall_seconds": optimizer_wall[arm],
            } for arm in LEARNED_ARMS},
        },
        "resources": {
            "wall_seconds": wall, "peak_rss_bytes": peak,
            "status": "measured" if peak is not None else "resources_unmeasured",
            "per_arm_wall_seconds": learned_wall,
            "per_arm_wall_seconds_per_update": {
                arm: learned_wall[arm] / updates for arm in LEARNED_ARMS},
            "per_arm_wall_seconds_per_environment_slot": {
                arm: learned_wall[arm] / costs["learned_total_per_arm"] for arm in LEARNED_ARMS},
        },
    }
    (output_root / "summary.json").write_bytes(canonical_json_bytes(summary))
    return summary


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="FRRIE B01 one-root 512-update runner")
    for name in ("output-root", "seed-packet", "admission-receipt"):
        value.add_argument(f"--{name}", required=True, type=Path)
    value.add_argument("--seed-label", required=True)
    value.add_argument("--test-only", action="store_true")
    value.add_argument("--toy-updates", type=int, default=1)
    value.add_argument("--toy-eval-episodes", type=int, default=1)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.toy_updates != 1 or args.toy_eval_episodes != 1:
        raise B01ContractError("toy controls are fixed to one update and one episode")
    config = ((1, (0, 1), (6, 9), 1) if args.test_only else
              (PRODUCTION_UPDATES, PRODUCTION_CHECKPOINTS, PRODUCTION_ROSTERS,
               PRODUCTION_EVAL_EPISODES))
    execute(
        output_root=args.output_root, seed_packet=args.seed_packet,
        admission_receipt=args.admission_receipt, seed_label=args.seed_label,
        test_only=args.test_only, updates=config[0], checkpoints=config[1],
        rosters=config[2], eval_episodes=config[3],
    )
    return 0


__all__ = ["classify_seed", "cost_config", "execute", "exposure_record", "main", "parser"]
