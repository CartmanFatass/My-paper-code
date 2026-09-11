import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / ".agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py"
spec = importlib.util.spec_from_file_location("summarize_runs", SCRIPT)
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


def test_equal_seed_labels_do_not_imply_pairing(tmp_path):
    csv = tmp_path / "scores.csv"
    csv.write_text("task,seed,arm,score\ntoy,1,base,10\ntoy,1,new,13\ntoy,2,new,8\n")
    result = summary.summarize(csv, "base")
    assert result["paired_differences"] == []
    paired = summary.summarize(csv, "base", paired=True)
    assert paired["groups"] == result["groups"]
    difference = paired["paired_differences"][0]
    assert difference["differences"] == {"1": 3}
    assert difference["unmatched_arm_seeds"] == ["2"]
    with pytest.raises(ValueError, match="baseline"):
        summary.summarize(csv, paired=True)
