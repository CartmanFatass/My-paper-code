"""Isolation for the D-state-probe tests.

`probe_fsd_d_state_scale_b06.bind` rebinds module globals of the frozen baseline x interruption
runner, as the other thin entries do. One process per probe makes that harmless in production;
inside a whole-suite pytest run it would leak into the other objects' tests, so every test here
restores them (including `shared.base_summary`, which this object never wraps but its neighbours do).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import probe_fsd_d_state_scale_b06 as probe  # noqa: E402
import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_input_scale_b05 as scale  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

REBOUND = ("OBJECT_ID", "CARD", "BLOCKS", "ROLLOUTS", "PANEL_ROLLOUTS", "ARMS", "FLAT_ARM",
           "WALL_PLANS", "PLANNED_CONFIG_DIFFERENCES", "make_config", "shared")


@pytest.fixture(autouse=True)
def restore_frozen_runner_identities():
    frozen = {name: getattr(b01, name) for name in REBOUND}
    base_summary = production_shared.base_summary
    modules = {module: (module.shared, dict(module.CURRENT)) for module in (matched, scale)}
    probe_shared = probe.shared
    yield
    for name, value in frozen.items():
        setattr(b01, name, value)
    production_shared.base_summary = base_summary
    for module, (module_shared, current) in modules.items():
        module.shared = module_shared
        module.CURRENT.clear()
        module.CURRENT.update(current)
    probe.shared = probe_shared
