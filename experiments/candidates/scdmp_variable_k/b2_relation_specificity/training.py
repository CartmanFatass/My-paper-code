from __future__ import annotations

import copy
from collections.abc import Callable, Sequence

import numpy as np
import torch
from torch import Tensor

from ..corpus import BankRow
from .config import ADAM, ARMS, OPTIMIZER_UPDATES, ORDERED_PARAMETER_NAMES
from .corpus import Corpus, LockedBatchStream, support_certificate
from .lifecycle import Lifecycle
from .model import SCDMPModel
from .relations import arrays, auxiliary_loss, endpoint_loss, model_call_batch, standardized_row_loss

ResourceCheck = Callable[[], None]


def ordered_parameters(model: SCDMPModel) -> tuple[Tensor, ...]:
    mapping = dict(model.named_parameters())
    if tuple(mapping) != ORDERED_PARAMETER_NAMES:
        raise RuntimeError(f"parameter traversal mismatch: {tuple(mapping)}")
    result = tuple(mapping[name] for name in ORDERED_PARAMETER_NAMES)
    if len({id(p) for p in result}) != 24 or any(not p.requires_grad for p in result):
        raise RuntimeError("ordered B2 parameter tuple is incomplete, duplicated, or frozen")
    return result


def gradient_norm(grads: Sequence[Tensor]) -> Tensor:
    total: Tensor | None = None
    for grad in grads:
        if grad is None or not bool(torch.isfinite(grad).all()):
            raise RuntimeError("missing or nonfinite gradient component")
        g64 = grad.detach().to(dtype=torch.float64).contiguous().view(-1)
        part = torch.sum(g64 * g64, dtype=torch.float64)
        total = part if total is None else total + part
    if total is None:
        raise RuntimeError("empty gradient tuple")
    return torch.sqrt(total)


def _optimizer(model: SCDMPModel) -> torch.optim.Adam:
    return torch.optim.Adam(model.parameters(), lr=ADAM["lr"], betas=ADAM["betas"],
                            eps=ADAM["eps"], weight_decay=ADAM["weight_decay"])


def train_three_arms(corpus: Corpus, algorithm_seed: int, lifecycle: Lifecycle,
    resource_check: ResourceCheck | None = None) -> tuple[dict[str, SCDMPModel], dict[str, object]]:
    canonical = SCDMPModel(algorithm_seed)
    params = ordered_parameters(canonical)
    stream = LockedBatchStream(corpus, algorithm_seed)
    locked_zero = stream.next_batch()
    support = support_certificate(corpus, locked_zero)
    if not support["conforming"]:
        raise RuntimeError("locked B2 update-zero support failed before activity")
    l0_init = endpoint_loss(canonical, locked_zero, corpus.scales)
    if not lifecycle.scientific_activity_started:
        if algorithm_seed != 100:
            raise RuntimeError("first B2 activity must be B_100")
        lifecycle.begin_b100()
    else:
        lifecycle.record("seed_calibration_begin", algorithm_seed=algorithm_seed)
    g0_init = torch.autograd.grad(l0_init, params, allow_unused=False)
    b = gradient_norm(g0_init)
    b_value = float(b.item())
    if not np.isfinite(b_value) or b_value <= 1e-12:
        raise RuntimeError(f"invalid B_s={b_value}")
    t = b.to(torch.float64) * torch.tensor(0.25, dtype=torch.float64)
    models = {arm: copy.deepcopy(canonical) for arm in ARMS}
    states = {arm: models[arm].state_dict() for arm in ARMS}
    first = states[ARMS[0]]
    if any(not torch.equal(first[name], states[arm][name]) for arm in ARMS[1:] for name in first):
        raise RuntimeError("B2 initialized arm tensors are not byte-identical")
    optimizers = {arm: _optimizer(models[arm]) for arm in ARMS}
    trace: dict[str, list[dict[str, float | int]]] = {arm: [] for arm in ARMS}
    final_losses: dict[str, dict[str, float]] = {}
    for update in range(OPTIMIZER_UPDATES):
        if resource_check is not None:
            resource_check()
        batch = locked_zero if update == 0 else stream.next_batch()
        for arm in ARMS:
            model = models[arm]
            parameters = ordered_parameters(model)
            optimizers[arm].zero_grad(set_to_none=True)
            l0 = endpoint_loss(model, batch, corpus.scales)
            g0 = torch.autograd.grad(l0, parameters, allow_unused=False)
            laux = auxiliary_loss(model, batch, corpus.scales, arm)
            ga = torch.autograd.grad(laux, parameters, allow_unused=False)
            a = gradient_norm(ga)
            a_value = float(a.item())
            if not np.isfinite(a_value) or a_value < 0.01 * b_value:
                raise RuntimeError(f"seed={algorithm_seed} arm={arm} update={update} invalid A={a_value}")
            scale = t / a
            scale_value = float(scale.item())
            for parameter, endpoint_grad, auxiliary_grad in zip(parameters, g0, ga):
                combined = endpoint_grad.detach().to(torch.float64) + scale * auxiliary_grad.detach().to(torch.float64)
                if not bool(torch.isfinite(combined).all()):
                    raise RuntimeError("nonfinite combined gradient")
                parameter.grad = combined.to(torch.float32)
            clipped = torch.nn.utils.clip_grad_norm_(parameters, 1.0, norm_type=2.0,
                error_if_nonfinite=True, foreach=False)
            optimizers[arm].step()
            trace[arm].append({"update": update, "raw_auxiliary_norm": a_value,
                               "scale": scale_value, "preclip_combined_norm": float(clipped.item())})
            final_losses[arm] = {"endpoint": float(l0.detach().item()), "auxiliary": float(laux.detach().item())}
    return models, {"B_s": b_value, "T_s": float(t.item()), "support_certificate": support,
                    "arm_order": list(ARMS), "updates_per_arm": OPTIMIZER_UPDATES,
                    "gradient_trace": trace, "final_losses": final_losses,
                    "endpoint_gradient_traversals": len(ARMS) * OPTIMIZER_UPDATES,
                    "auxiliary_gradient_traversals": len(ARMS) * OPTIMIZER_UPDATES,
                    "B_s_gradient_traversals": 1}


def _component_rmse(pred: tuple[Tensor, Tensor, Tensor], rows: Sequence[BankRow],
    corpus: Corpus, reference: bool = False) -> dict[str, float]:
    true = (np.stack([np.stack((r.terminal.e, r.terminal.v), -1) for r in rows]),
            np.stack([r.node_rewards for r in rows]), np.stack([r.edge_rewards for r in rows]))
    scales = (np.asarray((corpus.scales.e, corpus.scales.v)), corpus.scales.node_reward,
              corpus.scales.edge_reward)
    if reference:
        reference_f = np.empty_like(true[0])
        reference_f[..., 0] = corpus.means["e"]
        reference_f[..., 1] = corpus.means["v"]
        arrays_pred = (reference_f,
                       np.full_like(true[1], corpus.means["node_reward"]),
                       np.full_like(true[2], corpus.means["edge_reward"]))
    else:
        arrays_pred = tuple(x.detach().cpu().numpy() for x in pred)
    return {name: float(np.sqrt(np.mean(np.square((p-y)/s))))
            for name, p, y, s in zip(("F", "node", "edge"), arrays_pred, true, scales)}


def train_support_competence(model: SCDMPModel, corpus: Corpus) -> dict[str, object]:
    arm_mse: dict[str, list[float]] = {x: [] for x in ("F", "node", "edge")}
    ref_mse: dict[str, list[float]] = {x: [] for x in ("F", "node", "edge")}
    with torch.no_grad():
        for duration in (2, 4, 8):
            rows = corpus.probe_rows[duration]
            e, v, q, actions, words = arrays(rows)
            pred = model_call_batch(model, e, v, q, actions, words)
            arm = _component_rmse(pred, rows, corpus)
            ref = _component_rmse(pred, rows, corpus, reference=True)
            for name in arm_mse:
                arm_mse[name].append(arm[name] ** 2)
                ref_mse[name].append(ref[name] ** 2)
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
    return {name: tensor.detach().cpu().numpy().tolist() for name, tensor in model.state_dict().items()}
