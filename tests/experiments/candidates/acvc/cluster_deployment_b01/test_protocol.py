"""Changed cluster construction, fixed binding and primary publication only."""
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import types

import pytest

from experiments.candidates.acvc.cluster_deployment_b01 import protocol as p
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real


def test_cluster_is_set_before_constructor_and_every_reset_without_changing_default():
    class Base:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.laws = [("constructor", kwargs["user_distribution"])]

        def reset(self, seed):
            self.laws.append((seed, self.kwargs["user_distribution"]))

    class Adapter:
        def __init__(self, base, seed):
            self.env = base
            base.reset(seed)

        def reset(self, seed):
            self.env.reset(seed)

    for seed in (2145701000, 3145700062, 3145700063, 3145700064):
        cluster = p.make_cluster(seed, Base, Adapter)
        uniform = make_real(seed, Base, Adapter)
        for episode in (0, 63):
            cluster.reset(3145702000 + episode)
        assert all(law == "cluster" for _, law in cluster.env.laws)
        assert all(law == "uniform" for _, law in uniform.env.laws)
        expected = dict(uniform.env.kwargs, user_distribution="cluster")
        assert cluster.env.kwargs == expected
        assert expected["n_uavs"] == 5 and expected["n_users"] == 50 and expected["max_steps"] == 256
        assert expected["seed"] == seed and expected["max_observed_users"] == 20


def test_cli_binds_exact_single_fit_three_panels_and_new_caps(monkeypatch):
    calls = []
    fake = types.ModuleType("scripts.run_acvc_fresh_dense_reuse_b01")
    fake.run = lambda *args, **kwargs: calls.append((args, kwargs)) or 0
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_cluster_deployment_b01.py"
    spec = importlib.util.spec_from_file_location("cluster_cli", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    publications = []
    monkeypatch.setattr(module, "publish", lambda *args: publications.append(args) or True)
    args = ["--output", "fixture-unused", "--launch-sha", "published", "--execution-seconds", "580"]
    assert module.main(args) == 0
    positional, options = calls[0]
    assert positional[0] == Path("fixture-unused") and positional[1] == "published" and positional[3] == 580
    assert options == dict(make_env=p.make_cluster, master=21457, evaluation_namespace=31457,
                           object_name=p.OBJECT, card_path=p.CARD, mode="UAV_B_EXPLORE",
                           allocation_seconds=p.CAPS, train_rule="C", eval_arms=("C", "F", "dwell"))
    assert p.CAPS == dict(whole_supervised_task=600, cumulative_runtime_support=600, complete_charge=1200)
    assert publications == [(Path("fixture-unused"), module.PROCESS_START)]
    assert not Path("fixture-unused").exists()
    with pytest.raises(SystemExit) as error:
        module.main(args + ["--seed", "20319"])
    assert error.value.code == 2 and len(calls) == 1


def test_cli_sets_thread_environment_before_protocol_import(monkeypatch):
    names = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS")
    for name in names:
        monkeypatch.setenv(name, "7")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    observed = []
    fake = types.ModuleType(p.__name__)

    def protocol_attribute(name):
        assert all(os.environ[k] == "1" for k in names)
        assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
        observed.append(name)
        return getattr(p, name)

    fake.__getattr__ = protocol_attribute
    monkeypatch.setitem(sys.modules, p.__name__, fake)
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_cluster_deployment_b01.py"
    spec = importlib.util.spec_from_file_location("cluster_import_order", script)
    spec.loader.exec_module(importlib.util.module_from_spec(spec))
    assert "make_cluster" in observed


def rows():
    result = []
    for arm in p.ARMS:
        for episode in range(64):
            baseline = episode / 64
            delta = 0 if arm == "C" else .007 if arm == "dwell" else .02 + (.04 if episode % 2 else -.04)
            score = baseline + delta
            result.append(dict(phase="eval", arm=arm, rule=arm, episode=episode, base=p.MASTER,
                               evaluation_namespace=p.EVALUATION_NAMESPACE, steps=256,
                               reset_seed=3145702000 + episode, J=score, S=score * 256))
    return result


def test_full_primary_keeps_dispersion_adverse_worlds_and_absolute_scores():
    assert all("master" not in r and r["base"] == p.MASTER for r in rows())
    result = p.final_panel(rows())
    assert result["complete"] and result["primaries"] == ["F-C", "F-dwell"]
    fc = result["contrasts"]["F-C"]
    assert fc["mean_J"] == pytest.approx(.02) and fc["mean_S"] == pytest.approx(5.12)
    assert fc["sample_SD_J"] == pytest.approx(.04 * math.sqrt(64 / 63))
    assert fc["conditional_SE_J"] == pytest.approx(fc["sample_SD_J"] / 8)
    assert fc["adverse"] == fc["favorable"] == 32 and fc["zero"] == 0
    assert fc["minimum_J"] == pytest.approx(-.02) and fc["maximum_J"] == pytest.approx(.06)
    assert len(fc["paired_differences_J"]) == 64 and fc["episode_ids"] == list(range(64))
    assert result["arm_mean_J"]["C"] == .4921875 and result["arm_mean_S"]["C"] == 126
    assert result["contrasts"]["F-dwell"]["mean_J"] == pytest.approx(.013)


@pytest.mark.parametrize("delta,expected", [(-.02, "DOWN"), (-.01, "WITHIN"), (0., "WITHIN"), (.01, "WITHIN"), (.02, "UP")])
def test_publication_reads_frozen_boundaries_and_sign(delta, expected):
    data = rows()
    for row in data:
        row["J"] = delta if row["arm"] == "F" else 0.
        row["S"] = row["J"] * 256
    result = p.final_panel(data)["contrasts"]["F-C"]
    assert result["reading"] == expected
    assert result["sign"] == ("positive" if delta > 0 else "negative" if delta < 0 else "zero")


@pytest.mark.parametrize("defect", ["missing", "duplicate", "nonfinite", "reset", "metric"])
def test_damaged_F_does_not_erase_intact_C_dwell(defect):
    data = rows()
    if defect == "missing":
        del data[64]
    elif defect == "duplicate":
        data[65] = data[64].copy()
    elif defect == "nonfinite":
        data[64]["J"] = None
    elif defect == "reset":
        data[64]["reset_seed"] += 1
    else:
        data[64]["S"] += 1
    result = p.final_panel(data)
    assert not result["complete"]
    assert not result["contrasts"]["F-C"]["complete"]
    assert not result["contrasts"]["F-dwell"]["complete"]
    assert result["contrasts"]["dwell-C"]["complete"]
    assert result["contrasts"]["dwell-C"]["mean_J"] == pytest.approx(.007)


def test_final_publication_preserves_existing_training_facts_and_partial_dependency(tmp_path):
    data = rows()
    data[64]["J"] = None
    before = dict(status="complete", configuration={}, counts={"optimizer_steps": 1024},
                  exposure={"total": {"displacement": 1.0}}, object=p.OBJECT,
                  master=p.MASTER, evaluation_namespace=p.EVALUATION_NAMESPACE, allocation_seconds=p.CAPS)
    (tmp_path / "summary.json").write_text(json.dumps(before), encoding="utf-8")
    (tmp_path / "episodes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in data), encoding="utf-8")
    assert not p.publish(tmp_path, time.monotonic())
    after = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert after["configuration"] == {"user_distribution": "cluster", "training_rule": "C"}
    assert after["counts"] == before["counts"] and after["exposure"] == before["exposure"]
    assert after["status"] == "incomplete" and after["primary"]["contrasts"]["dwell-C"]["complete"]
    assert len((tmp_path / "episodes.jsonl").read_text(encoding="utf-8").splitlines()) == 192
