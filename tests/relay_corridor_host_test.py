"""ADR 02 tests-as-specs 1-9 for the relay corridor host family.

Run (root ``CLAUDE.md`` sections Environment and Commands/Tests)::

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
        tests/relay_corridor_host_test.py \
        --basetemp <worktree>/temp/pytest_relay_corridor

Each test below is one row of ADR 02's "Tests-as-specs" paragraph, in order.
The margin table, the renewal variances and the ``C(k, lambda)`` values are
*expected* values here: every number the tests compare against them is computed
by enumeration or by the closed forms written out inside this file, never copied
from the host.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from envs.relay_corridor import (  # noqa: E402
    FixedKOracle,
    GreedyOnPublicState,
    HorizonValidationError,
    OpenLoopPlan,
    PROPOSAL_GRID,
    RelayCorridorAdapter,
    RelayCorridorConfig,
    RelayCorridorHost,
    SwitchingOracle,
    dp_service_profile,
    enumerate_references,
    make_renewal_law,
    proposal_config,
    rows_per_rollout,
    rollout_reference,
    validate_horizon,
)

#: Repository ``C(k, lambda)`` table, ``docs/Claude_docs/toy_studies/untied_k_n/RESULTS.md``.
C_TABLE = {(20, 0.005): 0.9539, (20, 0.02): 0.8310}

#: Mechanics page "Proposed grids": E4 at ``E[D] = 20``.
E4_MEAN = 20.0
E4_VARIANCES = {"deterministic": 0.0, "geometric": 380.0, "lognormal": 687.309}

#: ADR 02 "Resolution arithmetic".
EVAL_EPISODES = 4096


# ----------------------------------------------------------------------
# closed forms, written out here so the test does not trust the package
# ----------------------------------------------------------------------
def _c(k: int, lam: float) -> float:
    """``C(k, lambda) = (1 - (1 - lambda)^k) / (k * lambda)``."""
    if lam == 0.0:
        return 1.0
    return (1.0 - (1.0 - lam) ** k) / (k * lam)


def _j_switch(delta: float, lams, weights, horizon: int) -> float:
    """``J_sw = Delta * sum_r w_r * (1 + (H - 1)(1 - lambda_r)) / H``."""
    return delta * sum(
        w * (1.0 + (horizon - 1) * (1.0 - lam)) / horizon for w, lam in zip(weights, lams)
    )


def _j_fixed(delta: float, lams, weights, horizon: int, k: int) -> float:
    """``J_k = Delta * sum_r w_r * [C(k, lambda_r) - 1/k + 1/H]``."""
    return delta * sum(
        w * (_c(k, lam) - 1.0 / k + 1.0 / horizon) for w, lam in zip(weights, lams)
    )


def _record(tmp_path: Path, name: str, payload: dict) -> None:
    """Write one machine-generated metrics record under the isolated basetemp."""
    (tmp_path / f"{name}.json").write_text(json.dumps(payload, indent=2, default=str))


# ======================================================================
# Test 1 - distinct fixed-N family instances, ragged records without padding
# ======================================================================
def test_1_family_instances_emit_ragged_unpadded_records() -> None:
    """Invariant 1.

    Raggedness is a *family* boundary property.  ``rho = 0`` keeps cardinality
    fixed inside one object, so this asserts that distinct fixed-``N`` instances
    each emit exactly their own live cardinality with no padding row, no padding
    column and no sentinel; it does not require variable ``N`` inside one object
    (review §V.1).
    """
    seen_lengths = set()
    for n_agents in (3, 5, 6, 9):
        config = RelayCorridorConfig(n_agents=n_agents, horizon=40, d0_k_set=(1, 2, 4))
        host = RelayCorridorHost(config, batch_size=2, master_seed=1, episode_ids=[4, 9])
        records = host.public_state_records(lane=0)

        assert host.record_padding is False
        assert len(records["agents"]) == n_agents
        assert len(records["regions"]) == config.n_regions
        assert len(records["zones"]) == config.n_zones
        assert [r["agent_id"] for r in records["agents"]] == list(range(n_agents))

        # No padding row is disguised as a live one, and no sentinel appears.
        for record in records["agents"]:
            assert 0 <= record["region_id"] < config.n_regions
            assert 0 <= record["zone_id"] < config.n_zones
            assert 0 <= record["held_role"] < config.n_roles
            assert record["segment_age"] >= 0
            assert isinstance(record["lease_fresh"], bool)
        for record in records["regions"]:
            assert not np.isnan(record["probe_theta"]).any()
        seen_lengths.add(len(records["agents"]))

        # The observation boundary is the same cardinality, again unpadded.
        obs = host.observations()
        assert obs.shape == (2, n_agents, host.obs_dim)
        assert np.isfinite(obs).all()

    assert seen_lengths == {3, 5, 6, 9}


# ======================================================================
# Test 2 - permuted batch/enumeration order, identical keyed tapes
# ======================================================================
def test_2_keyed_streams_are_stable_and_order_independent() -> None:
    """Invariant 2: entity and regional-event streams are key stable."""
    config = RelayCorridorConfig(n_agents=6, horizon=60, d0_k_set=(1, 2, 5))
    episodes = [11, 4, 27, 3]
    permutation = [2, 0, 3, 1]

    host_a = RelayCorridorHost(config, batch_size=4, master_seed=17, episode_ids=episodes)
    host_b = RelayCorridorHost(
        config,
        batch_size=4,
        master_seed=17,
        episode_ids=[episodes[i] for i in permutation],
    )
    tapes_a = host_a.stream_tapes()
    tapes_b = host_b.stream_tapes()
    for name in tapes_a:
        np.testing.assert_array_equal(tapes_a[name][permutation], tapes_b[name])

    # A single-lane host holding one of those episodes draws the same tape.
    for lane, episode in enumerate(episodes):
        solo = RelayCorridorHost(config, batch_size=1, master_seed=17, episode_ids=[episode])
        solo_tapes = solo.stream_tapes()
        for name in tapes_a:
            np.testing.assert_array_equal(tapes_a[name][lane], solo_tapes[name][0])

    # Order independence carries through to realised trajectories.
    roles = np.zeros((4, config.n_agents), dtype=np.int64)
    renew = np.zeros((4, config.n_agents), dtype=bool)
    for _ in range(config.horizon - 1):
        host_a.step(roles, renew, build_obs=False)
        host_b.step(roles[permutation], renew[permutation], build_obs=False)
    np.testing.assert_array_equal(host_a.private_theta()[permutation], host_b.private_theta())
    np.testing.assert_array_equal(host_a.change_flag[permutation], host_b.change_flag)
    np.testing.assert_array_equal(host_a.cue[permutation], host_b.cue)

    # A different master seed must give a different tape (the key really binds).
    other = RelayCorridorHost(config, batch_size=4, master_seed=18, episode_ids=episodes)
    assert not np.array_equal(other.stream_tapes()["event_u"], tapes_a["event_u"])


# ======================================================================
# Test 3 - divisible and non-divisible N both execute
# ======================================================================
def test_3_every_positive_n_is_valid_there_is_no_n_mod_k_rule() -> None:
    """Invariant 3."""
    executed = {}
    for n_agents in range(1, 9):
        config = RelayCorridorConfig(n_agents=n_agents, n_roles=2, horizon=20, d0_k_set=(1, 2))
        adapter = RelayCorridorAdapter(config, num_envs=1, master_seed=n_agents)
        obs, info = adapter.reset()
        assert obs.shape == (n_agents, adapter.obs_dim)
        actions = np.zeros((n_agents, config.n_roles), dtype=np.float32)
        actions[:, 0] = 1.0
        total = 0.0
        for _ in range(config.horizon):
            obs, reward, terminated, _truncated, step_info = adapter.step(actions)
            total += float(reward)
            assert step_info["service_indicators"].shape == (n_agents,)
        assert terminated
        executed[n_agents] = total
        assert np.isfinite(total)

    # Both a divisible (N % K == 0) and a non-divisible roster ran.
    assert set(executed) == set(range(1, 9))
    assert 6 % 2 == 0 and 7 % 2 == 1


# ======================================================================
# Test 4 - pinning, full deterministic initial dwell, matched means, variances
# ======================================================================
def _expected_event_count(hazard: np.ndarray, horizon: int, n_roles: int) -> float:
    """Exact expected number of events in the ``H - 1`` transitions.

    ``dp_service_profile`` for the switching oracle gives ``service[t] =
    P(no event realised into t)`` for ``t >= 1``, so the complement sums to the
    expected event count.
    """
    profile = dp_service_profile(hazard, horizon, n_roles, renew_on_flag=True)
    return float((horizon - 1) - profile[1:].sum())


def test_4_pinning_dwell_laws_and_reported_variances(tmp_path: Path) -> None:
    """Invariant 4."""
    # --- pinning: agents never move region or zone --------------------
    config = proposal_config("small")
    host = RelayCorridorHost(config, batch_size=8, master_seed=23, episode_ids=list(range(8)))
    region0 = host.region_of_agent.copy()
    zone0 = host.zone_of_agent.copy()
    roles = np.zeros((8, config.n_agents), dtype=np.int64)
    renew = np.zeros((8, config.n_agents), dtype=bool)
    for _ in range(config.horizon - 1):
        host.step(roles, renew, build_obs=False)
        np.testing.assert_array_equal(host.region_of_agent, region0)
        np.testing.assert_array_equal(host.zone_of_agent, zone0)
    for lane in range(8):
        records = host.public_state_records(lane=lane)
        assert [r["region_id"] for r in records["agents"]] == list(region0)
        assert [r["zone_id"] for r in records["agents"]] == list(zone0)

    # --- scripted Bernoulli tape: the realised hazard is lambda_r ------
    events = np.stack(host.event_log, axis=0)  # [H - 1, B, R]
    assert events.shape == (config.horizon - 1, 8, config.n_regions)
    counts = events.sum(axis=0).mean(axis=0)
    for region, lam in enumerate(config.lambda_regions):
        expected = _expected_event_count(
            np.full(2, lam), config.horizon, config.n_roles
        )
        assert abs(expected - lam * (config.horizon - 1)) < 1e-9
        # 8 lanes only: a wide but non-vacuous band.
        assert abs(counts[region] - expected) < 6.0 * np.sqrt(max(expected, 1.0))

    # --- three mean-matched laws --------------------------------------
    moments = {}
    for name in ("deterministic", "geometric", "lognormal"):
        law = make_renewal_law(name, E4_MEAN, 1.0)
        moments[name] = {"mean": law.mean(), "variance": law.variance()}
        assert law.mean() == pytest.approx(E4_MEAN, abs=1e-9), name
        assert law.variance() == pytest.approx(E4_VARIANCES[name], abs=5e-4), name
    # Only E[D] is matched; the variances are genuinely different.
    variances = [moments[name]["variance"] for name in ("deterministic", "geometric", "lognormal")]
    assert variances[0] < variances[1] < variances[2]

    # --- deterministic episodes start with a FULL dwell ---------------
    det = RelayCorridorConfig(
        event_process="renewal",
        renewal_law="deterministic",
        renewal_mean=E4_MEAN,
        d0_k_set=(1, 2, 5, 20, 40),
    )
    det_host = RelayCorridorHost(det, batch_size=4, master_seed=31, episode_ids=[0, 1, 2, 3])
    roles = np.zeros((4, det.n_agents), dtype=np.int64)
    renew = np.zeros((4, det.n_agents), dtype=bool)
    for _ in range(det.horizon - 1):
        det_host.step(roles, renew, build_obs=False)
    det_events = np.stack(det_host.event_log, axis=0)
    event_steps = np.flatnonzero(det_events[:, 0, 0]) + 1
    assert list(event_steps) == list(range(20, det.horizon, 20))
    for lane in range(4):
        for region in range(det.n_regions):
            dwells = det_host.dwell_lengths(lane, region)
            assert dwells.size == det.horizon // 20 - 1
            assert set(dwells.tolist()) == {20}

    # --- the other two laws reproduce their own exact event counts -----
    for name in ("geometric", "lognormal"):
        config_r = RelayCorridorConfig(
            event_process="renewal",
            renewal_law=name,
            renewal_mean=E4_MEAN,
            lognormal_shape=1.0,
            d0_k_set=(1, 2, 5, 20, 40),
        )
        law = config_r.region_laws()[0]
        hazard = law.hazard_table(min(law.dp_age_cap(config_r.horizon), config_r.horizon))
        expected = _expected_event_count(hazard, config_r.horizon, config_r.n_roles)
        host_r = RelayCorridorHost(
            config_r, batch_size=256, master_seed=41, episode_ids=list(range(256))
        )
        roles = np.zeros((256, config_r.n_agents), dtype=np.int64)
        renew = np.zeros((256, config_r.n_agents), dtype=bool)
        for _ in range(config_r.horizon - 1):
            host_r.step(roles, renew, build_obs=False)
        realised = np.stack(host_r.event_log, axis=0).sum(axis=0)
        observed = float(realised.mean())
        stderr = float(realised.std(ddof=1) / np.sqrt(realised.size))
        assert abs(observed - expected) < 5.0 * max(stderr, 1e-9), (name, observed, expected)
        moments[name]["expected_events"] = expected
        moments[name]["observed_events"] = observed

    _record(tmp_path, "test4_dwell_laws", moments)


# ======================================================================
# Test 5 - the three proposal points, both margins, measured sigma_Delta
# ======================================================================
def test_5_enumerated_margins_match_the_proposal_table(tmp_path: Path) -> None:
    """Invariant 5.

    Both margins come from enumeration; the margin table is the expected value.
    ``m`` is registered and reported but is not an E2-E4 acceptance criterion.
    The acceptance-scale requirement is applied to ``m_dur`` with the
    ``sigma_Delta`` measured from matched (common-random-number) reference tapes.
    """
    # The repository C-table is the mechanics page's stated check value.
    for (k, lam), value in C_TABLE.items():
        assert _c(k, lam) == pytest.approx(value, abs=5e-5)

    summary = {}
    for level, row in PROPOSAL_GRID.items():
        config = proposal_config(level)
        report = enumerate_references(config)

        weights = config.region_weights
        lams = config.lambda_regions
        closed_switch = _j_switch(config.delta, lams, weights, config.horizon)
        closed_fixed = {
            k: _j_fixed(config.delta, lams, weights, config.horizon, k)
            for k in config.d0_k_set
        }
        closed_best_k = max(closed_fixed, key=lambda k: closed_fixed[k])
        closed_m_dur = closed_switch - closed_fixed[closed_best_k]
        closed_m = closed_switch - closed_fixed[closed_best_k] / config.n_roles

        # 1. the exact enumeration equals the mechanics page's closed forms
        assert report.j_switch == pytest.approx(closed_switch, abs=1e-12)
        for k, value in closed_fixed.items():
            assert report.j_fixed_k[k] == pytest.approx(value, abs=1e-12)
        assert report.best_fixed_k == closed_best_k == int(row["best_k"])
        assert report.j_open_best == pytest.approx(
            closed_fixed[closed_best_k] / config.n_roles, abs=1e-12
        )
        assert report.m == pytest.approx(closed_m, abs=1e-12)
        assert report.m_dur == pytest.approx(closed_m_dur, abs=1e-12)

        # 2. the enumeration reproduces the printed table digits
        assert round(report.m, 6) == pytest.approx(float(row["m"]), abs=5e-7)
        assert round(report.m_dur, 6) == pytest.approx(float(row["m_dur"]), abs=5e-7)

        # 3. the open-loop census is K^Z maps x (periods + never-renew)
        assert len(report.open_candidates) == (
            config.n_roles ** config.n_zones
        ) * (len(config.d0_k_set) + 1)

        # 4. sigma_Delta measured from matched reference tapes
        batch = 512
        host = RelayCorridorHost(
            config, batch_size=batch, master_seed=997, episode_ids=list(range(batch))
        )
        switch_tape = rollout_reference(host, SwitchingOracle())["mean_return"]
        fixed_tape = rollout_reference(host, FixedKOracle(report.best_fixed_k))["mean_return"]
        paired = switch_tape - fixed_tape
        sigma_delta = float(paired.std(ddof=1))
        assert sigma_delta <= 1.0  # per-episode mean-return differences lie in [-1, 1]
        resolution = 3.0 * sigma_delta / np.sqrt(EVAL_EPISODES)
        assert report.m_dur >= resolution
        assert report.resolution_ok(sigma_delta, EVAL_EPISODES)

        summary[level] = {
            "m_enumerated": report.m,
            "m_table": row["m"],
            "m_dur_enumerated": report.m_dur,
            "m_dur_table": row["m_dur"],
            "best_fixed_k": report.best_fixed_k,
            "J_switch": report.j_switch,
            "J_fixed_k": report.j_fixed_k,
            "J_open_best": report.j_open_best,
            "J_greedy": report.j_greedy,
            "sigma_Delta_measured": sigma_delta,
            "resolution_3sigma_over_sqrt_4096": resolution,
            "paired_gap_measured": float(paired.mean()),
        }

    # The smallest proposed m_dur clears the bound quoted in the ADR.
    assert min(v["m_dur_enumerated"] for v in summary.values()) > 3.0 / 64.0
    _record(tmp_path, "test5_margins", summary)


# ======================================================================
# Test 6 - too-short H rejects only fixed-k D0; D2 k_max is exempt; M emitted
# ======================================================================
def test_6_horizon_rule_rejects_only_fixed_k_d0_and_emits_m(tmp_path: Path) -> None:
    """Invariant 6: ``H >= 10 * max(D0_k_set)``; D2 ``k_max`` is exempt."""
    accepted = proposal_config("small")
    record = validate_horizon(accepted, mode="d0_fixed_k")
    assert record["accepted"] is True
    assert record["required_horizon"] == 400
    assert record["segments_at_largest_k"] == 10

    too_short = RelayCorridorConfig(horizon=100, d0_k_set=(1, 2, 5, 20, 40))
    with pytest.raises(HorizonValidationError):
        validate_horizon(too_short, mode="d0_fixed_k")

    # The same object as a D2 arm at a large k_max is accepted and reports M.
    d2_record = validate_horizon(too_short, mode="d2", k_max=too_short.horizon)
    assert d2_record["accepted"] is True
    assert d2_record["k_max_exempt"] is True
    assert d2_record["k_max"] == 100

    # M rows per rollout; ADR 01 revision 3's two published values.
    assert rows_per_rollout(32, 500, 10) == 1600
    assert rows_per_rollout(32, 500, 500) == 32
    corridor_m = {
        k: rows_per_rollout(32, accepted.horizon, k) for k in accepted.d0_k_set
    }
    assert corridor_m[40] == 32 * 10
    d2_m = rows_per_rollout(32, accepted.horizon, accepted.horizon)
    assert d2_m == 32
    _record(
        tmp_path,
        "test6_horizon_and_rows",
        {"d0": record, "d2": d2_record, "M_by_k": corridor_m, "M_d2_k_max_H": d2_m},
    )


# ======================================================================
# Test 7 - adapter surface, reward range, disabled probe and coupling
# ======================================================================
def test_7_adapter_argmax_renew_mask_reward_and_disabled_fields() -> None:
    """Invariant 7."""
    config = proposal_config("small", horizon=30, d0_k_set=(1, 2, 3))
    adapter = RelayCorridorAdapter(config, num_envs=1, master_seed=5)
    obs, info = adapter.reset()
    n, k = config.n_agents, config.n_roles
    assert adapter.n_z == k and adapter.action_dim == k and adapter.role_decode == "argmax"
    assert obs.shape == (n, adapter.obs_dim)
    assert info["state"].shape == (adapter.state_dim,)

    theta = adapter.host.private_theta()[0]
    target = adapter.host.target_roles()[0]

    # --- continuous K-vectors: the host takes the argmax ---------------
    actions = np.full((n, k), -3.0, dtype=np.float32)
    actions[np.arange(n), target] = -2.5  # still the argmax, by a small margin
    _obs, reward, _terminated, _truncated, step_info = adapter.step(actions)
    np.testing.assert_array_equal(step_info["roles"], target)
    assert step_info["service_indicators"].all()
    assert reward == pytest.approx(config.delta)
    assert 0.0 <= reward <= 1.0
    # The shared scalar is exactly the mean over per-agent indicators, times Delta.
    assert reward == pytest.approx(
        config.delta * step_info["service_indicators"].mean()
    )
    assert step_info["per_agent_service_reward"].sum() == pytest.approx(reward)

    # --- wrong role contributes zero ----------------------------------
    wrong = np.zeros((n, k), dtype=np.float32)
    wrong[np.arange(n), (target + 1) % k] = 1.0
    _obs, reward, _t, _tr, step_info = adapter.step(wrong)
    assert reward == 0.0
    assert not step_info["service_indicators"].any()

    # --- scripted S_t: RENEW is exact and contributes zero -------------
    s_t = [0, 3, 5]
    correct = np.zeros((n, k), dtype=np.float32)
    correct[np.arange(n), adapter.host.target_roles()[0]] = 1.0
    _obs, reward, _t, _tr, step_info = adapter.step(correct, renew_indices=s_t)
    mask = step_info["renew_mask"]
    assert list(np.flatnonzero(mask)) == s_t
    assert not step_info["service_indicators"][s_t].any()
    assert reward == pytest.approx(config.delta * (n - len(s_t)) / n)

    # A mask array and an index set must agree exactly.
    explicit = np.zeros(n, dtype=bool)
    explicit[s_t] = True
    _obs, reward_mask, _t, _tr, mask_info = adapter.step(
        correct, renew_mask=explicit
    )
    np.testing.assert_array_equal(mask_info["renew_mask"], explicit)

    # --- a stale lease contributes zero even with the right role -------
    stale = RelayCorridorAdapter(
        proposal_config("large", horizon=30, d0_k_set=(1, 2, 3)), num_envs=1, master_seed=13
    )
    stale.reset()
    saw_stale_zero = False
    for _ in range(29):
        roles_now = stale.host.target_roles()[0]
        act = np.zeros((n, k), dtype=np.float32)
        act[np.arange(n), roles_now] = 1.0
        _obs, reward, _t, _tr, sinfo = stale.step(act)
        fresh = sinfo["lease_fresh"]
        assert np.array_equal(sinfo["service_indicators"], fresh)
        assert 0.0 <= float(reward) <= 1.0
        if not fresh.all():
            saw_stale_zero = True
    assert saw_stale_zero, "a stale lease was never exercised"

    # --- reserved probe and coupling fields are exactly zero ----------
    layout = adapter.host.obs_slices
    obs_now = adapter.host.observations()
    assert np.count_nonzero(obs_now[:, :, layout["probe_theta"]]) == 0
    assert np.count_nonzero(obs_now[:, :, layout["probe_valid"]]) == 0
    assert np.count_nonzero(obs_now[:, :, layout["coupling"]]) == 0
    assert np.count_nonzero(adapter.host.probe_theta) == 0
    assert np.count_nonzero(adapter.host.coupling_field) == 0
    assert config.c_probe == 0.0 and config.e5_coupling_enabled is False

    # The switches themselves are refused rather than silently reinterpreted.
    with pytest.raises(NotImplementedError):
        RelayCorridorConfig(e5_coupling_enabled=True)
    with pytest.raises(ValueError):
        RelayCorridorConfig(c_probe=0.25)
    with pytest.raises(ValueError):
        RelayCorridorConfig(rho=0.1)


# ======================================================================
# Test 8 - reference traces, D = 20 / k = 20, cue timing, K = 2 greedy
# ======================================================================
def test_8_reference_traces_step_order_cue_timing_and_equalities(tmp_path: Path) -> None:
    """Invariant 8."""
    # --- deterministic D = 20: fixed k = 20 IS the switching oracle ----
    det = RelayCorridorConfig(
        event_process="renewal",
        renewal_law="deterministic",
        renewal_mean=20.0,
        d0_k_set=(1, 2, 5, 20, 40),
        delta=0.4,
    )
    det_report = enumerate_references(det)
    assert det_report.j_fixed_k[20] == pytest.approx(det_report.j_switch, abs=1e-12)
    assert det_report.m_dur == pytest.approx(0.0, abs=1e-12)
    assert det_report.best_fixed_k == 20
    # 19 events in 399 transitions, each costing exactly one step of service.
    assert det_report.j_switch == pytest.approx(0.4 * 381.0 / 400.0, abs=1e-12)

    det_host = RelayCorridorHost(det, batch_size=4, master_seed=61, episode_ids=[0, 1, 2, 3])
    realised = {}
    for policy, expected in (
        (SwitchingOracle(), det_report.j_switch),
        (FixedKOracle(20), det_report.j_fixed_k[20]),
        (FixedKOracle(5), det_report.j_fixed_k[5]),
        (FixedKOracle(40), det_report.j_fixed_k[40]),
        (GreedyOnPublicState(), det_report.j_greedy),
    ):
        out = rollout_reference(det_host, policy)
        # A latent-aware policy on a deterministic dwell law has no randomness
        # left, so this is an exact identity, not a Monte-Carlo agreement.
        assert out["mean_return"].std() == 0.0
        assert float(out["mean_return"][0]) == pytest.approx(expected, abs=1e-12), policy.name
        realised[policy.name] = float(out["mean_return"][0])

    # --- D0 structure cut: setup service and post-event service ---------
    fixed_out = rollout_reference(det_host, FixedKOracle(5))
    service = fixed_out["service_indicators"][:, 0, 0]
    renews = fixed_out["renew_masks"][:, 0, 0]
    boundaries = list(range(5, det.horizon, 5))
    assert list(np.flatnonzero(renews)) == boundaries
    assert not service[boundaries].any()  # setup service is lost at each boundary
    # Post-event service is lost until the next boundary re-stamps the lease.
    # With the deterministic law the events land *on* the k = 5 boundaries, so
    # that window collapses to the boundary step itself.
    events = np.flatnonzero(fixed_out["change_flags"][:, 0, 0])
    assert events.size == det.horizon // 20 - 1
    for event_step in events:
        next_renew = int(-(-int(event_step) // 5) * 5)
        window = range(int(event_step), min(next_renew + 1, det.horizon))
        assert not service[list(window)].any()

    # The unaligned case: a Bernoulli hazard puts events strictly inside the
    # fixed windows, and the stale run then really does reach the next boundary.
    e3 = proposal_config("large", horizon=200)
    e3_host = RelayCorridorHost(e3, batch_size=2, master_seed=88, episode_ids=[0, 1])
    e3_out = rollout_reference(e3_host, FixedKOracle(5))
    saw_unaligned = False
    for lane in range(2):
        for region in range(e3.n_regions):
            agents = np.flatnonzero(e3_host.region_of_agent == region)
            if agents.size == 0:
                continue
            svc = e3_out["service_indicators"][:, lane, agents[0]]
            for event_step in np.flatnonzero(e3_out["change_flags"][:, lane, region]):
                next_renew = int(-(-int(event_step) // 5) * 5)
                window = range(int(event_step), min(next_renew + 1, e3.horizon))
                assert not svc[list(window)].any()
                if int(event_step) % 5 != 0:
                    saw_unaligned = True
    assert saw_unaligned, "no event landed strictly inside a fixed window"

    # --- step order and cue timing, asserted directly -------------------
    config = proposal_config("large", horizon=200)
    host = RelayCorridorHost(config, batch_size=8, master_seed=77, episode_ids=list(range(8)))
    policy = SwitchingOracle()
    host.reset()
    policy.reset(host)
    theta_history = [host.private_theta().copy()]
    cue_history = [host.cue.copy()]
    flag_history = [host.change_flag.copy()]
    service_history = []
    for t in range(config.horizon):
        roles, renew = policy.act(host, t)
        _obs, _reward, _terminated, info = host.step(roles, renew, build_obs=False)
        service_history.append(info["service_indicators"].copy())
        theta_history.append(host.private_theta().copy())
        cue_history.append(host.cue.copy())
        flag_history.append(host.change_flag.copy())
    theta_history = np.stack(theta_history[:-1])   # theta at t = 0 .. H - 1
    cue_history = np.stack(cue_history[:-1])
    flag_history = np.stack(flag_history[:-1])
    service_history = np.stack(service_history)

    changed = np.zeros_like(flag_history, dtype=bool)
    changed[1:] = theta_history[1:] != theta_history[:-1]
    # The change flag at t marks exactly the event realised into t.
    np.testing.assert_array_equal(flag_history.astype(bool), changed)
    # The cue at t still shows theta_{t-1}: the OLD latent on a change step.
    np.testing.assert_array_equal(cue_history[1:], theta_history[:-1])
    assert (cue_history[changed] != theta_history[changed]).all()
    assert (cue_history[~changed] == theta_history[~changed]).all()
    # RENEW at t is a zero-service step, and service resumes at t + 1.
    flagged = flag_history[:, :, 0].astype(bool)
    region0 = np.flatnonzero(host.region_of_agent == 0)
    assert not service_history[:, :, region0][flagged].any()
    assert flagged.any(), "no event was exercised on region 0"
    for t, lane in zip(*np.nonzero(flagged[:-1])):
        if not flagged[t + 1, lane]:
            assert service_history[t + 1, lane, region0].all()

    # --- K = 2: greedy on public state equals the switching oracle -----
    for level in ("small", "medium", "large"):
        cfg = proposal_config(level)
        report = enumerate_references(cfg)
        assert cfg.n_roles == 2
        assert report.j_greedy == pytest.approx(report.j_switch, abs=1e-12)
        for k, value in report.j_fixed_k.items():
            assert value < report.j_switch, (level, k)  # the D0 cut is strict
        assert report.j_open_best < report.j_best_fixed_k

    # Greedy realised on the host matches the switching oracle step for step.
    crn = RelayCorridorHost(
        proposal_config("large"), batch_size=64, master_seed=123, episode_ids=list(range(64))
    )
    a = rollout_reference(crn, SwitchingOracle())
    b = rollout_reference(crn, GreedyOnPublicState())
    np.testing.assert_array_equal(a["service_indicators"], b["service_indicators"])
    np.testing.assert_allclose(a["mean_return"], b["mean_return"], atol=0.0)

    # An open-loop plan is strictly worse on the same tapes.
    open_out = rollout_reference(crn, OpenLoopPlan((0,) * crn.n_zones, 5))
    assert open_out["mean_return"].mean() < a["mean_return"].mean()

    # --- K = 3, the registered family point: the equality is not generic ---
    # The flag no longer selects among the K - 1 alternatives, so greedy waits
    # for the next cue, loses two steps per event, and falls strictly short of
    # the switching oracle.  m_dur compares two latent-aware oracles and is
    # therefore unchanged; m is not.
    k3 = RelayCorridorConfig(
        n_agents=6,
        n_roles=3,
        n_zones=4,
        horizon=400,
        delta=0.4,
        lambda_regions=(0.005, 0.02),
        d0_k_set=(1, 2, 5, 20, 40),
    )
    k3_report = enumerate_references(k3)
    assert len(k3_report.open_candidates) == 3 ** 4 * 6 == 486
    assert k3_report.j_greedy < k3_report.j_switch
    lam = np.array(k3.lambda_regions)
    two_step = k3.delta * float(
        np.mean((1.0 + (k3.horizon - 1) * (1.0 - lam) ** 2) / k3.horizon)
    )
    assert k3_report.j_greedy == pytest.approx(two_step, abs=5e-5)
    assert k3_report.m_dur == pytest.approx(
        enumerate_references(proposal_config("small")).m_dur, abs=1e-12
    )
    assert k3_report.m > enumerate_references(proposal_config("small")).m

    _record(
        tmp_path,
        "test8_reference_traces",
        {
            "deterministic_realised": realised,
            "deterministic_dp": det_report.as_dict(),
        },
    )


# ======================================================================
# Test 9 - pinned-CPU, native-disabled throughput; record the disposition
# ======================================================================
_BENCH = r"""
import json, platform, sys, time
import numpy as np
from envs.relay_corridor import RelayCorridorHost, proposal_config

assert "torch" not in sys.modules, "the host core must not import torch"
assert not any(name.startswith("experiments.") for name in sys.modules), (
    "the host core must not import experiments/candidates"
)
assert "envs.native" not in sys.modules, "the host core must not touch the native boundary"

cfg = proposal_config("small")
out = {}
for label, build_obs in (("mechanics", False), ("with_observations", True)):
    host = RelayCorridorHost(cfg, batch_size=1, master_seed=3, episode_ids=[0])
    roles = np.zeros((1, cfg.n_agents), dtype=np.int64)
    renew = np.zeros((1, cfg.n_agents), dtype=bool)
    host.reset()
    for _ in range(cfg.horizon):
        host.step(roles, renew, build_obs=build_obs)
    best = 0.0
    for _ in range(5):
        host.reset()
        t0 = time.perf_counter()
        for _ in range(cfg.horizon):
            host.step(roles, renew, build_obs=build_obs)
        best = max(best, cfg.horizon / (time.perf_counter() - t0))
    out[label + "_steps_per_s_core"] = best

host = RelayCorridorHost(cfg, batch_size=64, master_seed=3, episode_ids=list(range(64)))
roles = np.zeros((64, cfg.n_agents), dtype=np.int64)
renew = np.zeros((64, cfg.n_agents), dtype=bool)
host.reset()
for _ in range(cfg.horizon):
    host.step(roles, renew, build_obs=True)
best = 0.0
for _ in range(3):
    host.reset()
    t0 = time.perf_counter()
    for _ in range(cfg.horizon):
        host.step(roles, renew, build_obs=True)
    best = max(best, 64 * cfg.horizon / (time.perf_counter() - t0))
out["vectorized_batch64_env_steps_per_s_core"] = best
out["machine"] = {
    "processor": platform.processor(),
    "machine": platform.machine(),
    "platform": platform.platform(),
    "python": sys.version.split()[0],
    "numpy": np.__version__,
}
out["torch_imported"] = "torch" in sys.modules
print("BENCHMARK_JSON " + json.dumps(out))
"""


def test_9_native_disabled_numpy_throughput_against_the_recorded_target(tmp_path: Path) -> None:
    """Invariant 9: check native-disabled NumPy against the ``1e4`` steps/s/core target.

    The target is advice §3 P7's *target*, not a measurement, so this test
    records the disposition and does not fail on a miss.  It does fail if the
    host core reaches for torch, a native backend, or an isolated candidate.
    """
    script = tmp_path / "relay_corridor_benchmark.py"
    script.write_text(textwrap.dedent(_BENCH))
    env = dict(os.environ)
    env.update(
        {
            "PYTHONPATH": str(REPO_ROOT),
            "PYTHONHASHSEED": "0",
            # pinned CPU: one thread for every math backend NumPy might reach for
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert completed.returncode == 0, completed.stderr
    payload = None
    for line in completed.stdout.splitlines():
        if line.startswith("BENCHMARK_JSON "):
            payload = json.loads(line[len("BENCHMARK_JSON ") :])
    assert payload is not None, completed.stdout
    assert payload["torch_imported"] is False

    target = 1.0e4
    measured = payload["mechanics_steps_per_s_core"]
    payload["target_steps_per_s_core"] = target
    payload["disposition"] = "meets_target" if measured >= target else "below_target"
    payload["ratio_to_target"] = measured / target
    payload["pinned_threads"] = 1
    payload["native_disabled"] = True
    payload["measured_on"] = platform.node()
    _record(tmp_path, "test9_throughput", payload)

    # Recorded, not gated: the target is prospective advice, not a contract.
    assert measured > 0.0
    assert payload["disposition"] in ("meets_target", "below_target")
