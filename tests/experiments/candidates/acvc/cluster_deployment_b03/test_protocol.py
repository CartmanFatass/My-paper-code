import json
import sys
from types import SimpleNamespace

import pytest

from experiments.candidates.acvc.cluster_deployment_b02 import protocol as old
from experiments.candidates.acvc.cluster_deployment_b03 import protocol as new


def rows(master=new.MASTER, namespace=new.EVALUATION_NAMESPACE):
    return [dict(phase="eval", arm=arm, episode=i, base=master,
                 evaluation_namespace=namespace, reset_seed=100000 * namespace + 2000 + i,
                 steps=256, S=j * 256, J=j)
            for arm, j in (("C", .1), ("F", .14), ("dwell", .12)) for i in range(64)]


def test_new_identity_and_unchanged_old_defaults():
    result = new.final_panel(rows())
    assert result["complete"]
    assert result["contrasts"]["F-dwell"]["mean_J"] == pytest.approx(.02)
    assert result["contrasts"]["F-C"]["reading"] == "UP"
    assert not old.final_panel(rows())["complete"]
    assert old.final_panel(rows(old.MASTER, old.EVALUATION_NAMESPACE))["complete"]
    assert not new.final_panel(rows(old.MASTER, old.EVALUATION_NAMESPACE))["complete"]


def test_wrong_reset_or_missing_panel_is_not_a_complete_primary():
    changed = rows()
    changed[64]["reset_seed"] += 1
    result = new.final_panel(changed)
    assert not result["complete"]
    assert not result["contrasts"]["F-C"]["complete"]
    assert result["contrasts"]["dwell-C"]["complete"]
    assert not new.final_panel(rows()[:-1])["contrasts"]["F-dwell"]["complete"]


def test_runner_wires_identity_and_final_publication(tmp_path, monkeypatch):
    from scripts import run_acvc_cluster_deployment_b03 as runner

    observed = {}

    def fake_run(output, sha, start, seconds, **kwargs):
        observed.update(kwargs)
        assert sha == "f" * 40 and seconds == 1800
        output.mkdir()
        config = dict(master=kwargs["master"], evaluation_namespace=kwargs["evaluation_namespace"],
                      object=kwargs["object_name"], card=kwargs["card_path"])
        (output / "summary.json").write_text(json.dumps(dict(status="complete", configuration=config)))
        (output / "episodes.jsonl").write_text("\n".join(json.dumps(r) for r in rows()))
        return 0

    monkeypatch.setitem(sys.modules, "scripts.run_acvc_fresh_dense_reuse_b01", SimpleNamespace(run=fake_run))
    output = tmp_path / "output"
    assert runner.main(["--output", str(output), "--launch-sha", "f" * 40,
                        "--execution-seconds", "1800"]) == 0
    result = json.loads((output / "summary.json").read_text())
    assert observed["master"] == new.MASTER
    assert observed["evaluation_namespace"] == new.EVALUATION_NAMESPACE
    assert observed["train_rule"] == "C" and observed["eval_arms"] == new.ARMS
    assert observed["allocation_seconds"] == new.PLANNING_SECONDS
    assert observed["make_env"] is new.make_cluster
    assert result["configuration"]["object"] == new.OBJECT
    assert result["configuration"]["card"] == new.CARD
    assert result["primary"]["complete"]
    with pytest.raises(SystemExit):
        runner.main(["--seed", str(old.MASTER), "--output", str(output),
                     "--launch-sha", "f" * 40, "--execution-seconds", "1800"])
