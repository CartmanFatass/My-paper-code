"""B03 service and action-conditioned observation auxiliary replay.

Only actor-legal normalized observations, realized skills, and submitted raw
commands enter replay.  Future QoS and next observations are supervised targets;
neither head is part of the actor's action path.
"""

from __future__ import annotations

import copy
import math
from numbers import Integral, Real
from typing import Any, Mapping
import weakref

import torch
from torch import nn
from torch.nn import functional as F

from experiments.candidates.uav_service_auxiliary.b01.auxiliary import (
    future_window_targets,
    recurrent_entry_masks,
)


ARMS = frozenset({"D", "S", "G"})
CHECKPOINT_VERSION = 1
CALIBRATION_VERSION = 1
CALIBRATION_KEYS = frozenset(
    {
        "version",
        "observation_dim",
        "window",
        "mu",
        "scale",
        "service_target_mean",
        "valid_team_rows",
        "valid_agent_samples",
    }
)


def _module_device_dtype(module: nn.Module) -> tuple[torch.device, torch.dtype]:
    try:
        parameter = next(module.parameters())
    except StopIteration as exc:
        raise ValueError("actor must have parameters") from exc
    return parameter.device, parameter.dtype


def _trainable_parameters(module: nn.Module) -> list[nn.Parameter]:
    return [parameter for parameter in module.parameters() if parameter.requires_grad]


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite real number")
    return result


def _gradient_norm(parameters: list[nn.Parameter]) -> float:
    squares = None
    for parameter in parameters:
        if parameter.grad is None:
            continue
        value = parameter.grad.detach()
        term = torch.sum(value.double() * value.double())
        squares = term if squares is None else squares + term
    result = 0.0 if squares is None else float(torch.sqrt(squares))
    if not math.isfinite(result):
        raise FloatingPointError("non-finite auxiliary gradient norm")
    return result


def _snapshot(parameters: list[nn.Parameter]) -> list[torch.Tensor]:
    return [parameter.detach().clone() for parameter in parameters]


def _movement(before: list[torch.Tensor], parameters: list[nn.Parameter]) -> float:
    if len(before) != len(parameters):
        raise RuntimeError("parameter snapshot mismatch")
    squares = None
    for prior, parameter in zip(before, parameters):
        difference = parameter.detach().double() - prior.double()
        term = torch.sum(difference * difference)
        squares = term if squares is None else squares + term
    return 0.0 if squares is None else float(torch.sqrt(squares))


class _VectorMoments:
    """Float64 streaming vector summaries for JSON diagnostics."""

    def __init__(self, dimension: int) -> None:
        self.dimension = int(dimension)
        self.count = 0
        self.sum: torch.Tensor | None = None
        self.sum_squares: torch.Tensor | None = None
        self.sum_row_norms: torch.Tensor | None = None

    def add(self, values: torch.Tensor) -> None:
        rows = values.detach().reshape(-1, self.dimension).to(dtype=torch.float64)
        if rows.numel() == 0:
            return
        self.count += int(rows.shape[0])
        row_sum = rows.sum(dim=0)
        row_sum_squares = (rows * rows).sum(dim=0)
        row_norms = torch.linalg.vector_norm(rows, dim=-1).sum()
        if self.sum is None:
            self.sum = row_sum
            self.sum_squares = row_sum_squares
            self.sum_row_norms = row_norms
        else:
            self.sum += row_sum
            assert self.sum_squares is not None and self.sum_row_norms is not None
            self.sum_squares += row_sum_squares
            self.sum_row_norms += row_norms

    def as_dict(self) -> dict[str, Any]:
        if self.count:
            assert self.sum is not None and self.sum_squares is not None
            assert self.sum_row_norms is not None
            value_sum = self.sum.to(device="cpu")
            value_sum_squares = self.sum_squares.to(device="cpu")
            mean = value_sum / self.count
            variance = torch.clamp(value_sum_squares / self.count - mean * mean, min=0.0)
            rms = math.sqrt(
                float(value_sum_squares.sum()) / (self.count * self.dimension)
            )
            mean_norm = float(self.sum_row_norms.to(device="cpu")) / self.count
        else:
            mean = torch.zeros(self.dimension, dtype=torch.float64)
            variance = torch.zeros_like(mean)
            rms = 0.0
            mean_norm = 0.0
        return {
            "count": self.count,
            "rms": rms,
            "mean_l2_norm": mean_norm,
            "total_variance": float(variance.sum()),
            "mean": mean.tolist(),
            "variance_per_dimension": variance.tolist(),
        }


class B03AuxiliaryReplay:
    """Train both B03 heads and route one selected loss into base plus GRU."""

    def __init__(
        self,
        actor: nn.Module,
        arm: str,
        *,
        initialization_seed: int,
        generic_initialization_seed: int,
        observation_dim: int,
        action_dim: int = 4,
        window: int = 10,
        chunk_length: int = 50,
        head_lr: float = 3e-4,
        representation_lr: float = 3e-5,
        max_grad_norm: float = 0.5,
    ) -> None:
        if arm not in ARMS:
            raise ValueError(f"arm must be one of {sorted(ARMS)}, got {arm!r}")
        self._validate_actor(actor)
        self.arm = arm
        self.initialization_seed = int(initialization_seed)
        self.generic_initialization_seed = int(generic_initialization_seed)
        self.observation_dim = _positive_integer(observation_dim, "observation_dim")
        self.action_dim = _positive_integer(action_dim, "action_dim")
        self.window = _positive_integer(window, "window")
        if self.window < 2:
            raise ValueError("window must be at least 2 for next-observation targets")
        self.chunk_length = _positive_integer(chunk_length, "chunk_length")
        self.head_lr = _finite_float(head_lr, "head_lr")
        self.representation_lr = _finite_float(representation_lr, "representation_lr")
        self.max_grad_norm = _finite_float(max_grad_norm, "max_grad_norm")
        if self.head_lr <= 0 or self.representation_lr <= 0:
            raise ValueError("optimizer learning rates must be positive")
        if self.max_grad_norm <= 0:
            raise ValueError("max_grad_norm must be positive")

        self._actor_ref = weakref.ref(actor)
        self.hidden_size = int(actor.hidden_size)
        self.n_skills = int(actor.film_generator.in_features)
        self._updates = 0
        self._service_steps = 0
        self._generic_steps = 0
        self._representation_steps = 0
        self._calibration: dict[str, Any] | None = None

        device, dtype = _module_device_dtype(actor)
        # Each CPU fork restores the caller's RNG.  Moving initialized parameters
        # to the actor device consumes no device RNG.
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(self.initialization_seed)
            service_head = nn.Sequential(
                nn.Linear(self.hidden_size, 64),
                nn.ReLU(),
                nn.Linear(64, 1),
            )
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(self.generic_initialization_seed)
            generic_head = nn.Sequential(
                nn.Linear(self.hidden_size + self.action_dim, 64),
                nn.ReLU(),
                nn.Linear(64, self.observation_dim),
            )
        self.service_head = service_head.to(device=device, dtype=dtype)
        self.generic_head = generic_head.to(device=device, dtype=dtype)

        self._service_parameters = _trainable_parameters(self.service_head)
        self._generic_parameters = _trainable_parameters(self.generic_head)
        self._base_parameters = _trainable_parameters(actor.base)
        self._rnn_parameters = _trainable_parameters(actor.rnn)
        self._representation_parameters = self._base_parameters + self._rnn_parameters
        groups = (
            self._service_parameters,
            self._generic_parameters,
            self._representation_parameters,
        )
        if any(not group for group in groups):
            raise ValueError("B03 heads, actor base, and actor rnn must be trainable")
        all_ids = [id(parameter) for group in groups for parameter in group]
        if len(set(all_ids)) != len(all_ids):
            raise ValueError("B03 head and representation parameter sets overlap")

        self.service_optimizer = torch.optim.Adam(self._service_parameters, lr=self.head_lr)
        self.generic_optimizer = torch.optim.Adam(self._generic_parameters, lr=self.head_lr)
        self.representation_optimizer = (
            torch.optim.Adam(self._representation_parameters, lr=self.representation_lr)
            if self.arm in {"S", "G"}
            else None
        )

    @staticmethod
    def _validate_actor(actor: nn.Module) -> None:
        for name in ("base", "film_generator", "rnn", "hidden_size"):
            if not hasattr(actor, name):
                raise ValueError(f"actor is missing required attribute {name!r}")
        recurrent_n = int(getattr(actor.rnn, "_recurrent_N", 1))
        if recurrent_n != 1:
            raise ValueError("B03 auxiliary replay requires a one-layer actor rnn")
        if not isinstance(actor.film_generator, nn.Linear):
            raise ValueError("actor film_generator must be a linear skill-to-FiLM map")
        if actor.film_generator.out_features != 2 * int(actor.hidden_size):
            raise ValueError("actor FiLM output must contain hidden-size gamma and beta")

    def _bound_actor(self, actor: nn.Module) -> None:
        if self._actor_ref() is not actor:
            raise ValueError(
                "auxiliary replay is optimizer-bound to its construction actor; "
                "construct a new replay for a replacement actor"
            )

    def _observation_tensor(
        self,
        observations: Any,
        normalized_observations: Any | None,
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> tuple[torch.Tensor, int, int, int]:
        raw_shape = tuple(torch.as_tensor(observations).shape)
        if len(raw_shape) != 4:
            raise ValueError(f"observations must have shape [T,E,N,D], got {raw_shape}")
        T, E, N, D = raw_shape
        if min(T, E, N) <= 0 or D != self.observation_dim:
            raise ValueError(
                "observations must have positive T/E/N and configured observation_dim; "
                f"got {raw_shape}, expected D={self.observation_dim}"
            )
        replay = observations if normalized_observations is None else normalized_observations
        if tuple(torch.as_tensor(replay).shape) != raw_shape:
            raise ValueError("normalized_observations must match raw observations exactly")
        tensor = torch.as_tensor(replay, device=device, dtype=dtype)
        if not bool(torch.isfinite(tensor).all().item()):
            raise ValueError("replay observations must be finite")
        return tensor, T, E, N

    def _inputs(
        self,
        actor: nn.Module,
        observations: Any,
        skills: Any,
        dones: Any,
        actions: Any,
        *,
        initial_hidden: Any | None,
        normalized_observations: Any | None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, int, int, int]:
        self._bound_actor(actor)
        device, dtype = _module_device_dtype(actor)
        observation_tensor, T, E, N = self._observation_tensor(
            observations, normalized_observations, device=device, dtype=dtype
        )

        skill_value = torch.as_tensor(skills, device=device)
        if skill_value.shape != (T, E, N):
            raise ValueError(f"skills must have shape {(T, E, N)}, got {tuple(skill_value.shape)}")
        if skill_value.is_floating_point() and (
            not bool(torch.isfinite(skill_value).all().item())
            or not bool((skill_value == skill_value.round()).all().item())
        ):
            raise ValueError("skills must contain finite integer indices")
        skill_tensor = skill_value.long()
        if bool(((skill_tensor < 0) | (skill_tensor >= self.n_skills)).any().item()):
            raise ValueError(f"skills must be in [0,{self.n_skills})")

        done_tensor = torch.as_tensor(dones, device=device)
        masks = recurrent_entry_masks(done_tensor, N, dtype=dtype).to(device=device)
        if masks.shape[:2] != (T, E):
            raise ValueError(f"dones must have shape {(T, E)}, got {tuple(done_tensor.shape)}")

        action_tensor = torch.as_tensor(actions, device=device, dtype=dtype).detach()
        expected_actions = (T, E, N, self.action_dim)
        if action_tensor.shape != expected_actions:
            raise ValueError(
                f"actions must have shape {expected_actions}, got {tuple(action_tensor.shape)}"
            )
        if not bool(torch.isfinite(action_tensor).all().item()):
            raise ValueError("actions must be finite")

        if initial_hidden is None:
            hidden = torch.zeros(E, N, self.hidden_size, device=device, dtype=dtype)
        else:
            hidden = torch.as_tensor(initial_hidden, device=device, dtype=dtype)
            expected_hidden = (E, N, self.hidden_size)
            if hidden.shape != expected_hidden:
                raise ValueError(
                    f"initial_hidden must have shape {expected_hidden}, got {tuple(hidden.shape)}"
                )
            if not bool(torch.isfinite(hidden).all().item()):
                raise ValueError("initial_hidden must be finite")

        return (
            observation_tensor.reshape(T, E * N, self.observation_dim),
            skill_tensor.reshape(T, E * N),
            masks.reshape(T, E * N, 1),
            action_tensor.reshape(T, E * N, self.action_dim),
            hidden.reshape(E * N, self.hidden_size),
            T,
            E,
            N,
        )

    @staticmethod
    def _representations(
        actor: nn.Module,
        observations: torch.Tensor,
        skills: torch.Tensor,
        hidden: torch.Tensor,
        masks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        encoded = actor.base(observations)
        one_hot = F.one_hot(
            skills, num_classes=int(actor.film_generator.in_features)
        ).to(dtype=encoded.dtype)
        film = actor.film_generator(one_hot).detach()
        gamma, beta = torch.chunk(film, 2, dim=-1)
        return actor.rnn(gamma * encoded + beta, hidden, masks)

    def _calibration_from_inputs(
        self,
        observations: Any,
        dones: Any,
        qos: Any,
        normalized_observations: Any | None,
    ) -> dict[str, Any]:
        raw = torch.as_tensor(observations)
        shape = tuple(raw.shape)
        if len(shape) != 4 or shape[-1] != self.observation_dim or min(shape[:3]) <= 0:
            raise ValueError(
                f"observations must have shape [T,E,N,{self.observation_dim}], got {shape}"
            )
        replay = raw if normalized_observations is None else torch.as_tensor(normalized_observations)
        if tuple(replay.shape) != shape:
            raise ValueError("normalized_observations must match raw observations exactly")
        replay64 = replay.to(device="cpu", dtype=torch.float64)
        if not bool(torch.isfinite(replay64).all().item()):
            raise ValueError("replay observations must be finite")
        qos64 = torch.as_tensor(qos, device="cpu", dtype=torch.float64)
        service_target, valid = future_window_targets(qos64, dones, window=self.window)
        if tuple(service_target.shape) != shape[:2]:
            raise ValueError(f"qos and dones must have shape {shape[:2]}")
        valid = valid.to(device="cpu")
        # W>=2 guarantees every valid service start has a stored t+1 row.
        next_rows = replay64[1:]
        next_valid = valid[:-1].unsqueeze(-1).expand(-1, -1, shape[2])
        selected = next_rows[next_valid]
        if selected.shape[0] == 0:
            raise ValueError("calibration requires at least one W10-valid next-observation row")
        mu = selected.mean(dim=0)
        scale = torch.clamp(torch.sqrt((selected * selected).mean(dim=0)), min=1.0)
        selected_service = service_target.to(device="cpu", dtype=torch.float64)[valid]
        if selected_service.numel() == 0 or not bool(torch.isfinite(selected_service).all().item()):
            raise ValueError("calibration service targets must be finite and nonempty")
        return {
            "version": CALIBRATION_VERSION,
            "observation_dim": self.observation_dim,
            "window": self.window,
            "mu": mu.tolist(),
            "scale": scale.tolist(),
            "service_target_mean": float(selected_service.mean()),
            "valid_team_rows": int(valid.sum().item()),
            "valid_agent_samples": int(selected.shape[0]),
        }

    def calibrate(
        self,
        observations: Any,
        dones: Any,
        qos: Any,
        *,
        normalized_observations: Any | None = None,
    ) -> dict[str, Any]:
        """Set, or exactly verify, the first-training-rollout calibration."""

        candidate = self._validate_calibration(
            self._calibration_from_inputs(observations, dones, qos, normalized_observations)
        )
        if self._calibration is None:
            self._calibration = candidate
        elif self._calibration != candidate:
            raise ValueError("calibration is immutable and the verification rollout differs")
        return copy.deepcopy(self._calibration)

    def _validate_calibration(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping) or set(payload) != CALIBRATION_KEYS:
            actual = set(payload) if isinstance(payload, Mapping) else type(payload).__name__
            raise ValueError(f"calibration keys mismatch: got {actual!r}")
        if payload["version"] != CALIBRATION_VERSION:
            raise ValueError("calibration version mismatch")
        if payload["observation_dim"] != self.observation_dim:
            raise ValueError("calibration observation_dim mismatch")
        if payload["window"] != self.window:
            raise ValueError("calibration window mismatch")
        mu_raw, scale_raw = payload["mu"], payload["scale"]
        if not isinstance(mu_raw, (list, tuple)) or not isinstance(scale_raw, (list, tuple)):
            raise ValueError("calibration mu and scale must be fixed arrays")
        if len(mu_raw) != self.observation_dim or len(scale_raw) != self.observation_dim:
            raise ValueError("calibration mu and scale lengths must equal observation_dim")
        mu = [_finite_float(value, f"mu[{index}]") for index, value in enumerate(mu_raw)]
        scale = [
            _finite_float(value, f"scale[{index}]") for index, value in enumerate(scale_raw)
        ]
        if any(value < 1.0 for value in scale):
            raise ValueError("calibration scales must be at least one")
        valid_team_rows = _positive_integer(payload["valid_team_rows"], "valid_team_rows")
        valid_agent_samples = _positive_integer(
            payload["valid_agent_samples"], "valid_agent_samples"
        )
        return {
            "version": CALIBRATION_VERSION,
            "observation_dim": self.observation_dim,
            "window": self.window,
            "mu": mu,
            "scale": scale,
            "service_target_mean": _finite_float(
                payload["service_target_mean"], "service_target_mean"
            ),
            "valid_team_rows": valid_team_rows,
            "valid_agent_samples": valid_agent_samples,
        }

    def load_calibration(self, payload: Mapping[str, Any]) -> None:
        """Load exact D calibration, refusing any later change."""

        candidate = self._validate_calibration(payload)
        if self._calibration is not None and self._calibration != candidate:
            raise ValueError("calibration is immutable and cannot be replaced")
        self._calibration = candidate

    def calibration_state(self) -> dict[str, Any] | None:
        return copy.deepcopy(self._calibration)

    def _scaled_observation_targets(self, observations: torch.Tensor) -> torch.Tensor:
        if self._calibration is None:
            raise RuntimeError("calibrate or load_calibration before auxiliary update")
        mu = observations.new_tensor(self._calibration["mu"])
        scale = observations.new_tensor(self._calibration["scale"])
        return (observations[1:] - mu) / scale

    def update(
        self,
        actor: nn.Module,
        observations: Any,
        skills: Any,
        dones: Any,
        qos: Any,
        *,
        actions: Any,
        initial_hidden: Any | None = None,
        normalized_observations: Any | None = None,
    ) -> dict[str, Any]:
        """Run one chronological pass, stepping service then generic in each chunk."""

        if self._calibration is None:
            raise RuntimeError("calibrate or load_calibration before auxiliary update")
        obs, skill, masks, command, hidden, T, E, N = self._inputs(
            actor,
            observations,
            skills,
            dones,
            actions,
            initial_hidden=initial_hidden,
            normalized_observations=normalized_observations,
        )
        device, dtype = _module_device_dtype(actor)
        service_target, valid = future_window_targets(qos, dones, window=self.window)
        service_target = service_target.to(device=device, dtype=dtype)
        valid = valid.to(device=device)
        if service_target.shape != (T, E):
            raise ValueError(f"qos must have shape {(T, E)}, got {tuple(service_target.shape)}")
        observation_target = self._scaled_observation_targets(
            obs.reshape(T, E, N, self.observation_dim)
        )

        service_before = _snapshot(self._service_parameters)
        generic_before = _snapshot(self._generic_parameters)
        base_before = _snapshot(self._base_parameters)
        rnn_before = _snapshot(self._rnn_parameters)
        service_loss_sum = 0.0
        generic_loss_sum = 0.0
        valid_agent_count = 0
        valid_team_count = 0
        service_steps = generic_steps = representation_steps = 0
        service_grad_sum = generic_grad_sum = representation_grad_sum = 0.0
        service_grad_max = generic_grad_max = representation_grad_max = 0.0
        base_grad_max = rnn_grad_max = 0.0
        service_clipped = generic_clipped = representation_clipped = 0
        service_target_stats = _VectorMoments(1)
        service_prediction_stats = _VectorMoments(1)
        observation_target_stats = _VectorMoments(self.observation_dim)
        observation_prediction_stats = _VectorMoments(self.observation_dim)
        feature_stats = _VectorMoments(self.hidden_size)

        self.service_head.train()
        self.generic_head.train()
        for start in range(0, T, self.chunk_length):
            stop = min(start + self.chunk_length, T)
            features, hidden = self._representations(
                actor, obs[start:stop], skill[start:stop], hidden, masks[start:stop]
            )
            shaped_features = features.reshape(stop - start, E, N, self.hidden_size)
            service_features = features if self.arm == "S" else features.detach()
            generic_features = features if self.arm == "G" else features.detach()
            service_prediction = self.service_head(service_features).squeeze(-1).reshape(
                stop - start, E, N
            )
            generic_input = torch.cat((generic_features, command[start:stop]), dim=-1)
            generic_prediction = self.generic_head(generic_input).reshape(
                stop - start, E, N, self.observation_dim
            )
            chunk_valid = valid[start:stop]
            valid_agents = chunk_valid.unsqueeze(-1).expand(-1, -1, N)
            count = int(valid_agents.sum().item())
            if count:
                expanded_service = service_target[start:stop].unsqueeze(-1).expand(-1, -1, N)
                next_target = observation_target[start : min(stop, T - 1)]
                # Fixed W10 validity makes the final W-1 rows false.  Padding only
                # aligns indexing for a tail chunk; no padded row can be selected.
                if next_target.shape[0] < stop - start:
                    next_target = torch.cat(
                        (
                            next_target,
                            observation_target.new_zeros(
                                stop - start - next_target.shape[0], E, N, self.observation_dim
                            ),
                        ),
                        dim=0,
                    )
                service_loss = F.mse_loss(
                    service_prediction[valid_agents], expanded_service[valid_agents]
                )
                generic_loss = F.mse_loss(
                    generic_prediction[valid_agents], next_target[valid_agents]
                )
                if not bool(torch.isfinite(service_loss).item()) or not bool(
                    torch.isfinite(generic_loss).item()
                ):
                    raise FloatingPointError("non-finite B03 auxiliary loss")

                self.service_optimizer.zero_grad(set_to_none=True)
                if self.arm == "S":
                    assert self.representation_optimizer is not None
                    self.representation_optimizer.zero_grad(set_to_none=True)
                service_loss.backward()
                service_grad = float(
                    torch.nn.utils.clip_grad_norm_(
                        self._service_parameters,
                        self.max_grad_norm,
                        error_if_nonfinite=True,
                        foreach=False,
                    )
                )
                service_grad_sum += service_grad
                service_grad_max = max(service_grad_max, service_grad)
                service_clipped += int(service_grad > self.max_grad_norm)
                if self.arm == "S":
                    base_grad = _gradient_norm(self._base_parameters)
                    rnn_grad = _gradient_norm(self._rnn_parameters)
                    representation_grad = float(
                        torch.nn.utils.clip_grad_norm_(
                            self._representation_parameters,
                            self.max_grad_norm,
                            error_if_nonfinite=True,
                            foreach=False,
                        )
                    )
                    base_grad_max = max(base_grad_max, base_grad)
                    rnn_grad_max = max(rnn_grad_max, rnn_grad)
                    representation_grad_sum += representation_grad
                    representation_grad_max = max(representation_grad_max, representation_grad)
                    representation_clipped += int(representation_grad > self.max_grad_norm)
                self.service_optimizer.step()
                service_steps += 1
                if self.arm == "S":
                    assert self.representation_optimizer is not None
                    self.representation_optimizer.step()
                    representation_steps += 1

                self.generic_optimizer.zero_grad(set_to_none=True)
                if self.arm == "G":
                    assert self.representation_optimizer is not None
                    self.representation_optimizer.zero_grad(set_to_none=True)
                generic_loss.backward()
                generic_grad = float(
                    torch.nn.utils.clip_grad_norm_(
                        self._generic_parameters,
                        self.max_grad_norm,
                        error_if_nonfinite=True,
                        foreach=False,
                    )
                )
                generic_grad_sum += generic_grad
                generic_grad_max = max(generic_grad_max, generic_grad)
                generic_clipped += int(generic_grad > self.max_grad_norm)
                if self.arm == "G":
                    base_grad = _gradient_norm(self._base_parameters)
                    rnn_grad = _gradient_norm(self._rnn_parameters)
                    representation_grad = float(
                        torch.nn.utils.clip_grad_norm_(
                            self._representation_parameters,
                            self.max_grad_norm,
                            error_if_nonfinite=True,
                            foreach=False,
                        )
                    )
                    base_grad_max = max(base_grad_max, base_grad)
                    rnn_grad_max = max(rnn_grad_max, rnn_grad)
                    representation_grad_sum += representation_grad
                    representation_grad_max = max(representation_grad_max, representation_grad)
                    representation_clipped += int(representation_grad > self.max_grad_norm)
                self.generic_optimizer.step()
                generic_steps += 1
                if self.arm == "G":
                    assert self.representation_optimizer is not None
                    self.representation_optimizer.step()
                    representation_steps += 1

                service_loss_sum += float(service_loss.detach()) * count
                generic_loss_sum += float(generic_loss.detach()) * count
                valid_agent_count += count
                valid_team_count += int(chunk_valid.sum().item())
                service_target_stats.add(expanded_service[valid_agents].unsqueeze(-1))
                service_prediction_stats.add(service_prediction[valid_agents].unsqueeze(-1))
                observation_target_stats.add(next_target[valid_agents])
                observation_prediction_stats.add(generic_prediction[valid_agents])
                feature_stats.add(shaped_features[valid_agents])
            hidden = hidden.detach()

        self._updates += 1
        self._service_steps += service_steps
        self._generic_steps += generic_steps
        self._representation_steps += representation_steps

        def optimizer_diagnostics(
            steps: int, gradient_sum: float, gradient_max: float, clipped: int
        ) -> dict[str, float | int]:
            return {
                "optimizer_steps": steps,
                "preclip_gradient_norm_mean": gradient_sum / steps if steps else 0.0,
                "preclip_gradient_norm_max": gradient_max,
                "clip_fraction": clipped / steps if steps else 0.0,
            }

        service_loss_mean = service_loss_sum / valid_agent_count if valid_agent_count else 0.0
        generic_loss_mean = generic_loss_sum / valid_agent_count if valid_agent_count else 0.0
        return {
            "arm": self.arm,
            "pass": self._updates,
            "supervised_team_rows": valid_team_count,
            "supervised_agent_samples": valid_agent_count,
            "service": {
                "loss": service_loss_mean,
                "loss_coefficient": 1.0,
                "used_loss": service_loss_mean,
                **optimizer_diagnostics(
                    service_steps, service_grad_sum, service_grad_max, service_clipped
                ),
                "parameter_movement_l2": _movement(service_before, self._service_parameters),
                "target": service_target_stats.as_dict(),
                "prediction": service_prediction_stats.as_dict(),
            },
            "observation": {
                "loss": generic_loss_mean,
                "loss_coefficient": 1.0,
                "used_loss": generic_loss_mean,
                "scalar_elements": valid_agent_count * self.observation_dim,
                **optimizer_diagnostics(
                    generic_steps, generic_grad_sum, generic_grad_max, generic_clipped
                ),
                "parameter_movement_l2": _movement(generic_before, self._generic_parameters),
                "target": observation_target_stats.as_dict(),
                "prediction": observation_prediction_stats.as_dict(),
            },
            "representation": {
                **optimizer_diagnostics(
                    representation_steps,
                    representation_grad_sum,
                    representation_grad_max,
                    representation_clipped,
                ),
                "base_preclip_gradient_norm_max": base_grad_max,
                "gru_preclip_gradient_norm_max": rnn_grad_max,
                "base_parameter_movement_l2": _movement(base_before, self._base_parameters),
                "gru_parameter_movement_l2": _movement(rnn_before, self._rnn_parameters),
            },
            "features": feature_stats.as_dict(),
        }

    def predict_all(
        self,
        actor: nn.Module,
        observations: Any,
        skills: Any,
        dones: Any,
        *,
        actions: Any,
        initial_hidden: Any | None = None,
        normalized_observations: Any | None = None,
    ) -> dict[str, torch.Tensor]:
        """Return deterministic heads/features without updates, mode, or RNG changes.

        Observation predictions are always the raw generic-head outputs in the
        calibrated loss coordinates.  This remains available before calibration so
        rollout-0 predictions can be saved and scored once the scale exists.
        """

        obs, skill, masks, command, hidden, T, E, N = self._inputs(
            actor,
            observations,
            skills,
            dones,
            actions,
            initial_hidden=initial_hidden,
            normalized_observations=normalized_observations,
        )
        service_mode = self.service_head.training
        generic_mode = self.generic_head.training
        cpu_rng = torch.random.get_rng_state().clone()
        device, _ = _module_device_dtype(actor)
        cuda_rng = None
        if device.type == "cuda":
            cuda_rng = torch.cuda.get_rng_state(device).clone()
        service_chunks: list[torch.Tensor] = []
        observation_chunks: list[torch.Tensor] = []
        feature_chunks: list[torch.Tensor] = []
        self.service_head.eval()
        self.generic_head.eval()
        try:
            with torch.no_grad():
                for start in range(0, T, self.chunk_length):
                    stop = min(start + self.chunk_length, T)
                    features, hidden = self._representations(
                        actor, obs[start:stop], skill[start:stop], hidden, masks[start:stop]
                    )
                    service_chunks.append(
                        self.service_head(features).squeeze(-1).reshape(stop - start, E, N)
                    )
                    generic_input = torch.cat((features, command[start:stop]), dim=-1)
                    observation_chunks.append(
                        self.generic_head(generic_input).reshape(
                            stop - start, E, N, self.observation_dim
                        )
                    )
                    feature_chunks.append(features.reshape(stop - start, E, N, self.hidden_size))
                    hidden = hidden.detach()
            service = torch.cat(service_chunks, dim=0)
            observation = torch.cat(observation_chunks, dim=0)
            features = torch.cat(feature_chunks, dim=0)
            return {"service": service, "observation": observation, "features": features}
        finally:
            self.service_head.train(service_mode)
            self.generic_head.train(generic_mode)
            torch.random.set_rng_state(cpu_rng)
            if cuda_rng is not None:
                torch.cuda.set_rng_state(cuda_rng, device)

    def checkpoint_state(self) -> dict[str, Any]:
        """Return both heads, optimizers, calibration, counters, and bindings."""

        return copy.deepcopy(
            {
                "version": CHECKPOINT_VERSION,
                "arm": self.arm,
                "initialization_seed": self.initialization_seed,
                "generic_initialization_seed": self.generic_initialization_seed,
                "observation_dim": self.observation_dim,
                "action_dim": self.action_dim,
                "hidden_size": self.hidden_size,
                "n_skills": self.n_skills,
                "window": self.window,
                "chunk_length": self.chunk_length,
                "head_lr": self.head_lr,
                "representation_lr": self.representation_lr,
                "max_grad_norm": self.max_grad_norm,
                "updates": self._updates,
                "service_steps": self._service_steps,
                "generic_steps": self._generic_steps,
                "representation_steps": self._representation_steps,
                "calibration": self.calibration_state(),
                "service_head": self.service_head.state_dict(),
                "generic_head": self.generic_head.state_dict(),
                "service_optimizer": self.service_optimizer.state_dict(),
                "generic_optimizer": self.generic_optimizer.state_dict(),
                "representation_optimizer": (
                    None
                    if self.representation_optimizer is None
                    else self.representation_optimizer.state_dict()
                ),
            }
        )

    def load_checkpoint_state(self, payload: Mapping[str, Any]) -> None:
        """Restore after the paired native actor, validating all fixed bindings."""

        expected = {
            "version": CHECKPOINT_VERSION,
            "arm": self.arm,
            "initialization_seed": self.initialization_seed,
            "generic_initialization_seed": self.generic_initialization_seed,
            "observation_dim": self.observation_dim,
            "action_dim": self.action_dim,
            "hidden_size": self.hidden_size,
            "n_skills": self.n_skills,
            "window": self.window,
            "chunk_length": self.chunk_length,
            "head_lr": self.head_lr,
            "representation_lr": self.representation_lr,
            "max_grad_norm": self.max_grad_norm,
        }
        for name, value in expected.items():
            if payload.get(name) != value:
                raise ValueError(
                    f"B03 auxiliary checkpoint {name} mismatch: expected {value!r}, "
                    f"got {payload.get(name)!r}"
                )
        representation_state = payload.get("representation_optimizer")
        if (self.representation_optimizer is None) != (representation_state is None):
            raise ValueError("B03 auxiliary checkpoint representation optimizer mismatch")
        calibration = payload.get("calibration")
        validated_calibration = (
            None if calibration is None else self._validate_calibration(calibration)
        )
        if self._calibration is not None and self._calibration != validated_calibration:
            raise ValueError("B03 auxiliary checkpoint calibration mismatch")

        self.service_head.load_state_dict(payload["service_head"])
        self.generic_head.load_state_dict(payload["generic_head"])
        self.service_optimizer.load_state_dict(payload["service_optimizer"])
        self.generic_optimizer.load_state_dict(payload["generic_optimizer"])
        if self.representation_optimizer is not None:
            self.representation_optimizer.load_state_dict(representation_state)
        self._calibration = validated_calibration
        self._updates = int(payload["updates"])
        self._service_steps = int(payload["service_steps"])
        self._generic_steps = int(payload["generic_steps"])
        self._representation_steps = int(payload["representation_steps"])
