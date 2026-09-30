"""Zero-initialized bounded heads and the fixed weighted B05 paired-score fit.

Only cached original-S hidden vectors/logits enter this module. No backbone,
native environment, critic, or scientific asset is queried here.
"""
from collections.abc import Mapping
import hashlib
import time

import numpy as np
import torch
from torch import nn

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest, movement
from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest


BATCH_SIZE = 128
MU_ATOL = 5e-15
_COUNT_KEYS = ("head_fits_started", "head_fits_completed", "head_optimizer_steps", "head_training_rows")
DATA_KEYS = ("hidden", "logits", "mu", "action_a", "action_b", "delta_j", "weight")


class Head(nn.Module):
    """The identical one-row FP32 fitting/deployment program for CAL or CONT."""
    def __init__(self, kind):
        super().__init__()
        if kind not in ("CAL", "CONT"):
            raise ValueError("head kind must be CAL or CONT")
        self.kind = kind
        if kind == "CAL":
            self.alpha = nn.Parameter(torch.zeros((), dtype=torch.float32, device="cpu"))
        else:
            self.W = nn.Parameter(torch.zeros((27, 128), dtype=torch.float32, device="cpu"))
        self.b = nn.Parameter(torch.zeros(27, dtype=torch.float32, device="cpu"))

    def forward(self, hidden, logits):
        for value, shape in ((hidden, (128,)), (logits, (27,))):
            if (not isinstance(value, torch.Tensor) or value.shape != shape or
                    value.dtype != torch.float32 or value.device.type != "cpu"):
                raise ValueError("head accepts exactly one CPU FP32 hidden/logit row")
            if not torch.isfinite(value).all():
                raise FloatingPointError("nonfinite cached head context")
        if any(p.dtype != torch.float32 or p.device.type != "cpu" or not torch.isfinite(p).all()
               for p in self.parameters()):
            raise FloatingPointError("head parameters must remain finite CPU FP32")
        if self.kind == "CAL":
            preactivation = self.alpha * (logits - logits.mean()) + self.b
        else:
            preactivation = torch.mv(self.W, hidden) + self.b
        if not torch.isfinite(preactivation).all():
            raise FloatingPointError("nonfinite head preactivation")
        result = logits + .5 * torch.tanh(preactivation)
        if not torch.isfinite(result).all():
            raise FloatingPointError("nonfinite head logits")
        return result


def validate_data(data):
    """Require the saved NumPy contract and original-S mixture support.

    MU_ATOL bounds FP64 rounding in the bounded 27-term stable exponential
    normalization and half-mixture (about 23 machine epsilons at unit scale).
    It is a density agreement tolerance, not a finite-grid sampler theorem.
    """
    if not isinstance(data, Mapping) or "hidden" not in data:
        raise ValueError("cached fitting data must be a mapping")
    hidden = data["hidden"]
    if not isinstance(hidden, np.ndarray) or hidden.ndim != 2 or hidden.shape[1:] != (128,) or not len(hidden):
        raise ValueError("hidden requires nonempty Nx128 NumPy rows")
    n = len(hidden)
    fields = dict(hidden=((n, 128), np.float32), logits=((n, 27), np.float32),
                  mu=((n, 27), np.float64), action_a=((n,), np.int64), action_b=((n,), np.int64),
                  delta_j=((n,), np.float64), weight=((n,), np.float64))
    for key, (shape, dtype) in fields.items():
        if key not in data or not isinstance(data[key], np.ndarray) or data[key].shape != shape or data[key].dtype != np.dtype(dtype):
            raise ValueError(f"{key} requires NumPy {dtype} with shape {shape}")
        if not np.isfinite(data[key]).all():
            raise FloatingPointError("nonfinite cached fitting field: " + key)
    for key in ("action_a", "action_b"):
        if np.any((data[key] < 0) | (data[key] >= 27)):
            raise ValueError("paired actions must be in [0,27)")
    if np.any(data["weight"] <= 0):
        raise ValueError("context weights must be positive")
    z = data["logits"].astype(np.float64)
    p = np.exp(z - z.max(axis=-1, keepdims=True))
    p /= p.sum(axis=-1, keepdims=True, dtype=np.float64)
    expected_mu = .5 * p + .5 / 27.
    if np.any(data["mu"] < 1. / 54. - MU_ATOL) or np.max(np.abs(data["mu"] - expected_mu)) > MU_ATOL:
        raise ValueError("mu disagrees with the fixed half-S/half-uniform mixture")
    return n


def _indices(indices, n):
    if not isinstance(indices, np.ndarray) or indices.dtype != np.int64 or indices.shape != (BATCH_SIZE,):
        raise ValueError("exactly 128 NumPy int64 indices required")
    if np.any((indices < 0) | (indices >= n)):
        raise ValueError("batch index outside cached data")


def _log_probs(z):
    # Subtract before forming the log normalizer: adding log(sum(exp)) back to
    # a huge common logit would lose it even in FP64.
    shifted = z - z.max(dim=-1, keepdim=True).values
    return shifted - torch.logsumexp(shifted, dim=-1, keepdim=True)


def _loss(head, data, indices, counts=None):
    outputs = []
    for index in indices:
        # Copy only this cached row; detach context tensors from the parameter
        # graph. Exactly this Head.forward is also used in deployment.
        hidden = torch.tensor(data["hidden"][index], dtype=torch.float32)
        logits = torch.tensor(data["logits"][index], dtype=torch.float32)
        if counts is not None:
            counts["head_training_rows"] = counts.get("head_training_rows", 0) + 1
        outputs.append(head(hidden, logits))
    z = torch.stack(outputs).double()
    logp = _log_probs(z)
    p = logp.exp()
    source = torch.tensor(data["logits"][indices], dtype=torch.float64)
    log_s = _log_probs(source)
    mu = torch.tensor(data["mu"][indices], dtype=torch.float64)
    a = torch.tensor(data["action_a"][indices], dtype=torch.int64)
    b = torch.tensor(data["action_b"][indices], dtype=torch.int64)
    delta = torch.tensor(data["delta_j"][indices], dtype=torch.float64)
    weight = torch.tensor(data["weight"][indices], dtype=torch.float64)
    ratio_a = p.gather(-1, a[:, None]).squeeze(-1) / mu.gather(-1, a[:, None]).squeeze(-1)
    ratio_b = p.gather(-1, b[:, None]).squeeze(-1) / mu.gather(-1, b[:, None]).squeeze(-1)
    score = .5 * delta * (ratio_a - ratio_b)
    kl = (p * (logp - log_s)).sum(-1)
    entropy = -(p * logp).sum(-1)
    loss = (weight * (-score + .01 * kl)).sum() / BATCH_SIZE
    intermediates = (logp, p, log_s, ratio_a, ratio_b, score, kl, entropy, loss)
    if any(not torch.isfinite(value).all() for value in intermediates):
        raise FloatingPointError("nonfinite paired-score loss or density")
    diagnostics = dict(loss=float(loss.detach()), F=float((weight * score).detach().sum() / BATCH_SIZE),
                       KL=float((weight * kl).detach().sum() / BATCH_SIZE),
                       entropy=float(entropy.detach().mean()), weighted_entropy=float((weight * entropy).detach().mean()),
                       ratio_a_mean=float(ratio_a.detach().mean()), ratio_b_mean=float(ratio_b.detach().mean()))
    if not np.isfinite(list(diagnostics.values())).all():
        raise FloatingPointError("nonfinite paired-score diagnostics")
    return loss, diagnostics


def paired_loss(head, data, indices):
    """FP64 weighted objective with fixed denominator 128; FP32 head gradients."""
    n = validate_data(data)
    _indices(indices, n)
    if not isinstance(head, Head):
        raise ValueError("paired loss requires a CAL/CONT Head")
    return _loss(head, data, indices)


def _steps(optimizer, head):
    return [float(optimizer.state.get(p, {}).get("step", 0)) for p in head.parameters()]


def fit_head(kind, data, *, seed, counts, updates=2048, batch_size=128, progress=None):
    """One fixed fit; small synthetic checks may reduce updates, never batch size.

    ``progress(record)`` receives the same mutable record before/after each
    update and on failure. Exceptions carry ``fit_record``; no fit is retried.
    Counts retain attempted row calls and actual completed Adam steps on failure.
    """
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    n = validate_data(data)
    if type(updates) is not int or updates <= 0 or type(batch_size) is not int or batch_size != BATCH_SIZE:
        raise ValueError("positive update count and fixed batch size 128 required")
    if type(seed) is not int or seed < 0 or kind not in ("CAL", "CONT"):
        raise ValueError("valid head kind and nonnegative integer batch seed required")
    for key in _COUNT_KEYS:
        if type(counts.get(key, 0)) is not int or counts.get(key, 0) < 0:
            raise ValueError("invalid fitting counter: " + key)
    if progress is not None and not callable(progress):
        raise ValueError("progress must be a callable receiving the mutable fit record")
    head = Head(kind)
    optimizer = torch.optim.Adam(head.parameters(), lr=.001, betas=(.9, .999), eps=1e-8,
                                 weight_decay=0, amsgrad=False, foreach=False, fused=False)
    initial = {key: value.detach().clone() for key, value in head.state_dict().items()}
    start_counts = {key: counts.get(key, 0) for key in _COUNT_KEYS}
    counts["head_fits_started"] = counts.get("head_fits_started", 0) + 1
    record = dict(kind=kind, status="INCOMPLETE", seed=seed, contexts=n, planned_updates=updates,
                  batch_size=BATCH_SIZE, parameters=sum(p.numel() for p in head.parameters()),
                  data_sha256=array_digest(*(data[key] for key in DATA_KEYS)),
                  initial_state_sha256=state_digest(initial), initial_optimizer_entries=0,
                  updates=[], optimizer_steps=0, training_rows=0)
    rng = np.random.default_rng(seed)
    order = hashlib.sha256()

    def snapshot():
        record.update(final_state_sha256=state_digest(head.state_dict()), adam_step_values=_steps(optimizer, head),
                      optimizer_steps=counts.get("head_optimizer_steps", 0) - start_counts["head_optimizer_steps"],
                      training_rows=counts.get("head_training_rows", 0) - start_counts["head_training_rows"],
                      batch_order_sha256=order.hexdigest(), wall_seconds=time.perf_counter() - start_wall,
                      cpu_seconds=time.process_time() - start_cpu,
                      parameters_finite=all(bool(torch.isfinite(p).all()) for p in head.parameters()))
        record["movement"] = movement(initial, head.state_dict()) if record["parameters_finite"] else None
        record["counts"] = {key: counts.get(key, 0) - start_counts[key] for key in _COUNT_KEYS}

    def emit():
        snapshot()
        if progress is not None:
            progress(record)

    try:
        emit()
        for update in range(updates):
            indices = rng.integers(0, n, size=BATCH_SIZE)
            payload = indices.astype("<i8", copy=False).tobytes()
            order.update(payload)
            epoch = dict(update=update, batch_sha256=hashlib.sha256(payload).hexdigest(),
                         optimizer_step_completed=False, status="INCOMPLETE")
            record["updates"].append(epoch)
            emit()
            optimizer.zero_grad(set_to_none=True)
            loss, diagnostics = _loss(head, data, indices, counts)
            epoch.update(diagnostics)
            loss.backward()
            gradients = [p.grad for p in head.parameters()]
            if any(g is None or g.dtype != torch.float32 or not torch.isfinite(g).all() for g in gradients):
                raise FloatingPointError("nonfinite/missing FP32 head gradient")
            flat = torch.cat([g.detach().double().reshape(-1) for g in gradients])
            epoch.update(gradient_l2=float(torch.linalg.vector_norm(flat)), gradient_max_abs=float(flat.abs().max()))
            optimizer.step()
            counts["head_optimizer_steps"] = counts.get("head_optimizer_steps", 0) + 1
            epoch["optimizer_step_completed"] = True
            if (any(not torch.isfinite(p).all() for p in head.parameters()) or
                    any(not torch.isfinite(value).all() for entry in optimizer.state.values() for value in entry.values() if isinstance(value, torch.Tensor))):
                raise FloatingPointError("nonfinite head/Adam state after update")
            epoch.update(status="COMPLETE", state_sha256=state_digest(head.state_dict()),
                         adam_step_values=_steps(optimizer, head))
            emit()
        counts["head_fits_completed"] = counts.get("head_fits_completed", 0) + 1
        record["status"] = "COMPLETE"
        emit()
    except BaseException as error:
        record.update(status="FAILED", failure=dict(type=type(error).__name__, message=str(error)),
                      interrupted_call_work_may_be_unmeasured=True)
        snapshot()
        error.fit_record = record
        error.fit_head = head
        error.fit_optimizer = optimizer
        if progress is not None:
            try:
                progress(record)
            except BaseException as progress_error:
                error.progress_error = str(progress_error)
        raise
    return head, optimizer, record
