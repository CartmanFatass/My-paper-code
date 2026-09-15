"""Bounded synthetic checks for the baseline x interruption runner; zero real learners or hosts."""
import copy
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
spec = importlib.util.spec_from_file_location("fsd_baseline_helpers", Path(__file__).parents[1] /
                                            "uav_individual_renewal_b01/test_learning.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
r = helpers.r
import run_fsd_baseline_interruption_b01 as baseline

fake_only = helpers.fake_only
SEED = 772203
EVAL_SEED = baseline.BLOCKS[SEED]


class PanelAgent(helpers.Agent):
    """The fake learner moves the coordinator/discriminator optimizers only when skills exist."""

    def update(self, **kwargs):
        if self.config.n_z == 1:
            # The counted wrappers sit on the optimizer instances; bypass them for the never-trained modules.
            saved = {name: getattr(self, name + "_optimizer").step for name in baseline.FLAT_ONLY_ZERO}
            for name in saved:
                getattr(self, name + "_optimizer").step = lambda: None
            try:
                return super().update(**kwargs)
            finally:
                for name, step in saved.items():
                    getattr(self, name + "_optimizer").step = step
        losses = super().update(**kwargs)
        self.coordinator_optimizer.step()
        return losses


@pytest.fixture(autouse=True)
def bind_fake_shared(monkeypatch, fake_only):
    monkeypatch.setattr(baseline, "shared", r)
    monkeypatch.setattr(r, "HMASDAgent", PanelAgent)
    monkeypatch.setattr(r, "PROCESS_START", r.time.perf_counter() - 1e7)


def run_fake_fit(monkeypatch, tmp_path, arm, seed=SEED):
    saved = baseline.evaluate_panel
    def evaluate(*args, **kwargs):
        before = helpers.rng_state()
        result = saved(*args, **kwargs)
        helpers.assert_rng_equal(before, helpers.rng_state())
        return result
    monkeypatch.setattr(baseline, "evaluate_panel", evaluate)
    out = tmp_path / f"{arm}_{seed}"
    assert baseline.main(["fit", "--arm", arm, "--seed", str(seed), "--output-root", str(out)]) == 0
    return json.loads((out / "summary.json").read_text()), json.loads((out / "manifest.json").read_text())


@pytest.mark.parametrize("arm", list(baseline.ARMS))
def test_fit_bindings_three_panels_and_rng(monkeypatch, tmp_path, fake_only, arm):
    summary, manifest = run_fake_fit(monkeypatch, tmp_path, arm)
    assert summary["factorial_arm"] == manifest["factorial_arm"] == arm and "panels" not in manifest
    assert summary["rollouts"] == 15 and summary["panel_rollouts"] == [5, 10, 15] and summary["cap_seconds"] is None
    assert summary["counts"]["model_constructions"] == len(helpers.Agent.constructed) == 2
    assert summary["counts"]["update_stages"] == 15 and summary["counts"]["training_episodes"] == r.TRAIN_LANES * 15
    rows = summary["training_rows"]
    assert [row["rollout_index"] for row in rows] == list(range(15))
    assert all(row["updated"] for row in rows) and "stage" not in rows[0]
    assert [p["panel_rollouts"] for p in summary["panels"]] == [p["after_update"] for p in summary["panels"]] == [5, 10, 15]
    assert summary["evaluation"] == summary["panels"][-1] and summary["evaluation"]["status"] == "complete"
    assert summary["counts"]["evaluation_episodes"] == 3 * r.EVAL_LANES
    assert summary["counts"]["evaluation_agent_step_batches"] == 3 * r.HORIZON
    learner, evaluator = helpers.Agent.constructed
    assert learner is not evaluator and learner.updates == 15 and evaluator.updates == 0 and not evaluator.training
    for agent, phase_seed in ((learner, SEED), (evaluator, EVAL_SEED)):
        config = agent.config
        assert config.seed == phase_seed
        if arm == "FLAT":
            assert config.policy_interruption_mode == "off" and config.n_Z == config.n_z == 1
            assert config.k == baseline.FLAT_K == 10 and config.disable_high_level_training
            assert config.disable_discriminator_training and config.disable_discriminator_rewards
            assert config.lambda_D == config.lambda_d == config.lambda_h == 0.
            assert getattr(config, "coordinator_batch_size", None) is None
        else:
            assert config.policy_interruption_mode == "d2" and config.interruption_cost_c_Z == float("inf")
            assert config.n_Z == config.n_z == 6 and config.k == config.skill_cap_k_max == config.team_cap_k_Z == 10
            assert config.coordinator_batch_size == 1280
            assert config.interruption_cost_c == (.25 if arm == "I1280" else float("inf"))
    # Environments: one training batch, one evaluator-construction batch, one fresh batch per panel.
    assert [len(batch) for batch in fake_only] == [r.TRAIN_LANES, r.EVAL_LANES, r.EVAL_LANES, r.EVAL_LANES, r.EVAL_LANES]
    for batch in fake_only[1:]:
        assert [env.seed for env in batch] == list(range(EVAL_SEED, EVAL_SEED + r.EVAL_LANES))
    for batch in fake_only[2:]:
        assert all(env.resets == 1 for env in batch)
    # One reset at the start and one at every rollout end; no other environment reset.
    assert all(env.resets == 15 + 1 for env in fake_only[0])
    assert learner.reset_calls.count(0) == 15
    # Panel worlds are identical across panels: the first evaluation input of each panel matches.
    firsts = [inp for inp in evaluator.inputs if inp[2].sum() == 0 and not inp[3].any()]
    assert len(firsts) == 3
    for later in firsts[1:]:
        np.testing.assert_array_equal(firsts[0][0], later[0])
        np.testing.assert_array_equal(firsts[0][1], later[1])
    for name in ("skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator"):
        for source, target in zip(getattr(learner, name).parameters(), getattr(evaluator, name).parameters()):
            assert helpers.torch.equal(source, target) and source.data_ptr() != target.data_ptr()
    if arm == "FLAT":
        assert all(summary["optimizer_calls"][k] == 0 for k in baseline.FLAT_ONLY_ZERO)
    else:
        assert summary["optimizer_calls"]["coordinator"] == 15
    assert summary["optimizer_calls"]["discoverer_actor"] == 15 and not any(summary["evaluation_optimizer_calls"].values())
    panels = baseline.arm_panels(summary)
    assert list(panels) == [5, 10, 15]
    np.testing.assert_allclose(panels[15], summary["evaluation"]["native_scores_J"])
    if arm == "FLAT":
        d1280 = baseline.arm_panels(run_fake_fit(monkeypatch, tmp_path, "D1280")[0]) and json.loads(
            (tmp_path / "D1280_772203" / "summary.json").read_text())
        differing = {k for k in set(summary["learner_config"]) | set(d1280["learner_config"])
                     if summary["learner_config"].get(k) != d1280["learner_config"].get(k)}
        assert differing <= baseline.PLANNED_CONFIG_DIFFERENCES, differing


def test_panel_leaves_learner_state_untouched(monkeypatch, tmp_path, fake_only):
    """A panel changes nothing on the learner: no events, no normalizer or parameter change, RNG restored."""
    out = tmp_path / "learner"
    out.mkdir()
    summary = r.base_summary("D0", training_seed=SEED, evaluation_seed=EVAL_SEED, object_id="X", card="Y", caps=None)
    summary.update(factorial_arm="D1280", panels=[], panel_rollouts=[5, 10, 15], rollouts=15)
    envs, learner, theta0, counters = baseline.build_learner("D1280", summary, out, SEED)
    evaluator = baseline.build_evaluator("D1280", summary, out, EVAL_SEED)
    learner.value_norm_coordinator.mean += 1.5  # a learner state the evaluator must copy, not share
    events, norms = list(learner.events), copy.deepcopy((learner.obs_norm, learner.state_norm,
                                                          learner.value_norm_coordinator, learner.value_norm_discoverer))
    parameters = [v.clone() for name in ("skill_coordinator", "skill_discoverer") for v in getattr(learner, name).parameters()]
    before = helpers.rng_state()
    baseline.evaluate_panel(learner, evaluator, summary, out, 5)
    helpers.assert_rng_equal(before, helpers.rng_state())
    assert learner.events == events and learner.training
    for old, new in zip(norms, (learner.obs_norm, learner.state_norm, learner.value_norm_coordinator, learner.value_norm_discoverer)):
        assert old.mean == new.mean and old.var == new.var and old.count == new.count
    for old, new in zip(parameters, [v for name in ("skill_coordinator", "skill_discoverer") for v in getattr(learner, name).parameters()]):
        assert helpers.torch.equal(old, new)
    assert evaluator.agent.value_norm_coordinator.mean == learner.value_norm_coordinator.mean
    assert evaluator.agent.value_norm_coordinator is not learner.value_norm_coordinator
    assert "clear" in evaluator.agent.events and summary["panels"][0]["status"] == "complete"


def supplied_summaries(monkeypatch, tmp_path, scores):
    """Fake complete fits for every arm and block, with designed panel scores J[arm][seed][rollout]."""
    template = {arm: run_fake_fit(monkeypatch, tmp_path, arm)[0] for arm in baseline.ARMS}
    summaries = []
    for seed, evaluation_seed in baseline.BLOCKS.items():
        for arm, base in template.items():
            s = copy.deepcopy(base)
            s.update(block_seed=seed, training_seed=seed, evaluation_seed=evaluation_seed,
                     training_lane_seeds=list(range(seed, seed + r.TRAIN_LANES)),
                     evaluation_lane_seeds=list(range(evaluation_seed, evaluation_seed + r.EVAL_LANES)))
            s["learner_config"]["seed"], s["evaluation_config"]["seed"] = seed, evaluation_seed
            for panel in s["panels"]:
                panel["lane_seeds"] = s["evaluation_lane_seeds"]
                value = scores[arm][seed][panel["panel_rollouts"]]
                panel["native_scores_J"] = [value] * r.EVAL_LANES
                panel["returns_U"] = [value * r.HORIZON / r.N_UAVS] * r.EVAL_LANES
            s["evaluation"] = s["panels"][-1]
            summaries.append(s)
    return summaries


def designed_scores(si1280_15, h_15):
    scores = {arm: {} for arm in baseline.ARMS}
    for i, seed in enumerate(baseline.BLOCKS):
        flat = .30 + .01 * i
        for rollout in (5, 10, 15):
            scale = rollout / 15
            scores["FLAT"][seed] = scores["FLAT"].get(seed, {})
            scores["D1280"][seed] = scores["D1280"].get(seed, {})
            scores["I1280"][seed] = scores["I1280"].get(seed, {})
            scores["FLAT"][seed][rollout] = flat
            scores["D1280"][seed][rollout] = flat + h_15[i] * scale
            scores["I1280"][seed][rollout] = flat + h_15[i] * scale + si1280_15[i] * scale
    return scores


@pytest.mark.parametrize("si,importance,uncertainty,inside", [
    ([.08, .09, .10, .07], "locally_substantial_positive", "interval_excludes_zero", False),
    ([.01, -.01, .005, .0], "small_signed", "interval_includes_zero", True),
    ([-.08, -.09, -.10, -.07], "adverse", "interval_excludes_zero", False),
    ([.12, -.05, .09, .0], "small_signed", "interval_includes_zero", False),
])
def test_reduce_primary_readings_gaps_and_accumulation(monkeypatch, tmp_path, fake_only, si, importance, uncertainty, inside):
    h = [.02, -.01, .03, .0]
    summaries = supplied_summaries(monkeypatch, tmp_path, designed_scores(si, h))
    historical = [-.02644030, .08464985]
    result = baseline.assemble_blocks(summaries, historical)
    assert result["status"] == "complete" and len(result["blocks"]) == 4
    primary = result["primary"]
    assert primary["name"] == "SI1280_15" and primary["mei_J"] == .05 and primary["available_training_blocks"] == 4
    assert primary["mean"] == pytest.approx(np.mean(si))
    assert primary["importance_reading"] == importance and primary["uncertainty_reading"] == uncertainty
    assert primary["interval_inside_mei"] is inside
    se = np.std(si, ddof=1) / math.sqrt(4)
    assert primary["se"] == pytest.approx(se)
    assert primary["working_model_95pct_interval"] == pytest.approx([np.mean(si) - 3.1824 * se, np.mean(si) + 3.1824 * se])
    assert result["contrasts"]["GAP_D"]["15"]["mean"] == pytest.approx(np.mean(h))
    assert result["contrasts"]["GAP_I"]["15"]["mean"] == pytest.approx(np.mean(h) + np.mean(si))
    assert result["contrasts"]["SI1280"]["5"]["mean"] == pytest.approx(np.mean(si) / 3)
    assert "not section 11.7 headroom" in result["contrast_meaning"]["GAP_D"]
    pooled = result["rollout5_accumulation"]
    values = [v / 3 for v in si] + historical
    assert pooled["available_training_blocks"] == 6 and pooled["planned_training_blocks"] == 6
    assert pooled["mean"] == pytest.approx(np.mean(values))
    assert pooled["working_model_95pct_interval"][1] - pooled["mean"] == pytest.approx(
        2.5706 * np.std(values, ddof=1) / math.sqrt(6))
    assert pooled["new_blocks"]["available_training_blocks"] == 4 and pooled["historical_blocks"]["mean"] == pytest.approx(np.mean(historical))
    block = result["blocks"][0]
    assert set(block["arms"]) == set(baseline.ARMS) and not block["missing_or_invalid_arms"]
    assert block["contrasts"]["SI1280"]["by_rollout"]["15"]["value"] == pytest.approx(si[0])


@pytest.mark.parametrize("damage", ["flat_coordinator_trained", "unplanned_config", "missing_panel", "wrong_rollouts"])
def test_damaged_fit_limits_only_dependent_contrasts(monkeypatch, tmp_path, fake_only, damage):
    summaries = supplied_summaries(monkeypatch, tmp_path, designed_scores([.06] * 4, [.02] * 4))
    victim = next(s for s in summaries if s["factorial_arm"] == "FLAT" and s["block_seed"] == SEED)
    if damage == "flat_coordinator_trained":
        victim["optimizer_calls"]["coordinator"] = 1
    elif damage == "unplanned_config":
        victim["learner_config"]["gamma"] = .5
    elif damage == "missing_panel":
        victim["panels"].pop(1)
    else:
        victim["rollouts"] = 10
    result = baseline.assemble_blocks(summaries)
    block = result["blocks"][0]
    assert result["status"] == "incomplete" and "FLAT" in block["missing_or_invalid_arms"] or damage == "unplanned_config"
    assert block["contrasts"]["SI1280"]["status"] == "complete"
    assert block["contrasts"]["GAP_D"]["status"] == block["contrasts"]["GAP_I"]["status"] == "incomplete"
    assert result["primary"]["available_training_blocks"] == 4
    assert result["contrasts"]["GAP_D"]["15"]["available_training_blocks"] == 3
    assert result["rollout5_accumulation"]["available_training_blocks"] == 4


def test_reduce_reads_historical_factorial_summary(monkeypatch, tmp_path, fake_only):
    summaries = supplied_summaries(monkeypatch, tmp_path, designed_scores([.06] * 4, [.02] * 4))
    paths = []
    for i, s in enumerate(summaries):
        path = tmp_path / f"s{i}.json"
        path.write_text(json.dumps(s), encoding="utf-8")
        paths.append(str(path))
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"object_id": "FSD_INTERRUPTION_BATCH_B01", "blocks": [
        {"contrasts": {"SI1280": {"value": -.02644030}}}, {"contrasts": {"SI1280": {"value": .08464985}}}]}))
    out = tmp_path / "reduce"
    assert baseline.main(["reduce", "--summaries", *paths, "--historical-factorial-summary", str(old),
                          "--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["rollout5_accumulation"]["historical_blocks"]["mean"] == pytest.approx(np.mean([-.02644030, .08464985]))
    assert result["rollout5_accumulation"]["available_training_blocks"] == 6
    old.write_text(json.dumps({"object_id": "OTHER", "blocks": []}))
    with pytest.raises(ValueError):
        baseline.main(["reduce", "--summaries", *paths, "--historical-factorial-summary", str(old),
                       "--output-root", str(out)])


def test_collector_copy_matches_frozen_collector(monkeypatch, tmp_path, fake_only):
    """Five rollouts of the parametrised copy reproduce the frozen B01 collector's rows and storage."""
    outputs = []
    for label, collector in (("frozen", lambda *a: r.collect_training(*a)),
                             ("copy", lambda *a: baseline.collect_training(*a, rollouts=5))):
        helpers.Agent.constructed = []
        out = tmp_path / label
        out.mkdir()
        summary = r.base_summary("D0", training_seed=SEED, evaluation_seed=EVAL_SEED, object_id="X", card="Y", caps=None)
        envs, agent, theta0, counters = baseline.build_learner("D1280", summary, out, SEED)
        collector(envs, agent, theta0, counters, summary, out)
        outputs.append((summary["training_rows"], summary["counts"], agent.stored, agent.events,
                        (out / "training.jsonl").read_text()))
    frozen, copy_ = outputs
    assert frozen[0] == copy_[0] and frozen[1] == copy_[1] and frozen[3] == copy_[3] and frozen[4] == copy_[4]
    assert frozen[0][0]["segments"]["agent"]["count"] > 0  # the D arms keep their renewal metrics
    assert len(frozen[2]) == len(copy_[2]) == 5 * r.HORIZON
    for a, b in zip(frozen[2], copy_[2]):
        for key in ("states", "next_states", "observations", "next_observations", "actions", "rewards", "dones"):
            np.testing.assert_array_equal(a[key], b[key])


def test_flat_rows_carry_no_renewal_metrics(monkeypatch, tmp_path, fake_only):
    class OffAgent(PanelAgent):
        """The real agent has no D2 metrics on the `off` route; the fake mirrors that."""

        def _reset_metrics(self):
            super()._reset_metrics()
            if self.config.policy_interruption_mode == "off":
                self.d2_metrics = None

        def store_transition_batch(self, **kwargs):
            if self.d2_metrics is None:
                self.d2_metrics = {"segment_lengths_agent": [], "segment_lengths_team": []}
                try:
                    super().store_transition_batch(**kwargs)
                finally:
                    self.d2_metrics = None
            else:
                super().store_transition_batch(**kwargs)
    monkeypatch.setattr(r, "HMASDAgent", OffAgent)
    summary, _ = run_fake_fit(monkeypatch, tmp_path, "FLAT")
    assert all(row["d2_metrics"] is None and row["segments"] is None for row in summary["training_rows"])
    assert all(panel["d2_metrics"] is None for panel in summary["panels"])
    assert list(baseline.arm_panels(summary)) == [5, 10, 15]
