import json

import pytest

from experiments.candidates.acvc.cluster_fixed_lr_pair_b01 import protocol as p
from tools.analysis.acvc_fixed_lr_pair_b01 import analyze


@pytest.mark.parametrize("summary_tail", [None, '{"status":'])
def test_failed_original_still_publishes_independent_panel_and_complete_rows(tmp_path, summary_tail):
    paths = {recipe: tmp_path / recipe for recipe in p.RECIPES}
    for recipe, path in paths.items():
        path.mkdir()
        rows = []
        for arm, value in (("C", .1), ("F", .14), ("dwell", .12)):
            for episode in range(64):
                rows.append(dict(phase="eval",recipe=recipe,learning_rate=p.RECIPES[recipe],arm=arm,
                                 episode=episode,base=p.MASTER,evaluation_namespace=p.EVALUATION_NAMESPACE,
                                 checkpoint_episode=4096,reset_seed=100000*p.EVALUATION_NAMESPACE+2000+episode,
                                 steps=256,J=value,S=256*value))
        (path / "episodes.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n")
        (path / "updates.jsonl").write_text("")
        if recipe == "reference":
            (path / "summary.json").write_text(json.dumps({"primary":p.final_panel(rows,recipe)}))
        else:
            with (path / "episodes.jsonl").open("a") as stream:
                stream.write('{"phase":')
            if summary_tail is not None:
                (path / "summary.json").write_text(summary_tail)
    result = analyze(paths)
    assert result["object_status"] == "incomplete" and not result["checks_passed"]
    assert len(result["originals"]["low"]["ingestion_errors"]) == 2
    assert result["originals"]["reference"]["ingestion_errors"] == []
    assert result["pair"]["recipes"]["reference"]["contrasts"]["F-C"]["mean_J"] == pytest.approx(.04)
    assert result["pair"]["recipes"]["low"]["arms"]["C"]["available_rows"] == 64
    assert result["costs"]["resources"] == "resources_unmeasured"
    # Full panel rows remain a narrower direct fact; they do not prove either complete fit.
    assert result["pair"]["complete"] and result["object_status"] != "complete"
