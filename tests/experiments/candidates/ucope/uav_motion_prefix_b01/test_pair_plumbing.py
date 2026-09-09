"""P26 dispatch/arithmetic fixtures only: no model, learner or UAV imports/calls."""
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

from experiments.candidates.ucope.uav_motion_prefix_b01 import study


@pytest.fixture
def scratch(tmp_path):
    return tmp_path


def runner_module():
    path = Path("scripts/run_ucope_uav_motion_prefix_b01.py")
    spec = importlib.util.spec_from_file_location("p26_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed,pair,fixture", [(6901, "p24", False), (6902, "p24", False),
                                               (6801, "p21", False), (6802, "p21", False),
                                               (9001, "p21", True), (7001, "b02", False),
                                               (7002, "b02", False), (9001, "b02", True),
                                               (7101, "b03", False), (9001, "b03", True),
                                               (7201, "b04", False), (9001, "b04", True),
                                               (7301, "renewal_b01", False), (9001, "renewal_b01", True),
                                               (7401, "renewal_b02", False), (9001, "renewal_b02", True)])
def test_cli_actual_config_and_rng_propagation(seed, pair, fixture, scratch, monkeypatch):
    # Exercise the actual CLI/Config/run_pair stream expressions; substitute the
    # workload at its existing import boundary, without constructing any model.
    calls = {"initialization": [], "generator": [], "reset": [], "episodes": [], "saved": [], "credit": [], "update_credit": [], "heads": []}
    torch = ModuleType("torch")
    torch.set_num_threads = torch.set_num_interop_threads = lambda n: None
    torch.save = lambda payload, path: calls["saved"].append(payload["configuration"])
    monkeypatch.setitem(sys.modules, "torch", torch)
    prefix = "experiments.candidates.ucope.uav_motion_prefix_b01."
    environment = ModuleType(prefix + "environment")
    def factory(seed, *args):
        calls["reset"].append(seed)
        return object()
    environment.make_real = environment.SyntheticAdapter = factory
    monkeypatch.setitem(sys.modules, prefix + "environment", environment)
    policy = ModuleType(prefix + "policy")
    def templates(seed):
        calls["initialization"].append(seed)
        return None
    def generator(seed):
        calls["generator"].append(seed)
        return seed
    policy.templates, policy.generator = templates, generator
    def arm_copy(common, treatment, **kwargs):
        calls["heads"].append((treatment, kwargs))
        return (SimpleNamespace(state_dict=lambda: {}, arm="T" if treatment else "G"),
                SimpleNamespace(state_dict=lambda: {}))
    policy.arm_copy = arm_copy
    policy.snapshot = lambda *args: {}
    policy.exposure = lambda *args: {}
    monkeypatch.setitem(sys.modules, prefix + "policy", policy)
    learner = ModuleType(prefix + "learner")
    learner.optimizer_for = lambda *args: None
    learner.update = lambda *args, **kwargs: calls["update_credit"].append(dict(arm=args[0].arm, **kwargs)) or []
    def collect(env, actor, critic, horizon, reset, velocity, duration, metadata,
                check, counts, emit, diagnostic, limits, **kwargs):
        calls["episodes"].append((reset, velocity, duration, metadata.copy()))
        calls["credit"].append(kwargs.get("ratio_grouping", "joint"))
        assert "entropy_coef" not in kwargs
        assert kwargs.get("renewal", False) == (pair in ("renewal_b01", "renewal_b02"))
        if metadata["arm"] == "T":
            counts["duration_decisions"] += 5
        emit(dict(metadata, J=0.))
        return {}
    learner.collect_episode = collect
    monkeypatch.setitem(sys.modules, prefix + "learner", learner)
    runner = runner_module()
    argv = ["runner", "--seed", str(seed), "--out", str(scratch)]
    if pair != "p21":
        argv += ["--pair", pair]
    if fixture:
        argv += ["--engineering-fixture"]
    monkeypatch.setattr(sys, "argv", argv)
    assert runner.main() == 0
    summary = json.loads((scratch / "summary.json").read_text())
    assert summary["configuration"]["seed"] == seed
    assert summary["configuration"]["pair"] == pair
    assert summary["configuration"]["horizon"] == (8 if fixture else 256)
    assert summary["pair"] == ("ENGINEERING_FIXTURE" if fixture else pair)
    assert summary["declared_masters"] == ([seed] if fixture else list(study.declared_masters(pair)))
    assert summary["card_section"] == (7 if fixture and pair in ("renewal_b01", "renewal_b02") else "CODE_SPEC §4" if fixture and pair in ("b03", "b04", "renewal_b01", "renewal_b02") else "CODE_SPEC §8" if fixture
                                       else 5 if pair in ("b02", "b03", "b04", "renewal_b01", "renewal_b02") else 10 if pair == "p24" else 8)
    grouping = "agent_compound" if pair in ("b02", "b03", "b04", "renewal_b01", "renewal_b02") else "joint"
    entropy_coef = 0.0 if pair in ("b03", "b04", "renewal_b01", "renewal_b02") else 0.01
    assert set(calls["credit"]) == {grouping}
    assert all(c.get("ratio_grouping", "joint") == grouping for c in calls["update_credit"])
    assert summary["configuration"]["ratio_grouping"] == grouping
    assert summary["configuration"]["entropy_coef"] == entropy_coef
    assert all(c.get("entropy_coef", .01) == entropy_coef for c in calls["update_credit"])
    assert all(a["entropy_coef"] == entropy_coef for a in summary["arms"].values())
    if pair == "b02":
        assert summary["object"] == study.B02_OBJECT and summary["card"] == study.B02_CARD
        assert summary["ratio_grouping"] == grouping
    if pair == "b03":
        assert summary["object"] == study.B03_OBJECT and summary["card"] == study.B03_CARD
        assert summary["ratio_grouping"] == grouping and summary["entropy_coef"] == 0.0
    assert calls["initialization"] == [seed]  # templates retains b+11 internally, unchanged.
    b = 100000 * seed
    assert summary["seeds"]["initialization"] == b + 11
    if pair in ("b04", "renewal_b01", "renewal_b02"):
        expected_object, expected_card = ((study.RENEWAL_OBJECT, study.RENEWAL_CARD) if pair in ("renewal_b01", "renewal_b02")
                                          else (study.B04_OBJECT, study.B04_CARD))
        if pair == "renewal_b02":
            expected_object, expected_card = study.RENEWAL_B02_OBJECT, study.RENEWAL_B02_CARD
        assert summary["object"] == expected_object and summary["card"] == expected_card
        assert summary["ratio_grouping"] == grouping and summary["entropy_coef"] == 0.0
        for binding in (summary, summary["configuration"]):
            assert binding["treatment_duration_mode"] == "sampled_command"
            assert binding["treatment_duration_head_seed"] == b + 12
        assert calls["heads"] == [(True, {"duration_head_seed": b + 12}),
                                  (False, {"duration_head_seed": None})]
        assert summary["arms"]["T"]["duration_mode"] == "sampled_command"
        assert summary["arms"]["T"]["duration_head_seed"] == b + 12
        assert summary["arms"]["G"]["duration_mode"] == "none"
        assert summary["arms"]["G"]["duration_head_seed"] is None
    else:
        assert calls["heads"] == [(True, {}), (False, {})]
    assert calls["reset"] == [b + 1000, b + 1000]
    train_n, eval_n = (2, 2) if fixture else (512, 32)
    assert len(calls["update_credit"]) == train_n
    for arm in ("T", "G"):
        assert sum(c["arm"] == arm for c in calls["update_credit"]) == train_n // 2
    for arm in ("T", "G", "H"):
        entries = [c for c in calls["episodes"] if c[3]["arm"] == arm]
        train = [c for c in entries if c[3]["phase"] == "train"]
        evaluation = [c for c in entries if c[3]["phase"] == "eval"]
        assert len(train) == (0 if arm == "H" else train_n)
        assert [c[0] for c in train] == ([] if arm == "H" else list(range(b + 1000, b + 1000 + train_n)))
        assert all(c[1:3] == (b + 21, b + 22) for c in train)
        assert [c[0] for c in evaluation] == list(range(b + 2000, b + 2000 + eval_n))
        assert [c[1:3] for c in evaluation] == ([(None, None)] * eval_n if arm == "H"
                                                else [(b + 3000 + e, b + 4000 + e) for e in range(eval_n)])
    assert len(calls["saved"]) == 2 and all(c == summary["configuration"] for c in calls["saved"])


def summary(seed, differences, pair=None):
    result = {"seed": seed, "mode": "UAV_B_EXPLORE", "card": study.CARD,
              "primary": {"complete": True, "T_minus_G": study.difference_stats(differences)}}
    if pair:
        result.update(pair=pair, declared_masters=list(study.declared_masters(pair)),
                      card_section=5 if pair == "b02" else 10 if pair == "p24" else 8)
    if pair == "b02":
        result.update(object=study.B02_OBJECT, card=study.B02_CARD, ratio_grouping="agent_compound")
    return result


@pytest.mark.parametrize("pair,seeds", [("p21", (6801, 6802)), ("p24", (6901, 6902)), ("b02", (7001, 7002))])
def test_declared_pair_arithmetic(pair, seeds):
    inputs = [summary(seeds[0], [1, 3], pair), summary(seeds[1], [4, 6], pair)]
    result = study.aggregate(inputs, pair)
    assert result["pair"] == pair and result["declared_masters"] == list(seeds)
    assert result["card"] == (study.B02_CARD if pair == "b02" else study.CARD) and result["card_section"] == (5 if pair == "b02" else 10 if pair == "p24" else 8)
    assert result["primary"]["mean"] == 3.5
    assert result["primary"]["training_endpoint_sample_sd"] == pytest.approx(math.sqrt(4.5))
    assert result["primary"]["conditional_se"] == pytest.approx(math.sqrt(.5))
    assert result["primary"]["reading"] == "UP"
    assert study.aggregate(inputs[::-1], pair)["primary"]["mean"] == 3.5


def test_historical_p21_and_synthetic_aggregation_preserved():
    old = [summary(6801, [-1, -3]), summary(6802, [-4, -6])]
    assert study.aggregate(old)["primary"]["mean"] == -3.5
    assert study.aggregate(old)["primary"]["reading"] == "DOWN"
    for seed, item in enumerate(old):
        item.update(seed=seed, mode="ENGINEERING_FIXTURE")
    assert study.aggregate(old)["pair"] == "ENGINEERING_FIXTURE"


def test_cli_p24_aggregate_dispatch(scratch, monkeypatch):
    paths = [scratch / "6901.json", scratch / "6902.json"]
    for path, seed, differences in zip(paths, (6901, 6902), ([1, 3], [4, 6])):
        path.write_text(json.dumps(summary(seed, differences, "p24")))
    runner = runner_module()
    monkeypatch.setattr(runner, "run_pair", lambda *a: pytest.fail("workload entered"))
    monkeypatch.setattr(sys, "argv", ["runner", "--pair", "p24", "--aggregate",
                                     *map(str, paths), "--out", str(scratch / "aggregate")])
    assert runner.main() == 0
    result = json.loads((scratch / "aggregate/summary.json").read_text())
    assert result["pair"] == "p24" and result["primary"]["mean"] == 3.5


@pytest.mark.parametrize("fault", ["duplicate", "wrong_seed", "cross_pair", "wrong_declaration",
                                    "wrong_card", "synthetic_mixed", "too_many", "missing_p24_label"])
def test_aggregate_rejects_mismatches(fault):
    inputs = [summary(6901, [1, 3], "p24"), summary(6902, [4, 6], "p24")]
    if fault == "duplicate": inputs[1]["seed"] = 6901
    elif fault == "wrong_seed": inputs[1]["seed"] = 6903
    elif fault == "cross_pair": inputs[1]["pair"] = "p21"
    elif fault == "wrong_declaration": inputs[1]["declared_masters"] = [6801, 6802]
    elif fault == "wrong_card": inputs[1]["card_section"] = 8
    elif fault == "synthetic_mixed": inputs[1]["mode"] = "ENGINEERING_FIXTURE"
    elif fault == "too_many": inputs += [inputs[0]]
    elif fault == "missing_p24_label": del inputs[1]["pair"]
    with pytest.raises(ValueError): study.aggregate(inputs, "p24")


@pytest.mark.parametrize("args", [["--seed", "6901"], ["--pair", "p24", "--seed", "6801"],
                                   ["--pair", "p24", "--engineering-fixture", "--seed", "9001"]])
def test_cli_rejects_mismatched_seed_before_workload(args, scratch, monkeypatch):
    runner = runner_module()
    monkeypatch.setattr(runner, "run_pair", lambda *a: pytest.fail("workload entered"))
    monkeypatch.setattr(sys, "argv", ["runner", *args, "--out", str(scratch)])
    with pytest.raises(SystemExit) as error: runner.main()
    assert error.value.code == 2


@pytest.mark.parametrize("fault", ["object", "ratio_grouping", "pair", "card", "card_section",
                                    "declared_masters", "seed", "mode", "missing", "duplicate"])
def test_b02_rejects_mixed_objectives(fault):
    inputs = [summary(7001, [1, 3], "b02"), summary(7002, [4, 6], "b02")]
    if fault == "missing":
        del inputs[1]["ratio_grouping"]
    elif fault == "duplicate":
        inputs[1] = inputs[0]
    else:
        inputs[1][fault] = "wrong"
    with pytest.raises(ValueError):
        study.aggregate(inputs, "b02")


def test_b02_negative_partial_and_fixture_rejection():
    inputs = [summary(7001, [-1, -3], "b02"), summary(7002, [-4, -6], "b02")]
    assert study.aggregate(inputs, "b02")["primary"]["reading"] == "DOWN"
    inputs[0]["primary"]["complete"] = False
    assert study.aggregate(inputs, "b02")["primary"]["reading"] == "PARTIAL"
    for item in inputs:
        item["mode"] = "ENGINEERING_FIXTURE"
    with pytest.raises(ValueError):
        study.aggregate(inputs, "b02")


@pytest.mark.parametrize("pair", ["b03", "b04", "renewal_b01", "renewal_b02"])
def test_single_pair_rejects_aggregate_before_input_access(pair, scratch, monkeypatch):
    with pytest.raises(ValueError, match="one training pair"):
        study.aggregate(None, pair)
    runner = runner_module()
    monkeypatch.setattr(runner, "run_pair", lambda *a: pytest.fail("workload entered"))
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: pytest.fail("aggregate input read"))
    monkeypatch.setattr(sys, "argv", ["runner", "--pair", pair, "--aggregate",
                                     "missing-first.json", "missing-second.json", "--out", str(scratch)])
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2


@pytest.mark.parametrize("pair,seed", [("b03", s) for s in (7001, 7002, 7102, 9001)]
                         + [("b04", s) for s in (7001, 7101, 7202, 9001)]
                         + [("renewal_b01", s) for s in (7201, 7302, 7401, 9001)]
                         + [("renewal_b02", s) for s in (7301, 7402, 9001)])
def test_single_pair_wrong_master_never_enters_workload(pair, seed, scratch, monkeypatch):
    runner = runner_module()
    monkeypatch.setattr(runner, "run_pair", lambda *a: pytest.fail("workload entered"))
    monkeypatch.setattr(sys, "argv", ["runner", "--pair", pair, "--seed", str(seed), "--out", str(scratch)])
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2
