"""Isolation for the label-content tests.

The thin entries rebind module globals of the frozen baseline x interruption runner and wrap its
`shared.base_summary`; this object also wraps the frozen `build_learner` for the duration of a fit,
and its probe rebinds the runner without wrapping anything. One process per fit or probe makes that
harmless in production; inside a whole-suite pytest run it would leak into the other objects' tests,
so every test here restores them, including this object's own reference maps.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import probe_fsd_d_state_scale_b06 as b06  # noqa: E402
import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_entropy_b03 as entropy  # noqa: E402
import run_fsd_flat_input_scale_b05 as scale  # noqa: E402
import run_fsd_flat_update_b04 as update  # noqa: E402
import run_fsd_label_content_b08 as label  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_persistence_b07 as persistence  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

REBOUND = ("OBJECT_ID", "CARD", "BLOCKS", "ROLLOUTS", "PANEL_ROLLOUTS", "ARMS", "FLAT_ARM",
           "WALL_PLANS", "PLANNED_CONFIG_DIFFERENCES", "make_config", "build_learner", "shared")
THIN = (matched, entropy, update, scale, persistence, label)


@pytest.fixture(autouse=True)
def restore_frozen_runner_identities():
    frozen = {name: getattr(b01, name) for name in REBOUND}
    base_summary = production_shared.base_summary
    states = {module: (module.shared, module._orig_base_summary, dict(module.CURRENT))
              for module in THIN}
    probe_shared = b06.shared
    references = (dict(label.RECORDED_FITS), dict(label.REFERENCE_FITS), dict(label.REFERENCE))
    yield
    for name, value in frozen.items():
        setattr(b01, name, value)
    production_shared.base_summary = base_summary
    for module, (module_shared, original, current) in states.items():
        module.shared, module._orig_base_summary = module_shared, original
        module.CURRENT.clear()
        module.CURRENT.update(current)
    b06.shared = probe_shared
    for target, saved in zip((label.RECORDED_FITS, label.REFERENCE_FITS, label.REFERENCE),
                             references):
        target.clear()
        target.update(saved)
