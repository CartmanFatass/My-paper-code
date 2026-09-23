"""Candidate-local B04 training-law and RNG adapters.

The frozen B01 learner remains responsible for native acting, storage, PPO,
discriminator learning, recurrent replay, and factual heads.  This module only
separates the three stochastic process streams and supplies U's fixed uniform
high-level categorical law.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import math
import pickle
import random
from typing import Any, Iterator

import numpy as np
import torch

from experiments.candidates.complementary_skill_learning.b03.runner import (
    AuditedComplementaryAgent,
)


UNIFORM_LOG_FACTOR = -math.log(6.0)


def _capture_process_rng_state() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.random.get_rng_state().clone(),
        "torch_cuda": (
            [state.clone() for state in torch.cuda.get_rng_state_all()]
            if torch.cuda.is_available()
            else None
        ),
    }


def _restore_process_rng_state(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.random.set_rng_state(state["torch_cpu"])
    if state["torch_cuda"] is not None:
        torch.cuda.set_rng_state_all(state["torch_cuda"])


def _seed_process_rng(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _rng_state_digest(state: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(pickle.dumps(state["python"], protocol=4))
    numpy_state = state["numpy"]
    digest.update(str(numpy_state[0]).encode("ascii"))
    digest.update(np.ascontiguousarray(numpy_state[1]).tobytes())
    digest.update(pickle.dumps(numpy_state[2:], protocol=4))
    digest.update(state["torch_cpu"].cpu().numpy().tobytes())
    for cuda_state in state["torch_cuda"] or ():
        digest.update(cuda_state.cpu().numpy().tobytes())
    return digest.hexdigest()


class PersistentProcessRNG:
    """A private process RNG stream that restores its caller on every use."""

    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        outer = _capture_process_rng_state()
        try:
            _seed_process_rng(self.seed)
            self._state = _capture_process_rng_state()
        finally:
            _restore_process_rng_state(outer)

    @contextlib.contextmanager
    def use(self) -> Iterator[None]:
        outer = _capture_process_rng_state()
        _restore_process_rng_state(self._state)
        try:
            yield
        finally:
            self._state = _capture_process_rng_state()
            _restore_process_rng_state(outer)

    def state_dict(self) -> dict[str, Any]:
        return {"seed": self.seed, "state": copy.deepcopy(self._state)}

    def load_state_dict(self, body: dict[str, Any]) -> None:
        if int(body.get("seed", -1)) != self.seed:
            raise ValueError("private RNG stream seed mismatch")
        state = copy.deepcopy(body["state"])
        outer = _capture_process_rng_state()
        try:
            _restore_process_rng_state(state)
        finally:
            _restore_process_rng_state(outer)
        self._state = state

    def digest(self) -> str:
        return _rng_state_digest(self._state)


class UniformSkillDecoderLaw:
    """Class adapter returning constant logits for team and individual labels."""

    def forward(self, *args: Any, **kwargs: Any) -> torch.Tensor:
        logits = super().forward(*args, **kwargs)
        return torch.zeros_like(logits)


class TrainingLawAgent(AuditedComplementaryAgent):
    """B01/B03 learner with M or U high law and three private RNG streams."""

    def __init__(
        self,
        config: Any,
        arm: str,
        head_seed: int,
        aux_seed: int,
        low_action_seed: int,
        high_collection_seed: int,
        high_update_seed: int,
        log_dir: str,
        device: torch.device | str | None,
    ) -> None:
        arm = str(arm).upper()
        if arm not in {"M", "U"}:
            raise ValueError("B04 arm must be M or U")
        if bool(getattr(config, "disable_high_level_training", False)) != (arm == "U"):
            raise ValueError("B04 high-level training switch differs from the arm")

        # B04 always uses B01's detached-head D route.  The public arm is
        # restored after construction so checkpoints and telemetry say M/U.
        super().__init__(
            config=config,
            arm="D",
            head_seed=head_seed,
            aux_seed=aux_seed,
            log_dir=log_dir,
            device=device,
        )
        self.arm = arm
        if arm == "U":
            decoder = self.skill_coordinator.skill_decoder
            decoder.__class__ = type(
                "UniformSkillDecoder",
                (UniformSkillDecoderLaw, decoder.__class__),
                {},
            )

        self._rng_streams = {
            "low_actions": PersistentProcessRNG(low_action_seed),
            "high_collection": PersistentProcessRNG(high_collection_seed),
            "high_updates": PersistentProcessRNG(high_update_seed),
        }
        high_sampler = np.random.Generator(np.random.PCG64(int(high_update_seed)))
        self._high_sampler_state = copy.deepcopy(high_sampler.bit_generator.state)
        self._high_sampler_seed = int(high_update_seed)
        self._last_action_labels: tuple[np.ndarray, np.ndarray] | None = None
        self.label_flow_checks = {
            "action_batches": 0,
            "reward_batches": 0,
            "factual_batches": 0,
            "storage_batches": 0,
            "failures": 0,
        }
        self.uniform_factor_audits: list[dict[str, Any]] = []

    def _batched_assign_skills(self, *args: Any, **kwargs: Any):
        with self._rng_streams["high_collection"].use():
            return super()._batched_assign_skills(*args, **kwargs)

    def _batched_select_action(
        self,
        states_batch: np.ndarray,
        observations_batch: np.ndarray,
        agent_skills_batch: np.ndarray,
        team_skills_batch: np.ndarray,
        dones_batch: np.ndarray,
        deterministic: bool = False,
    ):
        team = np.asarray(team_skills_batch, dtype=np.int64).copy()
        agents = np.asarray(agent_skills_batch, dtype=np.int64).copy()
        self._last_action_labels = (team, agents)
        self.label_flow_checks["action_batches"] += 1
        with self._rng_streams["low_actions"].use():
            return super()._batched_select_action(
                states_batch,
                observations_batch,
                agent_skills_batch,
                team_skills_batch,
                dones_batch,
                deterministic=deterministic,
            )

    def update_coordinator(self, *args: Any, **kwargs: Any):
        # The native RolloutBuffer owns one PCG64 sampler shared by high D2 PPO
        # and low recurrent PPO.  Give the high update its fixed private state,
        # then restore the remaining learner's state even on failure.  This is
        # the object-private counterpart of the process RNG context above.
        remaining_learner_state = self.rollout_buffer.get_sampler_rng_state()
        self.rollout_buffer.set_sampler_rng_state(self._high_sampler_state)
        try:
            with self._rng_streams["high_updates"].use():
                return super().update_coordinator(*args, **kwargs)
        finally:
            self._high_sampler_state = self.rollout_buffer.get_sampler_rng_state()
            self.rollout_buffer.set_sampler_rng_state(remaining_learner_state)

    def _require_current_labels(
        self, team_skills: np.ndarray, agent_skills: np.ndarray, consumer: str
    ) -> None:
        if self._last_action_labels is None:
            self.label_flow_checks["failures"] += 1
            raise RuntimeError(f"{consumer} ran before B04 low action labels were recorded")
        expected_team, expected_agents = self._last_action_labels
        if not (
            np.array_equal(np.asarray(team_skills, dtype=np.int64), expected_team)
            and np.array_equal(np.asarray(agent_skills, dtype=np.int64), expected_agents)
        ):
            self.label_flow_checks["failures"] += 1
            raise RuntimeError(f"B04 labels changed between low action and {consumer}")

    def _compute_intrinsic_rewards_batch(self, *args: Any, **kwargs: Any):
        self._require_current_labels(
            kwargs["team_skills"], kwargs["agent_skills"], "native reward"
        )
        self.label_flow_checks["reward_batches"] += 1
        return super()._compute_intrinsic_rewards_batch(*args, **kwargs)

    def _capture_auxiliary_transitions(
        self,
        states: np.ndarray,
        observations: np.ndarray,
        rewards: np.ndarray,
        dones: np.ndarray,
        step_data: dict[str, Any],
    ) -> None:
        self._require_current_labels(
            step_data["team_skills"], step_data["agent_skills"], "factual heads"
        )
        self.label_flow_checks["factual_batches"] += 1
        return super()._capture_auxiliary_transitions(
            states, observations, rewards, dones, step_data
        )

    def store_transition_batch(self, *args: Any, **kwargs: Any):
        step_data = kwargs.get("step_data")
        if step_data is None:
            raise ValueError("B04 storage requires step_data")
        self._require_current_labels(
            step_data["team_skills"], step_data["agent_skills"], "native storage"
        )
        result = super().store_transition_batch(*args, **kwargs)
        t = int(kwargs["rollout_step_idx"])
        expected_team, expected_agents = self._last_action_labels
        if not (
            np.array_equal(self.rollout_buffer.team_skills[t, : len(expected_team)], expected_team)
            and np.array_equal(
                self.rollout_buffer.agent_skills[t, : len(expected_agents)], expected_agents
            )
        ):
            self.label_flow_checks["failures"] += 1
            raise RuntimeError("B04 canonical low storage changed the executed labels")
        self.label_flow_checks["storage_batches"] += 1
        return result

    def audit_uniform_d2_storage(self, steps_in_buffer: int) -> dict[str, Any]:
        if self.arm != "U":
            raise ValueError("uniform D2 storage audit is U-only")
        tables = self.rollout_buffer.get_d2_tables(int(steps_in_buffer))
        if tables is None:
            raise RuntimeError("U did not retain native D2 tables")
        team_valid = np.asarray(tables["team_valid"], dtype=np.bool_)
        agent_valid = np.asarray(tables["agent_valid"], dtype=np.bool_)
        decision = np.asarray(tables["decision"], dtype=np.bool_)
        sampled = np.asarray(tables["sampled_mask"], dtype=np.bool_)
        sample_team = np.asarray(tables["sample_Z"], dtype=np.bool_)
        team_factors = np.asarray(tables["team_old_log_prob"], dtype=np.float32)
        agent_factors = np.asarray(tables["agent_old_log_probs"], dtype=np.float32)
        team_labels = np.asarray(tables["team_skill"], dtype=np.int64)
        agent_labels = np.asarray(tables["agent_skills"], dtype=np.int64)

        if np.any(team_valid & ~decision) or np.any(agent_valid & ~decision[..., None]):
            raise RuntimeError("canonical U D2 segment lacks its decision record")
        if np.any(team_valid & ~sample_team) or np.any(agent_valid & ~sampled):
            raise RuntimeError("canonical U D2 segment was not sampled at its k10 boundary")
        if np.any((team_labels[team_valid] < 0) | (team_labels[team_valid] >= 6)):
            raise RuntimeError("canonical U team label is outside six-label support")
        expanded_team = np.broadcast_to(team_valid[..., None], agent_labels.shape)
        if np.any((agent_labels[expanded_team] < 0) | (agent_labels[expanded_team] >= 6)):
            raise RuntimeError("canonical U individual label is outside six-label support")
        if not np.allclose(
            team_factors[team_valid], UNIFORM_LOG_FACTOR, rtol=0.0, atol=2e-7
        ):
            raise RuntimeError("canonical U team factor is not log(1/6)")
        if not np.allclose(
            agent_factors[agent_valid], UNIFORM_LOG_FACTOR, rtol=0.0, atol=2e-7
        ):
            raise RuntimeError("canonical U individual factor is not log(1/6)")

        row_mask = team_valid | agent_valid.any(axis=-1)
        time_rows, env_rows = np.where(row_mask)
        limit = min(32, len(time_rows))
        audit = {
            "law": "independent_uniform_team_and_individual_1_over_6",
            "learned_policy_ppo_replay": "not_applicable",
            "canonical_rows_checked": int(row_mask.sum()),
            "team_factors_checked": int(team_valid.sum()),
            "individual_factors_checked": int(agent_valid.sum()),
            "expected_log_factor": UNIFORM_LOG_FACTOR,
            "representative_time_rows": time_rows[:limit].astype(np.int64).tolist(),
            "representative_env_rows": env_rows[:limit].astype(np.int64).tolist(),
            "representative_team_labels": team_labels[time_rows[:limit], env_rows[:limit]].tolist(),
            "representative_agent_labels": agent_labels[
                time_rows[:limit], env_rows[:limit]
            ].tolist(),
        }
        self.uniform_factor_audits.append(copy.deepcopy(audit))
        return audit

    def _native_replay_telemetry(self, steps_in_buffer: int) -> dict[str, Any]:
        if self.arm == "U":
            return self.audit_uniform_d2_storage(steps_in_buffer)
        return super()._native_replay_telemetry(steps_in_buffer)

    def rng_stream_state_dict(self) -> dict[str, Any]:
        return {
            name: stream.state_dict() for name, stream in self._rng_streams.items()
        }

    def rng_stream_telemetry(self) -> dict[str, Any]:
        return {
            name: {"seed": stream.seed, "state_sha256": stream.digest()}
            for name, stream in self._rng_streams.items()
        }

    @staticmethod
    def _sampler_state_digest(state: dict[str, Any]) -> str:
        return hashlib.sha256(pickle.dumps(state, protocol=4)).hexdigest()

    def sampler_rng_state_dict(self) -> dict[str, Any]:
        return {
            "remaining_learner": {
                "seed": int(self.rollout_sampler_seed),
                "state": self.rollout_buffer.get_sampler_rng_state(),
            },
            "high_updates": {
                "seed": self._high_sampler_seed,
                "state": copy.deepcopy(self._high_sampler_state),
            },
        }

    def sampler_rng_telemetry(self) -> dict[str, Any]:
        state = self.sampler_rng_state_dict()
        return {
            name: {
                "seed": body["seed"],
                "state_sha256": self._sampler_state_digest(body["state"]),
            }
            for name, body in state.items()
        }

    def load_sampler_rng_state_dict(self, state: dict[str, Any]) -> None:
        if set(state) != {"remaining_learner", "high_updates"}:
            raise ValueError("private sampler checkpoint stream set mismatch")
        if int(state["remaining_learner"].get("seed", -1)) != int(
            self.rollout_sampler_seed
        ):
            raise ValueError("remaining-learner sampler seed mismatch")
        if int(state["high_updates"].get("seed", -1)) != self._high_sampler_seed:
            raise ValueError("high-update sampler seed mismatch")
        self.rollout_buffer.set_sampler_rng_state(
            copy.deepcopy(state["remaining_learner"]["state"])
        )
        restored_high = copy.deepcopy(state["high_updates"]["state"])
        probe = np.random.default_rng()
        probe.bit_generator.state = copy.deepcopy(restored_high)
        self._high_sampler_state = restored_high

    def load_rng_stream_state_dict(self, state: dict[str, Any]) -> None:
        if set(state) != set(self._rng_streams):
            raise ValueError("private RNG checkpoint stream set mismatch")
        for name, stream in self._rng_streams.items():
            stream.load_state_dict(state[name])


__all__ = [
    "PersistentProcessRNG",
    "TrainingLawAgent",
    "UNIFORM_LOG_FACTOR",
    "UniformSkillDecoderLaw",
]
