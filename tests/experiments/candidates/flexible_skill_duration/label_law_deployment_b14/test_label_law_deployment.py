"""Unit checks of the deployment law, its draws, its guards and its readers.

No learner is constructed here: the law, the four panel streams, the rule's own step arithmetic,
the bind-and-restore, the fit reader's refusals, the faithful-load record and `reduce` are
exercised on synthetic inputs and on the published B13 fit records, so the arithmetic is pinned
independently of any panel.  The real tiny fit and its probe live beside this file in
`test_label_law_deployment_real_tiny.py`.
"""
import hashlib
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

import run_fsd_label_bandit_b13 as b13  # noqa: E402
import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_law_deployment_b14 as b14  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402

N_LABELS = b14.N_LABELS
N_AGENTS = 6
SEEDS = sorted(b14.BLOCKS)
LAUNCH_SHA = "0" * 40
FIT_SHA = "1" * 40
PUBLISHED = {arm: ROOT / "runs" / "flexible_skill_duration" / f"b13_{arm.lower()}_{SEEDS[0]}_a01"
             for arm in b14.ARMS}


# ---------------------------------------------------------------------------
# the law: B13's own, on the fit's own frozen estimate
# ---------------------------------------------------------------------------


def test_the_law_is_b13s_own_law_on_a_fixed_z():
    z = np.array([-1.2853613456588255, 1.4580878430089388, -2.4515246404376376,
                  4.458624712399041, -0.991289338991163, -1.1885372303203523])
    law, source = b13.label_law(b14.FrozenEstimate(z), b13.BANDIT_ARM)
    assert source == "softmax_z"
    soft = np.exp(z - z.max())
    soft = soft / soft.sum()
    expected = (b13.EXPLOIT_WEIGHT * soft
                + b13.FLOOR_WEIGHT * np.full(N_LABELS, 1. / N_LABELS))
    np.testing.assert_array_equal(law, expected)  # B13's own arithmetic, bit for bit
    assert float(law.sum()) == pytest.approx(1., abs=1e-15)
    assert float(law.min()) >= b13.LABEL_FLOOR - 1e-12
    assert b14.require_law(law) is not None
    # the constants are B13's and are not retyped here
    assert (b13.EXPLOIT_WEIGHT, b13.SOFTMAX_TEMPERATURE) == (.7, 1.)
    assert b13.FLOOR_WEIGHT == pytest.approx(.3) and b13.LABEL_FLOOR == pytest.approx(.05)


def test_require_law_refuses_a_law_that_is_not_the_declared_one():
    good = np.full(N_LABELS, 1. / N_LABELS)
    np.testing.assert_array_equal(b14.require_law(good), good)
    with pytest.raises(ValueError, match="not a vector"):
        b14.require_law(np.full(N_LABELS + 1, 1. / (N_LABELS + 1)))
    with pytest.raises(ValueError, match="does not sum to one"):
        b14.require_law(np.full(N_LABELS, .1))
    below = np.array([.75, .04, .05, .05, .055, .055])
    assert float(below.sum()) == pytest.approx(1.)
    with pytest.raises(ValueError, match="below B13's declared floor"):
        b14.require_law(below)


@pytest.mark.parametrize("arm", sorted(b14.ARMS))
def test_the_estimate_is_the_fits_own_final_one_and_the_law_follows_it(arm):
    """The published B13 fits of block 772803, read as the probe reads them."""
    summary = json.loads((PUBLISHED[arm] / "summary.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for line in
               (PUBLISHED[arm] / "bandit.jsonl").read_text(encoding="utf-8").strip().splitlines()]
    estimate = b14.fit_estimate(summary, records)
    last = records[-1]
    assert estimate["rollout"] == b13.ROLLOUTS == int(last["rollout"])
    assert estimate["z"] == last["estimate"]["z"]  # exactly the z the fit recorded
    assert estimate["beta_hat"] == last["estimate"]["beta_hat"]
    assert estimate["z_recomputed_from_beta_and_standard_error_matches"] is True
    law, _source = b13.label_law(b14.FrozenEstimate(estimate["z"]), b13.BANDIT_ARM)
    assert estimate["q"] == law.tolist()
    assert estimate["max_q"] == max(estimate["q"]) > 1. / N_LABELS
    if arm == b13.BANDIT_ARM:
        # the fit executed this law itself: exact list equality with its own record
        assert last["q_next_source"] == "softmax_z"
        assert estimate["q_matches_recorded_q_next"] is True
        assert estimate["q"] == last["q_next"]
    else:
        assert last["q_next_source"] == "uniform"
        assert estimate["q_matches_recorded_q_next"] is None
        assert "passively" in estimate["q_comparison_note"]


def test_the_estimate_reader_refuses_a_record_that_is_not_the_fits_own():
    summary = json.loads((PUBLISHED[b13.BANDIT_ARM] / "summary.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for line in
               (PUBLISHED[b13.BANDIT_ARM] / "bandit.jsonl").read_text(
                   encoding="utf-8").strip().splitlines()]
    b14.fit_estimate(summary, records)

    tampered = [dict(record) for record in records]
    estimate = dict(tampered[-1]["estimate"])
    estimate["z"] = [value + 1. for value in estimate["z"]]
    tampered[-1] = dict(tampered[-1], estimate=estimate)
    with pytest.raises(ValueError, match="not `beta_hat / standard_error`"):
        b14.fit_estimate(summary, tampered)

    short = [dict(record) for record in records[:-1]]
    with pytest.raises(ValueError, match="last estimator record is rollout 44, not 45"):
        b14.fit_estimate(summary, short)

    moved = [dict(record) for record in records]
    moved[-1] = dict(moved[-1], q_next=[1. / N_LABELS] * N_LABELS, q_next_source="softmax_z")
    with pytest.raises(ValueError, match="not the law the fit itself executed"):
        b14.fit_estimate(summary, moved)

    disagreeing = dict(summary)
    disagreeing["label_bandit_final"] = dict(summary["label_bandit_final"],
                                             z=[0.] * N_LABELS)
    with pytest.raises(ValueError, match="final state and its last estimator record disagree"):
        b14.fit_estimate(disagreeing, records)


# ---------------------------------------------------------------------------
# a stand-in evaluator, and the rules' own step arithmetic
# ---------------------------------------------------------------------------


class FakeAgent:
    """Only the attributes B08's execution rule and this object's step arithmetic touch."""

    D2_CAUSE_RESET = 0
    D2_CAUSE_CAP = 1

    def __init__(self, *, lanes=8):
        self.config = types.SimpleNamespace(n_agents=N_AGENTS, n_z=N_LABELS, n_Z=N_LABELS)
        self.d2_enabled = True
        self.d2_cost_c = self.d2_cost_c_Z = float("inf")
        self.lanes = lanes
        self.env_agent_skills = {lane: np.full(N_AGENTS, -1, dtype=np.int64)
                                 for lane in range(lanes)}
        self.env_team_skills = {lane: 0 for lane in range(lanes)}
        self._d2_last_step = None

    def _batched_assign_skills(self, *args, **kwargs):
        """The frozen call the rule wraps; the rule always calls it first and unchanged."""
        raise AssertionError("the stand-in evaluator's frozen assignment was called")

    def at_step(self, step, *, cap=10):
        """The frozen `_d2_last_step` of one panel step: a decision every `cap` steps."""
        decides = step % cap == 0
        self._d2_last_step = {
            "sampled_mask": np.full((self.lanes, N_AGENTS), decides, dtype=bool),
            "sample_Z": np.full(self.lanes, decides, dtype=bool),
            "team_cause": np.full(self.lanes, self.D2_CAUSE_RESET if step == 0
                                  else self.D2_CAUSE_CAP, dtype=np.int64)}
        return decides


def drive(rule, agent, *, steps=200, cap=10):
    """Run one rule over a panel of `steps` steps with the frozen caps cadence."""
    team = np.zeros(agent.lanes, dtype=np.int64)
    agents = np.zeros((agent.lanes, N_AGENTS), dtype=np.int64)
    executed = []
    for step in range(steps):
        agent.at_step(step, cap=cap)
        team, agents = rule._step(team, agents)
        executed.append(agents.copy())
    return np.stack(executed)


def law_of(z=(2., -1., .5, 0., -.5, 1.)):
    return b13.label_law(b14.FrozenEstimate(np.asarray(z, dtype=np.float64)),
                         b13.BANDIT_ARM)[0]


def test_the_law_panel_draws_follow_q_and_differ_between_replicates_while_reproducible():
    law = law_of()
    executed = {}
    with b14.bound_rules(law):
        for replicate in b14.REPLICATES:
            name = b14.panel_rule(b14.LAW_RULE, replicate)
            for repeat in range(2):
                agent = FakeAgent(lanes=16)
                rule = b14.DeploymentRule(name, agent,
                                          generator=b08.label_generator(782803, name))
                executed[(name, repeat)] = drive(rule, agent, steps=500)
                if repeat == 0:
                    record = rule.measures()
    # the same replicate is reproducible, and the two replicates are different draws
    for replicate in b14.REPLICATES:
        name = b14.panel_rule(b14.LAW_RULE, replicate)
        np.testing.assert_array_equal(executed[(name, 0)], executed[(name, 1)])
    first = executed[(b14.panel_rule(b14.LAW_RULE, "a"), 0)]
    second = executed[(b14.panel_rule(b14.LAW_RULE, "b"), 0)]
    assert not np.array_equal(first, second)

    # the executed labels follow q: 50 decisions x 16 lanes x 6 agents = 4,800 draws per panel
    for values in (first, second):
        decisions = values[::10]
        shares = np.bincount(decisions.reshape(-1), minlength=N_LABELS) / decisions.size
        assert decisions.size == 50 * 16 * N_AGENTS
        np.testing.assert_allclose(shares, law, atol=.02)
        assert int(np.argmax(shares)) == int(np.argmax(law))
    # and the record carries the law it deployed and the shares it executed
    assert record["law"] == law.tolist() and record["law_source"] == "b13_softmax_z"
    assert record["max_q"] == float(law.max())
    np.testing.assert_allclose(record["decision_label_shares"], law, atol=.02)
    assert record["decision_positions"] == 50 * 16 * N_AGENTS


def test_the_uniform_replicate_panels_are_b08s_own_rule_under_a_new_stream():
    """`uniform_every_10_{a,b}` is B08's `uniform_every_10`; only the stream is this object's."""
    name = b14.panel_rule(b14.UNIFORM_RULE, "a")
    seeded = lambda: np.random.default_rng([782803, 7])
    theirs_agent, mine_agent = FakeAgent(), FakeAgent()
    theirs = b08.ExecutionRule(b14.UNIFORM_RULE, theirs_agent, generator=seeded())
    with b14.bound_rules(None):
        mine = b14.DeploymentRule(name, mine_agent, generator=seeded())
        mine_executed = drive(mine, mine_agent)
        record = mine.measures()
    theirs_executed = drive(theirs, theirs_agent)
    np.testing.assert_array_equal(mine_executed, theirs_executed)
    assert record["law"] is None and record["law_source"] == "uniform"
    assert record["agent_label_histogram"] == theirs.measures()["agent_label_histogram"]
    assert record["agent_label_change_fraction"] == theirs.measures()[
        "agent_label_change_fraction"]


def test_the_boundaries_of_the_law_panel_are_the_boundaries_of_the_uniform_panel():
    law = law_of()
    indices, histograms = {}, {}
    with b14.bound_rules(law):
        for name in b14.PANEL_RULES:
            agent = FakeAgent()
            rule = b14.DeploymentRule(name, agent, generator=b08.label_generator(782803, name))
            executed = drive(rule, agent, steps=200)
            record = rule.measures()
            indices[name] = record["decision_step_indices"]
            histograms[name] = record["agent_label_histogram"]
            # between decisions the drawn labels are held, so the executed label only moves at a
            # boundary: that is the same cadence the frozen caps impose on `uniform_every_10`
            for step in range(1, 200):
                moved = not np.array_equal(executed[step], executed[step - 1])
                assert moved <= (step % 10 == 0)
    assert len({tuple(value) for value in indices.values()}) == 1
    assert indices[b14.PANEL_RULES[0]] == list(range(0, 200, 10))
    for name in b14.PANEL_RULES:
        assert sum(histograms[name]) == 200 * 8 * N_AGENTS


def test_the_panel_streams_are_dedicated_distinct_and_not_the_fits_own():
    draw = lambda generator: generator.integers(0, N_LABELS, size=(8, N_AGENTS))
    streams = {name: draw(b14.label_generator(782803, name)) for name in b14.PANEL_RULES}
    for name, values in streams.items():
        np.testing.assert_array_equal(values, draw(b14.label_generator(782803, name)))
        assert not np.array_equal(values, draw(b14.label_generator(782903, name)))
        # never the fit's own panel stream, which the faithful-load rerun alone uses
        assert not np.array_equal(
            values, draw(b14._orig_label_generator(782803, b14.UNIFORM_RULE)))
    pairs = list(streams.values())
    for index, first in enumerate(pairs):
        for second in pairs[index + 1:]:
            assert not np.array_equal(first, second)
    # a foreign rule name is delegated to B08's own constructor, unchanged
    np.testing.assert_array_equal(draw(b14.label_generator(782803, "uniform_every_step")),
                                  draw(b08.label_generator(782803, "uniform_every_step")))

    # and the draws touch no global stream
    random.seed(7)
    np.random.seed(7)
    torch.manual_seed(7)
    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    state = np.random.get_state()
    digest.update(str(state[0]).encode("utf-8"))
    digest.update(np.ascontiguousarray(state[1]).tobytes())
    digest.update(torch.get_rng_state().numpy().tobytes())
    before = digest.hexdigest()
    law = law_of()
    with b14.bound_rules(law):
        for name in b14.PANEL_RULES:
            agent = FakeAgent()
            rule = b14.DeploymentRule(name, agent, generator=b08.label_generator(782803, name))
            drive(rule, agent, steps=50)
    after = hashlib.sha256()
    after.update(repr(random.getstate()).encode("utf-8"))
    state = np.random.get_state()
    after.update(str(state[0]).encode("utf-8"))
    after.update(np.ascontiguousarray(state[1]).tobytes())
    after.update(torch.get_rng_state().numpy().tobytes())
    assert after.hexdigest() == before


# ---------------------------------------------------------------------------
# the bind-and-restore, and the instance-level wrapper
# ---------------------------------------------------------------------------


def test_bound_rules_restores_b08s_tables_including_on_an_exception():
    definitions = dict(b08.RULE_DEFINITIONS)
    random_rules, rule_class = b08.RANDOM_RULES, b08.ExecutionRule
    generator, current = b08.label_generator, dict(b14.CURRENT)
    law = law_of()

    with b14.bound_rules(law):
        assert b08.ExecutionRule is b14.DeploymentRule
        assert b08.label_generator is b14.label_generator
        assert set(b14.PANEL_RULES) <= set(b08.RANDOM_RULES)
        assert set(b14.PANEL_RULES) <= set(b08.RULE_DEFINITIONS)
        assert b14.CURRENT["law"] == law.tolist()
        assert b08.RULES == ("as_trained", "frozen_episode", "uniform_every_step",
                             "uniform_every_10")  # B08's own rule list is never touched
        assert "uniform_every_step" in b08.RULE_CAPS and len(b08.RULE_CAPS) == 1
    for restored, original in ((b08.ExecutionRule, rule_class),
                               (b08.RANDOM_RULES, random_rules),
                               (b08.label_generator, generator)):
        assert restored is original
    assert b08.RULE_DEFINITIONS == definitions
    assert b14.CURRENT == current

    with pytest.raises(RuntimeError, match="inside the binding"):
        with b14.bound_rules(law):
            raise RuntimeError("inside the binding")
    assert b08.ExecutionRule is rule_class and b08.label_generator is generator
    assert b08.RANDOM_RULES is random_rules and b08.RULE_DEFINITIONS == definitions
    assert b14.CURRENT == current


def test_a_law_panel_cannot_be_built_without_the_declared_law():
    with b14.bound_rules(None):
        with pytest.raises(ValueError, match="not a vector"):
            b14.DeploymentRule(b14.panel_rule(b14.LAW_RULE, "a"), FakeAgent(),
                               generator=np.random.default_rng(0))
        # the uniform replicate panels need no law
        b14.DeploymentRule(b14.panel_rule(b14.UNIFORM_RULE, "a"), FakeAgent(),
                           generator=np.random.default_rng(0))
    with pytest.raises(ValueError, match="unknown execution rule"):
        with b14.bound_rules(None):
            b14.DeploymentRule("law_every_10_c", FakeAgent(), generator=np.random.default_rng(0))


def test_the_rule_is_an_instance_attribute_and_comes_off_in_a_finally():
    agent = FakeAgent()
    with b14.bound_rules(law_of()):
        rule = b14.DeploymentRule(b14.panel_rule(b14.LAW_RULE, "a"), agent,
                                  generator=np.random.default_rng(0))
        with rule.attached():
            assert "_batched_assign_skills" in agent.__dict__
        assert "_batched_assign_skills" not in agent.__dict__
        assert "_batched_assign_skills" not in type(agent).__dict__.get("__slots__", ())

        with pytest.raises(RuntimeError, match="inside the panel"):
            with rule.attached():
                raise RuntimeError("inside the panel")
        assert "_batched_assign_skills" not in agent.__dict__

        # B08's own guard: a finite interruption cost would move the decision boundary
        agent.d2_cost_c = .25
        with pytest.raises(ValueError, match="infinite interruption costs"):
            with rule.attached():
                pass
        agent.d2_cost_c = float("inf")
        agent.d2_enabled = False
        with pytest.raises(ValueError, match="D2 route"):
            with rule.attached():
                pass


def test_the_run_time_rule_check_refuses_a_panel_that_did_not_deploy_its_rule():
    name = b14.panel_rule(b14.LAW_RULE, "a")
    record = {"rule": name, "panel_rule": name, "steps_recorded": 10, "lanes": 2,
              "n_agents": N_AGENTS, "agent_label_histogram": [20] * N_LABELS,
              "decision_step_indices": [0], "agent_label_change_fraction": .08,
              "law": [1. / N_LABELS] * N_LABELS}
    assert b14.check_rule_record(name, record) is record
    assert b14.check_rule_record("as_trained", {"rule": "as_trained"})  # a foreign rule is B08's
    with pytest.raises(ValueError, match="executed histogram covers"):
        b14.check_rule_record(name, dict(record, agent_label_histogram=[1] * N_LABELS))
    with pytest.raises(ValueError, match="took no decision"):
        b14.check_rule_record(name, dict(record, decision_step_indices=[]))
    with pytest.raises(ValueError, match="never changed an executed agent label"):
        b14.check_rule_record(name, dict(record, agent_label_change_fraction=0.))
    with pytest.raises(ValueError, match="no record of the law"):
        b14.check_rule_record(name, dict(record, law=None))


def test_the_share_check_is_recorded_and_never_raised():
    law = [.7, .06, .06, .06, .06, .06]
    shares = [.69, .062, .062, .062, .062, .062]
    record = {"executed_label_shares": shares, "law": law}
    check = b14.share_check(record)
    assert check["within_tolerance"] is True
    assert check["max_q"] == .7 and check["largest_executed_share"] == pytest.approx(.69)
    assert check["difference"] == pytest.approx(-.01)
    assert check["most_executed_label_is_argmax_q"] is True
    far = b14.share_check({"executed_label_shares": [.3, .14, .14, .14, .14, .14], "law": law})
    assert far["within_tolerance"] is False
    assert b14.share_check({"executed_label_shares": None, "law": law}) is None


# ---------------------------------------------------------------------------
# the fit this probe reads, and its refusals
# ---------------------------------------------------------------------------


@pytest.fixture
def fit_root(tmp_path):
    """A B13 fit root built from the published records of one fit, with a stand-in weights file.

    The weights are never loaded here: only the sidecar's recomputed sha256, the fit's own
    validation and the estimate reading are exercised, so a few bytes stand in for the real
    35 MB checkpoint, which is not in this checkout.
    """
    def build(arm=b13.UNIFORM_ARM, *, content=b"a stand-in checkpoint\n"):
        source = PUBLISHED[arm]
        root = tmp_path / f"b13_{arm.lower()}"
        root.mkdir(exist_ok=True)
        (root / "bandit.jsonl").write_bytes((source / "bandit.jsonl").read_bytes())
        weights = root / b14.WEIGHTS_NAME
        weights.write_bytes(content)
        digest = b08.file_sha256(weights)
        summary = json.loads((source / "summary.json").read_text(encoding="utf-8"))
        summary["final_weights"] = dict(summary["final_weights"], sha256=digest,
                                        bytes=weights.stat().st_size)
        sidecar = json.loads((source / "weights.json").read_text(encoding="utf-8"))
        sidecar.update(sha256=digest, bytes=weights.stat().st_size)
        (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        (root / b14.SIDECAR_NAME).write_text(json.dumps(sidecar), encoding="utf-8")
        return root
    return build


def rewrite(root, name, **fields):
    path = root / name
    value = json.loads(path.read_text(encoding="utf-8"))
    value.update(fields)
    path.write_text(json.dumps(value), encoding="utf-8")
    return value


def test_the_fit_reader_reads_a_complete_b13_fit_root(fit_root):
    root = fit_root(b13.UNIFORM_ARM)
    fit = b14.read_fit(root)
    assert fit["arm"] == b13.UNIFORM_ARM and fit["block_seed"] == SEEDS[0]
    assert fit["evaluation_seed"] == b14.BLOCKS[SEEDS[0]]
    assert fit["weights_record"]["sha256"] == b08.file_sha256(root / b14.WEIGHTS_NAME)
    assert len(fit["records"]) == b13.ROLLOUTS
    assert fit["estimate"]["q"] and len(fit["estimate"]["q"]) == N_LABELS
    entry, frozen = fit["reference_panel"], fit["reference_frozen_panel"]
    assert entry["rule"] == b14.UNIFORM_RULE == "uniform_every_10"
    assert int(entry["panel_rollouts"]) == b13.ROLLOUTS == 45
    assert entry["J_world_scores"] == frozen["native_scores_J"]
    assert len(entry["J_world_scores"]) == 32


def test_the_fit_reader_refuses_a_digest_mismatch_and_a_non_complete_fit(fit_root):
    root = fit_root(b13.UNIFORM_ARM)
    b14.read_fit(root)

    (root / b14.WEIGHTS_NAME).write_bytes(b"another checkpoint\n")
    with pytest.raises(ValueError, match="does not match the sha256"):
        b14.read_fit(root)

    root = fit_root(b13.UNIFORM_ARM)
    rewrite(root, "summary.json", status="incomplete")
    with pytest.raises(ValueError, match="is incomplete, not complete"):
        b14.read_fit(root)

    root = fit_root(b13.UNIFORM_ARM)
    rewrite(root, "summary.json", object_id="FSD_LABEL_MAP_B09")
    with pytest.raises(ValueError, match="is not a fit of FSD_LABEL_BANDIT_B13"):
        b14.read_fit(root)

    root = fit_root(b13.UNIFORM_ARM)
    rewrite(root, "summary.json", label_bandit_arm="D1280")
    with pytest.raises(ValueError, match="not one of B13's six planned fits"):
        b14.read_fit(root)

    root = fit_root(b13.UNIFORM_ARM)
    rewrite(root, b14.SIDECAR_NAME, arm=b13.BANDIT_ARM)
    with pytest.raises(ValueError, match="sidecar is not this fit's"):
        b14.read_fit(root)

    root = fit_root(b13.UNIFORM_ARM)
    (root / "bandit.jsonl").unlink()
    with pytest.raises(ValueError, match="does not exist"):
        b14.read_fit(root)

    # a fit whose coordinator took a step is B13's own refusal, through B13's own reader
    root = fit_root(b13.UNIFORM_ARM)
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    rewrite(root, "summary.json",
            optimizer_calls=dict(summary["optimizer_calls"], coordinator=3))
    with pytest.raises(ValueError, match="coordinator"):
        b14.read_fit(root)


def test_the_reference_panel_must_be_the_fits_own_last_uniform_panel(fit_root):
    root = fit_root(b13.BANDIT_ARM)
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    entry, _frozen = b14.fit_reference_panel(summary)
    assert entry["rule"] == b14.UNIFORM_RULE

    without = [run for run in summary["panel_runs"]
               if not (run["rule"] == b14.UNIFORM_RULE
                       and int(run["panel_rollouts"]) == b13.ROLLOUTS)]
    with pytest.raises(ValueError, match="exactly one uniform_every_10 panel"):
        b14.fit_reference_panel(dict(summary, panel_runs=without))

    extras = [panel for panel in summary["extra_panels"]
              if int(panel["panel_rollouts"]) != b13.ROLLOUTS]
    with pytest.raises(ValueError, match="frozen panel records"):
        b14.fit_reference_panel(dict(summary, extra_panels=extras))

    moved = [dict(panel) for panel in summary["extra_panels"]]
    index = next(position for position, panel in enumerate(moved)
                 if int(panel["panel_rollouts"]) == b13.ROLLOUTS)
    moved[index] = dict(moved[index],
                        native_scores_J=[0.] * len(moved[index]["native_scores_J"]))
    with pytest.raises(ValueError, match="do not carry the same world scores"):
        b14.fit_reference_panel(dict(summary, extra_panels=moved))


# ---------------------------------------------------------------------------
# the faithful load
# ---------------------------------------------------------------------------


def test_the_faithful_load_record_is_exact_equality_with_the_maximum_difference():
    reference = {"J_world_scores": [.41, .52, .33], "panel_rollouts": 45}
    same = b14.faithful_load_record({"J_world_scores": [.41, .52, .33], "J_mean": .42,
                                     "decision_steps": 1600}, reference)
    assert same["faithful_load"] is True and same["first_differing_world"] is None
    assert same["max_abs_difference"] == 0. and same["rerun_J_mean"] == .42
    assert same["worlds"] == same["reference_worlds"] == 3

    # one ulp is a failed load: the check is exact equality, unrelaxed
    drifted = b14.faithful_load_record(
        {"J_world_scores": [.41, np.nextafter(.52, 1.), .33], "J_mean": .42,
         "decision_steps": 1600}, reference)
    assert drifted["faithful_load"] is False and drifted["first_differing_world"] == 1
    assert 0. < drifted["max_abs_difference"] < 1e-15
    assert drifted["rerun_J_mean"] is None


def test_a_failed_faithful_load_writes_the_failed_status_and_no_scores(tmp_path, monkeypatch):
    """The contract of the failure path; the real rerun is exercised in the tiny-fit tests."""
    def fail(result, fit_root, out):
        result["faithful_load"] = {"faithful_load": False, "first_differing_world": 0,
                                   "max_abs_difference": .0123, "worlds": 32,
                                   "reference_panel_rollouts": 45}
        result["block_seed"], result["checkpoint_arm"] = SEEDS[0], b13.UNIFORM_ARM
        raise b14.FaithfulLoadFailure("the loaded weights do not reproduce the fit's own panel")

    monkeypatch.setattr(b14, "_run", fail)
    out = tmp_path / "probe"
    status = b14.run_probe(tmp_path / "fit", out, launch_sha=LAUNCH_SHA)
    assert status == 1
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "failed_faithful_load"
    assert "do not reproduce" in summary["failure"]
    assert summary["faithful_load"]["max_abs_difference"] == .0123
    assert summary["rules_measured"] is None and summary["J_by_rule"] is None
    assert summary["interpretation_limit"] and summary["wall_seconds"] >= 0.
    # and such a probe is never read as a result
    with pytest.raises(ValueError, match="incomplete probe: status failed_faithful_load"):
        b14.probe_row(summary)


# ---------------------------------------------------------------------------
# synthetic probes, and `reduce`
# ---------------------------------------------------------------------------


WORLDS = 8
BASE = np.linspace(.30, .50, WORLDS)


def fake_probe_summary(arm, seed, *, g_a, g_b, uniform_shift=.0, launch_sha=LAUNCH_SHA,
                       within=True, status="complete", object_id=b14.OBJECT_ID,
                       fit_launch_sha=FIT_SHA):
    """A production-shaped probe summary whose four panels carry known paired differences."""
    scores = {
        b14.panel_rule(b14.UNIFORM_RULE, "a"): BASE,
        b14.panel_rule(b14.UNIFORM_RULE, "b"): BASE + uniform_shift,
        b14.panel_rule(b14.LAW_RULE, "a"): BASE + g_a,
        b14.panel_rule(b14.LAW_RULE, "b"): BASE + uniform_shift + g_b}
    law = law_of().tolist()
    # the executed shares of a law panel follow q where the check holds, and are flat where it
    # does not (the largest share is then 1/6, far from this law's max q of about .43)
    shares = list(law) if within else [1. / N_LABELS] * N_LABELS
    measured = {}
    for name, values in scores.items():
        base_rule, replicate = b14.rule_parts(name)
        measured[name] = {
            "rule": name, "panel_rule": name, "base_rule": base_rule, "replicate": replicate,
            "J_mean": float(np.mean(values)), "J_world_scores": [float(v) for v in values],
            "agent_label_histogram": [100] * N_LABELS,
            "executed_label_shares": shares if base_rule == b14.LAW_RULE else [1. / N_LABELS] * 6,
            "decision_label_shares": shares if base_rule == b14.LAW_RULE else [1. / N_LABELS] * 6,
            "decision_steps": 1600, "decision_positions": 9600,
            "decision_step_indices": list(range(0, 500, 10)),
            "law": law if base_rule == b14.LAW_RULE else None,
            "evaluator_optimizer_calls": {name: 0 for name in b14.shared.NETWORKS}}
    checks = {name: b14.share_check(measured[name]) for name in b14.LAW_PANELS}
    return {
        "object_id": object_id, "card": b14.CARD, "command": "probe", "status": status,
        "failure": None, "launch_sha": launch_sha,
        "block_seed": seed, "checkpoint_arm": arm, "evaluation_seed": b14.BLOCKS[seed],
        "primary_group": arm == b14.PRIMARY_ARM,
        "fit": {"launch_sha": fit_launch_sha, "arm": arm, "block_seed": seed},
        "weights_record": {"sha256": "c" * 64},
        "weights_sha256_before": "c" * 64, "weights_sha256_after": "c" * 64,
        "weights_unchanged": True,
        "faithful_load": {"faithful_load": True, "max_abs_difference": 0.},
        "optimizer_steps": 0, "decision_boundaries_identical": True,
        "rules_measured": measured,
        "J_by_rule": {name: measured[name]["J_mean"] for name in b14.PANEL_RULES},
        "q": law, "estimate": {"q": law, "z": [0.] * N_LABELS},
        "share_checks": checks,
        "executed_label_shares": {name: measured[name]["executed_label_shares"]
                                  for name in b14.PANEL_RULES},
        "decision_steps": {name: 1600 for name in b14.PANEL_RULES},
        "wall_seconds": 900.}


def probes_for(gains, *, arm, **kwargs):
    """One probe per block of one arm; `gains` is {seed: (g_a, g_b)}."""
    return [fake_probe_summary(arm, seed, g_a=values[0], g_b=values[1], **kwargs)
            for seed, values in gains.items()]


def falls_short():
    primary = probes_for({SEEDS[0]: (.012, .008), SEEDS[1]: (.00, .00),
                          SEEDS[2]: (.025, .015)}, arm=b14.PRIMARY_ARM, uniform_shift=.004)
    secondary = probes_for({SEEDS[0]: (-.01, .01), SEEDS[1]: (.02, .00),
                            SEEDS[2]: (.00, -.02)}, arm=b14.SECONDARY_ARM)
    return primary + secondary


def test_reduce_reads_six_probes_and_groups_them_by_arm():
    result = b14.reduce_inputs(falls_short())
    assert result["status"] == "complete" and result["checkpoints_read"] == 6
    assert result["probe_launch_sha"] == LAUNCH_SHA and result["fit_launch_sha"] == FIT_SHA
    assert result["invalid_probes"] == {}
    assert result["object_id"] == b14.OBJECT_ID and result["card"] == b14.CARD
    assert sorted(result["groups"]) == sorted(b14.ARMS)
    assert result["groups"][b14.PRIMARY_ARM]["role"] == "primary"
    assert result["groups"][b14.SECONDARY_ARM]["role"] == "secondary"

    entry = [c for c in result["checkpoints"]
             if c["block_seed"] == SEEDS[0] and c["checkpoint_arm"] == b14.PRIMARY_ARM][0]
    assert entry["status"] == "complete" and entry["missing_or_invalid"] is None
    # G is the paired mean of the per-world differences, replicate by replicate
    assert entry["G_by_replicate"]["a"] == pytest.approx(.012)
    assert entry["G_by_replicate"]["b"] == pytest.approx(.008)
    assert entry["G"] == pytest.approx(.010)
    assert entry["replicate_difference"] == pytest.approx(.004)
    assert entry["G_positive"] is True and entry["G_at_or_above_the_margin"] is False
    assert entry["G_exceeds_twice_the_replicate_difference"] is True  # .010 > .008
    paired = entry["G_paired_by_replicate"]["a"]
    assert paired["worlds"] == WORLDS and paired["positive_worlds"] == WORLDS
    assert paired["sample_sd"] == pytest.approx(0., abs=1e-12)  # a constant per-world gain
    assert paired["paired_se"] == pytest.approx(0., abs=1e-12)
    # the two label-draw noise differences, paired by world
    assert entry[f"{b14.UNIFORM_RULE}_a_minus_b"]["mean"] == pytest.approx(-.004)
    assert entry[f"{b14.LAW_RULE}_a_minus_b"]["mean"] == pytest.approx(.012 - .008 - .004)
    assert entry["share_check_holds"] is True
    assert entry["share_check_by_panel"] == {name: True for name in b14.LAW_PANELS}

    group = result["groups"][b14.PRIMARY_ARM]
    assert group["checkpoints_read"] == 3
    assert group["mean_G"] == pytest.approx((.010 + .000 + .020) / 3.)
    assert group["G"]["available_blocks"] == 3
    assert group["blocks_with_G_at_or_above_the_margin"] == []
    assert sorted(group["G_by_block"]) == [str(seed) for seed in SEEDS]
    # the two groups are separate readings and are never pooled
    assert result["groups"][b14.SECONDARY_ARM]["mean_G"] == pytest.approx(0.)
    assert result["groups"][b14.SECONDARY_ARM]["blocks"] == SEEDS


def test_reduce_counts_the_two_declared_predictions_on_the_primary_group_alone():
    result = b14.reduce_inputs(falls_short())
    predictions = result["predictions"]
    assert predictions["DM_G_falls_short"]["holds"] is True
    assert predictions["DM_G_falls_short"]["blocks_at_or_above_the_margin"] == []
    assert predictions["REVERSAL"]["holds"] is False
    assert predictions["DM_G_falls_short"]["mean_G"] == pytest.approx(.01)
    assert predictions["intermediate_check"]["blocks_where_it_holds"] == SEEDS
    assert "No p-value is computed" in predictions["counting_note"]
    # the secondary group's own numbers never enter a prediction
    assert predictions["DM_G_falls_short"]["blocks_read"] == 3

    # a reversal: mean G >= .03 with two blocks whose gain beats twice the replicate difference
    reversal = probes_for({SEEDS[0]: (.05, .05), SEEDS[1]: (.06, .05), SEEDS[2]: (-.01, .01)},
                          arm=b14.PRIMARY_ARM)
    reversal += probes_for({seed: (.0, .0) for seed in SEEDS}, arm=b14.SECONDARY_ARM)
    predictions = b14.reduce_inputs(reversal)["predictions"]
    assert predictions["REVERSAL"]["mean_G"] == pytest.approx((.05 + .055 + .0) / 3.)
    assert predictions["REVERSAL"]["blocks_with_a_qualifying_gain"] == SEEDS[:2]
    assert predictions["REVERSAL"]["holds"] is True
    assert predictions["DM_G_falls_short"]["holds"] is False

    # a mean below the margin is not enough when two blocks are at or above it
    split = probes_for({SEEDS[0]: (.04, .04), SEEDS[1]: (.04, .04), SEEDS[2]: (-.06, -.06)},
                       arm=b14.PRIMARY_ARM)
    split += probes_for({seed: (.0, .0) for seed in SEEDS}, arm=b14.SECONDARY_ARM)
    predictions = b14.reduce_inputs(split)["predictions"]
    assert predictions["DM_G_falls_short"]["mean_G"] == pytest.approx(2. / 300.)
    assert predictions["DM_G_falls_short"]["blocks_at_or_above_the_margin"] == SEEDS[:2]
    assert predictions["DM_G_falls_short"]["holds"] is False
    assert predictions["REVERSAL"]["holds"] is False


def test_reduce_refuses_mixed_shas_and_duplicates_and_lists_an_invalid_probe():
    probes = falls_short()
    probes[0] = dict(probes[0], launch_sha="f" * 40)
    with pytest.raises(ValueError, match="mixed launch shas"):
        b14.reduce_inputs(probes)

    probes = falls_short()
    probes.append(probes[0])
    with pytest.raises(ValueError, match="duplicate checkpoint"):
        b14.reduce_inputs(probes)

    # an incomplete probe, a foreign object and an unfaithful load are listed, never dropped
    probes = falls_short()
    probes[0] = dict(probes[0], status="incomplete")
    probes[1] = dict(probes[1], object_id="FSD_LABEL_MAP_B09")
    probes[3] = dict(probes[3], faithful_load={"faithful_load": False})
    result = b14.reduce_inputs(probes)
    assert result["status"] == "incomplete" and result["checkpoints_read"] == 3
    assert result["probes_supplied"] == 6
    invalid = result["invalid_probes"]
    assert "incomplete probe" in invalid[f"{SEEDS[0]}:{b14.PRIMARY_ARM}"]
    assert "not a probe of this object" in invalid[f"{SEEDS[1]}:{b14.PRIMARY_ARM}"]
    assert "faithful load" in invalid[f"{SEEDS[0]}:{b14.SECONDARY_ARM}"]
    missing = [c for c in result["checkpoints"]
               if c["block_seed"] == SEEDS[0] and c["checkpoint_arm"] == b14.PRIMARY_ARM][0]
    assert missing["status"] == "incomplete"
    assert missing["missing_or_invalid"] == invalid[f"{SEEDS[0]}:{b14.PRIMARY_ARM}"]
    assert missing.get("G") is None
    assert result["groups"][b14.PRIMARY_ARM]["checkpoints_read"] == 1
    assert result["predictions"]["DM_G_falls_short"]["blocks_read"] == 1

    # nothing supplied at all: the predictions are unread, not False
    empty = b14.reduce_inputs([])
    assert empty["status"] == "incomplete" and empty["checkpoints_read"] == 0
    assert empty["predictions"]["DM_G_falls_short"]["holds"] is None
    assert empty["predictions"]["REVERSAL"]["holds"] is None
    assert empty["groups"][b14.PRIMARY_ARM]["mean_G"] is None


def test_a_probe_reader_refuses_a_probe_that_is_not_a_complete_reading():
    summary = fake_probe_summary(b14.PRIMARY_ARM, SEEDS[0], g_a=.01, g_b=.01)
    row = b14.probe_row(summary)
    assert row["checkpoint_arm"] == b14.PRIMARY_ARM and row["worlds"] == WORLDS
    assert row["J_by_rule"][b14.panel_rule(b14.LAW_RULE, "a")] == pytest.approx(
        float(np.mean(BASE)) + .01)

    for fields, message in (
            ({"optimizer_steps": 1}, "took an optimizer step"),
            ({"weights_unchanged": False}, "weights are unchanged"),
            ({"decision_boundaries_identical": False}, "frozen decision cadence"),
            ({"evaluation_seed": 1}, "evaluation seed"),
            ({"checkpoint_arm": "D1280"}, "six checkpoints"),
            ({"q": [.5, .5]}, "no record of the law"),
            ({"command": "fit"}, "not a probe of this object")):
        with pytest.raises(ValueError, match=message):
            b14.probe_row(dict(summary, **fields))
    short = {name: value for name, value in summary["rules_measured"].items()
             if name != b14.PANEL_RULES[-1]}
    with pytest.raises(ValueError, match="all four declared panels"):
        b14.probe_row(dict(summary, rules_measured=short))


def test_paired_difference_refuses_unpaired_inputs():
    with pytest.raises(ValueError, match="equal-length vectors"):
        b14.paired_difference([1., 2.], [1.])
    with pytest.raises(ValueError, match="equal-length vectors"):
        b14.paired_difference([], [])
    value = b14.paired_difference([.4, .5, .6], [.3, .5, .8])
    assert value["mean"] == pytest.approx((.1 + 0. - .2) / 3.)
    assert value["positive_worlds"] == 1 and value["negative_worlds"] == 1
    assert value["paired_se"] == pytest.approx(
        float(np.std([.1, 0., -.2], ddof=1)) / 3. ** .5)


# ---------------------------------------------------------------------------
# the command line
# ---------------------------------------------------------------------------


def test_the_command_line_refuses_a_launch_sha_that_is_not_head(tmp_path):
    never = tmp_path / "never"
    with pytest.raises(SystemExit):
        b14.main(["probe", "--fit-root", str(tmp_path), "--launch-sha", "f" * 40,
                  "--output-root", str(never)])
    with pytest.raises(SystemExit):  # the launch sha is required and recorded
        b14.main(["probe", "--fit-root", str(tmp_path), "--output-root", str(never)])
    assert not never.exists()


def test_the_declared_panels_and_sizes_are_the_notebook_entrys():
    assert b14.PANEL_RULES == ("uniform_every_10_a", "law_every_10_a",
                               "uniform_every_10_b", "law_every_10_b")
    assert b14.REPLICATES == ("a", "b") and b14.BASE_RULES == ("uniform_every_10", "law_every_10")
    assert b14.PRIMARY_ARM == "UNIFORM" and b14.SECONDARY_ARM == "BANDIT"
    assert b14.GAIN_MARGIN == .03 and b14.SHARE_TOLERANCE == .03
    assert b14.REVERSAL_BLOCKS == 2 and b14.SHORTFALL_BLOCKS == 1
    assert b14.REPLICATE_FACTOR == 2.
    assert sorted(b14.BLOCKS) == SEEDS == [772803, 772903, 773003]
    assert "three reused blocks" not in b14.INTERPRETATION_LIMIT  # the words, not the claim
    for phrase in ("Three reused blocks", "Mean actions only", "zero fits",
                   "each fit's own final one"):
        assert phrase in b14.INTERPRETATION_LIMIT
    assert b14.UNIFORM_RULE == b13.REFERENCE_RULE
    assert b09.BASELINE_RULE == "as_trained"  # this object never runs it; B08's tables stand
