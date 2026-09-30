"""Synthetic checks for the one fixed B02 opportunity; no study worlds."""

import hashlib
import json

import numpy as np
import pytest

from envs.pettingzoo import uav_radio
from experiments.candidates.uav_fleet_transmission.control import predict_next
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.b02 import option


@pytest.fixture
def fixture():
    rng = np.random.RandomState(41)
    positions = rng.uniform(0, 1000, (8, 3))
    positions[:, 2] = rng.uniform(50, 150, 8)
    return positions, rng.uniform(0, 1000, (50, 2))


def direct_score(users, positions, mask):
    loss = uav_radio.free_space_user_path_loss(positions, users)
    sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=mask_bits(mask, 8))
    connections = uav_radio.greedy_connection_assignment(sinr, 0, 10)
    result = uav_radio.service_metrics(sinr, connections, 0)
    height = (positions[:, 2].mean() - 50) / 100 * .1
    return dict(J=float(result["J"] - height), served=int(result["served"]),
                quality=float(result["quality"]), energy_penalty=float(height))


def test_sites_anchor_distance_row_ties_and_projection():
    users = np.zeros((50, 2))
    users[49] = [100, 200]
    sites = option._sites(users)
    np.testing.assert_array_equal(sites[:50], users)
    np.testing.assert_array_equal(sites[99], [10, 20])
    users = np.asarray([[i % 5 * 100., i // 5 * 100.] for i in range(50)])
    for anchor, centroid in enumerate(option._sites(users)[50:]):
        neighbors = sorted((i for i in range(50) if i != anchor),
                           key=lambda i: (sum((users[i] - users[anchor]) ** 2), i))[:9]
        np.testing.assert_array_equal(centroid, users[[anchor, *neighbors]].mean(axis=0))
    assert option._project(500., 515.) == 0  # equal distance: smaller coordinate
    assert option._project(500., 485.) == -1
    assert option._project(0., 0.) == 0  # duplicate clipped coordinates: |k|
    assert option._project(.1, 0.) == -1
    assert option._project(1000., 1000.) == 0
    assert option._project(0., 1000.) == 34


@pytest.mark.parametrize("target", [[0., 1000.], [500., 500.], [993., 23.]])
def test_transit_matches_direct_radio_and_native_clipped_motion(fixture, target):
    positions, users = fixture
    positions[7] = [0., 0., 149.999]
    oldmask = 127
    stay = direct_score(users, positions, oldmask)
    transit = option._transit(positions, 7, np.asarray(target), stay)
    assert transit["duration"] in (10, 20, 30, 40)
    assert transit["commands"].dtype == np.float32
    assert not transit["commands"][:, :7].any()
    assert set(np.unique(transit["commands"])) <= {-1., 0., 1.}
    predicted = positions.copy()
    total_J, total_served, path = 0., 0, 0.
    for commands in transit["commands"]:
        moved = predicted.copy()
        for member in range(8):
            moved[member] += commands[member] * 30 * 1.0
            moved[member] = np.clip(moved[member], [0, 0, 50], [1000, 1000, 150])
        score = direct_score(users, moved, oldmask)
        assert score["served"] == stay["served"]
        assert score["quality"] == stay["quality"]
        total_J += score["J"]
        total_served += score["served"]
        path += float(np.linalg.norm(moved - predicted, axis=1).sum())
        predicted = moved
    np.testing.assert_array_equal(transit["destination"], predicted)
    assert transit["transit_J"] == total_J
    assert transit["transit_served"] == total_served
    assert transit["path"] == path
    assert predicted[7, 2] == 50
    if transit["unrounded_duration"] < transit["duration"]:
        assert not transit["commands"][transit["unrounded_duration"]:].any()


def test_zero_distance_has_ten_tick_positive_commitment(fixture):
    positions, users = fixture
    positions[:, 2] = 50
    stay = direct_score(users, positions, 127)
    transit = option._transit(positions, 7, positions[7, :2], stay)
    assert transit["unrounded_duration"] == 0 and transit["duration"] == 10
    assert not transit["commands"].any()
    assert transit["path"] == 0


def test_arrival_all_required_masks_native_scores_and_ordered_digest(fixture):
    positions, users = fixture
    member = 5
    mask, trace = option.arrival_mask(users, positions, member)
    masks = [m for m in range(1, 256) if m & (1 << member)]
    scores = [direct_score(users, positions, m) for m in masks]
    expected = max(range(128), key=lambda i: (scores[i]["J"], scores[i]["served"], -masks[i]))
    assert mask == masks[expected]
    assert trace["selected_score"] == scores[expected]
    readings = [[m, s["J"], s["served"], s["quality"], s["energy_penalty"]]
                for m, s in zip(masks, scores)]
    assert trace["candidate_digest"] == hashlib.sha256(np.asarray(readings, dtype="<f8").tobytes()).hexdigest()
    assert trace["counts"]["requested_candidates"] == 128
    assert trace["counts"]["scored_candidates"] == 128
    json.dumps(trace, allow_nan=False)


class ZeroScores:
    def __init__(self, users):
        self.counts = dict(requested_candidates=0, scored_candidates=0, cached_candidates=0,
                           geometry_rows_computed=0, geometry_rows_reused=0)

    def score(self, positions, masks):
        self.counts["requested_candidates"] += len(masks)
        self.counts["scored_candidates"] += len(masks)
        return [dict(J=0., served=0, quality=0., energy_penalty=0.) for _ in masks]


def test_arrival_exact_ties_then_smaller_mask(monkeypatch, fixture):
    monkeypatch.setattr(option, "_Scores", ZeroScores)
    positions, users = fixture
    assert option.arrival_mask(users, positions, 3)[0] == 8
    class ServedScores(ZeroScores):
        def score(self, positions, masks):
            scores = super().score(positions, masks)
            for mask, score in zip(masks, scores):
                score["served"] = int(mask >= 16)
            return scores
    monkeypatch.setattr(option, "_Scores", ServedScores)
    assert option.arrival_mask(users, positions, 3)[0] == 24


def test_no_quiet_members_stay_only_and_validation(fixture):
    positions, users = fixture
    plan = option.plan_option(positions, users, np.int64(255), t=np.int64(40), horizon=np.int64(500))
    json.dumps(plan, allow_nan=False)
    assert not plan["initiated"] and plan["selected"] is None
    assert plan["member"] is plan["site"] is plan["arrival_t"] is plan["predicted_mask"] is None
    assert plan["commands"] == [] and plan["duration"] == 0
    assert plan["candidate_count"] == plan["counts"]["model_ticks"] == 0
    assert plan["counts"]["requested_candidates"] == 1
    assert plan["stay_total_J"] == 460 * direct_score(users, positions, 255)["J"]
    assert plan["candidate_digest"] == hashlib.sha256(b"").hexdigest()
    for kwargs in (dict(t=30), dict(horizon=510), dict(t=True)):
        with pytest.raises(ValueError):
            option.plan_option(positions, users, 255, **kwargs)
    for badmask in (0, 256, True):
        with pytest.raises((TypeError, ValueError)):
            option.plan_option(positions, users, badmask)
    with pytest.raises(ValueError):
        option.plan_option(positions[:4], users, 15)
    with pytest.raises(ValueError):
        option.arrival_mask(users, positions, 8)
    invalid = positions.copy()
    invalid[0, 2] = np.nan
    with pytest.raises(ValueError):
        option.plan_option(invalid, users, 127)


def test_duplicate_sites_keep_requests_but_cache_scores_and_geometry():
    positions = np.tile([0., 0., 50.], (8, 1))
    users = np.zeros((50, 2))
    plan = option.plan_option(positions, users, 127)
    assert plan["candidate_count"] == 100
    counts = plan["counts"]
    assert counts["requested_candidates"] == 12801
    assert counts["scored_candidates"] == 129
    assert counts["cached_candidates"] == 12672
    assert counts["geometry_rows_computed"] == 1
    assert counts["model_ticks"] == 1000
    json.dumps(plan, allow_nan=False)


def test_candidate_digest_all_rows_order_ties_and_strict_no_initiation(monkeypatch):
    monkeypatch.setattr(option, "_Scores", ZeroScores)
    positions = np.tile([500., 500., 50.], (8, 1))
    users = np.asarray([[i % 5 * 200., i // 5 * 100.] for i in range(50)])
    plan = option.plan_option(positions, users, 63)  # silent rows six, seven
    assert not plan["initiated"]
    assert plan["selected"]["member"] == 6
    assert plan["predicted_total_J"] == plan["stay_total_J"] == 0
    # Independent centroid, projection, command and digest reconstruction.
    centroids = []
    for anchor in range(50):
        neighbors = sorted((i for i in range(50) if i != anchor),
                           key=lambda i: (sum((users[i] - users[anchor]) ** 2), i))[:9]
        centroids.append(users[[anchor, *neighbors]].mean(axis=0))
    digest = hashlib.sha256()
    total_ticks = 0
    best_rank, best_choice = None, None
    for member in (6, 7):
        for site_index, site in enumerate(np.r_[users, centroids]):
            offsets = [min(range(-34, 35), key=lambda k: (
                abs(min(1000, max(0, positions[member, axis]+30*k))-site[axis]),
                min(1000, max(0, positions[member, axis]+30*k)), abs(k), k)) for axis in range(2)]
            steps = max(abs(k) for k in offsets)
            duration = 10 * max(1, (steps + 9) // 10)
            dest = positions.copy()
            path = 0.
            for tick in range(duration):
                nextpos = dest.copy()
                for axis, k in enumerate(offsets):
                    if tick < abs(k):
                        nextpos[member, axis] = min(1000, max(0, dest[member, axis]+30*np.sign(k)))
                path += float(np.linalg.norm(nextpos - dest, axis=1).sum())
                dest = nextpos
            row = [member, site_index, *offsets, 0, duration, 1 << member,
                   0., 0, path, 0., 0, 0., 0, 0., 0., *dest.reshape(-1)]
            digest.update(np.asarray(row, dtype="<f8").tobytes())
            total_ticks += duration
            rank = (-path, -duration, -member, -site_index)
            if best_rank is None or rank > best_rank:
                best_rank, best_choice = rank, (member, site_index)
    assert plan["candidate_digest"] == digest.hexdigest()
    assert (plan["selected"]["member"], plan["selected"]["site"]) == best_choice
    assert plan["counts"]["model_ticks"] == total_ticks
    assert plan["counts"]["requested_candidates"] == 1 + 200 * 128
    json.dumps(plan, allow_nan=False)


def test_service_gain_alone_does_not_initiate(monkeypatch):
    class ServiceOnlyScores(ZeroScores):
        def score(self, positions, masks):
            scores = super().score(positions, masks)
            for mask, score in zip(masks, scores):
                score["served"] = int(bool(mask & 128))
            return scores
    # Artificial exact J tie isolates the initiation rule from ranking rules.
    monkeypatch.setattr(option, "_Scores", ServiceOnlyScores)
    positions = np.tile([0., 0., 50.], (8, 1))
    plan = option.plan_option(positions, np.zeros((50, 2)), 127)
    assert plan["selected"]["predicted_total_J"] == plan["stay_total_J"] == 0
    assert plan["selected"]["predicted_total_served"] > plan["stay_total_served"]
    assert not plan["initiated"] and not plan["commands"]


def test_initiated_plan_tail_arithmetic_replay_and_purity(fixture):
    positions, users = fixture
    # Seven active vehicles far from a compact user cluster, a quiet member
    # at the cluster. This is constructed correctness coverage, not a panel.
    positions[:7] = [1000., 1000., 100.]
    positions[7] = [0., 0., 150.]
    users[:] = [0., 0.]
    before_positions, before_users = positions.copy(), users.copy()
    before_rng = np.random.get_state()
    plan = option.plan_option(positions, users, 127)
    assert plan["initiated"] and plan["member"] == 7
    assert plan["duration"] == 10 and plan["arrival_t"] == 50
    assert plan["site"] == 0  # every site identical; lower index wins
    assert plan["predicted_total_J"] > plan["stay_total_J"]
    predicted = positions.copy()
    transit_J, transit_served = 0., 0
    for commands in np.asarray(plan["commands"], dtype=np.float32):
        predicted = predict_next(predicted, commands)
        score = direct_score(users, predicted, 127)
        transit_J += score["J"]
        transit_served += score["served"]
    np.testing.assert_array_equal(predicted, plan["predicted_destination"])
    tail = direct_score(users, predicted, plan["predicted_mask"])
    assert plan["predicted_total_J"] == transit_J + (460-plan["duration"]) * tail["J"]
    assert plan["predicted_total_served"] == transit_served + (460-plan["duration"]) * tail["served"]
    assert plan["selected"]["tail_score"] == tail
    assert option.plan_option(positions, users, 127) == plan
    np.testing.assert_array_equal(positions, before_positions)
    np.testing.assert_array_equal(users, before_users)
    after_rng = np.random.get_state()
    assert before_rng[0] == after_rng[0] and before_rng[2:] == after_rng[2:]
    np.testing.assert_array_equal(before_rng[1], after_rng[1])
    json.dumps(plan, allow_nan=False)
