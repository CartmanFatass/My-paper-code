"""Read only the output of the one CM-launched real engineering check."""

import json
import math
import os
from pathlib import Path

import pytest


@pytest.mark.skipif("VNFC_B01_CHECK_ROOT" not in os.environ, reason="requires the existing CM-launched check output")
def test_real_n7_training_and_primary_output():
    root = Path(os.environ["VNFC_B01_CHECK_ROOT"])
    summary = json.loads((root / "summary.json").read_text())
    assert summary["config"]["profile"] == "engineering-check"
    assert summary["config"]["seed"] == 2026090591
    assert summary["config"]["eval_seed"] == 2026090592
    evaluations = json.loads((root / "evaluation_episodes.json").read_text())
    training = json.loads((root / "training_episodes.json").read_text())
    curves = json.loads((root / "training_curves.json").read_text())
    assert len(evaluations) == 56 and len(training) == 128 and len(curves) == 4
    for row in evaluations + training:
        assert row["integrated_ticks"] == 240
        assert math.isclose(row["R_fail_60"], row["fail_endpoint"][0] / row["fail_endpoint"][1])
        assert math.isclose(row["U_total"], row["total_endpoint"][0] / row["total_endpoint"][1])
        assert math.isclose(row["J_ext"], .5 * row["R_fail_60"] + .5 * row["U_total"])
    for arm in ("MAPR", "DIRECT"):
        exposure = summary["exposure"][arm]
        assert exposure["training_episodes"] == 64 and exposure["joint_transitions"] == 384
        assert exposure["optimizer_steps"] == exposure["backward_calls"] == 64
        assert exposure["evaluation_episodes"] == 24
        assert exposure["final_parameters"]["displacement_norm"] > 0
        rows = [row for row in curves if row["arm"] == arm]
        assert sum(row["checks"]["physical_commands"] for row in rows) == 384
        assert sum(row["checks"]["zone2_commands"] for row in rows) == 192
        initial = next(row for row in summary["timings"]["evaluation"]
                       if row["arm"] == arm and row["checkpoint"] == "initial")
        assert initial["checks"]["presentation_checks"] == 1
    import torch
    for checkpoint in summary["checkpoints"]:
        restored = torch.load(root / checkpoint["path"], map_location="cpu", weights_only=True)
        assert restored["round"] in (0, 1, 2)
        assert restored["model_state"]
    assert len(summary["readout"]["contrasts"]) == 5
    assert summary["total_native_ticks"] == 44160
