"""Train and evaluate the frozen finite-resource comparison."""

from __future__ import annotations

import ctypes
import math
import os
import time
from collections import Counter, defaultdict
from typing import Mapping, Sequence

import torch

from . import config as C
from .environment import Episode, EvaluationOpportunity, exact_q, generate_evaluation, generate_training, make_episode
from .models import AssociationFactor, GenericPair
from .rng import cyclic_minibatches, uniform01


def initial_vector(seed: int) -> torch.Tensor:
    values = [
        2.0 * C.INIT_HALF_RANGE * uniform01(seed, C.RNG_NAMESPACES["initialization"], index)
        - C.INIT_HALF_RANGE
        for index in range(C.PARAMETERS)
    ]
    return torch.tensor(values, dtype=torch.float32)


def _peak_rss_bytes() -> int | None:
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return int(counters.PeakWorkingSetSize)
        return None
    try:
        import resource

        value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return value if value > 10_000_000 else value * 1024
    except (ImportError, OSError):
        return None


def _training_tensors(rows: Sequence[Episode]) -> tuple[torch.Tensor, ...]:
    return (
        torch.tensor([row.source for row in rows], dtype=torch.long),
        torch.tensor([row.content for row in rows], dtype=torch.long),
        torch.tensor([row.action for row in rows], dtype=torch.long),
        torch.tensor([row.utility for row in rows], dtype=torch.float32),
    )


def _summary_vector(vector: torch.Tensor) -> dict[str, object]:
    values = vector.detach().cpu().to(dtype=torch.float32)
    return {
        "values": [float(value) for value in values.tolist()],
        "count": int(values.numel()),
        "byte_count": int(values.numel() * values.element_size()),
        "min": float(values.min().item()),
        "max": float(values.max().item()),
        "l2": float(torch.linalg.vector_norm(values).item()),
    }


def _optimizer_bytes(optimizer: torch.optim.Optimizer) -> int:
    return sum(
        value.numel() * value.element_size()
        for state in optimizer.state.values()
        for value in state.values()
        if isinstance(value, torch.Tensor)
    )


def _check_deadlines(
    invocation_deadline: float,
    *,
    arm_deadline: float | None = None,
    phase: str,
) -> None:
    now = time.perf_counter()
    if now >= invocation_deadline:
        raise TimeoutError(f"invocation wall cap crossed during {phase}")
    if arm_deadline is not None and now >= arm_deadline:
        raise TimeoutError(f"learned-arm wall cap crossed during {phase}")


def _train_arm(
    model: GenericPair | AssociationFactor,
    tensors: tuple[torch.Tensor, ...],
    minibatches: Sequence[Sequence[int]],
    *,
    invocation_deadline: float,
    arm_deadline: float,
) -> dict[str, object]:
    started = time.perf_counter()
    _check_deadlines(
        invocation_deadline,
        arm_deadline=arm_deadline,
        phase=f"{model.name} training start",
    )
    source, content, action, target = tensors
    initial = model.theta.detach().clone()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=C.LEARNING_RATE,
        betas=C.ADAM_BETAS,
        eps=C.ADAM_EPS,
        weight_decay=0.0,
    )
    _check_deadlines(
        invocation_deadline,
        arm_deadline=arm_deadline,
        phase=f"{model.name} optimizer setup",
    )
    losses: list[float] = []
    for update, indices in enumerate(minibatches):
        _check_deadlines(
            invocation_deadline,
            arm_deadline=arm_deadline,
            phase=f"{model.name} update {update}",
        )
        batch = torch.tensor(indices, dtype=torch.long)
        optimizer.zero_grad(set_to_none=True)
        prediction = model(source[batch], content[batch], action[batch])
        loss = torch.mean((prediction - target[batch]) ** 2)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().item()))
        _check_deadlines(
            invocation_deadline,
            arm_deadline=arm_deadline,
            phase=f"{model.name} update {update} completion",
        )
    final = model.theta.detach().clone()
    displacement = final - initial
    changed = int(torch.count_nonzero(displacement).item())
    peak_rss = _peak_rss_bytes()
    _check_deadlines(
        invocation_deadline,
        arm_deadline=arm_deadline,
        phase=f"{model.name} training finalization",
    )
    training_wall = time.perf_counter() - started
    return {
        "model": model,
        "initial": initial,
        "final": final,
        "first_loss": losses[0],
        "last_loss": losses[-1],
        "loss_curve": losses,
        "training_wall_seconds": training_wall,
        "training_wall_seconds_per_update": training_wall / len(minibatches),
        "peak_rss_bytes_after_training": peak_rss,
        "linf_displacement": float(torch.max(torch.abs(displacement)).item()),
        "linf_displacement_over_init_half_range": float(
            torch.max(torch.abs(displacement)).item() / C.INIT_HALF_RANGE
        ),
        "l2_displacement": float(torch.linalg.vector_norm(displacement).item()),
        "changed_coordinate_count": changed,
        "optimizer_state_bytes": _optimizer_bytes(optimizer),
        "nonfinite_loss_count": sum(not math.isfinite(value) for value in losses),
        "nonfinite_final_parameter_count": int(
            torch.count_nonzero(~torch.isfinite(final)).item()
        ),
    }


def _cell_q(
    model: GenericPair | AssociationFactor | None,
    *,
    invocation_deadline: float,
    arm_deadline: float | None = None,
) -> dict[tuple[int, int, int], float]:
    cells: dict[tuple[int, int, int], float] = {}
    with torch.no_grad():
        for source in C.SOURCES:
            for content in C.CONTENTS:
                for action in C.ACTIONS:
                    _check_deadlines(
                        invocation_deadline,
                        arm_deadline=arm_deadline,
                        phase="action-time cell evaluation",
                    )
                    if model is None:
                        value = exact_q(source, content, action)
                    else:
                        value = float(
                            model(
                                torch.tensor([source]),
                                torch.tensor([content]),
                                torch.tensor([action]),
                            ).item()
                        )
                    cells[(source, content, action)] = value
    return cells


def _softmax_probabilities(q_minus: float, q_plus: float) -> tuple[float, float]:
    high = max(q_minus, q_plus)
    minus = math.exp(q_minus - high)
    plus = math.exp(q_plus - high)
    total = minus + plus
    return minus / total, plus / total


def greedy_action(q_minus: float, q_plus: float) -> int:
    return -1 if q_minus >= q_plus else 1


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _evaluate(
    q: Mapping[tuple[int, int, int], float],
    opportunities: Sequence[EvaluationOpportunity],
    *,
    invocation_deadline: float,
    arm_deadline: float | None = None,
) -> dict[str, object]:
    exact_values: list[float] = []
    predictions: list[float] = []
    context_probabilities: dict[tuple[int, int], float] = {}
    gradients: list[float] = []
    exact_gradients: list[float] = []
    competence = 0
    enumerated_utility: list[float] = []
    per_context_enumerated: dict[tuple[int, int], list[float]] = defaultdict(list)
    for source in C.SOURCES:
        for content in C.CONTENTS:
            _check_deadlines(
                invocation_deadline,
                arm_deadline=arm_deadline,
                phase="enumerated policy evaluation",
            )
            q_minus = q[(source, content, -1)]
            q_plus = q[(source, content, 1)]
            p_minus, p_plus = _softmax_probabilities(q_minus, q_plus)
            p_correct = p_plus if content == 1 else p_minus
            context_probabilities[(source, content)] = p_correct
            competence += int(greedy_action(q_minus, q_plus) == content)
            gradients.append(0.25 * (q_plus - q_minus))
            exact_gradients.append(
                0.25 * (exact_q(source, content, 1) - exact_q(source, content, -1))
            )
            for action, probability in ((-1, p_minus), (1, p_plus)):
                prediction = q[(source, content, action)]
                target = exact_q(source, content, action)
                predictions.append(prediction)
                exact_values.append(target)
                for mode in C.MODES:
                    contribution = probability * make_episode(source, content, action, mode).utility
                    enumerated_utility.append(contribution / len(C.MODES))
                    per_context_enumerated[(source, content)].append(contribution / len(C.MODES))
    errors = [prediction - target for prediction, target in zip(predictions, exact_values)]
    gradient_errors = [value - target for value, target in zip(gradients, exact_gradients)]
    gradient_error_l2 = math.sqrt(sum(value * value for value in gradient_errors))
    gradient_norm = math.sqrt(sum(value * value for value in gradients))
    exact_gradient_norm = math.sqrt(sum(value * value for value in exact_gradients))
    cosine = sum(a * b for a, b in zip(gradients, exact_gradients)) / (
        gradient_norm * exact_gradient_norm
    ) if gradient_norm > 0.0 else 0.0

    sampled: list[float] = []
    sampled_actions: list[int] = []
    per_context_sampled: dict[tuple[int, int], list[float]] = defaultdict(list)
    for opportunity in opportunities:
        _check_deadlines(
            invocation_deadline,
            arm_deadline=arm_deadline,
            phase="paired policy evaluation",
        )
        q_minus = q[(opportunity.source, opportunity.content, -1)]
        q_plus = q[(opportunity.source, opportunity.content, 1)]
        p_minus, _ = _softmax_probabilities(q_minus, q_plus)
        action = -1 if opportunity.action_uniform < p_minus else 1
        sampled_actions.append(action)
        utility = float(
            make_episode(opportunity.source, opportunity.content, action, opportunity.mode).utility
        )
        sampled.append(utility)
        per_context_sampled[(opportunity.source, opportunity.content)].append(utility)

    per_context = {}
    for source in C.SOURCES:
        for content in C.CONTENTS:
            key = (source, content)
            samples = per_context_sampled[key]
            per_context[f"s={source},c={content:+d}"] = {
                "probability_allocated_to_matching_relation": context_probabilities[key],
                "exact_expected_bounded_utility": sum(per_context_enumerated[key]),
                "paired_sampled_bounded_utility": _mean(samples) if samples else None,
                "paired_evaluation_episodes": len(samples),
            }
    source_counts = Counter(row.source for row in opportunities)
    content_counts = Counter(row.content for row in opportunities)
    action_counts = Counter(sampled_actions)
    mode_counts = Counter(row.mode for row in opportunities)
    _check_deadlines(
        invocation_deadline,
        arm_deadline=arm_deadline,
        phase="policy evaluation finalization",
    )
    return {
        "q_values": [
            {"source": s, "content": c, "action": a, "prediction": q[(s, c, a)], "exact_q": exact_q(s, c, a)}
            for s in C.SOURCES for c in C.CONTENTS for a in C.ACTIONS
        ],
        "prediction_range": [min(predictions), max(predictions)],
        "exact_q_range": [min(exact_values), max(exact_values)],
        "rmse_q": math.sqrt(_mean([value * value for value in errors])),
        "max_abs_q_error": max(abs(value) for value in errors),
        "c_q": competence,
        "tie_rule": C.TIE_RULE,
        "source_gradient_order": [f"s={s},c={c:+d}" for s in C.SOURCES for c in C.CONTENTS],
        "source_gradient": gradients,
        "exact_source_gradient": exact_gradients,
        "source_gradient_l2_error": gradient_error_l2,
        "source_gradient_cosine_to_exact": cosine,
        "mean_probability_allocated_to_matching_relation": _mean(list(context_probabilities.values())),
        "exact_expected_bounded_utility": sum(enumerated_utility) / (len(C.SOURCES) * len(C.CONTENTS)),
        "paired_sampled_bounded_utility": _mean(sampled),
        "paired_counts": {
            "source": {str(key): source_counts[key] for key in C.SOURCES},
            "content": {f"{key:+d}": content_counts[key] for key in C.CONTENTS},
            "action": {f"{key:+d}": action_counts[key] for key in C.ACTIONS},
            "mode": {key: mode_counts[key] for key in C.MODES},
        },
        "per_source_content": per_context,
        "evaluation_episodes": len(opportunities),
        "evaluation_environment_transitions": len(opportunities) * C.TRANSITIONS_PER_EPISODE,
        "exact_evaluation_cells": C.EXACT_EVALUATION_CELLS,
        "evaluator_calls": {"paired": len(opportunities), "enumerated": C.EXACT_EVALUATION_CELLS},
        "nonfinite_prediction_count": sum(not math.isfinite(value) for value in predictions),
    }


def classify_branch(
    generic: Mapping[str, float | int],
    factor: Mapping[str, float | int],
    complete_and_valid: bool = True,
) -> str:
    if not complete_and_valid:
        return "FRCS-INVALID-INCOMPLETE"
    if int(generic["c_q"]) < 8:
        return "FRCS-E-GENERIC-UNDEREXPOSED"
    delta_q = float(generic["rmse_q"]) - float(factor["rmse_q"])
    delta_g = float(generic["source_gradient_l2_error"]) - float(
        factor["source_gradient_l2_error"]
    )
    delta_u = float(factor["exact_expected_bounded_utility"]) - float(
        generic["exact_expected_bounded_utility"]
    )
    if delta_q > 0.0 and delta_g > 0.0 and delta_u > 0.0:
        return "FRCS-A-FACTORIZED-ENDPOINT-GAIN"
    if delta_q > 0.0 and delta_g > 0.0 and delta_u <= 0.0:
        return "FRCS-B-ESTIMATION-ONLY"
    if (
        float(generic["rmse_q"]) <= float(factor["rmse_q"])
        and float(generic["source_gradient_l2_error"])
        <= float(factor["source_gradient_l2_error"])
        and float(generic["exact_expected_bounded_utility"])
        >= float(factor["exact_expected_bounded_utility"])
    ):
        return "FRCS-C-GENERIC-MATCHES-OR-BEATS"
    return "FRCS-D-MIXED"


def _counts(rows: Sequence[Episode]) -> dict[str, dict[str, int]]:
    source_counts = Counter(row.source for row in rows)
    content_counts = Counter(row.content for row in rows)
    action_counts = Counter(row.action for row in rows)
    mode_counts = Counter(row.mode for row in rows)
    return {
        "source": {str(key): source_counts[key] for key in C.SOURCES},
        "content": {f"{key:+d}": content_counts[key] for key in C.CONTENTS},
        "action": {f"{key:+d}": action_counts[key] for key in C.ACTIONS},
        "mode": {key: mode_counts[key] for key in C.MODES},
    }


def _execute_experiment(
    seed: int,
    *,
    train_episodes: int = C.TRAIN_EPISODES,
    updates: int = C.UPDATES,
    batch_size: int = C.BATCH_SIZE,
    evaluation_episodes: int = C.EVALUATION_EPISODES,
    argv: Sequence[str] = (),
    launch_sha: str = "UNKNOWN",
    profile: str = "scientific",
    admission_receipt: Mapping[str, object] | None = None,
    timing: dict[str, object],
) -> dict[str, object]:
    torch.set_num_threads(1)
    started = float(timing["invocation_started"])
    invocation_deadline = started + C.INVOCATION_WALL_CAP_SECONDS
    rows = generate_training(seed, train_episodes)
    _check_deadlines(invocation_deadline, phase="training trajectory setup")
    opportunities = generate_evaluation(seed, evaluation_episodes)
    _check_deadlines(invocation_deadline, phase="evaluation opportunity setup")
    batches = cyclic_minibatches(
        seed,
        C.RNG_NAMESPACES["minibatch_permutation"],
        len(rows),
        updates,
        batch_size,
    )
    _check_deadlines(invocation_deadline, phase="minibatch setup")
    tensors = _training_tensors(rows)
    initial = initial_vector(seed)
    models = (GenericPair(initial), AssociationFactor(initial))
    _check_deadlines(invocation_deadline, phase="model setup")
    shared_setup_wall = time.perf_counter() - started
    timing["shared_setup_wall_seconds"] = shared_setup_wall
    if shared_setup_wall >= C.ARM_WALL_CAP_SECONDS:
        raise TimeoutError("shared setup exhausted the learned-arm wall cap")
    initial_bytes_equal = models[0].theta.detach().numpy().tobytes() == models[1].theta.detach().numpy().tobytes()

    learned: dict[str, dict[str, object]] = {}
    timing["per_learned_arm"] = {}
    for model in models:
        name = model.name
        arm_started = time.perf_counter()
        arm_deadline = arm_started + (C.ARM_WALL_CAP_SECONDS - shared_setup_wall)
        record = _train_arm(
            model,
            tensors,
            batches,
            invocation_deadline=invocation_deadline,
            arm_deadline=arm_deadline,
        )
        record.pop("model")
        evaluation_started = time.perf_counter()
        q = _cell_q(
            model,
            invocation_deadline=invocation_deadline,
            arm_deadline=arm_deadline,
        )
        evaluation = _evaluate(
            q,
            opportunities,
            invocation_deadline=invocation_deadline,
            arm_deadline=arm_deadline,
        )
        evaluation_wall = time.perf_counter() - evaluation_started
        arm_work_wall = time.perf_counter() - arm_started
        complete_arm_wall = shared_setup_wall + arm_work_wall
        timing["per_learned_arm"][name] = {
            "training_wall_seconds": record["training_wall_seconds"],
            "evaluation_wall_seconds": evaluation_wall,
            "arm_work_wall_seconds": arm_work_wall,
            "complete_wall_seconds_including_shared_setup": complete_arm_wall,
            "wall_cap_seconds": C.ARM_WALL_CAP_SECONDS,
            "within_cap": complete_arm_wall < C.ARM_WALL_CAP_SECONDS,
        }
        if complete_arm_wall >= C.ARM_WALL_CAP_SECONDS:
            raise TimeoutError(f"{name} complete learned-arm wall cap crossed")
        forward_rows = updates * batch_size + C.ACTION_TIME_MODEL_CELLS
        arithmetic = dict(model.arithmetic_per_row)
        learned[name] = {
            "role": "strongest_comparator" if name == "GENERIC_PAIR" else "treatment",
            "equation": (
                "0.5*(T1[s,c,a]+T2[s,c,a])"
                if name == "GENERIC_PAIR"
                else "0.5*(U1[s,a]*V1[c,a]+U2[s,a]*V2[c,a])+B[s]+D[c]+E[a]"
            ),
            "layout": list(model.layout),
            "trainable_parameters": int(model.theta.numel()),
            "parameter_bytes": int(model.theta.numel() * model.theta.element_size()),
            "adam_state_bytes_expected": C.ADAM_STATE_BYTES,
            "arithmetic_per_row": arithmetic,
            "analytical_forward_work": {
                "row_count_basis": {
                    "training_example_exposures": updates * batch_size,
                    "action_time_model_cells": C.ACTION_TIME_MODEL_CELLS,
                    "total_forward_rows": forward_rows,
                },
                "total_multiplies": forward_rows * int(arithmetic["multiplies"]),
                "total_adds": forward_rows * int(arithmetic["adds"]),
                "backward_arithmetic_claimed": False,
                "scope": "critic forward evaluations only; optimizer and backward arithmetic excluded",
            },
            "initial_parameters": _summary_vector(record.pop("initial")),
            "final_parameters": _summary_vector(record.pop("final")),
            "training": {
                **record,
                "updates": updates,
                "minibatch_size": batch_size,
                "example_exposures": updates * batch_size,
                "training_episodes": train_episodes,
                "training_environment_transitions": train_episodes * C.TRANSITIONS_PER_EPISODE,
            },
            "complete_arm_wall": dict(timing["per_learned_arm"][name]),
            "evaluation": evaluation,
        }

    reference_started = time.perf_counter()
    reference = _evaluate(
        _cell_q(None, invocation_deadline=invocation_deadline),
        opportunities,
        invocation_deadline=invocation_deadline,
    )
    timing["reference_evaluation_wall_seconds"] = time.perf_counter() - reference_started
    _check_deadlines(invocation_deadline, phase="reference evaluation completion")
    generic_eval = learned["GENERIC_PAIR"]["evaluation"]
    factor_eval = learned["ASSOCIATION_FACTOR"]["evaluation"]
    deltas = {
        "delta_q": generic_eval["rmse_q"] - factor_eval["rmse_q"],
        "delta_g": generic_eval["source_gradient_l2_error"] - factor_eval["source_gradient_l2_error"],
        "delta_u": factor_eval["exact_expected_bounded_utility"] - generic_eval["exact_expected_bounded_utility"],
    }
    finite = all(
        int(learned[name]["evaluation"]["nonfinite_prediction_count"]) == 0
        and int(learned[name]["training"]["nonfinite_loss_count"]) == 0
        and int(learned[name]["training"]["nonfinite_final_parameter_count"]) == 0
        for name in C.ARM_ORDER
    )
    moved = all(
        int(learned[name]["training"]["changed_coordinate_count"]) > 0
        for name in C.ARM_ORDER
    )
    peak_rss = _peak_rss_bytes()
    _check_deadlines(invocation_deadline, phase="final result-rule boundary")
    measured_wall = time.perf_counter() - started
    if measured_wall >= C.INVOCATION_WALL_CAP_SECONDS:
        raise TimeoutError("invocation wall cap crossed at final result-rule boundary")
    timing["invocation_wall_seconds"] = measured_wall
    wall_cap_status = {
        "per_learned_arm": {
            name: bool(timing["per_learned_arm"][name]["within_cap"])
            for name in C.ARM_ORDER
        },
        "sequential_invocation": measured_wall < C.INVOCATION_WALL_CAP_SECONDS,
    }
    wall_caps_respected = all(wall_cap_status["per_learned_arm"].values()) and bool(
        wall_cap_status["sequential_invocation"]
    )
    scientific_contract_exact = (
        seed == C.SCIENTIFIC_SEED
        and train_episodes == C.TRAIN_EPISODES
        and updates == C.UPDATES
        and batch_size == C.BATCH_SIZE
        and evaluation_episodes == C.EVALUATION_EPISODES
    )
    shared_contract = (
        initial_bytes_equal
        and finite
        and moved
        and bool(rows)
        and bool(opportunities)
        and bool(batches)
        and wall_caps_respected
        and scientific_contract_exact
    )
    result_rule_applied = profile == "scientific"
    branch = classify_branch(generic_eval, factor_eval, shared_contract) if result_rule_applied else None
    return {
        "object_id": C.OBJECT_ID,
        "evidence_class": "B_EXPLORE",
        "profile": profile,
        "seed": seed,
        "launch_sha": launch_sha,
        "argv": list(argv),
        "external_resource_admission": dict(admission_receipt or {}),
        "branch": branch,
        "result_rule_applied": result_rule_applied,
        "technical_outcome": (
            None if result_rule_applied else "NON_SCIENTIFIC_TOY_SMOKE_COMPLETE"
        ),
        "claim_ceiling": (
            "one-seed preliminary fixed-host finite-data critic-estimation evidence"
            if result_rule_applied
            else None
        ),
        "configuration": {
            "agents": 4,
            "topology": "directed_ring",
            "transitions_per_episode": C.TRANSITIONS_PER_EPISODE,
            "sources": list(C.SOURCES),
            "contents": list(C.CONTENTS),
            "actions": list(C.ACTIONS),
            "modes": list(C.MODES),
            "utility": "1{mode != EXPIRE} * 1{action == content}",
            "exact_q": "2/3 iff action == content, else 0",
            "action_time_observation": [
                "source_identity",
                "clockwise_and_counterclockwise_waiter_identities",
                "public_ordered_edge_keys",
                "content_sign",
                "readiness",
                "remaining_token",
            ],
            "selected_waiter": "(source + action) mod 4",
            "replacement_carrier": "(source + 2) mod 4; provenance relation remains action",
            "dtype": "float32",
            "adam": {"lr": C.LEARNING_RATE, "betas": list(C.ADAM_BETAS), "eps": C.ADAM_EPS, "weight_decay": 0.0},
            "arm_order": list(C.ARM_ORDER),
            "tie_rule": C.TIE_RULE,
            "softmax_temperature": 1.0,
        },
        "initialization": {
            "same_flat_32_scalar_initialization_bytes": initial_bytes_equal,
            "flat_byte_count_per_arm": C.PARAMETERS * C.FP32_BYTES,
            "generic_layout": list(C.GENERIC_LAYOUT),
            "factor_layout": list(C.FACTOR_LAYOUT),
            "distinct_mapping_and_reshape": C.GENERIC_LAYOUT != C.FACTOR_LAYOUT,
            "tensor_shape_identity_claimed": False,
        },
        "shared_work": {
            "counter_addressed_rng": "splitmix64 coordinate map",
            "namespaces": dict(C.RNG_NAMESPACES),
            "identical_lossless_action_time_cell_encoding": "(source s, content c, relation a)",
            "waiter_ids_and_ordered_edge_keys": "deterministic lossless functions of (s,a)",
            "readiness_and_remaining_token": "constant and identical in both arms",
            "all_named_action_time_observation_fields_shared": True,
            "treatment_only_observation_field_present": False,
            "same_training_rows_and_terminal_targets": True,
            "same_cyclic_permutation_and_minibatch_indices": True,
            "same_evaluation_opportunities": True,
            "same_zero_initialized_adam_moments_and_step": True,
            "same_actual_adam_state_bytes": (
                learned["GENERIC_PAIR"]["training"]["optimizer_state_bytes"]
                == learned["ASSOCIATION_FACTOR"]["training"]["optimizer_state_bytes"]
            ),
            "factor_auxiliary_labels_or_losses": False,
        },
        "training_population_counts": _counts(rows),
        "counts": {
            "training_episodes": len(rows),
            "training_environment_transitions": len(rows) * C.TRANSITIONS_PER_EPISODE,
            "optimizer_updates_per_learned_arm": updates,
            "minibatch_size": batch_size,
            "optimizer_example_exposures_per_learned_arm": updates * batch_size,
            "evaluation_episodes_per_arm_or_reference": len(opportunities),
            "evaluation_environment_transitions_per_arm_or_reference": len(opportunities) * C.TRANSITIONS_PER_EPISODE,
            "exact_evaluation_cells_per_arm_or_reference": C.EXACT_EVALUATION_CELLS,
            "learned_arms": 2,
            "reference_arms": 1,
            "total_optimizer_updates": 2 * updates,
            "total_optimizer_example_exposures": 2 * updates * batch_size,
            "total_evaluation_environment_transitions": (
                3 * len(opportunities) * C.TRANSITIONS_PER_EPISODE
            ),
        },
        "target_range": [float(tensors[3].min().item()), float(tensors[3].max().item())],
        "learned_arms": learned,
        "exact_q_reference": {
            "role": "calibrated_exact_q_reference",
            "native_optimal_ceiling": False,
            "empirical_arm": False,
            "learned_arm_win_eligible": False,
            "softmax_temperature": 1.0,
            "evaluation": reference,
        },
        "primary_differences": deltas,
        "cost_projection": C.project_cost_payload()["cost_law"],
        "exposure_line": C.EXPOSURE_LINE,
        "resource_telemetry": {
            "wall_seconds": measured_wall,
            "peak_rss_bytes": peak_rss,
            "status": "measured" if peak_rss is not None else "resources_unmeasured",
            "shared_setup_wall_seconds": shared_setup_wall,
            "per_learned_arm": dict(timing["per_learned_arm"]),
            "reference_evaluation_wall_seconds": timing["reference_evaluation_wall_seconds"],
            "invocation_wall_seconds": measured_wall,
            "invocation_wall_cap_seconds": C.INVOCATION_WALL_CAP_SECONDS,
            "invocation_within_cap": measured_wall < C.INVOCATION_WALL_CAP_SECONDS,
            "wall_cap_status": wall_cap_status,
        },
        "integrity": {
            "complete_and_valid": shared_contract if result_rule_applied else False,
            "technical_execution_complete": True,
            "scientific_contract_exact": scientific_contract_exact,
            "scientific_integrity_applicable": result_rule_applied,
            "nonfinite_prediction_counts": {
                name: learned[name]["evaluation"]["nonfinite_prediction_count"] for name in C.ARM_ORDER
            },
            "nonfinite_loss_counts": {
                name: learned[name]["training"]["nonfinite_loss_count"] for name in C.ARM_ORDER
            },
            "nonfinite_final_parameter_counts": {
                name: learned[name]["training"]["nonfinite_final_parameter_count"]
                for name in C.ARM_ORDER
            },
            "nonfinite_target_count": int(torch.count_nonzero(~torch.isfinite(tensors[3])).item()),
            "both_parameter_vectors_moved": moved,
            "required_counts_nonzero": bool(rows) and bool(opportunities) and bool(batches),
            "wall_caps_respected": wall_caps_respected,
        },
    }


def _rejected_scientific_request(
    seed: int,
    train_episodes: int,
    updates: int,
    batch_size: int,
    evaluation_episodes: int,
    argv: Sequence[str],
    launch_sha: str,
    admission_receipt: Mapping[str, object] | None,
) -> dict[str, object]:
    return {
        "object_id": C.OBJECT_ID,
        "evidence_class": "B_EXPLORE",
        "profile": "scientific",
        "seed": seed,
        "launch_sha": launch_sha,
        "argv": list(argv),
        "external_resource_admission": dict(admission_receipt or {}),
        "branch": None,
        "result_rule_applied": False,
        "technical_outcome": "NON_FROZEN_SCIENTIFIC_REQUEST_REJECTED",
        "claim_ceiling": None,
        "requested_counts": {
            "training_episodes": train_episodes,
            "optimizer_updates": updates,
            "minibatch_size": batch_size,
            "evaluation_episodes": evaluation_episodes,
        },
        "frozen_contract": {
            "seed": C.SCIENTIFIC_SEED,
            "training_episodes": C.TRAIN_EPISODES,
            "optimizer_updates": C.UPDATES,
            "minibatch_size": C.BATCH_SIZE,
            "evaluation_episodes": C.EVALUATION_EPISODES,
        },
        "integrity": {
            "complete_and_valid": False,
            "technical_execution_complete": False,
            "scientific_contract_exact": False,
            "scientific_integrity_applicable": False,
            "trajectories_models_optimizers_created": False,
        },
    }


def _cap_stop_summary(
    seed: int,
    profile: str,
    argv: Sequence[str],
    launch_sha: str,
    admission_receipt: Mapping[str, object] | None,
    timing: Mapping[str, object],
    error: TimeoutError,
) -> dict[str, object]:
    invocation_wall = time.perf_counter() - float(timing["invocation_started"])
    return {
        "object_id": C.OBJECT_ID,
        "evidence_class": "B_EXPLORE",
        "profile": profile,
        "seed": seed,
        "launch_sha": launch_sha,
        "argv": list(argv),
        "external_resource_admission": dict(admission_receipt or {}),
        "branch": None,
        "result_rule_applied": False,
        "technical_outcome": "INCOMPLETE_TECHNICAL_CAP_STOP",
        "claim_ceiling": None,
        "error": {"type": "TimeoutError", "message": str(error)},
        "resource_telemetry": {
            "wall_seconds": invocation_wall,
            "peak_rss_bytes": _peak_rss_bytes(),
            "shared_setup_wall_seconds": timing.get("shared_setup_wall_seconds"),
            "per_learned_arm": dict(timing.get("per_learned_arm", {})),
            "reference_evaluation_wall_seconds": timing.get(
                "reference_evaluation_wall_seconds"
            ),
            "invocation_wall_seconds": invocation_wall,
            "invocation_wall_cap_seconds": C.INVOCATION_WALL_CAP_SECONDS,
            "invocation_within_cap": invocation_wall < C.INVOCATION_WALL_CAP_SECONDS,
        },
        "integrity": {
            "complete_and_valid": False,
            "technical_execution_complete": False,
            "scientific_contract_exact": profile == "scientific",
            "scientific_integrity_applicable": profile == "scientific",
        },
    }


def run_experiment(
    seed: int,
    *,
    train_episodes: int = C.TRAIN_EPISODES,
    updates: int = C.UPDATES,
    batch_size: int = C.BATCH_SIZE,
    evaluation_episodes: int = C.EVALUATION_EPISODES,
    argv: Sequence[str] = (),
    launch_sha: str = "UNKNOWN",
    profile: str = "scientific",
    admission_receipt: Mapping[str, object] | None = None,
) -> dict[str, object]:
    scientific_contract_exact = (
        seed == C.SCIENTIFIC_SEED
        and train_episodes == C.TRAIN_EPISODES
        and updates == C.UPDATES
        and batch_size == C.BATCH_SIZE
        and evaluation_episodes == C.EVALUATION_EPISODES
    )
    if profile == "scientific" and not scientific_contract_exact:
        return _rejected_scientific_request(
            seed,
            train_episodes,
            updates,
            batch_size,
            evaluation_episodes,
            argv,
            launch_sha,
            admission_receipt,
        )

    timing: dict[str, object] = {"invocation_started": time.perf_counter()}
    try:
        return _execute_experiment(
            seed,
            train_episodes=train_episodes,
            updates=updates,
            batch_size=batch_size,
            evaluation_episodes=evaluation_episodes,
            argv=argv,
            launch_sha=launch_sha,
            profile=profile,
            admission_receipt=admission_receipt,
            timing=timing,
        )
    except TimeoutError as error:
        return _cap_stop_summary(
            seed,
            profile,
            argv,
            launch_sha,
            admission_receipt,
            timing,
            error,
        )
