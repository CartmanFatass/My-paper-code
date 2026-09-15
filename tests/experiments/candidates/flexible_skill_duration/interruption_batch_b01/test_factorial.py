"""Bounded synthetic checks; zero real learners, hosts or scientific invocations."""
import copy
import importlib.util
import inspect
import json
import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
spec = importlib.util.spec_from_file_location("fsd_factorial_helpers", Path(__file__).parents[1] /
                                            "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
r = helpers.r
import run_fsd_interruption_batch_b01 as factorial

fake_only = helpers.fake_only


@pytest.fixture(autouse=True)
def bind_fake_shared(monkeypatch, fake_only):
    monkeypatch.setattr(factorial, "shared", r)


@pytest.mark.parametrize("seed", [772003, 772103])
@pytest.mark.parametrize("arm,batch,gap", [("D128", 128, float("inf")), ("D1280", 1280, float("inf")),
                                         ("I128", 128, .25), ("I1280", 1280, .25)])
def test_actual_fit_bindings_rng_and_only_final(monkeypatch, tmp_path, fake_only, arm, batch, gap, seed):
    evaluation_seed = factorial.BLOCKS[seed]
    saved = r.final_evaluation
    def evaluate(*args, **kwargs):
        before = helpers.rng_state()
        result = saved(*args, **kwargs)
        helpers.assert_rng_equal(before, helpers.rng_state())
        return result
    monkeypatch.setattr(r, "final_evaluation", evaluate)
    monkeypatch.setattr(r, "PROCESS_START", r.time.perf_counter() - 1e7)
    assert factorial.main(["fit", "--arm", arm, "--seed", str(seed), "--output-root", str(tmp_path)]) == 0
    summary = json.loads((tmp_path / "summary.json").read_text())
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert summary["cap_seconds"] is manifest["cap_seconds"] is None
    assert summary["wall_seconds_before_publication"] > summary["ordinary_wall_plan_seconds"]
    assert summary["factorial_arm"] == manifest["factorial_arm"] == arm
    assert summary["block_seed"] == seed and summary["evaluation_seed"] == evaluation_seed
    assert summary["counts"]["model_constructions"] == len(helpers.Agent.constructed) == 2
    learner, evaluator = helpers.Agent.constructed
    for agent, phase_seed, envs in ((learner, seed, fake_only[0]), (evaluator, evaluation_seed, fake_only[1])):
        assert agent.config.coordinator_batch_size == batch and agent.config.interruption_cost_c == gap
        assert agent.config.policy_interruption_mode == "d2" and agent.config.interruption_cost_c_Z == float("inf")
        assert agent.config.seed == phase_seed
        assert [env.seed for env in envs] == list(range(phase_seed, phase_seed + len(envs)))
        assert agent.constructor_rng[0] == helpers.random.Random(phase_seed).random()
        assert agent.constructor_rng[1] == np.random.RandomState(phase_seed).rand()
        gen = helpers.torch.Generator().manual_seed(phase_seed)
        assert agent.constructor_rng[2] == float(helpers.torch.rand((), generator=gen))
    assert learner is not evaluator and learner.updates == 5 and evaluator.updates == 0
    assert not evaluator.training and len(evaluator.inputs) == r.HORIZON
    assert summary["evaluation"]["after_update"] == 5 and not any(summary["evaluation_optimizer_calls"].values())
    for name in ("skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator"):
        for source, target in zip(getattr(learner, name).parameters(), getattr(evaluator, name).parameters()):
            assert helpers.torch.equal(source, target) and source.data_ptr() != target.data_ptr()
    np.testing.assert_allclose(factorial.arm_endpoint(summary), summary["evaluation"]["native_scores_J"])


def supplied(arm, seed, score):
    renewal, batch = factorial.ARMS[arm]
    evaluation_seed = factorial.BLOCKS[seed]
    result = helpers.completed(renewal, np.full(r.EVAL_LANES, score * r.HORIZON / r.N_UAVS))
    result.update(object_id=factorial.OBJECT_ID, card=factorial.CARD, factorial_arm=arm,
                  block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                  training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                  evaluation_lane_seeds=list(range(evaluation_seed, evaluation_seed + r.EVAL_LANES)))
    result["evaluation"]["lane_seeds"] = result["evaluation_lane_seeds"]
    result["optimizer_calls"].update(discoverer_actor=5, discoverer_critic=5)
    for phase, count, phase_seed in (("learner_config", r.TRAIN_LANES, seed),
                                     ("evaluation_config", r.EVAL_LANES, evaluation_seed)):
        result[phase] = r.config_snapshot(factorial.make_config(arm, [helpers.Env(0, phase_seed)] * count, phase_seed))
    return result


def full_inputs():
    return [supplied(arm, seed, score) for seed, scores in
            ((772003, (.2, .3, .25, .4)), (772103, (.5, .56, .48, .52)))
            for arm, score in zip(factorial.ARMS, scores)]


def test_block_contrasts_training_uncertainty_and_publication(monkeypatch, tmp_path):
    monkeypatch.setattr(r, "HORIZON", 500)
    monkeypatch.setattr(r, "EVAL_LANES", 32)
    inputs = full_inputs()
    result = factorial.assemble_blocks(inputs)
    assert result["status"] == "complete"
    expected = ({"SI1280": .1, "SI128": .05, "MI": .075, "MB": .125, "INT": .05, "PKG": .2},
                {"SI1280": -.04, "SI128": -.02, "MI": -.03, "MB": .05, "INT": -.02, "PKG": .02})
    for block, values in zip(result["blocks"], expected):
        for name, value in values.items():
            assert block["contrasts"][name]["value"] == pytest.approx(value)
    primary = result["primary"]
    assert primary["available_training_blocks"] == 2
    assert primary["mean"] == pytest.approx(.03)
    assert primary["sample_sd"] == pytest.approx(.14 / math.sqrt(2))
    assert primary["se"] == pytest.approx(.07)
    assert primary["working_model_95pct_interval"] == pytest.approx([.03 - 12.7062047361747 * .07,
                                                                    .03 + 12.7062047361747 * .07])
    paths = []
    for index, value in enumerate(inputs):
        path = tmp_path / f"synthetic_arm_{index}.json"
        path.write_text(json.dumps(value))
        paths.append(str(path))
    assert factorial.main(["reduce", "--summaries", *paths, "--output-root", str(tmp_path / "readout")]) == 0
    published = json.loads((tmp_path / "readout/summary.json").read_text())
    assert published["primary"] == primary and published["input_summaries"] == paths


@pytest.mark.parametrize("damage", ["missing_low", "missing_primary", "wrong_batch", "wrong_seed", "short_learning",
                                   "missing_U", "nonfinite", "wrong_scaling", "unexpected_gamma"])
def test_failure_limits_only_dependent_contrasts(damage):
    inputs = full_inputs()
    target = inputs[0]
    if damage == "missing_low": inputs.pop(0)
    elif damage == "missing_primary": inputs.pop(1)
    elif damage == "wrong_batch": target["evaluation_config"]["coordinator_batch_size"] = 1280
    elif damage == "wrong_seed": target["training_seed"] += 1
    elif damage == "short_learning": target["counts"]["update_stages"] = 4
    elif damage == "missing_U": target["evaluation"]["returns_U"] = None
    elif damage == "nonfinite": target["evaluation"]["native_scores_J"][0] = float("nan")
    elif damage == "wrong_scaling": target["evaluation"]["returns_U"][0] += 1
    else: target["learner_config"]["gamma"] = .2
    original = copy.deepcopy(inputs)
    result = factorial.assemble_blocks(inputs)
    assert result["status"] == "incomplete"
    primary = result["primary"]
    if damage == "missing_primary":
        assert primary["available_training_blocks"] == 1 and primary["mean"] == pytest.approx(-.04)
        assert primary["sample_sd"] is primary["se"] is primary["working_model_95pct_interval"] is None
        assert result["contrasts"]["SI128"]["available_training_blocks"] == 2
    else:
        assert primary["available_training_blocks"] == 2 and primary["mean"] == pytest.approx(.03)
        assert result["contrasts"]["SI128"]["available_training_blocks"] == 1
    assert json.dumps(inputs, sort_keys=True) == json.dumps(original, sort_keys=True)


def test_old_defaults_and_duplicate_training_block():
    assert inspect.signature(r.make_config).parameters["coordinator_batch_size"].default is None
    assert inspect.signature(r.main).parameters["renewal_batch"].default is False
    assert r.base_summary("D0")["cap_seconds"] == 3600
    assert r.base_summary("I")["cap_seconds"] == 18000
    low = r.make_config("I", [helpers.Env(0, 1)], 1)
    assert getattr(low, "coordinator_batch_size", 128) == 128
    assert r.make_config("I", [helpers.Env(0, 1)], 1, renewal_batch=True).coordinator_batch_size == 1280
    values = full_inputs()
    with pytest.raises(ValueError, match="duplicate"):
        factorial.assemble_blocks(values + [values[0]])
