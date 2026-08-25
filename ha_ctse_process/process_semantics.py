"""Conditional process semantics for the Iteration-5 spatial carrier.

Only detached local motion consequences enter the positive process path.  The
module has no policy likelihood and cannot backpropagate into either policy.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
from typing import Any, Mapping, MutableSequence, Sequence

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F


EVENT_SEMANTIC_SCHEMA_VERSION = 1
PROCESS_WINDOW_LENGTH = 12
PROCESS_SKILL_COUNT = 3


def _detached_float_vector(value: Any, *, name: str) -> np.ndarray:
    """Copy one policy-side tensor/array into detached semantic storage."""

    if isinstance(value, torch.Tensor):
        array = value.detach().to(device="cpu", dtype=torch.float32).numpy()
    else:
        array = np.asarray(value, dtype=np.float32)
    vector = np.array(array, dtype=np.float32, copy=True).reshape(-1)
    if not np.isfinite(vector).all():
        raise ValueError(f"{name} must be finite")
    return vector


@dataclass(frozen=True)
class ProcessWindow:
    lifecycle_key: str
    membership_epoch: int
    policy_version: int
    skill: int
    linked_low_row_indices: tuple[int, ...]
    start_observation: np.ndarray
    start_actor_hidden: np.ndarray
    process_state_sequence: tuple[float, ...]

    def __post_init__(self) -> None:
        linked = tuple(int(value) for value in self.linked_low_row_indices)
        if any(value < 0 for value in linked) or len(set(linked)) != len(linked):
            raise ValueError("process-window low-row indices must be unique and non-negative")
        if len(linked) > PROCESS_WINDOW_LENGTH:
            raise ValueError("process window exceeded the frozen active-step limit")
        sequence = tuple(float(value) for value in self.process_state_sequence)
        if len(sequence) != len(linked) + 1 or not np.isfinite(sequence).all():
            raise ValueError("process-state sequence must contain one finite boundary per step")
        observation = _detached_float_vector(
            self.start_observation, name="start observation"
        )
        hidden = _detached_float_vector(
            self.start_actor_hidden, name="start actor hidden"
        )
        observation.setflags(write=False)
        hidden.setflags(write=False)
        membership_epoch = int(self.membership_epoch)
        policy_version = int(self.policy_version)
        skill = int(self.skill)
        if membership_epoch < 0 or policy_version < 0 or skill < 0:
            raise ValueError("process-window epoch, policy version and skill must be non-negative")
        object.__setattr__(self, "lifecycle_key", str(self.lifecycle_key))
        object.__setattr__(self, "membership_epoch", membership_epoch)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "skill", skill)
        object.__setattr__(self, "linked_low_row_indices", linked)
        object.__setattr__(self, "start_observation", observation)
        object.__setattr__(self, "start_actor_hidden", hidden)
        object.__setattr__(self, "process_state_sequence", sequence)

    @property
    def valid_length(self) -> int:
        return len(self.linked_low_row_indices)

    def process_features(self) -> np.ndarray:
        if self.valid_length <= 0:
            return np.zeros((0, 2), dtype=np.float32)
        states = np.asarray(self.process_state_sequence, dtype=np.float32)
        return np.stack((states[1:] - states[0], states[1:] - states[:-1]), axis=-1)


@dataclass
class _OpenWindow:
    lifecycle_key: str
    membership_epoch: int
    policy_version: int
    skill: int
    linked_low_row_indices: list[int]
    start_observation: np.ndarray
    start_actor_hidden: np.ndarray
    process_state_sequence: list[float]

    def close(self) -> ProcessWindow:
        return ProcessWindow(
            lifecycle_key=self.lifecycle_key,
            membership_epoch=self.membership_epoch,
            policy_version=self.policy_version,
            skill=self.skill,
            linked_low_row_indices=tuple(self.linked_low_row_indices),
            start_observation=self.start_observation.copy(),
            start_actor_hidden=self.start_actor_hidden.copy(),
            process_state_sequence=tuple(self.process_state_sequence),
        )


class ProcessWindowLedger:
    """One environment's non-overlapping lifecycle/window ownership ledger."""

    def __init__(self, *, max_window_length: int = 12) -> None:
        self.max_window_length = int(max_window_length)
        if self.max_window_length != PROCESS_WINDOW_LENGTH:
            raise ValueError("Iteration-5 process window length must be exactly 12")
        self._open: dict[tuple[str, int, int], _OpenWindow] = {}
        self._closed: list[ProcessWindow] = []
        self._owned_low_rows: set[tuple[int, int]] = set()

    @staticmethod
    def _key(lifecycle_key: str, membership_epoch: int, policy_version: int):
        return str(lifecycle_key), int(membership_epoch), int(policy_version)

    @property
    def closed_windows(self) -> tuple[ProcessWindow, ...]:
        return tuple(self._closed)

    @property
    def open_keys(self) -> tuple[tuple[str, int, int], ...]:
        return tuple(self._open)

    def window_length(
        self, lifecycle_key: str, membership_epoch: int, policy_version: int
    ) -> int:
        window = self._open.get(
            self._key(lifecycle_key, membership_epoch, policy_version)
        )
        return 0 if window is None else len(window.linked_low_row_indices)

    def open_window(
        self,
        *,
        lifecycle_key: str,
        membership_epoch: int,
        policy_version: int,
        skill: int,
        start_observation: Any,
        start_actor_hidden: Any,
        start_process_state: float,
    ) -> None:
        key = self._key(lifecycle_key, membership_epoch, policy_version)
        lifecycle = (key[0], key[1])
        if key[1] < 0 or key[2] < 0 or int(skill) < 0:
            raise ValueError("process-window epoch, policy version and skill must be non-negative")
        if key in self._open or any(
            (open_key[0], open_key[1]) == lifecycle for open_key in self._open
        ):
            raise RuntimeError("process lifecycle already owns an open window")
        observation = _detached_float_vector(
            start_observation, name="start observation"
        )
        hidden = _detached_float_vector(
            start_actor_hidden, name="start actor hidden"
        )
        state = float(start_process_state)
        if not np.isfinite(state):
            raise ValueError("process state must be finite")
        self._open[key] = _OpenWindow(
            lifecycle_key=str(lifecycle_key),
            membership_epoch=int(membership_epoch),
            policy_version=int(policy_version),
            skill=int(skill),
            linked_low_row_indices=[],
            start_observation=observation.copy(),
            start_actor_hidden=hidden.copy(),
            process_state_sequence=[state],
        )

    def observe_transition(
        self,
        *,
        lifecycle_key: str,
        membership_epoch: int,
        policy_version: int,
        low_row_index: int,
        post_process_state: float,
    ) -> None:
        key = self._key(lifecycle_key, membership_epoch, policy_version)
        window = self._open.get(key)
        if window is None:
            raise RuntimeError("process transition has no open lifecycle window")
        index = int(low_row_index)
        owner = (int(policy_version), index)
        if index < 0:
            raise ValueError("semantic low-row index must be non-negative")
        if owner in self._owned_low_rows:
            raise RuntimeError("one low transition cannot belong to two process windows")
        if len(window.linked_low_row_indices) >= self.max_window_length:
            raise RuntimeError("process window exceeded the frozen active-step limit")
        state = float(post_process_state)
        if not np.isfinite(state):
            raise ValueError("post process state must be finite")
        window.linked_low_row_indices.append(index)
        window.process_state_sequence.append(state)
        self._owned_low_rows.add(owner)

    def close_window(
        self, lifecycle_key: str, membership_epoch: int, policy_version: int
    ) -> ProcessWindow | None:
        key = self._key(lifecycle_key, membership_epoch, policy_version)
        window = self._open.pop(key, None)
        if window is None:
            return None
        closed = window.close()
        self._closed.append(closed)
        return closed

    def apply_event_boundary(
        self,
        *,
        lifecycle_key: str,
        membership_epoch: int,
        policy_version: int,
        action_kind: str,
        next_skill: int,
        observation: Any,
        actor_hidden: Any,
        process_state: float,
    ) -> None:
        key = self._key(lifecycle_key, membership_epoch, policy_version)
        kind = str(action_kind).upper()
        if kind == "KEEP":
            window = self._open.get(key)
            if window is None:
                raise RuntimeError("KEEP cannot create a missing process window")
            if int(next_skill) != int(window.skill):
                raise RuntimeError("KEEP must preserve the incumbent process skill")
            return
        if kind != "SET":
            raise ValueError("process event action kind must be KEEP or SET")
        incumbent = self._open.get(key)
        if incumbent is not None and int(next_skill) == int(incumbent.skill):
            raise RuntimeError("SET must replace the incumbent process skill")
        self.close_window(*key)
        self.open_window(
            lifecycle_key=key[0],
            membership_epoch=key[1],
            policy_version=key[2],
            skill=int(next_skill),
            start_observation=observation,
            start_actor_hidden=actor_hidden,
            start_process_state=process_state,
        )

    def roll_full_window(
        self,
        *,
        lifecycle_key: str,
        membership_epoch: int,
        policy_version: int,
        observation: Any,
        actor_hidden: Any,
        process_state: float,
    ) -> bool:
        key = self._key(lifecycle_key, membership_epoch, policy_version)
        window = self._open.get(key)
        if window is None or len(window.linked_low_row_indices) < self.max_window_length:
            return False
        if len(window.linked_low_row_indices) != self.max_window_length:
            raise RuntimeError("process window cannot roll after exceeding its limit")
        skill = int(window.skill)
        self.close_window(*key)
        self.open_window(
            lifecycle_key=key[0],
            membership_epoch=key[1],
            policy_version=key[2],
            skill=skill,
            start_observation=observation,
            start_actor_hidden=actor_hidden,
            start_process_state=process_state,
        )
        return True

    def apply_lifecycle_boundary(
        self,
        *,
        lifecycle_key: str,
        membership_epoch: int,
        policy_version: int,
        boundary_kind: str,
    ) -> None:
        if str(boundary_kind) not in {
            "TEMPORARY_LEAVE",
            "TERMINAL_LEAVE",
            "ROLLOUT_TRUNCATION",
            "EPISODE_TERMINAL",
        }:
            raise ValueError("unsupported process lifecycle boundary")
        self.close_window(lifecycle_key, membership_epoch, policy_version)

    def close_rollout(self) -> None:
        for key in tuple(self._open):
            self.close_window(*key)

    def drain_closed_windows(self) -> tuple[ProcessWindow, ...]:
        """Consume one completed rollout without carrying row indices forward."""

        if self._open:
            raise RuntimeError("cannot drain process windows before closing the rollout")
        windows = tuple(self._closed)
        self._closed.clear()
        self._owned_low_rows.clear()
        return windows

    def state_dict(self) -> dict[str, Any]:
        def encode(window: ProcessWindow | _OpenWindow) -> dict[str, Any]:
            linked = (
                window.linked_low_row_indices
                if isinstance(window.linked_low_row_indices, list)
                else list(window.linked_low_row_indices)
            )
            sequence = (
                window.process_state_sequence
                if isinstance(window.process_state_sequence, list)
                else list(window.process_state_sequence)
            )
            return {
                "lifecycle_key": str(window.lifecycle_key),
                "membership_epoch": int(window.membership_epoch),
                "policy_version": int(window.policy_version),
                "skill": int(window.skill),
                "linked_low_row_indices": [int(value) for value in linked],
                "start_observation": np.asarray(window.start_observation).tolist(),
                "start_actor_hidden": np.asarray(window.start_actor_hidden).tolist(),
                "process_state_sequence": [float(value) for value in sequence],
            }

        return {
            "schema_version": 1,
            "max_window_length": self.max_window_length,
            "open_windows": [encode(window) for window in self._open.values()],
            "closed_windows": [encode(window) for window in self._closed],
            "owned_low_rows": [list(owner) for owner in sorted(self._owned_low_rows)],
        }

    def load_state_dict(self, state: Mapping[str, Any]) -> None:
        value = deepcopy(dict(state))
        required = {
            "schema_version",
            "max_window_length",
            "open_windows",
            "closed_windows",
            "owned_low_rows",
        }
        if set(value) != required or int(value["schema_version"]) != 1:
            raise ValueError("process-window ledger schema mismatch")
        if int(value["max_window_length"]) != self.max_window_length:
            raise ValueError("process-window length mismatch")

        def decode(row: Mapping[str, Any]) -> _OpenWindow:
            item = dict(row)
            if set(item) != {
                "lifecycle_key",
                "membership_epoch",
                "policy_version",
                "skill",
                "linked_low_row_indices",
                "start_observation",
                "start_actor_hidden",
                "process_state_sequence",
            }:
                raise ValueError("process-window row schema mismatch")
            normalized = ProcessWindow(
                lifecycle_key=str(item["lifecycle_key"]),
                membership_epoch=int(item["membership_epoch"]),
                policy_version=int(item["policy_version"]),
                skill=int(item["skill"]),
                linked_low_row_indices=tuple(
                    int(x) for x in item["linked_low_row_indices"]
                ),
                start_observation=item["start_observation"],
                start_actor_hidden=item["start_actor_hidden"],
                process_state_sequence=tuple(
                    float(x) for x in item["process_state_sequence"]
                ),
            )
            return _OpenWindow(
                lifecycle_key=normalized.lifecycle_key,
                membership_epoch=normalized.membership_epoch,
                policy_version=normalized.policy_version,
                skill=normalized.skill,
                linked_low_row_indices=list(normalized.linked_low_row_indices),
                start_observation=normalized.start_observation.copy(),
                start_actor_hidden=normalized.start_actor_hidden.copy(),
                process_state_sequence=list(normalized.process_state_sequence),
            )

        decoded_open: dict[tuple[str, int, int], _OpenWindow] = {}
        active_lifecycles: set[tuple[str, int]] = set()
        for row in value["open_windows"]:
            window = decode(row)
            key = self._key(
                window.lifecycle_key, window.membership_epoch, window.policy_version
            )
            lifecycle = (window.lifecycle_key, window.membership_epoch)
            if key in decoded_open or lifecycle in active_lifecycles:
                raise ValueError("duplicate open process window")
            decoded_open[key] = window
            active_lifecycles.add(lifecycle)
        decoded_closed = [decode(row).close() for row in value["closed_windows"]]
        decoded_owners: set[tuple[int, int]] = set()
        for row in value["owned_low_rows"]:
            if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
                raise ValueError("process-window ownership row schema mismatch")
            pair = tuple(int(item) for item in row)
            if len(pair) != 2 or pair[0] < 0 or pair[1] < 0:
                raise ValueError("process-window ownership row is invalid")
            if pair in decoded_owners:
                raise ValueError("duplicate process-window ownership row")
            decoded_owners.add(pair)
        expected_owners: set[tuple[int, int]] = set()
        for window in (*decoded_open.values(), *decoded_closed):
            for index in window.linked_low_row_indices:
                owner = (int(window.policy_version), int(index))
                if owner in expected_owners:
                    raise ValueError("one restored low row belongs to two process windows")
                expected_owners.add(owner)
        if decoded_owners != expected_owners:
            raise ValueError("process-window ownership state mismatch")
        self._open = decoded_open
        self._closed = decoded_closed
        self._owned_low_rows = decoded_owners


class ConditionalProcessPosterior(nn.Module):
    """Shared context/null classifier plus masked local-process GRU."""

    def __init__(
        self,
        observation_dim: int,
        actor_hidden_dim: int,
        n_skills: int,
        hidden_dim: int = 32,
    ) -> None:
        super().__init__()
        self.observation_dim = int(observation_dim)
        self.actor_hidden_dim = int(actor_hidden_dim)
        self.n_skills = int(n_skills)
        self.hidden_dim = int(hidden_dim)
        if self.observation_dim <= 0 or self.actor_hidden_dim <= 0 or self.hidden_dim <= 0:
            raise ValueError("process-posterior dimensions must be positive")
        if self.n_skills != PROCESS_SKILL_COUNT:
            raise ValueError("Iteration-5 process posterior requires exactly three skills")
        self.context_tower = nn.Sequential(
            nn.Linear(self.observation_dim + self.actor_hidden_dim + 1, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.Tanh(),
        )
        self.process_gru = nn.GRU(2, self.hidden_dim, batch_first=True)
        self.skill_classifier = nn.Linear(self.hidden_dim, self.n_skills)

    def forward(
        self,
        start_observation: torch.Tensor,
        start_actor_hidden: torch.Tensor,
        process_features: torch.Tensor,
        valid_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        parameter = next(self.parameters())
        start_observation = start_observation.detach().to(
            device=parameter.device, dtype=parameter.dtype
        )
        start_actor_hidden = start_actor_hidden.detach().to(
            device=parameter.device, dtype=parameter.dtype
        )
        process_features = process_features.detach().to(
            device=parameter.device, dtype=parameter.dtype
        )
        valid_mask = valid_mask.detach().to(device=parameter.device)
        if process_features.ndim != 3 or process_features.shape[-1] != 2:
            raise ValueError("process posterior requires [batch,time,2] input")
        if process_features.shape[1] > PROCESS_WINDOW_LENGTH:
            raise ValueError("process posterior window exceeds the frozen length")
        if valid_mask.shape != process_features.shape[:2]:
            raise ValueError("process posterior mask shape mismatch")
        if start_observation.ndim != 2 or start_observation.shape != (
            process_features.shape[0],
            self.observation_dim,
        ):
            raise ValueError("process posterior start-observation shape mismatch")
        if start_actor_hidden.ndim != 2 or start_actor_hidden.shape != (
            process_features.shape[0],
            self.actor_hidden_dim,
        ):
            raise ValueError("process posterior start-hidden shape mismatch")
        if not bool(torch.isfinite(start_observation).all()) or not bool(
            torch.isfinite(start_actor_hidden).all()
        ) or not bool(torch.isfinite(process_features).all()):
            raise ValueError("process posterior inputs must be finite")
        if valid_mask.dtype != torch.bool:
            if not bool(((valid_mask == 0) | (valid_mask == 1)).all()):
                raise ValueError("process posterior mask must be binary")
            valid_mask = valid_mask.to(dtype=torch.bool)
        lengths = valid_mask.sum(dim=1).long()
        if bool((lengths <= 0).any()):
            raise ValueError("posterior training/scoring requires non-empty windows")
        prefix_mask = (
            torch.arange(process_features.shape[1], device=parameter.device)
            .unsqueeze(0)
            .expand(process_features.shape[0], -1)
            < lengths.unsqueeze(1)
        )
        if not torch.equal(valid_mask, prefix_mask):
            raise ValueError("process posterior mask must be a contiguous valid prefix")
        length_feature = (
            lengths.to(process_features.dtype).unsqueeze(-1)
            / float(PROCESS_WINDOW_LENGTH)
        )
        context = self.context_tower(
            torch.cat((start_observation, start_actor_hidden, length_feature), dim=-1)
        )
        packed = nn.utils.rnn.pack_padded_sequence(
            process_features,
            lengths.detach().cpu(),
            batch_first=True,
            enforce_sorted=False,
        )
        _rows, hidden = self.process_gru(packed)
        process = hidden[-1]
        null_logits = self.skill_classifier(context)
        full_logits = self.skill_classifier(context + process)
        return full_logits, null_logits


def _window_batch(
    windows: Sequence[ProcessWindow], *, device: torch.device, n_skills: int
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    rows = tuple(window for window in windows if window.valid_length > 0)
    if not rows:
        raise ValueError("process posterior requires at least one non-empty window")
    max_length = max(window.valid_length for window in rows)
    if max_length > PROCESS_WINDOW_LENGTH:
        raise ValueError("process posterior window exceeds the frozen length")
    if any(not 0 <= int(window.skill) < int(n_skills) for window in rows):
        raise ValueError("process window contains an out-of-range skill")
    observation_array = np.stack(
        [window.start_observation for window in rows]
    ).astype(np.float32, copy=False)
    hidden_array = np.stack(
        [window.start_actor_hidden for window in rows]
    ).astype(np.float32, copy=False)
    process_array = np.zeros((len(rows), max_length, 2), dtype=np.float32)
    mask_array = np.zeros((len(rows), max_length), dtype=np.bool_)
    for index, window in enumerate(rows):
        process_array[index, : window.valid_length] = window.process_features()
        mask_array[index, : window.valid_length] = True
    observation = torch.as_tensor(
        observation_array, dtype=torch.float32, device=device
    ).detach()
    hidden = torch.as_tensor(hidden_array, dtype=torch.float32, device=device).detach()
    process = torch.as_tensor(
        process_array, dtype=torch.float32, device=device
    ).detach()
    mask = torch.as_tensor(mask_array, dtype=torch.bool, device=device).detach()
    skills = torch.as_tensor(
        np.asarray([window.skill for window in rows], dtype=np.int64),
        dtype=torch.long,
        device=device,
    ).detach()
    return observation, hidden, process, mask, skills


@dataclass(frozen=True)
class PackedProcessWindows:
    """One immutable, device-resident view of a closed-window collection."""

    source_count: int
    source_indices: tuple[int, ...]
    strata: tuple[tuple[int, int, tuple[int, ...]], ...]
    observation: torch.Tensor
    hidden: torch.Tensor
    process: torch.Tensor
    mask: torch.Tensor
    skills: torch.Tensor

    @property
    def row_count(self) -> int:
        return len(self.source_indices)


class ProcessSemanticTrainer:
    def __init__(
        self,
        posterior: ConditionalProcessPosterior,
        *,
        beta: float,
        device: str | torch.device,
        learning_rate: float = 3e-4,
        sampler_seed: int = 57_057,
    ) -> None:
        self.device = torch.device(device)
        self.online = posterior.to(self.device)
        self.frozen = deepcopy(posterior).to(self.device)
        self.frozen.requires_grad_(False)
        self.frozen.eval()
        self.optimizer = torch.optim.Adam(self.online.parameters(), lr=float(learning_rate))
        self.beta = float(beta)
        if self.beta not in (0.0, 0.05):
            raise ValueError("Iteration-5 beta must be exactly 0 or 0.05")
        self.semantic_ready = False
        self.sampler_rng = np.random.Generator(
            np.random.PCG64(np.random.SeedSequence([int(sampler_seed)]))
        )
        self.posterior_steps = 0

    def pack_closed_windows(
        self, windows: Sequence[ProcessWindow]
    ) -> PackedProcessWindows:
        source_count = len(windows)
        valid_rows = tuple(
            (index, window)
            for index, window in enumerate(windows)
            if window.valid_length > 0
        )
        if not valid_rows:
            return PackedProcessWindows(
                source_count=source_count,
                source_indices=(),
                strata=(),
                observation=torch.empty(
                    (0, self.online.observation_dim),
                    dtype=torch.float32,
                    device=self.device,
                ),
                hidden=torch.empty(
                    (0, self.online.actor_hidden_dim),
                    dtype=torch.float32,
                    device=self.device,
                ),
                process=torch.empty(
                    (0, 0, 2), dtype=torch.float32, device=self.device
                ),
                mask=torch.empty((0, 0), dtype=torch.bool, device=self.device),
                skills=torch.empty((0,), dtype=torch.long, device=self.device),
            )
        source_indices = tuple(int(index) for index, _window in valid_rows)
        valid_windows = tuple(window for _index, window in valid_rows)
        observation, hidden, process, mask, skills = _window_batch(
            valid_windows, device=self.device, n_skills=self.online.n_skills
        )
        by_key: dict[tuple[int, int], list[int]] = {}
        for packed_index, window in enumerate(valid_windows):
            by_key.setdefault((int(window.skill), int(window.valid_length)), []).append(
                int(packed_index)
            )
        strata = tuple(
            (int(skill), int(valid_length), tuple(int(index) for index in by_key[key]))
            for key in sorted(by_key)
            for skill, valid_length in (key,)
        )
        return PackedProcessWindows(
            source_count=source_count,
            source_indices=source_indices,
            strata=strata,
            observation=observation,
            hidden=hidden,
            process=process,
            mask=mask,
            skills=skills,
        )

    def score_closed_windows(
        self, packed: PackedProcessWindows
    ) -> tuple[float, ...]:
        scores = np.zeros(int(packed.source_count), dtype=np.float64)
        if not self.semantic_ready or packed.row_count == 0:
            return tuple(float(value) for value in scores)
        with torch.no_grad():
            full, null = self.frozen(
                packed.observation, packed.hidden, packed.process, packed.mask
            )
            full_logp = F.log_softmax(full, dim=-1)
            null_logp = F.log_softmax(null, dim=-1)
            row = torch.arange(packed.row_count, device=self.device)
            values = torch.clamp(
                (full_logp[row, packed.skills] - null_logp[row, packed.skills])
                / math.log(float(PROCESS_SKILL_COUNT)),
                -1.0,
                1.0,
            )
        for index, value in zip(
            packed.source_indices, values.detach().cpu().numpy()
        ):
            scores[index] = float(value)
        return tuple(float(value) for value in scores)

    def apply_low_rewards(
        self,
        low_rows: MutableSequence[Any],
        windows: Sequence[ProcessWindow],
        scores: Sequence[float],
    ) -> int:
        if len(windows) != len(scores):
            raise ValueError("one semantic score is required per process window")
        assignments: list[tuple[Any, float]] = []
        seen: set[int] = set()
        for window, score in zip(windows, scores):
            score_value = float(score)
            if not np.isfinite(score_value) or not -1.0 <= score_value <= 1.0:
                raise ValueError("semantic score must be finite and clipped to [-1, 1]")
            if window.valid_length <= 0:
                continue
            reward = self.beta * score_value / float(window.valid_length)
            for index in window.linked_low_row_indices:
                if index in seen or not 0 <= int(index) < len(low_rows):
                    raise RuntimeError("semantic low-row ownership is invalid")
                row = low_rows[int(index)]
                if (
                    str(row.lifecycle_key) != window.lifecycle_key
                    or int(row.membership_epoch) != window.membership_epoch
                    or int(row.policy_version) != window.policy_version
                    or int(row.skill) != window.skill
                    or row.reward is None
                ):
                    raise RuntimeError("semantic window does not match its low transition")
                base_reward = float(row.reward)
                if not np.isfinite(base_reward):
                    raise RuntimeError("semantic low transition has a non-finite reward")
                assignments.append((row, base_reward + reward))
                seen.add(int(index))
        if len(seen) != len(low_rows):
            raise RuntimeError("every low transition must belong to exactly one process window")
        if self.beta == 0.0 or not self.semantic_ready:
            return 0
        for row, reward in assignments:
            row.reward = float(reward)
        return len(assignments)

    def _balanced_indices(self, packed: PackedProcessWindows) -> np.ndarray:
        if not packed.strata:
            return np.empty((0,), dtype=np.int64)
        skills = tuple(range(self.online.n_skills))
        if {skill for skill, _length, _rows in packed.strata} != set(skills):
            # A rollout without all skills has no balanced posterior update.
            return np.empty((0,), dtype=np.int64)
        # Joint stratification prevents either a frequent skill or a frequent
        # valid length from dominating the posterior minibatch.  Missing joint
        # strata remain visible to the explicitly trained context null rather
        # than being synthesized or relabelled.
        count = min(len(rows) for _skill, _length, rows in packed.strata)
        selected: list[int] = []
        for _skill, _length, rows in packed.strata:
            order = self.sampler_rng.permutation(len(rows))[:count]
            selected.extend(int(rows[int(index)]) for index in order)
        return np.asarray(selected, dtype=np.int64)

    def update_posterior(
        self, packed: PackedProcessWindows, *, passes: int = 1
    ) -> dict[str, float]:
        pass_count = int(passes)
        if pass_count <= 0:
            raise ValueError("posterior passes must be positive")
        selections = tuple(
            self._balanced_indices(packed) for _pass in range(pass_count)
        )
        if not selections or any(selection.size == 0 for selection in selections):
            return {
                "posterior_loss": 0.0,
                "posterior_steps": 0.0,
                "posterior_windows": 0.0,
            }
        selection_sizes = tuple(int(selection.size) for selection in selections)
        flat_indices = torch.as_tensor(
            np.concatenate(selections), dtype=torch.long, device=self.device
        )
        self.online.train()
        final_loss: torch.Tensor | None = None
        offset = 0
        executed = 0
        for selection_size in selection_sizes:
            indices = flat_indices[offset : offset + selection_size]
            offset += selection_size
            full, null = self.online(
                packed.observation.index_select(0, indices),
                packed.hidden.index_select(0, indices),
                packed.process.index_select(0, indices),
                packed.mask.index_select(0, indices),
            )
            selected_skills = packed.skills.index_select(0, indices)
            loss = F.cross_entropy(full, selected_skills) + F.cross_entropy(
                null, selected_skills
            )
            if not bool(torch.isfinite(loss)):
                raise RuntimeError("process posterior produced a non-finite loss")
            self.optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.online.parameters(), 0.5)
            self.optimizer.step()
            self.posterior_steps += 1
            executed += 1
            final_loss = loss.detach()
        if executed != pass_count or final_loss is None:
            raise RuntimeError("process posterior did not execute every requested pass")
        self.frozen.load_state_dict(self.online.state_dict(), strict=True)
        self.frozen.requires_grad_(False)
        self.frozen.eval()
        self.semantic_ready = True
        return {
            "posterior_loss": float(final_loss.cpu()),
            "posterior_steps": float(executed),
            "posterior_windows": float(selection_sizes[-1]),
        }

    def state_dict(self) -> dict[str, Any]:
        return {
            "online": deepcopy(self.online.state_dict()),
            "frozen": deepcopy(self.frozen.state_dict()),
            "optimizer": deepcopy(self.optimizer.state_dict()),
            "semantic_ready": bool(self.semantic_ready),
            "sampler_rng_state": deepcopy(self.sampler_rng.bit_generator.state),
            "posterior_steps": int(self.posterior_steps),
            "beta": float(self.beta),
        }

    def load_state_dict(self, state: Mapping[str, Any]) -> None:
        value = deepcopy(dict(state))
        required = {
            "online",
            "frozen",
            "optimizer",
            "semantic_ready",
            "sampler_rng_state",
            "posterior_steps",
            "beta",
        }
        if set(value) != required or float(value["beta"]) != self.beta:
            raise ValueError("semantic trainer state mismatch")
        posterior_steps = int(value["posterior_steps"])
        semantic_ready = bool(value["semantic_ready"])
        if posterior_steps < 0 or semantic_ready != (posterior_steps > 0):
            raise ValueError("semantic trainer readiness/counter state mismatch")
        candidate_rng = np.random.Generator(np.random.PCG64())
        try:
            candidate_rng.bit_generator.state = deepcopy(value["sampler_rng_state"])
        except (TypeError, ValueError) as error:
            raise ValueError("semantic sampler RNG state mismatch") from error
        self.online.load_state_dict(value["online"], strict=True)
        self.frozen.load_state_dict(value["frozen"], strict=True)
        self.frozen.requires_grad_(False)
        self.frozen.eval()
        self.optimizer.load_state_dict(value["optimizer"])
        for state_row in self.optimizer.state.values():
            for key, item in state_row.items():
                if isinstance(item, torch.Tensor):
                    state_row[key] = item.to(self.device)
        self.semantic_ready = semantic_ready
        self.sampler_rng.bit_generator.state = deepcopy(candidate_rng.bit_generator.state)
        self.posterior_steps = posterior_steps


def snapshot_event_semantic_bundle(
    *,
    trainer: ProcessSemanticTrainer,
    ledgers: Sequence[ProcessWindowLedger],
    intrinsic_applied_count: int,
) -> dict[str, Any]:
    count = int(intrinsic_applied_count)
    if count < 0:
        raise ValueError("semantic bundle intrinsic counter is invalid")
    return {
        "event_semantic_schema_version": EVENT_SEMANTIC_SCHEMA_VERSION,
        "trainer": trainer.state_dict(),
        "window_ledgers": [ledger.state_dict() for ledger in ledgers],
        "intrinsic_applied_count": count,
    }


def restore_event_semantic_bundle(
    bundle: Mapping[str, Any],
    *,
    trainer: ProcessSemanticTrainer,
    ledgers: Sequence[ProcessWindowLedger],
) -> int:
    value = deepcopy(dict(bundle))
    required = {
        "event_semantic_schema_version",
        "trainer",
        "window_ledgers",
        "intrinsic_applied_count",
    }
    if set(value) != required or int(
        value.get("event_semantic_schema_version", -1)
    ) != EVENT_SEMANTIC_SCHEMA_VERSION:
        raise ValueError("semantic bundle schema mismatch")
    rows = list(value["window_ledgers"])
    if len(rows) != len(ledgers):
        raise ValueError("semantic bundle ledger count mismatch")
    count = int(value["intrinsic_applied_count"])
    if count < 0:
        raise ValueError("semantic bundle intrinsic counter is invalid")
    # Validate every ledger before mutating any live runtime object.
    for ledger, state in zip(ledgers, rows):
        candidate = ProcessWindowLedger(max_window_length=ledger.max_window_length)
        candidate.load_state_dict(state)
    trainer.load_state_dict(value["trainer"])
    for ledger, state in zip(ledgers, rows):
        ledger.load_state_dict(state)
    return count


def reject_unexpected_event_semantic_bundle(
    payload: Mapping[str, Any], *, iteration5_mode: bool
) -> None:
    present = "event_semantic" in payload
    if iteration5_mode and not present:
        raise ValueError("Iteration-5 checkpoint is missing semantic bundle")
    if not iteration5_mode and present:
        raise ValueError("non-Iteration-5 checkpoint rejects semantic bundle")
