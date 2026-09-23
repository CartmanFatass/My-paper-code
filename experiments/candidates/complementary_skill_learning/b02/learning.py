"""Candidate-local B02 learner adapter.

The B01 learner supplies the fixed full-support coordinator and the two factual
heads.  B02 leaves both heads detached and changes only the native legacy MI
reward coefficient.  This adapter also makes the native batch-reward fallback
observable and fatal: an env-only fallback is scientifically indistinguishable
from the T arm unless it is tracked at the construction site.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from experiments.candidates.complementary_skill_learning.b01.learning import ComplementaryAgent


ARM_COEFFICIENTS = {"M": 0.5, "T": 0.0}


class ObjectiveComparisonAgent(ComplementaryAgent):
    """B01-D learner with the prospectively fixed M/T native reward objective."""

    def __init__(self, config: Any, arm: str, head_seed: int, aux_seed: int,
                 log_dir: str, device: Any) -> None:
        arm = str(arm).upper()
        if arm not in ARM_COEFFICIENTS:
            raise ValueError("arm must be M or T")
        expected = ARM_COEFFICIENTS[arm]
        if float(getattr(config, "legacy_mi_reward_coef", float("nan"))) != expected:
            raise ValueError(f"{arm} requires legacy_mi_reward_coef={expected}")
        required = {
            "lambda_e": 1.0, "lambda_D": 0.05, "lambda_d": 0.02,
            "normalize_intrinsic_mi": False, "use_prior_corrected_intrinsic": False,
            "intrinsic_mi_clip": 2.0, "enhanced_state": False, "w_entropy": 0,
            "use_horizon_window": False, "use_process_exploration": False,
            "use_discrete_skill_lifetimes": False,
        }
        for name, value in required.items():
            if getattr(config, name, None) != value:
                raise ValueError(f"B02 requires {name}={value!r}")
        if bool(getattr(config, "disable_discriminator_rewards", False)):
            raise ValueError("B02 requires discriminator reward computation in both arms")
        if bool(getattr(config, "disable_discriminator_training", False)):
            raise ValueError("B02 requires discriminator training in both arms")

        self.objective_arm = arm
        self._reward_fallback_total = 0
        self._reward_batch_calls = 0
        self._reward_rows = 0
        self._reward_finite_failures = 0
        self._reward_identity_failures = 0
        self._reward_team_forwards = 0
        self._reward_individual_forwards = 0
        self._last_reward_batch: dict[str, np.ndarray] | None = None
        self._capture_reward_scores = False
        self._current_reward_scores: list[np.ndarray] = []
        self._reward_score_batches: list[tuple[np.ndarray, np.ndarray]] = []
        super().__init__(config, "D", head_seed, aux_seed, log_dir, device)
        # B01 uses this label only to decide whether an auxiliary trunk optimizer
        # exists.  M/T are both detached, and checkpoint metadata must retain the
        # actual B02 arm.
        self.arm = arm

    def _empty_intrinsic_batch_result(self, next_states, next_observations, reward_matrix):
        self._reward_fallback_total += 1
        return super()._empty_intrinsic_batch_result(
            next_states, next_observations, reward_matrix
        )

    def _team_discriminator_logits(self, *args, **kwargs):
        logits = super()._team_discriminator_logits(*args, **kwargs)
        if self._capture_reward_scores:
            self._reward_team_forwards += 1
            if not bool(logits.isfinite().all()):
                raise FloatingPointError("nonfinite team discriminator logits before native repair")
        return logits

    def _individual_discriminator_logits(self, *args, **kwargs):
        logits = super()._individual_discriminator_logits(*args, **kwargs)
        if self._capture_reward_scores:
            self._reward_individual_forwards += 1
            if not bool(logits.isfinite().all()):
                raise FloatingPointError("nonfinite individual discriminator logits before native repair")
        return logits

    def _discriminator_mi_reward(self, *args, **kwargs):
        values = np.asarray(super()._discriminator_mi_reward(*args, **kwargs))
        if not np.isfinite(values).all():
            raise FloatingPointError("nonfinite native discriminator-score transformation")
        if self._capture_reward_scores:
            self._current_reward_scores.append(values.astype(np.float32, copy=True))
        return values

    def _compute_intrinsic_rewards_batch(self, *args, **kwargs):
        fallbacks_before = self._reward_fallback_total
        self._current_reward_scores = []
        self._capture_reward_scores = True
        try:
            result = super()._compute_intrinsic_rewards_batch(*args, **kwargs)
        finally:
            self._capture_reward_scores = False
        self._reward_batch_calls += 1
        if self._reward_fallback_total != fallbacks_before:
            raise RuntimeError("native intrinsic-reward batch fell back to env-only reward")
        keys = ("intrinsic", "env", "team_disc", "ind_disc", "uncertainty")
        arrays = {key: np.asarray(result[key], dtype=np.float32) for key in keys}
        shape = arrays["intrinsic"].shape
        self._reward_rows += int(shape[0])
        if any(value.shape != shape or not np.isfinite(value).all()
               for value in arrays.values()):
            self._reward_finite_failures += 1
            raise FloatingPointError("nonfinite or mis-shaped native reward components")
        reconstructed = (arrays["env"] + arrays["team_disc"]
                         + arrays["ind_disc"] + arrays["uncertainty"])
        if not np.allclose(arrays["intrinsic"], reconstructed, rtol=1e-6, atol=2e-6):
            self._reward_identity_failures += 1
            raise ValueError("native intrinsic reward component identity failed")
        if self.objective_arm == "T" and (
            np.count_nonzero(arrays["team_disc"]) or np.count_nonzero(arrays["ind_disc"])
        ):
            self._reward_identity_failures += 1
            raise ValueError("T arm received a nonzero discriminator reward component")
        if len(self._current_reward_scores) != 2:
            self._reward_identity_failures += 1
            raise ValueError("native reward path did not produce both discriminator scores")
        team_score = self._current_reward_scores[0].reshape(shape[0])
        ind_score = self._current_reward_scores[1].reshape(shape)
        expected_team = (float(self.config.legacy_mi_reward_coef)
                         * float(self.config.lambda_D) * team_score[:, None])
        expected_ind = (float(self.config.legacy_mi_reward_coef)
                        * float(self.config.lambda_d) * ind_score)
        if (not np.allclose(arrays["team_disc"], expected_team, rtol=1e-6, atol=2e-6)
                or not np.allclose(arrays["ind_disc"], expected_ind, rtol=1e-6, atol=2e-6)):
            self._reward_identity_failures += 1
            raise ValueError("native discriminator coefficient identity failed")
        self._reward_score_batches.append((team_score.copy(), ind_score.copy()))
        self._last_reward_batch = {key: value.copy() for key, value in arrays.items()}
        return result

    def reward_score_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        if not self._reward_score_batches:
            return (np.empty((0, 0), np.float32), np.empty((0, 0, 0), np.float32))
        return (
            np.stack([row[0] for row in self._reward_score_batches]),
            np.stack([row[1] for row in self._reward_score_batches]),
        )

    def clear_buffers(self) -> None:
        super().clear_buffers()
        self._reward_score_batches.clear()

    def reward_telemetry(self) -> dict[str, int | float | str]:
        return {
            "arm": self.objective_arm,
            "legacy_mi_reward_coef": float(self.config.legacy_mi_reward_coef),
            "batch_calls": self._reward_batch_calls,
            "environment_rows": self._reward_rows,
            "team_discriminator_forwards": self._reward_team_forwards,
            "individual_discriminator_forwards": self._reward_individual_forwards,
            "finite_failures": self._reward_finite_failures,
            "component_identity_failures": self._reward_identity_failures,
            "fallbacks": self._reward_fallback_total,
        }


__all__ = ["ARM_COEFFICIENTS", "ObjectiveComparisonAgent"]
