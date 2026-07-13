"""On-policy per-action density-ratio reward authorized by R29-G0."""

from __future__ import annotations

from math import log
from typing import Any

import numpy as np
import torch

from .r29_action_information import evaluate_executed_action_information


MODES = ("probe_only", "real_reward")
REWARD_COEF = 0.05
REWARD_CLIP = 0.05
LIKELIHOOD_PARITY_TOL = 2e-5


class R29ActionInformationContractError(RuntimeError):
    """The on-policy action-information contract was violated before PPO."""


def empty_r29_action_information_metrics(mode: str = "probe_only") -> dict[str, float]:
    metrics = {
        "r29_action_info_active": 0.0,
        "r29_action_info_mode_code": float(MODES.index(mode)) if mode in MODES else -1.0,
        "r29_action_info_rows": 0.0,
        "r29_action_info_raw_mean": 0.0,
        "r29_action_info_raw_abs_mean": 0.0,
        "r29_action_info_raw_positive_frac": 0.0,
        "r29_action_info_raw_q01": 0.0,
        "r29_action_info_raw_q99": 0.0,
        "r29_action_info_scaled_mean": 0.0,
        "r29_action_info_scaled_abs_mean": 0.0,
        "r29_action_info_clip_fraction": 0.0,
        "r29_action_info_reward_applied_steps": 0.0,
        "r29_action_info_reward_env_ratio": 0.0,
        "r29_action_info_likelihood_max_abs_error": 0.0,
    }
    metrics.update(
        {f"r29_action_info_skill_{skill}_mean": 0.0 for skill in range(4)}
    )
    return metrics


class OnPolicyActionInformationReward:
    """Compute a fixed rollout reward before the collection policy is updated."""

    def __init__(
        self,
        *,
        mode: str,
        actor: torch.nn.Module,
        coefficient: float = REWARD_COEF,
        clip: float = REWARD_CLIP,
    ) -> None:
        if mode not in MODES:
            raise R29ActionInformationContractError(f"unsupported R29 mode {mode!r}")
        if not np.isfinite(coefficient) or float(coefficient) <= 0.0:
            raise R29ActionInformationContractError("R29 coefficient must be positive")
        if not np.isfinite(clip) or float(clip) <= 0.0:
            raise R29ActionInformationContractError("R29 clip must be positive")
        if getattr(actor, "action_space_type", None) != "continuous":
            raise R29ActionInformationContractError("R29 requires a continuous actor")
        if type(actor.actor_act.action_out).__name__ != "TanhDiagGaussian":
            raise R29ActionInformationContractError("R29 requires TanhDiagGaussian")
        self.mode = mode
        self.actor = actor
        self.coefficient = float(coefficient)
        self.clip = float(clip)

    def _counterfactual_parameters(
        self,
        observations: torch.Tensor,
        hidden: torch.Tensor,
        team_codes: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        means: list[torch.Tensor] = []
        log_stds: list[torch.Tensor] = []
        rows = int(observations.shape[0])
        masks = torch.ones(rows, 1, dtype=torch.float32, device=observations.device)
        action_out = self.actor.actor_act.action_out
        with torch.no_grad():
            for skill in range(int(self.actor.n_skills)):
                labels = torch.full(
                    (rows,), skill, dtype=torch.long, device=observations.device
                )
                features = self.actor._actor_features(
                    observations, labels, team_codes
                )
                post_gru, _new_hidden = self.actor.actor_rnn(
                    features, hidden, masks
                )
                distribution = action_out._distribution(post_gru)
                means.append(distribution.mean)
                log_stds.append(torch.log(distribution.stddev))
        return torch.stack(means, dim=1), torch.stack(log_stds, dim=1)

    def apply(self, rollout: Any) -> dict[str, float]:
        metrics = empty_r29_action_information_metrics(self.mode)
        metrics["r29_action_info_active"] = 1.0
        if not getattr(rollout, "rewards", None):
            return metrics
        try:
            observations_np = np.asarray(rollout.obs, dtype=np.float32)
            hidden_np = np.asarray(rollout.low_actor_hxs, dtype=np.float32)
            actions_np = np.asarray(rollout.actions, dtype=np.float32)
            skills_np = np.asarray(rollout.skills, dtype=np.int64)
            old_logp_np = np.asarray(rollout.logp, dtype=np.float32)
            rewards_np = np.asarray(rollout.rewards, dtype=np.float32)
            team_codes_np = np.asarray(rollout.team_codes, dtype=np.int64)
        except (TypeError, ValueError) as error:
            raise R29ActionInformationContractError(
                "R29 rollout fields are not rectangular"
            ) from error
        time_steps = int(observations_np.shape[0])
        if skills_np.ndim != 2:
            raise R29ActionInformationContractError("R29 skill roster must be rank-2")
        n_agents = int(skills_np.shape[1])
        expected = (time_steps, n_agents)
        if (
            observations_np.shape[:2] != expected
            or hidden_np.shape[:2] != expected
            or actions_np.shape[:2] != expected
            or skills_np.shape != expected
            or old_logp_np.shape != expected
            or rewards_np.shape != expected
            or team_codes_np.shape != (time_steps,)
        ):
            raise R29ActionInformationContractError("R29 rollout shapes are misaligned")
        rows = time_steps * n_agents
        device = self.actor.device
        observations = torch.as_tensor(
            observations_np.reshape(rows, -1), dtype=torch.float32, device=device
        )
        hidden = torch.as_tensor(
            hidden_np.reshape(rows, -1), dtype=torch.float32, device=device
        )
        actions = torch.as_tensor(
            actions_np.reshape(rows, -1), dtype=torch.float32, device=device
        )
        skills = torch.as_tensor(
            skills_np.reshape(rows), dtype=torch.long, device=device
        )
        team_codes = torch.as_tensor(
            np.repeat(team_codes_np, n_agents),
            dtype=torch.long,
            device=device,
        )
        means, log_stds = self._counterfactual_parameters(
            observations, hidden, team_codes
        )
        with torch.no_grad():
            evaluation = evaluate_executed_action_information(
                means, log_stds, actions, skills
            )
        old_logp = torch.as_tensor(
            old_logp_np.reshape(rows), dtype=torch.float32, device=device
        )
        likelihood_error = float(
            torch.max(
                torch.abs(evaluation.squashed_actual_log_prob - old_logp)
            ).item()
        )
        if not np.isfinite(likelihood_error) or likelihood_error > LIKELIHOOD_PARITY_TOL:
            raise R29ActionInformationContractError(
                "R29 stored PPO likelihood mismatch: "
                f"{likelihood_error:.6g} > {LIKELIHOOD_PARITY_TOL:.6g}"
            )

        raw = evaluation.reward.detach().cpu().numpy().astype(np.float64)
        scaled_unclipped = self.coefficient * raw
        scaled = np.clip(scaled_unclipped, -self.clip, self.clip).astype(np.float32)
        if not np.isfinite(scaled).all():
            raise R29ActionInformationContractError("R29 scaled reward is non-finite")
        if self.mode == "real_reward":
            shaped = scaled.reshape(time_steps, n_agents)
            for step in range(time_steps):
                rollout.rewards[step] += shaped[step]
        env_abs_mean = float(np.mean(np.abs(rewards_np)))
        scaled_abs_mean = float(np.mean(np.abs(scaled)))
        skill_values = skills.detach().cpu().numpy().astype(np.int64)
        metrics.update(
            {
                "r29_action_info_rows": float(rows),
                "r29_action_info_raw_mean": float(np.mean(raw)),
                "r29_action_info_raw_abs_mean": float(np.mean(np.abs(raw))),
                "r29_action_info_raw_positive_frac": float(np.mean(raw > 0.0)),
                "r29_action_info_raw_q01": float(np.quantile(raw, 0.01)),
                "r29_action_info_raw_q99": float(np.quantile(raw, 0.99)),
                "r29_action_info_scaled_mean": float(np.mean(scaled)),
                "r29_action_info_scaled_abs_mean": scaled_abs_mean,
                "r29_action_info_clip_fraction": float(
                    np.mean(np.abs(scaled_unclipped) > self.clip)
                ),
                "r29_action_info_reward_applied_steps": (
                    float(rows) if self.mode == "real_reward" else 0.0
                ),
                "r29_action_info_reward_env_ratio": float(
                    scaled_abs_mean / max(env_abs_mean, 1e-8)
                ),
                "r29_action_info_likelihood_max_abs_error": likelihood_error,
            }
        )
        for skill in range(4):
            mask = skill_values == skill
            metrics[f"r29_action_info_skill_{skill}_mean"] = (
                float(np.mean(raw[mask])) if np.any(mask) else 0.0
            )
        return metrics
