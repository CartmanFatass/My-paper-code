"""Static N5 continuation with B06 ordering and the shared FP64 soft CE."""
import hashlib
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_copy, state_digest, movement
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import FROZEN as B06_FROZEN, array_digest
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import CountStudent, _finite, _steps
from .targets import MASS_ATOL, soft_cross_entropy


_SHAPES = {
    "count_weight": (128,), "network.0.weight": (128, 114), "network.0.bias": (128,),
    "network.2.weight": (128, 128), "network.2.bias": (128,),
    "network.4.weight": (27, 128), "network.4.bias": (27,),
}


def _validate_actor_adam(model, optimizer, protocol, prior_steps):
    if not isinstance(model, CountStudent) or not isinstance(optimizer, torch.optim.Adam):
        raise ValueError("CountStudent and continuing Adam required")
    named = dict(model.named_parameters())
    if (set(named) != set(_SHAPES) or set(model.state_dict()) != set(_SHAPES)
            or any(tuple(named[k].shape) != shape for k, shape in _SHAPES.items())
            or sum(p.numel() for p in named.values()) != 34843):
        raise ValueError("exact 34843-parameter count actor required")
    params = list(model.parameters())
    owned = [p for group in optimizer.param_groups for p in group["params"]]
    if len(optimizer.param_groups) != 1 or len(owned) != len(params) or set(owned) != set(params):
        raise ValueError("one Adam group must own exactly all actor parameters")
    options = dict(lr=protocol.learning_rate, betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False, maximize=False,
                   capturable=False, differentiable=False, decoupled_weight_decay=False)
    if any(optimizer.param_groups[0].get(key) != value for key, value in options.items()):
        raise ValueError("Adam configuration differs from fixed continuation")
    _finite(model, optimizer)
    if set(optimizer.state) - set(params) or prior_steps == 0 and optimizer.state:
        raise AssertionError("Adam is not fresh or contains foreign state")
    for p in params:
        entry = optimizer.state.get(p, {})
        if prior_steps:
            if set(entry) != {"step", "exp_avg", "exp_avg_sq"}:
                raise AssertionError("Adam was reset or has invalid moments")
            step = entry["step"]
            if (not isinstance(step, torch.Tensor) or step.shape != () or step.device.type != "cpu"
                    or step.dtype != torch.float32 or float(step) != prior_steps):
                raise AssertionError("Adam was reset or phases were skipped/repeated")
            for key in ("exp_avg", "exp_avg_sq"):
                if (entry[key].shape != p.shape or entry[key].dtype != torch.float32
                        or entry[key].device.type != "cpu"):
                    raise ValueError("Adam moment shape/dtype changed")
    if _steps(model, optimizer) != [prior_steps] * len(params):
        raise AssertionError("Adam was reset or phases were skipped/repeated")
    if torch.count_nonzero(model.count_weight):
        raise ValueError("N5 count branch must start and remain zero")
    if any(torch.count_nonzero(optimizer.state.get(model.count_weight, {}).get(
            key, torch.zeros((), dtype=torch.float32))) for key in ("exp_avg", "exp_avg_sq")):
        raise ValueError("N5 count branch Adam moments must remain zero")
    return params


def train_phase(model, optimizer, features, targets, phase, counts, *, protocol=B06_FROZEN,
                shuffle_root=29514101, progress=None):
    """Return a phase record; concatenate its epochs across the three phase calls.

    All stream diagnostics use paid pre-update minibatch forwards. Accuracy and
    confusion refer to target modes, not C labels. No endpoint forward is made.
    ``progress(phase, epoch_row)`` runs once per completed epoch. Failure retains
    ``error.phase_record`` and actual caller counters, including attempted row
    presentations charged before a forward (as in the B06 reference).
    """
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    protocol.validate()
    if type(phase) is not int or phase not in (0, 1, 2) or type(shuffle_root) is not int or shuffle_root < 0:
        raise ValueError("phase0..2 and nonnegative integer shuffle root required")
    if progress is not None and not callable(progress):
        raise ValueError("progress must be a completed-epoch callback")
    sizes = protocol.expected()["datasets"]
    if (len(sizes) != 3 or type(protocol.batch_size) is not int or protocol.batch_size <= 0
            or any(type(n) is not int or n <= 0 or n % protocol.batch_size for n in sizes)
            or len(protocol.epochs) != 3 or any(type(e) is not int or e <= 0 for e in protocol.epochs)):
        raise ValueError("three positive complete-batch phases required")
    if (not isinstance(features, np.ndarray) or features.dtype != np.float32
            or features.shape != (sizes[phase], 114) or not np.isfinite(features).all()):
        raise ValueError("phase requires finite NumPy FP32 features Nx114")
    if (not isinstance(targets, np.ndarray) or targets.dtype != np.float64
            or targets.shape != (sizes[phase], 27) or not np.isfinite(targets).all()
            or np.any(targets < 0.) or np.any(np.abs(targets.sum(axis=1, dtype=np.float64) - 1.) > MASS_ATOL)):
        raise ValueError("phase requires normalized nonnegative NumPy FP64 targets Nx27")
    for key in ("optimizer_steps", "sample_presentations"):
        if type(counts.get(key, 0)) is not int or counts.get(key, 0) < 0:
            raise ValueError("invalid training counter: " + key)
    prior_steps = sum(sizes[p] // protocol.batch_size * protocol.epochs[p] for p in range(phase))
    params = _validate_actor_adam(model, optimizer, protocol, prior_steps)
    x, y = np.ascontiguousarray(features), np.ascontiguousarray(targets)
    n = np.full(len(x), 5, dtype=np.int64)
    before = state_copy(model)
    x_t, y_t, n_t = torch.from_numpy(x), torch.from_numpy(y), torch.from_numpy(n)
    modes = np.argmax(y, axis=1)
    epochs, all_order = [], hashlib.sha256()
    record = dict(phase=phase, status="INCOMPLETE", examples=len(x), epochs=epochs,
                  optimizer_steps=0, sample_presentations=0, data_sha256=array_digest(x, y, n),
                  targets_sha256=array_digest(y), features_sha256=array_digest(x),
                  before_sha256=state_digest(before), shuffle_root=shuffle_root,
                  count_counts={str(k): len(x) if k == 5 else 0 for k in range(3, 8)},
                  target_mode_counts=np.bincount(modes, minlength=27).tolist(),
                  label_metric_scope="target-mode accuracy/confusion from paid pre-update forwards; no frozen-endpoint data pass",
                  loss_kernel="CPU FP32 logits cast to FP64 log_softmax; FP64 targets; mean row soft CE")

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
            row = dict(epoch=epoch, status="INCOMPLETE", updates=0, sample_presentations=0, stream_rows=0,
                       shuffle_sha256=hashlib.sha256(order_bytes).hexdigest(), zero_gradient_updates=0,
                       nonzero_gradient_updates=0, count_zero_gradient_updates=0, count_nonzero_gradient_updates=0,
                       max_gradient_norm_before_clip=0., max_count_gradient_norm_before_clip=0.)
            epochs.append(row)
            loss_sum = 0.
            for first in range(0, len(order), protocol.batch_size):
                indices = torch.from_numpy(order[first:first + protocol.batch_size])
                if len(indices) != protocol.batch_size:
                    raise AssertionError("no partial batch is authorized")
                optimizer.zero_grad(set_to_none=True)
                counts["sample_presentations"] = counts.get("sample_presentations", 0) + len(indices)
                record["sample_presentations"] += len(indices)
                row["sample_presentations"] += len(indices)
                logits = model(x_t[indices], n_t[indices])
                loss = soft_cross_entropy(logits, y_t[indices])
                truth, predicted = modes[indices.numpy()], logits.detach().argmax(-1).numpy()
                np.add.at(confusion, (truth, predicted), 1)
                loss_sum += float(loss.detach()) * len(indices)
                stream_rows = int(confusion.sum())
                row.update(stream_rows=stream_rows, stream_cross_entropy=loss_sum / stream_rows,
                           stream_target_mode_accuracy=float(np.trace(confusion) / stream_rows))
                loss.backward()
                count_norm = torch.linalg.vector_norm(model.count_weight.grad)
                norm = torch.nn.utils.clip_grad_norm_(params, protocol.grad_norm, error_if_nonfinite=True)
                if count_norm != 0:
                    raise AssertionError("N5 count gradient must remain zero")
                row["max_gradient_norm_before_clip"] = max(row["max_gradient_norm_before_clip"], float(norm))
                row["max_count_gradient_norm_before_clip"] = max(row["max_count_gradient_norm_before_clip"], float(count_norm))
                row["zero_gradient_updates" if norm == 0 else "nonzero_gradient_updates"] += 1
                row["count_zero_gradient_updates" if count_norm == 0 else "count_nonzero_gradient_updates"] += 1
                optimizer.step()
                counts["optimizer_steps"] = counts.get("optimizer_steps", 0) + 1
                record["optimizer_steps"] += 1
                row["updates"] += 1
                _finite(model, optimizer)
                if torch.count_nonzero(model.count_weight):
                    raise AssertionError("N5 count branch changed")
            row.update(status="COMPLETE", stream_cross_entropy=loss_sum / len(x),
                       stream_target_mode_accuracy=float(np.trace(confusion) / len(x)),
                       state_sha256=state_digest(model.state_dict()), adam_step_values=_steps(model, optimizer),
                       count_branch_movement=movement({"count_weight": before["count_weight"]},
                                                      {"count_weight": model.count_weight.detach()}))
            if epoch + 1 == protocol.epochs[phase]:
                row["stream_target_mode_confusion"] = confusion.tolist()
            if progress is not None:
                progress(phase, row)
        model.eval()
        if _steps(model, optimizer) != [prior_steps + record["optimizer_steps"]] * len(params):
            raise AssertionError("Adam did not update every parameter")
        record.update(status="COMPLETE", unique_feature_rows=len(np.unique(x, axis=0)))
        snapshot()
    except BaseException as error:
        if epochs and epochs[-1]["status"] != "COMPLETE":
            epochs[-1]["stream_target_mode_confusion"] = confusion.tolist()
        record.update(status="FAILED", failure=dict(type=type(error).__name__, message=str(error)),
                      interrupted_call_work_may_be_unmeasured=True)
        snapshot()
        error.phase_record = record
        raise
    return record
