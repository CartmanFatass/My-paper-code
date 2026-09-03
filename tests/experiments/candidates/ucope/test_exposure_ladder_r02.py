"""Per-arm exposure statistics and object identity for the R02 exposure ladder.

Registered by section 9 of
``docs/research/candidates/ucope/UCOPE_SECTION11_RECAST_INTAKE_20260902.md``.

R02 reuses R01's workload byte for byte and changes only the reading rule, which is applied
per arm against that arm's own threshold with ``FT-XF-FLEX``'s paired residual explicitly
inside its own displacement statistic. These tests pin the statistic the rule reads and the
object identity the runner records, and they check that R01's own fields are unchanged.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    LADDER_ARMS,
    LADDER_OBJECT_ID,
    LADDER_R02_MOVEMENT_THRESHOLDS,
    LADDER_R02_OBJECT_ID,
    LADDER_R02_RUNG_1_ID,
    LADDER_R02_RUNG_2_ID,
    LADDER_RUNG_1_ID,
    LADDER_RUNG_2_ID,
    ScoutConfig,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import build_arm  # noqa: E402

LADDER_SCRIPT = PROJECT_ROOT / "scripts" / "run_ucope_exposure_ladder_rung1.py"


def _load_ladder():
    spec = importlib.util.spec_from_file_location("ucope_exposure_ladder_r02", LADDER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _exposure(monkeypatch, mutate):
    import torch

    ladder = _load_ladder()
    config = ScoutConfig.ladder_rung_1()

    def fake_load_checkpoint(path):
        parts = Path(path).parts
        return {"arm_id": parts[-4], "seed_id": parts[-3], "fold_id": int(parts[-2].split("-")[1])}

    def fake_restore_checkpoint(payload):
        root, tail = build_arm(payload["arm_id"], payload["seed_id"], payload["fold_id"])
        with torch.no_grad():
            mutate(payload["arm_id"], "root", root)
            mutate(payload["arm_id"], "tail", tail)
        return root, tail, None, None

    monkeypatch.setattr(ladder, "load_checkpoint", fake_load_checkpoint)
    monkeypatch.setattr(ladder, "restore_checkpoint", fake_restore_checkpoint)
    return ladder.exposure_line(config, Path("synthetic")), config


def test_r02_object_identity_is_separate_and_r01_is_unchanged():
    ladder = _load_ladder()
    assert LADDER_R02_OBJECT_ID == "UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02"
    assert LADDER_R02_OBJECT_ID != LADDER_OBJECT_ID
    assert ladder.LADDER_OBJECTS["R01"] == (LADDER_OBJECT_ID, {1: LADDER_RUNG_1_ID, 2: LADDER_RUNG_2_ID})
    assert ladder.LADDER_OBJECTS["R02"] == (
        LADDER_R02_OBJECT_ID,
        {1: LADDER_R02_RUNG_1_ID, 2: LADDER_R02_RUNG_2_ID},
    )


def test_r02_reuses_the_r01_workload_byte_for_byte():
    """R02 changes only the reading rule; every configured quantity is R01's."""
    for factory in (ScoutConfig.ladder_rung_1, ScoutConfig.ladder_rung_2):
        config = factory()
        assert config.arms == LADDER_ARMS
        assert config.seed_ids == B1_SEEDS
        assert config.episodes_per_context == 5_120
        assert config.batch_size == 256


def test_r02_rejects_an_unknown_ladder_object(tmp_path):
    ladder = _load_ladder()
    with pytest.raises(ladder.LaunchRefusal):
        ladder.run_rung(tmp_path / "unused", rung=1, ladder_object="R99")


def test_r02_thresholds_are_declared_per_arm_and_equal():
    """Both arms share the optimizer arithmetic, so the two thresholds coincide at 0.30.

    They are nevertheless separate values applied separately, which is the whole point of
    the R02 rule: neither arm's number can decide the other arm's branch.
    """
    assert set(LADDER_R02_MOVEMENT_THRESHOLDS) == set(LADDER_ARMS)
    assert LADDER_R02_MOVEMENT_THRESHOLDS == {"FT-XF-FLEX": 0.30, "FT-XF-BC": 0.30}


def test_per_arm_block_reports_each_arm_separately(monkeypatch):
    step = 0.125

    def mutate(_arm_id, _stage, model):
        model.beta.add_(step)

    line, config = _exposure(monkeypatch, mutate)
    assert set(line["per_arm"]) == set(config.arms)
    for arm, block in line["per_arm"].items():
        arm_rows = [row for row in line["rows"] if row["arm_id"] == arm]
        assert block["rows"] == len(arm_rows) == 12
        assert block["minimum_beta_max_abs_coordinate_move"] == min(
            row["beta_max_abs_coordinate_move"] for row in arm_rows
        )
        assert block["minimum_max_abs_coordinate_move"] == min(row["max_abs_coordinate_move"] for row in arm_rows)
        assert block["movement_threshold"] == LADDER_R02_MOVEMENT_THRESHOLDS[arm]
        assert block["residual_included_in_max_abs_coordinate_move"] is (arm == "FT-XF-FLEX")


def test_bc_all_coordinate_move_equals_its_beta_move(monkeypatch):
    """FT-XF-BC has no residual, so the two statistics coincide exactly for that arm."""
    step = 0.125

    def mutate(_arm_id, _stage, model):
        model.beta.add_(step)

    line, _config = _exposure(monkeypatch, mutate)
    for row in line["rows"]:
        if row["arm_id"] == "FT-XF-BC":
            assert row["max_abs_coordinate_move"] == row["beta_max_abs_coordinate_move"]


def test_flex_residual_is_inside_the_r02_statistic_and_outside_the_r01_one(monkeypatch):
    """The exact defect the per-arm rule fixes: R01's m cannot see FLEX's residual move."""
    step = 0.5

    def mutate(arm_id, _stage, model):
        if arm_id == "FT-XF-FLEX":
            model.residual[4].bias.add_(step)

    line, _config = _exposure(monkeypatch, mutate)
    flex = line["per_arm"]["FT-XF-FLEX"]
    bc = line["per_arm"]["FT-XF-BC"]
    assert flex["minimum_beta_max_abs_coordinate_move"] == 0.0
    assert abs(flex["minimum_max_abs_coordinate_move"] - step) < 1e-6
    assert bc["minimum_max_abs_coordinate_move"] == 0.0
    # the R01 fields keep their old meaning, unchanged
    assert line["minimum_beta_max_abs_coordinate_move"] == 0.0
    assert line["learner_can_move_in_its_budget"] is False


def test_r01_exposure_fields_are_all_still_present(monkeypatch):
    def mutate(_arm_id, _stage, model):
        model.beta.add_(0.25)

    line, _config = _exposure(monkeypatch, mutate)
    required_row_fields = {
        "arm_id", "seed_id", "fold_id", "stage",
        "parameter_displacement_l2", "initialisation_scale_l2",
        "displacement_over_initialisation_scale",
        "beta_displacement_l2", "beta_initialisation_l2", "beta_max_abs_coordinate_move",
        "max_abs_coordinate_move",
    }
    for row in line["rows"]:
        assert set(row) == required_row_fields
    for field in (
        "statement", "learning_rate", "tail_updates", "root_updates", "rows",
        "minimum_displacement_ratio", "maximum_displacement_ratio",
        "minimum_beta_max_abs_coordinate_move", "maximum_beta_max_abs_coordinate_move",
        "learner_can_move_in_its_budget", "per_arm",
    ):
        assert field in line
