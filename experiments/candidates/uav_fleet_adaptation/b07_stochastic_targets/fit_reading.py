"""Saved phase identities/optimizer states and the paid full endpoint pass."""
import hashlib
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import movement, state_copy, state_digest
from experiments.candidates.uav_fleet_adaptation.b06_count_development.audit import _equal, _require
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import FROZEN as OLD_PROTOCOL
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import make_inherited
from experiments.candidates.uav_local_history.b01.study import file_identity
from .assets import checked_path
from .audit import forward_one, probability_reference
from .contract import FITS, FROZEN, INPUT_MANIFEST_SHA256, array_digest


def equal_tree(actual, expected, name):
    if isinstance(expected, dict):
        _require(isinstance(actual, dict) and set(actual) == set(expected), name + " keys")
        for key, value in expected.items():
            equal_tree(actual[key], value, name + "/" + str(key))
    elif isinstance(expected, (list, tuple)):
        _require(isinstance(actual, (list, tuple)) and len(actual) == len(expected), name + " length")
        for i, (a, b) in enumerate(zip(actual, expected)):
            equal_tree(a, b, name + "/" + str(i))
    elif isinstance(expected, float):
        _require(isinstance(actual, (float, int)) and np.isfinite(actual)
                 and abs(actual - expected) <= 1e-12, name)
    else:
        _require(actual == expected, name)


def _optimizer(saved, model, steps):
    value = saved["optimizer"]
    _require(set(value) == {"state", "param_groups"} and len(value["param_groups"]) == 1, "saved Adam schema")
    group = value["param_groups"][0]
    expected = dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                    amsgrad=False, foreach=False, fused=False, maximize=False, capturable=False, differentiable=False,
                    decoupled_weight_decay=False)
    for key, desired in expected.items():
        _require(group[key] == desired, "saved Adam option " + key)
    parameters = list(model.named_parameters())
    identities = group["params"]
    _require(identities == list(range(7)) and len(parameters) == 7
             and set(value["state"]) == set(identities), "saved Adam ownership")
    for index, (name, parameter) in zip(identities, parameters):
        state = value["state"][index]
        _require(set(state) == {"step", "exp_avg", "exp_avg_sq"}, "saved Adam moments")
        for key, tensor in state.items():
            shape = () if key == "step" else parameter.shape
            _require(isinstance(tensor, torch.Tensor) and tensor.device.type == "cpu"
                     and tensor.dtype == torch.float32 and tensor.shape == shape and torch.isfinite(tensor).all(),
                     "saved Adam tensor " + key)
        _require(float(state["step"]) == steps, "saved per-parameter Adam step")
        _require(torch.all(state["exp_avg_sq"] >= 0), "saved Adam squared moment")
        if name == "count_weight":
            _require(torch.count_nonzero(state["exp_avg"]) == 0 and torch.count_nonzero(state["exp_avg_sq"]) == 0,
                     "saved zero-count moments")


def check_fits(out, batch, manifest, parent_state, dataset, targets):
    """Verify every saved phase/epoch, without replaying an optimizer forward."""
    expected_order = [(arm, phase) for arm in FITS for phase in range(3)]
    _require([(c["arm"], c["phase"]) for c in batch["checkpoints"]] == expected_order, "all six phase checkpoints")
    _require([f["arm"] for f in batch["fits"]] == list(FITS), "both final fits")
    models, readings = {}, []
    for arm, fit in zip(FITS, batch["fits"]):
        initial = make_inherited(parent_state, FROZEN.actor_constructor_seed)
        original, previous = state_copy(initial), state_copy(initial)
        initial_sha = state_digest(original)
        _require(fit["initial_state_sha256"] == initial_sha == batch["initial_state_sha256"], "same inherited initialization")
        _require(len(fit["phases"]) == 3, "three continuing phases")
        fit_updates = fit_presentations = 0
        for phase, size in enumerate(FROZEN.expected()["datasets"]):
            record = fit["phases"][phase]
            binding = next(c for c in batch["checkpoints"] if (c["arm"], c["phase"]) == (arm, phase))
            equal_tree(record, binding["training_record"], "phase record/checkpoint binding")
            x, target = dataset[0][:size], targets[arm][:size]
            n = np.full(size, 5, dtype=np.int64)
            _require(record["status"] == "COMPLETE" and record["phase"] == phase and record["examples"] == size,
                     "complete phase identity")
            _require(record["before_sha256"] == state_digest(previous), "continuing actor identity")
            _require(record["features_sha256"] == array_digest(x) and record["targets_sha256"] == array_digest(target)
                     and record["data_sha256"] == array_digest(x, target, n), "complete static target row identity")
            _require(record["shuffle_root"] == FROZEN.shuffle_root and record["parameters_finite"] is True,
                     "phase shuffle/finite record")
            _require(record["count_counts"] == {str(k): size if k == 5 else 0 for k in range(3, 8)}, "N5-only fit")
            modes = np.argmax(target, axis=1)
            _equal(record["target_mode_counts"], np.bincount(modes, minlength=27), "target-mode counts")
            _require(record["unique_feature_rows"] == len(np.unique(x, axis=0)), "unique feature count")
            expected_epochs = OLD_PROTOCOL.epochs[phase]
            _require(len(record["epochs"]) == expected_epochs, "complete epoch trace")
            digest = hashlib.sha256()
            per_epoch = size // 512
            for epoch, erow in enumerate(record["epochs"]):
                order = np.random.default_rng(np.random.SeedSequence([FROZEN.shuffle_root, phase, epoch])).permutation(size)
                blob = order.astype("<i8", copy=False).tobytes()
                digest.update(blob)
                steps = fit_updates + (epoch + 1) * per_epoch
                _require(erow["epoch"] == epoch and erow["status"] == "COMPLETE"
                         and erow["updates"] == per_epoch and erow["sample_presentations"] == size
                         and erow["stream_rows"] == size and erow["shuffle_sha256"] == hashlib.sha256(blob).hexdigest()
                         and erow["adam_step_values"] == [steps] * 7, "complete original-ordered epoch exposure")
                _require(erow["zero_gradient_updates"] + erow["nonzero_gradient_updates"] == per_epoch
                         and erow["count_zero_gradient_updates"] == per_epoch
                         and erow["count_nonzero_gradient_updates"] == 0
                         and erow["max_count_gradient_norm_before_clip"] == 0., "gradient activation counters")
                _require(np.isfinite(erow["stream_cross_entropy"]) and erow["stream_cross_entropy"] >= 0
                         and 0 <= erow["stream_target_mode_accuracy"] <= 1
                         and np.isfinite(erow["max_gradient_norm_before_clip"])
                         and erow["max_gradient_norm_before_clip"] >= 0, "stream diagnostics range")
                equal_tree(erow["count_branch_movement"], movement({"count_weight": previous["count_weight"]},
                                                                  {"count_weight": previous["count_weight"]}),
                           "epoch count-zero movement")
                if epoch + 1 == expected_epochs:
                    confusion = np.asarray(erow["stream_target_mode_confusion"])
                    _require(confusion.shape == (27, 27) and np.issubdtype(confusion.dtype, np.integer)
                             and np.all(confusion >= 0) and int(confusion.sum()) == size, "last paid stream confusion")
                    _equal(confusion.sum(axis=1), np.bincount(modes, minlength=27), "stream target-mode totals")
                    _equal(erow["stream_target_mode_accuracy"], float(np.trace(confusion) / size), "stream accuracy")
                else:
                    _require("stream_target_mode_confusion" not in erow, "original confusion-save cadence")
            updates, presentations = expected_epochs * per_epoch, expected_epochs * size
            _require(record["optimizer_steps"] == updates and record["sample_presentations"] == presentations,
                     "phase cost")
            _require(record["all_shuffle_sha256"] == digest.hexdigest()
                     == manifest["fit"]["phases"][phase]["all_shuffle_sha256"], "same paid F0 shuffle exposure")
            fit_updates += updates
            fit_presentations += presentations
            saved = torch.load(checked_path(out, binding["path"], binding), map_location="cpu", weights_only=True)
            _require(saved["schema"] == "uav_fleet_adaptation.b07.full_actor.v1"
                     and saved["endpoint"] == arm and saved["phase"] == phase
                     and saved["launch_sha"] == batch["launch_sha"] and saved["protocol"] == FROZEN.to_dict()
                     and saved["input_manifest_sha256"] == INPUT_MANIFEST_SHA256
                     and saved["initial_state_sha256"] == initial_sha
                     and saved["targets_sha256"] == record["targets_sha256"], "new checkpoint source binding")
            model = make_inherited(parent_state, FROZEN.actor_constructor_seed)
            state = saved["state_dict"]
            _require(set(state) == set(original), "new actor tensor roster")
            for name, tensor in state.items():
                _require(tensor.shape == original[name].shape and tensor.dtype == torch.float32
                         and tensor.device.type == "cpu" and torch.isfinite(tensor).all(), "new actor tensor " + name)
            model.load_state_dict(state, strict=True)
            _require(torch.count_nonzero(model.count_weight) == 0, "zero count branch at every phase")
            digest_state = state_digest(state)
            _require(saved["state_sha256"] == binding["state_sha256"] == record["after_sha256"]
                     == record["epochs"][-1]["state_sha256"] == digest_state, "complete phase tensor identity")
            _require(saved["parameters"] == 34843 and saved["architecture"] == [114, 128, 128, 27]
                     and saved["activation"] == "relu" and saved["dtype"] == "float32"
                     and saved["optimizer_steps"] == binding["optimizer_steps"] == fit_updates
                     and saved["adam_step_values"] == record["adam_step_values"] == [fit_updates] * 7,
                     "saved architecture/optimizer steps")
            _optimizer(saved, model, fit_updates)
            equal_tree(record["movement"], movement(previous, state), "phase movement")
            equal_tree(record["count_branch_movement"], movement({"count_weight": previous["count_weight"]},
                                                                {"count_weight": state["count_weight"]}), "phase count movement")
            previous = state_copy(model)
        _require(fit_updates == 8000 and fit_presentations == 4096000, "complete static fit exposure")
        _require(fit["final_state_sha256"] == state_digest(previous) and fit["count_branch_l2"] == 0.
                 and fit["count_branch_changed"] == 0, "final fit identity")
        equal_tree(fit["movement"], movement(original, previous), "whole-fit movement")
        models[arm] = model.eval().requires_grad_(False)
        readings.append(dict(arm=arm, phases=3, epochs=70, optimizer_steps=fit_updates,
                             sample_presentations=fit_presentations, initial_state_sha256=initial_sha,
                             final_state_sha256=state_digest(previous), movement=fit["movement"],
                             scope="saved weights/Adam tensors, fixed row/shuffle identities and complete paid trace; no optimizer replay"))
    return models, readings


ENDPOINT_STATS = ("soft_CE_T", "soft_CE_H", "KL_T", "KL_H", "TV_T", "TV_H", "TV_P0", "entropy",
                  "mode_equals_T", "mode_equals_H", "mode_equals_C", "mode_equals_P0", "local_proxy")


def endpoint_reading(out, arm, actor, dataset, targets, scores, counts):
    wall, cpu = time.perf_counter(), time.process_time()
    x, labels, _ = dataset
    logits = np.empty((len(x), 27), dtype=np.float32)
    statistics = np.empty((len(x), len(ENDPOINT_STATS)), dtype=np.float64)
    for index, features in enumerate(x):
        z = forward_one(actor, features, counts)
        counts["endpoint_rows"] += 1
        logits[index] = z
        p = probability_reference(z)
        shifted = z.astype(np.float64) - np.max(z.astype(np.float64))
        logp = shifted - np.log(np.sum(np.exp(shifted), dtype=np.float64))
        t, h, parent = targets["T"][index], targets["H"][index], targets["parent_probabilities"][index]
        ce = [float(-np.sum(q * logp)) for q in (t, h)]
        kl = [float(np.sum(q[q > 0] * (np.log(q[q > 0]) - logp[q > 0]))) for q in (t, h)]
        mode = int(np.argmax(z))
        statistics[index] = [*ce, *kl, *(float(.5 * np.abs(p - q).sum()) for q in (t, h, parent)),
                             float(-np.sum(p[p > 0] * np.log(p[p > 0]))),
                             mode == np.argmax(t), mode == np.argmax(h), mode == labels[index],
                             mode == np.argmax(parent), float(p @ scores[index])]
    path = Path(out) / "diagnostics" / f"{arm}_endpoint.npz"
    if path.exists():
        raise FileExistsError("full endpoint pass already has an artifact")
    np.savez_compressed(path, logits=logits, statistics=statistics)
    binding = file_identity(path)
    binding["path"] = str(path.relative_to(out))
    return dict(arm=arm, rows=len(x), artifact=binding, columns=list(ENDPOINT_STATS),
                logits_sha256=array_digest(logits), statistics_sha256=array_digest(statistics),
                metrics={name: dict(mean=float(statistics[:, i].mean()), min=float(statistics[:, i].min()),
                                    max=float(statistics[:, i].max()),
                                    quantiles=np.quantile(statistics[:, i], [0, .1, .5, .9, 1]).tolist())
                         for i, name in enumerate(ENDPOINT_STATS)},
                cpu_seconds=time.process_time() - cpu, wall_seconds=time.perf_counter() - wall,
                scope="one frozen one-row forward on each of all 81920 training rows; exact decoded law/FP64 CE/proxy, "
                      "not held-out generalization or a new native rollout")
