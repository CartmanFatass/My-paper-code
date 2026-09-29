"""Cell-1 recipes (arms H and SET) for coupled_host_joint_skills_stage1 b01; no CLI tuning grid.

Adapted from ``agent_count_generalization/configuration.py`` (ACG H6 / SET recipes).  The only
declared recipe difference from ACG is arm H's ``policy_interruption_mode = "d2"`` with fixed
caps ``skill_cap_k_max = team_cap_k_Z = 10``, both interruption costs infinite and the age
feature off (b01 declaration, amended by the DM disposition of the Pro review, item 3).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from configs.config_1 import Config
from hmasd.baselines import apply_algorithm_config

from .adapter import DEV_WORLDS, HOLDOUT_WORLDS, OBS_DIM, STATE_DIM

DIRECTION = "coupled_host_joint_skills_stage1"
SEEDS = {"H": (931201, 931307, 931413), "SET": (932201, 932307, 932413)}
#: Pairing by position: 931201 <-> 932201, 931307 <-> 932307, 931413 <-> 932413.
PAIRS = tuple(zip(SEEDS["H"], SEEDS["SET"]))
ALGORITHM = {"H": "hmasd", "SET": "mappo"}
K = 10


@dataclass(frozen=True)
class FitSpec:
    horizon: int = 500
    train_lanes: int = 16
    eval_lanes: int = 16
    rollouts: int = 45
    panels: tuple = (0, 15, 30, 45)
    hidden_size: int = 256
    n_heads: int = 8
    n_layers: int = 2
    ppo_epochs: int = 15
    sequence_batch_size: int = 32
    coordinator_batch_size: int = 1280
    torch_threads: int = 4
    area_size: int = 5000
    dev_worlds: tuple = DEV_WORLDS
    holdout_worlds: tuple = HOLDOUT_WORLDS
    #: Worlds of the probe's one timed panel-sized run (timing only; no score is written).
    #: DM choice: non-panel worlds, so the probe never touches the declared panels.
    probe_panel_worlds: tuple = tuple(range(9000, 9032))
    probe_rollouts: int = 3


DEFAULT_SPEC = FitSpec()


def is_declared_fit_spec(spec: FitSpec) -> bool:
    """True for the declared cell-1 fit spec (area 5000 or the pre-declared 6000 fallback)."""
    return asdict(spec) in (asdict(DEFAULT_SPEC), asdict(FitSpec(area_size=6000)))


def make_config(arm, envs, seed, spec=DEFAULT_SPEC):
    if arm not in SEEDS:
        raise ValueError(f"unknown arm {arm}")
    config = Config()
    config.n_uavs = envs[0].n_uavs
    config.n_users = 50
    config.num_envs = len(envs)
    config.rollout_length = config.episode_length = spec.horizon
    config.k = K
    config.seed = int(seed)
    config.hidden_size = config.embedding_dim = config.gru_hidden_size = spec.hidden_size
    config.n_heads = spec.n_heads
    config.n_encoder_layers = config.n_decoder_layers = spec.n_layers
    if arm == "H":
        config.policy_interruption_mode = "d2"
        config.interruption_delta = 1
        config.interruption_cost_c = float("inf")
        config.interruption_cost_c_Z = float("inf")
        config.skill_cap_k_max = K
        config.team_cap_k_Z = K
        config.age_feature = "off"
    else:
        config.policy_interruption_mode = "off"
    config.use_obsnorm = config.use_statenorm = False
    config.use_lr_decay = False
    config.n_Z = config.n_z = 6
    config.ppo_epochs = spec.ppo_epochs
    config.sequence_batch_size = spec.sequence_batch_size
    config.coordinator_batch_size = spec.coordinator_batch_size
    config.total_timesteps = spec.train_lanes * spec.horizon * spec.rollouts
    config.update_env_dims(state_dim=envs[0].state_dim, obs_dim=envs[0].obs_dim,
                           n_agents=envs[0].n_uavs)
    config = apply_algorithm_config(config, ALGORITHM[arm])
    # MAPPO's algorithm switch also changes the recurrent chunk length. Restore
    # the declared ten-step information clock and truncated-BPTT length.
    config.k = K
    config.use_central_snapshot_in_flat_actor = arm == "SET"
    config.contract_arm = arm
    config.calculate_and_set_buffer_sizes()
    config.discriminator_batch_size = config.batch_size
    config.validate_config()
    if config.state_dim != STATE_DIM or config.obs_dim != OBS_DIM:
        raise ValueError("unexpected contract adapter observation/state widths")
    if arm == "H" and config.policy_interruption_mode != "d2":
        raise ValueError("arm H lost the d2 route")
    if arm == "SET" and config.policy_interruption_mode != "off":
        raise ValueError("arm SET left the off route")
    return config


def config_dict(config):
    fields = """contract_arm algorithm n_agents n_uavs n_users num_envs rollout_length
    episode_length k n_Z n_z state_dim obs_dim action_dim action_space_type
    gamma gae_lambda ppo_epochs num_mini_batch sequence_batch_size coordinator_batch_size
    high_level_batch_size high_level_buffer_size batch_size discriminator_batch_size
    lambda_e lambda_D lambda_d lambda_h lambda_l lambda_cd lambda_mi
    lr_coordinator lr_discoverer_actor lr_discoverer_critic lr_discriminator
    weight_decay clip_epsilon value_loss_coef max_grad_norm hidden_size embedding_dim
    n_heads n_encoder_layers n_decoder_layers gru_hidden_size use_valuenorm use_obsnorm
    use_statenorm use_lr_decay use_entropy_annealing total_timesteps seed
    policy_interruption_mode interruption_delta interruption_cost_c interruption_cost_c_Z
    skill_cap_k_max team_cap_k_Z age_feature
    use_central_snapshot_in_flat_actor disable_high_level_training
    disable_discriminator_training disable_discriminator_rewards collects_high_level_samples
    use_process_exploration use_horizon_window use_opt_compact""".split()
    result = {}
    for name in fields:
        value = getattr(config, name, None)
        if isinstance(value, float) and value != value:  # NaN never expected; keep JSON strict
            value = "nan"
        elif isinstance(value, float) and value in (float("inf"), float("-inf")):
            value = "inf" if value > 0 else "-inf"
        result[name] = value
    return result


OBSERVATION_LAYOUT = {
    "width": OBS_DIM,
    "own_position": "[0:3] x/area, y/area, (z - 50)/100",
    "users": "[3:63] 20 slots x (dx/area, dy/area, clip((SINR + 10)/50, 0, 1)); users with SINR >= 3 dB, "
             "SINR-descending",
    "uavs": "[63:87] 6 slots x (dx/area, dy/area, dz/100, clip((SINR + 10)/50, 0, 1)); from uav_sinr_matrix "
            "(not uav_connections), SINR-descending",
    "time": "[87] current_step / 500",
    "bs_connection": "[88] UAV-BS link bit (SINR >= 3 dB)",
    "legacy_hop": "[89] min(len(path)/3, 1) if routed else 1.0 (cannot tell 'unrouted' from 'one relay')",
    "source": "uav_env.py 382-433 + scenario2.py 220-259",
}
STATE_LAYOUT = {
    "width": STATE_DIM,
    "uav_slots": "[0:24) 8 slots x (x/area, y/area, (z - 50)/100); slots 6-7 zero",
    "validity": "[24:32) six ones, two zeros",
    "users": "[32:132) 50 x (x/area, y/area)",
    "time": "[132] current_step / 500",
    "information": "the native 119-dim state (UAV xyz, user xy, step fraction) rescaled; no BS/link/routing field",
}


def _parameter_counts(agent):
    counts = {}
    for name in ("skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator"):
        module = getattr(agent, name, None)
        if module is None:
            continue
        counts[name] = int(sum(p.numel() for p in module.parameters()))
        for child_name, child in module.named_modules():
            if child_name and type(child).__name__ in {"StateSetEncoder", "SetActorBase"}:
                counts[f"{name}.{child_name}"] = int(sum(p.numel() for p in child.parameters()))
    counts["discoverer_actor"] = int(sum(p.numel() for p in agent.skill_discoverer.actor.parameters()))
    counts["discoverer_critic"] = int(sum(p.numel() for p in agent.skill_discoverer.critic.parameters()))
    return counts


def matching_table(config_H, config_SET, agents, spec=DEFAULT_SPEC):
    """Pro's matching list for the H/SET package comparison (DM disposition item 3).

    ``agents`` maps ``"H"``/``"SET"`` to built agents (``models.build_agent``); only parameter
    counts and route attributes are read.
    """
    from .models import route_facts  # local import keeps torch out of module import paths

    configs = {"H": config_H, "SET": config_SET}
    for arm, config in configs.items():
        if getattr(config, "contract_arm", None) != arm:
            raise ValueError(f"matching_table needs the {arm} config in position {arm}")
    per_arm = {arm: config_dict(config) for arm, config in configs.items()}
    fields = sorted(per_arm["H"])
    differing = {name: {"H": per_arm["H"][name], "SET": per_arm["SET"][name]}
                 for name in fields if per_arm["H"][name] != per_arm["SET"][name]}
    exposure = spec.train_lanes * spec.horizon * spec.rollouts
    table = {
        "schema": 1,
        "direction": DIRECTION,
        "pairs_by_position": [list(pair) for pair in PAIRS],
        "lanes": spec.train_lanes,
        "horizon": spec.horizon,
        "rollouts": spec.rollouts,
        "exposure_team_steps_per_fit": exposure,
        "evaluation": {
            "panels_after_rollouts": list(spec.panels),
            "dev_worlds": [min(spec.dev_worlds), max(spec.dev_worlds)],
            "holdout_worlds": [min(spec.holdout_worlds), max(spec.holdout_worlds)],
            "modes": "dev deterministic at every panel; hold-out deterministic and sampled at the final rollout",
            "frozen_rule": "target built through the direction factory, strict_sync from the learner, "
                           "train(False), zero optimizer calls, parameter/normaliser digest unchanged",
            "eval_lanes": spec.eval_lanes,
        },
        "observation_encoding": OBSERVATION_LAYOUT,
        "state_encoding": STATE_LAYOUT,
        "state_consumers": {
            "H": "coordinator state embedding, discoverer critic base and team discriminator via StateSetEncoder",
            "SET": "coordinator (inactive) and discoverer critic base via StateSetEncoder; actor via "
                   "SetActorBase (current obs, state, held team-observation snapshot, one-hot ego)",
        },
        "snapshot_timing": {
            "H": "coordinator decides on the d2 clock: reset at episode start, then team_cap every 10 steps "
                 "(both costs infinite, so no gap/cap interruption); every decision re-samples all six agents",
            "SET": "held central snapshot refreshed at the 'off' route's ten-step skill timer "
                   "(use_central_snapshot_in_flat_actor, hmasd/agent.py 507-516)",
        },
        "reward_units": {
            "environment": "contract team reward r = 0.5 * (C_bh + S/D) per step; the adapter scalar is r / 6",
            "training_signal": "scalar r/6 per lane enters store_transition_batch for both arms",
            "H_auxiliary_weights": {name: per_arm["H"][name] for name in
                                    ("lambda_e", "lambda_D", "lambda_d", "lambda_h", "lambda_l",
                                     "lambda_cd", "lambda_mi")},
            "SET_auxiliary_weights": {name: per_arm["SET"][name] for name in
                                      ("lambda_e", "lambda_D", "lambda_d", "lambda_h", "lambda_l",
                                       "lambda_cd", "lambda_mi")},
            "readings": "team per-step r; J = 6 * scalar",
        },
        "gamma_gae": {arm: {"gamma": per_arm[arm]["gamma"], "gae_lambda": per_arm[arm]["gae_lambda"]}
                      for arm in configs},
        "normalisation": {arm: {name: per_arm[arm][name] for name in
                                ("use_valuenorm", "use_obsnorm", "use_statenorm")} for arm in configs},
        "learning_rates": {arm: {name: per_arm[arm][name] for name in
                                 ("lr_coordinator", "lr_discoverer_actor", "lr_discoverer_critic",
                                  "lr_discriminator", "weight_decay", "use_lr_decay",
                                  "use_entropy_annealing")} for arm in configs},
        "ppo": {arm: {name: per_arm[arm][name] for name in
                      ("clip_epsilon", "max_grad_norm", "value_loss_coef", "ppo_epochs",
                       "num_mini_batch")} for arm in configs},
        "batch_units": {arm: {name: per_arm[arm][name] for name in
                              ("sequence_batch_size", "coordinator_batch_size", "batch_size",
                               "high_level_batch_size", "high_level_buffer_size",
                               "discriminator_batch_size")} for arm in configs},
        "optimizer_calls": "counted per module by step post-hooks in every fit (summary.json optimizer_calls "
                           "and training.jsonl optimizer_delta)",
        "parameter_counts": {arm: _parameter_counts(agent) for arm, agent in agents.items()},
        "routes": {arm: route_facts(agent) for arm, agent in agents.items()},
        "information_entry_points": {
            "H": "per-agent obs (90) to the discoverer actor; 133-dim state to coordinator/critic/discriminator; "
                 "team and agent labels to the actor",
            "SET": "per-agent obs (90) + 133-dim state + held six-row observation snapshot + ego one-hot to the "
                   "actor; 133-dim state to the critic; labels constant (n_Z = n_z = 1)",
        },
        "reset_bootstrap_rule": "episodes end at step 500 with terminated True / truncated False; the runner "
                                "passes last_values = 0 and dones = True to agent.update for both arms (ACG rule); "
                                "every reset passes an explicit world seed",
        "training_worlds": "300000 + (seed % 1000) * 100 + lane + episode * 10000; paired seeds share it",
        "dtype_threads": {"dtype": "float32", "device": "cpu", "torch_threads": spec.torch_threads,
                          "blas_threads": 1},
        "rng_roles": {
            "fit_seed": "random/numpy/torch global seeds at fit start (network init, action and label sampling)",
            "training_worlds": "explicit reset seeds by the rule above (no draw from the global streams)",
            "panels": "global streams saved, reseeded to first_world + 51 per panel run, restored afterwards",
        },
        "final_rule": "the rollout-45 checkpoint is the endpoint; no checkpoint selection; sampled mode never "
                      "replaces the deterministic endpoint",
        "equal_update_count": "means the outer rollout schedule (45 updates) and the low-level update schedule "
                              "(ppo_epochs x sequence batches) only; H additionally updates the coordinator and "
                              "discriminators, SET does not",
        "cost_asymmetry": "d2 runs a teacher-forced coordinator forward (evaluate_held_batch) on every non-reset "
                          "step even with infinite costs; the off route (SET) does not",
        "differing_config_fields": differing,
        "config": per_arm,
    }
    return table
