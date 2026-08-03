"""Standalone low-level inference methods."""

from __future__ import annotations

import numpy as np
import torch


class StandaloneLowInferenceMixin:
    def act_low_batch(
        self,
        observations,
        *,
        env_ids=None,
        deterministic: bool = False,
        states=None,
        return_context: bool = False,
        capture_deterministic_action: bool = False,
    ):
        obs_rows = [self._joint_obs_array(obs) for obs in observations]
        batch_size = len(obs_rows)
        if batch_size <= 0:
            raise ValueError("act_low_batch requires at least one environment")
        if env_ids is None:
            env_ids_np = np.arange(batch_size, dtype=np.int64)
        else:
            env_ids_np = np.asarray(tuple(env_ids), dtype=np.int64).reshape(-1)
        if env_ids_np.shape != (batch_size,):
            raise ValueError("act_low_batch env_ids must match observations")
        if np.any(env_ids_np < 0) or np.any(env_ids_np >= self.num_envs):
            raise ValueError("act_low_batch env_id is outside the policy runtime")
        if np.unique(env_ids_np).size != batch_size:
            raise ValueError("act_low_batch env_ids must be unique")

        if states is None:
            state_rows = [None for _ in range(batch_size)]
        else:
            state_rows = list(states)
            if len(state_rows) != batch_size:
                raise ValueError("act_low_batch states must match observations")

        obs_np = np.asarray(obs_rows, dtype=np.float32)
        state_np = np.stack(
            [
                self._state_array(state_rows[row], obs_rows[row])
                for row in range(batch_size)
            ],
            axis=0,
        ).astype(np.float32, copy=False)
        skills_np = self.active_skills[env_ids_np].astype(np.int64, copy=True)
        team_codes_np = self.active_team_codes[env_ids_np].astype(np.int64, copy=True)
        actor_hxs_before = self.low_actor_hxs[env_ids_np].astype(np.float32, copy=True)
        critic_hxs_before = self.low_critic_hxs[env_ids_np].astype(np.float32, copy=True)

        flat_rows = batch_size * self.n_agents
        obs_t = torch.as_tensor(obs_np, dtype=torch.float32, device=self.device).reshape(
            flat_rows, self.obs_dim
        )
        skills_t = torch.as_tensor(
            skills_np, dtype=torch.long, device=self.device
        ).reshape(flat_rows)
        deterministic_actions = None
        with torch.no_grad():
            if self.use_recurrent_low_level:
                state_t = torch.as_tensor(
                    state_np, dtype=torch.float32, device=self.device
                ).unsqueeze(1).expand(
                    batch_size, self.n_agents, self.state_dim
                ).reshape(
                    flat_rows, self.state_dim
                )
                team_code_t = torch.as_tensor(
                    team_codes_np, dtype=torch.long, device=self.device
                ).unsqueeze(1).expand(
                    batch_size, self.n_agents
                ).reshape(flat_rows)
                agent_ids_t = torch.arange(
                    self.n_agents, dtype=torch.long, device=self.device
                ).repeat(batch_size)
                actor_hxs_t = torch.as_tensor(
                    actor_hxs_before, dtype=torch.float32, device=self.device
                ).reshape(flat_rows, self.low_rnn_hidden_size)
                critic_hxs_t = torch.as_tensor(
                    critic_hxs_before, dtype=torch.float32, device=self.device
                ).reshape(flat_rows, self.low_rnn_hidden_size)
                capture_deterministic = bool(capture_deterministic_action)
                low_kwargs = (
                    {"return_deterministic_action": True}
                    if capture_deterministic
                    else {}
                )
                low_result = self.low.act(
                    obs_t,
                    skills_t,
                    actor_hxs_t,
                    state_t,
                    team_code_t,
                    critic_hxs_t,
                    agent_ids_t,
                    deterministic=deterministic,
                    **low_kwargs,
                )
                if capture_deterministic:
                    (
                        actions,
                        logp,
                        _,
                        values,
                        new_actor_hxs,
                        new_critic_hxs,
                        deterministic_actions,
                    ) = low_result
                else:
                    actions, logp, _, values, new_actor_hxs, new_critic_hxs = low_result
                if self.low_value_norm is not None:
                    values = self.low_value_norm.denormalize_tensor(values)
            else:
                actions, logp, _, values = self.low.act(
                    obs_t,
                    skills_t,
                    deterministic=deterministic,
                )
                new_actor_hxs = None
                new_critic_hxs = None

        action_shape = (
            (batch_size, self.n_agents, self.action_dim)
            if self.action_space_type == "continuous"
            else (batch_size, self.n_agents)
        )
        actions_np = actions.detach().cpu().numpy().reshape(action_shape).astype(
            np.int64 if self.action_space_type == "discrete" else np.float32,
            copy=False,
        )
        logp_np = logp.detach().cpu().numpy().reshape(batch_size, self.n_agents).astype(
            np.float32, copy=False
        )
        values_np = values.detach().cpu().numpy().reshape(batch_size, self.n_agents).astype(
            np.float32, copy=False
        )
        deterministic_actions_np = None
        if deterministic_actions is not None:
            deterministic_actions_np = (
                deterministic_actions.detach()
                .cpu()
                .numpy()
                .reshape(batch_size, self.n_agents, self.action_dim)
                .astype(np.float32, copy=False)
            )
        if new_actor_hxs is not None and new_critic_hxs is not None:
            actor_hxs_after = (
                new_actor_hxs.detach()
                .cpu()
                .numpy()
                .reshape(batch_size, self.n_agents, self.low_rnn_hidden_size)
                .astype(np.float32, copy=False)
            )
            critic_hxs_after = (
                new_critic_hxs.detach()
                .cpu()
                .numpy()
                .reshape(batch_size, self.n_agents, self.low_rnn_hidden_size)
                .astype(np.float32, copy=False)
            )
            self.low_actor_hxs[env_ids_np] = actor_hxs_after
            self.low_critic_hxs[env_ids_np] = critic_hxs_after

        contexts = []
        for row, env_id in enumerate(env_ids_np):
            context = {
                "state": state_np[row].copy(),
                "team_code": int(team_codes_np[row]),
                "actor_hxs": actor_hxs_before[row].copy(),
                "critic_hxs": critic_hxs_before[row].copy(),
            }
            if deterministic_actions_np is not None:
                context["deterministic_actions"] = deterministic_actions_np[row].copy()
            self._last_low_context[int(env_id)] = context
            contexts.append(context)

        result = (actions_np, logp_np, values_np)
        if return_context:
            return (*result, contexts)
        return result

    def act_low(
        self,
        obs: np.ndarray,
        env_id: int = 0,
        deterministic: bool = False,
        state=None,
        return_context: bool = False,
        capture_deterministic_action: bool = False,
    ):
        result = self.act_low_batch(
            [obs],
            env_ids=[int(env_id)],
            deterministic=deterministic,
            states=[state],
            return_context=return_context,
            capture_deterministic_action=capture_deterministic_action,
        )
        if return_context:
            actions, logp, values, contexts = result
            return actions[0], logp[0], values[0], contexts[0]
        actions, logp, values = result
        return actions[0], logp[0], values[0]
