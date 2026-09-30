"""Fixed 114-input categorical student and one continuing Adam lineage."""
from __future__ import annotations

import copy
import hashlib
import time

import numpy as np
import torch
from torch import nn

from .contract import Protocol, array_digest


class Student(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(114, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU(), nn.Linear(128, 27),
        )

    def forward(self, features):
        if features.shape[-1] != 114:
            raise ValueError("student input must have 114 lawful features")
        return self.network(features)


def make_student(seed):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed))
        model = Student().cpu().float()
    if sum(p.numel() for p in model.parameters()) != 34715:
        raise AssertionError("actor parameter contract changed")
    return model


def make_optimizer(model, protocol: Protocol):
    return torch.optim.Adam(
        model.parameters(), lr=protocol.learning_rate, betas=(.9, .999), eps=1e-8,
        weight_decay=0, amsgrad=False, foreach=False, fused=False,
    )


def state_copy(model):
    return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}


def state_digest(state):
    digest = hashlib.sha256()
    for key in sorted(state):
        value = state[key].detach().cpu().contiguous().numpy()
        digest.update(key.encode("utf-8"))
        digest.update(array_digest(value).encode("ascii"))
    return digest.hexdigest()


def movement(before, after):
    delta = torch.cat([(after[k].double() - before[k].double()).reshape(-1) for k in sorted(before)])
    return {"l2": float(torch.linalg.vector_norm(delta)), "max_abs": float(delta.abs().max()),
            "changed_parameters": int(torch.count_nonzero(delta)), "parameters": delta.numel()}


def train_phase(model, optimizer, features, labels, phase, protocol, counts, progress=None):
    """No validation selection, extra forwards, dropped batches, or optimizer resets."""
    protocol.validate()
    expected = protocol.expected()
    x = np.ascontiguousarray(features, dtype=np.float32)
    y = np.ascontiguousarray(labels, dtype=np.int64)
    if x.shape != (expected["datasets"][phase], 114) or y.shape != (len(x),):
        raise ValueError("accumulated data disagrees with the fixed phase")
    if not np.isfinite(x).all() or np.any((y < 0) | (y >= 27)):
        raise ValueError("invalid supervised inputs/labels")
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    before = state_copy(model)
    x_t, y_t = torch.from_numpy(x), torch.from_numpy(y)
    epochs = []
    all_order = hashlib.sha256()
    model.train()
    for epoch in range(protocol.epochs[phase]):
        order = np.random.default_rng(np.random.SeedSequence(
            [protocol.shuffle_root, phase, epoch])).permutation(len(x))
        all_order.update(order.astype("<i8", copy=False).tobytes())
        confusion = np.zeros((27, 27), dtype=np.int64)
        loss_sum = 0.0
        max_grad = 0.0
        epoch_updates = 0
        for first in range(0, len(order), protocol.batch_size):
            indices = torch.from_numpy(order[first:first + protocol.batch_size])
            if indices.numel() != protocol.batch_size:
                raise AssertionError("no partial batch is authorized")
            optimizer.zero_grad(set_to_none=True)
            logits = model(x_t[indices])
            loss = nn.functional.cross_entropy(logits, y_t[indices], reduction="mean")
            if not torch.isfinite(loss):
                raise FloatingPointError("nonfinite supervised loss")
            truth = y_t[indices].numpy()
            predicted = logits.detach().argmax(-1).numpy()
            np.add.at(confusion, (truth, predicted), 1)
            loss_sum += float(loss.detach()) * len(indices)
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), protocol.grad_norm,
                                                 error_if_nonfinite=True)
            max_grad = max(max_grad, float(norm))
            optimizer.step()
            counts["optimizer_steps"] += 1
            counts["sample_presentations"] += len(indices)
            epoch_updates += 1
        if not all(torch.isfinite(p).all() for p in model.parameters()):
            raise FloatingPointError("nonfinite learner parameters")
        row = {"epoch": epoch, "updates": epoch_updates, "sample_presentations": len(x),
               "stream_cross_entropy": loss_sum / len(x),
               "stream_accuracy": float(np.trace(confusion) / len(x)),
               "max_gradient_norm_before_clip": max_grad,
               "shuffle_sha256": hashlib.sha256(order.astype("<i8", copy=False).tobytes()).hexdigest()}
        # This is the last epoch's existing pre-update forward stream, not an
        # unpriced fixed-checkpoint re-evaluation over the accumulated labels.
        if epoch + 1 == protocol.epochs[phase]:
            row["stream_confusion"] = confusion.tolist()
        epochs.append(row)
        if progress is not None:
            progress(phase, row)
    model.eval()
    after = state_copy(model)
    steps = [int(state["step"]) for state in optimizer.state.values()]
    if not steps or any(step != counts["optimizer_steps"] for step in steps):
        raise AssertionError("Adam was reset or did not update every parameter")
    unique_features = len(np.unique(x, axis=0))
    return {
        "phase": phase, "examples": len(x), "epochs": epochs,
        "optimizer_steps": sum(row["updates"] for row in epochs),
        "sample_presentations": sum(row["sample_presentations"] for row in epochs),
        "data_sha256": array_digest(x, y), "all_shuffle_sha256": all_order.hexdigest(),
        "before_sha256": state_digest(before), "after_sha256": state_digest(after),
        "movement": movement(before, after), "adam_step_values": steps,
        "wall_seconds": time.perf_counter() - start_wall,
        "cpu_seconds": time.process_time() - start_cpu,
        "label_counts": np.bincount(y, minlength=27).tolist(),
        "unique_feature_rows": unique_features,
        "label_metric_scope": "paid optimizer forwards before each update; no frozen-endpoint data pass",
    }


def checkpoint(model, optimizer=None):
    result = {"state_dict": state_copy(model), "state_sha256": state_digest(model.state_dict()),
              "architecture": [114, 128, 128, 27], "activation": "relu", "dtype": "float32"}
    if optimizer is not None:
        result["optimizer"] = copy.deepcopy(optimizer.state_dict())
    return result
