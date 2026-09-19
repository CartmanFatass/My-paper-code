"""Isolation for the coordinator-batch tests.

Both thin entries rebind module globals of the frozen baseline x interruption runner and wrap its
`shared.base_summary`. One process per fit makes that harmless in production; inside a whole-suite
pytest run it would leak into the other objects' tests, so every test here restores them.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_coordinator_batch_b02 as batch  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402

REBOUND = ("OBJECT_ID", "CARD", "BLOCKS", "ROLLOUTS", "PANEL_ROLLOUTS", "ARMS", "FLAT_ARM",
           "WALL_PLANS", "PLANNED_CONFIG_DIFFERENCES", "make_config", "shared")


@pytest.fixture(autouse=True)
def restore_frozen_runner_identities():
    frozen = {name: getattr(b01, name) for name in REBOUND}
    base_summary = production_shared.base_summary
    matched_state = (matched.shared, matched._orig_base_summary, dict(matched.CURRENT))
    batch_state = (batch.shared, batch._orig_base_summary, dict(batch.CURRENT))
    yield
    for name, value in frozen.items():
        setattr(b01, name, value)
    production_shared.base_summary = base_summary
    matched.shared, matched._orig_base_summary = matched_state[0], matched_state[1]
    matched.CURRENT.clear()
    matched.CURRENT.update(matched_state[2])
    batch.shared, batch._orig_base_summary = batch_state[0], batch_state[1]
    batch.CURRENT.clear()
    batch.CURRENT.update(batch_state[2])
