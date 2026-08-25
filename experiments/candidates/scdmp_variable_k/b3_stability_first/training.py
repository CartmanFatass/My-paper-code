from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence

import numpy as np
import torch
from torch import Tensor

from ..corpus import BankRow
from .config import (
    ADAM, ARMS, CALIBRATION_DOSE, CALIBRATION_MIN_RATIO, OPTIMIZER_UPDATES,
    ORDERED_PARAMETER_NAMES, QUARTERS,
)
from .corpus import Corpus, LockedBatchPlan, support_certificate
from .lifecycle import Lifecycle
from .model import SCDMPModel
from .relations import arrays, auxiliary_loss, endpoint_loss, model_call_batch

ResourceCheck = Callable[[], None]


def ordered_parameters(model: SCDMPModel) -> tuple[Tensor, ...]:
    mapping = dict(model.named_parameters())
    if tuple(mapping) != ORDERED_PARAMETER_NAMES:
        raise RuntimeError(f"parameter traversal mismatch: {tuple(mapping)}")
    result = tuple(mapping[name] for name in ORDERED_PARAMETER_NAMES)
    if len({id(p) for p in result}) != 24 or any(not p.requires_grad for p in result):
        raise RuntimeError("ordered B3 parameter tuple is incomplete, duplicated, or frozen")
    return result


def gradient_norm(grads: Sequence[Tensor]) -> Tensor:
    total: Tensor | None = None
    for grad in grads:
        if grad is None or not bool(torch.isfinite(grad).all()):
            raise RuntimeError("missing or nonfinite gradient component")
        flat = grad.detach().to(dtype=torch.float64).contiguous().view(-1)
        part = torch.sum(flat * flat, dtype=torch.float64)
        total = part if total is None else total + part
    if total is None:
        raise RuntimeError("empty gradient tuple")
    return torch.sqrt(total)


def gradient_dot(left: Sequence[Tensor], right: Sequence[Tensor]) -> Tensor:
    total: Tensor | None = None
    for first, second in zip(left, right):
        if first is None or second is None or not bool(torch.isfinite(first).all()) \
                or not bool(torch.isfinite(second).all()):
            raise RuntimeError("missing or nonfinite gradient component")
        part = torch.sum(first.detach().to(torch.float64).contiguous().view(-1)
                         * second.detach().to(torch.float64).contiguous().view(-1),
                         dtype=torch.float64)
        total = part if total is None else total + part
    if total is None:
        raise RuntimeError("empty gradient tuple")
    return total


def model_state_digest(model: SCDMPModel) -> str:
    digest = hashlib.sha256()
    for name, tensor in model.state_dict().items():
        digest.update(name.encode("utf-8"))
        array = tensor.detach().cpu().contiguous().numpy()
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def optimizer_for(model: SCDMPModel) -> torch.optim.Adam:
    return torch.optim.Adam(model.parameters(), lr=ADAM["lr"], betas=ADAM["betas"],
                            eps=ADAM["eps"], weight_decay=ADAM["weight_decay"])


def diagnostic_values(endpoint_norm: float, auxiliary_norm: float,
                      calibrated_auxiliary: float, coefficient: float,
                      dot: float | None = None) -> dict[str, float | None]:
    """Pure B3 diagnostic reduction; finite zero auxiliary norm is valid."""
    values = np.asarray((endpoint_norm, auxiliary_norm, calibrated_auxiliary, coefficient),
                        dtype=np.float64)
    if not np.all(np.isfinite(values)) or endpoint_norm < 0.0 or auxiliary_norm < 0.0 \
            or calibrated_auxiliary <= 0.0:
        raise RuntimeError("invalid B3 diagnostic input")
    delivered = float(np.float64(coefficient) * np.float64(auxiliary_norm))
    persistence = float(np.float64(auxiliary_norm) / np.float64(calibrated_auxiliary))
    ratio = float(np.float64(delivered) / max(np.float64(endpoint_norm), np.float64(1.0e-12)))
    cosine = None
    if endpoint_norm > 0.0 and auxiliary_norm > 0.0:
        if dot is None or not np.isfinite(dot):
            raise RuntimeError("positive-norm cosine requires a finite dot product")
        cosine = float(np.float64(dot) /
                       (np.float64(endpoint_norm) * np.float64(auxiliary_norm)))
    return {"D": delivered, "P": persistence, "R": ratio,
            "endpoint_auxiliary_cosine": cosine}


def calibrate_seed(corpus: Corpus, algorithm_seed: int, lifecycle: Lifecycle,
                   resource_check: ResourceCheck | None = None) -> list[dict[str, object]]:
    plan = LockedBatchPlan(corpus, algorithm_seed)
    locked_zero = plan.batch_for_update(0)
    support = support_certificate(corpus, locked_zero)
    if not support["conforming"]:
        raise RuntimeError(f"seed={algorithm_seed} locked update-zero support failed before activity")
    canonical = SCDMPModel(algorithm_seed)
    initial_digest = model_state_digest(canonical)
    if resource_check is not None:
        resource_check()
    b_value: float | None = None
    target: float | None = None
    endpoint_error: str | None = None
    try:
        endpoint_graph = endpoint_loss(canonical, locked_zero, corpus.scales)
        endpoint_parameters = ordered_parameters(canonical)
        if algorithm_seed == 200 and not lifecycle.scientific_activity_started:
            lifecycle.begin_seed_200_calibration()
        elif not lifecycle.scientific_activity_started:
            raise RuntimeError("first B3 scientific activity must be seed-200 endpoint calibration")
        endpoint_grads = torch.autograd.grad(endpoint_graph, endpoint_parameters, allow_unused=False)
        candidate_b = float(gradient_norm(endpoint_grads).item())
        if not np.isfinite(candidate_b) or candidate_b <= 1.0e-12:
            endpoint_error = f"invalid calibration endpoint norm B={candidate_b}"
        else:
            b_value = candidate_b
            target = float(np.float64(CALIBRATION_DOSE) * np.float64(candidate_b))
        del endpoint_graph, endpoint_grads
    except Exception as exc:
        endpoint_error = f"endpoint-gradient unavailable: {type(exc).__name__}: {exc}"
    if model_state_digest(canonical) != initial_digest:
        raise RuntimeError("calibration endpoint-gradient mutated the update-zero model")
    cells: list[dict[str, object]] = []
    for arm in ARMS:
        clone = SCDMPModel(algorithm_seed)
        if model_state_digest(clone) != initial_digest:
            raise RuntimeError("calibration clone is not byte-identical to canonical initialization")
        if resource_check is not None:
            resource_check()
        a_value: float | None = None
        coefficient: float | None = None
        auxiliary_error: str | None = None
        if not lifecycle.scientific_activity_started:
            auxiliary_error = "not invoked because the required seed-200 endpoint-gradient was unavailable"
        else:
            try:
                auxiliary_graph = auxiliary_loss(clone, locked_zero, corpus.scales, arm)
                auxiliary_grads = torch.autograd.grad(auxiliary_graph, ordered_parameters(clone),
                                                      allow_unused=False)
                candidate_a = float(gradient_norm(auxiliary_grads).item())
                if not np.isfinite(candidate_a):
                    auxiliary_error = f"nonfinite calibration auxiliary norm A={candidate_a}"
                else:
                    a_value = candidate_a
                del auxiliary_graph, auxiliary_grads
            except Exception as exc:
                auxiliary_error = f"auxiliary-gradient unavailable: {type(exc).__name__}: {exc}"
        calibration_error = endpoint_error or auxiliary_error
        if calibration_error is None and a_value is not None and b_value is not None:
            if a_value < CALIBRATION_MIN_RATIO * b_value:
                calibration_error = (f"calibration lower bound failed: A={a_value} "
                                     f"< {CALIBRATION_MIN_RATIO}*B={b_value}")
            else:
                coefficient = float(np.float64(target) / np.float64(a_value))
                if not np.isfinite(coefficient):
                    calibration_error = "nonfinite fixed coefficient"
                    coefficient = None
        if model_state_digest(clone) != initial_digest:
            raise RuntimeError("calibration auxiliary-gradient mutated the update-zero model")
        cells.append({"algorithm_seed": algorithm_seed, "arm": arm, "B_s": b_value,
                      "T_s": target, "A_s_m_cal": a_value,
                      "lambda_s_m": coefficient, "fixed_for_updates": [0, 999],
                      "initial_model_sha256": initial_digest,
                      "locked_batch_update": 0, "support_certificate": support,
                      "model_mutation_during_calibration": False,
                      "optimizer_created_during_calibration": False,
                      "calibration_valid": calibration_error is None,
                      "calibration_error": calibration_error})
        del clone
    del canonical
    return cells


def initialize_cell(algorithm_seed: int) -> tuple[SCDMPModel, torch.optim.Adam]:
    model = SCDMPModel(algorithm_seed)
    return model, optimizer_for(model)


def train_update(model: SCDMPModel, optimizer: torch.optim.Adam, corpus: Corpus,
                 algorithm_seed: int, arm: str, update: int,
                 calibration: dict[str, object], plan: LockedBatchPlan | None = None,
                 ) -> tuple[dict[str, object], dict[str, float]]:
    if arm not in ARMS or int(calibration["algorithm_seed"]) != algorithm_seed \
            or calibration["arm"] != arm:
        raise RuntimeError("B3 calibration/cell identity mismatch")
    batch = (plan if plan is not None else LockedBatchPlan(corpus, algorithm_seed)).batch_for_update(update)
    parameters = ordered_parameters(model)
    optimizer.zero_grad(set_to_none=True)
    endpoint_graph = endpoint_loss(model, batch, corpus.scales)
    endpoint_grads = torch.autograd.grad(endpoint_graph, parameters, allow_unused=False)
    auxiliary_graph = auxiliary_loss(model, batch, corpus.scales, arm)
    auxiliary_grads = torch.autograd.grad(auxiliary_graph, parameters, allow_unused=False)
    endpoint_norm = float(gradient_norm(endpoint_grads).item())
    auxiliary_norm = float(gradient_norm(auxiliary_grads).item())
    if not np.isfinite(endpoint_norm) or not np.isfinite(auxiliary_norm):
        raise RuntimeError("nonfinite required B3 gradient norm")
    coefficient = float(calibration["lambda_s_m"])
    calibrated_auxiliary = float(calibration["A_s_m_cal"])
    dot: float | None = None
    if endpoint_norm > 0.0 and auxiliary_norm > 0.0:
        dot = float(gradient_dot(endpoint_grads, auxiliary_grads).item())
    diagnostics = diagnostic_values(endpoint_norm, auxiliary_norm, calibrated_auxiliary,
                                    coefficient, dot)
    combined_grads: list[Tensor] = []
    for parameter, endpoint_grad, auxiliary_grad in zip(parameters, endpoint_grads, auxiliary_grads):
        combined = (endpoint_grad.detach().to(torch.float64)
                    + np.float64(coefficient) * auxiliary_grad.detach().to(torch.float64))
        if not bool(torch.isfinite(combined).all()):
            raise RuntimeError("nonfinite combined B3 gradient")
        parameter.grad = combined.to(torch.float32)
        combined_grads.append(parameter.grad)
    preclip = float(gradient_norm(combined_grads).item())
    clip_return = torch.nn.utils.clip_grad_norm_(parameters, 1.0, norm_type=2.0,
        error_if_nonfinite=True, foreach=False)
    if not np.isclose(float(clip_return.item()), preclip, rtol=2e-6, atol=1e-12):
        raise RuntimeError("clip_grad_norm_ preclip return disagrees with ordered norm")
    postclip = float(gradient_norm([p.grad for p in parameters]).item())  # type: ignore[list-item]
    clipping_multiplier = 1.0 if preclip == 0.0 else postclip / preclip
    optimizer.step()
    trace = {"update": update, "E": endpoint_norm, "A": auxiliary_norm,
             **diagnostics,
             "preclip_combined_norm": preclip,
             "clipping_multiplier": clipping_multiplier,
             "postclip_combined_norm": postclip,
             "fixed_lambda": coefficient,
             "calibration_target": float(calibration["T_s"]),
             "finite_zero_auxiliary_continues": True}
    losses = {"endpoint": float(endpoint_graph.detach().item()),
              "auxiliary": float(auxiliary_graph.detach().item())}
    return trace, losses


def summarize_trace(trace: list[dict[str, object]]) -> dict[str, object]:
    if [int(row["update"]) for row in trace] != list(range(OPTIMIZER_UPDATES)):
        raise RuntimeError("B3 trace is not the full ordered 1,000-update trajectory")
    quarters = []
    for start, stop in QUARTERS:
        rows = trace[start:stop + 1]
        quarters.append({"updates": [start, stop],
                         "median_P": float(np.median([float(x["P"]) for x in rows])),
                         "median_R": float(np.median([float(x["R"]) for x in rows]))})
    return {"quarters": quarters, "final_P": float(trace[-1]["P"]),
            "final_R": float(trace[-1]["R"]), "trajectory_length": len(trace),
            "undefined_cosine_updates": [int(x["update"]) for x in trace
                                           if x["endpoint_auxiliary_cosine"] is None]}


def _component_rmse(pred: tuple[Tensor, Tensor, Tensor], rows: Sequence[BankRow],
    corpus: Corpus, reference: bool = False) -> dict[str, float]:
    truth = (np.stack([np.stack((r.terminal.e, r.terminal.v), -1) for r in rows]),
             np.stack([r.node_rewards for r in rows]), np.stack([r.edge_rewards for r in rows]))
    scales = (np.asarray((corpus.scales.e, corpus.scales.v)), corpus.scales.node_reward,
              corpus.scales.edge_reward)
    if reference:
        reference_f = np.empty_like(truth[0])
        reference_f[..., 0] = corpus.means["e"]
        reference_f[..., 1] = corpus.means["v"]
        predicted = (reference_f, np.full_like(truth[1], corpus.means["node_reward"]),
                     np.full_like(truth[2], corpus.means["edge_reward"]))
    else:
        predicted = tuple(x.detach().cpu().numpy() for x in pred)
    return {name: float(np.sqrt(np.mean(np.square((value-target)/scale))))
            for name, value, target, scale in zip(("F", "node", "edge"), predicted, truth, scales)}


def train_support_competence(model: SCDMPModel, corpus: Corpus) -> dict[str, object]:
    arm_mse: dict[str, list[float]] = {x: [] for x in ("F", "node", "edge")}
    ref_mse: dict[str, list[float]] = {x: [] for x in ("F", "node", "edge")}
    with torch.no_grad():
        for duration in (2, 4, 8):
            rows = corpus.probe_rows[duration]
            e, v, q, actions, words = arrays(rows)
            pred = model_call_batch(model, e, v, q, actions, words)
            arm_values = _component_rmse(pred, rows, corpus)
            ref_values = _component_rmse(pred, rows, corpus, reference=True)
            for name in arm_mse:
                arm_mse[name].append(arm_values[name] ** 2)
                ref_mse[name].append(ref_values[name] ** 2)
    arm_components = {name: float(np.sqrt(np.mean(x))) for name, x in arm_mse.items()}
    ref_components = {name: float(np.sqrt(np.mean(x))) for name, x in ref_mse.items()}
    arm_composite = float(np.mean(list(arm_components.values())))
    ref_composite = float(np.mean(list(ref_components.values())))
    if not np.isfinite(ref_composite) or ref_composite <= 1e-12:
        raise RuntimeError("invalid train-support MEAN-REF denominator")
    return {"arm_component_rmse": arm_components, "mean_ref_component_rmse": ref_components,
            "arm_composite_rmse": arm_composite, "mean_ref_composite_rmse": ref_composite,
            "ratio": arm_composite / ref_composite}


def checkpoint(model: SCDMPModel) -> dict[str, object]:
    return {name: tensor.detach().cpu().numpy().tolist()
            for name, tensor in model.state_dict().items()}
