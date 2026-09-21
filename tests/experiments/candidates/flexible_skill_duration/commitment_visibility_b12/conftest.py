"""Isolation for the commitment-visibility tests.

The same layers the B08, B09, B10 and B11 suites describe. The thin entries rebind module globals
of the frozen baseline x interruption runner and wrap its `shared.base_summary`; B09 binds its own
execution rule and rule definitions into B08's module tables for the duration of a run, and a
failure inside that binding must not leave B08's tables carrying B09's rules for the rest of a
whole-suite pytest run. This object binds one thing of its own - B11's module-global
`collection_seed`, for the duration of one cap's collection - and a failure inside that binding must
not leave B11 carrying this object's seed derivation, so the fixture restores it too.
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
import run_fsd_coordinator_signal_b11 as signal  # noqa: E402
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
RULE_TABLES = ("RULES", "RANDOM_RULES", "RULE_CAPS", "BASELINE_RULE", "ExecutionRule")


@pytest.fixture(autouse=True)
def restore_frozen_runner_identities():
    frozen = {name: getattr(b01, name) for name in REBOUND}
    base_summary = production_shared.base_summary
    states = {module: (module.shared, module._orig_base_summary, dict(module.CURRENT))
              for module in THIN}
    probe_shared = b06.shared
    references = (dict(label.RECORDED_FITS), dict(label.REFERENCE_FITS), dict(label.REFERENCE))
    tables = {name: getattr(label, name) for name in RULE_TABLES}
    definitions = dict(label.RULE_DEFINITIONS)
    b11_collection_seed = signal.collection_seed
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
    for name, value in tables.items():
        setattr(label, name, value)
    label.RULE_DEFINITIONS.clear()
    label.RULE_DEFINITIONS.update(definitions)
    signal.collection_seed = b11_collection_seed
