"""Frozen one-root contact-active R128 learner comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..b01.constants import LEARNED_ARMS
from ..b01.contract import B01ContractError, canonical_json_bytes, validate_resource_receipt
from ..b01.r128_smoke import (
    _TimedTrainer,
    _build_adapter,
    _enforce_time_cap,
    _evaluate_cell,
    _launch_sha,
)
from ..b01.trainer import PairedB01Trainer
from ..b01.three_seed import _evaluate_cell as _evaluate_intervention_cell
from ..state_codec import decode_optimizer_state, encode_optimizer_state
from .collector import collect_r02_arm_update
from .semantics import (
    HORIZON,
    OBJECT_ID,
    PRODUCTION_CHECKPOINTS,
    PRODUCTION_EVAL_EPISODES,
    PRODUCTION_UPDATES,
    ROOT_HEX,
    ROSTERS,
    SEED,
    SEED_LABEL,
    TEST_ROOT_HEX,
    TEST_SEED_LABEL,
    classify_r02,
    cost_config,
    cut_contrasts,
    contact_integrity,
    exposure_record,
    _initialize_contact_pair,
    initialize_contact_pair,
)
from .tapes import evaluation_tape, production_training_inputs

PUBLIC_ARM = {
    "PHY_TRUST": "PHY_TRUST_004",
    "EDGE_FLEX": "EDGE_FLEX_150",
    "UNIFORM_LEGAL": "UNIFORM_LEGAL",
}


def _public(values: Mapping[str, Any]) -> dict[str, Any]:
    return {PUBLIC_ARM[key]: value for key, value in values.items()}


def _result_cell(
    arm: str, checkpoint: int | None, roster: int, values: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "arm": PUBLIC_ARM[arm], "checkpoint": checkpoint, "roster": roster,
        "intervention": "INTACT", **values,
    }


def _checkpoint_state(
    model: Any, optimizer: Any, *, checkpoint: int, arm: str,
) -> dict[str, Any]:
    model_bytes = model.parameter_bytes()
    optimizer_bytes = encode_optimizer_state(model, optimizer)
    decoded = decode_optimizer_state(optimizer_bytes)
    first = np.concatenate([value.reshape(-1) for value in decoded.first_moment.values()])
    second = np.concatenate([value.reshape(-1) for value in decoded.second_moment.values()])
    return {
        "checkpoint": checkpoint,
        "arm": PUBLIC_ARM[arm],
        "model_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "optimizer_sha256": hashlib.sha256(optimizer_bytes).hexdigest(),
        "adam_step": decoded.step,
        "first_moment": {
            "nonzero": int(np.count_nonzero(first)),
            "l1": float(np.abs(first).sum()),
            "linf": float(np.abs(first).max()),
        },
        "second_moment": {
            "nonzero": int(np.count_nonzero(second)),
            "l1": float(np.abs(second).sum()),
            "linf": float(np.abs(second).max()),
        },
    }


def _load_admission(path: Path) -> dict[str, Any]:
    if not path.is_absolute():
        raise B01ContractError("admission receipt path must be absolute")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B01ContractError("admission receipt is unreadable") from exc
    return validate_resource_receipt(value)


def _peak_rss_bytes() -> int | None:
    if sys.platform.startswith("linux"):
        try:
            import resource

            return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
        except (ImportError, OSError, AttributeError):
            return None
    if sys.platform == "win32":
        try:
            import psutil

            peak = getattr(psutil.Process().memory_info(), "peak_wset", None)
            return int(peak) if peak is not None else None
        except (ImportError, OSError, AttributeError):
            return None
    return None


def _training_curve_row(receipt: Any) -> dict[str, Any]:
    return {
        "update": receipt.update,
        "loss": receipt.loss,
        "score": receipt.score,
        "entropy": receipt.entropy,
        "critic": receipt.critic,
        "preclip_global_norm": receipt.preclip_global_norm,
        "backward_calls": receipt.backward_calls,
        "adam_steps": receipt.adam_steps,
        "projection_changed_indices": list(receipt.projection_changed_indices),
        "box_contact": receipt.box_contact,
        "maximum_box_overshoot": receipt.maximum_box_overshoot,
        "projection_displacement": receipt.projection_displacement,
        "optimizer_moments_unchanged_by_projection": (
            receipt.optimizer_moments_unchanged_by_projection
        ),
    }


def execute(
    *, output_root: Path, admission_receipt: Path, test_only: bool = False,
    adam_lr: float = 0.0003, seed: int = SEED, role_column_cut: bool = False,
) -> dict[str, Any]:
    if not output_root.is_absolute() or not admission_receipt.is_absolute():
        raise B01ContractError("output and admission paths must be absolute")
    admission = _load_admission(admission_receipt)
    started = time.perf_counter()
    updates = 1 if test_only else PRODUCTION_UPDATES
    checkpoints = (0, 1) if test_only else PRODUCTION_CHECKPOINTS
    eval_episodes = 1 if test_only else PRODUCTION_EVAL_EPISODES
    root_hex = TEST_ROOT_HEX if test_only else ROOT_HEX
    seed_label = TEST_SEED_LABEL if test_only else SEED_LABEL
    if seed == 2:
        root_hex, seed_label, adam_lr = f"{seed:064x}", "FRRIE-B07-CONTACT-BLOCK-002", 0.003
    if seed == 3:
        root_hex, seed_label, adam_lr = "0000000000000000000000000000000000000000000000000000000000000003", "FRRIE-B09-CONTACT-BLOCK-003", 0.003
    if role_column_cut:
        seed, root_hex, seed_label, adam_lr = 1, ROOT_HEX, SEED_LABEL, 0.003
    root = bytes.fromhex(root_hex)
    evaluation_tapes = {
        roster: tuple(
            evaluation_tape(
                root, seed_label=seed_label, roster=roster, episode=episode,
            )
            for episode in range(eval_episodes)
        )
        for roster in ROSTERS
    }
    output_root.mkdir(parents=True, exist_ok=True)
    launch_sha = _launch_sha()
    torch_threads = None
    adapter = _build_adapter()
    cells: list[dict[str, Any]] = []
    uniform: dict[int, dict[str, Any]] = {}
    tape_uses = {roster: 0 for roster in ROSTERS}
    learned_wall = {arm: 0.0 for arm in LEARNED_ARMS}
    optimizer_wall = {arm: 0.0 for arm in LEARNED_ARMS}
    training_slots = {arm: 0 for arm in LEARNED_ARMS}
    factual_episodes = {arm: 0 for arm in LEARNED_ARMS}
    backward = {arm: 0 for arm in LEARNED_ARMS}
    adam = {arm: 0 for arm in LEARNED_ARMS}
    training_curves = {arm: [] for arm in LEARNED_ARMS}
    checkpoint_states: list[dict[str, Any]] = []
    paired_updates = 0
    evaluation_preserved = True

    for roster in ROSTERS:
        uniform[roster], _ = _evaluate_cell(adapter, None, tapes=evaluation_tapes[roster])
        tape_uses[roster] += 1
        cells.append(_result_cell("UNIFORM_LEGAL", None, roster, uniform[roster]))
    _enforce_time_cap(started, learned_wall)

    import torch

    torch.set_num_threads(1)
    torch_threads = torch.get_num_threads()
    models, optimizers, initial_audit, raw_initial = _initialize_contact_pair(
        root_hex, seed_label, adam_lr=adam_lr,
    )
    if seed == 1 and not test_only and initial_audit["tight_changed_coordinates"] != 5:
        raise B01ContractError("initial tight clip did not change exactly five coordinates")
    if seed == 1 and initial_audit["tight_changed_coordinates"] <= 0:
        raise B01ContractError("initial tight clip was not active")
    paired = PairedB01Trainer(models, optimizers)
    paired.first_tight_contact_update = initial_audit["first_tight_contact_update"]
    paired.changed_coordinates = set(initial_audit["tight_changed_coordinate_indices"])
    paired.maximum_tight_overshoot = initial_audit["tight_maximum_overshoot"]
    paired.cumulative_tight_displacement = initial_audit["tight_projection_displacement"]
    timed = {arm: _TimedTrainer(paired.trainers[arm]) for arm in LEARNED_ARMS}
    paired.trainers.update(timed)

    checkpoint_set = set(checkpoints)
    for update in range(updates + 1):
        if update in checkpoint_set:
            for arm in LEARNED_ARMS:
                before_opt = encode_optimizer_state(models[arm], optimizers[arm])
                checkpoint_states.append(_checkpoint_state(
                    models[arm], optimizers[arm], checkpoint=update, arm=arm,
                ))
                arm_started = time.perf_counter()
                for roster in ROSTERS:
                    values, _ = _evaluate_cell(
                        adapter, models[arm], tapes=evaluation_tapes[roster]
                    )
                    tape_uses[roster] += 1
                    cells.append(_result_cell(arm, update, roster, values))
                    evaluation_preserved &= values["model_bytes_preserved"]
                learned_wall[arm] += time.perf_counter() - arm_started
                evaluation_preserved &= (
                    encode_optimizer_state(models[arm], optimizers[arm]) == before_opt
                )
            _enforce_time_cap(started, learned_wall)
        if update == updates:
            break
        number = update + 1
        tapes, origins = production_training_inputs(root, seed_label, number)
        batches = {}
        for arm in LEARNED_ARMS:
            arm_started = time.perf_counter()
            collected = collect_r02_arm_update(
                model=models[arm],
                adapter=adapter,
                tapes=tapes,
                origins=origins,
                update=number,
                seed_label=seed_label,
            )
            learned_wall[arm] += time.perf_counter() - arm_started
            batches[arm] = collected.batch
            training_slots[arm] += collected.audit.total_environment_slots
            factual_episodes[arm] += collected.audit.factual_episodes
        before_wall = {arm: timed[arm].wall_seconds for arm in LEARNED_ARMS}
        receipts = paired.update(batches, update=number)
        paired_updates += 1
        for arm in LEARNED_ARMS:
            elapsed = timed[arm].wall_seconds - before_wall[arm]
            learned_wall[arm] += elapsed
            optimizer_wall[arm] += elapsed
            backward[arm] += receipts[arm].backward_calls
            adam[arm] += receipts[arm].adam_steps
            training_curves[arm].append(_training_curve_row(receipts[arm]))
        _enforce_time_cap(started, learned_wall)

    if role_column_cut:
        for arm in LEARNED_ARMS:
            for roster in ROSTERS:
                arm_started = time.perf_counter()
                values, _ = _evaluate_intervention_cell(
                    adapter, models[arm], tapes=evaluation_tapes[roster], intervention="SEMANTIC_COLUMN_ROTATE",
                )
                cells.append({**_result_cell(arm, updates, roster, values), "intervention": "SEMANTIC_COLUMN_ROTATE"})
                tape_uses[roster] += 1
                evaluation_preserved &= values["model_bytes_preserved"]
                learned_wall[arm] += time.perf_counter() - arm_started
                _enforce_time_cap(started, learned_wall)
    projection = paired.projection_audit()
    final_displacement = {}
    for arm in LEARNED_ARMS:
        before = np.frombuffer(raw_initial[arm], dtype="<f4")
        after = np.frombuffer(models[arm].parameter_bytes(), dtype="<f4")
        absolute = np.abs(after - before)
        final_displacement[PUBLIC_ARM[arm]] = {
            "linf": float(absolute.max()),
            "l1": float(absolute.sum()),
        }

    descriptors = []
    for checkpoint in checkpoints:
        for roster in ROSTERS:
            phy = next(
                row for row in cells
                if row["arm"] == "PHY_TRUST_004"
                and row["checkpoint"] == checkpoint
                and row["roster"] == roster and row["intervention"] == "INTACT"
            )
            edge = next(
                row for row in cells
                if row["arm"] == "EDGE_FLEX_150"
                and row["checkpoint"] == checkpoint
                and row["roster"] == roster and row["intervention"] == "INTACT"
            )
            descriptors.append({
                "checkpoint": checkpoint,
                "roster": roster,
                "d_u": phy["J"] - edge["J"],
                "e_u": edge["J"] - uniform[roster]["J"],
            })
    update_128_descriptors = [
        {"roster": row["roster"], "d_128": row["d_u"], "e_128": row["e_u"]}
        for row in descriptors
        if row["checkpoint"] == PRODUCTION_UPDATES
    ]
    evaluation_episodes = sum(row["episodes"] for row in cells)
    evaluation_transitions = sum(row["transitions"] for row in cells)
    costs = cost_config(updates, checkpoints, eval_episodes, role_column_cut=role_column_cut)
    expected_uses = 1 + 2 * (len(checkpoints) + role_column_cut)
    same_tapes = all(value == expected_uses for value in tape_uses.values())
    paired_work = paired_updates == updates and len(set(training_slots.values())) == 1
    optimizer_projection_unchanged = initial_audit[
        "optimizer_state_unchanged_by_initial_projection"
    ] and all(
        row["optimizer_moments_unchanged_by_projection"]
        for curve in training_curves.values() for row in curve
    )

    contrasts, cut_complete = cut_contrasts(cells, checkpoints, eval_episodes) if role_column_cut else ([], False)
    contact = contact_integrity(initial_audit, training_curves, projection["first_tight_contact_update"])
    if test_only:
        complete = True
        completion = {"complete": True, "status": "TEST_ONLY_NON_RESULT"}
    else:
        expected = {
            "updates": 128,
            "factual_episodes_per_arm": _public({arm: 8_192 for arm in LEARNED_ARMS}),
            "training_slots_per_arm": _public({arm: 630_784 for arm in LEARNED_ARMS}),
            "backward_per_arm": _public({arm: 128 for arm in LEARNED_ARMS}),
            "adam_per_arm": _public({arm: 128 for arm in LEARNED_ARMS}),
            "paired_updates": 128,
            "cells": 22 if role_column_cut else 18,
            "learned_cells": 20 if role_column_cut else 16,
            "uniform_cells": 2,
            "evaluation_episodes": 5_632 if role_column_cut else 4_608,
            "evaluation_transitions": 67_584 if role_column_cut else 55_296,
            "descriptors": 8,
            "tape_uses": {n: 11 if role_column_cut else 9 for n in ROSTERS},
            "cost_config": cost_config(
                PRODUCTION_UPDATES, PRODUCTION_CHECKPOINTS, PRODUCTION_EVAL_EPISODES, role_column_cut=role_column_cut,
            ),
            "torch_threads": 1,
            "evaluation_preserved": True,
            "paired_information_work_equal": True,
            "raw_paired_initialization_equal": True,
            "initial_tight_clip_changed_coordinates": 5,
            "first_tight_contact_update": 0,
            "optimizer_moments_unchanged_by_projection": True,
            "learner_transitions_per_arm": _public({arm: 98_304 for arm in LEARNED_ARMS}),
        }
        observed = {
            "updates": paired_updates,
            "factual_episodes_per_arm": _public(factual_episodes),
            "training_slots_per_arm": _public(training_slots),
            "backward_per_arm": _public(backward),
            "adam_per_arm": _public(adam),
            "paired_updates": paired_updates,
            "cells": len(cells),
            "learned_cells": sum(row["arm"] in ("PHY_TRUST_004", "EDGE_FLEX_150") for row in cells),
            "uniform_cells": sum(row["arm"] == "UNIFORM_LEGAL" for row in cells),
            "evaluation_episodes": evaluation_episodes,
            "evaluation_transitions": evaluation_transitions,
            "descriptors": len(descriptors),
            "tape_uses": tape_uses,
            "cost_config": costs,
            "torch_threads": torch_threads,
            "evaluation_preserved": evaluation_preserved,
            "paired_information_work_equal": paired_work,
            "raw_paired_initialization_equal": (
                initial_audit["raw_paired_arm_bytes_equal"]
                and initial_audit["raw_paired_model_bytes_equal"]
            ),
            "initial_tight_clip_changed_coordinates": initial_audit[
                "tight_changed_coordinates"
            ],
            "first_tight_contact_update": projection["first_tight_contact_update"],
            "optimizer_moments_unchanged_by_projection": optimizer_projection_unchanged,
            "learner_transitions_per_arm": _public({
                arm: factual_episodes[arm] * HORIZON for arm in LEARNED_ARMS
            }),
        }
        if seed in (2, 3):
            for name in ("initial_tight_clip_changed_coordinates", "first_tight_contact_update"):
                del expected[name], observed[name]
            expected.update(initial_projection_conformant=True, contact_history_truthful=True)
            observed.update(contact)
        checks = {name: observed[name] == value for name, value in expected.items()}
        complete = all(checks.values())
        completion = {
            "complete": complete,
            "checks": checks,
            "expected": expected,
            "observed": observed,
        }

    final_group_lr = {
        PUBLIC_ARM[arm]: [group["lr"] for group in optimizers[arm].param_groups]
        for arm in LEARNED_ARMS
    }
    rule_inputs = {
        **contact,
        "r08_binding": seed == 1 and root_hex == ROOT_HEX and seed_label == SEED_LABEL,
        "cut_panel_complete": cut_complete,
        "cut_contrasts": contrasts,
        "r07_binding": seed == int(root_hex, 16) == 2 and seed_label == "FRRIE-B07-CONTACT-BLOCK-002",
        "r09_binding": seed == int(root_hex, 16) == 3 and seed_label == "FRRIE-B09-CONTACT-BLOCK-003",
        "initial_optimizer_group_lr": initial_audit["initial_optimizer_group_lr"],
        "final_optimizer_group_lr": final_group_lr,
        "complete": complete,
        "admission_valid": True,
        "exposure_present": True,
        "raw_paired_initialization_equal": (
            initial_audit["raw_paired_arm_bytes_equal"]
            and initial_audit["raw_paired_model_bytes_equal"]
        ),
        "initial_tight_clip_changed_exactly_five": (
            initial_audit["tight_changed_coordinates"] == 5
        ),
        "optimizer_moments_unchanged_by_projection": optimizer_projection_unchanged,
        "paired_information_work_equal": paired_work,
        "evaluation_preserved_model_bytes": evaluation_preserved,
        "same_evaluation_tapes": same_tapes,
        "required_curves_and_counts_present": bool(
            cells and descriptors and (test_only or all(len(rows) == updates for rows in training_curves.values()))
        ),
        "learner_transitions": sum(factual_episodes.values()) * HORIZON,
        "training_episodes": sum(factual_episodes.values()),
        "backward_calls": sum(backward.values()),
        "adam_steps": sum(adam.values()),
        "evaluation_episodes": evaluation_episodes,
        "first_tight_contact_update": projection["first_tight_contact_update"],
        "update_128_descriptors": update_128_descriptors,
    }
    wall = time.perf_counter() - started
    peak = _peak_rss_bytes()
    summary = {
        "object_id": (
            "FRRIE-B01-R128-LR003-R08-ROLE-COLUMN-CUT-20260905" if role_column_cut else
            "FRRIE-B01-CONTACT-R128-LR003-R09-THIRD-ROOT-20260905" if seed == 3 else
            "FRRIE-B01-CONTACT-R128-LR003-R07-SECOND-ROOT-20260905" if seed == 2 else
            "FRRIE-B01-CONTACT-ACTIVE-R128-LR003-R06-20260904" if adam_lr == 0.003 else OBJECT_ID
        ),
        "evidence_class": "B/EXPLORE",
        "test_only": test_only,
        "branch": classify_r02(
            rule_inputs, test_only=test_only, branch_prefix="R08" if role_column_cut else "R09" if seed == 3 else "R07" if seed == 2 else "R06" if adam_lr == 0.003 else "R02",
        ),
        "seed": seed,
        "seed_label": seed_label,
        "seed_root_hex": root_hex,
        "launch_sha": launch_sha,
        "admission": {
            "path": str(admission_receipt),
            "validated": True,
            "facts": admission,
        },
        "exposure": {**exposure_record(
            updates, initial_audit["tight_changed_coordinates"],
            adam_lr=initial_audit["initial_optimizer_group_lr"]["PHY_TRUST_004"][0],
        ), "first_tight_contact_update": projection["first_tight_contact_update"]},
        "deterministic_rule_inputs": rule_inputs,
        "runtime_configuration": {
            "device": "CPU",
            "dtype": "CPU_FP32_TEST_ONLY_NON_RESULT" if test_only else "CPU_FP32",
            "torch_threads": torch_threads,
            "native_width": 32,
            "training_roster_order": [9, 15] * 32,
            "arm_ids": ["PHY_TRUST_004", "EDGE_FLEX_150", "UNIFORM_LEGAL"],
        },
        "completion_audit": completion,
        "initialization_audit": initial_audit,
        "projection_audit": {
            **projection,
            "initial_contact": initial_audit,
            "per_update": _public(training_curves),
            "checkpoint_state": checkpoint_states,
            "optimizer_moments_unchanged_by_every_projection": optimizer_projection_unchanged,
            "final_parameter_displacement_from_raw_initial": final_displacement,
        },
        "evaluation_tape_reuse": {
            "rosters": list(ROSTERS),
            "episodes_per_roster": eval_episodes,
            "expected_cell_uses_per_roster": expected_uses,
            "completed_cell_uses_per_roster": {str(k): v for k, v in tape_uses.items()},
            "same_tape_objects_reused": same_tapes,
        },
        "cells": cells,
        "descriptive_estimands": descriptors,
        "cut_contrasts": contrasts,
        "work": {
            "expected_cost_law": costs,
            "observed_training_slots": _public(training_slots),
            "backward_calls": _public(backward),
            "adam_steps": _public(adam),
            "successful_paired_updates": paired_updates,
            "per_arm": {
                PUBLIC_ARM[arm]: {
                    "factual_training_episodes": factual_episodes[arm],
                    "factual_learner_transitions": factual_episodes[arm] * HORIZON,
                    "training_environment_slots": training_slots[arm],
                    "learned_evaluation_episodes": (
                        (len(checkpoints) + role_column_cut) * len(ROSTERS) * eval_episodes
                    ),
                    "learned_evaluation_environment_slots": (
                        (len(checkpoints) + role_column_cut) * len(ROSTERS) * eval_episodes * HORIZON
                    ),
                    "backward_calls": backward[arm],
                    "adam_steps": adam[arm],
                    "optimizer_wall_seconds": optimizer_wall[arm],
                }
                for arm in LEARNED_ARMS
            },
        },
        "resources": {
            "wall_seconds": wall,
            "peak_rss_bytes": peak,
            "status": "measured" if peak is not None else "resources_unmeasured",
            "per_arm_wall_seconds": _public(learned_wall),
            "per_arm_wall_seconds_per_update": _public({
                arm: learned_wall[arm] / updates for arm in LEARNED_ARMS
            }),
            "per_arm_wall_seconds_per_environment_slot": _public({
                arm: learned_wall[arm] / costs["learned_total_per_arm"]
                for arm in LEARNED_ARMS
            }),
        },
    }
    (output_root / "summary.json").write_bytes(canonical_json_bytes(summary))
    return summary


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="FRRIE contact-active one-root R128 runner")
    value.add_argument("--output-root", required=True, type=Path)
    value.add_argument("--admission-receipt", required=True, type=Path)
    value.add_argument("--seed", required=True, type=int)
    value.add_argument("--test-only", action="store_true")
    value.add_argument("--lr003", action="store_true")
    value.add_argument("--role-column-cut", action="store_true")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.seed not in (1, 2, 3):
        raise B01ContractError("contact seed must be literal 1, 2 or 3")
    execute(
        output_root=args.output_root,
        admission_receipt=args.admission_receipt,
        test_only=args.test_only,
        adam_lr=0.003 if args.lr003 else 0.0003, seed=args.seed, role_column_cut=args.role_column_cut,
    )
    return 0
