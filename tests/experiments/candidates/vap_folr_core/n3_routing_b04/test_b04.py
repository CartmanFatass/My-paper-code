import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts.run_folr_n3_routing_b04 import cost_projection, expected_counts, result_rule


@pytest.mark.parametrize("differences,branch", [
    ([0.05, 0.05, 0.05], "B04_TYPED_SIGNAL"),
    ([-0.05, -0.05, -0.05], "B04_GENERIC_SIGNAL"),
    ([0.04, -0.04, 0.0], "B04_WITHIN_MEI"),
    ([0.4, -0.1, -0.1], "B04_HETEROGENEOUS"),
    ([-0.4, 0.1, 0.1], "B04_HETEROGENEOUS"),
])
def test_first_matching_reading_rule(differences, branch):
    assert result_rule(differences)["branch"] == branch


def test_full_card_counts_and_shared_writer_charge():
    counts = expected_counts(3, 128, 64, 256, 16)
    assert counts["training_episodes"] == 98304
    assert counts["learner_updates"] == 1536
    assert counts["evaluation_episodes"] == 49920
    assert counts["complete_episodes"] == 148224
    assert counts["primitive_transitions"] == 444672
    coefficients = {phase: {"seconds_per_train_episode": 0.001,
                             "seconds_per_eval_episode": 0.002}
                    for phase in ("WRITER", "TYPED", "GENERIC", "RESET", "LATCH")}
    projected = cost_projection(coefficients)
    assert projected["three_seed_routing_arm_seconds_with_full_shared_writer"]["GENERIC"] == pytest.approx(90.624)


@pytest.mark.skipif("B04_SMOKE_OUTPUT" not in os.environ,
                    reason="The learner smoke is launched once through admitted agent-task.")
def test_runner_smoke_reaches_publication():
    """The admitting agent-task sets the output; no other test starts a learner."""
    import torch

    root = Path(__file__).resolve().parents[5]
    output = Path(os.environ["B04_SMOKE_OUTPUT"])
    start = time.perf_counter()
    subprocess.run([sys.executable, str(root / "scripts/run_folr_n3_routing_b04.py"),
                    "--smoke", "--seeds", "96041", "--output-root", str(output)],
                   cwd=root, check=True)
    assert time.perf_counter() - start < 60
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["configuration"]["technical_only"]
    assert summary["counts"]["primitive_transitions"] == summary["expected_counts"]["primitive_transitions"]
    assert summary["counts"]["updates"] == 8
    assert summary["counts"]["train_episodes"] == 512
    assert len(summary["seed_results"]) == 1
    seed = summary["seed_results"][0]
    for phase in [seed["writer"], *seed["arms"].values()]:
        assert len(phase["training_curve"]) == 2
        assert phase["parameters"]["relative_displacement"] > 0
    assert len(list(output.rglob("*.pt"))) == 4
    assert len(list(output.rglob("*.jsonl"))) == 5
    writer = torch.load(seed["writer"]["checkpoint"], map_location="cpu", weights_only=False)
    assert writer["updates"] == 2
    for arm, phase in seed["arms"].items():
        saved = torch.load(phase["checkpoint"], map_location="cpu", weights_only=False)
        assert saved["optimizer_state"]["state"]
        for name, value in writer["model_state"].items():
            assert torch.equal(saved["model_state"]["partner_writer." + name], value)
        rows = [json.loads(line) for line in Path(phase["final_rows"]).read_text().splitlines()]
        assert len(rows) == 512
        for row in rows:
            assert row["host_reward"] == float(row["action"] == 2 * row["s"] + row["n_new"])
            assert sum(row["probabilities"]) == pytest.approx(1.0, abs=1e-6)
            if arm in ("TYPED", "RESET"):
                assert row["n_old_flip_tv"] == 0
