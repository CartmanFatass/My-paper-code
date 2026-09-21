"""Fixed fresh identity and block-level confirmation reading."""

from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.vsp_03.opportunity_b09 import study


def blocks(values):
    return [{"seed": seed, "status": "complete", "comparisons": {
        a + "-" + b: {"mean": -v if (a,b) == ("G","O") else 0.}
        for a,b in study.CONTRASTS}} for seed,v in zip(study.SEEDS, values)]


@pytest.mark.parametrize("values,reading", [
    ([.01,.02,.03,.02,.02], "O_SUPERIOR"),
    ([-.01,-.02,-.03,-.02,-.02], "G_SUPERIOR"),
    ([-.02,-.01,0.,.01,.02], "INCONCLUSIVE"),
])
def test_actual_five_block_rule_and_sign(values, reading):
    result, label = study.aggregate(blocks(values))
    assert result["O-G"]["per_block"] == values
    assert label["label"] == reading
    assert result["O-G"]["df"] == 4
    if reading == "O_SUPERIOR":
        assert result["O-G"]["mean"] == pytest.approx(.02)
        assert result["O-G"]["t95"] == pytest.approx([.01122010966829831,.02877989033170169])
        assert not label["lower_bound_above_practical_reference"]


def test_missing_or_development_blocks_refuse():
    source = blocks([.02]*5)
    with pytest.raises(ValueError): study.aggregate(source[:-1])
    source[0]["seed"] = 21801
    with pytest.raises(ValueError): study.aggregate(source)


def test_confirmation_entry_refuses_direct_launch(tmp_path):
    root = Path(__file__).resolve().parents[5]
    output = tmp_path / "no_admission"
    proc = subprocess.run([sys.executable, str(root / "scripts/run_vsp03_opportunity_b09.py"),
                           "--seeds", *map(str, study.SEEDS), "--launch-sha", "a"*40,
                           "--out", str(output)], cwd=root, capture_output=True, text=True)
    assert proc.returncode != 0 and "admission" in proc.stderr.lower()
    assert not output.exists()
