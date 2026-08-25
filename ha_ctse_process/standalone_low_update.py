"""Low-level PPO update mechanics for the standalone process agent."""

from __future__ import annotations

from typing import Any

import random
import numpy as np
import torch
import torch.nn.functional as F

import ha_ctse_process.standalone_segments as standalone_segments


class StandaloneLowUpdateMixin:
    def _empty_low_metrics(self) -> dict[str, float]:
        return {
            "low_loss": 0.0,
            "low_policy_loss": 0.0,
            "low_value_loss": 0.0,
            "low_entropy_loss": 0.0,
            "low_actor_loss": 0.0,
            "low_critic_loss": 0.0,
            "low_entropy": 0.0,
            "low_sequence_chunks": 0.0,
            "low_value_norm_mean": float(self.low_value_norm.mean) if self.low_value_norm is not None else 0.0,
            "low_value_norm_std": float(np.sqrt(self.low_value_norm.var)) if self.low_value_norm is not None else 0.0,
            "low_value_error_abs_mean": 0.0,
            "low_value_error_rmse": 0.0,
            "low_advantage_std": 0.0,
            "low_ratio_mean": 0.0,
            "low_clip_frac": 0.0,
            "low_approx_kl": 0.0,
            "low_actor_grad_norm": 0.0,
            "low_critic_grad_norm": 0.0,
            "low_optimizer_steps": 0.0,
            "low_return_env_count": 0.0,
            "low_replay_logp_max_error": 0.0,
            "low_squashed_action_policy": 0.0,
            "low_fixed_primitive_policy": 0.0,
            "low_actor_h_norm_mean": 0.0,
            "low_critic_h_norm_mean": 0.0,
            "low_skill_usage_entropy": 0.0,
            "low_skill_return_std": 0.0,
            "low_skill_return_range": 0.0,
            "low_skill_value_error_abs_std": 0.0,
            "low_skill_entropy_std": 0.0,
            "low_team_usage_entropy": 0.0,
            "low_team_return_std": 0.0,
            "low_team_return_range": 0.0,
            "low_team_value_error_abs_std": 0.0,
            "return_mean": 0.0,
        }

    @staticmethod
    def _grad_norm(parameters) -> float:
        total = 0.0
        for param in parameters:
            if param.grad is None:
                continue
            grad = param.grad.detach()
            total += float(torch.sum(grad * grad).cpu().item())
        return float(np.sqrt(max(total, 0.0)))

    def _low_rollout_diagnostics(
        self,
        rollout: standalone_segments.Rollout,
        returns: np.ndarray,
        advantages: np.ndarray,
        values: np.ndarray,
    ) -> dict[str, float]:
        skills = np.asarray(rollout.skills, dtype=np.int64).reshape(-1)
        team_codes = np.asarray(rollout.team_codes, dtype=np.int64).reshape(-1)
        if team_codes.size:
            team_codes = np.repeat(team_codes, self.n_agents)
        returns_flat = np.asarray(returns, dtype=np.float32).reshape(-1)
        advantages_flat = np.asarray(advantages, dtype=np.float32).reshape(-1)
        values_flat = np.asarray(values, dtype=np.float32).reshape(-1)
        value_error = returns_flat - values_flat
        value_error_abs = np.abs(value_error)
        actor_hxs = np.asarray(rollout.low_actor_hxs, dtype=np.float32)
        critic_hxs = np.asarray(rollout.low_critic_hxs, dtype=np.float32)
        actor_h_norm = (
            np.linalg.norm(actor_hxs, axis=-1).reshape(-1)
            if actor_hxs.size
            else np.asarray([], dtype=np.float32)
        )
        critic_h_norm = (
            np.linalg.norm(critic_hxs, axis=-1).reshape(-1)
            if critic_hxs.size
            else np.asarray([], dtype=np.float32)
        )
        skill_return = self._group_mean_summary(skills, returns_flat, self.n_skills)
        skill_value_error = self._group_mean_summary(skills, value_error_abs, self.n_skills)
        team_return = self._group_mean_summary(team_codes, returns_flat, self.num_team_codes)
        team_value_error = self._group_mean_summary(team_codes, value_error_abs, self.num_team_codes)
        return {
            "low_value_error_abs_mean": float(np.mean(value_error_abs)) if value_error_abs.size else 0.0,
            "low_value_error_rmse": float(np.sqrt(np.mean(value_error * value_error))) if value_error.size else 0.0,
            "low_advantage_std": float(np.std(advantages_flat)) if advantages_flat.size else 0.0,
            "low_actor_h_norm_mean": float(np.mean(actor_h_norm)) if actor_h_norm.size else 0.0,
            "low_critic_h_norm_mean": float(np.mean(critic_h_norm)) if critic_h_norm.size else 0.0,
            "low_skill_usage_entropy": self._label_entropy_np(skills, self.n_skills),
            "low_skill_return_std": skill_return["std"],
            "low_skill_return_range": skill_return["range"],
            "low_skill_value_error_abs_std": skill_value_error["std"],
            "low_team_usage_entropy": self._label_entropy_np(team_codes, self.num_team_codes),
            "low_team_return_std": team_return["std"],
            "low_team_return_range": team_return["range"],
            "low_team_value_error_abs_std": team_value_error["std"],
        }

    def _low_returns(self, rollout: standalone_segments.Rollout) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        rewards = np.asarray(rollout.rewards, dtype=np.float32)
        values = np.asarray(rollout.values, dtype=np.float32)
        dones = np.asarray(rollout.dones, dtype=np.bool_)
        env_ids = np.asarray(
            rollout.env_ids if rollout.env_ids else [0 for _ in range(len(rewards))],
            dtype=np.int64,
        )
        bootstrap_values = getattr(rollout, "bootstrap_values", {}) or {}
        returns = np.zeros_like(rewards, dtype=np.float32)
        advantages = np.zeros_like(rewards, dtype=np.float32)
        for env_id in np.unique(env_ids):
            indices = np.flatnonzero(env_ids == int(env_id))
            last_gae = np.zeros(self.n_agents, dtype=np.float32)
            default_bootstrap = np.zeros(self.n_agents, dtype=np.float32)
            final_bootstrap = np.asarray(
                bootstrap_values.get(int(env_id), default_bootstrap),
                dtype=np.float32,
            ).reshape(-1)
            if final_bootstrap.size != self.n_agents:
                fitted = np.zeros(self.n_agents, dtype=np.float32)
                n = min(fitted.size, final_bootstrap.size)
                if n > 0:
                    fitted[:n] = final_bootstrap[:n]
                final_bootstrap = fitted
            for pos in range(indices.size - 1, -1, -1):
                idx = int(indices[pos])
                if bool(dones[idx]):
                    next_value = default_bootstrap
                    next_nonterminal = 0.0
                elif pos + 1 < indices.size:
                    next_value = values[int(indices[pos + 1])]
                    next_nonterminal = 1.0
                else:
                    next_value = final_bootstrap
                    next_nonterminal = 1.0
                delta = rewards[idx] + self.gamma * next_value * next_nonterminal - values[idx]
                last_gae = delta + self.gamma * self.low_gae_lambda * next_nonterminal * last_gae
                advantages[idx] = last_gae
                returns[idx] = advantages[idx] + values[idx]
        finite = np.isfinite(advantages)
        if np.any(finite):
            mean = float(np.mean(advantages[finite]))
            std = float(np.std(advantages[finite]))
            advantages = (advantages - mean) / (std + 1e-8)
        return returns, advantages.astype(np.float32), values, env_ids

    def _low_sequence_chunks(
        self,
        rollout: standalone_segments.Rollout,
        returns: np.ndarray,
        advantages: np.ndarray,
        env_ids: np.ndarray,
    ):
        obs_arr = np.asarray(rollout.obs, dtype=np.float32)
        states_arr = np.asarray(rollout.states, dtype=np.float32)
        skills_arr = np.asarray(rollout.skills, dtype=np.int64)
        team_codes_arr = np.asarray(rollout.team_codes, dtype=np.int64)
        actions_arr = np.asarray(rollout.actions)
        old_logp_arr = np.asarray(rollout.logp, dtype=np.float32)
        dones_arr = np.asarray(rollout.dones, dtype=np.bool_)
        actor_hxs_arr = np.asarray(rollout.low_actor_hxs, dtype=np.float32)
        critic_hxs_arr = np.asarray(rollout.low_critic_hxs, dtype=np.float32)
        values_arr = np.asarray(rollout.values, dtype=np.float32)
        seq_len = int(max(self.low_sequence_length, 1))
        chunks = []
        for env_id in np.unique(env_ids):
            indices = np.flatnonzero(env_ids == int(env_id))
            for start in range(0, len(indices), seq_len):
                chunk_indices = indices[start:start + seq_len]
                if chunk_indices.size == 0:
                    continue
                first = int(chunk_indices[0])
                chunks.append(
                    {
                        "indices": chunk_indices.astype(np.int64),
                        "initial_actor_hxs": actor_hxs_arr[first],
                        "initial_critic_hxs": critic_hxs_arr[first],
                    }
                )
        if not chunks:
            return {
                "num_chunks": 0,
                "lengths": np.zeros(0, dtype=np.int64),
            }

        num_chunks = len(chunks)
        lengths = np.asarray(
            [int(chunk["indices"].size) for chunk in chunks], dtype=np.int64
        )
        time_steps = int(np.max(lengths))
        obs = np.zeros(
            (time_steps, num_chunks, self.n_agents, self.obs_dim), dtype=np.float32
        )
        states = np.zeros(
            (time_steps, num_chunks, self.state_dim), dtype=np.float32
        )
        skills = np.zeros(
            (time_steps, num_chunks, self.n_agents), dtype=np.int64
        )
        team_codes = np.zeros((time_steps, num_chunks), dtype=np.int64)
        old_logp = np.zeros(
            (time_steps, num_chunks, self.n_agents), dtype=np.float32
        )
        old_values = np.zeros_like(old_logp, dtype=np.float32)
        packed_returns = np.zeros_like(old_logp, dtype=np.float32)
        packed_advantages = np.zeros_like(old_logp, dtype=np.float32)
        masks = np.zeros_like(old_logp, dtype=np.float32)
        reset_masks = np.ones_like(old_logp, dtype=np.float32)
        if self.action_space_type == "continuous":
            actions = np.zeros(
                (
                    time_steps,
                    num_chunks,
                    self.n_agents,
                    self.action_dim,
                ),
                dtype=np.float32,
            )
        else:
            actions = np.zeros(
                (time_steps, num_chunks, self.n_agents), dtype=np.int64
            )
        initial_actor_hxs = np.zeros(
            (num_chunks, self.n_agents, self.low_rnn_hidden_size),
            dtype=np.float32,
        )
        initial_critic_hxs = np.zeros_like(initial_actor_hxs, dtype=np.float32)

        for chunk_id, chunk in enumerate(chunks):
            chunk_indices = chunk["indices"]
            length = int(chunk_indices.size)
            row_slice = slice(0, length)
            obs[row_slice, chunk_id] = obs_arr[chunk_indices]
            states[row_slice, chunk_id] = states_arr[chunk_indices]
            skills[row_slice, chunk_id] = skills_arr[chunk_indices]
            team_codes[row_slice, chunk_id] = team_codes_arr[chunk_indices]
            actions[row_slice, chunk_id] = actions_arr[chunk_indices]
            old_logp[row_slice, chunk_id] = old_logp_arr[chunk_indices]
            old_values[row_slice, chunk_id] = values_arr[chunk_indices]
            packed_returns[row_slice, chunk_id] = returns[chunk_indices]
            packed_advantages[row_slice, chunk_id] = advantages[chunk_indices]
            masks[row_slice, chunk_id, :] = 1.0
            reset_masks[row_slice, chunk_id, :] = (
                ~dones_arr[chunk_indices]
            ).astype(np.float32)[:, None]
            initial_actor_hxs[chunk_id] = chunk["initial_actor_hxs"]
            initial_critic_hxs[chunk_id] = chunk["initial_critic_hxs"]

        return {
            "num_chunks": num_chunks,
            "lengths": lengths,
            "obs": torch.as_tensor(obs, dtype=torch.float32, device=self.device),
            "states": torch.as_tensor(states, dtype=torch.float32, device=self.device),
            "skills": torch.as_tensor(skills, dtype=torch.long, device=self.device),
            "team_codes": torch.as_tensor(
                team_codes, dtype=torch.long, device=self.device
            ),
            "actions": torch.as_tensor(
                actions,
                dtype=(
                    torch.float32
                    if self.action_space_type == "continuous"
                    else torch.long
                ),
                device=self.device,
            ),
            "old_logp": torch.as_tensor(
                old_logp, dtype=torch.float32, device=self.device
            ),
            "old_values": torch.as_tensor(
                old_values, dtype=torch.float32, device=self.device
            ),
            "returns": torch.as_tensor(
                packed_returns, dtype=torch.float32, device=self.device
            ),
            "advantages": torch.as_tensor(
                packed_advantages, dtype=torch.float32, device=self.device
            ),
            "masks": torch.as_tensor(
                masks, dtype=torch.float32, device=self.device
            ),
            "reset_masks": torch.as_tensor(
                reset_masks, dtype=torch.float32, device=self.device
            ),
            "initial_actor_hxs": torch.as_tensor(
                initial_actor_hxs, dtype=torch.float32, device=self.device
            ),
            "initial_critic_hxs": torch.as_tensor(
                initial_critic_hxs, dtype=torch.float32, device=self.device
            ),
        }

    def _low_batch_from_chunk_ids(
        self,
        data: dict[str, Any],
        chunk_ids,
    ):
        chunk_ids_np = np.asarray(chunk_ids, dtype=np.int64).reshape(-1)
        if chunk_ids_np.size <= 0:
            raise ValueError("low recurrent batch requires at least one chunk")
        time_steps = int(np.max(data["lengths"][chunk_ids_np]))
        chunk_ids_t = torch.as_tensor(
            chunk_ids_np, dtype=torch.long, device=self.device
        )
        batch_size = int(chunk_ids_np.size)
        time_major_names = (
            "obs",
            "states",
            "skills",
            "team_codes",
            "actions",
            "old_logp",
            "old_values",
            "returns",
            "advantages",
            "masks",
            "reset_masks",
        )
        batch = {
            name: data[name][:time_steps].index_select(1, chunk_ids_t)
            for name in time_major_names
        }
        batch["agent_ids"] = torch.arange(
            self.n_agents, dtype=torch.long, device=self.device
        ).reshape(1, 1, self.n_agents).expand(
            time_steps, batch_size, self.n_agents
        )
        batch["initial_actor_hxs"] = data["initial_actor_hxs"].index_select(
            0, chunk_ids_t
        )
        batch["initial_critic_hxs"] = data["initial_critic_hxs"].index_select(
            0, chunk_ids_t
        )
        return batch

    def _update_low_recurrent(self, rollout: standalone_segments.Rollout) -> dict[str, float]:
        returns, advantages, old_values_np, env_ids = self._low_returns(rollout)
        rollout_diagnostics = self._low_rollout_diagnostics(rollout, returns, advantages, old_values_np)
        if self.low_value_norm is not None:
            self.low_value_norm.update(returns.reshape(-1))
        data = self._low_sequence_chunks(rollout, returns, advantages, env_ids)
        num_chunks = int(data["num_chunks"])
        if num_chunks <= 0:
            return self._empty_low_metrics()

        low_replay_logp_max_error_t = torch.zeros(
            (), dtype=torch.float32, device=self.device
        )
        numpy_rng_state = np.random.get_state()
        python_rng_state = random.getstate()
        torch_rng_state = torch.random.get_rng_state()
        cuda_rng_state = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
        try:
            with torch.no_grad():
                for start in range(0, num_chunks, self.low_sequence_batch_size):
                    batch_ids = np.arange(
                        start,
                        min(start + self.low_sequence_batch_size, num_chunks),
                        dtype=np.int64,
                    )
                    batch = self._low_batch_from_chunk_ids(data, batch_ids)
                    logp, _entropy, _values = self.low.evaluate_sequence(
                        batch["obs"],
                        batch["skills"],
                        batch["actions"],
                        batch["states"],
                        batch["team_codes"],
                        batch["agent_ids"],
                        batch["initial_actor_hxs"],
                        batch["initial_critic_hxs"],
                        batch["masks"],
                        batch["reset_masks"],
                    )
                    valid = batch["masks"] > 0.0
                    replay_error = torch.abs(
                        logp[valid] - batch["old_logp"][valid]
                    )
                    low_replay_logp_max_error_t = torch.maximum(
                        low_replay_logp_max_error_t,
                        replay_error.max(),
                    )
        finally:
            np.random.set_state(numpy_rng_state)
            random.setstate(python_rng_state)
            torch.random.set_rng_state(torch_rng_state)
            if cuda_rng_state is not None:
                torch.cuda.set_rng_state_all(cuda_rng_state)

        metric_sums = torch.zeros(10, dtype=torch.float64, device=self.device)
        skill_entropy_sums_t = torch.zeros(
            self.n_skills, dtype=torch.float64, device=self.device
        )
        skill_entropy_counts_t = torch.zeros_like(skill_entropy_sums_t)
        actor_params = list(self.low.actor_update_parameters())
        critic_params = list(self.low.critic_update_parameters())
        update_count = 0
        for _epoch in range(self.low_ppo_epochs):
            order = self._low_update_shuffle_rng.permutation(num_chunks)
            for start in range(0, len(order), self.low_sequence_batch_size):
                batch_ids = order[start : start + self.low_sequence_batch_size]
                batch = self._low_batch_from_chunk_ids(data, batch_ids)
                logp, entropy, values = self.low.evaluate_sequence(
                    batch["obs"],
                    batch["skills"],
                    batch["actions"],
                    batch["states"],
                    batch["team_codes"],
                    batch["agent_ids"],
                    batch["initial_actor_hxs"],
                    batch["initial_critic_hxs"],
                    batch["masks"],
                    batch["reset_masks"],
                )
                valid = batch["masks"] > 0.0
                ratio = torch.exp(logp[valid] - batch["old_logp"][valid].detach())
                adv = batch["advantages"][valid]
                old_logp_valid = batch["old_logp"][valid].detach()
                policy_loss = -torch.min(
                    ratio * adv,
                    torch.clamp(ratio, 1.0 - self.low_clip, 1.0 + self.low_clip) * adv,
                ).mean()
                target_returns = batch["returns"]
                old_values = batch["old_values"]
                if self.low_value_norm is not None:
                    target_returns = self.low_value_norm.normalize_tensor(target_returns)
                    old_values = self.low_value_norm.normalize_tensor(old_values)
                    if self.low_value_clip > 0.0:
                        target_returns = target_returns.clamp(-self.low_value_clip, self.low_value_clip)
                target_returns = target_returns.detach()
                old_values = old_values.detach()
                if self.low_value_clip > 0.0:
                    clipped_values = old_values + (values - old_values).clamp(
                        -self.low_value_clip,
                        self.low_value_clip,
                    )
                    value_loss_unclipped = (values - target_returns).pow(2)
                    value_loss_clipped = (clipped_values - target_returns).pow(2)
                    value_loss = 0.5 * torch.max(
                        value_loss_unclipped[valid],
                        value_loss_clipped[valid],
                    ).mean()
                else:
                    value_loss = 0.5 * F.mse_loss(values[valid], target_returns[valid])
                entropy_mean = entropy[valid].mean()
                entropy_loss = -self.low_entropy_coef * entropy_mean
                actor_loss = policy_loss + entropy_loss
                critic_loss = self.low_value_loss_coef * value_loss
                loss = actor_loss + critic_loss

                self.low_actor_opt.zero_grad()
                self.low_critic_opt.zero_grad()
                loss.backward()
                if self.low_max_grad_norm > 0.0:
                    actor_grad_norm = torch.nn.utils.clip_grad_norm_(
                        actor_params, self.low_max_grad_norm
                    )
                    critic_grad_norm = torch.nn.utils.clip_grad_norm_(
                        critic_params, self.low_max_grad_norm
                    )
                else:
                    actor_grad_norm = torch.as_tensor(
                        self._grad_norm(actor_params),
                        dtype=torch.float32,
                        device=self.device,
                    )
                    critic_grad_norm = torch.as_tensor(
                        self._grad_norm(critic_params),
                        dtype=torch.float32,
                        device=self.device,
                    )
                self.low_actor_opt.step()
                self.low_critic_opt.step()

                with torch.no_grad():
                    metric_sums += torch.stack(
                        (
                            loss.detach(),
                            policy_loss.detach(),
                            value_loss.detach(),
                            entropy_loss.detach(),
                            entropy_mean.detach(),
                            ratio.detach().mean(),
                            (
                                torch.abs(ratio.detach() - 1.0) > self.low_clip
                            ).float().mean(),
                            (
                                old_logp_valid - logp[valid].detach()
                            ).mean(),
                            actor_grad_norm.detach(),
                            critic_grad_norm.detach(),
                        )
                    ).to(dtype=torch.float64)
                    skills_valid = batch["skills"][valid].long()
                    entropy_valid = entropy[valid].detach().to(dtype=torch.float64)
                    skill_entropy_sums_t.scatter_add_(
                        0, skills_valid, entropy_valid
                    )
                    skill_entropy_counts_t.scatter_add_(
                        0, skills_valid, torch.ones_like(entropy_valid)
                    )
                update_count += 1

        denom = max(update_count, 1)
        summary = torch.cat(
            (
                metric_sums,
                low_replay_logp_max_error_t.reshape(1).to(dtype=torch.float64),
                skill_entropy_sums_t,
                skill_entropy_counts_t,
            )
        ).detach().cpu().numpy()
        (
            total_loss,
            total_policy_loss,
            total_value_loss,
            total_entropy_loss,
            total_entropy,
            total_ratio_mean,
            total_clip_frac,
            total_approx_kl,
            total_actor_grad_norm,
            total_critic_grad_norm,
        ) = summary[:10]
        low_replay_logp_max_error = float(summary[10])
        skill_start = 11
        skill_entropy_sums = summary[
            skill_start : skill_start + self.n_skills
        ]
        skill_entropy_counts = summary[
            skill_start + self.n_skills : skill_start + 2 * self.n_skills
        ]
        active_skill_entropy = skill_entropy_counts > 0.0
        if np.any(active_skill_entropy):
            skill_entropy_means = skill_entropy_sums[active_skill_entropy] / skill_entropy_counts[active_skill_entropy]
            low_skill_entropy_std = float(np.std(skill_entropy_means))
        else:
            low_skill_entropy_std = 0.0
        return {
            "low_loss": total_loss / denom,
            "low_policy_loss": total_policy_loss / denom,
            "low_value_loss": total_value_loss / denom,
            "low_entropy_loss": total_entropy_loss / denom,
            "low_actor_loss": (total_policy_loss + total_entropy_loss) / denom,
            "low_critic_loss": self.low_value_loss_coef * total_value_loss / denom,
            "low_entropy": total_entropy / denom,
            "low_sequence_chunks": float(num_chunks),
            "low_value_norm_mean": float(self.low_value_norm.mean) if self.low_value_norm is not None else 0.0,
            "low_value_norm_std": float(np.sqrt(self.low_value_norm.var)) if self.low_value_norm is not None else 0.0,
            "low_ratio_mean": total_ratio_mean / denom,
            "low_clip_frac": total_clip_frac / denom,
            "low_approx_kl": total_approx_kl / denom,
            "low_actor_grad_norm": total_actor_grad_norm / denom,
            "low_critic_grad_norm": total_critic_grad_norm / denom,
            "low_optimizer_steps": float(update_count),
            "low_replay_logp_max_error": low_replay_logp_max_error,
            "low_skill_entropy_std": low_skill_entropy_std,
            "return_mean": float(np.mean(returns)),
            **rollout_diagnostics,
        }

    def update_low(self, rollout: standalone_segments.Rollout) -> dict[str, float]:
        if not rollout.rewards:
            return self._empty_low_metrics()
        if self.r39_toy_fixed_skill_primitives:
            env_ids = np.asarray(
                rollout.env_ids if rollout.env_ids else [0 for _ in rollout.rewards],
                dtype=np.int64,
            )
            return {
                **self._empty_low_metrics(),
                "low_return_env_count": float(np.unique(env_ids).size),
                "low_fixed_primitive_policy": 1.0,
            }
        if self.use_recurrent_low_level:
            return self._update_low_recurrent(rollout)
        returns, advantages, old_values_np, env_ids = self._low_returns(rollout)
        rollout_diagnostics = self._low_rollout_diagnostics(
            rollout, returns, advantages, old_values_np
        )

        obs_t = torch.as_tensor(np.asarray(rollout.obs), dtype=torch.float32, device=self.device).reshape(-1, rollout.obs[0].shape[-1])
        skills_t = torch.as_tensor(np.asarray(rollout.skills), dtype=torch.long, device=self.device).reshape(-1)
        if self.action_space_type == "continuous":
            actions_t = torch.as_tensor(
                np.asarray(rollout.actions),
                dtype=torch.float32,
                device=self.device,
            ).reshape(-1, self.action_dim)
        else:
            actions_t = torch.as_tensor(
                np.asarray(rollout.actions),
                dtype=torch.long,
                device=self.device,
            ).reshape(-1)
        old_logp_t = torch.as_tensor(np.asarray(rollout.logp), dtype=torch.float32, device=self.device).reshape(-1)
        returns_t = torch.as_tensor(returns, dtype=torch.float32, device=self.device).reshape(-1)
        adv_t = torch.as_tensor(advantages, dtype=torch.float32, device=self.device).reshape(-1)
        old_values_t = torch.as_tensor(old_values_np, dtype=torch.float32, device=self.device).reshape(-1)

        with torch.no_grad():
            replay_logp, _replay_entropy, _replay_values = self.low.evaluate(
                obs_t, skills_t, actions_t
            )
            replay_error = float(
                torch.max(torch.abs(replay_logp - old_logp_t)).detach().cpu().item()
            )

        totals = {
            "loss": 0.0,
            "policy": 0.0,
            "value": 0.0,
            "entropy_loss": 0.0,
            "entropy": 0.0,
            "ratio": 0.0,
            "clip": 0.0,
            "kl": 0.0,
            "actor_grad": 0.0,
            "critic_grad": 0.0,
        }
        skill_entropy_sums = np.zeros(self.n_skills, dtype=np.float64)
        skill_entropy_counts = np.zeros(self.n_skills, dtype=np.float64)
        update_count = 0
        for _epoch in range(self.low_ppo_epochs):
            logp, entropy, new_values = self.low.evaluate(obs_t, skills_t, actions_t)
            ratio = torch.exp(logp - old_logp_t.detach())
            policy_loss = -torch.min(
                ratio * adv_t,
                torch.clamp(ratio, 1.0 - self.low_clip, 1.0 + self.low_clip) * adv_t,
            ).mean()
            target_returns = returns_t.detach()
            previous_values = old_values_t.detach()
            if self.low_value_clip > 0.0:
                clipped_values = previous_values + (new_values - previous_values).clamp(
                    -self.low_value_clip, self.low_value_clip
                )
                value_loss = 0.5 * torch.max(
                    (new_values - target_returns).pow(2),
                    (clipped_values - target_returns).pow(2),
                ).mean()
            else:
                value_loss = 0.5 * F.mse_loss(new_values, target_returns)
            entropy_mean = entropy.mean()
            entropy_loss = -self.low_entropy_coef * entropy_mean
            critic_loss = self.low_value_loss_coef * value_loss
            loss = policy_loss + critic_loss + entropy_loss

            self.low_opt.zero_grad()
            loss.backward()
            actor_params = list(self.low.actor_update_parameters())
            critic_params = list(self.low.critic_update_parameters())
            if self.low_max_grad_norm > 0.0:
                actor_grad_norm = float(
                    torch.nn.utils.clip_grad_norm_(
                        actor_params, self.low_max_grad_norm
                    ).detach().cpu().item()
                )
                critic_grad_norm = float(
                    torch.nn.utils.clip_grad_norm_(
                        critic_params, self.low_max_grad_norm
                    ).detach().cpu().item()
                )
            else:
                actor_grad_norm = self._grad_norm(actor_params)
                critic_grad_norm = self._grad_norm(critic_params)
            self.low_opt.step()

            old_logp_detached = old_logp_t.detach()
            totals["loss"] += float(loss.detach().cpu().item())
            totals["policy"] += float(policy_loss.detach().cpu().item())
            totals["value"] += float(value_loss.detach().cpu().item())
            totals["entropy_loss"] += float(entropy_loss.detach().cpu().item())
            totals["entropy"] += float(entropy_mean.detach().cpu().item())
            totals["ratio"] += float(ratio.detach().mean().cpu().item())
            totals["clip"] += float(
                (torch.abs(ratio.detach() - 1.0) > self.low_clip)
                .float()
                .mean()
                .cpu()
                .item()
            )
            totals["kl"] += float(
                (old_logp_detached - logp.detach()).mean().cpu().item()
            )
            totals["actor_grad"] += actor_grad_norm
            totals["critic_grad"] += critic_grad_norm
            skills_np = skills_t.detach().cpu().numpy().astype(np.int64)
            entropy_np = entropy.detach().cpu().numpy().astype(np.float64)
            for skill_id in range(self.n_skills):
                mask = skills_np == skill_id
                if np.any(mask):
                    skill_entropy_sums[skill_id] += float(np.sum(entropy_np[mask]))
                    skill_entropy_counts[skill_id] += float(np.sum(mask))
            update_count += 1

        denom = max(update_count, 1)
        active_skill_entropy = skill_entropy_counts > 0.0
        low_skill_entropy_std = (
            float(
                np.std(
                    skill_entropy_sums[active_skill_entropy]
                    / skill_entropy_counts[active_skill_entropy]
                )
            )
            if np.any(active_skill_entropy)
            else 0.0
        )
        return {
            **self._empty_low_metrics(),
            "low_loss": totals["loss"] / denom,
            "low_policy_loss": totals["policy"] / denom,
            "low_value_loss": totals["value"] / denom,
            "low_entropy_loss": totals["entropy_loss"] / denom,
            "low_actor_loss": (totals["policy"] + totals["entropy_loss"]) / denom,
            "low_critic_loss": self.low_value_loss_coef * totals["value"] / denom,
            "low_entropy": totals["entropy"] / denom,
            "low_sequence_chunks": 0.0,
            "low_value_norm_mean": 0.0,
            "low_value_norm_std": 0.0,
            "low_ratio_mean": totals["ratio"] / denom,
            "low_clip_frac": totals["clip"] / denom,
            "low_approx_kl": totals["kl"] / denom,
            "low_actor_grad_norm": totals["actor_grad"] / denom,
            "low_critic_grad_norm": totals["critic_grad"] / denom,
            "low_optimizer_steps": float(update_count),
            "low_return_env_count": float(np.unique(env_ids).size),
            "low_replay_logp_max_error": replay_error,
            "low_squashed_action_policy": float(self.action_space_type == "continuous"),
            "low_skill_entropy_std": low_skill_entropy_std,
            "return_mean": float(returns.mean()),
            **rollout_diagnostics,
        }
