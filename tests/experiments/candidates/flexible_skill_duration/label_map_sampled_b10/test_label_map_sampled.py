"""The sampled-label-map entry: the action-noise binding, the measures and `reduce`.

A stub agent whose action selection can be wrapped, a stub actor for the executed-action check, pure
measure functions and synthetic published summaries only; the real stack is in
`test_label_map_sampled_real_tiny.py`. The synthetic B09 probe summaries are B09's own test
fixtures, loaded by path the way B09's tests load B08's, so the two objects are compared through one
shape and not two. Technical checks: nothing here asserts the direction or the size of any measured
quantity.
"""
import copy
import importlib.util
import json
import random
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_label_map_sampled_b09_fixtures",
    Path(__file__).parents[1] / "label_map_b09/test_label_map.py")
b09tests = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b09tests)

import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402
import run_fsd_label_map_sampled_b10 as b10  # noqa: E402

SEEDS = sorted(b10.BLOCKS)
WORLDS = b09tests.WORLDS
AS_TRAINED = b09tests.AS_TRAINED
HISTOGRAM = b09tests.HISTOGRAM
# B09's own synthetic mean-action map, which this object's synthetic probes are read against:
# 772803 [.28 .29 .31 .30 .27 .26], 772903 [.30 .33 .35 .29 .31 .28], 773003 [.29 .32 .30 .28 .27 .26].
MEAN_ACTION = b09tests.CONSTANTS
# The sampled label map of the synthetic probes, one mean per label, chosen so that the three
# declared statements and the three outcomes have known answers:
#   772803  the same order as B09's, spread .03           -> E1, rank correlation +1
#   772903  the same best label, spread .10, one tie      -> E2, a hand-computed correlation
#   773003  B09's order reversed, spread .06              -> neither, rank correlation -1
SAMPLED = {772803: [.300, .310, .320, .315, .295, .290],
           772903: [.300, .340, .400, .320, .310, .300],
           773003: [.300, .280, .290, .310, .320, .340]}
# r1 - r0 of label c is `GAP[seed] * (c - 2)`, so the replicate mean is the value above and the RMS
# over the six labels is `GAP[seed] * sqrt(19 / 6)`.
GAP = {772803: .004, 772903: .006, 773003: .005}
GAP_RMS = float(np.sqrt(np.mean([(label - 2) ** 2 for label in range(6)])))


def replicate_value(seed, label, replicate):
    gap = GAP[seed] * (label - 2)
    return SAMPLED[seed][label] + (gap / 2. if replicate else -gap / 2.)


# ---------------------------------------------------------------------------
# the panel set, the definitions and the seed
# ---------------------------------------------------------------------------


def test_the_panel_set_is_as_trained_plus_the_twelve_sampled_panels():
    assert b10.RULES[0] == b10.BASELINE_RULE == "as_trained" == b09.BASELINE_RULE
    assert b10.REPLICATES == (0, 1) and b10.N_LABELS == 6
    assert len(b10.RULES) == 13 and len(set(b10.RULES)) == 13
    assert b10.SAMPLED_RULES == tuple(f"sampled_constant_{label}_r{replicate}"
                                      for replicate in (0, 1) for label in range(6))
    for replicate in (0, 1):
        for label in range(6):
            name = b10.sampled_rule(label, replicate)
            assert b10.sampled_parts(name) == (label, replicate)
    assert b10.sampled_parts("as_trained") == (None, None)
    assert b10.sampled_parts("constant_3") == (None, None)
    # every panel carries a definition; the sampled ones name B09's label rule and the sampling
    for name in b10.RULES:
        assert isinstance(b10.RULE_DEFINITIONS[name], str) and len(b10.RULE_DEFINITIONS[name]) > 40
    assert b10.RULE_DEFINITIONS["as_trained"] == b09.RULE_DEFINITIONS["as_trained"]
    for label in range(6):
        text = b10.RULE_DEFINITIONS[b10.sampled_rule(label, 1)]
        assert f"B09's `constant_{label}` label rule" in text
        assert "sampled* from the policy's own Gaussian" in text
        assert "replicate 1" in text
    assert "wsl_4070" in b10.INTERPRETATION_LIMIT
    assert "isolate" in b10.INTERPRETATION_LIMIT or "isolates" in b10.INTERPRETATION_LIMIT
    # the source notes carry the file:line facts about what `deterministic` controls
    effects = b10.SOURCE_NOTES["deterministic_effects"]
    for citation in ("run_fsd_baseline_interruption_b01.py:224-225", "hmasd/agent.py:3249-3251",
                     "hmasd/agent.py:3266-3268", "hmasd/agent.py:2652-2661",
                     "hmasd/networks.py:1072", "hmasd/networks.py:1099",
                     "hmasd/r_mappo_utils.py:91-94"):
        assert citation in effects
    assert "store_rollout_step" in b10.SOURCE_NOTES["no_learner_state_written"]
    assert "hmasd/agent.py:3266-3268" in b10.SOURCE_NOTES["action_sampling_attachment"]
    assert "run_fsd_label_map_b09.py:212-213" in b10.SOURCE_NOTES[
        "coordinator_determinism_under_a_constant_label"]


def test_the_panel_seed_is_a_function_of_the_block_and_the_panel_name():
    seeds = {name: b10.panel_seed(782903, name) for name in b10.SAMPLED_RULES}
    assert len(set(seeds.values())) == len(b10.SAMPLED_RULES)  # every panel its own stream
    assert all(0 <= value < 2 ** 63 for value in seeds.values())
    assert b10.panel_seed(782903, "sampled_constant_2_r0") == b10.panel_seed(
        782903, "sampled_constant_2_r0")
    assert b10.panel_seed(782903, "sampled_constant_2_r0") != b10.panel_seed(
        782803, "sampled_constant_2_r0")  # another block, another stream
    assert b10.panel_seed(782903, "sampled_constant_2_r0") != b10.panel_seed(
        782903, "sampled_constant_2_r1")  # another replicate, another stream
    assert "sha256" in b10.SEED_DERIVATION and "manual_seed" in b10.SEED_DERIVATION


# ---------------------------------------------------------------------------
# the action-noise binding, on a stub whose action selection can be wrapped
# ---------------------------------------------------------------------------


class StubActionAgent:
    """The whole surface `SampledActions` touches: one instance method, and a draw to watch."""

    def __init__(self):
        self.requested = []

    def _batched_select_action(self, states, observations, agent_skills, team_skills, dones,
                               deterministic=False):
        self.requested.append(bool(deterministic))
        return torch.randn(3), None, None


def call(agent, deterministic=True, keyword=False):
    """One call in the shape the frozen `step` makes it: six positional arguments; the action."""
    if keyword:
        return agent._batched_select_action(None, None, None, None, None,
                                            deterministic=deterministic)[0]
    return agent._batched_select_action(None, None, None, None, None, deterministic)[0]


def states():
    return random.getstate(), np.random.get_state(), torch.get_rng_state().clone()


def same_states(before, after):
    return (before[0] == after[0] and before[1][0] == after[1][0] and before[1][2:] == after[1][2:]
            and np.array_equal(before[1][1], after[1][1]) and torch.equal(before[2], after[2]))


def test_the_wrapper_samples_for_one_panel_and_comes_off_afterwards():
    agent = StubActionAgent()
    original = StubActionAgent._batched_select_action
    sampler = b10.SampledActions(agent, "sampled_constant_1_r0", 782803)
    before = states()
    with sampler.attached() as bound:
        assert bound is sampler
        assert "_batched_select_action" in agent.__dict__  # an instance attribute, for this panel
        drawn = [call(agent).clone() for _ in range(3)]
        assert call(agent, keyword=True) is not None  # the keyword shape is handled too
    # the frozen method saw deterministic=False every time, though the caller asked for True
    assert agent.requested == [False] * 4
    assert sampler.requested == {True}
    assert sampler.calls == 4 and sampler.seeded_at_call == 0
    assert sampler.require_frozen_route() is sampler
    # the wrapper is off and the class was never touched
    assert "_batched_select_action" not in agent.__dict__
    assert StubActionAgent._batched_select_action is original
    # every global stream is the one the panel started from
    assert same_states(before, states())
    assert len(drawn) == 3


def test_the_wrapper_comes_off_and_restores_the_streams_when_the_panel_raises():
    agent = StubActionAgent()
    before = states()
    sampler = b10.SampledActions(agent, "sampled_constant_4_r1", 782803)
    with pytest.raises(ValueError, match="synthetic panel failure"):
        with sampler.attached():
            call(agent)
            raise ValueError("synthetic panel failure")
    assert "_batched_select_action" not in agent.__dict__
    assert StubActionAgent._batched_select_action.__qualname__.endswith("_batched_select_action")
    assert sampler.rng_restored is True
    assert same_states(before, states())


def test_the_wrapper_refuses_a_second_binding_and_a_call_without_the_flag():
    agent = StubActionAgent()
    sampler = b10.SampledActions(agent, "sampled_constant_0_r0", 782803)
    with sampler.attached():
        other = b10.SampledActions(agent, "sampled_constant_0_r1", 782803)
        with pytest.raises(ValueError, match="already wrapped"):
            with other.attached():
                pass
        # the first binding is still the one in place, and the failed one left nothing
        assert agent.__dict__["_batched_select_action"].__qualname__.startswith("SampledActions")
        with pytest.raises(ValueError, match="without its `deterministic` argument"):
            agent._batched_select_action(None, None, None)
    assert "_batched_select_action" not in agent.__dict__


def test_a_panel_that_did_not_run_the_frozen_route_is_refused():
    agent = StubActionAgent()
    sampler = b10.SampledActions(agent, "sampled_constant_0_r0", 782803)
    with pytest.raises(ValueError, match="selected no action"):
        sampler.require_frozen_route()
    with sampler.attached():
        call(agent, deterministic=False)  # a caller that was not the frozen evaluation route
    with pytest.raises(ValueError, match="not the frozen evaluation route"):
        sampler.require_frozen_route()


def test_a_sampled_panel_is_reproducible_and_independent_of_what_ran_before_it():
    """The draws are a function of (block, panel name) alone, whatever the stream was on entry."""
    def draws(rule, seed=782803):
        agent = StubActionAgent()
        sampler = b10.SampledActions(agent, rule, seed)
        with sampler.attached():
            drawn = [call(agent).clone() for _ in range(4)]
        return drawn, sampler.record()  # the record is taken after the panel, as the probe does

    torch.manual_seed(11)
    first, record = draws("sampled_constant_3_r0")
    torch.manual_seed(999)  # a different stream on entry
    [torch.randn(17) for _ in range(3)]
    second, _ = draws("sampled_constant_3_r0")
    other_replicate, _ = draws("sampled_constant_3_r1")
    other_block, _ = draws("sampled_constant_3_r0", seed=782903)
    assert all(torch.equal(a, b) for a, b in zip(first, second))
    assert not any(torch.equal(a, b) for a, b in zip(first, other_replicate))
    assert not any(torch.equal(a, b) for a, b in zip(first, other_block))
    assert record["torch_seed"] == b10.panel_seed(782803, "sampled_constant_3_r0")
    assert record["seeded_at_action_selection_call"] == 0
    assert record["deterministic_requested_by_the_frozen_route"] == [True]
    assert record["deterministic_executed"] is False
    assert record["rng_states_restored"] is True
    assert "run_fsd_label_map_sampled_b10.py:" in record["attached_at"]
    assert "hmasd/agent.py:3266-3268" in record["attached_at"]


# ---------------------------------------------------------------------------
# the runtime proof that the executed actions are not the mean actions
# ---------------------------------------------------------------------------


class StubDiscoverer:
    """An actor whose deterministic forward returns a fixed mean action at any input."""

    def __init__(self, mean):
        self.mean, self.deterministic = mean, []

    def __call__(self, observation, agent_skill, hidden, deterministic, compact_context=None,
                 central_input=None):
        self.deterministic.append(bool(deterministic))
        return self.mean.clone(), None, None, None


def capture_for(mean, executed, label):
    rows = int(mean.shape[0])
    entry = {"observation": torch.zeros(rows, 4), "hidden": torch.zeros(rows, 2),
             "agent_skill": torch.full((rows,), int(label), dtype=torch.long),
             "compact_context": None, "central_input": None, "action": executed,
             "deterministic": False}
    return types.SimpleNamespace(captured=[entry])


def stub_agent(mean):
    return types.SimpleNamespace(skill_discoverer=StubDiscoverer(mean))


def test_the_executed_action_check_reads_the_noise_against_the_policy_std():
    torch.manual_seed(5)
    rows, dimensions, std = 512, 3, np.array([2.9, 1.5, .8])
    mean = torch.randn(rows, dimensions).double()
    noise = torch.randn(rows, dimensions).double() * torch.as_tensor(std)
    agent = stub_agent(mean)
    check = b10.executed_action_check(agent, capture_for(mean, mean + noise, 2), std, 2)
    assert check["rows"] == rows and check["action_dimensions"] == dimensions
    assert check["rows_equal_to_the_mean_action"] == 0
    assert check["fraction_of_rows_differing_from_the_mean_action"] == 1.
    assert check["within_the_std_tolerance"] is True
    assert check["rms_executed_minus_mean_over_std_mean"] == pytest.approx(1., abs=.15)
    assert check["action_standard_deviation_per_dimension"] == list(std)
    assert check["max_absolute_executed_minus_mean"] > 0.
    assert agent.skill_discoverer.deterministic == [True]  # the mean, recomputed deterministically
    # the recomputation is read-only: it draws nothing from any global stream
    before = states()
    b10.executed_action_check(stub_agent(mean), capture_for(mean, mean + noise, 2), std, 2)
    assert same_states(before, states())


def test_the_executed_action_check_refuses_a_panel_that_executed_the_mean():
    rows, std = 64, np.array([2.9, 1.5, .8])
    mean = torch.zeros(rows, 3).double()
    with pytest.raises(ValueError, match="did not sample"):
        b10.executed_action_check(stub_agent(mean), capture_for(mean, mean.clone(), 1), std, 1)


def test_the_executed_action_check_refuses_noise_that_is_not_the_policys():
    torch.manual_seed(7)
    rows, std = 256, np.array([2.9, 1.5, .8])
    mean = torch.zeros(rows, 3).double()
    loud = mean + torch.randn(rows, 3).double() * torch.as_tensor(std) * 5.
    with pytest.raises(ValueError, match="outside a factor of"):
        b10.executed_action_check(stub_agent(mean), capture_for(mean, loud, 1), std, 1)
    quiet = mean + torch.randn(rows, 3).double() * torch.as_tensor(std) * .05
    with pytest.raises(ValueError, match="outside a factor of"):
        b10.executed_action_check(stub_agent(mean), capture_for(mean, quiet, 1), std, 1)


def test_the_executed_action_check_refuses_rows_that_do_not_hold_the_label():
    rows, std = 8, np.array([2.9, 1.5, .8])
    mean = torch.zeros(rows, 3).double()
    capture = capture_for(mean, mean + 1., 1)
    capture.captured[0]["agent_skill"][3] = 4
    with pytest.raises(ValueError, match="do not all hold label 1"):
        b10.executed_action_check(stub_agent(mean), capture, std, 1)
    with pytest.raises(ValueError, match="captured no actor call"):
        b10.executed_action_check(stub_agent(mean), types.SimpleNamespace(captured=[]), std, 1)


# ---------------------------------------------------------------------------
# the measures
# ---------------------------------------------------------------------------


def j_by_rule(seed, baseline=AS_TRAINED):
    values = {b10.BASELINE_RULE: baseline}
    for replicate in b10.REPLICATES:
        for label in range(6):
            values[b10.sampled_rule(label, replicate)] = replicate_value(seed, label, replicate)
    return values


def test_the_sampled_map_is_the_replicate_mean_the_difference_and_its_rms():
    seed = 772903
    reading = b10.sampled_reading(j_by_rule(seed), AS_TRAINED)
    for label in range(6):
        assert reading["sampled_J_by_label"][str(label)] == pytest.approx(SAMPLED[seed][label])
        assert reading["replicate_difference_by_label"][str(label)] == pytest.approx(
            GAP[seed] * (label - 2))
        assert reading["sampled_J_minus_as_trained_by_label"][str(label)] == pytest.approx(
            SAMPLED[seed][label] - AS_TRAINED)
        pair = reading["sampled_J_by_label_and_replicate"][str(label)]
        assert pair["1"] - pair["0"] == pytest.approx(GAP[seed] * (label - 2))
    assert reading["sampled_panel_noise_estimate"] == pytest.approx(GAP[seed] * GAP_RMS)
    assert reading["sampled_max_minus_min"] == pytest.approx(
        max(SAMPLED[seed]) - min(SAMPLED[seed]))
    assert reading["sampled_ranking"][0] == 2  # .40 is the largest sampled mean here
    assert reading["sampled_ranking"][-1] in (0, 5)  # the tie at .30 goes to the lowest label last
    assert reading["sampled_best_constant"]["label"] == 2
    assert "replicate" in reading["sampled_best_constant"]["definition"]


def test_the_rank_correlation_and_the_two_leads():
    assert b10.spearman([1, 2, 3], [1, 2, 3]) == pytest.approx(1.)
    assert b10.spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.)
    assert b10.spearman([1, 1, 1], [3, 2, 1]) is None  # a constant side has no order
    assert b10.spearman([1, 2], [1]) is None
    # ties share their average rank: two equal values cannot order each other
    assert b10.spearman([1., 1., 2.], [1., 2., 3.]) == pytest.approx(.8660254037844387)
    values = {0: .30, 1: .34, 2: .40, 3: .32, 4: .31, 5: .30}
    assert b10.lead_over_the_others(values, 2) == pytest.approx(.40 - np.mean([.30, .34, .32, .31,
                                                                              .30]))
    assert b10.lead_over_the_next_best(values, 2) == pytest.approx(.40 - .34)
    assert b10.lead_over_the_next_best(values, 4) == pytest.approx(.31 - .40)  # not the best: < 0
    assert b10.noise_estimate({0: .01, 1: -.01, 2: .01, 3: -.01}) == pytest.approx(.01)
    assert b10.noise_estimate({0: 0., 1: 0.}) == 0.


def test_the_block_outcome_is_e1_e2_or_neither():
    assert b10.block_outcome({"sampled_max_minus_min": .04}) == "E1"
    assert b10.block_outcome({"sampled_max_minus_min": .09}) == "E2"
    assert b10.block_outcome({"sampled_max_minus_min": .06}) == "neither"
    assert b10.block_outcome({"sampled_max_minus_min": b10.E1_MARGIN}) == "neither"
    assert b10.block_outcome({"sampled_max_minus_min": b10.E2_MARGIN}) == "neither"
    assert b10.block_outcome({"sampled_max_minus_min": None}) is None


# ---------------------------------------------------------------------------
# synthetic published summaries and `reduce`
# ---------------------------------------------------------------------------


def panel_record(name, value, histogram=None):
    scores = [float(value)] * WORLDS
    record = {"rule": name, "J_mean": float(np.mean(scores)), "J_world_scores": scores,
              "agent_label_histogram": list(histogram or [0] * 6),
              "team_label_histogram": [0] * 6,
              "agent_label_change_fraction": 0., "team_label_change_fraction": 0.,
              "decision_fraction": .1, "steps": 1000, "decision_steps": 100}
    label, replicate = b10.sampled_parts(name)
    if label is not None:
        record.update({
            "action_sampling": True, "replicate": replicate, "label": label,
            "label_rule": b09.constant_rule(label), "constant_label": label,
            "constant_team_label": label % 6,
            "executed_action_check": {
                "rows": 192, "rows_equal_to_the_mean_action": 0,
                "fraction_of_rows_differing_from_the_mean_action": 1.,
                "rms_executed_minus_mean_over_std_mean": 1.02,
                "within_the_std_tolerance": True},
            "action_sampling_record": {"torch_seed": 1, "deterministic_executed": False}})
    return record


def probe_summary(seed, sha="synthetic-source", **overrides):
    """A published probe summary of this object, in the shape `reduce` reads."""
    measured = {b10.BASELINE_RULE: panel_record(b10.BASELINE_RULE, AS_TRAINED, HISTOGRAM)}
    for replicate in b10.REPLICATES:
        for label in range(6):
            name = b10.sampled_rule(label, replicate)
            measured[name] = panel_record(name, replicate_value(seed, label, replicate))
    reading = b10.sampled_reading({name: measured[name]["J_mean"] for name in b10.RULES},
                                  AS_TRAINED)
    summary = {
        "object_id": b10.OBJECT_ID, "command": "probe", "status": "complete",
        "block_seed": seed, "evaluation_seed": b10.BLOCKS[seed], "launch_sha": sha,
        "optimizer_steps": 0, "weights_record": {"sha256": f"sha-{seed}"},
        "faithful_load": {"faithful_load": True, "first_differing_world": None},
        "rules_measured": measured, "rules": list(b10.RULES),
        "action_standard_deviation": {"per_dimension": [2.9, 2.9, 2.9], "mean": 2.9},
        "sampled_max_minus_min": reading["sampled_max_minus_min"],
        "sampled_panel_noise_estimate": reading["sampled_panel_noise_estimate"],
        "wall_seconds": 900.}
    summary.update(overrides)
    return summary


def supplied(probe_sha="synthetic-source", b09_sha="b09-source"):
    probes = [probe_summary(seed, probe_sha) for seed in SEEDS]
    others = [b09tests.probe_summary(seed, b09_sha) for seed in SEEDS]
    return probes, others


def test_the_synthetic_inputs_agree_with_b09s_own_probe_shape():
    """The fixture itself: the two objects' `as_trained` panels must be one panel."""
    probes, others = supplied()
    for probe, other in zip(probes, others):
        assert probe["rules_measured"]["as_trained"]["J_world_scores"] == other[
            "rules_measured"]["as_trained"]["J_world_scores"]
        assert probe["weights_record"]["sha256"] == other["weights_record"]["sha256"]
    assert b09.probe_row(others[0])["J_by_rule"]["constant_2"] == pytest.approx(
        MEAN_ACTION[SEEDS[0]][2])


def test_reduce_reads_three_probes_beside_b09s_three(tmp_path):
    probes, others = supplied()
    result = b10.reduce_inputs(probes, others)
    assert result["status"] == "complete" and result["object_id"] == b10.OBJECT_ID
    assert result["blocks_read"] == 3 and result["invalid_probes"] == {}
    assert result["invalid_b09_probes"] == {}
    assert result["probe_launch_sha"] == "synthetic-source"
    assert result["b09_probe_launch_sha"] == "b09-source"
    assert result["rules"] == list(b10.RULES) and result["b09_rules"] == list(b09.RULES)

    for index, block in enumerate(result["blocks"]):
        seed = SEEDS[index]
        assert block["status"] == "complete" and block["weights_match"] is True
        assert block["as_trained_identical_to_b09"] is True
        assert block["J_as_trained"] == pytest.approx(AS_TRAINED) == block["b09_J_as_trained"]
        for label in range(6):
            assert block["mean_action_J_by_label"][str(label)] == pytest.approx(
                MEAN_ACTION[seed][label])
            assert block["sampled_J_by_label"][str(label)] == pytest.approx(SAMPLED[seed][label])
            assert block["sampled_minus_mean_action_by_label"][str(label)] == pytest.approx(
                SAMPLED[seed][label] - MEAN_ACTION[seed][label])
            assert block["replicate_difference_by_label"][str(label)] == pytest.approx(
                GAP[seed] * (label - 2))
        assert block["sampled_max_minus_min"] == pytest.approx(
            max(SAMPLED[seed]) - min(SAMPLED[seed]))
        assert block["mean_action_max_minus_min"] == pytest.approx(
            max(MEAN_ACTION[seed]) - min(MEAN_ACTION[seed]))
        assert block["sampled_max_minus_min_minus_mean_action_max_minus_min"] == pytest.approx(
            block["sampled_max_minus_min"] - block["mean_action_max_minus_min"])
        assert block["sampled_panel_noise_estimate"] == pytest.approx(GAP[seed] * GAP_RMS)
        assert block["sampled_max_minus_min_matches_the_published_one"] is True
        assert block["best_mean_action_label"] == MEAN_ACTION[seed].index(max(MEAN_ACTION[seed]))
        assert block["action_standard_deviation"] == [2.9, 2.9, 2.9]
        assert block["worlds"] == WORLDS

    # 772803: the sampled order is B09's own, so the ranks agree exactly
    first = result["blocks"][0]
    assert first["mean_action_ranking"] == [2, 3, 1, 0, 4, 5] == first["sampled_ranking"]
    assert first["rank_correlation"] == pytest.approx(1.)
    assert first["best_label_is_b09s"] is True
    # 773003: the sampled order is B09's reversed
    last = result["blocks"][2]
    assert last["sampled_ranking"] == list(reversed(last["mean_action_ranking"]))
    assert last["rank_correlation"] == pytest.approx(-1.)
    assert last["best_label_is_b09s"] is False
    # 772903: two labels tie under sampling, so the correlation is the tie-corrected one
    middle = result["blocks"][1]
    assert middle["rank_correlation"] == pytest.approx(13.5 / (297.5 ** .5))
    assert middle["best_mean_action_label"] == 2
    assert middle["best_mean_action_label_lead_under_mean_actions"] == pytest.approx(
        .35 - np.mean([.30, .33, .29, .31, .28]))
    assert middle["best_mean_action_label_lead_under_sampling"] == pytest.approx(
        .40 - np.mean([.30, .34, .32, .31, .30]))
    assert middle["best_mean_action_label_lead_over_the_second_best_sampled_label"] == (
        pytest.approx(.40 - .34))

    # across the blocks, in B08's own working-model wording
    assert result["sampled_max_minus_min"]["available_blocks"] == 3
    assert result["sampled_max_minus_min"]["mean"] == pytest.approx(
        np.mean([max(SAMPLED[seed]) - min(SAMPLED[seed]) for seed in SEEDS]))
    assert "iid-normal paired block differences" in result["sampled_max_minus_min"]["working_model"]
    assert result["rank_correlation"]["available_blocks"] == 3
    assert result["sampled_panel_noise_estimate"]["mean"] == pytest.approx(
        np.mean([GAP[seed] * GAP_RMS for seed in SEEDS]))
    assert result["sampled_minus_mean_action_label_2"]["available_blocks"] == 3
    assert result["one_sampled_best_label_across_blocks"] is None  # 2, 2 and 5 here
    assert result["blocks_where_the_sampled_best_label_is_b09s"] == [772803, 772903]
    assert result["best_label_by_block"]["773003"] == {"mean_action": 1, "sampled": 5}
    # no verdict strings: numbers, definitions and limits only
    text = json.dumps(result).lower()
    for word in ("verdict", "confirmed", "the label matters", "invisible under training noise\","):
        assert word not in text


def test_the_prediction_counts_are_the_declared_statements(tmp_path):
    probes, others = supplied()
    predictions = b10.reduce_inputs(probes, others)["predictions"]
    spread = predictions["E1_the_sampled_spread_is_below_the_margin_on_every_block"]
    assert spread["blocks_considered"] == SEEDS and spread["blocks_read"] == 3
    assert spread["blocks_holding"] == 1  # .03 < .05 on 772803 only
    assert spread["per_block"]["772803"]["holds"] is True
    assert spread["per_block"]["772903"]["value"] == pytest.approx(.10)
    lead = predictions["E1_the_best_mean_action_labels_sampled_lead_on_772903_is_below_the_margin"]
    assert lead["blocks_considered"] == [772903] and lead["blocks_read"] == 1
    assert lead["blocks_holding"] == 0  # .40 - .34 = .06 is not below .05
    assert lead["per_block"]["772903"]["value"] == pytest.approx(.06)
    visible = predictions["E2_the_sampled_spread_is_above_the_margin_on_every_block"]
    assert visible["blocks_considered"] == SEEDS and visible["blocks_holding"] == 1
    assert visible["per_block"]["772903"]["holds"] is True
    assert predictions["outcome_by_block"] == {"772803": "E1", "772903": "E2", "773003": "neither"}
    assert "neither E1 nor E2" in predictions["counting_note"]
    assert "not a weight of evidence" in predictions["counting_note"]

    # a block that is not read is counted as not read, and holds nothing
    damaged = copy.deepcopy(probes)
    damaged[1]["status"] = "incomplete"
    predictions = b10.reduce_inputs(damaged, others)["predictions"]
    assert predictions["E1_the_sampled_spread_is_below_the_margin_on_every_block"][
        "blocks_read"] == 2
    lead = predictions["E1_the_best_mean_action_labels_sampled_lead_on_772903_is_below_the_margin"]
    assert lead["per_block"]["772903"] == {"read": False, "holds": None, "value": None}
    assert "772903" not in predictions["outcome_by_block"]


def test_reduce_refuses_a_block_that_is_not_b09s_own_checkpoint_and_panel(tmp_path):
    probes, others = supplied()
    damaged = copy.deepcopy(probes)
    damaged[0]["weights_record"] = {"sha256": "sha-of-another-checkpoint"}
    result = b10.reduce_inputs(damaged, others)
    assert result["status"] == "incomplete" and result["blocks_read"] == 2
    block = result["blocks"][0]
    assert block["weights_match"] is False and block["status"] == "incomplete"
    assert "sha256" in block["missing_or_invalid"]["weights"]
    assert "sampled_J_by_label" not in block

    damaged = copy.deepcopy(probes)
    scores = damaged[2]["rules_measured"]["as_trained"]["J_world_scores"]
    damaged[2]["rules_measured"]["as_trained"]["J_world_scores"] = [scores[0] + 1e-12] + scores[1:]
    result = b10.reduce_inputs(damaged, others)
    assert result["status"] == "incomplete"
    block = result["blocks"][2]
    assert block["weights_match"] is True and block["as_trained_identical_to_b09"] is False
    assert "not the same policy on the same worlds" in block["missing_or_invalid"]["as_trained"]

    # a B09 probe that was not supplied, and one B09's own reader refuses
    result = b10.reduce_inputs(probes, others[1:])
    assert result["blocks"][0]["missing_or_invalid"]["b09_probe"] == "not supplied"
    damaged = copy.deepcopy(others)
    damaged[1]["faithful_load"] = {"faithful_load": False, "first_differing_world": 3}
    result = b10.reduce_inputs(probes, damaged)
    assert "faithful load" in result["invalid_b09_probes"][str(SEEDS[1])]
    assert result["blocks"][1]["status"] == "incomplete"


def test_reduce_refuses_mixed_launch_shas_duplicates_and_unreadable_probes(tmp_path):
    probes, others = supplied()
    damaged = copy.deepcopy(probes)
    damaged[1]["launch_sha"] = "another-source"
    with pytest.raises(ValueError, match="mixed launch shas among the probes"):
        b10.reduce_inputs(damaged, others)
    with pytest.raises(ValueError, match="duplicate probe block"):
        b10.reduce_inputs(probes + [copy.deepcopy(probes[0])], others)
    with pytest.raises(ValueError, match="duplicate B09 probe block"):
        b10.reduce_inputs(probes, others + [copy.deepcopy(others[0])])

    for mutate, message in (
            (lambda s: s.update(status="incomplete"), "incomplete probe"),
            (lambda s: s.update(object_id="OTHER"), "not a probe of this object"),
            (lambda s: s.update(command="fit"), "not a probe of this object"),
            (lambda s: s.update(optimizer_steps=1), "took an optimizer step"),
            (lambda s: s.update(evaluation_seed=1), "one of this object's three blocks"),
            (lambda s: s["rules_measured"].pop("sampled_constant_3_r1"), "thirteen panels"),
            (lambda s: s["rules_measured"]["sampled_constant_0_r0"].update(action_sampling=False),
             "does not record that it sampled"),
            (lambda s: s["rules_measured"]["sampled_constant_5_r1"].update(
                executed_action_check={"rows": 8, "rows_equal_to_the_mean_action": 8}),
             "no proof that it left the mean action"),
            (lambda s: s.update(faithful_load={"faithful_load": False}), "faithful load")):
        damaged = copy.deepcopy(probes)
        mutate(damaged[2])
        result = b10.reduce_inputs(damaged, others)
        assert result["status"] == "incomplete"
        assert message in result["invalid_probes"][str(SEEDS[2])]
        assert result["blocks"][2]["status"] == "incomplete"


def test_reduce_publishes_a_summary_through_main(tmp_path):
    probes, others = supplied()
    written = []
    for name, summaries in (("b10", probes), ("b09", others)):
        for summary in summaries:
            path = tmp_path / f"{name}_{summary['block_seed']}.json"
            path.write_text(json.dumps(summary), encoding="utf-8")
            written.append(path)
    out = tmp_path / "reduce"
    assert b10.main(["reduce", "--probes"] + [str(p) for p in written[:3]]
                    + ["--b09-probes"] + [str(p) for p in written[3:]]
                    + ["--output-root", str(out)]) == 0
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "complete" and result["blocks_read"] == 3
    assert result["input_probes"] == [str(p) for p in written[:3]]
    assert result["input_b09_probes"] == [str(p) for p in written[3:]]
    assert result["predictions"]["outcome_by_block"]["772903"] == "E2"
    # B08's tables are untouched by a reading command
    assert b08.ExecutionRule is not b09.MapExecutionRule
    assert all(name not in b08.RULE_DEFINITIONS for name in b09.MAP_RULES)
