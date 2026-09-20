"""The label-map entry: the rules, the table binding, the per-world envelope and `reduce`.

A stub D2 agent, pure measure functions and synthetic published summaries only; the real stack is in
`test_label_map_real_tiny.py`. The stub agent and the synthetic B08 probe summaries are B08's own
test fixtures, loaded by path the way B08's tests load the production-boundary helpers, so the two
objects are compared through one shape and not two. Technical checks: nothing here asserts the
direction or the size of any measured quantity.
"""
import copy
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
    "fsd_label_map_b08_fixtures",
    Path(__file__).parents[1] / "label_content_b08/test_label_content.py")
b08tests = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b08tests)
StubD2Agent = b08tests.StubD2Agent

import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402

SEEDS = sorted(b09.BLOCKS)
EVALUATION_SEED = 782803
WORLDS = 4
# Synthetic panel means, one per constant label, chosen so the four declared statements have known
# answers; the world scores below are built to have exactly these means.
CONSTANTS = {772803: [.28, .29, .31, .30, .27, .26],
             772903: [.30, .33, .35, .29, .31, .28],
             773003: [.29, .32, .30, .28, .27, .26]}
FROZEN = {772803: .27, 772903: .28, 773003: .265}
# B08's own synthetic probe gives `as_trained` [.3] * 4 and `uniform_every_10` .33.
AS_TRAINED = .3
B08_REFERENCE = .33
HISTOGRAM = [10, 2, 40, 1, 0, 3]  # the coordinator's most used agent label is 2
BUMP = .2  # label c wins world c % WORLDS by this much, so the per-world envelope is known


# ---------------------------------------------------------------------------
# the rule set and the table binding
# ---------------------------------------------------------------------------


def test_the_rule_set_is_b08s_baseline_plus_this_objects_label_map():
    assert b09.RULES[0] == b09.BASELINE_RULE == "as_trained"
    assert b09.CONSTANT_RULES == tuple(f"constant_{label}" for label in range(6))
    assert b09.RULES == ("as_trained",) + b09.CONSTANT_RULES + ("uniform_frozen_episode",)
    assert b09.MAP_RULES == b09.CONSTANT_RULES + ("uniform_frozen_episode",)
    assert [b09.constant_label(name) for name in b09.CONSTANT_RULES] == list(range(6))
    assert b09.constant_label("as_trained") is None
    assert b09.constant_label(b09.FROZEN_RULE) is None
    assert b09.constant_rule(3) == "constant_3"
    # every rule carries a definition, and the constant ones say where the team label goes
    for name in b09.RULES:
        assert isinstance(b09.RULE_DEFINITIONS[name], str) and len(b09.RULE_DEFINITIONS[name]) > 40
    for name in b09.CONSTANT_RULES:
        assert "never reaches the low-level actor" in b09.RULE_DEFINITIONS[name]
        assert "bookkeeping" in b09.RULE_DEFINITIONS[name]
    assert b09.RULE_DEFINITIONS["as_trained"] == b08.RULE_DEFINITIONS["as_trained"]
    assert "holding logic B08's" in b09.RULE_DEFINITIONS[b09.FROZEN_RULE]
    assert "upper envelope" in b09.SOURCE_NOTES["oracle_envelope"]
    assert "wsl_4070" in b09.INTERPRETATION_LIMIT


def test_bound_rules_extends_b08s_tables_and_restores_every_one_of_them():
    before = {name: getattr(b08, name) for name in
              ("RULES", "RANDOM_RULES", "RULE_CAPS", "BASELINE_RULE", "ExecutionRule")}
    definitions = dict(b08.RULE_DEFINITIONS)
    with b09.bound_rules():
        assert b08.ExecutionRule is b09.MapExecutionRule
        assert set(b09.RULES) <= set(b08.RULE_DEFINITIONS)
        assert b09.FROZEN_RULE in b08.RANDOM_RULES
        # what is *not* extended: B08's own rule list, its caps and its baseline name
        assert b08.RULES == before["RULES"] and b08.RULE_CAPS == before["RULE_CAPS"]
        assert b08.BASELINE_RULE == before["BASELINE_RULE"]
        assert b09.FROZEN_RULE not in b08.RULE_CAPS and "constant_0" not in b08.RULE_CAPS
    for name, value in before.items():
        assert getattr(b08, name) is value
    assert b08.RULE_DEFINITIONS == definitions
    assert all(name not in b08.RULE_DEFINITIONS for name in b09.MAP_RULES)


def test_bound_rules_restores_the_tables_when_the_run_raises():
    definitions = dict(b08.RULE_DEFINITIONS)
    with pytest.raises(ValueError, match="synthetic panel failure"):
        with b09.bound_rules():
            raise ValueError("synthetic panel failure")
    assert b08.ExecutionRule is not b09.MapExecutionRule
    assert b08.RULE_DEFINITIONS == definitions
    assert b09.FROZEN_RULE not in b08.RANDOM_RULES


# ---------------------------------------------------------------------------
# the rules, on B08's stub D2 agent
# ---------------------------------------------------------------------------


def rule_for(name, agent, evaluation_seed=EVALUATION_SEED):
    """Built the way B08's own panel builds it: through B08's module global, inside the binding."""
    generator = (b08.label_generator(evaluation_seed, name) if name in b08.RANDOM_RULES else None)
    return b08.ExecutionRule(name, agent, generator=generator, horizon=100)


def run_panel(rule, agent, steps, episodes=1):
    """One stub panel; `episodes > 1` restarts the stub's step index, which is its episode reset."""
    executed = []
    with rule.attached():
        for episode in range(episodes):
            agent.step_index = 0 if episode else agent.step_index
            for _ in range(steps):
                team, agents, _ = agent._batched_assign_skills()
                executed.append((team.copy(), agents.copy()))
    return executed


def test_a_constant_rule_executes_one_label_everywhere_and_writes_it_back():
    agent = StubD2Agent(period=10)  # lanes 2, agents 3, n_Z 4, n_z 6
    with b09.bound_rules():
        rule = rule_for("constant_4", agent)
        assert isinstance(rule, b09.MapExecutionRule)
        executed = run_panel(rule, agent, 30)
        measures = rule.measures()
    for team, agents in executed:
        assert agents.tolist() == [[4] * agent.n_agents] * agent.lanes
        assert team.tolist() == [4 % 4] * agent.lanes  # n_Z is 4 here, so the team label wraps
    assert measures["constant_label"] == 4 and measures["constant_team_label"] == 0
    assert measures["agent_label_histogram"] == [0, 0, 0, 0, 30 * 2 * 3, 0]
    assert measures["team_label_histogram"] == [30 * 2, 0, 0, 0]
    assert measures["agent_label_change_fraction"] == 0.
    assert measures["team_label_change_fraction"] == 0.
    assert measures["caps_applied"] == {}  # the caps-10 cadence is the frozen one
    assert agent.decisions == 3  # the coordinator still decided at the same ticks
    # the executed label is also the label the agent now holds
    assert agent.env_agent_skills[0].tolist() == [4] * agent.n_agents
    assert agent.env_team_skills[1] == 0
    assert "_batched_assign_skills" not in agent.__dict__
    assert (agent.d2_k_max, agent.d2_k_Z) == (10, 10)
    assert b09.check_rule_record("constant_4", measures) is measures


def test_the_constant_team_label_is_the_agent_label_modulo_the_team_label_count():
    agent = StubD2Agent(period=10)
    with b09.bound_rules():
        rule = rule_for("constant_5", agent)
        executed = run_panel(rule, agent, 12)
        measures = rule.measures()
    assert all(team.tolist() == [1, 1] for team, _agents in executed)  # 5 % 4
    assert measures["constant_label"] == 5 and measures["constant_team_label"] == 1
    assert measures["agent_label_histogram"][5] == 12 * 2 * 3
    # a label the agent does not have is refused when the rule is built, not when it executes
    with b09.bound_rules():
        with pytest.raises(ValueError, match="outside the agent's"):
            b09.MapExecutionRule("constant_5", StubD2Agent(n_z=4))


def test_uniform_frozen_episode_holds_one_drawn_assignment_per_lane_and_episode():
    agent = StubD2Agent(period=10)
    with b09.bound_rules():
        rule = rule_for(b09.FROZEN_RULE, agent)
        executed = run_panel(rule, agent, 20, episodes=2)
        measures = rule.measures()
    first, second = executed[:20], executed[20:]
    for team, agents in first:  # held for the whole episode, decision ticks included
        assert team.tolist() == first[0][0].tolist()
        assert agents.tolist() == first[0][1].tolist()
    for team, agents in second:
        assert team.tolist() == second[0][0].tolist()
        assert agents.tolist() == second[0][1].tolist()
    assert measures["agent_label_change_fraction"] == 0.
    assert measures["team_label_change_fraction"] == 0.
    assert measures["caps_applied"] == {}
    assert measures["episodes"] == 4 == len(measures["episode_labels"])
    assert measures["episodes_per_lane"] == [2, 2]
    assert [entry["lane"] for entry in measures["episode_labels"]] == [0, 1, 0, 1]
    assert [entry["episode"] for entry in measures["episode_labels"]] == [0, 0, 1, 1]
    assert [entry["step"] for entry in measures["episode_labels"]] == [0, 0, 20, 20]
    for entry, (team, agents) in zip(measures["episode_labels"][:2], [first[0]] * 2):
        assert entry["agent_labels"] == agents[entry["lane"]].tolist()
        assert entry["team_label"] == int(team[entry["lane"]])
        assert entry["distinct_agent_labels"] == len(set(entry["agent_labels"]))
    assert "index `lane` of `J_world_scores`" in measures["episode_label_definition"]
    assert agent.env_agent_skills[0].tolist() == second[0][1][0].tolist()  # written back
    assert "_batched_assign_skills" not in agent.__dict__
    assert b09.check_rule_record(b09.FROZEN_RULE, measures) is measures


def test_the_frozen_draws_are_the_blocks_own_and_touch_no_global_stream():
    before = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())

    def drawn(evaluation_seed):
        agent = StubD2Agent(period=10)
        with b09.bound_rules():
            rule = rule_for(b09.FROZEN_RULE, agent, evaluation_seed=evaluation_seed)
            run_panel(rule, agent, 15, episodes=2)
            return [entry["agent_labels"] for entry in rule.measures()["episode_labels"]]

    labels = drawn(EVALUATION_SEED)
    after = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())
    assert before[0] == after[0]
    assert before[1][0] == after[1][0] and before[1][2:] == after[1][2:]
    np.testing.assert_array_equal(before[1][1], after[1][1])
    assert torch.equal(before[2], after[2])
    # the same block is the same stream, twice; another block is another stream
    assert drawn(EVALUATION_SEED) == labels
    assert drawn(782903) != labels
    # and it is this rule's own stream, not the stream B08's rules of the same block draw from
    assert b08.label_generator(EVALUATION_SEED, b09.FROZEN_RULE).integers(0, 6, 20).tolist() != \
        b08.label_generator(EVALUATION_SEED, "uniform_every_10").integers(0, 6, 20).tolist()


def test_the_map_rules_refuse_a_construction_they_are_not_defined_on():
    agent = StubD2Agent()
    agent.d2_cost_c = .25  # a finite interruption cost moves the decision boundary
    with b09.bound_rules():
        for name in ("constant_0", b09.FROZEN_RULE):
            with pytest.raises(ValueError, match="infinite interruption costs"):
                with rule_for(name, agent).attached():
                    pass
        agent.d2_cost_c = float("inf")
        agent.d2_enabled = False
        with pytest.raises(ValueError, match="D2 route"):
            with rule_for("constant_0", agent).attached():
                pass
        with pytest.raises(ValueError, match="needs its own label generator"):
            b09.MapExecutionRule(b09.FROZEN_RULE, agent)
        with pytest.raises(ValueError, match="unknown execution rule"):
            b09.MapExecutionRule("constant_9", agent)
    assert "_batched_assign_skills" not in agent.__dict__
    # outside the binding the map rules are not B08's rules at all
    with pytest.raises(ValueError, match="unknown execution rule"):
        b08.ExecutionRule("constant_0", agent)


def test_check_rule_record_refuses_a_panel_that_did_not_execute_its_map():
    good = {"agent_label_histogram": [0, 0, 12, 0, 0, 0], "team_label_histogram": [0, 0, 6, 0],
            "constant_team_label": 2, "agent_label_change_fraction": 0.,
            "team_label_change_fraction": 0.}
    assert b09.check_rule_record("constant_2", good) is good
    with pytest.raises(ValueError, match="executed agent labels other than 2"):
        b09.check_rule_record("constant_2", dict(good, agent_label_histogram=[1, 0, 11, 0, 0, 0]))
    with pytest.raises(ValueError, match="executed agent labels other than 2"):
        b09.check_rule_record("constant_2", dict(good, agent_label_histogram=[0] * 6))
    with pytest.raises(ValueError, match="executed team labels other than 2"):
        b09.check_rule_record("constant_2", dict(good, team_label_histogram=[0, 1, 5, 0]))
    with pytest.raises(ValueError, match="changed an executed label"):
        b09.check_rule_record("constant_2", dict(good, agent_label_change_fraction=.2))
    for damaged in ({"agent_label_histogram": [1, 2]}, dict(good, constant_team_label=None)):
        with pytest.raises(ValueError, match="no executed record"):
            b09.check_rule_record("constant_2", {key: value for key, value in damaged.items()
                                                 if value is not None})
    frozen = {"agent_label_histogram": [2, 2, 2, 2, 2, 2], "team_label_histogram": [3, 3, 3, 3],
              "agent_label_change_fraction": 0., "team_label_change_fraction": 0.}
    assert b09.check_rule_record(b09.FROZEN_RULE, frozen) is frozen
    with pytest.raises(ValueError, match="changed an executed label"):
        b09.check_rule_record(b09.FROZEN_RULE, dict(frozen, team_label_change_fraction=.1))
    with pytest.raises(ValueError, match="no label comparison"):
        b09.check_rule_record(b09.FROZEN_RULE, dict(frozen, agent_label_change_fraction=None))
    # B08's own rules are not checked here: they have no declared map
    assert b09.check_rule_record("as_trained", {"agent_label_histogram": [1, 2, 3, 4, 5, 6],
                                                "agent_label_change_fraction": .4}) is not None


# ---------------------------------------------------------------------------
# the readings: the label map, the ranking and the per-world envelope
# ---------------------------------------------------------------------------


def test_best_constant_ranks_the_labels_and_gives_a_tie_to_the_lowest_label():
    j_by_rule = {b09.constant_rule(label): value for label, value in
                 enumerate([.2, .5, .4, .5, .1, .3])}
    j_by_rule["as_trained"] = .45
    best = b09.best_constant(j_by_rule, .45)
    assert best["label"] == 1 and best["J"] == pytest.approx(.5)  # 1 and 3 tie; 1 is lower
    assert best["J_minus_as_trained"] == pytest.approx(.05)
    assert best["worst_label"] == 4 and best["worst_J"] == pytest.approx(.1)
    assert best["max_minus_min"] == pytest.approx(.4)
    assert best["ranking"] == [1, 3, 2, 5, 0, 4]
    assert best["J_by_label"]["2"] == pytest.approx(.4)
    flat = {b09.constant_rule(label): .25 for label in range(6)}
    assert b09.best_constant(flat, .25)["ranking"] == list(range(6))
    assert b09.best_constant(flat, .25)["max_minus_min"] == 0.


def test_the_per_world_envelope_is_the_per_world_maximum_over_the_labels():
    scores = {0: [.1, .4, .2], 1: [.2, .1, .3], 2: [.5, .2, .1],
              3: [.3, .4, .4], 4: [.0, .0, .5], 5: [.4, .3, .7]}
    by_rule = {b09.constant_rule(label): value for label, value in scores.items()}
    baseline = [.3, .3, .3]
    result = b09.per_world_best_constant(by_rule, baseline)
    assert result["worlds"] == 3
    assert [record["label"] for record in result["records"]] == [2, 0, 5]  # world 1 ties 0 and 3
    assert [record["J"] for record in result["records"]] == pytest.approx([.5, .4, .7])
    assert [record["as_trained_J"] for record in result["records"]] == [.3, .3, .3]
    assert [record["J_minus_as_trained"] for record in result["records"]] == pytest.approx(
        [.2, .1, .4])
    assert result["records"][0]["J_by_label"] == pytest.approx([.1, .2, .5, .3, .0, .4])
    assert result["oracle_constant_envelope_J"] == pytest.approx(np.mean([.5, .4, .7]))
    assert result["label_counts"] == {"0": 1, "1": 0, "2": 1, "3": 0, "4": 0, "5": 1}
    assert sum(result["label_counts"].values()) == result["worlds"]
    assert "selected on the same" in result["selection_note"]


# ---------------------------------------------------------------------------
# synthetic published summaries and `reduce`
# ---------------------------------------------------------------------------


def constant_scores(mean, label):
    """Four world scores with exactly this mean, where label `label` wins world `label % 4`."""
    return [mean - BUMP / WORLDS + (BUMP if world == label % WORLDS else 0.)
            for world in range(WORLDS)]


def panel_record(name, scores, histogram=None):
    scores = [float(value) for value in scores]
    record = {"rule": name, "J_mean": float(np.mean(scores)), "J_world_scores": scores,
              "agent_label_histogram": list(histogram or [0] * 6),
              "team_label_histogram": [0] * 6,
              "agent_label_change_fraction": 0., "team_label_change_fraction": 0.,
              "decision_fraction": .1, "steps": 1000, "decision_steps": 100}
    if b09.constant_label(name) is not None:
        record["constant_label"] = b09.constant_label(name)
        record["constant_team_label"] = b09.constant_label(name) % 6
    if name == b09.FROZEN_RULE:
        record["episode_labels"] = [{"lane": lane, "episode": 0, "step": 0, "team_label": 0,
                                     "agent_labels": [lane] * 6, "distinct_agent_labels": 1}
                                    for lane in range(WORLDS)]
        record["episodes_per_lane"] = [1] * WORLDS
    return record


def probe_summary(seed, sha="synthetic-source", **overrides):
    """A published probe summary of this object, in the shape `reduce` reads."""
    measured = {b09.BASELINE_RULE: panel_record(b09.BASELINE_RULE, [AS_TRAINED] * WORLDS,
                                                HISTOGRAM)}
    for label in range(6):
        measured[b09.constant_rule(label)] = panel_record(
            b09.constant_rule(label), constant_scores(CONSTANTS[seed][label], label))
    measured[b09.FROZEN_RULE] = panel_record(b09.FROZEN_RULE, [FROZEN[seed]] * WORLDS)
    envelope = b09.per_world_best_constant(
        {name: measured[name]["J_world_scores"] for name in b09.CONSTANT_RULES},
        measured[b09.BASELINE_RULE]["J_world_scores"])
    summary = {
        "object_id": b09.OBJECT_ID, "command": "probe", "status": "complete",
        "block_seed": seed, "evaluation_seed": b09.BLOCKS[seed], "launch_sha": sha,
        "optimizer_steps": 0, "weights_record": {"sha256": f"sha-{seed}"},
        "faithful_load": {"faithful_load": True, "first_differing_world": None},
        "rules_measured": measured, "rules": list(b09.RULES),
        "oracle_constant_envelope_J": envelope["oracle_constant_envelope_J"],
        "wall_seconds": 300.}
    summary.update(overrides)
    return summary


def supplied(probe_sha="synthetic-source", b08_sha="b08-source"):
    probes = [probe_summary(seed, probe_sha) for seed in SEEDS]
    others = []
    for seed in SEEDS:
        summary = b08tests.probe_summary(seed, f"sha-{seed}", launch_sha=b08_sha)
        # one `as_trained` panel, so B08's probe carries the same executed histogram
        summary["rules_measured"]["as_trained"]["agent_label_histogram"] = list(HISTOGRAM)
        others.append(summary)
    return probes, others


def test_the_synthetic_inputs_agree_with_b08s_own_probe_shape():
    """The fixture itself: the two objects' `as_trained` panels must be one panel."""
    probes, others = supplied()
    for probe, other in zip(probes, others):
        assert probe["rules_measured"]["as_trained"]["J_world_scores"] == other[
            "rules_measured"]["as_trained"]["J_world_scores"]
        assert probe["weights_record"]["sha256"] == other["weights_record"]["sha256"]
    assert others[0]["rules_measured"]["uniform_every_10"]["J_mean"] == pytest.approx(B08_REFERENCE)


def test_reduce_reads_three_probes_beside_b08s_three(tmp_path):
    probes, others = supplied()
    result = b09.reduce_inputs(probes, others)
    assert result["status"] == "complete" and result["object_id"] == b09.OBJECT_ID
    assert result["blocks_read"] == 3 and result["invalid_probes"] == {}
    assert result["invalid_b08_probes"] == {}
    assert result["probe_launch_sha"] == "synthetic-source"
    assert result["b08_probe_launch_sha"] == "b08-source"
    assert result["rules"] == list(b09.RULES) and result["b08_reference_rule"] == "uniform_every_10"

    for index, block in enumerate(result["blocks"]):
        seed = SEEDS[index]
        assert block["status"] == "complete" and block["weights_match"] is True
        assert block["as_trained_identical_to_b08"] is True
        assert block["J_by_rule"]["as_trained"] == pytest.approx(AS_TRAINED)
        assert block["J_minus_as_trained"]["as_trained"] == 0.
        best = max(CONSTANTS[seed])
        assert block["best_constant"]["label"] == CONSTANTS[seed].index(best)
        assert block["best_constant"]["J"] == pytest.approx(best)
        assert block["best_constant_minus_as_trained"] == pytest.approx(best - AS_TRAINED)
        assert block["best_constant_minus_b08_uniform_every_10"] == pytest.approx(
            best - B08_REFERENCE)
        assert block["max_constant_minus_min_constant"] == pytest.approx(
            best - min(CONSTANTS[seed]))
        assert block["uniform_frozen_episode_minus_as_trained"] == pytest.approx(
            FROZEN[seed] - AS_TRAINED)
        assert block["uniform_frozen_episode_minus_b08_uniform_every_10"] == pytest.approx(
            FROZEN[seed] - B08_REFERENCE)
        assert block["oracle_envelope_matches_the_published_one"] is True
        # the envelope is the mean of the per-world maxima, which the fixture makes exact
        winners = [max(CONSTANTS[seed][label] + (BUMP - BUMP / WORLDS)
                       for label in range(6) if label % WORLDS == world)
                   for world in range(WORLDS)]
        assert block["oracle_constant_envelope_J"] == pytest.approx(np.mean(winners))
        assert block["oracle_envelope_minus_as_trained"] == pytest.approx(
            np.mean(winners) - AS_TRAINED)
        # the ranking sits beside the histogram the coordinator's own panel produced
        assert [row["label"] for row in block["constant_ranking"]] == block["best_constant"][
            "ranking"]
        assert [row["rank"] for row in block["constant_ranking"]] == [1, 2, 3, 4, 5, 6]
        assert block["as_trained_agent_label_histogram"] == HISTOGRAM
        assert block["b08_as_trained_agent_label_histogram"] == HISTOGRAM
        assert block["as_trained_histogram_matches_b08"] is True
        most_used = block["coordinator_most_used_label"]
        assert most_used["label"] == 2 and most_used["executions"] == 40
        assert most_used["execution_fraction"] == pytest.approx(40 / sum(HISTOGRAM))
        assert most_used["rank_among_constants"] == block["best_constant"]["ranking"].index(2) + 1
        assert most_used["J_as_a_constant"] == pytest.approx(CONSTANTS[seed][2])
        assert most_used["is_the_best_constant"] is (block["best_constant"]["label"] == 2)
        assert most_used["is_the_worst_constant"] is (block["best_constant"]["worst_label"] == 2)
        assert block["b08_J_by_rule"]["uniform_every_10"] == pytest.approx(B08_REFERENCE)

    # across the blocks, in B08's own working-model wording
    assert result["J_by_rule"]["as_trained"]["available_blocks"] == 3
    assert result["best_constant_minus_as_trained"]["available_blocks"] == 3
    assert result["best_constant_minus_as_trained"]["mean"] == pytest.approx(
        np.mean([max(CONSTANTS[seed]) - AS_TRAINED for seed in SEEDS]))
    assert "iid-normal paired block differences" in result[
        "best_constant_minus_as_trained"]["working_model"]
    assert result["oracle_envelope_minus_as_trained"]["positive_blocks"] == 3
    assert result["J_uniform_frozen_episode_minus_as_trained"]["available_blocks"] == 3
    assert result["one_best_constant_label_across_blocks"] is None  # 2, 2 and 1 here
    assert result["best_constant_label_by_block"] == {
        str(seed): CONSTANTS[seed].index(max(CONSTANTS[seed])) for seed in SEEDS}
    # no verdict strings: numbers, definitions and limits only
    text = json.dumps(result).lower()
    for word in ("inert", "content present", "verdict", "confirmed", "the label matters"):
        assert word not in text


def test_the_prediction_counts_are_the_declared_statements(tmp_path):
    probes, others = supplied()
    predictions = b09.reduce_inputs(probes, others)["predictions"]
    p1 = predictions["P1_a_constant_label_beats_as_trained_on_772903"]
    assert p1["blocks_considered"] == [772903] and p1["blocks_read"] == 1
    assert p1["blocks_holding"] == 1  # .35 - .30 = .05 > .03
    assert p1["per_block"]["772903"]["value"] == pytest.approx(.05)
    p2 = predictions["P2_the_best_constant_is_within_the_margin_on_772803_and_773003"]
    assert p2["blocks_considered"] == [772803, 773003] and p2["blocks_holding"] == 2
    p3 = predictions["P3_the_oracle_envelope_exceeds_as_trained_on_every_block"]
    assert p3["blocks_considered"] == SEEDS and p3["blocks_holding"] == 3
    alternative = predictions["A_every_constant_at_or_below_b08_uniform_every_10_on_772903"]
    assert alternative["blocks_considered"] == [772903]
    assert alternative["blocks_holding"] == 0  # .35 is above B08's .33 here
    assert alternative["per_block"]["772903"]["value"] is False
    assert "not a weight of evidence" in predictions["counting_note"]

    # a block that is not read is counted as not read, and holds nothing
    damaged = copy.deepcopy(probes)
    damaged[1]["status"] = "incomplete"
    predictions = b09.reduce_inputs(damaged, others)["predictions"]
    p1 = predictions["P1_a_constant_label_beats_as_trained_on_772903"]
    assert p1["blocks_read"] == 0 and p1["blocks_holding"] == 0
    assert p1["per_block"]["772903"] == {"read": False, "holds": None, "value": None}


def test_reduce_refuses_a_block_that_is_not_b08s_own_checkpoint_and_panel(tmp_path):
    probes, others = supplied()
    damaged = copy.deepcopy(probes)
    damaged[0]["weights_record"] = {"sha256": "sha-of-another-checkpoint"}
    result = b09.reduce_inputs(damaged, others)
    assert result["status"] == "incomplete" and result["blocks_read"] == 2
    block = result["blocks"][0]
    assert block["weights_match"] is False and block["status"] == "incomplete"
    assert "sha256" in block["missing_or_invalid"]["weights"]
    assert "J_by_rule" not in block

    damaged = copy.deepcopy(probes)
    scores = damaged[2]["rules_measured"]["as_trained"]["J_world_scores"]
    damaged[2]["rules_measured"]["as_trained"]["J_world_scores"] = [scores[0] + 1e-12] + scores[1:]
    result = b09.reduce_inputs(damaged, others)
    assert result["status"] == "incomplete"
    block = result["blocks"][2]
    assert block["weights_match"] is True and block["as_trained_identical_to_b08"] is False
    assert "not the same policy on the same worlds" in block["missing_or_invalid"]["as_trained"]

    # a histogram that is not B08's is recorded beside it, and refuses nothing: what ties the two
    # probes together is the world scores, which are compared exactly
    damaged = copy.deepcopy(others)
    damaged[0]["rules_measured"]["as_trained"]["agent_label_histogram"] = [6, 6, 6, 6, 6, 6]
    result = b09.reduce_inputs(probes, damaged)
    assert result["status"] == "complete"
    assert result["blocks"][0]["as_trained_histogram_matches_b08"] is False
    assert result["blocks"][0]["b08_as_trained_agent_label_histogram"] == [6] * 6

    # a B08 probe that was not supplied, and one B08's own reader refuses
    result = b09.reduce_inputs(probes, others[1:])
    assert result["blocks"][0]["missing_or_invalid"]["b08_probe"] == "not supplied"
    damaged = copy.deepcopy(others)
    damaged[1]["faithful_load"] = {"faithful_load": False, "first_differing_world": 3}
    result = b09.reduce_inputs(probes, damaged)
    assert "faithful load" in result["invalid_b08_probes"][str(SEEDS[1])]
    assert result["blocks"][1]["status"] == "incomplete"


def test_reduce_refuses_mixed_launch_shas_duplicates_and_unreadable_probes(tmp_path):
    probes, others = supplied()
    damaged = copy.deepcopy(probes)
    damaged[1]["launch_sha"] = "another-source"
    with pytest.raises(ValueError, match="mixed launch shas among the probes"):
        b09.reduce_inputs(damaged, others)
    with pytest.raises(ValueError, match="duplicate probe block"):
        b09.reduce_inputs(probes + [copy.deepcopy(probes[0])], others)
    with pytest.raises(ValueError, match="duplicate B08 probe block"):
        b09.reduce_inputs(probes, others + [copy.deepcopy(others[0])])

    for mutate, message in (
            (lambda s: s.update(status="incomplete"), "incomplete probe"),
            (lambda s: s.update(object_id="OTHER"), "not a probe of this object"),
            (lambda s: s.update(command="fit"), "not a probe of this object"),
            (lambda s: s.update(optimizer_steps=1), "took an optimizer step"),
            (lambda s: s.update(evaluation_seed=1), "one of this object's three blocks"),
            (lambda s: s["rules_measured"].pop("constant_3"), "all eight execution rules"),
            (lambda s: s.update(faithful_load={"faithful_load": False}), "faithful load")):
        damaged = copy.deepcopy(probes)
        mutate(damaged[2])
        result = b09.reduce_inputs(damaged, others)
        assert result["status"] == "incomplete"
        assert message in result["invalid_probes"][str(SEEDS[2])]
        assert result["blocks"][2]["status"] == "incomplete"


def test_reduce_publishes_a_summary_through_main(tmp_path):
    probes, others = supplied()
    written = []
    for name, summaries in (("b09", probes), ("b08", others)):
        for summary in summaries:
            path = tmp_path / f"{name}_{summary['block_seed']}.json"
            path.write_text(json.dumps(summary), encoding="utf-8")
            written.append(path)
    out = tmp_path / "reduce"
    assert b09.main(["reduce", "--probes"] + [str(p) for p in written[:3]]
                    + ["--b08-probes"] + [str(p) for p in written[3:]]
                    + ["--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and result["blocks_read"] == 3
    assert result["input_probes"] == [str(p) for p in written[:3]]
    assert result["input_b08_probes"] == [str(p) for p in written[3:]]
    # B08's tables are untouched by a reading command
    assert b08.ExecutionRule is not b09.MapExecutionRule
    assert all(name not in b08.RULE_DEFINITIONS for name in b09.MAP_RULES)
