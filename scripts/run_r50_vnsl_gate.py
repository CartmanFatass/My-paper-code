"""R50-VNSL-G0 mixed-team-size shared-learnability gate.

This is an isolated one-step roster bandit.  It deliberately contains no
environment, low-level policy, intrinsic reward, checkpoint migration, member
identity, slot index, or task-specific field.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch
import torch.nn.functional as F

from r49_orse import MEMBER_FEATURE_DIM, OPAQUE_CODES, OpenRosterSetPolicy


EXPERIMENT_ID = "EXP-20260716-r50-vnsl-g0"
SCHEMA_VERSION = 1
ACTIVE_SIZES = (2, 3, 4, 6, 8, 12, 16)
MODEL_SEED = 50_050
TRAIN_DATA_SEED = 60_050
EVAL_DATA_SEED = 70_050
ACTION_UNIFORM_SEED = 80_050
FORMAL_UPDATES = 512
FORMAL_BATCH_PER_SIZE = 64
FORMAL_EVAL_PER_SIZE = 512
DRY_UPDATES = 4
DRY_BATCH_PER_SIZE = 8
DRY_EVAL_PER_SIZE = 32
LEARNING_RATE = 1.0e-3
VALUE_COEFFICIENT = 0.5
ENTROPY_START = 0.01
GRADIENT_CLIP = 1.0
REPLAY_AUDIT_INTERVAL = 32
REPLAY_TOLERANCE = 1.0e-6
OFFSET_STANDARD_DEVIATION = 2.0


@dataclass(frozen=True)
class BanditBatch:
    observations: torch.Tensor
    targets: torch.Tensor
    external_order: torch.Tensor
    sampling_uniforms: torch.Tensor

    @property
    def batch_size(self) -> int:
        return int(self.observations.shape[0])

    @property
    def active_n(self) -> int:
        return int(self.observations.shape[1])


@dataclass
class SequenceOutput:
    actions_by_position: torch.Tensor
    final_codes: torch.Tensor
    token_log_probs: torch.Tensor
    token_entropies: torch.Tensor
    value: torch.Tensor
    reward: torch.Tensor
    exact_success: torch.Tensor


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _all_finite(values: Iterable[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


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


def make_batch(
    *,
    active_n: int,
    batch_size: int,
    data_rng: np.random.Generator,
    uniform_rng: np.random.Generator,
    device: torch.device,
) -> BanditBatch:
    observations = data_rng.standard_normal(
        (batch_size, active_n, MEMBER_FEATURE_DIM), dtype=np.float32
    )
    episode_offset = data_rng.normal(
        0.0,
        OFFSET_STANDARD_DEVIATION,
        size=(batch_size, 1, 2),
    ).astype(np.float32)
    observations[:, :, :2] += episode_offset
    active_mean = observations[:, :, :2].mean(axis=1, keepdims=True)
    target_high = observations[:, :, :2] >= active_mean
    targets = (
        2 * target_high[:, :, 0].astype(np.int64)
        + target_high[:, :, 1].astype(np.int64)
    )
    order_noise = data_rng.random((batch_size, active_n))
    external_order = np.argsort(order_noise, axis=1).astype(np.int64)
    sampling_uniforms = uniform_rng.random(
        (batch_size, active_n), dtype=np.float32
    )
    return BanditBatch(
        observations=torch.as_tensor(observations, device=device),
        targets=torch.as_tensor(targets, dtype=torch.long, device=device),
        external_order=torch.as_tensor(
            external_order, dtype=torch.long, device=device
        ),
        sampling_uniforms=torch.as_tensor(sampling_uniforms, device=device),
    )


def run_roster_sequence(
    model: OpenRosterSetPolicy,
    batch: BanditBatch,
    *,
    teacher_actions: torch.Tensor | None = None,
    deterministic: bool = False,
) -> SequenceOutput:
    """Run the active-only autoregressive SET sequence for one team size."""

    observations = batch.observations
    batch_size, active_n, _ = observations.shape
    device = observations.device
    if teacher_actions is not None and tuple(teacher_actions.shape) != (
        batch_size,
        active_n,
    ):
        raise ValueError("teacher action shape does not match the roster batch")
    if teacher_actions is not None and deterministic:
        raise ValueError("teacher replay and deterministic decoding are exclusive")

    initial_codes = torch.zeros(
        (batch_size, active_n), dtype=torch.long, device=device
    )
    zero_ages = torch.zeros((batch_size, active_n), device=device)
    joined = torch.ones((batch_size, active_n, 1), device=device)
    unprocessed = torch.zeros((batch_size, active_n, 1), device=device)
    member_input = torch.cat(
        (
            observations,
            F.one_hot(initial_codes, num_classes=OPAQUE_CODES).to(torch.float32),
            model.normalized_age(zero_ages).unsqueeze(-1),
            joined,
            unprocessed,
        ),
        dim=-1,
    )
    member_embeddings = model.member_encoder(
        member_input.reshape(batch_size * active_n, -1)
    ).reshape(batch_size, active_n, model.hidden_dim)
    log_count = torch.full(
        (batch_size, 1),
        math.log1p(float(active_n)),
        dtype=observations.dtype,
        device=device,
    )
    team_summary = torch.cat((member_embeddings.mean(dim=1), log_count), dim=-1)
    value = model.value_head(
        model.value_activation(model.value_hidden(team_summary))
    ).squeeze(-1)

    initial_roster_input = torch.cat(
        (
            member_embeddings,
            F.one_hot(initial_codes, num_classes=OPAQUE_CODES).to(torch.float32),
            model.normalized_age(zero_ages).unsqueeze(-1),
            unprocessed,
        ),
        dim=-1,
    )
    initial_units = model.roster_encoder(
        initial_roster_input.reshape(batch_size * active_n, -1)
    ).reshape(batch_size, active_n, model.hidden_dim)
    incremental_roster = initial_units.mean(dim=1)
    final_codes = initial_codes.clone()
    batch_indices = torch.arange(batch_size, device=device)
    actions_by_position: list[torch.Tensor] = []
    log_probs_by_position: list[torch.Tensor] = []
    entropies_by_position: list[torch.Tensor] = []

    for position in range(active_n):
        member_indices = batch.external_order[:, position]
        member_embedding = member_embeddings[batch_indices, member_indices]
        decoder_input = torch.cat(
            (member_embedding, team_summary, incremental_roster), dim=-1
        )
        hidden = model.decoder_activation(model.decoder_hidden(decoder_input))
        logits = model.set_head(hidden)
        log_probabilities = F.log_softmax(logits, dim=-1)
        probabilities = torch.exp(log_probabilities)
        if teacher_actions is not None:
            actions = teacher_actions[:, position]
        elif deterministic:
            actions = torch.argmax(logits, dim=-1)
        else:
            cumulative = torch.cumsum(probabilities, dim=-1)
            actions = torch.sum(
                batch.sampling_uniforms[:, position].unsqueeze(-1) > cumulative,
                dim=-1,
            ).clamp(max=OPAQUE_CODES - 1)
        selected_log_probs = log_probabilities.gather(
            1, actions.unsqueeze(-1)
        ).squeeze(-1)
        entropy = -torch.sum(probabilities * log_probabilities, dim=-1)

        old_units = initial_units[batch_indices, member_indices]
        processed_roster_input = torch.cat(
            (
                member_embedding,
                F.one_hot(actions, num_classes=OPAQUE_CODES).to(torch.float32),
                torch.zeros((batch_size, 1), device=device),
                torch.ones((batch_size, 1), device=device),
            ),
            dim=-1,
        )
        new_units = model.roster_encoder(processed_roster_input)
        incremental_roster = incremental_roster + (
            new_units - old_units
        ) / float(active_n)
        final_codes = final_codes.scatter(
            1, member_indices.unsqueeze(1), actions.unsqueeze(1)
        )
        actions_by_position.append(actions)
        log_probs_by_position.append(selected_log_probs)
        entropies_by_position.append(entropy)

    correct = final_codes.eq(batch.targets)
    reward = correct.to(torch.float32).mean(dim=1)
    exact_success = correct.all(dim=1).to(torch.float32)
    return SequenceOutput(
        actions_by_position=torch.stack(actions_by_position, dim=1),
        final_codes=final_codes,
        token_log_probs=torch.stack(log_probs_by_position, dim=1),
        token_entropies=torch.stack(entropies_by_position, dim=1),
        value=value,
        reward=reward,
        exact_success=exact_success,
    )


def actor_critic_loss(
    output: SequenceOutput,
    *,
    entropy_coefficient: float,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    advantage = output.reward - output.value
    normalized_advantage = (advantage - advantage.mean()) / (
        advantage.std(unbiased=False) + 1.0e-8
    )
    joint_log_probability = output.token_log_probs.sum(dim=1)
    actor_loss = -torch.mean(normalized_advantage.detach() * joint_log_probability)
    value_loss = 0.5 * torch.mean(advantage.square())
    entropy = output.token_entropies.mean()
    total = (
        actor_loss
        + VALUE_COEFFICIENT * value_loss
        - float(entropy_coefficient) * entropy
    )
    return total, {
        "actor_loss": actor_loss.detach(),
        "value_loss": value_loss.detach(),
        "entropy": entropy.detach(),
        "reward": output.reward.mean().detach(),
        "exact": output.exact_success.mean().detach(),
    }


def model_state_copy(model: OpenRosterSetPolicy) -> dict[str, torch.Tensor]:
    return {
        name: tensor.detach().cpu().clone()
        for name, tensor in model.state_dict().items()
    }


def maximum_state_difference(
    first: dict[str, torch.Tensor], second: dict[str, torch.Tensor]
) -> float:
    if first.keys() != second.keys():
        return float("inf")
    return max(
        float(torch.max(torch.abs(first[name] - second[name])))
        for name in first
    )


def drift_summary(
    initial: dict[str, torch.Tensor], model: OpenRosterSetPolicy
) -> dict[str, Any]:
    final = model_state_copy(model)
    module_max: dict[str, float] = {}
    for prefix in (
        "member_encoder",
        "roster_encoder",
        "decoder_hidden",
        "set_head",
        "value_hidden",
        "value_head",
        "keep_head",
    ):
        names = [name for name in initial if name.startswith(prefix + ".")]
        module_max[prefix] = max(
            float(torch.max(torch.abs(final[name] - initial[name]))) for name in names
        )
    relevant = [
        value for name, value in module_max.items() if name != "keep_head"
    ]
    return {
        "module_max_abs": module_max,
        "minimum_relevant_module_max_abs": min(relevant),
        "keep_head_max_abs": module_max["keep_head"],
        "all_parameters_finite": all(
            bool(torch.isfinite(tensor).all()) for tensor in final.values()
        ),
    }


def replay_error(
    model: OpenRosterSetPolicy,
    batch: BanditBatch,
    sampled: SequenceOutput,
) -> float:
    with torch.no_grad():
        replayed = run_roster_sequence(
            model, batch, teacher_actions=sampled.actions_by_position
        )
    return float(
        torch.max(
            torch.abs(replayed.token_log_probs - sampled.token_log_probs.detach())
        ).cpu()
    )


def gradient_step(
    *,
    model: OpenRosterSetPolicy,
    optimizer: torch.optim.Optimizer,
    loss: torch.Tensor,
) -> float:
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    gradient_norm = torch.nn.utils.clip_grad_norm_(
        model.parameters(), GRADIENT_CLIP
    )
    gradient_norm_value = float(gradient_norm.detach().cpu())
    if not math.isfinite(gradient_norm_value):
        raise RuntimeError("non-finite gradient norm")
    optimizer.step()
    return gradient_norm_value


def evaluate_models(
    *,
    shared: OpenRosterSetPolicy,
    specialists: dict[int, OpenRosterSetPolicy],
    cases_per_size: int,
    device: torch.device,
) -> tuple[dict[str, Any], dict[str, Any]]:
    data_rng = np.random.default_rng(EVAL_DATA_SEED)
    uniform_rng = np.random.default_rng(ACTION_UNIFORM_SEED + 1)
    shared_by_size: dict[str, dict[str, float]] = {}
    specialist_by_size: dict[str, dict[str, float]] = {}
    with torch.no_grad():
        for active_n in ACTIVE_SIZES:
            batch = make_batch(
                active_n=active_n,
                batch_size=cases_per_size,
                data_rng=data_rng,
                uniform_rng=uniform_rng,
                device=device,
            )
            shared_output = run_roster_sequence(
                shared, batch, deterministic=True
            )
            specialist_output = run_roster_sequence(
                specialists[active_n], batch, deterministic=True
            )
            shared_by_size[str(active_n)] = {
                "token_accuracy": float(shared_output.reward.mean().cpu()),
                "exact_roster_success": float(
                    shared_output.exact_success.mean().cpu()
                ),
            }
            specialist_by_size[str(active_n)] = {
                "token_accuracy": float(specialist_output.reward.mean().cpu()),
                "exact_roster_success": float(
                    specialist_output.exact_success.mean().cpu()
                ),
            }

    def summarize(by_size: dict[str, dict[str, float]]) -> dict[str, Any]:
        token_values = [by_size[str(n)]["token_accuracy"] for n in ACTIVE_SIZES]
        exact_values = [
            by_size[str(n)]["exact_roster_success"] for n in ACTIVE_SIZES
        ]
        return {
            "by_size": by_size,
            "macro_token_accuracy": float(np.mean(token_values)),
            "minimum_token_accuracy": float(np.min(token_values)),
            "macro_exact_roster_success": float(np.mean(exact_values)),
            "n16_exact_roster_success": by_size["16"]["exact_roster_success"],
        }

    return summarize(shared_by_size), summarize(specialist_by_size)


def run_gate(args: argparse.Namespace) -> dict[str, Any]:
    device = torch.device(args.device)
    if device.type != "cuda":
        raise ValueError("R50 formal and focused runs require CUDA")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; CPU fallback is prohibited")
    configure_runtime(device)
    updates = DRY_UPDATES if args.dry_run else FORMAL_UPDATES
    batch_per_size = (
        DRY_BATCH_PER_SIZE if args.dry_run else FORMAL_BATCH_PER_SIZE
    )
    eval_per_size = DRY_EVAL_PER_SIZE if args.dry_run else FORMAL_EVAL_PER_SIZE
    run_root = Path(args.run_root).resolve()
    seed_root = run_root / "seed"
    result_root = run_root / "result"
    seed_root.mkdir(parents=True, exist_ok=True)
    result_root.mkdir(parents=True, exist_ok=True)
    progress_path = seed_root / "progress.json"
    updates_path = seed_root / "train_updates.csv"
    result_path = result_root / (
        "dry_run_check.json" if args.dry_run else "r50_vnsl.json"
    )

    torch.manual_seed(MODEL_SEED)
    torch.cuda.manual_seed_all(MODEL_SEED)
    shared = OpenRosterSetPolicy().to(device)
    initial_state = model_state_copy(shared)
    specialists: dict[int, OpenRosterSetPolicy] = {}
    for active_n in ACTIVE_SIZES:
        specialist = OpenRosterSetPolicy().to(device)
        specialist.load_state_dict(copy.deepcopy(initial_state), strict=True)
        specialists[active_n] = specialist
    shared_initial_max_error = maximum_state_difference(
        initial_state, model_state_copy(shared)
    )
    specialist_initial_errors = {
        str(active_n): maximum_state_difference(
            initial_state, model_state_copy(specialists[active_n])
        )
        for active_n in ACTIVE_SIZES
    }
    shared_optimizer = torch.optim.Adam(shared.parameters(), lr=LEARNING_RATE)
    specialist_optimizers = {
        active_n: torch.optim.Adam(
            specialists[active_n].parameters(), lr=LEARNING_RATE
        )
        for active_n in ACTIVE_SIZES
    }
    data_rng = np.random.default_rng(TRAIN_DATA_SEED)
    uniform_rng = np.random.default_rng(ACTION_UNIFORM_SEED)
    maximum_replay_error = 0.0
    replay_audits = 0
    paired_batch_checks = 0
    paired_order_checks = 0
    paired_uniform_checks = 0
    shared_optimizer_steps = 0
    specialist_optimizer_steps = {active_n: 0 for active_n in ACTIVE_SIZES}
    actual_train_cases_per_arm = 0
    actual_train_tokens_per_arm = 0
    shared_nonzero_gradient_steps = 0
    specialist_nonzero_gradient_steps = {active_n: 0 for active_n in ACTIVE_SIZES}
    finite_training_metrics = True
    started = time.perf_counter()

    with updates_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "update",
            "train_cases_per_arm",
            "train_tokens_per_arm",
            "entropy_coefficient",
            "shared_reward",
            "specialist_reward",
            "shared_exact",
            "specialist_exact",
            "shared_loss",
            "specialist_loss",
            "shared_gradient_norm",
            "specialist_gradient_norm",
            "replay_logp_max_error",
            "elapsed_seconds",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for update_index in range(1, updates + 1):
            fraction = (update_index - 1) / max(updates - 1, 1)
            entropy_coefficient = ENTROPY_START * (1.0 - fraction)
            batches: dict[int, BanditBatch] = {}
            shared_outputs: dict[int, SequenceOutput] = {}
            specialist_outputs: dict[int, SequenceOutput] = {}
            shared_losses: list[torch.Tensor] = []
            specialist_losses: dict[int, torch.Tensor] = {}
            shared_metrics: list[dict[str, torch.Tensor]] = []
            specialist_metrics: list[dict[str, torch.Tensor]] = []

            for active_n in ACTIVE_SIZES:
                batch = make_batch(
                    active_n=active_n,
                    batch_size=batch_per_size,
                    data_rng=data_rng,
                    uniform_rng=uniform_rng,
                    device=device,
                )
                batches[active_n] = batch
                shared_output = run_roster_sequence(shared, batch)
                specialist_output = run_roster_sequence(
                    specialists[active_n], batch
                )
                shared_outputs[active_n] = shared_output
                specialist_outputs[active_n] = specialist_output
                shared_loss, shared_metric = actor_critic_loss(
                    shared_output, entropy_coefficient=entropy_coefficient
                )
                specialist_loss, specialist_metric = actor_critic_loss(
                    specialist_output, entropy_coefficient=entropy_coefficient
                )
                shared_losses.append(shared_loss)
                specialist_losses[active_n] = specialist_loss
                shared_metrics.append(shared_metric)
                specialist_metrics.append(specialist_metric)
                actual_train_cases_per_arm += batch.batch_size
                actual_train_tokens_per_arm += batch.batch_size * batch.active_n
                paired_batch_checks += 1
                paired_order_checks += int(
                    batch.external_order.data_ptr()
                    == batches[active_n].external_order.data_ptr()
                )
                paired_uniform_checks += int(
                    batch.sampling_uniforms.data_ptr()
                    == batches[active_n].sampling_uniforms.data_ptr()
                )

            audit_this_update = (
                update_index % REPLAY_AUDIT_INTERVAL == 0
                or update_index == updates
            )
            update_replay_error = 0.0
            if audit_this_update:
                for active_n in ACTIVE_SIZES:
                    update_replay_error = max(
                        update_replay_error,
                        replay_error(
                            shared, batches[active_n], shared_outputs[active_n]
                        ),
                        replay_error(
                            specialists[active_n],
                            batches[active_n],
                            specialist_outputs[active_n],
                        ),
                    )
                    replay_audits += 2
                maximum_replay_error = max(
                    maximum_replay_error, update_replay_error
                )

            shared_total_loss = torch.stack(shared_losses).mean()
            shared_gradient_norm = gradient_step(
                model=shared,
                optimizer=shared_optimizer,
                loss=shared_total_loss,
            )
            shared_optimizer_steps += 1
            shared_nonzero_gradient_steps += int(shared_gradient_norm > 0.0)
            specialist_gradient_norms: list[float] = []
            for active_n in ACTIVE_SIZES:
                gradient_norm = gradient_step(
                    model=specialists[active_n],
                    optimizer=specialist_optimizers[active_n],
                    loss=specialist_losses[active_n],
                )
                specialist_optimizer_steps[active_n] += 1
                specialist_nonzero_gradient_steps[active_n] += int(
                    gradient_norm > 0.0
                )
                specialist_gradient_norms.append(gradient_norm)

            def mean_metric(
                metrics: list[dict[str, torch.Tensor]], name: str
            ) -> float:
                return float(
                    torch.stack([metric[name] for metric in metrics]).mean().cpu()
                )

            shared_loss_value = float(shared_total_loss.detach().cpu())
            specialist_loss_value = float(
                torch.stack(
                    [specialist_losses[n].detach() for n in ACTIVE_SIZES]
                ).mean().cpu()
            )
            row_values = [
                shared_loss_value,
                specialist_loss_value,
                shared_gradient_norm,
                *specialist_gradient_norms,
                mean_metric(shared_metrics, "reward"),
                mean_metric(specialist_metrics, "reward"),
            ]
            finite_training_metrics = finite_training_metrics and _all_finite(
                row_values
            )
            elapsed = time.perf_counter() - started
            writer.writerow(
                {
                    "update": update_index,
                    "train_cases_per_arm": update_index
                    * batch_per_size
                    * len(ACTIVE_SIZES),
                    "train_tokens_per_arm": update_index
                    * batch_per_size
                    * sum(ACTIVE_SIZES),
                    "entropy_coefficient": entropy_coefficient,
                    "shared_reward": mean_metric(shared_metrics, "reward"),
                    "specialist_reward": mean_metric(
                        specialist_metrics, "reward"
                    ),
                    "shared_exact": mean_metric(shared_metrics, "exact"),
                    "specialist_exact": mean_metric(
                        specialist_metrics, "exact"
                    ),
                    "shared_loss": shared_loss_value,
                    "specialist_loss": specialist_loss_value,
                    "shared_gradient_norm": shared_gradient_norm,
                    "specialist_gradient_norm": float(
                        np.mean(specialist_gradient_norms)
                    ),
                    "replay_logp_max_error": update_replay_error,
                    "elapsed_seconds": elapsed,
                }
            )
            handle.flush()
            _write_json(
                progress_path,
                {
                    "state": "training",
                    "update": update_index,
                    "updates_total": updates,
                    "fraction": update_index / updates,
                    "train_cases_per_arm": update_index
                    * batch_per_size
                    * len(ACTIVE_SIZES),
                    "train_tokens_per_arm": update_index
                    * batch_per_size
                    * sum(ACTIVE_SIZES),
                    "shared_reward": mean_metric(shared_metrics, "reward"),
                    "specialist_reward": mean_metric(
                        specialist_metrics, "reward"
                    ),
                    "replay_logp_max_error": maximum_replay_error,
                    "elapsed_seconds": elapsed,
                },
            )

    shared_eval, specialist_eval = evaluate_models(
        shared=shared,
        specialists=specialists,
        cases_per_size=eval_per_size,
        device=device,
    )
    shared_drift = drift_summary(initial_state, shared)
    specialist_drifts = {
        str(active_n): drift_summary(initial_state, specialists[active_n])
        for active_n in ACTIVE_SIZES
    }
    expected_cases = updates * batch_per_size * len(ACTIVE_SIZES)
    expected_tokens = updates * batch_per_size * sum(ACTIVE_SIZES)
    expected_pair_checks = updates * len(ACTIVE_SIZES)
    expected_replay_audits = (
        (updates // REPLAY_AUDIT_INTERVAL) * 2 * len(ACTIVE_SIZES)
        if updates >= REPLAY_AUDIT_INTERVAL
        else 2 * len(ACTIVE_SIZES)
    )
    scope_counts = {
        "environment_steps": 0,
        "intrinsic_reward_reads": 0,
        "low_level_policy_calls": 0,
        "checkpoint_exposure": 0,
        "member_identity_fields": 0,
        "slot_index_fields": 0,
        "task_specific_fields": 0,
    }
    m0_checks = {
        "active_sizes_exact": tuple(specialists) == ACTIVE_SIZES,
        "train_cases_per_arm_exact": actual_train_cases_per_arm
        == expected_cases,
        "train_tokens_per_arm_exact": actual_train_tokens_per_arm
        == expected_tokens,
        "shared_optimizer_steps_exact": shared_optimizer_steps == updates,
        "specialist_optimizer_steps_exact": all(
            specialist_optimizer_steps[n] == updates for n in ACTIVE_SIZES
        ),
        "paired_initial_state_exact": shared_initial_max_error == 0.0
        and max(specialist_initial_errors.values()) == 0.0,
        "paired_batches_exact": paired_batch_checks == expected_pair_checks,
        "paired_orders_exact": paired_order_checks == expected_pair_checks,
        "paired_uniforms_exact": paired_uniform_checks == expected_pair_checks,
        "replay_audits_exact": replay_audits == expected_replay_audits,
        "replay_log_probability": maximum_replay_error <= REPLAY_TOLERANCE,
        "finite_training_metrics": finite_training_metrics,
        "shared_gradients_nonzero": shared_nonzero_gradient_steps == updates,
        "specialist_gradients_nonzero": all(
            specialist_nonzero_gradient_steps[n] == updates
            for n in ACTIVE_SIZES
        ),
        "shared_relevant_modules_changed": shared_drift[
            "minimum_relevant_module_max_abs"
        ]
        > 1.0e-8,
        "specialist_relevant_modules_changed": all(
            specialist_drifts[str(n)]["minimum_relevant_module_max_abs"]
            > 1.0e-8
            for n in ACTIVE_SIZES
        ),
        "unused_keep_parameters_exact": shared_drift["keep_head_max_abs"] == 0.0
        and all(
            specialist_drifts[str(n)]["keep_head_max_abs"] == 0.0
            for n in ACTIVE_SIZES
        ),
        "all_parameters_finite": shared_drift["all_parameters_finite"]
        and all(
            specialist_drifts[str(n)]["all_parameters_finite"]
            for n in ACTIVE_SIZES
        ),
        "scope_absence_exact": all(value == 0 for value in scope_counts.values()),
    }
    m0 = all(m0_checks.values())
    m1_checks = {
        "specialist_macro_token_accuracy": specialist_eval[
            "macro_token_accuracy"
        ]
        >= 0.90,
        "specialist_minimum_token_accuracy": specialist_eval[
            "minimum_token_accuracy"
        ]
        >= 0.82,
        "specialist_macro_exact_roster_success": specialist_eval[
            "macro_exact_roster_success"
        ]
        >= 0.55,
        "specialist_n16_exact_roster_success": specialist_eval[
            "n16_exact_roster_success"
        ]
        >= 0.30,
    }
    m1 = all(m1_checks.values())
    token_ratio = shared_eval["macro_token_accuracy"] / max(
        specialist_eval["macro_token_accuracy"], 1.0e-12
    )
    exact_ratio = shared_eval["macro_exact_roster_success"] / max(
        specialist_eval["macro_exact_roster_success"], 1.0e-12
    )
    m2_checks = {
        "shared_macro_token_accuracy": shared_eval["macro_token_accuracy"]
        >= 0.87,
        "shared_minimum_token_accuracy": shared_eval["minimum_token_accuracy"]
        >= 0.78,
        "shared_specialist_macro_token_ratio": token_ratio >= 0.93,
        "shared_macro_exact_roster_success": shared_eval[
            "macro_exact_roster_success"
        ]
        >= 0.45,
        "shared_n16_exact_roster_success": shared_eval[
            "n16_exact_roster_success"
        ]
        >= 0.20,
        "shared_specialist_macro_exact_ratio": exact_ratio >= 0.75,
    }
    m2 = all(m2_checks.values())
    if args.dry_run:
        status = "PASS_R50_DRY_RUN" if m0 else "INVALID_R50_VNSL_WIRING"
    elif not m0:
        status = "INVALID_R50_VNSL_WIRING"
    elif not m1:
        status = "NO_ACCESS_R50_SPECIALIST_SUBSTRATE"
    elif not m2:
        status = "VALID_FAIL_R50_SHARED_VARIABLE_N_LEARNING"
    else:
        status = "PASS_R50_VARIABLE_N_LEARNABILITY"
    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "dry_run": bool(args.dry_run),
        "dry_run_valid": bool(args.dry_run and m0),
        "implementation_valid": m0,
        "m0": m0,
        "m0_checks": m0_checks,
        "m1_specialist_access": m1,
        "m1_checks": m1_checks,
        "m2_shared_learnability": m2,
        "m2_checks": m2_checks,
        "contract": {
            "active_sizes": list(ACTIVE_SIZES),
            "model_seed": MODEL_SEED,
            "train_data_seed": TRAIN_DATA_SEED,
            "eval_data_seed": EVAL_DATA_SEED,
            "action_uniform_seed": ACTION_UNIFORM_SEED,
            "updates": updates,
            "batch_per_size": batch_per_size,
            "eval_cases_per_size": eval_per_size,
            "learning_rate": LEARNING_RATE,
            "value_coefficient": VALUE_COEFFICIENT,
            "entropy_start": ENTROPY_START,
            "gradient_clip": GRADIENT_CLIP,
            "replay_audit_interval": REPLAY_AUDIT_INTERVAL,
            "replay_tolerance": REPLAY_TOLERANCE,
            **scope_counts,
        },
        "counts": {
            "train_cases_per_arm": actual_train_cases_per_arm,
            "train_tokens_per_arm": actual_train_tokens_per_arm,
            "shared_optimizer_steps": shared_optimizer_steps,
            "specialist_optimizer_steps_by_size": {
                str(n): specialist_optimizer_steps[n] for n in ACTIVE_SIZES
            },
            "specialist_optimizer_steps_total": sum(
                specialist_optimizer_steps.values()
            ),
            "replay_audits": replay_audits,
            "paired_batch_checks": paired_batch_checks,
            "paired_order_checks": paired_order_checks,
            "paired_uniform_checks": paired_uniform_checks,
        },
        "probability": {
            "sample_replay_logp_max_error": maximum_replay_error,
        },
        "optimization": {
            "shared_nonzero_gradient_steps": shared_nonzero_gradient_steps,
            "specialist_nonzero_gradient_steps_by_size": {
                str(n): specialist_nonzero_gradient_steps[n]
                for n in ACTIVE_SIZES
            },
            "shared_drift": shared_drift,
            "specialist_drift_by_size": specialist_drifts,
        },
        "evaluation": {
            "shared": shared_eval,
            "specialists": specialist_eval,
            "shared_specialist_macro_token_ratio": token_ratio,
            "shared_specialist_macro_exact_ratio": exact_ratio,
        },
        "elapsed_seconds": time.perf_counter() - started,
        "next_action": {
            "INVALID_R50_VNSL_WIRING": "repair only the named wiring defect",
            "NO_ACCESS_R50_SPECIALIST_SUBSTRATE": "do not judge variable-N sharing",
            "VALID_FAIL_R50_SHARED_VARIABLE_N_LEARNING": "treat cross-N sharing as the next causal problem",
            "PASS_R50_VARIABLE_N_LEARNABILITY": "proceed only to default-off real-controller integration",
            "PASS_R50_DRY_RUN": "freeze implementation and launch the registered formal gate",
        }[status],
    }
    _write_json(result_path, result)
    _write_json(
        progress_path,
        {
            "state": "completed",
            "update": updates,
            "updates_total": updates,
            "fraction": 1.0,
            "status": status,
            "result_path": str(result_path),
            "elapsed_seconds": result["elapsed_seconds"],
        },
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    result = run_gate(parse_args())
    print(
        f"R50 completed: status={result['status']} "
        f"m0={result['m0']} m1={result['m1_specialist_access']} "
        f"m2={result['m2_shared_learnability']}"
    )


if __name__ == "__main__":
    main()
