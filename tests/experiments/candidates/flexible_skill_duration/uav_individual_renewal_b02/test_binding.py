"""B02 binding checks using the existing fake-only UAV learning seams."""
import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
spec = importlib.util.spec_from_file_location("uav_b01_helpers", Path(__file__).parents[1] /
                                            "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
r = helpers.r
import run_fsd_uav_individual_renewal_b02 as b02

fake_only = helpers.fake_only
BINDING = dict(training_seed=770603, evaluation_seed=780603, object_id=b02.OBJECT_ID, card=b02.CARD)


@pytest.fixture(autouse=True)
def shared_fake_module(monkeypatch, fake_only):
    # The helper loads the identical shared source under its isolated test name.
    monkeypatch.setattr(b02, "shared", r)


def test_complete_b02_consumers_and_later_b01_defaults(monkeypatch, tmp_path, fake_only):
    defaults = (r.TRAIN_SEED, r.EVAL_SEED, r.OBJECT_ID, r.CARD)
    seeds, rng_checks = [], []
    original_seed, original_eval = r.seed_rng, r.final_evaluation
    def seed(value):
        seeds.append(value)
        original_seed(value)
    def evaluate(*args, **kwargs):
        before = helpers.rng_state()
        result = original_eval(*args, **kwargs)
        helpers.assert_rng_equal(before, helpers.rng_state())
        rng_checks.append(kwargs["evaluation_seed"])
        return result
    monkeypatch.setattr(r, "seed_rng", seed)
    monkeypatch.setattr(r, "final_evaluation", evaluate)
    for entry, name, train, evaluation, object_id, card in (
            (b02.main, "B02", 770603, 780603, b02.OBJECT_ID, b02.CARD),
            (r.main, "B01_after_B02", 770503, 780503, r.OBJECT_ID, r.CARD)):
        for arm in ("D0", "I"):
            out = tmp_path / name / arm
            args = helpers.argv(arm, out)
            if arm == "I": args += ["--d0-summary", str(tmp_path / name / "D0/summary.json")]
            assert entry(args) == 0
            s = json.loads((out / "summary.json").read_text())
            manifest = json.loads((out / "manifest.json").read_text())
            assert s["object_id"] == manifest["object_id"] == object_id
            assert s["card"] == manifest["card"] == card
            assert s["training_seed"] == train and s["evaluation_seed"] == evaluation
            assert s["training_lane_seeds"] == list(range(train, train + r.TRAIN_LANES))
            assert s["evaluation_lane_seeds"] == list(range(evaluation, evaluation + r.EVAL_LANES))
            assert s["evaluation"]["lane_seeds"] == s["evaluation_lane_seeds"]
            assert seeds[-2:] == [train, evaluation] and rng_checks[-1] == evaluation
            learner, evaluator = helpers.Agent.constructed[-2:]
            for agent, envs, key in ((learner, fake_only[-2], train), (evaluator, fake_only[-1], evaluation)):
                assert agent.config.seed == key
                assert [env.seed for env in envs] == list(range(key, key + len(envs)))
                assert agent.config.interruption_cost_c == (.25 if arm == "I" else float("inf"))
                assert agent.config.interruption_cost_c_Z == float("inf")
                # Constructor draws observe the selected process seed before reset/rollout.
                assert agent.constructor_rng[0] == helpers.random.Random(key).random()
                assert agent.constructor_rng[1] == np.random.RandomState(key).rand()
                gen = helpers.torch.Generator().manual_seed(key)
                assert agent.constructor_rng[2] == float(helpers.torch.rand((), generator=gen))
            assert s["learner_config"]["seed"] == train and s["evaluation_config"]["seed"] == evaluation
            assert s["counts"]["update_stages"] == 5 and s["evaluation"]["after_update"] == 5
            assert s["counts"]["training_transitions"] == r.TRAIN_LANES * r.HORIZON * 5
            assert not any(s["evaluation_optimizer_calls"].values())
            np.testing.assert_allclose(s["evaluation"]["native_scores_J"],
                                       6 * np.array(s["evaluation"]["returns_U"]) / r.HORIZON)
            if arm == "I":
                assert s["pair"]["status"] == "complete"
                assert s["pair"]["card_reading"] == "small_or_resolution_limited"
                assert s["pair"]["i_minus_d0"]["mean"] == 0
        assert (r.TRAIN_SEED, r.EVAL_SEED, r.OBJECT_ID, r.CARD) == defaults
    assert seeds == [770603, 780603] * 2 + [770503, 780503] * 2


def bound_completed(arm):
    s = helpers.completed(arm, [1., 2., 3.])
    s.update(object_id=b02.OBJECT_ID, card=b02.CARD, training_seed=770603, evaluation_seed=780603,
             training_lane_seeds=list(range(770603, 770603 + r.TRAIN_LANES)),
             evaluation_lane_seeds=list(range(780603, 780603 + r.EVAL_LANES)))
    s["learner_config"]["seed"] = 770603
    s["evaluation_config"]["seed"] = 780603
    s["evaluation"]["lane_seeds"] = s["evaluation_lane_seeds"]
    return s


@pytest.mark.parametrize("damage", ["old_object", "both_old_cards", "training_seed", "evaluation_seed",
                                   "learner_seed", "evaluator_seed", "endpoint_lanes"])
def test_pair_uses_selected_binding(damage):
    treatment, control = bound_completed("I"), bound_completed("D0")
    good = r.assemble_pair(treatment, control, **BINDING)
    control["launch_sha"] = "another-document-descendant"
    assert r.assemble_pair(treatment, control, **BINDING) == good
    if damage == "old_object": control["object_id"] = r.OBJECT_ID
    elif damage == "both_old_cards": treatment["card"] = control["card"] = r.CARD
    elif damage == "training_seed": control["training_seed"] = r.TRAIN_SEED
    elif damage == "evaluation_seed": control["evaluation_seed"] = r.EVAL_SEED
    elif damage == "learner_seed": control["learner_config"]["seed"] = r.TRAIN_SEED
    elif damage == "evaluator_seed": control["evaluation_config"]["seed"] = r.EVAL_SEED
    else: control["evaluation"]["lane_seeds"] = list(range(r.EVAL_SEED, r.EVAL_SEED + r.EVAL_LANES))
    with pytest.raises(ValueError):
        r.assemble_pair(treatment, control, **BINDING)


def test_old_b01_companion_keeps_own_b02_endpoint_without_pair(tmp_path):
    old = helpers.completed("D0", [1., 2., 3.])
    original = copy.deepcopy(old)
    path = tmp_path / "old_b01.json"
    path.write_text(json.dumps(old))
    assert b02.main(helpers.argv("I", tmp_path / "B02", "--d0-summary", path)) == 1
    result = json.loads((tmp_path / "B02/summary.json").read_text())
    assert result["status"] == result["evaluation"]["status"] == "complete"
    assert result["object_id"] == b02.OBJECT_ID and result["training_seed"] == 770603
    assert result["pair"]["status"] == "incomplete" and "card_reading" not in result["pair"]
    assert json.loads(path.read_text()) == original
