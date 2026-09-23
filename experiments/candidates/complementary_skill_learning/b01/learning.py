"""Candidate-local learner for complementary-skill-learning B01.

The native learner remains the owner of acting, PPO, discriminator training and
recurrent storage.  This adapter changes only the individual high-level law to
the prospectively fixed full-support mixture and adds the two train-only return
heads fed by factual ten-step windows.
"""

from __future__ import annotations

import copy
import hashlib
import math
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from hmasd.agent import HMASDAgent
from hmasd.networks import SkillDecoder


MIXTURE_POLICY_WEIGHT = 0.9
MIXTURE_UNIFORM_WEIGHT = 0.1
AUXILIARY_DISCOUNT = 0.99
AUXILIARY_HORIZON = 10
AUXILIARY_BATCH_SIZE = 128
AUXILIARY_GRADIENT_SCALE = 0.05
AUXILIARY_LEARNING_RATE = 3e-4
AUXILIARY_ADAM_EPS = 1e-5
AUXILIARY_MAX_GRAD_NORM = 0.5
CONTEXT_WIDTH = 64
UNARY_WIDTH = 64
PAIR_RANK = 32


class MixtureSkillDecoder(SkillDecoder):
    """Return ``log(mu)`` for individual tokens after the native clamp.

    ``Categorical(logits=...)`` therefore uses the same full-support law for
    collection, deterministic decoding, held-skill gap checks and ordered PPO
    replay.  Step zero is the unchanged native team distribution.
    """

    def forward(self, *args: Any, **kwargs: Any) -> torch.Tensor:
        logits = super().forward(*args, **kwargs)
        step = kwargs.get("step", args[4] if len(args) > 4 else 0)
        if int(step) == 0:
            return logits
        n_labels = logits.shape[-1]
        log_pi = F.log_softmax(logits, dim=-1)
        log_policy = log_pi + math.log(MIXTURE_POLICY_WEIGHT)
        log_uniform = torch.full_like(
            log_pi, math.log(MIXTURE_UNIFORM_WEIGHT / float(n_labels))
        )
        return torch.logaddexp(log_policy, log_uniform)


class _StructuredPHead(nn.Module):
    """Context baseline plus identity-aware unary and rank-32 pair means."""

    def __init__(self, context_dim: int, embedding_dim: int, n_agents: int):
        super().__init__()
        self.n_agents = int(n_agents)
        self.context = nn.Sequential(
            nn.Linear(context_dim, CONTEXT_WIDTH),
            nn.SiLU(),
            nn.Linear(CONTEXT_WIDTH, CONTEXT_WIDTH),
            nn.SiLU(),
        )
        self.baseline = nn.Linear(CONTEXT_WIDTH, 1)
        item_dim = CONTEXT_WIDTH + embedding_dim + self.n_agents
        self.unary = nn.Sequential(
            nn.Linear(item_dim, UNARY_WIDTH),
            nn.SiLU(),
            nn.Linear(UNARY_WIDTH, 1),
        )
        self.pair_left = nn.Linear(item_dim, PAIR_RANK)
        self.pair_right = nn.Linear(item_dim, PAIR_RANK)

    def forward(self, context: torch.Tensor, embeddings: torch.Tensor) -> torch.Tensor:
        batch, n_agents, _ = embeddings.shape
        if n_agents != self.n_agents:
            raise ValueError(f"P head expected {self.n_agents} agents, got {n_agents}")
        contextual = self.context(context)
        identities = torch.eye(
            n_agents, dtype=embeddings.dtype, device=embeddings.device
        ).unsqueeze(0).expand(batch, -1, -1)
        items = torch.cat(
            [contextual.unsqueeze(1).expand(-1, n_agents, -1), embeddings, identities],
            dim=-1,
        )
        unary_mean = self.unary(items).squeeze(-1).mean(dim=1)
        left = self.pair_left(items)
        right = self.pair_right(items)
        pair_terms = []
        scale = math.sqrt(float(PAIR_RANK))
        for i in range(n_agents):
            for j in range(i + 1, n_agents):
                symmetric = (
                    (left[:, i] * right[:, j]).sum(dim=-1)
                    + (left[:, j] * right[:, i]).sum(dim=-1)
                ) / (2.0 * scale)
                pair_terms.append(symmetric)
        pair_mean = torch.stack(pair_terms, dim=1).mean(dim=1)
        return self.baseline(contextual).squeeze(-1) + unary_mean + pair_mean


class _GeneralGHead(nn.Module):
    """Ordinary two-hidden-layer MLP over the same ordered information."""

    def __init__(self, input_dim: int, width: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, width),
            nn.SiLU(),
            nn.Linear(width, width),
            nn.SiLU(),
            nn.Linear(width, 1),
        )

    def forward(self, context: torch.Tensor, embeddings: torch.Tensor) -> torch.Tensor:
        full_input = torch.cat([context, embeddings.flatten(start_dim=1)], dim=-1)
        return self.network(full_input).squeeze(-1)


def _parameter_count(module: nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters())


def _matched_g_width(input_dim: int, target_parameters: int) -> int:
    """Choose the integer width closest to P's count before any result exists."""

    def count(width: int) -> int:
        return input_dim * width + width + width * width + width + width + 1

    # The positive quadratic root is only a starting point; inspect neighboring
    # integers because parameter count is discrete.
    linear = input_dim + 3
    root = max(1, int((-linear + math.sqrt(linear * linear + 4 * target_parameters)) / 2))
    candidates = range(max(1, root - 4), root + 6)
    return min(candidates, key=lambda width: (abs(count(width) - target_parameters), width))


def _tensor_digest(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
        digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _module_snapshot(parameters: list[torch.nn.Parameter]) -> list[torch.Tensor]:
    return [parameter.detach().clone() for parameter in parameters]


def _relative_movement(
    parameters: list[torch.nn.Parameter], before: list[torch.Tensor]
) -> float:
    with torch.no_grad():
        delta_sq = sum(
            ((parameter.detach() - initial).double() ** 2).sum()
            for parameter, initial in zip(parameters, before)
        )
        base_sq = sum(initial.double().square().sum() for initial in before)
        denominator = torch.sqrt(base_sq).item()
        numerator = torch.sqrt(delta_sq).item()
    return float(numerator / max(denominator, 1e-12))


class ComplementaryAgent(HMASDAgent):
    """Native HMASD with the fixed B01 mixture law and auxiliary heads."""

    def __init__(
        self,
        config: Any,
        arm: str,
        head_seed: int,
        aux_seed: int,
        log_dir: str,
        device: torch.device | str | None,
    ) -> None:
        arm = str(arm).upper()
        if arm not in {"D", "G", "P"}:
            raise ValueError("arm must be one of D, G or P")
        if bool(getattr(config, "use_obsnorm", False)) or bool(
            getattr(config, "use_statenorm", False)
        ):
            raise ValueError("B01 requires observation and state normalizers to be disabled")
        if str(getattr(config, "policy_interruption_mode", "off")) != "d2":
            raise ValueError("B01 requires the native D2 path")
        if math.isfinite(float(getattr(config, "interruption_cost_c", float("inf")))):
            raise ValueError("B01 requires infinite individual interruption cost")
        if math.isfinite(float(getattr(config, "interruption_cost_c_Z", float("inf")))):
            raise ValueError("B01 requires infinite team interruption cost")
        if int(getattr(config, "skill_cap_k_max", -1)) != AUXILIARY_HORIZON:
            raise ValueError("B01 requires skill_cap_k_max=10")
        if int(getattr(config, "team_cap_k_Z", -1)) != AUXILIARY_HORIZON:
            raise ValueError("B01 requires team_cap_k_Z=10")

        super().__init__(config, log_dir=log_dir, device=device)
        if self.skill_discoverer.actor_context_adapter is not None or bool(
            getattr(self.skill_discoverer, "use_central_snapshot", False)
        ):
            raise ValueError("B01 does not permit an actor context or central-input adapter")
        if int(config.n_agents) < 2:
            raise ValueError("the pair head requires at least two agents")
        if int(config.n_z) != 6 or int(config.n_Z) != 6:
            raise ValueError("B01 requires all six team and individual labels")

        self.arm = arm
        self.head_seed = int(head_seed)
        self.aux_seed = int(aux_seed)
        self._install_mixture_decoder()

        self._shuffle_rng = np.random.Generator(np.random.PCG64(self.aux_seed))
        self._pending_windows: dict[int, dict[str, Any]] = {}
        self._auxiliary_samples: list[dict[str, Any]] = []
        self._auxiliary_consumed = False
        self._discarded_terminal_windows = 0
        self._pending_replay_telemetry: dict[str, Any] | None = None
        self.auxiliary_history: list[dict[str, Any]] = []
        self.target_mean: float | None = None
        self.target_std: float | None = None
        self.first_rollout_target_sha256: str | None = None

        self._build_auxiliary_modules()

    def _install_mixture_decoder(self) -> None:
        decoder = self.skill_coordinator.skill_decoder
        if not isinstance(decoder, SkillDecoder):
            raise TypeError("native coordinator does not expose a SkillDecoder")
        # Reclassifying the already initialized module introduces no parameters,
        # state-dict keys or RNG draws.
        decoder.__class__ = MixtureSkillDecoder

    def _build_auxiliary_modules(self) -> None:
        n_agents = int(self.config.n_agents)
        state_dim = int(self.config.state_dim)
        obs_dim = int(self.config.obs_dim)
        hidden_dim = int(self.config.gru_hidden_size)
        context_dim = state_dim + n_agents * obs_dim + n_agents * hidden_dim + 1 + int(self.config.n_Z)
        g_input_dim = context_dim + n_agents * hidden_dim

        cpu_rng_state = torch.random.get_rng_state()
        try:
            torch.random.default_generator.manual_seed(self.head_seed)
            p_head = _StructuredPHead(context_dim, hidden_dim, n_agents)
            p_count = _parameter_count(p_head)
            self.G_width = _matched_g_width(g_input_dim, p_count)
            g_head = _GeneralGHead(g_input_dim, self.G_width)
        finally:
            torch.random.set_rng_state(cpu_rng_state)

        self.p_head = p_head.to(self.device)
        self.g_head = g_head.to(self.device)
        # Both heads receive the same fixed per-row normalization of the raw
        # factual context.  It has no learned state and therefore belongs to
        # neither head optimizer.
        self.context_normalizer = nn.LayerNorm(
            context_dim, elementwise_affine=False
        ).to(self.device)
        self.g_head_optimizer = torch.optim.Adam(
            self.g_head.parameters(), lr=AUXILIARY_LEARNING_RATE,
            eps=AUXILIARY_ADAM_EPS, weight_decay=0.0,
        )
        self.p_head_optimizer = torch.optim.Adam(
            self.p_head.parameters(), lr=AUXILIARY_LEARNING_RATE,
            eps=AUXILIARY_ADAM_EPS, weight_decay=0.0,
        )

        trunk_parameters = self._trunk_parameters()
        self.auxiliary_trunk_optimizer = (
            torch.optim.Adam(
                trunk_parameters, lr=AUXILIARY_LEARNING_RATE,
                eps=AUXILIARY_ADAM_EPS, weight_decay=0.0,
            )
            if self.arm in {"G", "P"}
            else None
        )
        self.parameter_counts = {
            "G": _parameter_count(self.g_head),
            "P": _parameter_count(self.p_head),
            "actor_base": _parameter_count(self.skill_discoverer.actor.base),
            "actor_film": _parameter_count(self.skill_discoverer.actor.film_generator),
            "actor_gru": _parameter_count(self.skill_discoverer.actor.rnn),
        }
        self.parameter_counts["auxiliary_trunk"] = (
            self.parameter_counts["actor_base"]
            + self.parameter_counts["actor_film"]
            + self.parameter_counts["actor_gru"]
        )
        self.auxiliary_architecture = {
            "context_input_dim": context_dim,
            "actor_embedding_dim": hidden_dim,
            "G_input_dim": g_input_dim,
            "G_width": self.G_width,
            "P_context_width": CONTEXT_WIDTH,
            "P_unary_width": UNARY_WIDTH,
            "P_pair_rank": PAIR_RANK,
            "context_normalization": "LayerNorm(elementwise_affine=False)",
            "context_fields": (
                "state", "ordered_joint_observations", "ordered_entering_actor_hidden",
                "step_div_500", "team_skill_onehot",
            ),
        }

    def _trunk_parameter_groups(self) -> dict[str, list[torch.nn.Parameter]]:
        actor = self.skill_discoverer.actor
        return {
            "base": list(actor.base.parameters()),
            "film": list(actor.film_generator.parameters()),
            "gru": list(actor.rnn.parameters()),
        }

    def _trunk_parameters(self) -> list[torch.nn.Parameter]:
        groups = self._trunk_parameter_groups()
        return groups["base"] + groups["film"] + groups["gru"]

    def step(
        self,
        states_batch: np.ndarray,
        observations_batch: np.ndarray,
        env_steps_batch: np.ndarray,
        dones_batch: np.ndarray,
        deterministic: bool = False,
        return_step_data: bool = False,
        build_infos: bool = True,
    ):
        result = super().step(
            states_batch,
            observations_batch,
            env_steps_batch,
            dones_batch,
            deterministic=deterministic,
            return_step_data=return_step_data,
            build_infos=build_infos,
        )
        if not return_step_data:
            return result
        actions, infos, step_data = result
        num_envs = len(states_batch)
        step_data["complementary_steps"] = np.asarray(env_steps_batch, dtype=np.int64).copy()
        step_data["complementary_entering_hidden"] = np.stack(
            [self.get_prev_actor_hidden_np(env_id) for env_id in range(num_envs)], axis=0
        )
        entry = 1.0 - np.asarray(dones_batch, dtype=np.float32).reshape(num_envs, 1)
        step_data["complementary_entry_masks"] = np.repeat(
            entry, int(self.config.n_agents), axis=1
        )
        return actions, infos, step_data

    @staticmethod
    def _raw_scalar_reward(reward: Any) -> float:
        values = np.asarray(reward, dtype=np.float64).reshape(-1)
        if values.size == 0 or not np.isfinite(values).all():
            raise ValueError("raw environment reward must be finite and non-empty")
        if not np.allclose(values, values[0], rtol=0.0, atol=1e-7):
            raise ValueError("B01 requires the factual scalar environment reward")
        return float(values[0])

    def _boundary_record(
        self,
        env_id: int,
        states: np.ndarray,
        observations: np.ndarray,
        step_data: dict[str, Any],
    ) -> dict[str, Any]:
        required = (
            "complementary_steps", "complementary_entering_hidden",
            "complementary_entry_masks", "team_skills", "agent_skills",
        )
        missing = [name for name in required if name not in step_data]
        if missing:
            raise ValueError(f"step_data is missing complementary fields: {missing}")
        return {
            "env_id": int(env_id),
            "state": np.asarray(states[env_id], dtype=np.float32).copy(),
            "observations": np.asarray(observations[env_id], dtype=np.float32).copy(),
            "entering_hidden": np.asarray(
                step_data["complementary_entering_hidden"][env_id], dtype=np.float32
            ).copy(),
            "entry_masks": np.asarray(
                step_data["complementary_entry_masks"][env_id], dtype=np.float32
            ).copy(),
            "step": int(step_data["complementary_steps"][env_id]),
            "team_skill": int(step_data["team_skills"][env_id]),
            "agent_skills": np.asarray(
                step_data["agent_skills"][env_id], dtype=np.int64
            ).copy(),
            "rewards": [],
        }

    def _finish_window(self, record: dict[str, Any]) -> None:
        rewards = np.asarray(record.pop("rewards"), dtype=np.float64)
        powers = np.power(AUXILIARY_DISCOUNT, np.arange(AUXILIARY_HORIZON, dtype=np.float64))
        record["target"] = float(np.dot(powers, rewards))
        self._auxiliary_samples.append(record)

    def _capture_auxiliary_transitions(
        self,
        states: np.ndarray,
        observations: np.ndarray,
        rewards: np.ndarray,
        dones: np.ndarray,
        step_data: dict[str, Any],
    ) -> None:
        num_envs = len(rewards)
        if "d2_team_decision" not in step_data or "d2_sampled_mask" not in step_data:
            raise ValueError("B01 requires native D2 boundary metadata in step_data")
        team_boundary = np.asarray(step_data["d2_team_decision"], dtype=np.bool_)
        sampled_mask = np.asarray(step_data["d2_sampled_mask"], dtype=np.bool_)
        done_rows = np.asarray(dones, dtype=np.bool_).reshape(num_envs, -1).any(axis=1)

        for env_id in range(num_envs):
            if bool(team_boundary[env_id]):
                if not bool(sampled_mask[env_id].all()):
                    raise RuntimeError("a D2 team boundary did not sample every agent")
                if env_id in self._pending_windows:
                    raise RuntimeError("overlapping ten-step auxiliary windows")
                self._pending_windows[env_id] = self._boundary_record(
                    env_id, states, observations, step_data
                )

            pending = self._pending_windows.get(env_id)
            if pending is None:
                continue
            pending["rewards"].append(self._raw_scalar_reward(rewards[env_id]))
            if len(pending["rewards"]) == AUXILIARY_HORIZON:
                self._finish_window(pending)
                del self._pending_windows[env_id]
            elif bool(done_rows[env_id]):
                # A terminal reward is retained above.  A boundary without ten
                # factual same-episode rewards has no valid target and is not
                # allowed to cross into the reset episode.
                self._discarded_terminal_windows += 1
                del self._pending_windows[env_id]

    def store_transition_batch(
        self,
        states: np.ndarray,
        next_states: np.ndarray,
        observations: np.ndarray,
        next_observations: np.ndarray,
        actions: np.ndarray,
        rewards: np.ndarray,
        dones: np.ndarray,
        infos_batch: Any = None,
        rollout_step_idx: int | None = None,
        step_data: dict[str, Any] | None = None,
    ):
        if step_data is None:
            raise ValueError("B01 storage requires step_data")
        self._capture_auxiliary_transitions(
            states, observations, rewards, dones, step_data,
        )
        return super().store_transition_batch(
            states,
            next_states,
            observations,
            next_observations,
            actions,
            rewards,
            dones,
            infos_batch=infos_batch,
            rollout_step_idx=rollout_step_idx,
            step_data=step_data,
        )

    def _stack_samples(self) -> dict[str, np.ndarray]:
        if not self._auxiliary_samples:
            return {}
        return {
            "states": np.stack([row["state"] for row in self._auxiliary_samples]),
            "observations": np.stack([row["observations"] for row in self._auxiliary_samples]),
            "entering_hidden": np.stack([row["entering_hidden"] for row in self._auxiliary_samples]),
            "entry_masks": np.stack([row["entry_masks"] for row in self._auxiliary_samples]),
            "steps": np.asarray([row["step"] for row in self._auxiliary_samples], dtype=np.float32),
            "team_skills": np.asarray([row["team_skill"] for row in self._auxiliary_samples], dtype=np.int64),
            "agent_skills": np.stack([row["agent_skills"] for row in self._auxiliary_samples]),
            "env_ids": np.asarray([row["env_id"] for row in self._auxiliary_samples], dtype=np.int64),
            "targets": np.asarray([row["target"] for row in self._auxiliary_samples], dtype=np.float64),
        }

    def _validate_auxiliary_shapes(
        self,
        states: torch.Tensor,
        observations: torch.Tensor,
        entering_hidden: torch.Tensor,
        entry_masks: torch.Tensor,
        steps: torch.Tensor,
        team_skills: torch.Tensor,
        agent_skills: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        n_agents = int(self.config.n_agents)
        if states.dim() != 2 or states.shape[1] != int(self.config.state_dim):
            raise ValueError("states must have shape (B,state_dim)")
        batch = states.shape[0]
        if observations.shape != (batch, n_agents, int(self.config.obs_dim)):
            raise ValueError("observations must have shape (B,N,obs_dim)")
        if entering_hidden.dim() == 4 and entering_hidden.shape[2] == 1:
            entering_hidden = entering_hidden.squeeze(2)
        if entering_hidden.shape != (batch, n_agents, int(self.config.gru_hidden_size)):
            raise ValueError("entering_hidden must have shape (B,N,H) or (B,N,1,H)")
        if entry_masks.dim() == 3 and entry_masks.shape[-1] == 1:
            entry_masks = entry_masks.squeeze(-1)
        if entry_masks.shape != (batch, n_agents):
            raise ValueError("entry_masks must have shape (B,N) or (B,N,1)")
        if steps.reshape(-1).shape[0] != batch:
            raise ValueError("steps must have shape (B,)")
        if team_skills.reshape(-1).shape[0] != batch:
            raise ValueError("team_skills must have shape (B,)")
        if agent_skills.shape != (batch, n_agents):
            raise ValueError("agent_skills must have shape (B,N)")
        if not bool(torch.isfinite(states).all()) or not bool(torch.isfinite(observations).all()):
            raise ValueError("auxiliary inputs must be finite")
        return entering_hidden, entry_masks

    def _auxiliary_features(
        self,
        states: torch.Tensor,
        observations: torch.Tensor,
        entering_hidden: torch.Tensor,
        entry_masks: torch.Tensor,
        steps: torch.Tensor,
        team_skills: torch.Tensor,
        agent_skills: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        entering_hidden, entry_masks = self._validate_auxiliary_shapes(
            states, observations, entering_hidden, entry_masks, steps,
            team_skills, agent_skills,
        )
        batch, n_agents, _ = observations.shape
        actor = self.skill_discoverer.actor
        obs_flat = observations.reshape(batch * n_agents, -1)
        skill_flat = agent_skills.long().reshape(-1)
        hidden_flat = entering_hidden.reshape(batch * n_agents, -1)
        masks_flat = entry_masks.reshape(batch * n_agents, 1)
        base = actor.base(obs_flat)
        skill_onehot = F.one_hot(skill_flat, num_classes=int(self.config.n_z)).to(base.dtype)
        gamma, beta = torch.chunk(actor.film_generator(skill_onehot), 2, dim=-1)
        film = gamma * base + beta
        embedded, _ = actor.rnn(film, hidden_flat, masks_flat)
        embeddings = embedded.reshape(batch, n_agents, -1)
        context = torch.cat(
            [
                states,
                observations.flatten(start_dim=1),
                entering_hidden.flatten(start_dim=1),
                steps.reshape(-1, 1).to(states.dtype) / 500.0,
                F.one_hot(team_skills.long().reshape(-1), num_classes=int(self.config.n_Z)).to(states.dtype),
            ],
            dim=-1,
        )
        return context, embeddings

    def _head_predictions(
        self,
        states: torch.Tensor,
        observations: torch.Tensor,
        entering_hidden: torch.Tensor,
        entry_masks: torch.Tensor,
        steps: torch.Tensor,
        team_skills: torch.Tensor,
        agent_skills: torch.Tensor,
        *,
        training: bool,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        context, embeddings = self._auxiliary_features(
            states, observations, entering_hidden, entry_masks, steps,
            team_skills, agent_skills,
        )
        context = self.context_normalizer(context)
        detached = embeddings.detach()
        if training and self.arm == "G":
            g_embeddings = detached + AUXILIARY_GRADIENT_SCALE * (embeddings - detached)
        else:
            g_embeddings = detached
        if training and self.arm == "P":
            p_embeddings = detached + AUXILIARY_GRADIENT_SCALE * (embeddings - detached)
        else:
            p_embeddings = detached
        return self.g_head(context, g_embeddings), self.p_head(context, p_embeddings)

    def predict_returns(
        self,
        states: np.ndarray | torch.Tensor,
        observations: np.ndarray | torch.Tensor,
        entering_hidden: np.ndarray | torch.Tensor,
        entry_masks: np.ndarray | torch.Tensor,
        steps: np.ndarray | torch.Tensor,
        team_skills: np.ndarray | torch.Tensor,
        agent_skills: np.ndarray | torch.Tensor,
    ) -> dict[str, np.ndarray] | dict[str, torch.Tensor]:
        if self.target_mean is None or self.target_std is None:
            raise RuntimeError("auxiliary target calibration is not frozen")
        return_tensors = any(
            torch.is_tensor(value)
            for value in (states, observations, entering_hidden, entry_masks, steps, team_skills, agent_skills)
        )
        tensors = [
            torch.as_tensor(value, device=self.device, dtype=dtype)
            for value, dtype in (
                (states, torch.float32), (observations, torch.float32),
                (entering_hidden, torch.float32), (entry_masks, torch.float32),
                (steps, torch.float32), (team_skills, torch.long),
                (agent_skills, torch.long),
            )
        ]
        with torch.no_grad():
            g_normalized, p_normalized = self._head_predictions(*tensors, training=False)
            g_raw = g_normalized * self.target_std + self.target_mean
            p_raw = p_normalized * self.target_std + self.target_mean
        if return_tensors:
            return {"G": g_raw, "P": p_raw}
        return {"G": g_raw.cpu().numpy(), "P": p_raw.cpu().numpy()}

    @staticmethod
    def _grad_norm(parameters: list[torch.nn.Parameter]) -> float:
        squared = sum(
            parameter.grad.detach().double().square().sum()
            for parameter in parameters if parameter.grad is not None
        )
        if isinstance(squared, int):
            return 0.0
        return float(torch.sqrt(squared).item())

    def _batch_tensors(
        self, arrays: dict[str, np.ndarray], indices: np.ndarray
    ) -> list[torch.Tensor]:
        return [
            torch.as_tensor(arrays[name][indices], device=self.device, dtype=dtype)
            for name, dtype in (
                ("states", torch.float32), ("observations", torch.float32),
                ("entering_hidden", torch.float32), ("entry_masks", torch.float32),
                ("steps", torch.float32), ("team_skills", torch.long),
                ("agent_skills", torch.long),
            )
        ]

    def _empty_auxiliary_row(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "samples": 0,
            "head_optimizer_steps": {"G": 0, "P": 0},
            "trunk_optimizer_steps": 0,
            "parameter_counts": dict(self.parameter_counts),
            "architecture": dict(self.auxiliary_architecture),
            "G_width": self.G_width,
            "discarded_terminal_windows": self._discarded_terminal_windows,
        }

    def _run_auxiliary_update(self) -> dict[str, Any]:
        if self._auxiliary_consumed:
            raise RuntimeError("auxiliary samples were already consumed; clear buffers first")
        self._auxiliary_consumed = True
        arrays = self._stack_samples()
        if not arrays:
            return self._empty_auxiliary_row()

        targets_raw = arrays["targets"]
        target_hash = _tensor_digest(targets_raw)
        if self.target_mean is None:
            self.target_mean = float(targets_raw.mean())
            population_std = float(targets_raw.std(ddof=0))
            self.target_std = max(population_std, 1e-6)
            self.first_rollout_target_sha256 = target_hash
        assert self.target_std is not None and self.target_mean is not None
        targets = ((targets_raw - self.target_mean) / self.target_std).astype(np.float32)

        trunk_groups = self._trunk_parameter_groups()
        trunk_parameters = self._trunk_parameters()
        trunk_before = {
            name: _module_snapshot(parameters) for name, parameters in trunk_groups.items()
        }
        order = self._shuffle_rng.permutation(len(targets))
        losses = {"G": [], "P": []}
        gradients = {"G": [], "P": [], "trunk": []}
        clipped = {"G": 0, "P": 0, "trunk": 0}
        optimizer_steps = 0

        for start in range(0, len(order), AUXILIARY_BATCH_SIZE):
            indices = order[start : start + AUXILIARY_BATCH_SIZE]
            batch_inputs = self._batch_tensors(arrays, indices)
            batch_targets = torch.as_tensor(
                targets[indices], dtype=torch.float32, device=self.device
            )
            self.g_head_optimizer.zero_grad(set_to_none=True)
            self.p_head_optimizer.zero_grad(set_to_none=True)
            for parameter in trunk_parameters:
                parameter.grad = None
            if self.auxiliary_trunk_optimizer is not None:
                self.auxiliary_trunk_optimizer.zero_grad(set_to_none=True)

            g_prediction, p_prediction = self._head_predictions(
                *batch_inputs, training=True
            )
            g_loss = F.mse_loss(g_prediction, batch_targets)
            p_loss = F.mse_loss(p_prediction, batch_targets)
            (g_loss + p_loss).backward()

            for name, parameters in (
                ("G", list(self.g_head.parameters())),
                ("P", list(self.p_head.parameters())),
            ):
                norm = self._grad_norm(parameters)
                gradients[name].append(norm)
                clipped[name] += int(norm > AUXILIARY_MAX_GRAD_NORM)
                torch.nn.utils.clip_grad_norm_(parameters, AUXILIARY_MAX_GRAD_NORM)
            trunk_norm = self._grad_norm(trunk_parameters)
            gradients["trunk"].append(trunk_norm)
            clipped["trunk"] += int(trunk_norm > AUXILIARY_MAX_GRAD_NORM)
            if self.auxiliary_trunk_optimizer is not None:
                torch.nn.utils.clip_grad_norm_(trunk_parameters, AUXILIARY_MAX_GRAD_NORM)

            self.g_head_optimizer.step()
            self.p_head_optimizer.step()
            if self.auxiliary_trunk_optimizer is not None:
                self.auxiliary_trunk_optimizer.step()
            losses["G"].append(float(g_loss.detach().cpu()))
            losses["P"].append(float(p_loss.detach().cpu()))
            optimizer_steps += 1

        prediction_inputs = self._batch_tensors(arrays, np.arange(len(targets)))
        with torch.no_grad():
            g_norm, p_norm = self._head_predictions(*prediction_inputs, training=False)
            g_raw = (g_norm * self.target_std + self.target_mean).cpu().numpy()
            p_raw = (p_norm * self.target_std + self.target_mean).cpu().numpy()

        first = self._auxiliary_samples[0]
        boundary_digest = _tensor_digest(
            first["state"], first["observations"], first["entering_hidden"],
            first["entry_masks"], np.asarray(
                [first["env_id"], first["step"], first["team_skill"]], dtype=np.int64
            ),
            first["agent_skills"],
        )
        movement = {
            name: _relative_movement(parameters, trunk_before[name])
            for name, parameters in trunk_groups.items()
        }
        for parameter in trunk_parameters:
            parameter.grad = None

        return {
            "arm": self.arm,
            "samples": int(len(targets)),
            "head_optimizer_steps": {"G": optimizer_steps, "P": optimizer_steps},
            "trunk_optimizer_steps": optimizer_steps if self.auxiliary_trunk_optimizer is not None else 0,
            "loss_normalized": {name: float(np.mean(value)) for name, value in losses.items()},
            "loss_raw": {
                "G": float(np.mean((g_raw - targets_raw) ** 2)),
                "P": float(np.mean((p_raw - targets_raw) ** 2)),
            },
            "output_variance_raw": {
                "G": float(np.var(g_raw)), "P": float(np.var(p_raw)),
            },
            "gradient_norm_mean": {
                name: float(np.mean(value)) if value else 0.0
                for name, value in gradients.items()
            },
            "gradient_clip_count": clipped,
            "trunk_relative_movement": movement,
            "raw_target_sha256": target_hash,
            "first_rollout_target_sha256": self.first_rollout_target_sha256,
            "target_calibration": {"mean": self.target_mean, "population_std": self.target_std},
            "boundary_sample": {
                "sha256": boundary_digest,
                "env_id": int(first["env_id"]),
                "step": int(first["step"]),
                "team_skill": int(first["team_skill"]),
                "agent_skills": first["agent_skills"].tolist(),
                "entry_masks": first["entry_masks"].tolist(),
            },
            "raw_prediction_rows": {
                "env_id": arrays["env_ids"].astype(np.int64).tolist(),
                "boundary_step": arrays["steps"].astype(np.int64).tolist(),
                "raw_target": targets_raw.astype(np.float64).tolist(),
                "G_raw_prediction": g_raw.astype(np.float64).tolist(),
                "P_raw_prediction": p_raw.astype(np.float64).tolist(),
            },
            "parameter_counts": dict(self.parameter_counts),
            "architecture": dict(self.auxiliary_architecture),
            "G_width": self.G_width,
            "discarded_terminal_windows": self._discarded_terminal_windows,
        }

    def _native_replay_telemetry(self, steps_in_buffer: int) -> dict[str, Any]:
        """Replay canonical stored D2 rows before PPO changes the coordinator."""

        data = self.rollout_buffer._get_full_rollout_data()
        tables = self.rollout_buffer.get_d2_tables(steps_in_buffer)
        if data is None or tables is None:
            return {"rows": 0, "law": "mu=.9*pi+.1/6"}
        row_mask = tables["agent_valid"].any(axis=-1) | tables["team_valid"]
        time_rows, env_rows = np.where(row_mask)
        time_rows, env_rows = time_rows[:32], env_rows[:32]
        if time_rows.size == 0:
            return {"rows": 0, "law": "mu=.9*pi+.1/6"}

        def tensor(array: np.ndarray, dtype: torch.dtype) -> torch.Tensor:
            view = np.ascontiguousarray(array[time_rows, env_rows])
            return torch.as_tensor(view, dtype=dtype, device=self.device)

        inputs = {
            "state": tensor(data["states"], torch.float32),
            "observations": tensor(data["obs"], torch.float32),
            "team_skills": tensor(tables["team_skill"], torch.long),
            "agent_skills": tensor(tables["agent_skills"], torch.long),
            "order": tensor(tables["order"], torch.long),
            "sampled_mask": tensor(tables["sampled_mask"], torch.bool),
            "sample_Z_mask": tensor(tables["sample_Z"], torch.bool),
        }
        with torch.no_grad():
            replay = self.skill_coordinator.evaluate_training_batch_ordered(**inputs)
        old_team = tensor(tables["team_old_log_prob"], torch.float32)
        old_agents = tensor(tables["agent_old_log_probs"], torch.float32)
        replay_team = replay["team_log_probs"]
        replay_agents = replay["agent_log_probs"]
        sample_z = inputs["sample_Z_mask"]
        sampled = inputs["sampled_mask"]
        sampled_differences = []
        if bool(sample_z.any()):
            sampled_differences.append((replay_team[sample_z] - old_team[sample_z]).abs())
        if bool(sampled.any()):
            sampled_differences.append((replay_agents[sampled] - old_agents[sampled]).abs())
        max_difference = (
            float(torch.cat(sampled_differences).max().cpu())
            if sampled_differences else 0.0
        )
        forced_team = ~sample_z
        forced_agents = ~sampled
        forced_abs = []
        if bool(forced_team.any()):
            forced_abs.extend([replay_team[forced_team].abs(), old_team[forced_team].abs()])
        if bool(forced_agents.any()):
            forced_abs.extend([replay_agents[forced_agents].abs(), old_agents[forced_agents].abs()])
        max_forced_abs = (
            float(torch.cat(forced_abs).max().cpu()) if forced_abs else 0.0
        )
        return {
            "law": "mu=.9*pi+.1/6",
            "rows": int(time_rows.size),
            "time_rows": time_rows.astype(np.int64).tolist(),
            "env_rows": env_rows.astype(np.int64).tolist(),
            "sample_Z": sample_z.cpu().tolist(),
            "sampled_mask": sampled.cpu().tolist(),
            "old_team_log_mu": old_team.cpu().tolist(),
            "replayed_team_log_mu": replay_team.cpu().tolist(),
            "old_agent_log_mu": old_agents.cpu().tolist(),
            "replayed_agent_log_mu": replay_agents.cpu().tolist(),
            "max_sampled_log_mu_discrepancy": max_difference,
            "max_forced_abs_log_probability": max_forced_abs,
            "forced_team_factors": int(forced_team.sum().cpu()),
            "forced_agent_factors": int(forced_agents.sum().cpu()),
        }

    def update(
        self,
        last_values: np.ndarray,
        dones: np.ndarray,
        steps_in_buffer: int,
        last_state: np.ndarray | None = None,
        last_observations: np.ndarray | None = None,
    ):
        self._pending_replay_telemetry = self._native_replay_telemetry(int(steps_in_buffer))
        native_result = super().update(
            last_values,
            dones,
            steps_in_buffer,
            last_state=last_state,
            last_observations=last_observations,
        )
        auxiliary_row = self._run_auxiliary_update()
        auxiliary_row["native_mu_replay"] = self._pending_replay_telemetry
        self._pending_replay_telemetry = None
        self.auxiliary_history.append(auxiliary_row)
        if isinstance(native_result, dict):
            native_result = dict(native_result)
            native_result["complementary_auxiliary"] = auxiliary_row
        return native_result

    def clear_buffers(self) -> None:
        super().clear_buffers()
        self._pending_windows.clear()
        self._auxiliary_samples.clear()
        self._auxiliary_consumed = False
        self._discarded_terminal_windows = 0

    def auxiliary_state_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "arm": self.arm,
            "head_seed": self.head_seed,
            "aux_seed": self.aux_seed,
            "G_width": self.G_width,
            "parameter_counts": dict(self.parameter_counts),
            "architecture": dict(self.auxiliary_architecture),
            "g_head": self.g_head.state_dict(),
            "p_head": self.p_head.state_dict(),
            "g_head_optimizer": self.g_head_optimizer.state_dict(),
            "p_head_optimizer": self.p_head_optimizer.state_dict(),
            "auxiliary_trunk_optimizer": (
                self.auxiliary_trunk_optimizer.state_dict()
                if self.auxiliary_trunk_optimizer is not None else None
            ),
            "target_mean": self.target_mean,
            "target_std": self.target_std,
            "first_rollout_target_sha256": self.first_rollout_target_sha256,
            "shuffle_state": copy.deepcopy(self._shuffle_rng.bit_generator.state),
            "auxiliary_history": copy.deepcopy(self.auxiliary_history),
        }

    def load_auxiliary_state_dict(self, state: dict[str, Any]) -> None:
        if int(state.get("schema_version", -1)) != 1:
            raise ValueError("unsupported auxiliary checkpoint schema")
        if str(state.get("arm")) != self.arm:
            raise ValueError("auxiliary checkpoint arm mismatch")
        if int(state.get("G_width", -1)) != self.G_width:
            raise ValueError("auxiliary checkpoint G width mismatch")
        if dict(state.get("parameter_counts", {})) != self.parameter_counts:
            raise ValueError("auxiliary checkpoint parameter counts mismatch")
        self.g_head.load_state_dict(state["g_head"])
        self.p_head.load_state_dict(state["p_head"])
        self.g_head_optimizer.load_state_dict(state["g_head_optimizer"])
        self.p_head_optimizer.load_state_dict(state["p_head_optimizer"])
        saved_trunk = state.get("auxiliary_trunk_optimizer")
        if (saved_trunk is None) != (self.auxiliary_trunk_optimizer is None):
            raise ValueError("auxiliary checkpoint trunk optimizer mismatch")
        if self.auxiliary_trunk_optimizer is not None:
            self.auxiliary_trunk_optimizer.load_state_dict(saved_trunk)
        self.target_mean = state.get("target_mean")
        self.target_std = state.get("target_std")
        self.first_rollout_target_sha256 = state.get("first_rollout_target_sha256")
        self._shuffle_rng.bit_generator.state = copy.deepcopy(state["shuffle_state"])
        self.auxiliary_history = copy.deepcopy(state.get("auxiliary_history", []))


__all__ = [
    "ComplementaryAgent",
    "MixtureSkillDecoder",
    "MIXTURE_POLICY_WEIGHT",
    "MIXTURE_UNIFORM_WEIGHT",
]
