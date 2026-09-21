"""Unit checks of the label bandit's arithmetic, its guards and its readers.

No learner is constructed here: the estimator, the law, the draws, the rule's own step arithmetic,
the commitment reader's refusals, the declared-difference guard and `reduce` are exercised on
synthetic inputs, so the arithmetic is pinned independently of any fit.  The real tiny fits live
beside this file in `test_label_bandit_real_tiny.py`.
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

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_commitment_visibility_b12 as b12  # noqa: E402
import run_fsd_label_bandit_b13 as bandit  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402

N_LABELS = bandit.N_LABELS
N_AGENTS = 6
SEEDS = sorted(bandit.BLOCKS)
LAUNCH_SHA = "0" * 40


# ---------------------------------------------------------------------------
# synthetic commitments
# ---------------------------------------------------------------------------


def synthetic_commitments(generator, *, lanes=16, n_positions=50, effect=None, noise=.01,
                          forbidden=()):
    """One rollout's commitments with a known additive label effect and position drift."""
    effect = np.zeros(N_LABELS) if effect is None else np.asarray(effect, dtype=np.float64)
    allowed = [label for label in range(N_LABELS) if label not in forbidden]
    rows = lanes * n_positions
    labels = np.asarray(generator.choice(allowed, size=(rows, N_AGENTS)), dtype=np.int64)
    counts = np.stack([(labels == label).sum(axis=1) for label in range(N_LABELS)],
                      axis=1).astype(np.float64)
    position = np.tile(np.arange(n_positions, dtype=np.int64), lanes)
    lane = np.repeat(np.arange(lanes, dtype=np.int64), n_positions)
    response = counts @ effect + .001 * position + noise * generator.standard_normal(rows)
    return {"rows": rows, "counts": counts, "position": position, "lane": lane,
            "clusters": lane, "response": response, "labels": labels, "n_agents": N_AGENTS,
            "n_positions": n_positions}


def direct_fit(commitments):
    """B12's own regression on the same table: the estimate one rollout implies."""
    fit = b12.label_regression(
        commitments["counts"], commitments["position"], commitments["response"],
        commitments["clusters"], n_positions=commitments["n_positions"], team_size=N_AGENTS,
        n_labels=N_LABELS)
    beta = np.asarray([fit["centred_coefficients"][str(c)] for c in range(N_LABELS)])
    var = np.asarray([fit["clustered_se"][str(c)] for c in range(N_LABELS)]) ** 2
    return fit, beta, var


# ---------------------------------------------------------------------------
# the estimator
# ---------------------------------------------------------------------------


def test_the_first_usable_rollout_is_the_estimate_and_later_ones_are_the_declared_combination():
    generator = np.random.default_rng(11)
    tables = [synthetic_commitments(generator, effect=[.03, 0., -.02, .01, 0., -.01])
              for _ in range(3)]
    fits = [direct_fit(table) for table in tables]
    estimator = bandit.LabelEstimator()

    record = estimator.update(tables[0], n_positions=tables[0]["n_positions"])
    assert record["rank_deficient"] is False and record["skipped_reason"] is None
    assert record["regression"]["full_rank"] is True
    assert record["regression"]["clusters"] == 16  # one lane-episode is one cluster
    np.testing.assert_array_equal(estimator.beta, fits[0][1])
    np.testing.assert_array_equal(estimator.variance, fits[0][2])
    assert estimator.rollouts_used == estimator.rollouts_seen == 1

    expected_beta, expected_var = fits[0][1].copy(), fits[0][2].copy()
    assert estimator.innovation is None and estimator.empirical_variance() is None
    expected_innovation = None
    for index in (1, 2):
        estimator.update(tables[index], n_positions=tables[index]["n_positions"])
        squared = float(np.mean((fits[index][1] - expected_beta) ** 2))  # before the combination
        expected_innovation = (squared if expected_innovation is None
                               else .8 * expected_innovation + .2 * squared)
        expected_beta = .8 * expected_beta + .2 * fits[index][1]
        expected_var = .64 * expected_var + .04 * fits[index][2]
        np.testing.assert_allclose(estimator.beta, expected_beta, rtol=0, atol=1e-15)
        np.testing.assert_allclose(estimator.variance, expected_var, rtol=0, atol=1e-20)
    assert estimator.rollouts_used == 3
    # the amended denominator: the larger of the clustered combination and the innovation-based
    # variance of the estimate (pooled over labels), so |z| can only be lowered by the amendment
    np.testing.assert_allclose(estimator.innovation, expected_innovation, rtol=1e-12, atol=0)
    gain = .2 / 1.8
    empirical = expected_innovation * gain / (1. + gain)
    np.testing.assert_allclose(estimator.empirical_variance(), empirical, rtol=1e-12, atol=0)
    denominator = np.maximum(np.sqrt(np.maximum(estimator.variance, empirical)), 1e-12)
    np.testing.assert_array_equal(estimator.z(), estimator.beta / denominator)
    declared = estimator.beta / np.maximum(np.sqrt(estimator.variance), 1e-12)
    assert (np.abs(estimator.z()) <= np.abs(declared) + 1e-15).all()
    assert bandit.EMA_WEIGHT == .8 and bandit.STANDARD_ERROR_FLOOR == 1e-12


def test_a_rollout_with_an_absent_label_is_skipped_and_the_estimate_keeps_its_value():
    generator = np.random.default_rng(12)
    good = synthetic_commitments(generator, effect=[.02] + [0.] * 5)
    estimator = bandit.LabelEstimator()
    estimator.update(good, n_positions=good["n_positions"])
    kept_beta, kept_var = estimator.beta.copy(), estimator.variance.copy()

    # a label that is never held anywhere gives an all-zero count column
    assert 3 != b12.DROP_LABEL
    deficient = synthetic_commitments(generator, forbidden=(3,))
    record = estimator.update(deficient, n_positions=deficient["n_positions"])
    assert record["absent_labels"] == [3]
    assert record["rank_deficient"] is True and "rank" in record["skipped_reason"]
    assert record["beta_rollout"] is not None  # the rollout's own numbers are still recorded
    np.testing.assert_array_equal(estimator.beta, kept_beta)
    np.testing.assert_array_equal(estimator.variance, kept_var)
    assert estimator.rollouts_seen == 2 and estimator.rollouts_used == 1
    assert len(estimator.skipped) == 1

    # the absence of the dropped label is skipped too, on the absent-label clause
    dropped = synthetic_commitments(generator, forbidden=(b12.DROP_LABEL,))
    record = estimator.update(dropped, n_positions=dropped["n_positions"])
    assert record["absent_labels"] == [b12.DROP_LABEL]
    assert record["skipped_reason"] is not None
    assert estimator.rollouts_seen == 3 and estimator.rollouts_used == 1
    np.testing.assert_array_equal(estimator.beta, kept_beta)


def test_the_estimator_reads_the_label_columns_it_declares():
    """Not a result: a planted additive effect, to pin that the imported regression is wired up."""
    generator = np.random.default_rng(13)
    table = synthetic_commitments(generator, effect=[.00, .02, -.03, .01, .00, .00], noise=.005)
    estimator = bandit.LabelEstimator()
    estimator.update(table, n_positions=table["n_positions"])
    assert estimator.argmax_label() == 1
    assert int(np.argmin(estimator.beta)) == 2


# ---------------------------------------------------------------------------
# the law
# ---------------------------------------------------------------------------


def test_the_law_is_uniform_until_an_estimate_exists_and_uniform_throughout_in_the_uniform_arm():
    estimator = bandit.LabelEstimator()
    for arm in bandit.ARMS:
        law, source = bandit.label_law(estimator, arm)
        np.testing.assert_allclose(law, np.full(N_LABELS, 1. / N_LABELS))
        assert source in ("uniform", "uniform_no_estimate")
    estimator.beta = np.array([1., 0., 0., 0., 0., 0.])
    estimator.variance = np.full(N_LABELS, 1e-2)
    estimator.rollouts_used = 1
    law, source = bandit.label_law(estimator, bandit.UNIFORM_ARM)
    assert source == "uniform"
    np.testing.assert_allclose(law, np.full(N_LABELS, 1. / N_LABELS))
    law, source = bandit.label_law(estimator, bandit.BANDIT_ARM)
    assert source == "softmax_z"
    assert law[0] > law[1]
    with pytest.raises(ValueError, match="unknown arm"):
        bandit.label_law(estimator, "D1280")


def test_the_softmax_is_stable_at_a_large_z_and_never_goes_below_the_declared_floor():
    estimator = bandit.LabelEstimator()
    estimator.rollouts_used = 1
    for scale in (1e3, 1e8, 1e300):
        estimator.beta = np.array([scale, -scale, 0., 0., 0., 0.])
        estimator.variance = np.full(N_LABELS, 1.)
        law, _source = bandit.label_law(estimator, bandit.BANDIT_ARM)
        assert np.isfinite(law).all()
        assert abs(float(law.sum()) - 1.) < 1e-12
        assert float(law.min()) >= bandit.LABEL_FLOOR - 1e-12
        assert law[0] == pytest.approx(bandit.EXPLOIT_WEIGHT + bandit.LABEL_FLOOR, abs=1e-12)
    # a zero estimate with a zero variance is the floored denominator, not a division by zero
    estimator.beta = np.zeros(N_LABELS)
    estimator.variance = np.zeros(N_LABELS)
    law, _source = bandit.label_law(estimator, bandit.BANDIT_ARM)
    np.testing.assert_allclose(law, np.full(N_LABELS, 1. / N_LABELS))
    assert bandit.EXPLOIT_WEIGHT == .7 and bandit.FLOOR_WEIGHT == pytest.approx(.3)
    assert bandit.LABEL_FLOOR == pytest.approx(.05)


# ---------------------------------------------------------------------------
# the draws
# ---------------------------------------------------------------------------


def global_rng_digest():
    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    state = np.random.get_state()
    digest.update(str(state[0]).encode("utf-8"))
    digest.update(np.ascontiguousarray(state[1]).tobytes())
    digest.update(str(state[2:]).encode("utf-8"))
    digest.update(torch.get_rng_state().numpy().tobytes())
    return digest.hexdigest()


def test_the_draws_are_reproducible_per_block_and_arm_and_touch_no_global_stream():
    law = np.array([.5, .1, .1, .1, .1, .1])
    draw = lambda generator: generator.choice(N_LABELS, size=(16, 6), p=law)
    seed = SEEDS[0]
    first = draw(bandit.label_generator(seed, bandit.BANDIT_ARM))
    second = draw(bandit.label_generator(seed, bandit.BANDIT_ARM))
    np.testing.assert_array_equal(first, second)
    other_arm = draw(bandit.label_generator(seed, bandit.UNIFORM_ARM))
    other_block = draw(bandit.label_generator(SEEDS[1], bandit.BANDIT_ARM))
    assert not np.array_equal(first, other_arm)
    assert not np.array_equal(first, other_block)

    random.seed(7)
    np.random.seed(7)
    torch.manual_seed(7)
    before = global_rng_digest()
    generator = bandit.label_generator(seed, bandit.BANDIT_ARM)
    for _ in range(50):
        generator.choice(N_LABELS, size=(16, 6), p=law)
    assert global_rng_digest() == before


# ---------------------------------------------------------------------------
# a stand-in learner, and the rule's own step arithmetic
# ---------------------------------------------------------------------------


class FakeAgent:
    """Only the attributes the rule and the commitment reader touch.

    `_batched_assign_skills` is defined on the class, exactly as the real learner's is, so the
    rule's "this learner already carries an instance-level assignment" guard means what it means on
    a real fit.
    """

    def __init__(self, *, lanes=2, cap=10, gamma=.99):
        self.config = types.SimpleNamespace(n_agents=N_AGENTS, n_z=N_LABELS, n_Z=N_LABELS,
                                            gamma=gamma)
        self.d2_enabled = True
        self.d2_cost_c = self.d2_cost_c_Z = float("inf")
        self.d2_age_feature = "off"
        self.d2_k_max = self.d2_k_Z = cap
        self.env_agent_skills = {lane: np.full(N_AGENTS, -1, dtype=np.int64)
                                 for lane in range(lanes)}
        self.env_team_skills = {lane: 0 for lane in range(lanes)}
        self._d2_last_step = {"sampled_mask": np.zeros((lanes, N_AGENTS), dtype=bool)}
        self.rollout_buffer = None

    def _batched_assign_skills(self, *args, **kwargs):
        """The frozen call the rule wraps; the rule always calls it first and unchanged."""
        raise AssertionError("the stand-in learner's frozen assignment was called")


def test_a_rule_draws_only_at_the_sampled_positions_and_writes_the_executed_labels_back():
    agent = FakeAgent(lanes=4)
    rule = bandit.LabelBanditRule(bandit.BANDIT_ARM, agent,
                                  generator=bandit.label_generator(SEEDS[0], bandit.BANDIT_ARM),
                                  horizon=3)
    rule.set_law(np.array([1., 0., 0., 0., 0., 0.]), "test")
    with rule.attached():
        assert "_batched_assign_skills" in agent.__dict__
        held = np.tile(np.array([2, 3, 4, 5, 0, 1]), (4, 1))
        for lane in range(4):
            agent.env_agent_skills[lane] = held[lane].copy()
        # step 0: every lane decides, so every position is redrawn
        agent._d2_last_step = {"sampled_mask": np.ones((4, N_AGENTS), dtype=bool)}
        executed = rule._step((None, None, np.zeros(4, dtype=np.int64)), {}, held.copy())
        assert (executed == 0).all()  # the law puts all its mass on label 0
        for lane in range(4):
            np.testing.assert_array_equal(agent.env_agent_skills[lane], executed[lane])
        assert rule.replaced == 4 * N_AGENTS and rule.draws == 4 * N_AGENTS
        # step 1: nothing decides, so the held labels come through unchanged
        agent._d2_last_step = {"sampled_mask": np.zeros((4, N_AGENTS), dtype=bool)}
        kept = rule._step((None, None, np.ones(4, dtype=np.int64)), {}, executed.copy())
        np.testing.assert_array_equal(kept, executed)
        assert rule.replaced == 4 * N_AGENTS  # no further position was replaced
        # a position that was not sampled but changed is a broken held label and is refused
        broken = executed.copy()
        broken[0, 0] = 5
        with pytest.raises(ValueError, match="held position"):
            rule._step((None, None, np.full(4, 2, dtype=np.int64)), {}, broken)
    assert "_batched_assign_skills" not in agent.__dict__


def test_the_rule_refuses_a_lane_that_is_not_at_the_rollout_step_and_an_over_long_rollout():
    agent = FakeAgent(lanes=2)
    rule = bandit.LabelBanditRule(bandit.UNIFORM_ARM, agent,
                                  generator=bandit.label_generator(SEEDS[0], bandit.UNIFORM_ARM),
                                  horizon=1)
    held = np.zeros((2, N_AGENTS), dtype=np.int64)
    with rule.attached():
        with pytest.raises(ValueError, match="not all at rollout step"):
            rule._step((None, None, np.array([0, 3])), {}, held.copy())
        rule._step((None, None, np.zeros(2, dtype=np.int64)), {}, held.copy())
        with pytest.raises(ValueError, match="more assignment calls in a rollout"):
            rule._step((None, None, np.ones(2, dtype=np.int64)), {}, held.copy())
    executed = rule.drain()
    assert executed.shape == (1, 2, N_AGENTS) and rule.step_index == 0
    with pytest.raises(ValueError, match="assignment calls, not"):
        rule.drain()  # a second drain: the fresh rollout has taken no calls yet


def test_the_rule_refuses_a_construction_it_is_not_defined_on():
    agent = FakeAgent(lanes=2)
    generator = bandit.label_generator(SEEDS[0], bandit.BANDIT_ARM)
    rule = bandit.LabelBanditRule(bandit.BANDIT_ARM, agent, generator=generator, horizon=2)
    agent.d2_cost_c = .25
    with pytest.raises(ValueError, match="infinite interruption costs"):
        with rule.attached():
            pass
    agent.d2_cost_c = float("inf")
    agent.d2_age_feature = "normalized"
    with pytest.raises(ValueError, match="age feature"):
        with rule.attached():
            pass
    agent.d2_age_feature = "off"
    agent.d2_k_max = 1
    with pytest.raises(ValueError, match="frozen caps"):
        with rule.attached():
            pass
    agent.d2_k_max = 10
    agent.d2_enabled = False
    with pytest.raises(ValueError, match="D2 route"):
        with rule.attached():
            pass
    agent.d2_enabled = True
    with rule.attached():
        assert "_batched_assign_skills" in agent.__dict__
    assert "_batched_assign_skills" not in agent.__dict__
    with pytest.raises(ValueError, match="unknown arm"):
        bandit.LabelBanditRule("D1280", agent, generator=generator)


# ---------------------------------------------------------------------------
# the commitments the estimator reads
# ---------------------------------------------------------------------------


def commitment_fixture(*, lanes=2, horizon=20, cap=10, seed=5, gamma=.99):
    """A stand-in rollout buffer whose D2 tables are the cadence's, and the tape beside it."""
    generator = np.random.default_rng(seed)
    rewards = generator.normal(.07, .01, size=(horizon, lanes))
    starts = list(range(0, horizon, cap))
    labels = {(lane, start): generator.integers(0, N_LABELS, size=N_AGENTS)
              for lane in range(lanes) for start in starts}
    team_valid = np.zeros((horizon, lanes), dtype=bool)
    agent_valid = np.zeros((horizon, lanes, N_AGENTS), dtype=bool)
    sampled = np.zeros((horizon, lanes, N_AGENTS), dtype=bool)
    skills = np.full((horizon, lanes, N_AGENTS), -1, dtype=np.int64)
    elapsed = np.zeros((horizon, lanes), dtype=np.int64)
    reward = np.zeros((horizon, lanes), dtype=np.float64)
    executed = np.full((horizon, lanes, N_AGENTS), -1, dtype=np.int64)
    for lane in range(lanes):
        for start in starts:
            length = min(cap, horizon - start)
            team_valid[start, lane] = True
            agent_valid[start, lane] = True
            sampled[start, lane] = True
            skills[start, lane] = labels[(lane, start)]
            executed[start, lane] = labels[(lane, start)]
            elapsed[start, lane] = length
            window = rewards[start:start + length, lane]
            reward[start, lane] = float(
                (np.power(gamma, np.arange(window.size)) * window).sum())
    agent = FakeAgent(lanes=lanes, cap=cap, gamma=gamma)
    agent.rollout_buffer = types.SimpleNamespace(
        get_d2_tables=lambda num_steps=None: {
            "team_valid": team_valid, "agent_valid": agent_valid, "sampled_mask": sampled,
            "agent_skills": skills, "team_elapsed": elapsed, "team_reward": reward})
    return agent, rewards, executed, labels


def test_the_commitment_reader_returns_the_cadences_table_and_the_declared_response():
    agent, rewards, executed, labels = commitment_fixture()
    table = bandit.rollout_commitments(agent, rewards, executed, horizon=20, cap=10, lanes=2)
    assert table["rows"] == 4 and table["n_positions"] == 2
    # the rows come out in the tables' own (step, lane) order
    np.testing.assert_array_equal(table["start"], np.array([0, 0, 10, 10]))
    np.testing.assert_array_equal(table["lane"], np.array([0, 1, 0, 1]))
    np.testing.assert_array_equal(table["position"], np.array([0, 0, 1, 1]))
    np.testing.assert_array_equal(table["clusters"], table["lane"])  # one lane-episode, one cluster
    assert table["counts"].sum(axis=1).tolist() == [float(N_AGENTS)] * 4
    # the response is the undiscounted mean team reward per step of the commitment
    np.testing.assert_allclose(table["response"],
                               [rewards[0:10, 0].mean(), rewards[0:10, 1].mean(),
                                rewards[10:20, 0].mean(), rewards[10:20, 1].mean()])
    assert table["discounted_agreement_max_abs"] < 1e-12
    np.testing.assert_array_equal(table["labels"][0], labels[(0, 0)])
    np.testing.assert_array_equal(table["labels"][1], labels[(1, 0)])
    assert table["mean_reward_per_step"] == pytest.approx(float(rewards.mean()))


def test_the_commitment_reader_refuses_a_buffer_that_is_not_this_objects_execution():
    agent, rewards, executed, _labels = commitment_fixture()
    wrong = executed.copy()
    wrong[0, 0, 0] = (wrong[0, 0, 0] + 1) % N_LABELS
    with pytest.raises(ValueError, match="not the labels this object executed"):
        bandit.rollout_commitments(agent, rewards, wrong, horizon=20, cap=10, lanes=2)

    with pytest.raises(ValueError, match="not the cadence's"):
        bandit.rollout_commitments(agent, rewards, executed, horizon=20, cap=5, lanes=2)

    shifted = np.asarray(rewards, dtype=np.float64) + .5
    with pytest.raises(ValueError, match="discounted commitment reward"):
        bandit.rollout_commitments(agent, shifted, executed, horizon=20, cap=10, lanes=2)

    with pytest.raises(ValueError, match=r"\[horizon, lanes\]"):
        bandit.rollout_commitments(agent, rewards.T, executed, horizon=20, cap=10, lanes=2)

    agent.rollout_buffer = types.SimpleNamespace(get_d2_tables=lambda num_steps=None: None)
    with pytest.raises(ValueError, match="no D2 tables"):
        bandit.rollout_commitments(agent, rewards, executed, horizon=20, cap=10, lanes=2)


def test_the_reward_tape_holds_one_rollout_and_clears_its_lists_in_place():
    envs = [types.SimpleNamespace() for _ in range(2)]
    tape = bandit.RolloutRewardTape(envs)
    stores = tape.rewards
    for step in range(3):
        for lane in range(2):
            tape.rewards[lane].append(float(step + lane))
    values = tape.drain(3)
    assert values.shape == (3, 2)
    np.testing.assert_array_equal(values[:, 0], [0., 1., 2.])
    np.testing.assert_array_equal(values[:, 1], [1., 2., 3.])
    # the wrapper closes over the list objects, so they are cleared in place and never rebound
    assert tape.rewards is stores and all(not store for store in stores)
    assert tape.rollouts_drained == 1
    tape.rewards[0].append(1.)
    with pytest.raises(ValueError, match="steps per lane"):
        tape.drain(3)


# ---------------------------------------------------------------------------
# the declared configuration difference
# ---------------------------------------------------------------------------


def fake_envs(count=16):
    return [types.SimpleNamespace(state_dim=119, obs_dim=30) for _ in range(count)]


def test_the_declared_difference_is_the_one_flag_and_nothing_else(monkeypatch):
    bandit.bind()
    envs = fake_envs()
    config = bandit.make_config(bandit.BANDIT_ARM, envs, SEEDS[0])
    assert getattr(config, bandit.DECLARED_FIELD) is True
    baseline = matched._orig_make_config(bandit.BANDIT_ARM, envs, SEEDS[0])
    assert getattr(baseline, bandit.DECLARED_FIELD, False) is False
    # every recorded snapshot field is the D1280 construction's, and the flag is not one of them
    assert bandit.config_differences(bandit.shared.config_snapshot(config),
                                     bandit.shared.config_snapshot(baseline)) == {}
    assert bandit.DECLARED_FIELD not in bandit.shared.config_snapshot(config)
    assert config.policy_interruption_mode == "d2"
    assert config.interruption_cost_c == config.interruption_cost_c_Z == float("inf")
    assert config.age_feature == "off"
    assert (config.skill_cap_k_max, config.team_cap_k_Z) == tuple(bandit.ARM_CAPS)
    assert config.n_z == config.n_Z == N_LABELS and config.k == bandit.SKILL_PERIOD
    assert config.coordinator_batch_size == bandit.ARMS[bandit.BANDIT_ARM][1]

    # a second declared field that *is* a snapshot field is refused
    assert "lambda_h" in bandit.shared.e0.CONFIG_DUMP_FIELDS
    monkeypatch.setitem(bandit.ARM_OVERRIDES, bandit.BANDIT_ARM,
                        {bandit.DECLARED_FIELD: True, "lambda_h": .02})
    with pytest.raises(ValueError, match="moved the recorded configuration snapshot"):
        bandit.make_config(bandit.BANDIT_ARM, envs, SEEDS[0])
    # and an unknown arm never builds anything
    with pytest.raises(ValueError, match="unknown arm"):
        bandit.make_config("D1280", envs, SEEDS[0])


def test_the_allowed_differences_are_empty_on_the_production_host():
    assert bandit.allowed_differences(bandit.BANDIT_ARM) == set()
    assert bandit.host_geometry() == bandit.probe.FROZEN_GEOMETRY
    with pytest.raises(ValueError, match="unknown arm"):
        bandit.allowed_differences("D1280")


def test_the_plan_guard_is_the_six_declared_fits():
    for arm in bandit.ARMS:
        for seed in SEEDS:
            bandit.plan_guard(arm, seed)
    assert sorted(bandit.ARMS) == sorted([bandit.BANDIT_ARM, bandit.UNIFORM_ARM])
    assert len(SEEDS) == 3
    with pytest.raises(SystemExit):
        bandit.plan_guard("D1280", SEEDS[0])
    with pytest.raises(SystemExit):
        bandit.plan_guard(bandit.BANDIT_ARM, 772203)


def test_the_panel_schedule_is_two_panels_a_boundary_and_the_map_at_the_last_one():
    assert bandit.expected_panels() == 2 * len(bandit.PANEL_ROLLOUTS) + N_LABELS == 24
    assert bandit.panel_names(5, 2) == [("best_estimate", "constant_2"),
                                        ("uniform_every_10", "uniform_every_10")]
    final = bandit.panel_names(bandit.ROLLOUTS, 4)
    assert [name for name, _ in final] == [
        "best_estimate", "uniform_every_10"] + [f"constant_{c}" for c in range(N_LABELS)]
    assert final[0][1] == "constant_4"
    assert bandit.LATE_PANELS == (30, 35, 40, 45)
    # the executed rules are B09's constants and B08's own reference rule, not new definitions
    with b09.bound_rules():
        for _name, executed in final:
            assert executed in b09.b08.RULE_DEFINITIONS


# ---------------------------------------------------------------------------
# synthetic fits, and `reduce`
# ---------------------------------------------------------------------------


def world_scores(value, worlds=32):
    """32 world scores whose mean is exactly `value`: the readers take the mean of the panel."""
    return [float(value)] * worlds


def fake_panel(boundary, value, evaluation_seed, worlds=32, horizon=500):
    returns = [score * horizon / 6. for score in world_scores(value, worlds)]
    return {"status": "complete", "panel_rollouts": int(boundary), "after_update": int(boundary),
            "episode_ids": list(range(worlds)),
            "lane_seeds": list(range(evaluation_seed, evaluation_seed + worlds)),
            "steps_per_lane": [horizon] * worlds, "completed_episodes": worlds,
            "return_sums_U": returns, "returns_U": returns,
            "native_scores_J": world_scores(value, worlds),
            "evaluator_optimizer_calls": {name: 0 for name in bandit.shared.NETWORKS}}


def fake_fit_summary(arm, seed, *, best, reference, label_map, shares, argmax,
                     launch_sha=LAUNCH_SHA, rank_deficient=()):
    """A production-shaped summary of one fit, carrying the numbers the reading is checked on.

    `best` and `reference` are {boundary: J}; `label_map` is {label: J} at the last boundary;
    `shares` is the largest executed label share per rollout and `argmax` the deployed label.
    """
    lanes, worlds, horizon = 16, 32, 500
    rollouts, panels = bandit.ROLLOUTS, bandit.expected_panels()
    evaluation_seed = bandit.BLOCKS[seed]
    epochs = 15
    config = {"n_agents": 6, "n_users": 50, "num_envs": lanes, "rollout_length": horizon,
              "seed": seed, "policy_interruption_mode": "d2", "interruption_cost_c_Z": "Infinity",
              "interruption_cost_c": "Infinity", "interruption_delta": 1, "age_feature": "off",
              "n_Z": N_LABELS, "n_z": N_LABELS, "k": bandit.SKILL_PERIOD,
              "skill_cap_k_max": bandit.ARM_CAPS[0], "team_cap_k_Z": bandit.ARM_CAPS[1],
              "coordinator_batch_size": bandit.ARMS[arm][1]}
    law = np.full(N_LABELS, 1. / N_LABELS)
    rows = []
    for index in range(rollouts):
        estimate = {"beta_hat": [0.] * N_LABELS, "var_hat": [1.] * N_LABELS,
                    "standard_error": [1.] * N_LABELS, "z": [0.] * N_LABELS,
                    "argmax_beta_hat": int(argmax[index]), "estimate_available": True,
                    "rollouts_used": index + 1, "rollouts_seen": index + 1}
        share = float(shares[index])
        record = {"rollout": index + 1, "arm": arm, "commitments": 800,
                  "commitment_label_counts": [800] * N_LABELS,
                  "label_shares": [share] + [(1. - share) / 5.] * 5,
                  "largest_label_share": share, "most_executed_label": 0,
                  "executed_label_entropy": 1.7,
                  "cumulative_executed_label_counts": [1] * N_LABELS,
                  "q_used": law.tolist(), "q_used_source": "uniform",
                  "q_next": law.tolist(), "q_next_source": "uniform",
                  "argmax_q_next": int(argmax[index]), "estimate": estimate,
                  "rollout_fit": {"rank_deficient": bool((index + 1) in rank_deficient)},
                  "discounted_agreement_max_abs": 0., "mean_reward_per_step": .07,
                  "discriminator_team_accuracy": .3, "discriminator_individual_accuracy": .28,
                  "action_standard_deviation_mean": 2.9}
        rows.append({"rollout_index": index, "updated": True, "label_bandit": record,
                     "losses": {"discriminator_team_accuracy": .3,
                                "discriminator_individual_accuracy": .28},
                     "relative_initialization_displacement": {"coordinator": 0.}})

    def histogram_of(label):
        values = [0] * N_LABELS
        values[label] = lanes * horizon
        return values

    panel_runs = []
    for boundary in bandit.PANEL_ROLLOUTS:
        label = int(argmax[boundary - 1])
        for rule, value in ((bandit.SCHEDULE_RULE, best[boundary]),
                            (bandit.REFERENCE_RULE, reference[boundary])):
            schedule = rule == bandit.SCHEDULE_RULE
            panel_runs.append({
                "panel_rollouts": boundary, "rule": rule,
                "executed_rule": b09.constant_rule(label) if schedule else rule,
                "schedule_slot": schedule, "constant_label": label if schedule else None,
                "estimate": rows[boundary - 1]["label_bandit"]["estimate"],
                "J_mean": float(value), "J_world_scores": world_scores(value),
                "agent_label_histogram": histogram_of(label) if schedule else [1] * N_LABELS})
    for label in range(N_LABELS):
        panel_runs.append({
            "panel_rollouts": bandit.ROLLOUTS, "rule": b09.constant_rule(label),
            "executed_rule": b09.constant_rule(label), "schedule_slot": False,
            "constant_label": label, "estimate": rows[-1]["label_bandit"]["estimate"],
            "J_mean": float(label_map[label]), "J_world_scores": world_scores(label_map[label]),
            "agent_label_histogram": histogram_of(label)})
    return {
        "object_id": bandit.OBJECT_ID, "card": bandit.CARD, "arm": "D0",
        "launch_sha": launch_sha, "status": "complete", "failure": None,
        "training_seed": seed, "evaluation_seed": evaluation_seed,
        "training_lane_seeds": list(range(seed, seed + lanes)),
        "evaluation_lane_seeds": list(range(evaluation_seed, evaluation_seed + worlds)),
        "block_seed": seed, "factorial_arm": arm, "label_bandit_object": bandit.OBJECT_ID,
        "label_bandit_arm": arm, "arm_overrides": dict(bandit.ARM_OVERRIDES[arm]),
        "declared_config_difference": {"field": bandit.DECLARED_FIELD, "baseline": False,
                                       "fit": True, "in_config_snapshot": False},
        "rollouts": rollouts, "panel_rollouts": list(bandit.PANEL_ROLLOUTS),
        "panels": [fake_panel(boundary, best[boundary], evaluation_seed)
                   for boundary in bandit.PANEL_ROLLOUTS],
        "extra_panels": [], "panel_runs": panel_runs, "training_rows": rows,
        "learner_config": dict(config),
        "evaluation_config": dict(config, num_envs=worlds, seed=evaluation_seed),
        "counts": {"model_constructions": 2, "training_starts": 1, "checkpoint_loads": 0,
                   "training_transitions": lanes * horizon * rollouts,
                   "stored_training_transitions": lanes * horizon * rollouts,
                   "training_episodes": lanes * rollouts, "update_stages": rollouts,
                   "training_agent_step_batches": horizon * rollouts,
                   "evaluation_steps": worlds * horizon * panels,
                   "evaluation_agent_step_batches": horizon * panels,
                   "evaluation_episodes": worlds * panels},
        "optimizer_calls": {"coordinator": 0, "discoverer_actor": epochs * rollouts,
                            "discoverer_critic": epochs * rollouts,
                            "team_discriminator": rollouts,
                            "individual_discriminator": rollouts},
        "label_bandit_final": {"argmax_beta_hat": int(argmax[-1])},
        "final_weights": {"sha256": "a" * 64},
        "wall_seconds_before_publication": 8000., "peak_rss_bytes": 2900000000}


def flat(value):
    return {boundary: value for boundary in bandit.PANEL_ROLLOUTS}


def default_fits():
    """Six fits whose numbers make P1-P4 and the alternative resolve in a known way."""
    fits = []
    for seed in SEEDS:
        fits.append(fake_fit_summary(
            bandit.BANDIT_ARM, seed, best=flat(.50), reference=flat(.45),
            label_map={0: .30, 1: .50, 2: .40, 3: .35, 4: .32, 5: .31},
            shares=[.2] * 10 + [.5] * 35, argmax=[1] * bandit.ROLLOUTS))
        fits.append(fake_fit_summary(
            bandit.UNIFORM_ARM, seed, best=flat(.49), reference=flat(.44),
            label_map={0: .30, 1: .49, 2: .40, 3: .35, 4: .32, 5: .31},
            shares=[.2] * bandit.ROLLOUTS, argmax=[1] * bandit.ROLLOUTS))
    return fits


@pytest.fixture
def canned_references(monkeypatch):
    """The foreign readers are canned, on purpose.

    `reduce` is checked for *this* object's arithmetic and refusals. The published D1280 reader and
    B09's probe reader belong to their own objects and are exercised by their own tests; here they
    are replaced by fixed rows so those objects' own inputs are not needed to pin this arithmetic.
    """
    def fit_endpoint(summary):
        if summary.get("broken"):
            raise ValueError("synthetic unreadable reference")
        return {boundary: np.full(32, float(summary["level"]))
                for boundary in bandit.PANEL_ROLLOUTS}

    def probe_row(summary):
        j_by_rule = {b09.BASELINE_RULE: .40, "uniform_frozen_episode": .38}
        j_by_rule.update({b09.constant_rule(label): value
                          for label, value in enumerate(summary["constants"])})
        return {"block_seed": int(summary["block_seed"]), "launch_sha": LAUNCH_SHA,
                "weights_sha256": "b" * 64, "J_by_rule": j_by_rule}

    monkeypatch.setattr(matched, "fit_endpoint", fit_endpoint)
    monkeypatch.setattr(b09, "probe_row", probe_row)
    references = [{"block_seed": seed, "factorial_arm": "D1280", "stage": 1, "level": .40,
                   "object_id": matched.OBJECT_ID, "launch_sha": LAUNCH_SHA,
                   "counts": {}, "optimizer_calls": {}} for seed in SEEDS]
    probes = [{"block_seed": seed, "constants": [.30, .45, .40, .35, .32, .31]} for seed in SEEDS]
    return references, probes


def test_reduce_reads_the_six_fits_and_counts_the_declared_predictions(canned_references):
    references, probes = canned_references
    result = bandit.reduce_inputs(default_fits(), references, probes)

    assert result["status"] == "complete" and result["blocks_read"] == 3
    assert result["batch_launch_sha"] == LAUNCH_SHA
    assert result["invalid_fits"] == {} and result["invalid_references"] == {}
    assert result["fits_supplied"] == result["fits_planned"] == 6
    assert result["object_id"] == bandit.OBJECT_ID and result["card"] == bandit.CARD
    block = result["blocks"][0]
    arm = block["arms"][bandit.BANDIT_ARM]
    assert arm[f"J_{bandit.ROLLOUTS}"][bandit.SCHEDULE_RULE] == pytest.approx(.50)
    assert arm["J_late_window"][bandit.SCHEDULE_RULE] == pytest.approx(.50)
    assert arm["best_estimate_minus_d1280_J45"] == pytest.approx(.10)
    assert arm["best_estimate_minus_uniform_every_10_J45"] == pytest.approx(.05)
    assert arm["best_estimate_minus_b09_best_constant_J45"] == pytest.approx(.05)
    assert arm["uniform_every_10_minus_d1280_J45"] == pytest.approx(.05)
    assert arm["label_map_ranking"] == [1, 2, 3, 4, 5, 0]
    assert arm["rank_of_argmax_beta_hat_in_the_map"] == 1
    assert arm["final_argmax_beta_hat"] == 1
    assert arm["map_spread"] == pytest.approx(.20)
    assert arm["schedule_slot_matches_its_constant_panel"] is True
    assert arm["b09_best_constant_label"] == 1
    assert arm["final_argmax_is_b09_best_constant"] is True
    assert arm["first_rollout_largest_share_above_threshold"] == 11
    assert arm["argmax_beta_hat_changes_after_15"] == 0
    assert block["bandit_minus_uniform"]["J45_best_estimate"] == pytest.approx(.01)

    predictions = result["predictions"]
    assert predictions["P1_bandit_law_leaves_uniform_by_rollout_15"]["blocks_holding"] == 3
    for arm_name in bandit.ARMS:
        key = f"P2_argmax_beta_is_in_the_top_two_of_the_map_{arm_name}"
        assert predictions[key]["blocks_holding"] == 3
    assert predictions["P3_bandit_best_estimate_beats_d1280_by_the_margin"]["blocks_holding"] == 3
    assert predictions["P4_bandit_minus_uniform_within_the_band"]["blocks_holding"] == 3
    assert predictions["A_the_ranking_drifts_faster_than_the_estimate_follows"][
        "blocks_holding"] == 0
    mean = predictions["P3_mean_over_blocks"]
    assert mean["mean_J45_minus_d1280"] == pytest.approx(.10)
    assert mean["mean_J45_clause_holds"] is True
    assert mean["mean_late_window_clause_holds"] is True
    assert "not an interval" in predictions["counting_note"]

    across = result[f"best_estimate_minus_d1280_J45_{bandit.BANDIT_ARM}"]
    assert across["available_blocks"] == 3 and across["mean"] == pytest.approx(.10)
    assert "coverage not validated" in across["working_model"]
    assert result["bandit_minus_uniform"]["J45_best_estimate"]["mean"] == pytest.approx(.01)


def test_reduce_counts_the_alternative_when_the_deployed_label_drifts(canned_references):
    references, probes = canned_references
    drifting = []
    for seed in SEEDS:
        argmax = [1] * 16 + [(index + 1) % 3 for index in range(bandit.ROLLOUTS - 16)]
        for arm, best in ((bandit.BANDIT_ARM, .40), (bandit.UNIFORM_ARM, .41)):
            drifting.append(fake_fit_summary(
                arm, seed, best=flat(best), reference=flat(.44),
                label_map={0: .30, 1: .50, 2: .40, 3: .35, 4: .32, 5: .31},
                shares=[.2] * bandit.ROLLOUTS, argmax=argmax))
    result = bandit.reduce_inputs(drifting, references, probes)
    predictions = result["predictions"]
    assert predictions["P1_bandit_law_leaves_uniform_by_rollout_15"]["blocks_holding"] == 0
    assert predictions["P3_bandit_best_estimate_beats_d1280_by_the_margin"]["blocks_holding"] == 0
    entry = predictions["A_the_ranking_drifts_faster_than_the_estimate_follows"]
    assert entry["blocks_holding"] == 3
    value = entry["per_block"][str(SEEDS[0])]["value"]
    assert value["changes_after_15"] >= bandit.ALTERNATIVE_CHANGES
    assert value["best_estimate_minus_uniform_every_10_J45"] < 0.
    # the argmax the map ranks second still satisfies P2
    assert predictions[
        f"P2_argmax_beta_is_in_the_top_two_of_the_map_{bandit.BANDIT_ARM}"]["blocks_holding"] == 3
    assert result["blocks"][0]["arms"][bandit.BANDIT_ARM][
        "rank_of_argmax_beta_hat_in_the_map"] == 2


def test_reduce_refuses_mixed_launch_shas_and_duplicates_and_lists_a_failed_fit(canned_references):
    references, probes = canned_references
    fits = default_fits()
    fits[0] = dict(fits[0], launch_sha="f" * 40)
    with pytest.raises(ValueError, match="mixed launch shas"):
        bandit.reduce_inputs(fits, references, probes)

    fits = default_fits()
    fits.append(fits[0])
    with pytest.raises(ValueError, match="duplicate block and arm"):
        bandit.reduce_inputs(fits, references, probes)

    # a technical failure is reported with its reason and left out of the counts, never dropped
    fits = default_fits()
    fits[0] = dict(fits[0], optimizer_calls=dict(fits[0]["optimizer_calls"], coordinator=3))
    result = bandit.reduce_inputs(fits, references, probes)
    assert result["status"] == "incomplete" and result["blocks_read"] == 2
    key = f"{SEEDS[0]}:{bandit.BANDIT_ARM}"
    assert "coordinator" in result["invalid_fits"][key]
    assert result["blocks"][0]["missing_or_invalid"][bandit.BANDIT_ARM] == result[
        "invalid_fits"][key]
    assert result["fits_supplied"] == 6 and result["fits_planned"] == 6
    assert result["blocks"][0]["arms"][bandit.UNIFORM_ARM] is not None
    assert result["blocks"][0]["arms"].get(bandit.BANDIT_ARM) is None
    assert result["blocks"][0]["bandit_minus_uniform"] is None
    assert result["predictions"]["P4_bandit_minus_uniform_within_the_band"][
        "per_block"][str(SEEDS[0])]["read"] is False
    assert result["predictions"][
        "P3_bandit_best_estimate_beats_d1280_by_the_margin"]["blocks_read"] == 2


def test_reduce_reports_an_unreadable_reference_or_a_missing_probe(canned_references):
    references, probes = canned_references
    references = [dict(reference) for reference in references]
    references[1]["broken"] = True
    result = bandit.reduce_inputs(default_fits(), references, probes)
    assert result["status"] == "incomplete" and result["blocks_read"] == 2
    assert "synthetic unreadable reference" in json.dumps(result["invalid_references"])
    assert result["blocks"][1]["missing_or_invalid"]["d1280_reference"]

    result = bandit.reduce_inputs(default_fits(), references[:1] + references[2:], probes[:2])
    assert result["blocks"][1]["missing_or_invalid"]["d1280_reference"]
    assert result["blocks"][2]["missing_or_invalid"]["b09_probe"] == "not supplied"


def test_a_fit_reader_refuses_a_summary_that_is_not_this_objects_complete_fit():
    summary = fake_fit_summary(bandit.BANDIT_ARM, SEEDS[0], best=flat(.5), reference=flat(.4),
                               label_map={label: .3 for label in range(N_LABELS)},
                               shares=[.2] * bandit.ROLLOUTS, argmax=[0] * bandit.ROLLOUTS)
    assert sorted(bandit.fit_endpoint(summary)) == list(bandit.PANEL_ROLLOUTS)

    with pytest.raises(ValueError, match="not a label-bandit fit"):
        bandit.fit_endpoint(dict(summary, label_bandit_object="OTHER"))
    with pytest.raises(ValueError, match="does not record its declared override"):
        bandit.fit_endpoint(dict(summary, arm_overrides={}))
    with pytest.raises(ValueError, match="not the declared"):
        bandit.fit_endpoint(dict(summary, panel_runs=summary["panel_runs"][:-1]))
    with pytest.raises(ValueError, match="one label-bandit record per rollout"):
        bandit.fit_endpoint(dict(summary, training_rows=[
            dict(row, label_bandit=None) for row in summary["training_rows"]]))
    with pytest.raises(ValueError, match="coordinator"):
        bandit.fit_endpoint(dict(summary, optimizer_calls=dict(summary["optimizer_calls"],
                                                               coordinator=1)))
    with pytest.raises(ValueError, match="incomplete or wrong"):
        bandit.fit_endpoint(dict(summary, status="incomplete"))

    runs = [dict(entry) for entry in summary["panel_runs"]]
    runs[0] = dict(runs[0], agent_label_histogram=[1] * N_LABELS)
    with pytest.raises(ValueError, match="executed labels other than argmax"):
        bandit.fit_endpoint(dict(summary, panel_runs=runs))


def test_a_fit_reader_refuses_a_construction_that_is_not_the_declared_one():
    summary = fake_fit_summary(bandit.UNIFORM_ARM, SEEDS[1], best=flat(.5), reference=flat(.4),
                               label_map={label: .3 for label in range(N_LABELS)},
                               shares=[.2] * bandit.ROLLOUTS, argmax=[0] * bandit.ROLLOUTS)
    bandit.fit_endpoint(summary)
    for field, value in (("interruption_cost_c", 0.25), ("age_feature", "normalized")):
        broken = dict(summary, learner_config=dict(summary["learner_config"], **{field: value}))
        with pytest.raises(ValueError):
            bandit.fit_endpoint(broken)
    with pytest.raises(ValueError, match="one declared configuration difference"):
        bandit.fit_endpoint(dict(summary, declared_config_difference={
            "field": bandit.DECLARED_FIELD, "fit": False}))


# ---------------------------------------------------------------------------
# the launch script, read as text
# ---------------------------------------------------------------------------


def test_the_launch_script_composes_one_admitted_fit_of_this_object():
    path = (ROOT / "experiments" / "candidates" / "flexible_skill_duration" / "label_bandit_b13"
            / "launch_fit.sh")
    text = path.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in text
    assert 'if [ "$#" -ne 6 ]; then' in text
    assert "usage: launch_fit.sh <node> <lead> <launch_sha> <tag> <arm> <seed>" in text
    assert "exit 2" in text
    assert "node=$1; lead=$2; launch_sha=$3; tag=$4; arm=$5; seed=$6" in text
    assert "scripts/hmasd_launch.py launch" in text
    assert "scripts/run_fsd_label_bandit_b13.py fit" in text
    assert '--arm "$arm" --seed "$seed" --launch-sha "$launch_sha" --output-root "$output"' in text
    assert "--direction flexible_skill_duration" in text
    assert '--node "$node"' in text and "--snapshot" in text
    assert '--lead "$lead"' in text and '--sha "$launch_sha"' in text
    assert 'output="runs/flexible_skill_duration/${tag}"' in text
    assert "control_plane_interpreter" in text  # the kernel runs under 3.11+, not the science venv
    for arm in bandit.ARMS:
        assert arm in text
    for seed in SEEDS:
        assert str(seed) in text
    assert "\r" not in text  # the repository's LF paths


def test_the_command_line_refuses_an_out_of_plan_arm_or_block():
    never = str(ROOT / "temp" / "label_bandit_b13_never_created")
    for argv in (["fit", "--arm", "D1280", "--seed", str(SEEDS[0]), "--output-root", never],
                 ["fit", "--arm", bandit.BANDIT_ARM, "--seed", "772203", "--output-root", never],
                 ["fit", "--arm", bandit.BANDIT_ARM, "--seed", str(SEEDS[0])]):
        with pytest.raises(SystemExit):
            bandit.main(argv)
    assert not Path(never).exists()  # nothing is created before the plan guard and the admission
    assert b01.build_learner is not bandit.build_learner
