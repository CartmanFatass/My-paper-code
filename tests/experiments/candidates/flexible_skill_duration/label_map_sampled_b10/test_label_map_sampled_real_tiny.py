"""Real tiny-host executions of the sampled-label-map probe.

Two lanes, twenty-step episodes, the real Scenario 1 environment and the real D agent, through the
frozen runner's own learner construction, evaluator construction and evaluation panels; then B08's
real checkpoint, B08's real `load_model`, B09's real constant-label rules on the real D2 route, and
this object's action noise on the real diagonal-Gaussian head. The tiny fit and the tiny harness are
B08's own test fixtures, loaded by path, because this object probes B08's checkpoints and is read
against B09's panels, and all three must be checked against one panel and not against copies of it.
Technical checks, no result: nothing here asserts the direction or the size of any measured
quantity.
"""
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_label_map_sampled_b08_tiny",
    Path(__file__).parents[1] / "label_content_b08/test_label_content_real_tiny.py")
b08tiny = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b08tiny)

import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402
import run_fsd_label_map_sampled_b10 as b10  # noqa: E402

shrunken = b08tiny.shrunken
build_harness = b08tiny.build_harness
point_at_the_tiny_fit = b08tiny.point_at_the_tiny_fit
comparable_metrics = b08tiny.comparable_metrics
SEED, EVALUATION_SEED = b08tiny.SEED, b08tiny.EVALUATION_SEED
LANES, HORIZON = b08tiny.LANES, b08tiny.HORIZON
N_UAVS, N_z, SKILL_PERIOD = b08tiny.N_UAVS, b08tiny.N_z, b08tiny.SKILL_PERIOD
ROLLOUTS, ADMISSION = b08tiny.ROLLOUTS, b08tiny.ADMISSION
PANEL_ROWS = HORIZON * LANES * N_UAVS  # executed (step, lane, agent) positions of one panel


@pytest.fixture
def tiny():
    with shrunken() as shared:
        yield shared


@pytest.fixture(scope="module")
def tiny_fit(tmp_path_factory):
    """B08's own tiny fit, run once: its summary, its output root and its checkpoint."""
    out = tmp_path_factory.mktemp("label_map_sampled_fit")
    with shrunken():
        assert b08.run_fit(b08.SAVE_ARM, SEED, out, admission=ADMISSION) == 0
    return json.loads((out / "summary.json").read_text()), out


@pytest.fixture
def harness(tmp_path, tiny, tiny_fit):
    """B08's probe harness: its learner with the checkpoint loaded, and its evaluator."""
    _fit_summary, fit_out = tiny_fit
    summary, learner, evaluator = build_harness(tmp_path / "harness",
                                                fit_out / b08.WEIGHTS_NAME)
    return summary, learner, evaluator, tmp_path / "harness"


@pytest.fixture
def prepared(harness):
    """The harness after one `as_trained` panel, which is what puts the loaded weights on the
    evaluator: the baseline panel record and the policy's own action standard deviation."""
    summary, learner, evaluator, out = harness
    with b09.bound_rules():
        baseline = b10.run_rule_panel("as_trained", learner, evaluator, summary, out, 0,
                                      evaluation_seed=EVALUATION_SEED)
    standard_deviation, _note = b08.action_standard_deviation(
        evaluator.agent.skill_discoverer.actor)
    return harness, baseline, standard_deviation


def sampled_panel(harness, name, index, standard_deviation):
    """One of this object's sampled panels, through B09's binding, as the probe runs it."""
    summary, learner, evaluator, out = harness
    with b09.bound_rules():
        return b10.run_rule_panel(name, learner, evaluator, summary, out, index,
                                  evaluation_seed=EVALUATION_SEED,
                                  standard_deviation=standard_deviation)


def tables_are_b08s():
    """B08's rule tables, after a run: B09's binding is off and nothing of B09's is left."""
    return (b08.ExecutionRule is not b09.MapExecutionRule
            and all(name not in b08.RULE_DEFINITIONS for name in b09.MAP_RULES)
            and b09.FROZEN_RULE not in b08.RANDOM_RULES
            and sorted(b08.RULE_DEFINITIONS) == sorted(b08.RULES))


def nothing_is_attached(agent):
    """Every wrapper and hook of one panel is off the evaluator agent instance again."""
    return ("_batched_select_action" not in agent.__dict__
            and "_batched_assign_skills" not in agent.__dict__
            and agent.skill_discoverer._forward_hooks == {}
            and (agent.d2_k_max, agent.d2_k_Z) == b08.ARM_CAPS)


def parameter_digest(agent):
    """A digest of every weight and running statistic an update could have moved."""
    digest = hashlib.sha256()
    modules = [("skill_coordinator", agent.skill_coordinator),
               ("skill_discoverer", agent.skill_discoverer)]
    for name in ("value_norm_coordinator", "value_norm_discoverer", "team_discriminator",
                 "individual_discriminator"):
        module = getattr(agent, name, None)
        if module is not None:
            modules.append((name, module))
    for name, module in modules:
        digest.update(name.encode("utf-8"))
        if hasattr(module, "state_dict"):  # the networks
            for key, tensor in sorted(module.state_dict().items()):
                digest.update(key.encode("utf-8"))
                digest.update(np.ascontiguousarray(tensor.detach().cpu().numpy()).tobytes())
            continue
        for key in ("mean", "var", "count"):  # the ValueNorm running statistics
            digest.update(key.encode("utf-8"))
            digest.update(np.ascontiguousarray(
                np.asarray(getattr(module, key), dtype=np.float64)).tobytes())
    return digest.hexdigest()


def streams():
    return random.getstate(), np.random.get_state(), torch.get_rng_state().clone()


def same_streams(before, after):
    return (before[0] == after[0] and before[1][0] == after[1][0] and before[1][2:] == after[1][2:]
            and np.array_equal(before[1][1], after[1][1]) and torch.equal(before[2], after[2]))


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def test_the_probe_runs_thirteen_panels_and_takes_no_step(tmp_path, tiny, tiny_fit, monkeypatch):
    fit_summary, fit_out = tiny_fit
    point_at_the_tiny_fit(monkeypatch, fit_out / "summary.json")
    out = tmp_path / "probe"
    head = b10.shared.e0._git("rev-parse", "HEAD")
    assert b10.main(["probe", "--seed", str(SEED), "--weights",
                     str(fit_out / b08.WEIGHTS_NAME), "--launch-sha", head,
                     "--output-root", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())

    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == b10.OBJECT_ID and summary["command"] == "probe"
    assert summary["card"] == b10.CARD and "B10" in summary["card"]
    assert summary["block_seed"] == SEED and summary["evaluation_seed"] == EVALUATION_SEED
    assert summary["launch_sha"] == head == summary["requested_launch_sha"]
    assert summary["reference_object_ids"] == [b09.OBJECT_ID, b08.OBJECT_ID]
    assert summary["optimizer_steps"] == 0 and not any(summary["optimizer_calls"].values())
    assert summary["evaluation_panels"] == len(b10.RULES) == 13
    assert summary["evaluation_steps"] == LANES * HORIZON * len(b10.RULES)
    assert summary["evaluation_episodes"] == LANES * len(b10.RULES)
    assert summary["coordinator_training_mode"] is False
    assert (out / "construction" / "summary.json").exists()

    # (a) the loaded weights reproduce B08's own fit panel, bit for bit; B09's check, unrelaxed
    faithful = summary["faithful_load"]
    assert faithful["faithful_load"] is True and faithful["first_differing_world"] is None
    assert faithful["worlds"] == LANES and "not relaxed" in faithful["definition"]
    final_panel = [p for p in fit_summary["panels"] if p["panel_rollouts"] == ROLLOUTS][0]
    measured = summary["rules_measured"]
    assert measured["as_trained"]["J_world_scores"] == final_panel["native_scores_J"]
    assert summary["weights_record"]["sha256"] == fit_summary["final_weights"]["sha256"]
    assert measured["as_trained"].get("action_sampling") is None  # the baseline is mean actions

    # the policy's own action noise, read from the actor at the loaded weights after that panel
    deviation = summary["action_standard_deviation"]
    assert len(deviation["per_dimension"]) >= 1 and all(v > 0. for v in deviation["per_dimension"])
    assert deviation["head"] == "DiagGaussian" and deviation["mean_and_std_share_a_space"] is True
    assert "r_mappo_utils" in deviation["reader"]

    # (b) twelve sampled panels: B09's constant label everywhere, the action drawn from the Gaussian
    assert sorted(measured) == sorted(b10.RULES)
    for replicate in b10.REPLICATES:
        for label in range(N_z):
            name = b10.sampled_rule(label, replicate)
            record = measured[name]
            assert record["rule"] == name and record["action_sampling"] is True
            assert record["replicate"] == replicate and record["label"] == label
            assert record["label_rule"] == f"constant_{label}"
            assert record["constant_label"] == label and record["constant_team_label"] == label
            assert record["agent_label_histogram"] == [
                PANEL_ROWS if index == label else 0 for index in range(N_z)]
            assert record["team_label_histogram"][label] == HORIZON * LANES
            assert record["agent_label_change_fraction"] == 0.
            assert record["caps_applied"] == {}
            assert record["decision_steps"] == LANES * (HORIZON // SKILL_PERIOD)  # frozen cadence
            assert record["steps"] == LANES * HORIZON and record["lanes"] == LANES
            assert len(record["J_world_scores"]) == LANES
            assert not any(record["evaluator_optimizer_calls"].values())
            # the panel really ran the frozen route with the one flag replaced
            sampling = record["action_sampling_record"]
            assert sampling["torch_seed"] == b10.panel_seed(EVALUATION_SEED, name)
            assert sampling["deterministic_requested_by_the_frozen_route"] == [True]
            assert sampling["deterministic_executed"] is False
            assert sampling["seeded_at_action_selection_call"] == 0
            assert sampling["action_selection_calls"] == HORIZON
            assert sampling["rng_states_restored"] is True
            # and it executed actions that are not the policy's mean actions
            check = record["executed_action_check"]
            assert check["rows"] == record["actor_capture"]["captured_rows"] > 0
            assert check["rows_equal_to_the_mean_action"] == 0
            assert check["fraction_of_rows_differing_from_the_mean_action"] == 1.
            assert check["within_the_std_tolerance"] is True
            assert .5 <= check["rms_executed_minus_mean_over_std_mean"] <= 2.
            assert check["action_standard_deviation_per_dimension"] == deviation["per_dimension"]
            assert record["actor_capture_deterministic_arguments"] == [False]
    assert summary["sampled_panel_seeds"][b10.SAMPLED_RULES[0]]["torch_seed"] == b10.panel_seed(
        EVALUATION_SEED, b10.SAMPLED_RULES[0])

    # the readings the notebook entry asked for
    assert set(summary["J_by_rule"]) == set(b10.RULES)
    assert summary["J_minus_as_trained"]["as_trained"] == 0.
    for label in range(N_z):
        pair = [summary["J_by_rule"][b10.sampled_rule(label, r)] for r in b10.REPLICATES]
        assert summary["sampled_J_by_label"][str(label)] == pytest.approx(float(np.mean(pair)))
        assert summary["replicate_difference_by_label"][str(label)] == pytest.approx(
            pair[1] - pair[0])
        assert summary["sampled_J_minus_as_trained_by_label"][str(label)] == pytest.approx(
            float(np.mean(pair)) - summary["J_by_rule"]["as_trained"])
    means = [summary["sampled_J_by_label"][str(label)] for label in range(N_z)]
    assert summary["sampled_max_minus_min"] == pytest.approx(max(means) - min(means))
    assert summary["sampled_panel_noise_estimate"] == pytest.approx(float(np.sqrt(np.mean(
        [summary["replicate_difference_by_label"][str(label)] ** 2 for label in range(N_z)]))))
    assert sorted(summary["sampled_ranking"]) == list(range(N_z))
    assert summary["sampled_ranking"][0] == max(range(N_z), key=lambda label: (means[label],
                                                                              -label))
    assert summary["evaluation_route_determinism"]["low_level_action"].startswith("the Gaussian")
    assert "wsl_4070" in summary["interpretation_limit"]
    assert sorted(summary["rule_definitions"]) == sorted(b10.RULES)
    assert summary["wall_seconds"] > 0.

    # B08's tables are the ones B08 published with
    assert tables_are_b08s()


def test_an_unfaithful_load_stops_the_probe_before_any_sampled_panel(tmp_path, tiny, tiny_fit,
                                                                     monkeypatch):
    """The reference is a panel this checkpoint cannot reproduce, so nothing is ever sampled."""
    _fit_summary, fit_out = tiny_fit
    reference = tmp_path / "reference_summary.json"
    damaged = json.loads((fit_out / "summary.json").read_text())
    for panel in damaged["panels"]:
        panel["native_scores_J"] = [value + 1. for value in panel["native_scores_J"]]
    reference.write_text(json.dumps(damaged), encoding="utf-8")
    point_at_the_tiny_fit(monkeypatch, reference)
    out = tmp_path / "probe"
    assert b10.run_probe(SEED, fit_out / b08.WEIGHTS_NAME, out) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["faithful_load"]["faithful_load"] is False
    assert summary["faithful_load"]["first_differing_world"] == 0
    assert "first differing world index 0" in summary["failure"]
    assert sorted(summary["rules_measured"]) == ["as_trained"]
    assert "sampled_J_by_label" not in summary and "J_by_rule" not in summary
    assert tables_are_b08s()


# ---------------------------------------------------------------------------
# the panels, in B08's own harness
# ---------------------------------------------------------------------------


def test_the_as_trained_panel_is_the_same_panel_whatever_sampled_panels_ran(prepared):
    """The baseline panel is B08's own, before and after twelve panels of sampled actions."""
    (summary, learner, evaluator, out), baseline, standard_deviation = prepared
    plain = b08.run_rule_panel("as_trained", learner, evaluator, summary, out, 1,
                               evaluation_seed=EVALUATION_SEED)  # no binding of any kind
    assert baseline["J_world_scores"] == plain["J_world_scores"]
    assert baseline["returns_U"] == plain["returns_U"]
    assert comparable_metrics(baseline["d2_metrics"]) == comparable_metrics(plain["d2_metrics"])
    assert baseline["agent_label_histogram"] == plain["agent_label_histogram"]

    for index, name in enumerate(("sampled_constant_0_r0", "sampled_constant_5_r1")):
        sampled_panel(prepared[0], name, index + 2, standard_deviation)
    with b09.bound_rules():
        after = b10.run_rule_panel("as_trained", learner, evaluator, summary, out, 4,
                                   evaluation_seed=EVALUATION_SEED)
    assert after["J_world_scores"] == baseline["J_world_scores"]
    assert after["returns_U"] == baseline["returns_U"]
    assert after["component_means"] == baseline["component_means"]
    assert comparable_metrics(after["d2_metrics"]) == comparable_metrics(baseline["d2_metrics"])
    assert after["agent_label_histogram"] == baseline["agent_label_histogram"]
    assert after.get("action_sampling") is None  # the baseline never samples
    assert nothing_is_attached(evaluator.agent) and tables_are_b08s()


def test_a_sampled_panel_is_reproducible_across_replicates_and_panel_orders(prepared):
    """A sampled panel is a function of (block, label, replicate) alone, whatever ran before it."""
    (summary, learner, evaluator, out), _baseline, standard_deviation = prepared
    before = streams()
    first = sampled_panel(prepared[0], "sampled_constant_2_r0", 1, standard_deviation)
    other = sampled_panel(prepared[0], "sampled_constant_2_r1", 2, standard_deviation)
    again = sampled_panel(prepared[0], "sampled_constant_2_r0", 3, standard_deviation)
    other_label = sampled_panel(prepared[0], "sampled_constant_3_r0", 4, standard_deviation)
    # the same panel twice, with another replicate in between, is the same panel
    assert again["J_world_scores"] == first["J_world_scores"]
    assert again["returns_U"] == first["returns_U"]
    assert again["component_means"] == first["component_means"]
    assert again["executed_action_check"]["rms_executed_minus_mean_per_dimension"] == first[
        "executed_action_check"]["rms_executed_minus_mean_per_dimension"]
    # another replicate is another stream, and another label is another panel
    assert other["J_world_scores"] != first["J_world_scores"]
    assert other["action_sampling_record"]["torch_seed"] != first["action_sampling_record"][
        "torch_seed"]
    assert other_label["J_world_scores"] != first["J_world_scores"]
    assert other_label["agent_label_histogram"] == [0, 0, 0, PANEL_ROWS, 0, 0]
    # the panels left every global stream where they found it
    assert same_streams(before, streams())
    assert nothing_is_attached(evaluator.agent) and tables_are_b08s()


def test_a_sampled_panel_executes_its_label_and_leaves_the_policys_mean_action(prepared):
    (summary, learner, evaluator, out), baseline, standard_deviation = prepared
    agent = evaluator.agent
    record = sampled_panel(prepared[0], "sampled_constant_4_r0", 1, standard_deviation)
    # B09's label rule, unchanged: one label everywhere, written back, at the frozen cadence
    assert record["agent_label_histogram"] == [0, 0, 0, 0, PANEL_ROWS, 0]
    assert record["team_label_histogram"] == [0, 0, 0, 0, HORIZON * LANES, 0]
    assert record["agent_label_change_fraction"] == 0.
    assert record["decision_steps"] == LANES * (HORIZON // SKILL_PERIOD)
    for lane in range(LANES):
        assert agent.env_agent_skills[lane].tolist() == [4] * N_UAVS
        assert agent.env_team_skills[lane] == 4
    # the actions really left the mean, by the policy's own noise
    check = record["executed_action_check"]
    assert check["rows_equal_to_the_mean_action"] == 0
    assert check["fraction_of_rows_differing_from_the_mean_action"] == 1.
    assert check["within_the_std_tolerance"] is True
    assert check["action_dimensions"] == len(standard_deviation)
    assert record["actor_capture_deterministic_arguments"] == [False]
    # and the panel is not the mean-action panel of the same label
    with b09.bound_rules():
        mean_action = b09.run_rule_panel("constant_4", learner, evaluator, summary, out, 2,
                                         evaluation_seed=EVALUATION_SEED)
    assert mean_action["agent_label_histogram"] == record["agent_label_histogram"]
    assert mean_action["J_world_scores"] != record["J_world_scores"]
    assert mean_action.get("action_sampling") is None
    assert nothing_is_attached(agent) and tables_are_b08s()


def test_the_binding_comes_off_after_a_raising_panel_and_never_touches_the_class(prepared):
    (summary, learner, evaluator, out), _baseline, _std = prepared
    agent = evaluator.agent
    original = type(agent)._batched_select_action
    sampler = b10.SampledActions(agent, "sampled_constant_1_r0", EVALUATION_SEED)
    before = streams()
    with pytest.raises(ValueError, match="synthetic panel failure"):
        with sampler.attached():
            assert "_batched_select_action" in agent.__dict__
            assert "step" not in agent.__dict__  # the frozen dispatcher is still the class's own
            raise ValueError("synthetic panel failure")
    assert type(agent)._batched_select_action is original  # the class was never touched
    assert nothing_is_attached(agent)
    assert same_streams(before, streams())
    # a panel that raises inside B09's own binding leaves B08's tables alone too
    with pytest.raises(ValueError, match="synthetic panel failure"):
        with b09.bound_rules():
            raise ValueError("synthetic panel failure")
    assert tables_are_b08s()


def test_a_sampled_panel_takes_no_optimizer_step_and_writes_no_learner_state(prepared):
    (summary, learner, evaluator, out), _baseline, standard_deviation = prepared
    learner_before = parameter_digest(learner)
    evaluator_before = parameter_digest(evaluator.agent)  # after the baseline panel's own sync
    counters = b10.shared.optimizer_counters(evaluator.agent)
    learner_counters = b10.shared.optimizer_counters(learner)
    record = sampled_panel(prepared[0], "sampled_constant_0_r1", 1, standard_deviation)
    assert not any(record["evaluator_optimizer_calls"].values())
    assert not any(b10.shared.optimizer_counts(counters).values())
    assert not any(b10.shared.optimizer_counts(learner_counters).values())
    assert parameter_digest(learner) == learner_before
    assert parameter_digest(evaluator.agent) == evaluator_before
    assert nothing_is_attached(evaluator.agent) and tables_are_b08s()
