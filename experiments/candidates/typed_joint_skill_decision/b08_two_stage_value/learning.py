"""One fixed whole-menu fit; importing this module performs no fit.

Callbacks each receive one detached record dictionary. Checkpoint state tensors
and predictions are fresh copies: callback writes cannot mutate the learner or
later checkpoints. No checkpoint selection or early stopping is provided.
"""
from copy import deepcopy
from time import process_time

import numpy as np
import torch

from . import model
from .features import SHAPES

WORLDS, EPOCHS, BATCH_SIZE, UPDATES = 128, 256, 16, 2048
CHECKPOINT_INTERVAL = 256


def pairwise_loss(scores, q2, valid):
    """FP64 pair differences, uniform world weights, singleton loss zero."""
    if (scores.dtype != torch.float32 or scores.device.type != "cpu"
            or scores.ndim != 2 or scores.shape[1] != 8
            or q2.dtype != torch.float64 or q2.device.type != "cpu" or q2.shape != scores.shape
            or valid.dtype != torch.bool or valid.device.type != "cpu" or valid.shape != scores.shape
            or not valid[:, 0].all() or (valid[:, 1:] & ~valid[:, :-1]).any()):
        raise ValueError("FP32 scores, FP64 labels and nonempty prefix validity required")
    losses = []
    for row in range(scores.shape[0]):
        indices = torch.triu_indices(int(valid[row].sum()), int(valid[row].sum()), offset=1)
        values = scores[row].double()
        if indices.shape[1] == 0:
            # Retain the singleton and a differentiable zero, no padded access.
            losses.append(values[0] * 0.)
        else:
            i, j = indices
            residual = (values[i] - values[j]) - (100. * (q2[row, i] - q2[row, j]) / 460.)
            losses.append(residual.square().mean())
    return torch.stack(losses).mean()


def epoch_batches(permutation_seed):
    """256 complete independent RandomState shuffles, eight batches each."""
    rng = np.random.RandomState(permutation_seed)
    for epoch in range(1, EPOCHS + 1):
        order = rng.permutation(WORLDS)
        for begin in range(0, WORLDS, BATCH_SIZE):
            yield epoch, order[begin:begin + BATCH_SIZE].copy()


def _validate_bank(feature_bank, q2, world_ids):
    if set(feature_bank) != {*SHAPES, "valid"}:
        raise ValueError("exact B08 feature bank required")
    result = {}
    for key, shape in {**SHAPES, "valid": (8,)}.items():
        value = feature_bank[key]
        dtype = torch.bool if key == "valid" else torch.float32
        if isinstance(value, torch.Tensor):
            if value.dtype != dtype or value.device.type != "cpu":
                raise ValueError(f"bank dtype/device differs: {key}")
            result[key] = value.detach().clone().contiguous()
        else:
            array = np.asarray(value)
            if array.dtype != (np.bool_ if key == "valid" else np.float32):
                raise ValueError(f"bank dtype differs: {key}")
            result[key] = torch.from_numpy(np.array(array, copy=True, order="C"))
        if tuple(result[key].shape) != (WORLDS, *shape):
            raise ValueError("exactly128 whole padded menus required")
    for begin in range(0, WORLDS, BATCH_SIZE):
        model.validate_inputs({k: v[begin:begin + BATCH_SIZE] for k, v in result.items()})
    labels = np.asarray(q2)
    if labels.dtype != np.float64 or labels.shape != (WORLDS, 8):
        raise ValueError("original FP64 q2[128,8] required")
    if not np.isfinite(labels[result["valid"].numpy()]).all():
        raise ValueError("nonfinite valid Q2 label")
    ids = list(world_ids)
    if len(ids) != WORLDS or len(set(ids)) != WORLDS:
        raise ValueError("128 distinct world identities required")
    return result, torch.from_numpy(np.array(labels, copy=True, order="C")), ids


def predict_menus(module, bank):
    """One B=1 call per saved world; keep all eight prediction bits."""
    predictions = np.empty((WORLDS, 8), dtype=np.float32)
    with torch.no_grad():
        for i in range(WORLDS):
            predictions[i] = module({k: v[i:i + 1] for k, v in bank.items()})[0].numpy()
    if not np.isfinite(predictions).all():
        raise FloatingPointError("nonfinite saved predictions")
    return predictions


def fit(feature_bank, q2, world_ids, *, init_seed, permutation_seed, on_checkpoint, on_update):
    """Exactly2048 Adam updates; return final state and metadata.

    ``fit_id`` is the caller-supplied init/permutation seed pair, not a new RNG
    address. Every callback retains fixed bank world order plus its batch IDs.
    Final metadata separates checkpoint_work_cpu_seconds (clone, predictions,
    movement, record construction and persistence callback) from
    update_callback_cpu_seconds (only the update callback). Their timed scopes
    never overlap. The caller can subtract both from its measured fit CPU;
    record identities, counters and forward-query exposure are unchanged.
    """
    bank, labels, ids = _validate_bank(feature_bank, q2, world_ids)
    module = model.build(init_seed)
    initial = model.clone_state(module)
    optimizer = torch.optim.Adam(module.parameters(), lr=.001, betas=(.9, .999),
                                 eps=1e-8, weight_decay=0.)
    counts = bank["valid"].sum(dim=1).numpy().astype(np.int64)
    pair_counts = counts * (counts - 1) // 2
    world_exposure = np.zeros(WORLDS, dtype=np.int64)
    updates, candidate_exposure, pair_exposure = 0, 0, 0
    checkpoint_work_cpu_seconds, update_callback_cpu_seconds = 0., 0.
    identity = {"fit_id": {"init_seed": int(init_seed), "permutation_seed": int(permutation_seed)},
                "init_seed": int(init_seed), "permutation_seed": int(permutation_seed),
                "world_ids": ids, "epochs": EPOCHS, "batch_size": BATCH_SIZE,
                "scheduled_updates": UPDATES}

    def metadata():
        return {**deepcopy(identity), "update": updates, "optimizer_counter": updates,
                "world_exposure": world_exposure.tolist(), "menu_presentations": int(world_exposure.sum()),
                "candidate_presentations": candidate_exposure, "pair_presentations": pair_exposure}

    def checkpoint():
        nonlocal checkpoint_work_cpu_seconds
        started = process_time()
        try:
            state = model.clone_state(module)
            record = {**metadata(), "state": state, "predictions": predict_menus(module, bank),
                      "valid": bank["valid"].numpy().copy(),
                      "parameter_movement": model.parameter_movement(initial, state)}
            on_checkpoint(record)
        finally:
            checkpoint_work_cpu_seconds += process_time() - started

    checkpoint()
    for epoch, indices in epoch_batches(permutation_seed):
        optimizer.zero_grad(set_to_none=True)
        scores = module({k: v[indices] for k, v in bank.items()})
        loss = pairwise_loss(scores, labels[indices], bank["valid"][indices])
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite whole-menu loss before update")
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(module.parameters(), 1., error_if_nonfinite=True)
        if not torch.isfinite(norm):
            raise FloatingPointError("nonfinite gradient norm before update")
        optimizer.step()
        updates += 1
        steps = [int(value["step"].item()) for value in optimizer.state.values() if "step" in value]
        if len(steps) != len(model.STATE_SHAPES) or any(step != updates for step in steps):
            raise RuntimeError("optimizer counter differs from declared update")
        if any(not torch.isfinite(p).all() for p in module.parameters()):
            raise FloatingPointError("nonfinite parameters after update")
        world_exposure[indices] += 1
        candidate_exposure += int(counts[indices].sum())
        pair_exposure += int(pair_counts[indices].sum())
        record = {**metadata(), "epoch": epoch, "batch_world_ids": [ids[i] for i in indices],
                  "batch_indices": indices.tolist(), "valid_candidates": counts[indices].tolist(),
                  "valid_pairs": pair_counts[indices].tolist(), "loss": float(loss.detach()),
                  "gradient_norm_before_clip": float(norm), "finite_loss": True,
                  "finite_gradient": True, "actual_optimizer_steps": steps}
        started = process_time()
        try:
            on_update(record)
        finally:
            update_callback_cpu_seconds += process_time() - started
        if updates % CHECKPOINT_INTERVAL == 0:
            checkpoint()
    if updates != UPDATES or not np.all(world_exposure == EPOCHS):
        raise RuntimeError("fixed whole-world update/exposure schedule incomplete")
    final = model.clone_state(module)
    return {"state": final, "metadata": {
        **metadata(), "parameter_movement": model.parameter_movement(initial, final),
        "checkpoint_work_cpu_seconds": checkpoint_work_cpu_seconds,
        "update_callback_cpu_seconds": update_callback_cpu_seconds}}
