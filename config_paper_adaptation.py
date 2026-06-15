from config_1 import Config as BaseConfig


class Config(BaseConfig):
    """Paper experiment presets for HMASD domain adaptation studies.

    Use with:
      python train_multiproc_config_1.py --config config_paper_adaptation --preset S4-R3
      python train_multiproc_config_1.py --config config_paper_adaptation --preset S6-S6
      python train_multiproc_config_1.py --config config_paper_adaptation --preset S6-S10
    """

    experiment_preset = "S4-R3"
    paper_data_level = "standard"
    collect_step_rewards = True
    collect_reward_components = True
    collect_performance_metrics = True
    enable_data_sampling = True
    data_sampling_interval = 10
    enable_data_compression = False
    paper_data_dir = None

    def __init__(self, preset=None):
        if preset:
            self.apply_preset(preset)
        else:
            self.apply_preset(self.experiment_preset)

    def apply_preset(self, preset):
        preset = str(preset).upper()
        self.experiment_preset = preset

        if preset.startswith("S4-R"):
            self._apply_scenario4_reward_preset(preset)
        elif preset.startswith("S6-S"):
            self._apply_scenario6_progressive_preset(preset)
        else:
            raise ValueError(
                f"Unknown paper preset '{preset}'. Expected S4-R0/R1/R2/R3 or S6-S4/S5/S6/S7/S8/S9/S10."
            )

    def _disable_backhaul_robustness(self):
        self.w_backhaul_outage = 0.0
        self.w_full_disconnect = 0.0
        self.w_coverage_drop = 0.0
        self.w_outage_memory = 0.0
        self.w_relay_break = 0.0
        self.w_backhaul_margin = 0.0
        self.enable_backhaul_action_guard = False

    def _restore_backhaul_robustness(self):
        self.w_backhaul_outage = 0.8
        self.w_full_disconnect = 1.0
        self.w_coverage_drop = 0.2
        self.w_outage_memory = 0.25
        self.w_relay_break = 1.2
        self.w_backhaul_margin = 0.6

    def _apply_scenario4_reward_preset(self, preset):
        self.scenario = 4
        self.scenario_label = preset
        self.scenario6_reward_type = None
        self.progressive_stage = "S0"

        if preset == "S4-R0":
            self.reward_type = "naive"
            self.w_load_balance = 0.0
            self.w_first_contact = 0.0
            self.w_repulsion = 0.0
            self._disable_backhaul_robustness()
        elif preset == "S4-R1":
            self.reward_type = "load_balance"
            self.w_load_balance = 0.35
            self.w_first_contact = 0.0
            self.w_repulsion = 0.0
            self._disable_backhaul_robustness()
        elif preset == "S4-R2":
            self.reward_type = "load_balance"
            self.w_load_balance = 0.35
            self.w_first_contact = 0.0
            self.w_repulsion = 0.0
            self._restore_backhaul_robustness()
            self.enable_backhaul_action_guard = False
        elif preset == "S4-R3":
            self.reward_type = "load_balance"
            self.w_load_balance = 0.35
            self.w_first_contact = 0.0
            self.w_repulsion = 0.0
            self._restore_backhaul_robustness()
            self.enable_backhaul_action_guard = True
        else:
            raise ValueError(f"Unknown scenario4 reward preset '{preset}'.")

    def _apply_scenario6_progressive_preset(self, preset):
        stage = preset.split("-", 1)[1]
        if stage not in {f"S{i}" for i in range(11)}:
            raise ValueError(f"Unknown scenario6 stage preset '{preset}'.")

        self.scenario = 6
        self.scenario_label = preset
        self.progressive_stage = stage
        self.progressive_scale_mode = "train"
        self.scenario6_reward_type = "progressive_coverage_balance"
        self.reward_type = "load_balance"

        # Fixed maxima keep scenario6 state shape stable across staged profiles.
        self.progressive_max_agents = 6
        self.progressive_max_users = 30
        self.progressive_max_ground_bs = 3
        self.max_observed_bs = 3
        self.max_observed_uavs = max(getattr(self, "max_observed_uavs", 6), 6)
        self.max_observed_users = max(getattr(self, "max_observed_users", 30), 30)

        # Scenario6 owns final reward, but keep robustness metrics available for logging.
        self._restore_backhaul_robustness()
        self.enable_backhaul_action_guard = stage in {"S6", "S7", "S8", "S9", "S10"}
