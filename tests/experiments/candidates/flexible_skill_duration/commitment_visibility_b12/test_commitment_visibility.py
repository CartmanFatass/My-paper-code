"""The commitment-visibility entry: the caps, the reward tape, the regression and `reduce`.

Planted arrays and synthetic published summaries only; the real stack - the frozen collector's own
calls through B11's collection, the real D2 route at four caps and the real checkpoint - is in
`test_commitment_visibility_real_tiny.py`. The synthetic B09 and B10 probe summaries are those
objects' own test fixtures, loaded by path the way B10's and B11's tests load B09's, so the objects
are compared through one shape and not several. Technical checks: nothing here asserts the direction
or the size of any measured quantity.
"""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


b09tests = _load("fsd_commitment_visibility_b09_fixtures", "label_map_b09/test_label_map.py")
b10tests = _load("fsd_commitment_visibility_b10_fixtures",
                 "label_map_sampled_b10/test_label_map_sampled.py")

import run_fsd_commitment_visibility_b12 as b12  # noqa: E402
import run_fsd_coordinator_signal_b11 as b11  # noqa: E402
import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402
import run_fsd_label_map_sampled_b10 as b10  # noqa: E402

SEEDS = sorted(b12.BLOCKS)
WORLDS = b09tests.WORLDS
AS_TRAINED = b09tests.AS_TRAINED
N_LABELS = b12.N_LABELS
# B09's synthetic mean-action map orders the labels
#   772803 [2, 3, 1, 0, 4, 5]   772903 [2, 1, 4, 0, 3, 5]   773003 [1, 2, 0, 3, 4, 5],
# so B09's best label is 2, 2 and 1. B10's synthetic sampled spread is .030, .100 and .060 J.
BEST_LABEL = {772803: 2, 772903: 2, 773003: 1}
B10_SPREAD = {seed: max(b10tests.SAMPLED[seed]) - min(b10tests.SAMPLED[seed]) for seed in SEEDS}


# ---------------------------------------------------------------------------
# identity, the declared collection and the source map
# ---------------------------------------------------------------------------


def test_the_object_identity_and_the_declared_collection():
    assert b12.OBJECT_ID == "FSD_COMMITMENT_VISIBILITY_B12"
    assert b12.CARD.endswith("(2026-09-20 19:11 PDT, B12 specified before any score)")
    assert "NOTES.md" in b12.CARD and "flexible_skill_duration" in b12.CARD
    assert b12.CAPS == (10, 50, 100, 500) and b12.ROLLOUTS_PER_CAP == 16
    assert b12.FROZEN_CAP == 10 == b08.ARM_CAPS[0]
    assert b12.PERMUTATIONS == 1000 and b12.PERMUTATION_PERCENTILE == 95.
    assert b12.RESPONSES == (b12.UNDISCOUNTED, b12.DISCOUNTED)
    assert b12.PRIMARY_RESPONSE == b12.UNDISCOUNTED == "undiscounted_mean_reward_per_step"
    assert b12.DISCOUNTED == "discounted_segment_reward"
    assert b12.NON_ADDITIVITY_CAP == 500 and b12.ALTERNATIVE_FRACTION == .5
    assert b12.N_LABELS == 6 == b11.N_LABELS
    assert b12.BLOCKS == b11.BLOCKS == b09.BLOCKS == b10.BLOCKS
    assert b12.CAUSES_EXPECTED == ("reset", "team_cap")
    assert "wsl_4070" in b12.INTERPRETATION_LIMIT
    assert "not a `k` sweep for performance" in b12.INTERPRETATION_LIMIT
    assert "ten-step targets" in b12.INTERPRETATION_LIMIT  # the secondary table's own limit


def test_the_source_map_carries_the_file_line_facts_it_claims():
    notes = b12.SOURCE_NOTES
    # the two attributes the learner's decision cadence actually reads
    assert "hmasd/agent.py:2596" in notes["cap_attributes"]
    assert "hmasd/agent.py:2613" in notes["cap_attributes"]
    assert "hmasd/agent.py:482-484" in notes["cap_attributes"]
    assert "hmasd/utils.py:485-516" in notes["cap_attributes"]  # no cap-keyed preallocation
    assert "hmasd/agent.py:6309" in notes["cap_attributes"]  # the one `config.k` this probe avoids
    assert "run_fsd_label_content_b08.py:139" in notes["cap_attributes"]  # B08's own RULE_CAPS
    assert "hmasd/agent.py:2348-2355" in notes["responses"]
    assert "hmasd/networks.py:1801-1809" in notes["placebo"]
    # the U -> J reporting factor, cited at both ends
    assert "run_fsd_baseline_interruption_b01.py:254" in notes["reporting_factor"]
    assert "run_fsd_uav_individual_renewal_b01.py:140" in notes["reporting_factor"]
    assert "N_UAVS / HORIZON" in notes["reporting_factor"]
    # the frozen collector B11 transcribes is recorded by name, lines and digest
    record = b11.frozen_collector_source()
    assert record["function"].endswith("collect_training") and len(record["sha256"]) == 64


def test_the_collection_seeds_are_a_function_of_the_block_the_cap_and_the_rollout():
    seeds = {(seed, cap, rollout): b12.collection_seed(seed, cap, rollout)
             for seed in SEEDS for cap in b12.CAPS for rollout in range(4)}
    assert len(set(seeds.values())) == len(seeds)
    assert all(0 <= value < 2 ** 31 for value in seeds.values())
    assert b12.collection_seed(772903, 50, 2) == b12.collection_seed(772903, 50, 2)
    assert b12.collection_seed(772903, 50, 2) != b12.collection_seed(772903, 100, 2)
    assert b12.collection_seed(772903, 50, 2) != b12.collection_seed(772803, 50, 2)
    # and it is not B11's own derivation of the same block and rollout
    assert b12.collection_seed(772903, 10, 2) != b11.collection_seed(772903, 2)
    assert "b12:cap" in b12.SEED_DERIVATION and "seed_rng" in b12.SEED_DERIVATION
    assert "restores it in a `finally`" in b12.SEED_DERIVATION


def test_the_permutation_generator_is_dedicated_and_reproducible():
    first = b12.permutation_generator(782803, 50, "u").integers(0, 1000, 5).tolist()
    assert first == b12.permutation_generator(782803, 50, "u").integers(0, 1000, 5).tolist()
    assert first != b12.permutation_generator(782803, 100, "u").integers(0, 1000, 5).tolist()
    assert first != b12.permutation_generator(782903, 50, "u").integers(0, 1000, 5).tolist()
    assert first != b12.permutation_generator(782803, 50, "d").integers(0, 1000, 5).tolist()


def test_the_expected_row_geometry_is_the_cadence_the_cap_implies():
    assert b12.expected_team_rows(16, 500, 10) == 800  # B11's own geometry
    assert b12.expected_team_rows(16, 500, 50) == 160
    assert b12.expected_team_rows(16, 500, 100) == 80
    assert b12.expected_team_rows(16, 500, 500) == 16
    assert b12.expected_team_rows(16, 500, 1000) == 16  # a cap past the horizon decides once
    assert b12.expected_team_rows(2, 20, 10) == 4


# ---------------------------------------------------------------------------
# the caps: set on the learner instance, restored in a `finally`
# ---------------------------------------------------------------------------


class StubAgent:
    """Only the attributes the cap manager reads and writes."""

    def __init__(self, *, d2_enabled=True, cost=float("inf"), age_feature="off", caps=(10, 10)):
        self.d2_enabled = d2_enabled
        self.d2_cost_c = self.d2_cost_c_Z = cost
        self.d2_age_feature = age_feature
        self.d2_k_max, self.d2_k_Z = caps


def test_the_cap_manager_sets_both_caps_and_restores_them():
    agent = StubAgent()
    with b12.commitment_cap(agent, 500) as restored:
        assert (agent.d2_k_max, agent.d2_k_Z) == (500, 500)
        assert restored == {"d2_k_max": 10, "d2_k_Z": 10}
    assert (agent.d2_k_max, agent.d2_k_Z) == (10, 10)


def test_the_cap_manager_restores_when_the_body_raises():
    agent = StubAgent()
    with pytest.raises(RuntimeError, match="inside the collection"):
        with b12.commitment_cap(agent, 100):
            assert agent.d2_k_Z == 100
            raise RuntimeError("something failed inside the collection")
    assert (agent.d2_k_max, agent.d2_k_Z) == (10, 10)


@pytest.mark.parametrize("agent,message", [
    (StubAgent(d2_enabled=False), "defined on the D2 route"),
    (StubAgent(cost=.25), "infinite interruption costs"),
    (StubAgent(age_feature="normalized"), "age feature to be off"),
])
def test_the_cap_manager_refuses_a_construction_the_cap_is_not_the_only_lever_on(agent, message):
    caps = (agent.d2_k_max, agent.d2_k_Z)
    with pytest.raises(ValueError, match=message):
        with b12.commitment_cap(agent, 50):
            pass
    assert (agent.d2_k_max, agent.d2_k_Z) == caps  # nothing was set before the refusal


def test_the_cap_manager_refuses_a_cap_below_one_step():
    agent = StubAgent()
    with pytest.raises(ValueError, match="at least one step"):
        with b12.commitment_cap(agent, 0):
            pass
    assert (agent.d2_k_max, agent.d2_k_Z) == (10, 10)


def test_b11s_seed_derivation_is_bound_for_one_cap_and_put_back():
    original = b11.collection_seed
    with b12.b11_collection_seed_bound(100):
        assert b11.collection_seed(772803, 3) == b12.collection_seed(772803, 100, 3)
    assert b11.collection_seed is original
    assert b11.collection_seed(772803, 3) != b12.collection_seed(772803, 100, 3)
    with pytest.raises(RuntimeError):
        with b12.b11_collection_seed_bound(100):
            raise RuntimeError("a cap's collection failed")
    assert b11.collection_seed is original  # a failure does not leave B11 marked


# ---------------------------------------------------------------------------
# the reward tape: B11's loop untouched, the raw per-step reward kept
# ---------------------------------------------------------------------------


class StubEnv:
    """An environment whose `step` returns a known reward and a recognisable result object."""

    def __init__(self, base):
        self.base = base
        self.calls = 0

    def step(self, action):
        self.calls += 1
        return ("obs", self.base + self.calls, False, False, {"action": action})


def test_the_reward_tape_records_every_step_and_leaves_the_environments_as_it_found_them():
    envs = [StubEnv(0.), StubEnv(100.)]
    tape = b12.RewardTape(envs)
    with tape.attached():
        assert all("step" in env.__dict__ for env in envs)
        results = [[env.step(index) for index in range(4)] for env in envs]
    assert not any("step" in env.__dict__ for env in envs)
    assert [env.calls for env in envs] == [4, 4]
    # the wrapper returns the frozen result unchanged
    assert results[0][2] == ("obs", 3., False, False, {"action": 2})
    assert tape.rewards[0] == [1., 2., 3., 4.] and tape.rewards[1] == [101., 102., 103., 104.]
    assert tape.calls == 8
    assert tape.require_shape(2, 2) == 4
    first = tape.rollout(0, 2)
    assert first.shape == (2, 2)  # [horizon, lanes]
    assert first.tolist() == [[1., 101.], [2., 102.]]
    assert tape.rollout(1, 2).tolist() == [[3., 103.], [4., 104.]]
    with pytest.raises(ValueError, match="not the 6 the collection takes"):
        tape.require_shape(3, 2)


def test_the_reward_tape_refuses_to_shadow_an_existing_instance_step():
    env = StubEnv(0.)
    env.step = lambda action: ("obs", 7., False, False, {})
    with pytest.raises(ValueError, match="already carries an instance-level `step`"):
        with b12.RewardTape([env]).attached():
            pass


def test_the_reward_tape_puts_the_frozen_step_back_when_the_body_raises():
    envs = [StubEnv(0.)]
    with pytest.raises(RuntimeError):
        with b12.RewardTape(envs).attached():
            raise RuntimeError("a collection failed")
    assert "step" not in envs[0].__dict__


# ---------------------------------------------------------------------------
# the commitments of one rollout
# ---------------------------------------------------------------------------


def planted_rollout(cap, *, horizon=20, lanes=2, n_agents=6, rollout=0, generator=None,
                    gamma=.99):
    """A `rollout_frame`-shaped frame and the per-step rewards that produced it."""
    generator = np.random.default_rng(11) if generator is None else generator
    starts = list(range(0, horizon, cap))
    rewards = generator.normal(size=(horizon, lanes))
    rows = []
    for lane in range(lanes):
        for start in starts:
            rows.append((lane, start, min(cap, horizon - start)))
    count = len(rows)
    labels = generator.integers(0, N_LABELS, size=(count, n_agents))
    counts = np.stack([(labels == label).sum(axis=1) for label in range(N_LABELS)],
                      axis=1).astype(np.float64)
    discounted = np.asarray(
        [float((np.power(gamma, np.arange(length)) * rewards[start:start + length, lane]).sum())
         for lane, start, length in rows], dtype=np.float64)
    elapsed = np.asarray([length for _lane, _start, length in rows], dtype=np.int64)
    frame = {
        "rows_M": count, "rows_M_team": count, "rows_M_agent": count * n_agents,
        "flushed_open_segments": 0,
        "team": {"rollout": np.full(count, rollout, dtype=np.int64),
                 "lane": np.asarray([lane for lane, _s, _l in rows], dtype=np.int64),
                 "step": np.asarray([start for _lane, start, _l in rows], dtype=np.int64),
                 "label": generator.integers(0, N_LABELS, size=count),
                 "advantage": generator.normal(size=count),
                 "value": generator.normal(size=count),
                 "reward": discounted, "elapsed": elapsed,
                 "counts": counts},
        "agent": {"label": labels.reshape(-1),
                  "elapsed": np.repeat(elapsed, n_agents)}}
    return frame, rewards


def test_the_commitments_carry_both_responses_and_the_position_in_the_episode():
    frame, rewards = planted_rollout(10, horizon=20, lanes=2)
    commitments = b12.commitment_frame(frame, rewards, cap=10, gamma=.99, horizon=20)
    assert commitments["position"].tolist() == [0, 1, 0, 1]
    assert commitments["elapsed"].tolist() == [10, 10, 10, 10]
    assert commitments["n_agents"] == 6
    # the undiscounted response is the raw per-step sum over the commitment's own steps, per step
    for index in range(commitments["position"].size):
        lane, start, length = (int(commitments["lane"][index]), int(commitments["start"][index]),
                               int(commitments["elapsed"][index]))
        window = rewards[start:start + length, lane]
        assert commitments["undiscounted_sum"][index] == pytest.approx(float(window.sum()))
        assert commitments[b12.UNDISCOUNTED][index] == pytest.approx(float(window.mean()))
        assert commitments["discounted_from_tape"][index] == pytest.approx(
            float((np.power(.99, np.arange(length)) * window).sum()))
    # the discounted response is the buffer's own segment reward, and the tape reproduces it
    assert np.allclose(commitments[b12.DISCOUNTED], commitments["discounted_from_tape"])
    assert np.array_equal(commitments["homogeneity"], (commitments["counts"] ** 2).sum(axis=1))
    assert commitments["team_one_hot"].sum(axis=1).tolist() == [1.] * 4


def test_a_long_cap_gives_one_commitment_per_lane_episode_with_the_whole_horizon():
    frame, rewards = planted_rollout(500, horizon=20, lanes=2)
    commitments = b12.commitment_frame(frame, rewards, cap=500, gamma=.99, horizon=20)
    assert commitments["position"].tolist() == [0, 0]
    assert commitments["elapsed"].tolist() == [20, 20]
    assert commitments[b12.UNDISCOUNTED][0] == pytest.approx(float(rewards[:, 0].mean()))


@pytest.mark.parametrize("damage,message", [
    ("elapsed", "not the cadence of cap"),
    ("agent_elapsed", "does not share its team commitment"),
])
def test_the_commitments_refuse_a_rollout_whose_segments_are_not_the_caps(damage, message):
    frame, rewards = planted_rollout(10, horizon=20, lanes=2)
    if damage == "elapsed":
        frame["team"]["elapsed"] = frame["team"]["elapsed"].copy()
        frame["team"]["elapsed"][1] = 7
        frame["agent"]["elapsed"] = np.repeat(frame["team"]["elapsed"], 6)
    else:
        frame["agent"]["elapsed"] = frame["agent"]["elapsed"].copy()
        frame["agent"]["elapsed"][3] = 4
    with pytest.raises(ValueError, match=message):
        b12.commitment_frame(frame, rewards, cap=10, gamma=.99, horizon=20)


def test_the_pooled_commitments_cluster_on_the_rollout_and_the_lane():
    generator = np.random.default_rng(4)
    frames = [b12.commitment_frame(*planted_rollout(10, rollout=index, generator=generator),
                                   cap=10, gamma=.99, horizon=20) for index in range(3)]
    pooled = b12.stack_commitments(frames)
    assert pooled["position"].size == 12 and pooled["counts"].shape == (12, 6)
    assert np.unique(pooled["clusters"]).size == 6  # three rollouts x two lanes
    assert pooled["cap"].tolist() == [10] * 12


# ---------------------------------------------------------------------------
# the regression with position fixed effects
# ---------------------------------------------------------------------------


def planted_design(*, rows=1500, positions=5, coefficients, effects=None, noise=.01,
                   homogeneity=0., seed=3, clusters=40):
    """Counts, positions, clusters and a response built from known centred coefficients."""
    generator = np.random.default_rng(seed)
    labels = generator.integers(0, N_LABELS, size=(rows, 6))
    counts = np.stack([(labels == label).sum(axis=1) for label in range(N_LABELS)],
                      axis=1).astype(np.float64)
    position = generator.integers(0, positions, size=rows)
    effects = np.linspace(.5, 1.5, positions) if effects is None else np.asarray(effects)
    beta = np.asarray(coefficients, dtype=np.float64)
    response = (counts @ beta + effects[position]
                + homogeneity * (counts ** 2).sum(axis=1)
                + generator.normal(0., noise, size=rows))
    return {"counts": counts, "positions": position, "response": response,
            "clusters": generator.integers(0, clusters, size=rows),
            "n_positions": positions, "effects": effects, "beta": beta}


def test_the_regression_recovers_the_planted_centred_coefficients():
    planted = [.10, -.02, .03, -.05, .01, -.07]
    planted = [value - float(np.mean(planted)) for value in planted]
    data = planted_design(coefficients=planted)
    fit = b12.label_regression(data["counts"], data["positions"], data["response"],
                               data["clusters"], n_positions=data["n_positions"])
    assert fit["full_rank"] is True and fit["positions"] == 5
    assert fit["segments"] == 1500 and fit["dropped_label"] == b12.DROP_LABEL == 5
    for label in range(N_LABELS):
        assert fit["centred_coefficients"][str(label)] == pytest.approx(planted[label], abs=.002)
        assert fit["clustered_se"][str(label)] > 0.
    assert sum(fit["centred_coefficients"].values()) == pytest.approx(0., abs=1e-12)
    assert fit["ranking"][0] == 0 and fit["ranking"][-1] == 5
    assert fit["max_minus_min"] == pytest.approx(max(planted) - min(planted), abs=.004)
    assert fit["max_minus_min_clustered_se"] > 0.
    assert fit["r_squared"] > .9 and fit["residual_sd"] == pytest.approx(.01, abs=.002)


def test_the_centred_coefficients_and_the_all_equal_prediction_do_not_depend_on_the_dropped_label():
    planted = [.10, -.02, .03, -.05, .01, -.07]
    planted = [value - float(np.mean(planted)) for value in planted]
    data = planted_design(coefficients=planted)
    fits = [b12.label_regression(data["counts"], data["positions"], data["response"],
                                 data["clusters"], n_positions=data["n_positions"],
                                 drop_label=drop) for drop in range(N_LABELS)]
    for fit in fits[1:]:
        for label in range(N_LABELS):
            assert fit["centred_coefficients"][str(label)] == pytest.approx(
                fits[0]["centred_coefficients"][str(label)], abs=1e-9)
            assert fit["all_equal_prediction"][str(label)] == pytest.approx(
                fits[0]["all_equal_prediction"][str(label)], abs=1e-9)
        assert fit["max_minus_min"] == pytest.approx(fits[0]["max_minus_min"], abs=1e-9)
    # and the prediction is the all-equal configuration the planted model implies
    for label in range(N_LABELS):
        assert fits[0]["all_equal_prediction"][str(label)] == pytest.approx(
            6. * planted[label] + float(data["effects"].mean()), abs=.02)


def test_the_position_fixed_effects_absorb_a_drift_the_counts_would_otherwise_take():
    """With the response built from the position alone, the centred coefficients stay near zero."""
    data = planted_design(coefficients=[0.] * 6, effects=[0., 1., 2., 3., 4.], noise=.001)
    fit = b12.label_regression(data["counts"], data["positions"], data["response"],
                               data["clusters"], n_positions=data["n_positions"])
    assert fit["max_minus_min"] < .001
    assert fit["mean_position_effect"] == pytest.approx(float(np.mean(data["effects"][
        data["positions"]])), abs=.01)


# ---------------------------------------------------------------------------
# the permutation calibration
# ---------------------------------------------------------------------------


def test_the_permutation_calibration_reproduces_the_fit_and_counts_its_own_arithmetic():
    planted = [.10, -.02, .03, -.05, .01, -.07]
    planted = [value - float(np.mean(planted)) for value in planted]
    data = planted_design(coefficients=planted)
    fit = b12.label_regression(data["counts"], data["positions"], data["response"],
                               data["clusters"], n_positions=data["n_positions"])
    calibration = b12.permutation_calibration(
        data["counts"], data["positions"], data["response"],
        b12.permutation_generator(782803, 50, "u"), n_positions=data["n_positions"],
        observed=fit["max_minus_min"], permutations=200)
    assert calibration["identity_check"] == pytest.approx(fit["max_minus_min"], abs=1e-12)
    assert calibration["permutations"] == 200 and calibration["percentile"] == 95.
    assert calibration["p_value"] == pytest.approx(1. / 201.)  # nothing beats a real effect
    assert calibration["exceeds_percentile_value"] is True
    assert calibration["percentile_value"] < fit["max_minus_min"]
    assert calibration["distribution"]["max"] < fit["max_minus_min"]
    assert "1 + #{permuted >= observed}" in calibration["definition"]


def test_the_permutation_p_value_is_the_count_it_says_it_is_and_is_deterministic():
    data = planted_design(coefficients=[0.] * 6, noise=.05, rows=400, positions=4, seed=17)
    fit = b12.label_regression(data["counts"], data["positions"], data["response"],
                               data["clusters"], n_positions=data["n_positions"])
    arguments = dict(n_positions=data["n_positions"], observed=fit["max_minus_min"],
                     permutations=100)
    first = b12.permutation_calibration(
        data["counts"], data["positions"], data["response"],
        b12.permutation_generator(782903, 100, "u"), **arguments)
    second = b12.permutation_calibration(
        data["counts"], data["positions"], data["response"],
        b12.permutation_generator(782903, 100, "u"), **arguments)
    assert first["distribution"] == second["distribution"]
    assert first["p_value"] == second["p_value"] == first["upper_p_value"]
    # the p-value is (1 + exceedances) / (1 + permutations), so it lies on that grid
    assert first["p_value"] * 101. == pytest.approx(round(first["p_value"] * 101.))
    assert 1. / 101. <= first["p_value"] <= 1.
    # under no planted effect the observed spread is an ordinary draw from its own distribution
    assert first["p_value"] > .01
    other = b12.permutation_calibration(
        data["counts"], data["positions"], data["response"],
        b12.permutation_generator(782903, 500, "u"), **arguments)
    assert other["distribution"] != first["distribution"]


def test_the_permutation_refuses_a_statistic_it_does_not_reproduce():
    data = planted_design(coefficients=[.1, 0., 0., 0., 0., -.1], rows=300, positions=3)
    with pytest.raises(ValueError, match="identity permutation"):
        b12.permutation_calibration(
            data["counts"], data["positions"], data["response"],
            b12.permutation_generator(782803, 50, "u"), n_positions=data["n_positions"],
            observed=99., permutations=10)


# ---------------------------------------------------------------------------
# the placebo, the non-additivity term and the whole response block
# ---------------------------------------------------------------------------


def commitments_from(data, *, team_labels=None, n_agents=6):
    """A pooled-commitment table in the shape `response_block` reads."""
    rows = data["response"].size
    generator = np.random.default_rng(29)
    team_labels = generator.integers(0, N_LABELS, size=rows) if team_labels is None else team_labels
    one_hot = np.zeros((rows, N_LABELS), dtype=np.float64)
    one_hot[np.arange(rows), team_labels] = 1.
    return {"counts": data["counts"], "position": data["positions"],
            "clusters": data["clusters"], "team_one_hot": one_hot,
            "homogeneity": (data["counts"] ** 2).sum(axis=1),
            "n_agents": n_agents,
            b12.UNDISCOUNTED: data["response"],
            b12.DISCOUNTED: data["response"] * .5}


def test_the_response_block_carries_the_regression_its_calibration_and_the_placebo():
    planted = [.10, -.02, .03, -.05, .01, -.07]
    planted = [value - float(np.mean(planted)) for value in planted]
    data = planted_design(coefficients=planted, rows=900, positions=3)
    block = b12.response_block(commitments_from(data), b12.UNDISCOUNTED, evaluation_seed=782803,
                               cap=50, n_positions=3, reporting_factor=6. / 500.)
    assert block["response"] == b12.UNDISCOUNTED
    assert block["agent_label_regression"]["max_minus_min"] == pytest.approx(
        max(planted) - min(planted), abs=.01)
    assert block["shows_the_ranking_spread_clause"] is True
    assert block["centred_coefficient_drop_invariance"]["max_absolute_difference"] < 1e-9
    assert block["centred_coefficient_drop_invariance"]["alternate_dropped_label"] == 0
    # the placebo is the same regression on the team label, which cannot have moved the reward
    assert block["placebo_regression"]["segments"] == 900
    assert block["placebo_spread_clause"] is False
    assert (block["placebo_regression"]["max_minus_min"]
            < block["agent_label_regression"]["max_minus_min"])
    assert "never reaches the low-level actor" in block["placebo_note"]
    assert "non_additivity" not in block  # cap 50 is not the non-additivity cap


def test_the_non_additivity_term_recovers_a_planted_coordination_effect():
    planted = [.02, .01, 0., -.01, -.01, -.01]
    planted = [value - float(np.mean(planted)) for value in planted]
    data = planted_design(coefficients=planted, rows=900, positions=1, homogeneity=.004,
                          noise=.01, seed=23)
    block = b12.response_block(commitments_from(data), b12.UNDISCOUNTED, evaluation_seed=782803,
                               cap=500, n_positions=1, reporting_factor=6. / 500.,
                               non_additivity=True)
    extra = block["non_additivity"]["model"]["extra"]
    assert extra["name"] == "sum_c n_c^2 (centred)"
    assert extra["coefficient"] == pytest.approx(.004, abs=.0008)
    assert extra["clustered_se"] > 0.
    calibration = block["non_additivity"]["permutation"]
    assert calibration["statistic"] == "extra coefficient"
    assert calibration["p_value"] < .05 and calibration["exceeds_percentile_value"] is True
    assert block["non_additivity"]["homogeneity_min"] >= 6.
    assert block["non_additivity"]["homogeneity_max"] <= 36.
    # the all-equal prediction and its conversion to an episode J
    prediction = block["all_equal_prediction"]
    assert prediction["is_a_mean_reward_per_step"] is True
    assert prediction["reporting_factor"] == pytest.approx(6. / 500.)
    for label in range(N_LABELS):
        assert prediction["episode_J_by_label"][str(label)] == pytest.approx(
            6. * prediction["prediction_by_label"][str(label)])
    assert prediction["episode_J_max_minus_min"] == pytest.approx(
        6. * prediction["max_minus_min"])
    assert "run_fsd_baseline_interruption_b01.py:254" in prediction["conversion"]


def test_the_discounted_response_carries_no_episode_J_conversion():
    data = planted_design(coefficients=[0.] * 6, rows=400, positions=1)
    block = b12.response_block(commitments_from(data), b12.DISCOUNTED, evaluation_seed=782803,
                               cap=500, n_positions=1, reporting_factor=6. / 500.,
                               non_additivity=True)
    assert block["all_equal_prediction"]["episode_J_by_label"] is None
    assert block["all_equal_prediction"]["episode_J_max_minus_min"] is None
    assert block["all_equal_prediction"]["is_a_mean_reward_per_step"] is False


def test_the_behaviour_block_reports_the_episode_return_and_its_native_score():
    returns = np.array([100., 120., 110., 130.])
    block = b12.behaviour_block(returns, horizon=500, n_uavs=6)
    assert block["lane_episodes"] == 4
    assert block["mean_episode_return_U"] == pytest.approx(115.)
    assert block["mean_episode_J"] == pytest.approx(6. * 115. / 500.)
    assert block["mean_reward_per_step"] == pytest.approx(115. / 500.)
    assert block["clustered_se_episode_J"] == pytest.approx(
        block["clustered_se_episode_return_U"] * 6. / 500.)


# ---------------------------------------------------------------------------
# synthetic published summaries and `reduce`
# ---------------------------------------------------------------------------


def regression_for(coefficients, *, segments=1000, clusters=256, team_size=6, positions=5):
    values = {label: float(coefficients[label]) for label in range(N_LABELS)}
    order, _ranked = b11.ranking_of(
        {str(label): {"coefficient": values[label]} for label in range(N_LABELS)}, "coefficient")
    spread = b11.spread_of(values)
    return {
        "segments": segments, "columns": 5 + positions, "rank": 5 + positions, "full_rank": True,
        "clusters": clusters, "positions": positions, "small_sample_correction": 1.,
        "dropped_label": 5,
        "centred_coefficients": {str(label): values[label] for label in range(N_LABELS)},
        "clustered_se": {str(label): .001 for label in range(N_LABELS)},
        "ranking": order, "best_label": spread["best_label"], "worst_label": spread["worst_label"],
        "max_minus_min": spread["max_minus_min"], "max_minus_min_clustered_se": .002,
        "drop_parametrised_coefficients": {str(label): values[label] - values[5]
                                           for label in range(N_LABELS)},
        "mean_position_effect": .2,
        "all_equal_prediction": {str(label): team_size * values[label] + .2
                                 for label in range(N_LABELS)},
        "residual_sd": .05, "r_squared": .01, "definition": "planted"}


def calibration_for(observed, percentile_value, *, p_value=.01):
    return {"permutations": 1000, "statistic": "centred coefficient spread",
            "observed": observed, "identity_check": observed, "percentile": 95.,
            "percentile_value": percentile_value,
            "exceeds_percentile_value": bool(observed > percentile_value),
            "p_value": p_value, "upper_p_value": p_value,
            "distribution": {"mean": percentile_value / 2., "sd": .001,
                             "min": 0., "max": percentile_value * 1.1,
                             "median": percentile_value / 2.},
            "definition": "planted"}


def cap_block(cap, *, coefficients, percentile_value, placebo_percentile=.5,
              placebo_spread=.1, prediction=None, rollouts=16, lanes=16):
    positions = max(1, 500 // cap)
    spread = max(coefficients) - min(coefficients)
    responses = {}
    for response in b12.RESPONSES:
        scale = 1. if response == b12.UNDISCOUNTED else .5
        scaled = [value * scale for value in coefficients]
        regression = regression_for(scaled, positions=positions)
        block = {
            "response": response, "response_definition": "planted",
            "mean": .1, "sd": .05,
            "agent_label_regression": regression,
            "agent_label_permutation": calibration_for(spread * scale,
                                                       percentile_value * scale),
            "centred_coefficient_drop_invariance": {"alternate_dropped_label": 0,
                                                    "max_absolute_difference": 0.,
                                                    "definition": "planted"},
            "placebo_regression": regression_for([placebo_spread * scale] + [0.] * 5, team_size=1,
                                                 positions=positions),
            "placebo_permutation": calibration_for(placebo_spread * scale,
                                                   placebo_percentile * scale, p_value=.4),
            "placebo_note": "the team label never reaches the low-level actor",
            "shows_the_ranking_spread_clause": bool(spread > percentile_value),
            "placebo_spread_clause": bool(placebo_spread > placebo_percentile)}
        if cap == b12.NON_ADDITIVITY_CAP:
            block["non_additivity"] = {
                "homogeneity_mean": 12., "homogeneity_min": 6., "homogeneity_max": 36.,
                "model": dict(regression, extra={"name": "sum_c n_c^2 (centred)",
                                                 "coefficient": .0005, "clustered_se": .0004,
                                                 "width": 1}),
                "permutation": {"permutations": 1000, "statistic": "extra coefficient",
                                "observed": .0005, "identity_check": .0005, "percentile": 95.,
                                "percentile_value": .0009,
                                "exceeds_percentile_value": False, "p_value": .3,
                                "upper_p_value": .3,
                                "distribution": {"mean": .0004, "sd": .0002, "min": 0.,
                                                 "max": .001, "median": .0004},
                                "definition": "planted"},
                "definition": "planted"}
            per_label = prediction if prediction is not None else [
                value * 6. for value in scaled]
            block["all_equal_prediction"] = {
                "response": response,
                "prediction_by_label": {str(label): per_label[label]
                                        for label in range(N_LABELS)},
                "max_minus_min": max(per_label) - min(per_label),
                "best_label": int(np.argmax(per_label)),
                "is_a_mean_reward_per_step": response == b12.UNDISCOUNTED,
                "reporting_factor": 6. / 500.,
                "episode_J_by_label": ({str(label): per_label[label] * 6.
                                        for label in range(N_LABELS)}
                                       if response == b12.UNDISCOUNTED else None),
                "episode_J_max_minus_min": ((max(per_label) - min(per_label)) * 6.
                                            if response == b12.UNDISCOUNTED else None),
                "conversion": "planted", "definition": "planted"}
        responses[response] = block
    return {
        "cap": cap, "rollouts": rollouts, "lane_episodes": rollouts * lanes,
        "commitments": rollouts * lanes * positions,
        "commitments_per_lane_episode": positions,
        "expected_team_rows_per_rollout": lanes * positions,
        "team_rows": rollouts * lanes * positions,
        "agent_rows": rollouts * lanes * positions * 6,
        "clusters": rollouts * lanes, "positions": positions,
        "mean_commitment_elapsed": float(min(cap, 500)),
        "responses": responses,
        "behaviour": {"lane_episodes": rollouts * lanes, "mean_episode_return_U": 25.,
                      "clustered_se_episode_return_U": .5, "mean_episode_J": .3,
                      "clustered_se_episode_J": .006, "mean_reward_per_step": .05,
                      "definition": "planted"},
        "label_law": {"agent_label_shares": [1. / 6.] * 6,
                      "agent_label_entropy_estimate": 1.78,
                      "uniform_entropy": math.log(6.)},
        "secondary_agent_advantage": {"agent_label_ranking": [0, 1, 2, 3, 4, 5],
                                      "reading_note": "arithmetic, not signal"},
        "discounted_reward_agreement": {"max_absolute_difference": 1e-7, "tolerance": 1e-5},
        "wall_seconds": 400.}


# The planted readings, chosen so every declared count has a known answer:
#   772803  cap 10 and 50 fail, 100 and 500 pass, best label 2 first     -> smallest passing 100
#   772903  cap 10 fails, 50, 100 and 500 pass, best label 2 second      -> smallest passing 50
#   773003  every cap fails, and the all-equal prediction spans little   -> the alternative
COEFFICIENTS = {
    772803: {10: [.001, .000, .002, .001, .000, .000], 50: [.002, .001, .004, .002, .001, .000],
             100: [.004, .002, .010, .003, .001, .000], 500: [.006, .003, .020, .004, .001, .000]},
    772903: {10: [.001, .000, .001, .000, .000, .000], 50: [.003, .008, .006, .001, .002, .000],
             100: [.004, .009, .008, .001, .002, .000], 500: [.005, .011, .010, .001, .002, .000]},
    773003: {cap: [.001, .002, .001, .000, .000, .000] for cap in b12.CAPS}}
PERCENTILE = {772803: {10: .004, 50: .006, 100: .006, 500: .006},
              772903: {10: .004, 50: .004, 100: .004, 500: .004},
              773003: {cap: .010 for cap in b12.CAPS}}
# 773003's cap-500 all-equal prediction spans .001 * 6 = .006 J, well under half of B10's .060
ALTERNATIVE_PREDICTION = [.0002, .0004, .0002, .0000, .0000, .0000]


def measures_for(seed, caps=b12.CAPS, **overrides):
    measures = {str(cap): cap_block(
        cap, coefficients=COEFFICIENTS[seed][cap], percentile_value=PERCENTILE[seed][cap],
        prediction=(ALTERNATIVE_PREDICTION if seed == 773003 and cap == b12.NON_ADDITIVITY_CAP
                    else None))
        for cap in caps}
    measures.update(overrides)
    return measures


def probe_summary(seed, sha="synthetic-source", **overrides):
    """A published probe summary of this object, in the shape `reduce` reads."""
    measures = overrides.pop("measures", None) or measures_for(seed)
    summary = {
        "object_id": b12.OBJECT_ID, "command": "probe", "status": "complete",
        "block_seed": seed, "evaluation_seed": b12.BLOCKS[seed], "launch_sha": sha,
        "caps": list(b12.CAPS), "rollouts_per_cap": 16,
        "responses": list(b12.RESPONSES), "primary_response": b12.PRIMARY_RESPONSE,
        "optimizer_steps": 0, "optimizer_calls": {},
        "weights_record": {"sha256": f"sha-{seed}"},
        "faithful_load": {"faithful_load": True, "first_differing_world": None},
        "learner_state": {"before": {"parameter_digest": "d"},
                          "after": {"parameter_digest": "d"}, "unchanged": True},
        "collection_rng": {"restored": True},
        "measures": measures, "reporting_factor": 6. / 500.,
        "as_trained_world_scores": [AS_TRAINED] * WORLDS, "J_as_trained": AS_TRAINED,
        "collection_geometry": [{"cap": 10, "rows_M": 800}],
        "update_law": {"gamma": .99, "lambda_h": .07, "ppo_epochs": 15},
        "wall_seconds": 1700.}
    summary.update(overrides)
    return summary


def supplied(sha="synthetic-source", b09_sha="b09-source", b10_sha="b10-source"):
    probes = [probe_summary(seed, sha) for seed in SEEDS]
    nine = [b09tests.probe_summary(seed, b09_sha) for seed in SEEDS]
    ten = [b10tests.probe_summary(seed, b10_sha) for seed in SEEDS]
    return probes, nine, ten


def test_the_synthetic_inputs_agree_with_b09s_and_b10s_own_probe_shapes():
    probes, nine, ten = supplied()
    for probe, b09_probe, b10_probe in zip(probes, nine, ten):
        scores = probe["as_trained_world_scores"]
        assert scores == b09_probe["rules_measured"]["as_trained"]["J_world_scores"]
        assert scores == b10_probe["rules_measured"]["as_trained"]["J_world_scores"]
        assert (probe["weights_record"]["sha256"] == b09_probe["weights_record"]["sha256"]
                == b10_probe["weights_record"]["sha256"])
    for seed, probe in zip(SEEDS, nine):
        assert b11.b09_probe_row(probe)["best_mean_action_label"] == BEST_LABEL[seed]
    for seed, probe in zip(SEEDS, ten):
        assert b12.b10_sampled_spread(b11.b10_probe_row(probe)) == pytest.approx(B10_SPREAD[seed])


def test_reduce_reads_three_probes_beside_b09s_and_b10s():
    probes, nine, ten = supplied()
    result = b12.reduce_inputs(probes, nine, ten)
    assert result["status"] == "complete" and result["object_id"] == b12.OBJECT_ID
    assert result["blocks_read"] == 3 and result["invalid_probes"] == {}
    assert result["invalid_b09_probes"] == {} and result["invalid_b10_probes"] == {}
    assert result["probe_launch_sha"] == "synthetic-source"
    assert result["b09_probe_launch_sha"] == "b09-source"
    assert result["b10_probe_launch_sha"] == "b10-source"
    assert result["caps"] == list(b12.CAPS) and result["primary_response"] == b12.UNDISCOUNTED
    assert result["reference_object_ids"] == [b11.OBJECT_ID, b10.OBJECT_ID, b09.OBJECT_ID,
                                              b08.OBJECT_ID]
    assert "wsl_4070" in result["interpretation_limit"]
    by_seed = {block["training_seed"]: block for block in result["blocks"]}
    for seed in SEEDS:
        block = by_seed[seed]
        assert block["status"] == "complete" and block["weights_match"] is True
        assert block["as_trained_identical_to_b09_and_b10"] is True
        assert block["best_mean_action_label"] == BEST_LABEL[seed]
        assert block["sampled_J_max_minus_min"] == pytest.approx(B10_SPREAD[seed])
        assert sorted(block["by_cap"]) == sorted(str(cap) for cap in b12.CAPS)
    # the criterion, cap by cap, exactly as the notebook declared it
    assert by_seed[772803]["caps_showing_the_ranking"] == [100, 500]
    assert by_seed[772803]["smallest_cap_showing_the_ranking"] == 100
    assert by_seed[772903]["caps_showing_the_ranking"] == [50, 100, 500]
    assert by_seed[772903]["smallest_cap_showing_the_ranking"] == 50
    assert by_seed[773003]["caps_showing_the_ranking"] == []
    assert by_seed[773003]["smallest_cap_showing_the_ranking"] is None
    assert not any(block["placebo_flag"] for block in result["blocks"])
    # both clauses are reported separately, on both responses
    cap100 = by_seed[772803]["by_cap"]["100"]
    for response in b12.RESPONSES:
        entry = cap100[response]
        assert entry["spread_exceeds_permutation_percentile"] is True
        assert entry["best_mean_action_label_rank"] == 1
        assert entry["best_mean_action_label_in_top_two"] is True
        assert entry["shows_the_ranking"] is True
        assert entry["placebo_passes_the_same_spread_test"] is False
        assert "declared before any score" in entry["criterion"]
    cap10 = by_seed[772803]["by_cap"]["10"][b12.UNDISCOUNTED]
    assert cap10["spread_exceeds_permutation_percentile"] is False
    assert cap10["shows_the_ranking"] is False
    # the rank agreement with B09's and B10's maps travels with every cap
    assert cap100["undiscounted_mean_reward_per_step"][
        "rank_correlation_with_sampled_b10"] is not None
    assert by_seed[772803]["rank_correlation_with_mean_action_b09_by_cap"]["500"] is not None
    # the across-block descriptions use the direction's own helper and wording
    assert result["spread_by_cap"]["500"]["available_blocks"] == 3
    assert "working_model" in result["spread_by_cap"]["500"]
    assert result["blocks_showing_the_ranking_by_cap"]["500"] == [772803, 772903]
    assert result["blocks_showing_the_ranking_by_cap"]["10"] == []
    assert result["smallest_cap_showing_the_ranking_by_block"]["772903"] == 50
    assert result["wall_seconds_by_cap"]["10"]["mean"] == pytest.approx(400.)


def test_the_predictions_are_counted_where_they_are_read():
    probes, nine, ten = supplied()
    predictions = b12.reduce_inputs(probes, nine, ten)["predictions"]
    first = predictions["P1_cap_10_fails_the_criterion"]
    assert first["blocks_considered"] == SEEDS and first["blocks_read"] == 3
    assert first["blocks_holding"] == 3  # cap 10 fails on every planted block
    second = predictions["P2_cap_500_passes_the_criterion"]
    assert second["blocks_holding"] == 2 and second["per_block"]["773003"]["holds"] is False
    third = predictions["P3_the_smallest_passing_cap_is_50_or_100"]
    assert third["blocks_holding"] == 2
    assert third["per_block"]["772803"]["value"] == 100
    assert third["per_block"]["772903"]["value"] == 50
    assert third["per_block"]["773003"]["value"] is None
    alternative = predictions["ALTERNATIVE_the_map_is_joint_not_additive"]
    assert alternative["blocks_holding"] == 1
    value = alternative["per_block"]["773003"]["value"]
    assert value["cap_500_shows_the_ranking"] is False
    assert value["prediction_below_half_of_b10_sampled_spread"] is True
    assert value["all_equal_prediction_J_max_minus_min"] == pytest.approx(.0004 * 6.)
    assert value["b10_sampled_J_max_minus_min"] == pytest.approx(B10_SPREAD[773003])
    assert alternative["per_block"]["772903"]["holds"] is False
    placebo = predictions["PLACEBO_no_cap_has_a_passing_placebo"]
    assert placebo["blocks_holding"] == 3 and placebo["per_block"]["772803"]["value"] == []
    assert "not a prediction" in placebo["statement"]
    assert "counted nowhere" in predictions["counting_note"]
    # a block that is not read is counted as not read, and never as holding
    partial = b12.reduce_inputs(probes[:1], nine[:1], ten[:1])
    assert partial["status"] == "incomplete" and partial["blocks_read"] == 1
    rows = partial["predictions"]["P2_cap_500_passes_the_criterion"]
    assert rows["blocks_read"] == 1 and rows["per_block"]["772903"]["read"] is False


def test_a_passing_placebo_is_flagged_on_the_cap_it_invalidates():
    probes, nine, ten = supplied()
    damaged = measures_for(772903)
    for response in b12.RESPONSES:
        damaged["100"]["responses"][response]["placebo_permutation"][
            "exceeds_percentile_value"] = True
    probes[1] = probe_summary(772903, measures=damaged)
    result = b12.reduce_inputs(probes, nine, ten)
    block = [entry for entry in result["blocks"] if entry["training_seed"] == 772903][0]
    assert block["caps_with_a_passing_placebo"] == [100]
    assert block["placebo_flag"] is True
    assert block["by_cap"]["100"][b12.UNDISCOUNTED][
        "placebo_invalidates_this_reading"] is True
    assert result["placebo_flag_by_block"]["772903"] is True
    assert result["predictions"]["PLACEBO_no_cap_has_a_passing_placebo"]["blocks_holding"] == 2


def test_the_criterions_second_clause_can_fail_on_its_own():
    """A cap whose spread beats its calibration but whose ranking does not put B09's best first."""
    probes, nine, ten = supplied()
    damaged = measures_for(772803)
    # label 5 first, B09's best label 2 fourth: the spread clause holds, the ranking clause does not
    upended = [.001, .002, .003, .004, .005, .020]
    for response in b12.RESPONSES:
        scale = 1. if response == b12.UNDISCOUNTED else .5
        block = damaged["500"]["responses"][response]
        block["agent_label_regression"] = regression_for([value * scale for value in upended],
                                                         positions=1)
        block["agent_label_permutation"] = calibration_for(
            (max(upended) - min(upended)) * scale, .006 * scale)
    probes[0] = probe_summary(772803, measures=damaged)
    result = b12.reduce_inputs(probes, nine, ten)
    block = result["blocks"][0]["by_cap"]["500"][b12.UNDISCOUNTED]
    assert block["spread_exceeds_permutation_percentile"] is True
    assert block["best_mean_action_label_rank"] == 4
    assert block["best_mean_action_label_in_top_two"] is False
    assert block["shows_the_ranking"] is False
    assert result["blocks"][0]["caps_showing_the_ranking"] == [100]


@pytest.mark.parametrize("damage,message", [
    ({"status": "incomplete"}, "incomplete probe"),
    ({"optimizer_steps": 1}, "optimizer step"),
    ({"faithful_load": {"faithful_load": False}}, "faithful load"),
    ({"learner_state": {"unchanged": False}}, "unchanged parameters"),
    ({"object_id": "SOMETHING_ELSE"}, "not a probe of this object"),
    ({"block_seed": 999}, "not one of this object's three blocks"),
    ({"as_trained_world_scores": []}, "no `as_trained` world scores"),
    ({"caps": []}, "one measured block per declared cap"),
])
def test_reduce_refuses_a_probe_that_is_not_this_objects_complete_zero_step_one(damage, message):
    with pytest.raises(ValueError, match=message):
        b12.probe_row(probe_summary(772803, **damage))


def test_reduce_refuses_a_probe_without_the_tables_every_cap_needs():
    short = measures_for(772803)
    short["500"]["responses"][b12.UNDISCOUNTED]["agent_label_regression"][
        "centred_coefficients"].pop("5")
    with pytest.raises(ValueError, match="six-label coefficient table"):
        b12.probe_row(probe_summary(772803, measures=short))
    missing = measures_for(772803)
    missing["50"]["responses"][b12.DISCOUNTED]["agent_label_permutation"] = None
    with pytest.raises(ValueError, match="permutation calibration"):
        b12.probe_row(probe_summary(772803, measures=missing))
    no_regression = measures_for(772803)
    no_regression["100"]["responses"][b12.UNDISCOUNTED]["agent_label_regression"] = None
    with pytest.raises(ValueError, match="carries no undiscounted"):
        b12.probe_row(probe_summary(772803, measures=no_regression))
    empty = measures_for(772803)
    empty["10"]["rollouts"] = 0
    with pytest.raises(ValueError, match="no collected rollout"):
        b12.probe_row(probe_summary(772803, measures=empty))
    partial = measures_for(772803, caps=(10, 50))
    with pytest.raises(ValueError, match="one measured block per declared cap"):
        b12.probe_row(probe_summary(772803, measures=partial))


def test_reduce_refuses_mixed_launch_shas_duplicate_blocks_and_mixed_cap_sets():
    probes, nine, ten = supplied()
    mixed = [probe_summary(SEEDS[0], "one"), probe_summary(SEEDS[1], "another")]
    with pytest.raises(ValueError, match="mixed launch shas"):
        b12.reduce_inputs(mixed, nine, ten)
    with pytest.raises(ValueError, match="duplicate this object's probe block"):
        b12.reduce_inputs(probes + [probe_summary(SEEDS[0])], nine, ten)
    with pytest.raises(ValueError, match="duplicate B09 probe block"):
        b12.reduce_inputs(probes, nine + [nine[0]], ten)
    with pytest.raises(ValueError, match="duplicate B10 probe block"):
        b12.reduce_inputs(probes, nine, ten + [ten[0]])
    others = list(probes)
    others[2] = probe_summary(SEEDS[2], caps=[10, 50], measures=measures_for(SEEDS[2],
                                                                            caps=(10, 50)))
    with pytest.raises(ValueError, match="one set of caps"):
        b12.reduce_inputs(others, nine, ten)


def test_reduce_refuses_a_block_whose_checkpoint_or_panel_is_not_b09s_and_b10s():
    probes, nine, ten = supplied()
    probes[0] = probe_summary(SEEDS[0], weights_record={"sha256": "another-checkpoint"})
    probes[1] = probe_summary(SEEDS[1], as_trained_world_scores=[AS_TRAINED + 1.] * WORLDS)
    result = b12.reduce_inputs(probes, nine, ten)
    assert result["status"] == "incomplete" and result["blocks_read"] == 1
    assert "weights" in result["blocks"][0]["missing_or_invalid"]
    assert result["blocks"][0]["weights_match"] is False
    assert "as_trained" in result["blocks"][1]["missing_or_invalid"]
    assert result["blocks"][1]["as_trained_identical_to_b09_and_b10"] is False
    without = b12.reduce_inputs(*supplied()[:2], ten[:2])
    assert without["blocks"][2]["missing_or_invalid"]["b10_probe"] == "not supplied"
    assert without["status"] == "incomplete"


def test_reduce_refuses_a_b09_or_b10_probe_its_own_reader_refuses():
    probes, nine, ten = supplied()
    nine[0] = dict(nine[0], status="incomplete")
    ten[1] = dict(ten[1], optimizer_steps=3)
    result = b12.reduce_inputs(probes, nine, ten)
    assert result["blocks_read"] == 1
    assert "incomplete probe" in result["invalid_b09_probes"][str(SEEDS[0])]
    assert "optimizer step" in result["invalid_b10_probes"][str(SEEDS[1])]


def test_reduce_writes_a_summary_and_reports_its_status(tmp_path):
    probes, nine, ten = supplied()
    paths = []
    for name, batch in (("probe", probes), ("b09", nine), ("b10", ten)):
        for summary in batch:
            path = tmp_path / f"{name}_{summary['block_seed']}.json"
            path.write_text(__import__("json").dumps(summary), encoding="utf-8")
            paths.append((name, path))
    arguments = ["reduce", "--output-root", str(tmp_path / "reduce")]
    for flag, name in (("--probes", "probe"), ("--b09-probes", "b09"), ("--b10-probes", "b10")):
        arguments.append(flag)
        arguments.extend(str(path) for kind, path in paths if kind == name)
    assert b12.main(arguments) == 0
    written = __import__("json").loads(
        (tmp_path / "reduce" / "summary.json").read_text(encoding="utf-8"))
    assert written["status"] == "complete" and written["blocks_read"] == 3
    assert len(written["input_probes"]) == 3
    assert written["object_id"] == b12.OBJECT_ID
