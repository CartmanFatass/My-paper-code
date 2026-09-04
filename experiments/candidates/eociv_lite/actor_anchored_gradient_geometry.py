"""Pure gradient and retained-state geometry for EOCIV-B6.

This module deliberately knows nothing about the environment or artifact
lifecycle.  It owns the ordered parameter layout, exact vector realization,
lossless CPU serialization, copied-Adam diagnostics, and balanced vector
decompositions used by the B6 runtime.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import torch
from torch import nn


EXPECTED_PARAMETER_NAMES = (
    "log_std",
    "obs.weight",
    "recurrent.weight",
    "slot.weight",
    "slot.bias",
    "actor.weight",
    "actor.bias",
    "value.weight",
    "value.bias",
    "content_embedding.weight",
)
EXPECTED_PARAMETER_NUMELS = (2, 160, 256, 512, 16, 32, 2, 16, 1, 64)
EXPECTED_TOTAL_NUMEL = 1061
GROUPS = {
    "shared_trunk": ("obs.weight", "recurrent.weight", "slot.weight", "slot.bias", "content_embedding.weight"),
    "policy_head": ("log_std", "actor.weight", "actor.bias"),
    "value_head": ("value.weight", "value.bias"),
}


class GeometryError(RuntimeError):
    """Fail-closed B6 geometry or retained-state error."""


def ordered_layout(module: nn.Module) -> dict[str, Any]:
    named = tuple(module.named_parameters())
    names = tuple(name for name, _ in named)
    numels = tuple(parameter.numel() for _, parameter in named)
    if names != EXPECTED_PARAMETER_NAMES or numels != EXPECTED_PARAMETER_NUMELS:
        raise GeometryError(f"unregistered parameter layout: names={names}, numels={numels}")
    offsets: dict[str, tuple[int, int]] = {}
    cursor = 0
    rows = []
    for name, parameter in named:
        end = cursor + parameter.numel()
        offsets[name] = (cursor, end)
        rows.append({
            "name": name,
            "shape": list(parameter.shape),
            "dtype": str(parameter.dtype).removeprefix("torch."),
            "numel": parameter.numel(),
            "start": cursor,
            "end": end,
        })
        cursor = end
    if cursor != EXPECTED_TOTAL_NUMEL:
        raise GeometryError("parameter total changed")
    group_indices: dict[str, list[int]] = {}
    for group, members in GROUPS.items():
        indices: list[int] = []
        for member in members:
            start, end = offsets[member]
            indices.extend(range(start, end))
        group_indices[group] = indices
    if sorted(index for values in group_indices.values() for index in values) != list(range(cursor)):
        raise GeometryError("structural groups do not partition the parameter vector")
    material = "|".join(f"{row['name']}:{row['shape']}:{row['dtype']}" for row in rows)
    return {
        "parameters": rows,
        "total_numel": cursor,
        "groups": {key: list(value) for key, value in GROUPS.items()},
        "group_indices": group_indices,
        "layout_sha256": hashlib.sha256(material.encode("utf-8")).hexdigest(),
    }


def flatten_gradients(
    loss: torch.Tensor,
    parameters: Sequence[nn.Parameter],
    *,
    retain_graph: bool = True,
) -> torch.Tensor:
    gradients = torch.autograd.grad(
        loss, tuple(parameters), retain_graph=retain_graph, allow_unused=True
    )
    pieces = [
        torch.zeros(parameter.numel(), dtype=torch.float64)
        if gradient is None
        else gradient.detach().cpu().contiguous().reshape(-1).to(torch.float64)
        for parameter, gradient in zip(parameters, gradients)
    ]
    vector = torch.cat(pieces)
    if vector.numel() != EXPECTED_TOTAL_NUMEL or not torch.isfinite(vector).all():
        raise GeometryError("gradient vector is nonfinite or has the wrong size")
    return vector


def actor_critic_vectors(
    actor_loss: torch.Tensor,
    critic_loss: torch.Tensor,
    module: nn.Module,
) -> tuple[torch.Tensor, torch.Tensor]:
    layout = ordered_layout(module)
    parameters = tuple(module.parameters())
    if any(parameter.grad is not None for parameter in parameters):
        raise GeometryError("gradient extraction requires untouched .grad fields")
    actor = flatten_gradients(actor_loss, parameters, retain_graph=True)
    critic = flatten_gradients(0.5 * critic_loss, parameters, retain_graph=True)
    if any(parameter.grad is not None for parameter in parameters):
        raise GeometryError("autograd.grad polluted .grad fields")
    idx = layout["group_indices"]
    if torch.count_nonzero(actor[idx["value_head"]]).item() != 0:
        raise GeometryError("actor vector has nonzero value-head entries")
    if torch.count_nonzero(critic[idx["policy_head"]]).item() != 0:
        raise GeometryError("critic vector has nonzero policy-head entries")
    return actor, critic


def l2_norm(vector: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(vector.to(torch.float64)))


def project_cap(vector: torch.Tensor, cap: float = 0.5) -> tuple[torch.Tensor, float]:
    value = vector.to(torch.float64)
    norm = l2_norm(value)
    if not math.isfinite(norm):
        raise GeometryError("nonfinite vector norm")
    scale = 1.0 if norm == 0.0 else min(1.0, float(cap) / norm)
    return value * scale, scale


def intervention_vectors(
    actor: torch.Tensor,
    critic: torch.Tensor,
    *,
    cap: float = 0.5,
    require_nonzero_actor: bool = True,
) -> dict[str, Any]:
    a = actor.to(torch.float64)
    v = critic.to(torch.float64)
    actor_norm = l2_norm(a)
    critic_norm = l2_norm(v)
    if not math.isfinite(actor_norm) or not math.isfinite(critic_norm):
        raise GeometryError("nonfinite actor or critic norm")
    if require_nonzero_actor and actor_norm == 0.0:
        raise GeometryError("exactly zero actor norm")
    alpha = 1.0 if critic_norm == 0.0 else min(1.0, float(cap) / critic_norm, actor_norm / critic_norm)
    if not math.isfinite(alpha):
        raise GeometryError("nonfinite treatment alpha")
    baseline_pre = a + v
    treatment_pre = a + alpha * v
    baseline, baseline_scale = project_cap(baseline_pre, cap)
    treatment, treatment_scale = project_cap(treatment_pre, cap)
    if l2_norm(alpha * v) > min(actor_norm, float(cap)) + 1e-12:
        raise GeometryError("critic constraint was not realized")
    return {
        "actor": a,
        "critic": v,
        "alpha": alpha,
        "baseline_pre": baseline_pre,
        "treatment_pre": treatment_pre,
        "baseline": baseline,
        "treatment": treatment,
        "actor_norm": actor_norm,
        "critic_norm": critic_norm,
        "baseline_pre_norm": l2_norm(baseline_pre),
        "treatment_pre_norm": l2_norm(treatment_pre),
        "baseline_final_scale": baseline_scale,
        "treatment_final_scale": treatment_scale,
    }


def assign_gradient_vector(module: nn.Module, vector: torch.Tensor) -> torch.Tensor:
    layout = ordered_layout(module)
    value = vector.detach().cpu().to(torch.float64).reshape(-1)
    if value.numel() != layout["total_numel"] or not torch.isfinite(value).all():
        raise GeometryError("assigned gradient is invalid")
    pieces = []
    for row, parameter in zip(layout["parameters"], module.parameters()):
        piece = value[row["start"] : row["end"]].reshape(parameter.shape).to(parameter.dtype)
        parameter.grad = piece.clone()
        pieces.append(parameter.grad.detach().cpu().reshape(-1).to(torch.float64))
    realized = torch.cat(pieces)
    expected = torch.cat([
        value[row["start"] : row["end"]].to(parameter.dtype).to(torch.float64)
        for row, parameter in zip(layout["parameters"], module.parameters())
    ])
    if not torch.equal(realized, expected):
        raise GeometryError("assigned gradient did not round-trip exactly")
    return realized


def _tensor_bytes(tensor: torch.Tensor) -> bytes:
    value = tensor.detach().cpu().contiguous()
    if value.dtype == torch.bfloat16:
        return value.view(torch.uint16).numpy().astype("<u2", copy=False).tobytes()
    array = value.numpy()
    return array.astype(array.dtype.newbyteorder("<"), copy=False).tobytes()


def tensor_record(name: str, tensor: torch.Tensor) -> dict[str, Any]:
    value = tensor.detach().cpu().contiguous()
    raw = _tensor_bytes(value)
    return {
        "name": name,
        "dtype": str(value.dtype).removeprefix("torch."),
        "shape": list(value.shape),
        "byte_order": "little",
        "encoding": "base64",
        "data": base64.b64encode(raw).decode("ascii"),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


_NUMPY_DTYPES = {
    "float32": np.dtype("<f4"), "float64": np.dtype("<f8"),
    "int64": np.dtype("<i8"), "int32": np.dtype("<i4"),
    "uint8": np.dtype("u1"), "bool": np.dtype("?"),
}


def tensor_from_record(record: Mapping[str, Any]) -> torch.Tensor:
    dtype_name = str(record["dtype"])
    if dtype_name not in _NUMPY_DTYPES:
        raise GeometryError(f"unsupported retained dtype {dtype_name}")
    raw = base64.b64decode(str(record["data"]), validate=True)
    if hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise GeometryError("retained tensor hash mismatch")
    array = np.frombuffer(raw, dtype=_NUMPY_DTYPES[dtype_name]).copy()
    shape = tuple(int(value) for value in record["shape"])
    if array.size != int(np.prod(shape, dtype=np.int64)):
        raise GeometryError("retained tensor shape mismatch")
    return torch.from_numpy(array.reshape(shape))


def serialize_parameter_state(module: nn.Module) -> dict[str, Any]:
    layout = ordered_layout(module)
    records = [tensor_record(name, parameter) for name, parameter in module.named_parameters()]
    for (name, parameter), record in zip(module.named_parameters(), records):
        if not torch.equal(parameter.detach().cpu(), tensor_from_record(record)):
            raise GeometryError(f"parameter round-trip failed for {name}")
    return {"layout_sha256": layout["layout_sha256"], "tensors": records, "state_sha256": records_digest(records)}


def materialize_zero_adam(optimizer: torch.optim.Adam) -> None:
    for group in optimizer.param_groups:
        for parameter in group["params"]:
            state = optimizer.state[parameter]
            if state:
                raise GeometryError("INIT optimizer was not empty before zero materialization")
            state["step"] = torch.tensor(0.0)
            state["exp_avg"] = torch.zeros_like(parameter, memory_format=torch.preserve_format)
            state["exp_avg_sq"] = torch.zeros_like(parameter, memory_format=torch.preserve_format)


def serialize_optimizer_state(module: nn.Module, optimizer: torch.optim.Adam) -> dict[str, Any]:
    names = {id(parameter): name for name, parameter in module.named_parameters()}
    rows = []
    group_rows = []
    for group_index, group in enumerate(optimizer.param_groups):
        parameter_names = [names[id(parameter)] for parameter in group["params"]]
        group_rows.append({
            "group_index": group_index,
            "parameter_names": parameter_names,
            "lr": float(group["lr"]), "betas": [float(x) for x in group["betas"]],
            "eps": float(group["eps"]), "weight_decay": float(group["weight_decay"]),
            "amsgrad": bool(group["amsgrad"]), "maximize": bool(group["maximize"]),
        })
        for parameter, name in zip(group["params"], parameter_names):
            state = optimizer.state.get(parameter, {})
            if set(state) != {"step", "exp_avg", "exp_avg_sq"}:
                raise GeometryError(f"Adam state is incomplete for {name}: {set(state)}")
            records = [tensor_record(f"{name}.{key}", state[key]) for key in ("step", "exp_avg", "exp_avg_sq")]
            if any(not torch.equal(state[key].detach().cpu(), tensor_from_record(record)) for key, record in zip(("step", "exp_avg", "exp_avg_sq"), records)):
                raise GeometryError(f"optimizer round-trip failed for {name}")
            rows.append({"parameter_name": name, "state": records})
    return {"parameter_groups": group_rows, "states": rows, "state_sha256": hashlib.sha256(repr((group_rows, [row["state"] for row in rows])).encode()).hexdigest()}


def records_digest(records: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(str(record["name"]).encode())
        digest.update(str(record["sha256"]).encode())
    return digest.hexdigest()


def vector_record(name: str, vector: torch.Tensor) -> dict[str, Any]:
    return tensor_record(name, vector.detach().cpu().to(torch.float32).contiguous())


def copied_adam_next_delta(
    module: nn.Module,
    optimizer: torch.optim.Adam,
    gradient: torch.Tensor,
) -> torch.Tensor:
    before_parameters = [parameter.detach().cpu().clone() for parameter in module.parameters()]
    before_state = copy.deepcopy(optimizer.state_dict())
    value = gradient.detach().cpu().to(torch.float64).reshape(-1)
    layout = ordered_layout(module)
    if value.numel() != layout["total_numel"]:
        raise GeometryError("copied Adam gradient size mismatch")
    if len(optimizer.param_groups) != 1:
        raise GeometryError("B6 copied Adam requires the registered single parameter group")
    group = optimizer.param_groups[0]
    if bool(group["amsgrad"]) or bool(group["maximize"]) or float(group["weight_decay"]) != 0.0:
        raise GeometryError("B6 copied Adam admits only the registered default Adam rule")
    copied_parameters = [nn.Parameter(parameter.clone()) for parameter in before_parameters]
    copied_optimizer = torch.optim.Adam(
        copied_parameters, lr=float(group["lr"]), betas=tuple(float(x) for x in group["betas"]),
        eps=float(group["eps"]), weight_decay=float(group["weight_decay"]),
        amsgrad=bool(group["amsgrad"]), maximize=bool(group["maximize"]),
    )
    copied_optimizer.load_state_dict(copy.deepcopy(before_state))
    for row, parameter in zip(layout["parameters"], copied_parameters):
        parameter.grad = value[row["start"]:row["end"]].reshape(parameter.shape).to(parameter.dtype).clone()
    copied_optimizer.step()
    delta = torch.cat([(parameter.detach()-before).reshape(-1).to(torch.float64) for parameter,before in zip(copied_parameters,before_parameters)])
    if any(not torch.equal(parameter.detach().cpu(), before) for parameter, before in zip(module.parameters(), before_parameters)):
        raise GeometryError("copied Adam mutated source parameters")
    current = optimizer.state_dict()
    if current["param_groups"] != before_state["param_groups"]:
        raise GeometryError("copied Adam mutated source parameter groups")
    for key in before_state["state"]:
        for field in ("step", "exp_avg", "exp_avg_sq"):
            if not torch.equal(current["state"][key][field], before_state["state"][key][field]):
                raise GeometryError("copied Adam mutated source moments")
    return delta


def projection_diagnostics(actor: torch.Tensor, delta: torch.Tensor, layout: Mapping[str, Any]) -> dict[str, Any]:
    a = actor.to(torch.float64)
    direction = -delta.to(torch.float64)
    actor_norm = l2_norm(a)
    delta_norm = l2_norm(direction)
    dot = float(torch.dot(direction, a))
    cosine = 0.0 if actor_norm == 0.0 or delta_norm == 0.0 else dot / (actor_norm * delta_norm)
    groups = {}
    for group, indices in layout["group_indices"].items():
        av = a[indices]
        dv = direction[indices]
        groups[group] = {"negative_delta_actor_projection": float(torch.dot(dv, av)), "negative_delta_norm": l2_norm(dv), "actor_norm": l2_norm(av)}
    return {"negative_delta_actor_projection": dot, "cosine": cosine, "negative_delta_norm": delta_norm, "groups": groups}


def energy_identity(actor: torch.Tensor, critic: torch.Tensor, layout: Mapping[str, Any]) -> dict[str, Any]:
    a, v = actor.to(torch.float64), critic.to(torch.float64)
    def one(indices: Sequence[int]) -> dict[str, float]:
        aa, vv = a[list(indices)], v[list(indices)]
        actor_energy = float(torch.dot(aa, aa))
        critic_energy = float(torch.dot(vv, vv))
        cross = float(torch.dot(aa, vv))
        joint = float(torch.dot(aa + vv, aa + vv))
        overlap = 0.0 if actor_energy == 0.0 or critic_energy == 0.0 else max(
            -1.0, min(1.0, cross / math.sqrt(actor_energy * critic_energy))
        )
        if not math.isfinite(overlap) or not -1.0 <= overlap <= 1.0:
            raise GeometryError("actor/critic bounded overlap is invalid")
        residual = joint - (actor_energy + critic_energy + 2.0 * cross)
        if abs(residual) > 1e-9 * max(1.0, joint, actor_energy, critic_energy):
            raise GeometryError("joint energy identity failed")
        return {"actor": actor_energy, "critic": critic_energy, "cross": cross, "joint": joint, "bounded_overlap": overlap, "identity_residual": residual}
    output = {"full": one(range(a.numel()))}
    output.update({group: one(indices) for group, indices in layout["group_indices"].items()})
    return output


def finite_variance(actor_cells: Mapping[tuple[int, int], torch.Tensor], critic_cells: Mapping[tuple[int, int], torch.Tensor], layout: Mapping[str, Any]) -> dict[str, Any]:
    roots = sorted({key[0] for key in actor_cells})
    shocks = sorted({key[1] for key in actor_cells})
    if len(roots) != 3 or len(shocks) != 4 or set(actor_cells) != set(critic_cells) or len(actor_cells) != 12:
        raise GeometryError("finite variance requires balanced 3-root x 4-shock cells")
    def components(cells: Mapping[tuple[int, int], torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
        root_means = {root: torch.stack([cells[(root, shock)].to(torch.float64) for shock in shocks]).mean(0) for root in roots}
        grand = torch.stack(list(root_means.values())).mean(0)
        root_rows = torch.stack([root_means[root] - grand for root in roots])
        shock_rows = torch.stack([cells[(root, shock)].to(torch.float64) - root_means[root] for root in roots for shock in shocks])
        return root_rows, shock_rows
    ar, ash = components(actor_cells)
    cr, csh = components(critic_cells)
    def summarized(a_rows: torch.Tensor, c_rows: torch.Tensor, divisor: float, indices: Sequence[int] | None = None) -> dict[str, Any]:
        if indices is not None:
            a_rows, c_rows = a_rows[:, list(indices)], c_rows[:, list(indices)]
        mean_a = (a_rows.square().sum(1).sum() / divisor).item()
        mean_c = (c_rows.square().sum(1).sum() / divisor).item()
        cross = ((a_rows * c_rows).sum(1).sum() / divisor).item()
        joint = ((a_rows + c_rows).square().sum(1).sum() / divisor).item()
        return {"actor": mean_a, "critic": mean_c, "cross": cross, "joint": joint, "identity_residual": joint - mean_a - mean_c - 2.0 * cross}
    full = {"V_root": summarized(ar, cr, 3.0), "V_shock": summarized(ash, csh, 48.0)}
    return {
        **full,
        "groups": {
            group: {"V_root": summarized(ar, cr, 3.0, indices), "V_shock": summarized(ash, csh, 48.0, indices)}
            for group, indices in layout["group_indices"].items()
        },
    }


def balanced_factorial(
    actor_cells: Mapping[tuple[str, int, int], torch.Tensor],
    critic_cells: Mapping[tuple[str, int, int], torch.Tensor],
    layout: Mapping[str, Any],
) -> dict[str, Any]:
    states = ("INIT", "BASELINE_FINAL", "TREATMENT_FINAL")
    roots = (0, 1, 2)
    shocks = (0, 1, 2, 3)
    keys = {(state, root, shock) for state in states for root in roots for shock in shocks}
    if set(actor_cells) != keys or set(critic_cells) != keys:
        raise GeometryError("factorial requires exact 3-state x 3-root x 4-shock cells")

    def effects(cells: Mapping[tuple[str, int, int], torch.Tensor]) -> dict[str, list[torch.Tensor]]:
        x = {key: cells[key].to(torch.float64) for key in keys}
        grand = torch.stack(list(x.values())).mean(0)
        sm = {s: torch.stack([x[(s, r, h)] for r in roots for h in shocks]).mean(0) for s in states}
        rm = {r: torch.stack([x[(s, r, h)] for s in states for h in shocks]).mean(0) for r in roots}
        hm = {h: torch.stack([x[(s, r, h)] for s in states for r in roots]).mean(0) for h in shocks}
        srm = {(s, r): torch.stack([x[(s, r, h)] for h in shocks]).mean(0) for s in states for r in roots}
        shm = {(s, h): torch.stack([x[(s, r, h)] for r in roots]).mean(0) for s in states for h in shocks}
        rhm = {(r, h): torch.stack([x[(s, r, h)] for s in states]).mean(0) for r in roots for h in shocks}
        result = {
            "state": [sm[s] - grand for s in states],
            "root": [rm[r] - grand for r in roots],
            "shock": [hm[h] - grand for h in shocks],
            "state_x_root": [srm[(s, r)] - sm[s] - rm[r] + grand for s in states for r in roots],
            "state_x_shock": [shm[(s, h)] - sm[s] - hm[h] + grand for s in states for h in shocks],
            "root_x_shock": [rhm[(r, h)] - rm[r] - hm[h] + grand for r in roots for h in shocks],
        }
        result["state_x_root_x_shock"] = [
            x[(s, r, h)] - srm[(s, r)] - shm[(s, h)] - rhm[(r, h)] + sm[s] + rm[r] + hm[h] - grand
            for s in states for r in roots for h in shocks
        ]
        reconstruction = []
        for s in states:
            for r in roots:
                for h in shocks:
                    rebuilt = grand + (sm[s]-grand) + (rm[r]-grand) + (hm[h]-grand)
                    rebuilt += srm[(s,r)]-sm[s]-rm[r]+grand
                    rebuilt += shm[(s,h)]-sm[s]-hm[h]+grand
                    rebuilt += rhm[(r,h)]-rm[r]-hm[h]+grand
                    rebuilt += x[(s,r,h)]-srm[(s,r)]-shm[(s,h)]-rhm[(r,h)]+sm[s]+rm[r]+hm[h]-grand
                    reconstruction.append(l2_norm(rebuilt-x[(s,r,h)]))
        if max(reconstruction) > 1e-10:
            raise GeometryError("factorial reconstruction failed")
        result["_reconstruction_max"] = [torch.tensor(max(reconstruction), dtype=torch.float64)]
        return result

    ae, ce = effects(actor_cells), effects(critic_cells)
    output: dict[str, Any] = {}
    for term in ("state", "root", "shock", "state_x_root", "state_x_shock", "root_x_shock", "state_x_root_x_shock"):
        arows, crows = torch.stack(ae[term]), torch.stack(ce[term])
        divisor = float(arows.shape[0])
        output[term] = {
            "actor": float(arows.square().sum(1).mean()),
            "critic": float(crows.square().sum(1).mean()),
            "cross": float((arows*crows).sum(1).mean()),
            "joint": float((arows+crows).square().sum(1).mean()),
        }
        output[term]["identity_residual"] = output[term]["joint"] - output[term]["actor"] - output[term]["critic"] - 2.0*output[term]["cross"]
    output["reconstruction_max"] = max(float(ae["_reconstruction_max"][0]), float(ce["_reconstruction_max"][0]))
    output["groups"] = {}
    for group, indices in layout["group_indices"].items():
        group_output = {}
        for term in ("state", "root", "shock", "state_x_root", "state_x_shock", "root_x_shock", "state_x_root_x_shock"):
            arows, crows = torch.stack(ae[term])[:, indices], torch.stack(ce[term])[:, indices]
            group_output[term] = {
                "actor": float(arows.square().sum(1).mean()),
                "critic": float(crows.square().sum(1).mean()),
                "cross": float((arows*crows).sum(1).mean()),
                "joint": float((arows+crows).square().sum(1).mean()),
            }
            group_output[term]["identity_residual"] = group_output[term]["joint"] - group_output[term]["actor"] - group_output[term]["critic"] - 2.0*group_output[term]["cross"]
        output["groups"][group] = group_output
    return output
