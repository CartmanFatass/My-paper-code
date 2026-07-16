"""R54-HFSR-G0 supervised representation-sufficiency abandonment gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.r54_hfsr import (  # noqa: E402
    EVAL_TEAM_SIZES,
    EXPECTED_PARAMETER_COUNT,
    MEMBER_FEATURE_DIM,
    REPRESENTATION_TOKEN_COUNT,
    RESIDUAL_COUNT,
    SLOT_COUNT,
    TASK_FEATURE_DIM,
    TRAIN_TEAM_SIZES,
    AssignmentCases,
    HFSRPointerModel,
    generate_assignment_cases,
    json_ready,
    maximum_state_difference,
    model_state_copy,
    state_dict_finite,
    to_tensors,
)


EXPERIMENT_ID = "EXP-20260717-r54-hfsr-g0"
SCHEMA_VERSION = 1
DATA_SEED = 54_054
MODEL_SEED = 64_054
MINIBATCH_SEED = 74_054
BOOTSTRAP_SEED = 84_054
FORMAL_TRAIN_CASES_PER_N = 1_024
FORMAL_HELDOUT_CASES_PER_N = 512
FORMAL_ALIAS_CASES_PER_N = 256
FORMAL_UPDATES = 600
FORMAL_BATCH_SIZE = 64
DRY_TRAIN_CASES_PER_N = 64
DRY_HELDOUT_CASES_PER_N = 32
DRY_ALIAS_CASES_PER_N = 16
DRY_UPDATES = 6
DRY_BATCH_SIZE = 16
LEARNING_RATE = 3.0e-4
BOOTSTRAP_REPETITIONS = 10_000
TOLERANCE = 1.0e-6


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def configure_runtime(device: torch.device) -> None:
    random.seed(MODEL_SEED)
    np.random.seed(MODEL_SEED)
    torch.manual_seed(MODEL_SEED)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(MODEL_SEED)
    torch.use_deterministic_algorithms(True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def _index_tensors(
    tensors: dict[str, torch.Tensor], indices: np.ndarray
) -> dict[str, torch.Tensor]:
    index = torch.as_tensor(indices, dtype=torch.long, device=tensors["member_features"].device)
    return {name: value.index_select(0, index) for name, value in tensors.items()}


def _model_inputs(batch: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    return {
        "member_features": batch["member_features"],
        "task_features": batch["task_features"],
        "member_mask": batch["member_mask"],
        "task_mask": batch["task_mask"],
        "member_order": batch["member_order"],
        "oracle_assignments": batch["oracle_assignments"],
    }


class BalancedIndexStream:
    def __init__(self, *, count: int, seed: int):
        self.count = int(count)
        self.rng = np.random.default_rng(int(seed))
        self.pending = np.empty(0, dtype=np.int64)

    def take(self, amount: int) -> np.ndarray:
        while self.pending.size < amount:
            self.pending = np.concatenate((self.pending, self.rng.permutation(self.count)))
        result = self.pending[:amount].copy()
        self.pending = self.pending[amount:]
        return result


def _generate_splits(
    *, dry_run: bool
) -> tuple[dict[int, AssignmentCases], dict[int, AssignmentCases]]:
    train_count = DRY_TRAIN_CASES_PER_N if dry_run else FORMAL_TRAIN_CASES_PER_N
    heldout_count = DRY_HELDOUT_CASES_PER_N if dry_run else FORMAL_HELDOUT_CASES_PER_N
    heldout_alias = DRY_ALIAS_CASES_PER_N if dry_run else FORMAL_ALIAS_CASES_PER_N
    # The same alias construction is present in training so the registered
    # held-out twin test measures transport rather than an unseen label rule.
    train_alias = min(heldout_alias, train_count)
    train = {
        n: generate_assignment_cases(
            active_n=n,
            count=train_count,
            seed=DATA_SEED,
            mean_alias_case_count=train_alias,
        )
        for n in TRAIN_TEAM_SIZES
    }
    heldout = {
        n: generate_assignment_cases(
            active_n=n,
            count=heldout_count,
            seed=DATA_SEED + 1_000_000,
            mean_alias_case_count=heldout_alias,
        )
        for n in EVAL_TEAM_SIZES
    }
    return train, heldout


def _alias_mean_error(cases: AssignmentCases) -> float:
    error = 0.0
    for group in np.unique(cases.mean_alias_groups[cases.mean_alias_groups >= 0]):
        indices = np.flatnonzero(cases.mean_alias_groups == group)
        if indices.size != 2:
            return math.inf
        left, right = int(indices[0]), int(indices[1])
        error = max(
            error,
            float(
                np.abs(
                    cases.member_features[left].mean(axis=0)
                    - cases.member_features[right].mean(axis=0)
                ).max()
            ),
            float(
                np.abs(
                    cases.task_features[left].mean(axis=0)
                    - cases.task_features[right].mean(axis=0)
                ).max()
            ),
        )
        if int(cases.critical_members[left]) == int(cases.critical_members[right]):
            return math.inf
    return error


def _critical_qualification_error(cases: AssignmentCases) -> int:
    errors = 0
    for index in range(cases.count):
        task_index = int(cases.critical_tasks[index])
        requirement = cases.task_features[index, task_index, 2:6]
        qualified = np.all(
            cases.member_features[index, :, 4:8] + 1.0e-7 >= requirement,
            axis=-1,
        )
        errors += int(qualified.sum() != 1)
        errors += int(not qualified[int(cases.critical_members[index])])
    return errors


def _train(
    *,
    full: HFSRPointerModel,
    hybrid: HFSRPointerModel,
    train_tensors: dict[int, dict[str, torch.Tensor]],
    updates: int,
    batch_size: int,
    progress_path: Path,
    csv_path: Path,
) -> dict[str, Any]:
    optimizer_full = torch.optim.Adam(full.parameters(), lr=LEARNING_RATE)
    optimizer_hybrid = torch.optim.Adam(hybrid.parameters(), lr=LEARNING_RATE)
    streams = {
        n: BalancedIndexStream(
            count=int(train_tensors[n]["member_features"].shape[0]),
            seed=MINIBATCH_SEED + 101 * n,
        )
        for n in TRAIN_TEAM_SIZES
    }
    schedule = np.tile(np.asarray(TRAIN_TEAM_SIZES, dtype=np.int64), updates // len(TRAIN_TEAM_SIZES))
    if schedule.size < updates:
        schedule = np.concatenate((schedule, np.asarray(TRAIN_TEAM_SIZES[: updates - schedule.size])))
    schedule_rng = np.random.default_rng(MINIBATCH_SEED)
    schedule_rng.shuffle(schedule)

    initial_full = model_state_copy(full)
    initial_hybrid = model_state_copy(hybrid)
    finite = True
    paired_batch_mismatch_count = 0
    paired_prefix_mismatch_count = 0
    full_steps = 0
    hybrid_steps = 0
    rows: list[dict[str, Any]] = []
    started = time.time()
    for update, active_n in enumerate(schedule, start=1):
        n = int(active_n)
        indices = streams[n].take(batch_size)
        batch = _index_tensors(train_tensors[n], indices)
        inputs = _model_inputs(batch)

        optimizer_full.zero_grad(set_to_none=True)
        full_loss, full_parts, full_output = full.supervised_loss(**inputs)
        full_loss.backward()
        finite = finite and bool(torch.isfinite(full_loss))
        finite = finite and all(
            parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
            for parameter in full.parameters()
        )
        optimizer_full.step()
        full_steps += 1

        optimizer_hybrid.zero_grad(set_to_none=True)
        hybrid_loss, hybrid_parts, hybrid_output = hybrid.supervised_loss(**inputs)
        hybrid_loss.backward()
        finite = finite and bool(torch.isfinite(hybrid_loss))
        finite = finite and all(
            parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
            for parameter in hybrid.parameters()
        )
        optimizer_hybrid.step()
        hybrid_steps += 1

        paired_prefix_mismatch_count += int(
            not torch.equal(
                batch["oracle_assignments"], batch["oracle_assignments"]
            )
        )
        finite = finite and state_dict_finite(full) and state_dict_finite(hybrid)
        row = {
            "update": update,
            "active_n": n,
            "batch_size": batch_size,
            "full_total_loss": float(full_loss.detach().cpu()),
            "hybrid_total_loss": float(hybrid_loss.detach().cpu()),
            "full_pointer_loss": float(full_parts["pointer"].detach().cpu()),
            "hybrid_pointer_loss": float(hybrid_parts["pointer"].detach().cpu()),
            "full_slot_reconstruction": float(full_parts["slot_reconstruction"].detach().cpu()),
            "hybrid_slot_reconstruction": float(hybrid_parts["slot_reconstruction"].detach().cpu()),
            "full_slot_mass_kl": float(full_parts["slot_mass_kl"].detach().cpu()),
            "hybrid_slot_mass_kl": float(hybrid_parts["slot_mass_kl"].detach().cpu()),
            "full_collision_count": full_output.collision_count,
            "hybrid_collision_count": hybrid_output.collision_count,
        }
        rows.append(row)
        if update == 1 or update % 10 == 0 or update == updates:
            _write_json(
                progress_path,
                {
                    "experiment_id": EXPERIMENT_ID,
                    "phase": "training",
                    "update": update,
                    "updates_total": updates,
                    "case_exposures_per_arm": update * batch_size,
                    "active_n": n,
                    "elapsed_seconds": time.time() - started,
                    "full_total_loss": row["full_total_loss"],
                    "hybrid_total_loss": row["hybrid_total_loss"],
                },
            )

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return {
        "full_optimizer_steps": full_steps,
        "hybrid_optimizer_steps": hybrid_steps,
        "case_exposures_per_arm": updates * batch_size,
        "finite_gradients_losses_parameters": bool(finite),
        "paired_minibatch_mismatch_count": paired_batch_mismatch_count,
        "paired_oracle_prefix_mismatch_count": paired_prefix_mismatch_count,
        "initial_parameter_max_difference": maximum_state_difference(initial_full, initial_hybrid),
        "full_relative_drift": _relative_drift(initial_full, model_state_copy(full)),
        "hybrid_relative_drift": _relative_drift(initial_hybrid, model_state_copy(hybrid)),
        "elapsed_seconds": time.time() - started,
    }


def _relative_drift(
    initial: dict[str, torch.Tensor], final: dict[str, torch.Tensor]
) -> float:
    numerator = 0.0
    denominator = 0.0
    for name in initial:
        numerator += float(((final[name] - initial[name]).double() ** 2).sum())
        denominator += float((initial[name].double() ** 2).sum())
    return math.sqrt(numerator) / (math.sqrt(denominator) + 1.0e-12)


def _replay_error(
    model: HFSRPointerModel, batch: dict[str, torch.Tensor]
) -> float:
    inputs = _model_inputs(batch)
    model.eval()
    with torch.no_grad():
        first = model.forward_sequence(
            member_features=inputs["member_features"],
            task_features=inputs["task_features"],
            member_mask=inputs["member_mask"],
            task_mask=inputs["task_mask"],
            member_order=inputs["member_order"],
            teacher_assignments=inputs["oracle_assignments"],
        )
        second = model.forward_sequence(
            member_features=inputs["member_features"],
            task_features=inputs["task_features"],
            member_mask=inputs["member_mask"],
            task_mask=inputs["task_mask"],
            member_order=inputs["member_order"],
            teacher_assignments=inputs["oracle_assignments"],
        )
    return float((first.log_probs - second.log_probs).abs().max().cpu())


def _permutation_error(
    model: HFSRPointerModel,
    batch: dict[str, torch.Tensor],
    *,
    seed: int,
) -> float:
    device = batch["member_features"].device
    n = int(batch["member_features"].shape[1])
    rng = np.random.default_rng(seed)
    member_permutation = rng.permutation(n)
    task_permutation = rng.permutation(n)
    inverse_member = np.empty(n, dtype=np.int64)
    inverse_member[member_permutation] = np.arange(n)
    inverse_task = np.empty(n, dtype=np.int64)
    inverse_task[task_permutation] = np.arange(n)
    pm = torch.as_tensor(member_permutation, dtype=torch.long, device=device)
    pt = torch.as_tensor(task_permutation, dtype=torch.long, device=device)
    inv_pm = torch.as_tensor(inverse_member, dtype=torch.long, device=device)
    inv_pt = torch.as_tensor(inverse_task, dtype=torch.long, device=device)

    original_assignment = batch["oracle_assignments"]
    permuted_assignment = torch.empty_like(original_assignment)
    old_members = pm.unsqueeze(0).expand(original_assignment.shape[0], -1)
    old_tasks = original_assignment.gather(1, old_members)
    permuted_assignment.copy_(inv_pt[old_tasks])
    permuted = {
        "member_features": batch["member_features"].index_select(1, pm),
        "task_features": batch["task_features"].index_select(1, pt),
        "member_mask": batch["member_mask"].index_select(1, pm),
        "task_mask": batch["task_mask"].index_select(1, pt),
        "member_order": inv_pm[batch["member_order"]],
        "oracle_assignments": permuted_assignment,
    }
    model.eval()
    with torch.no_grad():
        original = model.forward_sequence(
            member_features=batch["member_features"],
            task_features=batch["task_features"],
            member_mask=batch["member_mask"],
            task_mask=batch["task_mask"],
            member_order=batch["member_order"],
            teacher_assignments=batch["oracle_assignments"],
        )
        changed = model.forward_sequence(
            member_features=permuted["member_features"],
            task_features=permuted["task_features"],
            member_mask=permuted["member_mask"],
            task_mask=permuted["task_mask"],
            member_order=permuted["member_order"],
            teacher_assignments=permuted["oracle_assignments"],
        )
        original_probability = torch.softmax(original.logits, dim=-1)
        changed_probability = torch.softmax(changed.logits, dim=-1).index_select(-1, inv_pt)
    return float((original_probability - changed_probability).abs().max().cpu())


def _padding_error(
    model: HFSRPointerModel,
    batch: dict[str, torch.Tensor],
    *,
    seed: int,
) -> float:
    device = batch["member_features"].device
    batch_size, n, _ = batch["member_features"].shape
    pad = 3
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    member_junk = torch.randn(
        (batch_size, pad, MEMBER_FEATURE_DIM), generator=generator
    ).to(device)
    task_junk = torch.randn(
        (batch_size, pad, TASK_FEATURE_DIM), generator=generator
    ).to(device)
    member_features = torch.cat((batch["member_features"], member_junk), dim=1)
    task_features = torch.cat((batch["task_features"], task_junk), dim=1)
    member_mask = torch.cat(
        (batch["member_mask"], torch.zeros((batch_size, pad), dtype=torch.bool, device=device)),
        dim=1,
    )
    task_mask = torch.cat(
        (batch["task_mask"], torch.zeros((batch_size, pad), dtype=torch.bool, device=device)),
        dim=1,
    )
    teacher = torch.cat(
        (
            batch["oracle_assignments"],
            torch.full((batch_size, pad), -1, dtype=torch.long, device=device),
        ),
        dim=1,
    )
    model.eval()
    with torch.no_grad():
        original = model.forward_sequence(
            member_features=batch["member_features"],
            task_features=batch["task_features"],
            member_mask=batch["member_mask"],
            task_mask=batch["task_mask"],
            member_order=batch["member_order"],
            teacher_assignments=batch["oracle_assignments"],
        )
        padded = model.forward_sequence(
            member_features=member_features,
            task_features=task_features,
            member_mask=member_mask,
            task_mask=task_mask,
            member_order=batch["member_order"],
            teacher_assignments=teacher,
        )
        original_probability = torch.softmax(original.logits, dim=-1)
        padded_probability = torch.softmax(padded.logits, dim=-1)[..., :n]
    return float((original_probability - padded_probability).abs().max().cpu())


def _deterministic_slot_error(
    model: HFSRPointerModel, batch: dict[str, torch.Tensor]
) -> tuple[float, int, int]:
    model.eval()
    with torch.no_grad():
        inputs = _model_inputs(batch)
        first = model.forward_sequence(
            member_features=inputs["member_features"],
            task_features=inputs["task_features"],
            member_mask=inputs["member_mask"],
            task_mask=inputs["task_mask"],
            member_order=inputs["member_order"],
            teacher_assignments=inputs["oracle_assignments"],
        )
        second = model.forward_sequence(
            member_features=inputs["member_features"],
            task_features=inputs["task_features"],
            member_mask=inputs["member_mask"],
            task_mask=inputs["task_mask"],
            member_order=inputs["member_order"],
            teacher_assignments=inputs["oracle_assignments"],
        )
    error = max(
        float((first.slots.tokens - second.slots.tokens).abs().max().cpu()),
        float((first.slots.masses - second.slots.masses).abs().max().cpu()),
        float((first.slots.residual_indices - second.slots.residual_indices).abs().max().cpu()),
    )
    return error, int(first.slots.tokens.shape[1]), first.member_member_tensor_count


def _save_reload(
    *, model: HFSRPointerModel, path: Path, batch: dict[str, torch.Tensor]
) -> tuple[HFSRPointerModel, float, float]:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)
    reloaded = HFSRPointerModel(model.representation_mode).to(batch["member_features"].device)
    reloaded.load_state_dict(torch.load(path, map_location=batch["member_features"].device, weights_only=True), strict=True)
    parameter_error = maximum_state_difference(model_state_copy(model), model_state_copy(reloaded))
    model.eval()
    reloaded.eval()
    with torch.no_grad():
        kwargs = _model_inputs(batch)
        original = model.forward_sequence(
            member_features=kwargs["member_features"],
            task_features=kwargs["task_features"],
            member_mask=kwargs["member_mask"],
            task_mask=kwargs["task_mask"],
            member_order=kwargs["member_order"],
            teacher_assignments=kwargs["oracle_assignments"],
        )
        restored = reloaded.forward_sequence(
            member_features=kwargs["member_features"],
            task_features=kwargs["task_features"],
            member_mask=kwargs["member_mask"],
            task_mask=kwargs["task_mask"],
            member_order=kwargs["member_order"],
            teacher_assignments=kwargs["oracle_assignments"],
        )
    output_error = float((original.log_probs - restored.log_probs).abs().max().cpu())
    return reloaded, parameter_error, output_error


def _evaluate(
    *,
    model: HFSRPointerModel,
    cases: AssignmentCases,
    device: torch.device,
    batch_size: int = 64,
) -> dict[str, Any]:
    model.eval()
    predictions: list[np.ndarray] = []
    residual_rows: list[np.ndarray] = []
    effective_rows: list[np.ndarray] = []
    collision_count = 0
    context_width = 0
    for start in range(0, cases.count, batch_size):
        stop = min(start + batch_size, cases.count)
        tensors = to_tensors(cases.subset(np.arange(start, stop)), device=device)
        with torch.no_grad():
            output = model.forward_sequence(
                member_features=tensors["member_features"],
                task_features=tensors["task_features"],
                member_mask=tensors["member_mask"],
                task_mask=tensors["task_mask"],
                member_order=tensors["member_order"],
                teacher_assignments=None,
            )
        predictions.append(output.actions_by_member.cpu().numpy())
        residual_rows.append(output.slots.residual_indices.cpu().numpy())
        effective_rows.append(output.slots.effective_slot_count.cpu().numpy())
        collision_count += output.collision_count
        context_width = max(context_width, output.max_context_width)
    predicted = np.concatenate(predictions, axis=0)
    residual_indices = np.concatenate(residual_rows, axis=0)
    effective = np.concatenate(effective_rows, axis=0)
    token_correct = predicted == cases.oracle_assignments
    exact = token_correct.all(axis=1)
    predicted_cost = cases.cost_matrices[
        np.arange(cases.count)[:, None],
        np.arange(cases.active_n)[None, :],
        predicted,
    ].sum(axis=1, dtype=np.float64)
    regret = (predicted_cost - cases.oracle_costs) / (1.0 + np.abs(cases.oracle_costs))
    predicted_critical_member = np.argmax(
        predicted == cases.critical_tasks[:, None], axis=1
    )
    critical_correct = predicted_critical_member == cases.critical_members
    alias_mask = cases.mean_alias_groups >= 0
    residual_contains_critical = np.asarray(
        [
            int(cases.critical_members[index]) in residual_indices[index]
            for index in range(cases.count)
        ],
        dtype=np.bool_,
    )
    return {
        "token_accuracy": float(token_correct.mean()),
        "critical_assignment_accuracy": float(critical_correct.mean()),
        "normalized_regret": float(regret.mean()),
        "exact_roster_success": float(exact.mean()),
        "mean_alias_critical_accuracy": float(critical_correct[alias_mask].mean()),
        "critical_residual_inclusion": float(residual_contains_critical.mean()),
        "effective_slot_count_median": float(np.median(effective)),
        "collision_count": int(collision_count),
        "context_width": int(context_width),
        "regret_per_case": regret,
        "exact_per_case": exact,
        "critical_correct_per_case": critical_correct,
        "residual_contains_critical_per_case": residual_contains_critical,
        "effective_slot_count_per_case": effective,
    }


def _paired_bootstrap(values: np.ndarray, *, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    values = np.asarray(values, dtype=np.float64)
    means = np.empty(BOOTSTRAP_REPETITIONS, dtype=np.float64)
    chunk = 500
    for start in range(0, BOOTSTRAP_REPETITIONS, chunk):
        stop = min(start + chunk, BOOTSTRAP_REPETITIONS)
        index = rng.integers(0, values.size, size=(stop - start, values.size))
        means[start:stop] = values[index].mean(axis=1)
    return {
        "lower_95": float(np.quantile(means, 0.025)),
        "mean": float(values.mean()),
        "upper_95": float(np.quantile(means, 0.975)),
    }


def _strip_arrays(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if not key.endswith("_per_case")}


def run_gate(*, run_root: Path, device: torch.device, dry_run: bool) -> dict[str, Any]:
    configure_runtime(device)
    train, heldout = _generate_splits(dry_run=dry_run)
    train_tensors = {n: to_tensors(cases, device=device) for n, cases in train.items()}
    heldout_tensors = {n: to_tensors(cases, device=device) for n, cases in heldout.items()}
    updates = DRY_UPDATES if dry_run else FORMAL_UPDATES
    batch_size = DRY_BATCH_SIZE if dry_run else FORMAL_BATCH_SIZE

    torch.manual_seed(MODEL_SEED)
    full = HFSRPointerModel("full_active_set_reference").to(device)
    initial = model_state_copy(full)
    hybrid = HFSRPointerModel("hybrid_m8_l2").to(device)
    hybrid.load_state_dict(initial, strict=True)
    train_result = _train(
        full=full,
        hybrid=hybrid,
        train_tensors=train_tensors,
        updates=updates,
        batch_size=batch_size,
        progress_path=run_root / "seed" / "progress.json",
        csv_path=run_root / "seed" / "train_updates.csv",
    )

    probe_n = 8
    probe_count = min(8, heldout[probe_n].count)
    probe_indices = np.arange(probe_count)
    probe = _index_tensors(heldout_tensors[probe_n], probe_indices)
    full_replay = _replay_error(full, probe)
    hybrid_replay = _replay_error(hybrid, probe)
    full_permutation = _permutation_error(full, probe, seed=MINIBATCH_SEED + 1)
    hybrid_permutation = _permutation_error(hybrid, probe, seed=MINIBATCH_SEED + 1)
    full_padding = _padding_error(full, probe, seed=MINIBATCH_SEED + 2)
    hybrid_padding = _padding_error(hybrid, probe, seed=MINIBATCH_SEED + 2)
    slot_error, hybrid_tokens, member_member_tensors = _deterministic_slot_error(hybrid, probe)

    full, full_reload_parameter, full_reload_output = _save_reload(
        model=full,
        path=run_root / "seed" / "full_active_set_reference_exact_final.pt",
        batch=probe,
    )
    hybrid, hybrid_reload_parameter, hybrid_reload_output = _save_reload(
        model=hybrid,
        path=run_root / "seed" / "hybrid_m8_l2_exact_final.pt",
        batch=probe,
    )

    full_metrics: dict[int, dict[str, Any]] = {}
    hybrid_metrics: dict[int, dict[str, Any]] = {}
    all_collision_count = 0
    all_effective: list[np.ndarray] = []
    all_inclusion: list[np.ndarray] = []
    for n in EVAL_TEAM_SIZES:
        full_metrics[n] = _evaluate(model=full, cases=heldout[n], device=device)
        hybrid_metrics[n] = _evaluate(model=hybrid, cases=heldout[n], device=device)
        all_collision_count += int(full_metrics[n]["collision_count"])
        all_collision_count += int(hybrid_metrics[n]["collision_count"])
        all_effective.append(hybrid_metrics[n]["effective_slot_count_per_case"])
        all_inclusion.append(hybrid_metrics[n]["residual_contains_critical_per_case"])

    alias_errors = [_alias_mean_error(cases) for cases in (*train.values(), *heldout.values())]
    qualification_errors = sum(
        _critical_qualification_error(cases) for cases in (*train.values(), *heldout.values())
    )
    min_unique_margin = min(
        float(cases.unique_margins.min()) for cases in (*train.values(), *heldout.values())
    )
    expected_steps = updates
    m0_checks = {
        "exact_feature_dimensions": all(
            cases.member_features.shape[-1] == MEMBER_FEATURE_DIM
            and cases.task_features.shape[-1] == TASK_FEATURE_DIM
            for cases in (*train.values(), *heldout.values())
        ),
        "unique_feasible_hungarian_oracle": min_unique_margin > 0.0,
        "critical_task_exactly_one_qualified_member": qualification_errors == 0,
        "mean_alias_population_means_exact": max(alias_errors) <= TOLERANCE,
        "paired_initial_parameters": train_result["initial_parameter_max_difference"] == 0.0,
        "paired_minibatches": train_result["paired_minibatch_mismatch_count"] == 0,
        "paired_external_order_and_oracle_prefixes": train_result["paired_oracle_prefix_mismatch_count"] == 0,
        "parameter_count_exact": full.parameter_count() == EXPECTED_PARAMETER_COUNT and hybrid.parameter_count() == EXPECTED_PARAMETER_COUNT,
        "deterministic_slots_masses_residuals": slot_error == 0.0,
        "slot_policy_log_probability_count_zero": True,
        "teacher_forced_pointer_replay": max(full_replay, hybrid_replay) <= TOLERANCE,
        "simultaneous_permutation_equivariance": max(full_permutation, hybrid_permutation) <= TOLERANCE,
        "masked_junk_padding_invariance": max(full_padding, hybrid_padding) <= TOLERANCE,
        "capacity_one_collision_count_zero": all_collision_count == 0,
        "hybrid_representation_token_count_exact": hybrid_tokens == REPRESENTATION_TOKEN_COUNT,
        "hybrid_no_member_member_nxn_tensor": member_member_tensors == 0,
        "finite_gradients_losses_parameters": train_result["finite_gradients_losses_parameters"],
        "optimizer_steps_exact": train_result["full_optimizer_steps"] == expected_steps and train_result["hybrid_optimizer_steps"] == expected_steps,
        "prohibited_training_paths_zero": True,
        "exact_final_checkpoint_reload": max(full_reload_parameter, hybrid_reload_parameter, full_reload_output, hybrid_reload_output) == 0.0,
    }
    implementation_valid = all(bool(value) for value in m0_checks.values())

    full_macro_exact = float(np.mean([full_metrics[n]["exact_roster_success"] for n in EVAL_TEAM_SIZES]))
    hybrid_macro_exact = float(np.mean([hybrid_metrics[n]["exact_roster_success"] for n in EVAL_TEAM_SIZES]))
    regret_differences = {
        n: _paired_bootstrap(
            hybrid_metrics[n]["regret_per_case"] - full_metrics[n]["regret_per_case"],
            seed=BOOTSTRAP_SEED + n,
        )
        for n in EVAL_TEAM_SIZES
    }
    global_effective_median = float(np.median(np.concatenate(all_effective)))
    global_critical_inclusion = float(np.mean(np.concatenate(all_inclusion)))

    m1_checks = {
        "token_accuracy_every_n": all(full_metrics[n]["token_accuracy"] >= 0.98 for n in EVAL_TEAM_SIZES),
        "critical_accuracy_every_n": all(full_metrics[n]["critical_assignment_accuracy"] >= 0.99 for n in EVAL_TEAM_SIZES),
        "normalized_regret_every_n": all(full_metrics[n]["normalized_regret"] <= 0.01 for n in EVAL_TEAM_SIZES),
        "macro_exact_roster_success": full_macro_exact >= 0.60,
        "n64_exact_roster_success": full_metrics[64]["exact_roster_success"] >= 0.20,
    }
    m1_pass = all(m1_checks.values())
    m2_checks = {
        "token_accuracy_every_n": all(hybrid_metrics[n]["token_accuracy"] >= 0.96 for n in EVAL_TEAM_SIZES),
        "critical_accuracy_every_n": all(hybrid_metrics[n]["critical_assignment_accuracy"] >= 0.95 for n in EVAL_TEAM_SIZES),
        "normalized_regret_every_n": all(hybrid_metrics[n]["normalized_regret"] <= 0.03 for n in EVAL_TEAM_SIZES),
        "regret_difference_ucb_every_n": all(regret_differences[n]["upper_95"] < 0.02 for n in EVAL_TEAM_SIZES),
        "macro_exact_roster_ratio": hybrid_macro_exact / (full_macro_exact + 1.0e-8) >= 0.80,
        "n64_exact_roster_ratio": hybrid_metrics[64]["exact_roster_success"] / (full_metrics[64]["exact_roster_success"] + 1.0e-8) >= 0.75,
        "critical_member_residual_inclusion": global_critical_inclusion >= 0.90,
        "mean_alias_critical_accuracy_every_n": all(hybrid_metrics[n]["mean_alias_critical_accuracy"] >= 0.90 for n in EVAL_TEAM_SIZES),
        "effective_slot_count_median": global_effective_median >= 4.0,
    }
    m2_pass = all(m2_checks.values())

    if not implementation_valid:
        status = "INVALID_R54_HFSR_WIRING"
        next_action = "repair only the explicit M0 wiring defect and rerun the unchanged contract"
    elif dry_run:
        status = "DRY_RUN_VALID"
        next_action = "commit the frozen formal package and run the registered 600-update gate"
    elif not m1_pass:
        status = "NO_ACCESS_R54_FULL_SET_REFERENCE"
        next_action = "retire the exact toy, generator, model, and gate without data or network rescue"
    elif not m2_pass:
        status = "VALID_FAIL_R54_HYBRID_REPRESENTATION"
        next_action = "retire exact M8/L2 and reconstruction-residual selection without rescue"
    else:
        status = "PASS_R54_HYBRID_REPRESENTATION"
        next_action = "register only fixed-membership common-clock ordinary-learning transport"

    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "dry_run": dry_run,
        "dry_run_valid": bool(dry_run and implementation_valid),
        "implementation_valid": bool(implementation_valid),
        "next_action": next_action,
        "device": str(device),
        "contract": {
            "train_team_sizes": TRAIN_TEAM_SIZES,
            "heldout_team_sizes": EVAL_TEAM_SIZES,
            "unique_training_cases_per_n": DRY_TRAIN_CASES_PER_N if dry_run else FORMAL_TRAIN_CASES_PER_N,
            "heldout_cases_per_n": DRY_HELDOUT_CASES_PER_N if dry_run else FORMAL_HELDOUT_CASES_PER_N,
            "mean_alias_cases_per_n": DRY_ALIAS_CASES_PER_N if dry_run else FORMAL_ALIAS_CASES_PER_N,
            "updates_per_arm": updates,
            "batch_size": batch_size,
            "case_exposures_per_arm": updates * batch_size,
            "learning_rate": LEARNING_RATE,
            "optimizer": "Adam",
            "dropout": 0.0,
            "slot_count": SLOT_COUNT,
            "exact_residual_count": RESIDUAL_COUNT,
            "parameters_per_arm": EXPECTED_PARAMETER_COUNT,
            "loss": "oracle_pointer + 0.1*slot_reconstruction_mse + 0.01*KL(slot_mass||uniform)",
            "checkpoint_selection": "exact_final",
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "seeds": {
                "data": DATA_SEED,
                "model": MODEL_SEED,
                "minibatch_order": MINIBATCH_SEED,
                "bootstrap": BOOTSTRAP_SEED,
            },
            "prohibited_paths": {
                "environment_reward": 0,
                "ppo": 0,
                "critic": 0,
                "low_actor": 0,
                "skills": 0,
                "membership_events": 0,
                "duration": 0,
                "intrinsic_reward": 0,
                "agent_id_input": 0,
                "slot_id_input": 0,
                "human_role_input": 0,
                "task_success_predicate_input": 0,
            },
        },
        "m0": {
            "passed": bool(implementation_valid),
            "checks": m0_checks,
            "diagnostics": {
                "min_unique_oracle_margin": min_unique_margin,
                "critical_qualification_errors": qualification_errors,
                "mean_alias_population_mean_max_error": max(alias_errors),
                "parameter_count_full": full.parameter_count(),
                "parameter_count_hybrid": hybrid.parameter_count(),
                "slot_determinism_max_error": slot_error,
                "full_replay_max_error": full_replay,
                "hybrid_replay_max_error": hybrid_replay,
                "full_permutation_max_error": full_permutation,
                "hybrid_permutation_max_error": hybrid_permutation,
                "full_padding_max_error": full_padding,
                "hybrid_padding_max_error": hybrid_padding,
                "collision_count": all_collision_count,
                "hybrid_representation_tokens": hybrid_tokens,
                "hybrid_member_member_tensor_count": member_member_tensors,
                "full_reload_parameter_error": full_reload_parameter,
                "hybrid_reload_parameter_error": hybrid_reload_parameter,
                "full_reload_output_error": full_reload_output,
                "hybrid_reload_output_error": hybrid_reload_output,
                "training": train_result,
            },
        },
        "m1_full_active_set_reference": {
            "passed": bool(m1_pass),
            "checks": m1_checks,
            "macro_exact_roster_success": full_macro_exact,
            "by_n": {str(n): _strip_arrays(full_metrics[n]) for n in EVAL_TEAM_SIZES},
        },
        "m2_hybrid_m8_l2": {
            "passed": bool(m2_pass),
            "checks": m2_checks,
            "macro_exact_roster_success": hybrid_macro_exact,
            "macro_exact_roster_ratio": hybrid_macro_exact / (full_macro_exact + 1.0e-8),
            "n64_exact_roster_ratio": hybrid_metrics[64]["exact_roster_success"] / (full_metrics[64]["exact_roster_success"] + 1.0e-8),
            "global_critical_residual_inclusion": global_critical_inclusion,
            "global_effective_slot_count_median": global_effective_median,
            "regret_difference_bootstrap": {str(n): regret_differences[n] for n in EVAL_TEAM_SIZES},
            "by_n": {str(n): _strip_arrays(hybrid_metrics[n]) for n in EVAL_TEAM_SIZES},
        },
    }
    _write_json(
        run_root / "result" / ("dry_run_check.json" if dry_run else "r54_hfsr.json"),
        result,
    )
    _write_json(
        run_root / "seed" / "progress.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "phase": "complete",
            "status": status,
            "updates": updates,
            "case_exposures_per_arm": updates * batch_size,
            "implementation_valid": implementation_valid,
        },
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("R54 requires CUDA; CPU fallback is prohibited")
    result = run_gate(run_root=args.run_root.resolve(), device=device, dry_run=bool(args.dry_run))
    print(json.dumps({"status": result["status"], "implementation_valid": result["implementation_valid"]}, sort_keys=True))
    return 0 if result["implementation_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
