"""Auxiliary factual-service replay for UAV service auxiliary B01.

The replay consumes only actor-legal observations and realized skills.  Future QoS is
used to construct supervised targets and is never an actor or recurrent input.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from typing import Any
import weakref

import torch
from torch import nn
from torch.nn import functional as F


ARMS = frozenset({"detach", "joint"})
CHECKPOINT_VERSION = 1


@dataclass(frozen=True)
class AuxiliaryUpdate:
    """Measurements from one chronological auxiliary replay pass."""

    loss: float
    supervised_team_rows: int
    supervised_agent_samples: int
    optimizer_steps: int
    head_gradient_norm: float
    representation_gradient_norm: float

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _transition_dones(dones: Any) -> torch.Tensor:
    value = torch.as_tensor(dones)
    if value.ndim != 2:
        raise ValueError(f"dones must have shape [T,E], got {tuple(value.shape)}")
    if value.dtype != torch.bool:
        if not bool(torch.isfinite(value).all().item()):
            raise ValueError("dones must be finite binary values")
        if not bool(((value == 0) | (value == 1)).all().item()):
            raise ValueError("dones must be binary transition flags")
        value = value.bool()
    return value


def future_window_targets(
    qos: Any,
    dones: Any,
    *,
    window: int = 10,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return future-window means and the rows having a complete episode-local label.

    ``dones[t,e]`` marks the transition taken from observation row ``t``.  A
    terminal transition may be the final member of a complete target window, but a
    terminal transition before that point censors the target.  The final ``window-1``
    collection rows are therefore always censored.
    """

    if int(window) != window or window <= 0:
        raise ValueError("window must be a positive integer")
    window = int(window)
    qos_tensor = torch.as_tensor(qos)
    if qos_tensor.ndim != 2:
        raise ValueError(f"qos must have shape [T,E], got {tuple(qos_tensor.shape)}")
    if not (qos_tensor.is_floating_point() or qos_tensor.is_complex()):
        qos_tensor = qos_tensor.float()
    if qos_tensor.is_complex() or not bool(torch.isfinite(qos_tensor).all().item()):
        raise ValueError("qos must contain finite real values")
    done_tensor = _transition_dones(dones).to(device=qos_tensor.device)
    if done_tensor.shape != qos_tensor.shape:
        raise ValueError(
            "dones and qos must have the same [T,E] shape, got "
            f"{tuple(done_tensor.shape)} and {tuple(qos_tensor.shape)}"
        )

    targets = torch.zeros_like(qos_tensor)
    valid = torch.zeros_like(done_tensor)
    if qos_tensor.shape[0] < window:
        return targets, valid

    qos_windows = qos_tensor.unfold(0, window, 1)
    targets[: qos_windows.shape[0]] = qos_windows.mean(dim=-1)
    if window == 1:
        valid[: qos_windows.shape[0]] = True
    else:
        done_windows = done_tensor.unfold(0, window, 1)
        valid[: done_windows.shape[0]] = ~done_windows[..., :-1].any(dim=-1)
    return targets, valid


def recurrent_entry_masks(
    dones: Any,
    n_agents: int,
    *,
    dtype: torch.dtype = torch.float32,
) -> torch.Tensor:
    """Build actor-entry masks of shape ``[T,E,N,1]`` from transition dones."""

    if int(n_agents) != n_agents or n_agents <= 0:
        raise ValueError("n_agents must be a positive integer")
    done_tensor = _transition_dones(dones)
    masks = torch.ones(
        (*done_tensor.shape, int(n_agents), 1),
        dtype=dtype,
        device=done_tensor.device,
    )
    if done_tensor.shape[0] > 1:
        masks[1:] = (~done_tensor[:-1]).to(dtype=dtype).unsqueeze(-1).unsqueeze(-1)
    return masks


def _module_device_dtype(module: nn.Module) -> tuple[torch.device, torch.dtype]:
    try:
        parameter = next(module.parameters())
    except StopIteration as exc:
        raise ValueError("actor must have parameters") from exc
    return parameter.device, parameter.dtype


def _trainable_parameters(module: nn.Module) -> list[nn.Parameter]:
    return [parameter for parameter in module.parameters() if parameter.requires_grad]


class AuxiliaryReplay:
    """Train the B01 factual head, optionally updating actor base and recurrent state."""

    def __init__(
        self,
        actor: nn.Module,
        arm: str,
        *,
        initialization_seed: int,
        window: int = 10,
        chunk_length: int = 50,
        head_lr: float = 3e-4,
        representation_lr: float = 3e-5,
        max_grad_norm: float = 0.5,
    ) -> None:
        if arm not in ARMS:
            raise ValueError(f"arm must be one of {sorted(ARMS)}, got {arm!r}")
        if int(window) != window or window <= 0:
            raise ValueError("window must be a positive integer")
        if int(chunk_length) != chunk_length or chunk_length <= 0:
            raise ValueError("chunk_length must be a positive integer")
        if head_lr <= 0 or representation_lr <= 0:
            raise ValueError("optimizer learning rates must be positive")
        if max_grad_norm <= 0:
            raise ValueError("max_grad_norm must be positive")
        self._validate_actor(actor)

        self.arm = arm
        self.initialization_seed = int(initialization_seed)
        self.window = int(window)
        self.chunk_length = int(chunk_length)
        self.head_lr = float(head_lr)
        self.representation_lr = float(representation_lr)
        self.max_grad_norm = float(max_grad_norm)
        self._actor_ref = weakref.ref(actor)
        self._updates = 0

        device, dtype = _module_device_dtype(actor)
        # The head is built on CPU, so preserving the CPU generator is sufficient;
        # moving initialized parameters to the actor device consumes no device RNG.
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(self.initialization_seed)
            head = nn.Sequential(
                nn.Linear(int(actor.hidden_size), 64),
                nn.ReLU(),
                nn.Linear(64, 1),
            )
        self.head = head.to(device=device, dtype=dtype)
        self._head_parameters = _trainable_parameters(self.head)
        self._representation_parameters = (
            _trainable_parameters(actor.base) + _trainable_parameters(actor.rnn)
        )
        if not self._head_parameters:
            raise ValueError("auxiliary head has no trainable parameters")
        if not self._representation_parameters:
            raise ValueError("actor base and rnn have no trainable parameters")
        if len({id(parameter) for parameter in self._representation_parameters}) != len(
            self._representation_parameters
        ):
            raise ValueError("actor base and rnn parameter sets overlap")

        self.head_optimizer = torch.optim.Adam(self._head_parameters, lr=self.head_lr)
        self.representation_optimizer = (
            torch.optim.Adam(self._representation_parameters, lr=self.representation_lr)
            if arm == "joint"
            else None
        )

    @staticmethod
    def _validate_actor(actor: nn.Module) -> None:
        for name in ("base", "film_generator", "rnn", "hidden_size"):
            if not hasattr(actor, name):
                raise ValueError(f"actor is missing required attribute {name!r}")
        recurrent_n = int(getattr(actor.rnn, "_recurrent_N", 1))
        if recurrent_n != 1:
            raise ValueError("B01 auxiliary replay requires a one-layer actor rnn")
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

    def _inputs(
        self,
        actor: nn.Module,
        observations: Any,
        skills: Any,
        dones: Any,
        *,
        initial_hidden: Any | None,
        normalized_observations: Any | None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, int, int, int]:
        self._bound_actor(actor)
        raw_shape = tuple(torch.as_tensor(observations).shape)
        if len(raw_shape) != 4:
            raise ValueError(f"observations must have shape [T,E,N,D], got {raw_shape}")
        T, E, N, _ = raw_shape
        if min(T, E, N) <= 0:
            raise ValueError("observations must have positive T, E and N dimensions")
        replay_observations = observations if normalized_observations is None else normalized_observations
        if tuple(torch.as_tensor(replay_observations).shape) != raw_shape:
            raise ValueError("normalized_observations must match raw observations exactly")

        device, dtype = _module_device_dtype(actor)
        observation_tensor = torch.as_tensor(
            replay_observations, device=device, dtype=dtype
        )
        if not bool(torch.isfinite(observation_tensor).all().item()):
            raise ValueError("replay observations must be finite")

        skill_value = torch.as_tensor(skills, device=device)
        if skill_value.shape != (T, E, N):
            raise ValueError(
                f"skills must have shape {(T, E, N)}, got {tuple(skill_value.shape)}"
            )
        if skill_value.is_floating_point():
            if not bool(torch.isfinite(skill_value).all().item()) or not bool(
                (skill_value == skill_value.round()).all().item()
            ):
                raise ValueError("skills must contain finite integer indices")
        skill_tensor = skill_value.long()
        n_skills = int(actor.film_generator.in_features)
        if bool(((skill_tensor < 0) | (skill_tensor >= n_skills)).any().item()):
            raise ValueError(f"skills must be in [0,{n_skills})")

        done_tensor = _transition_dones(dones).to(device=device)
        if done_tensor.shape != (T, E):
            raise ValueError(f"dones must have shape {(T, E)}, got {tuple(done_tensor.shape)}")
        masks = recurrent_entry_masks(done_tensor, N, dtype=dtype).reshape(T, E * N, 1)

        if initial_hidden is None:
            hidden = torch.zeros(E, N, int(actor.hidden_size), device=device, dtype=dtype)
        else:
            hidden = torch.as_tensor(initial_hidden, device=device, dtype=dtype)
            expected = (E, N, int(actor.hidden_size))
            if hidden.shape != expected:
                raise ValueError(
                    f"initial_hidden must have shape {expected}, got {tuple(hidden.shape)}"
                )
            if not bool(torch.isfinite(hidden).all().item()):
                raise ValueError("initial_hidden must be finite")

        return (
            observation_tensor.reshape(T, E * N, raw_shape[-1]),
            skill_tensor.reshape(T, E * N),
            masks,
            hidden.reshape(E * N, int(actor.hidden_size)),
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
        # FiLM values condition the replay exactly as in R_Actor while remaining
        # constants for this loss.  Gradients still pass through ``encoded``.
        film = actor.film_generator(one_hot).detach()
        gamma, beta = torch.chunk(film, 2, dim=-1)
        conditioned = gamma * encoded + beta
        return actor.rnn(conditioned, hidden, masks)

    def update(
        self,
        actor: nn.Module,
        observations: Any,
        skills: Any,
        dones: Any,
        qos: Any,
        *,
        initial_hidden: Any | None = None,
        normalized_observations: Any | None = None,
    ) -> AuxiliaryUpdate:
        """Run one chronological, 50-step-TBPTT-style auxiliary pass."""

        obs, skill, masks, hidden, T, E, N = self._inputs(
            actor,
            observations,
            skills,
            dones,
            initial_hidden=initial_hidden,
            normalized_observations=normalized_observations,
        )
        target, valid = future_window_targets(qos, dones, window=self.window)
        device, dtype = _module_device_dtype(actor)
        target = target.to(device=device, dtype=dtype)
        valid = valid.to(device=device)
        if target.shape != (T, E):
            raise ValueError(f"qos must have shape {(T, E)}, got {tuple(target.shape)}")

        weighted_loss = 0.0
        supervised_samples = 0
        supervised_team_rows = 0
        optimizer_steps = 0
        maximum_head_gradient = 0.0
        maximum_representation_gradient = 0.0

        self.head.train()
        for start in range(0, T, self.chunk_length):
            stop = min(start + self.chunk_length, T)
            features, hidden = self._representations(
                actor,
                obs[start:stop],
                skill[start:stop],
                hidden,
                masks[start:stop],
            )
            replay_features = features if self.arm == "joint" else features.detach()
            predictions = self.head(replay_features).squeeze(-1).reshape(stop - start, E, N)
            chunk_valid = valid[start:stop]
            valid_agents = chunk_valid.unsqueeze(-1).expand(-1, -1, N)
            valid_count = int(valid_agents.sum().item())
            if valid_count:
                expanded_targets = target[start:stop].unsqueeze(-1).expand(-1, -1, N)
                loss = F.mse_loss(predictions[valid_agents], expanded_targets[valid_agents])
                if not bool(torch.isfinite(loss).item()):
                    raise FloatingPointError("non-finite auxiliary loss")

                self.head_optimizer.zero_grad(set_to_none=True)
                if self.representation_optimizer is not None:
                    self.representation_optimizer.zero_grad(set_to_none=True)
                loss.backward()
                head_gradient = torch.nn.utils.clip_grad_norm_(
                    self._head_parameters,
                    self.max_grad_norm,
                    error_if_nonfinite=True,
                    foreach=False,
                )
                maximum_head_gradient = max(maximum_head_gradient, float(head_gradient))
                if self.representation_optimizer is not None:
                    representation_gradient = torch.nn.utils.clip_grad_norm_(
                        self._representation_parameters,
                        self.max_grad_norm,
                        error_if_nonfinite=True,
                        foreach=False,
                    )
                    maximum_representation_gradient = max(
                        maximum_representation_gradient, float(representation_gradient)
                    )
                self.head_optimizer.step()
                if self.representation_optimizer is not None:
                    self.representation_optimizer.step()

                weighted_loss += float(loss.detach()) * valid_count
                supervised_samples += valid_count
                supervised_team_rows += int(chunk_valid.sum().item())
                optimizer_steps += 1
            # This is the intentional TBPTT boundary.  It is applied even when a
            # chunk has no label, so later chunks cannot backpropagate through it.
            hidden = hidden.detach()

        self._updates += 1
        return AuxiliaryUpdate(
            loss=weighted_loss / supervised_samples if supervised_samples else 0.0,
            supervised_team_rows=supervised_team_rows,
            supervised_agent_samples=supervised_samples,
            optimizer_steps=optimizer_steps,
            head_gradient_norm=maximum_head_gradient,
            representation_gradient_norm=maximum_representation_gradient,
        )

    def predict(
        self,
        actor: nn.Module,
        observations: Any,
        skills: Any,
        dones: Any,
        *,
        initial_hidden: Any | None = None,
        normalized_observations: Any | None = None,
    ) -> torch.Tensor:
        """Replay a factual trajectory deterministically and return ``[T,E,N]``."""

        obs, skill, masks, hidden, T, E, N = self._inputs(
            actor,
            observations,
            skills,
            dones,
            initial_hidden=initial_hidden,
            normalized_observations=normalized_observations,
        )
        was_training = self.head.training
        self.head.eval()
        chunks = []
        try:
            with torch.no_grad():
                for start in range(0, T, self.chunk_length):
                    stop = min(start + self.chunk_length, T)
                    features, hidden = self._representations(
                        actor,
                        obs[start:stop],
                        skill[start:stop],
                        hidden,
                        masks[start:stop],
                    )
                    chunks.append(
                        self.head(features).squeeze(-1).reshape(stop - start, E, N)
                    )
                    hidden = hidden.detach()
        finally:
            self.head.train(was_training)
        return torch.cat(chunks, dim=0)

    def checkpoint_state(self) -> dict[str, Any]:
        """Return the head and optimizer state stored beside the native actor checkpoint."""

        return copy.deepcopy(
            {
                "version": CHECKPOINT_VERSION,
                "arm": self.arm,
                "initialization_seed": self.initialization_seed,
                "window": self.window,
                "chunk_length": self.chunk_length,
                "head_lr": self.head_lr,
                "representation_lr": self.representation_lr,
                "max_grad_norm": self.max_grad_norm,
                "updates": self._updates,
                "head": self.head.state_dict(),
                "head_optimizer": self.head_optimizer.state_dict(),
                "representation_optimizer": (
                    None
                    if self.representation_optimizer is None
                    else self.representation_optimizer.state_dict()
                ),
            }
        )

    def load_checkpoint_state(self, payload: dict[str, Any]) -> None:
        """Restore state after the runner has restored the paired native actor."""

        expected = {
            "version": CHECKPOINT_VERSION,
            "arm": self.arm,
            "initialization_seed": self.initialization_seed,
            "window": self.window,
            "chunk_length": self.chunk_length,
            "head_lr": self.head_lr,
            "representation_lr": self.representation_lr,
            "max_grad_norm": self.max_grad_norm,
        }
        for name, value in expected.items():
            if payload.get(name) != value:
                raise ValueError(
                    f"auxiliary checkpoint {name} mismatch: expected {value!r}, "
                    f"got {payload.get(name)!r}"
                )
        representation_state = payload.get("representation_optimizer")
        if (self.representation_optimizer is None) != (representation_state is None):
            raise ValueError("auxiliary checkpoint representation optimizer mismatch")
        self.head.load_state_dict(payload["head"])
        self.head_optimizer.load_state_dict(payload["head_optimizer"])
        if self.representation_optimizer is not None:
            self.representation_optimizer.load_state_dict(representation_state)
        self._updates = int(payload["updates"])
