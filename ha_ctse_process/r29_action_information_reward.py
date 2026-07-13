"""On-policy recurrent terminal-block density-ratio reward for R29-T10."""

from __future__ import annotations

from collections import defaultdict
from math import log
from typing import Any

import numpy as np
import torch

from .r29_action_information import evaluate_executed_action_information


MODES = ("probe_only", "real_reward")
REWARD_COEF = 0.05
REWARD_CLIP = 0.05
TERMINAL_WINDOW = 10
LIKELIHOOD_PARITY_TOL = 2e-5


class R29ActionInformationContractError(RuntimeError):
    """The on-policy action-information contract was violated before PPO."""


def empty_r29_action_information_metrics(mode: str = "probe_only") -> dict[str, float]:
    metrics = {
        "r29_action_info_active": 0.0,
        "r29_action_info_mode_code": float(MODES.index(mode)) if mode in MODES else -1.0,
        "r29_action_info_rows": 0.0,
        "r29_action_info_segments": 0.0,
        "r29_action_info_terminal_rows": 0.0,
        "r29_action_info_excluded_segments": 0.0,
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
        "r29_action_info_symmetric_kl_mean": 0.0,
        "r29_action_info_symmetric_kl_mean_component": 0.0,
        "r29_action_info_symmetric_kl_variance_component": 0.0,
    }
    metrics.update(
        {f"r29_action_info_skill_{skill}_mean": 0.0 for skill in range(4)}
    )
    return metrics


class OnPolicyActionInformationReward:
    """Score complete skill lifetimes before the collection policy is updated."""

    def __init__(
        self,
        *,
        mode: str,
        actor: torch.nn.Module,
        skill_interval: int,
        coefficient: float = REWARD_COEF,
        clip: float = REWARD_CLIP,
        terminal_window: int = TERMINAL_WINDOW,
    ) -> None:
        if mode not in MODES:
            raise R29ActionInformationContractError(f"unsupported R29 mode {mode!r}")
        if not np.isfinite(coefficient) or float(coefficient) <= 0.0:
            raise R29ActionInformationContractError("R29 coefficient must be positive")
        if not np.isfinite(clip) or float(clip) <= 0.0:
            raise R29ActionInformationContractError("R29 clip must be positive")
        if int(skill_interval) <= 0 or int(terminal_window) <= 0:
            raise R29ActionInformationContractError(
                "R29 skill interval and terminal window must be positive"
            )
        if int(terminal_window) > int(skill_interval):
            raise R29ActionInformationContractError(
                "R29 terminal window cannot exceed one skill interval"
            )
        if getattr(actor, "action_space_type", None) != "continuous":
            raise R29ActionInformationContractError("R29 requires a continuous actor")
        if type(actor.actor_act.action_out).__name__ != "TanhDiagGaussian":
            raise R29ActionInformationContractError("R29 requires TanhDiagGaussian")
        self.mode = mode
        self.actor = actor
        self.skill_interval = int(skill_interval)
        self.coefficient = float(coefficient)
        self.clip = float(clip)
        self.terminal_window = int(terminal_window)

    def _is_complete_lifetime(self, segment: Any) -> bool:
        expected_length = int(segment.duration_target) * self.skill_interval
        return bool(
            int(segment.length) == expected_length
            and expected_length >= self.terminal_window
            and str(segment.completion_reason) != "episode"
            and not bool(segment.terminal)
        )

    @staticmethod
    def _symmetric_kl_components(
        means: torch.Tensor,
        log_stds: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, int]:
        mean_sum = torch.zeros((), dtype=torch.float64, device=means.device)
        variance_sum = torch.zeros((), dtype=torch.float64, device=means.device)
        pair_rows = 0
        variances = torch.exp(2.0 * log_stds)
        for left in range(int(means.shape[1])):
            for right in range(left + 1, int(means.shape[1])):
                delta_square = (means[:, left] - means[:, right]).square()
                left_variance = variances[:, left]
                right_variance = variances[:, right]
                mean_component = 0.25 * (
                    delta_square
                    * (left_variance.reciprocal() + right_variance.reciprocal())
                ).sum(dim=-1)
                variance_component = 0.25 * (
                    left_variance / right_variance
                    + right_variance / left_variance
                    - 2.0
                ).sum(dim=-1)
                mean_sum += mean_component.double().sum()
                variance_sum += variance_component.double().sum()
                pair_rows += int(mean_component.numel())
        return mean_sum, variance_sum, pair_rows

    def _validate_segment_indices(
        self,
        segment: Any,
        *,
        time_steps: int,
        n_agents: int,
        env_ids: np.ndarray,
        skills: np.ndarray,
    ) -> None:
        agent_id = int(segment.agent_id)
        if agent_id < 0 or agent_id >= n_agents:
            raise R29ActionInformationContractError("R29 segment agent is outside rollout")
        indices = [int(index) for index in segment.rollout_indices]
        if len(indices) != int(segment.length):
            raise R29ActionInformationContractError(
                "R29 segment length and rollout indices disagree"
            )
        if any(index < 0 or index >= time_steps for index in indices):
            raise R29ActionInformationContractError("R29 segment index is outside rollout")
        if any(right <= left for left, right in zip(indices, indices[1:])):
            raise R29ActionInformationContractError(
                "R29 segment rollout indices are not ordered"
            )
        expected_env = int(segment.env_id)
        expected_skill = int(segment.skill)
        if any(int(env_ids[index]) != expected_env for index in indices):
            raise R29ActionInformationContractError("R29 segment crosses environments")
        if any(int(skills[index, agent_id]) != expected_skill for index in indices):
            raise R29ActionInformationContractError("R29 segment skill is not persistent")

    def _score_length_bucket(
        self,
        segments: list[Any],
        *,
        observations: np.ndarray,
        hidden: np.ndarray,
        actions: np.ndarray,
        old_logp: np.ndarray,
        team_codes: np.ndarray,
    ) -> tuple[np.ndarray, float, float, float, int]:
        device = self.actor.device
        batch_size = len(segments)
        num_skills = int(self.actor.n_skills)
        segment_length = int(segments[0].length)
        agent_ids = np.asarray(
            [int(segment.agent_id) for segment in segments], dtype=np.int64
        )
        index_rows = np.asarray(
            [[int(index) for index in segment.rollout_indices] for segment in segments],
            dtype=np.int64,
        )
        actual_skills = torch.as_tensor(
            [int(segment.skill) for segment in segments],
            dtype=torch.long,
            device=device,
        )
        candidate_skills = torch.arange(
            num_skills, dtype=torch.long, device=device
        ).repeat(batch_size)
        initial_hidden = hidden[index_rows[:, 0], agent_ids]
        recurrent_hidden = torch.as_tensor(
            initial_hidden, dtype=torch.float32, device=device
        ).repeat_interleave(num_skills, dim=0)
        masks = torch.ones(
            batch_size * num_skills, 1, dtype=torch.float32, device=device
        )
        block_log_likelihood = torch.zeros(
            batch_size, num_skills, dtype=torch.float32, device=device
        )
        likelihood_max_error = 0.0
        kl_mean_sum = torch.zeros((), dtype=torch.float64, device=device)
        kl_variance_sum = torch.zeros((), dtype=torch.float64, device=device)
        kl_pair_rows = 0
        action_out = self.actor.actor_act.action_out

        with torch.no_grad():
            for offset in range(segment_length):
                step_indices = index_rows[:, offset]
                step_observations = torch.as_tensor(
                    observations[step_indices, agent_ids],
                    dtype=torch.float32,
                    device=device,
                )
                expanded_observations = (
                    step_observations[:, None, :]
                    .expand(-1, num_skills, -1)
                    .reshape(batch_size * num_skills, -1)
                )
                step_team_codes = torch.as_tensor(
                    team_codes[step_indices], dtype=torch.long, device=device
                )
                expanded_team_codes = (
                    step_team_codes[:, None]
                    .expand(-1, num_skills)
                    .reshape(batch_size * num_skills)
                )
                features = self.actor._actor_features(
                    expanded_observations,
                    candidate_skills,
                    expanded_team_codes,
                )
                post_gru, recurrent_hidden = self.actor.actor_rnn(
                    features, recurrent_hidden, masks
                )
                distribution = action_out._distribution(post_gru)
                means = distribution.mean.reshape(batch_size, num_skills, -1)
                log_stds = torch.log(distribution.stddev).reshape(
                    batch_size, num_skills, -1
                )
                step_actions = torch.as_tensor(
                    actions[step_indices, agent_ids],
                    dtype=torch.float32,
                    device=device,
                )
                evaluation = evaluate_executed_action_information(
                    means,
                    log_stds,
                    step_actions,
                    actual_skills,
                )
                stored_logp = torch.as_tensor(
                    old_logp[step_indices, agent_ids],
                    dtype=torch.float32,
                    device=device,
                )
                step_error = float(
                    torch.max(
                        torch.abs(evaluation.squashed_actual_log_prob - stored_logp)
                    ).item()
                )
                likelihood_max_error = max(likelihood_max_error, step_error)
                if offset >= segment_length - self.terminal_window:
                    block_log_likelihood += evaluation.candidate_raw_log_prob
                    mean_sum, variance_sum, pair_rows = self._symmetric_kl_components(
                        means, log_stds
                    )
                    kl_mean_sum += mean_sum
                    kl_variance_sum += variance_sum
                    kl_pair_rows += pair_rows

            actual_block_log_likelihood = block_log_likelihood.gather(
                1, actual_skills[:, None]
            ).squeeze(1)
            raw = (
                actual_block_log_likelihood
                - torch.logsumexp(block_log_likelihood, dim=1)
                + log(num_skills)
            )
        if not torch.isfinite(raw).all():
            raise R29ActionInformationContractError("R29 terminal-block score is non-finite")
        return (
            raw.detach().cpu().numpy().astype(np.float64),
            likelihood_max_error,
            float(kl_mean_sum.item()),
            float(kl_variance_sum.item()),
            kl_pair_rows,
        )

    def apply(self, segments: list[Any], rollout: Any) -> dict[str, float]:
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
            env_ids_np = np.asarray(rollout.env_ids, dtype=np.int64)
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
            or env_ids_np.shape != (time_steps,)
        ):
            raise R29ActionInformationContractError("R29 rollout shapes are misaligned")

        eligible: list[Any] = []
        for segment in segments:
            if not self._is_complete_lifetime(segment):
                continue
            self._validate_segment_indices(
                segment,
                time_steps=time_steps,
                n_agents=n_agents,
                env_ids=env_ids_np,
                skills=skills_np,
            )
            eligible.append(segment)
        metrics["r29_action_info_excluded_segments"] = float(
            len(segments) - len(eligible)
        )
        if not eligible:
            return metrics

        by_length: dict[int, list[Any]] = defaultdict(list)
        for segment in eligible:
            by_length[int(segment.length)].append(segment)

        raw_parts: list[np.ndarray] = []
        skill_parts: list[np.ndarray] = []
        terminal_targets: list[tuple[int, int]] = []
        likelihood_max_error = 0.0
        kl_mean_sum = 0.0
        kl_variance_sum = 0.0
        kl_pair_rows = 0
        replay_rows = 0
        for length in sorted(by_length):
            bucket = by_length[length]
            raw, error, mean_sum, variance_sum, pair_rows = self._score_length_bucket(
                bucket,
                observations=observations_np,
                hidden=hidden_np,
                actions=actions_np,
                old_logp=old_logp_np,
                team_codes=team_codes_np,
            )
            raw_parts.append(raw)
            skill_parts.append(
                np.asarray([int(segment.skill) for segment in bucket], dtype=np.int64)
            )
            terminal_targets.extend(
                (int(segment.rollout_indices[-1]), int(segment.agent_id))
                for segment in bucket
            )
            likelihood_max_error = max(likelihood_max_error, error)
            kl_mean_sum += mean_sum
            kl_variance_sum += variance_sum
            kl_pair_rows += pair_rows
            replay_rows += int(length) * len(bucket)

        if (
            not np.isfinite(likelihood_max_error)
            or likelihood_max_error > LIKELIHOOD_PARITY_TOL
        ):
            raise R29ActionInformationContractError(
                "R29 stored PPO likelihood mismatch: "
                f"{likelihood_max_error:.6g} > {LIKELIHOOD_PARITY_TOL:.6g}"
            )

        raw = np.concatenate(raw_parts)
        skill_values = np.concatenate(skill_parts)
        scaled_unclipped = self.coefficient * raw
        scaled = np.clip(scaled_unclipped, -self.clip, self.clip).astype(np.float32)
        if not np.isfinite(scaled).all():
            raise R29ActionInformationContractError("R29 scaled reward is non-finite")
        if self.mode == "real_reward":
            for reward, (step, agent_id) in zip(scaled, terminal_targets):
                rollout.rewards[step][agent_id] += float(reward)

        env_abs_mean = float(np.mean(np.abs(rewards_np)))
        full_rollout_intrinsic_abs_mean = float(np.sum(np.abs(scaled))) / float(
            max(rewards_np.size, 1)
        )
        scaled_abs_mean = float(np.mean(np.abs(scaled)))
        mean_kl = kl_mean_sum / float(max(kl_pair_rows, 1))
        variance_kl = kl_variance_sum / float(max(kl_pair_rows, 1))
        metrics.update(
            {
                "r29_action_info_rows": float(replay_rows),
                "r29_action_info_segments": float(len(eligible)),
                "r29_action_info_terminal_rows": float(
                    len(eligible) * self.terminal_window
                ),
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
                    float(len(eligible)) if self.mode == "real_reward" else 0.0
                ),
                "r29_action_info_reward_env_ratio": float(
                    full_rollout_intrinsic_abs_mean / max(env_abs_mean, 1e-8)
                ),
                "r29_action_info_likelihood_max_abs_error": likelihood_max_error,
                "r29_action_info_symmetric_kl_mean": mean_kl + variance_kl,
                "r29_action_info_symmetric_kl_mean_component": mean_kl,
                "r29_action_info_symmetric_kl_variance_component": variance_kl,
            }
        )
        for skill in range(4):
            mask = skill_values == skill
            metrics[f"r29_action_info_skill_{skill}_mean"] = (
                float(np.mean(raw[mask])) if np.any(mask) else 0.0
            )
        return metrics
