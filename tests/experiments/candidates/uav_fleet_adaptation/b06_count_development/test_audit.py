"""Artificial saved arrays only: no native/helper/controller/actor construction."""
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_fleet_adaptation.b06_count_development.audit import check_episode
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b06_count_development.reading import episode_metrics
from experiments.candidates.uav_local_history.b01.controller import COMMANDS, WAYPOINTS


def protocol(horizon=8):
    p = SimpleNamespace(horizon=horizon, fixture_horizon=8, period=4, fixture_world=190,
                        layout_root=101, evaluation_roots=(102, 103), evaluation_worlds=(150,))
    p.phase_worlds = lambda lineage, phase: (110 + lineage * 10 + phase * 2, 111 + lineage * 10 + phase * 2)
    p.acquisition_count = lambda arm, index: 5 if arm == "F" else (3 if index == 0 else 7)
    return p


def assignment(values):
    out = np.zeros(values.shape, dtype=bool)
    for index in np.argsort(-values.flatten(), kind="stable"):
        i, j = divmod(int(index), 50)
        if values[i, j] >= 3 and out[i].sum() < 10 and not out[:, j].any():
            out[i, j] = True
    return out


def observation(positions, users, sinr, peer, tick, horizon):
    n = len(positions)
    out = np.zeros((n, 104), dtype=np.float64)
    out[:, :2] = positions[:, :2] / 1000
    out[:, 2] = (positions[:, 2] - 50) / 100
    out[:, -1] = tick / horizon
    for i in range(n):
        js = np.flatnonzero(sinr[i] >= 3)
        js = js[np.argsort(-sinr[i, js], kind="stable")][:20]
        out[i, 3:3 + 3 * len(js)].reshape(-1, 3)[:] = np.c_[
            (users[js] - positions[i, :2]) / 1000, np.clip((sinr[i, js] + 10) / 50, 0, 1)]
        js = np.flatnonzero((peer[i] >= 3) & (np.arange(n) != i))
        js = js[np.argsort(-peer[i, js], kind="stable")]
        out[i, 63:63 + 4 * len(js)].reshape(-1, 4)[:] = np.c_[
            (positions[js] - positions[i]) / [1000, 1000, 100], np.clip((peer[i, js] + 10) / 50, 0, 1)]
    return out.astype(np.float32)


def counts(kind, misses, requests, users, peers, stochastic=False, ordinary=False):
    c = dict(requests=requests, hits=requests - misses, misses=misses, cache_entries=misses,
             cache_key_bytes=414 * misses, cache_array_bytes=misses * {"C": 900, "student": 564, "feature": 456}[kind],
             helper_calls=0 if kind == "C" else misses,
             helper_setup_links=0 if kind == "C" else (1 + peers) * users * misses,
             helper_extreme_links=0 if kind == "C" else 2 * users * misses)
    if kind == "C":
        c.update(trajectories=27 * misses, model_ticks=108 * misses,
                 candidate_links=108 * users * misses, setup_links=(1 + peers) * users * misses,
                 objective_reductions=108 * misses)
    if kind == "student":
        c["neural_rows"] = misses
    if kind == "student" or ordinary:
        c["sampled_draws"] = requests if stochastic else 0
    return c


def fixture(*, n=5, kind="fixture", arm="C", phase=None, horizon=8, fallback=False, tape=0, logit_row=None):
    p = protocol(horizon)
    neural = (kind == "acquisition" and phase != 0) or kind == "evaluation" and arm not in ("C", "Q")
    training = kind == "acquisition"
    lineage = 0 if training or neural else None
    world = (p.phase_worlds(lineage, phase)[0 if n != 7 else 1] if training
             else p.fixture_world if kind == "fixture" else p.evaluation_worlds[0])
    stochastic = kind == "evaluation" and arm != "C"
    tape = tape if stochastic else None
    root = p.evaluation_roots[tape] if stochastic else None
    temperature = (2. if arm == "Bstar" else 1.) if neural else None
    h = p.fixture_horizon if kind == "fixture" else p.horizon
    d = h // 4
    users = np.random.default_rng(np.random.SeedSequence([p.layout_root, world, 1])).uniform(0, 1000, (50, 2))
    seven = np.random.default_rng(np.random.SeedSequence([p.layout_root, world, 2])).uniform(
        [0, 0, 50], [1000, 1000, 150], (7, 3))
    sinr = np.full((n, 50), -20., dtype=np.float64)
    if not fallback:
        sinr[:, :25] = np.r_[np.full(12, 35.), np.arange(13, 0, -1) + 3.]
    peer = np.full((n, n), 15., dtype=np.float64)
    np.fill_diagonal(peer, -np.inf)
    conn = assignment(sinr)
    service = int(conn.sum())
    quality = float(np.clip((sinr[conn] - 3) / 30, 0, 1).sum() / max(service, 1))
    raw = dict(initial_users=users, initial_seven_uavs=seven, initial_sinr=sinr.copy(),
               initial_peer_sinr=peer.copy(), initial_connections=conn.copy(),
               sinr=np.broadcast_to(sinr, (h, n, 50)).copy(),
               peer_sinr=np.broadcast_to(peer, (h, n, n)).copy(),
               connections=np.broadcast_to(conn, (h, n, 50)).copy(),
               reward=np.full(h, .7 * service / 50 + .3 * quality), served=np.full(h, service, dtype=np.int64),
               sinr_quality=np.full(h, quality), transmitter_mask=np.ones((h, n), dtype=bool),
               terminated=np.arange(1, h + 1) == p.horizon, truncated=np.zeros(h, dtype=bool),
               decision_ticks=np.arange(0, h, 4, dtype=np.int64), positions=np.empty((h + 1, n, 3)),
               observations=np.empty((h, n, 104), dtype=np.float32), commands=np.empty((h, n, 3), dtype=np.float32),
               nav_pre=np.empty((d, n), dtype=np.int64), nav_next=np.empty((d, n), dtype=np.int64),
               fallback=np.full((d, n), fallback), action_index=np.empty((d, n), dtype=np.int64),
               memo_hit=np.empty((d, n), dtype=bool), features=np.empty((d, n, 114), dtype=np.float32),
               n_current=np.full((d, n), 0 if fallback else 20, dtype=np.int64),
               n_peers=np.full((d, n), n - 1, dtype=np.int64))
    if neural:
        logits = np.full((d, n, 27), -1000., dtype=np.float32)
        logits[:, :, 0] = 1000.
        if logit_row is not None:
            logits[:] = logit_row
        raw.update(logits=logits, probabilities=np.empty((d, n, 27)), innovation=np.empty((d, n)), entropy=np.zeros((d, n)))
    if training:
        raw.update(expert_action_index=np.empty((d, n), dtype=np.int64), expert_fallback=np.full((d, n), fallback),
                   expert_nav_next=np.empty((d, n), dtype=np.int64), expert_memo_hit=np.empty((d, n), dtype=bool),
                   expert_scores=np.zeros((d, n, 27)), expert_served=np.zeros((d, n, 27)))
    elif not neural:
        raw.update(policy_scores=np.zeros((d, n, 27)), policy_served=np.zeros((d, n, 27)),
                   mode_index=np.empty((d, n), dtype=np.int64), probabilities=np.empty((d, n, 27)), innovation=np.empty((d, n)))
    raw["positions"][0] = seven[:n]
    navs, keys, misses = [], [set() for _ in range(n)], 0
    for i in range(n):
        own = observation(seven[:n], users, sinr, peer, 0, p.horizon)[i, :3].astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
        navs.append(int(np.argmin(((WAYPOINTS - own[:2]) ** 2).sum(1))))
    for t in range(h):
        obs = observation(raw["positions"][t], users, sinr, peer, t, p.horizon)
        raw["observations"][t] = obs
        if t % 4 == 0:
            di = t // 4
            raw["nav_pre"][di] = navs
            for i in range(n):
                own = obs[i, :3].astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
                nav = navs[i]
                key = bytes([n, nav]) + obs[i, :103].tobytes()
                hit = key in keys[i]
                misses += int(not hit)
                keys[i].add(key)
                raw["memo_hit"][di, i] = hit
                raw["features"][di, i] = np.concatenate([obs[i, :103], np.eye(10)[nav], [fallback]])
                navs[i] = (nav + 1) % 10 if fallback and np.linalg.norm(WAYPOINTS[nav] - own[:2]) <= 60 else nav
                mode = 0
                if fallback:
                    ends = np.tile(own, (27, 1))
                    for _ in range(4):
                        ends = np.minimum(np.maximum(ends + COMMANDS * 30, [0, 0, 50]), [1000, 1000, 150])
                    mode = int(np.argmin(((ends - np.r_[WAYPOINTS[navs[i]], 50]) ** 2).sum(1)))
                if training or not neural:
                    prefix = "expert_" if training else "policy_"
                    if not fallback:
                        raw[prefix + "scores"][di, i] = .014
                        raw[prefix + "scores"][di, i, 0] = .02
                        raw[prefix + "served"][di, i] = 1
                    if training:
                        raw["expert_action_index"][di, i] = mode
                        raw["expert_nav_next"][di, i] = navs[i]
                        raw["expert_memo_hit"][di, i] = hit
                    else:
                        raw["mode_index"][di, i] = mode
                if neural or not training:
                    if neural:
                        z = raw["logits"][di, i].astype(np.float64) / temperature
                        probs = np.exp(z - max(z)); probs /= sum(probs)
                        positive = probs > 0
                        raw["entropy"][di, i] = -sum(probs[positive] * np.log(probs[positive]))
                    else:
                        probs = np.full(27, .1 / 26) if stochastic else np.zeros(27)
                        probs[mode] = .9 if stochastic else 1
                    uniform = (np.random.default_rng(np.random.SeedSequence([root, world, t, i])).random()
                               if stochastic else -1.)
                    raw["probabilities"][di, i] = probs
                    raw["innovation"][di, i] = uniform
                    cdf = np.cumsum(probs); cdf[-1] = 1
                    action = int(np.searchsorted(cdf, uniform, side="right")) if stochastic else (int(np.argmax(z)) if neural else mode)
                else:
                    action = mode
                raw["action_index"][di, i] = action
            raw["nav_next"][di] = navs
        raw["commands"][t] = COMMANDS[raw["action_index"][t // 4]]
        raw["positions"][t + 1] = np.clip(raw["positions"][t] + raw["commands"][t] * 30,
                                             [0, 0, 50], [1000, 1000, 150])
    raw["terminal_observation"] = observation(raw["positions"][-1], users, sinr, peer, h, p.horizon)
    requests = d * n
    u, peers = (0 if fallback else 20), n - 1
    row = dict(id=f"{kind}_L{lineage}_{arm}_N{n}_w{world}_p{phase}_t{tape}", kind=kind, arm=arm,
               lineage=lineage, phase=phase, world=world, n=n, neural=neural, tape=tape, sampling_root=root,
               temperature=temperature, initial_state_sha256=array_digest(seven[:n], users),
               shared_layout_sha256=array_digest(users, seven),
               policy_counts=counts("student" if neural else "C", misses, requests, u, peers,
                                    stochastic, ordinary=not training),
               expert_counts=counts("C", misses, requests, u, peers) if training else {},
               feature_counts=counts("feature", misses, requests, u, peers) if kind == "fixture" or training and phase == 0 else {},
               label_data_sha256=(array_digest(raw["features"].reshape(-1, 114), raw["expert_action_index"].flatten(),
                                               np.full(requests, n, dtype=np.int64)) if training else None),
               **episode_metrics(raw))
    return raw, row, p


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7])
def test_all_counts_and_partial_terminal(n):
    raw, row, p = fixture(n=n, horizon=256)
    result = check_episode(raw, row, p)
    assert result["saved_native_steps"] == 8
    assert result["saved_agent_ticks"] == 8 * n
    assert result["decision_rows"] == 2 * n
    assert result["observation_rows"] == 9 * n
    assert result["metrics"]["policy_cache_hits"] == n
    assert not raw["terminated"].any()
    assert raw["terminal_observation"][0, -1] == np.float32(8 / 256)
    assert raw["served"][0] == 25
    assert np.max(raw["connections"].sum(-1)) == 10
    assert result["metrics"]["visible_peer_counts"][n - 1] == 2 * n


@pytest.mark.parametrize("kind,arm,phase,n", [
    ("acquisition", "F", 0, 5), ("acquisition", "F", 1, 5), ("acquisition", "M", 2, 7),
    ("evaluation", "C", None, 4), ("evaluation", "Q", None, 6),
    ("evaluation", "P", None, 5), ("evaluation", "M", None, 6), ("evaluation", "Bstar", None, 4),
])
def test_policy_branches(kind, arm, phase, n):
    raw, row, p = fixture(kind=kind, arm=arm, phase=phase, n=n)
    result = check_episode(raw, row, p)
    assert result["metrics"] == episode_metrics(raw)
    assert raw["terminated"][-1]
    if row["sampling_root"] is not None:
        assert result["policy_counts"]["sampled_draws"] == 2 * n


def test_full_clock_and_underflow_density():
    raw, row, p = fixture(kind="evaluation", arm="Bstar", n=6, horizon=256)
    result = check_episode(raw, row, p)
    assert result["saved_native_steps"] == 256
    assert raw["probabilities"][..., 0].min() == 1
    assert np.count_nonzero(raw["probabilities"][..., 1:]) == 0
    assert result["policy_counts"]["neural_rows"] == 6
    assert raw["terminal_observation"][0, -1] == 1


def test_supplied_fallback_sweep_and_zero_service():
    raw, row, p = fixture(n=7, fallback=True)
    result = check_episode(raw, row, p)
    assert result["fallback_geometric_rankings"] == 14
    assert result["metrics"]["longest_zero_service_streak"] == 8
    assert result["metrics"]["zero_service_ticks"] == list(range(8))
    assert result["policy_counts"]["candidate_links"] == 0


@pytest.mark.parametrize("field,index,value", [
    ("observations", (0, 0, 3), .2), ("observations", (1, 0, 103), .9),
    ("terminal_observation", (0, 64), .4), ("positions", (3, 0, 0), 1.),
    ("initial_users", (0, 0), 1.), ("initial_seven_uavs", (6, 0), 1.),
    ("initial_connections", (0, 0), False), ("connections", (0, 0, 0), False),
    ("reward", (0,), .99), ("sinr_quality", (0,), .99), ("served", (0,), 0),
    ("commands", (1, 0, 0), 1.), ("terminated", (0,), True), ("truncated", (0,), True),
    ("transmitter_mask", (0, 0), False), ("decision_ticks", (1,), 3),
    ("features", (0, 0, 103), .4), ("features", (0, 0, 113), 1.),
    ("nav_pre", (0, 0), 10), ("nav_next", (0, 0), 10),
    ("n_current", (0, 0), 19), ("n_peers", (0, 0), 0),
    ("memo_hit", (0, 0), True), ("memo_hit", (1, 0), False),
    ("mode_index", (0, 0), 26), ("policy_scores", (1, 0, 1), .03),
    ("policy_served", (0, 0, 0), 1.1), ("probabilities", (0, 0, 0), .9),
    ("innovation", (0, 0), .5), ("action_index", (0, 0), 27),
])
def test_saved_field_drift(field, index, value):
    raw, row, p = fixture()
    raw[field][index] = value
    with pytest.raises(ValueError):
        check_episode(raw, row, p)


@pytest.mark.parametrize("field", ["probabilities", "entropy", "innovation", "logits"])
def test_neural_saved_density_and_cache_drift(field):
    raw, row, p = fixture(kind="evaluation", arm="P")
    raw[field].flat[-1] += .125
    with pytest.raises(ValueError):
        check_episode(raw, row, p)


@pytest.mark.parametrize("field", ["expert_action_index", "expert_fallback", "expert_nav_next", "expert_memo_hit", "expert_scores"])
def test_teacher_drift(field):
    raw, row, p = fixture(kind="acquisition", arm="F", phase=1)
    if raw[field].dtype == bool:
        raw[field].flat[-1] = not raw[field].flat[-1]
    else:
        raw[field].flat[-1] += 1
    with pytest.raises(ValueError):
        check_episode(raw, row, p)


def test_fallback_label_drift():
    raw, row, p = fixture(kind="acquisition", arm="M", phase=0, n=3, fallback=True)
    raw["expert_action_index"][0, 0] = (raw["expert_action_index"][0, 0] + 1) % 27
    with pytest.raises(ValueError, match="ranking/label"):
        check_episode(raw, row, p)


@pytest.mark.parametrize("change", ["extra", "dtype", "nan", "offdiag_inf", "positive_diag_inf", "counter", "metric", "digest", "tape", "count"])
def test_contract_drift(change):
    raw, row, p = fixture(kind="evaluation", arm="Q")
    if change == "extra": raw["extra"] = np.zeros(1)
    elif change == "dtype": raw["features"] = raw["features"].astype(np.float64)
    elif change == "nan": raw["sinr"][0, 0, 0] = np.nan
    elif change == "offdiag_inf": raw["peer_sinr"][0, 0, 1] = -np.inf
    elif change == "positive_diag_inf": raw["peer_sinr"][0, 0, 0] = np.inf
    elif change == "counter": row["policy_counts"]["sampled_draws"] -= 1
    elif change == "metric": row["mean_served"] += 1
    elif change == "digest": row["shared_layout_sha256"] = "0" * 64
    elif change == "tape": row["sampling_root"] = p.evaluation_roots[1]
    else: row["n"] = True
    with pytest.raises(ValueError):
        check_episode(raw, row, p)


def test_private_tapes_use_identical_addresses_across_n():
    raw4, row4, p = fixture(kind="evaluation", arm="P", n=4, tape=1)
    raw6, row6, _ = fixture(kind="evaluation", arm="P", n=6, tape=1)
    np.testing.assert_array_equal(raw4["innovation"], raw6["innovation"][:, :4])
    np.testing.assert_array_equal(raw4["positions"][0], raw6["positions"][0, :4])
    check_episode(raw4, row4, p)
    check_episode(raw6, row6, p)


def test_finite_peer_diagonal_is_ignored_by_observation():
    raw, row, p = fixture()
    for matrix in (raw["initial_peer_sinr"], *raw["peer_sinr"]):
        np.fill_diagonal(matrix, 99.)
    check_episode(raw, row, p)


def test_label_digest_includes_public_count():
    raw, row, p = fixture(kind="acquisition", arm="F", phase=0)
    row["label_data_sha256"] = array_digest(raw["features"].reshape(-1, 114), raw["expert_action_index"].flatten(),
                                          np.full(10, 3, dtype=np.int64))
    with pytest.raises(ValueError, match="label/count"):
        check_episode(raw, row, p)


@pytest.mark.parametrize("arm", ["P", "Bstar"])
def test_nontrivial_fp64_density_and_temperature(arm):
    logits = np.linspace(-8, 6, 27, dtype=np.float32)
    raw, row, p = fixture(kind="evaluation", arm=arm, logit_row=logits)
    result = check_episode(raw, row, p)
    expected = np.exp(logits.astype(np.float64) / row["temperature"] - float(logits[-1]) / row["temperature"])
    expected /= expected.sum()
    np.testing.assert_array_equal(raw["probabilities"][0, 0], expected)
    assert result["metrics"]["mean_entropy"] > 0
    raw["probabilities"][0, 0] = np.full(27, 1 / 27)
    with pytest.raises(ValueError, match="probabilities"):
        check_episode(raw, row, p)


def test_greedy_acquisition_is_separate_from_teacher_label():
    raw, row, p = fixture(kind="acquisition", arm="F", phase=1,
                          logit_row=np.arange(27, dtype=np.float32))
    assert np.all(raw["action_index"] == 26)
    assert np.all(raw["expert_action_index"] == 0)
    check_episode(raw, row, p)
    raw["action_index"][0, 0] = 0
    with pytest.raises(ValueError):
        check_episode(raw, row, p)


def test_audit_does_not_invoke_source_numerical_methods(monkeypatch):
    from experiments.candidates.uav_local_history.b01 import controller
    raw, row, p = fixture(fallback=True)
    def forbidden(*args, **kwargs):
        raise AssertionError("audit made a numerical controller query")
    monkeypatch.setattr(controller, "_parse", forbidden)
    monkeypatch.setattr(controller, "_power", forbidden)
    for name in ("__init__", "_score", "_trajectories"):
        monkeypatch.setattr(controller.LocalController, name, forbidden)
    check_episode(raw, row, p)


def test_negative_probability_is_invalid_even_inside_precision_tolerance():
    raw, row, p = fixture(kind="evaluation", arm="P")
    raw["probabilities"][0, 0, 1] = -1e-16
    with pytest.raises(ValueError, match="probability range"):
        check_episode(raw, row, p)
