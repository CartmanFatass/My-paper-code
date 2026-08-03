"""Standard standalone training-loop owner for HA-CTSE process-core."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

from ha_ctse_process.event_process_runner import (
    _run_iteration5_process_semantics_branch,
)
from ha_ctse_process import standalone_manifest
from ha_ctse_process import standalone_novelty
from ha_ctse_process import standalone_variable_roster_runner
from ha_ctse_process.infrastructure_profiling import InfrastructureProfiler
from ha_ctse_process.standalone_evaluation import evaluate
from ha_ctse_process.standalone_metrics import (
    audit_r37_identity_observation,
    emit,
    empty_r37_identity_metrics,
    export_update_metrics,
    log_eval_metrics,
    log_train_metrics,
)
from ha_ctse_process.checkpoint_io import (
    load_checkpoint,
    prune_periodic_checkpoints,
    save_checkpoint,
)
from ha_ctse_process.standalone_agent import (
    StandaloneProcessAgent,
)
from ha_ctse_process.standalone_segments import Rollout
from ha_ctse_process.standalone_cli import (
    action_space_details,
    create_agent,
    create_collector,
)
from ha_ctse_process.standalone_contracts import (
    dispatch_variable_roster_event_boundary,
    enforce_iteration5_process_semantics_contract,
    is_iteration5_process_semantics,
    is_variable_roster_event,
)
from ha_ctse_process.standalone_event_support import (
    enforce_variable_roster_event_resume_boundary,
)


def empty_r30_no_high_metrics() -> dict[str, float]:
    return {
        "r30_high_rows": 0.0,
        "r30_decision_rows": 0.0,
        "high_optimizer_steps": 0.0,
    }


def _cuda_synchronize_callback(agent: StandaloneProcessAgent):
    device = torch.device(getattr(agent, "device", "cuda"))
    return lambda: torch.cuda.synchronize(device)


def train_loop(config, args: argparse.Namespace, writer) -> tuple[StandaloneProcessAgent, int, int]:
    if is_iteration5_process_semantics(config):
        enforce_iteration5_process_semantics_contract(config, args)
        return _run_iteration5_process_semantics_branch(config, args, writer)
    if is_variable_roster_event(config):
        enforce_variable_roster_event_resume_boundary(config, args)
        if not hasattr(config, "scenario") or not hasattr(args, "rollout_length"):
            dispatch_variable_roster_event_boundary(config)
        return standalone_variable_roster_runner.run_variable_roster_event_branch(
            config, args, writer
        )
    num_envs = max(int(args.num_envs), 1)
    collector = create_collector(config, args, scale_mode="train", num_envs=num_envs)
    try:
        observations, states, _infos = collector.reset_all(seed=int(args.seed))
        # Per-env pre-step state/reward info: the post-step state of step t is the
        # pre-step (true segment-start) state of step t+1.  Seeded from reset info.
        def _seed_info(infos, key):
            out = [{} for _ in range(num_envs)]
            if isinstance(infos, (list, tuple)):
                for i in range(min(num_envs, len(infos))):
                    info_i = infos[i]
                    if isinstance(info_i, dict) and isinstance(info_i.get(key), dict):
                        out[i] = dict(info_i[key])
            return out

        prev_state_info = _seed_info(_infos, "state_info")
        prev_reward_info = _seed_info(_infos, "reward_info")
        effect_views = [
            (
                np.asarray(info.get("intrinsic_effect_view"), dtype=np.float32).copy()
                if isinstance(info, dict) and info.get("intrinsic_effect_view") is not None
                else None
            )
            for info in _infos
        ]
        env = SimpleNamespace(**collector.spec)
        action_space_type, _, _ = action_space_details(env)
        state_dim = int(collector.spec.get("state_dim") or 0) or (
            int(np.asarray(states[0], dtype=np.float32).reshape(-1).size)
            if states and states[0] is not None
            else None
        )
        agent = create_agent(config, args, env, num_envs=num_envs, state_dim=state_dim)
        profiler = None
        profile_interval = int(getattr(args, "infrastructure_profile_interval", 0))
        if profile_interval > 0:
            synchronize = (
                _cuda_synchronize_callback(agent)
                if torch.cuda.is_available()
                and str(getattr(agent, "device", "")).startswith("cuda")
                else None
            )
            profiler = InfrastructureProfiler(
                args.log_dir,
                profile_interval,
                cuda_synchronize=synchronize,
            )
        aem_enabled = bool(getattr(config, "aem_joint_novelty_enabled", False))
        if (bool(getattr(agent, "r31_enabled", False)) or aem_enabled) and any(
            view is None for view in effect_views
        ):
            raise RuntimeError(
                "active position-only objective requires intrinsic_effect_view"
            )
        aem_novelty = (
            standalone_novelty.EpisodicJointPositionNovelty(
                num_envs=num_envs,
                grid_size=int(getattr(config, "aem_joint_position_grid_size", 5)),
                episode_horizon=int(getattr(config, "aem_episode_horizon", 80)),
            )
            if aem_enabled
            else None
        )

        total_steps = 0
        update_idx = 0
        if args.resume_from:
            total_steps, update_idx = load_checkpoint(args.resume_from, agent, load_optimizers=True)
            emit(
                args,
                "standalone_resume "
                f"path={args.resume_from} total_steps={total_steps} update_idx={update_idx}"
            )

        standalone_manifest.export_run_manifest(
            args,
            config,
            env=env,
            agent=agent,
            total_steps=total_steps,
            update_idx=update_idx,
            mode="train",
        )
        param_counts = agent.parameter_counts()
        emit(
            args,
            "standalone_train_start "
            f"scenario={config.scenario} preset={args.preset or 'none'} "
            f"num_envs={num_envs} n_agents={env.n_uavs} obs_dim={env.obs_dim} action_dim={env.action_dim} "
            f"action_space_type={action_space_type} collector={args.collector_backend} "
            f"policy_update=on_policy "
            f"process_reward_mode={getattr(config, 'process_reward_mode', 'mi_outcome')} "
            f"process_reward_injection={getattr(config, 'process_reward_injection', 'none')} "
            f"process_warmup_steps={int(getattr(config, 'process_reward_warmup_steps', 0))} "
            f"process_shortcut_margin={float(getattr(config, 'process_shortcut_margin', 0.0))} "
            f"process_shortcut_margin_coef={float(getattr(config, 'process_shortcut_margin_coef', 0.0))} "
            f"context_shortcut={bool(getattr(config, 'use_context_skill_shortcut', True))} "
            f"context_shortcut_coef={float(getattr(config, 'context_shortcut_coef', 0.0))} "
            f"transition_context_shortcut_coef={float(getattr(config, 'transition_context_shortcut_coef', 0.0))} "
            f"intrinsic_phase_bins={int(getattr(config, 'intrinsic_phase_bins', 0))} "
            f"transition_disc={bool(getattr(config, 'use_transition_skill_discriminator', True))} "
            f"transition_coef={float(getattr(config, 'transition_skill_coef', 0.0))} "
            f"transition_reward_coef={float(getattr(config, 'transition_skill_reward_coef', 0.0))} "
            f"transition_reward_warmup={int(getattr(config, 'transition_skill_reward_warmup_steps', 0))} "
            f"transition_max_samples={int(getattr(config, 'transition_skill_max_samples', 0))} "
            f"topology_role_probe={bool(getattr(config, 'use_topology_role_probe', True))} "
            f"topology_role_coef={float(getattr(config, 'topology_role_coef', 0.0))} "
            f"topology_role_injection={getattr(config, 'topology_role_injection', 'none')} "
            f"topology_role_reward_coef={float(getattr(config, 'topology_role_reward_coef', 0.0))} "
            f"skill_effect_probe={bool(getattr(config, 'skill_effect_discovery_on', False))} "
            f"skill_effect_reward={bool(getattr(config, 'skill_effect_reward_on', False))} "
            f"skill_effect_horizons={tuple(getattr(config, 'skill_effect_horizons', ())) } "
            f"skill_effect_stride={int(getattr(config, 'skill_effect_stride', 0))} "
            f"skill_effect_max_windows={int(getattr(config, 'skill_effect_max_windows', 0))} "
            f"skill_effect_hidden_dim={int(getattr(config, 'skill_effect_hidden_dim', 0))} "
            f"skill_effect_group_balanced_loss={bool(getattr(config, 'skill_effect_group_balanced_loss', True))} "
            f"skill_effect_intervention_probe={bool(getattr(config, 'skill_effect_intervention_probe_on', False))} "
            f"skill_effect_intervention_max_samples={int(getattr(config, 'skill_effect_intervention_max_samples', 0))} "
            f"skill_force_probe={bool(getattr(config, 'skill_force_probe_on', False))} "
            f"skill_force_reward={bool(getattr(config, 'enable_skill_forcing_reward', False))} "
            f"skill_force_injection={getattr(config, 'skill_force_reward_injection', 'low_only')} "
            f"skill_force_disc_coef={float(getattr(config, 'skill_force_disc_coef', 0.0))} "
            f"skill_force_effect_coef={float(getattr(config, 'skill_force_effect_coef', 0.0))} "
            f"skill_force_duration_entropy_coef={float(getattr(config, 'skill_force_duration_entropy_coef', 0.0))} "
            f"skill_force_warmup={int(getattr(config, 'skill_force_warmup_steps', 0))} "
            f"skill_force_shortcut_gate={bool(getattr(config, 'skill_force_kill_on_shortcut', True))} "
            f"skill_force_use_comm_fields={bool(getattr(config, 'skill_force_use_comm_fields', False))} "
            f"semantic_shortcut_hard_stop={bool(getattr(config, 'semantic_shortcut_hard_stop_enabled', True))} "
            f"semantic_shortcut_margin={float(getattr(config, 'semantic_shortcut_hard_stop_margin', 0.0))} "
            f"g_intervention_kl={bool(getattr(config, 'use_g_intervention_kl_diagnostic', True))} "
            f"g_info_diag={bool(getattr(config, 'use_g_info_diagnostic', True))} "
            f"g_info_obj={bool(getattr(config, 'enable_g_info_objective', False))} "
            f"g_info_coef_skill={float(getattr(config, 'g_info_coef_skill', 0.0))} "
            f"g_info_coef_duration={float(getattr(config, 'g_info_coef_duration', 0.0))} "
            f"g_info_coef_edit={float(getattr(config, 'g_info_coef_edit', 0.0))} "
            f"g_info_warmup={int(getattr(config, 'g_info_warmup_steps', 0))} "
            f"g_info_anneal={int(getattr(config, 'g_info_anneal_steps', 0))} "
            f"situation_diag={bool(getattr(config, 'enable_situation_diagnostics', False))} "
            f"situation_hazard_control={bool(getattr(config, 'enable_situation_hazard_control', False))} "
            f"situation_source={getattr(config, 'situation_substrate_source', 'omega')} "
            f"situation_num_kappa={int(getattr(config, 'situation_num_kappa', 0))} "
            f"situation_debounce={int(getattr(config, 'situation_debounce_steps', 0))} "
            f"situation_hazard_mode={getattr(config, 'situation_hazard_mode', 'diagnostic')} "
            f"situation_hazard_interval={int(getattr(config, 'situation_hazard_check_interval', 0))} "
            f"situation_hazard_min_age={int(getattr(config, 'situation_hazard_min_age', 0))} "
            f"situation_hazard_hidden={int(getattr(config, 'situation_hazard_hidden_dim', 0))} "
            f"situation_hazard_entropy_coef={float(getattr(config, 'situation_hazard_entropy_coef', 0.0))} "
            f"situation_hazard_value_coef={float(getattr(config, 'situation_hazard_value_coef', 0.0))} "
            f"situation_hazard_clip_epsilon={float(getattr(config, 'situation_hazard_clip_epsilon', 0.0))} "
            f"situation_hazard_reward_coef={float(getattr(config, 'situation_hazard_reward_coef', 0.0))} "
            f"situation_hazard_conservative_guard={bool(getattr(config, 'situation_hazard_conservative_guard', False))} "
            f"situation_hazard_min_dwell={int(getattr(config, 'situation_hazard_min_dwell_checks', 0))} "
            f"situation_hazard_confirm_changes={int(getattr(config, 'situation_hazard_confirm_changes', 0))} "
            f"situation_hazard_max_force_rate={float(getattr(config, 'situation_hazard_max_force_rate', 1.0))} "
            f"situation_hazard_rate_window={int(getattr(config, 'situation_hazard_rate_window', 0))} "
            f"team_transition_probe={bool(getattr(config, 'enable_team_transition_probe', False))} "
            f"team_transition_reward={bool(getattr(config, 'enable_team_transition_reward', False))} "
            f"team_transition_coef={float(getattr(config, 'team_transition_coef', 0.0))} "
            f"team_transition_clip={float(getattr(config, 'team_transition_clip', 0.0))} "
            f"team_transition_warmup={int(getattr(config, 'team_transition_warmup_steps', 0))} "
            f"team_intent={bool(getattr(config, 'enable_team_intent', False))} "
            f"team_intent_k={int(getattr(config, 'team_intent_k', 0))} "
            f"team_disc_probe={bool(getattr(config, 'enable_team_disc_probe', False))} "
            f"team_disc_reward={bool(getattr(config, 'enable_team_disc_reward', False))} "
            f"team_disc_coef={float(getattr(config, 'team_disc_coef', 0.0))} "
            f"team_disc_clip={float(getattr(config, 'team_disc_clip', 0.0))} "
            f"team_disc_warmup={int(getattr(config, 'team_disc_warmup_steps', 0))} "
            f"r24_qd_probe={bool(getattr(config, 'enable_team_conditioned_qd_probe', False))} "
            f"r24_qd_export={bool(getattr(config, 'r24_qd_export_windows', False))} "
            f"r24_qd_export_dir={getattr(config, 'r24_qd_export_dir', '')} "
            f"r24_qd_export_max_rows={int(getattr(config, 'r24_qd_export_max_rows_per_update', 0))} "
            f"intrinsic_segment_gate={bool(getattr(config, 'intrinsic_segment_gate_enabled', True))} "
            f"intrinsic_gate_margin={float(getattr(config, 'intrinsic_segment_gate_margin', 0.0))} "
            f"intrinsic_gate_min_segments={int(getattr(config, 'intrinsic_segment_gate_min_segments', 0))} "
            f"smdp_discount={bool(getattr(config, 'use_smdp_discounted_high_return', True))} "
            f"smdp_bootstrap={bool(getattr(config, 'use_smdp_bootstrap', True))} "
            f"smdp_bootstrap_coef={float(getattr(config, 'smdp_bootstrap_coef', 1.0))} "
            f"duration_entropy_floor={bool(getattr(config, 'duration_entropy_floor_enabled', False))} "
            f"duration_entropy_floor_threshold={float(getattr(config, 'duration_entropy_floor_threshold', 0.0))} "
            f"duration_entropy_floor_coef={float(getattr(config, 'duration_entropy_floor_coef', 0.0))} "
            f"duration_entropy_floor_warmup={int(getattr(config, 'duration_entropy_floor_warmup_steps', 0))} "
            f"z_entropy_floor={bool(getattr(config, 'z_entropy_floor_enabled', False))} "
            f"z_entropy_floor_threshold={float(getattr(config, 'z_entropy_floor_threshold', 0.0))} "
            f"z_entropy_floor_coef={float(getattr(config, 'z_entropy_floor_coef', 0.0))} "
            f"z_entropy_floor_warmup={int(getattr(config, 'z_entropy_floor_warmup_steps', 0))} "
            f"reward_ratio_guard_mode={str(getattr(config, 'reward_ratio_guard_mode', 'kill'))} "
            f"high_value_norm={bool(getattr(config, 'use_high_value_norm', True))} "
            f"recurrent_low={bool(getattr(config, 'use_recurrent_low_level', True))} "
            f"low_arch={getattr(config, 'low_level_architecture', 'strict_hmasd_mappo')} "
            f"low_actor_team_code={bool(getattr(config, 'low_actor_condition_on_team_code', False))} "
            f"prototype_response={bool(getattr(config, 'use_prototype_response_skills', False))} "
            f"prototype_extra_codes={int(getattr(config, 'prototype_skill_extra_codes', 0))} "
            f"legacy_n_skills={int(getattr(config, 'legacy_n_skills_override', 0))} "
            f"ar_selection={bool(getattr(agent, 'use_autoregressive_selection', False))} "
            f"parallel_selection={bool(getattr(agent, 'parallel_selection', False))} "
            f"ar_prefix_mode={str(getattr(agent, 'ar_prefix_mode', 'none'))} "
            f"high_omega={bool(getattr(config, 'high_condition_on_omega', False))} "
            f"agent_proto_rel={bool(getattr(config, 'use_agent_prototype_relevance', False))} "
            f"per_agent_kappa={bool(getattr(config, 'use_per_agent_kappa', False))} "
            f"proto_disc_probe={bool(getattr(config, 'enable_prototype_disc_probe', False))} "
            f"proto_disc_reward={bool(getattr(config, 'enable_prototype_disc_reward', False))} "
            f"proto_disc_learned_prior={bool(getattr(config, 'prototype_disc_use_learned_prior', False))} "
            f"proto_disc_condition={getattr(config, 'prototype_disc_condition', 'kappa')} "
            f"proto_disc_coef={float(getattr(config, 'prototype_disc_reward_coef', 0.0))} "
            f"compact_return_head={bool(getattr(config, 'use_compact_return_head', False))} "
            f"network_scale={getattr(config, 'network_scale_profile', 'custom')} "
            f"low_value_norm={bool(getattr(config, 'use_low_value_norm', True))} "
            f"low_seq_len={int(getattr(config, 'low_sequence_length', 0))} "
            f"clip={float(getattr(config, 'clip_epsilon', 0.2))} "
            f"low_clip={float(getattr(config, 'low_clip_epsilon', getattr(config, 'clip_epsilon', 0.2)))} "
            f"params_total={param_counts.get('total_trainable', 0)} "
            f"params_high_stack={param_counts.get('high_stack', 0)} "
            f"params_low={param_counts.get('low', 0)} "
            f"params_process_stack={param_counts.get('process_stack', 0)} "
            f"params_skill_effect={param_counts.get('skill_effect_discovery', 0)} "
            f"params_team_transition={param_counts.get('team_transition', 0)} "
            f"params_team_disc={param_counts.get('team_discriminator', 0)} "
            f"duration_candidates={tuple(getattr(config, 'skill_lifetime_candidates', ())) } "
            f"rollout_length={args.rollout_length} total_timesteps={args.total_timesteps} "
            f"save_interval={args.save_interval} checkpoint_keep_last={args.checkpoint_keep_last}"
        )

        last_eval_step = int(total_steps)
        proto_ratio_over05_count = 0
        proto_ratio_consecutive_over05_count = 0
        proto_ratio_kill_triggered_count = 0
        proto_ratio_guard_warmup_steps = int(getattr(config, "prototype_disc_warmup_steps", 0))
        reward_ratio_guard_mode = str(getattr(config, "reward_ratio_guard_mode", "kill")).lower()
        if reward_ratio_guard_mode not in {"kill", "warn"}:
            reward_ratio_guard_mode = "kill"
        team_disc_ratio_over05_count = 0
        team_disc_ratio_consecutive_over05_count = 0
        team_disc_ratio_kill_triggered_count = 0
        team_disc_ratio_guard_warmup_steps = int(getattr(config, "team_disc_warmup_steps", 0))
        combined_intrinsic_ratio_over05_count = 0
        combined_intrinsic_ratio_consecutive_over05_count = 0
        combined_intrinsic_ratio_kill_triggered_count = 0
        while total_steps < int(args.total_timesteps):
            rollout = Rollout()
            episode_rewards = []
            r37_update_metrics = empty_r37_identity_metrics(config)
            for _local_step in range(int(args.rollout_length)):
                if profiler is not None:
                    profiler.start("inference", torch_phase=True)
                pre_obs = list(observations)
                rollout_base = len(rollout.rewards)
                pre_rollout_indices = [
                    rollout_base + env_id for env_id in range(num_envs)
                ]
                for env_id in range(num_envs):
                    obs = observations[env_id]
                    identity_audit = audit_r37_identity_observation(
                        config, obs, states[env_id]
                    )
                    r37_update_metrics["r37_identity_audit_rows"] += identity_audit[
                        "r37_identity_audit_rows"
                    ]
                    for field in (
                        "r37_identity_slot_max_abs_error",
                        "r37_critic_identity_max_abs_error",
                    ):
                        r37_update_metrics[field] = max(
                            r37_update_metrics[field], identity_audit[field]
                        )
                    rollout_idx = pre_rollout_indices[env_id]
                    agent.maybe_assign_skills(
                        obs,
                        state=states[env_id],
                        step=rollout_idx,
                        k=int(args.skill_interval),
                        env_id=env_id,
                        policy_update=int(update_idx + 1),
                        effect_view=effect_views[env_id],
                    )

                (
                    pre_actions_batch,
                    pre_logp_batch,
                    pre_values_batch,
                    pre_low_context,
                ) = agent.act_low_batch(
                    pre_obs,
                    env_ids=range(num_envs),
                    states=states,
                    return_context=True,
                )
                pre_actions = [pre_actions_batch[env_id] for env_id in range(num_envs)]
                pre_logp = [pre_logp_batch[env_id] for env_id in range(num_envs)]
                pre_values = [pre_values_batch[env_id] for env_id in range(num_envs)]

                if profiler is not None:
                    profiler.stop(torch_phase=True)
                    profiler.start("collector_env")
                step_results = collector.step(pre_actions)
                if profiler is not None:
                    profiler.stop()
                    profiler.start("transition_ledger_pack")
                for env_id, result in enumerate(step_results):
                    obs = pre_obs[env_id]
                    actions = pre_actions[env_id]
                    logp = pre_logp[env_id]
                    values = pre_values[env_id]
                    low_context = pre_low_context[env_id]
                    rollout_idx = pre_rollout_indices[env_id]
                    next_obs = result.obs
                    reward = result.reward
                    terminated = result.terminated
                    truncated = result.truncated
                    info = result.info
                    done = bool(terminated or truncated)
                    next_effect_view = info.get("intrinsic_effect_view")
                    if bool(getattr(agent, "r31_enabled", False)) or aem_enabled:
                        if next_effect_view is None:
                            raise RuntimeError(
                                "active position-only objective step did not expose "
                                "intrinsic_effect_view"
                            )
                        next_effect_view = np.asarray(
                            next_effect_view,
                            dtype=np.float32,
                        ).copy()
                    reward_components = info.get("reward_components", {})
                    individual_rewards = np.asarray(
                        reward_components.get(
                            "individual_rewards",
                            [float(reward)] * int(env.n_uavs),
                        ),
                        dtype=np.float32,
                    )
                    if individual_rewards.shape[0] != int(env.n_uavs):
                        individual_rewards = np.full(int(env.n_uavs), float(reward), dtype=np.float32)
                    low_training_rewards = individual_rewards.copy()
                    if aem_novelty is not None:
                        bonus = aem_novelty.observe(env_id, next_effect_view)
                        low_training_rewards += np.float32(bonus)

                    agent.segments.append(
                        env_id,
                        obs,
                        actions,
                        individual_rewards,
                        next_obs,
                        rollout_idx,
                        reward_info=info.get("reward_info", {}),
                        state_info=info.get("state_info", {}),
                        next_state=info.get("next_state", states[env_id]),
                        done=done,
                        pre_state_info=prev_state_info[env_id],
                        pre_reward_info=prev_reward_info[env_id],
                        deterministic_actions=low_context.get("deterministic_actions"),
                    )
                    # This step's post-step state is the next step's pre-step state.
                    prev_state_info[env_id] = info.get("state_info", {}) or {}
                    prev_reward_info[env_id] = info.get("reward_info", {}) or {}
                    rollout.env_ids.append(int(env_id))
                    rollout.obs.append(np.asarray(obs, dtype=np.float32))
                    rollout.states.append(np.asarray(low_context["state"], dtype=np.float32))
                    rollout.next_states.append(np.asarray(info.get("next_state", states[env_id]), dtype=np.float32))
                    rollout.skills.append(agent.active_skills[env_id].copy())
                    rollout.team_codes.append(int(low_context["team_code"]))
                    rollout.actions.append(actions.copy())
                    if "deterministic_actions" in low_context:
                        rollout.deterministic_actions.append(
                            np.asarray(low_context["deterministic_actions"], dtype=np.float32).copy()
                        )
                    rollout.logp.append(logp.copy())
                    rollout.values.append(values.copy())
                    rollout.low_actor_hxs.append(np.asarray(low_context["actor_hxs"], dtype=np.float32))
                    rollout.low_critic_hxs.append(np.asarray(low_context["critic_hxs"], dtype=np.float32))
                    rollout.rewards.append(low_training_rewards)
                    rollout.dones.append(done)
                    episode_rewards.append(float(np.mean(individual_rewards)))

                    total_steps += 1
                    agent.record_environment_step(
                        env_id,
                        reward=float(reward),
                        next_obs=next_obs,
                        next_state=info.get("next_state", states[env_id]),
                        done=done,
                        effect_view=next_effect_view,
                        rollout_index=rollout_idx,
                    )
                    observations[env_id] = next_obs
                    states[env_id] = info.get("next_state", states[env_id])
                    effect_views[env_id] = next_effect_view
                    if done:
                        agent.segments.flush(env_id, reason="episode")
                        observations[env_id], info = collector.reset_one(env_id)
                        if aem_novelty is not None:
                            aem_novelty.reset_env(env_id)
                        states[env_id] = info.get("state")
                        # Re-seed pre-step info from the reset state for the next segment.
                        prev_state_info[env_id] = info.get("state_info", {}) or {}
                        prev_reward_info[env_id] = info.get("reward_info", {}) or {}
                        reset_effect_view = info.get("intrinsic_effect_view")
                        effect_views[env_id] = (
                            np.asarray(reset_effect_view, dtype=np.float32).copy()
                            if reset_effect_view is not None
                            else None
                        )
                        if bool(getattr(agent, "r31_enabled", False)) and effect_views[env_id] is None:
                            raise RuntimeError(
                                "R31 reset did not expose intrinsic_effect_view"
                            )
                        agent.reset_env_state(env_id)
                if profiler is not None:
                    profiler.stop()
                if total_steps >= int(args.total_timesteps):
                    break

            if profiler is not None:
                profiler.start("transition_ledger_pack")
            agent.truncate_high_rows_for_update(observations, states)
            agent.segments.flush(reason="update")
            rollout.bootstrap_values = agent.low_bootstrap_values(observations, states)
            r31_score_metrics = agent.r31_score_complete_windows(rollout)
            if profiler is not None:
                profiler.stop()
                profiler.start("update", torch_phase=True)
            process_metrics = agent.process_update(
                rollout,
                total_steps=total_steps,
                update_idx=update_idx + 1,
            )
            process_metrics.update(
                aem_novelty.pop_update_metrics()
                if aem_novelty is not None
                else standalone_novelty.empty_aem_metrics(active=False)
            )
            process_metrics.update(r37_update_metrics)
            process_metrics.update(r31_score_metrics)
            low_metrics = agent.update_low(rollout)
            process_metrics.update(agent.r31_update_effect_posterior())
            if bool(getattr(agent, "constant_skill_no_high", False)):
                process_metrics.update(empty_r30_no_high_metrics())
            if bool(getattr(agent, "r30_enabled", False)) and not bool(
                getattr(agent, "constant_skill_no_high", False)
            ):
                process_metrics.update(
                    agent.update_high_from_checks(total_steps=total_steps)
                )
            update_idx += 1
            if bool(getattr(agent, "r30_enabled", False)) and not bool(
                getattr(agent, "constant_skill_no_high", False)
            ):
                agent.start_high_continuations_after_update(
                    observations,
                    states,
                    policy_update=update_idx + 1,
                )
            if profiler is not None:
                profiler.stop(torch_phase=True)
                profiler.start("metrics")
            env_reward_mean = float(np.mean(episode_rewards)) if episode_rewards else 0.0
            proto_ratio = float(process_metrics.get("proto_disc_reward_env_ratio", 0.0))
            proto_reward_steps = float(process_metrics.get("proto_disc_reward_applied_steps", 0.0))
            proto_ratio_guard_active = (
                proto_reward_steps > 0.0 and int(total_steps) >= int(proto_ratio_guard_warmup_steps)
            )
            proto_ratio_kill_message = ""
            if proto_ratio_guard_active and not np.isfinite(proto_ratio):
                proto_ratio_kill_message = (
                    "prototype discriminator reward/env ratio became non-finite "
                    f"at update={update_idx} total_steps={total_steps}"
                )
            elif proto_ratio_guard_active:
                if proto_ratio > 0.5:
                    proto_ratio_over05_count += 1
                    proto_ratio_consecutive_over05_count += 1
                else:
                    proto_ratio_consecutive_over05_count = 0
                if proto_ratio > 1.0:
                    proto_ratio_kill_message = (
                        "prototype discriminator reward/env ratio exceeded instant guard "
                        f"ratio={proto_ratio:.6f} update={update_idx} total_steps={total_steps}"
                    )
                elif proto_ratio_consecutive_over05_count >= 5:
                    proto_ratio_kill_message = (
                        "prototype discriminator reward/env ratio exceeded sustained guard "
                        f"ratio={proto_ratio:.6f} count={proto_ratio_consecutive_over05_count} "
                        f"update={update_idx} total_steps={total_steps}"
                    )
            else:
                proto_ratio_consecutive_over05_count = 0
            if proto_ratio_kill_message:
                proto_ratio_kill_triggered_count += 1
            process_metrics["proto_disc_reward_env_ratio_over05_count"] = float(proto_ratio_over05_count)
            process_metrics["proto_disc_reward_env_ratio_guard_active"] = float(proto_ratio_guard_active)
            process_metrics["proto_disc_reward_env_ratio_kill_triggered"] = float(
                proto_ratio_kill_triggered_count
            )
            team_disc_ratio = float(process_metrics.get("team_disc_reward_env_ratio", 0.0))
            team_disc_reward_steps = float(process_metrics.get("team_disc_reward_applied_steps", 0.0))
            team_disc_ratio_guard_active = (
                team_disc_reward_steps > 0.0 and int(total_steps) >= int(team_disc_ratio_guard_warmup_steps)
            )
            team_disc_ratio_kill_message = ""
            if team_disc_ratio_guard_active and not np.isfinite(team_disc_ratio):
                team_disc_ratio_kill_message = (
                    "team discriminator reward/env ratio became non-finite "
                    f"at update={update_idx} total_steps={total_steps}"
                )
            elif team_disc_ratio_guard_active:
                if team_disc_ratio > 0.5:
                    team_disc_ratio_over05_count += 1
                    team_disc_ratio_consecutive_over05_count += 1
                else:
                    team_disc_ratio_consecutive_over05_count = 0
                if team_disc_ratio > 1.0:
                    team_disc_ratio_kill_message = (
                        "team discriminator reward/env ratio exceeded instant guard "
                        f"ratio={team_disc_ratio:.6f} update={update_idx} total_steps={total_steps}"
                    )
                elif team_disc_ratio_consecutive_over05_count >= 5:
                    team_disc_ratio_kill_message = (
                        "team discriminator reward/env ratio exceeded sustained guard "
                        f"ratio={team_disc_ratio:.6f} count={team_disc_ratio_consecutive_over05_count} "
                        f"update={update_idx} total_steps={total_steps}"
                    )
            else:
                team_disc_ratio_consecutive_over05_count = 0
            if team_disc_ratio_kill_message:
                team_disc_ratio_kill_triggered_count += 1
            process_metrics["team_disc_reward_env_ratio_over05_count"] = float(team_disc_ratio_over05_count)
            process_metrics["team_disc_reward_env_ratio_guard_active"] = float(team_disc_ratio_guard_active)
            process_metrics["team_disc_reward_env_ratio_kill_triggered"] = float(
                team_disc_ratio_kill_triggered_count
            )
            proto_component_ratio = float(abs(proto_ratio)) if proto_reward_steps > 0.0 else 0.0
            team_disc_component_ratio = float(abs(team_disc_ratio)) if team_disc_reward_steps > 0.0 else 0.0
            combined_intrinsic_ratio = float(proto_component_ratio + team_disc_component_ratio)
            combined_intrinsic_reward_steps = proto_reward_steps + team_disc_reward_steps
            combined_intrinsic_guard_active = bool(
                combined_intrinsic_reward_steps > 0.0
                and (proto_ratio_guard_active or team_disc_ratio_guard_active)
            )
            combined_intrinsic_kill_message = ""
            if combined_intrinsic_guard_active and not np.isfinite(combined_intrinsic_ratio):
                combined_intrinsic_kill_message = (
                    "combined intrinsic reward/env ratio became non-finite "
                    f"at update={update_idx} total_steps={total_steps}"
                )
            elif combined_intrinsic_guard_active:
                if combined_intrinsic_ratio > 0.5:
                    combined_intrinsic_ratio_over05_count += 1
                    combined_intrinsic_ratio_consecutive_over05_count += 1
                else:
                    combined_intrinsic_ratio_consecutive_over05_count = 0
                if combined_intrinsic_ratio > 1.0:
                    combined_intrinsic_kill_message = (
                        "combined intrinsic reward/env ratio exceeded instant guard "
                        f"ratio={combined_intrinsic_ratio:.6f} update={update_idx} total_steps={total_steps}"
                    )
                elif combined_intrinsic_ratio_consecutive_over05_count >= 5:
                    combined_intrinsic_kill_message = (
                        "combined intrinsic reward/env ratio exceeded sustained guard "
                        f"ratio={combined_intrinsic_ratio:.6f} "
                        f"count={combined_intrinsic_ratio_consecutive_over05_count} "
                        f"update={update_idx} total_steps={total_steps}"
                    )
            else:
                combined_intrinsic_ratio_consecutive_over05_count = 0
            if combined_intrinsic_kill_message:
                combined_intrinsic_ratio_kill_triggered_count += 1
            process_metrics["combined_intrinsic_env_ratio"] = float(combined_intrinsic_ratio)
            process_metrics["combined_intrinsic_env_ratio_over05_count"] = float(
                combined_intrinsic_ratio_over05_count
            )
            process_metrics["combined_intrinsic_env_ratio_guard_active"] = float(
                combined_intrinsic_guard_active
            )
            process_metrics["combined_intrinsic_env_ratio_kill_triggered"] = float(
                combined_intrinsic_ratio_kill_triggered_count
            )
            emit(
                args,
                "standalone_update "
                f"update={update_idx} total_steps={total_steps} "
                f"env_reward_mean={env_reward_mean:.6f} "
                f"aem_active={process_metrics.get('aem_active', 0.0):.0f} "
                f"aem_bonus_applied_steps={process_metrics.get('aem_bonus_applied_steps', 0.0):.0f} "
                f"aem_bonus_sum={process_metrics.get('aem_bonus_sum', 0.0):.6f} "
                f"aem_bonus_max={process_metrics.get('aem_bonus_max', 0.0):.6f} "
                f"aem_count_resets={process_metrics.get('aem_count_resets', 0.0):.0f} "
                f"process_segments={process_metrics['process_segments']:.0f} "
                f"process_loss={process_metrics['process_loss']:.6f} "
                f"process_mi={process_metrics.get('process_mi_estimate_mean', 0.0):.6f} "
                f"process_resid_mi={process_metrics.get('process_residual_mi_mean', 0.0):.6f} "
                f"process_shortcut_acc={process_metrics.get('process_shortcut_max_acc', 0.0):.3f} "
                f"process_margin_loss={process_metrics.get('process_shortcut_margin_loss', 0.0):.6f} "
                f"process_warmup={process_metrics.get('process_reward_warmup_active', 0.0):.0f} "
                f"trans_samples={process_metrics.get('transition_skill_samples', 0.0):.0f} "
                f"trans_acc={process_metrics.get('transition_skill_acc', 0.0):.3f} "
                f"trans_ctx_acc={process_metrics.get('transition_skill_context_acc', 0.0):.3f} "
                f"trans_mi={process_metrics.get('transition_skill_mi_mean', 0.0):.6f} "
                f"trans_resid_mi={process_metrics.get('transition_skill_residual_mi_mean', 0.0):.6f} "
                f"trans_reward={process_metrics.get('transition_skill_reward_mean', 0.0):.6f} "
                f"trans_active={process_metrics.get('transition_skill_reward_active', 0.0):.0f} "
                f"r31_windows={process_metrics.get('r31_effect_windows', 0.0):.0f} "
                f"r31_info={process_metrics.get('r31_effect_information_mean', 0.0):.6f} "
                f"r31_full_acc={process_metrics.get('r31_effect_full_acc', 0.0):.3f} "
                f"r31_ctx_acc={process_metrics.get('r31_effect_context_acc', 0.0):.3f} "
                f"r31_reward={process_metrics.get('r31_effect_reward_mean', 0.0):.6f} "
                f"team_t_samples={process_metrics.get('team_transition_samples', 0.0):.0f} "
                f"team_t_mi={process_metrics.get('team_transition_mi_mean', 0.0):.6f} "
                f"team_t_self={process_metrics.get('team_transition_self_frac', 0.0):.3f} "
                f"team_t_rew={process_metrics.get('team_transition_reward_high_mean', 0.0):.6f} "
                f"team_t_ratio={process_metrics.get('team_transition_reward_env_ratio', 0.0):.3f} "
                f"team_t_renew_corr={process_metrics.get('team_transition_reward_renewal_corr', 0.0):.3f} "
                f"z_ent={process_metrics.get('z_usage_entropy', 0.0):.3f} "
                f"z_ent_floor={process_metrics.get('z_entropy_floor_active', 0.0):.0f} "
                f"z_ent_gap={process_metrics.get('z_entropy_floor_gap', 0.0):.3f} "
                f"z_dwell={process_metrics.get('z_dwell', 0.0):.2f} "
                f"z_trunc={process_metrics.get('z_boundary_trunc_rate', 0.0):.3f} "
                f"z_trunc_d3={process_metrics.get('z_boundary_trunc_rate_dur3', 0.0):.3f} "
                f"z_trunc_d7={process_metrics.get('z_boundary_trunc_rate_dur7', 0.0):.3f} "
                f"z_trunc_d13={process_metrics.get('z_boundary_trunc_rate_dur13', 0.0):.3f} "
                f"z_trunc_d24={process_metrics.get('z_boundary_trunc_rate_dur24', 0.0):.3f} "
                f"z_itv={process_metrics.get('z_assignment_itv', 0.0):.6f} "
                f"team_disc_acc={process_metrics.get('team_disc_acc', 0.0):.3f} "
                f"team_disc_resid={process_metrics.get('team_disc_residual_mean', 0.0):.6f} "
                f"team_disc_reward={process_metrics.get('team_disc_reward_mean', 0.0):.6f} "
                f"team_disc_steps={process_metrics.get('team_disc_reward_applied_steps', 0.0):.0f} "
                f"team_disc_ratio={process_metrics.get('team_disc_reward_env_ratio', 0.0):.3f} "
                f"team_disc_guard={process_metrics.get('team_disc_reward_env_ratio_guard_active', 0.0):.0f} "
                f"team_disc_o05={process_metrics.get('team_disc_reward_env_ratio_over05_count', 0.0):.0f} "
                f"team_disc_kill={process_metrics.get('team_disc_reward_env_ratio_kill_triggered', 0.0):.0f} "
                f"combined_intr_ratio={process_metrics.get('combined_intrinsic_env_ratio', 0.0):.3f} "
                f"combined_intr_guard={process_metrics.get('combined_intrinsic_env_ratio_guard_active', 0.0):.0f} "
                f"combined_intr_o05={process_metrics.get('combined_intrinsic_env_ratio_over05_count', 0.0):.0f} "
                f"combined_intr_kill={process_metrics.get('combined_intrinsic_env_ratio_kill_triggered', 0.0):.0f} "
                f"proto_acc={process_metrics.get('proto_disc_acc', 0.0):.3f} "
                f"proto_prior_acc={process_metrics.get('proto_disc_prior_acc', 0.0):.3f} "
                f"proto_null={process_metrics.get('proto_disc_null_logp_mean', 0.0):.6f} "
                f"proto_ar_kl={process_metrics.get('proto_ar_parallel_kl', 0.0):.6f} "
                f"roster_kl_shuf={process_metrics.get('roster_ar_kl_shuffled', 0.0):.6f} "
                f"sel_def={process_metrics.get('selection_independence_deficit', 0.0):.6f} "
                f"proto_resid={process_metrics.get('proto_disc_residual_mean', 0.0):.6f} "
                f"proto_reward={process_metrics.get('proto_disc_reward_mean', 0.0):.6f} "
                f"proto_steps={process_metrics.get('proto_disc_reward_applied_steps', 0.0):.0f} "
                f"proto_ratio_guard={process_metrics.get('proto_disc_reward_env_ratio_guard_active', 0.0):.0f} "
                f"proto_ratio_o05={process_metrics.get('proto_disc_reward_env_ratio_over05_count', 0.0):.0f} "
                f"proto_ratio_kill={process_metrics.get('proto_disc_reward_env_ratio_kill_triggered', 0.0):.0f} "
                f"proto_skill_ent={process_metrics.get('proto_skill_selection_entropy', 0.0):.3f} "
                f"proto_kappa_ent={process_metrics.get('proto_skill_usage_entropy_by_kappa', 0.0):.3f} "
                f"proto_align={process_metrics.get('proto_skill_relevance_alignment', 0.0):.3f} "
                f"proto_rel_dwell={process_metrics.get('proto_rel_argmax_dwell_median', 0.0):.1f} "
                f"proto_rel_stab={process_metrics.get('proto_rel_stability_cos', 0.0):.3f} "
                f"high_intr_gate={process_metrics.get('intrinsic_segment_high_gate_active', 0.0):.0f} "
                f"high_intr_score={process_metrics.get('intrinsic_segment_high_gate_score', 0.0):.6f} "
                f"high_intr_reason={process_metrics.get('intrinsic_segment_high_gate_reason_code', 0.0):.0f} "
                f"posterior_gap_short={process_metrics.get('posterior_acc_minus_shortcut_max', 0.0):.3f} "
                f"posterior_gap_ctx={process_metrics.get('posterior_acc_minus_context_shortcut', 0.0):.3f} "
                f"posterior_acc={process_metrics.get('process_posterior_acc', 0.0):.3f} "
                f"ctx_short_acc={process_metrics.get('process_shortcut_context_acc', 0.0):.3f} "
                f"process_reward_mean={process_metrics['process_reward_mean']:.6f} "
                f"process_reward_raw={process_metrics.get('process_reward_unclipped_mean', 0.0):.6f} "
                f"process_mi_reward={process_metrics.get('process_reward_mi_component_mean', 0.0):.6f} "
                f"process_reward_high={process_metrics.get('process_reward_high_mean', 0.0):.6f} "
                f"process_reward_low={process_metrics.get('process_reward_low_mean', 0.0):.6f} "
                f"semantic_stop={process_metrics.get('semantic_shortcut_hard_stop_triggered', 0.0):.0f} "
                f"semantic_stop_apply={process_metrics.get('semantic_shortcut_hard_stop_applied', 0.0):.0f} "
                f"semantic_stop_score={process_metrics.get('semantic_shortcut_hard_stop_score', 0.0):.3f} "
                f"outcome_available={process_metrics['outcome_available_mean']:.3f} "
                f"outcome_abs_mean={process_metrics['outcome_abs_mean']:.6f} "
                f"out_full_loss={process_metrics.get('outcome_residual_full_loss', 0.0):.6f} "
                f"out_base_loss={process_metrics.get('outcome_residual_base_loss', 0.0):.6f} "
                f"out_gain={process_metrics.get('outcome_residual_gain_mean', 0.0):.6f} "
                f"out_pos={process_metrics.get('outcome_residual_gain_positive_frac', 0.0):.3f} "
                f"out_active={process_metrics.get('outcome_residual_reward_active', 0.0):.0f} "
                f"role_avail={process_metrics.get('topology_role_available_frac', 0.0):.3f} "
                f"role_acc={process_metrics.get('topology_role_acc', 0.0):.3f} "
                f"role_ctx_acc={process_metrics.get('topology_role_shortcut_acc', 0.0):.3f} "
                f"role_gain={process_metrics.get('topology_role_resid_gain_mean', 0.0):.6f} "
                f"role_pos={process_metrics.get('topology_role_resid_gain_positive_frac', 0.0):.3f} "
                f"role_z_mi={process_metrics.get('topology_role_z_mi', 0.0):.3f} "
                f"topo_pot_active={process_metrics.get('topology_potential_active', 0.0):.0f} "
                f"topo_pot_raw={process_metrics.get('topology_potential_raw_mean', 0.0):.6f} "
                f"topo_pot_rew={process_metrics.get('topology_potential_reward_mean', 0.0):.6f} "
                f"topo_pot_low={process_metrics.get('topology_potential_low_mean', 0.0):.6f} "
                f"topo_phi_start={process_metrics.get('topology_potential_phi_start_mean', 0.0):.6f} "
                f"topo_phi_end={process_metrics.get('topology_potential_phi_end_mean', 0.0):.6f} "
                f"effect_windows={process_metrics.get('effect_windows', 0.0):.0f} "
                f"effect_loss_full={process_metrics.get('effect_loss_full', 0.0):.6f} "
                f"effect_loss_base={process_metrics.get('effect_loss_base', 0.0):.6f} "
                f"effect_gain={process_metrics.get('effect_gain_mean', 0.0):.6f} "
                f"effect_gbal={process_metrics.get('effect_gain_group_balanced_mean', 0.0):.6f} "
                f"effect_nonmotion={process_metrics.get('effect_gain_nonmotion', 0.0):.6f} "
                f"effect_pos={process_metrics.get('effect_gain_positive_frac', 0.0):.3f} "
                f"effect_motion={process_metrics.get('effect_gain_motion', 0.0):.6f} "
                f"effect_service={process_metrics.get('effect_gain_service', 0.0):.6f} "
                f"effect_energy={process_metrics.get('effect_gain_energy', 0.0):.6f} "
                f"effect_topology={process_metrics.get('effect_gain_topology', 0.0):.6f} "
                f"effect_h0={process_metrics.get('effect_gain_horizon_0', 0.0):.6f} "
                f"effect_h1={process_metrics.get('effect_gain_horizon_1', 0.0):.6f} "
                f"effect_h2={process_metrics.get('effect_gain_horizon_2', 0.0):.6f} "
                f"effect_act_eta={process_metrics.get('effect_action_skill_eta2', 0.0):.3f} "
                f"effect_tgt_eta={process_metrics.get('effect_target_skill_eta2', 0.0):.3f} "
                f"effect_obs_tgt_l2={process_metrics.get('effect_observed_target_skill_l2_mean', 0.0):.6f} "
                f"effect_obs_nm_l2={process_metrics.get('effect_observed_target_skill_l2_nonmotion', 0.0):.6f} "
                f"effect_act_tgt_corr={process_metrics.get('effect_observed_action_target_corr', 0.0):.3f} "
                f"effect_end_avail={process_metrics.get('effect_endstate_available_frac', 0.0):.3f} "
                f"effect_mean_avail={process_metrics.get('effect_window_mean_available_frac', 0.0):.3f} "
                f"effect_skill_ent={process_metrics.get('effect_skill_usage_entropy', 0.0):.3f} "
                f"effect_gap_dur={process_metrics.get('effect_gain_minus_duration_baseline', 0.0):.6f} "
                f"effect_gap_rew={process_metrics.get('effect_gain_minus_reward_baseline', 0.0):.6f} "
                f"effect_low_rew={process_metrics.get('effect_reward_low_mean', 0.0):.6f} "
                f"effect_steps={process_metrics.get('effect_reward_applied_steps', 0.0):.0f} "
                f"force_rew={process_metrics.get('force_reward_low_mean', 0.0):.6f} "
                f"force_steps={process_metrics.get('force_reward_applied_steps', 0.0):.0f} "
                f"force_disc_acc={process_metrics.get('force_disc_acc', 0.0):.3f} "
                f"force_resid={process_metrics.get('force_disc_residual_mean', 0.0):.6f} "
                f"force_eff_resid={process_metrics.get('force_effect_residual_mean', 0.0):.6f} "
                f"force_shortcut_acc={process_metrics.get('force_shortcut_best_acc', 0.0):.3f} "
                f"force_margin={process_metrics.get('force_shortcut_margin', 0.0):.3f} "
                f"force_gate={process_metrics.get('force_gate_active', 0.0):.0f} "
                f"force_reason={process_metrics.get('force_gate_reason', 0.0):.0f} "
                f"effect_itv_samples={process_metrics.get('effect_intervention_samples', 0.0):.0f} "
                f"effect_itv_act_l2={process_metrics.get('effect_intervention_action_l2_mean', 0.0):.6f} "
                f"effect_itv_pred_l2={process_metrics.get('effect_intervention_pred_effect_l2_mean', 0.0):.6f} "
                f"duration_only_acc={process_metrics.get('duration_only_accuracy', 0.0):.3f} "
                f"length_only_acc={process_metrics.get('length_only_accuracy', 0.0):.3f} "
                f"reward_sum_only_acc={process_metrics.get('reward_sum_only_accuracy', 0.0):.3f} "
                f"posterior_gap_dur={process_metrics.get('posterior_acc_minus_duration_only', 0.0):.3f} "
                f"posterior_gap_len={process_metrics.get('posterior_acc_minus_length_only', 0.0):.3f} "
                f"posterior_gap_rew={process_metrics.get('posterior_acc_minus_reward_sum_only', 0.0):.3f} "
                f"switch_rate={process_metrics.get('skill_switch_rate', 0.0):.3f} "
                f"seg_len_mean={process_metrics.get('segment_length_mean', 0.0):.2f} "
                f"high_loss={process_metrics['high_loss']:.6f} "
                f"high_value_loss={process_metrics.get('high_value_loss', 0.0):.6f} "
                f"high_entropy={process_metrics['high_entropy']:.6f} "
                f"high_return_mean={process_metrics['high_return_mean']:.6f} "
                f"high_env_return={process_metrics.get('high_env_return_mean', 0.0):.6f} "
                f"high_bootstrap={process_metrics.get('high_bootstrap_value_mean', 0.0):.6f} "
                f"high_bootstrap_contrib={process_metrics.get('high_bootstrap_contribution_mean', 0.0):.6f} "
                f"high_vnorm_mean={process_metrics.get('high_value_norm_mean', 0.0):.6f} "
                f"high_vnorm_std={process_metrics.get('high_value_norm_std', 0.0):.6f} "
                f"high_grad_norm={process_metrics.get('high_grad_norm', 0.0):.6f} "
                f"skill_entropy={process_metrics.get('skill_usage_entropy', 0.0):.3f} "
                f"duration_entropy={process_metrics.get('duration_usage_entropy', 0.0):.3f} "
                f"duration_policy_entropy={process_metrics.get('duration_policy_entropy_norm', 0.0):.3f} "
                f"dur_ent_floor={process_metrics.get('duration_entropy_floor_active', 0.0):.0f} "
                f"dur_ent_gap={process_metrics.get('duration_entropy_floor_gap', 0.0):.3f} "
                f"dur_ent_loss={process_metrics.get('duration_entropy_floor_loss', 0.0):.6f} "
                f"z_ent={process_metrics.get('z_usage_entropy', 0.0):.3f} "
                f"z_ent_floor={process_metrics.get('z_entropy_floor_active', 0.0):.0f} "
                f"z_ent_gap={process_metrics.get('z_entropy_floor_gap', 0.0):.3f} "
                f"z_pol_ent={process_metrics.get('z_policy_entropy_norm', 0.0):.3f} "
                f"z_decisions={process_metrics.get('z_decisions_per_update', 0.0):.0f} "
                f"z_adv_mean={process_metrics.get('z_advantage_mean', 0.0):.6f} "
                f"z_adv_std={process_metrics.get('z_advantage_std', 0.0):.6f} "
                f"z_trunc={process_metrics.get('z_boundary_trunc_rate', 0.0):.3f} "
                f"z_trunc_d3={process_metrics.get('z_boundary_trunc_rate_dur3', 0.0):.3f} "
                f"z_trunc_d7={process_metrics.get('z_boundary_trunc_rate_dur7', 0.0):.3f} "
                f"z_trunc_d13={process_metrics.get('z_boundary_trunc_rate_dur13', 0.0):.3f} "
                f"z_trunc_d24={process_metrics.get('z_boundary_trunc_rate_dur24', 0.0):.3f} "
                f"g_entropy={process_metrics.get('team_code_usage_entropy', 0.0):.3f} "
                f"g_skill_mi={process_metrics.get('team_code_skill_mi', 0.0):.3f} "
                f"g_dur_mi={process_metrics.get('team_code_duration_mi', 0.0):.3f} "
                f"g_edit_mi={process_metrics.get('team_code_edit_mi', 0.0):.3f} "
                f"g_ikl={process_metrics.get('g_intervention_kl_mean', 0.0):.6f} "
                f"g_itv={process_metrics.get('g_intervention_tv_mean', 0.0):.6f} "
                f"g_info_active={process_metrics.get('g_info_active', 0.0):.0f} "
                f"g_info_obj={process_metrics.get('g_info_objective_active', 0.0):.0f} "
                f"g_info_loss={process_metrics.get('g_info_loss', 0.0):.6f} "
                f"g_mi_z={process_metrics.get('g_info_skill_mi', 0.0):.6f} "
                f"g_mi_dur={process_metrics.get('g_info_duration_mi', 0.0):.6f} "
                f"g_itv_z={process_metrics.get('g_itv_tv_skill', 0.0):.6f} "
                f"g_itv_dur={process_metrics.get('g_itv_tv_duration', 0.0):.6f} "
                f"g_joint_dist={process_metrics.get('g_joint_assignment_distance', 0.0):.6f} "
                f"situation_enabled={process_metrics.get('situation_enabled', 0.0):.0f} "
                f"situation_change={process_metrics.get('situation_change_rate', 0.0):.3f} "
                f"situation_kappa={process_metrics.get('situation_unique_kappa', 0.0):.0f} "
                f"situation_seg_change={process_metrics.get('situation_segment_change_frac', 0.0):.3f} "
                f"situation_hazard_enabled={process_metrics.get('situation_hazard_control_enabled', 0.0):.0f} "
                f"situation_hazard_force={process_metrics.get('situation_hazard_forced_renewal_rate', 0.0):.3f} "
                f"situation_hazard_mode={process_metrics.get('situation_hazard_mode_code', 0.0):.0f} "
                f"situation_guard={process_metrics.get('situation_hazard_conservative_guard', 0.0):.0f} "
                f"situation_guard_events={process_metrics.get('situation_hazard_guard_event_count', 0.0):.0f} "
                f"situation_guard_allow={process_metrics.get('situation_hazard_guard_allow_rate', 0.0):.3f} "
                f"situation_guard_confirm={process_metrics.get('situation_hazard_guard_confirm_block_rate', 0.0):.3f} "
                f"situation_guard_dwell={process_metrics.get('situation_hazard_guard_dwell_block_rate', 0.0):.3f} "
                f"situation_guard_ratecap={process_metrics.get('situation_hazard_guard_rate_cap_block_rate', 0.0):.3f} "
                f"situation_guard_recent_force={process_metrics.get('situation_hazard_guard_recent_force_rate', 0.0):.3f} "
                f"credit_disc={process_metrics.get('credit_full_disconnect_mean', 0.0):.3f} "
                f"credit_recover={process_metrics.get('credit_recovery_rate', 0.0):.3f} "
                f"credit_collapse={process_metrics.get('credit_collapse_rate', 0.0):.3f} "
                f"credit_bh_frac={process_metrics.get('credit_backhaul_connected_step_fraction', 0.0):.3f} "
                f"credit_bh_thr={process_metrics.get('credit_throughput_when_backhaul_connected_mbps', 0.0):.6f} "
                f"credit_d_conn={process_metrics.get('credit_delta_connectivity_ratio_mean', 0.0):.6f} "
                f"credit_d_served={process_metrics.get('credit_delta_backhaul_served_users_mean', 0.0):.6f} "
                f"credit_d_outage={process_metrics.get('credit_delta_backhaul_outage_ratio_mean', 0.0):.6f} "
                f"p2_seg={process_metrics.get('p2_segments', 0.0):.0f} "
                f"p2_avail={process_metrics.get('p2_available_frac', 0.0):.3f} "
                f"p2_window={process_metrics.get('p2_window_frac', 0.0):.3f} "
                f"p2_dphi_full={process_metrics.get('delta_phi_soft_nonzero_rate_when_full_disconnect', 0.0):.3f} "
                f"p2_dphi_near={process_metrics.get('delta_phi_soft_nonzero_rate_when_near_disconnect', 0.0):.3f} "
                f"p2_corr_rec={process_metrics.get('p2_corr_phi_recovery_event', 0.0):.3f} "
                f"p2_partial={process_metrics.get('p2_partial_recovery_frac', 0.0):.3f} "
                f"p2_corr_dbh={process_metrics.get('p2_corr_credit_delta_bh_frac', 0.0):.3f} "
                f"p2_dbh={process_metrics.get('p2_delta_bh_frac_mean', 0.0):.6f} "
                f"p2_fteam={process_metrics.get('p2_f_team_mean', 0.0):.6f} "
                f"low_loss={low_metrics['low_loss']:.6f} "
                f"low_value_loss={low_metrics.get('low_value_loss', 0.0):.6f} "
                f"low_actor_loss={low_metrics.get('low_actor_loss', 0.0):.6f} "
                f"low_critic_loss={low_metrics.get('low_critic_loss', 0.0):.6f} "
                f"low_chunks={low_metrics.get('low_sequence_chunks', 0.0):.0f} "
                f"low_vnorm_mean={low_metrics.get('low_value_norm_mean', 0.0):.6f} "
                f"low_vnorm_std={low_metrics.get('low_value_norm_std', 0.0):.6f} "
                f"low_verr={low_metrics.get('low_value_error_abs_mean', 0.0):.6f} "
                f"low_vrmse={low_metrics.get('low_value_error_rmse', 0.0):.6f} "
                f"low_adv_std={low_metrics.get('low_advantage_std', 0.0):.6f} "
                f"low_ratio={low_metrics.get('low_ratio_mean', 0.0):.6f} "
                f"low_clip={low_metrics.get('low_clip_frac', 0.0):.6f} "
                f"low_kl={low_metrics.get('low_approx_kl', 0.0):.6f} "
                f"low_agn={low_metrics.get('low_actor_grad_norm', 0.0):.6f} "
                f"low_cgn={low_metrics.get('low_critic_grad_norm', 0.0):.6f} "
                f"low_ahn={low_metrics.get('low_actor_h_norm_mean', 0.0):.6f} "
                f"low_chn={low_metrics.get('low_critic_h_norm_mean', 0.0):.6f} "
                f"low_sent={low_metrics.get('low_skill_usage_entropy', 0.0):.3f} "
                f"low_sret_std={low_metrics.get('low_skill_return_std', 0.0):.6f} "
                f"low_sret_rng={low_metrics.get('low_skill_return_range', 0.0):.6f} "
                f"low_sverr_std={low_metrics.get('low_skill_value_error_abs_std', 0.0):.6f} "
                f"low_sent_std={low_metrics.get('low_skill_entropy_std', 0.0):.6f} "
                f"low_tent={low_metrics.get('low_team_usage_entropy', 0.0):.3f} "
                f"low_tret_std={low_metrics.get('low_team_return_std', 0.0):.6f} "
                f"low_tret_rng={low_metrics.get('low_team_return_range', 0.0):.6f} "
                f"low_tverr_std={low_metrics.get('low_team_value_error_abs_std', 0.0):.6f} "
                f"return_mean={low_metrics['return_mean']:.6f}"
            )
            log_train_metrics(writer, total_steps, episode_rewards, process_metrics, low_metrics)
            export_update_metrics(args, update_idx, total_steps, env_reward_mean, process_metrics, low_metrics)
            if profiler is not None:
                profiler.stop()
            if proto_ratio_kill_message:
                if reward_ratio_guard_mode == "warn":
                    emit(args, f"standalone_runtime_guard_warn mode=warn {proto_ratio_kill_message}")
                else:
                    emit(args, f"standalone_runtime_guard mode=kill {proto_ratio_kill_message}")
                    raise RuntimeError(proto_ratio_kill_message)
            if team_disc_ratio_kill_message:
                if reward_ratio_guard_mode == "warn":
                    emit(args, f"standalone_runtime_guard_warn mode=warn {team_disc_ratio_kill_message}")
                else:
                    emit(args, f"standalone_runtime_guard mode=kill {team_disc_ratio_kill_message}")
                    raise RuntimeError(team_disc_ratio_kill_message)
            if combined_intrinsic_kill_message:
                if reward_ratio_guard_mode == "warn":
                    emit(args, f"standalone_runtime_guard_warn mode=warn {combined_intrinsic_kill_message}")
                else:
                    emit(args, f"standalone_runtime_guard mode=kill {combined_intrinsic_kill_message}")
                    raise RuntimeError(combined_intrinsic_kill_message)
            if not bool(getattr(agent, "r30_enabled", False)):
                agent.reset_all_policy_state()

            if profiler is not None:
                profiler.start("checkpoint_eval")
            if int(args.save_interval) > 0 and update_idx % int(args.save_interval) == 0:
                save_checkpoint(
                    Path(args.log_dir) / f"standalone_process_core_update_{update_idx}.pt",
                    agent,
                    args,
                    config,
                    total_steps,
                    update_idx,
                )
                prune_periodic_checkpoints(args.log_dir, int(args.checkpoint_keep_last))

            if int(args.eval_interval) > 0 and total_steps - last_eval_step >= int(args.eval_interval):
                eval_metrics = evaluate(
                    agent,
                    config,
                    args,
                    episodes=int(args.eval_episodes),
                    total_steps=total_steps,
                )
                log_eval_metrics(writer, total_steps, eval_metrics)
                last_eval_step = int(total_steps)
            if profiler is not None:
                profiler.stop()
                profiler.finish_update(update=update_idx, total_steps=total_steps)

        save_checkpoint(
            Path(args.log_dir) / "standalone_process_core_final.pt",
            agent,
            args,
            config,
            total_steps,
            update_idx,
        )
        standalone_manifest.export_run_manifest(
            args,
            config,
            env=env,
            agent=agent,
            total_steps=total_steps,
            update_idx=update_idx,
            mode="train",
        )
        return agent, total_steps, update_idx
    finally:
        collector.close()
