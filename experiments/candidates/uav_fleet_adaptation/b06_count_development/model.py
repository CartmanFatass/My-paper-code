"""Inherited 114-feature Student with a zero count branch and phased CE training."""
from collections.abc import Mapping
import hashlib
import time

import numpy as np
import torch
from torch import nn

from experiments.candidates.uav_fleet_adaptation.b02.model import (
    Student, state_copy, state_digest, movement, checkpoint as original_checkpoint,
)
from .contract import array_digest


class CountStudent(Student):
    def __init__(self):
        super().__init__()
        self.count_weight = nn.Parameter(torch.zeros(128, dtype=torch.float32, device="cpu"))

    def forward(self, features, fleet_counts):
        if (not isinstance(features, torch.Tensor) or features.ndim < 1 or features.shape[-1] != 114 or
                features.dtype != torch.float32 or features.device.type != "cpu"):
            raise ValueError("features require CPU FP32 rows of width 114")
        count = torch.as_tensor(fleet_counts)
        if (count.shape != features.shape[:-1] or count.device.type != "cpu" or
                count.dtype not in (torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8)):
            raise ValueError("integer fleet counts must match the feature row shape")
        if not torch.isfinite(features).all() or ((count < 3) | (count > 7)).any():
            raise ValueError("finite features and fleet counts N3..N7 required")
        phi = (count.to(dtype=torch.float32) - 5.) / 2.
        # No zero-branch shortcut: N3/N7 must have a branch gradient at init.
        hidden = self.network[0](features) + self.count_weight * phi[..., None]
        for layer in self.network[1:]:
            hidden = layer(hidden)
        return hidden


def make_inherited(parent_state, seed):
    """Copy only original tensors from an in-memory parent; fresh zero branch."""
    if type(seed) is not int or seed < 0 or not isinstance(parent_state, Mapping):
        raise ValueError("original parent tensor mapping and integer seed required")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        model = CountStudent().cpu().float()
    expected = {key: value for key, value in model.state_dict().items() if key != "count_weight"}
    if set(parent_state) != set(expected):
        raise ValueError("parent state must contain exactly the original Student keys")
    for key, value in parent_state.items():
        if (not isinstance(value, torch.Tensor) or value.shape != expected[key].shape or
                value.dtype != torch.float32 or value.device.type != "cpu" or not torch.isfinite(value).all()):
            raise ValueError("invalid original parent tensor: " + key)
    copied = {key: value.detach().clone() for key, value in parent_state.items()}
    copied["count_weight"] = torch.zeros_like(model.count_weight)
    model.load_state_dict(copied, strict=True)
    if sum(p.numel() for p in model.parameters()) != 34843:
        raise AssertionError("count actor parameter contract changed")
    return model


def make_optimizer(model, protocol):
    protocol.validate()
    return torch.optim.Adam(model.parameters(), lr=protocol.learning_rate, betas=(.9, .999), eps=1e-8,
                            weight_decay=0, amsgrad=False, foreach=False, fused=False)


def _steps(model, optimizer):
    return [int(optimizer.state.get(p, {}).get("step", 0)) for p in model.parameters()]


def _finite(model, optimizer):
    if any(p.dtype != torch.float32 or p.device.type != "cpu" or not p.requires_grad for p in model.parameters()):
        raise ValueError("all learner parameters must remain trainable CPU FP32")
    if (any(not torch.isfinite(p).all() for p in model.parameters()) or
            any(not torch.isfinite(value).all() for entry in optimizer.state.values() for value in entry.values() if isinstance(value, torch.Tensor))):
        raise FloatingPointError("nonfinite learner/Adam state")


def train_phase(model, optimizer, features, labels, fleet_counts, phase, protocol, counts, shuffle_root, progress=None):
    """Original batch CE/order/clip program, adding count inputs and diagnostics.

    No endpoint forward or partial batch. Adam continues across all three phases.
    Failure exceptions retain ``phase_record`` and the caller's actual counters.
    ``progress(phase, epoch_row)`` retains the original completed-epoch interface.
    """
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    protocol.validate()
    if type(phase) is not int or phase not in (0, 1, 2) or type(shuffle_root) is not int or shuffle_root < 0:
        raise ValueError("phase 0..2 and nonnegative integer shuffle root required")
    if progress is not None and not callable(progress):
        raise ValueError("progress must be a completed-epoch callback")
    expected = protocol.expected()
    if len(expected["datasets"]) != 3 or any(n % protocol.batch_size for n in expected["datasets"]):
        raise ValueError("three complete-batch accumulated datasets required")
    x, y, n = np.asarray(features), np.asarray(labels), np.asarray(fleet_counts)
    if (x.shape != (expected["datasets"][phase], 114) or x.dtype != np.float32 or
            y.shape != (len(x),) or y.dtype != np.int64 or n.shape != (len(x),) or n.dtype != np.int64):
        raise ValueError("phase requires FP32 features and matching int64 labels/counts")
    if not np.isfinite(x).all() or np.any((y < 0) | (y >= 27)) or np.any((n < 3) | (n > 7)):
        raise ValueError("invalid features/labels/fleet counts")
    for key in ("optimizer_steps", "sample_presentations"):
        if type(counts.get(key, 0)) is not int or counts.get(key, 0) < 0:
            raise ValueError("invalid training counter: " + key)
    if not isinstance(model, CountStudent) or not isinstance(optimizer, torch.optim.Adam):
        raise ValueError("count actor and continuing Adam required")
    params = list(model.parameters())
    owned = [p for group in optimizer.param_groups for p in group["params"]]
    if len(owned) != len(params) or set(owned) != set(params):
        raise ValueError("optimizer must own exactly all actor parameters")
    if len(optimizer.param_groups) != 1:
        raise ValueError("one continuing Adam parameter group required")
    options = dict(lr=protocol.learning_rate, betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False, maximize=False)
    if any(optimizer.param_groups[0][key] != value for key, value in options.items()):
        raise ValueError("Adam configuration differs from the fixed continuation")
    prior_steps = sum(expected["datasets"][p] // protocol.batch_size * protocol.epochs[p] for p in range(phase))
    if _steps(model, optimizer) != [prior_steps] * len(params):
        raise AssertionError("Adam was reset or phases were skipped/repeated")
    _finite(model, optimizer)
    x, y, n = np.ascontiguousarray(x), np.ascontiguousarray(y), np.ascontiguousarray(n)
    before = state_copy(model)
    x_t, y_t, n_t = torch.from_numpy(x), torch.from_numpy(y), torch.from_numpy(n)
    epochs, all_order = [], hashlib.sha256()
    record = dict(phase=phase, status="INCOMPLETE", examples=len(x), epochs=epochs, optimizer_steps=0,
                  sample_presentations=0, data_sha256=array_digest(x, y, n), before_sha256=state_digest(before),
                  shuffle_root=shuffle_root, count_counts={str(k): int(np.count_nonzero(n == k)) for k in range(3, 8)})

    def snapshot():
        finite = all(bool(torch.isfinite(p).all()) for p in params)
        after = state_copy(model)
        record.update(after_sha256=state_digest(after), all_shuffle_sha256=all_order.hexdigest(),
                      adam_step_values=_steps(model, optimizer), parameters_finite=finite,
                      movement=movement(before, after) if finite else None,
                      count_branch_movement=movement({"count_weight": before["count_weight"]},
                                                     {"count_weight": after["count_weight"]}) if finite else None,
                      wall_seconds=time.perf_counter() - start_wall, cpu_seconds=time.process_time() - start_cpu)

    model.train()
    try:
        for epoch in range(protocol.epochs[phase]):
            order = np.random.default_rng(np.random.SeedSequence([shuffle_root, phase, epoch])).permutation(len(x))
            order_bytes = order.astype("<i8", copy=False).tobytes()
            all_order.update(order_bytes)
            confusion = np.zeros((27, 27), dtype=np.int64)
            row = dict(epoch=epoch, status="INCOMPLETE", updates=0, sample_presentations=0,
                       shuffle_sha256=hashlib.sha256(order_bytes).hexdigest(), zero_gradient_updates=0,
                       nonzero_gradient_updates=0, count_zero_gradient_updates=0, count_nonzero_gradient_updates=0,
                       max_gradient_norm_before_clip=0., max_count_gradient_norm_before_clip=0.)
            epochs.append(row)
            loss_sum = 0.
            for first in range(0, len(order), protocol.batch_size):
                indices = torch.from_numpy(order[first:first + protocol.batch_size])
                optimizer.zero_grad(set_to_none=True)
                counts["sample_presentations"] = counts.get("sample_presentations", 0) + len(indices)
                record["sample_presentations"] += len(indices)
                row["sample_presentations"] += len(indices)
                logits = model(x_t[indices], n_t[indices])
                loss = nn.functional.cross_entropy(logits, y_t[indices], reduction="mean")
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite supervised loss")
                truth, predicted = y_t[indices].numpy(), logits.detach().argmax(-1).numpy()
                np.add.at(confusion, (truth, predicted), 1)
                loss_sum += float(loss.detach()) * len(indices)
                stream_rows = int(confusion.sum())
                row.update(stream_rows=stream_rows, stream_cross_entropy=loss_sum / stream_rows,
                           stream_accuracy=float(np.trace(confusion) / stream_rows))
                loss.backward()
                count_norm = torch.linalg.vector_norm(model.count_weight.grad)
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), protocol.grad_norm, error_if_nonfinite=True)
                row["max_gradient_norm_before_clip"] = max(row["max_gradient_norm_before_clip"], float(norm))
                row["max_count_gradient_norm_before_clip"] = max(row["max_count_gradient_norm_before_clip"], float(count_norm))
                row["zero_gradient_updates" if norm == 0 else "nonzero_gradient_updates"] += 1
                row["count_zero_gradient_updates" if count_norm == 0 else "count_nonzero_gradient_updates"] += 1
                optimizer.step()
                counts["optimizer_steps"] = counts.get("optimizer_steps", 0) + 1
                record["optimizer_steps"] += 1
                row["updates"] += 1
                _finite(model, optimizer)
            row.update(status="COMPLETE", stream_cross_entropy=loss_sum / len(x),
                       stream_accuracy=float(np.trace(confusion) / len(x)), state_sha256=state_digest(model.state_dict()),
                       adam_step_values=_steps(model, optimizer),
                       count_branch_movement=movement({"count_weight": before["count_weight"]},
                                                      {"count_weight": model.count_weight.detach()}))
            if epoch + 1 == protocol.epochs[phase]:
                row["stream_confusion"] = confusion.tolist()
            if progress is not None:
                progress(phase, row)
        model.eval()
        if _steps(model, optimizer) != [prior_steps + record["optimizer_steps"]] * len(params):
            raise AssertionError("Adam did not update every parameter")
        record.update(status="COMPLETE", label_counts=np.bincount(y, minlength=27).tolist(),
                      unique_feature_rows=len(np.unique(x, axis=0)),
                      label_metric_scope="paid optimizer forwards before each update; no frozen-endpoint data pass")
        snapshot()
    except BaseException as error:
        if epochs and epochs[-1]["status"] != "COMPLETE":
            epochs[-1]["stream_confusion"] = confusion.tolist()
        record.update(status="FAILED", failure=dict(type=type(error).__name__, message=str(error)),
                      interrupted_call_work_may_be_unmeasured=True)
        snapshot()
        error.phase_record = record
        raise
    return record


def checkpoint(model, optimizer=None):
    if not isinstance(model, CountStudent):
        raise ValueError("count checkpoint requires CountStudent")
    result = original_checkpoint(model, optimizer)
    result.update(parameters=34843, count_domain=[3, 4, 5, 6, 7],
                  count_branch=dict(shape=[128], feature="(N-5)/2", placement="before first ReLU"))
    if optimizer is not None:
        steps = _steps(model, optimizer)
        if len(set(steps)) != 1:
            raise AssertionError("inconsistent checkpoint Adam steps")
        result.update(optimizer_steps=steps[0], adam_step_values=steps)
    return result
