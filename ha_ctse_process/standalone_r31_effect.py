"""Standalone R31 effect-information scoring and posterior updates."""

from __future__ import annotations

import numpy as np
import torch

import ha_ctse_process.standalone_segments as standalone_segments
from ha_ctse_process.intrinsic_rewards import effect_information_reward
from ha_ctse_process.r31_effect_information import (
    build_effect_and_context,
    matched_context_shuffle,
)


class StandaloneR31EffectMixin:
    def _empty_r31_metrics(self) -> dict[str, float]:
        metrics = {
            "r31_effect_windows": 0.0,
            "r31_effect_invalid_windows": 0.0,
            "r31_effect_information_mean": 0.0,
            "r31_effect_information_positive_frac": 0.0,
            "r31_effect_full_acc": 0.0,
            "r31_effect_context_acc": 0.0,
            "r31_effect_shuffle_mean": 0.0,
            "r31_effect_shuffle_abs_mean": 0.0,
            "r31_effect_shuffle_valid_frac": 0.0,
            "r31_effect_reward_mean": 0.0,
            "r31_effect_reward_applied_endpoints": 0.0,
            "r31_effect_posterior_samples": 0.0,
            "r31_effect_posterior_loss": 0.0,
            "r31_effect_full_loss": 0.0,
            "r31_effect_context_loss": 0.0,
        }
        for skill in range(self.n_skills):
            metrics[f"r31_effect_skill_{skill}_mean"] = 0.0
            metrics[f"r31_effect_skill_{skill}_samples"] = 0.0
        return metrics
    def r31_score_complete_windows(self, rollout: standalone_segments.Rollout) -> dict[str, float]:
        """Score complete natural windows with the previous frozen posterior."""

        metrics = self._empty_r31_metrics()
        if not self.r31_enabled:
            return metrics
        if self.r31_effect_windows is None or self.r31_effect_posterior is None:
            raise RuntimeError("R31 is enabled without its window buffer/posterior")
        if self._r31_scored_batch is not None or self._r31_scored_rows:
            raise RuntimeError("R31 previous scored batch was not consumed")

        rows = self.r31_effect_windows.pop_completed()
        invalid_rows = self.r31_effect_windows.pop_invalidated()
        metrics["r31_effect_invalid_windows"] = float(len(invalid_rows))
        if not rows:
            return metrics

        effects: list[np.ndarray] = []
        contexts: list[np.ndarray] = []
        labels: list[int] = []
        for row in rows:
            if not row.ready or row.transition_count != self.r31_effect_window:
                raise RuntimeError("R31 attempted to score an incomplete natural window")
            endpoint = int(row.endpoint_rollout_index)
            if not 0 <= endpoint < len(rollout.rewards):
                raise IndexError(
                    f"R31 endpoint index {endpoint} is outside the current rollout"
                )
            if int(rollout.env_ids[endpoint]) != int(row.env_id):
                raise RuntimeError("R31 endpoint env does not match the natural window")
            effect, context = build_effect_and_context(
                row.effect_view_sequence,
                row.active_skills,
                row.focal_agent,
                self.n_skills,
            )
            effects.append(effect)
            contexts.append(context)
            labels.append(int(row.active_skills[row.focal_agent]))

        effect_np = np.asarray(effects, dtype=np.float32)
        context_np = np.asarray(contexts, dtype=np.float32)
        label_np = np.asarray(labels, dtype=np.int64)
        effect_t = torch.as_tensor(effect_np, dtype=torch.float32, device=self.device)
        context_t = torch.as_tensor(context_np, dtype=torch.float32, device=self.device)
        label_t = torch.as_tensor(label_np, dtype=torch.long, device=self.device)
        self.r31_effect_posterior.eval()
        with torch.no_grad():
            full_logits, context_logits = self.r31_effect_posterior(
                effect_t,
                context_t,
            )
            log_full = self.r31_effect_posterior.log_prob_for_labels(
                full_logits,
                label_t,
            )
            log_context = self.r31_effect_posterior.log_prob_for_labels(
                context_logits,
                label_t,
            )
            delta = log_full - log_context
            reward = effect_information_reward(
                delta,
                coef=self.r31_effect_coef,
                clip=self.r31_effect_clip,
                enabled=self.r31_reward_enabled,
            )
            full_acc = (full_logits.argmax(dim=-1) == label_t).float().mean()
            context_acc = (context_logits.argmax(dim=-1) == label_t).float().mean()

        delta_np = delta.detach().cpu().numpy().astype(np.float32)
        reward_np = reward.detach().cpu().numpy().astype(np.float32)
        for sample, row in enumerate(rows):
            if self.r31_reward_enabled:
                rollout.rewards[row.endpoint_rollout_index][row.focal_agent] += float(
                    reward_np[sample]
                )

        starts = np.asarray(
            [row.effect_view_sequence[0] for row in rows],
            dtype=np.float32,
        )
        active_skills = np.asarray(
            [row.active_skills for row in rows],
            dtype=np.int64,
        )
        focal_agents = np.asarray(
            [row.focal_agent for row in rows],
            dtype=np.int64,
        )
        shuffled_effects, _donors, shuffle_valid = matched_context_shuffle(
            effect_np,
            starts,
            active_skills,
            focal_agents,
            rng=31031 + int(rows[0].policy_update),
        )
        shuffle_delta_np = np.zeros(len(rows), dtype=np.float32)
        if bool(np.any(shuffle_valid)):
            shuffled_t = torch.as_tensor(
                shuffled_effects,
                dtype=torch.float32,
                device=self.device,
            )
            with torch.no_grad():
                shuffled_logits = self.r31_effect_posterior.full_logits(
                    shuffled_t,
                    context_t,
                )
                shuffle_delta = self.r31_effect_posterior.log_prob_for_labels(
                    shuffled_logits,
                    label_t,
                ) - log_context
            shuffle_delta_np = (
                shuffle_delta.detach().cpu().numpy().astype(np.float32)
            )

        metrics.update(
            {
                "r31_effect_windows": float(len(rows)),
                "r31_effect_information_mean": float(np.mean(delta_np)),
                "r31_effect_information_positive_frac": float(
                    np.mean(delta_np > 0.0)
                ),
                "r31_effect_full_acc": float(full_acc.detach().cpu().item()),
                "r31_effect_context_acc": float(
                    context_acc.detach().cpu().item()
                ),
                "r31_effect_shuffle_mean": float(
                    np.mean(shuffle_delta_np[shuffle_valid])
                )
                if bool(np.any(shuffle_valid))
                else 0.0,
                "r31_effect_shuffle_abs_mean": float(
                    np.mean(np.abs(shuffle_delta_np[shuffle_valid]))
                )
                if bool(np.any(shuffle_valid))
                else 0.0,
                "r31_effect_shuffle_valid_frac": float(np.mean(shuffle_valid)),
                "r31_effect_reward_mean": float(np.mean(reward_np)),
                "r31_effect_reward_applied_endpoints": float(
                    len(rows) if self.r31_reward_enabled else 0
                ),
            }
        )
        for skill in range(self.n_skills):
            skill_mask = label_np == skill
            metrics[f"r31_effect_skill_{skill}_samples"] = float(
                np.sum(skill_mask)
            )
            metrics[f"r31_effect_skill_{skill}_mean"] = (
                float(np.mean(delta_np[skill_mask]))
                if bool(np.any(skill_mask))
                else 0.0
            )

        self._r31_scored_rows = rows
        self._r31_scored_batch = (effect_np, context_np, label_np)
        return metrics

    def r31_update_effect_posterior(self) -> dict[str, float]:
        """Fit R31 after low PPO, using only this rollout's natural windows."""

        metrics = {
            "r31_effect_posterior_samples": 0.0,
            "r31_effect_posterior_loss": 0.0,
            "r31_effect_full_loss": 0.0,
            "r31_effect_context_loss": 0.0,
        }
        if not self.r31_enabled or self._r31_scored_batch is None:
            return metrics
        if self.r31_effect_posterior is None or self.r31_effect_opt is None:
            raise RuntimeError("R31 is enabled without its posterior optimizer")
        effect_np, context_np, label_np = self._r31_scored_batch
        effect_t = torch.as_tensor(effect_np, dtype=torch.float32, device=self.device)
        context_t = torch.as_tensor(context_np, dtype=torch.float32, device=self.device)
        label_t = torch.as_tensor(label_np, dtype=torch.long, device=self.device)
        self.r31_effect_posterior.train()
        full_logits, context_logits = self.r31_effect_posterior(
            effect_t,
            context_t,
        )
        terms = self.r31_effect_posterior.losses(
            full_logits,
            context_logits,
            label_t,
        )
        self.r31_effect_opt.zero_grad()
        terms["loss"].backward()
        torch.nn.utils.clip_grad_norm_(self.r31_effect_posterior.parameters(), 10.0)
        self.r31_effect_opt.step()
        metrics.update(
            {
                "r31_effect_posterior_samples": float(label_np.size),
                "r31_effect_posterior_loss": float(
                    terms["loss"].detach().cpu().item()
                ),
                "r31_effect_full_loss": float(
                    terms["full_loss"].detach().cpu().item()
                ),
                "r31_effect_context_loss": float(
                    terms["context_loss"].detach().cpu().item()
                ),
            }
        )
        self._r31_scored_rows = []
        self._r31_scored_batch = None
        return metrics
