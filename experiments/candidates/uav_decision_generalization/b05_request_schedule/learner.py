"""Fixed B05 cost Double-DQN; only cached public features and G enter here.

The runner owns exploration, environment collection, deployment deadlines and the
canonical-G initialization path. This module never evaluates G or a host model.
"""
from __future__ import annotations

import copy
import hashlib
import time
from contextlib import contextmanager

import numpy as np
import torch
from torch import nn

from .contract import FEATURE_COUNT, TORCH_INIT_SEEDS, rng_domain

CAPACITY = 32768
FIT_TRANSITIONS = 30720
WARMUP = 256
BATCH_SIZE = 128
TARGET_PERIOD = 256
SCALE = 1200.0


def _array(value, shape, dtype, name):
    if not isinstance(value, np.ndarray) or value.shape != shape or value.dtype != dtype:
        raise ValueError(f"{name} must be {dtype} {shape}")
    if not np.isfinite(value).all():
        raise ValueError(f"{name} must be finite")
    return value


def _integer(value, name, minimum=0, maximum=None):
    if (isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, np.integer)) or value < minimum
            or (maximum is not None and value > maximum)):
        raise ValueError(f"invalid {name}")
    return int(value)


def lexicographic_actions(total, raw_g):
    """Float64 cost, then unscaled canonical G, then action ID; batched or single."""
    total = np.asarray(total)
    raw_g = np.asarray(raw_g)
    if (total.dtype != np.float64 or raw_g.dtype != np.float64
            or total.shape != raw_g.shape or total.ndim not in (1, 2)
            or total.shape[-1] != 4 or not np.isfinite(total).all()
            or not np.isfinite(raw_g).all()):
        raise ValueError("finite float64 four-action costs required")
    return np.lexsort((np.broadcast_to(np.arange(4), total.shape), raw_g, total),
                      axis=-1)[..., 0]


def compose_q(raw_g, residual):
    """Frozen inference composition; canonical G is never cast to float32."""
    raw_g, residual = np.asarray(raw_g), np.asarray(residual)
    if (raw_g.dtype != np.float64 or residual.dtype != np.float32
            or raw_g.shape != residual.shape or raw_g.ndim not in (1, 2)
            or raw_g.shape[-1] != 4 or not np.isfinite(raw_g).all()
            or not np.isfinite(residual).all()):
        raise ValueError("finite float64 G and float32 four-action residuals required")
    total = raw_g / SCALE + residual.astype(np.float64)
    if not np.isfinite(total).all():
        raise FloatingPointError("nonfinite composed Q")
    return total


class ResidualScorer(nn.Module):
    """303 -> 128 ReLU -> 128 ReLU -> 1, CPU float32, exact zero head."""

    def __init__(self, seed):
        super().__init__()
        # Default Linear initialization is Torch Kaiming-uniform. Fork preserves
        # the caller's CPU RNG; this model does not own an exploration stream.
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(seed)
            self.layers = nn.Sequential(
                nn.Linear(FEATURE_COUNT, 128, device="cpu", dtype=torch.float32),
                nn.ReLU(), nn.Linear(128, 128, device="cpu", dtype=torch.float32),
                nn.ReLU(), nn.Linear(128, 1, device="cpu", dtype=torch.float32))
            nn.init.zeros_(self.layers[-1].weight)
            nn.init.zeros_(self.layers[-1].bias)
        assert sum(p.numel() for p in self.parameters()) == 55553

    def forward(self, features):
        if (features.device.type != "cpu" or features.dtype != torch.float32
                or features.ndim != 2 or features.shape[1] != FEATURE_COUNT):
            raise ValueError("CPU float32 feature rows required")
        return self.layers(features).squeeze(-1)


class Replay:
    """Fit-private, append-only cache. Terminal transitions have no next rows."""

    def __init__(self):
        self.rows = []

    def __len__(self):
        return len(self.rows)

    def append(self, features, raw_g, action, cost, next_features, next_raw_g, terminated):
        if len(self) >= CAPACITY:
            raise RuntimeError("replay capacity exceeded; overwriting is forbidden")
        _array(features, (4, FEATURE_COUNT), np.dtype("float32"), "features")
        _array(raw_g, (4,), np.dtype("float64"), "raw_g")
        action = _integer(action, "action", maximum=3)
        cost = _integer(cost, "macro cost", maximum=np.iinfo(np.int64).max)
        if not isinstance(terminated, (bool, np.bool_)):
            raise ValueError("terminated must be boolean")
        if terminated:
            if next_features is not None or next_raw_g is not None:
                raise ValueError("terminal transitions must omit next caches")
        else:
            _array(next_features, (4, FEATURE_COUNT), np.dtype("float32"), "next_features")
            _array(next_raw_g, (4,), np.dtype("float64"), "next_raw_g")
        def frozen(array):
            if array is None:
                return None
            result = array.copy()
            result.flags.writeable = False
            return result
        self.rows.append((frozen(features), frozen(raw_g), action, cost,
                          frozen(next_features), frozen(next_raw_g), bool(terminated)))

    def sample(self, sampler):
        indices = np.asarray(sampler.choice(len(self), size=BATCH_SIZE, replace=False))
        if (indices.shape != (BATCH_SIZE,) or indices.dtype.kind not in "iu"
                or len(np.unique(indices)) != BATCH_SIZE
                or np.any(indices < 0) or np.any(indices >= len(self))):
            raise ValueError("sampler must return 128 distinct valid replay indices")
        return indices, [self.rows[int(i)] for i in indices]


def _digest(value):
    """Typed recursive hash of checkpoint state, without pickle/version metadata."""
    digest = hashlib.sha256()
    def feed(item):
        if isinstance(item, torch.Tensor):
            feed(item.detach().cpu().numpy())
        elif isinstance(item, np.ndarray):
            digest.update(b"array" + item.dtype.str.encode() + repr(item.shape).encode())
            digest.update(np.ascontiguousarray(item).tobytes())
        elif isinstance(item, dict):
            digest.update(b"dict")
            for key in sorted(item, key=lambda x: (type(x).__name__, repr(x))):
                feed(key)
                feed(item[key])
        elif isinstance(item, (tuple, list)):
            digest.update(type(item).__name__.encode() + str(len(item)).encode())
            for child in item:
                feed(child)
        else:
            digest.update(type(item).__name__.encode() + repr(item).encode() + b";")
    feed(value)
    return digest.hexdigest()


class ResidualLearner:
    """One fixed fit. Failed updates quarantine this instance until checkpoint restore."""

    def __init__(self, fit_index, event_callback=None):
        wall, cpu = time.perf_counter(), time.process_time()
        self.fit_index = _integer(fit_index, "fit_index", maximum=2)
        if event_callback is not None and not callable(event_callback):
            raise ValueError("event_callback must be callable or None")
        self.event_callback = event_callback
        self._event_callback_failed = False
        self.failed = False
        self.counters = dict(transition_attempts=0, transitions=0, update_attempts=0,
                             updates=0, backward_attempts=0, backwards=0,
                             optimizer_attempts=0, optimizer_steps=0,
                             initial_target_copy_attempts=0, initial_target_copies=0,
                             target_copy_attempts=0, target_copies=0, update_failures=0)
        self.forward_counts = {}
        self.online = ResidualScorer(TORCH_INIT_SEEDS[self.fit_index])
        self.counters["initial_target_copy_attempts"] += 1
        self._emit("initial_target_copy.attempt")
        self.target = copy.deepcopy(self.online)
        self.target.requires_grad_(False)
        self.counters["initial_target_copies"] += 1
        self._emit("initial_target_copy.complete")
        self.optimizer = torch.optim.Adam(self.online.parameters(), lr=3e-4,
                                         betas=(.9, .999), eps=1e-8, weight_decay=0)
        self.initial = {k: v.detach().clone() for k, v in self.online.state_dict().items()}
        self.replay = Replay()
        self.sampler = np.random.Generator(np.random.PCG64(np.random.SeedSequence(
            rng_domain("replay", self.fit_index))))
        self.last_update = None
        self.timing = {"construction_wall_s": time.perf_counter() - wall,
                       "construction_cpu_s": time.process_time() - cpu,
                       "update_wall_s": 0., "update_cpu_s": 0.}

    def _emit(self, event):
        """Publish counted boundaries to callback(event, numeric_counts).

        Snapshots contain cumulative counters plus nested numeric ``forward``
        counts. No network/cache/checkpoint state is sent or retained. Callback
        cost is inside its enclosing construction/choose/store/update timing.
        A failing sink is quarantined and never called again by this instance.
        """
        if self._event_callback_failed:
            raise RuntimeError("event callback previously failed")
        if self.event_callback is None:
            return
        counts = {**self.counters, "forward": copy.deepcopy(self.forward_counts)}
        try:
            self.event_callback(event, counts)
        except Exception:
            self._event_callback_failed = True
            self.failed = True
            raise

    @contextmanager
    def _timed(self, name):
        wall, cpu = time.perf_counter(), time.process_time()
        try:
            yield
        finally:
            for suffix, value in (("wall_s", time.perf_counter() - wall),
                                  ("cpu_s", time.process_time() - cpu)):
                key = name + "_" + suffix
                self.timing[key] = self.timing.get(key, 0.) + value

    def _forward(self, model, features, role):
        counts = self.forward_counts.setdefault(role, dict(attempts=0, calls=0,
                                                           attempted_rows=0, rows=0))
        counts["attempts"] += 1
        counts["attempted_rows"] += len(features)
        self._emit(f"forward.{role}.attempt")
        residual = model(features)
        counts["calls"] += 1
        counts["rows"] += len(features)
        self._emit(f"forward.{role}.complete")
        if residual.shape != (len(features),) or residual.dtype != torch.float32:
            raise ValueError("scorer must return one float32 residual per row")
        if not torch.isfinite(residual).all():
            raise FloatingPointError("nonfinite residual")
        return residual

    def choose(self, features, raw_g):
        """Always score all four rows, including runner-selected exploratory steps."""
        with self._timed("choose"):
            _array(features, (4, FEATURE_COUNT), np.dtype("float32"), "features")
            _array(raw_g, (4,), np.dtype("float64"), "raw_g")
            with torch.no_grad():
                residual = self._forward(self.online, torch.from_numpy(features.copy()),
                                         "collection").numpy().copy()
            total = compose_q(raw_g, residual)
            return int(lexicographic_actions(total, raw_g)), total, residual

    def observe(self, features, raw_g, action, cost, next_features=None,
                next_raw_g=None, *, terminated):
        # Store time excludes the separately reported update; callers must not
        # add nested update time to an inclusive observe measurement.
        with self._timed("observe_store"):
            if self.failed:
                raise RuntimeError("learner has a failed update")
            if self.counters["transitions"] >= FIT_TRANSITIONS:
                raise RuntimeError("fixed fit transition allowance exhausted")
            self.counters["transition_attempts"] += 1
            self._emit("transition.attempt")
            self.replay.append(features, raw_g, action, cost, next_features, next_raw_g,
                               terminated)
            self.counters["transitions"] += 1
            self._emit("transition.complete")
        if self.counters["transitions"] <= WARMUP:
            return None
        return self._update()

    def _update(self):
        wall, cpu = time.perf_counter(), time.process_time()
        self.counters["update_attempts"] += 1
        try:
            self._emit("update.attempt")
            indices, rows = self.replay.sample(self.sampler)
            actions = np.asarray([r[2] for r in rows], dtype=np.int64)
            current = np.stack([r[0][a] for r, a in zip(rows, actions)])
            baseline = torch.from_numpy(np.asarray([r[1][a] for r, a in zip(rows, actions)]))
            prediction = baseline / SCALE + self._forward(
                self.online, torch.from_numpy(current), "update_current").double()
            with torch.no_grad():
                expected = torch.tensor([r[3] / SCALE for r in rows], dtype=torch.float64)
                live_indices = [i for i, r in enumerate(rows) if not r[6]]
                if live_indices:
                    live = [rows[i] for i in live_indices]
                    features = np.stack([r[4] for r in live])
                    raw_g = np.stack([r[5] for r in live])
                    online = self._forward(self.online, torch.from_numpy(
                        features.reshape(-1, FEATURE_COUNT)), "update_next_online")
                    total = compose_q(raw_g, online.numpy().reshape(-1, 4))
                    selected = lexicographic_actions(total, raw_g)
                    chosen_features = features[np.arange(len(live)), selected]
                    target = self._forward(self.target, torch.from_numpy(chosen_features),
                                           "update_next_target").double()
                    bootstrap = torch.from_numpy(raw_g[np.arange(len(live)), selected]) / SCALE + target
                    expected[live_indices] += bootstrap
            if not torch.isfinite(prediction).all() or not torch.isfinite(expected).all():
                raise FloatingPointError("nonfinite prediction or target")
            loss = torch.nn.functional.huber_loss(prediction, expected, reduction="mean", delta=1.)
            if not torch.isfinite(loss):
                raise FloatingPointError("nonfinite loss")
            self.optimizer.zero_grad(set_to_none=True)
            self.counters["backward_attempts"] += 1
            self._emit("backward.attempt")
            loss.backward()
            self.counters["backwards"] += 1
            self._emit("backward.complete")
            grad_norm = torch.nn.utils.clip_grad_norm_(self.online.parameters(), 10.,
                                                     error_if_nonfinite=True)
            if not torch.isfinite(grad_norm):
                raise FloatingPointError("nonfinite gradient norm")
            self.counters["optimizer_attempts"] += 1
            self._emit("optimizer.attempt")
            self.optimizer.step()
            self.counters["optimizer_steps"] += 1
            self._emit("optimizer.complete")
            self.counters["updates"] += 1
            self._emit("update.complete")
            for parameter in self.online.parameters():
                if not torch.isfinite(parameter).all():
                    raise FloatingPointError("nonfinite parameter after optimizer")
            for state in self.optimizer.state.values():
                for value in state.values():
                    if isinstance(value, torch.Tensor) and not torch.isfinite(value).all():
                        raise FloatingPointError("nonfinite optimizer state")
            if self.counters["updates"] % TARGET_PERIOD == 0:
                self.counters["target_copy_attempts"] += 1
                self._emit("target_copy.attempt")
                self.target.load_state_dict(self.online.state_dict())
                self.counters["target_copies"] += 1
                self._emit("target_copy.complete")
            self.last_update = {"loss": float(loss.detach()), "grad_norm_before_clip": float(grad_norm),
                                "grad_norm_after_clip": float(torch.linalg.vector_norm(torch.cat([
                                    p.grad.reshape(-1) for p in self.online.parameters() if p.grad is not None]))),
                                "target_mean": float(expected.mean()),
                                "prediction_mean": float(prediction.detach().mean()),
                                "nonterminal_rows": len(live_indices),
                                "sample_indices": indices.tolist(), "update": self.counters["updates"]}
            return copy.deepcopy(self.last_update)
        except Exception:
            self.counters["update_failures"] += 1
            self.failed = True
            if not self._event_callback_failed:
                self._emit("update.failure")
            raise
        finally:
            self.timing["update_wall_s"] += time.perf_counter() - wall
            self.timing["update_cpu_s"] += time.process_time() - cpu

    def _state(self):
        return {"schema": 1, "fit_index": self.fit_index,
                "init_seed": TORCH_INIT_SEEDS[self.fit_index],
                "online": self.online.state_dict(), "target": self.target.state_dict(),
                "optimizer": self.optimizer.state_dict(), "initial": self.initial,
                "replay": self.replay.rows, "sampler": self.sampler.bit_generator.state,
                "counters": self.counters, "forward_counts": self.forward_counts,
                "failed": self.failed, "last_update": self.last_update, "timing": self.timing}

    def state_dict(self):
        """Owned snapshot, including replay and sampling continuation; no file writes."""
        return copy.deepcopy(self._state())

    def deployment_state_dict(self):
        """Small frozen endpoint: online weights and identity, without replay/Adam."""
        return {"schema": 1, "fit_index": self.fit_index,
                "init_seed": TORCH_INIT_SEEDS[self.fit_index],
                "online": copy.deepcopy(self.online.state_dict()),
                "certificate": self.zero_head_certificate(),
                "counters": copy.deepcopy(self.counters)}

    def compact_training_state_dict(self):
        """Unique final optimizer/target state; replay lives in mission traces.

        Typed replay/full-state identities bind the retained canonical caches
        without writing a second copy of every current/next feature matrix.
        This record is evidence, not a restart/resume contract.
        """
        state = self._state()
        result = copy.deepcopy({key: value for key, value in state.items() if key != "replay"})
        result.update(replay_size=len(self.replay), replay_sha256=_digest(self.replay.rows),
                      full_state_sha256=_digest(state), replay_storage="canonical mission transitions")
        return result

    def load_state_dict(self, state):
        """Restore a same-fit CPU checkpoint; reject corrupt contracts before mutation."""
        if (state["schema"] != 1 or state["fit_index"] != self.fit_index
                or state["init_seed"] != TORCH_INIT_SEEDS[self.fit_index]):
            raise ValueError("checkpoint identity mismatch")
        for name in ("online", "target", "initial"):
            current = self.online.state_dict()
            if state[name].keys() != current.keys():
                raise ValueError("checkpoint parameter keys mismatch")
            for key, value in state[name].items():
                if (not isinstance(value, torch.Tensor) or value.dtype != torch.float32
                        or value.device.type != "cpu" or value.shape != current[key].shape
                        or not torch.isfinite(value).all()):
                    raise ValueError("invalid checkpoint parameter")
        if _digest(state["initial"]) != _digest(self.initial):
            raise ValueError("checkpoint initialization mismatch")
        replay = Replay()
        for row in state["replay"]:
            replay.append(*row)
        counters = state["counters"]
        if counters.keys() != self.counters.keys():
            raise ValueError("invalid checkpoint counters")
        for name, value in counters.items():
            _integer(value, name)
        if counters["transitions"] != len(replay) or len(replay) > FIT_TRANSITIONS:
            raise ValueError("checkpoint replay/transition mismatch")
        if counters["updates"] != counters["optimizer_steps"]:
            raise ValueError("checkpoint optimizer count mismatch")
        sampler = np.random.Generator(np.random.PCG64(np.random.SeedSequence(
            rng_domain("replay", self.fit_index))))
        sampler.bit_generator.state = copy.deepcopy(state["sampler"])
        # Validate optimizer on a detached model, without RNG use or updates.
        validation_model = copy.deepcopy(self.online)
        optimizer = torch.optim.Adam(validation_model.parameters(), lr=3e-4)
        optimizer.load_state_dict(copy.deepcopy(state["optimizer"]))
        group = optimizer.param_groups[0]
        if (len(optimizer.param_groups) != 1 or group["lr"] != 3e-4
                or group["betas"] != (.9, .999) or group["eps"] != 1e-8
                or group["weight_decay"] != 0 or group["amsgrad"]
                or group["maximize"] or group["capturable"] or group["differentiable"]
                or group["foreach"] is not None or group["fused"] is not None):
            raise ValueError("checkpoint optimizer hyperparameters mismatch")
        for parameter, values in optimizer.state.items():
            if values.keys() != {"step", "exp_avg", "exp_avg_sq"}:
                raise ValueError("invalid checkpoint optimizer state keys")
            for key, value in values.items():
                if (not isinstance(value, torch.Tensor) or not torch.isfinite(value).all()
                        or value.dtype != torch.float32 or value.device.type != "cpu"
                        or value.shape != (() if key == "step" else parameter.shape)):
                    raise ValueError("invalid checkpoint optimizer state tensor")
        self.online.load_state_dict(state["online"])
        self.target.load_state_dict(state["target"])
        self.optimizer.load_state_dict(copy.deepcopy(state["optimizer"]))
        self.initial = copy.deepcopy(state["initial"])
        self.replay, self.sampler = replay, sampler
        self.counters = copy.deepcopy(counters)
        self.forward_counts = copy.deepcopy(state["forward_counts"])
        self.failed = bool(state["failed"])
        self.last_update = copy.deepcopy(state["last_update"])
        self.timing = copy.deepcopy(state["timing"])

    def checkpoint_identity(self):
        return _digest(self._state())

    def zero_head_certificate(self):
        head = self.online.layers[-1]
        return {"parameter_count": sum(p.numel() for p in self.online.parameters()),
                "init_seed": TORCH_INIT_SEEDS[self.fit_index], "dtype": "float32",
                "device": "cpu", "exact_zero_head": bool(
                    torch.count_nonzero(head.weight) == 0 and torch.count_nonzero(head.bias) == 0),
                "parameter_sha256": _digest(self.online.state_dict()),
                "initial_parameter_sha256": _digest(self.initial)}

    def metrics(self):
        differences = torch.cat([(v.detach() - self.initial[k]).reshape(-1).double()
                                 for k, v in self.online.state_dict().items()])
        return {**copy.deepcopy(self.counters), "forward": copy.deepcopy(self.forward_counts),
                "timing": copy.deepcopy(self.timing), "failed": self.failed,
                "last_update": copy.deepcopy(self.last_update), "replay_size": len(self.replay),
                "parameter_motion_l2": float(torch.linalg.vector_norm(differences)),
                "parameter_motion_max": float(differences.abs().max()),
                "parameter_changed_coordinates": int(torch.count_nonzero(differences))}
