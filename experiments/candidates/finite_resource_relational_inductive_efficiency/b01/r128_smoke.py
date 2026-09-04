"""Small in-memory FRRIE B01 R128 learner/evaluation path."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..arms import initialize_paired_arms
from ..native_adapter import build_package_native_artifact, load_package_native_adapter
from ..orchestration import OriginCoordinate
from ..policy import make_actor_critic
from ..rng import AddressedRNG
from ..state_codec import encode_optimizer_state
from ..tapes import generate_training_origin_schedule
from ..training import make_optimizer
from .batch_collector import _collect_b01_arm_update
from .constants import LEARNED_ARMS, ROOT_LABELS, TEST_SEED_LABEL, TRAIN_ROSTER_ORDER
from .contract import (
    B01ContractError, canonical_json_bytes, named_compute_profile,
    validate_resource_receipt,
)
from .native_batch import B01NativeBatchEnvironment
from .seed_packet import (
    create_production_seed_packet, read_production_seed_packet, read_test_seed_packet,
)
from .tapes import evaluation_tape, training_tape
from .trainer import PairedB01Trainer

OBJECT_ID = "FRRIE-B01-SECTION11-R128-SMOKE-20260904"
PRODUCTION_LABEL = ROOT_LABELS[0]
PRODUCTION_UPDATES = 128
PRODUCTION_CHECKPOINTS = (0, 32, 64, 128)
PRODUCTION_EVAL_EPISODES = 256
HORIZON = 12
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
NativeEnvironment = B01NativeBatchEnvironment


def exposure_record(updates: int) -> dict[str, Any]:
    nominal = round(updates * 0.0003, 10)
    ratio = round(nominal / 0.05, 10)
    return {
        "updates": updates,
        "adam_lr": 0.0003,
        "nominal_lr_exposure": nominal,
        "init_half_range": 0.05,
        "nominal_exposure_over_init_half_range": ratio,
        "line": (
            f"updates={updates}; adam_lr=0.0003; nominal_lr_exposure={nominal:.4f}; "
            f"init_half_range=0.05; nominal_exposure_over_init_half_range={ratio:.3f}"
        ),
    }
def cost_config(updates: int, checkpoints: Sequence[int], episodes: int) -> dict[str, Any]:
    training = 4_928 * updates
    evaluation = len(checkpoints) * 2 * episodes * HORIZON
    uniform = 2 * episodes * HORIZON
    return {
        "updates": updates, "checkpoints": list(checkpoints), "evaluation_episodes_per_cell": episodes,
        "learned_training_per_arm": training, "learned_evaluation_per_arm": evaluation,
        "learned_total_per_arm": training + evaluation, "shared_uniform": uniform,
        "invocation": 2 * (training + evaluation) + uniform,
        "optimizer_steps_per_arm": updates, "cells": 2 + 4 * len(checkpoints),
        "evaluation_episodes_total": 2 * episodes + 4 * len(checkpoints) * episodes,
        "factual_learner_transitions_per_arm": 64 * updates * HORIZON,
        "factual_learner_transitions_total": 128 * updates * HORIZON,
    }
class _TimedTrainer:
    def __init__(self, inner: Any) -> None:
        self.inner, self.optimizer, self.wall_seconds = inner, inner.optimizer, 0.0
    def update(self, *args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        try:
            return self.inner.update(*args, **kwargs)
        finally:
            self.wall_seconds += time.perf_counter() - started
def classify_r128(rule_inputs: Mapping[str, Any], *, test_only: bool = False) -> str:
    if test_only:
        return "TEST_ONLY_NON_RESULT"
    required_true = (
        "complete", "admission_valid", "exposure_present",
        "paired_information_work_equal", "precontact_full_state_equal",
        "precontact_evaluation_equal",
        "evaluation_preserved_model_bytes", "required_measurements_present",
    )
    required_positive = (
        "learner_transitions", "training_episodes", "backward_calls", "adam_steps",
        "evaluation_episodes",
    )
    if any(rule_inputs.get(name) is not True for name in required_true) or any(
        type(rule_inputs.get(name)) is not int or rule_inputs[name] <= 0
        for name in required_positive
    ):
        return "R128_INVALID_INCOMPLETE"
    contact = rule_inputs.get("first_tight_contact_update")
    if contact is None:
        return "R128_VALID_NO_CONTACT"
    if type(contact) is int and 1 <= contact <= PRODUCTION_UPDATES:
        return "R128_VALID_CONTACT"
    return "R128_INVALID_INCOMPLETE"
def _load_admission(path: Path) -> dict[str, Any]:
    if not path.is_absolute():
        raise B01ContractError("admission receipt path must be absolute")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B01ContractError("admission receipt is unreadable") from exc
    return validate_resource_receipt(value)
def _seed_root(path: Path, label: str, *, test_only: bool) -> tuple[bytes, dict[str, Any]]:
    if not path.is_absolute():
        raise B01ContractError("seed packet path must be absolute")
    if test_only:
        packet = read_test_seed_packet(path)
        if label != TEST_SEED_LABEL:
            raise B01ContractError("TEST run requires the canonical first TEST label")
    else:
        if not path.exists():
            create_production_seed_packet(path)
        packet = read_production_seed_packet(path)
        if label != PRODUCTION_LABEL:
            raise B01ContractError("R128 production run requires root 001")
    index = packet["labels"].index(label)
    return bytes.fromhex(packet["roots_hex"][index]), packet
def _build_adapter() -> Any:
    build_package_native_artifact()
    return load_package_native_adapter(named_compute_profile())
def _production_training_inputs(
    root: bytes, label: str, update: int,
) -> tuple[tuple[Any, ...], tuple[tuple[OriginCoordinate, ...], ...]]:
    rng = AddressedRNG(root)
    schedules = {
        roster: generate_training_origin_schedule(
            rng, seed_block=label, roster=roster, update=update, purpose="TRAIN",
        )
        for roster in (9, 15)
    }
    by_coordinate = {
        (roster, episode): tuple(
            OriginCoordinate(row.public_role_index, row.selected_slot, row.simulator_index)
            for row in sorted(
                (item for item in schedule.selections if item.episode == episode),
                key=lambda item: item.public_role_index,
            )
        )
        for roster, schedule in schedules.items()
        for episode in range(32)
    }
    tapes = tuple(
        training_tape(
            root, seed_label=label, roster=roster, update=update, episode=position // 2,
        )
        for position, roster in enumerate(TRAIN_ROSTER_ORDER)
    )
    return tapes, tuple(by_coordinate[(tape.roster, tape.episode)] for tape in tapes)
def _uniform_actions(masks: np.ndarray, uniforms: np.ndarray) -> np.ndarray:
    actions = np.empty(masks.shape[:2], dtype=np.int64)
    for lane in range(masks.shape[0]):
        for entity in range(masks.shape[1]):
            support = np.flatnonzero(masks[lane, entity])
            rank = min(int(float(uniforms[lane, entity]) * len(support)), len(support) - 1)
            actions[lane, entity] = int(support[rank])
    return actions
class _ToyPolicy:
    """Non-result policy used only by the explicit TEST-only runner path."""

    def __init__(self, arm: str) -> None:
        self.arm_id = arm
        self._state = bytearray(b"TEST_ONLY_TOY_STATE")
    def parameter_bytes(self) -> bytes:
        return bytes(self._state)
    def update(self) -> None:
        self._state[-1] = (self._state[-1] + 1) % 256
    def select_actions(
        self, masks: np.ndarray, uniforms: np.ndarray, hidden: Any,
    ) -> tuple[np.ndarray, Any]:
        return _uniform_actions(masks, uniforms), hidden
def _learned_actions(
    model: Any, observations: np.ndarray, roles: np.ndarray, masks: np.ndarray,
    uniforms: np.ndarray, hidden: Any,
) -> tuple[np.ndarray, Any]:
    if hasattr(model, "select_actions"):
        return model.select_actions(masks, uniforms, hidden)
    import torch
    actor = model.actor_step_batch(
        torch.from_numpy(np.ascontiguousarray(observations)),
        torch.from_numpy(np.ascontiguousarray(roles)), hidden,
    )
    actions = model.actions_from_uniforms_batch(
        actor.probabilities, torch.from_numpy(np.ascontiguousarray(uniforms, dtype=np.float32)),
    )
    return actions.numpy(), actor.hidden
def _evaluate_cell(
    adapter: Any, model: Any | None, *, tapes: tuple[Any, ...],
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
    action_trace, terminal_trace = [], []
    for start in range(0, episodes, 32):
        batch_tapes = tapes[start:min(start + 32, episodes)]
        environment = NativeEnvironment(adapter, roster=roster, lanes=len(batch_tapes))
        environment.reset(batch_tapes)
        hidden: Any = None
        if model is not None and not hasattr(model, "select_actions"):
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
                else:
                    if hasattr(model, "select_actions"):
                        actions, hidden = _learned_actions(
                            model, frame.observations, frame.roles, frame.legal_masks,
                            uniforms, hidden,
                        )
                    else:
                        import torch
                        with torch.no_grad():
                            actions, hidden = _learned_actions(
                                model, frame.observations, frame.roles, frame.legal_masks,
                                uniforms, hidden,
                            )
                terminal = environment.step(actions)
                action_trace.append(np.asarray(actions, dtype=np.int64).tobytes(order="C"))
                action_counts_np = np.bincount(np.asarray(actions).reshape(-1), minlength=6)
                action_counts = [a + int(b) for a, b in zip(action_counts, action_counts_np)]
        finally:
            if model is not None and not hasattr(model, "select_actions"):
                model.train(was_training)
        if terminal is None or terminal.terminals != (True,) * len(batch_tapes):
            raise B01ContractError("evaluation did not terminate all native lanes")
        terminal_trace.append(tuple((float(value).hex(), tuple(asdict(primitive).items()))
                                    for value, primitive in zip(terminal.returns, terminal.primitives)))
        returns.extend(map(float, terminal.returns))
        for primitive in terminal.primitives:
            direct = asdict(primitive)
            dw.append(direct["dw"])
            de.append(direct["de"])
            waste.append(direct["waste"])
            for name in sums:
                sums[name] += int(direct[name])
    preserved = model is None or model.parameter_bytes() == before
    summary = {
        "J": float(np.mean(returns)), "D_W": float(np.mean(dw)),
        "D_E": float(np.mean(de)), "min_D": float(np.mean(np.minimum(dw, de))),
        "WASTE": float(np.mean(waste)), "action_counts": action_counts,
        "native_event_counts": sums, "episodes": episodes,
        "transitions": episodes * HORIZON, "environment_slots": episodes * HORIZON,
        "model_bytes_preserved": preserved,
    }
    return summary, (tuple(action_trace), tuple(terminal_trace))
def _peak_rss_bytes() -> int | None:
    try:
        import psutil
        info = psutil.Process().memory_info()
        return int(getattr(info, "peak_wset", info.rss))
    except (ImportError, OSError, AttributeError):
        return None
def _launch_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
        cwd=REPOSITORY_ROOT,
    ).stdout.strip()
def _cell(arm: str, checkpoint: int | None, roster: int, values: Mapping[str, Any]) -> dict[str, Any]:
    return {"arm": arm, "checkpoint": checkpoint, "roster": roster, "intervention": "INTACT", **values}
def _enforce_time_cap(started: float, learned_wall: Mapping[str, float]) -> None:
    if any(value > 4 * 3600 for value in learned_wall.values()) or time.perf_counter() - started > 8 * 3600:
        raise TimeoutError("R128 machine-time cap reached")
def execute(
    *, output_root: Path, seed_packet: Path, admission_receipt: Path, seed_label: str,
    test_only: bool, updates: int, checkpoints: Sequence[int], eval_episodes: int,
) -> dict[str, Any]:
    if not all(path.is_absolute() for path in (output_root, seed_packet, admission_receipt)):
        raise B01ContractError("output, seed packet, and admission paths must be absolute")
    admission = _load_admission(admission_receipt)
    started = time.perf_counter()
    root, packet = _seed_root(seed_packet, seed_label, test_only=test_only)
    evaluation_tapes = {
        roster: tuple(evaluation_tape(root, seed_label=seed_label, roster=roster, episode=i)
                      for i in range(eval_episodes))
        for roster in (9, 15)
    }
    launch_sha = _launch_sha()
    output_root.mkdir(parents=True, exist_ok=True)
    torch_threads = None
    if not test_only:
        import torch
        torch.set_num_threads(1)
        torch_threads = torch.get_num_threads()
    adapter = _build_adapter()
    cells: list[dict[str, Any]] = []
    learned_wall = {arm: 0.0 for arm in LEARNED_ARMS}
    training_slots = {arm: 0 for arm in LEARNED_ARMS}
    backward = {arm: 0 for arm in LEARNED_ARMS}
    adam = {arm: 0 for arm in LEARNED_ARMS}
    factual_episodes = {arm: 0 for arm in LEARNED_ARMS}
    optimizer_wall = {arm: 0.0 for arm in LEARNED_ARMS}
    paired_assertions = precontact_information_assertions = 0
    eval_preserved = True
    precontact_evaluation_equal = True
    tape_uses = {9: 0, 15: 0}
    uniform = {}
    for roster in (9, 15):
        uniform[roster], _ = _evaluate_cell(adapter, None, tapes=evaluation_tapes[roster])
        tape_uses[roster] += 1
        cells.append(_cell("UNIFORM_LEGAL", None, roster, uniform[roster]))
    _enforce_time_cap(started, learned_wall)

    if test_only:
        models = {arm: _ToyPolicy(arm) for arm in LEARNED_ARMS}
        initial = {arm: models[arm].parameter_bytes() for arm in LEARNED_ARMS}
        first_contact = None
        precontact_equal = True
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

    checkpoint_set = set(checkpoints)
    for update in range(0, updates + 1):
        if update in checkpoint_set:
            checkpoint_rows = {}
            checkpoint_traces = {}
            for arm in LEARNED_ARMS:
                before_opt = None if test_only else encode_optimizer_state(models[arm], optimizers[arm])
                t0 = time.perf_counter()
                for roster in (9, 15):
                    values, trace = _evaluate_cell(
                        adapter, models[arm], tapes=evaluation_tapes[roster],
                    )
                    tape_uses[roster] += 1
                    cells.append(_cell(arm, update, roster, values))
                    checkpoint_rows[(arm, roster)] = values
                    checkpoint_traces[(arm, roster)] = trace
                    eval_preserved = eval_preserved and values["model_bytes_preserved"]
                learned_wall[arm] += time.perf_counter() - t0
                if not test_only:
                    eval_preserved = eval_preserved and (
                        encode_optimizer_state(models[arm], optimizers[arm]) == before_opt
                    )
            contact_at_checkpoint = None if test_only else paired.first_tight_contact_update
            if contact_at_checkpoint is None:
                checkpoint_equal = all(
                    checkpoint_traces[("PHY_TRUST", roster)]
                    == checkpoint_traces[("EDGE_FLEX", roster)]
                    for roster in (9, 15)
                )
                precontact_evaluation_equal = precontact_evaluation_equal and checkpoint_equal
                if not checkpoint_equal:
                    raise B01ContractError("paired evaluation differed before tight contact")
            _enforce_time_cap(started, learned_wall)
        if update == updates:
            break
        update_number = update + 1
        if test_only:
            for arm in LEARNED_ARMS:
                models[arm].update()
                training_slots[arm] += 4_928
                backward[arm] += 1
                adam[arm] += 1
            precontact_equal = models["PHY_TRUST"].parameter_bytes() == models["EDGE_FLEX"].parameter_bytes()
        else:
            tapes, origins = _production_training_inputs(root, seed_label, update_number)
            batches = {}
            for arm in LEARNED_ARMS:
                t0 = time.perf_counter()
                collected = _collect_b01_arm_update(
                    model=models[arm], adapter=adapter, tapes=tapes, origins=origins,
                    update=update_number, allowed_seed_labels=(seed_label,),
                )
                learned_wall[arm] += time.perf_counter() - t0
                batches[arm] = collected.batch
                training_slots[arm] += collected.audit.total_environment_slots
                factual_episodes[arm] += collected.audit.factual_episodes
            was_precontact = paired.first_tight_contact_update is None
            before_optimizer_wall = {arm: timed[arm].wall_seconds for arm in LEARNED_ARMS}
            receipts = paired.update(batches, update=update_number)
            paired_assertions += 1
            precontact_information_assertions += int(was_precontact)
            for arm in LEARNED_ARMS:
                elapsed = timed[arm].wall_seconds - before_optimizer_wall[arm]
                learned_wall[arm] += elapsed
                optimizer_wall[arm] += elapsed
                backward[arm] += receipts[arm].backward_calls
                adam[arm] += receipts[arm].adam_steps
        _enforce_time_cap(started, learned_wall)

    if test_only:
        first_contact = None
    else:
        projection = paired.projection_audit()
        first_contact = projection["first_tight_contact_update"]
        precontact_equal = projection["precontact_full_state_equal"]
    distances = {
        arm: float(np.max(np.abs(
            np.frombuffer(models[arm].parameter_bytes(), dtype="<f4")
            - np.frombuffer(initial[arm], dtype="<f4")
        ))) / 0.05 if not test_only else 0.0
        for arm in LEARNED_ARMS
    }
    descriptors = []
    for checkpoint in checkpoints:
        for roster in (9, 15):
            phy_cell = next(row for row in cells if row["arm"] == "PHY_TRUST" and row["checkpoint"] == checkpoint and row["roster"] == roster)
            edge_cell = next(row for row in cells if row["arm"] == "EDGE_FLEX" and row["checkpoint"] == checkpoint and row["roster"] == roster)
            descriptors.append({
                "checkpoint": checkpoint, "roster": roster,
                "d_u": phy_cell["J"] - edge_cell["J"],
                "e_u": edge_cell["J"] - uniform[roster]["J"],
            })
    evaluation_episode_count = sum(row["episodes"] for row in cells)
    evaluation_transitions = sum(row["transitions"] for row in cells)
    costs = cost_config(updates, checkpoints, eval_episodes)
    expected_tape_uses = 1 + 2 * len(checkpoints)
    tape_reuse = {
        "rosters": [9, 15], "episodes_per_roster": eval_episodes,
        "expected_cell_uses_per_roster": expected_tape_uses,
        "completed_cell_uses_per_roster": {str(k): v for k, v in tape_uses.items()},
        "same_tape_objects_reused": all(v == expected_tape_uses for v in tape_uses.values()),
    }
    expected_precontact = updates if test_only or first_contact is None else first_contact
    paired_information_work_equal = test_only or (
        paired_assertions == updates
        and precontact_information_assertions == expected_precontact
        and len(set(training_slots.values())) == 1
    )
    if test_only:
        completion = {"status": "TEST_ONLY_NON_RESULT", "complete": True}
        complete = True
    else:
        expected = {
            "updates": 128, "factual_episodes_per_arm": {arm: 8_192 for arm in LEARNED_ARMS},
            "training_slots_per_arm": {arm: 630_784 for arm in LEARNED_ARMS},
            "backward_per_arm": {arm: 128 for arm in LEARNED_ARMS},
            "adam_per_arm": {arm: 128 for arm in LEARNED_ARMS},
            "paired_updates": 128, "precontact_information_assertions": expected_precontact,
            "cells": 18, "learned_cells": 16, "uniform_cells": 2,
            "evaluation_episodes": 4_608,
            "evaluation_transitions": 55_296, "descriptors": 8,
            "tape_uses": {9: 9, 15: 9}, "cost_config": cost_config(
                PRODUCTION_UPDATES, PRODUCTION_CHECKPOINTS, PRODUCTION_EVAL_EPISODES),
            "torch_threads": 1, "evaluation_preserved": True,
            "paired_information_work_equal": True, "precontact_state_equal": True,
            "precontact_evaluation_equal": True,
            "learner_transitions_per_arm": {arm: 98_304 for arm in LEARNED_ARMS},
            "learner_transitions_total": 196_608,
        }
        observed = {
            "updates": paired_assertions, "factual_episodes_per_arm": factual_episodes,
            "training_slots_per_arm": training_slots, "backward_per_arm": backward,
            "adam_per_arm": adam, "paired_updates": paired_assertions,
            "precontact_information_assertions": precontact_information_assertions,
            "cells": len(cells),
            "learned_cells": sum(row["arm"] in LEARNED_ARMS for row in cells),
            "uniform_cells": sum(row["arm"] == "UNIFORM_LEGAL" for row in cells),
            "evaluation_episodes": evaluation_episode_count,
            "evaluation_transitions": evaluation_transitions, "descriptors": len(descriptors),
            "tape_uses": tape_uses, "cost_config": costs,
            "torch_threads": torch_threads, "evaluation_preserved": eval_preserved,
            "paired_information_work_equal": paired_information_work_equal,
            "precontact_state_equal": precontact_equal,
            "precontact_evaluation_equal": precontact_evaluation_equal,
            "learner_transitions_per_arm": {
                arm: factual_episodes[arm] * HORIZON for arm in LEARNED_ARMS},
            "learner_transitions_total": sum(factual_episodes.values()) * HORIZON,
        }
        checks = {name: observed[name] == value for name, value in expected.items()}
        complete = all(checks.values())
        completion = {"complete": complete, "checks": checks, "expected": expected, "observed": observed}
    rule_inputs = {
        "complete": complete, "admission_valid": True, "exposure_present": True,
        "paired_information_work_equal": paired_information_work_equal,
        "precontact_full_state_equal": precontact_equal,
        "precontact_evaluation_equal": precontact_evaluation_equal,
        "evaluation_preserved_model_bytes": eval_preserved,
        "required_measurements_present": bool(cells and descriptors and tape_reuse["same_tape_objects_reused"]),
        "learner_transitions": sum(factual_episodes.values()) * HORIZON,
        "factual_transitions": sum(factual_episodes.values()) * HORIZON,
        "training_episodes": sum(factual_episodes.values()),
        "backward_calls": sum(backward.values()), "adam_steps": sum(adam.values()),
        "evaluation_episodes": evaluation_episode_count,
        "first_tight_contact_update": first_contact,
    }
    wall = time.perf_counter() - started
    peak = _peak_rss_bytes()
    summary = {
        "object_id": OBJECT_ID, "test_only": test_only,
        "branch": classify_r128(rule_inputs, test_only=test_only),
        "seed_label": seed_label, "seed_packet_path": str(seed_packet),
        "seed_packet_schema": packet["schema"], "launch_sha": launch_sha,
        "admission": {"path": str(admission_receipt), "validated": True, "facts": admission},
        "deterministic_rule_inputs": rule_inputs, "exposure": exposure_record(updates),
        "runtime_configuration": {"torch_threads": torch_threads, "native_width": 32},
        "completion_audit": completion, "evaluation_tape_reuse": tape_reuse,
        "projection_audit": {
            **projection, "precontact_evaluation_equal": precontact_evaluation_equal,
            "changed_coordinate_inventory": sorted(
                [] if test_only else paired.changed_coordinates
            ),
        },
        "linf_theta_final_minus_initial_over_0_05": distances,
        "cells": cells, "descriptive_estimands": descriptors,
        "work": {
            "observed_training_slots": training_slots, "backward_calls": backward,
            "adam_steps": adam, "expected_cost_law": costs,
            "direct_paired_checks": {
                "status": "TEST_ONLY_NON_RESULT" if test_only else "DIRECT_PRODUCTION",
                "successful_paired_updates": paired_assertions,
                "successful_precontact_information_assertions": precontact_information_assertions,
                "expected_precontact_information_assertions": expected_precontact,
            },
            "per_arm": {
                arm: {
                    "factual_training_episodes": factual_episodes[arm],
                    "factual_transitions": factual_episodes[arm] * HORIZON,
                    "learner_transitions": factual_episodes[arm] * HORIZON,
                    "training_environment_slots": training_slots[arm],
                    "evaluation_episodes": len(checkpoints) * 2 * eval_episodes,
                    "evaluation_environment_slots": len(checkpoints) * 2 * eval_episodes * HORIZON,
                    "backward_calls": backward[arm], "adam_steps": adam[arm],
                    "optimizer_wall_seconds": optimizer_wall[arm],
                }
                for arm in LEARNED_ARMS
            },
        },
        "resources": {
            "wall_seconds": wall, "peak_rss_bytes": peak,
            "status": "measured" if peak is not None else "resources_unmeasured",
            "per_arm_wall_seconds": learned_wall,
            "per_arm_wall_seconds_per_update": {arm: learned_wall[arm] / updates
                                                 for arm in LEARNED_ARMS},
            "per_arm_wall_seconds_per_environment_slot": {
                arm: learned_wall[arm] / costs["learned_total_per_arm"]
                for arm in LEARNED_ARMS
            },
            "observed_slots_per_wall_second": costs["invocation"] / wall,
        },
    }
    (output_root / "summary.json").write_bytes(canonical_json_bytes(summary))
    return summary
def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="FRRIE B01 in-memory R128 smoke")
    for name in ("output-root", "seed-packet", "admission-receipt"):
        value.add_argument(f"--{name}", required=True, type=Path)
    value.add_argument("--seed-label", required=True)
    value.add_argument("--test-only", action="store_true")
    value.add_argument("--toy-updates", type=int, default=1)
    value.add_argument("--toy-eval-episodes", type=int, default=1)
    return value
def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.test_only:
        updates, checkpoints, episodes = 1, (0, 1), 1
    else:
        updates, checkpoints, episodes = PRODUCTION_UPDATES, PRODUCTION_CHECKPOINTS, PRODUCTION_EVAL_EPISODES
    if args.toy_updates != 1 or args.toy_eval_episodes != 1:
        raise B01ContractError("toy controls are fixed to one update/episode")
    execute(
        output_root=args.output_root, seed_packet=args.seed_packet,
        admission_receipt=args.admission_receipt, seed_label=args.seed_label,
        test_only=args.test_only, updates=updates, checkpoints=checkpoints,
        eval_episodes=episodes,
    )
    return 0
__all__ = ["classify_r128", "execute", "exposure_record", "main", "parser"]
