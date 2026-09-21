"""The coordinator-signal entry: the seeds, the measure arithmetic and `reduce`.

Planted arrays and synthetic published summaries only; the real stack - the frozen collector's own
calls, the real D2 route and the comparison with the real `update_coordinator_d2` path - is in
`test_coordinator_signal_real_tiny.py`. The synthetic B09 and B10 probe summaries are those
objects' own test fixtures, loaded by path the way B10's tests load B09's, so the three objects are
compared through one shape and not three. Technical checks: nothing here asserts the direction or
the size of any measured quantity.
"""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


b09tests = _load("fsd_coordinator_signal_b09_fixtures", "label_map_b09/test_label_map.py")
b10tests = _load("fsd_coordinator_signal_b10_fixtures",
                 "label_map_sampled_b10/test_label_map_sampled.py")

import run_fsd_coordinator_signal_b11 as b11  # noqa: E402
import run_fsd_label_content_b08 as b08  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402
import run_fsd_label_map_sampled_b10 as b10  # noqa: E402

SEEDS = sorted(b11.BLOCKS)
WORLDS = b09tests.WORLDS
AS_TRAINED = b09tests.AS_TRAINED
# B09's synthetic mean-action map (`b09tests.CONSTANTS`) orders the labels
#   772803 [2, 3, 1, 0, 4, 5]   772903 [2, 1, 4, 0, 3, 5]   773003 [1, 2, 0, 3, 4, 5].
# The planted advantage tables below are chosen against it:
#   772803  the same order                      -> rank correlation +1
#   772903  label 1 first and label 0 last      -> E2a's second clause holds
#   773003  exactly B09's order reversed        -> rank correlation -1
ADVANTAGE = {772803: [.3, .4, .6, .5, .2, .1],
             772903: [.1, .6, .5, .3, .4, .2],
             773003: [.3, .1, .2, .4, .5, .6]}
# The perfect-credit reference's coefficients: the same order as the advantage on 772803 and
# 772903, and a flat table on 773003 (every coefficient equal, so its spread is zero).
COEFFICIENTS = {772803: [.03, .04, .06, .05, .02, .01],
                772903: [.01, .06, .05, .03, .04, .02],
                773003: [.02] * 6}
SPREAD_SE = {772803: .1, 772903: .05, 773003: .3}  # E2a holds on 772803 and 772903, not on 773003
COEFFICIENT_GAP_SE = {772803: .005, 772903: .004, 773003: .01}


# ---------------------------------------------------------------------------
# identity, seeds and the source map
# ---------------------------------------------------------------------------


def test_the_object_identity_and_the_declared_collection():
    assert b11.OBJECT_ID == "FSD_COORDINATOR_SIGNAL_B11"
    assert b11.CARD.endswith("(2026-09-20 16:40 PDT, next research judgment, B11)")
    assert "NOTES.md" in b11.CARD and "flexible_skill_duration" in b11.CARD
    assert b11.ROLLOUTS == 4 and b11.N_LABELS == 6 == b09.N_LABELS
    assert b11.BLOCKS == b09.BLOCKS == b10.BLOCKS
    assert b11.SAVE_ARM == b09.SAVE_ARM and b11.BASELINE_RULE == "as_trained"
    assert b11.SPREAD_MULTIPLE == 2. and b11.BOOTSTRAP_RESAMPLES == 1000
    assert b11.CAUSES_EXPECTED == ("reset", "team_cap")
    assert "wsl_4070" in b11.INTERPRETATION_LIMIT
    assert "end of training" in b11.INTERPRETATION_LIMIT  # the one limit the entry named
    assert "not the fit's worlds" in b11.INTERPRETATION_LIMIT


def test_the_source_map_carries_the_file_line_facts_it_claims():
    notes = b11.SOURCE_NOTES
    assert "run_fsd_baseline_interruption_b01.py:95-151" in notes["collector_transcription"]
    assert "hmasd/agent.py:7029-7097" in notes["bootstrap"]
    assert "hmasd/agent.py:6046-6050" in notes["advantages"]
    assert "hmasd/utils.py:894" in notes["advantages"] and "1018" in notes["advantages"]
    assert "hmasd/agent.py:2348-2355" in notes["segment_reward"]
    assert "hmasd/agent.py:6153-6164" in notes["standardisation"]
    assert "hmasd/agent.py:6075-6078" in notes["no_update"]
    assert "hmasd/networks.py:1801-1809" in notes["team_label_is_a_placebo"]
    assert "hmasd/utils.py:567-599" in notes["row_geometry"]
    assert "hmasd/utils.py:551-553" in notes["score_function_estimate"]
    # the frozen collector this object transcribes is recorded, by name, lines and digest
    record = b11.frozen_collector_source()
    assert record["function"].endswith("collect_training")
    assert len(record["sha256"]) == 64 and "-" in record["lines"]


def test_the_collection_seeds_are_a_function_of_the_block_and_the_rollout():
    seeds = {(seed, rollout): b11.collection_seed(seed, rollout)
             for seed in SEEDS for rollout in range(4)}
    assert len(set(seeds.values())) == len(seeds)  # every rollout of every block its own stream
    assert all(0 <= value < 2 ** 31 for value in seeds.values())  # numpy.random.seed accepts it
    assert b11.collection_seed(772903, 2) == b11.collection_seed(772903, 2)
    assert b11.collection_seed(772903, 2) != b11.collection_seed(772803, 2)
    assert "sha256" in b11.SEED_DERIVATION and "seed_rng" in b11.SEED_DERIVATION
    # the collection lanes are the block's own, offset off the fit's first rollout
    for seed in SEEDS:
        base = b11.world_base_seed(seed)
        assert base == seed + 500
        lanes = list(range(base, base + 16))
        assert not set(lanes) & set(range(seed, seed + 16))  # not the fit's training lanes
        for other in SEEDS:
            assert not set(lanes) & set(range(other, other + 16))
            assert not set(lanes) & set(range(b11.BLOCKS[other], b11.BLOCKS[other] + 32))
    # the bootstrap generator is dedicated and reproducible
    first = b11.bootstrap_generator(772803).integers(0, 10, 5).tolist()
    assert first == b11.bootstrap_generator(772803).integers(0, 10, 5).tolist()
    assert first != b11.bootstrap_generator(772903).integers(0, 10, 5).tolist()


# ---------------------------------------------------------------------------
# the standardisation: the update's own inline formula
# ---------------------------------------------------------------------------


def inline_standardisation(team_advantages, agent_advantages, team_mask, agent_mask):
    """hmasd/agent.py:6153-6164, retyped here so the object's helper is checked against it."""
    batch = {"team_advantages": torch.as_tensor(team_advantages, dtype=torch.float32),
             "agent_advantages": torch.as_tensor(agent_advantages, dtype=torch.float32)}
    team_mask = torch.as_tensor(team_mask, dtype=torch.float32)
    agent_mask = torch.as_tensor(agent_mask, dtype=torch.float32)
    team_advantages_batch = batch["team_advantages"] * team_mask
    agent_advantages_batch = batch["agent_advantages"] * agent_mask
    all_advantages = torch.cat(
        [team_advantages_batch.reshape(-1), agent_advantages_batch.reshape(-1)], dim=0)
    all_mask = torch.cat([team_mask.reshape(-1), agent_mask.reshape(-1)], dim=0)
    mask_total = torch.clamp(all_mask.sum(), min=1.0)
    global_mean = (all_advantages * all_mask).sum() / mask_total
    global_var = ((all_advantages - global_mean) ** 2 * all_mask).sum() / mask_total
    global_std = torch.sqrt(global_var) + 1e-8
    return ((batch["team_advantages"] - global_mean) / global_std,
            (batch["agent_advantages"] - global_mean) / global_std,
            float(global_mean), float(global_std))


@pytest.mark.parametrize("masked", [False, True])
def test_the_standardisation_is_the_updates_own_inline_arithmetic(masked):
    generator = np.random.default_rng(7)
    team = generator.normal(size=9).astype(np.float64)
    agent = generator.normal(size=(9, 6)).astype(np.float64)
    team_mask = np.ones(9, dtype=np.float64)
    agent_mask = np.ones((9, 6), dtype=np.float64)
    if masked:  # an invalid row contributes to neither the mean nor the variance
        team_mask[3] = 0.
        agent_mask[5, 2] = 0.
        agent_mask[7, :] = 0.
    ours = b11.standardise_minibatch(team, agent, team_mask, agent_mask)
    team_std, agent_std, mean, std = inline_standardisation(team, agent, team_mask, agent_mask)
    assert np.array_equal(ours["team"], team_std.numpy().astype(np.float64))
    assert np.array_equal(ours["agent"], agent_std.numpy().astype(np.float64))
    assert ours["mean"] == mean and ours["std"] == std
    assert ours["masked_entries"] == int(team_mask.sum() + agent_mask.sum())
    assert "6153-6164" in ours["definition"]
    # one shared mean and standard deviation over both heads, not one per head
    valid = np.concatenate([team[team_mask > 0], agent[agent_mask > 0]])
    assert ours["mean"] == pytest.approx(float(valid.mean()), rel=1e-6)
    assert ours["std"] == pytest.approx(float(valid.std()) + 1e-8, rel=1e-6)


# ---------------------------------------------------------------------------
# the tables, the clustered errors and the bootstrap
# ---------------------------------------------------------------------------


def planted_rows(labels, advantages, clusters, *, returns=None, values=None):
    rows = {"rollout": np.zeros(len(labels), dtype=np.int64),
            "lane": np.asarray(clusters, dtype=np.int64),
            "label": np.asarray(labels, dtype=np.int64),
            "advantage": np.asarray(advantages, dtype=np.float64),
            "standardised_advantage": np.asarray(advantages, dtype=np.float64) * 2.,
            "return": np.asarray(returns if returns is not None else advantages, dtype=np.float64),
            "value": np.asarray(values if values is not None else advantages, dtype=np.float64),
            "reward": np.asarray(advantages, dtype=np.float64),
            "old_log_prob": np.full(len(labels), -math.log(6.), dtype=np.float64)}
    return rows


def test_the_cluster_index_is_the_rollout_and_the_lane():
    rows = {"rollout": np.array([0, 0, 1, 1, 2]), "lane": np.array([0, 3, 0, 3, 1])}
    clusters = b11.clusters_of(rows)
    assert len(set(clusters.tolist())) == 5  # a lane of another rollout is another cluster
    assert clusters[0] != clusters[2] and clusters[0] != clusters[1]
    means = b11.cluster_means([1., 3., 5., 7., 9.], clusters)
    assert means.tolist() == [1., 3., 5., 7., 9.]
    # two rows in one cluster share a mean
    same = b11.clusters_of({"rollout": np.array([0, 0]), "lane": np.array([2, 2])})
    assert b11.cluster_means([1., 3.], same).tolist() == [2.]


def test_the_label_table_carries_counts_shares_and_two_standard_errors():
    labels = [0, 0, 0, 0, 1, 1, 2, 2]
    advantages = [1., 2., 3., 4., 10., 12., -1., -3.]
    clusters = [0, 0, 1, 1, 0, 1, 0, 1]  # two lanes, so a label has two cluster means
    rows = planted_rows(labels, advantages, clusters)
    table = b11.label_table(rows, b11.clusters_of(rows))
    assert sorted(table) == [str(label) for label in range(6)]
    assert table["0"]["count"] == 4 and table["0"]["share"] == pytest.approx(.5)
    assert table["0"]["mean_advantage"] == pytest.approx(2.5)
    assert table["0"]["se_advantage"] == pytest.approx(
        float(np.std([1., 2., 3., 4.], ddof=1) / math.sqrt(4)))
    assert table["0"]["clusters"] == 2
    assert table["0"]["mean_of_cluster_means"] == pytest.approx(2.5)
    assert table["0"]["clustered_se_advantage"] == pytest.approx(
        float(np.std([1.5, 3.5], ddof=1) / math.sqrt(2)))
    assert table["1"]["mean_advantage"] == pytest.approx(11.)
    assert table["3"]["count"] == 0 and table["3"]["mean_advantage"] is None
    assert table["3"]["clustered_se_advantage"] is None
    assert table["0"]["mean_standardised_advantage"] == pytest.approx(5.)
    order, values = b11.ranking_of(table, "mean_advantage")
    assert order == [1, 0, 2]  # the labels that carry a value, highest first
    assert b11.spread_of(values)["max_minus_min"] == pytest.approx(11. - (-2.))
    assert b11.spread_of(values)["best_label"] == 1 and b11.spread_of(values)["worst_label"] == 2
    assert b11.rank_of(order, 0) == 2 and b11.rank_of(order, 5) is None


def test_the_ranking_breaks_an_exact_tie_by_the_lowest_label():
    table = {str(label): {"mean_advantage": 1.} for label in range(6)}
    table["4"]["mean_advantage"] = 2.
    order, _values = b11.ranking_of(table, "mean_advantage")
    assert order == [4, 0, 1, 2, 3, 5]


def test_eta_squared_is_the_between_label_share_of_the_variance():
    labels = np.array([0, 0, 1, 1])
    assert b11.eta_squared(np.array([1., 1., 3., 3.]), labels) == pytest.approx(1.)
    assert b11.eta_squared(np.array([1., 3., 1., 3.]), labels) == pytest.approx(0.)
    assert b11.eta_squared(np.array([2., 2., 2., 2.]), labels) is None  # no variance at all
    mixed = b11.eta_squared(np.array([0., 2., 3., 5.]), labels)
    assert 0. < mixed < 1.


def test_the_spread_bootstrap_is_reproducible_and_counts_what_it_dropped():
    generator = np.random.default_rng(3)
    labels, advantages, clusters = [], [], []
    for cluster in range(8):
        for label in range(6):
            for _row in range(3):
                labels.append(label)
                clusters.append(cluster)
                advantages.append(label * .1 + generator.normal(scale=.01))
    rows = planted_rows(labels, advantages, clusters)
    keys = b11.clusters_of(rows)
    first = b11.spread_bootstrap(rows["advantage"], rows["label"], keys,
                                 b11.bootstrap_generator(772803))
    second = b11.spread_bootstrap(rows["advantage"], rows["label"], keys,
                                  b11.bootstrap_generator(772803))
    assert first["clustered_se"] == second["clustered_se"]
    assert first["percentile_interval"] == second["percentile_interval"]
    assert first["clusters"] == 8 and first["resamples"] == 1000
    assert first["usable_resamples"] == 1000  # every cluster carries every label here
    assert first["interval_percentiles"] == [2.5, 97.5]
    assert first["clustered_se"] > 0.
    low, high = first["percentile_interval"]
    assert low <= first["bootstrap_mean"] <= high
    assert "resampled with replacement" in first["definition"]
    # a label that lives in one cluster only loses resamples, and the loss is counted
    rare = dict(rows)
    rare["label"] = rows["label"].copy()
    rare["label"][(keys > 0)] = np.where(rare["label"][(keys > 0)] == 5, 4,
                                         rare["label"][(keys > 0)])
    sparse = b11.spread_bootstrap(rare["advantage"], rare["label"], keys,
                                  b11.bootstrap_generator(772803))
    assert sparse["usable_resamples"] < sparse["resamples"]
    # fewer than two clusters cannot carry a cluster bootstrap
    assert b11.spread_bootstrap(rows["advantage"], rows["label"], np.zeros_like(keys),
                                b11.bootstrap_generator(772803)) is None


# ---------------------------------------------------------------------------
# the perfect-credit reference
# ---------------------------------------------------------------------------


def planted_segments(coefficients, segments=240, noise=0., seed=11, state=None):
    """Segments of six agents with random labels; the reward is additive in the label counts."""
    generator = np.random.default_rng(seed)
    labels = generator.integers(0, 6, size=(segments, 6))
    counts = np.stack([(labels == label).sum(axis=1) for label in range(6)], axis=1)
    reward = counts @ np.asarray(coefficients, dtype=np.float64)
    values = generator.normal(size=segments)
    if state is not None:
        reward = reward + state * values
    if noise:
        reward = reward + generator.normal(scale=noise, size=segments)
    clusters = np.repeat(np.arange(segments // 10), 10)[:segments]
    return counts.astype(np.float64), reward, clusters, values


def test_the_additive_model_recovers_planted_coefficients():
    planted = [.05, .10, -.02, .00, .07, .03]
    counts, reward, clusters, _values = planted_segments(planted)
    fit = b11.additive_model(counts, reward, clusters)
    assert fit["segments"] == 240 and fit["columns"] == 6 and fit["rank"] == 6
    assert fit["state_control"] is False and fit["value_coefficient"] is None
    for label in range(6):
        assert fit["coefficients"][str(label)] == pytest.approx(planted[label], abs=1e-9)
        assert fit["clustered_se"][str(label)] == pytest.approx(0., abs=1e-9)  # an exact fit
    assert fit["best_label"] == 1 and fit["worst_label"] == 2
    assert fit["max_minus_min"] == pytest.approx(.10 - (-.02))
    assert fit["ranking"] == [1, 4, 0, 5, 3, 2]
    assert fit["r_squared"] == pytest.approx(1.)
    assert "perfect-credit reference" in fit["definition"]
    assert fit["clusters"] == 24


def test_the_additive_model_with_noise_and_with_a_state_control():
    planted = [.05, .10, -.02, .00, .07, .03]
    counts, reward, clusters, values = planted_segments(planted, noise=.02, state=.5)
    plain = b11.additive_model(counts, reward, clusters)
    controlled = b11.additive_model(counts, reward, clusters, value=values)
    assert controlled["state_control"] is True and controlled["columns"] == 7
    assert controlled["value_coefficient"] == pytest.approx(.5, abs=.02)
    assert controlled["value_clustered_se"] is not None
    for label in range(6):
        assert controlled["coefficients"][str(label)] == pytest.approx(planted[label], abs=.02)
        assert controlled["clustered_se"][str(label)] > 0.
    # the state control removes a source of segment variance, so the fit is tighter
    assert controlled["r_squared"] > plain["r_squared"]
    assert controlled["max_minus_min_clustered_se"] > 0.


def test_the_clustered_covariance_is_the_sandwich_it_claims():
    planted = [.05, .10, -.02, .00, .07, .03]
    counts, reward, clusters, _values = planted_segments(planted, noise=.05)
    beta, _residuals, _rank, _singular = np.linalg.lstsq(counts, reward, rcond=None)
    errors = reward - counts @ beta
    covariance, groups, scale = b11.clustered_covariance(counts, errors, clusters)
    bread = np.linalg.pinv(counts.T @ counts)
    meat = np.zeros((6, 6))
    for key in np.unique(clusters):
        mask = clusters == key
        score = counts[mask].T @ errors[mask]
        meat += np.outer(score, score)
    expected = bread @ meat @ bread
    correction = (groups / (groups - 1.)) * ((len(reward) - 1.) / (len(reward) - 6))
    assert scale == pytest.approx(correction)
    assert np.allclose(covariance, expected * correction)
    assert groups == 24
    plain, _groups, plain_scale = b11.clustered_covariance(counts, errors, clusters,
                                                           correction=False)
    assert plain_scale == 1. and np.allclose(plain, expected)
    # the standard error of the best-minus-worst gap is the paired one, not a sum of two
    fit = b11.additive_model(counts, reward, clusters)
    best, worst = fit["best_label"], fit["worst_label"]
    paired = math.sqrt(covariance[best, best] + covariance[worst, worst]
                       - 2. * covariance[best, worst])
    assert fit["max_minus_min_clustered_se"] == pytest.approx(paired)


# ---------------------------------------------------------------------------
# the executed law and the descriptive gradient block
# ---------------------------------------------------------------------------


def test_the_label_law_is_the_executed_shares_and_the_entropy_estimate():
    labels = [0, 0, 1, 2, 2, 2]
    rows = planted_rows(labels, [1.] * 6, [0] * 6)
    rows["old_log_prob"] = np.full(6, -math.log(6.))  # a flat law, exactly
    team = planted_rows([1, 1], [1., 1.], [0, 1])
    team["old_log_prob"] = np.full(2, -math.log(3.))
    law = b11.law_summary(rows, team)
    assert law["agent_label_counts"] == [2, 1, 3, 0, 0, 0]
    assert law["agent_label_shares"][2] == pytest.approx(.5)
    assert law["agent_label_entropy_estimate"] == pytest.approx(math.log(6.))
    assert law["uniform_entropy"] == pytest.approx(math.log(6.))
    assert law["agent_entropy_gap_to_uniform"] == pytest.approx(0.)
    assert law["team_label_entropy_estimate"] == pytest.approx(math.log(3.))
    assert law["mean_chosen_agent_label_probability"] == pytest.approx(1. / 6.)


def test_the_policy_gradient_block_is_the_shares_score_function_estimate():
    labels = [0, 0, 1, 1, 2, 2]
    rows = planted_rows(labels, [0., 0., 0., 0., 0., 0.], [0] * 6)
    rows["standardised_advantage"] = np.array([1., 1., -1., -1., 0., 0.])
    law = b11.law_summary(rows, planted_rows([0], [0.], [0]))
    block = b11.policy_gradient_block(rows, law, .07)
    assert block["estimator"] == "score_function_with_shares_as_q"
    assert block["mean_standardised_advantage"] == pytest.approx(0.)
    for label, expected in ((0, 2. / 6.), (1, -2. / 6.), (2, 0.)):
        entry = block["per_label"][str(label)]
        assert entry["share"] == pytest.approx(1. / 3.)
        assert entry["mean_standardised_advantage_indicator"] == pytest.approx(expected)
        assert entry["policy_gradient_pull"] == pytest.approx(expected)  # the mean is zero here
    assert block["max_minus_min"] == pytest.approx(4. / 6.)
    assert block["entropy_coefficient_lambda_h"] == pytest.approx(.07)
    assert block["label_law_entropy_gap_to_ln6"] is not None
    assert "descriptive, approximate" in block["reading_note"]
    assert "1[label = c]" in b11.SOURCE_NOTES["score_function_estimate"]


# ---------------------------------------------------------------------------
# synthetic published summaries and `reduce`
# ---------------------------------------------------------------------------


def measures_for(seed, *, advantage=None, coefficients=None, spread_se=None, gap_se=None,
                 rollouts=4):
    """This object's published measures, planted so every reading has a known answer."""
    advantage = list(ADVANTAGE[seed] if advantage is None else advantage)
    coefficients = list(COEFFICIENTS[seed] if coefficients is None else coefficients)
    spread_se = SPREAD_SE[seed] if spread_se is None else spread_se
    gap_se = COEFFICIENT_GAP_SE[seed] if gap_se is None else gap_se
    table = {str(label): {"label": label, "count": 100, "share": 1. / 6.,
                          "mean_advantage": advantage[label], "se_advantage": .01,
                          "clustered_se_advantage": .02,
                          "mean_standardised_advantage": advantage[label] * 2.,
                          "mean_return": advantage[label], "mean_value": .5,
                          "clusters": 64, "mean_of_cluster_means": advantage[label]}
             for label in range(6)}
    order, values = b11.ranking_of(table, "mean_advantage")
    spread = b11.spread_of(values)
    team_table = {str(label): dict(table[str(label)], mean_advantage=.5) for label in range(6)}
    reference_table = {str(label): {"coefficient": coefficients[label]} for label in range(6)}
    reference_order, reference_values = b11.ranking_of(reference_table, "coefficient")
    reference_spread = b11.spread_of(reference_values)
    return {
        "rollouts": rollouts, "agent_rows": 600 * rollouts, "team_rows": 100 * rollouts,
        "clusters": 16 * rollouts,
        "agent_label_table": table,
        "agent_label_ranking": order,
        "agent_label_mean_advantage": {str(label): advantage[label] for label in range(6)},
        "agent_label_spread": spread,
        "agent_label_spread_bootstrap": {"clusters": 16 * rollouts, "resamples": 1000,
                                         "usable_resamples": 1000, "clustered_se": spread_se,
                                         "percentile_interval": [spread["max_minus_min"] - .01,
                                                                 spread["max_minus_min"] + .01],
                                         "interval_percentiles": [2.5, 97.5],
                                         "bootstrap_mean": spread["max_minus_min"]},
        "agent_label_spread_over_clustered_se": spread["max_minus_min"] / spread_se,
        "agent_label_spread_exceeds_twice_its_clustered_se": bool(
            spread["max_minus_min"] > 2. * spread_se),
        "agent_advantage_eta_squared": .02,
        "agent_standardised_advantage_eta_squared": .02,
        "team_label_table": team_table,
        "team_label_ranking": b11.ranking_of(team_table, "mean_advantage")[0],
        "team_label_spread": b11.spread_of(b11.ranking_of(team_table, "mean_advantage")[1]),
        "additive_reference": {
            "segments": 100 * rollouts, "columns": 6, "rank": 6, "clusters": 16 * rollouts,
            "state_control": False,
            "coefficients": {str(label): coefficients[label] for label in range(6)},
            "clustered_se": {str(label): gap_se for label in range(6)},
            "value_coefficient": None, "value_clustered_se": None,
            "ranking": reference_order,
            "best_label": reference_spread["best_label"],
            "worst_label": reference_spread["worst_label"],
            "max_minus_min": reference_spread["max_minus_min"],
            "max_minus_min_clustered_se": gap_se,
            "residual_sd": .1, "r_squared": .3, "definition": "perfect-credit reference"},
        "additive_reference_with_state_control": {
            "coefficients": {str(label): coefficients[label] for label in range(6)},
            "value_coefficient": .8, "state_control": True},
        "label_law": {"agent_label_shares": [1. / 6.] * 6,
                      "agent_label_entropy_estimate": 1.75,
                      "agent_entropy_gap_to_uniform": math.log(6.) - 1.75,
                      "uniform_entropy": math.log(6.)},
        "policy_gradient": {"estimator": "score_function_with_shares_as_q",
                            "entropy_coefficient_lambda_h": .07, "max_minus_min": .01},
        "per_rollout": [], "mean_segment_reward": .2, "mean_segment_elapsed": 10.}


def probe_summary(seed, sha="synthetic-source", **overrides):
    """A published probe summary of this object, in the shape `reduce` reads."""
    measures = overrides.pop("measures", None) or measures_for(seed)
    summary = {
        "object_id": b11.OBJECT_ID, "command": "probe", "status": "complete",
        "block_seed": seed, "evaluation_seed": b11.BLOCKS[seed], "launch_sha": sha,
        "optimizer_steps": 0, "optimizer_calls": {},
        "weights_record": {"sha256": f"sha-{seed}"},
        "faithful_load": {"faithful_load": True, "first_differing_world": None},
        "learner_state": {"before": {"parameter_digest": "d"},
                          "after": {"parameter_digest": "d"}, "unchanged": True},
        "collection_rng": {"restored": True},
        "rollouts": measures["rollouts"], "measures": measures,
        "as_trained_world_scores": [AS_TRAINED] * WORLDS, "J_as_trained": AS_TRAINED,
        "collection_geometry": [{"rows_M": 800, "rows_M_agent": 4800, "rows_M_team": 800}],
        "update_law": {"gamma": .99, "lambda_h": .07, "ppo_epochs": 15},
        "wall_seconds": 700.}
    summary.update(overrides)
    return summary


def supplied(sha="synthetic-source", b09_sha="b09-source", b10_sha="b10-source"):
    probes = [probe_summary(seed, sha) for seed in SEEDS]
    nine = [b09tests.probe_summary(seed, b09_sha) for seed in SEEDS]
    ten = [b10tests.probe_summary(seed, b10_sha) for seed in SEEDS]
    return probes, nine, ten


def test_the_synthetic_inputs_agree_with_b09s_and_b10s_own_probe_shapes():
    """The fixture itself: the three objects' `as_trained` panels must be one panel."""
    probes, nine, ten = supplied()
    for probe, b09_probe, b10_probe in zip(probes, nine, ten):
        scores = probe["as_trained_world_scores"]
        assert scores == b09_probe["rules_measured"]["as_trained"]["J_world_scores"]
        assert scores == b10_probe["rules_measured"]["as_trained"]["J_world_scores"]
        assert (probe["weights_record"]["sha256"] == b09_probe["weights_record"]["sha256"]
                == b10_probe["weights_record"]["sha256"])
    assert b11.b09_probe_row(nine[1])["best_mean_action_label"] == 2  # B09's synthetic map
    assert b11.b09_probe_row(nine[1])["coordinator_most_used_label"] == 2
    assert b11.b10_probe_row(ten[1])["sampled_J_by_label"][2] == pytest.approx(
        b10tests.SAMPLED[772903][2])


def test_reduce_reads_three_probes_beside_b09s_and_b10s():
    probes, nine, ten = supplied()
    result = b11.reduce_inputs(probes, nine, ten)
    assert result["status"] == "complete" and result["object_id"] == b11.OBJECT_ID
    assert result["blocks_read"] == 3 and result["invalid_probes"] == {}
    assert result["invalid_b09_probes"] == {} and result["invalid_b10_probes"] == {}
    assert result["probe_launch_sha"] == "synthetic-source"
    assert result["b09_probe_launch_sha"] == "b09-source"
    assert result["b10_probe_launch_sha"] == "b10-source"
    assert result["reference_object_ids"] == [b10.OBJECT_ID, b09.OBJECT_ID, b08.OBJECT_ID]
    assert "wsl_4070" in result["interpretation_limit"]

    for index, block in enumerate(result["blocks"]):
        seed = SEEDS[index]
        assert block["status"] == "complete" and block["weights_match"] is True
        assert block["as_trained_identical_to_b09_and_b10"] is True
        for label in range(6):
            assert block["agent_label_mean_advantage"][str(label)] == pytest.approx(
                ADVANTAGE[seed][label])
            assert block["additive_coefficients"][str(label)] == pytest.approx(
                COEFFICIENTS[seed][label])
            assert block["mean_action_J_by_label"][str(label)] == pytest.approx(
                b09tests.CONSTANTS[seed][label])
            assert block["sampled_J_by_label"][str(label)] == pytest.approx(
                b10tests.SAMPLED[seed][label])
    # the planted orders: the same as B09's, then label 1 first, then B09's reversed
    by_seed = {block["training_seed"]: block for block in result["blocks"]}
    assert by_seed[772803]["rank_correlation_advantage_vs_mean_action"] == pytest.approx(1.)
    assert by_seed[773003]["rank_correlation_advantage_vs_mean_action"] == pytest.approx(-1.)
    assert by_seed[772903]["agent_label_ranking"][0] == 1
    assert b11.rank_of(by_seed[772903]["agent_label_ranking"], 0) == 6
    assert by_seed[772803]["best_mean_action_label"] == 2
    assert by_seed[772803]["best_mean_action_label_is_first_by_advantage"] is True
    assert by_seed[772903]["best_mean_action_label"] == 2
    assert by_seed[772903]["best_mean_action_label_advantage_rank"] == 2
    assert by_seed[772903]["best_mean_action_label_is_first_by_advantage"] is False
    # the coordinator's most used deployed label is B09's own `as_trained` histogram argmax
    assert by_seed[772803]["coordinator_most_used_label"] == 2
    assert by_seed[772803]["coordinator_most_used_label_advantage_rank"] == 1
    assert by_seed[773003]["coordinator_most_used_label_advantage_rank"] == 5
    # the reference travels beside the signal, always labelled
    assert by_seed[772803]["rank_correlation_additive_vs_mean_action"] == pytest.approx(1.)
    assert by_seed[773003]["additive_max_minus_min"] == pytest.approx(0.)  # a flat table
    assert by_seed[773003]["additive_exceeds_twice_its_clustered_se"] is False
    assert "perfect-credit reference" in by_seed[772803]["additive_reference_note"]
    assert "never reaches the low-level actor" in by_seed[772803]["team_label_placebo_note"]
    # the across-block descriptions use the direction's own helper and wording
    assert result["agent_label_spread"]["available_blocks"] == 3
    assert "working_model" in result["agent_label_spread"]
    assert result["rank_correlation_advantage_vs_mean_action"]["mean"] == pytest.approx(
        (1. + by_seed[772903]["rank_correlation_advantage_vs_mean_action"] - 1.) / 3.)
    assert result["best_label_by_block"]["772903"]["advantage"] == 1
    assert result["ranking_by_block"]["772803"]["mean_action_b09"] == [2, 3, 1, 0, 4, 5]
    assert result["coordinator_most_used_label_rank_by_block"]["772803"]["label"] == 2


def test_the_predictions_are_counted_where_they_are_read():
    probes, nine, ten = supplied()
    predictions = b11.reduce_inputs(probes, nine, ten)["predictions"]
    spread = predictions["E2a_the_advantage_spread_exceeds_twice_its_clustered_standard_error"]
    assert spread["blocks_considered"] == SEEDS and spread["blocks_read"] == 3
    assert spread["blocks_holding"] == 2  # .5/.1 and .5/.05 hold; .5/.3 does not
    assert spread["per_block"]["773003"]["holds"] is False
    absent = predictions["E2b_the_advantage_spread_is_within_twice_its_clustered_standard_error"]
    assert absent["blocks_holding"] == 1 and absent["per_block"]["773003"]["holds"] is True
    clause = predictions["E2a_on_772903_label_1_is_first_and_label_0_is_in_the_bottom_half"]
    assert clause["blocks_considered"] == [772903] and clause["blocks_holding"] == 1
    assert clause["per_block"]["772903"]["value"]["label_1_rank"] == 1
    assert clause["per_block"]["772903"]["value"]["label_0_rank"] == 6
    reference = predictions[
        "REFERENCE_the_additive_coefficient_spread_exceeds_twice_its_clustered_standard_error"]
    assert reference["blocks_holding"] == 2 and "perfect-credit" in reference["statement"]
    assert predictions["REFERENCE_on_772903_label_1_is_first_and_label_0_is_in_the_bottom_half"][
        "blocks_holding"] == 1
    assert "not that signal" in predictions["counting_note"]
    # a block that is not read is counted as not read, and never as holding
    partial = b11.reduce_inputs(probes[:1], nine[:1], ten[:1])
    assert partial["status"] == "incomplete" and partial["blocks_read"] == 1
    rows = partial["predictions"][
        "E2a_the_advantage_spread_exceeds_twice_its_clustered_standard_error"]
    assert rows["blocks_read"] == 1 and rows["per_block"]["772903"]["read"] is False


def test_the_advantage_and_the_reference_can_disagree_without_confusing_the_reading():
    """The two rank correlations are separate columns: one signal, one perfect-credit reference."""
    probes, nine, ten = supplied()
    probes[0] = probe_summary(772803, measures=measures_for(
        772803, coefficients=list(reversed(ADVANTAGE[772803]))))
    block = b11.reduce_inputs(probes, nine, ten)["blocks"][0]
    assert block["rank_correlation_advantage_vs_mean_action"] == pytest.approx(1.)
    assert block["rank_correlation_additive_vs_mean_action"] != pytest.approx(1.)
    assert block["agent_label_ranking"] != block["additive_ranking"]


@pytest.mark.parametrize("damage,message", [
    ({"status": "incomplete"}, "incomplete probe"),
    ({"optimizer_steps": 1}, "optimizer step"),
    ({"faithful_load": {"faithful_load": False}}, "faithful load"),
    ({"learner_state": {"unchanged": False}}, "unchanged parameters"),
    ({"object_id": "SOMETHING_ELSE"}, "not a probe of this object"),
    ({"block_seed": 999}, "not one of this object's three blocks"),
    ({"as_trained_world_scores": []}, "no `as_trained` world scores"),
])
def test_reduce_refuses_a_probe_that_is_not_this_objects_complete_zero_step_one(damage, message):
    with pytest.raises(ValueError, match=message):
        b11.probe_row(probe_summary(772803, **damage))


def test_reduce_refuses_a_probe_without_the_tables_the_reading_needs():
    short = measures_for(772803)
    short["agent_label_table"].pop("5")
    with pytest.raises(ValueError, match="six-label advantage table"):
        b11.probe_row(probe_summary(772803, measures=short))
    missing = measures_for(772803)
    missing["additive_reference"] = None
    with pytest.raises(ValueError, match="perfect-credit reference"):
        b11.probe_row(probe_summary(772803, measures=missing))
    empty = measures_for(772803, rollouts=0)
    with pytest.raises(ValueError, match="no collected rollout"):
        b11.probe_row(probe_summary(772803, measures=empty))


def test_reduce_refuses_mixed_launch_shas_and_duplicate_blocks():
    probes, nine, ten = supplied()
    mixed = [probe_summary(SEEDS[0], "one"), probe_summary(SEEDS[1], "another")]
    with pytest.raises(ValueError, match="mixed launch shas"):
        b11.reduce_inputs(mixed, nine, ten)
    with pytest.raises(ValueError, match="duplicate this object's probe block"):
        b11.reduce_inputs(probes + [probe_summary(SEEDS[0])], nine, ten)
    with pytest.raises(ValueError, match="duplicate B09 probe block"):
        b11.reduce_inputs(probes, nine + [nine[0]], ten)
    with pytest.raises(ValueError, match="duplicate B10 probe block"):
        b11.reduce_inputs(probes, nine, ten + [ten[0]])


def test_reduce_refuses_a_block_whose_checkpoint_or_panel_is_not_b09s_and_b10s():
    probes, nine, ten = supplied()
    probes[0] = probe_summary(SEEDS[0], weights_record={"sha256": "another-checkpoint"})
    probes[1] = probe_summary(SEEDS[1], as_trained_world_scores=[AS_TRAINED + 1.] * WORLDS)
    result = b11.reduce_inputs(probes, nine, ten)
    assert result["status"] == "incomplete" and result["blocks_read"] == 1
    assert "weights" in result["blocks"][0]["missing_or_invalid"]
    assert result["blocks"][0]["weights_match"] is False
    assert "as_trained" in result["blocks"][1]["missing_or_invalid"]
    assert result["blocks"][1]["as_trained_identical_to_b09_and_b10"] is False
    # a missing B10 probe leaves the block unread, with the reason recorded
    without = b11.reduce_inputs(*supplied()[:2], ten[:2])
    assert without["blocks"][2]["missing_or_invalid"]["b10_probe"] == "not supplied"
    assert without["status"] == "incomplete"


def test_reduce_refuses_a_b09_or_b10_probe_its_own_reader_refuses():
    probes, nine, ten = supplied()
    nine[0] = dict(nine[0], status="incomplete")
    ten[1] = dict(ten[1], optimizer_steps=3)
    result = b11.reduce_inputs(probes, nine, ten)
    assert result["blocks_read"] == 1
    assert "incomplete probe" in result["invalid_b09_probes"][str(SEEDS[0])]
    assert "optimizer step" in result["invalid_b10_probes"][str(SEEDS[1])]
