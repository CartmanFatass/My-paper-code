"""A real tiny-host B13 fit and this object's probe of its own checkpoint.

Six lanes, thirty-step episodes, two rollouts, the real Scenario 1 environment and the real D
agent: one B13 `UNIFORM` fit runs through the frozen runner, saves its weights and its sidecar,
and this object's `probe` then rebuilds that fit, loads the checkpoint and runs the faithful-load
rerun and the four declared panels on the same host.  It is the one check that the faithful-load
rerun really reproduces the fit's own `uniform_every_10` panel bit for bit when the panel and the
fit ran on the same host; the production probe makes the same claim about wsl_4070, where the six
B13 fits ran and where their checkpoints are.

Technical checks, no result: nothing here asserts the direction or the size of any measured
quantity.  Kept apart from the synthetic tests in `test_label_law_deployment.py`.
"""
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_label_bandit_b13 as b13  # noqa: E402
import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_law_deployment_b14 as b14  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402

SEED = sorted(b14.BLOCKS)[0]
EVALUATION_SEED = b14.BLOCKS[SEED]
ARM = b13.UNIFORM_ARM  # the primary group's arm: its estimator ran passively during the fit
LANES, HORIZON, ROLLOUTS = 6, 30, 2
N_AGENTS, N_LABELS = 6, b14.N_LABELS
ADMISSION = {"sha": "tiny-technical-check", "command_sha256": "x"}


@contextmanager
def shrunken():
    """The tiny host, applied to the shared module and to B13's own rollout schedule."""
    shared = b01.shared
    saved = {"TRAIN_LANES": shared.TRAIN_LANES, "EVAL_LANES": shared.EVAL_LANES,
             "HORIZON": shared.HORIZON, "PROCESS_START": shared.PROCESS_START}
    theirs = {"ROLLOUTS": b13.ROLLOUTS, "PANEL_ROLLOUTS": b13.PANEL_ROLLOUTS,
              "LATE_PANELS": b13.LATE_PANELS}
    shared.TRAIN_LANES = shared.EVAL_LANES = LANES
    shared.HORIZON = HORIZON
    shared.PROCESS_START = shared.time.perf_counter()
    b13.ROLLOUTS, b13.PANEL_ROLLOUTS = ROLLOUTS, tuple(range(1, ROLLOUTS + 1))
    b13.LATE_PANELS = b13.PANEL_ROLLOUTS
    try:
        yield shared
    finally:
        for name, value in saved.items():
            setattr(shared, name, value)
        for name, value in theirs.items():
            setattr(b13, name, value)


def globals_are_restored():
    """Every table and global this object binds for the duration of its four panels."""
    return {
        "execution_rule": b08.ExecutionRule is not b14.DeploymentRule,
        "label_generator": b08.label_generator is b14._orig_label_generator,
        "random_rules": all(name not in b08.RANDOM_RULES for name in b14.PANEL_RULES),
        "rule_definitions": all(name not in b08.RULE_DEFINITIONS for name in b14.PANEL_RULES),
        "law": b14.CURRENT["law"] is None}


@pytest.fixture(scope="module")
def tiny_probe(tmp_path_factory):
    """One tiny B13 fit, then this object's probe of its own checkpoint. Run once."""
    captured = {}
    with shrunken():
        fit_root = tmp_path_factory.mktemp("b13_fit")
        assert b13.run_fit(ARM, SEED, fit_root, admission=ADMISSION) == 0
        captured["fit_root"] = fit_root
        captured["fit"] = json.loads((fit_root / "summary.json").read_text(encoding="utf-8"))

        learner, evaluator = b01.build_learner, b01.build_evaluator

        def learner_spy(arm, summary, out, training_seed):
            result = learner(arm, summary, out, training_seed)
            captured["learner"] = result[1]
            captured["learner_steps"] = optimizer_steps(result[1])
            return result

        def evaluator_spy(arm, summary, out, evaluation_seed):
            result = evaluator(arm, summary, out, evaluation_seed)
            captured["evaluator"] = result
            captured["evaluator_steps"] = optimizer_steps(result.agent)
            return result

        b01.build_learner, b01.build_evaluator = learner_spy, evaluator_spy
        try:
            out = tmp_path_factory.mktemp("b14_probe")
            captured["status"] = b14.run_probe(fit_root, out, launch_sha="tiny-technical-check")
        finally:
            b01.build_learner, b01.build_evaluator = learner, evaluator
        captured["out"] = out
        captured["summary"] = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        captured["restored"] = globals_are_restored()
    return captured


def optimizer_steps(agent):
    """The `step` callables of one agent's optimizers, as they are before any guard is applied."""
    return {name: getattr(agent, f"{name}_optimizer").step for name in b01.shared.NETWORKS
            if getattr(agent, f"{name}_optimizer", None) is not None}


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def test_the_probe_completes_on_the_fits_own_construction_and_checkpoint(tiny_probe):
    summary = tiny_probe["summary"]
    assert tiny_probe["status"] == 0
    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == b14.OBJECT_ID and summary["card"] == b14.CARD
    assert summary["command"] == "probe"
    assert summary["checkpoint_arm"] == ARM and summary["primary_group"] is True
    assert summary["block_seed"] == SEED and summary["evaluation_seed"] == EVALUATION_SEED
    assert summary["fit"]["object_id"] == b13.OBJECT_ID
    assert summary["fit"]["launch_sha"] == tiny_probe["fit"]["launch_sha"]
    # the construction is the fit's own, including B13's one declared difference
    assert summary["learner_config_differences_from_the_fit"] == {}
    assert summary["evaluation_config_differences_from_the_fit"] == {}
    assert summary["declared_config_difference"]["field"] == b13.DECLARED_FIELD
    assert summary["declared_config_difference"]["probe"] is True
    assert summary["declared_config_difference"]["fit"] is True
    assert summary["coordinator_training_mode"] is False


def test_the_faithful_load_reproduces_the_fits_own_uniform_panel_on_this_host(tiny_probe):
    """The rerun and the fit's recorded panel, by exact equality of the native world scores."""
    summary, fit = tiny_probe["summary"], tiny_probe["fit"]
    faithful = summary["faithful_load"]
    assert faithful["faithful_load"] is True
    assert faithful["first_differing_world"] is None
    assert faithful["max_abs_difference"] == 0.
    assert faithful["reference_rule"] == b14.UNIFORM_RULE
    assert faithful["reference_panel_rollouts"] == ROLLOUTS
    recorded = [entry for entry in fit["panel_runs"]
                if entry["rule"] == b14.UNIFORM_RULE
                and entry["panel_rollouts"] == ROLLOUTS][0]
    assert faithful["rerun_J_mean"] == recorded["J_mean"]
    assert faithful["worlds"] == faithful["reference_worlds"] == LANES
    assert summary["reference_panel"]["J_mean"] == recorded["J_mean"]


def test_the_four_panels_run_on_the_same_worlds_under_four_distinct_label_streams(tiny_probe):
    summary = tiny_probe["summary"]
    scores = summary["J_world_scores"]
    assert sorted(scores) == sorted(b14.PANEL_RULES)
    assert {len(value) for value in scores.values()} == {LANES}
    assert all(np.isfinite(value).all() for value in scores.values())
    # four streams, four different panels; the two uniform replicates differ from each other
    assert scores[b14.panel_rule(b14.UNIFORM_RULE, "a")] != scores[
        b14.panel_rule(b14.UNIFORM_RULE, "b")]
    assert scores[b14.panel_rule(b14.LAW_RULE, "a")] != scores[
        b14.panel_rule(b14.LAW_RULE, "b")]
    for name in b14.PANEL_RULES:
        record = summary["rules_measured"][name]
        base, replicate = b14.rule_parts(name)
        assert record["base_rule"] == base and record["replicate"] == replicate
        assert record["random_labels"]["generator"] == b14.GENERATOR_DERIVATION
        assert record["random_labels"]["replicate_index"] == b14.REPLICATES.index(replicate)
        assert sum(record["agent_label_histogram"]) == LANES * HORIZON * N_AGENTS
        assert record["decision_positions"] == len(
            record["decision_step_indices"]) * LANES * N_AGENTS
        if base == b14.LAW_RULE:
            assert record["law"] == summary["q"]
            assert record["law_source"] == "b13_softmax_z"
        else:
            assert record["law"] is None and record["law_source"] == "uniform"
    # the law is the fit's own frozen final estimate through B13's own law
    law, _source = b13.label_law(b14.FrozenEstimate(summary["estimate"]["z"]), b13.BANDIT_ARM)
    assert summary["q"] == law.tolist()
    assert summary["estimate"]["rollout"] == ROLLOUTS


def test_the_four_panels_share_the_frozen_decision_cadence(tiny_probe):
    summary, fit = tiny_probe["summary"], tiny_probe["fit"]
    assert summary["decision_boundaries_identical"] is True
    indices = {name: summary["rules_measured"][name]["decision_step_indices"]
               for name in b14.PANEL_RULES}
    assert len({tuple(value) for value in indices.values()}) == 1
    assert indices[b14.PANEL_RULES[0]] == list(range(0, HORIZON, b13.COMMITMENT_CAP))
    # and they are the cadence the fit's own panel ran at
    recorded = [entry for entry in fit["panel_runs"]
                if entry["rule"] == b14.UNIFORM_RULE
                and entry["panel_rollouts"] == ROLLOUTS][0]
    assert set(summary["decision_steps"].values()) == {recorded["decision_steps"]}


def test_the_probe_takes_no_optimizer_step_and_leaves_the_weights_untouched(tiny_probe):
    summary = tiny_probe["summary"]
    assert summary["optimizer_steps"] == 0
    assert set(summary["optimizer_calls"].values()) == {0}
    for calls in summary["evaluator_optimizer_calls"].values():
        assert set(calls.values()) == {0}
    digest = b08.file_sha256(tiny_probe["fit_root"] / b14.WEIGHTS_NAME)
    assert summary["weights_sha256_before"] == summary["weights_sha256_after"] == digest
    assert summary["weights_unchanged"] is True
    assert summary["weights_record"]["sidecar_record"]["sha256"] == digest
    assert tiny_probe["fit"]["final_weights"]["sha256"] == digest
    # the guard was taken off both agents again: no optimizer is left with the raising step, and
    # each one carries the callable it carried before the probe (the learner's frozen counter is
    # an object and compares by identity; a plain `Adam.step` is a bound method and by equality)
    for agent, steps in ((tiny_probe["learner"], tiny_probe["learner_steps"]),
                         (tiny_probe["evaluator"].agent, tiny_probe["evaluator_steps"])):
        for name, original in steps.items():
            step = getattr(agent, f"{name}_optimizer").step
            assert getattr(step, "__name__", "") != "refuse"
            assert step == original
    assert all(counter.count == 0 for counter in tiny_probe["learner_steps"].values())


def test_every_wrapper_and_module_global_is_restored_after_the_probe(tiny_probe):
    assert tiny_probe["restored"] == {name: True for name in tiny_probe["restored"]}
    assert "_batched_assign_skills" not in tiny_probe["evaluator"].agent.__dict__
    assert "_batched_assign_skills" not in tiny_probe["learner"].__dict__
    assert "update" not in tiny_probe["learner"].__dict__
    assert b13.CURRENT["arm"] is None and b13.CURRENT["agent"] is None


def test_the_share_check_is_recorded_for_both_law_panels(tiny_probe):
    """The intermediate check is recorded, never raised; the tiny host's 108 draws prove nothing."""
    summary = tiny_probe["summary"]
    assert sorted(summary["share_checks"]) == sorted(b14.LAW_PANELS)
    for name, check in summary["share_checks"].items():
        assert check["q"] == summary["q"]
        assert check["max_q"] == max(summary["q"])
        assert isinstance(check["within_tolerance"], bool)
        assert check["tolerance"] == b14.SHARE_TOLERANCE
        assert sum(check["executed_label_shares"]) == pytest.approx(1.)


def test_this_objects_own_readers_read_its_own_tiny_probe(tiny_probe):
    row = b14.probe_row(tiny_probe["summary"])
    assert row["block_seed"] == SEED and row["checkpoint_arm"] == ARM
    assert row["worlds"] == LANES and row["faithful_load"] is True
    reading = b14.checkpoint_reading(row)
    assert reading["G"] == pytest.approx(
        (reading["G_by_replicate"]["a"] + reading["G_by_replicate"]["b"]) / 2.)
    first = np.asarray(row["J_world_scores"][b14.panel_rule(b14.LAW_RULE, "a")])
    second = np.asarray(row["J_world_scores"][b14.panel_rule(b14.UNIFORM_RULE, "a")])
    assert reading["G_by_replicate"]["a"] == pytest.approx(float((first - second).mean()))
    assert reading["G_paired_by_replicate"]["a"]["worlds"] == LANES
    assert reading["replicate_difference"] >= 0.
    result = b14.reduce_inputs([tiny_probe["summary"]])
    assert result["status"] == "incomplete" and result["checkpoints_read"] == 1
    assert result["invalid_probes"] == {}
    assert result["groups"][ARM]["checkpoints_read"] == 1
    assert result["groups"][ARM]["G_by_block"][str(SEED)] == pytest.approx(reading["G"])


# ---------------------------------------------------------------------------
# the failure path, on the same real checkpoint
# ---------------------------------------------------------------------------


def test_a_failed_faithful_load_stops_the_probe_before_any_rule_panel(tiny_probe, tmp_path,
                                                                      monkeypatch):
    """The fit's recorded panel is perturbed by one world, so the rerun cannot reproduce it."""
    original = b14.fit_reference_panel

    def perturbed(summary):
        entry, frozen = original(summary)
        scores = list(entry["J_world_scores"])
        scores[1] = scores[1] + .25
        return dict(entry, J_world_scores=scores), frozen

    monkeypatch.setattr(b14, "fit_reference_panel", perturbed)
    out = tmp_path / "failed"
    with shrunken():
        status = b14.run_probe(tiny_probe["fit_root"], out, launch_sha="tiny-technical-check")
    assert status == 1
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "failed_faithful_load"
    assert "do not reproduce the fit's own" in summary["failure"]
    faithful = summary["faithful_load"]
    assert faithful["faithful_load"] is False
    assert faithful["first_differing_world"] == 1
    assert faithful["max_abs_difference"] == pytest.approx(.25)
    assert faithful["rerun_J_mean"] is None
    # no rule panel ran and none is recorded
    assert summary["rules_measured"] is None and summary["J_by_rule"] is None
    assert summary.get("share_checks") is None
    assert globals_are_restored() == {"execution_rule": True, "label_generator": True,
                                      "random_rules": True, "rule_definitions": True,
                                      "law": True}
    assert b09.b08.ExecutionRule is not b14.DeploymentRule
    with pytest.raises(ValueError, match="incomplete probe"):
        b14.probe_row(summary)
