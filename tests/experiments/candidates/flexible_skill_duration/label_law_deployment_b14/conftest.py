"""Isolation for the label-law-deployment tests.

The thin entries rebind module globals of the frozen baseline x interruption runner; this object
also binds its own rule class, rule definitions, panel-stream constructor and rule names into B08's
module tables while its four panels run, and B13's own `bind()` rebinds the frozen runner's
identities.  One process per probe makes that harmless in production, but inside a whole-suite
pytest run it would leak into the other objects' tests, so every test here restores them,
including B08's and B09's rule tables, B13's `CURRENT` and this object's own.
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
import run_fsd_commitment_visibility_b12 as b12  # noqa: E402
import run_fsd_flat_entropy_b03 as entropy  # noqa: E402
import run_fsd_flat_input_scale_b05 as scale  # noqa: E402
import run_fsd_flat_update_b04 as update  # noqa: E402
import run_fsd_label_bandit_b13 as b13  # noqa: E402
import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_law_deployment_b14 as b14  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_persistence_b07 as persistence  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

REBOUND = ("OBJECT_ID", "CARD", "BLOCKS", "ROLLOUTS", "PANEL_ROLLOUTS", "ARMS", "FLAT_ARM",
           "WALL_PLANS", "PLANNED_CONFIG_DIFFERENCES", "make_config", "build_learner",
           "evaluate_panel", "shared")
THIN = (matched, entropy, update, scale, persistence, b08, b13)


@pytest.fixture(autouse=True)
def restore_frozen_runner_identities():
    frozen = {name: getattr(b01, name) for name in REBOUND}
    base_summary = production_shared.base_summary
    states = {module: (module.shared, module._orig_base_summary, dict(module.CURRENT))
              for module in THIN}
    probe_shared = b06.shared
    rules = (dict(b08.RULE_DEFINITIONS), b08.RANDOM_RULES, b08.ExecutionRule, b08.label_generator)
    references = (dict(b13.RECORDED_FITS), dict(b08.RECORDED_FITS),
                  dict(b08.REFERENCE_FITS), dict(b08.REFERENCE))
    geometry = (b12.shared, b09.shared, b14.shared)
    mine = dict(b14.CURRENT)
    yield
    for name, value in frozen.items():
        setattr(b01, name, value)
    production_shared.base_summary = base_summary
    for module, (module_shared, original, current) in states.items():
        module.shared, module._orig_base_summary = module_shared, original
        module.CURRENT.clear()
        module.CURRENT.update(current)
    b06.shared = probe_shared
    b08.RULE_DEFINITIONS.clear()
    b08.RULE_DEFINITIONS.update(rules[0])
    b08.RANDOM_RULES, b08.ExecutionRule, b08.label_generator = rules[1], rules[2], rules[3]
    for target, saved in zip((b13.RECORDED_FITS, b08.RECORDED_FITS, b08.REFERENCE_FITS,
                              b08.REFERENCE), references):
        target.clear()
        target.update(saved)
    b12.shared, b09.shared, b14.shared = geometry
    b14.CURRENT.clear()
    b14.CURRENT.update(mine)
