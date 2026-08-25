"""Deterministic Scenario 7 physical-feasibility preflight."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_1 import Config
from train_multiproc_config_1 import run_scenario7_physical_feasibility_check


if __name__ == "__main__":
    summary = run_scenario7_physical_feasibility_check(
        Config("S7-S3"),
        seed_count=20,
    )
    print(
        f"qos_feasible={summary['qos_feasible_rate']:.1%}, "
        f"no_charge_pressure={summary['no_charge_pressure_rate']:.1%}, "
        f"charging_success={summary['charge_success_rate']:.1%}, "
        f"depletion_free={summary['depletion_free_rate']:.1%}, "
        f"rotation_qos={summary['mean_rotation_qos_satisfaction_ratio']:.3f}"
    )
