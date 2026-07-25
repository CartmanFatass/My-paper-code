"""D7.2B toy positive control — learned-keep carrier with a supplied executor.

`docs/research/designs/D7_2B_TOY_POSITIVE_CONTROL_REALIZATION.md`.

This is **not** `config_r39_native_hmasd_toy.py`. That one drives the
`hmasd_original` lane through `r39_native_toy_*` flags under native-categorical
edit, which is the branch where KEEP is a post-hoc collision label rather than a
decision. D7.2B needs the opposite: the standalone R30 lane with the learned-keep
branch live, so `sigmoid(keep_logit)` is a real renewal decision, plus the supplied
primitive executor the D7 ruling permits so the competence floor sits above the
carrier under test.
"""

from __future__ import annotations

from ha_ctse_process.config import Config as StandaloneConfig


class Config(StandaloneConfig):
    """Learned-keep R30 on the two-timescale toy, fixed primitives, CPU."""

    scenario = "two_timescale_role_free_actions"
    scenario_label = "d7_2b_toy_learned_keep"

    # Source geometry, matching envs/pettingzoo/two_timescale_role_free_actions.py.
    n_agents = 2
    n_uavs = 2
    max_observed_uavs = 2
    obs_dim = 4
    state_dim = 6
    action_dim = 2
    action_bound = 1.0
    action_space_type = "continuous"
    episode_length = 40
    max_steps = 40

    # The two clocks the source itself sets. `skill_interval` must equal
    # `r39_toy_k0`, so every check falls on a fast flip and every sixth check
    # coincides with a slow flip. D7 fixes Delta as one check interval and the
    # primary H as one slow period.
    k = 5
    skill_interval = 5
    r39_toy_k0 = 5
    r39_toy_slow_period_blocks = 6

    # Four skills, one per table row: 0/1 are the x-axis (slow duty), 2/3 the
    # y-axis (fast duty).
    n_Z = 4
    n_z = 4

    # The carrier: R30 with the learned-keep branch live.
    high_controller = "r30_fixed_clock_ar_edit"
    r39_native_categorical_edit = False
    r30_force_refresh_every_check = False
    r30_keep_init = 0.6
    # Direct-state high context. This is the run's *information contract*, not a
    # tuning knob: the toy's local observations are identically zero and the
    # initial target signs are redrawn every episode, so a high actor without the
    # centralized state cannot tell which target is which. Both match rates then
    # cap near 0.5 and D7's competence floor of 0.75 is unreachable for an
    # architectural reason rather than a carrier one -- measured, see the
    # no-state-access control in CURRENT_WORK.md. Role labels are still never
    # fed to any policy; the centralized state carries the two targets, which the
    # environment docstring names as the route by which task context selects
    # skills, and never says which agent should serve which.
    r39_toy_direct_state_context = True
    r30_bridge_context_mode = "direct_state_zero_team"
    team_bridge_type = "none"
    r30_high_buffer_version = 2
    # Optimizer budget, not a credit choice. The first screen ran one epoch at
    # lr_coordinator = 1e-4 for 200 updates -- 200 optimizer steps -- and the high
    # actor did not move: at update 150 keep_prob was 0.599 against its 0.6 init
    # and the skill distribution sat at entropy 1.096 against a ln(3) = 1.0986
    # maximum, uniform to three decimals across every target-sign combination.
    # Three passes over each batch and a ten-times learning rate give 3,000 steps
    # for the same wall-clock shape. block_return stays out of reach: it requires
    # force_refresh_every_check, where KEEP is not a decision.
    r30_high_ppo_epochs = 3
    lr_coordinator = 1e-3
    r30_high_actor_advantage_mode = "smdp_gae"
    r30_high_gae_lambda = 0.95
    high_keep_entropy_coef = 0.0

    # The supplied executor. Zero parameters, no optimizer -- the competence
    # prerequisite is met by construction so a null can only be about the carrier.
    r39_toy_fixed_skill_primitives = True
    r39_toy_fixed_skill_action_schema = "axis4_xy_v1"

    # A constant skill->action table is stateless, so there is no recurrent
    # low-level policy to thread hidden state through. This is not a tuning
    # choice: `act_low_batch` calls the recurrent low actor with the strict
    # HMASD signature (obs, skills, actor_hxs, state, team_code, critic_hxs,
    # agent_ids), and `FixedSkillPrimitivePolicy.act(obs, skills, deterministic)`
    # raises against it. The feedforward path is the one whose call shape the
    # table actually satisfies, and it leaves the stored hidden states untouched.
    use_recurrent_low_level = False
    low_level_architecture = "feedforward"

    # Small networks; the decision problem is tiny and the run is a screen.
    hidden_size = 32
    embedding_dim = 32
    gru_hidden_size = 32
    opt_compact_dim = 16
    opt_num_prototypes = 4
    process_encoder_embedding_dim = 8
    skill_lifetime_candidates = (1, 2)

    # External reward only. R30 is reward-pure outside the Alice--Bob semantic
    # lane, and D7 reads external task return alone.
    process_reward_injection = "none"
    outcome_residual_injection = "none"
    topology_role_injection = "none"
    topology_potential_injection = "none"
    skill_effect_reward_injection = "none"
    skill_force_reward_injection = "none"
    use_process_reward_for_discoverer = False
    disable_discriminator_training = True
    disable_discriminator_rewards = True
    lambda_D = 0.0
    lambda_d = 0.0
    enable_prototype_disc_reward = False
    enable_team_transition_reward = False
    enable_team_disc_reward = False
    enable_assignment_actionability_reward = False
    skill_effect_reward_on = False
    enable_skill_forcing_reward = False
    p2_recovery_credit_reward_on = False
    use_topology_potential_shaping = False
    alice_bob_semantic_reward_enabled = False
    transition_skill_reward_coef = 0.0

    # Guards the R30 construction check reads directly.
    edit_penalty_alpha = 0.0
    switch_penalty_beta = 0.0
    duration_entropy_floor_enabled = False
    z_entropy_floor_enabled = False
    enable_team_intent = False
    use_compact_return_head = False
    z_assignment_residual_gain = 0.0
    low_actor_condition_on_team_code = False
    parallel_selection = False
    use_autoregressive_selection = True
    ar_prefix_mode = "roster"
    r29_action_info_mode = "off"
    r31_effect_mode = "off"

    # The competence attempt, not a screen. The contract's routing rule is that a
    # flat condition A at screen scale buys a larger budget rather than a
    # conclusion, because neither a screen nor the 20-update prior art can license
    # one. 640k steps at 640 steps per update is 1,000 updates.
    num_envs = 16
    rollout_length = 40
    total_timesteps = 640_000
    eval_episodes = 64
